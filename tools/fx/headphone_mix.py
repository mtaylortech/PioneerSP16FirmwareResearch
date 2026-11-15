# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Clean re-implementation of the SP-16 1.60 headphone cue mix (HeadphoneUnit + HeadphoneRouter) and the main-output selector
(Output12Router). F209-F213, H057; docs/effects/signal-flow.md. Own code, no firmware bytes.

HeadphoneUnit::processBlock 0x1b10ec (14-in / 2-out graph node; buffer = 14 channels, 64 frames):
  1. HeadphoneRouter (+0x80) processBlock 0x1af3d8: its OutputSelector (+0xa0; ctor 0xe6ee4(7 pairs, async 1, monoDup 1, 128))
     writes the selected input pair over channels 0/1 of the same buffer (copy x GainSmoother gain). A mono selection
     (one index = -1) writes one channel and copies it to the other (monoDup).
  2. the three monitor ("cue") pairs of the 6-channel buffer rendered by BufferedAudioProcessor(0) (+0x90; sys+0x5f0, reading the
     shared buffer sys+0x6b4 written by RecMonitorUnit) each pass a 44-sample MuteSmoother (+0x130/+0x134/+0x138) and are added
     to ch0/1 with gain 1.0 (AudioBuffer::addFrom 0x578dc8). Gate k is open (unmuted) when the router's "CueMaster" flag
     (+0x140) is 0; otherwise muted = IMonitorMixer (+0x94 = RecMonitorUnit+0x80) slot 4(k, 0).
  3. MuteCrossfadeSmoother (+0x1d4; length (int)(sr * 0.001) = 44 @ 44.1 kHz) crossfade 0xe8228: muted = IMonitorMixer slot 8
     (RecMonitorUnit byte +0x420) -> ch0/1 := ch11/ch12 (graph: audio input (0,1); ch11 also carries MTU ch13), linear 44 samples.
  4. VolumeKnob (+0x8c): table[i] * 0.5 (F096 table), 100-sample ramp from the parameter's sample offset (persists, F110).
Output: ch0/1.

HeadphoneRouter::setHeadphoneSource 0x1afbac(index): index = position of the identifier in the enum table 0xf62138
(paramId 0x0d000001): 0 CueMaster, 1 Cue12, 2 Cue34, 3 Cue56, 4 Cue78, 5..12 Cue1..Cue8. The selected pair depends on the router
byte +0x98, which every writer sets to 1 (ctor 0x1b0918, ctor 0x1b0af4, DSF callback 0x1af61c); SOURCE_PAIRS gives both.

Output12Router::processBlock 0x1b2610 (4 in / 2 out): OutputSelector (+0x8c; ctor 0xe6ee4(2 pairs, async 1, monoDup 1, 128)),
selection 0x1b28f8(value, force): 0 "Master" -> (0,1) (master out), 1 "4Assign" -> (2,3) (MTU out 6/7); other values: no change.

Arithmetic: float32, round to nearest; NEON vector helpers flush denormals (track_mix.neon_add / vec_mul).
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import track_mix as TM                      # noqa: E402  Smoother (GainSmoother), knob_gain, neon_add, F
import fx_processors as FP                  # noqa: E402  MuteSmoother with process / crossfade (0xe7fd8 / 0xe808c / 0xe8228)

F = TM.F

SOURCE_NAMES = ["CueMaster", "Cue12", "Cue34", "Cue56", "Cue78", "Cue1", "Cue2", "Cue3", "Cue4", "Cue5", "Cue6", "Cue7", "Cue8"]
# (pair if router +0x98 == 0, pair if +0x98 == 1, CueMaster flag +0x140); -1 = channel not written (mono source)
SOURCE_PAIRS = {
    0: ((0, 1), (2, 3), 1),
    1: ((4, 5), (2, 3), 0),
    2: ((6, 7), (6, 7), 0),
    3: ((8, 9), (8, 9), 0),
    4: ((10, 11), (10, 11), 0),
    5: ((4, -1), (2, -1), 0),
    6: ((-1, 5), (-1, 3), 0),
    7: ((6, -1), (6, -1), 0),
    8: ((7, -1), (7, -1), 0),
    9: ((8, -1), (8, -1), 0),
    10: ((9, -1), (9, -1), 0),
    11: ((10, -1), (10, -1), 0),
    12: ((11, -1), (11, -1), 0),
}
MAIN_OUT_PAIRS = {0: (0, 1), 1: (2, 3)}     # Output12Router: "Master", "4Assign"


class Selector:
    """OutputSelector processBlock 0xe6b8c. target/current pairs (+0x8c/+0x90, +0x94/+0x98), GainSmoother(xfade, 1.0) +0x88.
    If current != target: setTarget(0); if the smoother is idle (fade-out finished in an earlier block): current := target,
    setTarget(1). Then copy-with-gain of the current pair into ch0/1 (stereo 0xe89f0, mono 0xe8f10 + copy 0x578724).
    Selecting the current pair again during a fade-out does not restart the fade-in (the gain stays at 0 until the next change)."""
    def __init__(self, xfade=128, mono_dup=True, initial=(0, 1)):
        self.sm = TM.Smoother(xfade, 1.0)
        self.target = tuple(initial); self.cur = tuple(initial); self.mono_dup = mono_dup

    def select(self, a, b):                 # setSelection 0xe6ff4 (single-thread path: store the target)
        self.target = (a, b)

    def process(self, chans):
        """chans: list of channel lists, modified in place (ch0/1 overwritten)."""
        if self.cur != self.target:
            self.sm.set_target(0.0, 1, 0)
            if self.sm.state == 0:
                self.cur = self.target
                self.sm.set_target(1.0, 1, 0)
        a, b = self.cur
        if a >= 0 and b >= 0:
            out = [chans[a][:], chans[b][:]]
            self.sm.apply(out)
            chans[0][:] = out[0]; chans[1][:] = out[1]
        elif a >= 0:
            out = [chans[a][:]]
            self.sm.apply(out)
            chans[0][:] = out[0]
            if self.mono_dup: chans[1][:] = chans[0][:]
        elif b >= 0:
            out = [chans[b][:]]
            self.sm.apply(out)
            chans[1][:] = out[0]
            if self.mono_dup: chans[0][:] = chans[1][:]
        # both < 0: ch0/1 untouched (not produced by setHeadphoneSource)


class HeadphoneRouter:
    """HeadphoneRouter (new 0x148, vt 0x8624dc): +0x98 flag (always 1 in 1.60), +0xa0 Selector(7 pairs), +0xa4 source index,
    +0x140 CueMaster flag."""
    def __init__(self, source=0, flag98=1):
        self.flag98 = flag98
        self.sel = Selector(128, True, (0, 1))
        self.source = None; self.master = 0
        self.set_source(source)

    def set_source(self, idx):              # setHeadphoneSource 0x1afbac
        if idx not in SOURCE_PAIRS:         # unknown index: no selection change; flag cleared; index still recorded
            self.source = idx; self.master = 0
            return
        p0, p1, m = SOURCE_PAIRS[idx]
        self.sel.select(*(p1 if self.flag98 else p0))
        self.source = idx; self.master = m

    def process(self, chans):
        self.sel.process(chans)


class VolumeKnob:
    """VolumeKnob (Volume(0, 100) + slot 2 := 127): gain = table[index] * 0.5, GainSmoother(100, 1.0); slot 2 writes the index,
    slot 3 writes index and offset; processBlock never clears the offset (F110)."""
    def __init__(self, index=127):
        self.index = index; self.offset = 0
        self.sm = TM.Smoother(100, 1.0)

    def set(self, index, offset=None):
        self.index = index
        if offset is not None: self.offset = offset

    def apply(self, chans):
        self.sm.set_target(TM.knob_gain(self.index), 1, self.offset)
        self.sm.apply(chans)


class HeadphoneUnit:
    CUE_LEN = 44

    def __init__(self, source=0, sr=44100, flag98=1, knob=127):
        self.router = HeadphoneRouter(source, flag98)
        self.cue_ms = [FP.MuteSmoother(self.CUE_LEN, 0) for _ in range(3)]
        self.xf = FP.MuteSmoother(self.CUE_LEN, 0)
        self.xf.__init__(int(sr * 0.001), 0)  # prepareToPlay 0x1b0d94 -> setLength 0xe81e0((int)(sr * 0.001)), unmuted
        self.knob = VolumeKnob(knob)

    def process(self, ch14, cue6, gates=(0, 0, 0), xfade=0):
        """ch14: 14 input channel lists (HP graph inputs); cue6: 6 monitor channels (or None = no cue source);
        gates: IMonitorMixer slot 4(k, 0) results; xfade: IMonitorMixer slot 8 result. Returns [L, R]."""
        n = len(ch14[0])
        ch = [[F(x) for x in c] for c in ch14]
        self.router.process(ch)
        L, R = ch[0], ch[1]
        cue = [[F(x) for x in c] for c in cue6] if cue6 is not None else [[0.0] * n for _ in range(6)]
        for k in range(3):
            self.cue_ms[k].set_muted(gates[k] if self.router.master else 0)
        for k in range(3):
            cl, cr = cue[2 * k], cue[2 * k + 1]
            self.cue_ms[k].process(cl, cr, n)
            L[:] = [TM.neon_add(a, b) for a, b in zip(L, cl)]
            R[:] = [TM.neon_add(a, b) for a, b in zip(R, cr)]
        self.xf.set_muted(xfade)
        self.xf.crossfade(L, R, ch[11], ch[12], n)
        self.knob.apply([L, R])
        return [L, R]


class Output12Router:
    """Output12Router (new 0x98, vt 0x862b54): Selector(2 pairs) +0x8c on the 4-channel buffer [master L/R, MTU out6/7]."""
    def __init__(self, mode=0):
        self.sel = Selector(128, True, (0, 1))
        self.mode = None
        self.set_mode(mode, force=True)

    def set_mode(self, v, force=False):      # 0x1b28f8(value, force)
        if v == self.mode and not force:
            return
        if v in MAIN_OUT_PAIRS:
            self.sel.select(*MAIN_OUT_PAIRS[v])
        self.mode = v

    def process(self, ch4):
        ch = [[F(x) for x in c] for c in ch4]
        self.sel.process(ch)
        return [ch[0], ch[1]]
