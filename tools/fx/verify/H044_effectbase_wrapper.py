#!/usr/bin/env python3
"""H044 — one common EffectBase slot-18 wrapper model (harness/models/effectbase.py) validated against the real 1.60 code.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Emulation is guest-memory only (unicorn); nothing is
written outside --out, and no image is built. Own code only; Pioneer bytes are read at run time and never stored.

Sections (criteria of kb/cycles/026.md):
  C1  constants/records: literal constants used by the wrapper laws (read from the file), the slot-31 gate records for modes 0..3
      (emulated slot 31 vs model), the gate/SmoothFloat/SignalGate/IirHpf1stOrder state after the real ctor vs the model ctor,
      HPF coefficients 0xe1aa0 (emulated slot 5) vs the model for several fc / fs.
  C3  stub matrix: H011 stub effect (real EffectBase ctor, own slots 23..27) driven through the real slot 18 0x106de4 with the
      processBlock activation sequence; the model with the same injected slot 25/26 must give bit-identical output, slot-9 and
      slot-18 returns, slot-25 (n, input) and gate / skip / HPF state after every block.
  C4  composition: real InsertFxDelay (mode 1), real InsertFxCompressor (+0xa8 = 1, as the Insert ctor leaves it), real Flanger
      (HPF on) through the real slot 18 vs effectbase.EffectBase wrapping the per-effect slot-25 models.
  C5  processor: real InsertFxProcessor setFxType 0x11735c + processBlock 0x116860 (H011 stand-in fields) with stub effects and a
      real InsertFxCompressor at index 7, vs effectbase.InsertProcessor.
  C6  H074 numbers (Insert COMPRESSOR skip/clamp) from C4/C5.
Run: .venv/bin/python -B harness/H044_effectbase_wrapper.py --out DIR      (--quick: fewer cases)
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import sp16img                                                 # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
import H011_effect_interface as H11                            # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import effectbase as EB                                        # noqa: E402
from lofi import F                                             # noqa: E402

EB_CTOR = 0x1067d8
N = 64


def sha(b): return hashlib.sha256(b).hexdigest()
def bits(xs): return [f2u(x) for x in xs]
def pack(xs): return struct.pack("<%df" % len(xs), *xs)


# ===================================================================================================================== emulated side
def make_stub(h, label, fs=44100, mode=0, w=1.0, gain=0.5, ret=0):
    """As H011 Host.make_stub, with the sample rate as a parameter."""
    e = h.e
    o = e.malloc(0x1c0, "stub effect"); e.call(EB_CTOR, o, fs, 64, mode)
    vt = e.malloc(4 * 34, "stub vtable copy")
    e.w32(vt, e.u32(H11.EB_VT - 8)); e.w32(vt + 4, e.u32(H11.EB_VT - 4))
    for k in range(32): e.w32(vt + 8 + 4 * k, h.base[k])
    for k in (23, 24, 25, 26, 27): e.w32(vt + 8 + 4 * k, h.STUB + 4 * k)
    e.w32(o, vt + 8)
    h.objs[o] = label; h.cfg[o] = dict(w=w, gain=gain, ret=ret)
    return o


def emu_state(e, o):
    """Wrapper state of an emulated EffectBase object (all floats as bits)."""
    g = e.u32(o + 0xc8); u = e.u32; b = lambda a: e.rd(a, 1)[0]
    s = {"g.cur": u(g + 0x1c), "g.trans": b(g + 0x20), "g.tgt": u(g + 0x24), "g.pend": b(g + 0x28), "g.c0": u(g + 0xc0),
         "g.c4": u(g + 0xc4), "skip": (b(o + 0xac), u(o + 0xb0)), "clamp": (b(o + 0xb4), u(o + 0xb8)), "hpf": (b(o + 0xcc), b(o + 0xcd)),
         "dry": u(o + 0x10), "wet": u(o + 0x14)}
    for nm, a in (("in", g + 0x48), ("dry", g + 0x6c), ("wet", g + 0x90)):
        s["sf." + nm] = (u(a + 4), u(a + 8), u(a + 0xc), u(a + 0x10), u(a + 0x14), u(a + 0x1c))
    for nm, a in (("gA", o + 0x128), ("gB", o + 0x170)):
        q = a + 0x1c; s[nm] = (u(q + 4), u(q + 8), u(q + 0xc), u(q + 0x10), u(q + 0x14))
    hp = o + 0xd8
    s["hpf.coef"] = (u(hp + 0xc), u(hp + 0x24), u(hp + 0x28), u(hp + 0x2c), u(hp + 0x34), b(hp + 0x48))
    st1 = u(hp + 0x10); st5 = u(hp + 0x20)
    s["hpf.st"] = (u(st1), u(st1 + 4), u(st1 + 8), u(st1 + 12), u(st5), u(st5 + 4))
    return s


def model_state(m):
    g = m.gate
    s = {"g.cur": g.cur, "g.trans": g.trans, "g.tgt": g.tgt, "g.pend": g.pend, "g.c0": f2u(g.c0), "g.c4": f2u(g.c4),
         "skip": (m.skip_armed, m.skip), "clamp": (m.clamp_armed, m.clamp), "hpf": (m.hpf_req, m.hpf_cur),
         "dry": f2u(m.dry), "wet": f2u(m.wet)}
    for nm, sf in (("in", g.sin), ("dry", g.sdry), ("wet", g.swet)):
        s["sf." + nm] = (sf.state, f2u(sf.cur), f2u(sf.target), f2u(sf.step), sf.rem, sf.N)
    for nm, gg in (("gA", m.gA), ("gB", m.gB)):
        r = gg.r; s[nm] = (r.state, f2u(r.cur), f2u(r.target), f2u(r.inc), r.rem)
    hp = m.hpf
    s["hpf.coef"] = (f2u(hp.fc), f2u(hp.k), f2u(hp.b0), f2u(hp.b1), f2u(hp.a1), 0)
    s["hpf.st"] = (f2u(hp.v1[0]), f2u(hp.v1[1]), f2u(hp.y1[0]), f2u(hp.y1[1]), f2u(hp.yp[0]), f2u(hp.yp[1]))
    return s


def sdiff(a, b): return [(k, a[k], b.get(k)) for k in a if a[k] != b.get(k)]


# ===================================================================================================================== signals
def signal(kind, nblk, seed=11, amp=0.5):
    n = nblk * N; g = random.Random(seed)
    if kind == "noise":
        return [F(g.uniform(-amp, amp)) for _ in range(n)], [F(g.uniform(-amp, amp)) for _ in range(n)]
    if kind == "dc":
        return [F(0.5)] * n, [F(-0.25)] * n
    if kind == "impulse":
        L = [F(0.0)] * n; R = [F(0.0)] * n
        for i in range(3, n, 97): L[i] = F(0.9); R[(i + 40) % n] = F(-0.7)
        return L, R
    if kind == "tiny":      # denormal / near-FLT_MIN noise (flush-to-zero paths)
        return [F(g.uniform(-4e-38, 4e-38)) for _ in range(n)], [F(g.uniform(-4e-38, 4e-38)) for _ in range(n)]
    if kind == "sine":
        return ([F(0.6 * math.sin(2 * math.pi * 440.0 * i / 44100.0)) for i in range(n)],
                [F(0.4 * math.sin(2 * math.pi * 97.0 * i / 44100.0 + 0.3)) for i in range(n)])
    raise ValueError(kind)


# ===================================================================================================================== C3 stub case
def run_stub_case(spec, keep=False):
    """spec: name, fs, mode, w, gain, ret, s22 (slot-22 value; None = leave ctor 1), hpf (bool), nine_d, sig, nblk, act (first
    activation block), events {block: [ops]}. ops: ("stop", a) ("act",) ("w", w) ("ret", r) ("gain", g) ("hpf", on, fc) ("s21", v)."""
    fs = spec.get("fs", 44100); mode = spec.get("mode", 0); nblk = spec.get("nblk", 200)
    h = H11.Host(); e = h.e
    o = make_stub(h, "S", fs=fs, mode=mode, w=spec.get("w", 1.0), gain=spec.get("gain", 0.5), ret=spec.get("ret", 0))
    cfg = dict(w=spec.get("w", 1.0), gain=spec.get("gain", 0.5), ret=spec.get("ret", 0))
    mlog = []
    def s25(eb, L, R, n):
        mlog.append((n, bits(L), bits(R)))
        g = cfg["gain"]
        for k in range(n): L[k] = F(g * L[k]); R[k] = F(g * R[k])
        return cfg["ret"]
    def s26(eb): eb.dry = F(1.0 - cfg["w"]); eb.wet = F(cfg["w"])
    m = EB.EffectBase(fs=fs, mode=mode, slot25=s25, slot26=s26)
    s22 = spec.get("s22", 0)
    if s22 is not None: h.vc(o, 22, s22); m.slot22(s22)
    if spec.get("hpf", True): e.call(0x106c7c, o, 1, f2u(spec.get("fc", 10.0))); m.set_post_hpf(True, spec.get("fc", 10.0))
    nine_d = spec.get("nine_d", 1)
    L, R = signal(spec.get("sig", "noise"), nblk, seed=spec.get("seed", 11))
    bl = e.malloc(256); br = e.malloc(256)
    want = spec.get("act", 0) == 0
    act_at = spec.get("act", 0)
    events = spec.get("events", {})
    res = dict(name=spec["name"], samples=0, exact=0, maxdiff=0.0, state_diffs=0, s9_diffs=0, ret_diffs=0, s25_diffs=0, first=None)
    outE = []; s9log = []; nlog = []
    for b in range(nblk):
        if b == act_at: want = True
        for op in events.get(b, []):
            if op[0] == "stop": h.vc(o, 6, f2u(op[1])); m.slot6(op[1]); want = False
            elif op[0] == "act": want = True
            elif op[0] == "w":
                cfg["w"] = op[1]; h.cfg[o]["w"] = op[1]
                e.w32(o + 0x10, f2u(F(1.0 - op[1]))); e.w32(o + 0x14, f2u(F(op[1]))); m.dry = F(1.0 - op[1]); m.wet = F(op[1])
            elif op[0] == "ret": cfg["ret"] = op[1]; h.cfg[o]["ret"] = op[1]
            elif op[0] == "gain": cfg["gain"] = op[1]; h.cfg[o]["gain"] = op[1]
            elif op[0] == "hpf": e.call(0x106c7c, o, 1 if op[1] else 0, f2u(op[2])); m.set_post_hpf(op[1], op[2])
            elif op[0] == "s21": h.vc(o, 21, op[1]); m.slot21(op[1])
        s9e = h.vc(o, 9); s9m = m.slot9(); s9log.append(s9e)
        if s9e != s9m: res["s9_diffs"] += 1
        if want and s9e == 0:
            h.vc(o, 5, 0, 1); m.slot5(0.0, 1)
            if nine_d: h.vc(o, 7, 0); m.slot7()
            else: h.vc(o, 8); m.slot8()
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        n25 = len(h.s25); nm25 = len(mlog)
        e.set_floats(bl, xL); e.set_floats(br, xR)
        r = h.vc(o, 18, bl, br, N)
        oL = e.floats(bl, N); oR = e.floats(br, N)
        mL = list(xL); mR = list(xR); rm = m.slot18(mL, mR, N)
        if (r & 0xffffffff) != (rm & 0xffffffff): res["ret_diffs"] += 1
        el = [(c["n"], bits(c["inL"]), bits(c["inR"])) for c in h.s25[n25:]]
        if el != mlog[nm25:]: res["s25_diffs"] += 1
        nlog.append([c[0] for c in el])
        outE.append((oL, oR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["exact"] += 1
            else:
                res["maxdiff"] = max(res["maxdiff"], abs(a_ - b_))
                if res["first"] is None: res["first"] = ("block %d" % b, a_, b_)
        dd = sdiff(emu_state(e, o), model_state(m))
        if dd:
            res["state_diffs"] += 1
            if res["first"] is None: res["first"] = ("state after block %d" % b, dd[:3])
    blob = b"".join(pack(l) + pack(r_) for l, r_ in outE)
    res["sha"] = sha(blob)[:16]
    res["ok"] = (res["exact"] == res["samples"] and not res["state_diffs"] and not res["s9_diffs"] and not res["ret_diffs"]
                 and not res["s25_diffs"])
    res["n_first"] = nlog[:6]; res["s9_first"] = s9log[:8]
    if keep: res["_out"] = outE; res["_in"] = (L, R); res["_n"] = nlog; res["_s9"] = s9log
    return res, blob


def stub_matrix(quick=False):
    cases = []
    base_ev = {60: [("w", 0.3)], 120: [("stop", 1.0)], 150: [("act",)], 175: [("w", 0.8)]}
    for fs in (44100, 48000):
        for mode in (0, 1):
            for hpf in (False, True):
                for s22 in (0, 1):
                    cases.append(dict(name="m%d_%s_s22=%d_fs%d" % (mode, "hpf" if hpf else "nohpf", s22, fs), fs=fs, mode=mode, hpf=hpf,
                                      s22=s22, events=base_ev, nblk=200))
    if not quick:
        for sig in ("dc", "impulse", "sine", "tiny"):
            for mode in (0, 1):
                for hpf in (False, True):
                    cases.append(dict(name="%s_m%d_%s" % (sig, mode, "hpf" if hpf else "nohpf"), sig=sig, mode=mode, hpf=hpf, s22=0,
                                      gain=1.0, events=base_ev, nblk=200))
        cases += [
            dict(name="act_mid_b37_m1_hpf", mode=1, act=37, events={90: [("stop", 1.0)], 130: [("act",)]}, nblk=200),
            dict(name="act_mid_b37_m0_s22=1", mode=0, s22=1, act=37, events={90: [("stop", 1.0)], 130: [("act",)]}, nblk=200),
            dict(name="ret1_always_m0", ret=1, events={100: [("stop", 1.0)]}, nblk=200),
            dict(name="ret_toggle_m1", mode=1, events={1: [("ret", 1)], 10: [("ret", 0)], 80: [("stop", 1.0)], 81: [("ret", 1)],
                                                         90: [("ret", 0)], 140: [("act",)]}, nblk=200),
            dict(name="stop_during_fadein_m0", events={1: [("stop", 1.0)], 30: [("act",)]}, nblk=200),
            dict(name="stop_during_fadein_m1_s22=1", mode=1, s22=1, events={1: [("stop", 1.0)], 30: [("act",)]}, nblk=200),
            dict(name="mix_change_during_fadein_m0", events={1: [("w", 0.2)], 2: [("w", 0.9)], 100: [("stop", 0.5)], 130: [("act",)]},
                 nblk=200),
            dict(name="stop_arg_0.5_m1", mode=1, events={50: [("stop", 0.5)], 80: [("act",)]}, nblk=200),
            dict(name="slot8_m0", nine_d=0, events={60: [("stop", 1.0)], 90: [("act",)]}, nblk=200),
            dict(name="slot8_m1", mode=1, nine_d=0, events={30: [("w", 0.4)], 60: [("stop", 1.0)], 90: [("act",)]}, nblk=200),
            dict(name="mode2", mode=2, events=base_ev, nblk=200),
            dict(name="mode3", mode=3, events=base_ev, nblk=200),
            dict(name="hpf_runtime_toggle", hpf=False, events={20: [("hpf", True, 10.0)], 60: [("hpf", False, 10.0)],
                                                                 100: [("hpf", True, 2.0)], 140: [("hpf", True, 30000.0)],
                                                                 150: [("stop", 1.0)], 160: [("act",)]}, nblk=200),
            dict(name="fc_clamp_low_2Hz", fc=2.0, sig="dc", gain=1.0, nblk=200),
            dict(name="fc_clamp_high_30k_fs48k", fs=48000, fc=30000.0, nblk=200),
            dict(name="inplace_slot21_0", events={0: [("s21", 0)]}, nblk=200),
            dict(name="w0_bypass_m1_hpf", mode=1, w=0.0, nblk=200),
            dict(name="gain_change_m1", mode=1, events={70: [("gain", -1.5)], 140: [("gain", 0.0)]}, nblk=200),
        ]
    return cases


# ===================================================================================================================== C3 mutants
def _patch(obj, name, fn):
    old = getattr(obj, name); setattr(obj, name, fn)
    return lambda: setattr(obj, name, old)


def _m_exact_ramp():
    def block(self, n):
        g = []; c0 = self.cur; rem = self.rem
        if n < 1: return g
        if self.state != 0:
            k = self.N - rem
            start = F(self.target - F(self.step * self.N))
            if n < rem:
                g = [F(start + F(self.step * (k + i))) for i in range(n)]
                self.cur = F(start + F(self.step * (k + n))); self.rem = rem - n; return g
            g = [F(start + F(self.step * (k + i))) for i in range(rem)]
            self.state = 0; self.rem = 0
        g += [self.target if g or self.state == 0 and rem else self.cur] * (n - len(g))
        self.cur = g[-1] if g else self.cur
        return g
    return _patch(EB.SmoothFloat, "block", block)


def _m_no_input_fade(): return _patch(EB.InOutGain, "input_fade", lambda self, cL, cR, n: None)


def _m_no_skip():
    orig = EB.EffectBase.slot5
    def slot5(self, a=0.0, honour_skip=1): return orig(self, a, 0)
    return _patch(EB.EffectBase, "slot5", slot5)


def _m_fused_mix():
    def mix(self, L, R, i0, cL, cR, n):
        if not self.copy: return
        if not self.trans:
            if self.cur == 1: self.sdry.set_target(self.c0); self.swet.set_target(self.c4)
            if self.cur == 2 and self.c8: self.swet.set_target(self.c4)
        d = self.sdry.block(n) if self.sdry.state else [self.sdry.cur] * n
        w = self.swet.block(n) if self.swet.state else [self.swet.cur] * n
        for k in range(n):
            L[i0 + k] = F(L[i0 + k] * d[k] + cL[k] * w[k]); R[i0 + k] = F(R[i0 + k] * d[k] + cR[k] * w[k])
        if self.trans and self.sin.state == 0 and self.sdry.state == 0 and self.swet.state == 0:
            self.cur = self.tgt; self.trans = 0
    return _patch(EB.InOutGain, "mix", mix)


def _m_instant_glide():
    orig = EB.InOutGain.mix
    def mix(self, L, R, i0, cL, cR, n):
        if not self.trans and self.cur == 1:
            self.sdry.snap(self.c0); self.swet.snap(self.c4)
        return orig(self, L, R, i0, cL, cR, n)
    return _patch(EB.InOutGain, "mix", mix)


def _m_hpf_no_ftz():
    def process(self, L, R, n):
        for ch, buf in ((0, L), (1, R)):
            v1, y1 = self.v1[ch], self.y1[ch]
            for j in range(n):
                v = F(buf[j]); o = F(F(F(self.b0 * v) + F(self.b1 * v1)) - F(self.a1 * y1)); buf[j] = o; v1 = v; y1 = o
            self.v1[ch], self.y1[ch], self.yp[ch] = v1, y1, y1
    return _patch(EB.IirHpf1stOrder, "process", process)


def _m_hpf_double():
    def coefs(self):
        w = math.tan(float(self.fc) * (math.pi / float(self.fs)))
        self.b0 = F(1.0 / (w + 1.0)); self.b1 = F(-self.b0); self.a1 = F(F(w - 1.0) / F(w + 1.0))
    return _patch(EB.IirHpf1stOrder, "coefs", coefs)


def _m_clamp_full_block():
    orig = EB.EffectBase.slot6
    def slot6(self, a=1.0):
        orig(self, a); self.clamp_armed = 0; self.clamp = 0
    return _patch(EB.EffectBase, "slot6", slot6)


MUTANTS = [("exact t/N ramp (no accumulation)", "m0_nohpf_s22=0_fs44100", _m_exact_ramp),
           ("no mode-1 input fade", "m1_nohpf_s22=0_fs44100", _m_no_input_fade),
           ("no +0xa8 activation skip", "m0_nohpf_s22=1_fs44100", _m_no_skip),
           ("single-rounding (fused) mix", "m0_nohpf_s22=0_fs44100", _m_fused_mix),
           ("dry/wet change applied at once", "m0_nohpf_s22=0_fs44100", _m_instant_glide),
           ("HPF without flush-to-zero", "tiny_m0_hpf", _m_hpf_no_ftz),
           ("HPF a1 in float, no 1/2pi*2pi", "m0_hpf_s22=0_fs44100", _m_hpf_double),
           ("no stop clamp (n stays 64)", "m0_nohpf_s22=1_fs44100", _m_clamp_full_block)]


# ===================================================================================================================== C4 real effects
def init_insert_like(x, idx, s22, hpf):
    """Insert-processor ctor steps for one effect (F141): slot 22(e, 0) unless Insert index 7; 0x106c7c(e, 1, 10) for the HPF set;
    then InsertFxProcessor slot 52 defaults for the index."""
    e, o = x.e, x.o
    if s22 is not None: e.vcall(o, 22, s22)
    if hpf: e.call(0x106c7c, o, 1, f2u(10.0))
    cont = e.malloc(0x100); arr = e.malloc(40)
    for i in range(10): e.w32(arr + 4 * i, o if i == idx else 0)
    e.w32(cont + 0x80, arr); e.w32(cont + 0x88, 10)
    x.s14 = []
    e.call(H7.CONTAINER_DEFAULTS, cont, idx)
    return list(x.s14)


def build_real(kind):
    """Returns (x: emulated object wrapper with .e .o, model EffectBase, per-block feed(x, model) or None, label)."""
    if kind == "delay":
        import H039_insert_delay_model as H39
        import insert_delay as MD
        x = H39.EmuDelay(defaults=False)
        s14 = init_insert_like(x, 4, 0, False)
        md = MD.InsertDelay(); md.insert_defaults()
        def s25(eb, L, R, n):
            oL, oR = md.process(L, R); L[:] = oL; R[:] = oR; eb.dry = md.dry; eb.wet = md.wet; return 0
        def s26(eb): md.update_mix(); eb.dry = md.dry; eb.wet = md.wet
        def s27(eb): md.reset(); return 0
        m = EB.EffectBase(mode=1, slot25=s25, slot26=s26, slot27=s27); m.slot22(0)
        return x, m, md, s14
    if kind == "compressor":
        import H040_compressor_model as H40
        import compressor as MC
        x = H40.EmuComp(defaults=False)
        s14 = init_insert_like(x, 7, None, False)           # Insert ctor never calls slot 22 for index 7 (F141): +0xa8 stays 1
        mc = H40.Model(); mc.insert_defaults()
        def s25(eb, L, R, n):
            oL, oR = mc.process(L, R); L[:] = oL; R[:] = oR; eb.dry = mc.dry; eb.wet = mc.wet; return 0
        def s26(eb): mc.update_mix(); eb.dry = mc.dry; eb.wet = mc.wet
        def s27(eb): mc.reset(); return 0
        m = EB.EffectBase(mode=0, slot25=s25, slot26=s26, slot27=s27)
        return x, m, mc, s14
    if kind == "flanger":
        import H034_flanger_model as H34
        import flanger as MF
        x = H34.EmuFlanger(defaults=False)
        s14 = init_insert_like(x, 1, 0, True)
        mf = MF.Flanger()
        for idx, u in s14: mf.set_param(idx, u2f(u))
        def s25(eb, L, R, n):
            r = mf.process(L, R); eb.dry = mf.dry; eb.wet = mf.wet; return r
        def s26(eb): eb.wet = mf.mix; eb.dry = F(1.0)
        def s27(eb): return mf.reset()
        m = EB.EffectBase(mode=0, slot25=s25, slot26=s26, slot27=s27); m.slot22(0); m.set_post_hpf(True, 10.0)
        return x, m, mf, s14
    raise ValueError(kind)


def run_real_case(kind, name, sig="noise", nblk=200, params=(), events=None, feed_bpm=None, keep=False):
    x, m, mm, s14 = build_real(kind)
    e, o = x.e, x.o
    for idx, v in params: e.vcall(o, 14, idx, f2u(v)); mm.set_param(idx, v)
    L, R = signal(sig, nblk, seed=7)
    bl = e.malloc(256); br = e.malloc(256)
    res = dict(name=name, samples=0, exact=0, maxdiff=0.0, state_diffs=0, s9_diffs=0, first=None)
    outE = []; want = True; events = events or {}
    for b in range(nblk):
        for op in events.get(b, []):
            if op[0] == "stop": e.vcall(o, 6, f2u(op[1])); m.slot6(op[1]); want = False
            elif op[0] == "act": want = True
            elif op[0] == "p": e.vcall(o, 14, op[1], f2u(op[2])); mm.set_param(op[1], op[2])
        s9e = e.vcall(o, 9)[0]; s9m = m.slot9()
        if s9e != s9m: res["s9_diffs"] += 1
        if want and s9e == 0:
            e.vcall(o, 5, 0, 1); m.slot5(0.0, 1); e.vcall(o, 7, 0); m.slot7()
        if feed_bpm is not None: e.vcall(o, 14, 7, f2u(feed_bpm)); mm.set_param(7, feed_bpm)
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        e.set_floats(bl, xL); e.set_floats(br, xR)
        e.vcall(o, 18, bl, br, N)
        oL = e.floats(bl, N); oR = e.floats(br, N)
        mL = list(xL); mR = list(xR); m.slot18(mL, mR, N)
        outE.append((oL, oR, mL, mR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["exact"] += 1
            else:
                res["maxdiff"] = max(res["maxdiff"], abs(a_ - b_))
                if res["first"] is None: res["first"] = ("block %d" % b, a_, b_)
        dd = sdiff(emu_state(e, o), model_state(m))
        if dd:
            res["state_diffs"] += 1
            if res["first"] is None: res["first"] = ("state after block %d" % b, dd[:3])
    blob = b"".join(pack(a) + pack(c) for a, c, _, _ in outE)
    res["sha"] = sha(blob)[:16]
    res["ok"] = res["exact"] == res["samples"] and not res["state_diffs"] and not res["s9_diffs"]
    if keep: res["_out"] = outE; res["_in"] = (L, R)
    return res, blob


# ===================================================================================================================== C4 extension table
def _adapt(mm, s26law, proc="process"):
    """Wrap a per-effect slot-25 model: process(L, R) returning new lists / (L, R) / an int (in place)."""
    pf = getattr(mm, proc)
    def s25(eb, L, R, n):
        r = pf(L, R)
        ret = 0
        if isinstance(r, tuple) and len(r) == 2 and isinstance(r[0], list):
            L[:] = [F(x) for x in r[0]]; R[:] = [F(x) for x in r[1]]
        elif isinstance(r, int): ret = r
        d, w = s26law(mm, after_process=True)
        if d is not None: eb.dry = d; eb.wet = w
        return ret
    def s26(eb):
        d, w = s26law(mm, after_process=False)
        if d is not None: eb.dry = d; eb.wet = w
    return s25, s26


def build_generic(kind, neutral27=False):
    """(e, o_eb, model EffectBase, per-effect model, per-block feed(blk) -> [(idx, v)]) for every effect with a slot-25 model.
    Emulated objects are built by each effect's own harness class, then put into the Insert (or Send) processor ctor state of F141:
    slot 22(e, 0) except Insert index 7, 0x106c7c(e, on, 10) on only for Chorus/Flanger/MMF/LoFi/Distortion/Phaser."""
    keep_dw = lambda mm, after_process: (mm.dry, mm.wet) if mm.dry is not None else (None, None)
    def p5law(mm, after_process):                         # slot 26 = wet Mixratio (param 5), dry 1 - Mixratio (LoFi, MMF)
        v = mm.params[5].get(); return F(F(1.0) - v), v
    bpm = lambda b: [(7, 120.0)]
    if kind == "chorus":
        import H033_chorus_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 0, 1, 0
        law = lambda mm, after_process: (F(1.0), mm.mix); feed = bpm; s27 = mm.reset
    elif kind == "flanger":
        import H034_flanger_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 0, 1, 0
        law = lambda mm, after_process: (F(1.0), mm.mix); feed = bpm; s27 = mm.reset
    elif kind == "peq":
        import H026_peq_model as X, peq as MP; x = X.EmuPEQ(); mm = MP.PEQ(); mm.insert_defaults(); eo = x.o; mode, hpf, s22 = 0, 0, 0
        law = lambda mm, after_process: (F(0.0), F(1.0)); feed = None; s27 = mm.reset   # slot 27 0x10a7ec (H076)
    elif kind == "mmf":
        import H023_mmf_model as X, mmf as MM; x = X.EmuMMF(); mm = MM.MMF(); mm.insert_defaults(); eo = x.o; mode, hpf, s22 = 0, 1, 0
        law = p5law; feed = None; s27 = mm.reset                                # slot 27 0x107fa8 (H076)
    elif kind == "delay":
        import H039_insert_delay_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 1, 0, 0
        law = keep_dw; feed = bpm; s27 = mm.reset
        mm_upd = mm.update_mix
    elif kind == "lofi":
        import H021_lofi_model as X, lofi as ML; x = X.EmuLoFi(); mm = ML.LoFi(); mm.insert_defaults(); eo = x.o; mode, hpf, s22 = 0, 1, 0
        law = p5law; feed = None; s27 = mm.reset                                # slot 27 0xfb5a4 (H076)
    elif kind == "distortion":
        import H035_distortion_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 0, 1, 0
        law = keep_dw; feed = None; s27 = mm.reset
    elif kind == "compressor":
        import H040_compressor_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 0, 0, None
        law = keep_dw; feed = None; s27 = mm.reset
    elif kind == "phaser":
        import H028_phaser_model as X, phaser as MPh; x = X.EmuPhaser(); mm = MPh.Phaser(); mm.insert_defaults(); eo = x.o
        mode, hpf, s22 = 0, 1, 0
        def law(mm, after_process):                     # slot 26 0x10cb48: mix = Mixratio; wet = mix, dry = 1 - mix
            if not after_process: mm.mix = mm.p[5].get(); mm.wet = mm.mix; mm.dry = F(F(1.0) - mm.mix)
            return mm.dry, mm.wet
        feed = bpm; s27 = mm.reset
    elif kind == "ducker":
        import H041_ducker_model as X; x, mm = X.new_pair(); eo = x.o; mode, hpf, s22 = 0, 0, 0
        law = lambda mm, after_process: (0.0, 1.0); s27 = mm.reset
        def feed(b):
            out = [(7, 120.0)]
            if b % 37 == 5: out += [(8, 1.0), (9, float(b % 50))]
            return out
    elif kind == "send_delay":
        import H043_send_delay_model as X; x, mm = X.new_pair(); eo = x.eb; mode, hpf, s22 = 1, 0, 0
        law = keep_dw                                    # slot 26 copies the stored +0x6a4/+0x6a8 (written in slot 25 only)
        feed = bpm; s27 = mm.reset
    elif kind == "send_reverb":
        import H005_send_reverb_model as X; x, mm = X.new_pair(activate=False); eo = x.o; mode, hpf, s22 = 1, 0, 0
        def law(mm, after_process):
            if not after_process: mm.slot32()
            return mm.eb_dry, mm.eb_wet
        feed = None; s27 = mm.reset
    elif kind == "send_compressor":
        import H040_compressor_model as X; x, mm = X.new_pair(send=True); eo = x.o; mode, hpf, s22 = 0, 0, 0
        law = keep_dw; feed = None; s27 = mm.reset
    else:
        raise ValueError(kind)
    e = x.e
    if neutral27:                                         # alternative test: guest vtable copy with slot 27 = the EffectBase base slot 27
        vt = e.u32(eo); nv = e.malloc(4 * 48, "vtable copy (slot 27 neutralised)")
        for k in range(46): e.w32(nv + 4 * k, e.u32(vt - 8 + 4 * k))
        e.w32(nv + 8 + 4 * 27, e.u32(H11.EB_VT + 4 * 27)); e.w32(eo, nv + 8); s27 = None
    if s22 is not None: e.vcall(eo, 22, s22)
    else: e.vcall(eo, 22, 1)
    e.call(0x106c7c, eo, hpf, f2u(10.0))
    if kind == "delay":
        s26law = lambda mm, after_process: (mm_upd() if not after_process else None) or (mm.dry, mm.wet)
    elif kind in ("compressor", "send_compressor"):
        s26law = lambda mm, after_process: (mm.update_mix() if not after_process else None) or (mm.dry, mm.wet)
    else:
        s26law = law
    s25, s26 = _adapt(mm, s26law, "process_send" if kind == "send_compressor" else "process")
    m = EB.EffectBase(mode=mode, slot25=s25, slot26=s26, slot27=(lambda eb: s27()) if s27 else None)
    m.slot22(1 if s22 is None else s22); m.set_post_hpf(bool(hpf), 10.0)
    return e, eo, m, mm, feed


DRY_SHA = [None]
EXT_KINDS = ["chorus", "flanger", "peq", "mmf", "delay", "lofi", "distortion", "compressor", "phaser", "ducker",
             "send_delay", "send_reverb", "send_compressor"]


EXT_PARAMS = {"chorus": ((5, 0.7),), "flanger": ((5, 0.7), (4, 0.5)), "peq": ((1, 0.8), (4, 0.2)), "delay": ((5, 0.5), (0, 0.05), (1, 0.5)),
              "phaser": ((5, 0.6),), "compressor": ((0, 0.2), (1, 0.8), (5, 1.0), (4, 0.7)),
              "send_compressor": ((0, 0.2), (1, 0.8), (5, 1.0), (4, 0.7)), "send_delay": ((0, 0.02),)}


def run_generic(kind, sig="noise", nblk=200, events=None, neutral27=False):
    e, o, m, mm, feed = build_generic(kind, neutral27)
    for idx, v in EXT_PARAMS.get(kind, ()): e.vcall(o, 14, idx, f2u(v)); mm.set_param(idx, v)
    L, R = signal(sig, nblk, seed=3)
    bl = e.malloc(256); br = e.malloc(256)
    res = dict(name=kind, samples=0, exact=0, maxdiff=0.0, state_diffs=0, s9_diffs=0, first=None, first_block=None)
    want = True; events = events or {}; blob = b""
    for b in range(nblk):
        for op in events.get(b, []):
            if op[0] == "stop": e.vcall(o, 6, f2u(op[1])); m.slot6(op[1]); want = False
            elif op[0] == "act": want = True
        s9e = e.vcall(o, 9)[0]; s9m = m.slot9()
        if s9e != s9m: res["s9_diffs"] += 1
        if want and s9e == 0:
            e.vcall(o, 5, 0, 1); m.slot5(0.0, 1); e.vcall(o, 7, 0); m.slot7()
        if feed:
            for idx, v in feed(b): e.vcall(o, 14, idx, f2u(v)); mm.set_param(idx, v)
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
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
        dd = sdiff(emu_state(e, o), model_state(m))
        if dd:
            res["state_diffs"] += 1
            if res["first"] is None: res["first"] = ("state after block %d" % b, dd[:3])
    res["sha"] = sha(blob)[:16]
    res["ok"] = res["exact"] == res["samples"] and not res["state_diffs"] and not res["s9_diffs"]
    return res, blob


# ===================================================================================================================== C5 processor
def proc_rig(h, eff_by_idx, nine_d=1):
    """As the H011 stand-in InsertFxProcessor (fields hand-set; real setFxType / processBlock / MuteSmoother)."""
    e = h.e
    p = e.malloc(0x148); arr = e.malloc(40)
    for k in range(10): e.w32(arr + 4 * k, eff_by_idx.get(k, 0))
    e.w32(p, H11.PROC_VT["InsertFxProcessor"]); e.w32(p + 0x80, arr); e.w32(p + 0x84, 10); e.w32(p + 0x88, 10)
    e.wr(p + 0x9c, bytes([0, nine_d, 0])); e.w32(p + 0xa4, 0xffffffff); e.w32(p + 0xa8, 0xffffffff)
    dd = e.malloc(8); e.w32(dd, e.malloc(256)); e.w32(dd + 4, e.malloc(256)); e.w32(p + 0xb8, dd)
    ms = e.malloc(0x20); e.call(0xe7fd8, ms, 128, 0); e.w32(p + 0x144, ms)
    buf = e.malloc(0x100); ch = e.malloc(8); Lb = e.malloc(256); Rb = e.malloc(256)
    e.w32(ch, Lb); e.w32(ch + 4, Rb); e.w32(buf + 0xc, ch)
    return p, buf, Lb, Rb


def run_processor(schedule, nblk=200, sig="noise", comp_params=(), keep=False):
    """Real processor: stub A (index 5, gain 0.5, HPF on), stub B (index 3, gain 0.25, mode 1, HPF on), real InsertFxCompressor
    (index 7, +0xa8 = 1). schedule = {block: index} for setFxType before that block."""
    import H040_compressor_model as H40
    h = H11.Host(); e = h.e
    A = make_stub(h, "A", gain=0.5); B = make_stub(h, "B", mode=1, gain=0.25)
    for o in (A, B): h.vc(o, 22, 0); e.call(0x106c7c, o, 1, f2u(10.0))
    C = e.malloc(H40.SIZE_I, "InsertFxCompressor"); e.call(H40.CTOR_I, C, 44100, 64); h.objs[C] = "C"
    p, buf, Lb, Rb = proc_rig(h, {5: A, 3: B, 7: C})
    e.call(H7.CONTAINER_DEFAULTS, p, 7)
    for idx, v in comp_params: e.vcall(C, 14, idx, f2u(v))
    # model side
    mc = H40.Model(); mc.insert_defaults()
    for idx, v in comp_params: mc.set_param(idx, v)
    def stub_model(gain, mode):
        def s25(eb, L, R, n):
            for k in range(n): L[k] = F(gain * L[k]); R[k] = F(gain * R[k])
            return 0
        def s26(eb): eb.dry = F(0.0); eb.wet = F(1.0)
        m = EB.EffectBase(mode=mode, slot25=s25, slot26=s26); m.slot22(0); m.set_post_hpf(True, 10.0); return m
    def c25(eb, L, R, n):
        oL, oR = mc.process(L, R); L[:] = oL; R[:] = oR; eb.dry = mc.dry; eb.wet = mc.wet; return 0
    def c26(eb): mc.update_mix(); eb.dry = mc.dry; eb.wet = mc.wet
    def c27(eb): mc.reset(); return 0
    mC = EB.EffectBase(mode=0, slot25=c25, slot26=c26, slot27=c27)        # +0xa8 left at 1
    P = EB.InsertProcessor({5: stub_model(0.5, 0), 3: stub_model(0.25, 1), 7: mC})
    L, R = signal(sig, nblk, seed=5)
    res = dict(samples=0, exact=0, maxdiff=0.0, idx_diffs=0, first=None)
    outE = []; cur = []
    for b in range(nblk):
        if b in schedule:
            e.call(0x11735c, p, schedule[b] & 0xffffffff); P.set_fx_type(schedule[b])
        xL = L[N * b:N * b + N]; xR = R[N * b:N * b + N]
        e.set_floats(Lb, xL); e.set_floats(Rb, xR)
        e.call(0x116860, p, buf)
        oL = e.floats(Lb, N); oR = e.floats(Rb, N)
        mL = list(xL); mR = list(xR); P.process_block(mL, mR, N)
        ce = e.u32(p + 0xa4); ce = ce - (1 << 32) if ce & 0x80000000 else ce
        cur.append(ce)
        if ce != P.cur: res["idx_diffs"] += 1
        outE.append((oL, oR, mL, mR))
        for a_, b_ in zip(oL + oR, mL + mR):
            res["samples"] += 1
            if f2u(a_) == f2u(b_): res["exact"] += 1
            else:
                res["maxdiff"] = max(res["maxdiff"], abs(a_ - b_))
                if res["first"] is None: res["first"] = ("block %d" % b, a_, b_)
    blob = b"".join(pack(a) + pack(c) for a, c, _, _ in outE)
    res["sha"] = sha(blob)[:16]; res["cur"] = cur
    res["ok"] = res["exact"] == res["samples"] and not res["idx_diffs"]
    if keep: res["_out"] = outE; res["_in"] = (L, R)
    return res, blob


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H044"))
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = sp16img.Image()
    fu = lambda va: u2f(im.u32(va))
    dd = lambda va: struct.unpack("<d", struct.pack("<II", im.u32(va), im.u32(va + 4)))[0]

    # ------------------------------------------------------------------------------------------------ C1 constants
    P("== C1 constants used by the wrapper laws (read from the 1.60 file)")
    consts = {"fade ms 0x8420a8": fu(0x8420a8), "0.001f @0x1063b8 (slot 5 skip)": fu(0x1063b8), "0.001f @0x105d1c (slot 6 clamp)": fu(0x105d1c),
              "0.001f @0xf5a44 (setSmoothingTime)": fu(0xf5a44), "HPF fc floor 0x83bc40": fu(0x83bc40), "pi @0xe1b18": dd(0xe1b18),
              "1/2pi @0xe1b20": dd(0xe1b20), "2pi @0xe1b28": dd(0xe1b28)}
    for k, v in consts.items(): P("  %-40s %r" % (k, v))
    check(consts["fade ms 0x8420a8"] == EB.K_FADE_MS and consts["0.001f @0x1063b8 (slot 5 skip)"] == EB.K_MILLI and
          consts["0.001f @0x105d1c (slot 6 clamp)"] == EB.K_MILLI and consts["0.001f @0xf5a44 (setSmoothingTime)"] == EB.K_MILLI and
          consts["HPF fc floor 0x83bc40"] == 5.0 and consts["pi @0xe1b18"] == EB.D_PI and consts["1/2pi @0xe1b20"] == EB.D_INV_2PI and
          consts["2pi @0xe1b28"] == EB.D_2PI, "model constants equal the 1.60 literals (3.3333333 ms, 0.001f, 5 Hz floor, pi, 1/2pi, 2pi)")
    J["c1_consts"] = consts
    P("  fade length trunc(f32(f32(3.3333333*0.001)*fs)): 44100 -> %d, 48000 -> %d, 96000 -> %d" %
      (EB.fade_samples(44100), EB.fade_samples(48000), EB.fade_samples(96000)))
    # slot-31 records for modes 0..3 (emulated slot 31 vs model)
    P("\n== C1 gate records (slot 31 0x105d78) after the real ctor + slot 31, dry 0.3 / wet 0.7, modes 0..3, vs model")
    rec_ok = True; rec_tab = {}
    for mode in (0, 1, 2, 3):
        h = H11.Host(); e = h.e; o = make_stub(h, "R", mode=mode, w=0.7)
        e.w32(o + 0x10, f2u(F(0.3))); e.w32(o + 0x14, f2u(F(0.7)))
        e.vcall(o, 31)
        w = [e.u32(o + 0x18 + 4 * i) for i in range(30)]
        m = EB.EffectBase(mode=mode); m.dry = F(0.3); m.wet = F(0.7); m.slot31()
        mw = []
        for r in m.recs:
            for i, v in enumerate(r):
                mw.append(None if v is None else (v if i % 2 == 0 else f2u(v)))
        ok = all(mv is None or mv == ev for mv, ev in zip(mw, w))
        rec_ok &= ok
        txt = " | ".join(",".join(("%d" % w[6 * r + 2 * k]) + ":" + ("%.2g" % u2f(w[6 * r + 2 * k + 1])) for k in range(3)) for r in range(5))
        rec_tab[mode] = txt
        P("  mode %d  R0..R4 (in-mode:gain, dry, wet): %s   model %s" % (mode, txt, "==" if ok else "DIFFERS"))
    check(rec_ok, "model slot-31 records equal the emulated records for modes 0, 1, 2 and 3 (3: records left at ctor values)")
    J["c1_records"] = rec_tab
    # ctor state and HPF coefficients at activation
    P("\n== C1 ctor state + HPF coefficients 0xe1aa0 after slot 5 (fc via 0x106c7c), real vs model")
    coef_ok = True; ctor_ok = True; coef_tab = []
    for fs in (44100, 48000):
        for fc in (10.0, 2.0, 5.0, 20.0, 1000.0, 30000.0):
            h = H11.Host(); e = h.e; o = make_stub(h, "H", fs=fs)
            m = EB.EffectBase(fs=fs)
            if fc == 10.0:
                d0 = sdiff(emu_state(e, o), model_state(m)); ctor_ok &= not d0
                if d0: P("  ctor state differs fs %d: %s" % (fs, d0[:3]))
            e.call(0x106c7c, o, 1, f2u(fc)); m.set_post_hpf(True, fc)
            e.vcall(o, 5, 0, 1); m.slot5(0.0, 1)
            hp = o + 0xd8
            ce = (e.u32(hp + 0xc), e.u32(hp + 0x28), e.u32(hp + 0x2c), e.u32(hp + 0x34))
            cm = (f2u(m.hpf.fc), f2u(m.hpf.b0), f2u(m.hpf.b1), f2u(m.hpf.a1))
            coef_ok &= ce == cm
            coef_tab.append((fs, fc, u2f(ce[0]), u2f(ce[1]), u2f(ce[3]), ce == cm))
    for t in coef_tab: P("  fs %d fc req %-8g -> fc %-8g b0 %.9g a1 %.9g  model %s" % (t[0], t[1], t[2], t[3], t[4], "==" if t[5] else "DIFFERS"))
    check(ctor_ok, "model ctor state (gate, 3 SmoothFloats N/1/N, 2 SignalGates, HPF fc/coefs, skip/clamp, +0xcc/+0xcd) equals the "
                   "emulated EffectBase ctor at 44100 and 48000")
    check(coef_ok, "HPF fc clamp max(5, min(fc, fs/2)) and coefficients b0 = 1/(w+1), b1 = -b0, a1 = (w-1)/(w+1), w = tan(pi fc/fs) "
                   "bit-equal to the real 0xe1aa0 for 12 fc/fs pairs")
    J["c1_coefs"] = coef_tab

    P("\n== C1 SmoothFloat ramp law 0xf55a4 / 0xf5668 (value_t = f32(value_{t-1} + f32(f32(1 - 0) * f32(1/N))), first sample = start)")
    for fs in (44100, 48000):
        sf = EB.SmoothFloat(fs); sf.set_time(EB.K_FADE_MS); sf.snap(0.0); sf.set_target(1.0); g = sf.block(sf.N + 3)
        dev = max(abs(g[t] - t / sf.N) for t in range(sf.N))
        P("  fs %d: N %d, g[0] %.9g g[1] %.9g g[N/2] %.9g g[N-1] %.9g g[N] %.9g; max |g_t - t/N| (t < N) %.3g" % (
            fs, sf.N, g[0], g[1], g[sf.N // 2], g[sf.N - 1], g[sf.N], dev))
        J.setdefault("c1_ramp", {})[fs] = dict(N=sf.N, dev=dev, last=g[sf.N - 1])
    P("\n== C1 gate modes 0..3 (ctor arg 4): real slot 18, stub out = 0.5*in, wet 1, DC 0.5 / -0.25, no HPF, slot 6 at sample 256")
    prof = {}
    for mode in (0, 1, 2, 3):
        r, _ = run_stub_case(dict(name="prof%d" % mode, mode=mode, hpf=False, sig="dc", nblk=10, events={4: [("stop", 1.0)]}), keep=True)
        oL = [x for blk in r["_out"] for x in blk[0]]
        pts = (0, 1, 73, 146, 147, 200, 256, 256 + 73, 256 + 146, 256 + 147, 600)
        prof[mode] = ["%.4f" % (oL[i] / 0.5) for i in pts]
        P("  mode %d (%s) out/in at %s = %s; slot 9 per block %s" % (mode, "OK " if r["ok"] else "BAD", list(pts), prof[mode], r["_s9"]))
        check(r["ok"], "mode %d DC profile: model == real slot 18 bit-exactly" % mode)
    J["c1_mode_profiles"] = prof

    # ------------------------------------------------------------------------------------------------ C3 stub matrix
    P("\n== C3 stub effect through the real slot 18 vs effectbase.EffectBase (same injected slot 25/26), >= 200 blocks per case")
    cases = stub_matrix(a.quick); allblob = b""; rows = []
    for spec in cases:
        r, blob = run_stub_case(spec); allblob += blob; rows.append(r)
        P("  %-34s %s samples %6d exact %6d maxdiff %.3g state/s9/ret/s25 diffs %d/%d/%d/%d sha %s n0 %s%s" % (
            r["name"], "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["state_diffs"], r["s9_diffs"], r["ret_diffs"],
            r["s25_diffs"], r["sha"], r["n_first"][:4], "" if r["ok"] else "  first %s" % (r["first"],)))
    nok = sum(1 for r in rows if r["ok"])
    check(nok == len(rows), "stub matrix: %d/%d cases bit-exact (output, slot-9/18 returns, slot-25 n and input, gate/skip/HPF state "
                             "after every block)" % (nok, len(rows)))
    J["c3"] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]
    J["c3_sha_all"] = sha(allblob)
    P("  all C3 outputs sha256 %s (%d cases, %d samples)" % (sha(allblob), len(rows), sum(r["samples"] for r in rows)))
    open(os.path.join(a.out, "c3_stub_outputs.f32"), "wb").write(allblob)

    # ------------------------------------------------------------------------------------------------ C3 alternatives (mutants)
    P("\n== C3 alternative laws (model mutants) on the stub cases they should affect; each must FAIL against the real slot 18")
    mut_rows = []
    for mname, case_name, patch in MUTANTS:
        spec = next(c for c in stub_matrix(False) if c["name"] == case_name)
        undo = patch()
        try:
            r, _ = run_stub_case(spec)
        finally:
            undo()
        out_same = r["exact"] == r["samples"]
        mut_rows.append((mname, case_name, r["ok"], r["exact"], r["samples"], r["maxdiff"], out_same))
        P("  %-32s on %-24s -> %s exact %d/%d maxdiff %.3g state-diff blocks %d" % (
            mname, case_name, "matches (!)" if r["ok"] else ("output identical, state differs" if out_same else "refuted"), r["exact"],
            r["samples"], r["maxdiff"], r["state_diffs"]))
    check(all(not x[6] for x in mut_rows if not x[0].startswith("no stop clamp")) and all(not x[2] for x in mut_rows),
          "every alternative law except 'no stop clamp' is refuted on the output by the real slot 18; 'no stop clamp' gives the same "
          "output (the clamp ends exactly when the 147-sample stop fade ends) and is refuted only by the +0xb4/+0xb8 state")
    J["c3_mutants"] = mut_rows

    # ------------------------------------------------------------------------------------------------ C4 real effects
    P("\n== C4 real effects through the real slot 18 vs EffectBase model wrapping the per-effect slot-25 models")
    real = [("delay", "InsertFxDelay mode 1, defaults + mix 0.5", "noise", ((5, 0.5),), {80: [("stop", 1.0)], 110: [("act",)]}, None),
            ("delay", "InsertFxDelay mode 1, mix 0.5 fb 0.6 t 0.1", "impulse", ((5, 0.5), (1, 0.6), (0, 0.1)),
             {50: [("p", 5, 0.9)], 120: [("stop", 1.0)], 140: [("act",)]}, None),
            ("compressor", "InsertFxCompressor +0xa8=1, defaults", "noise", (), {100: [("stop", 1.0)], 130: [("act",)]}, None),
            ("compressor", "InsertFxCompressor +0xa8=1, T 0.2 R 0.8 mix 1 gain 0.7", "sine",
             ((0, 0.2), (1, 0.8), (5, 1.0), (4, 0.7), (2, 0.1), (3, 0.2)), {100: [("stop", 1.0)], 130: [("act",)]}, None),
            ("flanger", "Flanger HPF on, defaults + mix 1", "noise", ((5, 1.0),), {90: [("p", 5, 0.4)], 120: [("stop", 1.0)], 150: [("act",)]}, 120.0)]
    if a.quick: real = real[::2]
    rrows = []; rblob = b""; keepc = {}
    for kind, name, sig, prm, ev, bpm in real:
        r, blob = run_real_case(kind, name, sig=sig, params=prm, events=ev, feed_bpm=bpm, keep=True); rblob += blob; rrows.append(r)
        keepc[name] = r
        P("  %-52s %s samples %6d exact %6d maxdiff %.3g state/s9 diffs %d/%d sha %s%s" % (
            name, "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["state_diffs"], r["s9_diffs"], r["sha"],
            "" if r["ok"] else "  first %s" % (r["first"],)))
    nok4 = sum(1 for r in rrows if r["ok"])
    check(nok4 == len(rrows), "composition: %d/%d real-effect cases bit-exact (activation, stop and re-activation included)" % (nok4, len(rrows)))
    J["c4"] = [{k: v for k, v in r.items() if not k.startswith("_")} for r in rrows]
    open(os.path.join(a.out, "c4_real_outputs.f32"), "wb").write(rblob)

    P("\n== C4 extension: every effect with a slot-25 model, own harness builder, Insert/Send ctor state (F141), activation at block 0, "
      "slot 6 at block 120, re-activation at block 150, 200 blocks of noise")
    trows = []; tblob = b""
    Ld, Rd = signal("noise", 200, seed=3); DRY_SHA[0] = sha(b"".join(pack(Ld[N * b:N * b + N]) + pack(Rd[N * b:N * b + N]) for b in range(200)))[:16]
    for kind in (EXT_KINDS if not a.quick else ["chorus", "lofi"]):
        try:
            r, blob = run_generic(kind, events={120: [("stop", 1.0)], 150: [("act",)]})
        except Exception as ex:                                          # report, do not stop the run
            r = dict(name=kind, ok=False, error="%s: %s" % (type(ex).__name__, ex)); blob = b""
        tblob += blob; trows.append(r)
        if "error" in r: P("  %-16s ERROR %s" % (kind, r["error"][:200])); continue
        P("  %-16s %s samples %6d exact %6d maxdiff %.3g first diff block %s state/s9 diffs %d/%d sha %s%s" % (
            kind, "OK " if r["ok"] else "BAD", r["samples"], r["exact"], r["maxdiff"], r["first_block"], r["state_diffs"], r["s9_diffs"],
            r["sha"], "" if r["ok"] else "  first %s" % (r["first"],)))
    for kind in ("peq", "mmf", "lofi"):
        r, _ = run_generic(kind, events={120: [("stop", 1.0)], 150: [("act",)]}, neutral27=True)
        P("  alternative (%s with its slot 27 replaced by the EffectBase base slot 27 in a guest vtable copy, model without reset): "
          "%s exact %d/%d maxdiff %.3g state diffs %d" % (kind, "OK " if r["ok"] else "BAD", r["exact"], r["samples"], r["maxdiff"], r["state_diffs"]))
        trows.append(dict(r, name=kind + "_slot27_neutralised"))
    main_rows = [r for r in trows if not r["name"].endswith("_neutralised")]
    J["c4_ext"] = trows
    P("  extension: %d/%d effects bit-exact end to end; dry-passthrough cases (output == input everywhere): %s" % (
        sum(1 for r in main_rows if r.get("ok")), len(main_rows), [r["name"] for r in main_rows if r.get("sha") == DRY_SHA[0]]))
    open(os.path.join(a.out, "c4_ext_outputs.f32"), "wb").write(tblob)

    # ------------------------------------------------------------------------------------------------ C5 processor
    P("\n== C5 real InsertFxProcessor setFxType/processBlock (stubs at 5 and 3, real InsertFxCompressor at 7) vs model InsertProcessor")
    sched = {0: 5, 30: 7, 70: 3, 110: 7, 150: 5, 170: -1, 185: 7}
    cp = ((0, 0.2), (1, 0.8), (5, 1.0), (4, 0.7))
    r5, blob5 = run_processor(sched, nblk=200, sig="sine", comp_params=cp, keep=True)
    P("  schedule (block: setFxType index) %s" % sched)
    P("  current index per block (real) changes at: %s" % [(b, c) for b, c in enumerate(r5["cur"]) if b == 0 or c != r5["cur"][b - 1]])
    P("  %s samples %d exact %d maxdiff %.3g index diffs %d sha %s%s" % ("OK " if r5["ok"] else "BAD", r5["samples"], r5["exact"],
                                                                           r5["maxdiff"], r5["idx_diffs"], r5["sha"],
                                                                           "" if r5["ok"] else " first %s" % (r5["first"],)))
    check(r5["ok"], "processor level: sequential FX changes 5 -> 7 -> 3 -> 7 -> 5 -> Off -> 7 through the real setFxType/processBlock "
                    "equal the model bit-exactly (old fades out, swap when slot 9 = 0, new fades in)")
    J["c5"] = {k: v for k, v in r5.items() if not k.startswith("_")}
    open(os.path.join(a.out, "c5_processor_outputs.f32"), "wb").write(blob5)

    # ------------------------------------------------------------------------------------------------ C6 H074 numbers
    P("\n== C6 H074: Insert COMPRESSOR (+0xa8 = 1) activation skip / stop clamp vs other inserts (+0xa8 = 0)")
    cr = keepc.get("InsertFxCompressor +0xa8=1, T 0.2 R 0.8 mix 1 gain 0.7") or rrows[-1]
    out = cr["_out"]; Lin = cr["_in"][0]
    oL = [x for blk in out for x in blk[0]]
    eq_dry = [i for i in range(len(oL)) if f2u(oL[i]) == f2u(Lin[i])]
    first_diff = next((i for i in range(len(oL)) if f2u(oL[i]) != f2u(Lin[i])), None)
    P("  activation at sample 0: output == input (bit-exact) for samples 0..%s; first differing sample %s" % (
        (first_diff - 1) if first_diff else None, first_diff))
    stop_s = 100 * N
    tail = [i - stop_s for i in range(stop_s, stop_s + 400) if f2u(oL[i]) != f2u(Lin[i])]
    P("  after slot 6 at sample %d: last sample that differs from the input = stop + %s; samples differing in [stop, stop+147): %d, "
      "in [stop+147, stop+400): %d" % (stop_s, max(tail) if tail else None, sum(1 for t in tail if t < 147), sum(1 for t in tail if t >= 147)))
    react = 130 * N
    fd2 = next((i for i in range(react, react + 400) if f2u(oL[i]) != f2u(Lin[i])), None)
    P("  re-activation at sample %d: first differing sample = +%s" % (react, (fd2 - react) if fd2 is not None else None))
    # comparison: same compressor with +0xa8 = 0 (model only, validated above) and a delay (+0xa8 = 0)
    import H040_compressor_model as H40
    mc = H40.Model(); mc.insert_defaults()
    for idx, v in ((0, 0.2), (1, 0.8), (5, 1.0), (4, 0.7), (2, 0.1), (3, 0.2)): mc.set_param(idx, v)
    def c25(eb, L, R, n):
        x1, x2 = mc.process(L, R); L[:] = x1; R[:] = x2; eb.dry = mc.dry; eb.wet = mc.wet; return 0
    def c26(eb): mc.update_mix(); eb.dry = mc.dry; eb.wet = mc.wet
    m0 = EB.EffectBase(slot25=c25, slot26=c26, slot27=lambda eb: mc.reset()); m0.slot22(0)
    Lr, Rr = cr["_in"]; o0 = []
    for b in range(200):
        if b == 100: m0.slot6(1.0)
        if b < 100 and m0.slot9() == 0: m0.slot5(0.0, 1); m0.slot7()
        xL = Lr[N * b:N * b + N]; xR = Rr[N * b:N * b + N]; mL = list(xL); mR = list(xR); m0.slot18(mL, mR, N); o0 += mL
    fd0 = next((i for i in range(len(o0)) if f2u(o0[i]) != f2u(Lin[i])), None)
    tail0 = [i - stop_s for i in range(stop_s, stop_s + 400) if f2u(o0[i]) != f2u(Lin[i])]
    P("  same compressor with +0xa8 = 0 (model): first differing sample %s; after stop last differing = stop + %s" % (fd0, max(tail0) if tail0 else None))
    fl = keepc.get("Flanger HPF on, defaults + mix 1")
    fdf = None
    if fl:
        fL = [x for blk in fl["_out"] for x in blk[0]]; fIn = fl["_in"][0]
        fdf = next((i for i in range(len(fL)) if f2u(fL[i]) != f2u(fIn[i])), None)
        ftail = [i - 120 * N for i in range(120 * N, 120 * N + 400) if f2u(fL[i]) != f2u(fIn[i])]
        P("  real Flanger (+0xa8 = 0): first sample differing from the input %s; after its slot 6 (block 120) last differing = stop + %s"
          % (fdf, max(ftail) if ftail else None))
    rmsd = math.sqrt(sum((oL[i] - Lin[i]) ** 2 for i in range(148, 295)) / 147)
    rms0 = math.sqrt(sum((o0[i] - Lin[i]) ** 2 for i in range(0, 147)) / 147)
    P("  rms(out - in): real compressor (+0xa8 = 1) samples 0..146 = 0, 148..294 = %.4g; model with +0xa8 = 0, samples 0..146 = %.4g"
      % (rmsd, rms0))
    check(first_diff is not None and first_diff == 148 and fd0 is not None and fd0 <= 2 and (fdf is None or fdf <= 2) and fd2 == react + 148,
          "H074 (start): real Insert COMPRESSOR output equals the dry input bit-exactly for samples 0..147 after activation (skip 147, "
          "then the fade-in ramp starts at wet 0), also on re-activation; with +0xa8 = 0 (same compressor, model) and on the real "
          "Flanger the wet path starts at sample 1")
    check(tail and max(tail) == 146 and tail0 and max(tail0) == 146,
          "H074 (stop): after slot 6 the compressor differs from the input for exactly samples stop..stop+146 with +0xa8 = 1 and "
          "with +0xa8 = 0: the 147-sample clamp coincides with the 147-sample stop fade, so it changes nothing audible")
    J["c6"] = dict(first_diff=first_diff, stop_tail_max=max(tail) if tail else None, react_first=(fd2 - react) if fd2 is not None else None,
                   a8_0_first_diff=fd0, a8_0_tail=max(tail0) if tail0 else None)

    P("\nRESULT: %d failed checks" % len(fails))
    open(os.path.join(a.out, "h044_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h044.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
