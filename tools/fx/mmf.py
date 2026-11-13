# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python model of the TORAIZ SP-16 1.60 MultiModeFilter insert effect (Insert index 3, Master/Send index 5), slot 25
(0x108ee4) and its parameter path.

Own re-implementation written from the analysis in docs/effects/multimode-filter.md. It contains no firmware bytes. It reuses the
shared-block models of lofi.py (LinearParameter, SignalGate/SmoothFloat, IirFilter HPF/LPF/BPF biquad, NEON
vector multiply), because MMF instantiates the same 1.60 classes (vtables 0x840ac8, 0x840e40, 0x840c28/0x840c48/0x841918).
Arithmetic mirrors the 1.60 code's precision (float32 VFP steps, float64 where the code uses double, NEON flush-to-zero).

Signal flow per block (all addresses 1.60):
  108ee4  apply changed parameters (107d18) -> filter container (108808) -> output gain ramp (e89f0) -> slot 26 if MIXRATIO changed
  108808  cutoff / Q exponential step ramp (one step per 44.1 samples; cutoff step multiplier 1000^(1/G), G = 64..576 from GLIDE),
          sub-filter "wrapper" of the current kind:
             kind 0/1/2 = one LPF / HPF / BPF biquad (12 dB/oct), Q as set
             kind 3/4/5 = two identical cascaded LPF / HPF / BPF biquads (24 dB/oct), each with Q' = sqrt(Q)
             kind 6     = no filter
          and its own 132-sample SignalGate for kind switches and large cutoff jumps (only when GLIDE = 0).
  e89f0   output gain: linear ramp to the new GAIN target over 132 samples (VFP), else multiply by the current gain (NEON).
Usage:
  m = MMF(); m.insert_defaults(); m.set_param(idx, value); L, R = m.process(L, R)   (lists of floats, one block)
"""
import math
from lofi import F, EPS, FS, Param, SignalGate, Biquad, vmul_block, near, rnd, log10f, G3, G4

PARAM_NAMES = ["CUTOFF", "GAIN", "Q", "GLIDE", "NONE", "MIXRATIO", "FILTERTYPE", "FILTERDB"]   # slot-14 index 0..7
# ctor "last" (= current) values, from the 1.60 ctor 0x109e8c (emulated readback); float kinds 0..5, choice kinds 6..7
CTOR_VALUES = [0.5, 0.5, 0.5, 0.0, 0.0, 0.0, 6, 0]
# Insert defaults (InsertFxProcessor slot 52, case 3; emulated readback)
# GAIN = float32(2/3) -> 0 dB; Q = float32(5/98) -> 0.2 + 9.8 * 5/98 = 0.7 (float32 0x3f333333)
INSERT_DEFAULTS = {0: 0.566, 1: 2.0 / 3.0, 2: 5.0 / 98.0, 3: 0.0, 4: 0.0, 5: 1.0, 6: 0.0, 7: 1.0}
APPLY_ORDER_DEFAULTS = (0, 1, 2, 3, 4, 5, 6, 7)
KIND_NAMES = ["LPF 12 dB", "HPF 12 dB", "BPF 12 dB", "LPF 24 dB", "HPF 24 dB", "BPF 24 dB", "off"]
MIN_FC = F(5.0)                                   # data word 0x83bc40


def kind_of(t, db):
    """0x107c24: FILTERTYPE t (0 LPF, 1 HPF, 2 BPF, other = off) and FILTERDB db (1 = single biquad, other = two)."""
    if t in (0, 1, 2):
        return t if db == 1 else t + 3
    return 6


class Wrapper:
    """0xc-byte sub-filter wrapper (ctor 0x1080a0): +0 kind, +4 first biquad, +8 second biquad (kinds 3..5) or none."""
    def __init__(self, kind, fs):
        self.kind = kind
        typ = ["lpf", "hpf", "bpf"][kind % 3] if kind < 6 else None
        self.stages = [] if typ is None else ([Biquad(typ, fs)] if kind < 3 else [Biquad(typ, fs), Biquad(typ, fs)])

    def configure(self, cut_c, q_c, flag):          # kinds 0..2 inline in 108808; kinds 3..5 = 0x107b64 (Q' = sqrt(Q))
        if not self.stages: return
        q = float(q_c) if self.kind < 3 else math.sqrt(float(q_c))
        for s in self.stages:
            v = s.nyq
            if cut_c <= v: v = cut_c
            fc = MIN_FC
            if fc <= v: fc = v
            s.Q = q; s.fc = fc
            s.coefs()
            s.flag48 = flag

    def process(self, L, R, i0, n):                 # IirFilter slot 2 (0xe16dc) on each stage in turn
        for s in self.stages:
            s.process(L, R, i0, n)


class FilterContainer:
    """Object at MMF+0x498 (size 0x50, ctor 0x10913c)."""
    def __init__(self, fs):
        self.w = [Wrapper(k, fs) for k in range(7)]
        self.gate = SignalGate(fs, rnd(F(F(F(fs) * F(0.001)) * F(3.0))))
        self.pending = 0; self.cur = 0                         # +0x10 / +0x14 (ctor 0 = LPF 12 dB)
        self.cut_t = self.cut_c = F(1000.0)                    # +0x18 / +0x1c
        self.cut_mult = F(0.0); self.cut_steps = 0              # +0x20 (ctor copies +0x48 before it is set) / +0x24
        self.q_t = self.q_c = F(0.7)                           # +0x28 / +0x2c
        self.q_mult = G3; self.q_steps = 0                     # +0x30 / +0x34
        self.next = F(0.0); self.maxsteps = 0                  # +0x38 / +0x3c
        self.flag40 = 0; self.dirty41 = 0; self.glide42 = 0    # bytes +0x40 / +0x41 / +0x42
        self.set_glide_steps(F(64.0))                          # +0x44 / +0x48 / +0x4c

    def set_glide_steps(self, g):
        self.g44 = g
        m = F(math.pow(10.0, float(F(log10f(F(1000.0)) / g))))
        self.up48 = m; self.dn4c = F(F(1.0) / m)

    def set_kind(self, k):                              # tail of 0x107c24
        self.pending = k
        if k != self.cur: self.gate.close()

    def ramp_setup(self):                               # 0x108608
        if self.dirty41:
            n = rnd(abs(F(F(F(1.0) / log10f(self.up48)) * log10f(F(self.cut_t / self.cut_c)))))
            self.cut_steps = n + 1
            self.cut_mult = self.up48 if self.cut_t > self.cut_c else self.dn4c
            n2 = rnd(abs(F(F(F(1.0) / log10f(G3)) * log10f(F(self.q_t / self.q_c)))))
            self.q_steps = n2 + 1
            self.q_mult = G3 if self.q_t > self.q_c else G4
            self.next = F(44.1); self.dirty41 = 0
        self.maxsteps = max(self.q_steps, self.cut_steps)
        r = self.gate.r
        if r.state == 1 and near(r.target, self.gate.off): return
        if float(self.cut_steps) > float(self.g44) * 152.0 / 1000.0 and not self.glide42:
            self.gate.close()

    def _swap(self):
        self.cur = self.pending; self.cut_c = self.cut_t; self.q_c = self.q_t
        self.cut_steps = self.q_steps = self.maxsteps = 0
        w = self.w[self.cur]
        w.configure(self.cut_c, self.q_c, 1)
        return w

    def process(self, L, R, i0, n):                     # 0x108808
        if self.cur != 6: self.ramp_setup()
        r = self.gate.r
        if r.state == 1 and near(r.target, self.gate.off):          # fading out
            rem = r.rem
            if n < rem:
                self.w[self.cur].process(L, R, i0, n); self.gate.apply(L, R, i0, n); return
            self.w[self.cur].process(L, R, i0, rem); self.gate.apply(L, R, i0, rem)
            w = self._swap()
            w.process(L, R, i0 + rem, n - rem); self.gate.open(); self.gate.apply(L, R, i0 + rem, n - rem); return
        if r.state != 1 and near(r.cur, self.gate.off):              # closed: switch now, then fade in
            w = self._swap()
            w.process(L, R, i0, n); self.gate.open(); self.gate.apply(L, R, i0, n); return
        rem = n; pos = i0                                            # open or fading in: stepped cutoff/Q ramp
        while rem > 0:
            if self.maxsteps <= 0:
                chunk = rem; rem = 0
            else:
                s15 = self.next; r6 = rnd(s15)
                if rem >= r6:
                    s14 = F(r6); rem -= r6
                    ocs = self.cut_steps; self.cut_steps = ocs - 1 if ocs > 1 else 0
                    oqs = self.q_steps
                    self.next = F(F(s15 - s14) + F(44.1))
                    self.cut_c = F(self.cut_c * self.cut_mult) if ocs > 1 else self.cut_t
                    self.q_steps = oqs - 1 if oqs > 1 else 0
                    self.flag40 = 1
                    self.q_c = F(self.q_c * self.q_mult) if oqs > 1 else self.q_t
                    chunk = r6
                else:
                    chunk = rem; self.next = F(s15 - F(rem)); rem = 0
            w = self.w[self.cur]
            w.process(L, R, pos, chunk); pos += chunk
            if self.flag40:
                w.configure(self.cut_c, self.q_c, 0); self.flag40 = 0
        self.gate.apply(L, R, i0, n)


class GainRamp:
    """Object at MMF+0x49c (size 0x24, ctor 0xe8900(obj, N = round(3 ms * fs), 1.0)); setTarget 0xe895c; process 0xe89f0."""
    def __init__(self, n, g):
        self.inc = F(0); self.target = F(g); self.cur = F(g); self.rem = 0     # +0 / +4 / +8 / +0xc
        self.N = n if n > 0 else 1; self.invN = F(F(1.0) / F(n)) if n > 0 else F(1.0)   # +0x10 / +0x14
        self.delay = 0; self.idle = 1; self.state = 0                          # +0x18 / byte +0x1c / +0x20

    def set_target(self, g, force=1, delay=0):          # 0xe895c (MMF passes force 1, delay 0)
        g = F(g)
        if not self.idle and force: return
        if not (self.target > g or self.target < g): return     # equal (or unordered): keep the current ramp
        self.inc = F(F(g - self.cur) * self.invN); self.target = g; self.delay = delay
        self.rem = self.N; self.state = 2 if delay > 0 else 1; self.idle = force

    def process(self, L, R, n):                         # 0xe89f0(obj, L, R, L, R, n), in place
        i = 0
        while n > 0:
            if self.state == 2:                          # delay before the ramp (not reached from MMF: delay 0)
                d = self.delay
                if n <= d:
                    vmul_block(L, i, n, self.cur); vmul_block(R, i, n, self.cur); self.delay = d - n; return
                vmul_block(L, i, d, self.cur); vmul_block(R, i, d, self.cur)
                i += d; n -= d; self.delay = 0; self.state = 1
            elif self.state == 1:
                g = self.cur; rem = self.rem
                k = n if n < rem else rem
                for j in range(i, i + k):
                    L[j] = F(L[j] * g); R[j] = F(R[j] * g); g = F(g + self.inc)
                if n < rem:
                    self.cur = g; self.rem = rem - n; return
                i += rem; n -= rem
                self.rem = 0; self.state = 0; self.cur = self.target; self.inc = F(0); self.idle = 1
            else:
                vmul_block(L, i, n, self.cur); vmul_block(R, i, n, self.cur); return


class MMF:
    def __init__(self, fs=FS, block=64):
        self.fs = fs
        self.params = [Param("float", v) for v in CTOR_VALUES[:6]] + [Param("choice", CTOR_VALUES[6]),
                                                                       Param("choice", CTOR_VALUES[7])]
        self.filt = FilterContainer(fs)                                      # +0x498
        self.gain = GainRamp(rnd(F(F(F(fs) * F(0.001)) * F(3.0))), 1.0)      # +0x49c
        self.wet = None; self.dry = None                                     # EffectBase +0x14 / +0x10 (slot 26)

    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24
        if 0 <= idx < 8: self.params[idx].set(v); return 0
        return 3

    def insert_defaults(self):
        for i in APPLY_ORDER_DEFAULTS: self.set_param(i, INSERT_DEFAULTS[i])

    # formulas (also used by the harness readback checks)
    @staticmethod
    def cutoff_hz(v): return F(F(math.pow(1000.0, float(F(v)))) * F(20.0))
    @staticmethod
    def q_of(v): return F(F(0.2) + F(F(v) * F(9.8)))
    @staticmethod
    def gain_db(v): return F(F(F(v) * F(45.0)) - F(30.0))
    @staticmethod
    def gain_lin(v): return F(math.pow(10.0, float(F(MMF.gain_db(v) * F(0.05)))))
    @staticmethod
    def glide_steps(v):
        s = F(F(F(1.0) + F(F(v) * F(8.0))) * F(64.0))
        d = F(s - F(64.0))
        if d <= 0: d = -d
        return (F(64.0), 0) if d < EPS else (s, 1)

    def apply_params(self):                             # 0x107d18: CUTOFF, Q, GAIN, GLIDE, then FILTERTYPE/FILTERDB
        P = self.params; C = self.filt
        if P[0].changed():
            C.cut_t = self.cutoff_hz(P[0].get()); C.dirty41 = 1
        if P[2].changed():
            C.q_t = self.q_of(P[2].get()); C.dirty41 = 1
        if P[1].changed():
            self.gain.set_target(self.gain_lin(P[1].get()), 1, 0)
        if P[3].changed():
            g, flag = self.glide_steps(P[3].get())
            C.glide42 = flag; C.set_glide_steps(g)
        c6 = P[6].changed(); c7 = P[7].changed()      # both are evaluated every block
        if c6 or c7:
            C.set_kind(kind_of(rnd(P[6].get()), rnd(P[7].get())))
        # P[4] "NONE" is never read by the DSP

    def process(self, L, R):                            # slot 25 0x108ee4; returns new lists
        L = [F(x) for x in L]; R = [F(x) for x in R]; n = len(L)
        self.apply_params()
        self.filt.process(L, R, 0, n)
        self.gain.process(L, R, n)
        if self.params[5].changed():                    # slot 26 0x107b30
            v = self.params[5].get(); self.wet = v; self.dry = F(F(1.0) - v)
        return [float(x) for x in L], [float(x) for x in R]
