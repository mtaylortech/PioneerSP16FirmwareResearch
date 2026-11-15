# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Pure-Python models of the TORAIZ SP-16 1.60 MasterFxProcessor and SendFxProcessor hosts (setFxType, processBlock, the
FxProcessorBase disable switch 0x112a08) and of the MuteSmoother used by the Send processor's input mute.

Own re-implementation written from the analysis in docs/effects/fx-processors.md; it contains no firmware bytes. The effects are
effectbase.EffectBase objects (effectbase.py) wrapping the per-effect slot-25 models.

Field map (processor object; FxProcessorBase fields per F016/F019):
  +0x80 array, +0x88 count, +0x8c effect pointer of `current` (written at the swap and by setFxType from Off), +0x90 pointer of
  `pending`, +0x94 tempo provider (vt+0x1c -> double BPM), +0x9c bypass byte (Insert only), +0x9d start-variant byte (ctor 1),
  +0x9e disable byte (ctor 1; FX-mode routing writes it through 0x112a08), +0xa0 current index, +0xa4 pending index,
  Send only: +0xa8 MuteSmoother* (created by prepareToPlay 0x119bd8, length roundToInt(f32(f32(fs)*0.001f)*3) = 132 @44.1 k).

processBlock (64 frames, in place on the bus channels):
  Master 0x112acc: if current >= 0: slot 9 of current; if 0: current := pending, +0x8c := array[pending]; if pending >= 0 and
           +0x9e == 0: slot 5(e, 0.0, 1) then slot 7(e, 0) if +0x9d else slot 8(e).  Then if 0 <= current < count: per-index feed
           (indices 0, 2, 3, 9: slot 14(e, 7, clamp(f32(tempo), 1, 999))) and slot 18(e, L, R, 64). No input/output stage of its own.
  Send 0x119994: MuteSmoother.setMuted(pending == -1 or +0x9e != 0 ? 1 : +0x9d ^ 1); MuteSmoother.process(L, R) in place; then as
           Master, except (a) slot 9 / swap only when current >= 0 AND +0x9e == 0, (b) slot 5 third argument 0.
setFxType (Master 0x1132e4 = Send 0x11a254): if n == pending: return; if current == -1: current = pending = n (verbatim),
           +0x8c = +0x90 = array[n] (0 if n >= count); else old slot 6(1.0f), pending = n (-1 if n < 0), +0x90 = array[n] or 0.
0x112a08(proc, flag): if +0x9e == flag: return; +0x9e = flag; if flag and +0x8c: +0x8c->slot6(1.0f). Re-enable calls nothing.
0x1129bc(proc, v) (F176-F178, H079; `set_start_mode`): if +0x90 == 0: return; +0x9d = v; if +0x9e: return; +0x90->slot7(0) if v
           else +0x90->slot8(). Reader 0x11cae0 = byte +0x9d (`get_start_mode`).
"""
from lofi import F

TEMPO_MIN, TEMPO_MAX = F(1.0), F(999.0)
FEED_INDICES = (0, 2, 3, 9)          # Master/Send processBlock jump table: SendFxDelay, Chorus, Flanger, Phaser


def clamp_tempo(bpm):
    f = F(bpm)                       # vcvt.f32.f64
    if f < TEMPO_MIN: return TEMPO_MIN
    if f > TEMPO_MAX: return TEMPO_MAX
    return f


def mute_samples(fs):
    """prepareToPlay 0x119bd8: juce::roundToInt(f32(f32(fs) * 0.001f) * 3.0f) (magic-number rounding = round half to even)."""
    x = float(F(F(F(float(fs)) * F(0.001)) * F(3.0)))
    return int(round(x))


class MuteSmoother:
    """MuteSmoother (0x20 bytes, vt 0x83d2b0): ctor 0xe7fd8(n, muted), setMuted 0xe8050, process 0xe808c(inL, inR, outL, outR, n).
    Fields: +4 muted, +8 N, +0xc 1/N, +0x10 remaining, +0x14 step, +0x18 gain, +0x1c state (0 idle open, 1 ramp, 2 closed)."""
    def __init__(self, n, muted=0):
        if n < 1:
            self.N = 1; self.inv = F(1.0)
        else:
            self.N = n; self.inv = F(1.0 / float(F(float(n))))
        self.muted = 1 if muted else 0; self.rem = 0
        if not muted:
            self.state = 0; self.g = F(1.0); self.step = F(-self.inv)
        else:
            self.state = 2; self.g = F(0.0); self.step = self.inv

    def set_muted(self, m):
        m = 1 if m else 0
        if self.muted == m: return
        st = F(-self.inv) if m else self.inv
        self.muted = m; self.rem = self.N - self.rem; self.state = 1; self.step = st

    def process(self, L, R, n):                       # in place (the processors pass in == out)
        if self.state == 0: return
        i = 0
        while True:
            if n == 0: return
            if self.state != 1:
                if self.state == 2:
                    for k in range(n): L[i + k] = 0.0; R[i + k] = 0.0
                return
            rem, g, st = self.rem, self.g, self.step
            if n <= rem:
                for k in range(n):
                    L[i + k] = F(L[i + k] * g); R[i + k] = F(R[i + k] * g); g = F(g + st)
                self.g = g; self.rem = rem - n; return
            if rem > 0:
                for k in range(rem):
                    L[i + k] = F(L[i + k] * g); R[i + k] = F(R[i + k] * g); g = F(g + st)
                i += rem
            if not self.muted: break
            n -= rem; self.state = 2; self.rem = 0; self.g = F(0.0)
        self.state = 0; self.rem = 0; self.g = F(1.0)


    def crossfade(self, L, R, dL, dR, n):
        """0xe8228(ms, L, R, dryL, dryR, n) (Insert bypass, +0x9c): idle -> nothing (processed); ramp -> L = f32(f32(dry*(1-g)) +
        f32(g*L)) with g the smoother gain (1 = processed, 0 = dry); closed -> L := dry copy (0x578724 = memcpy)."""
        if self.state == 0: return
        i = 0
        while True:
            if n == 0: return
            if self.state != 1:
                if self.state == 2:
                    L[i:i + n] = dL[i:i + n]; R[i:i + n] = dR[i:i + n]
                return
            rem, g, st = self.rem, self.g, self.step
            m = n if n <= rem else max(rem, 0)
            for k in range(i, i + m):
                a = F(1.0 - g)
                L[k] = F(F(dL[k] * a) + F(g * L[k])); R[k] = F(F(a * dR[k]) + F(g * R[k])); g = F(g + st)
            if n <= rem:
                self.g = g; self.rem = rem - n; return
            i += m
            if not self.muted: break
            n -= rem; self.state = 2; self.rem = 0; self.g = F(0.0)
        self.state = 0; self.rem = 0; self.g = F(1.0)


class _FxProcessor:
    """Common part of Master/Send: effect table, current/pending, +0x8c/+0x90, flags +0x9d/+0x9e, setFxType, disable."""
    SLOT5_HONOUR_SKIP = 1
    FEED = FEED_INDICES

    def __init__(self, effects, count=10, nine_d=1, nine_e=0, tempo=None, feed=None):
        self.fx = dict(effects); self.count = count
        self.cur = -1; self.pend = -1; self.p8c = None; self.p90 = None
        self.nine_d = nine_d; self.nine_e = nine_e
        self.tempo = tempo or (lambda: 120.0)          # +0x94 vt+0x1c (double)
        self.feed = feed                               # feed(idx, eb, bpm): slot 14(e, 7, bpm) on the per-effect model
        self.log = []                                  # (event, index) for slots 5/6/7/8 and the feed

    def _get(self, i):
        return self.fx.get(i) if 0 <= i < self.count else None

    def set_fx_type(self, n):                          # 0x1132e4 / 0x11a254
        if self.pend == n: return
        if self.cur == -1:
            self.cur = self.pend = n; self.p8c = self._get(n); self.p90 = self._get(n); return
        old = self._get(self.cur)
        old.slot6(1.0); self.log.append(("slot6", self.cur))
        if n < 0:
            self.pend = -1; self.p90 = None; return
        self.pend = n; self.p90 = self._get(n)

    def set_disabled(self, flag):                      # FxProcessorBase 0x112a08
        flag = 1 if flag else 0
        if self.nine_e == flag: return
        self.nine_e = flag
        if self.p8c is None or not flag: return
        self.p8c.slot6(1.0); self.log.append(("slot6", self.cur))

    def set_start_mode(self, v):                       # FxProcessorBase 0x1129bc (manager s46 thunk 0x11caf4, IEffector +0x60 0x11caec)
        """Cycle 034 (H079). No pending effect pointer (+0x90 == 0, i.e. pending Off or index >= count): return, nothing stored.
        Else +0x9d := v & 0xff; if the processor is disabled (+0x9e != 0) nothing else; otherwise call the +0x90 effect directly:
        slot 7(e, 0) if v != 0 (full 32-bit test) else slot 8(e). No old-value check (re-sending the same value calls it again)."""
        e = self.p90
        if e is None: return
        self.nine_d = v & 0xff
        if self.nine_e: return
        i = next((k for k, x in self.fx.items() if x is e), None)
        if v & 0xffffffff: e.slot7(0); self.log.append(("slot7", i))
        else: e.slot8(); self.log.append(("slot8", i))

    def get_start_mode(self):                          # reader 0x11cae0 (manager s47; IEffector +0x64 0x11cad8): byte +0x9d
        return self.nine_d

    def _swap(self):
        p = self.pend
        self.cur = p; self.p8c = self._get(p)
        if p >= 0 and not self.nine_e:
            ne = self._get(p)
            ne.slot5(0.0, self.SLOT5_HONOUR_SKIP); self.log.append(("slot5", p))
            if self.nine_d: ne.slot7(0); self.log.append(("slot7", p))
            else: ne.slot8(); self.log.append(("slot8", p))

    def _run(self, L, R, n):
        c = self.cur
        e = self._get(c)
        if e is None: return
        if c in self.FEED:
            bpm = clamp_tempo(self.tempo())
            if self.feed: self.feed(c, e, bpm)
            self.log.append(("feed7", c, bpm))
        e.slot18(L, R, n)


class MasterProcessor(_FxProcessor):
    """MasterFxProcessor::processBlock 0x112acc. No input mute, no bypass stage, no output stage: a disabled processor (or an
    Off one) leaves the main bus untouched once the effect's slot-6 fade-out has ended."""
    SLOT5_HONOUR_SKIP = 1

    def process_block(self, L, R, n=64):
        if self.cur >= 0:
            if self._get(self.cur).slot9() == 0: self._swap()
        self._run(L, R, n)


class SendProcessor(_FxProcessor):
    """SendFxProcessor::processBlock 0x119994: input MuteSmoother (+0xa8) keyed by pending == -1 / +0x9e / !+0x9d, then the
    effect; while disabled the current effect is not polled (no slot 9, no swap)."""
    SLOT5_HONOUR_SKIP = 0

    def __init__(self, effects, fs=44100, mute_n=None, **kw):
        super().__init__(effects, **kw)
        self.ms = MuteSmoother(mute_samples(fs) if mute_n is None else mute_n, 0)

    def mute_flag(self):
        if self.pend == -1 or self.nine_e: return 1
        return self.nine_d ^ 1

    def process_block(self, L, R, n=64):
        self.ms.set_muted(self.mute_flag())
        self.ms.process(L, R, n)
        if self.cur >= 0 and not self.nine_e:
            if self._get(self.cur).slot9() == 0: self._swap()
        self._run(L, R, n)


class InsertProcessorFull(_FxProcessor):
    """InsertFxProcessor::processBlock 0x116860 with its bypass stage: copy the input to the dry buffers (+0xb8), MuteSmoother
    (+0x144, N 132 @44.1 k after prepareToPlay) setMuted(+0x9c bypass, setter 0x1129b4), the Master-like poll/swap (+0x9e,
    slot 5(e, 0, 1)), per-index feed (indices 0, 4, 1, 8: slot 14(e, 7, tempo); index 9 Ducker has its own feed, not modelled
    here), slot 18, then the crossfade 0xe8228 processed <-> dry. setFxType 0x11735c behaves as Master's (offsets +0xa4/+0xa8)."""
    SLOT5_HONOUR_SKIP = 1
    FEED = (0, 1, 4, 8)

    def __init__(self, effects, fs=44100, bypass_n=None, **kw):
        super().__init__(effects, **kw)
        self.bypass = 0
        self.ms = MuteSmoother(mute_samples(fs) if bypass_n is None else bypass_n, 0)

    def set_bypass(self, f): self.bypass = f & 0xff               # 0x1129b4: strb r1, [r0, #0x9c]

    def process_block(self, L, R, n=64):
        dL = list(L); dR = list(R)
        self.ms.set_muted(self.bypass)
        if self.cur >= 0:
            if self._get(self.cur).slot9() == 0: self._swap()
        if self.cur == 9 and self._get(9) is not None: raise NotImplementedError("Insert Ducker feed (case 9) not modelled")
        self._run(L, R, n)
        self.ms.crossfade(L, R, dL, dR, n)
