#!/usr/bin/env python3
"""H076 (+ H025) — slot-27 reset of PEQ (0x10a7ec), MultiModeFilter (0x107fa8) and LoFi (0xfb5a4): exact semantics, state-dump
agreement with the models' reset(), and the H044 composition across stop / re-activation.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Emulation is guest-memory only (unicorn); nothing is
written outside --out and no image is built. Own code only; Pioneer bytes are read at run time and never stored.

Sections (criteria of kb/cycles/027.md):
  C1  write set: every guest heap write made by the REAL slot 27, mapped to named fields, per case (which fields are written,
      which change value). Static facts come from the REA decompile (recorded in the cycle file).
  C2  state dumps: the real slot 25 rig of each effect (H021 / H023 / H026 builders) processes audio with non-default
      parameters (mid-glide changes, pending changes, type switches), then real slot 27 vs model reset(); full field dumps
      (raw bits, all filter taps of every stage, gates, ramps, glide state, parameters) before and after must be equal, and
      the next blocks stay bit-exact. Model mutants (alternative reset semantics) must be refuted.
  C3  regression: H021 / H023 / H026 / H044 re-run as subprocesses; their recorded hashes must be unchanged.
  C4  composition: real effect through the real slot 18 0x106de4 (Insert ctor state, F141) vs effectbase.EffectBase + model,
      >= 220 blocks, activation, mid-run parameter changes (incl. while stopped and mid-glide), two stops / re-activations;
      3+ settings x {noise, sine, impulse} per effect. Then the full 13-effect H044 c4_ext table.
  C5  side results: what slot 27 does / does not reset that is audible (re-activation transient vs no reset; PEQ first-block
      start-up through slot 18 = H030).
Run: .venv/bin/python -B harness/H076_slot27_reset.py --out DIR      (--skip-regress: no C3 subprocesses)
"""
import argparse, hashlib, json, math, os, random, struct, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
from unicorn import UC_HOOK_MEM_WRITE                          # noqa: E402
from emu import f2u, u2f, d2u, HEAP_BASE, HEAP_SIZE            # noqa: E402
import H044_effectbase_wrapper as H44                          # noqa: E402
import H021_lofi_model as X21                                  # noqa: E402
import H023_mmf_model as X23                                   # noqa: E402
import H026_peq_model as X26                                   # noqa: E402
import effectbase as EB                                        # noqa: E402
import lofi as ML                                              # noqa: E402
import mmf as MM                                               # noqa: E402
import peq as MP                                               # noqa: E402
from lofi import F                                             # noqa: E402

N = 64
SLOT27 = {"lofi": 0xfb5a4, "mmf": 0x107fa8, "peq": 0x10a7ec}


def sha(b): return hashlib.sha256(b).hexdigest()
def pack(xs): return struct.pack("<%df" % len(xs), *xs)


# ===================================================================================================================== field tables
# Emulated side: name -> (address, type); model side: name -> bits. Types: f (float32 bits), i (int32), b (byte), d (double bits).
def _mbits(t, v):
    if t == "f": return f2u(float(v))
    if t == "d": return d2u(float(v))
    if t == "b": return int(v) & 0xff
    return int(v) & 0xffffffff


def _eread(e, a, t):
    if t == "b": return e.rd(a, 1)[0]
    if t == "d": return struct.unpack("<Q", e.rd(a, 8))[0]
    return e.u32(a)


class Fields:
    """Pairs of emulated (addr, type) and model value per field name."""
    def __init__(self): self.E = {}; self.M = {}
    def add(self, name, t, addr=None, mval=None):
        if addr is not None: self.E[name] = (addr, t)
        if mval is not None or addr is None: self.M[name] = (t, mval)


def f_biquad(FE, e, s, m, pre):           # IirFilter (0x50): F029
    u = e.u32 if e else None
    for nm, off, t, mv in (("fc", 0xc, "f", m.fc), ("k", 0x24, "f", m.k), ("b0", 0x28, "f", m.b0), ("b1", 0x2c, "f", m.b1),
                           ("b2", 0x30, "f", m.b2), ("a1", 0x34, "f", m.a1), ("a2", 0x38, "f", m.a2), ("Q", 0x40, "d", m.Q),
                           ("reseed", 0x48, "b", m.flag48)):
        FE.add(pre + nm, t, s + off if e else None, mv)
    for j in range(4):
        p = u(s + 0x10 + 4 * j) if e else None
        for q, (nm, mv) in enumerate((("vL", m.v[j][0]), ("vR", m.v[j][1]), ("yL", m.y[j][0]), ("yR", m.y[j][1]))):
            FE.add(pre + "tap%d.%s" % (j + 1, nm), "f", p + 4 * q if e else None, mv)
    p = u(s + 0x20) if e else None
    FE.add(pre + "yprev.L", "f", p if e else None, m.yprev[0]); FE.add(pre + "yprev.R", "f", p + 4 if e else None, m.yprev[1])


def f_iir2(FE, e, s, m, pre):             # IirFilter2 (0x90): F040
    u = e.u32 if e else None
    for nm, off, t, mv in (("fc", 8, "f", m.fc), ("Q", 0x18, "d", m.Q), ("p", 0x38, "d", m.p), ("gdb", 0x58, "d", m.gdb),
                           ("reseed", 0x78, "b", m.flag78)):
        FE.add(pre + nm, t, s + off if e else None, mv)
    for j in range(4):
        p = u(s + 0x7c + 4 * j) if e else None
        for q, (nm, mv) in enumerate((("xL", m.x[j][0]), ("xR", m.x[j][1]), ("yL", m.y[j][0]), ("yR", m.y[j][1]))):
            FE.add(pre + "tap%d.%s" % (j + 1, nm), "f", p + 4 * q if e else None, mv)
    c = u(s + 0x8c) if e else None
    for j, (nm, mv) in enumerate((("b0", m.b0), ("b1", m.b1), ("b2", m.b2), ("a1", m.a1), ("a2", m.a2))):
        FE.add(pre + nm + ".L", "f", c + 8 * j if e else None, mv); FE.add(pre + nm + ".R", "f", c + 8 * j + 4 if e else None, mv)


def f_gate(FE, e, g, m, pre):             # SignalGate ramp (F029)
    r = m.r
    for nm, off, t, mv in (("state", 0x20, "i", r.state), ("cur", 0x24, "f", r.cur), ("target", 0x28, "f", r.target),
                           ("inc", 0x2c, "f", r.inc), ("rem", 0x30, "i", r.rem)):
        FE.add(pre + nm, t, g + off if e else None, mv)


def f_gainramp(FE, e, G, m, pre):         # GainRamp (F035)
    for nm, off, t, mv in (("inc", 0, "f", m.inc), ("target", 4, "f", m.target), ("cur", 8, "f", m.cur), ("rem", 0xc, "i", m.rem),
                           ("N", 0x10, "i", m.N), ("invN", 0x14, "f", m.invN), ("delay", 0x18, "i", m.delay),
                           ("idle", 0x1c, "b", m.idle), ("state", 0x20, "i", m.state)):
        FE.add(pre + nm, t, G + off if e else None, mv)


def f_params(FE, e, o, m, poff):
    for k, off in sorted(poff.items()):
        p = m.params[k]
        if p.kind == "float":
            FE.add("param%d.last" % k, "f", o + off + 0x24 if e else None, p.last); FE.add("param%d.cur" % k, "f", o + off + 0x28 if e else None, p.cur)
        else:
            FE.add("param%d.last" % k, "i", o + off + 0x40 if e else None, p.last); FE.add("param%d.cur" % k, "i", o + off + 0x44 if e else None, p.cur)


def fields_lofi(e, o, m):
    FE = Fields(); u = e.u32
    P, Q, H, C, G = (u(o + x) for x in (0x498, 0x49c, 0x4a0, 0x4a4, 0x4a8))
    f_params(FE, e, o, m, X21.PARAM_OFF)
    FE.add("pos.pending", "i", o + 0x4ac, m.pos_pending); FE.add("pos.cur", "i", o + 0x4b0, m.pos_cur)
    for nm, off, t, mv in (("N", 0, "i", m.pre_N), ("target", 4, "f", m.pre_t), ("cur", 8, "f", m.pre_c), ("inc", 0xc, "f", m.pre_inc),
                           ("cnt", 0x10, "i", m.pre_cnt)):
        FE.add("preamp." + nm, t, P + off, mv)
    for nm, off, t, mv in (("bits", 0, "i", m.bits), ("scale", 4, "f", m.scale), ("inv", 8, "f", m.inv)):
        FE.add("crusher." + nm, t, Q + off, mv)
    for nm, off, mv in (("phase", 8, m.sh_phase), ("step", 0xc, m.sh_step), ("holdL", 0x10, m.sh_hold[0]), ("holdR", 0x14, m.sh_hold[1])):
        FE.add("sh." + nm, "f", H + off, mv)
    c = m.filt
    for nm, off, t, mv in (("pending", 0x10, "i", c.pending), ("cur", 0x14, "i", c.cur), ("cut_t", 0x18, "f", c.cut_t),
                           ("cut_c", 0x1c, "f", c.cut_c), ("cut_mult", 0x20, "f", c.cut_mult), ("cut_steps", 0x24, "i", c.cut_steps),
                           ("q_t", 0x28, "f", c.q_t), ("q_c", 0x2c, "f", c.q_c), ("q_mult", 0x30, "f", c.q_mult),
                           ("q_steps", 0x34, "i", c.q_steps), ("next", 0x38, "f", c.next), ("maxsteps", 0x3c, "i", c.maxsteps),
                           ("recompute", 0x40, "b", c.flag40), ("dirty", 0x41, "b", c.dirty41)):
        FE.add("filt." + nm, t, C + off, mv)
    f_gate(FE, e, u(C + 0xc), c.gate, "filt.gate.")
    for k in range(4):
        f_biquad(FE, e, u(u(C) + 4 * k), c.subs[k], "filt.sub%d.%s." % (k, ["hpf", "lpf", "bpf", "off"][k]))
    f_gate(FE, e, G, m.gate, "posgate.")
    return FE


def fields_mmf(e, o, m):
    FE = Fields(); u = e.u32
    C, G = u(o + 0x498), u(o + 0x49c)
    f_params(FE, e, o, m, X23.PARAM_OFF)
    c = m.filt
    for nm, off, t, mv in (("pending", 0x10, "i", c.pending), ("cur", 0x14, "i", c.cur), ("cut_t", 0x18, "f", c.cut_t),
                           ("cut_c", 0x1c, "f", c.cut_c), ("cut_mult", 0x20, "f", c.cut_mult), ("cut_steps", 0x24, "i", c.cut_steps),
                           ("q_t", 0x28, "f", c.q_t), ("q_c", 0x2c, "f", c.q_c), ("q_mult", 0x30, "f", c.q_mult),
                           ("q_steps", 0x34, "i", c.q_steps), ("next", 0x38, "f", c.next), ("maxsteps", 0x3c, "i", c.maxsteps),
                           ("recompute", 0x40, "b", c.flag40), ("dirty", 0x41, "b", c.dirty41), ("glide_on", 0x42, "b", c.glide42),
                           ("G", 0x44, "f", c.g44), ("up", 0x48, "f", c.up48), ("down", 0x4c, "f", c.dn4c)):
        FE.add("filt." + nm, t, C + off, mv)
    f_gate(FE, e, u(C + 0xc), c.gate, "filt.gate.")
    for k in range(7):
        w = u(u(C) + 4 * k); mw = c.w[k]
        FE.add("filt.kind%d.kind" % k, "i", w, mw.kind)
        for j, s in enumerate(mw.stages):
            f_biquad(FE, e, u(w + 4 + 4 * j), s, "filt.kind%d.bq%d." % (k, j + 1))
        if len(mw.stages) < 2: FE.add("filt.kind%d.ptr8" % k, "i", w + 8, 0)
    f_gainramp(FE, e, G, m.gain, "gain.")
    return FE


def fields_peq(e, o, m):
    FE = Fields(); u = e.u32
    f_params(FE, e, o, m, X26.PARAM_OFF)
    for bi, off0 in enumerate((0x498, 0x49c)):
        B = u(o + off0); b = m.bands[bi]; pre = "band%d." % (bi + 1)
        f_gate(FE, e, u(B + 0xc), b.gate, pre + "gate."); f_gainramp(FE, e, u(B + 0x10), b.gain, pre + "gain.")
        for nm, off, t, mv in (("pending", 0x14, "i", b.pending), ("cur", 0x18, "i", b.cur), ("f_t", 0x1c, "f", b.ft),
                               ("f_c", 0x20, "f", b.fc), ("f_mult", 0x24, "f", b.fmult), ("f_steps", 0x2c, "i", b.fsteps),
                               ("q_t", 0x30, "f", b.qt), ("q_c", 0x34, "f", b.qc), ("q_mult", 0x38, "f", b.qmult),
                               ("q_steps", 0x40, "i", b.qsteps), ("g_t", 0x44, "f", b.gt), ("g_c", 0x48, "f", b.gc),
                               ("g_step", 0x4c, "f", b.gstep), ("g_steps", 0x54, "i", b.gsteps), ("next", 0x58, "f", b.next),
                               ("maxsteps", 0x5c, "i", b.maxsteps), ("recompute", 0x60, "b", b.flag60), ("stepnow", 0x61, "b", b.flag61),
                               ("dirty", 0x62, "b", b.dirty62)):
            FE.add(pre + nm, t, B + off, mv)
        for k in range(5):
            S = u(u(B) + 4 * k); st = b.st[k]; sp = pre + "stage%d." % k
            FE.add(sp + "kind", "i", S + 0xc, st.kind)
            if k in (3, 4): f_biquad(FE, e, u(S), st.f, sp + ("lpf." if k == 3 else "hpf."))
            else: f_iir2(FE, e, u(S + 4), st.f, sp + ("lowshelf." if k < 2 else "peak."))
    return FE


FIELDS = {"lofi": fields_lofi, "mmf": fields_mmf, "peq": fields_peq}


def dump_pair(kind, e, o, m):
    FE = FIELDS[kind](e, o, m)
    ev = {k: _eread(e, a, t) for k, (a, t) in FE.E.items()}
    mv = {k: _mbits(t, v) for k, (t, v) in FE.M.items()}
    return ev, mv, FE


def ddiff(a, b): return [k for k in a if a[k] != b.get(k)]


def fmt_bits(name, v, FE):
    t = FE.E[name][1] if name in FE.E else "i"
    if t == "f": return "%.9g" % u2f(v)
    if t == "d": return "%.17g" % struct.unpack("<d", struct.pack("<Q", v))[0]
    return str(v if v < 0x80000000 else v - (1 << 32))


# ===================================================================================================================== write log
class WriteLog:
    """Logs every guest heap write while armed (UC_HOOK_MEM_WRITE over the bump heap)."""
    def __init__(self, e):
        self.e = e; self.on = False; self.w = []
        e.uc.hook_add(UC_HOOK_MEM_WRITE, self._h, begin=HEAP_BASE, end=HEAP_BASE + HEAP_SIZE - 1)
    def _h(self, uc, access, addr, size, value, _):
        if self.on: self.w.append((uc.reg_read(__import__("unicorn").arm_const.UC_ARM_REG_PC), addr, size, value))


def map_writes(wl_entries, FE, before_e, after_e):
    """Map each written byte range to field names; returns (written fields, changed fields, unmapped writes)."""
    amap = {}
    for nm, (a, t) in FE.E.items():
        n = {"b": 1, "d": 8}.get(t, 4)
        for k in range(n): amap[a + k] = nm
    written = set(); unm = []
    for pc, a, sz, v in wl_entries:
        hit = False
        for k in range(sz):
            nm = amap.get(a + k)
            if nm: written.add(nm); hit = True
        if not hit: unm.append((hex(pc), hex(a), sz))
    changed = {nm for nm in written if before_e[nm] != after_e[nm]}
    return written, changed, unm


def group(names):
    """Compress field names: 'filt.sub1.lpf.tap3.vL' -> 'filt.sub1.lpf.taps'."""
    out = {}
    for nm in sorted(names):
        g = nm
        for key in (".tap", ".yprev"):
            if key in nm: g = nm.split(key)[0] + ".taps"; break
        out[g] = out.get(g, 0) + 1
    return ["%s(%d)" % (k, v) if v > 1 else k for k, v in sorted(out.items())]


# ===================================================================================================================== C2 rigs
def new_rig(kind):
    if kind == "lofi":
        x = X21.EmuLoFi(); m = ML.LoFi(); m.insert_defaults()
    elif kind == "mmf":
        x = X23.EmuMMF(); m = MM.MMF(); m.insert_defaults()
    else:
        x = X26.EmuPEQ(); m = MP.PEQ(); m.insert_defaults()
    return x, m


def sig_block(kind, b, g):
    if kind == "noise": return [F(g.uniform(-0.6, 0.6)) for _ in range(N)], [F(g.uniform(-0.6, 0.6)) for _ in range(N)]
    if kind == "sine":
        return ([F(0.7 * math.sin(2 * math.pi * 330.0 * (b * N + i) / 44100.0)) for i in range(N)],
                [F(0.5 * math.sin(2 * math.pi * 1210.0 * (b * N + i) / 44100.0 + 0.4)) for i in range(N)])
    L = [F(0.0)] * N; R = [F(0.0)] * N
    if b % 3 == 0: L[5] = F(0.9); R[40] = F(-0.8)
    return L, R


# Each C2 case: name, steps. Steps: ("p", idx, v) set via slot 14 on both; ("blk", n) n blocks; ("reset",) the compared slot 27.
C2_CASES = {
    "lofi": [
        ("L1 HPF post, bits 0.6 red 0.4 pre 0.35; cutoff glide in progress at reset", "noise",
         [("p", 6, 0.0), ("p", 2, 0.6), ("p", 1, 0.4), ("p", 0, 0.35), ("p", 5, 0.8), ("blk", 6), ("p", 3, 0.62), ("p", 4, 0.3),
          ("blk", 1), ("reset",), ("blk", 6)]),
        ("L2 LPF pre (pos 0), res 0.5, red 0.15 (S&H holds), preamp ramp in progress", "sine",
         [("p", 6, 1.0), ("p", 7, 0.0), ("p", 4, 0.5), ("p", 1, 0.15), ("p", 3, 0.45), ("blk", 6), ("p", 0, 0.7), ("blk", 0),
          ("reset",), ("blk", 6)]),
        ("L3 BPF, bits 0.3, cutoff 0.7; then type -> LPF pending (set, not yet consumed) at reset", "noise",
         [("p", 6, 2.0), ("p", 2, 0.3), ("p", 3, 0.7), ("blk", 6), ("p", 6, 1.0), ("p", 3, 0.66), ("reset",), ("blk", 8)]),
        ("L4 HPF -> LPF switch done (old HPF keeps taps), red 0.5, reset on LPF", "noise",
         [("p", 6, 0.0), ("p", 1, 0.5), ("blk", 5), ("p", 6, 1.0), ("blk", 6), ("reset",), ("blk", 6)]),
        ("L6 LPF, impulses, red 0.05 (sparse S&H)", "impulse",
         [("p", 6, 1.0), ("p", 1, 0.05), ("blk", 6), ("reset",), ("blk", 6)]),
        ("L5 Off (type 3), red 0.1 bits 0.4", "noise",
         [("p", 6, 3.0), ("p", 1, 0.1), ("p", 2, 0.4), ("blk", 6), ("reset",), ("blk", 4)]),
    ],
    "mmf": [
        ("M1 LPF 12 dB, cutoff 0.3 Q 0.4 GLIDE 0.6, gain 0.8; cutoff glide in progress at reset", "noise",
         [("p", 0, 0.3), ("p", 2, 0.4), ("p", 3, 0.6), ("p", 1, 0.8), ("p", 5, 0.7), ("blk", 6), ("p", 0, 0.7), ("blk", 1), ("reset",), ("blk", 8)]),
        ("M2 HPF 24 dB (db 0), cutoff 0.6 Q 0.6; GAIN ramp in progress at reset", "sine",
         [("p", 6, 1.0), ("p", 7, 0.0), ("p", 0, 0.6), ("p", 2, 0.6), ("blk", 6), ("p", 1, 0.3), ("blk", 0), ("reset",), ("blk", 6)]),
        ("M3 BPF 24 dB (db 2), GLIDE 1, Q 0.8; cutoff change pending (not consumed) at reset", "noise",
         [("p", 6, 2.0), ("p", 7, 2.0), ("p", 3, 1.0), ("p", 2, 0.8), ("blk", 6), ("p", 0, 0.45), ("reset",), ("blk", 8)]),
        ("M4 BPF 12 dB -> LPF 24 dB switch done (old BPF keeps taps), reset on LPF 24", "impulse",
         [("p", 6, 2.0), ("blk", 5), ("p", 6, 0.0), ("p", 7, 0.0), ("blk", 6), ("reset",), ("blk", 6)]),
        ("M5 kind switch LPF 12 -> HPF 12 in progress (gate fading) at reset", "noise",
         [("p", 0, 0.5), ("blk", 5), ("p", 6, 1.0), ("blk", 1), ("reset",), ("blk", 6)]),
        ("M6 off (FILTERTYPE 3)", "noise",
         [("p", 6, 3.0), ("blk", 5), ("reset",), ("blk", 3)]),
    ],
    "peq": [
        ("P1 shelves (types 0/1), gains 0.8 / 0.3; band-1 gain glide in progress at reset", "noise",
         [("p", 1, 0.8), ("p", 4, 0.3), ("blk", 6), ("p", 1, 0.5), ("blk", 1), ("reset",), ("blk", 8)]),
        ("P2 peak (2) / LPF (3), Q 0.3; band-2 freq glide in progress at reset", "sine",
         [("p", 6, 2.0), ("p", 7, 3.0), ("p", 2, 0.3), ("p", 1, 0.9), ("blk", 6), ("p", 3, 0.6), ("blk", 1), ("reset",), ("blk", 8)]),
        ("P3 HPF (4) / peak (2); band-1 freq change pending (not consumed) at reset", "noise",
         [("p", 6, 4.0), ("p", 7, 2.0), ("p", 4, 0.9), ("blk", 6), ("p", 0, 0.4), ("p", 5, 0.5), ("reset",), ("blk", 8)]),
        ("P4 band-1 type switch 0 -> 3 done (old shelf keeps taps), band 2 HPF", "impulse",
         [("p", 7, 4.0), ("blk", 5), ("p", 6, 3.0), ("blk", 6), ("reset",), ("blk", 6)]),
        ("P5 band-2 type switch 1 -> 2 in progress (gate fading) at reset", "noise",
         [("p", 4, 0.9), ("blk", 5), ("p", 7, 2.0), ("blk", 1), ("reset",), ("blk", 6)]),
    ],
}


# ----- alternative reset semantics (model mutants), each a function(model) replacing reset()
def _taps_all_lofi(m):
    m.apply_params()
    for s in m.filt.subs: s.clear_taps()
    m.sh_hold = [F(0), F(0)]; m.sh_phase = m.sh_step


def _taps_all_mmf(m):
    m.apply_params()
    for w in m.filt.w:
        for s in w.stages: s.clear_taps()


def _taps_all_peq(m):
    m.apply_params()
    for b in m.bands:
        for st in b.st: st.f.clear_taps()


def _noapply(kind):
    def f(m):
        cls = {"lofi": ML.LoFi, "mmf": MM.MMF, "peq": MP.PEQ}[kind]
        ap = m.apply_params; m.apply_params = lambda: None
        try: cls.reset(m)
        finally: m.apply_params = ap
    return f


def _snap_glide(kind):
    def f(m):
        {"lofi": ML.LoFi, "mmf": MM.MMF, "peq": MP.PEQ}[kind].reset(m)
        if kind == "peq":
            for b in m.bands:
                b.fc = b.ft; b.qc = b.qt; b.gc = b.gt; b.fsteps = b.qsteps = b.gsteps = b.maxsteps = 0
        else:
            c = m.filt; c.cut_c = c.cut_t; c.q_c = c.q_t; c.cut_steps = c.q_steps = c.maxsteps = 0
    return f


def _pending_stage_peq(m):
    m.apply_params()
    for b in m.bands: b.st[b.pending].f.clear_taps()


def _lofi_phase(val):
    def f(m):
        ML.LoFi.reset(m); m.sh_phase = F(val)
    return f


def _lofi_keep_holds(m):
    h = list(m.sh_hold); ML.LoFi.reset(m); m.sh_hold = h


def _lofi_snap_preamp(m):
    ML.LoFi.reset(m); m.pre_c = m.pre_t; m.pre_cnt = 0


def _gain_snap(m):
    MM.MMF.reset(m); g = m.gain; g.cur = g.target; g.rem = 0; g.state = 0; g.inc = F(0)


MUTANTS = {
    "lofi": [("no reset", lambda m: None), ("no parameter apply", _noapply("lofi")), ("clear taps of all 4 sub-filters", _taps_all_lofi),
             ("S&H phase := 0", _lofi_phase(0.0)), ("S&H phase := 1.0 (ctor value)", _lofi_phase(1.0)), ("S&H holds kept", _lofi_keep_holds),
             ("glide snapped to target", _snap_glide("lofi")), ("preamp ramp snapped", _lofi_snap_preamp)],
    "mmf": [("no reset", lambda m: None), ("no parameter apply", _noapply("mmf")), ("clear taps of all 7 kinds", _taps_all_mmf),
            ("glide snapped to target", _snap_glide("mmf")), ("GainRamp snapped to target", _gain_snap)],
    "peq": [("no reset", lambda m: None), ("no parameter apply", _noapply("peq")), ("clear taps of all 5 stages", _taps_all_peq),
            ("clear pending (not current) stage", _pending_stage_peq), ("glide snapped to target", _snap_glide("peq"))],
}


def run_c2_case(kind, name, sig, steps, mutant=None, log=True):
    """Returns dict with before/after equality, write sets, downstream exactness. mutant: function(model) used instead of reset().
    Every case starts with one block at the Insert defaults (F026: a value equal to the ctor 'last' value is otherwise never applied)."""
    steps = [("blk", 1)] + list(steps)
    x, m = new_rig(kind)
    e, o = x.e, x.o
    wl = WriteLog(e) if log else None
    g = random.Random(sum(map(ord, name)))
    b = 0; res = dict(name=name, pre_exact=True, pre_state_diff=[], before_diff=[], after_diff=[], post_exact=True, post_state_diff=[],
                      post_blocks=0, ret=None, written=[], changed=[], unmapped=[], reset_done=False, maxdiff=0.0)
    for st in steps:
        if st[0] == "p":
            x.set_param(st[1], st[2]); m.set_param(st[1], st[2])
        elif st[0] == "blk":
            for _ in range(st[1]):
                L, R = sig_block(sig, b, g); b += 1
                eo = x.process(L, R); mo = m.process(L, R)
                ok = [f2u(a) for a in eo[0] + eo[1]] == [f2u(a) for a in mo[0] + mo[1]]
                if not ok:
                    res["maxdiff"] = max(res["maxdiff"], max(abs(a - c) for a, c in zip(eo[0] + eo[1], mo[0] + mo[1])))
                if res["reset_done"]:
                    res["post_blocks"] += 1; res["post_exact"] &= ok
                else:
                    res["pre_exact"] &= ok
                ev, mv, FE = dump_pair(kind, e, o, m)
                dd = ddiff(ev, mv)
                if dd: (res["post_state_diff"] if res["reset_done"] else res["pre_state_diff"]).append((b - 1, dd[:4]))
        elif st[0] == "reset":
            ev0, mv0, FE = dump_pair(kind, e, o, m)
            res["before_diff"] = ddiff(ev0, mv0)
            if wl: wl.w = []; wl.on = True
            r0, _ = e.vcall(o, 27)
            if wl: wl.on = False
            res["ret"] = r0
            rm = m.reset() if mutant is None else (mutant(m) or 0)
            ev1, mv1, FE = dump_pair(kind, e, o, m)
            res["after_diff"] = ddiff(ev1, mv1)
            res["model_ret"] = rm
            if wl:
                wr, ch, unm = map_writes(wl.w, FE, ev0, ev1)
                res["written"] = sorted(wr); res["changed"] = sorted(ch); res["unmapped"] = unm
                res["n_writes"] = len(wl.w)
            res["changed_emu_all"] = sorted(k for k in ev0 if ev0[k] != ev1[k])
            res["reset_done"] = True
            res["_ev"] = (ev0, ev1, FE)
    res["ok"] = (res["pre_exact"] and not res["pre_state_diff"] and not res["before_diff"] and not res["after_diff"] and
                 res["post_exact"] and not res["post_state_diff"] and res["ret"] == 0)
    return res


# ===================================================================================================================== C4 composition
def run_comp(kind, params, sig, events, nblk=220, seed=5):
    """As H044.run_generic, plus ('p', idx, v) events (applied to both sides at any time, incl. while stopped) and
    effect-state comparison (C2 field dumps) after every block."""
    e, o, m, mm, feed = H44.build_generic(kind)
    for idx, v in params: e.vcall(o, 14, idx, f2u(v)); mm.set_param(idx, v)
    g = random.Random(seed)
    res = dict(samples=0, exact=0, maxdiff=0.0, state_diffs=0, fx_state_diffs=0, s9_diffs=0, first=None, first_block=None, s27_calls=0)
    want = True; blob = b""
    bl = e.malloc(256); br = e.malloc(256)
    for b in range(nblk):
        for op in events.get(b, []):
            if op[0] == "stop": e.vcall(o, 6, f2u(op[1])); m.slot6(op[1]); want = False
            elif op[0] == "act": want = True
            elif op[0] == "p": e.vcall(o, 14, op[1], f2u(op[2])); mm.set_param(op[1], op[2])
        s9e = e.vcall(o, 9)[0]; s9m = m.slot9()
        if s9e != s9m: res["s9_diffs"] += 1
        if want and s9e == 0:
            e.vcall(o, 5, 0, 1); m.slot5(0.0, 1); e.vcall(o, 7, 0); m.slot7(); res["s27_calls"] += 1
        xL, xR = sig_block(sig, b, g)
        e.set_floats(bl, xL); e.set_floats(br, xR); e.vcall(o, 18, bl, br, N)
        oL = e.floats(bl, N); oR = e.floats(br, N)
        mL = list(xL); mR = list(xR); m.slot18(mL, mR, N)
        blob += pack(oL) + pack(oR)
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["exact"] += 1
            else:
                d = abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf")
                res["maxdiff"] = max(res["maxdiff"], d)
                if res["first_block"] is None: res["first_block"] = b
        dd = H44.sdiff(H44.emu_state(e, o), H44.model_state(m))
        if dd:
            res["state_diffs"] += 1
            if res["first"] is None: res["first"] = ("wrapper state after block %d" % b, dd[:3])
        ev, mv, _ = dump_pair(kind, e, o, mm)
        fd = ddiff(ev, mv)
        if fd:
            res["fx_state_diffs"] += 1
            if res["first"] is None: res["first"] = ("effect state after block %d" % b, fd[:3])
    res["sha"] = sha(blob)[:16]
    res["ok"] = (res["exact"] == res["samples"] and not res["state_diffs"] and not res["fx_state_diffs"] and not res["s9_diffs"])
    return res, blob


COMP_SETTINGS = {
    "lofi": [("HPF post, bits 0.6 red 0.4 pre 0.35 mix 0.8", ((6, 0.0), (2, 0.6), (1, 0.4), (0, 0.35), (5, 0.8)),
              [(40, 3, 0.62), (68, 0, 0.7), (85, 1, 0.2), (130, 6, 2.0), (175, 3, 0.3)]),
             ("LPF pre (pos 0), res 0.5 red 0.15", ((6, 1.0), (7, 0.0), (4, 0.5), (1, 0.15), (3, 0.45)),
              [(40, 4, 0.2), (68, 3, 0.52), (85, 6, 0.0), (130, 2, 0.5), (175, 5, 0.5)]),
             ("BPF, bits 0.3 cutoff 0.7 mix 0.6", ((6, 2.0), (2, 0.3), (3, 0.7), (5, 0.6)),
              [(40, 7, 0.0), (68, 3, 0.75), (85, 3, 0.4), (130, 6, 3.0), (175, 6, 1.0)])],
    "mmf": [("LPF 12 dB cutoff 0.3 Q 0.4 GLIDE 0.6 gain 0.8 mix 0.7", ((0, 0.3), (2, 0.4), (3, 0.6), (1, 0.8), (5, 0.7)),
             [(40, 0, 0.6), (68, 0, 0.9), (85, 2, 0.7), (130, 6, 1.0), (175, 1, 0.5)]),
            ("HPF 24 dB (db 0) cutoff 0.6 Q 0.6", ((6, 1.0), (7, 0.0), (0, 0.6), (2, 0.6)),
             [(40, 1, 0.3), (68, 0, 0.4), (85, 7, 1.0), (130, 0, 0.7), (175, 6, 2.0)]),
            ("BPF 24 dB (db 2) GLIDE 1 Q 0.8 mix 0.7", ((6, 2.0), (7, 2.0), (3, 1.0), (2, 0.8), (5, 0.7)),
             [(40, 0, 0.45), (68, 0, 0.8), (85, 3, 0.0), (130, 7, 1.0), (175, 6, 0.0)])],
    "peq": [("shelves 0/1 gains 0.8/0.3", ((1, 0.8), (4, 0.3)),
             [(40, 0, 0.3), (68, 1, 0.5), (85, 3, 0.7), (130, 6, 2.0), (175, 4, 0.9)]),
            ("peak (2) / LPF (3) Q 0.3 gain 0.9", ((6, 2.0), (7, 3.0), (2, 0.3), (1, 0.9)),
             [(40, 3, 0.6), (68, 0, 0.7), (85, 7, 1.0), (130, 2, 0.8), (175, 6, 4.0)]),
            ("HPF (4) / peak (2) gain2 0.9", ((6, 4.0), (7, 2.0), (4, 0.9)),
             [(40, 5, 0.5), (68, 3, 0.3), (85, 0, 0.4), (130, 7, 0.0), (175, 1, 0.2)])],
}
# stop at 70 (mid-glide: changes at 68), parameter change at 85 while stopped (applied first by slot 27), re-activation at 100,
# second stop at 150 and re-activation requested at 152 (taken when slot 9 = 0)
def comp_events(changes, params=()):
    ev = {70: [("stop", 1.0)], 100: [("act",)], 150: [("stop", 1.0)], 152: [("act",)]}
    if params: ev[2] = [("p", i, v) for i, v in params]       # after the activation block (F026 trap avoided)
    for b, i, v in changes: ev.setdefault(b, []).insert(0, ("p", i, v))
    return ev


# ===================================================================================================================== C3 regression
REGRESS = {   # recorded hashes (kb/findings.md F026-F044 evidence lines and cycle 026; re-measured before any model change)
    "H021_lofi_model": {"h021_report.txt": "9273c8539ec99503", "h021.json": "f331677019ff01ab", "*.f32": "86f8975ad079c80a"},
    "H023_mmf_model": {"h023_report.txt": "9c33b389017baf0e", "h023.json": "e4e396bc3b259a32", "*.f32": "5ccbbf43034ea127"},
    "H026_peq_model": {"h026_report.txt": "ed20422ff6c89624", "h026.json": "fa2ebab646ecf486", "*.f32": "a3cb69854f6b5ea8"},
    "H044_effectbase_wrapper": {"c3_stub_outputs.f32": "b7f91882648d031f", "c4_real_outputs.f32": "47c85123b102cfeb",
                                "c4_ext_outputs.f32": "6909f55ba50f89ac", "c5_processor_outputs.f32": "526c2b9ffb40ed33"},
}


def regress(out):
    rows = []; procs = {}
    for h in REGRESS:
        d = os.path.join(out, "regress", h); os.makedirs(d, exist_ok=True)
        procs[h] = subprocess.Popen([sys.executable, "-B", os.path.join(HERE, h + ".py"), "--out", d],
                                    stdout=open(d + ".log", "w"), stderr=subprocess.STDOUT)
    for h, p in procs.items():
        rc = p.wait(); d = os.path.join(out, "regress", h)
        log = open(d + ".log").read()
        got = {}
        for fn in REGRESS[h]:
            if fn == "*.f32":
                fs = sorted(x for x in os.listdir(d) if x.endswith(".f32"))
                got[fn] = sha(b"".join(open(os.path.join(d, x), "rb").read() for x in fs))[:16]
            else:
                pth = os.path.join(d, fn)
                got[fn] = sha(open(pth, "rb").read())[:16] if os.path.exists(pth) else None
        ok = rc == 0 and "RESULT: 0 failed checks" in log and all(got[k] == v for k, v in REGRESS[h].items())
        rows.append((h, rc, ok, got, [ln for ln in log.splitlines() if ln.startswith("RESULT")][-1:]))
    return rows


# ===================================================================================================================== main
def c5_lofi_gap(P, J):
    """C5 (c): exact-zero run after each activation of the real LoFi through slot 18 (S&H restart by slot 27)."""
    # (c) LoFi: slot 27 sets the S&H phase := step with holds 0, so the wet path outputs 0 for floor(step) samples after every
    # activation; with MIXRATIO 1 the dry part has faded out after 147 samples -> exact digital silence until the first capture.
    P("  LoFi S&H restart after activation (real slot 18, filter Off, MIXRATIO 1, 1 kHz sine 0.5 (phase 0.5 rad, no zero samples); "
      "activation 0, stop 40, re-activation 60):")
    J["c5_lofi_gap"] = []
    for red in (1.0, 0.5, 0.2, 0.05, 0.0):
        for neutral in (False, True):
            e, o, m, mm, feed = H44.build_generic("lofi", neutral27=neutral)
            e.vcall(o, 14, 1, f2u(red)); mm.set_param(1, red)
            bl = e.malloc(256); br = e.malloc(256); want = True; out = []; acts = []
            for b in range(120):
                if b == 40: e.vcall(o, 6, f2u(1.0)); want = False
                if b == 60: want = True
                if want and e.vcall(o, 9)[0] == 0: e.vcall(o, 5, 0, 1); e.vcall(o, 7, 0); acts.append(b * N)
                xL = [F(0.5 * math.sin(2 * math.pi * 1000.0 * (b * N + i) / 44100.0 + 0.5)) for i in range(N)]   # never exactly 0
                e.set_floats(bl, xL); e.set_floats(br, xL); e.vcall(o, 18, bl, br, N); out += e.floats(bl, N)
            def zrun(s0):
                i = s0
                while i < len(out) and out[i] != 0.0: i += 1
                j = i
                while j < len(out) and out[j] == 0.0: j += 1
                return (i - s0, j - i)
            tm = ML.LoFi(); tm.set_param(1, red); tm.apply_params(); step = tm.sh_step
            gaps = [zrun(s) for s in acts]
            P("    REDUCTION %-4g step %-9.6g %-26s activations at samples %s -> (first zero sample after activation, length of "
              "the exact-zero run) %s" % (red, step, "(real slot 27)" if not neutral else "(slot 27 = base, no reset)", acts, gaps))
            J["c5_lofi_gap"].append(dict(red=red, step=step, neutral=neutral, acts=acts, gaps=gaps))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H076"))
    ap.add_argument("--skip-regress", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []; t0 = time.time()
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)

    # -------------------------------------------------------------------------------------------- C1 + C2
    P("== C1/C2 real slot 27 vs model reset(): full state dumps before/after, heap write log of the real slot 27, next blocks")
    J["c2"] = {}
    union = {}
    for kind in ("lofi", "mmf", "peq"):
        x0, _ = new_rig(kind); vs = x0.e.u32(x0.e.u32(x0.o) + 4 * 27)
        P("\n-- %s: vtable slot 27 of the emulated object = 0x%x (expected 0x%x)" % (kind, vs, SLOT27[kind]))
        check(vs == SLOT27[kind], "%s vtable slot 27 is 0x%x" % (kind, SLOT27[kind]))
        rows = []
        for name, sig, steps in C2_CASES[kind]:
            r = run_c2_case(kind, name, sig, steps)
            ev0, ev1, FE = r.pop("_ev")
            rows.append(r)
            union.setdefault(kind, set()).update(r["changed"])
            P("  %-88s %s ret %s  fields %d  before/after diffs %d/%d  pre/post exact %s/%s (%d post blocks)" % (
                name, "OK " if r["ok"] else "BAD", r["ret"], len(FE.E), len(r["before_diff"]), len(r["after_diff"]), r["pre_exact"],
                r["post_exact"], r["post_blocks"]))
            if r["before_diff"] or r["after_diff"] or r["pre_state_diff"] or r["post_state_diff"]:
                P("     diffs: before %s after %s pre %s post %s" % (r["before_diff"][:4], r["after_diff"][:4], r["pre_state_diff"][:2],
                                                                     r["post_state_diff"][:2]))
            P("     heap writes %d; fields written: %s" % (r.get("n_writes", 0), ", ".join(group(r["written"]))))
            P("     fields changed by slot 27: %s" % ", ".join(group(r["changed"])))
            ch_nontap = [k for k in r["changed"] if ".tap" not in k and ".yprev" not in k]
            for k in ch_nontap:
                P("       %-28s %s -> %s" % (k, fmt_bits(k, ev0[k], FE), fmt_bits(k, ev1[k], FE)))
            if r["unmapped"]: P("     unmapped writes: %s" % r["unmapped"][:8])
            if set(r["changed_emu_all"]) != set(r["changed"]):
                P("     NOTE fields changed but not seen in the write log: %s" % sorted(set(r["changed_emu_all"]) - set(r["changed"])))
        nok = sum(1 for r in rows if r["ok"])
        check(nok == len(rows), "%s: %d/%d slot-27 cases with model state == emulated state before and after slot 27 (all fields, "
                                "bit-exact), slot 27 returns 0, and the next blocks bit-exact (output + state)" % (kind, nok, len(rows)))
        check(all(not r["unmapped"] for r in rows), "%s: every heap write of the real slot 27 lands in a named field" % kind)
        J["c2"][kind] = [{k: v for k, v in r.items()} for r in rows]

        # alternative reset semantics
        P("  alternatives (model mutants instead of reset(); refuted = some case differs in state after slot 27 or in later output):")
        mrows = []
        for mname, mf in MUTANTS[kind]:
            hits = []
            for name, sig, steps in C2_CASES[kind]:
                r = run_c2_case(kind, name, sig, steps, mutant=mf, log=False)
                r.pop("_ev", None)
                if not r["ok"]: hits.append((name.split()[0], len(r["after_diff"]), r["post_exact"]))
            mrows.append((mname, hits))
            P("    %-40s %s %s" % (mname, "refuted by" if hits else "NOT refuted", hits))
        J["c2"][kind + "_mutants"] = mrows
        nref = [m for m, h in mrows if not h]
        check(not nref, "%s: every alternative reset semantics is refuted by at least one case (not refuted: %s)" % (kind, nref))

    P("\n  union of fields changed by the real slot 27 over all cases:")
    for kind in ("lofi", "mmf", "peq"):
        P("    %s: %s" % (kind, ", ".join(group(union[kind]))))
    J["c2_union"] = {k: sorted(v) for k, v in union.items()}

    # H025 claims, explicitly
    lofi_rows = J["c2"]["lofi"]
    l2 = next(r for r in lofi_rows if r["name"].startswith("L2"))
    cur_taps = any(".tap" in k and "sub1" in k for k in l2["changed"])
    other_taps = any(".tap" in k and "sub1" not in k for r in lofi_rows for k in r["changed"]
                     if (r["name"].startswith("L2") or r["name"].startswith("L4")))
    holds = all(("sh.holdL" in r["written"] and "sh.holdR" in r["written"]) for r in lofi_rows)
    phase = all("sh.phase" in r["written"] for r in lofi_rows)
    P("  H025: current sub-filter taps cleared %s; other sub-filters untouched %s; holds zeroed in every case %s; phase written "
      "in every case %s" % (cur_taps, not other_taps, holds, phase))
    check(cur_taps and not other_taps and holds and phase, "H025 claims (taps cleared: current sub-filter only; holds := 0; "
          "phase := step) agree with the emulated slot 27 and the model")

    # -------------------------------------------------------------------------------------------- C3
    if not a.skip_regress:
        P("\n== C3 regression: H021 / H023 / H026 / H044 re-run (subprocesses), recorded hashes")
        rr = regress(a.out)
        for h, rc, ok, got, res in rr:
            P("  %-26s rc %d %s %s %s" % (h, rc, "OK " if ok else "BAD", res, " ".join("%s %s" % (k, v) for k, v in got.items())))
        check(all(r[2] for r in rr), "H021/H023/H026/H044 outputs unchanged (report/json/f32 hashes as recorded; H044 f32 hashes as "
                                     "recorded)")
        J["c3"] = [(h, rc, ok, got) for h, rc, ok, got, _ in rr]

    # -------------------------------------------------------------------------------------------- C4
    P("\n== C4 composition: real effect via real slot 18 (Insert ctor state) vs effectbase + model with reset(); 220 blocks; "
      "stop 70 (glide running), change while stopped at 85, re-activation 100, stop 150, re-activation 152")
    crow = []; cblob = b""
    for kind in ("peq", "mmf", "lofi"):
        for sname, prm, chg in COMP_SETTINGS[kind]:
            for sig in ("noise", "sine", "impulse"):
                r, blob = run_comp(kind, (), sig, comp_events(chg, prm))
                r.update(kind=kind, setting=sname, sig=sig); crow.append(r); cblob += blob
                P("  %-5s %-52s %-7s %s exact %6d/%6d maxdiff %.3g wrapper/fx state diffs %d/%d s9 %d slot5->27 calls %d sha %s%s" % (
                    kind, sname, sig, "OK " if r["ok"] else "BAD", r["exact"], r["samples"], r["maxdiff"], r["state_diffs"],
                    r["fx_state_diffs"], r["s9_diffs"], r["s27_calls"], r["sha"], "" if r["ok"] else "  first %s" % (r["first"],)))
    nok = sum(1 for r in crow if r["ok"])
    check(nok == len(crow), "composition: %d/%d cases bit-exact (output, wrapper state, effect state after every block)" % (nok, len(crow)))
    J["c4"] = crow; J["c4_sha_all"] = sha(cblob)
    P("  all C4 outputs sha256 %s (%d cases, %d samples)" % (sha(cblob), len(crow), sum(r["samples"] for r in crow)))
    open(os.path.join(a.out, "c4_comp_outputs.f32"), "wb").write(cblob)

    P("\n== C4 full 13-effect H044 c4_ext table (activation 0, slot 6 at 120, re-activation at 150, 200 blocks noise)")
    trows = []; tblob = b""
    for kind in H44.EXT_KINDS:
        r, blob = H44.run_generic(kind, events={120: [("stop", 1.0)], 150: [("act",)]})
        tblob += blob; trows.append(r)
        P("  %-16s %s samples %6d exact %6d maxdiff %.3g state/s9 diffs %d/%d sha %s" % (
            kind, "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["state_diffs"], r["s9_diffs"], r["sha"]))
    P("  c4_ext emulated outputs sha256 %s (H044 recorded 6909f55b…)" % sha(tblob)[:16])
    check(all(r["ok"] for r in trows) and sha(tblob)[:16] == "6909f55ba50f89ac",
          "c4_ext: %d/13 effects bit-exact end to end, emulated-output hash unchanged" % sum(1 for r in trows if r["ok"]))
    J["c4_ext"] = trows

    # -------------------------------------------------------------------------------------------- C5
    P("\n== C5 side results")
    # (a) size of the reset's effect at re-activation: real composition vs the same with the real slot 27 replaced by the base one
    for kind in ("peq", "mmf", "lofi"):
        sname, prm, chg = COMP_SETTINGS[kind][0]
        outs = []
        for neutral in (False, True):
            e, o, m, mm, feed = H44.build_generic(kind, neutral27=neutral)
            g = random.Random(5); bl = e.malloc(256); br = e.malloc(256); want = True; ev = comp_events(chg, prm); seq = []
            for b in range(220):
                for op in ev.get(b, []):
                    if op[0] == "stop": e.vcall(o, 6, f2u(op[1])); want = False
                    elif op[0] == "act": want = True
                    elif op[0] == "p": e.vcall(o, 14, op[1], f2u(op[2]))
                if want and e.vcall(o, 9)[0] == 0: e.vcall(o, 5, 0, 1); e.vcall(o, 7, 0)
                xL, xR = sig_block("noise", b, g); e.set_floats(bl, xL); e.set_floats(br, xR); e.vcall(o, 18, bl, br, N)
                seq.append(e.floats(bl, N) + e.floats(br, N))
            outs.append(seq)
        d = [max(abs(p - q) for p, q in zip(outs[0][b], outs[1][b])) for b in range(220)]
        first0 = next((b for b in range(220) if d[b] > 0), None)
        first = next((b for b in range(100, 220) if d[b] > 0), None)          # from the first re-activation on
        P("  %s: first activation (block 0..69): max |real - no-reset| %.3g (slot 27 also runs at the first activation)" % (
            kind, max(d[0:70])))
        P("  %s: real slot 27 vs base slot 27 (no reset), noise, '%s': first differing block %s, max |diff| %.3g; max in the first 3 "
          "blocks after the re-activation %.3g, after 10 blocks %.3g" % (kind, sname, first, max(d),
                                                                      max(d[first:first + 3]) if first is not None else 0.0,
                                                                      max(d[first + 10:]) if first is not None else 0.0))
        J.setdefault("c5_reset_effect", {})[kind] = dict(first=first, maxdiff=max(d))
    # (b) H030: PEQ cold start through slot 18 (first activation) vs re-activation, 1 kHz-ish sine, defaults (0 dB)
    e, o, m, mm, feed = H44.build_generic("peq")
    bl = e.malloc(256); br = e.malloc(256); want = True; gains = []
    for b in range(200):
        if b == 100: e.vcall(o, 6, f2u(1.0)); want = False
        if b == 120: want = True
        if want and e.vcall(o, 9)[0] == 0: e.vcall(o, 5, 0, 1); e.vcall(o, 7, 0)
        xL = [F(0.5 * math.sin(2 * math.pi * 1000.0 * (b * N + i) / 44100.0)) for i in range(N)]
        e.set_floats(bl, xL); e.set_floats(br, xL); e.vcall(o, 18, bl, br, N); yL = e.floats(bl, N)
        gains.append(math.sqrt(sum(y * y for y in yL) / N) / math.sqrt(sum(x * x for x in xL) / N))
    P("  H030 PEQ defaults (0 dB shelves) through real slot 18, 1 kHz sine: per-block rms gain at first activation %s; at "
      "re-activation (blocks 120..125) %s; steady %s" % (["%.4f" % x for x in gains[0:5]], ["%.4f" % x for x in gains[120:126]],
                                                       "%.4f" % gains[90]))
    J["c5_h030"] = dict(first=gains[0:5], react=gains[120:126], steady=gains[90])
    e, o, m, mm, feed = H44.build_generic("peq")
    bl = e.malloc(256); br = e.malloc(256); want = True; ratio = []
    for b in range(200):
        if b == 100: e.vcall(o, 6, f2u(1.0)); want = False
        if b == 120: want = True
        if want and e.vcall(o, 9)[0] == 0: e.vcall(o, 5, 0, 1); e.vcall(o, 7, 0)
        e.set_floats(bl, [F(0.5)] * N); e.set_floats(br, [F(0.5)] * N); e.vcall(o, 18, bl, br, N)
        ratio += [y / 0.5 for y in e.floats(bl, N)]
    r0 = min(range(0, 400), key=lambda i: ratio[i]); r1 = min(range(120 * N, 120 * N + 400), key=lambda i: ratio[i])
    P("  H030 PEQ defaults, DC 0.5 through real slot 18: min out/in after the first activation %.4f (%.2f dB) at sample %d; "
      "after the re-activation (block 120) %.4f at +%d; predicted (1 - t/147) + (t/132)^2 * t/147 at t = 132/sqrt(3) = %.4f" % (
          ratio[r0], 20 * math.log10(ratio[r0]), r0, ratio[r1], r1 - 120 * N,
          (1 - (132 / math.sqrt(3)) / 147) + (1 / 3.0) * (132 / math.sqrt(3)) / 147))
    J["c5_h030_dc"] = dict(min_first=ratio[r0], at=r0, min_react=ratio[r1])
    c5_lofi_gap(P, J)

    P("\nRESULT: %d failed checks" % len(fails))
    print("(elapsed %.0f s; not written to the report so its hash is reproducible)" % (time.time() - t0))
    open(os.path.join(a.out, "h076_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h076.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
