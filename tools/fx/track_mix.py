# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Clean re-implementation of the SP-16 1.60 per-track mixing chain (F095-F101, H009; docs/effects/signal-flow.md). Own code, no firmware bytes.

Signal flow of one track (TrackUnit::processBlock, 64 frames per block; track buffer = 6 channels):
    source (PlayerUnit) -> main L/R (ch 0/1)
    copy main -> ch 4/5                                (pre-insert tap: Dave-Smith/DSF send source)
    insert FX processors, in slot order, on main
    Mute #2 on ch 4/5
    Pan on main  (linear balance law, 0 dB centre)
    Mute #1 on main
    copy main -> ch 2/3, VolumeKnob on ch 2/3          (send tap: post-insert, post-pan, post-mute, pre-fader)
    VolumeFader on main                                (track level)
MultiTrackUnit then sums ch 0/1 of all tracks into its output 0/1 and ch 2/3 into output 2/3 with gain 1.0
(SimpleTwoMixUnit, normalisation off).

Arithmetic: IEEE single precision, round to nearest (F() = round a double to float; a single +,-,*,/ of two floats done in double
and rounded once equals the float operation). Scalar VFP code keeps denormals (FPSCR.FZ = 0). JUCE vector helpers use NEON;
ARMv7 NEON flushes denormal inputs and results to zero (`ftz`).
"""
import ctypes, math

_cf = ctypes.c_float


def F(x): return _cf(x).value


TINY = 1.1754943508222875e-38           # smallest normal float


def ftz(x):
    return math.copysign(0.0, x) if (x != 0.0 and abs(x) < TINY) else x


def neon_mul(x, g):                      # FloatVectorOperations::copyWithMultiply / multiply (NEON lanes)
    return ftz(F(ftz(x) * ftz(g)))


def vec_mul(c, pos, k, g):
    """FloatVectorOperations::copyWithMultiply(dst, src, g, k) as compiled in 1.60 (0x5792c8): the first 4*(k//4) samples of the
    segment in NEON lanes (denormals flushed), the remaining k % 4 samples with scalar VFP (denormals kept)."""
    nv = 4 * (k // 4)
    for i in range(pos, pos + nv): c[i] = neon_mul(c[i], g)
    for i in range(pos + nv, pos + k): c[i] = F(c[i] * g)


def neon_add(a, b):                      # FloatVectorOperations::add (NEON lanes)
    return ftz(F(ftz(a) + ftz(b)))


# ---------------------------------------------------------------------------------------------------------------------
# gain laws
_LOW_DB = {1: -54, 2: -50, 3: -48, 4: -46, 5: -45, 6: -44, 7: -43, 8: -42, 9: -41}


def volume_table():
    """128 entries. 0 = silence, 1..9 = fixed dB steps, 10..100 = (i/100)^2, 101..127 = 2^(ln(i/100)/ln(1.27)), i.e. (i/100)^2.89999
    so that 127 -> exactly 2.0 (+6.02 dB)."""
    t = [0.0] * 128
    for i in range(1, 128):
        if i < 10:
            t[i] = F(10.0 ** (_LOW_DB[i] / 20.0))
        elif i <= 100:
            t[i] = F((i / 100.0) ** 2)
        else:
            t[i] = F(2.0 ** (math.log(i / 100.0) / math.log(1.27)))
    return t


VOLUME_TABLE = volume_table()


def fader_gain(index):          # VolumeFader / Volume slot 13: table[index]
    return VOLUME_TABLE[index]


def knob_gain(index):           # VolumeKnob slot 13: table[index] * 0.5   (127 -> 1.0, 100 -> 0.5)
    return F(VOLUME_TABLE[index] * 0.5)


def pan_gains(p):
    """Pan::processBlock: linear balance. p in -64..+64. Centre: both 1.0 (0 dB)."""
    p = int(p)
    if p < 0:
        return 1.0, F(float(p + 64) * 0.015625)
    if p > 0:
        return F(float(64 - p) * 0.015625), 1.0
    return 1.0, 1.0


def clamp_param(value, mod, mod_on, lo, hi):
    """Parameter struct (ctor 0x1c3b70): with modulation on, value + mod is clamped to [lo, hi]; otherwise value is used as is."""
    if not mod_on:
        return value
    v = value + mod
    return lo if v < lo else (hi if v >= hi else v)


# ---------------------------------------------------------------------------------------------------------------------
class Smoother:
    """Linear gain smoother (0x24-byte struct; ctor 0xe8900, setTarget 0xe895c, stereo apply 0xe89f0, mono apply 0xe8f10)."""
    def __init__(self, length, init=1.0):
        self.length = length if length > 0 else 1
        self.inv = F(1.0 / float(length)) if length > 0 else 1.0
        self.step = 0.0; self.target = F(init); self.cur = F(init)
        self.count = 0; self.offset = 0; self.flag = 1; self.state = 0

    def set_target(self, t, force=1, offset=0):
        t = F(t)
        if not self.flag and force:
            return
        if self.target == t:
            return
        self.step = F(F(t - self.cur) * self.inv)
        self.target = t; self.count = self.length; self.offset = offset
        self.state = 2 if offset > 0 else 1
        self.flag = force

    def apply(self, chans):
        n = len(chans[0]); pos = 0
        while n:
            if self.state == 2:
                k = n if self.offset >= n else self.offset
                for c in chans: vec_mul(c, pos, k, self.cur)
                if self.offset >= n:
                    self.offset -= n
                    return
                pos += k; n -= k; self.offset = 0; self.state = 1
                continue
            if self.state == 1:
                g = self.cur
                k = n if self.count > n else self.count
                for i in range(pos, pos + k):
                    for c in chans: c[i] = F(c[i] * g)
                    g = F(g + self.step)
                pos += k; n -= k
                if self.count > k:
                    self.count -= k; self.cur = g
                    return
                self.cur = self.target; self.count = 0; self.state = 0; self.step = 0.0; self.flag = 1
                continue
            for c in chans: vec_mul(c, pos, n, self.cur)
            return

    def state_tuple(self):
        return (self.step, self.target, self.cur, self.count, self.length, self.inv, self.offset, self.flag, self.state)


class MuteSmoother:
    """MuteSmoother (ctor 0xe7fd8, set 0xe8050, apply 0xe808c): 128-sample linear fade; the muted state clears the buffer."""
    def __init__(self, length=128, on=False):
        self.length = length if length > 0 else 1
        self.inv = F(1.0 / float(length)) if length > 0 else 1.0
        self.counter = 0; self.muted = not on
        if on:
            self.step = -self.inv; self.g = 1.0; self.state = 0
        else:
            self.step = self.inv; self.g = 0.0; self.state = 2

    def set_muted(self, m):
        m = bool(m)
        if self.muted == m:
            return
        self.step = -self.inv if m else self.inv
        self.muted = m; self.counter = self.length - self.counter; self.state = 1

    def apply(self, chans):
        n = len(chans[0]); pos = 0
        while n:
            if self.state == 0:
                return
            if self.state == 2:
                for c in chans:
                    for i in range(pos, pos + n): c[i] = 0.0
                return
            k = n if self.counter >= n else self.counter
            g = self.g
            for i in range(pos, pos + k):
                for c in chans: c[i] = F(c[i] * g)
                g = F(g + self.step)
            if self.counter >= n:
                self.counter -= n; self.g = g
                return
            pos += k; n -= k; self.counter = 0
            if self.muted:
                self.state = 2; self.g = 0.0
            else:
                self.state = 0; self.g = 1.0
                return


# ---------------------------------------------------------------------------------------------------------------------
class Track:
    """One TrackUnit. fader index 0..127 (TrackData volume; VolumeFader ctor 100 = 0 dB), pan -64..64 (TrackData pan),
    send index 0..127 (VolumeKnob, ctor 0), mute flags (Mute+0x84). Each value may carry a sample offset at which its
    100-sample ramp starts."""
    RAMP = 100

    def __init__(self, fader=100, pan=0, send=0, main_on=True, pre_on=False):
        self.fader = fader; self.pan = pan; self.send = send
        self.fader_off = self.pan_off = self.send_off = 0
        self.sm_fader = Smoother(self.RAMP, 1.0)
        self.sm_pan_l = Smoother(self.RAMP, 1.0); self.sm_pan_r = Smoother(self.RAMP, 1.0)
        self.sm_send = Smoother(self.RAMP, 1.0)
        self.mute_main = MuteSmoother(128, on=False); self.mute_pre = MuteSmoother(128, on=False)
        self.main_on = main_on; self.pre_on = pre_on

    def set(self, fader=None, pan=None, send=None, offset=0):
        if fader is not None: self.fader, self.fader_off = fader, offset
        if pan is not None: self.pan, self.pan_off = pan, offset
        if send is not None: self.send, self.send_off = send, offset

    def process(self, src_l, src_r, inserts=()):
        L = [F(x) for x in src_l]; R = [F(x) for x in src_r]
        pre_l, pre_r = L[:], R[:]                               # ch 4/5 tap (two copyFrom calls after the player)
        for fx in inserts:                                      # InsertFxProcessor slot 5, in slot order
            L, R = fx(L, R)
        self.mute_pre.set_muted(not self.pre_on); self.mute_pre.apply([pre_l, pre_r])
        gl, gr = pan_gains(self.pan)
        self.sm_pan_l.set_target(gl, 1, self.pan_off); self.sm_pan_r.set_target(gr, 1, self.pan_off)
        self.sm_pan_l.apply([L]); self.sm_pan_r.apply([R])
        self.mute_main.set_muted(not self.main_on); self.mute_main.apply([L, R])
        s_l, s_r = L[:], R[:]                                   # ch 2/3 tap
        self.sm_send.set_target(knob_gain(self.send), 1, self.send_off); self.sm_send.apply([s_l, s_r])
        self.sm_fader.set_target(fader_gain(self.fader), 1, self.fader_off); self.sm_fader.apply([L, R])
        self.fader_off = self.pan_off = self.send_off = 0       # processBlock clears the parameter offsets (+0x10) after use
        return [L, R, s_l, s_r, pre_l, pre_r]


def sum_tracks(track_outs, pair, normalise=False):
    """SimpleTwoMixUnit (0x1535f8): bus = ((0 + t0) + t1) + ... per channel with NEON adds; normalise -> * 1/(numCh/2)."""
    n = len(track_outs[0][0])
    acc_l = [0.0] * n; acc_r = [0.0] * n
    for t in track_outs:
        acc_l = [neon_add(a, b) for a, b in zip(acc_l, t[pair[0]])]
        acc_r = [neon_add(a, b) for a, b in zip(acc_r, t[pair[1]])]
    if normalise:
        g = F(1.0 / float(len(track_outs) + 1))
        acc_l = [neon_mul(a, g) for a in acc_l]; acc_r = [neon_mul(a, g) for a in acc_r]
    return acc_l, acc_r


# ---------------------------------------------------------------------------------------------------------------------
# Cycle 037 (H052) additions — routing modes of the DSF (analog filter) loop. Additive: Track above is unchanged (H009 hashes).
class OutputSelector:
    """OutputSelector (0xa0; ctor 0xe6ee4(pairs 2, async 0, monoDup 1, xfade 128), processBlock 0xe6b8c, setSelection 0xe6ff4).
    Input view of 4 channels = 2 stereo pairs; writes the selected pair into channels 0/1 through a GainSmoother (copy x gain).
    A new selection fades the OLD pair 1 -> 0 over `xfade` samples; in the first block that starts with the fade finished the
    selector switches to the new pair and fades it 0 -> 1 over `xfade` samples (a dip, not an overlap crossfade)."""
    def __init__(self, xfade=128):
        self.sm = Smoother(xfade, 1.0)
        self.target = (0, 1); self.cur = (0, 1)

    def select(self, a, b):                  # setSelection 0xe6ff4 (async flag 0 -> stores the target pair only)
        self.target = (a, b)

    def process(self, chans):
        if self.cur != self.target:
            self.sm.set_target(0.0, 1, 0)
            if self.sm.state == 0:           # fade-out finished in an earlier block
                self.cur = self.target
                self.sm.set_target(1.0, 1, 0)
        out = [chans[self.cur[0]][:], chans[self.cur[1]][:]]
        self.sm.apply(out)
        return out


# TrackUnit::setSendSource (slot 101 0x1ca218 -> 0x1ca0dc): selections per mode (0 = no DSF loop, 1 = DSF Pre FX, 2 = DSF Post FX)
ROUTING = {0: {"110": (0, 1), "118": (0, 1), "114": (0, 1)},
           1: {"110": (2, 3), "118": (0, 1), "114": (0, 1)},
           2: {"110": (0, 1), "118": (2, 3), "114": (2, 3)}}


class RoutedTrack(Track):
    """Track with the four OutputSelectors of TrackUnit::processBlock 0x1ca58c and the two external buffers
    (+0x604 = MultiTrackUnit +0x100 = MTU input ch 0/1, the audio input; +0x608 = MTU +0x198 = MTU input ch 4/5, the DSF return).
      +0x10c [main, ext604]  -> main   (track type Thru selects ext604, 0x1cb584)
      copy main -> ch 4/5    (DSF send tap)
      +0x110 [main, ext608]  -> main   (mode 1: DSF return replaces the source before the inserts)
      inserts on main
      +0x118 [ch4/5, main]   -> ch 4/5 (mode 2: post-insert main is sent to the DSF)
      Mute #2 on ch 4/5      (open iff the track is audible and mode != 0, 0x1ca3c8)
      +0x114 [main, ext608]  -> main   (mode 2: DSF return replaces the post-insert main)
      then Pan / Mute #1 / send tap / fader exactly as Track."""
    def __init__(self, mode=0, thru=False, **kw):
        super().__init__(**kw)
        self.sel = {k: OutputSelector() for k in ("10c", "110", "114", "118")}
        self.mode = 0; self.thru = False
        self.set_mode(mode); self.set_thru(thru)
        for s in self.sel.values():          # construction-time selections take effect without a fade
            s.cur = s.target

    def set_mode(self, mode):
        if mode in ROUTING:                  # 0x1ca0dc ignores other values
            for k, p in ROUTING[mode].items(): self.sel[k].select(*p)
            self.mode = mode

    def set_thru(self, thru):
        self.thru = bool(thru); self.sel["10c"].select(*((2, 3) if thru else (0, 1)))

    def process(self, src_l, src_r, ext604=None, ext608=None, inserts=()):
        n = len(src_l)
        z = [0.0] * n
        e4 = ext604 or (z, z); e8 = ext608 or (z, z)
        e4 = [[F(x) for x in e4[0]], [F(x) for x in e4[1]]]; e8 = [[F(x) for x in e8[0]], [F(x) for x in e8[1]]]
        L = [F(x) for x in src_l]; R = [F(x) for x in src_r]
        pre_on = self.main_on and self.mode != 0  # 0x1ca3c8 (track gate open, not Midi assumed)
        L, R = self.sel["10c"].process([L, R, e4[0], e4[1]])
        pre_l, pre_r = L[:], R[:]
        L, R = self.sel["110"].process([L, R, e8[0], e8[1]])
        for fx in inserts:                   # the track buffer is float32: an insert's output is stored rounded
            L, R = fx(L, R); L = [F(x) for x in L]; R = [F(x) for x in R]
        pre_l, pre_r = self.sel["118"].process([pre_l, pre_r, L, R])
        self.mute_pre.set_muted(not pre_on); self.mute_pre.apply([pre_l, pre_r])
        L, R = self.sel["114"].process([L, R, e8[0], e8[1]])
        gl, gr = pan_gains(self.pan)
        self.sm_pan_l.set_target(gl, 1, self.pan_off); self.sm_pan_r.set_target(gr, 1, self.pan_off)
        self.sm_pan_l.apply([L]); self.sm_pan_r.apply([R])
        self.mute_main.set_muted(not self.main_on); self.mute_main.apply([L, R])
        s_l, s_r = L[:], R[:]
        self.sm_send.set_target(knob_gain(self.send), 1, self.send_off); self.sm_send.apply([s_l, s_r])
        self.sm_fader.set_target(fader_gain(self.fader), 1, self.fader_off); self.sm_fader.apply([L, R])
        self.fader_off = self.pan_off = self.send_off = 0
        return [L, R, s_l, s_r, pre_l, pre_r]


def dsf_apply(route, send_mode, send_track, filter_on, n_tracks):
    """DaveSmithManager apply 0xc64b0: TrackUnit mode per track. route 1 (Track) with the filter on gives the selected track
    [1, 2][send_mode] (table 0x834ac8; send_mode >= 2 -> 0); every other track, route 0 (Master) or filter off -> 0."""
    if route == 1 and filter_on:
        v = (1, 2)[send_mode] if 0 <= send_mode < 2 else 0
        return [v if t == send_track else 0 for t in range(n_tracks)]
    return [0] * n_tracks
