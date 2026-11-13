#!/usr/bin/env python3
"""H021 — LoFi (Insert index 5) algorithm reconstruction: 1.60 emulation (slot 25 0xfc0f4 called directly) vs. the own-code
Python model harness/models/lofi.py.

Sections (criteria of kb/cycles/005.md):
  C2  parameter formulas: set each parameter through EffectBase slot 14 0x105d24 at 7 values, run one slot-25 block (which applies
      it in 0xfb20c / slot 26), read the stored coefficient(s) from the emulated object and compare with the closed-form formula.
      Also the biquad coefficients of each sub-filter (after the ramp settles) and the static-init globals.
  C3  state layout dump after init / after a block (offsets read from the emulated object).
  C4  model vs. emulation matrix: impulse, 1 kHz sine, white noise (seed 1234), 16 x 64 stereo, several parameter settings and
      parameter-change sequences; per-case bit-exact count and max |error|.
  C5  start-up: per-block rms gain at defaults, emulation vs. model vs. the (i/132)^2 law.
  C6  alternatives: FILTERTYPE 0 vs 3, quantiser sign symmetry / truncation, S&H vs. interpolation, BITDEPTH/REDUCTION 0.5
      "no change" = change-detection (last value 0.5) vs. mapping.
Outputs only to --out (default harness/out/H021/). Run: .venv/bin/python -B harness/H021_lofi_model.py --out DIR
"""
import argparse, hashlib, json, math, os, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import random                                                 # noqa: E402
from emu import f2u, u2f                                      # noqa: E402
import H007_effect_emu as H7                                  # noqa: E402
import lofi as M                                              # noqa: E402

N = 64
FS = 44100
NBLK = 16
FX = H7.EFFECTS["lofi"]
PARAM_OFF = {0: 0x1b8, 1: 0x270, 2: 0x214, 3: 0x2cc, 4: 0x328, 5: 0x384, 6: 0x3e0, 7: 0x43c}   # slot-14 index -> object offset


def sha(b): return hashlib.sha256(b).hexdigest()
def f32(x): return u2f(f2u(x))


# ------------------------------------------------------------------------------------------------------------------------
class EmuLoFi:
    """1.60 LoFi object built by its ctor + Insert init (H007), processed by calling slot 25 directly."""
    def __init__(self, defaults=True):
        self.r = H7.Run(FX); self.e = self.r.e; self.o = self.r.obj
        if defaults: self.r.insert_init()
        self.bl = self.e.malloc(4 * N, "L"); self.br = self.e.malloc(4 * N, "R")

    def set_param(self, idx, v): return self.r.set_param(idx, v)

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    # field readers
    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def f(self, a): return self.e.f32(a)
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]

    def state(self):
        o = self.o; u, i, f, d = self.u, self.i, self.f, self.d
        P, Q, H, Fc, G = (u(o + x) for x in (0x498, 0x49c, 0x4a0, 0x4a4, 0x4a8))
        def gate(g):
            return {"vptr": hex(u(g)), "state+0x20": i(g + 0x20), "cur+0x24": f(g + 0x24), "target+0x28": f(g + 0x28),
                    "inc+0x2c": f(g + 0x2c), "rem+0x30": i(g + 0x30), "ms+0x34": f(g + 0x34), "N+0x38": i(g + 0x38),
                    "invN+0x3c": f(g + 0x3c), "off+0x40": f(g + 0x40), "on+0x44": f(g + 0x44), "fs+0x1c": i(g + 0x1c),
                    "fs+0x10": i(g + 0x10), "bs+0x14": i(g + 0x14), "inv_fs+0x18": f(g + 0x18), "buf+0xc": hex(u(g + 0xc))}
        subs = []
        for k in range(u(Fc + 8)):
            s = u(u(Fc) + 4 * k)
            subs.append({"vptr": hex(u(s)), "nyq+4": f(s + 4), "fs+8": i(s + 8), "fc+0xc": f(s + 0xc), "Q+0x40": d(s + 0x40),
                         "b0,b1,b2,a1,a2 +0x28..": [f(s + 0x28 + 4 * j) for j in range(5)], "k+0x24": f(s + 0x24),
                         "flag+0x48": self.e.rd(s + 0x48, 1)[0],
                         "hist +0x10..+0x1c (v,y pairs)": [[f(u(s + 0x10 + 4 * j) + 4 * q) for q in range(4)] for j in range(4)],
                         "yprev +0x20": [f(u(s + 0x20)), f(u(s + 0x20) + 4)]})
        st = {
            "EffectBase dry+0x10 / wet+0x14": [f(o + 0x10), f(o + 0x14)],
            "pos pending+0x4ac / current+0x4b0": [i(o + 0x4ac), i(o + 0x4b0)],
            "preamp +0x498": {"N+0": i(P), "target+4": f(P + 4), "cur+8": f(P + 8), "inc+0xc": f(P + 0xc), "cnt+0x10": i(P + 0x10)},
            "crusher +0x49c": {"bits+0": i(Q), "scale+4": f(Q + 4), "inv+8": f(Q + 8)},
            "samplehold +0x4a0": {"fs+0": i(H), "fs+4": i(H + 4), "phase+8": f(H + 8), "step+0xc": f(H + 0xc),
                                  "holdL+0x10": f(H + 0x10), "holdR+0x14": f(H + 0x14)},
            "filter +0x4a4": {"count+8": u(Fc + 8), "pending+0x10": i(Fc + 0x10), "cur+0x14": i(Fc + 0x14),
                              "cut_t+0x18": f(Fc + 0x18), "cut_c+0x1c": f(Fc + 0x1c), "cut_mult+0x20": f(Fc + 0x20),
                              "cut_steps+0x24": i(Fc + 0x24), "q_t+0x28": f(Fc + 0x28), "q_c+0x2c": f(Fc + 0x2c),
                              "q_mult+0x30": f(Fc + 0x30), "q_steps+0x34": i(Fc + 0x34), "next+0x38": f(Fc + 0x38),
                              "maxsteps+0x3c": i(Fc + 0x3c), "flag+0x40": self.e.rd(Fc + 0x40, 1)[0],
                              "dirty+0x41": self.e.rd(Fc + 0x41, 1)[0], "gate+0xc": gate(u(Fc + 0xc)), "subs": subs},
            "posgate +0x4a8": gate(G),
            "params (last, cur)": {M.PARAM_NAMES[k]: ([f(o + off + 0x24), f(o + off + 0x28)] if k < 6 else
                                                      [i(o + off + 0x40), i(o + off + 0x44)]) for k, off in PARAM_OFF.items()},
            "globals 0xf52ebc..": [f(0xf52ebc + 4 * k) for k in range(5)],
        }
        return st


# ------------------------------------------------------------------------------------------------------------------------
def signal(kind, nblk=NBLK, seed=1234):
    tot = N * nblk
    if kind == "impulse":
        L = [1.0 if k == 0 else 0.0 for k in range(tot)]; R = [-0.5 if k == 0 else 0.0 for k in range(tot)]
    elif kind == "impulse_b4":                     # impulse after the start-up fades (block 4, sample 3)
        k0 = 4 * N + 3
        L = [0.9 if k == k0 else 0.0 for k in range(tot)]; R = [-0.45 if k == k0 else 0.0 for k in range(tot)]
    elif kind == "sine1k":
        L = [0.5 * math.sin(2 * math.pi * 1000.0 * k / FS) for k in range(tot)]
        R = [0.5 * math.cos(2 * math.pi * 1000.0 * k / FS) for k in range(tot)]
    elif kind == "noise":
        g = random.Random(seed)
        L = [g.uniform(-0.8, 0.8) for _ in range(tot)]; R = [g.uniform(-0.8, 0.8) for _ in range(tot)]
    elif kind == "ramp":                           # slow ramp -1..1 (quantiser transfer curve, both signs)
        L = [-1.0 + 2.0 * k / (tot - 1) for k in range(tot)]; R = [1.0 - 2.0 * k / (tot - 1) for k in range(tot)]
    else:
        raise ValueError(kind)
    return [f32(x) for x in L], [f32(x) for x in R]


def run_both(sig, setp=(), events=(), nblk=NBLK, model_only=False, emu_only=False, want_state=False, prime=0):
    """prime: silent slot-25 blocks run first (not returned) so the Insert defaults are applied and both start-up fades are done
    (132 samples < 3 blocks); setp: [(idx, v)] set after that; events: [(block, idx, v)] set before that compared block.
    Note: with prime=0, a value equal to the parameter's ctor 'last' value (float 0.5, FILTERTYPE 0, FILTERPOSITION 2) is never
    applied (0xf0ffc change detection), which is part of the 1.60 behaviour being modelled."""
    L, R = signal(sig, nblk)
    out = {}
    for which in ("emu", "model"):
        if (which == "emu" and model_only) or (which == "model" and emu_only): continue
        if which == "emu":
            x = EmuLoFi()
        else:
            x = M.LoFi(); x.insert_defaults()
        for _ in range(prime): x.process([0.0] * N, [0.0] * N)
        for idx, v in setp: x.set_param(idx, v)
        oL, oR, states = [], [], []
        for b in range(nblk):
            for (eb, idx, v) in events:
                if eb == b: x.set_param(idx, v)
            l, r = x.process(L[b * N:(b + 1) * N], R[b * N:(b + 1) * N])
            oL += l; oR += r
            if want_state and which == "emu": states.append(x.state())
        out[which] = (oL, oR, states, x)
    return L, R, out


def pack(L, R): return struct.pack("<%df" % len(L), *L) + struct.pack("<%df" % len(R), *R)


def compare(a, b):
    A = [f32(v) for v in a[0] + a[1]]; B = [f32(v) for v in b[0] + b[1]]
    bit = sum(1 for x, y in zip(A, B) if f2u(x) == f2u(y))
    val = sum(1 for x, y in zip(A, B) if x == y)
    err = max((abs(x - y) for x, y in zip(A, B)), default=0.0)
    first = next((k for k in range(len(A)) if A[k] != B[k]), None)
    return {"n": len(A), "bit_exact": bit, "value_equal": val, "max_abs_err": err, "first_diff_index": first}


def rms(xs): return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else 0.0


# ------------------------------------------------------------------------------------------------------------------------
C4_CASES = [
    # name, prime blocks, settings [(slot-14 index, value)], events [(block, idx, value)]
    # index: 0 PREAMP 1 REDUCTION 2 BITDEPTH 3 CUTOFF 4 RESONANCE 5 MIXRATIO 6 FILTERTYPE 7 FILTERPOSITION
    ("cold_defaults", 0, [], []),
    ("cold_lpf_post_preamp", 0, [(6, 1.0), (3, 0.5), (4, 0.6), (0, 0.4)], []),
    ("cold_bpf_pre_crush", 0, [(6, 2.0), (7, 0.0), (3, 0.55), (4, 0.2), (2, 0.3)], []),
    ("hpf_post_q", 3, [(6, 0.0), (3, 0.4), (4, 0.3)], []),
    ("lpf_post_preamp", 3, [(6, 1.0), (3, 0.5), (4, 0.6), (0, 0.4)], []),
    ("bpf_pre_crush", 3, [(6, 2.0), (7, 0.0), (3, 0.55), (4, 0.2), (2, 0.3)], []),
    ("off_pre_red07_bits07", 3, [(6, 3.0), (7, 0.0), (1, 0.7), (2, 0.7)], []),
    ("lpf_pre_all", 3, [(6, 1.0), (7, 0.0), (0, 0.7), (1, 0.3), (2, 0.3), (3, 0.35), (4, 0.9)], []),
    ("hpf_post_red03_bits07", 3, [(6, 0.0), (7, 1.0), (1, 0.3), (2, 0.7), (0, 0.2), (3, 0.62)], []),
    ("hpf_pre_pos0", 3, [(6, 0.0), (7, 0.0), (3, 0.3), (4, 0.8), (0, 1.0)], []),
    ("seq_type_pos_cutjump", 3, [(6, 1.0), (3, 0.5)], [(5, 6, 2.0), (8, 7, 0.0), (10, 3, 0.8), (12, 4, 0.7), (13, 0, 0.5)]),
    ("seq_small_cut_ramp", 3, [(6, 1.0), (3, 0.5)], [(4, 3, 0.52), (9, 3, 0.47), (11, 1, 0.8), (12, 2, 0.6)]),
    ("seq_hpf_to_off_pos2", 3, [(6, 0.0), (3, 0.45), (7, 0.0)], [(3, 6, 3.0), (7, 7, 2.0), (9, 6, 1.0), (12, 7, 0.0)]),
]
C4_SIGNALS = ["impulse", "impulse_b4", "sine1k", "noise"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H021"))
    ap.add_argument("--quick", action="store_true", help="only defaults case (debug)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)

    # ---------------- C3 state after init and after block 0 -------------------------------------------------------
    P("== C3 state layout (emulated 1.60 object) ==")
    x = EmuLoFi(defaults=False); s_ctor = x.state()
    x = EmuLoFi(); s_init = x.state()
    L, R = signal("sine1k", 1); x.process(L, R); s_b0 = x.state()
    res["state_after_ctor"] = s_ctor; res["state_after_insert_init"] = s_init; res["state_after_block0"] = s_b0
    for k in ("preamp +0x498", "crusher +0x49c", "samplehold +0x4a0", "pos pending+0x4ac / current+0x4b0",
              "EffectBase dry+0x10 / wet+0x14", "globals 0xf52ebc.."):
        P("  %-36s ctor %s" % (k, s_ctor[k])); P("  %-36s blk0 %s" % ("", s_b0[k]))
    fk = {k: v for k, v in s_b0["filter +0x4a4"].items() if k not in ("subs", "gate+0xc")}
    P("  filter +0x4a4 (after block 0): %s" % fk)
    P("  filter gate (after block 0): %s" % {k: s_b0["filter +0x4a4"]["gate+0xc"][k] for k in
                                            ("vptr", "state+0x20", "cur+0x24", "target+0x28", "rem+0x30", "N+0x38", "off+0x40", "on+0x44")})
    P("  position gate (after block 0): %s" % {k: s_b0["posgate +0x4a8"][k] for k in
                                              ("vptr", "state+0x20", "cur+0x24", "target+0x28", "rem+0x30", "N+0x38", "off+0x40", "on+0x44")})
    for j, s in enumerate(s_ctor["filter +0x4a4"]["subs"]):
        P("  sub-filter %d after ctor: vptr %s nyq %.6g fs %d fc %.6g Q %.17g k %g coefs %s" %
          (j, s["vptr"], s["nyq+4"], s["fs+8"], s["fc+0xc"], s["Q+0x40"], s["k+0x24"], s["b0,b1,b2,a1,a2 +0x28.."]))
    P("  params after insert init (last, cur): %s" % s_init["params (last, cur)"])
    gm = [float(M.G0), float(M.G1), float(M.G2), float(M.G3), float(M.G4)]
    check(s_ctor["globals 0xf52ebc.."] == [f32(v) for v in gm], "static-init globals = [17, 1000^(1/250), inverse, 50^(1/100), inverse] "
          "(model formula): %s" % gm)

    # model state equality for a few scalar fields after block 0
    mm = M.LoFi(); mm.insert_defaults(); mm.process(L, R)
    pairs = [("preamp cur", s_b0["preamp +0x498"]["cur+8"], mm.pre_c), ("preamp target", s_b0["preamp +0x498"]["target+4"], mm.pre_t),
             ("bits", s_b0["crusher +0x49c"]["bits+0"], mm.bits), ("sh step", s_b0["samplehold +0x4a0"]["step+0xc"], mm.sh_step),
             ("sh phase", s_b0["samplehold +0x4a0"]["phase+8"], mm.sh_phase),
             ("cut_t", s_b0["filter +0x4a4"]["cut_t+0x18"], mm.filt.cut_t), ("q_t", s_b0["filter +0x4a4"]["q_t+0x28"], mm.filt.q_t),
             ("posgate cur", s_b0["posgate +0x4a8"]["cur+0x24"], mm.gate.r.cur),
             ("filtgate cur", s_b0["filter +0x4a4"]["gate+0xc"]["cur+0x24"], mm.filt.gate.r.cur),
             ("wet", s_b0["EffectBase dry+0x10 / wet+0x14"][1], mm.wet), ("dry", s_b0["EffectBase dry+0x10 / wet+0x14"][0], mm.dry)]
    check(all(f32(float(b)) == a_ for _, a_, b in pairs), "model state after block 0 equals emulated fields: %s" %
          ", ".join("%s %r/%r" % (n, a_, float(b)) for n, a_, b in pairs))

    if not a.quick:
        # ---------------- C2 parameter formulas -------------------------------------------------------------------------
        P(); P("== C2 parameter -> stored coefficient (slot 14 set, one slot-25 block applies it) ==")
        VALS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        L1, R1 = signal("sine1k", 1)
        c2 = {}
        def after(idx, v, extra=(), blocks=1):
            x = EmuLoFi(); x.process(L1, R1)            # block 0 applies the Insert defaults (so 'last' != 0.5 afterwards)
            for i_, v_ in extra: x.set_param(i_, v_)
            x.set_param(idx, v)
            for _ in range(blocks): x.process(L1, R1)
            return x.state()
        rows = []
        for v in VALS:
            v = f32(v)                                 # the parameter stores float32
            st = after(0, v); p = st["preamp +0x498"]
            e_ = f32(f32(v * 42.0) * f32(0.05)); tgt = f32(math.pow(10.0, e_))
            rows.append(("PREAMP", v, "target+4 (gain)", p["target+4"], tgt))
            st = after(2, v); q = st["crusher +0x49c"]
            bits = M.BITS[int(round(f32(v * 17.0)))]
            rows.append(("BITDEPTH", v, "bits+0", q["bits+0"], bits))
            if bits < 31: rows.append(("BITDEPTH", v, "scale+4", q["scale+4"], float(1 << bits)))
            st = after(1, v); h = st["samplehold +0x4a0"]
            rate = int(round(f32(math.pow(1000.0000610351562, v) * 44.099998474121094)))
            rows.append(("REDUCTION", v, "step+0xc", h["step+0xc"], 1.0 if rate > FS else f32(f32(FS) / f32(rate))))
            st = after(3, v); fc = st["filter +0x4a4"]
            rows.append(("CUTOFF", v, "cut_t+0x18 (Hz)", fc["cut_t+0x18"], f32(math.pow(1000.0, v) * 20.0)))
            st = after(4, v); fc = st["filter +0x4a4"]
            rows.append(("RESONANCE", v, "q_t+0x28 (Q)", fc["q_t+0x28"], f32(f32(0.2) + f32(v * f32(9.8)))))
            st = after(5, v)
            rows.append(("MIXRATIO", v, "wet+0x14", st["EffectBase dry+0x10 / wet+0x14"][1], f32(v)))
            rows.append(("MIXRATIO", v, "dry+0x10", st["EffectBase dry+0x10 / wet+0x14"][0], f32(1.0 - f32(v))))
        for t in (0.0, 1.0, 2.0, 3.0, 2.7, 4.0):
            st = after(6, t, blocks=4); fc = st["filter +0x4a4"]
            exp = int(t) if int(t) <= 3 else 3
            rows.append(("FILTERTYPE", t, "pending+0x10", fc["pending+0x10"], exp))
            rows.append(("FILTERTYPE", t, "cur+0x14 (after 4 blocks)", fc["cur+0x14"], exp))
        for pv in (0.0, 1.0, 2.0):
            for ft in (3.0, 1.0):
                st = after(7, pv, extra=[(6, ft)], blocks=6)
                rows.append(("FILTERPOSITION", pv, "pending+0x4ac (FT %d)" % ft, st["pos pending+0x4ac / current+0x4b0"][0], int(pv)))
                rows.append(("FILTERPOSITION", pv, "current+0x4b0 (FT %d, 6 blk)" % ft, st["pos pending+0x4ac / current+0x4b0"][1], int(pv)))
        nbad = 0; nbit = 0
        for name, v, fld, got, exp in rows:
            ok = (got == exp) if isinstance(exp, int) else (got == f32(exp) or (exp != 0 and abs(got - exp) / abs(exp) <= 1e-6))
            nbit += (got == exp) if isinstance(exp, int) else (f2u(got) == f2u(f32(exp)))
            if not ok: nbad += 1
            c2.setdefault(name, []).append({"v": v, "field": fld, "emu": got, "formula": float(exp), "ok": ok})
        for name in c2:
            P("  %-14s %s" % (name, "; ".join("%s %s=%.9g/%.9g%s" % (r["v"], r["field"].split()[0], r["emu"], r["formula"],
                                                                     "" if r["ok"] else " MISMATCH") for r in c2[name])))
        check(nbad == 0, "all %d stored-coefficient readbacks equal the closed-form formula (bit-exact float32 or rel err <= 1e-6); "
              "bit-exact: %d/%d" % (len(rows), nbit, len(rows)))
        res["C2_bit_exact"] = [nbit, len(rows)]
        res["C2_rows"] = c2

        # biquad coefficients after the ramp settles, per type
        P("  biquad coefficients after ramp settles (12 blocks), emu vs model:")
        cbad = 0; cq = []
        for ft, cv, rv in [(0.0, 0.4, 0.3), (1.0, 0.5, 0.6), (2.0, 0.55, 0.2), (1.0, 0.95, 0.0), (0.0, 0.05, 1.0), (2.0, 1.0, 0.5),
                           (2.0, 0.2, 0.0)]:
            x = EmuLoFi(); mm = M.LoFi(); mm.insert_defaults()
            for o_ in (x, mm):
                o_.process(L1, R1)                     # apply the Insert defaults first (else FILTERTYPE 0 = ctor 'last' is ignored)
                o_.set_param(6, ft); o_.set_param(3, cv); o_.set_param(4, rv)
                for _ in range(12): o_.process(L1, R1)
            st = x.state()["filter +0x4a4"]; sub = st["subs"][int(ft)]
            ms = mm.filt.subs[int(ft)]
            me = [float(ms.b0), float(ms.b1), float(ms.b2), float(ms.a1), float(ms.a2)]
            ok = sub["b0,b1,b2,a1,a2 +0x28.."] == me and sub["fc+0xc"] == float(ms.fc) and sub["Q+0x40"] == ms.Q
            cbad += not ok
            cq.append({"type": ft, "CUTOFF": cv, "RES": rv, "fc": sub["fc+0xc"], "Q": sub["Q+0x40"], "emu": sub["b0,b1,b2,a1,a2 +0x28.."],
                       "model": me, "ok": ok, "cut_c": st["cut_c+0x1c"], "cut_t": st["cut_t+0x18"]})
            P("   type %d CUTOFF %.2f RES %.2f: fc %.6g (cut_t %.6g) Q %.6g coefs %s %s" %
              (ft, cv, rv, sub["fc+0xc"], st["cut_t+0x18"], sub["Q+0x40"], ["%.7g" % c for c in sub["b0,b1,b2,a1,a2 +0x28.."]],
               "== model" if ok else "!= model %s" % me))
        check(cbad == 0, "biquad coefficients (HPF/LPF/BPF formulas, fc clamp 5..22050, Q double) match the model bit-exactly")
        res["C2_biquad"] = cq

    # ---------------- C4 model vs emulation --------------------------------------------------------------------------
    P(); P("== C4 model vs emulation (slot 25 direct, %d blocks x %d, stereo) ==" % (NBLK, N))
    cases = C4_CASES[:1] if a.quick else C4_CASES
    c4 = {}; allexact = True
    for name, pr, setp, ev in cases:
        for sig in C4_SIGNALS:
            L, R, out = run_both(sig, setp, ev, prime=pr)
            c = compare(out["emu"][:2], out["model"][:2])
            c["emu_sha"] = sha(pack(*out["emu"][:2]))[:16]; c["model_sha"] = sha(pack(*out["model"][:2]))[:16]
            c["rms_in"] = rms(L + R); c["rms_out"] = rms(out["emu"][0] + out["emu"][1])
            c4["%s/%s" % (name, sig)] = c
            ex = c["bit_exact"] == c["n"]
            allexact &= ex
            P("  %-22s %-8s bit-exact %4d/%d  max|err| %.3g  first diff %s  rms in/out %.4f/%.4f  sha %s" %
              (name, sig, c["bit_exact"], c["n"], c["max_abs_err"], c["first_diff_index"], c["rms_in"], c["rms_out"], c["emu_sha"]))
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, sig)), "wb") as fh: fh.write(pack(*out["emu"][:2]))
    res["C4"] = c4
    check(allexact, "model output is bit-exact to emulated 1.60 slot 25 in all %d C4 runs" % len(c4))

    # ---------------- C5 start-up -------------------------------------------------------------------------------------
    P(); P("== C5 start-up at defaults (slot 25 direct, 1 kHz sine) ==")
    L, R, out = run_both("sine1k", nblk=4)
    law = [((k + 1) / 132.0 if False else min(k, 132) / 132.0) ** 2 for k in range(4 * N)]
    rowsg = []
    for b in range(4):
        sl = slice(b * N, (b + 1) * N)
        gi = rms(L[sl]); ge = rms(out["emu"][0][sl]) / gi; gm_ = rms(out["model"][0][sl]) / gi
        gl = rms([x * w for x, w in zip(L[sl], law[sl])]) / gi
        rowsg.append((b, round(ge, 4), round(gm_, 4), round(gl, 4)))
    P("  per block (block, emu rms gain, model rms gain, (n/132)^2 law): %s" % rowsg)
    gk = [out["emu"][0][k] / L[k] for k in range(1, 140) if abs(L[k]) > 0.05]
    P("  emu sample gain / (n/132)^2 at n = 10, 50, 100, 131, 140: %s" %
      ["%.6f" % (out["emu"][0][k] / L[k] / max(law[k], 1e-30)) for k in (10, 50, 100, 131, 140)])
    res["C5"] = rowsg

    # ---------------- C6 alternatives ---------------------------------------------------------------------------------
    if not a.quick:
        P(); P("== C6 alternative explanations ==")
        # (a) FILTERTYPE 0 vs 3 (F025 said identical through slot 18)
        _, _, o0 = run_both("impulse_b4", [(6, 0.0)], emu_only=True, prime=3)
        _, _, o3 = run_both("impulse_b4", [(6, 3.0)], emu_only=True, prime=3)
        k0 = 4 * N + 3
        P("  (a) primed (3 silent blocks), late impulse, FILTERTYPE 0 (IirHpf2ndOrder) L[k0:k0+5]: %s" % ["%.6g" % v for v in o0["emu"][0][k0:k0 + 5]])
        P("      late impulse, FILTERTYPE 3 (IirOff)         L[k0:k0+5]: %s" % ["%.6g" % v for v in o3["emu"][0][k0:k0 + 5]])
        same = o0["emu"][0] == o3["emu"][0]
        check(not same, "FILTERTYPE 0 and 3 differ once FILTERTYPE 0 is actually applied (0 = HPF ~998 Hz, 3 = no filter)")
        res["C6_ft0_vs_ft3_identical"] = same
        # F025 conditions: set via slot 14 BEFORE the defaults block in H007 -- H007 set FILTERTYPE 0.0: is it the same as
        # the ctor 'last' value (0)?  Then no change is detected and the filter stays IirOff.
        x = EmuLoFi(); x.set_param(6, 0.0); st = x.state()
        P("      H007 sequence (Insert init, then slot14 FILTERTYPE 0.0, no block yet): FILTERTYPE (last, cur) = %s" %
          st["params (last, cur)"]["FILTERTYPE"])
        _, _, oh = run_both("impulse_b4", [(6, 0.0)], emu_only=True)
        st = oh["emu"][3].state()
        check(oh["emu"][0] == o3["emu"][0] or st["filter +0x4a4"]["cur+0x14"] == 3, "H007/F025 sequence (FILTERTYPE 0.0 set before "
              "the first block) leaves the filter on IirOff: F025's 'type 0 == type 3' is change detection, not the filter")
        P("      cold (no priming), after 16 blocks: filter pending/cur = %d/%d; FILTERTYPE (last, cur) = %s" %
          (st["filter +0x4a4"]["pending+0x10"], st["filter +0x4a4"]["cur+0x14"], st["params (last, cur)"]["FILTERTYPE"]))
        res["C6_ft0_after"] = [st["filter +0x4a4"]["pending+0x10"], st["filter +0x4a4"]["cur+0x14"]]
        # (b) quantiser: truncation of sqrt-companded magnitude, odd symmetric; vs. plain rounding / plain truncation
        L, R, out = run_both("ramp", [(2, 0.3)], nblk=4)
        ex = out["emu"][0]; inp = L
        bits = M.BITS[int(round(f32(0.3 * 17.0)))]
        odd = all(abs(ex[k] + ex[len(ex) - 1 - k]) < 1e-7 for k in range(len(ex)) if abs(inp[k] + inp[len(inp) - 1 - k]) < 1e-7)
        def plain(x, mode):
            s = 1 << bits; v = x * s
            return (math.floor(v + 0.5) if mode == "round" else math.trunc(v)) / s
        idx = range(3 * N, 4 * N)
        e_sq = max(abs(ex[k] - math.copysign((math.trunc(2 ** bits * math.sqrt(abs(inp[k]))) / 2 ** bits) ** 2, inp[k])) for k in idx)
        e_rd = max(abs(ex[k] - plain(inp[k], "round")) for k in idx)
        e_tr = max(abs(ex[k] - plain(inp[k], "trunc")) for k in idx)
        P("  (b) BITDEPTH 0.3 -> %d bits, ramp input (block 3, after fades): max|emu - sign*(trunc(2^b sqrt|x|)/2^b)^2| = %.3g;"
          " vs plain round %.3g; vs plain trunc %.3g; distinct output levels %d" % (bits, e_sq, e_rd, e_tr, len(set(ex[3 * N:4 * N]))))
        check(e_sq < 1e-6 and e_rd > 1e-3 and e_tr > 1e-3, "quantiser = sqrt-companded magnitude truncation (not plain rounding/truncation)")
        res["C6_quantiser"] = {"bits": bits, "err_sqrt_trunc": e_sq, "err_plain_round": e_rd, "err_plain_trunc": e_tr}
        # negative inputs: emulate a single block with mirrored signs directly
        x = EmuLoFi(); Lb, Rb = signal("ramp", 1); x.set_param(2, 0.3)
        for _ in range(4): l1, r1 = x.process(Lb, Rb)
        neg = all(abs(l1[k] + r1[k]) < 1e-7 for k in range(N))     # R = -L sample by sample in 'ramp'
        check(neg, "quantiser is odd-symmetric: output(-x) = -output(x) (L/R mirrored ramp, block 4)")
        # (c) S&H vs. interpolation: REDUCTION 0.3 -> step; output must be piecewise constant with runs of ~step samples
        L, R, out = run_both("sine1k", [(1, 0.3)], nblk=8, emu_only=True, prime=3)
        ex = out["emu"][0]; inp = L
        runs = []; c = 1; starts = [0]
        for k in range(1, len(ex)):
            if ex[k] == ex[k - 1]: c += 1
            else: runs.append(c); c = 1; starts.append(k)
        interior = runs[1:]                      # the first run is cut by the parameter change; the last run is still open
        sc_ = f32(f32(1.0 + f32(1.0 * 0.2)) * f32(0.8333333))
        held_ok = all(ex[k0_] == f32(sc_ * inp[k0_]) for k0_ in starts)   # each run starts with the current input sample * preamp scale
        rate = int(round(f32(math.pow(1000.0000610351562, 0.3) * 44.099998474121094)))
        P("  (c) REDUCTION 0.3 -> rate %d Hz, step %.5f: run lengths of equal output samples (primed, 8 blocks) %s; each run = the "
          "input sample at its start (x preamp scale %.8f): %s" % (rate, FS / rate, sorted(set(interior)), sc_, held_ok))
        check(held_ok and set(interior) <= {int(FS / rate), int(FS / rate) + 1, len(ex) - starts[-1]},
              "rate reduction is sample-and-hold of input samples (no interpolation), period fs/rate samples")
        # (d) BITDEPTH 0.5 / REDUCTION 0.5 unchanged in H007: change detection, not mapping
        L, R, oa = run_both("sine1k", [(2, 0.5)], nblk=4, emu_only=True)
        L, R, ob = run_both("sine1k", [], nblk=4, emu_only=True)
        L, R, oc = run_both("sine1k", [], [(1, 2, 0.5)], nblk=4, emu_only=True)
        sa = oa["emu"][3].state()["crusher +0x49c"]["bits+0"]; sc = oc["emu"][3].state()["crusher +0x49c"]["bits+0"]
        P("  (d) BITDEPTH 0.5 set before block 0: bits = %d, output == defaults: %s; set at block 1 (after defaults applied): bits = %d,"
          " output == defaults: %s" % (sa, oa["emu"][0] == ob["emu"][0], sc, oc["emu"][0] == ob["emu"][0]))
        check(oa["emu"][0] == ob["emu"][0] and sa == 32 and sc == 9 and oc["emu"][0] != ob["emu"][0],
              "H007's 'BITDEPTH 0.5 = no change' is change detection (last value 0.5 from the ctor), not a >=32-bit mapping: "
              "0.5 maps to 9 bits")
        res["C6_bitdepth05"] = {"before_block0_bits": sa, "at_block1_bits": sc}

        # (e) FILTERPOSITION 1 vs 2 (code tests only +0x4b0 == 0): identical output; 0 differs
        outs_ = {}
        for pv in (0.0, 1.0, 2.0):
            _, _, o_ = run_both("noise", [(6, 0.0), (3, 0.4), (7, pv), (0, 0.6)], emu_only=True, prime=3)
            outs_[pv] = o_["emu"][0]
        P("  (e) FILTERPOSITION with HPF + PREAMP 0.6 (noise, primed): pos1 == pos2: %s; pos0 == pos1: %s" %
          (outs_[1.0] == outs_[2.0], outs_[0.0] == outs_[1.0]))
        check(outs_[1.0] == outs_[2.0] and outs_[0.0] != outs_[1.0], "FILTERPOSITION 1 and 2 are the same (filter after the "
              "crusher chain); only 0 puts the filter first")

    P(); P("RESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h021_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(res, open(os.path.join(a.out, "h021.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
