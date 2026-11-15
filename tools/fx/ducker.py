# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
# Parts follow the public fdlibm algorithm; Sun's fdlibm notice is quoted below and must be preserved (see NOTICE.md).
"""Own-code model of the SP-16 1.60 Ducker insert effect (Insert index 9; class `Ducker`, vtable 0x841098, new 0x598, ctor 0xf61a0;
slot 25 0xf6ef4). Reconstructed in docs/effects/ducker.md (H041); contains no firmware bytes.

What it is: a *trigger-driven* gain envelope (no level detector, no sidechain audio, no free-running LFO). A trigger starts a
duck: the gain falls from 1 to 1 - DEPTH over the ATTACK time and then rises back to 1 over the RELEASE time; both segments follow
a curve whose shape is set by ATTACKCURVE / RELEASECURVE. The trigger comes from the sequencer through a per-track trigger table
(InsertFxProcessor processBlock feeds TRIGGER = table.flag[SOURCE] and OFFSET = table.offset[SOURCE] every block, see tools/fx/verify/H041_ducker_model.py).

Per block (slot 25, n samples, in place, both channels get the same gain):
  0. update (0xf6630), in this order, each with F026 change detection:
       TRIGGER (toggle) changed and on -> if state is idle(0) or release(2): offset := OFFSET (int), trigger flag := 1, control
         counter := 0; in every state the attack sample counter i := 0; then TRIGGER is written back to off (so it acts on an
         off -> on edge only);
       ATTACKCURVE / RELEASECURVE -> curve base c = (float) pow(100, 2v - 1)   (0.01 ... 100, 1 = linear);
       DEPTH -> D;  BPM, SYNC, ATTACK, RELEASE -> stored + dirty;
       if dirty: free: A = fs*ATTACK (0...1 s), Rl = 8*fs*RELEASE (0...8 s);
                 sync: q = fs*0.25*60/BPM (samples per 1/16 note), A = q*TA[rint(127 ATTACK)], Rl = q*TR[rint(127 RELEASE)];
                 Na = max(1, trunc(A)) samples, attack phase step 1/Na; release phase step 1/max(fs/1000, Rl).
  1. state machine: idle -> (trigger; skip OFFSET samples first) -> attack -> release -> idle; a trigger during release jumps
     back to attack at the phase whose curve value equals the current gain; a trigger during attack restarts its sample count.
  2. envelope: piecewise-linear interpolation between control points every 11 samples (fewer at the segment end): at each control
     point the phase x moves 11 steps ahead, target = curve(x), per-sample increment = (target - g) / count.
       attack:  target = (1 - D) + D * (1 - (c^x - 1)/(c - 1))   (linear if |c - 1| <= 2^-23: (1 - D) + D (1 - x))
       release: target = (1 - D) + D * (c^y - 1)/(c - 1), y = 1 - x + 11 r (x counts down)  (linear: (1 - D) + D y)
     the release ends (g := 1, x := 0) when x <= 0.
  3. slot 26: EffectBase dry +0x10 = 0, wet +0x14 = 1 (output = the ducked signal only; there is no Mixratio).
pow is glibc 2.13 dbl-64 (correctly rounded) -> cr_pow; log10f (retrigger only) is glibc 2.13 e_log10f/e_logf -> own port below.
"""
import ctypes, decimal, math, struct
from decimal import Decimal as Dec

_cf = ctypes.c_float
def F(x): return _cf(x).value
def fbits(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def ffrom(u): return struct.unpack("<f", struct.pack("<I", u & 0xffffffff))[0]

FS = 44100
N = 64
FLT_MIN = 1.17549435e-38
EPS_D = 2.0 ** -23                 # double literal 0x3e80000000000000 (curve |c - 1| test)
EPS_F = F(2.0 ** -23)              # float literal 0x34000000 (retrigger DEPTH test)
K_QUARTER = F(0.25); K_60 = F(60.0); K_127 = F(127.0); K_MILLI = F(0.001); K_8 = F(8.0)
NAMES = {0: "ATTACK", 1: "ATTACKCURVE", 2: "RELEASE", 3: "RELEASECURVE", 4: "NONE", 5: "DEPTH", 6: "SYNC", 7: "BPM",
         8: "TRIGGER", 9: "OFFSET", 10: "SOURCE"}
# Insert slot-52 case-9 defaults (emulated, F088-F094): (index, value). SOURCE (10) is set to (float) of the processor's own
# track index (InsertFxProcessor +0xa0); the harness stand-in processor has index 0. Use insert_defaults(own_track=k) otherwise.
INSERT_DEFAULTS = [(0, ffrom(0x3cf5c28f)), (1, 0.5), (2, ffrom(0x3d198cfc)), (3, 0.5), (5, 1.0), (6, 0.0), (10, 0.0)]

_CTX = decimal.Context(prec=60, rounding=decimal.ROUND_HALF_EVEN)


def cr_pow(x, y):
    """Correctly rounded pow for finite x > 0 (glibc 2.13 dbl-64 __ieee754_pow returns correctly rounded results)."""
    if y == 0.0: return 1.0
    if y == 1.0: return x
    with decimal.localcontext(_CTX):
        return float((Dec(y) * Dec(x).ln()).exp())


def _sync_table(segs):
    out = []
    for start, step, cnt in segs:
        for k in range(cnt): out.append(F(float(Dec(start) + Dec(step) * k)))
    return out


# Sync multipliers in 1/16 notes (128 entries each), written as decimal segments (start, step, count). The harness asserts them
# against the 1.60 tables at 0x841118 / 0x841318.
TA = _sync_table([("0", "0.01", 50), ("0.5", "0.02", 25), ("1.0", "0.05", 40), ("3.0", "0.05", 5), ("3.3", "0.1", 8)])
TR = _sync_table([("0.25", "0.05", 15), ("1.0", "0.1", 30), ("4.0", "0.2", 20), ("8.0", "0.25", 32), ("16.0", "0.5", 29),
                  ("31", "1", 2)])


def rint_d(x):                    # (double)x + 1.5*2^52, low word: round half to even
    return int(round(float(x)))


def trunc(x):                     # vcvt.s32.f32
    if x != x: return 0
    if x >= 2147483647.0: return 2147483647
    if x <= -2147483648.0: return -2147483648
    return int(x)


# ---------------------------------------------------------------------------------------------------------------------------
# glibc 2.13 log10f (sysdeps/ieee754/flt-32/e_log10f.c on e_logf.c, the fdlibm float algorithms), own re-implementation from the
# published algorithm; constants are the published fdlibm values (Sun's fdlibm notice: "Developed at SunPro, a Sun Microsystems,
# Inc. business. Permission to use, copy, modify, and distribute this software is freely granted, provided that this notice is
# preserved."). Positive finite normal arguments only (the only case reached).
_ln2_hi = ffrom(0x3f317180); _ln2_lo = ffrom(0x3717f7d1)
_Lg = [ffrom(u) for u in (0x3f2aaaab, 0x3ecccccd, 0x3e924925, 0x3e638e29, 0x3e3a3325, 0x3e1cd04f, 0x3e178897)]
_two25 = ffrom(0x4c000000); _ivln10 = ffrom(0x3ede5bd9); _log10_2hi = ffrom(0x3e9a2080); _log10_2lo = ffrom(0x355427db)


def logf(x):
    ix = fbits(x); k = 0
    if ix < 0x00800000:
        x = F(x * _two25); k -= 25; ix = fbits(x)
    k += (ix >> 23) - 127
    ix &= 0x007fffff
    i = (ix + (0x95f64 << 3)) & 0x800000
    x = ffrom(ix | (i ^ 0x3f800000))
    k += (i >> 23)
    f = F(x - 1.0)
    if (0x007fffff & (15 + ix)) < 16:
        if f == 0.0:
            if k == 0: return 0.0
            dk = F(k); return F(F(dk * _ln2_hi) + F(dk * _ln2_lo))
        R = F(F(f * f) * F(0.5 - F(F(0.33333333333333333) * f)))
        if k == 0: return F(f - R)
        dk = F(k); return F(F(dk * _ln2_hi) - F(F(R - F(dk * _ln2_lo)) - f))
    s = F(f / F(2.0 + f)); dk = F(k); z = F(s * s)
    i = ix - (0x6147a << 3); w = F(z * z); j = (0x6b851 << 3) - ix
    t1 = F(w * F(_Lg[1] + F(w * F(_Lg[3] + F(w * _Lg[5])))))
    t2 = F(z * F(_Lg[0] + F(w * F(_Lg[2] + F(w * F(_Lg[4] + F(w * _Lg[6])))))))
    i |= j; R = F(t2 + t1)
    if i > 0:
        hfsq = F(F(0.5 * f) * f)
        if k == 0: return F(f - F(hfsq - F(s * F(hfsq + R))))
        return F(F(dk * _ln2_hi) - F(F(hfsq - F(F(s * F(hfsq + R)) + F(dk * _ln2_lo))) - f))
    if k == 0: return F(f - F(s * F(f - R)))
    return F(F(dk * _ln2_hi) - F(F(F(s * F(f - R)) - F(dk * _ln2_lo)) - f))


def log10f(x):
    hx = fbits(x); k = 0
    if hx < 0x00800000:
        k -= 25; x = F(x * _two25); hx = fbits(x)
    k += (hx >> 23) - 127
    i = (k & 0x80000000) >> 31 if k >= 0 else 1
    hx = (hx & 0x007fffff) | ((0x7f - i) << 23)
    y = F(k + i)
    x = ffrom(hx)
    z = F(F(y * _log10_2lo) + F(_ivln10 * logf(x)))
    return F(z + F(y * _log10_2hi))


# ---------------------------------------------------------------------------------------------------------------------------
class LinParam:
    """LinearParameter float kind: last +0x24 / current +0x28 (setValue unclamped, change test within +-FLT_MIN)."""
    def __init__(self, d): self.last = self.cur = F(d)
    def set(self, v): self.cur = F(v)
    def changed(self):
        d = F(self.last - self.cur)
        if d <= FLT_MIN and -FLT_MIN <= d: return False
        self.last = self.cur; return True


class Toggle:
    """ToggleParameter: set v >= 1 on, v <= 0 off, else unchanged; bytes last +0x24 / current +0x25."""
    def __init__(self, d=0): self.last = self.cur = d
    def set(self, v):
        v = F(v)
        if v >= 1.0: self.cur = 1
        elif v <= 0.0: self.cur = 0
    def changed(self):
        c = self.cur != self.last
        if c: self.last = self.cur
        return c


class Choice:
    """LinearParameter choice kind: int current +0x44 = (int)v."""
    def __init__(self, d=0): self.last = self.cur = d
    def set(self, v): self.cur = trunc(F(v))


class Ducker:
    STEP = 11                                # control-point spacing in samples (literal 11.0 and the count cap 11)

    def __init__(self, fs=FS):
        self.fs = fs
        self.p = {0: LinParam(0.5), 1: LinParam(0.5), 2: LinParam(0.5), 3: LinParam(0.5), 4: LinParam(0.0), 5: LinParam(0.0),
                  6: Toggle(0), 7: LinParam(120.0), 8: Toggle(0), 9: Choice(0), 10: Choice(0)}
        # ctor state (+0x544 ... +0x594)
        self.attack = F(0.5); self.release = F(0.5); self.ca = 1.0; self.cr = 1.0; self.D = 0.0; self.sync = 0; self.bpm = F(120.0)
        self.trig = 0; self.offset = 0; self.dirty = 0; self.g = 1.0; self.inc_a = 0.0; self.inc_r = 0.0; self.cnt = 0
        self.a_done = 0; self.r_done = 0; self.x = 0.0; self.pinc = 1.0; self.pdec = 1.0; self.Na = 44; self.i = 0; self.state = 0
        self.dry = 1.0; self.wet = 0.0          # EffectBase +0x10 / +0x14 until slot 26 runs
        self.log10f = log10f; self.pow = cr_pow

    def insert_defaults(self, own_track=0):
        for i, v in INSERT_DEFAULTS: self.set_param(i, float(own_track) if i == 10 else v)

    def set_param(self, idx, v):
        if idx in self.p: self.p[idx].set(v); return 0
        return 3

    # --- 0xf6630 ----------------------------------------------------------------------------------------------------------
    @staticmethod
    def curve(v): return F(cr_pow(100.0, float(F(F(v + v) - 1.0))))

    def update(self):
        p = self.p
        if p[8].changed():
            if p[8].cur:
                off = p[9].cur
                if self.state == 0 or self.state == 2:
                    self.cnt = 0; self.offset = off; self.trig = 1
                self.i = 0
                p[8].cur = 0                                     # 0xf0614(TRIGGER, 0): current only
        if p[1].changed(): self.ca = F(self.pow(100.0, float(F(F(p[1].cur + p[1].cur) - 1.0))))
        if p[3].changed(): self.cr = F(self.pow(100.0, float(F(F(p[3].cur + p[3].cur) - 1.0))))
        if p[5].changed(): self.D = p[5].cur
        if p[7].changed(): self.bpm = p[7].cur; self.dirty = 1
        if p[6].changed(): self.sync = p[6].cur; self.dirty = 1
        if p[0].changed(): self.attack = p[0].cur; self.dirty = 1
        if p[2].changed(): self.release = p[2].cur; self.dirty = 1
        if not self.dirty: return
        fs = F(float(self.fs))
        if self.sync:
            q = F(F(F(fs * K_QUARTER) * K_60) / self.bpm)
            ia = rint_d(F(self.attack * K_127)); ir = rint_d(F(self.release * K_127))
            A = F(q * TA[ia]); Rl = F(q * TR[ir])
        else:
            A = F(fs * self.attack); Rl = F(F(fs * self.release) * K_8)
        if A < 1.0:
            self.Na = 1; self.pinc = 1.0
        else:
            self.Na = trunc(A); self.pinc = F(1.0 / F(float(self.Na)))
        self.dirty = 0
        m = F(fs * K_MILLI)
        if m <= Rl: m = Rl
        self.pdec = F(1.0 / m)

    # --- 0xf69e4 attack -----------------------------------------------------------------------------------------------------
    def _attack(self, L, R, pos, n):
        c = self.ca; D = self.D; Na = self.Na; g = self.g; x = self.x; inc = self.inc_a; cnt = self.cnt; i = self.i
        dc = float(c); curved = (dc - 1.0 > EPS_D) or (1.0 - dc > EPS_D)
        if n <= 0:
            pass
        elif Na <= i:
            self.a_done = 1; cnt = 0; x = 1.0
        elif curved:
            r5 = Na - i
            while True:
                cnt -= 1
                if cnt <= 0:
                    x = F(x + F(self.pinc * F(float(self.STEP))))
                    cnt = r5 if r5 < self.STEP else self.STEP
                    if x > 1.0: x = 1.0
                    pw = self.pow(dc, float(x))
                    d18 = 1.0 - (pw - 1.0) / float(F(c - 1.0))
                    tgt = F(float(F(1.0 - D)) + d18 * float(D))
                    inc = F(F(tgt - g) / F(float(cnt)))
                g = F(g + inc)
                L[pos] = F(L[pos] * g); R[pos] = F(R[pos] * g); pos += 1; n -= 1
                i = Na + 1 - r5
                if n <= 0: break
                r5 -= 1
                if r5 == 0:
                    self.a_done = 1; cnt = 0; x = 1.0; break
        else:
            r0 = Na - i
            while True:
                cnt -= 1
                if cnt <= 0:
                    x = F(x + F(self.pinc * F(float(self.STEP))))
                    cnt = r0 if r0 < self.STEP else self.STEP
                    s14 = 0.0; s15 = F(1.0 - D)
                    if x <= 1.0: s14 = F(1.0 - x)
                    s15 = F(F(s15 + F(D * s14)) - g)
                    if x > 1.0: x = 1.0
                    inc = F(s15 / F(float(cnt)))
                g = F(g + inc)
                L[pos] = F(L[pos] * g); R[pos] = F(R[pos] * g); pos += 1; n -= 1; i += 1; r0 -= 1
                if n == 0: break
                if i == Na:
                    self.a_done = 1; cnt = 0; x = 1.0; break
        self.g = g; self.x = x; self.i = i; self.inc_a = inc; self.cnt = cnt
        return pos, n

    # --- 0xf6c6c release ----------------------------------------------------------------------------------------------------
    def _release(self, L, R, pos, n):
        c = self.cr; D = self.D; r = self.pdec; g = self.g; x = self.x; inc = self.inc_r; cnt = self.cnt
        dc = float(c); curved = (dc - 1.0 > EPS_D) or (1.0 - dc > EPS_D)
        done = False
        if n > 0:
            x = F(x - r)
            if not (x > 0.0): done = True
            while not done:
                cnt -= 1
                if cnt <= 0:
                    s14 = F(x / r)
                    y = F(F(1.0 - x) + F(r * F(float(self.STEP))))
                    cnt = trunc(s14)
                    if cnt < 1: cnt = 1
                    if cnt >= self.STEP: cnt = self.STEP
                    if y > 1.0: y = 1.0
                    if curved:
                        pw = self.pow(dc, float(y))
                        d18 = (pw - 1.0) / float(F(c - 1.0))
                        tgt = F(float(F(1.0 - D)) + d18 * float(D))
                        inc = F(F(tgt - g) / F(float(cnt)))
                    else:
                        inc = F(F(F(F(1.0 - D) + F(y * D)) - g) / F(float(cnt)))
                g = F(g + inc)
                L[pos] = F(L[pos] * g); R[pos] = F(R[pos] * g); pos += 1; n -= 1
                if n <= 0: break
                x = F(x - r)
                if not (x > 0.0): done = True
        if done:
            self.r_done = 1; x = 0.0; g = 1.0
        self.g = g; self.x = x; self.inc_r = inc; self.cnt = cnt
        return pos, n

    # --- retrigger during release (inside slot 25) ---------------------------------------------------------------------------
    def _retrigger_phase(self):
        D = self.D; self.trig = 0
        if not (D > EPS_F): return
        c = self.ca; dc = float(c)
        if (dc - 1.0 > EPS_D) or (1.0 - dc > EPS_D):
            s17 = F(F(self.g + F(D + F(c * F(1.0 - self.g)))) - 1.0)
            if s17 <= 0.0:
                self.x = 0.0
            else:
                lc = self.log10f(c)
                self.x = F(self.log10f(F(s17 / D)) / lc)
        else:
            self.x = F(F(1.0 - self.g) / D)

    # --- slot 25 ----------------------------------------------------------------------------------------------------------
    def process(self, L, R):
        L = list(L); R = list(R); n = len(L); pos = 0
        self.update()
        while n > 0:
            st = self.state
            if st == 1:
                pos, n = self._attack(L, R, pos, n)
                if self.a_done: self.a_done = 0; self.state = 2
            elif st == 2:
                if self.trig == 0:
                    pos, n = self._release(L, R, pos, n)
                    if self.r_done: self.state = 0; self.r_done = 0
                else:
                    self._retrigger_phase(); self.state = 1
            elif st == 0:
                if self.trig == 0: break
                off = self.offset
                if off > 0:
                    if off > n: break
                    pos += off; n -= off; self.offset = 0
                self.trig = 0; self.state = 1
            else:
                raise RuntimeError("state %r" % st)
        self.dry = 0.0; self.wet = 1.0                          # slot 26 0xf6188
        return L, R

    # --- slot 27 (0xf69a8): reset = run the parameter update only --------------------------------------------------------------
    def reset(self):
        self.update()
