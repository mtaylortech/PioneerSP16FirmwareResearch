#!/usr/bin/env python3
"""H010 — send bus, Send FX return and master-side graph connections in 1.60 (kb/cycles/019.md).

Sections (criteria of cycle 019):
  C1  graph connections: linear symbolic walk (harness/lib/symwalk.py) of the graph build 0x1bc8d4 and its connection helpers; every
      connectPair/addConnection call decoded to source node/channels -> destination node/channels and asserted against the expected
      table; node classes (vptr-1 -> typeinfo name), channel counts (setPlayConfigDetails 0x5f9e90 arguments), canConnect checks.
  C2  CompositeFxUnit::processBlock 0x1a94cc (REAL) with stand-in Master/Send units, inline and pooled paths, distinct signals per input.
  C3  SendFxUnit::processBlock 0x1b3068 (REAL) with a stand-in processor and the REAL return VolumeFader (Volume::processBlock 0xe9b70,
      slot 13 table) on >= 5 indices; SendFxProcessor::processBlock 0x119994 (REAL) front end with no effect pending (MuteSmoother).
  C4  MasterOutUnit::processBlock 0x1b2150 (REAL) with the REAL SimpleTwoMixUnit 0x1535f8 (6 ch) and REAL master VolumeFader.
  C5  model harness/models/bus_mix.py vs the emulated chain CompositeFxUnit -> (real SendFxUnit) -> MasterOutUnit, >= 6 settings x
      {impulse, sine, noise, steps}, 60 blocks, mid-run fader changes through the real Volume setters.
  C7  alternatives: model mutants (return before Master FX, separate output, return pre-fader, no return fader) must fail.
Outputs only to --out (default harness/out/H010/). Run: .venv/bin/python -B harness/H010_send_bus.py --out DIR [--regress]
"""
import argparse, hashlib, json, math, os, random, re, struct, sys, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
import sp16img                                                 # noqa: E402
from symwalk import Walker, State, U                           # noqa: E402
import H009_track_mix as h9                                    # noqa: E402  (AudioBuf, Fakes, sig, guard stubs, regress list)
import track_mix as TM                                         # noqa: E402
import bus_mix as BM                                           # noqa: E402

N = 64
F = TM.F
AB_CTOR = 0x576998
VT_FADER, VT_FADER2 = 0x83e380, 0x83e3c0
VT_STMU, VT_SENDFXUNIT, VT_MASTEROUT, VT_COMPOSITE = 0x849010, 0x862e28, 0x862a58, 0x861854
CF_PB, SFU_PB, MOU_PB, SFP_PB, JOB_RUN = 0x1a94cc, 0x1b3068, 0x1b2150, 0x119994, 0x153980
MUTE_SM_CTOR, SMOOTH_CTOR = 0xe7fd8, 0xe8900


def sha(b): return hashlib.sha256(b).hexdigest()
def bits(xs): return [f2u(x) for x in xs]


# =========================================================================================================== C1 static decode
NODE_NAMES = ["multiTrackUnitNode", "liveSamplingNode", "compositeFxUnitNode", "masterOutUnitNode", "headphoneUnitNode",
              "masterAssignableSelectorNode", "dsfDriveMasterNode", "dsfDriveSendNode"]
IN_HELPERS = {0x1b7480: (0, 1), 0x1b76a0: (2, 3), 0x1b77b0: (4, 5), 0x1b7590: (6, 7)}
OUT_HELPERS = {0x1b78c0: [(0, 1), (12, 13)], 0x1b7ab0: [(2, 3)], 0x1b7bc0: [(4, 5)], 0x1b7cd0: [(6, 7)], 0x1b7de0: [(8, 9)],
               0x1b7ef0: [(10, 11)]}
EXPECTED = [   # (site, src, src pair, dst, dst pair)
    (0x1bda9c, "audioIn", (0, 1), "multiTrackUnit", (0, 1)), (0x1bdac4, "audioIn", (2, 3), "multiTrackUnit", (2, 3)),
    (0x1bdaec, "audioIn", (4, 5), "multiTrackUnit", (4, 5)), (0x1bdc3c, "audioIn", (0, 1), "liveSampling", (0, 1)),
    (0x1be3ec, "multiTrackUnit", (0, 1), "compositeFxUnit", (0, 1)), (0x1be448, "multiTrackUnit", (2, 3), "compositeFxUnit", (2, 3)),
    (0x1be9a0, "compositeFxUnit", (0, 1), "masterOutUnit", (0, 1)), (0x1bea04, "compositeFxUnit", (2, 3), "masterOutUnit", (2, 3)),
    (0x1bea5c, "multiTrackUnit", (14, 15), "masterOutUnit", (4, 5)), (0x1bed4c, "masterOutUnit", (2, 3), "headphoneUnit", (0, 1)),
    (0x1beda0, "audioIn", (2, 3), "headphoneUnit", (2, 3)), (0x1bedf4, "multiTrackUnit", (6, 7), "headphoneUnit", (4, 5)),
    (0x1bee4c, "multiTrackUnit", (8, 9), "headphoneUnit", (6, 7)), (0x1beea4, "multiTrackUnit", (10, 11), "headphoneUnit", (8, 9)),
    (0x1beefc, "multiTrackUnit", (12, 13), "headphoneUnit", (10, 11)), (0x1bef50, "audioIn", (0, 1), "headphoneUnit", (11, 12)),
    (0x1bf0d0, "masterOutUnit", (0, 1), "masterAssignableSelector", (0, 1)),
    (0x1bf104, "multiTrackUnit", (6, 7), "masterAssignableSelector", (2, 3)),
    (0x1bf408, "masterAssignableSelector", (0, 1), "dsfDriveMaster", (0, 1)),
    (0x1bf464, "multiTrackUnit", (4, 5), "dsfDriveSend", (0, 1)),
    (0x1bf474, "dsfDriveMaster", (0, 1), "audioOut", (0, 1)), (0x1bf474, "dsfDriveMaster", (0, 1), "audioOut", (12, 13)),
    (0x1bf4a0, "multiTrackUnit", (8, 9), "audioOut", (2, 3)), (0x1bf4cc, "multiTrackUnit", (10, 11), "audioOut", (4, 5)),
    (0x1bf4f8, "multiTrackUnit", (12, 13), "audioOut", (6, 7)), (0x1bf508, "headphoneUnit", (0, 1), "audioOut", (8, 9)),
    (0x1bf518, "dsfDriveSend", (0, 1), "audioOut", (10, 11)),
    (0x1bf530, "audioIn", "midi", "liveSampling", "midi"), (0x1bf544, "liveSampling", "midi", "multiTrackUnit", "midi"),
    (0x1bf55c, "masterOutUnit", "midi", "audioOut", "midi"),
]
NODE_CLASS = {  # node -> (sys offset, ctor, expected class name, (in, out), processBlock = vtable slot 5)
    "multiTrackUnit": (0x6a0, 0x1c67e4, "MultiTrackUnit", (6, 16), 0x1c4ff8),
    "compositeFxUnit": (0x698, 0x1aa808, "CompositeFxUnit", (4, 4), 0x1a94cc),
    "masterOutUnit": (0x6a4, 0x1b2398, "MasterOutUnit", (6, 4), 0x1b2150),
    "headphoneUnit": (0x69c, 0x1b17b0, "HeadphoneUnit", (14, 2), 0x1b10ec),
    "masterAssignableSelector": (0x6a8, 0x1b2d8c, "Output12Router", (4, 2), 0x1b2610),
    "dsfDriveMaster": (0x6ac, 0xc3ed0, "DaveSmithDriveUnit", (2, 2), 0xc3ce8),
    "dsfDriveSend": (0x6b0, 0xc3ed0, "DaveSmithDriveUnit", (2, 2), 0xc3ce8),
    "liveSampling": (0x5a0, 0x13d7e8, "LiveSampling", (2, None), None),
}


def static_c1(im, P, check, J):
    P("\n== C1 graph connections (static, symbolic walk of 0x1bc8d4)")
    conns = []; nodes = []

    def pairval(st, p):
        if p[0] == "lit": return (("mem", p[1]), ("mem", p[1] + 4))
        if p[0] == "sp": return (st.stack.get(p[1], U), st.stack.get(p[1] + 4, U))
        if p[0] == "base" and p[1] == "sys": return ("sysptr", p[2])
        return (U, U)

    def h_str(st, site):
        a, b = st.r.get("r0", U), st.r.get("r1", U)
        if a[0] == "sp" and b[0] == "lit": st.stack[a[1]] = ("str", im.cstr(b[1], 80))

    def h_node(st, site):
        n = st.r.get("r2", U); s = st.stack.get(n[1], U) if n[0] == "sp" else U
        name = s[1] if s[0] == "str" else "?"
        nodes.append((site, name)); return ("node", name)

    def h_conn(st, site):
        conns.append((site, st.r.get("r1"), pairval(st, st.r.get("r2", U)), st.r.get("r3"), pairval(st, st.stack.get(0, U))))

    def mk_in(pair):
        return lambda st, site: conns.append((site, ("io", "audioIn"), ("lit2", pair), st.r.get("r1"), pairval(st, st.r.get("r2", U))))

    def mk_out(pairs):
        def h(st, site):
            for p in pairs: conns.append((site, st.r.get("r1"), pairval(st, st.r.get("r2", U)), ("io", "audioOut"), ("lit2", p)))
        return h

    def h_midi(st, site):
        conns.append((site, st.r.get("r1"), "midi", st.r.get("r2"), "midi"))
    calls = {0x64a3fc: h_str, 0x1b6020: h_node, 0x1b61bc: h_conn, 0x1b7380: h_midi}
    calls.update({a: mk_in(p) for a, p in IN_HELPERS.items()}); calls.update({a: mk_out(p) for a, p in OUT_HELPERS.items()})
    st = State(); st.r["r0"] = ("base", "sys", 0)
    st = Walker(im, calls).walk(0x1bc8d4, 0x1bf8b0, st, fork=True, fork_min=0x1bf8b0)

    def node(v):
        if v[0] == "io": return v[1]
        if v[0] == "id" and v[1].endswith("Node"): return v[1][:-4]
        if v == ("id", "sys+0x3bc"): return "audioIn"
        if v == ("id", "sys+0x3c0"): return "audioOut"
        return repr(v)

    sysw = {0x50c: None, 0x514: None}
    # sys+0x50c/+0x514 pairs: HexaTrackAudioSystem ctor 0x1c2cac stores literal pairs (vldr d16 + vst1.32 at 0x1c2d58..0x1c2d68)
    lit50c = (im.u32(0x1c2d58 + 8 + 0x220), im.u32(0x1c2d58 + 8 + 0x224)); lit514 = (im.u32(0x1c2d60 + 8 + 0x220), im.u32(0x1c2d60 + 8 + 0x224))

    def pair(p):
        if p == "midi": return "midi"
        if p[0] == "lit2": return p[1]
        if p[0] == "sysptr": return {0x50c: lit50c, 0x514: lit514}.get(p[1])
        out = []
        for v in p:
            if v[0] == "mem": v = ("lit", st.statics.get(v[1], None))
            out.append(v[1] if v[0] == "lit" else None)
        return tuple(out)
    # helper pair statics come from the helpers' own guard initialisers
    got = []
    for site, s, sp, d, dp in conns:
        got.append((site, node(s), pair(sp), node(d), pair(dp)))
    for site, s, sp, d, dp in sorted(got):
        P("  @0x%x  %-26s %-9s -> %-26s %s" % (site, s, sp, d, dp))
    bad = sorted(set(got) ^ set(EXPECTED), key=repr)
    P("  nodes added (addNamedNode 0x1b6020): %s" % [n for _, n in nodes])
    check(not bad and [n for _, n in nodes] == NODE_NAMES and len(got) == 30,
          "C1: 16 connectPair + 4 audio-in + 6 audio-out (7 pairs) + 3 MIDI connections decoded; all match the expected table")
    if bad: P("  MISMATCH: %s" % bad)
    # helper static pairs (from their initialisers) — re-derive each helper's pair independently
    hp = {}
    for a in list(IN_HELPERS) + list(OUT_HELPERS):
        s2 = Walker(im, {}).walk(a, a + (0xf8 if a == 0x1b78c0 else 0x88 if a in IN_HELPERS else 0x80), State(), fork=False)
        hp[a] = [tuple(sorted(s2.statics[k] for k in sorted(s2.statics)[i:i + 2])) for i in range(0, len(s2.statics), 2)]
    P("  helper pair statics: %s" % {hex(a): v for a, v in hp.items()})
    check(all(hp[a] == [IN_HELPERS[a]] for a in IN_HELPERS) and all(sorted(hp[a]) == sorted(OUT_HELPERS[a]) for a in OUT_HELPERS),
          "C1: helper pair statics (0x1b7480/76a0/77b0/7590 inputs; 0x1b78c0/7ab0/7bc0/7cd0/7de0/7ef0 outputs) as tabled")
    # straight-line: no in-body conditional branch skips a connection site
    ins = im.disasm(0x1bda00, 0x1bf560)
    sites = sorted(set(s for s, *_ in EXPECTED))
    skips = []
    for i in ins:
        if re.match(r"b(eq|ne|lt|gt|le|ge|hi|ls|cc|cs|mi|pl)$", i.mnemonic) or i.mnemonic == "b":
            t = int(i.op_str.lstrip("#"), 0)
            if t < 0x1bf8b0:
                lo, hi = (i.address, t) if t > i.address else (t, i.address)
                skips += [hex(s) for s in sites if lo < s < hi]
    P("  in-body branches spanning a connection site: %s" % (skips or "none"))
    check(not skips, "C1: every connection call lies on the straight-line path of 0x1bc8d4 (no in-body branch spans one)")
    # connection primitive + canConnect checks (instruction assertions)
    asserts = {0x1b61fc: "bl #0x5fae80", 0x1b6220: "bl #0x5ff2c4", 0x1b623c: "bl #0x5fae80", 0x1b6260: "bl #0x5ff2c4",
               0x5faefc: "ldr r3, [r0, #0x30]", 0x5faf00: "cmp r5, r3", 0x5faf34: "ldr r3, [r0, #0x2c]", 0x5faf38: "cmp r4, r3",
               0x1b73bc: "bl #0x5fae80", 0x1b73dc: "bl #0x5ff2c4", 0x1b8334: "bl #0x5f9e90", 0x1b82d8: "ldr r6, [r4, #0x204]",
               0x1b82e0: "ldr r7, [r4, #0x208]", 0x5714b4: "bl #0x1c2cac", 0x57146c: "str r7, [sp, #0x58]",
               0x571434: "str lr, [sp, #0x5c]", 0x571418: "mov r7, #4", 0x571420: "mov lr, #0xc"}

    def insn(a):
        i = list(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a))[0]
        return "%s %s" % (i.mnemonic, i.op_str)
    abad = {hex(a): insn(a) for a, v in asserts.items() if insn(a) != v}
    P("  primitives/canConnect/graph-config instruction assertions: %d, %s" % (len(asserts), abad or "all match"))
    midi_idx = im.u32(0xaa4c20)
    check(not abad and midi_idx == 0x1000 and lit50c == (0, 1) and lit514 == (2, 3),
          "C1: connectPair 0x1b61bc = 2x(canConnect 0x5fae80 ? addConnection 0x5ff2c4); canConnect checks src ch < numOut (+0x30), "
          "dst ch < numIn (+0x2c); MIDI helper channel 0x1000; selector dst pairs sys+0x50c=(0,1), +0x514=(2,3); graph cfg 4 in/12 out")
    # node classes / channel counts
    import json as _j
    ti = {int(r["typeinfo"], 16): r["name"] for r in _j.load(open(os.path.join(HERE, "out", "H001", "typeinfo_all.json")))} \
        if os.path.exists(os.path.join(HERE, "out", "H001", "typeinfo_all.json")) else None
    primary = {}
    for r in _j.load(open(os.path.join(HERE, "out", "H001", "typeinfo_all.json"))):
        if r["vtables"]: primary.setdefault(r["name"], int(r["vtables"][0], 16))
    rows = []; nbad = []
    for nm, (off, ctor, cls, io, pb) in NODE_CLASS.items():
        rec = []
        def h(st_, site, rec=rec): rec.append((st_.r.get("r1"), st_.r.get("r2")))
        lo, hi = im.func_of(ctor)
        if ctor == 0x13d7e8: hi = 0x13de64
        st0 = State(); st0.r["r0"] = ("base", "this", 0)
        s3 = Walker(im, {0x5f9e90: h}, strings=False).walk(lo, hi, st0, fork=False)
        vt_name = None; vt_found = None
        prim = primary.get(cls)               # primary vtable = first vtable group listed for the class's typeinfo (H001 table)
        for i in im.disasm(lo, hi):           # the ctor must load a literal at a fixed distance before/at the primary vtable
            m = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", i.op_str)
            if i.mnemonic.startswith("ldr") and m and vt_found is None and prim is not None:
                v = im.u32(i.address + 8 + int(m.group(2), 0))
                if v is not None and -0x300 < v - prim < 0x300:
                    vt_found = prim; vt_name = ti[im.u32(prim - 4)]
        ch = rec[0] if rec else None
        chv = tuple(x[1] if x and x[0] == "lit" else ("ret", hex(x[1])) if x and x[0] == "ret" else None for x in ch) if ch else None
        if nm == "headphoneUnit":   # counts come from two getters: 0x1afac0 -> 14, 0x1afac8 -> 2
            chv = (14 if insn(0x1afac0) == "mov r0, #0xe" else None, 2 if insn(0x1afac8) == "mov r0, #2" else None)
        slot5 = im.u32(vt_found + 0x14) if vt_found else None
        ok = vt_name == cls and (chv[0] == io[0] and (io[1] is None or chv[1] == io[1])) and (pb is None or slot5 == pb)
        if not ok: nbad.append(nm)
        rows.append((nm, hex(off), cls, hex(vt_found or 0), chv, hex(slot5 or 0)))
        P("  %-25s sys+0x%x  %-19s vt 0x%x  in/out %s  slot5 0x%x" % (nm, off, vt_name, vt_found or 0, chv, slot5 or 0))
    check(not nbad, "C1: node classes (RTTI), channel counts (setPlayConfigDetails args) and processBlock (vtable slot 5) as tabled")
    J["c1"] = {"connections": [[hex(a), b, c if isinstance(c, str) else list(c), d, e if isinstance(e, str) else list(e)]
                               for a, b, c, d, e in sorted(got)], "nodes": rows}


# =========================================================================================================== emulation rigs
class Rig:
    def __init__(self):
        self.e = e = emu.Emu(insn_limit=50_000_000)
        self.fk = h9.Fakes(e)
        self.log = []

    def fader(self, index=100):
        """VolumeFader stand-in exactly as ctor 0xe9e5c -> 0xe9d28(this, 100, 100) leaves it (H009 C1/C7), index then set."""
        e = self.e
        V = e.malloc(0x98, "VolumeFader"); e.wr(V, b"\0" * 0x98)
        s = e.malloc(0x24, "smoother"); e.call(SMOOTH_CTOR, s, 100, f2u(1.0))
        e.w32(V, VT_FADER); e.w32(V + 8, VT_FADER2); e.w32(V + 0x88, s); e.w32(V + 0x8c, 100)
        if index != 100: e.vcall(V, 2, index)          # Volume slot 2 0xe86e0: set index (what VolumeProxy 0xe78ac calls)
        return V

    def set_fader(self, V, index, offset=0):
        if offset: self.e.vcall(V, 3, index, offset)      # slot 3 0xe86f0: index + sample offset
        else: self.e.vcall(V, 2, index)

    def holder(self, name, cb):
        """object whose IAudioProcessor sub-object at +8 has a fake vtable (processBlock = slot 5 +0x14)."""
        e = self.e
        h = e.malloc(0x40, "holder"); e.wr(h, b"\0" * 0x40)
        inner = self.fk.obj(name, {0x14: cb}); e.w32(h + 8, e.u32(inner))
        return h

    def chans(self, buf):
        e = self.e; n = e.u32(buf); arr = e.u32(buf + 0xc)
        return [e.u32(arr + 4 * i) for i in range(n)]

    def fxobj(self, name, fx, tag):
        """fake unit with slot 5 applying a python fx(L, R) on channels 0/1 of the AudioBuffer in r1 (logs the channel pointers)."""
        def cb(em, nm):
            buf = em.r(1); ch = self.chans(buf); self.log.append((tag, ch))
            if fx is not None:
                l, r = fx(em.floats(ch[0], N), em.floats(ch[1], N)); em.set_floats(ch[0], l); em.set_floats(ch[1], r)
        return self.fk.obj(name, {0x14: cb})


def build_sendunit(rg, proc_fx, ret_index=100):
    e = rg.e
    S = e.malloc(0x100, "SendFxUnit stand-in"); e.wr(S, b"\0" * 0x100); e.w32(S, VT_SENDFXUNIT)
    e.w32(S + 0x8c, rg.fxobj("sendproc", proc_fx, "SendFxProcessor(+0x8c)"))
    V = rg.fader(ret_index); e.w32(S + 0x90, V)
    e.w32(S + 0x80, rg.fk.obj("send meter", {0x14: lambda em, nm: rg.log.append(("PeakDetector(+0x80)", rg.chans(em.r(1))))}))
    return S, V


def build_composite(rg, master, send, pooled):
    e = rg.e
    CF = e.malloc(0x200, "CompositeFxUnit stand-in"); e.wr(CF, b"\0" * 0x200); e.w32(CF, VT_COMPOSITE)
    e.call(AB_CTOR, CF + 0xa4); e.call(AB_CTOR, CF + 0x13c)
    e.w32(CF + 0x8c, master); e.w32(CF + 0x90, send)
    rg.jobs = []
    if pooled:
        pool = rg.fk.obj("pool", {0x10: lambda em, nm: rg.jobs.append(em.r(1)), 0x14: lambda em, nm: rg.log.append(("pool.run",))})
        e.w32(CF + 0x94, pool)
        for off in (0x9c, 0xa0):
            j = e.malloc(0x10, "job"); e.wr(j, b"\0" * 0x10); e.w32(CF + off, j)
    return CF


def run_composite(rg, CF, buf):
    e = rg.e
    rg.jobs = []
    e.call(CF_PB, CF, buf.obj, 0)
    for j in rg.jobs: e.call(JOB_RUN, j)      # stand-in pool: runs the queued jobs with the real job runner 0x153980 afterwards


def build_masterout(rg, index=100):
    e = rg.e
    MO = e.malloc(0x130, "MasterOutUnit stand-in"); e.wr(MO, b"\0" * 0x130); e.w32(MO, VT_MASTEROUT)
    st = e.malloc(0xa0, "SimpleTwoMixUnit(6,0)"); e.wr(st, b"\0" * 0xa0)
    # fields exactly as SimpleTwoMixUnit ctor 0x153844(this, 6, 0) writes them (0x15386c..0x1538a8)
    e.w32(st, VT_STMU); e.w32(st + 0x80, 6); e.w32(st + 0x84, 2); e.w32(st + 0x88, 0); e.w32(st + 0x8c, 1)
    e.wr(st + 0x90, b"\x00"); e.w32(st + 0x94, f2u(1.0)); e.w32(st + 0x98, 0)
    e.w32(MO + 0x80, st)
    V = rg.fader(index); e.w32(MO + 0x84, V)
    e.w32(MO + 0x88, rg.fk.obj("master meter", {0x14: lambda em, nm: rg.log.append(("PeakDetector(+0x88)", rg.chans(em.r(1))))}))
    e.w32(MO + 0x90, rg.holder("renderer", lambda em, nm: rg.log.append(("AudioRenderer(+0x90)", rg.chans(em.r(1))))))
    e.call(AB_CTOR, MO + 0x94)
    return MO, V


# =========================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H010"))
    ap.add_argument("--regress", action="store_true", help="re-run H009 and H021..H041 and compare their recorded hashes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []; f32 = {}

    def P(s_=""): rep.append(s_); print(s_, flush=True)

    def check(c, msg):
        P(("PASS " if c else "FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    P("H010 send bus / return / master side — target sha256 %s" % emu.SHA)
    static_c1(im, P, check, J)

    # ------------------------------------------------------------------------------------------------ C2 CompositeFxUnit
    P("\n== C2 CompositeFxUnit::processBlock 0x1a94cc (real; stand-in Master/Send units)")
    rg = Rig(); e = rg.e
    rng = random.Random(19)
    gm = lambda l, r: ([F(x * 0.5) for x in l], [F(x * 0.25) for x in r])          # noqa: E731
    gs = lambda l, r: ([F(-x) for x in l], [F(x * 2.0) for x in r])                # noqa: E731
    c2 = []
    for sname, pooled, fm, fs in (("inline/identity", False, None, None), ("inline/gains", False, gm, gs),
                                  ("pooled/identity", True, None, None), ("pooled/gains", True, gm, gs)):
        rg.log = []
        mu = rg.fxobj("master", fm, "MasterFxUnit(+0x8c)"); su = rg.fxobj("send", fs, "SendFxUnit(+0x90)")
        CF = build_composite(rg, mu, su, pooled)
        buf = h9.AudioBuf(e, 4)
        ins = [[F(rng.uniform(-1, 1)) for _ in range(N)] for _ in range(4)]
        for c_ in range(4): buf.write(c_, ins[c_])
        run_composite(rg, CF, buf)
        outs = [buf.read(c_) for c_ in range(4)]
        exm = (fm or (lambda l, r: (l, r)))(ins[0], ins[1]); exs = (fs or (lambda l, r: (l, r)))(ins[2], ins[3])
        ok = [bits(x) for x in outs] == [bits(x) for x in (exm[0], exm[1], exs[0], exs[1])]
        cn = {p_: "in%d" % k_ for k_, p_ in enumerate(buf.ptrs)}
        seen = [(t, [cn.get(c_, hex(c_)) for c_ in ch]) for t, *rest in rg.log if t != "pool.run" for ch in rest]
        P("  %-16s units saw %s; outputs: out0/1 = master(in0/1), out2/3 = send(in2/3), no cross-sum: %s" % (sname, seen, ok))
        c2.append(ok and seen == [("MasterFxUnit(+0x8c)", ["in0", "in1"]), ("SendFxUnit(+0x90)", ["in2", "in3"])])
        f32.setdefault("c2", []).extend(sum(outs, []))
    check(all(c2), "C2: CompositeFxUnit processes in place and does not sum: Master unit on ch0/1, Send unit on ch2/3 "
          "(4 settings: inline/pooled x identity/gain stand-ins); no gain of its own")
    J["c2"] = c2

    # ------------------------------------------------------------------------------------------------ C3 Send unit / return fader
    P("\n== C3 SendFxUnit::processBlock 0x1b3068 (real) with the real return VolumeFader (+0x90)")
    rg3 = Rig(); e3 = rg3.e
    c3 = []
    for idx in (0, 1, 50, 71, 100, 115, 127):
        rg3.log = []
        S, V = build_sendunit(rg3, None, idx)
        b3 = h9.AudioBuf(e3, 2)
        for blk in range(3):              # ctor smoother starts at 1.0 -> ramps to the target over 100 samples, then constant
            b3.write(0, [1.0] * N); b3.write(1, [-0.5] * N); e3.call(SFU_PB, S, b3.obj, 0)
        g = b3.read(0)[-1]; g2 = b3.read(1)[-1]
        c3.append((idx, g, g2, TM.fader_gain(idx)))
        P("  return index %3d: gain L %.9g R %.9g (model table %.9g); order %s" % (idx, g, -2 * g2, TM.fader_gain(idx),
                                                                               [t for t, *_ in rg3.log][-2:]))
    check(all(F(g) == F(t) and F(-2 * g2) == F(t) for _, g, g2, t in c3) and
          [t for t, *_ in rg3.log][-2:] == ["SendFxProcessor(+0x8c)", "PeakDetector(+0x80)"],
          "C3: Send return level = VolumeFader table (0 -> 0, 50 -> -12.04 dB, 100 -> 0 dB, 127 -> +6.02 dB) after the processor, "
          "before the send meter")
    # ramp check: model Fader vs real on a step from 100 to 60 with offset 17
    S, V = build_sendunit(rg3, None, 100); b3 = h9.AudioBuf(e3, 2); mf = BM.SendUnit(None, 100)
    rbad = 0
    for blk in range(6):
        if blk == 2: rg3.set_fader(V, 60, 17); mf.ret.set(60, 17)
        l = h9.sig("sine", blk, 0, None); r = h9.sig("steps", blk, 1, None)
        b3.write(0, l); b3.write(1, r); e3.call(SFU_PB, S, b3.obj, 0)
        ml, mr = mf.process(l[:], r[:])
        rbad += (bits(b3.read(0)) != bits(ml)) + (bits(b3.read(1)) != bits(mr))
        f32.setdefault("c3_ramp", []).extend(b3.read(0) + b3.read(1))
    check(rbad == 0, "C3: return-fader change (100 -> 60 at sample offset 17) ramps linearly over 100 samples (model bit-exact)")
    J["c3_gains"] = c3

    # SendFxProcessor front end with no effect: MuteSmoother +0xa8 mutes the send bus (128-sample fade)
    P("  SendFxProcessor::processBlock 0x119994 (real), no effect pending (+0xa0 = +0xa4 = -1):")
    P4 = e3.malloc(0xb0, "SendFxProcessor stand-in"); e3.wr(P4, b"\0" * 0xb0); e3.w32(P4, 0x842d40)
    ms = e3.malloc(0x20, "MuteSmoother"); e3.call(MUTE_SM_CTOR, ms, 132, 0)   # as prepareToPlay 0x119bd8 @0x11a1e8: rint(sr*0.001*3), unmuted
    e3.w32(P4 + 0xa8, ms); e3.w32(P4 + 0xa0, 0xffffffff); e3.w32(P4 + 0xa4, 0xffffffff); e3.w32(P4 + 0x88, 0)
    bP = h9.AudioBuf(e3, 2); mm = BM.SendProcessorMute(44100)
    outs = []; mbad = 0
    for blk in range(4):
        l = h9.sig("dc", blk, 0, None); bP.write(0, l); bP.write(1, l); e3.call(SFP_PB, P4, bP.obj, 0)
        ml, mr = mm.process(l[:], l[:], False)
        outs.append(bP.read(0)); mbad += (bits(bP.read(0)) != bits(ml)) + (bits(bP.read(1)) != bits(mr))
    P("    DC 1.0 in -> out[0] %.6g, out[63] %.6g, out[127] %.6g, out[131] %.6g, out[132] %.6g, out[192..255] max %.3g" %
      (outs[0][0], outs[0][63], outs[1][63], outs[2][3], outs[2][4], max(abs(x) for x in outs[3])))
    check(mbad == 0 and max(abs(x) for x in outs[3] + outs[2][4:]) == 0.0 and outs[0][0] == 1.0 and outs[2][3] != 0.0,
          "C3: with no Send effect pending the SendFxProcessor mutes the send bus with a 132-sample (3 ms) linear fade (no dry leak)")
    J["c3_mute"] = [outs[0][0], outs[0][63], outs[1][63], outs[2][3], outs[2][4]]

    # ------------------------------------------------------------------------------------------------ C4 MasterOutUnit
    P("\n== C4 MasterOutUnit::processBlock 0x1b2150 (real) with real SimpleTwoMixUnit(6) and real master VolumeFader")
    rg4 = Rig(); e4 = rg4.e
    c4 = []
    for idx in (0, 10, 50, 100, 112, 127):
        rg4.log = []
        MO, V = build_masterout(rg4, idx)
        b4 = h9.AudioBuf(e4, 6)
        vals = [0.5, -0.25, 0.125, 0.0625, -0.03125, 0.015625]
        for blk in range(3):
            for c_ in range(6): b4.write(c_, [vals[c_]] * N)
            e4.call(MOU_PB, MO, b4.obj, 0)
        o = [b4.read(c_)[-1] for c_ in range(6)]
        g = TM.fader_gain(idx)
        exp_l = F(F(F(0.5 + 0.125) - 0.03125) * g); exp_r = F(F(F(-0.25 + 0.0625) + 0.015625) * g)
        c4.append((idx, o, exp_l, exp_r))
        P("  master index %3d: out0 %.9g out1 %.9g (model %.9g %.9g) out2/3 copy %s, out4/5 %s; order %s" %
          (idx, o[0], o[1], exp_l, exp_r, o[2] == o[0] and o[3] == o[1], o[4:], [t for t, *_ in rg4.log][-2:]))
    check(all(o[0] == el and o[1] == er and o[2] == o[0] and o[3] == o[1] for _, o, el, er in c4) and
          [t for t, *_ in rg4.log][-2:] == ["PeakDetector(+0x88)", "AudioRenderer(+0x90)"],
          "C4: MasterOutUnit: ch0/1 = (in0/1 + in2/3 + in4/5) x master VolumeFader (table), then meter, renderer; ch2/3 := ch0/1")
    J["c4"] = [(i, o) for i, o, *_ in c4]
    # DSF drive (DaveSmithDriveUnit +0x88 = DSFDrive, ctor 0xe86a0 @0xc3f34): slot 13 0xe85e8 gain law, real code
    dd = []
    for idx in (0, 1, 100, 511, 512, 800, 1023):
        r0, _ = e4.call(0xe85e8, 0, idx); dd.append((idx, u2f(r0), BM.dsf_drive_gain(idx)))
    P("  DSFDrive slot 13 0xe85e8 (real): %s" % ", ".join("%d -> %.9g" % (i, g) for i, g, _ in dd))
    rng_ = (im.u32(0xe8738), im.u32(0xe873c))
    check(all(f2u(g) == f2u(m) for _, g, m in dd) and rng_ == (0, 1023),
          "C4: DSF drive gain = 1 + 3*(i/1023)^2 (index 0..1023, 0 dB .. +12.04 dB; model bit-exact on 7 indices)")
    J["c4_dsf"] = dd
    # static: FX mode (CompositeFxUnit::setFxMode task 0x1a9c54 / scene load 0x1aa060, 0x1aa240) and enable path
    fx_tab = (list(im.data[im.off(0x861840):im.off(0x861840) + 3]), list(im.data[im.off(0x861844):im.off(0x861844) + 3]))
    sasserts = {0x11cafc: "ldr r0, [r0, #0x1c]", 0x11cb00: "b #0x112a08", 0x112a1c: "strb r1, [r0, #0x9e]",
                0x1b3574: "ldr r0, [r0, #0x90]", 0x1b3564: "ldr r0, [r0, #0x88]", 0x1b1e58: "ldr r0, [r0, #0x80]",
                0x1199bc: "beq #0x1199cc", 0x1199c0: "ldrb r3, [r0, #0x9e]", 0x1199d4: "bl #0xe8050", 0x1199f4: "bl #0xe808c",
                0x119b84: "ldrb r1, [r0, #0x9d]", 0x119b88: "eor r1, r1, #1", 0x1b3468: "bl #0xe9e5c", 0x1b347c: "str r6, [r4, #0x90]",
                0x1b243c: "bl #0xe9e5c", 0x1b2450: "str r6, [r4, #0x84]", 0x1b2408: "bl #0x153844", 0x1b23fc: "mov r1, #6",
                0x1bde2c: "bl #0x1b3574", 0x1bde40: "ldr r2, [r7, #0x554]", 0x1bde48: "bl #0xe78ac",
                0x1be8b8: "bl #0x1b2600", 0x1be8cc: "ldr r2, [r7, #0x558]", 0x1be8d4: "bl #0xe78ac", 0x1b2600: "ldr r0, [r0, #0x84]",
                0x1bec64: "bl #0x1b1b78", 0x1bec78: "ldr r2, [r7, #0x550]", 0x1bec80: "bl #0xe78ac",
                0xe791c: "ldr r1, [r2]", 0xe7920: "ldr r3, [r3, #8]", 0x11a1e8: "bl #0xe7fd8", 0x11a1ec: "str r7, [r4, #0xa8]"}

    def insn(a_):
        i_ = list(im.md.disasm(im.data[im.off(a_):im.off(a_) + 4], a_))[0]
        return "%s %s" % (i_.mnemonic, i_.op_str)
    sbad = {hex(k): insn(k) for k, v in sasserts.items() if insn(k) != v}
    P("  FX mode enable tables 0x861840 (send) %s, 0x861844 (master) %s; %d static assertions: %s" %
      (fx_tab[0], fx_tab[1], len(sasserts), sbad or "all match"))
    check(not sbad and fx_tab == ([1, 0, 0], [0, 1, 0]),
          "C3/C6 static: FX mode 0 'EffectModeSend' enables the Send processor and disables Master (0x112a08 -> +0x9e), mode 1 "
          "'EffectModeMaster' the reverse; Send processor mutes its input when off; return/master/headphone faders bound by "
          "VolumeProxy 0xe78ac to sys+0x554/+0x558/+0x550 (ProjectManager values)")

    # ------------------------------------------------------------------------------------------------ C5 model, full chain
    P("\n== C5 model (harness/models/bus_mix.py) vs emulated chain: CompositeFxUnit -> SendFxUnit(real, stand-in processor) "
      "-> MasterOutUnit")

    def mfx_shape(l, r): return [F(F(x * 0.5) + 0.125) for x in l], [F(x * x) for x in r]
    def sfx_wet(l, r): return [F(F(x * -0.75) + F(y * 0.25)) for x, y in zip(l, r)], [F(x * 0.6) for x in r]
    SETTINGS = [  # name, master fx, send fx, return idx, master idx, events {block: (target, index, offset)}
        ("unity", None, None, 100, 100, {}),
        ("fx both", mfx_shape, sfx_wet, 100, 100, {}),
        ("return min", mfx_shape, sfx_wet, 0, 100, {25: ("ret", 100, 0)}),
        ("return max, master low", None, sfx_wet, 127, 30, {}),
        ("master 0", mfx_shape, None, 100, 0, {20: ("master", 127, 33)}),
        ("mid changes", mfx_shape, sfx_wet, 71, 88, {10: ("ret", 20, 5), 30: ("master", 100, 63), 40: ("ret", 127, 99)}),
        ("low", None, None, 3, 12, {15: ("master", 9, 1)}),
    ]
    kinds = ["impulse", "sine", "noise", "steps"]
    tot = 0; nbad = 0; worst = 0.0
    for sname, fm, fs, ri, mi, evs in SETTINGS:
        for kind in kinds:
            rgc = Rig(); ec = rgc.e
            mu = rgc.fxobj("master", fm, "MasterFxUnit")
            SU, RV = build_sendunit(rgc, fs, ri)
            CF = build_composite(rgc, mu, SU, False)
            MO, MV = build_masterout(rgc, mi)
            model = BM.BusChain(fm, fs, ri, mi)
            r_ = random.Random(zlib.crc32((sname + '/' + kind).encode()))
            cb = h9.AudioBuf(ec, 4); mb = h9.AudioBuf(ec, 6)
            for blk in range(60):
                if blk in evs:
                    tgt, ix, off = evs[blk]
                    if tgt == "ret": rgc.set_fader(RV, ix, off); model.send.ret.set(ix, off)
                    else: rgc.set_fader(MV, ix, off); model.mout.fader.set(ix, off)
                src = [h9.sig(kind, blk, c_ % 2, r_) for c_ in range(4)]
                src[2] = [F(x * 0.5) for x in src[2]]; src[3] = [F(x * -0.375) for x in src[3]]
                x14 = [h9.sig("sine" if kind != "sine" else "steps", blk, c_, r_) for c_ in range(2)]
                for c_ in range(4): cb.write(c_, src[c_])
                run_composite(rgc, CF, cb)
                co = [cb.read(c_) for c_ in range(4)]
                for c_ in range(4): mb.write(c_, co[c_])
                mb.write(4, x14[0]); mb.write(5, x14[1])
                ec.call(MOU_PB, MO, mb.obj, 0)
                mo = [mb.read(c_) for c_ in range(6)]
                mc, mm_ = model.process(src[0], src[1], src[2], src[3], x14[0], x14[1])
                for c_ in range(4):
                    tot += N
                    nbad += sum(p != q for p, q in zip(bits(co[c_]), bits(mc[c_])))
                    nbad += sum(p != q for p, q in zip(bits(mo[c_]), bits(mm_[c_])))
                    worst = max(worst, max(abs(p - q) for p, q in zip(mo[c_], mm_[c_])))
                f32.setdefault("c5_%s_%s" % (sname.replace(" ", "_").replace(",", ""), kind), []).extend(sum(mo[:4], []))
    P("  %d settings x %d signals x 60 blocks x 64 frames: %d channel-samples compared (composite out0-3 + master out0-3), "
      "%d differ, max |diff| %.3g" % (len(SETTINGS), len(kinds), 2 * tot, nbad, worst))
    check(nbad == 0, "C5: bus_mix.py bit-exact to the emulated CompositeFxUnit + real SendFxUnit return fader + real MasterOutUnit")
    J["c5"] = {"compared": 2 * tot, "differ": nbad}

    # ------------------------------------------------------------------------------------------------ C7 alternatives (mutants)
    P("\n== C7 alternatives: model mutants against the emulated chain (setting 'fx both' and 'mid changes', noise + sine)")

    class PreMaster(BM.BusChain):          # (a) return summed BEFORE the Master FX
        def process(self, ml, mr, sl, sr, xl, xr):
            s = self.send.process([F(x) for x in sl], [F(x) for x in sr])
            a_ = [TM.neon_add(p, q) for p, q in zip(ml, s[0])]; b_ = [TM.neon_add(p, q) for p, q in zip(mr, s[1])]
            m = self.master_fx(a_, b_) if self.master_fx else (a_, b_)
            z = [0.0] * N
            return None, self.mout.process([m[0], m[1], z, z, xl, xr])

    class Separate(BM.BusChain):           # (a') return as a separate output, not summed into the master
        def process(self, ml, mr, sl, sr, xl, xr):
            c, _ = BM.BusChain.process(self, ml, mr, sl, sr, xl, xr)
            z = [0.0] * N
            return None, self.mout.process([c[0], c[1], z, z, xl, xr])

    class DryWet(BM.BusChain):             # (b) dry send added to the wet return
        def process(self, ml, mr, sl, sr, xl, xr):
            c = BM.composite([ml, mr, sl, sr], self.master_fx, self.send)
            c[2] = [TM.neon_add(p, F(q)) for p, q in zip(c[2], sl)]; c[3] = [TM.neon_add(p, F(q)) for p, q in zip(c[3], sr)]
            return c, self.mout.process(c + [xl, xr])

    class NoRetFader(BM.BusChain):         # no return level stage
        def __init__(self, *a_, **k_):
            BM.BusChain.__init__(self, *a_, **k_); self.send.ret = BM.Fader(100)
        def process(self, *a_):
            self.send.ret.set(100); return BM.BusChain.process(self, *a_)
    mut_res = {}
    for mname, cls in (("return before Master FX", PreMaster), ("return as separate output", Separate),
                       ("dry send + wet return", DryWet), ("no return fader", NoRetFader)):
        bad = 0
        for sname, fm, fs, ri, mi, evs in (SETTINGS[1], SETTINGS[5]):
            for kind in ("noise", "sine"):
                ref = BM.BusChain(fm, fs, ri, mi); mut = cls(fm, fs, ri, mi)
                r1 = random.Random(5); r2 = random.Random(5)
                for blk in range(60):
                    if blk in evs:
                        tgt, ix, off = evs[blk]
                        for m_ in (ref, mut):
                            (m_.send.ret if tgt == "ret" else m_.mout.fader).set(ix, off)
                    srcs = []
                    for rr in (r1, r2):
                        s_ = [h9.sig(kind, blk, c_ % 2, rr) for c_ in range(4)]
                        s_[2] = [F(x * 0.5) for x in s_[2]]; s_[3] = [F(x * -0.375) for x in s_[3]]
                        srcs.append(s_)
                    x14 = [h9.sig("steps", blk, c_, None) for c_ in range(2)]
                    _, a1 = ref.process(*srcs[0], *x14); _, a2 = mut.process(*srcs[1], *x14)
                    bad += sum(sum(p != q for p, q in zip(bits(a1[c_]), bits(a2[c_]))) for c_ in range(2))
        mut_res[mname] = bad
        P("  mutant %-28s master-out samples differing from the (emulation-verified) model: %d" % (mname, bad))
    check(all(v > 0 for v in mut_res.values()), "C7: mutants 'return before Master FX', 'separate output', 'dry+wet return', "
          "'no return fader' all differ from the verified chain")
    J["c7"] = mut_res

    # ------------------------------------------------------------------------------------------------ outputs
    for k_, v in sorted(f32.items()):
        open(os.path.join(a.out, "h010_%s.f32" % k_), "wb").write(struct.pack("<%df" % len(v), *v))
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h010_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h010.json"), "w"), indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


def regress(out):
    """Re-run H009 (its own recorded hashes) and H021..H041 (H009's regression list)."""
    import subprocess
    d = os.path.join(out, "regress", "H009"); os.makedirs(d, exist_ok=True)
    rc = subprocess.call([sys.executable, "-B", os.path.join(HERE, "H009_track_mix.py"), "--out", d],
                         stdout=open(os.path.join(out, "regress", "H009.log"), "w"), stderr=subprocess.STDOUT)
    exp = {"h009_report.txt": "9f1dc1261c82883f76d950560ed7b7341759b34d0c4df4feddf347510679cda6",
           "h009.json": "47a28721b7c9f75dd8a22f9a4db15617fad1219460487ba211b8368c275d73d0"}
    import glob
    got = {k: sha(open(os.path.join(d, k), "rb").read()) for k in exp if os.path.exists(os.path.join(d, k))}
    f32s = sha(b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(d, "*.f32")))))
    ok9 = got == exp and f32s == "98769095832ed8a4e5b0b29b035068b1fd07e0702a2e5f5a12b4a9188c0a631d"
    lines = ["H009 rc %d  %s  report %s…  json %s…  f32 %s…" % (rc, "OK " if ok9 else "BAD", got.get("h009_report.txt", "-")[:8],
                                                             got.get("h009.json", "-")[:8], f32s[:8])]
    r2 = h9.regress(out)
    txt = "\n".join(lines) + "\n" + open(os.path.join(out, "h009_regress.txt")).read()
    open(os.path.join(out, "h010_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok9 and r2 == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
