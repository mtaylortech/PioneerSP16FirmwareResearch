# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Distortion insert effect (Insert index 6; class `Distortion`, vtable 0x842898,
built inline in the InsertFxProcessor ctor 0x118b0c, new 0x1d8; DSP kernel class `c_distortion`, vtable 0x8418a0,
ctor 0xfa568, init 0xfa36c, process 0xfa78c). Reconstructed in docs/effects/distortion.md (H035); contains no firmware bytes.

Signal flow per block (Distortion slot 25 0x115d48 -> 0xfa78c(kernel, L, R, L, R); always `block` = 64 samples, in place):
  0. if drive (+0x104) < 0 (only after a failed re-init): return 0, buffers untouched.
  1. one-pole high-pass  : lp = b*x + a*lp ; y = x - lp            (a = exp(-2 pi fc / fs), b = 1 - a; fc +0xe8, 50 Hz init)
  2. one-pole low-pass   : y = b*x + a*y                            (fc +0xfc, 20 kHz init)
  3. auto-gain ("dynamics") per sample, both channels share one gain g (+0x110, 1..100):
       L *= g, R *= g; m = max(|L|, |R|);
       m >= hi (+0x108 = T)          : g *= dec (exp(-1/(0.003 fs)), 3 ms), g >= 1, hold := reload
       lo (+0x10c = 0.70795 T) <= m  : hold := reload
       else                          : hold > 0 ? hold -= 1 : g *= inc (exp(1/(0.1 fs)), 100 ms), g <= 100
     (reload +0x11c = fs/50 = 882 samples = 20 ms). With T = 0 (Insert default) g stays 1.
  4. waveshaper per sample: x = y * drive (drive +0x104 = 10^(dB/20));
       x > 1  -> s = c = 1, w = 0;  x < -1 -> s = c = -1, w = 0;
       else   c = x^3, s = 1.5 x - 0.5 c, w = blend * (1 - |s|)^3     (blend +0x134 = clamp(dB/20, 0, 1))
       out = 0.7 * (w * c + (1 - w) * s)       i.e. soft clip, blended towards the raw cube x^3 at low levels.
  5. one-pole low-pass (output, fc +0xd4, 20 kHz init): y = b*x + a*y.
  6. slot 26 0x115bc4 does nothing; dry/wet were written by slot 14 index 5 (EffectBase +0x10 = 1 - v, +0x14 = v).
Parameters through slot 14 0x1164d8 (all applied immediately; the kernel setters skip unchanged values):
  0 DRIVE  : dB = 40 v -> kernel 0xfa614: drive = powf(10, dB * 0.05), blend = clamp(dB * 0.05, 0, 1)
  1 (out LPF), 2 (HPF), 3 (pre LPF): f = (float)(20 * pow(10.0, (double)(3 v))) -> kernel slots 5 / 6 / 7, cutoff clamped
    to [50, 20000] Hz, coefficient a = expf((f * -2 pi) * (1/fs))
  4 threshold T (raw v) -> kernel slot 8: v < 0 -> 0, v > 1 -> 1; hi = T, lo = T * 0.70794576 (-3 dB)
  5 MIXRATIO -> kernel slot 9 (100.0, unused) and EffectBase dry = 1 - v, wet = v.
The kernel's oscillator (+0x28) is constructed (sine, 1 Hz) and never run.
All float32 arithmetic is scalar VFP (FPSCR = 0, no flush-to-zero), modelled with F() (round to nearest even).
libm: expf = glibc 2.13 algorithm (glibc_expf.py; its two tables are read at run time from the local 1.60 libm with
glibc_expf.load_tables(), otherwise it falls back to the correctly rounded crmath.expf, which differs in ~1/3000 arguments);
double pow(10, y) correctly rounded via decimal (the 1.60 glibc dbl-64 pow is correctly rounded; the host's is not always);
powf = fdlibm (fdlibm_powf).
"""
from decimal import Decimal as _D, localcontext as _lc
from osc import Osc, OwnLibm, F, fbits
import glibc_expf as GE
from fdlibm_powf import powf

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "DRIVE", 1: "OUT_LPF(TONE?)", 2: "HPF(LO FREQ?)", 3: "PRE_LPF(HI FREQ?)", 4: "DYNAMICS(threshold)", 5: "MIXRATIO"}
K_TENTH = F(0.1)                   # 0x3dcccccd
K_LO0 = fbits(0x3d90fcbf)          # init low threshold (0.1 * 0.70794576, as stored by init)
K_M3DB = fbits(0x3f353bef)         # 0.70794576 = 10^(-3/20)
K_3MS = fbits(0x3b449ba6)          # 0.003
K_HUNDREDTH = F(0.01)              # 0x3c23d70a
K_W20K = fbits(0xc7f56fdb)         # -125663.71 = -2 pi * 20000 (init only)
K_W50 = fbits(0xc39d1463)          # -314.15927 = -2 pi * 50 (init only)
K_M2PI = fbits(0xc0c90fdb)         # -6.2831855 (setters)
K_FMIN = F(50.0); K_FMAX = F(20000.0)
K_GMAX = F(100.0)
K_07 = fbits(0x3f333333)           # 0.7
K_005 = fbits(0x3d4ccccd)          # 0.05
K_40 = F(40.0)
K_HALFN = F(-0.5); K_15 = F(1.5)


def pow10_cr(y):
    """Correctly rounded double 10**y (the 1.60 glibc pow is correctly rounded)."""
    with _lc() as c:
        c.prec = 60
        return float(_D(10) ** _D(y))


def freq_of(v):
    """Slot 14 indices 1..3: (float)(20.0 * pow(10.0, (double)F(3 v))) in double."""
    return F(20.0 * pow10_cr(float(F(F(v) * F(3.0)))))


class Kernel:
    """c_distortion (0x138 bytes). Field names follow the 1.60 offsets."""
    def __init__(self, block=BLOCK, fs=FS, id_counter=1, libm=None):
        self.fs = fs; self.block = block                                    # +0x04 / +0x08
        self.osc, _ = Osc.ctor(0, 1.0, 44100, id_counter, libm=libm or OwnLibm())   # +0x28, never run
        self.e130 = 0
        self.init(block, fs)

    def init(self, block, fs):
        """0xfa36c (also kernel slot 2 0xfa4f4 when block > 0 and fs > 0): full re-initialisation."""
        fsf = F(float(fs))
        self.n = block                                                      # +0x100
        self.hi = K_TENTH; self.lo = K_LO0                                  # +0x108 / +0x10c
        self.drive = F(1.0); self.g = F(1.0)                                # +0x104 / +0x110
        self.inc = GE.expf(F(F(1.0) / F(fsf * K_TENTH)))                    # +0x114
        self.dec = GE.expf(F(F(-1.0) / F(fsf * K_3MS)))                     # +0x118
        self.x124 = F(0.0); self.x128 = F(0.0); self.blend = F(0.0); self.e130 = 0   # +0x124 / +0x128 / +0x134 / +0x130
        self.fc_out = K_FMAX                                                # +0xd4
        q = abs(fs) // 50
        self.reload = q if fs >= 0 else -q                                  # +0x11c (C division)
        self.hold = self.reload                                             # +0x120
        self.inv_fs = F(F(1.0) / fsf)                                       # +0xc0
        self.x12c = F(F(1.0) / F(fsf * K_HUNDREDTH))                        # +0x12c (unused by process)
        self.a_out = GE.expf(F(self.inv_fs * K_W20K)); self.b_out = F(F(1.0) - self.a_out)   # +0xc4 / +0xc8
        self.z_out = [F(0.0), F(0.0)]                                       # +0xcc / +0xd0
        self.fc_hp = K_FMIN                                                 # +0xe8
        self.a_hp = GE.expf(F(self.inv_fs * K_W50)); self.b_hp = F(F(1.0) - self.a_hp)       # +0xd8 / +0xdc
        self.z_hp = [F(0.0), F(0.0)]                                        # +0xe0 / +0xe4
        self.fc_pre = K_FMAX                                                # +0xfc
        self.a_pre = GE.expf(F(self.inv_fs * K_W20K)); self.b_pre = F(F(1.0) - self.a_pre)   # +0xec / +0xf0
        self.z_pre = [F(0.0), F(0.0)]                                       # +0xf4 / +0xf8
        self.p_drive = F(0.0); self.p_out = K_FMAX; self.p_hp = K_FMIN; self.p_pre = K_FMAX  # +0x0c/+0x10/+0x14/+0x18
        self.p_thr = K_TENTH; self.p_x20 = F(0.0)                           # +0x1c / +0x20
        return 1

    def reinit(self, block, fs):
        """Kernel slot 2 0xfa4f4."""
        if block > 0 and fs > 0: return self.init(block, fs)
        self.drive = F(-1.0); return 0

    # --- setters (vtable slots) -----------------------------------------------------------------------------------
    def set_drive_db(self, p):
        """0xfa614 (non-virtual, from slot 14 index 0)."""
        p = F(p)
        if self.p_drive == p: return self.p_drive
        e = F(p * K_005)
        self.drive = powf(F(10.0), e)
        self.blend = F(0.0)
        if p > 0.0:
            self.blend = e
            if e > 1.0: self.blend = F(1.0)
        self.p_drive = p
        return p

    def _cutoff(self, attr_p, attr_fc, attr_a, attr_b, v):
        """Slots 5/6/7: skip if unchanged; cutoff field = v clamped to [50, 20000] (a NaN v is stored raw and its
        coefficient computed from 20000); a = expf((fc * -2 pi) * (1/fs)), b = 1 - a; change copy = raw v."""
        v = F(v)
        if getattr(self, attr_p) == v: return getattr(self, attr_p)
        stored = v
        if v < K_FMIN: fc = stored = K_FMIN
        elif v > K_FMAX: fc = stored = K_FMAX
        elif v <= K_FMAX: fc = v
        else: fc = K_FMAX
        setattr(self, attr_fc, stored)
        a = GE.expf(F(F(fc * K_M2PI) * self.inv_fs))
        setattr(self, attr_p, v); setattr(self, attr_a, a); setattr(self, attr_b, F(F(1.0) - a))
        return v

    def set_out_lpf(self, v): return self._cutoff("p_out", "fc_out", "a_out", "b_out", v)     # slot 5 0xfa2d0
    def set_hpf(self, v): return self._cutoff("p_hp", "fc_hp", "a_hp", "b_hp", v)             # slot 6 0xfa234
    def set_pre_lpf(self, v): return self._cutoff("p_pre", "fc_pre", "a_pre", "b_pre", v)     # slot 7 0xfa198

    def set_threshold(self, v):
        """Slot 8 0xfa07c."""
        v = F(v)
        if self.p_thr == v: return self.p_thr
        if v < 0.0: hi = lo = F(0.0)
        elif v > 1.0: hi = F(1.0); lo = K_M3DB
        else: hi = v; lo = F(v * K_M3DB)
        self.hi = hi; self.lo = lo; self.p_thr = hi
        return hi

    def set_x20(self, v):
        """Slot 9 0xfa0e8 (Distortion always passes 100.0): +0x20 = clamp(v, 0, 100), +0x124 = that / 100 (unused)."""
        v = F(v)
        if self.p_x20 == v: return self.p_x20
        if v < 0.0: s15 = s14 = F(0.0)
        elif v > 100.0: s15 = K_GMAX; s14 = F(1.0)
        else: s15 = v; s14 = F(v * K_HUNDREDTH)
        self.x124 = s14; self.p_x20 = s15
        return s15

    def set_e130(self, on):
        """Slots 16 / 17 0xfa154 / 0xfa174 (byte +0x130, never read by process)."""
        if self.drive < 0.0: return 0
        self.e130 = 1 if on else 0; return 1

    # --- process -----------------------------------------------------------------------------------------------------
    def process(self, L, R):
        """0xfa78c(kernel, L, R, L, R): in place on the first `n` samples of L and R."""
        if self.drive < 0.0: return 0
        n = self.n
        if n < 1: return 1
        a, b = self.a_hp, self.b_hp; zl, zr = self.z_hp
        for i in range(n):
            zl = F(F(b * L[i]) + F(a * zl)); L[i] = F(L[i] - zl)
            zr = F(F(b * R[i]) + F(a * zr)); R[i] = F(R[i] - zr)
        self.z_hp = [zl, zr]
        a, b = self.a_pre, self.b_pre; yl, yr = self.z_pre
        for i in range(n):
            yl = F(F(b * L[i]) + F(a * yl)); L[i] = yl
            yr = F(F(b * R[i]) + F(a * yr)); R[i] = yr
        self.z_pre = [yl, yr]
        g = self.g; hold = self.hold; hi, lo, inc, dec, reload = self.hi, self.lo, self.inc, self.dec, self.reload
        for i in range(n):
            L[i] = F(L[i] * g); R[i] = F(R[i] * g)
            m = abs(L[i]); r = abs(R[i])
            if m < r: m = r
            if m >= hi:
                g = F(g * dec); hold = reload
                if g < 1.0: g = F(1.0)
            elif m >= lo:
                hold = reload
            elif hold > 0:
                hold -= 1
            else:
                g = F(g * inc)
                if g > K_GMAX: g = K_GMAX
        self.g = g; self.hold = hold
        d, bl = self.drive, self.blend
        for buf in (L, R):
            for i in range(n):
                buf[i] = self.shape(buf[i], d, bl)
        a, b = self.a_out, self.b_out; yl, yr = self.z_out
        for i in range(n):
            yl = F(F(b * L[i]) + F(a * yl)); L[i] = yl
            yr = F(F(b * R[i]) + F(a * yr)); R[i] = yr
        self.z_out = [yl, yr]
        return 1

    @staticmethod
    def shape(y, drive, blend):
        x = F(y * drive)
        if x > 1.0:
            s = c = F(1.0); t = F(0.0)
        elif x < -1.0:
            s = c = F(-1.0); t = F(0.0)
        else:
            c = F(x * F(x * x))
            s = F(F(c * K_HALFN) + F(x * K_15))
            t = F(F(1.0) - s) if not (s < 0.0) else F(s + F(1.0))
            t = F(t * F(t * t))
        w = F(blend * t)
        return F(F(F(w * c) + F(F(F(1.0) - w) * s)) * K_07)


class Distortion:
    """The Distortion effect object (0x1d8 bytes): EffectBase + kernel pointer +0x1b8 + six stored parameter values."""
    def __init__(self, block=BLOCK, fs=FS, id_counter=1, libm=None):
        self.k = Kernel(block, fs, id_counter, libm)
        self.dry = F(1.0); self.wet = F(0.0)          # EffectBase +0x10 / +0x14 (EffectBase ctor values; overwritten by index 5)
        # +0x1bc..+0x1d0: stored slot-14 values; the inline ctor block writes three 8-byte pairs (values set by harness)
        self.pv = [F(0.0)] * 6

    def set_param(self, idx, v):
        """Slot 14 0x1164d8. Always returns 0."""
        v = F(v); k = self.k
        if idx == 0:
            k.set_drive_db(F(v * K_40))
        elif idx in (1, 2, 3):
            f = freq_of(v)
            (k.set_out_lpf, k.set_hpf, k.set_pre_lpf)[idx - 1](f)
        elif idx == 4:
            k.set_threshold(v)
        elif idx == 5:
            k.set_x20(K_GMAX)
            self.wet = v; self.dry = F(F(1.0) - v)
        else:
            return 0
        self.pv[idx] = v
        return 0

    def get_param(self, idx):
        """Slot 15 0x115a78: stored value (0..5), else 0."""
        return self.pv[idx] if 0 <= idx <= 5 else F(0.0)

    def reset(self):
        """Slot 27 0x115b0c: kernel slot 2 (64, 44100) = full kernel re-init, then slot 14 (i, stored value) for i = 0..5."""
        self.k.reinit(64, 44100)
        for i in range(6): self.set_param(i, self.pv[i])
        return 0

    def process(self, L, R):
        """Slot 25 0x115d48 -> kernel process; returns 0 (the kernel's return value is discarded)."""
        self.k.process(L, R)
        return 0
