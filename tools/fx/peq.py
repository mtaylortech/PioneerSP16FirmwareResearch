# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python model of the TORAIZ SP-16 1.60 ParametricEqualizer ("2-band EQ") insert effect (Insert index 2, Master/Send
index 4), slot 25 (0x10ae70) and its parameter path.

Own re-implementation written from the analysis in docs/effects/parametric-eq.md. It contains no firmware bytes. It reuses the
shared-block models of lofi.py (LinearParameter, SignalGate, IirLpf/Hpf2ndOrder biquad, NEON helpers) and mmf.py (GainRamp),
and fdlibm_powf.py for the single-precision powf/log10f of the glibc 2.13 libm the 1.60 code calls (not correctly rounded).

Signal flow per block (all addresses 1.60):
  10ae70  apply changed parameters (10a4f0) -> band 1 (10c208 on [+0x498]) -> band 2 (10c208 on [+0x49c]) -> slot 26 (dry 0, wet 1)
  10c208  one EQ band: ramp setup (10abdc) -> stepped glide of frequency (x1000^(1/250) per step), Q (x10^0.02 per step) and
          gain (+-0.04 dB per step), one step per 44.1 samples -> the current stage's filter -> the band's GainRamp (44-sample
          linear ramps) -> the band's 132-sample SignalGate (type switches; jumps of > 38 freq / > 70 Q / > 250 gain steps).
          Stages (BANDxTYPE):
             0  LowShelvingFilter (IirFilter2, vt 0x83bcc0) with +gain dB, output gain 1
             1  LowShelvingFilter with -gain dB, output gain 10^(gain/20)  (= a high shelf)
             2  PeakingFilter (IirFilter2, vt 0x83bcf0) with +gain dB, output gain 1
             3  IirLpf2ndOrder (vt 0x840c28), output gain 10^(gain/20)
             4  IirHpf2ndOrder (vt 0x840c48), output gain 10^(gain/20)
             5  (ctor default) no stage object: the 1.60 code dereferences a null stage -> not a valid running state
Usage:
  m = PEQ(); m.insert_defaults(); m.set_param(idx, value); L, R = m.process(L, R)   (lists of floats, one block)
"""
import math
from lofi import F, EPS, FS, Param, SignalGate, Biquad, near, rnd, nmul, nadd, nsub, vmul_block
import mmf
import fdlibm_powf as FL

PARAM_NAMES = ["B1FREQUENCY", "B1GAIN", "B1Q", "B2FREQUENCY", "B2GAIN", "B2Q", "BAND1TYPE", "BAND2TYPE"]   # slot-14 index
CTOR_VALUES = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 5, 5]          # ctor 0x10baec "last" values (emulated readback)
INSERT_DEFAULTS = {0: 0.566, 1: 2.0 / 3.0, 2: 6.0 / 99.0, 3: 0.566, 4: 2.0 / 3.0, 5: 6.0 / 99.0, 6: 0.0, 7: 1.0}   # slot 52 case 2 (emulated)
TYPE_NAMES = ["low shelf", "high shelf (low shelf -g, out +g)", "peaking", "LPF 12 dB + gain", "HPF 12 dB + gain"]

# .init_array entry 0x13aa8: step multipliers (0xf52f00/04/08/0c)
M_F = FL.powf(10.0, F(0.012)); M_FI = F(F(1.0) / M_F)        # frequency: 10^(3/250) = 1000^(1/250) per step
M_Q = FL.powf(10.0, F(0.02)); M_QI = F(F(1.0) / M_Q)         # Q: 10^(1/50) per step
MIN_FC = F(5.0)                                              # data word 0x83bc40 (IirFilter stages only)
PI = 3.141592653589793; INV_TWO_PI = 0.15915494309189535; TWO_PI = 6.283185307179586


def trunc_s32(x):                                            # vcvt.s32.f32 (round toward zero)
    return int(x)


class IirFilter2:
    """IirFilter2 (0x90 bytes, base ctor 0xe2df0): LowShelvingFilter (vt 0x83bcc0, ctor 0xe311c, coefs 0xe2540) or
    PeakingFilter (vt 0x83bcf0, ctor 0xe30e4, coefs 0xe2440). Slot 6 0xe2ab4 = configure; slot 2 0xe34d8 -> slot 8 0xe27b8
    = process (NEON, L/R lanes, DF-I, 4-deep tap history, re-seed on flag +0x78)."""
    def __init__(self, kind, fs):
        self.kind = kind                                     # 'lowshelf' or 'peaking'
        self.fs = fs
        nyq = F(float(int(fs / 2)))
        self.fc_min = F(1.0); self.fc_max = nyq              # +0xc / +0x10
        self.fc = F(F(nyq + F(1.0)) * F(0.5))                # +8 (ctor, kept if inside the limits)
        self.Q = 0.7071067811865476                          # +0x18 (double); limits +0x20 0.01, +0x28 20
        self.Q_min = 0.01; self.Q_max = 20.0
        self.p = 0.0; self.p_min = -1.0; self.p_max = 100.0  # +0x38 (= V - 1), limits +0x40 / +0x48
        self.gdb = 0.0; self.g_min = -80.0; self.g_max = 40.0   # +0x58, limits +0x60 / +0x68
        self.flag78 = 0
        z = lambda: [F(0), F(0)]
        self.x = [z(), z(), z(), z()]; self.y = [z(), z(), z(), z()]   # +0x7c..+0x88: {x_k, y_k} per lane
        self.b0 = self.b1 = self.b2 = self.a1 = self.a2 = F(0)          # [+0x8c]

    def configure(self, fc, Q, gdb, flag):                   # slot 6 0xe2ab4
        fc = F(fc)
        if not fc < self.fc_min and fc <= self.fc_max: self.fc = fc
        if not Q < self.Q_min and Q <= self.Q_max: self.Q = Q
        if not gdb < self.g_min and gdb <= self.g_max: self.gdb = gdb
        p = math.pow(10.0, gdb / 20.0) - 1.0
        if not p < self.p_min and p <= self.p_max: self.p = p
        else: p = self.p
        self.coefs(self.fc, self.Q, p, F(float(self.fs)))
        self.flag78 = flag

    def coefs(self, fc, Q, p, fs):                           # slot 9: 0xe2540 / 0xe2440 (double math, float32 stores)
        t = math.tan(float(fc) * (PI / float(fs)))
        K = (t * INV_TWO_PI) * TWO_PI
        iq = 1.0 / Q
        if self.kind == "lowshelf":
            V = p + 1.0; sv = math.sqrt(V)
            K2 = K * K; K2x2 = K2 + K2
            kq = K * iq
            nrm = 1.0 / ((kq + 1.0) + K2)
            s = (sv * K) * iq
            VK2 = K2 * V
            b1n = K2x2 * V - 2.0
            b0n = (s + 1.0) + VK2
            b2n = VK2 + (1.0 - s)
            a1n = K2x2 - 2.0
            a2n = (1.0 - kq) + K2
            self.b0 = F(b0n * nrm); self.b1 = F(b1n * nrm); self.b2 = F(b2n * nrm)
            self.a1 = F(a1n * nrm); self.a2 = F(a2n * nrm)
        else:
            kq = K * iq; K2 = K * K
            nrm = 1.0 / ((kq + 1.0) + K2)
            V = p + 1.0
            vk = (V * K) * iq
            K2x2 = K2 + K2
            a2n = (1.0 - kq) + K2
            a1n = K2x2 - 2.0
            b0n = (vk + 1.0) + K2
            b2n = (1.0 - vk) + K2
            self.b0 = F(b0n * nrm); self.a1 = F(a1n * nrm); self.b1 = self.a1
            self.b2 = F(b2n * nrm); self.a2 = F(a2n * nrm)

    def process(self, L, R, i0, n):                          # 0xe27b8
        b0, b1, b2, a1, a2 = self.b0, self.b1, self.b2, self.a1, self.a2
        for ch, buf in ((0, L), (1, R)):
            x1, x2, x3, x4 = (self.x[i][ch] for i in range(4))
            y1, y2, y3, y4 = (self.y[i][ch] for i in range(4))
            if self.flag78 and self.Q > 0:                   # re-filter the last 4 inputs with the new coefficients
                y4 = nmul(b0, x4)
                y3 = nsub(nadd(nmul(b0, x3), nmul(b1, x4)), nmul(a1, y4))
                y2 = nsub(nsub(nadd(nadd(nmul(b0, x2), nmul(b1, x3)), nmul(b2, x4)), nmul(a1, y3)), nmul(a2, y4))
                y1 = nsub(nsub(nadd(nadd(nmul(b0, x1), nmul(b1, x2)), nmul(b2, x3)), nmul(a1, y2)), nmul(a2, y3))
            for j in range(n):
                x = buf[i0 + j]
                o = nmul(b0, x)
                o = nadd(o, nmul(b1, x1)); o = nadd(o, nmul(b2, x2))
                o = nsub(o, nmul(a1, y1)); o = nsub(o, nmul(a2, y2))
                buf[i0 + j] = o
                x4, x3, x2, x1 = x3, x2, x1, x
                y4, y3, y2, y1 = y3, y2, y1, o
            for i, (a, b) in enumerate(((x1, y1), (x2, y2), (x3, y3), (x4, y4))):
                self.x[i][ch] = a; self.y[i][ch] = b
        self.flag78 = 0


class GainRamp(mmf.GainRamp):
    """GainRamp (0x24 bytes, ctor 0xe8900(obj, 44, 1.0) here); setTarget 0xe895c, setNow 0xe9358, process 0xe89f0."""
    def set_now(self, g):                                    # 0xe9358
        g = F(g); self.rem = 0; self.state = 0; self.cur = g; self.target = g; self.inc = F(0); self.idle = 1

    def process_at(self, L, R, i0, n):                       # 0xe89f0 on L+i0 / R+i0
        if n <= 0: return
        if i0 == 0:
            self.process(L, R, n); return
        tl = L[i0:i0 + n]; tr = R[i0:i0 + n]
        self.process(tl, tr, n)
        L[i0:i0 + n] = tl; R[i0:i0 + n] = tr


def gain_lin(gdb):                                           # (float)pow(10, (double)(gdb * 0.05f))
    return F(math.pow(10.0, float(F(F(gdb) * F(0.05)))))


class Stage:
    """0x10-byte stage (ctor 0x10a928(stage, fs, gainramp, kind)): +0 IirFilter (kinds 3, 4), +4 IirFilter2 (kinds 0..2),
    +8 the band's GainRamp, +0xc kind."""
    def __init__(self, kind, fs, gain):
        self.kind = kind; self.gain = gain
        if kind in (0, 1): self.f = IirFilter2("lowshelf", fs)
        elif kind == 2: self.f = IirFilter2("peaking", fs)
        elif kind == 3: self.f = Biquad("lpf", fs)
        else: self.f = Biquad("hpf", fs)

    def configure(self, fc, qc, gc, flag, swap=False):
        """Step path (10c3a4..10c4c4 / 10c64c..10c754) and swap path (10c0f0..10c1f8)."""
        k = self.kind; f = self.f
        if k in (0, 2):
            f.configure(fc, float(qc), float(gc), flag); self.gain.set_target(F(1.0), 1, 0); return
        if k == 1:
            f.configure(fc, float(qc), -float(gc), flag)
        else:
            v = f.nyq
            if fc <= v: v = fc
            c = MIN_FC
            if c <= v: c = v
            f.Q = float(qc); f.fc = c
            f.coefs(); f.flag48 = flag
        g = gain_lin(gc)
        if swap: self.gain.set_now(g)
        else: self.gain.set_target(g, 1, 0)

    def process(self, L, R, i0, n):
        self.f.process(L, R, i0, n)
        self.gain.process_at(L, R, i0, n)


class Band:
    """One EQ band, 0x64 bytes (ctor 0x10afd4), process 0x10c208."""
    def __init__(self, fs=FS):
        self.gain = GainRamp(44, 1.0)                        # +0x10
        self.st = [Stage(k, fs, self.gain) for k in range(5)]   # +0/+4/+8 vector (count 5)
        self.gate = SignalGate(fs, rnd(F(F(F(fs) * F(0.001)) * F(3.0))))   # +0xc, built closed
        self.pending = 0; self.cur = 0                       # +0x14 / +0x18
        self.ft = self.fc = F(1000.0); self.fmult = M_F; self.fsteps = 0      # +0x1c / +0x20 / +0x24 / +0x2c
        self.qt = self.qc = F(0.7); self.qmult = M_Q; self.qsteps = 0         # +0x30 / +0x34 / +0x38 / +0x40
        self.gt = self.gc = F(0.0); self.gstep = F(0.04); self.gsteps = 0     # +0x44 / +0x48 / +0x4c / +0x54
        self.next = F(0.0); self.maxsteps = 0                # +0x58 / +0x5c
        self.flag60 = 0; self.flag61 = 0; self.dirty62 = 0   # bytes +0x60 recompute, +0x61 step now, +0x62 dirty

    def stage(self):
        if not 0 <= self.cur < len(self.st):
            raise RuntimeError("band type %d has no stage object (null dereference in 1.60 0x10c208)" % self.cur)
        return self.st[self.cur]

    # -- parameter setters (inline in 0x10a4f0) --
    def set_freq(self, v):
        self.ft = F(FL.powf(1000.0, v) * F(20.0)); self.dirty62 = 1; self.flag61 = 1 if self.fsteps == 0 else 0
    def set_gain(self, v):
        self.flag61 = 1 if self.gsteps == 0 else self.flag61; self.dirty62 = 1
        self.gt = F(F(F(v) * F(45.0)) - F(30.0))
    def set_q(self, v):
        self.flag61 = 1 if self.qsteps == 0 else self.flag61; self.dirty62 = 1
        self.qt = F(F(0.1) + F(F(v) * F(9.9)))
    def set_type(self, v):
        t = rnd(v); self.pending = t
        if self.cur != t: self.gate.close()

    def ramp_setup(self):                                    # 0x10abdc
        if self.dirty62:
            self.fsteps = trunc_s32(abs(F(F(F(1.0) / FL.log10f(M_F)) * FL.log10f(F(self.ft / self.fc))))) + 1
            self.fmult = M_F if self.ft > self.fc else M_FI
            self.qsteps = trunc_s32(abs(F(F(F(1.0) / FL.log10f(M_Q)) * FL.log10f(F(self.qt / self.qc))))) + 1
            self.qmult = M_Q if self.qt > self.qc else M_QI
            self.next = F(44.1); self.dirty62 = 0
            self.gsteps = trunc_s32(F(abs(F(self.gt - self.gc)) * F(25.0))) + 1
            self.gstep = F(0.04) if self.gt > self.gc else F(-0.04)
        self.maxsteps = max(self.fsteps, self.qsteps, self.gsteps)
        if self.fsteps > 38 or self.qsteps > 70 or self.gsteps > 250:
            self.gate.close()

    def _step(self):
        if self.fsteps > 1: self.fsteps -= 1; self.fc = F(self.fc * self.fmult)
        else: self.fsteps = 0; self.fc = self.ft
        if self.qsteps > 1: self.qsteps -= 1; self.qc = F(self.qc * self.qmult)
        else: self.qsteps = 0; self.qc = self.qt
        if self.gsteps > 1: self.gsteps -= 1; self.gc = F(self.gc + self.gstep)
        else: self.gsteps = 0; self.gc = self.gt

    def _swap(self):                                         # 0x10c070
        self.fsteps = self.qsteps = self.gsteps = self.maxsteps = 0
        self.fc = self.ft; self.qc = self.qt; self.gc = self.gt
        self.cur = self.pending
        if 0 <= self.cur < len(self.st):
            self.st[self.cur].configure(self.ft, self.qt, self.gt, 1, swap=True)
        self.gate.open()

    def process(self, L, R, n):                              # 0x10c208, in place on lists L, R
        self.ramp_setup()
        r = self.gate.r
        if r.state == 1:
            if near(r.target, self.gate.off):                # fading out (type switch or large jump)
                rem = r.rem
                if n < rem:
                    self.stage().process(L, R, 0, n); self.gate.apply(L, R, 0, n); return
                self.stage().process(L, R, 0, rem); self.gate.apply(L, R, 0, rem)
                self._swap()
                self.stage().process(L, R, rem, n - rem); self.gate.apply(L, R, rem, n - rem); return
        elif near(r.cur, self.gate.off):                     # closed: switch now; this block is NOT filtered
            self._swap(); self.gate.apply(L, R, 0, n); return
        rem = n; pos = 0
        while rem > 0:
            if self.maxsteps <= 0:
                chunk = rem; rem = 0
            else:
                if self.flag61:                              # first step taken at once after a parameter change
                    self._step()
                    self.stage().configure(self.fc, self.qc, self.gc, 0)
                    self.flag61 = 0
                s15 = self.next; r8 = rnd(s15)
                if rem < r8:
                    chunk = rem; self.next = F(s15 - F(float(rem))); rem = 0
                else:
                    chunk = r8; rem -= r8
                    self.next = F(F(s15 - F(float(r8))) + F(44.1))
                    self._step(); self.flag60 = 1
            st = self.stage()
            st.process(L, R, pos, chunk); pos += chunk
            if self.flag60:
                st.configure(self.fc, self.qc, self.gc, 0); self.flag60 = 0
        self.gate.apply(L, R, 0, n)


class PEQ:
    def __init__(self, fs=FS, block=64):
        self.fs = fs
        self.params = [Param("float", v) for v in CTOR_VALUES[:6]] + [Param("choice", CTOR_VALUES[6]),
                                                                       Param("choice", CTOR_VALUES[7])]
        self.bands = [Band(fs), Band(fs)]                    # +0x498, +0x49c
        self.wet = None; self.dry = None                     # EffectBase +0x14 / +0x10 (slot 26 0x10a4d8)

    def set_param(self, idx, v):                             # EffectBase slot 14 0x105d24
        if 0 <= idx < 8: self.params[idx].set(v); return 0
        return 3

    def insert_defaults(self):
        for i in range(8): self.set_param(i, INSERT_DEFAULTS[i])

    # formulas (also used by the harness readback checks)
    @staticmethod
    def freq_hz(v): return F(FL.powf(1000.0, F(v)) * F(20.0))
    @staticmethod
    def gain_db(v): return F(F(F(v) * F(45.0)) - F(30.0))
    @staticmethod
    def q_of(v): return F(F(0.1) + F(F(v) * F(9.9)))

    def apply_params(self):                                  # 0x10a4f0: B1F, B1G, B1Q, B2F, B2G, B2Q, TYPE1, TYPE2
        P = self.params; b1, b2 = self.bands
        for base, b in ((0, b1), (3, b2)):
            if P[base].changed(): b.set_freq(P[base].get())
            if P[base + 1].changed(): b.set_gain(P[base + 1].get())
            if P[base + 2].changed(): b.set_q(P[base + 2].get())
        if P[6].changed(): b1.set_type(P[6].get())
        if P[7].changed(): b2.set_type(P[7].get())

    def process(self, L, R):                                 # slot 25 0x10ae70; returns new lists
        L = [F(x) for x in L]; R = [F(x) for x in R]; n = len(L)
        self.apply_params()
        self.bands[0].process(L, R, n)
        self.bands[1].process(L, R, n)
        self.dry = F(0.0); self.wet = F(1.0)                 # slot 26, every block
        return [float(x) for x in L], [float(x) for x in R]
