#!/usr/bin/env python3
"""H001 - locate RTTI typeinfo objects and vtables for FX processing classes in 1.60.

Deterministic static scan of target/EP085_Main_R_fw160 (never modified).

Method (Itanium C++ ABI, ARM EABI, non-PIE executable):
  * The libstdc++ typeinfo vtables (_ZTVN10__cxxabiv1{17__class,20__si_class,21__vmi_class}_type_infoE)
    are imported via R_ARM_COPY into .bss. A typeinfo object's vptr is therefore the absolute value
    (COPY address + 8), already present in the file bytes (no load-time relocation of .rodata).
  * Every aligned word in the loaded image equal to one of those three values starts a typeinfo object:
      class: [vptr, name]            si: [vptr, name, base]       vmi: [vptr, name, flags, n, (base, offflags)*n]
  * A vtable group is found where an aligned word == typeinfo address T and the previous word (offset-to-top)
    is 0 or a small negative number; the address point is that word + 4. Words that are typeinfo base fields
    (si +8, vmi base entries) are excluded explicitly.
  * Vtable end rule: starting at the address point, take consecutive words while the word is a code pointer
    (inside .text, or the __cxa_pure_virtual / other PLT stub inside .plt) AND the word's address is not the
    start of another typeinfo object or the offset-to-top word of another vtable group. Stop at the first
    word failing this.
  * Function extents for slot targets come from .ARM.exidx (sorted function starts; end = next start).
    Body shape counters (capstone, ARM mode): VFP/NEON instruction count, backward branches (loops),
    calls (bl/blx), and loads/stores of floats.

Outputs (only in --out DIR): typeinfo_all.json, fx_classes.json, fx_report.txt
"""
import argparse, json, os, re, struct, subprocess, sys
from collections import defaultdict

import lief
import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TARGET = os.path.join(ROOT, "target", "EP085_Main_R_fw160")
SHA = "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"

FX_RE = re.compile(r"(Fx|Effect|effect|Reverb|Delay|Compressor|LoFi|Lofi|Chorus|Flanger|Phaser|Ducker|"
                   r"Distortion|Limiter|Eq|Filter|Gain)")
F005 = ["FxProcessorBase", "InsertFxProcessor", "MasterFxProcessor", "SendFxProcessor", "EffectBase",
        "c_effect_base", "EffectInOutGain", "InsertFxDelay", "InsertFxCompressor", "SendFxDelay",
        "SendFxReverb", "SendFxCompressor", "FxCompressor", "PerformanceFxLoFi", "MasterFxUnit",
        "SendFxUnit", "InsertFxParameterManager", "MasterFxParameterManager", "SendFxParameterManager",
        "FxParameterManagerBase"]


class Image:
    def __init__(self, path):
        self.data = open(path, "rb").read()
        self.elf = lief.parse(path)
        self.segs = [(p.virtual_address, p.physical_size, p.file_offset)
                     for p in self.elf.segments if p.type == lief.ELF.Segment.TYPE.LOAD]
        self.sec = {s.name: (s.virtual_address, s.virtual_address + s.size) for s in self.elf.sections if s.name}

    def off(self, va):
        for v, sz, o in self.segs:
            if v <= va < v + sz:
                return o + va - v
        return None

    def u32(self, va):
        o = self.off(va)
        if o is None or o + 4 > len(self.data):
            return None
        return struct.unpack_from("<I", self.data, o)[0]

    def cstr(self, va, maxlen=512):
        o = self.off(va)
        if o is None:
            return None
        e = self.data.find(b"\0", o, o + maxlen)
        if e < 0:
            return None
        try:
            return self.data[o:e].decode("ascii")
        except UnicodeDecodeError:
            return None

    def in_sec(self, va, name):
        a, b = self.sec[name]
        return a <= va < b


def demangle_all(names):
    """Demangle typeinfo name strings via c++filt on '_ZTS'+name (typeinfo-name symbol)."""
    if not names:
        return {}
    try:
        p = subprocess.run(["c++filt", "-n"], input="\n".join("_ZTS" + n.lstrip("*") for n in names), capture_output=True,
                           text=True, check=True)
        out = p.stdout.splitlines()
        res = {}
        for n, d in zip(names, out):
            d = d.strip()
            d = re.sub(r"^typeinfo name for ", "", d)
            res[n] = ("(local) " if n.startswith("*") else "") + d
        return res
    except Exception:
        return {n: n for n in names}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H001"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    import hashlib
    h = hashlib.sha256(open(TARGET, "rb").read()).hexdigest()
    assert h == SHA, "target hash mismatch: " + h

    img = Image(TARGET)
    elf = img.elf

    # --- 1. typeinfo vtable values (COPY reloc address + 8)
    tiv = {}
    for r in elf.dynamic_relocations:
        if r.has_symbol and r.symbol.name.startswith("_ZTVN10__cxxabiv1"):
            kind = re.sub(r"_ZTVN10__cxxabiv1\d+(__\w+)E", r"\1", r.symbol.name)
            tiv[r.address + 8] = kind
    plt_syms = {}
    for s in elf.dynamic_symbols:
        if s.value and img.in_sec(s.value, ".plt"):
            plt_syms[s.value] = s.name

    # all aligned words of the loaded file-backed image
    words = {}
    for v, sz, o in img.segs:
        n = sz // 4
        vals = struct.unpack_from("<%dI" % n, img.data, o)
        for i, w in enumerate(vals):
            words[v + 4 * i] = w

    # --- 2. typeinfo objects
    tinfo = {}
    for a, w in words.items():
        if w in tiv:
            kind = tiv[w]
            if kind not in ("__class_type_info", "__si_class_type_info", "__vmi_class_type_info"):
                continue
            namep = words.get(a + 4)
            name = img.cstr(namep) if namep else None
            if not name or not re.match(r"^\*?(\d+|N|S|Z)", name):
                continue
            t = {"addr": a, "kind": kind, "name_ptr": namep, "mangled": name, "bases": [], "field_words": []}
            if kind == "__si_class_type_info":
                t["bases"].append({"ti": words.get(a + 8), "offset_flags": None})
                t["field_words"] = [a + 8]
            elif kind == "__vmi_class_type_info":
                t["vmi_flags"] = words.get(a + 8)
                cnt = words.get(a + 12)
                t["vmi_count"] = cnt
                if cnt is not None and 0 < cnt < 64:
                    for k in range(cnt):
                        t["bases"].append({"ti": words.get(a + 16 + 8 * k),
                                           "offset_flags": words.get(a + 20 + 8 * k)})
                        t["field_words"] += [a + 16 + 8 * k]
            tinfo[a] = t
    dm = demangle_all(sorted({t["mangled"] for t in tinfo.values()}))
    for t in tinfo.values():
        t["name"] = dm.get(t["mangled"], t["mangled"])
    base_field_words = {fw for t in tinfo.values() for fw in t["field_words"]}

    # --- 3. vtable groups
    text_lo, text_hi = img.sec[".text"]
    plt_lo, plt_hi = img.sec[".plt"]

    def is_code_ptr(w):
        return (text_lo <= (w & ~1) < text_hi) or (plt_lo <= w < plt_hi)

    vgroups = []  # (ott_addr, ti, ott)
    for a, w in words.items():
        if w in tinfo and a not in base_field_words and (a - 4) in words:
            ott = words[a - 4]
            sott = ott - (1 << 32) if ott & 0x80000000 else ott
            if -0x10000 <= sott <= 0:
                vgroups.append((a - 4, w, sott))
    vgroup_starts = {g[0] for g in vgroups}
    tinfo_starts = set(tinfo)

    vtables = defaultdict(list)
    for ott_addr, ti, sott in sorted(vgroups):
        ap_ = ott_addr + 8
        slots = []
        x = ap_
        while True:
            if x in tinfo_starts or x in vgroup_starts:
                end_reason = "next typeinfo/vtable group starts"
                break
            w = words.get(x)
            if w is None:
                end_reason = "end of mapped image"
                break
            if not is_code_ptr(w):
                end_reason = "non-code word 0x%08x" % w
                break
            slots.append(w)
            x += 4
        vtables[ti].append({"address_point": ap_, "offset_to_top": sott, "slots": slots,
                            "n_slots": len(slots), "end_reason": end_reason, "end_addr": x})

    # --- 4. exidx function starts
    ex_lo, ex_hi = img.sec[".ARM.exidx"]
    starts = []
    for a in range(ex_lo, ex_hi, 8):
        w = words[a]
        off = w & 0x7fffffff
        if off & 0x40000000:
            off -= 0x80000000
        starts.append((a + off) & 0xffffffff)
    starts = sorted(set(starts))
    import bisect

    def extent(fa):
        i = bisect.bisect_right(starts, fa)
        if i < len(starts):
            return starts[i]
        return text_hi

    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)

    def shape(fa):
        if not (text_lo <= fa < text_hi):
            return {"import": plt_syms.get(fa, "plt?")}
        if fa & 1:
            return {"thumb": True}
        end = extent(fa)
        if fa not in set(starts[max(0, bisect.bisect_left(starts, fa) - 0):bisect.bisect_left(starts, fa) + 1]):
            exidx_start = False
        else:
            exidx_start = True
        end = min(end, fa + 0x4000)
        o = img.off(fa)
        code = img.data[o:o + (end - fa)]
        n = vfp = neon = back = calls = 0
        mn = defaultdict(int)
        callees = []
        for ins in md.disasm(code, fa):
            n += 1
            m = ins.mnemonic
            if m.startswith("v"):
                vfp += 1
                if re.match(r"v(ld|st)\d|v\w+\.(i|f)32$|vdup|vmov\.i|vzip|vuzp|vext|vpadd", m) or "q" in ins.op_str:
                    neon += 1
                mn[m.split(".")[0]] += 1
            if m.startswith("b") and not m.startswith("bic") and ins.op_str.startswith("#"):
                tgt = int(ins.op_str[1:], 16)
                if m.startswith("bl"):
                    calls += 1
                    callees.append(tgt)
                elif tgt <= ins.address:
                    back += 1
            if m.startswith("blx") and not ins.op_str.startswith("#"):
                calls += 1
        return {"exidx_start": exidx_start, "size": end - fa, "insns": n, "vfp": vfp, "neon": neon,
                "back_branches": back, "calls": calls, "top_v": sorted(mn.items(), key=lambda kv: -kv[1])[:6],
                "callees": [hex(c) for c in callees[:12]]}

    # --- 5. outputs
    all_rows = []
    for a, t in sorted(tinfo.items()):
        all_rows.append({"typeinfo": hex(a), "kind": t["kind"], "name": t["name"], "mangled": t["mangled"],
                         "bases": [hex(b["ti"]) if b["ti"] else None for b in t["bases"]],
                         "vtables": [hex(v["address_point"]) for v in vtables.get(a, [])]})
    json.dump(all_rows, open(os.path.join(args.out, "typeinfo_all.json"), "w"), indent=1)

    fx = {a: t for a, t in tinfo.items() if FX_RE.search(t["name"]) and "ViewController" not in t["name"]
          and "Widget" not in t["name"]}
    # include every descendant of the DSP base classes (names the regex can miss, e.g. c_distortion)
    DSP_ROOTS = {"EffectBase", "c_effect_base", "FxProcessorBase", "SamplingRateAndBufferSizeVariable",
                 "IirFilter", "IirFilter2", "FxParameterManagerBase", "Parameter", "IEffector"}
    changed = True
    while changed:
        changed = False
        for a, t in tinfo.items():
            if a in fx:
                continue
            for b in t["bases"]:
                if b["ti"] in tinfo and (tinfo[b["ti"]]["name"] in DSP_ROOTS or
                                         (b["ti"] in fx and tinfo[b["ti"]]["name"] != "IAudioProcessor")):
                    if "ViewController" not in t["name"] and "Widget" not in t["name"]:
                        fx[a] = t
                        changed = True
                        break
    # include bases of FX classes (transitively) so the tree is complete
    changed = True
    while changed:
        changed = False
        for a in list(fx):
            for b in fx[a]["bases"]:
                if b["ti"] in tinfo and b["ti"] not in fx:
                    fx[b["ti"]] = tinfo[b["ti"]]
                    changed = True

    shape_cache = {}
    fxout = []
    for a, t in sorted(fx.items(), key=lambda kv: kv[1]["name"]):
        vts = []
        for v in vtables.get(a, []):
            sl = []
            for i, s in enumerate(v["slots"]):
                if s not in shape_cache:
                    shape_cache[s] = shape(s)
                sl.append({"i": i, "target": hex(s), **shape_cache[s]})
            vts.append({"address_point": hex(v["address_point"]), "offset_to_top": v["offset_to_top"],
                        "n_slots": v["n_slots"], "end_reason": v["end_reason"], "slots": sl})
        fxout.append({"name": t["name"], "mangled": t["mangled"], "typeinfo": hex(a), "kind": t["kind"],
                      "vmi_flags": t.get("vmi_flags"),
                      "bases": [{"ti": hex(b["ti"]) if b["ti"] else None,
                                 "name": tinfo[b["ti"]]["name"] if b["ti"] in tinfo else None,
                                 "offset_flags": hex(b["offset_flags"]) if b["offset_flags"] is not None else None}
                                for b in t["bases"]],
                      "vtables": vts})
    json.dump(fxout, open(os.path.join(args.out, "fx_classes.json"), "w"), indent=1)

    # text report
    L = []
    L.append("typeinfo objects total: %d ; vtable groups total: %d" % (len(tinfo), len(vgroups)))
    L.append("typeinfo vptr values: " + ", ".join("%s=0x%x" % (k, v) for v, k in sorted(tiv.items())))
    names_present = {t["name"] for t in tinfo.values()}
    L.append("F005 names with typeinfo object: %d/%d ; missing: %s" % (
        sum(n in names_present for n in F005), len(F005), [n for n in F005 if n not in names_present]))
    L.append("")
    L.append("%-44s %-10s %-6s %-40s %s" % ("class", "typeinfo", "kind", "bases", "vtables(ap:nslots:ott)"))
    for c in fxout:
        L.append("%-44s %-10s %-6s %-40s %s" % (
            c["name"][:44], c["typeinfo"], c["kind"].replace("_type_info", "").strip("_")[:6],
            ",".join((b["name"] or "?") for b in c["bases"])[:40],
            " ".join("%s:%d:%d" % (v["address_point"], v["n_slots"], v["offset_to_top"]) for v in c["vtables"])))
    open(os.path.join(args.out, "fx_report.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))

    # --- 6. F005 summary + end-rule consistency check
    S = ["F005 classes: name | typeinfo | kind | bases(offset_flags) | vtable groups ap:nslots:offset_to_top | end"]
    byname = {c["name"]: c for c in fxout}
    for n in F005:
        c = byname[n]
        S.append("%s | %s | %s | %s | %s | %s" % (
            n, c["typeinfo"], c["kind"].strip("_"),
            ", ".join("%s%s" % (b["name"], ("(" + b["offset_flags"] + ")") if b["offset_flags"] else "")
                      for b in c["bases"]) or "-",
            " ".join("%s:%d:%d" % (v["address_point"], v["n_slots"], v["offset_to_top"]) for v in c["vtables"]) or "NONE",
            "; ".join(v["end_reason"] for v in c["vtables"][:1])))
    S.append("")
    S.append("End-rule check: primary vtable of each FX class vs its primary (offset 0) base's primary vtable")
    bad = checked = 0
    for c in fxout:
        if not c["vtables"] or not c["bases"]:
            continue
        b0 = c["bases"][0]
        if b0["offset_flags"] not in (None,) and (int(b0["offset_flags"], 16) >> 8) != 0:
            continue
        bc = tinfo.get(int(b0["ti"], 16)) if b0["ti"] else None
        # base's own vtable: the offset-0 group closest below the base typeinfo (excludes construction vtables)
        bti = int(b0["ti"], 16) if b0["ti"] else 0
        bv = sorted([v for v in vtables.get(bti, []) if v["offset_to_top"] == 0 and v["address_point"] < bti],
                    key=lambda v: bti - v["address_point"]) if bc else []
        pv = [v for v in c["vtables"] if v["offset_to_top"] == 0]
        if bv and pv:
            ok = pv[0]["n_slots"] >= bv[0]["n_slots"]
            checked += 1
            bad += not ok
            if not ok:
                S.append("  VIOLATION %s (%d) < base %s (%d)" % (c["name"], pv[0]["n_slots"], bc["name"], bv[0]["n_slots"]))
    S.append("  pairs checked: %d ; violations: %d" % (checked, bad))
    open(os.path.join(args.out, "f005_summary.txt"), "w").write("\n".join(S) + "\n")
    print("\n".join(S))


if __name__ == "__main__":
    main()
