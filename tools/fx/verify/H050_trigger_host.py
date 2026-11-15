#!/usr/bin/env python3
"""H050 — Ducker trigger table host rule (1.60): table shape, row <-> track, and where the table is written / read / cleared within one
audio callback. Own code; reads target/EP085_Main_R_fw160 (sha256 asserted) and runs single functions in unicorn.

Sections (criteria of kb/cycles/039.md):
  C1  table shape: instruction assertions on the creation site 0x1bcf70..0x1bcf94, ctor 0x130d54, set/get/get/clear 0x1310c4 /
      0x1310dc / 0x1310e8 / 0x1310f4, eraser slot 5 0x130cac; caller census; emulation of the REAL ctor (count 16, heap pre-filled
      with 0xA5) + set/get rows 0..15, 16, 40 + REAL eraser.
  C2  row <-> track: HTAS config (0x571404..0x5714b4 -> 0x1c2cac -> 0x1b8198 memcpy to sys+0x204), buildMultiTrackUnit loop 0x1bc7c8,
      constructTrack 0x1bacec insert loop and InsertFxProcessor ctor 0x118b0c / FxProcessorBase ctor 0x1128cc; census of every
      InsertFxProcessor creation and of stores to +0x98/+0xa0 in the processor's own methods; REAL Insert ctor emulated for t = 0, 7, 15.
  C3  callback order: HTAS processBlock graph calls, JUCE 3.1.1 AudioProcessorGraph::processBlock 0x5f91fc (sequential ops), the
      render-order builder 0x5fe3a4 (insertion by isAnInputTo), canConnect 0x5fae80 MIDI rules, every pre/post-chain append, the MIDI and
      audio connections pre -> ... -> multiTrackUnit -> ... -> post, chain processBlock 0x1b8aec, MultiTrackUnit -> parallel manager
      0x1539c0 (join). Own re-implementation of the JUCE insertion order applied to the extracted edges for random node orders.
  C4  consequence + rig: several REAL Duckers (real processBlock 0x116860) sharing one table built by the REAL ctor (16 rows), triggers
      sent through the REAL manager slot 2 to both insert managers of a track, REAL eraser once per callback after all processors;
      model harness/models/ducker.py fed by the host rule "row(SOURCE) = last FULL/HALF event of that track in this callback, else 0";
      alternatives: shuffled processor order (worker threads), dispatch after the inserts, erase before the inserts, no erase.
      Re-runs H049 E3 cases with H041 ProcRig switched to ROWS = 16 + REAL ctor.
Outputs only to --out (default harness/out/H050/). Run: .venv/bin/python -B harness/H050_trigger_host.py --out DIR
"""
import argparse, hashlib, json, os, random, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, d2u, SP, PC, LR, SENTINEL                 # noqa: E402
import sp16img                                                 # noqa: E402
from sp16img import annotate, const_sites                      # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H041_ducker_model as H41                                # noqa: E402

N = 64
TT_CTOR, TT_SET, TT_FLAG, TT_OFF, TT_CLEAR = 0x130d54, 0x1310c4, 0x1310dc, 0x1310e8, 0x1310f4
ERASER_CTOR, ERASER_S5, ERASER_VT = 0x130d24, 0x130cac, 0x844bf8
IFP_CTOR, IFP_VT, FPB_CTOR = 0x118b0c, 0x842c10, 0x1128cc
PROC_BLOCK, MGR_SLOT2 = H41.PROC_BLOCK, H41.MGR_SLOT2
LOG = []; FAILS = []


def P(s=""):
    LOG.append(s); print(s, flush=True)


def check(ok, msg):
    P(("PASS  " if ok else "FAIL  ") + msg)
    if not ok: FAILS.append(msg)


def sha(b): return hashlib.sha256(b).hexdigest()


def ins(im, a):
    i = next(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a), None)
    return None if i is None else "%s %s" % (i.mnemonic, i.op_str)


def assert_sites(im, sites, what):
    bad = {hex(a): (ins(im, a), v) for a, v in sites.items() if ins(im, a) != v}
    check(not bad, "%s: %d instruction assertions%s" % (what, len(sites), "" if not bad else " MISMATCH %s" % bad))


def callers(im, t):
    return sorted(s for s, tg, k in im.direct_calls() if tg == t)


# ======================================================================================================================== C1
def c1(im, J):
    P("\n== C1 table shape (static + REAL ctor / accessors / eraser emulated)")
    assert_sites(im, {
        0x1bcf70: "mov r0, #0xc", 0x1bcf74: "bl #0x102e8", 0x1bcf78: "mov r1, #0x10", 0x1bcf80: "bl #0x130d54",
        0x1bcf94: "str r4, [r7, #0x57c]", 0x1c2dc0: "str sl, [r4, #0x57c]",
        0x130d58: "lsl r5, r1, #2", 0x130d60: "str r1, [r0, #8]", 0x130d68: "bl #0x109fc", 0x130d6c: "str r0, [r4]",
        0x130d74: "bl #0x109fc", 0x130d80: "str r0, [r4, #4]", 0x130d98: "str r1, [r5, r3]", 0x130da0: "str r1, [r0, r3]",
        0x1310c4: "ldr ip, [r0]", 0x1310c8: "ldr r3, [r0, #4]", 0x1310cc: "mov r0, #1", 0x1310d0: "str r0, [ip, r1, lsl #2]",
        0x1310d4: "str r2, [r3, r1, lsl #2]", 0x1310d8: "bx lr",
        0x1310dc: "ldr r3, [r0]", 0x1310e0: "ldr r0, [r3, r1, lsl #2]", 0x1310e8: "ldr r3, [r0, #4]", 0x1310ec: "ldr r0, [r3, r1, lsl #2]",
        0x1310f4: "ldr r3, [r0, #8]", 0x131118: "str r1, [r5, r3]", 0x131120: "str r1, [r4, r3]", 0x131128: "ldr ip, [r0, #8]",
        0x130cac: "ldr r0, [r0, #0x80]", 0x130cb0: "b #0x1310f4",
        0x130d3c: "str r5, [r4, #0x80]", 0x1bcfb0: "mov r0, #0x88", 0x1bcfb8: "mov r1, r4", 0x1bcfc0: "bl #0x130d24",
        0x1bcfd4: "str r5, [r7, #0x580]"}, "table ctor / accessors / eraser / creation site")
    plt = im.plt()
    check(plt.get(0x109fc) == "_Znaj" and plt.get(0x102e8) == "_Znwj", "0x109fc = operator new[] (%s), 0x102e8 = operator new (%s)"
          % (plt.get(0x109fc), plt.get(0x102e8)))
    cen = {hex(t): [hex(s) for s in callers(im, t)] for t in (TT_CTOR, TT_SET, TT_FLAG, TT_OFF, TT_CLEAR, ERASER_S5, ERASER_CTOR)}
    ptr = {hex(t): len(const_sites(im, [t])[t]) for t in (TT_CTOR, TT_SET, TT_FLAG, TT_OFF, TT_CLEAR, ERASER_CTOR)}
    P("  direct callers: %s; pointer words: %s" % (cen, ptr))
    J["c1_callers"] = cen
    check(cen == {"0x130d54": ["0x1bcf80"], "0x1310c4": ["0x11685c"], "0x1310dc": ["0x116a04"], "0x1310e8": ["0x116a40"],
                  "0x1310f4": ["0x130cb0"], "0x130cac": [], "0x130d24": ["0x1bcfc0"]} and not any(ptr.values()),
          "one table (ctor only @0x1bcf80, count 16), set only from slot 54 @0x11685c, gets only from processBlock, clear only from eraser "
          "slot 5 (vtable word 0x844bf8+0x14 = 0x%x), one eraser (ctor @0x1bcfc0)" % im.u32(ERASER_VT + 0x14))
    # --- emulation -----------------------------------------------------------------------------------------------------
    e = emu.Emu(heap_fill=0xA5)
    t = e.malloc(12, "harness: table object"); n0 = len(e.allocs)
    r0, _ = e.call(TT_CTOR, t, 16)
    arrs = [(a, n, k) for a, n, k in e.allocs[n0:]]
    fl, of, cnt = e.u32(t), e.u32(t + 4), e.u32(t + 8)
    zero = e.rd(fl, 64) == b"\0" * 64 and e.rd(of, 64) == b"\0" * 64
    P("  ctor(t, 16): returns this %s; count +8 = %d; new[] calls %s; flag array 0x%x, offset array 0x%x; both zeroed: %s" % (
        r0 == t, cnt, [(hex(a), n, k) for a, n, k in arrs], fl, of, zero))
    check(r0 == t and cnt == 16 and [n for _, n, _ in arrs] == [64, 64] and (fl, of) == (arrs[0][0], arrs[1][0]) and zero,
          "layout {int *flag (+0), int *offset (+4), int count (+8)}: two new int[16] (64 bytes each), zero-filled by the ctor")
    for r in range(16): e.call(TT_SET, t, r, 100 + r)
    got = [(e.call(TT_FLAG, t, r)[0], e.call(TT_OFF, t, r)[0]) for r in range(16)]
    check(got == [(1, 100 + r) for r in range(16)], "set(row, off) -> flag[row] = 1, offset[row] = off; get flag/offset read them back (rows 0..15)")
    after_off = e.rd(of + 64, 16)
    g16 = (e.call(TT_FLAG, t, 16)[0], e.call(TT_OFF, t, 16)[0]); g40 = (e.call(TT_FLAG, t, 40)[0], e.call(TT_OFF, t, 40)[0])
    P("  in this emulator the arrays are adjacent (offset array = flag array + 64): %s" % (of == fl + 64))
    P("  get(row 16) = (0x%x, 0x%x) = (offset[0], word after offset array); get(row 40) = (0x%x, 0x%x)" % (g16 + g40))
    check(g16 == (100, struct.unpack("<I", after_off[:4])[0]) and g40[0] == e.u32(fl + 160) and g40[1] == e.u32(of + 160),
          "no bounds check: row >= 16 reads the word 4*row past each array start (here row 16 flag = offset[0] = 100; "
          "offset = heap fill 0x%x); on the device the value depends on the heap layout" % g16[1])
    er = e.malloc(0x88, "harness: eraser"); e.w32(er + 0x80, t)
    e.call(ERASER_S5, er)
    cleared = e.rd(fl, 64) == b"\0" * 64 and e.rd(of, 64) == b"\0" * 64
    check(cleared and e.rd(of + 64, 16) == after_off and e.u32(t + 8) == 16,
          "REAL eraser slot 5 (+0x80 = table) zeroes exactly flag[0..15] and offset[0..15]; memory after the arrays untouched")
    J["c1"] = {"count": cnt, "new[]": [n for _, n, _ in arrs], "get16": g16, "get40": g40}


# ======================================================================================================================== C2
def c2(im, J):
    P("\n== C2 row <-> track (static provenance + REAL Insert ctor emulated)")
    assert_sites(im, {
        # LiveSamplerApplication: HTAS config on the stack, passed by value (r1-r3 + 0x54 stack bytes)
        0x571404: "mov r6, #0x10", 0x571408: "mov r1, #2", 0x571448: "str r1, [sp, #0x80]", 0x571480: "str r6, [sp, #0x64]",
        0x57148c: "add r1, sp, #0x64", 0x571490: "mov r2, #0x54", 0x5714a4: "bl #0x1078c", 0x5714a8: "add r3, sp, #0x58",
        0x5714b0: "ldm r3, {r1, r2, r3}", 0x5714b4: "bl #0x1c2cac",
        0x1c2cc8: "stm r5, {r1, r2, r3}", 0x1c2ccc: "add r1, sp, #0x88", 0x1c2cd0: "mov r2, #0x54", 0x1c2ce4: "bl #0x1b8198",
        0x1b81b0: "stm r5, {r1, r2, r3}", 0x1b81c4: "mov r2, #0x60", 0x1b81c8: "add r0, r4, #0x204", 0x1b81e0: "bl #0x1078c",
        # buildMultiTrackUnit: for t in 0 .. sys+0x210-1: constructTrack(sys, t)
        0x1bc7ec: "ldr r3, [r4, #0x210]", 0x1bc7f8: "mov r6, #0", 0x1bc804: "mov r1, r6", 0x1bc808: "bl #0x1bacec",
        0x1bc87c: "add r6, r6, #1", 0x1bc884: "ldr r3, [r4, #0x210]", 0x1bc888: "cmp r3, r6", 0x1bc88c: "bgt #0x1bc800",
        0x1bda3c: "bl #0x1bc7c8",
        # constructTrack: track index kept at [sp,#0x1c]; insert loop slot r6 = 0 .. TrackUnit+0xb8 - 1
        0x1bad04: "str r1, [sp, #0x1c]", 0x1bacf8: "ldr r5, [r0, #0x22c]", 0x1ccef4: "ldr ip, [r5]", 0x1ccf2c: "str ip, [r4, #0xb8]",
        0x1c7880: "ldr r0, [r0, #0xb8]", 0x1bbd18: "ldr r3, [r3, #0xd4]", 0x1bbd24: "str r0, [sp, #0x30]", 0x1bbd40: "mov r6, #0",
        0x1bbd54: "ldr sb, [r4, #0x578]", 0x1bbd5c: "ldr r5, [r4, #0x57c]", 0x1bbd70: "ldr r1, [sp, #0x1c]", 0x1bbd74: "mov r2, sb",
        0x1bbd78: "mov r3, r5", 0x1bbd80: "bl #0x118b0c", 0x1bbd8c: "mov r1, r6", 0x1bbf40: "mov r1, r6", 0x1bbf44: "bl #0x1c9874",
        0x1bc0e0: "add r6, r6, #1", 0x1bc0e4: "cmp sl, r6", 0x1bc0e8: "bne #0x1bbd4c",
        # InsertFxProcessor ctor: +0xa0 = arg1; base ctor (arg2, arg3) -> +0x94, +0x98
        0x118b14: "mov r5, r1", 0x118b18: "mov r1, r2", 0x118b1c: "mov r2, r3", 0x118b24: "bl #0x1128cc", 0x118b40: "str r5, [r4, #0xa0]",
        0x112908: "str r5, [r4, #0x94]", 0x11290c: "str r6, [r4, #0x98]",
        # readers
        0x116854: "ldr r0, [r0, #0x98]", 0x116858: "ldr r1, [r3, #0xa0]", 0x1169f4: "ldr r0, [r4, #0x98]"}, "config / track loop / insert loop / ctor")
    # [sp,#0x1c] has exactly one writer in constructTrack; nothing else writes sp+0x1c (stm sp only covers sp+0/+4)
    L = annotate(im, 0x1bacec, 0x1bc7c8)
    w1c = [l for l in L if re.search(r"^0x[0-9a-f]+: str\w* \w+, \[sp, #0x1c\]", l)]
    multi = [l for l in L if re.search(r": (strd|stm\w*|push|sub sp|add sp)", l) and "sp" in l.split(": ", 1)[1]]
    P("  writes of [sp,#0x1c] in constructTrack: %s; multi-register / sp-adjusting writes: %s" % (w1c, multi))
    check(len(w1c) == 1 and w1c[0].startswith("0x1bad04") and
          [l.split(": ", 1)[1] for l in multi] == ["sub sp, sp, #0x4c", "stm sp, {r6, r7}", "stm sp, {sb, fp}", "add sp, sp, #0x4c"],
          "InsertFxProcessor ctor arg 1 = constructTrack's own int argument t (single writer @0x1bad04)")
    # word stores of +0x210 / +0x22c / +0x57c in HTAS code: only the ctor zero-fill and the creation site
    lo, hi = im.sec[".text"]; o = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o); st = {0x210: [], 0x22c: [], 0x57c: []}
    for k, w in enumerate(W):
        if (w >> 28) != 0xf and (w & 0x0ff00000) == 0x05800000 and (w & 0xfff) in st:
            a = lo + 4 * k; f = im.func_of(a)[0]
            if 0x1b5000 <= f < 0x1c3000: st[w & 0xfff].append(hex(a))
    P("  word stores [rX,#imm] inside AudioSystemBase/HTAS code 0x1b5000..0x1c3000: %s" % st)
    check(st == {0x210: [], 0x22c: [], 0x57c: ["0x1bcf94", "0x1c2dc0"]},
          "sys+0x210 (tracks = 16) and sys+0x22c (inserts per track = 2) come only from the config memcpy; sys+0x57c only ctor 0 / table")
    # creation order inside slot 55: no branch enters (0x1bcf80, 0x1bda3c] from before 0x1bcf80
    s55, e55 = 0x1bc8d4, 0x1c10f4; jumps = []
    BR = {"b"} | {"b" + c for c in ("eq", "ne", "hs", "lo", "cs", "cc", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le")}
    nins = 0
    for i in im.disasm(s55, e55):
        nins += 1
        if i.mnemonic in BR and i.op_str.startswith("#"):
            tg = int(i.op_str[1:], 16)
            if i.address < 0x1bcf80 and 0x1bcf80 < tg <= 0x1bda3c: jumps.append((hex(i.address), hex(tg)))
    P("  slot 55: %d instructions decoded (0x%x..0x%x)" % (nins, s55, e55))
    check(not jumps, "slot 55: the table is created (@0x1bcf80) on every path before the tracks are built (@0x1bda3c); "
          "branches skipping it: %s" % jumps)
    # every InsertFxProcessor creation
    cen = {hex(t): [hex(s) for s in callers(im, t)] for t in (IFP_CTOR, 0x1bacec, 0x1bc7c8)}
    vtw = [(k, hex(b)) for k, b in const_sites(im, [IFP_VT])[IFP_VT]]
    ptr = {hex(t): len(const_sites(im, [t])[t]) for t in (IFP_CTOR, 0x1bacec, 0x1bc7c8)}
    P("  callers %s; pointer words %s; vptr 0x842c10 materialised at %s" % (cen, ptr, vtw))
    J["c2_census"] = {"callers": cen, "vt_sites": vtw}
    check(cen == {"0x118b0c": ["0x1bbd80"], "0x1bacec": ["0x1bc808"], "0x1bc7c8": ["0x1bda3c"]} and not any(ptr.values()),
          "InsertFxProcessor is built only in constructTrack's insert loop (1 site), constructTrack only by buildMultiTrackUnit, "
          "which slot 55 calls once")
    # stores to +0x98 / +0xa0 in the InsertFxProcessor / FxProcessorBase methods (all words of both vtables)
    meth = set()
    for vt in (IFP_VT, 0x842790):
        for k in range(120):
            f = im.u32(vt + 4 * k)
            if f is not None and im.sec[".plt"][0] <= f < im.sec[".plt"][1]: continue      # e.g. __cxa_pure_virtual
            if f is None or not (im.sec[".text"][0] <= f < im.sec[".text"][1]): break
            meth.add(f)
    hits = []
    import bisect
    starts = sorted(set(im.starts()) | {t for _, t, k in im.direct_calls() if k == "bl"} | meth)   # extent = next known entry
    for f in sorted(meth):
        e_ = starts[bisect.bisect_right(starts, f)]
        for i in im.disasm(f, e_):
            if i.mnemonic in ("str", "strd") and re.search(r"#0x(98|a0)\]", i.op_str): hits.append((hex(f), hex(i.address), i.op_str))
    P("  %d method entries scanned; stores to [rX,#0x98]/[rX,#0xa0]: %s" % (len(meth), hits))
    J["c2_method_stores"] = hits
    check(not hits, "no InsertFxProcessor/FxProcessorBase method stores +0x98 or +0xa0 (they keep the ctor values)")
    # REAL Insert ctor
    import H077_master_send_proc as H77
    res = {}
    for tr in (0, 7, 15):
        e = H31.new_emu()
        for f in H77.STATIC_INIT: e.call(f)
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(H77.FRAC_INIT[0], H77.FRAC_INIT[1])
        e.add_watch(H77.JUCE_SETPLAY, lambda em: em.uc.reg_write(PC, em.uc.reg_read(LR)))
        tob = e.malloc(8); tbl = e.malloc(12); e.call(TT_CTOR, tbl, 16)
        p = e.malloc(0x148)
        e.call(IFP_CTOR, p, tr, tob, tbl)
        res[tr] = (e.u32(p) == IFP_VT, e.u32(p + 0xa0), e.u32(p + 0x94) == tob, e.u32(p + 0x98) == tbl)
    P("  REAL ctor 0x118b0c(p, t, tempo, table): (vptr ok, +0xa0, +0x94 = tempo, +0x98 = table) = %s" % res)
    J["c2_ctor"] = res
    check(all(v == (True, t_, True, True) for t_, v in res.items()), "+0xa0 = t and +0x98 = the shared table for t = 0, 7, 15")
    table = {"track %d, FX%d" % (t_ + 1, s_ + 1): {"+0xa0": t_, "+0x98": "sys+0x57c (one table)"} for t_ in range(16) for s_ in range(2)}
    J["c2_table"] = table
    P("  => track t (0-based), FX1 and FX2: +0xa0 = t, +0x98 = sys+0x57c, for t = 0..15 (32 processors; no other Insert processor)")


# ======================================================================================================================== C3
EDGES = [  # (src, dst, kind, site)
    ("midiIn", "pre", "midi", 0x1b6bd8), ("pre", "resamplePlayer", "midi", 0x1b6c34), ("resamplePlayer", "deviceInput", "midi", 0x1b6c90),
    ("deviceOutput", "resampleRecorder", "midi", 0x1b6cec), ("resampleRecorder", "post", "midi", 0x1b6d48), ("post", "midiOut", "midi", 0x1b6da4),
    ("deviceInput", "liveSampling", "midi", 0x1bf530), ("liveSampling", "multiTrackUnit", "midi", 0x1bf544),
    ("masterOut", "deviceOutput", "midi", 0x1bf55c),
    ("multiTrackUnit", "compositeFx", "audio 0x1bea5c-style pair", 0x1be3ec), ("multiTrackUnit", "compositeFx", "audio", 0x1be448),
    ("compositeFx", "masterOut", "audio (0,1)->(0,1)", 0x1be9a0), ("compositeFx", "masterOut", "audio", 0x1bea04),
    ("multiTrackUnit", "masterOut", "audio (14,15)->(4,5)", 0x1bea5c),
]
NODES = ["audioIn", "audioOut", "midiIn", "midiOut", "pre", "resamplePlayer", "resampleRecorder", "post", "deviceOutput", "deviceInput",
         "multiTrackUnit", "liveSampling", "compositeFx", "masterOut", "headphone", "masterAssignable", "dsfDriveMaster", "dsfDriveSend"]


def juce_order(nodes, edges):
    """Own re-implementation of JUCE 3.1.1 AudioProcessorGraph::buildRenderingSequence node ordering (as read at 0x5fe40c..0x5fe604):
    each node is inserted before the first already-ordered node it is (transitively, depth-limited) an input to."""
    src = {}
    for a, b in edges: src.setdefault(b, set()).add(a)
    limit = len(src) - 1

    def is_input(a, b, rc):
        s = src.get(b)
        if s is None: return False
        if a in s: return True
        if rc - 1 >= 0:
            return any(is_input(a, x, rc - 1) for x in sorted(s))
        return False
    order = []
    for nd in nodes:
        j = 0
        while j < len(order) and not is_input(nd, order[j], limit): j += 1
        order.insert(j, nd)
    return order


def c3(im, J):
    P("\n== C3 callback order (static)")
    assert_sites(im, {
        # HTAS processBlock -> graph processBlock (each path once, then return)
        0x1c140c: "bl #0x5f91fc", 0x1c1418: "add sp, sp, #0xc", 0x1c15f0: "b #0x5f91fc", 0x1c1870: "bl #0x5f91fc", 0x1c18a4: "b #0x1c1418",
        0x1c18ec: "bl #0x5f91fc", 0x1c1908: "b #0x1c1418", 0x1c1950: "bl #0x5f91fc",
        # graph processBlock: ops[i]->perform in array order (graph+0x148 data, +0x150 count)
        0x5f9274: "ldr r0, [r5, #0x148]", 0x5f9284: "ldr r0, [r0, r4, lsl #2]", 0x5f9288: "add r4, r4, #1", 0x5f9290: "ldr ip, [ip, #8]",
        0x5f9294: "blx ip", 0x5f9298: "ldr r3, [r5, #0x150]", 0x5f92a0: "bgt #0x5f9274",
        # order builder 0x5fe3a4: nodes graph+0x88 / +0x90, lookup table from connections graph+0x94, insertion by isAnInputTo
        0x5fe3dc: "add r1, r4, #0x94", 0x5fe3e8: "bl #0x6075a4", 0x5fe3ec: "ldr r3, [r4, #0x90]", 0x5fe40c: "ldr r3, [r5, #0x88]",
        0x5fe410: "ldr r3, [r3, r4, lsl #2]", 0x5fe4dc: "sub sl, ip, #1", 0x5fe4e8: "ldr r2, [fp, r8, lsl #2]", 0x5fe508: "beq #0x5fed0c",
        0x5fe580: "add r8, r8, #1", 0x5fe5d0: "bl #0x10798", 0x5fe5e4: "strne r4, [fp]", 0x5fe5f8: "add r4, r4, #1",
        0x5fed0c: "ldr r7, [r2, #0xc]", 0x5fed28: "cmp r0, r4", 0x5fed94: "bl #0x602ba0", 0x5feca8: "str r4, [r5, #0x148]",
        # canConnect: MIDI source needs vt+0x38 (producesMidi), MIDI destination vt+0x34 (acceptsMidi); audio: ch < +0x30 / +0x2c
        0x5faef0: "cmp r5, #0x1000", 0x5faefc: "ldr r3, [r0, #0x30]", 0x5faf34: "ldr r3, [r0, #0x2c]", 0x5faf70: "ldr r3, [r3, #0x34]",
        0x5faf88: "ldr r3, [r3, #0x38]",
        # pre / post chains = graph nodes
        0x1b6448: "bl #0x102e8", 0x1b6454: "bl #0x1b8a00", 0x1b6460: "str r5, [r4, #0x3ac]", 0x1b6490: "mov r1, r5",
        0x1b6498: "bl #0x5fdfec", 0x1b64cc: "str r5, [r4, #0x3c4]", 0x1b6600: "bl #0x1b8a00", 0x1b6610: "str r5, [r4, #0x3b0]",
        0x1b6748: "str r5, [r4, #0x3c8]", 0x1bda70: "str r0, [r7, #0x74c]", 0x1bdc10: "str r0, [sp, #0x40]",
        0x1bded8: "str r0, [sp, #0x38]", 0x1be934: "str r0, [sp, #0x24]",
        0x1bd950: "ldr r0, [r7, #0x3ac]", 0x1bd958: "ldr r1, [r7, #0x598]", 0x1bd95c: "bl #0x1b8c54",
        0x1bd970: "ldr r0, [r7, #0x3b0]", 0x1bd978: "ldr r1, [r7, #0x580]", 0x1bd97c: "bl #0x1b8c54",
        # chain processBlock: members in vector order, each vt+0x14 (processBlock), synchronous
        0x1b8b14: "ldr r3, [r5, #0x80]", 0x1b8b34: "ldr r0, [r3, r4, lsl #2]", 0x1b8b4c: "ldr r3, [r3, #0x14]", 0x1b8b50: "blx r3",
        0x1b8b58: "cmp r4, r6",
        # MIDI connections (srcNode+8 = id, dstNode+8)
        0x1b6be4: "ldr r2, [r4, #0x3c4]", 0x1b6be8: "ldr r3, [r4, #0x3d0]", 0x1b6c34: "bl #0x5ff2c4",
        0x1b6c40: "ldr r2, [r4, #0x3d0]", 0x1b6c44: "ldr r3, [r4, #0x3bc]", 0x1b6c90: "bl #0x5ff2c4",
        0x1b6c9c: "ldr r2, [r4, #0x3c0]", 0x1b6ca0: "ldr r3, [r4, #0x3cc]", 0x1b6cec: "bl #0x5ff2c4",
        0x1b6cf8: "ldr r2, [r4, #0x3cc]", 0x1b6cfc: "ldr r3, [r4, #0x3c8]", 0x1b6d48: "bl #0x5ff2c4",
        0x1bf51c: "ldr r3, [r7, #0x3bc]", 0x1bf524: "ldr r5, [sp, #0x40]", 0x1bf528: "ldr r1, [r3, #8]", 0x1bf52c: "ldr r2, [r5, #8]",
        0x1bf530: "bl #0x1b7380", 0x1bf534: "ldr r3, [r7, #0x74c]", 0x1bf53c: "ldr r1, [r5, #8]", 0x1bf540: "ldr r2, [r3, #8]",
        0x1bf544: "bl #0x1b7380", 0x1bf548: "ldr r3, [r7, #0x3c0]", 0x1bf550: "ldr r5, [sp, #0x24]", 0x1bf554: "ldr r2, [r3, #8]",
        0x1bf558: "ldr r1, [r5, #8]", 0x1bf55c: "bl #0x1b7380",
        # audio: MTU -> compositeFx, compositeFx -> masterOut, MTU (14,15) -> masterOut (4,5)
        0x1be394: "ldr r2, [r7, #0x74c]", 0x1be3ac: "ldr ip, [sp, #0x38]", 0x1be3ec: "bl #0x1b61bc",
        0x1be944: "ldr r5, [sp, #0x38]", 0x1be960: "ldr ip, [sp, #0x24]", 0x1be9a0: "bl #0x1b61bc",
        0x1bea0c: "ldr r2, [r7, #0x74c]", 0x1bea24: "ldr r1, [sp, #0x24]", 0x1bea5c: "bl #0x1b61bc",
        0x1b7380: "ldr r3, [pc, #0x74]", 0x1b73bc: "bl #0x5fae80", 0x1b73dc: "bl #0x5ff2c4",
        # MultiTrackUnit: parallel manager = sys+0x5cc (setter 0x1c4408), run + join (slot 5 0x1539c0)
        0x1bda44: "ldr r1, [r7, #0x5cc]", 0x1bda48: "bl #0x1c4408", 0x1c4408: "str r1, [r0, #0x98]",
        0x1c52d4: "ldr r3, [r3, #0x10]", 0x1c537c: "ldr r3, [r3, #0x14]", 0x1c5380: "blx r3", 0x1c5570: "ldr r3, [r3, #0x14]",
        0x153a30: "bl #0x153980", 0x153a64: "bl #0x116bc", 0x153a68: "ldr r3, [r4, #0x20]", 0x153a6c: "cmp r6, r3",
        0x153a70: "bgt #0x153a5c"}, "graph / order builder / canConnect / chains / connections / MTU join")
    check(im.u32(0xaa4c20) == 0x1000 and im.u32(0x849190 + 0x14) == 0x1539c0 and im.u32(0x85e4dc + 0x14) == 0x191218
          and im.u32(ERASER_VT + 0x14) == ERASER_S5 and im.plt().get(0x116bc) == "nanosleep",
          "MIDI channel index word 0xaa4c20 = 0x1000; manager vt+0x14 = 0x1539c0; Sequencer vt+0x14 = processBlock 0x191218; "
          "TriggerEraser vt+0x14 = 0x130cac")
    # every chain append
    app = []
    for s in callers(im, 0x1b8c54):
        L = [x.split(": ", 1)[1] for x in annotate(im, s - 16, s + 4)]
        ch = [re.search(r"#(0x3ac|0x3b0)\]", x) for x in L]; mem = [re.search(r"ldr r1, \[r7, #(0x[0-9a-f]+)\]", x) for x in L]
        app.append((hex(s), next((c.group(1) for c in ch if c), "?"), next((m.group(1) for m in mem if m), "?")))
    P("  chain appends (site, chain, member sys+off): %s" % app)
    post = [x for x in app if x[1] == "0x3b0"]; pre_seq = [x for x in app if x[1] == "0x3ac" and x[2] == "0x598"]
    check(len(post) == 2 and post[0][2] == "0x580" and len(pre_seq) == 1,
          "Sequencer (sys+0x598) is in the pre chain only; TriggerEraser (sys+0x580) is the first member of the post chain")
    # vtable checks: every node processor on the path accepts and produces MIDI
    cls = {"chain 0x8639b8": 0x8639b8, "resample 0x861fc8": 0x861fc8, "deviceInput 0x8620e8": 0x8620e8,
           "liveSampling 0x8465ec": 0x8465ec, "multiTrackUnit 0x864570": 0x864570, "masterOut 0x862a58": 0x862a58,
           "deviceOutput 0x8621f8": 0x8621f8}
    mid = {k: (hex(im.u32(v + 0x34)), hex(im.u32(v + 0x38))) for k, v in cls.items()}
    P("  (acceptsMidi vt+0x34, producesMidi vt+0x38): %s; 0xc4054 = %s, 0xc405c = %s" % (mid, ins(im, 0xc4054), ins(im, 0xc405c)))
    check(all(v == ("0xc4054", "0xc405c") for v in mid.values()) and ins(im, 0xc4054) == "mov r0, #1" and ins(im, 0xc405c) == "mov r0, #1",
          "every processor on the MIDI path returns 1 for acceptsMidi and producesMidi, so canConnect accepts each MIDI connection")
    rem = {hex(f): (len(callers(im, f)), len(const_sites(im, [f])[f])) for f in (0x1b7404, 0x1b7508, 0x1b7618, 0x1b7728, 0x1b7838, 0x1b79b8,
                                                                               0x1b7b38, 0x1b7c48, 0x1b7d58, 0x1b7e68, 0x1b7f78)}
    P("  Pioneer disconnect helpers ('remove midi connection' 0x1b7404 and the per-pair removers): (callers, pointer words) %s" % rem)
    check(all(v == (0, 0) for v in rem.values()), "no Pioneer code removes graph connections after the build (all removers unreferenced)")
    # ordering model
    rnd = random.Random(39); bad = 0; bad_noaudio = 0
    E = [(a, b) for a, b, _, _ in EDGES]; E_noaudio = [(a, b) for a, b, k, _ in EDGES if k == "midi"]
    for it in range(3000):
        nodes = NODES[:]; rnd.shuffle(nodes)
        o = juce_order(nodes, E)
        bad += not (o.index("pre") < o.index("multiTrackUnit") < o.index("post"))
        o2 = juce_order(nodes, E_noaudio)
        bad_noaudio += not (o2.index("multiTrackUnit") < o2.index("post"))
    P("  own JUCE-3.1.1 ordering model on the %d extracted edges, 3000 random node-array orders: pre < multiTrackUnit < post violated "
      "%d times; with only the MIDI edges (audio edges dropped) multiTrackUnit < post violated %d times" % (len(E), bad, bad_noaudio))
    J["c3_order"] = {"violations": bad, "violations_midi_only": bad_noaudio}
    check(bad == 0 and bad_noaudio > 0, "with these connections every node order gives pre -> multiTrackUnit -> post; the MTU-before-post "
          "part rests on the audio edges MTU -> masterOut / compositeFx (without them it is not guaranteed)")


# ======================================================================================================================== C4
class MultiRig:
    """Several REAL Duckers, each inside the REAL InsertFxProcessor processBlock 0x116860 (stand-in processor fields as H041 ProcRig),
    sharing ONE trigger table built by the REAL ctor 0x130d54(t, 16); 32 insert managers (16 tracks x FX1/FX2) pointing at their
    processor (+0x98 = table, +0xa0 = track, C2); REAL manager slot 2 0x1263f4 for every event, REAL eraser 0x130cac."""

    def __init__(self, duckers, pre=((0, 0.004), (2, 0.001))):
        self.e = e = H31.new_emu()
        for a_ in (0xe8050, 0xe8228): e.add_watch(a_, lambda em: em.uc.reg_write(PC, em.uc.reg_read(LR)))
        def tempo(em):
            u = d2u(120.0); em.setr(0, u & 0xffffffff); em.setr(1, u >> 32)
        e.add_watch(H41.TEMPO_FN, tempo)
        tvt = e.malloc(64); e.w32(tvt + 0x1c, H41.TEMPO_FN); tob = e.malloc(8); e.w32(tob, tvt)
        self.table = t = e.malloc(12); e.call(TT_CTOR, t, 16)
        self.flags, self.offs = e.u32(t), e.u32(t + 4)
        self.d = []
        for tr, slot, src in duckers:
            x = H41.EmuDuck(defaults=True, e=e)
            for idx, v in pre: x.set(idx, v)
            x.set(10, float(src))
            p = e.malloc(0x148); arr = e.malloc(40)
            for k in range(10): e.w32(arr + 4 * k, x.o if k == 9 else 0)
            e.w32(p, H41.VT_PROC); e.w32(p + 0x80, arr); e.w32(p + 0x88, 10); e.w32(p + 0x94, tob); e.w32(p + 0x98, t)
            e.wr(p + 0x9d, b"\x01\x00"); e.w32(p + 0xa0, tr); e.w32(p + 0xa4, 9); e.w32(p + 0xa8, 9)
            dd = e.malloc(8); e.w32(dd, e.malloc(256)); e.w32(dd + 4, e.malloc(256)); e.w32(p + 0xb8, dd)
            buf = e.malloc(0x100); ch = e.malloc(8); Lb = e.malloc(256); Rb = e.malloc(256)
            e.w32(ch, Lb); e.w32(ch + 4, Rb); e.w32(buf + 0xc, ch)
            m = H41.Model(); m.insert_defaults()
            for idx, v in pre: m.set_param(idx, v)
            m.set_param(10, float(src))
            self.d.append(dict(track=tr, slot=slot, src=src, x=x, p=p, buf=buf, Lb=Lb, Rb=Rb, m=m, first=True, cap=None,
                               nbit=0, nsamp=0, duck=[], start={}))
        self.mgr = {}
        byts = {(d["track"], d["slot"]): d["p"] for d in self.d}
        for tr in range(16):
            for s in range(2):
                p = byts.get((tr, s))
                if p is None:
                    p = e.malloc(0x148); e.w32(p, H41.VT_PROC); e.w32(p + 0x98, t); e.w32(p + 0xa0, tr)
                mk = e.malloc(0x98); e.w32(mk + 0x1c, p); self.mgr[(tr, s)] = mk
        self.eraser = er = e.malloc(0x88); e.w32(er + 0x80, t)
        self.cur = None
        def cin(em):
            self.cur = (em.r(0), em.r(1), em.r(2), em.r(3), em.floats(em.r(1), em.r(3)), em.floats(em.r(2), em.r(3)))
        def cout(em):
            o, l_, r_, n_, iL, iR = self.cur
            self.caps[o] = (iL, iR, em.floats(l_, n_), em.floats(r_, n_))
        e.add_watch(0x106ecc, cin); e.add_watch(0x106ed0, cout)

    def dispatch(self, tr, off, ty):          # as the Sequencer dispatcher: both insert managers of the track get (offset, type)
        for s in range(2): self.e.call(MGR_SLOT2, self.mgr[(tr, s)], off, ty)

    def run_proc(self, d, L, R):
        e = self.e; e.set_floats(d["Lb"], L); e.set_floats(d["Rb"], R)
        e.call(PROC_BLOCK, d["p"], d["buf"])

    def callback(self, b, events, L, R, order="static", rnd=None):
        e = self.e; self.caps = {}
        procs = list(self.d)
        if order == "shuffled": rnd.shuffle(procs)
        if order in ("static", "shuffled", "no_erase"):
            for ev in events: self.dispatch(*ev)
            for d in procs: self.run_proc(d, L, R)
            if order != "no_erase": e.call(ERASER_S5, self.eraser)
        elif order == "dispatch_after":
            for d in procs: self.run_proc(d, L, R)
            for ev in events: self.dispatch(*ev)
            e.call(ERASER_S5, self.eraser)
        elif order == "erase_before":
            for ev in events: self.dispatch(*ev)
            e.call(ERASER_S5, self.eraser)
            for d in procs: self.run_proc(d, L, R)
        # model side: host rule from the event list, not from the table
        for d in self.d:
            last = [of for tr, of, ty in events if tr == d["src"] and ty in (11, 15)]
            row = (1, last[-1]) if last else (0, 0)
            m = d["m"]
            if d["first"]: m.reset(); m.dry, m.wet = 0.0, 1.0; d["first"] = False
            for idx, v in ((7, 120.0), (8, float(row[0])), (9, float(row[1]))): m.set_param(idx, v)
            cap = self.caps.get(d["x"].o)
            if cap is None: continue
            iL, iR, oL, oR = cap
            mL, mR = m.process(iL, iR)
            for p_, q_ in zip(mL + mR, oL + oR):
                d["nsamp"] += 1; d["nbit"] += f2u(p_) != f2u(q_)
            chg = [i for i in range(N) if oL[i] != iL[i] or oR[i] != iR[i]]
            if chg: d["duck"].append(b)
            if chg and (b - 1) not in d["duck"]: d["start"][b] = chg[0]


DUCKERS = [(3, 0, 3), (3, 1, 3), (7, 0, 3), (0, 1, 15), (15, 0, 0), (9, 1, 9)]    # (track, slot FX1=0/FX2=1, SOURCE)
SCHED = {10: [(3, 17, 15)], 20: [(3, 5, 11)], 25: [(15, 0, 15)], 30: [(0, 63, 15)], 40: [(3, 10, 15), (3, 40, 11)],
         50: [(3, 5, 8)], 60: [(0, 3, 15), (15, 60, 11)], 70: [(3, 33, 15), (3, 50, 12)], 75: [(9, 20, 15), (3, 7, 0)]}
EXPECT = {(3, 0): {10: 17, 20: 5, 40: 40, 70: 33}, (3, 1): {10: 17, 20: 5, 40: 40, 70: 33}, (7, 0): {10: 17, 20: 5, 40: 40, 70: 33},
          (0, 1): {25: 0, 60: 60}, (15, 0): {30: 63, 60: 3}, (9, 1): {75: 20}}


def run_multi(order, nblk=90, seed=0):
    rig = MultiRig(DUCKERS); rnd = random.Random(seed)
    Ls, Rs = H41.signal("noise", nblk, seed=5); out = bytearray()
    for b in range(nblk):
        rig.callback(b, SCHED.get(b, []), Ls[b * N:(b + 1) * N], Rs[b * N:(b + 1) * N], order=order, rnd=rnd)
        for d in rig.d:
            c = rig.caps.get(d["x"].o)
            if c: out += struct.pack("<%df" % (2 * N), *(c[2] + c[3]))
    return rig, bytes(out)


def c4(im, J, out):
    P("\n== C4 consequence: several REAL Duckers, one REAL 16-row table, dispatch -> all inserts -> eraser once per callback")
    P("  Duckers (track, FX slot, SOURCE), 0-based tracks: %s" % DUCKERS)
    P("  events per callback (track, offset, type) sent to both insert managers of the track: %s" % SCHED)
    rig, b_static = run_multi("static")
    res = {}
    for d in rig.d:
        k = (d["track"], d["slot"]); res[str(k)] = {"start": d["start"], "mism": d["nbit"], "samples": d["nsamp"]}
        P("  Ducker track %d FX%d SOURCE %d: duck starts (block: sample) %s, expected %s; model (host rule) vs emulation: %d of %d differ"
          % (d["track"], d["slot"] + 1, d["src"], d["start"], EXPECT[k], d["nbit"], d["nsamp"]))
    ok = all(d["start"] == EXPECT[(d["track"], d["slot"])] and d["nbit"] == 0 and d["nsamp"] == 90 * 2 * N for d in rig.d)
    check(ok, "every Ducker ducks in the callback of its SOURCE track's FULL/HALF event, at that event's offset (last event wins; "
          "types 8/12/0 ignored); FX1 and FX2 of one track share the row; the next callback sees a cleared row; 0 differing samples")
    open(os.path.join(out, "c4_static.f32"), "wb").write(b_static)
    J["c4_static"] = {"ducker": res, "sha": sha(b_static)}
    _, b_sh = run_multi("shuffled", seed=7)
    P("  shuffled processor order each callback (worker threads): outputs sha %s vs static %s" % (sha(b_sh)[:16], sha(b_static)[:16]))
    check(b_sh == b_static, "processor order within the callback does not matter (processBlock only reads the table)")
    alt = {}
    for order in ("dispatch_after", "erase_before", "no_erase"):
        r2, _ = run_multi(order)
        alt[order] = {str((d["track"], d["slot"])): (d["start"], d["nbit"]) for d in r2.d}
        n_duck = sum(len(d["duck"]) for d in r2.d); mism = sum(d["nbit"] for d in r2.d)
        P("  alternative order %-14s: ducking blocks %d, duck starts %s, model (same-callback rule) mismatches %d"
          % (order, n_duck, [d["start"] for d in r2.d], mism))
        alt[order]["n_duck"] = n_duck; alt[order]["mism"] = mism
    J["c4_alt"] = alt
    check(alt["dispatch_after"]["n_duck"] == 0 and alt["erase_before"]["n_duck"] == 0 and alt["no_erase"]["mism"] > 0,
          "alternatives: dispatch after the inserts or erase before them -> no Ducker ever ducks (cleared before it is read); "
          "no erase -> flags stay set and the Ducker re-triggers every block (model mismatch)")
    # H049 E3 cases with the updated ProcRig (16 rows, REAL ctor)
    import H049_trigger_senders as H49
    H41.ProcRig.ROWS = 16; H41.ProcRig.REAL_TABLE = True
    J49 = {"_out": out}
    n0 = len(H49.FAILS); H49.LOG.clear()
    H49.e3(J49)
    P("  H049 E3 re-run with ProcRig ROWS = 16 + REAL ctor table:")
    for s in J49["e3"]:
        P("    %-46s starts %s expected %s; %d of %d samples differ" % (s["case"], s["first_change"], s["expected"], s["model_mismatch"],
                                                                         s["samples"]))
    J["c4_h049_e3"] = {"cases": J49["e3"], "sha": J49["e3_sha"]}
    check(len(H49.FAILS) == n0 and all(s["ok"] for s in J49["e3"]) and sum(s["model_mismatch"] for s in J49["e3"]) == 0,
          "H049 E3 (9 cases) passes unchanged with the 16-row REAL table: 0 differing samples")
    H41.ProcRig.ROWS = 17; H41.ProcRig.REAL_TABLE = False


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H050"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    J = {}
    im = sp16img.Image()
    P("H050 trigger table host rule — target sha256 %s" % emu.SHA)
    c1(im, J); c2(im, J); c3(im, J); c4(im, J, a.out)
    P("\nRESULT: %d failed checks" % len(FAILS))
    rep = "\n".join(LOG) + "\n"
    open(os.path.join(a.out, "h050_report.txt"), "w").write(rep)
    js = json.dumps(J, indent=0, sort_keys=True, default=str)
    open(os.path.join(a.out, "h050.json"), "w").write(js)
    print("report sha256 %s  json sha256 %s" % (sha(rep.encode()), sha(js.encode())))


if __name__ == "__main__":
    main()
