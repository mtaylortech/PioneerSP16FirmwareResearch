# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Own-code model of the SP-16 1.60 SYNC toggle (parameter-manager slot 34) and the shared time/rate parameter specs.

What the manager does when the user presses SYNC on a time-based effect (F183-F186, H082; docs/effects/parameters.md):
  * store the new SYNC byte in prj::EffectData +0x28;
  * read the tempo T = max(float(tempo provider), 0.5) (FxProcessorBase 0x112a48; the Insert manager then clamps to >= 0.1 too);
  * take the time parameter's stored normalised value v (EffectData +0x38 = sub 0; Ducker also +0x48 = sub 2), turn it into an
    integer step of the range of the mode it is LEAVING, turn that into a musical/physical quantity, convert the quantity to the
    mode it is ENTERING at tempo T, pick the nearest step there, and store v' = (j - lo) / (hi - 1 - lo) (clamped to [0, 1])
    in EffectData and in the effect (slot 14 index 0, Ducker also 2), then send SYNC = float(sync) as slot-14 index 6.
  * free -> sync for a rate (Hz) effect: beats per LFO cycle b = (T / 60) * (1 / Hz) -> nearest table fraction;
    sync -> free: Hz = (T / 60) * (1 / b) -> round(Hz * K) as the free step.
  * free -> sync for a delay (ms): beats = ms * (T / 60) * 0.001 -> nearest fraction; sync -> free: ms = beats * (60 / T) * 1000 ->
    round(ms) as the free step (1 ms steps).
  * Ducker (ms <-> 1/16 notes, two parameters ATTACK sub 0 and RELEASE sub 2): sixteenths = ms * (T * 0.004 / 60) -> table
    search; ms = sixteenths * (60000 / T) * 0.25 -> trunc(ms * 10) as the free step (0.1 ms steps, truncation, not rounding).
The integer step i of a stored value is roundToInt(lo + v * (hi - 1 - lo)) (JUCE roundToInt: double + 1.5*2^52, round half to even)
-- the same law the effects themselves use, so the UI quantisation is v = (i - lo) / (hi - 1 - lo).

Every arithmetic step is float32 (rounded after each operation, VFP vmla is not fused). Family constants are the BasicParamSpec
helpers (1.60 addresses in FAMILIES); fraction tables are the .bss tables at 0xf61f18 + 4*idx filled by .init_array code; the
Ducker sixteenth tables are 0x8a9b20 / 0x8a9d20 (equal to ducker.TA / ducker.TR; the harness asserts this).
No firmware bytes are stored here: all numbers are our own derived values, asserted against the 1.60 target by
tools/fx/verify/H082_sync_convert.py.
"""
import ctypes, math, struct

import ducker as _DK                                         # TA / TR sixteenth tables (decimal segments, asserted vs 1.60)

_cf = ctypes.c_float
def F(x): return _cf(x).value
def fbits(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def ffrom(u): return struct.unpack("<f", struct.pack("<I", u & 0xffffffff))[0]


def fdiv(a, b):
    a = F(a); b = F(b)
    if b == 0.0:
        if a == 0.0 or a != a: return float("nan")
        return math.copysign(math.inf, a) * math.copysign(1.0, b)
    return F(a / b)


def fmul(a, b): return F(F(a) * F(b))
def fadd(a, b): return F(F(a) + F(b))


def round_to_int(x):
    """vcvt.f64.f32 + vadd.f64 1.5*2^52, low word (signed): round half to even for |x| < 2^31."""
    x = float(x)
    if x != x or math.isinf(x): raise ValueError("roundToInt of non-finite")
    r = round(x)                                               # Python round() = half-even
    r &= 0xffffffff
    return r - (1 << 32) if r & 0x80000000 else r


def trunc_s32(x):                                              # vcvt.s32.f32 (round toward zero, saturating)
    return _DK.trunc(x)


def step_of(lo, hi, v):
    """Integer step of a normalised value: roundToInt(f32(f32(lo) + f32(v * f32(hi - 1 - lo))))."""
    return round_to_int(fadd(float(lo), fmul(v, float(hi - 1 - lo))))


def norm_of(lo, hi, i):
    """Normalised value of integer step i: f32(f32(i - lo) / f32(hi - 1 - lo))."""
    return fdiv(float(i - lo), float(hi - 1 - lo))


def clamp01_out(v):                                            # bmi -> 0.0 ; vmovgt -> 1.0 (NaN passes)
    if v < 0.0: return 0.0
    if v > 1.0: return 1.0
    return v


clamp01_in = clamp01_out                                       # same code shape on the input (not on the Ducker)

# ------------------------------------------------------------------------------------------------------------- parameter families
# free: (range helper, (lo, hi), index->value kind/scale, value->index kind/scale); sync: (range helper, (lo, hi), fraction table)
# Fractions (num, den) in beats per LFO cycle (rates) or beats of delay (delays); order as stored (chain direction in 'order').
FAMILIES = {
    "chorus": dict(free=(0x349778, (1, 101)), i2v=(0x349798, "scale", 0.1), v2i=(0x3497b4, "round_scale", 10.0),
                   sync=(0x3497e0, (0, 10)), f2v=(0x349a44, 0xf61f50, 2), v2f=(0x349aa4, "desc"),
                   fracs=[(16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (3, 4), (1, 2), (1, 4), (1, 8), (1, 16)], kind="rate"),
    "flanger": dict(free=(0x349e30, (1, 101)), i2v=(0x349e50, "scale", 0.01), v2i=(0x349e6c, "round_scale", 100.0),
                    sync=(0x349e9c, (0, 7)), f2v=(0x34a088, 0xf61f78, 4), v2f=(0x34a0e8, "desc"),
                    fracs=[(64, 1), (32, 1), (16, 1), (8, 1), (4, 1), (2, 1), (1, 1)], kind="rate"),
    "phaser": dict(free=(0x34c220, (1, 1001)), i2v=(0x34c240, "scale", 0.01), v2i=(0x34c25c, "round_scale", 100.0),
                   sync=(0x34c28c, (0, 12)), f2v=(0x34c534, 0xf61fcc, 4), v2f=(0x34c594, "desc"),
                   fracs=[(64, 1), (32, 1), (16, 1), (8, 1), (4, 1), (2, 1), (1, 1), (3, 4), (1, 2), (1, 4), (1, 8), (1, 16)],
                   kind="rate"),
    "insert_delay": dict(free=(0x34ba18, (10, 1001)), i2v=(0x34ba38, "id", None), v2i=(0x34ba48, "round", None),
                         sync=(0x34ba68, (0, 6)), f2v=(0x34bc2c, 0xf61fb4, 2), v2f=(0x34bc8c, "asc"),
                         fracs=[(1, 8), (1, 4), (1, 2), (3, 4), (1, 1), (2, 1)], kind="delay"),
    "send_delay": dict(free=(0x34a428, (10, 4001)), i2v=(0x34a448, "id", None), v2i=(0x34a458, "round", None),
                       sync=(0x34a478, (0, 8)), f2v=(0x34a688, 0xf61f94, 6), v2f=(0x34a6e8, "asc"),
                       fracs=[(1, 8), (1, 4), (1, 2), (3, 4), (1, 1), (2, 1), (4, 1), (8, 1)], kind="delay"),
    # Ducker: free = 0.1 ms steps, sync = 128 sixteenth-note multipliers (table search with +1e-4)
    "ducker_attack": dict(free=(0x34ca40, (0, 10001)), i2v=(0x34ca58, "scale", 0.1), v2i=(0x34ca7c, "trunc_scale", 10.0),
                          sync=(0x34ca94, (0, 128)), f2v=(0x34caa8, 0x8a9b20, None), v2f=(0x34cac8, "bsearch"),
                          table=_DK.TA, kind="ducker"),
    "ducker_release": dict(free=(0x34cb60, (1, 80001)), i2v=(0x34cb78, "scale", 0.1), v2i=(0x34cb9c, "trunc_scale", 10.0),
                           sync=(0x34cbb4, (0, 128)), f2v=(0x34cbc8, 0x8a9d20, None), v2f=(0x34cbe8, "bsearch"),
                           table=_DK.TR, kind="ducker"),
}
BSEARCH_EPS = F(1e-4)                                          # 0x38d1b717
K_60 = F(60.0); K_1 = F(1.0); K_MILLI = F(0.001); K_1000 = F(1000.0); K_60000 = F(60000.0); K_QUARTER = F(0.25)
K_0004 = F(0.004); K_HALF = F(0.5); K_TENTH = F(0.1)

# s34 jump-table case -> (family, effect index passed to 0x112924) per context
CASES = {
    "insert": {0: ("chorus", 0), 1: ("flanger", 1), 4: ("insert_delay", 4), 8: ("phaser", 8), 9: ("ducker", 9)},
    "master": {0: ("send_delay", 0), 2: ("chorus", 2), 3: ("flanger", 3), 9: ("phaser", 9)},
    "send":   {0: ("send_delay", 0), 2: ("chorus", 2), 3: ("flanger", 3), 9: ("phaser", 9)},
}


def frac_value(fam, i):
    """indexToFraction: index outside [0, n) -> assert + default index; f32(num) / f32(den)."""
    F_ = FAMILIES[fam]
    if F_["kind"] == "ducker":
        return F_["table"][i]                                  # no bounds check in 1.60 (caller keeps 0 <= i < 128)
    n = len(F_["fracs"])
    if not (0 <= i < n): i = F_["f2v"][2]
    a, b = F_["fracs"][i]
    return fdiv(float(a), float(b))


def frac_index(fam, x):
    """valueToIndex in sync mode."""
    F_ = FAMILIES[fam]
    order = F_["v2f"][1]
    if order == "bsearch":
        T = F_["table"]; lo, hi = 0, 127
        mid = 0
        while hi > lo:
            mid = lo + (hi - lo) // 2
            if fadd(T[mid], BSEARCH_EPS) > x: hi = mid
            else: lo = mid + 1
        return hi if lo == hi else mid
    f = [fdiv(float(a), float(b)) for a, b in F_["fracs"]]
    n = len(f)
    for k in range(n - 1):
        m = fmul(fadd(f[k], f[k + 1]), K_HALF)
        if (x > m) if order == "desc" else (x < m): return k
    return n - 1


def free_value(fam, i):
    kind, k = FAMILIES[fam]["i2v"][1:]
    if kind == "scale": return fmul(float(i), k)
    return F(float(i))


def free_index(fam, x):
    kind, k = FAMILIES[fam]["v2i"][1:]
    if kind == "round_scale": return round_to_int(fmul(x, k))
    if kind == "trunc_scale": return trunc_s32(fmul(x, k))
    return round_to_int(F(x))


def tempo_f32(bpm, insert=True):
    """0x112a48: f32(double tempo), < 0.5 -> 0.5; the Insert s34 adds `< 0.1 -> 0.1` (never active after 0x112a48)."""
    t = F(bpm)
    if t < K_HALF: t = K_HALF
    if insert and t < F(0.1): t = F(0.1)
    return t


def convert(fam, v, sync, T):
    """Convert one stored normalised value v (already input-clamped where the code clamps) at f32 tempo T.
    sync = new SYNC state (1: free -> sync, 0: sync -> free). Returns (v_out, detail dict)."""
    F_ = FAMILIES[fam]; kind = F_["kind"]
    (flo, fhi), (slo, shi) = F_["free"][1], F_["sync"][1]
    if sync:
        i = step_of(flo, fhi, v); x = free_value(fam, i)
        if kind == "rate":   y = fmul(fdiv(T, K_60), fdiv(K_1, x))           # beats per cycle = (T/60) * (1/Hz)
        elif kind == "delay": y = fmul(fmul(x, fdiv(T, K_60)), K_MILLI)       # beats = ms * (T/60) * 0.001
        else:                y = fmul(x, fdiv(fmul(T, K_0004), K_60))         # sixteenths = ms * (T*0.004/60)
        j = frac_index(fam, y); vo = norm_of(slo, shi, j)
    else:
        i = step_of(slo, shi, v); x = frac_value(fam, i)
        if kind == "rate":   y = fmul(fdiv(T, K_60), fdiv(K_1, x))           # Hz = (T/60) * (1/beats)
        elif kind == "delay": y = fmul(fmul(x, fdiv(K_60, T)), K_1000)        # ms = beats * (60/T) * 1000
        else:                y = fmul(fmul(x, fdiv(K_60000, T)), K_QUARTER)   # ms = sixteenths * (60000/T) * 0.25
        j = free_index(fam, y); vo = norm_of(flo, fhi, j)
    return clamp01_out(vo), dict(i=i, x=x, y=y, j=j)


def s34(ctx, case, ed0, ed2, sync, bpm):
    """Model of manager slot 34 (Insert 0x126c90, Master 0x1208ac, Send 0x12b3b4) for jump-table case `case` (the processor's
    pending effect index). Returns dict(ed0, ed2, calls=[(effect, idx, float)], sync_byte); calls == [] for other cases."""
    T = tempo_f32(bpm, insert=(ctx == "insert"))
    out = dict(ed0=F(ed0), ed2=F(ed2), calls=[], sync_byte=sync & 0xff, T=T, detail={})
    if case not in CASES[ctx]: return out
    fam, eff = CASES[ctx][case]
    if fam == "ducker":                                        # no input clamp; ATTACK (sub 0) then RELEASE (sub 2)
        a, da = convert("ducker_attack", F(ed0), sync, T)
        r, dr = convert("ducker_release", F(ed2), sync, T)
        out.update(ed0=a, ed2=r, detail=dict(attack=da, release=dr))
        out["calls"] = [(eff, 0, a), (eff, 2, r), (eff, 6, F(float(sync & 0xffffffff)))]
        return out
    v, d = convert(fam, clamp01_in(F(ed0)), sync, T)
    out.update(ed0=v, detail=d)
    out["calls"] = [(eff, 0, v), (eff, 6, F(float(sync & 0xffffffff)))]
    return out


# ------------------------------------------------------------------------------------------------------------- reachable values
def reachable(fam, sync):
    """Every normalised value the UI step code can store for the time parameter of `fam` in the given mode, with its
    integer step and physical value (free: Hz or ms; sync: beats per cycle / beats of delay / sixteenths)."""
    F_ = FAMILIES[fam]
    lo, hi = (F_["sync"] if sync else F_["free"])[1]
    out = []
    for i in range(lo, hi):
        v = norm_of(lo, hi, i)
        out.append((i, v, frac_value(fam, i) if sync else free_value(fam, i)))
    return out
