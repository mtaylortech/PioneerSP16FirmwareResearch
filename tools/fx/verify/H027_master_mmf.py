#!/usr/bin/env python3
"""H027 — Master/Send MultiModeFilter (array index 5) vs the Insert one (index 3): construction identity, vtable identity and
bit-exactness of harness/models/mmf.py at non-default settings inside the real Master and Send processors.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time
and never stored; outputs are our own derived numbers. Emulation is guest-memory only; nothing is written outside --out.

Sections (criteria of kb/cycles/033.md):
  C1 static  : capstone over the three processor ctors (Insert 0x118b0c, Master 0x114bc0, Send 0x11bbe4): the MMF `new`, the ctor
               call 0x109e8c and its argument set-up, the post-construction calls on the MMF array slot (slot 22 vt+0x58, 0x106c7c),
               census of callers of 0x109e8c and of the vptr literal 0x8420b8; the slot-52/53 default case bodies for MMF.
  C1 dynamic : the REAL processor ctors (via harness/H077 EmuProc) with entry hooks on 0x109e8c, the EffectBase ctor 0x1067d8, all 32
               MMF vtable targets and 0x106c7c, logging every call whose `this` is the MMF object (phase, caller function, args);
               a canonical object-graph dump (heap pointers replaced by graph ids) of the MMF object after the processor ctor and
               after prepareToPlay + enable, compared Insert[3] vs Master[5] vs Send[5].
  C2         : vptr of the built objects; MMF vtable slot table.
  C3         : REAL Master processBlock 0x112acc / Send 0x119994 with the ctor-built index-5 object, 17 non-default settings
               (slot 14 and the real manager base s27 0x11ce58 on a stand-in manager) x noise/sine/impulse x 200 blocks, vs
               fx_processors + effectbase + mmf.py (model MMF built from mmf.INSERT_DEFAULTS, not from the logged defaults);
               per block outputs (raw bits), processor state, slot 5/6/7/8 + feed events, wrapper state of all 10 effects; MMF
               field-level state (H076 field table) every 10 blocks and at the end.
  C4         : Master, settings the object accepts but the UI does not send (FILTERTYPE 3/4/5/7/-1, FILTERDB 0/3; F171).
  C5 (alt)   : model variants that must fail (no post-HPF, FILTERDB 2 = 12 dB, Chorus-style mix law, Q' = Q in 24 dB stages).
Run: .venv/bin/python -B harness/H027_master_mmf.py --out DIR [--jobs N]
"""
import argparse, bisect, hashlib, json, math, os, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from sp16img import Image                                      # noqa: E402
import H077_master_send_proc as H77                            # noqa: E402
import H044_effectbase_wrapper as H44                          # noqa: E402
import H076_slot27_reset as H76                                # noqa: E402
import effectbase as EB                                        # noqa: E402
import fx_processors as FP                                     # noqa: E402
import mmf as MM                                               # noqa: E402
from lofi import F                                             # noqa: E402

N = 64
MMF_CTOR, MMF_SIZE, MMF_VT = 0x109e8c, 0x4a0, 0x8420b8
EB_CTOR, POST_HPF, NEW = 0x1067d8, 0x106c7c, 0x102e8
BASE_S27 = 0x11ce58
MGR_VT = {"master": 0x8437ec, "send": 0x8446d4}
IDX = {"insert": 3, "master": 5, "send": 5}
CTOR = {"insert": 0x118b0c, "master": 0x114bc0, "send": 0x11bbe4}
S52 = {"insert": 0x117434, "master": 0x1133f4, "send": 0x11a364}       # Insert slot 53 / Master, Send slot 52 (initEffectDefaults)
UI_DEFAULT_IDX = (0, 1, 2, 3, 5, 6, 7)


def sha(b): return hashlib.sha256(b).hexdigest()
def pack(xs): return struct.pack("<%df" % len(xs), *xs)
def s32(u): return u - (1 << 32) if u & 0x80000000 else u


# ===================================================================================================================== C1 static
def dis_words(im, a, end):
    """Word-by-word ARM decode (literal pools become .word) -> list of (addr, mnemonic, op_str)."""
    out = []
    for va in range(a, end, 4):
        o = im.off(va); w = im.data[o:o + 4]
        ins = list(im.md.disasm(w, va))
        out.append((va, ins[0].mnemonic, ins[0].op_str) if ins else (va, ".word", "0x%08x" % struct.unpack("<I", w)[0]))
    return out


def norm(ins, base):
    """Normalise branch targets of local branches to offsets from base; keep call targets absolute."""
    out = []
    for va, mn, op in ins:
        if mn in ("b", "bne", "beq", "bhi", "bls", "bgt", "blt", "bge", "ble", "bcc", "bcs", "bpl", "bmi") and op.startswith("#0x"):
            op = "+0x%x" % (int(op[1:], 16) - base)
        if mn == ".word": op = "<lit>"
        out.append("%s %s" % (mn, op))
    return out


def static_part(im, P, check, J):
    J["calls_to_mmf_ctor"] = sites = [(hex(s), k, hex(im.func_of(s)[0])) for s, t, k in im.direct_calls() if t == MMF_CTOR]
    P("  direct branches to the MMF ctor 0x109e8c (whole .text bit-pattern scan): %s" % sites)
    check(sorted(int(f, 16) for _, _, f in sites) == sorted(CTOR.values()) and all(k == "bl" for _, k, _ in sites),
          "0x109e8c is called exactly once from each of the three processor ctors and from nowhere else")
    # vptr literal census
    pat = struct.pack("<I", MMF_VT); offs = []; i = 0
    while True:
        i = im.data.find(pat, i)
        if i < 0: break
        offs.append(i); i += 1
    vas = []
    for o in offs:
        for v, sz, fo in im.segs:
            if fo <= o < fo + sz: vas.append(v + o - fo)
    owners = [(hex(va), hex(im.func_of(va)[0]) if im.func_of(va) else None) for va in vas]
    J["vptr_literal_sites"] = owners
    P("  file words equal to the MMF vptr 0x8420b8: %s" % owners)
    check(all(f is not None and int(f, 16) not in CTOR.values() for _, f in owners) and
          any(f is not None and int(f, 16) == MMF_CTOR for _, f in owners),
          "the vptr literal is in the MMF ctor's literal pool (and one other non-processor function), never in a processor ctor")
    # the MMF ctor's own EffectBase ctor call and its arguments
    mc = dis_words(im, MMF_CTOR, MMF_CTOR + 0x80)
    k = next(j for j, x in enumerate(mc) if x[1] == "bl" and x[2] == "#0x%x" % EB_CTOR)
    J["mmf_ctor_head"] = ["%x %s %s" % x for x in mc[:k + 1]]
    P("  MMF ctor 0x109e8c up to its EffectBase ctor call:\n    " + "\n    ".join(J["mmf_ctor_head"]))
    # per processor: the MMF build window
    win = {}
    for which, c in CTOR.items():
        st = im.func_of(c); ins = dis_words(im, c, st[1])
        kc = next(j for j, x in enumerate(ins) if x[1] == "bl" and x[2] == "#0x%x" % MMF_CTOR)
        kn = max(j for j in range(kc) if ins[j][1] == "mov" and ins[j][2] == "r0, #0x%x" % MMF_SIZE)
        w = ins[kn:kc + 2]
        win[which] = dict(start=hex(ins[kn][0]), call=hex(ins[kc][0]), text=norm(w, ins[kn][0]))
        # post-construction calls on array element 4*idx
        posts = []
        for j in range(len(ins) - 6):
            if ins[j][1] == "ldrhi" and ins[j][2].startswith("r0, [r3, #"):
                off = int(ins[j][2].split("#")[1].rstrip("]"), 16)
                nxt = ins[j + 1:j + 4]
                r1 = r2 = None
                for q in range(j - 6, j):
                    if ins[q][1] == "mov" and ins[q][2].startswith("r1, #"): r1 = int(ins[q][2].split("#")[1], 16)
                    if ins[q][1] == "movt" and ins[q][2].startswith("r2, #"): r2 = int(ins[q][2].split("#")[1], 16) << 16
                if nxt[0][1] == "bl":
                    posts.append((off // 4, "bl " + nxt[0][2], r1, r2))
                elif nxt[0][1] == "ldr" and nxt[1][1] == "ldr" and nxt[2][1] == "blx":
                    posts.append((off // 4, "vcall vt+%s" % nxt[1][2].split("#")[1].rstrip("]"), r1, r2))
        win[which]["posts"] = posts
    J["build_windows"] = win
    for which in CTOR:
        P("  %-6s MMF build %s..%s: %s" % (which, win[which]["start"], win[which]["call"], " ; ".join(win[which]["text"])))
    check(win["insert"]["text"] == win["master"]["text"] == win["send"]["text"],
          "the MMF build window (new 0x4a0 -> r1 = 0xac44 (44100), r2 = 0x40 (64), r0 = new -> bl 0x109e8c) is instruction-identical "
          "in all three processor ctors (local branches normalised)")
    for which in CTOR:
        mine = [p for p in win[which]["posts"] if p[0] == IDX[which]]
        win[which]["posts_mmf"] = mine
        P("  %-6s post-construction calls on array element %d: %s" % (which, IDX[which],
          [(c, None if r1 is None else r1, None if r2 is None else "0x%08x (%g)" % (r2, u2f(r2))) for _, c, r1, r2 in mine]))
    norm_posts = {w: [(c, r1, r2) for _, c, r1, r2 in win[w]["posts_mmf"]] for w in CTOR}
    check(norm_posts["insert"] == norm_posts["master"] == norm_posts["send"] ==
          [("vcall vt+0x58", 0, None), ("bl #0x106c7c", 1, 0x41200000)],
          "post-construction calls on the MMF element: slot 22 (vt+0x58)(e, 0) then 0x106c7c(e, 1, 10.0f), identical in all three")
    # slot-52/53 default case for MMF
    cases = {}
    for which, a in S52.items():
        ins = dis_words(im, a, a + 0x40)
        k = next(j for j, x in enumerate(ins) if x[1] == "ldrls" and x[2].startswith("pc, [pc, r1, lsl #2]"))
        tab = [im.u32(ins[k][0] + 8 + 4 * i) for i in range(10)]
        tgt = tab[IDX[which]]; nxt = min([t for t in tab if t > tgt] + [im.func_of(a)[1]])
        body = dis_words(im, tgt, nxt)
        # semantic token stream: getter calls (bl), slot-14 vcalls (vt+0x38) with the last immediate r1 / r2 and the array
        # element they load (ldr r0, [r3, #4*i]); one hop through an unconditional branch out of the case (shared tails)
        toks = []; r1 = r2 = el = None; seq = list(body); hops = 0; k = 0
        while k < len(seq):
            va, mn, op = seq[k]; k += 1
            if mn == "bl": toks.append(("call", op))
            elif mn == "mov" and op.startswith("r1, #"): r1 = int(op.split("#")[1], 16)
            elif mn == "mov" and op.startswith("r2, #"): r2 = int(op.split("#")[1], 16)
            elif mn in ("ldr", "ldrhi") and op.startswith("r0, [r3, #"): el = int(op.split("#")[1].rstrip("]"), 16) // 4
            elif mn == "ldr" and op == "r3, [r3, #0x38]":
                toks.append(("slot14", "elem=%s" % ("IDX" if el == IDX[which] else el), r1, r2)); r2 = None
            elif mn == "b" and op.startswith("#0x"):
                t = int(op[1:], 16)
                if not (tgt <= t < nxt) and hops == 0:
                    hops += 1; tail = dis_words(im, t, t + 0x40)
                    cut = next((j for j, x in enumerate(tail) if x[1] in ("b", "pop", "vpop", "bl") or
                                (j > 0 and tail[j - 1][1] == "blx")), len(tail))
                    seq = seq[:k] + tail[:cut]; toks.append(("tail-hop", hex(t), cut))
        hop_info = [t[1:] for t in toks if t[0] == "tail-hop"]
        toks = [t for t in toks if t[0] != "tail-hop"]
        cases[which] = dict(table=[hex(t) for t in tab], case=hex(tgt), end=hex(nxt), n_ins=len(body), hops=hops, hop=hop_info,
                            tokens=toks)
    J["slot52_mmf_case"] = cases
    for which in S52:
        c = cases[which]
        P("  %-6s slot-5%s jump-table entry %d -> MMF case %s..%s (%d words, tail hop %s): getters %s; slot-14 (index, r2 imm) %s" % (
            which, "3" if which == "insert" else "2", IDX[which], c["case"], c["end"], c["n_ins"], c["hop"],
            [t[1] for t in c["tokens"] if t[0] == "call"],
            [(t[2], None if t[3] is None else hex(t[3])) for t in c["tokens"] if t[0] == "slot14"]))
    check(cases["insert"]["tokens"] == cases["master"]["tokens"] == cases["send"]["tokens"] and
          all(t[1] == "elem=IDX" for t in cases["master"]["tokens"] if t[0] == "slot14"),
          "MMF default cases (Insert slot 53 case 3, Master/Send slot 52 case 5): same getter calls in the same order and the same "
          "slot-14 index sequence on the MMF array element (register allocation / tail merging differ only)")
    return J


# ===================================================================================================================== C1 dynamic
def chain_watch(e, addr, cb):
    old = e.watch.get(addr)
    if old is None: e.add_watch(addr, cb)
    else: e.watch[addr] = lambda em, old=old: (old(em), cb(em))


class Graph:
    """Canonical dump of a heap object graph: heap pointers -> (graph id, offset); stop at labelled objects."""
    def __init__(self, e, stops):
        self.e = e; al = sorted((a, n) for a, n, _ in e.allocs); self.starts = [a for a, _ in al]; self.al = al
        self.stops = stops

    def find(self, v):
        i = bisect.bisect_right(self.starts, v) - 1
        if i >= 0:
            a, n = self.al[i]
            if a <= v < a + n: return a, n
        return None

    def dump(self, root):
        e = self.e; ids = {root: 0}; order = [root]; out = []; q = 0
        while q < len(order):
            a = order[q]; q += 1
            _, n = self.find(a)
            row = []
            for off in range(0, n - n % 4, 4):
                w = e.u32(a + off); f = self.find(w)
                if f and w not in self.stops.values() and f[0] not in self.stops.values():
                    if f[0] not in ids: ids[f[0]] = len(order); order.append(f[0])
                    row.append("#%d+0x%x" % (ids[f[0]], w - f[0]))
                elif f:
                    lab = next((k for k, v in self.stops.items() if v == f[0]), "?")
                    row.append("%s+0x%x" % (lab, w - f[0]))
                else:
                    row.append("%08x" % w)
            out.append(dict(id=ids[a], size=n, words=row))
        return out


def dynamic_ctor(which, im):
    """REAL processor ctor + prepareToPlay + enable, logging every call on the MMF object."""
    log = []; phase = ["ctor"]; snap = {}
    vt_targets = {}
    for k in range(32): vt_targets.setdefault(im.u32(MMF_VT + 4 * k), []).append(k)
    orig_new = H77.H31.new_emu
    state = dict(mmf=None)

    def caller(em):
        lr = em.uc.reg_read(emu.LR) & ~1
        f = im.func_of(lr)
        if f is None: return "lr 0x%x" % lr
        if f[0] == CTOR[which]: return "processor ctor"
        if f[0] == S52[which]: return "processor slot-5%s (defaults)" % ("3" if which == "insert" else "2")
        return "0x%x" % f[0]

    def hooked():
        e = orig_new()
        base_add = e.add_watch
        def add_watch(addr, cb):                       # H077 adds its watches after ours: chain instead of replacing
            if addr in e.watch:
                old = e.watch[addr]; e.watch[addr] = lambda em, old=old: (old(em), cb(em))
            else: base_add(addr, cb)
        e.add_watch = add_watch
        def on_ctor(em):
            state["mmf"] = em.r(0)
            log.append(dict(phase=phase[0], fn="MMF ctor 0x109e8c", by=caller(em), args=[em.r(1), em.r(2)]))
        e.add_watch(MMF_CTOR, on_ctor)
        def on_eb(em):
            if em.r(0) == state["mmf"]:
                log.append(dict(phase=phase[0], fn="EffectBase ctor 0x1067d8", by=caller(em), args=[em.r(1), em.r(2), em.r(3)]))
        e.add_watch(EB_CTOR, on_eb)
        for t, ks in vt_targets.items():
            nargs = {14: 2, 22: 1}.get(ks[0], 2)       # slot 14(idx, value bits); slot 22(on); others: r1, r2 as seen
            def on_slot(em, t=t, ks=ks, nargs=nargs):
                if state["mmf"] is not None and em.r(0) == state["mmf"]:
                    log.append(dict(phase=phase[0], fn="vt slot %s 0x%x" % ("/".join(map(str, ks)), t), by=caller(em),
                                    args=[em.r(1), em.r(2)][:nargs]))
            e.add_watch(t, on_slot)
        def on_hpf(em):
            if em.r(0) == state["mmf"]:
                log.append(dict(phase=phase[0], fn="post-HPF 0x106c7c", by=caller(em), args=[em.r(1), em.r(2)]))
        e.add_watch(POST_HPF, on_hpf)
        def on_prep(em):
            if phase[0] == "ctor":                     # end of the processor ctor: dump the graph before prepareToPlay
                p = em.r(0); arr = em.u32(p + 0x80); cnt = em.u32(p + 0x88)
                stops = {"PROC": p, "ARRAY": arr}
                for i in range(cnt):
                    oo = em.u32(arr + 4 * i)
                    if oo != state["mmf"]: stops["EFFECT%d" % i] = oo
                tob = em.u32(p + 0x94)
                if tob: stops["TEMPO"] = tob
                snap["after_ctor"] = Graph(em, stops).dump(state["mmf"])
                phase[0] = "prepareToPlay"
        e.add_watch(H77.PROC[which]["prep"], on_prep)
        def on_dis(em):
            if phase[0] != "enable": phase[0] = "enable"
        e.add_watch(H77.DISABLE, on_dis)
        return e

    H77.H31.new_emu = hooked
    try:
        x = H77.EmuProc(which)
    finally:
        H77.H31.new_emu = orig_new
    o = x.objs[IDX[which]]
    assert o == state["mmf"], "array element %d is not the object built by 0x109e8c" % IDX[which]
    stops = {"PROC": x.p, "ARRAY": x.arr, "TEMPO": x.tob}
    for i, oo in enumerate(x.objs):
        if oo != o: stops["EFFECT%d" % i] = oo
    g_final = Graph(x.e, stops).dump(o)
    return x, log, g_final, snap["after_ctor"]


def graph_diff(a, b):
    d = []
    if len(a) != len(b): d.append(("node count", len(a), len(b)))
    for na, nb in zip(a, b):
        if na["size"] != nb["size"]: d.append(("size", na["id"], na["size"], nb["size"])); continue
        for k, (wa, wb) in enumerate(zip(na["words"], nb["words"])):
            if wa != wb: d.append((na["id"], hex(4 * k), wa, wb))
    return d


def dyn_part(im, P, check, J):
    res = {}
    for which in ("insert", "master", "send"):
        x, log, g, g0 = dynamic_ctor(which, im)
        e = x.e; o = x.objs[IDX[which]]
        eb = dict(vptr=hex(e.u32(o)), fs=e.u32(o + 0x90), blk=e.u32(o + 0x94), mode=e.u32(o + 0x98), a8=e.rd(o + 0xa8, 1)[0],
                  hpf_req=e.rd(o + 0xcc, 1)[0], hpf_fc=u2f(e.u32(o + 0xd0)))
        res[which] = dict(log=log, graph=g, graph0=g0, eb=eb, defaults=[(i, b) for i, b in x.defaults[IDX[which]]],
                          nodes=len(g), bytes=sum(n["size"] for n in g))
    J["dyn"] = {w: dict(log=r["log"], eb=r["eb"], defaults=[(i, hex(b), u2f(b)) for i, b in r["defaults"]], nodes=r["nodes"],
                        bytes=r["bytes"]) for w, r in res.items()}
    for w, r in res.items():
        P("  %-6s index %d: vptr %s, EffectBase fs %d block %d mode %d, +0xa8 %d, post-HPF req %d fc %g; graph %d objects / %d bytes" % (
            w, IDX[w], r["eb"]["vptr"], r["eb"]["fs"], r["eb"]["blk"], r["eb"]["mode"], r["eb"]["a8"], r["eb"]["hpf_req"],
            r["eb"]["hpf_fc"], r["nodes"], r["bytes"]))
        for L in r["log"]:
            P("      [%s] %s by %s args %s" % (L["phase"], L["fn"], L["by"], ["0x%x" % v for v in L["args"]]))
    def strip(lg):
        return [(L["phase"], L["fn"], L["by"].replace("slot-53", "slot-5x").replace("slot-52", "slot-5x"), tuple(L["args"])) for L in lg]
    check(strip(res["insert"]["log"]) == strip(res["master"]["log"]) == strip(res["send"]["log"]),
          "the sequence of calls on the MMF object during ctor / prepareToPlay / enable (function, caller role, arguments) is "
          "identical for Insert[3], Master[5], Send[5]")
    ctor_args = {w: next(L["args"] for L in r["log"] if L["fn"].startswith("MMF ctor")) for w, r in res.items()}
    eb_args = {w: next(L["args"] for L in r["log"] if L["fn"].startswith("EffectBase")) for w, r in res.items()}
    J["ctor_args"] = ctor_args; J["eb_args"] = eb_args
    check(all(v == [44100, 64] for v in ctor_args.values()) and all(v == [44100, 64, 0] for v in eb_args.values()),
          "MMF ctor called with (fs 44100, block 64) and EffectBase ctor with (44100, 64, mode 0) in all three processors")
    check(all(r["eb"]["vptr"] == hex(MMF_VT) for r in res.values()), "vptr of the built object = 0x8420b8 (MultiModeFilter) in all three")
    dm0 = graph_diff(res["insert"]["graph0"], res["master"]["graph0"]); ds0 = graph_diff(res["master"]["graph0"], res["send"]["graph0"])
    P("  canonical object graph at the end of the processor ctor: Insert vs Master %d differing words, Master vs Send %d" % (len(dm0), len(ds0)))
    check(not dm0 and not ds0, "MMF object graph word-identical Insert[3] = Master[5] = Send[5] at the end of the processor ctor")
    dpp = graph_diff(res["master"]["graph0"], res["master"]["graph"])
    P("  Master: words changed in the MMF graph by prepareToPlay + enable: %d %s" % (len(dpp), dpp[:6]))
    J["master_graph_changed_by_prepare"] = dpp[:50]
    J["graph_hash"] = {w: sha(json.dumps(r["graph"]).encode())[:16] for w, r in res.items()}
    dm = graph_diff(res["insert"]["graph"], res["master"]["graph"]); ds = graph_diff(res["master"]["graph"], res["send"]["graph"])
    J["graph_diff_insert_master"] = dm[:50]; J["graph_diff_master_send"] = ds[:50]
    P("  canonical object graph after ctor+prepareToPlay+enable: Insert vs Master %d differing words, Master vs Send %d" % (len(dm), len(ds)))
    for d in dm[:10]: P("    I/M diff %s" % (d,))
    check(not dm and not ds, "the complete MMF object graph (0x4a0 object + every heap child reachable from it, heap pointers "
                             "canonicalised) is word-identical Insert[3] = Master[5] = Send[5] after construction")
    dI, dM, dS = (res[w]["defaults"] for w in ("insert", "master", "send"))
    model_def = [(i, f2u(F(MM.INSERT_DEFAULTS[i]))) for i in UI_DEFAULT_IDX]
    P("  slot-52/53 slot-14 calls on MMF: Insert %s" % [(i, round(u2f(b), 7)) for i, b in dI])
    P("                                   Master %s; Send %s" % ("== Insert" if dM == dI else dM, "== Insert" if dS == dI else dS))
    check(dI == dM == dS == model_def, "slot-52 (Master/Send) and slot-53 (Insert) MMF defaults are bit-identical to each other and "
                                       "to mmf.INSERT_DEFAULTS (indices 0,1,2,3,5,6,7)")
    vt = [(k, hex(im.u32(MMF_VT + 4 * k))) for k in range(32)]
    J["vtable"] = vt
    P("  MMF vtable 0x8420b8 (32 slots): 14 %s, 18 %s, 22 %s, 25 %s, 26 %s, 27 %s; RTTI name %r" % (
        vt[14][1], vt[18][1], vt[22][1], vt[25][1], vt[26][1], vt[27][1], im.cstr(im.u32(im.u32(MMF_VT - 4) + 4))))
    return res


# ===================================================================================================================== C3/C4 rig
class Model:
    """Per-effect models for all 10 Master/Send slots as H077 builds them, except index 5, which is built independently of the
    emulator: mmf.MMF + mmf.INSERT_DEFAULTS (UI indices), slot 22(0), post-HPF on at 10 Hz, EffectBase mode 0."""
    def __init__(self, which, x, mut=None):
        self.which = which; self.kinds = H77.KINDS; self.ebs = {}; self.mms = {}
        for i, kind in enumerate(self.kinds):
            if i == 5:
                d = [(k, f2u(F(MM.INSERT_DEFAULTS[k]))) for k in UI_DEFAULT_IDX]
                self.ebs[i], self.mms[i] = model_mmf(d, mut)
            else:
                hpf = x.e.rd(x.objs[i] + 0xcc, 1)[0]; a8 = x.e.rd(x.objs[i] + 0xa8, 1)[0]
                self.ebs[i], self.mms[i] = H77.model_effect(kind, x.defaults[i], hpf, a8)
        self.bpm = 120.0
        feed = lambda idx, eb, bpm: self.mms[idx].set_param(7, bpm)
        cls = {"master": FP.MasterProcessor, "send": FP.SendProcessor}[which]
        self.P = cls(self.ebs, tempo=lambda: self.bpm, feed=feed, nine_e=1)
        self.P.set_disabled(0); self.P.log = []

    def set_param(self, i, idx, v): self.mms[i].set_param(idx, v); H77.sync_direct(self.kinds[i], self.ebs[i], self.mms[i])

    def pstate(self): return H77.ModelProc.pstate(self)


def model_mmf(defaults, mut=None):
    mm = MM.MMF()
    for idx, bits in defaults: mm.set_param(idx, u2f(bits))
    if mut == "chorus_mix_law":
        law = lambda mm, after_process: (F(1.0), mm.params[5].get())
    else:
        def law(mm, after_process):
            v = mm.params[5].get(); return F(F(1.0) - v), v
    s25, s26 = H44._adapt(mm, law, "process")
    m = EB.EffectBase(mode=0, slot25=s25, slot26=s26, slot27=lambda eb: mm.reset())
    m.slot22(0); m.set_post_hpf(mut != "no_post_hpf", 10.0)
    return m, mm


class Manager:
    """Stand-in Master/Send parameter manager for the REAL base slot 27 0x11ce58 (layout as harness/H004 C4)."""
    def __init__(self, x):
        e = x.e; self.e = e
        self.ed = ed = e.malloc(0x100); e.wr(ed, b"\0" * 0x100)
        h = e.malloc(0x80); e.wr(h, b"\0" * 0x80); iw = e.malloc(4); e.w32(iw, 0); e.w32(h + 8, iw); e.w32(h + 0x50, 0); e.w32(h + 0xc, ed)
        self.m = m = e.malloc(0x100); e.wr(m, b"\0" * 0x100); e.w32(m, MGR_VT[x.which]); e.w32(m + 0x1c, x.p); e.w32(m + 0x20, h)
        e.wr(m + 0x24, b"\1")

    def s27(self, v, k): self.e.call(BASE_S27, self.m, f2u(v), k)


def run_case(spec):
    """ops {block: [op]}; op: ("p", k, v) slot 14 on index 5; ("s27", k, v) manager; ("fx", n); ("dis", f)."""
    t0 = time.time(); mut = spec.get("mutant")
    restore = None
    if mut == "db2_is_12db":
        restore = MM.kind_of
        MM.kind_of = lambda t, db: (t if db in (1, 2) else t + 3) if t in (0, 1, 2) else 6
    elif mut == "cascade_q_unsqrt":
        restore = MM.Wrapper.configure
        def conf(self, cut_c, q_c, flag):              # alternative: 24 dB stages use Q itself instead of sqrt(Q)
            if not self.stages: return
            for s in self.stages:
                v = s.nyq
                if cut_c <= v: v = cut_c
                fc = MM.MIN_FC
                if fc <= v: fc = v
                s.Q = float(q_c); s.fc = fc; s.coefs(); s.flag48 = flag
        MM.Wrapper.configure = conf
    try:
        return _run_case(spec, t0)
    finally:
        if mut == "db2_is_12db": MM.kind_of = restore
        elif mut == "cascade_q_unsqrt": MM.Wrapper.configure = restore


def _run_case(spec, t0):
    which = spec["proc"]
    x = H77.EmuProc(which); m = Model(which, x, spec.get("mutant")); mg = Manager(x)
    o5 = x.objs[5]
    nblk = spec.get("nblk", 200); ops = spec.get("ops", {})
    L, R = H77.signal(spec["sig"], nblk, seed=spec.get("seed", 5))
    res = dict(name=spec["name"], proc=which, sig=spec["sig"], samples=0, exact=0, maxdiff=0.0, pdiff=0, evdiff=0, wdiff=0, fdiff=0,
               fchecks=0, s27_ok=0, s27_n=0, first=None, wet_blocks=0, mmf_fields=0)
    blob = b""
    for b in range(nblk):
        x.ev = []; x.s14 = []; m.P.log = []
        for op in ops.get(b, []):
            if op[0] == "fx": x.set_fx_type(op[1]); m.P.set_fx_type(op[1])
            elif op[0] == "dis": x.set_disabled(op[1]); m.P.set_disabled(op[1])
            elif op[0] == "p": x.set_param(5, op[1], op[2]); m.set_param(5, op[1], op[2])
            elif op[0] == "s27":
                n0 = len(x.s14); mg.s27(op[2], op[1]); got = [(x.idx_of.get(oo), s32(i), bb) for _, oo, i, bb in x.s14[n0:]]
                tgt = m.P.pend
                res["s27_n"] += 1
                if got == [(tgt, op[1], f2u(F(op[2])))] and x.e.u32(mg.ed + 0x38 + 8 * op[1]) == f2u(F(op[2])): res["s27_ok"] += 1
                elif res["first"] is None: res["first"] = ("s27 block %d" % b, got, tgt)
                if tgt >= 0: m.set_param(tgt, op[1], op[2])
            elif op[0] == "bpm": x.bpm = op[1]; m.bpm = op[1]
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        oL, oR = x.block(xL, xR)
        mL = list(xL); mR = list(xR); m.P.process_block(mL, mR, N)
        blob += pack(oL) + pack(oR)
        if any(f2u(a_) != f2u(c_) for a_, c_ in zip(oL + oR, xL + xR)): res["wet_blocks"] += 1
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(F(b_)): res["exact"] += 1
            else:
                d = abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf")
                res["maxdiff"] = max(res["maxdiff"], d)
                if res["first"] is None: res["first"] = ("out block %d" % b, a_, b_)
        ps_e, ps_m = x.pstate(), m.pstate()
        if ps_e != ps_m:
            res["pdiff"] += 1
            if res["first"] is None: res["first"] = ("pstate block %d" % b, ps_e, ps_m)
        ev_e = [e_ for e_ in x.ev] + [("feed7", x.idx_of[oo], f2u(F(u2f(bb)))) for w, oo, idx, bb in x.s14 if w == "feed" and idx == 7]
        ev_e += [("feed%d" % idx, x.idx_of[oo], bb) for w, oo, idx, bb in x.s14 if w == "feed" and idx != 7]
        ev_m = [l for l in m.P.log if l[0] != "feed7"] + [("feed7", l[1], f2u(l[2])) for l in m.P.log if l[0] == "feed7"]
        if sorted(map(str, ev_e)) != sorted(map(str, ev_m)):
            res["evdiff"] += 1
            if res["first"] is None: res["first"] = ("events block %d" % b, ev_e, ev_m)
        for i in m.ebs:
            dd = H44.sdiff(H44.emu_state(x.e, x.objs[i]), H44.model_state(m.ebs[i]))
            if dd:
                res["wdiff"] += 1
                if res["first"] is None: res["first"] = ("wrapper %d block %d" % (i, b), dd[:3])
                break
        if b % 10 == 9 or b == nblk - 1:
            ev, mv, _ = H76.dump_pair("mmf", x.e, o5, m.mms[5])
            res["fchecks"] += 1; res["mmf_fields"] = len(ev)
            dd = H76.ddiff(ev, mv)
            if dd:
                res["fdiff"] += 1
                if res["first"] is None: res["first"] = ("mmf fields block %d" % b, dd[:5])
            if b == nblk - 1: res["final_fields_sha"] = sha(json.dumps(sorted(ev.items())).encode())[:16]
    res["sha"] = sha(blob)[:16]
    res["ok"] = (res["exact"] == res["samples"] and not res["pdiff"] and not res["evdiff"] and not res["wdiff"] and not res["fdiff"]
                 and res["s27_ok"] == res["s27_n"])
    res["secs"] = round(time.time() - t0, 1)
    return res, blob


# ===================================================================================================================== cases
def P_(**kw):
    """Parameter dict by name -> slot-14 ops."""
    names = dict(cut=0, gain=1, q=2, glide=3, mix=5, ft=6, db=7)
    return [("p", names[k], float(v)) for k, v in kw.items()]


UI = [  # (name, block-0 slot-14 ops (before setFxType), mid-run ops {block: ops}, uses s27)
    ("lp12_c30_q60", P_(ft=0, db=1, cut=0.30, q=0.60), {}),
    ("lp24_c70_q20", P_(ft=0, db=2, cut=0.70, q=0.20), {}),
    ("hp12_c60_q90", P_(ft=1, db=1, cut=0.60, q=0.90), {}),
    ("hp24_c40_q50", P_(ft=1, db=2, cut=0.40, q=0.50), {}),
    ("bp12_c50_q100", P_(ft=2, db=1, cut=0.50, q=1.0), {}),
    ("bp24_c55_q80", P_(ft=2, db=2, cut=0.55, q=0.80), {}),
    ("off12_gain80_mix50", P_(ft=6, db=1, gain=0.80, mix=0.50), {}),
    ("off24_gain30", P_(ft=6, db=2, gain=0.30), {}),
    ("lp12_cut0_q1_extreme", P_(ft=0, db=1, cut=0.0, q=1.0), {}),
    ("hp24_cut1_q0_extreme", P_(ft=1, db=2, cut=1.0, q=0.0), {}),
    ("bp12_mix0", P_(ft=2, db=1, cut=0.2, mix=0.0), {}),
    ("lp24_gain0_cut50", P_(ft=0, db=2, gain=0.0, cut=0.5), {}),
    ("hp12_gain1_glide1", P_(ft=1, db=1, gain=1.0, cut=0.8, q=0.3, glide=1.0), {}),
    ("bp24_cut1_q1_glide50_mix70", P_(ft=2, db=2, cut=1.0, q=1.0, glide=0.5, mix=0.7), {}),
    ("midrun_changes", P_(ft=0, db=1, cut=0.1, glide=0.5),
     {60: P_(cut=0.9), 100: P_(ft=1, db=2), 140: P_(ft=2, db=1, q=0.9), 170: P_(mix=0.3, gain=0.9), 185: P_(ft=6)}),
    ("s27_manager_route", P_(ft=0, db=2),
     {1: [("s27", 0, 0.25), ("s27", 2, 0.75), ("s27", 5, 0.6), ("s27", 1, 0.4), ("s27", 3, 0.3)], 80: [("s27", 0, 0.85)],
      130: [("s27", 5, 0.2), ("s27", 2, 0.1)]}),
    ("onoff_type_switch", P_(ft=1, db=1, cut=0.7, q=0.4),
     {60: [("fx", -1)], 80: [("fx", 5)], 90: P_(cut=0.2), 120: [("fx", 2)], 150: [("fx", 5)], 170: [("dis", 1)], 180: [("dis", 0)]}),
]

BEYOND = [  # not UI-reachable (F171): FILTERTYPE names "...24" -> 3/4/5, FilterOrder1 -> FILTERDB 0, and out-of-range choices
    ("ft3_LowPass24_db1", P_(ft=3, db=1, cut=0.4), {}),
    ("ft4_HighPass24_db1", P_(ft=4, db=1, cut=0.4), {}),
    ("ft5_BandPass24_db2", P_(ft=5, db=2, cut=0.4), {}),
    ("ft7_out_of_range", P_(ft=7, db=1, cut=0.4), {}),
    ("ftm1_negative", P_(ft=-1, db=1, cut=0.4), {}),
    ("lp_db0_Order1", P_(ft=0, db=0, cut=0.4, q=0.6), {}),
    ("bp_db0_Order1", P_(ft=2, db=0, cut=0.6, q=0.6), {}),
    ("hp_db3_out_of_range", P_(ft=1, db=3, cut=0.5, q=0.5), {}),
    ("ft2.7_truncation", P_(ft=2.7, db=1.9, cut=0.5, q=0.5), {}),
    ("REF_UI_ft6_Off_db1", P_(ft=6, db=1, cut=0.4), {}),            # UI-reachable references for the derived equalities
    ("REF_UI_lp_db2_Order4", P_(ft=0, db=2, cut=0.4, q=0.6), {}),
    ("REF_UI_bp_db2_Order4", P_(ft=2, db=2, cut=0.6, q=0.6), {}),
    ("REF_UI_hp_db2_Order4", P_(ft=1, db=2, cut=0.5, q=0.5), {}),
    ("REF_UI_bp_db1_Order2", P_(ft=2, db=1, cut=0.5, q=0.5), {}),
]


def mk(name, proc, sig, pre, mid, section, mutant=None, nblk=200):
    ops = {0: list(pre) + [("fx", 5)]}
    for b, v in mid.items(): ops.setdefault(b, []).extend(v)
    return dict(name="%s_%s_%s%s" % (proc, name, sig, "" if not mutant else "_MUT_" + mutant), proc=proc, sig=sig, ops=ops,
                section=section, mutant=mutant, nblk=nblk)


def all_cases():
    cs = []
    for proc in ("master", "send"):
        for name, pre, mid in UI:
            for sig in ("noise", "sine", "impulse"): cs.append(mk(name, proc, sig, pre, mid, "c3"))
    for proc in ("master", "send"):
        for sig in ("noise", "sine", "impulse"): cs.append(mk("processor_defaults", proc, sig, (), {}, "ref"))
    for name, pre, mid in BEYOND:
        for sig in ("noise", "sine"): cs.append(mk(name, "master", sig, pre, mid, "c4"))
    U = {n: (p, m) for n, p, m in UI}
    for mut, nm, sig in (("no_post_hpf", "bp12_c50_q100", "noise"), ("db2_is_12db", "lp24_c70_q20", "noise"),
                         ("chorus_mix_law", "off12_gain80_mix50", "sine"), ("cascade_q_unsqrt", "bp24_c55_q80", "noise")):
        cs.append(mk(nm, "master", sig, U[nm][0], U[nm][1], "c5", mutant=mut))
    return cs


def _worker(spec):
    try:
        r, blob = run_case(spec)
    except Exception as ex:
        import traceback
        r = dict(name=spec["name"], ok=False, error="%s: %s" % (type(ex).__name__, ex), tb=traceback.format_exc()[-1500:]); blob = b""
    r["section"] = spec["section"]; r["mutant"] = spec.get("mutant")
    return r, blob


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H027"))
    ap.add_argument("--jobs", type=int, default=6); ap.add_argument("--only", help="comma list of c1,c3,c4,c5")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else {"c1", "c3", "c4", "c5"}
    if "c3" in only: only.add("ref")
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = Image()
    P("target sha256 %s (asserted by sp16img)" % sha(im.data))
    if "c1" in only:
        P("== C1 static: MMF construction in the processor ctors (capstone)")
        static_part(im, P, check, J)
        P("\n== C1/C2 dynamic: REAL processor ctors, calls on the MMF object, object graph, defaults, vptr")
        dyn_part(im, P, check, J)
    jobs = [c for c in all_cases() if c["section"] in only]
    if jobs:
        P("\n== running %d emulation cases with %d jobs" % (len(jobs), a.jobs))
        t0 = time.time()
        if a.jobs > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.jobs) as pool: results = pool.map(_worker, jobs, chunksize=1)
        else:
            results = [_worker(s) for s in jobs]
        print("  done in %.0f s (timing not written to the report, so reports are reproducible)" % (time.time() - t0), flush=True)
        for sec, title in (("c3", "C3 non-default settings in the REAL Master/Send processors vs fx_processors + effectbase + mmf.py"),
                           ("c4", "C4 Master, settings NOT UI-reachable (F171)"),
                           ("c5", "C5 alternative models (each must FAIL)")):
            rows = [(r, b) for r, b in results if r["section"] == sec]
            if not rows: continue
            P("\n== " + title)
            for r, b in rows:
                if "error" in r: P("  %-52s ERROR %s" % (r["name"], r["error"][:300])); continue
                P("  %-52s %s exact %6d/%6d maxdiff %.3g p/ev/wr/fld diffs %d/%d/%d/%d (fld checks %d x %d fields) s27 %d/%d wet %3d sha %s%s" % (
                    r["name"], "OK " if r["ok"] else "BAD", r["exact"], r["samples"], r["maxdiff"], r["pdiff"], r["evdiff"], r["wdiff"],
                    r["fdiff"], r["fchecks"], r["mmf_fields"], r["s27_ok"], r["s27_n"], r["wet_blocks"], r["sha"],
                    "" if r["ok"] or sec == "c5" else "  first %s" % (str(r["first"])[:300],)))
            if sec != "c5":
                blob = b"".join(b for _, b in rows)
                open(os.path.join(a.out, "%s_outputs.f32" % sec), "wb").write(blob)
                nok = sum(1 for r, _ in rows if r.get("ok"))
                P("  %s: %d/%d cases bit-exact, %d samples, outputs sha256 %s" % (sec, nok, len(rows), sum(r.get("samples", 0) for r, _ in rows), sha(blob)))
                check(nok == len(rows), "%s: every case bit-exact (outputs, processor state, events, wrapper state of all 10 effects every "
                                        "block; MMF field-level state every 10 blocks and at the end; s27 routing)" % sec)
                if sec == "c3":
                    ref = {(r["proc"], r["sig"]): r["sha"] for r, _ in results if r["section"] == "ref" and "error" not in r}
                    refok = all(r.get("ok") for r, _ in results if r["section"] == "ref")
                    same_def = [r["name"] for r, _ in rows if ref.get((r["proc"], r["sig"])) == r["sha"]]
                    P("  reference runs at processor defaults (6, also bit-exact: %s); C3 cases whose output equals the default output: %s" % (
                        refok, same_def))
                    check(refok and not same_def, "every C3 setting changes the output relative to the processor-default run")
                    for proc in ("master", "send"):
                        for sig in ("noise", "sine", "impulse"):
                            sh = [r["sha"] for r, _ in rows if r["proc"] == proc and r["sig"] == sig and "error" not in r]
                            P("  %s/%s: %d settings -> %d distinct outputs" % (proc, sig, len(sh), len(set(sh))))
                    ms = {(r["name"].replace("master_", "", 1)): r["sha"] for r, _ in rows if r["proc"] == "master"}
                    ss = {(r["name"].replace("send_", "", 1)): r["sha"] for r, _ in rows if r["proc"] == "send"}
                    same = sum(1 for k in ms if ss.get(k) == ms[k])
                    P("  Master vs Send outputs identical for %d/%d (setting, signal) pairs" % (same, len(ms)))
                    J["c3_master_send_same"] = [same, len(ms)]
                if sec == "c4":
                    d = {r["name"]: r["sha"] for r, _ in rows}
                    eq = {}
                    for sig in ("noise", "sine"):
                        g = lambda n: d["master_%s_%s" % (n, sig)]
                        eq[sig] = dict(
                            off=len({g(n) for n in ("ft3_LowPass24_db1", "ft4_HighPass24_db1", "ft5_BandPass24_db2", "ft7_out_of_range",
                                                    "ftm1_negative", "REF_UI_ft6_Off_db1")}) == 1,
                            order1_eq_order4=g("lp_db0_Order1") == g("REF_UI_lp_db2_Order4") and g("bp_db0_Order1") == g("REF_UI_bp_db2_Order4"),
                            db3_eq_order4=g("hp_db3_out_of_range") == g("REF_UI_hp_db2_Order4"),
                            trunc_2p7_1p9_eq_bp_order2=g("ft2.7_truncation") == g("REF_UI_bp_db1_Order2"))
                        P("  derived (%s): FILTERTYPE 3/4/5/7/-1 == UI Off (6): %s; FILTERDB 0 (FilterOrder1) == Order4 (2): %s; "
                          "FILTERDB 3 == Order4: %s; FILTERTYPE 2.7 / FILTERDB 1.9 == BPF Order2 (truncation): %s" % (
                              sig, eq[sig]["off"], eq[sig]["order1_eq_order4"], eq[sig]["db3_eq_order4"], eq[sig]["trunc_2p7_1p9_eq_bp_order2"]))
                    J["c4_derived"] = eq
                    check(all(all(v.values()) for v in eq.values()), "C4 derived equalities hold (non-UI values collapse onto UI kinds)")
            else:
                check(all(not r.get("ok") for r, _ in rows) and all("error" not in r for r, _ in rows),
                      "every alternative model is refuted by the real Master processor")
            J[sec] = [{k: v for k, v in r.items() if k != "secs"} for r, _ in rows]
    J["fails"] = fails
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h027_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h027.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
