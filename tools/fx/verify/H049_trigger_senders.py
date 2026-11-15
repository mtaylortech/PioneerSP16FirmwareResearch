#!/usr/bin/env python3
"""H049 — who sends event types 11/15 to InsertFxParameterManager slot 2 0x1263f4 (the Ducker trigger), with which offset, when.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code; Pioneer bytes are read at run time, never stored.
Emulation is guest-memory only (unicorn); outputs only under --out.

Sections
  S1  static assertions (capstone instruction text at fixed 1.60 addresses + direct-call / pointer-word census):
      receiver interface implementers (RTTI, from H049_rtti.py logic), the only dispatcher 0x199ae0 and its callers, the
      per-track receiver table T (= Sequencer+0x1d0, new 0x284) and where constructTrack fills it, the type/offset expressions,
      the mute override, the trigger-type labels, the realtime (pad) path, the graph placement (pre-/post-processing chains).
  E1  emulation of the REAL dispatcher 0x199ae0(T, offset, StepData*) with a constructed T: IFPM entries are stand-in managers with the
      REAL InsertFxParameterManager vtable 0x84407c whose +0x1c is a stand-in processor with the REAL InsertFxProcessor vtable 0x842c10
      (so 0x1263f4 -> 0x11684c -> 0x1310c4 run for real); other receivers are recorders; ITrack/ITrackMixer are Python stubs giving
      track type and mute. StepData built by the REAL ctor 0x350600(step, type). Matrix: tracks x types x track types x mute x offsets.
  E2  emulation of the REAL Sequencer::processStep 0x19412c(seq, offset, step, flags) (stand-in Sequencer blob, T at +0x1d0) for
      pattern-step flags 2 and realtime flags 3 -> same (offset, type) at 0x1263f4.
  E3  end to end: StepData -> real dispatcher -> real manager/processor -> real trigger table -> real InsertFxProcessor processBlock
      0x116860 with a real Ducker (H041 ProcRig) vs the bit-exact model harness/models/ducker.py fed with the table row.
Run: .venv/bin/python -B harness/H049_trigger_senders.py --out harness/out/H049
"""
import argparse, hashlib, json, os, re, struct, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, SENTINEL                             # noqa: E402
import sp16img                                                 # noqa: E402

# libstdc++ static-guard functions are reached from 0x19412c; stub them (acquire -> 1 = "initialise now", release no-op)
emu.STUBS.setdefault("__cxa_guard_acquire", (lambda e: e.setr(0, 1), "static guard acquire: always 1 (initialise)"))
emu.STUBS.setdefault("__cxa_guard_release", (lambda e: None, "static guard release: no-op"))
import H041_ducker_model as H41                                # noqa: E402
from ducker import F                                           # noqa: E402

DISPATCH, PROCSTEP, STEP_CTOR, STEP_SET = 0x199ae0, 0x19412c, 0x350600, 0x351814
MGR_SLOT2, TT_SET, ERASER5 = 0x1263f4, 0x1310c4, 0x130cac
VT_IFPM, VT_PROC = 0x84407c, 0x842c10
N = 64
RECV = {0x44: "player(+0x44)", 0x84: "+0x84", 0x144: "lfo(+0x144)", 0x184: "trackunit(+0x184)", 0x1c4: "midi(+0x1c4)",
        0x204: "+0x204", 0x244: "+0x244"}

LOG = []
def P(s=""):
    print(s); LOG.append(s)

FAILS = []
def check(ok, msg):
    P(("  PASS " if ok else "  FAIL ") + msg)
    if not ok: FAILS.append(msg)


def sha(b): return hashlib.sha256(b).hexdigest()


# ============================================================================================================== S1 static
def ins_at(im, va):
    i = list(im.md.disasm(im.data[im.off(va):im.off(va) + 4], va))
    return ("%s %s" % (i[0].mnemonic, i[0].op_str)) if i else None


def static_checks(im, J):
    P("== S1 static assertions (1.60 instruction text / census)")
    exp = {
        # receiver slot-2 implementations
        0x1263f4: "cmp r2, #0xb", 0x1263f8: "cmpne r2, #0xf", 0x126418: "blx r3",
        0x13163c: "tst r2, #2", 0x131660: "cmp r2, #0xf", 0x1316bc: "cmp r2, #0xb",
        0x14be10: "cmp r2, #0xf", 0x11fcd0: "bx lr", 0x11fc44: "bx lr",
        # Sequencer ctor: T = new(0x284), ctor 0x1995b4, stored at Sequencer+0x1d0
        0x1951b4: "mov r0, #0x284", 0x1951c0: "bl #0x1995b4", 0x1951c4: "str r5, [r4, #0x1d0]",
        # constructTrack 0x1bacec fills T (sp+0x20 = [[sys+0x598]+0x1d0])
        0x1baee0: "ldr r3, [r3, #0x1d0]", 0x1baee4: "add ip, r6, #0x80", 0x1baf00: "str ip, [r3, #4]",
        0x1bb208: "add r2, r8, #0x90", 0x1bb21c: "str r2, [r3, #0x144]",
        0x1bbcd0: "add lr, r6, #0xa0", 0x1bbcd8: "str lr, [ip, #0x184]",
        0x1bbd3c: "add r3, r6, sl, lsl #3", 0x1bbd44: "add r3, r3, #0xc0", 0x1bc024: "str r5, [sl, #4]!",
        # dispatcher 0x199ae0: r5 = offset (r1), sb = step+8 (type), ITrack vt+0x40 type, Midi (2) skips the managers,
        # FX1 / FX2 manager slot 2 with r2 = mute ? 8 : type
        0x199af8: "mov r5, r1", 0x199b00: "ldr sb, [r2, #8]", 0x199b08: "ldr r3, [r3, #0x40]",
        0x199c0c: "cmp sl, #2", 0x199c18: "ldr r6, [r2, #0xc4]", 0x199d6c: "mov r1, r5", 0x199d70: "ldr r3, [r3, #8]",
        0x199d7c: "moveq r2, sb", 0x199d80: "movne r2, #8", 0x199d90: "ldr r6, [r2, #0xc8]", 0x199efc: "movne r2, #8",
        0x19a034: "ldr r6, [r8, #0x184]",
        # processStep 0x19412c ends with dispatch(seq+0x1d0 table, offset, step)
        0x194184: "ldr r0, [r5, #0x1d0]", 0x194198: "bl #0x199ae0",
        # ITrack slot 12 -> TrackUnit+0xdc (= +0x90 ITrackMixer, ctor 0x1ccf08/0x1ccfd8); ITrackMixer slot 12 -> TrackData+0x39
        0x1ce8bc: "ldr r0, [r0, #0xdc]", 0x1ce8ec: "ldr r0, [r0, #0x614]", 0x1ccf08: "add r5, r4, #0x90",
        0x1ccf48: "str r5, [sp, #0x34]", 0x1ccfd8: "str r5, [r4, #0xdc]", 0x1c841c: "ldrb r0, [r3, #0x39]",
        0x17dbe0: "ldrb r1, [r3, #0x39]", 0x17dc70: "ldrb r1, [r3, #0x38]",
        # trigger-type validity / labels
        0x35476c: "movw r2, #0x9f01", 0x354794: "mov r3, #0xf", 0x311634: "cmp r3, #0xb", 0x311638: "streq sb, [r5, #-4]",
        0x311640: "cmp r3, #0xf", 0x311644: "streq fp, [r5, #-4]", 0x31164c: "cmp r3, #8", 0x311650: "moveq r3, #2",
        # Sequencer processBlock offsets (pattern step call 0x191ef0 with [sp+0x30] = clamp(trunc(n*d/len), 0, n-1))
        0x191e60: "vdiv.f64 d16, d17, d16", 0x191e7c: "sub r7, r7, #1", 0x191e84: "movge r3, r7", 0x191ee0: "mov r3, #2",
        0x191ef0: "bl #0x19412c", 0x191554: "mov ip, #0xf", 0x19155c: "str ip, [sp, #0x190]", 0x19156c: "bl #0x19412c",
        0x1916cc: "bl #0x6472f0", 0x1916f0: "bl #0x504b58", 0x1916fc: "bl #0x504eec",
        # realtime: triggerSoundInternal builds StepData(type 15), calls IRealTimeSequenceEditor slot 5; thunk -0x88
        0x16b778: "mov r1, #0xf", 0x16b77c: "add r0, sp, #0x10", 0x16b78c: "bl #0x350600",
        0x16ba14: "add r1, sp, #0x10", 0x16ba18: "mov r2, #1", 0x16ba1c: "ldr r3, [r3, #0x14]", 0x1901b0: "sub r0, r0, #0x88", 0x1901b4: "b #0x1901b8",
        # graph: Sequencer (sys+0x598) appended to the pre-processing chain sys+0x3ac; TriggerEraser sys+0x580 to post chain +0x3b0
        0x1bd950: "ldr r0, [r7, #0x3ac]", 0x1bd958: "ldr r1, [r7, #0x598]", 0x1bd95c: "bl #0x1b8c54",
        0x1bd970: "ldr r0, [r7, #0x3b0]", 0x1bd978: "ldr r1, [r7, #0x580]", 0x1bd97c: "bl #0x1b8c54",
        0x1bcfc0: "bl #0x130d24", 0x1bcfd4: "str r5, [r7, #0x580]", 0x130d34: "ldr r3, [pc, #0xc]",
        0x1bcf78: "mov r1, #0x10", 0x1bcf80: "bl #0x130d54",
        0x1b6460: "str r5, [r4, #0x3ac]", 0x1b64cc: "str r5, [r4, #0x3c4]", 0x1b6610: "str r5, [r4, #0x3b0]",
        0x1b6748: "str r5, [r4, #0x3c8]",
        # MIDI connections ("add midi connection", juce addConnection 0x5fae80/0x5ff2c4 with the MIDI channel constant):
        # midiIn -> pre(+0x3c4) -> resamplePlayer(+0x3d0) -> deviceInput(+0x3bc) -> liveSampling -> multiTrackUnit(+0x74c);
        # masterOut -> (+0x3c0) -> resampleRecorder(+0x3cc) -> post(+0x3c8) -> midiOut
        0x1b6b80: "ldr r3, [r4, #0x3c4]", 0x1b6be4: "ldr r2, [r4, #0x3c4]", 0x1b6be8: "ldr r3, [r4, #0x3d0]",
        0x1b6c40: "ldr r2, [r4, #0x3d0]", 0x1b6c44: "ldr r3, [r4, #0x3bc]", 0x1b6c9c: "ldr r2, [r4, #0x3c0]",
        0x1b6ca0: "ldr r3, [r4, #0x3cc]", 0x1b6cf8: "ldr r2, [r4, #0x3cc]", 0x1b6cfc: "ldr r3, [r4, #0x3c8]",
        0x1bf51c: "ldr r3, [r7, #0x3bc]", 0x1bf530: "bl #0x1b7380", 0x1bf534: "ldr r3, [r7, #0x74c]", 0x1bf544: "bl #0x1b7380",
        0x1bf548: "ldr r3, [r7, #0x3c0]", 0x1bf55c: "bl #0x1b7380", 0x1bda70: "str r0, [r7, #0x74c]", 0x1bdc10: "str r0, [sp, #0x40]",
        0x1be934: "str r0, [sp, #0x24]",
    }
    bad = []
    for va, t in sorted(exp.items()):
        if t is None: continue
        got = ins_at(im, va)
        if got != t: bad.append((hex(va), t, got))
    check(not bad, "%d instruction assertions at fixed 1.60 addresses%s" % (sum(1 for t in exp.values() if t), (": %s" % bad) if bad else ""))
    check(im.u32(0x130d40 + 0x8) == 0x844bf8 or im.u32(0x130d48) == 0x844bf8,
          "0x130d24 (sys+0x580 object, new 0x88) stores vptr 0x844bf8 = TriggerEraser")
    # direct-call census
    dc = im.direct_calls()
    callers = lambda t: sorted(s for s, tt, k in dc if tt == t)
    words = {}
    for va, sz, off in im.segs:
        for i, w in enumerate(struct.unpack_from("<%dI" % (sz // 4), im.data, off)):
            words.setdefault(w, []).append(va + 4 * i)
    c_disp = callers(DISPATCH); c_ps = callers(PROCSTEP)
    fo = lambda xs: sorted(set(hex(im.func_of(x)[0]) for x in xs))
    P("  callers of dispatcher 0x199ae0: %s (functions %s); pointer words: %d" % ([hex(x) for x in c_disp], fo(c_disp),
                                                                                 len(words.get(DISPATCH, []))))
    P("  callers of processStep 0x19412c: %d sites in %s; pointer words: %d" % (len(c_ps), fo(c_ps), len(words.get(PROCSTEP, []))))
    check(c_disp == [0x194198] and not words.get(DISPATCH) and fo(c_ps) == ["0x1901b8", "0x191218"] and len(c_ps) == 10
          and not words.get(PROCSTEP),
          "single dispatcher 0x199ae0 (only caller processStep 0x19412c); processStep reached only from setRealTimeSequenceData "
          "0x1901b8 (5 sites) and Sequencer processBlock 0x191218 (5 sites)")
    w_ifpm2 = [hex(x) for x in words.get(MGR_SLOT2, [])]
    w_s54 = [hex(x) for x in words.get(0x11684c, [])]
    check(w_ifpm2 == ["0x844084"] and not callers(MGR_SLOT2) and w_s54 == ["0x842ce8"] and callers(TT_SET) == [0x11685c],
          "0x1263f4 only as IFPM vtable slot 2 (0x844084), no direct calls; slot 54 0x11684c only in the Insert processor vtable; "
          "TriggerTable_set 0x1310c4 only reached from 0x11684c's tail branch 0x11685c")
    # vtable ids of the Sequencer sub-objects
    seq_vt = 0x85e4dc
    check(im.u32(seq_vt + 5 * 4) == 0x191218 and im.u32(0x85e7dc + 5 * 4) == 0x1901b0,
          "Sequencer primary (IAudioProcessor) slot 5 = 0x191218 (processBlock position); IRealTimeSequenceEditor (+0x88) slot 5 = "
          "thunk 0x1901b0 -> 0x1901b8")
    ti = im.u32(0x85db84 - 4); tn = im.cstr(im.u32(ti + 4), 120)
    check(tn == "*ZN9Sequencer23setRealTimeSequenceDataERN3prj8StepDataEbE4Task",
          "0x1901b8's local task class typeinfo name = Sequencer::setRealTimeSequenceData(prj::StepData&, bool)::Task")
    s1 = im.cstr(im.u32(0x34a1c + 8 + 0xb38), 40); s2 = im.cstr(im.u32(0x34a28 + 8 + 0xb34), 40)
    check((s1, s2) == ("Full Trigger", "Full & Half Trigger") and im.u32(0x34a18 + 8 + 0xb38) + 4 == im.u32(0x34a24 + 8 + 0xb34),
          "LFO 'Trigger On' option strings: index 0 'Full Trigger', index 1 'Full & Half Trigger' (consecutive juce::String statics)")
    nm = lambda lit: im.cstr(im.u32(lit), 40)
    check((nm(0x1bda4c + 8 - 0xd64), nm(0x1bdbf0 + 8 - 0xef0), nm(0x1be914 + 8 + 0x268), nm(0x1b6480 + 8 + 0x1e8),
           nm(0x1b662c + 8 + 0x48), nm(0x1b73a0 + 8 + 0x58)) ==
          ("multiTrackUnitNode", "liveSamplingNode", "masterOutUnitNode", "preProcessingNode", "postProcessingNode",
           "add midi connection"), "graph node / connection names at the asserted sites")
    s3 = im.cstr(im.u32(0x17dbc8 + 8 + 0x6c), 40)
    check(s3 == "muteSetting = ", "TrackData describer prints byte +0x39 as 'muteSetting' (next to 'soloSetting' = +0x38)")
    J["s1"] = {"bad": bad, "dispatch_callers": [hex(x) for x in c_disp], "procstep_callers": [hex(x) for x in c_ps]}


# ============================================================================================================== E1/E2 rig
class Rig:
    """Real Ducker processor (H041 ProcRig, own track `own`, SOURCE `source`) plus a constructed receiver table T for the dispatcher."""
    def __init__(self, own=3, source=3, pre=((0, 0.004), (2, 0.001))):
        self.pr = pr = H41.ProcRig(own_track=own, source=source, bpm=120.0, pre=list(pre))
        e = self.e = pr.e
        self.calls = []; self.ifpm = []; self.tt = []
        self.ttype = [0] * 16; self.mute = [0] * 16
        self._stub = SENTINEL + 0x400
        e.add_watch(MGR_SLOT2, lambda em: self.ifpm.append((em.r(0), em.r(1), em.r(2))))
        e.add_watch(TT_SET, lambda em: self.tt.append((em.r(1), em.r(2))))
        self.T = T = e.malloc(0x284); e.wr(T, b"\0" * 0x284)
        self.mgr1, self.mgr2 = {}, {}
        for t in range(16):
            # ITrack stand-in at T+4[t]: slot 16 (+0x40) track type, slot 12 (+0x30) -> ITrackMixer stand-in, slot 14 (+0x38)
            if t == 0:
                self._mixid, self._itid = {}, {}
                self._mixvt = self._vt({0x30: (lambda em: em.setr(0, self.mute[self._mixid[em.r(0)]]))})
                self._itvt = self._vt({0x40: (lambda em: em.setr(0, self.ttype[self._itid[em.r(0)][0]])),
                                       0x30: (lambda em: em.setr(0, self._itid[em.r(0)][1])),
                                       0x38: (lambda em: em.setr(0, self.ttype[self._itid[em.r(0)][0]]))})
            mix = e.malloc(16); e.w32(mix, self._mixvt); self._mixid[mix] = t
            it = e.malloc(16); e.w32(it, self._itvt); self._itid[it] = (t, mix)
            e.w32(T + 4 + 4 * t, it)
            m1 = pr.mgr[t]; e.w32(m1, VT_IFPM)                       # stand-in managers with the REAL IFPM vtable
            p2 = e.malloc(0x148); e.w32(p2, VT_PROC); e.w32(p2 + 0x98, pr.table); e.w32(p2 + 0xa0, t)
            m2 = e.malloc(0x98); e.w32(m2, VT_IFPM); e.w32(m2 + 0x1c, p2)
            self.mgr1[t], self.mgr2[t] = m1, m2
            e.w32(T + 0xc4 + 8 * t, m1); e.w32(T + 0xc8 + 8 * t, m2)
            for off, nm in RECV.items():
                e.w32(T + off + 4 * t, self._recorder(nm, t))
        self.mgrname = {**{v: ("FX1", k) for k, v in self.mgr1.items()}, **{v: ("FX2", k) for k, v in self.mgr2.items()}}

    def _fn(self, cb):
        a = self._stub; self._stub += 4
        assert a < SENTINEL + 0x1000
        self.e.add_watch(a, cb); return a

    def _vt(self, slots):
        e = self.e; vt = e.malloc(0x100)
        dflt = self._fn(lambda em: em.setr(0, 0))
        for k in range(0, 0x100, 4): e.w32(vt + k, dflt)
        for off, cb in slots.items(): e.w32(vt + off, self._fn(cb))
        return vt

    def _obj(self, slots):
        e = self.e; vt = e.malloc(0x100)
        dflt = self._fn(lambda em: em.setr(0, 0))
        for k in range(0, 0x100, 4): e.w32(vt + k, dflt)
        for off, cb in slots.items(): e.w32(vt + off, self._fn(cb))
        o = e.malloc(16); e.w32(o, vt); return o

    def _recorder(self, nm, t):
        """recorder object: one shared vtable for all recorders; the callee identifies (category, track) from r0"""
        e = self.e
        if not hasattr(self, "_rvt"):
            self._rid = {}
            self._rvt = vt = e.malloc(0x100)
            dflt = self._fn(lambda em: em.setr(0, 0))
            for k in range(0, 0x100, 4): e.w32(vt + k, dflt)
            for s in range(2, 12):
                e.w32(vt + 4 * s, self._fn(lambda em, s=s: self.calls.append(self._rid[em.r(0)] + (s, em.r(1), em.r(2), em.r(3)))
                                           or em.setr(0, 0)))
        o = e.malloc(16); e.w32(o, self._rvt); self._rid[o] = (nm, t)
        return o

    def step(self, track, ttype, stepidx=5, locks=()):
        e = self.e; st = e.malloc(0xa8); e.wr(st, b"\0" * 0xa8)
        e.call(STEP_CTOR, st, ttype)
        e.w32(st, track); e.w32(st + 4, stepidx)
        for idx, v in locks: e.call(STEP_SET, st, idx, v & 0xffffffff, 0)
        return st

    def clear(self):
        self.calls.clear(); self.ifpm.clear(); self.tt.clear()
        self.e.call(ERASER5, self.pr.eraser)

    def row(self, t): return self.e.u32(self.pr.flags + 4 * t), self.e.u32(self.pr.offs + 4 * t)


def predict(track, ttype, tt, mute, off):
    """Our reading of 0x199ae0 (+ 0x1263f4): what the IFPMs and the trigger table receive."""
    ifpm = [] if tt == 2 else [("FX1", track, off, 8 if mute else ttype), ("FX2", track, off, 8 if mute else ttype)]
    fire = tt != 2 and not mute and ttype in (11, 15)
    return ifpm, fire


def e1(J):
    P("\n== E1 real dispatcher 0x199ae0(T, offset, StepData) with a constructed receiver table")
    rig = Rig()
    e = rig.e
    st0 = rig.step(4, 15)
    hdr = [e.u32(st0 + k) for k in (0, 4, 8)]
    words = [e.u32(st0 + 12 + 4 * s) for s in range(35)]
    def v22(w):
        x = (w << 2) & 0xffffffff; x = x - (1 << 32) if x & 0x80000000 else x
        return x >> 10
    nempty = sum(1 for w in words if v22(w) == -0x8000)
    P("  real StepData ctor 0x350600(step, 15): header (+0,+4,+8) after our track/step writes = %s; %d of 35 lock words empty "
      "(value22 = -32768)" % (hdr, nempty))
    check(e.u32(st0 + 8) == 15, "StepData ctor stores its trigger-type argument at +8")
    rows = []; nbad = 0; ncase = 0
    for track in (0, 7, 15):
        for ttype in (0, 8, 9, 10, 11, 12, 15):
            for tt in (0, 1, 2):
                for mute in (0, 1):
                    for off in (0, 23, 63):
                        rig.clear(); rig.ttype[track] = tt; rig.mute[track] = mute
                        st = rig.step(track, ttype)
                        e.call(DISPATCH, rig.T, off, st)
                        got_ifpm = [rig.mgrname[m] + (o, ty) for m, o, ty in rig.ifpm]
                        fl = [t for t in range(16) if rig.row(t)[0]]
                        got_fire = fl == [track] and rig.row(track)[1] == off and rig.tt == [(track, off), (track, off)]
                        exp_ifpm, exp_fire = predict(track, ttype, tt, mute, off)
                        ok = got_ifpm == exp_ifpm and (got_fire if exp_fire else (not fl and not rig.tt))
                        # other receivers: which slot-2 (+8) calls arrived, with which (offset, type)
                        s2 = sorted(set((nm, o, ty) for nm, t, s, o, ty, _ in rig.calls if s == 2))
                        s3 = sorted(set((nm, o, ty) for nm, t, s, o, ty, _ in rig.calls if s == 3))
                        rows.append({"track": track, "type": ttype, "tt": tt, "mute": mute, "off": off, "ifpm": got_ifpm,
                                     "fire": bool(fl), "slot2": s2, "slot3": s3, "ok": ok})
                        ncase += 1; nbad += 0 if ok else 1
                        rig.ttype[track] = 0; rig.mute[track] = 0
    check(nbad == 0, "%d dispatcher cases (tracks 0/7/15 x types 0,8,9,10,11,12,15 x track type Sample/Thru/Midi x mute 0/1 x "
                     "offsets 0/23/63): FX1 then FX2 manager slot 2 get (offset unchanged, mute ? 8 : StepData+8) for non-Midi "
                     "tracks, none for Midi; the trigger table row = track index is set (offset unchanged) iff type is 11 or 15, "
                     "not muted, not Midi; %d mismatches" % (ncase, nbad))
    # other receivers (summarised): which get slot 2 (+8) / slot 3 (+0xc) and with which values
    summ = {}
    for r in rows:
        for nm, o, ty in r["slot2"]:
            summ.setdefault(("slot2", nm, r["tt"]), set()).add((o == r["off"], ty == r["type"]))
        for nm, o, ty in r["slot3"]:
            summ.setdefault(("slot3", nm, r["tt"]), set()).add((o == r["off"], ty == r["type"]))
    for k in sorted(summ):
        P("  %s of %-18s for track type %d: (offset equal, type equal) = %s" % (k[0], k[1], k[2], sorted(summ[k])))
    exp_keys = {("slot2", "lfo(+0x144)", 0), ("slot2", "lfo(+0x144)", 1), ("slot2", "lfo(+0x144)", 2),
                ("slot2", "trackunit(+0x184)", 0), ("slot2", "trackunit(+0x184)", 1), ("slot2", "midi(+0x1c4)", 2),
                ("slot3", "player(+0x44)", 0)}
    check(set(summ) == exp_keys and all(v == {(True, True)} for v in summ.values()),
          "other receivers: LFO (+0x144) slot 2 for every track type; TrackUnit (+0x184) slot 2 for Sample/Thru; MIDI formatter "
          "(+0x1c4) slot 2 for Midi; player (+0x44) slot 3 (+0xc) for Sample only; all with the same (offset, StepData type), "
          "mute does not change them")
    # alternative: is the override driven by solo / anything other than the ITrackMixer slot-12 value? (mute stub only)
    rig.clear(); rig.mute[2] = 1; e.call(DISPATCH, rig.T, 10, rig.step(2, 11))
    check([x[2] for x in rig.ifpm] == [8, 8] and not rig.tt, "mute stub = 1 (ITrackMixer slot 12 = TrackData muteSetting): both "
                                                              "managers get type 8, no trigger")
    rig.mute[2] = 0
    # two events for one track in one block: the later offset wins (TriggerTable_set overwrites)
    rig.clear()
    e.call(DISPATCH, rig.T, 10, rig.step(6, 15)); e.call(DISPATCH, rig.T, 40, rig.step(6, 11))
    check(rig.row(6) == (1, 40), "two triggers on one track inside one block: table row keeps the later dispatch's offset (40)")
    J["e1"] = {"cases": ncase, "mismatches": nbad, "rows": rows}
    return rows


def e2(J):
    P("\n== E2 real Sequencer::processStep 0x19412c(seq, offset, step, flags) -> dispatcher -> 0x1263f4")
    rig = Rig(); e = rig.e
    seq = e.malloc(0x1900); e.wr(seq, b"\0" * 0x1900)
    vt = e.malloc(0x400)
    zero = rig._fn(lambda em: em.setr(0, 0))
    for k in range(0, 0x400, 4): e.w32(vt + k, zero)
    e.w32(seq, vt); e.w32(seq + 0x1d0, rig.T)
    lst = e.malloc(12); e.wr(lst, b"\0" * 12); e.w32(seq + 0x1cc, lst)          # track list used by FULL steps (bit 2)
    def switchable(nbytes=0x100):
        """SwitchableObject<T,17> stand-in: +8 -> current index cell (0); +0x50 slot table[0] = 0; +0xc -> zeroed T data"""
        so = e.malloc(0x100); e.wr(so, b"\0" * 0x100); cell = e.malloc(4); e.w32(cell, 0); e.w32(so + 8, cell)
        d = e.malloc(nbytes); e.wr(d, b"\0" * nbytes); e.w32(so + 0xc, d); return so
    for t in range(16):
        e.w32(seq + 0xb8 + 4 * t, switchable())       # prj::PlaybackData (read by realtime FULL steps)
        e.w32(seq + 0x178 + 4 * t, switchable())      # prj::SequencerData (read only if params 11/12 are empty)
    nbad = 0; res = []
    for ttype in (0, 8, 11, 15):
        for flags in (2, 3):
            for off in (0, 41):
                rig.clear()
                e.wr(seq + 0xd90, b"\0" * (0xa0 * 16))                      # forget the last stored FULL step (see dedupe below)
                st = rig.step(9, ttype, locks=((0xb, 1), (0xc, 2)))         # retrigger count 1, speed index 2 (no SequencerData reads)
                if e.error: break
                e.call(PROCSTEP, seq, off, st, flags)
                got = [(rig.mgrname[m], o, ty) for m, o, ty in rig.ifpm]
                exp = [(("FX1", 9), off, ttype), (("FX2", 9), off, ttype)]
                fire = rig.row(9)
                ok = got == exp and (fire == (1, off) if ttype in (11, 15) else fire == (0, 0)) and e.error is None
                nbad += 0 if ok else 1
                res.append({"type": ttype, "flags": flags, "off": off, "ifpm": [(a[0], a[1], b, c) for a, b, c in got],
                            "row": fire, "ok": ok, "err": e.error})
    P("  cases: %s" % [(r["type"], r["flags"], r["off"], r["row"]) for r in res])
    check(nbad == 0, "processStep passes offset and StepData type unchanged to both managers (types 0/8/11/15, flags 2 = pattern "
                     "step, 3 = realtime; offsets 0/41); only 11/15 set the table; %d mismatches" % nbad)
    # dedupe: a realtime FULL step (flags bit 0, bit 2 clear) identical (0x351174) to the last FULL step stored for the track at
    # seq+0xd90+0xa0*t is dropped unless byte seq+0xe2c+0xa0*t (or seq+0x21b+t) is set
    dd = []
    for label, second_locks, byte_e2c in (("identical", ((0xb, 1), (0xc, 2)), 0), ("different lock (param 3)", ((0xb, 1), (0xc, 2), (3, 7)), 0),
                                          ("identical, +0xe2c byte set", ((0xb, 1), (0xc, 2)), 1)):
        e.wr(seq + 0xd90, b"\0" * (0xa0 * 16)); rig.clear()
        e.call(PROCSTEP, seq, 12, rig.step(9, 15, locks=((0xb, 1), (0xc, 2))), 2)      # pattern FULL step
        n1 = len(rig.ifpm)
        e.wr(seq + 0xe2c + 0xa0 * 9, bytes([byte_e2c]))
        e.call(PROCSTEP, seq, 30, rig.step(9, 15, locks=second_locks), 3)              # realtime FULL step
        dd.append((label, n1, len(rig.ifpm) - n1, rig.row(9)))
        e.wr(seq + 0xe2c + 0xa0 * 9, b"\0")
    P("  pattern FULL @12 then realtime FULL @30 on track 9: (case, IFPM calls first, IFPM calls second, table row) = %s" % dd)
    check([x[2] for x in dd] == [0, 2, 2] and dd[0][3] == (1, 12) and dd[1][3] == (1, 30) and dd[2][3] == (1, 30),
          "realtime FULL step identical to the track's last stored FULL step is not dispatched (no duck re-trigger); a different "
          "step, or byte seq+0xe2c+0xa0*t set, is dispatched")
    J["e2_dedupe"] = dd
    rc = [e.u32(seq + 0x290 + 0x18 * 9 + k) for k in (0x10, 0x14)]
    P("  after the last FULL step: retrigger record seq+0x290+0x18*9: count +0x10 = %d, mode +0x14 = %d" % (rc[0], rc[1] - (1 << 32) if rc[1] & 0x80000000 else rc[1]))
    J["e2"] = res


def e3(J):
    P("\n== E3 end to end: StepData -> 0x199ae0 -> 0x1263f4 -> table -> real InsertFxProcessor processBlock + real Ducker vs model")
    out = bytearray(); summary = []
    cases = [
        ("own track 3, FULL (15) @17", 3, 3, {10: [(3, 15, 17, 0, 0)]}, {10: 17}),
        ("own track 3, HALF (11) @5", 3, 3, {10: [(3, 11, 5, 0, 0)]}, {10: 5}),
        ("own track 3, PARAM-only (8) @5", 3, 3, {10: [(3, 8, 5, 0, 0)]}, {}),
        ("own track 3 muted, FULL @5", 3, 3, {10: [(3, 15, 5, 0, 1)]}, {}),
        ("own track 3 as Midi track, FULL @5", 3, 3, {10: [(3, 15, 5, 2, 0)]}, {}),
        ("own track 3 Thru, FULL @30", 3, 3, {10: [(3, 15, 30, 1, 0)]}, {10: 30}),
        ("SOURCE 5: track-5 FULL @9, track-3 FULL @20", 3, 5, {10: [(5, 15, 9, 0, 0)], 40: [(3, 15, 20, 0, 0)]}, {10: 9}),
        ("two steps one block @10 then @40", 3, 3, {10: [(3, 15, 10, 0, 0), (3, 11, 40, 0, 0)]}, {10: 40}),
        ("empty type 0 @5", 3, 3, {10: [(3, 0, 5, 0, 0)]}, {}),
    ]
    Ls, Rs = H41.signal("noise", 80, seed=5)
    nbit_all = 0
    for name, own, src, sched, exp_first in cases:
        rig = Rig(own=own, source=src); e = rig.e; pr = rig.pr
        m = H41.Model(); m.insert_defaults(); m.set_param(0, 0.004); m.set_param(2, 0.001); m.set_param(10, float(src))
        duck = []; first = {}; nbit = 0; nsamp = 0
        for b in range(80):
            for tr, ty, of, tt, mu in sched.get(b, []):
                rig.ttype[tr] = tt; rig.mute[tr] = mu
                e.call(DISPATCH, rig.T, of, rig.step(tr, ty))
                rig.ttype[tr] = 0; rig.mute[tr] = 0
            row = (e.u32(pr.flags + 4 * src), e.u32(pr.offs + 4 * src))
            bL = Ls[b * N:(b + 1) * N]; bR = Rs[b * N:(b + 1) * N]
            pr.block(bL, bR)
            cin = pr.cap.get("in"); cout = pr.cap.get("out")
            if b == 0: m.reset(); m.dry, m.wet = 0.0, 1.0
            for idx, v in ((7, 120.0), (8, float(row[0])), (9, float(row[1]))): m.set_param(idx, v)
            if cin is None: continue
            mL, mR = m.process(cin[3], cin[4])
            for p_, q_ in zip(mL + mR, cout[0] + cout[1]):
                nsamp += 1; nbit += f2u(p_) != f2u(q_)
            out += struct.pack("<%df" % (2 * N), *(cout[0] + cout[1]))
            ch = [i for i in range(N) if cout[0][i] != cin[3][i] or cout[1][i] != cin[4][i]]
            if ch: duck.append(b)
            if ch and (b - 1) not in duck: first[b] = ch[0]
        ok = first == exp_first and nbit == 0
        nbit_all += nbit
        summary.append({"case": name, "first_change": first, "expected": exp_first, "model_mismatch": nbit, "samples": nsamp, "ok": ok})
        P("  %-46s duck starts %s (expected %s); model vs emulation: %d of %d samples differ" % (name, first, exp_first, nbit, nsamp))
        check(ok, name)
    J["e3"] = summary
    open(os.path.join(J["_out"], "e3_outputs.f32"), "wb").write(bytes(out))
    J["e3_sha"] = sha(bytes(out))
    P("  e3_outputs.f32 sha256 %s" % J["e3_sha"])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H049"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    J = {"_out": a.out}
    im = sp16img.Image()
    static_checks(im, J)
    e1(J); e2(J); e3(J)
    P("\nRESULT: %d failed checks" % len(FAILS))
    J.pop("_out")
    rep = "\n".join(LOG) + "\n"
    open(os.path.join(a.out, "h049_report.txt"), "w").write(rep)
    js = json.dumps(J, indent=0, sort_keys=True, default=str)
    open(os.path.join(a.out, "h049.json"), "w").write(js)
    print("report sha256 %s  json sha256 %s" % (sha(rep.encode()), sha(js.encode())))


if __name__ == "__main__":
    main()
