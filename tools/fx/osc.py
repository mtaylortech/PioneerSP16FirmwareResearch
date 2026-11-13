# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 shared vtable-less modulation oscillator (0x98-byte object; ctor 0x100af0 ->
init 0x100710, stereo process 0x101bdc). Reconstructed in docs/effects/oscillator.md; contains no firmware bytes.

Used by c_chorus (0xff008), c_flanger (0x100234), c_distortion (0xfa568), Phaser (0x10d654) and LfoProcessor (0x135da0).
It is NOT the RTTI `LFO` class (F047).

Object layout (offsets of the 1.60 object; names are ours):
  +0x00 amp (f32)        +0x04 off (f32)        +0x08 id (i32)          +0x0c wave (i32, -1 = invalid)
  +0x10 freq Hz (f32)    +0x18 1/fs (f64)       +0x20 slope / sine step w (f64)
  +0x28 sine cos(w) | pulse duty (f64)           +0x30 sine 2cos(w) (f64)    +0x38 sine sin(w) (f64)
  +0x40 sine y[n] | other: phase position c*k (f64, used by hold mode)        +0x48 sine y[n-1] | random held L value (f64)
  +0x50 R phase offset (f32; sine: cos(2*pi*ph))  +0x54 sine sin(2*pi*ph) | random held R value (f32)
  +0x58/+0x5c smoothing a = 1-e, b = e (f32)      +0x60/+0x64 smoothing state L/R (f32)
  +0x68 resync counter (u32)  +0x6c resync period = fs (u32)  +0x70 hold flag (f64)  +0x78 smoothing-off flag (f64)
  +0x80 counter c (f32)  +0x84 period-1 P (f32)  +0x88 random index offset (u32)  +0x8c random index (u32)  +0x90 -> table

Waveforms (process, per sample; c += 1 and wraps at P; k = (float)slope; ph = +0x50):
  0 sine     recursive oscillator in double: y = 2cos(w)*y1 - y2; L = (float)(sin(w)*y) clamped to +-1 (the clamp also resets
             the recursion); R = ph*L - (float)(y1' - y*cos(w))*ph2  (= sin(theta + phase offset))
  1 triangle k = 4f/fs: x = c*k - 1 (c <= P/2) or 3 - c*k; R uses c + P*ph/4
  2 saw      k = -2f/fs (always negative): x = 1 + c*k (falling ramp); R uses c + P*ph/2
  3,4,5 pulse duty d = 0.5 / 0.25 / 0.125: x = +1 if c <= d*P else -1; R uses c + P*ph
  6 random   sample-and-hold of an 8192-entry table (firmware .data 0xb70e50, supplied by the caller), one new value per
             period; R leads (ph < 0.5) or L leads (ph >= 0.5), the other channel takes the previous value on its own wrap.
then out = off + amp*x and an optional one-pole smoother y = a*x + b*y (a = 1 - b, b = exp(-2*pi*hz/fs)).

Float32 arithmetic is modelled with F() (round to nearest even); double arithmetic is Python float. VFP vmla/vmls are
modelled unfused (two roundings), as on the Cortex-A9 VFPv3. libm calls (sincos/cos/acos double; cosf/sinf/expf/acosf
float) go through the injectable `libm` object; the default OwnLibm uses crmath.py / fdlibm_sincosf.py.
"""
import math, struct
import crmath as CR
import fdlibm_sincosf as SCF

F32 = struct.Struct("<f")
U32 = struct.Struct("<I")


def F(x):
    return F32.unpack(F32.pack(x))[0]


def bits(x): return U32.unpack(F32.pack(x))[0]
def fbits(u): return F32.unpack(U32.pack(u & 0xffffffff))[0]


TWO_PI = 6.283185307179586                 # double literal (0x401921fb54442d18)
TWO_PI_F = F(6.2831855)                    # float literal 0x40c90fdb
NEG_TWO_PI_F = F(-6.2831855)               # float literal 0xc0c90fdb (setSmoothingHz)
SMOOTH_INIT_K = F(-314.15927)              # float literal 0xc39d1463 (= -2*pi*50: init smoothing 50 Hz)
F_MIN = F(0.0044100005)                    # float literal 0x3b9081c4 (frequency floor)
P_FLOOR = F(9999998.0)                     # setFrequency period for f <= F_MIN
TABLE_N = 0x2000


class OwnLibm:
    """Default: own re-implementations matching the 1.60 glibc 2.13 libm — correctly rounded double sin/cos/acos
    (crmath, = glibc dbl-64), fdlibm float sinf/cosf (fdlibm_sincosf), correctly rounded expf/acosf (glibc expf is NOT
    always correctly rounded: rare 1-ulp differences, see docs/effects/oscillator.md)."""
    def sincos(self, x): return CR.sincos(x)
    def cos(self, x): return CR.cos(x)
    def acos(self, x): return CR.acos(x)
    def cosf(self, x): return SCF.cosf(x)
    def sinf(self, x): return SCF.sinf(x)
    def expf(self, x): return CR.expf(x)
    def acosf(self, x): return F(CR.acos(x))


class HostLibm:
    """Host math as a stand-in for the 1.60 glibc libm (double sin/cos/acos; float cosf/sinf/expf/acosf)."""
    def sincos(self, x): return math.sin(x), math.cos(x)
    def cos(self, x): return math.cos(x)
    def acos(self, x): return math.acos(x)
    def cosf(self, x): return F(math.cos(x))
    def sinf(self, x): return F(math.sin(x))
    def expf(self, x): return F(math.exp(x))
    def acosf(self, x): return F(math.acos(x))


def _wrap01(ph):
    ph = F(ph)
    while ph < 0.0: ph = F(ph + 1.0)
    while ph >= 1.0: ph = F(ph - 1.0)
    return ph


class Osc:
    """Mirror of the 1.60 oscillator object. `table` = list of >= 8193 floats (8192 table words + the following word,
    reachable by an index-wrap quirk); `libm` = HostLibm-like object."""

    def __init__(self, table=None, libm=None, id_before=0, rand_off=0, counter=0.0):
        self.table = table; self.libm = libm or OwnLibm()
        # fields not written by init keep their previous memory content (here: caller-supplied)
        self.id = id_before & 0xffffffff; self.r_off = rand_off & 0xffffffff; self.c = F(counter)
        self.amp = F(1.0); self.off = F(0.0); self.wave = -1; self.freq = F(0.0)
        self.inv_fs = self.slope = self.d28 = self.d30 = self.d38 = self.d40 = self.d48 = 0.0
        self.ph = self.ph2 = F(0.0); self.c58 = self.c5c = F(0.0); self.sm = [F(0.0), F(0.0)]
        self.rs_cnt = 0; self.rs_per = 0; self.hold = 0.0; self.smooth_off = 0.0; self.P = F(0.0); self.r_idx = 0

    # ---------------------------------------------------------------- construction --------------------------------
    @classmethod
    def ctor(cls, wave, freq, fs, id_counter, table=None, libm=None, id_before=0, rand_off=0, counter=0.0):
        """0x100af0(obj, wave, freq, fs): init (which reads the id word BEFORE it is assigned), then table pointer and
        id = global counter 0xb70e4c (post-increment). Returns (osc, new counter)."""
        o = cls(table, libm, id_before, rand_off, counter)
        o.init(wave, freq, fs)
        o.id = id_counter & 0xffffffff
        return o, id_counter + 1

    def init(self, wave, freq, fs):                                    # 0x100710(obj, wave, freq, fs) -> 0/1
        freq = F(freq); fs = int(fs)
        x = (self.id * 448) & 0xffffffff
        if self.r_off > 0x2000: self.r_off = 0
        fsu = fs & 0xffffffff
        self.rs_cnt = x
        self.wave = -1; self.off = F(0.0); self.freq = F(0.0)
        self.inv_fs = self.slope = self.d28 = self.d30 = self.d38 = self.d40 = self.d48 = 0.0
        self.amp = F(1.0); self.ph = self.ph2 = F(0.0)
        self.rs_per = fsu; self.r_idx = 0
        if fsu < x:
            while fsu < x: x = (x - fsu) & 0xffffffff
            self.rs_cnt = x
        self.hold = 0.0
        if fs <= 0: return 0
        self.inv_fs = 1.0 / float(fs)
        e = self.libm.expf(F(F(self.inv_fs) * SMOOTH_INIT_K))
        self.smooth_off = 0.0; self.sm = [F(0.0), F(0.0)]
        self.c5c = e; self.c58 = F(1.0 - e)
        if freq == 0.0: return 0
        fsf = F(float(fs))
        if freq <= F_MIN: freq = F_MIN
        P = F(F(fsf / freq) - 1.0)
        if P < 1.0: P = F(1.0)
        self.P = P
        if not 0 <= wave <= 6: return 0
        if wave == 0:
            w = (float(abs(freq)) * TWO_PI) * self.inv_fs
            s, c = self.libm.sincos(w)
            self.slope = w; self.d28 = c; self.ph, self.ph2 = F(1.0), F(0.0)
            self.d38 = s; self.d48 = 0.0; self.d40 = 1.0; self.d30 = c + c
        elif wave == 1:
            self.ph = F(0.0); self.d40 = 1.0
            self.slope = (self.inv_fs * 4.0) * float(freq); self.c = F(P * 0.25)
        elif wave == 2:
            self.c = F(0.0); self.ph = F(0.0); self.d40 = 2.0
            self.slope = (self.inv_fs * -2.0) * float(freq)
        elif wave in (3, 4, 5):
            self.d28 = {3: 0.5, 4: 0.25, 5: 0.125}[wave]
            if freq < 0.0 and wave != 3: self.d28 = {4: 0.75, 5: 0.875}[wave]     # unreachable: freq >= F_MIN here
            self.slope = self.inv_fs * float(freq)
            self.c = F(0.0); self.d40 = 0.0; self.ph = F(0.0)
        else:                                                          # 6 random
            self.d40 = 0.0; fa = abs(freq); self.c = F(0.0)
            idx = self.r_idx + self.r_off
            if idx >= 0x2000: idx -= 0x2000
            self.r_idx = self.r_idx + 1 if self.r_idx < 0x2000 else 0
            v = F(self.table[idx])
            self.ph2 = v; self.ph = F(0.0)
            self.slope = self.inv_fs * float(fa); self.d48 = float(v)
        self.freq = freq; self.wave = wave
        return 1

    # ---------------------------------------------------------------- setters --------------------------------------
    def set_frequency(self, f):                                        # 0x101090 -> 1/0
        f = F(f)
        if f == 0.0: self.hold = 1.0; return 1
        Pold = self.P
        if f <= F_MIN:
            Pn = P_FLOOR; f = F_MIN; self.P = Pn
        else:
            Pn = F(F(F(44100.0) / f) - 1.0)                            # literal 44100, not fs
            self.P = Pn
            if Pn < 1.0: Pn = F(1.0); self.P = Pn
        self.c = _fdiv(F(Pn * self.c), Pold)                          # counter rescaled to the new period
        w_ = self.wave
        if w_ == 0:
            fa = abs(f)
            w = (float(fa) * TWO_PI) * self.inv_fs
            y1, s_old, cw_old, y2 = self.d40, self.d38, self.d28, self.d48
            d10 = y1 * s_old
            d11 = y2 - y1 * cw_old
            s, c = self.libm.sincos(w)
            self.slope = w; self.d28 = c; self.d38 = s
            d18 = (d10 * c) / s
            self.d40 = d10 / s; self.d30 = c + c
            self.d48 = d18 + d11
        elif w_ == 1: self.slope = (self.inv_fs * 4.0) * float(f)
        elif w_ == 2: self.slope = (self.inv_fs * -2.0) * float(f)
        elif w_ == 3: self.d28 = 0.5; self.slope = self.inv_fs * float(f)
        elif w_ in (4, 5):
            self.d28 = 0.25 if w_ == 4 else 0.125
            self.slope = self.inv_fs * float(f)
            if f < 0.0: self.d28 = 0.75 if w_ == 4 else 0.875
        elif w_ == 6: self.slope = self.inv_fs * float(abs(f))
        else: return 0
        self.freq = f
        return 1

    def set_period_ms(self, ms):                                       # 0x101320
        ms = F(ms)
        if ms == 0.0: return 0
        return self.set_frequency(F(F(1000.0) / ms))

    def set_phase_offset(self, ph):                                    # 0x1017d4 (R-channel offset, cycles)
        if self.freq == 0.0: return 0
        ph = _wrap01(ph)
        if self.wave == 0:
            a = F(ph * TWO_PI_F); self.ph = self.libm.cosf(a); self.ph2 = self.libm.sinf(a)
        elif self.wave == 1: self.ph = F(ph * 4.0)
        elif self.wave == 2: self.ph = F(ph + ph)
        elif 3 <= self.wave <= 6: self.ph = ph
        else: return 0
        return 1

    def reset_phase(self, ph):                                         # 0x101440
        if self.freq == 0.0: return 0
        ph = _wrap01(ph)
        w_ = self.wave
        if w_ == 0:
            d8 = float(ph) * TWO_PI
            s = self.d38
            self.d40 = self.libm.cos(d8) / s
            self.d48 = self.libm.cos(d8 - self.slope) / s
            self.c = F(self.P * ph)
        elif w_ == 1:
            d16 = 1.0 + float(ph) * 4.0
            self.d40 = d16
            c = F(F(ph + 0.25) * self.P)
            self.c = c
            if d16 >= 4.0: self.d40 = d16 - 4.0
            if self.P < c: self.c = F(c - self.P)
        elif w_ == 2: self.c = F(self.P * ph); self.d40 = float(ph) + float(ph)
        elif 3 <= w_ <= 6: self.c = F(self.P * ph); self.d40 = float(ph)
        else: return 0
        return 1

    def set_smoothing_hz(self, hz):                                    # 0x1019f0
        hz = F(hz)
        if not self.inv_fs > 0.0: return 0
        if not hz > 0.0: self.c5c = F(0.0); self.c58 = F(1.0); return 1
        e = self.libm.expf(F(F(hz * NEG_TWO_PI_F) * F(self.inv_fs)))
        self.c5c = e; self.c58 = F(1.0 - e)
        return 1

    def set_amplitude(self, a): self.amp = F(a); return 1             # 0x1019d8
    def set_offset(self, o): self.off = F(o); return 1                # 0x1019e4
    def set_smoothing_off(self, v): self.smooth_off = float(v & 0xffffffff)  # 0x102cb0 (u32 -> double)
    def set_rand_offset(self, k): self.r_off = k & 0xffffffff         # 0x102c50
    def set_hold(self): self.hold = 1.0                               # 0x102c3c
    def clear_hold(self): self.hold = 0.0                             # 0x102c2c

    def resync(self):                                                  # 0x101b30
        if self.wave == 0:
            y1, s, y2 = self.d40, self.d38, self.d48
            v = y1 * s
            dr = 1.0 if y1 <= y2 or y1 != y1 or y2 != y2 else -1.0
            if v > 1.0: v = 1.0
            elif v < -1.0: v = -1.0
            self.d40 = v / s
            a = self.libm.acos(v)
            self.d48 = self.libm.cos(a * dr - self.slope) / s
        self.rs_cnt = 0
        return 1

    # ---------------------------------------------------------------- process --------------------------------------
    def process(self, n):
        """0x101bdc(obj, L, R, n). Returns (L, R) lists, or None when the waveform is invalid (buffers untouched, ret 0)."""
        if not 0 <= self.wave <= 6: return None
        if self.hold != 0.0:
            Lc, Rc = self._hold_values()
            L = [Lc] * max(n, 0); R = [Rc] * max(n, 0)
        else:
            L, R = [0.0] * max(n, 0), [0.0] * max(n, 0)
            getattr(self, "_run%d" % {0: 0, 1: 1, 2: 2, 3: 3, 4: 3, 5: 3, 6: 6}[self.wave])(L, R, n)
            self.rs_cnt = (self.rs_cnt + n) & 0xffffffff
            if self.rs_cnt > self.rs_per: self.resync()
        amp, off = self.amp, self.off
        for i in range(max(n, 0)):
            L[i] = F(off + F(amp * L[i])); R[i] = F(off + F(amp * R[i]))
        if self.smooth_off == 0.0:
            a, b = self.c58, self.c5c
            y0, y1 = self.sm
            for i in range(max(n, 0)):
                y0 = F(F(a * L[i]) + F(b * y0)); L[i] = y0
                y1 = F(F(a * R[i]) + F(b * y1)); R[i] = y1
            self.sm = [y0, y1]
        else:
            self.sm = [F(0.0), F(0.0)]
        return L, R

    def _hold_values(self):
        w_ = self.wave; ph = self.ph
        if w_ == 0:
            Lc = F(self.d40 * self.d38)
            t = self.d48 - self.d40 * self.d28
            Rc = F(F(Lc * ph) - F(F(t) * self.ph2))
        elif w_ == 1:
            d = self.d40; f = F(d)
            Lc = F(3.0 - f) if d > 2.0 else F(f - 1.0)
            t = F(f + ph)
            if t >= 4.0: t = F(t - 4.0)
            Rc = F(3.0 - t) if t > 2.0 else F(t - 1.0)
        elif w_ == 2:
            f = F(self.d40); t = F(f + ph); Lc = F(f - 1.0)
            if t >= 2.0: t = F(t - 2.0)
            Rc = F(t - 1.0)
        elif w_ in (3, 4, 5):
            d = self.d40; f = F(d); t = F(f + ph)
            Lc = F(1.0) if d <= self.d28 else F(-1.0)
            if t >= 1.0: t = F(t - 1.0)
            Rc = F(-1.0) if self.d28 < float(t) else F(1.0)
        else:
            Lc = F(self.d48); Rc = self.ph2
        return Lc, Rc

    def _run0(self, L, R, n):                                          # sine, 0x1021c0
        s = self.d38; ph, ph2 = self.ph, self.ph2
        inv = 1.0 / s if s != 0.0 else 1.0
        if n > 0:
            k2, cw, ninv = self.d30, self.d28, -inv
            y1, y2 = self.d40, self.d48
            for i in range(n):
                y = k2 * y1 - y2
                x = F(s * y)
                if x > 1.0:
                    x = F(1.0); prev = inv; cur = inv
                elif x < -1.0:
                    x = F(-1.0); prev = ninv; cur = ninv
                else:
                    prev = y1; cur = y
                L[i] = x
                q = prev - cur * cw
                R[i] = F(F(ph * x) - F(F(q) * ph2))
                y1, y2 = cur, prev
            self.d40, self.d48 = y1, y2
        c = F(self.c + F(float(n))); P = self.P
        if not P > c:
            c = F(c - P)
            while P <= c: c = F(c - P)
        self.c = c

    def _run1(self, L, R, n):                                          # triangle, 0x101e14 / 0x10252c
        P = self.P; q = F(P * 0.25); k = F(self.slope); offR = F(q * self.ph); half = F(P * 0.5); c = self.c
        pos = not (k < 0.0)
        def tri(t):
            ck = F(t * k)
            if pos: return F(3.0 - ck) if t > half else F(ck - 1.0)
            return F((3.0 if t > half else 1.0) + ck)
        for i in range(max(n, 0)):
            c = F(c + 1.0)
            if c >= P: c = F(c - P)
            L[i] = tri(c)
            cr = F(c + offR)
            if cr >= P: cr = F(cr - P)
            R[i] = tri(cr)
        self.d40 = float(c) * float(k) if pos else -(float(c) * float(k))
        self.c = c

    def _run2(self, L, R, n):                                          # saw, 0x101f08 / 0x1024bc
        P = self.P; offR = F(F(P * self.ph) * 0.5); k = F(self.slope); c = self.c
        pos = not (k < 0.0)
        for i in range(max(n, 0)):
            c = F(c + 1.0)
            if c >= P: c = F(c - P)
            cr = F(c + offR)
            if cr >= P: cr = F(cr - P)
            if pos: L[i] = F(F(c * k) - 1.0); R[i] = F(F(cr * k) - 1.0)
            else: L[i] = F(1.0 + F(c * k)); R[i] = F(1.0 + F(cr * k))
        self.d40 = float(c) * float(k) if pos else -(float(c) * float(k))
        self.c = c

    def _run3(self, L, R, n):                                          # pulse 3/4/5, 0x101fa0 / 0x102430
        P = self.P; offR = F(P * self.ph); k = F(self.slope); thr = F(F(self.d28) * P); c = self.c
        pos = not (k < 0.0)
        one, mone = F(1.0), F(-1.0)
        for i in range(max(n, 0)):
            c = F(c + 1.0)
            if c >= P: c = F(c - P)
            cr = F(c + offR)
            if pos: L[i] = one if not c > thr else mone
            else: L[i] = mone if c < thr else one
            if cr >= P: cr = F(cr - P)
            R[i] = one if not cr > thr else mone
        self.d40 = float(c) * float(k) if pos else -(float(c) * float(k))
        self.c = c

    def _fetch(self):
        idx = (self.r_idx + self.r_off) & 0xffffffff
        if idx > 0x1fff: idx = (idx - 0x2000) & 0xffffffff
        self.r_idx = 0 if self.r_idx > 0x1fff else self.r_idx + 1
        return bits(F(self.table[idx]))

    def _run6(self, L, R, n):                                          # random, 0x102058
        P = self.P; cL = self.c; ph = self.ph
        cR = F(cL + F(ph * P))
        if cR >= P: cR = F(cR - P)
        k = F(self.slope); vL = bits(F(self.d48)); vR = bits(self.ph2)
        if n > 0:
            if not ph >= 0.5 and ph == ph:                             # branch A: R leads
                r8 = vR
                for i in range(n):
                    cR = F(cR + 1.0)
                    if not P > cR:
                        r8 = vR
                        while True:
                            cR = F(cR - P); vR = self._fetch()
                            if P > cR: break
                            r8 = vR
                    cL = F(cL + 1.0)
                    R[i] = fbits(vR)
                    if not P > cL:
                        while True:
                            cL = F(cL - P)
                            if P > cL: break
                        vL = r8
                    L[i] = fbits(vL)
            else:                                                      # branch B: L leads
                sl = vL
                for i in range(n):
                    cL = F(cL + 1.0)
                    if not P > cL:
                        sl = vL
                        while True:
                            cL = F(cL - P); vL = self._fetch()
                            if P > cL: break
                            sl = vL
                    cR = F(cR + 1.0)
                    L[i] = fbits(vL)
                    if not P > cR:
                        while True:
                            cR = F(cR - P)
                            if P > cR: break
                        vR = sl
                    R[i] = fbits(vR)
        self.ph2 = fbits(vR); self.c = cL
        self.d40 = float(cL) * float(k)
        self.d48 = float(fbits(vL))


def _fdiv(a, b):
    """float32 division with IEEE semantics for b == 0 (inf / nan), as VFP vdiv.f32."""
    if b == 0.0:
        if a == 0.0 or a != a: return float("nan")
        return math.copysign(float("inf"), a) * math.copysign(1.0, b)
    return F(a / b)
