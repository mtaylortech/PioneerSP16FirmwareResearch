#!/usr/bin/env python3
"""H041 — Ducker (Insert index 9; vtable 0x841098, new 0x598, ctor 0xf61a0, slot 25 0xf6ef4 -> update 0xf6630, attack 0xf69e4,
release 0xf6c6c, slot 26 0xf6188, slot 27 0xf69a8) end to end: trigger source -> parameters -> formulas -> envelope -> layout ->
bit-exact own-code model harness/models/ducker.py vs emulated slot 25.

Sections (criteria of kb/cycles/017.md):
  C1  key / trigger source: static call-site assertions (InsertFxProcessor processBlock case 9, InsertFxProcessor slot 54,
      InsertFxParameterManager slot 2, TriggerEraser slot 5, trigger table 0x1310c4/0x1310dc/0x1310e8/0x1310f4) and a processor-
      level emulation (real processBlock 0x116860 + real slot 54 + real manager slot 2 + real eraser) showing that the gain follows
      the trigger-table row selected by SOURCE, and not the own input, the own track row, other rows or the tempo.
  C2  parameter list: registrations logged in the real ctor, slot-14 index map, Insert slot-52 case-9 defaults, change detection.
  C3  formula sweeps: state read-back after slot 25 (Na, attack step, release step, curve bases, depth, sync tables) vs the model;
      libm oracle (pow, log10f).
  C4  envelope by emulation: durations, curve shape vs closed form, stereo link, input independence, retrigger behaviour.
  C5  layout: all state fields compared after every block (C6 runs); vtable slot roles.
  C6  end-to-end matrix: >= 8 settings x {impulse, sine, noise, steps, silence} x trigger patterns, >= 2 tempos, >= 120 blocks,
      + mid-run change runs + random-event runs.
  C7  start-up, slot 27 (reset), EffectBase slot 5, slot 10.
  C8  alternatives (external key vs internal tempo envelope vs self-key) and model mutants that must fail.
Outputs only to --out (default harness/out/H041/). Run: .venv/bin/python -B harness/H041_ducker_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, d2u, u2d, SP, PC, LR, SENTINEL       # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import ducker as M                                             # noqa: E402
from ducker import F                                           # noqa: E402

FS = 44100; N = 64
CTOR, SIZE, VT = 0xf61a0, 0x598, 0x841098
PARAM_OFF = {0: 0x1b8, 1: 0x214, 2: 0x270, 3: 0x2cc, 4: 0x328, 5: 0x384, 6: 0x3e0, 7: 0x408, 8: 0x464, 9: 0x48c, 10: 0x4e8}
LIN = (0, 1, 2, 3, 4, 5, 7); TOG = (6, 8); CHO = (9, 10)
PROC_BLOCK, PROC_SLOT54, MGR_SLOT2, ERASER_SLOT5 = 0x116860, 0x11684c, 0x1263f4, 0x130cac
VT_PROC = 0x842c10
TEMPO_FN = SENTINEL + 0x200


def sha(b): return hashlib.sha256(b).hexdigest()


class EmuDuck:
    """Ducker built by its real ctor (obj, 44100, 64), then (optionally) the H007 Insert init (slot 22, 0x106c7c(obj,1,10),
    InsertFxProcessor slot 52 case 9). Processed by calling slot 25 directly."""
    def __init__(self, defaults=True, log_regs=False, e=None):
        self.e = e = e or H31.new_emu()
        self.regs = []; self.s14 = []
        if log_regs:
            def cs(em):
                a_ = em.r(1); b_ = b""
                while len(b_) < 40:
                    c = em.rd(a_ + len(b_), 1)
                    if c == b"\0": break
                    b_ += c
                return b_.decode()
            def lin(em):
                sp = em.uc.reg_read(SP)
                self.regs.append({"kind": "LinearParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": u2f(em.r(3)), "max": u2f(em.u32(sp)), "default": u2f(em.u32(sp + 4))})
            def cho(em):
                sp = em.uc.reg_read(SP)
                self.regs.append({"kind": "LinearParameter(choice)", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": em.r(3), "max": em.u32(sp), "default": em.u32(sp + 4)})
            def tog(em):
                self.regs.append({"kind": "ToggleParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": None, "max": None, "default": None})
            e.add_watch(0xf1850, lin); e.add_watch(0xf1a00, cho); e.add_watch(0xf1800, tog)
        e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), em.r(2))))
        self.obj = self.o = e.malloc(SIZE, "new (harness: Ducker)")
        r0, _ = e.call(CTOR, self.o, FS, N)
        assert r0 == self.o and e.u32(self.o) == VT
        self.fx = {"insert_index": 9}; self.init_log = []
        if defaults:
            self.s14 = []
            H7.Run.insert_init(self)
            self.defaults_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def b(self, a): return self.e.rd(a, 1)[0]

    def state(self):
        o = self.o; u, i, b = self.u, self.i, self.b
        s = {"dry+0x10": u(o + 0x10), "wet+0x14": u(o + 0x14), "fs+0x90": u(o + 0x90),
             "attack+0x544": u(o + 0x544), "release+0x548": u(o + 0x548), "ca+0x54c": u(o + 0x54c), "cr+0x550": u(o + 0x550),
             "D+0x554": u(o + 0x554), "sync+0x558": b(o + 0x558), "bpm+0x55c": u(o + 0x55c), "trig+0x560": b(o + 0x560),
             "offset+0x564": i(o + 0x564), "dirty+0x568": b(o + 0x568), "g+0x56c": u(o + 0x56c), "inc_a+0x570": u(o + 0x570),
             "inc_r+0x574": u(o + 0x574), "cnt+0x578": i(o + 0x578), "a_done+0x57c": b(o + 0x57c), "r_done+0x57d": b(o + 0x57d),
             "x+0x580": u(o + 0x580), "pinc+0x584": u(o + 0x584), "pdec+0x588": u(o + 0x588), "Na+0x58c": i(o + 0x58c),
             "i+0x590": i(o + 0x590), "state+0x594": i(o + 0x594)}
        for k in LIN: s["p%d.last" % k] = u(o + PARAM_OFF[k] + 0x24); s["p%d.cur" % k] = u(o + PARAM_OFF[k] + 0x28)
        for k in TOG: s["p%d.last" % k] = b(o + PARAM_OFF[k] + 0x24); s["p%d.cur" % k] = b(o + PARAM_OFF[k] + 0x25)
        for k in CHO: s["p%d.cur" % k] = i(o + PARAM_OFF[k] + 0x44)
        return s


def model_state(m):
    fb = f2u
    s = {"dry+0x10": fb(m.dry), "wet+0x14": fb(m.wet), "fs+0x90": m.fs,
         "attack+0x544": fb(m.attack), "release+0x548": fb(m.release), "ca+0x54c": fb(m.ca), "cr+0x550": fb(m.cr),
         "D+0x554": fb(m.D), "sync+0x558": m.sync, "bpm+0x55c": fb(m.bpm), "trig+0x560": m.trig, "offset+0x564": m.offset,
         "dirty+0x568": m.dirty, "g+0x56c": fb(m.g), "inc_a+0x570": fb(m.inc_a), "inc_r+0x574": fb(m.inc_r), "cnt+0x578": m.cnt,
         "a_done+0x57c": m.a_done, "r_done+0x57d": m.r_done, "x+0x580": fb(m.x), "pinc+0x584": fb(m.pinc),
         "pdec+0x588": fb(m.pdec), "Na+0x58c": m.Na, "i+0x590": m.i, "state+0x594": m.state}
    for k in LIN: s["p%d.last" % k] = fb(m.p[k].last); s["p%d.cur" % k] = fb(m.p[k].cur)
    for k in TOG: s["p%d.last" % k] = m.p[k].last; s["p%d.cur" % k] = m.p[k].cur
    for k in CHO: s["p%d.cur" % k] = m.p[k].cur
    return s


class Model(M.Ducker):
    pass


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True, mut=None):
    x = EmuDuck(defaults=defaults)
    m = Model()
    if defaults: m.insert_defaults()
    if mut: mut(m)
    return x, m


def signal(kind, nblk, seed=11):
    n = nblk * N; rnd = random.Random(seed)
    if kind == "impulse":
        L = [F(1.0) if k % 397 == 0 else F(0.0) for k in range(n)]
        R = [F(-0.5) if k % 211 == 7 else F(0.0) for k in range(n)]
    elif kind == "sine":
        L = [F(0.8 * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(n)]
        R = [F(0.6 * math.sin(2 * math.pi * 440.0 * k / FS + 1.0)) for k in range(n)]
    elif kind == "dc":
        L = [F(1.0)] * n; R = [F(0.5)] * n
    elif kind == "noise":
        L = [F(rnd.uniform(-1.0, 1.0)) for _ in range(n)]
        R = [F(rnd.uniform(-1.0, 1.0)) for _ in range(n)]
    elif kind == "steps":
        lv = [-1.0, -40.0, -12.0, None, -3.0, -60.0, -20.0, -6.0]
        L = []; R = []
        for k in range(n):
            seg = lv[(k // (N * 15)) % len(lv)]
            a_ = 0.0 if seg is None else 10 ** (seg / 20)
            L.append(F(a_ * math.sin(2 * math.pi * 700.0 * k / FS))); R.append(F(a_ * 0.5))
    else:
        L = [F(0.0)] * n; R = [F(0.0)] * n
    return L, R


def trig_pattern(kind, nblk, seed=5):
    """{block: offset} — blocks in which the processor feeds TRIGGER = 1 (and OFFSET = offset)."""
    rr = random.Random(seed); ev = {}
    if kind == "beat":                        # one trigger every 37 blocks, varying offsets (incl. 0 and 64)
        offs = [0, 17, 63, 64, 5, 33, 1, 48]
        for k, b in enumerate(range(3, nblk, 37)): ev[b] = offs[k % len(offs)]
    elif kind == "dense":                      # random triggers incl. consecutive blocks (retrigger in attack / release)
        for b in range(2, nblk):
            if rr.random() < 0.12: ev[b] = rr.randint(0, 64)
    elif kind == "single":
        ev[4] = 21
    return ev


# settings: (name, [(idx, value)] after the Insert defaults, tempo per block (or list), blocks)
SETTINGS = [
    ("defaults_30ms_lin_300ms_D1", [], 120.0, 160),
    ("curved_A.01c.01_R.02c100_D.7", [(0, 0.01), (1, 0.0), (2, 0.02), (3, 1.0), (5, 0.7)], 120.0, 160),
    ("curved_Ac100_Rc.01_D.5", [(1, 1.0), (3, 0.0), (5, 0.5), (0, 0.004), (2, 0.004)], 120.0, 160),
    ("A0_Rmin1ms_c.25_c.8", [(0, 0.0), (2, 0.0), (1, 0.25), (3, 0.8)], 120.0, 160),
    ("sync120_A.5_R.3", [(6, 1.0), (0, 0.5), (2, 0.3)], 120.0, 160),
    ("sync87.5_A1_R.15_c.7_c.3", [(6, 1.0), (0, 1.0), (2, 0.15), (1, 0.7), (3, 0.3)], 87.5, 160),
    ("sync999_A.2_R.6_c.6_c.4", [(6, 1.0), (0, 0.2), (2, 0.6), (1, 0.6), (3, 0.4)], 999.0, 160),
    ("depth0", [(5, 0.0)], 120.0, 160),
    ("long_A1s_R8s_c.9_c.1_D.9", [(0, 1.0), (2, 1.0), (1, 0.9), (3, 0.1), (5, 0.9)], 133.0, 200),
    ("sync1bpm_A.05_R0_D.35", [(6, 1.0), (0, 0.05), (2, 0.0), (5, 0.35), (1, 0.45), (3, 0.55)], 1.0, 160),
]
SIGNALS = ("impulse", "sine", "noise", "steps", "silence")
PATTERNS = {"impulse": "beat", "sine": "dense", "noise": "beat", "steps": "dense", "silence": "dense"}
# event runs: (name, pre, tempo, blocks, {block: [ops]}, trigger pattern) ops: ("p", idx, v) | ("bpm", v) | ("reset",)
EVENTS = [
    ("param_and_tempo_changes", [(6, 1.0), (0, 0.4), (2, 0.4)], 120.0, 400,
     {40: [("bpm", 90.0)], 80: [("p", 1, 0.1)], 120: [("p", 3, 0.95)], 160: [("p", 5, 0.4)], 200: [("p", 6, 0.0)],
      240: [("p", 0, 0.002), ("p", 2, 0.01)], 280: [("bpm", 200.0), ("p", 6, 1.0)], 320: [("p", 4, 0.8)], 360: [("p", 5, 1.0)]},
     "dense"),
    ("resets_and_depth_changes", [(0, 0.02), (2, 0.05), (1, 0.3), (3, 0.7)], 120.0, 300,
     {50: [("reset",)], 60: [("p", 5, 0.0)], 61: [("p", 5, 1.0)], 100: [("reset",), ("p", 1, 0.5)], 150: [("bpm", 60.0)],
      200: [("p", 5, 1e-8)], 250: [("reset",), ("p", 5, 0.6)]}, "dense"),
]


def random_events(seed, nblk):
    rr = random.Random(seed); ev = {}
    for blk in range(3, nblk):
        if rr.random() < 0.15:
            ops = []
            for _ in range(rr.randint(1, 3)):
                idx = rr.choice([0, 1, 2, 3, 4, 5, 6])
                v = float(rr.randint(0, 1)) if idx == 6 else rr.choice([rr.random(), 0.0, 1.0, rr.random() * 0.05])
                ops.append(("p", idx, v))
            if rr.random() < 0.2: ops.append(("bpm", rr.choice([1.0, 60.0, 120.0, 174.5, 999.0, rr.uniform(1, 999)])))
            if rr.random() < 0.05: ops.append(("reset",))
            ev[blk] = ops
    return ev


def run_case(name, pre, tempo, kind, nblk, events=None, pattern=None, mut=None, sig=None, keep=False):
    x, m = new_pair(mut=mut)
    L, R = sig if sig is not None else signal(kind, nblk)
    trig = trig_pattern(pattern or PATTERNS.get(kind, "dense"), nblk)
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    bpm = tempo; maxerr = 0.0; nbit = 0; first_state = None; outb = bytearray(); ducked = 0; gmin = 1.0
    for blk in range(nblk):
        for op in (events or {}).get(blk, []):
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "bpm": bpm = op[1]
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
        fl = 1.0 if blk in trig else 0.0; of = float(trig.get(blk, 0))
        for idx, v in ((7, bpm), (8, fl), (9, of)): x.set(idx, v); m.set_param(idx, v)          # processBlock case-9 feed
        bL, bR = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
        eL, eR = x.process(bL, bR)
        mL, mR = m.process(bL, bR)
        for a_, b_ in zip(eL + eR, mL + mR):
            if f2u(a_) != f2u(b_):
                nbit += 1
                if not (math.isnan(a_) and math.isnan(b_)): maxerr = max(maxerr, abs(a_ - b_))
        for a_, i_ in zip(eL + eR, bL + bR):
            if a_ != i_: ducked += 1
        outb += struct.pack("<%df" % (2 * N), *(eL + eR))
        st = x.state(); gmin = min(gmin, u2f(st["g+0x56c"]))
        if first_state is None:
            dd = diff(st, model_state(m))
            if dd: first_state = (blk, [(k_, str(a_)[:40], str(b_)[:40]) for k_, a_, b_ in dd[:6]])
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 2 * N * nblk, "mismatched_samples": nbit, "max_abs_err": maxerr,
           "changed_samples": ducked, "first_state_diff": first_state, "min_gain": gmin, "triggers": len(trig)}
    return (res, bytes(outb), (x, m)) if keep else (res, bytes(outb))


# ------------------------------------------------------------------------------------------------------------------------
# C8 model mutants
def mut_linear_curves(m):                       # curve parameters ignored (always linear)
    m.curve_ignore = True
    oa, orl = Model._attack, Model._release
    def wrap(f):
        def g_(L, R, pos, n, m=m, f=f):
            ca, cr = m.ca, m.cr; m.ca = 1.0; m.cr = 1.0
            try: return f(m, L, R, pos, n)
            finally: m.ca, m.cr = ca, cr
        return g_
    m._attack = wrap(oa); m._release = wrap(orl)

def mut_per_sample(m):                          # control point every sample (no 11-sample interpolation)
    m.STEP = 1

def mut_step22(m):                              # control points every 22 samples
    m.STEP = 22

def mut_exp_release(m):                         # release = one-pole exponential recovery towards 1
    def rel(L, R, pos, n, m=m):
        k = F(m.pdec * 4.0)
        while n > 0:
            m.g = F(m.g + F(F(1.0 - m.g) * k)); L[pos] = F(L[pos] * m.g); R[pos] = F(R[pos] * m.g); pos += 1; n -= 1
            if m.g > 0.9999: m.g = 1.0; m.r_done = 1; m.x = 0.0; break
        return pos, n
    m._release = rel

def mut_retrig_from_top(m):                     # retrigger during release restarts the attack curve at x = 0
    def rp(m=m): m.trig = 0; m.x = 0.0
    m._retrigger_phase = rp

def mut_no_offset(m):                           # OFFSET ignored (duck starts at the block start)
    o = m.set_param
    def sp(idx, v, o=o): return o(idx, 0.0 if idx == 9 else v)
    m.set_param = sp

def mut_level_trigger(m):                       # TRIGGER as a level: every block with TRIGGER = 1 triggers
    o = m.set_param
    def sp(idx, v, o=o, m=m):
        r = o(idx, v)
        if idx == 8 and v >= 1.0: m.p[8].last = 0
        return r
    m.set_param = sp

def mut_per_channel(m):                         # right channel not ducked (per-channel / unlinked)
    op = m.process
    def pr(L, R, op=op):
        oL, _ = op(L, R); return oL, list(R)
    m.process = pr

def mut_hold_after_attack(m):                   # an extra hold of 11 samples at 1 - D before the release
    oa = Model._attack
    def a_(L, R, pos, n, m=m):
        r = oa(m, L, R, pos, n)
        if m.a_done: m.cnt = 12
        return r
    m._attack = a_


MUTANTS = [
    ("curves ignored (always linear)", mut_linear_curves, "curved_A.01c.01_R.02c100_D.7", "sine"),
    ("control point every sample", mut_per_sample, "curved_Ac100_Rc.01_D.5", "sine"),
    ("control points every 22 samples", mut_step22, "defaults_30ms_lin_300ms_D1", "sine"),
    ("exponential release", mut_exp_release, "defaults_30ms_lin_300ms_D1", "noise"),
    ("retrigger restarts at x = 0", mut_retrig_from_top, "curved_Ac100_Rc.01_D.5", "sine"),
    ("OFFSET ignored", mut_no_offset, "curved_Ac100_Rc.01_D.5", "noise"),
    ("TRIGGER level-sensitive", mut_level_trigger, "curved_Ac100_Rc.01_D.5", "sine"),
    ("unlinked (R not ducked)", mut_per_channel, "defaults_30ms_lin_300ms_D1", "sine"),
    ("hold after attack", mut_hold_after_attack, "curved_Ac100_Rc.01_D.5", "noise"),
]


def find_setting(name):
    for s in SETTINGS:
        if s[0] == name: return s
    raise KeyError(name)


# ------------------------------------------------------------------------------------------------------------------------
REGRESS = [
    ("H021", "H021_lofi_model.py", "h021", {"report": ("9273c853", "2677"), "json": ("f3316770", "d839"), "f32": ("86f8975a", "74a4")}),
    ("H023", "H023_mmf_model.py", "h023", {"report": ("9c33b389", "25eb"), "f32": ("5ccbbf43", "2baa")}),
    ("H026", "H026_peq_model.py", "h026", {"report": ("ed20422f", "93e9"), "json": ("fa2ebab6", "fbfd"), "f32": ("a3cb6985", "8f58")}),
    ("H028", "H028_phaser_model.py", "h028", {"report": ("1810c080", "9d227e"), "f32": ("cf14c39c", "5bd7")}),
    ("H031", "H031_osc_model.py", "h031", {"report": ("3fcde046", "d6ac"), "f32": ("2be562d2", "406f")}),
    ("H033", "H033_chorus_model.py", "h033", {"report": ("09032fa8", "6052"), "json": ("a04fce64", "c286"), "f32": ("ef54794e", "ce3d")}),
    ("H034", "H034_flanger_model.py", "h034", {"report": ("a9713642", "c019"), "json": ("861a3234", "913b"), "f32": ("b00781e5", "be46")}),
    ("H035", "H035_distortion_model.py", "h035", {"report": ("29a5598b", "b95b"), "json": ("7c0b94bc", "4c00"), "f32": ("c2ad7973", "82f0")}),
    ("H039", "H039_insert_delay_model.py", "h039", {"report": ("bde7d958", "43ca"), "json": ("dc699809", "893c"), "f32": ("cba3fdab", "4632")}),
    ("H040", "H040_compressor_model.py", "h040", {"report": ("88ae0286", "f8ba"), "json": ("c1581413", "4299"), "f32": ("716e131c", "f893")}),
]


def regress(out):
    import subprocess, glob
    procs = []
    for hid, script, pre, exp in REGRESS:
        d = os.path.join(out, "regress", hid); os.makedirs(d, exist_ok=True)
        lg = open(os.path.join(out, "regress", hid + ".log"), "w")
        procs.append((hid, pre, exp, d, subprocess.Popen([sys.executable, "-B", os.path.join(HERE, script), "--out", d],
                                                        stdout=lg, stderr=subprocess.STDOUT, cwd=os.path.dirname(HERE))))
    lines = []; ok_all = True
    for hid, pre, exp, d, p in procs:
        rc = p.wait(); got = {}
        rp = os.path.join(d, pre + "_report.txt"); jp = os.path.join(d, pre + ".json")
        if os.path.exists(rp): got["report"] = sha(open(rp, "rb").read())
        if os.path.exists(jp): got["json"] = sha(open(jp, "rb").read())
        fs_ = sorted(glob.glob(os.path.join(d, "*.f32")))
        got["f32"] = sha(b"".join(open(f_, "rb").read() for f_ in fs_))
        ok = all(k_ in got and got[k_].startswith(v[0]) and got[k_].endswith(v[1]) for k_, v in exp.items())
        ok_all &= ok
        lines.append("%s rc %d  %s  %s" % (hid, rc, "OK " if ok else "BAD", "  ".join("%s %s…%s" % (k_, got.get(k_, "-")[:8],
                                                                                         got.get(k_, "-")[-4:]) for k_ in exp)))
    txt = "\n".join(lines) + "\nREGRESSION: %s\n" % ("all recorded hashes reproduced" if ok_all else "MISMATCH")
    open(os.path.join(out, "h041_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok_all else 1


# ------------------------------------------------------------------------------------------------------------------------
class ProcRig:
    """A stand-in InsertFxProcessor (fields from F016/F017 and this cycle) around a real Ducker, run through the REAL processBlock
    0x116860; the trigger table (+0x98 {int *flag, int *offset, int count}) is written only by REAL code: InsertFxParameterManager
    slot 2 0x1263f4 -> InsertFxProcessor slot 54 0x11684c -> 0x1310c4; cleared by the REAL TriggerEraser slot 5 0x130cac.
    The processor-level dry copy 0xe8050 and post-mix 0xe8228 are neutralised (they do not touch the effect)."""
    ROWS = 17            # legacy stand-in (cycle 017). Cycle 039 / H050: the device table has 16 rows (ctor 0x130d54 called with 16
    REAL_TABLE = False   # @0x1bcf78/0x1bcf80); H050 sets ROWS = 16, REAL_TABLE = True to build it with the REAL ctor instead.

    def __init__(self, own_track, source, bpm=120.0, pre=()):
        self.x = x = EmuDuck(defaults=True); e = self.e = x.e
        for idx, v in pre: x.set(idx, v)
        x.set(10, float(source))
        self.bpm = bpm
        for a_ in (0xe8050, 0xe8228): e.add_watch(a_, lambda em: em.uc.reg_write(PC, em.uc.reg_read(LR)))
        def tempo(em):
            u = d2u(self.bpm); em.setr(0, u & 0xffffffff); em.setr(1, u >> 32)
        e.add_watch(TEMPO_FN, tempo)
        tvt = e.malloc(64); e.w32(tvt + 0x1c, TEMPO_FN); tob = e.malloc(8); e.w32(tob, tvt)
        if self.REAL_TABLE:
            self.table = t = e.malloc(12); e.call(0x130d54, t, self.ROWS)      # REAL TriggerTable ctor (new[] x2, zero, count)
            self.flags = e.u32(t); self.offs = e.u32(t + 4)
        else:
            self.table = t = e.malloc(12); self.flags = e.malloc(4 * self.ROWS); self.offs = e.malloc(4 * self.ROWS)
            e.w32(t, self.flags); e.w32(t + 4, self.offs); e.w32(t + 8, self.ROWS)
        self.proc = p = e.malloc(0x148); arr = e.malloc(40)
        for k in range(10): e.w32(arr + 4 * k, x.o if k == 9 else 0)
        e.w32(p, VT_PROC); e.w32(p + 0x80, arr); e.w32(p + 0x88, 10); e.w32(p + 0x94, tob); e.w32(p + 0x98, t)
        e.wr(p + 0x9d, b"\x01\x00"); e.w32(p + 0xa0, own_track); e.w32(p + 0xa4, 9); e.w32(p + 0xa8, 9)
        dd = e.malloc(8); e.w32(dd, e.malloc(256)); e.w32(dd + 4, e.malloc(256)); e.w32(p + 0xb8, dd)
        self.buf = e.malloc(0x100); ch = e.malloc(8); self.Lb = e.malloc(256); self.Rb = e.malloc(256)
        e.w32(ch, self.Lb); e.w32(ch + 4, self.Rb); e.w32(self.buf + 0xc, ch)
        self.mgr = {}
        for k in range(self.ROWS):                    # per-track stand-in processor + manager (only +0x98/+0xa0 and +0x1c used)
            pk = p if k == own_track else e.malloc(0x148)
            if k != own_track: e.w32(pk, VT_PROC); e.w32(pk + 0x98, t); e.w32(pk + 0xa0, k)
            mk = e.malloc(0x98); e.w32(mk + 0x1c, pk); self.mgr[k] = mk
        self.eraser = er = e.malloc(0x84); e.w32(er + 0x80, t)
        self.cap = {}
        e.add_watch(0x106ecc, lambda em: self.cap.__setitem__("in", (em.r(1), em.r(2), em.r(3), em.floats(em.r(1), em.r(3)),
                                                                      em.floats(em.r(2), em.r(3)))))
        e.add_watch(0x106ed0, lambda em: self.cap.__setitem__("out", (em.floats(self.cap["in"][0], self.cap["in"][2]),
                                                                       em.floats(self.cap["in"][1], self.cap["in"][2]))))

    def send(self, track, offset, etype):
        self.e.call(MGR_SLOT2, self.mgr[track], offset, etype)

    def block(self, L, R):
        e = self.e; self.cap = {}
        e.set_floats(self.Lb, L); e.set_floats(self.Rb, R)
        e.call(PROC_BLOCK, self.proc, self.buf)
        out = (e.floats(self.Lb, N), e.floats(self.Rb, N))
        e.call(ERASER_SLOT5, self.eraser)
        return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H041"))
    ap.add_argument("--skip-matrix", action="store_true")
    ap.add_argument("--regress", action="store_true", help="only re-run H021..H040 and compare their recorded hashes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)

    P("H041 Ducker end-to-end — target sha256 %s" % emu.SHA)
    im = sp16img.Image()
    def ins(a_):
        return ["%s %s" % (i_.mnemonic, i_.op_str) for i_ in im.md.disasm(im.data[im.off(a_):im.off(a_) + 4], a_)][0]

    # ---------------------------------------------------------------------------------------------------------- C1 static
    P("\n== C1 trigger source — static")
    vt = [im.u32(VT + 4 * k) for k in range(32)]
    P("  Ducker vtable 0x841098 slots 23..27: %s" % [hex(v) for v in vt[23:28]])
    sites = {0x116a04: "bl #0x1310dc", 0x116a40: "bl #0x1310e8", 0x1169e4: "ldr r3, [r3, #0x3c]", 0x1169d8: "mov r1, #0xa",
             0x116a0c: "mov r1, #8", 0x116a48: "mov r1, #9", 0x1169b8: "mov r1, #7", 0x1169f4: "ldr r0, [r4, #0x98]",
             0x116854: "ldr r0, [r0, #0x98]", 0x116858: "ldr r1, [r3, #0xa0]", 0x11685c: "b #0x1310c4",
             0x1263f4: "cmp r2, #0xb", 0x1263f8: "cmpne r2, #0xf", 0x12640c: "ldr r0, [r0, #0x1c]", 0x126414: "ldr r3, [r3, #0xd8]",
             0x130cac: "ldr r0, [r0, #0x80]", 0x130cb0: "b #0x1310f4", 0x1310d0: "str r0, [ip, r1, lsl #2]",
             0x1310d4: "str r2, [r3, r1, lsl #2]", 0x118b40: "str r5, [r4, #0xa0]", 0xf6948: "add r0, r4, #0x480",
             0xf6984: "bl #0xf0614", 0xf6934: "bl #0xf0814"}
    bad = {hex(k_): (ins(k_), v) for k_, v in sites.items() if ins(k_) != v}
    P("  %d instruction assertions (processBlock case 9, InsertFxProcessor slot 54, InsertFxParameterManager slot 2, TriggerEraser "
      "slot 5, table set/get, processor ctor +0xa0, Ducker update trigger branch): %s" % (len(sites), "all match" if not bad else bad))
    slot_ok = (im.u32(VT_PROC + 4 * 54) == PROC_SLOT54 and im.u32(0x84407c + 8) == MGR_SLOT2 and im.u32(0x844bf8 + 20) == ERASER_SLOT5)
    def rtti(vt_):
        return im.cstr(im.u32(im.u32(vt_ - 4) + 4), 60)
    P("  vtable homes: 0x11684c = %s slot 54; 0x1263f4 = %s slot 2; 0x130cac = %s slot 5" % (rtti(VT_PROC), rtti(0x84407c),
                                                                                            rtti(0x844bf8)))
    calls = im.direct_calls()
    callers = {t_: sorted(hex(s_) for s_, t__, k_ in calls if t__ == t_) for t_ in (0xf69b8, 0x1310c4, 0x1310dc, 0x1310e8, 0x1310f4)}
    P("  direct callers: %s" % callers)
    check(not bad and slot_ok and callers[0x1310c4] == ["0x11685c"] and callers[0x1310dc] == ["0x116a04"] and callers[0xf69b8] == [],
          "trigger path (static): InsertFxParameterManager slot 2 (ITriggerAndParameterReceiver) forwards event types 11 and 15 to "
          "InsertFxProcessor slot 54, which writes table[own track +0xa0] = (1, offset); processBlock case 9 reads row rint(SOURCE) "
          "into Ducker slot-14 TRIGGER (8) and OFFSET (9) every block; TriggerEraser slot 5 clears the table; the non-virtual "
          "Ducker helper 0xf69b8 has no caller (its code is inlined in update 0xf6630)")

    # ---------------------------------------------------------------------------------------------------------- C1 emulation
    P("\n== C1 trigger source — processor-level emulation (real processBlock / slot 54 / manager slot 2 / eraser)")
    rig = ProcRig(own_track=7, source=3, bpm=120.0, pre=[(0, 0.004), (2, 0.001)])
    # which event types set the table?
    tset = []
    for t_ in range(0, 24):
        rig.send(5, 9, t_); fl = rig.e.u32(rig.flags + 4 * 5); of = rig.e.u32(rig.offs + 4 * 5)
        if fl: tset.append((t_, of))
        rig.e.call(ERASER_SLOT5, rig.eraser)
    P("  manager slot 2 event types 0..23 that set table[5]: %s (flag 1, offset 9 each); eraser clears" % tset)
    check([t_ for t_, _ in tset] == [11, 15] and all(o_ == 9 for _, o_ in tset), "only event types 11 and 15 reach the trigger table")
    sched = {10: [(3, 17, 11)], 30: [(7, 5, 11)], 45: [(5, 0, 15)], 60: [(3, 40, 15)], 61: [(3, 2, 11)], 90: [(16, 1, 11)],
             100: [(3, 64, 11)], 101: [(3, 0, 12)], 130: [(3, 33, 15), (7, 1, 11)]}
    loud = set(range(70, 80))                     # loud burst on the own input (self-key test) without trigger
    tempos = {20: 60.0, 50: 240.0, 110: 120.0}    # tempo changes without trigger (internal-envelope test)
    Ls, Rs = signal("noise", 150, seed=3)
    m = Model(); m.insert_defaults(); m.set_param(0, 0.004); m.set_param(2, 0.001); m.set_param(10, 3.0)
    duck_blocks = []; nbit = 0; nsamp = 0; first_change = {}; cap_ok = 0
    for b in range(150):
        if b in tempos: rig.bpm = tempos[b]
        for tr, of, ty in sched.get(b, []): rig.send(tr, of, ty)
        row = (rig.e.u32(rig.flags + 4 * 3), rig.e.u32(rig.offs + 4 * 3))
        g = 4.0 if b in loud else 1.0
        bL = [F(g * v) for v in Ls[b * N:(b + 1) * N]]; bR = [F(g * v) for v in Rs[b * N:(b + 1) * N]]
        oL, oR = rig.block(bL, bR)
        cin = rig.cap.get("in"); cout = rig.cap.get("out")
        if b == 0: m.reset(); m.dry, m.wet = 0.0, 1.0       # activation in block 0: EffectBase slot 5 -> slot 27 (update), slot 26
        for idx, v in ((7, min(max(rig.bpm, 1.0), 999.0)), (8, float(row[0])), (9, float(row[1]))): m.set_param(idx, v)
        if cin is None: continue
        mL, mR = m.process(cin[3], cin[4]); cap_ok += 1
        for p_, q_ in zip(mL + mR, cout[0] + cout[1]):
            nsamp += 1
            if f2u(p_) != f2u(q_): nbit += 1
        ch = [i_ for i_ in range(N) if cout[0][i_] != cin[3][i_] or cout[1][i_] != cin[4][i_]]
        if ch: duck_blocks.append(b)
        if ch and (b - 1) not in duck_blocks: first_change[b] = ch[0]
    P("  own track 7, SOURCE 3; events (block: track, offset, type): %s" % {k_: v for k_, v in sched.items()})
    P("  blocks where slot 25 changed the signal: %s" % _ranges(duck_blocks))
    P("  first changed sample of each duck: %s" % first_change)
    P("  slot-25 output inside processBlock vs model fed with table row SOURCE: %d of %d samples differ (%d blocks)" % (nbit, nsamp, cap_ok))
    J["c1_proc"] = {"duck_blocks": duck_blocks, "first_change": first_change, "mism": nbit, "samples": nsamp}
    check(nbit == 0 and first_change == {10: 17, 60: 40, 101: 0, 130: 33} and
          all(b_ not in duck_blocks for b_ in list(range(30, 34)) + list(range(45, 49)) + list(range(70, 80)) + list(range(90, 94))
              + [20, 50, 110]),
          "the gain follows table row SOURCE (track 3): ducks start at block 10 sample 17, 60/40, 101/0 (offset 64 = whole block "
          "skipped), 130/33; "
          "triggers of the own track 7, of tracks 5 and 16, event type 12, a 4x louder own input and tempo changes do not duck; "
          "model fed with that row is bit-exact to the emulated slot 25")
    # SOURCE = own track: own-track triggers do duck (the table is shared, SOURCE selects the row)
    rig2 = ProcRig(own_track=7, source=7, bpm=120.0, pre=[(0, 0.004), (2, 0.001)])
    seen = []
    for b in range(40):
        if b == 10: rig2.send(7, 3, 11)
        if b == 20: rig2.send(3, 3, 11)
        rig2.block([F(0.5)] * N, [F(0.5)] * N)
        c_ = rig2.cap.get("out")
        if c_ and any(v != 0.5 for v in c_[0]): seen.append(b)
    P("  SOURCE = own track 7: slot 25 changed blocks %s (own-track trigger at 10, track-3 trigger at 20)" % _ranges(seen))
    check(seen and seen[0] == 10 and 20 not in seen, "with SOURCE = own track index the Ducker follows its own track's triggers")

    # ---------------------------------------------------------------------------------------------------------- C2
    P("\n== C2 parameters")
    x = EmuDuck(defaults=False, log_regs=True)
    for r_ in x.regs:
        P("  reg %-23s +0x%03x id %2d %-13s min %s max %s default %s" % (r_["kind"], r_["off"], r_["id"], r_["name"], r_["min"],
                                                                     r_["max"], r_["default"]))
    J["registrations"] = x.regs
    exp_regs = [("ATTACK", 0, 0x1b8), ("ATTACKCURVE", 1, 0x214), ("RELEASE", 2, 0x270), ("RELEASECURVE", 3, 0x2cc),
                ("NONE", 4, 0x328), ("DEPTH", 5, 0x384), ("SYNC", 6, 0x3e0), ("BPM", 7, 0x408), ("TRIGGER", 8, 0x464),
                ("OFFSET", 9, 0x48c), ("SOURCE", 10, 0x4e8)]
    check([(r_["name"], r_["id"], r_["off"]) for r_ in x.regs] == exp_regs and
          [r_["default"] for r_ in x.regs] == [0.5, 0.5, 0.5, 0.5, 0.0, 0.0, None, 120.0, None, 0, 0] and
          (x.regs[9]["max"], x.regs[10]["max"], x.regs[7]["min"], x.regs[7]["max"]) == (64, 16, 1.0, 999.0),
          "11 Parameter objects at +0x1b8 + 0x5c k (toggles 0x28 long): ATTACK 0, ATTACKCURVE 1, RELEASE 2, RELEASECURVE 3, NONE 4, "
          "DEPTH 5 (0..1), SYNC 6 / TRIGGER 8 (toggles), BPM 7 (1..999, 120), OFFSET 9 (choice 0..64), SOURCE 10 (choice 0..16)")
    imap = {}
    for idx in range(13):
        xx = EmuDuck(defaults=False); s0 = xx.e.rd(xx.o, SIZE); ret = xx.set(idx, 1.0 if idx in TOG else 0.37 if idx < 9 else 5.7)
        s1 = xx.e.rd(xx.o, SIZE)
        imap[idx] = {"ret": ret, "changed": ["+0x%x" % k for k in range(0, SIZE, 4) if s0[k:k + 4] != s1[k:k + 4]]}
    P("  slot14(i, v): " + "; ".join("%d->ret %d %s" % (k_, v["ret"], v["changed"]) for k_, v in imap.items()))
    J["slot14_map"] = imap
    exp_ch = {i_: ["+0x%x" % (PARAM_OFF[i_] + 0x28)] for i_ in LIN}
    exp_ch.update({6: ["+0x%x" % (PARAM_OFF[6] + 0x24)], 8: ["+0x%x" % (PARAM_OFF[8] + 0x24)],
                   9: ["+0x%x" % (PARAM_OFF[9] + 0x44)], 10: ["+0x%x" % (PARAM_OFF[10] + 0x44)]})
    check(all(imap[i_]["ret"] == 0 and imap[i_]["changed"] == exp_ch[i_] for i_ in range(11)) and
          all(imap[i_]["ret"] == 3 for i_ in (11, 12)),
          "slot 14 (EffectBase 0x105d24) only stores (floats +0x28, toggle byte +0x25, choices +0x44 = trunc(v)); nothing reaches the "
          "DSP state before the next slot 25; indices 11/12 return 3")
    xd = EmuDuck(defaults=True)
    dl = [(i_, u2f(v)) for i_, v in xd.defaults_s14]
    P("  Insert slot-52 case 9 defaults (slot-14 calls): %s" % dl)
    J["insert_defaults"] = dl
    xo = EmuDuck(defaults=False); xo.s14 = []
    cont = xo.e.malloc(0x100); arr = xo.e.malloc(40)
    for k in range(10): xo.e.w32(arr + 4 * k, xo.o if k == 9 else 0)
    xo.e.w32(cont + 0x80, arr); xo.e.w32(cont + 0x88, 10); xo.e.w32(cont + 0xa0, 5)
    xo.e.call(0x118a9c, cont, 9); src5 = [u2f(v) for i_, v in xo.s14 if i_ == 10]
    P("  slot 52 case 9 with stand-in processor track index +0xa0 = 5: SOURCE set to %s (reads processor +0xa0 @0x117888)" % src5)
    check([(i_, f2u(v)) for i_, v in dl] == [(i_, f2u(v)) for i_, v in M.INSERT_DEFAULTS] and src5 == [5.0] and
          ins(0x117888) == "ldr r2, [r4, #0xa0]",
          "Insert defaults: ATTACK 0.03 (30 ms), ATTACKCURVE 0.5, RELEASE 0.037488 (0.2999 s), RELEASECURVE 0.5, DEPTH 1, SYNC 0, "
          "SOURCE = the processor's own track index (+0xa0; 0 in the zero-filled stand-in) — NONE, BPM, TRIGGER, OFFSET not set")
    # change detection: value equal to the ctor 'last' is not applied (DEPTH default 0 -> set 0 then 0.3 then 0.3)
    xc = EmuDuck(defaults=False); xc.set(0, 0.5); xc.process([0.0] * N, [0.0] * N); st0 = xc.state()
    xc.set(0, 0.25); xc.process([0.0] * N, [0.0] * N); st1 = xc.state()
    P("  change detection: ATTACK 0.5 (= ctor last) -> Na %d (ctor 44, not recomputed); ATTACK 0.25 -> Na %d" % (st0["Na+0x58c"],
                                                                                                           st1["Na+0x58c"]))
    check(st0["Na+0x58c"] == 44 and st1["Na+0x58c"] == int(F(F(44100.0) * F(0.25))),
          "F026 change detection: a value equal to the stored last value is ignored; times are only computed when ATTACK/RELEASE/"
          "SYNC/BPM change (ctor leaves Na = 44, steps 1.0)")
    # NONE (index 4) has no effect
    r1, b1 = run_case("none0", [(4, 0.0)], 120.0, "noise", 60)
    r2, b2 = run_case("none1", [(4, 0.9)], 120.0, "noise", 60)
    check(b1 == b2 and r1["mismatched_samples"] == 0, "parameter 4 'NONE' is registered but never read (output identical for 0 / 0.9)")
    # slot 15 read-back of SOURCE as used by processBlock
    xs = EmuDuck(defaults=True); xs.set(10, 3.6); tmp = xs.e.malloc(4); xs.e.vcall(xs.o, 15, 10, tmp)
    P("  slot 15 (10) after SOURCE 3.6: %r (choice int 3 -> float)" % xs.e.f32(tmp))
    check(xs.e.f32(tmp) == 3.0, "SOURCE is an integer choice; processBlock reads it with slot 15 and rint()s it to the table row")

    # ---------------------------------------------------------------------------------------------------------- C3
    P("\n== C3 formula sweeps (state after slot 25 vs model)")
    sweeps = {0: [0.0, 1e-5, 2.2675e-5, 2.2676e-5, 0.001, 0.03, 0.123456, 0.5, 0.75, 1.0],
              2: [0.0, 1e-4, 1.25e-4, 1.26e-4, 0.0375, 0.2, 0.5, 0.9, 1.0],
              1: [0.0, 0.1, 0.25, 0.4999999, 0.5, 0.5000001, 0.75, 0.9, 1.0],
              3: [0.0, 0.2, 0.3333, 0.5, 0.6, 0.99, 1.0],
              5: [0.0, 1e-8, 1.2e-7, 0.25, 0.5, 0.999, 1.0],
              7: [1.0, 33.3, 60.0, 87.5, 120.0, 133.0, 174.25, 999.0]}
    sync_vals = [0.0, 0.5 / 127, F(0.5 / 127) * 1.0000001, 1.5 / 127, 10 / 127, 0.25, 0.5, 63.5 / 127, 0.9, 115 / 127, 1.0]
    FIELDS = ("Na+0x58c", "pinc+0x584", "pdec+0x588", "ca+0x54c", "cr+0x550", "D+0x554", "bpm+0x55c", "attack+0x544",
              "release+0x548", "sync+0x558")
    nb_ = 0; nt_ = 0; examples = []
    def probe(pre):
        nonlocal nb_, nt_
        xq, mq = new_pair()
        for i_, v_ in pre: xq.set(i_, v_); mq.set_param(i_, v_)
        xq.process([0.0] * N, [0.0] * N); mq.process([0.0] * N, [0.0] * N)
        se, sm = xq.state(), model_state(mq)
        bad_ = [k_ for k_ in FIELDS if se[k_] != sm[k_]]
        nt_ += 1; nb_ += bool(bad_)
        return se, bad_
    for idx, vals in sweeps.items():
        row = []
        for v_ in vals:
            pre = [(idx, v_)] + ([(0, 0.25)] if idx == 7 else []) + ([(6, 1.0)] if idx == 7 else [])
            se, bad_ = probe(pre)
            key = {0: "Na+0x58c", 2: "pdec+0x588", 1: "ca+0x54c", 3: "cr+0x550", 5: "D+0x554", 7: "Na+0x58c"}[idx]
            val = se[key] if key.startswith("Na") else u2f(se[key])
            row.append("%s->%s%s" % (v_, ("%d" % val) if key.startswith("Na") else ("%.7g" % val), "!" if bad_ else ""))
        P("  %-12s %s" % (M.NAMES[idx], ", ".join(row)))
    for nm_, idx in (("ATTACK sync", 0), ("RELEASE sync", 2)):
        row = []
        for v_ in sync_vals:
            se, bad_ = probe([(6, 1.0), (idx, v_)])
            val = se["Na+0x58c"] if idx == 0 else 1.0 / u2f(se["pdec+0x588"])
            row.append("%.6g->%s%s" % (v_, ("%d" % val) if idx == 0 else ("%.1f" % val), "!" if bad_ else ""))
        P("  %-12s %s" % (nm_, ", ".join(row)))
    P("  probes: %d, with any field mismatch: %d" % (nt_, nb_))
    check(nb_ == 0, "%d sweep probes (>= 5 values per parameter incl. rounding boundaries): Na = max(1, trunc(fs A)) (free: A = ATTACK "
          "s; sync: q TA[rint(127 v)], q = fs 0.25 60 / BPM), release step 1/max(fs/1000, Rl) (free: Rl = 8 fs RELEASE; sync q "
          "TR[rint(127 v)]), curve base c = (float)pow(100, 2v - 1), DEPTH stored as is — all bit-equal to the model" % nt_)
    ta_fw = [u2f(im.u32(0x841118 + 4 * k)) for k in range(128)]; tr_fw = [u2f(im.u32(0x841318 + 4 * k)) for k in range(128)]
    check([f2u(v) for v in ta_fw] == [f2u(v) for v in M.TA] and [f2u(v) for v in tr_fw] == [f2u(v) for v in M.TR],
          "sync tables: attack 0x841118 = 0..0.49 step 0.01, 0.5..0.98 step 0.02, 1..3.2 step 0.05, 3.3..4 step 0.1 (1/16 notes); "
          "release 0x841318 = 0.25..0.95 step 0.05, 1..3.9 step 0.1, 4..7.8 step 0.2, 8..15.75 step 0.25, 16..30 step 0.5, 31, 32 "
          "(model segments equal the 1.60 tables, 2 x 128 floats)")
    # libm oracle
    e0 = x.e; powa = e0.lib_exports["pow"][0]; l10 = e0.lib_exports["log10f"][0]
    rr = random.Random(7); pb = 0; lb = 0; npw = 0; nl = 0
    args = [(100.0, float(F(F(v + v) - 1.0))) for v in [k / 997 for k in range(998)]]
    args += [(float(F(rr.uniform(0.01, 100.0))), float(F(rr.random()))) for _ in range(1500)]
    for xa, ya in args:
        ux, uy = d2u(xa), d2u(ya); r0, r1 = e0.call(powa, ux & 0xffffffff, ux >> 32, uy & 0xffffffff, uy >> 32)
        npw += 1; pb += (u2d(r0 | (r1 << 32)) != M.cr_pow(xa, ya))
    largs = [F(rr.uniform(0.01, 100.0)) for _ in range(1500)] + [F(1.0 + rr.random() * 1e-5) for _ in range(300)] + \
            [F(2.0 ** rr.uniform(-20, 20)) for _ in range(700)] + [F(1.0), F(100.0), F(0.01), F(10.0)]
    l10_cr = 0
    for v_ in largs:
        got = u2f(e0.call(l10, f2u(v_))[0]); nl += 1; lb += (f2u(got) != f2u(M.log10f(v_)))
        l10_cr += (f2u(got) != f2u(F(math.log10(v_))))
    P("  libm: pow %d args, model cr_pow mismatches %d; log10f %d args, model port mismatches %d (host F(log10) would differ in %d)"
      % (npw, pb, nl, lb, l10_cr))
    J["libm"] = {"pow": [npw, pb], "log10f": [nl, lb, l10_cr]}
    check(pb == 0 and lb == 0, "libm oracle: 1.60 pow = correctly rounded (cr_pow), 1.60 log10f = the fdlibm float algorithm "
          "(own port in ducker.py)")

    # ---------------------------------------------------------------------------------------------------------- C4
    P("\n== C4 envelope by emulation (DC input, single trigger at block 4 offset 21)")
    shapes = []; NB4 = 260
    for nm_, pre in (("linear 30/300 ms", []), ("ATTACKCURVE 0 (c=.01) RELEASECURVE 1 (c=100)", [(1, 0.0), (3, 1.0), (0, 0.005), (2, 0.01)]),
                     ("ATTACKCURVE 1 RELEASECURVE 0", [(1, 1.0), (3, 0.0), (0, 0.005), (2, 0.01)]),
                     ("DEPTH 0.6", [(5, 0.6), (0, 0.002), (2, 0.004)])):
        res_, blob, (xq, mq) = run_case(nm_, pre, 120.0, "dc", NB4, pattern="single", keep=True)
        out = struct.unpack("<%df" % (len(blob) // 4), blob)
        g = []
        for b in range(NB4): g += out[b * 2 * N:b * 2 * N + N]
        t0 = 4 * N + 21
        imin = min(range(len(g)), key=lambda k: (g[k], k)); iend = max(k for k in range(len(g)) if g[k] != 1.0) + 1
        Na = xq.state()["Na+0x58c"]; Rl = 1.0 / u2f(xq.state()["pdec+0x588"])
        D = u2f(xq.state()["D+0x554"]); ca = u2f(xq.state()["ca+0x54c"]); cr = u2f(xq.state()["cr+0x550"])
        # closed form at the attack midpoint / release midpoint vs measured gain (interpolation error <= 1 control step)
        def att(xp): return (1 - D) + D * (1 - ((ca ** xp - 1) / (ca - 1) if abs(ca - 1) > 2 ** -23 else xp))
        def rel(yp): return (1 - D) + D * ((cr ** yp - 1) / (cr - 1) if abs(cr - 1) > 2 ** -23 else yp)
        mid_a = g[t0 + Na // 2]; mid_r = g[t0 + Na + int(Rl) // 2]
        sh = {"name": nm_, "first_change": next(k for k in range(len(g)) if g[k] != 1.0), "t0": t0, "attack_end": imin,
              "Na": Na, "release_end": iend, "Rl": Rl, "min": g[imin], "mid_attack": (mid_a, att(0.5)), "mid_release": (mid_r, rel(0.5))}
        shapes.append(sh)
        P("  %-44s duck starts %d (trigger %d), minimum %.6f at %d (t0+%d, Na %d), back to 1 at %d (t0+Na+%d, release %.1f); "
          "mid-attack g %.4f vs curve %.4f; mid-release g %.4f vs curve %.4f; R/L gain equal %s; model mism %d" %
          (nm_, sh["first_change"], t0, sh["min"], imin, imin - t0, Na, iend, iend - t0 - Na, Rl, mid_a, att(0.5), mid_r, rel(0.5),
           all(out[b * 2 * N + N + i_] == 0.5 * out[b * 2 * N + i_] or out[b * 2 * N + i_] == 1.0 for b in range(NB4) for i_ in range(N)),
           res_["mismatched_samples"]))
    J["shapes"] = shapes
    check(all(s["first_change"] == s["t0"] and abs(s["attack_end"] - s["t0"] - (s["Na"] - 1)) <= 1 and
              abs(s["release_end"] - s["t0"] - s["Na"] - s["Rl"]) <= 2 + 0.01 * s["Rl"] and abs(s["mid_attack"][0] - s["mid_attack"][1]) < 0.02 and
              abs(s["mid_release"][0] - s["mid_release"][1]) < 0.02 for s in shapes),
          "envelope: duck starts at the trigger sample (block start + OFFSET), falls to 1 - DEPTH in Na samples along "
          "(1-D)+D(1-(c^x-1)/(c-1)), then rises to 1 in max(1 ms, Rl) along (1-D)+D(c^y-1)/(c-1); no hold; L and R get the same gain")
    # input independence (self-key refutation at slot-25 level): gain trace identical for different inputs
    traces = []
    for kind in ("dc", "noise", "steps"):
        res_, blob, (xq, mq) = run_case("indep", [(1, 0.2), (3, 0.8)], 120.0, kind, 120, pattern="dense", keep=True)
        L_, R_ = signal(kind, 120); out = struct.unpack("<%df" % (len(blob) // 4), blob)
        gt = []
        for b in range(120):
            for i_ in range(N):
                inp = L_[b * N + i_]; o_ = out[b * 2 * N + i_]
                gt.append(None if inp == 0.0 else round(o_ / inp, 5))
        traces.append(gt)
    agree = sum(1 for k in range(len(traces[0])) if None not in (traces[0][k], traces[1][k], traces[2][k])
                and not (traces[0][k] == traces[1][k] == traces[2][k]))
    P("  gain trace out/in for DC, noise and level steps with the same trigger pattern: %d samples disagree (>1e-5)" % agree)
    check(agree == 0, "the gain does not depend on the audio input (no level detector: not self-keyed)")

    # ---------------------------------------------------------------------------------------------------------- C5 (vtable)
    P("\n== C5 layout / vtable")
    P("  vtable 0x841098: own slots 0 0xf7138 / 1 0xf7250 (dtors), 23 0xf6178 (returns 4), 24 0xf6180 (returns 0), 25 0xf6ef4 "
      "(process), 26 0xf6188 (dry 0 / wet 1), 27 0xf69a8 (= update 0xf6630, returns 0); 28-30 0xf7120/8/30 (return 0, shared with "
      "FxCompressor); other slots EffectBase defaults")
    check(vt[23:28] == [0xf6178, 0xf6180, 0xf6ef4, 0xf6188, 0xf69a8] and ins(0xf6178) == "mov r0, #4" and ins(0xf6180) == "mov r0, #0"
          and ins(0xf69ac) == "bl #0xf6630", "own vtable slots as listed")
    xc = EmuDuck(defaults=True); mc = Model(); mc.insert_defaults()
    check(diff(xc.state(), model_state(mc)) == [], "%d state fields equal after ctor + Insert init (compared after every block in C6)"
          % len(model_state(mc)))

    # ---------------------------------------------------------------------------------------------------------- C6
    hashes = {}
    if not a.skip_matrix:
        P("\n== C6 end-to-end matrix (slot 25 output, full state after every block)")
        results = []
        for nm, pre, tempo, nb in SETTINGS:
            for kind in SIGNALS:
                r_, blob = run_case(nm, pre, tempo, kind, nb)
                fn = "%s__%s.f32" % (nm, kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-30s %-7s %3d blk %2d trig  mism %d  max|err| %g  changed %5d  min g %-9.4g state %s" %
                  (nm, kind, nb, r_["triggers"], r_["mismatched_samples"], r_["max_abs_err"], r_["changed_samples"], r_["min_gain"],
                   "ok" if r_["first_state_diff"] is None else r_["first_state_diff"]))
        for nm, pre, tempo, nb, ev, pat in EVENTS:
            for kind in ("noise", "steps"):
                r_, blob = run_case(nm, pre, tempo, kind, nb, events=ev, pattern=pat)
                fn = "%s__%s.f32" % (nm, kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-30s %-7s %3d blk %2d trig  mism %d  max|err| %g  changed %5d  min g %-9.4g state %s" %
                  (nm, kind, nb, r_["triggers"], r_["mismatched_samples"], r_["max_abs_err"], r_["changed_samples"], r_["min_gain"],
                   "ok" if r_["first_state_diff"] is None else r_["first_state_diff"]))
        for sd in (1, 2, 3):
            ev = random_events(sd, 300)
            r_, blob = run_case("random_events_%d" % sd, [], 120.0, ("noise", "steps", "sine")[sd - 1], 300, events=ev, pattern="dense")
            fn = "random_events_%d.f32" % sd; open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
            results.append(r_)
            P("  %-30s %-7s %3d blk %2d trig  mism %d  max|err| %g  changed %5d  min g %-9.4g state %s (%d event blocks)" %
              (r_["name"], r_["signal"], 300, r_["triggers"], r_["mismatched_samples"], r_["max_abs_err"], r_["changed_samples"],
               r_["min_gain"], "ok" if r_["first_state_diff"] is None else r_["first_state_diff"], len(ev)))
        J["matrix"] = results
        tot = sum(r_["samples"] for r_ in results)
        check(all(r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None for r_ in results),
              "ducker.py bit-exact to emulated slot 25: %d runs, %d output samples, full state equal after every block" % (len(results), tot))
        check(len(SETTINGS) >= 8 and all(s[3] >= 120 for s in SETTINGS) and len(EVENTS) >= 2 and
              len(set(s[2] for s in SETTINGS if (6, 1.0) in s[1])) >= 2,
              "coverage: %d settings x %d signals (>= 120 blocks; ATTACK 0..1 s and sync, RELEASE 1 ms..8 s and sync, both curves "
              "0..1, DEPTH 0..1, tempos 1/87.5/120/999 BPM with sync), %d event runs + 3 random-event runs" % (len(SETTINGS), len(SIGNALS),
                                                                                                         len(EVENTS)))

    # ---------------------------------------------------------------------------------------------------------- C7
    P("\n== C7 start-up, reset, retrigger")
    xs, ms_ = new_pair()
    L_, R_ = signal("noise", 3)
    eL, eR = xs.process(L_[:N], R_[:N]); mL, mR = ms_.process(L_[:N], R_[:N])
    check(eL == L_[:N] and eR == R_[:N] and [f2u(v) for v in eL] == [f2u(v) for v in mL],
          "no start-up mute/fade inside slot 25: without a trigger the block passes unchanged (gain 1, state idle)")
    # reset in the middle of a duck
    for idx, v in ((0, 0.01), (2, 0.02)): xs.set(idx, v); ms_.set_param(idx, v)
    xs.set(8, 1.0); ms_.set_param(8, 1.0)
    for k in range(1, 3): xs.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); ms_.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
    s_before = xs.state(); xs.e.vcall(xs.o, 27); ms_.reset(); s27 = xs.state()
    dif27 = [k_ for k_ in s_before if s_before[k_] != s27[k_]]
    P("  slot 27 mid-duck (state %d, g %.4f): fields changed %s" % (s_before["state+0x594"], u2f(s_before["g+0x56c"]), dif27))
    check(diff(s27, model_state(ms_)) == [] and s27["state+0x594"] == s_before["state+0x594"] and s27["g+0x56c"] == s_before["g+0x56c"],
          "slot 27 (0xf69a8) only runs the parameter update 0xf6630: envelope state, phase and gain are kept (no reset of the duck)")
    calls = []
    for a_ in (0xf69a8, 0xf6630, 0xf6188, 0x10623c):
        xs.e.add_watch(a_, lambda em, a_=a_: calls.append(hex(a_)))
    xs.e.vcall(xs.o, 5, 0, 1); s5 = xs.state()
    P("  EffectBase slot 5 (activation) calls %s; dry/wet after %r/%r; state %d kept" % (calls, u2f(s5["dry+0x10"]), u2f(s5["wet+0x14"]),
                                                                                      s5["state+0x594"]))
    check("0xf69a8" in calls and "0xf6188" in calls and u2f(s5["dry+0x10"]) == 0.0 and u2f(s5["wet+0x14"]) == 1.0,
          "EffectBase slot 5 runs slot 27 (update) and slot 26 (dry 0, wet 1); the envelope is not cleared")
    s0 = xs.state(); r10 = xs.e.vcall(xs.o, 10)[0]; s1 = xs.state()
    check(r10 == 2 and s0 == s1, "slot 10 (retrigger) = EffectBase default 0x10594c: returns 2, changes nothing (no retrigger slot; "
          "the only trigger input is TRIGGER/OFFSET via slot 14)")
    xi = EmuDuck(defaults=False)
    P("  ctor without Insert init: dry/wet %r/%r (EffectBase), Na %d, steps %r/%r (times not computed until a time parameter "
      "changes)" % (u2f(xi.state()["dry+0x10"]), u2f(xi.state()["wet+0x14"]), xi.state()["Na+0x58c"], u2f(xi.state()["pinc+0x584"]),
                    u2f(xi.state()["pdec+0x588"])))

    # ---------------------------------------------------------------------------------------------------------- C8
    P("\n== C8 alternatives")
    # internal tempo-synced envelope: SYNC on, many tempo changes, no trigger -> gain stays 1
    xt, mt = new_pair(); xt.set(6, 1.0); xt.set(0, 0.5); changed = 0
    Lt, Rt = signal("noise", 200, seed=9)
    for b in range(200):
        xt.set(7, [1.0, 60.0, 120.0, 240.0, 999.0][b // 40]); xt.set(8, 0.0)
        oL, oR = xt.process(Lt[b * N:(b + 1) * N], Rt[b * N:(b + 1) * N])
        changed += sum(1 for p_, q_ in zip(oL + oR, Lt[b * N:(b + 1) * N] + Rt[b * N:(b + 1) * N]) if p_ != q_)
    P("  SYNC on, BPM 1/60/120/240/999, no trigger, 200 blocks: %d samples changed" % changed)
    check(changed == 0, "no internal tempo-synced envelope: without a trigger the gain stays 1 at every tempo (BPM only scales the "
          "ATTACK/RELEASE times when SYNC is on)")
    mres = []
    for nm_, fn_, case, kind in MUTANTS:
        s_ = find_setting(case)
        r_, _ = run_case(s_[0], s_[1], s_[2], kind, s_[3], mut=fn_)
        caught = r_["mismatched_samples"] > 0                  # output-based only
        mres.append((nm_, case, kind, r_["mismatched_samples"], r_["max_abs_err"], caught))
        P("  mutant %-34s on %-30s %-7s mism %6d  max|err| %-10.4g -> %s" % (nm_, case, kind, r_["mismatched_samples"],
                                                                           r_["max_abs_err"], "CAUGHT" if caught else "not caught"))
    J["mutants"] = mres
    check(all(m_[5] for m_ in mres), "all %d alternative models are refuted by emulation" % len(mres))

    # ---------------------------------------------------------------------------------------------------------- outputs
    P("\nRESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  FAILED: " + f_)
    cat = b"".join(open(os.path.join(a.out, k_), "rb").read() for k_ in sorted(hashes))
    J["f32_hashes"] = hashes; J["f32_concat_sha256"] = sha(cat) if hashes else None
    P("f32 files: %d, sorted concatenation sha256 %s" % (len(hashes), J["f32_concat_sha256"]))
    open(os.path.join(a.out, "h041_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h041.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


def _ranges(xs):
    out = []; s = None; p = None
    for v in xs:
        if s is None: s = p = v
        elif v == p + 1: p = v
        else: out.append((s, p)); s = p = v
    if s is not None: out.append((s, p))
    return out


if __name__ == "__main__":
    sys.exit(main())
