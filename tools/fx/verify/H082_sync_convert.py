#!/usr/bin/env python3
"""H082 — the SYNC toggle (parameter-manager slot 34) free <-> beat conversion, and the UI quantisation law.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time
and never stored; outputs are our own derived numbers (recipes, counts, hashes). Emulation is guest-memory only.

Sections (criteria of kb/cycles/036.md):
  C1 static: walk every jump-table case of s34 (Insert 0x126c90, Master 0x1208ac, Send 0x12b3b4) along both directions
     (SYNC arg r1 == 0 / != 0) and record helper calls, float literals, clamps, EffectData stores and 0x112924 arguments;
     classify each of the 42 helpers by instruction template (range pair, index->value, value->index, indexToFraction,
     nearest-fraction chain, Ducker table and binary search) and compare the extracted constants with models/sync_convert.py.
  C1b tables: fraction tables after the real .init_array code (H077 EmuProc), Ducker sixteenth tables (static) vs the model.
  C1c helper emulation: every helper called in unicorn over many inputs vs the model functions.
  C2 s34 emulation: REAL processor + REAL manager ctor + REAL EffectData ctor (H083 Rig) in the three contexts, grid tempo x value
     x direction x reachable type; ED fields, slot-14 calls; plus s50 after the toggle and emulated round trips.
  C3 model check: every emulated output equals models/sync_convert.py bit-exactly (raw float32 bits); round trips via the model.
  C4 UI: step routines 0x316a10 / 0x313ecc and the value formatter 0x314d4c (static helper use; emulation with the H086 stub rig).
Run: .venv/bin/python -B harness/H082_sync_convert.py --out DIR
"""
import argparse, hashlib, json, math, os, re, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from sp16img import Image                                      # noqa: E402
import sync_convert as SC                                      # noqa: E402

S34 = {"insert": 0x126c90, "master": 0x1208ac, "send": 0x12b3b4}
S50 = {"insert": 0x126458, "master": 0x120224, "send": 0x12ad2c}
TEMPO_GET = 0x112a48
SETIDX = 0x112924
ASSERT_FN = 0x4f782c
MAGIC = 6755399441055744.0                                     # 1.5 * 2^52 (roundToInt)
TEMPOS = [20.0, 60.0, 120.0, 133.7, 300.0, 87.5, 0.25, 999.0]
BASEV = [0.0, 1.0, 0.05, 0.1, 0.123, 0.25, 1.0 / 3, 0.5, 0.6, 0.75, 0.9, 0.999]
OUTV = [-0.25, 1.5]


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u & 0x80000000 else u
def F(x): return SC.F(x)
def fb(x): return SC.fbits(x)


# ===================================================================================================================== C1 static
def one(im, a):
    L = list(im.disasm(a, a + 4))
    if not L: raise RuntimeError("undecodable 0x%x" % a)
    return L[0]


def tgt(op):
    m = re.match(r"#(0x[0-9a-f]+)$", op); return int(m.group(1), 16) if m else None


def pc_lit(im, i, kind):
    m = re.search(r"\[pc, #(-?0x[0-9a-f]+|-?\d+)\]", i.op_str)
    a = i.address + 8 + int(m.group(1), 0)
    if kind == "d": return struct.unpack("<d", struct.pack("<II", im.u32(a), im.u32(a + 4)))[0]
    return u2f(im.u32(a))


def jump_table(im, fn):
    a = fn
    for _ in range(64):
        i = one(im, a)
        if i.mnemonic == "ldrls" and i.op_str.startswith("pc, [pc, r6, lsl #2]"):
            ret = tgt(one(im, a + 4).op_str)
            return a, [im.u32(a + 8 + 4 * k) for k in range(10)], ret
        a += 4
    raise RuntimeError("no jump table in 0x%x" % fn)


def prologue(im, fn, jt):
    """Instruction facts between entry and the jump table."""
    ops = [(i.address, i.mnemonic, i.op_str) for i in im.disasm(fn, jt)]
    txt = ["%s %s" % (m, o) for _, m, o in ops]
    calls = [tgt(o) for _, m, o in ops if m == "bl"]
    vt = [o for _, m, o in ops if m == "ldr" and "#0xc0]" in o]
    clamp01 = None
    for i in im.disasm(fn, jt):
        if i.mnemonic == "vldr" and "[pc" in i.op_str: clamp01 = pc_lit(im, i, "f")
    return dict(guard=any("ldrb r3, [r0, #0x24]" == t for t in txt), store28=any(t.startswith("strb r5, [r3, #0x28]") for t in txt),
                type_vcall=bool(vt), calls=[hex(c) for c in calls], tempo_floor=clamp01)


def walk(im, start, ret, sync):
    """Follow one direction of one case. Returns ordered op list."""
    ops = []; a = start; last_cmp = None; regs = {}; n = 0
    while n < 3000:
        n += 1
        if a == ret: ops.append(("ret",)); return ops
        i = one(im, a); m, op = i.mnemonic, i.op_str
        if m == "b":
            a = tgt(op); continue
        if m in ("beq", "bne") and last_cmp == "r5, #0":
            take = (m == "beq") == (sync == 0)
            ops.append(("fork", hex(a), m)); a = tgt(op) if take else a + 4; continue
        if m == "bmi":
            s = one(im, tgt(op)); back = one(im, tgt(op) + 4)
            assert s.mnemonic == "vldr" and back.mnemonic == "b", hex(a)
            ops.append(("clamp_lo", s.op_str.split(",")[0], pc_lit(im, s, "f"), hex(tgt(back.op_str))))
            a += 4; continue
        if m == "bhi" and last_cmp == "r3, #0x10":
            a += 4; continue                                      # SwitchableObject index assert path (index 0 here)
        if m.startswith("b") and m not in ("bl", "blx") and m != "bic":
            raise RuntimeError("unexpected branch %s %s @0x%x" % (m, op, a))
        if m == "bl":
            t = tgt(op)
            ops.append(("call", t, regs.get("r1"), regs.get("r2"))); a += 4; continue
        if m == "cmp": last_cmp = op
        mm = re.match(r"(r[12]), #(0x[0-9a-f]+|\d+)$", op)
        if m == "mov" and mm: regs[mm.group(1)] = int(mm.group(2), 0)
        if m == "mov" and op == "r2, r1": regs["r2"] = regs.get("r1")
        if m == "vldr" and "[pc" in op:
            ops.append(("lit", op.split(",")[0], pc_lit(im, i, "d" if op.startswith("d") else "f")))
        elif m == "vldr":
            ops.append(("load", op))
        if m == "vstr": ops.append(("store", op))
        if m.startswith("vmovgt"): ops.append(("clamp_hi", op))
        if m == "vmov.f32" and "#" in op: ops.append(("imm", op))
        if m in ("vdiv.f32", "vmul.f32", "vmla.f32", "vadd.f64", "vadd.f32", "vcvt.f32.u32"): ops.append(("fop", m, op))
        a += 4
    raise RuntimeError("walk did not terminate from 0x%x" % start)


def summarize(ops):
    helpers = [hex(o[1]) for o in ops if o[0] == "call" and o[1] not in (SETIDX, ASSERT_FN)]
    sets = [(o[2], o[3]) for o in ops if o[0] == "call" and o[1] == SETIDX]
    lits = [o[2] for o in ops if o[0] == "lit"]
    clamps = [(o[1], o[2]) for o in ops if o[0] == "clamp_lo"]
    stores = [o[1] for o in ops if o[0] == "store"]
    loads = [o[1] for o in ops if o[0] == "load"]
    fops = [o[1] for o in ops if o[0] == "fop"]
    imms = [o[1] for o in ops if o[0] == "imm"]
    first_call = next((k for k, o in enumerate(ops) if o[0] == "call"), None)
    in_clamp = any(o[0] == "clamp_lo" for o in ops[:first_call])
    return dict(helpers=helpers, sets=sets, lits=lits, clamps=clamps, stores=stores, loads=loads, fops=fops, imms=imms, input_clamp=in_clamp)


def classify(im, a):
    """Instruction-template classification of one helper. Returns (kind, params)."""
    L = [(i.mnemonic, i.op_str, i) for i in im.disasm(a, a + 4 * 12)]
    t = ["%s %s" % (m, o) for m, o, _ in L]
    if t[0].startswith("vldr d16, [pc") and t[1] == "vst1.32 {d16}, [r0]" and t[2] == "bx lr":
        la = L[0][2].address + 8 + int(re.search(r"#(0x[0-9a-f]+|\d+)\]", t[0]).group(1), 0)
        return "range", (s32(im.u32(la)), s32(im.u32(la + 4)))
    if t[0] == "vmov s13, r0" and t[1] == "vcvt.f32.s32 s14, s13" and t[2].startswith("vldr s15, [pc") and \
            t[3] == "vmul.f32 s13, s14, s15" and t[4] == "vmov r0, s13" and t[5] == "bx lr":
        return "i2v_scale", pc_lit(im, L[2][2], "f")
    if t[:4] == ["vmov s15, r0", "vcvt.f32.s32 s15, s15", "vmov r0, s15", "bx lr"]:
        return "i2v_id", None
    if t[:6] == ["vmov s15, r0", "vcvt.f64.f32 d17, s15", t[2], "vadd.f64 d18, d17, d16", "vmov r0, r1, d18", "bx lr"] and \
            t[2].startswith("vldr d16, [pc") and pc_lit(im, L[2][2], "d") == MAGIC:
        return "v2i_round", None
    if t[0] in ("vmov.f32 s15, #1.000000e+01", "vmov s14, r0"):
        # round_scale (10 via immediate, or vldr literal) / trunc_scale
        k = None; mag = None; trunc = False
        for m, o, i in L[:9]:
            if m == "vmov.f32" and o.startswith("s15, #"): k = float(o.split("#")[1])
            if m == "vldr" and o.startswith("s15, [pc"): k = pc_lit(im, i, "f")
            if m == "vldr" and o.startswith("d16, [pc"): mag = pc_lit(im, i, "d")
            if m == "vcvt.s32.f32": trunc = True
            if m == "bx": break
        if trunc and k is not None: return "v2i_trunc_scale", k
        if mag == MAGIC and k is not None: return "v2i_round_scale", k
    if L[0][0] == "cmp" and L[0][1].startswith("r0, #"):
        n1 = int(L[0][1].split("#")[1], 0)
        body = list(im.disasm(a, a + 4 * 20)); tb = None; dflt = None
        for i in body:
            if i.mnemonic == "ldr" and "[pc" in i.op_str and tb is None:
                lit = im.u32(i.address + 8 + int(re.search(r"#(0x[0-9a-f]+|\d+)\]", i.op_str).group(1), 0))
                if 0xf00000 <= lit < 0x1000000: tb = lit
            if i.mnemonic == "mov" and i.op_str.startswith("r0, #") and dflt is None: dflt = int(i.op_str.split("#")[1], 0)
            if i.mnemonic == "pop": break
        if tb: return "frac_idx", (n1 + 1, tb, dflt)
    if t[0] == "movw r3, #0xaa00" and t[1] == "movt r3, #0x8a" and t[2] == "add r3, r3, r0, lsl #2" and t[3].startswith("sub r3, r3, #"):
        return "table", 0x8aaa00 - int(t[3].split("#")[1], 0)
    if L[0][0] == "ldr" and "[pc" in L[0][1] and t[1].startswith("mov r2, #") and t[2] == "mov r3, #0":
        body = list(im.disasm(a, a + 4 * 32)); sub = None; eps = None
        for i in body:
            if i.mnemonic == "sub" and i.op_str.startswith("ip, ip, #"): sub = int(i.op_str.split("#")[1], 0)
            if i.mnemonic == "vldr" and "[pc" in i.op_str: eps = pc_lit(im, i, "f")
            if i.mnemonic == "bx": break
        return "bsearch", (int(t[1].split("#")[1], 0) + 1, 0x8aaa00 - sub, eps)
    if L[0][0] == "ldr" and "[pc" in L[0][1]:
        # nearest-fraction chain: ldrh offsets + per-step return constants and conditions
        base = im.u32(L[0][2].address + 8 + int(re.search(r"#(0x[0-9a-f]+|\d+)\]", L[0][1]).group(1), 0))
        offs = []; rets = []; conds = set(); end = None; tail = False
        for i in im.disasm(a, a + 4 * 600):
            if tail and not ((i.mnemonic == "mov" and i.op_str.startswith("r0, #")) or (i.mnemonic == "bx" and i.op_str == "lr")):
                break
            if i.mnemonic == "ldrh":
                mo = re.search(r"#(0x[0-9a-f]+|\d+)\]", i.op_str); offs.append(int(mo.group(1), 0))
            mm = re.match(r"mov(gt|mi|le|pl)?$", i.mnemonic)
            if mm and i.op_str.startswith("r0, #"):
                rets.append((mm.group(1), int(i.op_str.split("#")[1], 0))); conds.add(mm.group(1))
            if i.mnemonic == "bx" and i.op_str == "lr" and end is None:
                end = i.address; tail = True
        ent = sorted(set((o - (base and 0)) for o in offs))
        return "nearest", dict(base=base, offs=ent, rets=rets, conds=sorted(c for c in conds if c), end=hex(end) if end else None)
    return "unknown", t[:6]


def c1_static(im, check, J):
    walks = {}
    for ctx, fn in S34.items():
        jt, words, ret = jump_table(im, fn)
        pro = prologue(im, fn, jt)
        J.setdefault("prologue", {})[ctx] = dict(pro, jt=hex(jt), ret=hex(ret), table=[hex(w) for w in words])
        cases = {k: w for k, w in enumerate(words) if w != ret}
        check(sorted(cases) == sorted(SC.CASES[ctx]),
              "%s s34 0x%x: jump table @0x%x has non-default cases %s (model %s); default -> 0x%x (return, no slot-14 call)" % (
                  ctx, fn, jt, sorted(cases), sorted(SC.CASES[ctx]), ret))
        exp_calls = [hex(TEMPO_GET)]
        check(pro["guard"] and pro["store28"] and pro["type_vcall"] and pro["calls"] == exp_calls,
              "%s s34 prologue: +0x24 guard, strb r1 -> ED+0x28 (before anything else), type = processor vt+0xc0, one call: tempo 0x112a48;"
              " extra tempo floor literal: %s" % (ctx, pro["tempo_floor"]))
        for case, start in sorted(cases.items()):
            for sync in (1, 0):
                walks[(ctx, case, sync)] = summarize(walk(im, start, ret, sync))
    # helpers
    used = sorted(set(int(h, 16) for w in walks.values() for h in w["helpers"]))
    cls = {a: classify(im, a) for a in used}
    J["helpers"] = {hex(a): [k, (v if not isinstance(v, float) else v)] for a, (k, v) in cls.items()}
    check(len(used) == 42 and not any(k == "unknown" for k, _ in cls.values()),
          "42 distinct helpers called by the three s34, every one matched an instruction template: %s" % (
              {k: sum(1 for kk, _ in cls.values() if kk == k) for k in sorted(set(kk for kk, _ in cls.values()))}))
    # compare with the model's family constants
    bad = []
    for fam, Fm in SC.FAMILIES.items():
        def want(addr, kind, val):
            k, v = cls.get(addr, (None, None))
            if k != kind or (val is not None and v != val): bad.append((fam, hex(addr), kind, val, k, v))
        want(Fm["free"][0], "range", Fm["free"][1]); want(Fm["sync"][0], "range", Fm["sync"][1])
        ik, ivk, ivv = Fm["i2v"]
        want(ik, {"scale": "i2v_scale", "id": "i2v_id"}[ivk], F(ivv) if ivv is not None else None)
        vk, vvk, vvv = Fm["v2i"]
        want(vk, {"round_scale": "v2i_round_scale", "trunc_scale": "v2i_trunc_scale", "round": "v2i_round"}[vvk],
             F(vvv) if vvv is not None else None)
        if Fm["kind"] == "ducker":
            want(Fm["f2v"][0], "table", Fm["f2v"][1])
            k, v = cls[Fm["v2f"][0]]
            if not (k == "bsearch" and v[0] == 128 and v[1] == Fm["f2v"][1] and v[2] == SC.BSEARCH_EPS): bad.append((fam, "bsearch", v))
        else:
            n = len(Fm["fracs"])
            want(Fm["f2v"][0], "frac_idx", (n, Fm["f2v"][1], Fm["f2v"][2]))
            k, v = cls[Fm["v2f"][0]]
            first = (Fm["f2v"][1] - v["base"])
            ok = (k == "nearest" and v["offs"] == list(range(first, first + 4 * n, 2))
                  and sorted(r for _, r in v["rets"]) == list(range(n)) and
                  v["conds"] == (["gt", "le"] if Fm["v2f"][1] == "desc" else ["mi", "pl"]))
            if not ok: bad.append((fam, "nearest", k, v))
    check(not bad, "model FAMILIES constants = template-extracted helper constants for all 7 families "
                   "(ranges, scales, rounding kind, fraction-table address/size/default, chain direction & order) %s" % (bad[:3],))
    # recipe checks per case/direction
    rec_bad = []
    for (ctx, case, sync), w in walks.items():
        fam, eff = SC.CASES[ctx][case]
        fams = ["ducker_attack", "ducker_release"] if fam == "ducker" else [fam]
        exp_h = []
        for f_ in fams:
            Fm = SC.FAMILIES[f_]
            if sync: exp_h += [Fm["free"][0], Fm["i2v"][0], Fm["v2f"][0], Fm["sync"][0]]
            else:    exp_h += [Fm["sync"][0], Fm["f2v"][0], Fm["v2i"][0], Fm["free"][0]]
        exp_sets = [(eff, 0)] + ([(eff, 2)] if fam == "ducker" else []) + [(eff, 6)]
        kind = SC.FAMILIES[fams[0]]["kind"]
        exp_lits = {("rate", 1): [MAGIC, 60.0], ("rate", 0): [MAGIC, 60.0],
                    ("delay", 1): [MAGIC, 60.0, F(0.001)], ("delay", 0): [MAGIC, 60.0, 1000.0],
                    ("ducker", 1): [MAGIC, F(0.004), 60.0], ("ducker", 0): [MAGIC, 60000.0]}[(kind, sync)]
        exp_store = ["s17, [r3, #0x38]", "s16, [ip, #0x48]"] if fam == "ducker" else None
        got_lits = [x for x in w["lits"] if x != 0.0]
        ok = ([int(h, 16) for h in w["helpers"]] == exp_h and w["sets"] == exp_sets and got_lits == exp_lits
              and w["input_clamp"] == (fam != "ducker")
              and all(v == 0.0 for _, v in w["clamps"])
              and len(w["stores"]) == (2 if fam == "ducker" else 1)
              and all("#0x38]" in s or "#0x48]" in s for s in w["stores"]))
        if fam == "ducker": ok = ok and w["stores"] == exp_store
        if not ok: rec_bad.append(((ctx, case, sync), w))
    J["walks"] = {"%s/%d/%d" % k: v for k, v in walks.items()}
    check(not rec_bad, "every s34 case/direction (%d paths) has exactly the recipe of the model: helper order "
                       "range->step->value->convert->index->range, float literals, input clamp (all but the Ducker), output clamps to 0.0/1.0,"
                       " ED store(s) +0x38 (+0x48 Ducker) and 0x112924(eff,0[,2]) then (eff,6): bad %s" % (
                           len(walks), [k for k, _ in rec_bad][:4]))
    # same float-op sequence for the same family in all contexts
    seqs = {}
    for (ctx, case, sync), w in walks.items():
        seqs.setdefault((SC.CASES[ctx][case][0], sync), set()).add(tuple(w["fops"]))
    check(all(len(v) == 1 for v in seqs.values()),
          "the float-op mnemonic sequence of each (family, direction) is identical in every context that has it (%d groups)" % len(seqs))
    J["fop_seqs"] = {"%s/%d" % k: list(list(v)[0]) for k, v in seqs.items()}
    return walks, cls


# ===================================================================================================================== C1b/C1c tables + helpers
def c1b_tables(im, check, J, e):
    bad = []
    for fam, Fm in SC.FAMILIES.items():
        if Fm["kind"] == "ducker":
            T = [u2f(im.u32(Fm["f2v"][1] + 4 * i)) for i in range(128)]
            if [fb(x) for x in T] != [fb(x) for x in Fm["table"]]: bad.append(fam)
        else:
            base = Fm["f2v"][1]
            got = [(e.u32(base + 4 * i) & 0xffff, e.u32(base + 4 * i) >> 16) for i in range(len(Fm["fracs"]))]
            J.setdefault("fracs", {})[fam] = got
            if got != Fm["fracs"]: bad.append((fam, got))
    check(not bad, "fraction tables (after the real .init_array code, 0xf61f18 + 4*idx, u16 num / u16 den) and the Ducker "
                   "sixteenth tables 0x8a9b20 / 0x8a9d20 equal the model (Ducker = ducker.TA / ducker.TR bit-exact): bad %s" % (bad,))


def c1c_helpers(check, J, e, cls):
    n = 0; bad = []
    sret = e.malloc(16)
    import random
    rnd = random.Random(82)
    for fam, Fm in SC.FAMILIES.items():
        for key in ("free", "sync"):
            a, (lo, hi) = Fm[key]
            e.wr(sret, b"\xee" * 8); e.call(a, sret)
            got = struct.unpack("<ii", e.rd(sret, 8)); n += 1
            if got != (lo, hi): bad.append((fam, key, got))
        lo, hi = Fm["free"][1]
        for i in list(range(lo, min(hi, lo + 50))) + [hi - 1] + [rnd.randrange(lo, hi) for _ in range(30)]:
            r = e.call(Fm["i2v"][0], i & 0xffffffff)[0]; n += 1
            if r != fb(SC.free_value(fam, i)): bad.append((fam, "i2v", i))
        xs = [SC.free_value(fam, i) for i in range(lo, hi, max(1, (hi - lo) // 200))]
        xs += [F(x + d) for x in xs[:60] for d in (0.0004, -0.0004, 0.05, -0.05)] + [F(rnd.uniform(0, 1.2 * SC.free_value(fam, hi - 1)))
                                                                                       for _ in range(200)]
        for x in xs:
            r = s32(e.call(Fm["v2i"][0], fb(x))[0]); n += 1
            if r != SC.free_index(fam, x): bad.append((fam, "v2i", x, r))
        slo, shi = Fm["sync"][1]
        for i in range(slo, shi):
            r = e.call(Fm["f2v"][0], i)[0]; n += 1
            if r != fb(SC.frac_value(fam, i)): bad.append((fam, "f2v", i))
        vals = [SC.frac_value(fam, i) for i in range(slo, shi)]
        mids = [F((vals[k] + vals[k + 1]) * 0.5) for k in range(len(vals) - 1)]
        ys = vals + mids + [F(m * (1 + d)) for m in mids for d in (1e-6, -1e-6, 1e-3, -1e-3)] + [math.nextafter(m, 0) for m in mids] + \
            [math.nextafter(m, 1e9) for m in mids] + [0.0, -1.0, 1e9] + [F(rnd.uniform(0, 1.5 * max(vals))) for _ in range(300)]
        for y in ys:
            y = F(y)
            r = s32(e.call(Fm["v2f"][0], fb(y))[0]); n += 1
            if r != SC.frac_index(fam, y): bad.append((fam, "v2f", y, r, SC.frac_index(fam, y)))
    J["helper_emu"] = dict(n=n, bad=bad[:20])
    check(not bad, "C1c helpers emulated one by one vs the model: %d calls (ranges, index->value, value->index incl. rounding "
                   "boundaries, indexToFraction, nearest-fraction chains at/around every midpoint, Ducker binary search), %d mismatches %s" % (
                       n, len(bad), bad[:3]))
    return n


# ===================================================================================================================== C2/C3 s34 emulation
class S34Rig:
    def __init__(self, which):
        import H083_enum_defaults as H83
        self.r = H83.Rig(which); self.which = which
        self.e = self.r.e; self.x = self.r.x; self.m = self.r.m; self.ed = self.r.ed
        self.pend_get = {"insert": 0x116838, "master": 0x112cbc, "send": 0x119980}[which]

    def set_type(self, t):
        self.x.set_fx_type(t)
        assert s32(self.e.call(self.pend_get, self.x.p)[0]) == t

    def run(self, ed0, ed2, sync, bpm):
        e = self.e
        e.w32(self.ed + 0x38, fb(ed0)); e.w32(self.ed + 0x48, fb(ed2)); e.wr(self.ed + 0x28, bytes([1 - (sync & 1)]))
        self.x.bpm = bpm; self.x.tempo_calls = 0; self.r.clear()
        e.call(S34[self.which], self.m, sync)
        return dict(ed0=e.u32(self.ed + 0x38), ed2=e.u32(self.ed + 0x48), b28=e.rd(self.ed + 0x28, 1)[0],
                    calls=[(a, b, int(c, 16)) for a, b, c in self.r.s14_log()], tempo_calls=self.x.tempo_calls)

    def s50(self, k):
        e = self.e; sret = e.malloc(16)
        e.call(S50[self.which], sret, self.m, k)
        return struct.unpack("<ii", e.rd(sret, 8))


def grid_values(fam):
    Fm = SC.FAMILIES["ducker_attack" if fam == "ducker" else fam]
    vs = list(BASEV)
    for key in ("free", "sync"):
        lo, hi = Fm[key][1]
        step = max(1, (hi - lo) // 12)
        vs += [SC.norm_of(lo, hi, i) for i in range(lo, hi, step)]
        vs += [F((i - lo + 0.5) / (hi - 1 - lo)) for i in range(lo, hi - 1, max(1, (hi - lo) // 6))]   # rounding boundaries
    if fam != "ducker": vs += OUTV
    out = []
    for v in vs:
        v = F(v)
        if fb(v) not in [fb(x) for x in out]: out.append(v)
    return out


def c2_c3(check, J):
    t0 = time.time()
    rows = []; mism = []; total = 0; per = {}; recs = []
    rigs = {}
    s50_bad = []; s50_n = 0
    for ctx in ("insert", "master", "send"):
        rig = rigs[ctx] = S34Rig(ctx)
        # non-time types: no slot-14 call (the default case)
        for t in range(10):
            if t in SC.CASES[ctx]: continue
            rig.set_type(t); o = rig.run(0.5, 0.5, 1, 120.0); total += 1
            if o["calls"] or o["ed0"] != fb(0.5) or o["b28"] != 1: mism.append((ctx, t, "non-time", o))
        for case, (fam, eff) in sorted(SC.CASES[ctx].items()):
            rig.set_type(case)
            vs = grid_values(fam)
            cnt = 0
            for bpm in TEMPOS:
                for k, v in enumerate(vs):
                    w = vs[(len(vs) - 1 - k)] if fam == "ducker" else 0.77
                    for sync in (1, 0):
                        o = rig.run(v, w, sync, bpm); mo = SC.s34(ctx, case, v, w, sync, bpm)
                        exp = dict(ed0=fb(mo["ed0"]), ed2=fb(mo["ed2"]) if fam == "ducker" else fb(F(w)),
                                   calls=[(a, b, fb(c)) for a, b, c in mo["calls"]])
                        ok = (o["ed0"] == exp["ed0"] and o["ed2"] == exp["ed2"] and o["calls"] == exp["calls"] and o["b28"] == sync
                              and o["tempo_calls"] == 1)
                        total += 1; cnt += 1
                        rows.append("%s,%d,%s,%r,%d,%r,%r,%08x,%08x,%s" % (ctx, case, fam, bpm, sync, v, w, o["ed0"], o["ed2"],
                                                                          ";".join("%d:%d:%08x" % c for c in o["calls"])))
                        if not ok: mism.append((ctx, case, bpm, v, w, sync, o, exp))
                        recs.append((ctx, case, bpm, v, w, sync, o))
                # s50 after the toggle: range of the mode just entered
                if bpm == 120.0:
                    for sync in (1, 0):
                        rig.run(0.5, 0.5, sync, bpm)
                        for sub, f_ in ([(0, "ducker_attack"), (2, "ducker_release")] if fam == "ducker" else [(0, fam)]):
                            exp = SC.FAMILIES[f_]["sync" if sync else "free"][1]; got = rig.s50(sub); s50_n += 1
                            if tuple(got) != tuple(exp): s50_bad.append((ctx, case, sub, sync, got, exp))
            per["%s/%d/%s" % (ctx, case, fam)] = cnt
    J["c2"] = dict(total=total, per=per, mismatches=[str(m)[:300] for m in mism[:20]], seconds=round(time.time() - t0, 1))
    check(total >= 500 and not mism,
          "C2/C3 real s34 (H083 rig: real processor + manager ctor + EffectData ctor) vs models/sync_convert.py: %d cases "
          "(%s), %d mismatches (ED +0x38, +0x48, ED+0x28, every slot-14 call bit-exact; tempo read once)" % (
              total, ", ".join("%s=%d" % kv for kv in sorted(per.items())), len(mism)))
    check(not s50_bad, "after each toggle the real s50 returns the range of the mode just entered (sync range if the effect's live "
                       "SYNC > 0.5, else free) for the time sub-slot(s): %d/%d %s" % (s50_n - len(s50_bad), s50_n, s50_bad[:3]))
    # emulated round trips off -> on -> off (and on -> off -> on) for every free step at 3 tempos
    rt = {}; rt_bad = []; rt_n = 0
    for ctx in ("insert", "master"):
        rig = rigs[ctx]
        for case, (fam, eff) in sorted(SC.CASES[ctx].items()):
            rig.set_type(case)
            fams = ["ducker_attack", "ducker_release"] if fam == "ducker" else [fam]
            lo, hi = SC.FAMILIES[fams[0]]["free"][1]
            step = max(1, (hi - lo) // 40)
            for bpm in (60.0, 120.0, 133.7):
                for i in range(lo, hi, step):
                    v = SC.norm_of(lo, hi, i)
                    rig.run(v, v, 1, bpm); o = rig.run(u2f(rig.e.u32(rig.ed + 0x38)), u2f(rig.e.u32(rig.ed + 0x48)), 0, bpm)
                    m1 = SC.s34(ctx, case, v, v, 1, bpm); m2 = SC.s34(ctx, case, m1["ed0"], m1["ed2"], 0, bpm)
                    rt_n += 1
                    if o["ed0"] != fb(m2["ed0"]): rt_bad.append((ctx, case, bpm, i))
    check(not rt_bad, "emulated round trips free -> sync -> free (%d cases, Insert + Master) equal the model's round trip bit-exactly %s"
          % (rt_n, rt_bad[:3]))
    distinct = {}
    for ctx, case, bpm, v, w, sync, o in recs:
        distinct.setdefault("%s/%s/%d" % (ctx, SC.CASES[ctx][case][0], sync), set()).add(o["ed0"])
    J["c2_distinct_outputs"] = {k: len(v) for k, v in sorted(distinct.items())}
    return rows, total, recs, rigs


def convert_double_factor(fam, v, sync, bpm):
    """Alternative A5: the tempo factor computed in double from the double tempo, rounded to float once."""
    Fm = SC.FAMILIES[fam]; kind = Fm["kind"]
    (flo, fhi), (slo, shi) = Fm["free"][1], Fm["sync"][1]
    b = max(float(bpm), 0.5)
    if sync:
        i = SC.step_of(flo, fhi, v); x = SC.free_value(fam, i)
        if kind == "rate": y = SC.fmul(F(b / 60.0), SC.fdiv(1.0, x))
        elif kind == "delay": y = SC.fmul(SC.fmul(x, F(b / 60.0)), SC.K_MILLI)
        else: y = SC.fmul(x, F(b * F(0.004) / 60.0))
        return SC.clamp01_out(SC.norm_of(slo, shi, SC.frac_index(fam, y)))
    i = SC.step_of(slo, shi, v); x = SC.frac_value(fam, i)
    if kind == "rate": y = SC.fmul(F(b / 60.0), SC.fdiv(1.0, x))
    elif kind == "delay": y = SC.fmul(SC.fmul(x, F(60.0 / b)), SC.K_1000)
    else: y = SC.fmul(SC.fmul(x, F(60000.0 / b)), SC.K_QUARTER)
    return SC.clamp01_out(SC.norm_of(flo, fhi, SC.free_index(fam, y)))


def a5_cases(check, J, rigs):
    """Find (model-only) tempos on a 0.1 BPM grid where A5 differs from the f32-tempo law, then emulate exactly those cases."""
    found = []
    for ctx in ("insert", "master"):
        for case, (fam, eff) in sorted(SC.CASES[ctx].items()):
            fams = ["ducker_attack", "ducker_release"] if fam == "ducker" else [fam]
            per = 0
            for k in range(0, 2801, 7):
                bpm = 20.0 + 0.1 * k
                T = SC.tempo_f32(bpm, insert=(ctx == "insert"))
                for f_ in fams:
                    for sync in (0, 1):
                        lo, hi = SC.FAMILIES[f_]["free" if sync else "sync"][1]
                        for i in range(lo, hi, max(1, (hi - lo) // 50)):
                            v = SC.norm_of(lo, hi, i)
                            if fb(SC.convert(f_, v, sync, T)[0]) != fb(convert_double_factor(f_, v, sync, bpm)):
                                found.append((ctx, case, f_, bpm, v, sync)); per += 1
                                break
                        if per >= 4: break
                    if per >= 4: break
                if per >= 4: break
    recs = []; bad = 0
    for ctx, case, f_, bpm, v, sync in found:
        rig = rigs[ctx]; rig.set_type(case)
        w = v if f_ == "ducker_release" else 0.5
        v0 = 0.5 if f_ == "ducker_release" else v
        o = rig.run(v0, w, sync, bpm); mo = SC.s34(ctx, case, v0, w, sync, bpm)
        sub = "ed2" if f_ == "ducker_release" else "ed0"
        if o[sub] != fb(mo[sub]): bad += 1
        alt = convert_double_factor(f_, v, sync, bpm)
        recs.append((ctx, case, f_, bpm, v, sync, o[sub] == fb(mo[sub]), o[sub] == fb(alt)))
    J["a5_cases"] = [str(r) for r in recs]
    n_alt = sum(1 for r in recs if r[7])
    check(len(recs) >= 5 and bad == 0 and n_alt == 0,
          "A5 (tempo factor in double) refuted on %d discriminating emulated cases found on a 0.1-BPM tempo grid: real s34 = float32-tempo "
          "model in %d, = A5 in %d" % (len(recs), len(recs) - bad, n_alt))


def guest_mutant(check, J, rigs):
    """Negative control: change the Chorus free-rate scale literal (0.1 at 0x3497b0, guest copy only) -> real s34 must now
    disagree with the model for Chorus free->sync, and agree again after restoring."""
    rig = rigs["insert"]; e = rig.e; a = 0x3497b0
    orig = e.rd(a, 4); e.wr(a, struct.pack("<f", 0.2)); rig.set_type(0)
    bad = 0; n = 0
    for bpm in (60.0, 120.0):
        for v in grid_values("chorus"):
            o = rig.run(v, 0.77, 1, bpm); n += 1
            if o["ed0"] != fb(SC.s34("insert", 0, v, 0.77, 1, bpm)["ed0"]): bad += 1
    e.wr(a, orig)
    ok_after = all(rig.run(v, 0.77, 1, 120.0)["ed0"] == fb(SC.s34("insert", 0, v, 0.77, 1, 120.0)["ed0"]) for v in grid_values("chorus"))
    J["guest_mutant"] = dict(n=n, bad=bad, ok_after=ok_after)
    check(bad > 0 and ok_after, "negative control: guest-only patch of the Chorus Hz scale literal 0x3497b0 (0.1 -> 0.2) makes %d/%d "
                                "Chorus free->sync cases disagree with the model; restored -> all agree again" % (bad, n))


def alternatives(check, J, recs):
    """Plausible alternative laws, each scored against the emulated s34 outputs (must all be refuted)."""
    import contextlib
    @contextlib.contextmanager
    def patched(**kw):
        old = {k: getattr(SC, k) for k in kw}
        for k, v in kw.items(): setattr(SC, k, v)
        try: yield
        finally:
            for k, v in old.items(): setattr(SC, k, v)
    orig_frac_index = SC.frac_index; orig_free_index = SC.free_index; orig_tempo = SC.tempo_f32; orig_convert = SC.convert

    def half_up(x):
        x = float(x); return int(math.floor(x + 0.5))
    def geo_index(fam, x):
        Fm = SC.FAMILIES[fam]
        if Fm["v2f"][1] == "bsearch": return orig_frac_index(fam, x)
        f = [a / b for a, b in Fm["fracs"]]
        if x <= 0: return min(range(len(f)), key=lambda k: f[k])
        return min(range(len(f)), key=lambda k: abs(math.log(f[k]) - math.log(x)))
    def ducker_round(fam, x):
        if SC.FAMILIES[fam]["v2i"][1] == "trunc_scale": return SC.round_to_int(SC.fmul(x, 10.0))
        return orig_free_index(fam, x)
    def identity_convert(fam, v, sync, T): return SC.clamp01_out(v), dict(j=None)
    alts = {"A1 no conversion (SYNC only re-interprets the stored value)": dict(convert=identity_convert),
            "A2 round half away from zero (not JUCE half-even)": dict(round_to_int=lambda x: half_up(x)),
            "A3 nearest fraction in the log domain (geometric midpoints)": dict(frac_index=geo_index),
            "A4 Ducker sync->free rounds (not truncates) ms*10": dict(free_index=ducker_round)}
    res = {}
    for name, kw in alts.items():
        bad = 0
        with patched(**kw):
            for ctx, case, bpm, v, w, sync, o in recs:
                try:
                    mo = SC.s34(ctx, case, v, w, sync, bpm)
                    if fb(mo["ed0"]) != o["ed0"] or (SC.CASES[ctx][case][0] == "ducker" and fb(mo["ed2"]) != o["ed2"]): bad += 1
                except Exception:                              # noqa: BLE001
                    bad += 1
        res[name] = bad
    J["alternatives"] = res
    check(all(b > 0 for b in res.values()), "alternatives scored against the %d emulated s34 cases, each refuted (mismatching cases): %s" % (
        len(recs), res))


def round_trip_table(J):
    """Model-only: for every free step i (and every sync step), does off->on->off (on->off->on) return the start value?"""
    out = {}
    for fam in ("chorus", "flanger", "phaser", "insert_delay", "send_delay", "ducker_attack", "ducker_release"):
        Fm = SC.FAMILIES[fam]
        for bpm in (20.0, 60.0, 120.0, 133.7, 300.0):
            T = SC.tempo_f32(bpm)
            flo, fhi = Fm["free"][1]; slo, shi = Fm["sync"][1]
            same_f = 0; sample_f = []
            for i in range(flo, fhi):
                v = SC.norm_of(flo, fhi, i)
                v1, _ = SC.convert(fam, v, 1, T); v2, d2 = SC.convert(fam, v1, 0, T)
                if fb(v2) == fb(v): same_f += 1
                elif len(sample_f) < 3: sample_f.append((i, d2["j"]))
            same_s = 0; sample_s = []
            for j in range(slo, shi):
                v = SC.norm_of(slo, shi, j)
                v1, d1 = SC.convert(fam, v, 0, T); v2, d2 = SC.convert(fam, v1, 1, T)
                if fb(v2) == fb(v): same_s += 1
                elif len(sample_s) < 3: sample_s.append((j, d1["j"], d2["j"]))
            out["%s/%g" % (fam, bpm)] = dict(free_same=same_f, free_n=fhi - flo, free_ex=sample_f, sync_same=same_s, sync_n=shi - slo,
                                             sync_ex=sample_s)
    J["round_trip"] = out
    return out



# ===================================================================================================================== C4 UI step + formatter
STEP = {"insert": 0x316a10, "sendmaster": 0x313ecc}
FORMATTER = {"insert": 0x314d4c, "sendmaster": 0x31235c}
STEP_MULT = 0x311aa0
LOGGER = 0x647ca0
STR_CTOR = 0x64a3fc
STR_FORMATTED = 0x635768
# (context, kind, k, family): kinds = the step routine's `kind` argument (Insert: FxParamIndex; the Delay boxes pass 11 -- H086
# stageD knob table: Insert/Master Delay Time kind 11 k0, Ducker Attack 69 k0, Release 67 k2); Chorus/Flanger/Phaser 0/5/61 found
# by the dispatch scan below.
C4_ROWS = [("insert", 0, 0, "chorus"), ("insert", 5, 0, "flanger"), ("insert", 11, 0, "insert_delay"), ("insert", 61, 0, "phaser"),
           ("insert", 69, 0, "ducker_attack"), ("insert", 67, 2, "ducker_release"),
           ("send", 0, 0, "chorus"), ("send", 5, 0, "flanger"), ("send", 11, 0, "send_delay"), ("send", 61, 0, "phaser"),
           ("master", 11, 0, "send_delay"), ("master", 0, 0, "chorus")]


def c4(im, check, J, Pr):
    import H086_ui_manager_calls as H86
    rig = H86.Rig(); e = rig.e
    # the H086 rig does not run .init_array: fill the BasicParamSpec fraction tables (.bss 0xf61f18) with the real init code
    # exactly as H077 EmuProc does (FRAC_INIT 0x6cbe0..0x6ce8c, r4 = 0xf61f18), so the formatter shows real fractions
    import H077_master_send_proc as H77
    for i_ in range(13): e.setr(i_, 0)
    e.setr(4, 0xf61f18); e.uc.reg_write(emu.SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
    e.uc.emu_start(H77.FRAC_INIT[0], H77.FRAC_INIT[1])
    check(all((e.u32(SC.FAMILIES[f_]["f2v"][1] + 4 * j) & 0xffff, e.u32(SC.FAMILIES[f_]["f2v"][1] + 4 * j) >> 16) == fr
              for f_ in ("chorus", "flanger", "phaser", "insert_delay", "send_delay") for j, fr in enumerate(SC.FAMILIES[f_]["fracs"])),
          "C4 rig: real fraction-table init code run in the UI rig; tables equal the model")
    for a in (0x7c1644, 0x7ccc24, 0x2ee918, 0x2ee9a0, 0x1ea258, 0x392a84): rig.skip(a)      # UI redraw stand-ins (as H086)
    from unicorn import arm_const as A
    log_hits = []
    def _logger(em):
        log_hits.append(em.uc.reg_read(A.UC_ARM_REG_LR)); em.setr(0, 0); em.uc.reg_write(A.UC_ARM_REG_PC, em.uc.reg_read(A.UC_ARM_REG_LR))
    e.add_watch(LOGGER, _logger)
    helpers = {}
    for fam, Fm in SC.FAMILIES.items():
        for key in ("free", "sync", "i2v", "v2i", "f2v", "v2f"): helpers[Fm[key][0]] = (fam, key)
    hits = []; fmts = []; fargs = []; mults = []
    for a_, fk in helpers.items(): e.add_watch(a_, lambda em, fk=fk: hits.append(fk))
    e.add_watch(STR_CTOR, lambda em: fmts.append(rig._cstr(em.r(1))))
    e.add_watch(STR_FORMATTED, lambda em: fargs.append((em.r(2), em.r(3))))
    no = rig._obj("cfg_item_false", lambda off: 0, 16)
    tbl = e.u32(rig.cfg + 8); arr = e.u32(tbl + 4); yes = e.u32(arr + 4 * 6)
    ref = rig.ctrl + 0x20

    def run(ctx, kind, k, delta, v, sync, rng, coarse):
        e.w32(rig.dm + 0x74, 1 if ctx == "insert" else 0); rig.send_mode = 0 if ctx == "master" else 1
        e.w32(arr + 4 * 6, no if coarse else yes)
        rig.state["param"] = v; rig.state["sync"] = sync; rig.state["rng"] = rng
        del hits[:], fmts[:], fargs[:], log_hits[:]
        got = rig.run(STEP["insert" if ctx == "insert" else "sendmaster"], ref, k, kind, delta & 0xffffffff)
        s27 = [(f2u(g["value"]), g["k"], g["ctx"]) for g in got if g["off"] == 0x10]
        return s27, list(dict.fromkeys(hits)), [f for f in fmts if f and "%" in f], list(fargs), list(log_hits)

    # dispatch scan: which kinds of each step routine use a time-family helper (sync off / on)
    scan = {}
    for ctx in ("insert", "send"):
        for kind in range(0, 0x48):
            for sync in (0, 1):
                try:
                    _, h, _, _, lg = run(ctx, kind, 0, 1, 0.5, sync, (0, 101), False)
                except Exception as ex:                       # noqa: BLE001
                    h, lg = [("ERR", str(ex)[:60])], []
                fams = sorted(set(f for f, _ in h if f != "ERR"))
                if fams: scan.setdefault("%s/%d" % (ctx, kind), {})[sync] = fams
    J["c4_scan"] = scan
    exp_scan = {"insert/0": "chorus", "insert/5": "flanger", "insert/11": "insert_delay", "insert/61": "phaser",
                "insert/67": "ducker_release", "insert/69": "ducker_attack", "send/0": "chorus", "send/5": "flanger",
                "send/11": "send_delay", "send/61": "phaser", "send/67": "ducker_release", "send/69": "ducker_attack"}
    ok = sorted(scan) == sorted(exp_scan) and all(scan[k_][s_] == [f_] for k_, f_ in exp_scan.items() for s_ in (0, 1))
    check(ok, "C4 dispatch scan (real step routines, kinds 0..71, sync 0/1): the only kinds that touch a time-family helper are %s" % (
        {k_: v_.get(0) for k_, v_ in sorted(scan.items())}))
    # step cases
    n = 0; bad = []; disp = {}
    vs = [0.0, 1.0, 0.5, 0.3, 0.77, 0.123]
    for ctx, kind, k, fam in C4_ROWS:
        Fm = SC.FAMILIES[fam]
        for sync in (0, 1):
            lo, hi = Fm["sync" if sync else "free"][1]
            for v in vs + [SC.norm_of(lo, hi, lo + 1), SC.norm_of(lo, hi, hi - 2)]:
                v = F(v)
                for delta in (1, -1, 2, -3, 7):
                    for coarse in (False, True):
                        s27, h, fm, fa, lg = run(ctx, kind, k, delta, v, sync, (lo, hi), coarse)
                        i = SC.step_of(lo, hi, v)
                        m = 1
                        if coarse and not sync:
                            m = s32(e.call(STEP_MULT, kind, i & 0xffffffff, delta & 0xffffffff)[0]); mults.append((fam, i, delta, m))
                        i2 = min(max(i + m * delta, lo), hi - 1)
                        exp = fb(SC.norm_of(lo, hi, i2))
                        want_ctx = {"insert": "Insert", "send": "Send", "master": "Master"}[ctx]
                        okc = s27 == [(exp, k, want_ctx)] and not lg
                        # display: free -> printf double = free value of the CURRENT step; sync -> '%d/%d' (num, den) or Ducker %.2f
                        if fm:
                            fmt = fm[-1]
                            if fmt == "%d/%d":
                                num, den = Fm["fracs"][i]
                                okd = fa and fa[-1] == (num, den)
                                shown = "%d/%d" % fa[-1] if fa else None
                            else:
                                dv = struct.unpack("<d", struct.pack("<II", *fa[-1]))[0] if fa else None
                                want = SC.frac_value(fam, i) if sync else SC.free_value(fam, i)
                                okd = dv == want; shown = fmt % dv if dv is not None else None
                        else:
                            fmt = None; okd = True; shown = None
                        disp.setdefault("%s/%s/%d" % (ctx, fam, sync), set()).add(fmt)
                        n += 1
                        if not (okc and okd): bad.append((ctx, kind, fam, sync, v, delta, coarse, s27, exp, fm, fa[-1:] if fa else None))
    J["c4_steps"] = dict(n=n, bad=[str(b)[:300] for b in bad[:20]], formats={k_: sorted(x for x in v_ if x) or [None]
                                                                             for k_, v_ in sorted(disp.items())},
                         coarse_mults=sorted(set((f_, m_) for f_, _, _, m_ in mults)))
    check(n >= 50 and not bad,
          "C4 real UI step routine (0x316a10 Insert / 0x313ecc Send-Master, real value formatter 0x314d4c / 0x31235c inside) on the H086 "
          "stub IEffector: %d cases (12 kind/context rows x SYNC 0/1 x 8 values x 5 deltas x fine/coarse): s27 value = (i' - lo)/(hi - 1 - lo)"
          " with i = roundToInt(lo + v(hi-1-lo)) of the family range of the CURRENT mode, i' = clamp(i + m*delta, lo, hi-1), m = 1 in "
          "sync mode or fine mode, m = 0x311aa0(kind, i, delta) in coarse free mode; display value = the current step's value: %d bad %s" % (
              n, len(bad), bad[:2]))
    Pr("  C4 display formats per context/family/sync: %s" % J["c4_steps"]["formats"])
    Pr("  C4 coarse-mode step sizes seen (family, m): %s" % J["c4_steps"]["coarse_mults"])
    # reachable values and their physical meaning through the existing effect models
    import chorus as C, flanger as FL, phaser as PH, insert_delay as ID, send_delay as SD
    eff_free = {"chorus": C.Chorus.free_hz if hasattr(C, "Chorus") else None}
    tab = {}; badmap = []
    for fam in ("chorus", "flanger", "phaser", "insert_delay", "send_delay", "ducker_attack", "ducker_release"):
        for sync in (0, 1):
            R = SC.reachable(fam, sync)
            # UI step i -> v -> the effect's own integer step (rint on the same range) must give i back for every reachable value
            lo, hi = SC.FAMILIES[fam]["sync" if sync else "free"][1]
            lossless = all(SC.step_of(lo, hi, v) == i for i, v, _ in R)
            if not lossless: badmap.append((fam, sync))
            tab["%s/%d" % (fam, sync)] = dict(n=len(R), first=R[0][2], last=R[-1][2], v_first=R[0][1], v_last=R[-1][1],
                                              step=(R[1][2] - R[0][2]) if len(R) > 1 else None)
    check(not badmap, "every reachable UI value v = (i - lo)/(hi - 1 - lo) maps back to the same integer step i under the effects' "
                      "roundToInt(lo + v(hi-1-lo)) (lossless UI <-> effect quantisation, 7 families x 2 modes) %s" % badmap)
    # physical values via the existing (bit-exact) effect models: the free value the UI displays is the value the effect uses
    ch = C.Chorus(); fl = FL.Flanger()
    phys_free = {"chorus": C.Chorus.free_hz, "flanger": FL.Flanger.free_hz, "phaser": PH.Phaser.rate_hz,
                 "insert_delay": ID.InsertDelay.free_ms, "send_delay": SD.SendDelay.free_ms}
    mism = []
    for fam, fn in phys_free.items():
        for i, v, x in SC.reachable(fam, 0):
            if fb(fn(v)) != fb(x): mism.append((fam, i))
    check(not mism, "free mode: for every reachable step the effect model's own value (Chorus/Flanger free_hz, Phaser rate_hz, "
                    "InsertDelay/SendDelay free_ms) equals the UI/s34 helper value (%d steps) %s" % (
                        sum(len(SC.reachable(f_, 0)) for f_ in phys_free), mism[:3]))
    rows = []
    for bpm in (60.0, 120.0, 133.7):
        b = F(bpm)
        for fam, fn in (("chorus", lambda v: ch.sync_hz(v, b)), ("flanger", lambda v: fl.sync_hz(v, b)),
                        ("phaser", lambda v: F(F(1000.0) / F(F(F(F(60000.0) / b) * F(float(PH.SYNC_FRACTIONS[PH.Phaser.sync_index(v)][0])))
                                                         / F(float(PH.SYNC_FRACTIONS[PH.Phaser.sync_index(v)][1]))))),
                        ("insert_delay", lambda v: ID.InsertDelay.sync_ms(v, b)), ("send_delay", lambda v: SD.SendDelay.sync_ms(v, b))):
            vals = [fn(v) for _, v, _ in SC.reachable(fam, 1)]
            rows.append((fam, bpm, ["%.4g" % x for x in vals]))
    J["c4_sync_physical"] = rows
    Pr("  C4 sync-mode reachable values -> effect quantity (Hz for rates, ms for delays) via the effect models:")
    for fam, bpm, vals in rows:
        if bpm in (60.0, 120.0): Pr("    %-12s %5.1f BPM: %s" % (fam, bpm, " ".join(vals)))
    J["c4_reachable"] = tab
    return tab


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H082"))
    ap.add_argument("--skip-c4", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []

    def Pr(s=""): rep.append(s); print(s, flush=True)

    def check(c, msg):
        Pr(("[PASS] " if c else "[FAIL] ") + msg)
        if not c: fails.append(msg)
    im = Image()
    Pr("H082 SYNC conversion. target sha256 %s" % sha(im.data))
    walks, cls = c1_static(im, check, J)
    import H077_master_send_proc as H77
    x = H77.EmuProc("insert")
    c1b_tables(im, check, J, x.e)
    c1c_helpers(check, J, x.e, cls)
    rows, total, recs, rigs = c2_c3(check, J)
    alternatives(check, J, recs)
    a5_cases(check, J, rigs)
    guest_mutant(check, J, rigs)
    Pr("  distinct ED+0x38 outputs per context/family/direction: %s" % J["c2_distinct_outputs"])
    rt = round_trip_table(J)
    Pr("== round trips (model, every step): family/bpm: free->sync->free same/n ; sync->free->sync same/n")
    for k, v in rt.items():
        Pr("  %-22s free %4d/%-5d  sync %3d/%-3d  ex_free(i,j')=%s ex_sync(j,i,j')=%s" % (
            k, v["free_same"], v["free_n"], v["sync_same"], v["sync_n"], v["free_ex"][:2], v["sync_ex"][:2]))
    if not a.skip_c4:
        c4(im, check, J, Pr)
    with open(os.path.join(a.out, "c2_cases.csv"), "w") as f:
        f.write("ctx,case,family,bpm,sync,v_in,w_in,ed0,ed2,calls\n"); f.write("\n".join(rows) + "\n")
    with open(os.path.join(a.out, "h082.json"), "w") as f: json.dump(J, f, indent=1, sort_keys=True, default=str)
    Pr("RESULT: %d failed checks" % len(fails))
    with open(os.path.join(a.out, "h082_report.txt"), "w") as f: f.write("\n".join(rep) + "\n")
    for nm in ("h082_report.txt", "h082.json", "c2_cases.csv"):
        print("  %s %s" % (nm, sha(open(os.path.join(a.out, nm), "rb").read())))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
