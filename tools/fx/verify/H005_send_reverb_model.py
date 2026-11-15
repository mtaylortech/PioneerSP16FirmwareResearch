#!/usr/bin/env python3
"""H005 — SendFxReverb (Send/Master "Reverb", index 1 of both FX processor arrays; primary vtable 0x842618 = EffectBase part,
secondary vtable 0x8426b0 = Reverb9NXSBase sub-object at +0x1b8; new 0x478, ctor 0x1123d0(obj, 44100, 64); EffectBase slot 25
0x111730 -> own slot 32 0x1120c4 -> Reverb9NXSBase slot 18 0x10e2e0) end to end: Freeverb test, parameters, formulas, state layout and a
bit-exact own-code model harness/models/send_reverb.py vs the emulated 1.60 slot 25.

Sections (criteria of kb/cycles/022.md):
  C1  Freeverb / juce::Reverb test (constants and symbols in the image; actual comb/allpass lengths).
  C2  parameter list (registrations logged in the real ctor, slot-14 index map, Send/Master slot-52 defaults, feeds).
  C3  formula sweeps by emulated read-back vs the model (full state after every step).
  C4  layout: state compared after every block in C5.
  C5  end-to-end matrix: settings x {impulse, sine, noise, silence, L-only, R-only} + mid-run event runs; regress mode.
  C6  start-up, reset, retrigger.  C7  Send vs Master.  C8  alternatives (model mutants that must fail).
Outputs only to --out (default harness/out/H005/). Run: .venv/bin/python -B harness/H005_send_reverb_model.py --out DIR
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
import send_reverb as M                                        # noqa: E402
from lofi import F                                             # noqa: E402

FS = 44100; N = 64
CTOR, SIZE, VT, VT2, R9OFF = 0x1123d0, 0x478, 0x842618, 0x8426b0, 0x1b8
SLOT52 = {"send": 0x11baa8, "master": 0x114ad4}
PARAM_OFF = [0x244 + 0x5c * i for i in range(6)]


def sha(b): return hashlib.sha256(b).hexdigest()


class EmuSendReverb:
    """SendFxReverb built by its real ctor 0x1123d0(obj, 44100, 64), then (optionally) the processor init as in the Send/Master ctors:
    EffectBase slot 22 (e, 0), then Send (or Master) slot 52 (container, 1) with a stand-in container (+0x80 array whose entry 1 is the
    object, +0x88 count 10); then (optionally) the activation reset slot 27. Processed by calling EffectBase slot 25."""
    def __init__(self, defaults="send", activate=True, log_regs=False, watch=None, heap_fill=0):
        if heap_fill:
            e = emu.Emu(heap_fill=heap_fill)
            e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))
            lm, base, _ = e._libs["libm.so.6"]
            for r in lm.dynamic_relocations:
                if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(base + r.address, 0x3d000000)
            self.e = e
        else:
            self.e = e = H31.new_emu()
        self.regs = []; self.s14 = []
        for i in range(13): e.setr(i, 0)
        e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
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
            e.add_watch(0xf1850, lin)
        for a_, cb in (watch or {}).items(): e.add_watch(a_, cb)
        e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), em.r(2))))
        self.o = e.malloc(SIZE, "new (harness: SendFxReverb)")
        r0, _ = e.call(CTOR, self.o, FS, N)
        assert r0 == self.o and e.u32(self.o) == VT and e.u32(self.o + R9OFF) == VT2
        self.r9 = self.o + R9OFF
        self.defaults_s14 = []
        if defaults:
            e.vcall(self.o, 22, 0)
            cont = e.malloc(0x100, "harness: FX processor stand-in (+0x80 array, +0x88 count)"); arr = e.malloc(40)
            for i in range(10): e.w32(arr + 4 * i, self.o if i == 1 else 0)
            e.w32(cont + 0x80, arr); e.w32(cont + 0x88, 10)
            self.s14 = []
            e.call(SLOT52[defaults], cont, 1)
            self.defaults_s14 = list(self.s14)
        if activate: self.reset()
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]
    def reset(self): return self.e.vcall(self.o, 27)[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    # --- field access ------------------------------------------------------------------------------------------------------
    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]
    def b(self, a): return self.e.rd(a, 1)[0]

    def state(self):
        o = self.o; r = self.r9; u, i, d = self.u, self.i, self.d
        s = {"dry+0x46c": u(o + 0x46c), "wet+0x470": u(o + 0x470), "eb.dry+0x10": u(o + 0x10), "eb.wet+0x14": u(o + 0x14)}
        for k_, off in enumerate(PARAM_OFF): s["p%d.last/cur" % k_] = [u(o + off + 0x24), u(o + off + 0x28)]
        s.update({"r9.room": [i(r + 0x5c), i(r + 0x60), i(r + 0x64)], "r9.glide": u(r + 0x70),
                  "r9.chunk": [i(r + 0x74), i(r + 0x78), i(r + 0x7c)], "r9.gain": [u(r + 0x80), u(r + 0x84)], "r9.lpfstep": u(r + 0x88)})
        for nm, off in (("lpf", 0x1c), ("hpf", 0x20)):
            fl = u(r + off); st = u(fl + 0x10)
            s[nm] = [u(fl + 0xc), u(fl + 0x28), u(fl + 0x2c), u(fl + 0x34), u(fl + 0x24), u(st), u(st + 4), u(st + 8), u(st + 12)]
        for k_ in range(5):
            c = u(r + 0x24 + 4 * k_); nm = "c%d" % k_
            s[nm + ".pos"] = [i(c + 0x38), i(c + 0x3c), i(c + 0x40), u(c + 0x44), u(c + 0x50)]
            s[nm + ".dly"] = [u(c + 0x54), u(c + 0x58), d(c + 0x60), d(c + 0x68), u(c + 0x70), u(c + 0x74), u(c + 0x78), u(c + 0x7c),
                              i(c + 0x80), i(c + 0x84)]
            s[nm + ".gain"] = [u(c + 0x88 + 4 * j) for j in range(6)] + [i(c + 0xa0), i(c + 0xa4)]
            s[nm + ".spr"] = [u(c + 0xa8 + 4 * j) for j in range(6)] + [i(c + 0xc0), i(c + 0xc4)]
            h = u(r + 0x38 + 4 * k_); fl = u(h); st = u(fl + 0x10)
            s[nm + ".lpf"] = [d(h + 0x18), d(h + 0x20), u(h + 0x28), u(h + 0x2c), u(h + 0x30), self.b(h + 0x40), u(fl + 0xc),
                              u(fl + 0x28), u(fl + 0x2c), u(fl + 0x34), u(st), u(st + 4), u(st + 8), u(st + 12)]
        for k_ in range(2):
            a = u(r + 0x4c + 4 * k_)
            s["ap%d" % k_] = [u(a + 0x20), u(a + 0x24), u(a + 0x28), u(a + 0x2c), u(a + 0x30), u(a + 0x34), u(a + 0x38), u(a + 0x3c),
                              i(a + 0x4c), i(a + 0x50), i(a + 0x54), u(a + 0x58)]
        p = u(o + 0x474)
        s["pd"] = [i(p + 0x24), u(p + 0x2c), d(p + 0x38), u(p + 0x40), u(p + 0x44), u(p + 0x48), i(p + 0x4c), i(p + 0x50), u(p + 0x54),
                   i(p + 0x5c), i(p + 0x60)]
        return s

    def rings(self):
        out = []; r = self.r9; u = self.u
        for k_ in range(5):
            c = u(r + 0x24 + 4 * k_); n = u(c + 0x34)
            out += [self.e.rd(u(c + 0x2c), 4 * n), self.e.rd(u(c + 0x30), 4 * n)]
        for k_ in range(2):
            a = u(r + 0x4c + 4 * k_); n = u(a + 0x40)
            out += [self.e.rd(u(a + 0x44), 4 * n), self.e.rd(u(a + 0x48), 4 * n)]
        p = u(self.o + 0x474); n = u(p + 0x28)
        out += [self.e.rd(u(p + 0x1c), 4 * n), self.e.rd(u(p + 0x20), 4 * n)]
        return out


def model_state(m):
    fb = f2u
    s = {"dry+0x46c": fb(m.dry), "wet+0x470": fb(m.wet), "eb.dry+0x10": fb(m.eb_dry), "eb.wet+0x14": fb(m.eb_wet)}
    for k_ in range(6): s["p%d.last/cur" % k_] = [fb(m.p[k_].last), fb(m.p[k_].cur)]
    s.update({"r9.room": [m.room_cur, m.room_set, m.room_tgt], "r9.glide": fb(m.glide_t),
              "r9.chunk": [m.chunk_n, m.chunk_rem, m.idle], "r9.gain": [fb(m.in_gain), fb(m.out_gain)], "r9.lpfstep": m.lpf_step})
    for nm, f_ in (("lpf", m.lpf), ("hpf", m.hpf)):
        s[nm] = [fb(f_.fc), fb(f_.b0), fb(f_.b1), fb(f_.a1), fb(f_.k), fb(f_.v1[0]), fb(f_.v1[1]), fb(f_.y1[0]), fb(f_.y1[1])]
    for k_, c in enumerate(m.combs):
        nm = "c%d" % k_
        s[nm + ".pos"] = [c.w, c.count, c.thresh, fb(c.fade), fb(c.glide)]
        s[nm + ".dly"] = [fb(c.ms[0]), fb(c.ms[1]), c.d[0], c.d[1], fb(c.tgt[0]), fb(c.tgt[1]), fb(c.dinc[0]), fb(c.dinc[1]), c.dcnt, c.dst]
        s[nm + ".gain"] = [fb(c.g[0]), fb(c.g[1]), fb(c.ginc[0]), fb(c.ginc[1]), fb(c.gtgt[0]), fb(c.gtgt[1]), c.gcnt, c.gst]
        s[nm + ".spr"] = [fb(c.s[0]), fb(c.s[1]), fb(c.sinc[0]), fb(c.sinc[1]), fb(c.stgt[0]), fb(c.stgt[1]), c.scnt, c.sst]
        h = c.lpf
        s[nm + ".lpf"] = [h.tgt_cut, h.cut, h.cur, h.tgt, fb(h.acc), h.flag, fb(h.fc), fb(h.b0), fb(h.b1), fb(h.a1),
                          fb(h.v1[0]), fb(h.v1[1]), fb(h.y1[0]), fb(h.y1[1])]
    for k_, a in enumerate(m.aps):
        s["ap%d" % k_] = [fb(a.ms[0]), fb(a.ms[1]), fb(a.dsamp[0]), fb(a.dsamp[1]), fb(a.ng[0]), fb(a.ng[1]), fb(a.g[0]), fb(a.g[1]),
                          a.w, a.count, a.thresh, fb(a.fade)]
    p = m.pd
    s["pd"] = [p.w, fb(p.ms), p.d, fb(p.inc), fb(p.cur), fb(p.tgt), p.cnt, p.st, fb(p.fade), p.count, p.thr]
    return s


def model_rings(m):
    out = []
    for c in m.combs: out += [struct.pack("<%df" % c.len, *c.ring[0]), struct.pack("<%df" % c.len, *c.ring[1])]
    for a in m.aps: out += [struct.pack("<%df" % a.len, *a.ring[0]), struct.pack("<%df" % a.len, *a.ring[1])]
    p = m.pd; out += [struct.pack("<%df" % p.len, *p.ring[0]), struct.pack("<%df" % p.len, *p.ring[1])]
    return out


def _eq(a, b):
    if isinstance(a, float) and isinstance(b, float):
        return struct.pack("<d", a) == struct.pack("<d", b)
    if isinstance(a, list) and isinstance(b, list): return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    return a == b


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if not _eq(se.get(k_), v)]


def new_pair(defaults="send", activate=True, mut=None):
    x = EmuSendReverb(defaults=defaults, activate=activate)
    m = M.SendReverb()
    if defaults: m.defaults(master=(defaults == "master"))
    if mut: mut(m)
    if activate: m.reset()
    return x, m


def signal(kind, nblk, seed=11):
    n = nblk * N; rnd = random.Random(seed)
    if kind == "impulse":        # impulse train: one every 30011 samples (L) / 40009 samples (R, half height)
        L = [F(1.0) if k % 30011 == 64 else F(0.0) for k in range(n)]
        R = [F(0.5) if k % 40009 == 7000 else F(0.0) for k in range(n)]
    elif kind == "sine":
        L = [F(0.5 * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(n)]
        R = [F(0.3 * math.sin(2 * math.pi * 3500.0 * k / FS + 1.0)) for k in range(n)]
    elif kind == "noise":
        L = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
        R = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
    elif kind == "Lonly":
        L = [F(rnd.uniform(-0.8, 0.8)) if (k % 20000) < 300 else F(0.0) for k in range(n)]
        R = [F(0.0)] * n
    elif kind == "Ronly":
        L = [F(0.0)] * n
        R = [F(rnd.uniform(-0.8, 0.8)) if (k % 20000) < 300 else F(0.0) for k in range(n)]
    else:
        L = [F(0.0)] * n; R = [F(0.0)] * n
    return L, R


def run_case(name, pre, events, kind, nblk, mut=None, keep=False, check_state=True, emu_obj=None, defaults="send", activate=True,
             state_every=1):
    x, m = new_pair(defaults=defaults, activate=activate, mut=mut) if emu_obj is None else emu_obj
    L, R = signal(kind, nblk)
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    maxerr = 0.0; nbit = 0; first_state = None; outb = bytearray(); nonzero = 0; first_nz = None
    for blk in range(nblk):
        for op in events.get(blk, []):
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "reset": x.reset(); m.reset()
        bL, bR = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
        eL, eR = x.process(bL, bR)
        mL, mR = m.process(bL, bR)
        for a_, b_ in zip(eL + eR, mL + mR):
            if f2u(a_) != f2u(b_):
                nbit += 1
                if not (math.isnan(a_) and math.isnan(b_)): maxerr = max(maxerr, abs(a_ - b_))
            if a_ != 0.0:
                nonzero += 1
                if first_nz is None: first_nz = blk
        outb += struct.pack("<%df" % (2 * N), *(eL + eR))
        if check_state and first_state is None and (blk % state_every == 0 or blk == nblk - 1):
            dd = diff(x.state(), model_state(m))
            if dd: first_state = (blk, dd[:6])
    ring_eq = x.rings() == model_rings(m)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 2 * N * nblk, "mismatched_samples": nbit, "max_abs_err": maxerr,
           "nonzero_out": nonzero, "first_nonzero_block": first_nz, "first_state_diff": first_state, "final_ring_equal": ring_eq}
    return (res, bytes(outb), (x, m)) if keep else (res, bytes(outb))




# ------------------------------------------------------------------------------------------------------------------------
# C5 matrix: settings (name, [(idx, v)] after the slot-52 defaults, blocks, defaults kind)
SETTINGS = [
    ("send_defaults", [], 400, "send"),
    ("master_defaults_mix.5", [], 400, "master"),
    ("all_min_pd0_room0_rt0_lpf0_spr0", [(1, 0.0), (2, 0.0)], 400, "send"),
    ("all_max_pd1_room1_rt1_lpf1_spr1", [(0, 1.0), (1, 1.0), (2, 1.0), (3, 1.0), (4, 1.0)], 500, "send"),
    ("pd.25_room.3_rt.09_lpf.5_spr.3", [(0, 0.25), (1, 0.3), (2, 0.09), (3, 0.5), (4, 0.3)], 400, "send"),
    ("pd.05_room.75_rt.7_lpf.2_spr.5", [(0, 0.05), (1, 0.75), (2, 0.7), (3, 0.2), (4, 0.5)], 400, "send"),
    ("pd.6_room.1_rt.52_lpf.8_spr.9_mix.6", [(0, 0.6), (1, 0.1), (2, 0.52), (3, 0.8), (4, 0.9), (5, 0.6)], 400, "send"),
    ("pd.001_room.6_rt.3_lpf.95_spr.15", [(0, 0.001), (1, 0.6), (2, 0.3), (3, 0.95), (4, 0.15)], 400, "send"),
    ("long_tail_room.9_rt.9_spr.7", [(1, 0.9), (2, 0.9), (4, 0.7), (0, 0.1)], 1200, "send"),
]
SIGNALS = ("impulse", "sine", "noise", "silence", "Lonly", "Ronly")
# mid-run events: {block: [ops]}, op = ("p", idx, v) | ("reset",)
EVENTS = [
    ("room_changes", [(2, 0.6), (4, 0.25)], 800,
     {150: [("p", 1, 0.9)], 300: [("p", 1, 0.1)], 301: [("p", 1, 0.12)], 302: [("p", 1, 0.5)], 450: [("p", 1, 0.0)],
      600: [("p", 1, 1.0)]}),
    ("pd_rt_lpf_spread_mix_changes", [(0, 0.1), (1, 0.4)], 900,
     {120: [("p", 0, 0.6)], 200: [("p", 2, 0.95)], 260: [("p", 3, 0.7)], 300: [("p", 4, 0.45)], 360: [("p", 0, 0.0)],
      420: [("p", 5, 0.8)], 480: [("p", 2, 0.05)], 520: [("p", 4, 0.85), ("p", 3, 0.0)], 600: [("p", 0, 1.0), ("p", 2, 0.5)],
      700: [("p", 4, 0.0), ("p", 5, 0.3)]}),
    ("reset_and_restart", [(1, 0.7), (2, 0.8), (0, 0.2)], 700,
     {150: [("reset",)], 151: [("p", 1, 0.3)], 400: [("p", 0, 0.5), ("reset",)], 401: [("p", 2, 0.2), ("p", 4, 0.6)]}),
]
EVENT_SIGNALS = ("impulse", "noise", "sine", "Lonly")


def matrix_jobs():
    jobs = []
    for nm, pre, nb, dfl in SETTINGS:
        for sig in SIGNALS: jobs.append(("setting", nm, pre, {}, sig, nb, dfl, None))
    for nm, pre, nb, ev in EVENTS:
        for sig in EVENT_SIGNALS: jobs.append(("event", nm, pre, ev, sig, nb, "send", None))
    return jobs


def mutant_jobs():
    jobs = []
    for nm_, fn_, case, sig, nb in MUTANTS:
        c_ = find_case(case); jobs.append((c_[0], c_[1], c_[2], c_[3], sig, nb, c_[4], nm_))
    return jobs


def find_case(name):
    for nm, pre, nb, dfl in SETTINGS:
        if nm == name: return ("setting", nm, pre, {}, dfl)
    for nm, pre, nb, ev in EVENTS:
        if nm == name: return ("event", nm, pre, ev, "send")
    raise KeyError(name)


def run_parallel(kind, nworkers, wdir):
    """Run matrix_jobs()/mutant_jobs() in nworkers subprocesses of this script (no multiprocessing semaphores: the sandbox forbids
    sysconf(SC_SEM_NSEMS_MAX)); worker k runs jobs i with i % nworkers == k and pickles its results."""
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
    kind_, name, pre, ev, sig, nb, dfl, mutname = args
    mut = dict((n_, f_) for n_, f_, _, _, _ in MUTANTS).get(mutname) if mutname else None
    return run_case(name, pre, ev, sig, nb, mut=mut, defaults=dfl, check_state=(mut is None))


# ------------------------------------------------------------------------------------------------------------------------
# C8 model mutants (alternatives; each must be caught by its target run)
def _comb_variant(c, inL, inR, n, interp=False, damp_outside=False, no_spread=False):
    """ReverbComb.process with one structural change (harness-only alternative)."""
    L = c.len; lenf = F(float(L)); rL, rR = c.ring
    fading = c.fade < 1.0; w0 = c.w; w = w0; oL = [F(0.0)] * n; oR = [F(0.0)] * n
    for k in range(n):
        c.dcnt += c.dst
        if c.dcnt < 0:
            c.dinc = [F(0.0), F(0.0)]; c.dcnt = 0; c.dst = 0; c.d = [float(c.tgt[0]), float(c.tgt[1])]
        else:
            c.d[0] += float(c.dinc[0]); c.d[1] += float(c.dinc[1])
        wf = F(float(w)); ys = []
        for ch in (0, 1):
            p = F(wf - F(c.d[ch]))
            if p < 0.0: p = F(lenf + p)
            i = int(p); r = (rL, rR)[ch]
            if interp:
                fr = F(p - F(float(i))); j = i + 1 if i < L - 1 else 0
                ys.append(F(F(r[i] * F(F(1.0) - fr)) + F(fr * r[j])))
            else: ys.append(r[i])
        if fading:
            if c.thresh < k + c.count: c.fade = F(c.fade + c.fadeinc)
            if c.fade > 1.0: c.fade = F(1.0)
        c.gcnt += c.gst
        if c.gcnt < 0: c.g = list(c.gtgt); c.gcnt = 0; c.gst = 0; c.ginc = [F(0.0), F(0.0)]
        else: c.g = [F(c.g[0] + c.ginc[0]), F(c.g[1] + c.ginc[1])]
        if fading: oL[k] = F(F(c.fade * ys[0]) * c.g[0]); oR[k] = F(F(c.fade * ys[1]) * c.g[1])
        else: oL[k] = F(c.g[0] * ys[0]); oR[k] = F(c.g[1] * ys[1])
        w = w + 1 if w < L - 1 else 0
    if fading: c.count += n
    fL = list(oL); fR = list(oR); c.lpf.process(fL, fR, n)
    if damp_outside: fL, oL = list(oL), fL; fR, oR = list(oR), fR       # output = damped, feedback = undamped
    w = w0
    for k in range(n):
        c.scnt += c.sst
        if c.scnt < 0: c.s = list(c.stgt); c.scnt = 0; c.sst = 0; c.sinc = [F(0.0), F(0.0)]
        else: c.s = [F(c.s[0] + c.sinc[0]), F(c.s[1] + c.sinc[1])]
        a, b = (F(1.0), F(0.0)) if no_spread else c.s
        rL[w] = F(F(inL[k] + F(a * fL[k])) + F(b * fR[k])); rR[w] = F(F(inR[k] + F(b * fL[k])) + F(a * fR[k]))
        w = w + 1 if w < L - 1 else 0
    c.w = w
    return oL, oR


def _patch_combs(m, **kw):
    for c in m.combs: c.process = (lambda inL, inR, n, c=c: _comb_variant(c, inL, inR, n, **kw))


def mut_mono_input(m):                          # (b) mono-summed input: both channels get (L + R) / 2
    orig = m.chunk
    def ch(L, R, n, orig=orig):
        s = [F(F(a + b) * F(0.5)) for a, b in zip(L, R)]; L[:] = s; R[:] = list(s); orig(L, R, n)
    m.chunk = ch
def mut_damp_outside(m): _patch_combs(m, damp_outside=True)      # (c) damping LPF on the output tap, not in the feedback loop
def mut_interp_read(m): _patch_combs(m, interp=True)            # (d) interpolated comb read instead of truncated integer read
def mut_no_spread(m): _patch_combs(m, no_spread=True)           # LR SWAP SPREAD ignored (straight feedback only)
def mut_no_glide(m):                            # comb delay jumps on a room change (no glide)
    for c in m.combs:
        orig = c.set_delay
        def sd(ms, ch, c=c, orig=orig):
            orig(ms, ch); c.d[ch] = float(c.tgt[ch]); c.dinc[ch] = F(0.0)
        c.set_delay = sd
def mut_freeverb_lengths(m):                    # (a) Freeverb comb tunings (first 5 of 1116..1617 samples, spread 23) instead
    tun = [1116, 1188, 1277, 1356, 1422]        #     of the room-scaled 9NXS lengths
    for c, t in zip(m.combs, tun):
        orig = c.set_delay
        def sd(ms, ch, c=c, t=t, orig=orig):
            orig(F((t + 23 * ch) * 1000.0 / FS), ch)
        c.set_delay = sd


MUTANTS = [
    ("mono_summed_input", mut_mono_input, "send_defaults", "Lonly", 300),
    ("damping_outside_loop", mut_damp_outside, "pd.05_room.75_rt.7_lpf.2_spr.5", "noise", 300),
    ("interpolated_comb_read", mut_interp_read, "room_changes", "noise", 400),
    ("spread_ignored", mut_no_spread, "pd.05_room.75_rt.7_lpf.2_spr.5", "Lonly", 300),
    ("no_delay_glide", mut_no_glide, "room_changes", "noise", 400),
    ("freeverb_comb_lengths", mut_freeverb_lengths, "send_defaults", "impulse", 300),
]


class Freeverb:
    """Classic Freeverb / juce::Reverb (own code from the published algorithm, defaults roomSize 0.5, damping 0.5, wet 0.33, dry 0,
    width 1) for the H005 alternative (a): 8 parallel LBCF combs + 4 series allpasses per channel, R tunings + 23."""
    def __init__(self):
        ct = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617]; at = [556, 441, 341, 225]
        self.cb = [[[0.0] * (t + 23 * ch) for t in ct] for ch in (0, 1)]; self.ab = [[[0.0] * (t + 23 * ch) for t in at] for ch in (0, 1)]
        self.ci = [[0] * 8, [0] * 8]; self.ai = [[0] * 4, [0] * 4]; self.lp = [[0.0] * 8, [0.0] * 8]
        self.fb = 0.5 * 0.28 + 0.7; self.damp = 0.5 * 0.4; self.gain = 0.015; self.wet1 = 0.33 * 3.0 * (0.5 + 0.5); self.wet2 = 0.0

    def process(self, L, R):
        oL = []; oR = []
        for xl, xr in zip(L, R):
            inp = (xl + xr) * self.gain; outs = []
            for ch in (0, 1):
                acc = 0.0
                for k in range(8):
                    b = self.cb[ch][k]; i = self.ci[ch][k]; y = b[i]
                    self.lp[ch][k] = y * (1 - self.damp) + self.lp[ch][k] * self.damp
                    b[i] = inp + self.lp[ch][k] * self.fb; self.ci[ch][k] = (i + 1) % len(b); acc += y
                for k in range(4):
                    b = self.ab[ch][k]; i = self.ai[ch][k]; bo = b[i]; b[i] = acc + bo * 0.5; acc = bo - acc
                    self.ai[ch][k] = (i + 1) % len(b)
                outs.append(acc)
            oL.append(outs[0] * self.wet1 + outs[1] * self.wet2); oR.append(outs[1] * self.wet1 + outs[0] * self.wet2)
        return oL, oR


# ------------------------------------------------------------------------------------------------------------------------
TEMPO_FN = emu.SENTINEL + 0x240
PROC = {"send": {"block": 0x119994, "vt": 0x842d40}, "master": {"block": 0x112acc, "vt": 0x842aa8}}


class ProcRig:
    """Stand-in Send/Master FX processor (as in H043) with the real SendFxReverb at array index 1 (selected index +0xa0/+0xa4 = 1);
    the Send mute smoother 0xe8050/0xe808c is neutralised; tempo source stubbed (logged)."""
    def __init__(self, which, pre=()):
        self.which = which
        self.x = x = EmuSendReverb(defaults=which, activate=False); e = self.e = x.e
        for idx, v in pre: x.set(idx, v)
        self.resets = 0; self.tempo_calls = 0; self.cap = {}
        for a_ in (0xe8050, 0xe808c): e.add_watch(a_, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        def tempo(em):
            self.tempo_calls += 1; u = emu.d2u(120.0); em.setr(0, u & 0xffffffff); em.setr(1, u >> 32)
            em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
        e.add_watch(TEMPO_FN, tempo)
        e.add_watch(0x11208c, lambda em: setattr(self, "resets", self.resets + 1))
        tvt = e.malloc(64); e.w32(tvt + 0x1c, TEMPO_FN); tob = e.malloc(8); e.w32(tob, tvt)
        self.proc = p = e.malloc(0x148); arr = e.malloc(40)
        for k in range(10): e.w32(arr + 4 * k, x.o if k == 1 else 0)
        e.w32(p, PROC[which]["vt"]); e.w32(p + 0x80, arr); e.w32(p + 0x84, 10); e.w32(p + 0x88, 10); e.w32(p + 0x94, tob)
        e.wr(p + 0x9c, b"\x00\x01\x00\x00"); e.w32(p + 0xa0, 1); e.w32(p + 0xa4, 1); e.w32(p + 0xa8, e.malloc(0x40))
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
H043_REC = {"h043_report.txt": ("29227f2c", "4b8b"), "h043.json": ("0f8fe70a", "8ba1")}
H043_F32 = ("b6b3f9b5", "53a6f")
H043_REGRESS = ("0962b163", "7c29")
RCODE = (0x10e2e0, 0x112680)        # Reverb9NXSBase / ReverbAllPass / ReverbComb / ReverbPreDelay / SendFxReverb code range


def regress(out):
    """Re-run H043 (its recorded report/json/f32 hashes) and H043 --regress (= H055 + H055 --regress = H010 + H009 + H021..H041)."""
    import subprocess, glob
    d = os.path.join(out, "regress", "H043"); d2 = os.path.join(out, "regress", "H043r")
    os.makedirs(d, exist_ok=True); os.makedirs(d2, exist_ok=True)
    p1 = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "H043_send_delay_model.py"), "--jobs", "5", "--out", d],
                          stdout=open(os.path.join(out, "regress", "H043.log"), "w"), stderr=subprocess.STDOUT)
    p2 = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, "H043_send_delay_model.py"), "--regress", "--out", d2],
                          stdout=open(os.path.join(out, "regress", "H043r.log"), "w"), stderr=subprocess.STDOUT)
    rc1 = p1.wait(); rc2 = p2.wait()
    got = {k: sha(open(os.path.join(d, k), "rb").read()) for k in H043_REC if os.path.exists(os.path.join(d, k))}
    f32s = sha(b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(d, "*.f32")))))
    ok1 = rc1 == 0 and all(got.get(k, "").startswith(v[0]) and got.get(k, "").endswith(v[1]) for k, v in H043_REC.items()) and \
        f32s.startswith(H043_F32[0]) and f32s.endswith(H043_F32[1])
    rp = os.path.join(d2, "h043_regress.txt"); rtxt = open(rp).read() if os.path.exists(rp) else ""
    rs = sha(rtxt.encode()) if rtxt else ""
    ok2 = rc2 == 0 and rs.startswith(H043_REGRESS[0]) and rs.endswith(H043_REGRESS[1]) and "all recorded hashes reproduced" in rtxt
    txt = ("H043 rc %d %s report %s json %s f32 %s\nH043 --regress rc %d %s h043_regress.txt %s\n--- h043_regress.txt:\n%s"
           "REGRESSION: %s\n" % (rc1, "OK " if ok1 else "BAD", got.get("h043_report.txt", "-"), got.get("h043.json", "-"), f32s,
                                rc2, "OK " if ok2 else "BAD", rs, rtxt,
                                "all recorded hashes reproduced" if ok1 and ok2 else "MISMATCH"))
    open(os.path.join(out, "h005_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok1 and ok2 else 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H005"))
    ap.add_argument("--skip-matrix", action="store_true"); ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--regress", action="store_true", help="only re-run H043 and H043 --regress and compare the recorded hashes")
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
    P("H005 SendFxReverb end-to-end — target sha256 %s" % emu.SHA)
    im = sp16img.Image()
    lo, hi = im.sec[".text"]; o0 = im.off(lo); nw = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % nw, im.data, o0)

    # ---------------------------------------------------------------------------------------------------------- C1
    P("\n== C1 Freeverb / juce::Reverb test")
    combs = [1116, 1188, 1277, 1356, 1422, 1491, 1557, 1617]; aps = [556, 441, 341, 225]
    arr16 = struct.pack("<8h", *combs); arr32 = struct.pack("<8i", *combs); ap16 = struct.pack("<4h", *aps); ap32 = struct.pack("<4i", *aps)
    hits = {nm: im.data.count(b_) for nm, b_ in (("comb int16 array", arr16), ("comb int32 array", arr32), ("allpass int16 array", ap16),
                                                  ("allpass int32 array", ap32))}
    P("  tuning arrays anywhere in the file: %s" % hits)
    J["freeverb_arrays"] = hits
    # movw / mov-immediate sites of the tuning numbers in .text (whole image and inside the reverb code range)
    def imm_sites(val):
        out = []
        for k, w in enumerate(W):
            if (w >> 28) == 0xf: continue
            if (w & 0x0ff00000) == 0x03000000 and (((w >> 4) & 0xf000) | (w & 0xfff)) == val: out.append(lo + 4 * k)
            elif (w & 0x0fe00000) in (0x03a00000,) :
                rot = ((w >> 8) & 0xf) * 2; imm = w & 0xff; v = ((imm >> rot) | (imm << (32 - rot))) & 0xffffffff if rot else imm
                if v == val: out.append(lo + 4 * k)
            elif w == val: out.append(lo + 4 * k)
        return out
    tun = {}
    for v in combs + aps + [23]:
        s_ = imm_sites(v); tun[v] = (len(s_), sum(1 for x_ in s_ if RCODE[0] <= x_ < RCODE[1]))
    P("  tuning-number immediate/literal sites (whole .text, inside reverb code 0x10e2e0..0x112680): %s" % tun)
    J["freeverb_imm_sites"] = tun
    fl_lits = {"0.015f": 0x3c75c28f, "0.28f": 0x3e8f5c29, "0.7f": 0x3f333333, "0.4f": 0x3ecccccd, "3.0f": 0x40400000, "2.0f": 0x40000000}
    lit = {}
    for nm, b_ in fl_lits.items():
        s_ = [lo + 4 * k for k, w in enumerate(W) if w == b_]
        lit[nm] = (len(s_), [hex(x_) for x_ in s_ if RCODE[0] <= x_ < RCODE[1]])
    P("  float literal words (count in .text, sites inside reverb code): %s" % lit)
    J["freeverb_float_lits"] = lit
    names = sorted(set(m_.group().decode() for m_ in __import__("re").finditer(rb"[0-9]+[A-Za-z_0-9]*Reverb[A-Za-z_0-9]*", im.data)))
    juce_rev = [n_ for n_ in names if "juce" in n_.lower()]
    P("  RTTI-style names containing 'Reverb': %s; containing 'juce': %s" % (names, juce_rev))
    J["reverb_names"] = names
    # the JUCE library copy of Freeverb: juce::Reverb (header-only, no RTTI) is inlined into juce::ReverbAudioSource code
    tsites = sorted(set(x_ for v in combs for x_ in imm_sites(v)))
    owners = sorted(set(hex(im.func_of(x_)[0]) for x_ in tsites))
    calls = im.direct_calls()
    out_tg = sorted(set(t_ for s_, t_, k_ in calls if RCODE[0] <= s_ < RCODE[1] and not (RCODE[0] <= t_ < RCODE[1]) and k_ != "b"))
    P("  Freeverb comb-tuning sites %s in exidx function(s) %s (Ghidra FUN_00585680 = juce::Reverb::setSampleRate inlined; callers "
      "0x5755ec / 0x582cbc of juce::ReverbAudioSource vt 0x933118)" % ([hex(x_) for x_ in tsites], owners))
    P("  direct-call targets of the reverb code outside it: %s" % [hex(t_) for t_ in out_tg])
    J["juce_freeverb_sites"] = [hex(x_) for x_ in tsites]; J["reverb_call_targets"] = [hex(t_) for t_ in out_tg]
    vt_slots = [im.u32(0x842618 + 4 * k) for k in range(36)] + [im.u32(0x8426b0 + 4 * k) for k in range(19)] + \
        [im.u32(0x842380 + 4 * k) for k in range(19)]
    juce_rev_code = (0x570000, 0x590000)
    check(hits["comb int16 array"] == 0 and hits["comb int32 array"] == 0 and
          all(t_[1] == 0 for v_, t_ in tun.items() if v_ != 23) and lit["0.015f"][1] == [] and lit["0.28f"][1] == [] and
          all(not (0x582c00 <= t_ < 0x586100) for t_ in out_tg + vt_slots),
          "Freeverb constants exist only in the JUCE library (juce::ReverbAudioSource / juce::Reverb, 0x582cbc..0x586068); none in the "
          "SendFxReverb code, and neither its calls nor its 3 vtables reach that code")
    m0 = M.SendReverb(); m0.defaults(); m0.reset()
    rows = []
    for room in (1, 50, 100):
        s = M.room_scale(room)
        rows.append((room, [(round(F(s * ml), 4), round(F(s * mr), 4), int(F(F(F(s * ml) * F(0.001)) * F(44100.0))),
                             int(F(F(F(s * mr) * F(0.001)) * F(44100.0)))) for ml, mr in M.COMB_MS]))
    for room, cs_ in rows: P("  room %3d: comb (L ms, R ms, L smp, R smp) = %s" % (room, cs_))
    P("  allpass delays (samples, truncated read): %s, gain 0.7; Freeverb: combs %s (+23 R), allpasses %s, g 0.5" %
      ([(int(a_.dsamp[0]), int(a_.dsamp[1])) for a_ in m0.aps], combs, aps))
    J["comb_table"] = rows

    # ---------------------------------------------------------------------------------------------------------- C2
    P("\n== C2 parameters")
    x = EmuSendReverb(defaults=None, activate=False, log_regs=True)
    for r_ in x.regs:
        P("  reg %-15s off +0x%03x id %d %-16s min %s max %s default %s" % (r_["kind"], r_["off"], r_["id"], r_["name"], r_["min"],
                                                                         r_["max"], r_["default"]))
    J["registrations"] = x.regs
    check([r_["name"] for r_ in x.regs] == list(M.PARAM_NAMES.values()) and [r_["default"] for r_ in x.regs] ==
          [M.CTOR_DEFAULTS[i] for i in range(6)], "6 LinearParameters 0..1, ctor defaults 0.5/0.5/0/0/0/0 (model CTOR_DEFAULTS)")
    rc = {}
    for idx in (0, 1, 2, 3, 4, 5, 6, 7, 12, 0xffffffff): rc[idx] = x.set(idx, 0.25)
    P("  slot 14 return codes for indices: %s" % {hex(k_) if k_ > 99 else k_: v for k_, v in rc.items()})
    check(all(rc[i] == 0 for i in range(6)) and all(rc[i] == 3 for i in (6, 7, 12, 0xffffffff)), "slot 14: indices 0..5 accepted, others return 3")
    curs = [u2f(x.u(x.o + off + 0x28)) for off in PARAM_OFF]
    check(curs == [0.25] * 6, "slot 14 stores the value in Parameter +0x28 (cur) of +0x244 + 0x5c i")
    xa, xb = EmuSendReverb("send"), EmuSendReverb("master")
    da = [(i_, hex(v_)) for i_, v_ in xa.defaults_s14]; db = [(i_, hex(v_)) for i_, v_ in xb.defaults_s14]
    P("  slot-52 defaults index 1: Send %s / Master %s" % (da, db))
    J["defaults"] = {"send": da, "master": db}
    check(xa.defaults_s14 == M.SEND_DEFAULTS and xb.defaults_s14 == M.MASTER_DEFAULTS,
          "slot-52 defaults = model (Send MIX 1.0, Master 0.5; PRE DELAY 0, ROOM 49/99, REVERB TIME 49/99, LPF 0, SPREAD 0)")
    tabs = {nm: [im.u32(base + 4 * k) for k in range(10)] for nm, base in (("send", 0x119a40), ("master", 0x112b4c))}
    feed = {nm: sorted(k for k in range(10) if t_[k] == t_[0]) for nm, t_ in tabs.items()}
    P("  processBlock jump tables: Send 0x119a40 idx1 -> 0x%x (tempo feed for %s), Master 0x112b4c idx1 -> 0x%x (feed %s)" %
      (tabs["send"][1], feed["send"], tabs["master"][1], feed["master"]))
    check(1 not in feed["send"] and 1 not in feed["master"], "index 1 (Reverb) gets no per-block tempo/parameter feed")
    # nothing applies at set time: state equal before/after a set, differs after the next slot 25
    s0 = xa.state(); xa.set(1, 0.9); xa.set(0, 0.7); xa.set(2, 0.1); xa.set(3, 0.6); xa.set(4, 0.55); xa.set(5, 0.3); s1 = xa.state()
    imm = sorted(k_ for k_ in s1 if s1[k_] != s0[k_] and not k_.startswith("p"))
    xa.process([F(0.0)] * N, [F(0.0)] * N); s2 = xa.state()
    later = sorted(k_ for k_ in s2 if s2[k_] != s1[k_])
    P("  fields changed by set() alone: %s; changed by the next slot 25: %d fields (%s ...)" % (imm, len(later), later[:8]))
    check(imm == [] and len(later) > 10, "slot 14 only stores; everything takes effect at the next slot 25 (no immediate apply)")

    # ---------------------------------------------------------------------------------------------------------- C3
    P("\n== C3 formula sweeps (emulated read-back vs model, full state after one silent block per value)")
    def sweep(idx, vals, keys):
        x_, m_ = new_pair(); bad = 0; tab = []
        for v in vals:
            x_.set(idx, v); m_.set_param(idx, v)
            x_.process([F(0.0)] * N, [F(0.0)] * N); m_.process([F(0.0)] * N, [F(0.0)] * N)
            dd = diff(x_.state(), model_state(m_))
            if dd: bad += 1
            st = x_.state(); tab.append((v, [st[k_] if not isinstance(st[k_], list) else st[k_][:3] for k_ in keys]))
        return bad, tab
    SW = [(0, [0.0, 0.0009, 0.001, 0.0011, 0.25, 0.5, 0.999, 1.0, 1.2, -0.1], ["pd"]),
          (1, [0.0, 0.0101, 0.010101, 0.0102, 0.5, 49 / 99, 0.999, 1.0, 1.0101, -0.01], ["r9.room"]),
          (2, [0.0, 0.05, 0.09, 0.0901, 0.3, 0.5137255, 0.5138, 0.75, 1.0, 1.05], ["r9.gain", "c0.gain"]),
          (3, [0.0, 0.005, 0.0101, 0.0102, 0.5, 0.99, 0.9999, 1.0, 1.1], ["r9.lpfstep", "c0.lpf"]),
          (4, [0.0, 0.1, 0.1999, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], ["c0.spr", "c4.spr"]),
          (5, [0.0, 0.3, 0.7499, 0.75, 0.9, 1.0], ["dry+0x46c", "wet+0x470", "eb.wet+0x14"])]
    totbad = 0
    for idx, vals, keys in SW:
        bad, tab = sweep(idx, vals, keys); totbad += bad
        P("  %-16s %2d values, state mismatches %d" % (M.PARAM_NAMES[idx], len(vals), bad))
        for v, ks in tab[:12]: P("     v=%-10.6g %s" % (v, ks))
        J.setdefault("sweeps", {})[M.PARAM_NAMES[idx]] = tab
    check(totbad == 0, "all parameter sweeps: emulated state == model state after every step")
    # direct read-back of the coefficient routine SFR slot 33 0x11185c for (room, REVERB TIME) pairs: comb targets ms/gain/input gain
    xd, md = new_pair(); bad = 0; n_ = 0; gtab = []
    for rt in (0.0, 0.05, 0.09, 0.0901, 0.3, 49 / 99, 0.7, 1.0):
        xd.set(2, rt); md.set_param(2, rt)
        for room in (1, 2, 25, 50, 75, 99, 100):
            xd.e.w32(xd.r9 + 0x5c, room); md.room_cur = room
            xd.e.call(0x11185c, xd.o); md.slot17(); n_ += 1
            se, sm = xd.state(), model_state(md)
            ks = [k_ for k_ in se if k_.endswith((".dly", ".gain", ".spr")) or k_ == "r9.gain"]
            if any(not _eq(se[k_], sm[k_]) for k_ in ks): bad += 1
            if room in (1, 50, 100):
                gtab.append((rt, room, float(M.reverb_time(rt)), [round(u2f(se["c%d.gain" % c_][4]), 6) for c_ in range(5)]))
    for r_ in gtab: P("     RT v=%-8.5g room %3d T60=%-9.4g s comb L gains %s" % r_)
    P("  slot 33 direct calls: %d (REVERB TIME x room) pairs, mismatches %d" % (n_, bad))
    J["rt_table"] = gtab
    check(bad == 0, "comb delay/gain/spread targets and input gain from slot 33 == model for 56 (REVERB TIME, room) pairs")
    bad = 0; n_ = 0
    for cur in (1, 30, 50, 100):
        for tgt in (1, 31, 50, 80, 100):
            for prev in (20.0, 20.5, 26.0, 33.3333, 39.5, 40.0, 41.0):
                r0, _ = xd.e.call(0x111780, xd.o, cur, tgt, f2u(F(prev))); n_ += 1
                if r0 != f2u(M.glide_time(cur, tgt, prev)): bad += 1
    P("  glide-time routine 0x111780: %d (cur, tgt, prev) cases, mismatches %d (t = max(20, prev -> 40 - 2/3 |cur - tgt| by 2/3 ms))" % (n_, bad))
    check(bad == 0, "glide-time routine == model")

    # ---------------------------------------------------------------------------------------------------------- C5 matrix
    hashes = {}
    if not a.skip_matrix:
        P("\n== C5 end-to-end matrix (emulated slot 25 vs model; full state compared after every block, all rings at the end)")
        jobs, outs = run_parallel("matrix", a.jobs, os.path.join(a.out, "work"))
        allok = True; tot = 0; res_ = []
        for jb, (r_, blob) in zip(jobs, outs):
            ok = r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None and r_["final_ring_equal"]
            allok &= ok; tot += r_["samples"]; res_.append(r_)
            P("  %-7s %-36s %-7s %5d blk  mism %d  max|err| %g  nonzero %6d first_nz_blk %s  state %s  rings %s" % (
                jb[0], jb[1], jb[4], r_["blocks"], r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"],
                r_["first_nonzero_block"], "eq" if r_["first_state_diff"] is None else r_["first_state_diff"],
                "eq" if r_["final_ring_equal"] else "DIFF"))
            fn = "%s__%s.f32" % (jb[1].replace("/", "_"), jb[4]); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
        J["matrix"] = res_
        check(allok, "matrix: %d runs, %d output samples, all bit-exact with state and rings equal" % (len(jobs), tot))
        check(all(r_["nonzero_out"] > 0 for r_ in res_ if r_["signal"] != "silence"), "every non-silent run produced reverb output")
    return main_part2(a, P, check, fails, rep, J, im, hashes)


def main_part2(a, P, check, fails, rep, J, im, hashes):
    # ---------------------------------------------------------------------------------------------------------- C6
    P("\n== C6 start-up, reset, retrigger")
    def nz(xs): return sum(1 for v in xs if v != 0.0)
    # (a) start-up after activation: output gated by the comb/allpass warm-up (count > len = 4454 samples) + 3 ms fade
    r_, _ = run_case("startup_impulse_t0", [], {}, "impulse", 120)
    P("  activated, impulse at t=64: first non-zero output block %s (sample >= 4455 -> block 69)" % r_["first_nonzero_block"])
    check(r_["first_nonzero_block"] == 69 and r_["mismatched_samples"] == 0, "start-up: no output before block 69 (101 ms warm-up gate)")
    # (b) never activated (no slot 27 / slot 23): LPF/HPF coefficients 0, allpass delays/gains 0, output gain 0 -> silent
    r_, _ = run_case("no_activation_noise", [], {}, "noise", 300, activate=False)
    P("  NOT activated, noise 300 blocks: non-zero outputs %d, mismatches %d, state %s" % (r_["nonzero_out"], r_["mismatched_samples"],
                                                                                          "eq" if r_["first_state_diff"] is None else "DIFF"))
    check(r_["nonzero_out"] == 0 and r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None,
          "without the activation reset the reverb is silent (fixed filters/allpasses/out gain only set by R9 slot 16)")
    # (c) slot 27 reset mid-run: rings kept, write indices rewound, gates closed -> stale tail resurfaces after the warm-up
    x, m = new_pair()
    L, R = signal("noise", 200)
    for blk in range(200): x.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]); m.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
    rb = x.rings(); nzb = [nz(struct.unpack("<%df" % (len(b_) // 4), b_)) for b_ in rb]
    x.reset(); m.reset(); ra = x.rings()
    st = x.state()
    out_after = []; same = True
    for blk in range(120):
        eL, eR = x.process([F(0.0)] * N, [F(0.0)] * N); mL, mR = m.process([F(0.0)] * N, [F(0.0)] * N)
        same &= [f2u(v) for v in eL + eR] == [f2u(v) for v in mL + mR]; out_after.append(nz(eL + eR))
    first = next((k for k, v in enumerate(out_after) if v), None)
    P("  reset after 200 noise blocks: ring non-zero counts before %s; rings unchanged by reset: %s; comb w/count/fade after reset %s;"
      " silence afterwards -> first non-zero output block %s (stale ring content), model bit-exact %s" % (
          nzb[:4], ra == rb, st["c0.pos"][:4], first, same))
    check(ra == rb and first is None and same, "slot 27 keeps all rings (no clear), but the warm-up gate (len samples = ring length) "
          "overwrites them before it opens: with PRE DELAY 0 the old tail never resurfaces")
    x, m = new_pair()
    x.set(0, 1.0); m.set_param(0, 1.0)
    for blk in range(200): x.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]); m.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
    x.reset(); m.reset(); out2 = []; same2 = True
    for blk in range(150):
        eL, eR = x.process([F(0.0)] * N, [F(0.0)] * N); mL, mR = m.process([F(0.0)] * N, [F(0.0)] * N)
        same2 &= [f2u(v) for v in eL + eR] == [f2u(v) for v in mL + mR]; out2.append(nz(eL + eR))
    first2 = next((k for k, v in enumerate(out2) if v), None)
    P("  same with PRE DELAY 100 ms: silence after the reset -> first non-zero output block %s, non-zero samples %d (stale pre-delay "
      "ring content read during its own 4-sample-threshold fade feeds the combs), model bit-exact %s" % (first2, sum(out2), same2))
    check(same2, "reset with a long pre-delay: model bit-exact (stale content behaviour reproduced)")
    # (c3) out-of-bounds pre-delay read: PRE DELAY 0.1 (10 ms) -> target 441.00003 samples, pos = w - D rounds up to the ring length
    x, m = new_pair(); x.set(0, 0.1); m.set_param(0, 0.1); bad = 0
    L, R = signal("noise", 300, seed=3)
    x.process([F(0.0)] * N, [F(0.0)] * N); m.process([F(0.0)] * N, [F(0.0)] * N); x.reset(); m.reset()   # D = 441.00003 at once
    for blk in range(300):
        eL, eR = x.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]); mL, mR = m.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
        bad += sum(1 for p_, q_ in zip(eL + eR, mL + mR) if f2u(p_) != f2u(q_))
    P("  PRE DELAY 0.1: model out-of-bounds pre-delay reads %d in 300 blocks (one per ring cycle and channel), mismatches vs emulation %d "
      "(emulator heap padding after the ring is zero)" % (m.pd.oob, bad))
    check(m.pd.oob > 0 and bad == 0, "pre-delay reads one float past its ring for 10/20/30/40/60/80/90 ms (zero padding in the emulator)")
    xh = EmuSendReverb(heap_fill=0xA5); xh.set(0, 0.1); mh = M.SendReverb(); mh.defaults(); mh.reset(); mh.set_param(0, 0.1); badh = 0
    xh.process([F(0.0)] * N, [F(0.0)] * N); mh.process([F(0.0)] * N, [F(0.0)] * N); xh.reset(); mh.reset()
    for blk in range(300):
        eL, eR = xh.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]); mL, mR = mh.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
        badh += sum(1 for p_, q_ in zip(eL + eR, mL + mR) if f2u(p_) != f2u(q_))
    xh2 = EmuSendReverb(heap_fill=0xA5); mh2 = M.SendReverb(); mh2.defaults(); mh2.reset(); badh2 = 0
    for blk in range(300):
        eL, eR = xh2.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]); mL, mR = mh2.process(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
        badh2 += sum(1 for p_, q_ in zip(eL + eR, mL + mR) if f2u(p_) != f2u(q_))
    P("  heap filled with 0xA5: PRE DELAY 0.1 mismatches %d (the past-the-end word 0xA5A5A5A5 = -2.9e-16 replaces the dropped sample; too small "
      "to change any output bit here); Send defaults mismatches %d" % (badh, badh2))
    J["oob"] = {"pd_oob_reads": m.pd.oob, "mism_zero_heap": bad, "mism_A5_pd.1": badh, "mism_A5_defaults": badh2}
    check(badh2 == 0, "with a 0xA5 heap the default setting stays bit-exact (no other uninitialised-memory dependence)")
    # (d) slot 5 activation (e, 0, 0) / (e, 0, 1) and slot 10
    for args in ((0, 0), (0, 1)):
        xs = EmuSendReverb(defaults="send", activate=False); calls = []
        xs.e.add_watch(0x11208c, lambda em: calls.append(1))
        xs.e.vcall(xs.o, 5, *args)
        P("  EffectBase slot 5 %s on a fresh object -> slot 27 calls %d" % (args, len(calls)))
        J.setdefault("slot5", {})[str(args)] = len(calls)
    xs = EmuSendReverb(defaults="send"); s0 = xs.state(); r10 = xs.e.vcall(xs.o, 10)[0]; s1 = xs.state()
    P("  slot 10 (0x%x) returns %d, state changed: %s" % (im.u32(0x842618 + 40), r10, s0 != s1))
    calls = im.direct_calls(); clears = sorted(set(hex(s_) for s_, t_, k_ in calls if t_ == 0x57861c and RCODE[0] <= s_ < RCODE[1]))
    P("  ring clear (0x57861c) call sites inside the reverb code: %s (constructors only)" % clears)
    J["clear_sites"] = clears

    # ---------------------------------------------------------------------------------------------------------- C7
    P("\n== C7 Send vs Master")
    sites = sorted(hex(s_) for s_, t_, k_ in calls if t_ == CTOR)
    P("  ctor call sites of 0x1123d0: %s" % sites)
    J["ctor_sites"] = sites
    def ctx(site): return [im.u32(site - 4 * k) for k in range(1, 5)]
    if len(sites) == 2:
        a_, b_ = (int(s_, 16) for s_ in sites)
        same_w = [im.u32(a_ - 4 * k) == im.u32(b_ - 4 * k) for k in (1, 2, 3, 5, 6)]
        P("  movw r0,#0x478 / bl new / movw r1,#0xac44 / mov r2,#0x40 / mov r5,r0 words identical at both sites: %s" % same_w)
        check(all(same_w), "Master 0x114c88 and Send 0x11bcb4 build the reverb identically: new(0x478), ctor(obj, 44100, 64)")
    pres = {}
    for which in ("send", "master"):
        rig = ProcRig(which, pre=[(1, 0.6), (2, 0.7), (4, 0.35)])
        m = M.SendReverb(); m.defaults(master=(which == "master"))
        for idx, v in [(1, 0.6), (2, 0.7), (4, 0.35)]: m.set_param(idx, v)
        L, R = signal("noise", 300, seed=5); bad = 0; resets = 0; s14 = 0; stbad = 0
        for blk in range(300):
            if blk == 150:
                rig.x.set(1, 0.2); m.set_param(1, 0.2)
            (oL, oR), nres, s14l = rig.block(L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N])
            resets += nres; s14 += len(s14l)
            if nres: m.reset()
            iL, iR = rig.cap["in"][3], rig.cap["in"][4]
            mL, mR = m.process(iL, iR)
            eL, eR = rig.cap["out"]
            bad += sum(1 for p_, q_ in zip(eL + eR, mL + mR) if f2u(p_) != f2u(q_))
            if diff(rig.x.state(), model_state(m)): stbad += 1
        pres[which] = (bad, stbad, resets, rig.tempo_calls, s14)
        P("  %-6s processBlock rig 300 blocks: slot-25 mismatches %d, state-diff blocks %d, slot-27 resets %d, tempo calls %d, slot-14 "
          "feeds %d" % ((which,) + pres[which]))
    J["proc_rigs"] = pres
    check(all(v[0] == 0 and v[1] == 0 and v[2] == 1 and v[3] == 0 and v[4] == 0 for v in pres.values()),
          "Send and Master processBlock: same class, slot 25 bit-exact with the model, 1 activation reset, no tempo/parameter feed")

    # ---------------------------------------------------------------------------------------------------------- C8
    P("\n== C8 alternatives")
    jobs, outs = run_parallel("mutants", a.jobs, os.path.join(a.out, "work"))
    mres = []
    for (nm_, fn_, case, sig, nb), (r_, _) in zip(MUTANTS, outs):
        caught = r_["mismatched_samples"] > 0 or not r_["final_ring_equal"]
        mres.append((nm_, case, sig, r_["mismatched_samples"], r_["max_abs_err"], caught))
        P("  mutant %-24s on %-34s %-7s mism %6d  max|err| %-10.4g -> %s" % (nm_, case, sig, r_["mismatched_samples"], r_["max_abs_err"],
                                                                            "CAUGHT" if caught else "not caught"))
    J["mutants"] = mres
    check(all(m_[5] for m_ in mres), "all %d alternative models are refuted by emulation" % len(mres))
    # (a) full Freeverb vs the emulated impulse response (send defaults, activation, impulse at sample 0 of block 80)
    x, m = new_pair(); fv = Freeverb(); nb = 300
    eL_all = []; fL_all = []
    for blk in range(nb):
        L = [F(1.0) if (blk == 80 and k == 0) else F(0.0) for k in range(N)]    # after the 69-block warm-up gate
        eL, _ = x.process(L, [F(0.0)] * N); fL, _ = fv.process(L, [0.0] * N); eL_all += eL; fL_all += fL
    def first_nz(v): return next((k for k, s_ in enumerate(v) if abs(s_) > 1e-9), None)
    def corr(p_, q_):
        mp = sum(p_) / len(p_); mq = sum(q_) / len(q_)
        num = sum((u - mp) * (v - mq) for u, v in zip(p_, q_)); den = math.sqrt(sum((u - mp) ** 2 for u in p_) * sum((v - mq) ** 2 for v in q_))
        return num / den if den else 0.0
    P("  impulse response L (send defaults): first non-zero sample emulated %s vs Freeverb %s; correlation %.4f" % (
        first_nz(eL_all), first_nz(fL_all), corr(eL_all, fL_all)))
    J["freeverb_ir"] = {"first_emu": first_nz(eL_all), "first_freeverb": first_nz(fL_all), "corr": corr(eL_all, fL_all)}
    check(abs(corr(eL_all, fL_all)) < 0.2 and first_nz(eL_all) != first_nz(fL_all), "(a) Freeverb impulse response does not match")
    # (b) true stereo: L-only input -> R output and vice versa (comb rings per channel; spread 0 keeps channels apart before the allpasses)
    r_, blob = run_case("Lonly_spread0", [], {}, "Lonly", 200)
    vals = struct.unpack("<%df" % (len(blob) // 4), blob); rnz = sum(1 for k in range(len(vals)) if (k // N) % 2 == 1 and vals[k] != 0.0)
    P("  (b) L-only input, spread 0: non-zero R output samples %d (true stereo, no mono sum)" % rnz)
    check(rnz == 0, "(b) with spread 0 an L-only input produces no R output: separate L/R paths (not mono-summed)")
    r_, blob = run_case("Lonly_spread1", [(4, 1.0)], {}, "Lonly", 200)
    vals = struct.unpack("<%df" % (len(blob) // 4), blob); rnz = sum(1 for k in range(len(vals)) if (k // N) % 2 == 1 and vals[k] != 0.0)
    P("  (b) L-only input, spread 1: non-zero R output samples %d (cross feedback)" % rnz)
    check(rnz > 0 and r_["mismatched_samples"] == 0, "(b) spread 1 swaps the feedback L<->R (R output appears), bit-exact")

    # ---------------------------------------------------------------------------------------------------------- outputs
    P("\nRESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  FAILED: " + f_)
    cat = b"".join(open(os.path.join(a.out, k_), "rb").read() for k_ in sorted(hashes))
    J["f32_hashes"] = hashes; J["f32_concat_sha256"] = sha(cat) if hashes else None
    P("f32 files: %d, sorted concatenation sha256 %s" % (len(hashes), J["f32_concat_sha256"]))
    open(os.path.join(a.out, "h005_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h005.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
