#!/usr/bin/env python3
"""H079 round 2 (cycle 034): forward type propagation of the three FX parameter-manager pointers (own code, static only).

Question: can any 1.60 code reach the +0x9d setter 0x1129bc through a manager pointer (primary vt+0xb8 = slot 46 thunk 0x11caf4,
vt+0xbc = slot 47 reader 0x11cae0) or through its IEffector sub-object (manager+0x14: vt+0x60 / vt+0x64 = adjustors 0x11caec /
0x11cad8)?  The thunks occur only in those vtable slots (word scan in H079_fx_onoff.py), so these are the only entries.

Method
 1. Allocation sites: the code that materialises the Insert / Master / Send manager vtables (const_sites) gives the ctors; their
    direct callers are the allocation sites. The instructions after each `new`+ctor are asserted and the stores of the new
    pointer (and of pointer+k) are listed: these are the holder fields.
 2. Getters: every out-of-line function returning a holder field (found from the holders' classes) and their vtable slots.
 3. Strong forward propagation (interprocedural, worklist): harness/lib/armflow.Flow extended with typed tags
      O:T_MFU / O:T_SFU / O:T_TU / O:T_HTAS / O:T_Z (holder objects), O:MGRARR (array of manager pointers), O:MGR (manager),
      P:MGR+0x14 (IEffector), Q:x (interior pointer from a register add).
    Seeds: holder-class vtable methods (this = holder), adjustor-thunk targets, direct getter callers, every function containing a
    root (0x32b664) route call. Rules: [T_MFU+0x80], [T_SFU+0x88] -> MGR; [T_TU+0xe8], [T_HTAS+0x65c] -> MGRARR; [T_HTAS+0x608] ->
    T_MFU; [T_HTAS+0x604] -> T_SFU; [T_HTAS+0x598] -> T_Z; [T_Z+0x1d0] -> T_Y; any load from T_Y / Q:T_Y -> MGR; any load from
    MGRARR / Q:MGRARR -> MGR; getter calls and getter vcall slots -> MGR / IE. Tags flow through registers, the stack frame,
    bl arguments (r0-r3, [sp], [sp+4]) into callees, and through return values into every direct caller.
    Sinks: vcall with receiver MGR at vt+0xb8/+0xbc, or IE at vt+0x60/+0x64. Also recorded: stores of MGR/IE/MGRARR to memory (copies),
    MGR/IE passed to indirect calls.
 4. Weak, type-free net (intra-procedural, every function that contains a candidate vcall): any load at +0x80/+0x88 (any base) -> WMGR,
    any element of [x+0xe8] / [x+0x65c] / [x+0x1d0] -> WMGR, any vcall result at a getter slot offset (0x24, 0xd8, 0x178, 0x17c, 0x70,
    0x74, 0x90) -> WIE. Every weak sink is listed for a by-hand base-type check.
Limits: path-insensitive; no alias analysis; ARM mode only (no Thumb code calls into these entries, H079 round 1 + critic).
"""
import argparse, bisect, hashlib, json, os, re, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib"))
from sp16img import Image, const_sites                          # noqa: E402
import armflow                                                 # noqa: E402
from armflow import Flow, State, refined_starts, nreg, _imm    # noqa: E402

SINK_MGR = (0xb8, 0xbc); SINK_IE = (0x60, 0x64)
GET_MGR = {0x1b1e58: "MasterFxUnit::getManager [+0x80]", 0x1b3564: "SendFxUnit::getManager [+0x88]"}
GET_IE = {0x1c7890: "TrackUnit getInsertIEffector(i) [+0xe8][i]+0x14", 0x1c7888: "  (adjustor -0x80)",
          0x1b94f0: "HTAS master IEffector [[+0x608]+0x80]+0x14", 0x1b94e8: "  (adjustor -0x200)",
          0x1b9510: "HTAS send IEffector [[+0x604]+0x88]+0x14", 0x1b9508: "  (adjustor -0x200)"}
# typed getter vcall slots: (receiver tag, vt offset) -> IE
VSLOT_IE = {("T_TU", 0xd8), ("T_TU+0x80", 0x24), ("T_HTAS", 0x178), ("T_HTAS", 0x17c), ("T_HTAS+0x200", 0x70), ("T_HTAS+0x200", 0x74),
            ("R", 0x70), ("R", 0x74), ("R", 0x90), ("R.0x10", 0x24)}
WEAK_SLOTS = (0x24, 0xd8, 0x178, 0x17c, 0x70, 0x74, 0x90)
FIELD = {("T_MFU", 0x80): "O:MGR", ("T_SFU", 0x88): "O:MGR", ("T_TU", 0xe8): "O:MGRARR", ("T_HTAS", 0x65c): "O:MGRARR",
         ("T_HTAS", 0x620): "O:TUARR", ("T_HTAS", 0x608): "O:T_MFU", ("T_HTAS", 0x604): "O:T_SFU", ("T_HTAS", 0x598): "O:T_Z", ("T_Z", 0x1d0): "O:T_Y"}
VT = {"T_MFU": [(0x862978, 46)], "T_SFU": [(0x862e28, 46)], "T_HTAS": [(0x863da0, 110), (0x863f60, 3), (0x863f74, 57), (0x864060, 6),
      (0x864080, 3)], "T_TU": [(0x864cac, 103), (0x864e50, 23), (0x864eb4, 13), (0x864ef4, 6), (0x864f18, 24), (0x864f80, 8),
      (0x864fa8, 3), (0x864fbc, 4), (0x864fd4, 2)],
      # the managers themselves (FxParameterManagerBase, Master, Insert, Send): primary 48+ slots, IEffector sub-vtable 27 slots
      "MGR": []}   # filled by mgr_groups(): every sub-vtable of FxParameterManagerBase / Master / Insert / Send + 3 construction groups
MGR_PRIM = (0x8430cc, 0x8437ec, 0x84407c, 0x8446d4, 0x843b4c, 0x8443e4, 0x844a34)
MGR_SUB = {}   # sub-object offset -> [vtable address points]


def mgr_groups(im):
    """Sub-vtables of each manager vtable group: same typeinfo pointer at vt-4, offset-to-top 0 / -k. Size = up to the next group
    entry (minus its 8-byte header), the last one up to the first non-code word."""
    out = []
    for prim in MGR_PRIM:
        ti0 = im.u32(prim - 4); g = []
        for a_ in range(prim - 8, prim + 0x400, 4):
            if im.u32(a_ + 4) == ti0 and (im.u32(a_) == 0 or im.u32(a_) >= 0xffffff00):
                g.append((a_ + 8, (1 << 32) - im.u32(a_) if im.u32(a_) else 0))
        for n_, (vt, k) in enumerate(g):
            if n_ + 1 < len(g): sz = (g[n_ + 1][0] - 8 - vt) // 4
            else:
                sz = 0
                while 0x8000 <= (im.u32(vt + 4 * sz) or 0) < 0x800000: sz += 1
            out.append((vt, sz, k)); MGR_SUB.setdefault(k, []).append(vt)
    return out
MGRTAGS = ("O:MGR", "P:MGR+0x14", "O:MGRARR")


def sha(b): return hashlib.sha256(b).hexdigest()


class TFlow(Flow):
    """armflow.Flow + typed holder/manager tags (strong) or type-free weak tags."""

    def __init__(self, im, weak=False, woffs=(0x80, 0x88)):
        super().__init__(im); self.weak = weak; self.woffs = woffs; self.rets = set(); self.extra = []; self.rettags = {}

    def analyse_seeded(self, start, end, seeds):
        self.rets = set(); self.extra = []
        init = State({'r%d' % k: frozenset(['ARG:r%d' % k]) for k in range(4)})
        for k, v in seeds.items():
            if k.startswith('r'): init.reg[k] = frozenset(set(init.reg.get(k, frozenset())) | set(v))
            else: init.stk[int(k[3:])] = frozenset(v)
        ins = self.im.disasm(start, end)
        idx = {i.address: n for n, i in enumerate(ins)}
        states = {start: init}; work = [start]; events = {}; it = 0
        while work and it < 60 * len(ins):
            it += 1; a = work.pop()
            if a not in idx: continue
            i = ins[idx[a]]; st = states[a].copy()
            succ, _ = self._step2(i, st, start, end, events)
            for sa, ss in succ:
                if sa not in idx: continue
                if sa not in states: states[sa] = ss.copy(); work.append(sa)
                elif states[sa].merge(ss): work.append(sa)
        return sorted(events.values(), key=lambda e: (e['site'], e['kind']))

    def _step2(self, i, st, fs, fe, events):
        m, op = i.mnemonic, i.op_str
        w = int.from_bytes(i.bytes, 'little')
        if (w == 0xe12fff1e) or (m.startswith('pop') and 'pc' in op and (w >> 28) == 0xe) or w == 0xe49df004:
            self.rets |= set(st.g('r0'))
        ops = [x.strip() for x in re.split(r',(?![^\[]*\])(?![^{]*\})', op)] if op else []
        pre = None
        base = m[:-2] if (w >> 28) not in (0xe, 0xf) and len(m) > 2 else m
        # register add: interior pointer
        if base in ('add', 'adds') and len(ops) >= 3 and not ops[2].startswith('#') and nreg(ops[0]) in armflow.REGS:
            src = set(st.g(ops[1])) | set(st.g(ops[2].split()[0]))
            pre = ('reg', nreg(ops[0]), {('Q:' + t[2:]) if t.startswith('O:') else t for t in src
                                         if t.startswith('O:T_Y') or t.startswith('O:MGRARR') or t.startswith('O:TUARR') or t.startswith('Q:') or t.startswith('O:WARR')})
        elif base in ('ldr',) and len(ops) >= 2:
            mm = re.match(r'\[(\w+)(?:,\s*([^\]]+))?\](!?)', ops[1])
            if mm and nreg(mm.group(1)) not in ('pc', 'sp'):
                bt = set(st.g(mm.group(1))); offs = mm.group(2); off = _imm(offs) if offs and offs.startswith('#') else None
                add = set()
                for t in bt:
                    nm = t[2:] if t.startswith('O:') or t.startswith('P:') else None
                    if t in ('O:MGRARR', 'Q:MGRARR', 'O:T_Y', 'Q:T_Y'): add.add('O:MGR')
                    if t in ('O:WARR', 'Q:WARR'): add.add('O:WMGR')
                    if t in ('O:TUARR', 'Q:TUARR'): add.add('O:T_TU')
                    if nm and off is not None and (nm, off) in FIELD: add.add(FIELD[(nm, off)])
                    if t.startswith('P:T_') and off is not None and nm.count('+') == 1:
                        b_, k_ = nm.split('+', 1); k_ = int(k_, 16)
                        if (b_, off + k_) in FIELD: add.add(FIELD[(b_, off + k_)])
                if self.weak and off is not None:
                    if off in self.woffs: add.add('O:WMGR')
                    if off in (0xe8, 0x65c, 0x1d0): add.add('O:WARR')
                pre = ('ldr', nreg(ops[0]), add) if add else None
        succ_ = None
        old_tags = set(st.g(ops[0])) if ops and nreg(ops[0]) in armflow.REGS else set()
        mb = re.match(r'\[(\w+)', ops[1]) if len(ops) > 1 else None
        old_base = set(st.g(mb.group(1))) if mb and nreg(mb.group(1)) in armflow.REGS else set()
        succ, out = self._step(i, st, fs, fe, events)
        if pre:
            for _, s2 in succ:
                cur = set(s2.g(pre[1]))
                s2.s(pre[1], (cur | pre[2]) if pre[0] == 'ldr' else (pre[2] | {t for t in cur}))
        # calls: getter returns
        if base in ('bl', 'blx') and ops and ops[0].startswith('#'):
            t = _imm(ops[0])
            if t in GET_MGR or t in GET_IE:
                for _, s2 in succ: s2.s('r0', {'O:MGR'} if t in GET_MGR else {'P:MGR+0x14'})
            elif t in self.rettags:
                for _, s2 in succ: s2.s('r0', set(s2.g('r0')) | set(self.rettags[t]))
        elif base == 'blx' and ops and not ops[0].startswith('#'):
            res = set()
            for _, s2 in succ:
                for t in list(s2.g('r0')):
                    if t.startswith('O:') and '.' in t:
                        obj, o = t[2:].rsplit('.', 1); o = int(o, 0)
                        if (obj, o) in VSLOT_IE or any(obj.startswith(x + '.') for x in ('R.0x10',)) and o == 0x24 and obj == 'R.0x10':
                            res.add('P:MGR+0x14')
                        if self.weak and o in WEAK_SLOTS: res.add('P:WMGR+0x14')
                if res: s2.s('r0', set(s2.g('r0')) | res)
        # stores of manager tags (copies)
        if base in ('str',) and len(ops) >= 2 and nreg(ops[0]) in armflow.REGS:
            v = {t for t in old_tags if t in MGRTAGS or t in ('O:T_MFU', 'O:T_SFU', 'O:T_TU', 'O:TUARR')}
            mm = re.match(r'\[(\w+)(?:,\s*([^\]]+))?\](!?)', ops[1])
            if v and mm and nreg(mm.group(1)) != 'sp' and not any(t.startswith('SP:') for t in old_base):
                self.extra.append(dict(site=i.address, val=sorted(v), base=sorted(old_base)[:4], off=mm.group(2)))
        if ops and nreg(ops[0]) in armflow.REGS:
            for _, s2 in succ:
                tg = s2.g(ops[0])
                if any(fold(t) != t for t in tg):
                    s2.s(ops[0], {fold(t) for t in tg})
        return succ, out


def my_starts(im):
    """Function starts: .ARM.exidx ∪ direct bl/blx targets ∪ aligned code pointers in .rodata/.data/.init_array (vtables,
    callback tables) ∪ `push`/`stmdb sp!` right after an unconditional terminator. (armflow.refined_starts also splits at every
    `push {..lr}`, which cuts shrink-wrapped preambles such as `ldr r0,[r0,#0x84]` at 0x1b1e60 off their function.)"""
    lo, hi = im.sec['.text']
    s = set(x for x in im.starts() if lo <= x < hi)
    s |= {t for _, t, k in im.direct_calls() if k in ('bl', 'blx') and lo <= t < hi and t % 4 == 0}
    for sec in ('.rodata', '.data', '.init_array'):
        a_, b_ = im.sec[sec]; o_ = im.off(a_); n_ = (b_ - a_) // 4
        for w_ in struct.unpack_from('<%dI' % n_, im.data, o_):
            if lo <= w_ < hi and w_ % 4 == 0: s.add(w_)
    o = im.off(lo); W = struct.unpack_from('<%dI' % ((hi - lo) // 4), im.data, o); prev = False
    for k, w in enumerate(W):
        if prev and ((w & 0xffff0000) == 0xe92d0000 or (w & 0xffff0fff) == 0xe52d0004): s.add(lo + 4 * k)
        prev = (w == 0xe12fff1e) or ((w & 0xffff8000) == 0xe8bd8000) or ((w & 0x0f000000) == 0x0a000000 and (w >> 28) == 0xe) or w == 0xe49df004
    return sorted(s)


def fold(t):
    if not (t.startswith('P:MGR+') and t.count('+') > 1 and re.match(r'^(\+0x[0-9a-f]+)+$', t[5:])): return t
    k = sum(int(x, 16) for x in t[6:].split('+')) & 0xffffffff
    return 'O:MGR' if k == 0 else 'P:MGR+0x%x' % k


def holder_methods(im):
    """{fn: tag} for holder-class vtable entries; adjustor thunks `sub r0,r0,#k; b T` seed T with this."""
    seeds = {}
    if not VT["MGR"]: VT["MGR"] = [(vt, sz) for vt, sz, k in mgr_groups(im)]
    for tag, vts in VT.items():
        for vt, n in vts:
            adj = -s32(im.u32(vt - 8))
            for k in range(n):
                f = im.u32(vt + 4 * k)
                if not f or not (0x8000 <= f < 0x800000): continue
                ins = im.disasm(f, f + 8)
                if len(ins) == 2 and ins[0].mnemonic == 'sub' and ins[0].op_str.startswith('r0, r0, #') and ins[1].mnemonic == 'b':
                    seeds.setdefault(_imm(ins[1].op_str), set()).add('O:' + tag)
                elif adj == 0:
                    seeds.setdefault(f, set()).add('O:' + tag)
                elif tag == 'MGR':
                    seeds.setdefault(f, set()).add('P:MGR+0x%x' % adj)
                else:
                    seeds.setdefault(f, set()).add('P:%s+0x%x' % (tag, adj))
    return seeds


def s32(u): return u - (1 << 32) if u & 0x80000000 else u


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H079", "r2"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = Image(); L = []; J = {}; nfail = [0]
    def P(s=""): print(s); L.append(s)
    def check(c, s):
        P(("  PASS " if c else "  FAIL ") + s)
        if not c: nfail[0] += 1
    t0 = time.time()
    P("H079 round 2: forward propagation of manager pointers. target sha256 %s" % sha(im.data))
    # ---------------------------------------------------------------- 1. allocation sites
    P("\n[1] manager ctors and allocation sites")
    VTS = {"Insert": 0x84407c, "Master": 0x8437ec, "Send": 0x8446d4}
    cs = const_sites(im, VTS.values()); dc = im.direct_calls(); alloc = {}
    for nm, v in VTS.items():
        fns = sorted(set(im.func_of(s)[0] for _, s in cs[v]))
        callers = {f: [(s, k) for s, t, k in dc if t == f] for f in fns}
        ctor = [f for f, c in callers.items() if any(k == 'bl' for _, k in c)]
        sites = [s for f in ctor for s, k in callers[f] if k == 'bl']
        alloc[nm] = dict(vt=hex(v), fns=[hex(f) for f in fns], ctor=[hex(f) for f in ctor], sites=[hex(s) for s in sites],
                         others={hex(f): [(hex(s), k) for s, k in c] for f, c in callers.items() if f not in ctor})
        P("  %-6s vt %s materialised in %s; ctor %s, only bl call site(s) %s (other functions reached only by in-class thunk "
          "branches)" % (nm, hex(v), alloc[nm]["fns"], alloc[nm]["ctor"], alloc[nm]["sites"]))
    check(alloc["Insert"]["sites"] == ["0x1bbda0"] and alloc["Master"]["sites"] == ["0x1b1dcc"] and alloc["Send"]["sites"] == ["0x1b3434"],
          "exactly one allocation site per manager class: Insert 0x1bbda0 (in 0x1bacec, TrackUnit factory), Master 0x1b1dcc (in 0x1b1d30, "
          "MasterFxUnit ctor), Send 0x1b3434 (in 0x1b3314, SendFxUnit ctor)")
    # the stores after each site (asserted instruction text)
    def seq(a0, a1): return ["%s %s" % (i.mnemonic, i.op_str) for i in im.disasm(a0, a1)]
    exp = {
        "Master": (0x1b1db8, 0x1b1de4, ["mov r0, #0x40", "bl #0x102e8", "mov r1, r7", "mov r2, r5", "mov r6, r0", "bl #0x1260f0",
                   "ldr r0, [r4, #0x80]", "cmp r6, r0", "beq #0x1b1df4", "cmp r0, #0", "str r6, [r4, #0x80]"]),
        "Send": (0x1b3420, 0x1b344c, ["mov r0, #0x40", "bl #0x102e8", "mov r1, r8", "mov r2, r5", "mov r6, r0", "bl #0x130bd4",
                 "ldr r0, [r4, #0x88]", "cmp r6, r0", "beq #0x1b345c", "cmp r0, #0", "str r6, [r4, #0x88]"]),
    }
    for nm, (a0, a1, e) in exp.items():
        check(seq(a0, a1) == e, "%s: new(0x40) -> ctor -> sole store `str r6,[r4,#0x%x]` (ScopedPointer replace); r6 is then dead "
              "(function epilogue / reused by next new)" % (nm, 0x80 if nm == "Master" else 0x88))
    ins_txt = seq(0x1bbd84, 0x1bc070)
    want = ["mov r5, r0", "bl #0x12864c", "add sl, r5, #0xc", "add sl, r5, #0x10", "add r2, r5, #0x14", "bl #0x1c9874",
            "str r5, [r0, sl, lsl #2]", "addne r1, r5, #8", "str r5, [sl, #4]!", "add r5, r5, #4"]
    pos = [ins_txt.index(x) if x in ins_txt else -1 for x in want]
    check(all(p >= 0 for p in pos) and pos == sorted(pos),
          "Insert: r5 = manager; uses in order: +0xc and +0x10 appended to two listener arrays ([[sys+0x590]+0x9c]+0x24, "
          "[[sys+0x590]+0xa0]+0x2c), +0x14 (IEffector) -> 0x1c9874(TU, slot, IE, proc), r5 stored to [sys+0x65c][n], r5 stored "
          "pre-indexed into [[sys+0x598]+0x1d0] + 0xc4 + 8*track + 4*slot, +8 -> [sp+0x28]->vt+0x44, +4 -> [[sys+0x598]+0x8c]->vt+0x38")
    t9874 = seq(0x1c9874, 0x1c98bc)
    check("bl #0x110ec" in t9874 and "str r7, [r3, r5, lsl #2]" in t9874 and "ldr r3, [r4, #0xe8]" in t9874 and
          im.u32(0x1c9894 + 8 + 0x198) == 0x842f64 and im.u32(0x1c9898 + 8 + 0x198) == 0x844334,
          "0x1c9874: __dynamic_cast(IE, 0x842f64, 0x844334, 0x14) -> TrackUnit+0xe8[slot] = manager (offset-0 pointer); proc -> +0xf4[]")
    ti_names = {hex(t): im.cstr(im.u32(t + 4), 60) for t in (0x842f64, 0x844334)}
    P("    typeinfo names: %s" % ti_names)
    ins_after = seq(0x1bc070, 0x1bc0e0)
    check([x for x in ins_after if re.search(r"\br5\b", x) and x.startswith("str")] == ["strne r5, [ip]"],
          "Insert: after 0x1bc060 (r5 = manager+4) the only store of r5 is `strne r5,[ip]` 0x1bc0d8: manager+4 appended to the "
          "listener array [[sys+0x598]+0x90] (sub-object +4, not a manager / IEffector pointer)")
    # sub-objects +4/+8/+0xc/+0x10 have their own vtables: the thunks are not in them
    J["alloc"] = alloc
    P("  holders: MasterFxUnit+0x80, SendFxUnit+0x88, TrackUnit+0xe8[slot], HexaTrackAudioSystem+0x65c[n], Z+0x1d0 table "
      "(Z = [sys+0x598], sequencer-side object, ctor 0x19484c; Y = new(0x284) struct, ctor 0x1995b4, no vtable)")
    # ---------------------------------------------------------------- 2. getters
    P("\n[2] getters (out-of-line) and their entries")
    g = {}
    for f, d in list(GET_MGR.items()) + list(GET_IE.items()):
        dd = [(hex(s), k) for s, t, k in dc if t == f]
        g[hex(f)] = dict(desc=d, body=seq(f, f + 8), direct=dd)
        P("  %s %-46s direct %d" % (hex(f), d, len(dd)))
    J["getters"] = g
    # ---------------------------------------------------------------- 3. strong propagation
    P("\n[3] strong typed propagation")
    st = my_starts(im)
    MRANGE = (0x11c000, 0x132000)    # manager code (FxParameterManagerBase / Master / Insert / Send .cpp), as in round 1
    def fend(f): return st[bisect.bisect_right(st, f)]
    seeds = {f: {'r0': set(v)} for f, v in holder_methods(im).items()}
    getter_callers = set(im.func_of(s)[0] and st[bisect.bisect_right(st, s) - 1] for s, t, k in dc if t in GET_MGR or t in GET_IE)
    root_callers = set(st[bisect.bisect_right(st, s) - 1] for s, t, k in dc if t == armflow.ROOT_GETTER)
    for f in getter_callers | root_callers: seeds.setdefault(f, {})
    mrange = [f for f in st if MRANGE[0] <= f < MRANGE[1]]
    for f in mrange: seeds.setdefault(f, {}).setdefault('r0', set()).add('O:MGR')   # over-approximation: this = manager
    P("  seeds: %d holder-class methods/thunk targets, %d getter callers, %d root-getter callers, %d functions in manager code %s "
      "with this = manager (over-approximation)" % (len(holder_methods(im)), len(getter_callers), len(root_callers), len(mrange),
                                                     [hex(x) for x in MRANGE]))
    callers_of = {}
    for s, t, k in dc:
        if k in ('bl', 'blx'): callers_of.setdefault(t, set()).add(st[bisect.bisect_right(st, s) - 1])
    fl = TFlow(im); done = {}; work = sorted(seeds); sinks = []; copies = []; vargs = []; rets = {}; nan = 0; dispatched = set(); vcount = {}; ctrl_setfx = set()
    INTEREST = lambda tags: {t for t in tags if t in MGRTAGS or t.startswith('O:T_') or t.startswith('P:T_') or t.startswith('Q:')}
    while work:
        f = work.pop()
        key = json.dumps({k: sorted(v) for k, v in sorted(seeds[f].items())})
        if done.get(f) == key: continue
        done[f] = key; nan += 1
        e = fend(f)
        if e - f > 0x20000: continue
        try: evs = fl.analyse_seeded(f, e, seeds[f])
        except Exception as ex: P("  analyse error %s: %s" % (hex(f), ex)); continue
        for x in fl.extra: copies.append((x['site'], f, ','.join(x['val']), x['off'], x['base']))
        r0 = {t for t in INTEREST(fl.rets) if t in MGRTAGS}
        if r0 and not r0 <= rets.get(f, set()):
            rets[f] = rets.get(f, set()) | r0; fl.rettags[f] = rets[f]
            for c in callers_of.get(f, ()):
                seeds.setdefault(c, {}); work.append(c)
        for ev in evs:
            if ev['kind'] == 'vcall':
                o = ev['obj']
                if (o == 'MGR' and ev['off'] in SINK_MGR) or (o == 'MGR+0x14' and ev['off'] in SINK_IE):
                    sinks.append((ev['site'], f, o, ev['off']))
                for an in ('r1', 'r2', 'r3', 'sp+0', 'sp+4'):
                    if {'O:MGR', 'P:MGR+0x14'} & set(ev['args'].get(an, ())):
                        vargs.append((ev['site'], f, o, ev['off'], an))
                mk = 0 if o == 'MGR' else (int(o[4:], 16) if re.match(r'^MGR\+0x[0-9a-f]+$', o) else None)
                if mk is not None: vcount[(mk, ev['off'])] = vcount.get((mk, ev['off']), 0) + 1
                if o == 'MGR+0x1c' and ev['off'] == 0xbc: ctrl_setfx.add(ev['site'])
                if mk is not None:      # dispatch into every manager sub-vtable at that offset: propagate this + args
                    for vt in MGR_SUB.get(mk, ()):
                        t = im.u32(vt + ev['off'])
                        if not t or t not in set(st): continue
                        dispatched.add((hex(ev['site']), o, hex(ev['off']), hex(t)))
                        add = {'r0': {'O:MGR'} if mk == 0 else {'P:MGR+0x%x' % mk}}
                        for an in ('r1', 'r2', 'r3', 'sp+0', 'sp+4'):
                            tg = {x for x in INTEREST(ev['args'].get(an, ())) if not x.startswith('Q:')}
                            if tg: add['r' + an[1] if an[0] == 'r' else 'stk' + an[3:]] = tg
                        sd = seeds.setdefault(t, {}); ch = False
                        for k_, v_ in add.items():
                            if not set(v_) <= sd.get(k_, set()): sd[k_] = sd.get(k_, set()) | set(v_); ch = True
                        if ch or t not in done: work.append(t)
            elif ev['kind'] in ('bl', 'tail'):
                t = ev['off']
                if t in GET_MGR or t in GET_IE: continue
                add = {}
                for an in ('r0', 'r1', 'r2', 'r3', 'sp+0', 'sp+4'):
                    tg = INTEREST(ev['args'].get(an, ()))
                    tg = {x for x in tg if not x.startswith('Q:')}
                    if tg: add['r' + an[1] if an[0] == 'r' else 'stk' + an[3:]] = tg
                if add and t in set(st):
                    sd = seeds.setdefault(t, {}); ch = False
                    for k_, v_ in add.items():
                        if not set(v_) <= sd.get(k_, set()): sd[k_] = sd.get(k_, set()) | set(v_); ch = True
                    if ch or t not in done: work.append(t)
        # RET propagation: callee returns interest tags -> treat as bl result. Re-run callers with knowledge via seeds hack:
    # second pass: functions whose callees return manager tags -> analyse those callers with a return override
    P("  analysed %d function instances, %d distinct functions" % (nan, len(done))); print("  (%.1fs)" % (time.time() - t0))
    retm = {hex(f): sorted(v) for f, v in rets.items() if set(v) & set(MGRTAGS)}
    P("  functions returning a manager / IEffector / array tag: %d %s" % (len(retm), list(retm.items())[:12]))
    J["strong"] = dict(functions=len(done), sinks=[(hex(a), hex(b), c, hex(d)) for a, b, c, d in sinks],
                       copies=sorted(set((hex(a), hex(b), c, str(d), ",".join(e_)) for a, b, c, d, e_ in copies)),
                       vcall_args=sorted(set((hex(a), hex(b), c, hex(d), e_) for a, b, c, d, e_ in vargs)),
                       returns=retm)
    P("  SINKS (receiver manager at vt+0xb8/+0xbc or IEffector at vt+0x60/+0x64): %d %s" % (len(sinks), J["strong"]["sinks"]))
    P("  copies (store of a manager / IEffector / array / holder-object tag to non-stack memory): %d distinct" % len(J["strong"]["copies"]))
    for c in J["strong"]["copies"]: P("    %s in %s: %s -> [%s + %s]" % (c[0], c[1], c[2], c[4], c[3]))
    J["strong"]["dispatched"] = sorted(dispatched)
    J["strong"]["vcalls_on_manager_by_subobject_offset"] = {"+0x%x vt+0x%x" % k: v for k, v in sorted(vcount.items())}
    P("  vcalls whose receiver is a manager sub-object (MGR+k), by (k, vt offset): %s" % J["strong"]["vcalls_on_manager_by_subobject_offset"])
    P("  positive control: manager -> processor [MGR+0x1c] vt+0xbc (setFxType, F173) sites found: %d" % len(ctrl_setfx))
    check(len(ctrl_setfx) >= 20, "positive control: the propagation types `this` in manager code (>= 20 setFxType calls on [MGR+0x1c] seen)")
    P("  vcalls on a manager / IEffector receiver dispatched into the manager vtables: %d sites -> %d distinct targets" % (
        len(set(d[0] for d in dispatched)), len(set(d[3] for d in dispatched))))
    P("  manager/IEffector passed to an indirect call: %d distinct" % len(J["strong"]["vcall_args"]))
    for c in J["strong"]["vcall_args"]: P("    %s in %s: receiver %s vt+%s arg %s" % c)
    # return-value pass: callers of returning functions re-analysed with bl result override
    if retm:
        extra_get = {int(k, 16): v for k, v in retm.items()}
        GET_MGR.update({f: "derived getter" for f, v in extra_get.items() if 'O:MGR' in v})
        GET_IE.update({f: "derived IE getter" for f, v in extra_get.items() if 'P:MGR+0x14' in v and 'O:MGR' not in v})
        rs = []
        for f in sorted(set(c for g_ in extra_get for c in callers_of.get(g_, ()))):
            evs = fl.analyse_seeded(f, fend(f), seeds.get(f, {}))
            for ev in evs:
                if ev['kind'] == 'vcall' and ((ev['obj'] == 'MGR' and ev['off'] in SINK_MGR) or (ev['obj'] == 'MGR+0x14' and ev['off'] in SINK_IE)):
                    rs.append((hex(ev['site']), hex(f), ev['obj'], hex(ev['off'])))
        P("  return-pass: %d callers of derived getters re-analysed, sinks %s" % (
            len(set(c for g_ in extra_get for c in callers_of.get(g_, ()))), rs))
        J["strong"]["return_pass_sinks"] = rs; sinks += rs
    check(not sinks, "strong propagation: no manager-typed receiver reaches vt+0xb8/+0xbc and no IEffector-typed receiver reaches "
          "vt+0x60/+0x64")
    # ---------------------------------------------------------------- 4. weak net over every candidate vcall site
    P("\n[4] weak type-free net over every `ldr rF,[rV,#0xb8|0xbc|0x60|0x64]; ... blx rF` site")
    lo, hi = im.sec[".text"]; n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, im.off(lo)); cand = []
    for k, w in enumerate(W):
        if (w & 0x0ffffff0) != 0x012fff30 or (w >> 28) == 0xf: continue
        rf = w & 0xf
        for j in range(k - 1, max(k - 40, -1), -1):
            x = W[j]
            if (x >> 28) != 0xf and (x & 0x0ff00000) == 0x05900000 and ((x >> 12) & 0xf) == rf:
                if (x & 0xfff) in (0xb8, 0xbc, 0x60, 0x64): cand.append((lo + 4 * k, x & 0xfff))
                break
            if (x >> 28) != 0xf and ((x >> 12) & 0xf) == rf and ((x >> 26) & 3) in (0, 1) and not ((x >> 20) & 1 == 0 and (x >> 26) & 3 == 1): break
    byf = {}
    for s_, o_ in cand: byf.setdefault(st[bisect.bisect_right(st, s_) - 1], []).append((s_, o_))
    wf = TFlow(im, weak=True); wf.rettags = dict(fl.rettags); weak = []; unres = []
    for f, ss in sorted(byf.items()):
        evs = wf.analyse_seeded(f, fend(f), seeds.get(f, {}))
        ev_at = {}
        for ev in evs:
            if ev['kind'] == 'vcall': ev_at.setdefault(ev['site'], []).append(ev)
        for s_, o_ in ss:
            objs = [ev['obj'] for ev in ev_at.get(s_, [])]
            if not objs: unres.append((hex(s_), hex(o_), hex(f)))
            for ob in objs:
                if (o_ in SINK_MGR and ob in ('MGR', 'WMGR')) or (o_ in SINK_IE and ob in ('MGR+0x14', 'WMGR+0x14')):
                    weak.append((hex(s_), hex(o_), hex(f), ob))
    # control: the same net with +0x84 / +0x8c (Master/SendFxUnit processor fields, F173/F174) must flag 0x1b1e60 / 0x1b357c-style sites
    cf = TFlow(im, weak=True, woffs=(0x84, 0x8c)); ctrl = []
    for f, ss in sorted(byf.items()):
        for ev in cf.analyse_seeded(f, fend(f), {}):
            if ev['kind'] == 'vcall' and ev['obj'] == 'WMGR' and ev['off'] in SINK_MGR and any(ev['site'] == x for x, _ in ss):
                ctrl.append((hex(ev['site']), hex(f)))
    P("  control (+0x84/+0x8c instead of +0x80/+0x88): %d hits, e.g. %s" % (len(ctrl), ctrl[:6]))
    check(any(f_ == '0x1b1e60' for _, f_ in ctrl) and any(f_ == '0x1b357c' for _, f_ in ctrl),
          "weak-net control: the processor-field calls in 0x1b1e60 ([MFU+0x84] vt+0xb8) and 0x1b357c ([SFU+0x8c] vt+0xb8) are flagged")
    # unresolved: the instruction that last defined r0 before the blx
    ud = []
    for s_, o_, f in unres:
        s_ = int(s_, 16); d = None
        for i in reversed(im.disasm(max(int(f, 16), s_ - 0xa0), s_)):
            ops = [x.strip() for x in re.split(r',(?![^\[]*\])', i.op_str)]
            if ops and nreg(ops[0]) == 'r0' and not i.mnemonic.startswith(('str', 'cmp', 'tst', 'push', 'vst', 'b')):
                d = "%s: %s %s" % (hex(i.address), i.mnemonic, i.op_str); break
            if i.mnemonic in ('bl', 'blx'):
                d = "%s: %s %s (r0 = call result)" % (hex(i.address), i.mnemonic, i.op_str); break
        ud.append((hex(s_), o_, f, d))
    unres = ud
    J["weak"] = dict(candidates=len(cand), functions=len(byf), hits=weak, unresolved=unres, control=ctrl)
    P("  candidate sites %d in %d functions (40-word window)" % (len(cand), len(byf)))
    P("  weak hits (receiver from any +0x80/+0x88 load, an element of any [x+0xe8|0x65c|0x1d0], or a getter-slot result): %d" % len(weak))
    for h in weak: P("    %s vt+%s in %s receiver %s" % h)
    P("  sites with no receiver tag at all (unresolved): %d" % len(unres))
    for u in unres: P("    %s vt+%s in %s; r0 defined by %s" % u)
    P("\nRESULT: %d failed checks" % nfail[0])
    open(os.path.join(a.out, "h079_r2_report.txt"), "w").write("\n".join(L) + "\n")
    json.dump(J, open(os.path.join(a.out, "h079_r2.json"), "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
