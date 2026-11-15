#!/usr/bin/env python3
"""H039 — InsertFxDelay (Insert index 4; vtable 0x841c80, new 0x5d0, ctor 0x103488, slot 25 0x102cc0 -> slot 26 0x102ebc + slot 33
0x102d3c; second base DelayEchoBaseSingleDelay at +0x1b8, vtable 0x841d10) end to end: parameters -> formulas -> state layout ->
bit-exact own-code model harness/models/insert_delay.py vs the emulated 1.60 slot 25.

Sections (criteria of kb/cycles/015.md):
  C1  parameter list: LinearParameter/ToggleParameter registrations logged in the real ctor, slot-14 index map (emulated), Insert
      slot-52 case-4 defaults, change detection, which indices slot 32 reads.
  C2  formula sweeps by emulated read-back vs the model: delay time free (>= 30 values incl. rint boundaries), sync (6 divisions x
      BPM 1..999), feedback, HiCut (target step / cutoff / settled coefficients), Mixratio (dry/wet); sync table; libm oracle.
  C3  layout: model state == emulated fields after every block of every C4 run; constants (ring length, ramp N, filter steps).
  C4  end-to-end matrix: >= 8 settings x {impulse train, sine, noise, silence} + mid-run change runs (delay time, BPM, HiCut,
      feedback, Mixratio, SYNC), slot-25 output bit-exact, state compared after every block.
  C5  start-up gate, slot 27 reset (and EffectBase slot 5 activation path), slot 10, buffer contents on delay-time change.
  C6  alternatives (model mutants that must fail): feedback before the HiCut, delay-time glide (interpolated) instead of
      mute-jump, warm-up counter by chunk, crossfade Mixratio, LowCut/Spread active, unquantised delay time.
  C7  SendFxDelay relation: static comparison of the core routines its methods call.
Outputs only to --out (default harness/out/H039/). Run: .venv/bin/python -B harness/H039_insert_delay_model.py --out DIR
"""
import argparse, hashlib, json, math, os, random, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import EmuAbort, f2u, u2f, SP                          # noqa: E402
import sp16img                                                 # noqa: E402
import H031_osc_model as H31                                   # noqa: E402
import H007_effect_emu as H7                                   # noqa: E402
import insert_delay as M                                       # noqa: E402
from lofi import F                                             # noqa: E402

FS = 44100; N = 64
FRAC_INIT = (0x6cbe0, 0x6ce8c)      # straight-line part of .init_array entry 0x6cb20 (fills the Fraction tables, r4 = 0xf61f18)
SYNC_TABLE = 0xf61fb4               # InsertFxDelay sync divisions (read by 0x34ba88), {u16 num, u16 den}
CTOR, SIZE, VT = 0x103488, 0x5d0, 0x841c80
REG = {0xf1850: "LinearParameter", 0xf1800: "ToggleParameter"}
PARAM_OFF = {0: 0x30c, 1: 0x368, 2: 0x3c4, 3: 0x420, 4: 0x47c, 5: 0x4d8, 6: 0x534, 7: 0x55c}


def sha(b): return hashlib.sha256(b).hexdigest()


class EmuDelay:
    """InsertFxDelay built by its real ctor 0x103488(obj, 44100, 64) after the sync-table initialiser, then (optionally) the H007
    Insert init (slot 22, 0x106c7c(obj,1,10), InsertFxProcessor slot 52 case 4); processed by calling slot 25 directly."""
    def __init__(self, defaults=True, log_regs=False, watch=None):
        self.e = e = H31.new_emu(); self.regs = []; self.s14 = []
        for i in range(13): e.setr(i, 0)
        e.setr(4, 0xf61f18); e.uc.reg_write(SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
        e.uc.emu_start(FRAC_INIT[0], FRAC_INIT[1])
        if log_regs:
            for a_, nm in REG.items():
                def cb(em, a_=a_, nm=nm):
                    sp = em.uc.reg_read(SP)
                    st = [em.u32(sp + 4 * k) for k in range(4)]
                    nmp = em.r(1); s = b""
                    while True:
                        c = em.rd(nmp + len(s), 1)
                        if c == b"\0" or len(s) > 40: break
                        s += c
                    self.regs.append({"kind": nm, "off": em.r(0) - self.o, "name": s.decode(), "id": em.r(2),
                                      "min": u2f(em.r(3)) if nm == "LinearParameter" else None,
                                      "max": u2f(st[0]) if nm == "LinearParameter" else None,
                                      "default": u2f(st[1]) if nm == "LinearParameter" else None})
                e.add_watch(a_, cb)
        for a_, cb in (watch or {}).items(): e.add_watch(a_, cb)
        e.add_watch(0x105d24, lambda em: self.s14.append((em.r(1), em.r(2))))
        self.obj = self.o = e.malloc(SIZE, "new (harness: InsertFxDelay)")
        r0, _ = e.call(CTOR, self.o, FS, N)
        assert r0 == self.o and e.u32(self.o) == VT
        self.fx = {"insert_index": 4}; self.init_log = []
        self.regs_done = list(self.regs)
        if defaults:
            self.s14 = []
            H7.Run.insert_init(self)
            self.defaults_s14 = list(self.s14)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set(self, idx, v): return self.e.vcall(self.o, 14, idx, f2u(v))[0]
    def set_bits(self, idx, bits): return self.e.vcall(self.o, 14, idx, bits)[0]

    def process(self, L, R):
        e = self.e
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, len(L))
        assert r0 == 0
        return e.floats(self.bl, len(L)), e.floats(self.br, len(L))

    # --- field access ------------------------------------------------------------------------------------------------------
    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def f(self, a): return self.e.u32(a)                         # float fields compared as bits
    def d(self, a): return struct.unpack("<d", self.e.rd(a, 8))[0]
    def b(self, a): return self.e.rd(a, 1)[0]

    def ptrs(self):
        o = self.o; mod = self.u(o + 0x29c); ring = self.u(mod + 0x1c); fc = self.u(o + 0x5b8); fl = self.u(fc)
        return o, mod, ring, fc, fl

    def state(self):
        o, mod, ring, fc, fl = self.ptrs(); f, u, i, b, d = self.f, self.u, self.i, self.b, self.d
        g = mod + 0x50; s = o + 0x2a0; st = self.u(fl + 0x10)
        out = {"dry+0x10": f(o + 0x10), "wet+0x14": f(o + 0x14),
               "sync+0x5bc": b(o + 0x5bc), "bpm+0x5c0": f(o + 0x5c0), "time+0x5c4": f(o + 0x5c4), "dirty+0x5c8": b(o + 0x5c8),
               "m.ms+0x20": f(mod + 0x20), "m.D+0x24": i(mod + 0x24), "m.pend+0x28": b(mod + 0x28), "m.pms+0x2c": f(mod + 0x2c),
               "m.pD+0x30": i(mod + 0x30), "m.warm+0x7c": b(mod + 0x7c), "m.full+0x7d": b(mod + 0x7d), "m.cnt+0x80": i(mod + 0x80),
               "g.state": i(g + 4), "g.cur": f(g + 8), "g.tgt": f(g + 0xc), "g.inc": f(g + 0x10), "g.rem": i(g + 0x14),
               "r.w+0x1c": i(ring + 0x1c), "r.pos+0x28": d(ring + 0x28),
               "fb.state": i(s + 4), "fb.cur": f(s + 8), "fb.tgt": f(s + 0xc), "fb.inc": f(s + 0x10), "fb.rem": i(s + 0x14),
               "h.tgtcut+0x18": d(fc + 0x18), "h.cut+0x20": d(fc + 0x20), "h.cur+0x28": u(fc + 0x28), "h.tgt+0x2c": u(fc + 0x2c),
               "h.acc+0x30": f(fc + 0x30), "h.flag+0x40": b(fc + 0x40),
               "h.fc+0xc": f(fl + 0xc), "h.b0": f(fl + 0x28), "h.b1": f(fl + 0x2c), "h.a1": f(fl + 0x34), "h.k": f(fl + 0x24),
               "h.v1": [f(st), f(st + 4)], "h.y1": [f(st + 8), f(st + 12)]}
        for k_, off in PARAM_OFF.items():
            if k_ == 6: out["p6.last/cur"] = [b(o + off + 0x24), b(o + off + 0x25)]
            else: out["p%d.last/cur" % k_] = [f(o + off + 0x24), f(o + off + 0x28)]
        return out

    def ring(self):
        o, mod, ring, fc, fl = self.ptrs()
        n = self.u(ring + 4); raw = self.e.rd(self.u(ring + 0x18), 8 * n)
        return n, raw


def model_state(m):
    fb = f2u; mod = m.mod; g = mod.gate.r; s = m.fbg; h = m.hicut
    out = {"dry+0x10": fb(m.dry), "wet+0x14": fb(m.wet),
           "sync+0x5bc": m.sync_v, "bpm+0x5c0": fb(m.bpm_v), "time+0x5c4": fb(m.time_v), "dirty+0x5c8": m.dirty,
           "m.ms+0x20": fb(mod.ms), "m.D+0x24": mod.D, "m.pend+0x28": mod.pend, "m.pms+0x2c": fb(mod.pms), "m.pD+0x30": mod.pD,
           "m.warm+0x7c": mod.warm, "m.full+0x7d": mod.full, "m.cnt+0x80": mod.cnt,
           "g.state": g.state, "g.cur": fb(g.cur), "g.tgt": fb(g.target), "g.inc": fb(g.inc), "g.rem": g.rem,
           "r.w+0x1c": mod.ring.w, "r.pos+0x28": mod.ring.pos,
           "fb.state": s.state, "fb.cur": fb(s.cur), "fb.tgt": fb(s.target), "fb.inc": fb(s.inc), "fb.rem": s.rem,
           "h.tgtcut+0x18": h.tgt_cut, "h.cut+0x20": h.cut, "h.cur+0x28": h.cur, "h.tgt+0x2c": h.tgt,
           "h.acc+0x30": fb(h.acc), "h.flag+0x40": h.flag,
           "h.fc+0xc": fb(h.fc), "h.b0": fb(h.b0), "h.b1": fb(h.b1), "h.a1": fb(h.a1), "h.k": fb(h.k),
           "h.v1": [fb(h.v1[0]), fb(h.v1[1])], "h.y1": [fb(h.y1[0]), fb(h.y1[1])]}
    for k_ in PARAM_OFF:
        p = m.p[k_]
        out["p%d.last/cur" % k_] = [p.last, p.cur] if k_ == 6 else [fb(p.last), fb(p.cur)]
    return out


def model_ring(m):
    r = m.mod.ring
    return r.L, b"".join(struct.pack("<ff", r.buf[0][k], r.buf[1][k]) for k in range(r.L))


def diff(se, sm): return [(k_, se.get(k_), v) for k_, v in sm.items() if se.get(k_) != v]


def new_pair(defaults=True, mut=None):
    x = EmuDelay(defaults=defaults)
    m = M.InsertDelay()
    if defaults: m.insert_defaults()
    if mut: mut(m)
    return x, m


def signal(kind, nblk, seed=11):
    n = nblk * N; rnd = random.Random(seed)
    if kind == "impulse":        # impulse train: one every 1999 samples (L) / 3001 samples (R, half height)
        L = [F(1.0) if k % 1999 == 0 else F(0.0) for k in range(n)]
        R = [F(0.5) if k % 3001 == 7 else F(0.0) for k in range(n)]
    elif kind == "sine":
        L = [F(0.5 * math.sin(2 * math.pi * 1000.0 * k / FS)) for k in range(n)]
        R = [F(0.3 * math.sin(2 * math.pi * 3500.0 * k / FS + 1.0)) for k in range(n)]
    elif kind == "noise":
        L = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
        R = [F(rnd.uniform(-0.5, 0.5)) for _ in range(n)]
    else:
        L = [F(0.0)] * n; R = [F(0.0)] * n
    return L, R


# settings: (name, [(idx, value)] after the Insert defaults, bpm fed every block, blocks)
SETTINGS = [
    ("defaults_500ms_fb.7", [], 120.0, 1100),
    ("min_10ms_fb.5_hicut.5", [(0, 0.0), (1, 0.5), (2, 0.5)], 120.0, 160),
    ("max_1000ms_fb1_maxfb", [(0, 1.0), (1, 1.0)], 120.0, 2100),
    ("free_59.5->60ms_fb.95_hicut0_mix.8", [(0, 0.05), (1, 0.95), (2, 0.0), (5, 0.8)], 120.0, 240),
    ("sync_120_3/4beat_fb.6", [(6, 1.0), (0, 0.6), (1, 0.6), (2, 0.8)], 120.0, 600),
    ("sync_87.5_1/4beat_fb.4", [(6, 1.0), (0, 0.2), (1, 0.4), (2, 0.25)], 87.5, 400),
    ("sync_999_1/8beat_clamp10ms", [(6, 1.0), (0, 0.0), (1, 0.8), (2, 0.6)], 999.0, 160),
    ("sync_60_2beats_clamp1000", [(6, 1.0), (0, 1.0), (1, 0.3), (2, 0.9)], 60.0, 1500),
    ("sync_133.37_1beat_fb.99", [(6, 1.0), (0, 0.8), (1, 0.99), (2, 0.4), (5, 0.3)], 133.37, 1000),
    ("free_.1234_fb0_hicut.3", [(0, 0.1234), (1, 0.0), (2, 0.3), (5, 1.0)], 120.0, 160),
]
# mid-run events: {block: [ops]}, op = ("p", idx, v) | ("bpm", v) | ("reset",)
EVENTS = [
    ("time_changes_free", [(0, 0.2), (1, 0.6), (2, 0.7)], 120.0, 700,
     {150: [("p", 0, 0.04)], 260: [("p", 0, 0.75)], 400: [("p", 0, 0.3)], 401: [("p", 0, 0.1)], 403: [("p", 0, 0.5)]}),
    ("bpm_changes_sync", [(6, 1.0), (0, 0.6), (1, 0.7), (2, 0.6)], 120.0, 700,
     {150: [("bpm", 140.0)], 300: [("bpm", 60.0)], 301: [("bpm", 140.0)], 450: [("bpm", 999.0)], 520: [("bpm", 1.0)],
      600: [("bpm", 133.37)]}),
    ("hicut_fb_mix_sync_changes", [(0, 0.1), (1, 0.5), (2, 1.0)], 120.0, 500,
     {100: [("p", 2, 0.0)], 130: [("p", 2, 0.7), ("p", 1, 0.9)], 200: [("p", 5, 0.5)], 250: [("p", 6, 1.0)], 251: [("p", 0, 0.3)],
      320: [("p", 6, 0.0)], 330: [("p", 1, 0.0)], 400: [("p", 2, 0.33), ("p", 1, 1.0)]}),
    ("reset_and_restart", [(0, 0.15), (1, 0.8), (2, 0.6)], 120.0, 500,
     {120: [("reset",)], 121: [("p", 0, 0.05)], 300: [("p", 0, 0.2), ("reset",)], 301: [("p", 3, 1.0), ("p", 4, 1.0)]}),
    # ring full of old samples (> 46600 frames written), reset, short delay until warm, then the longest delay: the warm-up counter
    # over-counts during the gate fade (two inner chunks per block), so the gate re-opens shortly before the read pointer reaches
    # post-reset samples and stale pre-reset ring content becomes audible for a few samples.
    ("reset_stale_ring", [(0, 0.5), (1, 0.9), (2, 1.0)], 120.0, 1700,
     {800: [("reset",)], 801: [("p", 0, 0.0)], 830: [("p", 0, 1.0)]}),
]


def run_case(name, pre, bpm, events, kind, nblk, mut=None, keep=False, check_state=True, emu_obj=None):
    x, m = new_pair(mut=mut) if emu_obj is None else emu_obj
    L, R = signal(kind, nblk)
    for idx, v in pre: x.set(idx, v); m.set_param(idx, v)
    cur_bpm = bpm; maxerr = 0.0; nbit = 0; first_state = None; outb = bytearray()
    nonzero = 0
    for blk in range(nblk):
        for op in events.get(blk, []):
            if op[0] == "p": x.set(op[1], op[2]); m.set_param(op[1], op[2])
            elif op[0] == "bpm": cur_bpm = op[1]
            elif op[0] == "reset": x.e.vcall(x.o, 27); m.reset()
        x.set(7, cur_bpm); m.set_param(7, cur_bpm)                          # processBlock tempo feed (F017)
        bL, bR = L[blk * N:(blk + 1) * N], R[blk * N:(blk + 1) * N]
        eL, eR = x.process(bL, bR)
        mL, mR = m.process(bL, bR)
        for a_, b_ in zip(eL + eR, mL + mR):
            if f2u(a_) != f2u(b_):
                nbit += 1
                if not (math.isnan(a_) and math.isnan(b_)): maxerr = max(maxerr, abs(a_ - b_))
            if a_ != 0.0: nonzero += 1
        outb += struct.pack("<%df" % (2 * N), *(eL + eR))
        if check_state and first_state is None:
            dd = diff(x.state(), model_state(m))
            if dd: first_state = (blk, dd[:6])
    ring_eq = x.ring() == model_ring(m)
    res = {"name": name, "signal": kind, "blocks": nblk, "samples": 2 * N * nblk, "mismatched_samples": nbit, "max_abs_err": maxerr,
           "nonzero_out": nonzero, "first_state_diff": first_state, "final_ring_equal": ring_eq,
           "ms_log": [float(v) for v in m.ms_log][:12]}
    return (res, bytes(outb), (x, m)) if keep else (res, bytes(outb))


# ------------------------------------------------------------------------------------------------------------------------
# C6 model mutants (each must be caught by its target run)
def mut_fb_before_hicut(m):
    def process(L, R, m=m):
        m.update_mix(); m.apply_params()
        n = len(L); oL = list(L); oR = list(R)
        yL, yR = m.mod.read(n)
        wL = list(yL); wR = list(yR)                      # feedback taken BEFORE the HiCut
        m.hicut.process(yL, yR, n)
        m._fb_mul(wL, wR, n); M.ftz_list_add(wL, L, n); M.ftz_list_add(wR, R, n)
        m.mod.write(wL, wR, n)
        return yL, yR
    m.process = process


def mut_no_mute_jump(m):                                  # delay change = immediate jump, no gate fade
    def set_delay(ms, glide=1, mod=m.mod):
        x = F(min(max(F(ms), F(0.0)), mod.maxms))
        if M.near(x, mod.ms): return
        mod.ms = x; mod.D = mod.samples(x); mod.pms = x; mod.pD = mod.D
        mod.ring.set_delay(F(float(mod.D)))
    m.mod.set_delay = set_delay


def mut_count_chunk(m):                                   # warm-up counter adds the chunk, not the whole request
    mod = m.mod
    def read(n, mod=mod):
        oL, oR = [], []; rem = n
        while True:
            r = mod.gate.r
            c = min(r.rem, mod.D, rem) if mod._closing() else min(rem, mod.D)
            L, R = mod.ring.read(c); mod.gate.apply(L, R, 0, c); oL += L; oR += R; rem -= c
            cf = mod.full
            if not mod.full:
                mod.cnt += c; mod.warm = 1 if mod.D <= mod.cnt else 0
                if mod.full_thr <= mod.cnt: mod.full = 1; cf = 1
            if mod.pend and r.state != 1 and M.near(r.cur, mod.gate.off):
                mod.ms = mod.pms; mod.D = mod.pD; mod.ring.set_delay(F(float(mod.D - (n - rem)))); cf = mod.full; mod.pend = 0
            if cf == 0 and mod.warm == 0: mod.gate.close()
            elif not mod._closing(): mod.gate.open()
            if rem < 1: return oL, oR
    mod.read = read


def mut_crossfade_mix(m):
    def um(m=m):
        v = m.p[5].get(); m.wet = F(v); m.dry = F(F(1.0) - v)
    m.update_mix = um


def mut_unquantised_time(m):
    m.free_ms = lambda v: F(F(10.0) + F(F(v) * F(990.0)))


def mut_zeroing_reset(m):
    r = m.mod.ring
    def rewind(r=r):
        r.buf = [[F(0.0)] * r.L, [F(0.0)] * r.L]; r.w = 0; r.pos = 0.0
    r.rewind = rewind


def mut_hicut_no_glide(m):
    h = m.hicut
    orig = h.set_step
    def set_step(idx, h=h, orig=orig):
        orig(idx); h.cur = h.tgt; h.cut = h.tgt_cut
    h.set_step = set_step


MUTANTS = [
    ("feedback before HiCut", mut_fb_before_hicut, "hicut_fb_mix_sync_changes", "noise"),
    ("delay change = immediate jump (no fade)", mut_no_mute_jump, "time_changes_free", "noise"),
    ("warm-up counter adds the chunk", mut_count_chunk, "reset_stale_ring", "noise"),
    ("Mixratio crossfade (dry 1-v, wet v)", mut_crossfade_mix, "hicut_fb_mix_sync_changes", "noise"),
    ("unquantised delay time 10+990v", mut_unquantised_time, "free_.1234_fb0_hicut.3", "noise"),
    ("reset zeroes the ring", mut_zeroing_reset, "reset_stale_ring", "noise"),
    ("HiCut jumps without glide", mut_hicut_no_glide, "hicut_fb_mix_sync_changes", "noise"),
]


def find_case(name):
    for s in SETTINGS:
        if s[0] == name: return s[0], s[1], s[2], {}, s[3]
    for s in EVENTS:
        if s[0] == name: return s[0], s[1], s[2], s[4], s[3]
    raise KeyError(name)


# ------------------------------------------------------------------------------------------------------------------------
# regression: earlier harnesses must reproduce their recorded hashes (kb/findings.md evidence lines); (prefix, suffix) pairs
REGRESS = [
    ("H021", "H021_lofi_model.py", "h021", {"report": ("9273c853", "2677"), "json": ("f3316770", "d839"), "f32": ("86f8975a", "74a4")}),
    ("H023", "H023_mmf_model.py", "h023", {"report": ("9c33b389", "25eb"), "f32": ("5ccbbf43", "2baa")}),
    ("H026", "H026_peq_model.py", "h026", {"report": ("ed20422f", "93e9"), "json": ("fa2ebab6", "fbfd"), "f32": ("a3cb6985", "8f58")}),
    ("H028", "H028_phaser_model.py", "h028", {"report": ("1810c080", "9d227e"), "f32": ("cf14c39c", "5bd7")}),
    ("H031", "H031_osc_model.py", "h031", {"report": ("3fcde046", "d6ac"), "f32": ("2be562d2", "406f")}),
    ("H033", "H033_chorus_model.py", "h033", {"report": ("09032fa8", "6052"), "json": ("a04fce64", "c286"), "f32": ("ef54794e", "ce3d")}),
    ("H034", "H034_flanger_model.py", "h034", {"report": ("a9713642", "c019"), "json": ("861a3234", "913b"), "f32": ("b00781e5", "be46")}),
    ("H035", "H035_distortion_model.py", "h035", {"report": ("29a5598b", "b95b"), "json": ("7c0b94bc", "4c00"), "f32": ("c2ad7973", "82f0")}),
]


def regress(out):
    import subprocess, glob
    procs = []
    for hid, script, pre, exp in REGRESS:
        d = os.path.join(out, "regress", hid); os.makedirs(d, exist_ok=True)
        lg = open(os.path.join(out, "regress", hid + ".log"), "w")
        procs.append((hid, pre, exp, d, subprocess.Popen([sys.executable, "-B", os.path.join(HERE, script), "--out", d],
                                                        stdout=lg, stderr=subprocess.STDOUT, cwd=os.path.dirname(HERE))))
    lines = []; ok_all = True
    for hid, pre, exp, d, p in procs:
        rc = p.wait()
        got = {}
        rp = os.path.join(d, pre + "_report.txt"); jp = os.path.join(d, pre + ".json")
        if os.path.exists(rp): got["report"] = sha(open(rp, "rb").read())
        if os.path.exists(jp): got["json"] = sha(open(jp, "rb").read())
        fs_ = sorted(glob.glob(os.path.join(d, "*.f32")))
        got["f32"] = sha(b"".join(open(f_, "rb").read() for f_ in fs_))
        ok = all(k_ in got and got[k_].startswith(v[0]) and got[k_].endswith(v[1]) for k_, v in exp.items())
        ok_all &= ok
        lines.append("%s rc %d  %s  %s" % (hid, rc, "OK " if ok else "BAD", "  ".join("%s %s…%s" % (k_, got.get(k_, "-")[:8],
                                                                                         got.get(k_, "-")[-4:]) for k_ in exp)))
    txt = "\n".join(lines) + "\nREGRESSION: %s\n" % ("all recorded hashes reproduced" if ok_all else "MISMATCH")
    open(os.path.join(out, "h039_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok_all else 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H039"))
    ap.add_argument("--skip-matrix", action="store_true"); ap.add_argument("--mutants", action="store_true")
    ap.add_argument("--regress", action="store_true", help="only re-run H021..H035 and compare their recorded hashes")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    rep = []; J = {}; fails = []
    def P(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        P(("PASS  " if c else "FAIL  ") + msg)
        if not c: fails.append(msg)

    P("H039 InsertFxDelay end-to-end — target sha256 %s" % emu.SHA)
    im = sp16img.Image()

    # ---------------------------------------------------------------------------------------------------------- C1
    P("\n== C1 parameters")
    x = EmuDelay(defaults=False, log_regs=True)
    regs = x.regs_done
    for r_ in regs:
        P("  reg %-15s off +0x%03x id %d %-13s min %s max %s default %s" % (r_["kind"], r_["off"], r_["id"], r_["name"], r_["min"],
                                                                         r_["max"], r_["default"]))
    J["registrations"] = regs
    main_regs = [r_ for r_ in regs if r_["off"] >= 0x300]
    check([(r_["name"], r_["id"], r_["off"]) for r_ in main_regs] ==
          [("DelayTime", 0, 0x30c), ("Feedback", 1, 0x368), ("HiCut", 2, 0x3c4), ("LowCut", 3, 0x420), ("Spread", 4, 0x47c),
           ("Mixratio", 5, 0x4d8), ("SYNC", 6, 0x534), ("BPM", 7, 0x55c)],
          "8 InsertFxDelay parameters registered (7 LinearParameter + SYNC ToggleParameter), ids 0..7 at +0x30c + 0x5c*i")
    check([(r_["min"], r_["max"], r_["default"]) for r_ in main_regs if r_["kind"] == "LinearParameter"] ==
          [(0.0, 1.0, 0.75), (0.0, 1.0, 0.0), (0.0, 1.0, 1.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), (1.0, 999.0, 120.0)],
          "ranges/ctor defaults: DelayTime 0..1 (0.75), Feedback/HiCut/LowCut/Spread/Mixratio 0..1 (0,1,0,0,0), BPM 1..999 (120)")
    desd_regs = [r_ for r_ in regs if r_["off"] < 0x300]
    P("  DelayEchoBaseSingleDelay registrations (own Parameter objects, not reachable through slot 14): %s" %
      [(r_["name"], hex(r_["off"]), r_["min"], r_["max"]) for r_ in desd_regs])
    # change detection: ctor-equal value never applied
    xs = EmuDelay(defaults=False); ms0 = M.InsertDelay()
    xs.set(0, 0.75); ms0.set_param(0, 0.75)
    xs.process([0.0] * N, [0.0] * N); ms0.process([0.0] * N, [0.0] * N)
    st = xs.state()
    check(st["m.ms+0x20"] == f2u(50.0) and st["m.D+0x24"] == 2205 and st["m.pend+0x28"] == 0 and diff(st, model_state(ms0)) == [],
          "F026 change detection: DelayTime set to its ctor value 0.75 is never applied; the module keeps its ctor delay 50 ms = 2205 samples")
    # slot-14 index map
    imap = {}
    for idx in range(10):
        xx = EmuDelay(defaults=False); s0 = xx.state()
        ret = xx.set(idx, 0.37); s1 = xx.state()
        imm = sorted(k_ for k_ in s1 if s1[k_] != s0[k_])
        xx.process([0.0] * N, [0.0] * N); s2 = xx.state()
        later = sorted(k_ for k_ in s2 if s2[k_] != s1[k_] and not k_.startswith(("r.", "m.cnt", "h.v1", "h.y1", "g.", "fb.")))
        imap[idx] = {"ret": ret, "changed_immediately": imm, "changed_after_next_slot25": later}
        P("  slot14(%d, 0.37) -> ret %d, immediate %s, after next slot 25 %s" % (idx, ret, imm, later))
    J["slot14_map"] = imap
    xt6 = EmuDelay(defaults=False); r6a = xt6.set(6, 1.0); r6b = xt6.set(6, 0.0); r6c = xt6.set(6, 0.999)
    P("  slot14(6, 1.0) -> %d, (6, 0.0) -> %d, (6, 0.999) -> %d" % (r6a, r6b, r6c))
    check(all(imap[i]["ret"] == 0 for i in (0, 1, 2, 3, 4, 5, 7)) and imap[8]["ret"] == 3 and imap[9]["ret"] == 3 and
          all(imap[i]["changed_immediately"] == ["p%d.last/cur" % i] for i in (0, 1, 2, 3, 4, 5, 7)) and
          imap[6]["changed_immediately"] == [] and imap[6]["ret"] == 3 and (r6a, r6b, r6c) == (0, 0, 3),
          "slot 14 (EffectBase 0x105d24) only stores into the Parameter object (indices 0..7 return 0; >= 8 return 3); the SYNC "
          "toggle accepts only v >= 1 (on) or v <= 0 (off) and returns 3 (value ignored) for 0 < v < 1")
    check(imap[3]["changed_after_next_slot25"] == [] and imap[4]["changed_after_next_slot25"] == [],
          "LowCut (3) and Spread (4) are never consumed: no DSP field changes after the next slot 25")
    check("m.pms+0x2c" in imap[0]["changed_after_next_slot25"] and "fb.tgt" not in imap[1]["changed_immediately"] and
          "wet+0x14" in imap[5]["changed_after_next_slot25"],
          "DelayTime/Feedback/HiCut/Mixratio are applied at the next slot 25 (slot 26 mix first, then slot 32 inside slot 33)")
    xd = EmuDelay(defaults=True)
    J["insert_defaults_s14"] = [(i_, "0x%08x" % b_) for i_, b_ in xd.defaults_s14]
    P("  Insert slot 52 case 4 defaults: %s" % [(i_, "0x%08x" % b_, u2f(b_)) for i_, b_ in xd.defaults_s14])
    check(xd.defaults_s14 == M.INSERT_DEFAULTS,
          "Insert defaults (slot 52 case 4): DelayTime 49/99 (500 ms), Feedback 0.7, HiCut 1.0, Mixratio 0, SYNC 0 (BPM fed per block)")

    # ---------------------------------------------------------------------------------------------------------- C2
    P("\n== C2 formula sweeps (emulated read-back vs model, full state after every step)")
    tab = [(x.u(SYNC_TABLE + 4 * k) & 0xffff, x.u(SYNC_TABLE + 4 * k) >> 16) for k in range(7)]
    check(tab == M.SYNC_BEATS, "sync table 0xf61fb4 (filled by .init_array 0x6cb20) = %s beats (index 6 = assert fallback)" % tab)

    def sweep(name, setup, seq, key_fields):
        xw, mw = new_pair()
        for idx, v in setup: xw.set(idx, v); mw.set_param(idx, v)
        bpm = 120.0; rows = []; bad = 0; nvals = 0
        for item in seq:
            if item[0] == "bpm": bpm = item[1]; continue
            idx, v = item
            xw.set(idx, v); mw.set_param(idx, v)
            xw.set(7, bpm); mw.set_param(7, bpm)
            xw.process([0.0] * N, [0.0] * N); mw.process([0.0] * N, [0.0] * N)
            se, sm = xw.state(), model_state(mw); dd = diff(se, sm)
            nvals += len(sm)
            if dd: bad += 1
            rows.append((item, bpm, {k_: se[k_] for k_ in key_fields}, dd[:3]))
        P("  %-10s %3d steps, %5d field comparisons, %d steps with a difference" % (name, len(rows), nvals, bad))
        return rows, bad

    def fl(u): return u2f(u) if isinstance(u, int) else u
    # free delay time
    vs = [0.0, 1.0, 49 / 99, 0.25, 0.5, 0.75, 1 / 990, 0.5 / 990, 1.5 / 990, 2.5 / 990, 0.123456, 0.999, 0.9995, 1.05, 0.3, 0.6]
    for k in (10.5, 11.5, 500.5, 999.5):                   # rint half-way points 10 + 990 v = k and their float neighbours
        v0 = F((k - 10.0) / 990.0); vs += [v0, F(math.nextafter(v0, 0.0)), F(math.nextafter(v0, 1.0))]
    rr5 = random.Random(5); vs += [rr5.random() for _ in range(14)]
    vs = [F(v) for v in vs]
    seq = []
    for v in vs: seq += [(0, v), (0, v)]                   # second identical set: no change (dirty stays 0)
    rows, bad = sweep("time free", [(1, 0.0)], seq, ["m.pms+0x2c", "m.pD+0x30", "m.ms+0x20", "m.D+0x24"])
    P("    v -> ms/samples: " + ", ".join("%.6g->%g/%d" % (r_[0][1], fl(r_[2]["m.pms+0x2c"]), r_[2]["m.pD+0x30"]) for r_ in rows[::2][:20]))
    check(bad == 0 and len(set(vs)) >= 30, "DelayTime free: ms = rint(10 + 990 v) (half-even; 10..1000, > 1000 clamped), samples = "
          "trunc(ms*0.001f*fs): %d values incl. rint boundaries, 0 mismatches" % len(set(vs)))
    J["sweep_time_free"] = [(r_[0][1], fl(r_[2]["m.pms+0x2c"]), r_[2]["m.pD+0x30"]) for r_ in rows[::2]]
    # sync
    seq = []; sv = [0.0, 0.0999, 0.1, 0.2, 0.3, 0.3001, 0.5, 0.7, 0.9, 1.0]
    for bpm in (1.0, 30.0, 60.0, 87.5, 120.0, 133.37, 200.0, 333.0, 999.0):
        seq.append(("bpm", bpm)); seq += [(0, F(v)) for v in sv]
    rows, bad = sweep("time sync", [(6, 1.0), (1, 0.0)], seq, ["m.pms+0x2c", "m.pD+0x30"])
    P("    bpm 120: " + ", ".join("%g->%g" % (r_[0][1], fl(r_[2]["m.pms+0x2c"])) for r_ in rows if r_[1] == 120.0))
    P("    bpm 133.37: " + ", ".join("%g->%.6g" % (r_[0][1], fl(r_[2]["m.pms+0x2c"])) for r_ in rows if r_[1] == 133.37))
    check(bad == 0, "DelayTime sync: i = rint(5v), ms = F(F(F(num/den)*1000)*60)/BPM clamped [10, 1000] for 9 BPM values 1..999 x %d "
          "values; 0 mismatches" % len(sv))
    J["sweep_time_sync"] = [(r_[1], r_[0][1], fl(r_[2]["m.pms+0x2c"]), r_[2]["m.pD+0x30"]) for r_ in rows]
    # feedback
    fv = [0.0, 0.004999, 0.005, 0.015, 0.025, 0.25, 0.5, 0.7, 0.994999, 0.995, 1.0, 1.2, -0.004, 0.33, 0.66]
    rows, bad = sweep("feedback", [], [(1, F(v)) for v in fv], ["fb.tgt", "fb.state", "fb.rem"])
    P("    v -> gain target: " + ", ".join("%g->%.8g" % (r_[0][1], fl(r_[2]["fb.tgt"])) for r_ in rows))
    check(bad == 0, "Feedback: g = F(rint(100v) * 0.01f) (0..1.00 in 0.01 steps; v > 1 gives g > 1, unclamped), 147-sample linear "
          "ramp (SmoothFloat obj+0x2a0); %d values, 0 mismatches" % len(fv))
    J["sweep_feedback"] = [(r_[0][1], fl(r_[2]["fb.tgt"])) for r_ in rows]
    # hicut (targets), then a settle
    hv = [0.0, 0.0005, 0.001001, 0.25, 0.5, 0.75, 0.999, 1.0, -0.1, 1.5, 0.123, 0.876]
    seq = []
    for v in hv: seq += [(2, F(v))] + [(3, 0.0)] * 2       # a few blocks of glide after each target
    rows, bad = sweep("hicut", [(1, 0.0)], seq, ["h.tgt+0x2c", "h.tgtcut+0x18", "h.cur+0x28", "h.fc+0xc"])
    P("    v -> step/target Hz: " + ", ".join("%g->%d/%.2f" % (r_[0][1], r_[2]["h.tgt+0x2c"] + 1, r_[2]["h.tgtcut+0x18"])
                                               for r_ in rows if r_[0][0] == 2))
    check(bad == 0, "HiCut: step = trunc_u32(999v) + 1 clamped 1..1000, target 2000*10^((step-1)/999) Hz (pow), glide 1 step per "
          "1/3 ms (one coefficient update per 14.7 samples), fc = clamp(cut, 5, fs/2); %d values, 0 mismatches" % len(hv))
    J["sweep_hicut"] = [(r_[0][1], r_[2]["h.tgt+0x2c"] + 1, r_[2]["h.tgtcut+0x18"]) for r_ in rows if r_[0][0] == 2]
    # settled filter: run long enough for the full glide 999 -> 0 steps and compare coefficients
    xw, mw = new_pair(); xw.set(2, 0.0); mw.set_param(2, 0.0)
    for _ in range(260): xw.set(7, 120.0); mw.set_param(7, 120.0); xw.process([0.0] * N, [0.0] * N); mw.process([0.0] * N, [0.0] * N)
    se = xw.state()
    P("    after 260 blocks at HiCut 0: cur step %d, cut %.6f Hz (target %.6f), fc %r, b0 %r, a1 %r" %
      (se["h.cur+0x28"], se["h.cut+0x20"], se["h.tgtcut+0x18"], u2f(se["h.fc+0xc"]), u2f(se["h.b0"]), u2f(se["h.a1"])))
    check(diff(se, model_state(mw)) == [] and se["h.cur+0x28"] == 0, "HiCut glide 20 kHz -> 2 kHz reaches step 0 (999 steps x 1/3 ms "
          "= 333 ms) and the settled coefficients match (cut = 20000/m^999 accumulated, not the exact target)")
    # mixratio
    mv = [0.0, 0.3, 0.5, 0.749999, 0.75, 0.8, 0.9, 1.0, 1.2, -0.2]
    rows, bad = sweep("mixratio", [], [(5, F(v)) for v in mv], ["dry+0x10", "wet+0x14"])
    P("    v -> dry/wet: " + ", ".join("%g->%.7g/%.7g" % (r_[0][1], fl(r_[2]["dry+0x10"]), fl(r_[2]["wet+0x14"])) for r_ in rows))
    check(bad == 0, "Mixratio (slot 26): v < 0.75: wet = v*1.3333334f, dry = 1; v >= 0.75: wet = 1, dry = 1 - 4(v - 0.75); %d values" % len(mv))
    J["sweep_mix"] = [(r_[0][1], fl(r_[2]["dry+0x10"]), fl(r_[2]["wet+0x14"])) for r_ in rows]
    # libm oracle: tan / pow / log10 from the real 1.60 libm vs the model's correctly rounded versions
    e = x.e; tmp = {}
    def lcall(nm, *ds):
        args = []
        for dv in ds: u = emu.d2u(dv); args += [u & 0xffffffff, u >> 32]
        r0, r1 = e.call(e.lib_exports[nm][0], *args); return emu.u2d(r0 | (r1 << 32))
    rr = random.Random(7); bad_t = bad_th = 0
    targs = [float(F(fc)) * (math.pi / 44100.0) for fc in [5.0, 2000.0, 20000.0, 22050.0] + [rr.uniform(5, 22050) for _ in range(1500)]]
    for t in targs:
        o = lcall("tan", t)
        if o != M.cr_tan(t): bad_t += 1
        if o != math.tan(t): bad_th += 1
    bad_p = bad_ph = 0
    mult = lcall("pow", 10.0, lcall("log10", 10.0) / 999.0)
    for k in range(1000):
        o = lcall("pow", mult, float(k))
        if o != M.cr_pow(mult, float(k)): bad_p += 1
        if o != math.pow(mult, float(k)): bad_ph += 1
    P("  libm: tan %d args: model cr_tan mismatches %d (host math.tan %d); pow(m, k) k=0..999: cr_pow %d (host %d); "
      "10^(log10(10)/999) = %r (model %r)" % (len(targs), bad_t, bad_th, bad_p, bad_ph, mult, M.HiCut().mult))
    check(bad_t == 0 and bad_p == 0 and mult == M.HiCut().mult, "correctly rounded tan/pow reproduce the emulated 1.60 libm")
    J["libm"] = {"tan_args": len(targs), "tan_mism_cr": bad_t, "tan_mism_host": bad_th, "pow_mism_cr": bad_p, "pow_mism_host": bad_ph}

    # ---------------------------------------------------------------------------------------------------------- C3
    P("\n== C3 layout / constants")
    xc = EmuDelay(); mc = M.InsertDelay(); mc.insert_defaults()
    o_, mod, ring, fc, fl_ = xc.ptrs()
    consts = {"ring frames": (xc.u(ring + 4), mc.mod.ring.L), "ring hi": (xc.u(ring + 0xc), mc.mod.ring.L - 1),
              "gate N": (xc.u(mod + 0x34 + 0x38), mc.mod.gate.r.N), "fb ramp N": (xc.u(o_ + 0x2a0 + 0x1c), mc.fbg.N),
              "maxms": (xc.f32(mod + 0x84) if hasattr(xc, "f32") else u2f(xc.u(mod + 0x84)), mc.mod.maxms),
              "interp flag +0x88": (xc.b(mod + 0x88), 1), "filter steps": (xc.u(fc + 0xc), mc.hicut.steps),
              "fmin": (xc.u(fc + 4), mc.hicut.fmin), "mult": (xc.d(fc + 0x38), mc.hicut.mult),
              "period": (xc.u(fc + 0x10), f2u(mc.hicut.period)), "ms/sample": (xc.u(fc + 0x34), f2u(mc.hicut.mps)),
              "nyq": (xc.u(fl_ + 4), f2u(mc.hicut.nyq)), "filter vptr": (hex(xc.u(fl_)), "0x840dd8"),
              "ring vptr": (hex(xc.u(ring)), "0x83e5c0"), "module vptr": (hex(xc.u(mod)), "0x840010"),
              "DESD vptr +0x1b8": (hex(xc.u(o_ + 0x1b8)), "0x841d10"), "scratch buffers +0x1c0": (xc.u(o_ + 0x1c0), 7)}
    for k_, (ev, mv_) in consts.items(): P("  %-24s emu %-22r model %r" % (k_, ev, mv_))
    check(all(ev == mv_ for ev, mv_ in consts.values()), "constants: ring 46600 frames (1000 ms + 2500), ramps N = 147 (3.33 ms), "
          "HiCut 1000 steps 2..20 kHz, mult 10^(1/999), 1/3 ms per step, vptrs RingBuffer/DelayModuleStereo/IirLpf1stOrder")
    check(diff(xc.state(), model_state(mc)) == [], "%d state fields equal after ctor + Insert init (compared after every block in C4)"
          % len(model_state(mc)))

    # ---------------------------------------------------------------------------------------------------------- C4
    hashes = {}
    if not a.skip_matrix:
        P("\n== C4 end-to-end matrix (slot 25 output, state after every block, final ring)")
        results = []
        for nm, pre, bpm, nb in SETTINGS:
            for kind in ("impulse", "sine", "noise", "silence"):
                r_, blob = run_case(nm, pre, bpm, {}, kind, nb)
                fn = "%s__%s.f32" % (nm.replace("/", "_"), kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-36s %-8s %4d blk  mism %d  max|err| %g  nonzero %6d  state %s  ring %s  ms %s" %
                  (nm, kind, nb, r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], "ok" if r_["first_state_diff"] is None
                   else r_["first_state_diff"], "eq" if r_["final_ring_equal"] else "DIFF", r_["ms_log"]))
        for nm, pre, bpm, nb, ev in EVENTS:
            for kind in ("impulse", "noise", "sine"):
                r_, blob = run_case(nm, pre, bpm, ev, kind, nb)
                fn = "%s__%s.f32" % (nm, kind); open(os.path.join(a.out, fn), "wb").write(blob); hashes[fn] = sha(blob)
                results.append(r_)
                P("  %-36s %-8s %4d blk  mism %d  max|err| %g  nonzero %6d  state %s  ring %s  ms %s" %
                  (nm, kind, nb, r_["mismatched_samples"], r_["max_abs_err"], r_["nonzero_out"], "ok" if r_["first_state_diff"] is None
                   else r_["first_state_diff"], "eq" if r_["final_ring_equal"] else "DIFF", r_["ms_log"]))
        J["matrix"] = results
        tot = sum(r_["samples"] for r_ in results)
        check(all(r_["mismatched_samples"] == 0 and r_["first_state_diff"] is None and r_["final_ring_equal"] for r_ in results),
              "insert_delay.py bit-exact to emulated slot 25: %d runs, %d output samples, state equal after every block, final ring equal"
              % (len(results), tot))
        check(len(SETTINGS) >= 8 and all(s[3] >= 120 for s in SETTINGS) and len(EVENTS) >= 2,
              "coverage: %d settings x 4 signals (>= 120 blocks; max delay, max feedback, free + sync, BPM 1..999), %d event runs"
              % (len(SETTINGS), len(EVENTS)))

    # ---------------------------------------------------------------------------------------------------------- C5
    P("\n== C5 start-up, reset, retrigger")
    def single_impulse(at, nblk=1100):
        xs, ms_ = new_pair()
        L = [F(1.0) if k == at else F(0.0) for k in range(N * nblk)]; same = True; nz = []; gtr = {}
        for blk in range(nblk):
            xs.set(7, 120.0); ms_.set_param(7, 120.0)
            eL, _ = xs.process(L[blk * N:(blk + 1) * N], [0.0] * N); mL, _ = ms_.process(L[blk * N:(blk + 1) * N], [0.0] * N)
            same = same and [f2u(v) for v in eL] == [f2u(v) for v in mL]
            nz += [(blk * N + k, v) for k, v in enumerate(eL) if v != 0.0]
            if blk in (343, 344, 345, 346): s_ = xs.state(); gtr[blk] = (round(u2f(s_["g.cur"]), 4), s_["m.warm+0x7c"], s_["m.cnt+0x80"])
        return same, nz, gtr
    same0, nz0, gtr0 = single_impulse(0)
    same1, nz1, gtr1 = single_impulse(64 * 3)
    P("  single impulse at t=0, Insert defaults (500 ms = 22050 samples, fb 0.7), 1100 blocks: model==emu %s; non-zero output samples "
      "%d; (gate, warm, counter) after blocks 343..346: %s" % (same0, len(nz0), gtr0))
    P("  same with the impulse at t=192: model==emu %s; first non-zero outputs %s; non-zero output samples %d" %
      (same1, [(t, round(v, 4)) for t, v in nz1[:3]], len(nz1)))
    J["startup"] = {"impulse_t0_nonzero": len(nz0), "impulse_t192_first": nz1[:3], "gate": {str(k): v for k, v in gtr0.items()}}
    check(same0 and same1 and len(nz0) == 0 and bool(nz1) and nz1[0][0] == 192 + 22050,
          "start-up quirk: the warm-up gate opens only after the block in which the counter reaches the delay (block 344, counter "
          "22080 >= 22050) and then fades in over 147 samples; an impulse at t = 0 echoes at sample 22050 inside block 344 and is muted, "
          "and because the gated signal is also the feedback source the delay stays silent (0 non-zero samples); an impulse at t = 192 "
          "echoes at 22242")
    # Mixratio at slot-18 level (EffectBase dry/wet sum; 0x106c88 post-stage neutralised)
    def slot18_run(mix):
        xq, mq = new_pair(); e = xq.e; cap = {}
        e.add_watch(0x106c88, lambda em: em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR)))
        # the slot-18 copy path ramps the effect INPUT after activation (0x1074c4, EffectInOutGain): feed the model what slot 25 gets
        e.add_watch(0x102cc0, lambda em: cap.__setitem__("in", (em.floats(em.r(1), em.r(3)), em.floats(em.r(2), em.r(3)))))
        Lq, Rq = signal("noise", 60); o = []; w = []; ramped = 0
        for i_, v_ in ((5, mix), (0, 0.0), (1, 0.5)): xq.set(i_, v_); mq.set_param(i_, v_)
        bl = e.malloc(4 * N); br = e.malloc(4 * N)
        for b in range(60):
            e.set_floats(bl, Lq[N * b:N * b + N]); e.set_floats(br, Rq[N * b:N * b + N])
            xq.set(7, 120.0); mq.set_param(7, 120.0)
            s9 = e.vcall(xq.o, 9)[0]
            if s9 == 0 and b == 0: e.vcall(xq.o, 5, 0, 1); e.vcall(xq.o, 7, 0); mq.reset()
            e.vcall(xq.o, 18, bl, br, N)
            o.append((e.floats(bl, N), e.floats(br, N)))
            ramped += sum(1 for k in range(N) if f2u(cap["in"][0][k]) != f2u(Lq[N * b + k]))
            w.append(mq.process(cap["in"][0], cap["in"][1]))
        dry, wet = mq.dry, mq.wet
        P("    (mix %g: %d of the first slot-25 input samples differ from the raw input = EffectBase input fade-in after activation)"
          % (mix, ramped))
        laws = {"slot-26 law F(F(dry*in)+F(wet*y))": 0, "crossfade F(F((1-v)in)+F(v y))": 0, "unity dry F(in+F(v y))": 0}
        ns = 0; nzw = 0
        for b in range(40, 60):
            for ch in (0, 1):
                for i in range(N):
                    inp = (Lq if ch == 0 else Rq)[N * b + i]; y = w[b][ch][i]; out = o[b][ch][i]; ns += 1; nzw += y != 0.0
                    laws["slot-26 law F(F(dry*in)+F(wet*y))"] += f2u(out) != f2u(F(F(dry * inp) + F(wet * y)))
                    laws["crossfade F(F((1-v)in)+F(v y))"] += f2u(out) != f2u(F(F(F(1.0 - F(mix)) * inp) + F(F(mix) * y)))
                    laws["unity dry F(in+F(v y))"] += f2u(out) != f2u(F(inp + F(F(mix) * y)))
        return laws, ns, nzw, (float(dry), float(wet))
    s18 = {mix: slot18_run(mix) for mix in (0.3, 0.9, 1.0)}
    for k_, (laws, ns, nzw, dw) in s18.items():
        P("  slot 18 (activated, 0x106c88 neutralised), Mixratio %g (dry/wet %s), blocks 40..59 (%d non-zero wet samples): "
          "mismatching samples per law %s of %d" % (k_, dw, nzw, laws, ns))
    J["slot18_mix"] = {str(k_): v for k_, v in s18.items()}
    check(all(v[0]["slot-26 law F(F(dry*in)+F(wet*y))"] == 0 and v[2] > 1000 for v in s18.values()) and
          s18[0.3][0]["crossfade F(F((1-v)in)+F(v y))"] > 0 and s18[0.9][0]["unity dry F(in+F(v y))"] > 0,
          "Mixratio law at slot-18 level: out = dry*in + wet*y with the slot-26 values (dry 1 until wet reaches 1 at v = 0.75, then dry "
          "falls to 0 at v = 1); neither a plain crossfade nor unity dry + v*wet fits")
    # reset retains the ring
    xr, mr = new_pair(); Ls, Rs = signal("noise", 800)
    xr.set(0, 0.5); mr.set_param(0, 0.5)
    for blk in range(800):
        xr.set(7, 120.0); mr.set_param(7, 120.0)
        xr.process(Ls[blk * N:(blk + 1) * N], Rs[blk * N:(blk + 1) * N]); mr.process(Ls[blk * N:(blk + 1) * N], Rs[blk * N:(blk + 1) * N])
    def nzr(xx):
        n_, raw = xx.ring(); flt = struct.unpack("<%df" % (2 * n_), raw); return sum(1 for k in range(n_) if flt[2 * k] != 0.0)
    before = nzr(xr); calls = []
    for a_ in (0x102d04, 0x103d20, 0xec94c, 0xe9fb8, 0xea670, 0xf50b8, 0x10623c, 0x102ebc):
        xr.e.add_watch(a_, lambda em, a_=a_: calls.append(hex(a_)))
    xr.e.vcall(xr.o, 27); mr.reset()
    se = xr.state(); after = nzr(xr)
    P("  slot 27: call chain %s; ring non-zero frames before %d after %d; w %d, read pos %r, gate cur %r, cnt %d, warm %d, full %d" %
      (calls, before, after, se["r.w+0x1c"], se["r.pos+0x28"], u2f(se["g.cur"]), se["m.cnt+0x80"], se["m.warm+0x7c"], se["m.full+0x7d"]))
    check(before == after == 46600 and se["r.w+0x1c"] == 0 and diff(se, model_state(mr)) == [] and xr.ring() == model_ring(mr),
          "slot 27 reset = slot 32 (twice) + module reset 0xec94c: ring indices rewound (write 0, read -D), samples KEPT, gate closed at "
          "once, counter/warm/full 0, feedback ramp snapped; model state and ring equal")
    # EffectBase slot 5 activation path
    calls.clear(); xr.e.vcall(xr.o, 5, 0, 1)
    P("  EffectBase slot 5 (activation, F022) calls: %s" % calls)
    check("0x102d04" in calls and "0xec94c" in calls, "EffectBase slot 5 (activation) runs slot 27, i.e. activation rewinds the delay "
          "and closes its gate (but keeps the ring samples)")
    # slot 10
    s0 = xr.state(); r10 = xr.e.vcall(xr.o, 10)[0]; s1 = xr.state()
    check(r10 == 2 and s0 == s1, "slot 10 (retrigger) = EffectBase default 0x10594c: returns 2, changes nothing")
    # delay-time change: buffer kept, mute-jump (gate trace)
    xt, mt = new_pair(); xt.set(0, 0.2); mt.set_param(0, 0.2); gtrace = []
    Ln, Rn = signal("noise", 400)
    for blk in range(400):
        if blk == 300: xt.set(0, 0.05); mt.set_param(0, 0.05)
        xt.set(7, 120.0); mt.set_param(7, 120.0)
        xt.process(Ln[blk * N:(blk + 1) * N], Rn[blk * N:(blk + 1) * N]); mt.process(Ln[blk * N:(blk + 1) * N], Rn[blk * N:(blk + 1) * N])
        if 299 <= blk <= 306:
            s_ = xt.state(); gtrace.append((blk, u2f(s_["g.cur"]), s_["g.state"], s_["m.D+0x24"], s_["m.pend+0x28"]))
    P("  time change 208 ms -> 60 ms at block 300 (block, gate, gate state, D, pending): %s" % gtrace)
    check(gtrace[1][4] == 1 and gtrace[3][3] == mt.mod.samples(F(60.0)) and gtrace[-1][1] == 1.0,
          "delay-time change = fade out (147 samples) -> read pointer jump -> fade in (147 samples); no glide, no buffer clear")

    # ---------------------------------------------------------------------------------------------------------- C6
    P("\n== C6 alternatives")
    # LowCut / Spread inactive (emulated): outputs identical
    def emu_out(pre, nb=200):
        xx = EmuDelay(); Lq, Rq = signal("noise", nb); out = b""
        for idx, v in pre: xx.set(idx, v)
        for blk in range(nb):
            xx.set(7, 120.0); eL, eR = xx.process(Lq[blk * N:(blk + 1) * N], Rq[blk * N:(blk + 1) * N])
            out += struct.pack("<%df" % (2 * N), *(eL + eR))
        return out
    base = emu_out([(0, 0.05), (1, 0.6)])
    alt = emu_out([(0, 0.05), (1, 0.6), (3, 1.0), (4, 1.0)])
    alt2 = emu_out([(0, 0.05), (1, 0.6), (3, 0.5), (4, 0.25)])
    check(base == alt == alt2, "alternative 'LowCut/Spread act on the signal' refuted: emulated output identical for LowCut/Spread "
          "0/0, 1/1, 0.5/0.25 (200 noise blocks)")
    # integer read: frac always 0
    xi, mi = new_pair(); fracs = set(); Lq, Rq = signal("noise", 300)
    for blk in range(300):
        if blk in (50, 100, 101, 200): v = {50: 0.33, 100: 0.777, 101: 0.0101, 200: 0.6}[blk]; xi.set(0, v); mi.set_param(0, v)
        xi.set(7, 120.0); xi.process(Lq[blk * N:(blk + 1) * N], Rq[blk * N:(blk + 1) * N])
        p_ = xi.state()["r.pos+0x28"]; fracs.add(p_ - int(p_))
    check(fracs == {0.0}, "alternative 'fractional (interpolated) delay' refuted: read position always integral (ms -> trunc samples; "
          "the interpolating read 0xeaa84 runs with frac = 0, i.e. an integer-sample delay)")
    if a.mutants or True:
        mres = []
        for nm_, fn_, case, kind in MUTANTS:
            c_ = find_case(case)
            r_, _ = run_case(c_[0], c_[1], c_[2], c_[3], kind, c_[4], mut=fn_)
            caught = r_["mismatched_samples"] > 0 or r_["first_state_diff"] is not None or not r_["final_ring_equal"]
            mres.append((nm_, case, kind, r_["mismatched_samples"], r_["max_abs_err"], caught))
            P("  mutant %-42s on %-28s %-6s mism %6d  max|err| %-10.4g  -> %s" % (nm_, case, kind, r_["mismatched_samples"],
                                                                               r_["max_abs_err"], "CAUGHT" if caught else "not caught"))
        J["mutants"] = mres
        check(all(m_[5] for m_ in mres), "all %d alternative models are refuted by emulation" % len(mres))

    # ---------------------------------------------------------------------------------------------------------- C7
    P("\n== C7 SendFxDelay relation (static)")
    calls_all = im.direct_calls()
    def callees(fn):
        s, e_ = im.func_of(fn)
        if s is None: return set()
        return set(t for site, t, k in calls_all if s <= site < e_ and k in ("bl", "blx"))
    def closure(roots, depth=3):
        seen = set(roots); fr_ = set(roots)
        for _ in range(depth):
            nx = set()
            for f_ in fr_: nx |= callees(f_)
            nx -= seen; seen |= nx; fr_ = nx
        return seen
    core = {0xec734: "DelayModuleStereo ctor", 0xec9bc: "setDelay", 0xecacc: "chunk", 0xecaf4: "read+gate", 0xecd2c: "write",
            0xec94c: "module reset", 0xea2a4: "RingBuffer ctor", 0xeaa84: "ring read interp", 0xea77c: "ring read plain",
            0xea670: "ring setDelay", 0xf3ce4: "HiCut ctor", 0xf438c: "HiCut process", 0xf41ac: "HiCut setStep",
            0xf5b9c: "gain ramp multiply"}
    ins_roots = [0x103488, 0x102cc0, 0x102d3c, 0x102f30, 0x102d04, 0x103d20, 0x104774]
    send_vt = [im.u32(0x841ea8 + 4 * k) for k in range(15)] + [im.u32(0x841eec + 4 * k) for k in (11, 23, 24, 25, 26, 27)]
    send_roots = [0x1054ac] + [v for v in send_vt if v]
    ci = closure(ins_roots); cs = closure(send_roots)
    rows7 = [(hex(k_), nm_, k_ in ci, k_ in cs) for k_, nm_ in core.items()]
    for r_ in rows7: P("  %-9s %-20s Insert %-5s Send %s" % r_)
    J["send_relation"] = rows7
    P("  SendFxDelay primary vtable 0x841ea8 shares DelayEchoBase slots 2/3/4/6/7 (0x103980/0x1042f0/0x104108/0x103878/0x103880) "
      "with vtable 0x841de0; strings DelayTimeLch/Rch, FeedbackGainLch/Rch (0x841e50..) and maxms 4000.0 (0x841fa8)")
    shared = [r_ for r_ in rows7 if r_[2] and r_[3]]
    P("  shared core routines: %d of %d" % (len(shared), len(rows7)))
    J["send_shared"] = len(shared)

    # ---------------------------------------------------------------------------------------------------------- outputs
    P("\nRESULT: %d failed checks" % len(fails))
    for f_ in fails: P("  FAILED: " + f_)
    cat = b"".join(open(os.path.join(a.out, k_), "rb").read() for k_ in sorted(hashes))
    J["f32_hashes"] = hashes; J["f32_concat_sha256"] = sha(cat) if hashes else None
    P("f32 files: %d, sorted concatenation sha256 %s" % (len(hashes), J["f32_concat_sha256"]))
    open(os.path.join(a.out, "h039_report.txt"), "w").write("\n".join(rep) + "\n")
    open(os.path.join(a.out, "h039.json"), "w").write(json.dumps(J, indent=1, sort_keys=True, default=str))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
