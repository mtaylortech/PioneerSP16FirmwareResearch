# SP-16 firmware research, tools/fx. Python transliteration of the public fdlibm algorithm (no firmware bytes).
# fdlibm notice (must be preserved):
#   Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
#   Developed at SunPro, a Sun Microsystems, Inc. business.
#   Permission to use, copy, modify, and distribute this software is freely granted,
#   provided that this notice is preserved.
#   Conversion to float by Ian Lance Taylor, Cygnus Support.
# The project's own changes are MIT (see LICENSE at the repository root).
"""Own Python re-implementation of the classic fdlibm single-precision power function (the public algorithm used by
glibc's sysdeps/ieee754/flt-32/e_powf.c up to glibc 2.27). The SP-16 1.60 root filesystem ships glibc 2.13, whose libm
`powf` is this algorithm; it is NOT correctly rounded (about 9 % of powf(1000, v) results differ by 1 ulp from the
correctly rounded value), so effect models that call powf need it for bit-exact results (docs/effects/parametric-eq.md).

Written from the published algorithm description; it contains no firmware bytes. Each float32 operation is computed in
double and rounded to float32 (exact for + - * /). Covers finite positive x with any finite y (the cases the SP-16 effect
code reaches); the special-value branches of the C code (NaN, inf, x <= 0, |y| > 2^27) are handled only partly and fall
back to math.pow where marked.

`TH_ADD` selects the constant added when forming t_h: the historical fdlibm/glibc source uses 0x0040000 (a known
typo of 0x00400000). The harness tests which one reproduces the 1.60 libm.
Credit: fdlibm, Copyright (C) 1993 by Sun Microsystems, Inc. ("Permission to use, copy, modify, and distribute this
software is freely granted, provided that this notice is preserved."); float conversion by Ian Lance Taylor, Cygnus Support.
"""
import ctypes, math, struct

_cf = ctypes.c_float
def F(x): return _cf(x).value
def w_of(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def f_of(w): return struct.unpack("<f", struct.pack("<I", w & 0xffffffff))[0]
def s32(w): return w - (1 << 32) if w & 0x80000000 else w

bp = [F(1.0), F(1.5)]
dp_h = [F(0.0), f_of(0x3f15c000)]
dp_l = [F(0.0), f_of(0x35d1cfdc)]
two24 = f_of(0x4b800000)
L1, L2, L3 = f_of(0x3f19999a), f_of(0x3edb6db7), f_of(0x3eaaaaab)
L4, L5, L6 = f_of(0x3e8ba305), f_of(0x3e6c3255), f_of(0x3e53f142)
P1, P2, P3 = f_of(0x3e2aaaab), f_of(0xbb360b61), f_of(0x388ab355)
P4, P5 = f_of(0xb5ddea0e), f_of(0x3331bb4c)
lg2, lg2_h, lg2_l = f_of(0x3f317218), f_of(0x3f317200), f_of(0x35bfbe8c)
cp, cp_h, cp_l = f_of(0x3f76384f), f_of(0x3f763800), f_of(0x369dc3a0)
THREE = F(3.0); ONE = F(1.0); TWO = F(2.0)

TH_ADD = 0x0040000          # historical fdlibm constant (see module docstring)


def _trunc12(x): return f_of(w_of(x) & 0xfffff000)


def powf(x, y, th_add=None):
    th_add = TH_ADD if th_add is None else th_add
    x = F(x); y = F(y)
    hx = s32(w_of(x)); hy = s32(w_of(y)); ix = hx & 0x7fffffff; iy = hy & 0x7fffffff
    if iy == 0: return ONE
    if x == 1.0: return ONE
    if ix > 0x7f800000 or iy > 0x7f800000 or hx < 0 or iy >= 0x7f800000 or ix >= 0x7f800000 or ix == 0:
        return F(math.pow(x, y))                         # special values: not reached by the effect code
    if iy == 0x3f800000: return x if hy >= 0 else F(ONE / x)
    if hy == 0x40000000: return F(x * x)
    if hy == 0x3f000000: return F(math.sqrt(x))
    ax = abs(x)
    if ix == 0x3f800000: return ONE
    if iy > 0x4d000000: return F(math.pow(x, y))         # |y| > 2^27: not reached
    n = 0
    if ix < 0x00800000:
        ax = F(ax * two24); n -= 24; ix = w_of(ax)
    n += (ix >> 23) - 0x7f
    j = ix & 0x007fffff
    ix = j | 0x3f800000
    if j <= 0x1cc471: k = 0
    elif j < 0x5db3d7: k = 1
    else:
        k = 0; n += 1; ix -= 0x00800000
    ax = f_of(ix)
    u = F(ax - bp[k]); v = F(ONE / F(ax + bp[k])); s = F(u * v)
    s_h = _trunc12(s)
    t_h = f_of(((ix >> 1) | 0x20000000) + th_add + (k << 21))
    t_l = F(ax - F(t_h - bp[k]))
    s_l = F(v * F(F(u - F(s_h * t_h)) - F(s_h * t_l)))
    s2 = F(s * s)
    poly = F(L5 + F(s2 * L6)); poly = F(L4 + F(s2 * poly)); poly = F(L3 + F(s2 * poly))
    poly = F(L2 + F(s2 * poly)); poly = F(L1 + F(s2 * poly))
    r = F(F(s2 * s2) * poly)
    r = F(r + F(s_l * F(s_h + s)))
    s2 = F(s_h * s_h)
    t_h = _trunc12(F(F(THREE + s2) + r))
    t_l = F(r - F(F(t_h - THREE) - s2))
    u = F(s_h * t_h)
    v = F(F(s_l * t_h) + F(t_l * s))
    p_h = _trunc12(F(u + v))
    p_l = F(v - F(p_h - u))
    z_h = F(cp_h * p_h)
    z_l = F(F(F(cp_l * p_h) + F(p_l * cp)) + dp_l[k])
    t = F(float(n))
    t1 = _trunc12(F(F(F(z_h + z_l) + dp_h[k]) + t))
    t2 = F(z_l - F(F(F(t1 - t) - dp_h[k]) - z_h))
    sgn = ONE
    y1 = _trunc12(y)
    p_l = F(F(F(y - y1) * t1) + F(y * t2))
    p_h = F(y1 * t1)
    z = F(p_l + p_h)
    j = s32(w_of(z))
    if j > 0x43000000 or (j & 0x7fffffff) > 0x43160000 or j == 0x43000000 or j == s32(0xc3160000):
        return F(math.pow(x, y))                         # overflow/underflow edges: not reached
    i = j & 0x7fffffff
    k = (i >> 23) - 0x7f
    n = 0
    if i > 0x3f000000:
        n = j + (0x00800000 >> (k + 1))
        k = ((n & 0x7fffffff) >> 23) - 0x7f
        t = f_of(n & ~(0x007fffff >> k))
        n = ((n & 0x007fffff) | 0x00800000) >> (23 - k)
        if j < 0: n = -n
        p_h = F(p_h - t)
    t = _trunc12(F(p_l + p_h))
    u = F(t * lg2_h)
    v = F(F(F(p_l - F(t - p_h)) * lg2) + F(t * lg2_l))
    z = F(u + v)
    w = F(v - F(z - u))
    t = F(z * z)
    q = F(P4 + F(t * P5)); q = F(P3 + F(t * q)); q = F(P2 + F(t * q)); q = F(P1 + F(t * q))
    t1 = F(z - F(t * q))
    r = F(F(F(z * t1) / F(t1 - TWO)) - F(w + F(z * w)))
    z = F(ONE - F(r - z))
    j = s32(w_of(z)) + (n << 23)
    if (j >> 23) <= 0:
        z = F(math.ldexp(z, n))
    else:
        z = f_of(j)
    return F(sgn * z)


# ---- single-precision natural and base-10 logarithm (fdlibm e_logf.c / e_log10f.c algorithm, as in glibc 2.13) ----
ln2_hi, ln2_lo = f_of(0x3f317180), f_of(0x3717f7d1)
Lg1, Lg2, Lg3, Lg4 = f_of(0x3f2aaaab), f_of(0x3ecccccd), f_of(0x3e924925), f_of(0x3e638e29)
Lg5, Lg6, Lg7 = f_of(0x3e3a3325), f_of(0x3e1cd04f), f_of(0x3e178897)
two25 = f_of(0x4c000000)
ivln10, log10_2hi, log10_2lo = f_of(0x3ede5bd9), f_of(0x3e9a2080), f_of(0x355427db)
HALF = F(0.5); THIRD = F(0.33333333333333333)


def logf(x):
    x = F(x); ix = s32(w_of(x)); k = 0
    if ix < 0x00800000 or ix >= 0x7f800000:
        return F(math.log(x)) if x > 0 and not math.isinf(x) else float("nan")   # not reached by the effect code
    k += (ix >> 23) - 127
    ix &= 0x007fffff
    i = (ix + (0x95f64 << 3)) & 0x800000
    x = f_of(ix | (i ^ 0x3f800000))
    k += i >> 23
    f = F(x - ONE)
    if (0x007fffff & (15 + ix)) < 16:
        if f == 0.0:
            if k == 0: return F(0.0)
            dk = F(float(k)); return F(F(dk * ln2_hi) + F(dk * ln2_lo))
        R = F(F(f * f) * F(HALF - F(THIRD * f)))
        if k == 0: return F(f - R)
        dk = F(float(k)); return F(F(dk * ln2_hi) - F(F(R - F(dk * ln2_lo)) - f))
    s = F(f / F(TWO + f))
    dk = F(float(k))
    z = F(s * s)
    i = ix - (0x6147a << 3)
    w = F(z * z)
    j = (0x6b851 << 3) - ix
    t1 = F(w * F(Lg2 + F(w * F(Lg4 + F(w * Lg6)))))
    t2 = F(z * F(Lg1 + F(w * F(Lg3 + F(w * F(Lg5 + F(w * Lg7)))))))
    i |= j
    R = F(t2 + t1)
    if i > 0:
        hfsq = F(F(HALF * f) * f)
        if k == 0: return F(f - F(hfsq - F(s * F(hfsq + R))))
        return F(F(dk * ln2_hi) - F(F(hfsq - F(F(s * F(hfsq + R)) + F(dk * ln2_lo))) - f))
    if k == 0: return F(f - F(s * F(f - R)))
    return F(F(dk * ln2_hi) - F(F(F(s * F(f - R)) - F(dk * ln2_lo)) - f))


def log10f(x):
    x = F(x); hx = s32(w_of(x)); k = 0
    if hx < 0x00800000 or hx >= 0x7f800000:
        return F(math.log10(x)) if x > 0 and not math.isinf(x) else float("nan")  # not reached by the effect code
    k += (hx >> 23) - 127
    i = (k & 0x80000000) >> 31 if k >= 0 else 1
    hx = (hx & 0x007fffff) | ((0x7f - i) << 23)
    y = F(float(k + i))
    x = f_of(hx)
    z = F(F(y * log10_2lo) + F(ivln10 * logf(x)))
    return F(z + F(y * log10_2hi))
