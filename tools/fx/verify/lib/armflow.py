"""Small path-insensitive forward value-tag analysis for ARM functions of target/EP085_Main_R_fw160 (own code, cycle 031 / H086).

Each register / stack slot holds a *set* of symbolic tags; states merge by union at CFG joins; conditional instructions keep the old
and the new value. Tags:
  'ARG:rN'      value of rN at function entry (N = 0..3), 'ARGS:n' incoming stack argument at [sp_entry + n]
  'C:n'         integer constant (mov/mvn/movw/movt), 'L:0x...' word loaded from a pc-relative literal
  'R'           the audio-system root interface (bl 0x32b664, or ldr [rB, rK] with rK = movw #0x4344)
  'O:path'      object returned by a virtual call: path = parent '.' vt-offset  (e.g. 'R.0x10.0x24')
  'V:x'         vtable pointer loaded from object x; 'F:x@off' virtual function pointer
  'M:x+off'     word loaded from [x + off] (x = ARG or member chain), 'P:x+off' address x + off
  'RET:0x...'   r0 after a direct bl
Recorded events: every `blx reg` whose register holds an 'F:' tag (object, offset, argument tag sets r0..r3 and outgoing stack
slots [sp+0], [sp+4]); every direct bl with its argument tag sets; stores of tracked objects to non-stack memory (escapes).
This is a heuristic reader (no alias analysis, stack modelled per frame offset); callers must check important sites by hand."""
import re

ROOT_GETTER = 0x32b664
REGS = ['r0', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9', 'r10', 'r11', 'r12', 'lr']
ALIAS = {'sb': 'r9', 'sl': 'r10', 'fp': 'r11', 'ip': 'r12'}
MAXTAGS = 12


def nreg(r):
    r = r.strip()
    return ALIAS.get(r, r)


def _imm(s):
    s = s.strip().lstrip('#')
    try:
        return int(s, 0)
    except ValueError:
        return None


def _cap(s):
    if len(s) > MAXTAGS:
        return frozenset(sorted(s)[:MAXTAGS])
    return frozenset(s)


class State:
    __slots__ = ('reg', 'stk', 'sp')

    def __init__(self, reg=None, stk=None, sp=0):
        self.reg = dict(reg or {}); self.stk = dict(stk or {}); self.sp = sp

    def copy(self):
        return State(self.reg, self.stk, self.sp)

    def merge(self, o):
        ch = False
        for k, v in o.reg.items():
            nv = _cap(self.reg.get(k, frozenset()) | v)
            if nv != self.reg.get(k, frozenset()):
                self.reg[k] = nv; ch = True
        for k, v in o.stk.items():
            nv = _cap(self.stk.get(k, frozenset()) | v)
            if nv != self.stk.get(k, frozenset()):
                self.stk[k] = nv; ch = True
        return ch

    def g(self, r):
        return self.reg.get(nreg(r), frozenset())

    def s(self, r, v):
        r = nreg(r)
        if v:
            self.reg[r] = _cap(v)
        else:
            self.reg.pop(r, None)


def _is_obj(t):
    return t == 'R' or t.startswith('O:') or t.startswith('ARG:') or t.startswith('M:') or t.startswith('RET:') or t.startswith('P:')


def _objname(t):
    return 'R' if t == 'R' else t.split(':', 1)[1] if ':' in t else t


class Flow:
    def __init__(self, im):
        self.im = im

    def analyse(self, start, end, max_iter=60):
        im = self.im
        ins = im.disasm(start, end)
        idx = {i.address: n for n, i in enumerate(ins)}
        init = State({'r%d' % k: frozenset(['ARG:r%d' % k]) for k in range(4)})
        states = {start: init}
        work = [start]
        events = {}
        it = 0
        while work and it < max_iter * len(ins):
            it += 1
            a = work.pop()
            if a not in idx:
                continue
            i = ins[idx[a]]
            st = states[a].copy()
            succ, out = self._step(i, st, start, end, events)
            for sa, ss in succ:
                if sa not in idx:
                    continue
                if sa not in states:
                    states[sa] = ss.copy(); work.append(sa)
                elif states[sa].merge(ss):
                    work.append(sa)
        return sorted(events.values(), key=lambda e: e['site'])

    # ------------------------------------------------------------------------------------------------------------------------
    def _step(self, i, st, fs, fe, events):
        m, op = i.mnemonic, i.op_str
        nxt = i.address + 4
        w = int.from_bytes(i.bytes, 'little')
        cc = w >> 28
        cond = cc not in (0xe, 0xf)
        base = m[:-2] if cond and len(m) > 2 else m
        if cc == 0xf and m == 'blx':
            base = 'blx'
        old = st.copy()
        ops = [x.strip() for x in re.split(r',(?![^\[]*\])(?![^{]*\})', op)] if op else []
        succ = []
        term = False
        if base == 'b':
            t = _imm(ops[0]) if ops and ops[0].startswith('#') else None
            if t is not None and fs <= t < fe:
                succ.append((t, st))
            elif t is not None:
                self._call(i, st, t, events, tail=True)
            if not cond:
                term = True
        elif base in ('bl', 'blx') and ops and ops[0].startswith('#'):
            t = _imm(ops[0])
            self._call(i, st, t, events)
        elif base in ('blx',):
            r = nreg(ops[0]); fts = [x for x in st.g(r) if x.startswith('F:')]
            if fts:
                for ft in fts:
                    obj, off = ft[2:].rsplit('@', 1)
                    key = (i.address, obj, off)
                    ev = events.setdefault(key, dict(site=i.address, kind='vcall', obj=obj, off=int(off, 0), args={}))
                    for a in ('r0', 'r1', 'r2', 'r3'):
                        ev['args'].setdefault(a, set()).update(st.g(a))
                    for so in (0, 4, 8):
                        ev['args'].setdefault('sp+%d' % so, set()).update(st.stk.get(st.sp + so, frozenset()))
            res = set()
            for ft in fts:
                obj, off = ft[2:].rsplit('@', 1)
                res.add('O:%s.%s' % (obj, off))
            for r_ in ('r0', 'r1', 'r2', 'r3', 'r12', 'lr'):
                st.s(r_, None)
            st.s('r0', res)
        elif base == 'bx':
            term = not cond
        elif base in ('pop', 'ldm', 'ldmia', 'ldmfd') and 'pc' in op:
            term = True
            if cond:
                term = False
            self._popregs(st, op)
        elif base == 'push' or base in ('stmdb', 'stmfd') and op.startswith('sp!'):
            regs = re.findall(r'\b(r\d+|sb|sl|fp|ip|lr)\b', op.split('{', 1)[1]) if '{' in op else []
            st.sp -= 4 * len(regs)
            for n, r in enumerate(regs):
                v = st.g(r)
                if v:
                    st.stk[st.sp + 4 * n] = v
        elif base in ('pop', 'ldm', 'ldmia', 'ldmfd'):
            self._popregs(st, op)
        elif base in ('ldr', 'ldrb', 'ldrh', 'ldrsb', 'ldrsh') and len(ops) >= 2:
            if nreg(ops[0]) == 'pc' and ops[1].startswith('[pc, '):
                # ARM jump table: ldr pc, [pc, rX, lsl #2] followed by the default branch and the table words
                a = i.address + 8
                while fs <= a < fe:
                    w_ = self.im.u32(a)
                    if not (fs <= w_ < fe):
                        break
                    succ.append((w_, st.copy())); a += 4
            else:
                self._ldr(i, st, base, ops)
            if nreg(ops[0]) == 'pc' and not cond:
                term = True
        elif base in ('str', 'strb', 'strh') and len(ops) >= 2:
            self._str(i, st, ops, events)
        elif base in ('mov', 'movs', 'mvn', 'mvns', 'movw', 'movt') and len(ops) == 2 and not (nreg(ops[0]) == 'pc'):
            d = nreg(ops[0])
            if ops[1].startswith('#'):
                v = _imm(ops[1])
                if base.startswith('mvn'):
                    v = (~v) & 0xffffffff
                if base == 'movt':
                    lo = [x for x in st.g(d) if x.startswith('C:')]
                    st.s(d, {'C:0x%x' % (((v & 0xffff) << 16) | (int(lo[0][2:], 0) & 0xffff))} if lo else set())
                else:
                    st.s(d, {'C:0x%x' % v} if base != 'movw' or v != 0x4344 else {'K4344'})
            elif nreg(ops[1]) in REGS:
                st.s(d, st.g(ops[1]))
            else:
                st.s(d, None)
        elif base in ('add', 'adds', 'sub', 'subs') and len(ops) == 3:
            d = nreg(ops[0]); src = nreg(ops[1])
            v = _imm(ops[2]) if ops[2].startswith('#') else None
            if src == 'sp' and v is not None:
                st.s(d, {'SP:%d' % (st.sp + (v if base.startswith('add') else -v))})
            elif d == 'sp' and src == 'sp' and v is not None:
                st.sp += v if base.startswith('add') else -v
            elif v is not None and st.g(src):
                vv = v if base.startswith('add') else -v
                nt = set()
                for t in st.g(src):
                    if t.startswith('C:'):
                        nt.add('C:0x%x' % ((int(t[2:], 0) + vv) & 0xffffffff))
                    elif vv == 0:
                        nt.add(t)
                    elif t.startswith('SP:'):
                        nt.add('SP:%d' % (int(t[3:]) + vv))
                    elif _is_obj(t):
                        nt.add('P:%s+0x%x' % (_objname(t), vv & 0xffffffff))
                st.s(d, nt)
            else:
                st.s(d, None)
        elif base in ('cmp', 'cmn', 'tst', 'teq', 'vcmp', 'vcmpe', 'vmrs', 'nop', 'vstr', 'vpush', 'vstmdb'):
            pass
        elif base == 'vpop' or base == 'vldmia':
            pass
        else:
            # any other instruction writing a core register clobbers it
            if ops and nreg(ops[0]) in REGS and not base.startswith('v'):
                st.s(ops[0], None)
            elif base == 'vmov' and ops and nreg(ops[0]) in REGS:
                st.s(ops[0], {'FLOAT'})
                if len(ops) >= 3 and nreg(ops[1]) in REGS:
                    st.s(ops[1], {'FLOAT'})
        if cond and base not in ('b',):
            st.merge(old)
        if not term:
            succ.append((nxt, st))
        return succ, None

    def _popregs(self, st, op):
        regs = re.findall(r'\b(r\d+|sb|sl|fp|ip|lr|pc)\b', op.split('{', 1)[1]) if '{' in op else []
        for n, r in enumerate(regs):
            if r == 'pc':
                continue
            st.s(r, st.stk.get(st.sp + 4 * n, frozenset()))
        st.sp += 4 * len(regs)

    def _ldr(self, i, st, base, ops):
        im = self.im
        d = nreg(ops[0])
        mem = ops[1]
        mm = re.match(r'\[(\w+)(?:,\s*([^\]]+))?\](!?)', mem)
        if not mm:
            st.s(d, None); return
        b = nreg(mm.group(1)); offs = mm.group(2)
        post = ops[2] if len(ops) > 2 else None
        if b == 'pc' and offs and offs.startswith('#'):
            lit = i.address + 8 + _imm(offs)
            v = im.u32(lit)
            st.s(d, {'L:0x%x' % v} if v is not None else None); return
        if offs and not offs.startswith('#'):
            rz = nreg(offs.split(',')[0])
            if 'K4344' in st.g(rz):
                st.s(d, {'R'}); return
            st.s(d, None); return
        off = _imm(offs) if offs else 0
        if b == 'sp':
            st.s(d, st.stk.get(st.sp + off, frozenset())); return
        nt = set()
        for t in st.g(b):
            if t.startswith('SP:'):
                nt |= st.stk.get(int(t[3:]) + off, frozenset())
            elif t.startswith('V:'):
                nt.add('F:%s@0x%x' % (t[2:], off))
            elif base == 'ldr' and off == 0 and (t == 'R' or t.startswith('O:')):
                nt.add('V:' + _objname(t))
            elif base == 'ldr' and off == 0 and (t.startswith('M:') or t.startswith('ARG:') or t.startswith('RET:') or t.startswith('P:')):
                nt.add('V:' + _objname(t)); nt.add('M:%s+0x0' % _objname(t))
            elif base == 'ldr' and (_is_obj(t)) and t.count('+') < 4:
                nt.add('M:%s+0x%x' % (_objname(t), off & 0xffffffff))
        st.s(d, nt)

    def _str(self, i, st, ops, events):
        src = nreg(ops[0]); mem = ops[1]
        mm = re.match(r'\[(\w+)(?:,\s*([^\]]+))?\](!?)', mem)
        if not mm:
            return
        b = nreg(mm.group(1)); offs = mm.group(2)
        off = _imm(offs) if offs and offs.startswith('#') else (0 if not offs else None)
        v = st.g(src)
        if b == 'sp' and off is not None:
            if v:
                st.stk[st.sp + off] = v
            else:
                st.stk.pop(st.sp + off, None)
            if mm.group(3) == '!':
                st.sp += off
            return
        for t in st.g(b):
            if t.startswith('SP:') and off is not None:
                if v:
                    st.stk[int(t[3:]) + off] = v
                return
        tracked = [x for x in v if x == 'R' or x.startswith('O:')]
        if tracked:
            key = (i.address, 'escape', ','.join(sorted(tracked)))
            events.setdefault(key, dict(site=i.address, kind='escape', obj=','.join(sorted(tracked)), off=off, args={'base': set(st.g(b))}))

    def _call(self, i, st, t, events, tail=False):
        key = (i.address, 'bl', t)
        ev = events.setdefault(key, dict(site=i.address, kind='tail' if tail else 'bl', obj=None, off=t, args={}))
        for a in ('r0', 'r1', 'r2', 'r3'):
            ev['args'].setdefault(a, set()).update(st.g(a))
        for so in (0, 4):
            ev['args'].setdefault('sp+%d' % so, set()).update(st.stk.get(st.sp + so, frozenset()))
        for r_ in ('r0', 'r1', 'r2', 'r3', 'r12', 'lr'):
            st.s(r_, None)
        st.s('r0', {'R'} if t == ROOT_GETTER else {'RET:0x%x' % t})


def refined_starts(im, lo=None, hi=None):
    """Function starts = .ARM.exidx starts ∪ direct bl/blx targets ∪ `push`/`stmdb sp!` instructions that follow an unconditional
    terminator (bx lr / pop {..pc} / b) — exidx alone merges some leaf/adjacent functions (e.g. 0x2ff434 inside 0x2ff350's extent)."""
    import bisect
    lo = lo or im.sec['.text'][0]; hi = hi or im.sec['.text'][1]
    s = set(x for x in im.starts() if lo <= x < hi)
    for site, t, k in im.direct_calls():
        if k in ('bl', 'blx') and lo <= t < hi:
            s.add(t)
    o = im.off(lo)
    prev_term = False
    for va in range(lo, hi, 4):
        w = int.from_bytes(im.data[o + va - lo:o + va - lo + 4], 'little')
        is_push = (w & 0xffff0000) == 0xe92d0000 or (w & 0xffff0fff) == 0xe52d0004   # stmdb sp!,{..} / str rX,[sp,#-4]!
        if (prev_term and is_push) or (w & 0xffff4000) == 0xe92d4000:   # any push {.., lr}: a non-leaf function prologue
            s.add(va)
        prev_term = (w == 0xe12fff1e) or ((w & 0xffff8000) == 0xe8bd8000) or ((w & 0x0f000000) == 0x0a000000 and (w >> 28) == 0xe) \
            or w == 0xe49df004
    return sorted(s)
