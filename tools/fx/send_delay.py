# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Send/Master "Delay" (class `SendFxDelay`; primary vtable 0x841ea8 = DelayEchoBase
part, secondary vtable 0x841eec = EffectBase sub-object at +0x238; new 0x6c0, ctor 0x1054ac(obj, 44100, 64); index 0 of both
the Send and the Master FX processor arrays). Reconstructed in docs/effects/send-delay.md (H043). Contains no firmware bytes: only the
documented numeric constants of the algorithm. Reuses the shared blocks of insert_delay.py.

EffectBase slot 25 0x104e90 -> primary slot 14 0x104e98, per 64-sample block:
  1. mix law from Mixratio (no change detection): v < 0.75: dry 1, wet v*4/3; else wet 1, dry 1 - 4 (v - 0.75)
     -> +0x6a4/+0x6a8, copied by primary slot 13 0x1049e8 to EffectBase +0x10/+0x14 (the dry/wet sum is EffectBase's job).
  2. change detection SYNC, BPM, DelayTime (dirty flag +0x6b8). If dirty: ms = free: rint(10 + 3990 v) (10..4000 ms, 1 ms
     steps); sync: i = rint(7 v), beats = (1/8, 1/4, 1/2, 3/4, 1, 2, 4, 8)[i], ms = beats * 60000 / BPM clamped to [10, 4000];
     the SAME ms is written into both base Parameters DelayTimeLch (+0x2c) and DelayTimeRch (+0x88).
  3. every block (no change detection): Feedback v -> FeedbackGainLch/Rch (+0xe4/+0x140) unquantised; HiCut step
     trunc_s32(999 v) + 1 (1st-order LPF 2..20 kHz, 1000 log steps); LowCut x = 1 - v, step trunc_s32(999 (1 - x^4)) + 1
     (1st-order HPF 1..1000 Hz, 1000 log steps).
  4. primary slot 5 0x104a30 (DelayEchoBase process):
     a. primary slot 8 0x104ce4: L/R module setDelay(ms, glide) when the Parameter differs from the module's current ms; L/R
        feedback SmoothFloat targets; direct SmoothFloat target 1 - Spread, cross SmoothFloat target Spread (147-sample ramps).
     b. per chunk (chunk = left module's next read length):
          yL = modL.read(c), yR = modR.read(c)                 (two mono DelayModules, integer delay, own SignalGates)
          L' = direct*yL + cross*yR ; R' = direct*yR + cross*yL   (Spread = cross-feed / channel swap)
          L', R' -> HiCut LPF -> LowCut HPF                       (both inside the loop)
          out = (L', R')                                          (wet only)
          modL.write(inL + fbL*L') ; modR.write(inR + fbR*R')    (feedback taken after the matrix and both filters)
"""
import math
import struct

from lofi import F, near, nadd, nmul, vmul_block, Smooth, EPS
from chorus import LinParam, Toggle, rint_idx
import insert_delay as ID
from insert_delay import ftz_list_add, cr_tan, cr_pow, cr_log10, DelayModuleStereo, HiCut

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "DelayTime", 1: "Feedback", 2: "HiCut", 3: "LowCut", 4: "Spread", 5: "Mixratio", 6: "SYNC", 7: "BPM"}
# slot-52 defaults for index 0 (emulated bits): Send 0x11baa8 / Master 0x114ad4; they differ only in Mixratio (Send 1.0, Master 0.5)
SEND_DEFAULTS = [(0, 0x3dfb823f), (1, 0x3f333333), (2, 0x3f800000), (3, 0x0), (4, 0x0), (5, 0x3f800000), (6, 0x0)]
MASTER_DEFAULTS = [(0, 0x3dfb823f), (1, 0x3f333333), (2, 0x3f800000), (3, 0x0), (4, 0x0), (5, 0x3f000000), (6, 0x0)]
# Sync divisions (numerator, denominator) in beats, index = rint(7 v); .bss table 0xf61f94 (filled by .init_array 0x6cb20)
SYNC_BEATS = [(1, 8), (1, 4), (1, 2), (3, 4), (1, 1), (2, 1), (4, 1), (8, 1)]
MAXMS = 4000.0


def b2f(bits): return struct.unpack("<f", struct.pack("<I", bits))[0]


def trunc_s32(x):
    """vcvt.s32.f32: round toward zero, saturating; NaN -> 0."""
    if math.isnan(x): return 0
    if x >= 2147483647.0: return 2147483647
    if x <= -2147483648.0: return -2147483648
    return int(x)


# ---------------------------------------------------------------------------------------------------------------------------
class MonoRing(ID.RingBuffer):
    """RingBuffer (vtable 0x83e5c0) used by one mono DelayModule: interleaved storage of `frames` frames, only lane 0 is
    read (0xeb424, linear interpolation; delay is integer so fr = 0) and written (slot 6 0xebadc). frames = 2 * (trunc(maxms
    * 0.001 * fs) + 2500) / 2 = 178,900 at 44.1 kHz / 4000 ms."""
    def read(self, n):
        oL, _ = ID.RingBuffer.read(self, n)
        return oL

    def write1(self, L, n):
        bl = self.buf[0]; w = self.w
        for k in range(n):
            bl[w] = L[k]
            w = 0 if w == self.L - 1 else w + 1
        self.w = w


class DelayModuleMono(DelayModuleStereo):
    """DelayModule (vtable 0x840028, new 0x8c, ctor 0xec0fc(m, fs, block, maxms 4000)); same fields and control logic as
    DelayModuleStereo (+0x20 ms, +0x24 D, +0x28/+0x2c/+0x30 pending, +0x34 SignalGate, +0x7c warm, +0x7d full, +0x80 counter,
    +0x84 maxms, +0x88 = 1). setDelay 0xec384, read 0xec4bc, write 0xec6d4, reset 0xec314, next-chunk 0xec494."""
    def __init__(self, fs=FS, block=BLOCK, maxms=MAXMS):
        DelayModuleStereo.__init__(self, fs, block, maxms)
        lim = int(F(F(self.maxms * ID.K_MILLI) * F(float(fs))))
        self.ring = MonoRing(lim + 2500)
        self.D = int(F(F(float(fs)) * F(0.05)))          # ctor: trunc(fs * 0.05f) = 2205 (ms = 50.0)
        self.pD = self.D

    def read1(self, n):
        """0xec4bc(m, buf, n): the stereo control loop on one lane (the gate multiplies only this lane)."""
        ring = self.ring
        orig = ring.read
        def rd(c, ring=ring):
            L = MonoRing.read(ring, c)
            return L, [F(0.0)] * c
        ring.read = rd
        try:
            oL, _ = DelayModuleStereo.read(self, n)
        finally:
            ring.read = orig
        return oL

    def write1(self, L, n): self.ring.write1(L, n)


class SteppedFilter(HiCut):
    """Stepped 1st-order filter container (new 0x48, ctor 0xf3ce4(c, type, order 1, fs, 1000 steps, 1/3 ms, fmin, fmax)),
    shared code with the Insert HiCut: set_step 0xf41ac, process 0xf438c (glide one step per 1/3 ms), filter run 0xe1490.
    kind 'lpf' (type 1, IirLpf1stOrder vt 0x840dd8, coefs 0xe1b30) starts at the top step (cut = fmax);
    kind 'hpf' (type 0, IirHpf1stOrder vt 0x840db8, coefs 0xe1aa0) starts at step 0 (cut = fmin)."""
    def __init__(self, kind, fs=FS, steps=1000, fmin=2000, fmax=20000):
        self.kind = kind
        HiCut.__init__(self, fs, steps, fmin, fmax)
        if kind == "hpf":
            self.cur = self.tgt = 0; self.cut = self.tgt_cut = float(fmin)
            self._coefs()

    def _coefs(self):
        if self.kind == "lpf": return HiCut._coefs(self)
        self.fc = self._clampfc(self.cut)
        t = cr_tan(float(self.fc) * (ID.PI / float(self.fs)))
        d = (t * ID.INV_2PI) * ID.TWO_PI
        r = 1.0 / (d + 1.0)
        self.b0 = F(r); self.b1 = F(-r); self.a1 = F((d - 1.0) * r)


def smooth_mul(s, src_a, src_b, n):
    """0xf5b9c(srcA, srcB, dstA, dstB, SmoothFloat, scratch, n) out of place: ramp -> per-sample gains (0x5790c4, NEON groups of
    4 + VFP tail); settled at 1 -> copy; settled at 0 -> +0.0 (memset); else constant multiply (0x578734). src_b may be None."""
    if s.state == 1:
        g = s.gains(n)
        a = list(src_a); vmul_block(a, 0, n, g)
        if src_b is None: return a, None
        b = list(src_b); vmul_block(b, 0, n, g); return a, b
    c = s.cur
    if near(c, F(1.0)):
        return list(src_a), (None if src_b is None else list(src_b))
    if abs(float(c)) < float(EPS):
        return [F(0.0)] * n, (None if src_b is None else [F(0.0)] * n)
    a = list(src_a); vmul_block(a, 0, n, c)
    if src_b is None: return a, None
    b = list(src_b); vmul_block(b, 0, n, c); return a, b


# ---------------------------------------------------------------------------------------------------------------------------
class SendDelay:
    """SendFxDelay parameter path (0x104e98) + DelayEchoBase process (0x104a30)."""
    def __init__(self, fs=FS, block=BLOCK):
        self.fs = fs; self.block = block
        # SendFxDelay Parameters (+0x3f0 + 0x5c i; SYNC toggle +0x618, BPM +0x640)
        self.p = {0: LinParam(0.5), 1: LinParam(0.0), 2: LinParam(1.0), 3: LinParam(0.0), 4: LinParam(0.0), 5: LinParam(0.0),
                  6: Toggle(0), 7: LinParam(120.0)}
        # DelayEchoBase Parameters: DelayTimeLch +0x2c / Rch +0x88 (1..4000 ms, ctor 1.0), FeedbackGainLch +0xe4 / Rch +0x140 (0)
        self.bp = {"tL": LinParam(1.0), "tR": LinParam(1.0), "gL": LinParam(0.0), "gR": LinParam(0.0)}
        self.sync_v = 0; self.bpm_v = F(120.0); self.time_v = F(0.5); self.dirty = 0      # +0x6ac/+0x6b0/+0x6b4/+0x6b8
        self.modL = DelayModuleMono(fs, block, MAXMS); self.modR = DelayModuleMono(fs, block, MAXMS)   # +0x19c / +0x1a0
        n = int(F(F(ID.RAMP_MS * ID.K_MILLI) * F(float(fs))))                                         # 147
        self.fbL = Smooth(fs, n); self.fbL.set_now(F(0.0))       # +0x1a4
        self.fbR = Smooth(fs, n); self.fbR.set_now(F(0.0))       # +0x1c8
        self.direct = Smooth(fs, n); self.direct.set_now(F(1.0))  # +0x1ec
        self.cross = Smooth(fs, n); self.cross.set_now(F(0.0))   # +0x210
        self.hicut = SteppedFilter("lpf", fs, 1000, 2000, 20000)  # +0x69c
        self.lowcut = SteppedFilter("hpf", fs, 1000, 1, 1000)     # +0x6a0
        self.dry = F(1.0); self.wet = F(0.0)                      # +0x6a4 / +0x6a8 (-> EffectBase +0x10 / +0x14)
        self.ms_log = []

    # -- parameters ---------------------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24 -> Parameter slot 4
        if idx in self.p:
            if idx == 6:
                v = F(v)
                if not (v >= 1.0 or v <= 0.0): return 3
            self.p[idx].set(v); return 0
        return 3

    def defaults(self, master=False):
        for i, bits in (MASTER_DEFAULTS if master else SEND_DEFAULTS):
            self.set_param(i, b2f(bits))

    @staticmethod
    def free_ms(v): return F(float(rint_idx(10, 4001, v)))

    @staticmethod
    def sync_ms(v, bpm):
        i = rint_idx(0, 8, v)
        if not (0 <= i <= 7): i = 6                     # 0x34a498: unsigned i > 7 -> assert log + index 6
        a, b = SYNC_BEATS[i]
        ms = F(F(F(F(F(float(a)) / F(float(b))) * F(1000.0)) * F(60.0)) / F(bpm))
        if ms < F(10.0): return F(10.0)
        return F(MAXMS) if F(MAXMS) < ms else ms

    @staticmethod
    def hicut_step(v): return (trunc_s32(F(F(v) * F(999.0))) + 1) & 0xffffffff

    @staticmethod
    def lowcut_step(v):
        x = F(F(1.0) - F(v))
        x4 = F(x * F(x * F(x * x)))
        return (trunc_s32(F(F(F(1.0) - x4) * F(999.0))) + 1) & 0xffffffff

    def update_mix(self):                               # 0x104e98 head + slot 13 0x1049e8
        v = self.p[5].get()
        if v < F(0.75):
            self.dry = F(1.0); self.wet = F(F(v * ID.K_FOUR_THIRDS) + F(0.0))
        else:
            self.wet = F(1.0); self.dry = F(F(F(v - F(0.75)) * F(-4.0)) + F(1.0))

    def apply_params(self):                             # 0x104e98 (before the slot-5 call)
        p = self.p
        if p[6].changed(): self.sync_v = p[6].get(); self.dirty = 1
        if p[7].changed(): self.bpm_v = p[7].get(); self.dirty = 1
        if p[0].changed(): self.time_v = p[0].get(); self.dirty = 1
        if self.dirty:
            ms = self.sync_ms(self.time_v, self.bpm_v) if self.sync_v else self.free_ms(self.time_v)
            self.ms_log.append(ms)
            self.bp["tL"].set(ms); self.bp["tR"].set(ms); self.dirty = 0
        g = p[1].get(); self.bp["gL"].set(g); self.bp["gR"].set(g)
        self.hicut.set_step(self.hicut_step(p[2].get()))
        self.lowcut.set_step(self.lowcut_step(p[3].get()))

    def apply_base(self):                               # primary slot 8 0x104ce4
        tL, tR, gL, gR = (self.bp[k].get() for k in ("tL", "tR", "gL", "gR"))
        c = self.p[4].get()                             # Spread (+0x560), read directly by the base
        if not near(tL, self.modL.ms): self.modL.set_delay(tL, 1)
        if not near(gL, self.fbL.target): self.fbL.set_target(gL)
        if not near(tR, self.modR.ms): self.modR.set_delay(tR, 1)
        if not near(gR, self.fbR.target): self.fbR.set_target(gR)
        self.direct.set_target(F(F(1.0) - c))
        self.cross.set_target(c)

    # -- processing ---------------------------------------------------------------------------------------------------------
    def core(self, L, R):                               # primary slot 5 0x104a30
        self.apply_base()
        n = len(L); oL = list(L); oR = list(R); pos = 0
        while n - pos > 0:
            c = min(self.modL.chunk(), n - pos)
            s0 = self.modL.read1(c); s1 = self.modR.read1(c)
            s5, s4 = smooth_mul(self.cross, s0, s1, c)          # cross * (yL, yR)
            s0, s1 = smooth_mul(self.direct, s0, s1, c)         # direct * (yL, yR)
            ftz_list_add(s0, s4, c); ftz_list_add(s1, s5, c)    # L' = d yL + x yR ; R' = d yR + x yL
            self.hicut.process(s0, s1, c)
            self.lowcut.process(s0, s1, c)
            s2, _ = smooth_mul(self.fbL, s0, None, c)
            s3, _ = smooth_mul(self.fbR, s1, None, c)
            ftz_list_add(s2, L[pos:pos + c], c); ftz_list_add(s3, R[pos:pos + c], c)
            oL[pos:pos + c] = s0; oR[pos:pos + c] = s1
            self.modL.write1(s2, c); self.modR.write1(s3, c)
            pos += c
        return oL, oR

    def process(self, L, R):                            # EffectBase slot 25 0x104e90 -> 0x104e98 (returns the wet block)
        self.update_mix()
        self.apply_params()
        return self.core(L, R)

    def reset(self):                                    # EffectBase slot 27 0x1049fc -> 0x104a04: slot 8, then slot 4 0x104108
        self.apply_base()
        self.apply_base()                               # slot 4 starts with slot 8 again
        self.modL.reset(); self.fbL.set_now(self.fbL.target)
        self.modR.reset(); self.fbR.set_now(self.fbR.target)
        self.direct.set_now(self.direct.target); self.cross.set_now(self.cross.target)
