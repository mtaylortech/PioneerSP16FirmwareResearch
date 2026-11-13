#!/usr/bin/env python3
"""H023 — MultiModeFilter (Insert index 3) algorithm reconstruction: 1.60 emulation (ctor 0x109e8c, slot 25 0x108ee4 called
directly) vs. the own-code Python model harness/models/mmf.py.

Sections (criteria of kb/cycles/006.md):
  C1  parameters: registration calls 0xf1850 / 0xf1a00 logged during the real ctor (name, id, min, max, default), ctor and
      Insert-default values, slot-14 index -> parameter object map.
  C3  shared blocks: vptrs of every sub-object of an emulated MMF (parameters, gate, sub-filter biquads), direct callees of the
      ctor and slot 25 (capstone).
  C4  parameter formulas: set each parameter through EffectBase slot 14 0x105d24 at 7 values after one defaults block (F026),
      run one slot-25 block, read the stored coefficient(s), compare with the closed-form formula; FILTERTYPE x FILTERDB kinds;
      biquad coefficients per kind after the ramp settles (model vs. emulation).
  C5  state layout dump (emulated object after ctor / insert init / block 0).
  C6  model vs. emulation matrix: impulse, late impulse, 1 kHz sine, white noise (seed 1234), 16 x 64 stereo, settings covering
      kinds 0..6, intermediate CUTOFF/Q/GAIN/GLIDE and mid-run changes; per-case bit-exact count and max |error|.
  C7  alternatives: 24 dB = cascade with Q' = sqrt(Q) vs. same Q; cutoff change glided vs. immediate; GAIN after vs. before the
      filter; FILTERDB 0 vs 2; NONE (index 4) has no effect.
Outputs only to --out (default harness/out/H023/). Run: .venv/bin/python -B harness/H023_mmf_model.py --out DIR
"""
import argparse, hashlib, json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import random                                                 # noqa: E402
from emu import Emu, f2u, u2f, init_array, SP                 # noqa: E402
import H007_effect_emu as H7                                  # noqa: E402
import sp16img                                                # noqa: E402
import mmf as M                                               # noqa: E402
import lofi as LM                                             # noqa: E402

N = 64
FS = 44100
NBLK = 16
FX = dict(ctor=0x109e8c, size=0x4a0, vtable=0x8420b8, ctor_args=(44100, 64), insert_index=3, static_init=[0x13a28],
          params=[("CUTOFF", 0x1b8), ("GAIN", 0x214), ("Q", 0x270), ("GLIDE", 0x2cc), ("NONE", 0x328), ("MIXRATIO", 0x384),
                  ("FILTERTYPE", 0x3e0), ("FILTERDB", 0x43c)])
PARAM_OFF = dict((k, off) for k, (_, off) in enumerate(FX["params"]))     # slot-14 index -> object offset (checked in C1)
REG_FUNCS = {0xf1850: "LinearParameter float ctor 0xf1850", 0xf1a00: "LinearParameter choice ctor 0xf1a00"}
VT_NAMES = {0x840ac8: "LinearParameter", 0x840e40: "SignalGate", 0x840c28: "IirLpf2ndOrder", 0x840c48: "IirHpf2ndOrder",
            0x841918: "IirBpf2ndOrder", 0x841938: "IirOff", 0x8420b8: "MultiModeFilter"}


def sha(b): return hashlib.sha256(b).hexdigest()
def f32(x): return u2f(f2u(x))


# ------------------------------------------------------------------------------------------------------------------------
class EmuMMF:
    """1.60 MultiModeFilter built by its ctor + Insert init (H007 sequence), processed by calling slot 25 directly."""
    def __init__(self, defaults=True, log_regs=False):
        self.fx = FX; self.e = e = Emu(); self.init_log = []; self.regs = []
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
        self.obj = self.o = e.malloc(FX["size"], "new (harness: MMF object)")
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

    def biquad(self, s):
        f, u = self.f, self.u
        return {"vptr": hex(u(s)), "nyq+4": f(s + 4), "fs+8": self.i(s + 8), "fc+0xc": f(s + 0xc), "Q+0x40": self.d(s + 0x40),
                "b0,b1,b2,a1,a2 +0x28..": [f(s + 0x28 + 4 * j) for j in range(5)], "k+0x24": f(s + 0x24), "flag+0x48": self.b(s + 0x48)}

    def gate(self, g):
        f, i = self.f, self.i
        return {"vptr": hex(self.u(g)), "state+0x20": i(g + 0x20), "cur+0x24": f(g + 0x24), "target+0x28": f(g + 0x28),
                "inc+0x2c": f(g + 0x2c), "rem+0x30": i(g + 0x30), "N+0x38": i(g + 0x38), "off+0x40": f(g + 0x40), "on+0x44": f(g + 0x44)}

    def state(self):
        o = self.o; u, i, f = self.u, self.i, self.f
        C, G = u(o + 0x498), u(o + 0x49c)
        wr = []
        for k in range(u(C + 8)):
            w = u(u(C) + 4 * k)
            st = [self.biquad(u(w + 4 + 4 * j)) for j in range(2) if u(w + 4 + 4 * j)]
            wr.append({"kind+0": i(w), "stages": st})
        return {
            "EffectBase dry+0x10 / wet+0x14": [f(o + 0x10), f(o + 0x14)],
            "filter +0x498": {"count+8": u(C + 8), "cap+4": u(C + 4), "pending+0x10": i(C + 0x10), "cur+0x14": i(C + 0x14),
                              "cut_t+0x18": f(C + 0x18), "cut_c+0x1c": f(C + 0x1c), "cut_mult+0x20": f(C + 0x20),
                              "cut_steps+0x24": i(C + 0x24), "q_t+0x28": f(C + 0x28), "q_c+0x2c": f(C + 0x2c),
                              "q_mult+0x30": f(C + 0x30), "q_steps+0x34": i(C + 0x34), "next+0x38": f(C + 0x38),
                              "maxsteps+0x3c": i(C + 0x3c), "flag+0x40": self.b(C + 0x40), "dirty+0x41": self.b(C + 0x41),
                              "glide+0x42": self.b(C + 0x42), "glide_steps+0x44": f(C + 0x44), "up+0x48": f(C + 0x48),
                              "down+0x4c": f(C + 0x4c), "gate+0xc": self.gate(u(C + 0xc)), "wrappers": wr},
            "gain +0x49c": {"inc+0": f(G), "target+4": f(G + 4), "cur+8": f(G + 8), "rem+0xc": i(G + 0xc), "N+0x10": i(G + 0x10),
                            "invN+0x14": f(G + 0x14), "delay+0x18": i(G + 0x18), "idle+0x1c": self.b(G + 0x1c), "state+0x20": i(G + 0x20)},
            "params (last, cur)": {M.PARAM_NAMES[k]: ([f(o + off + 0x24), f(o + off + 0x28)] if k < 6 else
                                                      [i(o + off + 0x40), i(o + off + 0x44)]) for k, off in PARAM_OFF.items()},
            "globals 0xf52ef4/8": [f(0xf52ef4), f(0xf52ef8)],
        }


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
    if which == "emu": return EmuMMF()
    m = (model_cls or M.MMF)(); m.insert_defaults(); return m


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


# index: 0 CUTOFF 1 GAIN 2 Q 3 GLIDE 4 NONE 5 MIXRATIO 6 FILTERTYPE 7 FILTERDB
C6_CASES = [
    ("cold_defaults", 0, [], []),                                                        # kind 0 LPF12, 997.8 Hz, Q 0.7
    ("lpf12_q_gain", 3, [(6, 0.0), (7, 1.0), (0, 0.4), (2, 0.6), (1, 0.5)], []),
    ("hpf12", 3, [(6, 1.0), (7, 1.0), (0, 0.5), (2, 0.3), (1, 0.8)], []),
    ("bpf12", 3, [(6, 2.0), (7, 1.0), (0, 0.55), (2, 0.2)], []),
    ("lpf24_db0", 3, [(6, 0.0), (7, 0.0), (0, 0.45), (2, 0.7), (1, 0.6)], []),
    ("hpf24_db2", 3, [(6, 1.0), (7, 2.0), (0, 0.35), (2, 0.4)], []),
    ("bpf24", 3, [(6, 2.0), (7, 0.0), (0, 0.6), (2, 0.9), (1, 0.3)], []),
    ("off_type3_gain", 3, [(6, 3.0), (7, 1.0), (1, 0.9)], []),
    ("extreme_bpf24", 3, [(6, 2.0), (7, 0.0), (0, 1.0), (2, 1.0), (1, 1.0)], [(8, 0, 0.0), (8, 2, 0.0), (12, 1, 0.0)]),
    ("seq_glide", 3, [(6, 0.0), (7, 1.0), (3, 0.5)],
     [(2, 0, 0.3), (6, 0, 0.8), (9, 2, 0.8), (11, 3, 0.0), (12, 0, 0.2), (14, 0, 0.25)]),
    ("seq_type_switch", 3, [(6, 0.0), (7, 1.0), (3, 0.2), (0, 0.5)],
     [(2, 6, 1.0), (4, 7, 0.0), (5, 0, 0.7), (7, 6, 2.0), (9, 1, 0.9), (10, 6, 3.0), (12, 6, 0.0), (13, 1, 0.4)]),
    ("seq_cut_jump_glide0", 3, [(6, 1.0), (7, 0.0), (0, 0.5)],
     [(3, 0, 0.53), (6, 0, 0.9), (8, 2, 0.95), (10, 0, 0.1), (12, 7, 1.0), (13, 0, 0.12)]),
]
C6_SIGNALS = ["impulse", "impulse_b4", "sine1k", "noise"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H023"))
    ap.add_argument("--quick", action="store_true", help="only the cold defaults case (debug)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()

    # ---------------- C1 parameters ----------------------------------------------------------------------------------
    P("== C1 parameters (registration calls during the real 1.60 ctor 0x109e8c) ==")
    x = EmuMMF(defaults=False, log_regs=True)
    check(x.vptr == FX["vtable"], "vptr after ctor = 0x%x (MultiModeFilter)" % x.vptr)
    regs = []
    for r in x.regs:
        nm = im.cstr(r["name_ptr"]); off = r["obj_off"] - x.o
        fl = r["func"].startswith("LinearParameter float")
        rng = (u2f(r["r3"]), u2f(r["stack"][0]), u2f(r["stack"][1])) if fl else (r["r3"], r["stack"][0], r["stack"][1])
        unit = im.cstr(r["stack"][2])
        regs.append({"name": nm, "id": r["id"], "obj_off": hex(off), "kind": "float" if fl else "choice", "min,max,default": rng,
                     "unit_str": unit})
        P("  id %d %-10s at obj+0x%x  %-6s min %s max %s default %s  (unit/label string %r)" %
          (r["id"], nm, off, "float" if fl else "choice", rng[0], rng[1], rng[2], unit))
    res["C1_registrations"] = regs
    check([r["name"] for r in regs] == M.PARAM_NAMES and [r["id"] for r in regs] == list(range(8)) and
          [int(r["obj_off"], 16) for r in regs] == [off for _, off in FX["params"]],
          "8 parameters registered, ids 0..7 in obj order +0x1b8 + 0x5c*k: %s" % [r["name"] for r in regs])
    s_ctor = x.state()
    P("  ctor (last, cur): %s" % s_ctor["params (last, cur)"])
    xi = EmuMMF(); s_init = xi.state()
    P("  after Insert init (slot 52 case 3) (last, cur): %s" % s_init["params (last, cur)"])
    exp_init = {nm: (f32(M.INSERT_DEFAULTS[k]) if k < 6 else int(M.INSERT_DEFAULTS[k])) for k, nm in enumerate(M.PARAM_NAMES)}
    check(all(s_init["params (last, cur)"][nm][1] == exp_init[nm] for nm in M.PARAM_NAMES), "Insert defaults = model INSERT_DEFAULTS")
    check(all(s_ctor["params (last, cur)"][nm][0] == (f32(M.CTOR_VALUES[k]) if k < 6 else M.CTOR_VALUES[k])
              for k, nm in enumerate(M.PARAM_NAMES)), "ctor 'last' values = model CTOR_VALUES %s" % M.CTOR_VALUES)
    res["C1_ctor_params"] = s_ctor["params (last, cur)"]; res["C1_insert_defaults"] = s_init["params (last, cur)"]
    # slot-14 index -> parameter object
    idxmap = {}
    L1, R1 = signal("sine1k", 1)
    for idx in range(9):
        y = EmuMMF(); y.process(L1, R1); before = y.state()["params (last, cur)"]
        rc = y.set_param(idx, 0.123 if idx < 6 else 2.0); after = y.state()["params (last, cur)"]
        ch = [k for k in before if before[k] != after[k]]
        idxmap[idx] = {"ret": rc, "changed": ch}
    P("  slot-14 index -> changed parameter: %s" % {k: (v["changed"], v["ret"]) for k, v in idxmap.items()})
    check(all(idxmap[k]["changed"] == [M.PARAM_NAMES[k]] for k in range(8)) and idxmap[8]["changed"] == [],
          "slot-14 index k sets parameter id k (k = 0..7); index 8 changes nothing")
    res["C1_slot14_map"] = idxmap

    # ---------------- C3 shared blocks --------------------------------------------------------------------------------
    P(); P("== C3 shared blocks: vptrs inside an emulated MMF, callees of ctor / slot 25 ==")
    o = xi.o; vps = {}
    for nm, off in FX["params"]: vps["param %s +0x%x" % (nm, off)] = xi.u(o + off)
    C = xi.u(o + 0x498)
    vps["filter gate [+0x498]+0xc"] = xi.u(xi.u(C + 0xc))
    for k, w in enumerate(s_init["filter +0x498"]["wrappers"]):
        for j, st in enumerate(w["stages"]): vps["wrapper %d (kind %d) stage %d" % (k, w["kind+0"], j)] = int(st["vptr"], 16)
    for k, v in vps.items(): P("  %-34s vptr 0x%x %s" % (k, v, VT_NAMES.get(v, "?")))
    res["C3_vptrs"] = {k: hex(v) for k, v in vps.items()}
    kinds = [w["kind+0"] for w in s_init["filter +0x498"]["wrappers"]]
    st_names = [[VT_NAMES[int(s["vptr"], 16)] for s in w["stages"]] for w in s_init["filter +0x498"]["wrappers"]]
    P("  wrapper kinds %s, stages %s" % (kinds, st_names))
    check(kinds == list(range(7)) and st_names == [["IirLpf2ndOrder"], ["IirHpf2ndOrder"], ["IirBpf2ndOrder"],
                                                   ["IirLpf2ndOrder"] * 2, ["IirHpf2ndOrder"] * 2, ["IirBpf2ndOrder"] * 2, []],
          "7 wrappers: kinds 0..2 = one LPF/HPF/BPF biquad, 3..5 = two of the same, 6 = none")
    check(all(v == 0x840ac8 for k, v in vps.items() if k.startswith("param")) and vps["filter gate [+0x498]+0xc"] == 0x840e40,
          "parameters are LinearParameter (0x840ac8), filter gate is SignalGate (0x840e40)")
    for fn, lo, hi in (("ctor 0x109e8c", 0x109e8c, 0x10a1d8), ("slot 25 0x108ee4", 0x108ee4, 0x108f44),
                       ("container ctor 0x10913c", 0x10913c, 0x109950), ("wrapper ctor 0x1080a0", 0x1080a0, 0x10833c),
                       ("container process 0x108808", 0x108808, 0x108ee4)):
        plt = im.plt(); tg = []
        for ins in im.disasm(lo, hi):
            if ins.mnemonic in ("bl", "b") and ins.op_str.startswith("#0x"):
                t = int(ins.op_str[1:], 16)
                if not (lo <= t < hi): tg.append(plt.get(t, hex(t)))
        P("  direct callees of %s: %s" % (fn, sorted(set(tg))))
        res.setdefault("C3_callees", {})[fn] = sorted(set(tg))

    # ---------------- C5 state layout ----------------------------------------------------------------------------------
    P(); P("== C5 state layout (emulated 1.60 object) ==")
    xb = EmuMMF(); L1, R1 = signal("sine1k", 1); xb.process(L1, R1); s_b0 = xb.state()
    for tag, s in (("ctor", s_ctor), ("insert init", s_init), ("block 0", s_b0)):
        fk = {k: v for k, v in s["filter +0x498"].items() if k not in ("wrappers", "gate+0xc")}
        P("  %-11s filter %s" % (tag, fk)); P("  %-11s gain %s" % ("", s["gain +0x49c"]))
        P("  %-11s filter gate %s" % ("", s["filter +0x498"]["gate+0xc"]))
    P("  globals 0xf52ef4/8 (static init 0x13a28) = %s" % s_ctor["globals 0xf52ef4/8"])
    check(s_ctor["globals 0xf52ef4/8"] == [float(LM.G3), float(LM.G4)], "Q step multipliers 0xf52ef4/8 = 50^(1/100) and inverse "
          "(same values as LoFi's 0xf52ec8/cc)")
    for j, w in enumerate(s_ctor["filter +0x498"]["wrappers"]):
        for st in w["stages"]:
            P("  ctor wrapper %d: nyq %.6g fs %d fc %.6g Q %.17g k %g coefs %s" % (j, st["nyq+4"], st["fs+8"], st["fc+0xc"],
                                                                                st["Q+0x40"], st["k+0x24"], st["b0,b1,b2,a1,a2 +0x28.."]))
            break
    res["C5_state_ctor"] = s_ctor; res["C5_state_init"] = s_init; res["C5_state_block0"] = s_b0
    mm = M.MMF(); mm.insert_defaults(); mm.process(L1, R1)
    pairs = [("cut_t", s_b0["filter +0x498"]["cut_t+0x18"], mm.filt.cut_t), ("cut_c", s_b0["filter +0x498"]["cut_c+0x1c"], mm.filt.cut_c),
             ("q_t", s_b0["filter +0x498"]["q_t+0x28"], mm.filt.q_t), ("cur kind", s_b0["filter +0x498"]["cur+0x14"], mm.filt.cur),
             ("up48", s_b0["filter +0x498"]["up+0x48"], mm.filt.up48), ("down4c", s_b0["filter +0x498"]["down+0x4c"], mm.filt.dn4c),
             ("glide44", s_b0["filter +0x498"]["glide_steps+0x44"], mm.filt.g44),
             ("gate cur", s_b0["filter +0x498"]["gate+0xc"]["cur+0x24"], mm.filt.gate.r.cur),
             ("gain target", s_b0["gain +0x49c"]["target+4"], mm.gain.target), ("gain cur", s_b0["gain +0x49c"]["cur+8"], mm.gain.cur),
             ("wet", s_b0["EffectBase dry+0x10 / wet+0x14"][1], mm.wet), ("dry", s_b0["EffectBase dry+0x10 / wet+0x14"][0], mm.dry)]
    check(all(f32(float(b)) == a_ for _, a_, b in pairs), "model state after block 0 equals emulated fields: %s" %
          ", ".join("%s %r/%r" % (n, a_, float(b)) for n, a_, b in pairs))

    if not a.quick:
        # ---------------- C4 parameter formulas ---------------------------------------------------------------------
        P(); P("== C4 parameter -> stored coefficient (slot 14 set after a defaults block, one slot-25 block applies it) ==")
        VALS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        def after(sets, blocks=1):
            y = EmuMMF(); y.process(L1, R1)
            for i_, v_ in sets: y.set_param(i_, v_)
            for _ in range(blocks): y.process(L1, R1)
            return y.state()
        rows = []
        for v in VALS:
            v = f32(v)
            st = after([(0, v)]); rows.append(("CUTOFF", v, "cut_t+0x18 (Hz)", st["filter +0x498"]["cut_t+0x18"], M.MMF.cutoff_hz(v)))
            st = after([(2, v)]); rows.append(("Q", v, "q_t+0x28", st["filter +0x498"]["q_t+0x28"], M.MMF.q_of(v)))
            st = after([(1, v)]); g = st["gain +0x49c"]
            rows.append(("GAIN", v, "target+4 (linear)", g["target+4"], M.MMF.gain_lin(v)))
            rows.append(("GAIN", v, "dB = 45v - 30", 20 * math.log10(g["target+4"]) if g["target+4"] > 0 else -999, float(M.MMF.gain_db(v))))
            st = after([(3, v)]); c = st["filter +0x498"]; gs, gf = M.MMF.glide_steps(v)
            m48 = f32(math.pow(10.0, float(f32(f32(math.log10(1000.0)) / gs))))
            rows.append(("GLIDE", v, "steps+0x44", c["glide_steps+0x44"], gs))
            rows.append(("GLIDE", v, "flag+0x42", c["glide+0x42"], gf))
            rows.append(("GLIDE", v, "up+0x48", c["up+0x48"], m48))
            rows.append(("GLIDE", v, "down+0x4c", c["down+0x4c"], f32(1.0 / m48)))
            st = after([(5, v)])
            rows.append(("MIXRATIO", v, "wet+0x14", st["EffectBase dry+0x10 / wet+0x14"][1], f32(v)))
            rows.append(("MIXRATIO", v, "dry+0x10", st["EffectBase dry+0x10 / wet+0x14"][0], f32(1.0 - f32(v))))
        for t in (0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 2.7, -1.0):
            for db in (0.0, 1.0, 2.0):
                st = after([(6, t), (7, db)], blocks=4); c = st["filter +0x498"]
                k = M.kind_of(LM.rnd(float(int(t))), LM.rnd(db))
                rows.append(("FILTERTYPE/DB", (t, db), "pending+0x10", c["pending+0x10"], k))
                rows.append(("FILTERTYPE/DB", (t, db), "cur+0x14 (4 blk)", c["cur+0x14"], k))
        nbad = 0; nbit = 0; c4 = {}
        for name, v, fld, got, exp in rows:
            if fld.startswith("dB"):
                ok = abs(got - exp) <= 1e-4; nbit += ok
            elif isinstance(exp, int):
                ok = got == exp; nbit += ok
            else:
                ok = got == f32(exp) or (exp != 0 and abs(got - exp) / abs(exp) <= 1e-6); nbit += f2u(got) == f2u(f32(exp))
            nbad += not ok
            c4.setdefault(name, []).append({"v": v, "field": fld, "emu": got, "formula": float(exp), "ok": ok})
        for name in c4:
            P("  %-13s %s" % (name, "; ".join("%s %s=%.9g/%.9g%s" % (r["v"], r["field"].split()[0], r["emu"], r["formula"],
                                                                    "" if r["ok"] else " MISMATCH") for r in c4[name])))
        check(nbad == 0, "all %d readbacks equal the closed-form formula (bit-exact float32/int, or dB within 1e-4); exact: %d/%d"
              % (len(rows), nbit, len(rows)))
        res["C4_rows"] = c4; res["C4_exact"] = [nbit, len(rows)]
        # biquad coefficients per kind after the ramp settles: emulation vs model (and vs the LoFi biquad formula)
        P("  biquad coefficients after the ramp settles (12 blocks), emu vs model:")
        cbad = 0; cq = []
        for ft, db, cv, qv in [(0.0, 1.0, 0.4, 0.3), (1.0, 1.0, 0.5, 0.6), (2.0, 1.0, 0.55, 0.2), (0.0, 0.0, 0.45, 0.7),
                               (1.0, 2.0, 0.35, 0.4), (2.0, 0.0, 0.6, 0.9), (0.0, 0.0, 1.0, 1.0), (2.0, 0.0, 0.0, 0.0)]:
            y = EmuMMF(); mm = M.MMF(); mm.insert_defaults()
            for o_ in (y, mm):
                o_.process(L1, R1)
                o_.set_param(6, ft); o_.set_param(7, db); o_.set_param(0, cv); o_.set_param(2, qv)
                for _ in range(12): o_.process(L1, R1)
            st = y.state()["filter +0x498"]; k = st["cur+0x14"]
            es = st["wrappers"][k]["stages"]; ms = mm.filt.w[k].stages
            ok = len(es) == len(ms) and all(e_["b0,b1,b2,a1,a2 +0x28.."] == [float(c) for c in (s.b0, s.b1, s.b2, s.a1, s.a2)] and
                                            e_["fc+0xc"] == float(s.fc) and e_["Q+0x40"] == s.Q for e_, s in zip(es, ms))
            qexp = M.MMF.q_of(qv)
            qok = all(e_["Q+0x40"] == (float(qexp) if k < 3 else math.sqrt(float(qexp))) for e_ in es)
            cbad += not (ok and qok)
            cq.append({"kind": k, "CUTOFF": cv, "Q": qv, "fc": es[0]["fc+0xc"], "Q_stage": es[0]["Q+0x40"], "emu": es[0]["b0,b1,b2,a1,a2 +0x28.."],
                       "ok": ok, "q_ok": qok})
            P("   kind %d (%s) CUTOFF %.2f Q %.2f: fc %.6g stage-Q %.9g (Q %.6g) b/a %s %s" %
              (k, M.KIND_NAMES[k], cv, qv, es[0]["fc+0xc"], es[0]["Q+0x40"], qexp, ["%.7g" % c for c in es[0]["b0,b1,b2,a1,a2 +0x28.."]],
               "== model" if ok and qok else "!= model"))
        check(cbad == 0, "biquad coefficients of every kind (LPF/HPF/BPF x 12/24 dB, fc clamp 5..22050) equal the model bit-exactly; "
              "24 dB stages carry Q' = sqrt(Q)")
        res["C4_biquad"] = cq

    # ---------------- C6 model vs emulation --------------------------------------------------------------------------
    P(); P("== C6 model vs emulation (slot 25 direct, %d blocks x %d, stereo) ==" % (NBLK, N))
    cases = C6_CASES[:1] if a.quick else C6_CASES
    c6 = {}; allexact = True; kinds_seen = set()
    for name, pr, setp, ev in cases:
        for sig in C6_SIGNALS:
            L, R, out = run_both(sig, setp, ev, prime=pr)
            c = compare(out["emu"][:2], out["model"][:2])
            c["emu_sha"] = sha(pack(*out["emu"][:2]))[:16]
            c["rms_in"] = rms(L + R); c["rms_out"] = rms(out["emu"][0] + out["emu"][1])
            kinds_seen.add(out["emu"][2].state()["filter +0x498"]["cur+0x14"])
            c6["%s/%s" % (name, sig)] = c
            ex = c["bit_exact"] == c["n"]; allexact &= ex
            P("  %-20s %-10s bit-exact %4d/%d  max|err| %.3g  first diff %s  rms in/out %.4f/%.4f  sha %s" %
              (name, sig, c["bit_exact"], c["n"], c["max_abs_err"], c["first_diff_index"], c["rms_in"], c["rms_out"], c["emu_sha"]))
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, sig)), "wb") as fh: fh.write(pack(*out["emu"][:2]))
    res["C6"] = c6
    check(allexact, "model output is bit-exact to emulated 1.60 slot 25 in all %d C6 runs" % len(c6))
    P("  final filter kinds reached across cases: %s" % sorted(kinds_seen))

    if not a.quick:
        # ---------------- C7 alternatives ---------------------------------------------------------------------------
        P(); P("== C7 alternative explanations ==")
        # (a) 24 dB cascade with Q' = Q (not sqrt): a model variant must diverge from the emulation
        class AltQ(M.Wrapper):
            def configure(self, cut_c, q_c, flag):
                k = self.kind; self.kind = 0 if k < 6 else k        # pretend single-stage Q mapping
                M.Wrapper.configure(self, cut_c, q_c, flag); self.kind = k
        class MMFAltQ(M.MMF):
            def __init__(s, *aa, **kk):
                M.MMF.__init__(s, *aa, **kk)
                for k in range(7):
                    w = s.filt.w[k]; nw = AltQ(k, FS); nw.stages = w.stages; s.filt.w[k] = nw
        setp = [(6, 0.0), (7, 0.0), (0, 0.45), (2, 0.7)]
        _, _, o1 = run_both("noise", setp, prime=3)
        _, _, o2 = run_both("noise", setp, prime=3, model_cls=MMFAltQ, model_only=True)
        c_t = compare(o1["emu"][:2], o1["model"][:2]); c_a = compare(o1["emu"][:2], o2["model"][:2])
        P("  (a) LPF 24 dB, Q 0.7*: model with Q' = sqrt(Q): %d/%d bit-exact; variant with Q' = Q: %d/%d, max|err| %.3g" %
          (c_t["bit_exact"], c_t["n"], c_a["bit_exact"], c_a["n"], c_a["max_abs_err"]))
        check(c_t["bit_exact"] == c_t["n"] and c_a["bit_exact"] < c_a["n"] // 2, "24 dB = two biquads with Q' = sqrt(Q) each, not Q")
        res["C7a"] = {"sqrtQ": c_t, "sameQ": c_a}
        # (b) cutoff change glided (stepped) vs immediate; and glide time vs GLIDE
        traj = {}
        for gv, cv in ((0.0, 0.3), (0.0, 0.53), (0.5, 0.3), (1.0, 0.3)):
            y = EmuMMF(); mm = M.MMF(); mm.insert_defaults(); sett = {}
            for nm_, o_ in (("emu", y), ("model", mm)):
                o_.process(L1, R1); o_.set_param(3, gv); o_.process(L1, R1); o_.set_param(0, cv); cs = []
                for b in range(400):
                    o_.process(L1, R1)
                    if nm_ == "emu":
                        st = y.state()["filter +0x498"]; cs.append((st["cut_c+0x1c"], st["gate+0xc"]["state+0x20"], st["cut_t+0x18"]))
                    else:
                        cs.append((float(mm.filt.cut_c), mm.filt.gate.r.state, float(mm.filt.cut_t)))
                    if cs[-1][0] == cs[-1][2] and b > 2: break
                sett[nm_] = (next((b for b, c_ in enumerate(cs) if c_[0] == c_[2]), None), cs)
            cs = sett["emu"][1]
            gated = any(c_[1] == 1 for c_ in cs[:3]) and cs[0][0] == cs[1][0]
            ratio = cs[0][2] / 997.7688598632812
            traj["%.1f/%.2f" % (gv, cv)] = {"settle_block_emu": sett["emu"][0], "settle_block_model": sett["model"][0],
                                            "gated_jump": gated, "ratio": ratio, "first4_cut_c": [round(c_[0], 2) for c_ in cs[:4]]}
            P("  (b) GLIDE %.1f, cutoff 997.8 -> %.2f Hz (ratio %.3f): cut_c first blocks %s; equals target from block %s (model %s); "
              "gate fade-out jump: %s" % (gv, cs[0][2], ratio, [round(c_[0], 2) for c_ in cs[:4]], sett["emu"][0], sett["model"][0], gated))
        t = traj
        check(all(v["settle_block_emu"] == v["settle_block_model"] for v in t.values()) and t["0.0/0.30"]["gated_jump"] and
              not t["0.0/0.53"]["gated_jump"] and not t["0.5/0.30"]["gated_jump"] and
              t["1.0/0.30"]["settle_block_emu"] > t["0.5/0.30"]["settle_block_emu"] > t["0.0/0.53"]["settle_block_emu"],
              "GLIDE 0: a large cutoff jump (> 9.728 steps) fades the gate out and jumps, a small one glides; GLIDE > 0: always an "
              "exponential glide, longer for larger GLIDE (emu settle block = model)")
        res["C7b"] = traj
        # (c) GAIN after vs. before the filter: model variant applying the gain ramp before the filter
        class MMFPre(M.MMF):
            def process(s, L, R):
                L = [LM.F(v) for v in L]; R = [LM.F(v) for v in R]; n = len(L)
                s.apply_params(); s.gain.process(L, R, n); s.filt.process(L, R, 0, n)
                if s.params[5].changed():
                    v = s.params[5].get(); s.wet = v; s.dry = LM.F(LM.F(1.0) - v)
                return L, R
        setp = [(6, 1.0), (7, 1.0), (0, 0.5), (2, 0.6), (1, 0.85)]
        _, _, o1 = run_both("noise", setp, prime=3)
        _, _, o2 = run_both("noise", setp, prime=3, model_cls=MMFPre, model_only=True)
        c_t = compare(o1["emu"][:2], o1["model"][:2]); c_a = compare(o1["emu"][:2], o2["model"][:2])
        P("  (c) HPF 12 dB, GAIN 0.85 (+8.25 dB): gain after filter %d/%d bit-exact; gain before filter %d/%d (max|err| %.3g)" %
          (c_t["bit_exact"], c_t["n"], c_a["bit_exact"], c_a["n"], c_a["max_abs_err"]))
        check(c_t["bit_exact"] == c_t["n"] and c_a["bit_exact"] < c_t["n"], "GAIN is applied after the filter (pre-filter gain differs)")
        res["C7c"] = {"after": c_t, "before": c_a}
        # (d) FILTERDB 0 vs 2 (both two-stage), and 1 (single)
        outs = {}
        for db in (0.0, 1.0, 2.0):
            _, _, o_ = run_both("noise", [(6, 2.0), (7, db), (0, 0.5), (2, 0.5)], emu_only=True, prime=3)
            outs[db] = o_["emu"][0]
        P("  (d) BPF, FILTERDB 0 == 2: %s; 0 == 1: %s" % (outs[0.0] == outs[2.0], outs[0.0] == outs[1.0]))
        check(outs[0.0] == outs[2.0] and outs[0.0] != outs[1.0], "FILTERDB 0 and 2 give identical output (24 dB); 1 differs (12 dB)")
        # (e) index 4 'NONE' has no effect on the output
        _, _, o_a = run_both("noise", [(6, 0.0), (0, 0.5)], emu_only=True, prime=3)
        _, _, o_b = run_both("noise", [(6, 0.0), (0, 0.5), (4, 0.77)], emu_only=True, prime=3)
        check(o_a["emu"][0] == o_b["emu"][0], "parameter 4 'NONE' set to 0.77 leaves the output bit-identical")
        # (f) the LoFi biquad formula: MMF stage coefficients equal lofi.Biquad for the same fc/Q (shared IirFilter code)
        y = EmuMMF(); y.process(L1, R1); y.set_param(6, 1.0); y.set_param(0, 0.42); y.set_param(2, 0.33)
        for _ in range(12): y.process(L1, R1)
        st = y.state()["filter +0x498"]["wrappers"][1]["stages"][0]
        bq = LM.Biquad("hpf", FS); bq.fc = LM.F(st["fc+0xc"]); bq.Q = st["Q+0x40"]; bq.coefs()
        same = st["b0,b1,b2,a1,a2 +0x28.."] == [float(c) for c in (bq.b0, bq.b1, bq.b2, bq.a1, bq.a2)]
        P("  (f) HPF 12 dB stage: emulated coefficients == lofi.Biquad('hpf') closed form: %s" % same)
        check(same, "MMF biquads use the LoFi-documented bilinear formulas (same IirFilter code)")
        # (g) start-up: gate ramp (n/132) on the filter output at defaults
        L, R, out = run_both("sine1k", nblk=4, model_only=False)
        gb = [round(rms(out["emu"][0][b * N:(b + 1) * N]) / rms(L[b * N:(b + 1) * N]), 4) for b in range(4)]
        P("  (g) cold defaults, 1 kHz sine, per-block rms gain emu: %s (filter gate 0->1 over 132 samples, LPF 997.8 Hz Q 0.7)" % gb)
        res["C7g_startup_gain"] = gb

    P(); P("RESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h023_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(res, open(os.path.join(a.out, "h023.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
