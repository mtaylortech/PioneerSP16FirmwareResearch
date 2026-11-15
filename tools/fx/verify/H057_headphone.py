#!/usr/bin/env python3
"""H057 — headphone cue mix (HeadphoneUnit / HeadphoneRouter) and the main-output selector (Output12Router), 1.60 (kb/cycles/042.md).

Sections (success criteria of cycle 042):
  S   static assertions (capstone): router/selector ctors and flag writers, setHeadphoneSource identifier order, UI setters and the
      OutputSettingViewController popup mapping, MuteSmoother lengths, crossfade length literal, Output12Router selection writer.
  C1  setHeadphoneSource 0x1afbac (REAL, reached through router vt slot 2 0x1b0770) for all 13 source indices: OutputSelector target
      pair and CueMaster flag (+0x140), with router +0x98 = 1 (as built) and 0 (forced; unreachable alternative).
  C2  REAL HeadphoneUnit ctor 0x1b17b0 + prepareToPlay 0x1b0d94 + processBlock 0x1b10ec: input->output gain matrix (unit impulse on
      each of the 14 inputs and 6 cue channels) for every source, cue gates, crossfade, VolumeKnob law, selector switch shape.
  C3  REAL Output12Router ctor 0x1b2d8c + 0x1b28f8 + processBlock 0x1b2610: both selections, switch shape, unknown value.
  C4  models/headphone_mix.py vs emulation: random scenarios (sources, gates, crossfade, knob slot 2/3 with offsets, modes), >= 1e5
      output samples per routine, bit-exact float32.
Emulation boundary: JUCE AudioProcessor base ctor 0x5f9e00 / setPlayConfigDetails 0x5f9e90 (recording stubs, as H055); juce Identifier /
String / Value helpers (0x666e84, 0x627ba0, 0x6280c8, 0x62abf4) and the enum<->identifier converters 0x34f058/0x34f018/0x34ef78/0x34ef38
replaced by an index model (identifier object address -> enum index, table order asserted in S); the async task box global 0xb81be4
points to a stand-in with no thread (+0x18 = 0 -> direct store, the audio-thread path); the cue source (+0x90) and IMonitorMixer (+0x94)
are harness fakes. Everything else is real 1.60 code (selector, smoothers, AudioBuffer ops, VolumeKnob, meter).
Outputs only to --out (default harness/out/H057/). Run: .venv/bin/python -B harness/H057_headphone.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from unicorn import arm_const as A                             # noqa: E402
import sp16img                                                 # noqa: E402
import H009_track_mix as h9                                    # noqa: E402  (AudioBuf, Fakes, guard stubs)
import track_mix as TM                                         # noqa: E402
import headphone_mix as HM                                     # noqa: E402

N = 64
F = TM.F
HP_CTOR, HP_PREP, HP_PB, HP_ROUTER, HP_KNOB = 0x1b17b0, 0x1b0d94, 0x1b10ec, 0x1b1b70, 0x1b1b78
RT_SETSRC, RT_SLOT2 = 0x1afbac, 0x1b0770
O12_CTOR, O12_SEL, O12_PB, O12_SETMODE = 0x1b2d8c, 0x1b28f8, 0x1b2610, 0x1b2d84
VOL_SET, VOL_SETOFF = 0xe86e0, 0xe86f0
JUCE_AP_CTOR, JUCE_SETPLAY = 0x5f9e00, 0x5f9e90
TASKBOX_GLOBAL = 0xb81be4
# identifier statics used by 0x1afbac / 0x1b28f8 (S asserts their table order): address -> enum index
HP_IDS = {0xf5392c: 0, 0xf53940: 1, 0xf53948: 2, 0xf53950: 3, 0xf53958: 4, 0xf53960: 5, 0xf53968: 6, 0xf53970: 7,
          0xf53978: 8, 0xf53980: 9, 0xf53988: 10, 0xf53990: 11, 0xf53998: 12}
O12_IDS = {0xf53a10: 0, 0xf53a24: 1}
FAKEID_HP, FAKEID_O12 = 0x3c000000, 0x3c001000

emu.STUBS.setdefault("pthread_mutex_lock", (lambda e: e.setr(0, 0), "no-op, returns 0 (single thread)"))
emu.STUBS.setdefault("pthread_mutex_unlock", (lambda e: e.setr(0, 0), "no-op, returns 0 (single thread)"))
emu.STUBS.setdefault("pthread_self", (lambda e: e.setr(0, 0x1234), "constant thread id"))


def sha(b): return hashlib.sha256(b).hexdigest()


def ret(em, v=None):
    if v is not None: em.setr(0, v & 0xffffffff)
    em.uc.reg_write(A.UC_ARM_REG_PC, em.uc.reg_read(A.UC_ARM_REG_LR))


# =========================================================================================================== rig
class Rig:
    def __init__(self):
        self.e = e = emu.Emu(insn_limit=80_000_000)
        self.fk = h9.Fakes(e)
        self.juce = []; self.values = {}; self.vlog = []
        e.add_watch(JUCE_AP_CTOR, lambda em: self._juce(em, "AudioProcessor ctor"))
        e.add_watch(JUCE_SETPLAY, lambda em: self._juce(em, "setPlayConfigDetails"))
        # identifier / string / value index model
        e.add_watch(0x666e84, lambda em: ret(em, em.r(0)))                      # Identifier(const char*): no-op
        e.add_watch(0x6280c8, lambda em: ret(em))                               # String/Identifier dtor: no-op
        e.add_watch(0x627ba0, lambda em: (em.w32(em.r(0), em.r(1)), ret(em, em.r(0))))   # copy ctor: *dst = id handle
        e.add_watch(0x62abf4, self._value_set)                                  # Value/property assign
        e.add_watch(0x34f058, lambda em: ret(em, self._to_index(em.r(0), HP_IDS, FAKEID_HP)))
        e.add_watch(0x34ef78, lambda em: ret(em, self._to_index(em.r(0), O12_IDS, FAKEID_O12)))
        e.add_watch(0x34f018, lambda em: ret(em, FAKEID_HP + em.r(0)))
        e.add_watch(0x34ef38, lambda em: ret(em, FAKEID_O12 + em.r(0)))
        # async task box stand-in: +0x18 == 0 -> setSelection / setHeadphoneSource store directly
        tb = e.malloc(0x40, "taskbox"); e.wr(tb, b"\0" * 0x40); e.w32(TASKBOX_GLOBAL, tb)

    def _juce(self, em, name):
        self.juce.append((name, em.r(0), em.r(1), em.r(2)))
        if name == "setPlayConfigDetails":
            em.w32(em.r(0) + 0x2c, em.r(1)); em.w32(em.r(0) + 0x30, em.r(2))
        ret(em)

    def _to_index(self, addr, ids, base):
        if addr in ids: return ids[addr]
        if addr in self.values: return self.values[addr]
        raise emu.EmuAbort("identifierToIndex on unknown address 0x%x" % addr)

    def _value_set(self, em):
        dst, src = em.r(0), em.r(1); h = em.u32(src)
        idx = h - FAKEID_HP if FAKEID_HP <= h < FAKEID_HP + 0x100 else (h - FAKEID_O12 if FAKEID_O12 <= h < FAKEID_O12 + 0x100 else None)
        self.values[dst] = idx; self.vlog.append((dst, idx)); ret(em, dst)

    def routing(self, field_off, value):
        """SwitchableObject<prj::RoutingData,17> stand-in: +8 -> index word (0); +0x50 = 0; +0xc -> RoutingData; RD+field = value."""
        e = self.e
        sw = e.malloc(0x100, "SwitchableObject"); e.wr(sw, b"\0" * 0x100)
        ix = e.malloc(4, "objectIndex"); e.w32(ix, 0); e.w32(sw + 8, ix)
        rd = e.malloc(0x100, "RoutingData"); e.wr(rd, b"\0" * 0x100); e.w32(sw + 0xc, rd)
        self.values[rd + field_off] = value
        return sw, rd


class HPRig(Rig):
    def build(self, source=0):
        e = self.e
        self.sw, self.rd = self.routing(0x28, source)
        self.cue = [[0.0] * N for _ in range(6)]; self.gates = [0, 0, 0]; self.xf = 0; self.mix_calls = []

        def cue_pb(em, nm):
            buf = em.r(1); nch = em.u32(buf); arr = em.u32(buf + 0xc)
            for c in range(min(nch, 6)): em.set_floats(em.u32(arr + 4 * c), self.cue[c])
        cp = self.fk.obj("cueSource", {0x14: cue_pb, 0x0c: lambda em, nm: None}, size=0x40)
        e.w32(cp + 0x2c, 6); e.w32(cp + 0x30, 6)
        self.cue_proc = cp

        def g4(em, nm): self.mix_calls.append(("slot4", em.r(1), em.r(2))); em.setr(0, self.gates[em.r(1)])
        def g8(em, nm): self.mix_calls.append(("slot8",)); em.setr(0, self.xf)
        mx = self.fk.obj("IMonitorMixer", {0x10: g4, 0x20: g8}, size=0x40)
        self.obj = obj = e.malloc(0x1d8, "HeadphoneUnit"); e.wr(obj, b"\0" * 0x1d8)
        e.call(HP_CTOR, obj, self.sw, cp, mx)
        self.router = e.call(HP_ROUTER, obj)[0]; self.knob = e.call(HP_KNOB, obj)[0]
        lo, hi = struct.unpack("<II", struct.pack("<d", 44100.0))
        e.call(HP_PREP, obj, 0, lo, hi, stack_args=(N,))
        self.buf = h9.AudioBuf(e, 14)
        return obj

    def block(self, ins, cue=None):
        e = self.e
        for c in range(14): self.buf.write(c, ins[c])
        if cue is not None: self.cue = cue
        e.call(HP_PB, self.obj, self.buf.obj, 0)
        return [self.buf.read(0), self.buf.read(1)]

    def set_source(self, idx):                   # IHeadphoneRouter slot 2 (async wrapper 0x1b0770 -> 0x1afbac)
        self.e.call(RT_SLOT2, self.router, idx)

    def sel_state(self):
        s = self.e.u32(self.router + 0xa0); u = lambda a: struct.unpack("<i", struct.pack("<I", self.e.u32(a)))[0]
        return (u(s + 0x8c), u(s + 0x90)), (u(s + 0x94), u(s + 0x98)), self.e.rd(self.router + 0x140, 1)[0], self.e.rd(self.router + 0x98, 1)[0]


class O12Rig(Rig):
    def build(self, mode=0):
        e = self.e
        self.sw, self.rd = self.routing(0x24, mode)
        self.obj = obj = e.malloc(0x98, "Output12Router"); e.wr(obj, b"\0" * 0x98)
        e.call(O12_CTOR, obj, self.sw)
        self.buf = h9.AudioBuf(e, 4)
        return obj

    def block(self, ins):
        for c in range(4): self.buf.write(c, ins[c])
        self.e.call(O12_PB, self.obj, self.buf.obj, 0)
        return [self.buf.read(0), self.buf.read(1)]

    def sel_state(self):
        s = self.e.u32(self.obj + 0x8c); u = lambda a: struct.unpack("<i", struct.pack("<I", self.e.u32(a)))[0]
        return (u(s + 0x8c), u(s + 0x90)), (u(s + 0x94), u(s + 0x98))




# =========================================================================================================== static
STATIC = {
    # HeadphoneRouter: +0x98 byte written only to 1 (ctor 0x1b0918, ctor 0x1b0af4, IDaveSmith callback 0x1af61c); selector (7, 1, 1, 0x80)
    0x1b0994: "mov r3, #1", 0x1b099c: "strb r3, [r4, #0x98]", 0x1b0b80: "mov r2, #1", 0x1b0b88: "strb r2, [r4, #0x98]",
    0x1af638: "mov r3, #1", 0x1af63c: "strb r3, [r0, #0x98]",
    0x1b0bd0: "mov r1, #7", 0x1b0bd8: "mov ip, #0x80", 0x1b0be4: "bl #0xe6ee4",
    0x1af3a0: "ldr r0, [r0, #0xa4]", 0x1b0ce4: "ldrb r0, [r0, #0x140]",
    # HeadphoneUnit: four MuteSmoother(44, 0) (three cue + crossfade), crossfade setLength((int)(sr * 0.001))
    0x1b194c: "mov r1, #0x2c", 0x1b1958: "bl #0xe7fd8", 0x1b1988: "mov r1, #0x2c", 0x1b1994: "bl #0xe7fd8",
    0x1b19c4: "mov r1, #0x2c", 0x1b19d0: "bl #0xe7fd8", 0x1b1a00: "mov r1, #0x2c", 0x1b1a0c: "bl #0xe7fd8",
    0x1b0ec4: "vcvt.s32.f64 s15, d16", 0x1b0ed8: "b #0xe81e0", 0x1b1198: "bl #0x1b0ce4",
    # product graph: HeadphoneUnit(RoutingData, sys+0x5f0 BufferedAudioProcessor(0), sys+0x5d0 RecMonitorUnit + 0x80 = IMonitorMixer)
    0x1be744: "mov r1, #6", 0x1be764: "mov r1, #0", 0x1be770: "bl #0x1acf14", 0x1be7a0: "mov r1, #1", 0x1be7ac: "bl #0x1acf14",
    0x1be7e8: "bl #0x1ac134", 0x1bea60: "ldr r4, [r7, #0x5d0]", 0x1bea68: "ldr r6, [r7, #0x5f0]", 0x1bea70: "addne r4, r4, #0x80",
    0x1bea88: "bl #0x1b17b0", 0x1bef64: "bl #0x1b2d8c",
    # Output12Router ctor: OutputSelector(2, 1, 1, 0x80), forced selection 0x1b28f8(v, 1); setOutputMode 0x1b2d84 = 0x1b28f8(v, 0)
    0x1b2e00: "mov r2, #1", 0x1b2e04: "mov r1, #2", 0x1b2e0c: "mov ip, #0x80", 0x1b2e18: "bl #0xe6ee4", 0x1b2e70: "mov r2, #1",
    0x1b2d84: "mov r2, #0", 0x1b2d88: "b #0x1b28f8",
    # UI: ControllerData setOutputMode 0x2f6518 -> IAudioSystem slot 37 (+0x94); setHeadphoneSource 0x2f6be4 -> slot 39 (+0x9c) -> slot 2
    0x2f6538: "bl #0x32b664", 0x2f6544: "ldr r3, [r3, #0x94]", 0x2f6c5c: "bl #0x32b664", 0x2f6c64: "ldr r3, [r3, #0x9c]",
    0x2f6c74: "ldr r3, [r3, #8]",
}
VT_ISYS = 0x863f74


def insn_text(im, a):
    i = list(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a))[0]
    return "%s %s" % (i.mnemonic, i.op_str)


def id_table(im):
    """static initialiser 0x6cb20: stores of identifier-object pointers into the enum tables (base 0xf61f18): +0x218.. (paramId
    0x0d000000, Output12) and +0x220.. (0x0d000001, headphone source). Returns {table offset: identifier object address}."""
    import re
    lo, hi = im.func_of(0x6db1c); ins = im.disasm(lo, hi); out = {}
    for k, i in enumerate(ins):
        m = re.match(r"(\w+), \[(\w+), #(0x[0-9a-f]+)\]", i.op_str)
        if i.mnemonic == "str" and m and 0x218 <= int(m.group(3), 16) <= 0x250:
            for j in reversed(ins[k - 6:k]):
                mm = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", j.op_str)
                if j.mnemonic == "ldr" and mm and mm.group(1) == m.group(1):
                    out[int(m.group(3), 16)] = im.u32(j.address + 8 + int(mm.group(2), 0)); break
    return out


def static_section(im, P, check, J):
    P("\n== S static assertions (capstone)")
    bad = {hex(a): insn_text(im, a) for a, v in STATIC.items() if insn_text(im, a) != v}
    P("  %d instruction assertions: %s" % (len(STATIC), bad or "all match"))
    tab = id_table(im)
    o12 = [tab.get(0x218), tab.get(0x21c)]; hp = [tab.get(0x220 + 4 * i) for i in range(13)]
    ok_ids = o12 == [0xf53a10, 0xf53a24] and hp == sorted(HP_IDS, key=HP_IDS.get)
    P("  enum tables (static init 0x6cb20): Output12 [0x%x 'Master', 0x%x '4Assign']; headphone source %s" %
      (o12[0], o12[1], ["0x%x" % x for x in hp]))
    P("  identifier strings used by 0x1afbac: %s" % ([im.cstr(a, 12) for a in (0x862820, 0x86282c, 0x862834, 0x86283c, 0x862844)] +
                                                    [im.cstr(0x86284c + 8 * i, 6) for i in range(8)]))
    isys = {s: im.u32(VT_ISYS + 4 * s) for s in (37, 38, 39, 44)}
    dbl = struct.unpack("<d", struct.pack("<II", im.u32(0x1b0ee0), im.u32(0x1b0ee4)))[0]
    vt_r = {s: im.u32(0x8624dc + 4 * s) for s in (2, 3, 9, 10)}
    P("  IAudioSystem vt 0x863f74 slots 37/38/39/44 = %s (setOutputMode / getOutputMode / getHeadphoneRouter / getMonitorMixer thunks)"
      % {k: hex(v) for k, v in isys.items()})
    P("  HeadphoneRouter vt 0x8624dc slots 2/3/9/10 = %s; crossfade length literal %.6g" % ({k: hex(v) for k, v in vt_r.items()}, dbl))
    check(not bad and ok_ids and isys == {37: 0x1b94a8, 38: 0x1b9498, 39: 0x1b9488, 44: 0x1b9304} and dbl == 0.001 and
          vt_r == {2: 0x1b0770, 3: 0x1af3a0, 9: 0x1af518, 10: 0x1af3d8},
          "S: router +0x98 written only as 1; selectors (7,1,1,128)/(2,1,1,128); MuteSmoother(44) x4; crossfade len (int)(sr*0.001); "
          "graph args sys+0x5f0/sys+0x5d0+0x80; enum tables 0 CueMaster,1 Cue12..4 Cue78,5..12 Cue1..Cue8 / 0 Master,1 4Assign; UI setters")
    J["static"] = {"asserts": len(STATIC), "bad": bad, "hp_ids": [hex(x) for x in hp], "o12_ids": [hex(x) for x in o12]}


# =========================================================================================================== UI popup emulation
def ui_section(P, check, J):
    """REAL OutputSettingViewController popup handler 0x26fa50 and getHpCuePopupListRow 0x2720dc; ControllerData calls stubbed."""
    P("\n== C1b UI: popup handler 0x26fa50 (row -> source / mode) and getHpCuePopupListRow 0x2720dc (source -> row), both modes")
    rg = Rig(); e = rg.e; st = {"mode": 0, "hp": 0, "log": [], "assign": [0] * 16}
    def stub(a, fn): e.add_watch(a, lambda em: ret(em, fn(em)))
    stub(0x2ee918, lambda em: None); stub(0x7c1644, lambda em: None)
    stub(0x2f63dc, lambda em: st["mode"]); stub(0x2f6630, lambda em: st["hp"])
    stub(0x2f6518, lambda em: st["log"].append(("mode", em.r(1))))
    stub(0x2f6be4, lambda em: st["log"].append(("hp", em.r(1))))
    stub(0x2f7208, lambda em: st["assign"][em.r(1)]); stub(0x2f77d4, lambda em: st["log"].append(("trk", em.r(1), em.r(2))))
    w1 = rg.fk.obj("modePopup", {0x14: lambda em, nm: em.setr(0, 0)}); w2 = rg.fk.obj("hpPopup", {0x14: lambda em, nm: em.setr(0, 0)})
    this = e.malloc(0x600, "OutputSettingViewController"); e.wr(this, b"\0" * 0x600)
    e.w32(this + 0x4f4, w1); e.w32(this + 0x4f8, w2)
    rows = {}
    for mode in (0, 1):
        st["mode"] = mode; rows[mode] = []
        for row in range(14):
            st["log"] = []; e.call(0x26fa50, this, w2, row)
            rows[mode].append(st["log"][0][1] if st["log"] else None)
    inv = {}
    reach = {m: sorted(set(x for x in rows[m] if x is not None)) for m in (0, 1)}
    for mode in (0, 1):
        st["mode"] = mode; inv[mode] = {}
        for src in reach[mode]:                  # other combinations take the logging error path
            st["hp"] = src; inv[mode][src] = e.call(0x2720dc, this)[0]
    fix = {}
    for mode in (0, 1):
        for src in range(13):
            st["mode"] = 1 - mode; st["hp"] = src; st["log"] = []
            e.call(0x26fa50, this, w1, mode)
            fix[(mode, src)] = [x[1] for x in st["log"] if x[0] == "hp"]
    reach = {m: sorted(set(x for x in rows[m] if x is not None)) for m in (0, 1)}
    P("  HP CUE rows -> source index: mode 0 'Master' (M + 6ch) %s; mode 1 '4Assign' (8ch) %s" % (rows[0][:12], rows[1][:12]))
    P("  reachable sources: Master mode %s; 4Assign mode %s" % ([HM.SOURCE_NAMES[i] for i in reach[0]], [HM.SOURCE_NAMES[i] for i in reach[1]]))
    rt = all(inv[m][s] == rows[m].index(s) for m in (0, 1) for s in reach[m])
    P("  getHpCuePopupListRow round trip on the reachable set: %s" % rt)
    P("  output-mode change auto-correction of the HP source: to Master: %s; to 4Assign: %s" %
      ({HM.SOURCE_NAMES[s]: HM.SOURCE_NAMES[v[0]] for (m, s), v in fix.items() if m == 0 and v},
       {HM.SOURCE_NAMES[s]: HM.SOURCE_NAMES[v[0]] for (m, s), v in fix.items() if m == 1 and v}))
    exp0 = [0, 2, 3, 4, 7, 8, 9, 10, 11, 12]; exp1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    ok = (rows[0][:10] == exp0 and all(x is None for x in rows[0][10:]) and rows[1][:12] == exp1 and all(x is None for x in rows[1][12:])
          and rt and {s for (m, s), v in fix.items() if m == 0 and v == [0]} == {1, 5, 6}
          and {s for (m, s), v in fix.items() if m == 1 and v == [1]} == {0})
    check(ok, "C1b: UI rows: Master mode -> {CueMaster, Cue34, Cue56, Cue78, Cue3..Cue8}; 4Assign mode -> {Cue12, Cue34, Cue56, Cue78, "
              "Cue1..Cue8}; switching to Master turns Cue12/Cue1/Cue2 into CueMaster, switching to 4Assign turns CueMaster into Cue12")
    J["ui"] = {"rows": rows, "reach": reach, "fix": {"%d:%d" % k: v for k, v in fix.items()}}
    return reach


# =========================================================================================================== helpers
DC20 = [F(2.0 ** -(k + 1)) for k in range(20)]          # inputs 0..13 = HP in, 14..19 = cue ch 0..5 (distinct powers of two)


def decode(v):
    """value = sum of distinct DC20 terms -> list of input labels (exact in float32)."""
    out = []; x = v
    for k in range(20):
        if x >= DC20[k]: out.append(("in%d" % k) if k < 14 else ("cue%d" % (k - 14))); x -= DC20[k]
    return out if abs(x) < 2.0 ** -22 else out + ["?%g" % x]


def sigs(rng, b, nch, salt):
    out = []
    for c in range(nch):
        kind = (c + salt) % 4
        row = []
        for i in range(N):
            t = b * N + i
            if kind == 0: v = (0.2 + 0.05 * c) * math.sin(2 * math.pi * (150 + 37 * c) * t / 44100.0)
            elif kind == 1: v = rng.uniform(-0.6, 0.6)
            elif kind == 2: v = [0.5, -0.25, 0.125, 0.75, -0.5][(t // (90 + 7 * c)) % 5] * (1 if c % 2 else -1)
            else: v = 0.3 * math.cos(2 * math.pi * (61 + 13 * c) * t / 44100.0) + 0.1
            row.append(F(v))
        out.append(row)
    return out


def bits(xs): return b"".join(struct.pack("<f", x) for x in xs)


# =========================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H057"))
    ap.add_argument("--blocks", type=int, default=1000, help="random-scenario blocks per routine in C4 (x 128 output samples)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []; f32 = {}

    def P(s_=""): rep.append(s_); print(s_, flush=True)

    def check(c, msg):
        P(("PASS " if c else "FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    P("H057 headphone cue mix / main-output selector — target sha256 %s" % emu.SHA)
    static_section(im, P, check, J)

    # ------------------------------------------------------------------------------------------------ C1 setHeadphoneSource
    P("\n== C1 setHeadphoneSource 0x1afbac (REAL, via router vt slot 2 0x1b0770): OutputSelector target, CueMaster flag +0x140")
    rg = HPRig(); rg.build(0)
    tgt, cur, m140, f98 = rg.sel_state()
    P("  after the REAL ctor (RoutingData source 0): router +0x98 = %d, target %s, current %s, +0x140 = %d" % (f98, tgt, cur, m140))
    c1 = {}
    for flag in (1, 0):
        e = rg.e
        e.wr(rg.router + 0x98, bytes([flag]))
        for idx in list(range(13)) + [13]:
            rg.vlog = []
            if idx == 13: rg.set_source(4)
            rg.set_source(idx)
            t_, c_, m_, f_ = rg.sel_state()
            c1[(flag, idx)] = (t_, m_, e.u32(rg.router + 0xa4), rg.vlog[-1][1] if rg.vlog else None)
        P("  +0x98 = %d%s: %s" % (flag, " (as built; every writer stores 1)" if flag else " (forced; unreachable alternative)",
                                  ", ".join("%s %s%s" % (HM.SOURCE_NAMES[i] if i < 13 else "idx13", c1[(flag, i)][0],
                                                         " M" if c1[(flag, i)][1] else "") for i in range(14))))
    ok = all(c1[(f, i)][0] == HM.SOURCE_PAIRS[i][0 if f == 0 else 1] and c1[(f, i)][1] == HM.SOURCE_PAIRS[i][2] and
             c1[(f, i)][2] == i and c1[(f, i)][3] == i for f in (0, 1) for i in range(13))
    unk = c1[(1, 13)]
    P("  unknown index 13 (after Cue78): target stays %s, +0x140 = %d, +0xa4 = %d, RoutingData written %s" % (unk[0], unk[1], unk[2], unk[3]))
    check(ok and unk[0] == (10, 11) and unk[1] == 0 and f98 == 1,
          "C1: 13 sources -> pairs (as built): CueMaster/Cue12 (2,3) [CueMaster sets +0x140], Cue34 (6,7), Cue56 (8,9), Cue78 (10,11), "
          "Cue1 (2,-) Cue2 (-,3) Cue3 (6,-) Cue4 (7,-) Cue5 (8,-) Cue6 (9,-) Cue7 (10,-) Cue8 (11,-); +0x98 = 0 would give CueMaster (0,1), "
          "Cue12 (4,5), Cue1 (4,-), Cue2 (-,5); the index is written back to RoutingData+0x28 and +0xa4")
    J["c1"] = {"%d:%d" % k: [list(v[0]), v[1], v[2], v[3]] for k, v in c1.items()}
    reach = ui_section(P, check, J)

    # ------------------------------------------------------------------------------------------------ C2 processBlock law
    P("\n== C2 HeadphoneUnit REAL ctor 0x1b17b0 + prepareToPlay 0x1b0d94 + processBlock 0x1b10ec (64-sample blocks)")
    ins_dc = [[DC20[k]] * N for k in range(14)]; cue_dc = [[DC20[14 + k]] * N for k in range(6)]
    mat = {}; mdl_ok = True
    configs = [(s, (0, 0, 0), 0) for s in range(13)] + [(0, (1, 0, 1), 0), (0, (1, 1, 1), 0), (2, (1, 1, 1), 0), (0, (0, 0, 0), 1),
                                                       (7, (0, 0, 0), 1)]
    for s, gates, xf in configs:
        r = HPRig(); r.build(s); r.gates = list(gates); r.xf = xf
        md = HM.HeadphoneUnit(s)
        for b in range(6):
            o = r.block(ins_dc, cue_dc); om = md.process(ins_dc, cue_dc, gates, xf)
            mdl_ok &= bits(o[0] + o[1]) == bits(om[0] + om[1])
        mat[(s, gates, xf)] = (decode(o[0][-1]), decode(o[1][-1]))
    for (s, g, x), (l, rr) in mat.items():
        P("  %-9s gates %s xfade %d:  L = %s   R = %s" % (HM.SOURCE_NAMES[s], g, x, " + ".join(l), " + ".join(rr)))
    allcue_l = ["cue0", "cue2", "cue4"]; allcue_r = ["cue1", "cue3", "cue5"]
    exp_ok = True
    for (s, g, x), (l, rr) in mat.items():
        if x:
            exp_ok &= (l, rr) == (["in11"], ["in12"]); continue
        a_, b_ = HM.SOURCE_PAIRS[s][1]
        sl = ["in%d" % (a_ if a_ >= 0 else b_)]; sr = ["in%d" % (b_ if b_ >= 0 else a_)]
        gl = [c for k, c in enumerate(allcue_l) if not (HM.SOURCE_PAIRS[s][2] and g[k])]
        gr = [c for k, c in enumerate(allcue_r) if not (HM.SOURCE_PAIRS[s][2] and g[k])]
        exp_ok &= l == sorted(sl + gl, key=lambda z: (z[:2] != "in", int(z[2:] if z[:2] == "in" else z[3:]))) and \
            rr == sorted(sr + gr, key=lambda z: (z[:2] != "in", int(z[2:] if z[:2] == "in" else z[3:])))
    check(exp_ok and mdl_ok,
          "C2a gain matrix (steady state, knob 127 = x1.0): L/R = selected pair (mono sources duplicated) + the three monitor pairs at gain "
          "1.0; with CueMaster a monitor pair is removed iff IMonitorMixer slot 4(k,0) = 1 (other sources ignore it); crossfade on -> "
          "L = in11, R = in12; in0/1 (master copy) and in13 never reach the output; model bit-exact on all %d configs" % len(configs))
    J["c2_matrix"] = {"%s|%s|%d" % (HM.SOURCE_NAMES[s], g, x): v for (s, g, x), v in mat.items()}

    # shapes: selector switch, A->B->A, cue gate, crossfade, knob
    def run(r, md, nb, gates=(0, 0, 0), xf=0, ins=ins_dc, cue=cue_dc):
        out = []; om_ = []
        for b in range(nb):
            o = r.block(ins, cue); om = md.process(ins, cue, gates, xf); out.append(o); om_.append(om)
        return out, om_
    one = [[0.0] * N for _ in range(14)]; one[6] = [1.0] * N; one[8] = [0.5] * N; one[11] = [0.25] * N; one[12] = [-0.25] * N
    zc = [[0.0] * N for _ in range(6)]
    r = HPRig(); r.build(2); md = HM.HeadphoneUnit(2); run(r, md, 6, ins=one, cue=zc)
    r.set_source(3); md.router.set_source(3)
    sw, swm = run(r, md, 5, ins=one, cue=zc); swL = sum((o[0] for o in sw), []); swmL = sum((o[0] for o in swm), [])
    P("  selector switch Cue34 (in6 = 1.0) -> Cue56 (in8 = 0.5) at a block boundary: L[0] %.6g L[64] %.6g L[127] %.6g L[128] %.6g "
      "L[129] %.6g L[192] %.6g L[255] %.6g L[256] %.6g" % tuple(swL[i] for i in (0, 64, 127, 128, 129, 192, 255, 256)))
    dip = abs(swL[64] - 0.5) < 1e-6 and swL[128] == 0.0 and abs(swL[192] - 0.25) < 1e-6 and swL[256] == 0.5
    r.set_source(2); md.router.set_source(2); q1, q1m = run(r, md, 1, ins=one, cue=zc)     # current = Cue56: start a switch to Cue34
    r.set_source(3); md.router.set_source(3); q2, q2m = run(r, md, 6, ins=one, cue=zc)     # ... and go back to Cue56 mid fade-out
    stuck = all(x == 0.0 for x in q2[-1][0])
    P("  A->B->A within one block of the fade-out (Cue56 -> Cue34 -> Cue56): last L block all zero = %s (gain stays 0 until the next "
      "change: selector only fades in after switching pairs)" % stuck)
    r2 = HPRig(); r2.build(0); md2 = HM.HeadphoneUnit(0); cue1 = [[1.0] * N] + [[0.0] * N] * 5
    run(r2, md2, 6, ins=[[0.0] * N] * 14, cue=cue1)
    r2.gates = [1, 0, 0]; g1, g1m = run(r2, md2, 2, gates=(1, 0, 0), ins=[[0.0] * N] * 14, cue=cue1)
    gL = g1[0][0] + g1[1][0]
    P("  cue gate 0 closing (CueMaster): L[0] %.6g L[22] %.6g L[43] %.6g L[44] %.6g -> 44-sample linear MuteSmoother" % (gL[0], gL[22], gL[43], gL[44]))
    gate_ok = gL[0] == 1.0 and abs(gL[22] - 0.5) < 1e-6 and abs(gL[43] - 1 / 44.0) < 1e-6 and gL[44] == 0.0
    r3 = HPRig(); r3.build(2); md3 = HM.HeadphoneUnit(2); run(r3, md3, 6, ins=one, cue=zc)
    r3.xf = 1; x1, x1m = run(r3, md3, 2, xf=1, ins=one, cue=zc); xL = x1[0][0] + x1[1][0]
    r3.xf = 0; x2, x2m = run(r3, md3, 2, xf=0, ins=one, cue=zc); xL2 = x2[0][0] + x2[1][0]
    P("  crossfade on (in6 = 1.0 -> in11 = 0.25): L[0] %.6g L[22] %.6g L[44] %.6g; off again: L[0] %.6g L[22] %.6g L[44] %.6g" %
      (xL[0], xL[22], xL[44], xL2[0], xL2[22], xL2[44]))
    xf_ok = xL[0] == 1.0 and abs(xL[22] - 0.625) < 1e-6 and xL[44] == 0.25 and xL2[0] == 0.25 and xL2[44] == 1.0
    knob = {}
    for idx in (0, 1, 10, 50, 100, 127):
        rk = HPRig(); rk.build(2); rk.e.call(VOL_SET, rk.knob, idx); mk = HM.HeadphoneUnit(2); mk.knob.set(idx)
        o, om = run(rk, mk, 6, ins=one, cue=zc); knob[idx] = (o[-1][0][-1], TM.knob_gain(idx), bits(sum((x[0] + x[1] for x in o), [])) ==
                                                                bits(sum((x[0] + x[1] for x in om), [])))
    P("  VolumeKnob DC gain (in6 = 1.0): %s" % ", ".join("%d -> %.7g (table*0.5 %.7g)" % (k, v[0], v[1]) for k, v in knob.items()))
    rk = HPRig(); rk.build(2); mk = HM.HeadphoneUnit(2); run(rk, mk, 6, ins=one, cue=zc)
    rk.e.call(VOL_SETOFF, rk.knob, 64, 17); mk.knob.set(64, 17); kr, krm = run(rk, mk, 3, ins=one, cue=zc)
    kL = sum((o[0] for o in kr), []); tg = TM.knob_gain(64)
    lin = all(abs(kL[17 + k] - (1.0 + (tg - 1.0) * k / 100.0)) < 3e-6 for k in range(100)) and kL[16] == 1.0 and kL[117] == tg
    rk.e.call(VOL_SET, rk.knob, 100); mk.knob.set(100); kp, kpm = run(rk, mk, 1, ins=one, cue=zc)
    persist = kp[0][0][17] == kp[0][0][0] and kp[0][0][18] != kp[0][0][0]
    P("  knob slot 3 (64, offset 17): L[16] %.7g L[17] %.7g L[67] %.7g L[117] %.7g (target %.7g): linear 100 samples from the offset %s; "
      "later slot 2 (100) ramps from the stale offset 17: %s" % (kL[16], kL[17], kL[67], kL[117], tg, lin, persist))
    shapes_model = all(bits(sum((o[0] + o[1] for o in A_), [])) == bits(sum((o[0] + o[1] for o in B_), []))
                       for A_, B_ in ((sw, swm), (q1, q1m), (q2, q2m), (g1, g1m), (x1, x1m), (x2, x2m), (kr, krm), (kp, kpm)))
    check(dip and stuck and gate_ok and xf_ok and lin and persist and all(v[2] and v[0] == v[1] for v in knob.values()) and shapes_model,
          "C2b shapes: source switch = 128-sample linear fade-out of the old pair then 128-sample fade-in of the new one (a dip); "
          "re-selecting the old pair during the fade-out leaves the output silent; cue gates and the audio-input crossfade are linear "
          "over 44 samples; VolumeKnob = table[i]*0.5 with a 100-sample ramp from the (persisting) offset; model bit-exact on all shapes")
    J["c2_shapes"] = {"switch": [swL[i] for i in (0, 64, 127, 128, 192, 256)], "stuck": stuck, "gate": [gL[0], gL[22], gL[44]],
                      "xf": [xL[0], xL[22], xL[44]], "knob": {k: v[0] for k, v in knob.items()}, "ramp": [kL[16], kL[17], kL[67], kL[117]]}
    f32["c2_switch"] = swL; f32["c2_knob_ramp"] = kL

    # ------------------------------------------------------------------------------------------------ C3 Output12Router
    P("\n== C3 Output12Router REAL ctor 0x1b2d8c + selection 0x1b28f8 / setOutputMode 0x1b2d84 + processBlock 0x1b2610")
    ins4 = [[1.0] * N, [-0.5] * N, [0.25] * N, [-0.125] * N]
    o3 = {}
    for mode in (0, 1):
        q = O12Rig(); q.build(mode); mq = HM.Output12Router(mode)
        oo = [q.block(ins4) for _ in range(5)]; om = [mq.process(ins4) for _ in range(5)]
        o3[mode] = (q.sel_state(), oo[-1][0][-1], oo[-1][1][-1], bits(sum((x[0] + x[1] for x in oo), [])) == bits(sum((x[0] + x[1] for x in om), [])))
    P("  ctor with RoutingData 0 'Master': selector %s -> out (%.4g, %.4g); with 1 '4Assign': selector %s -> out (%.4g, %.4g)" %
      (o3[0][0], o3[0][1], o3[0][2], o3[1][0], o3[1][1], o3[1][2]))
    q = O12Rig(); q.build(0); mq = HM.Output12Router(0); [q.block(ins4) for _ in range(2)]; [mq.process(ins4) for _ in range(2)]
    q.vlog = []; q.e.call(O12_SETMODE, q.obj, 1); mq.set_mode(1)
    s3 = [q.block(ins4) for _ in range(5)]; s3m = [mq.process(ins4) for _ in range(5)]; sL = sum((x[0] for x in s3), [])
    P("  switch Master -> 4Assign: L[0] %.6g L[64] %.6g L[128] %.6g L[192] %.6g L[256] %.6g (RoutingData+0x24 <- %s)" %
      (sL[0], sL[64], sL[128], sL[192], sL[256], [v for _, v in q.vlog]))
    q.vlog = []; q.e.call(O12_SETMODE, q.obj, 1); same = (q.vlog == [])
    q.e.call(O12_SETMODE, q.obj, 2); mq.set_mode(1); mq.set_mode(2); t2 = q.sel_state()
    s4 = [q.block(ins4) for _ in range(3)]; s4m = [mq.process(ins4) for _ in range(3)]
    P("  same value unforced: no write (%s); value 2: selector stays %s, RoutingData <- %s" % (same, t2, [v for _, v in q.vlog]))
    q.e.call(O12_SETMODE, q.obj, 0); mq.set_mode(0); s5 = [q.block(ins4)]; s5m = [mq.process(ins4)]
    q.e.call(O12_SETMODE, q.obj, 1); mq.set_mode(1); s6 = [q.block(ins4) for _ in range(6)]; s6m = [mq.process(ins4) for _ in range(6)]
    o_stuck = all(x == 0.0 for x in s6[-1][0])
    P("  4Assign -> Master -> 4Assign within one block: last block silent = %s (same selector quirk)" % o_stuck)
    s4 += s5 + s6; s4m += s5m + s6m
    o12_ok = (o3[0][0] == ((0, 1), (0, 1)) and o3[0][1:3] == (1.0, -0.5) and o3[1][0][0] == (2, 3) and o3[1][1:3] == (0.25, -0.125) and
              abs(sL[64] - 0.5) < 1e-6 and sL[128] == 0.0 and abs(sL[192] - 0.125) < 1e-6 and sL[256] == 0.25 and same and
              t2[0] == (2, 3) and o_stuck and all(v[3] for v in o3.values()) and
              bits(sum((x[0] + x[1] for x in s3 + s4), [])) == bits(sum((x[0] + x[1] for x in s3m + s4m), [])))
    check(o12_ok, "C3: Output12Router: 'Master' (0) -> main = in0/1 (master), '4Assign' (1) -> main = in2/3 (MTU out6/7); switch = "
                  "128-sample fade-out + 128-sample fade-in; unforced same value ignored; other values leave the selection; model bit-exact")
    J["c3"] = {"modes": {m: [list(v[0][0]), v[1], v[2]] for m, v in o3.items()}, "switch": [sL[i] for i in (0, 64, 128, 192, 256)]}
    f32["c3_switch"] = sL

    # ------------------------------------------------------------------------------------------------ C4 random model comparison
    P("\n== C4 model harness/models/headphone_mix.py vs emulation (random scenarios, %d blocks per routine)" % a.blocks)
    rng = random.Random(42057)
    hp_bad = hp_n = 0; hp_out = []; ev = {"src": 0, "gate": 0, "xf": 0, "k2": 0, "k3": 0}
    runs = 4; per = a.blocks // runs
    for run_i in range(runs):
        s0 = rng.choice(reach[run_i % 2]); r = HPRig(); r.build(s0); md = HM.HeadphoneUnit(s0)
        for b in range(per):
            if rng.random() < 0.10:
                s = rng.choice(reach[run_i % 2]); r.set_source(s); md.router.set_source(s); ev["src"] += 1
            if rng.random() < 0.12:
                k = rng.randrange(3); r.gates[k] ^= 1; ev["gate"] += 1
            if rng.random() < 0.06:
                r.xf ^= 1; ev["xf"] += 1
            if rng.random() < 0.08:
                i_ = rng.choice([0, 127, rng.randrange(128)]); r.e.call(VOL_SET, r.knob, i_); md.knob.set(i_); ev["k2"] += 1
            if rng.random() < 0.08:
                i_ = rng.choice([0, 127, rng.randrange(128)]); off = rng.choice([0, 1, 17, 63, 64, 90, rng.randrange(130)])
                r.e.call(VOL_SETOFF, r.knob, i_, off); md.knob.set(i_, off); ev["k3"] += 1
            ins = sigs(rng, b, 14, run_i); cue = sigs(rng, b, 6, run_i + 1)
            o = r.block(ins, cue); om = md.process(ins, cue, tuple(r.gates), r.xf)
            ob, mb = bits(o[0] + o[1]), bits(om[0] + om[1])
            hp_n += 2 * N; hp_bad += sum(ob[4 * i:4 * i + 4] != mb[4 * i:4 * i + 4] for i in range(2 * N)); hp_out.append(ob)
    o_bad = o_n = 0; o_out = []; oev = 0
    for run_i in range(2):
        m0 = run_i; q = O12Rig(); q.build(m0); mq = HM.Output12Router(m0)
        for b in range(a.blocks // 2):
            if rng.random() < 0.12:
                v = rng.choice([0, 1, 0, 1, 2]); q.e.call(O12_SETMODE, q.obj, v); mq.set_mode(v); oev += 1
            if rng.random() < 0.03:
                v = rng.choice([0, 1]); q.e.call(O12_SEL, q.obj, v, 1); mq.set_mode(v, force=True); oev += 1
            ins = sigs(rng, b, 4, run_i + 2)
            o = q.block(ins); om = mq.process(ins)
            ob, mb = bits(o[0] + o[1]), bits(om[0] + om[1])
            o_n += 2 * N; o_bad += sum(ob[4 * i:4 * i + 4] != mb[4 * i:4 * i + 4] for i in range(2 * N)); o_out.append(ob)
    hph, oh = sha(b"".join(hp_out)), sha(b"".join(o_out))
    P("  HeadphoneUnit: %d output samples, %d differ; events %s; emulated output sha256 %s" % (hp_n, hp_bad, ev, hph))
    P("  Output12Router: %d output samples, %d differ; %d selection events; emulated output sha256 %s" % (o_n, o_bad, oev, oh))
    check(hp_bad == 0 and o_bad == 0 and hp_n >= 100000 and o_n >= 100000,
          "C4: model bit-exact (float32) to the emulated 1.60 routines on >= 1e5 output samples each, with source/selection switches, "
          "gate and crossfade toggles, knob slot 2/3 changes (offsets 0..129, indices incl. 0 and 127)")
    J["c4"] = {"hp_samples": hp_n, "hp_differ": hp_bad, "hp_sha": hph, "o12_samples": o_n, "o12_differ": o_bad, "o12_sha": oh, "events": ev}
    f32["c4_hp"] = None; f32["c4_o12"] = None
    open(os.path.join(a.out, "c4_hp.f32"), "wb").write(b"".join(hp_out)); open(os.path.join(a.out, "c4_o12.f32"), "wb").write(b"".join(o_out))

    # ------------------------------------------------------------------------------------------------ C5 alternatives
    P("\n== C5 alternative laws (model variants) vs the same emulated scenario (300 blocks): each must mismatch")
    class MixMaster(HM.HeadphoneUnit):          # H057 text: master copy in0/1 mixed with the cue pairs
        def process(self, ch14, cue6, gates=(0, 0, 0), xfade=0):
            o = super().process(ch14, cue6, gates, xfade)
            g = TM.knob_gain(self.knob.index)
            return [[F(x + F(F(a) * g)) for x, a in zip(o[0], ch14[0])], [F(x + F(F(a) * g)) for x, a in zip(o[1], ch14[1])]]
    class GatesAlways(HM.HeadphoneUnit):        # monitor gates applied for every source (ignore +0x140)
        def process(self, ch14, cue6, gates=(0, 0, 0), xfade=0):
            m = self.router.master; self.router.master = 1
            try: return super().process(ch14, cue6, gates, xfade)
            finally: self.router.master = m
    def flag0(s): return HM.HeadphoneUnit(s, flag98=0)
    def xf132(s):
        u = HM.HeadphoneUnit(s); u.xf.__init__(132, 0); return u
    def instant(s):
        u = HM.HeadphoneUnit(s); u.router.sel.sm = TM.Smoother(1, 1.0); return u
    variants = {"model": HM.HeadphoneUnit, "master copy mixed in (H057 text)": MixMaster, "router +0x98 = 0 (CueMaster = in0/1)": flag0,
                "monitor gates for every source": GatesAlways, "crossfade 132 samples": xf132, "selector switch without fade": instant}
    rng = random.Random(5705); s0 = 0; r = HPRig(); r.build(s0); mods = {k: f(s0) for k, f in variants.items()}; bad = {k: 0 for k in variants}
    for b in range(300):
        if rng.random() < 0.10:
            sx = rng.choice(reach[0]); r.set_source(sx); [m.router.set_source(sx) for m in mods.values()]
        if rng.random() < 0.12: r.gates[rng.randrange(3)] ^= 1
        if rng.random() < 0.06: r.xf ^= 1
        if rng.random() < 0.08:
            i_ = rng.randrange(128); r.e.call(VOL_SET, r.knob, i_); [m.knob.set(i_) for m in mods.values()]
        ins = sigs(rng, b, 14, 0); cue = sigs(rng, b, 6, 1)
        ob = bits(sum(r.block(ins, cue), []))
        for k, m in mods.items():
            mb = bits(sum(m.process(ins, cue, tuple(r.gates), r.xf), [])); bad[k] += sum(ob[4 * i:4 * i + 4] != mb[4 * i:4 * i + 4] for i in range(2 * N))
    for k, v in bad.items(): P("  %-40s %6d of %d samples differ" % (k, v, 300 * 2 * N))
    check(bad["model"] == 0 and all(v > 0 for k, v in bad.items() if k != "model"),
          "C5: only the documented law matches; the H057-text 'master copy mixed in', CueMaster = in0/1, gates for all sources, a 132-sample "
          "crossfade and an unfaded selector switch are all refuted by the emulation")
    J["c5"] = bad

    for k, v in f32.items():
        if v is not None: open(os.path.join(a.out, k + ".f32"), "wb").write(bits(v))
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h057_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h057.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
