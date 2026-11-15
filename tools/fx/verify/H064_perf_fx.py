#!/usr/bin/env python3
"""H064 — Performance FX (PerformanceFxLoFi): class inventory, owner/placement, kernel sharing, parameters, bit-exact model.

Sections (criteria of kb/cycles/023.md):
  C1  class inventory: every typeinfo name containing Perform/Perf; PerformanceFxLoFi vtable vs LoFi vs EffectBase slot by slot.
  C2  owner/placement: every reference to the ctor 0xfd1f8 (direct bl/b, aligned data words in the whole file, movw/movt and
      literal pools in .text, pc-relative add/sub), to the vtable 0x8419d8 and to its own slot functions outside the vtable.
  C3  kernel sharing: direct callees of PerformanceFxLoFi slot 25 0xfc434 vs LoFi slot 25 0xfc0f4 / kernel 0xfbf64; S&H loop shape.
  C4  parameters: ctor registration (name, index, ctor "last"/default/range), slot-14 index map, and emulated read-back of every
      derived field at 8 values per parameter (incl. range ends) against closed-form formulas.
  C5  model vs emulation: harness/models/perf_lofi.py vs real slot 25 on sine/noise/impulse/silence/L-only, >= 6 settings,
      60 blocks each, plus mid-run parameter changes; outputs AND full state compared after every block.
  C6  lifecycle: inherited EffectBase slots 5-9 (same entries as LoFi), own slot 27 reset emulated vs model, slot 23/24.
  C7  alternatives: LoFi-kernel order mutants, "same code" (callee sets), owner search, other Performance FX types.
Outputs only to --out (default harness/out/H064/).  Run: .venv/bin/python -B harness/H064_perf_fx.py --out DIR
  --regress: re-run H005 (recorded hashes) and H005 --regress (= H043, H055, H010, H009, H021..H041 chain).
"""
import argparse, hashlib, json, math, os, random, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
from emu import Emu, f2u, u2f, init_array                  # noqa: E402
from sp16img import Image, const_sites, litadd_sites       # noqa: E402
import perf_lofi as M                                      # noqa: E402

N = 64
FS = 44100
NBLK = 60
CTOR, VT, TI = 0xfd1f8, 0x8419d8, 0x841b14
LOFI_VT, EB_VT = 0x841a68, 0x841fb8
SIZE = 0x400                       # harness allocation; the ctor writes up to +0x349 (checked below), real size unknown (never allocated)
PARAM_OFF = [0x1b8, 0x214, 0x270, 0x2cc]
STATIC_INIT = 0x137cc
SLOT14 = 14


def sha(b): return hashlib.sha256(b).hexdigest()
def F(x): return u2f(f2u(x))


# ======================================================================================================================
class EmuPerf:
    def __init__(self, heap_fill=0):
        self.e = e = Emu(heap_fill=heap_fill)
        assert STATIC_INIT in init_array(e)
        e.call(STATIC_INIT)
        self.o = e.malloc(SIZE, "harness: PerformanceFxLoFi object")
        e.call(CTOR, self.o, FS, N)
        self.bl = e.malloc(4 * N, "L"); self.br = e.malloc(4 * N, "R")

    def set_param(self, idx, v):
        r0, _ = self.e.vcall(self.o, SLOT14, idx, f2u(v)); return r0

    def process(self, L, R):
        e = self.e; n = len(L)
        e.set_floats(self.bl, L); e.set_floats(self.br, R)
        r0, _ = e.vcall(self.o, 25, self.bl, self.br, n)
        assert r0 == 0
        return e.floats(self.bl, n), e.floats(self.br, n)

    def reset(self):
        r0, _ = self.e.vcall(self.o, 27); return r0

    def u(self, a): return self.e.u32(a)
    def i(self, a): v = self.e.u32(a); return v - (1 << 32) if v & 0x80000000 else v
    def b(self, a): return self.e.rd(a, 1)[0]

    def state(self):
        o, u, i, b = self.o, self.u, self.i, self.b
        H, Q, FA, FB = (u(o + x) for x in (0x328, 0x32c, 0x330, 0x334))
        st = {"dry+0x10": u(o + 0x10), "wet+0x14": u(o + 0x14),
              "L+0x338": u(o + 0x338), "R+0x33c": u(o + 0x33c), "CM+0x340": u(o + 0x340), "RES+0x344": u(o + 0x344),
              "flag_sh+0x348": b(o + 0x348), "flag_filt+0x349": b(o + 0x349),
              "sh.phase": u(H + 8), "sh.step": u(H + 0xc), "sh.holdL": u(H + 0x10), "sh.holdR": u(H + 0x14),
              "sh.fs": [i(H), i(H + 4)],
              "cr.bits": i(Q), "cr.scale": u(Q + 4), "cr.inv": u(Q + 8)}
        for nm, C in (("fa", FA), ("fb", FB)):
            st.update({nm + ".pending": i(C + 0x10), nm + ".cur": i(C + 0x14), nm + ".cut_t": u(C + 0x18), nm + ".cut_c": u(C + 0x1c),
                       nm + ".cut_mult": u(C + 0x20), nm + ".cut_steps": i(C + 0x24), nm + ".q_t": u(C + 0x28),
                       nm + ".q_c": u(C + 0x2c), nm + ".q_mult": u(C + 0x30), nm + ".q_steps": i(C + 0x34),
                       nm + ".next": u(C + 0x38), nm + ".maxsteps": i(C + 0x3c), nm + ".flag40": b(C + 0x40),
                       nm + ".dirty41": b(C + 0x41)})
            g = u(C + 0xc)
            st.update({nm + ".gate.state": i(g + 0x20), nm + ".gate.cur": u(g + 0x24), nm + ".gate.target": u(g + 0x28),
                       nm + ".gate.inc": u(g + 0x2c), nm + ".gate.rem": i(g + 0x30)})
            cur = i(C + 0x14); s = u(u(C) + 4 * cur)
            st[nm + ".sub.vptr"] = hex(u(s))
            st[nm + ".sub.coef"] = [u(s + 0x28 + 4 * j) for j in range(5)]
            st[nm + ".sub.hist"] = [[u(u(s + 0x10 + 4 * j) + 4 * q) for q in range(4)] for j in range(4)] + \
                [[u(u(s + 0x20)), u(u(s + 0x20) + 4)]]
        for k, off in enumerate(PARAM_OFF):
            st["p%d.last,cur" % k] = [u(o + off + 0x24), u(o + off + 0x28)]
        return st


SUB_VPTR = {"hpf": "0x840c48", "lpf": "0x840c28", "bpf": "0x841918", "off": "0x841938"}


def model_state(m):
    st = {"dry+0x10": f2u(m.dry) if m.dry is not None else None, "wet+0x14": f2u(m.wet) if m.wet is not None else None,
          "L+0x338": f2u(m.L), "R+0x33c": f2u(m.R), "CM+0x340": f2u(m.CM), "RES+0x344": f2u(m.RES),
          "flag_sh+0x348": m.flag_sh, "flag_filt+0x349": m.flag_filt,
          "sh.phase": f2u(m.sh_phase), "sh.step": f2u(m.sh_step), "sh.holdL": f2u(m.sh_hold[0]), "sh.holdR": f2u(m.sh_hold[1]),
          "sh.fs": [m.fs, m.fs], "cr.bits": m.bits, "cr.scale": f2u(m.scale), "cr.inv": f2u(m.inv)}
    for nm, c in (("fa", m.fa), ("fb", m.fb)):
        r = c.gate.r
        st.update({nm + ".pending": c.pending, nm + ".cur": c.cur, nm + ".cut_t": f2u(c.cut_t), nm + ".cut_c": f2u(c.cut_c),
                   nm + ".cut_mult": f2u(c.cut_mult), nm + ".cut_steps": c.cut_steps, nm + ".q_t": f2u(c.q_t),
                   nm + ".q_c": f2u(c.q_c), nm + ".q_mult": f2u(c.q_mult), nm + ".q_steps": c.q_steps,
                   nm + ".next": f2u(c.next), nm + ".maxsteps": c.maxsteps, nm + ".flag40": c.flag40, nm + ".dirty41": c.dirty41,
                   nm + ".gate.state": r.state, nm + ".gate.cur": f2u(r.cur), nm + ".gate.target": f2u(r.target),
                   nm + ".gate.inc": f2u(r.inc), nm + ".gate.rem": r.rem})
        s = c.subs[c.cur]
        st[nm + ".sub.vptr"] = SUB_VPTR[s.kind]
        st[nm + ".sub.coef"] = [f2u(x) for x in (s.b0, s.b1, s.b2, s.a1, s.a2)]
        st[nm + ".sub.hist"] = [[f2u(s.v[j][0]), f2u(s.v[j][1]), f2u(s.y[j][0]), f2u(s.y[j][1])] for j in range(4)] + \
            [[f2u(s.yprev[0]), f2u(s.yprev[1])]]
    for k, p in enumerate(m.params):
        st["p%d.last,cur" % k] = [f2u(p.last), f2u(p.cur)]
    return st


def diff_state(a, b):
    d = []
    for k in a:
        if k in ("dry+0x10", "wet+0x14") and b.get(k) is None:
            continue                                     # model has not run slot 26 yet; emulation holds the EffectBase ctor value
        if a[k] != b.get(k): d.append(k)
    return d


# ======================================================================================================================
def signal(kind, nblk=NBLK, seed=1234):
    tot = N * nblk
    if kind == "impulse":
        L = [0.0] * tot; R = [0.0] * tot
        for k0 in range(0, tot, 997): L[k0] = 0.9; R[k0] = -0.45
    elif kind == "silence":
        L = [0.0] * tot; R = [0.0] * tot
    elif kind == "sine":
        L = [0.5 * math.sin(2 * math.pi * 1000.0 * k / FS) for k in range(tot)]
        R = [0.5 * math.cos(2 * math.pi * 440.0 * k / FS) for k in range(tot)]
    elif kind == "noise":
        g = random.Random(seed)
        L = [g.uniform(-0.9, 0.9) for _ in range(tot)]; R = [g.uniform(-0.9, 0.9) for _ in range(tot)]
    elif kind == "lonly":
        L = [0.7 * math.sin(2 * math.pi * 3000.0 * k / FS) for k in range(tot)]; R = [0.0] * tot
    else:
        raise ValueError(kind)
    return [F(x) for x in L], [F(x) for x in R]


SETTINGS = {   # (LEVEL, REDUCTION, CUTOFFMAX, RESONANCE); values equal to a ctor 'last' (L 0.0, others 0.5) are not applied (F026)
    "S1_lvl0.02": (0.02, 0.6, 0.4, 0.3),
    "S2_lvl0.1_cm0": (0.1, 1.0, 0.0, 0.0),
    "S3_lvl0.3_cm1": (0.3, 0.2, 1.0, 1.0),
    "S4_lvl0.5": (0.5, 0.7, 0.3, 0.1),
    "S5_lvl0.75": (0.75, 1.0, 0.6, 0.9),
    "S6_lvl1_cm1": (1.0, 1.0, 1.0, 0.0),
    "S7_lvl1_cm0_res1": (1.0, 0.0, 0.0, 1.0),
    "S8_defaults_unapplied": (0.0, 0.5, 0.5, 0.5),
}
EVENTS = {     # (block, idx, value)
    "E1_sweep": [(0, 0, 0.2), (0, 1, 0.8), (0, 2, 0.3), (0, 3, 0.6), (12, 0, 0.9), (25, 2, 0.95), (33, 3, 0.05), (41, 1, 0.1),
                 (47, 0, 0.0), (53, 0, 0.6), (53, 2, 0.0)],
    "E2_level_ramp": [(b, 0, b / 59.0) for b in range(60)] + [(0, 1, 1.0), (0, 2, 0.7), (0, 3, 0.8)],
}


def run_case(sig, setp=(), events=(), nblk=NBLK, model_order="perf", want_state=True, heap_fill=0, resets=()):
    L, R = signal(sig, nblk)
    em = EmuPerf(heap_fill=heap_fill); mo = M.PerfLoFi()
    for idx, v in setp:
        assert em.set_param(idx, v) == 0; mo.set_param(idx, v)
    eo = ([], []); mo_ = ([], []); sdiff = []
    for b in range(nblk):
        for (eb, idx, v) in events:
            if eb == b: em.set_param(idx, v); mo.set_param(idx, v)
        if b in resets:
            assert em.reset() == 0; mo.reset()
        x = em.process(L[b * N:(b + 1) * N], R[b * N:(b + 1) * N])
        y = mo.process(L[b * N:(b + 1) * N], R[b * N:(b + 1) * N], order=model_order)
        eo[0].extend(x[0]); eo[1].extend(x[1]); mo_[0].extend(y[0]); mo_[1].extend(y[1])
        if want_state:
            d = diff_state(em.state(), model_state(mo))
            if d: sdiff.append((b, d[:6]))
    nd = sum(1 for a, c in zip(eo[0] + eo[1], mo_[0] + mo_[1]) if f2u(a) != f2u(c))
    mx = max([abs(a - c) for a, c in zip(eo[0] + eo[1], mo_[0] + mo_[1]) if not (math.isnan(a) or math.isnan(c))] + [0.0])
    return {"emu": eo, "model": mo_, "ndiff": nd, "maxerr": mx, "state_diff_blocks": len(sdiff), "state_diff_first": sdiff[:3],
            "em": em, "mo": mo}


# ======================================================================================================================
def c1_inventory(im, rep, res, check):
    tis = json.load(open(os.path.join(HERE, "out", "H001", "typeinfo_all.json"))) \
        if os.path.exists(os.path.join(HERE, "out", "H001", "typeinfo_all.json")) else None
    # own scan of typeinfo name strings (independent of H001 output): mangled class names containing Perform / Perf
    names = sorted(set(m.group().decode() for m in re.finditer(rb"(?<![A-Za-z0-9_])\d+\w*?Perf\w*", im.data)))
    rep.append("C1 typeinfo-style names containing 'Perf': %s" % names)
    res["c1_names"] = names
    wrd = lambda a: im.u32(a)
    # typeinfo of PerformanceFxLoFi: vptr (si), name, base
    ti_vptr, ti_name, ti_base = wrd(TI), wrd(TI + 4), wrd(TI + 8)
    rep.append("C1 typeinfo 0x%x: vptr 0x%x (si = 0xb81948), name 0x%x '%s', base 0x%x (EffectBase typeinfo 0x842048)"
               % (TI, ti_vptr, ti_name, im.cstr(ti_name), ti_base))
    check([n for n in names if "PerformanceFx" in n] == ["17PerformanceFxLoFi"],
          "C1 exactly one PerformanceFx* class name in the binary: PerformanceFxLoFi")
    check(ti_vptr == 0xb81948 and ti_base == 0x842048 and im.cstr(ti_name) == "17PerformanceFxLoFi",
          "C1 PerformanceFxLoFi is an si subclass of EffectBase")
    check(wrd(VT - 4) == TI and wrd(VT - 8) == 0, "C1 vtable 0x8419d8: typeinfo at vt-4, offset-to-top 0")
    def slots(vt, n): return [wrd(vt + 4 * k) for k in range(n)]
    P, Lo, E = slots(VT, 33), slots(LOFI_VT, 32), slots(EB_VT, 32)
    rows = []
    own = []
    for k in range(33):
        p = P[k]; lo = Lo[k] if k < 32 else None; eb = E[k] if k < 32 else None
        tag = "inherited (=EffectBase)" if p == eb else ("= LoFi" if p == lo else "own")
        if tag == "own": own.append(k)
        rows.append("  slot %2d  Perf 0x%06x  LoFi %s  EffectBase %s  -> %s" % (k, p, "0x%06x" % lo if lo else "-",
                                                                                "0x%06x" % eb if eb else "-", tag))
    rep.append("C1 vtable comparison (33 vs 32 vs 32 slots):"); rep.extend(rows)
    res["c1_own_slots"] = own
    check(own == [0, 1, 23, 24, 25, 26, 27, 32], "C1 own slots = 0,1,23,24,25,26,27,32 (all others inherited from EffectBase)")
    check(all(P[k] == Lo[k] for k in range(32) if k not in (0, 1, 23, 24, 25, 26, 27)),
          "C1 every non-own slot is the same entry LoFi uses (both inherit EffectBase)")
    check(im.u32(VT + 4 * 33) == 0, "C1 vtable ends after 33 slots (next word 0)")


def c2_owner(im, rep, res, check):
    calls = im.direct_calls()
    tgt = {CTOR: "ctor", 0xfdef8: "dtor D1 (slot 0)", 0xfe0dc: "dtor D0 (slot 1)", 0xfc434: "slot 25", 0xfac70: "slot 26",
           0xfb02c: "slot 27", 0xfacec: "slot 32", 0xfdbfc: "slot 23", 0xfdc04: "slot 24", 0xfc278: "param apply"}
    out = {}
    for t, nm in tgt.items():
        dc = [(hex(s), k) for s, tt, k in calls if tt == t]
        out[nm] = {"direct": dc}
    # aligned data words anywhere in the file (vtables, function tables) equal to the ctor or any slot function
    d = im.data
    for t, nm in tgt.items():
        hits = []
        for v in (t, t | 1):
            pat = struct.pack("<I", v); i = d.find(pat)
            while i >= 0:
                if i % 4 == 0: hits.append(i)
                i = d.find(pat, i + 1)
        vas = []; unwind = []
        ex = [im.sec[k] for k in (".ARM.extab", ".ARM.exidx") if k in im.sec]
        for off in hits:
            for va, sz, fo in im.segs:
                if fo <= off < fo + sz:
                    v = va + off - fo
                    (unwind if any(a <= v < b for a, b in ex) else vas).append(hex(v))
        out[nm]["data_words"] = vas; out[nm]["unwind_table_words(ignored)"] = unwind
    cs = const_sites(im, list(tgt) + [VT, TI])
    for t, nm in tgt.items(): out[nm]["text_const"] = [(k, hex(a)) for k, a in cs[t]]
    # pc-relative adr (add/sub rX, pc, #imm) resolving to the ctor
    adr = []
    lo, hi = im.sec[".text"]
    for i in im.md.disasm(d[im.off(lo):im.off(hi)], lo):
        if i.mnemonic in ("add", "sub", "adr") and "pc" in i.op_str:
            m = re.match(r"\w+, pc, #(-?0x[0-9a-f]+|-?\d+)$", i.op_str)
            if m:
                v = i.address + 8 + (int(m.group(1), 0) if i.mnemonic != "sub" else -int(m.group(1), 0))
                if v in tgt: adr.append((hex(i.address), hex(v)))
    res["c2_refs"] = out; res["c2_adr"] = adr
    vt_sites = [(k, hex(a), hex(im.func_of(a)[0])) for k, a in cs[VT]]
    la = litadd_sites(im, [VT, VT - 8])
    rep.append("C2 vtable 0x8419d8 literal/movw sites (site, containing function): %s; ldr+add sites: %s"
               % (vt_sites, {hex(k): v for k, v in la.items()}))
    rep.append("C2 typeinfo 0x841b14 materialised in .text: %s" % [(k, hex(a)) for k, a in cs[TI]])
    for nm, v in out.items():
        rep.append("C2 refs to %-16s direct=%s data_words=%s text_const=%s (coincidental words in .ARM.extab/.exidx: %d)"
                   % (nm, v["direct"], v["data_words"], v["text_const"], len(v["unwind_table_words(ignored)"])))
    rep.append("C2 pc-relative address formations to these functions: %s" % adr)
    check(not out["ctor"]["direct"] and not out["ctor"]["data_words"] and not out["ctor"]["text_const"] and not adr,
          "C2 ctor 0xfd1f8 has no direct call, no data pointer, no materialised constant, no pc-relative formation")
    check(sorted(im.func_of(int(a, 16))[0] for _, a, _ in vt_sites) == sorted([0xfd1f8, 0xfdef8, 0xfe0dc]) and
          not any(la.values()), "C2 vtable 0x8419d8 is stored only by its ctor and its two dtors")
    slot_data = {nm: v["data_words"] for nm, v in out.items() if nm not in ("ctor", "param apply")}
    exp = {"dtor D1 (slot 0)": [hex(VT)], "dtor D0 (slot 1)": [hex(VT + 4)], "slot 25": [hex(VT + 100)], "slot 26": [hex(VT + 104)],
           "slot 27": [hex(VT + 108)], "slot 32": [hex(VT + 128)], "slot 23": [hex(VT + 92)], "slot 24": [hex(VT + 96)]}
    check(slot_data == exp, "C2 each own slot function is referenced only by its own vtable entry")
    check(out["dtor D1 (slot 0)"]["direct"] == [("0xfe0f8", "bl")] or all(im.func_of(int(s, 16))[0] == 0xfe0dc
                                                                       for s, _ in out["dtor D1 (slot 0)"]["direct"]),
          "C2 D1 dtor is called only from the D0 dtor")
    # the three FX processors' ctors and HexaTrackAudioSystem graph build: none reference the Perf ctor or vtable
    for nm, a in (("InsertFxProcessor ctor", 0x118b0c), ("MasterFxProcessor ctor", 0x114bc0), ("SendFxProcessor ctor", 0x11bbe4)):
        s, e = im.func_of(a)
        cl = sorted(set(hex(t) for site, t, k in calls if s <= site < e and k == "bl" and 0xf0000 <= t < 0x120000))
        has = any(t == CTOR for site, t, k in calls if s <= site < e)
        rep.append("C2 %s 0x%x..0x%x calls FX ctors %s; calls PerformanceFxLoFi ctor: %s" % (nm, s, e, cl, has))
        check(not has and "0xfd640" in cl, "C2 %s builds LoFi (0xfd640) but not PerformanceFxLoFi" % nm)


def c3_kernel(im, rep, res, check):
    calls = im.direct_calls()
    def callees(a):
        s, e = im.func_of(a)
        return [(hex(site), hex(t)) for site, t, k in calls if s <= site < e and k in ("bl", "b") and not (s <= t < e)]
    P = callees(0xfc434); L = callees(0xfc0f4); K = callees(0xfbf64)
    rep.append("C3 Perf slot 25 0xfc434 direct callees: %s (+ vcall [vt+0x68] = slot 26)" % P)
    rep.append("C3 LoFi slot 25 0xfc0f4 direct callees: %s" % L)
    rep.append("C3 LoFi kernel 0xfbf64 direct callees: %s" % K)
    res["c3"] = {"perf25": P, "lofi25": L, "kernel": K}
    pt = [t for _, t in P]
    check("0xfbf64" not in pt, "C3 Perf slot 25 does not call the LoFi kernel 0xfbf64")
    check(pt == ["0xfc278", "0xfbb70", "0xfaf28", "0xfbb70"], "C3 Perf slot 25 = param apply 0xfc278, filter 0xfbb70, crusher 0xfaf28, filter 0xfbb70")
    check(sorted(set(pt) & set(t for _, t in K)) == ["0xfaf28", "0xfbb70"], "C3 shared blocks with the LoFi kernel: filter container 0xfbb70, crusher 0xfaf28")
    check("0xfb6e4" not in pt and "0xf521c" not in pt, "C3 no preamp 0xfb6e4 and no position gate 0xf521c in Perf slot 25")
    # S&H loop shape: mnemonic sequences (no bytes) of the Perf inline loop vs the LoFi inline loop
    pm = [i.mnemonic for i in im.disasm(0xfc4ac, 0xfc4e0)]
    lm = [i.mnemonic for i in im.disasm(0xfbfc4, 0xfc014)]
    rep.append("C3 S&H loop mnemonics Perf 0xfc4ac..0xfc4dc: %s" % " ".join(pm))
    rep.append("C3 S&H loop mnemonics LoFi 0xfbfc4..0xfc010: %s" % " ".join(lm))
    # param apply: compare the callee sets of the two parameter-apply functions
    rep.append("C3 Perf param apply 0xfc278 callees: %s" % sorted(set(t for _, t in callees(0xfc278))))
    rep.append("C3 LoFi param apply 0xfb20c callees: %s" % sorted(set(t for _, t in callees(0xfb20c))))
    rep.append("C3 Perf slot 32 0xfacec callees: %s; slot 27 0xfb02c callees: %s"
               % (sorted(set(t for _, t in callees(0xfacec))), sorted(set(t for _, t in callees(0xfb02c)))))
    # the filter containers are built by the shared ctor 0xfc5e4 in both classes
    ctor_c = sorted(set(hex(t) for site, t, k in calls if 0xfd1f8 <= site < 0xfd640 and k == "bl"))
    rep.append("C3 Perf ctor 0xfd1f8 callees: %s" % ctor_c)
    check("0xfc5e4" in ctor_c and "0x1067d8" in ctor_c, "C3 Perf ctor uses the EffectBase ctor 0x1067d8 and the LoFi filter-container ctor 0xfc5e4")


def c4_params(rep, res, check):
    e = EmuPerf(heap_fill=0xA5)
    raw = e.e.rd(e.o, SIZE)
    last = max(k for k in range(SIZE) if raw[k] != 0xA5)
    rep.append("C4 ctor writes object bytes up to +0x%x (harness allocation 0x%x)" % (last, SIZE))
    check(last == 0x349, "C4 highest byte written by the ctor is +0x349 (object >= 0x34c bytes)")
    names = []
    for k, off in enumerate(PARAM_OFF):
        p = e.o + off
        nm = None
        names.append({"idx": k, "off": hex(off), "vptr": hex(e.u(p)), "kind": e.u(p + 0x10),
                      "last": u2f(e.u(p + 0x24)), "cur": u2f(e.u(p + 0x28)), "min": u2f(e.u(p + 0x2c)), "max": u2f(e.u(p + 0x30)),
                      "default+0x3c": u2f(e.u(p + 0x3c))})
    rep.append("C4 parameters after ctor: %s" % names)
    res["c4_params"] = names
    check([n["last"] for n in names] == [0.0, 0.5, 0.5, 0.5] and all(n["min"] == 0.0 and n["max"] == 1.0 for n in names),
          "C4 ctor last values LEVEL 0, REDUCTION/CUTOFFMAX/RESONANCE 0.5; range 0..1")
    # slot-14 index map
    m = []
    for idx in range(6):
        b0 = e.e.rd(e.o, 0x34c); r = e.set_param(idx, 0.25); b1 = e.e.rd(e.o, 0x34c)
        ch = [hex(i) for i in range(0, 0x34c, 4) if b0[i:i + 4] != b1[i:i + 4]]
        m.append((idx, r, ch))
    rep.append("C4 slot 14 (index, return, changed words): %s" % m)
    check([x[2] for x in m] == [["0x1e0"], ["0x23c"], ["0x298"], ["0x2f4"], [], []] and m[4][1] == 3 and m[5][1] == 3,
          "C4 slot 14 index 0..3 -> LEVEL, REDUCTION, CUTOFFMAX, RESONANCE (+0x28 of each); index >= 4 returns 3")
    # read-back sweeps
    VALS = [0.0, 0.1, 0.25, 0.4999, 0.5, 0.7, 0.9, 1.0]
    BASE = [0.6, 0.8, 0.3, 0.2]
    n_ok = n_all = 0; fails = []; tab = []

    def formula(Lv, Rv, CM, RES):
        Lv, Rv, CM, RES = F(Lv), F(Rv), F(CM), F(RES)
        b = F(math.pow(float(F(5.0 / 12.0)), float(F(Lv + Lv))) * 12.0) if Lv < 0.5 else F(5.0)
        scale = F(M.powf(F(2.0), b) * F(0.5))
        step = F(F(Lv * F(44.1)) * Rv); step = F(1.0) if step < 1.0 else step
        fa = F(math.pow(float(F(0.015)), float(F(F(F(1.0) - CM) * Lv))) * 20000.0)
        fb = F(math.pow(400.0, float(F(Lv * CM))) * 20.0)
        def q(fc):
            x = F(F(0.707107) + F(RES * F(7.2928929)))
            if fc > 2500.0: x = max(F(x * F(F(F(20000.0) - fc) * F(5.7142857e-05))), F(0.707107))
            if fc < 700.0: x = max(F(x * F(F(fc - F(20.0)) * F(0.00147058826))), F(0.1))
            return x
        if Lv < F(4 / 255.0): dry, wet = 1.0, 0.0
        elif not Lv < F(37 / 255.0): dry, wet = 0.0, 1.0
        else:
            w = F(F(Lv - F(4 / 255.0)) / F(33 / 255.0)); dry, wet = F(1.0 - w), w
        return {"cr.bits": int(round(b)), "cr.scale": f2u(scale), "cr.inv": f2u(F(1.0 / scale)), "sh.step": f2u(step),
                "fa.cut_t": f2u(fa), "fb.cut_t": f2u(fb), "fa.q_t": f2u(q(fa)), "fb.q_t": f2u(q(fb)),
                "dry+0x10": f2u(F(dry)), "wet+0x14": f2u(F(wet))}

    for pi in range(4):
        for v in VALS:
            x = EmuPerf()
            for k in range(4): x.set_param(k, BASE[k])
            x.process([0.0] * N, [0.0] * N)
            x.set_param(pi, v); x.process([0.0] * N, [0.0] * N)
            st = x.state()
            cur = list(BASE); cur[pi] = v
            exp = formula(*cur)
            q_note = ""
            for k, ev in exp.items():
                if k.endswith(".q_t") and st[k] != ev:
                    # a Q change below FLT_EPSILON keeps the old target (vstrpl): accept if |new - old| < eps
                    pass
                n_all += 1
                if st[k] == ev: n_ok += 1
                else: fails.append((M.PARAM_NAMES[pi], v, k, u2f(st[k]), u2f(ev)))
            tab.append("  %-9s v=%-6g bits=%d scale=%-9.6g step=%-8.5g LPF=%-9.6g Hz q=%-7.5g HPF=%-8.6g Hz q=%-7.5g dry=%-6.4g wet=%-6.4g"
                       % (M.PARAM_NAMES[pi], v, st["cr.bits"], u2f(st["cr.scale"]), u2f(st["sh.step"]), u2f(st["fa.cut_t"]),
                          u2f(st["fa.q_t"]), u2f(st["fb.cut_t"]), u2f(st["fb.q_t"]), u2f(st["dry+0x10"]), u2f(st["wet+0x14"])))
    rep.append("C4 read-back table (base LEVEL 0.6, REDUCTION 0.8, CUTOFFMAX 0.3, RESONANCE 0.2; one parameter swept):")
    rep.extend(tab)
    rep.append("C4 read-back: %d/%d fields equal the closed-form formulas; mismatches: %s" % (n_ok, n_all, fails[:10]))
    res["c4_readback"] = {"ok": n_ok, "all": n_all, "fails": fails}
    check(n_ok == n_all, "C4 all %d read-back fields (8 values x 4 parameters x 10 fields) equal the formulas" % n_all)
    # unapplied-default quirk: LEVEL 0 and REDUCTION 0.5 set before the first block are never applied
    x = EmuPerf()
    x.set_param(0, 0.0); x.set_param(1, 0.5); x.process([0.0] * N, [0.0] * N); st = x.state()
    rep.append("C4 fresh object, LEVEL 0 / REDUCTION 0.5 set before block 0: bits %d, step %g, LPF %g, HPF %g, dry %g wet %g"
               % (st["cr.bits"], u2f(st["sh.step"]), u2f(st["fa.cut_t"]), u2f(st["fb.cut_t"]), u2f(st["dry+0x10"]), u2f(st["wet+0x14"])))
    check(st["cr.bits"] == 32 and u2f(st["fa.cut_t"]) == 1000.0, "C4 ctor-last values are never applied (crusher stays off, cutoffs keep ctor 1000 Hz)")


def c5_matrix(out, rep, res, check, quick=False):
    sigs = ["sine", "noise", "impulse", "silence", "lonly"]
    rows = []; tot = 0; bad = 0; allf32 = []
    cases = [(nm, [(k, v) for k, v in enumerate(s)], []) for nm, s in SETTINGS.items()] + \
        [(nm, [], ev) for nm, ev in EVENTS.items()]
    if quick: cases = cases[:2]; sigs = sigs[:2]
    for nm, setp, ev in cases:
        for sg in sigs:
            r = run_case(sg, setp=setp, events=ev)
            tot += 1
            ok = r["ndiff"] == 0 and r["state_diff_blocks"] == 0
            if not ok: bad += 1
            fn = "%s__%s.f32" % (nm, sg)
            blob = struct.pack("<%df" % (2 * N * NBLK), *(r["emu"][0] + r["emu"][1]))
            open(os.path.join(out, fn), "wb").write(blob); allf32.append(fn)
            rms_in = math.sqrt(sum(x * x for x in signal(sg)[0]) / (N * NBLK)) or 1.0
            rms_out = math.sqrt(sum(x * x for x in r["emu"][0]) / (N * NBLK))
            rows.append("  %-24s %-8s samples differ %d / %d, max|err| %.3g, state-diff blocks %d, L rms out/in %.4f %s"
                        % (nm, sg, r["ndiff"], 2 * N * NBLK, r["maxerr"], r["state_diff_blocks"], rms_out / rms_in,
                           "" if ok else "FIRST %s" % r["state_diff_first"]))
    rep.append("C5 model vs emulation (slot 25, 60 blocks x 64 stereo, outputs and full state after every block):")
    rep.extend(rows)
    # robustness: heap pre-filled with 0xA5 (uninitialised-field reads would show up as differences)
    r = run_case("noise", events=EVENTS["E1_sweep"], heap_fill=0xA5)
    ref = struct.pack("<%df" % (2 * N * NBLK), *(r["emu"][0] + r["emu"][1]))
    same = ref == open(os.path.join(out, "E1_sweep__noise.f32"), "rb").read() if not quick else True
    rep.append("C5 heap 0xA5 run (E1_sweep, noise): samples differ from model %d, state-diff blocks %d, emulated output identical to "
               "the zero-heap run: %s" % (r["ndiff"], r["state_diff_blocks"], same))
    check(r["ndiff"] == 0 and r["state_diff_blocks"] == 0 and same, "C5 result independent of heap contents (0xA5 fill)")
    res["c5"] = {"runs": tot, "bad": bad}
    check(bad == 0, "C5 %d runs (%d settings/event runs x %d signals) bit-exact, state equal every block" % (tot, len(cases), len(sigs)))
    return allf32


def c6_lifecycle(im, rep, res, check):
    # inherited lifecycle slots
    P = [im.u32(VT + 4 * k) for k in range(33)]; Lo = [im.u32(LOFI_VT + 4 * k) for k in range(32)]
    inh = {k: (hex(P[k]), P[k] == Lo[k]) for k in (5, 6, 7, 8, 9, 18, 22)}
    rep.append("C6 lifecycle slots (entry, same as LoFi): %s; own slot 27 0x%x (LoFi 0x%x)" % (inh, P[27], Lo[27]))
    check(all(v[1] for v in inh.values()), "C6 slots 5,6,7,8,9,18,22 are the EffectBase entries (same as LoFi)")
    # slot 27 reset: emulated vs model, mid-run
    r = run_case("noise", setp=[(0, 0.7), (1, 0.9), (2, 0.4), (3, 0.6)], events=[(20, 0, 0.3)], resets=(10, 30, 31), nblk=40)
    rep.append("C6 slot 27 reset at blocks 10, 30, 31 (noise, 40 blocks): samples differ %d, state-diff blocks %d"
               % (r["ndiff"], r["state_diff_blocks"]))
    check(r["ndiff"] == 0 and r["state_diff_blocks"] == 0, "C6 slot 27 reset model = emulation (outputs and state)")
    x = EmuPerf()
    a, _ = x.e.vcall(x.o, 23); b, _ = x.e.vcall(x.o, 24)
    rep.append("C6 slot 23 returns %d, slot 24 returns %d (LoFi: own 0x%x / 0x%x)" % (a, b, Lo[23], Lo[24]))
    check(a == 0 and b == 0, "C6 own slots 23/24 return 0")
    # generic EffectBase activation path works on this object (slot 22, 0x106c7c, slot 5 + slot 7, slot 18)
    x = EmuPerf(); e = x.e
    for k, v in enumerate((0.8, 1.0, 0.5001, 0.3)): x.set_param(k, v)
    e.vcall(x.o, 22, 0); e.call(0x106c7c, x.o, 1, f2u(10.0))
    L, R = signal("sine", 4)
    outs = []
    for b in range(4):
        s9, _ = e.vcall(x.o, 9)
        if s9 == 0: e.vcall(x.o, 5, 0, 1); e.vcall(x.o, 7, 0)
        e.set_floats(x.bl, L[b * N:(b + 1) * N]); e.set_floats(x.br, R[b * N:(b + 1) * N])
        e.vcall(x.o, 18, x.bl, x.br, N)
        outs.append(math.sqrt(sum(v * v for v in e.floats(x.bl, N)) / N))
    rep.append("C6 through the generic EffectBase path (slot 22, 0x106c7c, slot 9/5/7, slot 18): per-block L rms %s" %
               ["%.4f" % v for v in outs])
    check(all(math.isfinite(v) for v in outs), "C6 the class runs through the shared EffectBase slot 18 dispatcher like LoFi")


def c7_alternatives(rep, res, check):
    out = {}
    for order in ("sh_before_crush", "filters_last"):
        tot = 0
        for nm in ("S4_lvl0.5", "S6_lvl1_cm1", "E1_sweep"):
            setp = [(k, v) for k, v in enumerate(SETTINGS[nm])] if nm in SETTINGS else []
            ev = EVENTS.get(nm, [])
            r = run_case("noise", setp=setp, events=ev, model_order=order, want_state=False, nblk=20)
            tot += r["ndiff"]
        out[order] = tot
    rep.append("C7(a) order mutants vs emulation (noise, 3 settings x 20 blocks; differing samples): %s" % out)
    check(out["filters_last"] > 1000, "C7(a) LoFi 'post' order (crusher -> S&H -> filters) is refuted by emulation")
    check(out["sh_before_crush"] > 0, "C7(a) S&H-before-crusher order differs from emulation (weak mutant: the two stages commute "
          "except for the held value carried across parameter changes)")
    res["c7_mutants"] = out


def c7_search(im, rep, res, check):
    """C7(b)/(c): what else could be a 'performance FX'. Searched: all printable strings (>= 4 chars) of the main binary."""
    pat = re.compile(r"(?i:perform|perffx|perf_fx|touchfx|touch_fx|stutter|beatrepeat|beat_repeat|slicer|vinyl|tapestop|tape_stop|"
                     r"glitch)|Roll[A-Z_]|\bRoll\b|Ribbon")
    hits = []
    for m in re.finditer(rb"[\x20-\x7e]{4,}", im.data):
        s = m.group().decode()
        if pat.search(s): hits.append(s)
    cls = sorted(set(h for h in hits if re.fullmatch(r"N?\d+\w+E?", h)))          # mangled class names (typeinfo names)
    rep.append("C7(c) strings matching performance-FX words: %d; class-like names among them: %s" % (len(hits), cls))
    rep.append("C7(c) other matches (first 12, truncated): %s" % [h[:60] for h in hits if h not in cls][:12])
    res["c7_search"] = {"n": len(hits), "classes": cls}
    check(not any(re.search(r"Fx|Effect", c) and "PerformanceFxLoFi" not in c for c in cls),
          "C7(c) no other FX/Effect class among performance-word names (ribbon/strip classes are UI/sequencer controllers)")
    # parameter-name strings of the class: referenced only from its ctor?
    cs = const_sites(im, [0x841b48, 0x841b50])
    where = {hex(k): sorted(set(hex(im.func_of(a)[0]) for _, a in v)) for k, v in cs.items()}
    rep.append("C7(b) 'LEVEL' 0x841b48 / 'CUTOFFMAX' 0x841b50 materialised in functions: %s" % where)
    check(all(v == ["0xfd1f8"] for v in where.values()), "C7(b) the class's own parameter-name strings are used only by its ctor")


# ======================================================================================================================
H005_REC = {"h005_report.txt": ("099e46ae", "c53f"), "h005.json": ("a6c1e847", "f304")}
H005_F32 = ("9d751574", "91fa")
H021_REC = {"h021_report.txt": ("9273c853", "2677"), "h021.json": ("f3316770", "d839")}
H021_F32 = ("86f8975a", "74a4")


def regress(out):
    """Re-run H021 (recorded hashes), H005 (recorded hashes) and H005 --regress (= H043 + H043 --regress = H055, H010, H009, H021..H041)."""
    import subprocess, glob
    os.makedirs(os.path.join(out, "regress"), exist_ok=True)
    jobs = {"H021": ([os.path.join(HERE, "H021_lofi_model.py")], "H021"),
            "H005": ([os.path.join(HERE, "H005_send_reverb_model.py"), "--jobs", "5"], "H005"),
            "H005r": ([os.path.join(HERE, "H005_send_reverb_model.py"), "--regress"], "H005r")}
    procs = {}
    for k, (args, d) in jobs.items():
        dd = os.path.join(out, "regress", d); os.makedirs(dd, exist_ok=True)
        procs[k] = (subprocess.Popen([sys.executable, "-B"] + args + ["--out", dd],
                                     stdout=open(os.path.join(out, "regress", k + ".log"), "w"), stderr=subprocess.STDOUT), dd)
    rc = {k: p.wait() for k, (p, _) in procs.items()}

    def chk(d, rec, f32rec):
        got = {k: sha(open(os.path.join(d, k), "rb").read()) for k in rec if os.path.exists(os.path.join(d, k))}
        f32s = sha(b"".join(open(f, "rb").read() for f in sorted(glob.glob(os.path.join(d, "*.f32")))))
        ok = all(got.get(k, "").startswith(v[0]) and got.get(k, "").endswith(v[1]) for k, v in rec.items()) and \
            f32s.startswith(f32rec[0]) and f32s.endswith(f32rec[1])
        return ok, got, f32s
    ok21, g21, f21 = chk(procs["H021"][1], H021_REC, H021_F32)
    ok5, g5, f5 = chk(procs["H005"][1], H005_REC, H005_F32)
    rp = os.path.join(procs["H005r"][1], "h005_regress.txt"); rtxt = open(rp).read() if os.path.exists(rp) else ""
    ok5r = rc["H005r"] == 0 and "REGRESSION: all recorded hashes reproduced" in rtxt
    ok21 = ok21 and rc["H021"] == 0; ok5 = ok5 and rc["H005"] == 0
    txt = ("H021 rc %d %s %s f32 %s\nH005 rc %d %s %s f32 %s\nH005 --regress rc %d %s\n--- h005_regress.txt:\n%s\nREGRESSION: %s\n"
           % (rc["H021"], "OK " if ok21 else "BAD", g21, f21, rc["H005"], "OK " if ok5 else "BAD", g5, f5, rc["H005r"],
              "OK " if ok5r else "BAD", rtxt, "all recorded hashes reproduced" if ok21 and ok5 and ok5r else "MISMATCH"))
    open(os.path.join(out, "h064_regress.txt"), "w").write(txt); print(txt)
    return 0 if ok21 and ok5 and ok5r else 1


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H064"))
    ap.add_argument("--quick", action="store_true", help="C5 on 2 cases x 2 signals only")
    ap.add_argument("--regress", action="store_true", help="only re-run H021, H005 and H005 --regress and compare recorded hashes")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    if a.regress: return regress(a.out)
    im = Image()
    rep = ["H064 PerformanceFxLoFi — target sha256 %s" % sha(im.data)]
    res = {}; fails = []; passes = []

    def check(c, msg):
        (passes if c else fails).append(msg); rep.append(("PASS " if c else "FAIL ") + msg)
    c1_inventory(im, rep, res, check)
    c2_owner(im, rep, res, check)
    c3_kernel(im, rep, res, check)
    c4_params(rep, res, check)
    f32s = c5_matrix(a.out, rep, res, check, quick=a.quick)
    c6_lifecycle(im, rep, res, check)
    c7_alternatives(rep, res, check)
    c7_search(im, rep, res, check)
    rep.append("RESULT: %d failed checks (%d PASS)" % (len(fails), len(passes)))
    txt = "\n".join(rep) + "\n"
    open(os.path.join(a.out, "h064_report.txt"), "w").write(txt)
    json.dump(res, open(os.path.join(a.out, "h064.json"), "w"), indent=1, sort_keys=True, default=str)
    print(txt)
    print("h064_report.txt", sha(txt.encode()))
    print("h064.json", sha(open(os.path.join(a.out, "h064.json"), "rb").read()))
    print("f32 (sorted concat)", sha(b"".join(open(os.path.join(a.out, f), "rb").read() for f in sorted(f32s))))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
