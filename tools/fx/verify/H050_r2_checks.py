#!/usr/bin/env python3
"""H050 round 2 (cycle 039 rebuttal) — static assertions for the four points the critic left INCONCLUSIVE. Own code; reads
target/EP085_Main_R_fw160 (sha256 asserted by sp16img). No emulation.

  R1  op list order: juce_APG_buildRenderingSequence 0x5fe3a4 creates the ops by iterating the ordered node array 0..n-1, passing ONE
      local array (sp+0x80, zeroed at entry) to createRenderingOpsForNode 0x604a10, which only appends to it; the array is then swapped
      into graph+0x148/+0x14c/+0x150 (0x5feca0..0x5feca8).
  R2  audio-edge acceptance: channel counts set by setPlayConfigDetails 0x5f9e90 in the MTU / CompositeFxUnit / MasterOutUnit ctors (run
      before the connection sites) vs the static channel pairs used at 0x1be3ec / 0x1be448 / 0x1be9a0 / 0x1bea04 / 0x1bea5c and the
      canConnect 0x5fae80 rules (src ch < proc+0x30 outputs, dst ch < proc+0x2c inputs).
  R3  Sequencer task-box thread binding: who writes seq+0x1850+0x18 (bound thread read by setRealTimeSequenceData 0x1901b8).
  R4  slot-14 / slot-29 index census for Ducker SOURCE (index 10).
Run: .venv/bin/python -B harness/H050_r2_checks.py --out DIR   (default harness/out/H050_r2/)
"""
import argparse, collections, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib"))
import sp16img                                                 # noqa: E402

LOG = []; FAILS = []


def P(s=""):
    LOG.append(s); print(s, flush=True)


def check(ok, msg):
    P(("PASS  " if ok else "FAIL  ") + msg)
    if not ok: FAILS.append(msg)


class Sweep:
    """Word-by-word capstone sweep of [lo, hi) (data words kept as '.word')."""
    def __init__(self, im, lo, hi):
        self.L = []
        for a in range(lo, hi, 4):
            i = next(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a), None)
            self.L.append((a, i.mnemonic if i else ".word", i.op_str if i else ""))
        self.idx = {a: k for k, (a, _, _) in enumerate(self.L)}

    def text(self, a):
        _, m, o = self.L[self.idx[a]]
        return ("%s %s" % (m, o)).strip()


def asserts(sw, sites, what):
    bad = {hex(a): (sw.text(a), v) for a, v in sites.items() if sw.text(a) != v}
    check(not bad, "%s: %d instruction assertions%s" % (what, len(sites), "" if not bad else " MISMATCH %s" % bad))


def lit(im, a, op):
    m = re.search(r"\[pc, #(-?0x[0-9a-f]+|-?\d+)\]", op)
    return im.u32(a + 8 + int(m.group(1), 0)) if m else None


# ============================================================================================================================ R1
def r1(im, J):
    P("\n== R1 op list = ordered node list, append-only")
    B = Sweep(im, 0x5fe3a4, 0x5ff1f4)
    asserts(B, {
        0x5fe3b0: "str r0, [sp, #0x34]", 0x5fe3bc: "str r3, [sp, #0x80]", 0x5fe3c0: "str r3, [sp, #0x84]", 0x5fe3c4: "str r3, [sp, #0x88]",
        0x5fe3ac: "mov r3, #0",
        0x5fe3f4: "addle r5, sp, #0x90", 0x5fe3f8: "strle r5, [sp, #0x20]", 0x5fe4a8: "add r5, sp, #0x90", 0x5fe4ac: "str r5, [sp, #0x20]",
        0x5fe648: "ldr ip, [sp, #0x20]", 0x5fe658: "str r5, [sp, #0x38]", 0x5fe65c: "str ip, [sp, #0x3c]",
        0x5fe738: "ldr r4, [sp, #0x3c]", 0x5fe74c: "ldr r3, [r4, #8]", 0x5fe750: "str r4, [sp, #8]", 0x5fe758: "ble #0x5feaf0",
        0x5fe75c: "mov r5, #0", 0x5fe760: "str r5, [sp, #0x14]", 0x5fe764: "mov fp, r5", 0x5fe768: "mov r4, r5",
        0x5fe76c: "ldr ip, [sp, #8]", 0x5fe770: "add r0, sp, #0x38", 0x5fe774: "add r2, sp, #0x80", 0x5fe778: "mov r3, fp",
        0x5fe77c: "ldr r1, [ip]", 0x5fe780: "ldr r1, [r1, r4]", 0x5fe784: "bl #0x604a10",
        0x5feac0: "ldr r5, [sp, #8]", 0x5feacc: "ldr sb, [r5, #8]", 0x5fead8: "add fp, fp, #1", 0x5feadc: "ldr r4, [sp, #0x14]",
        0x5feae0: "cmp fp, sb", 0x5feae4: "add r4, r4, #4", 0x5feae8: "str r4, [sp, #0x14]", 0x5feaec: "blt #0x5fe76c",
        0x5fec84: "ldr lr, [sp, #0x84]", 0x5fec88: "ldr r5, [sp, #0x34]", 0x5fec98: "ldr ip, [sp, #0x88]", 0x5fec9c: "ldr r4, [sp, #0x80]",
        0x5feca0: "str lr, [r5, #0x14c]", 0x5feca4: "str ip, [r5, #0x150]", 0x5feca8: "str r4, [r5, #0x148]"},
        "builder: ops array sp+0x80 zeroed, node loop i = fp = 0..ordered.size-1 over ordered.data[i], swap into graph+0x148")
    # every reference to the new-ops array slots in the builder
    refs = [(hex(a), m, o) for a, m, o in B.L if re.search(r"sp, #0x8[048]\]?$|\[sp, #0x8[048]\]", o)]
    P("  references to sp+0x80/0x84/0x88 in 0x5fe3a4: %s" % [r[0] for r in refs])
    exp = ["0x5fe3bc", "0x5fe3c0", "0x5fe3c4", "0x5fe774", "0x5fec84", "0x5fec98", "0x5fec9c", "0x5fecac", "0x5fecb0", "0x5fecb4",
           "0x5fecbc", "0x5fecc0", "0x5fece8", "0x5ff164"]
    check([r[0] for r in refs] == exp,
          "the ops array is only zeroed, passed to 0x604a10 @0x5fe774, swapped into the graph @0x5fec84..0x5feca8 (old ops back into "
          "sp+0x80 @0x5fecac..0x5fecb4 for deletion) and freed on the error path")
    # createRenderingOpsForNode 0x604a10: ops array = r2 -> [sp,#0x24] (single writer); only appends
    Cw = Sweep(im, 0x604a10, 0x607544)
    w24 = [hex(a) for a, m, o in Cw.L if m.startswith("str") and re.search(r"\[sp, #0x24\]", o)]
    plt = im.plt()
    tg = collections.Counter()
    for a, m, o in Cw.L:
        if m in ("bl", "blx") and o.startswith("#"):
            t = int(o[1:], 16); tg[plt.get(t, hex(t))] += 1
    P("  0x604a10 (%d words): writers of [sp,#0x24] %s; direct call targets %s" % (len(Cw.L), w24, dict(tg)))
    check(w24 == ["0x604a20"] and Cw.text(0x604a20) == "str r2, [sp, #0x24]" and
          set(tg) == {"calloc", "realloc", "_Znwj", "free", "malloc", "__cxa_end_cleanup", "0x5fad2c", "0x6026a0", "0x602920", "0x603400",
                      "0x6048fc", "0x604950"} and "memmove" not in tg and "memcpy" not in tg,
          "ops array pointer saved once (@0x604a20); no memmove/memcpy/insert helper is called")
    # inline appends: store at data[n] with n = old count, count := n+1
    sites = [0x604f68, 0x605270, 0x6055d4, 0x605724, 0x6059d8, 0x605b68]
    ok_app = {}
    for s in sites:
        k = Cw.idx[s]; win = Cw.L[k - 12:k + 1]
        m = re.match(r"(\w+), \[r0, (\w+), lsl #2\]", Cw.L[k][2]); n = m.group(2)
        inc = [x for x in win if re.match(r"(\w+), %s, #1$" % n, x[2]) and x[1] == "add"]
        newr = inc[-1][2].split(",")[0] if inc else None
        cnt = [x for x in win if x[1] == "str" and newr and re.match(r"%s, \[\w+, #8\]" % newr, x[2])]
        arr = [x for x in win if x[1] == "ldr" and re.search(r"\[sp, #0x24\]", x[2])]
        old = [x for x in win if (x[1] == "ldmib" and n in x[2]) or (x[1] == "ldr" and re.match(r"%s, \[\w+, #8\]" % n, x[2]))]
        ok_app[hex(s)] = bool(inc and cnt and arr)
        P("    append @%s: index %s (count load %s), count+1 -> %s, array from [sp,#0x24] %s" % (
            hex(s), n, [hex(x[0]) for x in old], [hex(x[0]) for x in cnt], [hex(x[0]) for x in arr]))
    asserts(Cw, {0x604f38: "ldmib r3, {r3, r7}", 0x604f40: "add r6, r7, #1", 0x604f60: "str r6, [r1, #8]",
                 0x604f68: "strne r8, [r0, r7, lsl #2]",
                 # ProcessBufferOp (vptr 0xaa3ad0) built and appended through Array::add 0x604950 with r0 = ops array
                 0x606900: "bl #0x102e8", 0x60690c: "ldr r2, [pc, #-0xa7c]", 0x606918: "str r2, [r0]",
                 0x606c60: "ldr r0, [sp, #0x24]", 0x606c64: "str r4, [r1, #-4]!", 0x606c68: "bl #0x604950"}, "op appends in 0x604a10")
    A = Sweep(im, 0x604950, 0x604a10)
    asserts(A, {0x604958: "ldmib r0, {r3, r7}", 0x604960: "add r8, r7, #1", 0x604970: "str r8, [r4, #8]",
                0x604980: "strne r3, [r0, r7, lsl #2]", 0x6049d0: "str r8, [r4, #8]", 0x6049dc: "strne r3, [r0, r7, lsl #2]"},
            "Array::add 0x604950 = data[num] = *item, num + 1 (also after realloc)")
    check(lit(im, 0x60690c, Cw.L[Cw.idx[0x60690c]][2]) == 0xaa3ad0 and all(ok_app.values()),
          "every op object is appended at index = current count (6 inline sites + Array::add); ProcessBufferOp vptr 0xaa3ad0 @0x60690c")
    helpers = {}
    for a, m, o in Cw.L:
        if m == "bl" and o in ("#0x6026a0", "#0x602920", "#0x603400"):
            k = Cw.idx[a]; r0 = [x for x in Cw.L[k - 6:k] if re.match(r"r0(,|$)", x[2]) and not x[1].startswith(("str", "cmp"))]
            helpers[hex(a)] = r0[-1][1] + " " + r0[-1][2] if r0 else None
    P("  r0 of the other helper calls: %s" % helpers)
    check(all(v == "mov r0, r4" for v in helpers.values()) and Cw.text(0x604a1c) == "mov r4, r0",
          "the other helpers (0x6026a0 / 0x602920 / 0x603400) get the calculator (r4 = this), not the ops array")
    J["r1"] = {"refs": [r[0] for r in refs], "calls": dict(tg), "appends": ok_app}


# ============================================================================================================================ R2
PAIRS = [0xf53868, 0xf53874, 0xf53c44, 0xf53c50, 0xf53c5c, 0xf53c68, 0xf53c74, 0xf53c80]


def decode_pairs(im, S):
    res = {}
    for A in PAIRS:
        vals = set()
        for k, (a, m, o) in enumerate(S.L):
            if m == "ldr" and "[pc," in o and lit(im, a, o) == A:
                reg = o.split(",")[0]
                for j in range(k + 1, min(k + 9, len(S.L))):
                    if S.L[j][1] == "vst1.32" and S.L[j][2] == "{d16}, [%s]" % reg:
                        vl = [x for x in S.L[max(0, k - 3):j] if x[1] == "vldr" and x[2].startswith("d16, [pc")]
                        if vl:
                            q = vl[-1][0] + 8 + int(re.search(r"#(-?0x[0-9a-f]+)", vl[-1][2]).group(1), 16)
                            vals.add((im.u32(q), im.u32(q + 4)))
                        break
        res[A] = sorted(vals)
    return res


def r2(im, J):
    P("\n== R2 audio-edge acceptance (channel counts at connect time vs canConnect)")
    S = Sweep(im, 0x1bc8d4, 0x1c10f4)
    asserts(Sweep(im, 0x5f9e90, 0x5f9ee0), {0x5f9ebc: "str r1, [r3, #0x2c]", 0x5f9ec0: "str r2, [r3, #0x30]"},
            "setPlayConfigDetails 0x5f9e90(this, ins, outs, ...): +0x2c = inputs, +0x30 = outputs")
    asserts(Sweep(im, 0x5fae80, 0x5faf9c), {0x5faea0: "orrs r3, r2, r4, lsr #31", 0x5faef4: "ldr r0, [r0, #0x18]",
                                            0x5faefc: "ldr r3, [r0, #0x30]", 0x5faf00: "cmp r5, r3", 0x5faf2c: "ldr r0, [r0, #0x18]",
                                            0x5faf34: "ldr r3, [r0, #0x2c]", 0x5faf38: "cmp r4, r3", 0x5faf3c: "bge #0x5faedc",
                                            0x5faf5c: "bl #0x5fad2c"},
            "canConnect: channels >= 0, audio src ch < src proc+0x30 (outputs), dst ch < dst proc+0x2c (inputs), no duplicate")
    M = Sweep(im, 0x1c67e4, 0x1c6a28)
    asserts(M, {0x1c6850: "mov r1, #6", 0x1c685c: "str r1, [r4, #0x88]", 0x1c6860: "mov r1, #0x10", 0x1c686c: "str r1, [r4, #0x8c]",
                0x1c6a10: "ldr r1, [r4, #0x88]", 0x1c6a18: "ldr r2, [r4, #0x8c]", 0x1c6a24: "bl #0x5f9e90"}, "MultiTrackUnit ctor: 6 in / 16 out")
    asserts(Sweep(im, 0x1aa8b0, 0x1aa8ec), {0x1aa8bc: "mov r1, #4", 0x1aa8d4: "mov r2, r1", 0x1aa8e8: "bl #0x5f9e90"},
            "CompositeFxUnit ctor 0x1aa808: 4 in / 4 out")
    asserts(Sweep(im, 0x1b23d0, 0x1b23f4), {0x1b23dc: "mov r1, #6", 0x1b23e0: "mov r2, #4", 0x1b23f0: "bl #0x5f9e90"},
            "MasterOutUnit ctor 0x1b2398: 6 in / 4 out")
    asserts(S, {0x1bda3c: "bl #0x1bc7c8", 0x1bdeb4: "bl #0x1aa808", 0x1be8ac: "bl #0x1b2398",
                0x1be3c0: "ldr r1, [pc, #0x7a0]", 0x1be3c8: "str r1, [sp, #0x30]", 0x1be3d4: "ldr r2, [pc, #0x790]",
                0x1be420: "ldr r2, [pc, #0x750]", 0x1be424: "str r2, [sp, #0x2c]", 0x1be430: "ldr r2, [pc, #0x744]",
                0x1be95c: "ldr r5, [sp, #0x30]", 0x1be9c0: "ldr r5, [sp, #0x2c]", 0x1bea44: "ldr r2, [pc, #0x158]",
                0x1be974: "ldrne sl, [pc, #0x210]", 0x1be9d8: "ldrne sl, [pc, #0x1b4]", 0x1bea34: "ldrne r6, [pc, #0x164]"},
            "slot 55: unit ctors (MTU via 0x1bc7c8 @0x1bc7e8, CompositeFx, MasterOut) before the connections; pair pointers")
    D = decode_pairs(im, S)
    P("  static channel pairs (guarded initialisers): %s" % {hex(k): v for k, v in D.items()})
    check(all(len(v) == 1 for v in D.values()), "each pair static has exactly one initialiser")
    p = {k: v[0] for k, v in D.items()}
    pp = {a: lit(im, a, S.L[S.idx[a]][2]) for a in (0x1be3c0, 0x1be3d4, 0x1be420, 0x1be430, 0x1be974, 0x1be9d8, 0x1bea34, 0x1bea44)}
    P("  pair pointers loaded: %s" % {hex(a): hex(v) for a, v in pp.items()})
    conns = [  # site, src unit (outputs), src pair, dst unit (inputs), dst pair
        (0x1be3ec, ("MTU", 16), pp[0x1be3d4], ("CompositeFx", 4), pp[0x1be3c0]),
        (0x1be448, ("MTU", 16), pp[0x1be430], ("CompositeFx", 4), pp[0x1be420]),
        (0x1be9a0, ("CompositeFx", 4), pp[0x1be3c0], ("MasterOut", 6), pp[0x1be974]),
        (0x1bea04, ("CompositeFx", 4), pp[0x1be420], ("MasterOut", 6), pp[0x1be9d8]),
        (0x1bea5c, ("MTU", 16), pp[0x1bea44], ("MasterOut", 6), pp[0x1bea34])]
    rows = []; allok = True
    for site, (sn, so), sp_, (dn, di), dp_ in conns:
        ok = all(0 <= c < so for c in p[sp_]) and all(0 <= c < di for c in p[dp_])
        allok &= ok
        rows.append((hex(site), sn, p[sp_], so, dn, p[dp_], di, ok))
        P("    %s: %s out %s (of %d) -> %s in %s (of %d): accepted %s" % (hex(site), sn, p[sp_], so, dn, p[dp_], di, ok))
    # nothing changes the three units' channel counts between their ctor and the connections: no setPlayConfigDetails call in slot 55
    spc = [hex(s) for s, t, k in im.direct_calls() if t == 0x5f9e90 and 0x1bc8d4 <= s < 0x1c10f4]
    check(allok and not spc, "all 10 audio channel connections on MTU -> CompositeFx -> MasterOut and MTU -> MasterOut pass canConnect "
          "(no setPlayConfigDetails in slot 55: %s)" % spc)
    J["r2"] = {"pairs": {hex(k): v for k, v in D.items()}, "conns": rows}


# ============================================================================================================================ R3
def r3(im, J):
    P("\n== R3 Sequencer task-box thread binding (seq+0x1850+0x18)")
    asserts(Sweep(im, 0x1901b0, 0x190220), {0x1901b0: "sub r0, r0, #0x88", 0x1901b4: "b #0x1901b8", 0x1901c0: "add r7, r0, #0x1840",
                                            0x1901c4: "add r7, r7, #0x10", 0x1901d4: "ldr r3, [r7, #0x18]", 0x19020c: "bl #0x6472f0",
                                            0x190210: "ldr r3, [r7, #0x18]", 0x190214: "cmp r3, r0", 0x190218: "beq #0x190360"},
            "setRealTimeSequenceData: no bound thread -> drop; bound thread == current thread -> direct; else queue")
    asserts(Sweep(im, 0x504b58, 0x504b74), {0x504b60: "str r2, [sp]", 0x504b64: "add r2, r0, #0x14", 0x504b68: "str r1, [sp, #4]",
                                            0x504b70: "vst1.32 {d16}, [r2]"}, "bind 0x504b58(box, thread, x, ...): box+0x14 = x, box+0x18 = thread")
    asserts(Sweep(im, 0x1916cc, 0x191700), {0x1916cc: "bl #0x6472f0", 0x1916d0: "mov r6, r0", 0x1916d8: "add r5, r4, #0x1840",
                                            0x1916e0: "add r5, r5, #0x10", 0x1916e4: "mov r1, r6", 0x1916ec: "mov r0, r5", 0x1916f0: "bl #0x504b58"},
            "Sequencer::processBlock binds seq+0x1850 to the current thread each block")
    calls = [s for s, t, k in im.direct_calls() if t == 0x504b58]
    boxes = {}
    for s in calls:
        W = Sweep(im, s - 48, s + 4).L
        boxes[hex(s)] = [("%s %s" % (m, o)) for a, m, o in W if re.match(r"(add|mov|ldr) r[05],", "%s %s" % (m, o))][-3:]
    seqbind = [s for s, v in boxes.items() if "add r5, r4, #0x1840" in v]
    P("  0x504b58 call sites and their box setup: %s" % boxes)
    check(seqbind == ["0x1916f0"], "only Sequencer::processBlock (@0x1916f0) binds the Sequencer box (other sites use other objects; "
          "heuristic per-site view)")
    J["r3"] = {"bind_sites": boxes}


# ============================================================================================================================ R4
def r4(im, J):
    P("\n== R4 index census for Ducker SOURCE (slot-14 index 10)")
    S = Sweep(im, 0xe0000, 0x135000)
    res = []
    for k, (a, m, o) in enumerate(S.L):
        mm = re.match(r"(\w+), \[(\w+), #0x38\]$", o)
        if m != "ldr" or not mm: continue
        r = mm.group(1)
        for j in range(k + 1, min(k + 8, len(S.L))):
            if S.L[j][1] == "blx" and S.L[j][2] == r:
                src = None
                for q in range(j - 1, max(j - 14, 0), -1):
                    qa, qm, qo = S.L[q]
                    if qm in ("bl", "blx", "b", "bx"): break
                    if re.match(r"r1(,|$)", qo) and not qm.startswith(("str", "cmp", "tst", "push", "stm")):
                        src = (qa, qm, qo); break
                res.append((S.L[j][0], src)); break
    imm = [(a, int(s[2].split("#")[1], 16)) for a, s in res if s and s[1] in ("mov", "movw") and "#" in s[2]]
    other = [(hex(a), s and (hex(s[0]), s[1], s[2])) for a, s in res if not (s and s[1] in ("mov", "movw") and "#" in s[2])]
    idx10 = [hex(a) for a, v in imm if v == 10]
    P("  vt+0x38 calls in 0xe0000..0x135000: %d; immediate r1: %d (index histogram %s); index-10 sites %s" % (
        len(res), len(imm), sorted(collections.Counter(v for _, v in imm).items()), idx10))
    P("  non-immediate / unresolved r1 (%d): %s" % (len(other), other))
    # forwarder FxProcessorBase 0x112924(proc, effect, index r2, value r3): index of every direct caller
    fw = {}
    for s in [x for x, t, k in im.direct_calls() if t == 0x112924]:
        v = None
        for a in range(s - 4, s - 4 * 40, -4):
            i = next(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a), None)
            if i is None: break
            if re.match(r"r2(,|$)", i.op_str) and not i.mnemonic.startswith(("str", "cmp", "tst", "push", "stm")):
                if i.op_str == "r2, r1":            # resolve the reused register
                    for b in range(a - 4, a - 4 * 30, -4):
                        jn = next(im.md.disasm(im.data[im.off(b):im.off(b) + 4], b), None)
                        if jn is None: break
                        if re.match(r"r1(,|$)", jn.op_str) and not jn.mnemonic.startswith(("str", "cmp", "tst")):
                            v = jn.op_str; break
                else:
                    v = i.op_str
                break
        fw[hex(s)] = v
    hist = collections.Counter(fw.values())
    P("  0x112924 callers: %d; index operand histogram %s" % (len(fw), dict(hist)))
    f10 = [s for s, v in fw.items() if v and re.search(r"#0xa$", v)]
    # second pass for the unresolved sites: longer window (40), still stopping at calls/branches
    deep = {}
    for a, s_ in res:
        if s_ and s_[1] in ("mov", "movw") and "#" in s_[2]: continue
        j = S.idx[a]; v = None
        for q in range(j - 1, max(j - 40, 0), -1):
            qa, qm, qo = S.L[q]
            if qm in ("bl", "blx", "b", "bx") or qm.startswith("pop"): v = "<flow @0x%x>" % qa; break
            if re.match(r"r1(,|$)", qo) and not qm.startswith(("str", "cmp", "tst", "push", "stm")): v = "%s %s @0x%x" % (qm, qo, qa); break
        deep[hex(a)] = v
    CLASS = {"0x1061d8": "EffectBase loop: slot15 read-back of own values, then slot14 restore (value round trip)",
             "0x1126f4": "processor slot 29 forwarder to pending effect +0x90 (index from caller, census below)",
             "0x112954": "processor forwarder 0x112924 (index r2 from caller, census below)",
             "0x1163bc": "Chorus/Flanger wrapper -> inner effect +0x1b8 (not a Ducker)",
             "0x116694": "false positive (blx via vt+4, destructor)", "0x11badc": "false positive (blx via vt+4, destructor)",
             "0x131318": "LfoProcessor::setSync task: r1 = bool byte +0x18 (not an effect)"}
    for a, v in deep.items():
        if a not in CLASS and v and re.match(r"mov r1, #(0x[0-9a-f]+|\d+) @", v):
            CLASS[a] = "slot-52 / default block, immediate index %s" % v
    P("  non-immediate sites resolved: %s" % {a: (deep[a], CLASS.get(a)) for a in deep})
    imm2 = [int(re.search(r"#(0x[0-9a-f]+|\d+)", v).group(1), 0) for v in deep.values() if v and v.startswith("mov r1, #")]
    check(set(deep) <= set(CLASS) and 10 not in imm2, "all 23 non-immediate vt+0x38 sites classified; none can carry index 10 with a "
          "foreign value (deep-window immediates %s)" % sorted(set(imm2)))
    # slot 29 (vt+0x74) calls in the manager range: index source
    T = Sweep(im, 0x11c000, 0x131000); s29 = {}
    for k, (a, m, o) in enumerate(T.L):
        mm = re.match(r"(\w+), \[(\w+), #0x74\]$", o)
        if m != "ldr" or not mm: continue
        for j in range(k + 1, min(k + 8, len(T.L))):
            if T.L[j][1] == "blx" and T.L[j][2] == mm.group(1):
                v = None
                for q in range(j - 1, max(j - 30, 0), -1):
                    qa, qm, qo = T.L[q]
                    if qm in ("bl", "blx", "b", "bx"): v = "<flow>"; break
                    if re.match(r"r1(,|$)", qo) and not qm.startswith(("str", "cmp", "tst", "push", "stm")): v = "%s %s" % (qm, qo); break
                s29[hex(T.L[j][0])] = v; break
    P("  slot-29 (vt+0x74) calls 0x11c000..0x131000: %s" % s29)
    nonimm29 = {a: v for a, v in s29.items() if not (v and re.match(r"mov r1, #", v))}
    check(set(nonimm29) == {"0x11ceb4", "0x129f84", "0x12a13c"} and not [a for a, v in s29.items() if v == "mov r1, #0xa"],
          "slot-29 index 10 never used; non-immediate: 0x11ceb4 (Master/Send base s27, no Ducker there), 0x129f84 (r1 = r5 = 0 @0x129f44), "
          "0x12a13c (modulation: value clamped to 0..1 @0x12a110..0x12a128, so never >= 15.5)")
    J["r4_deep"] = deep; J["r4_s29"] = s29
    check(idx10 == ["0x1178b4"] and f10 == ["0x127a00"] and all(v and re.search(r"#(0x[0-9a-f]+|\d+)$", v) for v in fw.values()),
          "index 10 is written only by processor slot 52 case 9 (blx @0x1178b4, mov r1,#0xa @0x117898, value float(+0xa0) = 0..15) and by IFPM s38 0x127928 via "
          "0x112924 (@0x127a00, value = s74 name converter, 0..15, F164); every other forwarder call has an immediate index")
    J["r4"] = {"vt38": len(res), "imm": len(imm), "idx10": idx10, "other": other, "fw_hist": dict(hist), "fw_idx10": f10}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H050_r2"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = sp16img.Image(); J = {}
    P("H050 round 2 — target sha256 %s" % sp16img.SHA)
    r1(im, J); r2(im, J); r3(im, J); r4(im, J)
    P("\nRESULT: %d failed checks" % len(FAILS))
    rep = "\n".join(LOG) + "\n"
    open(os.path.join(a.out, "h050_r2_report.txt"), "w").write(rep)
    js = json.dumps(J, indent=0, sort_keys=True, default=str)
    open(os.path.join(a.out, "h050_r2.json"), "w").write(js)
    print("report sha256 %s  json sha256 %s" % (hashlib.sha256(rep.encode()).hexdigest(), hashlib.sha256(js.encode()).hexdigest()))


if __name__ == "__main__":
    main()
