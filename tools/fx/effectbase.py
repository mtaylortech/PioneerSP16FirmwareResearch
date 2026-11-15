# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python model of the TORAIZ SP-16 1.60 EffectBase wrapper: slot 18 0x106de4 (dispatcher) with its EffectInOutGain gate,
the post-stage 0x106c88 (SignalGate -> IirHpf1stOrder -> SignalGate), the dry/wet mix 0x10770c, the 147-sample skip/clamp
(+0xa8..+0xb8) and the lifecycle slots 5/6/7/8/9/22/31, with an injectable slot 25 (process), slot 26 (updateMix) and slot 27 (reset).

Own re-implementation written from the analysis in docs/effects/effectbase.md; it contains no firmware bytes. Arithmetic mirrors the
1.60 code: float32 for VFP single steps, double for the HPF coefficient step, flush-to-zero (NEON) for groups of 4 in the vector
helpers and for the whole HPF, plain float32 (VFP) for the n % 4 tail. Shared blocks come from lofi.py (SignalGate,
vmul_block, near/ftz/nmul/nadd/nsub), which were validated bit-exactly with LoFi (F030).

Signal flow of slot18(L, R, n) (caller buffers, in place; returns the slot-25 value or 0):
  1  gate copy flag (+0xd0, always 1 unless slot 21(0)): apply the pending gate target (0x107374); if not running (0x1079d0) return 0.
  2  if +0xa8: skip (armed by slot 5): the first `skip` samples are left untouched (dry) and the gate does NOT advance;
                clamp (armed by slot 6): only the first `clamp` samples are processed, the rest of the block is left dry.
  3  copy L/R into the EffectBase copy buffers; input fade (0x1074c4: copy *= gate.in); r = slot25(copy, n')
  4  r == 0: post-stage on the copy; gate.dry/wet := e+0x10/+0x14; mix 0x10770c: L = L*gate.dry + copy*gate.wet.
Gains are SmoothFloat ramps (0xf55a4): linear, N = trunc(f32(f32(3.3333333*0.001)*fs)) = 147 @44.1 k / 160 @48 k, value_t =
f32(value_{t-1} + step), step = f32(f32(target - current) * f32(1/N)); the first ramp sample is the start value.

Usage:
  eb = EffectBase(fs=44100, mode=0, slot25=fn, slot26=fn, slot27=fn)    # fn(eb, ...) ; slot25(eb, L, R, n) -> int, in place
  eb.slot22(0); eb.set_post_hpf(True, 10.0)                            # Insert-processor ctor steps (F141)
  per block (InsertFxProcessor processBlock): if eb.slot9() == 0: eb.slot5(0.0, 1); eb.slot7()  ;  eb.slot18(L, R, 64)
"""
import math
import crmath as CR                                    # glibc-exact double tan (H029)
from lofi import F, EPS, near, ftz, nmul, nadd, nsub, vmul_block, SignalGate

K_FADE_MS = F(3.3333333)          # 0x8420a8 / gate +0xcc / literal 0x40555555
K_MILLI = F(0.001)
D_PI = math.pi                    # 0xe1b18
D_INV_2PI = 0.15915494309189535   # 0xe1b20
D_2PI = 2.0 * math.pi             # 0xe1b28


def fade_samples(fs, ms=K_FADE_MS):
    return int(F(F(ms * K_MILLI) * F(float(fs))))          # vcvt.s32.f32 truncates


def vadd_block(dst, i0, src, n):
    """0x578a6c: dst[i0+k] += src[k]; NEON (flush-to-zero) for groups of 4, VFP for the n % 4 tail."""
    q = n - n % 4
    for k in range(n):
        dst[i0 + k] = nadd(dst[i0 + k], src[k]) if k < q else F(dst[i0 + k] + src[k])


class SmoothFloat:
    """SmoothFloat (0x24 bytes: fs, state, cur, target, step, remaining, ms, N, 1/N)."""
    def __init__(self, fs):
        self.fs = fs; self.state = 0; self.cur = F(0.0); self.target = F(0.0); self.step = F(0.0); self.rem = 0
        n = int(F(F(float(fs)) * F(0.0033333332)))            # ctor 0xf54b8
        self.N = max(n, 1); self.inv = F(1.0 / F(float(self.N)))

    def set_time(self, ms):                                  # 0xf5a00 setSmoothingTime -> setSmoothingSamples
        ms = F(ms)
        if not ms > 0: return
        n = int(F(F(ms * K_MILLI) * F(float(self.fs))))
        if n < 1: return
        if self.state == 0:
            self.N = n; self.inv = F(1.0 / F(float(n))); return
        if self.state == 1:                                  # a running ramp restarts from the current value with the new length
            old = self.target; self.target = self.cur; self.state = 0
            self.N = n; self.inv = F(1.0 / F(float(n)))
            if not near(old, self.cur):
                self.target = old; self.state = 1; self.rem = self.N
                self.step = F(F(old - self.cur) * self.inv)

    def snap(self, v):                                       # 0xf5584
        v = F(v); self.state = 0; self.cur = v; self.target = v; self.step = F(0.0); self.rem = 0

    def set_target(self, v):                                 # 0xf5668
        v = F(v)
        if near(v, self.target): return
        self.target = v; self.state = 1; self.rem = self.N
        self.step = F(F(v - self.cur) * self.inv)

    def block(self, n):                                      # 0xf55a4 -> per-sample gains
        g = []; c = self.cur; rem = self.rem
        if n < 1: return g
        if self.state != 0:
            if n < rem:
                for _ in range(n): g.append(c); c = F(c + self.step)
                self.cur = c; self.rem = rem - n; return g
            for _ in range(max(rem, 0)): g.append(c); c = F(c + self.step)
            self.state = 0; c = self.target; rem = 0
        g += [c] * (n - len(g))
        self.cur = c; self.rem = rem
        return g

    def apply(self, L, R, i0, n, buf_scratch=None):
        """The common 'multiply both channels by this gain' pattern of 0x1074c4 / 0x10770c."""
        if self.state == 0:
            v = self.cur
            if near(v, F(1.0)): return
            if abs(v) < EPS:                                 # memset 0 (+0.0)
                for k in range(n): L[i0 + k] = 0.0; R[i0 + k] = 0.0
                return
            vmul_block(L, i0, n, v); vmul_block(R, i0, n, v); return
        g = self.block(n)
        vmul_block(L, i0, n, g); vmul_block(R, i0, n, g)


class InOutGain:
    """EffectInOutGain (new 0xd4, ctor 0x10711c, vt 0x842078): three SmoothFloats (input +0x48, dry +0x6c, wet +0x90) and a
    3-state machine (0 off, 1 running, 2 running-variant) with a pending target."""
    def __init__(self, fs, mode1=False):
        self.sin, self.sdry, self.swet = SmoothFloat(fs), SmoothFloat(fs), SmoothFloat(fs)
        for s in (self.sin, self.sdry, self.swet): s.set_time(K_FADE_MS)
        self.cur = 0; self.trans = 0; self.tgt = 0          # +0x1c, +0x20, +0x24
        self.pend = 0; self.pstate = 0                       # +0x28, +0x2c
        self.prec = [0, F(0.0), 1, F(1.0), 1, F(0.0)]        # +0x30..+0x44 as (in-mode, in, dry-mode, dry, wet-mode, wet)
        self.c0 = F(1.0); self.c4 = F(0.0)                   # +0xc0 / +0xc4 dry / wet copied from e+0x10/+0x14 every block
        self.c8 = 1 if mode1 else 0                          # +0xc8: set by the EffectBase ctor for mode 1
        self.time = K_FADE_MS                                # +0xcc
        self.copy = 1                                        # +0xd0 (slot 21)

    def sfs(self): return (self.sin, self.sdry, self.swet)

    def start(self, state, rec):                             # 0x107310(gate, state, record)
        if not self.copy:
            self.cur = state; self.trans = 0; self.tgt = state; return
        self.pstate = state; self.pend = 1; self.prec = list(rec)

    def reset(self, rec):                                    # 0x1072bc(gate, record)
        self.cur = 0; self.trans = 0; self.tgt = 0
        if self.copy:
            self.sin.snap(rec[1]); self.sdry.snap(rec[3]); self.swet.snap(rec[5])

    def apply_pending(self):                                 # 0x107374
        if not (self.copy and self.pend): return
        new, old = self.pstate, self.tgt; self.pend = 0
        if new == old: return
        if self.trans:
            self.cur = old
            for s in self.sfs(): s.snap(s.cur)
        self.trans = 1; self.tgt = new
        for s in self.sfs(): s.set_time(K_FADE_MS)
        for s, md, g in zip(self.sfs(), self.prec[0::2], self.prec[1::2]):
            if md == 0: s.snap(g)
            elif md == 1: s.set_target(g)

    def running(self):                                       # 0x1079d0 (slot 9)
        c, t = self.cur, self.tgt
        if c != t:
            if c == 0: return t
            if t != 0:
                if c == 2: return 1 if t == 1 else 0
                if c != 1: return 0
                return 1 if t == 2 else 0
        return c

    def input_fade(self, cL, cR, n):                         # 0x1074c4
        if self.copy: self.sin.apply(cL, cR, 0, n)

    def mix(self, L, R, i0, cL, cR, n):                      # 0x10770c
        if not self.copy: return
        if not self.trans:
            if self.cur == 1:
                self.sdry.set_target(self.c0); self.swet.set_target(self.c4)
            if self.cur == 2 and self.c8:
                self.swet.set_target(self.c4)
        self.sdry.apply(L, R, i0, n)
        self.swet.apply(cL, cR, 0, n)
        vadd_block(L, i0, cL, n); vadd_block(R, i0, cR, n)
        if self.trans and self.sin.state == 0 and self.sdry.state == 0 and self.swet.state == 0:
            self.cur = self.tgt; self.trans = 0
            for s in self.sfs(): s.set_time(self.time)


class IirHpf1stOrder:
    """IirHpf1stOrder (vt 0x840db8) at EffectBase +0xd8: one pole, NEON (two lanes L/R, flush-to-zero).
    coefs 0xe1aa0: w = tan(fc*pi/fs) (double) -> b0 = 1/(w+1), b1 = -b0, a1 = (w-1)/(w+1); process 0xe1490:
    v = x + k*y[-1] (k = 0); y = b0*v + b1*v[-1] - a1*y[-1]."""
    def __init__(self, fs):
        self.fs = fs; self.fmax = F(float(fs >> 1))
        fc0 = F(F(F(22050.0) + F(5.0)) * F(0.5))              # IirFilter ctor default (44.1 kHz based) = 11027.5
        self.fc = fc0 if fc0 <= self.fmax else self.fmax      # EffectBase ctor: min(fc, fs/2) (unused: slot 5 sets fc)
        self.k = F(0.0); self.b0 = self.b1 = self.a1 = F(0.0)
        self.zero(); self.coefs()

    def zero(self):
        self.v1 = [0.0, 0.0]; self.y1 = [0.0, 0.0]; self.yp = [0.0, 0.0]

    def coefs(self):
        w = CR.tan(float(self.fc) * (D_PI / float(self.fs)))
        w = (w * D_INV_2PI) * D_2PI
        nrm = 1.0 / (w + 1.0)
        a1 = (w - 1.0) * nrm
        self.b0 = F(nrm); self.b1 = F(-nrm); self.a1 = F(a1)

    def process(self, L, R, n):
        b0, b1, a1, k = self.b0, self.b1, self.a1, self.k
        for ch, buf in ((0, L), (1, R)):
            v1, y1, yp = self.v1[ch], self.y1[ch], self.yp[ch]
            for j in range(n):
                v = nadd(buf[j], nmul(k, yp))
                o = nsub(nadd(nmul(b0, v), nmul(b1, v1)), nmul(a1, y1))
                buf[j] = o; v1 = v; y1 = o; yp = o
            self.v1[ch], self.y1[ch], self.yp[ch] = v1, y1, yp


def _records(mode, dry, wet, old):
    """slot 31 0x105d78: gate target records R0 (reset), R1 (slot 5, state 2), R2 (slot 6, state 0), R3 (slot 7, state 1),
    R4 (slot 8, state 2); each (in-mode, in, dry-mode, dry, wet-mode, wet), mode 0 = snap, 1 = 147-sample ramp.
    Modes other than 0/1/2 leave the records unchanged (ctor values)."""
    one, zero = F(1.0), F(0.0)
    if mode in (0, 2):
        r1_in_mode = 1 if mode == 0 else 0
        return [[None, one, None, one, None, zero],
                [r1_in_mode, one, 0, one, 0, zero],
                [0, one, 1, one, 1, zero],
                [0, one, 1, dry, 1, wet],
                [0, one, 1, one, 1, zero]]
    if mode == 1:
        return [[None, zero, None, one, None, zero],
                [0, zero, 0, one, 1, wet],
                [1, zero, 1, one, 1, zero],
                [1, one, 1, dry, 1, wet],
                [1, zero, 1, one, 0, wet]]
    return [list(r) for r in old]


class EffectBase:
    """EffectBase (sizeof 0x1b8) wrapper state with injectable slots 25/26/27 (and optional 28/29/30 hooks, all base no-ops)."""
    def __init__(self, fs=44100, block=64, mode=0, slot25=None, slot26=None, slot27=None):
        self.fs = fs; self.block = block; self.mode = mode
        self.dry = F(1.0); self.wet = F(0.0)                 # +0x10 / +0x14
        self.skip_en = 1                                     # +0xa8 (ctor 1; processors call slot 22(e, 0) except Insert FX 7)
        self.skip_armed = 0; self.skip = 0                   # +0xac / +0xb0
        self.clamp_armed = 0; self.clamp = 0                 # +0xb4 / +0xb8
        self.gate = InOutGain(fs, mode1=(mode == 1))         # +0xc8
        self.hpf_req = 0; self.hpf_cur = 0; self.hpf_fc = F(10.0)   # +0xcc / +0xcd / +0xd0
        self.hpf = IirHpf1stOrder(fs)                        # +0xd8
        n = fade_samples(fs)
        self.gA = SignalGate(fs, n); self.gB = SignalGate(fs, n)    # +0x128 / +0x170 (start closed)
        ctor_recs = _records(0, F(1.0), F(0.0), None)        # the ctor writes the mode-0 pattern with dry 1 / wet 0
        ctor_recs[0][0] = ctor_recs[0][2] = ctor_recs[0][4] = 1
        self.recs = ctor_recs
        self._s25 = slot25 or (lambda eb, L, R, n: 0)
        self._s26 = slot26 or (lambda eb: None)
        self._s27 = slot27 or (lambda eb: 0)

    # ---------------------------------------------------------------------------------------------------------- host setup
    def slot22(self, on): self.skip_en = 1 if on else 0                    # 0x1059b0
    def slot21(self, on): self.gate.copy = 1 if on else 0                  # 0x1059a8
    def set_post_hpf(self, on, fc=10.0):                                   # 0x106c7c(e, on, fc)
        self.hpf_req = 1 if on else 0; self.hpf_fc = F(fc)

    def _fc(self):
        s15 = self.hpf_fc if self.hpf_fc <= self.hpf.fmax else self.hpf.fmax
        return s15 if F(5.0) <= s15 else F(5.0)

    def slot31(self): self.recs = _records(self.mode, self.dry, self.wet, self.recs)

    # ---------------------------------------------------------------------------------------------------------- lifecycle
    def slot5(self, a=0.0, honour_skip=1):                                 # 0x10623c start
        if honour_skip and self.skip_en:
            self.clamp_armed = 0; self.skip_armed = 1; self.clamp = 0
            self.skip = fade_samples(self.fs)
        self.hpf_cur = self.hpf_req
        self.hpf.zero(); self.hpf.fc = self._fc(); self.hpf.coefs()
        for g in (self.gA, self.gB): g.r.set_now(g.on if self.hpf_cur else g.off)   # 0xf50c8 / 0xf50b8
        self._s27(self); self._s26(self); self.slot31()
        self.recs[1][3] = F(a)
        self.gate.reset(self.recs[0]); self.gate.start(2, self.recs[1])
        return 0

    def slot6(self, a=1.0):                                                # 0x105c94 stop
        if self.skip_en:
            self.skip_armed = 0; self.clamp_armed = 1; self.skip = 0
            self.clamp = fade_samples(self.fs)
        self.slot31(); self.recs[2][3] = F(a)
        self.gate.start(0, self.recs[2])

    def slot7(self, *_):                                                   # 0x105c58 start variant (processor +0x9d != 0)
        self.slot31(); self.gate.start(1, self.recs[3]); return 0

    def slot8(self, *_):                                                   # 0x105c20 start variant (processor +0x9d == 0)
        self.slot31(); self.gate.start(2, self.recs[4])

    def slot9(self): return self.gate.running()                            # 0x1059bc -> 0x1079d0

    # ---------------------------------------------------------------------------------------------------------- post-stage
    def post(self, cL, cR, n):                                             # 0x106c88
        if self.hpf_cur != self.hpf_req:
            self.hpf_cur = self.hpf_req
            if not self.hpf_cur:
                self.gA.close(); self.gB.close()
            else:
                self.hpf.fc = self._fc(); self.hpf.coefs()
                self.gA.open(); self.gB.open()
        if not self.hpf_cur:
            a, b = self.gA, self.gB
            if a.r.state != 1 and near(a.r.cur, a.off) and b.r.state != 1 and near(b.r.cur, b.off):
                return
        self.gA.apply(cL, cR, 0, n); self.hpf.process(cL, cR, n); self.gB.apply(cL, cR, 0, n)

    # ---------------------------------------------------------------------------------------------------------- slot 18
    def slot18(self, L, R, n):                                             # 0x106de4
        g = self.gate
        if g.copy:
            g.apply_pending()
            if not g.running(): return 0
        i0 = 0
        if self.skip_en:
            if self.skip_armed:
                c = self.skip
                if n < c:
                    self.skip = c - n; return 0
                n -= c; i0 = c; self.skip_armed = 0; self.skip = 0
            if self.clamp_armed:
                c = self.clamp
                if n < c: self.clamp = c - n
                else: self.clamp = 0; self.clamp_armed = 0; n = c
        if not g.copy:
            sL = L[i0:i0 + n]; sR = R[i0:i0 + n]
            r = self._s25(self, sL, sR, n)
            L[i0:i0 + n] = sL; R[i0:i0 + n] = sR
            return r
        cL = [F(x) for x in L[i0:i0 + n]]; cR = [F(x) for x in R[i0:i0 + n]]
        g.input_fade(cL, cR, n)
        r = self._s25(self, cL, cR, n)
        if r == 0:
            self.post(cL, cR, n)
            g.c0 = self.dry; g.c4 = self.wet
            g.mix(L, R, i0, cL, cR, n)
        return r


class InsertProcessor:
    """InsertFxProcessor setFxType 0x11735c / processBlock 0x116860 as seen by its effects (enabled state, +0x9e = 0): the effect
    array, current +0xa4 / pending +0xa8 indices, slot 9 -> swap -> slot 5(e, 0, 1) + slot 7 (+0x9d != 0) or slot 8, then slot 18.
    `feed(idx, eb)` is called before slot 18 for the per-index parameter feed (tempo etc., F143 item 3)."""
    def __init__(self, effects, nine_d=1, feed=None):
        self.fx = dict(effects); self.cur = -1; self.pend = -1; self.nine_d = nine_d; self.feed = feed

    def set_fx_type(self, idx):
        if self.pend == idx: return
        if self.cur == -1:
            self.cur = self.pend = idx; return
        e = self.fx.get(self.cur)
        if e is not None: e.slot6(1.0)
        self.pend = idx if idx >= 0 else -1

    def process_block(self, L, R, n=64):
        if self.cur >= 0:
            e = self.fx.get(self.cur)
            if e is not None and e.slot9() == 0:
                self.cur = self.pend
                ne = self.fx.get(self.cur)
                if self.cur >= 0 and ne is not None:
                    ne.slot5(0.0, 1)
                    if self.nine_d: ne.slot7(0)
                    else: ne.slot8()
        e = self.fx.get(self.cur)
        if e is not None:
            if self.feed: self.feed(self.cur, e)
            e.slot18(L, R, n)
