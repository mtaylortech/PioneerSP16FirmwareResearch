# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Flanger insert effect (Insert index 1; class `Flanger`, vtable 0x8429a8, built
inline in the InsertFxProcessor ctor 0x118b0c; DSP kernel class `c_flanger`, vtable 0x841c10, ctor 0x100234).
Reconstructed in docs/effects/flanger.md (H034); contains no firmware bytes (the oscillator random table is not used here).

Signal flow per block (Flanger slot 25 0x115f58, same structure as Chorus slot 25):
  1. consume parameter changes (RATE +0x1bc, SYNC +0x218, BPM +0x240, F026 change detection) -> dirty byte +0x2ac.
     If dirty: rate in Hz (free: i = rint(1 + 99 v), Hz = 0.01 i, i.e. 0.01 .. 1.00 Hz;
     Sync: i = rint(6 v), Hz = BPM * (b_i / a_i) / 60 from a 7-entry fraction table) -> kernel slot 3 (clamp
     0.00026042 .. 128 Hz) -> oscillator setFrequency.
  2. kernel slot 19 0xff9ac (always block = 64 samples, in place):
       reset flag +0xf2 (set by the ctor): write index, last read indices, ring and feedback memories cleared
       (the oscillator is NOT restarted); retrigger flag +0xf0 (kernel slot 18, from Flanger slot 10) restarts the
       oscillator (resetPhase 0);
       oscillator (sine, 50 Hz smoother) -> per-channel delay d (samples) = offset + amp * sine;
       per-sample gain g(d) = 1 + 0.013154167 d - 0.6314 for d <= 48 samples, else 1;
       per sample: ring[w] = x + fb * y_prev; w += 1; out = (1 - fr) ring[r] + fr ring[r - 1] with r = w_old - int(d),
       fr = d - int(d) (ring 7 fs / 1000 + block = 372 samples); y_prev = out (before the gain);
       after the loop out *= g(d) per sample.
     Wet only: no dry path. No start-up mute or fade (the ctor computes Chorus-style fade constants that slot 19 never reads).
  3. slot 26 0x1159d4 (every block): EffectBase dry +0x10 = 1.0, wet +0x14 = Mixratio (+0x29c).
Parameters through slot 14 0x1163f0: 0 RATE (deferred), 1 DEPTH, 2 PHASE, 3 DEPTH SCALE, 4 FEEDBACK (immediate, kernel slots
5/6/7/8), 5 MIXRATIO (immediate store), 6 SYNC, 7 BPM (deferred).
All float32 arithmetic is scalar VFP (no flush-to-zero with FPSCR = 0), modelled with F() (round to nearest even).
"""
from osc import Osc, OwnLibm, F, fbits
from chorus import LinParam, Toggle, rint_idx

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "RATE", 1: "DEPTH", 2: "PHASE", 3: "DEPTHSCALE", 4: "FEEDBACK", 5: "MIXRATIO", 6: "SYNC", 7: "BPM"}
# Flanger sync fractions (a, b), index 0..6: Hz = BPM * b / a / 60, i.e. one oscillator cycle lasts a/b beats.
# Established by emulating the 1.60 static initialiser (docs/effects/flanger.md);
# tools/fx/verify/H034_flanger_model.py asserts them against the emulated table.
SYNC_FRACTIONS = [(64, 1), (32, 1), (16, 1), (8, 1), (4, 1), (2, 1), (1, 1)]
K_RATE_MIN = fbits(0x3988888a)    # kernel slot 3 clamp, 0.00026041671
K_RATE_MAX = F(128.0)
K_HUNDREDTH = F(0.01)             # 0x3c23d70a
K_TENTH = F(0.1)                  # 0x3dcccccd
K_MILLI = F(0.001)                # 0x3a83126f
K_OFF = F(0.2)                    # 0x3e4ccccd
K_PH = F(1.0 / 380.0)             # 0x3b2c7692
K_PH_MAX = F(180.0 / 380.0)       # 0x3ef286bd
K_FB_MAX = F(0.98999995)          # 0x3f7d70a3
K_RAMP = F(0.0033)                # 0x3b5844d0
K_SIXTIETH = F(1.0 / 60.0)        # 0x3c888889
K_KNEE = F(48.0)                  # 0x42400000
K_GSLOPE = F(0.013154167)         # 0x3c578493
K_GSUB = F(0.6314)                # 0x3f21a36e


class Kernel:
    """c_flanger (0x118 bytes). Field names follow the 1.60 offsets."""
    def __init__(self, block=BLOCK, fs=FS, id_counter=1, libm=None):
        self.fs = fs; self.block = block                                  # +0x04 / +0x08
        self.osc, _ = Osc.ctor(0, 1.0, 44100, id_counter, libm=libm or OwnLibm())   # +0x28 (literal 44100)
        fsf = F(float(fs)); k = F(fsf * K_RAMP)
        q7 = abs(fs * 7) // 1000
        self.ln = (q7 if fs >= 0 else -q7) + block                        # +0xc0 = fs*7/1000 (C division) + block
        self.w = 0; self.rL = 0; self.rR = 0                              # +0xcc / +0xd0 / +0xd4
        q = F(F(float(block)) / k)
        self.coef = F(F(1.0) / k)                                         # +0xe8 (unused by slot 19)
        self.ncoef = F(F(0.0) - self.coef)                                # +0xec (unused)
        self.tol = F(F(F(F(q * q) * q) * q) * q)                          # +0x110 (unused)
        self.retrig = 0; self.e1 = 0; self.reset_flag = 1                 # +0xf0 / +0xf1 / +0xf2
        self.y = [F(0.0), F(0.0)]                                         # +0xf4 / +0xf8 previous pre-gain outputs
        self.x_fc = F(0.0)                                                # +0xfc (kernel slot 9 fraction; unused)
        self.fb = F(0.0)                                                  # +0x10c feedback
        self.prepare()                                                    # 0xff798: rings, osc and gain buffers
        self.rate = K_TENTH; self.depth = F(100.0); self.phase = F(0.0); self.scale = F(2.0)   # +0x0c..+0x18
        self.fb_i = F(0.0); self.x20 = F(0.0)                             # +0x1c / +0x20
        self.osc.set_frequency(K_TENTH)
        amp = F(F(F(fsf + fsf) * K_MILLI) * F(0.5))
        if self.osc.set_amplitude(amp): self.osc.set_offset(F(amp + K_OFF))

    def prepare(self):                                                    # slot 2 0xff990 -> 0xff798 (re-allocate, zero)
        self.ring = [[F(0.0)] * self.ln, [F(0.0)] * self.ln]               # +0xc4 / +0xc8
        self.dL = [F(0.0)] * self.block; self.dR = [F(0.0)] * self.block  # +0xd8 / +0xdc oscillator buffers
        self.gL = [F(0.0)] * self.block; self.gR = [F(0.0)] * self.block  # +0xe0 / +0xe4 gain buffers

    # ---- kernel vtable slots ----------------------------------------------------------------------------------
    def set_rate(self, hz):                                                # slot 3 0xffdc4
        hz = F(hz)
        if not hz < 0.0: sign = F(1.0); mag = hz
        else: sign = F(-1.0); mag = F(-hz)
        if mag < K_RATE_MIN: mag = K_RATE_MIN; arg = F(sign * K_RATE_MIN)
        elif mag <= K_RATE_MAX or mag != mag: arg = F(mag * sign)
        else: mag = K_RATE_MAX; arg = F(sign * K_RATE_MAX)
        self.rate = mag
        if self.ln == 0 or not self.osc.set_frequency(arg): self.rate = F(0.0); return F(0.0)
        return self.rate

    def set_period_ms(self, ms):                                           # slot 4 0xfff50 (not reached from Flanger)
        ms = F(ms)
        if ms < 100.0: ms = F(100.0)
        elif ms > 10000.0: ms = F(10000.0)
        self.rate = ms                                                     # stored into the rate field +0x0c
        if self.ln == 0 or not ms <= 100000.0 or not self.osc.set_period_ms(ms): self.rate = F(0.0); return F(0.0)
        return self.rate

    def _apply_amp(self):
        t = F(F(self.depth * self.scale) * K_HUNDREDTH)
        if t < 0.0: t = F(0.0)
        amp = F(F(F(F(float(self.fs)) * t) * K_MILLI) * F(0.5))
        if self.osc.set_amplitude(amp): self.osc.set_offset(F(amp + K_OFF))

    def set_depth(self, v):                                                # slot 5 0xfffd4 (lo 0, hi 101)
        d = F(float(rint_idx(0, 101, v)))
        if d < 0.0: d = F(0.0)
        elif d > 100.0: d = F(100.0)
        self.depth = d
        if self.ln: self._apply_amp()
        return self.depth

    def set_phase(self, v):                                                # slot 6 0xffe68 (lo 0, hi 181) degrees
        deg = F(float(rint_idx(0, 181, v)))
        if deg < 0.0: deg = F(0.0); ph = F(0.0)
        elif deg > 180.0: deg = F(180.0); ph = K_PH_MAX
        else: ph = F(deg * K_PH)
        self.phase = deg
        if self.ln == 0 or not self.osc.set_phase_offset(ph): self.phase = F(0.0); return F(0.0)
        return deg

    def set_scale(self, v):                                                # slot 7 0x100104 (lo 1, hi 71) x 0.1
        s = F(F(float(rint_idx(1, 71, v))) * K_TENTH)
        if s < K_TENTH: s = K_TENTH
        elif s > 7.0: s = F(7.0)
        self.scale = s
        if self.ln: self._apply_amp()
        return self.scale

    def set_feedback(self, v):                                             # slot 8 0xff694 (lo 0, hi 100)
        i = F(float(rint_idx(0, 100, v)))
        if i < 0.0: i = F(0.0); f = F(0.0)
        elif i <= 99.0: f = F(i * K_HUNDREDTH)
        else: i = F(99.0); f = K_FB_MAX
        self.fb_i = i
        if self.ln == 0 or not f >= 0.0 or not f < 1.0: self.fb_i = F(0.0); return F(0.0)
        self.fb = f
        return i

    def set_x20(self, v):                                                  # slot 9 0xff598 (lo 0, hi 101); unused by slot 19
        i = F(float(rint_idx(0, 101, v)))
        if i < 0.0: i = F(0.0); f = F(0.0)
        elif i > 100.0: i = F(100.0); f = F(1.0)
        else: f = F(i * K_HUNDREDTH)
        self.x20 = i
        if self.ln == 0 or not f >= 0.0 or f > 1.0: self.x20 = F(0.0); return F(0.0)
        self.x_fc = f
        return i

    def retrigger(self): self.retrig = 1; return 1                          # slot 18 0xff3a8

    @staticmethod
    def gain(d):
        return F(F(F(1.0) + F(d * K_GSLOPE)) - K_GSUB) if d <= K_KNEE else F(1.0)

    def process(self, L, R):                                               # slot 19 0xff9ac (in place, n = block)
        if self.ln == 0: return 0
        if self.reset_flag:
            self.w = 0; self.rL = 0; self.rR = 0
            self.ring = [[F(0.0)] * self.ln, [F(0.0)] * self.ln]
            self.y = [F(0.0), F(0.0)]; self.reset_flag = 0
        if self.retrig:
            self.osc.reset_phase(F(0.0)); self.retrig = 0
        n = self.block
        self.dL, self.dR = self.osc.process(n)
        if n <= 0: return 1
        dL, dR = self.dL, self.dR
        self.gL = [self.gain(d) for d in dL]; self.gR = [self.gain(d) for d in dR]
        ln = self.ln; rb0, rb1 = self.ring; w = self.w; fb = self.fb; y0, y1 = self.y
        rL = rR = 0
        for i in range(n):
            iL = int(dL[i]); iR = int(dR[i])
            rL = w - iL
            if rL < 0: rL += ln
            rR = w - iR
            if rR < 0: rR += ln
            rb0[w] = F(L[i] + F(y0 * fb)); rb1[w] = F(R[i] + F(y1 * fb))
            w += 1
            if w >= ln: w = 0
            fr = F(dL[i] - F(float(iL)))
            p = rb0[ln - 1] if rL < 1 else rb0[rL - 1]
            y0 = F(F(F(F(1.0) - fr) * rb0[rL]) + F(fr * p))
            fr = F(dR[i] - F(float(iR)))
            p = rb1[ln - 1] if rR < 1 else rb1[rR - 1]
            y1 = F(F(F(F(1.0) - fr) * rb1[rR]) + F(fr * p))
            L[i] = y0; R[i] = y1
        self.w = w; self.rL = rL; self.rR = rR; self.y = [y0, y1]
        for i in range(n):
            L[i] = F(L[i] * self.gL[i]); R[i] = F(R[i] * self.gR[i])
        return 1


class Flanger:
    """Flanger object (0x2b0 bytes): EffectBase + kernel pointer +0x1b8, parameters and per-block copies."""
    def __init__(self, fs=FS, block=BLOCK, id_counter=1, libm=None, fractions=None):
        self.k = Kernel(block, fs, id_counter, libm)                       # +0x1b8
        self.p_rate = LinParam(0.5)                                        # +0x1bc "RATE" id 0, 0..1
        self.p_sync = Toggle(0)                                            # +0x218 "SYNC" id 6
        self.p_bpm = LinParam(120.0)                                       # +0x240 "BPM" id 7, 1..999
        self.mix = F(0.0)                                                  # +0x29c (ctor 0, Chorus has 1.0)
        self.rate_v = F(0.5); self.sync_v = 0; self.bpm_v = F(120.0)       # +0x2a0 / +0x2a4 / +0x2a8
        self.dirty = 0                                                     # +0x2ac
        self.dry = F(1.0); self.wet = F(0.0)                               # EffectBase +0x10 / +0x14
        self.fractions = fractions or SYNC_FRACTIONS

    def set_param(self, idx, v):                                           # slot 14 0x1163f0 (always returns 0)
        if idx == 0: self.p_rate.set(v)
        elif idx == 1: self.k.set_depth(v)
        elif idx == 2: self.k.set_phase(v)
        elif idx == 3: self.k.set_scale(v)
        elif idx == 4: self.k.set_feedback(v)
        elif idx == 5: self.mix = F(v)
        elif idx == 6: self.p_sync.set(v)
        elif idx == 7: self.p_bpm.set(v)
        return 0

    @staticmethod
    def free_hz(v):                                                        # 0x349e30 range {1, 101}; 0x349e50 i * 0.01f
        return F(F(float(rint_idx(1, 101, v))) * K_HUNDREDTH)

    def sync_hz(self, v, bpm):                                             # 0x349e9c range {0, 7}; 0x349eb8 fraction
        i = rint_idx(0, 7, v)
        if not 0 <= i <= 6: i = 4                                          # assert path of 0x349eb8 (log, then index 4)
        a, b = self.fractions[i]                                           # first / second u16 of the entry
        return F(F(F(F(float(b)) * F(bpm)) / F(float(a))) * K_SIXTIETH)

    def retrigger(self): return self.k.retrigger()                         # slot 10 0x1159e8 -> kernel slot 18
    def reset(self): self.k.prepare(); return 0                            # slot 27 0x1159b0 -> kernel slot 2 (64, 44100)

    def process(self, L, R):                                               # slot 25 0x115f58; returns 0, modifies lists
        if self.p_rate.changed(): self.rate_v = self.p_rate.get(); self.dirty = 1
        if self.p_sync.changed(): self.sync_v = self.p_sync.get(); self.dirty = 1
        if self.p_bpm.changed(): self.bpm_v = self.p_bpm.get(); self.dirty = 1
        if self.dirty:
            hz = self.sync_hz(self.rate_v, self.bpm_v) if self.sync_v else self.free_hz(self.rate_v)
            self.k.set_rate(hz); self.dirty = 0
        self.k.process(L, R)
        self.wet = self.mix; self.dry = F(1.0)                             # slot 26 0x1159d4
        return 0
