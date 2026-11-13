#!/usr/bin/env python3
"""H031 — shared vtable-less oscillator (ctor 0x100af0 -> init 0x100710, process 0x101bdc) of the 1.60 FX code: emulation of
the real routines vs the own-code model harness/models/osc.py, plus its configuration in c_chorus / c_flanger / c_distortion /
Phaser / LfoProcessor and harness construction of the inline-built Chorus / Flanger / Distortion effects.

Sections (criteria of kb/cycles/009.md):
  C1  layout: every field written by the ctor/init (emulated object dump vs model), entry points, id counter / random table.
  C2  waveforms: out-of-range waveform values, hold mode, per-waveform shape facts read back from emulation.
  C3  model vs emulation matrix: 7 waveforms x >= 6 settings (>= 32 calls x n = 64, variable n, mid-run setters), output
      and full object state compared bit-exactly after every call.
  C4  configuration per user: oscillator setter calls logged during construction, Insert defaults, first block, slot-14 changes.
  C6  construction of Chorus / Flanger / Distortion (inline blocks of InsertFxProcessor ctor 0x118b0c) and slot-25 runs; also
      the C5 role evidence: in-situ oscillator check and a re-statement of the c_chorus / c_flanger kernels with the
      oscillator output as the delay time (bit-exact), plus the amplitude-modulation / constant-delay alternatives.
  C7  alternatives: recursive sine vs direct sin (drift, resync); random = table lookup (memory patch) vs PRNG.
Outputs only to --out (default harness/out/H031/). Run: .venv/bin/python -B harness/H031_osc_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import Emu, EmuAbort, f2u, u2f, d2u, u2d, SP           # noqa: E402
import sp16img                                                 # noqa: E402
import osc as M                                                # noqa: E402

FS = 44100
OSC_SIZE = 0x98
A = dict(ctor=0x100af0, init=0x100710, init_ms=0x100b28, set_freq=0x101090, set_period_ms=0x101320, set_phase=0x1017d4,
         reset_phase=0x101440, set_amp=0x1019d8, set_off=0x1019e4, set_smooth_hz=0x1019f0, set_smooth_off=0x102cb0,
         resync=0x101b30, process=0x101bdc, set_rand_off=0x102c50, set_waveform=0x100b5c)
TABLE = 0xb70e50
ID_COUNTER = 0xb70e4c
NMAX = 64


def sha(b): return hashlib.sha256(b).hexdigest()


def load_table(im):
    """8192 table floats at 0xb70e50 plus the following .data word (index-wrap quirk) — read from the target at run time."""
    return list(struct.unpack_from("<8193f", im.data, im.off(TABLE)))


# ------------------------------------------------------------------------------------------------------------------------
def new_emu():
    e = Emu()
    # libm expf -> feholdexcept reads _rtld_global_ro._dl_hwcap (+0x40); provide HWCAP_VFP (0x40) as on the i.MX6 (cycle 008)
    e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))
    lm, base, _ = e._libs["libm.so.6"]
    for r in lm.dynamic_relocations:
        if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(base + r.address, 0x3d000000)
    return e


class EmuLibm:
    """The real 1.60 libm exports, called through the emulator (oracle for the model's libm calls)."""
    def __init__(self, e):
        self.e = e; self.x = {n: e.lib_exports[n][0] for n in ("sincos", "cos", "acos", "cosf", "sinf", "expf", "acosf")}
        self.tmp = e.malloc(16, "harness: sincos out")
    def _d(self, nm, x):
        u = d2u(x); r0, r1 = self.e.call(self.x[nm], u & 0xffffffff, u >> 32); return u2d(r0 | (r1 << 32))
    def _f(self, nm, x): return u2f(self.e.call(self.x[nm], f2u(x))[0])
    def sincos(self, x):
        u = d2u(x); self.e.call(self.x["sincos"], u & 0xffffffff, u >> 32, self.tmp, self.tmp + 8)
        return struct.unpack("<dd", self.e.rd(self.tmp, 16))
    def cos(self, x): return self._d("cos", x)
    def acos(self, x): return self._d("acos", x)
    def cosf(self, x): return self._f("cosf", x)
    def sinf(self, x): return self._f("sinf", x)
    def expf(self, x): return self._f("expf", x)
    def acosf(self, x): return self._f("acosf", x)


class EmuOsc:
    """One oscillator object built by the real 1.60 ctor 0x100af0 inside a fresh emulator."""
    def __init__(self, wave, freq, fs=FS, id_before=0, rand_off=0, counter=0.0, e=None):
        self.e = e = e or new_emu()
        self.counter_before = e.u32(ID_COUNTER)
        self.o = e.malloc(OSC_SIZE, "harness: oscillator (new 0x98)")
        e.w32(self.o + 8, id_before); e.w32(self.o + 0x88, rand_off); e.w32(self.o + 0x80, f2u(counter))
        r0, _ = e.call(A["ctor"], self.o, wave & 0xffffffff, f2u(freq), fs & 0xffffffff)
        assert r0 == self.o
        self.bl = e.malloc(4 * 4096, "L"); self.br = e.malloc(4 * 4096, "R")

    def call(self, name, *args):
        return self.e.call(A[name], self.o, *[(f2u(a) if isinstance(a, float) else a & 0xffffffff) for a in args])[0]

    def process(self, n, fill=(0.123, -0.456)):
        e = self.e
        e.set_floats(self.bl, [fill[0]] * max(n, 1)); e.set_floats(self.br, [fill[1]] * max(n, 1))
        r0 = e.call(A["process"], self.o, self.bl, self.br, n & 0xffffffff)[0]
        k = max(n, 0)
        return r0, e.floats(self.bl, k), e.floats(self.br, k)

    def state(self):
        e, o = self.e, self.o
        u = lambda a: e.u32(o + a)
        d = lambda a: struct.unpack("<Q", e.rd(o + a, 8))[0]
        return {"amp+0": u(0), "off+4": u(4), "id+8": u(8), "wave+0xc": u(0xc), "freq+0x10": u(0x10), "pad+0x14": u(0x14),
                "inv_fs+0x18": d(0x18), "slope+0x20": d(0x20), "d28": d(0x28), "d30": d(0x30), "d38": d(0x38), "d40": d(0x40),
                "d48": d(0x48), "ph+0x50": u(0x50), "ph2+0x54": u(0x54), "c58": u(0x58), "c5c": u(0x5c), "sm0+0x60": u(0x60),
                "sm1+0x64": u(0x64), "rs_cnt+0x68": u(0x68), "rs_per+0x6c": u(0x6c), "hold+0x70": d(0x70),
                "smooth_off+0x78": d(0x78), "c+0x80": u(0x80), "P+0x84": u(0x84), "r_off+0x88": u(0x88), "r_idx+0x8c": u(0x8c),
                "table+0x90": u(0x90), "pad+0x94": u(0x94)}


def model_state(m):
    fb = lambda x: f2u(x)
    db = lambda x: d2u(x)
    return {"amp+0": fb(m.amp), "off+4": fb(m.off), "id+8": m.id & 0xffffffff, "wave+0xc": m.wave & 0xffffffff, "freq+0x10": fb(m.freq),
            "inv_fs+0x18": db(m.inv_fs), "slope+0x20": db(m.slope), "d28": db(m.d28), "d30": db(m.d30), "d38": db(m.d38),
            "d40": db(m.d40), "d48": db(m.d48), "ph+0x50": fb(m.ph), "ph2+0x54": fb(m.ph2), "c58": fb(m.c58), "c5c": fb(m.c5c),
            "sm0+0x60": fb(m.sm[0]), "sm1+0x64": fb(m.sm[1]), "rs_cnt+0x68": m.rs_cnt, "rs_per+0x6c": m.rs_per,
            "hold+0x70": db(m.hold), "smooth_off+0x78": db(m.smooth_off), "c+0x80": fb(m.c), "P+0x84": fb(m.P),
            "r_off+0x88": m.r_off, "r_idx+0x8c": m.r_idx}


def diff_state(se, sm):
    return [(k, se[k], v) for k, v in sm.items() if se[k] != v]


# ------------------------------------------------------------------------------------------------------------------------
# A run = ctor args + a list of operations. op: ("p", n) process; ("freq", f); ("ms", ms); ("phase", ph); ("reset", ph);
# ("resync",); ("amp", a); ("off", o); ("smooth", hz); ("smooth_off", u); ("rand_off", k)
OPS = {"freq": ("set_freq", "set_frequency"), "ms": ("set_period_ms", "set_period_ms"), "phase": ("set_phase", "set_phase_offset"),
       "reset": ("reset_phase", "reset_phase"), "resync": ("resync", "resync"), "amp": ("set_amp", "set_amplitude"),
       "off": ("set_off", "set_offset"), "smooth": ("set_smooth_hz", "set_smoothing_hz"),
       "smooth_off": ("set_smooth_off", "set_smoothing_off"), "rand_off": ("set_rand_off", "set_rand_offset")}
RET_NONE = ("set_smoothing_off", "set_rand_offset")


def run_case(case, table, libm_kind="own", keep=False):
    """Run one case on emulation and model; compare outputs and full state after every op. Returns a result dict."""
    wave, freq = case.get("ctor_wave", case["wave"]), case["freq"]
    ka = dict(id_before=case.get("id_before", 0), rand_off=case.get("rand_off", 0), counter=case.get("counter", 0.0))
    x = EmuOsc(wave, freq, **ka)
    libm = {"own": M.OwnLibm, "host": M.HostLibm}[libm_kind]() if libm_kind in ("own", "host") else EmuLibm(new_emu())
    m, _ = M.Osc.ctor(wave, freq, FS, x.counter_before, table=table, libm=libm, **ka)
    res = {"name": case["name"], "wave": case["wave"], "calls": 0, "samples": 0, "bit_exact": 0, "max_abs_err": 0.0, "state_diffs": 0,
           "ret_diffs": 0, "first": None, "ops": len(case["ops"])}
    outE, outM = [], []
    bad = diff_state(x.state(), model_state(m))
    if bad: res["state_diffs"] += len(bad); res["first"] = res["first"] or ("ctor", bad[:4])
    for k, op in enumerate(case["ops"]):
        if op[0] == "p":
            n = op[1]
            re, le, rr = x.process(n)
            mo = m.process(n)
            rm = 0 if mo is None else 1
            if mo is None: mo = ([u2f(f2u(0.123))] * max(n, 0), [u2f(f2u(-0.456))] * max(n, 0))
            res["calls"] += 1; res["samples"] += 2 * max(n, 0)
            if re != rm: res["ret_diffs"] += 1
            for a, b in zip(le + rr, mo[0] + mo[1]):
                if f2u(a) == f2u(b): res["bit_exact"] += 1
                else:
                    err = abs(a - b) if a == a and b == b else float("inf")
                    res["max_abs_err"] = max(res["max_abs_err"], err)
                    if res["first"] is None: res["first"] = ("op %d %s" % (k, op), a, b)
            if keep: outE.append((le, rr)); outM.append(mo)
        elif op[0] == "init":                                          # re-init 0x100710(obj, wave, freq, fs)
            re = x.e.call(A["init"], x.o, op[1] & 0xffffffff, f2u(op[2]), op[3])[0]
            rm = m.init(op[1], op[2], op[3])
            if re != rm: res["ret_diffs"] += 1
        else:
            en, mn = OPS[op[0]]
            re = x.call(en, *op[1:])
            rm = getattr(m, mn)(*op[1:])
            if mn not in RET_NONE and re != rm:
                res["ret_diffs"] += 1
                if res["first"] is None: res["first"] = ("ret op %d %s" % (k, op), re, rm)
        bad = diff_state(x.state(), model_state(m))
        if bad:
            res["state_diffs"] += len(bad)
            if res["first"] is None: res["first"] = ("state after op %d %s" % (k, op), bad[:4])
    res["exact"] = res["bit_exact"] == res["samples"] and not res["state_diffs"] and not res["ret_diffs"]
    if keep: res["_outE"] = outE; res["_outM"] = outM; res["_emu"] = x; res["_model"] = m
    return res


def blocks(nb, n=64): return [("p", n)] * nb


def varn(seed, count):
    g = random.Random(seed); return [("p", g.choice([1, 2, 3, 7, 16, 31, 33, 63, 64, g.randint(1, 64)])) for _ in range(count)]


def c3_cases():
    C = []
    for w in range(7):
        nm = "w%d" % w
        C.append({"name": nm + "_slow_0.05Hz", "wave": w, "freq": 0.05, "ops": [("smooth_off", 1)] + blocks(32)})
        C.append({"name": nm + "_7.3Hz_ph0.3_amp_off", "wave": w, "freq": 7.3,
                  "ops": [("smooth_off", 1), ("phase", 0.3), ("amp", 0.5), ("off", 0.5)] + blocks(32)})
        C.append({"name": nm + "_440Hz_ph0.75_smooth50Hz_then2kHz", "wave": w, "freq": 440.0,
                  "ops": [("phase", 0.75), ("amp", 22.05), ("off", 22.25)] + blocks(16) + [("smooth", 2000.0)] + blocks(16)})
        C.append({"name": nm + "_events_3Hz", "wave": w, "freq": 3.0,
                  "ops": [("smooth_off", 1), ("phase", 0.1)] + blocks(8) + [("freq", 11.5)] + blocks(4) + [("ms", 37.5)] + blocks(4)
                  + [("phase", 0.6)] + blocks(4) + [("reset", 0.25)] + blocks(4) + [("resync",)] + blocks(4)
                  + [("amp", 0.3), ("off", -0.2)] + blocks(4) + [("reset", 0.9), ("phase", 0.55), ("freq", 0.003)] + blocks(4)})
        C.append({"name": nm + "_varn_5.5Hz_ph0.45_smooth", "wave": w, "freq": 5.5,
                  "ops": [("phase", 0.45), ("smooth", 300.0)] + varn(100 + w, 60) + [("freq", 17.0)] + varn(200 + w, 20)})
        C.append({"name": nm + "_hold_freq0", "wave": w, "freq": 2.0,
                  "ops": [("smooth_off", 1), ("phase", 0.35)] + blocks(8) + [("freq", 0.0)] + blocks(4) + [("phase", 0.8)] + blocks(4)
                  + [("freq", 4.0)] + blocks(4) + [("smooth_off", 0)] + blocks(4)})
        C.append({"name": nm + "_resync_id98_1kHz", "wave": w, "freq": 1000.0, "id_before": 98,
                  "ops": [("smooth_off", 1), ("phase", 0.2)] + blocks(40)})
    # random-waveform specials: R-lead / L-lead, offset change, index wrap with offset 0x2000 (reads the word after the table)
    C.append({"name": "w6_Llead_ph0.7_randoff", "wave": 6, "freq": 900.0, "rand_off": 0x1ff0,
              "ops": [("smooth_off", 1), ("phase", 0.7)] + blocks(16) + [("rand_off", 0x0123)] + blocks(16)})
    C.append({"name": "w6_wrap_20kHz_off0x2000", "wave": 6, "freq": 20000.0, "rand_off": 0x2000,
              "ops": [("smooth_off", 1), ("phase", 0.25)] + blocks(170)})
    C.append({"name": "w0_long_1kHz_resync", "wave": 0, "freq": 1000.0, "ops": [("smooth_off", 1), ("phase", 0.125)] + blocks(1500)})
    # out-of-range waveform values: init returns 0, wave stays -1, process returns 0 (buffers untouched)
    for w in (7, -1, 100):
        C.append({"name": "invalid_wave_%d" % w, "wave": w, "freq": 2.0, "ops": [("phase", 0.3), ("freq", 5.0), ("reset", 0.1)] + blocks(4)})
    C.append({"name": "w1_init_freq0", "wave": 1, "freq": 0.0, "ops": blocks(2) + [("freq", 3.0)] + blocks(2)})
    # waveform 6 cannot be built by the ctor (init dereferences the table pointer +0x90 before the ctor sets it, C1):
    # build with waveform 1, then re-initialise with 0x100710 (as LfoProcessor 0x134fc4 -> 0x1015c8 does)
    for c in C:
        if c["wave"] == 6:
            c["ctor_wave"] = 1; c["ops"] = [("init", 6, c["freq"], FS)] + c["ops"]
    return C


# ------------------------------------------------------------------------------------------------------------------------
def osc_from_emu(e, q, table):
    """Model oscillator loaded from the raw fields of an emulated 0x98-byte object at q (used to check in-situ blocks)."""
    u = lambda a: e.u32(q + a); f = lambda a: u2f(e.u32(q + a)); d = lambda a: struct.unpack("<d", e.rd(q + a, 8))[0]
    m = M.Osc(table)
    m.amp, m.off, m.id, m.wave, m.freq = f(0), f(4), u(8), (u(0xc) if u(0xc) < 0x80000000 else u(0xc) - (1 << 32)), f(0x10)
    m.inv_fs, m.slope, m.d28, m.d30, m.d38, m.d40, m.d48 = d(0x18), d(0x20), d(0x28), d(0x30), d(0x38), d(0x40), d(0x48)
    m.ph, m.ph2, m.c58, m.c5c, m.sm = f(0x50), f(0x54), f(0x58), f(0x5c), [f(0x60), f(0x64)]
    m.rs_cnt, m.rs_per, m.hold, m.smooth_off = u(0x68), u(0x6c), d(0x70), d(0x78)
    m.c, m.P, m.r_off, m.r_idx = f(0x80), f(0x84), u(0x88), u(0x8c)
    return m


def run_block(e, start, end, regs, scratch_sp=None):
    """Run a straight-line block of the InsertFxProcessor ctor [start, end) with chosen registers (cycle-008 trick)."""
    for i in range(13): e.setr(i, regs.get(i, 0x5a5a5a5a))
    sp = emu.STACK_BASE + emu.STACK_SIZE - 0x2000
    e.uc.reg_write(SP, sp); e.error = None
    e.uc.emu_start(start, end, count=50_000_000)
    if e.error: raise EmuAbort(e.error)
    return [e.r(i) for i in range(13)]


INSERT_BUILD = {   # inline construction blocks inside InsertFxProcessor ctor 0x118b0c (C6)
    "Chorus": dict(index=0, start=0x118b50, end=0x118c68, r0=None, vptr=0x842920, size=0x2b0, kernel=0xff008, ksize=0x100,
                   osc_buf=(0xd0, 0xd4)),
    "Flanger": dict(index=1, start=0x118cd8, end=0x118de0, r0=0x2b0, vptr=0x8429a8, size=0x2b0, kernel=0x100234, ksize=0x118,
                    osc_buf=(0xd8, 0xdc)),
    "Distortion": dict(index=6, start=0x119060, end=0x1190f0, r0=0x1d8, vptr=0x842898, size=0x1d8, kernel=0xfa568, ksize=0x138,
                       osc_buf=None),
}


class EmuInline:
    """Chorus / Flanger / Distortion built by running their inline block of the 1.60 InsertFxProcessor ctor, then the H007
    Insert init (slot 22, 0x106c7c(obj, 1, 10.0f), slot 52 for the index) and the tempo feed (slot 14 index 7 = BPM)."""
    def __init__(self, name, bpm=120.0, log_calls=()):
        import H007_effect_emu as H7
        self.name = name; self.fx = b = dict(INSERT_BUILD[name]); b["insert_index"] = b["index"]
        self.e = e = new_emu(); self.calls = {a_: 0 for a_ in log_calls}; self.osc_snap = None; self.table = None
        self.log = []
        self.osc_calls = 0
        def snap(em):                                  # oscillator state at the moment Osc_process is entered
            self.osc_calls += 1
            if self.table is not None and em.r(0) == self.kernel + 0x28: self.osc_snap = osc_from_emu(em, em.r(0), self.table)
        e.add_watch(A["process"], snap)
        for a_ in log_calls: e.add_watch(a_, lambda em, a_=a_: self.log.append((a_, em.r(1), u2f(em.r(1)), u2f(em.r(2)))))
        self.proc = e.malloc(0x200, "harness: InsertFxProcessor scratch (r4)")
        e.w32(self.proc + 0x84, 64); e.w32(self.proc + 0x88, 0); e.w32(self.proc + 0x80, e.malloc(256, "harness: array"))
        regs = {4: self.proc, 7: 0x841564, 8: 0x841568}     # r7/r8 = "min"/"max" name pointers loaded at 0x118b7c/0x118b84
        if b["r0"] is not None: regs[0] = b["r0"]
        r = run_block(e, b["start"], b["end"], regs)
        self.obj = self.o = r[6]; self.kernel = e.u32(self.o + 0x1b8)
        self.init_log = []
        H7.Run.insert_init(self)
        if name in ("Chorus", "Flanger"): e.vcall(self.o, 14, 7, f2u(bpm))
        self.bl = e.malloc(4 * 64, "L"); self.br = e.malloc(4 * 64, "R")

    def process(self, L, R):
        e = self.e; e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0 = e.vcall(self.o, 25, self.bl, self.br)[0]
        return r0, e.floats(self.bl, 64), e.floats(self.br, 64)


def test_signal(nblk, seed=7):
    g = random.Random(seed); L = []; R = []
    for k in range(64 * nblk):
        L.append(u2f(f2u(0.5 * math.sin(2 * math.pi * 440.0 * k / FS) + g.uniform(-0.1, 0.1))))
        R.append(u2f(f2u(0.5 * math.cos(2 * math.pi * 330.0 * k / FS) + g.uniform(-0.1, 0.1))))
    return L, R


F = M.F


def chorus_kernel_model(e, k, inL, inR, dL, dR):
    """Python re-statement of c_chorus slot 19 0xfe710 (one block, n = 64) from the emulated kernel state at k, using the
    oscillator outputs dL/dR as DELAY TIMES in samples (linear interpolation in a ring buffer), then the start-up gain ramp."""
    n = len(inL); ln = e.u32(k + 0xc0); idx = e.u32(k + 0xcc); flag = e.rd(k + 0xf8, 1)[0]
    bufs = [e.floats(e.u32(k + 0xc4), ln), e.floats(e.u32(k + 0xc8), ln)]
    outs = [[0.0] * n, [0.0] * n]; lnf = F(float(ln))
    for i in range(n):
        fi = F(float(idx)); bufs[0][idx] = inL[i]; bufs[1][idx] = inR[i]
        for ch, d in ((0, dL[i]), (1, dR[i])):
            pos = F(fi - d)
            if pos < 0.0:
                pos = F(pos + lnf); i0 = int(pos)
                if i0 < ln: frac = F(pos - F(float(i0))); om = F(1.0 - frac); i1 = i0 + 1
                else: frac = F(0.0); om = F(1.0); i0 = 0; i1 = 1
            else:
                i0 = int(pos); frac = F(pos - F(float(i0))); om = F(1.0 - frac); i1 = i0 + 1
            if i1 >= ln: i1 = 0
            outs[ch][i] = F(F(frac * bufs[ch][i1]) + F(om * bufs[ch][i0]))
        idx += 1
        if idx >= ln: idx = 0; flag = 1
    g = u2f(e.u32(k + 0xe8)); kd = u2f(e.u32(k + 0xd8))
    target = F(1.0) if flag else F(0.0)
    step = F(F(target - g) * kd)
    for i in range(n):
        g = F(g + step); outs[0][i] = F(g * outs[0][i]); outs[1][i] = F(outs[1][i] * g)
    return outs


def flanger_kernel_model(e, k, inL, inR, dL, dR):
    """Python re-statement of c_flanger slot 19 0xff9ac (one block): DELAY TIME = oscillator output (samples), linear
    interpolation, feedback of the previous output (+0x10c) into the line, delay-dependent gain g(d) = 0.3686..1 (d <= 48)."""
    n = len(inL); ln = e.u32(k + 0xc0); idx = e.u32(k + 0xcc)
    bufs = [e.floats(e.u32(k + 0xc4), ln), e.floats(e.u32(k + 0xc8), ln)]
    fbk = u2f(e.u32(k + 0x10c)); y = [u2f(e.u32(k + 0xf4)), u2f(e.u32(k + 0xf8))]
    def gain(d): return F(F(F(d * F(0.013154167)) + 1.0) - F(0.6314)) if d <= 48.0 else F(1.0)
    gl = [gain(d) for d in dL]; gr = [gain(d) for d in dR]
    outs = [[0.0] * n, [0.0] * n]
    for i in range(n):
        rd = []
        for d in (dL[i], dR[i]):
            r = idx - int(d)
            if r < 0: r += ln
            rd.append(r)
        bufs[0][idx] = F(inL[i] + F(y[0] * fbk)); bufs[1][idx] = F(inR[i] + F(y[1] * fbk))
        idx = idx + 1 if idx + 1 < ln else 0
        for ch, d in ((0, dL[i]), (1, dR[i])):
            fr = F(d - F(float(int(d)))); r = rd[ch]
            b1 = bufs[ch][ln - 1] if r < 1 else bufs[ch][r - 1]
            o = F(F(F(1.0 - fr) * bufs[ch][r]) + F(fr * b1))
            outs[ch][i] = o; y[ch] = o
    return [[F(o * g) for o, g in zip(outs[0], gl)], [F(o * g) for o, g in zip(outs[1], gr)]]


class Snap:
    """Read-only copy of chosen emulator memory regions (pre-block kernel state for the kernel re-statements)."""
    def __init__(self, e, regions):
        self.r = [(a_, e.rd(a_, n)) for a_, n in regions]
    def rd(self, a_, n):
        for b, d in self.r:
            if b <= a_ and a_ + n <= b + len(d): return d[a_ - b:a_ - b + n]
        raise KeyError(hex(a_))
    def u32(self, a_): return struct.unpack("<I", self.rd(a_, 4))[0]
    def floats(self, a_, n): return list(struct.unpack("<%df" % n, self.rd(a_, 4 * n)))


def kernel_snap(e, k):
    ln = e.u32(k + 0xc0)
    return Snap(e, [(k, 0x118), (e.u32(k + 0xc4), 4 * ln), (e.u32(k + 0xc8), 4 * ln)])


ENTRY_POINTS = [  # (address, name, arguments / effect) — C1 table
    (0x100af0, "Osc_ctor", "(osc, wave, freq f32, fs): init, then +0x90 = table 0xb70e50, +8 = id = [0xb70e4c]++"),
    (0x100710, "Osc_init", "(osc, wave, freq, fs) -> 1 ok / 0 (fs <= 0, freq == 0, wave not 0..6): resets all fields"),
    (0x100b28, "Osc_initPeriodMs", "(osc, wave, ms, fs): init with 1000/ms (ms == 0 -> 0)"),
    (0x1015c8, "Osc_initMsPhaseAmp", "(osc, wave, ms, fs, [sp] phase, [sp+4] amp): init(1000/ms), resetPhase(phase), amp"),
    (0x100b54, "Osc_getWaveform", "-> +0xc"),
    (0x100b5c, "Osc_setWaveform", "(osc, wave): same wave -> no-op; else converts the phase position to the new waveform"),
    (0x101090, "Osc_setFrequency", "(osc, f): 0 -> hold; P = 44100/f - 1 (literal), c rescaled c*Pnew/Pold, slope/sine coefs"),
    (0x101320, "Osc_setPeriodMs", "(osc, ms): setFrequency(1000/ms); ms == 0 -> 0"),
    (0x1012f8, "Osc_getPeriodMs", "-> 1000/freq (0 if freq 0)"),
    (0x1017d4, "Osc_setPhaseOffset", "(osc, ph cycles): wrap to [0,1); +0x50 = ph*4 (tri) / ph*2 (saw) / ph (pulse, random) / cosf,sinf(2pi ph) (sine)"),
    (0x1018cc, "Osc_setPhaseOffset2", "(osc, x): ph = x*0.001/freq, then as setPhaseOffset (no direct caller)"),
    (0x101620, "Osc_getPhaseOffset", "-> phase offset in cycles (sine via acosf)"),
    (0x1016dc, "Osc_getPhaseOffset2", "-> phase offset * 1000/freq"),
    (0x101440, "Osc_resetPhase", "(osc, ph): restart the waveform at phase ph (counter c = P*ph, tri +1/4; sine y1/y2 from cos)"),
    (0x1019d8, "Osc_setAmplitude", "+0 = a"), (0x1019e4, "Osc_setOffset", "+4 = o"),
    (0x1019f0, "Osc_setSmoothingHz", "(osc, hz): b = expf(-2pi*hz/fs) (+0x5c), a = 1 - b (+0x58); hz <= 0 -> a 1, b 0"),
    (0x102cb0, "Osc_setSmoothingOff", "(osc, u32): +0x78 = (double)u; non-zero disables the output smoother"),
    (0x101a70, "Osc_smoothMono", "(osc, buf, n): smoother on one buffer (no caller found)"),
    (0x101ab8, "Osc_smoothStereo", "(osc, L, R, n): smoother on two buffers (no caller found)"),
    (0x101b24, "Osc_setResyncPeriod", "+0x6c = n (no caller found)"),
    (0x101b30, "Osc_resync", "sine only: re-derive y1/y2 from the clamped current value (amplitude renormalisation); +0x68 = 0"),
    (0x102c10, "Osc_resyncIfRunning", "freq != 0 -> resync"),
    (0x102c2c, "Osc_clearHold", "+0x70 = 0"), (0x102c3c, "Osc_setHold", "+0x70 = 1.0"),
    (0x102c50, "Osc_setRandomOffset", "+0x88 = k (random table start offset)"),
    (0x102c58, "Osc_nextRandom", "-> table[(+0x8c + +0x88) mod 0x2000], +0x8c advanced"),
    (0x102c8c, "Osc_randomMask", "-> 0x1fff"), (0x102c94, "Osc_tableAt", "(osc, i) -> table[i] (i >= 0x2000 masked)"),
    (0x101bdc, "Osc_process", "(osc, L, R, n) -> 1 / 0 (invalid wave: buffers untouched): n control samples per channel"),
    (0x1025d4, "Osc_processMono", "(osc, buf, n?) one-channel variant (LfoProcessor 0x1358b8 only; not modelled)"),
]

# ------------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H031"))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    im = sp16img.Image()
    table = load_table(im)


    # ---------------- C1 layout / API ------------------------------------------------------------------------------------
    P("== C1 oscillator object layout and entry points ==")
    calls = {}
    for site, tgt, kind in im.direct_calls():
        calls.setdefault(tgt, []).append(site)
    ep = []
    for addr, nm, what in ENTRY_POINTS:
        c = [hex(x_) for x_ in calls.get(addr, []) if not (0x100638 <= x_ < 0x102cc0)]
        ep.append({"addr": hex(addr), "name": nm, "what": what, "outside_callers": c})
        P("  0x%06x %-22s callers outside the block: %-3d %s" % (addr, nm, len(c), what))
    res["C1_entry_points"] = ep
    x = EmuOsc(1, 2.0); st = x.state()
    P("  ctor(osc, 1, 2.0 Hz, 44100) fields: " + ", ".join("%s=%s" % (k_, hex(v)) for k_, v in st.items()))
    m, _ = M.Osc.ctor(1, 2.0, FS, x.counter_before, table=table)
    check(not diff_state(st, model_state(m)) and st["pad+0x14"] == 0 and st["pad+0x94"] == 0 and st["table+0x90"] == TABLE,
          "ctor state == model in every field; +0x90 = table 0x%x; +0x14/+0x94 never written (0)" % TABLE)
    e = new_emu(); c0 = e.u32(ID_COUNTER)
    o1 = EmuOsc(1, 1.0, e=e); o2 = EmuOsc(0, 1.0, e=e)
    ids = (e.u32(o1.o + 8), e.u32(o2.o + 8), e.u32(ID_COUNTER))
    P("  id counter 0x%x: .data initial value %d; two ctors -> ids %d, %d, counter %d" % (ID_COUNTER, c0, *ids))
    check(c0 == 1 and ids == (1, 2, 3), "id = global counter 0xb70e4c (initial 1 in .data), post-incremented by each ctor")
    xa = EmuOsc(1, 1.0, id_before=98); xb = EmuOsc(1, 1.0, id_before=0)
    P("  init reads +8 BEFORE the ctor assigns the id: garbage id 98 -> resync counter +0x68 = %d (98*448 mod 44100 = %d); id 0 -> %d"
      % (xa.state()["rs_cnt+0x68"], 98 * 448 % 44100, xb.state()["rs_cnt+0x68"]))
    check(xa.state()["rs_cnt+0x68"] == 98 * 448 % 44100 and xb.state()["rs_cnt+0x68"] == 0,
          "resync phase (+0x68) at construction comes from the uninitialised id word (heap content)")
    crash = None
    try: EmuOsc(6, 2.0)
    except EmuAbort as ex: crash = str(ex)
    e6 = new_emu(); q = e6.malloc(OSC_SIZE); e6.w32(q + 0x90, TABLE)
    r6 = e6.call(A["ctor"], q, 6, f2u(2.0), FS)[0]
    P("  ctor with waveform 6 and +0x90 = 0: %s; with +0x90 pre-set to the table: ok, held value %r = table[0] %r" %
      (crash, u2f(e6.u32(q + 0x54)), u2f(struct.unpack("<I", struct.pack("<f", table[0]))[0])))
    check(crash is not None and "0x1008ec" in crash and u2f(e6.u32(q + 0x54)) == table[0],
          "waveform 6 cannot be constructed by the ctor: init reads the table pointer +0x90 before the ctor stores it (0x1008c8/0x1008ec)")
    tab = table[:8192]
    mean = sum(tab) / 8192.0; sd = math.sqrt(sum((v - mean) ** 2 for v in tab) / 8192.0)
    refs = sp16img.const_sites(im, [TABLE])[TABLE]
    sec = [k_ for k_, (lo, hi) in im.sec.items() if lo <= TABLE < hi]
    P("  random table 0x%x: section %s, 8192 float32, min %.6f max %.6f mean %.5f sd %.5f (uniform [-1,1): sd 0.57735); code refs %s; "
      "word after the table (index-wrap quirk) = 0x%08x" % (TABLE, sec, min(tab), max(tab), mean, sd, [(t_, hex(a_)) for t_, a_ in refs],
                                                            struct.unpack("<I", struct.pack("<f", table[8192]))[0]))
    check(sec == [".data"] and [a_ for _, a_ in refs] == [0x100b08] and abs(sd - 1 / math.sqrt(3)) < 0.01,
          "the table is initialised .data (file contents), referenced only by the ctor (movw/movt 0x100b08): no runtime generator")
    res["C1"] = {"ctor_state": st, "ids": ids, "wave6_ctor_crash": crash, "table_stats": [min(tab), max(tab), mean, sd]}

    # ---------------- C2 waveform facts (emulated 1.60) ------------------------------------------------------------------
    P(); P("== C2 waveform shapes read back from emulation: f = 441 Hz (P = 99), smoothing off, amp 1 / offset 0 ==")
    c2 = {}
    for w in range(7):
        if w == 6:
            x = EmuOsc(1, 441.0); x.e.call(A["init"], x.o, 6, f2u(441.0), FS)
        else:
            x = EmuOsc(w, 441.0)
        x.call("set_smooth_off", 1); x.call("set_phase", 0.25)
        L = []; R = []
        for _ in range(8):
            _, l, r = x.process(64); L += l; R += r
        Pp = u2f(x.state()["P+0x84"]); per = L[100:199]
        # lag (samples) by which R leads L: R[i] == L[i + lag]
        def lag_of(L, R):
            best = None
            for lg in range(0, 99):
                err = sum(abs(R[i] - L[i + lg]) for i in range(150, 350))
                if best is None or err < best[1]: best = (lg, err)
            return best
        lg = lag_of(L, R)
        d = {"P": Pp, "min": min(per), "max": max(per), "distinct_in_period": len(set(per)), "R_leads_by": lg[0], "lag_err": lg[1],
             "frac_pos": sum(1 for v in per if v > 0) / 99.0}
        if w in (3, 4, 5):
            edges = [i for i in range(1, len(L)) if L[i] > 0 >= L[i - 1]]
            d["period_samples"] = sorted(set(b_ - a_ for a_, b_ in zip(edges, edges[1:])))
        if w == 0:
            th = [2 * math.pi * 441.0 / FS * (i + 2) for i in range(len(L))]
            d["max_err_vs_sin"] = max(abs(L[i] - math.sin(th[i])) for i in range(len(L)))
        c2[w] = d
        P("  wave %d: P %.1f  min %.6f max %.6f  distinct/period %3d  fraction > 0 %.3f  R leads L by %2d samples (ph 0.25 -> P/4 = %.2f) err %.3g%s"
          % (w, Pp, d["min"], d["max"], d["distinct_in_period"], d["frac_pos"], lg[0], Pp / 4, lg[1],
             "  max|L[i] - sin((i+2)w)| %.2g" % d["max_err_vs_sin"] if w == 0 else
             ("  rising-edge spacing %s samples" % d["period_samples"] if "period_samples" in d else "")))
    res["C2"] = c2
    check(abs(c2[0]["max_err_vs_sin"]) < 1e-5 and abs(c2[1]["max"] - c2[1]["min"] - 2.0) < 0.05 and abs(c2[3]["frac_pos"] - 0.5) < 0.02
          and c2[3]["period_samples"] == [99] and c2[4]["period_samples"] == [99]
          and abs(c2[4]["frac_pos"] - 0.25) < 0.02 and abs(c2[5]["frac_pos"] - 0.125) < 0.02 and c2[6]["distinct_in_period"] <= 2
          and all(abs(c2[w]["R_leads_by"] - 99 / 4.0) <= 1 for w in range(6)),
          "sine = sin((n+2)w) from init; period = P = fs/f - 1 samples (not fs/f); triangle +-1 within 4f/fs; pulse duty 1/2, 1/4, 1/8; "
          "random holds one value per period; R leads L by ph*P samples")
    # hold mode: saw output while running vs after setFrequency(0)
    x = EmuOsc(2, 441.0); x.call("set_smooth_off", 1)
    _, l, _ = x.process(30); x.call("set_freq", 0.0); _, lh, _ = x.process(4)
    P("  saw: last running value %.6f, held value after setFrequency(0) %.6f (sign-inverted ramp position)" % (l[-1], lh[0]))
    check(abs(l[-1] + lh[0]) < 0.05, "hold mode (+0x70) re-derives the saw from c*|k| - 1, the inverse of the running 1 + c*k ramp")
    x = EmuOsc(1, 441.0); x.call("set_smooth_off", 1); x.call("set_freq", 0.0); x.call("set_freq", 300.0)
    _, lh2, _ = x.process(8)
    check(len(set(lh2)) == 1 and x.state()["hold+0x70"] != 0, "setFrequency(f != 0) does not leave hold mode; only init clears +0x70")

    # ---------------- C3 model vs emulation --------------------------------------------------------------------------
    P("== C3 oscillator model vs emulated 1.60 (ctor 0x100af0 + setters + process 0x101bdc), output + full state after every call ==")
    cases = c3_cases()
    if a.quick: cases = [c for c in cases if "events" in c["name"] or "invalid" in c["name"]]
    c3 = []; allx = True; hashes = []
    for c in cases:
        r = run_case(c, table, keep=True)
        oe = b"".join(struct.pack("<%df" % len(l), *l) + struct.pack("<%df" % len(rr), *rr) for l, rr in r.pop("_outE"))
        r.pop("_outM"); r.pop("_emu"); r.pop("_model")
        r["emu_sha"] = sha(oe)[:16]; hashes.append(oe)
        with open(os.path.join(a.out, "emu_%s.f32" % c["name"]), "wb") as fh: fh.write(oe)
        c3.append(r); allx &= r["exact"]
        P("  %-40s calls %4d  bit-exact %7d/%-7d max|err| %-8.3g state diffs %d ret diffs %d %s" %
          (r["name"], r["calls"], r["bit_exact"], r["samples"], r["max_abs_err"], r["state_diffs"], r["ret_diffs"],
           "" if r["exact"] else "FIRST %s" % (r["first"],)))
    res["C3"] = c3
    res["C3_totals"] = [len(c3), sum(c_['samples'] for c_ in c3), sum(c_['calls'] for c_ in c3)]
    check(allx, "model == emulation bit-exactly (outputs, return codes and all object fields) in all %d C3 runs" % len(c3))
    # libm: own re-implementations (OwnLibm) vs the real 1.60 libm, on the argument ranges the oscillator uses
    el = EmuLibm(new_emu()); ol = M.OwnLibm(); hl = M.HostLibm(); g = random.Random(5)
    fa = [F(g.uniform(0, 1) * 6.2831855) for _ in range(1500)]
    da = [g.uniform(0, 0.3) for _ in range(800)] + [g.uniform(-7, 7) for _ in range(800)]
    aa = [g.uniform(-1, 1) for _ in range(1000)]
    ea = [F(g.uniform(-0.2, 0)) for _ in range(1500)] + [F(F(1.0 / FS) * M.SMOOTH_INIT_K)] + \
         [F(F(F(h_) * M.NEG_TWO_PI_F) * F(1.0 / FS)) for h_ in (300.0, 2000.0, 20000.0)]
    lm = {}
    for nm_, args in (("sincos", da), ("cos", da), ("acos", aa), ("cosf", fa), ("sinf", fa), ("expf", ea)):
        ev = [getattr(el, nm_)(v) for v in args]
        lm[nm_] = {"own": sum(getattr(ol, nm_)(v) == r_ for v, r_ in zip(args, ev)),
                   "host": sum(getattr(hl, nm_)(v) == r_ for v, r_ in zip(args, ev)), "n": len(args)}
    used = [ea[-4], ea[-3], ea[-2], ea[-1]]
    used_ok = all(el.expf(v) == ol.expf(v) for v in used)
    P("  libm (own / host / n vs emulated 1.60 libm): " + ", ".join("%s %d/%d/%d" % (k_, v["own"], v["host"], v["n"]) for k_, v in lm.items())
      + "; expf at the smoothing arguments used (50 Hz init, 300, 2000, 20000 Hz): %s" % ("equal" if used_ok else "DIFFER"))
    check(all(lm[k_]["own"] == lm[k_]["n"] for k_ in ("sincos", "cos", "acos", "cosf", "sinf")) and used_ok,
          "crmath (correctly rounded double sin/cos/acos) and fdlibm_sincosf reproduce the 1.60 libm exactly; glibc expf is "
          "not always correctly rounded (%d/%d differ from crmath), but equal at every argument the matrix uses"
          % (lm["expf"]["n"] - lm["expf"]["own"], lm["expf"]["n"]))
    res["C3_libm"] = lm


    if not a.quick:
        # ---------------- C4/C5/C6 users, roles and inline-built effects ---------------------------------------------
        P(); P("== C6 inline construction (blocks of InsertFxProcessor ctor 0x118b0c) + Insert init; slot 25 called directly ==")
        c6 = {}
        for name in ("Chorus", "Flanger", "Distortion"):
            b = INSERT_BUILD[name]; outs = []
            nb = 120 if name != "Distortion" else 16
            Ls, Rs = test_signal(nb)
            for rep_ in range(2):
                x = EmuInline(name); x.table = table; e = x.e; k = x.kernel
                o = []; insitu_bad = 0; kbad = 0; kn = 0; kerr = 0.0; amb = 0; ctb = 0
                for blk in range(nb):
                    inL, inR = Ls[64 * blk:64 * blk + 64], Rs[64 * blk:64 * blk + 64]
                    pre = kernel_snap(e, k) if b["osc_buf"] else None
                    r0, oL, oR = x.process(inL, inR)
                    o.append((oL, oR))
                    if b["osc_buf"]:
                        dL = e.floats(e.u32(k + b["osc_buf"][0]), 64); dR = e.floats(e.u32(k + b["osc_buf"][1]), 64)
                        mL, mR = x.osc_snap.process(64)
                        insitu_bad += sum(f2u(p_) != f2u(q_) for p_, q_ in zip(dL + dR, mL + mR))
                        km = (chorus_kernel_model if name == "Chorus" else flanger_kernel_model)(pre, k, inL, inR, dL, dR)
                        for p_, q_ in zip(oL + oR, km[0] + km[1]):
                            kn += 1; kbad += f2u(p_) != f2u(q_); kerr = max(kerr, abs(p_ - q_))
                        # alternatives: oscillator as an amplitude (gain) instead of a delay time; constant delay = offset
                        dc = [u2f(e.u32(k + 0x2c))] * 64
                        alt = (chorus_kernel_model if name == "Chorus" else flanger_kernel_model)(pre, k, inL, inR, dc, dc)
                        ctb += sum(f2u(p_) == f2u(q_) for p_, q_ in zip(oL + oR, alt[0] + alt[1]) if p_ != 0.0)
                        amb += sum(f2u(p_) == f2u(F(i_ * g_)) for p_, i_, g_ in zip(oL + oR, inL + inR, dL + dR) if p_ != 0.0)
                blob = b"".join(struct.pack("<64f", *l) + struct.pack("<64f", *r) for l, r in o)
                outs.append(blob)
            q = k + 0x28
            ost = {"wave": e.u32(q + 0xc), "freq_Hz": u2f(e.u32(q + 0x10)), "amp": u2f(e.u32(q)), "offset": u2f(e.u32(q + 4)),
                   "phase+0x50": u2f(e.u32(q + 0x50)), "smooth_b+0x5c": u2f(e.u32(q + 0x5c)),
                   "smooth_off": struct.unpack("<d", e.rd(q + 0x78, 8))[0]}
            nz = sum(1 for v in struct.unpack("<%df" % (len(outs[0]) // 4), outs[0]) if v != 0.0)
            c6[name] = {"obj_vptr": hex(e.u32(x.o)), "kernel_vptr": hex(e.u32(k)), "blocks": nb, "nonzero": nz,
                        "sha": [sha(z)[:16] for z in outs], "osc_calls": x.osc_calls, "osc_after": ost,
                        "osc_insitu_mismatch": insitu_bad, "kernel_restatement": [kn - kbad, kn, kerr],
                        "alt_const_delay_equal": ctb, "alt_amplitude_mod_equal": amb}
            with open(os.path.join(a.out, "emu_%s_slot25.f32" % name), "wb") as fh: fh.write(outs[0])
            P("  %-10s obj vptr %s kernel %s (new 0x%x / 0x%x, ctor 0x%x)  %d blocks, non-zero %d/%d, runs %s, Osc_process calls %d"
              % (name, c6[name]["obj_vptr"], c6[name]["kernel_vptr"], b["size"], b["ksize"], b["kernel"], nb, nz, 128 * nb,
                 "identical" if outs[0] == outs[1] else "DIFFER", x.osc_calls))
            P("             oscillator after the run: %s" % ost)
            if b["osc_buf"]:
                P("             in-situ oscillator (osc.py from the state at Osc_process entry) mismatches %d/%d; kernel re-statement "
                  "(delay = oscillator output) bit-exact %d/%d max|err| %.3g; alternatives (non-zero samples): constant delay equal %d, amplitude-mod equal %d"
                  % (insitu_bad, 128 * nb, kn - kbad, kn, kerr, ctb, amb))
        res["C6"] = c6

        ch, fl, di = c6["Chorus"], c6["Flanger"], c6["Distortion"]
        check(all(c6[n_]["sha"][0] == c6[n_]["sha"][1] and c6[n_]["nonzero"] > 0 for n_ in c6),
              "Chorus, Flanger, Distortion built from their inline ctor blocks run slot 25 deterministically with non-trivial output")
        check(ch["osc_insitu_mismatch"] == 0 and fl["osc_insitu_mismatch"] == 0 and ch["osc_calls"] == 120 and fl["osc_calls"] == 120,
              "inside c_chorus / c_flanger the oscillator output (+0xd0/+0xd4, +0xd8/+0xdc) equals osc.py bit-exactly every block")
        check(ch["kernel_restatement"][0] == ch["kernel_restatement"][1] and fl["kernel_restatement"][0] == fl["kernel_restatement"][1],
              "Chorus/Flanger kernel output == re-statement with the oscillator value as the DELAY TIME (samples) of a linearly "
              "interpolated ring buffer (Flanger: + output feedback and delay-dependent gain)")
        check(di["osc_calls"] == 0 and di["osc_after"]["freq_Hz"] == 1.0 and di["osc_after"]["amp"] == 1.0,
              "Distortion never runs its oscillator (Osc_process not called; state stays at the ctor values 1 Hz, amp 1)")

        # ---------------- C4 configuration per user (emulated setter log) --------------------------------------------
        P(); P("== C4 oscillator configuration: kernel setter calls during construction, Insert defaults, first block and slot-14 changes ==")
        KS = {"Chorus": {0xfeb10: "k3 setRateHz", 0xfebc4: "k4 setPeriodMs", 0xfed90: "k5 setDepth", 0xfec34: "k6 setPhase",
                         0xfeecc: "k7 setDepthScale", 0x116224: "slot14"},
              "Flanger": {0xffdc4: "k3 setRateHz", 0xfff50: "k4 setPeriodMs", 0xfffd4: "k5 setDepth", 0xffe68: "k6 setPhase",
                          0x100104: "k7 setDepthScale", 0x1163f0: "slot14"}}
        OSCS = {A["set_freq"]: "Osc_setFrequency", A["set_period_ms"]: "Osc_setPeriodMs", A["set_amp"]: "Osc_setAmplitude",
                A["set_off"]: "Osc_setOffset", A["set_phase"]: "Osc_setPhaseOffset", A["reset_phase"]: "Osc_resetPhase",
                A["set_waveform"]: "Osc_setWaveform", A["set_smooth_off"]: "Osc_setSmoothingOff", A["set_smooth_hz"]: "Osc_setSmoothingHz"}
        c4 = {}
        for name in ("Chorus", "Flanger"):
            watch = dict(KS[name]); watch.update(OSCS)
            x = EmuInline(name, log_calls=tuple(a_ for a_ in watch if a_ != A["process"])); x.table = table
            nm = lambda a_, r1, fv, f2: "%s(%s)" % (watch[a_], ("%d" % r1) if a_ in (A["set_waveform"], A["set_smooth_off"], 0x116224, 0x1163f0)
                                                    else "%.6g" % fv) + (" v=%.4g" % f2 if a_ in (0x116224, 0x1163f0) else "")
            init_log = [nm(*l_) for l_ in x.log]; x.log = []
            x.process([0.0] * 64, [0.0] * 64); blk_log = [nm(*l_) for l_ in x.log]; x.log = []
            for idx, v in ((0, 0.75), (1, 0.6), (2, 0.4), (3, 0.3)):
                x.e.vcall(x.o, 14, idx, f2u(v))
            x.process([0.0] * 64, [0.0] * 64); chg_log = [nm(*l_) for l_ in x.log]
            q = x.kernel + 0x28; e = x.e
            after = {"freq": u2f(e.u32(q + 0x10)), "amp": u2f(e.u32(q)), "off": u2f(e.u32(q + 4)), "ph50": u2f(e.u32(q + 0x50)),
                     "ph54": u2f(e.u32(q + 0x54))}
            c4[name] = {"construction+defaults": init_log, "first_block": blk_log, "after_slot14(0:.75,1:.6,2:.4,3:.3)": chg_log, "osc": after}
            P("  %s construction + Insert defaults: %s" % (name, init_log))
            P("  %s first slot-25 block: %s" % (name, blk_log))
            P("  %s after slot 14 (0 Rate .75, 1 .6, 2 .4, 3 .3) + one block: %s -> osc %s" % (name, chg_log, after))
        res["C4"] = c4
        check(any("Osc_setWaveform(0)" in l_ for l_ in c4["Chorus"]["construction+defaults"]) and
              any(l_.startswith("Osc_setAmplitude") for l_ in c4["Chorus"]["after_slot14(0:.75,1:.6,2:.4,3:.3)"]),
              "Chorus/Flanger: sine oscillator, 0.1 Hz at ctor; Rate -> kernel slot 3 -> Osc_setFrequency every change; depth -> amplitude/offset")

        # ---------------- C7 alternatives ----------------------------------------------------------------------------
        P(); P("== C7 alternative explanations ==")
        # (a) sine: recursive oscillator + periodic resync vs direct sinf of the phase
        x = EmuOsc(0, 1000.0); x.call("set_smooth_off", 1)
        m, _ = M.Osc.ctor(0, 1000.0, FS, x.counter_before, table=table); m.set_smoothing_off(1)
        class NoResync(M.Osc):
            def resync(self): self.rs_cnt = 0; return 1
        mn, _ = NoResync.ctor(0, 1000.0, FS, x.counter_before, table=table); mn.set_smoothing_off(1)
        nb = 1500; E = []; resyncs = 0; prev = x.state()["rs_cnt+0x68"]
        for _ in range(nb):
            _, l, _r = x.process(64); E += l
            cur = x.state()["rs_cnt+0x68"]
            if cur < prev: resyncs += 1
            prev = cur
        Mo = []; Mn = []
        for _ in range(nb): Mo += m.process(64)[0]; Mn += mn.process(64)[0]
        w0 = 2 * math.pi * 1000.0 / FS
        direct = [F(math.sin(w0 * (i + 2))) for i in range(len(E))]
        eq_direct = sum(f2u(p_) == f2u(q_) for p_, q_ in zip(E, direct))
        err_direct = max(abs(p_ - q_) for p_, q_ in zip(E, direct))
        eq_model = sum(f2u(p_) == f2u(q_) for p_, q_ in zip(E, Mo)); eq_nores = sum(f2u(p_) == f2u(q_) for p_, q_ in zip(E, Mn))
        first_nores = next((i for i, (p_, q_) in enumerate(zip(E, Mn)) if f2u(p_) != f2u(q_)), None)
        P("  sine 1 kHz, %d samples: resyncs seen %d (every fs = 44100 samples); emulation vs direct F(sin((i+2)w)): bit-equal %d/%d, "
          "max|diff| %.3g; vs model %d/%d; vs model WITHOUT resync %d/%d (first difference at sample %s, right after the first resync)"
          % (len(E), resyncs, eq_direct, len(E), err_direct, eq_model, len(E), eq_nores, len(E), first_nores))
        check(eq_model == len(E) and eq_direct < len(E) and resyncs >= 2 and eq_nores < len(E) and first_nores is not None
              and first_nores >= 44100 - 64,
              "waveform 0 is a recursive (2cos(w)) oscillator renormalised once per second by resync 0x101b30, not a direct sin() of the phase")
        res["C7_sine"] = {"samples": len(E), "resyncs": resyncs, "eq_direct": eq_direct, "max_err_direct": err_direct,
                          "eq_model": eq_model, "eq_no_resync": eq_nores, "first_no_resync_diff": first_nores}
        # (b) random: table lookup (patch the table in emulated memory) vs a runtime PRNG (glibc rand(), seed 1)
        neg = [-v for v in table[:8192]] + [table[8192]]
        x = EmuOsc(1, 3000.0); x.e.wr(TABLE, struct.pack("<8192f", *neg[:8192])); x.e.call(A["init"], x.o, 6, f2u(3000.0), FS)
        x.call("set_smooth_off", 1)
        m, _ = M.Osc.ctor(1, 3000.0, FS, x.counter_before, table=neg); m.init(6, 3000.0, FS); m.set_smoothing_off(1)
        E = []; Mo = []
        for _ in range(64):
            E += x.process(64)[1]; Mo += m.process(64)[0]
        eq = sum(f2u(p_) == f2u(q_) for p_, q_ in zip(E, Mo))
        def glibc_rand(seed, n):
            r = [0] * 34; r[0] = seed
            for i in range(1, 31):
                hi, lo = divmod(r[i - 1], 127773); w = 16807 * lo - 2836 * hi
                r[i] = w + 2147483647 if w < 0 else w
            for i in range(31, 34): r[i] = r[i - 31]
            out = []
            for i in range(34, 344 + n):
                r.append((r[i - 31] + r[i - 3]) & 0xffffffff)
                if i >= 344: out.append(r[i] >> 1)
            return out
        g = glibc_rand(1, 1000)
        cand = {"2x/RAND_MAX-1": [F(2.0 * v / 2147483647.0 - 1.0) for v in g], "x/RAND_MAX": [F(v / 2147483647.0) for v in g]}
        pr = {k_: sum(1 for p_, q_ in zip(v, table[:1000]) if abs(p_ - q_) < 1e-6) for k_, v in cand.items()}
        P("  random: table patched (negated) in emulated .data -> emulation == model with the negated table %d/%d; glibc rand() seed 1 "
          "first 1000 values within 1e-6 of the table: %s" % (eq, len(E), pr))
        check(eq == len(E) and all(v == 0 for v in pr.values()),
              "waveform 6 reads the static .data table (output follows a patched table); it is not a runtime PRNG (glibc rand seed 1: 0 matches)")
        res["C7_random"] = {"patched_eq": [eq, len(E)], "glibc_rand_matches": pr}

    P(); P("RESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  failed: " + f_)
    with open(os.path.join(a.out, "h031_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    with open(os.path.join(a.out, "h031.json"), "w") as fh: json.dump(res, fh, indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
