#!/usr/bin/env python3
"""H028 — Phaser (Insert index 8 / Master index 9) algorithm reconstruction: 1.60 emulation (ctor 0x10d654, slot 25
0x10d630 called directly) vs. the own-code Python model harness/models/phaser.py.

Sections (criteria of kb/cycles/008.md):
  C1  parameters: registration calls 0xf1850 (float) / 0xf1800 (toggle) logged during the real ctor; ctor values; Insert
      defaults (slot 52 case 8, slot-14 call log); slot-14 index map; toggle semantics; tempo feed (static check of the
      InsertFxProcessor processBlock jump table).
  C2  signal flow: dynamic call order inside slot 25 (code hooks), per-block counts.
  C3  shared vs new blocks: vptrs / vtable-less sub-objects, callers of the oscillator block, RTTI `LFO` vtable.
  C4  parameter formulas: slot-14 readbacks at 7 values; tempo-synced period at 4 tempi x 12 divisions; libm tanf vs the
      fdlibm re-implementation.
  C5  state layout dump (emulated object + oscillator) and model-vs-emulation field comparison over several blocks.
  C6  model vs emulation matrix: impulse, 1 kHz sine, white noise (seed 1234), 64 blocks x 64 stereo, settings covering
      sync off/on, all divisions in a sweep, intermediate values, mid-run parameter and tempo changes, retrigger, reset.
  C7  alternatives: stage count, feedback tap, LFO shape, coefficient mapping, L/R offset, per-block vs interpolated coefficient.
Outputs only to --out (default harness/out/H028/). Run: .venv/bin/python -B harness/H028_phaser_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import emu                                                     # noqa: E402
from emu import Emu, EmuAbort, f2u, u2f, init_array, SP        # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import sp16img                                                 # noqa: E402
import phaser as M                                             # noqa: E402
import fdlibm_tanf as FT                                       # noqa: E402
from lofi import F                                             # noqa: E402

N = 64
FS = 44100
NBLK = 64
FX = dict(ctor=0x10d654, size=0x4f0, vtable=0x8422b8, ctor_args=(44100, 64), insert_index=8, static_init=[])
PARAM_OFF = [0x220 + 0x5c * k for k in range(6)] + [0x448, 0x470]     # Rate..Mixratio, Sync (toggle), BPM
REG_FUNCS = {0xf1850: "LinearParameter float ctor 0xf1850", 0xf1800: "ToggleParameter ctor 0xf1800"}
PLT_TANF = 0x104c8
FRAC_INIT = (0x6cbe0, 0x6ce8c)          # straight-line part of .init_array entry 0x6cb20 that fills the Fraction table 0xf61fcc
FLOW_SITES = {0x10d260: "Phaser_process", 0x10df00: "Phaser_updateRate", 0x101bdc: "Osc_process", 0x10cf40: "Phaser_kernel",
              0x101090: "Osc_setFrequency", 0x1017d4: "Osc_setPhaseOffset", 0x101440: "Osc_resetPhase", PLT_TANF: "tanf",
              0xff40: "powf", 0x10cb48: "Phaser_slot26_mix", 0x34c8c8: "freqIndexToHz", 0x34c240: "rateIndexToHz",
              0x34c2a8: "syncIndexToFraction"}


def sha(b): return hashlib.sha256(b).hexdigest()
def f32(x): return u2f(f2u(x))


def _guard_acq(e): g = e.r(0); e.setr(0, 0 if (e.u32(g) & 1) else 1)
def _guard_rel(e): e.w32(e.r(0), 1)


# ------------------------------------------------------------------------------------------------------------------------
class EmuPhaser:
    """1.60 Phaser built by its ctor + Insert init (H007 sequence), processed by calling slot 25 directly."""
    def __init__(self, defaults=True, log_regs=False, flow=False, log_slot14=False):
        self.fx = FX; self.e = e = Emu(); self.init_log = []; self.regs = []; self.trace = None; self.s14 = []
        # libm expf -> feholdexcept reads _rtld_global_ro._dl_hwcap (+0x40); provide HWCAP_VFP (0x40) as on the i.MX6
        e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))
        lm, base, _ = e._libs["libm.so.6"]
        for r in lm.dynamic_relocations:
            if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(base + r.address, 0x3d000000)
        # Fraction table (0xf61fcc, 12 x {u16 num, u16 den}) used by the sync rate: run its straight-line initialiser
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
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
        if log_slot14:
            e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), u2f(em.r(2)))))
        self.obj = self.o = e.malloc(FX["size"], "new (harness: Phaser object)")
        r0, _ = e.call(FX["ctor"], self.obj, *FX["ctor_args"])
        assert r0 == self.obj
        self.vptr = e.u32(self.obj)
        if defaults: H7.Run.insert_init(self)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set_param(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]
    def retrigger(self): return self.e.vcall(self.o, 10)[0]
    def reset(self): return self.e.vcall(self.o, 27)[0]

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

    def osc(self):
        q = self.u(self.o + 0x21c); f, d, i = self.f, self.d, self.i
        return {"amp+0": f(q), "off+4": f(q + 4), "id+8": i(q + 8), "wave+0xc": i(q + 0xc), "freq+0x10": f(q + 0x10),
                "inv_fs+0x18": d(q + 0x18), "slope+0x20": d(q + 0x20), "d40+0x40": d(q + 0x40), "ph+0x50": f(q + 0x50),
                "hold+0x70": d(q + 0x70), "smooth_off+0x78": d(q + 0x78), "c+0x80": f(q + 0x80), "P+0x84": f(q + 0x84),
                "cnt+0x68": self.u(q + 0x68), "fs+0x6c": self.u(q + 0x6c), "sm+0x58": f(q + 0x58), "sm+0x5c": f(q + 0x5c)}

    def state(self):
        o = self.o; f, i = self.f, self.i
        z = self.u(o + 0x1f4)
        s = {"fs+0x1b8": i(o + 0x1b8), "rc+0x1bc": i(o + 0x1bc), "t_lo+0x1c0": f(o + 0x1c0), "t_hi+0x1c4": f(o + 0x1c4),
             "a_lo+0x1c8": f(o + 0x1c8), "a_hi+0x1cc": f(o + 0x1cc), "g_hi+0x1d0": f(o + 0x1d0), "g_lo+0x1d4": f(o + 0x1d4),
             "cntA+0x1d8": i(o + 0x1d8), "cntF+0x1dc": i(o + 0x1dc), "fb+0x1e0": f(o + 0x1e0),
             "y+0x1e4": [f(o + 0x1e4), f(o + 0x1e8)], "a+0x1ec": [f(o + 0x1ec), f(o + 0x1f0)],
             "z[+0x1f4]": [self.e.f32(z + 4 * k) for k in range(12)], "pole+0x1f8": f(o + 0x1f8), "pole1+0x1fc": f(o + 0x1fc),
             "s+0x200": [f(o + 0x200), f(o + 0x204)], "lo_t+0x208": f(o + 0x208), "hi_t+0x20c": f(o + 0x20c),
             "copy+0x210": f(o + 0x210), "period_ms+0x4cc": f(o + 0x4cc), "width+0x4d0": f(o + 0x4d0),
             "phase+0x4d4": f(o + 0x4d4), "freq_v+0x4d8": f(o + 0x4d8), "fb_t+0x4dc": f(o + 0x4dc), "mix+0x4e0": f(o + 0x4e0),
             "sync+0x4e4": self.b(o + 0x4e4), "bpm+0x4e8": f(o + 0x4e8), "flag+0x4ec": self.b(o + 0x4ec),
             "dry+0x10": f(o + 0x10), "wet+0x14": f(o + 0x14)}
        s["osc"] = self.osc()
        s["params (last, cur)"] = {nm: ([f(o + off + 0x24), f(o + off + 0x28)] if k != 6 else [self.b(o + off + 0x24), self.b(o + off + 0x25)])
                                   for k, (nm, off) in enumerate(zip(M.PARAM_NAMES, PARAM_OFF))}
        return s

    def osc_buf(self, n):
        return self.e.floats(self.u(self.o + 0x214), n), self.e.floats(self.u(self.o + 0x218), n)


def model_state(m):
    s = {"fs+0x1b8": m.fs, "rc+0x1bc": m.rc, "t_lo+0x1c0": m.t_lo, "t_hi+0x1c4": m.t_hi, "a_lo+0x1c8": m.a_lo,
         "a_hi+0x1cc": m.a_hi, "g_hi+0x1d0": m.g_hi, "g_lo+0x1d4": m.g_lo, "cntA+0x1d8": m.cntA, "cntF+0x1dc": m.cntF,
         "fb+0x1e0": m.fb, "y+0x1e4": list(m.y), "a+0x1ec": list(m.a), "z[+0x1f4]": [m.z[k][j] for k in range(6) for j in (0, 1)],
         "pole+0x1f8": m.pole, "pole1+0x1fc": m.pole1, "s+0x200": list(m.s), "lo_t+0x208": m.lo_t, "hi_t+0x20c": m.hi_t,
         "copy+0x210": m.t_lo, "period_ms+0x4cc": m.period_ms, "width+0x4d0": m.width, "phase+0x4d4": m.phase_v,
         "freq_v+0x4d8": m.freq_v, "fb_t+0x4dc": m.fb_t, "mix+0x4e0": m.mix, "sync+0x4e4": m.sync, "bpm+0x4e8": m.bpm,
         "flag+0x4ec": m.reset_flag, "dry+0x10": m.dry, "wet+0x14": m.wet}
    q = m.lfo
    s["osc"] = {"amp+0": q.amp, "off+4": q.off, "wave+0xc": q.wave, "freq+0x10": q.freq, "inv_fs+0x18": q.inv_fs,
                "slope+0x20": q.slope, "d40+0x40": q.d40, "ph+0x50": q.ph, "hold+0x70": q.hold, "smooth_off+0x78": q.smooth_off,
                "c+0x80": q.c, "P+0x84": q.P}
    return s


def diff_state(se, sm):
    bad = []
    for k, v in sm.items():
        if k == "osc":
            for kk, vv in v.items():
                if se["osc"][kk] != vv: bad.append(("osc " + kk, se["osc"][kk], vv))
        elif k == "params (last, cur)": continue
        else:
            a = se[k]
            if isinstance(a, list):
                if any(f2u(f32(x)) != f2u(f32(y)) for x, y in zip(a, v)): bad.append((k, a, v))
            elif isinstance(a, float):
                if f2u(f32(a)) != f2u(f32(v)): bad.append((k, a, v))
            elif a != v: bad.append((k, a, v))
    n = sum(len(v) for k, v in sm.items() if k == "osc") + sum(1 for k in sm if k != "osc")
    return bad, n


# ------------------------------------------------------------------------------------------------------------------------
def signal(kind, nblk=NBLK, seed=1234):
    tot = N * nblk
    if kind == "impulse":
        L = [1.0 if k == 0 else 0.0 for k in range(tot)]; R = [-0.5 if k == 0 else 0.0 for k in range(tot)]
    elif kind == "impulses":                                       # an impulse every 16 blocks (probes the moving notches)
        L = [0.9 if k % (16 * N) == 5 else 0.0 for k in range(tot)]; R = [-0.45 if k % (16 * N) == 5 else 0.0 for k in range(tot)]
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
    if which == "emu": return EmuPhaser()
    m = (model_cls or M.Phaser)(); m.insert_defaults(); return m


def run_both(sig, setp=(), events=(), nblk=NBLK, prime=0, model_cls=None, emu_only=False, model_only=False):
    """prime: silent blocks first; setp after that; events [(block, op, arg...)] with op 'p' (idx, v), 'retrig', 'reset'.
    The tempo feed (InsertFxProcessor processBlock, F017) is slot-14 index 7 with the BPM value, sent before every block."""
    L, R = signal(sig, nblk)
    out = {}
    for which in ("emu", "model"):
        if (which == "model" and emu_only) or (which == "emu" and model_only): continue
        x = make(which, model_cls)
        for _ in range(prime): x.process([0.0] * N, [0.0] * N)
        for idx, v in setp: x.set_param(idx, v)
        oL, oR = [], []
        for b in range(nblk):
            for ev in events:
                if ev[0] != b: continue
                if ev[1] == "p": x.set_param(ev[2], ev[3])
                elif ev[1] == "retrig": x.retrigger()
                elif ev[1] == "reset": x.reset()
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


# index: 0 RATE 1 WIDTH 2 PHASE 3 FREQUENCY 4 FEEDBACK 5 MIXRATIO 6 SYNC 7 BPM (tempo feed)
TEMPO = (7, 120.0)
C6_CASES = [
    ("cold_insert_defaults", 0, [TEMPO], []),                                          # 2 Hz, width 1, 18 kHz, fb 0
    ("fast_mid", 1, [TEMPO, (0, 0.8), (1, 0.6), (2, 0.25), (3, 0.5), (4, 0.4), (5, 0.7)], []),
    ("deep_fb_lowfreq", 1, [TEMPO, (0, 0.95), (1, 1.0), (2, 0.5), (3, 0.2), (4, 1.0), (5, 1.0)], []),
    ("narrow_slow", 1, [TEMPO, (0, 0.05), (1, 0.15), (2, 1.0), (3, 0.85), (4, 0.7), (5, 0.3)], [(20, "p", 7, 133.0)]),  # tempo change, unsynced
    ("sync_quarter_120", 1, [TEMPO, (6, 1.0), (0, 9 / 11), (1, 0.8), (3, 0.6), (4, 0.6), (5, 0.5)], []),
    ("sync_sweep_divisions", 1, [TEMPO, (6, 1.0), (0, 1.0), (3, 0.7), (4, 0.3)],
     [(4 * k, "p", 0, (11 - k) / 11.0) for k in range(12)]),                           # all 12 divisions, every 4 blocks
    ("tempo_change", 1, [TEMPO, (6, 1.0), (0, 1.0), (1, 0.9), (3, 0.4), (4, 0.5)],
     [(16, "p", 7, 90.0), (32, "p", 7, 174.5), (48, "p", 7, 60.0), (48, "p", 0, 10 / 11.0), (56, "p", 0, 1.0), (56, "p", 7, 150.0)]),
    ("seq_param_changes", 1, [TEMPO, (0, 0.6), (1, 0.7), (3, 0.5), (4, 0.2), (5, 0.6)],
     [(8, "p", 0, 0.9), (12, "p", 4, 0.9), (20, "p", 1, 0.3), (24, "p", 3, 0.9), (30, "p", 2, 0.75), (36, "p", 6, 1.0),
      (40, "p", 0, 0.3), (44, "p", 6, 0.0), (50, "p", 4, 0.0), (54, "p", 5, 1.0)]),
    ("retrigger_reset", 1, [TEMPO, (0, 0.7), (1, 0.8), (3, 0.55), (4, 0.75), (2, 0.4)],
     [(10, "retrig"), (25, "reset"), (26, "p", 0, 0.4), (40, "retrig"), (41, "p", 3, 0.3), (52, "reset")]),
    ("extremes", 1, [TEMPO, (0, 1.0), (1, 0.0), (2, 0.0), (3, 0.0), (4, 1.0), (5, 1.0)],
     [(16, "p", 1, 1.0), (24, "p", 3, 1.0), (32, "p", 0, 0.0), (40, "p", 2, 1.0), (48, "p", 4, 0.0)]),
    ("fast_free_2cycles", 1, [TEMPO, (0, 1.0), (1, 1.0), (2, 0.5), (3, 0.8), (4, 0.85), (5, 1.0)], [], 160),   # 10 Hz, 232 ms
    ("tanf_sensitive", 1, [TEMPO, (0, 0.8), (1, 0.0), (3, 204 / 256.0), (4, 0.5), (5, 0.8)],                  # host tan != libm tanf
     [(32, "p", 3, 212 / 256.0), (48, "p", 3, 248 / 256.0)]),
]
C6_SIGNALS = ["impulse", "impulses", "sine1k", "noise"]       # single impulse: long tail into denormals (NEON flush-to-zero)


# ------------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H028"))
    ap.add_argument("--quick", action="store_true", help="C1/C5 and one C6 case (debug)")
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
    P("== C1 parameters (registration calls during the real 1.60 ctor 0x10d654) ==")
    x = EmuPhaser(defaults=False, log_regs=True)
    check(x.vptr == FX["vtable"], "vptr after ctor = 0x%x (Phaser)" % x.vptr)
    regs = []
    for r in x.regs:
        nm = im.cstr(r["name_ptr"]); off = r["obj_off"] - x.o
        fl = r["func"].startswith("LinearParameter")
        rng = (u2f(r["r3"]), u2f(r["stack"][0]), u2f(r["stack"][1])) if fl else None
        regs.append({"name": nm, "name_ptr": hex(r["name_ptr"]), "id": r["id"], "obj_off": hex(off),
                     "kind": "float" if fl else "toggle", "min,max,default": rng})
        P("  id %d %-9s (str 0x%x) at obj+0x%x  %-6s %s" % (r["id"], nm, r["name_ptr"], off, "float" if fl else "toggle",
                                                           "min %s max %s default %s" % rng if rng else "(bool, ctor off)"))
    res["C1_registrations"] = regs
    check([r["name"] for r in regs] == M.REG_NAMES and [r["id"] for r in regs] == list(range(8)) and
          [int(r["obj_off"], 16) for r in regs] == PARAM_OFF, "8 parameters, ids 0..7: %s" % [r["name"] for r in regs])
    s_ctor = x.state()
    P("  ctor (last, cur): %s" % s_ctor["params (last, cur)"])
    check(all(s_ctor["params (last, cur)"][nm] == [f32(M.CTOR_VALUES[k])] * 2 for k, nm in enumerate(M.PARAM_NAMES)),
          "ctor last = cur = registered default for every parameter %s" % M.CTOR_VALUES)
    xi = EmuPhaser(defaults=False, log_slot14=True); H7.Run.insert_init(xi)
    P("  Insert defaults (slot 52 case 8, slot-14 calls (index, value)): %s" % xi.s14)
    check(xi.s14 == [(k, f32(M.INSERT_DEFAULTS[k])) for k in sorted(M.INSERT_DEFAULTS)],
          "slot 52 case 8 sets Rate 199/999 (2.00 Hz), Width 1, Phase 0, Frequency 1, Feedback 0, Mixratio 0, Sync 0")
    res["C1_insert_defaults_calls"] = xi.s14
    idxmap = {}
    for idx in range(9):
        y = EmuPhaser(); y.process(L1, R1); before = y.state()["params (last, cur)"]
        rc = y.set_param(idx, 1.0 if idx == 6 else (77.0 if idx == 7 else 0.123)); after = y.state()["params (last, cur)"]
        idxmap[idx] = {"ret": rc, "changed": [k for k in before if before[k] != after[k]]}
    P("  slot-14 index -> changed parameter (ret): %s" % {k: (v["changed"], v["ret"]) for k, v in idxmap.items()})
    check(all(idxmap[k]["changed"] == [M.PARAM_NAMES[k]] and idxmap[k]["ret"] == 0 for k in range(8)) and
          idxmap[8]["changed"] == [] and idxmap[8]["ret"] == 3, "slot-14 index k sets parameter id k (0..7, ret 0); 8 -> ret 3")
    res["C1_slot14_map"] = idxmap
    tg = []
    for v in (1.0, 0.3, 0.5, 0.99, 0.0, 1.5, -1.0, 0.7):
        y = EmuPhaser(); y.process(L1, R1)
        if v in (0.3, 0.5, 0.99, 0.0, 0.7): y.set_param(6, 1.0)
        rc = y.set_param(6, v); cur = y.state()["params (last, cur)"]["SYNC"][1]
        mt = M.Toggle(1 if v in (0.3, 0.5, 0.99, 0.0, 0.7) else 0); mr = mt.set(v)
        tg.append({"start": 1 if v in (0.3, 0.5, 0.99, 0.0, 0.7) else 0, "v": v, "ret": rc, "cur": cur, "model": [mr, mt.cur]})
    P("  Sync toggle set(v) from start state -> (ret, cur): %s" % [(t["start"], t["v"], t["ret"], t["cur"]) for t in tg])
    check(all([t["ret"], t["cur"]] == t["model"] for t in tg), "toggle: v >= 1 -> on, v <= 0 -> off, 0 < v < 1 -> unchanged (ret 3)")
    res["C1_toggle"] = tg
    # tempo feed: InsertFxProcessor processBlock 0x116860 jump table @0x11694c, case for index 8
    jt = 0x11694c
    ins = im.disasm(jt - 0x10, jt + 4)
    cases = [im.u32(jt + 4 * k) for k in range(10)]
    t8 = cases[8]; body = im.disasm(t8 - 0x2c, t8 + 0x30)       # case 0x116b28 + its shared clamp/feed tail 0x116afc
    has7 = any(i.mnemonic == "mov" and i.op_str.endswith(", #7") and i.op_str.startswith("r1") for i in body)
    has14 = any("#0x38]" in i.op_str for i in body)
    clamp_hi = u2f(im.u32(0x116afc + 8 + 0xbc))
    P("  processBlock jump table 0x%x: case targets %s; index 8 -> 0x%x: tempo = (float)[proc+0x94]->vt+0x1c(), clamp 1.0..%g, "
      "'mov r1, #7' %s, slot-14 call (+0x38) %s" % (jt, [hex(c) for c in cases], t8, clamp_hi, has7, has14))
    check(cases[8] == cases[1] and has7 and has14 and clamp_hi == 999.0, "Insert index 8 (Phaser) shares the tempo-feed case with index 1: "
          "slot 14(e, 7, tempo) every block (F017)")
    res["C1_tempo_feed_case"] = {"cases": [hex(c) for c in cases], "has_r1_7": has7, "has_slot14": has14}

    # ---------------- C2 signal flow ---------------------------------------------------------------------------------
    P(); P("== C2 signal flow: routines reached inside slot 25 (code hooks), in order ==")
    xf = EmuPhaser(flow=True)
    traces = []
    for b in range(4):
        xf.trace = []
        if b == 2: xf.set_param(0, 0.6); xf.set_param(3, 0.4); xf.set_param(2, 0.5)
        if b == 3: xf.set_param(6, 1.0)
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
        P("  block %d%s: %s" % (b, {2: " (after RATE 0.6, FREQUENCY 0.4, PHASE 0.5)", 3: " (after SYNC on)"}.get(b, ""), compact(tr)))
    res["C2_traces"] = [[FLOW_SITES[a_] for a_ in tr] for tr in traces]
    t1 = [FLOW_SITES[a_] for a_ in traces[1]]
    check(t1 == ["Phaser_process", "Osc_process", "Phaser_kernel", "Phaser_slot26_mix"],
          "steady block: 0x10d260 > oscillator 0x101bdc (once, n samples) > kernel 0x10cf40 > slot 26 0x10cb48")
    t2 = [FLOW_SITES[a_] for a_ in traces[2]]
    check(t2.index("Phaser_updateRate") < t2.index("Osc_setPhaseOffset") < t2.index("Osc_process") < t2.index("freqIndexToHz")
          < t2.index("Phaser_kernel") and t2.count("tanf") == 2,
          "changes: rate update > phase offset > oscillator > frequency/width range (2 x tanf) > kernel")
    t3 = [FLOW_SITES[a_] for a_ in traces[3]]
    check("syncIndexToFraction" in t3 and "rateIndexToHz" not in t3, "SYNC on: period from the Fraction table (0x34c2a8)")

    # ---------------- C3 shared vs new blocks ------------------------------------------------------------------------
    P(); P("== C3 shared vs new blocks ==")
    vps = {M.PARAM_NAMES[k]: hex(xi.u(xi.o + off)) for k, off in enumerate(PARAM_OFF)}
    P("  parameter vptrs: %s" % vps)
    check(all(v == "0x840ac8" for k, v in vps.items() if k != "SYNC") and vps["SYNC"] == "0x840b20",
          "7 LinearParameter (0x840ac8) + 1 ToggleParameter (0x840b20)")
    q = xi.u(xi.o + 0x21c)
    w0 = xi.u(q)
    P("  oscillator object [+0x21c] (new 0x98, ctor 0x100af0): first word 0x%x (= amplitude 0.5f, no vptr); +0x90 -> 0x%x" % (w0, xi.u(q + 0x90)))
    check(w0 == f2u(0.5), "the Phaser oscillator object has no vtable (word 0 is the amplitude)")
    ti = im.u32(0x840398 - 4); tname = im.cstr(im.u32(ti + 4))
    P("  RTTI class `LFO`: vtable 0x840398, typeinfo 0x%x name %r (SamplingRateAndBufferSizeVariable child; not this object)" % (ti, tname))
    res["C3"] = {"param_vptrs": vps, "osc_word0": hex(w0), "rtti_LFO": [hex(ti), tname]}
    sub = {"SignalGate 0x840e40": 0x840e40, "IirFilter vptrs": None}
    words = [xi.u(xi.o + k) for k in range(0x1b8, 0x4f0, 4)]
    known = {0x840e40: "SignalGate", 0x840c28: "IirLpf2ndOrder", 0x840c48: "IirHpf2ndOrder", 0x841918: "IirBpf2ndOrder",
             0x841938: "IirOff", 0x83bcc0: "LowShelvingFilter", 0x83bcf0: "PeakingFilter", 0x840398: "LFO"}
    found = sorted(set(known[w] for w in words if w in known))
    P("  known block vptrs inside the Phaser object (+0x1b8..+0x4f0): %s" % (found or "none"))
    check(not found, "no SignalGate / IirFilter / IirFilter2 / RTTI-LFO object inside the Phaser")
    for fn, lo, hi in (("ctor 0x10d654", 0x10d654, 0x10da48), ("process 0x10d260", 0x10d260, 0x10d618),
                       ("kernel 0x10cf40", 0x10cf40, 0x10d254), ("reset 0x10cb78", 0x10cb78, 0x10cf30)):
        plt = im.plt(); tg_ = []
        for i_ in im.disasm(lo, hi):
            if i_.mnemonic in ("bl", "b", "blx") and i_.op_str.startswith("#0x"):
                t = int(i_.op_str[1:], 16)
                if not (lo <= t < hi): tg_.append(plt.get(t, hex(t)))
        P("  direct callees of %s: %s" % (fn, sorted(set(tg_))))
        res.setdefault("C3_callees", {})[fn] = sorted(set(tg_))
    check(not any(c in res["C3_callees"]["process 0x10d260"] + res["C3_callees"]["kernel 0x10cf40"]
                  for c in ("0xe89f0", "0xe895c", "0xf521c", "0xe16dc")), "no GainRamp / SignalGate / IirFilter call in process or kernel")

    # ---------------- C5 state layout ----------------------------------------------------------------------------------
    P(); P("== C5 state layout (emulated 1.60 object) vs model ==")
    mc = M.Phaser()
    bad, nf = diff_state(s_ctor, model_state(mc))
    P("  ctor state: %s" % {k: v for k, v in s_ctor.items() if k not in ("params (last, cur)",)})
    check(not bad, "model ctor state equals %d emulated fields%s" % (nf, "" if not bad else ": %s" % bad))
    xs = EmuPhaser(); ms = M.Phaser(); ms.insert_defaults()
    xs.set_param(*TEMPO); ms.set_param(*TEMPO)
    Ln, Rn = signal("noise", 8)
    nbad = 0; ntot = 0; ex = []
    for b in range(8):
        if b == 3: [o_.set_param(i_, v_) for o_ in (xs, ms) for i_, v_ in ((0, 0.9), (4, 0.8), (1, 0.4), (2, 0.3))]
        if b == 5: [o_.set_param(i_, v_) for o_ in (xs, ms) for i_, v_ in ((6, 1.0), (0, 0.5))]
        xs.process(Ln[b * N:(b + 1) * N], Rn[b * N:(b + 1) * N]); ms.process(Ln[b * N:(b + 1) * N], Rn[b * N:(b + 1) * N])
        bad, nf = diff_state(xs.state(), model_state(ms)); nbad += len(bad); ntot += nf
        eb = xs.osc_buf(N)
        if [f2u(v) for v in eb[0] + eb[1]] != [f2u(v) for v in ms.lfo_buf[0] + ms.lfo_buf[1]]: nbad += 1; ex.append(("osc buffer", b))
        ntot += 1
        if bad and len(ex) < 4: ex.append((b, bad[:3]))
    s_b0 = xs.state()
    check(nbad == 0, "after each of 8 blocks (with parameter and sync changes) model == emulation for %d field/buffer checks%s" %
          (ntot, "" if not ex else ": %s" % ex))
    res["C5_state_ctor"] = s_ctor; res["C5_state_after8"] = s_b0; res["C5_checks"] = [ntot, nbad]
    P("  oscillator after 8 blocks: %s" % s_b0["osc"])

    if not a.quick:
        # ---------------- C4 parameter formulas -------------------------------------------------------------------------
        P(); P("== C4 parameter -> stored value (slot 14 after a defaults block; one slot-25 block applies it) ==")
        VALS = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
        def after(sets, blocks=1):
            y = EmuPhaser(); y.set_param(*TEMPO); y.process(L1, R1)
            for i_, v_ in sets: y.set_param(i_, v_)
            for _ in range(blocks): y.process(L1, R1)
            return y.state()
        rows = []
        for v in VALS:
            v = f32(v)
            st = after([(0, v)])
            hz = M.Phaser.rate_hz(v); ms_ = f32(1000.0 / hz)
            rows.append(("RATE free", v, "period_ms+0x4cc", st["period_ms+0x4cc"], ms_, 1000.0 / (round(1 + 999 * v) / 100.0)))
            rows.append(("RATE free", v, "osc freq+0x10 (Hz)", st["osc"]["freq+0x10"], f32(1000.0 / ms_), round(1 + 999 * v) / 100.0))
            rows.append(("RATE free", v, "osc P+0x84", st["osc"]["P+0x84"], f32(f32(44100.0 / f32(1000.0 / ms_)) - 1.0), None))
            st = after([(3, v)])
            fh = M.Phaser.freq_hz(v)
            rows.append(("FREQUENCY", v, "hi_t+0x20c", st["hi_t+0x20c"], FT.tanf(f32(f32(fh * M.PI_F) / FS)),
                         math.tan(math.pi * 300.0 * 60.0 ** (round(256 * v) / 256.0) / FS)))
            st = after([(1, v), (3, 0.6)])
            m_ = M.Phaser(); m_.insert_defaults(); m_.process(L1, R1); m_.set_param(1, v); m_.set_param(3, 0.6); m_.process(L1, R1)
            f6 = 300.0 * 60.0 ** (round(256 * 0.6) / 256.0); lo_closed = f6 - (1 - (1 - float(v)) ** 2) * (f6 - 100.0)
            rows.append(("WIDTH (freq 0.6)", v, "lo_t+0x208", st["lo_t+0x208"], m_.lo_t, math.tan(math.pi * max(lo_closed, 100.0) / FS)))
            st = after([(2, v)])
            ph = f32(f32(v) * 0.5); ph = ph - 1.0 if ph >= 1.0 else ph
            rows.append(("PHASE", v, "osc ph+0x50 (x4 cycles)", st["osc"]["ph+0x50"], f32(ph * 4.0), 2.0 * float(v)))
            st = after([(4, v)], blocks=4)
            rows.append(("FEEDBACK", v, "fb_t+0x4dc", st["fb_t+0x4dc"], f32(0.0 + f32(v * f32(0.99))), 0.99 * v))
            rows.append(("FEEDBACK", v, "fb+0x1e0 (after 192 smp)", st["fb+0x1e0"], f32(0.0 + f32(v * f32(0.99))), 0.99 * v))
            st = after([(5, v)])
            rows.append(("MIXRATIO", v, "wet+0x14", st["wet+0x14"], v, v)); rows.append(("MIXRATIO", v, "dry+0x10", st["dry+0x10"], f32(1.0 - v), 1 - v))
        nbad = 0; nbit = 0; c4 = {}; nclose = 0
        for name, v, fld, got, exp, closed in rows:
            ok = f2u(f32(got)) == f2u(f32(exp)); nbit += ok; nbad += not ok
            cl = closed is None or abs(got - closed) <= 1e-5 * max(1.0, abs(closed)); nclose += cl
            c4.setdefault(name + " / " + fld, []).append({"v": v, "emu": got, "formula": float(exp), "closed_form": closed, "ok": ok, "close": cl})
        for name in c4:
            P("  %-44s %s" % (name, "; ".join("%.2g=%.9g%s%s" % (r["v"], r["emu"], "" if r["ok"] else " (formula %.9g) MISMATCH" % r["formula"],
                                                                "" if r["close"] else " (closed %.6g)" % r["closed_form"]) for r in c4[name])))
        check(nbad == 0, "all %d readbacks equal the float32 formulas bit-exactly" % len(rows))
        check(nclose == len(rows), "and agree with the plain closed forms within 1e-5 relative (rate = round(1+999v)/100 Hz, "
              "f = 300*60^(round(256v)/256) Hz, lo = f - (1-(1-w)^2)(f-100), phase = v/2 cycle, fb = 0.99v)")
        res["C4_rows"] = c4; res["C4_exact"] = [nbit, len(rows)]
        # tempo-synced period: 4 tempi x 12 divisions
        P("  tempo-synced period (SYNC on), ms = 60000/BPM * beats:")
        srows = []; sbad = 0
        for bpm in (60.0, 90.0, 120.0, 174.5):
            got = []
            for k in range(12):
                y = EmuPhaser(); y.set_param(7, bpm); y.process(L1, R1); y.set_param(6, 1.0); y.set_param(0, k / 11.0); y.process(L1, R1)
                st = y.state(); num, den = M.SYNC_FRACTIONS[k]
                exp = f32(f32(f32(60000.0 / f32(bpm)) * num) / den)
                ok = f2u(st["period_ms+0x4cc"]) == f2u(exp) and abs(st["period_ms+0x4cc"] / (60000.0 / bpm * num / den) - 1.0) <= 1e-6
                ok &= st["osc"]["freq+0x10"] == f32(1000.0 / exp) and st["bpm+0x4e8"] == f32(bpm)
                sbad += not ok; got.append(st["period_ms+0x4cc"])
                srows.append({"bpm": bpm, "index": k, "beats": "%d/%d" % (num, den), "ms": st["period_ms+0x4cc"], "ok": ok})
            P("   BPM %6.1f: %s" % (bpm, ", ".join("%s=%.6g" % ("%d/%d" % M.SYNC_FRACTIONS[k], got[k]) for k in range(12))))
        check(sbad == 0, "48 synced periods (4 tempi x 12 divisions 64/1 .. 1/16 beats) bit-exact (and within 1e-6 of 60000/BPM*beats); BPM stored at +0x4e8")
        res["C4_sync"] = srows
        # tanf: real 1.60 libm (emulated PLT) vs fdlibm model vs host-rounded
        e = EmuPhaser().e; g = random.Random(11)
        tv = [f32(g.uniform(0.0, 2.3)) for _ in range(3000)] + [f32(math.pi * f / FS) for f in range(20, 20001, 9)]
        et = [u2f(e.call(PLT_TANF, f2u(t))[0]) for t in tv]
        t_fd = sum(f2u(r) == f2u(FT.tanf(t)) for r, t in zip(et, tv)); t_host = sum(f2u(r) == f2u(f32(math.tan(t))) for r, t in zip(et, tv))
        P("  libm tanf (PLT 0x%x) vs fdlibm model: %d/%d bit-exact; host-rounded tan: %d/%d" % (PLT_TANF, t_fd, len(tv), t_host, len(tv)))
        lmb = open(os.path.join(emu.LIBDIR, "libm.so.6"), "rb").read()
        consts = [f2u(c) for c in [FT.PIO4, FT.PIO4LO, FT.PIO2_1, FT.PIO2_1T, FT.PIO2_2, FT.PIO2_2T] + FT.T]
        cfound = sum(1 for c in consts if struct.pack("<I", c) in lmb)
        check(t_fd == len(tv) and t_host < len(tv) and cfound == len(consts),
              "1.60 libm tanf = fdlibm single-precision algorithm (bit-exact); its %d constants occur in libm.so.6" % len(consts))
        res["C4_tanf"] = {"fdlibm": [t_fd, len(tv)], "host": [t_host, len(tv)], "constants_found": [cfound, len(consts)]}

    # ---------------- C6 model vs emulation --------------------------------------------------------------------------
    P(); P("== C6 model vs emulation (slot 25 direct, %d blocks x %d, stereo) ==" % (NBLK, N))
    cases = C6_CASES[:1] if a.quick else C6_CASES
    c6 = {}; allexact = True
    for case in cases:
        name, pr, setp, ev = case[:4]; nb = case[4] if len(case) > 4 else NBLK
        for sig in C6_SIGNALS:
            L, R, out = run_both(sig, setp, ev, prime=pr, nblk=nb)
            c = compare(out["emu"][:2], out["model"][:2])
            ms_e, ms_m = out["emu"][2].state(), model_state(out["model"][2])
            sb, _ = diff_state(ms_e, ms_m)
            c["final_state_diffs"] = len(sb)
            c["emu_sha"] = sha(pack(*out["emu"][:2]))[:16]
            c["rms_in"] = rms(L + R); c["rms_out"] = rms(out["emu"][0] + out["emu"][1])
            c6["%s/%s" % (name, sig)] = c
            exa = c["bit_exact"] == c["n"] and not sb; allexact &= exa
            P("  %-22s %-9s bit-exact %5d/%d  max|err| %.3g  first diff %s  state diffs %d  rms in/out %.4f/%.4f  sha %s" %
              (name, sig, c["bit_exact"], c["n"], c["max_abs_err"], c["first_diff_index"], len(sb), c["rms_in"], c["rms_out"], c["emu_sha"]))
            with open(os.path.join(a.out, "emu_%s_%s.f32" % (name, sig)), "wb") as fh: fh.write(pack(*out["emu"][:2]))
    res["C6"] = c6
    check(allexact, "model output and final state are bit-exact to emulated 1.60 slot 25 in all %d C6 runs" % len(c6))

    if not a.quick:
        # ---------------- C7 alternatives ---------------------------------------------------------------------------
        P(); P("== C7 alternative explanations (model variants vs emulation, case fast_mid / deep_fb_lowfreq, noise + sine) ==")
        base = {c[0]: c[1:4] for c in C6_CASES}
        class Stages(M.Phaser):
            NST = 4
            def kernel(self, L, R, dfb, da, n):
                z = self.z; self.z = z[:self.NST]
                M.Phaser.kernel(self, L, R, dfb, da, n); self.z = self.z + z[self.NST:]
        class Stages8(Stages): NST = 6
        class FbFromAllpass(M.Phaser):                           # feedback taken from the last all-pass output, not the sum
            def kernel(self, L, R, dfb, da, n):
                fb = self.fb; a_ = list(self.a); s = list(self.s); z = self.z
                inv = F(F(1.0) / F(self.a_hi - self.a_lo)); diff = F(self.g_lo - self.g_hi)
                for i in range(n):
                    fb = F(fb + dfb)
                    for j, buf in ((0, L), (1, R)):
                        a_[j] = F(a_[j] + da[j]); xin = buf[i]
                        x = F(F(s[j] * fb) + xin)
                        g = F(self.g_lo - F(F(F(a_[j] - self.a_lo) * inv) * diff))
                        for k in range(6):
                            v = F(x - F(a_[j] * z[k][j])); x = F(F(a_[j] * v) + z[k][j]); z[k][j] = v
                        s[j] = F(F(x * self.pole1) + F(s[j] * self.pole))
                        buf[i] = F(F(xin + x) * g)
                self.fb = fb; self.a = a_; self.s = s
        class LinearMap(M.Phaser):                               # coefficient linear in the LFO (not cubic)
            def process(self, L, R):
                orig = M.LFO.process
                def proc(lfo, n):
                    l, r = orig(lfo, n)
                    cb = lambda t: F(math.copysign(abs(t) ** (1.0 / 3.0), t))
                    return [cb(t) for t in l], [cb(t) for t in r]
                M.LFO.process = proc
                try: return M.Phaser.process(self, L, R)
                finally: M.LFO.process = orig
        class SineLFO(M.Phaser):                                 # sine LFO of the same frequency and phase
            def process(self, L, R):
                orig = M.LFO.process
                def proc(lfo, n):
                    l, r = orig(lfo, n)
                    tri2s = lambda t: F(0.5 - 0.5 * math.cos(math.pi * float(t)))     # map triangle position to a raised cosine
                    return [tri2s(t) for t in l], [tri2s(t) for t in r]
                M.LFO.process = proc
                try: return M.Phaser.process(self, L, R)
                finally: M.LFO.process = orig
        class NoPhaseOffset(M.Phaser):                           # R uses the L LFO phase (offset 0 regardless of PHASE)
            def process(self, L, R):
                self.lfo.ph = F(0.0); return M.Phaser.process(self, L, R)
        class StepCoef(M.Phaser):                                # coefficient stepped once per block (no interpolation)
            def kernel(self, L, R, dfb, da, n):
                tgt = self.a_target; self.a = list(tgt)
                M.Phaser.kernel(self, L, R, dfb, (F(0.0), F(0.0)), n)
        variants = [("4 all-pass stages", Stages), ("6 stages (control: = model)", Stages8),
                    ("feedback from the last all-pass (not the output sum)", FbFromAllpass),
                    ("coefficient linear in the LFO (not cubic)", LinearMap), ("raised-cosine (sine) LFO", SineLFO),
                    ("L/R LFO offset 0 (PHASE ignored)", NoPhaseOffset), ("coefficient stepped per block", StepCoef)]
        c7 = []
        for vname, cls in variants:
            for cname in ("fast_mid", "deep_fb_lowfreq"):
                pr, sp, ev = base[cname]
                tot = 0; bit = 0; err = 0.0
                for sig in ("noise", "sine1k"):
                    L, R, out = run_both(sig, sp, ev, prime=pr, nblk=32, model_cls=cls)
                    c = compare(out["emu"][:2], out["model"][:2]); tot += c["n"]; bit += c["bit_exact"]; err = max(err, c["max_abs_err"])
                c7.append({"variant": vname, "case": cname, "bit_exact": bit, "n": tot, "max_abs_err": err})
                P("  %-54s %-16s bit-exact %5d/%d  max|err| %.3g" % (vname, cname, bit, tot, err))
        res["C7"] = c7
        ctrl = [r for r in c7 if r["variant"].startswith("6 stages")]
        rest = [r for r in c7 if not r["variant"].startswith("6 stages")]
        check(all(r["bit_exact"] == r["n"] for r in ctrl) and all(r["max_abs_err"] > 0.01 for r in rest),
              "only the reconstructed structure matches; every alternative differs (max|err| > 0.01; the 'offset 0' variant "
              "changes only the R channel, so ~half its samples stay equal)")
        # notch structure of the emulated chain: frozen coefficient (rate floor, width 0), feedback 0 -> 3 notches
        y = EmuPhaser(); y.set_param(*TEMPO)
        for i_, v_ in ((0, 0.0), (1, 0.0), (3, 0.5), (4, 0.0), (5, 1.0)): y.set_param(i_, v_)
        for _ in range(8): y.process([0.0] * N, [0.0] * N)
        imp = [1.0] + [0.0] * (N - 1); h = []
        for b in range(64):
            h += y.process(imp if b == 0 else [0.0] * N, [0.0] * N)[0]
        a_ = y.state()["a+0x1ec"][0]; g_ = None
        def H(fq):
            w = 2 * math.pi * fq / FS; return abs(sum(h[k] * complex(math.cos(w * k), -math.sin(w * k)) for k in range(len(h))))
        fc = M.Phaser.freq_hz(0.5)
        grid = [20.0 * 1.01 ** k for k in range(700) if 20.0 * 1.01 ** k < 21000]
        mags = [H(fq) for fq in grid]
        notches = [round(grid[k]) for k in range(1, len(grid) - 1) if mags[k] < mags[k - 1] and mags[k] < mags[k + 1] and mags[k] < 0.2]
        # theory: first-order all-pass phase phi(f) = -2 atan(tan(pi f/fs)/t), t = tan(pi fc/fs); 6 stages; notch where 6 phi = -(2m+1) pi
        t = math.tan(math.pi * fc / FS)
        def theory(nst): return [round(FS / math.pi * math.atan(t * math.tan((2 * m + 1) * math.pi / (2 * nst))))
                                 for m in range(nst // 2)]
        theo = theory(6)
        P("  frozen chain (Frequency 0.5 -> fc %.1f Hz, width 0, fb 0): coefficient %.6f, |H| notches at %s Hz; first-order all-pass "
          "theory: 4 stages %s, 6 stages %s, 7 stages %s, 8 stages %s Hz" % (fc, a_, notches, theory(4), theo, theory(7), theory(8)))
        check(len(notches) == 3 and all(abs(n_ - t_) / t_ < 0.02 for n_, t_ in zip(notches, theo)),
              "emulated impulse response has 3 notches where 6 cascaded first-order all-passes put them (+-2 %)")
        res["C7_notches"] = {"fc": fc, "coef": a_, "notches": notches, "theory": {n_: theory(n_) for n_ in (4, 6, 7, 8)}}

    P(); P("RESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  failed: " + f_)
    with open(os.path.join(a.out, "h028_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    with open(os.path.join(a.out, "h028.json"), "w") as fh: json.dump(res, fh, indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
