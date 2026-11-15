# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code model of the SP-16 1.60 FxCompressor core as run by InsertFxCompressor slot 25 (0xf8718) and SendFxCompressor slot 25
(0xf8270). Reconstructed from the 1.60 binary's behaviour (docs/effects/compressor.md); contains no firmware bytes.

Signal flow per block of n samples (all float32 unless noted):
  1. input meters (peak hold with decay, display only)
  2. detector, once per block:  LevelDetect 1 = "RMS": running mean (double accumulator) of max(L^2, R^2) over a 3 ms ring
     (132 samples @44.1 kHz), level = sqrt(max mean in block) * sqrt(2);  any other value = "peak": level = max over the block of
     max(|L|, |R|).  Level floor 1e-8.  The detector is stereo-linked and feed-forward (input side).
  3. gain computer, once per block, in dB: L = 20 log10(level); threshold T = rint(-52 + 52 v) dB, ratio R = rint(10 + 290 v)/10,
     knee K = 18 v dB: a soft knee of total width W = 2K, computed as an interpolated slope and threshold point, which equals the
     standard quadratic soft knee y = L + (1/R - 1)(L - T + K)^2 / (4K); target gain g_t = 10^(-(L - y)/20).
  4. target tracking: an attack (g_t below the held target) sets a hold counter of min(release ms * fs / 4000, 441) samples;
     after the hold runs out the target rises by a factor e per block (capped by g_t and 1).
  5. a geometric per-sample ramp from the current gain to the target over `ramp` samples (the in-block index of the detector
     maximum, or max(n, 44) after a threshold/ratio/knee change or a hold expiry), then a per-sample slew limiter:
     at most x exp(-1/(attack_ms fs/1000)) down and x exp(+1/(release_ms fs/1000)) up per sample.
  6. out = gain * in (both channels the same gain); output meters; make-up gain 10^(rint(50 v)/20) and Mixratio are applied by
     EffectBase through slot 26: wet = Mixratio * makeup, dry = 1 - Mixratio.
"""
import math, struct
import ctypes

from fdlibm_powf import powf
import glibc_expf
from glibc_log10 import log10 as glibc_log10

_cf = ctypes.c_float
def F(x): return _cf(x).value
def fbits(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def ffrom(u): return struct.unpack("<f", struct.pack("<I", u & 0xffffffff))[0]

FS = 44100
N = 64
K_MILLI = F(0.001)
K_TENTH = F(0.1)
K_005 = F(0.05)
K_M005 = F(-0.05)
K_1E8 = ffrom(0x322bcc77)
K_SQRT2 = float(F(1.4142135))         # double of the float literal (0x3ff6a09e60000000)
K_KNEE_HYST = ffrom(0x3fb4ce08)       # 1.4125376 = +3 dB
C_E = None                            # expf(1), expf(-1): set by _consts()
C_EINV = None

# Insert slot-52 case-7 defaults (emulated): (index, float bits)
INSERT_DEFAULTS = [(0, 0x3f800000), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0x3f800000), (7, 0), (8, 0)]


def _consts():
    global C_E, C_EINV
    if not glibc_expf.loaded():
        glibc_expf.load_tables()
    C_E = glibc_expf.expf(1.0); C_EINV = glibc_expf.expf(-1.0)


def rint(x):                     # (double)x + 1.5*2^52, low word: round half to even
    return int(round(float(x)))


def trunc(x):                    # vcvt.s32.f32 (round towards zero)
    return int(x)


def qmap(v, lo, hi):             # F(lo + F(v * (hi - 1 - lo))) -> rint   (vmla.f32, then the double trick)
    return rint(F(float(lo) + F(F(v) * float(hi - 1 - lo))))


# --- parameter mappings (range helpers 0x34b640..0x34b850) -------------------------------------------------------------------
def thr_db(v): return float(qmap(v, -52, 1))                       # -52..0 dB, 1 dB steps
def ratio(v): return F(float(qmap(v, 10, 301)) * K_TENTH)          # 1.0..30.0 in 0.1 steps
def knee_db(v): return F(F(v) * 18.0)                              # 0..18 dB, continuous
def gain_db(v): return float(qmap(v, 0, 51))                       # 0..50 dB, 1 dB steps
def attack_ms(v):                                                  # 0.05..1.0 ms in 0.05 ms steps, then 2..1000 ms in 1 ms
    i = qmap(v, 1, 0x3fc)
    return F(float(i) * K_005) if i <= 20 else float(i - 19)
def release_ms(v): return float(qmap(v, 10, 0xfa1))                # 10..4000 ms, 1 ms steps


class Meter:
    """Peak-hold meter (0xf9490 half): [cur, floor 1e-8, ceil 2.0, decay -1 dB, hold blocks, counter]."""
    def __init__(self, fs=FS, n=N):
        self.cur = K_1E8; self.floor = K_1E8; self.ceil = 2.0; self.decay = ffrom(0x3f642905)
        self.hold = trunc(F(10.0 / F(F(F(float(n)) / F(float(fs))) * 1000.0))); self.cnt = 0

    def update(self, x):
        p = 0.0
        for s in x:
            a = s if not (s <= 0.0) else -s
            if p < a: p = a
        if p <= self.floor: p = self.floor
        v = self.ceil
        if p <= v: v = p
        if self.cur < v:
            self.cur = v; self.cnt = 0
        elif self.hold < self.cnt:
            self.cnt = 0
            d = F(self.cur * self.decay)
            if not (d < self.floor): self.cur = d
        else:
            self.cnt += 1

    def reset(self):                                               # 0xf7e38: cur = min(max(floor, 0), ceil), counter 0
        f = self.floor if not (self.floor <= 0.0) else 0.0
        self.cur = f if f <= self.ceil else self.ceil
        self.cnt = 0


class Compressor:
    """FxCompressor state + InsertFxCompressor slot 25. Fields named after their object offsets."""
    def __init__(self, fs=FS, n=N, send=False):
        if C_E is None: _consts()
        self.fs = fs; self.n = n; self.send = send
        fsf = F(float(fs))
        # parameters (current values as stored by slot 14; LinearParameter +0x28, LevelDetect choice int +0x44)
        self.p = {0: 1.0, 1: 0.0, 2: 1.0, 3: 1.0, 4: 0.5, 5: 0.0, 7: 0.0, 9: 1.0, 10: 1.0, 11: 1.0, 12: 1.0, 13: 1.0}
        self.level_detect = 0
        self.ld_copy = 0         # +0x748 copy of LevelDetect read by slot 25 (and the ctor)
        self.lookahead = 0                                         # +0x74c copy (only refreshed by the Send slot 25)
        self.lookahead_param = 0                                   # LookAhead ToggleParameter (+0x498; not reachable by slot 14)
        self.thr_pt = 0.0        # +0x690 knee/threshold point (dB)
        self.slope = 1.0         # +0x68c gain-computer slope (1 or 1/R or interpolated)
        self.gain = 1.0          # +0x694 current gain
        self.makeup = 1.0        # +0x698
        self.peak = 0.0          # +0x6a4 detector level of the block
        self.ramp = 0            # +0x6a8 ramp length / in-block index of the detector maximum (1-based)
        self.mtr = [Meter(fs, n) for _ in range(4)]                # +0x6ac in L, +0x6c4 in R, +0x6e0 out L, +0x6f8 out R
        self.mingain = 1.0       # +0x6dc
        self.win = trunc(F(F(fsf * 3.0) / 1000.0))                 # +0x730 RMS window (132)
        self.inv_win = F(1.0 / float(self.win))                    # +0x738
        self.ring = [0.0] * self.win                               # +0x73c
        self.pos = 0             # +0x734
        self.sum = 0.0           # +0x740 (double)
        self.cnt = 0             # +0x76c samples in the window so far
        self.w = 0.0             # +0x768 last window weight
        self.det = [0.0] * n     # +0x6a0 detector buffer (|x| peak or mean square per sample)
        self.L = 0.0             # +0x750 level dB
        self.hold = 0            # +0x754 hold counter (samples)
        self.hold_lim = 0        # +0x758 hold length of the last attack
        self.target = 1.0        # +0x75c target gain
        self.gbuf = [0.0] * n    # +0x760 per-sample ramp
        self.rel_ms = 10.0       # +0x764
        self.last_knee = 0.0     # +0x784
        self.last_thr = 1.0      # +0x788 (ctor copy of Threshold's ctor value)
        self.last_ratio = 0.0    # +0x78c
        self.dry = 1.0; self.wet = 0.0                             # EffectBase +0x10 / +0x14 (EffectBase ctor values)
        # Send look-ahead (+0x710.. ; 2 ms + 1 sample delay line and a crossfade); Insert never runs it
        self.la_len = trunc(F(F(fsf + fsf) / 1000.0)) + 1          # 89
        self.la_pos = 0
        self.la_L = [0.0] * self.la_len; self.la_R = [0.0] * self.la_len
        self.la_fade = 1.0       # +0x728
        self.la_step = F(1000.0 / F(fsf * F(3.3333333)))           # +0x72c
        self.c_e = C_E; self.c_einv = C_EINV                       # +0x770 / +0x774
        self.trace = None

    # ---------------------------------------------------------------------------------------------------------- slot 14
    def set_param(self, idx, v):
        if idx == 8:
            self.level_detect = trunc(F(v)); return 0
        if idx in self.p:
            self.p[idx] = F(v); return 0
        return 3

    def insert_defaults(self):
        for i, b in INSERT_DEFAULTS: self.set_param(i, ffrom(b))

    # ---------------------------------------------------------------------------------------------------------- slot 26
    def update_mix(self):                                          # 0xf7380
        v = self.p[5]
        self.wet = F(v * self.makeup); self.dry = F(1.0 - v)

    # ---------------------------------------------------------------------------------------------------------- slot 27
    def reset(self):                                               # 0xf7fb8 -> 0xf7e38
        self.gain = 1.0; self.makeup = 1.0; self.mingain = 1.0
        self.la_pos = 0; self.la_L = [0.0] * self.la_len; self.la_R = [0.0] * self.la_len
        self.la_fade = 0.0 if self.lookahead else 1.0
        self.cnt = 0; self.hold = 0; self.sum = 0.0; self.target = 1.0; self.rel_ms = 10.0
        for m in self.mtr: m.reset()

    # ---------------------------------------------------------------------------------------------------------- detectors
    def detect_peak(self, L, R, n):                                # 0xf8b88
        self.peak = 0.0; self.sum = 0.0; self.ramp = 1; self.cnt = 0
        for i in range(n):
            a = L[i]; b = R[i]
            if a <= 0.0: a = -a
            if b <= 0.0: b = -b
            if a <= b: a = b
            if a < K_1E8: a = K_1E8
            self.det[i] = a
            if self.peak < a: self.ramp = i + 1; self.peak = a

    def detect_rms(self, L, R, n):                                 # 0xf8718 inline (LevelDetect == 1)
        self.ramp = 1
        mx = 0.0; s = self.sum; pos = self.pos
        for i in range(n):
            c = self.cnt; w = 0.0
            if c < self.win: self.cnt = c + 1
            else: w = 1.0
            self.w = w
            old = F(w * self.ring[pos])
            a = F(L[i] * L[i]); b = F(R[i] * R[i])
            x = a if a > b else b
            s = s - old
            self.ring[pos] = x
            s = s + x
            ms = F(s * float(self.inv_win))
            self.det[i] = ms
            if ms > mx: self.ramp = i + 1; mx = ms
            pos += 1
            if pos >= self.win: pos = 0
        self.pos = pos; self.sum = s
        r = F(math.sqrt(mx) * K_SQRT2)
        self.peak = r
        if r < K_1E8: self.peak = K_1E8

    # ---------------------------------------------------------------------------------------------------------- gain computer
    def _ms44(self, n):
        m = trunc(F(F(float(self.fs)) * K_MILLI))
        return n if n >= m else m

    def gain_stage(self, inL, inR, outL, outR, n):               # 0xf8c40
        fsf = F(float(self.fs))
        v = self.p[0]
        if v != self.last_thr: self.last_thr = v; self.ramp = self._ms44(n)
        T = thr_db(v)
        v = self.p[1]
        if v != self.last_ratio: self.last_ratio = v; self.ramp = self._ms44(n)
        invR = F(1.0 / ratio(v))
        K = knee_db(self.p[7])
        makeup = powf(10.0, F(gain_db(self.p[4]) * K_005))
        A = attack_ms(self.p[2])
        a = self.c_einv if A == 0.0 else glibc_expf.expf(-F(1.0 / F(F(A * fsf) * K_MILLI)))
        Rl = release_ms(self.p[3]); self.rel_ms = Rl
        r = self.c_e if Rl == 0.0 else glibc_expf.expf(F(1.0 / F(F(Rl * fsf) * K_MILLI)))
        L = F(20.0 * glibc_log10(float(self.peak)))                # libm log10 (double), x 20 in double
        self.L = L
        if K > 0.0:
            if self.last_knee <= 0.0: self.ramp = self._ms44(n)
            lo = F(T - K); twoK = F(K + K); self.slope = 1.0; hi = F(T + K); invW = F(1.0 / twoK)
            if lo < L:
                if hi < L: self.slope = invR
                if hi >= L:
                    s10 = F(F(L - lo) * invW)
                    self.slope = F(1.0 + F(F(invR - 1.0) * s10))
                self.thr_pt = -160.0
                if hi < L: self.thr_pt = T
                elif hi >= L:
                    s14 = F(F(L - lo) * invW)
                    self.thr_pt = F(lo + F(F(T - lo) * s14))
            else:
                self.thr_pt = -160.0
        else:
            if self.last_knee > 0.0: self.ramp = self._ms44(n)
            self.slope = 1.0
            if T < L: self.slope = invR; self.thr_pt = T
            else: self.thr_pt = -160.0
        self.last_knee = K
        r1 = trunc(F(F(fsf * K_MILLI) * 10.0))                     # 441 (10 ms)
        r2 = trunc(F(F(F(fsf * Rl) * K_MILLI) * 0.25))             # release/4 in samples
        r3 = r2 if r2 < r1 else r1
        attack = False
        if L > -160.0:
            y = F(self.thr_pt + F(F(L - self.thr_pt) * self.slope))
            gt = powf(10.0, F(F(L - y) * K_M005))
            if gt < 1.0 and not (gt > F(self.target * K_KNEE_HYST)):
                attack = True
                self.hold = r2; r3 = self.ramp
                if gt < self.target: self.target = gt
                if r2 > r1: self.hold = r1; r2 = r1
                self.hold_lim = r2
        else:
            gt = 1.0
        if not attack:
            expired = True
            h = self.hold
            if h > 0:
                h -= n; self.hold = h
                if r3 < self.hold_lim and r3 < h: self.hold = r3; h = r3
                if h > 0: expired = False
            if expired:
                tg = F(self.target * self.c_e); self.target = tg
                if gt < tg: self.target = gt; tg = gt
                if tg > 1.0: self.target = 1.0
            self.ramp = self._ms44(n); r3 = self.ramp
        if r3 <= 0: r3 = 1; self.ramp = 1
        k = powf(F(self.target / self.gain), F(1.0 / float(r3)))
        self.k_last = k
        g = self.gain; tgt = self.target
        if k > 1.0:
            for i in range(n):
                g = F(g * k)
                if g > tgt: g = tgt
                self.gbuf[i] = g
        else:
            for i in range(n):
                g = F(g * k)
                if g < tgt: g = tgt
                self.gbuf[i] = g
        mn = 1.0; s15 = 1.0; cur = self.gain
        for i in range(n):
            b = self.gbuf[i]
            if cur >= b:                                           # vcmpe + blt (unordered: neither branch)
                s12 = F(a * cur)
                if b > s12: s15 = b
                elif b <= s12: s15 = s12
            if cur < b:
                s14 = F(r * cur)
                if b < s14: s15 = b
                elif b >= s14: s15 = s14
            cur = s15
            xl = inL[i]; xr = inR[i]
            outL[i] = F(cur * xl)
            outR[i] = F(xr * cur)
            if cur < mn: mn = cur
        self.gain = cur
        self.makeup = makeup
        self.mingain = mn
        self.update_mix()                                          # vtable +0x68 = slot 26
        if self.trace is not None:
            self.trace.append({"T": T, "R": ratio(self.p[1]), "K": K, "L": L, "gt": gt, "a": a, "r": r, "ramp": r3, "k": k})

    # ---------------------------------------------------------------------------------------------------------- slot 25
    def process(self, L, R):
        """InsertFxCompressor slot 25 0xf8718 on one block (returns the new L, R; in place on the device)."""
        n = len(L); L = list(L); R = list(R)
        self.ld_copy = self.level_detect
        self.mtr[0].update(L); self.mtr[1].update(R)
        if self.ld_copy == 1: self.detect_rms(L, R, n)
        else: self.detect_peak(L, R, n)
        self.gain_stage(L, R, L, R, n)
        self.mtr[2].update(L); self.mtr[3].update(R)
        self._views()
        return L, R

    def _views(self):
        self.p[9] = self.mtr[0].cur; self.p[10] = self.mtr[1].cur; self.p[11] = self.mingain
        v = F(self.mtr[2].cur * self.makeup); self.p[12] = 2.0 if v > 2.0 else v
        v = F(self.mtr[3].cur * self.makeup); self.p[13] = 2.0 if v > 2.0 else v

    def process_send(self, L, R):
        """SendFxCompressor slot 25 0xf8270: 2 ms look-ahead line + crossfade, detector on the undelayed input."""
        n = len(L); L = list(L); R = list(R)
        self.ld_copy = self.level_detect; self.lookahead = self.lookahead_param
        nl = self.la_len; w = self.la_pos; rd = w + 1
        if rd >= nl: rd = rd - nl
        dL = [0.0] * n; dR = [0.0] * n
        for i in range(n):
            dL[i] = self.la_L[rd]; dR[i] = self.la_R[rd]
            rd = rd + 1 if rd + 1 < nl else 0
            self.la_L[w] = L[i]; self.la_R[w] = R[i]
            w = w + 1 if w + 1 < nl else 0
        self.la_pos = w
        step = -self.la_step if self.lookahead else self.la_step
        aL = [0.0] * n; aR = [0.0] * n
        for i in range(n):
            f = F(step + self.la_fade); self.la_fade = f
            if f > 1.0: self.la_fade = 1.0; f = 1.0; c = 0.0
            elif f >= 0.0: c = F(1.0 - f)
            else: self.la_fade = 0.0; f = 0.0; c = 1.0
            aL[i] = F(F(dL[i] * c) + F(f * L[i]))
            fa = self.la_fade
            aR[i] = F(F(dR[i] * F(1.0 - fa)) + F(R[i] * fa))
        self.mtr[0].update(L); self.mtr[1].update(R)
        if self.ld_copy == 1: self.detect_rms(L, R, n)
        else: self.detect_peak(L, R, n)
        self.gain_stage(aL, aR, L, R, n)
        self.mtr[2].update(L); self.mtr[3].update(R)
        self._views()
        return L, R
