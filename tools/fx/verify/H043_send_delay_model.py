#!/usr/bin/env python3
"""H043 — SendFxDelay (Send/Master "Delay", index 0 of both FX processor arrays; primary vtable 0x841ea8, secondary 0x841eec with
the EffectBase sub-object at +0x238; new 0x6c0, ctor 0x1054ac(obj, 44100, 64); EffectBase slot 25 0x104e90 -> 0x104e98 ->
primary slot 5 0x104a30) end to end: parameters -> formulas -> state layout -> bit-exact own-code model harness/models/send_delay.py
vs the emulated 1.60 slot 25.

Sections (criteria of kb/cycles/021.md):
  C1  parameter list (registrations logged in the real ctor, slot-14 index map, Send 0x11baa8 / Master 0x114ad4 slot-52 defaults,
      per-block tempo feed jump tables, change detection).
  C2  formula sweeps by emulated read-back vs the model (full state after every step).
  C3  layout / constants (ring length, ramps, filters, vptrs); state compared after every block in C4.
  C4  end-to-end matrix: settings x {impulse, sine, noise, silence, L-only, R-only} + mid-run event runs.
  C5  start-up gate, slot 27 reset, slot 10, ring on delay change.
  C6  Send vs Master object.
  C7  alternatives (model mutants that must fail).
Outputs only to --out (default harness/out/H043/). Run: .venv/bin/python -B harness/H043_send_delay_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, SP                                    # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import send_delay as M                                         # noqa: E402
import insert_delay as ID                                      # noqa: E402
from lofi import F                                             # noqa: E402

FS = 44100; N = 64
FRAC_INIT = (0x6cbe0, 0x6ce8c)      # straight-line part of .init_array entry 0x6cb20 (fills the Fraction tables, r4 = 0xf61f18)
SYNC_TABLE = 0xf61f94               # SendFxDelay sync divisions (read by 0x34a498), {u16 num, u16 den} x 8
CTOR, SIZE, VT, VT2, EB = 0x1054ac, 0x6c0, 0x841ea8, 0x841eec, 0x238
SLOT52 = {"send": 0x11baa8, "master": 0x114ad4}
PARAM_OFF = {0: 0x3f0, 1: 0x44c, 2: 0x4a8, 3: 0x504, 4: 0x560, 5: 0x5bc, 6: 0x618, 7: 0x640}
BASE_OFF = {"tL": 0x2c, "tR": 0x88, "gL": 0xe4, "gR": 0x140}
SMOOTH_OFF = {"fbL": 0x1a4, "fbR": 0x1c8, "direct": 0x1ec, "cross": 0x210}


def sha(b): return hashlib.sha256(b).hexdigest()


class EmuSendDelay:
    """SendFxDelay built by its real ctor 0x1054ac(obj, 44100, 64) after the Fraction-table initialiser, then (optionally) the
    processor init as in the Send/Master ctors: EffectBase slot 22 (e, 0), then Send (or Master) slot 52 (container, 0) with a
    stand-in container (+0x80 array whose entry 0 is obj+0x238, +0x88 count 10). Processed by calling EffectBase slot 25."""
    def __init__(self, defaults="send", log_regs=False, watch=None):
        self.e = e = H31.new_emu(); self.regs = []; self.s14 = []
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
        if log_regs:
            def cs(em):
                a_ = em.r(1); b_ = b""
                while len(b_) < 40:
                    c = em.rd(a_ + len(b_), 1)
                    if c == b"\0": break
                    b_ += c
                return b_.decode()
            def lin(em):
                sp = em.uc.reg_read(SP); st = [em.u32(sp + 4 * k) for k in range(2)]
                self.regs.append({"kind": "LinearParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": u2f(em.r(3)), "max": u2f(st[0]), "default": u2f(st[1])})
            def tog(em):
                self.regs.append({"kind": "ToggleParameter", "off": em.r(0) - self.o, "name": cs(em), "id": em.r(2),
                                  "min": None, "max": None, "default": None})
            e.add_watch(0xf1850, lin); e.add_watch(0xf1800, tog)
        for a_, cb in (watch or {}).items(): e.add_watch(a_, cb)
        e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), em.r(2))))
        # 0x4f782c = assert/log printf used by the out-of-range branch of the sync table reader 0x34a498 (logging only; the reader
        # then uses index 6): skipped, because vsprintf is not loaded
        e.add_watch(0x4f782c, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        self.o = e.malloc(SIZE, "new (harness: SendFxDelay)")
        r0, _ = e.call(CTOR, self.o, FS, N)
        assert r0 == self.o and e.u32(self.o) == VT and e.u32(self.o + EB) == VT2
        self.eb = self.o + EB
        self.defaults_s14 = []
        if defaults:
            e.vcall(self.eb, 22, 0)
            cont = e.malloc(0x100, "harness: FX processor stand-in (+0x80 array, +0x88 count)"); arr = e.malloc(40)
            for i in range(10): e.w32(arr + 4 * i, self.eb if i == 0 else 0)
            e.w32(cont + 0x80, arr); e.w32(cont + 0x88, 10)
            self.s14 = []
            e.call(SLOT52[defaults], cont, 0)
            self.defaults_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.eb, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.eb, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    # --- field access ------------------------------------------------------------------------------------------------------
    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]
    def b(self, a): return self.e.rd(a, 1)[0]

    def state(self):
        o = self.o; u, i, b, d = self.u, self.i, self.b, self.d
        s = {"dry+0x6a4": u(o + 0x6a4), "wet+0x6a8": u(o + 0x6a8), "eb.dry+0x10": u(o + EB + 0x10), "eb.wet+0x14": u(o + EB + 0x14),
             "sync+0x6ac": b(o + 0x6ac), "bpm+0x6b0": u(o + 0x6b0), "time+0x6b4": u(o + 0x6b4), "dirty+0x6b8": b(o + 0x6b8)}
        for k_, off in PARAM_OFF.items():
            if k_ == 6: s["p6.last/cur"] = [b(o + off + 0x24), b(o + off + 0x25)]
            else: s["p%d.last/cur" % k_] = [u(o + off + 0x24), u(o + off + 0x28)]
        for k_, off in BASE_OFF.items(): s["bp.%s" % k_] = [u(o + off + 0x24), u(o + off + 0x28)]
        for nm, off in (("mL", 0x19c), ("mR", 0x1a0)):
            m = u(o + off); g = m + 0x50; ring = u(m + 0x1c)
            s.update({nm + ".ms": u(m + 0x20), nm + ".D": i(m + 0x24), nm + ".pend": b(m + 0x28), nm + ".pms": u(m + 0x2c),
                      nm + ".pD": i(m + 0x30), nm + ".warm": b(m + 0x7c), nm + ".full": b(m + 0x7d), nm + ".cnt": i(m + 0x80),
                      nm + ".g": [i(g + 4), u(g + 8), u(g + 0xc), u(g + 0x10), i(g + 0x14)],
                      nm + ".r.w": i(ring + 0x1c), nm + ".r.pos": d(ring + 0x28)})
        for nm, off in SMOOTH_OFF.items():
            sm = o + off; s[nm] = [i(sm + 4), u(sm + 8), u(sm + 0xc), u(sm + 0x10), i(sm + 0x14)]
        for nm, off in (("hc", 0x69c), ("lc", 0x6a0)):
            c = u(o + off); fl = u(c); st = u(fl + 0x10)
            s.update({nm + ".tgtcut": d(c + 0x18), nm + ".cut": d(c + 0x20), nm + ".cur": u(c + 0x28), nm + ".tgt": u(c + 0x2c),
                      nm + ".acc": u(c + 0x30), nm + ".flag": b(c + 0x40), nm + ".fc": u(fl + 0xc),
                      nm + ".coef": [u(fl + 0x28), u(fl + 0x2c), u(fl + 0x34), u(fl + 0x24)],
                      nm + ".st": [u(st), u(st + 4), u(st + 8), u(st + 12)]})
        return s

    def rings(self):
        out = []
        for off in (0x19c, 0x1a0):
            ring = self.u(self.u(self.o + off) + 0x1c)
            n = self.u(ring + 4); raw = self.e.rd(self.u(ring + 0x18), 8 * n)
            out.append((n, raw))
        return out


def model_state(m):
    fb = f2u
    s = {"dry+0x6a4": fb(m.dry), "wet+0x6a8": fb(m.wet), "eb.dry+0x10": fb(m.dry), "eb.wet+0x14": fb(m.wet),
         "sync+0x6ac": m.sync_v, "bpm+0x6b0": fb(m.bpm_v), "time+0x6b4": fb(m.time_v), "dirty+0x6b8": m.dirty}
    for k_ in PARAM_OFF:
        p = m.p[k_]
        s["p%d.last/cur" % k_] = [p.last, p.cur] if k_ == 6 else [fb(p.last), fb(p.cur)]
    for k_ in BASE_OFF: s["bp.%s" % k_] = [fb(m.bp[k_].last), fb(m.bp[k_].cur)]
    for nm, mod in (("mL", m.modL), ("mR", m.modR)):
        g = mod.gate.r
        s.update({nm + ".ms": fb(mod.ms), nm + ".D": mod.D, nm + ".pend": mod.pend, nm + ".pms": fb(mod.pms), nm + ".pD": mod.pD,
                  nm + ".warm": mod.warm, nm + ".full": mod.full, nm + ".cnt": mod.cnt,
                  nm + ".g": [g.state, fb(g.cur), fb(g.target), fb(g.inc), g.rem],
                  nm + ".r.w": mod.ring.w, nm + ".r.pos": mod.ring.pos})
    for nm in SMOOTH_OFF:
        sm = getattr(m, nm); s[nm] = [sm.state, fb(sm.cur), fb(sm.target), fb(sm.inc), sm.rem]
    for nm, h in (("hc", m.hicut), ("lc", m.lowcut)):
        s.update({nm + ".tgtcut": h.tgt_cut, nm + ".cut": h.cut, nm + ".cur": h.cur, nm + ".tgt": h.tgt, nm + ".acc": fb(h.acc),
                  nm + ".flag": h.flag, nm + ".fc": fb(h.fc), nm + ".coef": [fb(h.b0), fb(h.b1), fb(h.a1), fb(h.k)],
                  nm + ".st": [fb(h.v1[0]), fb(h.v1[1]), fb(h.y1[0]), fb(h.y1[1])]})
    return s


def model_rings(m):
    out = []
    for mod in (m.modL, m.modR):
        r = mod.ring
        out.append((r.L, b"".join(struct.pack("<ff", r.buf[0][k], 0.0) for k in range(r.L))))
    return out


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults="send", mut=None):
    x = EmuSendDelay(defaults=defaults)
    m = M.SendDelay()
    if defaults: m.defaults(master=(defaults == "master"))
    if mut: mut(m)
    return x, m


def signal(kind, nblk, seed=11):
    n = nblk * N; rnd = random.Random(seed)
    if kind == "impulse":        # impulse train: one every 9973 samples (L) / 15013 samples (R, half height)
        L = [F(1.0) if k % 9973 == 0 else F(0.0) for k in range(n)]
        R = [F(0.5) if k % 15013 == 7 else F(0.0) for k in range(n)]
    elif kind == "sine":
        L = [F(0.5 * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(n)]
        R = [F(0.3 * math.sin(2 * math.pi * 3500.0 * k / FS + 1.0)) for k in range(n)]
    elif kind == "noise":
        L = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
        R = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
    elif kind == "Lonly":        # bursts on L only (R silent)
        L = [F(rnd.uniform(-0.8, 0.8)) if (k % 20000) < 300 else F(0.0) for k in range(n)]
        R = [F(0.0)] * n
    elif kind == "Ronly":
        L = [F(0.0)] * n
        R = [F(rnd.uniform(-0.8, 0.8)) if (k % 20000) < 300 else F(0.0) for k in range(n)]
    else:
        L = [F(0.0)] * n; R = [F(0.0)] * n
    return L, R


def run_case(name, pre, bpm, events, kind, nblk, mut=None, keep=False, check_state=True, emu_obj=None, defaults="send",
             state_every=1):
    x, m = new_pair(defaults=defaults, mut=mut) if emu_obj is None else emu_obj
    L, R = signal(kind, nblk)
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    cur_bpm = bpm; maxerr = 0.0; nbit = 0; first_state = None; outb = bytearray(); nonzero = 0
    for blk in range(nblk):
        for op in events.get(blk, []):
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "bpm": cur_bpm = op[1]
            elif op[0] == "reset": x.e.vcall(x.eb, 27); m.reset()
            elif op[0] == "base":                                           # direct LinearParameter setValue 0xf0874 (not slot 14)
                x.e.call(0xf0874, x.o + BASE_OFF[op[1]], f2u(op[2])); m.bp[op[1]].set(op[2])
        x.set(7, cur_bpm); m.set_param(7, cur_bpm)                          # processBlock tempo feed (index 0 is fed)
        bL, bR = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
        eL, eR = x.process(bL, bR)
        mL, mR = m.process(bL, bR)
        for a_, b_ in zip(eL + eR, mL + mR):
            if f2u(a_) != f2u(b_):
                nbit += 1
                if not (math.isnan(a_) and math.isnan(b_)): maxerr = max(maxerr, abs(a_ - b_))
            if a_ != 0.0: nonzero += 1
        outb += struct.pack("<%df" % (2 * N), *(eL + eR))
        if check_state and first_state is None and (blk % state_every == 0 or blk == nblk - 1):
            dd = diff(x.state(), model_state(m))
            if dd: first_state = (blk, dd[:6])
    ring_eq = x.rings() == model_rings(m)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 2 * N * nblk, "mismatched_samples": nbit, "max_abs_err": maxerr,
           "nonzero_out": nonzero, "first_state_diff": first_state, "final_ring_equal": ring_eq,
           "ms_log": [float(v) for v in m.ms_log][:12]}
    return (res, bytes(outb), (x, m)) if keep else (res, bytes(outb))


# ------------------------------------------------------------------------------------------------------------------------
# C4 matrix: settings (name, [(idx, v)] after the slot-52 defaults, bpm fed every block, blocks, defaults kind)
def ms_v(ms): return F((ms - 10.0) / 3990.0)


SETTINGS = [
    ("send_defaults_500ms_fb.7", [], 120.0, 1100, "send"),
    ("max_4000ms_fb1", [(0, 1.0), (1, 1.0)], 120.0, 5800, "send"),
    ("min_10ms_fb.5_hicut.5_lowcut.3", [(0, 0.0), (1, 0.5), (2, 0.5), (3, 0.3)], 120.0, 200, "send"),
    ("pingpong_spread1_300ms_fb.8", [(0, ms_v(300.0)), (1, 0.8), (4, 1.0)], 120.0, 1000, "send"),
    ("spread.5_fb.955_hicut0_lowcut1", [(0, 0.05), (1, 0.955), (2, 0.0), (3, 1.0), (4, 0.5)], 120.0, 600, "send"),
    ("sync120_quarter_fb.6_spread.25", [(6, 1.0), (0, F(1 / 7)), (1, 0.6), (4, 0.25), (2, 0.8)], 120.0, 700, "send"),
    ("sync87.5_8beats_clamp4000", [(6, 1.0), (0, 1.0), (1, 0.4)], 87.5, 5800, "send"),
    ("sync999_eighth_clamp10ms", [(6, 1.0), (0, 0.0), (1, 0.8), (3, 0.6)], 999.0, 200, "send"),
    ("sync133.37_3/4_fb.99_mix.6", [(6, 1.0), (0, F(3 / 7)), (1, 0.99), (5, 0.6), (2, 0.4)], 133.37, 900, "send"),
    ("free_.1234_fb1_spread.75_lowcut.8", [(0, 0.1234), (1, 1.0), (4, 0.75), (3, 0.8)], 120.0, 1000, "send"),
    ("fb1.2_unclamped_10ms", [(0, 0.0), (1, 1.2)], 120.0, 400, "send"),
    ("master_defaults_mix.5", [], 120.0, 1100, "master"),
]
SIGNALS = ("impulse", "sine", "noise", "silence", "Lonly", "Ronly")
# mid-run events: {block: [ops]}, op = ("p", idx, v) | ("bpm", v) | ("reset",) | ("base", key, v)
EVENTS = [
    ("time_changes_free", [(0, 0.05), (1, 0.6), (4, 0.3)], 120.0, 900,
     {150: [("p", 0, 0.01)], 260: [("p", 0, 0.3)], 400: [("p", 0, 0.1)], 401: [("p", 0, 0.02)], 403: [("p", 0, 0.6)],
      700: [("p", 0, 0.0)]}),
    ("bpm_changes_sync", [(6, 1.0), (0, F(4 / 7)), (1, 0.7), (4, 0.5)], 120.0, 900,
     {150: [("bpm", 140.0)], 300: [("bpm", 60.0)], 301: [("bpm", 140.0)], 450: [("bpm", 999.0)], 520: [("bpm", 1.0)],
      600: [("bpm", 133.37)]}),
    ("fb_spread_filter_mix_sync_changes", [(0, 0.02), (1, 0.5)], 120.0, 700,
     {100: [("p", 2, 0.0)], 130: [("p", 2, 0.7), ("p", 1, 0.9)], 200: [("p", 5, 0.5)], 230: [("p", 4, 1.0)], 250: [("p", 6, 1.0)],
      251: [("p", 0, 0.3)], 320: [("p", 6, 0.0)], 330: [("p", 1, 0.0)], 360: [("p", 3, 0.9)],
      400: [("p", 2, 0.33), ("p", 1, 1.0), ("p", 4, 0.0)], 500: [("p", 3, 0.0)], 600: [("p", 4, 0.6)]}),
    ("reset_and_restart", [(0, 0.03), (1, 0.8), (4, 0.4)], 120.0, 600,
     {120: [("reset",)], 121: [("p", 0, 0.01)], 300: [("p", 0, 0.05), ("reset",)], 301: [("p", 3, 1.0), ("p", 2, 0.2)]}),
    # DelayTimeLch/Rch written directly (not reachable through slot 14): shows the base supports different L/R times
    ("base_LR_times_direct", [(0, 0.05), (1, 0.7)], 120.0, 700,
     {1: [("base", "tL", 150.0), ("base", "tR", 333.0)], 400: [("base", "gR", 0.2)], 500: [("p", 0, 0.08)]}),
]
EVENT_SIGNALS = ("impulse", "noise", "sine", "Lonly")


def matrix_jobs():
    jobs = []
    for nm, pre, bpm, nb, dfl in SETTINGS:
        for sig in SIGNALS: jobs.append(("setting", nm, pre, bpm, {}, sig, nb, dfl, None))
    for nm, pre, bpm, nb, ev in EVENTS:
        for sig in EVENT_SIGNALS: jobs.append(("event", nm, pre, bpm, ev, sig, nb, "send", None))
    return jobs


def mutant_jobs():
    jobs = []
    for nm_, fn_, case, sig in MUTANTS:
        c_ = find_case(case); jobs.append((c_[0], c_[1], c_[2], c_[3], c_[4], sig, c_[5], c_[6], nm_))
    return jobs


def run_parallel(kind, nworkers, wdir):
    """Run matrix_jobs()/mutant_jobs() in nworkers subprocesses of this script (no multiprocessing semaphores: the sandbox
    forbids sysconf(SC_SEM_NSEMS_MAX)); worker k runs jobs i with i % nworkers == k and pickles its results."""
    import subprocess, pickle
    os.makedirs(wdir, exist_ok=True)
    procs = [subprocess.Popen([sys.executable, "-B", os.path.abspath(__file__), "--worker", "%s:%d:%d" % (kind, k, nworkers),
                               "--out", wdir], stdout=open(os.path.join(wdir, "w%s%d.log" % (kind, k)), "w"),
                              stderr=subprocess.STDOUT) for k in range(nworkers)]
    for p_ in procs:
        if p_.wait() != 0: raise RuntimeError("worker failed, see %s" % wdir)
    jobs = matrix_jobs() if kind == "matrix" else mutant_jobs()
    res = [None] * len(jobs)
    for k in range(nworkers):
        for i, r in pickle.load(open(os.path.join(wdir, "w%s%d.pkl" % (kind, k)), "rb")): res[i] = r
    return jobs, res


def worker(spec, wdir):
    import pickle
    kind, k, nw = spec.split(":"); k = int(k); nw = int(nw)
    jobs = matrix_jobs() if kind == "matrix" else mutant_jobs()
    out = [(i, _job(jb)) for i, jb in enumerate(jobs) if i % nw == k]
    pickle.dump(out, open(os.path.join(wdir, "w%s%d.pkl" % (kind, k)), "wb"))
    return 0


def _job(args):
    kind_, name, pre, bpm, ev, sig, nb, dfl, mutname = args
    mut = dict((n_, f_) for n_, f_, _, _ in MUTANTS).get(mutname) if mutname else None
    return run_case(name, pre, bpm, ev, sig, nb, mut=mut, defaults=dfl)


# ------------------------------------------------------------------------------------------------------------------------
# C7 model mutants (alternatives; each must be caught by its target run)
def mut_independent_lr(m):                     # (a) no cross-feed: Spread ignored (direct 1, cross 0)
    orig = m.apply_base
    def ab(m=m, orig=orig):
        orig(); m.direct.set_now(F(1.0)); m.cross.set_now(F(0.0))
    m.apply_base = ab


def mut_cross_in_feedback_only(m):             # (a') ping-pong only inside the loop: output = filtered yL/yR, feedback cross-mixed
    def core(L, R, m=m):
        m.apply_base()
        n = len(L); oL = list(L); oR = list(R); pos = 0
        while n - pos > 0:
            c = min(m.modL.chunk(), n - pos)
            yL = m.modL.read1(c); yR = m.modR.read1(c)
            m.hicut.process(yL, yR, c); m.lowcut.process(yL, yR, c)
            s5, s4 = M.smooth_mul(m.cross, yL, yR, c); s0, s1 = M.smooth_mul(m.direct, yL, yR, c)
            M.ftz_list_add(s0, s4, c); M.ftz_list_add(s1, s5, c)
            s2, _ = M.smooth_mul(m.fbL, s0, None, c); s3, _ = M.smooth_mul(m.fbR, s1, None, c)
            M.ftz_list_add(s2, L[pos:pos + c], c); M.ftz_list_add(s3, R[pos:pos + c], c)
            oL[pos:pos + c] = yL; oR[pos:pos + c] = yR
            m.modL.write1(s2, c); m.modR.write1(s3, c); pos += c
        return oL, oR
    m.core = core


def mut_filters_outside_loop(m):               # (b) feedback taken before the filters; filters only on the output
    def core(L, R, m=m):
        m.apply_base()
        n = len(L); oL = list(L); oR = list(R); pos = 0
        while n - pos > 0:
            c = min(m.modL.chunk(), n - pos)
            s0 = m.modL.read1(c); s1 = m.modR.read1(c)
            s5, s4 = M.smooth_mul(m.cross, s0, s1, c); s0, s1 = M.smooth_mul(m.direct, s0, s1, c)
            M.ftz_list_add(s0, s4, c); M.ftz_list_add(s1, s5, c)
            s2, _ = M.smooth_mul(m.fbL, s0, None, c); s3, _ = M.smooth_mul(m.fbR, s1, None, c)
            m.hicut.process(s0, s1, c); m.lowcut.process(s0, s1, c)
            M.ftz_list_add(s2, L[pos:pos + c], c); M.ftz_list_add(s3, R[pos:pos + c], c)
            oL[pos:pos + c] = s0; oR[pos:pos + c] = s1
            m.modL.write1(s2, c); m.modR.write1(s3, c); pos += c
        return oL, oR
    m.core = core


def mut_swap_hicut_lowcut(m):                  # (b') the HiCut knob drives the HPF container and LowCut the LPF container
    orig = m.apply_params
    def ap(m=m, orig=orig):
        orig()
        m.hicut.set_step(m.lowcut_step(m.p[3].get())); m.lowcut.set_step(m.hicut_step(m.p[2].get()))
    m.apply_params = ap


def mut_fractional_read(m):                    # (c) interpolated (fractional-sample) delay instead of integer samples
    for mod in (m.modL, m.modR):
        r = mod.ring; orig = r.set_delay
        def sd(d, mod=mod, orig=orig):
            exact = float(mod.ms) * 0.001 * 44100.0
            orig(F(float(d) + (exact - math.floor(exact))))
        r.set_delay = sd


def mut_quantised_feedback(m):                 # Insert-style feedback rint(100v)/100
    orig = m.apply_params
    def ap(m=m, orig=orig):
        orig(); g = ID.InsertDelay.feedback(m.p[1].get()); m.bp["gL"].set(g); m.bp["gR"].set(g)
    m.apply_params = ap


def mut_glide_time(m):                         # delay change jumps immediately (no gate fade-out / fade-in)
    for mod in (m.modL, m.modR):
        def set_delay(ms, glide=1, mod=mod):
            x = F(min(max(F(ms), F(0.0)), mod.maxms))
            if M.near(x, mod.ms): return
            mod.ms = x; mod.D = mod.samples(x); mod.pms = x; mod.pD = mod.D
            mod.ring.set_delay(F(float(mod.D)))
        mod.set_delay = set_delay


def mut_separate_free_time(m):                 # Rch gets its own (e.g. 1.5x) time: refuted by the single shared write
    orig = m.apply_params
    def ap(m=m, orig=orig):
        d = m.dirty or m.p[0].last != m.p[0].cur
        orig()
        if d and m.ms_log: m.bp["tR"].set(F(min(F(4000.0), F(m.ms_log[-1] * F(1.5)))))
    m.apply_params = ap


MUTANTS = [
    ("(a) independent L/R feedback, Spread ignored", mut_independent_lr, "pingpong_spread1_300ms_fb.8", "Lonly"),
    ("(a') cross-feed only inside the loop", mut_cross_in_feedback_only, "pingpong_spread1_300ms_fb.8", "Lonly"),
    ("(b) filters outside the feedback loop", mut_filters_outside_loop, "spread.5_fb.955_hicut0_lowcut1", "noise"),
    ("(b') HiCut/LowCut roles swapped", mut_swap_hicut_lowcut, "min_10ms_fb.5_hicut.5_lowcut.3", "noise"),
    ("(c) fractional (interpolated) delay", mut_fractional_read, "sync133.37_3/4_fb.99_mix.6", "noise"),
    ("Insert-style quantised feedback", mut_quantised_feedback, "spread.5_fb.955_hicut0_lowcut1", "noise"),
    ("delay change jumps without fade", mut_glide_time, "time_changes_free", "noise"),
    ("separate L/R free times (R = 1.5 L)", mut_separate_free_time, "time_changes_free", "noise"),
]


def find_case(name):
    for s in SETTINGS:
        if s[0] == name: return ("setting", s[0], s[1], s[2], {}, s[3], s[4])
    for s in EVENTS:
        if s[0] == name: return ("event", s[0], s[1], s[2], s[4], s[3], "send")
    raise KeyError(name)


# ------------------------------------------------------------------------------------------------------------------------
# C6 processor rigs: stand-in Send/Master processors around a real SendFxDelay, run through the REAL processBlock
TEMPO_FN = emu.SENTINEL + 0x240
PROC = {"send": {"block": 0x119994, "vt": 0x842d40}, "master": {"block": 0x112acc, "vt": 0x842aa8}}


class ProcRig:
    def __init__(self, which, pre=(), bpm=120.0):
        self.which = which
        self.x = x = EmuSendDelay(defaults=which); e = self.e = x.e
        for idx, v in pre: x.set(idx, v)
        self.bpm = bpm; self.resets = 0; self.s14 = []; self.cap = {}
        for a_ in (0xe8050, 0xe808c): e.add_watch(a_, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        def tempo(em):
            u = emu.d2u(self.bpm); em.setr(0, u & 0xffffffff); em.setr(1, u >> 32)
            em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
        e.add_watch(TEMPO_FN, tempo)
        e.add_watch(0x104a04, lambda em: setattr(self, "resets", self.resets + 1))
        # slot-14 calls are logged by EmuSendDelay's own watch on 0x105d24 (x.s14); a second add_watch on the same address would
        # register a second hook that runs the (replaced) callback twice
        tvt = e.malloc(64); e.w32(tvt + 0x1c, TEMPO_FN); tob = e.malloc(8); e.w32(tob, tvt)
        self.proc = p = e.malloc(0x148); arr = e.malloc(40)
        for k in range(10): e.w32(arr + 4 * k, x.eb if k == 0 else 0)
        e.w32(p, PROC[which]["vt"]); e.w32(p + 0x80, arr); e.w32(p + 0x84, 10); e.w32(p + 0x88, 10); e.w32(p + 0x94, tob)
        e.wr(p + 0x9c, b"\x00\x01\x00\x00"); e.w32(p + 0xa0, 0); e.w32(p + 0xa4, 0); e.w32(p + 0xa8, e.malloc(0x40))
        self.buf = e.malloc(0x100); ch = e.malloc(8); self.Lb = e.malloc(256); self.Rb = e.malloc(256)
        e.w32(ch, self.Lb); e.w32(ch + 4, self.Rb); e.w32(self.buf + 0xc, ch)
        e.add_watch(0x106ecc, lambda em: self.cap.__setitem__("in", (em.r(1), em.r(2), em.r(3), em.floats(em.r(1), em.r(3)),
                                                                     em.floats(em.r(2), em.r(3)))))
        e.add_watch(0x106ed0, lambda em: self.cap.__setitem__("out", (em.floats(self.cap["in"][0], self.cap["in"][2]),
                                                                      em.floats(self.cap["in"][1], self.cap["in"][2]))))

    def block(self, L, R):
        e = self.e; self.cap = {}; self.x.s14 = []; r0 = self.resets
        e.set_floats(self.Lb, L); e.set_floats(self.Rb, R)
        e.call(PROC[self.which]["block"], self.proc, self.buf)
        return (e.floats(self.Lb, N), e.floats(self.Rb, N)), self.resets - r0, list(self.x.s14)


# ------------------------------------------------------------------------------------------------------------------------
# kb records the report hash as "4863e9d3a281bf40…cbf0f": the first 16 hex digits match, the 5-digit suffix is a transcription slip
# (the file hash ends …cfbf0f); the full 16-digit prefix is checked here
REGRESS_H055 = {"h055_report.txt": ("4863e9d3a281bf40", "cfbf0f"), "h055.json": ("e1b2d811", "57921")}
REGRESS_H055_F32 = ("29998cdd", "18c1b")
REGRESS_H055_R = ("711de066", "dcac")


def regress(out):
    """Re-run H055 (its recorded hashes) and H055 --regress (H010 + H010 --regress = H009 + H021..H041)."""
    import subprocess, glob
    d = os.path.join(out, "regress", "H055"); os.makedirs(d, exist_ok=True)
    d2 = os.path.join(out, "regress", "H055r"); os.makedirs(d2, exist_ok=True)
    p1 = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "H055_device_out.py"), "--out", d],
                          stdout=open(os.path.join(out, "regress", "H055.log"), "w"), stderr=subprocess.STDOUT)
    p2 = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "H055_device_out.py"), "--regress", "--out", d2],
                          stdout=open(os.path.join(out, "regress", "H055r.log"), "w"), stderr=subprocess.STDOUT)
    rc1 = p1.wait(); rc2 = p2.wait()
    got = {k: sha(open(os.path.join(d, k), "rb").read()) for k in REGRESS_H055 if os.path.exists(os.path.join(d, k))}
    f32s = sha(b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(d, "*.f32")))))
    ok1 = rc1 == 0 and all(got.get(k, "").startswith(v[0]) and got.get(k, "").endswith(v[1]) for k, v in REGRESS_H055.items()) and \
        f32s.startswith(REGRESS_H055_F32[0]) and f32s.endswith(REGRESS_H055_F32[1])
    rp = os.path.join(d2, "h055_regress.txt"); rtxt = open(rp).read() if os.path.exists(rp) else ""
    rs = sha(rtxt.encode())
    ok2 = rc2 == 0 and rs.startswith(REGRESS_H055_R[0]) and rs.endswith(REGRESS_H055_R[1])
    txt = ("H055 rc %d %s report %s json %s f32 %s\nH055 --regress rc %d %s h055_regress.txt %s…%s\n--- h055_regress.txt:\n%s"
           "REGRESSION: %s\n" % (rc1, "OK " if ok1 else "BAD", got.get("h055_report.txt", "-")[:8], got.get("h055.json", "-")[:8],
                                 f32s[:8], rc2, "OK " if ok2 else "BAD", rs[:8], rs[-4:], rtxt,
                                 "all recorded hashes reproduced" if ok1 and ok2 else "MISMATCH"))
    open(os.path.join(out, "h043_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok1 and ok2 else 1


# ------------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H043"))
    ap.add_argument("--skip-matrix", action="store_true"); ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--regress", action="store_true", help="only re-run H055 (+ its regress chain) and compare the recorded hashes")
    ap.add_argument("--worker", help=argparse.SUPPRESS)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.worker: return worker(a.worker, a.out)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)
    def fl(u): return u2f(u) if isinstance(u, int) else u
    P("H043 SendFxDelay end-to-end — target sha256 %s" % emu.SHA)
    im = sp16img.Image()

    # ---------------------------------------------------------------------------------------------------------- C1
    P("\n== C1 parameters")
    x = EmuSendDelay(defaults=None, log_regs=True)
    for r_ in x.regs:
        P("  reg %-15s off +0x%03x id %d %-16s min %s max %s default %s" % (r_["kind"], r_["off"], r_["id"], r_["name"], r_["min"],
                                                                         r_["max"], r_["default"]))
    J["registrations"] = x.regs
    check([(r_["name"], r_["id"], r_["off"], r_["min"], r_["max"], r_["default"]) for r_ in x.regs] ==
          [("DelayTimeLch", 0, 0x2c, 1.0, 4000.0, 1.0), ("DelayTimeRch", 1, 0x88, 1.0, 4000.0, 1.0),
           ("FeedbackGainLch", 2, 0xe4, 0.0, 1.0, 0.0), ("FeedbackGainRch", 3, 0x140, 0.0, 1.0, 0.0),
           ("DelayTime", 0, 0x3f0, 0.0, 1.0, 0.5), ("Feedback", 1, 0x44c, 0.0, 1.0, 0.0), ("HiCut", 2, 0x4a8, 0.0, 1.0, 1.0),
           ("LowCut", 3, 0x504, 0.0, 1.0, 0.0), ("Spread", 4, 0x560, 0.0, 1.0, 0.0), ("Mixratio", 5, 0x5bc, 0.0, 1.0, 0.0),
           ("SYNC", 6, 0x618, None, None, None), ("BPM", 7, 0x640, 1.0, 999.0, 120.0)],
          "ctor 0x1054ac registers 4 DelayEchoBase LinearParameters (DelayTimeLch/Rch 1..4000 ms, FeedbackGainLch/Rch 0..1) and 8 "
          "SendFxDelay parameters at +0x3f0 + 0x5c*i (SYNC = ToggleParameter +0x618, BPM 1..999 +0x640)")
    imap = {}
    for idx in range(10):
        xx = EmuSendDelay(defaults=None); s0 = xx.state()
        ret = xx.set(idx, 0.37); s1 = xx.state()
        imm = sorted(k_ for k_ in s1 if s1[k_] != s0[k_])
        xx.process([0.0] * N, [0.0] * N); s2 = xx.state()
        xb = EmuSendDelay(defaults=None); xb.process([0.0] * N, [0.0] * N); s2b = xb.state()      # same block without the set
        later = sorted(k_ for k_ in s2 if s2[k_] != s2b[k_] and k_ not in imm)
        imap[idx] = {"ret": ret, "changed_immediately": imm, "differs_after_next_slot25": later}
        P("  slot14(%d, 0.37) -> ret %d, immediate %s, after next slot 25 (vs no set) %s" % (idx, ret, imm, later[:9]))
    J["slot14_map"] = imap
    xt6 = EmuSendDelay(defaults=None); r6 = (xt6.set(6, 1.0), xt6.set(6, 0.0), xt6.set(6, 0.999))
    check(all(imap[i]["ret"] == 0 for i in (0, 1, 2, 3, 4, 5, 7)) and imap[8]["ret"] == 3 and imap[9]["ret"] == 3 and
          all(imap[i]["changed_immediately"] == ["p%d.last/cur" % i] for i in (0, 1, 2, 3, 4, 5, 7)) and
          imap[6]["ret"] == 3 and imap[6]["changed_immediately"] == [] and r6 == (0, 0, 3),
          "slot 14 (EffectBase 0x105d24) only stores (0..5, 7 return 0; >= 8 return 3; SYNC accepts only v >= 1 / v <= 0, else 3)")
    check(all(len(imap[i]["differs_after_next_slot25"]) > 0 for i in (0, 1, 2, 3, 4, 5, 7)),
          "every index 0..5 and 7 reaches DSP state at the next slot 25 (LowCut and Spread are live, unlike InsertFxDelay)")
    for d in ("send", "master"):
        xd = EmuSendDelay(defaults=d)
        J["defaults_" + d] = [(i_, "0x%08x" % b_, u2f(b_)) for i_, b_ in xd.defaults_s14]
        P("  %s slot 52 (0x%x) index-0 defaults: %s" % (d, SLOT52[d], [(i_, round(u2f(b_), 7)) for i_, b_ in xd.defaults_s14]))
    check([tuple(t[:2]) for t in J["defaults_send"]] == [(i, "0x%08x" % b) for i, b in M.SEND_DEFAULTS] and
          [tuple(t[:2]) for t in J["defaults_master"]] == [(i, "0x%08x" % b) for i, b in M.MASTER_DEFAULTS],
          "slot-52 defaults for index 0: DelayTime 0.122807 (= 7/57 -> 500 ms), Feedback 0.7, HiCut 1.0, LowCut 0, Spread 0, SYNC 0; "
          "Mixratio Send 1.0 / Master 0.5 (the only difference); no BPM (fed per block)")
    tabs = {nm: [hex(im.u32(base + 4 * k)) for k in range(10)] for nm, base in (("send", 0x119a40), ("master", 0x112b4c))}
    feed = {"send": "0x119a68", "master": "0x112b74"}
    fed = {nm: [k for k in range(10) if tabs[nm][k] == feed[nm]] for nm in tabs}
    lit = (u2f(im.u32(0x119bd4)), u2f(im.u32(0x112cb8)))
    P("  processBlock jump tables: Send 0x119a40 feeds indices %s, Master 0x112b4c feeds %s (slot 14 index 7, clamp 1..%s)"
      % (fed["send"], fed["master"], lit))
    J["tempo_feed"] = fed
    check(fed["send"] == fed["master"] == [0, 2, 3, 9] and lit == (999.0, 999.0),
          "tempo: both processBlocks feed index 0 (Delay), 2, 3, 9 every block with tempo clamped to 1..999 as slot-14 index 7")
    # change detection: ctor-equal values before the first block
    xs = EmuSendDelay(defaults=None); ms0 = M.SendDelay()
    xs.set(0, 0.5); ms0.set_param(0, 0.5); xs.process([0.0] * N, [0.0] * N); ms0.process([0.0] * N, [0.0] * N)
    st = xs.state()
    P("  DelayTime 0.5 (= ctor value) before the first block: dirty never set; base DelayTimeLch stays at its ctor 1.0 ms -> module "
      "pending ms %r, pending D %d" % (u2f(st["mL.pms"]), st["mL.pD"]))
    check(st["mL.pms"] == f2u(1.0) and st["mL.pD"] == 44 and diff(st, model_state(ms0)) == [],
          "F026 change detection on SYNC/BPM/DelayTime: a value equal to the ctor value is never applied; with DelayTime never changed the "
          "lines run at the base ctor 1.0 ms (44 samples), not at 0.5 -> 2005 ms")

    # ---------------------------------------------------------------------------------------------------------- C2
    P("\n== C2 formula sweeps (emulated read-back vs model, full state after every step)")
    tab = [(x.u(SYNC_TABLE + 4 * k) & 0xffff, x.u(SYNC_TABLE + 4 * k) >> 16) for k in range(8)]
    check(tab == M.SYNC_BEATS, "sync table 0xf61f94 (filled by .init_array 0x6cb20) = %s beats" % tab)

    def sweep(name, setup, seq, key_fields, defaults="send"):
        xw, mw = new_pair(defaults=defaults)
        for idx, v in setup: xw.set(idx, v); mw.set_param(idx, v)
        bpm = 120.0; rows = []; bad = 0; nvals = 0
        for item in seq:
            if item[0] == "bpm": bpm = item[1]; continue
            idx, v = item
            xw.set(idx, v); mw.set_param(idx, v); xw.set(7, bpm); mw.set_param(7, bpm)
            xw.process([0.0] * N, [0.0] * N); mw.process([0.0] * N, [0.0] * N)
            se, sm = xw.state(), model_state(mw); dd = diff(se, sm); nvals += len(sm)
            if dd: bad += 1
            rows.append((item, bpm, {k_: se[k_] for k_ in key_fields}, dd[:3]))
        P("  %-10s %3d steps, %6d field comparisons, %d steps with a difference" % (name, len(rows), nvals, bad))
        return rows, bad
    # free delay time
    vs = [0.0, 1.0, 0.5, 0.25, 0.75, 7 / 57, 1 / 3990, 0.5 / 3990, 1.5 / 3990, 2.5 / 3990, 0.123456, 0.999, 0.99987, 1.05, -0.002, 0.3]
    for k in (10.5, 11.5, 499.5, 2000.5, 3999.5):            # rint half-way points 10 + 3990 v = k and their float neighbours
        v0 = F((k - 10.0) / 3990.0); vs += [v0, F(math.nextafter(v0, 0.0)), F(math.nextafter(v0, 1.0))]
    rr5 = random.Random(5); vs += [rr5.random() for _ in range(14)]
    vs = [F(v) for v in vs]; seq = []
    for v in vs: seq += [(0, v), (0, v)]
    rows, bad = sweep("time free", [(1, 0.0)], seq, ["mL.pms", "mL.pD", "mR.pms", "mR.pD", "bp.tL", "bp.tR"])
    P("    v -> ms/samples: " + ", ".join("%.6g->%g/%d" % (r_[0][1], fl(r_[2]["mL.pms"]), r_[2]["mL.pD"]) for r_ in rows[::2][:24]))
    check(bad == 0 and len(set(vs)) >= 30 and all(r_[2]["mL.pms"] == r_[2]["mR.pms"] and r_[2]["bp.tL"] == r_[2]["bp.tR"] for r_ in rows),
          "DelayTime free: ms = rint_even(10 + 3990 v) (10..4000 ms in 1 ms steps; > 4000 clamped by setDelay), samples = "
          "trunc(F(ms*0.001f)*fs), identical for L and R: %d values incl. rint boundaries, 0 mismatches" % len(set(vs)))
    J["sweep_time_free"] = [(r_[0][1], fl(r_[2]["mL.pms"]), r_[2]["mL.pD"]) for r_ in rows[::2]]
    # sync
    seq = []; sv = [0.0, 0.0714, 1 / 7, 2 / 7, 3 / 7, 4 / 7, 5 / 7, 6 / 7, 1.0, 0.0715, 1.2, -0.2]
    for bpm in (1.0, 30.0, 60.0, 87.5, 120.0, 133.37, 200.0, 333.0, 999.0):
        seq.append(("bpm", bpm)); seq += [(0, F(v)) for v in sv]
    rows, bad = sweep("time sync", [(6, 1.0), (1, 0.0)], seq, ["mL.pms", "mL.pD"])
    P("    bpm 120: " + ", ".join("%.4g->%g" % (r_[0][1], fl(r_[2]["mL.pms"])) for r_ in rows if r_[1] == 120.0))
    P("    bpm 133.37: " + ", ".join("%.4g->%.6g" % (r_[0][1], fl(r_[2]["mL.pms"])) for r_ in rows if r_[1] == 133.37))
    check(bad == 0, "DelayTime sync: i = rint(7v) -> beats 1/8,1/4,1/2,3/4,1,2,4,8 (out of range -> index 6 = 4 beats), "
          "ms = F(F(F(num/den)*1000)*60)/BPM clamped [10, 4000]; 9 BPM values 1..999 x %d values, 0 mismatches" % len(sv))
    J["sweep_time_sync"] = [(r_[1], r_[0][1], fl(r_[2]["mL.pms"]), r_[2]["mL.pD"]) for r_ in rows]
    # feedback
    fv = [0.0, 0.005, 0.123, 0.25, 0.5, 0.7, 0.995, 1.0, 1.2, -0.1, 0.33333, 0.66]
    rows, bad = sweep("feedback", [], [(1, F(v)) for v in fv], ["fbL", "fbR", "bp.gL", "bp.gR"])
    P("    v -> gain target L/R: " + ", ".join("%g->%.8g/%.8g" % (r_[0][1], fl(r_[2]["fbL"][2]), fl(r_[2]["fbR"][2])) for r_ in rows))
    check(bad == 0 and all(fl(r_[2]["fbL"][2]) == F(r_[0][1]) == fl(r_[2]["fbR"][2]) for r_ in rows),
          "Feedback: g = v unquantised and unclamped (0.123 -> 0.123, 1.2 -> 1.2), same for L and R, re-read every block (no change "
          "detection), reached by 147-sample linear SmoothFloat ramps (+0x1a4/+0x1c8); %d values, 0 mismatches" % len(fv))
    J["sweep_feedback"] = [(r_[0][1], fl(r_[2]["fbL"][2])) for r_ in rows]
    # spread
    sp = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.3, -0.2]
    rows, bad = sweep("spread", [], [(4, F(v)) for v in sp], ["direct", "cross"])
    P("    v -> direct/cross targets: " + ", ".join("%g->%.7g/%.7g" % (r_[0][1], fl(r_[2]["direct"][2]), fl(r_[2]["cross"][2]))
                                                    for r_ in rows))
    check(bad == 0, "Spread: direct gain target F(1 - v), cross gain target v (147-sample ramps, every block); %d values" % len(sp))
    J["sweep_spread"] = [(r_[0][1], fl(r_[2]["direct"][2]), fl(r_[2]["cross"][2])) for r_ in rows]
    # hicut / lowcut targets
    hv = [0.0, 0.0005, 0.001001, 0.25, 0.5, 0.75, 0.999, 1.0, -0.1, 1.5, 0.123, 0.876]
    seq = []
    for v in hv: seq += [(2, F(v))] + [(5, 0.0)] * 2
    rows, bad = sweep("hicut", [(1, 0.0)], seq, ["hc.tgt", "hc.tgtcut", "hc.cur", "hc.fc"])
    P("    v -> step/target Hz: " + ", ".join("%g->%d/%.2f" % (r_[0][1], r_[2]["hc.tgt"] + 1, r_[2]["hc.tgtcut"]) for r_ in rows
                                               if r_[0][0] == 2))
    check(bad == 0, "HiCut: step = trunc_s32(999v) + 1 clamped 1..1000 (v <= 0 -> 1), target 2000*10^((step-1)/999) Hz = 2..20 kHz, "
          "glide 1 step per 1/3 ms; 1st-order LPF (IirLpf1stOrder); %d values, 0 mismatches" % len(hv))
    J["sweep_hicut"] = [(r_[0][1], r_[2]["hc.tgt"] + 1, r_[2]["hc.tgtcut"]) for r_ in rows if r_[0][0] == 2]
    lv = [0.0, 0.05, 0.1, 0.2, 0.25, 0.5, 0.75, 0.9, 0.999, 1.0, -0.1, 1.2, 0.0001, 0.3]
    seq = []
    for v in lv: seq += [(3, F(v))] + [(5, 0.0)] * 2
    rows, bad = sweep("lowcut", [(1, 0.0)], seq, ["lc.tgt", "lc.tgtcut", "lc.cur", "lc.fc"])
    P("    v -> step/target Hz: " + ", ".join("%g->%d/%.3f" % (r_[0][1], r_[2]["lc.tgt"] + 1, r_[2]["lc.tgtcut"]) for r_ in rows
                                               if r_[0][0] == 3))
    check(bad == 0, "LowCut: x = 1 - v, step = trunc_s32(999 (1 - x^4)) + 1, target 1*1000^((step-1)/999) Hz = 1..1000 Hz (passed to "
          "the coefficients clamped to >= 5 Hz), glide 1 step per 1/3 ms; 1st-order HPF (IirHpf1stOrder); %d values, 0 mismatches" % len(lv))
    J["sweep_lowcut"] = [(r_[0][1], r_[2]["lc.tgt"] + 1, r_[2]["lc.tgtcut"]) for r_ in rows if r_[0][0] == 3]
    # settled filters (full glides)
    xw, mw = new_pair(); xw.set(2, 0.0); mw.set_param(2, 0.0); xw.set(3, 1.0); mw.set_param(3, 1.0)
    for _ in range(260): xw.set(7, 120.0); mw.set_param(7, 120.0); xw.process([0.0] * N, [0.0] * N); mw.process([0.0] * N, [0.0] * N)
    se = xw.state()
    P("    after 260 blocks HiCut 0 / LowCut 1: hc step %d cut %.4f fc %r coef %s; lc step %d cut %.4f fc %r coef %s" %
      (se["hc.cur"], se["hc.cut"], u2f(se["hc.fc"]), [u2f(c) for c in se["hc.coef"][:3]], se["lc.cur"], se["lc.cut"], u2f(se["lc.fc"]),
       [u2f(c) for c in se["lc.coef"][:3]]))
    check(diff(se, model_state(mw)) == [] and se["hc.cur"] == 0 and se["lc.cur"] == 999,
          "full glides (HiCut 20 k -> 2 kHz, LowCut 1 Hz -> 1 kHz, 999 steps x 1/3 ms) settle with model-equal coefficients")
    # mixratio
    mv = [0.0, 0.3, 0.5, 0.749999, 0.75, 0.8, 0.9, 1.0, 1.2, -0.2]
    rows, bad = sweep("mixratio", [], [(5, F(v)) for v in mv], ["dry+0x6a4", "wet+0x6a8", "eb.dry+0x10", "eb.wet+0x14"])
    P("    v -> dry/wet: " + ", ".join("%g->%.7g/%.7g" % (r_[0][1], fl(r_[2]["eb.dry+0x10"]), fl(r_[2]["eb.wet+0x14"])) for r_ in rows))
    check(bad == 0 and all(r_[2]["dry+0x6a4"] == r_[2]["eb.dry+0x10"] for r_ in rows),
          "Mixratio (head of 0x104e98, every block): v < 0.75: dry 1, wet v*1.3333334f; else wet 1, dry 1 - 4(v - 0.75); copied by "
          "slot 13 0x1049e8 to EffectBase +0x10/+0x14 (same law as InsertFxDelay); %d values" % len(mv))
    J["sweep_mix"] = [(r_[0][1], fl(r_[2]["eb.dry+0x10"]), fl(r_[2]["eb.wet+0x14"])) for r_ in rows]
    # libm oracle for the LowCut coefficient range (tan of 5..1000 Hz) and the 1000-step multiplier
    e = x.e
    def lcall(nm, *ds):
        args = []
        for dv in ds: u = emu.d2u(dv); args += [u & 0xffffffff, u >> 32]
        r0, r1 = e.call(e.lib_exports[nm][0], *args); return emu.u2d(r0 | (r1 << 32))
    rr = random.Random(9); bad_t = 0
    targs = [float(F(fc)) * (math.pi / 44100.0) for fc in [5.0, 1000.0] + [rr.uniform(5, 1000) for _ in range(500)]]
    for t in targs:
        if lcall("tan", t) != ID.cr_tan(t): bad_t += 1
    mult = lcall("pow", 10.0, lcall("log10", 1000.0) / 999.0)
    P("  libm: tan on %d LowCut args: cr_tan mismatches %d; 10^(log10(1000)/999) = %r (model %r)" % (len(targs), bad_t, mult,
                                                                                                  M.SteppedFilter("hpf", 44100, 1000, 1, 1000).mult))
    check(bad_t == 0 and mult == M.SteppedFilter("hpf", 44100, 1000, 1, 1000).mult, "correctly rounded tan/pow reproduce the 1.60 libm")

    # ---------------------------------------------------------------------------------------------------------- C3
    P("\n== C3 layout / constants / vtables")
    xc, mc = new_pair()
    o = xc.o; mL = xc.u(o + 0x19c); ring = xc.u(mL + 0x1c); hc = xc.u(o + 0x69c); lc = xc.u(o + 0x6a0)
    consts = {"ring frames": (xc.u(ring + 4), mc.modL.ring.L), "ring vptr": (hex(xc.u(ring)), "0x83e5c0"),
              "module vptr (L,R)": ((hex(xc.u(mL)), hex(xc.u(xc.u(o + 0x1a0)))), ("0x840028", "0x840028")),
              "maxms": (u2f(xc.u(mL + 0x84)), float(mc.modL.maxms)), "interp flag +0x88": (xc.b(mL + 0x88), 1),
              "gate N": (xc.u(mL + 0x34 + 0x38), mc.modL.gate.r.N), "fb/direct/cross ramp N": (xc.u(o + 0x1a4 + 0x1c), mc.fbL.N),
              "HiCut vptr/fmin/fmax/steps": ((hex(xc.u(xc.u(hc))), xc.u(hc + 4), xc.u(hc + 8), xc.u(hc + 0xc)), ("0x840dd8", 2000, 20000, 1000)),
              "LowCut vptr/fmin/fmax/steps": ((hex(xc.u(xc.u(lc))), xc.u(lc + 4), xc.u(lc + 8), xc.u(lc + 0xc)), ("0x840db8", 1, 1000, 1000)),
              "block +4 / scratch count +8 / fs +0x10": ((xc.u(o + 4), xc.u(o + 8), xc.u(o + 0x10)), (64, 7, 44100)),
              "vptrs primary/secondary": ((hex(xc.u(o)), hex(xc.u(o + EB))), ("0x841ea8", "0x841eec"))}
    for k_, (ev, mv_) in consts.items(): P("  %-40s emu %-40r model/expected %r" % (k_, ev, mv_))
    check(all(ev == mv_ for ev, mv_ in consts.values()), "constants: two mono DelayModules (vt 0x840028) with rings of 178,900 frames "
          "(4000 ms + 2500), 147-sample ramps/gates, HiCut LPF 2..20 kHz and LowCut HPF 1..1000 Hz (1000 steps each)")
    check(diff(xc.state(), model_state(mc)) == [] and xc.rings() == model_rings(mc),
          "%d state fields + both rings equal after ctor + Send slot 52 (compared after every block in C4)" % len(model_state(mc)))
    pv = [im.u32(VT + 4 * k) for k in range(15)]; dv = [im.u32(0x841de0 + 4 * k) for k in range(15)]
    sv2 = [im.u32(VT2 + 4 * k) for k in range(32)]; ebv = [im.u32(0x841fb8 + 4 * k) for k in range(32)]
    P("  primary vtable 0x841ea8 (DelayEchoBase layout, 15 slots): " + ", ".join("%d %s%s" % (k, hex(v), "" if v != dv[k] else "=DEB")
                                                                               for k, v in enumerate(pv)))
    P("  secondary 0x841eec overrides of EffectBase 0x841fb8: " + ", ".join("%d %s" % (k, hex(v)) for k, v in enumerate(sv2) if v != ebv[k]))
    J["vtables"] = {"primary": [hex(v) for v in pv], "secondary_overrides": {k: hex(v) for k, v in enumerate(sv2) if v != ebv[k]}}
    check(pv[5] == 0x104a30 and pv[8] == 0x104ce4 and pv[13] == 0x1049e8 and pv[14] == 0x104e98 and sv2[25] == 0x104e90 and
          sv2[27] == 0x1049fc and sv2[26] == 0x1049e0 and sv2[10] == ebv[10],
          "vtable roles: primary 5 process 0x104a30, 8 apply base params 0x104ce4, 13 mix copy 0x1049e8, 14 param update+process 0x104e98; "
          "secondary 25 -> 0x104e98, 26 -> slot 13, 27 -> 0x104a04 (slot 8 + slot 4 reset), slot 10 = EffectBase default")

    # ---------------------------------------------------------------------------------------------------------- C4
    hashes = {}
    if not a.skip_matrix:
        P("\n== C4 end-to-end matrix (slot 25 output, state after every block, final rings)")
        jobs, outs = run_parallel("matrix", a.jobs, os.path.join(a.out, "work"))
        results = []
        for jb, (r_, blob) in zip(jobs, outs):
            fn = "%s__%s.f32" % (jb[1].replace("/", "_"), jb[5]); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
            results.append(r_)
            P("  %-36s %-7s %4d blk  mism %d  max|err| %g  nonzero %6d  state %s  rings %s  ms %s" %
              (jb[1], jb[5], jb[6], r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], "ok" if r_["first_state_diff"] is None
               else r_["first_state_diff"], "eq" if r_["final_ring_equal"] else "DIFF", r_["ms_log"][:6]))
        J["matrix"] = results
        tot = sum(r_["samples"] for r_ in results)
        check(all(r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None and r_["final_ring_equal"] for r_ in results),
              "send_delay.py bit-exact to emulated slot 25: %d runs, %d output samples, state equal after every block, final rings equal"
              % (len(results), tot))
        nonsilent = [r_ for r_ in results if r_["signal"] != "silence"]
        check(len(SETTINGS) >= 8 and all(s[3] >= 120 for s in SETTINGS) and len(EVENTS) >= 2 and
              all(r_["nonzero_out"] > 0 for r_ in nonsilent),
              "coverage: %d settings x %d signals, %d event runs x %d signals; every non-silent run has non-zero (echo) output"
              % (len(SETTINGS), len(SIGNALS), len(EVENTS), len(EVENT_SIGNALS)))
    a._hashes = hashes
    return main_part2(a, P, check, fails, rep, J, im, fl)


def main_part2(a, P, check, fails, rep, J, im, fl):
    hashes = a._hashes
    # ---------------------------------------------------------------------------------------------------------- C5
    P("\n== C5 start-up, reset, retrigger, delay change")
    def single_impulse(at, nblk, pre=(), defaults="send", ch=0):
        xs, ms_ = new_pair(defaults=defaults)
        for i_, v_ in pre: xs.set(i_, v_); ms_.set_param(i_, v_)
        imp = [F(1.0) if k == at else F(0.0) for k in range(N * nblk)]; z = [F(0.0)] * (N * nblk)
        L, R = (imp, z) if ch == 0 else (z, imp)
        same = True; nz = []
        for blk in range(nblk):
            xs.set(7, 120.0); ms_.set_param(7, 120.0)
            bl, br = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
            eL, eR = xs.process(bl, br); mL_, mR_ = ms_.process(bl, br)
            same = same and [f2u(v) for v in eL + eR] == [f2u(v) for v in mL_ + mR_]
            nz += [(blk * N + k, "L", v) for k, v in enumerate(eL) if v != 0.0] + [(blk * N + k, "R", v) for k, v in enumerate(eR) if v != 0.0]
        return same, sorted(nz)
    s0, nz0 = single_impulse(0, 1100)
    s1, nz1 = single_impulse(192, 1100)
    P("  Send defaults (500 ms = 22050 samples, fb 0.7): impulse at t=0 -> %d non-zero outputs in 1100 blocks (model==emu %s); at t=192 -> "
      "first %s, %d non-zero (model==emu %s)" % (len(nz0), s0, [(t, c, round(v, 4)) for t, c, v in nz1[:2]], len(nz1), s1))
    check(s0 and s1 and len(nz0) == 0 and nz1 and nz1[0][0] == 192 + 22050,
          "start-up: same warm-up gate as InsertFxDelay (F079): an impulse at t = 0 falls in the muted window and, since the gated signal "
          "is the feedback source, never echoes; an impulse at t = 192 echoes at 22242")
    s2, nz2 = single_impulse(192, 3000, pre=[(0, ms_v(50.0)), (1, 0.0)])
    P("  first applied delay = 50 ms (= module ctor value, setDelay is a no-op): impulse at t=192 -> first outputs %s (model==emu %s)"
      % ([(t, c, round(v, 4)) for t, c, v in nz2[:2]], s2))
    check(s2 and nz2 and nz2[0][0] == 192 + 178900,
          "quirk: if the first DelayTime applied after construction is exactly 50 ms the read pointer is never placed and the echo comes "
          "after the full ring length 178,900 samples (4.057 s) instead of 2205 samples, until the delay time changes")
    s3, nz3 = single_impulse(192, 500, pre=[(0, ms_v(300.0)), (1, 0.6), (4, 1.0)])
    P("  Spread 1.0, 300 ms, fb 0.6, L impulse at t=192: first echoes %s" % [(t, c, round(v, 4)) for t, c, v in nz3[:3]])
    fR = min([t for t, c, _ in nz3 if c == "R"] or [-1]); fL = min([t for t, c, _ in nz3 if c == "L"] or [-1])
    P("    first non-zero R at %d, first non-zero L at %d" % (fR, fL))
    check(s3 and fR == 192 + 13230 and fL == 192 + 2 * 13230,
          "Spread 1 = ping-pong: an L impulse echoes first on R (13230 samples), then on L (26460)")
    # reset
    xr, mr = new_pair(); Ls, Rs = signal("noise", 3000)
    for i_, v_ in ((0, 0.12), (1, 0.9), (4, 0.3)): xr.set(i_, v_); mr.set_param(i_, v_)
    for blk in range(3000):
        xr.set(7, 120.0); mr.set_param(7, 120.0)
        xr.process(Ls[blk * N:(blk + 1) * N], Rs[blk * N:(blk + 1) * N]); mr.process(Ls[blk * N:(blk + 1) * N], Rs[blk * N:(blk + 1) * N])
    def nzr(xx): return [sum(1 for k in range(n_) if struct.unpack_from("<f", raw, 8 * k)[0] != 0.0) for n_, raw in xx.rings()]
    before = nzr(xr); calls = []
    for a_ in (0x1049fc, 0x104a04, 0x104ce4, 0x104108, 0xec314, 0xf5584, 0x104e98, 0x10623c):
        xr.e.add_watch(a_, lambda em, a_=a_: calls.append(hex(a_)))
    xr.e.vcall(xr.eb, 27); mr.reset()
    se = xr.state(); after = nzr(xr)
    P("  slot 27: calls %s; ring non-zero frames before %s after %s; mL w %d pos %r gate %r cnt %d warm %d" %
      (calls, before, after, se["mL.r.w"], se["mL.r.pos"], se["mL.g"][:2], se["mL.cnt"], se["mL.warm"]))
    check(before == after and before[0] > 170000 and se["mL.r.w"] == 0 and diff(se, model_state(mr)) == [] and
          xr.rings() == model_rings(mr) and "0x104e98" not in calls,
          "slot 27 = slot 8 (apply base params) + slot 4 0x104108 (slot 8 again, both module resets 0xec314, all four ramps snapped): ring "
          "indices rewound, samples KEPT, gates closed, counters 0; pending Parameter changes are NOT consumed (0x104e98 not called)")
    calls.clear(); r5 = xr.e.vcall(xr.eb, 5, 0, 0)[0]; c5a = list(calls)
    P("  EffectBase slot 5 (e, 0, 0) [Send activation] calls %s" % c5a)
    check("0x104a04" in c5a, "EffectBase slot 5 (activation) runs slot 27: activation rewinds both lines (ring samples kept)")
    s0_ = xr.state(); r10 = xr.e.vcall(xr.eb, 10)[0]; s1_ = xr.state()
    check(r10 == 2 and s0_ == s1_, "slot 10 = EffectBase default 0x10594c: returns 2, no state change")
    # delay change
    xt, mt = new_pair(); gtr = []
    for i_, v_ in ((0, ms_v(208.0)), (1, 0.5)): xt.set(i_, v_); mt.set_param(i_, v_)
    Ln, Rn = signal("noise", 400)
    for blk in range(400):
        if blk == 300: xt.set(0, ms_v(60.0)); mt.set_param(0, ms_v(60.0))
        xt.set(7, 120.0); mt.set_param(7, 120.0)
        xt.process(Ln[blk * N:(blk + 1) * N], Rn[blk * N:(blk + 1) * N]); mt.process(Ln[blk * N:(blk + 1) * N], Rn[blk * N:(blk + 1) * N])
        if 299 <= blk <= 306:
            s_ = xt.state(); gtr.append((blk, round(u2f(s_["mL.g"][1]), 4), s_["mL.g"][0], s_["mL.D"], s_["mR.D"], s_["mL.pend"]))
    P("  time change 208 -> 60 ms at block 300 (block, gate L, state, D L, D R, pending): %s" % gtr)
    check(gtr[1][5] == 1 and gtr[3][3] == gtr[3][4] == 2646 and gtr[-1][1] == 1.0,
          "delay-time change: both lines fade out (147 samples), jump to the new delay together, fade in; no glide, no buffer clear")
    J["startup"] = {"t0": len(nz0), "t192": nz1[:2], "q50": nz2[:2], "pingpong": nz3[:3], "reset_calls": calls, "gate_trace": gtr}

    # ---------------------------------------------------------------------------------------------------------- C6
    P("\n== C6 Send vs Master object (real processBlock rigs, slot-25 in/out captured, model fed the captured input)")
    blk_m = [im.u32(0x114bdc + 4 * k) for k in range(9)]; blk_s = [im.u32(0x11bc04 + 4 * k) for k in range(10)]
    P("  ctor sites: Master 0x114bec new / 0x114bf0 movw r1,#0xac44 / mov r2,#0x40 / bl 0x1054ac @0x114bfc; Send 0x11bc18 / 0x11bc1c "
      "/ 0x11bc20 / bl @0x11bc28 (identical words: %s)" % (im.u32(0x114bf0) == im.u32(0x11bc1c) and im.u32(0x114bf4) == im.u32(0x11bc20)))
    rig_res = {}
    for which in ("send", "master"):
        rg = ProcRig(which); m = M.SendDelay(); m.defaults(master=(which == "master"))
        Lq, Rq = signal("noise", 800); bpm_ev = {0: 120.0, 300: 90.0, 500: 133.37}
        for i_, v_ in ((6, 1.0), (0, F(2 / 7)), (1, 0.6), (4, 0.3)): rg.x.set(i_, v_); m.set_param(i_, v_)
        bad = 0; resets = []; feeds = 0; nz = 0; st_bad = None
        for b in range(800):
            if b in bpm_ev: rg.bpm = bpm_ev[b]
            (oL, oR), nres, s14 = rg.block(Lq[N * b:N * b + N], Rq[N * b:N * b + N])
            for _ in range(nres): m.reset()
            if nres: resets.append(b)
            feeds += sum(1 for i_, v_ in s14 if i_ == 7 and u2f(v_) == F(rg.bpm))
            for i_, v_ in s14: m.set_param(i_, u2f(v_))
            if "in" not in rg.cap: bad += N; continue
            yL, yR = m.process(rg.cap["in"][3], rg.cap["in"][4])
            bad += sum(1 for p_, q_ in zip(yL + yR, rg.cap["out"][0] + rg.cap["out"][1]) if f2u(p_) != f2u(q_))
            nz += sum(1 for v in yL + yR if v != 0.0)
            if st_bad is None and diff(rg.x.state(), model_state(m)): st_bad = (b, diff(rg.x.state(), model_state(m))[:3])
        rig_res[which] = {"mism": bad, "resets_at": resets, "tempo_feeds": feeds, "nonzero": nz, "state": st_bad,
                          "ms_log": [float(v) for v in m.ms_log]}
        P("  %-6s rig: 800 noise blocks, sync 1/2 beat, BPM 120 -> 90 (blk 300) -> 133.37 (blk 500): slot-25 mismatches %d, state %s, "
          "slot-27 calls at blocks %s, tempo feeds (index 7 = rig BPM) %d, non-zero wet %d, ms %s" %
          (which, bad, "ok" if st_bad is None else st_bad, resets, feeds, nz, rig_res[which]["ms_log"]))
    J["rigs"] = rig_res
    check(all(r_["mism"] == 0 and r_["state"] is None and r_["tempo_feeds"] == 800 and r_["nonzero"] > 0 for r_ in rig_res.values())
          and rig_res["send"]["ms_log"] == rig_res["master"]["ms_log"] ==
          [float(M.SendDelay.sync_ms(F(2 / 7), F(b_))) for b_ in (120.0, 90.0, 133.37)],
          "Send and Master: the real processBlock feeds the tempo to index 0 every block (BPM changes re-time the synced delay at the next "
          "block) and the same SendFxDelay slot 25 matches the model bit-exactly through the processor")
    P("  activation: Send slot 5 (e,0,0) reset at blocks %s, Master slot 5 (e,0,1) reset at blocks %s" %
      (rig_res["send"]["resets_at"], rig_res["master"]["resets_at"]))

    # ---------------------------------------------------------------------------------------------------------- C7
    P("\n== C7 alternatives")
    xi, mi = new_pair(); fracs = set(); Lq, Rq = signal("noise", 300)
    for blk in range(300):
        if blk in (50, 100, 101, 200): v = {50: 0.33, 100: 0.777, 101: 0.0101, 200: 0.6}[blk]; xi.set(0, v)
        xi.set(7, 133.37 if blk > 150 else 120.0); xi.process(Lq[blk * N:(blk + 1) * N], Rq[blk * N:(blk + 1) * N])
        st = xi.state(); fracs.add(st["mL.r.pos"] - int(st["mL.r.pos"])); fracs.add(st["mR.r.pos"] - int(st["mR.r.pos"]))
    check(fracs == {0.0}, "(c) integer read: both read positions always integral (the interpolating ring read runs with frac 0)")
    jobs, outs = run_parallel("mutants", a.jobs, os.path.join(a.out, "work"))
    mres = []
    for (nm_, fn_, case, sig), (r_, _) in zip(MUTANTS, outs):
        caught = r_["mismatched_samples"] > 0 or r_["first_state_diff"] is not None or not r_["final_ring_equal"]
        mres.append((nm_, case, sig, r_["mismatched_samples"], r_["max_abs_err"], caught))
        P("  mutant %-44s on %-34s %-6s mism %6d  max|err| %-10.4g -> %s" % (nm_, case, sig, r_["mismatched_samples"], r_["max_abs_err"],
                                                                             "CAUGHT" if caught else "not caught"))
    J["mutants"] = mres
    check(all(m_[5] for m_ in mres), "all %d alternative models are refuted by emulation" % len(mres))

    # ---------------------------------------------------------------------------------------------------------- outputs
    P("\nRESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  FAILED: " + f_)
    cat = b"".join(open(os.path.join(a.out, k_), "rb").read() for k_ in sorted(hashes))
    J["f32_hashes"] = hashes; J["f32_concat_sha256"] = sha(cat) if hashes else None
    P("f32 files: %d, sorted concatenation sha256 %s" % (len(hashes), J["f32_concat_sha256"]))
    open(os.path.join(a.out, "h043_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h043.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
