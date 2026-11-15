# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Chorus insert effect (Insert index 0; class `Chorus`, vtable 0x842920, built
inline in the InsertFxProcessor ctor 0x118b0c; DSP kernel class `c_chorus`, vtable 0x841ba0, ctor 0xff008).
Reconstructed in docs/effects/chorus.md (H033); contains no firmware bytes (the oscillator random table is not used here).

Signal flow per block (Chorus slot 25 0x115d70):
  1. consume parameter changes (RATE +0x1bc, SYNC +0x218, BPM +0x240 -- all three every block, F026 change detection);
     any change sets the dirty byte +0x2ac. If dirty: rate in Hz from RATE (free: i = rint(1 + 99 v), Hz = 0.1 i;
     Sync: i = rint(9 v), Hz = BPM * (n_i / d_i) / 60 from a 10-entry fraction table) -> kernel slot 3 (clamp
     0.00104167..64 Hz) -> oscillator setFrequency.
  2. kernel slot 19 0xfe710 (always block = 64 samples, in place):
       reset flag +0xe2 (set by the ctor) clears ring/index/full flag and restarts the oscillator (resetPhase 0);
       retrigger flag +0xe0 (kernel slot 18, from Chorus slot 10) restarts the oscillator;
       oscillator (sine, 50 Hz output smoother) -> per-channel delay d (samples) = offset + amp * sine;
       per sample: ring[w] = x; out = linear interpolation at position w - d (ring of fs/10 + block = 4474 samples);
       then an output gain g that stays 0 until the ring has wrapped once and then approaches 1 block by block
       (step per sample = (target - g) / (0.0033 fs), snapped to the target within (block / (0.0033 fs))^5).
     Wet only: no dry path, no feedback.
  3. slot 26 0x115a38 (every block): EffectBase dry +0x10 = 1.0, wet +0x14 = Mixratio (+0x29c). The dry/wet sum is
     done later by EffectBase slot 18 (not modelled here).
Parameters set through slot 14 0x116224: 0 RATE (deferred), 1 DEPTH, 2 PHASE, 3 DEPTH SCALE (immediate kernel slots 5/6/7),
5 MIXRATIO (immediate store), 6 SYNC, 7 BPM (deferred); index 4 is ignored.
All float32 arithmetic is scalar VFP (no flush-to-zero with FPSCR = 0), modelled with F() (round to nearest even).
"""
import math
from osc import Osc, OwnLibm, F

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "RATE", 1: "DEPTH", 2: "PHASE", 3: "DEPTHSCALE", 5: "MIXRATIO", 6: "SYNC", 7: "BPM"}
# Sync fractions (a, b), index 0..9: Hz = BPM * b / a / 60, i.e. one oscillator cycle lasts a/b beats
# (16, 8, 4, 2, 1, 3/4, 1/2, 1/4, 1/8, 1/16 beats). Established by emulating the 1.60 static initialiser
# (docs/effects/chorus.md); tools/fx/verify/H033_chorus_model.py asserts them against the emulated table.
SYNC_FRACTIONS = [(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (3, 4), (1, 2), (1, 4), (1, 8), (1, 16)]
FLT_MIN = 1.17549435e-38
K_RATE_MIN = F(0.00104167)        # kernel slot 3 clamp (literal 0x3a8888a5)
K_RATE_MAX = F(64.0)
K_TENTH = F(0.1)                  # literal 0x3dcccccd
K_HUNDREDTH = F(0.01)             # 0x3c23d70a
K_MILLI = F(0.001)                # 0x3a83126f
K_OFF = F(0.2)                    # 0x3e4ccccd
K_PH = F(1.0 / 380.0)             # 0x3b2c7692 (phase degrees -> cycles)
K_PH_MAX = F(180.0 / 380.0)       # 0x3ef286bd
K_RAMP = F(0.0033)                # 0x3b5844d0
K_SIXTIETH = F(1.0 / 60.0)        # 0x3c888889


def rint_idx(lo, hi, v):
    """BasicParamSpec index: F(lo + F(v*(hi-1-lo))) + 1.5*2^52 (double), low word = round half to even."""
    x = F(F(float(lo)) + F(F(v) * F(float(hi - 1 - lo))))
    return int(round(float(x)))


class LinParam:
    """LinearParameter (vtable 0x840ac8), float kind: last +0x24, current +0x28; setValue unclamped."""
    def __init__(self, default):
        self.last = self.cur = F(default)
    def set(self, v): self.cur = F(v)                     # 0xf0874
    def changed(self):                                    # 0xf0ffc
        d = F(self.last - self.cur)
        if d <= FLT_MIN and -FLT_MIN <= d: return False
        self.last = self.cur
        return True
    def get(self): return self.cur                        # 0xf0898


class Toggle:
    """ToggleParameter (vtable 0x840b20): bytes last +0x24 / current +0x25."""
    def __init__(self, default=0): self.last = self.cur = int(default)
    def set(self, v):                                     # 0xf0738
        v = F(v)
        if v >= 1.0: self.cur = 1
        elif v <= 0.0: self.cur = 0
    def changed(self):                                    # 0xf0858
        c = self.cur != self.last
        if c: self.last = self.cur
        return c
    def get(self): return self.cur                        # 0xf0814


class Kernel:
    """c_chorus (0x100 bytes). Field names follow the 1.60 offsets."""
    def __init__(self, block=BLOCK, fs=FS, id_counter=1, libm=None):
        self.fs = fs; self.block = block                                  # +0x04 / +0x08
        self.osc, _ = Osc.ctor(0, 1.0, 44100, id_counter, libm=libm or OwnLibm())   # +0x28 (literal 44100)
        fsf = F(float(fs)); k = F(fsf * K_RAMP)
        self.ln = int(fs / 10) + block                                    # +0xc0 ring length (C int division)
        self.ring = [[F(0.0)] * self.ln, [F(0.0)] * self.ln]               # +0xc4 / +0xc8
        self.w = 0                                                        # +0xcc write index
        q = F(F(float(block)) / k)
        self.coef = F(F(1.0) / k)                                         # +0xd8
        self.ncoef = F(F(0.0) - self.coef)                                # +0xdc
        self.tol = F(q * F(q * F(q * F(q * q))))                          # +0xf4
        self.retrig = 0; self.e1 = 0; self.reset_flag = 1                 # +0xe0 / +0xe1 / +0xe2
        self.g = F(0.0); self.target = F(0.0); self.step = F(0.0)         # +0xe8 / +0xec / +0xf0
        self.full = 0                                                     # +0xf8
        self.x20 = F(0.0); self.x1c = F(0.0)
        # ctor parameter state and oscillator configuration (0xff120..0xff1dc)
        self.rate = K_TENTH; self.depth = F(100.0); self.phase = F(0.0); self.scale = F(1.0)   # +0x0c..+0x18
        self.osc.set_frequency(K_TENTH)
        amp = F(F(fsf * K_MILLI) * F(0.5))
        self.osc.set_amplitude(amp); self.osc.set_offset(F(amp + K_OFF))
        self.osc.set_phase_offset(F(0.0))
        self.dL = [F(0.0)] * block; self.dR = [F(0.0)] * block            # +0xd0 / +0xd4 oscillator buffers

    # ---- kernel vtable slots ----------------------------------------------------------------------------------
    def set_rate(self, hz):                                                # slot 3 0xfeb10
        hz = F(hz)
        if not hz < 0.0: sign = F(1.0); mag = hz
        else: sign = F(-1.0); mag = F(-hz)
        if mag < K_RATE_MIN: mag = K_RATE_MIN; arg = F(sign * K_RATE_MIN)
        elif mag <= K_RATE_MAX or mag != mag: arg = F(mag * sign)
        else: mag = K_RATE_MAX; arg = F(sign * K_RATE_MAX)
        self.rate = mag
        if self.ln == 0 or not self.osc.set_frequency(arg): self.rate = F(0.0); return F(0.0)
        return self.rate

    def _apply_amp(self):
        t = F(F(self.depth * self.scale) * K_HUNDREDTH)
        if t < 0.0 or not t <= 100.0: return
        amp = F(F(F(t * F(float(self.fs))) * K_MILLI) * F(0.5))
        if self.osc.set_amplitude(amp): self.osc.set_offset(F(amp + K_OFF))

    def set_depth(self, v):                                                # slot 5 0xfed90 (lo 0, hi 101)
        d = F(float(rint_idx(0, 101, v)))
        if d < 0.0: d = F(0.0)
        elif d > 100.0: d = F(100.0)
        self.depth = d
        if self.ln: self._apply_amp()
        return d

    def set_scale(self, v):                                                # slot 7 0xfeecc (lo 10, hi 101) x 0.1
        s = F(F(float(rint_idx(10, 101, v))) * K_TENTH)
        if s < 1.0: s = F(1.0)
        elif s > 100.0: s = F(100.0)
        self.scale = s
        if self.ln: self._apply_amp()
        return s

    def set_phase(self, v):                                                # slot 6 0xfec34 (lo 0, hi 181) degrees
        deg = F(float(rint_idx(0, 181, v)))
        if deg < 0.0: deg = F(0.0); ph = F(0.0)
        elif deg > 180.0: deg = F(180.0); ph = K_PH_MAX
        else: ph = F(deg * K_PH)
        self.phase = deg
        if self.ln == 0 or not self.osc.set_phase_offset(ph): self.phase = F(0.0); return F(0.0)
        return deg

    def retrigger(self): self.retrig = 1; return 1                          # slot 18 0xfe300

    def prepare(self):                                                     # slot 2 0xfe6f4 -> 0xfe59c (re-allocate, zero)
        self.ring = [[F(0.0)] * self.ln, [F(0.0)] * self.ln]
        self.dL = [F(0.0)] * self.block; self.dR = [F(0.0)] * self.block

    def process(self, L, R):                                               # slot 19 0xfe710 (in place, n = block)
        if self.ln == 0: return 0
        if self.reset_flag:
            self.w = 0; self.prepare_ring_only(); self.full = 0
            self.osc.reset_phase(F(0.0)); self.reset_flag = 0
        if self.retrig:
            self.osc.reset_phase(F(0.0)); self.retrig = 0
        n = self.block
        self.dL, self.dR = self.osc.process(n)
        ln = self.ln; lnf = F(float(ln)); rb = self.ring; w = self.w
        for i in range(n):
            fw = F(float(w)); rb[0][w] = L[i]; rb[1][w] = R[i]
            for ch, d in ((0, self.dL[i]), (1, self.dR[i])):
                pos = F(fw - d)
                if pos < 0.0:
                    pos = F(pos + lnf); i0 = int(pos)
                    if i0 < ln: fr = F(pos - F(float(i0))); om = F(F(1.0) - fr); i1 = i0 + 1
                    else: fr = F(0.0); om = F(1.0); i0 = 0; i1 = 1
                else:
                    i0 = int(pos); fr = F(pos - F(float(i0))); om = F(F(1.0) - fr); i1 = i0 + 1
                if i1 >= ln: i1 = 0
                y = F(F(fr * rb[ch][i1]) + F(om * rb[ch][i0]))
                if ch == 0: L[i] = y
                else: R[i] = y
            w += 1
            if w >= ln: w = 0; self.full = 1
        self.w = w
        g = self.g
        self.target = F(1.0) if self.full else F(0.0)
        self.step = step = F(F(self.target - g) * self.coef)
        for i in range(n):
            g = F(g + step); L[i] = F(g * L[i]); R[i] = F(R[i] * g)
        self.g = g
        if step > 0.0 and self.target < F(g + self.tol): self.g = self.target
        if step < 0.0 and F(g - self.tol) < self.target: self.g = self.target
        return 1

    def prepare_ring_only(self):
        self.ring = [[F(0.0)] * self.ln, [F(0.0)] * self.ln]


class Chorus:
    """Chorus object (0x2b0 bytes): EffectBase + kernel pointer +0x1b8, parameters and per-block copies."""
    def __init__(self, fs=FS, block=BLOCK, id_counter=1, libm=None, fractions=None):
        self.k = Kernel(block, fs, id_counter, libm)                       # +0x1b8
        self.p_rate = LinParam(0.5)                                        # +0x1bc "RATE" id 0, 0..1
        self.p_sync = Toggle(0)                                            # +0x218 "SYNC" id 6
        self.p_bpm = LinParam(120.0)                                       # +0x240 "BPM" id 7, 1..999
        self.mix = F(1.0)                                                  # +0x29c
        self.rate_v = F(0.5); self.sync_v = 0; self.bpm_v = F(120.0)       # +0x2a0 / +0x2a4 / +0x2a8
        self.dirty = 0                                                     # +0x2ac
        self.dry = F(1.0); self.wet = F(0.0)                               # EffectBase +0x10 / +0x14 (base ctor 1 / 0)
        self.fractions = fractions or SYNC_FRACTIONS

    def set_param(self, idx, v):                                           # slot 14 0x116224 (always returns 0)
        if idx == 0: self.p_rate.set(v)
        elif idx == 1: self.k.set_depth(v)
        elif idx == 2: self.k.set_phase(v)
        elif idx == 3: self.k.set_scale(v)
        elif idx == 5: self.mix = F(v)
        elif idx == 6: self.p_sync.set(v)
        elif idx == 7: self.p_bpm.set(v)
        return 0

    @staticmethod
    def free_hz(v):                                                        # 0x349778 range {1, 101}; 0x349798 i * 0.1f
        return F(F(float(rint_idx(1, 101, v))) * K_TENTH)

    def sync_hz(self, v, bpm):                                             # 0x3497e0 range {0, 10}; 0x349800 fraction
        i = rint_idx(0, 10, v)
        if not 0 <= i <= 9: i = 2                                          # assert path of 0x349800 (log, then index 2)
        a, b = self.fractions[i]                                           # first / second u16 of the entry
        return F(F(F(F(float(b)) * F(bpm)) / F(float(a))) * K_SIXTIETH)

    def retrigger(self): return self.k.retrigger()                         # slot 10 0x115a4c -> kernel slot 18
    def reset(self): self.k.prepare(); return 0                            # slot 27 0x115a14 -> kernel slot 2 (64, 44100)

    def process(self, L, R):                                               # slot 25 0x115d70; returns 0, modifies lists
        if self.p_rate.changed(): self.rate_v = self.p_rate.get(); self.dirty = 1
        if self.p_sync.changed(): self.sync_v = self.p_sync.get(); self.dirty = 1
        if self.p_bpm.changed(): self.bpm_v = self.p_bpm.get(); self.dirty = 1
        if self.dirty:
            hz = self.sync_hz(self.rate_v, self.bpm_v) if self.sync_v else self.free_hz(self.rate_v)
            self.k.set_rate(hz); self.dirty = 0
        self.k.process(L, R)
        self.wet = self.mix; self.dry = F(1.0)                             # slot 26 0x115a38
        return 0
