# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Clean re-implementation of the SP-16 1.60 device output stage (F109-F114, H055; docs/effects/signal-flow.md). Own code, no firmware bytes.

AudioDeviceOutputUnit (graph node "deviceOutputUnitNode", object sys+0x3b8, node sys+0x3c0; ctor 0x1ae7dc, processBlock 0x1ae3e4) is the
last node of the AudioProcessorGraph before the device. It has 7 stereo pairs = 14 in / 14 out (see docs/effects/signal-flow.md for addresses):

    for pair p in 0..6 (channels 2p, 2p+1, processed in place):
        OutputVolume[p]   Volume subclass, index 0..1023 (ctor 1023), gain = table[index] * float(1/32767) with the same
                          100-sample linear GainSmoother as the track fader (ramp starts after the parameter's sample offset)
        FixedAttenuator[p] multiply by a constant: -cfg[p] for pairs 0..5 (the ctor flips the sign when the pair's flag is set),
                          +cfg[6] for pair 6. cfg = AudioSystemBase config floats sys+0x24c..0x260 (pair 6 reuses sys+0x24c):
                          0.5 in the product (HexaTrackAudioSystem) build, 1.0 in the factory test build.
    then BulkMuteUnit over all 14 channels: one 64-sample MuteSmoother per pair; current/target state bytes; while the states differ
    every pair's MuteSmoother runs and the target is adopted when all have finished; when current == target == muted the whole
    buffer is cleared; when both are unmuted nothing is done. Built muted, then unmuted by the AudioDeviceOutputUnit ctor (so the
    first block adopts "unmuted" with no fade). muteAllOutput(bool) 0x1c10f4 calls mute 0x1aeee4 / unmute 0x1aef3c.

Graph: pairs 0..5 = device output channels 0..11 (master, assignable outs (3 pairs), headphones, DSF filter send), pair 6 = (12,13) ->
digital resample recorder (internal, no sign flip). No clipping, limiting or integer conversion happens in this unit.

The OutputVolume table (1024 x u16 at 0x83d750, 0 .. 32767) is a hand-drawn piecewise-linear taper; it has no closed form we could find,
so it is read from the 1.60 binary at run time (like glibc_expf.load_tables); nothing of it is stored here.
The default TARGET path below is the research-folder layout (the model sat in harness/models/ next to target/ and decoded/; in this repo pass the path explicitly, see tools/fx/README.md): call load_table(path) with the path to your own 1.60
EP085_Main_R (the SHA-256 is checked).
Arithmetic as track_mix.py (float32 round-to-nearest; NEON flush-to-zero in the JUCE vector helpers, scalar tail keeps denormals).
"""
import hashlib, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from track_mix import F, Smoother, MuteSmoother, vec_mul   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = os.path.join(ROOT, "target", "EP085_Main_R_fw160")
SHA = "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"
TABLE_VA, IMAGE_BASE, N_INDEX = 0x83d750, 0x8000, 1024          # first PT_LOAD: file offset 0 <-> VA 0x8000
SCALE = F(1.0 / 32767.0)                                           # literal used by OutputVolume slot 13 0xe9914
RAMP = 100
PAIRS = 7
BULK_LEN = 64
CFG_PRODUCT = [0.5] * 7       # sys+0x24c..0x260 (+ pair 6 = sys+0x24c) written by 0x5712cc for HexaTrackAudioSystem
CFG_TEST = [1.0] * 7          # same words for TestModeAudioSystem
FLAGS = [1, 1, 1, 1, 1, 1, 0]  # sign-flip flags built by 0x1b6284 (pairs 0..5 set, pair 6 clear)

_TABLE = None


def load_table(path=TARGET):
    """Read the 1024-entry u16 OutputVolume table from the 1.60 binary (hash-checked). Returns a tuple of ints."""
    global _TABLE
    if _TABLE is None or path != TARGET:
        raw = open(path, "rb").read()
        assert hashlib.sha256(raw).hexdigest() == SHA, "not the 1.60 EP085_Main_R_fw160"
        off = TABLE_VA - IMAGE_BASE
        t = struct.unpack_from("<%dH" % N_INDEX, raw, off)
        if path != TARGET: return t
        _TABLE = t
    return _TABLE


def outvol_gain(index, table=None):
    """OutputVolume slot 13: float(u16 table[index]) * float(1/32767). 0 -> 0, 1 -> 206/32767 (-44.0 dB), 1008..1023 -> 1.0."""
    t = table or load_table()
    return F(float(t[index]) * SCALE)


class OutputVolume:
    """Volume(1023, 100): index (+0x8c), sample offset (+0x90), GainSmoother(100, 1.0) (+0x88).
    slot 2 sets the index only (the stored offset is kept and reused); slot 3 sets index and offset."""
    def __init__(self, index=1023, table=None):
        self.index = index; self.offset = 0; self.table = table
        self.sm = Smoother(RAMP, 1.0)

    def set(self, index, offset=None):
        self.index = index
        if offset is not None: self.offset = offset

    def apply(self, chans):
        self.sm.set_target(outvol_gain(self.index, self.table), 1, self.offset)
        self.sm.apply(chans)


class FixedAttenuator:
    def __init__(self, cfg, flip):
        self.g = F(-cfg) if flip else F(cfg)

    def apply(self, chans):
        for c in chans: vec_mul(c, 0, len(c), self.g)        # FloatVectorOperations::multiply 0x579178 (NEON + scalar tail)


class BulkMute:
    """BulkMuteUnit(7, 64) (ctor 0x1af1b0, processBlock 0x1aec8c, mute 0x1aeee4, unmute 0x1aef3c)."""
    def __init__(self, pairs=PAIRS, length=BULK_LEN, unmute_after_ctor=True):
        self.ms = [MuteSmoother(length, on=True) for _ in range(pairs)]   # ctor arg 0: idle, gain 1
        self.cur = True; self.tgt = True                                     # +0x8c / +0x8d: built muted
        if unmute_after_ctor: self.set_muted(False)

    def set_muted(self, m):
        self.tgt = bool(m)
        for s in self.ms: s.set_muted(self.tgt)

    def process(self, chans):
        if self.cur == self.tgt:
            if self.cur:
                for c in chans:
                    for i in range(len(c)): c[i] = 0.0
            return
        want = 2 if self.tgt else 0
        done = True
        for p, s in enumerate(self.ms):
            s.apply([chans[2 * p], chans[2 * p + 1]])
            done = done and s.state == want
        if done: self.cur = self.tgt


class DeviceOut:
    """AudioDeviceOutputUnit::processBlock 0x1ae3e4 on 14 channel lists (in place; also returned)."""
    def __init__(self, cfg=CFG_PRODUCT, flags=FLAGS, indices=None, table=None):
        self.vol = [OutputVolume((indices or [1023] * PAIRS)[p], table) for p in range(PAIRS)]
        self.att = [FixedAttenuator(cfg[p], flags[p]) for p in range(PAIRS)]
        self.bulk = BulkMute()

    def process(self, chans):
        chans = [[F(x) for x in c] for c in chans]
        for p in range(PAIRS):
            pair = [chans[2 * p], chans[2 * p + 1]]
            self.vol[p].apply(pair)
            self.att[p].apply(pair)
        self.bulk.process(chans)
        return chans


class OutputVolumeController:
    """OutputVolumeController (vt 0x866158; ctor 0x1d1308, apply 0x1d1210, listener 0x1d12d4): listens to UIVolume id 1 (a 10-bit panel
    pot, 0..1023). v == 0 -> OutputVolume[0..4] and [6] = 0; v != 0 -> [0] = [6] = 1023 (OutputVolume slot 6 = 1023), [1..4] = v.
    Pair 5 (DSF send) is never touched."""
    def __init__(self, dev):
        self.dev = dev

    def on_pot(self, v, src_id=1):
        if src_id != 1: return
        d = self.dev.vol
        d[0].set(1023 if v else 0); d[6].set(1023 if v else 0)
        for p in (1, 2, 3, 4): d[p].set(v)


def table_summary(table=None):
    """Short numeric description of the taper (used in the research log; no bulk dump)."""
    import math
    t = table or load_table()
    pts = {i: (t[i], (20 * math.log10(t[i] / 32767.0)) if t[i] else None) for i in (0, 1, 100, 256, 512, 768, 900, 1000, 1008, 1023)}
    return pts
