# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Clean re-implementation of the SP-16 1.60 bus side of the mixer (F102-F108, H010; docs/effects/signal-flow.md). Own code, no firmware bytes.

Signal flow after MultiTrackUnit (64 frames per block; see docs/effects/signal-flow.md for the addresses):

    MTU out0/1 (track main sum) --> CompositeFxUnit in0/1 --> MasterFxUnit (Master FX processor, in place) --> out0/1
    MTU out2/3 (track send sum) --> CompositeFxUnit in2/3 --> SendFxUnit:  Send FX processor (in place)
                                                                           --> return VolumeFader (128-entry table, 100 = 0 dB)
                                                                           --> meter                               --> out2/3
    CompositeFxUnit has no summing of its own: out0/1 = Master FX(in0/1), out2/3 = Send return(in2/3).

    MasterOutUnit in0/1 = CompositeFxUnit out0/1, in2/3 = CompositeFxUnit out2/3, in4/5 = MTU out14/15:
        SimpleTwoMixUnit(6): ch0 += ch2, ch0 += ch4 (and ch1 += ch3, ch1 += ch5), NEON adds, gain 1.0
        master VolumeFader on ch0/1 (same table and 100-sample ramp as the track fader)
        meter, renderer (no audio change)
        ch2/3 := copy of ch0/1 (feeds the headphone unit), ch0/1 -> masterAssignableSelector -> DSF drive -> device out 0/1.

So the Send FX return is summed into the master bus AFTER the Master FX (not before it). The FX mode of CompositeFxUnit
(prj::RoutingData "EffectModeSend"/"EffectModeMaster") enables one of the two processors and disables the other; a disabled
or "Off" Send processor mutes its input with a 132-sample (3 ms) fade (MuteSmoother) before the (absent) effect.

FX processors are parameters of this model (callables f(L, R) -> (L, R)); the real effects are modelled elsewhere.
Arithmetic as in track_mix.py (float32 round-to-nearest, NEON flush-to-zero in the JUCE vector helpers).
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from track_mix import F, neon_add, Smoother, MuteSmoother, fader_gain   # noqa: E402

RAMP = 100


class Fader:
    """A Volume/VolumeFader object (index 0..127, ctor index 100) with its 100-sample linear GainSmoother."""
    def __init__(self, index=100):
        self.index = index; self.offset = 0
        self.sm = Smoother(RAMP, 1.0)

    def set(self, index, offset=0):
        self.index = index; self.offset = offset

    def apply(self, chans):
        self.sm.set_target(fader_gain(self.index), 1, self.offset)
        self.offset = 0
        self.sm.apply(chans)


class SendUnit:
    """SendFxUnit::processBlock: processor (in place) -> return fader -> meter (no change)."""
    def __init__(self, fx=None, ret_index=100):
        self.fx = fx; self.ret = Fader(ret_index)

    def process(self, L, R):
        if self.fx is not None:
            L, R = self.fx(L, R)
        self.ret.apply([L, R])
        return L, R


class SendProcessorMute:
    """SendFxProcessor::processBlock front end: MuteSmoother +0xa8 muted when no effect is pending or the processor is disabled
    (+0x9e), applied to the send bus before the effect. Built in prepareToPlay with length rint(sr * 0.001 * 3) (132 at 44.1 kHz),
    initially unmuted."""
    def __init__(self, sr=44100):
        n = int(F(F(F(float(sr)) * F(0.001)) * 3.0) + 6755399441055744.0 - 6755399441055744.0)
        self.ms = MuteSmoother(n, on=True)

    def process(self, L, R, active):
        self.ms.set_muted(not active)
        self.ms.apply([L, R])
        return L, R


def composite(ins, master_fx, send_unit):
    """CompositeFxUnit::processBlock: in place, no summing. ins = 4 channel lists. Returns 4 lists."""
    m = [F(x) for x in ins[0]], [F(x) for x in ins[1]]
    s = [F(x) for x in ins[2]], [F(x) for x in ins[3]]
    ml, mr = master_fx(*m) if master_fx else m
    sl, sr = send_unit.process(*s) if send_unit else s
    return [ml, mr, sl, sr]


class MasterOut:
    """MasterOutUnit::processBlock (6 in / 4 out used)."""
    def __init__(self, index=100):
        self.fader = Fader(index)

    def process(self, ch):
        ch = [[F(x) for x in c] for c in ch]
        L = [neon_add(neon_add(a, b), c) for a, b, c in zip(ch[0], ch[2], ch[4])]
        R = [neon_add(neon_add(a, b), c) for a, b, c in zip(ch[1], ch[3], ch[5])]
        self.fader.apply([L, R])
        return [L, R, L[:], R[:], ch[4], ch[5]]


class BusChain:
    """MTU outputs (main 0/1, send 2/3, out14/15) -> CompositeFxUnit -> MasterOutUnit. Returns MasterOutUnit channels."""
    def __init__(self, master_fx=None, send_fx=None, ret_index=100, master_index=100):
        self.master_fx = master_fx
        self.send = SendUnit(send_fx, ret_index)
        self.mout = MasterOut(master_index)

    def process(self, main_l, main_r, send_l, send_r, x_l, x_r):
        c = composite([main_l, main_r, send_l, send_r], self.master_fx, self.send)
        return c, self.mout.process(c + [x_l, x_r])


def dsf_drive_gain(index):
    """DSFDrive (Volume subclass in DaveSmithDriveUnit +0x88) slot 13 0xe85e8: 1 + 3*(i/1023)^2 in double, rounded to float.
    Range 0..1023 (slot 5), ctor index 0 (gain 1.0); byte +0x94 set forces 1.0. Applied with the same 100-sample GainSmoother."""
    x = float(index) * (1.0 / 1023.0)
    return F(1.0 + (x * x) * 3.0)

