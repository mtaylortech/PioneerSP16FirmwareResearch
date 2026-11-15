#!/usr/bin/env python3
"""H052 — TrackUnit routing mode +0x61c and the external buffers +0x604/+0x608: the DSF (Dave Smith analog filter) loop.

Sections (criteria of kb/cycles/037.md):
  S1  static: who writes the mode (TrackUnit::setSendSource slot 101 0x1ca218 = IDaveSmithSendSource slot 2 via thunk 0x1ca210;
      DaveSmithManager apply 0xc64b0 with table 0x834ac8; IDaveSmithManager setters; MixerViewController popup; prj::RoutingData
      reader 0xc4508), who supplies/fills the external buffers (MultiTrackUnit prepare 0x1c5dc0, MultiTrackUnit::processBlock
      0x1c4ff8 input copies, AudioDeviceInputUnit::processBlock 0x1ad590), and +0x10c (setTrackType 0x1cb584). Instruction / data
      assertions only; short facts are printed, no listings.
  E1  REAL DaveSmithManager apply 0xc64b0 on a DaveSmithManager stand-in whose sources are four TrackUnit stand-ins (IDaveSmithSendSource
      at +0xa8, real thunk 0x1ca210 -> real 0x1ca218 -> real 0x1ca0dc -> real OutputSelector::setSelection 0xe6ff4): resulting +0x61c
      and selector targets for every (route, send mode, send track, filter) in a grid, against harness/models/track_mix.dsf_apply.
  E2  REAL TrackUnit::processBlock 0x1ca58c with four REAL OutputSelectors (ctor 0xe6ee4, processBlock 0xe6b8c), the real routing
      setter (slot 101), distinct signals on source / +0x604 / +0x608, a nonlinear insert stand-in, modes 0/1/2 and switches; every
      block compared bit-exactly with harness/models/track_mix.RoutedTrack. DC runs measure the switch fade (length and shape).
  E3  the 4-track run after E1's apply (selected track Pre/Post FX, others mode 0) vs the model.
  ALT alternatives that must fail: "mode 1 = after the inserts", "mode 2 = before the inserts", "overlap crossfade", "ext +0x604 is the
      DSF return".
Outputs only to --out (default harness/out/H052/). Run: .venv/bin/python -B harness/H052_dsf_loop.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, PC, LR                               # noqa: E402
import sp16img                                                 # noqa: E402
import H009_track_mix as h9                                    # noqa: E402
import track_mix as M                                          # noqa: E402

N = 64
SEL_CTOR, SEL_SET, SEL_PB = 0xe6ee4, 0xe6ff4, 0xe6b8c
TU_S101, TU_SETROUTE, TU_S101_THUNK = 0x1ca218, 0x1ca0dc, 0x1ca210
DSM_APPLY = 0xc64b0
JUCE_AP_CTOR, JUCE_SETPLAY = 0x5f9e00, 0x5f9e90
VT_TU_IDSS = 0x864fbc                     # TrackUnit secondary vtable for IDaveSmithSendSource (+0xa8)


COUNTS = {}                               # entries into real code, summed over all rigs (proves the real routines ran)


def sha(b): return hashlib.sha256(b).hexdigest()
def bits(xs): return [f2u(x) for x in xs]


# ========================================================================================================================= rig
class Rig:
    def __init__(self):
        self.e = e = emu.Emu(insn_limit=80_000_000)
        self.fk = h9.Fakes(e)
        self.juce = []
        e.add_watch(JUCE_AP_CTOR, lambda em: self._skip(em, "AudioProcessor ctor"))
        e.add_watch(JUCE_SETPLAY, lambda em: self._skip(em, "setPlayConfigDetails"))
        for addr, nm in ((SEL_PB, "OutputSelector.processBlock 0xe6b8c"), (SEL_SET, "OutputSelector.setSelection 0xe6ff4"),
                         (TU_SETROUTE, "TrackUnit setRouting 0x1ca0dc"), (h9.TRACK_PB, "TrackUnit.processBlock 0x1ca58c"),
                         (TU_S101_THUNK, "IDaveSmithSendSource thunk 0x1ca210")):
            e.add_watch(addr, lambda em, nm=nm: COUNTS.__setitem__(nm, COUNTS.get(nm, 0) + 1))

    def _skip(self, em, name):
        """Stand-in for two JUCE base-class calls (same as H055): record, store numIn/numOut for setPlayConfigDetails, return."""
        self.juce.append((name, em.r(0), em.r(1), em.r(2)))
        if name == "setPlayConfigDetails":
            em.w32(em.r(0) + 0x2c, em.r(1)); em.w32(em.r(0) + 0x30, em.r(2))
        em.uc.reg_write(PC, em.uc.reg_read(LR))

    def selector(self):
        """REAL OutputSelector ctor 0xe6ee4(this, pairs 2, async 0, monoDup 1, xfade 128) — exactly the TrackUnit ctor's arguments."""
        e = self.e
        o = e.malloc(0xa0, "OutputSelector"); e.wr(o, b"\0" * 0xa0)
        e.call(SEL_CTOR, o, 2, 0, 1, stack_args=(0x80,))
        return o

    def track(self, name="T", n_inserts=1, insert_fx=None):
        """H009 TrackRig with its four fake selectors replaced by real ones; +0xb4 task box (zero = run inline); +0xa8 vptr."""
        e = self.e
        t = h9.TrackRig(e, self.fk, name=name, n_inserts=n_inserts, insert_fx=insert_fx)
        t.sel = {}
        for off in (0x10c, 0x110, 0x114, 0x118):
            s = self.selector(); e.w32(t.T + off, s); t.sel[off] = s
        box = e.malloc(0x40, "task box"); e.wr(box, b"\0" * 0x40); e.w32(t.T + 0xb4, box)
        e.w32(t.T + 0xa8, VT_TU_IDSS)
        return t

    def mode_of(self, t): return self.e.u32(t.T + 0x61c)

    def sel_state(self, t):
        e = self.e
        return {hex(off): (e.u32(s + 0x8c), e.u32(s + 0x90), e.u32(s + 0x94), e.u32(s + 0x98)) for off, s in t.sel.items()}

    def set_mode(self, t, m):            # TrackUnit slot 101 (real), r0 = TrackUnit
        self.e.call(TU_S101, t.T, m & 0xffffffff)

    def set_thru(self, t, on):           # what setTrackType 0x1cb584 does to +0x10c at its end (needs prj::TrackData otherwise)
        self.e.call(SEL_SET, t.sel[0x10c], 2 if on else 0, 3 if on else 1)

    def block(self, t, src, e604, e608):
        """one real TrackUnit::processBlock; Mute#2 flag per the 0x1ca3c8 rule applied to the REAL stored mode (+0x61c)."""
        t.src = src
        t.ext[0].write(0, e604[0]); t.ext[0].write(1, e604[1])
        t.ext[1].write(0, e608[0]); t.ext[1].write(1, e608[1])
        t.pre_on = 1 if (t.main_on and self.mode_of(t) != 0) else 0
        return t.block()


def sigs(kind, b, rng):
    return (h9.sig(kind, b, 0, rng), h9.sig(kind, b, 1, rng))


def tone(freq, amp, b):
    return [M.F(amp * math.sin(2 * math.pi * freq * (b * N + i) / 44100.0)) for i in range(N)]


# ========================================================================================================================= main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H052"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []; f32 = {}
    def P(s_=""): rep.append(s_); print(s_, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)

    P("H052 DSF loop routing — target sha256 %s" % emu.SHA)
    im = sp16img.Image()
    def ins(a_): return ["%s %s" % (i_.mnemonic, i_.op_str) for i_ in im.md.disasm(im.data[im.off(a_):im.off(a_) + 4], a_)][0]
    def ti_name(ti): return im.cstr(im.u32(ti + 4), 80)

    # ===================================================================================================== S1 static
    P("\n== S1 static: mode writers, buffer owners, +0x10c")
    sites = {
        # TrackUnit ctors: +0x61c := 0, then slot 101 with the stored value
        0x1cd09c: "str r8, [r4, #0x61c]", 0x1cd670: "ldr r1, [r4, #0x61c]", 0x1cd67c: "bl #0x1ca218",
        0x1cdd5c: "str r6, [r4, #0x61c]", 0x1ce328: "ldr r1, [r4, #0x61c]", 0x1ce334: "bl #0x1ca218",
        # slot 101 tail-calls 0x1ca0dc (same-thread path), async task 0x1c7d90 re-calls slot 101 (vt+0x194) with the stored arg
        0x1ca39c: "b #0x1ca0dc", 0x1ca3ac: "b #0x1ca0dc", 0x1c7da4: "ldr r3, [r3, #0x194]", 0x1c7da8: "blx r3",
        # IDaveSmithSendSource thunk (TrackUnit +0xa8)
        0x1ca210: "sub r0, r0, #0xa8", 0x1ca214: "b #0x1ca218", 0x1ce944: "sub r0, r0, #0xa8",
        # DaveSmithManager apply 0xc64b0: selector +0x9c slot 2 (send track), route==1 && filter -> table[sendMode] for the
        # selected source, 0 for others; else 0 for all
        0xc64b8: "ldr r0, [r0, #0x9c]", 0xc64c8: "ldr r3, [r3, #8]", 0xc64d4: "cmp r3, #1", 0xc6530: "ldrb r3, [r6, #0xc]",
        0xc6544: "cmp r3, #1", 0xc6554: "ldrls r8, [r3, #0x5e0]", 0xc658c: "cmp r2, r4", 0xc6594: "moveq r1, r8",
        0xc64f4: "mov r1, #0", 0xc6574: "mov r1, #0",
        # DaveSmithManager::processBlock state machine 0xc6be0 (slot 5): state 2 -> apply(+0xe4); input mutes 0x1ae2bc(+0x98, 1/0)
        0xc6c78: "bl #0xc64b0", 0xc6c44: "bl #0xc65dc", 0xc6e28: "mov r1, #1", 0xc6e2c: "bl #0x1ae2bc", 0xc6e58: "mov r1, #0",
        # IDaveSmithManager setters (pending state +0xd0 route / +0xd4 send source / +0xd8 track / +0xdc filter)
        0xc4afc: "streq r3, [r0, #0xd0]", 0xc4db8: "str sl, [r6, #0xd8]", 0xc4dbc: "str r3, [r6, #0xd0]",
        0xc510c: "str sl, [r6, #0xd4]", 0xc4f64: "str sl, [r6, #0xd0]", 0xc41e4: "strb r3, [r0, #0xdc]",
        0xc41f8: "strb r3, [r0, #0xdc]",
        # MixerViewController ANALOG FILTER popup 0x26b6ac: row 0 -> assignToMaster (+0x1c) / assignToTrack(i) (+0x20);
        # row 1 -> setSendTrackSource (+0x38) 0 (Pre FX) / 1 (Post FX)
        0x26b754: "ldr r3, [r3, #0x1c]", 0x26b844: "ldr r3, [r3, #0x20]",
        # MultiTrackUnit prepare 0x1c5dc0: MTU+0x100 / +0x198 (2 ch each) -> every TrackUnit +0x604 / +0x608
        0x1c5f9c: "add sl, r7, #0x100", 0x1c5fa4: "add r8, r7, #0x198", 0x1c5fa8: "mov r1, #2", 0x1c5fc8: "mov r1, #2",
        0x1c6004: "mov r1, sl", 0x1c6008: "bl #0x1c9a4c", 0x1c6010: "mov r1, r8", 0x1c6014: "bl #0x1c9a54",
        # MultiTrackUnit::processBlock 0x1c4ff8: copies its input pairs into +0x100 (pair at 0xf53c9c) and +0x198 (0xf53c38) first
        0x1c5168: "add fp, r4, #0x100", 0x1c51a8: "bl #0x577d5c", 0x1c51dc: "add r7, r4, #0x198", 0x1c521c: "bl #0x577d5c",
        0x1c524c: "bl #0x577d5c",
        # setTrackType 0x1cb584 is where +0x10c is selected (Thru -> (2,3)); TrackUnit setters
        0x1c9a4c: "str r1, [r0, #0x604]", 0x1c9a54: "str r1, [r0, #0x608]",
    }
    bad = {hex(k_): (ins(k_), v) for k_, v in sites.items() if ins(k_) != v}
    P("  %d instruction assertions: %s" % (len(sites), "all match" if not bad else bad))
    J["s1_bad"] = bad
    # data facts
    tab = [im.u32(0x834ac8), im.u32(0x834ac8 + 4)]
    vt_tu = {"slot101": hex(im.u32(0x864cac + 101 * 4)), "slot102": hex(im.u32(0x864cac + 102 * 4)),
             "IDSS@+0xa8 off2top": hex(im.u32(VT_TU_IDSS - 8)), "IDSS slot2": hex(im.u32(VT_TU_IDSS + 8)),
             "IDSS slot3": hex(im.u32(VT_TU_IDSS + 12))}
    ti = im.u32(0x864cac - 4); nb = im.u32(ti + 12)
    bases = {ti_name(im.u32(ti + 16 + 8 * k_)): hex(im.u32(ti + 20 + 8 * k_) >> 8) for k_ in range(nb)}
    mti = im.u32(0x864570 - 4)
    mbases = {ti_name(im.u32(mti + 16 + 8 * k_)): hex(im.u32(mti + 20 + 8 * k_) >> 8) for k_ in range(im.u32(mti + 12))}
    pairs = {hex(a_): (struct.unpack("<ii", im.data[im.off(a_):im.off(a_) + 8])) for a_ in (0x1c59c0, 0x1c59d0, 0x1c59d8)}
    strings = {hex(a_): im.cstr(a_, 120) for a_ in (0x865288, 0x834d7c, 0x834d98, 0x834db4, 0x834dcc, 0x8a5464, 0x8a5488,
                                                    0x8a54ec, 0x8a5584, 0x882078, 0x882090, 0x8820a0, 0x88214c, 0x882154,
                                                    0x936564, 0x936584, 0x936400)}
    tu_setsel = sorted({hex(im.func_of(s_)[0]) for s_, t_, k_ in im.direct_calls() if t_ == SEL_SET and 0x1c3000 <= s_ < 0x1d0000})
    n_setsel = sum(1 for s_, t_, k_ in im.direct_calls() if t_ == SEL_SET and 0x1c3000 <= s_ < 0x1d0000)
    w101 = sorted({hex(s_) for s_, t_, k_ in im.direct_calls() if t_ in (TU_S101, TU_SETROUTE)})
    P("  direct setSelection 0xe6ff4 calls in TrackUnit/MTU code 0x1c3000-0x1d0000: %d, in functions %s; direct branches to "
      "slot 101 / 0x1ca0dc: %s" % (n_setsel, tu_setsel, w101))
    J["s1_setsel"] = (n_setsel, tu_setsel, w101)
    if not (n_setsel == 11 and tu_setsel == ["0x1ca0dc", "0x1cb584"] and
            w101 == ["0x1ca214", "0x1ca39c", "0x1ca3ac", "0x1cd67c", "0x1ce334"]):
        bad["setsel"] = (n_setsel, tu_setsel, w101)
    task_ti = im.u32(0x864b64 - 4)
    P("  table 0x834ac8 (send source -> TrackUnit mode): %s" % tab)
    P("  TrackUnit vtable: %s" % vt_tu)
    P("  TrackUnit bases: %s" % bases)
    P("  MultiTrackUnit bases: %s" % mbases)
    P("  channel-pair literals 0x1c59c0/0x1c59d0/0x1c59d8 (MTU input copies): %s" % pairs)
    P("  slot-101 task class: %s" % ti_name(task_ti))
    for k_, v in strings.items(): P("  string %s: %s" % (k_, v))
    J["s1_data"] = {"table": tab, "vt": vt_tu, "bases": bases, "mtu_bases": mbases, "pairs": pairs, "strings": strings}
    check(not bad and tab == [1, 2] and bases.get("20IDaveSmithSendSource") == "0xa8" and vt_tu["IDSS slot2"] == "0x1ca210"
          and vt_tu["slot101"] == "0x1ca218" and mbases.get("28IDaveSmithSendSourceSelector") == "0x80"
          and pairs == {"0x1c59c0": (0, 1), "0x1c59d0": (4, 5), "0x1c59d8": (2, 3)},
          "static: +0x61c is written only by TrackUnit::setSendSource(IDaveSmithSendSource::SendSource) (slot 101 = IDaveSmithSendSource "
          "slot 2 via thunk 0x1ca210; ctors pass the initial 0; its async task re-posts the same value); the only caller with a value "
          "is DaveSmithManager apply 0xc64b0 (table 0x834ac8 = [1, 2]); +0x604 = MultiTrackUnit+0x100 <- MTU input ch 0/1, "
          "+0x608 = MultiTrackUnit+0x198 <- MTU input ch 4/5, both copied at the start of MultiTrackUnit::processBlock")

    # ===================================================================================================== E1 apply grid
    P("\n== E1 real DaveSmithManager apply 0xc64b0 -> real TrackUnit::setSendSource -> real OutputSelector::setSelection")
    R = Rig(); e = R.e
    NT = 4
    trs = [R.track(name="T%d" % k_, n_inserts=1, insert_fx=[h9.fx_shape]) for k_ in range(NT)]
    sel_log = []
    selfake = R.fk.obj("MTU.IDaveSmithSendSourceSelector", {8: lambda em, nm: sel_log.append(em.r(1) - (1 << 32) if em.r(1) >> 31 else em.r(1))})
    DSM = e.malloc(0x118, "DaveSmithManager stand-in"); e.wr(DSM, b"\0" * 0x118)
    src_arr = e.malloc(4 * NT, "sources"); [e.w32(src_arr + 4 * k_, trs[k_].T + 0xa8) for k_ in range(NT)]
    e.w32(DSM + 0x9c, selfake); e.w32(DSM + 0xa0, src_arr); e.w32(DSM + 0xa4, NT); e.w32(DSM + 0xa8, NT)
    st = e.malloc(0x10, "DSM state")
    def apply(route, smode, track, filt):
        e.wr(st, struct.pack("<iiiB3x", route, smode, track, filt))
        sel_log.clear(); e.call(DSM_APPLY, DSM, st)
        return [R.mode_of(t) for t in trs], list(sel_log)
    grid_bad = []; grid = []
    exp_sel = {0: ((0, 1), (0, 1), (0, 1)), 1: ((2, 3), (0, 1), (0, 1)), 2: ((0, 1), (2, 3), (2, 3))}
    for route in (0, 1, 2):
        for smode in (0, 1, 2, 3):
            for track in range(NT):
                for filt in (0, 1):
                    modes, sl = apply(route, smode, track, filt)
                    want = M.dsf_apply(route, smode, track, filt, NT)
                    selok = all((tuple(e.u32(t.sel[0x110] + o) for o in (0x8c, 0x90)),
                                 tuple(e.u32(t.sel[0x118] + o) for o in (0x8c, 0x90)),
                                 tuple(e.u32(t.sel[0x114] + o) for o in (0x8c, 0x90))) == exp_sel[m] for t, m in zip(trs, modes))
                    grid.append(((route, smode, track, filt), modes, sl))
                    if modes != want or sl != [track] or not selok: grid_bad.append(((route, smode, track, filt), modes, want, sl, selok))
    P("  grid route {0,1,2} x send mode {0..3} x track {0..3} x filter {0,1} = %d applies; mismatches vs model / selector "
      "targets / MTU selector call: %d" % (len(grid), len(grid_bad)))
    for g_ in grid:
        if g_[0][2] == 1 and g_[0][3] == 1 and g_[0][0] <= 1 and g_[0][1] <= 2:
            P("    route %d send %d track %d filter %d -> TrackUnit modes %s, MTU setSendSourceIndex(%s)" % (g_[0] + (g_[1], g_[2])))
    J["e1_grid_bad"] = grid_bad; J["e1_grid_n"] = len(grid)
    # invalid mode value directly into slot 101 leaves everything unchanged
    R.set_mode(trs[0], 1); before = (R.mode_of(trs[0]), R.sel_state(trs[0]))
    R.set_mode(trs[0], 3); R.set_mode(trs[0], -1); after = (R.mode_of(trs[0]), R.sel_state(trs[0]))
    P("  slot 101 with 3 and -1 after mode 1: unchanged = %s" % (before == after))
    check(not grid_bad and before == after,
          "mode values: the selected track gets 1 (Pre FX) or 2 (Post FX) only when route = Track (1) and the filter flag is set; all "
          "other tracks, route Master (0), route >1, filter off, or send mode >= 2 give 0; the MTU send selector always receives the "
          "send track index; slot 101 ignores values other than 0/1/2")

    # ===================================================================================================== E2 modes
    P("\n== E2 real TrackUnit::processBlock + real OutputSelectors: modes 0/1/2 and switches vs RoutedTrack")
    def run(schedule, name, kinds=("noise", "sine", "steps"), inserts=(h9.fx_shape,), thru_at=None, mute_at=None, seed=5):
        """schedule: {block: mode}; distinct signals: source = kinds[0], +0x604 = kinds[1] (tone), +0x608 = kinds[2]."""
        R_ = Rig(); t = R_.track(name=name, n_inserts=len(inserts), insert_fx=list(inserts))
        t.set(fader=100, pan=0, send=127)
        mdl = M.RoutedTrack(fader=100, pan=0, send=127, main_on=True, pre_on=False)
        rng = random.Random(seed); nb = max(schedule) + 40
        diff = 0; first = None; rows = []
        for b in range(nb):
            if b in schedule:
                R_.set_mode(t, schedule[b]); mdl.set_mode(schedule[b])
            if thru_at is not None and b in thru_at:
                R_.set_thru(t, thru_at[b]); mdl.set_thru(thru_at[b])
            if mute_at is not None and b in mute_at:
                t.main_on = mute_at[b]; mdl.main_on = bool(mute_at[b])
            src = sigs(kinds[0], b, rng)
            e604 = (tone(330.0, 0.6, b), tone(495.0, 0.6, b)) if kinds[1] == "tone" else sigs(kinds[1], b, rng)
            e608 = sigs(kinds[2], b, rng)
            o = R_.block(t, src, e604, e608)
            m = mdl.process(src[0], src[1], e604, e608, inserts=list(inserts))
            d = sum(bits(o[c]) != bits(m[c]) for c in range(6))
            if d and first is None: first = (b, [c for c in range(6) if bits(o[c]) != bits(m[c])])
            diff += d
            rows.append(R_.mode_of(t))
            for c in range(6): f32.setdefault("e2_%s" % name, []).extend(o[c])
        return {"blocks": nb, "diff_channel_blocks": diff, "first": first, "modes": rows, "samples": nb * N * 6}
    runs = {
        "mode0": run({0: 0}, "mode0"),
        "mode1": run({0: 1}, "mode1"),
        "mode2": run({0: 2}, "mode2"),
        "switch_0_1_2_0": run({0: 0, 30: 1, 70: 2, 110: 0}, "switch_0_1_2_0"),
        "switch_0_2_1_0": run({0: 0, 30: 2, 70: 1, 110: 0}, "switch_0_2_1_0", seed=6),
        "fast_switch": run({0: 0, 30: 1, 31: 2, 32: 0, 33: 2, 35: 1}, "fast_switch", seed=7),
        "thru_mode2": run({0: 0, 10: 2, 60: 1}, "thru_mode2", kinds=("noise", "tone", "sine"), thru_at={0: True, 90: False}, seed=8),
        "mode1_mute": run({0: 1}, "mode1_mute", mute_at={20: 0, 40: 1}, seed=9),
        "mode2_noinsert": run({0: 2}, "mode2_noinsert", inserts=(), seed=10),
        "mode1_2inserts": run({0: 0, 5: 1, 50: 2}, "mode1_2inserts", inserts=(h9.fx_shape, h9.fx_clip), seed=11),
    }
    tot_s = sum(r_["samples"] for r_ in runs.values()); tot_d = sum(r_["diff_channel_blocks"] for r_ in runs.values())
    for k_, r_ in runs.items():
        cnt = {m_: r_["modes"].count(m_) for m_ in (0, 1, 2)}
        P("  %-16s %3d blocks (mode block counts %s): channel-blocks differing from the model %d%s" % (
            k_, r_["blocks"], cnt, r_["diff_channel_blocks"], (" first %s" % (r_["first"],)) if r_["first"] else ""))
    J["e2_runs"] = {k_: {kk: vv for kk, vv in r_.items() if kk != "modes"} for k_, r_ in runs.items()}
    check(tot_d == 0 and all(runs[k_]["modes"].count(m_) >= 30 for k_, m_ in (("mode0", 0), ("mode1", 1), ("mode2", 2))),
          "real TrackUnit + real OutputSelectors vs model RoutedTrack: %d runs, %d samples (6 ch), 0 channel-blocks differ; >= 30 "
          "blocks in each steady mode" % (len(runs), tot_s))

    # what each mode does (signal identity check with the model's own pieces): mode 1 main = fx(ext608), ch4/5 = source; mode 2
    # main = ext608 (post-insert replaced), ch4/5 = fx(source) — shown on block 35 of the steady runs
    def ident(mode, b=35):
        R_ = Rig(); t = R_.track(name="id", n_inserts=1, insert_fx=[h9.fx_shape]); t.set(fader=100, pan=0, send=127)
        R_.set_mode(t, mode); rng = random.Random(1)
        for k in range(b + 1):
            src = sigs("noise", k, rng); e604 = sigs("sine", k, rng); e608 = sigs("steps", k, rng)
            o = R_.block(t, src, e604, e608)
        fxs = h9.fx_shape(*src); fx8 = h9.fx_shape(*e608)
        return {"main=fx(src)": bits(o[0]) == bits(fxs[0]) and bits(o[1]) == bits(fxs[1]),
                "main=fx(ext608)": bits(o[0]) == bits(fx8[0]) and bits(o[1]) == bits(fx8[1]),
                "main=ext608": bits(o[0]) == bits(e608[0]) and bits(o[1]) == bits(e608[1]),
                "ch45=src": bits(o[4]) == bits(src[0]) and bits(o[5]) == bits(src[1]),
                "ch45=fx(src)": bits(o[4]) == bits(fxs[0]) and bits(o[5]) == bits(fxs[1]),
                "ch45=0": not any(o[4]) and not any(o[5]),
                "send=main": bits(o[2]) == bits(o[0]) and bits(o[3]) == bits(o[1])}
    idt = {m_: ident(m_) for m_ in (0, 1, 2)}
    for m_, d_ in idt.items(): P("  mode %d, block 35 (unity fader/pan, send 127): %s" % (m_, {k_: v for k_, v in d_.items() if v}))
    J["e2_identity"] = idt
    check(idt[0]["main=fx(src)"] and idt[0]["ch45=0"] and idt[1]["main=fx(ext608)"] and idt[1]["ch45=src"]
          and idt[2]["main=ext608"] and idt[2]["ch45=fx(src)"] and all(d_["send=main"] for d_ in idt.values()),
          "mode 0: main = FX(source), DSF send ch4/5 silent (Mute#2); mode 1 (Pre FX): ch4/5 = raw source, main = FX(+0x608 return); "
          "mode 2 (Post FX): ch4/5 = FX(source), main = +0x608 return (inserts' output replaced, before Pan); send tap follows main")

    # switch fade: DC source 1.0 with return 0 shows the fade-out; source 0 with return 1.0 the fade-in
    def fade(src_v, ret_v, frm, to):
        R_ = Rig(); t = R_.track(name="fade", n_inserts=0); t.set(fader=100, pan=0, send=127); R_.set_mode(t, frm)
        dc = lambda v: ([M.F(v)] * N, [M.F(v)] * N)
        for k in range(6): R_.block(t, dc(src_v), dc(0.0), dc(ret_v))
        R_.set_mode(t, to); tr = []
        for k in range(6): tr += R_.block(t, dc(src_v), dc(0.0), dc(ret_v))[0]
        return tr
    fo = fade(1.0, 0.0, 0, 1); fi = fade(0.0, 1.0, 0, 1)
    out_end = next((k_ for k_, v in enumerate(fo) if v == 0.0), -1)
    in_start = next((k_ for k_, v in enumerate(fi) if v != 0.0), -1)
    in_end = next((k_ for k_, v in enumerate(fi) if v == 1.0), -1)
    lin_o = all(abs(fo[k_] - (1.0 - k_ / 128.0)) < 3e-6 for k_ in range(128))
    lin_i = all(abs(fi[128 + k_] - (k_ / 128.0)) < 3e-6 for k_ in range(128))
    P("  switch 0 -> 1 (no inserts, DC): old path 1 -> 0: first zero sample %d, linear %s; new path 0 -> 1: first non-zero sample "
      "%d, reaches 1.0 at %d, linear %s; samples 120..136 old+new sum: %s" % (
          out_end, lin_o, in_start, in_end, lin_i, [round(fo[k_] + fi[k_], 4) for k_ in range(120, 137, 4)]))
    J["e2_fade"] = {"out_end": out_end, "in_start": in_start, "in_end": in_end, "lin_out": lin_o, "lin_in": lin_i}
    f32["e2_fade_out"] = fo; f32["e2_fade_in"] = fi
    check(out_end == 128 and in_start == 129 and in_end == 256 and lin_o and lin_i,
          "switch fade: the old path ramps linearly 1 -> 0 over 128 samples (gain applied before the step), then the new path ramps "
          "0 -> 1 over the next 128 samples — a 256-sample dip through silence, not an overlap crossfade (64-sample blocks: 2 + 2 blocks)")

    # ===================================================================================================== E3 four tracks
    P("\n== E3 four real TrackUnits after a real apply (route Track, send track 2, Post FX) vs model")
    modes, _ = apply(1, 1, 2, 1)
    for t in trs: t.set(fader=100, pan=0, send=100)
    mdls = [M.RoutedTrack(fader=100, pan=0, send=100) for _ in range(NT)]
    for m_, md in zip(modes, mdls): md.set_mode(0); md.sel = {k: M.OutputSelector() for k in md.sel}; md.set_mode(m_)
    # E1 left each track's selectors with targets set but current pairs still (0,1) (no block ran yet), as the fresh models
    rng = random.Random(3); d3 = 0; buses = []
    for b in range(40):
        if b == 20:
            modes2, _ = apply(1, 0, 2, 1); [md.set_mode(m_) for md, m_ in zip(mdls, modes2)]
        outs = []; mouts = []
        for k_, (t, md) in enumerate(zip(trs, mdls)):
            src = sigs(["noise", "sine", "steps", "impulse"][k_], b, rng); e604 = sigs("sine", b, rng); e608 = sigs("noise", b, rng)
            outs.append(R.block(t, src, e604, e608)); mouts.append(md.process(src[0], src[1], e604, e608, inserts=[h9.fx_shape]))
            d3 += sum(bits(outs[-1][c]) != bits(mouts[-1][c]) for c in range(6))
        for c in range(6): f32.setdefault("e3_tracks", []).extend(sum((o[c] for o in outs), []))
    P("  modes after apply(Track, PostFx, 2, on): %s; after apply(Track, PreFx, 2, on) at block 20: %s; 40 blocks x 4 tracks: "
      "channel-blocks differing %d" % (modes, modes2, d3))
    J["e3"] = {"modes": modes, "modes2": modes2, "diff": d3}
    check(modes == [0, 0, 2, 0] and modes2 == [0, 0, 1, 0] and d3 == 0,
          "only the selected send track changes routing; Post FX -> Pre FX on the fly is the 2 -> 1 switch with the selector fades")

    # ===================================================================================================== ALT
    P("\n== ALT alternative explanations (model mutants vs the emulated mode runs)")
    class Swap12(M.RoutedTrack):
        def set_mode(self, mode): super().set_mode({1: 2, 2: 1}.get(mode, mode))
    class Overlap(M.OutputSelector):
        def process(self, chans):
            if self.cur != self.target: self.cur = self.target
            return [chans[self.cur[0]][:], chans[self.cur[1]][:]]
    class Ret604(M.RoutedTrack):
        def process(self, sl, sr, ext604=None, ext608=None, inserts=()): return super().process(sl, sr, ext608, ext604, inserts)
    def mut(cls, sel_cls=None, schedule=None, name="m"):
        R_ = Rig(); t = R_.track(name=name, n_inserts=1, insert_fx=[h9.fx_shape]); t.set(fader=100, pan=0, send=127)
        md = cls(fader=100, pan=0, send=127)
        if sel_cls: md.sel = {k: sel_cls() for k in md.sel}
        rng = random.Random(21); d = 0
        for b in range(60):
            if b in schedule: R_.set_mode(t, schedule[b]); md.set_mode(schedule[b])
            src = sigs("noise", b, rng); e604 = sigs("sine", b, rng); e608 = sigs("steps", b, rng)
            o = R_.block(t, src, e604, e608); m = md.process(src[0], src[1], e604, e608, inserts=[h9.fx_shape])
            d += sum(sum(1 for x, y in zip(bits(o[c]), bits(m[c])) if x != y) for c in range(6))
        return d
    alts = {"mode 1 = after the inserts / mode 2 = before (swapped)": mut(Swap12, schedule={0: 0, 10: 1, 35: 2}),
            "instant switch / overlap crossfade instead of the 128+128 dip": mut(M.RoutedTrack, Overlap, schedule={0: 0, 10: 1, 35: 2}),
            "ext +0x604 is the DSF return (instead of +0x608)": mut(Ret604, schedule={0: 0, 10: 1, 35: 2})}
    for k_, v in alts.items(): P("  %-62s differing samples %d" % (k_, v))
    J["alt"] = alts
    check(all(v > 0 for v in alts.values()), "every alternative mutant fails against the emulation")

    # ===================================================================================================== E4 buffer fill
    P("\n== E4 who fills +0x608: real AudioDeviceInputUnit (ctor 0x1ade60, prepareToPlay 0x1ad070, processBlock 0x1ad590) and the "
      "real JUCE copyFrom 0x577d5c used by MultiTrackUnit::processBlock")
    R4 = Rig(); e4 = R4.e
    din = e4.malloc(0x568, "AudioDeviceInputUnit"); e4.wr(din, b"\0" * 0x568)
    e4.call(0x1ade60, din, f2u(1.0))                       # +0x84 input gain: runtime config value in the device; 1.0 here
    dsr = emu.d2u(44100.0)
    e4.w32(din + 0x2c, 6); e4.w32(din + 0x30, 8)
    e4.call(0x1ad070, din, 0, dsr & 0xffffffff, dsr >> 32, stack_args=(N,))
    dbuf = h9.AudioBuf(e4, 8); dmidi = e4.malloc(0x10, "midi"); e4.wr(dmidi, b"\0" * 0x10)
    rng4 = random.Random(4)
    def din_block():
        xs = [[M.F(rng4.uniform(-1, 1)) for _ in range(N)] for _ in range(8)]
        for c in range(8): dbuf.write(c, xs[c])
        e4.wr(dbuf.obj + 0x94, b"\x00")
        e4.call(0x1ad590, din, dbuf.obj, dmidi)
        return xs, [dbuf.read(c) for c in range(8)]
    ok_pass = True
    for b in range(8):
        xs, ys = din_block()
        ok_pass &= bits(ys[4]) == bits(xs[2]) and bits(ys[5]) == bits(xs[3]) and bits(ys[2]) == bits(xs[2])
    e4.call(0x1ae2bc, din, 1)                              # what DaveSmithManager state 6 does before re-routing (0xc6e2c)
    xs, ys = din_block(); xs2, ys2 = din_block()
    fade_end = next((k_ for k_ in range(N) if ys[4][k_] == 0.0 and xs[2][k_] != 0.0), -1)
    muted = not any(ys2[4]) and not any(ys2[5]) and not any(ys2[2]) and bits(ys2[6]) == bits(xs2[2])
    e4.call(0x1ae2bc, din, 0)
    for b in range(3): xs3, ys3 = din_block()
    unmuted = bits(ys3[4]) == bits(xs3[2])
    P("  out ch4/5 (-> MTU in4/5 -> MTU+0x198 -> TrackUnit +0x608) == device input ch2/3 for 8 noise blocks: %s; device input ch4/5 "
      "(resample player) does not reach out ch4/5" % ok_pass)
    P("  0x1ae2bc(1): out ch2/3 and ch4/5 fade to 0 (first zero at sample %d of the block), next block silent %s, ch6/7 keep the raw "
      "input; 0x1ae2bc(0): restored %s" % (fade_end, muted, unmuted))
    srcb = h9.AudioBuf(e4, 6); dstb = h9.AudioBuf(e4, 2)
    xs = [[M.F(rng4.uniform(-1, 1)) for _ in range(N)] for _ in range(6)]
    for c in range(6): srcb.write(c, xs[c])
    e4.call(0x577d5c, dstb.obj, 0, 0, srcb.obj, stack_args=(4, 0, N)); e4.call(0x577d5c, dstb.obj, 1, 0, srcb.obj, stack_args=(5, 0, N))
    cf_ok = bits(dstb.read(0)) == bits(xs[4]) and bits(dstb.read(1)) == bits(xs[5])
    P("  copyFrom 0x577d5c(dst, dstCh, dstStart, src, [srcCh, srcStart, n]) with the MTU's +0x198 arguments (src ch 4/5): "
      "dst ch0/1 = src ch4/5: %s" % cf_ok)
    J["e4"] = {"pass": ok_pass, "fade_end": fade_end, "muted": muted, "unmuted": unmuted, "copyFrom": cf_ok}
    check(ok_pass and muted and unmuted and cf_ok and 0 < fade_end < N,
          "+0x608 is filled in the same callback, before the tracks run, from MultiTrackUnit input ch4/5 = AudioDeviceInputUnit out ch4/5 "
          "= device input ch2/3 after the two return mutes (+0x98, +0xa4); DaveSmithManager's 0x1ae2bc(1/0) mutes / unmutes that "
          "return (and out ch2/3) with a short fade while it switches")

    # ===================================================================================================== E2b settings
    P("\n== E2b non-unity track settings through a mode cycle (fader 80, pan -20, send 64; mid-run fader/pan/send events)")
    R5 = Rig(); t5 = R5.track(name="set", n_inserts=1, insert_fx=[h9.fx_shape]); t5.set(fader=80, pan=-20, send=64)
    m5 = M.RoutedTrack(fader=80, pan=-20, send=64); rng5 = random.Random(55); d5 = 0
    sched = {0: 1, 25: 2, 50: 0, 60: 2}
    for b in range(90):
        if b in sched: R5.set_mode(t5, sched[b]); m5.set_mode(sched[b])
        if b == 30: t5.set(fader=127, offset=17); m5.set(fader=127, offset=17)
        if b == 65: t5.set(pan=40, send=127, offset=50); m5.set(pan=40, send=127, offset=50)
        src = sigs("noise", b, rng5); e604 = sigs("sine", b, rng5); e608 = sigs("noise", b, rng5)
        o = R5.block(t5, src, e604, e608); m = m5.process(src[0], src[1], e604, e608, inserts=[h9.fx_shape])
        d5 += sum(bits(o[c]) != bits(m[c]) for c in range(6))
        for c in range(6): f32.setdefault("e2b_settings", []).extend(o[c])
    P("  90 blocks: channel-blocks differing %d" % d5)
    J["e2b"] = d5
    check(d5 == 0, "modes combine bit-exactly with fader/pan/send laws and their offset ramps (H009 stages unchanged after the selectors)")

    # ===================================================================================================== outputs
    P("\nJUCE base calls stubbed: %d (AudioProcessor ctor / setPlayConfigDetails only)" % (len(R.juce)))
    P("real-code entry counts: %s" % dict(sorted(COUNTS.items())))
    J["counts"] = COUNTS
    P("RESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h052_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h052.json"), "w"), indent=1, sort_keys=True, default=str)
    for k_, v in f32.items():
        open(os.path.join(a.out, k_ + ".f32"), "wb").write(struct.pack("<%df" % len(v), *v))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
