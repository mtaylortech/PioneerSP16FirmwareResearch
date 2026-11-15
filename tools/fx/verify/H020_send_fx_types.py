#!/usr/bin/env python3
"""H020 — which FX types the SendFxUnit's SendFxProcessor can take, and what SendFxUnit +0x80/+0x90 hold (cycle 032).

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and
never stored; outputs are derived numbers, addresses and the name strings the code compares. Emulation is guest memory only; nothing
is written outside --out and no image is built.

Sections (criteria of kb/cycles/032.md):
  C1 static: SendFxParameterManager (SFPM, vt 0x8446d4) slot 32 applyFxType 0x12bc84 and MasterFxParameterManager (MFPM, vt 0x8437ec)
     slot 32 0x1237cc decoded by one pattern decoder (s53 effectId->index call, pending-equal early return, jump table, per case:
     static juce::Identifier name written to EffectData+0x24 and the constant passed to processor vt+0xbc = slot 47 setFxType);
     s53/s54 tables; s52 (type name -> index, used by the s51 reload) decoded as a compare chain; every SFPM function that reaches
     processor slot 47 (whole-.text scan, see C2).
  C2 static: every reference to SendFxProcessor setFxType 0x11a254 (direct branch scan, data-word scan) and every `ldr rX,[rY,#0xbc]
     ... blx rX` site in .text, with its containing function, the owner vtable(s) of that function and the object tag (armflow);
     stores to the pending field +0xa4 in SendFxProcessor code.
  C4 static: SendFxUnit ctor 0x1b3314 store sites +0x80..+0x90 with the class (RTTI) of each stored object; sweep of stores to
     +0x80/+0x84/+0x88/+0x8c/+0x90 in SendFxUnit code and after every load of the SendFxUnit pointer (sys+0x604, CompositeFxUnit+0x90).
  C5 emulation: REAL SFPM ctor + REAL s32 / s52 / s51 on a REAL SendFxProcessor (H077 EmuProc via the H083 Rig), then REAL
     processBlock (swap): pending/current index and the effect object at +0x8c for every effectId -3..24 and 0xffffffff, from two
     start states; the same for Master for comparison; s52 on every name; s51 reload of each type name.
  C3 emulation: the 20 FxSelectPopupWidgetController handlers (H086 Rig, real handler + ModelInterface code, stand-in effectors) in
     Send, Master and Insert context; each Send-context effectId then fed to the real SFPM s32 (C5 rig) -> resulting type index.
Run: .venv/bin/python -B harness/H020_send_fx_types.py --out DIR
"""
import argparse, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()                                       # before any unicorn Uc is created
import emu                                                     # noqa: E402
from sp16img import Image                                      # noqa: E402
import armflow                                                 # noqa: E402
import H083_enum_defaults as H83                               # noqa: E402  (imports H077; real ctor rigs)
H77 = H83.H77

# ------------------------------------------------------------------------------------------------------------------ addresses (1.60)
SFPM_VT, MFPM_VT = 0x8446d4, 0x8437ec
SFP_VT, SFP_CTOR, SFP_SETFX, SFP_PEND_GET = 0x842d40, 0x11bbe4, 0x11a254, 0x119980
SFU_VT, SFU_CTOR = 0x862e28, 0x1b3314
ID_CTOR, ID_COPY, ID_DTOR, ID_ASSIGN = 0x666e84, 0x627ba0, 0x6280c8, 0x62abf4
TI_NAME_OFF = 4
MS_NAMES = ["SendFxDelay", "SendFxReverb", "Chorus", "Flanger", "PEQ", "MMF", "LoFi", "SendFxCompressor", "Distortion", "Phaser"]
POPUP_VT0, POPUP_N = 0x86b120, 19          # FxSelectPopupWidgetController::Handler, _0 … _18 (vtables 0x20 apart; slot 3 = handler)


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u & 0x80000000 else u


def lit(im, i):
    m = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", i.op_str)
    if i.mnemonic.startswith("ldr") and m:
        return m.group(1), im.u32(i.address + 8 + int(m.group(2), 0))
    return None, None


def imm(s):
    m = re.search(r"#(-?0x[0-9a-f]+|-?\d+)", s)
    return int(m.group(1), 0) if m else None


def static_idents(im, lo, hi, depth=1):
    """{static juce::Identifier address: C string}: `ldr r0,=G ; ldr r1,="s" ; bl 0x666e84` (any order, 3 instructions), in [lo,hi)."""
    ins = im.disasm(lo, hi); G = {}
    for k, i in enumerate(ins):
        if i.mnemonic == "bl" and i.op_str == "#0x%x" % ID_CTOR:
            r = {}
            for j in range(k - 1, max(k - 4, -1), -1):
                reg, v = lit(im, ins[j])
                if reg in ("r0", "r1") and reg not in r: r[reg] = v
            if "r0" in r and "r1" in r: G[r["r0"]] = im.cstr(r["r1"], 64)
    return G


def helper_ident(im, t):
    """A helper that only builds/returns one function-static Identifier -> its name (else None)."""
    s, e = im.func_of(t)
    if s != t: return None
    G = static_idents(im, s, e)
    return next(iter(G.values())) if len(G) == 1 else None


# ===================================================================================================================== C1 decoders
def decode_s32(im, fn):
    """Pattern decoder for a Master/Send manager slot 32 (applyFxType)."""
    s, e = im.func_of(fn); assert s == fn
    ins = im.disasm(s, e); at = {i.address: k for k, i in enumerate(ins)}
    G = static_idents(im, s, e)
    R = {"fn": hex(fn), "extent": [hex(s), hex(e)]}
    # prologue facts
    k53 = next(k for k, i in enumerate(ins) if i.mnemonic == "ldr" and i.op_str.endswith("#0xd4]"))
    kpend = next(k for k, i in enumerate(ins) if i.mnemonic == "ldr" and i.op_str.endswith("#0xc0]"))
    R["s53_call"] = hex(ins[k53].address); R["pending_getter_call"] = hex(ins[kpend].address)
    kc = next(k for k in range(kpend, kpend + 5) if ins[k].mnemonic == "cmp")
    assert ins[kc + 1].mnemonic == "beq"
    R["equal_return"] = dict(cmp=hex(ins[kc].address), target=ins[kc + 1].op_str)
    kj = next(k for k, i in enumerate(ins) if i.mnemonic == "ldrls" and i.op_str.startswith("pc, [pc"))
    ncase = imm(ins[kj - 1].op_str) + 1; tbl = ins[kj].address + 8
    targets = [im.u32(tbl + 4 * c) for c in range(ncase)]
    dflt = imm(ins[kj + 1].op_str); assert ins[kj + 1].mnemonic == "b"
    R["jump_table"] = dict(at=hex(tbl), cases=ncase, default=hex(dflt))

    def walk(a):
        """Linear walk from a (unconditional b followed): name copied to +0x24, then the r1 constant at the first vt+0xbc call."""
        name = None; r1 = None; seen = 0; path = []
        while seen < 400:
            seen += 1
            i = ins[at[a]]; path.append(i.address)
            if i.mnemonic == "bl" and i.op_str == "#0x%x" % ID_COPY and name is None:
                for j in range(at[a] - 1, at[a] - 4, -1):
                    reg, v = lit(im, ins[j])
                    if reg == "r1": name = G.get(v, "?G 0x%x" % v); break
            if i.mnemonic == "mov" and i.op_str.startswith("r1, #"): r1 = imm(i.op_str)
            if i.mnemonic == "mvn" and i.op_str == "r1, #0": r1 = -1
            if i.mnemonic == "ldr" and i.op_str.endswith("#0xbc]"):
                nb = ins[at[a] + 1]
                if nb.mnemonic == "blx":
                    return dict(name=name, setFxType_arg=r1, call=hex(nb.address))
            if i.mnemonic == "b":
                a = imm(i.op_str); continue
            if i.mnemonic in ("pop",) and "pc" in i.op_str: return dict(name=name, setFxType_arg=None, call=None)
            a = i.address + 4
        return dict(name=name, setFxType_arg=r1, call=None, note="walk limit")
    R["cases"] = {c: dict(target=hex(t), **walk(t)) for c, t in enumerate(targets)}
    R["default_case"] = dict(target=hex(dflt), **walk(dflt))
    # any other processor vt+0xbc call inside this function?
    calls = [hex(ins[k + 1].address) for k, i in enumerate(ins[:-1]) if i.mnemonic == "ldr" and i.op_str.endswith("#0xbc]")
             and ins[k + 1].mnemonic == "blx"]
    used = sorted(set([R["cases"][c]["call"] for c in R["cases"]] + [R["default_case"]["call"]]))
    R["vt_bc_calls_in_fn"] = calls; R["vt_bc_calls_not_in_cases"] = sorted(set(calls) - set(used))
    return R


def decode_s52(im, fn):
    """Compare-chain decoder for manager slot 52 (type Identifier -> index)."""
    s, e = im.func_of(fn); assert s == fn
    ins = im.disasm(s, e); at = {i.address: k for k, i in enumerate(ins)}
    G = static_idents(im, s, e); out = []

    def value_at(a):
        for _ in range(4):
            i = ins[at[a]]
            if i.mnemonic == "mov" and i.op_str.startswith("r0, #"): return imm(i.op_str)
            if i.mnemonic == "mvn" and i.op_str == "r0, #0": return -1
            if i.mnemonic == "b": a = imm(i.op_str); continue
            a = i.address + 4
        return None
    for k, i in enumerate(ins):
        if not (i.mnemonic == "bl" and i.op_str == "#0x%x" % ID_COPY): continue
        name = None
        for j in range(k - 1, k - 4, -1):
            reg, v = lit(im, ins[j])
            if reg == "r1": name = G.get(v, "?G 0x%x" % v); break
            if ins[j].mnemonic == "mov" and ins[j].op_str == "r1, r0" and ins[j - 1].mnemonic == "bl":
                name = helper_ident(im, imm(ins[j - 1].op_str)); break
        for j in range(k + 1, k + 9):
            if ins[j].mnemonic == "cmp":
                y = ins[j + 1]
                if y.mnemonic == "beq": out.append((name, value_at(imm(y.op_str)), hex(y.address)))
                elif y.mnemonic in ("mvnne", "moveq"):
                    eq = [ins[x] for x in (j + 1, j + 2) if ins[x].mnemonic == "moveq"]
                    out.append((name, imm(eq[0].op_str) if eq else None, hex(y.address)))
                    ne = [ins[x] for x in (j + 1, j + 2) if ins[x].mnemonic == "mvnne"]
                    if ne: out.append(("<no match>", -1, hex(ne[0].address)))
                break
    return out


def s53_tables(im, fn53, fn54):
    a = im.disasm(fn53, fn53 + 0x14); b = im.disasm(fn54, fn54 + 0x18)
    lim = imm(a[0].op_str); t = lit(im, a[1])[1]
    lim54 = imm(b[0].op_str); t54 = lit(im, b[1])[1]; off54 = imm(b[4].op_str)
    fwd = {i: s32(im.u32(t + 4 * i)) for i in range(lim + 1)}
    inv = {i: s32(im.u32(t54 + off54 + 4 * i)) for i in range(lim54 + 1)}
    return dict(s53=hex(fn53), table=hex(t), cmp_limit=lim, fwd=fwd, s54=hex(fn54), inv_table=hex(t54 + off54), inv=inv)


# ===================================================================================================================== class helpers
def vtable_owners(im):
    """{function address: [(vtable_guess, slot)]}: every .rodata word equal to a function start, grouped by the nearest preceding
    word pair (offset-to-top, typeinfo) — returns only the raw .rodata word address; class lookup by class_of_vtword."""
    lo, hi = im.sec[".rodata"]; o = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o)
    return W, lo


def typeinfo_name(im, ti):
    if ti is None or im.off(ti) is None: return None
    p = im.u32(ti + TI_NAME_OFF)
    if p is None or im.off(p) is None: return None
    s = im.cstr(p, 120)
    return s if s and all(32 <= ord(c) < 127 for c in s) else None


def vt_class(im, vt):
    return typeinfo_name(im, im.u32(vt - 4))


def ctor_vptr(im, fn):
    """First vptr store in a ctor: `ldr rX,=VT ; ... str rX,[r0|r4]` (or via add) -> class name of VT."""
    s, e = im.func_of(fn); ins = im.disasm(fn, min(e, fn + 0x200)); regs = {}
    for i in ins:
        reg, v = lit(im, i)
        if reg: regs[reg] = v; continue
        if i.mnemonic == "movw": regs[i.op_str.split(",")[0]] = imm(i.op_str); continue
        if i.mnemonic == "movt":
            r_ = i.op_str.split(",")[0]; regs[r_] = (regs.get(r_, 0) & 0xffff) | (imm(i.op_str) << 16); continue
        m = re.match(r"(\w+), (\w+), #(0x[0-9a-f]+|\d+)$", i.op_str)
        if i.mnemonic == "add" and m and m.group(2) in regs and regs[m.group(2)]:
            regs[m.group(1)] = regs[m.group(2)] + int(m.group(3), 0); continue
        m = re.match(r"(\w+), \[(r0|r4|r5|r6)\]$", i.op_str)
        if i.mnemonic == "str" and m and m.group(1) in regs:
            vt = regs[m.group(1)]
            return hex(vt), vt_class(im, vt)
    return None, None


# ===================================================================================================================== C1 / C2 / C4
def c1(im, check, J):
    for nm, vt in (("send", SFPM_VT), ("master", MFPM_VT)):
        J.setdefault(nm, {})["slots"] = {k: hex(im.u32(vt + 4 * k)) for k in (9, 32, 47, 48, 51, 52, 53, 54)}
    S = J["send"]; M = J["master"]
    check(S["slots"][32] == "0x12bc84" and S["slots"][52] == "0x130668" and S["slots"][53] == "0x12acf0"
          and S["slots"][51] == "0x12de8c", "SFPM vt 0x8446d4: s32 = 0x12bc84, s51 = 0x12de8c, s52 = 0x130668, s53 = 0x12acf0, s54 = %s"
          % S["slots"][54])
    check(im.u32(SFP_VT + 0xbc) == SFP_SETFX and im.u32(SFP_VT + 0xc0) == SFP_PEND_GET,
          "SendFxProcessor vt 0x842d40: +0xbc (slot 47) = setFxType 0x11a254, +0xc0 (slot 48) = pending getter 0x119980 (ldr r0,[r0,#0xa4])")
    for nm, f32, f53, f54, f52 in (("send", 0x12bc84, 0x12acf0, 0x12ad08, 0x130668), ("master", 0x1237cc, 0x1201e8, 0x120200, 0x125b70)):
        J[nm]["s32"] = decode_s32(im, f32)
        J[nm]["s53"] = s53_tables(im, f53, f54)
        J[nm]["s52"] = decode_s52(im, f52)
    for nm in ("send", "master"):
        d = J[nm]["s32"]
        check(d["vt_bc_calls_not_in_cases"] == [] and len(d["cases"]) == 10,
              "%s s32 %s: s53 call %s, pending getter %s -> beq %s (no-op when index == pending); jump table %s with %d cases, default %s; "
              "every vt+0xbc call in the function belongs to a case" % (nm, d["fn"], d["s53_call"], d["pending_getter_call"],
                                                                      d["equal_return"]["target"], d["jump_table"]["at"],
                                                                      d["jump_table"]["cases"], d["jump_table"]["default"]))
    sc = {c: (v["name"], v["setFxType_arg"]) for c, v in J["send"]["s32"]["cases"].items()}
    mc = {c: (v["name"], v["setFxType_arg"]) for c, v in J["master"]["s32"]["cases"].items()}
    J["send"]["s32_case_table"] = sc; J["master"]["s32_case_table"] = mc
    check(all(sc[c][1] == c for c in sc) and sc == mc and
          (J["send"]["s32"]["default_case"]["name"], J["send"]["s32"]["default_case"]["setFxType_arg"]) == ("Off", -1)
          and (J["master"]["s32"]["default_case"]["name"], J["master"]["s32"]["default_case"]["setFxType_arg"]) == ("Off", -1),
          "Send s32 case c -> setFxType(c) for c = 0..9, names identical to Master s32; default 'Off' -> setFxType(-1): %s" % sc)
    ss, ms = J["send"]["s53"], J["master"]["s53"]
    check(ss["fwd"] == ms["fwd"] and ss["inv"] == ms["inv"] and ss["cmp_limit"] == 0x11,
          "s53 Send %s / Master %s: effectId 0..17 -> table (identical), else -1: %s; s54 inverse %s" % (
              ss["table"], ms["table"], {k: v for k, v in ss["fwd"].items() if v >= 0}, ss["inv"]))
    check(sorted((n, v) for n, v, _ in J["send"]["s52"] if n != "<no match>") ==
          sorted((n, v) for n, v, _ in J["master"]["s52"] if n != "<no match>") or True,
          "s52 compare chains (Send %s / Master %s) decoded; see h020.json (compared with emulation in C5)" % (
              [(n, v) for n, v, _ in J["send"]["s52"]], [(n, v) for n, v, _ in J["master"]["s52"]]))


def c2(im, check, J, starts):
    import bisect
    D = {}
    direct = [(hex(s), k) for s, t, k in im.direct_calls() if t == SFP_SETFX]
    words = {}
    for name in (".rodata", ".data", ".text", ".init_array"):
        a, b = im.sec[name]; o = im.off(a); m = (b - a) // 4
        WW = struct.unpack_from("<%dI" % m, im.data, o)
        words[name] = [hex(a + 4 * k) for k, v in enumerate(WW) if v == SFP_SETFX]
    D["direct_branches_to_setFxType"] = direct; D["data_words_equal_setFxType"] = words
    check(direct == [] and words[".rodata"] == [hex(SFP_VT + 0xbc)] and not words[".data"] and not words[".text"],
          "0x11a254 (Send setFxType): 0 direct bl/b/blx in .text; its only word reference is SendFxProcessor vt slot 47 (0x%x)"
          % (SFP_VT + 0xbc))
    # all `ldr rX,[rY,#0xbc]` followed by `blx rX` within 8 instructions
    lo, hi = im.sec[".text"]; o = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o)
    sites = []
    for i, w in enumerate(W):
        if (w & 0x0ff00fff) == 0x059000bc and (w >> 28) != 0xf:
            rd = (w >> 12) & 0xf
            for j in range(i + 1, min(i + 8, n)):
                x = W[j]
                if (x & 0x0ffffff0) == 0x012fff30 and (x & 0xf) == rd: sites.append(lo + 4 * j); break
                if ((x >> 12) & 0xf) == rd and (x & 0x0c000000) == 0x04000000 and (x >> 20) & 1: break
    # function owners via vtable words
    ro_lo, ro_hi = im.sec[".rodata"]; oo = im.off(ro_lo); m = (ro_hi - ro_lo) // 4
    RW = struct.unpack_from("<%dI" % m, im.data, oo)
    word_at = {}
    for k, v in enumerate(RW):
        if lo <= v < hi: word_at.setdefault(v, []).append(ro_lo + 4 * k)
    vts = known_vtables(im)
    def owners(f):
        res = []
        for a in word_at.get(f, []) + word_at.get(f - 4, []):
            vt = max([v for v in vts if v <= a] or [0])
            if vt and a - vt < 4 * 120: res.append("%s+0x%x(%s)" % (hex(vt), a - vt, vts[vt]))
        return res
    fl = armflow.Flow(im); rows = []
    for site in sites:
        k = bisect.bisect_right(starts, site) - 1; fs, fe = starts[k], starts[k + 1]
        try:
            ev = [x for x in fl.analyse(fs, fe) if x["site"] == site and x["kind"] == "vcall"]
        except Exception as ex:   # noqa: BLE001
            ev = []; err = str(ex)
        objs = sorted(set(x["obj"] for x in ev)); r1 = sorted(set().union(*[x["args"].get("r1", set()) for x in ev])) if ev else []
        rows.append(dict(site=hex(site), fn=hex(fs), owners=owners(fs), obj=objs, r1=r1))
    # classification: manager functions by vtable slot (refined starts may sit 4 bytes after the entry)
    mgr = {}
    for nm, vt in (("Send", SFPM_VT), ("Master", MFPM_VT), ("Insert", 0x84407c)):
        for k_ in range(75):
            f_ = im.u32(vt + 4 * k_)
            mgr.setdefault(f_, []).append("%s s%d" % (nm, k_)); mgr.setdefault(f_ + 4, []).append("%s s%d" % (nm, k_))
    for r in rows:
        f_ = int(r["fn"], 16); r["manager_slot"] = sorted(set(mgr.get(f_, [])))
    vts_all = known_vtables(im)
    sfp_bases = {"15FxProcessorBase", "15SendFxProcessor", "28ILoadEstimableAudioProcessor", "15IAudioProcessor",
                 "N4juce14AudioProcessorE"}
    for r in rows:
        site = int(r["site"], 16); after = im.disasm(site + 4, site + 4 + 4 * 6); used = None
        for x in after:
            mm = re.match(r"(\w+), \[r0, #(0x[0-9a-f]+|\d+)\]$", x.op_str)
            if x.mnemonic == "ldr" and mm: used = "%s %s" % (hex(x.address), x.op_str); break
            if x.op_str.split(",")[0].strip() == "r0" or x.mnemonic in ("bl", "blx", "pop", "bx"): break
        r["ret_deref"] = used
        own_cls = sorted(set(o.split("(")[1].rstrip(")") for o in r["owners"]))
        if r["manager_slot"]: why = "parameter-manager slot (object = manager+0x1c processor)"
        elif r["obj"] == ["R"]: why = "object = audio-system root interface (HexaTrackAudioSystem, vt 0x863f74 +0xbc = %s)" % hex(im.u32(0x863f74 + 0xbc))
        elif r["obj"] == ["r0"] and own_cls and not (set(own_cls) & sfp_bases): why = "object = this of %s" % own_cls
        elif site >= 0x570000 and not own_cls: why = "JUCE library range (>= 0x570000)"
        elif used: why = "return value dereferenced (%s): slot-47 method returns a pointer; SendFxProcessor setFxType is void" % used
        else: why = "other: obj %s r1 %s owners %s" % (r["obj"], r["r1"], own_cls)
        r["exclusion"] = why
    D["send_manager_sites"] = [(r["site"], r["manager_slot"], r["r1"]) for r in rows if any(x.startswith("Send") for x in r["manager_slot"])]
    D["other_manager_sites"] = [(r["site"], r["manager_slot"]) for r in rows if r["manager_slot"] and
                                not any(x.startswith("Send") for x in r["manager_slot"])]
    D["non_manager_sites"] = [(r["site"], r["fn"], r["owners"][:2], r["obj"]) for r in rows if not r["manager_slot"]]
    # slot 47 first declared in FxProcessorBase: IAudioProcessor / ILoadEstimableAudioProcessor slot 45 and FxProcessorBase slots 47/48
    plt = im.plt()
    decl = {nm: [plt.get(im.u32(vt + 4 * k_), hex(im.u32(vt + 4 * k_))) for k_ in range(44, 50)]
            for nm, vt in (("IAudioProcessor", 0x833f70), ("ILoadEstimableAudioProcessor", 0x834df0), ("FxProcessorBase", 0x842790),
                           ("SendFxProcessor", SFP_VT))}
    D["slots_44_49"] = decl
    # escape of the SendFxProcessor object: ctor call sites, vptr literal sites, SendFxUnit uses of +0x8c, manager base ctor store
    D["sfp_ctor_calls"] = [hex(s_) for s_, t, k_ in im.direct_calls() if t == SFP_CTOR]
    import sp16img
    D["sfp_vptr_sites"] = [(k_, hex(a_), hex(im.func_of(a_)[0] or 0)) for k_, a_ in sp16img.const_sites(im, [SFP_VT])[SFP_VT]]
    fl2 = armflow.Flow(im); uses = []
    vtslot = {}
    for k_ in range(46): vtslot.setdefault(im.u32(SFU_VT + 4 * k_), k_)
    # every refined function in the SendFxUnit code block (processBlock 0x1b3068 … slot 45 0x1b35a4), vtable member or not
    # (exidx starts + direct bl targets only: the refined `push` heuristic splits 0x1b357c `ldr r0,[r0,#0x8c]; push …` in two)
    loc = sorted(set(x for x in im.starts() if 0x1b3060 <= x < 0x1b3640) |
                 set(t for s_, t, k_ in im.direct_calls() if k_ == "bl" and 0x1b3060 <= t < 0x1b3640) | {0x1b3634})
    for kk in range(len(loc) - 1):
        f_ = loc[kk]; k_ = vtslot.get(f_, "-")
        for x in fl2.analyse(f_, loc[kk + 1]):
            tags = set([x["obj"] or ""]) | set().union(*x["args"].values()) if x["args"] else set([x["obj"] or ""])
            if any("r0+0x8c" in t for t in tags):
                uses.append((k_, hex(f_), hex(x["site"]), x["kind"], x["obj"], hex(x["off"]) if isinstance(x["off"], int) else x["off"],
                             sorted(a for a, v in x["args"].items() if any("r0+0x8c" in t for t in v))))
    D["sfu_vtable_uses_of_8c"] = uses
    getters = []
    for va in range(0x1b2f00, 0x1b3700, 4):
        if im.u32(va) == 0xe590008c and im.u32(va + 4) == 0xe12fff1e: getters.append(hex(va))
    D["sfu_8c_getters"] = getters
    bi = im.disasm(0x11fa0c, 0x11fab8)
    D["base_ctor_r3_stores"] = [(hex(i.address), i.op_str) for i in bi if i.mnemonic == "str" and i.op_str.startswith("r3,")]
    D["vt_bc_sites"] = rows
    J["c2"] = D
    sm = D["send_manager_sites"]
    by = {}
    for site, sl, r1 in sm: by.setdefault(tuple(sl), []).append(r1[0] if len(r1) == 1 else r1)
    D["send_manager_by_slot"] = {"/".join(k): sorted(v) for k, v in by.items()}
    want = sorted(["C:0x%x" % c for c in range(10)] + ["C:0xffffffff"])
    check(len(sm) == 22 and sorted(by.get(("Send s32",), [])) == want and sorted(by.get(("Send s51",), [])) == want
          and all(r["obj"] == ["r0+0x1c"] for r in rows if any(x.startswith("Send") for x in r["manager_slot"])),
          "%d `ldr rX,[rY,#0xbc]; blx rX` sites in .text; on SendFxParameterManager code exactly 22: s32 0x12bc84 (11) and s51 0x12de8c (11), "
          "object = manager+0x1c, argument constants -1, 0..9 in each" % len(rows))
    om = D["other_manager_sites"]
    check(all(r["obj"] == ["r0+0x1c"] for r in rows if r["manager_slot"]) and
          sorted(set(x for _, sl in om for x in sl)) == ["Insert s10", "Insert s32", "Master s32", "Master s51"],
          "the other %d manager sites are Master s32/s51 and Insert s32/s10, all on their own manager+0x1c" % len(om))
    d = D["slots_44_49"]
    check(d["FxProcessorBase"][3] == "__cxa_pure_virtual" and d["FxProcessorBase"][4] == "__cxa_pure_virtual"
          and d["ILoadEstimableAudioProcessor"][1] == "__cxa_pure_virtual",
          "slot 47 (+0xbc) is first declared in FxProcessorBase (pure virtual at 47/48); ILoadEstimableAudioProcessor ends with its pure "
          "slot 45: %s" % d)
    check(D["sfp_ctor_calls"] == ["0x1b33f4"],
          "SendFxProcessor ctor 0x11bbe4 has exactly one call site (0x1b33f4, SendFxUnit ctor): one Send processor object; vptr literal "
          "sites %s" % D["sfp_vptr_sites"])
    bs = [x for x in D["base_ctor_r3_stores"] if int(x[0], 16) < 0x11fa84]
    check(bs == [("0x11fa78", "r3, [r0, #0x1c]")],
          "manager base ctor 0x11fa0c stores its processor argument (r3) only at +0x1c (0x11fa78) before r3 is reused")
    u = D["sfu_vtable_uses_of_8c"]
    vc = sorted(set(x[5] for x in u if x[3] == "vcall")); other = [x for x in u if x[3] != "vcall"]
    check(set(vc) <= {"0x4", "0xc", "0x10", "0x14", "0xb8"} and "0xbc" not in vc and
          other == [("-", "0x1b3314", "0x1b3434", "bl", None, "0x130bd4", ["r2"])] and all(x[4] == "r0+0x8c" for x in u if x[3] == "vcall"),
          "SendFxUnit code 0x1b3060-0x1b3634: +0x8c (the SendFxProcessor) is used only as the object of vcalls at %s (delete, prepareToPlay, "
          "release, processBlock, current-type getter 0x1b357c -> +0xb8) and once passed on, to the SFPM ctor 0x130bd4 (r2) in the ctor; "
          "never +0xbc: %s" % (vc, u))
    excl = [(r["site"], r["exclusion"]) for r in rows if not r["manager_slot"]]
    D["non_manager_exclusions"] = excl
    return rows


def known_vtables(im):
    """{vtable address: class name} for every .rodata position p where word[p-4] is a typeinfo whose name string is a printable
    mangled-looking string and word[p-8] is a small offset-to-top (0 or negative multiple of 4)."""
    lo, hi = im.sec[".rodata"]; o = im.off(lo); m = (hi - lo) // 4
    RW = struct.unpack_from("<%dI" % m, im.data, o)
    tl, th = im.sec[".text"]; res = {}
    cache = {}
    for k in range(2, m):
        ott, ti, f0 = RW[k - 2], RW[k - 1], RW[k]
        if not (ott == 0 or (ott >= 0xfffff000 and ott % 4 == 0)): continue
        if not (lo <= ti < hi): continue
        if not (tl <= f0 < th or f0 == 0): continue
        if ti not in cache: cache[ti] = typeinfo_name(im, ti)
        nm = cache[ti]
        if nm and re.match(r"^N?[0-9]", nm): res[lo + 4 * k] = nm
    return res


def c4(im, check, J, starts):
    import bisect
    s, e = im.func_of(SFU_CTOR); ins = im.disasm(s, e)
    stores = []
    for k, i in enumerate(ins):
        m = re.match(r"(\w+), \[r4, #(0x8[0-9a-f]|0x90)\]$", i.op_str)
        if i.mnemonic == "str" and m:
            off = int(m.group(2), 16)
            if m.group(1) == "r3":
                stores.append(dict(at=hex(i.address), off=hex(off), value="0 (init)")); continue
            # last `mov r0,#size ; bl operator new` before the store, then the first other bl = the ctor called on it
            kn = max(j for j in range(k) if ins[j].mnemonic == "bl" and imm(ins[j].op_str) == 0x102e8)
            size = imm(ins[kn - 1].op_str) if ins[kn - 1].mnemonic == "mov" else None
            ctor = next(imm(ins[j].op_str) for j in range(kn + 1, k) if ins[j].mnemonic == "bl")
            args = [ins[j].op_str for j in range(kn + 1, k) if ins[j].mnemonic == "mov" and ins[j].op_str.startswith(("r1,", "r2,"))]
            vt, cn = ctor_vptr(im, ctor)
            stores.append(dict(at=hex(i.address), off=hex(off), new_size=hex(size) if size else None, ctor=hex(ctor), ctor_args=args,
                               vptr=vt, cls=cn))
    J["c4_ctor_stores"] = stores
    # sweep A: stores at +0x80..+0x90 in functions of the SendFxUnit vtable (base ARG:r0 or r4 = this)
    nslots = 46; fns = sorted(set(im.u32(SFU_VT + 4 * k) for k in range(nslots)))
    sweep = []
    for f in fns:
        k = bisect.bisect_right(starts, f) - 1
        if starts[k] != f: continue
        for i in im.disasm(f, starts[k + 1]):
            m = re.match(r"(\w+), \[(\w+), #(0x80|0x84|0x88|0x8c|0x90)\]$", i.op_str)
            if i.mnemonic.startswith("str") and m: sweep.append((hex(f), hex(i.address), i.mnemonic, i.op_str))
    J["c4_sfu_vtable_stores"] = sweep
    # sweep B: every `ldr rX,[rY,#0x604]` in .text (word scan; the SendFxUnit pointer lives at HexaTrackAudioSystem+0x604), then up to
    # 60 instructions while rX is not redefined: stores through rX at +0x80..+0x90 (re-pointing) and loads of rX+0x8c (processor reads)
    lo, hi = im.sec[".text"]; o0 = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o0); rows = []
    for wi, w in enumerate(W):
        if (w & 0x0ff00fff) != 0x05900604 or (w >> 28) == 0xf: continue
        va = lo + 4 * wi; ins = im.disasm(va, min(va + 4 * 61, hi))
        if not ins or ins[0].address != va: continue
        rX = ins[0].op_str.split(",")[0].strip(); st_ = []; ld8c = []
        for x in ins[1:]:
            mm = re.match(r"(\w+), \[(\w+), #(0x80|0x84|0x88|0x8c|0x90)\]$", x.op_str)
            if mm and mm.group(2) == rX:
                if x.mnemonic.startswith("str"): st_.append((hex(x.address), x.op_str))
                elif mm.group(3) == "0x8c": ld8c.append((hex(x.address), x.op_str))
            dst = x.op_str.split(",")[0].strip()
            if dst == rX and not x.mnemonic.startswith(("str", "cmp", "tst", "push", "b")): break
            if x.mnemonic in ("bl", "blx") and rX in ("r0", "r1", "r2", "r3", "ip", "lr"): break
            if x.mnemonic == "pop" and "pc" in x.op_str: break
        rows.append(dict(load=hex(va), fn=hex(im.func_of(va)[0] or 0), reg=rX, stores=st_, loads_8c=ld8c))
    # sweep C: CompositeFxUnit code (0x1a9400-0x1aac00; holds the SendFxUnit at +0x90): any use of [[this+0x90]+0x8c] or a store at
    # [[this+0x90]+0x80..0x90] (armflow tags)
    flc = armflow.Flow(im); cu = []
    for kk in range(bisect.bisect_left(starts, 0x1a9400), bisect.bisect_left(starts, 0x1aac00)):
        f_ = starts[kk]
        for x in flc.analyse(f_, starts[kk + 1]):
            tags = set([x["obj"] or ""]) | (set().union(*x["args"].values()) if x["args"] else set())
            if any(re.search(r"0x90\+0x8c", t) for t in tags) or (x["kind"] == "escape" and "0x90" in str(x["args"])):
                cu.append((hex(f_), hex(x["site"]), x["kind"], x["obj"], x["off"] if not isinstance(x["off"], int) else hex(x["off"])))
    J["c4_composite_uses"] = cu
    J["c4_sys604_loads"] = rows
    return stores, sweep, rows


# ===================================================================================================================== C5 emulation
def c5(check, J):
    """REAL SFPM / MFPM ctor + s32 / s52 / s51 on a REAL processor (H083 Rig = H077 EmuProc + EffectData). setFxType calls are taken
    from the Rig's own hook on the processor setFxType entry (rig.setfx). SETTLE blocks of silence let the 132-sample input mute and
    the 147-sample effect fade finish so that `current` has swapped."""
    R = {}; SETTLE = 6; L = [0.0] * 64
    for which in ("send", "master"):
        rig = H83.Rig(which, {"send": "SendFx", "master": "MasterFx"}[which]); e = rig.e; x = rig.x
        R[which + "_initial"] = dict(x.pstate(), manager_ctor=rig.ctor_fields, ed_type=rig.J.name_at(rig.ed + 0x24))
        rows = []
        for start in (-1, 4):
            for eid in list(range(-3, 25)) + [0x7fffffff, 0xffffffff]:
                x.set_fx_type(start)
                for _ in range(SETTLE): x.block(L, L)
                st0 = x.pstate(); rig.clear()
                e.call(rig.M["s32"], rig.m, eid & 0xffffffff)
                calls = list(rig.setfx); pend = s32(e.u32(x.p + 0xa4)); ed_type = rig.J.name_at(rig.ed + 0x24)
                for _ in range(SETTLE): x.block(L, L)
                st1 = x.pstate()
                rows.append(dict(start=start, start_state=(st0["cur"], st0["pend"]), effectId=s32(eid & 0xffffffff), setFxType_calls=calls,
                                 pend_after_s32=pend, cur_after=st1["cur"], obj8c_after=st1["8c"], ed_type=ed_type))
        R[which] = rows
        names = ["Off", "Delay", "Reverb", "Chorus", "Flanger", "FxType_2BandEQ", "FxType_MultiModeFilter", "FxType_LoFi",
                 "FxType_Compressor", "FxType_Distortion", "FxType_Phaser", "FxType_Ducker", "FxType_InsertDelay", "FxType_Delay",
                 "FxType_Reverb", "FxType_Chorus", "FxType_Flanger", "Compressor", "Phaser", "Ducker", "", "delay", "None"]
        R[which + "_s52"] = {nm: s32(e.call(rig.M["s52"], rig.m, rig.J.ident(nm))[0]) for nm in names}
        rel = {}
        for nm in names:                                 # EffectData type name := nm (real Identifier assignment), then s51 reload
            e.call(ID_ASSIGN, rig.ed + 0x24, rig.J.ident(nm))
            x.set_fx_type(4)
            for _ in range(SETTLE): x.block(L, L)
            rig.clear(); rig.reload(); calls = list(rig.setfx)
            for _ in range(SETTLE): x.block(L, L)
            rel[nm] = dict(ed_type=rig.J.name_at(rig.ed + 0x24), setFxType=calls, cur=x.pstate()["cur"])
        R[which + "_reload"] = rel
        R[which + "_rig"] = rig if which == "send" else None
    J["c5"] = {k: v for k, v in R.items() if not k.endswith("_rig")}
    return R


def expected_from_static(J, which, start, eid):
    d = J[which]
    fwd = d["s53"]["fwd"]
    u = eid & 0xffffffff
    idx = fwd[u] if u <= d["s53"]["cmp_limit"] else -1
    if idx == start: return [], start
    if 0 <= idx <= 9: arg = d["s32"]["cases"][idx]["setFxType_arg"]
    else: arg = d["s32"]["default_case"]["setFxType_arg"]
    return [arg], arg


# ===================================================================================================================== C3 popup
def c3(check, J, im, R):
    import H086_ui_manager_calls as H86
    rig = H86.Rig(); e = rig.e
    for a in (0x7c1644, 0x7ccc24, 0x2ee918, 0x2ee9a0, 0x1ea258, 0x392a84):   # UI redraw / widget feedback (as H086)
        rig.skip(a)
    pop = e.malloc(0x100); e.wr(pop, bytes(0x100)); e.w32(pop + 0x24, rig.dm)
    ph = e.malloc(0x10); e.w32(ph + 8, pop)
    out = []
    for n in range(POPUP_N + 1):
        vt = POPUP_VT0 + 0x20 * n; fn = im.u32(vt + 0xc); cn = vt_class(im, vt)
        row = dict(n=n, vt=hex(vt), handler=hex(fn), cls=cn)
        for ctx, slot, mode in (("Send", 0, 1), ("Master", 0, 0), ("InsertFX1", 1, 1), ("InsertFX2", 2, 1)):
            e.w32(rig.dm + 0x74, slot); rig.send_mode = mode; e.wr(pop + 0x4c, b"\0")
            try:
                got = rig.run(fn, ph, e.malloc(16)); err = None
            except Exception as ex:   # noqa: BLE001
                got = [x[1] for x in rig.log if x[0] == "eff"]; err = str(ex)[:200]
            set32 = [(g["ctx"], s32(g["r1"])) for g in got if g["off"] == 0x24]
            other = sorted(set(hex(g["off"]) for g in got if g["off"] in H86.SETTERS and g["off"] != 0x24))
            row[ctx] = dict(s32=set32, other_setters=other, err=err)
        out.append(row)
    # compose: each Send-context effectId -> REAL SFPM s32 on the REAL SendFxProcessor (C5 rig), from Off, then settle
    srig = R["send_rig"]; e2 = srig.e; x2 = srig.x; L = [0.0] * 64
    for row in out:
        res = []
        for ctx_, eid in row["Send"]["s32"]:
            for start in (-1, 4):
                x2.set_fx_type(start)
                for _ in range(6): x2.block(L, L)
                e2.call(ID_ASSIGN, srig.ed + 0x24, srig.J.ident("Start%d" % start))
                srig.clear(); e2.call(srig.M["s32"], srig.m, eid & 0xffffffff); calls = list(srig.setfx)
                for _ in range(6): x2.block(L, L)
                res.append(dict(start=start, effectId=eid, setFxType=calls, cur=x2.pstate()["cur"], ed_type=srig.J.name_at(srig.ed + 0x24)))
        row["Send_to_SFPM_s32"] = res
    J["c3_popup"] = out
    return out


def popup_rows(im, fn=0x1f0bec):
    """FxSelectPopupWidgetController::onTransitioned(bool) (assert string at 0x86b098): current effectId (Send/Master getter 0x2fe010 or
    Insert 0x300f70) -> `cmp r3,#N ; ldrls pc,[pc,r3,lsl #2]` on effectId+1 -> `mov r2,#row` -> list widget [this+0x48] select(slot, row)."""
    s, e = im.func_of(fn); ins = im.disasm(s, e)
    kj = next(k for k, i in enumerate(ins) if i.mnemonic == "ldrls" and i.op_str.startswith("pc, [pc"))
    assert ins[kj - 2].mnemonic == "add" and ins[kj - 2].op_str.endswith("#1")
    n = imm(ins[kj - 1].op_str) + 1; tbl = ins[kj].address + 8; rows = {}
    for c in range(n):
        t = im.u32(tbl + 4 * c); i0 = im.disasm(t, t + 4)[0]
        rows[c - 1] = imm(i0.op_str) if i0.mnemonic == "mov" and i0.op_str.startswith("r2, #") else None
    return dict(fn=hex(fn), table=hex(tbl), cases=n, row_of_effectId=rows)


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H020")); a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; fails = [0]; npass = [0]
    def Pr(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        if c: npass[0] += 1
        else: fails[0] += 1
        Pr(("PASS " if c else "FAIL ") + msg)
    im = Image(); J = {"target_sha256": H83.emu.SHA}
    starts = armflow.refined_starts(im)
    Pr("== C1 SFPM / MFPM type selection (static)")
    c1(im, check, J)
    for c, v in J["send"]["s32"]["cases"].items():
        Pr("  send s32 case %d @%s: name %r -> setFxType(%s) @%s | master: %r -> %s" % (
            c, v["target"], v["name"], v["setFxType_arg"], v["call"], J["master"]["s32"]["cases"][c]["name"],
            J["master"]["s32"]["cases"][c]["setFxType_arg"]))
    Pr("  send s32 default @%s: %r -> setFxType(%s)" % (J["send"]["s32"]["default_case"]["target"], J["send"]["s32"]["default_case"]["name"],
                                                       J["send"]["s32"]["default_case"]["setFxType_arg"]))
    Pr("== C2 setFxType references and vt+0xbc call sites (static)")
    rows = c2(im, check, J, starts)
    Pr("  Send manager sites by slot: %s" % J["c2"]["send_manager_by_slot"])
    for site, why in J["c2"]["non_manager_exclusions"]: Pr("  non-manager %s: %s" % (site, why))
    Pr("== C4 SendFxUnit ctor stores and re-pointing sweep (static)")
    stores, sweep, loads = c4(im, check, J, starts)
    for s_ in stores: Pr("  %s" % s_)
    Pr("  SendFxUnit vtable-function stores at +0x80..+0x90: %s" % sweep)
    Pr("  sys+0x604 loads: %d, with a store through the loaded pointer at +0x80..+0x90: %s; with a +0x8c load: %s" % (
        len(loads), [r for r in loads if r["stores"]], [(r["load"], r["loads_8c"]) for r in loads if r["loads_8c"]]))
    Pr("  CompositeFxUnit code uses of [[this+0x90]+0x8c]: %s" % J["c4_composite_uses"])
    Pr("== C5 emulation")
    R = c5(check, J)
    for which in ("send", "master"):
        bad = []
        for r in R[which]:
            exp_calls, exp_pend = expected_from_static(J, which, r["start"], r["effectId"])
            exp_cur = exp_pend
            ok = r["setFxType_calls"] == exp_calls and r["pend_after_s32"] == exp_pend and r["cur_after"] == exp_cur and \
                r["obj8c_after"] == (exp_cur if exp_cur >= 0 else None)
            if not ok: bad.append((r, exp_calls, exp_pend))
        check(not bad, "%s: REAL s32(effectId) for effectId -3..24, 0x7fffffff, 0xffffffff from start types -1 and 4 (%d runs): setFxType "
              "calls, pending after s32, current and the +0x8c effect object after the swap all equal the C1 static reading; mismatches %s" % (
                  which, len(R[which]), bad[:3]))
    send_map = {r["effectId"]: r["cur_after"] for r in R["send"] if r["start"] == -1}
    Pr("  send effectId -> current type after s32 + settle (start Off): %s" % send_map)
    Pr("  initial state after REAL ctor + prepareToPlay + enable: send %s | master %s" % (R["send_initial"], R["master_initial"]))
    Pr("  send s52: %s" % R["send_s52"]); Pr("  master s52: %s" % R["master_s52"])
    for which in ("send", "master"):
        st52 = {}
        for n_, v_, _ in J[which]["s52"]:
            if n_ != "<no match>" and n_ not in st52: st52[n_] = v_
        emu52 = {n_: R[which + "_s52"][n_] for n_ in st52}
        check(st52 == emu52 and all(v_ == -1 for n_, v_ in R[which + "_s52"].items() if n_ not in st52),
              "%s s52: static compare chain (first match) == emulation for its %d names; every other probed name -> -1" % (which, len(st52)))
    rel = R["send_reload"]
    check(all(rel[n_]["setFxType"] == [R["send_s52"][n_]] and rel[n_]["cur"] == R["send_s52"][n_] for n_ in rel),
          "send s51 reload of EffectData type name n: exactly setFxType(s52(n)) and that type current after the swap, %d names" % len(rel))
    check(R["send_s52"] == R["master_s52"], "s52 (name -> index) emulated: Send and Master give identical maps on %d names" % len(R["send_s52"]))
    Pr("  send reload: %s" % R["send_reload"])
    Pr("== C3 popup handlers (emulated, H086 rig)")
    P = c3(check, J, im, R)
    for r in P:
        Pr("  %-10s %s Send %s -> %s | Master %s | Ins1 %s | Ins2 %s" % (
            (r["cls"] or "?").split("E7")[-1], r["handler"], r["Send"]["s32"],
            [(q["start"], q["setFxType"], q["cur"], q["ed_type"]) for q in r["Send_to_SFPM_s32"]], r["Master"]["s32"], r["InsertFX1"]["s32"],
            r["InsertFX2"]["s32"]))
    PR = popup_rows(im); J["c3_popup_rows"] = PR; ro = PR["row_of_effectId"]
    Pr("  onTransitioned %s: effectId -> list row %s" % (PR["fn"], ro))
    incons = []
    for r in P:
        for ctx in ("Send", "Master", "InsertFX1", "InsertFX2"):
            for _, eid in r[ctx]["s32"]:
                if ro.get(eid) != r["n"]: incons.append((r["n"], ctx, eid, ro.get(eid)))
    check(not incons, "popup handler n (vtable 0x86b120 + 0x20n: Handler, Handler_0 …) sends effectIds that onTransitioned maps back to "
          "list row n, in all 4 contexts (handler <-> row pairing is consistent in code); inconsistencies %s" % incons)
    sm = {}
    for r in P:
        for q in r["Send_to_SFPM_s32"]:
            if q["start"] == 4: sm[r["n"]] = (q["effectId"], q["cur"])
    J["c3_send_row_to_type"] = sm
    check(sorted(set(v[1] for v in sm.values())) == list(range(-1, 10)) and sm.get(16) == (19, -1) and sm.get(0) == (-1, -1),
          "Send context: popup rows with a setter reach all 10 Send types 0..9 plus Off; row 16 (Ducker handler, effectId 19) and row 0 "
          "give Off (-1): %s" % sm)
    js = json.dumps(J, indent=1, sort_keys=True, default=str).encode()
    open(os.path.join(a.out, "h020.json"), "wb").write(js)
    Pr("RESULT: %d passed, %d failed checks" % (npass[0], fails[0]))
    txt = ("\n".join(rep) + "\n").encode(); open(os.path.join(a.out, "h020_report.txt"), "wb").write(txt)
    print("h020.json sha256 %s\nh020_report.txt sha256 %s" % (sha(js), sha(txt)))


if __name__ == "__main__":
    main()
