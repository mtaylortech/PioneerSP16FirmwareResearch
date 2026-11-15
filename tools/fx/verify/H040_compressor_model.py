#!/usr/bin/env python3
"""H040 — InsertFxCompressor (Insert index 7; vtable 0x841618, new 0x790, ctor 0xf8a20 -> FxCompressor ctor 0xf7584; slot 25
0xf8718 -> detector 0xf8b88 / inline RMS, gain stage 0xf8c40, meters 0xf9490, slot 26 0xf7380) end to end: parameters ->
formulas -> detector / gain computer -> state layout -> bit-exact own-code model harness/models/compressor.py vs emulated slot 25;
plus the SendFxCompressor (ctor 0xf8a40, slot 25 0xf8270) relation.

Sections (criteria of kb/cycles/016.md):
  C1  parameter list: registrations logged in the real ctor, slot-14 index map, Insert slot-52 case-7 defaults, which values apply when.
  C2  formula sweeps: per-block read-back of the mapped values at their call sites (threshold, ratio, knee, gain/makeup, attack ms +
      coefficient, release ms + coefficient, level dB, target gain, ramp factor) vs the model, >= 5 values per parameter incl. rint
      boundaries; Mixratio dry/wet; LevelDetect domain; libm oracle (log10, powf, expf).
  C3  detector and gain computer by emulation: static curve (steady-state gain vs input level) vs the closed form, knee shape,
      peak vs RMS, stereo link, feed-forward, attack/release timing, in-block "look-ahead" ramp, metering outputs.
  C4  layout: state fields compared after every block (all C5 runs); constants.
  C5  end-to-end matrix: >= 8 settings x {impulse, 3 sine levels, noise, level steps, silence} >= 120 blocks + mid-run change runs.
  C6  start-up, slot 27 reset, EffectBase slot 5, slot 10.
  C7  alternatives (model mutants that must fail).
  C8  SendFxCompressor: vtable/core comparison, Send object built with its real ctor vs the model (look-ahead path).
Outputs only to --out (default harness/out/H040/). Run: .venv/bin/python -B harness/H040_compressor_model.py --out DIR
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
import compressor as M                                         # noqa: E402
from compressor import F                                       # noqa: E402
import glibc_expf, fdlibm_powf                                 # noqa: E402
from insert_delay import cr_log10                              # noqa: E402
import glibc_log10                                             # noqa: E402
from unicorn import arm_const as A                             # noqa: E402

FS = 44100; N = 64
CTOR_I, SIZE_I, VT_I = 0xf8a20, 0x790, 0x841618
CTOR_S, SIZE_S, VT_S = 0xf8a40, 0x798, 0x8416a0
PARAM_OFF = {0: 0x1b8, 2: 0x214, 3: 0x270, 1: 0x2cc, 7: 0x328, 4: 0x384, 5: 0x3e0, 8: 0x43c, "LA": 0x498,
             9: 0x4c0, 10: 0x51c, 11: 0x578, 12: 0x5d4, 13: 0x630}
NAMES = {0: "Threshold", 1: "Ratio", 2: "Attack", 3: "Release", 4: "Gain", 5: "Mixratio", 7: "Knee", 8: "LevelDetect"}
# per-block read-back sites inside 0xf8c40 (value in r0 / VFP register at the given pc, i.e. just after it is produced)
SITES = {"T": (0xf8cf0, "r0"), "R": (0xf8d8c, "r0"), "K": (0xf8db4, "s16"), "Gdb": (0xf8df8, "r0"), "makeup": (0xf8e18, "r0"),
         "A": (0xf8e68, "r0"), "a": (0xf8e84, "s18"), "Rl": (0xf8edc, "r0"), "r": (0xf8efc, "s17"), "gt": (0xf92d0, "r0"),
         "k": (0xf90dc, "r0")}


def sha(b): return hashlib.sha256(b).hexdigest()


class EmuComp:
    """InsertFxCompressor (or SendFxCompressor) built by its real ctor (obj, 44100, 64), then (optionally) the H007 Insert init
    (slot 22, 0x106c7c(obj,1,10), InsertFxProcessor slot 52 case 7). Processed by calling slot 25 directly."""
    def __init__(self, defaults=True, send=False, log_regs=False, readback=False, heap_fill=0):
        self.e = e = H31.new_emu() if not heap_fill else self._emu_fill(heap_fill)
        self.regs = []; self.s14 = []; self.rb = {}; self.send = send
        if log_regs:
            def cs(em):
                a_ = em.r(1); b_ = b""
                while len(b_) < 40:
                    c = em.rd(a_ + len(b_), 1)
                    if c == b"\0": break
                    b_ += c
                return b_.decode()
            def lin(em):
                sp = em.uc.reg_read(SP); st = [em.u32(sp + 4 * k) for k in range(2)]
                self.regs.append({"kind": "LinearParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": u2f(em.r(3)), "max": u2f(st[0]), "default": u2f(st[1])})
            def cho(em):
                sp = em.uc.reg_read(SP); st = [em.u32(sp + 4 * k) for k in range(2)]
                self.regs.append({"kind": "LinearParameter(choice)", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": em.r(3), "max": st[0], "default": st[1]})
            def tog(em):
                self.regs.append({"kind": "ToggleParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": None, "max": None, "default": None})
            e.add_watch(0xf1850, lin); e.add_watch(0xf1a00, cho); e.add_watch(0xf1800, tog)
        if readback:
            for k_, (pc, reg) in SITES.items():
                def cb(em, k_=k_, reg=reg):
                    if reg == "r0": self.rb[k_] = u2f(em.r(0))
                    else: self.rb[k_] = u2f(em.uc.reg_read(getattr(A, "UC_ARM_REG_" + reg.upper())))
                e.add_watch(pc, cb)
        e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), em.r(2))))
        self.obj = self.o = e.malloc(SIZE_S if send else SIZE_I, "new (harness: %sFxCompressor)" % ("Send" if send else "Insert"))
        r0, _ = e.call(CTOR_S if send else CTOR_I, self.o, FS, N)
        assert r0 == self.o and e.u32(self.o) == (VT_S if send else VT_I)
        self.fx = {"insert_index": 7}; self.init_log = []
        if defaults:
            self.s14 = []
            H7.Run.insert_init(self)
            self.defaults_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    @staticmethod
    def _emu_fill(v):
        e = emu.Emu(heap_fill=v)
        e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))
        lm, base, _ = e._libs["libm.so.6"]
        for r in lm.dynamic_relocations:
            if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(base + r.address, 0x3d000000)
        return e

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        self.rb = {}
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    # --- fields ------------------------------------------------------------------------------------------------------------
    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]
    def b(self, a): return self.e.rd(a, 1)[0]
    def fl(self, p, n): return list(struct.unpack("<%dI" % n, self.e.rd(p, 4 * n)))

    def state(self):
        o = self.o; u, i, d, b = self.u, self.i, self.d, self.b
        s = {"dry+0x10": u(o + 0x10), "wet+0x14": u(o + 0x14), "slope+0x68c": u(o + 0x68c), "thr_pt+0x690": u(o + 0x690),
             "gain+0x694": u(o + 0x694), "makeup+0x698": u(o + 0x698), "peak+0x6a4": u(o + 0x6a4), "ramp+0x6a8": i(o + 0x6a8),
             "mingain+0x6dc": u(o + 0x6dc), "la_pos+0x714": i(o + 0x714), "la_fade+0x728": u(o + 0x728), "pos+0x734": i(o + 0x734),
             "sum+0x740": d(o + 0x740), "ld+0x748": i(o + 0x748), "la+0x74c": b(o + 0x74c), "L+0x750": u(o + 0x750),
             "hold+0x754": i(o + 0x754), "holdlim+0x758": i(o + 0x758), "target+0x75c": u(o + 0x75c), "relms+0x764": u(o + 0x764),
             "w+0x768": u(o + 0x768), "cnt+0x76c": i(o + 0x76c), "lastK+0x784": u(o + 0x784), "lastT+0x788": u(o + 0x788),
             "lastR+0x78c": u(o + 0x78c)}
        for k_, off in ((0, 0x6ac), (1, 0x6c4), (2, 0x6e0), (3, 0x6f8)):
            s["m%d.cur" % k_] = u(o + off); s["m%d.cnt" % k_] = i(o + off + 0x14)
        s["det"] = self.fl(u(o + 0x6a0), N); s["gbuf"] = self.fl(u(o + 0x760), N); s["ring"] = self.fl(u(o + 0x73c), 132)
        for k_ in (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13): s["p%d" % k_] = u(o + PARAM_OFF[k_] + 0x28)
        s["p8"] = i(o + PARAM_OFF[8] + 0x44)
        if self.send:
            s["laL"] = self.fl(u(o + 0x718), 89); s["laR"] = self.fl(u(o + 0x71c), 89)
        return s


def model_state(m, send=False):
    fb = f2u
    s = {"dry+0x10": fb(m.dry), "wet+0x14": fb(m.wet), "slope+0x68c": fb(m.slope), "thr_pt+0x690": fb(m.thr_pt),
         "gain+0x694": fb(m.gain), "makeup+0x698": fb(m.makeup), "peak+0x6a4": fb(m.peak), "ramp+0x6a8": m.ramp,
         "mingain+0x6dc": fb(m.mingain), "la_pos+0x714": m.la_pos, "la_fade+0x728": fb(m.la_fade), "pos+0x734": m.pos,
         "sum+0x740": m.sum, "ld+0x748": m.ld_copy, "la+0x74c": m.lookahead, "L+0x750": fb(m.L),
         "hold+0x754": m.hold, "holdlim+0x758": m.hold_lim, "target+0x75c": fb(m.target), "relms+0x764": fb(m.rel_ms),
         "w+0x768": fb(m.w), "cnt+0x76c": m.cnt, "lastK+0x784": fb(m.last_knee), "lastT+0x788": fb(m.last_thr),
         "lastR+0x78c": fb(m.last_ratio)}
    for k_ in range(4):
        s["m%d.cur" % k_] = fb(m.mtr[k_].cur); s["m%d.cnt" % k_] = m.mtr[k_].cnt
    s["det"] = [fb(x) for x in m.det]; s["gbuf"] = [fb(x) for x in m.gbuf]; s["ring"] = [fb(x) for x in m.ring]
    for k_ in (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13): s["p%d" % k_] = fb(m.p[k_])
    s["p8"] = m.level_detect
    if send:
        s["laL"] = [fb(x) for x in m.la_L]; s["laR"] = [fb(x) for x in m.la_R]
    return s


class Model(M.Compressor):
    """The model (subclass only so that mutants can wrap methods)."""
    pass


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True, mut=None, send=False, readback=False):
    x = EmuComp(defaults=defaults, send=send, readback=readback)
    m = Model(send=send)
    if defaults: m.insert_defaults()
    if mut: mut(m)
    return x, m


def signal(kind, nblk, seed=11):
    n = nblk * N; rnd = random.Random(seed)
    if kind == "impulse":
        L = [F(1.0) if k % 1999 == 0 else F(0.0) for k in range(n)]
        R = [F(0.5) if k % 3001 == 7 else F(0.0) for k in range(n)]
    elif kind.startswith("sine"):
        amp = {"sine_lo": 0.05, "sine_mid": 0.3, "sine_hi": 0.9}[kind]
        L = [F(amp * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(n)]
        R = [F(0.7 * amp * math.sin(2 * math.pi * 440.0 * k / FS + 1.0)) for k in range(n)]
    elif kind == "noise":
        L = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
        R = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
    elif kind == "steps":       # 1 kHz sine, level steps (dB re 1): -1, -40, -12, -60, -3, silence, -20 ... (attack and release)
        lv = [-1.0, -40.0, -12.0, -60.0, -3.0, None, -20.0, -6.0]
        L = []; R = []
        for k in range(n):
            seg = lv[(k // (N * 20)) % len(lv)]
            a_ = 0.0 if seg is None else 10 ** (seg / 20)
            L.append(F(a_ * math.sin(2 * math.pi * 1000.0 * k / FS))); R.append(F(0.5 * a_ * math.sin(2 * math.pi * 700.0 * k / FS)))
    else:
        L = [F(0.0)] * n; R = [F(0.0)] * n
    return L, R


SIGNALS = ("impulse", "sine_lo", "sine_mid", "sine_hi", "noise", "steps", "silence")
# settings: (name, [(idx, value)] after the Insert defaults, blocks)
SETTINGS = [
    ("defaults_1to1_0dB", [], 160),
    ("T-20_R4_A10_R100_G6", [(0, 32 / 52), (1, 30 / 290), (2, 28 / 1018), (3, 90 / 3990), (4, 6 / 50)], 160),
    ("limit_T-52_R30_fastest", [(0, 0.0), (1, 1.0), (2, 0.0), (3, 0.0)], 160),
    ("T0_R30_fastest", [(0, 1.0), (1, 1.0)], 160),
    ("slowest_A1000_R4000_T-30_R8", [(0, 22 / 52), (1, 70 / 290), (2, 1.0), (3, 1.0)], 200),
    ("knee18_RMS_T-24_R6", [(0, 28 / 52), (1, 50 / 290), (7, 1.0), (8, 1.0), (2, 0.1), (3, 0.05)], 160),
    ("knee9_RMS_T-12_R2_G50_mix.5", [(0, 40 / 52), (1, 10 / 290), (7, 0.5), (8, 1.0), (4, 1.0), (5, 0.5)], 160),
    ("mix0_T-40_R10_A33", [(0, 12 / 52), (1, 90 / 290), (2, 0.05), (5, 0.0)], 160),
    ("RMS_T-18_R3.3_A2_R300_knee.25", [(0, 34 / 52), (1, 23 / 290), (2, 20 / 1018), (3, 290 / 3990), (7, 0.25), (8, 1.0)], 160),
    ("LD2_peak_T-6_R1.5_knee.1", [(0, 46 / 52), (1, 5 / 290), (8, 2.0), (7, 0.1), (2, 0.3)], 160),
]
EVENTS = [
    ("param_changes", [(0, 0.5), (1, 0.3)], 400,
     {40: [("p", 0, 0.2)], 80: [("p", 1, 1.0)], 120: [("p", 7, 0.7)], 160: [("p", 2, 0.6), ("p", 3, 0.02)], 200: [("p", 4, 0.3)],
      240: [("p", 5, 0.4)], 280: [("p", 8, 1.0)], 320: [("p", 7, 0.0), ("p", 0, 0.9)], 360: [("p", 8, 0.0)]}),
    ("reset_and_detector_switch", [(0, 0.3), (1, 0.6), (8, 1.0), (3, 0.3)], 300,
     {50: [("reset",)], 51: [("p", 8, 0.0)], 100: [("p", 8, 1.0)], 150: [("reset",), ("p", 1, 0.1)], 200: [("p", 0, 0.0)],
      250: [("reset",)]}),
]


def random_events(seed, nblk):
    rr = random.Random(seed); ev = {}
    for blk in range(5, nblk):
        if rr.random() < 0.25:
            ops = []
            for _ in range(rr.randint(1, 3)):
                idx = rr.choice([0, 1, 2, 3, 4, 5, 7, 8])
                v = float(rr.randint(0, 1)) if idx == 8 else rr.choice([rr.random(), 0.0, 1.0, rr.uniform(-0.1, 1.1)])
                ops.append(("p", idx, v))
            if rr.random() < 0.05: ops.append(("reset",))
            ev[blk] = ops
    return ev


def run_case(name, pre, events, kind, nblk, mut=None, keep=False, send=False, readback=False, emu_obj=None, sig=None):
    x, m = emu_obj if emu_obj is not None else new_pair(mut=mut, send=send, readback=readback)
    L, R = sig if sig is not None else signal(kind, nblk)
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    maxerr = 0.0; nbit = 0; first_state = None; outb = bytearray(); nonzero = 0; rbbad = 0; gains = []
    m.trace = [] if readback else None
    for blk in range(nblk):
        for op in events.get(blk, []):
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
            elif op[0] == "la": x.e.wr(x.o + PARAM_OFF["LA"] + 0x25, bytes([op[1]])); m.lookahead_param = op[1]
        bL, bR = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
        eL, eR = x.process(bL, bR)
        mL, mR = (m.process_send(bL, bR) if send else m.process(bL, bR))
        for a_, b_ in zip(eL + eR, mL + mR):
            if f2u(a_) != f2u(b_):
                nbit += 1
                if not (math.isnan(a_) and math.isnan(b_)): maxerr = max(maxerr, abs(a_ - b_))
            if a_ != 0.0: nonzero += 1
        outb += struct.pack("<%df" % (2 * N), *(eL + eR))
        if first_state is None:
            dd = diff(x.state(), model_state(m, send))
            if dd: first_state = (blk, [(k_, str(a_)[:60], str(b_)[:60]) for k_, a_, b_ in dd[:5]])
        if readback:
            t = m.trace[-1]
            for k_, (pc, reg) in SITES.items():
                mv = {"T": t["T"], "R": t["R"], "K": t["K"], "Gdb": M.gain_db(m.p[4]), "makeup": m.makeup, "A": M.attack_ms(m.p[2]),
                      "a": t["a"], "Rl": M.release_ms(m.p[3]), "r": t["r"], "gt": t["gt"], "k": t.get("k")}[k_]
                if k_ in x.rb and mv is not None and f2u(x.rb[k_]) != f2u(mv): rbbad += 1
        gains.append(u2f(x.state()["gain+0x694"]))
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 2 * N * nblk, "mismatched_samples": nbit, "max_abs_err": maxerr,
           "nonzero_out": nonzero, "first_state_diff": first_state, "readback_mismatches": rbbad,
           "min_gain": min(gains) if gains else None}
    return (res, bytes(outb), (x, m)) if keep else (res, bytes(outb))


# ------------------------------------------------------------------------------------------------------------------------
# C7 model mutants
def mut_rms_is_peak(m):                        # the "RMS" setting would be a plain peak detector
    orig = m.detect_peak
    m.detect_rms = lambda L, R, n: orig(L, R, n)

def mut_per_channel(m):                        # detector on the left channel only (no stereo link)
    orig = m.detect_peak
    m.detect_peak = lambda L, R, n: orig(L, [0.0] * n, n)

def mut_feedback(m):                           # detector on the previous block's output (feedback topology)
    m._prev = ([0.0] * N, [0.0] * N); orig = m.detect_peak
    def dp(L, R, n, m=m): orig(m._prev[0], m._prev[1], n)
    m.detect_peak = dp
    op = m.process
    def pr(L, R, m=m, op=op):
        oL, oR = op(L, R); m._prev = (oL, oR); return oL, oR
    m.process = pr

def mut_hard_knee(m):                          # knee ignored
    m.p_knee_ignore = True
    orig = m.gain_stage
    def gs(*a, m=m, orig=orig):
        k = m.p[7]; m.p[7] = 0.0; orig(*a); m.p[7] = k
    m.gain_stage = gs

def mut_no_slew(m):                            # gain follows the per-sample ramp directly (no attack/release limiter)
    import compressor as CM                    # attack coefficient 0 (no limit downwards), release coefficient 1e30 (none upwards)
    def gs(inL, inR, outL, outR, n, m=m, orig=Model.gain_stage):
        sv = CM.glibc_expf.expf
        CM.glibc_expf.expf = lambda x: 0.0 if x < 0 else 1e30
        try: orig(m, inL, inR, outL, outR, n)
        finally: CM.glibc_expf.expf = sv
    m.gain_stage = gs

def mut_no_block_ramp(m):                      # target applied at the block start (ramp length 1)
    orig = fdlibm_powf.powf
    def gs(inL, inR, outL, outR, n, m=m, orig_gs=Model.gain_stage):
        import compressor as CM
        sv = CM.powf
        CM.powf = lambda x, y: orig(x, 1.0) if y < 1.0 and x != 10.0 else orig(x, y)
        try: orig_gs(m, inL, inR, outL, outR, n)
        finally: CM.powf = sv
    m.gain_stage = gs

def mut_unity_dry(m):                          # Mixratio as unity dry + v*wet (Chorus/Flanger law)
    def um(m=m):
        v = m.p[5]; m.wet = F(v * m.makeup); m.dry = 1.0
    m.update_mix = um

def mut_release_no_hold(m):                    # no hold counter: the target recovers immediately after an attack block
    orig = Model.gain_stage
    def gs(*a, m=m):
        orig(m, *a); m.hold = 0
    m.gain_stage = gs

def mut_level_rms_no_sqrt2(m):                 # RMS level without the sqrt(2) (crest) factor
    orig = Model.detect_rms
    def dr(L, R, n, m=m):
        sv = M.K_SQRT2; M.K_SQRT2 = 1.0
        try: orig(m, L, R, n)
        finally: M.K_SQRT2 = sv
    m.detect_rms = dr

MUTANTS = [
    ("RMS setting = peak detector", mut_rms_is_peak, "knee18_RMS_T-24_R6", "noise"),
    ("per-channel (L-only) detector", mut_per_channel, "T-20_R4_A10_R100_G6", "noise"),
    ("feedback detector (on output)", mut_feedback, "T-20_R4_A10_R100_G6", "steps"),
    ("hard knee (knee ignored)", mut_hard_knee, "knee9_RMS_T-12_R2_G50_mix.5", "sine_mid"),
    ("no attack/release slew limiter", mut_no_slew, "T-20_R4_A10_R100_G6", "steps"),
    ("no in-block ramp (jump at block start)", mut_no_block_ramp, "limit_T-52_R30_fastest", "impulse"),
    ("Mixratio unity dry + v*wet (state; audio refuted at slot 18 in C3)", mut_unity_dry, "knee9_RMS_T-12_R2_G50_mix.5", "noise"),
    ("no hold before release", mut_release_no_hold, "T-20_R4_A10_R100_G6", "steps"),
    ("RMS level without sqrt(2)", mut_level_rms_no_sqrt2, "RMS_T-18_R3.3_A2_R300_knee.25", "sine_mid"),
]


def find_case(name):
    for s in SETTINGS:
        if s[0] == name: return s[0], s[1], {}, s[2]
    for s in EVENTS:
        if s[0] == name: return s[0], s[1], s[3], s[2]
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
    open(os.path.join(out, "h040_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok_all else 1


def steady_gain(pre, amp, nblk=150, kind="sine1k"):
    """Emulated steady-state gain (+0x694) for a 1 kHz sine of amplitude amp on both channels; also the model's."""
    x, m = new_pair()
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    L = [F(amp * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(N * nblk)]
    for blk in range(nblk):
        b_ = L[blk * N:(blk + 1) * N]; x.process(b_, b_); m.process(b_, b_)
    return u2f(x.state()["gain+0x694"]), m.gain, u2f(x.state()["L+0x750"])


def closed_form_db(L, T, R, W):
    """Standard quadratic soft knee (width W dB): static output level y(L)."""
    if W > 0 and abs(L - T) <= W / 2: return L + (1 / R - 1) * (L - T + W / 2) ** 2 / (2 * W)
    return L if L <= T else T + (L - T) / R


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H040"))
    ap.add_argument("--skip-matrix", action="store_true")
    ap.add_argument("--regress", action="store_true", help="only re-run H021..H039 and compare their recorded hashes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)

    P("H040 InsertFxCompressor end-to-end — target sha256 %s" % emu.SHA)
    im = sp16img.Image()

    # ---------------------------------------------------------------------------------------------------------- C1
    P("\n== C1 parameters")
    x = EmuComp(defaults=False, log_regs=True)
    for r_ in x.regs:
        P("  reg %-23s +0x%03x id %2d %-19s min %s max %s default %s" % (r_["kind"], r_["off"], r_["id"], r_["name"], r_["min"],
                                                                     r_["max"], r_["default"]))
    J["registrations"] = x.regs
    exp_regs = [("Threshold", 0, 0x1b8, 1.0), ("Attack", 2, 0x214, 1.0), ("Release", 3, 0x270, 1.0), ("Ratio", 1, 0x2cc, 0.0),
                ("Knee", 7, 0x328, 0.0), ("Gain", 4, 0x384, 0.5), ("Mixratio", 5, 0x3e0, 0.0), ("LevelDetect", 8, 0x43c, 0),
                ("LookAhead", 0, 0x498, None), ("ViewInputLevelLch", 9, 0x4c0, 1.0), ("ViewInputLevelRch", 10, 0x51c, 1.0),
                ("ViewRatio", 11, 0x578, 1.0), ("ViewOutputLevelLch", 12, 0x5d4, 1.0), ("ViewOutputLevelRch", 13, 0x630, 1.0)]
    check([(r_["name"], r_["id"], r_["off"], r_["default"]) for r_ in x.regs] == exp_regs,
          "14 Parameter objects at +0x1b8 + 0x5c*k: Threshold 0, Attack 2, Release 3, Ratio 1, Knee 7, Gain 4, Mixratio 5 (LinearParameter "
          "0..1), LevelDetect 8 (choice 0..1), LookAhead (ToggleParameter, id 0), 5 View* meters 9..13 (0..2, ViewRatio 0..1e10)")
    # slot-14 map
    imap = {}
    for idx in range(16):
        xx = EmuComp(defaults=False); s0 = xx.e.rd(xx.o, SIZE_I); ret = xx.set(idx, 0.37); s1 = xx.e.rd(xx.o, SIZE_I)
        ch = ["+0x%x" % k for k in range(0, SIZE_I, 4) if s0[k:k + 4] != s1[k:k + 4]]
        imap[idx] = {"ret": ret, "changed": ch}
    P("  slot14(i, 0.37): " + "; ".join("%d->ret %d %s" % (k_, v["ret"], v["changed"]) for k_, v in imap.items()))
    xl = EmuComp(defaults=False); rl = xl.set(8, 1.7); ld = xl.i(xl.o + 0x43c + 0x44)
    P("  slot14(8, 1.7) -> ret %d, LevelDetect int +0x44 = %d (trunc)" % (rl, ld))
    J["slot14_map"] = imap
    check(all(imap[i]["ret"] == 0 and imap[i]["changed"] == ["+0x%x" % (PARAM_OFF[i] + 0x28)] for i in (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13))
          and imap[8]["ret"] == 0 and imap[8]["changed"] == [] and ld == 1 and all(imap[i]["ret"] == 3 for i in (6, 14, 15)),
          "slot 14 (EffectBase 0x105d24) only stores: float params at +0x28; LevelDetect (choice) stores trunc(v) at +0x44 (0.37 -> 0, "
          "no change; 1.7 -> 1); id 0 reaches Threshold, not LookAhead (registered later, same id); 6/14/15 return 3")
    xd = EmuComp(defaults=True)
    J["insert_defaults_s14"] = [(i_, "0x%08x" % b_) for i_, b_ in xd.defaults_s14]
    P("  Insert slot 52 case 7 defaults: %s" % [(i_, u2f(b_)) for i_, b_ in xd.defaults_s14])
    check(xd.defaults_s14 == M.INSERT_DEFAULTS, "Insert defaults (slot 52 case 7): Threshold 1 (0 dB), Ratio 0 (1:1), Attack 0 (0.05 ms), "
          "Release 0 (10 ms), Gain 0 (0 dB), Mixratio 1, Knee 0, LevelDetect 0 (peak) -> neutral (no compression), fully wet")
    # deferred application: nothing changes at slot 14; the next slot 25 reads every parameter (no change detection on values)
    xq, mq = new_pair(); xq.set(0, 0.5); xq.set(1, 0.5); mq.set_param(0, 0.5); mq.set_param(1, 0.5)
    sq0 = xq.state()
    L_, R_ = signal("sine_hi", 1); xq.process(L_, R_); mq.process(L_, R_); sq1 = xq.state()
    P("  after slot14(0,0.5),(1,0.5): thr_pt %r slope %r -> next slot 25: thr_pt %r slope %r gain %r ramp %d" %
      (u2f(sq0["thr_pt+0x690"]), u2f(sq0["slope+0x68c"]), u2f(sq1["thr_pt+0x690"]), u2f(sq1["slope+0x68c"]), u2f(sq1["gain+0x694"]),
       sq1["ramp+0x6a8"]))
    check(diff(sq1, model_state(mq)) == [] and sq0["thr_pt+0x690"] == 0 and u2f(sq1["thr_pt+0x690"]) == -26.0,
          "parameters take effect at the next slot 25 (0xf8c40 re-reads every parameter each block); Threshold/Ratio/Knee changes "
          "(copies +0x788/+0x78c/+0x784) only reset the ramp length to max(n, 44)")

    # ---------------------------------------------------------------------------------------------------------- C2
    P("\n== C2 formula sweeps (call-site read-back per block vs model)")
    def sweep(idx, vals, setup=()):
        xw, mw = new_pair(readback=True); mw.trace = []
        for i_, v_ in setup: xw.set(i_, v_); mw.set_param(i_, v_)
        L_, R_ = signal("sine_hi", len(vals) + 1)
        rows = []; bad = 0
        for k, v in enumerate(vals):
            xw.set(idx, v); mw.set_param(idx, v)
            xw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); mw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
            t = mw.trace[-1]
            mv = {"T": t["T"], "R": t["R"], "K": t["K"], "Gdb": M.gain_db(mw.p[4]), "makeup": mw.makeup, "A": M.attack_ms(mw.p[2]),
                  "a": t["a"], "Rl": M.release_ms(mw.p[3]), "r": t["r"], "gt": t["gt"]}
            dd = [k_ for k_, v_ in mv.items() if k_ in xw.rb and f2u(xw.rb[k_]) != f2u(v_)]
            st = diff(xw.state(), model_state(mw))
            if dd or st: bad += 1
            rows.append((v, {k_: xw.rb.get(k_) for k_ in mv}, dd, st[:2]))
        return rows, bad
    def half(lo, rng, k): return F((k + 0.5 - lo) / rng)        # v at which lo + v*rng = k + 0.5
    def around(v): return [v, u2f(f2u(v) - 1), u2f(f2u(v) + 1)]                 # the float and its two float neighbours
    sw = {}
    tv = [0.0, 1.0, 0.5, 0.25, 0.75, -0.1, 1.2] + around(half(-52, 52, -26)) + around(half(-52, 52, -51)) + [0.123, 0.987]
    sw["Threshold"] = (0, tv, "T", lambda v: M.thr_db(v))
    rv = [0.0, 1.0, 0.5, 30 / 290, 0.1, 0.9] + around(half(10, 290, 20)) + around(half(10, 290, 154)) + [0.0017, 0.3333]
    sw["Ratio"] = (1, rv, "R", lambda v: M.ratio(v))
    kv = [0.0, 1.0, 0.5, 0.25, 0.1, 0.01, 0.777, -0.2]
    sw["Knee"] = (7, kv, "K", lambda v: M.knee_db(v))
    gv = [0.0, 1.0, 0.5, 0.12, 0.7] + around(half(0, 50, 25)) + around(half(0, 50, 0)) + [1.3]
    sw["Gain"] = (4, gv, "Gdb", lambda v: M.gain_db(v))
    av = [0.0, 1.0, 0.5, 19 / 1018, 20 / 1018, 21 / 1018, 1 / 1018, 0.01, 0.05, 0.25] + around(half(1, 1018, 20)) + around(half(1, 1018, 1000))
    sw["Attack"] = (2, av, "A", lambda v: M.attack_ms(v))
    lv = [0.0, 1.0, 0.5, 0.01, 0.1, 0.25, 0.75] + around(half(10, 3990, 100)) + around(half(10, 3990, 3999))
    sw["Release"] = (3, lv, "Rl", lambda v: M.release_ms(v))
    tbl = {}
    for nm, (idx, vals, key, fn) in sw.items():
        setup = [(0, 0.3), (1, 0.5)] if idx not in (0, 1) else ([(1, 0.5)] if idx == 0 else [(0, 0.3)])
        rows, bad = sweep(idx, [F(v) for v in vals], setup)
        ok_fn = all(f2u(fn(F(r_[0]))) == f2u(r_[1][key]) for r_ in rows)
        tbl[nm] = [(r_[0], r_[1][key]) for r_ in rows]
        extra = ""
        if nm == "Attack": extra = "  coef a: " + ", ".join("%.5g->%.9g" % (r_[1]["A"], r_[1]["a"]) for r_ in rows[:6])
        if nm == "Release": extra = "  coef r: " + ", ".join("%.5g->%.9g" % (r_[1]["Rl"], r_[1]["r"]) for r_ in rows[:5])
        if nm == "Gain": extra = "  makeup: " + ", ".join("%g->%.9g" % (r_[1]["Gdb"], r_[1]["makeup"]) for r_ in rows[:5])
        P("  %-9s %2d values: %s%s" % (nm, len(rows), ", ".join("%.7g->%.7g" % (r_[0], r_[1][key]) for r_ in rows[:12]), extra))
        check(bad == 0 and ok_fn and len(set(vals)) >= 5, "%s: %d values (incl. rint boundaries / out of range), formula and all "
              "read-backs + full state equal to the model (0 mismatching blocks)" % (nm, len(set(vals))))
    J["sweeps"] = tbl
    # Mixratio
    mvs = [0.0, 0.3, 0.5, 1.0, 1.2, -0.2, 0.77]
    xw, mw = new_pair(); xw.set(4, 0.12); mw.set_param(4, 0.12); rows = []; bad = 0
    L_, R_ = signal("noise", len(mvs))
    for k, v in enumerate(mvs):
        xw.set(5, v); mw.set_param(5, v); xw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); mw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
        s_ = xw.state(); rows.append((v, u2f(s_["dry+0x10"]), u2f(s_["wet+0x14"]))); bad += diff(s_, model_state(mw)) != []
    P("  Mixratio (gain 6 dB, makeup %.7g): %s" % (mw.makeup, ", ".join("%g->dry %.7g wet %.7g" % r_ for r_ in rows)))
    check(bad == 0, "Mixratio (slot 26 0xf7380, called from 0xf8c40 every block): dry = 1 - v, wet = v * makeup (unclamped); %d values" % len(mvs))
    J["sweep_mix"] = rows
    # LevelDetect domain
    ldv = [0.0, 0.99, 1.0, 1.5, 2.0, -1.0, 3.7]; ldr = []
    for v in ldv:
        xw, mw = new_pair(); xw.set(8, v); mw.set_param(8, v); L_, R_ = signal("sine_mid", 3)
        for k in range(3): xw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); mw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
        s_ = xw.state(); ldr.append((v, s_["ld+0x748"], s_["cnt+0x76c"], diff(s_, model_state(mw)) == []))
    P("  LevelDetect v -> int, RMS counter after 3 blocks, model ok: %s" % ldr)
    check(all(r_[3] for r_ in ldr) and [r_[2] > 0 for r_ in ldr] == [False, False, True, True, False, False, False],
          "LevelDetect = trunc(v): 1 (v in [1, 2)) = RMS detector; 0 and every other integer = peak detector")
    # libm oracle
    e = xd.e
    def lcall_d(nm, *ds):
        args = []
        for dv in ds: u = emu.d2u(dv); args += [u & 0xffffffff, u >> 32]
        r0, r1 = e.call(e.lib_exports[nm][0], *args); return emu.u2d(r0 | (r1 << 32))
    def lcall_f(nm, *fs_): return u2f(e.call(e.lib_exports[nm][0], *[f2u(v) for v in fs_])[0])
    rr = random.Random(9)
    largs = [float(F(10 ** rr.uniform(-8, 0.5))) for _ in range(1500)] + [float(M.K_1E8), 1.0, 0.5, 0.25]
    bl_cr = sum(lcall_d("log10", v) != cr_log10(v) for v in largs); bl_h = sum(lcall_d("log10", v) != math.log10(v) for v in largs)
    bl_g = sum(lcall_d("log10", v) != glibc_log10.log10(v) for v in largs)
    bl_f = sum(f2u(F(20.0 * lcall_d("log10", v))) != f2u(F(20.0 * cr_log10(v))) for v in largs)
    pargs = [(10.0, F(rr.uniform(-8, 2.5))) for _ in range(800)] + [(F(rr.uniform(0.001, 3)), F(1.0 / rr.randint(1, 200))) for _ in range(800)]
    bp = sum(f2u(lcall_f("powf", x_, y_)) != f2u(fdlibm_powf.powf(x_, y_)) for x_, y_ in pargs)
    eargs = [F(-1.0 / (rr.uniform(0.1, 1000) * 44.1)) for _ in range(800)] + [F(1.0 / (rr.uniform(10, 4000) * 44.1)) for _ in range(800)]
    be = sum(f2u(lcall_f("expf", v)) != f2u(glibc_expf.expf(v)) for v in eargs)
    import crmath
    be_cr = sum(f2u(lcall_f("expf", v)) != f2u(crmath.expf(v)) for v in eargs)
    P("  libm: log10 %d args: glibc_log10 (fdlibm e_log10 on a correctly rounded log) mismatches %d, correctly rounded log10 %d "
      "(host math.log10 %d; after F(20*log10) %d); powf %d args: fdlibm %d; expf %d args: glibc_expf %d (correctly rounded expf %d)"
      % (len(largs), bl_g, bl_cr, bl_h, bl_f, len(pargs), bp, len(eargs), be, be_cr))
    check(bl_g == 0 and bp == 0 and be == 0 and bl_cr > 0, "model libm (glibc 2.13 fdlibm-style log10, fdlibm powf, glibc 2.13 expf) = "
          "emulated 1.60 libm; the 1.60 log10 is not correctly rounded")
    J["libm"] = {"log10": [len(largs), bl_g, bl_cr, bl_h, bl_f], "powf": [len(pargs), bp], "expf": [len(eargs), be, be_cr]}

    # ---------------------------------------------------------------------------------------------------------- C3
    P("\n== C3 detector and gain computer (emulated)")
    curve = []; okc = True
    for (T_, R_, W_) in ((-20, 4.0, 0.0), (-30, 10.0, 18.0), (-12, 2.0, 9.0)):
        pre = [(0, (T_ + 52) / 52), (1, (R_ * 10 - 10) / 290), (7, W_ / 18.0 / 2.0 if W_ else 0.0), (2, 0.0), (3, 0.0)]
        for ldb in (-50, -36, -30, -24, -21, -18, -12, -6, -1):
            ge, gm, Le = steady_gain(pre, 10 ** (ldb / 20), nblk=60)
            cf = closed_form_db(Le, T_, R_, W_) - Le
            curve.append((T_, R_, W_, ldb, round(Le, 3), round(20 * math.log10(ge), 4), round(cf, 4)))
            okc &= f2u(ge) == f2u(gm) and abs(20 * math.log10(ge) - cf) < 0.01
    for r_ in curve[::3]: P("    T %g R %g W %g: sine %d dB -> level %g dB, emulated gain %g dB, closed form %g dB" % r_)
    J["static_curve"] = curve
    check(okc, "static curve: steady-state gain (emulated) = model bit-exactly and = closed form within 0.01 dB: y = L below "
          "T - W/2, T + (L - T)/R above T + W/2, quadratic soft knee L + (1/R - 1)(L - T + W/2)^2 / (2W) inside, W = 2 x 18 v dB")
    # peak vs RMS on a sine and on a square-ish signal
    def level_of(sig_, ld):
        xw, mw = new_pair(); xw.set(8, ld); mw.set_param(8, ld)
        for k in range(10):
            b_ = sig_[k * N:(k + 1) * N]; xw.process(b_, b_)
        return u2f(xw.state()["L+0x750"])
    sine = [F(0.5 * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(640)]
    sq = [F(0.5 if (k // 22) % 2 == 0 else -0.5) for k in range(640)]
    spike = [F(0.5) if k % 200 == 0 else F(0.0) for k in range(640)]
    lv = {(nm, ld): level_of(s_, ld) for nm, s_ in (("sine", sine), ("square", sq), ("spike", spike)) for ld in (0.0, 1.0)}
    P("  level dB peak/RMS: sine 0.5 %.3f/%.3f, square 0.5 %.3f/%.3f, 1-sample spikes 0.5 every 200 %.3f/%.3f" %
      (lv[("sine", 0.0)], lv[("sine", 1.0)], lv[("square", 0.0)], lv[("square", 1.0)], lv[("spike", 0.0)], lv[("spike", 1.0)]))
    check(abs(lv[("sine", 0.0)] - lv[("sine", 1.0)]) < 0.05 and lv[("square", 1.0)] - lv[("square", 0.0)] > 2.9 and
          lv[("spike", 0.0)] - lv[("spike", 1.0)] > 15,
          "detector: peak = max(|L|,|R|) per block; RMS = sqrt(2) x sqrt(3 ms mean of max(L^2, R^2)) (sine reads the same on both; a "
          "square reads +3 dB on RMS; one-sample spikes every 200 samples read ~18 dB lower on RMS)")
    # stereo link / feed-forward / in-block ramp
    xw, mw = new_pair(); pre = [(0, 0.5), (1, 1.0)]
    for i_, v_ in pre: xw.set(i_, v_); mw.set_param(i_, v_)
    Lz = [F(0.0)] * N; Rz = [F(0.0)] * N; Lz[40] = F(0.9); Rz = [F(0.01)] * N
    xw.process([F(0.01)] * N, [F(0.01)] * N); eL, eR = xw.process(Lz, Rz); s_ = xw.state(); mw.process([F(0.01)] * N, [F(0.01)] * N); mw.process(Lz, Rz)
    gR = [eR[k] / Rz[k] for k in (0, 20, 39, 40, 63)]
    P("  L spike 0.9 at sample 40, R constant 0.01: R channel gain at samples 0/20/39/40/63 = %s; level %.3f dB = 20log10(0.9) "
      "(input side); ramp %d" % ([round(g, 5) for g in gR], u2f(s_["L+0x750"]), s_["ramp+0x6a8"]))
    check(gR[0] < 1.0 and gR[2] > gR[3] and abs(u2f(s_["L+0x750"]) - 20 * math.log10(0.9)) < 1e-4 and diff(s_, model_state(mw)) == [],
          "stereo-linked (an L-only peak reduces R), feed-forward (level = input peak, not output), and the gain already falls from the "
          "first sample of the block towards the target reached near the peak sample (in-block 'look-ahead' ramp of up to 63 samples)")
    # attack / release timing on a level step
    def step_trace(pre, nblk=120):
        xw, mw = new_pair()
        for i_, v_ in pre: xw.set(i_, v_); mw.set_param(i_, v_)
        tr = []; okk = True
        for k in range(nblk):
            a_ = 0.9 if 10 <= k < 40 else 0.03
            b_ = [F(a_ * math.sin(2 * math.pi * 1000.0 * (k * N + j) / FS)) for j in range(N)]
            xw.process(b_, b_); mw.process(b_, b_); s_ = xw.state()
            okk &= diff(s_, model_state(mw)) == []
            tr.append((k, round(20 * math.log10(u2f(s_["gain+0x694"])), 3), s_["hold+0x754"], round(u2f(s_["target+0x75c"]), 5)))
        return tr, okk
    tr1, ok1 = step_trace([(0, 32 / 52), (1, 1.0), (2, 0.0), (3, 0.0)])
    tr2, ok2 = step_trace([(0, 32 / 52), (1, 1.0), (2, 28 / 1018), (3, 490 / 3990)])
    P("  step -0.9 dBFS at block 10, back to -30 dB at block 40 (T -20, R 30): fastest (0.05/10 ms) gain dB/hold/target at blocks "
      "10,11,40,41,42,43,44,46: %s" % [tr1[k][1:] for k in (10, 11, 40, 41, 42, 43, 44, 46)])
    P("  same with attack 10 ms / release 500 ms: blocks 10,11,15,20,40,41,45,60,80: %s" % [tr2[k][1:] for k in (10, 11, 15, 20, 40, 41, 45, 60, 80)])
    J["step_fast"] = tr1; J["step_slow"] = tr2
    check(ok1 and ok2 and tr1[10][1] < -18 and tr2[11][1] > tr1[11][1] and tr2[41][2] > 0,
          "attack/release: per-sample slew limits exp(-1/(A fs/1000)) down and exp(+1/(Rl fs/1000)) up; after an attack block a "
          "hold of min(Rl/4, 10 ms) samples; afterwards the target rises x e per block; model = emulation in every block")
    # metering
    xw, mw = new_pair(); xw.set(0, 0.5); xw.set(1, 0.5); xw.set(4, 0.2); mw.set_param(0, 0.5); mw.set_param(1, 0.5); mw.set_param(4, 0.2)
    L_, R_ = signal("steps", 200); okm = True
    for k in range(200):
        xw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); mw.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
        okm &= diff(xw.state(), model_state(mw)) == []
    s_ = xw.state()
    P("  meters after 200 step blocks: ViewIn L/R %.5g/%.5g, ViewRatio (min gain) %.5g, ViewOut L/R %.5g/%.5g (x makeup, <= 2)" %
      tuple(u2f(s_[k_]) for k_ in ("p9", "p10", "p11", "p12", "p13")))
    check(okm, "metering: View* parameters 9..13 get per-block peak-hold meters (6-block hold, then x0.891 = -1 dB per block, floor "
          "1e-8, ceiling 2) of the input, the block's minimum gain, and output x makeup (clamped to 2); display only, no audio effect")

    # Mixratio at slot-18 level (EffectBase dry/wet sum with the slot-26 values; post-stage 0x106c88 neutralised)
    def slot18_run(mix):
        xq, mq = new_pair(); e = xq.e; cap = {}
        e.add_watch(0x106c88, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        e.add_watch(0xf8718, lambda em: cap.__setitem__("in", (em.floats(em.r(1), em.r(3)), em.floats(em.r(2), em.r(3)))))
        Lq, Rq = signal("noise", 60); o = []; w = []
        for i_, v_ in ((5, mix), (0, 32 / 52), (1, 30 / 290), (4, 0.12)): xq.set(i_, v_); mq.set_param(i_, v_)
        bl = e.malloc(4 * N); br = e.malloc(4 * N)
        for b in range(60):
            e.set_floats(bl, Lq[N * b:N * b + N]); e.set_floats(br, Rq[N * b:N * b + N])
            if b == 0 and e.vcall(xq.o, 9)[0] == 0: e.vcall(xq.o, 5, 0, 1); e.vcall(xq.o, 7, 0); mq.reset(); mq.update_mix()
            e.vcall(xq.o, 18, bl, br, N)
            o.append((e.floats(bl, N), e.floats(br, N)))
            w.append(mq.process(cap["in"][0], cap["in"][1]))
        dry, wet = mq.dry, mq.wet
        laws = {"crossfade F(F(dry*in)+F(wet*y)), dry 1-v, wet v*makeup": 0, "unity dry F(in+F(wet*y))": 0,
                "plain crossfade without makeup": 0}
        ns = 0
        for b in range(40, 60):
            for ch in (0, 1):
                for i in range(N):
                    inp = (Lq if ch == 0 else Rq)[N * b + i]; y = w[b][ch][i]; out = o[b][ch][i]; ns += 1
                    laws["crossfade F(F(dry*in)+F(wet*y)), dry 1-v, wet v*makeup"] += f2u(out) != f2u(F(F(dry * inp) + F(wet * y)))
                    laws["unity dry F(in+F(wet*y))"] += f2u(out) != f2u(F(inp + F(wet * y)))
                    laws["plain crossfade without makeup"] += f2u(out) != f2u(F(F(F(1.0 - F(mix)) * inp) + F(F(mix) * y)))
        return laws, ns, (float(dry), float(wet))
    s18 = {mix: slot18_run(mix) for mix in (0.3, 0.7, 1.0)}
    for k_, (laws, ns, dw) in s18.items():
        P("  slot 18 (activated, 0x106c88 neutralised), Mixratio %g (dry/wet %s), blocks 40..59: mismatching samples per law %s of %d"
          % (k_, dw, laws, ns))
    J["slot18_mix"] = {str(k_): v for k_, v in s18.items()}
    check(all(v[0]["crossfade F(F(dry*in)+F(wet*y)), dry 1-v, wet v*makeup"] == 0 for v in s18.values()) and
          all(s18[k_][0]["unity dry F(in+F(wet*y))"] > 0 for k_ in (0.3, 0.7)) and all(v[0]["plain crossfade without makeup"] > 0 for v in s18.values()),
          "Mixratio law at slot-18 level: out = (1 - v)*in + v*makeup*y (crossfade, make-up gain on the wet path only); unity dry "
          "and a crossfade without make-up both fail")

    # ---------------------------------------------------------------------------------------------------------- C4 (constants)
    P("\n== C4 layout / constants")
    xc, mc = new_pair(); o = xc.o
    consts = {"fs +0x69c": (xc.u(o + 0x69c), 44100), "RMS window +0x730": (xc.u(o + 0x730), mc.win),
              "1/window +0x738": (xc.u(o + 0x738), f2u(mc.inv_win)), "look-ahead len +0x710": (xc.u(o + 0x710), mc.la_len),
              "look-ahead step +0x72c": (xc.u(o + 0x72c), f2u(mc.la_step)), "e +0x770": (xc.u(o + 0x770), f2u(mc.c_e)),
              "1/e +0x774": (xc.u(o + 0x774), f2u(mc.c_einv)), "meter hold": (xc.u(o + 0x6bc), mc.mtr[0].hold),
              "meter decay": (xc.u(o + 0x6b8), f2u(mc.mtr[0].decay)), "meter ceil": (xc.u(o + 0x6b4), f2u(mc.mtr[0].ceil)),
              "meter floor": (xc.u(o + 0x6b0), f2u(mc.mtr[0].floor)), "vptr": (hex(xc.u(o)), hex(VT_I))}
    for k_, (ev, mv_) in consts.items(): P("  %-24s emu %-14r model %r" % (k_, ev, mv_))
    check(all(ev == mv_ for ev, mv_ in consts.values()), "constants: fs 44100, RMS window 132 (3 ms), look-ahead line 89, meter hold 6 "
          "blocks / decay 0.8912509 / ceil 2 / floor 1e-8, e and 1/e from expf(+-1)")
    check(diff(xc.state(), model_state(mc)) == [], "%d state fields (incl. detector/gain/RMS buffers, %d floats) equal after ctor + "
          "Insert init (compared after every block in C5)" % (len(model_state(mc)), N + N + 132))

    # ---------------------------------------------------------------------------------------------------------- C5
    hashes = {}
    if not a.skip_matrix:
        P("\n== C5 end-to-end matrix (slot 25 output, full state after every block)")
        results = []
        for nm, pre, nb in SETTINGS:
            for kind in SIGNALS:
                r_, blob = run_case(nm, pre, {}, kind, nb, readback=(kind == "steps"))
                fn = "%s__%s.f32" % (nm.replace("/", "_"), kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-32s %-8s %3d blk  mism %d  max|err| %g  nonzero %5d  min gain %-10.4g state %s%s" %
                  (nm, kind, nb, r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], r_["min_gain"],
                   "ok" if r_["first_state_diff"] is None else r_["first_state_diff"],
                   "  readback-mism %d" % r_["readback_mismatches"] if kind == "steps" else ""))
        for nm, pre, nb, ev in EVENTS:
            for kind in ("steps", "noise", "impulse"):
                r_, blob = run_case(nm, pre, ev, kind, nb)
                fn = "%s__%s.f32" % (nm, kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-32s %-8s %3d blk  mism %d  max|err| %g  nonzero %5d  min gain %-10.4g state %s" %
                  (nm, kind, nb, r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], r_["min_gain"],
                   "ok" if r_["first_state_diff"] is None else r_["first_state_diff"]))
        for sd in (1, 2, 3):
            ev = random_events(sd, 300)
            r_, blob = run_case("random_events_%d" % sd, [], ev, ("steps", "noise", "sine_hi")[sd - 1], 300)
            fn = "random_events_%d.f32" % sd; open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
            results.append(r_)
            P("  %-32s %-8s %3d blk  mism %d  max|err| %g  nonzero %5d  min gain %-10.4g state %s  (%d event blocks)" %
              (r_["name"], r_["signal"], 300, r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], r_["min_gain"],
               "ok" if r_["first_state_diff"] is None else r_["first_state_diff"], len(ev)))
        J["matrix"] = results
        tot = sum(r_["samples"] for r_ in results)
        check(all(r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None and r_["readback_mismatches"] == 0 for r_ in results),
              "compressor.py bit-exact to emulated slot 25: %d runs, %d output samples, full state equal after every block" % (len(results), tot))
        check(len(SETTINGS) >= 8 and all(s[2] >= 120 for s in SETTINGS) and len(EVENTS) >= 2,
              "coverage: %d settings x %d signals (>= 120 blocks; ratio 1..30, threshold -52..0, attack 0.05..1000 ms, release 10..4000 ms, "
              "knee 0..18, gain 0..50 dB, peak/RMS), %d event runs + 3 random-event runs" % (len(SETTINGS), len(SIGNALS), len(EVENTS)))

    # ---------------------------------------------------------------------------------------------------------- C6
    P("\n== C6 start-up, reset, retrigger")
    xs, ms_ = new_pair(); xs.set(0, 0.0); xs.set(1, 1.0); ms_.set_param(0, 0.0); ms_.set_param(1, 1.0)
    L_, R_ = signal("sine_hi", 2); eL, _ = xs.process(L_[:N], R_[:N]); mL, _ = ms_.process(L_[:N], R_[:N])
    P("  first block after construction (T -52, R 30, sine 0.9): out[0..3] %s, gain at end %.6g; no mute/fade" %
      ([round(v, 5) for v in eL[:4]], u2f(xs.state()["gain+0x694"])))
    check([f2u(v) for v in eL] == [f2u(v) for v in mL] and eL[1] != 0.0,
          "no start-up mute or fade: the gain starts at 1 (ctor) and ramps within the first block")
    calls = []
    for a_ in (0xf7fb8, 0xf7e38, 0x10623c, 0xf7380):
        xs.e.add_watch(a_, lambda em, a_=a_: calls.append(hex(a_)))
    for k in range(1, 2): xs.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N]); ms_.process(L_[k * N:(k + 1) * N], R_[k * N:(k + 1) * N])
    calls.clear(); xs.e.vcall(xs.o, 27); ms_.reset(); s27 = xs.state()
    P("  slot 27: calls %s; gain %r makeup %r target %r hold %d RMS sum %r cnt %d relms %r; RMS ring kept (non-zero %d)" %
      (calls, u2f(s27["gain+0x694"]), u2f(s27["makeup+0x698"]), u2f(s27["target+0x75c"]), s27["hold+0x754"], s27["sum+0x740"],
       s27["cnt+0x76c"], u2f(s27["relms+0x764"]), sum(1 for v in s27["ring"] if v)))
    check(diff(s27, model_state(ms_)) == [] and u2f(s27["gain+0x694"]) == 1.0,
          "slot 27 (0xf7fb8 -> 0xf7e38): gain, makeup, target = 1, hold 0, RMS sum/counter 0, release copy 10 ms, meters to floor, "
          "look-ahead line cleared + fade = 1 (0 if LookAhead); RMS ring samples, ramp and last-value copies kept; model equal")
    calls.clear(); xs.e.vcall(xs.o, 5, 0, 1); s5 = xs.state()
    P("  EffectBase slot 5 (activation) calls: %s; dry/wet after %r/%r" % (calls, u2f(s5["dry+0x10"]), u2f(s5["wet+0x14"])))
    check("0xf7fb8" in calls and "0xf7380" in calls, "EffectBase slot 5 (activation, F022) runs slot 27 and slot 26 (mix with makeup 1 "
          "until the next block)")
    s0 = xs.state(); r10 = xs.e.vcall(xs.o, 10)[0]; s1 = xs.state()
    check(r10 == 2 and s0 == s1, "slot 10 (retrigger) = EffectBase default 0x10594c: returns 2, changes nothing")
    # heap fill robustness: +0x758 is computed in the ctor from +0x764 before it is set
    xh = EmuComp(defaults=True, heap_fill=0xA5); hl = xh.i(xh.o + 0x758)
    P("  ctor quirk: hold length +0x758 is computed from +0x764 before +0x764 = 10 is stored: zero heap -> %d, 0xA5 heap -> %d" %
      (EmuComp(defaults=True).i(EmuComp(defaults=True).o + 0x758), hl))
    J["holdlim_heapA5"] = hl

    # ---------------------------------------------------------------------------------------------------------- C7
    P("\n== C7 alternatives (mutants must fail)")
    mres = []
    for nm_, fn_, case, kind in MUTANTS:
        c_ = find_case(case)
        r_, _ = run_case(c_[0], c_[1], c_[2], kind, c_[3], mut=fn_)
        caught = r_["mismatched_samples"] > 0 or r_["first_state_diff"] is not None
        mres.append((nm_, case, kind, r_["mismatched_samples"], r_["max_abs_err"], caught))
        P("  mutant %-40s on %-30s %-8s mism %6d  max|err| %-10.4g -> %s" % (nm_, case, kind, r_["mismatched_samples"],
                                                                           r_["max_abs_err"], "CAUGHT" if caught else "not caught"))
    J["mutants"] = mres
    check(all(m_[5] for m_ in mres), "all %d alternative models are refuted by emulation" % len(mres))

    # ---------------------------------------------------------------------------------------------------------- C8
    P("\n== C8 SendFxCompressor relation")
    vt = [[im.u32(v + 4 * k) for v in (0x841590, VT_I, VT_S)] for k in range(32)]
    dif = [k for k in range(32) if len(set(vt[k])) > 1]
    P("  vtables FxCompressor 0x841590 / Insert 0x841618 / Send 0x8416a0 differ only in slots %s: %s" %
      (dif, [(k, [hex(v) for v in vt[k]]) for k in dif]))
    check(dif == [0, 1, 25], "Insert and Send share every FxCompressor slot except the dtors (0, 1) and slot 25")
    calls_all = im.direct_calls()
    def callees(lo, hi): return sorted(set(t for s_, t, k in calls_all if lo <= s_ < hi and k in ("bl", "blx")))
    ci = callees(0xf8718, 0xf8a20); cs = callees(0xf8270, 0xf8718)
    P("  direct callees: Insert slot 25 %s; Send slot 25 %s" % ([hex(v) for v in ci], [hex(v) for v in cs]))
    check(set(ci) <= set(cs) and {0xf8b88, 0xf8c40, 0xf9490}.issubset(set(ci)) and set(cs) - set(ci) == {0xf0814},
          "Send slot 25 calls the same detector 0xf8b88, gain stage 0xf8c40 and meters 0xf9490 (+ the same inline RMS code) and "
          "additionally reads LookAhead (0xf0814) for its 2 ms delay line")
    xsn = EmuComp(defaults=False, send=True); P("  Send ctor 0xf8a40: vptr %s, extra buffers +0x790/+0x794 %s" %
                                                  (hex(xsn.u(xsn.o)), [hex(xsn.u(xsn.o + 0x790)), hex(xsn.u(xsn.o + 0x794))]))
    sres = []
    for nm, pre, la in (("send_T-20_R4", [(0, 32 / 52), (1, 30 / 290), (5, 1.0), (2, 0.0)], 0),
                        ("send_RMS_knee_lookahead", [(0, 28 / 52), (1, 50 / 290), (7, 1.0), (8, 1.0), (5, 0.7)], 1)):
        for kind in ("steps", "impulse"):
            ev = {0: [("la", la)]} if la else {}
            x_, m_ = new_pair(defaults=False, send=True)
            if la:                                     # LookAhead has no slot-14 index (id 0 = Threshold): set the toggle directly
                x_.e.wr(x_.o + PARAM_OFF["LA"] + 0x25, bytes([1])); m_.lookahead_param = 1
            r_, blob = run_case(nm, pre, {}, kind, 160, send=True, emu_obj=(x_, m_))
            fn = "%s__%s.f32" % (nm, kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
            sres.append(r_)
            P("  %-28s %-8s 160 blk  mism %d  max|err| %g  state %s" % (nm, kind, r_["mismatched_samples"], r_["max_abs_err"],
                                                                       "ok" if r_["first_state_diff"] is None else r_["first_state_diff"]))
    J["send"] = sres
    check(all(r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None for r_ in sres),
          "SendFxCompressor built with its real ctor = the same model (process_send: 89-sample delay line + 147-sample crossfade "
          "when LookAhead toggles; detector on the undelayed input), bit-exact on 2 settings x 2 signals")

    # ---------------------------------------------------------------------------------------------------------- outputs
    P("\nRESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  FAILED: " + f_)
    cat = b"".join(open(os.path.join(a.out, k_), "rb").read() for k_ in sorted(hashes))
    J["f32_hashes"] = hashes; J["f32_concat_sha256"] = sha(cat) if hashes else None
    P("f32 files: %d, sorted concatenation sha256 %s" % (len(hashes), J["f32_concat_sha256"]))
    open(os.path.join(a.out, "h040_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h040.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
