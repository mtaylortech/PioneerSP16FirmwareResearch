#!/usr/bin/env python3
"""H038 — FPSCR write census for the 1.60 main binary and its linked libraries; FZ/DN state of the audio threads (kb/cycles/040.md).

Sections (success criteria of cycle 040):
  C1  main binary census: every executable PT_LOAD of target/EP085_Main_R_fw160
        a) raw bit-pattern scan: ARM words (4-aligned AND every byte offset) matching MCR/MRC to cp10/cp11 with opc1 = 7
           (= VMSR/VMRS to any VFP system register; FPSCR when reg field = 1), and Thumb-2 halfword pairs at every 2-byte offset
           (hw1 0xEEE?/0xFEE? = VMSR/MCR(2), 0xEEF?/0xFEF? = VMRS/MRC(2), hw2 & 0x0E10 = 0x0A10);
        b) capstone linear sweep of the whole range in ARM mode and in Thumb mode (skipdata), every vmsr/vmrs/fmxr/fmrx and every
           mcr/mrc/mcr2/mrc2 naming p10/p11;
        c) per hit: section, containing .ARM.exidx function, whether it is a real instruction of an ARM function (4-aligned, in
           .text inside an exidx extent) or a data / misaligned / wrong-mode decode.
      Also: number of Thumb functions in .ARM.exidx, number of blx-immediate (ARM->Thumb) sites, .ARM.attributes FP tags.
  C2  libraries: DT_NEEDED closure of the main binary, resolved in decoded/lib/ (plus, read-only, the same 1.60 image2 payload lib
      directory for libs missing from decoded/lib/); same census over each library's executable segments, hit -> .symtab function;
      FP-environment imports of the main binary; reachability of each hit function from (i) a main-binary import, (ii) load-time
      code (ld.so entry, DT_INIT / DT_INIT_ARRAY of every lib) through direct bl/blx/b edges and PLT names (over-approximation);
      __fpu_control value in libc and whether the main binary overrides it.
  C3  the thread start path: census hits in pthread_create / start_thread / clone / ld.so; emitted as data for the cycle file.
  C4  emulation: own hand-encoded VFP/NEON instructions (no firmware bytes) on harness/lib/emu.Emu: FPSCR written with reg_write is
      read back by the guest (vmrs) and changes a scalar denormal multiply (FZ=0 keeps 1e-40, FZ=1 flushes); NEON flushes for both.
Outputs only to --out (default harness/out/H038/). Run: .venv/bin/python -B harness/H038_fpscr_census.py [--out DIR]
"""
import argparse, bisect, collections, glob, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import capstone, lief                                          # noqa: E402
import sp16img                                                 # noqa: E402

LIBDIR = os.path.join(ROOT, "decoded", "lib")
EXTRA_LIBDIR = os.environ.get("SP16_IMAGE2_LIBDIR") or os.path.join(ROOT, "decoded", "image2-lib")   # optional, read-only;
# path scrub (research-notes/EDIT-LOG.md): was a private home-relative constant. SP16_IMAGE2_LIBDIR = the lib/ folder of your
# own 1.60 root filesystem, for libraries missing from decoded/lib/; if it does not exist, those libraries are reported absent.
SYSREG = {0: "fpsid", 1: "fpscr", 5: "mvfr2", 6: "mvfr1", 7: "mvfr0", 8: "fpexc", 9: "fpinst", 10: "fpinst2"}
VFP_MNEM = {"vmsr", "vmrs", "fmxr", "fmrx"}
COP_MNEM = {"mcr", "mrc", "mcr2", "mrc2"}


# ------------------------------------------------------------------------------------------------------------------------------
# raw scans
def arm_raw(buf, base, aligned_only):
    """ARM: MCR/MRC cp10/cp11 opc1=7  (cond 1110 111L reg Rt 101x xxx1 xxxx); L=0 write (VMSR), L=1 read (VMRS)."""
    out = []
    step = 4 if aligned_only else 1
    for o in range(0, len(buf) - 3, step):
        w = struct.unpack_from("<I", buf, o)[0]
        if (w & 0x0FE00E10) == 0x0EE00A10:
            # vfp = cp10 (bits 11:8 = 1010) with SBZ bits 7:5, 3:0 zero = architectural VMSR/VMRS; cp11 with opc1 = 7 is the
            # Advanced SIMD VDUP (core) / VMOV (scalar <-> core) space, not a system-register transfer
            vfp = (w & 0x0FE00FFF) == 0x0EE00A10
            out.append((base + o, w, "write" if not (w >> 20) & 1 else "read", (w >> 16) & 0xf, (w >> 12) & 0xf, w >> 28,
                        vfp))
    return out


def thumb_raw(buf, base):
    out = []
    for o in range(0, len(buf) - 3, 2):
        h1, h2 = struct.unpack_from("<HH", buf, o)
        if (h1 & 0xEFE0) == 0xEEE0 and (h2 & 0x0E10) == 0x0A10:
            out.append((base + o, (h1 << 16) | h2, "write" if not (h1 >> 4) & 1 else "read", h1 & 0xf, (h2 >> 12) & 0xf,
                        h1 >> 12, (h1 & 0xFFE0) == 0xEEE0 and (h2 & 0x0FFF) == 0x0A10))
    return out


def sweep(buf, base, thumb):
    """capstone linear sweep with skipdata; returns (n_insn, hits[(addr, mnem, op_str, size)])."""
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if thumb else capstone.CS_MODE_ARM)
    md.skipdata = True
    n = 0; hits = []
    for a, sz, mn, op in md.disasm_lite(buf, base):
        n += 1
        if mn in VFP_MNEM or (mn in COP_MNEM and re.match(r"p1[01],", op)):
            hits.append((a, mn, op, sz))
    return n, hits


# ------------------------------------------------------------------------------------------------------------------------------
# ELF helpers (main + libs)
class Elf:
    def __init__(self, path):
        self.path = path; self.name = os.path.basename(path)
        self.raw = open(path, "rb").read()
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.e = lief.parse(path)
        self.segs = [(s.virtual_address, s.physical_size, s.file_offset, s.has(lief.ELF.Segment.FLAGS.X))
                     for s in self.e.segments if s.type == lief.ELF.Segment.TYPE.LOAD]
        self.secs = sorted((s.virtual_address, s.virtual_address + s.size, s.name) for s in self.e.sections
                           if s.name and s.virtual_address)
        F = {}
        for s in list(self.e.symtab_symbols) + list(self.e.dynamic_symbols):
            if s.type in (lief.ELF.Symbol.TYPE.FUNC, lief.ELF.Symbol.TYPE.GNU_IFUNC) and s.shndx != 0 and s.value:
                a = s.value & ~1
                if a not in F or (s.binding == lief.ELF.Symbol.BINDING.GLOBAL and F[a][2] != "g"):
                    F[a] = (s.name, s.size, "g" if s.binding == lief.ELF.Symbol.BINDING.GLOBAL else "l", s.value & 1)
        self.funcs = F; self.fstarts = sorted(F)
        self.exports = {s.name: s.value & ~1 for s in self.e.dynamic_symbols
                        if s.shndx != 0 and s.value and s.type in (lief.ELF.Symbol.TYPE.FUNC, lief.ELF.Symbol.TYPE.GNU_IFUNC)}
        self.imports = sorted({s.name for s in self.e.dynamic_symbols if s.shndx == 0 and s.name})
        self.plt = self._plt()

    def off(self, va):
        for v, sz, o, _ in self.segs:
            if v <= va < v + sz: return o + va - v
        return None

    def u32(self, va):
        o = self.off(va); return None if o is None else struct.unpack_from("<I", self.raw, o)[0]

    def section(self, va):
        for lo, hi, n in self.secs:
            if lo <= va < hi: return n
        return None

    def func(self, va):
        i = bisect.bisect_right(self.fstarts, va) - 1
        if i < 0: return None
        a = self.fstarts[i]; nm, sz, b, th = self.funcs[a]
        return (a, nm, sz, th) if (sz and va < a + sz) else (a, nm + "+?(beyond size)", sz, th)

    def _plt(self):
        got2name = {r.address: (r.symbol.name if r.has_symbol else "?") for r in self.e.pltgot_relocations}
        res = {}
        if ".plt" not in [n for _, _, n in self.secs]: return res
        lo, hi = [(l, h) for l, h, n in self.secs if n == ".plt"][0]
        rot = lambda w: (((w & 0xff) >> (2 * ((w >> 8) & 0xf))) | ((w & 0xff) << (32 - 2 * ((w >> 8) & 0xf)))) & 0xffffffff \
            if (w >> 8) & 0xf else w & 0xff
        for va in range(lo, hi - 8, 4):
            a, b, c = self.u32(va), self.u32(va + 4), self.u32(va + 8)
            if (a & 0xfffff000) == 0xe28fc000 and (b & 0xfffff000) == 0xe28cc000 and (c & 0xfffff000) == 0xe5bcf000:
                v = (va + 8 + rot(a) + rot(b) + (c & 0xfff)) & 0xffffffff
                if v in got2name:
                    res[va] = got2name[v]
                    if self.u32(va - 4) == 0xe7fd4778 or (self.u32(va - 4) or 0) & 0xffff == 0x4778:   # thumb 'bx pc; nop' prefix
                        res[va - 4] = got2name[v]
        return res

    def exec_ranges(self):
        return [(v, sz, o) for v, sz, o, x in self.segs if x]

    def call_edges(self):
        """{func_start: set(targets)} from direct ARM bl/blx/b and Thumb bl/blx/b.w inside each sized function symbol."""
        E = collections.defaultdict(set)
        for a in self.fstarts:
            nm, sz, b, th = self.funcs[a]
            if not sz: continue
            o = self.off(a)
            if o is None: continue
            buf = self.raw[o:o + sz]
            if not th:
                for k in range(0, len(buf) - 3, 4):
                    w = struct.unpack_from("<I", buf, k)[0]; op = (w >> 24) & 0xf
                    if op not in (0xa, 0xb): continue
                    imm = w & 0xffffff; imm = imm - 0x1000000 if imm & 0x800000 else imm
                    site = a + k
                    t = site + 8 + imm * 4 + (((w >> 23) & 2) if (w >> 28) == 0xf else 0)
                    E[a].add(t & 0xfffffffe)
            else:
                for k in range(0, len(buf) - 3, 2):
                    h1, h2 = struct.unpack_from("<HH", buf, k)
                    if (h1 & 0xf800) == 0xf000 and (h2 & 0xc000) == 0xc000 or (h1 & 0xf800) == 0xf000 and (h2 & 0xd000) == 0x9000:
                        S = (h1 >> 10) & 1; J1 = (h2 >> 13) & 1; J2 = (h2 >> 11) & 1
                        I1 = 1 ^ (J1 ^ S); I2 = 1 ^ (J2 ^ S)
                        imm = (S << 24) | (I1 << 23) | (I2 << 22) | ((h1 & 0x3ff) << 12) | ((h2 & 0x7ff) << 1)
                        if S: imm -= 1 << 25
                        site = a + k; t = site + 4 + imm
                        if not (h2 & 0x1000): t &= ~3        # blx -> ARM
                        E[a].add(t & 0xfffffffe)
        return E


def classify_main(im, a, mode):
    sec = None
    for n, (lo, hi) in im.sec.items():
        if lo <= a < hi: sec = n; break
    f0, f1 = im.func_of(a)
    infunc = f0 is not None and f0 <= a < f1
    real = mode == "arm" and a % 4 == 0 and sec in (".text", ".init", ".fini", ".plt") and (infunc or sec != ".text")
    return sec, (f0 if infunc else None), real


# ------------------------------------------------------------------------------------------------------------------------------
def c1_main(out):
    im = sp16img.Image()
    E = Elf(sp16img.TARGET)
    R = {"sha256": E.sha, "exec_ranges": [], "raw": {}, "sweep": {}, "hits": []}
    raw_aligned, raw_any, raw_thumb, sw = [], [], [], {"arm": [0, []], "thumb": [0, []]}
    for v, sz, o in E.exec_ranges():
        buf = E.raw[o:o + sz]
        R["exec_ranges"].append([hex(v), hex(v + sz)])
        raw_aligned += arm_raw(buf, v, True)
        raw_any += arm_raw(buf, v, False)
        raw_thumb += thumb_raw(buf, v)
        for mode in ("arm", "thumb"):
            n, h = sweep(buf, v, mode == "thumb")
            sw[mode][0] += n; sw[mode][1] += h

    def rows(lst, mode):
        rr = []
        for a, w, kind, reg, rt, cond, strict in lst:
            sec, f, real = classify_main(im, a, mode)
            sr = SYSREG.get(reg, "reg%d" % reg) if strict else "cp11/AdvSIMD(VDUP/VMOV-scalar)" if (w >> (8 if mode == "arm" else 8)) & 1 \
                else "cp10-nonSBZ"
            rr.append({"addr": hex(a), "word": "%08x" % w, "kind": kind, "sysreg": sr, "rt": rt,
                       "apsr_nzcv": kind == "read" and rt == 15, "reg": reg, "cond": cond, "strict_encoding": strict, "aligned4": a % 4 == 0, "section": sec,
                       "exidx_func": hex(f) if f else None, "real_instruction": real})
        return rr
    R["raw"]["arm_aligned"] = rows(raw_aligned, "arm")
    R["raw"]["arm_any_offset"] = rows(raw_any, "arm")
    R["raw"]["thumb_any_offset"] = rows(raw_thumb, "thumb")
    for mode in ("arm", "thumb"):
        n, h = sw[mode]
        R["sweep"][mode] = {"instructions": n, "hits": []}
        for a, mn, op, sz in h:
            sec, f, real = classify_main(im, a, mode)
            R["sweep"][mode]["hits"].append({"addr": hex(a), "insn": mn + " " + op, "section": sec,
                                             "exidx_func": hex(f) if f else None, "real_instruction": real})
    # thumb presence
    lo, hi = im.sec[".ARM.exidx"]; odd = 0; tot = 0
    for x in range(lo, hi, 8):
        oo = im.u32(x) & 0x7fffffff; oo = oo - 0x80000000 if oo & 0x40000000 else oo
        tot += 1; odd += ((x + oo) & 1)
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    blx = [s for s, t, k in im.direct_calls() if k == "blx"]
    blx_ok = [s for s in blx if any(i.mnemonic == "blx" for i in md.disasm(E.raw[E.off(s):E.off(s) + 4], s))
              and im.func_of(s)[0] is not None]
    R["exidx_functions"] = tot; R["exidx_thumb_functions"] = odd
    R["blx_imm_sites"] = len(blx); R["blx_imm_sites_in_exidx_funcs"] = len(blx_ok)
    R["blx_imm_sites_list"] = [hex(s) for s in blx_ok[:20]]
    # Thumb entry evidence: odd words (Thumb-bit code pointers) anywhere in the image that point into .text
    tlo, thi = im.sec[".text"]
    odd_ptrs = collections.Counter()
    for v, sz, o, _ in E.segs:
        for k in range(0, sz - 3, 4):
            w = struct.unpack_from("<I", E.raw, o + k)[0]
            if w & 1 and tlo <= w < thi: odd_ptrs[E.section(v + k)] += 1
    R["odd_text_pointers_by_section"] = dict(odd_ptrs)
    # every Thumb-mode FPSCR-write decode: covering aligned ARM word, its capstone ARM decode, containing exidx function
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cov = []
    for h in R["raw"]["thumb_any_offset"] + R["raw"]["arm_any_offset"]:
        if h["kind"] != "write" or h["reg"] != 1 or h["real_instruction"]: continue
        a = int(h["addr"], 16); words = sorted({a & ~3, (a + 3) & ~3})
        dec = []
        for wa in words:
            ii = list(md.disasm(E.raw[E.off(wa):E.off(wa) + 4], wa))
            dec.append("%x: %s" % (wa, (ii[0].mnemonic + " " + ii[0].op_str) if ii else "<invalid ARM>"))
        f0, f1 = im.func_of(a)
        cov.append({"addr": h["addr"], "decoded_as": "thumb" if h in R["raw"]["thumb_any_offset"] else "arm-misaligned",
                    "section": h["section"], "covering_arm_words": dec,
                    "in_exidx_arm_function": hex(f0) if f0 is not None and f0 <= a < f1 else None,
                    "odd_pointer_to_it": any(im.u32(x) == (a | 1) for x in [])})
    R["fpscr_write_false_decodes"] = cov
    # .ARM.attributes
    R["arm_attributes"] = arm_attributes(E)
    R["text_range"] = [hex(tlo), hex(thi)]
    return R


def arm_attributes(E):
    sec = [s for s in E.e.sections if s.name == ".ARM.attributes"]
    if not sec: return None
    b = bytes(sec[0].content); res = {}
    names = {5: "CPU_name", 6: "CPU_arch", 7: "CPU_arch_profile", 8: "ARM_ISA_use", 9: "THUMB_ISA_use", 10: "FP_arch",
             12: "Advanced_SIMD_arch", 17: "ABI_PCS_GOT_use", 18: "ABI_PCS_wchar_t", 20: "ABI_FP_denormal", 21: "ABI_FP_exceptions",
             22: "ABI_FP_user_exceptions", 23: "ABI_FP_number_model", 24: "ABI_align_needed", 25: "ABI_align8_preserved",
             26: "ABI_enum_size", 28: "ABI_VFP_args", 30: "ABI_optimization_goals", 34: "CPU_unaligned_access", 36: "FP_HP_extension",
             38: "ABI_FP_16bit_format", 42: "MPextension_use", 44: "DIV_use", 64: "nodefaults", 66: "Virtualization_use",
             68: "T2EE_use", 14: "ABI_PCS_R9_use", 15: "ABI_PCS_RW_data", 16: "ABI_PCS_RO_data", 19: "ABI_FP_rounding",
             32: "compatibility", 4: "CPU_raw_name", 65: "also_compatible_with", 67: "conformance", 70: "MPextension_use_old"}

    def uleb(b, i):
        r = s = 0
        while True:
            c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
            if not c & 0x80: return r, i
    assert b[0] == 0x41
    i = 1
    while i < len(b):
        ln = struct.unpack_from("<I", b, i)[0]; end = i + ln; j = i + 4
        vend = b[j:b.index(0, j)]; j = b.index(0, j) + 1
        while j < end:
            tag = b[j]; sl = struct.unpack_from("<I", b, j + 1)[0]; send = j + sl; k = j + 5
            while k < send:
                t, k = uleb(b, k)
                if t in (4, 5, 67, 32) or (t > 32 and t % 2 == 1 and t not in (65,)):
                    if t == 32:
                        _, k = uleb(b, k)
                    e2 = b.index(0, k); res[names.get(t, "tag%d" % t)] = b[k:e2].decode("latin1"); k = e2 + 1
                else:
                    v, k = uleb(b, k); res[names.get(t, "tag%d" % t)] = v
            j = send
        i = end
    return res


# ------------------------------------------------------------------------------------------------------------------------------
def lib_paths():
    found = {}
    for p in glob.glob(os.path.join(LIBDIR, "*")): found[os.path.basename(p)] = ("decoded/lib", p)
    return found


def c2_libs(out):
    main = Elf(sp16img.TARGET)
    have = lib_paths()
    extra = {}
    if os.path.isdir(EXTRA_LIBDIR):
        for p in glob.glob(os.path.join(EXTRA_LIBDIR, "*.so*")):
            if os.path.isfile(p): extra[os.path.basename(p)] = ("image2/payloads/lib (read-only)", os.path.realpath(p))
    # DT_NEEDED BFS (load order)
    order, missing, libs = [], [], {}
    q = list(main.e.libraries); seen = set()
    while q:
        n = q.pop(0)
        if n in seen: continue
        seen.add(n)
        src = have.get(n) or extra.get(n)
        if not src: missing.append(n); continue
        L = Elf(src[1]); L.src = src[0]; libs[n] = L; order.append(n)
        q += list(L.e.libraries)
    # ld.so is the interpreter
    if "ld-linux.so.3" not in libs and "ld-linux.so.3" in have:
        L = Elf(have["ld-linux.so.3"][1]); L.src = "decoded/lib"; libs["ld-linux.so.3"] = L; order.append("ld-linux.so.3")
    # check the extra dir is the same image: compare a decoded/lib lib with its twin
    same_image = {}
    for n in sorted(set(have) & set(extra)):
        if True:
            same_image[n] = hashlib.sha256(open(have[n][1], "rb").read()).hexdigest() == hashlib.sha256(open(extra[n][1], "rb").read()).hexdigest()
    # global symbol resolution (first definer in load order, main first)
    definer = {}
    for n in order:
        for s, a in libs[n].exports.items():
            definer.setdefault(s, (n, a))
    # census
    R = {"load_order": order, "missing": missing, "extra_dir_same_image_check": same_image, "libs": {}}
    hit_funcs = {}
    for n in order:
        L = libs[n]
        rec = {"source": L.src, "sha256": L.sha, "hits": [], "sweep_only": []}
        for v, sz, o in L.exec_ranges():
            buf = L.raw[o:o + sz]
            arm_sw = {a: (mn, op) for a, mn, op, _ in sweep(buf, v, False)[1]}
            th_sw = {a: (mn, op) for a, mn, op, _ in sweep(buf, v, True)[1]}
            for mode, lst in (("arm", arm_raw(buf, v, True)), ("thumb", thumb_raw(buf, v))):
                for a, w, kind, reg, rt, cond, strict in lst:
                    f = L.func(a)
                    fa, fname, fsz, fth = f if f else (None, None, None, None)
                    inside = f is not None and "beyond" not in fname
                    real = inside and strict and ((mode == "arm" and not fth) or (mode == "thumb" and fth))
                    dec = (arm_sw if mode == "arm" else th_sw).get(a)
                    sr = SYSREG.get(reg, "reg%d" % reg) if strict else ("cp11/AdvSIMD" if (w >> 8) & 1 else "cp10-nonSBZ")
                    rec["hits"].append({"addr": hex(a), "mode": mode, "kind": kind, "sysreg": sr, "apsr_nzcv": kind == "read" and rt == 15,
                                        "rt": rt, "strict": strict, "func": fname, "func_addr": hex(fa) if fa is not None else None,
                                        "section": L.section(a), "real_instruction": bool(real),
                                        "capstone": (dec[0] + " " + dec[1]) if dec else None})
                    if real and strict and kind == "write" and reg == 1:
                        hit_funcs.setdefault((n, fa), fname)
            # sweep-only hits not in raw lists (sanity: should be none)
            rawset = {int(h["addr"], 16) for h in rec["hits"]}
            rec["sweep_only"] += [hex(a) + " " + mn + " " + op for a, (mn, op) in list(arm_sw.items()) + list(th_sw.items())
                                 if a not in rawset and (mn in VFP_MNEM or "p10" in op or "p11" in op)]
        R["libs"][n] = rec
    # reachability graph
    edges = {}
    for n in order:
        L = libs[n]; E2 = L.call_edges(); g = {}
        for fa, ts in E2.items():
            outs = set()
            for t in ts:
                if t in L.plt:
                    d = definer.get(L.plt[t])
                    if d: outs.add(d)
                    continue
                f = L.func(t)
                if f and "beyond" not in f[1]: outs.add((n, f[0]))
            g[fa] = outs
        edges[n] = g
    def bfs(roots):
        prev = {r: None for r in roots}; q = list(roots)
        while q:
            x = q.pop(0)
            for y in edges.get(x[0], {}).get(x[1], ()):
                if y not in prev: prev[y] = x; q.append(y)
        return prev
    def path(prev, x):
        p = []
        while x is not None: p.append(x); x = prev[x]
        return [("%s:%s" % (n, libs[n].funcs.get(a, ("0x%x" % a,))[0])) for n, a in reversed(p)]
    main_func_imports = [s.name for s in main.e.dynamic_symbols if s.shndx == 0 and s.name and
                         s.type in (lief.ELF.Symbol.TYPE.FUNC,) ]
    roots_main = {definer[s] for s in main_func_imports if s in definer}
    unresolved = sorted(s for s in main_func_imports if s not in definer)
    roots_load = set()
    for n in order:
        L = libs[n]
        for ent in L.e.dynamic_entries:
            t = str(ent.tag)
            if t.endswith("INIT") and ent.value:
                f = L.func(ent.value & ~1); roots_load.add((n, f[0] if f else ent.value))
            if t.endswith("INIT_ARRAY"):
                for v in ent.array:
                    if v and v != 0xffffffff:
                        f = L.func(v & ~1)
                        if f: roots_load.add((n, f[0]))
    if "ld-linux.so.3" in libs:
        L = libs["ld-linux.so.3"]; f = L.func(L.e.entrypoint & ~1)
        if f: roots_load.add(("ld-linux.so.3", f[0]))
    # libc __libc_start_main runs main's init (via function pointer): treat it as a load root too (it is imported anyway)
    pm, pl = bfs(roots_main), bfs(roots_load)
    R["main_function_imports"] = len(main_func_imports); R["main_unresolved_imports"] = unresolved
    R["load_roots"] = sorted("%s:%s" % (n, libs[n].funcs.get(a, ("0x%x" % a,))[0]) for n, a in roots_load)
    writers = set(hit_funcs)
    R["main_imports_reaching_writers"] = {}
    for sname in main_func_imports:
        if sname not in definer: continue
        pr = bfs({definer[sname]})
        w = sorted("%s:%s" % (n, libs[n].funcs[a][0]) for n, a in writers if (n, a) in pr)
        if w: R["main_imports_reaching_writers"][sname] = w
    R["fpscr_write_functions"] = []
    for (n, fa), fname in sorted(hit_funcs.items(), key=lambda x: (x[0][0], x[0][1] or 0)):
        R["fpscr_write_functions"].append({"lib": n, "func": fname, "addr": hex(fa), "exported": fname in libs[n].exports,
                                           "imported_by_main": fname in main.imports,
                                           "reachable_from_main_imports": (n, fa) in pm,
                                           "path_from_main": path(pm, (n, fa)) if (n, fa) in pm else None,
                                           "reachable_from_load_time": (n, fa) in pl,
                                           "path_from_load": path(pl, (n, fa)) if (n, fa) in pl else None})
    # FP-environment imports by the main binary
    fp_re = re.compile(r"^(fe[a-z]+|__fe\w+|_FPU\w*|__setfpucw|__fpu_control|_?_?fpu\w*|__aeabi_\w+|fpsetmask|fpgetmask|"
                       r"__libc_fe\w+|setcontext|swapcontext|getcontext|makecontext|_?setjmp|_?longjmp|siglongjmp|sigsetjmp|__sigsetjmp)$")
    R["main_fp_env_imports"] = sorted(s for s in main.imports if fp_re.match(s))
    R["main_defines_fpu_control"] = any(s.name == "__fpu_control" for s in main.e.dynamic_symbols)
    # libc __fpu_control initial value
    libc = libs.get("libc.so.6")
    fc = [s for s in list(libc.e.symtab_symbols) + list(libc.e.dynamic_symbols) if s.name == "__fpu_control"]
    R["libc___fpu_control"] = {"addr": hex(fc[0].value), "section": libc.section(fc[0].value),
                               "value": hex(libc.u32(fc[0].value)) if libc.off(fc[0].value) is not None else "bss(0)"} if fc else None
    # which libs import __fpu_control (data references)
    R["fpu_control_importers"] = [n for n in order if "__fpu_control" in libs[n].imports]
    # disassembly context for every real FPSCR access in libs (written only to the out dir)
    ctx = []
    for n in order:
        L = libs[n]
        for h in R["libs"][n]["hits"]:
            if not h["real_instruction"]: continue
            a = int(h["addr"], 16); fa = int(h["func_addr"], 16); _, fsz, _, th = L.funcs[fa]
            md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if th else capstone.CS_MODE_ARM)
            o = L.off(fa)
            ctx.append("== %s %s @%s (%s %s)" % (n, h["func"], h["addr"], h["kind"], h["sysreg"]))
            for i in md.disasm(L.raw[o:o + fsz], fa):
                if a - 40 <= i.address <= a + 16: ctx.append("   0x%x: %s %s" % (i.address, i.mnemonic, i.op_str))
    open(os.path.join(out, "lib_context.txt"), "w").write("\n".join(ctx) + "\n")
    # constant analysis: immediates that touch FZ/DN/RMode bits in each FPSCR-writing function
    for rec in R["fpscr_write_functions"]:
        L = libs[rec["lib"]]; fa = int(rec["addr"], 16); _, fsz, _, th = L.funcs[fa]
        md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB if th else capstone.CS_MODE_ARM)
        o = L.off(fa); imms = set()
        for i in md.disasm(L.raw[o:o + fsz], fa):
            for m in re.finditer(r"#(0x[0-9a-f]+|\d+)", i.op_str):
                v = int(m.group(1), 0)
                if i.mnemonic[:3] in ("orr", "bic", "mov", "and", "eor", "tst", "cmp", "mvn") and v & 0x03c00000:
                    imms.add("%s %s" % (i.mnemonic, i.op_str))
            mm = re.match(r"\w+, \[pc, #(-?0x[0-9a-f]+|-?\d+)\]", i.op_str)
            if i.mnemonic.startswith("ldr") and mm and not th:
                lit = L.u32(i.address + 8 + int(mm.group(1), 0))
                if lit is not None and lit & 0x03c00000 and lit < 0x10000000: imms.add("literal 0x%x" % lit)
        rec["immediates_touching_bits22_25"] = sorted(imms)
    return R


# ------------------------------------------------------------------------------------------------------------------------------
def c4_emu():
    import emu
    from emu import f2u, u2f
    from unicorn import arm_const as A, UC_PROT_ALL
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    SCR = 0x3d000000
    # own hand-encoded test routines (ARM, cond AL)
    prog_scalar = [0xEE002A90,   # vmov s1, r2
                   0xEE013A10,   # vmov s2, r3
                   0xEE200A81,   # vmul.f32 s0, s1, s2
                   0xEE100A10,   # vmov r0, s0
                   0xEEF11A10,   # vmrs r1, fpscr
                   0xE12FFF1E]   # bx lr
    prog_neon = [0xEE002A90,   # vmov s1, r2
                 0xEE013A10,   # vmov s2, r3
                 0xF3BC2C00,   # vdup.32 d2, d0[1]
                 0xF3B43C01,   # vdup.32 d3, d1[0]
                 0xF3024D13,   # vmul.f32 d4, d2, d3
                 0xEE140A10,   # vmov r0, s8
                 0xEEF11A10,   # vmrs r1, fpscr
                 0xE12FFF1E]
    prog_set = [0xEEE10A10,    # vmsr fpscr, r0  (guest-side write, for the round-trip check)
                0xEEF10A10,    # vmrs r0, fpscr
                0xE12FFF1E]
    dis = {}
    for nm, p in (("scalar", prog_scalar), ("neon", prog_neon), ("set", prog_set)):
        b = struct.pack("<%dI" % len(p), *p)
        dis[nm] = ["%s %s" % (i.mnemonic, i.op_str) for i in md.disasm(b, 0)]
    e = emu.Emu()
    e.uc.mem_map(SCR, 0x1000, UC_PROT_ALL)
    e.uc.mem_write(SCR, struct.pack("<%dI" % len(prog_scalar), *prog_scalar))
    e.uc.mem_write(SCR + 0x100, struct.pack("<%dI" % len(prog_neon), *prog_neon))
    e.uc.mem_write(SCR + 0x200, struct.pack("<%dI" % len(prog_set), *prog_set))
    res = {"disasm_of_own_test_code": dis, "emu_initial_fpscr": hex(e.uc.reg_read(A.UC_ARM_REG_FPSCR)), "cases": []}
    cases = [("normal*normal->denormal", 1e-20, 1e-20), ("denormal*1", 1.0e-40, 1.0), ("normal*normal", 1.5, 2.0),
             ("tiny*0.99 (flanger-like tail)", 1.18e-38, 0.99)]
    for fpscr in (0x0, 1 << 24, 1 << 25, (1 << 24) | (1 << 25)):
        for nm, a, b in cases:
            for prog, off in (("scalar_vfp", 0), ("neon", 0x100)):
                e.uc.reg_write(A.UC_ARM_REG_FPSCR, fpscr)
                r0, r1 = e.call(SCR + off, 0, 0, f2u(a), f2u(b))
                res["cases"].append({"fpscr_set": hex(fpscr), "case": nm, "path": prog, "a": "%08x" % f2u(a), "b": "%08x" % f2u(b),
                                     "result_bits": "%08x" % r0, "result": repr(u2f(r0)), "fpscr_seen_by_guest": hex(r1)})
    # guest-side write round trip
    rt = []
    for v in (0x0, 0x01000000, 0x03c00000):
        r0, _ = e.call(SCR + 0x200, v)
        rt.append({"written": hex(v), "read_back": hex(r0 & 0xffffffff), "host_reg_read": hex(e.uc.reg_read(A.UC_ARM_REG_FPSCR))})
    res["guest_vmsr_roundtrip"] = rt
    e.uc.reg_write(A.UC_ARM_REG_FPSCR, 0)
    # real 1.60 libm expf (the reachable FPSCR writer chain feholdexcept / fesetround / fesetenv): FPSCR on entry vs exit,
    # value written at each vmsr (hooked), result bits. hwcap shim as in H031/H028 (HWCAP_VFP at _rtld_global_ro+0x40).
    e2 = emu.Emu()
    e2.uc.mem_map(0x3d000000, 0x1000, 3); e2.wr(0x3d000040, struct.pack("<Q", 0x40))
    lm, base, _ = e2._libs["libm.so.6"]
    for r in lm.dynamic_relocations:
        if r.has_symbol and r.symbol.name == "_rtld_global_ro": e2.w32(base + r.address, 0x3d000000)
    L = Elf(os.path.join(LIBDIR, "libm.so.6"))
    vmsr_sites = {}
    for v, sz, o in L.exec_ranges():
        for a, w, kind, reg, rt, cond, strict in arm_raw(L.raw[o:o + sz], v, True):
            f = L.func(a)
            if strict and kind == "write" and reg == 1 and f and "beyond" not in f[1]: vmsr_sites[base + a] = (f[1], rt)
    log = []
    def mk(site, fn, rt):
        def cb(em):
            log.append((fn, hex(em.uc.reg_read(A.UC_ARM_REG_FPSCR)), hex(em.r(rt))))
        return cb
    for site, (fn, rt) in vmsr_sites.items(): e2.add_watch(site, mk(site, fn, rt))
    expf = e2.lib_exports["expf"][0]
    xs = [-0.0142476, 0.5, -3.0, 10.0, -87.0]
    ex = []
    for fpscr in (0x0, 0x01000000, 0x02000000, 0x03000000, 0x00c00000, 0x0000009f):
        for x in xs:
            del log[:]
            e2.uc.reg_write(A.UC_ARM_REG_FPSCR, fpscr)
            r0, _ = e2.call(expf, f2u(x))
            ex.append({"fpscr_in": hex(fpscr), "x": x, "result_bits": "%08x" % r0, "fpscr_out": hex(e2.uc.reg_read(A.UC_ARM_REG_FPSCR)),
                       "vmsr_trace(func, fpscr_before, value_written)": list(log)})
    res["libm_expf_fpscr"] = ex
    res["libm_expf_vmsr_sites"] = {hex(k): v[0] for k, v in vmsr_sites.items()}
    return res


def c2b_dlopen(out):
    """Census of libraries that can enter the process via dlopen rather than DT_NEEDED: the X extension libraries named by
    strings in the main binary (JUCE Linux windowing: libXcursor/libXinerama/libXss) and every ALSA plug-in module of the image."""
    names = sorted({m.group().decode() for m in re.finditer(rb"lib[A-Za-z0-9_+-]+\.so(\.[0-9]+)*(?=\x00)",
                                                            open(sp16img.TARGET, "rb").read())})
    cands = []
    for n in names:
        p = os.path.join(EXTRA_LIBDIR, n)
        if os.path.exists(p) and not os.path.exists(os.path.join(LIBDIR, n)): cands.append((n, os.path.realpath(p)))
        elif not os.path.exists(p) and not os.path.exists(os.path.join(LIBDIR, n)): cands.append((n, None))
    for p in sorted(glob.glob(os.path.join(EXTRA_LIBDIR, "alsa-lib", "**", "*.so*"), recursive=True)):
        cands.append((os.path.relpath(p, EXTRA_LIBDIR), os.path.realpath(p)))
    R = {}
    for n, p in cands:
        if p is None: R[n] = "not present in image2 payloads/lib"; continue
        L = Elf(p); w = []; rd = 0
        for v, sz, o in L.exec_ranges():
            buf = L.raw[o:o + sz]
            for mode, lst in (("arm", arm_raw(buf, v, True)), ("thumb", thumb_raw(buf, v))):
                for a, wd, kind, reg, rt, cond, strict in lst:
                    f = L.func(a)
                    ok = strict and f is not None and "beyond" not in f[1] and ((mode == "arm") != bool(f[3]))
                    if ok and reg == 1 and kind == "write": w.append("%s@0x%x" % (f[1], a))
                    if ok and reg == 1 and kind == "read": rd += 1
        R[n] = {"sha256": L.sha[:16], "fpscr_writes": w, "fpscr_reads": rd, "needed": list(L.e.libraries)}
    return R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H038"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    r1 = c1_main(a.out)
    json.dump(r1, open(os.path.join(a.out, "c1_main.json"), "w"), indent=1)
    s = lambda lst, **kw: [x for x in lst if all(x.get(k) == v for k, v in kw.items())]
    print("C1 main sha256", r1["sha256"][:16], "exec ranges", r1["exec_ranges"], "text", r1["text_range"])
    for k in ("arm_aligned", "arm_any_offset", "thumb_any_offset"):
        L = r1["raw"][k]
        print("  raw %-16s loose reg-field-1 writes %d (real %d); strict 0x?EE1?A10 / EEE1 ?A10 writes %d" % (k,
              len([x for x in L if x["kind"] == "write" and x["reg"] == 1]),
              len([x for x in L if x["kind"] == "write" and x["reg"] == 1 and x["real_instruction"]]),
              len([x for x in L if x["kind"] == "write" and x["reg"] == 1 and x["strict_encoding"]])))
        print("  raw %-16s hits %4d | FPSCR writes %3d (real %d) | FPSCR reads %3d (real %d) | other sysreg %d | strict-FPSCR-write %d"
              % (k, len(L), len(s(L, kind="write", sysreg="fpscr")), len(s(L, kind="write", sysreg="fpscr", real_instruction=True)),
                 len(s(L, kind="read", sysreg="fpscr")), len(s(L, kind="read", sysreg="fpscr", real_instruction=True)),
                 len([x for x in L if x["sysreg"] != "fpscr"]), len(s(L, kind="write", strict_encoding=True))))
        bysec = collections.Counter((x["section"], x["kind"], x["sysreg"], x["real_instruction"]) for x in L)
        for kk, v in sorted(bysec.items(), key=str): print("      ", kk, v)
    for mode in ("arm", "thumb"):
        S = r1["sweep"][mode]
        print("  capstone %-5s instructions %d, vmsr/vmrs/fmxr/fmrx/mcr-p10/p11 hits %d, real %d"
              % (mode, S["instructions"], len(S["hits"]), len(s(S["hits"], real_instruction=True))))
        c = collections.Counter((h["insn"].split()[0], h["section"], h["real_instruction"]) for h in S["hits"])
        for kk, v in sorted(c.items(), key=str): print("      ", kk, v)
    print("  exidx functions %d, thumb %d; blx-imm sites %d (in exidx funcs %d)" % (
        r1["exidx_functions"], r1["exidx_thumb_functions"], r1["blx_imm_sites"], r1["blx_imm_sites_in_exidx_funcs"]))
    print("  .ARM.attributes", r1["arm_attributes"])
    print("  odd (Thumb-bit) pointers into .text by section:", r1["odd_text_pointers_by_section"])
    fd = r1["fpscr_write_false_decodes"]
    print("  FPSCR-write false decodes: %d; in exidx ARM functions %d; covering words all valid ARM %d; by section %s" % (
        len(fd), sum(1 for x in fd if x["in_exidx_arm_function"]), sum(1 for x in fd if all("invalid" not in w for w in x["covering_arm_words"])),
        dict(collections.Counter((x["decoded_as"], x["section"]) for x in fd))))
    for x in fd[:6]: print("     ", x)
    rd = [x for x in r1["raw"]["arm_aligned"] if x["kind"] == "read" and x["sysreg"] == "fpscr" and x["real_instruction"]]
    print("  real ARM FPSCR reads: %d, of which APSR_nzcv (vcmp flag transfer) %d; to a core register: %s" % (
        len(rd), sum(x["apsr_nzcv"] for x in rd), [(x["addr"], x["rt"], x["exidx_func"]) for x in rd if not x["apsr_nzcv"]]))
    nonv = [x for x in r1["raw"]["arm_aligned"] if x["real_instruction"] and x["sysreg"] != "fpscr"]
    print("  real ARM non-FPSCR opc1=7 cp10/11 words:", [(x["addr"], x["word"], x["sysreg"]) for x in nonv])

    r2 = c2_libs(a.out)
    json.dump(r2, open(os.path.join(a.out, "c2_libs.json"), "w"), indent=1)
    print("C2 load order", r2["load_order"]); print("   missing", r2["missing"], "extra-dir same image", r2["extra_dir_same_image_check"])
    for n, rec in r2["libs"].items():
        real = [h for h in rec["hits"] if h["real_instruction"]]
        if rec["hits"] or rec["sweep_only"]:
            print("  %-18s raw hits %3d real %3d | real FPSCR writes %d reads %d | sweep-only %d" % (
                n, len(rec["hits"]), len(real), len([h for h in real if h["kind"] == "write" and h["sysreg"] == "fpscr"]),
                len([h for h in real if h["kind"] == "read" and h["sysreg"] == "fpscr"]), len(rec["sweep_only"])))
        else:
            print("  %-18s no hits" % n)
    print("  main function imports", r2["main_function_imports"], "unresolved (in missing libs/weak)", len(r2["main_unresolved_imports"]))
    print("  main FP-environment-related imports:", r2["main_fp_env_imports"])
    print("  main defines __fpu_control:", r2["main_defines_fpu_control"], "| libc __fpu_control:", r2["libc___fpu_control"],
          "| importers:", r2["fpu_control_importers"])
    print("  load-time roots:", len(r2["load_roots"]))
    print("  main imports whose direct-call closure reaches an FPSCR writer:", r2["main_imports_reaching_writers"])
    for f in r2["fpscr_write_functions"]:
        print("   W %-14s %-28s %s exp=%d imp_by_main=%d reach_main=%d reach_load=%d imm=%s" % (
            f["lib"], f["func"], f["addr"], f["exported"], f["imported_by_main"], f["reachable_from_main_imports"],
            f["reachable_from_load_time"], f["immediates_touching_bits22_25"]))
        if f["path_from_main"]: print("        path(main):", " -> ".join(f["path_from_main"]))
        if f["path_from_load"]: print("        path(load):", " -> ".join(f["path_from_load"]))

    r2b = c2b_dlopen(a.out)
    json.dump(r2b, open(os.path.join(a.out, "c2b_dlopen.json"), "w"), indent=1)
    print("C2b dlopen candidates:")
    for n, v in r2b.items(): print("   %-48s %s" % (n, v))

    r4 = c4_emu()
    json.dump(r4, open(os.path.join(a.out, "c4_emu.json"), "w"), indent=1)
    print("C4 emu initial FPSCR", r4["emu_initial_fpscr"]); print("   own test code:", r4["disasm_of_own_test_code"])
    for c in r4["cases"]:
        print("   FPSCR=%-10s %-30s %-10s a=%s b=%s -> %s (%s) guest-sees %s" % (c["fpscr_set"], c["case"], c["path"], c["a"], c["b"],
                                                                             c["result_bits"], c["result"], c["fpscr_seen_by_guest"]))
    print("   guest vmsr round trip:", r4["guest_vmsr_roundtrip"])
    print("   libm vmsr sites hooked:", r4["libm_expf_vmsr_sites"])
    for c in r4["libm_expf_fpscr"]:
        print("   expf FPSCR in %-10s x=%-10g -> %s FPSCR out %-10s writes %s" % (c["fpscr_in"], c["x"], c["result_bits"], c["fpscr_out"],
              c["vmsr_trace(func, fpscr_before, value_written)"]))
    im = sp16img.Image(); plt = {v: k for k, v in im.plt().items()}
    for nm in ("expf", "exp", "powf", "pow", "sinf", "cosf", "tan", "log10f"):
        if nm in plt:
            sites = [s_ for s_, t, k in im.direct_calls() if t == plt[nm] and k == "bl"]
            print("   main bl sites to %-7s PLT 0x%x: %d (first %s)" % (nm, plt[nm], len(sites), [hex(x) for x in sites[:6]]))
    h = hashlib.sha256()
    for f in ("c1_main.json", "c2_libs.json", "c2b_dlopen.json", "c4_emu.json"):
        h.update(open(os.path.join(a.out, f), "rb").read())
    print("output digest", h.hexdigest()[:16])


if __name__ == "__main__":
    main()
