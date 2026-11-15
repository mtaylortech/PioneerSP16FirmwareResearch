# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code Python model of the SP-16 1.60 Insert Delay (Insert index 4; class `InsertFxDelay`, vtable 0x841c80, new 0x5d0,
ctor 0x103488; second base `DelayEchoBaseSingleDelay` at +0x1b8, vtable 0x841d10). Reconstructed in docs/effects/insert-delay.md (H039).
Contains no firmware bytes: only the documented numeric constants of the algorithm.

Slot 25 0x102cc0 per block (n = 64):
  1. slot 26 0x102ebc (mix law, EffectBase dry +0x10 / wet +0x14): v = Mixratio; v < 0.75: wet = v * 4/3, dry = 1;
     v >= 0.75: wet = 1, dry = 1 - 4 (v - 0.75). The dry/wet sum itself is done later by EffectBase slot 18 (not modelled).
  2. slot 33 0x102d3c:
     a. slot 32 0x102f30 consumes parameter changes (F026 change detection) in the order SYNC, BPM, DelayTime -> if any changed:
        delay ms = free: rint(10 + 990 v) (10..1000 ms, 1 ms steps); sync: i = rint(5 v), beats = (1/8, 1/4, 1/2, 3/4, 1, 2)[i],
        ms = beats * 60000 / BPM clamped to [10, 1000] -> DelayModuleStereo.setDelay(ms, glide=1);
        Feedback: g = 0.01 * rint(100 v) (0..1.00) -> SmoothFloat target (147-sample linear ramp);
        HiCut: step = trunc_u32(999 v) + 1 (1..1000) -> 1st-order LPF cutoff target 2000 * 10^((step-1)/999) Hz (2..20 kHz),
        glided one step per 1/3 ms. LowCut (index 3) and Spread (index 4) are stored but never read.
     b. per chunk (always the whole 64-sample block, because the delay is >= 441 samples):
        y = DelayModuleStereo.read(n)      (integer delay, ring of 46600 stereo frames, SignalGate 147-sample fade)
        y = HiCut(y)                       (IirLpf1stOrder, NEON, flush-to-zero)
        w = in + g * y                     (feedback taken after the HiCut filter; NEON multiply/add)
        out = y (wet only); DelayModuleStereo.write(w)
Delay-time changes do not glide: the gate fades the output to 0 over 147 samples, the read pointer jumps to the new delay and the
gate fades in again (147 samples). Start-up: the gate stays closed until the module has counted >= delay samples (the counter adds
the full block length once per inner read chunk), so the first echo after construction/reset is (partly) muted.
Reset (slot 27 0x102d04): parameters re-applied, pending delay committed, ring indices rewound (write 0, read = -D) WITHOUT clearing
the samples, gate closed at once, warm-up counter restarted, feedback ramp snapped to its target. The HiCut filter state is kept.
"""
import decimal
import math
from decimal import Decimal as D

from lofi import F, near, nmul, nadd, nsub, vmul_block, Smooth, SignalGate, EPS
from chorus import LinParam, Toggle, rint_idx

FS = 44100
BLOCK = 64
PARAM_NAMES = {0: "DelayTime", 1: "Feedback", 2: "HiCut", 3: "LowCut", 4: "Spread", 5: "Mixratio", 6: "SYNC", 7: "BPM"}
# Insert slot-52 case-4 defaults (emulated bits): DelayTime 49/99 (-> 500 ms), Feedback 0.7, HiCut 1.0, Mixratio 0, SYNC 0
INSERT_DEFAULTS = [(0, 0x3efd6a05), (1, 0x3f333333), (2, 0x3f800000), (5, 0x00000000), (6, 0x00000000)]
# Sync divisions (numerator, denominator) in beats, index 0..5 = rint(5 v); index 6 = the assert fallback of the table reader
SYNC_BEATS = [(1, 8), (1, 4), (1, 2), (3, 4), (1, 1), (2, 1), (64, 1)]
K_MILLI = F(0.001)          # 0x3a83126f
K_HUNDREDTH = F(0.01)       # 0x3c23d70a
K_999 = F(999.0)
K_FOUR_THIRDS = F(1.3333334)
RAMP_MS = F(3.3333333)      # 0x40555554 (gate / SmoothFloat ramp time)
PERIOD_MS = F(0.33333331)   # 0x3eaaaaaa (HiCut glide: one step per 1/3 ms)
F_FLOOR = F(5.0)            # global float 0x83bc40 (lowest cutoff passed to calcCoefs)
PI = 3.141592653589793
INV_2PI = 0.15915494309189535
TWO_PI = 6.283185307179586

_CTX = decimal.Context(prec=60, rounding=decimal.ROUND_HALF_EVEN)


# ---------------------------------------------------------------------------------------------------------------------------
# correctly rounded double tan / pow (glibc 2.13 dbl-64 tan and pow are correctly rounded; the host libm is not always)
def _dpi():
    with decimal.localcontext(_CTX) as c:
        c.prec += 5
        def atan_inv(n):
            x = D(1) / n; x2 = x * x; s = x; t = x; k = 1
            while True:
                t = -t * x2; k += 2; d = t / k
                if abs(d) < D(10) ** -(c.prec + 2): break
                s += d
            return s
        return +(16 * atan_inv(5) - 4 * atan_inv(239))
_PI_D = _dpi()


def cr_tan(x):
    if x == 0.0: return x
    with decimal.localcontext(_CTX) as c:
        c.prec = 60
        y = D(x)
        k = (y / _PI_D).to_integral_value(rounding=decimal.ROUND_HALF_EVEN)
        r = y - k * _PI_D
        r2 = r * r; s = r; t = r; n = 1
        while True:                                     # sin
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2; s += t
            if abs(t) < D(10) ** -70: break
        co = D(1); t = D(1); n = 0
        while True:                                     # cos
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2; co += t
            if abs(t) < D(10) ** -70: break
        return float(s / co)


def cr_pow(x, y):
    if y == 0.0: return 1.0
    with decimal.localcontext(_CTX) as c:
        c.prec = 60
        return float((D(y) * D(x).ln()).exp())


def cr_log10(x):
    with decimal.localcontext(_CTX) as c:
        c.prec = 60
        return float(D(x).log10())


def ftz_list_add(dst, src, n):
    """0x578a6c: dst += src; NEON (flush-to-zero) for groups of 4, VFP tail."""
    q = n - n % 4
    for k in range(n):
        dst[k] = nadd(dst[k], src[k]) if k < q else F(dst[k] + src[k])


# ---------------------------------------------------------------------------------------------------------------------------
class RingBuffer:
    """RingBuffer (vtable 0x83e5c0, ctor 0xea2a4): interleaved stereo float frames; lo +0x08 = 0, hi +0x0c = len - 1, buffer +0x18,
    write index +0x1c (int), forward read position +0x28 (double). Read 0xeaa84 (linear interpolation, used because +0x88 = 1),
    write 0xe9fe0 (slot 3 via slot 4 0xebab8), setReadDelay 0xea670."""
    def __init__(self, frames):
        self.L = frames; self.buf = [[F(0.0)] * frames, [F(0.0)] * frames]
        self.w = 0; self.pos = 0.0

    def rewind(self):                                   # slot 2 0xe9fb8: indices only (w = lo, pos = lo); the samples are KEPT
        self.w = 0; self.pos = 0.0

    def set_delay(self, d):                             # 0xea670(ring, float d, 0)
        p = float(self.w) - float(d)
        if p < 0.0: p += float(self.L)
        self.pos = p

    def read(self, n):                                  # 0xeaa84(ring, L, R, n, 0)
        pos = self.pos; i = int(pos); fr = F(pos - float(i)); om = F(F(1.0) - fr)
        bl, br = self.buf; Ln = self.L
        oL = [0.0] * n; oR = [0.0] * n
        for k in range(n):
            a = (i + k) % Ln; b = (a + 1) % Ln
            oL[k] = F(F(fr * bl[b]) + F(om * bl[a]))
            oR[k] = F(F(fr * br[b]) + F(om * br[a]))
        self.pos = float(fr) + float((i + n) % Ln if float(n) + pos + 1.0 > float(Ln - 1) else i + n)
        return oL, oR

    def write(self, L, R, n):                           # 0xe9fe0(ring, L, R, n, 0)
        bl, br = self.buf; w = self.w
        for k in range(n):
            bl[w] = L[k]; br[w] = R[k]
            w = 0 if w == self.L - 1 else w + 1
        self.w = w


class DelayModuleStereo:
    """DelayModuleStereo (vtable 0x840010, new 0x8c, ctor 0xec734(m, fs, block, maxms)) at DelayEchoBase +0xe4."""
    def __init__(self, fs=FS, block=BLOCK, maxms=1000.0):
        self.fs = fs; self.maxms = F(maxms)
        lim = int(F(F(self.maxms * K_MILLI) * F(float(fs))))
        self.ring = RingBuffer(lim + 2500)              # 46600 frames at 44.1 kHz
        self.ms = F(50.0); self.D = int(F(F(self.ms * K_MILLI) * F(float(fs))))    # ctor: 50 ms = 2205 samples
        self.pend = 0; self.pms = self.ms; self.pD = self.D
        n = int(F(F(RAMP_MS * K_MILLI) * F(float(fs))))                           # 147
        self.gate = SignalGate(fs, n)                   # SignalGate at +0x34, starts closed (0xf50b8)
        self.warm = 0; self.full = 0; self.cnt = 0      # +0x7c, +0x7d, +0x80
        self.full_thr = lim

    def samples(self, ms): return int(F(F(ms * K_MILLI) * F(float(self.fs))))

    def set_delay(self, ms, glide=1):                   # 0xec9bc
        x = F(ms)
        if not (x > 0.0): x = F(0.0) if not math.isnan(x) else x
        x = x if self.maxms > x else self.maxms
        if glide:
            ref = self.pms if self.pend else self.ms
            if near(x, ref): return
            self.pms = x; self.pend = 1; self.pD = self.samples(x)
            self.gate.close()
        else:
            self.pend = 0
            if near(x, self.ms): return
            self.ms = x; self.D = self.samples(x); self.pms = self.ms; self.pD = self.D
            self.ring.set_delay(F(float(self.D)))

    def chunk(self):                                    # 0xecacc
        return min(self.D, self.pD) if self.pend else self.D

    def _closing(self):
        r = self.gate.r
        return r.state == 1 and near(r.target, self.gate.off)

    def read(self, n):                                  # 0xecaf4(m, L, R, n)
        oL, oR = [], []
        rem = n
        while True:
            r = self.gate.r
            if self._closing(): c = min(r.rem, self.D, rem)
            else: c = min(rem, self.D)
            L, R = self.ring.read(c)
            self.gate.apply(L, R, 0, c)
            oL += L; oR += R
            rem -= c
            cflag = self.full
            if not self.full:
                self.cnt += n                           # quirk: adds the whole request per inner chunk
                self.warm = 1 if self.D <= self.cnt else 0
                if self.full_thr <= self.cnt: self.full = 1; cflag = 1
            if self.pend and r.state != 1:
                if near(r.cur, self.gate.off):          # gate fully closed: jump to the pending delay
                    self.ms = self.pms; self.D = self.pD
                    self.ring.set_delay(F(float(self.D - (n - rem))))
                    cflag = self.full; self.pend = 0
            if cflag == 0 and self.warm == 0:
                self.gate.close()
            else:
                if not self._closing():
                    self.gate.open()
            if rem < 1: return oL, oR

    def write(self, L, R, n): self.ring.write(L, R, n)  # 0xecd2c -> ring slot 4

    def reset(self):                                    # 0xec94c
        if self.pend: self.pend = 0; self.ms = self.pms; self.D = self.pD
        self.ring.rewind()
        self.ring.set_delay(F(float(self.D)))
        self.gate.r.set_now(self.gate.off)
        self.warm = 0; self.full = 0; self.cnt = 0


class HiCut:
    """1st-order low-pass container (new 0x48, ctor 0xf3ce4(c, 1 LPF, 1 order, fs, 1000 steps, 1/3 ms, 2000, 20000)) holding an
    IirLpf1stOrder (vtable 0x840dd8; calcCoefs 0xe1b30, process 0xe1490 = NEON 2-lane, flush-to-zero)."""
    def __init__(self, fs=FS, steps=1000, fmin=2000, fmax=20000):
        self.fs = fs; self.nyq = F(float(int(fs / 2))); self.steps = steps; self.fmin = fmin
        self.period = PERIOD_MS; self.mps = F(F(F(1.0) / F(float(fs))) * F(1000.0))
        self.mult = cr_pow(10.0, cr_log10(float(fmax) / float(fmin)) / float(steps - 1))   # 10^(1/999)
        self.cur = self.tgt = steps - 1; self.cut = self.tgt_cut = float(fmax); self.acc = F(0.0); self.flag = 0
        self.k = F(0.0); self.v1 = [F(0.0), F(0.0)]; self.y1 = [F(0.0), F(0.0)]
        self.fc = None; self._coefs()

    def _clampfc(self, cut):
        s13 = F(cut); s15 = s13 if s13 <= self.nyq else self.nyq
        return s15 if F_FLOOR <= s15 else F_FLOOR

    def _coefs(self):                                   # 0xf4550 -> 0xe1b30
        self.fc = self._clampfc(self.cut)
        t = cr_tan(float(self.fc) * (PI / float(self.fs)))
        d = (t * INV_2PI) * TWO_PI
        r = 1.0 / (d + 1.0)
        self.b0 = self.b1 = F(d * r); self.a1 = F((d - 1.0) * r)

    def set_step(self, idx):                            # 0xf41ac
        idx &= 0xffffffff
        if idx == 0: idx = 1
        t = min(idx, self.steps) - 1
        if t != self.tgt:
            self.tgt = t; self.tgt_cut = float(self.fmin) * cr_pow(self.mult, float(t))
        self.flag = 0

    def _step(self):                                    # 0xf4218
        if self.cur < self.tgt: self.cur += 1; self.cut = self.cut * self.mult
        elif self.cur > self.tgt: self.cur -= 1; self.cut = self.cut / self.mult
        else:
            self.cut = self.tgt_cut
            if self.flag == 0: self.cur = self.tgt
        self._coefs()

    def _run(self, L, R, i0, n):                        # 0xe1490
        b0, b1, a1, k = self.b0, self.b1, self.a1, self.k
        for ch, buf in ((0, L), (1, R)):
            v1 = self.v1[ch]; y1 = self.y1[ch]
            for j in range(i0, i0 + n):
                v = nadd(buf[j], nmul(k, y1))
                y = nsub(nadd(nmul(b0, v), nmul(b1, v1)), nmul(a1, y1))
                buf[j] = y; v1 = v; y1 = y
            self.v1[ch] = v1; self.y1[ch] = y1

    def process(self, L, R, n):                         # 0xf438c
        if self.cur == self.tgt and self.flag == 0:
            self._coefs(); self._run(L, R, 0, n); self.acc = F(0.0); return
        i0 = 0
        while n > 0:
            c = int(F(F(self.period - self.acc) / self.mps)) + 1
            c = min(c, n); n -= c
            self._run(L, R, i0, c); i0 += c
            self.acc = F(self.acc + F(F(float(c)) * self.mps))
            if self.acc < self.period: continue
            self.acc = F(self.acc - self.period)
            self._step()


class InsertDelay:
    """InsertFxDelay parameter path + DelayEchoBaseSingleDelay process (slot 25 0x102cc0 -> slot 26 0x102ebc, slot 33 0x102d3c)."""
    def __init__(self, fs=FS, block=BLOCK):
        self.fs = fs; self.block = block
        self.p = {0: LinParam(0.75), 1: LinParam(0.0), 2: LinParam(1.0), 3: LinParam(0.0), 4: LinParam(0.0), 5: LinParam(0.0),
                  6: Toggle(0), 7: LinParam(120.0)}
        self.sync_v = 0; self.bpm_v = F(120.0); self.time_v = F(0.5); self.dirty = 0      # +0x5bc / +0x5c0 / +0x5c4 / +0x5c8
        self.mod = DelayModuleStereo(fs, block, 1000.0)                                   # DelayEchoBase +0xe4 (obj +0x29c)
        n = int(F(F(RAMP_MS * K_MILLI) * F(float(fs))))
        self.fbg = Smooth(fs, n); self.fbg.set_now(F(0.0))                               # obj +0x2a0 (DelayEchoBase +0xe8)
        self.g2 = Smooth(fs, n); self.g2.set_now(F(1.0))                                 # +0x2c4 (unused by the Insert path)
        self.g3 = Smooth(fs, n); self.g3.set_now(F(0.0))                                 # +0x2e8 (unused)
        self.hicut = HiCut(fs)                                                            # obj +0x5b8
        self.dry = F(1.0); self.wet = F(0.0)
        self.ms_log = []

    # -- parameters ---------------------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24 -> Parameter slot 4
        if idx in self.p: self.p[idx].set(v); return 0
        return 3

    def insert_defaults(self):
        import struct
        for i, bits in INSERT_DEFAULTS:
            self.set_param(i, struct.unpack("<f", struct.pack("<I", bits))[0])

    @staticmethod
    def free_ms(v): return F(float(rint_idx(10, 1001, v)))

    @staticmethod
    def sync_ms(v, bpm):
        i = rint_idx(0, 6, v)
        if not (0 <= i <= 5): i = 6                     # 0x34ba88: unsigned i > 5 -> assert log + index 6
        a, b = SYNC_BEATS[i]
        ms = F(F(60000.0) / F(bpm)) if b == 0 else F(F(F(F(F(float(a)) / F(float(b))) * F(1000.0)) * F(60.0)) / F(bpm))
        if ms < F(10.0): return F(10.0)
        return F(1000.0) if ms > F(1000.0) else ms

    @staticmethod
    def feedback(v): return F(F(float(rint_idx(0, 101, v))) * K_HUNDREDTH)

    @staticmethod
    def hicut_step(v):
        x = F(F(v) * K_999)
        if math.isnan(x) or x <= 0.0: u = 0
        elif x >= 4294967296.0: u = 0xffffffff
        else: u = int(x)
        return (u + 1) & 0xffffffff

    def apply_params(self):                             # slot 32 0x102f30
        p = self.p
        if p[6].changed(): self.sync_v = p[6].get(); self.dirty = 1
        if p[7].changed(): self.bpm_v = p[7].get(); self.dirty = 1
        if p[0].changed(): self.time_v = p[0].get(); self.dirty = 1
        if self.dirty:
            ms = self.sync_ms(self.time_v, self.bpm_v) if self.sync_v else self.free_ms(self.time_v)
            self.ms_log.append(ms)
            self.mod.set_delay(ms, 1); self.dirty = 0
        if p[1].changed(): self.fbg.set_target(self.feedback(p[1].get()))
        if p[2].changed(): self.hicut.set_step(self.hicut_step(p[2].get()))

    def update_mix(self):                               # slot 26 0x102ebc
        v = self.p[5].get()
        if v >= F(0.75) or math.isnan(v):
            self.wet = F(1.0); self.dry = F(F(1.0) + F(F(v - F(0.75)) * F(-4.0)))
        else:
            self.wet = F(v * K_FOUR_THIRDS); self.dry = F(1.0)

    # -- processing ---------------------------------------------------------------------------------------------------------
    def _fb_mul(self, a, b, n):                         # 0xf5b9c(a, b, a, b, SmoothFloat, scratch, n)
        s = self.fbg
        if s.state == 1:
            g = s.gains(n); vmul_block(a, 0, n, g); vmul_block(b, 0, n, g); return
        c = s.cur
        if near(c, F(1.0)): return
        if abs(float(c)) < float(EPS):
            for k in range(n): a[k] = F(0.0); b[k] = F(0.0)
            return
        vmul_block(a, 0, n, c); vmul_block(b, 0, n, c)

    def process(self, L, R):                            # slot 25 0x102cc0 (returns the wet block)
        self.update_mix()
        self.apply_params()
        n = len(L); oL = list(L); oR = list(R); pos = 0
        while n - pos > 0:
            c = min(self.mod.chunk(), n - pos)
            yL, yR = self.mod.read(c)
            self.hicut.process(yL, yR, c)
            wL = list(yL); wR = list(yR)
            self._fb_mul(wL, wR, c)
            ftz_list_add(wL, L[pos:pos + c], c); ftz_list_add(wR, R[pos:pos + c], c)
            oL[pos:pos + c] = yL; oR[pos:pos + c] = yR
            self.mod.write(wL, wR, c)
            pos += c
        return oL, oR

    def reset(self):                                    # slot 27 0x102d04: slot 32, then DelayEchoBase slot 4 0x103d20
        self.apply_params()
        self.apply_params()                             # 0x103d20 calls own slot 8 -> 0x102f28 -> slot 32 again
        self.mod.reset()
        self.fbg.set_now(self.fbg.target); self.g2.set_now(self.g2.target); self.g3.set_now(self.g3.target)
