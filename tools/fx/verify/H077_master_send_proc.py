#!/usr/bin/env python3
"""H077 (+ H056, H037) — MasterFxProcessor / SendFxProcessor hosts: real 1.60 processor ctors, setFxType, processBlock and the
FxProcessorBase disable switch 0x112a08, driven in unicorn against harness/models/fx_processors.py (MasterProcessor,
SendProcessor, MuteSmoother) wrapping the per-effect models in harness/models/effectbase.py EffectBase.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Emulation is guest-memory only; nothing is written
outside --out and no image is built. Own code only; Pioneer bytes are read at run time and never stored.

Emulated side per case: fresh Emu; the .init_array pieces the effects read (LoFi 0x137cc, MMF 0x13a28, PEQ 0x13aa8, Fraction tables
0x6cbe0..0x6ce8c); REAL processor ctor (Master 0x114bc0 / Send 0x11bbe4, which builds all 10 effects, slot 22, 0x106c7c and slot 52
defaults); REAL prepareToPlay (Master 0x112cd0 / Send 0x119bd8 -> MuteSmoother 0xe7fd8) with the JUCE call 0x5f9e90
(setPlayConfigDetails) skipped; REAL 0x112a08(p, 0) to enable (the ctor leaves +0x9e = 1); then REAL setFxType / processBlock /
0x112a08. Stand-ins: tempo provider object at +0x94 (vt+0x1c returns the case BPM as a double), pthread_* stubs for the JUCE
AudioProcessor base, the bus buffer object (+0xc channel pointers, +0x94 byte).
Model side: per-effect models built at ctor state, then the slot-14 calls the REAL slot 52 made (logged), slot 22(0), post-HPF per
the ctor's +0xcc bytes; MasterProcessor / SendProcessor.

Sections (criteria of kb/cycles/028.md): C1 ctor facts; C3 type matrix + FX-change schedules; C4 disable (H056); C5 tempo feed and
slot-52 defaults (H037, Insert ctor for comparison); C6 alternatives (model mutants that must fail).
Run: .venv/bin/python -B harness/H077_master_send_proc.py --out DIR [--jobs N] [--quick]
"""
import argparse, hashlib, json, math, os, random, struct, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, d2u, SP, init_array                  # noqa: E402

def _r0(v): return lambda em: em.setr(0, v)
for _nm, _v in (("pthread_self", 1), ("pthread_mutex_init", 0), ("pthread_mutex_lock", 0), ("pthread_mutex_unlock", 0),
                ("pthread_mutex_destroy", 0), ("pthread_mutexattr_init", 0), ("pthread_mutexattr_settype", 0),
                ("pthread_mutexattr_destroy", 0), ("pthread_mutexattr_setprotocol", 0)):
    emu.STUBS.setdefault(_nm, (_r0(_v), "H077 stub (JUCE AudioProcessor base lock): returns %d" % _v))

import H031_osc_model as H31                                   # noqa: E402
import H044_effectbase_wrapper as H44                          # noqa: E402
import H040_compressor_model as H40                            # noqa: E402
import effectbase as EB                                        # noqa: E402
import fx_processors as FP                                     # noqa: E402
import chorus as C, flanger as FL, peq as MP, mmf as MM, lofi as ML, distortion as DM, phaser as MPh   # noqa: E402
import send_delay as SD, send_reverb as SR, insert_delay as ID  # noqa: E402
from lofi import F                                             # noqa: E402

N = 64
KINDS = ["send_delay", "send_reverb", "chorus", "flanger", "peq", "mmf", "lofi", "send_compressor", "distortion", "phaser"]
KINDS_INS = ["chorus", "flanger", "peq", "mmf", "insert_delay", "lofi", "distortion", "insert_compressor", "phaser", None]  # 9 Ducker: not modelled here
BYPASS_SET = 0x1129b4                                     # FxProcessorBase: strb r1, [r0, #0x9c]
PROC = {
    "master": dict(ctor=0x114bc0, size=0xa8, vt=0x842aa8, block=0x112acc, setfx=0x1132e4, prep=0x112cd0, s52=(0x1133f4, 0x114ad4),
                   pb=(0x112acc, 0x112cbc), cur=0xa0, pend=0xa4, ms=None),
    "send": dict(ctor=0x11bbe4, size=0xb0, vt=0x842d40, block=0x119994, setfx=0x11a254, prep=0x119bd8, s52=(0x11a364, 0x11baa8),
                 pb=(0x119994, 0x119bd8), cur=0xa0, pend=0xa4, ms=0xa8),
    "insert": dict(ctor=0x118b0c, size=0x148, vt=0x842c10, block=0x116860, setfx=0x11735c, prep=0x116bc4, s52=(0x117434, 0x118a9c),
                   pb=(0x116860, 0x116bc4), cur=0xa4, pend=0xa8, ms=0x144),
}
DISABLE = 0x112a08
SLOT14 = (0x105d24, 0x116224, 0x1163f0, 0x1164d8)          # base, Chorus, Flanger, Distortion (vt+0x38 of the 10 classes)
SLOTS = {0x10623c: "slot5", 0x105c94: "slot6", 0x105c58: "slot7", 0x105c20: "slot8"}
JUCE_SETPLAY = 0x5f9e90
TEMPO_FN = emu.SENTINEL + 0x300
STATIC_INIT = (0x137cc, 0x13a28, 0x13aa8)
FRAC_INIT = (0x6cbe0, 0x6ce8c)


def sha(b): return hashlib.sha256(b).hexdigest()
def pack(xs): return struct.pack("<%df" % len(xs), *xs)
def s32(u): return u - (1 << 32) if u & 0x80000000 else u


# ===================================================================================================================== emulated rig
class EmuProc:
    def __init__(self, which, enable=True):
        self.which = which; P = PROC[which]; self.P = P
        self.e = e = H31.new_emu()
        for f in STATIC_INIT:
            assert f in init_array(e), "0x%x not an .init_array entry" % f
            e.call(f)
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
        self.bpm = 120.0; self.tempo_calls = 0
        def tempo(em):
            self.tempo_calls += 1
            u = d2u(self.bpm); em.setr(0, u & 0xffffffff); em.setr(1, u >> 32); em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
        e.add_watch(TEMPO_FN, tempo)
        e.add_watch(JUCE_SETPLAY, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        self.s14 = []; self.ev = []; self.idx_of = {}
        def s14(em):
            lr = em.uc.reg_read(emu.LR)
            where = ("defaults" if P["s52"][0] <= lr < P["s52"][1] else "feed" if P["pb"][0] <= lr < P["pb"][1]
                     else "harness" if lr == emu.SENTINEL else "other@0x%x" % lr)
            self.s14.append((where, em.r(0), em.r(1), em.r(2)))
        for a in SLOT14: e.add_watch(a, s14)
        for a, nm in SLOTS.items():
            e.add_watch(a, lambda em, nm=nm: self.ev.append((nm, self.idx_of.get(em.r(0), em.r(0)))))
        tvt = e.malloc(64, "harness: tempo vtable"); e.w32(tvt + 0x1c, TEMPO_FN); self.tob = tob = e.malloc(8, "harness: tempo obj")
        e.w32(tob, tvt)
        self.p = p = e.malloc(P["size"], "new (processor)")
        if which == "insert": e.call(P["ctor"], p, 0, tob, 0)    # Insert ctor (this, +0xa0 owner value, +0x94 tempo, +0x98 Ducker source)
        else: e.call(P["ctor"], p, tob, 0)                        # Master/Send ctor (this, +0x94 tempo) -> 0x1128cc(this, tempo, 0)
        self.arr = e.u32(p + 0x80); self.count = e.u32(p + 0x88)
        self.objs = [e.u32(self.arr + 4 * i) for i in range(self.count)]
        self.idx_of = {o: i for i, o in enumerate(self.objs)}
        self.defaults = {i: [] for i in range(self.count)}
        for where, o, idx, bits in self.s14:
            if where == "defaults": self.defaults[self.idx_of[o]].append((idx, bits))
        self.ctor_other = [x for x in self.s14 if x[0] != "defaults"]
        self.flags_ctor = e.rd(p + 0x9c, 3)
        lo, hi = d2u(44100.0) & 0xffffffff, d2u(44100.0) >> 32
        e.call(P["prep"], p, 0, lo, hi, stack_args=(64,))
        self.ms = e.u32(p + P["ms"]) if P["ms"] else None
        if enable: self.set_disabled(0)
        self.s14 = []; self.ev = []
        self.buf = e.malloc(0x100, "harness: bus buffer"); ch = e.malloc(8); self.Lb = e.malloc(256); self.Rb = e.malloc(256)
        e.w32(ch, self.Lb); e.w32(ch + 4, self.Rb); e.w32(self.buf + 0xc, ch)

    def set_fx_type(self, n): self.e.call(self.P["setfx"], self.p, n & 0xffffffff)
    def set_disabled(self, f): self.e.call(DISABLE, self.p, f)
    def set_bypass(self, f): self.e.call(BYPASS_SET, self.p, f)
    def set_param(self, i, idx, v): self.e.vcall(self.objs[i], 14, idx, f2u(v))

    def block(self, L, R):
        e = self.e; e.set_floats(self.Lb, L); e.set_floats(self.Rb, R)
        e.call(self.P["block"], self.p, self.buf)
        return e.floats(self.Lb, N), e.floats(self.Rb, N)

    def pstate(self):
        e, p = self.e, self.p
        p8c = e.u32(p + 0x8c); p90 = e.u32(p + 0x90)
        s = {"cur": s32(e.u32(p + self.P["cur"])), "pend": s32(e.u32(p + self.P["pend"])), "8c": self.idx_of.get(p8c, None if p8c == 0 else p8c),
             "90": self.idx_of.get(p90, None if p90 == 0 else p90), "9e": e.rd(p + 0x9e, 1)[0], "9d": e.rd(p + 0x9d, 1)[0],
             "9c": e.rd(p + 0x9c, 1)[0]}
        if self.ms:
            m = self.ms
            s["ms"] = (e.rd(m + 4, 1)[0], e.u32(m + 8), e.u32(m + 0xc), e.u32(m + 0x10), e.u32(m + 0x14), e.u32(m + 0x18),
                       e.u32(m + 0x1c))
        return s


# ===================================================================================================================== model side
def model_effect(kind, defaults, hpf, a8=0):
    """Per-effect model at ctor state + the logged slot-52 calls, wrapped as H044 build_generic does (slot-26 laws, slot 27)."""
    keep_dw = lambda mm, after_process: (mm.dry, mm.wet) if mm.dry is not None else (None, None)
    def p5law(mm, after_process):
        v = mm.params[5].get(); return F(F(1.0) - v), v
    proc = "process"
    if kind == "chorus": mm = C.Chorus(); law = lambda mm, after_process: (F(1.0), mm.mix); mode = 0
    elif kind == "flanger": mm = FL.Flanger(); law = lambda mm, after_process: (F(1.0), mm.mix); mode = 0
    elif kind == "peq": mm = MP.PEQ(); law = lambda mm, after_process: (F(0.0), F(1.0)); mode = 0
    elif kind == "mmf": mm = MM.MMF(); law = p5law; mode = 0
    elif kind == "lofi": mm = ML.LoFi(); law = p5law; mode = 0
    elif kind == "distortion": mm = DM.Distortion(); law = keep_dw; mode = 0
    elif kind == "send_compressor":
        mm = H40.Model(send=True); mode = 0; proc = "process_send"
        law = lambda mm, after_process: (mm.update_mix() if not after_process else None) or (mm.dry, mm.wet)
    elif kind == "phaser":
        mm = MPh.Phaser(); mode = 0
        def law(mm, after_process):
            if not after_process: mm.mix = mm.p[5].get(); mm.wet = mm.mix; mm.dry = F(F(1.0) - mm.mix)
            return mm.dry, mm.wet
    elif kind == "send_delay": mm = SD.SendDelay(); law = keep_dw; mode = 1
    elif kind == "insert_delay":
        mm = ID.InsertDelay(); mode = 1
        law = lambda mm, after_process: (mm.update_mix() if not after_process else None) or (mm.dry, mm.wet)
    elif kind == "insert_compressor":
        mm = H40.Model(send=False); mode = 0
        law = lambda mm, after_process: (mm.update_mix() if not after_process else None) or (mm.dry, mm.wet)
    elif kind == "send_reverb":
        mm = SR.SendReverb(); mode = 1
        def law(mm, after_process):
            if not after_process: mm.slot32()
            return mm.eb_dry, mm.eb_wet
    else: raise ValueError(kind)
    for idx, bits in defaults: mm.set_param(idx, u2f(bits))
    s25, s26 = H44._adapt(mm, law, proc)
    m = EB.EffectBase(mode=mode, slot25=s25, slot26=s26, slot27=lambda eb: mm.reset())
    m.slot22(a8); m.set_post_hpf(bool(hpf), 10.0)
    sync_direct(kind, m, mm)
    return m, mm


def sync_direct(kind, eb, mm):
    """Distortion slot 14 0x1164d8 writes EffectBase +0x10/+0x14 itself on index 5 (no slot 26 needed)."""
    if kind == "distortion": eb.dry = mm.dry; eb.wet = mm.wet


class ModelProc:
    def __init__(self, which, x, mutant=None):
        self.which = which
        self.ebs = {}; self.mms = {}; self.kinds = KINDS_INS if which == "insert" else KINDS
        for i, kind in enumerate(self.kinds):
            if kind is None: continue
            hpf = x.e.rd(x.objs[i] + 0xcc, 1)[0]; a8 = x.e.rd(x.objs[i] + 0xa8, 1)[0]
            self.ebs[i], self.mms[i] = model_effect(kind, x.defaults[i], hpf, a8)
        self.bpm = 120.0
        feed = lambda idx, eb, bpm: self.mms[idx].set_param(7, bpm)
        cls = {"master": FP.MasterProcessor, "send": FP.SendProcessor, "insert": FP.InsertProcessorFull}[which]
        if mutant: cls = mutant(cls)
        self.P = cls(self.ebs, tempo=lambda: self.bpm, feed=feed, nine_e=1)
        self.P.set_disabled(0)
        self.P.log = []

    def set_param(self, i, idx, v):
        self.mms[i].set_param(idx, v); sync_direct(self.kinds[i], self.ebs[i], self.mms[i])

    def pstate(self):
        P = self.P
        ix = lambda eb: None if eb is None else next(i for i, e in self.ebs.items() if e is eb)
        s = {"cur": P.cur, "pend": P.pend, "8c": ix(P.p8c), "90": ix(P.p90), "9e": P.nine_e, "9d": P.nine_d,
             "9c": getattr(P, "bypass", 0)}
        if self.which in ("send", "insert"):
            m = P.ms
            s["ms"] = (m.muted, m.N, f2u(m.inv), m.rem & 0xffffffff, f2u(m.step), f2u(m.g), m.state)
        return s


# ===================================================================================================================== signals / cases
def signal(kind, nblk, seed=5):
    n = nblk * N; g = random.Random(seed)
    if kind == "noise": return [F(g.uniform(-0.5, 0.5)) for _ in range(n)], [F(g.uniform(-0.5, 0.5)) for _ in range(n)]
    if kind == "sine":
        return ([F(0.6 * math.sin(2 * math.pi * 440.0 * i / 44100.0)) for i in range(n)],
                [F(0.4 * math.sin(2 * math.pi * 97.0 * i / 44100.0 + 0.3)) for i in range(n)])
    if kind == "impulse":
        L = [F(0.0)] * n; R = [F(0.0)] * n
        for i in range(3, n, 997): L[i] = F(0.9); R[(i + 400) % n] = F(-0.7)
        return L, R
    raise ValueError(kind)


PRE = {"chorus": ((5, 0.7),), "flanger": ((5, 0.7), (4, 0.5)), "peq": ((1, 0.8), (4, 0.2)), "phaser": ((5, 0.6),),
       "send_compressor": ((0, 0.2), (1, 0.8), (4, 0.7)), "send_delay": ((0, 0.02),)}
MID = {k: ((5, 0.4),) for k in KINDS}; MID["peq"] = ((4, 0.6),)
TEMPO_SCHED = {0: 120.0, 70: 97.3, 130: 1500.0, 170: 0.4}


def run_case(spec):
    """spec: name, proc, sig, nblk, ops {block: [op]}; op: ("fx", n) ("dis", f) ("p", index, idx, v) ("bpm", v).
    Returns result dict + output blob. Comparison per block: output bits, processor state, slot 5/6/7/8 + feed events, wrapper
    state of all 10 effects."""
    t0 = time.time()
    x = EmuProc(spec["proc"]); m = ModelProc(spec["proc"], x, mutant=MUTANTS.get(spec.get("mutant")))
    nblk = spec.get("nblk", 200); ops = spec.get("ops", {})
    L, R = signal(spec.get("sig", "noise"), nblk, seed=spec.get("seed", 5))
    res = dict(name=spec["name"], samples=0, exact=0, maxdiff=0.0, pdiff=0, evdiff=0, wdiff=0, first=None, wet_blocks=0)
    blob = b""; trace = []
    for b in range(nblk):
        x.ev = []; x.s14 = []; m.P.log = []
        for op in ops.get(b, []):
            if op[0] == "fx": x.set_fx_type(op[1]); m.P.set_fx_type(op[1])
            elif op[0] == "dis": x.set_disabled(op[1]); m.P.set_disabled(op[1])
            elif op[0] == "p": x.set_param(op[1], op[2], op[3]); m.set_param(op[1], op[2], op[3])
            elif op[0] == "bpm": x.bpm = op[1]; m.bpm = op[1]
            elif op[0] == "byp": x.set_bypass(op[1]); m.P.set_bypass(op[1])
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        oL, oR = x.block(xL, xR)
        mL = list(xL); mR = list(xR); m.P.process_block(mL, mR, N)
        blob += pack(oL) + pack(oR)
        if any(f2u(a_) != f2u(c_) and a_ != 0.0 for a_, c_ in zip(oL + oR, xL + xR)): res["wet_blocks"] += 1
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
        ev_e = [e_ for e_ in x.ev] + [("feed7", x.idx_of[o], f2u(F(u2f(bits)))) for w, o, idx, bits in x.s14 if w == "feed" and idx == 7]
        ev_e += [("feed%d" % idx, x.idx_of[o], bits) for w, o, idx, bits in x.s14 if w == "feed" and idx != 7]
        # slot-14 calls made from inside an effect (e.g. Distortion slot 27 re-applying its stored values) are the effect model's
        # business (its reset()), not processor events; they are not compared here
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
        trace.append(dict(b=b, cur=ps_e["cur"], pend=ps_e["pend"], ev=[str(v) for v in x.ev],
                          feed=[(x.idx_of[o], idx, round(u2f(bits), 6)) for w, o, idx, bits in x.s14 if w == "feed"],
                          rms_in=math.sqrt(sum(v * v for v in xL) / N), rms_out=math.sqrt(sum(v * v for v in oL) / N),
                          eq_in=sum(1 for a_, c_ in zip(oL + oR, xL + xR) if f2u(a_) == f2u(c_)),
                          zero=sum(1 for a_ in oL + oR if a_ == 0.0)))
    res["sha"] = sha(blob)[:16]
    res["ok"] = res["exact"] == res["samples"] and not res["pdiff"] and not res["evdiff"] and not res["wdiff"]
    res["secs"] = round(time.time() - t0, 1)
    if spec.get("keep_trace"): res["trace"] = trace
    return res, blob


def matrix_cases(quick=False):
    cases = []
    sigs = ("noise", "sine", "impulse") if not quick else ("noise",)
    kinds = range(10) if not quick else (0, 1, 2, 6, 7)
    for proc in ("master", "send"):
        for t in kinds:
            kind = KINDS[t]
            for sig in sigs:
                ops = {b: [("bpm", v)] for b, v in TEMPO_SCHED.items()}
                ops[0] = ops[0] + [("p", t, i, v) for i, v in PRE.get(kind, ())] + [("fx", t)]
                ops[100] = [("p", t, i, v) for i, v in MID[kind]]
                cases.append(dict(name="%s_%d_%s_%s" % (proc, t, kind, sig), proc=proc, sig=sig, nblk=200, ops=ops, section="c3m"))
    return cases


SCHED = {
    "S1": {0: [("fx", 2)], 40: [("fx", 0)], 41: [("fx", 1)], 90: [("fx", 7)], 130: [("fx", -1)], 160: [("fx", 6)], 200: [("fx", 9)]},
    "S2": {0: [("fx", 8)], 20: [("fx", 4)], 21: [("fx", 5)], 22: [("fx", 3)], 60: [("fx", -1)], 61: [("fx", 2)], 100: [("fx", 2)],
           120: [("fx", 0)], 180: [("fx", -1)], 182: [("fx", 1)]},
}


def sched_cases(quick=False):
    cases = []
    for proc in ("master", "send"):
        for nm, sc in SCHED.items():
            for sig in (("sine", "noise") if not quick else ("sine",)):
                ops = {b: list(v) for b, v in sc.items()}
                ops.setdefault(0, []).insert(0, ("p", 2, 5, 0.7)); ops[0].insert(0, ("p", 0, 0, 0.02))
                ops.setdefault(70, []).append(("bpm", 133.0))
                cases.append(dict(name="%s_%s_%s" % (proc, nm, sig), proc=proc, sig=sig, nblk=240, ops=ops, section="c3s", keep_trace=True))
    return cases


def disable_cases(quick=False):
    cases = []
    for proc in ("master", "send"):
        for t in ((0, 6, 2, 1) if not quick else (6,)):
            pre = [("p", t, i, v) for i, v in PRE.get(KINDS[t], ())]
            ops = {0: pre + [("fx", t)], 100: [("dis", 1)], 150: [("dis", 0)]}
            cases.append(dict(name="%s_D1_%d_%s" % (proc, t, KINDS[t]), proc=proc, sig="noise", nblk=240, ops=ops, section="c4",
                              keep_trace=True, t=t))
        ops = {0: [("p", 2, 5, 0.7), ("fx", 6)], 50: [("dis", 1)], 70: [("fx", 2)], 110: [("dis", 0)], 150: [("dis", 1)], 152: [("dis", 1)],
               160: [("fx", -1)], 180: [("dis", 0)], 200: [("fx", 0)], 205: [("dis", 1)], 206: [("dis", 0)]}
        cases.append(dict(name="%s_D2_lofi_chorus_off_delay" % proc, proc=proc, sig="sine", nblk=240, ops=ops, section="c4", keep_trace=True))
    return cases


SYNC_PRE = {"send_delay": ((6, 1.0), (0, 0.4)), "chorus": ((6, 1.0), (5, 0.7), (0, 0.5)), "flanger": ((6, 1.0), (5, 0.7), (0, 0.6)),
            "phaser": ((6, 1.0), (5, 0.6), (0, 0.5))}
SYNC_TEMPO = {0: 120.0, 40: 140.0, 80: 60.5, 120: 2000.0, 160: 0.1}


def sync_cases():
    """C5: tempo-synced Delay/Chorus/Flanger/Phaser on Master and Send with tempo changes (feeds must change the output)."""
    cases = []
    for proc in ("master", "send"):
        for t in (0, 2, 3, 9):
            ops = {b: [("bpm", v)] for b, v in SYNC_TEMPO.items()}
            ops[0] = ops[0] + [("p", t, i, v) for i, v in SYNC_PRE[KINDS[t]]] + [("fx", t)]
            cases.append(dict(name="%s_sync_%d_%s" % (proc, t, KINDS[t]), proc=proc, sig="sine", nblk=200, ops=ops, section="c5",
                              keep_trace=True))
    return cases


def insert_cases():
    """C6b (criterion 6): real InsertFxProcessor (real ctor + prepareToPlay) with the bypass byte +0x9c (setter 0x1129b4)."""
    bp = {b: [("bpm", v)] for b, v in TEMPO_SCHED.items()}
    def mk(name, sig, nblk, ops):
        o = {b: list(v) for b, v in bp.items()}
        for b, v in ops.items(): o.setdefault(b, []).extend(v)
        return dict(name=name, proc="insert", sig=sig, nblk=nblk, ops=o, section="c6b", keep_trace=True)
    return [mk("insert_B1_lofi_bypass", "noise", 200, {0: [("fx", 5)], 80: [("byp", 1)], 120: [("byp", 0)], 121: [("byp", 1)],
                                                     123: [("byp", 0)], 160: [("byp", 1)]}),
            mk("insert_B2_delay_comp_bypass_disable", "sine", 220, {0: [("p", 4, 5, 0.5), ("fx", 4)], 50: [("byp", 1)], 60: [("fx", 7)],
                                                                   100: [("byp", 0)], 130: [("dis", 1)], 170: [("dis", 0)],
                                                                   200: [("byp", 1)]}),
            mk("insert_B3_off_bypass_peq", "noise", 120, {10: [("byp", 1)], 40: [("byp", 0)], 60: [("fx", 2)], 80: [("byp", 1)],
                                                        82: [("byp", 0)]}),
            mk("insert_B4_chorus_flanger_phaser_mmf_sync", "sine", 200, {0: [("p", 0, 6, 1.0), ("p", 0, 5, 0.7), ("p", 1, 5, 0.7),
                                                                          ("p", 8, 5, 0.6), ("fx", 0)], 50: [("fx", 1)],
                                                                      100: [("fx", 8)], 150: [("fx", 3)]})]


# ===================================================================================================================== C6 mutants
def _mut_master_no_poll_while_disabled(cls):
    class M(cls):
        def process_block(self, L, R, n=64):
            if self.cur >= 0 and not self.nine_e:
                if self._get(self.cur).slot9() == 0: self._swap()
            self._run(L, R, n)
    return M


def _mut_send_poll_while_disabled(cls):
    class M(cls):
        def process_block(self, L, R, n=64):
            self.ms.set_muted(self.mute_flag()); self.ms.process(L, R, n)
            if self.cur >= 0:
                if self._get(self.cur).slot9() == 0: self._swap()
            self._run(L, R, n)
    return M


def _mut_send_mute_on_current(cls):
    class M(cls):
        def mute_flag(self):
            return 1 if (self.cur == -1 or self.nine_e) else self.nine_d ^ 1
    return M


def _mut_master_input_mute(cls):
    class M(cls):
        def __init__(self, *a, **k):
            super().__init__(*a, **k); self.ms = FP.MuteSmoother(132, 0)
        def process_block(self, L, R, n=64):
            self.ms.set_muted(1 if (self.pend == -1 or self.nine_e) else 0); self.ms.process(L, R, n)
            super().process_block(L, R, n)
    return M


def _mut_no_feed(cls):
    class M(cls):
        def _run(self, L, R, n):
            e = self._get(self.cur)
            if e is not None: e.slot18(L, R, n)
    return M


def _mut_exact_mute_ramp(cls):
    class MS(FP.MuteSmoother):
        def process(self, L, R, n):
            if self.state == 1:
                k0 = self.N - self.rem
                st = self.step
                for k in range(min(n, self.rem)):
                    t = (k0 + k) / self.N
                    g = F(1.0 - t) if self.muted else F(t)
                    L[k] = F(L[k] * g); R[k] = F(R[k] * g)
                rem = self.rem
                if n <= rem:
                    self.rem -= n; self.g = F(1.0 - (k0 + n) / self.N) if self.muted else F((k0 + n) / self.N); return
                for k in range(rem, n):
                    if self.muted: L[k] = 0.0; R[k] = 0.0
                self.state = 2 if self.muted else 0; self.rem = 0; self.g = F(0.0) if self.muted else F(1.0); return
            return FP.MuteSmoother.process(self, L, R, n)
    class M(cls):
        def __init__(self, *a, **k):
            super().__init__(*a, **k); self.ms = MS(132, 0)
    return M


def _mut_bypass_128(cls):
    class M(cls):
        def __init__(self, *a, **k):
            super().__init__(*a, **k); self.ms = FP.MuteSmoother(128, 0)
    return M


def _mut_bypass_hard_switch(cls):
    class M(cls):
        def process_block(self, L, R, n=64):
            dL = list(L); dR = list(R)
            if self.cur >= 0 and self._get(self.cur).slot9() == 0: self._swap()
            self._run(L, R, n)
            if self.bypass: L[:] = dL; R[:] = dR
    return M


MUTANTS = {"bypass_N_128": _mut_bypass_128, "bypass_hard_switch": _mut_bypass_hard_switch,
           "master_no_poll_while_disabled": _mut_master_no_poll_while_disabled,
           "send_poll_while_disabled": _mut_send_poll_while_disabled,
           "send_mute_on_current": _mut_send_mute_on_current,
           "master_input_mute": _mut_master_input_mute,
           "no_tempo_feed": _mut_no_feed,
           "exact_t_over_N_mute_ramp": _mut_exact_mute_ramp}


def mutant_cases():
    D2m = disable_cases()[-1 - 5]; D2s = disable_cases()[-1]
    return [dict(D2m, name="mut_master_no_poll_while_disabled", mutant="master_no_poll_while_disabled", keep_trace=False),
            dict(D2s, name="mut_send_poll_while_disabled", mutant="send_poll_while_disabled", keep_trace=False),
            dict(sched_cases()[4], name="mut_send_mute_on_current", mutant="send_mute_on_current", keep_trace=False),
            dict(sched_cases()[0], name="mut_master_input_mute", mutant="master_input_mute", keep_trace=False),
            dict(matrix_cases()[2 * 3], name="mut_master_no_tempo_feed_chorus", mutant="no_tempo_feed"),
            dict(sched_cases()[4], name="mut_send_exact_t_over_N_mute_ramp", mutant="exact_t_over_N_mute_ramp", keep_trace=False),
            dict(sync_cases()[1], name="mut_master_no_tempo_feed_synced_chorus", mutant="no_tempo_feed", keep_trace=False),
            dict(sync_cases()[4], name="mut_send_no_tempo_feed_synced_delay", mutant="no_tempo_feed", keep_trace=False),
            dict(insert_cases()[0], name="mut_insert_bypass_N_128", mutant="bypass_N_128", keep_trace=False),
            dict(insert_cases()[0], name="mut_insert_bypass_hard_switch", mutant="bypass_hard_switch", keep_trace=False)]


# ===================================================================================================================== C1 / C5 static-ish facts
def ctor_facts():
    out = {}
    for which in ("master", "send", "insert"):
        try:
            x = EmuProc(which, enable=False)
        except Exception as ex:
            out[which] = dict(error="%s: %s" % (type(ex).__name__, ex)); continue
        e = x.e
        objs = [dict(i=i, vptr=hex(e.u32(o)), a8=e.rd(o + 0xa8, 1)[0], hpf_req=e.rd(o + 0xcc, 1)[0], hpf_fc=u2f(e.u32(o + 0xd0)),
                     mode=e.u32(o + 0x98), fs=e.u32(o + 0x90), blk=e.u32(o + 0x94)) for i, o in enumerate(x.objs)]
        d = dict(count=x.count, flags_9c_9d_9e_ctor=list(x.flags_ctor), cur=s32(e.u32(x.p + x.P["cur"])), pend=s32(e.u32(x.p + x.P["pend"])),
                 objs=objs, defaults={i: [(idx, u2f(b)) for idx, b in v] for i, v in x.defaults.items()},
                 ctor_other_s14=[(w, x.idx_of.get(o, hex(o)), idx, u2f(b)) for w, o, idx, b in x.ctor_other])
        if x.ms:
            m = x.ms
            d["mute"] = dict(N=e.u32(m + 8), inv=u2f(e.u32(m + 0xc)), muted=e.rd(m + 4, 1)[0], state=e.u32(m + 0x1c), g=u2f(e.u32(m + 0x18)))
        out[which] = d
    return out


# ===================================================================================================================== main
def _worker(spec):
    try:
        r, blob = run_case(spec)
    except Exception as ex:
        import traceback
        r = dict(name=spec["name"], ok=False, error="%s: %s" % (type(ex).__name__, ex), tb=traceback.format_exc()[-1500:]); blob = b""
    r["section"] = spec.get("section"); r["proc"] = spec.get("proc"); r["mutant"] = spec.get("mutant")
    return r, blob


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H077"))
    ap.add_argument("--jobs", type=int, default=6); ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only", help="comma list of sections c1,c3m,c3s,c4,c5,c6b,c6")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    only = set(a.only.split(",")) if a.only else {"c1", "c3m", "c3s", "c4", "c5", "c6b", "c6"}
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)

    if "c1" in only:
        P("== C1/C5 real processor ctors (Master 0x114bc0, Send 0x11bbe4, Insert 0x118b0c): flags, effects, slot-52 defaults")
        cf = ctor_facts(); J["ctor"] = cf
        for which, d in cf.items():
            if "error" in d: P("  %s ctor: ERROR %s" % (which, d["error"])); continue
            P("  %s: count %d, ctor bytes +0x9c/+0x9d/+0x9e = %s, current %d pending %d%s" % (
                which, d["count"], d["flags_9c_9d_9e_ctor"], d["cur"], d["pend"],
                ", MuteSmoother N %d 1/N %.9g muted %d state %d" % (d["mute"]["N"], d["mute"]["inv"], d["mute"]["muted"], d["mute"]["state"])
                if "mute" in d else ""))
            P("    per index (vptr, +0xa8, HPF req, gate mode): %s" % " ".join(
                "%d:%s/%d/%d/%d" % (o["i"], o["vptr"][2:], o["a8"], o["hpf_req"], o["mode"]) for o in d["objs"]))
            if d["ctor_other_s14"]: P("    slot-14 calls outside slot 52 during ctor: %s" % d["ctor_other_s14"][:12])
        if "error" not in cf.get("master", {}) and "error" not in cf.get("send", {}):
            md, sd = cf["master"]["defaults"], cf["send"]["defaults"]
            P("  slot-52 defaults (index: [(param, value)]), Master vs Send:")
            for i in range(10):
                P("    %d %-15s M %s%s" % (i, KINDS[i], [(p, round(v, 6)) for p, v in md[i]],
                                         "  == Send" if md[i] == sd[i] else "  Send %s" % [(p, round(v, 6)) for p, v in sd[i]]))
            check(all(o["a8"] == 0 for w in ("master", "send") for o in cf[w]["objs"]),
                  "Master/Send ctors leave EffectBase +0xa8 = 0 on all 10 effects (slot 22(e, 0)) -> slot 5's third argument has no effect")
            check([o["hpf_req"] for o in cf["master"]["objs"]] == [0, 0, 1, 1, 0, 1, 1, 0, 1, 1] ==
                  [o["hpf_req"] for o in cf["send"]["objs"]], "post-HPF requested for indices 2,3,5,6,8,9 only (F141)")
            check(cf["master"]["flags_9c_9d_9e_ctor"] == [0, 1, 1] == cf["send"]["flags_9c_9d_9e_ctor"],
                  "ctor bytes +0x9c = 0, +0x9d = 1, +0x9e = 1: both processors start DISABLED until 0x112a08(p, 0)")
            if "mute" in cf["send"]:
                check(cf["send"]["mute"]["N"] == 132 == FP.mute_samples(44100) and cf["send"]["mute"]["state"] == 0,
                      "Send prepareToPlay 0x119bd8 builds the MuteSmoother with N = 132 (= model mute_samples(44100)), unmuted, idle")
            if "error" not in cf.get("insert", {}):
                idf = cf["insert"]["defaults"][0]
                P("  Chorus slot-52 defaults: Insert (index 0) %s | Master (index 2) %s | Send (index 2) %s" % (
                    [(p, round(v, 6)) for p, v in idf], [(p, round(v, 6)) for p, v in md[2]], [(p, round(v, 6)) for p, v in sd[2]]))
                J["chorus_defaults"] = dict(insert=idf, master=md[2], send=sd[2])

    jobs = []
    if "c3m" in only: jobs += matrix_cases(a.quick)
    if "c3s" in only: jobs += sched_cases(a.quick)
    if "c4" in only: jobs += disable_cases(a.quick)
    if "c5" in only: jobs += sync_cases()
    if "c6b" in only: jobs += insert_cases()
    if "c6" in only: jobs += mutant_cases()
    P("\n== running %d cases with %d jobs" % (len(jobs), a.jobs))
    t0 = time.time()
    if a.jobs > 1:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(a.jobs) as pool: results = pool.map(_worker, jobs, chunksize=1)
    else:
        results = [_worker(s) for s in jobs]
    P("  done in %.0f s" % (time.time() - t0))
    blobs = {}
    for sec in ("c3m", "c3s", "c4", "c5", "c6b", "c6"):
        rows = [(r, b) for r, b in results if r.get("section") == sec and not r.get("mutant")]
        mrows = [(r, b) for r, b in results if r.get("mutant")]
        if sec == "c6": rows = mrows
        if not rows: continue
        P("\n== %s" % {"c3m": "C3 type matrix: real processor (ctor-built effects) vs model, 200 blocks, tempo 120/97.3/1500/0.4, mid-run param",
                       "c3s": "C3 FX-change schedules S1/S2 (Off->type, type->type during fade-out, type->Off, no-op re-select)",
                       "c4": "C4 disable 0x112a08 (H056)", "c5": "C5 tempo-synced effects on Master/Send (H037 feed)",
                       "c6b": "C6b Insert bypass +0x9c (0xe8050/0xe8228, H014) with the real Insert ctor",
                       "c6": "C6 alternative models (each must FAIL)"}[sec])
        for r, b in rows:
            if "error" in r: P("  %-40s ERROR %s" % (r["name"], r["error"][:300])); continue
            P("  %-40s %s samples %6d exact %6d maxdiff %.3g p/ev/wr diffs %d/%d/%d wet blocks %3d sha %s (%ss)%s" % (
                r["name"], "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["pdiff"], r["evdiff"], r["wdiff"],
                r["wet_blocks"], r["sha"], r["secs"], "" if r["ok"] or sec == "c6" else "  first %s" % (str(r["first"])[:400],)))
        if sec != "c6":
            blobs[sec] = b"".join(b for _, b in rows)
            open(os.path.join(a.out, "%s_outputs.f32" % sec), "wb").write(blobs[sec])
            nok = sum(1 for r, _ in rows if r.get("ok"))
            P("  %s: %d/%d cases bit-exact, %d samples, outputs sha256 %s" % (sec, nok, len(rows), sum(r.get("samples", 0) for r, _ in rows),
                                                                         sha(blobs[sec])))
            check(nok == len(rows), "%s: every case bit-exact (outputs, processor state incl. MuteSmoother, slot 5/6/7/8 + feed events, "
                                    "wrapper state of all 10 effects, every block)" % sec)
        else:
            check(all(not r.get("ok") for r, _ in rows if "error" not in r) and all("error" not in r for r, _ in rows),
                  "every alternative model is refuted by the real processor")
        J[sec] = [{k: v for k, v in r.items() if k != "trace"} for r, _ in rows]
    # traces of schedule / disable cases
    for r, _ in results:
        if r.get("trace"):
            J.setdefault("traces", {})[r["name"]] = r["trace"]
    # C4 summary (H056)
    if "c4" in only:
        P("\n== C4 summary: per block after disable / re-enable (out == in samples of 128; zero samples; events)")
        for r, _ in results:
            if r.get("section") != "c4" or "trace" not in r: continue
            tr = r["trace"]
            pick = [b for b in range(len(tr)) if tr[b]["ev"] or b in (99, 100, 101, 102, 103, 104, 149, 150, 151, 152, 153, 154)]
            P("  %s:" % r["name"])
            P("    " + "; ".join("b%d cur %d eq_in %d zero %d %s" % (b, tr[b]["cur"], tr[b]["eq_in"], tr[b]["zero"], ",".join(tr[b]["ev"]))
                                for b in pick[:40]))
    J["fails"] = fails
    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h077_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h077.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
