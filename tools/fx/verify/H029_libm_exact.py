#!/usr/bin/env python3
"""H029 — glibc-exact libm in the LoFi / MMF / PEQ (and other) models: removes the F044 host-libm residual.

Sections (success criteria of kb/cycles/041.md):
  A  inventory: every math.* / `**` call in harness/models/*.py (code lines, docstrings skipped), each classified
       (a) exact already (IEEE-exact op, exact constant, or own glibc-exact code), (b) host libm on an output path,
       (c) not on an output path; for (b) and the libm-backed (a) rows the 1.60 import, PLT stub and call sites, each
       call site checked to be a direct bl to that PLT stub. Run on the pre-change copy (--old-models) and on the
       current models; every hit must be in the table (unclassified hit = FAIL).
  B  library oracle: the real 1.60 libm (decoded/lib/libm.so.6, unicorn) for double tan, pow, exp and float log10f on
       >= 10^4 arguments each, from the argument domains the models reach plus random samples. Reported per routine:
       correctly rounded count (vs an independent prec-90 decimal reference), host `math` mismatches, own-replacement
       (crmath.tan / crmath.pow / crmath.exp / fdlibm_powf.log10f) mismatches (must be 0).
  C  no host libm left: the changed models run with math.tan/pow/exp/log/log10 replaced by a trap (any call = FAIL).
  D  random-setting stress against the emulated 1.60 coefficient routines (real libm), >= 10^4 settings per group,
       compared word-for-word with the current models and with the pre-change models (old-model error count):
       D1 IirFilter 2nd-order static calcCoefs 0xe1bb8 HPF / 0xe1ca0 LPF / 0xe1d88 BPF (LoFi, MMF, PEQ, PerfLoFi stages)
       D2 IirHpf1stOrder static calcCoefs 0xe1aa0 (EffectBase post-HPF)
       D3 PEQ IirFilter2 configure 0xe2ab4 (pow + slot-9 calcCoefs) on real objects + calcCoefs 0xe2440 / 0xe2540 at 48/96 kHz
       D4 LoFi ramp setup 0xfb994 and MMF ramp setup 0x108608 (log10f step counts) + MMF setGlide 0x108570 (log10f + pow)
       D5 parameter apply: LoFi 0xfb20c (PREAMP/REDUCTION/CUTOFF pow), MMF 0x107d18 (CUTOFF/GAIN pow), PerfLoFi 0xfc278
          (LEVEL/CUTOFFMAX/RESONANCE/REDUCTION: pow, powf, filter update 0xfacec); MMF also GLIDE (inline pow 0x107f70)
       D6 PEQ gain law (float)pow(10, (double)F(gdb * 0.05f)) (inline at 0x10c154 / 0x10c40c / 0x10c6ac): real pow on the
          exact argument expression vs peq.gain_lin
Outputs only to --out (default harness/out/H029/). Run: .venv/bin/python -B harness/H029_libm_exact.py --out DIR
Own code; no firmware bytes are stored (the emulator maps target/ and decoded/lib read-only at run time).
"""
import argparse, decimal, hashlib, importlib, json, math, os, random, re, struct, sys, time
from decimal import Decimal as D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODELS = os.path.join(HERE, "models")
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, MODELS)
import darwin_ctr_fix                                        # noqa: E402
darwin_ctr_fix.install()
from emu import Emu, f2u, u2f, d2u, u2d                       # noqa: E402
import sp16img                                                # noqa: E402

F32 = struct.Struct("<f")
def F(x): return F32.unpack(F32.pack(x))[0]
def sha(b): return hashlib.sha256(b).hexdigest()
def lohi(x): u = d2u(x); return u & 0xffffffff, u >> 32


# =========================================================================================================================
# model loading (current models, and the pre-change copy as separate module objects)
MODEL_NAMES = sorted(f[:-3] for f in os.listdir(MODELS) if f.endswith(".py"))


def load_models(path, names):
    """Import `names` from directory `path` as fresh module objects (their own imports resolve inside `path`), then restore
    sys.modules so the two model sets never mix."""
    allnames = set(MODEL_NAMES) | set(f[:-3] for f in os.listdir(path) if f.endswith(".py"))
    saved = {n: sys.modules.pop(n) for n in list(sys.modules) if n in allnames}
    sys.path.insert(0, path)
    try:
        mods = {n: importlib.import_module(n) for n in names}
    finally:
        sys.path.remove(path)
        for n in list(sys.modules):
            if n in allnames: del sys.modules[n]
        sys.modules.update(saved)
    return mods


# =========================================================================================================================
# A. inventory
HOST_RE = re.compile(r"\bmath\.(tan|pow|exp|expm1|log|log10|log2|log1p|sin|cos|acos|asin|atan|atan2|sinh|cosh|tanh|sqrt|hypot|"
                     r"cbrt|erf|gamma)\s*\(|\*\*(?!\s*kw)")

# PLT stubs of the 1.60 main binary (checked against .rel.plt at run time)
PLT = {"tan": 0x10e58, "pow": 0x11698, "log10f": 0x10ab0, "exp": 0x1144c, "sqrt": 0x10210, "powf": 0xff40, "tanf": 0x104c8,
       "expf": 0x103fc, "sqrtf": 0x10ef4, "log10": 0xffac, "sincos": 0x11560, "cos": 0x10ac8, "acos": 0x10348, "cosf": 0x11614, "sinf": 0x10b64}

# (file, regex on the code line, class, 1.60 routine, call sites, precision, what / why)
INVENTORY = [
    # ---- lofi.py ---------------------------------------------------------------------------------------------------
    ("lofi.py", r"def log10f\(x\): return F\(math\.log10", "b", "log10f", [0x13818, 0x1385c, 0xfba10, 0xfba1c, 0xfba78, 0xfba84],
     "float", "log10f: static G1/G3 (init 0x137cc) and filter ramp step counts (0xfb994); also imported by mmf.py"),
    ("lofi.py", r"G3 = F\(math\.pow\(10\.0", "b", "pow", [0x1383c], "double", "static G3 = 50^(1/100) (init 0x137cc)"),
    ("lofi.py", r"G1 = F\(math\.pow\(10\.0", "b", "pow", [0x13880], "double", "static G1 = 1000^(1/250) (init 0x137cc)"),
    ("lofi.py", r"w = math\.tan\(fc \* \(math\.pi / fs\)\)", "b", "tan", [0xe1be8, 0xe1cd0, 0xe1ddc], "double",
     "IirFilter 2nd-order calcCoefs HPF 0xe1bb8 / LPF 0xe1ca0 / BPF 0xe1d88 (LoFi, MMF, PEQ stages, PerfLoFi)"),
    ("lofi.py", r"s = math\.sqrt\(4\.0", "a", "sqrt", [0xe1e9c], "double", "BPF calcCoefs sqrt: IEEE correctly rounded on every host"),
    ("lofi.py", r"t = F\(math\.pow\(10\.0, float\(e\)\)\)", "b", "pow", [0xfb530], "double", "PREAMP gain target (0xfb20c)"),
    ("lofi.py", r"math\.pow\(1000\.0000610351562", "b", "pow", [0xfb430], "double", "REDUCTION rate (0xfb20c)"),
    ("lofi.py", r"cut_t = F\(math\.pow\(1000\.0", "b", "pow", [0xfb3d8], "double", "CUTOFF target (0xfb20c)"),
    ("lofi.py", r"a = F\(math\.sqrt\(F\(x \* sg\)\)\)", "a", "sqrtf", [0xfb010, 0xfb020], "float", "crusher 0xfaf28 sqrtf: IEEE exact"),
    # new code (after the switch)
    ("lofi.py", r"def log10f\(x\): return FP\.log10f", "a", "log10f", [0x13818, 0x1385c, 0xfba10, 0xfba1c, 0xfba78, 0xfba84],
     "float", "fdlibm log10f (fdlibm_powf.log10f)"),
    # ---- mmf.py ----------------------------------------------------------------------------------------------------
    ("mmf.py", r"q = float\(q_c\) if self\.kind < 3 else math\.sqrt", "a", "sqrt", [0x107c14], "double", "24 dB Q' = sqrt(Q) (0x107b64): IEEE exact"),
    ("mmf.py", r"m = F\(math\.pow\(10\.0, float\(F\(log10f", "b", "pow", [0x1091ec, 0x1085e0, 0x107f70], "double",
     "glide step multiplier 1000^(1/G) (ctor 0x10913c, setGlide 0x108570, apply 0x107d18); log10f via lofi.log10f"),
    ("mmf.py", r"def cutoff_hz\(v\): return F\(F\(math\.pow\(1000\.0", "b", "pow", [0x107de0], "double", "CUTOFF target (0x107d18)"),
    ("mmf.py", r"def gain_lin\(v\): return F\(math\.pow\(10\.0", "b", "pow", [0x107eac], "double", "GAIN target (0x107d18)"),
    # ---- peq.py ----------------------------------------------------------------------------------------------------
    ("peq.py", r"self\.Q = 1\.0 / math\.sqrt\(2\.0\)", "a", "constant", [], "double", "ctor Q 1/sqrt(2): IEEE exact constant"),
    ("peq.py", r"p = math\.pow\(10\.0, gdb / 20\.0\) - 1\.0", "b", "pow", [0xe2b44, 0xe2c04], "double",
     "IirFilter2 configure 0xe2ab4: p = 10^(gdb/20) - 1"),
    ("peq.py", r"t = math\.tan\(float\(fc\) \* \(PI / float\(fs\)\)\)", "b", "tan", [0xe2470, 0xe2570], "double",
     "Peaking 0xe2440 / LowShelving 0xe2540 calcCoefs"),
    ("peq.py", r"V = p \+ 1\.0; sv = math\.sqrt\(V\)", "a", "sqrt", [0xe2658], "double", "low shelf calcCoefs sqrt(V): IEEE exact"),
    ("peq.py", r"return F\(math\.pow\(10\.0, float\(F\(F\(gdb\)", "b", "pow", [0x10c154, 0x10c40c, 0x10c6ac], "double",
     "band output gain (float)pow(10, F(gdb*0.05f)) (swap 0x10c070, band process 0x10c208)"),
    # ---- perf_lofi.py ------------------------------------------------------------------------------------------------
    ("perf_lofi.py", r"b = F\(math\.pow\(B_BASE", "b", "pow", [0xfc40c, 0xfb0b4, 0xfc550], "double",
     "bits 12*(5/12)^(2L) (apply 0xfc278, slot 27 0xfb02c, 0xfc518)"),
    ("perf_lofi.py", r"fa = F\(math\.pow\(LPF_BASE", "b", "pow", [0xfad1c], "double", "LPF cutoff (filter update 0xfacec)"),
    ("perf_lofi.py", r"fb = F\(math\.pow\(400\.0", "b", "pow", [0xfae00], "double", "HPF cutoff (filter update 0xfacec)"),
    ("perf_lofi.py", r"a = F\(math\.sqrt\(F\(x \* sg\)\)\)", "a", "sqrtf", [0xfb010, 0xfb020], "float", "shared crusher 0xfaf28 sqrtf: IEEE exact"),
    # ---- effectbase.py -------------------------------------------------------------------------------------------------
    ("effectbase.py", r"w = math\.tan\(float\(self\.fc\)", "b", "tan", [0xe1ac8], "double",
     "IirHpf1stOrder calcCoefs 0xe1aa0 (EffectBase post-HPF)"),
    # ---- phaser.py ----------------------------------------------------------------------------------------------------
    ("phaser.py", r"self\.pole = F\(math\.exp\(FB_LP", "b", "exp", [0x10d978], "double", "feedback LPF pole exp(-2pi*10000/fs) (ctor 0x10d654)"),
    # ---- generic replacements (after the switch) -------------------------------------------------------------------------
    (None, r"\bCR\.(tan|pow|exp)\(", "a", "tan/pow/exp", [], "double", "crmath correctly rounded (= glibc 2.13 dbl-64, section B)"),
    # ---- already exact / not on an output path ---------------------------------------------------------------------------
    ("compressor.py", r"r = F\(math\.sqrt\(mx\)", "a", "sqrt", [0xf86f4, 0xf89fc], "double", "RMS detector sqrt (compressor slot-25 bodies 0xf8270 / 0xf8718): IEEE exact"),
    ("device_out.py", r"20 \* math\.log10\(t\[i\]", "c", "-", [], "-", "diagnostic printout of the output table in dB only"),
    ("fdlibm_powf.py", r"return F\(math\.pow\(x, y\)\)", "c", "powf", [], "float",
     "special-value fallbacks (x<=0, NaN/inf, |y|>2^27, over/underflow) not reached by any modelled argument"),
    ("fdlibm_powf.py", r"return F\(math\.sqrt\(x\)\)", "a", "powf", [], "float", "powf(x, 0.5) = sqrtf(x) as in fdlibm: IEEE exact"),
    ("fdlibm_powf.py", r"return F\(math\.(log|log10)\(x\)\) if x > 0", "c", "logf/log10f", [], "float",
     "subnormal/inf fallback, not reached"),
    ("fdlibm_powf.py", r"back to math\.pow where marked", "c", "-", [], "-", "docstring text"),
    ("glibc_log10.py", r"return math\.log10\(x\) if x > 0", "c", "log10", [], "double", "non-finite / x<=0 fallback, not reached"),
    ("osc.py", r"def (sincos|cos|acos|cosf|sinf|expf|acosf)\(self, x\): return (math|F\(math)", "c", "sin/cos/acos/expf", [], "-",
     "HostLibm: optional comparison backend; the model default is OwnLibm (crmath / fdlibm_sincosf)"),
    ("track_mix.py", r"t\[i\] = F\(10\.0 \*\* \(_LOW_DB", "a", "table 0x83e050", [], "float",
     "volume table is a static 128-float table in the 1.60 binary; H009 compares all 128 entries bit-exactly"),
    ("track_mix.py", r"t\[i\] = F\(\(i / 100\.0\) \*\* 2\)", "a", "table 0x83e050", [], "float", "same table (exhaustive check)"),
    ("track_mix.py", r"t\[i\] = F\(2\.0 \*\* \(math\.log", "a", "table 0x83e050", [], "float", "same table (exhaustive check)"),
    ("ducker.py", r"EPS_[DF] = .*2\.0 \*\* -23", "a", "constant", [], "-", "exact power of two"),
    ("glibc_expf.py", r"\(2\.0 \*\* int\(n\)\)", "a", "expf", [], "double", "exact power of two (exponent scaling)"),
    ("crmath.py", r"D\(10\) \*\* -\(c\.prec|\(2 \*\* k\)", "a", "-", [], "-", "Decimal arithmetic / exact integer power"),
    ("insert_delay.py", r"D\(10\) \*\* -", "a", "-", [], "-", "Decimal arithmetic inside own correctly rounded tan/pow"),
    ("distortion.py", r"_D\(10\) \*\* _D\(y\)|10\*\*y \(the 1\.60", "a", "pow", [], "double", "correctly rounded pow10 (Decimal)"),
]


def code_lines(path):
    """(lineno, text) of code lines; triple-quoted docstrings and comments are blanked (crude but sufficient here)."""
    out = []; ind = False; q = None
    for k, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line
        if ind:
            if q in s: ind = False; s = s.split(q, 1)[1]
            else: continue
        while True:
            m = re.search(r'("""|\'\'\')', s)
            if not m: break
            q = m.group(1); rest = s[m.end():]
            if q in rest: s = s[:m.start()] + rest.split(q, 1)[1]
            else: s = s[:m.start()]; ind = True; break
        s = re.sub(r"#.*$", "", s) if "#" in s and not re.search(r"['\"][^'\"]*#", s) else s
        if s.strip(): out.append((k, s.rstrip("\n")))
    return out


def inventory(models_dir, im):
    plt = im.plt()
    rows = []; unclassified = []
    for fn in sorted(f for f in os.listdir(models_dir) if f.endswith(".py")):
        for ln, text in code_lines(os.path.join(models_dir, fn)):
            for m in HOST_RE.finditer(text):
                hit = None
                for ent in INVENTORY:
                    if (ent[0] is None or ent[0] == fn) and re.search(ent[1], text):
                        hit = ent; break
                if hit is None:
                    unclassified.append((fn, ln, text.strip())); continue
                _, _, cls, routine, sites, prec, why = hit
                site_ok = []
                for s in sites:
                    w = im.u32(s); tgt = (s + 8 + ((w & 0xffffff) - ((w & 0x800000) << 1)) * 4) & 0xffffffff
                    nm = routine.split()[0]
                    site_ok.append((w >> 24) & 0xf == 0xb and plt.get(tgt) == nm and PLT.get(nm) == tgt)
                rows.append({"file": fn, "line": ln, "call": m.group(0).strip(), "code": text.strip()[:110], "class": cls,
                             "routine": routine, "plt": hex(PLT[routine.split()[0]]) if routine.split()[0] in PLT else "-",
                             "sites": [hex(s) for s in sites], "sites_ok": all(site_ok), "precision": prec, "why": why})
    return rows, unclassified


# =========================================================================================================================
# B. library oracle
def new_emu():
    e = Emu()
    # libm feholdexcept reads _rtld_global_ro._dl_hwcap (+0x40); HWCAP_VFP as on the i.MX6 (cycle 008 / H031)
    e.uc.mem_map(0x3d000000, 0x1000, 3); e.wr(0x3d000040, struct.pack("<Q", 0x40))
    lm, base, _ = e._libs["libm.so.6"]
    for r in lm.dynamic_relocations:
        if r.has_symbol and r.symbol.name == "_rtld_global_ro": e.w32(base + r.address, 0x3d000000)
    return e


class EmuLibm:
    def __init__(self, e):
        self.e = e; self.x = {n: e.lib_exports[n][0] for n in ("tan", "pow", "exp", "log10f")}
    def tan(self, x): r0, r1 = self.e.call(self.x["tan"], *lohi(x)); return u2d(r0 | (r1 << 32))
    def exp(self, x): r0, r1 = self.e.call(self.x["exp"], *lohi(x)); return u2d(r0 | (r1 << 32))
    def pow(self, x, y): r0, r1 = self.e.call(self.x["pow"], *lohi(x), *lohi(y)); return u2d(r0 | (r1 << 32))
    def log10f(self, x): return u2f(self.e.call(self.x["log10f"], f2u(x))[0])


_REF = decimal.Context(prec=90, rounding=decimal.ROUND_HALF_EVEN)


def _ref_pi():
    with decimal.localcontext(_REF) as c:
        c.prec = 100
        # Gauss-Legendre (independent of crmath's Machin series)
        a = D(1); b = D(1) / D(2).sqrt(); t = D(1) / 4; p = D(1)
        for _ in range(9):
            an = (a + b) / 2; b = (a * b).sqrt(); t -= p * (a - an) ** 2; a = an; p *= 2
        return (a + b) ** 2 / (4 * t)
REF_PI = _ref_pi()


def ref_tan(x):
    if x == 0.0: return x
    with decimal.localcontext(_REF) as c:
        c.prec = 100
        y = D(x); k = (y / REF_PI).to_integral_value(); r = y - k * REF_PI
        # tan via the half-angle continued fraction-free route: sin/cos Taylor at prec 100
        r2 = r * r; s = r; t = r; n = 1
        while abs(t) > D(10) ** -105:
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2; s += t
        co = D(1); t = D(1); n = 0
        while abs(t) > D(10) ** -105:
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2; co += t
        return float(s / co)


def ref_pow(x, y):
    with decimal.localcontext(_REF):
        return float(D(x) ** D(y))


def ref_exp(x):
    with decimal.localcontext(_REF):
        return float(D(x).exp())


def ref_log10f(x):
    """Correctly rounded float32 log10 (nearest of the float32 neighbours of a double approximation)."""
    with decimal.localcontext(_REF):
        v = D(x).log10()
    u = f2u(F(float(v)))
    cands = [u2f(w) for w in (u - 1, u, u + 1)]
    return min(cands, key=lambda c: (abs(D(c) - v), f2u(c) & 1))


def oracle_args(seed=29):
    g = random.Random(seed)
    PI = 3.141592653589793
    FSS = (44100, 48000, 96000)
    A = {"tan": [], "pow": [], "exp": [], "log10f": []}
    # ---- tan: x = (double)fc * (pi / (double)fs), fc float in [5, fs/2] (biquad / PEQ / 1st-order HPF), + random
    for fs in FSS:
        nyq = float(fs // 2)
        for k in range(1001):                                    # LoFi/MMF cutoff grid 20*1000^v (both product orders)
            v = F(k / 1000.0)
            for fc in (F(math.pow(1000.0, v) * 20.0), F(F(math.pow(1000.0, v)) * F(20.0))):
                fc = min(max(fc, 5.0), nyq); A["tan"].append(("biquad fs%d grid" % fs, float(fc) * (PI / float(fs))))
        for _ in range(2500):
            fc = F(math.exp(g.uniform(math.log(5.0), math.log(nyq))))
            A["tan"].append(("biquad fs%d random fc" % fs, float(fc) * (PI / float(fs))))
        for fc in (10.0, 11027.5, 5.0, nyq):
            A["tan"].append(("1st-order HPF fs%d" % fs, float(F(fc)) * (PI / float(fs))))
    for _ in range(1500):
        A["tan"].append(("random (-1.5, 1.5)", g.uniform(-1.5, 1.5)))
    # ---- pow
    for _ in range(1500):                                         # PEQ configure 10^(gdb/20), gdb double of a float dB
        gdb = float(F(F(F(g.random()) * F(45.0)) - F(30.0)))
        A["pow"].append(("10^(gdb/20) PEQ configure", 10.0, gdb / 20.0))
    for _ in range(1500):                                         # glide lattice +-0.04 dB from random starts
        gdb = F(F(g.random() * 45.0) - 30.0); st = F(0.04) if g.random() < 0.5 else F(-0.04)
        for _ in range(g.randrange(1, 40)): gdb = F(gdb + st)
        A["pow"].append(("10^(F(gdb*0.05f)) PEQ/MMF gain", 10.0, float(F(F(gdb) * F(0.05)))))
        A["pow"].append(("10^(gdb/20) PEQ configure (glide)", 10.0, float(gdb) / 20.0))
    for k in range(1001):
        A["pow"].append(("1000^v grid", 1000.0, float(F(k / 1000.0))))
    for _ in range(1500):
        v = float(F(g.random()))
        A["pow"].append(("1000^v random", 1000.0, v))
        A["pow"].append(("1000.00006^v LoFi REDUCTION", 1000.0000610351562, v))
    for _ in range(800):                                          # LoFi PREAMP 10^(F(F(v*42)*0.05))
        A["pow"].append(("LoFi PREAMP", 10.0, float(F(F(F(g.random()) * F(42.0)) * F(0.05)))))
    l1000 = None
    for _ in range(800):                                          # MMF glide 10^(F(log10f(1000)/G)), G = F(F(1+F(8v))*64)
        G = F(F(F(1.0) + F(F(g.random()) * F(8.0))) * F(64.0))
        A["pow"].append(("MMF glide", 10.0, ("glide", G)))
    for k in (50.0, 1000.0):
        A["pow"].append(("LoFi static G", 10.0, ("static", k, 100.0 if k == 50.0 else 250.0)))
    for _ in range(800):                                          # PerfLoFi
        L = F(g.random() * 0.5); CM = F(g.random())
        A["pow"].append(("PerfLoFi bits", float(F(5.0 / 12.0)), float(F(L + L))))
        A["pow"].append(("PerfLoFi LPF", float(F(0.015)), float(F(F(F(1.0) - CM) * F(L + L)))))
        A["pow"].append(("PerfLoFi HPF", 400.0, float(F(F(L + L) * CM))))
    for _ in range(1000):
        A["pow"].append(("random", math.exp(g.uniform(math.log(0.01), math.log(1000.0))), g.uniform(-5.0, 5.0)))
    # ---- exp: Phaser pole exp(-62831.853071795864 / fs) for fs 8000..192000 (every 16th), + random
    for fs in range(8000, 192001, 16):
        A["exp"].append(("Phaser pole", -62831.853071795864 / float(fs)))
    for _ in range(1000):
        A["exp"].append(("random (-50, 50)", g.uniform(-50.0, 50.0)))
    # ---- log10f
    for _ in range(4000):                                         # cutoff ratios t/c
        t = F(math.exp(g.uniform(math.log(5.0), math.log(22050.0)))); c = F(math.exp(g.uniform(math.log(5.0), math.log(22050.0))))
        A["log10f"].append(("cutoff ratio", F(t / c)))
    for _ in range(2500):                                         # Q ratios
        t = F(F(0.2) + F(F(g.random()) * F(9.8))); c = F(F(0.2) + F(F(g.random()) * F(9.8)))
        A["log10f"].append(("Q ratio", F(t / c)))
    for _ in range(3500):
        A["log10f"].append(("random float", F(math.exp(g.uniform(math.log(1e-6), math.log(1e6))))))
    for c in (50.0, 1000.0):
        A["log10f"].append(("static constant", F(c)))
    return A


def run_oracle(P, J, M):
    CR, FP = M["crmath"], M["fdlibm_powf"]
    e = new_emu(); L = EmuLibm(e)
    A = oracle_args()
    res = {}
    # resolve the composite pow arguments with the real log10f (as the firmware does) before calling pow
    pw = []
    for tag, x, y in A["pow"]:
        if isinstance(y, tuple):
            if y[0] == "glide": y = float(F(L.log10f(F(1000.0)) / y[1]))
            else: y = float(F(L.log10f(F(y[1])) / F(y[2])))
        pw.append((tag, x, y))
    A["pow"] = pw
    A["log10f"] += [("MMF glide multiplier", F(CR.pow(10.0, y))) for tag, x, y in pw if tag == "MMF glide"]
    plans = {
        "tan": (lambda a: L.tan(a[1]), lambda a: ref_tan(a[1]), lambda a: math.tan(a[1]), lambda a: CR.tan(a[1]), "crmath.tan"),
        "pow": (lambda a: L.pow(a[1], a[2]), lambda a: ref_pow(a[1], a[2]), lambda a: math.pow(a[1], a[2]),
                lambda a: CR.pow(a[1], a[2]), "crmath.pow"),
        "exp": (lambda a: L.exp(a[1]), lambda a: ref_exp(a[1]), lambda a: math.exp(a[1]), lambda a: CR.exp(a[1]), "crmath.exp"),
        "log10f": (lambda a: L.log10f(a[1]), lambda a: ref_log10f(a[1]), lambda a: F(math.log10(a[1])),
                   lambda a: FP.log10f(a[1]), "fdlibm_powf.log10f"),
    }
    digest = hashlib.sha256()
    for nm, (fe, fr, fh, fo, oname) in plans.items():
        t0 = time.time(); n = cr = host = own = 0; ex_host = []; ex_cr = []; ex_own = []; bytag = {}
        for a in A[nm]:
            ve = fe(a); vr = fr(a); vh = fh(a); vo = fo(a)
            n += 1; isc = ve == vr; cr += isc; host += ve != vh; own += ve != vo
            bt = bytag.setdefault(a[0], [0, 0, 0, 0]); bt[0] += 1; bt[1] += isc; bt[2] += ve != vh; bt[3] += ve != vo
            digest.update(struct.pack("<d", ve))
            if ve != vh and len(ex_host) < 3: ex_host.append([a[1:], ve, vh])
            if not isc and len(ex_cr) < 3: ex_cr.append([a[1:], ve, vr])
            if ve != vo and len(ex_own) < 5: ex_own.append([a[1:], ve, vo])
        uniq = len(set(tuple(a[1:]) for a in A[nm]))
        res[nm] = {"n": n, "unique_args": uniq, "correctly_rounded": cr, "host_math_differs": host, "own_replacement": oname,
                   "own_mismatch": own, "by_domain": bytag, "ex_host": ex_host, "ex_not_cr": ex_cr, "ex_own": ex_own,
                   }
        P("  %-6s n=%5d (unique %5d)  correctly rounded %5d/%d  host math differs %4d  %s mismatches %d" %
          (nm, n, uniq, cr, n, host, oname, own))
        for tg, (k_, c_, h_, o_) in sorted(bytag.items()):
            P("           %-34s n=%5d cr=%5d host-diff=%4d own-diff=%d" % (tg, k_, c_, h_, o_))
    res["emu_results_sha256"] = digest.hexdigest()
    res["libm_sha256"] = e._libs["libm.so.6"][2]
    J["B_oracle"] = res
    return res


# =========================================================================================================================
# C. no host libm left in the switched models
class _Trap:
    def __init__(self, real): self._real = real; self.calls = []
    def __getattr__(self, nm):
        v = getattr(self._real, nm)
        if nm in ("tan", "pow", "exp", "log", "log10", "log2", "expm1", "log1p", "sin", "cos", "acos", "atan"):
            def trap(*a, nm=nm):
                self.calls.append(nm); raise RuntimeError("host math.%s called" % nm)
            return trap
        return v


def run_no_host(P, J):
    mods = load_models(MODELS, ["lofi", "mmf", "peq", "perf_lofi", "effectbase", "phaser"])
    trap = _Trap(math)
    for m in mods.values():
        if hasattr(m, "math"): m.math = trap
    g = random.Random(7); errs = []
    def blocks(obj, nparam, nblk=24):
        for b in range(nblk):
            if b % 3 == 0:
                for k in range(nparam): obj.set_param(k, F(g.random()) if k < 6 else float(g.randrange(0, 4)))
            L = [F(g.uniform(-0.5, 0.5)) for _ in range(64)]; R = [F(g.uniform(-0.5, 0.5)) for _ in range(64)]
            obj.process(L, R)
    cases = [("lofi.LoFi", lambda: mods["lofi"].LoFi(), 8), ("mmf.MMF", lambda: mods["mmf"].MMF(), 8),
             ("peq.PEQ", lambda: mods["peq"].PEQ(), 8), ("perf_lofi.PerfLoFi", lambda: mods["perf_lofi"].PerfLoFi(), 4),
             ("phaser.Phaser", lambda: mods["phaser"].Phaser(), 6)]
    for fs in (44100, 48000, 96000):
        cases.append(("phaser.Phaser(fs=%d)" % fs, lambda fs=fs: mods["phaser"].Phaser(fs), 6))
    out = {}
    for nm, mk, npar in cases:
        try:
            o = mk()
            if hasattr(o, "insert_defaults"): o.insert_defaults()
            blocks(o, npar); out[nm] = "ok"
        except Exception as ex:
            out[nm] = "%s: %s" % (type(ex).__name__, ex); errs.append(nm)
    try:
        h = mods["effectbase"].IirHpf1stOrder(44100); h.fc = F(10.0); h.coefs(); out["effectbase.IirHpf1stOrder"] = "ok"
    except Exception as ex:
        out["effectbase.IirHpf1stOrder"] = "%s: %s" % (type(ex).__name__, ex); errs.append("effectbase")
    P("  models run with host math.tan/pow/exp/log/log10/sin/cos/acos/atan trapped: %s" % out)
    P("  host math calls attempted: %d" % len(trap.calls))
    J["C_no_host"] = {"cases": out, "host_calls": len(trap.calls)}
    return not errs and not trap.calls


# =========================================================================================================================
# D. random-setting stress against the emulated 1.60 coefficient routines
def stress(P, J, new, old, nscale=1.0):
    import H007_effect_emu as H7
    import H023_mmf_model as H23
    import H026_peq_model as H26
    import H064_perf_fx as H64
    g = random.Random(4029)
    res = {}; digest = hashlib.sha256()
    def N(k): return max(1, int(k * nscale))
    def rec(name, n, bad_new, bad_old, ex):
        res[name] = {"n": n, "new_model_mismatch": bad_new, "old_model_mismatch": bad_old, "examples": ex[:4]}
        P("  %-58s n=%5d  current model mismatches %d   pre-change model mismatches %d" % (name, n, bad_new, bad_old))

    def rand_fc(fs):
        r = g.random(); nyq = float(fs // 2)
        if r < 0.5: return F(math.exp(g.uniform(math.log(5.0), math.log(nyq))))
        if r < 0.8: return min(max(F(math.pow(1000.0, float(F(g.random()))) * 20.0), 5.0), nyq)
        return min(max(F(F(math.pow(1000.0, float(F(g.random())))) * F(20.0)), 5.0), nyq)

    def rand_q():
        r = g.random()
        q = F(F(0.2) + F(F(g.random()) * F(9.8))) if r < 0.5 else F(F(0.1) + F(F(g.random()) * F(9.9)))
        return math.sqrt(float(q)) if g.random() < 0.25 else float(q)

    e = new_emu(); out = e.malloc(128, "harness: coef out"); fobj = e.malloc(0x100, "harness: fake IirFilter2")
    e.w32(fobj + 0x8c, out)

    # ---- D1 biquad calcCoefs ------------------------------------------------------------------------------------------
    t0 = time.time(); n = bn = bo = 0; ex = []
    for i in range(N(12000)):
        kind, addr = [("hpf", 0xe1bb8), ("lpf", 0xe1ca0), ("bpf", 0xe1d88)][i % 3]
        fs = (44100, 48000, 96000)[(i // 3) % 3]
        fc = rand_fc(fs); Q = rand_q()
        e.call(addr, out, f2u(fc), *lohi(Q), stack_args=(fs,))
        ew = [e.u32(out + 4 * j) for j in range(5)]
        digest.update(struct.pack("<5I", *ew))
        ws = []
        for M in (new, old):
            b = M["lofi"].Biquad(kind, fs); b.fc = fc; b.Q = Q; b.coefs()
            ws.append([f2u(b.b0), f2u(b.b1), f2u(b.b2), f2u(b.a1), f2u(b.a2)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew:
            ex.append({"kind": kind, "fs": fs, "fc": fc, "Q": Q, "emu": [hex(w) for w in ew], "new": [hex(w) for w in ws[0]],
                       "old": [hex(w) for w in ws[1]]})
    rec("D1 IirFilter calcCoefs 0xe1bb8/0xe1ca0/0xe1d88 (fs 44.1/48/96k)", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))

    # ---- D2 1st-order HPF -------------------------------------------------------------------------------------------
    t0 = time.time(); n = bn = bo = 0; ex = []
    for i in range(N(10000)):
        fs = (44100, 48000, 96000)[i % 3]
        fc = F(10.0) if i % 50 == 0 else rand_fc(fs)
        e.wr(out, b"\0" * 16)
        e.call(0xe1aa0, out, f2u(fc), fs)
        ew = [e.u32(out), e.u32(out + 4), e.u32(out + 12)]
        digest.update(struct.pack("<3I", *ew))
        ws = []
        for M in (new, old):
            h = M["effectbase"].IirHpf1stOrder(fs); h.fc = fc; h.coefs(); ws.append([f2u(h.b0), f2u(h.b1), f2u(h.a1)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"fs": fs, "fc": fc, "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D2 IirHpf1stOrder calcCoefs 0xe1aa0 (fs 44.1/48/96k)", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))

    # ---- D3 PEQ IirFilter2 ---------------------------------------------------------------------------------------------
    t0 = time.time()
    ep = H26.EmuPEQ()
    objs = {}
    for B in (ep.u(ep.o + 0x498), ep.u(ep.o + 0x49c)):
        for k in range(ep.u(B + 8)):
            S = ep.u(ep.u(B) + 4 * k); p4 = ep.u(S + 4)
            if p4:
                vt = ep.u(p4)
                objs.setdefault({0x83bcc0: "lowshelf", 0x83bcf0: "peaking"}.get(vt, hex(vt)), p4)
    assert set(objs) >= {"lowshelf", "peaking"}, objs
    n = bn = bo = 0; ex = []
    for i in range(N(6000)):
        kind = ("lowshelf", "peaking")[i % 2]; o = objs[kind]
        fc = F(F(math.pow(1000.0, float(F(g.random())))) * F(20.0)) if g.random() < 0.6 else rand_fc(44100)
        Q = float(F(F(0.1) + F(F(g.random()) * F(9.9))))
        if g.random() < 0.6: gdb = float(F(F(F(g.random()) * F(45.0)) - F(30.0)))
        else: gdb = float(F(g.uniform(-80.0, 40.0)))
        ep.e.call(0xe2ab4, o, f2u(fc), *lohi(Q), stack_args=(*lohi(gdb), 0))
        cf = ep.u(o + 0x8c)
        ew = [ep.u(cf + 8 * j) for j in range(5)] + [ep.u(cf + 8 * j + 4) for j in range(5)]
        ep_p = struct.unpack("<d", ep.e.rd(o + 0x38, 8))[0]
        digest.update(struct.pack("<10I", *ew))
        ws = []
        for M in (new, old):
            m = M["peq"].IirFilter2(kind, 44100); m.configure(fc, Q, gdb, 0)
            w5 = [f2u(m.b0), f2u(m.b1), f2u(m.b2), f2u(m.a1), f2u(m.a2)]; ws.append(w5 + w5 + [m.p])
        ew_p = ew + [ep_p]
        n += 1; bn += ws[0] != ew_p; bo += ws[1] != ew_p
        if ws[0] != ew_p or ws[1] != ew_p:
            ex.append({"kind": kind, "fc": fc, "Q": Q, "gdb": gdb, "emu": ew_p, "new": ws[0], "old": ws[1]})
    rec("D3a PEQ IirFilter2 configure 0xe2ab4 (pow + calcCoefs, 44.1k)", n, bn, bo, ex)
    n = bn = bo = 0; ex = []
    for i in range(N(4000)):
        kind, addr = [("lowshelf", 0xe2540), ("peaking", 0xe2440)][i % 2]
        fs = (48000, 96000)[(i // 2) % 2]
        fc = min(rand_fc(fs), F(float(fs // 2))); Q = float(F(F(0.1) + F(F(g.random()) * F(9.9))))
        gdb = float(F(F(F(g.random()) * F(45.0)) - F(30.0))); p = new["crmath"].pow(10.0, gdb / 20.0) - 1.0
        e.call(addr, fobj, f2u(fc), *lohi(Q), stack_args=(*lohi(p), f2u(float(fs))))
        ew = [e.u32(out + 8 * j) for j in range(5)]
        digest.update(struct.pack("<5I", *ew))
        ws = []
        for M in (new, old):
            m = M["peq"].IirFilter2(kind, fs); m.coefs(fc, Q, p, F(float(fs)))
            ws.append([f2u(m.b0), f2u(m.b1), f2u(m.b2), f2u(m.a1), f2u(m.a2)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"kind": kind, "fs": fs, "fc": fc, "Q": Q, "p": p, "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D3b PEQ calcCoefs 0xe2540/0xe2440 direct (fs 48/96k)", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))

    # ---- D4 ramp setup step counts (log10f) and MMF setGlide (log10f + pow) -------------------------------------------
    t0 = time.time()
    lr = H7.Run(H7.EFFECTS["lofi"]); lr.insert_init(); le = lr.e; LC = le.u32(lr.obj + 0x4a4)
    em = H23.EmuMMF(); MC = em.u(em.o + 0x498)
    def wf(ee, a, v): ee.w32(a, f2u(v))
    def rf(ee, a): return ee.u32(a)
    def ri(ee, a): v = ee.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    n = bn = bo = 0; ex = []
    for i in range(N(5000)):
        ct = rand_fc(44100); cc = rand_fc(44100); qt = F(F(0.2) + F(F(g.random()) * F(9.8))); qc = F(F(0.2) + F(F(g.random()) * F(9.8)))
        if i % 10 == 0: cc = ct
        for a_, v_ in ((0x18, ct), (0x1c, cc), (0x28, qt), (0x2c, qc)): wf(le, LC + a_, v_)
        le.wr(LC + 0x41, b"\x01")
        le.call(0xfb994, LC)
        ew = [ri(le, LC + 0x24), rf(le, LC + 0x20), ri(le, LC + 0x34), rf(le, LC + 0x30), ri(le, LC + 0x3c)]
        digest.update(struct.pack("<5i", *[w - (1 << 32) if w > 0x7fffffff else w for w in ew]))
        ws = []
        for M in (new, old):
            c = M["lofi"].FilterContainer(44100); c.cut_t, c.cut_c, c.q_t, c.q_c, c.dirty41 = ct, cc, qt, qc, 1
            c.ramp_setup(); ws.append([c.cut_steps, f2u(c.cut_mult), c.q_steps, f2u(c.q_mult), c.maxsteps])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"ct": ct, "cc": cc, "qt": qt, "qc": qc, "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D4a LoFi ramp setup 0xfb994 (log10f step counts)", n, bn, bo, ex)
    n = bn = bo = 0; ex = []
    for i in range(N(5000)):
        v = F(g.random()) if i % 20 else F(0.0)
        gm, gflag = new["mmf"].MMF.glide_steps(v)
        em.e.call(0x108570, MC, f2u(F(F(F(1.0) + F(F(v) * F(8.0))) * F(64.0))))
        ct = rand_fc(44100); cc = rand_fc(44100); qt = F(F(0.2) + F(F(g.random()) * F(9.8))); qc = F(F(0.2) + F(F(g.random()) * F(9.8)))
        for a_, v_ in ((0x18, ct), (0x1c, cc), (0x28, qt), (0x2c, qc)): wf(em.e, MC + a_, v_)
        em.e.wr(MC + 0x41, b"\x01")
        em.e.call(0x108608, MC)
        ew = [rf(em.e, MC + 0x44), em.b(MC + 0x42), rf(em.e, MC + 0x48), rf(em.e, MC + 0x4c),
              ri(em.e, MC + 0x24), rf(em.e, MC + 0x20), ri(em.e, MC + 0x34), rf(em.e, MC + 0x30), ri(em.e, MC + 0x3c)]
        digest.update(struct.pack("<9q", *ew))
        ws = []
        for M in (new, old):
            gm_, gf_ = M["mmf"].MMF.glide_steps(v)
            c = M["mmf"].FilterContainer(44100); c.glide42 = gf_; c.set_glide_steps(gm_)
            c.cut_t, c.cut_c, c.q_t, c.q_c, c.dirty41 = ct, cc, qt, qc, 1
            c.ramp_setup()
            ws.append([f2u(c.g44), c.glide42, f2u(c.up48), f2u(c.dn4c), c.cut_steps, f2u(c.cut_mult), c.q_steps, f2u(c.q_mult),
                       c.maxsteps])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"v": v, "ct": ct, "cc": cc, "qt": qt, "qc": qc, "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D4b MMF setGlide 0x108570 (no caller found) + ramp setup 0x108608 (log10f, pow)", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))

    # ---- D5 parameter apply paths ---------------------------------------------------------------------------------------
    t0 = time.time()
    n = bn = bo = 0; ex = []
    P_ = le.u32(lr.obj + 0x498); H_ = le.u32(lr.obj + 0x4a0)
    for i in range(N(4000)):
        v0, v1, v3 = F(g.random()), F(g.random()), F(g.random())
        if i % 25 == 0 and i: v0, v1, v3 = F(0.0), F(1.0), F(1.0)   # range ends (not at i = 0, see D5b)
        for k_, v_ in ((0, v0), (1, v1), (3, v3)): lr.set_param(k_, v_)
        le.call(0xfb20c, lr.obj)
        ew = [rf(le, P_ + 4), rf(le, H_ + 0xc), rf(le, LC + 0x18)]
        digest.update(struct.pack("<3I", *ew))
        ws = []
        for M in (new, old):
            m = M["lofi"].LoFi()
            for k_, v_ in ((0, v0), (1, v1), (3, v3)): m.set_param(k_, v_)
            m.apply_params(); ws.append([f2u(m.pre_t), f2u(m.sh_step), f2u(m.filt.cut_t)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"v": [v0, v1, v3], "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D5a LoFi apply 0xfb20c (PREAMP/REDUCTION/CUTOFF: pow)", n, bn, bo, ex)
    n = bn = bo = 0; ex = []
    G_ = em.u(em.o + 0x49c)
    for i in range(N(3000)):
        v0, v1, v3 = F(g.random()), F(g.random()), F(g.random())
        if i % 25 == 0 and i: v0, v1, v3 = F(1.0), F(1.0), F(0.0)   # range ends (not at i = 0: an unchanged value is not re-applied)
        em.set_param(0, v0); em.set_param(1, v1); em.set_param(3, v3)
        em.e.call(0x107d18, em.o)
        ew = [rf(em.e, MC + 0x18), rf(em.e, G_ + 4), rf(em.e, MC + 0x44), em.b(MC + 0x42), rf(em.e, MC + 0x48), rf(em.e, MC + 0x4c)]
        digest.update(struct.pack("<6I", *ew))
        ws = []
        for M in (new, old):
            m = M["mmf"].MMF(); m.set_param(0, v0); m.set_param(1, v1); m.set_param(3, v3); m.apply_params()
            C = m.filt                                                                 # gain target = gain_lin (apply_params)
            ws.append([f2u(C.cut_t), f2u(M["mmf"].MMF.gain_lin(v1)), f2u(C.g44), C.glide42, f2u(C.up48), f2u(C.dn4c)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"v": [v0, v1, v3], "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D5b MMF apply 0x107d18 (CUTOFF/GAIN/GLIDE: pow, log10f)", n, bn, bo, ex)
    n = bn = bo = 0; ex = []
    ef = H64.EmuPerf(); o = ef.o
    for i in range(N(3000)):
        vs = [F(g.random()) for _ in range(4)]
        if i % 3 == 0: vs[0] = F(vs[0] * 0.5)                   # LEVEL < 0.5 (bits pow branch) more often
        st0 = ef.state()
        for k_ in range(4): ef.set_param(k_, vs[k_])
        ef.e.call(0xfc278, o)
        st = ef.state()
        ew = [st["cr.bits"], st["cr.scale"], st["cr.inv"], st["sh.step"], st["fa.cut_t"], st["fb.cut_t"], st["fa.q_t"], st["fb.q_t"]]
        digest.update(struct.pack("<8q", *ew))
        ws = []
        for M in (new, old):
            m = M["perf_lofi"].PerfLoFi()
            m.fa.q_t = u2f(st0["fa.q_t"]); m.fb.q_t = u2f(st0["fb.q_t"])
            for k_ in range(4): m.set_param(k_, vs[k_])
            m.apply_params()
            ws.append([m.bits, f2u(m.scale), f2u(m.inv), f2u(m.sh_step), f2u(m.fa.cut_t), f2u(m.fb.cut_t), f2u(m.fa.q_t), f2u(m.fb.q_t)])
        n += 1; bn += ws[0] != ew; bo += ws[1] != ew
        if ws[0] != ew or ws[1] != ew: ex.append({"v": vs, "emu": ew, "new": ws[0], "old": ws[1]})
    rec("D5c PerfLoFi apply 0xfc278 (+ filter update 0xfacec: pow, powf)", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))

    # ---- D6 PEQ band gain law ------------------------------------------------------------------------------------------
    t0 = time.time(); L = EmuLibm(e); n = bn = bo = 0; ex = []
    for i in range(N(10000)):
        gdb = F(F(F(g.random()) * F(45.0)) - F(30.0)); st = F(0.04) if g.random() < 0.5 else F(-0.04)
        for _ in range(g.randrange(0, 60)): gdb = F(gdb + st)
        ev = f2u(F(L.pow(10.0, float(F(F(gdb) * F(0.05))))))
        digest.update(struct.pack("<I", ev))
        ws = [f2u(M["peq"].gain_lin(gdb)) for M in (new, old)]
        n += 1; bn += ws[0] != ev; bo += ws[1] != ev
        if ws[0] != ev or ws[1] != ev: ex.append({"gdb": gdb, "emu": ev, "new": ws[0], "old": ws[1]})
    rec("D6 PEQ gain (float)pow(10, F(gdb*0.05f)) with the real pow", n, bn, bo, ex)
    print("      (%.0f s)" % (time.time() - t0))
    res["emu_results_sha256"] = digest.hexdigest()
    J["D_stress"] = res
    return res


# =========================================================================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H029"))
    ap.add_argument("--old-models", default=os.path.join(HERE, "out", "H029", "oldmodels"),
                    help="directory with the pre-change model copy (git show HEAD:harness/models/*.py)")
    ap.add_argument("--scale", type=float, default=1.0, help="stress size factor (1.0 = >= 10^4 per group)")
    ap.add_argument("--skip", default="", help="comma list of sections to skip (A,B,C,D)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []
    def P(s=""): print(s); rep.append(s)
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    skip = set(x.strip().upper() for x in a.skip.split(",") if x.strip())
    im = sp16img.Image()
    plt = im.plt()
    check(all(plt.get(v) == k for k, v in PLT.items()), "PLT stubs: %s" % {k: hex(v) for k, v in PLT.items()})
    has_old = os.path.isdir(a.old_models)
    new = load_models(MODELS, ["crmath", "fdlibm_powf", "lofi", "mmf", "peq", "perf_lofi", "effectbase", "phaser"])
    old = load_models(a.old_models, ["lofi", "mmf", "peq", "perf_lofi", "effectbase", "phaser"]) if has_old else None
    J["old_models_dir"] = a.old_models if has_old else None
    if has_old:
        J["old_models_sha256"] = {f: sha(open(os.path.join(a.old_models, f), "rb").read())
                                  for f in sorted(os.listdir(a.old_models)) if f.endswith(".py")}
    J["models_sha256"] = {f: sha(open(os.path.join(MODELS, f), "rb").read()) for f in sorted(os.listdir(MODELS)) if f.endswith(".py")}

    if "A" not in skip:
        P("== A inventory of host-libm calls in harness/models/*.py ==")
        for tag, d in (("pre-change", a.old_models if has_old else None), ("current", MODELS)):
            if d is None: continue
            rows, uncl = inventory(d, im)
            J["A_inventory_" + tag] = rows; J["A_unclassified_" + tag] = uncl
            P("  -- %s models (%s): %d hits" % (tag, os.path.relpath(d, ROOT), len(rows)))
            for r in rows:
                P("   [%s] %-14s %4d  %-12s -> %-16s %-7s sites %s%s  %s" %
                  (r["class"], r["file"], r["line"], r["call"], r["routine"], r["plt"], ",".join(r["sites"]) or "-",
                   "" if r["sites_ok"] else " (SITE CHECK FAILED)", r["why"][:70]))
            for u in uncl: P("   [?] UNCLASSIFIED %s:%d %s" % u)
            check(not uncl, "%s: every host-libm hit is classified (%d unclassified)" % (tag, len(uncl)))
            check(all(r["sites_ok"] for r in rows), "%s: every listed 1.60 call site is a direct bl to the named PLT stub" % tag)
            nb = [r for r in rows if r["class"] == "b"]
            if tag == "current":
                check(not nb, "current: no class-(b) host-libm call left (%d)" % len(nb))
            else:
                P("  pre-change class-(b) rows: %d" % len(nb))

    if "B" not in skip:
        P(); P("== B library oracle: real 1.60 libm (unicorn) vs reference / host / own replacement ==")
        r = run_oracle(P, J, new)
        for nm in ("tan", "pow", "exp", "log10f"):
            check(r[nm]["unique_args"] >= 10000 and r[nm]["own_mismatch"] == 0,
                  "%s: %s matches the emulated 1.60 routine on %d/%d arguments" %
                  (nm, r[nm]["own_replacement"], r[nm]["n"] - r[nm]["own_mismatch"], r[nm]["n"]))

    if "C" not in skip:
        P(); P("== C switched models never call host math.tan/pow/exp/log/log10 ==")
        check(run_no_host(P, J), "LoFi, MMF, PEQ, PerfLoFi, Phaser (3 fs), EffectBase HPF run with host libm trapped")

    if "D" not in skip:
        P(); P("== D random-setting stress vs the emulated 1.60 coefficient routines (real libm) ==")
        if old is None:
            P("  (no --old-models directory: pre-change comparison uses the current models)"); old = new
        r = stress(P, J, new, old, a.scale)
        for k, v in r.items():
            if not isinstance(v, dict): continue
            check(v["new_model_mismatch"] == 0,
                  "%s: current model = emulation in %d/%d settings" % (k, v["n"] - v["new_model_mismatch"], v["n"]))
        groups = {"LoFi/MMF biquad (D1)": ["D1"], "PEQ calcCoefs (D3a+D3b)": ["D3a", "D3b"], "LoFi+MMF step/glide (D4a+D4b)": ["D4a", "D4b"],
                  "param apply (D5a+D5b+D5c)": ["D5a", "D5b", "D5c"], "EffectBase HPF (D2)": ["D2"], "PEQ gain (D6)": ["D6"]}
        for gname, pre in groups.items():
            tot = sum(v["n"] for k, v in r.items() if isinstance(v, dict) and k.split()[0] in pre)
            check(tot >= 10000, "%s: %d settings (>= 10^4)" % (gname, tot))

    P(); P("RESULT: %d failed checks" % len(fails))
    J["fails"] = fails
    open(os.path.join(a.out, "h029_report.txt"), "w").write("\n".join(rep) + "\n")
    js = json.dumps(J, indent=1, sort_keys=True, default=str)
    open(os.path.join(a.out, "h029.json"), "w").write(js)
    print("report sha256 %s" % sha(("\n".join(rep) + "\n").encode()))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
