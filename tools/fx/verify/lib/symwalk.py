"""Tiny linear symbolic walker over ARM code of target/EP085_Main_R_fw160 (1.60), for decoding argument values at call sites.

Our own code (no firmware bytes). It walks instructions in address order (the compiler's fall-through 'main path'), ignoring
conditional branches except that every `beq/bne` target can be *forked* (walked with a copy of the state until an unconditional
`b`), which is how one-time `__cxa_guard_acquire` initialisers of function-local statics are evaluated. Values are tuples:
  ('lit', v)            a known 32-bit constant           ('sp', off)        address sp+off
  ('base', name, off)   address of a named object + off   ('mem', A)         the 32-bit word at static address A (resolved later)
  ('id', node)          word +8 of a node handle          ('ret', target)    return value of an unmodelled call
  ('arg', i)            incoming argument i               ('?',)             unknown
Anything not understood becomes ('?',). A model is only as good as the assertions the caller makes on its results.
"""
import re

REG = {"sb": "r9", "sl": "r10", "fp": "r11", "ip": "r12"}
U = ("?",)


def rn(r):
    return REG.get(r, r)


def imm(s):
    s = s.strip().lstrip("#")
    return int(s, 0)


class State:
    def __init__(self):
        self.r = {}           # reg -> value
        self.d = {}           # d-reg -> (v0, v1)
        self.stack = {}       # sp offset -> value
        self.objs = {}        # (name, off) -> value  (stores into named objects)
        self.statics = {}     # static address -> value (constant stores done by initialisers)
        self.last_str = None

    def copy(self):
        s = State(); s.r = dict(self.r); s.d = dict(self.d); s.stack = dict(self.stack); s.objs = dict(self.objs)
        s.statics = self.statics; s.last_str = self.last_str
        return s


def addv(v, k):
    if v[0] == "sp": return ("sp", v[1] + k)
    if v[0] == "base": return ("base", v[1], v[2] + k)
    if v[0] == "lit": return ("lit", (v[1] + k) & 0xffffffff)
    return U


def load(st, base, off):
    a = addv(base, off)
    if a[0] == "sp": return st.stack.get(a[1], ("stack?", a[1]))
    if a[0] == "base": return st.objs.get((a[1], a[2]), ("field", a[1], a[2]))
    if a[0] == "lit": return ("mem", a[1])
    if base[0] in ("node", "field") and off == 8: return ("id", base[1] if base[0] == "node" else "%s+0x%x" % (base[1], base[2]))
    return U


def store(st, base, off, v):
    a = addv(base, off)
    if a[0] == "sp": st.stack[a[1]] = v
    elif a[0] == "base": st.objs[(a[1], a[2])] = v
    elif a[0] == "lit" and v[0] == "lit": st.statics[a[1]] = v[1]


MEMOP = re.compile(r"(\w+), \[(\w+)(?:, #(-?0x[0-9a-f]+|-?\d+))?\]$")


class Walker:
    """calls: {target: handler(state, site) -> return value or None}. Unknown bl clobbers r0-r3, ip, lr."""
    def __init__(self, im, calls, strings=True):
        self.im = im; self.calls = calls; self.strings = strings
        self.forked = set()

    def walk(self, lo, hi, st, fork=True, stop_at_b=False, max_ins=100000, fork_min=None):
        im = self.im
        ins = im.disasm(lo, hi)
        pool = set()                       # literal-pool words referenced pc-relatively from this range: data, not code
        for i in ins:
            mm = re.match(r"\w+, \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", i.op_str)
            if mm and (i.mnemonic.startswith("ldr") or i.mnemonic == "vldr"):
                a = i.address + 8 + int(mm.group(1), 0); pool.update((a, a + 4) if i.mnemonic == "vldr" else (a,))
        for n, i in enumerate(ins):
            if n > max_ins: break
            if i.address in pool: continue
            m, op = i.mnemonic, i.op_str
            base_m = m[:-2] if len(m) > 3 and m[-2:] in ("eq", "ne", "lt", "gt", "le", "ge", "hi", "ls", "cs", "cc", "mi", "pl") and m not in ("bne", "beq") else m
            if m in ("b",) and stop_at_b:
                return st
            if m in ("beq", "bne", "blt", "bgt", "ble", "bge") and fork:
                t = imm(op)
                if t > i.address and t not in self.forked and t >= (hi if fork_min is None else fork_min):      # out-of-line initialiser block after the main body
                    self.forked.add(t)
                    self.walk(t, t + 0x80, st.copy(), fork=False, stop_at_b=True, max_ins=40)
                continue
            if m == "bl":
                t = imm(op); h = self.calls.get(t)
                ret = h(st, i.address) if h else None
                for r in ("r0", "r1", "r2", "r3", "r12", "lr"): st.r[r] = U
                st.r["r0"] = ret if ret is not None else ("ret", t)
                continue
            if m == "blx":
                for r in ("r0", "r1", "r2", "r3", "r12", "lr"): st.r[r] = U
                continue
            if base_m == "ldr":
                mm = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", op)
                if mm:
                    v = im.u32(i.address + 8 + int(mm.group(2), 0)); st.r[rn(mm.group(1))] = ("lit", v)
                    if self.strings and rn(mm.group(1)) == "r1":
                        s = im.cstr(v, 60) if v and im.off(v) is not None else None
                        if s and len(s) >= 4 and all(32 <= ord(c) < 127 for c in s): st.last_str = s
                    continue
                mm = MEMOP.match(op)
                if mm:
                    b = st.r.get(rn(mm.group(2)), ("sp", 0) if mm.group(2) == "sp" else U)
                    if mm.group(2) == "sp": b = ("sp", 0)
                    st.r[rn(mm.group(1))] = load(st, b, int(mm.group(3) or "0", 0)); continue
                st.r[rn(op.split(",")[0])] = U; continue
            if base_m == "str":
                mm = MEMOP.match(op)
                if mm:
                    b = ("sp", 0) if mm.group(2) == "sp" else st.r.get(rn(mm.group(2)), U)
                    store(st, b, int(mm.group(3) or "0", 0), st.r.get(rn(mm.group(1)), U))
                continue
            if m in ("ldm", "stm"):
                mm = re.match(r"(\w+), \{([^}]*)\}$", op)
                if mm:
                    b = ("sp", 0) if mm.group(1) == "sp" else st.r.get(rn(mm.group(1)), U)
                    regs = [rn(x.strip()) for x in mm.group(2).split(",")]
                    for k, r in enumerate(regs):
                        if m == "ldm": st.r[r] = load(st, b, 4 * k)
                        else: store(st, b, 4 * k, st.r.get(r, U))
                continue
            if m == "vldr":
                mm = re.match(r"(d\d+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", op)
                if mm:
                    a = i.address + 8 + int(mm.group(2), 0)
                    st.d[mm.group(1)] = (("lit", im.u32(a)), ("lit", im.u32(a + 4)))
                continue
            if m in ("vstr", "vst1.32", "vst1.64"):
                mm = re.match(r"\{?(d\d+)\}?, \[(\w+)(?:, #(-?0x[0-9a-f]+|-?\d+))?\]$", op)
                if mm and mm.group(1) in st.d:
                    b = ("sp", 0) if mm.group(2) == "sp" else st.r.get(rn(mm.group(2)), U)
                    off = int(mm.group(3) or "0", 0)
                    store(st, b, off, st.d[mm.group(1)][0]); store(st, b, off + 4, st.d[mm.group(1)][1])
                continue
            if m in ("mov", "movne", "moveq", "mvn"):
                d, s = [x.strip() for x in op.split(",", 1)]
                if s.startswith("#"):
                    v = imm(s); st.r[rn(d)] = ("lit", (~v if m == "mvn" else v) & 0xffffffff)
                else:
                    st.r[rn(d)] = st.r.get(rn(s), ("sp", 0) if s == "sp" else U)
                continue
            if m == "movw":
                d, s = [x.strip() for x in op.split(",", 1)]; st.r[rn(d)] = ("lit", imm(s)); continue
            if m == "movt":
                d, s = [x.strip() for x in op.split(",", 1)]; v = st.r.get(rn(d), U)
                st.r[rn(d)] = ("lit", (imm(s) << 16) | (v[1] & 0xffff)) if v[0] == "lit" else U; continue
            if m in ("add", "addne", "addeq", "sub"):
                p = [x.strip() for x in op.split(",")]
                if len(p) == 3 and p[2].startswith("#"):
                    b = ("sp", 0) if p[1] == "sp" else st.r.get(rn(p[1]), U)
                    k = imm(p[2]) * (-1 if m == "sub" else 1)
                    st.r[rn(p[0])] = addv(b, k) if not (m == "addne" and b[0] == "lit" and b[1] == 0) else U
                    continue
            if m in ("push", "pop", "cmp", "tst", "cmn", "teq") or m.startswith("v") or m.startswith("b"):
                continue
            d = op.split(",")[0].strip()
            if re.match(r"^(r\d+|sb|sl|fp|ip|lr)$", d): st.r[rn(d)] = U
        return st
