#!/usr/bin/env python3
"""H055 — device output stage (AudioDeviceOutputUnit) and what drives OutputVolume, 1.60 (kb/cycles/020.md).

Sections (criteria of cycle 020):
  S   static assertions (capstone): processBlock 0x1ae3e4 call structure, ctor argument struct built by 0x1b6284, config words written by
      0x5712cc (product / test) and copied by AudioSystemBase ctor 0x1b8198 to sys+0x204, IAudioSystem::getVolume switch 0x1b93f0,
      OutputVolumeController 0x1d1308/0x1d1210/0x1d12d4, UIVolume ids, BulkMute/muteAllOutput wiring, sys+0x564 state machine.
  C1  REAL ctor 0x1ae7dc (JUCE AudioProcessor base ctor 0x5f9e00 and setPlayConfigDetails 0x5f9e90 replaced by recording stubs) and
      REAL processBlock 0x1ae3e4 on 14 distinct channels: channel mapping, stage order (watch points), per-pair chain.
  C2  OutputVolume law: REAL slot 13 0xe9914 for all 1024 indices vs the model; DC through processBlock at 7 indices; step ramp.
  C3  FixedAttenuator: emulated gains/sign per pair for the product config, the test config and an arbitrary config.
  C4  BulkMuteUnit: start-up state, mute/unmute fade law and length (REAL 0x1aeee4 / 0x1aef3c / 0x1aec8c), mid-fade reversal.
  C5  OutputVolumeController: REAL ctor 0x1d1308 with the REAL IAudioSystem getVolume path (vt 0x863f74 slot 41 -> 0x1b93f0 -> 0x1ae614)
      and REAL UIVolume objects (vt 0x931780); pot changes through the REAL listener 0x1d12d4.
  C6  base graph 0x1b6284 connections (symbolic walk), asserted against the expected table.
  C7  model harness/models/device_out.py vs emulation, >= 6 settings x {impulse, sine, noise, steps} x 60 blocks x 64 frames x 14 ch.
Outputs only to --out (default harness/out/H055/). Run: .venv/bin/python -B harness/H055_device_out.py --out DIR [--regress]
"""
import argparse, hashlib, json, math, os, random, re, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from unicorn import arm_const as A                             # noqa: E402
import sp16img                                                 # noqa: E402
from symwalk import Walker, State, U                           # noqa: E402
import H009_track_mix as h9                                    # noqa: E402  (AudioBuf, Fakes, sig, guard stubs, regress list)
import track_mix as TM                                         # noqa: E402
import device_out as DO                                        # noqa: E402

N = 64
F = TM.F
DEV_CTOR, DEV_PB, GET_VOL, GET_BULK = 0x1ae7dc, 0x1ae3e4, 0x1ae614, 0x1ae62c
VOL_SLOT13, VOL_SET, VOL_SETOFF, VOL_GET = 0xe9914, 0xe86e0, 0xe86f0, 0xe86e8
ATT_PB, BULK_PB, BULK_MUTE, BULK_UNMUTE, BULK_CTOR = 0xe87f8, 0x1aec8c, 0x1aeee4, 0x1aef3c, 0x1af1b0
OVC_CTOR, OVC_APPLY, OVC_LISTEN = 0x1d1308, 0x1d1210, 0x1d12d4
UIVOL_CTOR, VT_UIVOL, VT_ISYS = 0x55ee5c, 0x931780, 0x863f74
JUCE_AP_CTOR, JUCE_SETPLAY = 0x5f9e00, 0x5f9e90

emu.STUBS.setdefault("pthread_mutex_lock", (lambda e: e.setr(0, 0), "no-op, returns 0 (single thread)"))
emu.STUBS.setdefault("pthread_mutex_unlock", (lambda e: e.setr(0, 0), "no-op, returns 0 (single thread)"))


def sha(b): return hashlib.sha256(b).hexdigest()
def bits(xs): return [f2u(x) for x in xs]


# =========================================================================================================== rig
class Rig:
    def __init__(self):
        self.e = e = emu.Emu(insn_limit=80_000_000)
        self.fk = h9.Fakes(e)
        self.juce = []; self.log = []
        e.add_watch(JUCE_AP_CTOR, lambda em: self._skip(em, "AudioProcessor ctor"))
        e.add_watch(JUCE_SETPLAY, lambda em: self._skip(em, "setPlayConfigDetails"))
        self.watch_on = False

    def _skip(self, em, name):
        """Stand-in for two JUCE base-class calls: record the arguments, store numIn/numOut (+0x2c/+0x30) for setPlayConfigDetails,
        return to the caller (no other side effects)."""
        self.juce.append((name, em.r(0), em.r(1), em.r(2)))
        if name == "setPlayConfigDetails":
            em.w32(em.r(0) + 0x2c, em.r(1)); em.w32(em.r(0) + 0x30, em.r(2))
        em.uc.reg_write(A.UC_ARM_REG_PC, em.uc.reg_read(A.UC_ARM_REG_LR))

    def build(self, cfg=DO.CFG_PRODUCT, flags=DO.FLAGS, count=7):
        """AudioDeviceOutputUnit via the REAL ctor 0x1ae7dc with the argument struct exactly as 0x1b6284 lays it out (count, 7 floats,
        8 flag bytes)."""
        e = self.e
        arg = e.malloc(0x30, "ctor arg"); e.wr(arg, b"\0" * 0x30)
        e.w32(arg, count)
        for i in range(7): e.w32(arg + 4 + 4 * i, f2u(cfg[i]))
        e.wr(arg + 0x20, bytes(list(flags) + [0] * (8 - len(flags))))
        obj = e.malloc(0x170, "AudioDeviceOutputUnit"); e.wr(obj, b"\0" * 0x170)
        self.juce = []
        e.call(DEV_CTOR, obj, arg)
        vols = [e.call(GET_VOL, obj, i)[0] for i in range(count)]
        atts = [e.u32(e.u32(obj + 0xc4) + 4 * i) for i in range(e.u32(obj + 0xcc))]
        bulk = e.call(GET_BULK, obj)[0]
        return obj, vols, atts, bulk

    def chans(self, buf):
        e = self.e; n = e.u32(buf); arr = e.u32(buf + 0xc)
        return [e.u32(arr + 4 * i) for i in range(n)]

    def trace(self, vols, atts, bulk):
        """watch points at the three processBlock entries: log (stage, pair, channel pointers of the buffer in r1)."""
        e = self.e
        vpb = e.u32(e.u32(vols[0] + 8) + 0x14)
        vmap = {v + 8: i for i, v in enumerate(vols)}; amap = {a: i for i, a in enumerate(atts)}
        def h(stage, mp):
            def cb(em):
                if self.watch_on: self.log.append((stage, mp.get(em.r(0), em.r(0)) if mp else None, tuple(self.chans(em.r(1)))))
            return cb
        e.add_watch(vpb, h("OutputVolume", vmap)); e.add_watch(ATT_PB, h("FixedAttenuator", amap))
        e.add_watch(BULK_PB, h("BulkMuteUnit", None))
        return vpb


class BufN(h9.AudioBuf):
    """AudioBuffer view of n samples (h9.AudioBuf is fixed at 64)."""
    def __init__(self, e, nch, n):
        self.e = e; self.nch = nch; self.n = n
        self.obj = e.malloc(0x98, "AudioBuffer"); e.call(h9.AB_CTOR, self.obj)
        self.ptrs = [e.malloc(4 * n, "chan") for _ in range(nch)]
        arr = e.malloc(4 * nch, "chanptrs")
        for i, p in enumerate(self.ptrs): e.w32(arr + 4 * i, p)
        e.call(h9.AB_REFER, self.obj, arr, nch, n)

    def read(self, i): return self.e.floats(self.ptrs[i], self.n)


def run_block(rg, obj, buf, ins):
    for c, x in enumerate(ins): buf.write(c, x)
    rg.e.call(DEV_PB, obj, buf.obj, 0)
    return [buf.read(c) for c in range(len(ins))]


def insn_text(im, a):
    i = list(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a))[0]
    return "%s %s" % (i.mnemonic, i.op_str)


# =========================================================================================================== static
STATIC = {
    # processBlock 0x1ae3e4: per pair view (setDataToReferTo), OutputVolume via sub-object +8 slot 5, attenuator slot 5, BulkMute slot 5
    0x1ae3e4: "push {r4, r5, r6, r7, r8, sb, sl, fp, lr}",
    # ctor 0x1ae7dc: FixedAttenuator sign flip, BulkMuteUnit(count, 64), unmute 0x1aef3c
    # 0x1b6284 builds the ctor argument struct: count 7, sys+0x24c..+0x260 (+0x24c again for pair 6), flag bytes 1,1,1,1,1,1,0
    0x1b6768: "ldr r8, [r4, #0x24c]", 0x1b6780: "ldr sb, [r4, #0x25c]", 0x1b6798: "strb r3, [sp, #0x3e]", 0x1b679c: "mov r3, #7",
    0x1b67a4: "ldr r2, [r4, #0x250]", 0x1b67b4: "ldr fp, [r4, #0x254]", 0x1b67c0: "ldr r3, [r4, #0x258]", 0x1b67c8: "ldr sb, [r4, #0x260]",
    0x1b67d8: "str r8, [sp, #0x5c]", 0x1b67e8: "bl #0x1ae7dc", 0x1b67f4: "str r5, [r4, #0x3b8]", 0x1b683c: "str r5, [r4, #0x3c0]",
    # 0x5712cc: product config (HexaTrackAudioSystem 0x1c2cac): word17 = 2.0f, words 18..23 = 0.5f; struct at sp+0x58
    0x571400: "mov r3, #0x3f000000", 0x571414: "str r3, [sp, #0xa0]", 0x571430: "str r3, [sp, #0xb4]",
    0x571474: "mov r2, #0x40000000", 0x57147c: "str r2, [sp, #0x9c]", 0x5714a8: "add r3, sp, #0x58", 0x5714b4: "bl #0x1c2cac",
    # test config (TestModeAudioSystem 0x53cf54): words 17..23 = 1.0f; struct at sp+0xb8
    0x5712e4: "mov r3, #0x3f800000", 0x571318: "str r3, [sp, #0xfc]", 0x571314: "str r3, [sp, #0x114]", 0x571388: "add r3, sp, #0xb8",
    0x571394: "bl #0x53cf54",
    # AudioSystemBase ctor 0x1b8198: memcpy(sys+0x204, config, 0x60)
    0x1b81c4: "mov r2, #0x60", 0x1b81c8: "add r0, r4, #0x204", 0x1b81e0: "bl #0x1078c",
    # getVolume(type): IAudioSystem (sys+0x200) slot 41 thunk -> switch; OutputVolume getter; BulkMute getter
    0x1b93e8: "sub r0, r0, #0x200", 0x1b93ec: "b #0x1b93f0", 0x1b93f0: "cmp r1, #8",
    0x1ae614: "ldr r3, [r0, #0xb4]", 0x1ae61c: "ldrlo r3, [r0, #0xac]", 0x1ae62c: "ldr r0, [r0, #0xd0]",
    # OutputVolume (0xe993c -> Volume(1023, 100), table +0x94 = 0x83d750) and slots 2/3/4/5/6/13
    0xe9940: "movw r1, #0x3ff", 0xe9944: "mov r2, #0x64", 0xe9968: "add r3, r3, #0x100", 0xe9970: "str r3, [r4, #0x94]",
    0xe9920: "ldrh r3, [r3, r1]", 0xe992c: "vmul.f32 s13, s14, s15", 0xe9990: "movw r0, #0x3ff",
    0xe86e0: "str r1, [r0, #0x8c]", 0xe86e8: "ldr r0, [r0, #0x8c]",
    # Volume::processBlock 0xe9b70: slot 13 gain -> GainSmoother setTarget(gain, 1, +0x90) -> applyStereo
    0xe9b90: "ldr r1, [r0, #0x8c]", 0xe9b94: "ldr r3, [ip, #0x34]", 0xe9ba8: "ldr r3, [r4, #0x90]", 0xe9bb8: "bl #0xe895c", 0xe9bd0: "bl #0xe89f0",
    # FixedAttenuator 0xe87f8: multiply(ch0, +0x80) then multiply(ch1, +0x80) via 0x579178
    0xe8810: "ldr r1, [r0, #0x80]", 0xe8820: "bl #0x579178", 0xe883c: "b #0x579178", 0xe88d0: "str r4, [r6, #0x80]",
    # OutputVolumeController
    0x1d133c: "ldr r3, [ip, #0xa4]", 0x1d13cc: "bl #0x556204", 0x1d1410: "bl #0x5560d8", 0x1d1428: "bl #0x1d1210",
    0x1d1230: "ldrne r1, [r4, #0xc]", 0x1d1254: "ldrne r1, [r4, #0x10]", 0x1d1270: "mov r1, r5", 0x1d12f0: "cmp r0, #1",
    0x1d1304: "b #0x1d1210",
    # UIVolume ids 0/1/2 (UIVolume::init 0x55eea8), range 0x3ff
    0x55a35c: "mov r1, r5", 0x55a350: "mov r5, #0", 0x55a3a0: "bl #0x55eea8", 0x55a4a8: "mov r1, ip", 0x55a49c: "mov ip, #1",
    0x55a4ec: "bl #0x55eea8", 0x55a5e0: "mov r1, #2", 0x55a628: "bl #0x55eea8", 0x55a364: "mvn ip, #0xfc00",
    0x55ebb0: "ldr r0, [r0, #8]", 0x55ebb8: "ldrh r0, [r0, #0x12]",
    # muteAllOutput(bool) 0x1c10f4: audio thread -> BulkMute mute/unmute directly, else post Task (run 0x1c1290)
    0x1c1104: "ldr r3, [r4, #0x4b4]", 0x1c1258: "ldr r0, [r4, #0x3b8]", 0x1c125c: "bl #0x1ae62c", 0x1c126c: "b #0x1aef3c",
    0x1c1274: "b #0x1aeee4", 0x1c129c: "b #0x1c10f4",
    # HexaTrackAudioSystem processBlock (slot 5) 0x1c12a0 state machine sys+0x564: state 4 unmutes, state 6 path mutes
    0x1c12d4: "ldr r3, [r4, #0x564]", 0x1c1328: "mov r1, #0", 0x1c132c: "bl #0x1c10f4", 0x1c1784: "mov r1, #1",
    0x1c178c: "bl #0x1c10f4",
    # writers of sys+0x564: switchToRendererMode() (vt slot 108) -> 6, switchToSamplerMode() (vt slot 107) -> 1
    0x1ba7e8: "moveq r3, #6", 0x1ba7ec: "streq r3, [r4, #0x564]", 0x1ba9c8: "moveq r3, #1", 0x1ba9cc: "streq r3, [r4, #0x564]",
}


def static_section(im, P, check, J):
    P("\n== S static assertions (capstone)")
    bad = {hex(a): insn_text(im, a) for a, v in STATIC.items() if insn_text(im, a) != v}
    P("  %d instruction assertions: %s" % (len(STATIC), bad or "all match"))
    sw = {t: im.u32(0x1b93fc + 4 * t) for t in range(9)}
    sw_ok = [sw[t] for t in range(6)] == [0x1b9430, 0x1b943c, 0x1b9448, 0x1b9454, 0x1b9460, 0x1b946c]
    pairs = [(t, insn_text(im, sw[t] + 4)) for t in range(6)]
    P("  getVolume(type) 0x1b93f0 cases 0..5 -> %s (each 'ldr r0,[r0,#0x3b8]; mov r1,#p; b 0x1ae614')" % pairs)
    P("  cases 6/7/8 -> 0x%x (sys+0x5bc master fader proxy) / 0x%x (sys+0x5b8 return fader proxy) / 0x%x (sys+0x5c0 headphone proxy)"
      % (sw[6], sw[7], sw[8]))
    isys = im.u32(VT_ISYS + 41 * 4); hts5 = im.u32(0x863da0 + 5 * 4); hts87 = im.u32(0x863da0 + 87 * 4)
    jt = {s: im.u32(0x1c12e4 + 4 * s) for s in range(9)}
    modes = (im.u32(0x863da0 + 108 * 4), im.u32(0x863da0 + 107 * 4), im.cstr(0x864294, 40), im.cstr(0x8642cc, 40))
    P("  sys+0x564 writers: vt slot 108 = 0x%x (%r...), slot 107 = 0x%x (%r...)" % (modes[0], modes[2], modes[1], modes[3]))
    vt_ovc = im.u32(0x866158 + 8)
    t = DO.load_table(); mono = all(t[i] <= t[i + 1] for i in range(1023))
    P("  IAudioSystem vt 0x863f74 slot 41 = 0x%x; HexaTrackAudioSystem vt slot 5 = 0x%x, slot 87 = 0x%x; OutputVolumeController slot 2 = 0x%x"
      % (isys, hts5, hts87, vt_ovc))
    P("  sys+0x564 jump table: %s" % {s: hex(v) for s, v in jt.items()})
    P("  OutputVolume table 0x83d750: monotonic %s, t[0] %d, t[1] %d, t[1008] %d, t[1023] %d, first 32767 at %d" %
      (mono, t[0], t[1], t[1008], t[1023], min(i for i in range(1024) if t[i] == 32767)))
    pv = [(p, insn_text(im, sw[p] + 4)) for p in range(6)]
    check(not bad and sw_ok and [x[1] for x in pv] == ["mov r1, #%d" % p for p in (0, 1, 2, 3, 4, 6)] and isys == 0x1b93e8 and
          hts5 == 0x1c12a0 and hts87 == 0x1b93f0 and vt_ovc == OVC_LISTEN and jt[4] == 0x1c1308 and jt[6] == 0x1c1708 and mono and
          modes[:2] == (0x1ba784, 0x1ba964) and modes[2].startswith("switchToRendererMode") and modes[3].startswith("switchToSamplerMode"),
          "S: processBlock/ctor/config/getVolume/controller/UIVolume/BulkMute/state-machine instruction assertions; getVolume types "
          "0..5 = OutputVolume pairs 0,1,2,3,4,6; config words 18..23 = 0.5f (product) / 1.0f (test) copied to sys+0x24c..0x260")
    J["static"] = {"asserts": len(STATIC), "bad": bad, "getVolume": {t_: hex(v) for t_, v in sw.items()}, "jt564": {s: hex(v) for s, v in jt.items()}}


# =========================================================================================================== C6 base graph
class _I:
    def __init__(self, i):
        self.address, self.mnemonic, self.op_str = i.address, i.mnemonic, i.op_str
        m = re.match(r"(\w+), (\w+), #0$", i.op_str)
        if i.mnemonic == "subs" and m: self.mnemonic, self.op_str = "mov", "%s, %s" % (m.group(1), m.group(2))


class SubsAsMov:
    """Image view for the symbolic walker: `subs rX, rY, #0` (node-handle null test after addNode) is a plain move."""
    def __init__(self, im): self.im = im
    def __getattr__(self, k): return getattr(self.im, k)
    def disasm(self, lo, hi): return [_I(i) for i in self.im.disasm(lo, hi)]


EXPECTED_BASE = [   # (src, src pair, dst, dst pair)
    ("audioInputProcessorNode", (0, 1), "deviceInputUnitNode", (0, 1)),
    ("audioInputProcessorNode", (2, 3), "deviceInputUnitNode", (2, 3)),
    ("digitalResamplePlayerNode", (0, 1), "deviceInputUnitNode", (4, 5)),
    ("deviceOutputUnitNode", (0, 1), "audioOutputProcessorNode", (0, 1)),
    ("deviceOutputUnitNode", (2, 3), "audioOutputProcessorNode", (2, 3)),
    ("deviceOutputUnitNode", (4, 5), "audioOutputProcessorNode", (4, 5)),
    ("deviceOutputUnitNode", (6, 7), "audioOutputProcessorNode", (6, 7)),
    ("deviceOutputUnitNode", (8, 9), "audioOutputProcessorNode", (8, 9)),
    ("deviceOutputUnitNode", (10, 11), "audioOutputProcessorNode", (10, 11)),
    ("deviceOutputUnitNode", (12, 13), "digitalResampleRecorderNode", (0, 1)),
]
EXPECTED_MIDI = [("midiInputProcessorNode", "preProcessingNode"), ("preProcessingNode", "digitalResamplePlayerNode"),
                 ("digitalResamplePlayerNode", "deviceInputUnitNode"), ("deviceOutputUnitNode", "digitalResampleRecorderNode"),
                 ("digitalResampleRecorderNode", "postProcessingNode"), ("postProcessingNode", "midiOutputProcessorNode")]


def static_c6(im, P, check, J):
    P("\n== C6 base graph 0x1b6284 (symbolic walk): connections made before slot 55")
    conns = []; midi = []; names = []

    def h_str(st, site):
        a, b = st.r.get("r0", U), st.r.get("r1", U)
        if a[0] == "sp" and b[0] == "lit": st.stack[a[1]] = ("str", im.cstr(b[1], 80))

    def h_node(st, site):
        nm = st.last_str or "?"; names.append((site, nm)); return ("node", nm)

    def pairval(st, p):
        if p[0] == "lit": return (("mem", p[1]), ("mem", p[1] + 4))
        if p[0] == "sp": return (st.stack.get(p[1], U), st.stack.get(p[1] + 4, U))
        return (U, U)

    def h_conn(st, site):
        conns.append((site, st.r.get("r1"), pairval(st, st.r.get("r2", U)), st.r.get("r3"), pairval(st, st.stack.get(0, U))))

    def h_can(st, site):
        midi.append((site, st.r.get("r1"), st.r.get("r3")))
    st = State(); st.r["r0"] = ("base", "sys", 0); st.r["r4"] = ("base", "sys", 0)
    lo, hi = im.func_of(0x1b6284)
    st = Walker(SubsAsMov(im), {0x64a3fc: h_str, 0x5fdfec: h_node, 0x1b61bc: h_conn, 0x5fae80: h_can}).walk(0x1b6284, hi, st, fork=True,
                                                                                                    fork_min=0x1b6dc0)

    def node(v):
        if v and v[0] == "id": return v[1]
        return repr(v)

    def pair(p):
        out = []
        for v in p:
            if v[0] == "mem": v = ("lit", st.statics.get(v[1]))
            out.append(v[1] if v[0] == "lit" else None)
        return tuple(out)
    got = [(node(s), pair(sp), node(d), pair(dp)) for _, s, sp, d, dp in conns]
    gotm = [(node(s), node(d)) for _, s, d in midi]
    for (site, *_), g in zip(conns, got): P("  @0x%x  %-28s %-9s -> %-28s %s" % (site, g[0], g[1], g[2], g[3]))
    P("  MIDI (canConnect 0x5fae80 ch 0x1000): %s" % gotm)
    P("  nodes created: %s" % [n for _, n in names])
    ok = got == EXPECTED_BASE and gotm == EXPECTED_MIDI
    check(ok, "C6: base graph 0x1b6284: audioIn(0..3) -> deviceInput(0..3); resamplePlayer -> deviceInput(4,5); deviceOutput pairs 0..5 "
          "-> audioOutputProcessorNode (0..11, device channels); deviceOutput (12,13) -> digitalResampleRecorder (0,1); 6 MIDI links")
    if not ok: P("  MISMATCH: got %s / %s" % (got, gotm))
    J["c6"] = {"connections": [[a, list(b), c, list(d)] for a, b, c, d in got], "midi": gotm}


# =========================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H055"))
    ap.add_argument("--regress", action="store_true", help="re-run H010 (its recorded hashes) and H009 + H021..H041 via H010 --regress")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []; f32 = {}

    def P(s_=""): rep.append(s_); print(s_, flush=True)

    def check(c, msg):
        P(("PASS " if c else "FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    P("H055 device output stage — target sha256 %s" % emu.SHA)
    static_section(im, P, check, J)

    # ------------------------------------------------------------------------------------------------ C1 order / mapping
    P("\n== C1 AudioDeviceOutputUnit: real ctor 0x1ae7dc + real processBlock 0x1ae3e4 (14 distinct channels)")
    rg = Rig(); e = rg.e
    obj, vols, atts, bulk = rg.build()
    lay = {"count+0x80": e.u32(obj + 0x80), "cfg+0x84..": [u2f(e.u32(obj + 0x84 + 4 * i)) for i in range(7)],
           "flags+0xa0": list(e.rd(obj + 0xa0, 8)), "nch+0xa8": e.u32(obj + 0xa8), "vol n+0xb4": e.u32(obj + 0xb4),
           "att n+0xcc": e.u32(obj + 0xcc), "att gains+0x80": [u2f(e.u32(x + 0x80)) for x in atts],
           "vol vt": hex(e.u32(vols[0])), "vol idx+0x8c": [e.u32(v + 0x8c) for v in vols], "vol table+0x94": hex(e.u32(vols[0] + 0x94)),
           "bulk vt": hex(e.u32(bulk)), "bulk +0x80/84/88": [e.u32(bulk + 0x80), e.u32(bulk + 0x84), e.u32(bulk + 0x88)],
           "bulk cur/tgt +0x8c/+0x8d": list(e.rd(bulk + 0x8c, 2)), "bulk +0x90": e.u32(bulk + 0x90), "bulk n smoothers": e.u32(bulk + 0x9c),
           "juce calls": [(n, hex(o), r1, r2) for n, o, r1, r2 in rg.juce if n == "setPlayConfigDetails"][:3] + ["..."]}
    for k, v in lay.items(): P("  %-26s %s" % (k, v))
    J["c1_layout"] = {k: v for k, v in lay.items() if k != "juce calls"}
    vpb = rg.trace(vols, atts, bulk)
    buf = h9.AudioBuf(e, 14)
    cn = {p_: k for k, p_ in enumerate(buf.ptrs)}
    vals = [F((k + 1) / 16.0 * (-1) ** k) for k in range(14)]
    rg.watch_on = True; rg.log = []
    o1 = run_block(rg, obj, buf, [[v] * N for v in vals])
    rg.watch_on = False
    order = [(s, p, tuple(cn.get(x, -1) for x in ch)) for s, p, ch in rg.log]
    exp_order = []
    for p in range(7): exp_order += [("OutputVolume", p, (2 * p, 2 * p + 1)), ("FixedAttenuator", p, (2 * p, 2 * p + 1))]
    exp_order.append(("BulkMuteUnit", None, tuple(range(14))))
    exp1 = [F(v * (-0.5 if k < 12 else 0.5)) for k, v in enumerate(vals)]
    P("  stage order: %s" % (["%s[%s]%s" % (s, p, ch) for s, p, ch in order][:5] + ["...", "%s%s" % (order[-1][0], order[-1][2])]))
    P("  in -> out (first sample per channel): %s" % ["%d:%.4g->%.4g" % (k, vals[k], o1[k][0]) for k in range(14)])
    mapping_ok = all(o1[k] == [exp1[k]] * N for k in range(14))
    check(order == exp_order and mapping_ok and vpb == 0xe9b68,
          "C1: per pair p (channels 2p,2p+1, in place, no cross-channel mixing): OutputVolume[p] (Volume::processBlock via sub-object "
          "slot 5 0x%x) -> FixedAttenuator[p] (0xe87f8); then BulkMuteUnit (0x1aec8c) over all 14 channels; no pair skips a stage; "
          "first block passes (bulk adopts 'unmuted', no fade)" % vpb)
    J["c1"] = {"order": order, "out": [o[0] for o in o1]}

    # ------------------------------------------------------------------------------------------------ C2 OutputVolume law
    P("\n== C2 OutputVolume law (real slot 13 0xe9914) and smoother")
    allg = [u2f(e.call(VOL_SLOT13, vols[0], i)[0]) for i in range(1024)]
    mdl = [DO.outvol_gain(i) for i in range(1024)]
    nb = sum(f2u(x) != f2u(y) for x, y in zip(allg, mdl))
    P("  slot 13 for indices 0..1023: %d differ from model float(t[i]) * float(1/32767)" % nb)
    show = (0, 1, 2, 10, 50, 100, 200, 256, 300, 512, 600, 700, 768, 800, 900, 1000, 1007, 1008, 1023)
    P("  gain (dB): " + ", ".join("%d %s" % (i, ("%.2f" % (20 * math.log10(allg[i]))) if allg[i] else "-inf") for i in show))
    # region slopes of the u16 table (shape summary)
    t = DO.load_table()
    def slope(a_, b_): return (t[b_] - t[a_]) / float(b_ - a_)
    P("  table shape: piecewise linear in 16-index groups; mean slope (u16/index) 12..204 %.3f, 268..572 %.3f, 748..908 %.3f, "
      "924..988 %.3f; flat 32767 from 1008; every group has the step pattern +1.72s, +0.28s at i = 16k+10, 16k+11" %
      (slope(12, 204), slope(268, 572), slope(748, 908), slope(924, 988)))
    # DC through processBlock at 7 indices (pair 2, attenuator -0.5)
    dc = []
    for idx in (0, 1, 100, 512, 800, 1000, 1023):
        rg2 = Rig(); o2, v2, a2, b2 = rg2.build()
        rg2.e.call(VOL_SET, v2[2], idx)
        b_ = h9.AudioBuf(rg2.e, 14)
        for blk in range(3): out = run_block(rg2, o2, b_, [[0.25] * N for _ in range(14)])
        g = out[4][-1] / (0.25 * -0.5)
        dc.append((idx, g, DO.outvol_gain(idx)))
    P("  processBlock DC (pair 2, in 0.25, after 3 blocks): " + ", ".join("%d -> %.9g (model %.9g)" % x for x in dc))
    # step ramp: index 1023 -> 512 at sample offset 17 (slot 3) on DC 1.0, pair 0
    rg3 = Rig(); o3, v3, a3, b3 = rg3.build(); b_ = h9.AudioBuf(rg3.e, 14)
    run_block(rg3, o3, b_, [[1.0] * N for _ in range(14)])
    rg3.e.call(VOL_SETOFF, v3[0], 512, 17)
    ramp = []
    for blk in range(3): ramp += run_block(rg3, o3, b_, [[1.0] * N for _ in range(14)])[0]
    gs = [x / -0.5 for x in ramp]
    tgt = DO.outvol_gain(512)
    lin = all(abs(gs[17 + k] - (1.0 + (tgt - 1.0) * k / 100.0)) < 2e-6 for k in range(100))
    P("  step 1023 -> 512 at offset 17: g[16] %.7g g[17] %.7g g[67] %.7g g[116] %.7g g[117] %.7g (target %.7g); linear over 100 samples "
      "from the offset: %s" % (gs[16], gs[17], gs[67], gs[116], gs[117], tgt, lin))
    # offset persistence: slot 3 (700, offset 40), later slot 2 (100) -> the ramp again starts at sample 40
    rg4 = Rig(); o4, v4, a4, b4 = rg4.build(); b_ = h9.AudioBuf(rg4.e, 14)
    rg4.e.call(VOL_SETOFF, v4[1], 700, 40); run_block(rg4, o4, b_, [[1.0] * N for _ in range(14)])
    for blk in range(3): run_block(rg4, o4, b_, [[1.0] * N for _ in range(14)])
    rg4.e.call(VOL_SET, v4[1], 100)
    pr = run_block(rg4, o4, b_, [[1.0] * N for _ in range(14)])[2]
    persist = pr[39] == pr[0] and pr[40] == pr[0] and pr[41] != pr[0]
    P("  offset persistence (slot 3 (700, 40) then slot 2 (100) four blocks later): out[0] %.7g out[39] %.7g out[40] %.7g out[41] %.7g "
      "-> ramp starts at the stale offset 40: %s" % (pr[0], pr[39], pr[40], pr[41], persist))
    check(nb == 0 and all(f2u(g) == f2u(m) for _, g, m in dc) and lin and persist and allg[1023] == 1.0 and allg[0] == 0.0,
          "C2: OutputVolume gain = float(u16 table 0x83d750[i]) * float(1/32767) for all 1024 indices (0 = mute, 1 = -44.03 dB, "
          "512 = -14.22 dB, 1008..1023 = 0 dB); 100-sample linear ramp from the parameter's sample offset; the offset persists "
          "(slot 2 reuses the last slot-3 offset)")
    J["c2"] = {"differ": nb, "dc": dc, "ramp": [gs[16], gs[17], gs[67], gs[116], gs[117]], "persist": persist}
    f32["c2_ramp"] = ramp

    # ------------------------------------------------------------------------------------------------ C3 FixedAttenuator
    P("\n== C3 FixedAttenuator values and sign (emulated output / input per channel, DC 0.25, all OutputVolume = 1023)")
    c3 = {}
    custom = ([0.75, 0.3, 1.5, 0.5, 0.25, 2.0, 0.6], [1, 0, 1, 0, 1, 0, 1])
    for name, cfg, flags in (("product (sys+0x24c.. = 0.5)", DO.CFG_PRODUCT, DO.FLAGS), ("test mode (1.0)", DO.CFG_TEST, DO.FLAGS),
                             ("arbitrary cfg/flags", custom[0], custom[1])):
        rgx = Rig(); ox, vx, ax, bx = rgx.build(cfg, flags); b_ = h9.AudioBuf(rgx.e, 14)
        out = run_block(rgx, ox, b_, [[0.25] * N for _ in range(14)])
        r = [out[2 * p][0] / 0.25 for p in range(7)]
        expect = [(-cfg[p] if flags[p] else cfg[p]) for p in range(7)]
        c3[name] = (r, all(F(r[p]) == F(expect[p]) and out[2 * p + 1] == out[2 * p] for p in range(7)))
        P("  %-28s gains per pair %s  (expected %s) %s" % (name, ["%g" % x for x in r], ["%g" % x for x in expect], c3[name][1]))
    check(all(v[1] for v in c3.values()),
          "C3: FixedAttenuator gain = config float, negated by the ctor (eor 0x80000000) when the pair flag is set: product build "
          "-0.5 on pairs 0..5 (device outs), +0.5 on pair 6 (resample recorder); test build -1/+1")
    J["c3"] = {k: v[0] for k, v in c3.items()}

    # ------------------------------------------------------------------------------------------------ C4 BulkMuteUnit
    P("\n== C4 BulkMuteUnit (real ctor 0x1af1b0 via 0x1ae7dc; mute 0x1aeee4, unmute 0x1aef3c, processBlock 0x1aec8c)")
    rgm = Rig(); om, vm, am, bm = rgm.build(); em = rgm.e; b_ = h9.AudioBuf(em, 14)
    st0 = list(em.rd(bm + 0x8c, 2))
    run_block(rgm, om, b_, [[1.0] * N for _ in range(14)])
    st1 = list(em.rd(bm + 0x8c, 2))
    em.call(BULK_MUTE, bm)
    seq = []
    for blk in range(3): seq += run_block(rgm, om, b_, [[1.0] * N for _ in range(14)])[0]
    st2 = list(em.rd(bm + 0x8c, 2))
    em.call(BULK_UNMUTE, bm)
    up = []
    for blk in range(2): up += run_block(rgm, om, b_, [[1.0] * N for _ in range(14)])[0]
    gm = [x / -0.5 for x in seq]; gu = [x / -0.5 for x in up]
    mute_lin = all(abs(gm[k] - (1.0 - k / 64.0)) < 1e-6 for k in range(64)) and all(x == 0.0 for x in gm[64:])
    unm_lin = all(abs(gu[k] - k / 64.0) < 1e-6 for k in range(64)) and all(x == 1.0 for x in gu[64:])
    P("  after ctor cur/tgt %s; after first block %s; mute: g[0] %.6g g[1] %.6g g[63] %.6g g[64] %.6g ... g[191] %.6g; state %s" %
      (st0, st1, gm[0], gm[1], gm[63], gm[64], gm[191], st2))
    P("  unmute: g[0] %.6g g[1] %.6g g[63] %.6g g[64] %.6g" % (gu[0], gu[1], gu[63], gu[64]))
    # reversals with 32-sample blocks (real code, model in lockstep): (a) unmute 32 samples into a mute fade, (b) mute again later,
    # (c) mute, let the fade end exactly at a block end, unmute before the unit adopts 'muted'
    rgr = Rig(); er = rgr.e; orr, vr, ar, br = rgr.build(); b32 = BufN(er, 14, 32); mr = DO.DeviceOut(); rv = []; rbad = 0
    def step32(ev=None):
        nonlocal rbad
        if ev == "mute": er.call(BULK_MUTE, br); mr.bulk.set_muted(True)
        if ev == "unmute": er.call(BULK_UNMUTE, br); mr.bulk.set_muted(False)
        src = [[1.0] * 32 for _ in range(14)]
        for c in range(14): b32.write(c, src[c])
        er.call(DEV_PB, orr, b32.obj, 0)
        o = b32.read(0); mo = mr.process(src)[0]
        rbad += sum(p_ != q_ for p_, q_ in zip(bits(o), bits(mo)))
        rv.append((ev, [x / -0.5 for x in o], list(er.rd(br + 0x8c, 2))))
    for ev in (None, "mute", "unmute", None, None, "mute", None, None, None, None, "unmute", None, None, "mute", None, None, "unmute",
               None, "mute", None):
        step32(ev)
    for k, (ev, g, stt_) in enumerate(rv):
        P("    blk32 %2d %-7s g[0] %-9.6g g[31] %-9.6g cur/tgt %s" % (k, ev or "", g[0], g[31], stt_))
    P("  32-sample reversal sequence: %d samples differ from the model" % rbad)
    gr = [g for _, g, _ in rv]
    # fresh BulkMuteUnit without the ctor's unmute: built muted -> clears the buffer
    rgf = Rig(); ef = rgf.e
    bf = ef.malloc(0xb0, "BulkMuteUnit"); ef.wr(bf, b"\0" * 0xb0); ef.call(BULK_CTOR, bf, 7, 64)
    bb = h9.AudioBuf(ef, 14)
    for c in range(14): bb.write(c, [0.5] * N)
    ef.call(BULK_PB, bf, bb.obj, 0)
    fresh_zero = all(x == 0.0 for c in range(14) for x in bb.read(c))
    P("  BulkMuteUnit(7, 64) alone (no unmute): cur/tgt %s, output all zero: %s" % (list(ef.rd(bf + 0x8c, 2)), fresh_zero))
    check(st0 == [1, 0] and st1 == [0, 0] and mute_lin and unm_lin and st2 == [1, 1] and fresh_zero and rbad == 0,
          "C4: BulkMuteUnit: 7 MuteSmoothers of 64 samples; mute = linear 1 -> 0 over 64 samples then cleared buffer, unmute = 0 -> 1 "
          "over 64 samples; built muted (+0x8c = +0x8d = 1, clears), the AudioDeviceOutputUnit ctor unmutes it (first block adopts "
          "unmuted with no fade); reversals before the unit adopts the new state are bit-exact to the model (see the blk32 log)")
    J["c4"] = {"st": [st0, st1, st2], "mute": gm[:66], "unmute": gu[:66], "rev32": [(ev, g[0], g[31], s_) for ev, g, s_ in rv],
               "fresh_zero": fresh_zero}
    f32["c4_mute"] = seq + up + sum(gr, [])

    # ------------------------------------------------------------------------------------------------ C5 OutputVolumeController
    P("\n== C5 OutputVolumeController (real ctor 0x1d1308, real getVolume path, real UIVolume objects, real listener 0x1d12d4)")
    rgc = Rig(); ec = rgc.e
    oc, vc, ac, bc = rgc.build()
    sysb = ec.malloc(0x600, "HexaTrackAudioSystem stand-in"); ec.wr(sysb, b"\0" * 0x600)
    ec.w32(sysb + 0x3b8, oc); ec.w32(sysb + 0x200, VT_ISYS)
    uiv = []
    for i in range(3):
        u = ec.malloc(0x28, "UIVolume"); ec.call(UIVOL_CTOR, u); ec.w32(u + 8, i)
        for off in (0xc, 0x12, 0x14): ec.wr(u + off, struct.pack("<H", 0))
        uiv.append(u)
    stt = ec.malloc(0x1100, "UIInputManager state"); ec.wr(stt, b"\0" * 0x1100)
    arr = ec.malloc(12, "UIVolume array"); [ec.w32(arr + 4 * i, uiv[i]) for i in range(3)]
    ec.w32(stt + 0x10, arr); ec.w32(stt + 0x18, 3)
    mgr = ec.malloc(0x10, "UIInputManager stand-in"); ec.wr(mgr, b"\0" * 0x10); ec.w32(mgr + 8, stt)
    ctrl = ec.malloc(0x2c, "OutputVolumeController"); ec.wr(ctrl, b"\0" * 0x2c)
    ec.call(OVC_CTOR, ctrl, sysb + 0x200, mgr)
    cached = [ec.u32(ctrl + o) for o in range(0x14, 0x2c, 4)]
    regd = ec.u32(uiv[1] + 0x24) == 1 and ec.u32(ec.u32(uiv[1] + 0x1c)) == ctrl

    def idx(): return [ec.call(VOL_GET, v)[0] for v in vc]
    P("  ctor: vt 0x%x, +0xc/+0x10 = %d/%d, cached volumes == OutputVolume[0,1,2,3,4,6]: %s, listener registered on UIVolume id 1: %s" %
      (ec.u32(ctrl), ec.u32(ctrl + 0xc), ec.u32(ctrl + 0x10), cached == [vc[p] for p in (0, 1, 2, 3, 4, 6)], regd))
    P("  indices after ctor (UIVolume 1 value 0): %s" % idx())
    c5 = []
    for src, v in ((1, 600), (1, 1), (1, 1023), (0, 300), (2, 5), (1, 0), (1, 777)):
        ec.wr(uiv[src] + 0x12, struct.pack("<H", v))
        ec.call(OVC_LISTEN, ctrl, uiv[src], v)
        got = idx()
        mc = DO.DeviceOut(); ctl = DO.OutputVolumeController(mc)
        for s_, v_ in c5: ctl.on_pot(v_[1], v_[0])
        ctl.on_pot(v, src)
        c5.append(((src, v), got))
        exp = [x.index for x in mc.vol]
        P("  UIVolume id %d = %4d -> OutputVolume indices %s  (model %s)" % (src, v, got, exp))
    # model check of the whole sequence
    mc = DO.DeviceOut(); ctl = DO.OutputVolumeController(mc); ctl.on_pot(0)
    seq_ok = True
    for (src, v), got in c5:
        ctl.on_pot(v, src)
        seq_ok = seq_ok and got == [x.index for x in mc.vol]
    check(regd and cached == [vc[p] for p in (0, 1, 2, 3, 4, 6)] and seq_ok and ec.u32(ctrl + 0xc) == 1023,
          "C5: OutputVolumeController listens to UIVolume id 1 (0..1023): pot 0 -> OutputVolume[0..4,6] = 0; pot v > 0 -> [0] = [6] = 1023, "
          "[1..4] = v; pair 5 (DSF send) untouched; ids 0/2 ignored")
    J["c5"] = c5

    # ------------------------------------------------------------------------------------------------ C6 base graph
    static_c6(im, P, check, J)

    # ------------------------------------------------------------------------------------------------ C7 model vs emulation
    P("\n== C7 model harness/models/device_out.py vs emulated AudioDeviceOutputUnit (14 channels)")
    SETTINGS = [  # name, cfg, flags, initial indices, events {block: [(kind, args)]}
        ("default", DO.CFG_PRODUCT, DO.FLAGS, None, {}),
        ("indices+changes", DO.CFG_PRODUCT, DO.FLAGS, [1023, 512, 100, 1, 800, 1023, 0],
         {5: [("off", 1, 700, 40)], 10: [("off", 0, 300, 17)], 20: [("set", 1, 100)], 30: [("set", 3, 1023)], 45: [("off", 6, 512, 63)]}),
        ("mute toggles", DO.CFG_PRODUCT, DO.FLAGS, [900, 1023, 1023, 600, 1023, 1023, 1023],
         {8: [("mute",)], 20: [("unmute",)], 21: [("mute",)], 40: [("unmute",)], 41: [("off", 0, 10, 5)]}),
        ("test cfg", DO.CFG_TEST, DO.FLAGS, [1023, 1023, 256, 1023, 50, 1023, 1023], {12: [("off", 2, 1023, 1)], 33: [("mute",)]}),
        ("arbitrary cfg", custom[0], custom[1], [1008, 1007, 11, 10, 16, 27, 512], {25: [("set", 6, 0)], 26: [("set", 6, 1023)]}),
        ("controller pot", DO.CFG_PRODUCT, DO.FLAGS, None,
         {0: [("pot", 0)], 10: [("pot", 600)], 25: [("pot", 1023)], 40: [("pot", 0)], 50: [("pot", 1)]}),
        ("low levels", DO.CFG_PRODUCT, DO.FLAGS, [2, 3, 4, 5, 6, 7, 8], {30: [("off", 4, 1, 33)], 31: [("mute",)], 50: [("unmute",)]}),
    ]
    kinds = ["impulse", "sine", "noise", "steps"]
    tot = 0; nbad = 0; worst = 0.0; per = {}
    for sname, cfg, flags, ind, evs in SETTINGS:
        for kind in kinds:
            rgs = Rig(); es = rgs.e
            os_, vs, as_, bs = rgs.build(cfg, flags)
            md = DO.DeviceOut(cfg, flags, ind)
            if ind:
                for p, ix in enumerate(ind): es.call(VOL_SET, vs[p], ix)
            ctrl = None
            if sname == "controller pot":        # minimal controller object for the REAL apply routine 0x1d1210
                ctrl = es.malloc(0x2c, "OVC"); es.wr(ctrl, b"\0" * 0x2c); es.w32(ctrl + 0xc, 1023); es.w32(ctrl + 0x10, 1023)
                for k_, p in enumerate((0, 1, 2, 3, 4, 6)): es.w32(ctrl + 0x14 + 4 * k_, vs[p])
                mctl = DO.OutputVolumeController(md)
            r_ = random.Random(zlib.crc32((sname + "/" + kind).encode()))
            bb = h9.AudioBuf(es, 14); bad = 0
            for blk in range(60):
                for ev in evs.get(blk, []):
                    if ev[0] == "off": es.call(VOL_SETOFF, vs[ev[1]], ev[2], ev[3]); md.vol[ev[1]].set(ev[2], ev[3])
                    elif ev[0] == "set": es.call(VOL_SET, vs[ev[1]], ev[2]); md.vol[ev[1]].set(ev[2])
                    elif ev[0] == "mute": es.call(BULK_MUTE, bs); md.bulk.set_muted(True)
                    elif ev[0] == "unmute": es.call(BULK_UNMUTE, bs); md.bulk.set_muted(False)
                    elif ev[0] == "pot": es.call(OVC_APPLY, ctrl, ev[1]); mctl.on_pot(ev[1])
                src = []
                for c in range(14):
                    x = h9.sig(kind if c % 3 else ("sine" if kind != "sine" else "steps"), blk, c % 2, r_)
                    src.append([F(v * (0.25 + 0.0625 * c)) for v in x])
                out = run_block(rgs, os_, bb, src)
                mo = md.process(src)
                for c in range(14):
                    tot += N
                    d = sum(p_ != q_ for p_, q_ in zip(bits(out[c]), bits(mo[c])))
                    bad += d
                    worst = max(worst, max(abs(p_ - q_) for p_, q_ in zip(out[c], mo[c])))
                f32.setdefault("c7_%s" % sname.replace(" ", "_").replace("+", "_"), []).extend(sum(out, []))
            per[(sname, kind)] = bad; nbad += bad
    for sname, *_ in SETTINGS:
        P("  %-16s differing samples per signal: %s" % (sname, [per[(sname, k)] for k in kinds]))
    P("  %d settings x %d signals x 60 blocks x 64 frames x 14 channels = %d channel-samples compared, %d differ, max |diff| %.3g" %
      (len(SETTINGS), len(kinds), tot, nbad, worst))
    # denormal input (NEON flush in multiply / copyWithMultiply vs scalar tail)
    rgd = Rig(); ed = rgd.e; od, vd, ad, bd = rgd.build(); md = DO.DeviceOut(); bb = h9.AudioBuf(ed, 14); dbad = 0; dtot = 0
    ed.call(VOL_SETOFF, vd[3], 400, 7); md.vol[3].set(400, 7)
    for blk in range(10):
        src = [h9.sig("denorm", blk, c % 2, None) for c in range(14)]
        out = run_block(rgd, od, bb, src); mo = md.process(src)
        for c in range(14):
            dtot += N; dbad += sum(p_ != q_ for p_, q_ in zip(bits(out[c]), bits(mo[c])))
    P("  denormal input (10 blocks, pair 3 ramp): %d of %d channel-samples differ" % (dbad, dtot))
    check(nbad == 0 and dbad == 0, "C7: device_out.py bit-exact to the emulated AudioDeviceOutputUnit (volume indices and ramps, stale "
          "offsets, mute toggles incl. mid-fade reversal, product/test/arbitrary attenuator configs, controller pot path, denormals)")
    J["c7"] = {"compared": tot, "differ": nbad, "denorm": [dtot, dbad]}

    # ------------------------------------------------------------------------------------------------ outputs
    for k_, v in sorted(f32.items()):
        open(os.path.join(a.out, "h055_%s.f32" % k_), "wb").write(struct.pack("<%df" % len(v), *v))
    P("\nimports used: %s" % sorted(set(n for n, *_ in rgd.e.import_report())))
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h055_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h055.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


def regress(out):
    """Re-run H010 (compare its recorded hashes) and H010 --regress (H009 + H021..H041)."""
    import subprocess, glob
    d = os.path.join(out, "regress", "H010"); os.makedirs(d, exist_ok=True)
    rc = subprocess.call([sys.executable, "-B", os.path.join(HERE, "H010_send_bus.py"), "--out", d],
                         stdout=open(os.path.join(out, "regress", "H010.log"), "w"), stderr=subprocess.STDOUT)
    exp = {"h010_report.txt": "8ed30f0b", "h010.json": "49848d76"}
    got = {k: sha(open(os.path.join(d, k), "rb").read()) for k in exp if os.path.exists(os.path.join(d, k))}
    f32s = sha(b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(d, "*.f32")))))
    ok10 = all(got.get(k, "").startswith(v) for k, v in exp.items()) and f32s.startswith("b04bf76d")
    d2 = os.path.join(out, "regress", "H010r"); os.makedirs(d2, exist_ok=True)
    rc2 = subprocess.call([sys.executable, "-B", os.path.join(HERE, "H010_send_bus.py"), "--regress", "--out", d2],
                          stdout=open(os.path.join(out, "regress", "H010r.log"), "w"), stderr=subprocess.STDOUT)
    rtxt = open(os.path.join(d2, "h010_regress.txt")).read() if os.path.exists(os.path.join(d2, "h010_regress.txt")) else ""
    ok2 = rc2 == 0 and sha(rtxt.encode()).startswith("f7a63fbf")
    txt = ("H010 rc %d %s report %s json %s f32 %s\nH010 --regress rc %d %s h010_regress.txt %s\n%s" %
           (rc, "OK " if ok10 else "BAD", got.get("h010_report.txt", "-")[:8], got.get("h010.json", "-")[:8], f32s[:8],
            rc2, "OK " if ok2 else "BAD", sha(rtxt.encode())[:8], rtxt))
    open(os.path.join(out, "h055_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok10 and ok2 else 1


if __name__ == "__main__":
    sys.exit(main())
