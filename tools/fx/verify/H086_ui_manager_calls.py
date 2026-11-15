#!/usr/bin/env python3
"""H086 — which FX parameter-manager setters the 1.60 UI can reach, and with which arguments.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and
never stored; outputs are our own derived tables (addresses, slot numbers, constants, name strings). Emulation is guest memory only.

Path found in cycle 031 (see kb/cycles/031.md, Worker):
  Fx*ViewController → ModelInterface static functions (ControllerDataReferrer&, …) → root = [[ref+4]+0x4344] (0x32b664 or inline
  movw #0x4344) → root vt+0x10 (track n) → vt+0x24 (FX slot) = Insert IEffector (TrackUnit 0x1c7890: +0xe8[i] + 0x14), or
  root vt+0x70 = Send IEffector (sys+0x604 SendFxUnit +0x88 SFPM + 0x14), vt+0x74 = Master IEffector (sys+0x608 MasterFxUnit +0x80
  MFPM + 0x14); root vt+0x90 = (CompositeFxUnit mode != 1) picks Send (true) or Master (false).
  IEffector = manager secondary vtable at +0x14 (Insert 0x844270, Master 0x8439e0, Send 0x8448c8, base 0x8432c0); its slot offsets map
  to manager primary slots (table IEFF below, derived by decoding the `sub r0,r0,#0x14; b` thunks).

Stages:
  A  inventory: forward tag analysis (harness/lib/armflow.py) over every function that obtains the root (bl 0x32b664 or movw #0x4344);
     lists every virtual call on an Insert/Master/Send IEffector object with its slot and argument tags.
  B  callers: every direct bl to the setter wrappers found in A, with argument tags (constants, literals, caller-side values).
  C  emulation of chosen controller / ModelInterface handlers with a recording stub IEffector (see stage C doc).
Run: .venv/bin/python -B harness/H086_ui_manager_calls.py --out DIR [--stage A|B|C|all]
"""
import argparse, collections, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE)
from sp16img import Image                      # noqa: E402
from armflow import Flow, refined_starts       # noqa: E402

ROOT_GETTER = 0x32b664
# IEffector byte offset -> (manager primary slot, role). Roles from cycles 029/030 and the base-slot code read in cycle 031.
IEFF = {0x00: (8, 'addListener'), 0x0c: (50, 'getParamRange(sret,k)'), 0x10: (27, 'SET param(v,k)'), 0x14: (28, 'nop'),
        0x18: (29, 'getParam(k)'), 0x1c: (30, 'ret0'), 0x20: (31, 'nop'), 0x24: (32, 'SET fxType(effectId)'),
        0x28: (33, 'getFxType'), 0x2c: (34, 'SET sync(bool)'), 0x30: (35, 'getSync byte+0x28'), 0x34: (42, 'SET bypass(byte+0x29)'),
        0x38: (43, 'getBypass'), 0x3c: (36, 'SET lookAhead(byte+0x28)'), 0x40: (37, 'getLookAhead byte+0x28'),
        0x44: (38, 'SET enum(Identifier,which)'), 0x48: (40, 'nop'), 0x4c: (39, 'getEnum(which)->Identifier'),
        0x50: (41, 'getMeter(i) 20log10'), 0x54: (49, 'ret1'), 0x58: (44, 'proc vt+0xc4'), 0x5c: (45, 'proc vt+0xc8'),
        0x60: (46, 'proc 0x1129bc'), 0x64: (47, 'proc byte+0x9d'), 0x68: (48, 'nop')}
SETTERS = {0x10, 0x24, 0x2c, 0x34, 0x3c, 0x44}


def ctx_of(obj):
    """Insert / Send / Master for an object path."""
    if obj.endswith('R.0x10.0x24') or obj == 'R.0x10.0x24':
        return 'Insert'
    if obj == 'R.0x70':
        return 'Send'
    if obj == 'R.0x74':
        return 'Master'
    return None


def root_functions(im, starts):
    import bisect, struct
    lo, hi = im.sec['.text']; o = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from('<%dI' % n, im.data, o)
    sites = [s for s, t, k in im.direct_calls() if t == ROOT_GETTER and k in ('bl', 'b')]
    sites += [lo + 4 * i for i, w in enumerate(W) if (w & 0xffff0fff) == 0xe3040344]
    fs = set()
    for s in sites:
        j = bisect.bisect_right(starts, s) - 1
        fs.add(starts[j])
    return sorted(fs), len(sites)


def fmt(ts):
    return '|'.join(sorted(ts)) if ts else '-'


def stage_a(im, out):
    starts = refined_starts(im)
    import bisect
    fl = Flow(im)
    funcs, nsites = root_functions(im, starts)
    rows = []; escapes = []; passes = []
    for f in funcs:
        e = starts[bisect.bisect_right(starts, f)]
        if f == ROOT_GETTER:
            continue
        for ev in fl.analyse(f, e):
            if ev['kind'] == 'vcall':
                c = ctx_of(ev['obj'])
                if c:
                    slot, role = IEFF.get(ev['off'], (None, '?'))
                    rows.append(dict(func=f, site=ev['site'], ctx=c, obj=ev['obj'], off=ev['off'], slot=slot, role=role,
                                     args={k: sorted(v) for k, v in ev['args'].items() if v}))
            elif ev['kind'] == 'escape':
                escapes.append(dict(func=f, site=ev['site'], obj=ev['obj'], base=sorted(ev['args']['base'])))
            elif ev['kind'] in ('bl', 'tail'):
                eff = [t for a in ('r0', 'r1', 'r2', 'r3') for t in ev['args'].get(a, ()) if t.startswith('O:') and ctx_of(t[2:])]
                if eff:
                    passes.append(dict(func=f, site=ev['site'], target=ev['off'], eff=sorted(set(eff))))
    # merge Send/Master pairs at one site
    merged = collections.OrderedDict()
    for r in rows:
        k = (r['site'], r['off'])
        if k in merged:
            merged[k]['ctx'] = '/'.join(sorted(set(merged[k]['ctx'].split('/') + [r['ctx']])))
        else:
            merged[k] = dict(r)
    rows = list(merged.values())
    with open(os.path.join(out, 'stageA_effector_calls.tsv'), 'w') as fh:
        fh.write('func\tsite\tctx\tieff_off\tmgr_slot\trole\tr1\tr2\tr3\tsp0\n')
        for r in rows:
            a = r['args']
            fh.write('0x%x\t0x%x\t%s\t0x%x\t%s\t%s\t%s\t%s\t%s\t%s\n' % (r['func'], r['site'], r['ctx'], r['off'], r['slot'], r['role'],
                     fmt(a.get('r1')), fmt(a.get('r2')), fmt(a.get('r3')), fmt(a.get('sp+0'))))
    summ = dict(root_sites=nsites, functions_scanned=len(funcs), effector_vcalls=len(rows),
                setter_calls=sum(1 for r in rows if r['off'] in SETTERS), escapes=escapes, passes=passes)
    print('Stage A: %d root-access sites in %d functions; %d IEffector vcalls (%d setter calls); %d escapes; %d effector-passing bl'
          % (nsites, len(funcs), len(rows), summ['setter_calls'], len(escapes), len(passes)))
    for r in rows:
        if r['off'] in SETTERS:
            a = r['args']
            print('  SET %-12s func 0x%x site 0x%x IE+0x%02x s%-2s %-28s r1=%s r2=%s' % (r['ctx'], r['func'], r['site'], r['off'], r['slot'],
                  r['role'], fmt(a.get('r1')), fmt(a.get('r2'))))
    return rows, summ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(HERE, 'out', 'H086'))
    ap.add_argument('--stage', default='all')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    im = Image()
    res = {}
    if a.stage in ('A', 'all'):
        rows, summ = stage_a(im, a.out)
        res['A'] = dict(summary={k: v for k, v in summ.items() if k not in ('escapes', 'passes')},
                        escapes=[{k: (hex(v) if isinstance(v, int) else v) for k, v in e.items()} for e in summ['escapes']],
                        passes=[{k: (hex(v) if isinstance(v, int) else v) for k, v in e.items()} for e in summ['passes']],
                        rows=[{k: (hex(v) if isinstance(v, int) and k in ('func', 'site', 'off') else v) for k, v in r.items()} for r in rows])
    if a.stage in ('B', 'all'):
        if 'A' not in res:
            rows, summ = stage_a(im, a.out)
        tb = stage_b(im, a.out, rows)
        res['B'] = [{k: (hex(v) if isinstance(v, int) else v) for k, v in t.items()} for t in tb]
    if a.stage in ('B', 'all'):
        res['D'] = [list(r) for r in stage_d(im, a.out, tb)]
    if a.stage in ('C', 'all'):
        print('Stage C (emulation):')
        rig, results, knob, box = stage_c(a.out)
        stage_c_knobs(rig, results, box)
        res['C'] = dict(results=results, failed=sum(1 for r in results if not r['ok']), n=len(results))
        print('Stage C: %d cases, %d failed' % (len(results), res['C']['failed']))
    with open(os.path.join(a.out, 'h086.json'), 'w') as fh:
        json.dump(res, fh, indent=1, sort_keys=True)



# ---------------------------------------------------------------------------------------------------------------------- stage B
class Owners:
    """Who owns a code address: data words that point at it (vtables / handler vtables, walked back to the typeinfo for the class
    name and slot index) and direct bl/b callers (recursively, bounded depth)."""

    def __init__(self, im, starts):
        import bisect, struct
        self.im = im; self.starts = starts; self.bisect = bisect
        self.calls_to = collections.defaultdict(list)
        for s, t, k in im.direct_calls():
            if k in ('bl', 'b', 'blx'):
                self.calls_to[t].append(s)
        self.data_to = collections.defaultdict(list)
        self.text_words_to = collections.defaultdict(list)     # words inside .text (jump tables, literal pools)
        lo, hi = im.sec['.text']
        for v, sz, o in im.segs:
            n = sz // 4
            ws = struct.unpack_from('<%dI' % n, im.data, o)
            for i, w in enumerate(ws):
                if lo <= w < hi:
                    a = v + 4 * i
                    if not (lo <= a < hi):
                        self.data_to[w].append(a)
                    else:
                        self.text_words_to[w].append(a)

    def func(self, a):
        """Containing function of a call site. The refined start list misses leaf functors without exidx/push (e.g. 0x2239fc
        `ldr r0,[r0,#8]; b ...`), so prefer the instruction after the last unconditional terminator before `a` when that address is
        referenced (data word or direct branch)."""
        j = self.bisect.bisect_right(self.starts, a) - 1
        st = self.starts[j]
        b = a - 4
        while b > st:
            w = self.im.u32(b)
            term = (w == 0xe12fff1e) or ((w & 0xffff8000) == 0xe8bd8000) or (w >> 28 == 0xe and (w & 0x0f000000) == 0x0a000000) \
                or w == 0xe49df004
            if term:
                c = b + 4
                internal = [x for x in self.calls_to.get(c, []) + self.text_words_to.get(c, []) if st <= x < a + 0x400]
                if self.data_to.get(c) or (self.calls_to.get(c) and len(internal) < len(self.calls_to.get(c))):
                    return c          # referenced from outside: a function entry
                if not internal:
                    return c          # unreferenced block after a terminator: a separate (dead) function, not st
            b -= 4
        return st

    def entry_aliases(self, f):
        """f and an immediately preceding `ldr rX,[r0,#..]` that some functions place before their push."""
        out = [f]
        w = self.im.u32(f - 4)
        if w is not None and (w & 0xfff00000) == 0xe5900000:
            out.append(f - 4)
        return out

    def vtable_of(self, ref):
        im = self.im
        for b in range(ref, ref - 0x400, -4):
            w = im.u32(b)
            if w is not None and 0x840000 < w < 0x980000:
                n = im.u32(w + 4)
                if n and 0x800000 < n < 0x980000:
                    s = im.cstr(n, 200)
                    if s and (s[0].isdigit() or s[:2] in ('N', '*N', '*Z', 'Z') or s[0] in 'NZ*'):
                        ott = im.u32(b - 4)
                        if ott is not None and (ott == 0 or ott >= 0xfffff000):
                            return s, b + 4, (ref - (b + 4)) // 4
        return None, None, None

    def owners(self, f, depth=3, seen=None):
        seen = seen or set()
        res = []
        for e in self.entry_aliases(f):
            if e in seen:
                continue
            seen.add(e)
            for d in self.data_to.get(e, []):
                cls, ap, slot = self.vtable_of(d)
                res.append(dict(kind='vtable', cls=cls, ap=ap, slot=slot, ref=d, chain=[e]))
            if depth > 0:
                for s in self.calls_to.get(e, []):
                    cf = self.func(s)
                    for o in self.owners(cf, depth - 1, seen):
                        o = dict(o); o['chain'] = o['chain'] + [s, e]; res.append(o)
                    if not self.data_to.get(cf) and not self.calls_to.get(cf) and not self.calls_to.get(cf - 4):
                        res.append(dict(kind='unreferenced', cls=None, ap=None, slot=None, ref=None, chain=[cf, s, e]))
        return res


def short_cls(s):
    """Sequential Itanium length-prefixed name parse; returns 'First' or 'First::Last' (enough for vtable owners)."""
    if not s:
        return '?'
    t = s.lstrip('*'); i = 0; names = []
    while i < len(t):
        if t[i].isdigit():
            j = i
            while j < len(t) and t[j].isdigit():
                j += 1
            n = int(t[i:j])
            if n == 0 or (i > 0 and t[i - 1] == '_'):
                if names:
                    names[-1] += t[i - 1:j]
                i = j; continue
            names.append(t[j:j + n]); i = j + n
        else:
            i += 1
    if not names:
        return s
    return names[0] if len(names) == 1 else names[0] + '::' + names[-1]


TYPE_GETTERS = [(0x300ecc, 0x301014, 'getInsertFxType'), (0x2fdfc4, 0x2fe09c, 'getSendMasterFxType')]
PARAM_WRAPPERS = {0x316a10: 'Insert setParam(ctx,k,FxParamIndex,delta)', 0x313ecc: 'SendMaster setParam(ctx,k,kind,delta)'}


def gates_in(im, f, e, site):
    """Constants compared with r0 right after a bl to an FX-type getter, in [f, site)."""
    out = []
    ins = im.disasm(f, min(e, site + 4))
    for n, i in enumerate(ins):
        if i.mnemonic == 'bl' and i.op_str.startswith('#'):
            t = int(i.op_str[1:], 16)
            for lo, hi, nm in TYPE_GETTERS:
                if lo <= t < hi:
                    for j in ins[n + 1:n + 4]:
                        if j.mnemonic.startswith('cmp') and j.op_str.startswith('r0, #'):
                            out.append((nm, int(j.op_str.split('#')[1], 0)))
                            break
                        if j.mnemonic == 'subs' and j.op_str.endswith(', r0, #0'):
                            out.append((nm, 0))
                            break
    return out


def const_of(ts):
    cs = [t for t in ts if t.startswith('C:')]
    return int(cs[0][2:], 0) if len(cs) == 1 and len(ts) == 1 else None


def stage_b(im, out, rows):
    import bisect
    starts = refined_starts(im)
    fl = Flow(im); ow = Owners(im, starts)
    wrappers = {}
    for r in rows:
        if r['off'] in SETTERS:
            f = r['func']
            wrappers.setdefault(f, set()).add((r['ctx'], r['off'], r['slot']))
    for w in PARAM_WRAPPERS:
        wrappers.setdefault(w, set())
    table = []
    cache = {}
    for w in sorted(wrappers):
        for e in ow.entry_aliases(w):
            for s in ow.calls_to.get(e, []):
                cf = ow.func(s)
                ce = starts[bisect.bisect_right(starts, cf)]
                if cf not in cache:
                    cache[cf] = {ev['site']: ev for ev in fl.analyse(cf, ce) if ev['kind'] in ('bl', 'tail')}
                ev = cache[cf].get(s, {'args': {}})
                a = {k: sorted(v) for k, v in ev['args'].items() if v}
                own = ow.owners(cf, depth=3)
                tag = ''
                if not own:
                    rs = starts[bisect.bisect_right(starts, s) - 1]
                    if rs != cf:
                        own = ow.owners(rs, depth=3); tag = '~enclosing 0x%x: ' % rs
                owners = sorted(set(tag + ('%s[s%s]' % (short_cls(o['cls']), o['slot']) if o['kind'] == 'vtable' else 'UNREFERENCED@0x%x' % o['chain'][0])
                                    for o in own)) or ['(no data ref / caller found)']
                table.append(dict(wrapper=w, site=s, caller=cf, args=a, gates=gates_in(im, cf, ce, s), owners=owners,
                                  sets=sorted('%s IE+0x%x s%s' % x for x in wrappers[w])))
    with open(os.path.join(out, 'stageB_callers.tsv'), 'w') as fh:
        fh.write('wrapper\tsets\tsite\tcaller\tr1\tr2\tr3\tgates\towners\n')
        for t in table:
            a = t['args']
            fh.write('0x%x\t%s\t0x%x\t0x%x\t%s\t%s\t%s\t%s\t%s\n' % (t['wrapper'], ';'.join(t['sets']) or PARAM_WRAPPERS.get(t['wrapper'], ''),
                     t['site'], t['caller'], fmt(a.get('r1')), fmt(a.get('r2')), fmt(a.get('r3')),
                     ';'.join('%s==%d' % g for g in t['gates']), ';'.join(t['owners'])))
    print('Stage B: %d call sites of %d setter wrappers' % (len(table), len(wrappers)))
    return table



# ---------------------------------------------------------------------------------------------------------------------- stage C
STUB_BASE = 0x3c000000          # our own executable page of `bx lr` words; each word is one stub vtable entry


class Rig:
    """Emulation rig for UI handlers. Everything below the IEffector is replaced by declared stand-ins:
      ref (ControllerDataReferrer, at ctrl+0x20): +4 -> DM;  DM +0x54 track index, +0x74 FX slot (0 = Send/Master, 1/2 = Insert FX1/FX2),
        +0x60/+0x64/+0x68 step-edit state (0 / -1 / 0 = not editing a step), +0x4344 -> ROOT, +0x434c -> CFG, +0x4348 -> MSG.
      ROOT (audio-system interface): vt+0x10 getTrack(i) -> TRACK, vt+0x70 -> SEND effector, vt+0x74 -> MASTER effector,
        vt+0x90 -> (CompositeFxUnit mode != 1) = rig.send_mode.  TRACK vt+0x24 getInsert(slot) -> INSERT effector.
      Effectors: 27-slot IEffector stub vtables; every call is recorded (ctx, IE offset, mgr slot, r1, r2, r3); getters return the
        rig state (fx type, param value, range, sync, enum Identifier).
      Any other virtual call on a stub object returns 0 and is recorded as 'other'.
    Real 1.60 code runs for the handler, the ModelInterface wrapper, juce::Identifier/String code and the __cxa_guard statics."""

    def __init__(self):
        import darwin_ctr_fix
        darwin_ctr_fix.install()
        import emu as E
        self.E = E
        E.STUBS.setdefault("__cxa_guard_acquire", (lambda e: e.setr(0, 0 if e.u32(e.r(0)) & 1 else 1), "H086: ARM EABI guard"))
        E.STUBS.setdefault("__cxa_guard_release", (lambda e: e.w32(e.r(0), 1), "H086: set guard bit 0"))
        E.STUBS.setdefault("__cxa_guard_abort", (lambda e: None, "H086: no-op"))
        for nm in ("pthread_mutex_lock", "pthread_mutex_unlock", "pthread_mutex_init", "pthread_mutex_destroy",
                   "pthread_mutexattr_init", "pthread_mutexattr_settype", "pthread_mutexattr_destroy",
                   "pthread_mutexattr_setprotocol"):
            E.STUBS.setdefault(nm, (lambda e: e.setr(0, 0), "H086: no-op"))
        E.STUBS.setdefault("pthread_self", (lambda e: e.setr(0, 1), "H086: returns 1"))

        def _vswprintf(em):
            em.w32(em.r(0), 0); em.setr(0, 0)
        E.STUBS.setdefault("vswprintf", (_vswprintf, "H086: writes an empty wide string, returns 0 (value text formatting only)"))
        self.e = e = E.Emu()
        from unicorn import UC_PROT_ALL
        e.uc.mem_map(STUB_BASE, 0x10000, UC_PROT_ALL)
        e.uc.mem_write(STUB_BASE, E.BX_LR * (0x10000 // 4))
        self.nstub = 0
        self.log = []
        self.state = dict(fxtype={'Insert': 16, 'Send': 15, 'Master': 15}, sync=0, lookahead=0, param=0.5, rng=(0, 100))
        self.send_mode = 1
        # objects
        self.eff = {c: self._obj('eff_' + c, self._eff_handler(c), 27) for c in ('Insert', 'Send', 'Master')}
        self.track = self._obj('track', self._track_handler, 16)
        self.root = self._obj('root', self._root_handler, 48)
        self.other = self._obj('other', lambda off: 0, 16)
        self.other2 = self._obj('other2', lambda off: 0, 16)
        self.yes = self._obj('yes', lambda off: 1, 16)
        # CFG (DM+0x434c): 0x5560bc(cfg, i) = (cfg+8)->array[i] (count at +0xc, array at +4); item 6's vt+0xc is asked a bool
        # before the knob value is applied (1 = skip 0x311aa0). Declared stand-in: every item answers 1.
        self.cfg = e.malloc(0x40); e.wr(self.cfg, bytes(0x40)); tbl = e.malloc(0x40); arr = e.malloc(0x80)
        for i in range(32):
            e.w32(arr + 4 * i, self.yes)
        e.w32(tbl + 4, arr); e.w32(tbl + 0xc, 32); e.w32(self.cfg + 8, tbl)
        self.dm = e.malloc(0x5000); e.wr(self.dm, bytes(0x5000))
        e.w32(self.dm + 0x54, 3); e.w32(self.dm + 0x74, 1); e.w32(self.dm + 0x60, 0); e.w32(self.dm + 0x64, 0xffffffff)
        e.w32(self.dm + 0x4344, self.root); e.w32(self.dm + 0x434c, self.cfg); e.w32(self.dm + 0x4348, self.other)
        self.ctrl = e.malloc(0x400); e.wr(self.ctrl, bytes(0x400))
        e.w32(self.ctrl + 0x24, self.dm)                     # ctrl+0x20 = ref: ref+4 -> DM
        for off in (0x13c, 0x140, 0x148):
            e.w32(self.ctrl + off, self.other)
        e.w32(self.ctrl + 0x144, self.other2)            # the selector widget the s19 handlers compare against
        self.handler = e.malloc(0x10); e.w32(self.handler + 8, self.ctrl)

    def _obj(self, name, fn, nslots):
        e = self.e
        vt = e.malloc(4 * nslots + 8)
        for i in range(nslots):
            a = STUB_BASE + 4 * self.nstub; self.nstub += 1
            e.w32(vt + 4 * i, a)
            e.add_watch(a, (lambda off, nm: (lambda em: self._dispatch(nm, off, fn)))(4 * i, name))
        o = e.malloc(0x40); e.wr(o, bytes(0x40)); e.w32(o, vt)
        return o

    def _dispatch(self, name, off, fn):
        e = self.e
        r = fn(off)
        if r is not None:
            e.setr(0, r)

    def _root_handler(self, off):
        self.log.append(('root', off, self.e.r(1)))
        if off == 0x10:
            return self.track
        if off == 0x70:
            return self.eff['Send'] + 0
        if off == 0x74:
            return self.eff['Master']
        if off == 0x90:
            return self.send_mode
        return 0

    def _track_handler(self, off):
        self.log.append(('track', off, self.e.r(1)))
        if off == 0x24:
            return self.eff['Insert']
        return 0

    def _eff_handler(self, ctx):
        def h(off):
            e = self.e
            r1, r2, r3 = e.r(1), e.r(2), e.r(3)
            slot, role = IEFF.get(off, (None, '?'))
            rec = dict(ctx=ctx, off=off, slot=slot, role=role, r1=r1, r2=r2, r3=r3)
            if off == 0x44:                                   # s38(Identifier*, which): read the pooled name text
                rec['name'] = self._cstr(e.u32(r1)); rec['which'] = r2
            if off == 0x10:
                rec['value'] = self.E.u2f(r1); rec['k'] = r2
            self.log.append(('eff', rec))
            st = self.state
            if off == 0x28:
                return st['fxtype'][ctx]
            if off in (0x30,):
                return st['sync']
            if off == 0x40:
                return st['lookahead']
            if off == 0x18:
                return self.E.f2u(st['param'])
            if off == 0x0c:                                   # getParamRange(sret=r0, this=r1, k=r2): two ints
                sret = e.r(0); e.w32(sret, st['rng'][0]); e.w32(sret + 4, st['rng'][1]); return sret
            if off == 0x4c:
                return 0
            return 0
        return h

    def _cstr(self, a):
        try:
            b = self.e.rd(a, 64)
            return b.split(b"\0")[0].decode('latin1')
        except Exception:
            return None

    def skip(self, addr, ret=0):
        e = self.e
        from unicorn import arm_const as A

        def cb(em):
            em.setr(0, ret); em.uc.reg_write(A.UC_ARM_REG_PC, em.uc.reg_read(A.UC_ARM_REG_LR))
        e.add_watch(addr, cb)

    def run(self, fn, *args):
        self.log = []
        self.e.call(fn, *args)
        return [x[1] for x in self.log if x[0] == 'eff']


def stage_c(out):
    rig = Rig()
    e = rig.e
    for a in (0x7c1644, 0x7ccc24, 0x2ee918, 0x2ee9a0, 0x1ea258, 0x392a84):   # UI redraw / widget feedback: skipped, declared
        rig.skip(a)
    results = []

    def case(name, fn, args, expect, setup=None):
        if setup:
            setup()
        try:
            got = rig.run(fn, *args)
            err = None
        except Exception as ex:          # noqa: BLE001
            got = [x[1] for x in rig.log if x[0] == 'eff']; err = str(ex)[:300]
        setters = [g for g in got if g['off'] in SETTERS]
        summ = [(g['ctx'], 's%s' % g['slot'], g.get('name', g.get('k', g['r1'])), g.get('which', round(g['value'], 6) if 'value' in g else None))
                for g in setters]
        ok = (err is None) and summ == expect
        results.append(dict(case=name, fn=hex(fn), setters=summ, expect=expect, ok=ok, err=err,
                            all_calls=[(g['ctx'], hex(g['off'])) for g in got]))
        print('  %s %-58s -> %s%s' % ('PASS' if ok else 'FAIL', name, summ, ('  ERR ' + err) if err else ''))

    def ctxset(slot, send_mode=1, ctrl_bytes=()):
        def f():
            e.w32(rig.dm + 0x74, slot); rig.send_mode = send_mode
            for off, v in ctrl_bytes:
                e.wr(rig.ctrl + off, bytes([v]))
        return f

    H = rig.handler
    # --- Insert compressor view controller handlers (FxInsertCompressorViewController ctor handler vtables 0x8781a8/c8/e8)
    case('InsComp Handler_0 (Peak)', 0x236970, (H,), [('Insert', 's38', 'LevelDetectPeak', 1)], ctxset(1))
    case('InsComp Handler_1 (RMS)', 0x236980, (H,), [('Insert', 's38', 'LevelDetectRMS', 1)], ctxset(1))
    case('InsComp Handler_2 (knee toggle, shown Hard)', 0x236a00, (H,), [('Insert', 's38', 'CompressorKneeSoft', 0)], ctxset(1, ctrl_bytes=[(0x188, 0)]))
    case('InsComp Handler_2 (knee toggle, shown Soft)', 0x236a00, (H,), [('Insert', 's38', 'CompressorKneeHard', 0)], ctxset(2, ctrl_bytes=[(0x188, 1)]))
    # --- Master compressor view controller handlers (Send/Master context: DM+0x74 = 0)
    case('MasComp Handler_0 (look-ahead toggle, Send mode)', 0x234790, (H,), [('Send', 's36', 1, None)], ctxset(0, 1, [(0x14c, 0)]))
    case('MasComp Handler_0 (look-ahead toggle, Master mode)', 0x234790, (H,), [('Master', 's36', 0, None)], ctxset(0, 0, [(0x14c, 1)]))
    case('MasComp Handler_2 (RMS, Master mode)', 0x234720, (H,), [('Master', 's38', 'LevelDetectRMS', 1)], ctxset(0, 0))
    case('MasComp Handler_3 (knee toggle, Master mode)', 0x2347a4, (H,), [('Master', 's38', 'CompressorKneeSoft', 0)], ctxset(0, 0, [(0x154, 0)]))
    # --- SYNC toggles (helpers shared by the Chorus/Delay/Flanger/Phaser(/Ducker) controllers' Handler_0)
    rig.state['sync'] = 0
    case('MasDelay Handler_0 (sync toggle, Send mode)', 0x24b0b4, (H,), [('Send', 's34', 1, None)], ctxset(0, 1))
    case('InsDelay sync helper 0x229180 (Insert)', 0x229180, (rig.ctrl,), [('Insert', 's34', 1, None)], ctxset(1))
    # --- FX type popup (FxSelectPopupWidgetController handlers): Compressor item in each context
    pop = e.malloc(0x100); e.wr(pop, bytes(0x100)); e.w32(pop + 0x24, rig.dm)
    ph = e.malloc(0x10); e.w32(ph + 8, pop)
    case('Popup Handler_13 (COMPRESSOR) Insert FX1', 0x1f2100, (ph,), [('Insert', 's32', 16, None)], ctxset(1))
    e.wr(pop + 0x4c, b'\0')
    case('Popup Handler_13 (COMPRESSOR) Master mode', 0x1f2100, (ph,), [('Master', 's32', 15, None)], ctxset(0, 0))
    e.wr(pop + 0x4c, b'\0')
    case('Popup Handler_9 (DELAY) Send mode', 0x1f1e80, (ph,), [('Send', 's32', 0, None)], ctxset(0, 1))
    e.wr(pop + 0x4c, b'\0')
    case('Popup Handler_14 (LIMITER item) Insert', 0x1f15b4, (ph, e.malloc(16)), [], ctxset(1))
    # --- selector change: Insert MMF view controller slot 19 (this, widget, index), widget = ctrl+0x144
    for idx, nm in ((0, 'FilterTypeHighPass'), (1, 'FilterTypeLowPass'), (2, 'FilterTypeBandPass'), (3, 'FilterTypeOff')):
        case('InsMMF VC s19 filter-type selector index %d' % idx, 0x23afdc, (rig.ctrl, rig.other2, idx), [('Insert', 's38', nm, 0)], ctxset(1))
    for idx, nm in ((0, 'FilterTypeHighPass'), (1, 'FilterTypeLowPass'), (2, 'FilterTypeBandPass'), (3, 'FilterTypeOff')):
        case('InsLoFi VC s19 filter-type selector index %d' % idx, 0x22d404, (rig.ctrl, rig.other2, idx), [('Insert', 's38', nm, 0)], ctxset(1))
    # --- the FILTERDB / position handlers
    case('InsMMF Handler_1 (FilterOrder2)', 0x23afb4, (H,), [('Insert', 's38', 'FilterOrder2', 1)], ctxset(1))
    case('InsMMF Handler_2 (FilterOrder4)', 0x23afc4, (H,), [('Insert', 's38', 'FilterOrder4', 1)], ctxset(1))
    # --- report-only maps (expected values derived from the static reading in kb/cycles/031.md; asserted)
    case('InsLoFi Handler_0 (position)', 0x22d3dc, (H,), [('Insert', 's38', 'FilterPositionPre', 1)], ctxset(1))
    case('InsLoFi Handler_1 (position)', 0x22d3ec, (H,), [('Insert', 's38', 'FilterPositionPost', 1)], ctxset(1))
    case('MasLoFi Handler_1 (position, Send)', 0x22ad14, (H,), [('Send', 's38', 'FilterPositionPost', 1)], ctxset(0, 1))
    case('MasMMF Handler_2 (FilterOrder4, Master)', 0x238b94, (H,), [('Master', 's38', 'FilterOrder4', 1)], ctxset(0, 0))
    w148 = rig._obj('mmfw', lambda off: 0, 16); e.w32(rig.ctrl + 0x148, w148)      # Master MMF: selector widget at +0x148
    for idx, nm in ((0, 'FilterTypeHighPass'), (1, 'FilterTypeLowPass'), (2, 'FilterTypeBandPass'), (3, 'FilterTypeOff')):
        case('MasMMF VC s19 filter-type selector index %d (Send)' % idx, 0x238bac, (rig.ctrl, w148, idx),
             [('Send', 's38', nm, 0)], ctxset(0, 1))
    e.w32(rig.ctrl + 0x148, rig.other)
    peq = {}
    for wid, band in ((0x144, 0), (0x148, 1)):
        wobj = rig._obj('peqw%d' % band, lambda off: 0, 16)
        e.w32(rig.ctrl + wid, wobj)
        for idx in range(6):
            rig.log = []
            ctxset(1)()
            try:
                got = rig.run(0x23ea48, rig.ctrl, wobj, idx)
            except Exception as ex:     # noqa: BLE001
                got = []; peq[(band, idx)] = 'ERR ' + str(ex)[:80]; continue
            st = [(g.get('name'), g.get('which')) for g in got if g['off'] == 0x44]
            peq[(band, idx)] = st
    e.w32(rig.ctrl + 0x144, rig.other2); e.w32(rig.ctrl + 0x148, rig.other)
    results.append(dict(case='InsPEQ VC s19 band-type selectors (report)', fn='0x23ea48', setters=[[list(k), v] for k, v in sorted(peq.items())],
                        expect=None, ok=all(isinstance(v, list) for v in peq.values()), err=None, all_calls=[]))
    print('  REPORT InsPEQ VC s19 (band, selector index) -> (name, which):')
    for k, v in sorted(peq.items()):
        print('      ', k, v)
    duck = {}
    w140 = rig._obj('duckw', lambda off: 0, 16); e.w32(rig.ctrl + 0x140, w140)
    for val in (0, 1, 15, 16, 17, -1):
        ctxset(1)()
        try:
            got = rig.run(0x21fec0, rig.ctrl, w140, val & 0xffffffff)
            duck[val] = [(g.get('name'), g.get('which')) for g in got if g['off'] == 0x44]
        except Exception as ex:         # noqa: BLE001
            duck[val] = 'ERR ' + str(ex)[:80]
    e.w32(rig.ctrl + 0x140, rig.other)
    results.append(dict(case='InsDucker VC s19 source selector (report)', fn='0x21fec0', setters=[[k, v] for k, v in sorted(duck.items())],
                        expect=None, ok=all(isinstance(v, list) for v in duck.values()), err=None, all_calls=[]))
    print('  REPORT InsDucker VC s19 value -> (name, which):', duck)
    # --- knob: ParameterBox encoder slots (this = box controller; box+0x20 = ref)
    box = e.malloc(0x100); e.wr(box, bytes(0x100)); e.w32(box + 0x24, rig.dm)
    def knob(name, fn, ctx_slot, send_mode, fxtype, k, kind_note, delta, start, rng):
        def f():
            ctxset(ctx_slot, send_mode)()
            rig.state['fxtype'] = {'Insert': fxtype, 'Send': fxtype, 'Master': fxtype}
            rig.state['param'] = start; rig.state['rng'] = rng
        lo, hi = rng
        iv = round(start * (hi - 1 - lo)) + lo
        exp_v = None
        case(name, fn, (box, delta), [((('Send' if send_mode else 'Master') if ctx_slot == 0 else 'Insert'), 's27', k, exp_v)], f)
    return rig, results, knob, box


def stage_c_knobs(rig, results, box):
    """Knob handlers: record the s27 call and compare k; the value is reported (not asserted) — the integer-step / range code
    of ModelInterface (0x313ecc / 0x316a10) is run for real on the stub ranges."""
    e = rig.e
    out = []
    for name, fn, slot, sm, ft, k in (('MasDelay box s21 (encoder 4) LowCut', 0x2cfb54, 0, 1, 0, 3),
                                      ('MasDelay box s22 (encoder 5) Spread', 0x2cfb20, 0, 0, 0, 4),
                                      ('MasReverb box s18 (encoder 1) PreDelay', 0x2be740, 0, 1, 2, 0),
                                      ('MasReverb box s21 (encoder 4) CombLPF', 0x2be6a4, 0, 1, 2, 3),
                                      ('MasReverb box s22 (encoder 5) Spread', 0x2be670, 0, 1, 2, 4),
                                      ('InsComp box s21 (encoder 4) Threshold', 0x2c7b48, 1, 1, 16, 0),
                                      ('MasDelay box s21 wrong type (Reverb)', 0x2cfb54, 0, 1, 2, None)):
        e.w32(rig.dm + 0x74, slot); rig.send_mode = sm
        rig.state['fxtype'] = {'Insert': ft, 'Send': ft, 'Master': ft}
        rig.state['param'] = 0.5; rig.state['rng'] = (0, 101)
        try:
            got = rig.run(fn, box, 1); err = None
        except Exception as ex:   # noqa: BLE001
            got = [x[1] for x in rig.log if x[0] == 'eff']; err = str(ex)[:300]
        s27 = [g for g in got if g['off'] == 0x10]
        summ = [(g['ctx'], 's27', g['k'], round(g['value'], 6)) for g in s27]
        ok = err is None and ((k is None and not s27) or (len(s27) == 1 and s27[0]['k'] == k))
        results.append(dict(case=name, fn=hex(fn), setters=summ, expect=k, ok=ok, err=err,
                            all_calls=[(g['ctx'], hex(g['off'])) for g in got]))
        print('  %s %-58s -> %s%s' % ('PASS' if ok else 'FAIL', name, summ, ('  ERR ' + err) if err else ''))
    return out



# ---------------------------------------------------------------------------------------------------------------------- stage D
# ParameterBox widget layouts (encoder n = widget position n-1 = box vtable slot 17+n, ParameterBox didChangeEncoderValue 0x2c004c,
# enabled only if widget[n-1] is non-null, visible (+0x68 bit 1) and enabled (+0xc8): 0x2bffb0). Box -> layout function pairing is
# by widget-class names (createBox<T> assert strings) and matching k semantics (`likely`); listed explicitly here.
BOX_LAYOUT = {'ParameterBoxInsertCompressorWidgetController': 0x4bd328, 'ParameterBoxMasterCompressorWidgetController': 0x4bdaac,
              'ParameterBoxInsertDelayWidgetController': 0x4c49f0, 'ParameterBoxMasterDelayWidgetController': 0x4c44b0,
              'ParameterBoxMasterReverbWidgetController': 0x4c3d2c, 'ParameterBoxInsertMultiModeFilterWidgetController': 0x4bf3b4,
              'ParameterBoxMasterMultiModeFilterWidgetController': 0x4bfb34, 'ParameterBoxInsertLofiWidgetController': 0x4c02b4,
              'ParameterBoxMasterLofiWidgetController': 0x4c0a3c, 'ParameterBoxInsertDistortionWidgetController': 0x4c164c,
              'ParameterBoxMasterDistortionWidgetController': 0x4c225c, 'ParameterBoxMaster2BandEqWidgetController': 0x4bec28,
              'ParameterBoxInsertDuckerWidgetController': 0x4c3368}


def _lit_strings(im, f, end):
    import re
    out = []
    for i in im.disasm(f, end):
        m = re.match(r'(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]', i.op_str)
        if i.mnemonic == 'ldr' and m:
            v = im.u32(i.address + 8 + int(m.group(2), 0))
            if v and im.off(v) is not None:
                sx = im.cstr(v, 240)
                if sx and len(sx) >= 3 and all(32 <= ord(c) < 127 for c in sx):
                    out.append((i.address, m.group(1), sx))
    return out


def widget_label(im, t, cache={}):
    import re
    if t in cache:
        return cache[t]
    lab = png = None
    for _, _, sx in _lit_strings(im, t, t + 0x400):
        m = re.search(r'with Box = (\w+)\]', sx)
        if m and not lab:
            lab = m.group(1).replace('Parameter', '').replace('Widget', '')
        m = re.match(r'(p\d+)_parametername\.png', sx)
        if m and not png:
            png = m.group(1)
    cache[t] = '%s[%s]' % (lab or 'generic', png or '?')
    return cache[t]


def box_layout(im, f):
    """Positions 0..5 of a box layout function (widget array built on the stack, then appended in order by 0x4b6124):
    (position, widget label, or None for a null placeholder). Inline-constructed widgets are labelled by their name String."""
    import re
    stores = []; last = None; zero = set(); lastlit = None; X = None
    for i in im.disasm(f, f + 0x400):
        m = re.match(r'(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]', i.op_str)
        if i.mnemonic == 'ldr' and m and m.group(1) == 'r1':
            v = im.u32(i.address + 8 + int(m.group(2), 0))
            sx = im.cstr(v, 120) if v and im.off(v) is not None else None
            if sx and len(sx) >= 3 and all(32 <= ord(c) < 127 for c in sx):
                lastlit = sx
        if i.mnemonic == 'bl' and i.op_str.startswith('#'):
            t = int(i.op_str[1:], 16)
            if t == 0x64a3fc:
                last = 'inline["%s"]' % lastlit
            elif t not in (0x4b6124, 0x627f38, 0x102e8, 0x4a822c, 0x103b4, 0x10774, 0x10d74):
                last = widget_label(im, t)
        if i.mnemonic == 'mov' and re.match(r'r\d+, #0$', i.op_str):
            zero.add(i.op_str.split(',')[0])
        m = re.match(r'r1, sp, #(0x[0-9a-f]+|\d+)$', i.op_str)
        if i.mnemonic == 'add' and m:
            X = int(m.group(1), 0)
        m = re.match(r'(r\d+), \[r1, #-(0x[0-9a-f]+|\d+)\]!$', i.op_str)
        if i.mnemonic == 'str' and m and X is not None:
            reg = m.group(1)
            stores.append((X - int(m.group(2), 0), None if reg in zero and reg != 'r0' else last))
            pass                                     # a zeroed register stays zero until rewritten (not tracked)
        if i.mnemonic == 'pop' and 'pc' in i.op_str:
            break
    if not stores:
        return []
    base = min(a for a, _ in stores)
    pos = {(a - base) // 4: w for a, w in stores}
    return [(p, pos.get(p)) for p in range(6)]


def stage_d(im, out, table):
    knob = collections.defaultdict(dict)
    for t in table:
        if t['wrapper'] in PARAM_WRAPPERS:
            for o in t['owners']:
                if '[s' in o and not o.startswith('~'):
                    cls, sl = o.rsplit('[s', 1)
                    sl = int(sl.rstrip(']'))
                    k = const_of(t['args'].get('r1', []))
                    kind = const_of(t['args'].get('r2', []))
                    g = t['gates'][0][1] if t['gates'] else None
                    if k is None and g is not None and t['args'].get('r1') and all(x.startswith('RET:') for x in t['args']['r1']):
                        k = g                       # compiler reused the compared type value (only path to the call)
                    if kind is None and g is not None and t['args'].get('r2') and all(x.startswith('RET:') for x in t['args']['r2']):
                        kind = g
                    knob[cls][sl] = (k, kind, g)
    rows = []
    with open(os.path.join(out, 'stageD_knob_tables.tsv'), 'w') as fh:
        fh.write('box\tencoder\twidget\tbox_slot\tk\tkind_or_FxParamIndex\ttype_gate\n')
        for cls, f in BOX_LAYOUT.items():
            lay = box_layout(im, f)
            for p, w in lay:
                k, kind, g = knob[cls].get(18 + p, (None, None, None))
                rows.append((cls, p + 1, w, 18 + p, k, kind, g))
                fh.write('%s\t%d\t%s\t%d\t%s\t%s\t%s\n' % (cls, p + 1, w, 18 + p, k, kind, g))
    print('Stage D: %d box layouts, %d encoder rows' % (len(BOX_LAYOUT), len(rows)))
    return rows


if __name__ == '__main__':
    main()
