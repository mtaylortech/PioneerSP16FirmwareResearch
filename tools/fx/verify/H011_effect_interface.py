#!/usr/bin/env python3
"""H011 — the effect plug-in interface of the 1.60 FX code (EffectBase virtual interface, object layout, how effects are created and
selected, host-side registration points, and a stub effect hosted through the real dispatcher / processor).

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Emulation is guest-memory only (unicorn); nothing is written
outside --out, and no image is built. Own code only; Pioneer bytes are read at run time and never stored.

Sections (criteria of kb/cycles/025.md):
  C1  slot matrix: own RTTI walk (typeinfo objects by their libstdc++ vptr values, si/vmi bases) -> EffectBase closure -> every vtable group
      of those classes (incl. secondary groups) -> slot targets by the F009 end rule; plus an independent sweep for every .rodata word equal
      to EffectBase slot 18 0x106de4 (catches vtables outside the RTTI closure, e.g. construction vtables). Matrix base/override/pure/extra.
  C2  slot roles: instruction assertions on every base slot body + a typed static vcall scan (register tags: this / effect-from-processor
      array or +0x8c/+0x90 / manager->processor) over all EffectBase-family methods, the FX processors and the parameter managers, plus a
      whole-.text vcall-offset census; dynamic caller log from the emulation in C6.
  C3  EffectBase layout: real EffectBase ctor 0x1067d8 emulated on a 0xA5-filled blob (written bytes + initial values), member RTTI,
      sizeof from the dtor member loop and the vmi second-base offsets, ctor-argument census at every call of 0x1067d8.
  C4  creation: every materialisation of every EffectBase-family vptr, every call of 0x1067d8 and of each concrete ctor, operator new
      sizes, containing functions; jump tables inside the processor ctors; dtor callers.
  C5  host-side registration points: jump tables (cmp #N; ldrls/addls pc) and index tables in processor / manager methods.
  C6  stub effect: real EffectBase ctor + our own vtable copy whose slots 23..27 are our own routines (Python hooks), driven through the
      real slot 18 0x106de4 and through the real InsertFxProcessor processBlock 0x116860 / setFxType 0x11735c; observed vs predicted.
Run: .venv/bin/python -B harness/H011_effect_interface.py --out DIR
"""
import argparse, bisect, hashlib, json, math, os, re, struct, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE)
import darwin_ctr_fix                                         # noqa: E402
darwin_ctr_fix.install()
import sp16img                                                # noqa: E402

TI_VPTR = {0xb81800: "class", 0xb81948: "si", 0xb81748: "vmi"}     # F007 (COPY + 8)
EB_VT, EB_CTOR, EB_DTOR, EB_SLOT18 = 0x841fb8, 0x1067d8, 0x106640, 0x106de4
NEW, NEWA = 0x102e8, 0x109fc                                          # PLT _Znwj / _Znaj
PROC_VT = {"InsertFxProcessor": 0x842c10, "MasterFxProcessor": 0x842aa8, "SendFxProcessor": 0x842d40}
PROC_CTOR = {"InsertFxProcessor": 0x118b0c, "MasterFxProcessor": 0x114bc0, "SendFxProcessor": 0x11bbe4}
MEMRE = re.compile(r"^(\w+), \[(\w+)(?:, #(-?0x[0-9a-f]+|-?\d+))?\](!?)(?:, #(-?0x[0-9a-f]+|-?\d+))?$")
REG = {"sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12"}


def rn(r): return REG.get(r, r)


COND = ("eq", "ne", "cs", "hs", "cc", "lo", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al")
BASEOPS = {"ldr", "str", "ldrb", "strb", "ldrh", "strh", "mov", "mvn", "add", "sub", "rsb", "vldr", "vstr", "blx", "bl", "b", "bx",
           "orr", "and", "eor", "bic", "lsl", "lsr", "asr", "mul", "pop", "push", "ldm", "stm", "cmp", "vmov"}


def split_cond(m):
    """('ldr', True) for 'ldrlo'; ('blx', False) for 'blx'; branch mnemonics like 'blo' -> ('b', True)."""
    if m in BASEOPS: return m, False
    if len(m) > 2 and m[-2:] in COND and m[:-2] in BASEOPS: return m[:-2], True
    return m, False


def dis(im, lo, hi):
    """capstone ARM disassembly of [lo, hi) that skips undecodable words instead of stopping."""
    out = []; a = lo
    while a < hi:
        got = False
        for i in im.md.disasm(im.data[im.off(a):im.off(hi)], a):
            out.append(i); a = i.address + i.size; got = True
        if a < hi:
            a += 4
    return out
def sha(b): return hashlib.sha256(b).hexdigest()


# ===================================================================================================================== RTTI / vtables
class Rtti:
    def __init__(self, im):
        self.im = im
        tlo, thi = im.sec[".text"]; plo, phi = im.sec[".plt"]
        self.is_code = lambda w: (tlo <= w < thi) or (plo <= w < phi)
        self.plt = im.plt()
        words = {}
        for va, sz, off in im.segs:
            n = sz // 4
            for i, w in enumerate(struct.unpack_from("<%dI" % n, im.data, off)):
                words[va + 4 * i] = w
        self.words = words
        self.ti = {}
        for a, w in words.items():
            if w in TI_VPTR:
                kind = TI_VPTR[w]; nm = im.cstr(words.get(a + 4, 0) or 0, 200)
                if not nm or not re.match(r"^[0-9A-Za-z_]+$", nm): continue
                bases = []
                if kind == "si": bases = [(words.get(a + 8), 0)]
                elif kind == "vmi":
                    nb = words.get(a + 12, 0)
                    if nb > 64: continue
                    bases = [(words.get(a + 16 + 8 * k), words.get(a + 20 + 8 * k)) for k in range(nb)]
                self.ti[a] = dict(kind=kind, name=nm, bases=bases)
        basefield = set()
        for a, t in self.ti.items():
            if t["kind"] == "si": basefield.add(a + 8)
            if t["kind"] == "vmi": basefield.update(a + 16 + 8 * k for k in range(len(t["bases"])))
        self.groups = []                       # (ott_addr, typeinfo, ott, address_point)
        rlo, rhi = im.sec[".rodata"]
        for a, w in words.items():
            if w in self.ti and a not in basefield and rlo <= a < rhi:
                ott = words.get(a - 4)
                if ott is None: continue
                otts = ott - (1 << 32) if ott & 0x80000000 else ott
                if -0x10000 <= otts <= 0:
                    self.groups.append((a - 4, w, otts, a + 4))
        self.groups.sort()
        self.group_starts = {g[0] for g in self.groups}
        self.ti_starts = set(self.ti)

    def slots(self, ap):
        out = []; a = ap
        while True:
            w = self.words.get(a)
            if w is None or not self.is_code(w) or a in self.group_starts or a in self.ti_starts:
                break
            out.append(w); a += 4
        return out

    def name(self, ti): return self.ti[ti]["name"].lstrip("0123456789")

    def closure(self, root_ti):
        """typeinfos that have root as a (transitive) base, with the base sub-object offset."""
        res = {root_ti: 0}; changed = True
        while changed:
            changed = False
            for a, t in self.ti.items():
                if a in res: continue
                for b, of in t["bases"]:
                    if b in res:
                        off = 0 if t["kind"] == "si" else ((of or 0) >> 8)
                        res[a] = res[b] + off; changed = True; break
        return res


# ===================================================================================================================== typed vcall scan
def _step(i, tags, ctx, vc, acc):
    """Transfer function of one instruction on a register-tag map (mutates tags). Records vcalls / this-field accesses."""
    m, op = i.mnemonic, i.op_str
    m, cond = split_cond(m)
    ops = [rn(x.strip()) for x in op.split(",")] if op else []
    def kill(r, cond=cond):
        if not cond: tags.pop(r, None)
    if m == "blx" and len(ops) == 1:
        t = tags.get(ops[0])
        if t and t[0] == "slot": vc.add((i.address, t[1], t[2]))
        for r in ("r0", "r1", "r2", "r3", "r12", "lr"): tags.pop(r, None)
        return
    if m == "bl":
        tgt = int(op.lstrip("#"), 0)
        t0 = tags.get("r0")
        if t0 and t0[0] == "eff": vc.add((i.address, t0, -tgt))        # direct (non-virtual) call with an effect as r0
        for r in ("r0", "r1", "r2", "r3", "r12", "lr"): tags.pop(r, None)
        if tgt == NEW: tags["r0"] = ("new", i.address)
        return
    if m in ("mov", "cpy") and len(ops) == 2 and not ops[1].startswith("#"):
        if ops[1] in tags: tags[ops[0]] = tags[ops[1]]
        else: kill(ops[0])
        return
    mm = MEMRE.match(op)
    if m in ("ldr", "str", "strb", "ldrb", "vldr", "vstr", "strh", "ldrh") and mm:
        rd, rb = rn(mm.group(1)), rn(mm.group(2)); off = int(mm.group(3) or "0", 0)
        if mm.group(5): off = 0
        bt = tags.get(rb)
        if bt and bt[0] == "this":
            acc.add((i.address, "w" if m.startswith(("str", "vstr")) else "r", off, "%s %s" % (i.mnemonic, op)))
        if m == "ldr":
            nt = None
            if bt is not None:
                if bt[0] in ("this", "eff", "proc", "new") and off == 0: nt = ("vt", bt)
                elif bt[0] == "vt": nt = ("slot", bt[1], off)
                elif bt[0] == "arr": nt = ("eff", "[%d]" % (off // 4))
                elif ctx == "proc" and bt[0] == "this" and off in (0x8c, 0x90): nt = ("eff", "+0x%x" % off)
                elif ctx == "proc" and bt[0] == "this" and off == 0x80: nt = ("arr",)
                elif ctx == "mgr" and bt[0] == "this" and off == 0x1c: nt = ("proc", "+0x1c")
            if nt: tags[rd] = nt
            else: kill(rd)
        if mm.group(4) == "!" or mm.group(5): tags.pop(rb, None)
        return
    if m == "ldr" and re.match(r"^\w+, \[\w+, \w+(, lsl #2)?\]$", op):
        rd = ops[0]; ra = rn(op.split("[")[1].split(",")[0])
        if tags.get(ra) == ("arr",): tags[rd] = ("eff", "array")
        else: kill(rd)
        return
    if m.startswith(("push", "stm", "vst", "vpush", "cmp", "cmn", "tst", "teq", "vcmp", "nop")) or m in ("b", "bx"):
        return
    if m.startswith("vmrs"):
        if "apsr" not in op and ops: kill(ops[0])
        return
    if m.startswith(("pop", "ldm")):
        for r in re.findall(r"\b(r\d+|sb|sl|fp|ip|lr)\b", op.split("{")[-1]): kill(rn(r))
        return
    if m.startswith("vmov"):
        for r in ops[:2]:
            if re.match(r"^r\d+$", r): kill(r)
        return
    if ops and re.match(r"^(r\d+|lr)$", ops[0]) and not m.startswith("v"):
        kill(ops[0])


def _succ(im, i, lo, hi):
    """Successors inside [lo, hi): fall-through, direct branch targets, jump-table entries (ldrls pc,[pc,rX,lsl #2])."""
    m, op = i.mnemonic, i.op_str
    base, cond = split_cond(m)
    nxt = i.address + i.size; out = []
    if base == "b":
        t = int(op.lstrip("#"), 0)
        if lo <= t < hi: out.append(t)
        if cond: out.append(nxt)
        return out
    if base == "bx" or (base == "pop" and "pc" in op) or (base == "ldm" and "pc" in op):
        return [nxt] if cond else []
    if base in ("ldr", "add") and op.startswith("pc,"):
        if base == "ldr" and re.match(r"^pc, \[pc, \w+, lsl #2\]$", op):
            a = i.address + 8
            while lo <= a < hi:
                w = im.u32(a)
                if not (lo <= w < hi): break
                out.append(w); a += 4
        elif base == "add" and re.match(r"^pc, pc, \w+, lsl #2$", op):
            a = i.address + 8
            while lo <= a < hi:
                x = list(im.md.disasm(im.data[im.off(a):im.off(a) + 4], a))
                if not x or x[0].mnemonic != "b": break
                out.append(a); a += 4
        if cond: out.append(nxt)
        return out
    return [nxt]


def scan_vcalls(im, lo, hi, ctx, entry_tag=("this",), entry=None):
    """Branch-aware register-tag dataflow over [lo, hi) from `entry` (default lo); merge = intersection of tags.
    ctx: 'eff' (r0 = effect), 'proc' (r0 = FX processor), 'mgr' (r0 = manager).
    Returns (vcalls, accesses): vcalls = [(site, object_tag, offset)], accesses = [(site, 'r'|'w', off, insn)] on this."""
    code = {i.address: i for i in dis(im, lo, hi)}
    entry = lo if entry is None else entry
    state = {entry: {"r0": entry_tag}}
    work = [entry]; vc = set(); acc = set(); visits = defaultdict(int)
    while work:
        a = work.pop()
        if a not in code: continue
        visits[a] += 1
        if visits[a] > 12: continue
        tags = dict(state[a]); i = code[a]
        _step(i, tags, ctx, vc, acc)
        for t in _succ(im, i, lo, hi):
            if t not in code: continue
            if t not in state:
                state[t] = dict(tags); work.append(t)
            else:
                old = state[t]; merged = {k: v for k, v in old.items() if tags.get(k) == v}
                if merged != old:
                    state[t] = merged; work.append(t)
    return sorted(vc, key=lambda x: x[0]), sorted(acc)


def tag_str(t):
    if t is None: return "?"
    if t[0] == "eff": return "effect(%s)" % t[1]
    if t[0] == "new": return "new@0x%x" % t[1]
    if t[0] == "proc": return "processor(%s)" % t[1]
    return t[0]


# ===================================================================================================================== emulation (C3, C6)
def f32(x): return struct.unpack("<f", struct.pack("<f", x))[0]


class Host:
    """One unicorn emulator (harness/lib/emu.py) hosting EffectBase objects: stub effects (real EffectBase ctor + own vtable copy whose
    slots 23..27 are own routines = Python hooks on `bx lr` slots of the sentinel page) and, optionally, real effects. Every call that
    enters an EffectBase base-slot body or a stub routine with r0 = a tracked object is logged with its return address."""
    STUB = None

    def __init__(self, heap_fill=0):
        import emu as EM
        self.EM = EM
        e = self.e = EM.Emu(heap_fill=heap_fill)
        e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))     # libm hwcap (as H031 new_emu)
        lm, b_, _ = e._libs["libm.so.6"]
        for r in lm.dynamic_relocations:
            if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(b_ + r.address, 0x3d000000)
        self.STUB = EM.SENTINEL + 0x400
        self.objs = {}; self.cfg = {}; self.log = []; self.s25 = []; self.events = []
        self.base = [e.u32(EB_VT + 4 * k) for k in range(32)]
        for k, t in enumerate(self.base):
            if t >= 0x10000 and t not in (0x11098,):
                e.add_watch(t, lambda em, k=k: self._rec(k))
        for k in (23, 24, 25, 26, 27):
            e.add_watch(self.STUB + 4 * k, lambda em, k=k: self._stub(k))

    def _rec(self, k, stub=False):
        e = self.e; o = e.r(0)
        if o in self.objs:
            self.log.append((k, (e.uc.reg_read(self.EM.LR) - 4) & 0xffffffff, self.objs[o], stub))

    def _stub(self, k):
        e = self.e; o = e.r(0); c = self.cfg[o]; self._rec(k, True)
        if k == 25:
            L, Rr, n = e.r(1), e.r(2), e.r(3)
            inL, inR = e.floats(L, n), e.floats(Rr, n)
            self.s25.append(dict(obj=o, L=L, R=Rr, n=n, inL=inL, inR=inR))
            g = c["gain"]
            e.set_floats(L, [f32(g * x) for x in inL]); e.set_floats(Rr, [f32(g * x) for x in inR])
            e.setr(0, c["ret"])
        elif k == 26:
            e.w32(o + 0x10, emu_f2u(1.0 - c["w"])); e.w32(o + 0x14, emu_f2u(c["w"])); e.setr(0, 0)
        else:
            self.events.append((k, self.objs[o], e.r(1), e.r(2))); e.setr(0, 0)

    def make_stub(self, label, mode=0, w=1.0, gain=0.5, ret=0):
        e = self.e
        o = e.malloc(0x1c0, "stub effect"); e.call(EB_CTOR, o, 44100, 64, mode)
        vt = e.malloc(4 * 34, "stub vtable copy")
        e.w32(vt, e.u32(EB_VT - 8)); e.w32(vt + 4, e.u32(EB_VT - 4))
        for k in range(32): e.w32(vt + 8 + 4 * k, self.base[k])
        for k in (23, 24, 25, 26, 27): e.w32(vt + 8 + 4 * k, self.STUB + 4 * k)
        e.w32(o, vt + 8)
        self.objs[o] = label; self.cfg[o] = dict(w=w, gain=gain, ret=ret)
        return o

    def insert_init(self, o, hpf=True):
        self.e.vcall(o, 22, 0)
        if hpf: self.e.call(0x106c7c, o, 1, emu_f2u(10.0))

    def vc(self, o, k, *a): return self.e.vcall(o, k, *a)[0]


def emu_f2u(x): return struct.unpack("<I", struct.pack("<f", x))[0]


def noise(nblk, seed=11, amp=0.5):
    import random
    g = random.Random(seed)
    L = [f32(g.uniform(-amp, amp)) for _ in range(64 * nblk)]; R = [f32(g.uniform(-amp, amp)) for _ in range(64 * nblk)]
    return L, R


def drive18(h, o, L, R, activate=True, pre=None, per_block=None):
    """Per block as InsertFxProcessor processBlock (F017/F022): slot 9; if 0 -> slot 5(e,0,1) + slot 7(e,0); slot 18(e, L, R, 64)."""
    e = h.e; bl = e.malloc(256); br = e.malloc(256); oL = []; oR = []; rets = []; s9s = []
    for b in range(len(L) // 64):
        if per_block: per_block(b)
        e.set_floats(bl, L[64 * b:64 * b + 64]); e.set_floats(br, R[64 * b:64 * b + 64])
        if activate:
            s9 = h.vc(o, 9); s9s.append(s9)
            if s9 == 0: h.vc(o, 5, 0, 1); h.vc(o, 7, 0)
        r = h.vc(o, 18, bl, br, 64); rets.append(r)
        oL += e.floats(bl, 64); oR += e.floats(br, 64)
    return oL, oR, rets, s9s, (bl, br)


def first_steady(out, ref):
    """index of the first sample from which out == ref (bit-exact) until the end, or None."""
    k = len(out)
    while k > 0 and out[k - 1] == ref[k - 1]: k -= 1
    return k if k < len(out) else None


def c3_c6(P, check, J, im, out):
    e_fail = []
    # ---------------------------------------------------------------------------------------------- C3 emulated ctor
    P("\n== C3 EffectBase layout — real ctor 0x1067d8 emulated on a 0xA5-filled 0x1c0 blob")
    lay = {}
    for mode in (0, 1, 2):
        h = Host(); e = h.e
        o = e.malloc(0x1c0); e.wr(o, b"\xa5" * 0x1c0)
        e.call(EB_CTOR, o, 44100, 64, mode)
        words = [e.u32(o + 4 * i) for i in range(0x1c0 // 4)]
        bts = e.rd(o, 0x1c0)
        lay[mode] = (words, bts, o, e)
    w0, b0, o0, e0 = lay[0]
    untouched = [4 * i for i, w in enumerate(w0) if w == 0xa5a5a5a5]
    P("  words never written by the ctor (still 0xA5A5A5A5), offsets: %s" % [hex(x) for x in untouched])
    beyond = [x for x in range(0x1b8, 0x1c0) if b0[x] != 0xa5]
    check(not beyond, "ctor writes nothing at or beyond +0x1b8 (sizeof(EffectBase) = 0x1b8 = 440)")
    diffm = [hex(4 * i) for i in range(0x1b8 // 4) if lay[0][0][i] != lay[1][0][i] and not (lay[0][0][i] >= 0x50000000 and lay[0][0][i] < 0x54000000)]
    P("  fields differing between mode 0 and mode 1 (excluding heap pointers): %s" % diffm)
    gate = w0[0xc8 // 4]
    gw = [e0.u32(gate + 4 * i) for i in range(0xd4 // 4)]
    P("  gate (EffectInOutGain) +0xd0 byte after ctor: %d; gate+0x10 fs %d, +0x14 %d" % (e0.rd(gate + 0xd0, 1)[0], gw[4], gw[5]))
    F = lambda i: struct.unpack("<f", struct.pack("<I", w0[i // 4]))[0]
    rows = [("+0x00", "vptr", hex(w0[0])), ("+0x04..+0x0f", "std::vector<Parameter*> begin/end/cap", "%s %s %s" % (hex(w0[1]), hex(w0[2]), hex(w0[3]))),
            ("+0x10", "dry gain (float)", F(0x10)), ("+0x14", "wet gain (float)", F(0x14)),
            ("+0x18..+0x8f", "5 gate target records × 0x18", " ".join("%x" % w for w in w0[6:0x90 // 4])),
            ("+0x90", "sample rate (int)", w0[0x90 // 4]), ("+0x94", "block size (int)", w0[0x94 // 4]), ("+0x98", "mode (ctor arg 4)", w0[0x98 // 4]),
            ("+0x9c", "copy-buffer length per channel", w0[0x9c // 4]), ("+0xa0", "copy-buffer channels", w0[0xa0 // 4]),
            ("+0xa4", "copy buffer (new[] 2·n floats)", hex(w0[0xa4 // 4])), ("+0xa8", "byte: fade skip/clamp enable (slot 22)", b0[0xa8]),
            ("+0xac/+0xb0", "byte skip armed / int skip count", "%d / %d" % (b0[0xac], w0[0xb0 // 4])),
            ("+0xb4/+0xb8", "byte clamp armed / int clamp count", "%d / %d" % (b0[0xb4], w0[0xb8 // 4])),
            ("+0xbc/+0xc0/+0xc4", "second buffer len / ch / ptr", "%d %d %s" % (w0[0xbc // 4], w0[0xc0 // 4], hex(w0[0xc4 // 4]))),
            ("+0xc8", "EffectInOutGain* (new 0xd4)", hex(gate)), ("+0xcc/+0xcd", "byte post-stage requested / current", "%d %d" % (b0[0xcc], b0[0xcd])),
            ("+0xd0", "post-stage HPF cutoff (float)", F(0xd0)), ("+0xd8..+0x127", "IirHpf1stOrder (vptr)", hex(w0[0xd8 // 4])),
            ("+0x128..+0x16f", "SignalGate A (vptr)", hex(w0[0x128 // 4])), ("+0x170..+0x1b7", "SignalGate B (vptr)", hex(w0[0x170 // 4]))]
    for r in rows: P("  %-18s %-42s %s" % r)
    J["c3_layout"] = [list(map(str, r)) for r in rows]
    check(w0[0] == EB_VT and w0[0x90 // 4] == 44100 and w0[0x94 // 4] == 64 and w0[0x98 // 4] == 0 and w0[0x9c // 4] == 64 and w0[0xa0 // 4] == 2
          and F(0x10) == 1.0 and F(0x14) == 0.0 and b0[0xa8] == 1 and F(0xd0) == 10.0 and w0[0xd8 // 4] == 0x840db8 and w0[0x128 // 4] == 0x840e40
          and w0[0x170 // 4] == 0x840e40 and lay[1][0][0x98 // 4] == 1 and w0[1] == w0[2],
          "emulated ctor(44100, 64, mode): vptr 0x841fb8, fs/block/mode at +0x90/+0x94/+0x98, copy buffer 64 × 2 ch, dry 1.0 / wet 0.0, +0xa8 = 1, "
          "HPF fc 10.0 (inactive, +0xcc = 0), member vptrs as static, empty parameter vector")
    # ---------------------------------------------------------------------------------------------- C6 stub effect, slot 18 direct
    P("\n== C6 stub effect through the real EffectBase slot 18 0x106de4 (own slots 23–27; out = gain·in in place)")
    NB = 12
    L, R = noise(NB)
    res = {}
    def run(name, w=1.0, gain=0.5, ret=0, hpf=True, inplace=False, skip=False, mode=0, sig=(L, R)):
        h = Host(); o = h.make_stub(name, mode=mode, w=w, gain=gain, ret=ret); h.insert_init(o, hpf=hpf)
        if inplace: h.vc(o, 21, 0)
        if skip: h.vc(o, 22, 1)
        oL, oR, rets, s9s, bufs = drive18(h, o, sig[0], sig[1])
        res[name] = dict(h=h, o=o, L=oL, R=oR, rets=rets, s9=s9s, bufs=bufs)
        return res[name]
    # contract of the slot-25 call
    r = run("copy_hpf_w1")
    h, o = r["h"], r["o"]; e = h.e
    cb = e.u32(o + 0xa4); nblk = e.u32(o + 0x9c)
    ptr_ok = all(c["L"] == cb and c["R"] == cb + 4 * nblk and c["n"] == 64 for c in h.s25)
    P("  copy path: slot 25 called %d× for %d blocks; L = [e+0xa4] = 0x%x, R = L + 4·[e+0x9c] (n_alloc %d), n = %s" %
      (len(h.s25), NB, cb, nblk, sorted({c["n"] for c in h.s25})))
    steady_in = [b for b, c in enumerate(h.s25) if c["inL"] == L[64 * b:64 * b + 64] and c["inR"] == R[64 * b:64 * b + 64]]
    P("  blocks whose slot-25 input equals the caller's input bit-exactly: %s (others = activation input fade 0x1074c4)" % steady_in)
    check(ptr_ok and len(h.s25) == NB and steady_in and steady_in == list(range(steady_in[0], NB)),
          "slot 25 contract (copy path): (this, float* L, float* R, int n) with L/R = the two planar halves of the EffectBase copy buffer "
          "(+0xa4, R at +4·[+0x9c]), n = 64; the input is the caller's block (bit-exact once the input fade is over); processed in place")
    # w=0: output must equal input
    r0 = run("copy_hpf_w0", w=0.0)
    st0 = first_steady(r0["L"] + r0["R"], L + R)
    P("  w = 0 (dry 1, wet 0): output == input bit-exactly from sample %s of %d" % (st0, 2 * len(L)))
    # post-stage off, w=1 -> 0.5 in
    rq = run("copy_nohpf_w1", hpf=False)
    ref = [f32(0.5 * x) for x in L]; refR = [f32(0.5 * x) for x in R]
    stq = first_steady(rq["L"], ref); stqR = first_steady(rq["R"], refR)
    P("  post-stage off, w = 1, gain 0.5: output == 0.5·input bit-exactly from sample L %s / R %s (activation ramp before)" % (stq, stqR))
    # linearity of the post-stage path: gain 0.5 vs gain 1.0, w=1, HPF on
    r1 = run("copy_hpf_w1_g1", gain=1.0)
    lin = all(f32(0.5 * a_) == b_ for a_, b_ in zip(r1["L"][147:] + r1["R"][147:], r["L"][147:] + r["R"][147:]))
    lin0 = sum(1 for a_, b_ in zip(r1["L"][:147], r["L"][:147]) if f32(0.5 * a_) != b_)
    hp_dev = max(abs(a_ - b_) for a_, b_ in zip(r1["L"][-640:], L[-640:]))
    P("  HPF on, w = 1: out(gain 0.5) == 0.5·out(gain 1) for every sample from 147 on: %s (in the first 147 samples %d differ: the dry "
      "share of the activation crossfade is not scaled); |out(gain 1) − in| max over the last 10 blocks %.3g (post-stage HPF)" % (lin, lin0, hp_dev))
    # DC test of the post-stage
    dc = ([0.5] * (64 * 40), [0.5] * (64 * 40))
    rdc = run("dc_hpf_g1", gain=1.0, sig=dc)
    tail = rdc["L"][-1]; tail_off = run("dc_nohpf_g1", gain=1.0, hpf=False, sig=dc)["L"][-1]
    pred_dc = 0.5 * math.exp(-2 * math.pi * 10.0 * (64 * 40 - 1) / 44100)
    P("  DC 0.5, w = 1, gain 1: last output (sample 2559) %.6g with post-stage, %.6g without; one-pole 10 Hz HPF prediction 0.5·exp(−2π·10·2559/44100) "
      "= %.6g (ratio %.4f)" % (tail, tail_off, pred_dc, tail / pred_dc))
    # w=0.25, HPF off: out = 0.75 in + 0.25 (0.5 in)
    rm = run("copy_nohpf_w025", w=0.25, hpf=False)
    cand = {"dry*in + wet*wet_sig": [f32(f32(0.75 * x) + f32(0.25 * f32(0.5 * x))) for x in L],
            "in*dry + (wet*wet_sig) fused-ish": [f32(0.75 * x + 0.25 * f32(0.5 * x)) for x in L]}
    for nm, cl in cand.items():
        P("  w = 0.25, post-stage off: steady samples (last 6 blocks) equal to %-34s %d/384; max |diff| %.3g" % (
            nm, sum(1 for a_, b_ in zip(rm["L"][-384:], cl[-384:]) if a_ == b_), max(abs(a_ - b_) for a_, b_ in zip(rm["L"][-384:], cl[-384:]))))
    near = max(abs(a_ - 0.875 * b_) for a_, b_ in zip(rm["L"][-384:], L[-384:]))
    # return value
    rr = run("ret1", ret=1)
    same = rr["L"] == L and rr["R"] == R
    P("  stub returns 1: slot 18 returns %s; caller buffers unchanged (= dry input) for all blocks: %s; stub still ran on the copies: %d calls"
      % (sorted(set(rr["rets"])), same, len(rr["h"].s25)))
    # in-place path
    ri = run("inplace", inplace=True)
    hi = ri["h"]; bl, br = ri["bufs"]
    ip_ptr = all(c["L"] == bl and c["R"] == br and c["n"] == 64 for c in hi.s25)
    ip_out = ri["L"] == ref and ri["R"] == refR
    P("  slot 21(e, 0) (gate +0xd0 = 0): slot 25 gets the caller's own buffers %s, n 64; output == 0.5·input bit-exactly from block 0: %s; "
      "slot 18 returns %s" % (ip_ptr, ip_out, sorted(set(ri["rets"]))))
    # skip/clamp
    rs = run("skip", skip=True)
    nseq = [c["n"] for c in rs["h"].s25]
    hs = rs["h"]; os_ = rs["o"]; bl, br = rs["bufs"]
    hs.vc(os_, 6, emu_f2u(1.0)); clampv = hs.e.u32(os_ + 0xb8); arm = hs.e.rd(os_ + 0xb4, 1)[0]
    before = len(hs.s25); ns2 = []
    for b in range(5):
        hs.e.set_floats(bl, L[:64]); hs.e.set_floats(br, R[:64]); hs.vc(os_, 18, bl, br, 64)
    ns2 = [c["n"] for c in hs.s25[before:]]
    P("  slot 22(e, 1) then activation: slot-25 n per block = %s (skip +0xb0 = 147 samples: 2 blocks skipped, then 64 − 19 = 45)" % nseq[:5])
    P("  then slot 6(e, 1.0f): clamp armed %d, +0xb8 = %d; next 5 slot-18 calls give n = %s" % (arm, clampv, ns2))
    P("  sub-checks: %s" % [st0 == 0, stq is not None, lin, abs(tail / pred_dc - 1) < 0.02 and tail_off == 0.5, same, set(rr["rets"]) == {1}, ip_ptr, ip_out,
                            nseq[:3] == [45, 64, 64], len(nseq) == NB - 2, ns2 == [64, 64, 19], clampv == 147])
    check(st0 == 0 and stq is not None and lin and abs(tail / pred_dc - 1) < 0.02 and tail_off == 0.5 and same and set(rr["rets"]) == {1} and ip_ptr and ip_out and
          nseq[:3] == [45, 64, 64] and len(nseq) == NB - 2 and ns2 == [64, 64, 19] and clampv == 147,
          "slot-18 contract: w = 0 -> exact dry; post-stage off & w = 1 -> exact gain·in after the activation ramp; post-stage is linear and "
          "removes DC; slot-25 return ≠ 0 -> slot 18 returns it and leaves the caller's buffers dry; in-place path (slot 21 = 0) bypasses gate, "
          "post-stage and mix; slot 22 = 1 -> 147-sample skip at start and, after slot 6, exactly 147 more samples processed, then none")
    J["c6_slot18"] = dict(copy_ptr_ok=ptr_ok, steady_from_block=steady_in[0] if steady_in else None, w0_exact_from=st0,
                          gain_exact_from=[stq, stqR], linear=lin, dc_tail=[tail, tail_off], ret1=[sorted(set(rr["rets"])), same],
                          inplace=[ip_ptr, ip_out], skip_n=nseq[:6], clamp_n=ns2, w025_maxdev_vs_0p875=near)
    # activation ramp shape (post-stage off, w=1)
    ratio = [(a_ / b_) if b_ else None for a_, b_ in zip(rq["L"][:256], L[:256])]
    pr = [f32(x * (1 - t / 147.0) + f32(0.5 * x) * (t / 147.0)) for t, x in enumerate(L[:147])]
    rdev = max(abs(a_ - b_) for a_, b_ in zip(rq["L"][:147], pr))
    P("  activation: first 147 output samples vs linear dry->wet crossfade in·(1 − t/147) + 0.5·in·t/147: max |diff| %.3g (|in| ≤ 0.5)" % rdev)
    J["c6_ramp_maxdev"] = rdev
    marks = [i for i in range(1, 256) if ratio[i] is not None and ratio[i - 1] is not None and abs(ratio[i] - 0.5) < 1e-6 <= abs(ratio[i - 1] - 0.5)]
    P("  activation ramp (post off, w 1): out/in at samples 0,16,32,64,96,128,146,147,148: %s; first exact-0.5 sample %s" %
      (["%.4f" % ratio[i] for i in (0, 16, 32, 64, 96, 128, 146, 147, 148)], stq))
    # gate mode 0/1/2 (ctor arg 4): activation and stop profile, post-stage off, w = 1, gain 0.5
    for md in (0, 1, 2):
        hm = Host(); om = hm.make_stub("M%d" % md, mode=md); hm.insert_init(om, hpf=False)
        LL = [0.5] * (64 * 8); RR = [0.5] * (64 * 8)
        def pb(b, hm=hm, om=om):
            if b == 4: hm.vc(om, 6, emu_f2u(1.0))
        mL, mR, mret, ms9, _ = drive18(hm, om, LL, RR, per_block=pb)
        prof = ["%.4f" % (x / 0.5) for x in (mL[0], mL[73], mL[146], mL[147], mL[200], mL[256], mL[256 + 73], mL[256 + 146], mL[256 + 147], mL[400])]
        P("  mode %d: out/in at samples 0, 73, 146, 147, 200 | stop at 256: 256, 329, 402, 403, 400… = %s; slot 9 per block %s" % (md, prof, ms9))
        J.setdefault("c6_modes", {})[md] = dict(profile=prof, s9=ms9)
    # stub slot calls log (dynamic callers) for the direct drive
    seq = [(k, hex(s)) for k, s, lab, st in res["copy_hpf_w1"]["h"].log[:16]]
    P("  first logged EffectBase-slot entries (slot, call site) in the direct drive: %s" % seq)
    # ---------------------------------------------------------------------------------------------- C6 through processBlock / setFxType
    P("\n== C6 stub effects inside a stand-in InsertFxProcessor: real setFxType 0x11735c + real processBlock 0x116860 (+ real 0xe8050/0xe8228)")
    def proc_rig(h, eff_by_idx, nine_d=1):
        e = h.e
        p = e.malloc(0x148); arr = e.malloc(40)
        for k in range(10): e.w32(arr + 4 * k, eff_by_idx.get(k, 0))
        e.w32(p, PROC_VT["InsertFxProcessor"]); e.w32(p + 0x80, arr); e.w32(p + 0x84, 10); e.w32(p + 0x88, 10)
        e.wr(p + 0x9c, bytes([0, nine_d, 0])); e.w32(p + 0xa4, 0xffffffff); e.w32(p + 0xa8, 0xffffffff)
        dd = e.malloc(8); e.w32(dd, e.malloc(256)); e.w32(dd + 4, e.malloc(256)); e.w32(p + 0xb8, dd)
        ms = e.malloc(0x20); e.call(0xe7fd8, ms, 128, 0); e.w32(p + 0x144, ms)
        buf = e.malloc(0x100); ch = e.malloc(8); Lb = e.malloc(256); Rb = e.malloc(256)
        e.w32(ch, Lb); e.w32(ch + 4, Rb); e.w32(buf + 0xc, ch)
        return p, buf, Lb, Rb
    hP = Host(); A = hP.make_stub("A", gain=0.5); B = hP.make_stub("B", gain=0.25)
    hP.insert_init(A); hP.insert_init(B)
    p, buf, Lb, Rb = proc_rig(hP, {5: A, 3: B})
    NBP = 40; LP, RP = noise(NBP, seed=5)
    e = hP.e
    nalloc0 = len(e.allocs); nctor = [0]
    e.add_watch(EB_CTOR, lambda em: nctor.__setitem__(0, nctor[0] + 1))
    e.call(0x11735c, p, 5)
    P("  setFxType(5) from Off: current %d, pending %d" % (e.u32(p + 0xa4), e.u32(p + 0xa8)))
    oL = []; oR = []; cur = []; swap_block = None; sel_block = 8
    for b in range(NBP):
        if b == sel_block:
            nlog = len(hP.log); e.call(0x11735c, p, 3)
            P("  block %d: setFxType(3): calls on the old effect: %s; current %d pending %d" % (
                b, [(k, hex(s), lab) for k, s, lab, st in hP.log[nlog:]], e.u32(p + 0xa4), e.u32(p + 0xa8)))
        e.set_floats(Lb, LP[64 * b:64 * b + 64]); e.set_floats(Rb, RP[64 * b:64 * b + 64])
        e.call(0x116860, p, buf)
        c_ = e.u32(p + 0xa4); cur.append(c_)
        if b > sel_block and swap_block is None and c_ == 3: swap_block = b
        oL += e.floats(Lb, 64); oR += e.floats(Rb, 64)
    P("  current index per block: %s" % cur)
    P("  heap allocations during setFxType ×2 + %d processBlock calls: %d; EffectBase ctor entries: %d" % (NBP, len(e.allocs) - nalloc0, nctor[0]))
    # reference: the same stubs driven directly through slot 18 (fresh host), segment 1 = A from block 0
    hR = Host(); A2 = hR.make_stub("A", gain=0.5); hR.insert_init(A2)
    rL, rR, _, _, _ = drive18(hR, A2, LP[:64 * sel_block], RP[:64 * sel_block])
    eqA = oL[:64 * sel_block] == rL and oR[:64 * sel_block] == rR
    P("  blocks 0..%d (effect A only): processor output == direct slot-18 drive of an identical stub, bit-exact: %s" % (sel_block - 1, eqA))
    tl = [(k, hex(s), lab) for k, s, lab, st in hP.log if k in (5, 6, 7, 8, 9) and lab == "B"][:6]
    P("  first slot 5–9 calls on B: %s; swap to index 3 at block %s (%d blocks after setFxType)" % (tl, swap_block, (swap_block or 0) - sel_block))
    stB = first_steady(oL, [f32(0.25 * x) if i >= 64 * (swap_block or NBP) else None for i, x in enumerate(LP)])
    # after swap: B is post-stage-on with w=1 -> compare with B driven directly from activation on the same input segment
    hR2 = Host(); B2 = hR2.make_stub("B", gain=0.25); hR2.insert_init(B2)
    sb = swap_block or NBP
    rL2, rR2, _, _, _ = drive18(hR2, B2, LP[64 * sb:], RP[64 * sb:])
    eqB = oL[64 * sb:] == rL2 and oR[64 * sb:] == rR2
    P("  blocks %d..%d (effect B after the swap): processor output == direct slot-18 drive of an identical fresh stub B: %s" % (sb, NBP - 1, eqB))
    fade = [max(abs(x) for x in oL[64 * b:64 * b + 64]) / max(1e-9, max(abs(x) for x in LP[64 * b:64 * b + 64])) for b in range(sel_block, sb + 1)]
    P("  output/input peak ratio per block during the A -> B change (blocks %d..%d): %s" % (sel_block, sb, ["%.3f" % x for x in fade]))
    dyn = defaultdict(set)
    for k, s, lab, st in hP.log: dyn[k].add(s)
    P("  dynamic EffectBase-slot callers (slot: call sites) seen in the processor run: %s" %
      {k: sorted(hex(x) for x in v) for k, v in sorted(dyn.items())})
    check(eqA and eqB and swap_block is not None and cur[:sel_block] == [5] * sel_block and len(e.allocs) == nalloc0 and nctor[0] == 0,
          "processor drive: setFxType + processBlock select the stub by index, activate it (slot 9 → 5 → 7), run it through slot 18, and its "
          "output equals the direct slot-18 drive bit-exactly; on setFxType(3) the old stub gets slot 6, keeps running until slot 9 returns 0, "
          "then B is activated and its output equals a fresh direct drive; no allocation and no constructor call happens on selection")
    J["c6_proc"] = dict(eqA=eqA, eqB=eqB, swap_block=swap_block, sel_block=sel_block, cur=cur,
                        dyn={k: sorted(hex(x) for x in v) for k, v in dyn.items()}, fade=[round(x, 4) for x in fade])
    # ---------------------------------------------------------------------------------------------- slots 3/4 contract on a stub
    P("\n== C6 slots 3/4 (sample rate / block size) on a running stub")
    h = Host(); o = h.make_stub("S"); h.insert_init(o)
    drive18(h, o, L[:128], R[:128])
    n0 = len(h.log); ev0 = len(h.events)
    r3 = h.vc(o, 3, 48000); seq3 = [(k, hex(s)) for k, s, lab, st in h.log[n0:]]
    ev = h.events[ev0:]
    r4 = h.vc(o, 4, 128); ev4 = h.events[ev0 + len(ev):]
    P("  slot 3(48000) -> %d; logged slot entries %s; stub hooks (slot, r1, r2) %s; +0x90 = %d" % (r3, seq3, ev, h.e.u32(o + 0x90)))
    P("  slot 4(128) -> %d; stub hooks %s; +0x94 %d, +0x9c %d; slot 3(22050) -> %d (unsupported); slot 4(0) -> %d" % (
        r4, ev4, h.e.u32(o + 0x94), h.e.u32(o + 0x9c), h.vc(o, 3, 22050), h.vc(o, 4, 0)))
    check(r3 == 0 and (23, "S", 48000, 44100) in ev and h.e.u32(o + 0x90) == 48000 and (24, "S", 128, 0) in [(a_, b_, c_, 0) for a_, b_, c_, d_ in ev4]
          and h.e.u32(o + 0x9c) == 128,
          "slot 3 calls slot 23(this, new, old) and stores +0x90; slot 4 calls slot 24(this, n) and re-sizes the copy buffer; unsupported "
          "rate / n <= 0 return 3")
    J["c6_slots34"] = dict(r3=r3, seq3=seq3, ev=ev, ev4=ev4)
    # ---------------------------------------------------------------------------------------------- parameter slots on a real LoFi
    P("\n== C2/C6 parameter slots 13/14/15/16/17/19/20 on a real LoFi (ctor 0xfd640) and on the stub")
    h = Host(); e = h.e
    e.call(0x137cc)
    lo = e.malloc(0x4b8); e.call(0xfd640, lo, 44100, 64); h.objs[lo] = "LoFi"
    n13 = h.vc(lo, 13)
    vals = []
    for i in range(n13):
        po = e.malloc(4); h.vc(lo, 15, i, po); vals.append(round(e.f32(po), 6))
    f17 = [h.vc(lo, 17, i) for i in range(n13)]
    pobj = [e.u32(e.u32(lo + 4) + 4 * i) for i in range(n13)]
    f14_ok = [e.u32(p_ + 0x14) for p_ in pobj] == f17
    sret = e.malloc(20); e.call(e.u32(e.u32(lo) + 4 * 16), sret, lo, 0); info0 = [hex(e.u32(sret + 4 * q)) for q in range(5)]
    e.call(e.u32(e.u32(lo) + 4 * 16), sret, lo, 99); info99 = [e.u32(sret + 4 * q) for q in range(5)]
    nm = e.u32(e.u32(lo) + 4 * 19)
    r19 = e.call(nm, lo)[0]; s19 = im.cstr(r19, 40)
    s20 = e.malloc(8); e.call(e.u32(e.u32(lo) + 4 * 20), s20, lo); mix = (e.f32(s20), e.f32(s20 + 4))
    bad14 = h.vc(lo, 14, 99, emu_f2u(0.5))
    st = Host(); so = st.make_stub("S"); n13s = st.vc(so, 13); b14 = st.vc(so, 14, 0, emu_f2u(0.5))
    P("  LoFi: slot 13 = %d parameters; slot 15 values %s; slot 17 = Parameter+0x14 for each: %s (%s); slot 16(0) %s; slot 16(99) %s" % (
        n13, vals, f14_ok, [hex(x) for x in f17[:3]], info0, info99))
    P("  LoFi: slot 19 -> \"%s\"; slot 20 -> (dry %.3f, wet %.3f); slot 14(99) -> %d; stub: slot 13 = %d, slot 14(0) -> %d" % (
        s19, mix[0], mix[1], bad14, n13s, b14))
    check(n13 == 8 and f14_ok and bad14 == 3 and n13s == 0 and b14 == 3 and s19 == "EFFECT BASE",
          "parameter interface: the Parameter* vector at +4 is the whole parameter model (slot 13 count, 14 set, 15 get, 16 info, 17 field +0x14); "
          "an effect without registered Parameters has 0 parameters and rejects every index with 3; slot 19 returns \"EFFECT BASE\" even for LoFi")
    J["c6_params"] = dict(n=n13, vals=vals, f17_is_p14=f14_ok, info0=info0, name=s19, mix=mix, stub_n=n13s)


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H011"))
    ap.add_argument("--static-only", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    P("H011 effect interface — target sha256 %s" % sp16img.SHA)
    starts = im.starts()
    def fn_of(va):
        i = bisect.bisect_right(starts, va) - 1
        return starts[i] if i >= 0 else None
    def fn_end(s):
        i = bisect.bisect_right(starts, s); return starts[i] if i < len(starts) else s + 4
    def ins(va):
        x = list(im.md.disasm(im.data[im.off(va):im.off(va) + 4], va)); return "%s %s" % (x[0].mnemonic, x[0].op_str) if x else "?"
    calls = im.direct_calls()
    callers_of = defaultdict(list)
    for s_, t_, k_ in calls:
        if k_ in ("bl", "b"): callers_of[t_].append((s_, k_))

    # ------------------------------------------------------------------------------------------------------------- C1
    P("\n== C1 slot matrix (own RTTI walk + F009 end rule)")
    R = Rtti(im)
    eb_ti = [t for t, v in R.ti.items() if v["name"] == "10EffectBase"]
    check(len(eb_ti) == 1 and im.u32(EB_VT - 4) == eb_ti[0], "EffectBase typeinfo unique (0x%x) and = word at vtable 0x841fb8 − 4" % eb_ti[0])
    clos = R.closure(eb_ti[0])
    P("  EffectBase RTTI closure: %d classes (incl. EffectBase): %s" % (len(clos), ", ".join(sorted(R.name(t) for t in clos))))
    check(len(clos) == 16, "closure = EffectBase + 15 descendants (F128)")
    h1 = os.path.join(HERE, "out", "H001", "fx_classes.json")
    cols = []          # (label, ti, ap, slots, eb_off)
    for (oa, ti, ott, apnt) in R.groups:
        if ti in clos:
            sl = R.slots(apnt)
            cols.append(("%s@%d" % (R.name(ti), ott) if ott else R.name(ti), ti, apnt, sl, clos[ti], ott))
    P("  vtable groups of closure classes: %d" % len(cols))
    for c in cols: P("    %-26s ap=0x%x slots=%d EffectBase-subobject offset=%d" % (c[0], c[2], len(c[3]), c[4]))
    if os.path.exists(h1):                       # optional cross-check against the cycle-001 implementation's output (H001_fx_rtti_vtables.py)
        old = {(c_["name"].lstrip("0123456789") if False else c_["name"], v_["offset_to_top"]): v_ for c_ in json.load(open(h1)) for v_ in c_["vtables"]}
        agree = 0; dis_ = []
        for c in cols:
            nm = R.name(c[1]); v_ = old.get((nm, c[5]))
            if v_ is None: dis_.append((c[0], "missing")); continue
            if int(v_["address_point"], 16) == c[2] and [int(x["target"], 16) for x in v_["slots"]] == c[3]: agree += 1
            else: dis_.append((c[0], v_["n_slots"], len(c[3])))
        P("  cross-check vs harness/out/H001/fx_classes.json: %d/%d vtable groups identical (address point + every slot target); differences %s" %
          (agree, len(cols), dis_))
    else:
        P("  (harness/out/H001/fx_classes.json not present: cross-check against the cycle-001 implementation skipped)")
    # independent sweep: every .rodata word == 0x106de4 -> candidate ap = word - 72
    rlo, rhi = im.sec[".rodata"]
    s18 = sorted(x for x, w in R.words.items() if w == EB_SLOT18 and rlo <= x < rhi)
    s18_ap = [x - 72 for x in s18]
    known_ap = {c[2] for c in cols}
    extra_ap = [x for x in s18_ap if x not in known_ap]
    P("  .rodata words == 0x106de4: %d; their ap (word − 72) not among closure groups: %s" % (len(s18), [hex(x) for x in extra_ap]))
    for x in extra_ap:
        ti = R.words.get(x - 4); P("    extra ap 0x%x: word[ap−4]=0x%x (%s), word[ap−8]=0x%x" % (x, ti, R.name(ti) if ti in R.ti else "not a typeinfo",
                                                                                    R.words.get(x - 8)))
    # EffectBase-subobject vtables: primary groups of classes whose EffectBase offset 0, secondary group with ott == -offset otherwise
    eb_cols = [c for c in cols if -c[5] == c[4]]
    base = R.slots(EB_VT)
    check(len(base) == 32 and base[18] == EB_SLOT18 and all(R.plt.get(base[k]) == "__cxa_pure_virtual" for k in (23, 24, 25, 26)),
          "EffectBase vtable 0x841fb8: 32 slots, slot 18 = 0x106de4, slots 23–26 = __cxa_pure_virtual")
    order = sorted(eb_cols, key=lambda c: (c[0] != "EffectBase", c[0]))
    mat = {}
    L = ["slot | " + " | ".join(c[0] for c in order)]
    for k in range(max(len(c[3]) for c in order)):
        row = []
        for c in order:
            sl = c[3]
            if k >= len(sl): row.append("-"); continue
            w = sl[k]
            if R.plt.get(w) == "__cxa_pure_virtual": cell = "P"
            elif k < 32 and w == base[k] and c[0] != "EffectBase": cell = "B"
            elif k >= 32: cell = "X:%x" % w
            else: cell = ("O:%x" % w) if c[0] != "EffectBase" else ("%x" % w)
            row.append(cell); mat[(c[0], k)] = cell
        L.append("%4d | " % k + " | ".join(row))
    open(os.path.join(a.out, "slot_matrix.txt"), "w").write("\n".join(L) + "\n")
    P("  slot matrix -> slot_matrix.txt (%d vtables × up to %d slots); legend B base, O override, P pure, X extra" %
      (len(order), max(len(c[3]) for c in order)))
    conc = [c for c in order if c[0] != "EffectBase"]
    ovr = {k: [c[0] for c in conc if k < len(c[3]) and c[3][k] != base[k]] for k in range(32)}
    P("  overridden-by counts per slot: " + ", ".join("%d:%d" % (k, len(v)) for k, v in ovr.items() if v))
    f009 = (all(len(ovr[k]) == len(conc) for k in (0, 1, 23, 24, 25, 26, 27)) and not ovr[18] and
            {k for k in list(range(2, 23)) + list(range(28, 32)) if ovr[k]} == {10, 11, 14, 15})
    check(f009, "F009 reproduced: slots 0,1,23–27 overridden by every concrete vtable; 18 never; among 2–22/28–31 only 10, 11, 14, 15")
    pure_left = [(c[0], k) for c in conc for k in (23, 24, 25, 26) if R.plt.get(c[3][k]) == "__cxa_pure_virtual"]
    P("  concrete vtables still pure in 23–26: %s" % (pure_left or "none"))
    extra = {c[0]: [(k, hex(c[3][k])) for k in range(32, len(c[3]))] for c in conc if len(c[3]) > 32}
    P("  slots beyond 31: %s" % extra)
    pf = [c for c in conc if c[0] == "PerformanceFxLoFi"][0]
    pl = {k: pf[3][k] for k in (0, 1, 23, 24, 25, 26, 27, 32)}
    check(pf[2] == 0x8419d8 and len(pf[3]) == 33 and pl == {0: 0xfdef8, 1: 0xfe0dc, 23: 0xfdbfc, 24: 0xfdc04, 25: 0xfc434, 26: 0xfac70,
                                                          27: 0xfb02c, 32: 0xfacec},
          "F128 reproduced: PerformanceFxLoFi vt 0x8419d8, 33 slots, own 0/1/23–27 and 32")
    J["c1"] = dict(classes=sorted(R.name(t) for t in clos), vtables=[dict(label=c[0], ap=hex(c[2]), n=len(c[3]),
                   eb_offset=c[4], slots=[hex(w) for w in c[3]]) for c in cols], extra_ap=[hex(x) for x in extra_ap],
                   overridden={k: v for k, v in ovr.items() if v})
    # other (non-EffectBase) vtables of closure classes
    sec = [c for c in cols if c not in eb_cols]
    P("  non-EffectBase groups of closure classes (second bases): %s" % [(c[0], hex(c[2]), len(c[3])) for c in sec])

    # ------------------------------------------------------------------------------------------------------------- C2 static
    P("\n== C2 slot roles — static vcall census")
    eff_methods = set()
    for c in cols:
        for w in c[3]:
            if R.is_code(w) and w not in R.plt: eff_methods.add(w)
    for k in range(32):
        if base[k] not in R.plt: eff_methods.add(base[k])
    eff_methods.update([0x106c88, 0x106c7c, EB_CTOR])
    vc_eff = []; acc_eff = {}
    for t in sorted(eff_methods):
        v, ac = scan_vcalls(im, fn_of(t), fn_end(fn_of(t)), "eff", entry=t)
        vc_eff += [(s_, t, tg, of) for s_, tg, of in v]; acc_eff[t] = ac
    # processors: every function from FxProcessorBase ctor to end of SendFxProcessor code (incl. slot targets of the 3 vtables)
    proc_entries = {s for s in starts if 0x1128cc <= s < 0x11c400}
    for v in PROC_VT.values():
        proc_entries |= {w for w in R.slots(v) if 0xf0000 <= w < 0x130000}      # incl. inherited FxProcessorBase slots below 0x1128cc
    proc_entries.add(0x1127a4)                                                    # FxProcessorBase dtor (called by the processor dtors)
    vc_proc = []
    for f in sorted(proc_entries):
        v, _ = scan_vcalls(im, fn_of(f), fn_end(fn_of(f)), "proc", entry=f)
        vc_proc += [(s_, f, tg, of) for s_, tg, of in v]
    mgr_fns = sorted(s for s in starts if 0x11f000 <= s < 0x12d000)
    vc_mgr = []
    for f in mgr_fns:
        v, _ = scan_vcalls(im, f, fn_end(fn_of(f)), "mgr")
        vc_mgr += [(s_, f, tg, of) for s_, tg, of in v]
    slot_callers = defaultdict(set)
    direct_eff = defaultdict(set)
    eb_methods = {w for c in eb_cols for w in c[3]}
    for s_, f, tg, of in vc_eff:
        if f not in eb_methods: continue           # methods only reachable through a second-base vtable: `this` is not an EffectBase
        if of >= 0 and tg and tg[0] == "this" and of % 4 == 0: slot_callers[of // 4].add(("self", s_, f))
    for s_, f, tg, of in vc_proc:
        if of < 0: direct_eff[-of].add((s_, f, tag_str(tg))); continue
        if tg and tg[0] in ("eff", "new") and of % 4 == 0: slot_callers[of // 4].add((tag_str(tg), s_, f))
    proc_self = defaultdict(set)
    for s_, f, tg, of in vc_mgr:
        if tg and tg[0] == "proc": proc_self[of // 4].add((s_, f))
    # whole-.text census of `ldr rX,[rV,#k]; ...; blx rX` offsets (untyped)
    lo, hi = im.sec[".text"]; cen = defaultdict(int)
    prev = []
    for i in dis(im, lo, hi):
        if i.mnemonic == "blx" and prev:
            for j in reversed(prev[-4:]):
                mm = re.match(r"^(\w+), \[(\w+)(?:, #(0x[0-9a-f]+|\d+))?\]$", j.op_str)
                if j.mnemonic == "ldr" and mm and mm.group(1) == i.op_str:
                    cen[int(mm.group(3) or "0", 0)] += 1; break
        prev.append(i); prev = prev[-6:]
    SLOTNAME = {}
    P("  typed vcall sites on effect objects (self = inside an EffectBase-family method on its own this; effect(+0x8c/+0x90/array) = "
      "FX processor code; new@ = object returned by operator new inside processor code):")
    mname = defaultdict(list)                 # method address -> ["Class.sK"]
    for c in order + [c for c in cols if c not in order]:
        for k, w in enumerate(c[3]): mname[w].append("%s.s%d" % (c[0], k))
    pslot0 = {}
    for pn, v in PROC_VT.items():
        for k, w in enumerate(R.slots(v)): pslot0.setdefault(w, []).append("%s.s%d" % (pn.replace("FxProcessor", "Proc"), k))
    for pn, f in PROC_CTOR.items(): pslot0.setdefault(f, []).append("%s.ctor" % pn.replace("FxProcessor", "Proc"))
    for nm in ("FxProcessorBase", "InsertFxParameterManager", "MasterFxParameterManager", "SendFxParameterManager", "FxParameterManagerBase"):
        tis = [t for t, v in R.ti.items() if R.name(t) == nm]
        for (oa, ti, ott, apnt) in R.groups:
            if ti in tis and ott == 0:
                for k, w in enumerate(R.slots(apnt)): pslot0.setdefault(w, []).append("%s.s%d" % (nm.replace("ParameterManager", "Mgr"), k))
    pslot0.setdefault(0x1127a4, []).append("FxProcessorBase_dtor")
    pslot0.setdefault(0x112a08, []).append("FxProcessorBase_setDisabled"); pslot0.setdefault(0x1129bc, []).append("FxProcessorBase_set9d")
    def fname(f):
        if f in pslot0: return "/".join(pslot0[f][:2])
        if f in mname: return "/".join(mname[f][:2]) + ("…" if len(mname[f]) > 2 else "")
        return "fn_0x%x" % f
    J["c2_caller_fns"] = {}
    for k in range(36):
        cs = sorted(slot_callers.get(k, []), key=lambda x: x[1])
        byfn = defaultdict(list)
        for who, s_, f in cs: byfn[(f, "self" if who == "self" else "proc")].append(s_)
        P("   slot %2d (+0x%02x): %3d typed sites in %d functions; untyped .text vcalls at this offset: %d" %
          (k, 4 * k, len(cs), len(byfn), cen.get(4 * k, 0)))
        items = sorted(byfn.items(), key=lambda x: (x[0][1] != "proc", x[0][0]))
        J["c2_caller_fns"][k] = [[fname(f), w, [hex(x) for x in v]] for (f, w), v in items]
        line = []
        for (f, w), v in items:
            line.append("%s%s(%s)" % ("" if w == "proc" else "self:", fname(f), ",".join("%x" % x for x in v[:3]) + ("…" if len(v) > 3 else "")))
        for j in range(0, len(line), 4): P("       " + "; ".join(line[j:j + 4]))
    J["c2_callers"] = {k: sorted([[w, hex(s_), hex(f)] for w, s_, f in v], key=lambda x: x[1]) for k, v in slot_callers.items()}
    P("  direct (non-virtual) calls with an effect object in r0, in FX processor code:")
    for t in sorted(direct_eff):
        P("   bl 0x%x: %s" % (t, ", ".join("0x%x(fn 0x%x %s)" % x for x in sorted(direct_eff[t])[:10])))
    J["c2_direct"] = {hex(t): [[hex(a_), hex(b_), c_] for a_, b_, c_ in sorted(v)] for t, v in direct_eff.items()}
    P("  manager -> processor vcalls (processor slot, site):")
    for k in sorted(proc_self):
        P("   processor slot %d: %s" % (k, ", ".join("0x%x(fn 0x%x)" % x for x in sorted(proc_self[k])[:8])))
    J["c2_mgr_to_proc"] = {k: [[hex(s), hex(f)] for s, f in sorted(v)] for k, v in proc_self.items()}
    # processor vtable slot names for the functions seen
    pslot = {}
    for pn, v in PROC_VT.items():
        for k, w in enumerate(R.slots(v)): pslot.setdefault(w, []).append("%s s%d" % (pn[:-11] if pn.endswith("FxProcessor") else pn, k))
    J["proc_slot_names"] = {hex(k): v for k, v in pslot.items()}
    open(os.path.join(a.out, "proc_fn_slots.txt"), "w").write(
        "\n".join("0x%x %s" % (f, pslot.get(f, "")) for f in sorted({x[1] for x in vc_proc})) + "\n")
    # ------------------------------------------------------------------------------------------------------------- C2 roles
    P("\n== C2 slot roles — instruction assertions on the EffectBase base bodies (vtable 0x841fb8)")
    ROLES = [  # slot, role, signature (soft-float AAPCS, F011/F021), base behaviour, {addr: expected instruction}
        (0, "~EffectBase (complete dtor)", "(this)", "vptr := 0x841fb8; gate +0xc8 deleted via its vt+4; 2 SignalGates +0x128/+0x170 and IirHpf1stOrder +0xd8 destroyed; buffers +0xa4/+0xc4 delete[]; parameter vector +4 freed",
         {0x106648: "ldr r0, [r0, #0xc8]", 0x106660: "ldr r3, [r3, #4]", 0x106668: "add r5, r8, #0x1b8", 0x10667c: "sub r4, r4, #0x48", 0x106724: "bl #0xf1c0c"}),
        (1, "deleting dtor", "(this)", "slot 0 then operator delete", {0x1067c4: "bl #0x106640", 0x1067cc: "bl #0x10bb8"}),
        (2, "isSampleRateSupported", "int (this, int fs)", "1 for 96000/48000/44100, else 0",
         {0x105910: "mov r3, #0x7700", 0x105914: "movt r3, #1", 0x105924: "movw r3, #0xbb80", 0x105930: "movw r0, #0xac44"}),
        (3, "setSampleRate", "int (this, int fs)", "0 if unchanged; 3 if slot 2 rejects; stores +0x90, updates gate fs, rescales +0xb0/+0xb8, calls slot 23(this,new,old); "
         "if that returns 0 and the gate is running: read every parameter (slot 15), slot 6(1.0f), re-set (slot 14), slot 5(1.0f,1) [and slot 7(0)]; re-inits HPF +0xd8 and SignalGates",
         {0x105f2c: "ldr r3, [r0, #0x90]", 0x105f54: "ldr r3, [r3, #8]", 0x105f60: "moveq r6, #3", 0x105f80: "str r5, [r4, #0x90]",
          0x105ffc: "ldr r3, [r3, #0x5c]", 0x106158: "ldr r3, [r3, #0x24]", 0x106188: "ldr r3, [r3, #0x3c]", 0x1061bc: "ldr r3, [r3, #0x18]",
          0x1061d4: "ldr r3, [r3, #0x38]", 0x106204: "ldr r3, [r3, #0x14]"}),
        (4, "setBlockSize", "int (this, int n)", "3 if n <= 0; 0 if unchanged; stores +0x94, re-allocates copy buffer +0xa4 (2·n floats, +0x9c = n) and +0xc4, the gate's buffer, calls gate vt+0xc, slot 24(this, n), SignalGate buffers",
         {0x1063d0: "movle r6, #3", 0x1063e0: "ldr r3, [r0, #0x94]", 0x1063fc: "str r5, [r4, #0x94]", 0x106450: "str r5, [r4, #0x9c]",
          0x10648c: "bl #0x109fc", 0x106514: "ldr r3, [r3, #0x60]"}),
        (5, "start / activate", "int (this, float fadeArg, int honourSkip)", "if honourSkip && +0xa8: arm skip +0xac=1, +0xb0 = (int)(fs·0.001·3.3333) (147 @44.1k); reset HPF +0xd8 and SignalGates; slot 27 (reset), slot 26 (mix), slot 31 (gate targets); +0x3c = fadeArg; gate reset 0x1072bc(gate, this+0x18); gate target state 2 from record this+0x30; returns 0",
         {0x10624c: "beq #0x10625c", 0x106250: "ldrb r3, [r0, #0xa8]", 0x10638c: "strb r2, [r0, #0xac]", 0x1063a0: "vstr s15, [r4, #0xb0]",
          0x106314: "ldr r3, [r3, #0x6c]", 0x106324: "ldr r3, [r3, #0x68]", 0x106334: "ldr r3, [r3, #0x7c]", 0x106340: "str r5, [r4, #0x3c]",
          0x106348: "bl #0x1072bc", 0x106350: "mov r1, #2", 0x106358: "bl #0x107310", 0x10635c: "mov r0, #0"}),
        (6, "stop / fade-out", "void (this, float fadeArg)", "if +0xa8: arm clamp +0xb4=1, +0xb8 = (int)(fs·0.001·3.3333); slot 31; +0x54 = fadeArg; gate target state 0 from record this+0x48; slot 28 (hook)",
         {0x105c9c: "ldrb r3, [r0, #0xa8]", 0x105ccc: "strb r2, [r0, #0xb4]", 0x105ce0: "vstr s15, [r4, #0xb8]", 0x105cf4: "str r5, [r4, #0x54]",
          0x105cfc: "mov r1, #0", 0x105d00: "add r2, r4, #0x48", 0x105d10: "ldr r3, [r3, #0x70]"}),
        (7, "fade-in variant 1", "int (this, int)", "slot 29 (hook), slot 31, gate target state 1 from record this+0x60; returns 0",
         {0x105c64: "ldr r3, [r3, #0x74]", 0x105c74: "ldr r3, [r3, #0x7c]", 0x105c80: "mov r1, #1", 0x105c84: "add r2, r4, #0x60", 0x105c8c: "mov r0, #0"}),
        (8, "fade-in variant 2", "void (this, ?)", "slot 31, gate target state 2 from record this+0x78, slot 30 (hook)",
         {0x105c2c: "ldr r3, [r3, #0x7c]", 0x105c38: "mov r1, #2", 0x105c3c: "add r2, r4, #0x78", 0x105c4c: "ldr r3, [r3, #0x78]"}),
        (9, "isRunning (gate active state)", "int (this)", "tail call EffectInOutGain 0x1079d0(gate); 0 = idle (processors swap pending in)",
         {0x1059bc: "ldr r0, [r0, #0xc8]", 0x1059c0: "b #0x1079d0"}),
        (10, "retrigger (modulation restart)", "int (this)", "returns 2 (not supported); overridden by Chorus/Flanger/Phaser/Distortion", {0x10594c: "mov r0, #2"}),
        (11, "optional hook 11", "int (this, ?)", "returns 2; overridden only in SendFxDelay's EffectBase vtable (0x104e64 -> DelayTime)", {0x105954: "mov r0, #2"}),
        (12, "optional hook 12", "int (this, ?)", "returns 2; never overridden", {0x10595c: "mov r0, #2"}),
        (13, "getNumParameters", "int (this)", "size of the Parameter* vector at +4 (0xf1c30: (end − begin)/4)", {0x1059fc: "add r0, r0, #4", 0x105a00: "b #0xf1c30"}),
        (14, "setParameter", "int (this, int index, float v)", "3 if index out of range, else Parameter(index) vt+0x10 (setValue)",
         {0x105d38: "bl #0xf1c30", 0x105d50: "mov r0, #3", 0x105d60: "bl #0xf1c44", 0x105d6c: "ldr r3, [r3, #0x10]"}),
        (15, "getParameter", "int (this, int index, float* out)", "Parameter(index) vt+0x20 (getValue into *out); no range check",
         {0x1059d0: "bl #0xf1c50", 0x1059dc: "ldr r3, [r3, #0x20]"}),
        (16, "getParameterInfo", "struct (sret, this, int index)", "5-word descriptor by Parameter kind (0xf17d8 = +0x10: 0/1/2), via Parameter vt+0x40 / +0x2c; zeros + flag 1 if out of range",
         {0x105a24: "bl #0xf1c30", 0x105a40: "bl #0xf17d8", 0x105a9c: "ldr r3, [r3, #0x40]", 0x105b10: "ldr r3, [r3, #0x2c]"}),
        (17, "getParameter field +0x14", "int (this, int index)", "Parameter(index)+0x14 (0xf17e8)", {0x1059f0: "bl #0xf1c50", 0x1059f8: "b #0xf17e8"}),
        (18, "processBlock dispatcher", "int (this, float* L, float* R, int n)", "see F010/F022/F023 and C6; calls slot 25 at 0x106ecc (copy path) / 0x106f14 (in place)",
         {0x106e00: "ldrb r3, [r0, #0xd0]", 0x106e2c: "blt #0x106f88", 0x106e8c: "bl #0x1078c", 0x106eb0: "bl #0x1074c4",
          0x106ec8: "ldr ip, [ip, #0x64]", 0x106ed4: "beq #0x106f40", 0x106f10: "ldr ip, [ip, #0x64]", 0x106f50: "bl #0x106c88", 0x106f80: "bl #0x10770c"}),
        (19, "getName", "const char* (this)", "returns 0x842060", {0x105964: "movw r0, #0x2060", 0x105968: "movt r0, #0x84"}),
        (20, "getMix", "struct{float dry, wet} (sret, this)", "slot 26 then returns {+0x10, +0x14}", {0x105988: "ldr r3, [r3, #0x68]", 0x105990: "ldm r5, {r0, r1}"}),
        (21, "setCopyMixPath", "int (this, bool)", "gate +0xd0 := arg (slot 18: copy + gate + post-stage + mix when set, in place otherwise)",
         {0x1059a0: "ldr r3, [r0, #0xc8]", 0x1059a8: "strb r1, [r3, #0xd0]"}),
        (22, "setFadeSkipEnable", "int (this, bool)", "+0xa8 := arg (enables the 147-sample skip/clamp of slots 5/6 and slot 18)", {0x1059b0: "strb r1, [r0, #0xa8]"}),
        (23, "onSampleRateChanged (pure)", "int (this, int newFs, int oldFs)", "__cxa_pure_virtual; called by slot 3", {}),
        (24, "onBlockSizeChanged (pure)", "int (this, int n)", "__cxa_pure_virtual; called by slot 4", {}),
        (25, "process (pure)", "int (this, float* L, float* R, int n)", "__cxa_pure_virtual; called only by slot 18", {}),
        (26, "updateMix (pure)", "void (this)", "__cxa_pure_virtual; writes dry +0x10 / wet +0x14; called by slot 5, slot 20 and every slot 25", {}),
        (27, "reset", "int (this)", "returns 0; called by slot 5", {0x1070e0: "mov r0, #0"}),
        (28, "onStop hook", "int (this)", "returns 0; called by slot 6", {0xf7120: "mov r0, #0"}),
        (29, "onStart hook (variant 1)", "int (this)", "returns 0; called by slot 7", {0xf7128: "mov r0, #0"}),
        (30, "onStart hook (variant 2)", "int (this)", "returns 0; called by slot 8", {0xf7130: "mov r0, #0"}),
        (31, "rebuildGateTargets", "void (this)", "fills the 4 gate target records +0x18/+0x30/+0x48/+0x60/+0x78 from mode +0x98 (0/1/2) and dry/wet +0x10/+0x14",
         {0x105d78: "ldr r3, [r0, #0x98]", 0x105d98: "ldr r5, [r0, #0x10]", 0x105da0: "ldr r4, [r0, #0x14]"}),
    ]
    badr = []
    for k, role, sig, beh, asrt in ROLES:
        for ad, exp in asrt.items():
            if ins(ad) != exp: badr.append((k, hex(ad), ins(ad), exp))
    check(not badr and [r[0] for r in ROLES] == list(range(32)) and all(base[k] == im.u32(EB_VT + 4 * k) for k in range(32)),
          "role table: %d instruction assertions on the 32 EffectBase base slots all hold %s" % (sum(len(r[4]) for r in ROLES), badr or ""))
    check(im.cstr(0x842060) == "EFFECT BASE", "slot 19 returns the C string \"%s\" (0x842060)" % im.cstr(0x842060))
    J["c2_roles"] = [dict(slot=k, role=r, sig=sg, base=beh, base_target=hex(base[k]), asserts=len(asrt)) for k, r, sg, beh, asrt in ROLES]
    # immediate r1 values at the processor ctors' slot-22 calls and 0x106c7c calls
    def imm_before(site, reg, n=12):
        for x in reversed(dis(im, site - 4 * n, site)):
            if x.op_str.startswith(reg + ", #") and x.mnemonic in ("mov", "movw", "movls", "movhi"):
                return int(x.op_str.split("#")[1], 0)
            if x.op_str.startswith(reg + ","): return None
        return None
    s22 = {}
    for who, s_, f in sorted(slot_callers.get(22, []), key=lambda x: x[1]): s22.setdefault(fname(f), []).append(imm_before(s_, "r1"))
    P("  slot 22 args (r1 immediates) by caller: %s" % {k: sorted(set(map(str, v))) for k, v in sorted(s22.items())})
    J["c2_slot22_r1"] = {k: sorted(set(x for x in v if x is not None)) for k, v in s22.items()}

    # ------------------------------------------------------------------------------------------------------------- C3 static
    P("\n== C3 EffectBase layout — static facts")
    m_ti = {}
    for off, vt in ((0xd8, 0x840db8), (0x128, 0x840e40), (0x170, 0x840e40)):
        m_ti[off] = R.name(im.u32(vt - 4))
    check(m_ti == {0xd8: "IirHpf1stOrder", 0x128: "SignalGate", 0x170: "SignalGate"} and ins(0x106870) == "str r3, [r4, #0xd8]"
          and ins(0x106864) == "ldr r3, [pc, #0x40c]" and im.u32(0x106864 + 8 + 0x40c) == 0x840db8,
          "members by RTTI of the vptrs stored in the ctor: +0xd8 IirHpf1stOrder (vt 0x840db8, ctor 0xe2120), +0x128 / +0x170 SignalGate (ctor 0xf4d74 stores vt 0x840e40)")
    gate_ti = R.name(im.u32(0x842078 - 4))
    check(gate_ti == "EffectInOutGain" and ins(0x106888) == "mov r0, #0xd4" and ins(0x1068a0) == "bl #0x10711c" and ins(0x1068cc) == "str r5, [r4, #0xc8]",
          "+0xc8 = new(0xd4) EffectInOutGain(fs, block) (ctor 0x10711c, vt 0x842078 = %s)" % gate_ti)
    # dtor member loop: +0x1b8 down to +0x128 in 0x48 steps -> last EffectBase member ends at +0x1b8
    check(ins(0x106668) == "add r5, r8, #0x1b8" and ins(0x10666c) == "add r7, r8, #0x128" and ins(0x10667c) == "sub r4, r4, #0x48",
          "dtor 0x106640 destroys a 2-element member array [+0x128, +0x1b8) of 0x48-byte SignalGates -> EffectBase members end at +0x1b8")
    vmi2 = {}
    for t, v in R.ti.items():
        if t in clos and v["kind"] == "vmi":
            vmi2[R.name(t)] = [(R.name(b) if b in R.ti else hex(b or 0), (of or 0) >> 8) for b, of in v["bases"]]
    P("  vmi classes in the closure and their bases (name, offset): %s" % vmi2)
    check(vmi2.get("InsertFxDelay") == [("EffectBase", 0), ("DelayEchoBaseSingleDelay", 440)] and
          vmi2.get("SendFxReverb") == [("EffectBase", 0), ("Reverb9NXSBase", 440)] and vmi2.get("SendFxDelay", [None, ("EffectBase", 568)])[1] == ("EffectBase", 568),
          "second bases placed right after the EffectBase sub-object at +440 = 0x1b8 (InsertFxDelay, SendFxReverb); SendFxDelay puts EffectBase at +568")
    # ctor argument census at every bl 0x1067d8
    ebc = sorted(s_ for s_, k_ in callers_of[EB_CTOR] if k_ == "bl")
    def regsrc(site, reg, n=16):
        for x in reversed(dis(im, site - 4 * n, site)):
            o = x.op_str
            if not o.startswith(reg + ","): continue
            if x.mnemonic in ("mov", "movw") and "#" in o: return "#%d" % int(o.split("#")[1], 0)
            return "%s %s" % (x.mnemonic, o)
        return "(arg)"
    cen_ctor = []
    for s_ in ebc:
        cen_ctor.append((s_, fn_of(s_), regsrc(s_, "r1"), regsrc(s_, "r2"), regsrc(s_, "r3")))
    P("  calls of EffectBase ctor 0x1067d8: %d (site, function, r1 fs, r2 block, r3 mode):" % len(cen_ctor))
    for c in cen_ctor: P("    0x%x in %s: r1=%s r2=%s r3=%s" % (c[0], fname(c[1]), c[2], c[3], c[4]))
    J["c3_ctor_calls"] = [[hex(c[0]), fname(c[1]), c[2], c[3], c[4]] for c in cen_ctor]

    # ------------------------------------------------------------------------------------------------------------- C4
    P("\n== C4 creation: construction sites of every EffectBase-family class")
    vts = {c[2]: c[0] for c in cols}
    cs = sp16img.const_sites(im, list(vts)); ls = sp16img.litadd_sites(im, list(vts))
    mat_sites = defaultdict(set)
    for v, L_ in cs.items():
        for kind, site in L_: mat_sites[v].add(fn_of(site))
    for v, L_ in ls.items():
        for a0, a1 in L_: mat_sites[v].add(fn_of(a1))
    rows4 = []
    for v in sorted(mat_sites):
        fns = sorted(mat_sites[v])
        P("  vptr 0x%x (%s) materialised in: %s" % (v, vts[v], ", ".join(fname(f) for f in fns)))
        rows4.append([hex(v), vts[v], [fname(f) for f in fns]])
    J["c4_vptr_sites"] = rows4
    # classify each materialising function: ctor if it calls 0x1067d8 / a parent ctor or is the inline block of a processor ctor
    allf = sorted({f for v in mat_sites.values() for f in v})
    proc_ctor_set = set(PROC_CTOR.values())
    eb_dtor_callers = {fn_of(s_) for s_, k_ in callers_of[EB_DTOR]}
    ctor_fns = {fn_of(s_) for s_ in ebc} - proc_ctor_set
    while True:                                   # ctor-type: calls 0x1067d8 or another ctor-type function (e.g. Insert/SendFxCompressor -> FxCompressor)
        more = {fn_of(s_) for f in ctor_fns for s_, k_ in callers_of[f] if k_ in ("bl", "b")} - ctor_fns - proc_ctor_set
        more = {f for f in more if f in allf}
        if not more: break
        ctor_fns |= more
    while True:
        more = {fn_of(s_) for f in eb_dtor_callers for s_, k_ in callers_of[f]} - eb_dtor_callers
        more = {f for f in more if f in allf}
        if not more: break
        eb_dtor_callers |= more
    roles4 = {}
    for f in allf:
        if f in proc_ctor_set: roles4[f] = "processor ctor (inline construction)"
        elif f in (EB_CTOR, EB_DTOR): roles4[f] = "EffectBase own ctor/dtor"
        elif f in ctor_fns: roles4[f] = "ctor (calls 0x1067d8 or a parent ctor)"
        elif f in eb_dtor_callers: roles4[f] = "dtor (calls 0x106640)"
        else: roles4[f] = "other"
    other = [f for f in allf if roles4[f] == "other"]
    P("  materialising functions: %d ctor-type, %d dtor-type, %d processor ctors, others: %s" % (
        sum(1 for v in roles4.values() if v.startswith("ctor")), sum(1 for v in roles4.values() if v.startswith("dtor")),
        sum(1 for v in roles4.values() if v.startswith("processor")), [fname(f) for f in other]))
    # callers of each ctor-type function
    ctor_callers = {}
    for f in sorted(ctor_fns | {f for f in allf if roles4[f].startswith("ctor")}):
        if f in proc_ctor_set: continue
        cl = sorted({fn_of(s_) for s_, k_ in callers_of[f] if k_ in ("bl", "b")})
        ctor_callers[f] = cl
        P("  ctor 0x%x: callers %s" % (f, [fname(x) for x in cl] or "none"))
    J["c4_ctor_callers"] = {hex(f): [fname(x) for x in v] for f, v in ctor_callers.items()}
    builders = set()
    for f, cl in ctor_callers.items(): builders.update(cl)
    builders |= {fn_of(s_) for s_ in ebc if fn_of(s_) in proc_ctor_set}
    leaf_builders = {b for b in builders if b not in ctor_callers}
    P("  functions that construct effects and are not themselves effect ctors: %s" % [fname(b) for b in sorted(leaf_builders)])
    check(leaf_builders <= proc_ctor_set and len(leaf_builders) == 3,
          "every effect construction is reached only from the three processor ctors (Insert 0x118b0c, Master 0x114bc0, Send 0x11bbe4)")
    # processor ctors: jump tables?
    for pn, f in PROC_CTOR.items():
        body = dis(im, f, fn_end(f))
        jt = [x for x in body if (split_cond(x.mnemonic)[0] in ("ldr", "add")) and x.op_str.startswith("pc,")]
        news = [x.address for x in body if x.mnemonic == "bl" and x.op_str == "#0x%x" % NEW]
        P("  %s ctor 0x%x..0x%x: %d instructions, pc-writing jump instructions %d, operator new calls %d" % (pn, f, fn_end(f), len(body), len(jt), len(news)))
        J.setdefault("c4_proc_ctor", {})[pn] = dict(n=len(body), jumptables=len(jt), news=len(news))
    check(all(v["jumptables"] == 0 for v in J["c4_proc_ctor"].values()),
          "no jump table / computed branch in any processor ctor: the 10 effects per processor are built by straight-line code (no type switch)")
    # dtor callers: direct calls of each concrete slot-0/1 target, and vcalls at offsets 0/4 in processor dtors
    dt = {}
    for c in conc:
        for k in (0, 1):
            cl = sorted({fn_of(s_) for s_, k_ in callers_of[c[3][k]]})
            dt["%s.s%d 0x%x" % (c[0], k, c[3][k])] = [fname(x) for x in cl]
    P("  direct callers of concrete dtors (slot 0/1 targets): %s" % {k: v for k, v in dt.items() if v})
    J["c4_dtor_direct"] = dt
    for pn, v in PROC_VT.items():
        for k in (0, 1):
            t = im.u32(v + 4 * k); body = dis(im, fn_of(t), fn_end(fn_of(t)))
            offs = []
            for j, x in enumerate(body):
                if x.mnemonic == "blx":
                    for y in reversed(body[max(0, j - 4):j]):
                        mm = re.match(r"^(\w+), \[(\w+)(?:, #(0x[0-9a-f]+|\d+))?\]$", y.op_str)
                        if y.mnemonic == "ldr" and mm and mm.group(1) == x.op_str: offs.append(int(mm.group(3) or "0", 0)); break
            P("  %s slot %d dtor 0x%x: vcall offsets %s; callers %s" % (pn, k, t, offs, sorted({fname(fn_of(s_)) for s_, _ in callers_of[t]})))
            J.setdefault("c4_proc_dtor", {})["%s.s%d" % (pn, k)] = dict(target=hex(t), vcall_offsets=offs,
                                                                         callers=sorted({fname(fn_of(s_)) for s_, _ in callers_of[t]}))

    # ------------------------------------------------------------------------------------------------------------- C5
    P("\n== C5 host-side registration points: jump tables and index tables in processor / manager code")
    mgr_vts = {}
    for nm in ("InsertFxParameterManager", "MasterFxParameterManager", "SendFxParameterManager"):
        tis = [t for t, v_ in R.ti.items() if R.name(t) == nm]
        for (oa, ti, ott, apnt) in R.groups:
            if ti in tis and ott == 0: mgr_vts[nm] = apnt
    P("  manager vtables: %s" % {k: hex(v) for k, v in mgr_vts.items()})
    fset = {}
    for pn, v in list(PROC_VT.items()) + list(mgr_vts.items()):
        for k, w in enumerate(R.slots(v)):
            if 0xf0000 <= w < 0x130000: fset.setdefault(w, "%s.s%d" % (pn, k))
    for pn, f in PROC_CTOR.items(): fset.setdefault(f, "%s.ctor" % pn)
    fset.setdefault(0x117434, "InsertFxProcessor.s52 body"); fset.setdefault(0x1133f4, "MasterFxProcessor.s52 body")
    fset.setdefault(0x11a364, "SendFxProcessor.s52 body")
    jts = []
    for f, nm in sorted(fset.items()):
        body = dis(im, fn_of(f), fn_end(fn_of(f))) if fn_of(f) is not None else []
        for j, x in enumerate(body):
            b_, c_ = split_cond(x.mnemonic)
            if b_ in ("ldr", "add") and x.op_str.startswith("pc, pc,") or (b_ == "ldr" and x.op_str.startswith("pc, [pc,")):
                n = None
                for y in reversed(body[max(0, j - 4):j]):
                    if y.mnemonic == "cmp" and "#" in y.op_str: n = int(y.op_str.split("#")[1], 0) + 1; break
                cases = []
                if b_ == "ldr" and n:
                    dflt = None
                    nx = list(im.md.disasm(im.data[im.off(x.address + 4):im.off(x.address + 8)], x.address + 4))
                    if nx and nx[0].mnemonic == "b": dflt = int(nx[0].op_str.lstrip("#"), 0)
                    tg = [im.u32(x.address + 8 + 4 * q) for q in range(n)]
                    cases = [q for q in range(n) if tg[q] != dflt]
                    groups = defaultdict(list)
                    for q in cases: groups[tg[q]].append(q)
                    cases = sorted(groups.values())
                jts.append((nm, f, x.address, n, cases))
    seen_j = set(); jts = [j for j in jts if not (j[2] in seen_j or seen_j.add(j[2]))]
    for nm, f, site, n, cases in jts:
        P("  jump table in %-36s (fn 0x%x) @0x%x: %s cases; non-default cases grouped by target: %s" % (nm, f, site, n, cases))
    J["c5_jumptables"] = [[nm, hex(f), hex(site), n, cases] for nm, f, site, n, cases in jts]
    # rodata tables loaded by literal and then indexed by a register (ldr/ldrsb rd, [rT, rI(, lsl #2)]) within 4 instructions
    tl = []; seen = set()
    for f, nm in sorted(fset.items()):
        body = dis(im, fn_of(f), fn_end(fn_of(f))) if fn_of(f) is not None else []
        for j, x in enumerate(body):
            mm = re.match(r"^(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", x.op_str)
            if not (split_cond(x.mnemonic)[0] == "ldr" and mm): continue
            v_ = im.u32(x.address + 8 + int(mm.group(2), 0))
            if not (v_ and rlo <= v_ < rhi): continue
            for y in body[j + 1:j + 5]:
                my = re.match(r"^(\w+), \[(\w+), (\w+)(, lsl #2)?\]$", y.op_str)
                if my and my.group(2) == mm.group(1) and split_cond(y.mnemonic)[0] in ("ldr", "ldrsb", "ldrb", "ldrsh") or \
                        (y.mnemonic.startswith("ldr") and y.op_str.endswith("[%s, %s]" % (mm.group(1), "r1"))):
                    if x.address in seen: break
                    seen.add(x.address); tl.append((nm, x.address, v_, y.mnemonic, bool(my and my.group(4)))); break
    for nm, site, v_, mn, w in tl:
        n = 20 if not w else 10
        vals = [struct.unpack_from("<i" if w else "<b", im.data, im.off(v_) + (4 if w else 1) * q)[0] for q in range(n)]
        P("  indexed table 0x%x (%s) in %s @0x%x: %s" % (v_, "int32" if w else "int8", nm, site, vals))
    J["c5_tables"] = [[nm, hex(site), hex(v_), mn] for nm, site, v_, mn, w in tl]
    if not a.static_only:
        c3_c6(P, check, J, im, a.out)
    with open(os.path.join(a.out, "h011.json"), "w") as fh: json.dump({k: v for k, v in J.items() if k != "_internal"}, fh, indent=1)
    txt = "\n".join(rep) + "\nRESULT: %d failed checks\n" % len(fails)
    open(os.path.join(a.out, "h011_report.txt"), "w").write(txt)
    print("RESULT: %d failed checks" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
