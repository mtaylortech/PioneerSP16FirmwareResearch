#!/usr/bin/env python3
"""H033 — Chorus (Insert index 0; vtable 0x842920, inline new 0x2b0; kernel c_chorus 0x841ba0, ctor 0xff008, slot 19 0xfe710)
end to end: parameters -> formulas -> state layout -> bit-exact own-code model harness/models/chorus.py vs the emulated
1.60 slot 25 0x115d70.

Sections (criteria of kb/cycles/010.md):
  C1  parameter list: registrations in the inline block, slot-14 index map (emulated), Insert slot-52 defaults, change detection.
  C2  formula sweeps: emulated read-back of kernel / oscillator / EffectBase fields vs the model after every slot-14 call or
      block (rate free >= 25 values, rate Sync >= 25 values x 3 tempi, depth / scale / phase / mixratio >= 7 values each),
      plus the sync fraction table.
  C3  layout: kernel and Chorus fields compared model vs emulation after every block; vtable slot list.
  C4  end-to-end matrix: >= 9 settings x {impulse train, sine, noise} x 160 blocks + mid-run change / retrigger / reset /
      tempo-change runs; slot-25 output bit-exact + state after every block.
  C5  retrigger (+0xe0 via Chorus slot 10 -> kernel slot 18), reset flag (+0xe2), kernel slots 16/17 (+0xe1) emulated.
  C6  alternatives: unquantised rate curve, deg/360 phase, crossfade dry/wet, linear 3.3 ms gain ramp, dry/wet in slot 25,
      slot-18 sum (EffectBase post-stage neutralised).
  C7  Master / Send context: inline construction blocks compared instruction by instruction and the Master-built object run.
Outputs only to --out (default harness/out/H033/). Run: .venv/bin/python -B harness/H033_chorus_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import EmuAbort, f2u, u2f, SP                          # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import chorus as C                                             # noqa: E402
from osc import F                                              # noqa: E402

FS = 44100; N = 64
FRAC_INIT = (0x6cbe0, 0x6ce8c)      # straight-line part of .init_array entry 0x6cb20 (fills the Fraction tables, r4 = 0xf61f18)
FRAC_TABLE = 0xf61f50               # Chorus sync fractions (read by 0x349800), 10 x {u16, u16}
CHORUS_SLOT14 = 0x116224
KSLOTS = {0xfeb10: "k3 setRate", 0xfed90: "k5 setDepth", 0xfec34: "k6 setPhase", 0xfeecc: "k7 setDepthScale",
          0x101090: "Osc_setFrequency", 0x1019d8: "Osc_setAmplitude", 0x1019e4: "Osc_setOffset", 0x1017d4: "Osc_setPhaseOffset",
          0x101440: "Osc_resetPhase"}


def sha(b): return hashlib.sha256(b).hexdigest()
def fb(x): return f2u(x)


class EmuChorus:
    """Chorus built by running the inline block of the 1.60 InsertFxProcessor ctor (0x118b50-0x118c68), after the sync
    fraction initialiser; then (optionally) the H007 Insert init (slot 22, 0x106c7c(obj,1,10), slot 52 case 0)."""
    def __init__(self, defaults=True, block=(0x118b50, 0x118c68), r0=None, log_calls=False, extra_regs=None):
        self.e = e = H31.new_emu(); self.log = []; self.s14 = []
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
        e.add_watch(CHORUS_SLOT14, lambda em: self.s14.append((em.r(1), em.r(2))))
        if log_calls:
            for a_, nm in KSLOTS.items():
                e.add_watch(a_, lambda em, nm=nm: self.log.append((nm, em.r(1))))
        proc = e.malloc(0x200, "harness: processor scratch (r4)")
        e.w32(proc + 0x84, 64); e.w32(proc + 0x88, 0); e.w32(proc + 0x80, e.malloc(256, "harness: array"))
        regs = {4: proc, 7: 0x841564, 8: 0x841568}
        if r0 is not None: regs[0] = r0
        for k_, v_ in (extra_regs or {}).items(): regs[k_] = v_(e, proc) if callable(v_) else v_
        r = H31.run_block(e, block[0], block[1], regs)
        self.obj = self.o = r[6]; self.k = e.u32(self.o + 0x1b8)
        self.fx = {"insert_index": 0}; self.init_log = []
        self.ctor_s14 = list(self.s14)
        if defaults: H7.Run.insert_init(self)
        self.default_s14 = self.s14[len(self.ctor_s14):]
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]
    def set_bits(self, idx, u): return self.e.vcall(self.o, 14, idx, u)[0]

    def process(self, L, R):
        e = self.e; e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0 = e.vcall(self.o, 25, self.bl, self.br, N)[0]
        return r0, e.floats(self.bl, N), e.floats(self.br, N)

    def fractions(self):
        return [struct.unpack("<HH", self.e.rd(FRAC_TABLE + 4 * i, 4)) for i in range(10)]

    def state(self):
        e, k, o = self.e, self.k, self.o
        u = lambda a: e.u32(a); b = lambda a: e.rd(a, 1)[0]
        s = {"k.fs+4": u(k + 4), "k.block+8": u(k + 8), "k.rate+0xc": u(k + 0xc), "k.depth+0x10": u(k + 0x10),
             "k.phase+0x14": u(k + 0x14), "k.scale+0x18": u(k + 0x18), "k.x1c": u(k + 0x1c), "k.x20": u(k + 0x20),
             "k.ln+0xc0": u(k + 0xc0), "k.w+0xcc": u(k + 0xcc), "k.coef+0xd8": u(k + 0xd8), "k.ncoef+0xdc": u(k + 0xdc),
             "k.retrig+0xe0": b(k + 0xe0), "k.e1": b(k + 0xe1), "k.reset+0xe2": b(k + 0xe2), "k.g+0xe8": u(k + 0xe8),
             "k.target+0xec": u(k + 0xec), "k.step+0xf0": u(k + 0xf0), "k.tol+0xf4": u(k + 0xf4), "k.full+0xf8": b(k + 0xf8),
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
         "k.phase+0x14": fb(k.phase), "k.scale+0x18": fb(k.scale), "k.x1c": fb(k.x1c), "k.x20": fb(k.x20),
         "k.ln+0xc0": k.ln, "k.w+0xcc": k.w, "k.coef+0xd8": fb(k.coef), "k.ncoef+0xdc": fb(k.ncoef),
         "k.retrig+0xe0": k.retrig, "k.e1": k.e1, "k.reset+0xe2": k.reset_flag, "k.g+0xe8": fb(k.g),
         "k.target+0xec": fb(k.target), "k.step+0xf0": fb(k.step), "k.tol+0xf4": fb(k.tol), "k.full+0xf8": k.full,
         "o.dry+0x10": fb(m.dry), "o.wet+0x14": fb(m.wet), "o.mix+0x29c": fb(m.mix), "o.rate+0x2a0": fb(m.rate_v),
         "o.sync+0x2a4": m.sync_v, "o.bpm+0x2a8": fb(m.bpm_v), "o.dirty+0x2ac": m.dirty,
         "p.rate.last": fb(m.p_rate.last), "p.rate.cur": fb(m.p_rate.cur), "p.sync.last": m.p_sync.last,
         "p.sync.cur": m.p_sync.cur, "p.bpm.last": fb(m.p_bpm.last), "p.bpm.cur": fb(m.p_bpm.cur)}
    for kk, v in H31.model_state(k.osc).items():
        if kk in ("r_off+0x88", "r_idx+0x8c"): continue
        s["osc." + kk] = v
    return s


def diff(se, sm): return [(k_, se[k_], v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True, fr=None):
    x = EmuChorus(defaults=defaults)
    m = C.Chorus(fractions=fr)              # fr None -> the model's own SYNC_FRACTIONS constants
    for idx, u in x.default_s14: m.set_param(idx, u2f(u))
    return x, m


# ---------------------------------------------------------------------------------------------------------------------
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


# settings: list of (idx, value) applied after the Insert defaults and one priming block; bpm = tempo fed every block.
SETTINGS = [
    ("insert_defaults", [], 120.0),
    ("rate10Hz_depth.5_scale1_ph180_mix.7", [(0, 1.0), (1, 0.5), (3, 1.0), (2, 1.0), (5, 0.7)], 120.0),
    ("extreme_depth_scale10_rate.37", [(0, 0.37), (1, 1.0), (3, 1.0), (2, 0.25)], 120.0),
    ("depth0_constant_delay", [(0, 0.8), (1, 0.0), (3, 0.5), (2, 0.6)], 120.0),
    ("sync_bpm120_rate.5", [(6, 1.0), (0, 0.5), (1, 0.8), (3, 0.6), (2, 0.4), (5, 0.3)], 120.0),
    ("sync_bpm87.5_rate.9", [(6, 1.0), (0, 0.9), (1, 0.9), (3, 0.9), (2, 0.15)], 87.5),
    ("sync_bpm200_rate0", [(6, 1.0), (0, 0.0), (1, 1.0), (3, 0.3)], 200.0),
    ("rate.05_ph.33_scale.25_depth.8", [(0, 0.05), (2, 0.33), (3, 0.25), (1, 0.8), (5, 1.0)], 120.0),
    ("rate0_ph.5_mix1", [(0, 0.0), (2, 0.5), (5, 1.0), (1, 0.66), (3, 0.77)], 120.0),
    ("sync_bpm999_rate1_clamp", [(6, 1.0), (0, 1.0), (1, 0.5), (3, 0.5)], 999.0),
]
# mid-run events: {block: [ops]}, op = ("p", idx, v) | ("bpm", v) | ("retrig",) | ("reset",) | ("ks16",) | ("ks17",)
EVENTS = [
    ("midrun_param_changes", [(1, 0.7), (3, 0.4)], 120.0,
     {90: [("p", 0, 0.62), ("p", 1, 0.2)], 100: [("p", 2, 0.9), ("p", 3, 1.0), ("p", 5, 0.5)], 110: [("p", 6, 1.0), ("p", 0, 0.3)],
      125: [("p", 6, 0.0)], 140: [("p", 1, 1.0), ("p", 0, 0.99)]}),
    ("midrun_retrigger_reset_mix", [(0, 0.2), (1, 0.9), (3, 0.6), (2, 0.7)], 120.0,
     {95: [("retrig",)], 105: [("reset",)], 112: [("p", 5, 0.25), ("retrig",)], 130: [("ks16",)], 140: [("ks17",), ("reset",)]}),
    ("tempo_changes_sync", [(6, 1.0), (0, 0.6), (1, 0.8), (3, 0.5)], 120.0,
     {100: [("bpm", 140.0)], 120: [("bpm", 61.25)], 135: [("bpm", 140.0)], 150: [("p", 0, 0.75), ("bpm", 300.0)]}),
    ("tempo_change_free_rate", [(0, 0.4), (1, 0.6)], 120.0, {100: [("bpm", 90.0)], 130: [("bpm", 90.0)]}),
]


def run_case(name, pre, bpm, events, kind, nblk, fr, keep=False, mut=None):
    x, m = new_pair(fr=fr)
    if mut: mut(m)
    L, R = signal(kind, nblk + 1)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 0, "bit_exact": 0, "max_abs_err": 0.0, "state_diffs": 0,
           "first": None, "nonzero": 0, "ret_diffs": 0}
    outE = []
    # priming block at the Insert defaults (F026: values equal to the ctor "last" values would otherwise not apply)
    blocks = [(L[0:N], R[0:N], [])]
    pre_ops = [("p", i, v) for i, v in pre]
    for b in range(nblk):
        ops = (pre_ops if b == 0 else []) + list(events.get(b + 1, []))
        blocks.append((L[N * (b + 1):N * (b + 2)], R[N * (b + 1):N * (b + 2)], ops))
    cur_bpm = bpm
    for bi, (bl, br, ops) in enumerate(blocks):
        for op in ops:
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "bpm": cur_bpm = op[1]
            elif op[0] == "retrig": x.e.vcall(x.o, 10); m.retrigger()
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
            elif op[0] == "ks16": x.e.vcall(x.k, 16); m.k.e1 = 1
            elif op[0] == "ks17": x.e.vcall(x.k, 17); m.k.e1 = 0
        x.set(7, cur_bpm); m.set_param(7, cur_bpm)                       # processBlock tempo feed (F017) before the block
        r0, oL, oR = x.process(bl, br)
        mL, mR = list(bl), list(br); rm = m.process(mL, mR)
        if r0 != rm: res["ret_diffs"] += 1
        if bi == 0: continue                                               # the priming block is not counted
        outE.append((oL, oR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["bit_exact"] += 1
            else:
                res["max_abs_err"] = max(res["max_abs_err"], abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf"))
                if res["first"] is None: res["first"] = ("block %d" % bi, a_, b_)
            if a_ != 0.0: res["nonzero"] += 1
        dd = diff(x.state(), model_state(m))
        if dd:
            res["state_diffs"] += len(dd)
            if res["first"] is None: res["first"] = ("state after block %d" % bi, dd[:4])
    rL, rR = x.ring()
    res["ring_equal"] = [f2u(a_) for a_ in rL + rR] == [f2u(a_) for a_ in m.k.ring[0] + m.k.ring[1]]
    res["exact"] = res["bit_exact"] == res["samples"] and not res["state_diffs"] and not res["ret_diffs"] and res["ring_equal"]
    blob = b"".join(struct.pack("<64f", *l) + struct.pack("<64f", *r) for l, r in outE)
    res["emu_sha"] = sha(blob)[:16]
    if keep: res["_x"] = x; res["_m"] = m
    return res, blob


# ---------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H033"))
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
        def m_nosnap(m): m.k.tol = F(-1e30)
        def m_ph360(m):
            orig = m.k.set_phase
            def sp(v):
                d = orig(v); m.k.osc.set_phase_offset(F(min(max(float(C.rint_idx(0, 181, v)), 0.0), 180.0) / 360.0)); return d
            m.k.set_phase = sp
        def m_rate_lin(m): m.free_hz = lambda v: F(0.1 + 9.9 * v)
        def m_crossfade(m):
            orig = m.process
            def pr(L, R): r = orig(L, R); m.dry = F(1.0 - m.mix); return r
            m.process = pr
        def m_ring(m): m.k.ln -= 64; m.k.ring = [[F(0.0)] * m.k.ln, [F(0.0)] * m.k.ln]
        def m_frac(m): m.fractions = [(f_[0], f_[1]) for f_ in reversed(C.SYNC_FRACTIONS)]
        def m_scale(m):
            m.k.set_scale = lambda v: (setattr(m.k, "scale", F(1.0 + 9.0 * F(v))), m.k._apply_amp(), m.k.scale)[2]
        cases = [("no gain snap", m_nosnap, [(1, 0.6)], {}), ("phase deg/360", m_ph360, [(2, 0.5)], {}),
                 ("rate 0.1+9.9v", m_rate_lin, [(0, 0.37)], {}), ("dry = 1 - mix", m_crossfade, [(5, 0.5)], {}),
                 ("ring fs/10 (no +block)", m_ring, [], {}), ("sync table reversed", m_frac, [(6, 1.0), (0, 0.2)], {}),
                 ("depth scale 1+9v", m_scale, [(3, 0.337)], {})]
        caught = 0
        for nm_, fn, pre, ev in cases:
            r_, _ = run_case("mut", pre, 120.0, ev, "noise", 90, None, mut=fn)
            caught += not r_["exact"]
            P("  %-24s caught %s (bit-exact %d/%d, state diffs %d)" % (nm_, not r_["exact"], r_["bit_exact"], r_["samples"], r_["state_diffs"]))
        check(caught == len(cases), "all %d mutants caught" % len(cases))
        P(); P("RESULT: %d failed checks" % len(fails))
        with open(os.path.join(a.out, "h033_mutants.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
        return 1 if fails else 0
    im = sp16img.Image()

    # ---------------- C1 parameter list ------------------------------------------------------------------------------
    P("== C1 Chorus parameters ==")
    x = EmuChorus(defaults=False, log_calls=True)
    fr = x.fractions()
    st0 = x.state()
    regs = []
    for off, kind in ((0x1bc, "LinearParameter"), (0x218, "ToggleParameter"), (0x240, "LinearParameter")):
        p = x.o + off
        regs.append({"off": hex(off), "vptr": hex(x.e.u32(p)), "kind": kind, "id": x.e.u32(p + 0xc) if kind else None,
                     "words": [hex(x.e.u32(p + 4 * i)) for i in range(0x0, 0x14)]})
    P("  parameter objects (vptr, first words): " + "; ".join("%s %s vptr %s" % (r_["off"], r_["kind"], r_["vptr"]) for r_ in regs))
    P("  ctor fields: mix +0x29c %r, rate copy +0x2a0 %r, sync +0x2a4 %d, bpm copy +0x2a8 %r, dirty +0x2ac %d; RATE last/cur %r/%r, "
      "BPM last/cur %r/%r" % (u2f(st0["o.mix+0x29c"]), u2f(st0["o.rate+0x2a0"]), st0["o.sync+0x2a4"], u2f(st0["o.bpm+0x2a8"]),
                              st0["o.dirty+0x2ac"], u2f(st0["p.rate.last"]), u2f(st0["p.rate.cur"]), u2f(st0["p.bpm.last"]),
                              u2f(st0["p.bpm.cur"])))
    m0 = C.Chorus()
    dd = diff(st0, model_state(m0))
    check(not dd, "ctor state (Chorus + c_chorus + oscillator, %d fields) == model before any call%s" % (len(st0), "" if not dd else " %s" % dd[:5]))
    # Insert defaults (slot 52 case 0)
    x = EmuChorus(defaults=True)
    dflt = [(i_, u2f(u_), hex(u_)) for i_, u_ in x.default_s14]
    P("  Insert slot-52 case 0 slot-14 calls (index, value, bits): %s" % dflt)
    res["C1_insert_defaults"] = dflt
    check([d_[0] for d_ in dflt] == [0, 1, 2, 3, 5, 6] and dflt[0][2] == hex(f2u(F(19.0 / 99.0))),
          "Insert defaults: RATE = 19/99 (-> i = 20, 2.0 Hz), DEPTH 1, PHASE 0, DEPTH SCALE 0, MIXRATIO 0, SYNC 0 (index 4/7 not set)")
    # slot-14 index map: which field each index changes, immediately
    imap = {}
    for idx in range(0, 9):
        x, m = new_pair()
        s_before = x.state(); r0 = x.set(idx, 0.37); s_after = x.state()
        ch = sorted(k_ for k_ in s_after if s_after[k_] != s_before[k_])
        imap[idx] = {"ret": r0, "changed_immediately": ch}
        P("  slot14(%d, 0.37) -> ret %d, fields changed immediately: %s" % (idx, r0, ch))
    res["C1_index_map"] = imap
    check(imap[0]["changed_immediately"] == ["p.rate.cur"] and imap[4]["changed_immediately"] == [] and
          imap[8]["changed_immediately"] == [] and imap[5]["changed_immediately"] == ["o.mix+0x29c"] and
          "k.depth+0x10" in imap[1]["changed_immediately"] and "osc.amp+0" in imap[1]["changed_immediately"] and
          "k.phase+0x14" in imap[2]["changed_immediately"] and "k.scale+0x18" in imap[3]["changed_immediately"] and
          imap[7]["changed_immediately"] == ["p.bpm.cur"] and all(v["ret"] == 0 for v in imap.values()),
          "index 0 RATE / 6 SYNC / 7 BPM are stored in Parameter objects (applied at the next slot 25); 1 DEPTH, 2 PHASE, 3 DEPTH SCALE "
          "go straight to the kernel (immediate); 5 MIXRATIO is a plain store; 4 and 8 do nothing; slot 14 always returns 0")
    # change detection: RATE equal to the ctor 'last' (0.5) before the first block is not applied
    x = EmuChorus(defaults=False); x.set(0, 0.5); x.process([0.0] * N, [0.0] * N); r_a = u2f(x.state()["k.rate+0xc"])
    x = EmuChorus(defaults=False); x.set(0, 0.5000001); x.process([0.0] * N, [0.0] * N); r_b = u2f(x.state()["k.rate+0xc"])
    P("  change detection: RATE 0.5 (= ctor last) before block 0 -> kernel rate %r (ctor 0.1 Hz kept); RATE 0.5000001 -> %r" % (r_a, r_b))
    check(r_a == F(0.1) and r_b == C.Chorus.free_hz(0.5000001), "F026 change detection holds for RATE (and the same object types for SYNC/BPM)")
    res["C1_change_detection"] = [r_a, r_b]

    # ---------------- C2 formula sweeps --------------------------------------------------------------------------------
    P(); P("== C2 formula read-backs (emulated fields vs model after every call/block) ==")
    P("  sync fraction table 0x%x (filled by .init_array 0x6cb20): %s" % (FRAC_TABLE, fr))
    check(C.SYNC_FRACTIONS == fr, "model fraction constants (chorus.SYNC_FRACTIONS) == emulated table")
    c2 = {}
    def sweep(name, setup, seq, fields, per_block):
        x, m = new_pair(); x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
        for idx, v in setup: x.set(idx, v); m.set_param(idx, v)
        x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
        rows = []; bad = 0
        for item in seq:
            if item[0] == "bpm": bpm = item[1]; x.set(7, bpm); m.set_param(7, bpm)
            else:
                idx, v = item; x.set(idx, v); m.set_param(idx, v)
            if per_block: x.process([0.0] * N, [0.0] * N); m.process([0.0] * N, [0.0] * N)
            se, sm = x.state(), model_state(m)
            dd = diff(se, sm); bad += bool(dd)
            rows.append([item] + [u2f(se[f_]) if isinstance(se[f_], int) and f_ not in ("o.sync+0x2a4",) else se[f_] for f_ in fields] +
                        ([dd[:3]] if dd else []))
        c2[name] = {"n": len(seq), "mismatch": bad, "rows": rows}
        P("  %-26s %3d values, model != emulation in %d" % (name, len(seq), bad))
        return rows
    vs = [0.0, 1e-4, 0.004, 0.005, 0.00505, 0.01, 0.0151, 0.05, 0.1, 0.1919, 0.25, 0.3333, 0.4, 0.49, 0.5, 0.5051, 0.6, 0.7, 0.75, 0.8,
          0.8838, 0.9, 0.95, 0.99, 0.995, 1.0]
    rows = sweep("rate_free", [], [(0, v) for v in vs], ["k.rate+0xc", "osc.freq+0x10", "osc.P+0x84"], True)
    P("    v -> kernel Hz (osc Hz, P): " + ", ".join("%g->%g" % (r_[0][1], r_[1]) for r_ in rows))
    seq = []
    for bpm in (120.0, 97.3, 999.0):
        seq.append(("bpm", bpm)); seq += [(0, v) for v in vs]
    rows = sweep("rate_sync_3_tempi", [(6, 1.0)], seq, ["k.rate+0xc", "osc.freq+0x10"], True)
    P("    bpm 120: " + ", ".join("%g->%.6g" % (r_[0][1], r_[1]) for r_ in rows[1:27]))
    P("    bpm 999: " + ", ".join("%g->%.6g" % (r_[0][1], r_[1]) for r_ in rows[-26:][::5]))
    dv = [0.0, 0.004, 0.005, 0.1, 0.333, 0.5, 0.505, 0.8, 0.99, 1.0, 1.2, -0.3]
    rows = sweep("depth_at_scale1", [(3, 0.0)], [(1, v) for v in dv], ["k.depth+0x10", "osc.amp+0", "osc.off+4"], False)
    P("    depth v -> d (amp, offset): " + ", ".join("%g->%g (%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    rows = sweep("scale_at_depth100", [(1, 1.0)], [(3, v) for v in dv], ["k.scale+0x18", "osc.amp+0", "osc.off+4"], False)
    P("    scale v -> s (amp, offset): " + ", ".join("%g->%g (%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    rows = sweep("depth_at_scale.37", [(3, 0.37)], [(1, v) for v in dv[:8]], ["k.depth+0x10", "osc.amp+0", "osc.off+4"], False)
    pv = [0.0, 0.002, 0.003, 0.1, 0.25, 0.5, 0.7, 0.9972, 1.0, 1.5, -0.2]
    rows = sweep("phase", [], [(2, v) for v in pv], ["k.phase+0x14", "osc.ph+0x50", "osc.ph2+0x54"], False)
    P("    phase v -> deg (cos 2pi ph, sin 2pi ph): " + ", ".join("%g->%g (%.5f,%.5f)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    mv = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5]
    rows = sweep("mixratio", [], [(5, v) for v in mv], ["o.mix+0x29c", "o.dry+0x10", "o.wet+0x14"], True)
    P("    mix v -> (mix, dry, wet) after a block: " + ", ".join("%g->(%g,%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    res["C2"] = {k_: {"n": v["n"], "mismatch": v["mismatch"]} for k_, v in c2.items()}
    res["C2_rows"] = {k_: [[str(c_) for c_ in r_] for r_ in v["rows"]] for k_, v in c2.items()}
    check(all(v["mismatch"] == 0 for v in c2.values()),
          "all %d read-backs (kernel, oscillator, EffectBase fields) == model formulas" % sum(v["n"] for v in c2.values()))

    # ---------------- C4 end-to-end matrix ------------------------------------------------------------------------------
    P(); P("== C4 end-to-end: emulated slot 25 (with the per-block tempo feed) vs harness/models/chorus.py, %d blocks ==" % a.blocks)
    c4 = []; blobs = []
    for name, pre, bpm in SETTINGS:
        for kind in ("impulse", "sine", "noise"):
            r_, blob = run_case(name, pre, bpm, {}, kind, a.blocks, None)
            c4.append(r_); blobs.append(blob)
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, kind)), "wb") as fh: fh.write(blob)
            P("  %-38s %-7s bit-exact %6d/%-6d max|err| %-8.3g state diffs %d ring %s nonzero %5d %s" %
              (name, kind, r_["bit_exact"], r_["samples"], r_["max_abs_err"], r_["state_diffs"], r_["ring_equal"], r_["nonzero"],
               "" if r_["exact"] else "FIRST %s" % (r_["first"],)))
    for name, pre, bpm, ev in EVENTS:
        for kind in ("sine", "noise"):
            r_, blob = run_case(name, pre, bpm, ev, kind, a.blocks, None)
            c4.append(r_); blobs.append(blob)
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, kind)), "wb") as fh: fh.write(blob)
            P("  %-38s %-7s bit-exact %6d/%-6d max|err| %-8.3g state diffs %d ring %s nonzero %5d %s" %
              (name, kind, r_["bit_exact"], r_["samples"], r_["max_abs_err"], r_["state_diffs"], r_["ring_equal"], r_["nonzero"],
               "" if r_["exact"] else "FIRST %s" % (r_["first"],)))
    res["C4"] = c4
    check(all(r_["exact"] for r_ in c4) and all(r_["nonzero"] > 0 for r_ in c4),
          "model == emulation bit-exactly (outputs, return codes, %d state fields after every block, final ring) in all %d runs"
          % (len(model_state(C.Chorus())), len(c4)))
    P("  totals: %d runs, %d samples" % (len(c4), sum(r_["samples"] for r_ in c4)))

    # ---------------- C3 layout / vtables -------------------------------------------------------------------------------
    P(); P("== C3 vtables ==")
    vt = {nm: [hex(im.u32(base + 4 * i)) for i in range(n)] for nm, base, n in (("Chorus 0x842920", 0x842920, 32), ("c_chorus 0x841ba0", 0x841ba0, 20))}
    for nm, v in vt.items(): P("  %s: %s" % (nm, " ".join("%d:%s" % (i, s) for i, s in enumerate(v))))
    res["C3_vtables"] = vt
    x, m = new_pair(); x.process([0.0] * N, [0.0] * N)
    P("  kernel/object fields after the first block: " + ", ".join("%s=%s" % (k_, hex(v) if isinstance(v, int) else v)
                                                                  for k_, v in x.state().items() if not k_.startswith("osc.")))

    # ---------------- C5 reset / retrigger -------------------------------------------------------------------------------
    P(); P("== C5 retrigger / reset flags ==")
    x, m = new_pair()
    for _ in range(3): x.set(7, 120.0); x.process([0.1] * N, [0.2] * N)
    c0 = x.state()["osc.c+0x80"]
    x.e.vcall(x.o, 10); s_r = x.state()
    x.set(7, 120.0); x.process([0.1] * N, [0.2] * N); s_r2 = x.state()
    P("  Chorus slot 10 0x115a4c -> kernel +0xe0 = %d; next block -> +0xe0 = %d, oscillator counter %r -> %r (restart from phase 0 + 64 samples)"
      % (s_r["k.retrig+0xe0"], s_r2["k.retrig+0xe0"], u2f(c0), u2f(s_r2["osc.c+0x80"])))
    x2 = EmuChorus(); st_ = x2.state()
    P("  reset flag +0xe2 after construction = %d; after the first block = %d (write index / ring / full flag cleared, resetPhase(0))"
      % (st_["k.reset+0xe2"], (x2.process([0.0] * N, [0.0] * N), x2.state()["k.reset+0xe2"])[1]))
    check(s_r["k.retrig+0xe0"] == 1 and s_r2["k.retrig+0xe0"] == 0 and st_["k.reset+0xe2"] == 1,
          "retrigger: Chorus slot 10 -> kernel slot 18 sets +0xe0, consumed by slot 19 (resetPhase(0)); +0xe2 is set only by the kernel ctor")
    # +0xe1 (kernel slots 16/17) has no effect on the output: same run with and without
    outs = []
    for flag in (False, True):
        x, _ = new_pair(); o = []
        L, R = signal("noise", 100)
        x.set(0, 0.3); x.set(1, 0.7)
        for b in range(100):
            if flag and b == 10: x.e.vcall(x.k, 16)
            x.set(7, 120.0); o.append(x.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
        outs.append(sha(repr(o).encode()))
    check(outs[0] == outs[1], "kernel byte +0xe1 (set by kernel slot 16, cleared by slot 17) does not change the slot-19 output")
    res["C5"] = {"retrig": [s_r["k.retrig+0xe0"], s_r2["k.retrig+0xe0"]], "e1_no_effect": outs[0] == outs[1]}

    # ---------------- C6 alternatives -------------------------------------------------------------------------------------
    P(); P("== C6 alternative explanations ==")
    rr = c2["rate_free"]["rows"]
    alt_lin = sum(1 for r_ in rr if F(0.1 + 9.9 * r_[0][1]) == r_[1])
    alt_q = sum(1 for r_ in rr if C.Chorus.free_hz(r_[0][1]) == r_[1])
    P("  rate free: quantised i*0.1 (i = rint(1+99v)) matches %d/%d; unquantised 0.1 + 9.9 v matches %d/%d" % (alt_q, len(rr), alt_lin, len(rr)))
    pr = c2["phase"]["rows"]
    k360 = 0
    for r_ in pr:
        v = r_[0][1]; deg = min(max(float(C.rint_idx(0, 181, v)), 0.0), 180.0)
        k360 += F(math.cos(2 * math.pi * deg / 360.0)) == r_[2]
    P("  phase: deg/380 cycles -> model matches all; deg/360 matches cos(2 pi ph) in %d/%d rows (only deg = 0)" % (k360, len(pr)))
    mr = c2["mixratio"]["rows"]
    xf = sum(1 for r_ in mr if r_[2] == F(1.0 - r_[0][1]))
    P("  dry/wet: dry stays 1.0 in %d/%d rows; crossfade (dry = 1 - mix) holds in %d/%d (only mix 0)" %
      (sum(1 for r_ in mr if r_[2] == 1.0), len(mr), xf, len(mr)))
    # mixratio not applied inside slot 25: same output for mix 0 / 0.5 / 1
    hs = []
    for mix in (0.0, 0.5, 1.0):
        x, _ = new_pair(); L, R = signal("noise", 90); o = []
        x.set(5, mix); x.set(1, 0.9)
        for b in range(90): x.set(7, 120.0); o.append(x.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
        hs.append(sha(repr(o).encode()))
    P("  slot-25 output hash for Mixratio 0 / 0.5 / 1: %s" % [h_[:12] for h_ in hs])
    # gain ramp: per-block exponential approach with snap vs a linear 3.3 ms (145.5-sample) ramp
    x, m = new_pair(); gs = []
    for b in range(90):
        x.set(7, 120.0); x.process([0.0] * N, [0.0] * N); gs.append(u2f(x.state()["k.g+0xe8"]))
    first = next(i for i, g in enumerate(gs) if g > 0)
    lin = [min(1.0, (64 * (i - first + 1) - (4474 - 64 * first) % 64) / (0.0033 * FS)) for i in range(first, len(gs))]
    P("  output gain g at the end of blocks %d..%d: %s; snapped to 1.0 at block %d; a linear 145.5-sample ramp would give %s"
      % (first, first + 7, ["%.4f" % g for g in gs[first:first + 8]], next(i for i, g in enumerate(gs) if g == 1.0),
         ["%.4f" % g for g in lin[:8]]))
    check(alt_q == len(rr) and alt_lin < len(rr) and k360 < len(pr) and xf < len(mr) and len(set(hs)) == 1 and
          gs[first + 2] != lin[2],
          "refuted: unquantised rate curve, phase deg/360, crossfade dry/wet, Mixratio applied in slot 25, linear 3.3 ms gain ramp")
    # slot-18 path with the EffectBase post-stage 0x106c88 neutralised: out = in * dry(1.0) + wet * slot-25 output ?
    def slot18_run(mix, neutral):
        x, m = new_pair(); e = x.e
        if neutral:
            def ret0(em):
                em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
            e.add_watch(0x106c88, ret0)
        L, R = signal("noise", 120); o = []; w = []
        x.set(5, mix); m.set_param(5, mix); x.set(1, 0.8); m.set_param(1, 0.8)
        bl = e.malloc(4 * N); br = e.malloc(4 * N)
        for b in range(120):
            e.set_floats(bl, L[N * b:N * b + N]); e.set_floats(br, R[N * b:N * b + N])
            s9 = e.vcall(x.o, 9)[0]
            if s9 == 0 and b == 0: e.vcall(x.o, 5, 0, 1); e.vcall(x.o, 7, 0)
            x.set(7, 120.0); m.set_param(7, 120.0)
            e.vcall(x.o, 18, bl, br, N)
            o.append((e.floats(bl, N), e.floats(br, N)))
            ml, mr_ = L[N * b:N * b + N], R[N * b:N * b + N]; wl, wr = list(ml), list(mr_)
            if b == 0: m.reset()                                     # slot 5 calls slot 27 (reset) before the first block
            m.process(wl, wr); w.append((wl, wr))
        err = 0.0; err_x = 0.0
        for b in range(100, 120):
            for ch in (0, 1):
                for i in range(N):
                    inp = (L if ch == 0 else R)[N * b + i]
                    err = max(err, abs(o[b][ch][i] - (inp + mix * w[b][ch][i])))
                    err_x = max(err_x, abs(o[b][ch][i] - ((1 - mix) * inp + mix * w[b][ch][i])))
        return err, err_x
    s18 = {}
    for mix in (0.0, 0.5, 1.0):
        s18[mix] = slot18_run(mix, True)
    P("  slot 18 (gate opened by slots 5/7, 0x106c88 neutralised), blocks 100..119: max|out - (in + mix*wet)| / max|out - ((1-mix) in + mix*wet)| = "
      + ", ".join("mix %g: %.3g / %.3g" % (k_, v[0], v[1]) for k_, v in s18.items()))
    res["C6"] = {"rate": [alt_q, alt_lin, len(rr)], "phase360": [k360, len(pr)], "crossfade": [xf, len(mr)], "mix_hashes": hs,
                 "gain": gs[first:first + 10], "slot18": {str(k_): v for k_, v in s18.items()}}
    check(all(v[0] < 1e-6 for v in s18.values()) and s18[0.5][1] > 1e-3,
          "slot 18 sums dry at unity: out = in + Mixratio * wet (crossfade refuted) after the gate has opened")

    # ---------------- C7 Master / Send context ----------------------------------------------------------------------------
    P(); P("== C7 Master / Send FX context ==")
    def stream(lo, hi):
        out = []
        for i in im.disasm(lo, hi):
            t = i.mnemonic + " " + i.op_str
            if "[pc, #" in i.op_str: t = i.mnemonic + " " + i.op_str.split(",")[0] + ", =0x%x" % im.u32(i.address + 8 + int(i.op_str.split("#")[1].rstrip("]"), 0))
            if i.mnemonic.startswith("b") and i.op_str.startswith("#"):
                tg = int(i.op_str[1:], 16)
                if lo <= tg <= hi: t = i.mnemonic + " <block+0x%x>" % (tg - lo)      # branch inside / to the end of the block
            out.append(t)
        return out
    ins = stream(0x118b5c, 0x118c68); mas = stream(0x114cfc, 0x114e08)
    sends = [s for s, t, k in im.direct_calls() if t == 0xff008 and 0x11bbe4 <= s < 0x11d000]
    snd = stream(sends[0] - 0xe4, sends[0] + 0x28) if sends else []
    for nm_, other in (("Master", mas), ("Send", snd)):
        dl = [(i_, p_, q_) for i_, (p_, q_) in enumerate(zip(ins, other)) if p_ != q_]
        P("  Insert vs %s differing instructions: %s" % (nm_, dl[:6]))
    P("  kernel ctor call sites: %s" % [hex(s) for s, t, k in im.direct_calls() if t == 0xff008])
    P("  Insert block 0x118b5c-0x118c68 (new(0x2b0) .. kernel install) vs Master block 0x114cfc-0x114e08: %d vs %d instructions, identical text (literals resolved): %s"
      % (len(ins), len(mas), ins == mas))
    P("  Send block ending at 0x%x: identical: %s" % (sends[0] + 0x28 if sends else 0, snd == ins))
    xm = EmuChorus(defaults=False, block=(0x114cf4, 0x114e08), extra_regs={3: lambda e_, p_: p_ + 0x100, 8: 0}); xi = EmuChorus(defaults=False)
    L, R = signal("noise", 100); hm = []; hi_ = []
    for xx, hh in ((xm, hm), (xi, hi_)):
        xx.set(0, 0.3); xx.set(1, 0.6); xx.set(3, 0.5)
        for b in range(100): xx.set(7, 120.0); hh.append(xx.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
    same = repr(hm) == repr(hi_)
    P("  Master-built Chorus (vptr 0x%x) vs Insert-built, 100 noise blocks: identical output %s" % (xm.e.u32(xm.o), same))
    res["C7"] = {"insert_eq_master": ins == mas, "insert_eq_send": snd == ins, "run_identical": same}
    check(ins == mas and snd == ins and same, "Master and Send processors build the identical Chorus object (same class, args, defaults "
          "of the object); the model applies there too (Master/Send slot-52 defaults and tempo feed not checked)")

    P(); P("RESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  failed: " + f_)
    with open(os.path.join(a.out, "h033_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    with open(os.path.join(a.out, "h033.json"), "w") as fh: json.dump(res, fh, indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
