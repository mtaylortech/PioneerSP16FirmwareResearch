#!/usr/bin/env python3
"""H034 — Flanger (Insert index 1; vtable 0x8429a8, inline new 0x2b0; kernel c_flanger 0x841c10, ctor 0x100234, slot 19 0xff9ac)
end to end: parameters -> formulas -> state layout -> bit-exact own-code model harness/models/flanger.py vs the emulated
1.60 slot 25 0x115f58.

Sections (criteria of kb/cycles/011.md):
  C1  parameter list: slot-14 index map (emulated), Insert slot-52 defaults (case 1), change detection, registrations.
  C2  formula sweeps: emulated read-back of kernel / oscillator / EffectBase fields vs the model after every slot-14 call or
      block (rate free incl. rounding boundaries, rate Sync x 4 tempi, depth / scale / phase / feedback / mixratio), plus the
      sync fraction table (0xf61f78).
  C3  layout: kernel and Flanger fields compared model vs emulation after every block; vtable slot list; kernel slot 4
      (0xfff50), slot 9 (0xff598), slots 16/17 called directly.
  C4  end-to-end matrix: 11 settings x {impulse train, sine, noise} x 160 blocks + 4 event runs x {sine, noise}; slot-25 output
      bit-exact + state (incl. oscillator / gain buffers) after every block + final ring.
  C5  start-up (no mute / fade), reset flag (+0xf2), retrigger (+0xf0 via Flanger slot 10 -> kernel slot 18), slot 27.
  C6  alternatives: feedback after the gain, unquantised feedback, knee scaling with the depth, Chorus rate law / clamp,
      Mixratio inside slot 25, slot-18 sum (EffectBase post-stage neutralised); --mutants runs deliberate model errors.
  C7  Master / Send context: construction blocks compared instruction by instruction; Master-built object run.
Outputs only to --out (default harness/out/H034/). Run: .venv/bin/python -B harness/H034_flanger_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, SP                                    # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import flanger as FL                                           # noqa: E402
import chorus as C                                             # noqa: E402
from osc import F                                              # noqa: E402

FS = 44100; N = 64
FRAC_INIT = (0x6cbe0, 0x6ce8c)      # straight-line part of .init_array entry 0x6cb20 (r4 = 0xf61f18): fills 0xf61f50..0xf61f97
FRAC_TABLE = 0xf61f78               # Flanger sync fractions (read by 0x349eb8), 7 x {u16, u16}
BUILD = {"insert": (0x118cd8, 0x118de0), "master": (0x114e78, 0x114f80), "send": (0x11bea4, 0x11bfac)}
KCTOR = 0x100234


def sha(b): return hashlib.sha256(b).hexdigest()
def fb(x): return f2u(x)
def fl_bits(xs): return tuple(f2u(x) for x in xs)


class EmuFlanger:
    """Flanger built by running the inline block of the 1.60 InsertFxProcessor ctor (0x118cd8-0x118de0), after the sync
    fraction initialiser; then (optionally) the H007 Insert init (slot 22, 0x106c7c(obj,1,10), slot 52 case 1)."""
    def __init__(self, defaults=True, where="insert", log=None):
        self.e = e = H31.new_emu(); self.s14 = []
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
        e.add_watch(0x1163f0, lambda em: self.s14.append((em.r(1), em.r(2))))
        self.log = []
        for a_ in (log or ()):
            e.add_watch(a_, lambda em, a_=a_: self.log.append((a_, em.r(1))))
        proc = e.malloc(0x200, "harness: processor scratch (r4)")
        e.w32(proc + 0x84, 64); e.w32(proc + 0x88, 0); e.w32(proc + 0x80, e.malloc(256, "harness: array"))
        r = H31.run_block(e, BUILD[where][0], BUILD[where][1], {0: 0x2b0, 4: proc, 7: 0x841564, 8: 0x841568})
        self.obj = self.o = r[6]; self.k = e.u32(self.o + 0x1b8)
        self.fx = {"insert_index": 1}; self.init_log = []
        if defaults: H7.Run.insert_init(self)
        self.default_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e; e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0 = e.vcall(self.o, 25, self.bl, self.br, N)[0]
        return r0, e.floats(self.bl, N), e.floats(self.br, N)

    def fractions(self, n=7):
        return [struct.unpack("<HH", self.e.rd(FRAC_TABLE + 4 * i, 4)) for i in range(n)]

    def state(self):
        e, k, o = self.e, self.k, self.o
        u = lambda a: e.u32(a); b = lambda a: e.rd(a, 1)[0]
        s = {"k.fs+4": u(k + 4), "k.block+8": u(k + 8), "k.rate+0xc": u(k + 0xc), "k.depth+0x10": u(k + 0x10),
             "k.phase+0x14": u(k + 0x14), "k.scale+0x18": u(k + 0x18), "k.fb_i+0x1c": u(k + 0x1c), "k.x20": u(k + 0x20),
             "k.ln+0xc0": u(k + 0xc0), "k.w+0xcc": u(k + 0xcc), "k.rL+0xd0": u(k + 0xd0), "k.rR+0xd4": u(k + 0xd4),
             "k.coef+0xe8": u(k + 0xe8), "k.ncoef+0xec": u(k + 0xec), "k.retrig+0xf0": b(k + 0xf0), "k.f1": b(k + 0xf1),
             "k.reset+0xf2": b(k + 0xf2), "k.yL+0xf4": u(k + 0xf4), "k.yR+0xf8": u(k + 0xf8), "k.x_fc+0xfc": u(k + 0xfc),
             "k.x100": u(k + 0x100), "k.x104": u(k + 0x104), "k.x108": u(k + 0x108), "k.fb+0x10c": u(k + 0x10c),
             "k.tol+0x110": u(k + 0x110),
             "k.dL+0xd8": tuple(struct.unpack("<%dI" % N, e.rd(u(k + 0xd8), 4 * N))),
             "k.dR+0xdc": tuple(struct.unpack("<%dI" % N, e.rd(u(k + 0xdc), 4 * N))),
             "k.gL+0xe0": tuple(struct.unpack("<%dI" % N, e.rd(u(k + 0xe0), 4 * N))),
             "k.gR+0xe4": tuple(struct.unpack("<%dI" % N, e.rd(u(k + 0xe4), 4 * N))),
             "o.dry+0x10": u(o + 0x10), "o.wet+0x14": u(o + 0x14), "o.mix+0x29c": u(o + 0x29c), "o.rate+0x2a0": u(o + 0x2a0),
             "o.sync+0x2a4": b(o + 0x2a4), "o.bpm+0x2a8": u(o + 0x2a8), "o.dirty+0x2ac": b(o + 0x2ac),
             "p.rate.last": u(o + 0x1bc + 0x24), "p.rate.cur": u(o + 0x1bc + 0x28), "p.sync.last": b(o + 0x218 + 0x24),
             "p.sync.cur": b(o + 0x218 + 0x25), "p.bpm.last": u(o + 0x240 + 0x24), "p.bpm.cur": u(o + 0x240 + 0x28)}
        q = k + 0x28; d = lambda a: struct.unpack("<Q", e.rd(q + a, 8))[0]
        for kk, off in (("amp+0", 0), ("off+4", 4), ("id+8", 8), ("wave+0xc", 0xc), ("freq+0x10", 0x10), ("ph+0x50", 0x50),
                        ("ph2+0x54", 0x54), ("c58", 0x58), ("c5c", 0x5c), ("sm0+0x60", 0x60), ("sm1+0x64", 0x64),
                        ("rs_cnt+0x68", 0x68), ("rs_per+0x6c", 0x6c), ("c+0x80", 0x80), ("P+0x84", 0x84)):
            s["osc." + kk] = u(q + off)
        for kk, off in (("inv_fs+0x18", 0x18), ("slope+0x20", 0x20), ("d28", 0x28), ("d30", 0x30), ("d38", 0x38),
                        ("d40", 0x40), ("d48", 0x48), ("hold+0x70", 0x70), ("smooth_off+0x78", 0x78)):
            s["osc." + kk] = d(off)
        return s

    def ring(self):
        e, k = self.e, self.k; ln = e.u32(k + 0xc0)
        return e.floats(e.u32(k + 0xc4), ln), e.floats(e.u32(k + 0xc8), ln)


def model_state(m):
    k = m.k
    s = {"k.fs+4": k.fs, "k.block+8": k.block, "k.rate+0xc": fb(k.rate), "k.depth+0x10": fb(k.depth),
         "k.phase+0x14": fb(k.phase), "k.scale+0x18": fb(k.scale), "k.fb_i+0x1c": fb(k.fb_i), "k.x20": fb(k.x20),
         "k.ln+0xc0": k.ln, "k.w+0xcc": k.w, "k.rL+0xd0": k.rL & 0xffffffff, "k.rR+0xd4": k.rR & 0xffffffff,
         "k.coef+0xe8": fb(k.coef), "k.ncoef+0xec": fb(k.ncoef), "k.retrig+0xf0": k.retrig, "k.f1": k.e1,
         "k.reset+0xf2": k.reset_flag, "k.yL+0xf4": fb(k.y[0]), "k.yR+0xf8": fb(k.y[1]), "k.x_fc+0xfc": fb(k.x_fc),
         "k.x100": 0, "k.x104": 0, "k.x108": 0, "k.fb+0x10c": fb(k.fb), "k.tol+0x110": fb(k.tol),
         "k.dL+0xd8": fl_bits(k.dL), "k.dR+0xdc": fl_bits(k.dR), "k.gL+0xe0": fl_bits(k.gL), "k.gR+0xe4": fl_bits(k.gR),
         "o.dry+0x10": fb(m.dry), "o.wet+0x14": fb(m.wet), "o.mix+0x29c": fb(m.mix), "o.rate+0x2a0": fb(m.rate_v),
         "o.sync+0x2a4": m.sync_v, "o.bpm+0x2a8": fb(m.bpm_v), "o.dirty+0x2ac": m.dirty,
         "p.rate.last": fb(m.p_rate.last), "p.rate.cur": fb(m.p_rate.cur), "p.sync.last": m.p_sync.last,
         "p.sync.cur": m.p_sync.cur, "p.bpm.last": fb(m.p_bpm.last), "p.bpm.cur": fb(m.p_bpm.cur)}
    for kk, v in H31.model_state(k.osc).items():
        if kk in ("r_off+0x88", "r_idx+0x8c"): continue
        s["osc." + kk] = v
    return s


def diff(se, sm): return [(k_, se[k_] if not isinstance(se[k_], tuple) else "buf", v if not isinstance(v, tuple) else "buf")
                          for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True):
    x = EmuFlanger(defaults=defaults)
    m = FL.Flanger()
    for idx, u in x.default_s14: m.set_param(idx, u2f(u))
    return x, m


def signal(kind, nblk, seed=11):
    g = random.Random(seed); L = []; R = []
    for k in range(N * nblk):
        if kind == "impulse":
            L.append(1.0 if k % 1000 == 0 else 0.0); R.append(-0.5 if k % 1000 == 333 else 0.0)
        elif kind == "sine":
            L.append(F(0.5 * math.sin(2 * math.pi * 440.0 * k / FS))); R.append(F(0.4 * math.cos(2 * math.pi * 1234.5 * k / FS)))
        else:
            L.append(F(g.uniform(-1, 1))); R.append(F(g.uniform(-1, 1)))
    return L, R


# settings: (name, [(idx, value)] applied after the Insert defaults and one priming block, bpm fed every block)
SETTINGS = [
    ("insert_defaults", [], 120.0),
    ("fb.99max_depth1_scale7_rate.3_ph.5", [(4, 1.0), (1, 1.0), (3, 1.0), (0, 0.3), (2, 0.5), (5, 0.7)], 120.0),
    ("fb0_small_delay_rate1Hz_ph180", [(4, 0.0), (1, 0.3), (3, 0.0), (0, 1.0), (2, 1.0)], 120.0),
    ("sync_bpm120_rate.5_fb.9", [(6, 1.0), (0, 0.5), (4, 0.9), (1, 0.8), (3, 0.3), (2, 0.4)], 120.0),
    ("sync_bpm87.5_rate1_fb.5_ph.25", [(6, 1.0), (0, 1.0), (4, 0.5), (2, 0.25), (1, 0.6)], 87.5),
    ("sync_bpm999_rate1_scale.5_fb.95", [(6, 1.0), (0, 1.0), (1, 1.0), (3, 0.5), (4, 0.95)], 999.0),
    ("depth0_constant_delay_fb.7", [(1, 0.0), (4, 0.7), (0, 0.8), (3, 0.6)], 120.0),
    ("rate0_.01Hz_depth1_scale1_fb.93_ph.75", [(0, 0.0), (1, 1.0), (3, 1.0), (4, 0.93), (2, 0.75)], 120.0),
    ("fb_negative_v-.5_clamps0", [(4, -0.5), (1, 0.6), (3, 0.2), (0, 0.45)], 120.0),
    ("fb_v1.5_clamps.99_scale.33_rate.77", [(4, 1.5), (1, 0.8), (3, 0.33), (0, 0.77), (2, 0.1)], 120.0),
    ("sync_bpm1_rate0_floor", [(6, 1.0), (0, 0.0), (1, 0.9), (4, 0.8), (3, 0.15)], 1.0),
]
EVENTS = [
    ("midrun_param_changes", [(1, 0.7), (3, 0.4), (4, 0.6)], 120.0,
     {90: [("p", 0, 0.62), ("p", 1, 0.2), ("p", 4, 0.98)], 100: [("p", 2, 0.9), ("p", 3, 1.0), ("p", 5, 0.5), ("p", 4, 0.1)],
      110: [("p", 6, 1.0), ("p", 0, 0.3)], 125: [("p", 6, 0.0), ("p", 4, 1.0)], 140: [("p", 1, 1.0), ("p", 0, 0.99), ("p", 3, 0.0)]}),
    ("midrun_retrigger_reset_mix_ks9_16_17", [(0, 0.2), (1, 0.9), (3, 0.6), (2, 0.7), (4, 0.85)], 120.0,
     {95: [("retrig",)], 105: [("reset",)], 112: [("p", 5, 0.25), ("retrig",)], 120: [("ks9", 0.42)], 130: [("ks16",)],
      140: [("ks17",), ("reset",)]}),
    ("tempo_changes_sync", [(6, 1.0), (0, 0.66), (1, 0.8), (3, 0.5), (4, 0.75)], 120.0,
     {100: [("bpm", 140.0)], 120: [("bpm", 61.25)], 135: [("bpm", 140.0)], 150: [("p", 0, 0.84), ("bpm", 300.0)]}),
    ("tempo_change_free_rate", [(0, 0.4), (1, 0.6), (4, 0.5)], 120.0, {100: [("bpm", 90.0)], 130: [("bpm", 90.0)]}),
]


def run_case(name, pre, bpm, events, kind, nblk, keep=False, mut=None, prime=True):
    x, m = new_pair()
    if mut: mut(m)
    L, R = signal(kind, nblk + 1)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 0, "bit_exact": 0, "max_abs_err": 0.0, "state_diffs": 0,
           "first": None, "nonzero": 0, "ret_diffs": 0, "peak": 0.0}
    outE = []
    blocks = [(L[0:N], R[0:N], [])] if prime else []
    pre_ops = [("p", i, v) for i, v in pre]
    for b in range(nblk):
        ops = (pre_ops if b == 0 else []) + list(events.get(b + 1, []))
        off = N * (b + 1) if prime else N * b
        blocks.append((L[off:off + N], R[off:off + N], ops))
    cur_bpm = bpm
    for bi, (bl, br, ops) in enumerate(blocks):
        for op in ops:
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "bpm": cur_bpm = op[1]
            elif op[0] == "retrig": x.e.vcall(x.o, 10); m.retrigger()
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
            elif op[0] == "ks9": x.e.vcall(x.k, 9, f2u(op[1])); m.k.set_x20(op[1])
            elif op[0] == "ks16": x.e.vcall(x.k, 16); m.k.e1 = 1
            elif op[0] == "ks17": x.e.vcall(x.k, 17); m.k.e1 = 0
        x.set(7, cur_bpm); m.set_param(7, cur_bpm)                       # processBlock tempo feed (F017) before the block
        r0, oL, oR = x.process(bl, br)
        mL, mR = list(bl), list(br); rm = m.process(mL, mR)
        if r0 != rm: res["ret_diffs"] += 1
        if prime and bi == 0: continue
        outE.append((oL, oR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["bit_exact"] += 1
            else:
                res["max_abs_err"] = max(res["max_abs_err"], abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf"))
                if res["first"] is None: res["first"] = ("block %d" % bi, a_, b_)
            if a_ != 0.0: res["nonzero"] += 1
            res["peak"] = max(res["peak"], abs(a_))
        dd = diff(x.state(), model_state(m))
        if dd:
            res["state_diffs"] += len(dd)
            if res["first"] is None: res["first"] = ("state after block %d" % bi, dd[:4])
    rL, rR = x.ring()
    res["ring_equal"] = [f2u(a_) for a_ in rL + rR] == [f2u(a_) for a_ in m.k.ring[0] + m.k.ring[1]]
    res["exact"] = res["bit_exact"] == res["samples"] and not res["state_diffs"] and not res["ret_diffs"] and res["ring_equal"]
    blob = b"".join(struct.pack("<64f", *l) + struct.pack("<64f", *r) for l, r in outE)
    res["emu_sha"] = sha(blob)[:16]
    if keep: res["_x"] = x; res["_m"] = m; res["_out"] = outE
    return res, blob


def mutants():
    """Deliberate model errors: each must make at least one comparison fail."""
    def m_fb_post(m):                       # feedback taken after the gain g(d)
        k = m.k; orig = k.process
        def pr(L, R):
            r = orig(L, R); k.y = [L[-1], R[-1]]; return r
        k.process = pr
    def m_fb_lin(m):                        # unquantised feedback 0.99 v
        k = m.k; orig = k.set_feedback
        def sf(v): r = orig(v); k.fb = F(min(max(0.99 * v, 0.0), 0.99)); return r
        k.set_feedback = sf
    def m_knee_scaled(m):                   # knee scaling with the oscillator amplitude instead of fixed 48 samples
        k = m.k
        k.gain = lambda d: F(F(F(1.0) + F(d * FL.K_GSLOPE)) - FL.K_GSUB) if d <= F(k.osc.amp + 4.0) else F(1.0)
    def m_rate_chorus(m):                   # Chorus rate law 0.1 rint(1 + 99 v)
        m.free_hz = C.Chorus.free_hz
    def m_nointerp(m):                      # no fractional interpolation (integer delay)
        k = m.k; orig = k.process
        def pr(L, R):
            k.osc_orig = k.osc.process
            def op(n):
                a, b = k.osc_orig(n); return [F(float(int(v))) for v in a], [F(float(int(v))) for v in b]
            k.osc.process = op; r = orig(L, R); k.osc.process = k.osc_orig; return r
        k.process = pr
    def m_ring(m): m.k.ln -= 64; m.k.ring = [[F(0.0)] * m.k.ln, [F(0.0)] * m.k.ln]
    def m_frac(m): m.fractions = [f_ for f_ in reversed(FL.SYNC_FRACTIONS)]
    def m_scale(m):
        k = m.k
        def ss(v): k.scale = F(0.1 + 7.0 * F(v)); k._apply_amp(); return k.scale
        k.set_scale = ss
    return [("feedback after gain", m_fb_post, [(4, 0.9), (1, 0.3), (3, 0.0)]),
            ("feedback unquantised 0.99v", m_fb_lin, [(4, 0.637)]),
            ("knee = amp + 4 (scales with depth)", m_knee_scaled, [(1, 1.0), (3, 1.0)]),
            ("Chorus rate law", m_rate_chorus, [(0, 0.37)]),
            ("integer delay (no interpolation)", m_nointerp, []),
            ("ring 7fs/1000 (no +block)", m_ring, [(1, 1.0), (3, 1.0)]),
            ("sync table reversed", m_frac, [(6, 1.0), (0, 0.2)]),
            ("depth scale 0.1+7v unquantised", m_scale, [(3, 0.337)])]


# ---------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H034"))
    ap.add_argument("--blocks", type=int, default=160)
    ap.add_argument("--mutants", action="store_true", help="only run the mutant check (deliberate model errors must be caught)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    if a.mutants:
        P("== mutants: each deliberate model error must make at least one comparison fail ==")
        caught = 0; ms = mutants()
        for nm_, fn, pre in ms:
            r_, _ = run_case("mut", pre, 120.0, {}, "noise", 60, mut=fn)
            caught += not r_["exact"]
            P("  %-36s caught %s (bit-exact %d/%d, state diffs %d)" % (nm_, not r_["exact"], r_["bit_exact"], r_["samples"], r_["state_diffs"]))
        check(caught == len(ms), "all %d mutants caught" % len(ms))
        P(); P("RESULT: %d failed checks" % len(fails))
        with open(os.path.join(a.out, "h034_mutants.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
        return 1 if fails else 0
    im = sp16img.Image()

    # ---------------- C1 parameter list ------------------------------------------------------------------------------
    P("== C1 Flanger parameters ==")
    x = EmuFlanger(defaults=False)
    st0 = x.state()
    vp = [(hex(off), hex(x.e.u32(x.o + off)), x.e.u32(x.o + off + 0x20)) for off in (0x1bc, 0x218, 0x240)]
    P("  parameter objects (offset, vptr, id +0x20; type +0x10 = %s): %s" % ([x.e.u32(x.o + off + 0x10) for off in (0x1bc, 0x218, 0x240)], vp))
    P("  ctor fields: mix +0x29c %r, rate copy +0x2a0 %r, sync +0x2a4 %d, bpm copy +0x2a8 %r, dirty +0x2ac %d; RATE last/cur %r/%r, "
      "BPM last/cur %r/%r" % (u2f(st0["o.mix+0x29c"]), u2f(st0["o.rate+0x2a0"]), st0["o.sync+0x2a4"], u2f(st0["o.bpm+0x2a8"]),
                              st0["o.dirty+0x2ac"], u2f(st0["p.rate.last"]), u2f(st0["p.rate.cur"]), u2f(st0["p.bpm.last"]),
                              u2f(st0["p.bpm.cur"])))
    P("  kernel ctor: rate %r Hz, depth %r, phase %r, scale %r, fb_i %r, fb %r, ring %d, osc amp %r off %r freq %r" %
      (u2f(st0["k.rate+0xc"]), u2f(st0["k.depth+0x10"]), u2f(st0["k.phase+0x14"]), u2f(st0["k.scale+0x18"]),
       u2f(st0["k.fb_i+0x1c"]), u2f(st0["k.fb+0x10c"]), st0["k.ln+0xc0"], u2f(st0["osc.amp+0"]), u2f(st0["osc.off+4"]),
       u2f(st0["osc.freq+0x10"])))
    dd = diff(st0, model_state(FL.Flanger()))
    check(not dd and vp == [("0x1bc", "0x840ac8", 0), ("0x218", "0x840b20", 6), ("0x240", "0x840ac8", 7)],
          "ctor state (Flanger + c_flanger + oscillator, %d fields) == model before any call; RATE id 0 / SYNC id 6 / BPM id 7%s"
          % (len(st0), "" if not dd else " %s" % dd[:5]))
    x = EmuFlanger(defaults=True)
    dflt = [(i_, u2f(u_), hex(u_)) for i_, u_ in x.default_s14]
    P("  Insert slot-52 case 1 slot-14 calls (index, value, bits): %s" % dflt)
    res["C1_insert_defaults"] = dflt
    st1 = x.state()
    P("  after defaults: kernel depth %r scale %r phase %r fb_i %r fb %r; osc amp %r off %r; mix %r" %
      (u2f(st1["k.depth+0x10"]), u2f(st1["k.scale+0x18"]), u2f(st1["k.phase+0x14"]), u2f(st1["k.fb_i+0x1c"]), u2f(st1["k.fb+0x10c"]),
       u2f(st1["osc.amp+0"]), u2f(st1["osc.off+4"]), u2f(st1["o.mix+0x29c"])))
    imap = {}
    for idx in range(0, 9):
        x, m = new_pair()
        s_before = x.state(); r0 = x.set(idx, 0.37); s_after = x.state()
        ch = sorted(k_ for k_ in s_after if s_after[k_] != s_before[k_])
        imap[idx] = {"ret": r0, "changed_immediately": ch}
        P("  slot14(%d, 0.37) -> ret %d, fields changed immediately: %s" % (idx, r0, ch))
    res["C1_index_map"] = imap
    check(imap[0]["changed_immediately"] == ["p.rate.cur"] and imap[8]["changed_immediately"] == [] and
          imap[5]["changed_immediately"] == ["o.mix+0x29c"] and "k.depth+0x10" in imap[1]["changed_immediately"] and
          "k.phase+0x14" in imap[2]["changed_immediately"] and "k.scale+0x18" in imap[3]["changed_immediately"] and
          "k.fb+0x10c" in imap[4]["changed_immediately"] and "k.fb_i+0x1c" in imap[4]["changed_immediately"] and
          imap[7]["changed_immediately"] == ["p.bpm.cur"] and all(v["ret"] == 0 for v in imap.values()),
          "index 0 RATE / 6 SYNC / 7 BPM stored in Parameter objects (next slot 25); 1 DEPTH, 2 PHASE, 3 DEPTH SCALE, 4 FEEDBACK "
          "go straight to the kernel (slots 5/6/7/8); 5 MIXRATIO plain store; 8 nothing; slot 14 always returns 0")
    x = EmuFlanger(defaults=False); x.set(0, 0.5); x.process([0.0] * N, [0.0] * N); r_a = u2f(x.state()["k.rate+0xc"])
    x = EmuFlanger(defaults=False); x.set(0, 0.5000001); x.process([0.0] * N, [0.0] * N); r_b = u2f(x.state()["k.rate+0xc"])
    P("  change detection: RATE 0.5 (= ctor last) before block 0 -> kernel rate %r (ctor 0.1 Hz kept); RATE 0.5000001 -> %r" % (r_a, r_b))
    check(r_a == F(0.1) and r_b == FL.Flanger.free_hz(0.5000001), "F026 change detection holds for RATE")
    res["C1_change_detection"] = [r_a, r_b]

    # ---------------- C2 formula sweeps --------------------------------------------------------------------------------
    P(); P("== C2 formula read-backs (emulated fields vs model after every call/block) ==")
    x = EmuFlanger(defaults=False); fr7 = x.fractions(8)
    P("  sync fraction table 0x%x (filled by .init_array 0x6cb20, block 0x6cbe0-0x6ce8c): %s (entry 7 belongs to the next table)" % (FRAC_TABLE, fr7))
    check(FL.SYNC_FRACTIONS == fr7[:7], "model fraction constants (flanger.SYNC_FRACTIONS) == emulated table entries 0..6")
    c2 = {}
    def sweep(name, setup, seq, fields, per_block):
        x, m = new_pair(); x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
        for idx, v in setup: x.set(idx, v); m.set_param(idx, v)
        x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
        rows = []; bad = 0
        for item in seq:
            if item[0] == "bpm": x.set(7, item[1]); m.set_param(7, item[1])
            elif item[0] == "k4": x.e.vcall(x.k, 4, f2u(item[1])); m.k.set_period_ms(item[1])
            elif item[0] == "k9": x.e.vcall(x.k, 9, f2u(item[1])); m.k.set_x20(item[1])
            else:
                idx, v = item; x.set(idx, v); m.set_param(idx, v)
            if per_block: x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
            se, sm = x.state(), model_state(m)
            dd = diff(se, sm); bad += bool(dd)
            rows.append([item] + [u2f(se[f_]) for f_ in fields] + ([dd[:3]] if dd else []))
        c2[name] = {"n": len(seq), "mismatch": bad, "rows": rows}
        P("  %-26s %3d values, model != emulation in %d" % (name, len(seq), bad))
        return rows
    vs = [0.0, 1e-4, 0.004, 0.005, 0.00505, 0.01, 0.0151, 0.05, 0.1, 0.1919, 0.25, 0.3333, 0.4, 0.49, 0.5, 0.5051, 0.6, 0.7, 0.75, 0.8,
          0.8838, 0.9, 0.95, 0.99, 0.995, 1.0]
    rows = sweep("rate_free", [], [(0, v) for v in vs], ["k.rate+0xc", "osc.freq+0x10", "osc.P+0x84"], True)
    P("    v -> kernel Hz: " + ", ".join("%g->%g" % (r_[0][1], r_[1]) for r_ in rows))
    bnd = []
    for kq in (1, 2, 50, 99, 100):
        c = (kq - 0.5) / 99.0
        for dv in (-1e-7, 0.0, 1e-7): bnd.append((0, F(c + dv)))
    sweep("rate_free_boundaries", [], bnd, ["k.rate+0xc"], True)
    seq = []
    for bpm in (120.0, 97.3, 999.0, 1.0):
        seq.append(("bpm", bpm)); seq += [(0, v) for v in vs]
        seq += [(0, F((kq + 0.5) / 6.0 + dv)) for kq in range(6) for dv in (-1e-7, 1e-7)]
    rows = sweep("rate_sync_4_tempi", [(6, 1.0)], seq, ["k.rate+0xc", "osc.freq+0x10"], True)
    per = len(vs) + 12 + 1
    P("    bpm 120: " + ", ".join("%g->%.6g" % (r_[0][1], r_[1]) for r_ in rows[1:1 + len(vs)][::3]))
    P("    bpm 999: " + ", ".join("%g->%.6g" % (r_[0][1], r_[1]) for r_ in rows[2 * per + 1:2 * per + 1 + len(vs)][::5]))
    P("    bpm 1  : " + ", ".join("%g->%.6g" % (r_[0][1], r_[1]) for r_ in rows[3 * per + 1:3 * per + 1 + len(vs)][::5]))
    dv_ = [0.0, 0.004, 0.005, 0.1, 0.333, 0.5, 0.505, 0.8, 0.99, 1.0, 1.2, -0.3]
    rows = sweep("depth_at_scale_ctor2", [], [(1, v) for v in dv_], ["k.depth+0x10", "osc.amp+0", "osc.off+4"], False)
    P("    depth v -> d (amp, offset) at scale 2.0: " + ", ".join("%g->%g (%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    rows = sweep("scale_at_depth100", [(1, 1.0)], [(3, v) for v in dv_ + [0.0072, 0.0073, 1e-9]], ["k.scale+0x18", "osc.amp+0", "osc.off+4"], False)
    P("    scale v -> s (amp, offset) at depth 100: " + ", ".join("%g->%g (%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    sweep("depth_at_scale.37", [(3, 0.37)], [(1, v) for v in dv_[:8]], ["k.depth+0x10", "osc.amp+0"], False)
    pv = [0.0, 0.002, 0.003, 0.1, 0.25, 0.5, 0.7, 0.9972, 1.0, 1.5, -0.2]
    rows = sweep("phase", [], [(2, v) for v in pv], ["k.phase+0x14", "osc.ph+0x50", "osc.ph2+0x54"], False)
    P("    phase v -> deg: " + ", ".join("%g->%g" % (r_[0][1], r_[1]) for r_ in rows))
    fv = [0.0, 0.004, 0.00505, 0.00506, 0.1, 0.25, 0.5, 0.5, 0.75, 0.9, 0.98, 0.9949, 0.995, 1.0, 1.01, 2.0, -0.001, -0.3, 0.33]
    fv += [F((kq + 0.5) / 99.0 + d_) for kq in (0, 49, 97, 98) for d_ in (-1e-7, 1e-7)]
    rows = sweep("feedback", [], [(4, v) for v in fv], ["k.fb_i+0x1c", "k.fb+0x10c"], False)
    P("    feedback v -> (index +0x1c, fb +0x10c): " + ", ".join("%.6g->(%g,%.8g)" % (r_[0][1], r_[1], r_[2]) for r_ in rows))
    mv = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5]
    rows = sweep("mixratio", [], [(5, v) for v in mv], ["o.mix+0x29c", "o.dry+0x10", "o.wet+0x14"], True)
    P("    mix v -> (mix, dry, wet) after a block: " + ", ".join("%g->(%g,%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    rows = sweep("kernel_slot4_periodMs", [], [("k4", v) for v in (50.0, 100.0, 250.0, 1000.0, 9999.0, 20000.0)],
                 ["k.rate+0xc", "osc.freq+0x10"], True)
    P("    kernel slot 4 (direct) ms -> (+0x0c, osc Hz): " + ", ".join("%g->(%g,%.6g)" % (r_[0][1], r_[1], r_[2]) for r_ in rows))
    rows = sweep("kernel_slot9", [], [("k9", v) for v in (0.0, 0.5, 1.0, 1.3, -0.2, 0.123)], ["k.x20", "k.x_fc+0xfc"], False)
    P("    kernel slot 9 (direct) v -> (+0x20, +0xfc): " + ", ".join("%g->(%g,%g)" % (r_[0][1], r_[1], r_[2]) for r_ in rows))
    res["C2"] = {k_: {"n": v["n"], "mismatch": v["mismatch"]} for k_, v in c2.items()}
    res["C2_rows"] = {k_: [[str(c_) for c_ in r_] for r_ in v["rows"]] for k_, v in c2.items()}
    check(all(v["mismatch"] == 0 for v in c2.values()),
          "all %d read-backs (kernel, oscillator, EffectBase fields) == model formulas" % sum(v["n"] for v in c2.values()))

    # ---------------- C4 end-to-end matrix ------------------------------------------------------------------------------
    P(); P("== C4 end-to-end: emulated slot 25 (with the per-block tempo feed) vs harness/models/flanger.py, %d blocks ==" % a.blocks)
    c4 = []
    def emit(r_, blob):
        c4.append(r_)
        with open(os.path.join(a.out, "emu_%s_%s.f32" % (r_["name"], r_["signal"])), "wb") as fh: fh.write(blob)
        P("  %-40s %-7s bit-exact %6d/%-6d max|err| %-8.3g state diffs %d ring %s nonzero %5d peak %.3f %s" %
          (r_["name"], r_["signal"], r_["bit_exact"], r_["samples"], r_["max_abs_err"], r_["state_diffs"], r_["ring_equal"],
           r_["nonzero"], r_["peak"], "" if r_["exact"] else "FIRST %s" % (r_["first"],)))
    for name, pre, bpm in SETTINGS:
        for kind in ("impulse", "sine", "noise"):
            emit(*run_case(name, pre, bpm, {}, kind, a.blocks))
    for name, pre, bpm, ev in EVENTS:
        for kind in ("sine", "noise"):
            emit(*run_case(name, pre, bpm, ev, kind, a.blocks))
    res["C4"] = c4
    check(all(r_["exact"] for r_ in c4) and all(r_["nonzero"] > 0 for r_ in c4),
          "model == emulation bit-exactly (outputs, return codes, %d state fields incl. oscillator/gain buffers after every block, "
          "final ring) in all %d runs" % (len(model_state(FL.Flanger())), len(c4)))
    P("  totals: %d runs, %d samples" % (len(c4), sum(r_["samples"] for r_ in c4)))

    # ---------------- C3 layout / vtables -------------------------------------------------------------------------------
    P(); P("== C3 vtables ==")
    vt = {nm: [hex(im.u32(base + 4 * i)) for i in range(n)] for nm, base, n in (("Flanger 0x8429a8", 0x8429a8, 32), ("c_flanger 0x841c10", 0x841c10, 20))}
    for nm, v in vt.items(): P("  %s: %s" % (nm, " ".join("%d:%s" % (i, s) for i, s in enumerate(v))))
    res["C3_vtables"] = vt
    ch_vt = [hex(im.u32(0x842920 + 4 * i)) for i in range(32)]
    P("  Flanger slots that differ from Chorus 0x842920: %s" % [i for i in range(32) if ch_vt[i] != vt["Flanger 0x8429a8"][i]])
    x, m = new_pair(); x.process([0.0] * N, [0.0] * N)
    P("  kernel/object fields after the first block: " + ", ".join("%s=%s" % (k_, hex(v)) for k_, v in x.state().items()
                                                                  if not k_.startswith("osc.") and not isinstance(v, tuple)))
    outs = []
    for flag in (False, True):
        x, _ = new_pair(); o = []
        L, R = signal("noise", 60)
        x.set(4, 0.8); x.set(1, 0.7)
        for b in range(60):
            if flag and b == 10: x.e.vcall(x.k, 16)
            if flag and b == 20: x.e.vcall(x.k, 9, f2u(0.77))
            x.set(7, 120.0); o.append(x.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
        outs.append(sha(repr(o).encode()))
    check(outs[0] == outs[1], "kernel byte +0xf1 (slots 16/17) and kernel slot 9 (+0x20/+0xfc) do not change the slot-19 output")

    # ---------------- C5 start-up / reset / retrigger -------------------------------------------------------------------
    P(); P("== C5 start-up, reset flag, retrigger, slot 27 ==")
    r_, _ = run_case("startup_no_prime", [], 120.0, {}, "noise", 3, keep=True, prime=False)
    b0 = r_["_out"][0]
    nz0 = sum(1 for v in b0[0] + b0[1] if v != 0.0)
    P("  first block after construction + Insert defaults (no priming): %d/128 non-zero output samples (bit-exact %s); "
      "first non-zero L sample index %d" % (nz0, r_["exact"], next(i for i, v in enumerate(b0[0]) if v != 0.0)))
    x, m = new_pair(); s_c = x.state(); x.set(7, 120.0); x.process([0.0] * N, [0.0] * N); s_1 = x.state()
    P("  reset flag +0xf2 after construction = %d, after block 0 = %d; osc counter c after block 0 = %r (no resetPhase in the reset path; "
      "the counter just advanced from its heap value 0)" % (s_c["k.reset+0xf2"], s_1["k.reset+0xf2"], u2f(s_1["osc.c+0x80"])))
    x, m = new_pair()
    for _ in range(5): x.set(7, 120.0); x.process([0.1] * N, [0.2] * N)
    c0 = x.state()["osc.c+0x80"]
    x.e.vcall(x.o, 10); s_r = x.state()
    x.set(7, 120.0); x.process([0.1] * N, [0.2] * N); s_r2 = x.state()
    P("  Flanger slot 10 0x1159e8 -> kernel +0xf0 = %d; next block -> +0xf0 = %d, oscillator counter %r -> %r (restart from phase 0)"
      % (s_r["k.retrig+0xf0"], s_r2["k.retrig+0xf0"], u2f(c0), u2f(s_r2["osc.c+0x80"])))
    x, m = new_pair()
    L, R = signal("noise", 20)
    for b in range(20): x.set(7, 120.0); x.process(L[N * b:N * b + N], R[N * b:N * b + N])
    s_b = x.state(); x.e.vcall(x.o, 27); s_a = x.state(); rl, rr = x.ring()
    P("  slot 27 0x1159b0 (reset): ring all zero %s, write index %d -> %d, y_prev L %r -> %r, fb %r -> %r"
      % (all(v == 0.0 for v in rl + rr), s_b["k.w+0xcc"], s_a["k.w+0xcc"], u2f(s_b["k.yL+0xf4"]), u2f(s_a["k.yL+0xf4"]),
         u2f(s_b["k.fb+0x10c"]), u2f(s_a["k.fb+0x10c"])))
    check(nz0 > 0 and r_["exact"] and s_c["k.reset+0xf2"] == 1 and s_1["k.reset+0xf2"] == 0 and s_r["k.retrig+0xf0"] == 1 and
          s_r2["k.retrig+0xf0"] == 0 and u2f(s_r2["osc.c+0x80"]) == 64.0 and all(v == 0.0 for v in rl + rr) and
          s_a["k.w+0xcc"] == s_b["k.w+0xcc"] and s_a["k.yL+0xf4"] == s_b["k.yL+0xf4"],
          "no start-up mute/fade (block 0 already has output); +0xf2 set by the ctor, consumed by block 0; slot 10 -> kernel slot 18 "
          "retrigger restarts the oscillator; slot 27 zeroes ring/buffers but keeps write index, y_prev and feedback")
    res["C5"] = {"block0_nonzero": nz0, "retrig": [s_r["k.retrig+0xf0"], s_r2["k.retrig+0xf0"]]}

    # ---------------- C6 alternatives -------------------------------------------------------------------------------------
    P(); P("== C6 alternative explanations ==")
    rr_ = c2["rate_free"]["rows"]
    alt_ch = sum(1 for r_ in rr_ if C.Chorus.free_hz(r_[0][1]) == r_[1])
    alt_lin = sum(1 for r_ in rr_ if F(0.01 + 0.99 * r_[0][1]) == r_[1])
    P("  rate free: 0.01 rint(1+99v) matches all; Chorus law 0.1 rint(1+99v) matches %d/%d; unquantised 0.01 + 0.99 v matches %d/%d"
      % (alt_ch, len(rr_), alt_lin, len(rr_)))
    fr_ = c2["feedback"]["rows"]
    lin_fb = sum(1 for r_ in fr_ if F(min(max(0.99 * r_[0][1], 0.0), 0.99)) == r_[2])
    P("  feedback: quantised rint(99v)*0.01 matches all; linear 0.99 v (clamped) matches %d/%d rows" % (lin_fb, len(fr_)))
    hs = []
    for mix in (0.0, 0.5, 1.0):
        x, _ = new_pair(); L, R = signal("noise", 40); o = []
        x.set(5, mix); x.set(4, 0.9)
        for b in range(40): x.set(7, 120.0); o.append(x.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
        hs.append(sha(repr(o).encode()))
    P("  slot-25 output hash for Mixratio 0 / 0.5 / 1: %s" % [h_[:12] for h_ in hs])
    # knee: g(d) read back from the emulated gain buffers over a run whose delays sweep 0.2..309 samples (depth 100, scale 7)
    xk, mk = new_pair(); L, R = signal("noise", 800); allg = []; kexact = True
    for i_, v_ in ((1, 1.0), (3, 1.0), (0, 0.99), (4, 0.5)): xk.set(i_, v_); mk.set_param(i_, v_)
    for b in range(800):
        xk.set(7, 120.0); mk.set_param(7, 120.0)
        _, oL, oR = xk.process(L[N * b:N * b + N], R[N * b:N * b + N]); mL, mR = L[N * b:N * b + N], R[N * b:N * b + N]
        mL, mR = list(mL), list(mR); mk.process(mL, mR); kexact &= fl_bits(oL + oR) == fl_bits(mL + mR)
        sk = xk.state()
        allg += list(zip([u2f(v) for v in sk["k.dL+0xd8"] + sk["k.dR+0xdc"]], [u2f(v) for v in sk["k.gL+0xe0"] + sk["k.gR+0xe4"]]))
    lo_ok = all(g == FL.Kernel.gain(d) for d, g in allg)
    below = [(d, g) for d, g in allg if d <= 48.0]
    near = sorted(allg, key=lambda t: abs(t[0] - 48.0))[:2]
    P("  knee probe (depth 100, scale 7, rate 0.99 Hz, fb 0.5, 800 blocks): delays %.3f..%.3f samples, %d of %d below the knee, "
      "g %.5f..%.5f; nearest the knee %s; all g == fixed-48 law: %s; output bit-exact: %s"
      % (min(d for d, _ in allg), max(d for d, _ in allg), len(below), len(allg), min(g for _, g in allg), max(g for _, g in allg),
         ["d %.4f g %.6f" % t for t in near], lo_ok, kexact))
    r_ = {"exact": kexact}
    check(alt_ch < len(rr_) and alt_lin < len(rr_) and lin_fb < len(fr_) and len(set(hs)) == 1 and lo_ok and r_["exact"],
          "refuted: Chorus rate law, unquantised rate, linear feedback, Mixratio applied in slot 25; knee fixed at 48 samples")
    def slot18_run(mix):
        x, m = new_pair(); e = x.e
        e.add_watch(0x106c88, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        L, R = signal("noise", 80); o = []; w = []
        x.set(5, mix); m.set_param(5, mix); x.set(4, 0.8); m.set_param(4, 0.8)
        bl = e.malloc(4 * N); br = e.malloc(4 * N)
        for b in range(80):
            e.set_floats(bl, L[N * b:N * b + N]); e.set_floats(br, R[N * b:N * b + N])
            s9 = e.vcall(x.o, 9)[0]
            if s9 == 0 and b == 0: e.vcall(x.o, 5, 0, 1); e.vcall(x.o, 7, 0)
            x.set(7, 120.0); m.set_param(7, 120.0)
            e.vcall(x.o, 18, bl, br, N)
            o.append((e.floats(bl, N), e.floats(br, N)))
            wl, wr = L[N * b:N * b + N], R[N * b:N * b + N]; wl, wr = list(wl), list(wr)
            if b == 0: m.reset()
            m.process(wl, wr); w.append((wl, wr))
        nb = 0; err_x = 0.0; ns = 0
        for b in range(60, 80):
            for ch in (0, 1):
                for i in range(N):
                    inp = (L if ch == 0 else R)[N * b + i]
                    ns += 1; nb += f2u(o[b][ch][i]) != f2u(F(inp + F(F(mix) * w[b][ch][i])))
                    err_x = max(err_x, abs(o[b][ch][i] - ((1 - mix) * inp + mix * w[b][ch][i])))
        return nb, ns, err_x
    s18 = {mix: slot18_run(mix) for mix in (0.0, 0.25, 1.0)}
    P("  slot 18 (gate opened by slots 5/7, 0x106c88 neutralised), blocks 60..79: samples != F(in + F(mix*wet)) / max|out - crossfade| = "
      + ", ".join("mix %g: %d/%d / %.3g" % (k_, v[0], v[1], v[2]) for k_, v in s18.items()))
    res["C6"] = {"rate": [alt_ch, alt_lin, len(rr_)], "fb_lin": [lin_fb, len(fr_)], "mix_hashes": hs,
                 "slot18": {str(k_): v for k_, v in s18.items()}}
    check(all(v[0] == 0 for v in s18.values()) and s18[0.25][2] > 1e-3,
          "slot 18 sums dry at unity: out = F(in + F(Mixratio * wet)) bit-exact (crossfade refuted)")

    # ---------------- C7 Master / Send context ----------------------------------------------------------------------------
    P(); P("== C7 Master / Send FX context ==")
    def stream(lo, hi):
        out = []
        for i in im.disasm(lo, hi):
            t = i.mnemonic + " " + i.op_str
            if "[pc, #" in i.op_str: t = i.mnemonic + " " + i.op_str.split(",")[0] + ", =0x%x" % im.u32(i.address + 8 + int(i.op_str.split("#")[1].rstrip("]"), 0))
            if i.mnemonic.startswith("b") and i.op_str.startswith("#"):
                tg = int(i.op_str[1:], 16)
                if lo <= tg <= hi: t = i.mnemonic + " <block+0x%x>" % (tg - lo)
            out.append(t)
        return out
    sites = [s for s, t, k in im.direct_calls() if t == KCTOR]
    P("  c_flanger ctor call sites: %s" % [hex(s) for s in sites])
    st = {w: stream(*BUILD[w]) for w in BUILD}
    for w in ("master", "send"):
        dl = [(i_, p_, q_) for i_, (p_, q_) in enumerate(zip(st["insert"], st[w])) if p_ != q_]
        P("  Insert 0x%x vs %s 0x%x: %d vs %d instructions, differing: %s" % (BUILD["insert"][0], w, BUILD[w][0], len(st["insert"]),
                                                                           len(st[w]), dl[:6]))
    xm = EmuFlanger(defaults=False, where="master"); xi = EmuFlanger(defaults=False)
    L, R = signal("noise", 100); hm = []; hi_ = []
    for xx, hh in ((xm, hm), (xi, hi_)):
        xx.set(0, 0.3); xx.set(1, 0.6); xx.set(3, 0.5); xx.set(4, 0.9)
        for b in range(100): xx.set(7, 120.0); hh.append(xx.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
    same = repr(hm) == repr(hi_)
    P("  Master-built Flanger (vptr 0x%x) vs Insert-built, 100 noise blocks: identical output %s" % (xm.e.u32(xm.o), same))
    res["C7"] = {"insert_eq_master": st["insert"] == st["master"], "insert_eq_send": st["insert"] == st["send"], "run_identical": same}
    check(st["insert"] == st["master"] == st["send"] and same and len(sites) == 3,
          "Master and Send processors build the identical Flanger object; the model applies there too (defaults/tempo feed not checked)")

    P(); P("RESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  failed: " + f_)
    with open(os.path.join(a.out, "h034_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    with open(os.path.join(a.out, "h034.json"), "w") as fh: json.dump(res, fh, indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
