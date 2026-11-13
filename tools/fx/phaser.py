# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Phaser effect (Insert index 8 / Master index 9; class `Phaser`, vtable 0x8422b8,
ctor 0x10d654, slot 25 0x10d630 -> 0x10d260). Reconstructed in docs/effects/phaser.md; contains no firmware bytes.

Signal flow per block (slot 25):
  0x10d260: apply changed parameters (Rate/BPM/Sync -> oscillator period; Phase -> oscillator L/R offset), run the oscillator for n
  samples, take the oscillator value at the LAST sample of the block, map it to an all-pass coefficient target per channel
  (cubic curve in the tan domain between a low and a high corner), and interpolate the coefficient linearly across the
  block; then the stereo kernel 0x10cf40:
      s   = (1-p)*y + p*s                        (one-pole low-pass of the previous output, p = exp(-2*pi*10000/fs))
      x   = in + fb*s                            (feedback injected at the chain input)
      6 x first-order all-pass  v = x - a*z; x = a*v + z; z = v      (H(z) = (a + z^-1)/(1 + a z^-1))
      out = (in + x) * g(a)                      (dry + all-pass sum, gain 0.7 at the low corner .. 0.5 at the high one)
      y   = out
  slot 26 0x10cb48 (every block): EffectBase wet = MIXRATIO, dry = 1 - MIXRATIO.
All float32; NEON lanes (the kernel) flush denormals to zero, scalar VFP code does not (FPSCR = 0).
"""
import math
from lofi import F, Param, ftz, nmul, nadd, nsub, FLT_MIN
import fdlibm_powf as FP
import fdlibm_tanf as FT

FS = 44100
PARAM_NAMES = ["RATE", "WIDTH", "PHASE", "FREQUENCY", "FEEDBACK", "MIXRATIO", "SYNC", "BPM"]   # slot-14 index 0..7
REG_NAMES = ["Rate", "Width", "Phase", "Frequency", "Feedback", "Mixratio", "Sync", "Bpm"]       # ctor registration strings
CTOR_VALUES = [0.5, 1.0, 0.0, 0.0, 0.5, 1.0, 0, 120.0]                                          # ctor defaults ("last")
INSERT_DEFAULTS = {0: 199.0 / 999.0, 1: 1.0, 2: 0.0, 3: 1.0, 4: 0.0, 5: 0.0, 6: 0.0}           # slot 52 case 8 (emulated)
SYNC_FRACTIONS = [(64, 1), (32, 1), (16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (3, 4), (1, 2), (1, 4), (1, 8), (1, 16)]  # beats
PI_F = F(math.pi)                                  # 0x40490fdb
K_LO, K_HI = F(314.15927), F(62831.855)            # pi*100, pi*20000 (ctor literals)
FB_LP = -62831.853071795864                        # -2*pi*10000 (double literal), feedback low-pass pole exp(FB_LP/fs)
P_MIN_HZ = F(0.0044100005)                         # oscillator frequency floor


def rint(x):                                       # double + 1.5*2^52, low word: round half to even
    return int(round(float(x)))


class Toggle:
    """ToggleParameter (vtable 0x840b20): bytes last +0x24 / current +0x25 (ctor 0/0)."""
    def __init__(self, default=0):
        self.last = self.cur = int(default)
    def set(self, v):                              # slot 4 0xf0738: v >= 1 -> on, v <= 0 -> off, otherwise unchanged (ret 3)
        v = F(v)
        if v >= 1.0: self.cur = 1; return 0
        if v > 0.0 or v != v: return 3
        self.cur = 0; return 0
    def changed(self):                             # slot 2 0xf0858
        c = self.cur != self.last
        if c: self.last = self.cur
        return c
    def get(self): return self.cur                 # 0xf0814


class LFO:
    """The shared vtable-less oscillator (NOT the RTTI `LFO` class; the Python name is historical; see osc.py for all
    waveforms) (0x98 bytes, ctor 0x100af0 -> 0x100710), triangle waveform (type 1) only; amplitude +0,
    offset +4, frequency +0x10, 1/fs +0x18 (double), slope +0x20 (double), phase state +0x40 (double), R offset +0x50,
    counter +0x80, period-1 +0x84, output smoothing +0x58/+0x5c (disabled when +0x78 != 0)."""
    def __init__(self, wave=1, freq=1.0, fs=FS):
        if wave != 1: raise NotImplementedError("only the triangle oscillator (type 1) is modelled")
        self.wave = wave; self.fs = fs
        self.amp, self.off = F(1.0), F(0.0)
        self.inv_fs = 1.0 / float(fs)
        self.hold = 0.0; self.smooth_off = 0.0; self.sm = [F(0.0), F(0.0)]
        self.c58 = self.c5c = None                 # smoothing coefficients (expf; unused while smoothing is off)
        freq = F(freq)
        if freq <= P_MIN_HZ: freq = P_MIN_HZ
        P = F(F(F(float(fs)) / freq) - F(1.0))
        self.P = F(1.0) if P < 1.0 else P
        self.ph = F(0.0); self.d40 = 1.0
        self.slope = (self.inv_fs * 4.0) * float(freq)
        self.c = F(self.P * F(0.25))
        self.freq = freq

    def set_frequency(self, hz):                   # 0x101090
        hz = F(hz)
        if hz == 0.0: self.hold = 1.0; return
        Pold = self.P
        if hz <= P_MIN_HZ:
            Pn = F(9999998.0); hz = P_MIN_HZ
        else:
            Pn = F(F(F(44100.0) / hz) - F(1.0))    # literal 44100.0, not fs
            if Pn < 1.0: Pn = F(1.0)
        self.P = Pn
        self.c = F(F(Pn * self.c) / Pold)
        self.slope = (self.inv_fs * 4.0) * float(hz)
        self.freq = hz

    def set_period_ms(self, ms):                   # 0x101320
        ms = F(ms)
        if ms == 0.0: return
        self.set_frequency(F(F(1000.0) / ms))

    @staticmethod
    def _wrap(ph):
        ph = F(ph)
        while ph < 0.0: ph = F(ph + F(1.0))
        while ph >= 1.0: ph = F(ph - F(1.0))
        return ph

    def set_phase(self, ph):                       # 0x1017d4 (R-channel phase offset, cycles)
        if self.freq == 0.0: return
        self.ph = F(self._wrap(ph) * F(4.0))

    def reset_phase(self, ph):                     # 0x101440
        if self.freq == 0.0: return
        ph = self._wrap(ph)
        self.d40 = 1.0 + float(ph) * 4.0
        c = F(F(ph + F(0.25)) * self.P)
        if self.d40 >= 4.0: self.d40 -= 4.0
        if self.P < c: c = F(c - self.P)
        self.c = c

    def process(self, n):                          # 0x101bdc -> (L list, R list)
        if self.hold != 0.0: raise NotImplementedError("oscillator hold mode (+0x70) not modelled")
        P = self.P; k = F(self.slope); c = self.c
        offR = F(F(P * F(0.25)) * self.ph); half = F(P * F(0.5))
        L = [0.0] * n; R = [0.0] * n
        pos = not (k < 0.0)
        def tri(t):
            ck = F(t * k)
            if pos: return F(F(3.0) - ck) if t > half else F(ck - F(1.0))
            return F((F(3.0) if t > half else F(1.0)) + ck)
        for i in range(n):
            c = F(c + F(1.0))
            if c >= P: c = F(c - P)
            L[i] = tri(c)
            cr = F(c + offR)
            if cr >= P: cr = F(cr - P)
            R[i] = tri(cr)
        self.d40 = float(c) * float(k) if pos else -(float(c) * float(k))
        self.c = c
        for i in range(n):
            L[i] = F(self.off + F(self.amp * L[i])); R[i] = F(self.off + F(self.amp * R[i]))
        if self.smooth_off == 0.0:
            a, b = self.c58, self.c5c
            for buf, j in ((L, 0), (R, 1)):
                prev = self.sm[j]
                for i in range(n):
                    prev = F(F(a * buf[i]) + F(b * prev)); buf[i] = prev
                self.sm[j] = prev
        else:
            self.sm = [F(0.0), F(0.0)]
        return L, R


class Phaser:
    def __init__(self, fs=FS, block=64):
        self.fs = fs; self.fsf = F(float(fs)); self.block = block
        self.rc = 3 * block                                            # +0x1bc
        self.t_lo = FT.tanf(F(K_LO / self.fsf))                        # +0x1c0  tan(pi*100/fs)
        self.t_hi = FT.tanf(F(K_HI / self.fsf))                        # +0x1c4  tan(pi*20000/fs)
        self.a_lo = F(F(self.t_lo - F(1.0)) / F(self.t_lo + F(1.0)))   # +0x1c8
        self.a_hi = F(F(self.t_hi - F(1.0)) / F(self.t_hi + F(1.0)))   # +0x1cc
        self.g_hi, self.g_lo = F(0.5), F(0.7)                          # +0x1d0 / +0x1d4: gain at a_hi / a_lo
        self.p = [Param("float", v) for v in CTOR_VALUES[:6]] + [Toggle(0), Param("float", 120.0)]
        self.cntA = self.cntF = -1                                     # +0x1d8 / +0x1dc
        self.fb = F(0.0); self.y = [F(0.0), F(0.0)]
        self.a = [self.a_hi, self.a_hi]                                # +0x1ec / +0x1f0
        self.z = [[F(0.0), F(0.0)] for _ in range(6)]                  # [+0x1f4] 6 stages x (L, R)
        self.pole = F(math.exp(FB_LP / float(fs)))                     # +0x1f8
        self.pole1 = F(F(1.0) - self.pole)                             # +0x1fc
        self.s = [F(0.0), F(0.0)]                                      # +0x200
        self.lo_t, self.hi_t = self.t_lo, self.t_hi                    # +0x208 / +0x20c
        self.lfo = LFO(1, 1.0, fs)                                     # [+0x21c]
        self.lfo.reset_phase(0.25)
        self.lfo.off = F(0.5); self.lfo.amp = F(0.5); self.lfo.smooth_off = 1.0
        self.reset_flag = 0                                            # +0x4ec
        self.dry, self.wet = F(1.0), F(0.0)                            # EffectBase +0x10 / +0x14 (ctor; overwritten by slot 26)
        # ctor tail: same computations as the per-block apply (rate, phase, range, feedback, mix)
        self.update_rate()
        self.phase_v = self.p[2].get(); self.lfo.set_phase(F(self.phase_v * F(0.5)))
        self.update_range(set_count=False)
        self.fb_t = F(F(0.0) + F(self.p[4].get() * F(0.99))); self.fb = self.fb_t
        self.mix = self.p[5].get(); self.sync = self.p[6].get(); self.bpm = self.p[7].get()
        self.lfo_buf = None; self.a_target = None

    def reset(self):                                                   # slot 27 0x10cf30 -> 0x10cb78
        """Re-initialise the oscillator and state from the current parameter values (change flags are NOT consumed)."""
        self.cntA = -1
        self.update_rate(apply=False)
        ms = self.period_ms
        if ms != 0.0:
            self.lfo = LFO(1, F(F(1000.0) / ms), self.fs)              # 0x100b28 -> 0x100710 (full re-init)
        self.lfo.reset_phase(0.25)
        self.lfo.off = F(0.5); self.lfo.amp = F(0.5); self.lfo.smooth_off = 1.0
        self.phase_v = self.p[2].get(); self.lfo.set_phase(F(self.phase_v * F(0.5)))
        self.update_range(set_count=False)
        self.cntF = -1; self.y = [F(0.0), F(0.0)]
        self.fb_t = F(F(0.0) + F(self.p[4].get() * F(0.99))); self.fb = self.fb_t
        self.z = [[F(0.0), F(0.0)] for _ in range(6)]; self.s = [F(0.0), F(0.0)]
        lL, lR = self.lfo.process(1)
        lo = self.lo_t; rng = F(self.hi_t - lo); a = []
        for xv in (lL[0], lR[0]):
            w = F(lo + F(F(xv * F(xv * xv)) * rng))
            a.append(F(F(w - F(1.0)) / F(w + F(1.0))))
        self.a = a; self.reset_flag = 0

    # --- parameters ---------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                                       # EffectBase slot 14 0x105d24
        if not 0 <= idx < 8: return 3
        r = self.p[idx].set(v)
        return r if isinstance(r, int) else 0

    def insert_defaults(self):
        for k in sorted(INSERT_DEFAULTS): self.set_param(k, INSERT_DEFAULTS[k])

    def retrigger(self): self.reset_flag = 1                           # slot 10 0x10cb38

    @staticmethod
    def rate_hz(v):                                                    # Rate (free): 0x34c220/0x34c240
        return F(F(float(rint(F(F(1.0) + F(F(v) * F(999.0)))))) * F(0.01))

    @staticmethod
    def sync_index(v):                                                 # Rate (sync): 0x34c28c/0x34c2a8
        i = rint(F(F(0.0) + F(F(v) * F(11.0))))
        return i if 0 <= i <= 11 else 4

    @staticmethod
    def freq_hz(v):                                                    # Frequency: 0x34c8a8/0x34c8c8
        idx = rint(F(F(0.0) + F(F(v) * F(256.0))))
        return F(FP.powf(F(60.0), F(F(float(idx)) * F(0.00390625))) * F(300.0))

    def update_rate(self, apply=True):                                 # 0x10df00
        v = self.p[0].get(); self.sync = self.p[6].get()
        if not self.sync:
            ms = F(F(1000.0) / self.rate_hz(v))
        else:
            num, den = SYNC_FRACTIONS[self.sync_index(v)]
            self.bpm = self.p[7].get()
            ms = F(F(F(F(60000.0) / self.bpm) * F(float(num))) / F(float(den)))
        self.period_ms = ms                                            # +0x4cc
        if apply: self.lfo.set_period_ms(ms)

    def update_range(self, set_count=True):                            # inline in 0x10d260 (also ctor, slot 27)
        self.width = self.p[1].get(); self.freq_v = self.p[3].get()
        f = self.freq_hz(self.freq_v)
        hi = FT.tanf(F(F(f * PI_F) / self.fsf))
        self.hi_t = self.t_hi if self.t_hi < hi else hi
        u = F(F(1.0) - self.width)
        lo_f = F(f - F(F(F(1.0) - F(u * u)) * F(f - F(100.0))))
        lo = FT.tanf(F(F(lo_f * PI_F) / self.fsf))
        if set_count: self.cntA = self.rc
        self.lo_t = self.t_lo if self.t_lo > lo else lo
        self.f_hi_hz, self.f_lo_hz = f, lo_f

    # --- processing ---------------------------------------------------------------------------------------------
    def kernel(self, L, R, dfb, da, n):                                # 0x10cf40 (NEON, 2 lanes)
        fb = self.fb; a = list(self.a); y = list(self.y); s = list(self.s); z = self.z
        inv = F(F(1.0) / F(self.a_hi - self.a_lo)); diff = F(self.g_lo - self.g_hi)
        for i in range(n):
            fb = F(fb + dfb)
            for j, buf in ((0, L), (1, R)):
                t1 = nmul(y[j], self.pole1); t2 = nmul(s[j], self.pole)
                a[j] = nadd(a[j], da[j])
                s[j] = nadd(t1, t2)
                xin = buf[i]
                x = nadd(nmul(s[j], fb), xin)
                g = nsub(self.g_lo, nmul(nmul(nsub(a[j], self.a_lo), inv), diff))
                for k in range(len(z)):                                # 6 stages
                    zk = z[k][j]
                    v = nsub(x, nmul(a[j], zk))
                    x = nadd(nmul(a[j], v), zk)
                    z[k][j] = v
                out = nmul(nadd(xin, x), g)
                buf[i] = out; y[j] = out
        self.fb = fb; self.a = a; self.y = y; self.s = s

    def process(self, L, R):                                           # slot 25 0x10d630; returns new lists
        L = [F(v) for v in L]; R = [F(v) for v in R]; n = len(L)
        P = self.p
        if self.reset_flag:
            self.lfo.reset_phase(0.25); self.reset_flag = 0
        if P[0].changed() or P[7].changed() or P[6].changed():         # short-circuit order as 0x10d290..0x10d578
            self.update_rate(); self.cntA = self.rc
        if P[2].changed():
            self.phase_v = P[2].get(); self.lfo.set_phase(F(self.phase_v * F(0.5))); self.cntA = self.rc
        lL, lR = self.lfo.process(n)
        self.lfo_buf = (lL, lR)
        if P[3].changed() or P[1].changed():
            self.update_range()
        lo = self.lo_t; rng = F(self.hi_t - lo)
        r3 = F(F(lR[-1] * lR[-1]) * lR[-1]); l3 = F(F(lL[-1] * lL[-1]) * lL[-1])
        wR = F(lo + F(rng * r3)); wL = F(lo + F(l3 * rng))
        aR = F(F(wR - F(1.0)) / F(wR + F(1.0))); aL = F(F(wL - F(1.0)) / F(wL + F(1.0)))
        div = F(float(self.cntA)) if self.cntA > 0 else F(float(n))
        da = (F(F(aL - self.a[0]) / div), F(F(aR - self.a[1]) / div))
        self.a_target = (aL, aR)
        if P[4].changed():
            self.fb_t = F(F(0.0) + F(P[4].get() * F(0.99))); self.cntF = self.rc
        dfb = F(F(self.fb_t - self.fb) / F(float(self.cntF))) if self.cntF > 0 else F(0.0)
        self.kernel(L, R, dfb, da, n)
        if self.cntA > 0:
            self.cntA -= n
            if self.cntA <= 0: self.a = [aL, aR]
        if self.cntF > 0:
            self.cntF -= n
            if self.cntF <= 0: self.fb = self.fb_t
        self.mix = P[5].get(); self.wet = self.mix; self.dry = F(F(1.0) - self.mix)   # slot 26 0x10cb48
        return L, R
