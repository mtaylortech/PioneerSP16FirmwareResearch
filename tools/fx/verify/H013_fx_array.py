#!/usr/bin/env python3
"""H013: InsertFxProcessor effect array this+0x80[] indexed by this+0xa4 (1.60, static).

C1  Constructor walk (Insert 0x118b0c; optional Master 0x114bc0 / Send 0x11bbe4): a linear register-tag tracker over the
    ctor body records every operator new (size), the first call made with that object in r0 (its ctor), the vptr stored
    at [obj+0] (inline, or found in the sub-ctor), member stores of new'ed objects, and every juce::Array append
    `str obj, [data, idx, lsl #2]`. Vtables are named from harness/out/H001/fx_classes.json (RTTI).
C2  Index field: reads/writes of +0xa4/+0xa8/+0x80/+0x88 in processBlock 0x116860, setFxType (vtable slot 47) and the
    ctor; the processBlock switch on the index; InsertFxParameterManager slot 53/54 tables (EFFECT_ID <-> index) and the
    slot-32 switch that calls processor vt+0xbc (slot 47) with constants.
C3  Index -> name: per index, (a) RTTI class from C1, (b) the FxType_* / name string the parameter manager's slot-32 case
    writes before calling setFxType(index), (c) the EFFECT_ID from the slot-53/54 tables, (d) whether processBlock feeds
    BPM (param 7) to that index, (e) whether the class ctor names a "BPM" parameter. Agreement of (a) and (b) is asserted.
Usage: .venv/bin/python harness/H013_fx_array.py [--out DIR]   (default harness/out/H013). Asserts the target SHA-256."""
import argparse, hashlib, json, os, re, struct, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import sp16img

ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(sp16img.ROOT, "harness", "out", "H013"))
A = ap.parse_args(); os.makedirs(A.out, exist_ok=True)
im = sp16img.Image(); plt = im.plt()
NEW = [va for va, n in plt.items() if n == "_Znwj"]; assert len(NEW) == 1; NEW = NEW[0]
FX = json.load(open(os.path.join(sp16img.ROOT, "harness", "out", "H001", "fx_classes.json")))
VT = {}; CLS = {}
for c in FX:
    CLS[c["name"]] = c
    for v in c["vtables"]: VT[int(v["address_point"], 16)] = (c["name"], v["offset_to_top"])
LOG = []; FAIL = []
def log(s=""): LOG.append(s); print(s)
def check(cond, msg):
    (LOG.append("  [ok] " + msg) if cond else (FAIL.append(msg), LOG.append("  [FAIL] " + msg))); print(("  [ok] " if cond else "  [FAIL] ") + msg)
def s32(x): return struct.unpack("<i", struct.pack("<I", x))[0]
def imm(tok):
    tok = tok.strip().lstrip("#"); return int(tok, 0)
def ancestors(name, seen=None):
    seen = set() if seen is None else seen
    c = CLS.get(name)
    if not c: return seen
    for b in c.get("bases") or []:
        n = b["name"]
        if n not in seen: seen.add(n); ancestors(n, seen)
    return seen

def body(lo, hi_ranges):
    out = []
    for a, b in hi_ranges: out += im.disasm(a, b)
    return out

RE_LIT = re.compile(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$")
RE_STR = re.compile(r"(\w+), \[(\w+)(?:, #(-?0x[0-9a-f]+|-?\d+))?\](?:, #(-?0x[0-9a-f]+|-?\d+))?$")
RE_IDX = re.compile(r"(\w+), \[(\w+), (\w+), lsl #2\]$")

def track(ins, this_reg="r0"):
    """Linear register-tag walk. Tags: ('this',), ('lit',v), ('imm',v), ('obj',k). Returns objects and events."""
    R = {this_reg: ("this",)}; objs = []; ev = []
    for i in ins:
        m, op = i.mnemonic, i.op_str
        mm = RE_LIT.match(op)
        if m == "ldr" and mm:
            R[mm.group(1)] = ("lit", im.u32(i.address + 8 + int(mm.group(2), 0))); continue
        if m in ("mov", "movw") and re.match(r"\w+, #", op):
            rd, v = op.split(", "); R[rd] = ("imm", imm(v) & 0xffffffff); continue
        if m == "mvn" and re.match(r"\w+, #", op):
            rd, v = op.split(", "); R[rd] = ("imm", (~imm(v)) & 0xffffffff); continue
        if m == "mov" and re.match(r"\w+, \w+$", op):
            rd, rs = op.split(", "); R[rd] = R.get(rs); continue
        if m in ("add", "addne") and re.match(r"(\w+), (\w+), #", op):   # addne: null-safe upcast `if (p) p += off`
            rd, rs, v = op.split(", ")
            t = R.get(rs); R[rd] = ("lit", (t[1] + imm(v)) & 0xffffffff) if t and t[0] == "lit" else (("objoff", t[1], imm(v)) if t and t[0] == "obj" else (("thisoff", imm(v)) if t and t[0] == "this" else None)); continue
        if m in ("bl", "blx") and op.startswith("#"):
            tg = imm(op)
            if tg == NEW:
                sz = R.get("r0"); k = len(objs)
                objs.append(dict(k=k, new_site=i.address, size=sz[1] if sz and sz[0] == "imm" else None, ctor=None, ctor_site=None,
                                 vptr=None, vptr_site=None, members=[]))
                for r in ("r0", "r1", "r2", "r3", "ip", "lr"): R.pop(r, None)
                R["r0"] = ("obj", k); continue
            t0 = R.get("r0")
            if t0 and t0[0] == "obj" and objs[t0[1]]["ctor"] is None:
                objs[t0[1]]["ctor"] = tg; objs[t0[1]]["ctor_site"] = i.address
            ev.append(("call", i.address, tg, t0))
            for r in ("r0", "r1", "r2", "r3", "ip", "lr"): R.pop(r, None)
            continue
        if m == "blx":
            ev.append(("vcall", i.address, op, R.get("r0"), R.get("r1")))
            for r in ("r0", "r1", "r2", "r3", "ip", "lr"): R.pop(r, None)
            continue
        if m == "str":
            mi = RE_IDX.match(op)
            if mi:
                v, b, x = mi.groups(); ev.append(("idxstore", i.address, R.get(v), R.get(b), R.get(x))); continue
            ms = RE_STR.match(op)
            if ms:
                v, b, off, post = ms.groups(); off = int(off, 0) if off else 0
                tv, tb = R.get(v), R.get(b)
                if tb and tb[0] == "obj":
                    o = objs[tb[1]]
                    if off == 0 and tv and tv[0] == "lit" and tv[1] in VT and o["vptr"] is None: o["vptr"], o["vptr_site"] = tv[1], i.address
                    elif tv and tv[0] == "obj": o["members"].append((off, tv[1], i.address))
                if tb and tb[0] == "this": ev.append(("thisstore", i.address, off, tv))
                if post and tb: R[b] = ("objoff", tb[1], int(post, 0)) if tb[0] == "obj" else None
                continue
        if m == "vst1.32" and re.match(r"\{d\d+\}, \[(\w+)\]$", op):
            b = re.match(r"\{d\d+\}, \[(\w+)\]$", op).group(1); ev.append(("vst1", i.address, R.get(b)))
            continue
        # any other write to a register clears its tag
        mr = re.match(r"(\w+)(?:,|$)", op)
        if mr and m not in ("cmp", "cmn", "tst", "teq", "push", "pop", "b", "bx", "vpush", "vpop") and not m.startswith(("str", "vst", "b")):
            R.pop(mr.group(1), None)
    return objs, ev

def subctor_vptr(fn):
    """Vptr stored at [this+0] inside a sub-ctor: last literal vtable stored at offset 0 via a this-alias."""
    s, e = im.func_of(fn); assert s == fn, hex(fn)
    _, ev = track(im.disasm(s, e)); hits = [(a, tv[1]) for k, a, off, tv in [x for x in ev if x[0] == "thisstore"]
                                            if off == 0 and tv and tv[0] == "lit" and tv[1] in VT]
    return hits

def ctor_report(name, ctor, ranges, own_vt):
    log("\n== %s ctor 0x%x  body %s" % (name, ctor, ["0x%x-0x%x" % r for r in ranges]))
    ins = body(ctor, ranges); objs, ev = track(ins)
    own = [(a, off, tv) for k, a, off, tv in [x for x in ev if x[0] == "thisstore"]]
    vps = [(a, tv[1]) for a, off, tv in own if off == 0 and tv and tv[0] == "lit" and tv[1] in VT]
    log("  own vptr stores at [this]: %s" % [("0x%x" % a, "0x%x" % v, VT[v][0]) for a, v in vps])
    check(any(v == own_vt for a, v in vps), "%s ctor stores its own vtable 0x%x at [this]" % (name, own_vt))
    fields = {}
    for a, off, tv in own:
        if off in (0xa4, 0xa8, 0x80, 0x84, 0x88, 0x8c, 0x90, 0xa0):
            fields.setdefault(off, []).append(("0x%x" % a, None if tv is None else (tv[0], "0x%x" % (tv[1] & 0xffffffff) if len(tv) > 1 and isinstance(tv[1], int) else tv)))
    for off in sorted(fields): log("  this+0x%x stores: %s" % (off, fields[off]))
    appends = [x for x in ev if x[0] == "idxstore" and x[2] and x[2][0] in ("obj", "objoff")]
    rows = []
    for n, (_, a, tv, tb, tx) in enumerate(appends):
        o = objs[tv[1]]; vp, vs, where = o["vptr"], o["vptr_site"], "inline"
        adj = tv[2] if tv[0] == "objoff" else 0     # pointer stored = obj + adj (base-subobject pointer)
        if vp is None and o["ctor"]:
            h = subctor_vptr(o["ctor"])
            if h: vs, vp = h[-1]; where = "in ctor 0x%x" % o["ctor"]
        cname = VT[vp][0] if vp in VT else None
        rows.append(dict(i=n, adj=adj, append_site="0x%x" % a, new_site="0x%x" % o["new_site"], size=o["size"], ctor="0x%x" % o["ctor"] if o["ctor"] else None,
                         vptr="0x%x" % vp if vp else None, vptr_site="0x%x" % vs if vs else None, vptr_where=where, cls=cname,
                         members=[("+0x%x" % off, "0x%x" % (objs[k]["size"] or 0), "0x%x" % (objs[k]["ctor"] or 0),
                                   VT.get(objs[k]["vptr"] or subctor_vptr(objs[k]["ctor"])[-1][1] if objs[k]["ctor"] and subctor_vptr(objs[k]["ctor"]) else objs[k]["vptr"], ("?",))[0])
                                  for off, k, _a in o["members"]]))
        r = rows[-1]
        log("  [%d] append@%s%s new(0x%x)@%s ctor=%s vptr=%s (%s @%s) class=%s members=%s" % (
            n, r["append_site"], (" (stores obj+0x%x)" % adj) if adj else "", r["size"] or 0, r["new_site"], r["ctor"], r["vptr"], where, r["vptr_site"], cname, r["members"]))
    vc = [(x[1], x[2], x[3], x[4]) for x in ev if x[0] == "vcall"]
    return rows, objs, ev, vc

OUT = {}
# ---------------------------------------------------------------- C1 Insert
log("# H013 FX processor effect arrays (1.60 EP085_Main_R_fw160 sha256 %s)" % sp16img.SHA)
INS_RANGES = [(0x118b0c, 0x1192c8), (0x1192f4, 0x1197d8)]   # Ghidra body (REA procedure_info): 0x118b0c-0x1192c7, 0x1192f4-0x1197d7
rows, objs, ev, vc = ctor_report("InsertFxProcessor", 0x118b0c, INS_RANGES, 0x842c10)
check(len(rows) == 10, "InsertFxProcessor ctor appends exactly 10 objects to this+0x80 (got %d)" % len(rows))
check(all(r["cls"] for r in rows), "every appended object has an RTTI-named vtable")
check(all("EffectBase" in ancestors(r["cls"]) for r in rows if r["cls"]), "every appended class derives from EffectBase")
check(len(set(r["cls"] for r in rows)) == len(rows), "no class appears twice")
# ldr/str count field +0x88 and data +0x80 inside the append sequences
cnt88 = [x for x in ev if x[0] == "thisstore" and x[2] == 0x88]
log("  stores to this+0x88 (count): %d sites %s" % (len(cnt88), ["0x%x" % x[1] for x in cnt88]))
# post-build per-element virtual calls
slot = lambda op: None
for a, op, t0, t1 in vc: pass
OUT["insert_ctor"] = rows
# ---------------------------------------------------------------- C1b: post-build calls (decoded from the listing, indices from ldr [data,#4i])
post = []
L = body(0x118b0c, INS_RANGES)
for k, i in enumerate(L):
    if i.mnemonic == "blx" and 0x119300 <= i.address < 0x1197d8:
        win = L[max(0, k - 8):k]
        sl = [w for w in win if re.match(r"r3, \[r3, #(0x[0-9a-f]+)\]$", w.op_str) and w.mnemonic == "ldr"]
        el = [w for w in win if re.match(r"r0, \[r3(?:, #(0x[0-9a-f]+|\d+))?\]$", w.op_str) and w.mnemonic.startswith("ldr")]
        a1 = [w for w in win if re.match(r"r1, #", w.op_str) and w.mnemonic == "mov"]
        thisv = [w for w in win if w.op_str == "r0, r4" and w.mnemonic == "mov"]
        if sl:
            off = int(re.match(r"r3, \[r3, #(0x[0-9a-f]+)\]$", sl[-1].op_str).group(1), 16)
            idx = (int(re.match(r"r0, \[r3(?:, #(0x[0-9a-f]+|\d+))?\]$", el[-1].op_str).group(1) or "0", 0) // 4) if el and not thisv else None
            post.append((i.address, off // 4, "this" if thisv or not el else "elem[%d]" % idx, imm(a1[-1].op_str.split(", ")[1]) if a1 else None))
    if i.mnemonic == "bl" and 0x119300 <= i.address < 0x1197d8 and i.op_str.startswith("#"):
        post.append((i.address, "bl 0x%x" % imm(i.op_str), None, None))
log("  post-build calls (site, vslot|bl, object, r1):")
for p in post: log("    0x%x %s %s r1=%s" % (p[0], p[1] if isinstance(p[1], str) else "vt slot %d" % p[1], p[2], p[3]))
s22 = sorted(int(p[2][5:-1]) for p in post if p[1] == 22 and p[2] and p[2].startswith("elem"))
s52 = sorted(p[3] for p in post if p[1] == 52 and p[2] == "this")
log("  slot 22 (+0x58, r1=0) called on elements %s; own slot 52 (+0xd0) called with r1=%s" % (s22, s52))
check(s22 == [0, 1, 2, 3, 4, 5, 6, 8, 9] and s52 == list(range(10)), "post-build: elem slot 22 on all but index 7; own slot 52 for 0..9")
OUT["insert_post"] = [dict(site="0x%x" % p[0], what=p[1], obj=p[2], r1=p[3]) for p in post]

# ---------------------------------------------------------------- C2 index field
log("\n== C2 index field")
def acc(lo, hi, offs=(0x80, 0x88, 0xa4, 0xa8, 0x8c, 0x90)):
    out = []
    for i in im.disasm(lo, hi):
        m = re.search(r"\[(\w+), #(0x[0-9a-f]+)\]", i.op_str)
        if m and int(m.group(2), 16) in offs and (i.mnemonic.startswith("ldr") or i.mnemonic.startswith("str")):
            out.append("0x%x %s %s" % (i.address, i.mnemonic, i.op_str))
        if i.mnemonic.startswith("vst1") or (i.mnemonic.startswith("add") and re.search(r"#0x(a4|8c)$", i.op_str)):
            out.append("0x%x %s %s" % (i.address, i.mnemonic, i.op_str))
        if re.search(r"lsl #2\]", i.op_str) and i.mnemonic.startswith("ldr"): out.append("0x%x %s %s" % (i.address, i.mnemonic, i.op_str))
    return out
s5 = im.u32(0x842c10 + 5 * 4); s47 = im.u32(0x842c10 + 47 * 4); s46 = im.u32(0x842c10 + 46 * 4); s48 = im.u32(0x842c10 + 48 * 4); s45 = im.u32(0x842c10 + 45 * 4)
check(s5 == 0x116860, "InsertFxProcessor slot 5 = 0x116860 (processBlock)")
check((s45, s46, s47, s48) == (0x11681c, 0x119900, 0x11735c, 0x116838), "slots 45/46/47/48 = 0x11681c/0x119900/0x11735c/0x116838")
pb = acc(0x116860, im.func_of(0x116860)[1]); log("  processBlock 0x116860 field accesses:"); [log("    " + x) for x in pb]
check("0x1168bc ldr r3, [r4, #0xa4]" in pb and "0x1168c0 ldr sl, [r4, #0xa8]" in pb, "processBlock reads current +0xa4 @0x1168bc and pending +0xa8 @0x1168c0")
check("0x116900 str sl, [r4, #0xa4]" in pb, "processBlock writes current := pending @0x116900")
sf = acc(0x11735c, 0x117434); log("  setFxType slot 47 0x11735c accesses:"); [log("    " + x) for x in sf]
check("0x1173b0 str r5, [r4, #0xa8]" in sf and "0x11741c vst1.32 {d16}, [r4]" in sf and "0x117418 add r4, r4, #0xa4" in sf,
      "setFxType writes pending +0xa8 (0x1173b0) and, when current==-1, both +0xa4/+0xa8 (vst1 @0x11741c)")
L5 = {i.address: "%s %s" % (i.mnemonic, i.op_str) for i in im.disasm(0x116860, im.func_of(0x116860)[1])}
check(L5.get(0x116934) == "ldr r5, [r2, r3, lsl #2]" and L5.get(0x116930) == "ldr r2, [r4, #0x80]" and L5.get(0x11692c) == "bhs #0x116a80",
      "0x116928-0x116934: if (cur <u count) r5 = this+0x80[cur], else skip to 0x116a80 (cur = -1 -> no effect)")
check(L5.get(0x116a64) == "ldr ip, [r5]" and L5.get(0x116a78) == "ldr ip, [ip, #0x48]" and L5.get(0x116a74) == "mov r3, #0x40",
      "0x116a64-0x116a7c: r5->vt[18] (+0x48)(r5, L, R, 0x40) - the effect run is array[cur]")
check(L5.get(0x1168fc) == "mov r3, sl" and L5.get(0x116acc) == "mov r3, sl" and L5.get(0x116bb0) == "mov r3, sl" and L5.get(0x1168cc) == "movlt sl, r3",
      "every path into 0x116928 sets r3 = sl = current index (+0xa4 or pending just copied into +0xa4)")
# alternative: array or index written elsewhere? scan every InsertFxProcessor own-slot function (not shared with
# FxProcessorBase) + the ctor + 0x117434 for stores to +0x80/+0x84/+0x88/+0xa4/+0xa8 (and vst1 via add #0xa4)
own_slots = sorted(set(int(a["target"], 16) for a, b in zip(CLS["InsertFxProcessor"]["vtables"][0]["slots"], CLS["FxProcessorBase"]["vtables"][0]["slots"]) if a["target"] != b["target"]))
W = {}
for f in own_slots + [0x117434]:
    a, e = im.func_of(f)
    if a != f: continue
    for i in im.disasm(f, e):
        m = re.search(r"\[(\w+), #(0x[0-9a-f]+)\]", i.op_str)
        if i.mnemonic.startswith("str") and m and int(m.group(2), 16) in (0x80, 0x84, 0x88, 0xa4, 0xa8): W.setdefault("0x%x" % f, []).append("0x%x %s %s" % (i.address, i.mnemonic, i.op_str))
        if i.mnemonic.startswith("add") and i.op_str.endswith("#0xa4"): W.setdefault("0x%x" % f, []).append("0x%x %s %s" % (i.address, i.mnemonic, i.op_str))
log("  writers of +0x80/+0x84/+0x88/+0xa4/+0xa8 among own slots %s (+0x117434): %s" % (["0x%x" % x for x in own_slots], W))
vt_users = sorted(set(sp16img.Image.func_of(im, site)[0] for kind, site in sp16img.const_sites(im, [0x842c10])[0x842c10]))
log("  functions materialising InsertFxProcessor vtable 0x842c10: %s" % ["0x%x" % x for x in vt_users])
OUT["alt_writers"] = W; OUT["vt_842c10_users"] = ["0x%x" % x for x in vt_users]
# processBlock switch on the current index
pbins = im.disasm(0x116860, im.func_of(0x116860)[1])
jt = None
for k, i in enumerate(pbins):
    if i.mnemonic == "ldrls" and i.op_str.startswith("pc, [pc,"):
        n = imm(pbins[k - 1].op_str.split(", ")[1]) + 1; base = i.address + 8
        jt = [im.u32(base + 4 * j) for j in range(n)]; jt_site = i.address; jt_reg = pbins[k - 1].op_str
        dflt = imm(pbins[k + 1].op_str)
log("  processBlock switch @0x%x on %s: targets %s default 0x%x" % (jt_site, jt_reg, ["0x%x" % t for t in jt], dflt))
groups = {}
for j, t in enumerate(jt): groups.setdefault(t, []).append(j)
nondef = {t: js for t, js in groups.items() if t != dflt}
log("  non-default case groups: %s" % {("0x%x" % t): js for t, js in nondef.items()})
bpm_idx = sorted(j for js in nondef.values() for j in js)
OUT["pb_switch"] = dict(site="0x%x" % jt_site, groups={("0x%x" % t): js for t, js in groups.items()}, default="0x%x" % dflt)
# slot 45 table
t45 = [im.u32(0x842be0 + 4 * j) for j in range(10)]
log("  slot 45 0x11681c returns table 0x842be0[cur] for cur<=9 else 1: %s" % t45)

# ---------------------------------------------------------------- parameter manager: slot 53/54 tables and slot 32 switch
log("\n== C2 hop: InsertFxParameterManager (vtable 0x84407c)")
m53, m54, m32 = im.u32(0x84407c + 53 * 4), im.u32(0x84407c + 54 * 4), im.u32(0x84407c + 32 * 4)
check((m53, m54, m32) == (0x1262b0, 0x1262cc, 0x1287d4), "IFPM slots 53/54/32 = 0x1262b0/0x1262cc/0x1287d4")
TB = 0x843d98
fwd = {e: s32(im.u32(TB + 4 * (e - 1))) for e in range(1, 21)}
rev = [s32(im.u32(TB + 0x50 + 4 * j)) for j in range(10)]
log("  slot 53: index = T[EFFECT_ID-1] for 1<=EFFECT_ID<=20 else -1, T@0x%x: %s" % (TB, fwd))
log("  slot 54: EFFECT_ID = T[0x50/4 + index] for index<=9 else -1: %s" % rev)
check(all(fwd[rev[j]] == j for j in range(10)), "tables are mutually inverse on the 10 valid indices")
check(sorted(e for e, v in fwd.items() if v >= 0) == list(range(1, 21))[0:1] + list(range(4, 21, 2)), "valid EFFECT_IDs are 1 and the even IDs 4..20")
# slot 32 switch: cases = index = slot53(arg); each calls processor vt+0xbc (slot 47) with a constant
def manager_switch(fn, label):
    """Switch `cmp r5,#9; ldrls pc,...` in a parameter-manager function: per case, the r1 constant passed to the
    processor's vt+0xbc (slot 47) call and the static String (`ldr r0,=S; ldr r1,="txt"; bl 0x666e84`) loaded into r1
    on the way. Unconditional `b` is followed; conditional branches fall through."""
    L32 = im.disasm(fn, im.func_of(fn)[1]); INS32 = {i.address: (k, i) for k, i in enumerate(L32)}
    SOBJ = {}
    for k in range(len(L32) - 2):
        a, b, c = L32[k], L32[k + 1], L32[k + 2]
        ma, mb = RE_LIT.match(a.op_str), RE_LIT.match(b.op_str)
        if a.mnemonic == "ldr" and b.mnemonic == "ldr" and ma and mb and ma.group(1) == "r0" and mb.group(1) == "r1" and c.op_str == "#0x666e84":
            SOBJ[im.u32(a.address + 8 + int(ma.group(2), 0))] = (im.cstr(im.u32(b.address + 8 + int(mb.group(2), 0))), b.address)
    log("  [%s 0x%x] static String objects (obj -> text @site): %s" % (label, fn, {("0x%x" % o): (t, "0x%x" % s) for o, (t, s) in SOBJ.items()}))
    k0 = [k for k, i in enumerate(L32) if i.mnemonic == "ldrls" and i.op_str.startswith("pc, [pc,")][0]
    cmpi = L32[k0 - 1]; n = imm(cmpi.op_str.split(", ")[1]) + 1; base = L32[k0].address + 8
    cases = [im.u32(base + 4 * j) for j in range(n)]; dflt32 = imm(L32[k0 + 1].op_str)
    log("  [%s] switch @0x%x on %s: %s default 0x%x" % (label, L32[k0].address, cmpi.op_str, ["0x%x" % c for c in cases], dflt32))
    def follow(start, limit=80):
        k = INS32[start][0]; s_obj = None; r1 = None; steps = 0
        while steps < limit:
            i = L32[k]; steps += 1
            mm = RE_LIT.match(i.op_str)
            if i.mnemonic == "ldr" and mm and mm.group(1) == "r1":
                v = im.u32(i.address + 8 + int(mm.group(2), 0))
                if v in SOBJ: s_obj = v
            if i.mnemonic == "mov" and re.match(r"r1, #", i.op_str): r1 = imm(i.op_str.split(", ")[1])
            if i.mnemonic == "mvn" and re.match(r"r1, #", i.op_str): r1 = s32(~imm(i.op_str.split(", ")[1]) & 0xffffffff)
            if i.mnemonic == "ldr" and i.op_str == "r3, [r3, #0xbc]":
                return dict(vcall_site="0x%x" % L32[k + 1].address, arg=r1, name=SOBJ[s_obj][0] if s_obj else None, name_site="0x%x" % SOBJ[s_obj][1] if s_obj else None)
            if i.mnemonic == "b" and i.op_str.startswith("#"): k = INS32[imm(i.op_str)][0]; continue
            k += 1
        return None
    MAP = {}
    for c, t in enumerate(cases):
        r = follow(t); MAP[c] = r; log("    case %d @0x%x -> setFxType(%s) @%s, name %r (init @%s)" % (c, t, r["arg"], r["vcall_site"], r["name"], r["name_site"]))
    rd = follow(dflt32); log("    default @0x%x -> setFxType(%s) @%s, name %r" % (dflt32, rd["arg"], rd["vcall_site"], rd["name"]))
    return MAP, rd
MAP, rd = manager_switch(0x1287d4, "InsertFxParameterManager slot 32")
check(all(MAP[c]["arg"] == c for c in MAP), "slot-32 case c calls setFxType(c): identity (switch value is already the processor index)")
check(rd["arg"] == -1 and rd["name"] == "Off", "default (index -1 / unmapped EFFECT_ID) calls setFxType(-1) with name 'Off'")

# ---------------------------------------------------------------- C3 mapping table
log("\n== C3 index -> FX type")
def norm(s): return re.sub(r"^FxType_", "", s or "").lower().replace("insert", "")
ALIAS = {"chorus": "chorus", "flanger": "flanger", "2bandeq": "parametricequalizer", "multimodefilter": "multimodefilter",
         "delay": "insertfxdelay", "lofi": "lofi", "distortion": "distortion", "compressor": "insertfxcompressor",
         "phaser": "phaser", "ducker": "ducker"}
bpm_ctor = {}
for r in rows:
    fn = int(r["ctor"], 16) if r["ctor"] else None
    names = []
    rng = [(0x118b0c, 0x1197d8)] if r["vptr_where"] == "inline" else [im.func_of(fn)]
    if r["vptr_where"] == "inline":
        # inline ctor: strings between this object's new and its append
        a0, a1 = int(r["new_site"], 16), int(r["append_site"], 16); rng = [(a0, a1)]
    for a, b in rng:
        for x in sp16img.annotate(im, a, end=b):
            m = re.search(r'"([^"]+)"$', x)
            if m: names.append(m.group(1))
    bpm_ctor[r["i"]] = "BPM" in names or "Bpm" in names
TABLE = []
for r in rows:
    j = r["i"]; nm = MAP[j]["name"]; eid = rev[j]
    agree = ALIAS.get(norm(nm)) == (r["cls"] or "").lower()
    TABLE.append(dict(index=j, rtti_class=r["cls"], manager_name=nm, effect_id=eid, pb_bpm_case=j in bpm_idx,
                      ctor_names_BPM=bpm_ctor[j], size=r["size"], ctor=r["ctor"], vptr=r["vptr"], agree=agree))
    log("  [%d] %-20s manager %-24r EFFECT_ID %2d  processBlock-BPM-case %-5s ctor-has-'BPM' %-5s  agree=%s" % (
        j, r["cls"], nm, eid, j in bpm_idx, bpm_ctor[j], agree))
check(all(t["agree"] for t in TABLE), "manager case name agrees with RTTI class for all 10 indices")
check(sorted(bpm_idx) == [0, 1, 4, 8, 9], "processBlock BPM cases are indices {0,1,4,8,9} (Chorus, Flanger, Delay, Phaser, Ducker)")
OUT["map"] = TABLE; OUT["effect_id_fwd"] = fwd

# ---------------------------------------------------------------- C4 Master / Send (optional)
log("\n== C4 Master / Send processors (optional)")
# Ghidra body ranges from REA procedure_info (literal pool between the two pieces is skipped)
C4 = (("MasterFxProcessor", 0x114bc0, 0x842aa8, [(0x114bc0, 0x115360), (0x11538c, 0x115890)]),
      ("SendFxProcessor", 0x11bbe4, 0x842d40, [(0x11bbe4, 0x11c38c), (0x11c3bc, 0x11c8c0)]))
for nm, ctor, vt, rngs in C4:
    rr, _, ev2, _ = ctor_report(nm, ctor, rngs, vt)
    OUT[nm] = rr
    check(len(rr) == 10, "%s ctor appends 10 objects (got %d)" % (nm, len(rr)))
    own = [im.u32(vt + 4 * k) for k in (5, 45, 46, 47, 48)]
    log("  %s slots 5/45/46/47/48 = %s" % (nm, ["0x%x" % x for x in own]))
    sf2 = acc(own[3], im.func_of(own[3])[1], offs=(0xa0, 0xa4, 0xa8)); log("  slot 47 (+0xa0/+0xa4/+0xa8) accesses: %s" % sf2)
    pb2 = acc(own[0], im.func_of(own[0])[1], offs=(0xa0, 0xa4, 0xa8)); log("  slot 5 processBlock (+0xa0/+0xa4/+0xa8 and indexed loads): %s" % pb2)
    log("  %s classes by index: %s" % (nm, [r["cls"] for r in rr]))

# Master/Send parameter managers: slot 53/54 tables and the setFxType switch
for mname, mvt in (("MasterFxParameterManager", 0x8437ec), ("SendFxParameterManager", 0x8446d4)):
    f53, f54 = im.u32(mvt + 53 * 4), im.u32(mvt + 54 * 4)
    log("  %s slot 53 0x%x: %s" % (mname, f53, " | ".join(sp16img.annotate(im, f53, end=f53 + 0x18))))
    log("  %s slot 54 0x%x: %s" % (mname, f54, " | ".join(sp16img.annotate(im, f54, end=f54 + 0x18))))
    sites = []
    for v in CLS[mname]["vtables"]:
        for sl in v["slots"]:
            t = int(sl["target"], 16); a, e = im.func_of(t)
            if a != t or not e: continue
            ins = im.disasm(t, e)
            n = sum(1 for x in ins if x.mnemonic == "ldr" and x.op_str == "r3, [r3, #0xbc]")
            if n and (v["address_point"], sl["i"], t) not in sites: sites.append((v["address_point"], sl["i"], t, n))
    log("  %s slots containing vt+0xbc calls: %s" % (mname, [(ap, i, "0x%x" % t, n) for ap, i, t, n in sites]))
MM, mrd = manager_switch(0x1237cc, "MasterFxParameterManager slot 32")
MALIAS = {"delay": "sendfxdelay", "reverb": "sendfxreverb", "chorus": "chorus", "flanger": "flanger", "2bandeq": "parametricequalizer",
          "multimodefilter": "multimodefilter", "lofi": "lofi", "compressor": "sendfxcompressor", "distortion": "distortion", "phaser": "phaser"}
check(all(MM[j]["arg"] == j and MALIAS.get(norm(MM[j]["name"])) == (OUT["MasterFxProcessor"][j]["cls"] or "").lower() for j in range(10)),
      "Master manager case j -> setFxType(j) and its name matches the RTTI class of MasterFxProcessor array[j] for all 10")
for mname, tb, n in (("MasterFxParameterManager", 0x8436e0, 18), ("SendFxParameterManager", 0x8445c8, 18)):
    f = {e: s32(im.u32(tb + 4 * e)) for e in range(n)}; r = [s32(im.u32(tb + 0x48 + 4 * j)) for j in range(10)]
    log("  %s slot 53 EFFECT_ID 0..17 -> index (T@0x%x): %s ; slot 54 index -> EFFECT_ID: %s" % (mname, tb, f, r))
    OUT[mname + "_tables"] = dict(fwd=f, rev=r)
OUT["master_manager_switch"] = {str(k): v for k, v in MM.items()}

open(os.path.join(A.out, "h013_report.txt"), "w").write("\n".join(LOG) + "\n")
json.dump(OUT, open(os.path.join(A.out, "h013.json"), "w"), indent=1, sort_keys=True)
log("\nassertions failed: %d" % len(FAIL))
for p in ("h013_report.txt", "h013.json"):
    print(p, hashlib.sha256(open(os.path.join(A.out, p), "rb").read()).hexdigest())
sys.exit(1 if FAIL else 0)
