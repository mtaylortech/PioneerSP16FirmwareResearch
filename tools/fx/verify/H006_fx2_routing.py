#!/usr/bin/env python3
"""H006 — where does the 1.60 "FX2 on SAMPLE and THRU tracks" change live?  (cycle 024)

Own code. Static only: capstone/lief over the 1.60 target and the read-only 1.50 ELF baseline.
Masked (relocation-insensitive) function comparison 1.50 vs 1.60:
  * functions = .ARM.exidx starts (extent = next start), in both images;
  * per instruction word: branch imm24 masked (target kept as a call edge), pc-relative load/store/add imm12 masked,
    movw/movt imm16 masked when the pair forms an in-image address;
  * literal-pool words (words loaded pc-relative inside the function): pointer-like values (inside the image) masked,
    with the pointed-to C string compared when both sides point at printable strings; other values compared verbatim.
Function starts are refined with every unconditional `bl` target and every RTTI vtable entry. Global pairing is an
order-preserving alignment of the masked-hash sequences (difflib), with similarity pairing inside replace blocks and a
few explicit pins justified by matching call sites (PINS). Each pair is classified 'same' (masked identical), 'imm'
(identical structure, only immediates differ: field offsets / stack slots / constants) or 'struct'.
Emulation (unicorn via harness/lib/emu.py; darwin_ctr_fix installed first): small 1.60 and 1.50 routines only
(parameter-id maps, MasterTempoQualityManager slot 5), on our own fake objects; the 1.50 ELF is read, never written.

Usage: .venv/bin/python -B harness/H006_fx2_routing.py --out DIR
"""
import argparse, bisect, collections, csv, difflib, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "lib"))
import capstone, lief  # noqa: E402

T160 = os.path.join(ROOT, "target", "EP085_Main_R_fw160")
SHA160 = "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"
def _env_path(var, fallback, what):   # path scrub (research-notes/EDIT-LOG.md): was a private home-relative constant
    p = os.environ.get(var) or fallback
    if not os.path.exists(p):
        sys.exit("%s not found at %s: set the environment variable %s to %s" % (what, p, var, what))
    return p


T150 = _env_path("SP16_APP150_ELF", os.path.join(ROOT, "target", "app-1.50.elf"), "your own 1.50 application ELF")
SHA150 = "075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2"
XVER = _env_path("SP16_CLASSES_XVER_CSV", os.path.join(HERE, "..", "..", "..", "symbols", "classes-crossversion.csv"),
                 "symbols/classes-crossversion.csv of this repository")


class Img:
    def __init__(self, path, sha, tag):
        self.tag = tag
        self.data = open(path, "rb").read()
        assert hashlib.sha256(self.data).hexdigest() == sha, "%s hash mismatch" % tag
        e = lief.parse(path)
        self.segs = [(p.virtual_address, p.physical_size, p.file_offset) for p in e.segments
                     if p.type == lief.ELF.Segment.TYPE.LOAD]
        self.sec = {s.name: (s.virtual_address, s.virtual_address + s.size) for s in e.sections if s.name}
        self.lo = min(v for v, _, _ in self.segs)
        self.hi = max(v + s for v, s, _ in self.segs) + 0x500000   # include .bss-ish region for pointers
        self.md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        lo, hi = self.sec[".ARM.exidx"]; s = set()
        for x in range(lo, hi, 8):
            o = self.u32(x) & 0x7fffffff; o = o - 0x80000000 if o & 0x40000000 else o
            s.add((x + o) & 0xffffffff)
        t0, t1 = self.sec[".text"]
        self.exidx_starts = sorted(a for a in s if t0 <= a < t1)
        self.starts = self.exidx_starts + [t1]

    def refine(self, extra):
        """Add extra function starts (unconditional bl targets, vtable entries) for finer extents."""
        t0, t1 = self.sec[".text"]
        n = (t1 - t0) // 4
        W = struct.unpack_from("<%dI" % n, self.data, self.off(t0))
        s = set(self.exidx_starts)
        for i, w in enumerate(W):
            if (w >> 24) == 0xeb:
                imm = w & 0xffffff; imm = imm - 0x1000000 if imm & 0x800000 else imm
                tg = (t0 + 4 * i + 8 + imm * 4) & 0xffffffff
                if t0 <= tg < t1: s.add(tg)
        s |= set(a for a in extra if t0 <= a < t1 and a % 4 == 0)
        self.starts = sorted(s) + [t1]

    def off(self, va):
        for v, sz, o in self.segs:
            if v <= va < v + sz: return o + va - v
        return None

    def u32(self, va):
        o = self.off(va); return None if o is None else struct.unpack_from("<I", self.data, o)[0]

    def cstr(self, va, n=120):
        o = self.off(va)
        if o is None: return None
        e = self.data.find(b"\0", o, o + n)
        if e < 0: return None
        s = self.data[o:e]
        return s.decode("latin1") if len(s) >= 2 and all(32 <= c < 127 for c in s) else None

    def func_of(self, va):
        i = bisect.bisect_right(self.starts, va) - 1
        return (self.starts[i], self.starts[i + 1]) if 0 <= i < len(self.starts) - 1 else (None, None)

    def ptrlike(self, v):
        return self.lo <= v < self.hi

    # -------------------------------------------------------------------------------------------------
    def norm(self, s, e):
        """Masked token list for function [s,e) plus ordered call edges and literal (pointer) list."""
        c = self.__dict__.setdefault("_nc", {})
        if (s, e) not in c: c[(s, e)] = self._norm(s, e)
        return c[(s, e)]

    def _norm(self, s, e):
        words = struct.unpack_from("<%dI" % ((e - s) // 4), self.data, self.off(s))
        lits = set()
        for k, w in enumerate(words):   # pc-relative single loads: ldr/ldrb/ldrh/vldr families (imm12 / imm8)
            va = s + 4 * k
            if (w & 0x0e5f0000) == 0x041f0000 and (w >> 28) != 0xf:       # ldr{b} rX,[pc,#±imm12]
                imm = w & 0xfff; a = va + 8 + (imm if w & (1 << 23) else -imm)
                if s <= a < e: lits.add(a)
            elif (w & 0x0f3f0e00) == 0x0d1f0a00:                           # vldr sX/dX,[pc,#±imm8*4]
                imm = (w & 0xff) * 4; a = va + 8 + (imm if w & (1 << 23) else -imm)
                if s <= a < e: lits.add(a); lits.add(a + 4) if (w & 0x100) else None
        toks, calls, ptrs = [], [], []
        for k, w in enumerate(words):
            va = s + 4 * k
            if va in lits:
                if self.ptrlike(w):
                    st = self.cstr(w); toks.append(("P", st)); ptrs.append(w)
                else:
                    toks.append(("L", w))
                continue
            if s <= w < e and (w & 3) == 0:                                 # jump-table entry (absolute, in-function)
                toks.append(("J", w - s)); continue
            cond = w >> 28; op = (w >> 25) & 7
            if op == 5:                                                     # b/bl/blx imm
                imm = w & 0xffffff; imm = imm - 0x1000000 if imm & 0x800000 else imm
                tgt = (va + 8 + imm * 4 + (((w >> 23) & 2) if cond == 0xf else 0)) & 0xffffffff
                inside = s <= tgt < e
                toks.append(("B", w & 0xff000000, (tgt - s) if inside else None))
                if not inside: calls.append(tgt)
                continue
            if (w & 0x000f0000) == 0x000f0000 and op in (2, 0) and cond != 0xf and ((w >> 26) & 3) == 1:
                toks.append(("R", w & 0xfffff000)); continue                # ldr/str with Rn = pc (imm12 masked)
            if (w & 0x0fef0000) == 0x028f0000 and cond != 0xf:              # add/sub rX, pc, #imm
                toks.append(("R", w & 0xfffff000)); continue
            if (w & 0x0f3f0e00) == 0x0d1f0a00:                              # vldr pc-relative
                toks.append(("R", w & 0xffffff00)); continue
            if (w & 0x0ff00000) in (0x03000000, 0x03400000) and cond != 0xf:   # movw/movt: imm16 masked
                toks.append(("W", w & 0xfff0f000)); continue
            toks.append(("I", w))
        return toks, calls, ptrs

    def mhash(self, s, e):
        toks, _, _ = self.norm(s, e)
        return hashlib.sha1(repr([t if t[0] != "P" else ("P",) for t in toks]).encode()).hexdigest()

    def listing(self, s, e):
        return list(self.md.disasm(self.data[self.off(s):self.off(e)], s))


def vtables(I, cls):
    """Primary vtable address points of class `cls` via its RTTI name string (typeinfo name = len+name)."""
    nm = ("%d%s" % (len(cls), cls)).encode() + b"\0"
    res = []
    for m in re.finditer(re.escape(nm), I.data):
        sva = None
        for v, sz, o in I.segs:
            if o <= m.start() < o + sz: sva = v + m.start() - o
        if sva is None: continue
        for t in re.finditer(re.escape(struct.pack("<I", sva)), I.data):
            if t.start() % 4: continue
            ti = sva_ti = None
            for v, sz, o in I.segs:
                if o <= t.start() < o + sz: ti = v + t.start() - o - 4
            for u in re.finditer(re.escape(struct.pack("<I", ti)), I.data):
                if u.start() % 4 == 0 and struct.unpack_from("<i", I.data, u.start() - 4)[0] == 0:
                    for v, sz, o in I.segs:
                        if o <= u.start() < o + sz: res.append(v + u.start() - o + 4)
    return sorted(set(res))


def classify(A, B, x, y):
    """'same' (masked identical) / 'imm' (only immediates differ: offsets, stack slots, constants) / 'struct'."""
    ex, ey = A.func_of(x)[1], B.func_of(y)[1]
    if A.mhash(x, ex) == B.mhash(y, ey):
        return "same", 1.0
    ta, tb = A.norm(x, ex)[0], B.norm(y, ey)[0]
    if len(ta) == len(tb) and all(p[0] == q[0] and (p[0] != "I" or (p[1] & 0xfffff000) == (q[1] & 0xfffff000))
                                  and (p[0] not in "BJ" or True) for p, q in zip(ta, tb)) and \
            all(p == q for p, q in zip(ta, tb) if p[0] in "LJ"):
        return "imm", 1.0
    la = [skel("%s %s" % (i.mnemonic, i.op_str)) for i in A.listing(x, ex)]
    lb = [skel("%s %s" % (i.mnemonic, i.op_str)) for i in B.listing(y, ey)]
    if la == lb: return "imm", 1.0
    return "struct", difflib.SequenceMatcher(None, la, lb, autojunk=False).ratio()


def vt_slots(I, vt, maxn=400):
    t0, t1 = I.sec[".text"]; out = []
    for k in range(maxn):
        w = I.u32(vt + 4 * k)
        if w is None or not (t0 <= w < t1 or w == 0): break
        if k > 2 and w == 0: break
        out.append(w)
    return out


def vt_compare(A, B, va, vb):
    sa, sb = vt_slots(A, va), vt_slots(B, vb); rows = []
    for k in range(max(len(sa), len(sb))):
        x = sa[k] if k < len(sa) else None; y = sb[k] if k < len(sb) else None
        if x and y: c, r = classify(A, B, x, y)
        else: c, r = ("only1.50" if x else "only1.60"), 0
        rows.append((k, x, y, c, r))
    return rows


def rtti_all(I, path):
    """{mangled class name: [primary vtable address points]} from libstdc++ typeinfo objects (COPY-relocated vptrs)."""
    e = lief.parse(path); tiv = set()
    for sym in e.symbols:
        if sym.name in ("_ZTVN10__cxxabiv117__class_type_infoE", "_ZTVN10__cxxabiv120__si_class_type_infoE",
                        "_ZTVN10__cxxabiv121__vmi_class_type_infoE") and sym.value:
            tiv.add(sym.value + 8)
    words = {}
    for v, sz, o in I.segs:
        n = sz // 4
        for k, w in enumerate(struct.unpack_from("<%dI" % n, I.data, o)):
            words.setdefault(w, []).append(v + 4 * k)
    ti = {}
    for t in tiv:
        for a in words.get(t, []):
            nm = I.cstr(I.u32(a + 4) or 0, 300)
            if nm: ti[a] = nm
    out = collections.defaultdict(list)
    for a, nm in ti.items():
        for r in words.get(a, []):
            if I.u32(r - 4) == 0: out[nm].append(r + 4)
    return out


def load():
    return Img(T150, SHA150, "1.50"), Img(T160, SHA160, "1.60")


def vt_pairs():
    """{class: (vt150, vt160)} from the read-only cross-version class map."""
    out = {}
    with open(XVER) as f:
        for r in csv.DictReader(f):
            a, b = r.get("vtable_1.50"), r.get("vtable_1.60")
            if a and b: out[r["class"]] = (int(a, 16), int(b, 16))
    return out


def match_all(A, B, log):
    """Return {f150: f160} by unique masked hashes, then call-edge and vtable-slot propagation."""
    fa = {s: (s, A.starts[i + 1]) for i, s in enumerate(A.starts[:-1])}
    fb = {s: (s, B.starts[i + 1]) for i, s in enumerate(B.starts[:-1])}
    ha = collections.defaultdict(list); hb = collections.defaultdict(list)
    na, nb = {}, {}
    for s, (x, e) in fa.items():
        na[s] = A.norm(x, e); ha[A.mhash(x, e)].append(s)
    for s, (x, e) in fb.items():
        nb[s] = B.norm(x, e); hb[B.mhash(x, e)].append(s)
    m = {}
    for h, la in ha.items():
        lb = hb.get(h)
        if lb and len(la) == 1 and len(lb) == 1: m[la[0]] = lb[0]
    log("anchors (unique masked hash): %d of %d (1.50) / %d (1.60)" % (len(m), len(fa), len(fb)))
    # vtable seeds
    vts = vt_pairs(); seeds = 0
    for cls, (va, vb) in vts.items():
        for k in range(2, 400):
            x, y = A.u32(va + 4 * k), B.u32(vb + 4 * k)
            if x is None or y is None or x not in fa or y not in fb: break
            if x not in m and y not in m.values(): m[x] = y; seeds += 1
    log("vtable-slot seeds added: %d (classes with both vtables: %d)" % (seeds, len(vts)))
    # propagate along ordered call lists where the call counts agree
    inv = {v: k for k, v in m.items()}
    changed = True; rounds = 0
    while changed and rounds < 20:
        changed = False; rounds += 1
        for x, y in list(m.items()):
            ca, cb = na[x][1], nb[y][1]
            if len(ca) != len(cb):
                sm = difflib.SequenceMatcher(None, [("B" if t in fa else "X") for t in ca], [("B" if t in fb else "X") for t in cb], autojunk=False)
                pairs = [(ca[i + k], cb[j + k]) for i, j, n in sm.get_matching_blocks() for k in range(n)]
            else:
                pairs = list(zip(ca, cb))
            for p, q in pairs:
                if p in fa and q in fb and p not in m and q not in inv:
                    m[p] = q; inv[q] = p; changed = True
    log("after call propagation (%d rounds): %d pairs" % (rounds, len(m)))
    return m, na, nb, fa, fb


def same_masked(A, B, x, y, na, nb):
    ta, tb = na[x][0], nb[y][0]
    return [t if t[0] != "P" else ("P",) for t in ta] == [t if t[0] != "P" else ("P",) for t in tb]


def str_diffs(na, nb, x, y):
    """Pointer literals whose C-string contents differ (in order)."""
    pa = [t[1] for t in na[x][0] if t[0] == "P"]; pb = [t[1] for t in nb[y][0] if t[0] == "P"]
    return [(a, b) for a, b in zip(pa, pb) if a != b] + ([("len", (len(pa), len(pb)))] if len(pa) != len(pb) else [])


def skel(t):
    """Instruction text with every immediate replaced (structure only: offsets / stack slots / targets ignored)."""
    return re.sub(r"#[-+]?(0x[0-9a-f]+|\d+)", "#N", t)


def lines(I, s, e):
    """[(va, text)] for [s,e): literal-pool / jump-table words shown as DATA, branch targets and pc offsets masked."""
    c = I.__dict__.setdefault("_lc", {})
    if (s, e) in c: return c[(s, e)]
    toks = I.norm(s, e)[0]; out = []
    for k, t in enumerate(toks):
        va = s + 4 * k
        if t[0] in "PLJ":
            out.append((va, "DATA" + ("" if t[0] != "P" or not t[1] else ' "%s"' % t[1][:40]))); continue
        ins = list(I.md.disasm(I.data[I.off(va):I.off(va) + 4], va, 1))
        if not ins: out.append((va, ".word")); continue
        i = ins[0]; txt = "%s %s" % (i.mnemonic, i.op_str)
        if t[0] == "B": txt = re.sub(r"#0x[0-9a-f]+", "#ADDR" if t[2] is None else "#+0x%x" % t[2], txt)
        txt = re.sub(r"\[pc, #-?0x[0-9a-f]+\]", "[pc,#L]", txt)
        if t[0] == "W": txt = re.sub(r"#0x[0-9a-f]+|#\d+", "#IMM16", txt)
        out.append((va, txt))
    c[(s, e)] = out
    return out


def fdiff(A, B, x, ex, y, ey, maxl=40, structural=False, show=6):
    """Diff of masked instruction text (structural=True also replaces every immediate by #N)."""
    la, lb = lines(A, x, ex), lines(B, y, ey)
    key = skel if structural else (lambda t: t)
    sm = difflib.SequenceMatcher(None, [key(t) for _, t in la], [key(t) for _, t in lb], autojunk=False)
    res = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal": continue
        res.append("%s 1.50@0x%x(+%d) 1.60@0x%x(+%d)" % (op, la[i1][0] if i1 < len(la) else ex, i2 - i1,
                                                         lb[j1][0] if j1 < len(lb) else ey, j2 - j1))
        for a, t in la[i1:i2][:show]: res.append("  - 0x%x %s" % (a, t))
        for a, t in lb[j1:j2][:show]: res.append("  + 0x%x %s" % (a, t))
        if len(res) > maxl: res.append("  ..."); break
    return res, sm.ratio()


def align_pairs(A, B):
    """Order-preserving alignment of the two function lists by masked hash.
    Returns (pairs {f150: f160}, added_1.60 [..], removed_1.50 [..]). In replace blocks: equal-size → by index;
    otherwise greedy by structural similarity >= 0.5 within the block."""
    sa, sb = A.starts[:-1], B.starts[:-1]
    ha = [A.mhash(x, A.starts[i + 1]) for i, x in enumerate(sa)]
    hb = [B.mhash(y, B.starts[i + 1]) for i, y in enumerate(sb)]
    sm = difflib.SequenceMatcher(None, ha, hb, autojunk=False)
    pairs, added, removed = {}, [], []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1): pairs[sa[i1 + k]] = sb[j1 + k]
        elif op == "replace" and i2 - i1 == j2 - j1:
            for k in range(i2 - i1): pairs[sa[i1 + k]] = sb[j1 + k]
        elif op == "replace" and (i2 - i1) * (j2 - j1) <= 4000:
            cand = []
            for i in range(i1, i2):
                for j in range(j1, j2):
                    ka = [skel(t) for _, t in lines(A, sa[i], A.starts[i + 1])]
                    kb = [skel(t) for _, t in lines(B, sb[j], B.starts[j + 1])]
                    if abs(len(ka) - len(kb)) > max(len(ka), len(kb)) // 2: continue
                    cand.append((difflib.SequenceMatcher(None, ka, kb, autojunk=False).ratio(), i, j))
            ui, uj = set(), set()
            for r, i, j in sorted(cand, reverse=True):
                if r < 0.5 or i in ui or j in uj: continue
                pairs[sa[i]] = sb[j]; ui.add(i); uj.add(j)
            removed += [sa[i] for i in range(i1, i2) if i not in ui]
            added += [sb[j] for j in range(j1, j2) if j not in uj]
        else:
            removed += sa[i1:i2]; added += sb[j1:j2]
    return pairs, added, removed


def score(A, B, x, y):
    c, r = classify(A, B, x, y)
    return {"same": 3.0, "imm": 2.0}.get(c, r), c, r


def call_fix(A, B, pairs, log=print, rounds=3, sources=None):
    """Re-pair functions using ordered direct-call edges of already paired functions: where the k-th call of x and of
    pairs[x] are aligned (by mnemonic context) to targets (p, q) and q scores better for p than p's current partner."""
    for _ in range(rounds):
        inv = {v: k for k, v in pairs.items()}; changes = 0
        for x, y in list(pairs.items()):
            if sources is not None and x not in sources: continue
            ca = A.norm(x, A.func_of(x)[1])[1]; cb = B.norm(y, B.func_of(y)[1])[1]
            if not ca or not cb: continue
            cand = []
            sm = difflib.SequenceMatcher(None, [pairs.get(t, -t) for t in ca], cb, autojunk=False)
            for op, i1, i2, j1, j2 in sm.get_opcodes():
                if op == "replace" and i2 - i1 == j2 - j1: cand += list(zip(ca[i1:i2], cb[j1:j2]))
            for p, q in cand:
                if A.func_of(p)[0] != p or B.func_of(q)[0] != q: continue
                cur = pairs.get(p)
                if cur == q: continue
                sn = score(A, B, p, q)
                if sn[0] < 0.6: continue
                so = score(A, B, p, cur)[0] if cur else -1
                other = inv.get(q); sq = score(A, B, other, q)[0] if other else -1
                if sn[0] > so and sn[0] > sq:
                    if cur: inv.pop(cur, None)
                    if other: pairs.pop(other, None)
                    pairs[p] = q; inv[q] = p; changes += 1
        log("call_fix round: %d re-pairings" % changes)
        if not changes: break
    return pairs


# =====================================================================================================================
# cycle-024 analysis
PINS = {0x126c78: 0x12864c}   # InsertFxParameterManager ctor: called at 1.50 0x1afbc8 / 1.60 0x1bbda0 in constructTrack

FX_CLASS_RE = re.compile(r"^(\d+)(EffectBase|Chorus|Flanger|ParametricEqualizer|MultiModeFilter|InsertFxDelay|LoFi|"
                         r"Distortion|InsertFxCompressor|FxCompressor|SendFxCompressor|Phaser|Ducker|SendFxDelay|"
                         r"SendFxReverb|Reverb9NXSBase|PerformanceFxLoFi|c_effect_base|c_chorus|c_flanger|c_distortion|"
                         r"DelayEchoBase\\w*|FxProcessorBase|InsertFxProcessor|MasterFxProcessor|SendFxProcessor|"
                         r"CompositeFxUnit|MasterFxUnit|SendFxUnit|TrackUnit|MultiTrackUnit|MasterOutUnit|"
                         r"OutputSelector|Pan|Volume|VolumeFader|VolumeKnob|Mute|SimpleTwoMixUnit|"
                         r"FxParameterManagerBase|InsertFxParameterManager|MasterFxParameterManager|"
                         r"SendFxParameterManager|MasterTempoQualityManager|LfoProcessor|EffectInOutGain)$")

# DSP entry points / kernels already modelled (kb/functions.md, 1.60)
DSP = [(0x106de4, "EffectBase slot 18 dispatcher"), (0x106c88, "EffectBase post-stage HPF"), (0x10770c, "EffectBase copy-back"),
       (0xfc0f4, "LoFi s25"), (0xfbf64, "LoFi chain"), (0xfb6e4, "LoFi preamp"), (0xfaf28, "LoFi crusher"),
       (0xfbb70, "LoFi filter"), (0xe16dc, "IirFilter process"), (0xfb20c, "LoFi param update"),
       (0x108ee4, "MMF s25"), (0x108808, "MMF filter"), (0xe89f0, "GainRamp"),
       (0x10ae70, "PEQ s25"), (0x10c208, "PEQ band"), (0xe34d8, "IirFilter2 process"),
       (0x10d630, "Phaser s25"), (0x10d260, "Phaser block"), (0x10cf40, "Phaser allpass kernel"), (0x101bdc, "Osc process"),
       (0x115d70, "Chorus s25"), (0xfe710, "c_chorus s19"), (0x115f58, "Flanger s25"), (0xff9ac, "c_flanger s19"),
       (0x115d48, "Distortion s25"), (0xfa78c, "c_distortion process"),
       (0x102cc0, "InsertFxDelay s25"), (0x102d3c, "InsertFxDelay core s33"), (0xf438c, "SteppedIirFilter process"),
       (0xe1490, "Iir1stOrder process"),
       (0xf8718, "InsertFxCompressor s25"), (0xf8270, "SendFxCompressor s25"), (0xf8c40, "FxCompressor gain stage"),
       (0xf6ef4, "Ducker s25"), (0x104e98, "SendFxDelay s25"), (0x104a30, "SendFxDelay core"),
       (0x111730, "SendFxReverb s25"), (0xfc434, "PerformanceFxLoFi s25"),
       (0x116860, "InsertFxProcessor processBlock"), (0x112acc, "MasterFxProcessor processBlock"),
       (0x119994, "SendFxProcessor processBlock"), (0xe8228, "insert post-effect mix"),
       (0x11735c, "InsertFxProcessor setFxType"), (0x118b0c, "InsertFxProcessor ctor")]

C2 = [(0x1aa808, "CompositeFxUnit ctor"), (0x1a94cc, "CompositeFxUnit processBlock"), (0x1a9888, "FX-mode method (tables)"),
      (0x1a9c54, "FX-mode task"), (0x1aa060, "routing handler 1"), (0x1aa240, "routing handler 2"),
      (0x11cafc, "FxParameterManagerBase setDisabled s9"), (0x112a08, "FxProcessorBase setFlag9e"),
      (0x1b3068, "SendFxUnit processBlock"), (0x1b1b80, "MasterFxUnit processBlock"), (0x1b2150, "MasterOutUnit processBlock")]

AUDIO = [(0x1ca58c, "TrackUnit processBlock"), (0x1cb584, "TrackUnit setTrackType"), (0x1cb034, "TrackData type string -> enum"),
         (0x1ca0dc, "TrackUnit setRoutingMode"), (0x1ca218, "TrackUnit slot 101"), (0x1c9874, "TrackUnit addInsert"),
         (0x1cceb0, "TrackUnit ctor"), (0x1c67e4, "MultiTrackUnit ctor"), (0x1c4ff8, "MultiTrackUnit processBlock"),
         (0x1c12a0, "HexaTrackAudioSystem processBlock"), (0x1bacec, "constructTrack"), (0x1bc8d4, "buildGraph s55"),
         (0xe6b8c, "OutputSelector processBlock"), (0xe6ff4, "OutputSelector setSelection")]

C3 = [(0x29aa98, "TrackMenuVC: param/destination label (id 100/200 split)"), (0x29af60, "TrackMenuVC: item -> view name"),
      (0x29ccac, "TrackMenuVC: popupCallback FX image update"), (0x29d0dc, "TrackMenuVC: track-menu refresh (FX images)"),
      (0x12864c, "InsertFxParameterManager ctor"), (0x129b34, "InsertFxParameterManager s10 per-block update"),
      (0x126320, "IFPM s57 id -> effect index"), (0x12633c, "IFPM s58 id -> sub-slot"), (0x1287a4, "IFPM id -> FX slot (new)"),
      (0x1a8e68, "MasterTempoQualityManager s5"), (0x1a91b0, "MTQ manager addInsertProcessor (new)"),
      (0x47a314, "TrackMenuView setFx1Image"), (0x47a3ec, "TrackMenuView setFx2Image"), (0x300f70, "ModelInterface getFxType(slot)"),
      (0x1f0bec, "FxSelectPopupWidgetController s13"), (0x55904, "static init: modulation destination name table")]


def direct_callers(I, tg):
    t0, t1 = I.sec[".text"]; n = (t1 - t0) // 4
    W = struct.unpack_from("<%dI" % n, I.data, I.off(t0)); out = []
    for i, w in enumerate(W):
        if ((w >> 24) & 0xf) in (0xa, 0xb) and (w >> 28) != 0xf:
            imm = w & 0xffffff; imm = imm - 0x1000000 if imm & 0x800000 else imm
            if (t0 + 4 * i + 8 + imm * 4) & 0xffffffff == tg: out.append(t0 + 4 * i)
    return out


def imm_detail(A, B, x, y, n=12):
    """For an 'imm' pair: the differing instruction texts (first n) and the set of (old, new) immediate pairs."""
    la, lb = lines(A, x, A.func_of(x)[1]), lines(B, y, B.func_of(y)[1]); out = []; pairs = collections.Counter()
    for (a, t), (b, u) in zip(la, lb):
        if t != u:
            out.append("0x%x %s | 0x%x %s" % (a, t, b, u))
            ia = re.findall(r"#(-?0x[0-9a-f]+|-?\d+)", t); ib = re.findall(r"#(-?0x[0-9a-f]+|-?\d+)", u)
            for p, q in zip(ia, ib):
                if p != q: pairs[(int(p, 0), int(q, 0))] += 1
    return out[:n], pairs


def bss_string_name(I, addr):
    """Name of a static juce::String object: the C string loaded next to the literal `addr` in its static initialiser."""
    t0, t1 = I.sec[".text"]
    pat = struct.pack("<I", addr)
    for m in re.finditer(re.escape(pat), I.data):
        if m.start() % 4: continue
        va = [v + m.start() - o for v, sz, o in I.segs if o <= m.start() < o + sz]
        if not va or not (t0 <= va[0] < t1): continue
        s, e = I.func_of(va[0])
        L = lines(I, s, e)
        ins = I.listing(s, e)
        for k, i in enumerate(ins):
            mm = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", i.op_str)
            if i.mnemonic == "ldr" and mm and i.address + 8 + int(mm.group(2), 0) == va[0]:
                for j in range(max(0, k - 3), min(len(ins), k + 4)):
                    m2 = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", ins[j].op_str)
                    if ins[j].mnemonic == "ldr" and m2 and m2.group(1) == "r1":
                        st = I.cstr(I.u32(ins[j].address + 8 + int(m2.group(2), 0)) or 0)
                        if st: return st
    return None


def item_view_table(I, s, strcopy):
    """TrackMenuViewController item-id -> view-name table built by the function's static-local initialiser.
    Linear symbolic walk (harness/lib/symwalk.py): ids are constant stores to static T+8k, names are String copies
    (strcopy(dest = T+8k+4, src = static juce::String)); src names via bss_string_name."""
    import symwalk
    copies = []
    def h(st, site):
        copies.append((st.r.get("r0"), st.r.get("r1"))); return None
    I.disasm = lambda lo, hi: I.listing(lo, hi)
    st = symwalk.State()
    symwalk.Walker(I, {strcopy: h}, strings=False).walk(s, I.func_of(s)[1], st, fork=False)
    rows = []
    for d, src in copies:
        if d and d[0] == "lit" and src and src[0] == "lit" and (d[1] - 4) in st.statics:
            rows.append((st.statics[d[1] - 4] - (1 << 32) if st.statics[d[1] - 4] & 0x80000000 else st.statics[d[1] - 4],
                         d[1], src[1]))
    return rows


def run_emulation(log):
    """E1: parameter-id maps (1.50 and 1.60); E2: MasterTempoQualityManager slot 5 (1.50 and 1.60)."""
    import emu as EM
    res = {}

    def make(version):
        if version == "1.60": return EM.Emu(libs=())
        old = (EM.TARGET, EM.SHA)
        EM.TARGET, EM.SHA = T150, SHA150          # read-only 1.50 baseline; restored immediately
        try: return EM.Emu(libs=())
        finally: EM.TARGET, EM.SHA = old

    # ---- E1 -------------------------------------------------------------------------------------------------------
    fns = {"1.50": {"s57": 0x124950, "s58": 0x12496c}, "1.60": {"s57": 0x126320, "s58": 0x12633c, "slot": 0x1287a4}}
    for ver, fs in fns.items():
        e = make(ver); tab = {}
        for nm, fa in fs.items():
            col = []
            for pid in range(0, 300):
                r0, _ = e.call(fa, 0, pid) if nm != "slot" else e.call(fa, 0, pid)
                col.append(r0 - (1 << 32) if r0 & 0x80000000 else r0)
            tab[nm] = col
        res["E1_" + ver] = tab
    a, b = res["E1_1.50"], res["E1_1.60"]
    rng = lambda c, lo, hi: [c[i] for i in range(lo, hi)]
    e1 = {
        "1.50 s57/s58 ids 100-155 == 1.60": rng(a["s57"], 100, 156) == rng(b["s57"], 100, 156) and rng(a["s58"], 100, 156) == rng(b["s58"], 100, 156),
        "1.50 ids 200-255 -> -1": all(v == -1 for v in rng(a["s57"], 200, 256) + rng(a["s58"], 200, 256)),
        "1.60 ids 200-255 == ids 100-155": rng(b["s57"], 200, 256) == rng(b["s57"], 100, 156) and rng(b["s58"], 200, 256) == rng(b["s58"], 100, 156),
        "1.60 ids 156-199 -> -1": all(v == -1 for v in rng(b["s57"], 156, 200) + rng(b["s58"], 156, 200)),
        "1.60 slot(id): 100-155 -> 0, 200-255 -> 1, else -1": all(b["slot"][i] == (0 if 100 <= i <= 155 else 1 if 200 <= i <= 255 else -1) for i in range(300)),
        "outside 100..255 -> -1 (both)": all(a["s57"][i] == -1 and b["s57"][i] == -1 for i in list(range(0, 100)) + list(range(256, 300))),
    }
    res["E1_checks"] = e1
    for k, v in e1.items(): log("  E1 %-52s %s" % (k, "PASS" if v else "FAIL"))

    # ---- E2: MasterTempoQualityManager slot 5 ------------------------------------------------------------------------
    from unicorn import UC_PROT_ALL
    from unicorn import arm_const as AC
    lay = {"1.50": dict(fn=0x19d258, en=0x94, obj80=0x80, l1=0x84, state=0x90, l2=None, log=()),
           "1.60": dict(fn=0x1a8e68, en=0xa0, obj80=0x80, l1=0x84, l2=0x90, state=0x9c, log=(0x64a3fc, 0x635768, 0x647ca0, 0x627f38))}
    CODE = 0x60000000

    def stub(e, at, val):
        e.w32(at, 0xe3e00000 if val == -1 else 0xe3a00000 | (val & 0xff)); e.w32(at + 4, 0xe12fff1e)   # mov/mvn r0,#v; bx lr
        return at

    def mkobj(e, slot_fn):
        vt = e.malloc(0x200); o = e.malloc(0x10); e.w32(o, vt)
        for k, fa in slot_fn.items(): e.w32(vt + 4 * k, fa)
        return o

    def arr(e, base, off, objs):
        buf = e.malloc(4 * max(1, len(objs)))
        for i, o in enumerate(objs): e.w32(buf + 4 * i, o)
        e.w32(base + off, buf); e.w32(base + off + 4, len(objs)); e.w32(base + off + 8, len(objs))

    cases = []
    for ver in ("1.50", "1.60"):
        L = lay[ver]
        for rev in (0, 1):
          for n_play in (0, 6, 12, 13, 16):
            for n_fx in (0, 8, 16, 24, 32):
                if ver == "1.50" and n_fx not in (0, 32): continue
                e = make(ver)
                e.uc.mem_map(CODE, 0x1000, UC_PROT_ALL)
                ret0, ret1, retm1, nop = stub(e, CODE, 0), stub(e, CODE + 8, 1), stub(e, CODE + 16, -1), CODE + 28
                e.w32(nop, 0xe12fff1e)
                notified = []
                e.uc.mem_map(CODE + 0x1000, 0x1000, UC_PROT_ALL)
                e.w32(CODE + 0x1000, 0xe12fff1e)
                e.add_watch(CODE + 0x1000, lambda em: notified.append(em.r(1)))
                logs = []
                for fa in L["log"]:
                    def skip(em, fa=fa):
                        if fa == 0x64a3fc: logs.append(em.r(1))
                        em.uc.reg_write(AC.UC_ARM_REG_PC, em.uc.reg_read(AC.UC_ARM_REG_LR))
                    e.add_watch(fa, skip)
                m = e.malloc(0x100)
                e.wr(m, b"\0" * 0x100)
                e.uc.mem_write(m + L["en"], b"\1")
                e.w32(m + L["state"], 7)                   # neither 0 nor 1: force the change/notify path
                players = [mkobj(e, {3: ret1, 2: CODE + 0x1000}) for _ in range(n_play)]
                if ver == "1.50":
                    arr(e, m, L["l1"], players)
                else:
                    fx = [mkobj(e, {46: (ret0 if i % 2 else ret1)}) for i in range(n_fx)]  # active insert FX (index >= 0)
                    fx += [mkobj(e, {46: retm1}) for _ in range(3)]                       # three "Off" inserts (-1)
                    arr(e, m, L["l1"], fx); arr(e, m, L["l2"], players)
                # +0x80 = CompositeFxUnit-like object: +0x90 SendFxUnit(+0x8c proc), +0x8c MasterFxUnit(+0x84 proc);
                # the real helper (1.50 0x19dec0 / 1.60 0x1a9c78) asks proc slot 46 (current FX index) == 1 (Reverb)
                cfx = e.malloc(0x100); e.wr(cfx, b"\0" * 0x100)
                sfu = e.malloc(0x100); e.wr(sfu, b"\0" * 0x100); mfu = e.malloc(0x100); e.wr(mfu, b"\0" * 0x100)
                e.w32(sfu + 0x8c, mkobj(e, {46: ret1 if rev else ret0})); e.w32(mfu + 0x84, mkobj(e, {46: retm1}))
                e.w32(cfx + 0x90, sfu); e.w32(cfx + 0x8c, mfu); e.w32(m + L["obj80"], cfx)
                if ver == "1.50":     # 1.50 slot 5 has no insert-FX list: put the FX count nowhere (must not matter)
                    pass
                e.call(L["fn"], m)
                st = e.u32(m + L["state"])
                cases.append({"ver": ver, "reverb": rev, "players": n_play, "active_fx": n_fx, "state": st, "notified": len(notified),
                              "log": [e.rd(x, 40).split(b"\0")[0].decode("latin1") for x in logs]})
    res["E2"] = cases
    for c in cases:
        exp = (1 if c["reverb"] and c["players"] > 12 else 0) if c["ver"] == "1.50" else \
            (1 if 8 * c["reverb"] + c["active_fx"] + 2 * c["players"] > 32 else 0)
        c["expected"] = exp
        log("  E2 %s reverb=%d players=%2d activeFX=%2d -> quality=%s (expected %s) notified=%d %s %s" % (
            c["ver"], c["reverb"], c["players"], c["active_fx"], "Low" if c["state"] else "High", "Low" if exp else "High",
            c["notified"], c["log"][:1], "PASS" if c["state"] == exp and c["notified"] == c["players"] else "FAIL"))
    res["E2_pass"] = all(c["state"] == c["expected"] and c["notified"] == c["players"] for c in cases)
    return res


def run_track_emulation(log):
    """E3: the REAL 1.60 TrackUnit::processBlock 0x1ca58c (H009 rig, logging fake inserts) with n_inserts = 1 (the 1.50
    config) and 2 (the 1.60 config); outputs compared with harness/models/track_mix.py (inserts in slot order)."""
    import random, zlib
    sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
    import H009_track_mix as H9
    M = H9.M; out = {}
    for nins, fx in ((1, [H9.fx_shape]), (2, [H9.fx_shape, H9.fx_clip])):
        e = H9.new_emu(); fk = H9.Fakes(e)
        t = H9.TrackRig(e, fk, n_inserts=nins, insert_fx=fx); t.main_on = 1
        mt = M.Track(fader=100, pan=0, send=100); t.set(fader=100, pan=0, send=100)
        mrev = M.Track(fader=100, pan=0, send=100)
        rng = random.Random(zlib.crc32(b"H006-%d" % nins)); mism = mrev_mism = tot = 0; diff_vs_1 = 0; fl = []
        order = None
        for b in range(24):
            sl = H9.sig("noise", b, 0, rng); sr = H9.sig("noise", b, 1, rng)
            t.events = []; t.src = (sl, sr); o = t.block()
            if b == 0: order = [ev[0] for ev in t.events if "Insert" in ev[0]]
            mo = mt.process(sl, sr, inserts=fx); mr = mrev.process(sl, sr, inserts=fx[::-1])
            for c in range(6):
                tot += H9.N
                mism += sum(1 for x, y in zip(H9.bits(o[c]), H9.bits(mo[c])) if x != y)
                mrev_mism += sum(1 for x, y in zip(H9.bits(o[c]), H9.bits(mr[c])) if x != y)
                fl.extend(o[c])
        out[nins] = dict(samples=tot, model_mismatch=mism, reversed_order_mismatch=mrev_mism, order=order,
                         sha=hashlib.sha256(struct.pack("<%df" % len(fl), *fl)).hexdigest())
        log("  E3 n_inserts=%d: %d samples, model mismatches %d, reversed-order mutant mismatches %d; insert calls %s" % (
            nins, tot, mism, mrev_mism, order))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H006"))
    ap.add_argument("--no-emu", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []

    def log(s=""): print(s); rep.append(s)

    def check(name, ok):
        log("  [%s] %s" % ("PASS" if ok else "FAIL", name))
        if not ok: fails.append(name)

    A, B = load()
    log("H006 — 1.50 (%s…) vs 1.60 (%s…)" % (SHA150[:8], SHA160[:8]))
    ra, rb = rtti_all(A, T150), rtti_all(B, T160)
    log("RTTI classes: 1.50 %d, 1.60 %d, common %d; only 1.50: %d, only 1.60: %d" % (
        len(ra), len(rb), len(set(ra) & set(rb)), len(set(ra) - set(rb)), len(set(rb) - set(ra))))
    J["classes_only_160"] = sorted(set(rb) - set(ra)); J["classes_only_150"] = sorted(set(ra) - set(rb))
    vte = lambda I, r: set(x for v in sum(r.values(), []) for x in vt_slots(I, v) if x)
    A.refine(vte(A, ra)); B.refine(vte(B, rb))
    pairs, added, removed = align_pairs(A, B)
    for x, y in PINS.items():
        for k in [k for k, v in pairs.items() if v == y]: pairs.pop(k)
        pairs[x] = y
        if y in added: added.remove(y)
    inv = {v: k for k, v in pairs.items()}
    cls = {x: classify(A, B, x, y) for x, y in pairs.items()}
    cnt = collections.Counter(c for c, _ in cls.values())
    log("functions: 1.50 %d, 1.60 %d; pairs %d (same %d, imm %d, struct %d); 1.60-only %d, 1.50-only %d" % (
        len(A.starts) - 1, len(B.starts) - 1, len(pairs), cnt["same"], cnt["imm"], cnt["struct"], len(added), len(removed)))
    J["counts"] = dict(cnt, pairs=len(pairs), added=len(added), removed=len(removed))
    with open(os.path.join(a.out, "function_pairs.tsv"), "w") as f:
        f.write("f160\tf150\tclass\tratio\n")
        for x, y in sorted(pairs.items(), key=lambda t: t[1]):
            f.write("0x%x\t0x%x\t%s\t%.3f\n" % (y, x, cls[x][0], cls[x][1]))
        for y in added: f.write("0x%x\t-\tonly1.60\t0\n" % y)
        for x in removed: f.write("-\t0x%x\tonly1.50\t0\n" % x)

    def status(y):
        if y not in pairs.values() and y not in added:
            y = B.func_of(y)[0]
        x = inv.get(y)
        if x is None: return None, ("only1.60" if y in added else "unpaired"), 0.0
        c, r = cls[x]; return x, c, r

    def table(title, items):
        log(title); rows = []
        for y, nm in items:
            x, c, r = status(y)
            log("  1.60 0x%-7x 1.50 %-9s %-8s %.3f  %s" % (y, ("0x%x" % x) if x else "-", c, r, nm))
            rows.append({"f160": hex(y), "f150": hex(x) if x else None, "class": c, "ratio": round(r, 3), "name": nm})
        return rows

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C1: what FX1/FX2 and the track type are ==")
    s150 = set(m.group().decode() for m in re.finditer(rb"[\x20-\x7e]{4,}", A.data))
    s160 = set(m.group().decode() for m in re.finditer(rb"[\x20-\x7e]{4,}", B.data))
    fx1 = sorted(x for x in s160 - s150 if x.startswith("FX1 > ")); fx2 = sorted(x for x in s160 - s150 if x.startswith("FX2 > "))
    fx0 = sorted(x for x in s150 - s160 if x.startswith("FX > "))
    log("  strings new in 1.60: %d 'FX1 > …', %d 'FX2 > …'; gone: %d 'FX > …'; 'FX2' alone: 1.50 %s, 1.60 %s" % (
        len(fx1), len(fx2), len(fx0), b"\0FX2\0" in A.data, b"\0FX2\0" in B.data))
    J["C1_strings"] = {"FX1>": len(fx1), "FX2>": len(fx2), "FX>": len(fx0)}
    check("C1 strings: 'FX > x' list (1.50) became 'FX1 > x' + 'FX2 > x' (1.60), same suffixes",
          sorted(x[6:] for x in fx1) == sorted(x[5:] for x in fx0) and len(fx2) >= len(fx1) - 8)
    trows = item_view_table(B, 0x29af60, 0x627ba0); trows150 = item_view_table(A, 0x298e0c, inv[0x627ba0])
    empty160, empty150 = 0xf6e5cc, None
    log("  TrackMenuViewController item -> view table (1.60 0x29af60 / 1.50 0x298e0c): %d / %d rows" % (len(trows), len(trows150)))
    nm_ = lambda I, l: (lambda n: n if n and n.endswith("View") else "<FX-slot view, resolved at run time>")(bss_string_name(I, l))
    t160 = [(i, nm_(B, l)) for i, d, l in trows]; t150 = [(i, nm_(A, l)) for i, d, l in trows150]
    log("   1.60: " + ", ".join("%d:%s" % (i, (n or "''").replace("View", "")) for i, n in t160))
    log("   1.50: " + ", ".join("%d:%s" % (i, (n or "''").replace("View", "")) for i, n in t150))
    J["C1_item_table_160"] = t160; J["C1_item_table_150"] = t150
    check("C1 item->view table identical in 1.50 and 1.60 (ids/names)", t160 == t150)
    # TrackData type string -> enum (0x1cb034) and TrackUnit +0x614
    strs = [t[1] for t in B.norm(0x1cb034, B.func_of(0x1cb034)[1])[0] if t[0] == "P" and t[1]]
    log("  track type: TrackUnit 0x1cb034 compares TrackData+0x24 String with %s (+ static 'Thru' 0x859acc) -> 0/1/2;"
        " setTrackType 0x1cb584 stores +0x614" % strs)
    # insert manager ctor: slot index
    log("  constructTrack insert loop: 1.50 IFPM ctor 0x126c78(this, track, cfg, proc) / 1.60 0x12864c(this, SLOT, track, cfg, proc)")
    sa_ = [i for i in A.listing(0x126c78, 0x126cb0) if i.op_str in ("r5, [r4, #0x3c]",)]
    sb_ = [i for i in B.listing(0x12864c, 0x128700) if i.op_str in ("r5, [r4, #0x3c]", "r6, [r4, #0x40]")]
    log("   1.50 +0x3c <- r1 (%d store); 1.60 +0x3c <- r1 = slot index, +0x40 <- r2 = track (%d stores); new size 0x94 -> 0x98" % (len(sa_), len(sb_)))
    check("C1 1.50 caller passes track index as r1, 1.60 passes loop index r6 as r1",
          any(i.op_str == "r1, [sp, #0x18]" for i in A.listing(0x1afbb8, 0x1afbbc)) and
          any(i.op_str == "r1, r6" for i in B.listing(0x1bbd8c, 0x1bbd90)))
    check("C1 IFPM allocation size 0x94 (1.50) -> 0x98 (1.60)",
          any(i.op_str == "r0, #0x94" for i in A.listing(0x1afbb0, 0x1afbb4)) and any(i.op_str == "r0, #0x98" for i in B.listing(0x1bbd84, 0x1bbd88)))
    # insert count value: LiveSamplerApplication builds the HexaTrackAudioSystem config on its stack (sp+0x58..0xb7, passed as
    # r1-r3 + 0x54 stack bytes) and AudioSystemBase ctor 0x1b8198 copies it to sys+0x204, so config word +0x28 = sys+0x22c.
    import symwalk
    def cfg_words(I, lo, hi):
        I.disasm = lambda l, h: I.listing(l, h)
        st = symwalk.State(); symwalk.Walker(I, {}, strings=False).walk(lo, hi, st, fork=False)
        return {o: (v[1] if v and v[0] == "lit" else None) for o, v in st.stack.items() if 0x58 <= o < 0xb8}
    cB = cfg_words(B, 0x5713fc, 0x5714b4); cA = cfg_words(A, 0x56f888, 0x56f940)
    diffw = {hex(o - 0x58): (cA.get(o), cB.get(o)) for o in sorted(set(cA) | set(cB)) if cA.get(o) != cB.get(o)}
    log("  HexaTrackAudioSystem config (24 words, 1.50 block 0x56f888 / 1.60 0x5713fc): words that differ {offset: (1.50, 1.60)} = %s" % diffw)
    log("   1.60 words: " + " ".join("%x:%s" % (o - 0x58, ("0x%x" % cB[o]) if cB.get(o) is not None else "?") for o in sorted(cB)))
    log("  alloc of HexaTrackAudioSystem: 1.50 %s ; 1.60 %s" % (
        [i.op_str for i in A.listing(0x56f888, 0x56f88c)], [i.op_str for i in B.listing(0x5713fc, 0x571400)]))
    J["C1_config_diff"] = diffw
    check("C1 inserts per track (config +0x28 -> sys+0x22c): 1 in 1.50, 2 in 1.60; no other config word differs",
          diffw == {"0x28": (1, 2)} and len(cB) == 24 and any(i.op_str == "r0, r4, #0x204" for i in B.listing(0x1b81c8, 0x1b81cc))
          and [i.op_str for i in A.listing(0x1ac2a8, 0x1ac2b0)] == ["r2, #0x60", "r0, r4, #0x204"]
          and [i.op_str for i in A.listing(0x56f940, 0x56f944)] == ["#0x1b68a4"] and inv.get(0x1c2cac) == 0x1b68a4
          and inv.get(0x1b8198) == 0x1ac27c)
    # insert count source
    check("C1 insert count read from HexaTrackAudioSystem+0x22c in both (TrackUnit cfg word 0)",
          any(i.op_str == "r5, [r0, #0x22c]" for i in A.listing(0x1aeb24, 0x1aeb28)) and any(i.op_str == "r5, [r0, #0x22c]" for i in B.listing(0x1bacf8, 0x1bacfc)))

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C2: CompositeFxUnit / FX-mode code ==")
    J["C2"] = table(" named functions:", C2)
    vrows = vt_compare(A, B, vtables(A, "CompositeFxUnit")[0], vtables(B, "CompositeFxUnit")[0])
    c2v = collections.Counter(r[3] for r in vrows)
    log("  CompositeFxUnit vtable (1.50 0x%x / 1.60 0x%x): %d slots %s" % (vtables(A, "CompositeFxUnit")[0],
                                                                         vtables(B, "CompositeFxUnit")[0], len(vrows), dict(c2v)))
    J["C2_vtable"] = dict(c2v)
    check("C2 all named CompositeFxUnit / FX-mode bodies masked-identical", all(r["class"] == "same" for r in J["C2"]))
    check("C2 all CompositeFxUnit vtable slots masked-identical", set(c2v) == {"same"})
    cm = [nm for nm in rb if re.search(r"CompositeFxMode|setFxMode|FxMode", nm)]
    for nm in cm:
        rr = vt_compare(A, B, ra[nm][0], rb[nm][0]) if nm in ra else []
        cc = collections.Counter(r[3] for r in rr)
        log("  %s: vtable 1.50 0x%x / 1.60 0x%x %s" % (nm, ra[nm][0] if nm in ra else 0, rb[nm][0], dict(cc)))
        check("C2 %s task class masked-identical" % nm[:40], set(cc) == {"same"})

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C3: where the change is ==")
    J["C3"] = table(" changed / new functions on the FX2 path:", C3)
    for y, x_hint in ((0x47a314, None), (0x47a3ec, None), (0x300f70, None)):
        x = inv.get(y)
        log("  callers of 1.60 0x%x: %d ; of 1.50 0x%x: %d" % (y, len(direct_callers(B, y)), x or 0, len(direct_callers(A, x)) if x else -1))
    J["C3_fx2img_callers"] = (len(direct_callers(A, inv[0x47a3ec])), len(direct_callers(B, 0x47a3ec)))
    check("C3 TrackMenuView FX2-image setter: 0 callers in 1.50, 2 in 1.60", J["C3_fx2img_callers"] == (0, 2))

    def slot_args(I, tg):
        out = []
        for site in direct_callers(I, tg):
            pre = I.listing(site - 12, site)
            v = [p.op_str for p in pre if p.op_str.startswith("r1, #")]
            out.append(v[-1][5:] if v else "?")
        return out
    sa1, sb1 = slot_args(A, inv[0x300f70]), slot_args(B, 0x300f70)
    log("  getFxType(ctx, slot) slot arguments: 1.50 %s ; 1.60 %s" % (sa1, sb1))
    J["C3_getfx_slots"] = (sa1, sb1)
    check("C3 TrackMenuViewController never asks for slot 1 in 1.50; asks in 1.60",
          [s for s, c in zip(sa1, direct_callers(A, inv[0x300f70])) if 0x298000 <= c < 0x29c000 and s == "1"] == [] and
          len([s for s, c in zip(sb1, direct_callers(B, 0x300f70)) if 0x29a000 <= c < 0x29e000 and s == "1"]) == 4)
    # item 6 / 11 behaviour in the item->view function
    i150 = [i for i in A.listing(0x298e9c, 0x298ea8)]; i160 = [i for i in B.listing(0x29aff0, 0x29b008)]
    log("  item 6/11 branch: 1.50 '%s' -> default empty view name; 1.60 '%s' -> getFxType(…, 1) -> FxInsert*View" % (
        "; ".join("%s %s" % (i.mnemonic, i.op_str) for i in i150), "; ".join("%s %s" % (i.mnemonic, i.op_str) for i in i160[3:6])))
    log("   1.60 items 6/11: %s" % "; ".join("%s %s" % (i.mnemonic, i.op_str) for i in i160))
    check("C3 1.50 items 6/11 jump to the not-found exit 0x298e70; 1.60 items 6/11 call getFxType(slot 1)",
          i150[-1].op_str == "#0x298e70" and i160[2].mnemonic == "bne" and i160[4].op_str == "r1, #1" and i160[5].op_str == "#0x300f70")
    # IFPM tables
    t57a, t57b = A.u32(0x124968), B.u32(0x126338); t58a, t58b = A.u32(0x124984), B.u32(0x126354)
    sbt = lambda I, va, n: list(struct.unpack_from("<%db" % n, I.data, I.off(va)))
    ok = (sbt(A, t57a, 56) == sbt(B, t57b, 156)[:56] == sbt(B, t57b, 156)[100:] and
          sbt(A, t58a, 56) == sbt(B, t58b, 156)[:56] == sbt(B, t58b, 156)[100:] and set(sbt(B, t57b, 156)[56:100]) == {-1})
    log("  IFPM s57/s58 tables: 1.50 0x%x/0x%x (56 B, ids 100-155) ; 1.60 0x%x/0x%x (156 B, ids 100-255, 200-255 = copy)" % (t57a, t58a, t57b, t58b))
    check("C3 IFPM id tables extended: ids 200-255 duplicate 100-155, 156-199 = -1", ok)
    rng = ["%s %s" % (i.mnemonic, i.op_str) for i in A.listing(0x124954, 0x124958)] + ["%s %s" % (i.mnemonic, i.op_str) for i in B.listing(0x126324, 0x126328)]
    log("  range checks: 1.50 '%s' ; 1.60 '%s'" % tuple(rng))
    nw = [hex(s) for s in direct_callers(B, 0x1287a4)]
    log("  new 1.60 helper 0x1287a4 (id -> slot) callers: %s" % nw)
    s10 = [(i.address, i.mnemonic, i.op_str) for i in B.listing(0x129f08, 0x129f38)]
    log("  1.60 IFPM s10 @0x129f08: id = +0x5c; slot(id) vs +0x3c; act only if equal  (%d instr)" % len(s10))
    check("C3 IFPM s10 compares slot(id) with +0x3c (1.60)", any(i[2] == "r3, [r4, #0x3c]" for i in s10) and any(i[2] == "r3, r1, #0xc8" for i in s10))
    # MasterTempoQualityManager registration
    log("  constructTrack 1.60 @0x1bc00c: sys+0x610 (MasterTempoQualityManager) 0x1a91b0(processor) — new; callers of 0x1a91b0: %s"
        % [hex(c) for c in direct_callers(B, 0x1a91b0)])
    check("C3 0x1a91b0 is 1.60-only with one caller in constructTrack", 0x1a91b0 in added and direct_callers(B, 0x1a91b0) == [0x1bc010])

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C4: DSP routines ==")
    J["C4"] = table(" modelled DSP entry points / kernels / processors:", DSP)
    check("C4 every listed DSP routine masked-identical", all(r["class"] == "same" for r in J["C4"]))
    fxv = {}
    for nm in sorted(set(ra) & set(rb)):
        if FX_CLASS_RE.match(nm) and len(ra[nm]) == 1 and len(rb[nm]) == 1:
            rows = vt_compare(A, B, ra[nm][0], rb[nm][0])
            fxv[nm] = collections.Counter(r[3] for r in rows)
    bad = {k: dict(v) for k, v in fxv.items() if set(v) - {"same"}}
    log("  FX / mixer class vtables compared: %d classes, %d slots; not all-same: %s" % (
        len(fxv), sum(sum(v.values()) for v in fxv.values()), bad))
    J["C4_vtables"] = {k: dict(v) for k, v in fxv.items()}

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C5: audio path ==")
    J["C5"] = table(" track / bus audio-path functions:", AUDIO)
    rows = vt_compare(A, B, vtables(A, "TrackUnit")[0], vtables(B, "TrackUnit")[0])
    log("  TrackUnit vtable: %s" % dict(collections.Counter(r[3] for r in rows)))
    helpers = [0x1b61bc, 0x1b7380, 0x1b7480, 0x1b76a0, 0x1b77b0, 0x1b7590, 0x1b78c0, 0x1b7ab0, 0x1b7ef0]

    def sig(I, s, tg):
        L = I.listing(s, I.func_of(s)[1]); out = []
        for k, i in enumerate(L):
            if i.mnemonic == "bl" and int(i.op_str[1:], 16) in tg:
                out.append((tg[int(i.op_str[1:], 16)], tuple(re.sub(r"\s", "", j.op_str) for j in L[max(0, k - 8):k]
                                                              if j.mnemonic in ("mov", "mvn") and "#" in j.op_str)))
        return out
    ga = sig(A, inv[0x1bc8d4], {inv[h]: h for h in helpers}); gb = sig(B, 0x1bc8d4, {h: h for h in helpers})
    log("  graph build: %d / %d connection-helper calls; immediate-argument signatures identical: %s" % (len(ga), len(gb), ga == gb))
    check("C5 graph connections (helper call order + immediates) identical", ga == gb and len(gb) == 26)
    d = fdiff(A, B, inv[0x1c4ff8], A.func_of(inv[0x1c4ff8])[1], 0x1c4ff8, B.func_of(0x1c4ff8)[1], structural=True)[0]
    log("  MultiTrackUnit processBlock structural diff (%d hunks): 1.50 skips unit +0xfc when MidiBuffer +0x528 is empty"
        " (0x57954c), 1.60 always calls it; rest = register allocation" % sum(1 for x in d if not x.startswith("  ")))
    if not a.no_emu:
        log("  emulation:")
        J["emu"] = run_emulation(log)
        check("C5 E1 parameter-id maps (6 checks)", all(J["emu"]["E1_checks"].values()))
        J["emu"]["E3"] = run_track_emulation(log)
        e3 = J["emu"]["E3"]
        check("C5 E3 real TrackUnit::processBlock == track_mix model with 1 insert (1.50 config) and 2 inserts (1.60), FX2 after FX1",
              e3[1]["model_mismatch"] == 0 and e3[2]["model_mismatch"] == 0 and e3[2]["reversed_order_mismatch"] > 0 and
              e3[1]["sha"] != e3[2]["sha"])
        check("C5 E2 MasterTempoQualityManager (1.50: Low iff reverb && players > 12; 1.60: Low iff 8·reverb + activeFX + 2·players > 32)", J["emu"]["E2_pass"])

    # ------------------------------------------------------------------------------------------------------------------
    log("\n== C6: alternatives ==")
    ifpm = vt_compare(A, B, vtables(A, "InsertFxParameterManager")[0], vtables(B, "InsertFxParameterManager")[0])
    log("  InsertFxParameterManager vtable: %s; struct: %s" % (dict(collections.Counter(r[3] for r in ifpm)),
                                                             ["s%d 0x%x" % (r[0], r[2]) for r in ifpm if r[3] == "struct"]))
    shifts = collections.Counter()
    for r in ifpm:
        if r[3] == "imm":
            _, p = imm_detail(A, B, r[1], r[2]); shifts.update(p)
    log("  IFPM 'imm' slots: immediate changes (old->new: count) %s" % dict(sorted(shifts.items())[:30]))
    J["C6_ifpm_imm"] = {"%s->%s" % k: v for k, v in shifts.items()}
    for nm in ("prj::TrackData", "TrackMenuViewController", "FxSelectPopupWidgetController", "LfoViewController"):
        mang = "N3prj9TrackDataE" if nm == "prj::TrackData" else "%d%s" % (len(nm), nm)
        if mang in ra and mang in rb:
            rr = vt_compare(A, B, ra[mang][0], rb[mang][0])
            log("  %s vtable: %s" % (nm, dict(collections.Counter(r[3] for r in rr))))

    # (d) project data: every vtable slot of prj:: data classes and their ctor lambdas, paired by alignment
    pc = collections.Counter(); pbad = []
    for nm in sorted(rb):
        if not re.search(r"prj9TrackData|prj10EffectData|prj16TrackRoutingData|prj11ProjectData", nm): continue
        for v in rb[nm]:
            for k, y in enumerate(vt_slots(B, v)):
                if not y: continue
                x, c, r = status(y); pc[c] += 1
                if c not in ("same",): pbad.append((nm, k, hex(y), c))
    log("  project-data classes (TrackData/EffectData/TrackRoutingData/ProjectData + ctor lambdas): slots %s; not same: %s" % (dict(pc), pbad[:6]))
    check("C6(d) project-data class code unchanged", not pbad and pc["same"] > 100)
    fsp = status(0x3bec88)
    log("  FxSelectPopupWidget builders 0x3bec88/0x3c237c: %s %.3f (diff = a colour constant moved to a static, see structural diff)" % (fsp[1], fsp[2]))

    log("\nRESULT: %d failed checks%s" % (len(fails), (": " + "; ".join(fails)) if fails else ""))
    J["fails"] = fails
    open(os.path.join(a.out, "h006_report.txt"), "w").write("\n".join(rep) + "\n")
    json.dump(J, open(os.path.join(a.out, "h006.json"), "w"), indent=1, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
