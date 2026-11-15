#!/usr/bin/env python3
"""H009 — per-track mixing in 1.60: TrackUnit chain (source -> insert FX -> pan -> mute -> send tap -> fader), gain laws, smoothing,
bus summing in MultiTrackUnit / SimpleTwoMixUnit, against the own-code model harness/models/track_mix.py.

Sections (criteria of kb/cycles/018.md):
  C1  chain: static assertions (constructTrack 0x1bacec, TrackUnit ctor 0x1cceb0, setters, processBlock 0x1ca58c call sites) and an
      emulation of the REAL TrackUnit::processBlock 0x1ca58c with stand-in member objects: real Pan / VolumeFader / VolumeKnob / Mute
      code, logging fakes for the player, LFO, OutputSelectors, insert managers/processors, meter, renderer, MIDI formatter.
  C2  volume law: table 0x83e050 vs model formula (128 entries), read-back of the real VolumeFader/VolumeKnob gains (>= 5 indices),
      ramp length and offset start.
  C3  pan law: real Pan processBlock on DC for 13 pan values incl. -64/0/+64, clamp through the parameter struct, ramp.
  C4  bus layout: real MultiTrackUnit routing builders 0x1c4448/0x1c4668/0x1c4888/0x1c4dd8 on a stand-in MultiTrackUnit and the real
      SimpleTwoMixUnit processBlock 0x1535f8 summing the outputs of real TrackUnit::processBlock runs.
  C6  model: bit-exact comparison over >= 6 settings x {impulse, sine, noise, level steps}, >= 50 blocks, mid-run changes.
  C8  alternatives: model mutants (constant-power / -3 dB pan, fader before insert, normalised sum, ...) must fail.
Outputs only to --out (default harness/out/H009/). Run: .venv/bin/python -B harness/H009_track_mix.py --out DIR [--regress]
"""
import argparse, hashlib, json, math, os, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, PC, LR                               # noqa: E402
import sp16img                                                 # noqa: E402
import track_mix as M                                          # noqa: E402
from track_mix import F                                        # noqa: E402

N = 64
# --- addresses (1.60) ---------------------------------------------------------------------------------------------------
TRACK_PB, TRACK_UPD = 0x1ca58c, 0x1ca3c8
AB_CTOR, AB_REFER = 0x576998, 0x576afc
SMOOTH_CTOR, MUTE_SM_CTOR = 0xe8900, 0xe7fd8
PARAM_CTOR, PAN_RANGE, VOL_RANGE = 0x1c3b70, 0x34877c, 0xe9b1c
VT_PAN, VT_PAN2 = 0x83d540, 0x83d570
VT_FADER, VT_FADER2, VT_KNOB, VT_KNOB2 = 0x83e380, 0x83e3c0, 0x83e4a0, 0x83e4e0
VT_MUTE, VT_STMU = 0x83d1d8, 0x849010
STMU_PB = 0x1535f8
MTU_ROUTE = {"main": 0x1c4448, "send": 0x1c4668, "assign": 0x1c4888, "dsf": 0x1c4dd8}
FAKE_BASE = 0x3d000000


def sha(b): return hashlib.sha256(b).hexdigest()


# --- libc++abi guard stubs (static locals inside the routines; same semantics as the real ones on a single thread) ------
def _guard_acq(e):
    g = e.r(0); e.setr(0, 0 if (e.u32(g) & 1) else 1)
def _guard_rel(e):
    e.w32(e.r(0), 1)
emu.STUBS.setdefault("__cxa_guard_acquire", (_guard_acq, "returns 1 when guard byte bit0 is clear"))
emu.STUBS.setdefault("__cxa_guard_release", (_guard_rel, "sets guard word to 1"))


class Fakes:
    """Executable page of `bx lr` slots; each slot runs a Python callback first. fake vtables live in the heap."""
    def __init__(self, e):
        self.e = e; self.n = 0; self.log = []
        e.uc.mem_map(FAKE_BASE, 0x10000, emu.UC_PROT_READ | emu.UC_PROT_EXEC)
        e.uc.mem_write(FAKE_BASE, emu.BX_LR * (0x10000 // 4))

    def fn(self, cb):
        a = FAKE_BASE + 4 * self.n; self.n += 1
        self.e.add_watch(a, cb)
        return a

    def obj(self, name, slots, size=0x40):
        """object with vptr -> fake vtable; slots {byte_off: callback(e, name)}"""
        e = self.e
        vt = e.malloc(0x200, "fake vt " + name); o = e.malloc(size, "fake " + name)
        e.wr(vt, b"\0" * 0x200); e.wr(o, b"\0" * size)
        for off, cb in slots.items():
            e.w32(vt + off, self.fn(lambda em, cb=cb, nm=name: cb(em, nm)))
        e.w32(o, vt)
        return o


class AudioBuf:
    """juce::AudioBuffer<float> (0x98 bytes: numCh, size, allocatedBytes, channels**, allocatedData, prealloc[32], isClear @+0x94)
    built by the real default ctor 0x576998 and made to refer to harness memory with the real setDataToReferTo 0x576afc."""
    def __init__(self, e, nch, ptrs=None):
        self.e = e; self.nch = nch
        self.obj = e.malloc(0x98, "AudioBuffer"); e.call(AB_CTOR, self.obj)
        self.ptrs = ptrs or [e.malloc(4 * N, "chan") for _ in range(nch)]
        arr = e.malloc(4 * nch, "chanptrs")
        for i, p in enumerate(self.ptrs): e.w32(arr + 4 * i, p)
        e.call(AB_REFER, self.obj, arr, nch, N)

    def read(self, i): return self.e.floats(self.ptrs[i], N)
    def write(self, i, x): self.e.set_floats(self.ptrs[i], x)


class TrackRig:
    """Stand-in TrackUnit (0x628 bytes) processed by the REAL TrackUnit::processBlock 0x1ca58c.
    Real code: processBlock, AudioBuffer ops, Pan (0xe9594), Volume (0xe9b70) with VolumeFader/VolumeKnob slot 13, Mute (0xe7d80),
    smoothers 0xe8900/0xe895c/0xe89f0/0xe8f10, MuteSmoother 0xe7fd8/0xe8050/0xe808c, parameter structs 0x1c3b70.
    Stand-ins: member object fields as written by their ctors (Pan 0xe97e0, Volume 0xe9d28, VolumeFader 0xe9e5c, VolumeKnob 0xe9f10,
    Mute 0xe7ec8) without the juce::AudioProcessor base ctor; per-block mute update 0x1ca3c8 (reads prj::TrackData) is skipped and
    its two outputs (Mute+0x84 flags) are set by the harness; player / LFO / inserts / selectors / meter / renderer are logging fakes.
    """
    def __init__(self, e, fk, name="T", n_inserts=1, insert_fx=None, src=None, graph=None):
        self.e = e; self.fk = fk; self.name = name; self.events = []
        T = self.T = e.malloc(0x628, "TrackUnit stand-in"); e.wr(T, b"\0" * 0x628)
        e.w32(T, 0x864cac)
        for off in (0x144, 0x1dc, 0x274, 0x30c, 0x3a4, 0x43c, 0x4d4, 0x56c): e.call(AB_CTOR, T + off)
        self.ext = [AudioBuf(e, 2), AudioBuf(e, 2)]
        e.w32(T + 0x604, self.ext[0].obj); e.w32(T + 0x608, self.ext[1].obj)
        self.graph = graph or AudioBuf(e, 6)
        self.midi = e.malloc(0x10, "MidiBuffer"); e.wr(self.midi, b"\0" * 0x10)
        self.src = src; self.insert_fx = insert_fx or []
        tmp = e.malloc(8, "range")

        def smoother(length):
            s = e.malloc(0x24, "smoother"); e.call(SMOOTH_CTOR, s, length, f2u(1.0)); return s

        def pstruct(range_fn):
            p = e.malloc(0x24, "param struct"); e.call(range_fn, tmp); e.call(PARAM_CTOR, p, tmp); return p
        # Pan (ctor 0xe97e0 with ramp 100): +0x88/+0x8c smoothers, +0x90 pan, +0x94 offset
        self.pan = P = e.malloc(0x98, "Pan"); e.wr(P, b"\0" * 0x98)
        e.w32(P, VT_PAN); e.w32(P + 8, VT_PAN2); e.w32(P + 0x88, smoother(100)); e.w32(P + 0x8c, smoother(100))
        # VolumeFader (0xe9e5c -> 0xe9d28(this, 100, 100)), VolumeKnob (0xe9f10 -> 0xe9d28(this, 0, 100))
        self.fader = V = e.malloc(0x98, "VolumeFader"); e.wr(V, b"\0" * 0x98)
        e.w32(V, VT_FADER); e.w32(V + 8, VT_FADER2); e.w32(V + 0x88, smoother(100)); e.w32(V + 0x8c, 100)
        self.knob = K = e.malloc(0x98, "VolumeKnob"); e.wr(K, b"\0" * 0x98)
        e.w32(K, VT_KNOB); e.w32(K + 8, VT_KNOB2); e.w32(K + 0x88, smoother(100)); e.w32(K + 0x8c, 0)
        # Mute x2 (0xe7ec8(this, 0, 0x80) -> MuteSmoother(128, 1))
        self.mutes = []
        for _ in range(2):
            m = e.malloc(0x88, "Mute"); e.wr(m, b"\0" * 0x88); e.w32(m, VT_MUTE)
            s = e.malloc(0x20, "MuteSmoother"); e.call(MUTE_SM_CTOR, s, 0x80, 1); e.w32(m + 0x80, s); e.w32(m + 0x84, 0)
            self.mutes.append(m)
        e.w32(T + 0x128, P); e.w32(T + 0x134, V); e.w32(T + 0x138, K)
        e.w32(T + 0x12c, self.mutes[0]); e.w32(T + 0x130, self.mutes[1])
        self.ps_pan, self.ps_fader, self.ps_knob = pstruct(PAN_RANGE), pstruct(VOL_RANGE), pstruct(VOL_RANGE)
        e.w32(T + 0x11c, self.ps_pan); e.w32(T + 0x120, self.ps_fader); e.w32(T + 0x124, self.ps_knob)
        e.w32(self.ps_fader + 4, 100)                      # TrackData volume default -> ctor vt+8 sets index (see C2)

        # ---- logging fakes ----------------------------------------------------------------------------------------------
        def chans_of(buf):
            n = e.u32(buf); arr = e.u32(buf + 0xc)
            return [e.u32(arr + 4 * i) for i in range(n)]

        def ev(tag, buf=None, extra=None):
            self.events.append((tag, None if buf is None else buf, extra))

        def on_src(em, nm):
            buf = em.r(1); ev("player(+0xcc).process", buf, chans_of(buf))
            if self.src is not None:
                l, r = self.src
                ch = chans_of(buf); em.set_floats(ch[0], l); em.set_floats(ch[1], r)
        e.w32(T + 0xcc, fk.obj(name + ".player", {0x14: on_src}))
        e.w32(T + 0xd4, fk.obj(name + ".lfo", {0x14: lambda em, nm: ev("lfo(+0xd4).process", em.r(1))}))
        for off in (0x10c, 0x110, 0x114, 0x118):
            e.w32(T + off, fk.obj(name + ".sel%x" % off,
                                  {0x14: lambda em, nm, off=off: ev("OutputSelector(+0x%x).process" % off, em.r(1), chans_of(em.r(1)))}))
        meter = fk.obj(name + ".meter", {0x14: lambda em, nm: ev("LevelMeter(+0x13c).process", em.r(1), chans_of(em.r(1)))})
        wrap = e.malloc(0x10, "meter wrapper"); e.wr(wrap, b"\0" * 0x10); e.w32(wrap + 8, meter); e.w32(T + 0x13c, wrap)
        for off, tag in ((0x108, "AudioRenderer(+0x108)"), (0xe4, "MidiTrackOutputFormatter(+0xe4)")):
            holder = e.malloc(0x40, "holder"); e.wr(holder, b"\0" * 0x40)
            inner = fk.obj(name + tag, {0x14: lambda em, nm, tag=tag: ev(tag + ".process", em.r(1))})
            e.w32(holder + 8, e.u32(inner)); e.w32(T + off, holder)
        n = n_inserts
        mg = e.malloc(4 * max(n, 1), "mgr array"); pr = e.malloc(4 * max(n, 1), "proc array")
        for i in range(n):
            e.w32(mg + 4 * i, fk.obj(name + ".mgr%d" % i, {0x28: lambda em, nm, i=i: ev("InsertFxParameterManager[%d] vt+0x28" % i)}))

            def on_fx(em, nm, i=i):
                buf = em.r(1); ch = chans_of(buf); ev("InsertFxProcessor[%d].process" % i, buf, ch)
                if i < len(self.insert_fx):
                    l, r = self.insert_fx[i](em.floats(ch[0], N), em.floats(ch[1], N))
                    em.set_floats(ch[0], l); em.set_floats(ch[1], r)
            e.w32(pr + 4 * i, fk.obj(name + ".fx%d" % i, {0x14: on_fx}))
        e.w32(T + 0xb8, n); e.w32(T + 0xe8, mg); e.w32(T + 0xf0, n); e.w32(T + 0xf4, pr); e.w32(T + 0xfc, n)
        # skip 0x1ca3c8 (per-block mute update from prj::TrackData), record that it was reached
        self.main_on = 1; self.pre_on = 0

        def upd(em):
            if em.r(0) != self.T: return
            ev("0x1ca3c8 mute update (skipped; harness sets Mute+0x84)")
            em.w32(self.mutes[0] + 0x84, self.main_on); em.w32(self.mutes[1] + 0x84, self.pre_on)
            em.uc.reg_write(PC, em.uc.reg_read(LR))
        if not getattr(e, "_h009_upd", False):
            e._h009_upd = {}
            e.add_watch(TRACK_UPD, lambda em: em._h009_upd[em.r(0)](em) if em.r(0) in em._h009_upd else None)
        e._h009_upd[T] = upd
        # log entries of the real member processBlocks (shared code; object identified by r0)
        if not getattr(e, "_h009_objs", None):
            e._h009_objs = {}
            for addr, tag in ((0xe9594, "Pan.process (0xe9594)"), (0xe9b70, "Volume.process (0xe9b70)"),
                              (0xe7d80, "Mute.process (0xe7d80)")):
                e.add_watch(addr, lambda em, tag=tag: em._h009_objs[em.r(0)][0].events.append(
                    ("%s %s" % (tag, em._h009_objs[em.r(0)][1]), em.r(1), chans_of(em.r(1)))) if em.r(0) in em._h009_objs else None)
        for o, nm in ((P, "Pan"), (V, "VolumeFader"), (K, "VolumeKnob"), (self.mutes[0], "Mute#1(+0x12c)"),
                      (self.mutes[1], "Mute#2(+0x130)")):
            e._h009_objs[o] = (self, nm)

    # parameters through the parameter structs (value +4, sample offset +0x10), exactly what processBlock reads
    def set(self, fader=None, pan=None, send=None, offset=0):
        e = self.e
        for v, ps in ((fader, self.ps_fader), (pan, self.ps_pan), (send, self.ps_knob)):
            if v is not None:
                e.w32(ps + 4, v & 0xffffffff); e.w32(ps + 0x10, offset)

    def block(self):
        self.events = []
        self.e.call(TRACK_PB, self.T, self.graph.obj, self.midi)
        return [self.graph.read(i) for i in range(6)]


# =========================================================================================================================
REGRESS = [
    ("H021", "H021_lofi_model.py", "h021", {"report": ("9273c853", "2677"), "json": ("f3316770", "d839"), "f32": ("86f8975a", "74a4")}),
    ("H023", "H023_mmf_model.py", "h023", {"report": ("9c33b389", "25eb"), "f32": ("5ccbbf43", "2baa")}),
    ("H026", "H026_peq_model.py", "h026", {"report": ("ed20422f", "93e9"), "json": ("fa2ebab6", "fbfd"), "f32": ("a3cb6985", "8f58")}),
    ("H028", "H028_phaser_model.py", "h028", {"report": ("1810c080", "9d227e"), "f32": ("cf14c39c", "5bd7")}),
    ("H031", "H031_osc_model.py", "h031", {"report": ("3fcde046", "d6ac"), "f32": ("2be562d2", "406f")}),
    ("H033", "H033_chorus_model.py", "h033", {"report": ("09032fa8", "6052"), "json": ("a04fce64", "c286"), "f32": ("ef54794e", "ce3d")}),
    ("H034", "H034_flanger_model.py", "h034", {"report": ("a9713642", "c019"), "json": ("861a3234", "913b"), "f32": ("b00781e5", "be46")}),
    ("H035", "H035_distortion_model.py", "h035", {"report": ("29a5598b", "b95b"), "json": ("7c0b94bc", "4c00"), "f32": ("c2ad7973", "82f0")}),
    ("H039", "H039_insert_delay_model.py", "h039", {"report": ("bde7d958", "43ca"), "json": ("dc699809", "893c"), "f32": ("cba3fdab", "4632")}),
    ("H040", "H040_compressor_model.py", "h040", {"report": ("88ae0286", "f8ba"), "json": ("c1581413", "4299"), "f32": ("716e131c", "f893")}),
    ("H041", "H041_ducker_model.py", "h041", {"report": ("5f54333e", "ca79"), "json": ("f8656fcd", "bbe5"), "f32": ("01334f1c", "7b58")}),
]


def regress(out):
    import subprocess, glob
    procs = []
    for hid, script, pre, exp in REGRESS:
        d = os.path.join(out, "regress", hid); os.makedirs(d, exist_ok=True)
        lg = open(os.path.join(out, "regress", hid + ".log"), "w")
        procs.append((hid, pre, exp, d, subprocess.Popen([sys.executable, "-B", os.path.join(HERE, script), "--out", d],
                                                        stdout=lg, stderr=subprocess.STDOUT, cwd=os.path.dirname(HERE))))
    lines = []; ok_all = True
    for hid, pre, exp, d, p in procs:
        rc = p.wait(); got = {}
        rp = os.path.join(d, pre + "_report.txt"); jp = os.path.join(d, pre + ".json")
        if os.path.exists(rp): got["report"] = sha(open(rp, "rb").read())
        if os.path.exists(jp): got["json"] = sha(open(jp, "rb").read())
        fs_ = sorted(glob.glob(os.path.join(d, "*.f32")))
        got["f32"] = sha(b"".join(open(f_, "rb").read() for f_ in fs_))
        ok = all(k_ in got and got[k_].startswith(v[0]) and got[k_].endswith(v[1]) for k_, v in exp.items())
        ok_all &= ok
        lines.append("%s rc %d  %s  %s" % (hid, rc, "OK " if ok else "BAD", "  ".join("%s %s…%s" % (k_, got.get(k_, "-")[:8],
                                                                                         got.get(k_, "-")[-4:]) for k_ in exp)))
    txt = "\n".join(lines) + "\nREGRESSION: %s\n" % ("all recorded hashes reproduced" if ok_all else "MISMATCH")
    open(os.path.join(out, "h009_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok_all else 1


def new_emu():
    return emu.Emu(insn_limit=50_000_000)


# =========================================================================================================================
import random                                                  # noqa: E402


def sig(kind, b, ch, rng):
    """64-sample block b of a test signal (lists of floats, already float32-representable)."""
    out = []
    for i in range(N):
        t = b * N + i
        if kind == "impulse":
            v = 1.0 if (t % 1000 == 7 + 3 * ch) else 0.0
        elif kind == "sine":
            v = 0.7 * math.sin(2 * math.pi * (220.0 + 110 * ch) * t / 44100.0)
        elif kind == "noise":
            v = rng.uniform(-1.0, 1.0)
        elif kind == "steps":
            v = [0.0, 1.0, -0.5, 0.25, 2.0, -1.0][(t // 150) % 6] * (1.0 if ch == 0 else -0.75)
        elif kind == "dc":
            v = 1.0
        elif kind == "denorm":
            v = [3e-39, -1e-40, 1e-38, 0.5, -7e-39][(t + ch) % 5]
        else:
            raise KeyError(kind)
        out.append(M.F(v))
    return out


def fx_shape(l, r):                    # harness-only stand-in insert effect (nonlinear, so its position is observable)
    return [M.F(M.F(x * 0.5) + 0.125) for x in l], [M.F(x * x) for x in r]


def fx_clip(l, r):
    return [max(-0.3, min(0.3, x)) for x in l], [max(-0.3, min(0.3, x)) for x in r]


def bits(xs): return [f2u(x) for x in xs]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H009"))
    ap.add_argument("--regress", action="store_true", help="only re-run H021..H041 and compare their recorded hashes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []; f32 = {}
    def P(s_=""): rep.append(s_); print(s_, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)

    P("H009 track mixing — target sha256 %s" % emu.SHA)
    im = sp16img.Image()
    def ins(a_):
        return ["%s %s" % (i_.mnemonic, i_.op_str) for i_ in im.md.disasm(im.data[im.off(a_):im.off(a_) + 4], a_)][0]
    def rtti(vt_):
        return im.cstr(im.u32(im.u32(vt_ - 4) + 4), 60)

    # ====================================================================================================== C1 static
    P("\n== C1 per-track chain — static")
    sites = {
        # HexaTrackAudioSystem 0x1bc7c8: new(0x568) MultiTrackUnit; for each track constructTrack + addTrack
        0x1bc7e8: "bl #0x1c67e4", 0x1bc808: "bl #0x1bacec", 0x1bc880: "bl #0x1c4390",
        # constructTrack 0x1bacec
        0x1bad38: "bl #0x1cceb0", 0x1baf28: "bl #0x135da0", 0x1bb1fc: "bl #0x1c9844", 0x1bb56c: "bl #0x162f10",
        0x1bb5a0: "bl #0x15bea0", 0x1bb65c: "bl #0x1c9834", 0x1bbd7c: "mov r7, r0", 0x1bbd80: "bl #0x118b0c",
        0x1bbd98: "str r7, [sp]", 0x1bbd9c: "mov r5, r0", 0x1bbda0: "bl #0x12864c", 0x1bbf34: "add r2, r5, #0x14",
        0x1bbf38: "mov r3, r7", 0x1bbf40: "mov r1, r6", 0x1bbf44: "bl #0x1c9874",
        # TrackUnit::addInsert 0x1c9874: +0xe8[slot] = manager (dynamic_cast), +0xf4[slot] = processor
        0x1c98a0: "bl #0x110ec", 0x1c98b4: "ldr r3, [r4, #0xe8]", 0x1c98b8: "str r7, [r3, r5, lsl #2]",
        0x1c9930: "ldr r3, [r4, #0xf4]", 0x1c9934: "str r6, [r3, r5, lsl #2]",
        # setters: player (+0xc8 manager, +0xcc PlayerUnit, +0xd8), LFO (+0xd0/+0xd4), MIDI (+0xe0/+0xe4)
        0x1c9834: "str r1, [r0, #0xc8]", 0x1c9838: "str r3, [r0, #0xcc]", 0x1c983c: "str r2, [r0, #0xd8]",
        0x1c9850: "vstr d16, [r0, #0xd0]", 0x1c9868: "vstr d16, [r0, #0xe0]",
        # TrackUnit ctor 0x1cceb0: member objects
        0x1cd168: "bl #0x5f9e90", 0x1cd29c: "bl #0xe97e0", 0x1cd2b0: "str r5, [r4, #0x128]", 0x1cd2d8: "bl #0xe7ec8",
        0x1cd2ec: "str r5, [r4, #0x12c]", 0x1cd30c: "bl #0xe9e5c", 0x1cd320: "str r5, [r4, #0x134]", 0x1cd340: "bl #0xe9f10",
        0x1cd354: "str r5, [r4, #0x138]", 0x1cd390: "bl #0xe5748", 0x1cd3a4: "str r5, [r4, #0x13c]", 0x1cd4bc: "bl #0xe7ec8",
        0x1cd4d0: "str r5, [r4, #0x130]", 0x1cd4f0: "bl #0x170408", 0x1cd504: "str r5, [r4, #0x108]",
        0x1cd18c: "bl #0xe6ee4", 0x1cd1a0: "str r5, [r4, #0x10c]", 0x1cd3dc: "bl #0x1c3b70", 0x1cd3f0: "str r6, [r4, #0x11c]",
        0x1cd42c: "bl #0x1c3b70", 0x1cd440: "str r6, [r4, #0x120]", 0x1cd47c: "bl #0x1c3b70", 0x1cd490: "str r6, [r4, #0x124]",
        # member ctors: Pan(ramp) / Volume(index, ramp)
        0xe9804: "ldr r2, [pc, #0xa8]", 0xe982c: "str r3, [r4, #0x90]", 0xe9854: "bl #0xe8900", 0xe9858: "str r7, [r4, #0x88]",
        0xe9874: "str r7, [r4, #0x8c]", 0xe9d64: "str r6, [r4, #0x8c]", 0xe9da4: "str r6, [r4, #0x88]",
        0xe9e5c: "mov r1, #0x64", 0xe9e64: "mov r2, r1", 0xe9f14: "mov r1, #0", 0xe9f18: "mov r2, #0x64",
        0xe7ef0: "str r6, [r4, #0x84]",
        # IVolume / IPan setters only store fields (no device/control write): Volume slot 2/3, Pan slot 2/3
        0xe86e0: "str r1, [r0, #0x8c]", 0xe86e4: "bx lr", 0xe86f4: "add r0, r0, #0x8c", 0xe8700: "vst1.32 {d16}, [r0]",
        0xe98cc: "str r1, [r0, #0x90]", 0xe98d0: "bx lr", 0xe98e0: "vstr d16, [r0, #0x90]",
        # TrackUnit::processBlock: clears its graph buffer, refers ch0/1 -> +0x43c, 2/3 -> +0x4d4, 4/5 -> +0x56c
        0x1ca5bc: "bl #0x5775c8",
        # SimpleTwoMixUnit::processBlock / ctor
        0x15364c: "bl #0x577b74", 0x153674: "bl #0x577b74", 0x1536cc: "bl #0x5778f8", 0x1538a8: "strb r4, [r6, #0x90]",
        # MultiTrackUnit ctor: 6 in / 16 out, +0x90 = 2(N+1), mixers with normalise = 0
        0x1c6850: "mov r1, #6", 0x1c6860: "mov r1, #0x10", 0x1c6828: "add r2, r0, #1", 0x1c6838: "lsl r2, r2, #1",
        0x1c6ce4: "ldr r1, [r4, #0x90]", 0x1c6ce8: "mov r2, #0", 0x1c6cf0: "bl #0x153844", 0x1c6d04: "str r5, [r4, #0xe8]",
        0x1c6d20: "ldr r1, [r4, #0x90]", 0x1c6d24: "mov r2, #0", 0x1c6d2c: "bl #0x153844", 0x1c6d40: "str r5, [r4, #0xec]",
        0x1c6cb4: "bl #0x1b4cf4", 0x1c6d64: "bl #0xc7b94",
    }
    bad = {hex(k_): (ins(k_), v) for k_, v in sites.items() if ins(k_) != v}
    P("  %d instruction assertions (MultiTrackUnit build 0x1bc7c8, constructTrack 0x1bacec, addInsert 0x1c9874, setters, TrackUnit "
      "ctor 0x1cceb0, Pan/Volume/Mute ctors, SimpleTwoMixUnit, MultiTrackUnit ctor): %s" % (len(sites), "all match" if not bad else bad))
    J["c1_static_bad"] = bad
    vts = {"TrackUnit": (0x864cac, 5, 0x1ca58c), "MultiTrackUnit": (0x864570, 5, 0x1c4ff8), "Pan(IAudioProcessor@+8)": (VT_PAN2, 5, 0xe958c),
           "VolumeFader(IAudioProcessor@+8)": (VT_FADER2, 5, 0xe9b68), "VolumeKnob(IAudioProcessor@+8)": (VT_KNOB2, 5, 0xe9b68),
           "Mute": (VT_MUTE, 5, 0xe7d80), "SimpleTwoMixUnit": (VT_STMU, 5, STMU_PB), "VolumeFader slot13": (VT_FADER, 13, 0xe9e48),
           "VolumeKnob slot13": (VT_KNOB, 13, 0xe9f08), "Volume slot3": (VT_FADER, 3, 0xe86f0), "Pan(IPan) slot3": (VT_PAN, 3, 0xe98d4)}
    vt_bad = {k_: hex(im.u32(v[0] + 4 * v[1])) for k_, v in vts.items() if im.u32(v[0] + 4 * v[1]) != v[2]}
    names = {k_: rtti(v[0]) for k_, v in vts.items()}
    P("  vtable slots: %s; RTTI names: %s" % ("all match" if not vt_bad else vt_bad, sorted(set(names.values()))))
    check(not bad and not vt_bad,
          "static chain: HexaTrackAudioSystem 0x1bc7c8 builds MultiTrackUnit and one TrackUnit per track (constructTrack 0x1bacec); "
          "TrackUnit owns PlayerUnit (+0xcc), LfoProcessor (+0xd4), insert managers/processors (+0xe8[]/+0xf4[] via 0x1c9874, "
          "InsertFxProcessor ctor 0x118b0c), OutputSelector x4 (+0x10c..+0x118), Pan (+0x128, ramp 100), Mute (+0x12c, +0x130), "
          "VolumeFader (+0x134, index 100, ramp 100), VolumeKnob (+0x138, index 0, ramp 100), LevelMeter (+0x13c), AudioRenderer (+0x108)")

    # ====================================================================================================== C1 dynamic
    P("\n== C1 per-track chain — emulated real TrackUnit::processBlock 0x1ca58c")
    e = new_emu(); fk = Fakes(e)
    rng = random.Random(9)
    src = (sig("noise", 0, 0, rng), sig("noise", 0, 1, rng))
    t = TrackRig(e, fk, n_inserts=2, src=src, insert_fx=[fx_shape, fx_clip])
    out = t.block()
    g = t.graph.ptrs
    names_ = {g[0]: "graph0", g[1]: "graph1", g[2]: "graph2", g[3]: "graph3", g[4]: "graph4", g[5]: "graph5"}
    for k_, x in enumerate(t.ext[0].ptrs): names_[x] = "ext604.%d" % k_
    for k_, x in enumerate(t.ext[1].ptrs): names_[x] = "ext608.%d" % k_
    seq = []
    for tag, buf, ch in t.events:
        seq.append("%s%s" % (tag, (" [" + ",".join(names_.get(c_, hex(c_)) for c_ in ch) + "]") if isinstance(ch, list) else ""))
    for s_ in seq: P("    " + s_)
    J["c1_sequence"] = seq
    expect = ["0x1ca3c8 mute update (skipped; harness sets Mute+0x84)", "lfo(+0xd4).process", "player(+0xcc).process [graph0,graph1]",
              "OutputSelector(+0x10c).process [graph0,graph1,ext604.0,ext604.1]",
              "OutputSelector(+0x110).process [graph0,graph1,ext608.0,ext608.1]",
              "InsertFxParameterManager[0] vt+0x28", "InsertFxProcessor[0].process [graph0,graph1]",
              "InsertFxParameterManager[1] vt+0x28", "InsertFxProcessor[1].process [graph0,graph1]",
              "OutputSelector(+0x118).process [graph4,graph5,graph0,graph1]", "Mute.process (0xe7d80) Mute#2(+0x130) [graph4,graph5]",
              "OutputSelector(+0x114).process [graph0,graph1,ext608.0,ext608.1]", "Pan.process (0xe9594) Pan [graph0,graph1]",
              "Mute.process (0xe7d80) Mute#1(+0x12c) [graph0,graph1]", "Volume.process (0xe9b70) VolumeKnob [graph2,graph3]",
              "Volume.process (0xe9b70) VolumeFader [graph0,graph1]", "LevelMeter(+0x13c).process [graph0,graph1]",
              "AudioRenderer(+0x108).process", "MidiTrackOutputFormatter(+0xe4).process"]
    check(seq == expect, "real TrackUnit::processBlock order: player -> [OutputSelector +0x10c] -> copy main->ch4/5 -> [+0x110] -> "
          "insert slot 0 (manager vt+0x28, processor vt+0x14) -> insert slot 1 -> [+0x118 on ch4/5+main] -> Mute#2(ch4/5) -> [+0x114] "
          "-> Pan(main) -> Mute#1(main) -> copy main->ch2/3 -> VolumeKnob(ch2/3) -> VolumeFader(main) -> meter -> renderer -> MIDI")
    # taps: run a model with the same fakes and compare all 6 channels of this first block
    mt = M.Track(main_on=True, pre_on=False)
    mo = mt.process(src[0], src[1], inserts=[fx_shape, fx_clip])
    same = all(bits(out[k_]) == bits(mo[k_]) for k_ in range(6))
    check(same, "first block (2 nonlinear stand-in inserts, mute fade-in, send ramp 1.0->0): all 6 track channels equal to the model "
          "(ch0/1 main, ch2/3 send tap, ch4/5 pre-insert tap)")
    J["c1_tap_equal"] = same

    # ====================================================================================================== C2 volume law
    P("\n== C2 volume law")
    tab = [u2f(im.u32(0x83e050 + 4 * k_)) for k_ in range(128)]
    tdiff = [k_ for k_ in range(128) if f2u(tab[k_]) != f2u(M.VOLUME_TABLE[k_])]
    P("  table 0x83e050 (128 floats) vs model formula: %d differ %s" % (len(tdiff), tdiff[:10]))
    P("  excerpt: " + ", ".join("%d:%.6g (%s dB)" % (k_, tab[k_], ("%.2f" % (20 * math.log10(tab[k_]))) if tab[k_] else "-inf")
                                 for k_ in (0, 1, 2, 9, 10, 25, 50, 71, 100, 101, 110, 127)))
    rng_lit = (struct.unpack("<ii", im.data[im.off(0xe9b28):im.off(0xe9b28) + 8]), struct.unpack("<ii", im.data[im.off(0x348788):im.off(0x348788) + 8]))
    P("  ranges: Volume slot 5 {%d, %d} -> parameter clamp [0, 127]; Pan slot 5 {%d, %d} -> [-64, 64]" % (rng_lit[0] + rng_lit[1]))
    check(not tdiff and rng_lit == ((0, 128), (-64, 65)), "volume table = 0 | -54,-50,-48,-46,-45,-44,-43,-42,-41 dB | (i/100)^2 for "
          "10..100 | 2^(ln(i/100)/ln 1.27) for 101..127 (index 100 = 0 dB, 127 = +6.02 dB); bit-exact for all 128 entries")
    # read-back through the real chain (DC input, pan 0, main on)
    e2 = new_emu(); fk2 = Fakes(e2)
    t2 = TrackRig(e2, fk2, n_inserts=0)
    t2.main_on = 1
    rb = []
    for idx in (0, 1, 5, 9, 10, 11, 50, 71, 99, 100, 101, 110, 126, 127):
        t2.set(fader=idx, send=idx)
        for _ in range(5):
            t2.src = (sig("dc", 0, 0, None), sig("dc", 0, 1, None)); o = t2.block()
        rb.append((idx, o[0][-1], o[1][-1], o[2][-1], o[3][-1]))
    rb_bad = [r_ for r_ in rb if not (f2u(r_[1]) == f2u(r_[2]) == f2u(M.fader_gain(r_[0])) and f2u(r_[3]) == f2u(r_[4]) == f2u(M.knob_gain(r_[0])))]
    for r_ in rb: P("    index %3d: fader gain %.9g  send (VolumeKnob) gain %.9g" % (r_[0], r_[1], r_[3]))
    J["c2_readback"] = rb
    check(not rb_bad, "read-back (real chain, 14 indices incl. 0 and 127): main = table[i] (VolumeFader), send = table[i]*0.5 "
          "(VolumeKnob: 127 -> 1.0, 100 -> 0.5 = -6.02 dB), L and R identical")
    # ramp: 100-sample linear ramp, starts at the parameter's sample offset
    t2.set(fader=100, send=127)
    for _ in range(4): t2.block()
    t2.set(fader=50, offset=0); o1 = t2.block(); o2 = t2.block()
    tr = o1[0] + o2[0]
    first_t = next((k_ for k_, v in enumerate(tr) if f2u(v) == f2u(M.fader_gain(50))), -1)
    lin = all(abs(tr[k_] - (1.0 + k_ * (0.25 - 1.0) / 100)) < 2e-6 for k_ in range(100))
    t2.set(fader=127, offset=30); o3 = t2.block(); o4 = t2.block(); o5 = t2.block(); tr2 = o3[0] + o4[0] + o5[0]
    start2 = next((k_ for k_, v in enumerate(tr2) if f2u(v) != f2u(M.fader_gain(50))), -1)
    end2 = next((k_ for k_, v in enumerate(tr2) if f2u(v) == f2u(M.fader_gain(127))), -1)
    P("  ramp 100 -> 50 at offset 0: first sample at target = %d; linear within 2e-6: %s; ramp 50 -> 127 at offset 30: first "
      "changed sample %d, first sample at target %d" % (first_t, lin, start2, end2))
    J["c2_ramp"] = (first_t, lin, start2, end2)
    check(first_t == 100 and lin and start2 == 31 and end2 == 130,
          "smoothing: per-sample linear ramp of exactly 100 samples (step = (target - current)/100, gain applied before the "
          "increment), crossing block boundaries, delayed by the parameter's sample offset (+0x10)")

    # ====================================================================================================== C3 pan law
    P("\n== C3 pan law")
    e3 = new_emu(); fk3 = Fakes(e3)
    t3 = TrackRig(e3, fk3, n_inserts=0); t3.main_on = 1
    t3.set(fader=100, send=127)
    pr = []
    for p_ in (-64, -63, -48, -32, -16, -1, 0, 1, 16, 32, 48, 63, 64):
        t3.set(pan=p_)
        for _ in range(5):
            t3.src = (sig("dc", 0, 0, None), sig("dc", 0, 1, None)); o = t3.block()
        pr.append((p_, o[0][-1], o[1][-1]))
    pbad = [r_ for r_ in pr if (f2u(r_[1]), f2u(r_[2])) != tuple(f2u(x) for x in M.pan_gains(r_[0]))]
    for r_ in pr: P("    pan %+3d: L %.9g (%s dB)  R %.9g (%s dB)" % (r_[0], r_[1], ("%.2f" % (20 * math.log10(r_[1]))) if r_[1] else "-inf",
                                                                  r_[2], ("%.2f" % (20 * math.log10(r_[2]))) if r_[2] else "-inf"))
    J["c3_pan"] = pr
    check(not pbad, "pan read-back (13 values incl. -64/0/+64): linear balance — p<0: L 1, R (64+p)/64; p>0: L (64-p)/64, R 1; "
          "centre both 1.0 (0 dB, no centre attenuation)")
    # no cross-feed: L-only source at hard right / hard left
    t3.set(pan=64)
    for _ in range(4):
        t3.src = (sig("dc", 0, 0, None), [0.0] * N); o = t3.block()
    xf1 = (o[0][-1], o[1][-1])
    t3.set(pan=-64)
    for _ in range(4):
        t3.src = (sig("dc", 0, 0, None), [0.0] * N); o = t3.block()
    xf2 = (o[0][-1], o[1][-1])
    P("  L-only source: pan +64 -> (L, R) = %s; pan -64 -> %s" % (xf1, xf2))
    check(xf1 == (0.0, 0.0) and xf2 == (1.0, 0.0), "no cross-feed: hard right silences an L-only source instead of moving it "
          "(balance control, stereo source assumed; a mono sample must already be on both channels)")
    # clamp through the parameter struct (modulation path) and the unclamped direct value
    e3.wr(t3.ps_pan + 1, b"\x01"); e3.w32(t3.ps_pan + 0xc, 100); e3.w32(t3.ps_pan + 4, 0)
    for _ in range(4):
        t3.src = (sig("dc", 0, 0, None), sig("dc", 0, 1, None)); o = t3.block()
    cl1 = (o[0][-1], o[1][-1])
    e3.wr(t3.ps_pan + 1, b"\x00"); e3.w32(t3.ps_pan + 0xc, 0); t3.set(pan=72)
    for _ in range(4):
        t3.src = (sig("dc", 0, 0, None), sig("dc", 0, 1, None)); o = t3.block()
    cl2 = (o[0][-1], o[1][-1])
    P("  modulation on, value 0 + mod 100 -> clamped to +64: (L, R) = %s; direct value +72 (no clamp in Pan): %s" % (cl1, cl2))
    check(cl1 == (0.0, 1.0) and cl2 == (M.F(-8 / 64), 1.0),
          "range: parameter struct clamps value+mod to [-64, 64] only when its modulation byte (+1) is set; Pan itself does not clamp")
    # pan ramp shape
    t3.set(pan=0)
    for _ in range(4): t3.block()
    t3.set(pan=-64, offset=10); o1 = t3.block(); o2 = t3.block(); trr = o1[1] + o2[1]
    st = next((k_ for k_, v in enumerate(trr) if v != 1.0), -1); en = next((k_ for k_, v in enumerate(trr) if v == 0.0), -1)
    P("  pan 0 -> -64 at offset 10: R starts moving at sample %d, reaches 0 at sample %d" % (st, en))
    check(st == 11 and en == 110, "pan smoothing: separate L and R gain smoothers, 100-sample linear ramp from the offset")

    # ====================================================================================================== C4 summing
    P("\n== C4 bus summing and channel layout")
    e4 = new_emu(); fk4 = Fakes(e4)
    NT = 4
    trs = [TrackRig(e4, fk4, name="T%d" % k_, n_inserts=1, insert_fx=[fx_shape]) for k_ in range(NT)]
    for k_, tt in enumerate(trs): tt.main_on = 1; tt.pre_on = 1 if k_ == 2 else 0
    trs[0].set(fader=100, pan=0, send=127); trs[1].set(fader=80, pan=-20, send=64); trs[2].set(fader=120, pan=40, send=0)
    trs[3].set(fader=0, pan=64, send=100)
    MTU = e4.malloc(0x560, "MultiTrackUnit stand-in"); e4.wr(MTU, b"\0" * 0x560)
    out16 = AudioBuf(e4, 16)
    e4.w32(MTU + 0x84, NT)
    arr = e4.malloc(4 * NT, "track bufs"); [e4.w32(arr + 4 * k_, trs[k_].graph.obj) for k_ in range(NT)]
    e4.w32(MTU + 0xa8, arr); e4.w32(MTU + 0xb0, NT)
    for off, nch, parr in ((0x2c8, 2 * NT + 2, 0x534), (0x360, 2 * NT + 2, 0x538), (0x3f8, 2 * NT + 8, 0x53c), (0x490, 2 * NT + 2, 0x540)):
        e4.call(AB_CTOR, MTU + off); e4.w32(MTU + off, nch)
        pa = e4.malloc(4 * nch, "chan ptr array"); e4.w32(MTU + parr, pa)
    for nm, fn in MTU_ROUTE.items(): e4.call(fn, MTU, out16.obj, N)
    gname = {p_: "out%d" % k_ for k_, p_ in enumerate(out16.ptrs)}
    for k_, tt in enumerate(trs):
        for c_, p_ in enumerate(tt.graph.ptrs): gname[p_] = "T%d.ch%d" % (k_, c_)
    lay = {}
    for nm, off in (("main 0x1c4448 -> +0x2c8", 0x2c8), ("send 0x1c4668 -> +0x360", 0x360), ("assign 0x1c4888 -> +0x3f8", 0x3f8),
                    ("dsf 0x1c4dd8 -> +0x490", 0x490)):
        n_ = e4.u32(MTU + off); ca = e4.u32(MTU + off + 0xc)
        lay[nm] = [gname.get(e4.u32(ca + 4 * i_), hex(e4.u32(ca + 4 * i_))) for i_ in range(n_)]
        P("  %s: %s" % (nm, lay[nm]))
    J["c4_layout"] = lay
    exp_main = ["out0", "out1"] + sum([["T%d.ch0" % k_, "T%d.ch1" % k_] for k_ in range(NT)], [])
    exp_send = ["out2", "out3"] + sum([["T%d.ch2" % k_, "T%d.ch3" % k_] for k_ in range(NT)], [])
    exp_as = sum([["T%d.ch0" % k_, "T%d.ch1" % k_] for k_ in range(NT)], []) + ["out%d" % k_ for k_ in range(6, 14)]
    exp_dsf = ["out4", "out5"] + sum([["T%d.ch4" % k_, "T%d.ch5" % k_] for k_ in range(NT)], [])
    check(lay["main 0x1c4448 -> +0x2c8"] == exp_main and lay["send 0x1c4668 -> +0x360"] == exp_send and
          lay["assign 0x1c4888 -> +0x3f8"] == exp_as and lay["dsf 0x1c4dd8 -> +0x490"] == exp_dsf,
          "routing builders (real code): mixer A = [out0/1 + every track ch0/1], mixer B = [out2/3 + every track ch2/3], "
          "AssignableUnit = [every track ch0/1 + out6..13], DsfSendOutputSelector = [out4/5 + every track ch4/5]")

    def stmu(normalise=False):
        o_ = e4.malloc(0xa0, "SimpleTwoMixUnit stand-in"); e4.wr(o_, b"\0" * 0xa0)
        nch = 2 * NT + 2
        e4.w32(o_, VT_STMU); e4.w32(o_ + 0x80, nch); e4.w32(o_ + 0x84, 2); e4.w32(o_ + 0x88, 0); e4.w32(o_ + 0x8c, 1)
        e4.wr(o_ + 0x90, b"\x01" if normalise else b"\x00"); e4.w32(o_ + 0x94, f2u(M.F(1.0 / (nch >> 1)) if normalise else 1.0))
        tmpb = e4.malloc(0x98, "AudioBuffer"); e4.call(AB_CTOR, tmpb); e4.w32(o_ + 0x98, tmpb)
        return o_
    mixA, mixB, mixN = stmu(), stmu(), stmu(True)
    models = [M.Track(fader=100, pan=0, send=127), M.Track(fader=80, pan=-20, send=64), M.Track(fader=120, pan=40, send=0, pre_on=True),
              M.Track(fader=0, pan=64, send=100)]
    rng4 = random.Random(44); sum_bad = 0; sums = []
    kinds = ["noise", "sine", "steps", "impulse"]
    for b in range(60):
        if b == 30:
            trs[1].set(fader=127, offset=5); models[1].set(fader=127, offset=5)
            trs[3].set(fader=100, pan=-64, offset=0); models[3].set(fader=100, pan=-64)
        touts = []; mouts = []
        for k_, tt in enumerate(trs):
            sl = sig(kinds[k_], b, 0, rng4); sr = sig(kinds[k_], b, 1, rng4)
            tt.src = (sl, sr); touts.append(tt.block())
            mouts.append(models[k_].process(sl, sr, inserts=[fx_shape]))
            sum_bad += sum(bits(touts[-1][c_]) != bits(mouts[-1][c_]) for c_ in range(6))
        for c_ in range(16): out16.write(c_, [0.0] * N)
        e4.wr(out16.obj + 0x94, b"\x00")
        for nm, fn in MTU_ROUTE.items(): e4.call(fn, MTU, out16.obj, N)
        e4.call(STMU_PB, mixA, MTU + 0x2c8, 0); e4.call(STMU_PB, mixB, MTU + 0x360, 0)
        bus = [out16.read(c_) for c_ in range(4)]
        ml = M.sum_tracks(mouts, (0, 1)); ms = M.sum_tracks(mouts, (2, 3))
        if [bits(x) for x in bus] != [bits(ml[0]), bits(ml[1]), bits(ms[0]), bits(ms[1])]: sum_bad += 1
        sums.append(bus)
        f32.setdefault("c4_bus", []).extend(bus[0] + bus[1] + bus[2] + bus[3])
    P("  60 blocks, 4 tracks (noise/sine/steps/impulse, different fader/pan/send, mid-run changes): per-track channel blocks and "
      "bus blocks not bit-equal to the model: %d" % sum_bad)
    # normalised variant (not used by MultiTrackUnit, flag 0) for comparison
    for c_ in range(16): out16.write(c_, [0.0] * N)
    for nm, fn in MTU_ROUTE.items(): e4.call(fn, MTU, out16.obj, N)
    e4.call(STMU_PB, mixN, MTU + 0x2c8, 0)
    nb = out16.read(0)
    mn = M.sum_tracks(mouts, (0, 1), normalise=True)[0]
    P("  normalise flag set (+0x90 = 1, not used by MultiTrackUnit): bus = sum x 1/(N+1): model match %s" % (bits(nb) == bits(mn)))
    check(sum_bad == 0 and bits(nb) == bits(mn),
          "summing (real SimpleTwoMixUnit 0x1535f8 on the real routing): out0/1 = sum of track ch0/1, out2/3 = sum of track ch2/3, "
          "float accumulate in track order with gain 1.0 and no headroom scaling (normalise flag 0 in MultiTrackUnit ctor)")
    J["c4_sum_bad"] = sum_bad

    # graph side: which MultiTrackUnit outputs reach CompositeFxUnit (Master FX / Send FX)
    stat = {a_: (e4.u32(a_), e4.u32(a_ + 4)) for a_ in (0xf53c44, 0xf53c50, 0xf53ca8, 0xf53c8c)}
    CF = e4.malloc(0x200, "CompositeFxUnit stand-in"); e4.wr(CF, b"\0" * 0x200)
    e4.call(AB_CTOR, CF + 0xa4); e4.call(AB_CTOR, CF + 0x13c)
    cf_log = {}
    for off, tag in ((0x8c, "MasterFxUnit"), (0x90, "SendFxUnit")):
        e4.w32(CF + off, fk4.obj("cf." + tag, {0x14: lambda em, nm, tag=tag: cf_log.__setitem__(
            tag, (em.r(1), [em.u32(em.u32(em.r(1) + 0xc) + 4 * i_) for i_ in range(em.u32(em.r(1)))]))}))
    cfbuf = AudioBuf(e4, 4)
    e4.call(0x1a94cc, CF, cfbuf.obj)
    stat.update({a_: (e4.u32(a_), e4.u32(a_ + 4)) for a_ in (0xf53868, 0xf53874)})
    cfn = {p_: "in%d" % k_ for k_, p_ in enumerate(cfbuf.ptrs)}
    cf_seen = {k_: (hex(v[0] - CF), [cfn.get(c_, hex(c_)) for c_ in v[1]]) for k_, v in cf_log.items()}
    P("  CompositeFxUnit::processBlock 0x1a94cc (real, stand-in units): %s" % cf_seen)
    P("  channel-pair statics after the real code ran: %s" % {hex(k_): v for k_, v in stat.items()})
    def lit(a_):
        i_ = list(im.md.disasm(im.data[im.off(a_):im.off(a_) + 4], a_))[0]
        return im.u32(a_ + 8 + int(i_.op_str.split("#")[1].rstrip("]"), 0))
    gsites = {0x1bda4c: ("lit", 0x864364), 0x1bda68: "bl #0x1b6020", 0x1bda70: "str r0, [r7, #0x74c]", 0x1bdec0: ("lit", 0x86438c),
              0x1bded8: "str r0, [sp, #0x38]", 0x1be394: "ldr r2, [r7, #0x74c]", 0x1be39c: "ldr r4, [r2, #8]",
              0x1be3ac: "ldr ip, [sp, #0x38]", 0x1be3b4: "ldr r5, [ip, #8]", 0x1be3c0: ("lit", 0xf53868), 0x1be3d4: ("lit", 0xf53c44),
              0x1be3d8: "mov r3, r5", 0x1be3e8: "mov r1, r4", 0x1be3ec: "bl #0x1b61bc", 0x1be3f4: "ldr r2, [r7, #0x74c]",
              0x1be420: ("lit", 0xf53874), 0x1be430: ("lit", 0xf53c50), 0x1be448: "bl #0x1b61bc", 0x1b61d4: ("lit", 0x863870)}
    gbad = {hex(k_): v for k_, v in gsites.items() if (lit(k_) != v[1] if isinstance(v, tuple) else ins(k_) != v)}
    P("  graph build 0x1bc8d4: %d assertions (node 'multiTrackUnitNode' -> sys+0x74c, 'compositeFxUnitNode' -> sp+0x38, two "
      "'add connection' calls 0x1b61bc with pair statics): %s" % (len(gsites), "all match" if not gbad else gbad))
    check(not gbad and stat[0xf53c44] == (0, 1) and stat[0xf53c50] == (2, 3) and stat[0xf53868] == (0, 1) and stat[0xf53874] == (2, 3)
          and cf_seen.get("MasterFxUnit") == ("0xa4", ["in0", "in1"]) and cf_seen.get("SendFxUnit") == ("0x13c", ["in2", "in3"]),
          "graph: MultiTrackUnit out 0/1 (track-sum) -> CompositeFxUnit in 0/1 -> MasterFxUnit; out 2/3 (send-sum) -> in 2/3 -> "
          "SendFxUnit")
    J["c4_graph"] = {"statics": {hex(k_): v for k_, v in stat.items()}, "composite": cf_seen}

    # ====================================================================================================== C5 / C7 static
    P("\n== C5/C7 parameter path (static)")
    psites = {0x1c8b00: "ldr r3, [r4, #0x120]", 0x1c8b20: "str r2, [r3, #4]", 0x1c8b28: "str sb, [r3, #0x10]",
              0x1c8b2c: "strb r2, [r3]", 0x1c8328: "cmp r2, #0xe", 0x1c8330: "cmp r2, #0xf", 0x1c8338: "cmp r2, #0xd",
              0x1c8340: "ldr r2, [r0, #0x120]", 0x1c8364: "str r0, [r2, #8]", 0x1c8368: "str r1, [r2, #0x10]",
              0x1c836c: "strb r3, [r2]", 0x1c8374: "ldr r2, [r0, #0x124]", 0x1c839c: "ldr r2, [r0, #0x11c]",
              0x1c7ab0: "str ip, [r5, #0xc]", 0x1c7ab4: "strb ip, [r5, #1]", 0x1c7a78: "strb r3, [ip]",
              0x1c799c: "ldr r3, [r0, #0x120]", 0x1c79a0: "ldr r0, [r3, #4]",
              0x17f2ec: "str r0, [r5, #0x30]", 0x17f1ec: "str r0, [r5, #0x34]"}
    pbad_ = {hex(k_): (ins(k_), v) for k_, v in psites.items() if ins(k_) != v}
    tslots = {66: 0x1c8988, 67: 0x1c87bc, 68: 0x1c8b54, 69: 0x1c799c, 70: 0x1c79b0, 71: 0x1c79c4, 72: 0x1c79d8, 77: 0x1c7a68,
              78: 0x1c8328, 79: 0x1c7a90}
    tvt = {k_: im.u32(0x864cac + 4 * k_) for k_ in tslots}
    P("  TrackUnit vtable 0x864cac slots %s" % {k_: hex(v) for k_, v in tvt.items()})
    P("  %d assertions: slot 66 setVolume(value, offset) -> +0x120: value +4 = clamp(v, min, max), offset +0x10, useAlt byte +0 = 0; "
      "slot 78 (receiver) ids 13/14/15 -> volume(+0x120)/pan(+0x11c)/send(+0x124) alt +8 = clamp, offset, useAlt = 1; slot 79 (LFO listener) clears mod "
      "+0xc / modOn +1; slot 77 clears useAlt; slot 69 returns volume +4; TrackData 'volume' fromVar -> +0x30, 'pan' -> +0x34: %s"
      % (len(psites), "all match" if not pbad_ else pbad_))
    check(not pbad_ and all(tvt[k_] == v for k_, v in tslots.items()),
          "volume / pan / send values reach the DSP only through the three parameter structs +0x120 / +0x11c / +0x124 "
          "(value, p-lock alt value, LFO modulation, sample offset), read once per block by TrackUnit::processBlock")

    # ====================================================================================================== C6 model matrix
    P("\n== C6 model vs emulation matrix")
    SETTINGS = [("unity", dict(fader=100, pan=0, send=0)), ("min", dict(fader=0, pan=0, send=127)), ("max", dict(fader=127, pan=0, send=127)),
                ("hardL", dict(fader=100, pan=-64, send=100)), ("hardR", dict(fader=90, pan=64, send=50)),
                ("mid", dict(fader=71, pan=-23, send=88)), ("low", dict(fader=3, pan=17, send=5))]
    CHANGES = {12: dict(fader=40, offset=0), 20: dict(pan=33, offset=17), 27: dict(send=127, offset=63), 33: dict(fader=127, pan=-64, offset=99),
               41: "mute", 47: "unmute", 50: "pre_on", 58: "pre_off", 61: dict(fader=100, pan=0, send=0, offset=1)}
    total = 0; mism = 0; runs = 0
    combos = [(sname, sv, kind, 1) for sname, sv in SETTINGS for kind in ("impulse", "sine", "noise", "steps", "denorm")]
    combos += [(sname, sv, kind, 0) for sname, sv in SETTINGS if sname in ("unity", "mid", "hardL") for kind in ("denorm", "noise")]
    for sname, sv, kind, nins in combos:
            em_ = new_emu(); fke = Fakes(em_)
            tt = TrackRig(em_, fke, n_inserts=nins, insert_fx=[fx_shape] if nins else []); tt.main_on = 1
            mt = M.Track(**sv); tt.set(**sv)
            rngs = random.Random(zlib.crc32((sname + kind).encode()))
            fl = []
            for b in range(70):
                ch_ = CHANGES.get(b)
                if isinstance(ch_, dict): tt.set(**ch_); mt.set(**ch_)
                elif ch_ == "mute": tt.main_on = 0; mt.main_on = False
                elif ch_ == "unmute": tt.main_on = 1; mt.main_on = True
                elif ch_ == "pre_on": tt.pre_on = 1; mt.pre_on = True
                elif ch_ == "pre_off": tt.pre_on = 0; mt.pre_on = False
                sl = sig(kind, b, 0, rngs); sr = sig(kind, b, 1, rngs)
                tt.src = (sl, sr); o = tt.block(); mo = mt.process(sl, sr, inserts=[fx_shape] if nins else [])
                for c_ in range(6):
                    total += N; mism += sum(1 for x, y in zip(bits(o[c_]), bits(mo[c_])) if x != y)
                    fl.extend(o[c_])
            f32["c6_%s_%s%s" % (sname, kind, "" if nins else "_noinsert")] = fl
            runs += 1
    P("  %d runs (7 settings x impulse/sine/noise/steps/denormal with one insert + 3 settings x denormal/noise without insert), 70 blocks x 64 frames, 9 mid-run events (fader/pan/send with "
      "offsets 0/17/63/99/1, mute, unmute, pre-tap on/off), 6 channels: %d samples compared, %d differ" % (runs, total, mism))
    J["c6"] = {"runs": runs, "samples": total, "mismatch": mism}
    check(mism == 0 and runs >= 30, "model bit-exact to the emulated real TrackUnit::processBlock on all 6 output channels")

    # ====================================================================================================== C8 mutants
    P("\n== C8 alternatives (model mutants must differ from the emulation)")
    ref = {k_: v for k_, v in f32.items() if k_.startswith("c6_mid_") or k_.startswith("c6_hardL_") or k_.startswith("c6_unity_denorm")}

    def run_model(sname, kind, track_cls=M.Track, nins=None):
        nins = 1 if nins is None else nins
        sv = dict(SETTINGS)[sname]; mt = track_cls(**sv); rngs = random.Random(zlib.crc32((sname + kind).encode())); fl = []
        for b in range(70):
            ch_ = CHANGES.get(b)
            if isinstance(ch_, dict): mt.set(**ch_)
            elif ch_ == "mute": mt.main_on = False
            elif ch_ == "unmute": mt.main_on = True
            elif ch_ == "pre_on": mt.pre_on = True
            elif ch_ == "pre_off": mt.pre_on = False
            sl = sig(kind, b, 0, rngs); sr = sig(kind, b, 1, rngs)
            o = mt.process(sl, sr, inserts=[fx_shape] if nins else [])
            for c_ in range(6): fl.extend(o[c_])
        return fl

    def nm_args(key):
        parts = key.split("_")
        return parts[1], parts[2], (0 if key.endswith("_noinsert") else 1)

    import contextlib
    @contextlib.contextmanager
    def patched(obj, name, val):
        old = getattr(obj, name); setattr(obj, name, val)
        try: yield
        finally: setattr(obj, name, old)

    class FaderFirst(M.Track):
        def process(self, l, r, inserts=()):
            self.sm_fader.set_target(M.fader_gain(self.fader), 1, self.fader_off)
            L = [M.F(x) for x in l]; R = [M.F(x) for x in r]; self.sm_fader.apply([L, R])
            self.fader = 100; o = M.Track.process(self, L, R, inserts); return o

    class SendPostFader(M.Track):
        def process(self, l, r, inserts=()):
            o = M.Track.process(self, l, r, inserts)
            s_l = o[0][:]; s_r = o[1][:]; self.sm_send.apply([s_l, s_r]); return [o[0], o[1], s_l, s_r, o[4], o[5]]

    class PrePostInsert(M.Track):
        def process(self, l, r, inserts=()):
            L, R = inserts[0]([M.F(x) for x in l], [M.F(x) for x in r]) if inserts else (l, r)
            o = M.Track.process(self, L, R, ()); return o
    mutants = [
        ("constant-power pan sin/cos (-3 dB centre)", lambda p: (M.F(math.cos((p + 64) / 128 * math.pi / 2)), M.F(math.sin((p + 64) / 128 * math.pi / 2))), "pan_gains"),
        ("sqrt pan law (-3 dB centre)", lambda p: (M.F(math.sqrt((64 - p) / 128)), M.F(math.sqrt((p + 64) / 128))), "pan_gains"),
        ("linear pan -6 dB centre", lambda p: (M.F((64 - p) / 128), M.F((p + 64) / 128)), "pan_gains"),
        ("dB-linear fader (-60..+6 dB)", lambda i: M.F(10 ** ((-60 + 66 * i / 127) / 20)) if i else 0.0, "fader_gain"),
        ("send knob without the 0.5 factor", lambda i: M.VOLUME_TABLE[i], "knob_gain"),
    ]
    mres = []
    for nm, fn, attr in mutants:
        with patched(M, attr, fn):
            d = sum(sum(1 for x, y in zip(bits(run_model(nm_args(s_)[0], nm_args(s_)[1], nins=nm_args(s_)[2])), bits(v)) if x != y) for s_, v in ref.items())
        mres.append((nm, d))
    for nm, cls in (("fader before the insert", FaderFirst), ("send tap post-fader", SendPostFader),
                    ("pre-insert tap after the insert", PrePostInsert)):
        d = sum(sum(1 for x, y in zip(bits(run_model(nm_args(s_)[0], nm_args(s_)[1], cls, nm_args(s_)[2])), bits(v)) if x != y) for s_, v in ref.items())
        mres.append((nm, d))
    with patched(M.Track, "RAMP", 64):
        d = sum(sum(1 for x, y in zip(bits(run_model(nm_args(s_)[0], nm_args(s_)[1], nins=nm_args(s_)[2])), bits(v)) if x != y) for s_, v in ref.items())
    mres.append(("ramp 64 samples instead of 100", d))
    with patched(M, "neon_mul", lambda x, g: M.F(x * g)):
        d = sum(sum(1 for x, y in zip(bits(run_model(nm_args(s_)[0], nm_args(s_)[1], nins=nm_args(s_)[2])), bits(v)) if x != y) for s_, v in ref.items())
    mres.append(("no denormal flush in the constant-gain (NEON) path", d))
    def vec_all_neon(c, pos, k, g):
        for i in range(pos, pos + k): c[i] = M.neon_mul(c[i], g)
    with patched(M, "vec_mul", vec_all_neon):
        d = sum(sum(1 for x, y in zip(bits(run_model(nm_args(s_)[0], nm_args(s_)[1], nins=nm_args(s_)[2])), bits(v)) if x != y) for s_, v in ref.items())
    mres.append(("NEON flush also on the k % 4 scalar tail", d))
    for nm, d in mres: P("    %-55s mismatched samples: %d" % (nm, d))
    J["c8_mutants"] = mres
    check(all(d > 0 for _, d in mres), "all %d alternative laws / orders / ramp lengths are refuted by the emulated output" % len(mres))

    # ====================================================================================================== outputs
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h009_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h009.json"), "w"), indent=1, sort_keys=True, default=str)
    for k_, v in f32.items():
        open(os.path.join(a.out, k_ + ".f32"), "wb").write(struct.pack("<%df" % len(v), *v))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
