#!/usr/bin/env python3
"""H079 — the FxProcessorBase +0x9d setter 0x1129bc (manager slot 46 thunk 0x11caf4 / IEffector +0x60 thunk 0x11caec) and its reader
0x11cae0 (slot 47 / IEffector +0x64 0x11cad8): static reading, +0x9d access sweep, callers, and bit-exact emulation on the real
Insert / Master / Send processors against harness/models/fx_processors.py (`set_start_mode`, cycle 034).

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and never
stored; outputs are our own derived tables and float outputs of the emulated routines. Emulation is guest-memory only.

Rig: harness/H077_master_send_proc.py (real processor ctors that build all effects + slot-52 defaults, real prepareToPlay, real
0x112a08 enable, real setFxType / processBlock), model side H077.ModelProc (fx_processors + effectbase + per-effect models).
New here: op ("9d", v, via) calls the REAL setter on the emulated processor through
   via = "s46"    stand-in manager object (+0 = the real primary manager vtable of that processor's manager class, +0x14 = the real
                  IEffector vtable, +0x1c = processor) -> real vt+0xb8 (slot 46 = 0x11caf4) -> 0x1129bc
         "ie60"   same object, r0 = mgr+0x14 -> real IEffector vt+0x60 (0x11caec: sub r0,#0x14) -> 0x11caf4 -> 0x1129bc
         "direct" 0x1129bc(p, v)
and FxProcessor.set_start_mode(v) on the model. Every block both readers (vt+0xbc slot 47 and IEffector +0x64) are called and must
equal the model's get_start_mode() and the emulated byte +0x9d.
Comparison every block: output float bits, processor state (cur/pend/+0x8c/+0x90/+0x9c/+0x9d/+0x9e, MuteSmoother), slot 5/6/7/8 + feed
call log, wrapper state of every effect (H044 emu_state/model_state).

Sections: c1 static (setter/thunk listing facts, vtable slots, +0x9d access sweep); c2 callers (direct branches, vtable/IEffector vcall
scan); c3 emulation matrix (schedules A-E x types x 3 processors + seeded fuzz + non-boolean edge values); c3m alternative setter
models (must FAIL); c4 audible meaning (emulated, toggled vs untouched reference).
Run: .venv/bin/python -B harness/H079_fx_onoff.py --out DIR [--jobs N] [--only c1,c2,c3,c3m,c4]
"""
import argparse, bisect, hashlib, json, math, os, random, re, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import H077_master_send_proc as H77                            # noqa: E402  (rig; installs the same stubs)
import H044_effectbase_wrapper as H44                          # noqa: E402
import fx_processors as FP                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from sp16img import Image                                      # noqa: E402

N = 64
SETTER, THUNK46, THUNK_IE60, READER, READER_IE64, DIS_THUNK = 0x1129bc, 0x11caf4, 0x11caec, 0x11cae0, 0x11cad8, 0x11cafc
MGR_VT = {"insert": (0x84407c, 0x844270), "master": (0x8437ec, 0x8439e0), "send": (0x8446d4, 0x8448c8)}   # primary, IEffector
TYPES = {"master": (0, 1, 7, 2, 6), "send": (0, 1, 7, 2, 6), "insert": (4, 7, 0, 5)}
PRE_INS = {"insert_delay": ((5, 0.5), (0, 0.05)), "insert_compressor": ((0, 0.2), (1, 0.8), (4, 0.7)), "chorus": ((5, 0.7),),
           "lofi": ((5, 0.8), (0, 0.3))}


def sha(b): return hashlib.sha256(b).hexdigest()
def pack(xs): return struct.pack("<%df" % len(xs), *xs)
def kinds(proc): return H77.KINDS_INS if proc == "insert" else H77.KINDS
def pre(proc, t):
    k = kinds(proc)[t]
    return PRE_INS.get(k, ()) if proc == "insert" else H77.PRE.get(k, ())


# ===================================================================================================================== emulated side
class Rig:
    def __init__(self, proc, mutant=None, raw_mute=False):
        self.x = x = H77.EmuProc(proc); self.m = H77.ModelProc(proc, x)
        if mutant: self.m.P.__class__ = MUTANTS[mutant](self.m.P.__class__)
        if raw_mute and hasattr(self.m.P, "ms"):
            ms = self.m.P.ms
            def set_muted_raw(m_, ms=ms):                   # 0xe8050 verbatim: compare the stored BYTE with the full argument, store
                if ms.muted == m_: return                    # the low byte, step sign from (arg != 0) - no 0/1 normalisation
                ms.step = F32(-ms.inv) if m_ else ms.inv; ms.muted = m_ & 0xff; ms.rem = ms.N - ms.rem; ms.state = 1
            ms.set_muted = set_muted_raw
        e = x.e; pv, iv = MGR_VT[proc]
        self.mgr = mgr = e.malloc(0x40, "harness: stand-in manager (vt, IEffector vt @+0x14, processor @+0x1c)")
        e.w32(mgr, pv); e.w32(mgr + 0x14, iv); e.w32(mgr + 0x1c, x.p)
        assert e.u32(pv + 0xb8) == THUNK46 and e.u32(pv + 0xbc) == READER
        assert e.u32(iv + 0x60) == THUNK_IE60 and e.u32(iv + 0x64) == READER_IE64

    def set9d(self, v, via):
        e = self.x.e
        if via == "s46": e.call(e.u32(e.u32(self.mgr) + 0xb8), self.mgr, v & 0xffffffff)
        elif via == "ie60": e.call(e.u32(e.u32(self.mgr + 0x14) + 0x60), self.mgr + 0x14, v & 0xffffffff)
        elif via == "direct": e.call(SETTER, self.x.p, v & 0xffffffff)
        else: raise ValueError(via)
        self.m.P.set_start_mode(v)

    def readers(self):
        e = self.x.e
        a = e.call(e.u32(e.u32(self.mgr) + 0xbc), self.mgr)[0]
        b = e.call(e.u32(e.u32(self.mgr + 0x14) + 0x64), self.mgr + 0x14)[0]
        return a, b, e.rd(self.x.p + 0x9d, 1)[0], self.m.P.get_start_mode()


def run_case(spec):
    """spec: name, proc, sig, nblk, ops {block: [op]}; ops as H077 plus ("9d", v, via). Returns (result, output blob)."""
    t0 = time.time()
    rg = Rig(spec["proc"], spec.get("mutant"), spec.get("raw_mute")); x, m = rg.x, rg.m
    nblk = spec.get("nblk", 240); ops = spec.get("ops", {}); emu_only = spec.get("emu_only")
    L, R = signal(spec.get("sig", "noise"), nblk, seed=spec.get("seed", 5))
    res = dict(name=spec["name"], samples=0, exact=0, maxdiff=0.0, pdiff=0, evdiff=0, wdiff=0, rdiff=0, first=None, wet_blocks=0,
               setter_calls=0, setter_slot_calls=0)
    blob = b""; trace = []
    for b in range(nblk):
        x.ev = []; x.s14 = []; m.P.log = []
        for op in ops.get(b, []):
            if op[0] == "fx": x.set_fx_type(op[1]); m.P.set_fx_type(op[1])
            elif op[0] == "dis": x.set_disabled(op[1]); m.P.set_disabled(op[1])
            elif op[0] == "p": x.set_param(op[1], op[2], op[3]); m.set_param(op[1], op[2], op[3])
            elif op[0] == "bpm": x.bpm = op[1]; m.bpm = op[1]
            elif op[0] == "byp": x.set_bypass(op[1]); m.P.set_bypass(op[1])
            elif op[0] == "9d":
                n0 = len(x.ev); rg.set9d(op[1], op[2]); res["setter_calls"] += 1
                res["setter_slot_calls"] += len(x.ev) - n0
        ev_ops = list(x.ev)
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        oL, oR = x.block(xL, xR)
        blob += pack(oL) + pack(oR)
        if any(f2u(a_) != f2u(c_) and a_ != 0.0 for a_, c_ in zip(oL + oR, xL + xR)): res["wet_blocks"] += 1
        tr = dict(b=b, ev=[str(v) for v in x.ev], ev_ops=[str(v) for v in ev_ops],
                  rms_in=math.sqrt(sum(v * v for v in xL + xR) / (2 * N)), rms_out=math.sqrt(sum(v * v for v in oL + oR) / (2 * N)),
                  rms_wet=math.sqrt(sum((a_ - c_) ** 2 for a_, c_ in zip(oL + oR, xL + xR)) / (2 * N)),
                  eq_in=sum(1 for a_, c_ in zip(oL + oR, xL + xR) if f2u(a_) == f2u(c_)), zero=sum(1 for a_ in oL + oR if a_ == 0.0))
        if emu_only:
            tr["out"] = oL + oR; trace.append(tr); continue
        mL = list(xL); mR = list(xR); m.P.process_block(mL, mR, N)
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
        r = rg.readers()
        if not (r[0] == r[1] == r[2] == r[3]):
            res["rdiff"] += 1
            if res["first"] is None: res["first"] = ("readers block %d (s47, IE+0x64, byte, model)" % b, r)
        ev_e = list(x.ev) + [("feed7", x.idx_of[o], f2u(F32(u2f(bits)))) for w, o, idx, bits in x.s14 if w == "feed" and idx == 7]
        ev_e += [("feed%d" % idx, x.idx_of[o], bits) for w, o, idx, bits in x.s14 if w == "feed" and idx != 7]
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
        tr.update(cur=ps_e["cur"], pend=ps_e["pend"], d9=ps_e["9d"], e9=ps_e["9e"])
        trace.append(tr)
    res["sha"] = sha(blob)[:16]
    res["ok"] = (not emu_only and res["exact"] == res["samples"] and not res["pdiff"] and not res["evdiff"] and not res["wdiff"]
                 and not res["rdiff"])
    res["secs"] = round(time.time() - t0, 1)
    if spec.get("keep_trace"): res["trace"] = trace
    return res, blob


def F32(v): return struct.unpack("<f", struct.pack("<f", v))[0]


def signal(kind, nblk, seed=5):
    """H077 signals plus: "tail" = noise 0.5 for blocks 0-59, then silence, one impulse 0.9 (both channels) at block 120 sample 0;
    "imp120" = silence with that impulse only."""
    if kind not in ("tail", "imp120"): return H77.signal(kind, nblk, seed=seed)
    g = random.Random(seed); n = nblk * N; L = [0.0] * n; R = [0.0] * n
    if kind == "tail":
        for i in range(60 * N): L[i] = F32(g.uniform(-0.5, 0.5)); R[i] = F32(g.uniform(-0.5, 0.5))
    L[120 * N] = F32(0.9); R[120 * N] = F32(0.9)
    return L, R


# ===================================================================================================================== cases
VIAS = ("s46", "ie60", "direct")


def sched(name, t, t2, via):
    """A: 1->0 / 0->1 / repeat while enabled. B: while disabled (+0x9e = 1) and re-enable. C: pending swap outstanding (type change
    fade-out, setter hits the NEW pending effect). D: during a fade-out to Off (+0x90 = 0) and during a disable fade-out.
    E: Off (-1): setter before any type, then type from Off (setter before the first block), Off again, re-select."""
    V = lambda v: ("9d", v, via)
    if name == "A": return {0: [("fx", t)], 60: [V(0)], 110: [V(1)], 150: [V(0)], 151: [V(0)], 180: [V(1)], 181: [V(1)], 210: [V(0)]}
    if name == "B": return {0: [("fx", t)], 40: [("dis", 1)], 60: [V(0)], 90: [("dis", 0)], 140: [V(1)], 170: [("dis", 1)],
                            175: [V(0)], 176: [V(1)], 200: [("dis", 0)], 220: [V(0)]}
    if name == "C": return {0: [("fx", t)], 60: [("fx", t2)], 61: [V(0)], 120: [("fx", t)], 121: [V(1)], 150: [V(0)],
                            170: [("fx", t2), V(1)], 172: [V(0)], 200: [("fx", t)], 201: [V(1)], 202: [V(0)], 203: [V(1)]}
    if name == "D": return {0: [("fx", t)], 60: [("fx", -1)], 61: [V(0)], 100: [("fx", t)], 101: [V(0)], 140: [("dis", 1), V(1)],
                            142: [V(0)], 180: [("dis", 0)], 200: [V(1)]}
    if name == "E": return {10: [V(0)], 30: [("fx", t), V(0)], 80: [V(1)], 120: [("fx", -1)], 160: [V(0)], 200: [("fx", t2)],
                            201: [V(0)], 220: [V(1)]}
    raise ValueError(name)


def matrix_cases():
    cases = []; k = 0
    for proc in ("master", "send", "insert"):
        tl = TYPES[proc]
        for j, t in enumerate(tl):
            t2 = tl[(j + 1) % len(tl)]
            for nm in "ABCDE":
                ops = {b: list(v) for b, v in sched(nm, t, t2, VIAS[k % 3]).items()}
                ops.setdefault(0, [])[:0] = [("p", t, i, v) for i, v in pre(proc, t)] + [("p", t2, i, v) for i, v in pre(proc, t2)]
                ops[0][:0] = [("bpm", 120.0)]
                sig = ("noise", "sine", "impulse")[k % 3]
                cases.append(dict(name="%s_%s_%d_%s_%s_%s" % (proc, nm, t, kinds(proc)[t], VIAS[k % 3], sig), proc=proc, sig=sig,
                                  nblk=240, ops=ops, section="c3", keep_trace=True, sched=nm, t=t))
                k += 1
    return cases


def fuzz_cases(nseed=4):
    cases = []
    for proc in ("master", "send", "insert"):
        tl = TYPES[proc]
        for s in range(nseed):
            g = random.Random(7900 + 31 * s + len(proc)); ops = {0: [("bpm", 120.0)]}
            for t in tl: ops[0] += [("p", t, i, v) for i, v in pre(proc, t)]
            for b in range(240):
                if g.random() < 0.12:
                    r = g.random()
                    if r < 0.5: op = ("9d", g.choice((0, 1)), g.choice(VIAS))
                    elif r < 0.8: op = ("fx", g.choice(tl + (-1,)))
                    else: op = ("dis", g.choice((0, 1)))
                    ops.setdefault(b, []).append(op)
                    if g.random() < 0.3: ops[b].append(("9d", g.choice((0, 1)), g.choice(VIAS)))
            cases.append(dict(name="%s_fuzz%d" % (proc, s), proc=proc, sig=("noise", "sine")[s % 2], nblk=240, ops=ops, section="c3f",
                              seed=11 + s))
    return cases


def edge_cases():
    """Non-boolean values: strb keeps the low byte, the branch tests all 32 bits (0x100 -> stores 0 but calls slot 7)."""
    out = []
    for proc in ("master", "send"):
        ops = {0: [("p", 2, 5, 0.7), ("fx", 2)], 40: [("9d", 2, "s46")], 80: [("9d", 0x100, "direct")], 120: [("fx", 6)],
               160: [("9d", 1, "s46")], 170: [("9d", 0x100, "ie60")], 200: [("fx", 2)]}
        out.append(dict(name="%s_edge_nonbool" % proc, proc=proc, sig="noise", nblk=240, ops=ops, section="c3e", keep_trace=True))
    # Send: +0x9d = 2 makes processBlock pass 2 ^ 1 = 3 to MuteSmoother setMuted 0xe8050, which compares its stored byte (1) with the
    # full argument and so re-arms the ramp every block; fx_processors.MuteSmoother normalises to 0/1. The plain-model Send case above is
    # expected to differ; this variant uses a harness-local verbatim set_muted and must be bit-exact.
    out.append(dict(out[-1], name="send_edge_nonbool_rawmute", raw_mute=True))
    return out


# ===================================================================================================================== alternative setter models
def _m_store_without_pending(cls):
    class M(cls):
        def set_start_mode(self, v):
            if self.p90 is None: self.nine_d = v & 0xff; return
            cls.set_start_mode(self, v)
    return M


def _m_store_only(cls):
    class M(cls):
        def set_start_mode(self, v):
            if self.p90 is not None: self.nine_d = v & 0xff
    return M


def _m_on_current(cls):
    class M(cls):
        def set_start_mode(self, v):
            if self.p90 is None: return
            self.nine_d = v & 0xff
            if self.nine_e or self.p8c is None: return
            i = next((k for k, x in self.fx.items() if x is self.p8c), None)
            if v: self.p8c.slot7(0); self.log.append(("slot7", i))
            else: self.p8c.slot8(); self.log.append(("slot8", i))
    return M


def _m_change_only(cls):
    class M(cls):
        def set_start_mode(self, v):
            if (v & 0xff) == self.nine_d and self.p90 is not None: return
            cls.set_start_mode(self, v)
    return M


def _m_ignore_disable(cls):
    class M(cls):
        def set_start_mode(self, v):
            e = self.p90
            if e is None: return
            self.nine_d = v & 0xff
            i = next((k for k, x in self.fx.items() if x is e), None)
            if v: e.slot7(0); self.log.append(("slot7", i))
            else: e.slot8(); self.log.append(("slot8", i))
    return M


def _m_inverted(cls):
    class M(cls):
        def set_start_mode(self, v):
            e = self.p90
            if e is None: return
            self.nine_d = v & 0xff
            if self.nine_e: return
            i = next((k for k, x in self.fx.items() if x is e), None)
            if not v: e.slot7(0); self.log.append(("slot7", i))
            else: e.slot8(); self.log.append(("slot8", i))
    return M


def _m_send_mute_ignores_9d(cls):
    class M(cls):
        def mute_flag(self): return 1 if (self.pend == -1 or self.nine_e) else 0
    return M


MUTANTS = {"store_without_pending": _m_store_without_pending, "store_only_no_call": _m_store_only, "call_on_current": _m_on_current,
           "call_only_on_change": _m_change_only, "call_even_if_disabled": _m_ignore_disable, "slot7_8_swapped": _m_inverted,
           "send_mute_ignores_9d": _m_send_mute_ignores_9d}


def mutant_cases():
    M = {c["name"]: c for c in matrix_cases()}
    pick = lambda pfx: next(c for n, c in M.items() if n.startswith(pfx))
    L = [("store_without_pending", "master_E_0"), ("store_without_pending", "send_E_1"), ("store_only_no_call", "master_A_2"),
         ("store_only_no_call", "insert_A_0"), ("call_on_current", "master_C_7"), ("call_on_current", "insert_C_4"),
         ("call_only_on_change", "send_A_2"), ("call_even_if_disabled", "master_B_6"), ("call_even_if_disabled", "insert_B_5"),
         ("slot7_8_swapped", "send_A_7"), ("send_mute_ignores_9d", "send_A_0")]
    return [dict(pick(c), name="mut_%s__%s" % (mu, c), mutant=mu, section="c3m", keep_trace=False) for mu, c in L]


# ===================================================================================================================== audible meaning (c4)
def meaning_cases():
    """Pairs (toggled, reference) emulated only: fx t at 0; +0x9d -> 0 at 80 (while running); -> 1 at 160. Reference: no setter."""
    out = []
    for proc in ("master", "send", "insert"):
        for t in TYPES[proc][:4]:
            base = {0: [("bpm", 120.0)] + [("p", t, i, v) for i, v in pre(proc, t)] + [("fx", t)]}
            tog = {b: list(v) for b, v in base.items()}; tog[80] = [("9d", 0, "s46")]; tog[160] = [("9d", 1, "s46")]
            # activation with +0x9d = 0: set 0 while running another type, then change type (swap -> slot 5 + slot 8)
            t2 = TYPES[proc][(TYPES[proc].index(t) + 1) % len(TYPES[proc])]
            act = {0: [("bpm", 120.0)] + [("p", t2, i, v) for i, v in pre(proc, t2)] + [("p", t, i, v) for i, v in pre(proc, t)] +
                   [("fx", t2)], 30: [("9d", 0, "s46")], 60: [("fx", t)], 160: [("9d", 1, "s46")]}
            ref2 = {0: act[0], 60: [("fx", t)]}
            for nm, ops in (("tog", tog), ("ref", base), ("act0", act), ("actref", ref2)):
                out.append(dict(name="%s_%d_%s_%s" % (proc, t, kinds(proc)[t], nm), proc=proc, sig="noise", nblk=240, ops=ops,
                                section="c4", keep_trace=True, emu_only=True, t=t, kind=nm))
            # new input after OFF (impulse at 120, silence otherwise) and tails of input that arrived before OFF ("tail" signal)
            off = {b: list(v) for b, v in base.items()}; off[80] = [("9d", 0, "s46")]
            for sig in ("imp120", "tail"):
                for nm, ops in (("off", off), ("on", base)):
                    out.append(dict(name="%s_%d_%s_%s_%s" % (proc, t, kinds(proc)[t], sig, nm), proc=proc, sig=sig, nblk=300, ops=ops,
                                    section="c4", keep_trace=True, emu_only=True, t=t, kind=sig + "_" + nm))
    return out


def meaning_table(results):
    R = {r["name"]: r for r, _ in results if r.get("section") == "c4" and "trace" in r}
    rows = []
    for nm, r in sorted(R.items()):
        if nm.endswith("_imp120_off") or nm.endswith("_tail_off"):
            ref = R[nm[:-4] + "_on"]; a, b = r["trace"], ref["trace"]; send = r["proc"] == "send"
            L0, R0 = signal("imp120" if "_imp120_" in nm else "tail", 300)
            def e(tr, lo, hi):
                acc = 0.0
                for k in range(lo, hi):
                    o = tr[k]["out"]; dry = ([0.0] * (2 * N)) if send else (L0[k * N:k * N + N] + R0[k * N:k * N + N])
                    acc += sum((p - q) ** 2 for p, q in zip(o, dry))
                return math.sqrt(acc / ((hi - lo) * 2 * N))
            if "_imp120_" in nm:
                rows.append(dict(case=nm, what="new input after OFF: rms(out - dry) blocks 120-300", off=round(e(a, 120, 300), 6),
                                 on=round(e(b, 120, 300), 6)))
            else:
                rows.append(dict(case=nm, what="tail of pre-OFF input: rms(out - dry) blocks 81-119 / 121-300", off=(round(e(a, 81, 120), 5),
                                 round(e(a, 121, 300), 5)), on=(round(e(b, 81, 120), 5), round(e(b, 121, 300), 5))))
            continue
        if not nm.endswith("_tog") and not nm.endswith("_act0"): continue
        ref = R[nm[:-4] + "_ref"] if nm.endswith("_tog") else R[nm[:-5] + "_actref"]
        a, b = r["trace"], ref["trace"]
        def seg(lo, hi, key): return sum(a[k][key] for k in range(lo, hi)) / (hi - lo)
        def first_dry(lo, hi):
            for k in range(lo, hi):
                if a[k]["eq_in"] == 2 * N: return k - lo
            return None
        def first_zero(lo, hi):
            for k in range(lo, hi):
                if a[k]["zero"] == 2 * N: return k - lo
            return None
        def diffref(lo, hi):
            return max(max(abs(p - q) for p, q in zip(a[k]["out"], b[k]["out"])) for k in range(lo, hi))
        def same_as_ref_from(lo, hi):
            for k in range(lo, hi):
                if all(f2u(p) == f2u(q) for j in range(k, hi) for p, q in zip(a[j]["out"], b[j]["out"])): return k - lo
            return None
        if nm.endswith("_tog"):
            off0 = 80; on0 = 160
            rows.append(dict(case=nm, ev80=a[80]["ev_ops"], ev160=a[160]["ev_ops"],
                             wet_before=round(seg(40, 80, "rms_wet"), 5), wet_off=round(seg(100, 160, "rms_wet"), 5),
                             wet_on=round(seg(200, 240, "rms_wet"), 5), out_off=round(seg(100, 160, "rms_out"), 5),
                             out_ref_off=round(sum(b[k]["rms_out"] for k in range(100, 160)) / 60, 5),
                             dry_after_off_blk=first_dry(off0, on0), zero_after_off_blk=first_zero(off0, on0),
                             same_as_ref_after_on_blk=same_as_ref_from(on0, 240), maxdiff_ref_off=round(diffref(100, 160), 5)))
        else:
            rows.append(dict(case=nm, ev60_64=[e for k in range(60, 66) for e in a[k]["ev"]], ev160=a[160]["ev_ops"],
                             wet_act0=round(seg(70, 160, "rms_wet"), 5), wet_ref=round(sum(b[k]["rms_wet"] for k in range(70, 160)) / 90, 5),
                             out_act0=round(seg(70, 160, "rms_out"), 5), dry_from_act=first_dry(64, 160), zero_from_act=first_zero(64, 160),
                             wet_on=round(seg(200, 240, "rms_wet"), 5), same_as_ref_after_on_blk=same_as_ref_from(160, 240)))
    return rows


# ===================================================================================================================== static (c1, c2)
def static_c1(im, P, check):
    J = {}
    lst = [(i.address, i.mnemonic, i.op_str) for i in im.disasm(SETTER, SETTER + 0x4c)]
    want = [("ldr", "r2, [r0, #0x90]"), ("push", "{r3, lr}"), ("cmp", "r2, #0"), ("popeq", "{r3, pc}"), ("ldrb", "r3, [r0, #0x9e]"),
            ("strb", "r1, [r0, #0x9d]"), ("cmp", "r3, #0"), ("popne", "{r3, pc}"), ("cmp", "r1, #0"), ("ldr", "r3, [r2]"),
            ("mov", "r0, r2"), ("bne", "#0x1129f8"), ("ldr", "r3, [r3, #0x20]"), ("blx", "r3"), ("pop", "{r3, pc}"),
            ("mov", "r1, #0"), ("ldr", "r3, [r3, #0x1c]"), ("blx", "r3"), ("pop", "{r3, pc}")]
    check([(m, o) for _, m, o in lst[:len(want)]] == want,
          "0x1129bc = 19 instructions: +0x90 == 0 -> return; +0x9d := r1 (byte); +0x9e != 0 -> return; r1 != 0 -> (+0x90)->vt+0x1c "
          "(slot 7)(e, 0) else ->vt+0x20 (slot 8)(e); returns the slot's r0 (void in practice)")
    P("    next function start after 0x1129bc: 0x%x (= 0x112a08, so 0x1129bc..0x112a04 is the whole body)" % im.starts()[
        bisect.bisect_right(im.starts(), SETTER)])
    th = {a: [(i.mnemonic, i.op_str) for i in im.disasm(a, a + 8)] for a in (READER_IE64, READER, THUNK_IE60, THUNK46, DIS_THUNK)}
    check(th[THUNK46] == [("ldr", "r0, [r0, #0x1c]"), ("b", "#0x1129bc")] and th[THUNK_IE60] == [("sub", "r0, r0, #0x14"), ("b", "#0x11caf4")],
          "0x11caf4 = `r0 := [this+0x1c]; b 0x1129bc` (manager -> processor); 0x11caec = IEffector adjustor `sub r0,#0x14; b 0x11caf4`")
    rd = [(i.mnemonic, i.op_str) for i in im.disasm(READER, READER + 12)]
    check(rd == [("ldr", "r3, [r0, #0x1c]"), ("ldrb", "r0, [r3, #0x9d]"), ("bx", "lr")] and
          th[READER_IE64] == [("sub", "r0, r0, #0x14"), ("b", "#0x11cae0")],
          "0x11cae0 = `return [[this+0x1c]+0x9d]` (byte); 0x11cad8 = IEffector adjustor -> 0x11cae0")
    # vtable words
    vt = {}
    for v in (SETTER, THUNK46, READER, THUNK_IE60, READER_IE64):
        locs = []; pat = struct.pack("<I", v); d = im.data; i = d.find(pat)
        while i >= 0:
            if i % 4 == 0:
                for va, sz, o in im.segs:
                    if o <= i < o + sz: locs.append(va + i - o)
            i = d.find(pat, i + 1)
        vt[v] = locs
    def owner(L):
        for k in range(1, 120):
            a = L - 4 * k; ti = im.u32(a)
            if ti and im.off(ti) is not None:
                nmp = im.u32(ti + 4)
                if nmp and im.off(nmp) is not None:
                    s = im.cstr(nmp, 60)
                    if s and re.match(r"^\d+[A-Za-z]", s) and im.u32(a - 4) in (0, 0xffffffec):
                        return "%s vt 0x%x slot %d (off 0x%x, ott %d)" % (s, a + 4, k - 1, 4 * (k - 1), s32(im.u32(a - 4)))
        return "?"
    J["vtable_words"] = {hex(v): [(hex(L), owner(L)) for L in locs] for v, locs in vt.items()}
    for v, locs in J["vtable_words"].items():
        P("    word %s at: %s" % (v, "; ".join("%s %s" % x for x in locs) or "none"))
    check(vt[SETTER] == [] and len(vt[THUNK46]) == 7 and len(vt[READER]) == 7 and len(vt[THUNK_IE60]) == 4 and len(vt[READER_IE64]) == 4,
          "0x1129bc has no pointer anywhere; 0x11caf4/0x11cae0 sit at primary slots 46/47 of 7 vtables (base, Insert, Master, Send + 3 "
          "base construction vtables); 0x11caec/0x11cad8 at IEffector +0x60/+0x64 of the 4 IEffector vtables")
    # +0x9d sweep
    lo, hi = im.sec[".text"]; o0 = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o0); hits = []
    for i, w in enumerate(W):
        va = lo + 4 * i
        if w >> 28 == 0xf: continue
        rn = (w >> 16) & 0xf
        if (w >> 25) & 7 == 2 and (w >> 24) & 1 and rn != 15:              # ldr/str/ldrb/strb imm, offset/pre-index
            off = (w & 0xfff) * (1 if (w >> 23) & 1 else -1); B = (w >> 22) & 1
            if (B and off == 0x9d) or (not B and 0x9a <= off <= 0x9d): hits.append((va, "byte" if B else "word"))
        if (w >> 25) & 7 == 0 and (w >> 4) & 9 == 9 and (w >> 5) & 3 and (w >> 22) & 1 and (w >> 24) & 1 and rn != 15:
            off = (((w >> 4) & 0xf0) | (w & 0xf)) * (1 if (w >> 23) & 1 else -1); sh = (w >> 5) & 3; L_ = (w >> 20) & 1
            kd = {(1, 0): "strh", (1, 1): "ldrh", (2, 1): "ldrsb", (3, 1): "ldrsh", (2, 0): "ldrd", (3, 0): "strd"}[(sh, L_)]
            if (kd in ("strh", "ldrh", "ldrsh") and off == 0x9c) or (kd == "ldrsb" and off == 0x9d) or \
               (kd in ("ldrd", "strd") and 0x96 <= off <= 0x9c): hits.append((va, kd))
    reg = [(va, k) for va, k in hits if 0x112000 <= va < 0x132000]
    other = [(va, k) for va, k in hits if not (0x112000 <= va < 0x132000)]
    rows = []
    for va, k in reg:
        ins = next(im.md.disasm(im.data[im.off(va):im.off(va) + 4], va)); rows.append((hex(va), hex(im.func_of(va)[0]), ins.mnemonic, ins.op_str))
    J["sweep"] = dict(total=len(hits), by_kind={k: sum(1 for _, kk in hits if kk == k) for k in sorted(set(kk for _, kk in hits))},
                      processor_region=rows, other_byte_sites=[(hex(va), hex(im.func_of(va)[0])) for va, k in other if k in ("byte", "ldrsb")])
    P("    sweep (.text, aligned ARM words, non-pc base): %d accesses that can touch byte 0x9d (%s); in 0x112000-0x132000 (processor + "
      "manager code): %d" % (len(hits), J["sweep"]["by_kind"], len(reg)))
    for r in rows: P("      %s fn %s  %s %s" % r)
    callers_of_other = {}
    for va, k in other:
        f = im.func_of(va)[0]
        callers_of_other[f] = [s for s, t, kd in im.direct_calls() if t == f and kd in ("bl", "b")]
    inproc = [hex(f) for f, cs in callers_of_other.items() if any(0x112000 <= c < 0x132000 for c in cs)]
    J["sweep"]["other_fns"] = len(callers_of_other); J["sweep"]["other_fns_called_from_processor_region"] = inproc
    expect = {("0x112914", "strb"), ("0x1129d0", "strb"), ("0x112c38", "ldrb"), ("0x116b78", "ldrb"), ("0x119b44", "ldrb"),
              ("0x119b84", "ldrb"), ("0x11cae4", "ldrb")}
    # the two outside functions that processor/manager code calls: EffectBase ctor 0x1067d8 (this = the new effect object: word stores
    # +0x98 mode / +0x9c block size) and 0x34bc8c (halfwords of the global at literal 0xf61f18) - neither receives a processor
    eb = [(i.address, i.op_str) for i in im.disasm(0x1067d8, 0x1068d0) if re.search(r"#0x9[89a-d]\]", i.op_str)]
    gl = im.u32(0x34bc8c + 8 + 0x12c) == 0xf61f18 and [(i.mnemonic, i.op_str) for i in im.disasm(0x34bca8, 0x34bcac)] == [("ldrh", "r1, [r3, #0x9c]")]
    J["sweep"]["outside_called"] = dict(effectbase_ctor=[(hex(a_), o_) for a_, o_ in eb], global_f61f18=bool(gl))
    check(set((r[0], r[2]) for r in rows) == expect and set(inproc) == {"0x1067d8", "0x34bc8c"} and gl and
          [o_ for _, o_ in eb] == ["r5, [r4, #0x98]", "r6, [r4, #0x9c]", "r3, [r4, #0x98]"],
          "in processor/manager code +0x9d is accessed at exactly 7 sites: writers ctor 0x112914, setter 0x1129d0; readers Master pB "
          "0x112c38, Insert pB 0x116b78, Send pB 0x119b44 (slot 7/8 choice) + 0x119b84 (input-mute flag, eor #1), reader 0x11cae4; of the "
          "%d other functions with a 0x9d-reaching access only 2 are called from that region and neither on a processor (EffectBase ctor "
          "0x1067d8 words +0x98/+0x9c of the effect; 0x34bc8c halfword of global 0xf61f18)" % len(callers_of_other))
    return J


def s32(u): return u - (1 << 32) if u is not None and u & 0x80000000 else u


def _words(im, v):
    pat = struct.pack("<I", v); d = im.data; i = d.find(pat); locs = []
    while i >= 0:
        if i % 4 == 0:
            for va, sz, o in im.segs:
                if o <= i < o + sz: locs.append(va + i - o)
        i = d.find(pat, i + 1)
    return locs


def _vt_owner(im, L, back=400):
    for k in range(1, back):
        a = L - 4 * k; ti = im.u32(a)
        if ti and im.off(ti) is not None and im.u32(ti + 4) and im.off(im.u32(ti + 4)) is not None:
            s = im.cstr(im.u32(ti + 4), 200)
            if s and re.match(r"^(N?\d+[A-Za-z_]|\*?Z?N\d)", s) and im.u32(a - 4) is not None and (im.u32(a - 4) == 0 or im.u32(a - 4) >= 0xffff0000):
                return "%s/slot%d" % (s, k - 1)
    return None


MGR_SOURCES = ("R.0x70", "R.0x74", "R.0x90", "R.0x10.0x24")          # root routes to IEffectors (F168)
EFF_GETTERS = (0x1c7888, 0x1c7890, 0x1b9510, 0x1b94f0, 0x1b94c0)      # TrackUnit/HexaTrackAudioSystem IEffector getters (F168)


def static_c2(im, P, check):
    """Callers. (a) direct branches to the five entry points; (b) the UI FX ON/OFF handlers and their ModelInterface stubs;
    (c) every `ldr rF,[rV,#off]` ... `blx rF` site in .text (aligned-word bit patterns, 11-word window) with off in {0xb8, 0xbc} (manager
    primary slots 46/47) or {0x60, 0x64} (IEffector), receiver provenance by harness/lib/armflow.py tag analysis of the containing
    function (refined starts)."""
    from armflow import Flow, refined_starts
    J = {}
    ent = (SETTER, THUNK46, READER, THUNK_IE60, READER_IE64)
    dc = [(hex(s), hex(t), k) for s, t, k in im.direct_calls() if t in ent]
    J["direct"] = dc
    check(sorted(dc) == sorted([("0x11cadc", "0x11cae0", "b"), ("0x11caf0", "0x11caf4", "b"), ("0x11caf8", "0x1129bc", "b")]),
          "direct branches to 0x1129bc/0x11caf4/0x11cae0/0x11caec/0x11cad8: only the three thunk tail branches (no bl from anywhere)")
    # (b) UI FX ON/OFF
    ui = {}
    for nm, setter, getter in (("SendMaster", 0x300e30, 0x300eb4), ("Insert", 0x304470, 0x3044f4)):
        body = [(i.mnemonic, i.op_str) for i in im.disasm(setter, setter + 0x58)]
        lits = [im.u32(i.address + 8 + int(m.group(1), 0)) for i in im.disasm(setter, setter + 0x58)
                for m in [re.match(r"\w+, \[pc, #(0x[0-9a-f]+)\]$", i.op_str)] if i.mnemonic == "ldr" and m]
        calls = [t for s_, t, k in im.direct_calls() if setter <= s_ < setter + 0x58 and k == "bl"]
        vcalls = [o for o in body if o[0] == "blx"]
        g = [(i.mnemonic, i.op_str) for i in im.disasm(getter, getter + 8)]
        callers = [(hex(s_), k) for s_, t, k in im.direct_calls() if t == setter]
        ui[nm] = dict(setter=hex(setter), log=im.cstr(lits[0], 60) if lits else None, tail=im.cstr(lits[1], 8) if len(lits) > 1 else None,
                      bl=[hex(c) for c in calls], blx=len(vcalls), getter=hex(getter), getter_body=g, callers=callers)
        P("    ModelInterface %s FxOnOff: setter %s builds \"%s\" + \"%s\", calls %s, %d indirect calls; getter %s = %s; callers %s" % (
            nm, hex(setter), ui[nm]["log"], ui[nm]["tail"], ui[nm]["bl"], len(vcalls), hex(getter), g, callers))
    lc = [(i.mnemonic, i.op_str) for i in im.disasm(0x647ca0, 0x647ccc)]
    check(all(u["blx"] == 0 and u["getter_body"] == [("mov", "r0, #0"), ("bx", "lr")] and u["bl"][-4:] == ["0x647ca0", "0x627f38", "0x627f38", "0x627f38"]
              for u in ui.values()) and ui["SendMaster"]["log"] == "ModelInterface::setSendMasterFxOnOff(" and
          ui["Insert"]["log"] == "ModelInterface::setInsertFxOnOff(" and ("bl", "#0x10d50") in lc,
          "UI FX ON/OFF is a stub in 1.60: ModelInterface::setSendMasterFxOnOff 0x300e30 / setInsertFxOnOff 0x304470 only build their own "
          "name + \")\" and print it (0x647ca0 -> std::ostream insert), no indirect call, no use of the value; the getters 0x300eb4 / "
          "0x3044f4 return 0")
    hs = {}
    for h in (0x23da9c, 0x23e9e8, 0x228734, 0x2291ac):
        own = [(hex(L), _vt_owner(im, L, 60)) for L in _words(im, h)]
        body = [(i.mnemonic, i.op_str) for i in im.disasm(h, h + 0x30)]
        hs[hex(h)] = dict(vtables=own, body_tail=body[-3:])
        P("    handler %s: vtable refs %s; ends %s" % (hex(h), own or "none (no pointer, no direct branch found)", body[5:11]))
    check(hs["0x23da9c"]["vtables"] and "FxMasterViewControllerBase" in hs["0x23da9c"]["vtables"][0][1] and "Handler_2" in hs["0x23da9c"]["vtables"][0][1]
          and hs["0x228734"]["vtables"] and "FxInsertViewControllerBase" in hs["0x228734"]["vtables"][0][1],
          "the button handlers FxMasterViewControllerBase::Handler_2 (0x23da9c) and FxInsertViewControllerBase::Handler (0x228734) toggle "
          "!getter() into a controller byte (+0x13d / +0x139, the on/off display state) and tail-call the stub setter")
    J["ui_onoff"] = dict(stubs=ui, handlers=hs)
    # (c) vcall scan
    lo, hi = im.sec[".text"]; n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, im.off(lo)); OFFS = (0xb8, 0xbc, 0x60, 0x64); cand = []
    for k, w in enumerate(W):
        if (w & 0x0ffffff0) != 0x012fff30 or (w >> 28) == 0xf: continue
        rf = w & 0xf
        for j in range(k - 1, max(k - 12, -1), -1):
            x = W[j]
            if (x >> 28) != 0xf and (x & 0x0ff00000) == 0x05900000 and ((x >> 12) & 0xf) == rf:
                if (x & 0xfff) in OFFS: cand.append((lo + 4 * k, x & 0xfff))
                break
            if (x >> 28) != 0xf and ((x >> 12) & 0xf) == rf and ((x >> 26) & 3) in (0, 1) and not ((x >> 20) & 1 == 0 and (x >> 26) & 3 == 1): break
    st = refined_starts(im); fl = Flow(im); byf = {}
    for a_, o_ in cand:
        f = st[bisect.bisect_right(st, a_) - 1]; byf.setdefault(f, []).append((a_, o_))
    rows = []
    for f, ss in byf.items():
        e_ = st[bisect.bisect_right(st, f)]
        try: evs = {ev["site"]: ev for ev in fl.analyse(f, e_)}
        except Exception: evs = {}
        for a_, o_ in ss:
            ev = evs.get(a_); obj = ev["obj"] if ev else None
            rows.append(dict(site=a_, off=o_, fn=f, obj=obj))
    def cat(r):
        o = r["obj"]
        if o is None: return "unresolved"
        if any(o == m or o.startswith(m + ".") for m in MGR_SOURCES): return "IEFFECTOR-ROUTE"
        if any(("RET:0x%x" % g) in o for g in EFF_GETTERS): return "IEFFECTOR-GETTER"
        if o == "R" or o.startswith("R."): return "root/other root object"
        if o.endswith("+0x1c") and 0x11c000 <= r["fn"] < 0x132000 and r["off"] == 0xbc: return "manager -> processor (+0x1c) vt+0xbc = setFxType"
        if o in ("r0", "ARG:r0") and 0x11c000 <= r["fn"] < 0x132000: return "MANAGER-SELF"
        if o in ("r0", "ARG:r0"): return "this-call outside manager code"
        if re.match(r"^0x[0-9a-f]+$", o): return "global/literal object"
        return "field of another object"
    C = {}
    for r in rows: r["cat"] = cat(r); C.setdefault(r["cat"], []).append(r)
    J["vcall"] = dict(candidates=len(cand), by_off={hex(o): sum(1 for _, oo in cand if oo == o) for o in OFFS}, functions=len(byf),
                      by_cat={k: len(v) for k, v in sorted(C.items())},
                      engine_sites=[(hex(r["site"]), hex(r["off"]), hex(r["fn"]), r["obj"], r["cat"]) for r in rows if 0x100000 <= r["fn"] < 0x200000])
    P("    vcall sites `ldr f,[vptr,#off]; blx f`: %d (%s) in %d functions; receiver categories %s" % (
        len(cand), J["vcall"]["by_off"], len(byf), J["vcall"]["by_cat"]))
    check(not any(k in C for k in ("IEFFECTOR-ROUTE", "IEFFECTOR-GETTER", "MANAGER-SELF")),
          "no vt+0xb8/+0xbc/+0x60/+0x64 call site has a receiver traced to an IEffector route (root vt+0x70/0x74/0x90, track vt+0x24), an "
          "IEffector getter, or `this` inside manager code (so no manager method - s10/s51 reload/s6 lock - calls slot 46/47 on itself)")
    return J, rows


# ===================================================================================================================== main
def _worker(spec):
    try:
        r, blob = run_case(spec)
    except Exception as ex:
        import traceback
        r = dict(name=spec["name"], ok=False, error="%s: %s" % (type(ex).__name__, ex), tb=traceback.format_exc()[-1500:]); blob = b""
    for k in ("section", "proc", "mutant", "sched", "t", "kind"): r[k] = spec.get(k)
    return r, blob


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H079"))
    ap.add_argument("--jobs", type=int, default=6); ap.add_argument("--only", default="c1,c2,c3,c3m,c4")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); only = set(a.only.split(","))
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = Image()
    if "c1" in only:
        P("== C1 static: setter 0x1129bc, thunks, vtable slots, +0x9d access sweep"); J["c1"] = static_c1(im, P, check)
    if "c2" in only:
        P("\n== C2 callers (static)"); J["c2"], _ = static_c2(im, P, check)
    jobs = []
    if "c3" in only: jobs += matrix_cases() + fuzz_cases() + edge_cases()
    if "c3m" in only: jobs += mutant_cases()
    if "c4" in only: jobs += meaning_cases()
    if jobs:
        P("\n== running %d emulation cases with %d jobs" % (len(jobs), a.jobs)); t0 = time.time()
        if a.jobs > 1:
            import multiprocessing as mp
            with mp.get_context("spawn").Pool(a.jobs) as pool: results = pool.map(_worker, jobs, chunksize=1)
        else:
            results = [_worker(s) for s in jobs]
        print("  done in %.0f s" % (time.time() - t0), flush=True)          # not in the report (keeps report/json deterministic)
        for sec, title in (("c3", "C3 matrix: schedules A-E x types x Insert/Master/Send, real setter vs set_start_mode"),
                           ("c3f", "C3 seeded fuzz (random 9d / type / disable ops, all three entry routes)"),
                           ("c3e", "C3 edge: non-boolean setter values (2, 0x100)"), ("c3m", "C3 alternative setter models (each must FAIL)")):
            rows = [(r, b) for r, b in results if r.get("section") == sec]
            if not rows: continue
            P("\n== " + title)
            for r, b in rows:
                if "error" in r: P("  %-44s ERROR %s" % (r["name"], r["error"][:300])); continue
                P("  %-44s %s samples %6d exact %6d maxdiff %.3g p/ev/wr/rd %d/%d/%d/%d setter %d (slot calls %d) wet %3d sha %s%s" % (
                    r["name"], "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["pdiff"], r["evdiff"], r["wdiff"],
                    r["rdiff"], r["setter_calls"], r["setter_slot_calls"], r["wet_blocks"], r["sha"],
                    "" if r["ok"] or sec == "c3m" else "  first %s" % (str(r["first"])[:400],)))
            if sec == "c3m":
                check(all("error" not in r and not r["ok"] for r, _ in rows), "c3m: every alternative setter model is refuted (%d/%d fail)" % (
                    sum(1 for r, _ in rows if not r.get("ok")), len(rows)))
                J[sec] = [{k: v for k, v in r.items() if k not in ("trace", "secs")} for r, _ in rows]; continue
            if sec == "c3e":
                d = {r["name"]: r for r, _ in rows}
                check(d["master_edge_nonbool"]["ok"] and d["send_edge_nonbool_rawmute"]["ok"] and not d["send_edge_nonbool"]["ok"],
                      "c3e: non-boolean values: Master bit-exact with set_start_mode (byte store, 32-bit test: 0x100 stores 0 but calls "
                      "slot 7); Send needs the verbatim 0xe8050 (no 0/1 normalisation) - fx_processors.MuteSmoother is valid for 0/1 only")
                J[sec] = [{k: v for k, v in r.items() if k not in ("trace", "secs")} for r, _ in rows]; continue
            blob = b"".join(b for _, b in rows); open(os.path.join(a.out, "%s_outputs.f32" % sec), "wb").write(blob)
            nok = sum(1 for r, _ in rows if r.get("ok"))
            P("  %s: %d/%d cases bit-exact, %d samples, %d setter calls (%d with a slot call), outputs sha256 %s" % (
                sec, nok, len(rows), sum(r.get("samples", 0) for r, _ in rows), sum(r.get("setter_calls", 0) for r, _ in rows),
                sum(1 for r, _ in rows for _ in [0] if r.get("setter_slot_calls")), sha(blob)))
            check(nok == len(rows), "%s: every case bit-exact (outputs, processor state, both readers, slot 5-8 + feed log, wrapper state, "
                                    "every block)" % sec)
            J[sec] = [{k: v for k, v in r.items() if k not in ("trace", "secs")} for r, _ in rows]
        c3 = [r for r, _ in results if r.get("section") == "c3" and "trace" in r]
        if c3:
            # per-schedule event summary at the setter blocks (first Master case)
            J["c3_setter_events"] = {r["name"]: {t["b"]: t["ev_ops"] for t in r["trace"] if t["ev_ops"] or t["b"] in ()} for r in c3}
            P("\n== C3 setter-call events (slot calls made by the setter itself, block: [events]) for one type per processor")
            for r in c3:
                if r["t"] in (0, 4) and r["proc"] in ("master", "send", "insert") and (r["proc"] != "insert" or r["t"] == 4):
                    sops = {b: e for b, e in J["c3_setter_events"][r["name"]].items() if any("slot7" in x or "slot8" in x for x in e)}
                    P("  %-40s %s" % (r["name"], " ".join("b%d:%s" % (b, ",".join(e)) for b, e in sorted(sops.items()))[:300]))
            ec = [r for r, _ in results if r.get("section") == "c3e" and "trace" in r]
            for r in ec:
                P("  edge %s: %s" % (r["name"], " ".join("b%d +0x9d=%d %s" % (t["b"], t["d9"], ",".join(t["ev_ops"]))
                                                        for t in r["trace"] if t["b"] in (40, 41, 80, 81, 160, 170, 171))))
        if "c4" in only:
            rows = meaning_table(results); J["c4"] = rows
            P("\n== C4 audible meaning (emulated only; toggled vs untouched reference, noise 0.5, rms per 128 samples)")
            for r in rows: P("  " + json.dumps(r))
            open(os.path.join(a.out, "c4_traces.json"), "w").write(json.dumps(
                {r["name"]: [{k: v for k, v in t.items() if k != "out"} for t in r["trace"]] for r, _ in results
                 if r.get("section") == "c4" and "trace" in r}, sort_keys=True))
    J["fails"] = fails
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h079_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h079.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
