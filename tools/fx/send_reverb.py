# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Send/Master "Reverb" (class `SendFxReverb`, primary vtable 0x842618 = EffectBase
part, secondary vtable 0x8426b0 = `Reverb9NXSBase` sub-object at +0x1b8; new 0x478, ctor 0x1123d0(obj, 44100, 64); index 1 of both
the Send and the Master FX processor arrays). Reconstructed in docs/effects/send-reverb.md (H005). Contains no firmware bytes: only the
documented numeric constants of the algorithm. Reuses shared blocks of insert_delay.py / send_delay.py / lofi.py.

NOT Freeverb: a 5-comb / 2-allpass stereo design (DJM-900NXS family name "Reverb9NXS").

EffectBase slot 25 0x111730, per 64-sample block (in place on L/R, output = wet only; the dry/wet sum is EffectBase slot 18):
  1. SFR slot 32 0x1120c4: mix law (Mixratio v < 0.75: dry 1, wet 4v/3; else wet 1, dry 1 - 4(v - 0.75)) -> +0x46c/+0x470,
     slot 26 0x11169c: EffectBase dry = +0x46c, wet = +0x470 * outGain (R9 +0x84 = 0.70792, set by the R9 init slot 16);
     ROOM SIZE v -> roomSet (R9 +0x60) = trunc(1 + 99 v) (1..100); COMB FILTER LPF v -> lpfStep (R9 +0x88) = trunc_u(1 + 99 (1 - v)).
  2. R9 slot 18 0x10e2e0: roomSet != roomTgt -> roomTgt = roomSet, idle = 0, slot 7 (new glide time / chunk length);
     slot 17 (= SFR slot 33 0x11185c, every block): comb delays/gains/LPF steps/spread gains and the input gain;
     slot 8 0x10e34c: chunk loop; the current room (+0x5c) steps by 1 toward roomTgt after each chunk of N = t ms (t = glide
     time 20..40 ms, slot 4 = SFR slot 35 0x111780) and every step re-runs slot 7 -> slot 17 (comb delays glide over t ms).
  3. R9 slot 9 0x10e418 per chunk: PreDelay (SFR slot 34 0x1117f0: 0..100 ms, linear-interpolated read, 1 s glide) ->
     x input gain (slot 11, 0.2 / 0.2..0.1 / 0) -> 1st-order LPF 14 kHz -> 1st-order HPF 80 Hz -> 5 parallel stereo combs
     (slot 12 0x10e924; outputs summed) -> 2 series stereo allpasses (slot 13 0x10fd28, g = 0.7).
  ReverbCombFilter 0x110b88 (per channel): y = g * ring[w - D] (D glides, truncated integer read), out = y (before damping);
  feedback: ring[w] = in + a * LPF(yL) + b * LPF(yR) (L) / in + b * LPF(yL) + a * LPF(yR) (R) with the LR-SWAP-SPREAD gains a, b.
  Comb delay (ms) = s * {22.09375, 38.666668 | 39.916668, 23.229168 | 23.854168, 40.864582 | 41.5, 24.802082 | 21.5, 23.885418}
  (L | R per comb), s = 0.2 + 0.171 (1.01 + 0.02306 room)^2; gain = 10^(-3 d / (1000 T)), T = RT60 polynomial in x = 1 + 99 v
  (REVERB TIME), blended toward 0.1 s for v <= 0.09.
"""
import math
import struct

from lofi import F, nmul, vmul_block
from chorus import LinParam
import insert_delay as ID
from insert_delay import ftz_list_add, cr_tan, HiCut
from send_delay import SteppedFilter, trunc_s32
from fdlibm_powf import powf

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "PRE DELAY", 1: "ROOM SIZE", 2: "REVERB TIME", 3: "COMB FILTER LPF", 4: "LR SWAP SPREAD", 5: "MIX RATIO"}
CTOR_DEFAULTS = {0: 0.5, 1: 0.5, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
# slot-52 defaults for index 1 (emulated bits): Send 0x11baa8 / Master 0x114ad4; they differ only in MIX RATIO (Send 1.0, Master 0.5)
SEND_DEFAULTS = [(0, 0x0), (1, 0x3efd6a05), (2, 0x3efd6a05), (3, 0x0), (4, 0x0), (5, 0x3f800000)]
MASTER_DEFAULTS = [(0, 0x0), (1, 0x3efd6a05), (2, 0x3efd6a05), (3, 0x0), (4, 0x0), (5, 0x3f000000)]
# comb delay factors (ms per unit of the room scale s), L/R for combs 1..5 (rodata 0x842408)
_MS_BITS = [0x41b0c000, 0x421aaaab, 0x421faaab, 0x41b9d556, 0x41bed556, 0x42237555, 0x42260000, 0x41c66aaa, 0x41ac0000, 0x41bf1556]
# RT60 polynomial (rodata 0x8425f8): T = c4 + c0 x^4 + c1 x^3 + c2 x^2 + c3 x
_POLY_BITS = [0x3640ca61, 0xb9af1116, 0x3c89b195, 0xbe66f1b4, 0x3fded499]
_AP_BITS = [(0x40df5554, 0x4103d555), (0x41b5eaaa, 0x41abd555)]     # allpass delays L/R (ms), gain 0.7 (R9 slot 16 0x10eae0)


def b2f(bits): return struct.unpack("<f", struct.pack("<I", bits & 0xffffffff))[0]
def f2b(x): return struct.unpack("<I", struct.pack("<f", x))[0]


COMB_MS = [(b2f(_MS_BITS[2 * i]), b2f(_MS_BITS[2 * i + 1])) for i in range(5)]   # 22.09375/38.666668 ... 21.5/23.885418
POLY = [b2f(b) for b in _POLY_BITS]                                                # 2.8728e-6, -3.3391e-4, 0.016808, -0.22553, 1.74086
AP_MS = [(b2f(a), b2f(b)) for a, b in _AP_BITS]                                    # 6.979/8.240 ms, 22.740/21.479 ms


def trunc_u32(x):
    """vcvt.u32.f32: round toward zero, saturating at 0 and 2^32-1; NaN -> 0."""
    if math.isnan(x) or x <= 0.0: return 0
    if x >= 4294967295.0: return 4294967295
    return int(x)


def clamp_lim(hi, v):
    """0x11031c(upper, value, name): value < 0 -> 0, value > upper -> upper (both also log a message); else value."""
    v = F(v)
    if v < 0.0: return F(0.0)
    if F(hi) < v: return F(hi)
    return v


K_MILLI = F(0.001)
K_FADE = F(0.003)
K_23 = b2f(0x3f2aaaab)          # 0.6666667: glide-time step (SFR slot 35)
K_TENTH = F(0.1)
K_PD_MIN = b2f(0x38d1b718)      # 0.00010000000475 (pre-delay floor 0.1 ms)


class Iir1:
    """Bare IirLpf1stOrder (vt 0x840dd8) / IirHpf1stOrder (vt 0x840db8), ctor 0xe1edc(obj, fs): coefficients 0 until the R9
    init (slot 16 0x10eae0) sets fc (LPF 14 kHz, HPF 80 Hz) and calls calcCoefs (0xe1b30 / 0xe1aa0). process = 0xe1490."""
    def __init__(self, kind, fs=FS):
        self.kind = kind; self.fs = fs; self.nyq = F(float(int(fs / 2)))
        self.b0 = self.b1 = self.a1 = self.k = F(0.0); self.v1 = [F(0.0), F(0.0)]; self.y1 = [F(0.0), F(0.0)]
        self.fc = F(F(self.nyq + F(5.0)) / F(2.0))         # ctor value (22050 + 5) / 2 = 11027.5 (unused: coefficients are 0)

    def set_fc(self, fc):
        self.fc = F(fc)
        t = cr_tan(float(self.fc) * (ID.PI / float(self.fs)))
        d = (t * ID.INV_2PI) * ID.TWO_PI
        r = 1.0 / (d + 1.0)
        if self.kind == "lpf": self.b0 = self.b1 = F(d * r)
        else: self.b0 = F(r); self.b1 = F(-r)
        self.a1 = F((d - 1.0) * r)

    def clear(self): self.v1 = [F(0.0), F(0.0)]; self.y1 = [F(0.0), F(0.0)]
    def process(self, L, R, n): HiCut._run(self, L, R, 0, n)


class ReverbComb:
    """ReverbCombFilter (vt 0x842540, new 0xc8, ctor 0x1106a0(c, fs, block)): stereo comb with gliding delay (double position,
    truncated integer read), gliding gain, damping LPF container inside the loop (+0x4c) and a 2x2 L/R spread matrix."""
    def __init__(self, fs=FS, block=BLOCK, maxf=18000.0):
        self.fs = fs; fsf = F(float(fs)); self.spm = F(fsf / F(1000.0))
        self.len = int(F(self.spm * F(101.0)))
        self.ring = [[F(0.0)] * self.len, [F(0.0)] * self.len]
        self.w = 0; self.count = 0; self.thresh = self.len; self.fade = F(0.0)
        self.fadeinc = F(F(1.0) / F(fsf * K_FADE))
        self.glide = F(100.0)
        self.ms = [F(0.0), F(0.0)]; self.d = [0.0, 0.0]; self.tgt = [F(0.0), F(0.0)]; self.dinc = [F(0.0), F(0.0)]
        self.dcnt = 0; self.dst = 0
        self.g = [F(0.0), F(0.0)]; self.gtgt = [F(0.0), F(0.0)]; self.ginc = [F(0.0), F(0.0)]; self.gcnt = 0; self.gst = 0
        self.s = [F(1.0), F(0.0)]; self.stgt = [F(1.0), F(0.0)]; self.sinc = [F(0.0), F(0.0)]; self.scnt = 0; self.sst = 0
        self.lpf = SteppedFilter("lpf", fs, 100, 2000, maxf)

    oob = 0
    def _oob(self):
        # read one float past the ring end (pos rounded up to len): firmware reads heap memory after the buffer; the emulator's
        # heap has zero padding there, so the model returns +0.0 and counts the event
        self.oob += 1; return F(0.0)

    def _n(self, ms): return trunc_s32(F(self.spm * F(ms)))

    def set_delay(self, ms, ch):                          # 0x1109d0
        ms = clamp_lim(100.0, ms)
        if ms == self.ms[ch]: return
        self.ms[ch] = ms; self.dst = -1
        t = F(F(ms * K_MILLI) * F(float(self.fs)))
        self.tgt[ch] = t
        n = self._n(self.glide); self.dcnt = n - 1
        self.dinc[ch] = F(F(float(t) - self.d[ch]) / F(float(n)))

    def set_gain(self, g, ch):                            # 0x110a7c
        g = clamp_lim(1.0, g)
        if g == self.gtgt[ch]: return
        self.gtgt[ch] = g; self.gst = -1
        n = self._n(self.glide); self.gcnt = n - 1
        self.ginc[ch] = F(F(g - self.g[ch]) / F(float(n)))

    def set_spread(self, v, ch):                          # 0x110afc
        v = clamp_lim(1.0, v)
        if v == self.stgt[ch]: return
        self.stgt[ch] = v; self.sst = -1
        n = self._n(F(3.0)); self.scnt = n - 1
        self.sinc[ch] = F(F(v - self.s[ch]) / F(float(n)))

    def reset(self):                                      # 0x110940 (+ damping container reset 0xf40f8 by the caller)
        self.w = 0; self.count = 0; self.fade = F(0.0); self.thresh = self.len
        self.d = [float(self.tgt[0]), float(self.tgt[1])]; self.dinc = [F(0.0), F(0.0)]; self.dcnt = 0; self.dst = 0
        self.g = list(self.gtgt); self.ginc = [F(0.0), F(0.0)]; self.gcnt = 0; self.gst = 0
        self.s = list(self.stgt); self.sinc = [F(0.0), F(0.0)]; self.scnt = 0; self.sst = 0

    def process(self, inL, inR, n):                       # 0x110b88 -> (outL, outR)
        L = self.len; lenf = F(float(L)); rL, rR = self.ring
        fading = self.fade < 1.0
        w0 = self.w; w = w0
        oL = [F(0.0)] * n; oR = [F(0.0)] * n
        for k in range(n):
            self.dcnt += self.dst
            if self.dcnt < 0:
                self.dinc = [F(0.0), F(0.0)]; self.dcnt = 0; self.dst = 0
                self.d = [float(self.tgt[0]), float(self.tgt[1])]
            else:
                self.d[0] += float(self.dinc[0]); self.d[1] += float(self.dinc[1])
            wf = F(float(w))
            pl = F(wf - F(self.d[0]))
            if pl < 0.0: pl = F(lenf + pl)
            pr = F(wf - F(self.d[1]))
            if pr < 0.0: pr = F(lenf + pr)
            il = int(pl); ir = int(pr)
            yl0 = rL[il] if il < L else self._oob(); yr0 = rR[ir] if ir < L else self._oob()
            if fading:
                if self.thresh < k + self.count: self.fade = F(self.fade + self.fadeinc)
                if self.fade > 1.0: self.fade = F(1.0)
            self.gcnt += self.gst
            if self.gcnt < 0:
                self.g = list(self.gtgt); self.gcnt = 0; self.gst = 0; self.ginc = [F(0.0), F(0.0)]
            else:
                self.g = [F(self.g[0] + self.ginc[0]), F(self.g[1] + self.ginc[1])]
            if fading:
                yl = F(F(self.fade * yl0) * self.g[0]); yr = F(F(self.fade * yr0) * self.g[1])
            else:
                yl = F(self.g[0] * yl0); yr = F(self.g[1] * yr0)
            oL[k] = yl; oR[k] = yr
            w = w + 1 if w < L - 1 else 0
        if fading: self.count += n
        fL = list(oL); fR = list(oR)
        self.lpf.process(fL, fR, n)
        w = w0
        for k in range(n):
            self.scnt += self.sst
            if self.scnt < 0:
                self.s = list(self.stgt); self.scnt = 0; self.sst = 0; self.sinc = [F(0.0), F(0.0)]
            else:
                self.s = [F(self.s[0] + self.sinc[0]), F(self.s[1] + self.sinc[1])]
            a, b = self.s
            rL[w] = F(F(inL[k] + F(a * fL[k])) + F(b * fR[k]))
            rR[w] = F(F(inR[k] + F(b * fL[k])) + F(a * fR[k]))
            w = w + 1 if w < L - 1 else 0
        self.w = w
        return oL, oR


class ReverbAllPass:
    oob = 0
    """ReverbAllPassFilter (vt 0x842438, new 0x60, ctor 0x10fe44(a, fs, block)): stereo Schroeder allpass with a fixed integer
    delay (truncated), y = ring[w - D] - g x, ring[w] = x + g y; 3 ms output fade-in after the first len samples."""
    def __init__(self, fs=FS, block=BLOCK):
        self.fs = fs; fsf = F(float(fs))
        self.len = (fs * 101) // 1000
        self.ring = [[F(0.0)] * self.len, [F(0.0)] * self.len]
        self.ms = [F(0.0), F(0.0)]; self.dsamp = [F(0.0), F(0.0)]; self.ng = [F(0.0), F(0.0)]; self.g = [F(0.0), F(0.0)]
        self.w = 0; self.count = 0; self.thresh = self.len; self.fade = F(0.0)
        self.fadeinc = F(F(1.0) / F(fsf * K_FADE))

    def set_delay(self, ms, ch):                          # 0x11003c
        self.ms[ch] = F(ms); self.dsamp[ch] = F(F(F(ms) * K_MILLI) * F(float(self.fs)))

    def set_gain(self, g, ch):                            # 0x110090
        self.g[ch] = F(g); self.ng[ch] = F(-F(g))

    def reset(self):                                      # 0x11001c
        self.w = 0; self.fade = F(0.0); self.count = 0; self.thresh = self.len

    def process(self, X, Y, n):                           # 0x1100d0 (in place)
        L = self.len; lenf = F(float(L)); rL, rR = self.ring
        dl, dr = self.dsamp; gl, gr = self.g; ngl, ngr = self.ng
        fading = self.fade < 1.0; s11 = F(0.0); w = self.w
        for k in range(n):
            wf = F(float(w))
            pl = F(wf - dl)
            if pl < 0.0: pl = F(lenf + pl)
            pr = F(wf - dr)
            if pr < 0.0: pr = F(lenf + pr)
            il = int(pl); ir = int(pr)
            yl0 = rL[il] if il < L else ReverbComb._oob(self); yr0 = rR[ir] if ir < L else ReverbComb._oob(self)
            xl = X[k]; xr = Y[k]
            if fading:
                if self.thresh < k + self.count: s11 = self.fadeinc
                self.fade = F(self.fade + s11)
                yl = F(F(self.fade * yl0) + F(ngl * xl)); yr = F(F(self.fade * yr0) + F(ngr * xr))
            else:
                yl = F(yl0 + F(ngl * xl)); yr = F(yr0 + F(ngr * xr))
            rL[w] = F(xl + F(gl * yl)); rR[w] = F(xr + F(gr * yr))
            X[k] = yl; Y[k] = yr
            w = w + 1 if w < L - 1 else 0
        if fading: self.count += n
        self.w = w


class ReverbPreDelay:
    """ReverbPreDelay (vt 0x8425b8, new 0x68, ctor 0x111144(p, fs, block)) at SFR +0x474: stereo delay 0.1..100 ms; delay changes
    glide over fs/1000*1000 samples (1 s); linear-interpolated read; during the 3 ms start-up fade the read is integer."""
    def __init__(self, fs=FS, block=BLOCK):
        self.fsf = fsf = F(float(fs)); self.ms = F(0.1)
        self.len = int(F(F(fsf * F(101.0)) / F(1000.0)))
        self.ring = [[F(0.0)] * self.len, [F(0.0)] * self.len]
        self.spm = F(fsf / F(1000.0))
        v = F(self.spm * self.ms)
        self.cur = self.tgt = v; self.d = float(v); self.thr = int(v)
        self.inc = F(0.0); self.cnt = 0; self.st = 0
        self.w = 0; self.count = 0; self.fade = F(0.0); self.oob = 0
        self.fadeinc = F(F(1.0) / F(fsf * K_FADE))

    def set(self, v):                                     # 0x11131c (called for ch 0 and 1; the channel is ignored)
        ms = F(F(v) * F(100.0)); self.ms = ms
        if not (ms >= F(0.1)):
            self.ms = F(0.1); self.tgt = F(self.fsf * K_PD_MIN); return
        f = K_TENTH
        if ms <= F(100.0): f = F(ms * K_MILLI)
        if F(100.0) < ms: self.ms = F(100.0)
        self.tgt = F(self.fsf * f)

    def reset(self):                                      # 0x1112b8
        self.count = 0; self.fade = F(0.0); self.w = 0; self.inc = F(0.0); self.cnt = 0; self.st = 0
        v = F(F(self.ms * K_MILLI) * self.fsf)
        self.tgt = self.cur = v; self.thr = trunc_s32(F(self.spm * K_TENTH)); self.d = float(v)

    def process(self, X, Y, n):                           # 0x11138c (in place)
        L = self.len; rL, rR = self.ring; w = self.w
        if self.fade < 1.0:
            di = int(self.d) if math.isfinite(self.d) else 0
            s12 = F(0.0)
            for k in range(n):
                rL[w] = X[k]; rR[w] = Y[k]
                w = w + 1 if w < L - 1 else 0
                if self.thr < self.count + k + 1: s12 = self.fadeinc
                f = F(s12 + self.fade)
                if f > 1.0: f = F(1.0)
                self.fade = f
                i = w - di
                if i < 0: i += L
                X[k] = F(f * rL[i]); Y[k] = F(rR[i] * f)
            self.count += n; self.w = w
            return
        lenf = F(float(L))
        if self.tgt != self.cur:
            self.cur = self.tgt; self.st = -1
            nn = trunc_s32(F(self.spm * F(1000.0))); self.cnt = nn - 1
            self.inc = F(F(float(self.tgt) - self.d) / F(float(nn)))
        for k in range(n):
            rL[w] = X[k]; rR[w] = Y[k]
            if w < L - 1: w += 1; wf = F(float(w))
            else: w = 0; wf = F(0.0)
            self.cnt += self.st
            if self.cnt < 0:
                self.inc = F(0.0); self.st = 0; self.cnt = 0; self.d = float(self.cur)
            else:
                self.d += float(self.inc)
            p = F(wf - F(self.d))
            if p < 0.0: p = F(p + lenf)
            i = int(p); fr = F(p - F(float(i)))
            if fr < 0.0: fr = F(-fr)
            j = i + 1 if i < L - 1 else 0
            om = F(F(1.0) - fr)
            if i < L: a0, b0 = rL[i], rR[i]
            else: a0 = b0 = F(0.0); self.oob += 2                     # one float past the ring end (see ReverbComb._oob)
            X[k] = F(F(a0 * om) + F(fr * rL[j])); Y[k] = F(F(b0 * om) + F(fr * rR[j]))
        self.w = w


def glide_time(cur, tgt, prev):
    """SFR slot 35 0x111780 (R9 slot 4): comb-delay glide time in ms: target 40 - 2/3 |cur - tgt| (>= 20), the previous time moves
    2/3 ms toward it per call, result >= 20."""
    d = abs(cur - tgt)
    tt = F(F(40.0) - F(F(float(d)) * K_23))
    if tt <= 20.0: tt = F(20.0)
    p = F(prev)
    if p < tt: p = F(p + K_23)
    elif p > tt: p = F(p - K_23)
    return F(20.0) if p <= 20.0 else p


def reverb_time(v):
    """RT60 in seconds from REVERB TIME v (SFR slot 33): x = 1 + 99 v; T = c4 + c0 x^4 + c1 x^3 + c2 x^2 + c3 x; v <= 0.09: T' = 0.1 + 10 v T."""
    v = F(v)
    x = F(F(1.0) + F(v * F(99.0)))
    x2 = F(x * x); x4 = F(x2 * x2); x3 = F(x * x2)
    c0, c1, c2, c3, c4 = (F(c) for c in POLY)
    acc = F(F(0.0) + F(x4 * c0)); acc = F(acc + F(c1 * x3)); acc = F(acc + F(c2 * x2)); acc = F(acc + F(c3 * x))
    T = F(c4 + acc)
    if v <= F(0.09):
        T = F(K_TENTH + F(F(v * T) * F(10.0)))
    return T


def room_scale(room):
    f = F(F(1.01) + F(F(float(room)) * F(0.02306)))
    return F(F(0.2) + F(F(f * f) * F(0.171)))


def input_gain(v):
    v = F(v)
    if v < 0.0 or v > F(1.0): return F(0.0)
    k = F(0.5137255)
    if v <= k: return b2f(0x3e4ccccd)
    return F(F(0.2) + F(F(F(v - k) * F(2.0564518)) * F(-0.1)))


def spread_gains(s):
    """LR SWAP SPREAD -> [(a, b)] for combs 1..5 (SFR slot 33): a = straight, b = swapped feedback gain."""
    s = F(s); one = F(1.0); z = F(0.0); five = F(5.0)
    def up(t): return F(F(s - F(t)) * five)
    def dn(t): return F(one - F(F(s - F(t)) * five))
    if s < F(0.2):
        return [(F(one - F(s * five)), z), (one, z), (one, z), (one, z), (z, F(s * five))]
    if s < F(0.4):
        return [(z, up(0.2)), (dn(0.2), z), (one, z), (one, z), (z, one)]
    if s < F(0.6):
        return [(z, one), (z, up(0.4)), (dn(0.4), z), (one, z), (z, one)]
    if s < F(0.8):
        return [(z, one), (z, one), (z, up(0.6)), (dn(0.6), z), (z, one)]
    return [(z, one), (z, one), (z, one), (z, up(0.8)), (z, one)]


class SendReverb:
    """SendFxReverb parameter path + Reverb9NXSBase process."""
    def __init__(self, fs=FS, block=BLOCK):
        self.fs = fs; self.block = block
        self.p = {i: LinParam(CTOR_DEFAULTS[i]) for i in range(6)}          # +0x244 + 0x5c i
        self.dry = F(1.0); self.wet = F(0.0); self.eb_dry = F(1.0); self.eb_wet = F(0.0)   # +0x46c/+0x470, EffectBase +0x10/+0x14
        # Reverb9NXSBase (+0x1b8)
        self.maxf = F(18000.0) if fs == 44100 else (F(30000.0) if fs == 96000 else (F(20500.0) if fs == 88200 else F(20000.0)))
        self.lpf = Iir1("lpf", fs); self.hpf = Iir1("hpf", fs)                # +0x1c / +0x20
        self.combs = [ReverbComb(fs, block, float(self.maxf)) for _ in range(5)]   # +0x24..+0x34 (damping +0x38..+0x48)
        self.aps = [ReverbAllPass(fs, block) for _ in range(2)]               # +0x4c / +0x50
        self.room_cur = 50; self.room_set = 50; self.room_tgt = 50            # +0x5c / +0x60 / +0x64
        self.glide_t = F(40.0)                                                 # +0x70
        self.chunk_n = trunc_s32(F(F(float(fs)) * b2f(0x3d23d70b)))          # +0x74 (fs * 0.04)
        self.chunk_rem = 0; self.idle = 1                                      # +0x78 / +0x7c
        self.in_gain = F(0.0); self.out_gain = F(0.0); self.lpf_step = 0      # +0x80 / +0x84 / +0x88
        self.pd = ReverbPreDelay(fs, block)                                    # SFR +0x474

    # -- parameters ---------------------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24 -> Parameter slot 4 (store only)
        if idx in self.p: self.p[idx].set(v); return 0
        return 3

    def defaults(self, master=False):
        for i, bits in (MASTER_DEFAULTS if master else SEND_DEFAULTS): self.set_param(i, b2f(bits))

    def slot32(self):                                   # 0x1120c4
        v = self.p[5].get()
        if v < F(0.75): self.dry = F(1.0); self.wet = F(F(v * ID.K_FOUR_THIRDS) + F(0.0))
        else: self.wet = F(1.0); self.dry = F(F(F(v - F(0.75)) * F(-4.0)) + F(1.0))
        self.eb_dry = self.dry; self.eb_wet = F(self.wet * self.out_gain)         # slot 26 0x11169c
        self.room_set = trunc_s32(F(F(1.0) + F(F(99.0) * self.p[1].get())))
        self.lpf_step = trunc_u32(F(F(1.0) + F(F(F(1.0) - self.p[3].get()) * F(99.0))))

    def slot17(self):                                   # SFR slot 33 0x11185c
        T = reverb_time(self.p[2].get())
        s = room_scale(self.room_cur)
        for c, (ml, mr) in zip(self.combs, COMB_MS):
            dl = F(s * F(ml)); dr = F(s * F(mr))
            gl = powf(F(10.0), F(F(F(dl * F(-3.0)) * K_MILLI) / T))
            gr = powf(F(10.0), F(F(F(dr * F(-3.0)) * K_MILLI) / T))
            c.set_delay(dl, 0); c.set_delay(dr, 1); c.set_gain(gl, 0); c.set_gain(gr, 1)
            c.lpf.set_step(self.lpf_step)
        for c, (a, b) in zip(self.combs, spread_gains(self.p[4].get())):
            c.set_spread(a, 0); c.set_spread(b, 1)
        self.in_gain = input_gain(self.p[2].get())

    def slot7(self):                                    # R9 0x10e540
        prev = self.glide_t if self.idle == 0 else F(40.0)
        t = glide_time(self.room_cur, self.room_tgt, prev)
        self.glide_t = t
        self.chunk_n = self.chunk_rem = trunc_s32(F(F(t * K_MILLI) * F(float(self.fs))))
        for c in self.combs: c.glide = t
        self.slot17()

    def slot6(self):                                    # R9 0x10e4d8
        if self.room_cur == self.room_tgt: self.idle = 1; return
        self.room_cur += 1 if self.room_cur < self.room_tgt else -1
        self.slot7()

    def slot16(self):                                   # R9 0x10eae0 (init: fixed filters, allpasses, output gain)
        nyq = self.lpf.nyq
        fc = F(14000.0) if F(14000.0) <= nyq else nyq
        self.lpf.set_fc(F(5.0) if fc < 5.0 else fc)
        fc = F(80.0) if F(80.0) <= nyq else nyq
        self.hpf.set_fc(fc if F(5.0) <= fc else F(5.0))
        for ap, (ml, mr) in zip(self.aps, AP_MS):
            ap.set_delay(ml, 0); ap.set_delay(mr, 1); ap.set_gain(F(0.7), 0); ap.set_gain(F(0.7), 1)
        self.out_gain = b2f(0x3f353bef)

    def chunk(self, L, R, n):                           # R9 slot 9 0x10e418 (in place)
        self.pd.set(self.p[0].get()); self.pd.set(self.p[0].get())          # SFR slot 34 0x1117f0
        self.pd.process(L, R, n)
        vmul_block(L, 0, n, self.in_gain); vmul_block(R, 0, n, self.in_gain)  # slot 11 0x10fcf4
        self.lpf.process(L, R, n); self.hpf.process(L, R, n)
        accL = [F(0.0)] * n; accR = [F(0.0)] * n                              # slot 12 0x10e924
        for c in self.combs:
            oL, oR = c.process(L, R, n)
            ftz_list_add(accL, oL, n); ftz_list_add(accR, oR, n)
        L[:] = accL; R[:] = accR
        for ap in self.aps: ap.process(L, R, n)                               # slot 13 0x10fd28

    def slot8(self, L, R):                              # R9 0x10e34c
        n = len(L); pos = 0; outL = []; outR = []
        while n > 0:
            if self.idle == 1 or (self.chunk_rem > n):
                c = n
                bl = L[pos:pos + c]; br = R[pos:pos + c]; self.chunk(bl, br, c); outL += bl; outR += br
                if self.idle != 1: self.chunk_rem -= n
                return outL, outR
            c = self.chunk_rem
            bl = L[pos:pos + c]; br = R[pos:pos + c]; self.chunk(bl, br, c); outL += bl; outR += br
            n -= c; pos += c
            self.slot6()
        return outL, outR

    def process(self, L, R):                            # EffectBase slot 25 0x111730 (returns the wet block)
        self.slot32()
        if self.room_set != self.room_tgt:              # R9 slot 18 0x10e2e0
            self.room_tgt = self.room_set; self.idle = 0; self.slot7()
        self.slot17()
        return self.slot8([F(x) for x in L], [F(x) for x in R])

    def reset(self):                                    # EffectBase slot 27 0x11208c: slot 32, R9 reset 0x10fae0, pre-delay reset
        self.slot32()
        self.slot16(); self.slot17()
        self.lpf.clear(); self.hpf.clear()
        for c in self.combs:
            c.reset()
            h = c.lpf; h.v1 = [F(0.0), F(0.0)]; h.y1 = [F(0.0), F(0.0)]          # 0xf40f8
            h.cur = h.tgt; h.acc = F(0.0); h.cut = h.tgt_cut; h._coefs()
        for ap in self.aps: ap.reset()
        self.room_cur = self.room_tgt
        self.glide_t = glide_time(self.room_tgt, self.room_tgt, F(40.0))
        self.chunk_n = 0; self.chunk_rem = 0; self.idle = 1
        self.pd.reset()
