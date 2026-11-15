#!/usr/bin/env python3
"""H080 (cycle 035) — who drives the Insert bypass setter 0x1129b4 (FxProcessorBase +0x9c, F157)?

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and
never stored; outputs are our own derived numbers, addresses and short name strings. Emulation is guest memory only; nothing is
written outside --out and no image is built.

Sections (criteria of kb/cycles/035.md)
  C1 caller semantics (static, capstone word-by-word): s42 0x11cfc8 (shared by every manager vtable), the reader s43 0x11cf58, the
     reload branch of InsertFxParameterManager s10 0x129b34 up to 0x129e58 (CFG: the call post-dominates the reload branch and needs
     both +0x24 and +0x25); caller scan for 0x1129b4 / s42 / s43 (direct branches, aligned pointer words incl. Thumb bit, movw/movt).
  C2 who sets the inputs: every `strb …,[…,#0x24|#0x25]` in manager code (0x11c000-0x132000) with its function and the vtable slots
     that hold it (+ the FPMB RTTI base-class map, so each slot is named by interface); outside manager code, forward type
     propagation of manager pointers (harness/H079_r2_propagate.py, re-run here with a store hook) for stores to MGR+0x24/+0x25;
     every `strb …,[…,#0x29]` in .text, split into EffectData code (functions carrying an EffectData marker string / vtable / the
     EffectData property-binder vtables 0x8ae630-0x8ae720) and the rest.
  C3 callers traced to sources: UI route (ModelInterface 0x2f8114 / getter 0x2f7fc4, TrackMenuViewController onFunction5Button /
     onFunction6Button, per-track mode byte +0x40e1 and its toggles), listener routes (IScenePatternSwitchListener /
     ISceneEditListener sub-vtables of all managers, ScenePatternSwitcher::switchSync broadcasts, default forwarding slots),
     TrackUnit per-block s10 call, propagation-dispatched call sites at IE+0x34 / IE+0x38 / s51 / s10.
  C4 emulation: REAL InsertFxProcessor (H077 EmuProc: real ctor, prepareToPlay, processBlock) + REAL InsertFxParameterManager ctor +
     REAL prj::EffectData ctor + stand-in SwitchableObject<EffectData,17> holder (H083 Rig, extended to two EffectData objects);
     the REAL manager entries are driven (IE+0x34 adjustor 0x11cfc0 via the IEffector vtable, s42, ISceneEditListener slots,
     IScenePatternSwitchListener slot 3 default 0xc6e98 -> slot 2, s51) and the REAL s10 is called once per block as TrackUnit
     0x1ca58c does, then the REAL processBlock. Every processor call the manager makes (setFxType, slot 14 on any effect, 0x1129b4)
     is logged in order and replayed on fx_processors.InsertProcessorFull + effectbase + the per-effect models; outputs (float32
     bits), processor state incl. +0x9c, slot-5..8 log and wrapper state are compared every block.
Stand-ins (declared): holder layout (+8 -> index word, +0x50 offset table, ED at holder + 4*T[i] + 0xc; from operator-> code),
EffectData Config (never read), a direct byte write to ED+0x29 standing in for the bBypass property binder (0x3589e8 `strb r0,
[r5,#0x29]`) and a direct write of the holder index word standing in for ScenePatternSwitcher::switchSync's store; the Insert
processor slot 54 (Ducker hook) skipped (as H083); pthread / guard stubs (H077 / H083).
Run: .venv/bin/python -B harness/H080_bypass_sources.py --out DIR [--jobs N] [--only c1,c2,c3,c4] [--no-prop]
"""
import argparse, bisect, hashlib, json, os, re, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
from sp16img import Image, const_sites                          # noqa: E402

BYPASS = 0x1129b4                 # FxProcessorBase: strb r1,[r0,#0x9c]
S42, S42_IE = 0x11cfc8, 0x11cfc0  # FxParameterManagerBase s42 setBypass / IEffector +0x34 adjustor
S43, S43_IE = 0x11cf58, 0x11cf50  # s43 getBypass / IEffector +0x38 adjustor
IFPM_S10, IFPM_S51 = 0x129b34, 0x126394
CALL_IN_S10 = 0x129e58
MGR_VT = {"base": 0x8430cc, "master": 0x8437ec, "insert": 0x84407c, "send": 0x8446d4,
          "cv1": 0x843b4c, "cv2": 0x8443e4, "cv3": 0x844a34}
IE_VT = {"base": 0x8432c0, "master": 0x8439e0, "insert": 0x844270, "send": 0x8448c8}
FPMB_TI = 0x8433f4
MRANGE = (0x11c000, 0x132000)
ED_MARKERS = (0x843030, 0x843768, 0x843ff8, 0x844650, 0x85a6e8, 0x85b420, 0x85b328, 0x8ae8f0, 0x8ae980, 0x8b16c0, 0x8b1750,
              0x8b17e0, 0x8b2248, 0x8ac720)
BINDER_VT_RANGE = (0x8ae630, 0x8ae720)
MI_SET, MI_GET, MI_GET_CUR = 0x2f8114, 0x2f7fc4, 0x2f8068
MI_MODE_GET, MI_MODE_SET = 0x2f81b8, 0x2f81d8
TMVC_F6, TMVC_F5 = 0x29bb0c, 0x29bd94


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u is not None and u & 0x80000000 else u


# ===================================================================================================================== static helpers
class Dis:
    """Word-by-word capstone decode of .text (data words inside code decode as None, never stop the listing)."""
    def __init__(self, im):
        self.im = im; self._c = {}
    def at(self, va):
        if va not in self._c:
            o = self.im.off(va); d = list(self.im.md.disasm(self.im.data[o:o + 4], va)) if o is not None else []
            self._c[va] = d[0] if d else None
        return self._c[va]
    def txt(self, va):
        i = self.at(va); return None if i is None else ("%s %s" % (i.mnemonic, i.op_str)).strip()
    def seq(self, a, b): return [self.txt(x) for x in range(a, b, 4)]


def va_of(im, off):
    for v, s, o in im.segs:
        if o <= off < o + s: return v + off - o


def word_refs(im, t):
    """Aligned 32-bit words equal to t (or t|1) anywhere in the file, as VAs."""
    out = []
    for val in (t, t | 1):
        b = struct.pack("<I", val); i = 0
        while True:
            i = im.data.find(b, i)
            if i < 0: break
            if i % 4 == 0: out.append((va_of(im, i), val))
            i += 1
    return out


def vt_owner(im, w, back=800):
    """(vtable address point, slot, offset-to-top, typeinfo name) for a word inside a vtable group."""
    for k in range(0, back, 4):
        a = w - k; ti = im.u32(a - 4); ott = im.u32(a - 8)
        if ti and 0x830000 <= ti < 0xb80000 and im.u32(ti + 4) and im.off(im.u32(ti + 4)) is not None:
            s = im.cstr(im.u32(ti + 4), 120)
            if s and (s[:1].isdigit() or s[:1] == "N") and ott is not None and (ott == 0 or ott > 0xffff0000):
                return a, k // 4, s32(ott), s
    return None


def rtti_bases(im, ti):
    fl = im.u32(ti + 8); n = im.u32(ti + 12); out = []
    if n is not None and 0 < n < 16 and fl is not None and fl < 16:
        for k in range(n):
            b = im.u32(ti + 16 + 8 * k); of = im.u32(ti + 20 + 8 * k)
            out.append((s32(of) >> 8, im.cstr(im.u32(b + 4), 80)))
    return out


def cfg_succ(D, va, lo, hi):
    """Successors of the instruction at va inside [lo,hi); 'EXIT' for returns. Jump tables `ldrls pc,[pc,rX,lsl #2]` use the
    bound of the preceding `cmp rX,#n`."""
    i = D.at(va)
    if i is None: return []
    m, op = i.mnemonic, i.op_str; w = struct.unpack("<I", i.bytes)[0]; cond = w >> 28
    nxt = [va + 4] if va + 4 < hi else []
    if m.startswith("b") and not m.startswith(("bl", "bx", "bic")) and op.startswith("#"):
        t = int(op[1:], 16); return [t] + (nxt if cond != 0xe else [])
    if m.startswith("bl") and op.startswith("#"): return nxt                      # bl / blx imm: returns
    if m.startswith("blx"): return nxt
    if m.startswith("bx"):
        if op == "lr": return ["EXIT"] + (nxt if cond != 0xe else [])
        return ["UNK"]
    if m.startswith("pop") and "pc" in op: return ["EXIT"] + (nxt if cond != 0xe else [])
    if m.startswith("ldr") and op.startswith("pc, [pc, r"):
        r = op.split(",")[2].strip()
        bound = None
        for j in range(va - 4, va - 40, -4):
            x = D.at(j)
            if x is not None and x.mnemonic == "cmp" and x.op_str.startswith(r + ", #"):
                bound = int(x.op_str.split("#")[1], 0); break
        tab = va + 8
        return [D.im.u32(tab + 4 * k) for k in range(bound + 1)] + nxt
    if ("pc" in op.split(",")[0]) and not m.startswith(("cmp", "str", "tst", "cmn", "push")): return ["UNK"]
    return nxt


def reach(D, start, lo, hi, avoid=(), cut=()):
    seen = set(); work = [start]; exits = set(); unk = set()
    while work:
        a = work.pop()
        if a in seen or a in avoid: continue
        seen.add(a)
        for s in cfg_succ(D, a, lo, hi):
            if s == "EXIT": exits.add(a); continue
            if s == "UNK": unk.add(a); continue
            if (a, s) in cut: continue
            if lo <= s < hi: work.append(s)
    return seen, exits, unk


def strb_sweep(im, D, offs, lo=None, hi=None):
    lo = lo or im.sec[".text"][0]; hi = hi or im.sec[".text"][1]; out = []
    pat = re.compile(r"^(\w+), \[(\w+), #(0x[0-9a-f]+|\d+)\]!?$")
    W = struct.unpack_from("<%dI" % ((hi - lo) // 4), im.data, im.off(lo))
    for k, w in enumerate(W):
        # ARM strb immediate offset: cond 01 0 P U 1 W 0 Rn Rt imm12 (bit 22 = B, bit 20 = L = 0)
        if (w >> 28) == 0xf or (w & 0x0c500000) != 0x04400000 or (w & 0x02000000): continue
        if (w & 0xfff) not in offs: continue
        va = lo + 4 * k; t = D.txt(va)
        if t and t.startswith("strb"):
            mm = pat.match(t.split(" ", 1)[1])
            if mm and int(mm.group(3), 0) in offs: out.append((va, t))
    return out


# ===================================================================================================================== C1
def c1(im, D, P, check):
    R = {}
    s42 = D.seq(S42, 0x11d014)
    exp42 = ["push {r3, r4, r5, lr}", "mov r4, r0", "ldrb r3, [r0, #0x24]", "mov r5, r1", "cmp r3, #0", "popeq {r3, r4, r5, pc}",
             "ldr r0, [r0, #0x1c]", "bl #0x1129b4", "ldr r4, [r4, #0x20]", "ldr r3, [r4, #8]", "ldr r3, [r3]", "cmp r3, #0x10",
             "bhi #0x11d014", "add r3, r3, #0x14", "ldr r3, [r4, r3, lsl #2]", "add r4, r4, r3, lsl #2", "ldr r3, [r4, #0xc]",
             "strb r5, [r3, #0x29]", "pop {r3, r4, r5, pc}"]
    check(s42 == exp42, "s42 0x11cfc8(mgr, v): +0x24 == 0 -> return, nothing written; else 0x1129b4([mgr+0x1c] = processor, v) and "
          "then EffectData[objectIndex]+0x29 := v (holder [mgr+0x20], objectIndex = *[holder+8] <= 16, ED = [holder + 4*T[i] + 0xc]); "
          "no return value (r0 = scratch); the bypass value is the caller's r1 byte unchanged")
    tail = D.seq(0x11d014, 0x11d02c)
    check(tail[3] == "bl #0x4f782c" and tail[5] == "b #0x11d00c" and
          "SwitchableObject" in (im.cstr(im.u32(0x11d018 + 8 + 0x10), 120) or "") and "prj::EffectData, int kNumberOfObjects = 17"
          in (im.cstr(im.u32(0x11d018 + 8 + 0x10), 140) or ""),
          "s42 out-of-range index path: assert print 0x4f782c (\"SwitchableObject<prj::EffectData, 17>::operator->\") then the same "
          "store (it does not skip the ED write)")
    s43 = D.seq(S43, 0x11cf9c)
    check(s43[0] == "ldrb r3, [r0, #0x24]" and s43[3] == "bne #0x11cf70" and s43[4] == "mov r0, r3" and
          s43[-2] == "ldrb r0, [r3, #0x29]" and D.seq(S43_IE, S43_IE + 8) == ["sub r0, r0, #0x14", "b #0x11cf58"],
          "s43 0x11cf58 (IE+0x38 adjustor 0x11cf50): returns 0 when +0x24 == 0, else EffectData[objectIndex]+0x29 (the stored "
          "bBypass byte, not the processor's +0x9c)")
    check(D.seq(S42_IE, S42_IE + 8) == ["sub r0, r0, #0x14", "b #0x11cfc8"], "IE+0x34 adjustor 0x11cfc0 = `sub r0,#0x14; b s42`")
    # every manager vtable: slot 42/43 and IE+0x34/+0x38
    vts = {nm: (hex(im.u32(v + 42 * 4)), hex(im.u32(v + 43 * 4))) for nm, v in MGR_VT.items()}
    ies = {nm: (hex(im.u32(v + 0x34)), hex(im.u32(v + 0x38))) for nm, v in IE_VT.items()}
    R["vt_s42_s43"] = vts; R["ie_34_38"] = ies
    check(all(v == (hex(S42), hex(S43)) for v in vts.values()) and all(v == (hex(S42_IE), hex(S43_IE)) for v in ies.values()),
          "s42/s43 are the same function in all 7 manager vtable groups (base, Master, Insert, Send + 3 construction vtables) and "
          "IE+0x34/+0x38 the same adjustors in all 4 IEffector sub-vtables: %s / %s" % (vts["insert"], ies["insert"]))
    # IFPM s10 reload branch
    lo, hi = IFPM_S10, 0x12b1b0
    hd = D.seq(lo, 0x129b74)
    check(hd[0] == "ldrb r3, [r0, #0x24]" and hd[5] == "beq #0x129f38" and hd[6] == "ldrb r3, [r0, #0x25]" and
          hd[8] == "beq #0x129eb4" and hd[11] == "strb r2, [r0, #0x25]" and hd[14] == "str r3, [sp, #0x10]" and
          D.txt(0x129f38) == "add sp, sp, #0x1c" and D.txt(0x129f3c) == "pop {r4, r5, r6, r7, pc}",
          "s10 0x129b34: +0x24 == 0 -> 0x129f38 return (nothing at all); +0x25 == 0 -> 0x129eb4 (trigger/edit/modulation part, no "
          "reload); else +0x25 := 0 and the reload branch 0x129b58")
    seq_call = D.seq(0x129e28, 0x129e5c)
    check(seq_call == ["ldr r6, [r4, #0x20]", "ldr r7, [r4, #0x1c]", "ldr r3, [r6, #8]", "ldr r3, [r3]", "cmp r3, #0x10",
                       "bhi #0x12a51c", "add r3, r3, #0x14", "ldr r3, [r6, r3, lsl #2]", "add r6, r6, r3, lsl #2",
                       "ldr r3, [r6, #0xc]", "ldrb r1, [r3, #0x29]", "mov r0, r7", "bl #0x1129b4"],
          "0x129e58: 0x1129b4([mgr+0x1c] = the manager's own processor, EffectData[objectIndex]+0x29) - the stored bBypass byte")
    seen, exits, unk = reach(D, 0x129b58, lo, hi, avoid=(CALL_IN_S10,))
    allr, _, unk2 = reach(D, 0x129b58, lo, hi)
    check(CALL_IN_S10 in allr and not exits and not unk,
          "CFG of s10 (word-by-word decode, jump tables @0x129d50 bound 9 included): from the reload branch 0x129b58 every path "
          "reaches the call 0x129e58 - with that node removed no return is reachable (%d nodes, exits %d, unresolved %d); so every "
          "reload applies the bypass byte, for every type incl. Off (-1 skips to 0x129e28)" % (len(seen), len(exits), len(unk)))
    ent, _, _ = reach(D, lo, lo, hi, cut={(0x129b54, 0x129b58)})
    ent2, _, _ = reach(D, lo, lo, hi, cut={(0x129b48, 0x129b4c)})
    check(CALL_IN_S10 not in ent and CALL_IN_S10 not in ent2,
          "without the fall-through 0x129b54 -> 0x129b58 (+0x25 set) or 0x129b48 -> 0x129b4c (+0x24 set) 0x129e58 is unreachable "
          "from the entry: the call happens only on a reload of an enabled manager")
    R["s10_reload_nodes"] = len(seen)
    # caller scans
    dc = im.direct_calls()
    callers = {t: sorted((hex(s), k) for s, tt, k in dc if tt == t) for t in (BYPASS, S42, S42_IE, S43, S43_IE, IFPM_S10, IFPM_S51)}
    for t in callers:   # confirm each hit is a real decoded branch
        callers[t] = [c for c in callers[t] if D.txt(int(c[0], 16)) and D.txt(int(c[0], 16)).split()[0].startswith("b")]
    wr = {t: [(hex(a), hex(v)) for a, v in word_refs(im, t)] for t in (BYPASS, S42, S42_IE, S43, S43_IE)}
    mv = const_sites(im, [BYPASS, BYPASS | 1, S42, S42 | 1, S42_IE, S42_IE | 1])
    R["callers"] = {hex(k): v for k, v in callers.items()}; R["words"] = {hex(k): v for k, v in wr.items()}
    R["movw_lit"] = {hex(k): [(a, hex(b)) for a, b in v] for k, v in mv.items()}
    check([c[0] for c in callers[BYPASS]] == ["0x11cfe4", "0x129e58"] and wr[BYPASS] == [] and
          not mv[BYPASS] and not mv[BYPASS | 1],
          "0x1129b4: direct branches only 0x11cfe4 (s42) and 0x129e58 (IFPM s10); no aligned pointer word (incl. |1), no literal-pool "
          "word or movw/movt pair anywhere in the file (whole-file word scan + .text const scan); REA xrefs gives the same two")
    vt_words = sorted(a for a, v in wr[S42])
    check(callers[S42] == [("0x11cfc4", "b")] and len(vt_words) == 7 and
          all(vt_owner(im, int(a, 16)) and vt_owner(im, int(a, 16))[1] == 42 for a in vt_words) and not mv[S42] and not mv[S42 | 1],
          "s42 0x11cfc8: only the IEffector adjustor's `b` 0x11cfc4 and slot 42 of the 7 manager vtable groups %s; no other pointer" %
          vt_words)
    ie_words = sorted(a for a, v in wr[S42_IE])
    check(callers[S42_IE] == [] and ie_words == sorted(hex(v + 0x34) for v in IE_VT.values()) and not mv[S42_IE] and not mv[S42_IE | 1],
          "IE+0x34 adjustor 0x11cfc0: no direct branch; its only pointer words are the 4 IEffector sub-vtable entries %s" % ie_words)
    # +0x9c stores in processor code
    st9c = strb_sweep(im, D, {0x9c}, 0x112000, 0x11c000)
    R["strb_9c_processor_code"] = st9c
    check([hex(a) for a, _ in st9c] == ["0x112910", "0x1129b4"] and D.txt(0x112910) == "strb r3, [r4, #0x9c]" and
          im.func_of(0x112910)[0] == 0x1128cc,
          "the only `strb …,[…,#0x9c]` in processor code 0x112000-0x11c000 are the FxProcessorBase ctor 0x1128cc (@0x112910, := 0) "
          "and the setter itself (%s)" % [hex(a) for a, _ in st9c])
    P("  callers %s" % json.dumps(R["callers"]))
    return R


# ===================================================================================================================== C2
class PropHook:
    stores = []


def run_propagation(outdir, P):
    """Re-run harness/H079_r2_propagate.py (F178 method) with a hook that records byte stores whose base carries a manager tag at
    +0x24/+0x25 (manager +0x24 = enable, +0x25 = reload request)."""
    import H079_r2_propagate as R2
    import armflow
    base_cls = R2.TFlow

    class HookFlow(base_cls):
        def _step2(self, i, st, fs, fe, events):
            m = i.mnemonic
            if m.startswith("strb") and not m.startswith("strbt"):
                mm = re.match(r"^\w+, \[(\w+), #(0x[0-9a-f]+|\d+)\]", i.op_str)
                if mm:
                    off = int(mm.group(2), 0); tags = set(st.g(mm.group(1)))
                    for t in tags:
                        k = None
                        if t in ("O:MGR", "O:WMGR"): k = 0
                        else:
                            x = re.match(r"^P:W?MGR\+0x([0-9a-f]+)$", t)
                            if x: k = int(x.group(1), 16)
                        if k is not None and (k + off) & 0xffffffff in (0x24, 0x25):
                            PropHook.stores.append((i.address, fs, t, off, self.weak))
            return super()._step2(i, st, fs, fe, events)
    R2.TFlow = HookFlow
    old = sys.argv; sys.argv = ["H079_r2_propagate.py", "--out", outdir]
    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): R2.main()
    finally:
        sys.argv = old; R2.TFlow = base_cls
    J = json.load(open(os.path.join(outdir, "h079_r2.json")))
    rep = open(os.path.join(outdir, "h079_r2_report.txt")).read()
    return J, rep


def c2(im, D, P, check, outdir, do_prop=True):
    R = {}
    # FPMB bases -> sub-object offsets
    bases = rtti_bases(im, FPMB_TI); R["fpmb_bases"] = bases
    bmap = {off: nm for off, nm in bases}
    check(bmap.get(0xc) == "27IScenePatternSwitchListener" and bmap.get(0x10) == "18ISceneEditListener" and bmap.get(0x14) == "9IEffector",
          "FxParameterManagerBase RTTI (vmi 0x8433f4) bases: %s" % ", ".join("+0x%x %s" % b for b in bases))
    sw = strb_sweep(im, D, {0x24, 0x25}, *MRANGE)
    rows = []
    for va, t in sw:
        f = im.func_of(va)[0]
        # function entry for listener slots: walk back to the nearest preceding instruction after a return / thunk pair
        refs = []
        for cand in (f,):
            for a, v in word_refs(im, cand):
                o = vt_owner(im, a)
                if o: refs.append("%s s%d ott%d %s" % (hex(o[0]), o[1], o[2], o[3]))
        rows.append(dict(site=hex(va), ins=t, fn=hex(f), vt=refs[:8]))
    R["strb_24_25_manager_code"] = rows
    for r in rows: P("    %s %-28s fn %s %s" % (r["site"], r["ins"], r["fn"], (r["vt"][:2] + (["…"] if len(r["vt"]) > 2 else []))))
    # classify the +0x24 stores
    want24 = {"0x11c9f8": "slot 14 / ISceneEditListener s2 (:= 0, then processor vt+0xc8 0x112780 = pending effect slot 6(1.0f) "
                          "fade-out; no reload)",
              "0x126364": "IFPM slot 20 / ISceneEditListener s8 (:= 0)", "0x126378": "IFPM slot 22 / ISceneEditListener s16 (:= 0)",
              "0x12638c": "IFPM slot 24 / ISceneEditListener s20 (:= 0)",
              "0x11fa80": "base ctor 0x11fa0c (+0x24 := 1)", "0x11fb14": "base ctor variant 0x11fad4 (construction vtables; := 1)",
              "0x11ca28": "slot 15 / ISceneEditListener s3 (:= 1, then s51(1))", "0x11ca44": "slot 16 / ISceneEditListener s4 (:= 0)",
              "0x11ca58": "slot 18 / ISceneEditListener s12 (:= 0)",
              "0x11cbe8": "slot 17 / ISceneEditListener s5 (:= 1; s51(1) if [arg2+8] == +0x38)",
              "0x11cc1c": "slot 19 / ISceneEditListener s13 (:= 1; s51(1) if [arg1+8] == +0x38)",
              "0x126a84": "IFPM slot 21 / ISceneEditListener s9 (:= 1; s51(1) if [arg2+0xc] == track +0x40 or -1)",
              "0x126ac4": "IFPM slot 23 / ISceneEditListener s17 (:= 1; s51(1) if [arg1+0xc] == +0x40 or -1)",
              "0x126b10": "IFPM slot 25 / ISceneEditListener s21 (:= 1; s51(1) for either track argument)"}
    got24 = {r["site"] for r in rows if r["ins"].endswith("#0x24]")}
    R["strb24_classified"] = want24
    check(got24 == set(want24), "manager code 0x11c000-0x132000 has exactly %d `strb …,[…,#0x24]` sites, all FxParameterManager "
          "+0x24 writes: %s" % (len(got24), "; ".join("%s %s" % kv for kv in sorted(want24.items()))))
    # read back each listener function's behaviour (asserted instruction text)
    chk = {
        0x11ca18: ["ldr ip, [r0]", "mov r2, #1", "push {r3, lr}", "mov r1, r2", "strb r2, [r0, #0x24]", "ldr r3, [ip, #0xcc]", "blx r3"],
        0x11ca40: ["mov r3, #0", "strb r3, [r0, #0x24]", "bx lr"], 0x11ca54: ["mov r3, #0", "strb r3, [r0, #0x24]", "bx lr"],
        0x11cc3c: ["ldrb r2, [r0, #0x24]", "push {r3, lr}", "cmp r2, #0", "popeq {r3, pc}", "ldr r2, [r0, #0x20]", "ldr r2, [r2, #8]",
                   "ldr r2, [r2]", "cmp r1, r2", "popeq {r3, pc}", "ldr ip, [r0]", "mov r1, #0", "str r2, [r0, #0x38]",
                   "ldr r3, [ip, #0xcc]", "blx r3"]}
    okb = all(D.seq(f, f + 4 * len(v)) == v for f, v in chk.items())
    check(okb, "listener bodies: 0x11ca18 (+0x24 := 1; s51(1)), 0x11ca40 / 0x11ca54 (+0x24 := 0), 0x11cc3c IScenePatternSwitchListener "
          "slot 2 (if +0x24 and arg != current objectIndex: +0x38 := objectIndex; s51(0))")
    s51 = D.seq(IFPM_S51, IFPM_S51 + 0x2c)
    check(s51 == ["cmp r1, #0", "push {r4, lr}", "mov r4, r0", "beq #0x1263b4", "ldr r0, [r0, #0x1c]", "ldr r3, [r0]",
                  "ldr r3, [r3, #0xd4]", "blx r3", "mov r3, #1", "strb r3, [r4, #0x25]", "pop {r4, pc}"] and
          im.u32(0x842c10 + 0xd4) == 0x117280,
          "IFPM s51 0x126394(mgr, f): f != 0 -> processor vt+0xd4 (Insert 0x117280: vt+0xd0 = slot-52 defaults for effects 0..9); "
          "then +0x25 := 1 (reload at the next s10)")
    # +0x25 stores = ctor clears + s51 + s10 clear
    got25 = sorted(r["site"] for r in rows if r["ins"].endswith("#0x25]"))
    R["strb25"] = got25
    P("    +0x25 stores in manager code: %s" % got25)
    # propagation: stores to MGR+0x24/+0x25 outside manager code
    if do_prop:
        pdir = os.path.join(outdir, "prop"); os.makedirs(pdir, exist_ok=True)
        PropHook.stores = []
        J2, rep2 = run_propagation(pdir, P)
        st = sorted(set((hex(a), hex(f), t, off, w) for a, f, t, off, w in PropHook.stores))
        outside = [s for s in st if not (MRANGE[0] <= int(s[0], 16) < MRANGE[1])]
        inside = [s for s in st if MRANGE[0] <= int(s[0], 16) < MRANGE[1]]
        R["prop"] = dict(result_line=[l for l in rep2.splitlines() if l.startswith("RESULT")], functions=J2["strong"]["functions"],
                         stores_inside=inside, stores_outside=outside)
        R["prop_dispatched"] = [d for d in J2["strong"]["dispatched"] if d[3] in
                                ("0x11cfc8", "0x11cfc0", "0x11cf58", "0x11cf50", "0x126394", "0x121174", "0x12de8c", "0x11fdcc",
                                 "0x129b34", "0x11fcc8")]
        P("    propagation: %s functions, stores to MGR+0x24/+0x25 inside manager code %d, outside %d %s" % (
            J2["strong"]["functions"], len(inside), len(outside), outside[:6]))
        listener_sites = {"0x11c9f8", "0x11ca28", "0x11ca44", "0x11ca58", "0x11cbe8", "0x11cc1c", "0x126364", "0x126378", "0x12638c",
                          "0x126a84", "0x126ac4", "0x126b10", "0x1263b8", "0x129b60"}
        check(listener_sites <= {x_[0] for x_ in inside},
              "store-hook positive control: inside manager code the hook sees the listener / s51 / s10 stores %s" % sorted(listener_sites))
        check(R["prop"]["result_line"] == ["RESULT: 0 failed checks"] and not outside,
              "forward manager-pointer propagation (F178 method re-run, %d functions; its own %s): no byte store to MGR+0x24/+0x25 "
              "outside manager code (strong and weak tags)" % (J2["strong"]["functions"], R["prop"]["result_line"]))
    # EffectData +0x29 writers
    s29 = strb_sweep(im, D, {0x29})
    mk = const_sites(im, ED_MARKERS)
    marked = {}
    for v, l in mk.items():
        for k, a in l: marked.setdefault(im.func_of(a)[0], set()).add(hex(v))
    binder_fns = set()
    for a in range(BINDER_VT_RANGE[0], BINDER_VT_RANGE[1], 4):
        f = im.u32(a)
        if f and 0x8000 <= f < 0x800000: binder_fns.add(f)
    ed_rows = []; other = []
    for va, t in s29:
        f = im.func_of(va)[0]
        if f in binder_fns or f in marked or MRANGE[0] <= va < MRANGE[1] and f == S42:
            slots = [hex(a) for a in range(BINDER_VT_RANGE[0], BINDER_VT_RANGE[1], 4) if im.u32(a) == f]
            ed_rows.append(dict(site=hex(va), ins=t, fn=hex(f), binder_slots=slots, markers=sorted(marked.get(f, ()))))
        else:
            other.append((hex(va), hex(f)))
    R["strb29_ed"] = ed_rows; R["strb29_other_count"] = len(other); R["strb29_other_in_manager_code"] = [
        o for o in other if MRANGE[0] <= int(o[0], 16) < MRANGE[1]]
    for r in ed_rows: P("    ED+0x29 writer %s %-24s fn %s binder-vt %s markers %s" % (r["site"], r["ins"], r["fn"], r["binder_slots"], r["markers"]))
    gotf = {r["fn"] for r in ed_rows}
    check({r["site"] for r in ed_rows} == {"0x11d00c", "0x355500", "0x35691c", "0x356950", "0x358a94", "0x359f68"} and
          D.seq(0x3554f0, 0x355504) == ["cmp r1, #0", "beq #0x355508", "ldrb r2, [r1, #0x29]", "ldr r3, [r0, #8]", "strb r2, [r3, #0x29]"]
          and not R["strb29_other_in_manager_code"],
          "EffectData +0x29 (\"bBypass\") writers in code that handles EffectData: s42 @0x11d00c (UI) and the EffectData "
          "ctor 0x359d1c (@0x359f68, := 0) and the bBypass property-binder functions: copyFrom 0x3554f0 (@0x355500, exidx groups it "
          "under 0x3554bc), reset 0x3568fc (@0x35691c/0x356950), load 0x3589e8 (@0x358a94) - functions %s; %d other `strb …,#0x29` sites in .text "
          "are in functions with no EffectData marker (other classes, `likely`), none in manager code" % (
              sorted(gotf - {hex(S42)}), len(other)))
    # binder identification: key string and the `strb [r5,#0x29]` load function asserts VarUtility::fromVar<bool>
    ld = D.seq(0x3589e8, 0x358b20)
    keys = [im.cstr(im.u32(a + 8 + int(D.at(a).op_str.split("#")[1].rstrip("]"), 0)), 40) for a in range(0x3589e8, 0x358b20, 4)
            if D.at(a) is not None and D.at(a).mnemonic == "ldr" and "[pc, #" in D.at(a).op_str]
    check("bBypass" in keys and "strb r0, [r5, #0x29]" in ld,
          "binder 0x3589e8 (binder vtable slot @0x8ae6c0) loads the value of key \"bBypass\" (juce::var -> bool) into ED+0x29; "
          "0x35859c writes ED+0x29 under the same key (save); 0x356f60 prints \"bBypass = true/false\"")
    return R


# ===================================================================================================================== C3
def c3(im, D, P, check, R2):
    R = {}
    mi = D.seq(MI_SET, 0x2f817c)
    check(mi[:3] == ["ldr r3, [r0, #4]", "push {r4, r5, r6, lr}", "mov r4, r1"] and "bl #0x32b664" in mi and
          mi[mi.index("bl #0x32b664") + 3] == "ldr r3, [r3, #0x10]" and "ldr r3, [r3, #0x24]" in mi and
          mi[-4:] == ["ldr r3, [r3]", "mov r1, r5", "ldr r3, [r3, #0x34]", "blx r3"],
          "ModelInterface::setEffectBypassMode 0x2f8114(ref, slot, bool): root(0x32b664) vt+0x10(track = [[ref+4]+0x54]) -> "
          "TrackUnit vt+0x24(slot) (0x1c7888 -> 0x1c7890: +0xe8[slot] + 0x14 = Insert manager's IEffector, slot < +0xf0) -> "
          "IE+0x34(bool) = s42; only Insert managers are reachable this way")
    g = D.seq(MI_GET, 0x2f8024)
    check(g[-3:] == ["ldr r3, [r3]", "ldr r3, [r3, #0x38]", "blx r3"] and "ldr r3, [r3, #0x24]" in g,
          "getEffectBypassMode 0x2f7fc4(ref, slot): same route -> IE+0x38 = s43 (stored ED+0x29)")
    tg = D.seq(0x1c7890, 0x1c78b8)
    check(tg == ["ldr r3, [r0, #0xf0]", "cmp r1, r3", "bhs #0x1c78b0", "ldr r3, [r0, #0xe8]", "ldr r0, [r3, r1, lsl #2]", "cmp r0, #0",
                 "addne r0, r0, #0x14", "bx lr", "mov r0, #0", "bx lr"], "TrackUnit 0x1c7890(slot): slot used as-is (0 = FX1, 1 = FX2)")
    # TrackMenuViewController handlers
    rows = {}
    for nm, f, slot in (("onFunction5Button", TMVC_F5, 0), ("onFunction6Button", TMVC_F6, 1)):
        hi = im.starts()[bisect.bisect_right(im.starts(), f)]
        txt = [(a, D.txt(a)) for a in range(f, hi, 4)]
        name = None
        for a, t in txt:
            if t and t.startswith("ldr r1, [pc, #"):
                s = im.cstr(im.u32(a + 8 + int(t.split("#")[1].rstrip("]"), 0)), 90)
                if s and "TrackMenuViewController::" in s: name = s
        sets = [a for a, t in txt if t == "bl #0x2f8114"]
        ok = True
        for a in sets:   # mov r1,#slot ; mov r0,r5 ; bl getter ; mov r1,#slot|1 ; eor r2,r0,#1 / eor r2,r0,r1 ; mov r0,r5 ; uxtb r2,r2
            w = [D.txt(a - 4 * k) for k in range(7, 0, -1)]
            ok &= (w[0] in ("mov r1, #%d" % slot,) and w[2] == "bl #0x2f7fc4" and w[3] == "mov r1, #%d" % (slot if slot == 0 else 1)
                   and w[4] in ("eor r2, r0, #1", "eor r2, r0, r1") and w[6] == "uxtb r2, r2")
        jt = D.at(f + 0x2c)
        rows[nm] = dict(fn=hex(f), assert_name=name, set_sites=[hex(a) for a in sets], toggle_pattern=ok)
    R["tmvc"] = rows
    check(rows["onFunction5Button"]["set_sites"] == ["0x29c020", "0x29c044"] and rows["onFunction6Button"]["set_sites"] ==
          ["0x29bb74", "0x29bcd0"] and all(r["toggle_pattern"] for r in rows.values()) and
          all(r["assert_name"] and r["assert_name"].endswith(k + "(IGuiButton*)") for k, r in rows.items()),
          "TrackMenuViewController::onFunction5Button 0x29bd94 / onFunction6Button 0x29bb0c call setEffectBypassMode(ref, 0 / 1, "
          "!getEffectBypassMode(ref, 0 / 1)): a toggle of insert slot 0 (FX1) / 1 (FX2) of the current track, value = NOT stored "
          "bBypass")
    # the conditions: track-type switch [ [this+0x12c] +0x16c ] and the per-track byte +0x40e1
    jt5 = [im.u32(0x29bdc8 + 4 * k) for k in range(4)]; jt6 = [im.u32(0x29bb40 + 4 * k) for k in range(4)]
    m5 = D.seq(0x29bf1c, 0x29bf24) + D.seq(0x29be6c, 0x29be74); m6 = D.seq(0x29bc24, 0x29bc2c) + D.seq(0x29bb50, 0x29bb58)
    mode_get = D.seq(0x46ca54, 0x46ca5c); byte_get = D.seq(MI_MODE_GET, MI_MODE_GET + 0x20)
    check(jt5 == [0x29bf1c, 0x29be6c, 0x29bdd8, 0x29bdd8] and jt6 == [0x29bc24, 0x29bb50, 0x29bc1c, 0x29bc1c] and
          m5 == ["cmp r6, #0", "bne #0x29c004", "cmp r6, #0", "bne #0x29c028"] and
          m6 == ["cmp r6, #0", "bne #0x29bcb4", "cmp r6, #0", "beq #0x29bb78"] and mode_get == ["ldr r0, [r0, #0x16c]", "bx lr"] and
          byte_get[2] == "cmp r3, #0xf" and byte_get[6] == "ldrbls r0, [r3, #0xe1]",
          "both handlers switch on [[this+0x12c]+0x16c] (0x46ca54): cases 0/1 toggle the FX bypass only when the per-track byte "
          "model+0x40e1+track (0x2f81b8, track = [[ref+4]+0x54] <= 15) is set; cases 2/3: F5 toggles setMidiCcBypassMode (0x311098), "
          "F6 nothing; with the byte clear F5/F6 open a view instead (vt+8 of [this+0x10])")
    # who toggles the per-track byte
    wr = sorted(hex(s) for s, t, k in im.direct_calls() if t == MI_MODE_SET and k == "bl")
    h1 = [vt_owner(im, a) for a, v in word_refs(im, 0x2d5684)]
    tinames = []
    for a, v in word_refs(im, 0x2d5684):
        ti = im.u32(a - 0x10); tinames.append(im.cstr(im.u32(ti + 4), 140) if ti else None)
    toggles = D.seq(0x2d5684, 0x2d56c4)
    R["mode_byte_setters"] = wr; R["mode_byte_handler_ti"] = tinames
    check(wr == ["0x2d56a4", "0x2d68f8"] and toggles[4:8] == ["bl #0x2f81b8", "eor r1, r0, #1", "mov r0, r4", "uxtb r1, r1"] and
          any(t and "GlobalSectionTrackMenuWidgetController" in t and "Handler_1" in t for t in tinames),
          "the per-track byte is written only by 0x2f81d8, called from 0x2d5684 and 0x2d68d8 (both: byte := !byte, then refresh "
          "widget [ctl+0x44] 0x49f4c4); 0x2d5684 is the callback slot of ButtonHandler GlobalSectionTrackMenuWidgetController ctor "
          "Handler_1 (vtable word %s); 0x2d68d8 has no reference (`likely` dead / inlined twin)" % [hex(a) for a, v in word_refs(im, 0x2d5684)])
    # which widget the per-track byte lights: GlobalSectionTrackMenuWidget 0x49f4c4 and its layout 0x49ea88
    w4c4 = D.seq(0x49f4c4, 0x49f4dc)
    lay = D.seq(0x49f064, 0x49f070)
    lit_ind = im.cstr(im.u32(0x49f02c + 8 + 0x40c), 40); lit_byp = im.cstr(im.u32(0x49f098 + 8 + 0x3a4), 40)
    check(w4c4 == ["ldrb r2, [r0, #0xd8]", "cmp r2, r1", "bxeq lr", "strb r1, [r0, #0xd8]", "ldr r0, [r0, #0xd0]", "b #0x38e824"] and
          lay == ["mov r4, r0", "bl #0x38e434", "str r4, [r6, #0xd0]"] and lit_ind == "ot_1_p0021_indicator" and
          lit_byp == "f_1_p0172_bypass" and D.txt(0x49f0b8) == "mov r0, #0xd4",
          "the Handler_1 refresh 0x49f4c4(widget, byte) sets widget +0xd8 and the state of widget +0xd0; the layout 0x49ea88 builds "
          "+0xd0 from skin \"ot_1_p0021_indicator\" (@0x49f06c) and right after it a part from skin \"f_1_p0172_bypass\" (@0x49f098): "
          "the per-track byte is shown by the indicator next to the BYPASS graphic of the global-section track menu (`likely`)")
    # listener sub-vtables of the Insert manager + default forwarding
    sps = {k: hex(im.u32(0x8441e4 + 4 * k)) for k in range(6)}
    sel = {k: hex(im.u32(0x844208 + 4 * k)) for k in range(24)}
    R["IScenePatternSwitchListener_insert"] = sps; R["ISceneEditListener_insert"] = sel
    fwd = (D.seq(0xc6e98, 0xc6eb4), D.seq(0xc6eb0, 0xc6eb4), D.seq(0xc6eb4, 0xc6ecc))
    check(sps[2] == "0x11cc34" and D.seq(0x11cc34, 0x11cc3c) == ["sub r0, r0, #0xc", "b #0x11cc3c"] and
          fwd[0] == ["ldr ip, [r0]", "push {r3, lr}", "ldr r3, [sp, #0xc]", "ldr ip, [ip, #8]", "blx ip", "pop {r3, pc}", "bx lr"]
          and fwd[2][3] == "ldr r3, [ip, #0x10]" and sps[3] == "0xc6e98" and sps[4] == "0xc6eb0" and sps[5] == "0xc6eb4",
          "IScenePatternSwitchListener sub-vtable (Insert 0x8441e4): slot 2 = 0x11cc34 -> 0x11cc3c (reload on scene change); slot 3 "
          "= default 0xc6e98 which forwards to slot 2; slot 5 = default 0xc6eb4 -> slot 4 = 0xc6eb0 `bx lr` (no-op)")
    ss = D.seq(0x18bc38, 0x18bc50) + D.seq(0x18bc88, 0x18bca0) + D.seq(0x18bcf4, 0x18bd08)
    nm = im.cstr(im.u32(0x18bc10 + 8 + 0x100), 80)
    check(nm and "ScenePatternSwitcher::switchSync" in nm and ss[:6] == ["ldr r2, [r5, #0xc]", "cmp r7, sl", "ldr r3, [r5, #0x10]",
          "str r7, [r2]", "str r6, [r3]", "beq #0x18bcbc"] and ss[6:12] == ["ldr r0, [r5, #0x24]", "ldr r0, [r0, r4, lsl #2]",
          "ldr ip, [r0]", "stm sp, {r6, sb}", "ldr ip, [ip, #0xc]", "blx ip"] and ss[12:] == ["ldr r0, [r5, #0x24]",
          "ldr r0, [r0, r4, lsl #2]", "ldr ip, [r0]", "ldr ip, [ip, #0x14]", "blx ip"],
          "ScenePatternSwitcher::switchSync 0x18bbb8: stores the new scene / pattern index through [this+0xc] / [this+0x10], then for "
          "each listener in [this+0x24] (count +0x2c): scene changed -> vt+0xc (slot 3), same scene -> vt+0x14 (slot 5)")
    # Insert allocation: manager +0xc / +0x10 appended to the two listener arrays (asserted in the propagation report too)
    seq = D.seq(0x1bbd84, 0x1bc070)
    check("add sl, r5, #0xc" in seq and "add sl, r5, #0x10" in seq,
          "Insert allocation 0x1bbda0: manager +0xc (IScenePatternSwitchListener) and +0x10 (ISceneEditListener) are appended to "
          "listener arrays of [[sys+0x590]+0x9c] / [[sys+0x590]+0xa0] (H079 round-2 assertion); that these two objects are the "
          "ScenePatternSwitcher / SceneEditor is `likely` (switcher array +0x24 / count +0x2c match)")
    # TrackUnit per-block s10
    tu = D.seq(0x1ca964, 0x1ca98c)
    w = word_refs(im, 0x1ca58c); o = vt_owner(im, w[0][0]) if w else None
    check(tu == ["ldr r3, [r5, #0xf0]", "cmp r4, r3", "bhs #0x1ca98c", "ldr r3, [r5, #0xe8]", "ldr r0, [r3, r6]", "cmp r0, #0",
                 "beq #0x1ca98c", "ldr r3, [r0]", "ldr r3, [r3, #0x28]", "blx r3"] and o and o[3] == "9TrackUnit",
          "TrackUnit vt slot %s (0x1ca58c, vtable 0x864cac) calls manager s10 (vt+0x28) for every insert slot i < +0xb8 each "
          "audio block, before the slot's processor work: a reload request is applied at the next block" % (o[1] if o else "?"))
    if R2 and "prop_dispatched" in R2:
        d = R2["prop_dispatched"]
        by = {}
        for site, rec, off, tgt in d: by.setdefault(tgt, set()).add(site)
        R["dispatched"] = {k: sorted(v) for k, v in by.items()}
        P("    propagation-dispatched sites: %s" % json.dumps(R["dispatched"]))
        ie38 = R["dispatched"].get("0x11cf50", [])
        fp_slot14 = all(D.seq(int(a, 16) - 0xc, int(a, 16) + 4) == ["ldr r3, [r0]", "ldr r3, [r3, #0x38]", "vmov r2, s15", "blx r3"]
                        for a in ("0x1136bc", "0x11791c", "0x118890", "0x11a664"))
        lfo = [vt_owner(im, a) for a, v in word_refs(im, 0x131300)]
        lfo_ti = im.cstr(im.u32(im.u32(0x845034 - 0xc) + 4), 80) if word_refs(im, 0x131300) == [(0x845034, 0x131300)] else None
        check(R["dispatched"].get("0x11cfc0") == ["0x2f8178"] and "0x11cfc8" not in R["dispatched"] and
              sorted(ie38) == ["0x1136bc", "0x11791c", "0x118890", "0x11a664", "0x131318", "0x2f8020", "0x2f80cc"] and fp_slot14
              and lfo_ti and "LfoProcessor7setSync" in lfo_ti,
              "manager/IEffector-typed call sites reaching s42: IE+0x34 only 0x2f8178 (setEffectBypassMode); none via primary "
              "vt+0xa8. IE+0x38 (s43): 0x2f8020 / 0x2f80cc (the two getEffectBypassMode variants) plus 5 tag over-approximations, "
              "checked: 0x1136bc/0x11791c/0x118890/0x11a664 are effect slot-14 calls (this, idx, float in r2) on an array element, "
              "0x131318 is in %s::run (vtable word 0x845034), whose +0x14 object is an LfoProcessor" % lfo_ti)
        check(sorted(R["dispatched"].get("0x126394", [])) == ["0x11ca30", "0x11cbf8", "0x11cc2c", "0x11cc70", "0x126aa4", "0x126ae4",
                                                              "0x126b3c", "0x126b50"] and R["dispatched"].get("0x129b34") == ["0x1ca988"],
              "s51 (reload request) is reached only from the listener slots (0x11ca18, 0x11cbd4, 0x11cc08, 0x11cc3c, 0x126a74, 0x126ab4, "
              "0x126af4); s10 only from TrackUnit 0x1ca988")
        sl = D.seq(0x1136b0, 0x1136c0)
        R["s43_overapprox_check"] = sl
    # Master/Send: their s51 / s10 never reach 0x1129b4
    dc = im.direct_calls()
    def reach_calls(f, depth):
        seen = set(); work = [(f, 0)]
        st = im.starts()
        while work:
            g, dd = work.pop()
            if g in seen or dd > depth: continue
            seen.add(g); hi = st[bisect.bisect_right(st, g)]
            for s, t, k in dc:
                if g <= s < hi and k in ("bl", "b") and not (g <= t < hi): work.append((t, dd + 1))
        return seen
    ms = {nm: (BYPASS in reach_calls(f, 3)) for nm, f in (("master_s51", 0x121174), ("send_s51", 0x12de8c), ("base_s51", 0x11fdcc))}
    R["ms_reload_reaches_bypass"] = ms
    check(not any(ms.values()) and D.seq(0x11fcc8, 0x11fccc) == ["bx lr"],
          "Master/Send managers: s10 is `bx lr` (0x11fcc8) and their s51 reloads (0x121174 / 0x12de8c) reach 0x1129b4 by no direct "
          "call chain (depth 3): a Master/Send reload never re-applies bBypass; only s42 could write their +0x9c, which their "
          "processBlock never reads (F157)")
    return R


# ===================================================================================================================== C4 (emulation)
N = 64
KIND_IDX = {"chorus": 0, "flanger": 1, "peq": 2, "mmf": 3, "insert_delay": 4, "lofi": 5, "distortion": 6, "insert_compressor": 7,
            "phaser": 8}


def _emu_imports():
    import emu
    from emu import f2u, u2f
    import H083_enum_defaults as H83
    import H077_master_send_proc as H77
    import H044_effectbase_wrapper as H44
    return emu, f2u, u2f, H83, H77, H44


class BypassRig:
    """H083 Rig (real Insert processor + real IFPM ctor + real EffectData) extended: a second real EffectData in the stand-in holder
    (scene object 1), unified ordered log of manager->processor calls."""
    def __init__(self, two_eds=True):
        emu, f2u, u2f, H83, H77, H44 = _emu_imports()
        self.H77 = H77; self.H44 = H44; self.f2u = f2u; self.u2f = u2f
        r = H83.Rig("insert", "InsertFx0"); self.r = r; e = self.e = r.e; x = self.x = r.x
        self.m = r.m; self.h = r.h; self.ed = [r.ed]
        if two_eds:
            ed1 = e.malloc(H83.ED_SIZE, "new(0x64) prj::EffectData #2"); e.wr(ed1, b"\xcc" * H83.ED_SIZE)
            e.call(H83.ED_CTOR, ed1, r.J.string("InsertFx0"), e.malloc(0x200)); self.ed.append(ed1)
            e.w32(self.h + 0x10, ed1); e.w32(self.h + 0x54, 1)          # T[1] = 1 -> ED1 at holder + 4 + 0xc
        self.iw = e.u32(self.h + 8)
        self.log = []; self.recording = True
        objidx = {o: i for i, o in enumerate(x.objs)}
        def wrap(addr, kind):
            orig = e.watch.get(addr)
            def cb(em):
                if orig: orig(em)
                if not self.recording: return
                if kind == "s14":
                    o = em.r(0)
                    if o in objidx: self.log.append(("p", objidx[o], s32(em.r(1)), em.r(2)))
                elif kind == "fx": self.log.append(("fx", s32(em.r(1))))
                elif kind == "byp": self.log.append(("byp", em.r(1) & 0xff))
            e.watch[addr] = cb
            if orig is None: e.uc.hook_add(emu.UC_HOOK_CODE, e._h_watch, begin=addr, end=addr)
        for a in sorted(set(e.u32(e.u32(o) + 0x38) for o in x.objs)): wrap(a, "s14")
        wrap(H77.PROC["insert"]["setfx"], "fx"); wrap(BYPASS, "byp")
        self.eid = r.effect_id_for()
        x.s14 = []; r.clear(); self.log = []

    # ---- device-side actions (all REAL entries)
    def ui_bypass(self, v):          # IE+0x34 via the IEffector vtable (what 0x2f8178 does)
        ie = self.m + 0x14; self.e.call(self.e.u32(self.e.u32(ie) + 0x34), ie, v)
    def s42(self, v): self.e.call(S42, self.m, v)
    def get_bypass(self):
        ie = self.m + 0x14; return self.e.call(self.e.u32(self.e.u32(ie) + 0x38), ie)[0]
    def select(self, kind):         # s32 applyFxType (FX popup route, F171/F173)
        t = -1 if kind is None else KIND_IDX[kind]
        self.e.call(0x1287d4, self.m, self.eid[t] if t >= 0 else 0xffffffff)
    def edit_begin(self): sub = self.m + 0x10; self.e.call(self.e.u32(self.e.u32(sub) + 4 * 4), sub)          # ISceneEditListener s4
    def edit_end(self): sub = self.m + 0x10; self.e.call(self.e.u32(self.e.u32(sub) + 4 * 3), sub)            # s3: +0x24 := 1, s51(1)
    def scene_switch(self, new):    # switchSync: store the new index, then listener slot 3 (default -> slot 2) with the old index
        old = self.e.u32(self.iw); self.e.w32(self.iw, new)
        sub = self.m + 0xc; f = self.e.u32(self.e.u32(sub) + 0xc)
        self.e.call(f, sub, old, 0, new, stack_args=(0, 0))
    def pattern_switch(self):       # same scene: listener slot 5 (default -> slot 4 = bx lr)
        sub = self.m + 0xc; f = self.e.u32(self.e.u32(sub) + 0x14); cur = self.e.u32(self.iw)
        self.e.call(f, sub, cur, 0, cur, stack_args=(1, 0))
    def ed_write29(self, i, v): self.e.wr(self.ed[i] + 0x29, bytes([v]))   # stand-in: bBypass binder load 0x3589e8
    def s51(self, f): self.e.call(IFPM_S51, self.m, f)
    def s10(self): self.e.call(IFPM_S10, self.m, 0)
    def ed_select_type(self, i, kind):
        """Write a type into scene object i: switch index to i, s32, restore (the UI would do this while scene i is current)."""
        cur = self.e.u32(self.iw); self.e.w32(self.iw, i); self.select(kind); self.e.w32(self.iw, cur)
    def mgr_bytes(self): return dict(en24=self.e.rd(self.m + 0x24, 1)[0], rl25=self.e.rd(self.m + 0x25, 1)[0],
                                     ed29=[self.e.rd(d + 0x29, 1)[0] for d in self.ed], idx=self.e.u32(self.iw),
                                     p9c=self.e.rd(self.x.p + 0x9c, 1)[0])


def run_case(spec):
    """spec: name, sig, nblk, pre [(op,args)], ops {block: [(op, args...)]}. Per block: actions -> REAL s10 -> REAL processBlock;
    the logged manager->processor calls are replayed in order on the model before its process_block."""
    try:
        return _run_case(spec)
    except Exception as ex:   # pragma: no cover
        import traceback
        return dict(name=spec["name"], error="%s\n%s" % (ex, traceback.format_exc()[-1500:])), b""


def _apply(rig, op):
    k = op[0]
    if k == "ui": rig.ui_bypass(op[1])
    elif k == "s42": rig.s42(op[1])
    elif k == "sel": rig.select(op[1])
    elif k == "edb": rig.edit_begin()
    elif k == "ede": rig.edit_end()
    elif k == "scene": rig.scene_switch(op[1])
    elif k == "pat": rig.pattern_switch()
    elif k == "ed29": rig.ed_write29(op[1], op[2])
    elif k == "s51": rig.s51(op[1])
    elif k == "edtype": rig.ed_select_type(op[1], op[2])
    elif k == "knob": rig.e.call(0x126c0c, rig.m, rig.f2u(op[2]), op[1])    # IFPM s27 setParamValue(v, k): ED[k] = v + edit flag
    else: raise ValueError(op)


def _run_case(spec):
    t0 = time.time()
    rig = BypassRig(); H77 = rig.H77; H44 = rig.H44; f2u = rig.f2u; u2f = rig.u2f; x = rig.x
    m = H77.ModelProc("insert", x)
    nblk = spec.get("nblk", 160); ops = spec.get("ops", {})
    L, R = H77.signal(spec.get("sig", "noise"), nblk, seed=spec.get("seed", 5))
    res = dict(name=spec["name"], section=spec.get("section", "c4"), samples=0, exact=0, maxdiff=0.0, pdiff=0, evdiff=0, wdiff=0,
               first=None, calls=[], bytes=[], dry_after=[])
    blob = b""
    mut = spec.get("mutant")
    def replay(log):
        for l in log:
            if l[0] == "fx": m.P.set_fx_type(l[1])
            elif l[0] == "byp":
                if mut != "drop_byp": m.P.set_bypass(l[1])
            elif l[0] == "p":
                if l[1] in m.mms: m.set_param(l[1], l[2], u2f(l[3]))
    # pre-roll actions (block -1): logged and replayed too
    for op in spec.get("pre", []):
        rig.log = []; _apply(rig, op); replay(rig.log)
    x.ev = []; m.P.log = []; x.s14 = []
    for b in range(nblk):
        rig.log = []; x.ev = []; m.P.log = []; x.s14 = []
        for op in ops.get(b, []): _apply(rig, op)
        rig.s10()
        log = list(rig.log)
        if log or ops.get(b):
            res["calls"].append([b, [list(o) for o in ops.get(b, [])],
                                 [l if l[0] != "p" else ("p", l[1], l[2], "%08x" % l[3]) for l in log], rig.mgr_bytes()])
        replay(log)
        if mut == "ed_every_block":       # alternative: the stored bBypass of the current scene object is applied every block
            m.P.set_bypass(rig.mgr_bytes()["ed29"][rig.mgr_bytes()["idx"]])
        rig.recording = False
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        oL, oR = x.block(xL, xR)
        rig.recording = True
        mL = list(xL); mR = list(xR); m.P.process_block(mL, mR, N)
        blob += struct.pack("<%df" % N, *oL) + struct.pack("<%df" % N, *oR)
        res["dry_after"].append(sum(1 for a_, c_ in zip(oL + oR, xL + xR) if f2u(a_) == f2u(c_)))
        res.setdefault("wet_blocks", 0); res["wet_blocks"] += res["dry_after"][-1] < 2 * N
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["exact"] += 1
            else:
                d = abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf")
                res["maxdiff"] = max(res["maxdiff"], d)
                if res["first"] is None: res["first"] = ("out block %d" % b, a_, b_)
        ps_e, ps_m = x.pstate(), m.pstate()
        if ps_e != ps_m:
            res["pdiff"] += 1
            if res["first"] is None: res["first"] = ("pstate block %d" % b, ps_e, ps_m)
        F = H77.F
        ev_e = [e_ for e_ in x.ev] + [("feed7", x.idx_of[o], f2u(F(u2f(bits)))) for w, o, idx, bits in x.s14 if w == "feed" and idx == 7]
        ev_e += [("feed%d" % idx, x.idx_of[o], bits) for w, o, idx, bits in x.s14 if w == "feed" and idx != 7]
        ev_m = [l for l in m.P.log if l[0] != "feed7"] + [("feed7", l[1], f2u(l[2])) for l in m.P.log if l[0] == "feed7"]
        x.s14 = []
        if sorted(map(str, ev_e)) != sorted(map(str, ev_m)):
            res["evdiff"] += 1
            if res["first"] is None: res["first"] = ("events block %d" % b, ev_e, ev_m)
        for i in m.ebs:
            dd = H44.sdiff(H44.emu_state(x.e, x.objs[i]), H44.model_state(m.ebs[i]))
            if dd:
                res["wdiff"] += 1
                if res["first"] is None: res["first"] = ("wrapper %d block %d" % (i, b), dd[:3])
                break
        res["bytes"].append(rig.mgr_bytes()["p9c"])
    res["sha"] = sha(blob)[:16]
    res["ok"] = res["exact"] == res["samples"] and not res["pdiff"] and not res["evdiff"] and not res["wdiff"]
    res["final"] = rig.mgr_bytes(); res["get_bypass_final"] = rig.get_bypass()
    res["secs"] = round(time.time() - t0, 1)
    return res, blob


def cases():
    C = []
    KN = {"chorus": [(5, 0.7), (1, 0.6)], "lofi": [(0, 0.3), (5, 0.8)], "insert_delay": [(0, 0.05), (5, 0.6)],
          "insert_compressor": [(0, 0.2), (1, 0.9), (4, 0.8)], "peq": [(1, 0.8), (4, 0.2)], "distortion": [(0, 0.8), (5, 0.7)]}
    def mk(name, kind, sig, ops, nblk=140, pre=None, expect=None):
        p = ([("sel", kind)] + [("knob", k, v) for k, v in KN[kind]]) if kind else []
        if pre is not None: pre = [q for o in pre for q in ([o] + ([("knob", k, v) for k, v in KN[o[1]]] if o[0] == "sel" else []))]
        C.append(dict(name=name, sig=sig, nblk=nblk, pre=(pre if pre is not None else p), ops=ops, expect=expect or {}))
    # A: UI route (IE+0x34 adjustor -> s42) on, off
    for kind, sig in (("chorus", "noise"), ("lofi", "sine"), ("insert_delay", "impulse"), ("insert_compressor", "noise")):
        mk("A_ui_%s" % kind, kind, sig, {30: [("ui", 1)], 90: [("ui", 0)]}, expect={30: (1, [1, 0]), 90: (0, [0, 0])})
    # B: manager frozen (+0x24 = 0, SceneEditor 'prepare' slot): UI write ignored, then 'finished' slot re-enables + reloads
    for kind, sig in (("peq", "noise"), ("distortion", "sine")):
        mk("B_frozen_%s" % kind, kind, sig, {20: [("ui", 1)], 30: [("edb",)], 40: [("ui", 0)], 60: [("ede",)], 100: [("ui", 0)]},
           expect={20: (1, [1, 0]), 40: (1, [1, 0]), 60: (1, [1, 0]), 100: (0, [0, 0])})
    # C: stored bBypass applied by a reload (project-load stand-in: ED+0x29 := 1 then reload paths)
    mk("C_ed29_scene_reload_lofi", "lofi", "noise", {20: [("ed29", 0, 1)], 40: [("scene", 0)], 50: [("scene", 1)], 51: [("scene", 0)]},
       expect={20: (0, [1, 0]), 40: (0, [1, 0]), 50: (0, [1, 0]), 51: (1, [1, 0])})
    mk("C_ed29_edit_end_chorus", "chorus", "sine", {20: [("ed29", 0, 1)], 40: [("edb",)], 41: [("ede",)], 100: [("ed29", 0, 0), ("s51", 0)]},
       expect={20: (0, [1, 0]), 41: (1, [1, 0]), 100: (0, [0, 0])})
    mk("C_ed29_s51_delay", "insert_delay", "impulse", {20: [("ed29", 0, 1), ("s51", 0)], 80: [("ed29", 0, 0), ("s51", 0)]},
       expect={20: (1, [1, 0]), 80: (0, [0, 0])})
    # D: two scenes with different type and bBypass: scene switches change both
    mk("D_two_scenes_chorus_lofi", "chorus", "noise", {40: [("scene", 1)], 100: [("scene", 0)]},
       pre=[("edtype", 1, "lofi"), ("ed29", 1, 1), ("sel", "chorus")], nblk=160, expect={40: (1, [0, 1]), 100: (0, [0, 1])})
    mk("D_two_scenes_comp_off", "insert_compressor", "sine", {30: [("ui", 1)], 50: [("scene", 1)], 110: [("scene", 0)]},
       pre=[("edtype", 1, None), ("sel", "insert_compressor")], nblk=160, expect={30: (1, [1, 0]), 50: (0, [1, 0]), 110: (1, [1, 0])})
    # E / F: negatives (alternative explanations): pattern-only switch, stored byte without reload, reload request while frozen
    mk("E_pattern_switch_lofi", "lofi", "noise", {20: [("ed29", 0, 1)], 40: [("pat",)]}, expect={20: (0, [1, 0]), 40: (0, [1, 0])})
    mk("F_ed29_no_reload_peq", "peq", "sine", {20: [("ed29", 0, 1)]}, nblk=80, expect={20: (0, [1, 0])})
    mk("F_reload_while_frozen_chorus", "chorus", "noise", {20: [("ed29", 0, 1), ("edb",), ("s51", 0)], 60: [("s42", 0)]},
       nblk=100, expect={20: (0, [1, 0]), 60: (0, [1, 0])})
    base = {c["name"]: c for c in C}
    for nm, mu in (("A_ui_lofi", "drop_byp"), ("B_frozen_peq", "drop_byp"), ("D_two_scenes_chorus_lofi", "drop_byp"),
                   ("F_ed29_no_reload_peq", "ed_every_block"), ("E_pattern_switch_lofi", "ed_every_block"),
                   ("F_reload_while_frozen_chorus", "ed_every_block")):
        c = dict(base[nm]); c["name"] = "X_%s_%s" % (mu, nm); c["mutant"] = mu; c["section"] = "c4x"; C.append(c)
    return C


def ms_case(spec):
    """Master / Send: REAL manager s42 on the REAL processor: +0x9c is written, output identical to the same run without it."""
    emu, f2u, u2f, H83, H77, H44 = _emu_imports()
    out = {}
    for with_bypass in (0, 1):
        r = H83.Rig(spec["proc"], "MasterFx" if spec["proc"] == "master" else "SendFx"); e = r.e; x = r.x
        eid = r.effect_id_for(); e.call(H83.MGR[spec["proc"]]["s32"], r.m, eid[spec["t"]])
        for k, v in spec["knobs"]: e.call(0x11ce58, r.m, f2u(v), k)        # base s27: ED[k] = v and slot 29 at once
        L, R = H77.signal("noise", spec["nblk"], seed=9); blob = b""; p9c = []
        for b in range(spec["nblk"]):
            if b == 20 and with_bypass: e.call(S42, r.m, 1)
            oL, oR = x.block(L[N * b:N * b + N], R[N * b:N * b + N]); blob += struct.pack("<%df" % N, *oL) + struct.pack("<%df" % N, *oR)
            p9c.append(e.rd(x.p + 0x9c, 1)[0])
        wet = sum(1 for i in range(len(L)) if f2u(struct.unpack_from("<f", blob, 8 * N * (i // N) + 4 * (i % N))[0]) != f2u(L[i]))
        out[with_bypass] = dict(sha=sha(blob), p9c_end=p9c[-1], ed29=e.rd(e.u32(r.h + 0xc) + 0x29, 1)[0], wetL=wet)
    return dict(name=spec["name"], same=out[0]["sha"] == out[1]["sha"], runs=out)


def _worker(spec): return ms_case(spec) if spec.get("ms") else run_case(spec)


def c4(P, check, out, jobs):
    specs = cases()
    P("  %d cases (14 + 6 alternatives) + 3 Master/Send checks" % len(specs)); print("  (%d jobs)" % jobs, flush=True)
    if jobs > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(jobs) as pool: results = pool.map(_worker, specs, chunksize=1)
    else:
        results = [_worker(s) for s in specs]
    rows = []; blob = b""; nok = 0; nexp = 0; alldry = True
    mres = [(spec, r) for spec, (r, b) in zip(specs, results) if spec.get("mutant")]
    results = [rb for spec, rb in zip(specs, results) if not spec.get("mutant")]
    specs = [spec for spec in specs if not spec.get("mutant")]
    for spec, r in mres:
        P("  alternative %-48s %s exact %d/%d first %s" % (r["name"], "matches (BAD)" if r.get("ok") else "refuted", r.get("exact", 0),
                                                           r.get("samples", 0), str(r.get("first"))[:160]))
    check(all("error" not in r and not r["ok"] for _, r in mres),
          "c4 alternatives refuted: dropping the logged bypass calls from the model (3 cases) and applying the stored bBypass every "
          "block instead of only on reload (3 cases) both fail the comparison (%d/%d fail)" % (
              sum(1 for _, r in mres if not r.get("ok")), len(mres)))
    for spec, (r, b) in zip(specs, results):
        if "error" in r:
            P("  %-34s ERROR %s" % (r["name"], r["error"][:600])); rows.append(r); continue
        blob += b
        # expected +0x9c / ED+0x29 after each action block
        ok_exp = True; got = {}
        for blk, (p9c, ed29) in spec["expect"].items():
            g = r["bytes"][blk]; e29 = None
            for c in r["calls"]:
                if c[0] == blk: e29 = c[3]["ed29"]
            got[blk] = (g, e29)
            ok_exp &= (g == p9c and e29 == ed29)
        nexp += ok_exp; nok += r["ok"]
        calls = {c[0]: (c[1], [l[:2] if l[0] == "p" else l for l in c[2]][:4] + (["…%d" % len(c[2])] if len(c[2]) > 4 else []))
                 for c in r["calls"]}
        P("  %-32s %s samples %6d exact %6d p/ev/wr %d/%d/%d expect %s sha %s%s" % (
            r["name"], "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["pdiff"], r["evdiff"], r["wdiff"],
            "ok" if ok_exp else "MISMATCH %s" % got, r["sha"], "" if r["ok"] else " first %s" % str(r["first"])[:300]))
        for blk in sorted(calls):
            P("      b%-3d %s -> %s" % (blk, calls[blk][0], calls[blk][1]))
        # blocks with +0x9c = 1 for >= 3 blocks in a row: output must equal the dry input exactly (F157: dry from sample 132)
        byp3 = [i for i in range(3, len(r["bytes"])) if r["bytes"][i] == r["bytes"][i - 1] == r["bytes"][i - 2] == r["bytes"][i - 3] == 1]
        r["bypassed_blocks_dry"] = (sum(1 for i in byp3 if r["dry_after"][i] == 2 * N), len(byp3))
        alldry &= r["bypassed_blocks_dry"][0] == r["bypassed_blocks_dry"][1]
        P("      wet blocks %d; blocks starting >= 192 samples after the bypass write whose output == dry input: %d/%d" % (
            r["wet_blocks"], r["bypassed_blocks_dry"][0], r["bypassed_blocks_dry"][1]))
        rows.append({k: v for k, v in r.items() if k not in ("secs", "bytes", "dry_after")})
        rows[-1]["dry_samples_per_block"] = r["dry_after"]
    open(os.path.join(out, "c4_outputs.f32"), "wb").write(blob)
    ms_specs = [dict(ms=1, name="M_master_distortion_s42", proc="master", t=8, knobs=[(0, 0.8), (5, 0.7)], nblk=80),
                dict(ms=1, name="M_send_lofi_s42", proc="send", t=6, knobs=[(0, 0.3), (5, 0.8)], nblk=80),
                dict(ms=1, name="M_master_lofi_s42", proc="master", t=6, knobs=[(0, 0.3), (5, 0.8)], nblk=80)]
    if jobs > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(min(jobs, 3)) as pool: msr = pool.map(_worker, ms_specs, chunksize=1)
    else: msr = [_worker(s_) for s_ in ms_specs]
    for r in msr: P("  %-24s output identical with/without s42(1): %s; %s" % (r["name"], r["same"], json.dumps(r["runs"], sort_keys=True)))
    check(all(r["same"] and r["runs"][1]["p9c_end"] == 1 and r["runs"][1]["ed29"] == 1 and r["runs"][0]["wetL"] > 0 for r in msr),
          "Master/Send: the REAL s42 writes the processor's +0x9c and the EffectData bBypass (1), and the output is bit-identical to the "
          "run without it (effect audibly wet in both): a Master/Send bypass write is inaudible")
    rows.append(dict(ms_cases=msr))
    P("  c4: %d/%d cases bit-exact (outputs, processor state incl. +0x9c, slot 5-8 log, wrapper state, every block); %d/%d match "
      "the expected +0x9c / ED+0x29 after every action; outputs sha256 %s" % (nok, len(specs), nexp, len(specs), sha(blob)))
    check(nok == len(specs) and nexp == len(specs), "c4: every case bit-exact and every expected +0x9c / bBypass value observed")
    check(alldry, "c4: in every case, every block that starts >= 192 samples after +0x9c became 1 (and it stayed 1) outputs the dry "
                  "input bit-exactly (F157: dry from sample 132; the effect itself keeps running, F157)")
    return rows, sha(blob)


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H080"))
    ap.add_argument("--jobs", type=int, default=6); ap.add_argument("--only", default="c1,c2,c3,c4")
    ap.add_argument("--no-prop", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); only = set(a.only.split(","))
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = Image(); D = Dis(im)
    P("H080 bypass sources. target sha256 %s" % sha(im.data))
    if "c1" in only: P("\n== C1 caller semantics (static)"); J["c1"] = c1(im, D, P, check)
    if "c2" in only: P("\n== C2 who writes manager +0x24/+0x25 and EffectData +0x29 (static)"); J["c2"] = c2(im, D, P, check, a.out, not a.no_prop)
    if "c3" in only: P("\n== C3 callers traced to sources (static)"); J["c3"] = c3(im, D, P, check, J.get("c2"))
    if "c4" in only:
        P("\n== C4 emulation: real Insert processor + real IFPM + real EffectData, driven through the real entries")
        J["c4"], J["c4_sha"] = c4(P, check, a.out, a.jobs)
    J["fails"] = fails
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h080_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h080.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
