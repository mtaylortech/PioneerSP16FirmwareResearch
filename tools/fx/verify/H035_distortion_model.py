#!/usr/bin/env python3
"""H035 — Distortion (Insert index 6; vtable 0x842898, inline new 0x1d8; kernel c_distortion 0x8418a0, ctor 0xfa568, init
0xfa36c, process 0xfa78c) end to end: parameters -> formulas -> state layout -> bit-exact own-code model
harness/models/distortion.py vs the emulated 1.60 slot 25 0x115d48.

Sections (criteria of kb/cycles/013.md):
  C1  parameter list: slot-14 index map (emulated), Insert slot-52 defaults (case 6), inline-ctor stores, change detection.
  C2  formula sweeps: emulated read-back of kernel / EffectBase fields vs the model after every slot-14 call (drive, the
      three cutoffs incl. clamp boundaries + a random cutoff sweep, threshold, mixratio); libm oracle checks (pow, expf, powf).
  C3  layout: kernel + Distortion fields compared model vs emulation after every block; vtables; kernel slots 9/16/17 direct.
  C4  end-to-end matrix: 9 settings x {impulse, sine low, sine high, noise, silence} x 160 blocks, a 520-block auto-gain run,
      3 event runs; slot-25 output bit-exact + state after every block.
  C5  start-up (no mute / fade), slot 27 reset, slot 10, EffectBase slot 5 activation.
  C6  alternatives (model mutants must fail; slot-18 dry/wet law).
  C7  Master / Send context: construction blocks compared instruction by instruction; Master-built object run.
Outputs only to --out (default harness/out/H035/). Run: .venv/bin/python -B harness/H035_distortion_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f, d2u, u2d, SP                         # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import distortion as DM                                        # noqa: E402
import crmath as CR                                            # noqa: E402
import glibc_expf as GE                                        # noqa: E402
GE.load_tables()
from fdlibm_powf import powf as fd_powf                        # noqa: E402
from osc import F                                              # noqa: E402

FS = 44100; N = 64
BUILD = {"insert": (0x119060, 0x1190f0)}
KCTOR = 0x10000 * 0 + 0xfa568
S14 = 0x1164d8
KFIELDS = ([(0x04, "fs", "i"), (0x08, "block", "i"), (0x0c, "p_drive", "f"), (0x10, "p_out", "f"), (0x14, "p_hp", "f"),
            (0x18, "p_pre", "f"), (0x1c, "p_thr", "f"), (0x20, "p_x20", "f"), (0x24, "x24", "z"),
            (0xc0, "inv_fs", "f"), (0xc4, "a_out", "f"), (0xc8, "b_out", "f"), (0xcc, "z_outL", "f"), (0xd0, "z_outR", "f"),
            (0xd4, "fc_out", "f"), (0xd8, "a_hp", "f"), (0xdc, "b_hp", "f"), (0xe0, "z_hpL", "f"), (0xe4, "z_hpR", "f"),
            (0xe8, "fc_hp", "f"), (0xec, "a_pre", "f"), (0xf0, "b_pre", "f"), (0xf4, "z_preL", "f"), (0xf8, "z_preR", "f"),
            (0xfc, "fc_pre", "f"), (0x100, "n", "i"), (0x104, "drive", "f"), (0x108, "hi", "f"), (0x10c, "lo", "f"),
            (0x110, "g", "f"), (0x114, "inc", "f"), (0x118, "dec", "f"), (0x11c, "reload", "i"), (0x120, "hold", "i"),
            (0x124, "x124", "f"), (0x128, "x128", "f"), (0x12c, "x12c", "f"), (0x130, "e130", "b"), (0x134, "blend", "f")])


def sha(b): return hashlib.sha256(b).hexdigest()
def fl_bits(xs): return tuple(f2u(x) for x in xs)


class EmuDist:
    """Distortion built by running the inline block of the 1.60 InsertFxProcessor ctor (0x119060-0x1190f0); then
    (optionally) the H007 Insert init (slot 22, 0x106c7c(obj,1,10), slot 52 case 6)."""
    def __init__(self, defaults=True, where="insert", start=None, end=None):
        self.e = e = H31.new_emu(); self.s14 = []
        e.add_watch(S14, lambda em: self.s14.append((em.r(1), em.r(2))))
        proc = e.malloc(0x200, "harness: processor scratch (r4)")
        e.w32(proc + 0x84, 64); e.w32(proc + 0x88, 0); e.w32(proc + 0x80, e.malloc(256, "harness: array"))
        lo, hi = (start, end) if start else BUILD[where]
        r = H31.run_block(e, lo, hi, {0: 0x1d8, 4: proc, 7: 0x841564, 8: 0x841568})
        self.obj = self.o = r[6]; self.k = e.u32(self.o + 0x1b8)
        self.fx = {"insert_index": 6}; self.init_log = []
        self.ctor_state = self.state()
        if defaults: H7.Run.insert_init(self)
        self.default_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]

    def process(self, L, R):
        e = self.e; e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0 = e.vcall(self.o, 25, self.bl, self.br, N)[0]
        return r0, e.floats(self.bl, N), e.floats(self.br, N)

    def state(self):
        e, k, o = self.e, self.k, self.o
        s = {}
        for off, nm, t in KFIELDS:
            s["k.%s+0x%x" % (nm, off)] = e.rd(k + off, 1)[0] if t == "b" else e.u32(k + off)
        s["o.dry+0x10"] = e.u32(o + 0x10); s["o.wet+0x14"] = e.u32(o + 0x14)
        for i in range(6): s["o.pv%d+0x%x" % (i, 0x1bc + 4 * i)] = e.u32(o + 0x1bc + 4 * i)
        q = k + 0x28; d = lambda a: struct.unpack("<Q", e.rd(q + a, 8))[0]
        for kk, off in (("amp+0", 0), ("off+4", 4), ("id+8", 8), ("wave+0xc", 0xc), ("freq+0x10", 0x10), ("ph+0x50", 0x50),
                        ("sm0+0x60", 0x60), ("sm1+0x64", 0x64), ("rs_cnt+0x68", 0x68), ("rs_per+0x6c", 0x6c), ("P+0x84", 0x84)):
            s["osc." + kk] = e.u32(q + off)
        for kk, off in (("inv_fs+0x18", 0x18), ("slope+0x20", 0x20), ("d40", 0x40), ("d48", 0x48)):
            s["osc." + kk] = d(off)
        return s


def model_state(m):
    k = m.k; s = {}
    for off, nm, t in KFIELDS:
        key = "k.%s+0x%x" % (nm, off)
        if nm.endswith("L") and nm.startswith("z_"): v = getattr(k, nm[:-1])[0]
        elif nm.endswith("R") and nm.startswith("z_"): v = getattr(k, nm[:-1])[1]
        elif nm == "x24": s[key] = 0; continue
        elif nm == "fs": s[key] = k.fs; continue
        elif nm == "block": s[key] = k.block; continue
        else: v = getattr(k, nm)
        s[key] = (v & 0xffffffff) if t in ("i", "b") else f2u(v)
    s["o.dry+0x10"] = f2u(m.dry); s["o.wet+0x14"] = f2u(m.wet)
    for i in range(6): s["o.pv%d+0x%x" % (i, 0x1bc + 4 * i)] = f2u(m.pv[i])
    ms = H31.model_state(k.osc)
    for kk in ("amp+0", "off+4", "id+8", "wave+0xc", "freq+0x10", "ph+0x50", "sm0+0x60", "sm1+0x64", "rs_cnt+0x68",
               "rs_per+0x6c", "P+0x84", "inv_fs+0x18", "slope+0x20", "d40", "d48"):
        s["osc." + kk] = ms[kk]
    return s


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True, where="insert"):
    x = EmuDist(defaults=defaults, where=where)
    m = DM.Distortion()
    if defaults:
        for idx, u in x.default_s14: m.set_param(idx, u2f(u))
    return x, m


def signal(kind, nblk, seed=11):
    g = random.Random(seed); L = []; R = []
    for k in range(N * nblk):
        if kind == "impulse":
            L.append(1.0 if k % 1000 == 0 else 0.0); R.append(-0.5 if k % 1000 == 333 else 0.0)
        elif kind == "sine_lo":
            L.append(F(0.003 * math.sin(2 * math.pi * 220.0 * k / FS))); R.append(F(0.0021 * math.cos(2 * math.pi * 330.5 * k / FS)))
        elif kind == "sine_hi":
            L.append(F(0.9 * math.sin(2 * math.pi * 3000.0 * k / FS))); R.append(F(0.95 * math.cos(2 * math.pi * 97.0 * k / FS)))
        elif kind == "silence":
            L.append(0.0); R.append(0.0)
        elif kind == "ramp":            # level sweep: quiet -> loud -> quiet (auto-gain up, down, hold, up)
            a = 0.002 if (k // (N * 40)) % 3 == 0 else (0.8 if (k // (N * 40)) % 3 == 1 else 0.02)
            L.append(F(a * math.sin(2 * math.pi * 440.0 * k / FS))); R.append(F(a * 0.5 * math.sin(2 * math.pi * 660.0 * k / FS)))
        else:
            L.append(F(g.uniform(-1, 1))); R.append(F(g.uniform(-1, 1)))
    return L, R


# settings: (name, [(idx, value)] applied after the Insert defaults and one priming block)
SETTINGS = [
    ("insert_defaults", []),
    ("drive.25_10dB_blend.5", [(0, 0.25)]),
    ("drive.5_20dB_hp.3_pre.8_out.7_T.5", [(0, 0.5), (2, 0.3), (3, 0.8), (1, 0.7), (4, 0.5), (5, 0.8)]),
    ("drive1_40dB_T.1_hp.45_pre.6_out.55", [(0, 1.0), (4, 0.1), (2, 0.45), (3, 0.6), (1, 0.55)]),
    ("drive.1_T1_out.3_mix.5", [(0, 0.1), (4, 1.0), (1, 0.3), (5, 0.5)]),
    ("drive.6_T.05_agc", [(0, 0.6), (4, 0.05), (2, 0.2)]),
    ("hp1_20k_pre0_clamp50", [(2, 1.0), (3, 0.0), (0, 0.3), (1, 0.0)]),
    ("T1.5_clamp_drive.37_mix.4", [(4, 1.5), (0, 0.37), (5, 0.4), (2, 0.6)]),
    ("Tneg_drive.75_filters.5", [(4, -0.2), (0, 0.75), (1, 0.5), (2, 0.5), (3, 0.5)]),
]
EVENTS = [
    ("midrun_param_changes", [(0, 0.3), (4, 0.3)],
     {40: [("p", 0, 0.8), ("p", 1, 0.4)], 70: [("p", 4, 0.02), ("p", 2, 0.66)], 100: [("p", 3, 0.25), ("p", 5, 0.3), ("p", 0, 0.05)],
      130: [("p", 4, 0.9), ("p", 0, 0.55), ("p", 1, 1.0)]}),
    ("midrun_reset_slot10_ks9_16_17_same_values", [(0, 0.45), (4, 0.2), (2, 0.4), (3, 0.7)],
     {50: [("reset",)], 60: [("retrig",)], 75: [("p", 4, 0.2), ("p", 0, 0.45)], 90: [("ks9", 37.0)], 95: [("ks16",)],
      110: [("ks17",), ("reset",)], 120: [("p", 2, 0.4)], 140: [("ks9", -3.0), ("reset",)]}),
    ("midrun_agc_threshold_steps", [(0, 0.2), (4, 0.5)],
     {30: [("p", 4, 0.01)], 60: [("p", 4, 0.6)], 61: [("p", 4, 0.0)], 90: [("p", 4, 0.25)], 120: [("p", 4, 1.0), ("p", 0, 0.9)]}),
]


def run_case(name, pre, events, kind, nblk, keep=False, mut=None, prime=True, where="insert"):
    x, m = new_pair(where=where)
    if mut: mut(m)
    L, R = signal(kind, nblk + 1)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 0, "bit_exact": 0, "max_abs_err": 0.0, "state_diffs": 0,
           "first": None, "nonzero": 0, "ret_diffs": 0, "peak": 0.0, "g_min": 1e9, "g_max": 0.0}
    outE = []
    blocks = [(L[0:N], R[0:N], [])] if prime else []
    pre_ops = [("p", i, v) for i, v in pre]
    for b in range(nblk):
        ops = (pre_ops if b == 0 else []) + list(events.get(b + 1, []))
        off = N * (b + 1) if prime else N * b
        blocks.append((L[off:off + N], R[off:off + N], ops))
    for bi, (bl, br, ops) in enumerate(blocks):
        for op in ops:
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "retrig": x.e.vcall(x.o, 10)
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
            elif op[0] == "ks9": x.e.vcall(x.k, 9, f2u(op[1])); m.k.set_x20(op[1])
            elif op[0] == "ks16": x.e.vcall(x.k, 16); m.k.set_e130(1)
            elif op[0] == "ks17": x.e.vcall(x.k, 17); m.k.set_e130(0)
        r0, oL, oR = x.process(bl, br)
        mL, mR = list(bl), list(br); rm = m.process(mL, mR)
        if r0 != rm: res["ret_diffs"] += 1
        se = x.state()
        res["g_min"] = min(res["g_min"], u2f(se["k.g+0x110"])); res["g_max"] = max(res["g_max"], u2f(se["k.g+0x110"]))
        if prime and bi == 0: continue
        outE.append((oL, oR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["bit_exact"] += 1
            else:
                res["max_abs_err"] = max(res["max_abs_err"], abs(a_ - b_) if a_ == a_ and b_ == b_ else float("inf"))
                if res["first"] is None: res["first"] = ("block %d" % bi, a_, b_)
            if a_ != 0.0: res["nonzero"] += 1
            res["peak"] = max(res["peak"], abs(a_))
        dd = diff(se, model_state(m))
        if dd:
            res["state_diffs"] += len(dd)
            if res["first"] is None: res["first"] = ("state after block %d" % bi, dd[:4])
    res["exact"] = res["bit_exact"] == res["samples"] and not res["state_diffs"] and not res["ret_diffs"]
    blob = b"".join(struct.pack("<64f", *l) + struct.pack("<64f", *r) for l, r in outE)
    res["emu_sha"] = sha(blob)[:16]
    if keep: res["_x"] = x; res["_m"] = m; res["_out"] = outE
    return res, blob


def _proc(k, L, R, order="hp_lp", env="shared", post07=False, shape=None):
    """Re-statement of the kernel process with switchable alternatives (used only by the mutants)."""
    n = k.n
    def onepole(L, R, a, b, z, hp):
        zl, zr = z
        for i in range(n):
            zl = F(F(b * L[i]) + F(a * zl)); zr = F(F(b * R[i]) + F(a * zr))
            if hp: L[i] = F(L[i] - zl); R[i] = F(R[i] - zr)
            else: L[i] = zl; R[i] = zr
        return [zl, zr]
    if order == "hp_lp":
        k.z_hp = onepole(L, R, k.a_hp, k.b_hp, k.z_hp, True); k.z_pre = onepole(L, R, k.a_pre, k.b_pre, k.z_pre, False)
    else:
        k.z_pre = onepole(L, R, k.a_pre, k.b_pre, k.z_pre, False); k.z_hp = onepole(L, R, k.a_hp, k.b_hp, k.z_hp, True)
    gs = [k.g, k.g]; hs = [k.hold, k.hold] if env == "perchannel" else None
    if env == "perchannel":
        gs = list(getattr(k, "_g2", [k.g, k.g])); hs = list(getattr(k, "_h2", [k.hold, k.hold]))
    g = k.g; hold = k.hold
    def step(g, hold, m):
        if m >= k.hi:
            g = F(g * k.dec); hold = k.reload
            if g < 1.0: g = F(1.0)
        elif m >= k.lo: hold = k.reload
        elif hold > 0: hold -= 1
        else:
            g = F(g * k.inc)
            if g > 100.0: g = F(100.0)
        return g, hold
    for i in range(n):
        if env == "perchannel":
            for c, buf in enumerate((L, R)):
                buf[i] = F(buf[i] * gs[c]); gs[c], hs[c] = step(gs[c], hs[c], abs(buf[i]))
        elif env == "pregain":
            m = max(abs(L[i]), abs(R[i])); L[i] = F(L[i] * g); R[i] = F(R[i] * g); g, hold = step(g, hold, m)
        else:
            L[i] = F(L[i] * g); R[i] = F(R[i] * g); g, hold = step(g, hold, max(abs(L[i]), abs(R[i])))
    if env == "perchannel": k._g2, k._h2 = gs, hs; k.g, k.hold = gs[0], hs[0]
    else: k.g, k.hold = g, hold
    sh = shape or k.shape
    for buf in (L, R):
        for i in range(n): buf[i] = sh(buf[i], k.drive, k.blend)
    k.z_out = onepole(L, R, k.a_out, k.b_out, k.z_out, False)
    if post07:
        for buf in (L, R):
            for i in range(n): buf[i] = F(buf[i] * DM.K_07)
    return 1


def _shape_variant(y, drive, blend, toward="cube", power=3, k07=True):
    x = F(y * drive)
    if x > 1.0: s = c = F(1.0); t = F(0.0)
    elif x < -1.0: s = c = F(-1.0); t = F(0.0)
    else:
        c = F(x * F(x * x)); s = F(F(c * DM.K_HALFN) + F(x * DM.K_15)); t = F(F(1.0) - abs(s))
        t = F(t * F(t * t)) if power == 3 else F(t * t)
        if toward == "hard": c = F(1.0) if x >= 0 else F(-1.0)
    w = F(blend * t); r = F(F(w * c) + F(F(F(1.0) - w) * s))
    return F(r * DM.K_07) if k07 else r


def mutants():
    """Deliberate model errors (alternative explanations): each must make at least one comparison fail."""
    def proc_mut(**kw):
        def mut(m):
            k = m.k; k.process = lambda L, R: _proc(k, L, R, **kw)
        return mut
    def m_unclamped_freq(m):                  # cutoff not clamped to [50, 20000]
        k = m.k
        def cut(attr_p, attr_fc, attr_a, attr_b, v):
            v = F(v)
            if getattr(k, attr_p) == v: return v
            a = GE.expf(F(F(v * DM.K_M2PI) * k.inv_fs))
            setattr(k, attr_p, v); setattr(k, attr_fc, v); setattr(k, attr_a, a); setattr(k, attr_b, F(F(1.0) - a)); return v
        k._cutoff = cut
    def m_blend_lin(m):                       # blend = v (= dB/40) instead of clamp(dB/20, 0, 1)
        k = m.k; orig = k.set_drive_db
        def sd(p):
            r = orig(p); k.blend = F(min(max(F(p / DM.K_40), 0.0), 1.0)); return r
        k.set_drive_db = sd
    return [("control: unmodified model (must NOT be caught)", lambda m: None, [(0, 0.6), (4, 0.3)], "ramp"),
            ("control: _proc re-statement (must NOT be caught)", proc_mut(), [(0, 0.6), (4, 0.3)], "ramp"),
            ("blend towards hard clip (not x^3)", proc_mut(shape=lambda y, d, b: _shape_variant(y, d, b, toward="hard")), [(0, 0.6)], "sine_hi"),
            ("soft-clip weight (1-|s|)^2", proc_mut(shape=lambda y, d, b: _shape_variant(y, d, b, power=2)), [(0, 0.6)], "noise"),
            ("x0.7 after the output LPF", proc_mut(post07=True, shape=lambda y, d, b: _shape_variant(y, d, b, k07=False)), [(0, 0.4), (1, 0.5)], "noise"),
            ("envelope on the pre-gain sample", proc_mut(env="pregain"), [(4, 0.3), (0, 0.2)], "ramp"),
            ("independent gain per channel", proc_mut(env="perchannel"), [(4, 0.3), (0, 0.2)], "ramp"),
            ("LPF before HPF", proc_mut(order="lp_hp"), [(2, 0.4), (3, 0.5)], "noise"),
            ("cutoff not clamped to 50..20000 Hz", m_unclamped_freq, [(2, 0.0), (3, 0.05)], "noise"),
            ("blend = dB/40 instead of clamp(dB/20)", m_blend_lin, [(0, 0.3)], "noise")]


# ---------------------------------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "out", "H035"))
    ap.add_argument("--blocks", type=int, default=160)
    ap.add_argument("--mutants", action="store_true", help="only run the mutant check (deliberate model errors must be caught)")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rep = []; res = {}; fails = []
    P = lambda s="": (rep.append(s), print(s, flush=True))
    def check(c, msg):
        P(("  PASS " if c else "  FAIL ") + msg)
        if not c: fails.append(msg)
    if a.mutants:
        P("== mutants: each deliberate model error must make at least one comparison fail ==")
        ok = 0; ms = mutants()
        for nm_, fn, pre, kind in ms:
            r_, _ = run_case("mut", pre, {}, kind, 60, mut=fn)
            ok += (not r_["exact"]) != nm_.startswith("control")
            P("  %-48s caught %s (bit-exact %d/%d, state diffs %d)" % (nm_, not r_["exact"], r_["bit_exact"], r_["samples"], r_["state_diffs"]))
        check(ok == len(ms), "all %d mutants caught and both controls exact" % (len(ms) - 2))
        P(); P("RESULT: %d failed checks" % len(fails))
        with open(os.path.join(a.out, "h035_mutants.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
        return 1 if fails else 0
    im = sp16img.Image()

    # ---------------- C1 parameter list ------------------------------------------------------------------------------
    P("== C1 Distortion parameters ==")
    x = EmuDist(defaults=False)
    st0 = x.state()
    m0 = DM.Distortion()
    dd = diff(st0, model_state(m0))
    P("  after inline ctor block: stored values +0x1bc..+0x1d0 = %s; EffectBase dry/wet %r/%r; kernel drive %r gain %r hold %d "
      "thr hi/lo %r/%r; cutoffs out/hp/pre %r/%r/%r" % ([u2f(st0["o.pv%d+0x%x" % (i, 0x1bc + 4 * i)]) for i in range(6)],
      u2f(st0["o.dry+0x10"]), u2f(st0["o.wet+0x14"]), u2f(st0["k.drive+0x104"]), u2f(st0["k.g+0x110"]), st0["k.hold+0x120"],
      u2f(st0["k.hi+0x108"]), u2f(st0["k.lo+0x10c"]), u2f(st0["k.fc_out+0xd4"]), u2f(st0["k.fc_hp+0xe8"]), u2f(st0["k.fc_pre+0xfc"])))
    check(not dd, "ctor state (Distortion + c_distortion + oscillator, %d fields) == model before any call%s" % (len(st0), "" if not dd else " %s" % dd[:5]))
    x = EmuDist(defaults=True)
    dflt = [(i_, u2f(u_), hex(u_)) for i_, u_ in x.default_s14]
    P("  Insert slot-52 case 6 slot-14 calls (index, value, bits): %s" % dflt)
    res["C1_insert_defaults"] = dflt
    st1 = x.state()
    P("  after defaults: drive %r blend %r, out/hp/pre cutoff %r/%r/%r (change copies %r/%r/%r), thr hi/lo %r/%r, dry/wet %r/%r, "
      "+0x20 %r +0x124 %r" % (u2f(st1["k.drive+0x104"]), u2f(st1["k.blend+0x134"]), u2f(st1["k.fc_out+0xd4"]), u2f(st1["k.fc_hp+0xe8"]),
      u2f(st1["k.fc_pre+0xfc"]), u2f(st1["k.p_out+0x10"]), u2f(st1["k.p_hp+0x14"]), u2f(st1["k.p_pre+0x18"]), u2f(st1["k.hi+0x108"]),
      u2f(st1["k.lo+0x10c"]), u2f(st1["o.dry+0x10"]), u2f(st1["o.wet+0x14"]), u2f(st1["k.p_x20+0x20"]), u2f(st1["k.x124+0x124"])))
    imap = {}
    for idx in range(0, 9):
        x, m = new_pair()
        s_before = x.state(); r0 = x.set(idx, 0.37); s_after = x.state()
        ch = sorted(k_ for k_ in s_after if s_after[k_] != s_before[k_])
        imap[idx] = {"ret": r0, "changed_immediately": ch}
        P("  slot14(%d, 0.37) -> ret %d, fields changed immediately: %s" % (idx, r0, ch))
    res["C1_index_map"] = imap
    check(set(imap[0]["changed_immediately"]) == {"k.p_drive+0xc", "k.drive+0x104", "k.blend+0x134", "o.pv0+0x1bc"} and
          set(imap[1]["changed_immediately"]) == {"k.p_out+0x10", "k.fc_out+0xd4", "k.a_out+0xc4", "k.b_out+0xc8", "o.pv1+0x1c0"} and
          set(imap[2]["changed_immediately"]) == {"k.p_hp+0x14", "k.fc_hp+0xe8", "k.a_hp+0xd8", "k.b_hp+0xdc", "o.pv2+0x1c4"} and
          set(imap[3]["changed_immediately"]) == {"k.p_pre+0x18", "k.fc_pre+0xfc", "k.a_pre+0xec", "k.b_pre+0xf0", "o.pv3+0x1c8"} and
          set(imap[4]["changed_immediately"]) == {"k.p_thr+0x1c", "k.hi+0x108", "k.lo+0x10c", "o.pv4+0x1cc"} and
          set(imap[5]["changed_immediately"]) == {"o.dry+0x10", "o.wet+0x14", "o.pv5+0x1d0"} and
          all(imap[i]["changed_immediately"] == [] for i in (6, 7, 8)) and all(v["ret"] == 0 for v in imap.values()),
          "index 0 drive / 1 output LPF / 2 HPF / 3 pre-clip LPF / 4 auto-gain threshold / 5 mix: all applied immediately "
          "(kernel 0xfa614 / slots 5 / 6 / 7 / 8 / EffectBase), stored at +0x1bc+4i; 6..8 ignored; slot 14 returns 0")
    # change detection: kernel setters skip unchanged values (poke a coefficient, re-send the same value)
    x, m = new_pair(); x.set(1, 0.5); x.e.w32(x.k + 0xc4, f2u(0.123)); x.set(1, 0.5); same = u2f(x.e.u32(x.k + 0xc4))
    x.set(1, 0.5000001); new = u2f(x.e.u32(x.k + 0xc4))
    x.e.w32(x.k + 0x104, f2u(3.0)); x.set(0, 0.0); d0 = u2f(x.e.u32(x.k + 0x104))
    P("  change detection: out-LPF coefficient poked to 0.123, same v re-sent -> %r (kept); v + 1 ulp -> %r; drive poked to 3, "
      "drive v 0 (= stored 0 dB) re-sent -> %r (kept)" % (same, new, d0))
    check(same == F(0.123) and new != F(0.123) and d0 == F(3.0), "kernel setters skip a value equal to their stored copy (+0x0c..+0x1c)")
    res["C1_change_detection"] = [same, new, d0]

    # ---------------- C2 formula sweeps --------------------------------------------------------------------------------
    P(); P("== C2 formula read-backs (emulated fields vs model after every slot-14 call) ==")
    c2 = {}
    def sweep(name, setup, seq, fields):
        x, m = new_pair()
        for idx, v in setup: x.set(idx, v); m.set_param(idx, v)
        rows = []; bad = 0
        for item in seq:
            if item[0] == "k9": x.e.vcall(x.k, 9, f2u(item[1])); m.k.set_x20(item[1])
            else:
                idx, v = item; x.set(idx, v); m.set_param(idx, v)
            se, sm = x.state(), model_state(m)
            dd = diff(se, sm); bad += bool(dd)
            rows.append([item] + [u2f(se[f_]) for f_ in fields] + ([dd[:3]] if dd else []))
        c2[name] = {"n": len(seq), "mismatch": bad, "rows": rows}
        P("  %-26s %4d values, model != emulation in %d" % (name, len(seq), bad))
        return rows
    dv = [0.0, 0.01, 0.1, 0.25, 0.3, 0.4999, 0.5, 0.5001, 0.75, 0.99, 1.0, 1.2, -0.1, 0.0]
    rows = sweep("drive", [], [(0, v) for v in dv], ["k.p_drive+0xc", "k.drive+0x104", "k.blend+0x134"])
    P("    v -> (dB, drive, blend): " + ", ".join("%g->(%g,%.6g,%g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    fv = [0.0, 0.05, 0.1, 0.13, 0.1327, 0.133, 0.2, 0.3333, 0.5, 0.75, 0.9, 0.99, 0.9999, 1.0, 1.1, -0.1]
    fsets = {}
    for idx, nm, flds in ((1, "out_lpf", ["k.p_out+0x10", "k.fc_out+0xd4", "k.a_out+0xc4"]), (2, "hpf", ["k.p_hp+0x14", "k.fc_hp+0xe8", "k.a_hp+0xd8"]),
                          (3, "pre_lpf", ["k.p_pre+0x18", "k.fc_pre+0xfc", "k.a_pre+0xec"])):
        rows = sweep(nm, [], [(idx, v) for v in fv], flds); fsets[nm] = rows
    P("    v -> (f, cutoff, a) [hpf]: " + ", ".join("%g->(%.6g,%.6g,%.6g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in fsets["hpf"]))
    g = random.Random(35)
    sweep("cutoff_random_300", [], [(1 + (i % 3), F(g.random())) for i in range(300)], ["k.a_out+0xc4"])
    tv = [0.0, 0.05, 0.1, 0.5, 0.70794576, 1.0, 1.5, -0.2, 0.33]
    rows = sweep("threshold", [], [(4, v) for v in tv], ["k.p_thr+0x1c", "k.hi+0x108", "k.lo+0x10c"])
    P("    v -> (copy, hi, lo): " + ", ".join("%g->(%g,%g,%.8g)" % (r_[0][1], r_[1], r_[2], r_[3]) for r_ in rows))
    mv = [0.0, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, -0.5]
    rows = sweep("mixratio", [], [(5, v) for v in mv], ["o.dry+0x10", "o.wet+0x14", "k.p_x20+0x20", "k.x124+0x124"])
    P("    v -> (dry, wet, kernel +0x20, +0x124): " + ", ".join("%g->(%g,%g,%g,%g)" % (r_[0][1], r_[1], r_[2], r_[3], r_[4]) for r_ in rows))
    rows = sweep("kernel_slot9_direct", [], [("k9", v) for v in (0.0, 50.0, 100.0, 150.0, -1.0, 12.5)], ["k.p_x20+0x20", "k.x124+0x124"])
    P("    kernel slot 9 v -> (+0x20, +0x124): " + ", ".join("%g->(%g,%g)" % (r_[0][1], r_[1], r_[2]) for r_ in rows))
    res["C2"] = {k_: {"n": v["n"], "mismatch": v["mismatch"]} for k_, v in c2.items()}
    res["C2_rows"] = {k_: [[str(c_) for c_ in r_] for r_ in v["rows"]] for k_, v in c2.items()}
    check(all(v["mismatch"] == 0 for v in c2.values()),
          "all %d read-backs (kernel + EffectBase fields) == model formulas" % sum(v["n"] for v in c2.values()))
    # libm oracles: emulated 1.60 libm vs the model's own routines
    e = H31.new_emu(); Lm = H31.EmuLibm(e); pw = e.lib_exports["pow"][0]; pwf = e.lib_exports["powf"][0]
    g = random.Random(7); bp = be = bf = 0; hp = 0; bcr = 0
    for i in range(2000):
        y = float(F(F(g.random()) * F(3.0))); u = d2u(y)
        r0, r1 = e.call(pw, 0, 0x40240000, u & 0xffffffff, u >> 32); r = u2d(r0 | (r1 << 32))
        bp += r != DM.pow10_cr(y); hp += r != math.pow(10.0, y)
    inv = F(1.0 / F(44100.0))
    for i in range(3000):
        fc = F(g.uniform(50.0, 20000.0)); arg = F(F(fc * DM.K_M2PI) * inv)
        r_ = f2u(Lm.expf(arg)); be += r_ != f2u(GE.expf(arg)); bcr += r_ != f2u(CR.expf(arg))
    for i in range(2000):
        p = F(F(g.random()) * F(40.0)); ex = F(p * DM.K_005)
        bf += f2u(u2f(e.call(pwf, f2u(10.0), f2u(ex))[0])) != f2u(fd_powf(10.0, ex))
    P("  libm oracle: pow(10, y) emu != decimal-CR in %d/2000 (host math.pow differs in %d/2000); expf(cutoff args) emu != glibc_expf "
      "in %d/3000 (correctly rounded crmath.expf would differ in %d/3000); powf(10, dB/20) emu != fdlibm in %d/2000" % (bp, hp, be, bcr, bf))
    res["C2_libm"] = {"pow": bp, "pow_host": hp, "expf": be, "expf_crmath": bcr, "powf": bf}
    check(bp == 0 and be == 0 and bf == 0, "the model's pow / expf / powf equal the emulated 1.60 libm on all sampled arguments")

    # ---------------- C4 end-to-end matrix ------------------------------------------------------------------------------
    P(); P("== C4 end-to-end: emulated slot 25 vs harness/models/distortion.py, %d blocks ==" % a.blocks)
    c4 = []
    def emit(r_, blob):
        c4.append(r_)
        with open(os.path.join(a.out, "emu_%s_%s.f32" % (r_["name"], r_["signal"])), "wb") as fh: fh.write(blob)
        P("  %-42s %-7s bit-exact %6d/%-6d max|err| %-8.3g state diffs %d nonzero %5d peak %.4f gain %.4g..%.4g %s" %
          (r_["name"], r_["signal"], r_["bit_exact"], r_["samples"], r_["max_abs_err"], r_["state_diffs"], r_["nonzero"],
           r_["peak"], r_["g_min"], r_["g_max"], "" if r_["exact"] else "FIRST %s" % (r_["first"],)))
    for name, pre in SETTINGS:
        for kind in ("impulse", "sine_lo", "sine_hi", "noise", "silence"):
            emit(*run_case(name, pre, {}, kind, a.blocks))
    emit(*run_case("agc_to_limit_T.5_drive.3", [(4, 0.5), (0, 0.3)], {}, "sine_lo", 520))
    emit(*run_case("agc_ramp_T.3_drive.4", [(4, 0.3), (0, 0.4), (5, 0.7)], {}, "ramp", 240))
    for name, pre, ev in EVENTS:
        for kind in ("ramp", "noise"):
            emit(*run_case(name, pre, ev, kind, a.blocks))
    res["C4"] = [{k_: v for k_, v in r_.items()} for r_ in c4]
    nz = [r_ for r_ in c4 if r_["signal"] != "silence"]
    check(all(r_["exact"] for r_ in c4) and all(r_["nonzero"] > 0 for r_ in nz),
          "model == emulation bit-exactly (outputs, return codes, %d state fields after every block) in all %d runs"
          % (len(model_state(DM.Distortion())), len(c4)))
    lim = [r_ for r_ in c4 if r_["name"].startswith("agc_to_limit")][0]
    P("  auto-gain range seen: min %.4g, max %.4g (limit run reaches %.4g)" % (min(r_["g_min"] for r_ in c4), max(r_["g_max"] for r_ in c4), lim["g_max"]))
    check(lim["g_max"] == 100.0 and min(r_["g_min"] for r_ in c4) == 1.0, "envelope limits 1 and 100 both exercised")
    P("  totals: %d runs, %d samples" % (len(c4), sum(r_["samples"] for r_ in c4)))

    # ---------------- C3 layout / vtables -------------------------------------------------------------------------------
    P(); P("== C3 vtables and unused fields ==")
    vt = {nm: [hex(im.u32(base + 4 * i)) for i in range(n)] for nm, base, n in (("Distortion 0x842898", 0x842898, 32), ("c_distortion 0x8418a0", 0x8418a0, 20),
                                                                                ("c_effect_base 0x841830", 0x841830, 20))}
    for nm, v in vt.items(): P("  %s: %s" % (nm, " ".join("%d:%s" % (i, s) for i, s in enumerate(v))))
    res["C3_vtables"] = vt
    ch_vt = [hex(im.u32(0x842920 + 4 * i)) for i in range(32)]
    P("  Distortion slots that differ from Chorus 0x842920: %s" % [i for i in range(32) if ch_vt[i] != vt["Distortion 0x842898"][i]])
    P("  c_distortion slots overriding c_effect_base: %s" % [i for i in range(20) if vt["c_distortion 0x8418a0"][i] != vt["c_effect_base 0x841830"][i]])
    calls = im.direct_calls()
    for t_ in (0xfa694, 0xfa70c, 0xfa614, 0xfa36c, 0xfa78c):
        P("  direct callers of 0x%x: %s" % (t_, [hex(s) for s, t, k in calls if t == t_]))
    outs = []
    for flag in (False, True):
        x, _ = new_pair(); o = []
        L, R = signal("noise", 40); x.set(0, 0.5); x.set(4, 0.3)
        for b in range(40):
            if flag and b == 10: x.e.vcall(x.k, 16)
            if flag and b == 20: x.e.vcall(x.k, 9, f2u(7.0))
            o.append(x.process(L[N * b:N * b + N], R[N * b:N * b + N])[1:])
        outs.append(sha(repr(o).encode()))
    check(outs[0] == outs[1], "kernel byte +0x130 (slots 16/17) and kernel slot 9 (+0x20/+0x124) do not change the output")
    # kernel slot 2 (re-init) at other block sizes / rates, its failure path, and recovery through Distortion slot 27
    x, m = new_pair(); L, R = signal("noise", 12); s2 = []
    for i_, v_ in ((0, 0.5), (4, 0.3), (1, 0.6)): x.set(i_, v_); m.set_param(i_, v_)
    for b, (blk, fs) in enumerate(((32, 48000), (64, 22050), (0, 44100), (64, -1))):
        r_e = x.e.vcall(x.k, 2, blk, fs & 0xffffffff)[0]; r_m = m.k.reinit(blk, fs)
        se = x.state(); dd2 = diff(se, model_state(m))
        ok_b = True
        for bb in range(2):
            Lb, Rb = L[N * (2 * b + bb):N * (2 * b + bb + 1)], R[N * (2 * b + bb):N * (2 * b + bb + 1)]
            _, oL, oR = x.process(Lb, Rb); mL, mR = list(Lb), list(Rb); m.k.process(mL, mR)
            ok_b &= fl_bits(oL + oR) == fl_bits(mL + mR)
        dd3 = diff(x.state(), model_state(m))
        s2.append((blk, fs, r_e, r_m, u2f(se["k.inc+0x114"]), u2f(se["k.dec+0x118"]), se["k.reload+0x11c"], u2f(se["k.drive+0x104"]),
                   len(dd2) + len(dd3), ok_b))
    x.e.vcall(x.o, 27); m.reset(); d27b = diff(x.state(), model_state(m))
    P("  kernel slot 2 (block, fs) -> (ret emu/model, inc, dec, hold reload, drive, state diffs, output exact incl. untouched "
      "buffers on failure): %s; Distortion slot 27 afterwards restores 64/44100 (diffs %d)" % (s2, len(d27b)))
    check(all(t[2] == t[3] and t[8] == 0 and t[9] for t in s2) and s2[2][7] == -1.0 and not d27b,
          "kernel slot 2 = init(block, fs) for block, fs > 0 (envelope constants exp(1/(0.1 fs)), exp(-1/(0.003 fs)), hold fs/50 "
          "follow fs); block or fs <= 0 -> drive -1, process returns 0 and leaves the buffers untouched")
    res["C3_slot2"] = [list(map(str, t)) for t in s2]

    # ---------------- C5 start-up / reset / retrigger -------------------------------------------------------------------
    P(); P("== C5 start-up, slot 27 reset, slot 10, slot 5 ==")
    r_, _ = run_case("startup_no_prime", [(0, 0.5)], {}, "noise", 3, keep=True, prime=False)
    b0 = r_["_out"][0]; nz0 = sum(1 for v in b0[0] + b0[1] if v != 0.0)
    P("  first block after construction + defaults (no priming): %d/128 non-zero output samples, bit-exact %s, first L sample %r"
      % (nz0, r_["exact"], b0[0][0]))
    x, m = new_pair()
    for i_, v_ in ((0, 0.6), (4, 0.4), (2, 0.5), (3, 0.6), (1, 0.7), (5, 0.6)): x.set(i_, v_); m.set_param(i_, v_)
    L, R = signal("ramp", 30)
    for b in range(30): x.process(L[N * b:N * b + N], R[N * b:N * b + N]); m.process(L[N * b:N * b + N][:], R[N * b:N * b + N][:])
    s_b = x.state(); r27 = x.e.vcall(x.o, 27)[0]; m.reset(); s_a = x.state()
    d27 = diff(s_a, model_state(m))
    P("  slot 27 0x115b0c: before gain %r hold %d z_hpL %r drive %r; after gain %r hold %d z_hpL %r drive %r cutoffs %r/%r/%r thr %r; "
      "ret %d; model diffs %s" % (u2f(s_b["k.g+0x110"]), s_b["k.hold+0x120"], u2f(s_b["k.z_hpL+0xe0"]), u2f(s_b["k.drive+0x104"]),
                                  u2f(s_a["k.g+0x110"]), s_a["k.hold+0x120"], u2f(s_a["k.z_hpL+0xe0"]), u2f(s_a["k.drive+0x104"]),
                                  u2f(s_a["k.fc_out+0xd4"]), u2f(s_a["k.fc_hp+0xe8"]), u2f(s_a["k.fc_pre+0xfc"]), u2f(s_a["k.hi+0x108"]), r27, d27[:4]))
    s_c = x.state(); r10 = x.e.vcall(x.o, 10)[0]; s_d = x.state()
    P("  slot 10 0x115bc8 returns %d, state changed: %s" % (r10, s_c != s_d))
    # EffectBase slot 5 (activation): does it reach slot 27?
    x2, _ = new_pair(); hits = []
    x2.e.add_watch(0x115b0c, lambda em: hits.append(1))
    for b in range(5): x2.process(L[N * b:N * b + N], R[N * b:N * b + N])
    s5b = x2.state(); x2.e.vcall(x2.o, 5, 0, 1); s5a = x2.state()
    P("  EffectBase slot 5 (0, 1): slot 27 entered %d times; kernel gain %r -> %r, z_hpL %r -> %r"
      % (len(hits), u2f(s5b["k.g+0x110"]), u2f(s5a["k.g+0x110"]), u2f(s5b["k.z_hpL+0xe0"]), u2f(s5a["k.z_hpL+0xe0"])))
    check(nz0 > 0 and r_["exact"] and not d27 and u2f(s_a["k.g+0x110"]) == 1.0 and s_a["k.hold+0x120"] == 882 and
          s_a["k.z_hpL+0xe0"] == 0 and s_c == s_d and r10 == 0,
          "no start-up mute/fade/gate; slot 27 = full kernel re-init (gain 1, hold 882, filter states 0) then the six stored "
          "values re-applied (model == emulation); slot 10 does nothing")
    res["C5"] = {"block0_nonzero": nz0, "slot27_diffs": len(d27), "slot5_reaches_slot27": len(hits)}

    # ---------------- C6 alternatives -------------------------------------------------------------------------------------
    P(); P("== C6 alternative explanations ==")
    caught = []
    for nm_, fn, pre, kind in mutants():
        r_, _ = run_case("mut", pre, {}, kind, 40, mut=fn)
        caught.append((not r_["exact"]) != nm_.startswith("control"))
        P("  mutant %-48s caught %s (bit-exact %d/%d, max|err| %.3g, state diffs %d)" % (nm_, not r_["exact"], r_["bit_exact"],
                                                                                    r_["samples"], r_["max_abs_err"], r_["state_diffs"]))
    check(all(caught), "all %d alternative models are refuted by the emulation; the 2 controls stay bit-exact" % (len(caught) - 2))
    # Mixratio at slot-18 level: crossfade dry = 1 - v vs dry at unity
    def slot18_run(mix):
        x, m = new_pair(); e = x.e
        e.add_watch(0x106c88, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        L, R = signal("noise", 60); o = []; w = []
        for i_, v_ in ((5, mix), (0, 0.5)): x.set(i_, v_); m.set_param(i_, v_)
        bl = e.malloc(4 * N); br = e.malloc(4 * N)
        for b in range(60):
            e.set_floats(bl, L[N * b:N * b + N]); e.set_floats(br, R[N * b:N * b + N])
            s9 = e.vcall(x.o, 9)[0]
            if s9 == 0 and b == 0: e.vcall(x.o, 5, 0, 1); e.vcall(x.o, 7, 0); m.reset()
            e.vcall(x.o, 18, bl, br, N)
            o.append((e.floats(bl, N), e.floats(br, N)))
            wl, wr = list(L[N * b:N * b + N]), list(R[N * b:N * b + N]); m.process(wl, wr); w.append((wl, wr))
        laws = {"F(F(dry*in)+F(wet*y))": 0, "F(in+F(mix*y))": 0, "F(F(wet*y)+F(dry*in))": 0}; ns = 0; err = 0.0
        dry = F(F(1.0) - F(mix)); wet = F(mix)
        for b in range(40, 60):
            for ch in (0, 1):
                for i in range(N):
                    inp = (L if ch == 0 else R)[N * b + i]; y = w[b][ch][i]; out = o[b][ch][i]; ns += 1
                    laws["F(F(dry*in)+F(wet*y))"] += f2u(out) != f2u(F(F(dry * inp) + F(wet * y)))
                    laws["F(in+F(mix*y))"] += f2u(out) != f2u(F(inp + F(wet * y)))
                    laws["F(F(wet*y)+F(dry*in))"] += f2u(out) != f2u(F(F(wet * y) + F(dry * inp)))
                    err = max(err, abs(out - (dry * inp + wet * y)))
        return laws, ns, err
    s18 = {mix: slot18_run(mix) for mix in (0.0, 0.3, 1.0)}
    for k_, (laws, ns, err) in s18.items():
        P("  slot 18 (gate opened, 0x106c88 neutralised), mix %g, blocks 40..59: mismatching samples per law %s of %d; max|out - "
          "((1-v) in + v y)| %.3g" % (k_, laws, ns, err))
    res["C6_slot18"] = {str(k_): [v[0], v[1], v[2]] for k_, v in s18.items()}
    check(all(v[0]["F(F(dry*in)+F(wet*y))"] == 0 or v[0]["F(F(wet*y)+F(dry*in))"] == 0 for v in s18.values()) and
          s18[0.3][0]["F(in+F(mix*y))"] > 0,
          "slot 18 crossfades: out = (1 - Mixratio) in + Mixratio y (unity-dry law of Chorus/Flanger refuted for Distortion)")

    # ---------------- C7 Master / Send context ----------------------------------------------------------------------------
    P(); P("== C7 Master / Send FX context ==")
    sites = [s for s, t, k in calls if t == KCTOR]
    P("  c_distortion ctor call sites: %s" % [hex(s) for s in sites])
    def stream(lo, hi):
        out = []
        for i in im.disasm(lo, hi):
            t = i.mnemonic + " " + i.op_str
            if "[pc, #" in i.op_str:
                lit = (i.address + 8 + int(i.op_str.split("#")[1].rstrip("]"), 0)) & ~3
                t = i.mnemonic + " " + i.op_str.split(",")[0] + ", =0x%x" % im.u32(lit)
            if i.mnemonic.startswith("b") and i.op_str.startswith("#"):
                tg = int(i.op_str[1:], 16)
                if lo <= tg <= hi: t = i.mnemonic + " <block+0x%x>" % (tg - lo)
            out.append(t)
        return out
    ins_site = 0x11909c; blocks = {}
    for s in sites:
        lo = s - (ins_site - BUILD["insert"][0]); hi = s + (BUILD["insert"][1] - ins_site)
        blocks[hex(s)] = (lo, hi)
    st = {k_: stream(*v) for k_, v in blocks.items()}
    ref = st[hex(ins_site)] if hex(ins_site) in st else None
    same_all = True
    for k_, v in st.items():
        dl = [(i_, p_, q_) for i_, (p_, q_) in enumerate(zip(ref, v)) if p_ != q_] if ref else ["no insert site"]
        same_all &= not dl and len(v) == len(ref)
        P("  block 0x%x-0x%x (site %s): %d instructions, differing from Insert: %s" % (blocks[k_][0], blocks[k_][1], k_, len(v), dl[:6]))
    runs = {}
    for k_, (lo, hi) in blocks.items():
        try:
            xx = EmuDist(defaults=False, start=lo, end=hi)
        except Exception as ex:
            runs[k_] = "build failed: %s" % ex; continue
        Ls, Rs = signal("noise", 60); hh = []
        for i_, v_ in ((0, 0.5), (4, 0.3), (2, 0.4), (3, 0.7), (1, 0.6), (5, 0.5)): xx.set(i_, v_)
        for b in range(60): hh.append(xx.process(Ls[N * b:N * b + N], Rs[N * b:N * b + N])[1:])
        runs[k_] = sha(repr(hh).encode())[:16] + " vptr 0x%x" % xx.e.u32(xx.o)
    P("  60 noise blocks from each built object (same parameters): %s" % runs)
    res["C7"] = {"sites": [hex(s) for s in sites], "identical_blocks": same_all, "runs": runs}
    hs = set(v.split()[0] for v in runs.values())
    check(len(sites) >= 2 and same_all and len(hs) == 1, "every c_distortion construction block is identical to the Insert one and "
          "the built objects give identical output (defaults not checked)")

    P(); P("RESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  failed: " + f_)
    with open(os.path.join(a.out, "h035_report.txt"), "w") as fh: fh.write("\n".join(rep) + "\n")
    with open(os.path.join(a.out, "h035.json"), "w") as fh: json.dump(res, fh, indent=1, sort_keys=True, default=str)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
