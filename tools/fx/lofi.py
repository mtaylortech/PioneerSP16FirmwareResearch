# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python model of the TORAIZ SP-16 1.60 LoFi insert effect, slot 25 (0xfc0f4) and its parameter path.

Own re-implementation written from the analysis in docs/effects/lofi.md. It contains no firmware bytes. Constants are
the documented numeric values of the algorithm (e.g. 42 dB preamp range, 44.1 Hz..44.1 kHz rate, 20 Hz..20 kHz cutoff, bit-depth
table). Arithmetic mirrors the 1.60 code's precision: float32 for VFP single-precision steps, float64 for double steps,
flush-to-zero for NEON steps (biquad, gate gain multiply), libm pow/tan/log10f via the host (double, then rounded).
Pure Python (no numpy): float32 ops are computed in double and rounded to float32, which is exact for + - * / sqrt.

Signal flow per 64-sample block (all addresses 1.60):
  fc0f4  apply changed parameters (fb20c) -> position-gate bookkeeping -> fbf64 -> slot 26 if MIXRATIO changed
  fbf64  position SignalGate gain on the input (f521c), then
           position 0 (PRE):   filter (fbb70) -> preamp/clipper (fb6e4) -> crusher (faf28, only bits < 32) -> sample-and-hold
           position != 0:      preamp -> crusher -> sample-and-hold -> filter
  filter container fbb70: cutoff / Q exponential step ramp (one step per 44.1 samples), sub-filter IirHpf/IirLpf/IirBpf/IirOff,
           its own SignalGate for type switches and large cutoff jumps (> 38 steps).
Usage:
  m = LoFi(); m.insert_defaults(); m.set_param(idx, value); L, R = m.process(L, R)   (lists of floats, one block)
"""
import ctypes, math

_cf = ctypes.c_float
def F(x):
    """Round a Python float (double) to float32 (round-to-nearest-even, overflow -> inf); result is a Python float."""
    return _cf(x).value
EPS = F(1.1920929e-07)          # FLT_EPSILON, used by every |a-b| < eps test
FLT_MIN = 1.17549435e-38
FS = 44100
TWO_PI = 6.283185307179586
INV_TWO_PI = 0.15915494309189535
FOUR_PI2 = 39.47841760435743
EIGHT_PI2 = 78.95683520871486

# BITDEPTH: bits = BITS[round(17 * v)]; >= 32 means "crusher off"
BITS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 24, 100]
INSERT_DEFAULTS = {0: 0.0, 2: 1.0, 1: 1.0, 3: 0.566, 4: 0.0510204, 5: 1.0, 6: 3.0, 7: 1.0}   # F025 (slot 52 case 5)
PARAM_NAMES = ["PREAMP", "REDUCTION", "BITDEPTH", "CUTOFF", "RESONANCE", "MIXRATIO", "FILTERTYPE", "FILTERPOSITION"]


def f32(x): return F(x)
def log10f(x): return F(math.log10(float(x)))
def rnd(x): return int(round(float(x)))          # double + 1.5*2^52 trick = round half to even
def near(a, b):
    d = F(F(a) - F(b))
    if d <= 0: d = -d
    return d < EPS


def ftz(x):
    x = F(x)
    if x != 0 and abs(float(x)) < FLT_MIN:
        return F(math.copysign(0.0, float(x)))
    return x
def nmul(a, b): return ftz(F(ftz(a) * ftz(b)))
def nadd(a, b): return ftz(F(ftz(a) + ftz(b)))
def nsub(a, b): return ftz(F(ftz(a) - ftz(b)))


# globals written by the .init_array initialiser 0x137cc
G0 = F(17.0)
G3 = F(math.pow(10.0, float(F(log10f(50.0) / F(100.0)))))      # Q step multiplier up   (50^(1/100))
G4 = F(F(1.0) / G3)
G1 = F(math.pow(10.0, float(F(log10f(1000.0) / F(250.0)))))    # cutoff step multiplier up (1000^(1/250))
G2 = F(F(1.0) / G1)


class Param:
    """LinearParameter (vtable 0x840ac8): float kind keeps last/current at +0x24/+0x28, choice kind at +0x40/+0x44."""
    def __init__(self, kind, default):
        self.kind = kind
        self.last = self.cur = (F(default) if kind == "float" else int(default))
    def set(self, v):                                   # slot 4 0xf0874 (reached from EffectBase slot 14)
        if self.kind == "float": self.cur = F(v)
        else: self.cur = int(F(v))                       # vcvt.s32.f32: truncate
    def changed(self):                                  # 0xf0ffc
        if self.kind == "choice":
            c = self.last != self.cur
            if c: self.last = self.cur
            return c
        d = F(self.last - self.cur)
        if d <= FLT_MIN and -FLT_MIN <= d: return False
        self.last = self.cur
        return True
    def get(self):                                      # 0xf0898
        return self.cur if self.kind == "float" else F(self.cur)


class Smooth:
    """SmoothFloat (ramp at SignalGate+0x1c): linear ramp of N samples."""
    def __init__(self, fs, n):
        self.state = 0; self.cur = F(0); self.target = F(0); self.inc = F(0); self.rem = 0
        self.N = n; self.invN = F(F(1.0) / F(n))
    def set_now(self, v):                               # 0xf5584
        self.state = 0; self.cur = F(v); self.target = F(v); self.inc = F(0); self.rem = 0
    def set_target(self, v):                            # 0xf5668
        v = F(v)
        if near(v, self.target): return
        self.target = v; self.state = 1; self.rem = self.N
        self.inc = F(F(v - self.cur) * self.invN)
    def gains(self, n):                                 # 0xf55a4
        g = []; c = self.cur; rem = self.rem
        if n < 1: return g
        if self.state != 0:
            if n < rem:
                for _ in range(n): g.append(c); c = F(c + self.inc)
                self.cur = c; self.rem = rem - n; return g
            for _ in range(max(rem, 0)): g.append(c); c = F(c + self.inc)
            self.state = 0; c = self.target; rem = 0
        g += [c] * (n - len(g))
        self.cur = c; self.rem = rem
        return g


def vmul_block(buf, i0, n, gains):
    """0x579018 / 0x579178: NEON (flush-to-zero) for groups of 4, VFP for the n % 4 tail."""
    q = n - n % 4
    for k in range(n):
        g = gains[k] if isinstance(gains, list) else gains
        buf[i0 + k] = nmul(buf[i0 + k], g) if k < q else F(buf[i0 + k] * g)


class SignalGate:
    """SignalGate (vtable 0x840e40), size 0x48: off = 0.0 (+0x40), on = 1.0 (+0x44), ramp at +0x1c; starts closed (0xf50b8)."""
    def __init__(self, fs, n):
        self.r = Smooth(fs, n); self.off = F(0.0); self.on = F(1.0)
        self.r.set_now(self.off)
    def open(self): self.r.set_target(self.on)          # 0xf5198
    def close(self): self.r.set_target(self.off)        # 0xf5188
    def apply(self, L, R, i0, n):                       # 0xf521c -> 0xf5a54
        r = self.r
        v = r.target if r.state == 1 else r.cur
        if not near(v, self.off) and not near(v, self.on):
            for k in range(n): L[i0 + k] = F(0); R[i0 + k] = F(0)
            return
        if r.state == 1:
            g = r.gains(n); vmul_block(L, i0, n, g); vmul_block(R, i0, n, g); return
        c = r.cur
        if near(c, F(1.0)): return
        if abs(float(c)) < float(EPS):
            for k in range(n): L[i0 + k] = F(0); R[i0 + k] = F(0)
            return
        vmul_block(L, i0, n, c); vmul_block(R, i0, n, c)


class Biquad:
    """IirFilter (size 0x50, base ctor 0xe1edc). kind: 'hpf' (vt 0x840c48), 'lpf' (0x840c28), 'bpf' (0x841918), 'off' (0x841938).
    Process 0xe16dc (NEON, L/R in two lanes): v = x + k*yprev; y = b0 v + b1 v1 + b2 v2 - a1 y1 - a2 y2."""
    def __init__(self, kind, fs):
        self.kind = kind; self.fs = fs if fs >= 10 else 10
        self.nyq = F(int(fs / 2)); self.fc = F(F(self.nyq + F(5.0)) * F(0.5)); self.Q = 0.7071067811865476
        self.b0 = self.b1 = self.b2 = self.a1 = self.a2 = self.k = F(0)
        z = lambda: [F(0), F(0)]
        self.v = [z(), z(), z(), z()]; self.y = [z(), z(), z(), z()]; self.yprev = z()   # v1..v4, y1..y4 per lane
        self.flag48 = 0

    def coefs(self):                                    # slot 4: 0xe1bb8 / 0xe1ca0 / 0xe1d88 / no-op
        if self.kind == "off": return
        fc = float(self.fc); Q = self.Q; fs = float(self.fs)
        if self.kind == "bpf":
            if not Q > 0.01: Q = 0.01
            w = math.tan(fc * (math.pi / fs))
            iq = 1.0 / Q
            s = math.sqrt(4.0 + iq * iq)
            f = w * INV_TWO_PI
            lo = (f * 0.5) * (s - iq)
            hi = lo + f * iq
            B = (hi - lo) * TWO_PI
            W = (hi * FOUR_PI2) * lo
            nrm = 1.0 / ((B + 1.0) + W)
            a1 = ((W - 1.0) + (W - 1.0)) * nrm
            a2 = ((1.0 - B) + W) * nrm
            self.b0 = F(B * nrm); self.b1 = F(0); self.a1 = F(a1); self.a2 = F(a2); self.b2 = F(-self.b0)
            return
        w = math.tan(fc * (math.pi / fs))
        f = w * INV_TWO_PI
        wq = ((1.0 / Q) * TWO_PI) * f
        w2 = (f * FOUR_PI2) * f
        nrm = 1.0 / ((wq + 1.0) + w2)
        a1 = ((f * EIGHT_PI2) * f - 2.0) * nrm
        a2 = (w2 + (1.0 - wq)) * nrm
        if self.kind == "hpf":
            self.b0 = F(nrm); self.b2 = self.b0; self.b1 = F(nrm * -2.0)
        else:
            self.b0 = F(w2 * nrm); self.b2 = self.b0; self.b1 = F(self.b0 + self.b0)
        self.a1 = F(a1); self.a2 = F(a2)

    def process(self, L, R, i0, n):                     # slot 2: 0xe16dc, or no-op for IirOff
        if self.kind == "off": return
        b0, b1, b2, a1, a2, k = self.b0, self.b1, self.b2, self.a1, self.a2, self.k
        for ch, buf in ((0, L), (1, R)):
            v1, v2, v3, v4 = (self.v[i][ch] for i in range(4))
            y1, y2, y3, y4 = (self.y[i][ch] for i in range(4))
            yp = self.yprev[ch]
            if self.flag48 and self.Q > 0:              # 0xe1844: re-filter the last 4 inputs with the new coefficients
                y4 = nmul(b0, v4)
                y3 = nsub(nadd(nmul(b0, v3), nmul(b1, v4)), nmul(a1, y4))
                y2 = nsub(nsub(nadd(nadd(nmul(b0, v2), nmul(b1, v3)), nmul(b2, v4)), nmul(a1, y3)), nmul(a2, y4))
                y1 = nsub(nsub(nadd(nadd(nmul(b0, v1), nmul(b1, v2)), nmul(b2, v3)), nmul(a1, y2)), nmul(a2, y3))
            for j in range(n):
                x = buf[i0 + j]
                v = nadd(x, nmul(k, yp))
                o = nmul(b0, v)
                o = nadd(o, nmul(b1, v1)); o = nadd(o, nmul(b2, v2))
                o = nsub(o, nmul(a1, y1)); o = nsub(o, nmul(a2, y2))
                buf[i0 + j] = o
                v4, v3, v2, v1 = v3, v2, v1, v
                y4, y3, y2, y1 = y3, y2, y1, o
                yp = o
            for i, (a, b) in enumerate(((v1, y1), (v2, y2), (v3, y3), (v4, y4))):
                self.v[i][ch] = a; self.y[i][ch] = b
            self.yprev[ch] = yp
        self.flag48 = 0


class FilterContainer:
    """Object at LoFi+0x4a4 (size 0x44, ctor 0xfc5e4)."""
    def __init__(self, fs):
        self.subs = [Biquad("hpf", fs), Biquad("lpf", fs), Biquad("bpf", fs), Biquad("off", fs)]   # FILTERTYPE 0..3
        self.gate = SignalGate(fs, rnd(F(F(F(fs) * F(0.001)) * F(3.0))))
        self.pending = 3; self.cur = 3
        self.cut_t = self.cut_c = F(1000.0); self.cut_mult = G1; self.cut_steps = 0
        self.q_t = self.q_c = F(F(0.7)); self.q_mult = G3; self.q_steps = 0
        self.next = F(0.0); self.maxsteps = 0; self.flag40 = 0; self.dirty41 = 0
        self.min_fc = F(5.0)

    def set_type(self, t):                              # inline in fb20c (same as 0xfbb50)
        if not 0 <= t <= 3: return
        self.pending = t
        if t != self.cur: self.gate.close()

    def configure(self, sub):
        s15 = sub.nyq
        if self.cut_c <= s15: s15 = self.cut_c
        s14 = self.min_fc
        if s14 <= s15: s14 = s15
        sub.Q = float(self.q_c); sub.fc = s14
        sub.coefs()

    def ramp_setup(self):                               # 0xfb994
        if self.dirty41:
            n = rnd(abs(F(F(F(1.0) / log10f(G1)) * log10f(F(self.cut_t / self.cut_c)))))
            self.cut_steps = n + 1
            self.cut_mult = G1 if self.cut_t > self.cut_c else G2
            n2 = rnd(abs(F(F(F(1.0) / log10f(G3)) * log10f(F(self.q_t / self.q_c)))))
            self.q_steps = n2 + 1
            self.q_mult = G3 if self.q_t > self.q_c else G4
            self.next = F(44.1); self.dirty41 = 0
        self.maxsteps = max(self.q_steps, self.cut_steps)
        r = self.gate.r
        if r.state == 1 and near(r.target, self.gate.off): return
        if float(self.cut_steps) > 38.0: self.gate.close()

    def _swap(self):
        self.cur = self.pending; self.cut_c = self.cut_t; self.q_c = self.q_t
        self.cut_steps = self.q_steps = self.maxsteps = 0
        sub = self.subs[self.cur]
        self.configure(sub); sub.flag48 = 1
        return sub

    def process(self, L, R, i0, n):                     # 0xfbb70
        if self.cur != 3: self.ramp_setup()
        r = self.gate.r
        if r.state == 1 and near(r.target, self.gate.off):          # fading out
            rem = r.rem
            if n < rem:
                self.subs[self.cur].process(L, R, i0, n); self.gate.apply(L, R, i0, n); return
            self.subs[self.cur].process(L, R, i0, rem); self.gate.apply(L, R, i0, rem)
            sub = self._swap()
            sub.process(L, R, i0 + rem, n - rem); self.gate.open(); self.gate.apply(L, R, i0 + rem, n - rem); return
        if r.state != 1 and near(r.cur, self.gate.off):              # closed: switch now, then fade in
            sub = self._swap()
            sub.process(L, R, i0, n); self.gate.open(); self.gate.apply(L, R, i0, n); return
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
            sub = self.subs[self.cur]
            sub.process(L, R, pos, chunk); pos += chunk
            if self.flag40:
                self.configure(sub); sub.flag48 = 0; self.flag40 = 0
        self.gate.apply(L, R, i0, n)


class LoFi:
    def __init__(self, fs=FS, block=64):
        self.fs = fs
        self.params = [Param("float", 0.5) for _ in range(6)] + [Param("choice", 0), Param("choice", 2)]
        # +0x498 preamp, +0x49c crusher, +0x4a0 sample-and-hold, +0x4a4 filter container, +0x4a8 position gate
        self.pre_N = rnd(F(F(fs) * F(0.001))); self.pre_t = F(1.0); self.pre_c = F(1.0); self.pre_inc = F(0); self.pre_cnt = 0
        self.bits = 32; self.scale = F(256.0); self.inv = F(F(1.0) / F(256.0))
        self.sh_fs = fs; self.sh_phase = F(1.0); self.sh_step = F(1.0); self.sh_hold = [F(0), F(0)]
        self.filt = FilterContainer(fs)
        self.gate = SignalGate(fs, rnd(F(F(F(fs) * F(0.001)) * F(3.0))))
        self.pos_pending = 1; self.pos_cur = 1
        self.wet = None; self.dry = None                 # EffectBase +0x14 / +0x10 (slot 26)

    # --- parameters --------------------------------------------------------------------------------------------
    def set_param(self, idx, v):                        # EffectBase slot 14 0x105d24 (index 0..7, else returns 3)
        if 0 <= idx < 8: self.params[idx].set(v); return 0
        return 3

    def insert_defaults(self):
        for i in (0, 2, 1, 3, 4, 5, 6, 7): self.set_param(i, INSERT_DEFAULTS[i])

    def apply_params(self):                             # 0xfb20c (order: PREAMP, BITDEPTH, REDUCTION, CUTOFF, RES, TYPE, POS)
        P = self.params
        if P[0].changed():
            v = P[0].get(); e = F(F(v * F(42.0)) * F(0.05))
            t = F(math.pow(10.0, float(e)))
            inv = F(F(1.0) / F(self.pre_N))
            self.pre_t = t; self.pre_cnt = self.pre_N; self.pre_inc = F(F(t - self.pre_c) * inv)
        if P[2].changed():
            v = P[2].get(); self.bits = BITS[rnd(F(v * G0))]
            iv = (1 << self.bits) if self.bits < 31 else (-(1 << 31) if self.bits == 31 else 0)
            self.scale = F(iv); self.inv = F(F(1.0) / self.scale) if iv else float('inf')
        if P[1].changed():
            v = P[1].get(); r = F(math.pow(1000.0000610351562, float(v)) * 44.099998474121094)
            rate = rnd(r)
            self.sh_step = F(1.0) if rate > self.sh_fs else F(F(self.sh_fs) / F(rate))
        if P[3].changed():
            v = P[3].get(); self.filt.cut_t = F(math.pow(1000.0, float(v)) * 20.0); self.filt.dirty41 = 1
        if P[4].changed():
            v = P[4].get(); q = F(F(0.2) + F(v * F(9.8)))
            if not near(self.filt.q_t, q): self.filt.q_t = q; self.filt.dirty41 = 1
        if P[6].changed():
            self.filt.set_type(rnd(P[6].get()))
        if P[7].changed():
            p = rnd(P[7].get()); self.pos_pending = p
            if self.filt.cur == 3: self.pos_cur = p
            else: self.gate.close()

    # --- stages ------------------------------------------------------------------------------------------------
    def preamp(self, L, R, i0, n):                      # 0xfb6e4: clip at +-1/g, then * (1 + 0.2 g) / 1.2
        g = self.pre_c; cnt = self.pre_cnt
        for j in range(i0, i0 + n):
            hi = F(F(1.0) / g); lo = -hi
            s = F(F(F(1.0) + F(g * F(0.2))) * F(0.8333333))
            for buf in (L, R):
                x = buf[j]
                if x < lo: x = lo
                elif x > hi: x = hi
                buf[j] = F(s * x)
            if cnt > 0: cnt -= 1; g = F(g + self.pre_inc)
            else: g = self.pre_t
        self.pre_c = g; self.pre_cnt = cnt

    def crush(self, L, R, i0, n):                       # 0xfaf28: sign * (trunc(2^b * sqrt|x|) / 2^b)^2
        sc = self.scale; inv = float(self.inv)
        for j in range(i0, i0 + n):
            for buf in (L, R):
                x = buf[j]
                sg = F(1.0) if x > 0 else F(-1.0)
                a = F(math.sqrt(F(x * sg)))
                q = F(math.trunc(float(F(sc * a))) * inv)
                buf[j] = F(sg * F(q * q))

    def sample_hold(self, L, R, i0, n):                 # inline in 0xfbf64 (same as 0xfb8e0)
        ph = self.sh_phase; st = self.sh_step; hL, hR = self.sh_hold
        for j in range(i0, i0 + n):
            if ph < F(1.0):
                ph = F(ph + st); hL = L[j]; hR = R[j]
            else:
                L[j] = hL; R[j] = hR
            ph = F(ph - F(1.0))
        self.sh_phase = ph; self.sh_hold = [hL, hR]

    def chain(self, L, R, i0, n):                       # 0xfbf64
        self.gate.apply(L, R, i0, n)
        if self.pos_cur == 0:
            self.filt.process(L, R, i0, n); self.preamp(L, R, i0, n)
            if self.bits < 32: self.crush(L, R, i0, n)
            self.sample_hold(L, R, i0, n)
        else:
            self.preamp(L, R, i0, n)
            if self.bits < 32: self.crush(L, R, i0, n)
            self.sample_hold(L, R, i0, n); self.filt.process(L, R, i0, n)

    def process(self, L, R):                            # slot 25 0xfc0f4; returns new lists
        L = [F(x) for x in L]; R = [F(x) for x in R]; n = len(L)
        self.apply_params()
        r = self.gate.r
        done = False
        if r.state == 1:
            if near(r.target, self.gate.off) and r.rem <= n:
                rem = r.rem
                self.chain(L, R, 0, rem); self.pos_cur = self.pos_pending; self.gate.open()
                self.chain(L, R, rem, n - rem); done = True
        elif near(r.cur, self.gate.off):
            self.pos_cur = self.pos_pending; self.gate.open()
        if not done: self.chain(L, R, 0, n)
        if self.params[5].changed():                    # slot 26 0xfaef4
            v = self.params[5].get(); self.wet = v; self.dry = F(F(1.0) - v)
        return [float(x) for x in L], [float(x) for x in R]
