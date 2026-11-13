#!/usr/bin/env python3
"""H007 — single-function unicorn emulation of one 1.60 insert effect (default: LoFi), driven through its real 1.60 code.

Sequence per scenario (fresh emulator each time, nothing hand-filled in the effect object):
  0. Static initialiser(s) the effect reads (.init_array entries; LoFi: 0x137cc, which fills .bss 0xf52ebc..0xf52ecc).
  1. obj = operator new(size); ctor(obj, 44100, 64)           [args as at InsertFxProcessor ctor call site 0x118fec]
  2. the InsertFxProcessor ctor's per-effect init, in its order:
       slot 22 (+0x58)(obj, 0)                                  [0x11931c..0x11943c]
       0x106c7c(obj, 1, 10.0f)                                  [0x11945c..0x119510; float in r2]
       InsertFxProcessor slot 52 0x118a9c(container, index)     [defaults; container = documented stand-in holding only
                                                                 +0x80 = effect array, +0x88 = count, the two fields it reads]
  3. optional parameter changes through EffectBase slot 14 (+0x38) 0x105d24(obj, paramIndex, float-bits)
  4. per 64-sample block, the effect calls InsertFxProcessor processBlock 0x116860 makes for index 5 (no tempo feed):
       mode "on"  (processor byte +0x9e = 0, +0x9d = 1, i.e. after FxProcessorBase 0x112a08(proc,0)):
                  s = slot 9 (+0x24)(obj)                              [@0x1168ec; = gate state 0x1079d0(ctx)]
                  if s == 0: slot 5 (+0x14)(obj, 0, 1); slot 7 (+0x1c)(obj, 0)    [@0x116b74, @0x116ba4]
                  slot 18 (+0x48) 0x106de4(obj, L, R, 64)              [@0x116a7c]
       mode "off" (ctor default +0x9e = 1): slot 9, then slot 18 only (slot 5/7 never called)
       mode "s25": slot 25 (+0x64) called directly (skips the slot-18 gate and dry/wet write-back), for comparison.
Outputs only to --out (default harness/out/H007/). Run: .venv/bin/python harness/H007_effect_emu.py --out DIR
"""
import argparse, hashlib, json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
sys.dont_write_bytecode = True
from emu import Emu, EmuAbort, f2u, u2f, d2u, u2d, init_array, STUBS, HEAP_BASE   # noqa: E402

N = 64          # F010: hard-coded block length at every processor -> slot 18 call site
FS = 44100      # F014 / ctor arg at 0x118fe0
NBLK = 16

EFFECTS = {
    "lofi": dict(
        ctor=0xfd640, size=0x4b8, vtable=0x841a68, ctor_args=(44100, 64), insert_index=5, static_init=[0x137cc],
        # parameter objects (each 0x5c bytes) at obj+off, names/ids as passed to 0xf1850/0xf1a00 in the ctor
        params=[("PREAMP", 0x1b8), ("BITDEPTH", 0x214), ("REDUCTION", 0x270), ("CUTOFF", 0x2cc), ("RESONANCE", 0x328),
                ("MIXRATIO", 0x384), ("FILTERTYPE", 0x3e0), ("FILTERPOSITION", 0x43c)],
    ),
}

SLOT_SETPARAM, SLOT_PROCESS18, SLOT_ENTRY25, SLOT9, SLOT22 = 14, 18, 25, 9, 22
CONTAINER_DEFAULTS = 0x118a9c      # InsertFxProcessor slot 52
SET_CC_D0 = 0x106c7c               # (obj, byte, float): +0xcc = byte, +0xd0 = float

# call sites that pass/return floats (criterion 5): bl address -> description
FLOAT_SITES = {
    0xfb3d8: "LoFi param update 0xfb20c: bl pow",
    0xfb430: "LoFi param update 0xfb20c: bl pow",
    0xfb530: "LoFi param update 0xfb20c: bl pow",
    0x1383c: "static init 0x137cc: bl pow",
    0x13880: "static init 0x137cc: bl pow",
    0x13818: "static init 0x137cc: bl log10f",
    0x1385c: "static init 0x137cc: bl log10f",
}


# dispatcher internals counted in the instrumented run (F010 sites)
COUNT_SITES = {0x106ec8: "slot18 -> slot25 call (copy path)", 0x106f10: "slot18 -> slot25 call (in-place path)",
               0x1074c4: "gate input stage 0x1074c4", 0x106c88: "0x106c88 after slot25 ret 0",
               0x10770c: "gate write-back/mix 0x10770c", 0xfc0f4: "LoFi slot 25 entry", 0xfbf64: "LoFi inner 0xfbf64",
               0xfb20c: "LoFi param update 0xfb20c", 0xfaef4: "LoFi slot 26 (wet/dry update)"}


def sha(b): return hashlib.sha256(b).hexdigest()


STATIC_SITES = dict(FLOAT_SITES)
STATIC_SITES.update({0x116b20: "InsertFxProcessor processBlock: blx effect slot 14 (setParameter)",
                     0x11945c: "InsertFxProcessor ctor: bl 0x106c7c(obj, 1, 10.0f)"})


def static_abi():
    """Capstone check at each float-carrying call site: which registers carry the float in/out (criterion 5, static half)."""
    import re, sp16img
    im = sp16img.Image(); plt = im.plt(); out = []
    vfp_arg = re.compile(r"\b(s[0-3]|d[01]|q0)\b")
    for site, what in sorted(STATIC_SITES.items()):
        before = im.disasm(site - 7 * 4, site)
        call = im.disasm(site, site + 4)[0]
        after = im.disasm(site + 4, site + 4 * 9)
        tgt = call.op_str.lstrip("#")
        tname = plt.get(int(tgt, 16), tgt) if tgt.startswith("0x") else call.op_str
        core_in = [("%s %s" % (i.mnemonic, i.op_str)) for i in before if re.match(r"(r[0-3])\b", i.op_str) and
                   i.mnemonic in ("mov", "movw", "movt", "vmov", "ldr", "add")]
        vfp_in = [("%s %s" % (i.mnemonic, i.op_str)) for i in before if vfp_arg.match(i.op_str)]
        res_use = [("%s %s" % (i.mnemonic, i.op_str)) for i in after if i.mnemonic == "vmov" and re.search(r"\br0\b", i.op_str)]
        vfp_res = [("%s %s" % (i.mnemonic, i.op_str)) for i in after if re.search(r"\b(s0|d0)\b", i.op_str)]
        out.append({"site": hex(site), "what": what, "call": "%s %s" % (call.mnemonic, call.op_str), "target": tname,
                    "core_arg_setup": core_in, "vfp_arg_reg_writes_before": vfp_in, "result_from_core": res_use,
                    "result_from_s0_d0": vfp_res})
    return out


def signal(kind, nblk=NBLK):
    tot = N * nblk
    if kind == "impulse":
        L = [1.0 if i == 0 else 0.0 for i in range(tot)]; R = [0.5 if i == 0 else 0.0 for i in range(tot)]
    elif kind == "impulse_late":      # unit impulse after the gate fade-in (block 10, sample 5)
        k = 10 * N + 5
        L = [1.0 if i == k else 0.0 for i in range(tot)]; R = [0.5 if i == k else 0.0 for i in range(tot)]
    elif kind == "silence":
        L = [0.0] * tot; R = [0.0] * tot
    elif kind == "sine1k":
        L = [0.5 * math.sin(2 * math.pi * 1000.0 * i / FS) for i in range(tot)]
        R = [0.5 * math.cos(2 * math.pi * 1000.0 * i / FS) for i in range(tot)]
    else:
        raise ValueError(kind)
    f = lambda xs: [u2f(f2u(x)) for x in xs]     # round to float32
    return f(L), f(R)


RUNS = []


class Run:
    """One fresh emulator + one effect object built by its 1.60 constructor."""

    def __init__(self, fx, heap_fill=0, log_abi=False):
        self.fx = fx; self.e = e = Emu(heap_fill=heap_fill)
        RUNS.append(self)
        self.abi = []; self.counts = {}
        if log_abi:
            self._watch_abi()
            for a_ in COUNT_SITES:
                e.add_watch(a_, lambda em, a_=a_: self.counts.__setitem__(a_, self.counts.get(a_, 0) + 1))
        self.static_ran = []
        for f in fx["static_init"]:
            assert f in init_array(e), "0x%x not an .init_array entry" % f
            e.call(f); self.static_ran.append(f)
        self.obj = obj = e.malloc(fx["size"], "new (harness: effect object)")
        r0, _ = e.call(fx["ctor"], obj, *fx["ctor_args"])
        self.ctor_ret = r0
        self.vptr = e.u32(obj)
        self.init_log = []

    # --- criterion 5 instrumentation ------------------------------------------------------------------------
    def _watch_abi(self):
        e = self.e
        for site, what in FLOAT_SITES.items():
            def before(em, site=site, what=what):
                rec = {"site": site, "what": what, "r": [em.r(i) for i in range(4)], "d0": em.dreg(0), "d1": em.dreg(1),
                       "s0": em.sreg(0)}
                self.abi.append(rec)
            def after(em, site=site):
                for rec in reversed(self.abi):
                    if rec["site"] == site and "ret_r0" not in rec:
                        rec["ret_r0"], rec["ret_r1"], rec["ret_d0"], rec["ret_s0"] = em.r(0), em.r(1), em.dreg(0), em.sreg(0)
                        break
            e.add_watch(site, before); e.add_watch(site + 4, after)
        def setp(em):
            self.abi.append({"site": 0x105d24, "what": "EffectBase slot 14 setParameter entry", "r": [em.r(i) for i in range(4)],
                             "s0": em.sreg(0), "d0": em.dreg(0)})
        e.add_watch(0x105d24, setp)

    # --- init sequence --------------------------------------------------------------------------------------
    def insert_init(self):
        e, obj, fx = self.e, self.obj, self.fx
        e.vcall(obj, SLOT22, 0); self.init_log.append("slot22(obj,0)")
        e.call(SET_CC_D0, obj, 1, f2u(10.0)); self.init_log.append("0x106c7c(obj,1,10.0f)")
        cont = e.malloc(0x100, "harness: InsertFxProcessor stand-in (+0x80 array, +0x88 count)")
        arr = e.malloc(40, "harness: effect array")
        for i in range(10): e.w32(arr + 4 * i, obj if i == fx["insert_index"] else 0)
        e.w32(cont + 0x80, arr); e.w32(cont + 0x88, 10)
        e.call(CONTAINER_DEFAULTS, cont, fx["insert_index"])
        self.init_log.append("InsertFxProcessor slot52 0x118a9c(container,%d)" % fx["insert_index"])

    def params(self):
        out = {}
        for name, off in self.fx["params"]:
            p = self.obj + off
            out[name] = {"type": self.e.u32(p + 0x10), "float": self.e.f32(p + 0x28), "int": self.e.u32(p + 0x44)}
        return out

    def set_param(self, idx, value):
        r0, _ = self.e.vcall(self.obj, SLOT_SETPARAM, idx, f2u(value))
        return r0

    # --- processing -----------------------------------------------------------------------------------------
    def gate(self):
        ctx = self.e.u32(self.obj + 0xc8)
        return self.e.u32(ctx + 0x1c), self.e.u32(ctx + 0x24)

    def process(self, L, R, mode="on"):
        e, obj = self.e, self.obj
        bl = e.malloc(4 * N, "harness: L block"); br = e.malloc(4 * N, "harness: R block")
        oL, oR, rets = [], [], []
        for b in range(len(L) // N):
            e.set_floats(bl, L[b * N:(b + 1) * N]); e.set_floats(br, R[b * N:(b + 1) * N])
            if mode in ("on", "off"):
                s9, _ = e.vcall(obj, SLOT9)
                act = ""
                if mode == "on" and s9 == 0:
                    e.vcall(obj, 5, 0, 1); e.vcall(obj, 7, 0); act = "slot5+slot7"
                r, _ = e.vcall(obj, SLOT_PROCESS18, bl, br, N)
                rets.append((s9, act, r, self.gate()))
            else:
                r, _ = e.vcall(obj, SLOT_ENTRY25, bl, br, N)
                rets.append((None, "", r, self.gate()))
            oL += e.floats(bl, N); oR += e.floats(br, N)
        return oL, oR, rets


def pack(L, R): return struct.pack("<%df" % len(L), *L) + struct.pack("<%df" % len(R), *R)


def stats(inL, inR, L, R):
    d = [a - b for a, b in zip(L + R, inL + inR)]
    rms = lambda xs: math.sqrt(sum(x * x for x in xs) / len(xs))
    holds = sum(1 for i in range(1, len(L)) if L[i] == L[i - 1])
    return {"rms_in": rms(inL + inR), "rms_out": rms(L + R), "rms_diff": rms(d), "max_abs_diff": max(abs(x) for x in d),
            "nonzero_out": sum(1 for x in L + R if x != 0.0), "distinct_L": len(set(L)), "equal_consecutive_L": holds,
            "identical_to_input": (L == inL and R == inR)}


def scenario(fx, sig, setp=(), mode="on", heap_fill=0, log_abi=False):
    run = Run(fx, heap_fill=heap_fill, log_abi=log_abi)
    run.insert_init()
    for idx, v in setp: run.set_param(idx, v)
    inL, inR = signal(sig)
    L, R, rets = run.process(inL, inR, mode)
    return run, inL, inR, L, R, rets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H007"))
    ap.add_argument("--effect", default="lofi", choices=sorted(EFFECTS))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    fx = EFFECTS[a.effect]
    rep = []; res = {"effect": a.effect, "fx": {k: (hex(v) if isinstance(v, int) else v) for k, v in fx.items()
                                                  if k not in ("params", "static_init")}}
    P = lambda s="": rep.append(s)
    fails = []
    def check(cond, msg):
        P(("  PASS " if cond else "  FAIL ") + msg)
        if not cond: fails.append(msg)

    # ---- C1/C2: build -----------------------------------------------------------------------------------------
    run = Run(fx, log_abi=True)
    e = run.e
    P("== C1 loader / C2 object (%s) ==" % a.effect)
    P("target sha256 verified; libs loaded: " + ", ".join("%s %s" % (k, v[:16]) for k, v in sorted(e.lib_hashes().items())))
    P("static init run: " + ", ".join(hex(x) for x in run.static_ran))
    check(run.vptr == fx["vtable"], "vptr after ctor = 0x%x (expected 0x%x)" % (run.vptr, fx["vtable"]))
    check(run.ctor_ret == run.obj, "ctor returns this")
    p0 = run.params()
    run.insert_init()
    p1 = run.params()
    P("init sequence: " + "; ".join(run.init_log))
    P("parameters after ctor -> after insert init (type, float +0x28, int +0x44):")
    for k in p0:
        P("  %-15s %d %.6g %d  ->  %d %.6g %d" % (k, p0[k]["type"], p0[k]["float"], p0[k]["int"], p1[k]["type"], p1[k]["float"],
                                                p1[k]["int"]))
    res["params_after_ctor"] = p0; res["params_after_init"] = p1

    # slot-14 index -> parameter object map (set each index on a fresh object, see which object changed)
    P("slot-14 index -> parameter object (set value 0.123 / int 1 on a fresh object):")
    idxmap = {}
    for idx in range(len(fx["params"]) + 1):
        r = Run(fx); r.insert_init(); before = r.params()
        rc = r.set_param(idx, 0.123 if idx < 6 else 1.0); after = r.params()
        ch = [k for k in before if before[k] != after[k]]
        idxmap[idx] = {"ret": rc, "changed": ch, "after": {k: after[k] for k in ch}}
        P("  idx %d -> ret %d, changed %s %s" % (idx, rc, ch, ["%.6g/%d" % (after[k]["float"], after[k]["int"]) for k in ch]))
    res["slot14_index_map"] = idxmap

    # ---- C3: process + determinism ------------------------------------------------------------------------------
    P(); P("== C3 process: %d blocks x %d samples, stereo; mode 'on' = processBlock 0x116860 effect calls with +0x9e=0 ==" % (NBLK, N))
    outs = {}
    for sig in ("impulse", "impulse_late", "silence", "sine1k"):
        h = []
        for rep_i in range(2):
            r, inL, inR, L, R, rets = scenario(fx, sig)
            h.append(sha(pack(L, R)))
        outs[sig] = (inL, inR, L, R, rets, r)
        with open(os.path.join(a.out, "out_%s_default.f32" % sig), "wb") as f: f.write(pack(L, R))
        st = stats(inL, inR, L, R)
        P("  %-8s sha256 %s  (2 independent emulators identical: %s)" % (sig, h[0][:16], h[0] == h[1]))
        P("           per block (slot9 ret, activation, slot18 ret, gate cur/target): b0 %s  b1 %s  b15 %s" %
          (rets[0], rets[1], rets[-1]))
        P("           rms_in %.6f rms_out %.6f rms_diff %.6f max|diff| %.6f nonzero_out %d distinct_L %d holds_L %d" %
          (st["rms_in"], st["rms_out"], st["rms_diff"], st["max_abs_diff"], st["nonzero_out"], st["distinct_L"],
           st["equal_consecutive_L"]))
        check(h[0] == h[1], "%s: bit-identical across two independent runs" % sig)
        check(all(x[2] == 0 for x in rets), "%s: every slot-18 call returned (ret 0)" % sig)
        res.setdefault("outputs", {})[sig] = {"sha256": h[0], "stats": st, "rets_first3": rets[:3]}
    imp, sl, sil = outs["impulse"], outs["sine1k"], outs["silence"]
    P("  impulse in L[0]=1.0, R[0]=0.5; out L[0:10]: " + " ".join("%.5g" % x for x in imp[2][:10]))
    P("                                  out R[0:10]: " + " ".join("%.5g" % x for x in imp[3][:10]))
    P("  impulse out L, first nonzero after 0: %s; max|L[64:]| %.3g" %
      (next((i for i in range(1, len(imp[2])) if imp[2][i] != 0.0), None), max(abs(x) for x in imp[2][64:])))
    P("  sine in  L[64:72]: " + " ".join("%.5f" % x for x in sl[0][64:72]))
    P("  sine out L[64:72]: " + " ".join("%.5f" % x for x in sl[2][64:72]))
    gains = []
    for b_ in (0, 1, 2, 4, 8, 15):
        sg = slice(b_ * N, (b_ + 1) * N)
        gi = math.sqrt(sum(x * x for x in sl[0][sg]) / N); go = math.sqrt(sum(x * x for x in sl[2][sg]) / N)
        dd = math.sqrt(sum((x - y) ** 2 for x, y in zip(sl[2][sg], sl[0][sg])) / N)
        gains.append((b_, round(go / gi, 4), round(dd, 5)))
    P("  sine1k per-block (block, rms gain out/in, rms diff): %s" % gains)
    res["sine1k_block_gain"] = gains
    sr = sl[5]; cut = sr.e.f32(sr.e.u32(sr.obj + 0x4a4) + 0x18); cutp = sr.e.f32(sr.obj + 0x2cc + 0x28)
    P("  LoFi filter object [obj+0x4a4]+0x18 = %.6g; 20*1000^CUTOFF(%.6g) = %.6g" % (cut, cutp, 20.0 * 1000.0 ** cutp))
    res["filter_cutoff_field"] = [cut, cutp, 20.0 * 1000.0 ** cutp]
    check(sil[2] == sil[0] and sil[3] == sil[1], "silence in -> exact silence out")
    check(not res["outputs"]["sine1k"]["stats"]["identical_to_input"], "sine1k output differs from input (mode on)")
    base = pack(sl[2], sl[3])

    P(); P("-- alternative A: processor FX off (+0x9e = 1, ctor default): slot 9 + slot 18 only --")
    _, inL, inR, Lo, Ro, ro = scenario(fx, "sine1k", mode="off")
    sto = stats(inL, inR, Lo, Ro)
    P("  off: identical_to_input %s; gate per block %s; slot18 rets %s" % (sto["identical_to_input"], ro[0][3],
                                                                         sorted(set(x[2] for x in ro))))
    res["off_identical_to_input"] = sto["identical_to_input"]
    check(sto["identical_to_input"], "FX off: output is the input, bit-exact (slot 18 returns before slot 25)")

    P(); P("-- alternative B: slot 25 called directly (no gate, no dry/wet write-back) vs. mode on --")
    _, _, _, L25, R25, _ = scenario(fx, "sine1k", mode="s25")
    st25 = stats(sl[0], sl[1], L25, R25)
    d = [x - y for x, y in zip(L25 + R25, sl[2] + sl[3])]
    P("  s25 sha %s; identical to mode on: %s; rms(s25 - on) %.3g; s25 rms_diff vs input %.6f" %
      (sha(pack(L25, R25))[:16], pack(L25, R25) == base, math.sqrt(sum(x * x for x in d) / len(d)), st25["rms_diff"]))
    res["s25_direct"] = {"sha256": sha(pack(L25, R25)), "identical_to_on": pack(L25, R25) == base, "stats": st25}

    # ---- C4: effect-caused, parameter sensitivity, alternatives -------------------------------------------------
    P(); P("== C4 parameter changes through slot 14 0x105d24 before processing (sine1k, mode on) ==")
    variants = {
        "mix0 (MIXRATIO=0.0)": [(5, 0.0)],
        "mix0.5 (MIXRATIO=0.5)": [(5, 0.5)],
        "bitdepth0 (BITDEPTH=0.0)": [(2, 0.0)],
        "bitdepth0.5 (BITDEPTH=0.5)": [(2, 0.5)],
        "reduction0 (REDUCTION=0.0)": [(1, 0.0)],
        "reduction0.5 (REDUCTION=0.5)": [(1, 0.5)],
        "cutoff0.2 (CUTOFF=0.2)": [(3, 0.2)],
        "preamp1 (PREAMP=1.0)": [(0, 1.0)],
    }
    res["variants"] = {}
    for name, sp in variants.items():
        _, inL, inR, L, R, _ = scenario(fx, "sine1k", setp=sp)
        st = stats(inL, inR, L, R); bb = pack(L, R)
        with open(os.path.join(a.out, "out_sine1k_%s.f32" % name.split()[0]), "wb") as f: f.write(bb)
        P("  %-28s sha %s differs_from_default %-5s identical_to_input %-5s rms_diff %.6f distinct_L %4d holds_L %4d" %
          (name, sha(bb)[:16], bb != base, st["identical_to_input"], st["rms_diff"], st["distinct_L"], st["equal_consecutive_L"]))
        res["variants"][name] = {"sha256": sha(bb), "differs_from_default": bb != base, "stats": st}
    check(sum(1 for v in res["variants"].values() if v["differs_from_default"]) >= 1,
          "at least one slot-14 parameter change changes the output")

    P(); P("-- late unit impulse (block 10 sample 5) per FILTERTYPE (slot 14 index 6), mode on: first 8 output samples L --")
    k0 = 10 * N + 5; res["impulse_late_by_filtertype"] = {}
    il = outs["impulse_late"]
    P("  default (FILTERTYPE int 3): " + " ".join("%.5g" % x for x in il[2][k0:k0 + 8]))
    for ftv in (0.0, 1.0, 2.0):
        _, inL, inR, L, R, _ = scenario(fx, "impulse_late", setp=[(6, ftv)])
        bb = pack(L, R)
        with open(os.path.join(a.out, "out_impulse_late_ft%d.f32" % int(ftv)), "wb") as f: f.write(bb)
        P("  FILTERTYPE %.0f: %s   sha %s  sum|L[k0+1:]| %.4g" % (ftv, " ".join("%.5g" % x for x in L[k0:k0 + 8]), sha(bb)[:16],
                                                            sum(abs(x) for x in L[k0 + 1:])))
        res["impulse_late_by_filtertype"][str(ftv)] = {"sha256": sha(bb), "first8_L": L[k0:k0 + 8]}
    _, inL, inR, L, R, _ = scenario(fx, "impulse_late", setp=[(6, 1.0), (5, 0.0)])
    P("  FILTERTYPE 1 with MIXRATIO 0.0: identical to input %s" % (L == inL and R == inR))
    check(L == inL and R == inR, "MIXRATIO 0 (wet = 0): output = input bit-exact even with an active filter")

    P(); P("-- alternative C: uninitialised-heap sensitivity (heap pre-filled 0xA5 instead of 0x00) --")
    _, _, _, Lh, Rh, _ = scenario(fx, "sine1k", heap_fill=0xA5)
    P("  sine1k with heap 0xA5: identical to heap 0x00: %s" % (pack(Lh, Rh) == base))
    res["heap_fill_independent"] = pack(Lh, Rh) == base

    # ---- C5: float ABI -------------------------------------------------------------------------------------------
    P(); P("== C5 float ABI at call sites (emulation: static init, build, insert init, slot-14 calls, 2 blocks) ==")
    run.set_param(5, 0.25); run.set_param(3, 0.3); run.set_param(1, 0.2); run.set_param(0, 0.4)
    sL, sR = signal("sine1k", 2); run.process(sL, sR)
    P("  static (capstone), per call site: core-register float setup / VFP arg-register writes / result moves:")
    sabi = static_abi(); res["float_abi_static"] = sabi
    for x in sabi:
        P("   %s %-58s %s -> %s" % (x["site"], x["what"], x["call"], x["target"]))
        P("        args in core: %s | writes to s0-s3/d0-d1 before call: %s | result read from r0: %s | from s0/d0: %s" %
          ("; ".join(x["core_arg_setup"][-4:]) or "-", x["vfp_arg_reg_writes_before"] or "none",
           "; ".join(x["result_from_core"]) or "-", x["result_from_s0_d0"] or "none"))
    P("  dispatcher/effect functions entered in this instrumented run (insert init + 4 slot-14 calls + 2 blocks):")
    for a_, nm in sorted(COUNT_SITES.items()):
        P("   0x%x %-40s x%d" % (a_, nm, run.counts.get(a_, 0)))
    res["instrumented_counts"] = {hex(k): run.counts.get(k, 0) for k in COUNT_SITES}
    abi = []
    P("  emulation:")
    for rec in run.abi:
        s = rec["site"]
        if s == 0x105d24:
            P("  0x105d24 setParameter entry: r1=%d r2=0x%08x (=%.6g as float) s0=0x%08x" % (rec["r"][1], rec["r"][2],
                                                                                         u2f(rec["r"][2]), rec["s0"]))
            abi.append({"site": hex(s), "arg_core_r2": u2f(rec["r"][2]), "s0": rec["s0"]}); continue
        if "ret_r0" not in rec: continue
        if "pow" in rec["what"]:
            x = u2d(rec["r"][0] | rec["r"][1] << 32); y = u2d(rec["r"][2] | rec["r"][3] << 32)
            got = u2d(rec["ret_r0"] | rec["ret_r1"] << 32); ref = math.pow(x, y)
            ulp = abs(d2u(got) - d2u(ref)) if got > 0 and ref > 0 else None
            hx = u2d(rec["d0"]), u2d(rec["d1"])
            P("  0x%x %s: core args pow(%.17g, %.17g) -> r0:r1 %.17g (host pow %.17g, %s ulp); d0,d1 at call = %.6g, %.6g; d0 after = %.6g"
              % (s, rec["what"], x, y, got, ref, ulp, hx[0], hx[1], u2d(rec["ret_d0"])))
            abi.append({"site": hex(s), "what": rec["what"], "x": x, "y": y, "ret_core": got, "host": ref, "ulp": ulp,
                        "d0_at_call": hx[0], "d1_at_call": hx[1], "d0_after": u2d(rec["ret_d0"])})
        else:   # log10f
            x = u2f(rec["r"][0]); got = u2f(rec["ret_r0"]); ref = u2f(f2u(math.log10(x)))
            P("  0x%x %s: core arg r0 = %.9g -> r0 %.9g (host log10 %.9g); s0 at call 0x%08x, s0 after 0x%08x" %
              (s, rec["what"], x, got, ref, rec["s0"], rec["ret_s0"]))
            abi.append({"site": hex(s), "what": rec["what"], "x": x, "ret_core": got, "host": ref, "s0_at_call": rec["s0"],
                        "s0_after": rec["ret_s0"]})
    res["float_abi"] = abi

    # ---- C1 import list -----------------------------------------------------------------------------------------
    P(); P("== C1 imports reached (all %d emulator instances of this run aggregated) ==" % len(RUNS))
    agg = {}
    for rr in RUNS:
        for nm, served, cnt, lr in rr.e.import_report():
            g = agg.setdefault(nm, [served, 0, lr]); g[1] += cnt
    for nm, (served, cnt, lr) in sorted(agg.items()):
        P("  %-26s x%-6d first call site 0x%x  -> %s" % (nm, cnt, lr - 4, served))
    rbw_all = sorted({w for rr in RUNS for w in rr.e.bss_rbw})
    reals = sorted({n for n, s in e.served.items() if s.startswith("real")})
    P("  real-library imports resolved (main binary GOT -> decoded/lib): %d, e.g. %s" % (len(reals), ", ".join(reals[:8])))
    P("  .bss words read before any write, all instances: %d %s" % (len(rbw_all), [hex(k) for k in rbw_all][:10]))
    res["imports"] = {k: v for k, v in sorted(agg.items())}; res["bss_read_before_write"] = rbw_all
    check(len(rbw_all) == 0, "no .bss read-before-write after static init (all instances)")

    # negative tests of the abort paths
    P(); P("== C1 abort-path self-tests ==")
    t = Emu()
    try:
        t.call(0x8, 0)   # address 0x8: unmapped -> must abort
        check(False, "unmapped fetch aborts")
    except EmuAbort as x:
        check("unmapped" in str(x), "unmapped fetch aborts: %s" % x)
    t = Emu()
    plt = {n: a for a, n in __import__("sp16img").Image().plt().items()}
    try:
        t.call(plt["pthread_create"], 0)
        check(False, "unlisted import aborts")
    except EmuAbort as x:
        check("unlisted import 'pthread_create'" in str(x), "unlisted import aborts: %s" % x)
    t = Emu()
    try:
        t.call(fx["ctor"], 0x1000, 44100, 64)   # this = unmapped page -> must abort with PC inside the ctor chain
        check(False, "unmapped write aborts")
    except EmuAbort as x:
        check("unmapped" in str(x), "unmapped data access aborts: %s" % x)

    t = Emu(vfp=False)
    try:
        t.call(0x137cc)
        check(False, "VFP disabled -> abort")
    except EmuAbort as x:
        check(True, "alternative: with CPACR/FPEXC VFP enable removed, the static init aborts: %s" % str(x)[:90])

    P(); P("RESULT: %d failed checks" % len(fails))
    txt = "\n".join(rep) + "\n"
    open(os.path.join(a.out, "h007_report.txt"), "w").write(txt)
    json.dump(res, open(os.path.join(a.out, "h007.json"), "w"), indent=1, sort_keys=True, default=str)
    print(txt)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
