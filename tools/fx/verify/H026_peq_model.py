#!/usr/bin/env python3
"""H026 — ParametricEqualizer (2-band EQ, Insert index 2) algorithm reconstruction: 1.60 emulation (ctor 0x10baec, slot 25
0x10ae70 called directly) vs. the own-code Python model harness/models/peq.py.

Sections (criteria of kb/cycles/007.md):
  C1  parameters: registration calls 0xf1850 / 0xf1a00 logged during the real ctor (name, id, min, max, default), ctor and
      Insert-default values, slot-14 index -> parameter object map.
  C2  signal flow: dynamic call order inside slot 25 (code hooks on the routines it reaches), per-block call counts.
  C3  shared vs new blocks: vptrs of every sub-object (parameters, band containers, stages, gates, gain ramps), RTTI names,
      direct callees (capstone) of ctor / slot 25 / band ctor / band process.
  C4  parameter formulas: set each parameter through EffectBase slot 14 0x105d24 at 7 values after one defaults block (F026),
      read the stored targets; coefficients of every stage kind after the glide settles vs closed-form formulas; libm
      powf/log10f vs the fdlibm re-implementation; step-count / gated-jump thresholds.
  C5  state layout dump (emulated object after ctor / Insert init / block 0) and model-vs-emulation field comparison.
  C6  model vs emulation matrix: impulse, late impulse, 1 kHz sine, white noise (seed 1234), 16 x 64 stereo, settings covering
      both bands, every stage kind, intermediate values and mid-run changes; per-case bit-exact count and max |error|.
  C7  alternatives: RBJ cookbook shelf/peak vs the 1.60 form; correctly rounded powf vs fdlibm powf; bands in parallel vs in
      series; kind-3/4 gain inside the filter vs a separate GainRamp; type 1 = high shelf (DC / Nyquist gains); first block
      after a closed gate unfiltered; BANDxTYPE 5.
Outputs only to --out (default harness/out/H026/). Run: .venv/bin/python -B harness/H026_peq_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
from emu import Emu, EmuAbort, f2u, u2f, init_array, SP     # noqa: E402
import H007_effect_emu as H7                                  # noqa: E402
import sp16img                                                # noqa: E402
import peq as M                                               # noqa: E402
import lofi as LM                                             # noqa: E402
import fdlibm_powf as FL                                      # noqa: E402

N = 64
FS = 44100
NBLK = 16
FX = dict(ctor=0x10baec, size=0x4a0, vtable=0x842198, ctor_args=(44100, 64), insert_index=2, static_init=[0x13aa8],
          params=[(nm, 0x1b8 + 0x5c * k) for k, nm in enumerate(M.PARAM_NAMES)])
PARAM_OFF = dict((k, off) for k, (_, off) in enumerate(FX["params"]))
REG_FUNCS = {0xf1850: "LinearParameter float ctor 0xf1850", 0xf1a00: "LinearParameter choice ctor 0xf1a00"}
VT_NAMES = {0x840ac8: "LinearParameter", 0x840e40: "SignalGate", 0x840c28: "IirLpf2ndOrder", 0x840c48: "IirHpf2ndOrder",
            0x83bcc0: "LowShelvingFilter", 0x83bcf0: "PeakingFilter", 0x842198: "ParametricEqualizer"}
PLT_POWF, PLT_LOG10F = 0xff40, 0x10ab0
FLOW_SITES = {0x10a4f0: "PEQ_updateChangedParams", 0x10c208: "PEQBand_process", 0x10abdc: "PEQBand_rampSetup",
              0x10c070: "PEQBand_swapType", 0xe27b8: "IirFilter2_processKernel", 0xe16dc: "IirFilter_process",
              0xe2ab4: "IirFilter2_configure", 0xe2540: "LowShelving_calcCoefs", 0xe2440: "Peaking_calcCoefs",
              0xe1ca0: "IirLpf_calcCoefs", 0xe1bb8: "IirHpf_calcCoefs", 0xe89f0: "GainRamp_process",
              0xe895c: "GainRamp_setTarget", 0xe9358: "GainRamp_setNow", 0xf521c: "SignalGate_apply",
              0xf5188: "SignalGate_close", 0xf5198: "SignalGate_open", 0x10a4d8: "PEQ_slot26_setDryWet"}


def sha(b): return hashlib.sha256(b).hexdigest()
def f32(x): return u2f(f2u(x))


# ------------------------------------------------------------------------------------------------------------------------
class EmuPEQ:
    """1.60 ParametricEqualizer built by its ctor + Insert init (H007 sequence), processed by calling slot 25 directly."""
    def __init__(self, defaults=True, log_regs=False, flow=False):
        self.fx = FX; self.e = e = Emu(); self.init_log = []; self.regs = []; self.trace = None
        for f in FX["static_init"]:
            assert f in init_array(e), "0x%x not an .init_array entry" % f
            e.call(f)
        if log_regs:
            for a_, nm in REG_FUNCS.items():
                def cb(em, a_=a_, nm=nm):
                    sp = em.uc.reg_read(SP)
                    self.regs.append({"func": nm, "obj_off": em.r(0), "name_ptr": em.r(1), "id": em.r(2), "r3": em.r(3),
                                      "stack": [em.u32(sp + 4 * k) for k in range(4)]})
                e.add_watch(a_, cb)
        if flow:
            for a_ in FLOW_SITES:
                e.add_watch(a_, lambda em, a_=a_: self.trace.append(a_) if self.trace is not None else None)
        self.obj = self.o = e.malloc(FX["size"], "new (harness: PEQ object)")
        r0, _ = e.call(FX["ctor"], self.obj, *FX["ctor_args"])
        assert r0 == self.obj
        self.vptr = e.u32(self.obj)
        if defaults: H7.Run.insert_init(self)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set_param(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def f(self, a): return self.e.f32(a)
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]
    def b(self, a): return self.e.rd(a, 1)[0]

    def iir2(self, s):
        f, d, u = self.f, self.d, self.u
        cf = u(s + 0x8c)
        return {"vptr": hex(u(s)), "fs+4": self.i(s + 4), "fc+8": f(s + 8), "fc_min+0xc": f(s + 0xc), "fc_max+0x10": f(s + 0x10),
                "Q+0x18": d(s + 0x18), "Q_min+0x20": d(s + 0x20), "Q_max+0x28": d(s + 0x28), "Q_default+0x30": d(s + 0x30),
                "p+0x38": d(s + 0x38), "p_min+0x40": d(s + 0x40), "p_max+0x48": d(s + 0x48), "gdb+0x58": d(s + 0x58),
                "g_min+0x60": d(s + 0x60), "g_max+0x68": d(s + 0x68), "flag+0x78": self.b(s + 0x78),
                "b0,b1,b2,a1,a2 [+0x8c] (lane L)": [f(cf + 8 * j) for j in range(5)],
                "lanes equal": all(f(cf + 8 * j) == f(cf + 8 * j + 4) for j in range(5))}

    def biquad(self, s):
        f, u = self.f, self.u
        return {"vptr": hex(u(s)), "nyq+4": f(s + 4), "fs+8": self.i(s + 8), "fc+0xc": f(s + 0xc), "Q+0x40": self.d(s + 0x40),
                "b0,b1,b2,a1,a2 +0x28..": [f(s + 0x28 + 4 * j) for j in range(5)], "k+0x24": f(s + 0x24), "flag+0x48": self.b(s + 0x48)}

    def gate(self, g):
        f, i = self.f, self.i
        return {"vptr": hex(self.u(g)), "state+0x20": i(g + 0x20), "cur+0x24": f(g + 0x24), "target+0x28": f(g + 0x28),
                "inc+0x2c": f(g + 0x2c), "rem+0x30": i(g + 0x30), "N+0x38": i(g + 0x38), "off+0x40": f(g + 0x40), "on+0x44": f(g + 0x44)}

    def gainramp(self, G):
        f, i = self.f, self.i
        return {"inc+0": f(G), "target+4": f(G + 4), "cur+8": f(G + 8), "rem+0xc": i(G + 0xc), "N+0x10": i(G + 0x10),
                "invN+0x14": f(G + 0x14), "delay+0x18": i(G + 0x18), "idle+0x1c": self.b(G + 0x1c), "state+0x20": i(G + 0x20)}

    def band(self, B):
        u, i, f, b = self.u, self.i, self.f, self.b
        stages = []
        for k in range(u(B + 8)):
            S = u(u(B) + 4 * k)
            kind = i(S + 0xc); p0, p4, p8 = u(S), u(S + 4), u(S + 8)
            stages.append({"kind+0xc": kind, "obj+0": (self.biquad(p0) if p0 else None), "obj+4": (self.iir2(p4) if p4 else None),
                           "gainramp+8": hex(p8)})
        return {"count+8": u(B + 8), "cap+4": u(B + 4), "gate+0xc": self.gate(u(B + 0xc)), "gainramp+0x10": self.gainramp(u(B + 0x10)),
                "gainramp ptr": hex(u(B + 0x10)), "pending+0x14": i(B + 0x14), "cur+0x18": i(B + 0x18),
                "f_t+0x1c": f(B + 0x1c), "f_c+0x20": f(B + 0x20), "f_mult+0x24": f(B + 0x24), "f_steps+0x2c": i(B + 0x2c),
                "q_t+0x30": f(B + 0x30), "q_c+0x34": f(B + 0x34), "q_mult+0x38": f(B + 0x38), "q_steps+0x40": i(B + 0x40),
                "g_t+0x44": f(B + 0x44), "g_c+0x48": f(B + 0x48), "g_step+0x4c": f(B + 0x4c), "g_steps+0x54": i(B + 0x54),
                "next+0x58": f(B + 0x58), "maxsteps+0x5c": i(B + 0x5c), "recompute+0x60": b(B + 0x60),
                "stepnow+0x61": b(B + 0x61), "dirty+0x62": b(B + 0x62), "stages": stages}

    def state(self):
        o = self.o; f, i = self.f, self.i
        return {"EffectBase dry+0x10 / wet+0x14": [f(o + 0x10), f(o + 0x14)],
                "band1 +0x498": self.band(self.u(o + 0x498)), "band2 +0x49c": self.band(self.u(o + 0x49c)),
                "params (last, cur)": {M.PARAM_NAMES[k]: ([f(o + off + 0x24), f(o + off + 0x28)] if k < 6 else
                                                          [i(o + off + 0x40), i(o + off + 0x44)]) for k, off in PARAM_OFF.items()},
                "globals 0xf52f00..0c": [f(0xf52f00 + 4 * k) for k in range(4)]}


# ------------------------------------------------------------------------------------------------------------------------
def signal(kind, nblk=NBLK, seed=1234):
    tot = N * nblk
    if kind == "impulse":
        L = [1.0 if k == 0 else 0.0 for k in range(tot)]; R = [-0.5 if k == 0 else 0.0 for k in range(tot)]
    elif kind == "impulse_b4":
        k0 = 4 * N + 3
        L = [0.9 if k == k0 else 0.0 for k in range(tot)]; R = [-0.45 if k == k0 else 0.0 for k in range(tot)]
    elif kind == "sine1k":
        L = [0.5 * math.sin(2 * math.pi * 1000.0 * k / FS) for k in range(tot)]
        R = [0.5 * math.cos(2 * math.pi * 1000.0 * k / FS) for k in range(tot)]
    elif kind == "noise":
        g = random.Random(seed)
        L = [g.uniform(-0.8, 0.8) for _ in range(tot)]; R = [g.uniform(-0.8, 0.8) for _ in range(tot)]
    else:
        raise ValueError(kind)
    return [f32(x) for x in L], [f32(x) for x in R]


def make(which, model_cls=None):
    if which == "emu": return EmuPEQ()
    m = (model_cls or M.PEQ)(); m.insert_defaults(); return m


def run_both(sig, setp=(), events=(), nblk=NBLK, emu_only=False, prime=0, model_cls=None, model_only=False):
    """prime: silent slot-25 blocks first (applies the Insert defaults, F026); setp after that; events [(block, idx, v)]."""
    L, R = signal(sig, nblk)
    out = {}
    for which in ("emu", "model"):
        if (which == "model" and emu_only) or (which == "emu" and model_only): continue
        x = make(which, model_cls)
        for _ in range(prime): x.process([0.0] * N, [0.0] * N)
        for idx, v in setp: x.set_param(idx, v)
        oL, oR = [], []
        for b in range(nblk):
            for (eb, idx, v) in events:
                if eb == b: x.set_param(idx, v)
            l, r = x.process(L[b * N:(b + 1) * N], R[b * N:(b + 1) * N])
            oL += l; oR += r
        out[which] = (oL, oR, x)
    return L, R, out


def pack(L, R): return struct.pack("<%df" % len(L), *L) + struct.pack("<%df" % len(R), *R)


def compare(a, b):
    A = [f32(v) for v in a[0] + a[1]]; B = [f32(v) for v in b[0] + b[1]]
    bit = sum(1 for x, y in zip(A, B) if f2u(x) == f2u(y))
    err = max((abs(x - y) for x, y in zip(A, B)), default=0.0)
    first = next((k for k in range(len(A)) if f2u(A[k]) != f2u(B[k])), None)
    return {"n": len(A), "bit_exact": bit, "max_abs_err": err, "first_diff_index": first}


def rms(xs): return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else 0.0


# closed-form coefficients (independent of the model's classes), computed from the targets
def cf_shelf(fc, Q, gdb, fs=FS):
    V = math.pow(10.0, gdb / 20.0); t = math.tan(float(fc) * (math.pi / fs)); K = (t * (1 / (2 * math.pi))) * (2 * math.pi)
    iq = 1.0 / Q; K2 = K * K; nrm = 1.0 / ((K * iq + 1.0) + K2); s = (math.sqrt(V) * K) * iq
    return [f32(((s + 1.0) + K2 * V) * nrm), f32(((K2 + K2) * V - 2.0) * nrm), f32((K2 * V + (1.0 - s)) * nrm),
            f32(((K2 + K2) - 2.0) * nrm), f32(((1.0 - K * iq) + K2) * nrm)]


def cf_peak(fc, Q, gdb, fs=FS):
    V = math.pow(10.0, gdb / 20.0); t = math.tan(float(fc) * (math.pi / fs)); K = (t * (1 / (2 * math.pi))) * (2 * math.pi)
    iq = 1.0 / Q; K2 = K * K; kq = K * iq; nrm = 1.0 / ((kq + 1.0) + K2); vk = (V * K) * iq
    a1 = f32(((K2 + K2) - 2.0) * nrm)
    return [f32(((vk + 1.0) + K2) * nrm), a1, f32(((1.0 - vk) + K2) * nrm), a1, f32(((1.0 - kq) + K2) * nrm)]


def cf_rbj(kind, fc, Q, gdb, fs=FS):
    """RBJ Audio-EQ-Cookbook low shelf / peaking (alternative hypothesis C7a)."""
    A = math.pow(10.0, gdb / 40.0); w0 = 2 * math.pi * fc / fs; c = math.cos(w0); al = math.sin(w0) / (2 * Q)
    if kind == "peak":
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        sa = 2 * math.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sa), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sa)]
        a = [(A + 1) + (A - 1) * c + sa, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sa]
    return [f32(b[0] / a[0]), f32(b[1] / a[0]), f32(b[2] / a[0]), f32(a[1] / a[0]), f32(a[2] / a[0])]


def H_at(c, z):                                               # |H(z)| for coefficients [b0, b1, b2, a1, a2]
    b0, b1, b2, a1, a2 = c
    zi = 1 / z
    return abs((b0 + b1 * zi + b2 * zi * zi) / (1 + a1 * zi + a2 * zi * zi))


# index: 0 B1FREQUENCY 1 B1GAIN 2 B1Q 3 B2FREQUENCY 4 B2GAIN 5 B2Q 6 BAND1TYPE 7 BAND2TYPE
C6_CASES = [
    ("cold_defaults", 0, [], []),                                                   # low shelf + high shelf at 997.8 Hz, 0 dB
    ("b1_lowshelf_boost", 2, [(6, 0.0), (0, 0.3), (1, 0.9), (2, 0.4)], []),
    ("b1_highshelf_cut", 2, [(6, 1.0), (0, 0.6), (1, 0.2), (2, 0.15)], []),
    ("b2_peak_boost", 2, [(7, 2.0), (3, 0.5), (4, 0.85), (5, 0.7)], []),
    ("b1_peak_cut_b2_lowshelf", 2, [(6, 2.0), (0, 0.4), (1, 0.35), (2, 0.25), (7, 0.0), (3, 0.2), (4, 0.95), (5, 0.55)], []),
    ("b1_lpf_b2_hpf", 2, [(6, 3.0), (0, 0.45), (1, 0.75), (2, 0.6), (7, 4.0), (3, 0.25), (4, 0.6), (5, 0.3)], []),
    ("b1_hpf_b2_lpf", 2, [(6, 4.0), (0, 0.35), (1, 0.55), (2, 0.8), (7, 3.0), (3, 0.7), (4, 0.7), (5, 0.1)], []),
    ("cold_types_set", 0, [(6, 2.0), (0, 0.4), (1, 0.9), (7, 3.0), (3, 0.5)], []),  # applied before the first block
    ("extreme", 2, [(6, 2.0), (0, 1.0), (1, 1.0), (2, 1.0), (7, 2.0), (3, 0.0), (4, 0.0), (5, 0.0)],
     [(8, 0, 0.0), (8, 1, 0.0), (8, 2, 0.0), (8, 3, 1.0), (8, 4, 1.0), (8, 5, 1.0)]),
    ("seq_glide", 2, [(6, 2.0), (0, 0.5), (1, 0.8), (2, 0.5)],
     [(2, 0, 0.55), (4, 1, 0.75), (5, 2, 0.6), (7, 0, 0.45), (9, 1, 0.9), (10, 2, 0.3), (12, 3, 0.62), (13, 4, 0.7)]),
    ("seq_jumps", 2, [(6, 0.0), (7, 1.0), (1, 0.8), (4, 0.4)],
     [(2, 0, 0.9), (5, 1, 0.3), (8, 2, 1.0), (11, 3, 0.1), (13, 5, 0.0)]),
    ("seq_type_switch", 2, [(6, 0.0), (7, 1.0), (1, 0.85), (4, 0.3), (2, 0.4)],
     [(2, 6, 1.0), (4, 7, 2.0), (6, 6, 3.0), (7, 0, 0.6), (9, 7, 4.0), (11, 6, 2.0), (12, 1, 0.5), (14, 7, 0.0)]),
]
C6_SIGNALS = ["impulse", "impulse_b4", "sine1k", "noise"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H026"))
    ap.add_argument("--quick", action="store_true", help="only C1/C5 and the cold defaults case (debug)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    L1, R1 = signal("sine1k", 1)

    # ---------------- C1 parameters ----------------------------------------------------------------------------------
    P("== C1 parameters (registration calls during the real 1.60 ctor 0x10baec) ==")
    x = EmuPEQ(defaults=False, log_regs=True)
    check(x.vptr == FX["vtable"], "vptr after ctor = 0x%x (ParametricEqualizer)" % x.vptr)
    regs = []
    for r in x.regs:
        nm = im.cstr(r["name_ptr"]); off = r["obj_off"] - x.o
        fl = r["func"].startswith("LinearParameter float")
        rng = (u2f(r["r3"]), u2f(r["stack"][0]), u2f(r["stack"][1])) if fl else (r["r3"], r["stack"][0], r["stack"][1])
        regs.append({"name": nm, "name_ptr": hex(r["name_ptr"]), "id": r["id"], "obj_off": hex(off), "kind": "float" if fl else "choice",
                     "min,max,default": rng})
        P("  id %d %-11s (str 0x%x) at obj+0x%x  %-6s min %s max %s default %s" %
          (r["id"], nm, r["name_ptr"], off, "float" if fl else "choice", rng[0], rng[1], rng[2]))
    res["C1_registrations"] = regs
    check([r["name"] for r in regs] == M.PARAM_NAMES and [r["id"] for r in regs] == list(range(8)) and
          [int(r["obj_off"], 16) for r in regs] == [off for _, off in FX["params"]],
          "8 parameters registered, ids 0..7 in obj order +0x1b8 + 0x5c*k: %s" % [r["name"] for r in regs])
    s_ctor = x.state()
    P("  ctor (last, cur): %s" % s_ctor["params (last, cur)"])
    check(all(s_ctor["params (last, cur)"][nm][0] == (f32(M.CTOR_VALUES[k]) if k < 6 else M.CTOR_VALUES[k])
              for k, nm in enumerate(M.PARAM_NAMES)), "ctor 'last' values = model CTOR_VALUES %s" % M.CTOR_VALUES)
    xi = EmuPEQ(); s_init = xi.state()
    P("  after Insert init (slot 52 case 2) (last, cur): %s" % s_init["params (last, cur)"])
    exp_init = {nm: (f32(M.INSERT_DEFAULTS[k]) if k < 6 else int(M.INSERT_DEFAULTS[k])) for k, nm in enumerate(M.PARAM_NAMES)}
    check(all(s_init["params (last, cur)"][nm][1] == exp_init[nm] for nm in M.PARAM_NAMES),
          "Insert defaults = model INSERT_DEFAULTS (freq 0.566, gain 2/3, Q 6/99, BAND1TYPE 0, BAND2TYPE 1)")
    res["C1_ctor_params"] = s_ctor["params (last, cur)"]; res["C1_insert_defaults"] = s_init["params (last, cur)"]
    idxmap = {}
    for idx in range(9):
        y = EmuPEQ(); y.process(L1, R1); before = y.state()["params (last, cur)"]
        rc = y.set_param(idx, 0.123 if idx < 6 else 2.0); after = y.state()["params (last, cur)"]
        idxmap[idx] = {"ret": rc, "changed": [k for k in before if before[k] != after[k]]}
    P("  slot-14 index -> changed parameter: %s" % {k: (v["changed"], v["ret"]) for k, v in idxmap.items()})
    check(all(idxmap[k]["changed"] == [M.PARAM_NAMES[k]] and idxmap[k]["ret"] == 0 for k in range(8)) and
          idxmap[8]["changed"] == [] and idxmap[8]["ret"] == 3, "slot-14 index k sets parameter id k (k = 0..7, ret 0); index 8 "
          "changes nothing (ret 3)")
    res["C1_slot14_map"] = idxmap
    P("  EffectBase dry +0x10 / wet +0x14 before block 0: %s" % xi.state()["EffectBase dry+0x10 / wet+0x14"])
    xi.process(L1, R1)
    dw = xi.state()["EffectBase dry+0x10 / wet+0x14"]
    check(dw == [0.0, 1.0], "after one slot-25 block: dry +0x10 = 0.0, wet +0x14 = 1.0 (slot 26 0x10a4d8, no MIX parameter): %s" % dw)

    # ---------------- C2 signal flow (dynamic order) -------------------------------------------------------------------
    P(); P("== C2 signal flow: routines reached inside slot 25 (code hooks), in order ==")
    xf = EmuPEQ(flow=True)
    traces = []
    for b in range(4):
        xf.trace = []
        if b == 2: xf.set_param(0, 0.6); xf.set_param(7, 2.0)
        xf.process(L1, R1)
        traces.append(xf.trace); xf.trace = None
    def compact(tr):
        out = []
        for a_ in tr:
            nm = FLOW_SITES[a_]
            if out and out[-1][0] == nm: out[-1][1] += 1
            else: out.append([nm, 1])
        return " > ".join("%s%s" % (n, "x%d" % c if c > 1 else "") for n, c in out)
    for b, tr in enumerate(traces):
        P("  block %d%s: %s" % (b, " (after B1FREQUENCY 0.6, BAND2TYPE 2)" if b == 2 else "", compact(tr)))
    res["C2_traces"] = [[FLOW_SITES[a_] for a_ in tr] for tr in traces]
    t3 = [FLOW_SITES[a_] for a_ in traces[3]]
    top = [n for n in t3 if n in ("PEQ_updateChangedParams", "PEQBand_process", "PEQ_slot26_setDryWet")]
    check(top == ["PEQ_updateChangedParams", "PEQBand_process", "PEQBand_process", "PEQ_slot26_setDryWet"],
          "slot 25 order: 0x10a4f0 params -> 0x10c208 band 1 -> 0x10c208 band 2 -> slot 26 0x10a4d8")
    t0 = [FLOW_SITES[a_] for a_ in traces[0]]
    check("IirFilter2_processKernel" not in t0 and "GainRamp_process" not in t0 and t0.count("PEQBand_swapType") == 2,
          "block 0 (gates closed): each band swaps in its type and only applies the gate; no filter / GainRamp runs")

    # ---------------- C3 shared vs new blocks -------------------------------------------------------------------------
    P(); P("== C3 shared vs new blocks: vptrs inside an emulated PEQ, RTTI, callees ==")
    o = xi.o; vps = {}
    for nm, off in FX["params"]: vps["param %s +0x%x" % (nm, off)] = xi.u(o + off)
    sb = xi.state()
    for bn in ("band1 +0x498", "band2 +0x49c"):
        bd = sb[bn]
        vps["%s gate +0xc" % bn] = int(bd["gate+0xc"]["vptr"], 16)
        for st in bd["stages"]:
            for slot in ("obj+0", "obj+4"):
                if st[slot]: vps["%s stage kind %d %s" % (bn, st["kind+0xc"], slot)] = int(st[slot]["vptr"], 16)
    for k, v in vps.items(): P("  %-40s vptr 0x%x %s" % (k, v, VT_NAMES.get(v, "?")))
    res["C3_vptrs"] = {k: hex(v) for k, v in vps.items()}
    rtti = {}
    for vt in (0x83bcc0, 0x83bcf0, 0x840c28, 0x840c48, 0x842198):
        ti = im.u32(vt - 4); bti = im.u32(ti + 8)
        rtti[hex(vt)] = (im.cstr(im.u32(ti + 4)), im.cstr(im.u32(bti + 4)))
    P("  RTTI (vtable: class, base): %s" % rtti); res["C3_rtti"] = rtti
    kinds = {bn: [(st["kind+0xc"], VT_NAMES[int((st["obj+0"] or st["obj+4"])["vptr"], 16)]) for st in sb[bn]["stages"]]
             for bn in ("band1 +0x498", "band2 +0x49c")}
    exp = [(0, "LowShelvingFilter"), (1, "LowShelvingFilter"), (2, "PeakingFilter"), (3, "IirLpf2ndOrder"), (4, "IirHpf2ndOrder")]
    check(all(v == exp for v in kinds.values()), "each band holds 5 stages: 0/1 LowShelvingFilter, 2 PeakingFilter, 3 IirLpf2ndOrder, "
          "4 IirHpf2ndOrder (stage ctor 0x10a928)")
    gr = [sb[bn]["gainramp ptr"] for bn in ("band1 +0x498", "band2 +0x49c")]
    check(all(st["gainramp+8"] == sb[bn]["gainramp ptr"] for bn in ("band1 +0x498", "band2 +0x49c") for st in sb[bn]["stages"])
          and gr[0] != gr[1], "all 5 stages of a band share the band's one GainRamp (+0x10); the two bands have separate ones")
    check(all(v == 0x840ac8 for k, v in vps.items() if k.startswith("param")) and
          all(v == 0x840e40 for k, v in vps.items() if k.endswith("gate +0xc")),
          "parameters are LinearParameter (0x840ac8); each band gate is SignalGate (0x840e40)")
    def thunk(t):                                            # resolve a single `b #target` thunk
        ins = im.disasm(t, t + 4)
        return "%s->%s" % (hex(t), ins[0].op_str[1:]) if ins and ins[0].mnemonic == "b" else hex(t)
    vt_slots = {"IirFilter2 %s (slots 2,4,6,8,9)" % hex(vt): [thunk(im.u32(vt + 4 * s)) for s in (2, 4, 6, 8, 9)] for vt in (0x83bcc0, 0x83bcf0)}
    vt_slots.update({"IirFilter %s (slots 0..4)" % hex(vt): [thunk(im.u32(vt + 4 * s)) for s in range(5)] for vt in (0x840c28, 0x840c48)})
    P("  vtable slots: %s" % vt_slots); res["C3_vt_slots"] = vt_slots
    check(all(v[2].endswith("0xe16dc") for k, v in vt_slots.items() if k.startswith("IirFilter "))
          and all(v[0] == "0xe34d8" and v[3] == "0xe27b8" for k, v in vt_slots.items() if k.startswith("IirFilter2")),
          "IirLpf/Hpf slot 2 = thunk to the shared process 0xe16dc; IirFilter2 slot 2 = 0xe34d8 (-> slot 8 0xe27b8, new kernel)")
    for fn, lo, hi in (("ctor 0x10baec", 0x10baec, 0x10bf00), ("slot 25 0x10ae70", 0x10ae70, 0x10aec8),
                       ("param apply 0x10a4f0", 0x10a4f0, 0x10a7d8), ("band ctor 0x10afd4", 0x10afd4, 0x10b7d4),
                       ("stage ctor 0x10a928", 0x10a928, 0x10ab74), ("band process 0x10c208", 0x10c208, 0x10c970),
                       ("band swap 0x10c070", 0x10c070, 0x10c208), ("ramp setup 0x10abdc", 0x10abdc, 0x10adb8)):
        plt = im.plt(); tg = []
        for ins in im.disasm(lo, hi):
            if ins.mnemonic in ("bl", "b", "blx") and ins.op_str.startswith("#0x"):
                t = int(ins.op_str[1:], 16)
                if not (lo <= t < hi): tg.append(plt.get(t, hex(t)))
        P("  direct callees of %s: %s" % (fn, sorted(set(tg))))
        res.setdefault("C3_callees", {})[fn] = sorted(set(tg))

    # ---------------- C5 state layout ----------------------------------------------------------------------------------
    P(); P("== C5 state layout (emulated 1.60 object) ==")
    xb = EmuPEQ(); xb.process(L1, R1); s_b0 = xb.state()
    for tag, s in (("ctor", s_ctor), ("insert init", s_init), ("block 0", s_b0)):
        bd = {k: v for k, v in s["band1 +0x498"].items() if k not in ("stages", "gate+0xc", "gainramp+0x10")}
        P("  %-11s band1 %s" % (tag, bd))
        P("  %-11s band1 gainramp %s" % ("", s["band1 +0x498"]["gainramp+0x10"]))
        P("  %-11s band1 gate %s" % ("", s["band1 +0x498"]["gate+0xc"]))
    st0 = s_ctor["band1 +0x498"]["stages"]
    P("  ctor LowShelvingFilter: %s" % {k: v for k, v in st0[0]["obj+4"].items()})
    P("  ctor IirLpf2ndOrder:    %s" % st0[3]["obj+0"])
    P("  globals 0xf52f00..0c (static init 0x13aa8) = %s" % s_ctor["globals 0xf52f00..0c"])
    check(s_ctor["globals 0xf52f00..0c"] == [M.M_F, M.M_FI, M.M_Q, M.M_QI],
          "step multipliers 0xf52f00/04/08/0c = powf(10, 0.012f), 1/., powf(10, 0.02f), 1/. (model constants)")
    res["C5_state_ctor"] = s_ctor; res["C5_state_init"] = s_init; res["C5_state_block0"] = s_b0
    mm = M.PEQ(); mm.insert_defaults(); mm.process(L1, R1)
    pairs = []
    for bi, bn in enumerate(("band1 +0x498", "band2 +0x49c")):
        e_, m_ = s_b0[bn], mm.bands[bi]
        st = e_["stages"][e_["cur+0x18"]]; ms = m_.st[m_.cur]
        ef = st["obj+4"] or st["obj+0"]
        pairs += [("%s %s" % (bn[:5], k), e_[k], v) for k, v in (
            ("pending+0x14", m_.pending), ("cur+0x18", m_.cur), ("f_t+0x1c", m_.ft), ("f_c+0x20", m_.fc), ("f_mult+0x24", m_.fmult),
            ("f_steps+0x2c", m_.fsteps), ("q_t+0x30", m_.qt), ("q_c+0x34", m_.qc), ("q_mult+0x38", m_.qmult),
            ("q_steps+0x40", m_.qsteps), ("g_t+0x44", m_.gt), ("g_c+0x48", m_.gc), ("g_step+0x4c", m_.gstep),
            ("g_steps+0x54", m_.gsteps), ("next+0x58", m_.next), ("maxsteps+0x5c", m_.maxsteps))]
        pairs += [("%s gate cur" % bn[:5], e_["gate+0xc"]["cur+0x24"], m_.gate.r.cur),
                  ("%s gain cur" % bn[:5], e_["gainramp+0x10"]["cur+8"], m_.gain.cur),
                  ("%s stage coefs" % bn[:5], ef.get("b0,b1,b2,a1,a2 [+0x8c] (lane L)") or ef.get("b0,b1,b2,a1,a2 +0x28.."),
                   [float(c) for c in (ms.f.b0, ms.f.b1, ms.f.b2, ms.f.a1, ms.f.a2)])]
    bad = [(n, a_, b_) for n, a_, b_ in pairs if (a_ != b_ if isinstance(a_, list) else f32(float(a_)) != f32(float(b_)))]
    check(not bad, "model state after block 0 equals %d emulated fields (both bands)%s" % (len(pairs), "" if not bad else ": %s" % bad))
    res["C5_model_fields_checked"] = len(pairs)

    if not a.quick:
        # ---------------- C4 parameter formulas ---------------------------------------------------------------------
        P(); P("== C4 parameter -> stored value (slot 14 set after a defaults block, one slot-25 block applies it) ==")
        VALS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        def after(sets, blocks=1):
            y = EmuPEQ(); y.process(L1, R1)
            for i_, v_ in sets: y.set_param(i_, v_)
            for _ in range(blocks): y.process(L1, R1)
            return y.state()
        rows = []
        for v in VALS:
            v = f32(v)
            for base, bn in ((0, "band1 +0x498"), (3, "band2 +0x49c")):
                st = after([(base, v)]); rows.append(("B%dFREQUENCY" % (base // 3 + 1), v, "f_t+0x1c (Hz)", st[bn]["f_t+0x1c"], M.PEQ.freq_hz(v)))
                st = after([(base + 1, v)]); rows.append(("B%dGAIN" % (base // 3 + 1), v, "g_t+0x44 (dB)", st[bn]["g_t+0x44"], M.PEQ.gain_db(v)))
                st = after([(base + 2, v)]); rows.append(("B%dQ" % (base // 3 + 1), v, "q_t+0x30", st[bn]["q_t+0x30"], M.PEQ.q_of(v)))
        for t in (0.0, 1.0, 2.0, 3.0, 4.0, 2.7, -0.5):
            for idx, bn in ((6, "band1 +0x498"), (7, "band2 +0x49c")):
                st = after([(idx, t)], blocks=4)
                k = int(t)
                rows.append(("BAND%dTYPE" % (idx - 5), t, "pending+0x14", st[bn]["pending+0x14"], k))
                rows.append(("BAND%dTYPE" % (idx - 5), t, "cur+0x18 (4 blk)", st[bn]["cur+0x18"], k))
        nbad = 0; nbit = 0; c4 = {}
        for name, v, fld, got, exp in rows:
            if isinstance(exp, int): ok = got == exp
            else: ok = f2u(f32(got)) == f2u(f32(exp))
            nbit += ok; nbad += not ok
            c4.setdefault(name, []).append({"v": v, "field": fld, "emu": got, "formula": float(exp), "ok": ok})
        for name in c4:
            P("  %-12s %s" % (name, "; ".join("%s=%.9g%s" % (r["v"], r["emu"], "" if r["ok"] else " (formula %.9g) MISMATCH" % r["formula"])
                                              for r in c4[name])))
        check(nbad == 0, "all %d readbacks equal the closed-form formula bit-exactly (freq = powf(1000, v)*20 with the fdlibm "
              "powf; gain dB = 45v - 30; Q = 0.1 + 9.9v; type = (int)v)" % len(rows))
        res["C4_rows"] = c4; res["C4_exact"] = [nbit, len(rows)]
        # stage coefficients after the glide settles vs closed-form formulas (from the targets), all kinds, both bands
        P("  stage coefficients after the glide settles (closed form from the targets):")
        combos = [(0, 0.3, 0.9, 0.4), (0, 0.0, 0.0, 0.0), (1, 0.6, 0.2, 0.15), (1, 1.0, 1.0, 1.0), (2, 0.5, 0.85, 0.7),
                  (2, 0.2, 0.1, 1.0), (3, 0.45, 0.75, 0.6), (3, 1.0, 0.0, 0.0), (4, 0.25, 0.6, 0.3), (4, 0.0, 1.0, 1.0)]
        cbad = 0; cq = []
        for bi, (t, fv, gv, qv) in enumerate(combos):
            band = bi % 2; base = 3 * band; bn = ("band1 +0x498", "band2 +0x49c")[band]
            y = EmuPEQ(); y.process(L1, R1)
            for i_, v_ in ((6 + band, float(t)), (base, fv), (base + 1, gv), (base + 2, qv)): y.set_param(i_, v_)
            for _ in range(200):
                y.process(L1, R1)
                bs = y.state()[bn]
                if bs["maxsteps+0x5c"] == 0 or (bs["f_steps+0x2c"] == 0 and bs["q_steps+0x40"] == 0 and bs["g_steps+0x54"] == 0): break
            for _ in range(2): y.process(L1, R1)
            bs = y.state()[bn]; st = bs["stages"][bs["cur+0x18"]]
            ft, qt, gt = bs["f_t+0x1c"], bs["q_t+0x30"], bs["g_t+0x44"]
            settled = bs["f_c+0x20"] == ft and bs["q_c+0x34"] == qt and bs["g_c+0x48"] == gt and bs["cur+0x18"] == t
            gain = bs["gainramp+0x10"]["target+4"]
            if t in (0, 1, 2):
                f2 = st["obj+4"]; got = f2["b0,b1,b2,a1,a2 [+0x8c] (lane L)"]
                g_used = gt if t != 1 else -gt
                exp = cf_shelf(ft, float(qt), float(g_used)) if t < 2 else cf_peak(ft, float(qt), float(g_used))
                exp_gain = 1.0 if t != 1 else M.gain_lin(gt)
                extra = (f2["fc+8"] == ft and f2["Q+0x18"] == float(qt) and f2["gdb+0x58"] == float(g_used) and
                         f2["p+0x38"] == math.pow(10.0, float(g_used) / 20.0) - 1.0 and f2["lanes equal"])
            else:
                bq = st["obj+0"]; got = bq["b0,b1,b2,a1,a2 +0x28.."]
                b_ = LM.Biquad("lpf" if t == 3 else "hpf", FS); b_.fc = min(max(ft, 5.0), 22050.0); b_.Q = float(qt); b_.coefs()
                exp = [float(c) for c in (b_.b0, b_.b1, b_.b2, b_.a1, b_.a2)]
                exp_gain = M.gain_lin(gt); extra = bq["fc+0xc"] == f32(min(max(ft, 5.0), 22050.0)) and bq["Q+0x40"] == float(qt)
            ok = settled and got == exp and gain == exp_gain and extra
            cbad += not ok
            cq.append({"band": band + 1, "type": t, "freq_v": fv, "gain_v": gv, "q_v": qv, "f_t": ft, "q_t": qt, "g_t": gt,
                       "coefs_emu": got, "coefs_formula": exp, "out_gain": gain, "ok": ok})
            P("   band %d type %d (%s) f %.6g Hz Q %.6g g %+.4g dB: b/a %s out gain %.7g %s" %
              (band + 1, t, M.TYPE_NAMES[t], ft, qt, gt, ["%.7g" % c for c in got], gain, "== formula" if ok else "!= formula"))
        check(cbad == 0, "after settling, every stage kind's coefficients, stored fc/Q/gain/p and the band output gain equal the "
              "closed-form formulas bit-exactly (%d combos, both bands, v = 0 and 1 included)" % len(combos))
        res["C4_coefs"] = cq
        # libm powf / log10f: real 1.60 libm (emulated PLT call) vs fdlibm re-implementation vs host-rounded
        e = EmuPEQ().e; g = random.Random(7)
        pv = [(1000.0, f32(k / 1000)) for k in range(1001)] + [(1000.0, f32(g.random())) for _ in range(2000)] + \
             [(10.0, f32(0.012)), (10.0, f32(0.02))] + [(10.0, f32(g.uniform(-2, 2))) for _ in range(500)] + \
             [(f32(g.uniform(0.01, 100)), f32(g.uniform(-3, 3))) for _ in range(1000)]
        ep = [u2f(e.call(PLT_POWF, f2u(x_), f2u(y_))[0]) for x_, y_ in pv]
        m_fd = sum(f2u(r) == f2u(FL.powf(x_, y_)) for r, (x_, y_) in zip(ep, pv))
        m_fix = sum(f2u(r) == f2u(FL.powf(x_, y_, 0x00400000)) for r, (x_, y_) in zip(ep, pv))
        m_host = sum(f2u(r) == f2u(f32(math.pow(x_, y_))) for r, (x_, y_) in zip(ep, pv))
        lv = [f32(g.uniform(0.001, 1000)) for _ in range(2000)] + [f32(math.exp(g.uniform(-8, 8))) for _ in range(1000)] + \
             [M.M_F, M.M_Q]
        el = [u2f(e.call(PLT_LOG10F, f2u(x_))[0]) for x_ in lv]
        l_fd = sum(f2u(r) == f2u(FL.log10f(x_)) for r, x_ in zip(el, lv)); l_host = sum(f2u(r) == f2u(LM.log10f(x_)) for r, x_ in zip(el, lv))
        P("  libm powf (PLT 0x%x) vs fdlibm model: %d/%d bit-exact; with the 'corrected' t_h constant: %d/%d; host-rounded pow: %d/%d" %
          (PLT_POWF, m_fd, len(pv), m_fix, len(pv), m_host, len(pv)))
        P("  libm log10f (PLT 0x%x) vs fdlibm model: %d/%d bit-exact; host-rounded log10: %d/%d" % (PLT_LOG10F, l_fd, len(lv), l_host, len(lv)))
        check(m_fd == len(pv) and l_fd == len(lv) and m_host < len(pv) and l_host < len(lv),
              "1.60 libm powf/log10f = fdlibm single-precision algorithm (bit-exact); host-rounded double results differ")
        res["C4_libm"] = {"powf_fdlibm": [m_fd, len(pv)], "powf_fixed_th": [m_fix, len(pv)], "powf_host": [m_host, len(pv)],
                          "log10f_fdlibm": [l_fd, len(lv)], "log10f_host": [l_host, len(lv)]}
        # step counts and gated-jump thresholds (freq > 38, Q > 70, gain > 250 steps)
        P("  glide step counts and gated jumps (one parameter changed after a defaults block):")
        jt = []
        for idx, v, desc in ((0, 0.566 + 0.14, "freq +0.14 (36 steps)"), (0, 0.566 + 0.16, "freq +0.16 (41 steps)"),
                             (1, 2 / 3 + 0.2, "gain +9 dB (226 steps)"), (1, 2 / 3 + 0.25, "gain +11.25 dB (282 steps)"),
                             (2, 1.0, "Q 0.7 -> 10 (58 steps)"), (2, 0.0, "Q 0.7 -> 0.1 (43 steps)")):
            y = EmuPEQ(); mm = M.PEQ(); mm.insert_defaults()
            for o_ in (y, mm): o_.process(L1, R1); o_.set_param(idx, v); o_.process(L1, R1)
            bs = y.state()["band1 +0x498"]; b_ = mm.bands[0]
            gated = bs["gate+0xc"]["state+0x20"] == 1 and bs["gate+0xc"]["target+0x28"] == 0.0
            steps = (bs["f_steps+0x2c"], bs["q_steps+0x40"], bs["g_steps+0x54"])
            jt.append({"change": desc, "steps after 1 block (f, q, g)": steps, "gate closing": gated,
                       "model same": steps == (b_.fsteps, b_.qsteps, b_.gsteps) and gated == (b_.gate.r.state == 1 and b_.gate.r.target == 0.0)})
            P("   %-28s steps left after the block (f, q, g) %s, gate fading out: %s, model agrees: %s" % (desc, steps, gated, jt[-1]["model same"]))
        check([j["gate closing"] for j in jt] == [False, True, False, True, False, False] and all(j["model same"] for j in jt),
              "gated jump only when freq steps > 38 or gain steps > 250 (Q steps <= 70 for any Q in 0.1..10 from 0.7); model agrees")
        res["C4_jumps"] = jt

    # ---------------- C6 model vs emulation --------------------------------------------------------------------------
    P(); P("== C6 model vs emulation (slot 25 direct, %d blocks x %d, stereo) ==" % (NBLK, N))
    cases = C6_CASES[:1] if a.quick else C6_CASES
    c6 = {}; allexact = True; types_seen = set()
    for name, pr, setp, ev in cases:
        for sig in C6_SIGNALS:
            L, R, out = run_both(sig, setp, ev, prime=pr)
            c = compare(out["emu"][:2], out["model"][:2])
            c["emu_sha"] = sha(pack(*out["emu"][:2]))[:16]
            c["rms_in"] = rms(L + R); c["rms_out"] = rms(out["emu"][0] + out["emu"][1])
            st = out["emu"][2].state(); types_seen.add(("b1", st["band1 +0x498"]["cur+0x18"])); types_seen.add(("b2", st["band2 +0x49c"]["cur+0x18"]))
            c6["%s/%s" % (name, sig)] = c
            ex = c["bit_exact"] == c["n"]; allexact &= ex
            P("  %-24s %-10s bit-exact %4d/%d  max|err| %.3g  first diff %s  rms in/out %.4f/%.4f  sha %s" %
              (name, sig, c["bit_exact"], c["n"], c["max_abs_err"], c["first_diff_index"], c["rms_in"], c["rms_out"], c["emu_sha"]))
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, sig)), "wb") as fh: fh.write(pack(*out["emu"][:2]))
    res["C6"] = c6
    check(allexact, "model output is bit-exact to emulated 1.60 slot 25 in all %d C6 runs" % len(c6))
    P("  final (band, type) reached across cases: %s" % sorted(types_seen))
    if not a.quick:
        check(all(("b%d" % b, t) in types_seen for b in (1, 2) for t in range(5)), "every stage type 0..4 ran in both bands")

    if not a.quick:
        # ---------------- C7 alternatives ---------------------------------------------------------------------------
        P(); P("== C7 alternative explanations ==")
        # (a) RBJ cookbook shelf / peaking vs the 1.60 form
        rb = []
        for kind, fc, Q, g in (("peak", 1000.0, 0.7, 9.0), ("peak", 1000.0, 0.7, -12.0), ("peak", 4000.0, 3.0, 6.0),
                               ("shelf", 200.0, 0.7, 9.0), ("shelf", 200.0, 0.7, -12.0)):
            y = EmuPEQ(); y.process(L1, R1)
            t = 2.0 if kind == "peak" else 0.0
            fv = math.log10(fc / 20.0) / 3.0; gv = (g + 30.0) / 45.0; qv = (Q - 0.1) / 9.9
            for i_, v_ in ((6, t), (0, fv), (1, gv), (2, qv)): y.set_param(i_, v_)
            for _ in range(200):
                y.process(L1, R1); bs = y.state()["band1 +0x498"]
                if bs["f_steps+0x2c"] == 0 and bs["q_steps+0x40"] == 0 and bs["g_steps+0x54"] == 0 and bs["cur+0x18"] == int(t): break
            bs = y.state()["band1 +0x498"]; got = bs["stages"][int(t)]["obj+4"]["b0,b1,b2,a1,a2 [+0x8c] (lane L)"]
            ft, qt, gt = bs["f_t+0x1c"], float(bs["q_t+0x30"]), float(bs["g_t+0x44"])
            ours = cf_peak(ft, qt, gt) if kind == "peak" else cf_shelf(ft, qt, gt)
            rbj = cf_rbj(kind, ft, qt, gt)
            w0 = 2 * math.pi * ft / FS; zc = complex(math.cos(w0), math.sin(w0))
            rb.append({"kind": kind, "fc": ft, "Q": qt, "gain_dB": gt, "emu==ours": got == ours, "emu==rbj": got == rbj,
                       "max|emu-rbj|": max(abs(p - q) for p, q in zip(got, rbj)),
                       "gain_dB_at_fc_emu": 20 * math.log10(H_at(got, zc)), "gain_dB_at_DC_emu": 20 * math.log10(H_at(got, 1)),
                       "gain_dB_at_Nyq_emu": 20 * math.log10(H_at(got, -1))})
            P("  (a) %-5s fc %.1f Q %.3g %+.2f dB: emu == 1.60 form %s, == RBJ cookbook %s (max|diff| %.3g); |H| at fc / DC / Nyquist "
              "%.2f / %.2f / %.2f dB" % (kind, ft, qt, gt, got == ours, got == rbj, rb[-1]["max|emu-rbj|"], rb[-1]["gain_dB_at_fc_emu"],
                                        rb[-1]["gain_dB_at_DC_emu"], rb[-1]["gain_dB_at_Nyq_emu"]))
        check(all(r["emu==ours"] and not r["emu==rbj"] for r in rb),
              "shelf/peaking coefficients follow the 1.60 (Zolzer-style, single boost form) formulas, not the RBJ cookbook")
        res["C7a"] = rb
        # (b) correctly rounded powf instead of fdlibm powf: model variant output vs emulation
        orig = FL.powf
        setp = [(6, 2.0), (0, 0.474), (1, 42.0 / 45.0), (2, 0.7)]   # type switch -> jump to the target
        _, _, o1 = run_both("noise", setp, prime=2)
        FL.powf = lambda x_, y_, th=None: f32(math.pow(f32(x_), f32(y_)))
        try:
            _, _, o2 = run_both("noise", setp, prime=2, model_only=True)
        finally:
            FL.powf = orig
        c_t = compare(o1["emu"][:2], o1["model"][:2]); c_a = compare(o1["emu"][:2], o2["model"][:2])
        P("  (b) B1 peaking (Q 7.03, +12 dB) at freq v 0.474: fdlibm powf model %d/%d bit-exact; host-rounded powf variant %d/%d (max|err| %.3g); "
          "stored f_t emu %r, fdlibm %r, host %r" % (c_t["bit_exact"], c_t["n"], c_a["bit_exact"], c_a["n"], c_a["max_abs_err"],
                                                    o1["emu"][2].state()["band1 +0x498"]["f_t+0x1c"], M.PEQ.freq_hz(0.474),
                                                    f32(f32(math.pow(1000.0, f32(0.474))) * 20.0)))
        check(c_t["bit_exact"] == c_t["n"] and c_a["bit_exact"] < c_a["n"], "fdlibm powf needed: a correctly rounded powf changes the "
              "output (frequency 1 ulp off)")
        res["C7b"] = {"fdlibm": c_t, "host": c_a}
        # (c) bands in parallel (sum of two band outputs) instead of in series
        class PEQPar(M.PEQ):
            def process(s, L, R):
                L = [LM.F(v) for v in L]; R = [LM.F(v) for v in R]; n = len(L); s.apply_params()
                L2, R2 = list(L), list(R)
                s.bands[0].process(L, R, n); s.bands[1].process(L2, R2, n)
                return [LM.F(p + q - r) for p, q, r in zip(L, L2, [LM.F(v) for v in L])], [LM.F(p + q - r) for p, q, r in zip(R, R2, R)]
        setp = [(6, 2.0), (0, 0.3), (1, 0.9), (7, 2.0), (3, 0.7), (4, 0.2)]
        _, _, o1 = run_both("noise", setp, prime=2)
        _, _, o2 = run_both("noise", setp, prime=2, model_cls=PEQPar, model_only=True)
        c_t = compare(o1["emu"][:2], o1["model"][:2]); c_a = compare(o1["emu"][:2], o2["model"][:2])
        P("  (c) two peaking bands: series model %d/%d bit-exact; parallel variant %d/%d (max|err| %.3g)" %
          (c_t["bit_exact"], c_t["n"], c_a["bit_exact"], c_a["n"], c_a["max_abs_err"]))
        check(c_t["bit_exact"] == c_t["n"] and c_a["bit_exact"] < c_t["n"] // 4, "bands are in series (band 1 output feeds band 2)")
        res["C7c"] = {"series": c_t, "parallel": c_a}
        # (d) LPF/HPF (types 3/4) gain: separate GainRamp after the filter, not 1 (and not inside the filter)
        F0 = LM.F(0.0)
        class PEQNoGain(M.PEQ):
            def __init__(s, *aa, **kk):
                M.PEQ.__init__(s, *aa, **kk)
                for b in s.bands:
                    for st in b.st:
                        if st.kind in (3, 4):
                            st.configure = (lambda st_: (lambda fc, qc, gc, flag, swap=False:
                                                         M.Stage.configure(st_, fc, qc, F0, flag, swap)))(st)
        setp = [(6, 3.0), (0, 0.6), (1, 0.85), (2, 0.4)]
        _, _, o1 = run_both("noise", setp, prime=2)
        _, _, o2 = run_both("noise", setp, prime=2, model_cls=PEQNoGain, model_only=True)
        c_t = compare(o1["emu"][:2], o1["model"][:2]); c_a = compare(o1["emu"][:2], o2["model"][:2])
        r_out = rms(o1["emu"][0][8 * N:] + o1["emu"][1][8 * N:]); r_ng = rms(o2["model"][0][8 * N:] + o2["model"][1][8 * N:])
        P("  (d) LPF + B1GAIN 0.85 (+8.25 dB): model %d/%d bit-exact; variant without the GainRamp gain %d/%d; rms ratio emu/variant "
          "(blocks 8..15) %.4f = %+.3f dB" % (c_t["bit_exact"], c_t["n"], c_a["bit_exact"], c_a["n"], r_out / r_ng, 20 * math.log10(r_out / r_ng)))
        check(c_t["bit_exact"] == c_t["n"] and c_a["bit_exact"] < c_t["n"] // 4 and abs(20 * math.log10(r_out / r_ng) - 8.25) < 0.01,
              "types 3/4 apply BxGAIN as a separate output gain (GainRamp) of exactly 10^(gain/20)")
        res["C7d"] = {"model": c_t, "no_gain": c_a, "rms_ratio_dB": 20 * math.log10(r_out / r_ng)}
        # (e) type 1 = high shelf: low shelf with -gain, output gain +gain -> DC 0 dB, Nyquist +gain
        hs = []
        for gv in (0.2, 0.9):
            y = EmuPEQ(); y.process(L1, R1)
            for i_, v_ in ((6, 1.0), (0, 0.5), (1, gv), (2, 6 / 99)): y.set_param(i_, v_)
            for _ in range(200):
                y.process(L1, R1); bs = y.state()["band1 +0x498"]
                if bs["g_steps+0x54"] == 0 and bs["f_steps+0x2c"] == 0 and bs["cur+0x18"] == 1: break
            bs = y.state()["band1 +0x498"]; c_ = bs["stages"][1]["obj+4"]["b0,b1,b2,a1,a2 [+0x8c] (lane L)"]
            og = bs["gainramp+0x10"]["cur+8"]
            dc = 20 * math.log10(H_at(c_, 1) * og); ny = 20 * math.log10(H_at(c_, -1) * og)
            hs.append({"gain_dB": bs["g_t+0x44"], "DC_dB": dc, "Nyquist_dB": ny})
            P("  (e) BAND1TYPE 1, gain %+.2f dB: total |H| (shelf x output gain %.5g) at DC %.4f dB, at Nyquist %.4f dB" %
              (bs["g_t+0x44"], og, dc, ny))
        check(all(abs(h["DC_dB"]) < 1e-3 and abs(h["Nyquist_dB"] - h["gain_dB"]) < 1e-3 for h in hs),
              "type 1 is a high shelf (0 dB at DC, +gain at Nyquist), built as low shelf(-gain) x output gain(+gain)")
        res["C7e"] = hs
        # (f) first block after a closed gate is not filtered: output = input * (n/132)^2 (two band gates in series)
        L, R, out = run_both("noise", [(6, 3.0), (0, 0.1), (7, 3.0), (3, 0.1)], nblk=3, emu_only=True, prime=0)
        oL = out["emu"][0]
        g_ = [LM.F(0.0)]
        for k in range(1, N): g_.append(LM.F(g_[-1] + LM.F(LM.F(1.0) / LM.F(132.0))))
        exp0 = [LM.F(LM.F(L[k] * g_[k]) * g_[k]) for k in range(N)]
        same = sum(f2u(f32(p)) == f2u(f32(q)) for p, q in zip(oL[:N], exp0)); err0 = max(abs(p - q) for p, q in zip(oL[:N], exp0))
        P("  (f) cold, both bands LPF at 39.9 Hz set before block 0: block 0 output == input x g1(n) x g2(n), g = 0, 1/132, ...: "
          "%d/%d samples (max|diff| %.3g); block 1 rms out/in %.4f (filtered)" %
          (same, N, err0, rms(oL[N:2 * N]) / rms(L[N:2 * N])))
        check(err0 < 1e-6 and rms(oL[N:2 * N]) / rms(L[N:2 * N]) < 0.2, "block 0 (gates closed) passes the input unfiltered, "
              "only gated; filtering starts at block 1")
        res["C7f"] = {"match": same, "max_err": err0}
        # (g) BANDxTYPE 5 (ctor 'last' value): no stage object -> null-pointer read in 0x10c208
        y = EmuPEQ(); y.process(L1, R1); y.set_param(6, 5.0); msg = None
        try:
            for _ in range(4): y.process(L1, R1)
        except (EmuAbort, Exception) as ex:          # noqa: BLE001
            msg = "%s: %s" % (type(ex).__name__, str(ex).splitlines()[0][:160])
        P("  (g) BAND1TYPE 5 set after one block: emulation -> %s" % msg)
        check(msg is not None, "BANDxTYPE 5 is not a valid running state: the band has 5 stages (0..4) and 0x10c208 dereferences a "
              "null stage once the swap selects index 5")
        res["C7g"] = msg
        # (h) cold, nothing set: per-block rms gain on the 1 kHz sine (start-up)
        L, R, out = run_both("sine1k", nblk=4)
        gb = [round(rms(out["emu"][0][b * N:(b + 1) * N]) / rms(L[b * N:(b + 1) * N]), 4) for b in range(4)]
        P("  (h) cold defaults, 1 kHz sine, per-block rms gain: %s (two closed 132-sample gates, then 0 dB shelves)" % gb)
        res["C7h_startup_gain"] = gb

    P(); P("RESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h026_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(res, open(os.path.join(a.out, "h026.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
