# SP-16 firmware research, tools/fx. Python transliteration of the public fdlibm algorithm (no firmware bytes).
# fdlibm notice (must be preserved):
#   Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
#   Developed at SunPro, a Sun Microsystems, Inc. business.
#   Permission to use, copy, modify, and distribute this software is freely granted,
#   provided that this notice is preserved.
#   Conversion to float by Ian Lance Taylor, Cygnus Support.
# The project's own changes are MIT (see LICENSE at the repository root).
"""Own Python re-implementation of the classic fdlibm single-precision tangent (the public algorithm of glibc's
sysdeps/ieee754/flt-32/s_tanf.c + k_tanf.c + e_rem_pio2f.c, as shipped in glibc 2.13 on the SP-16 1.60 root filesystem).
The 1.60 Phaser computes its all-pass coefficient bounds with libm `tanf` (PLT 0x104c8), which is not correctly rounded,
so a bit-exact model needs the same algorithm (docs/effects/phaser.md).

Written from the published algorithm description; it contains no firmware bytes. The constants are the published fdlibm
values (each also occurs in the 1.60 libm.so.6, checked by the project's unpublished harness). Each float32 operation is
computed in double and rounded to float32 (exact for + - * /). Covers finite |x| < 3*pi/4 (the Phaser reaches
|x| <= pi*20000/44100 ~ 1.42); larger arguments raise NotImplementedError.
Credit: fdlibm, Copyright (C) 1993 by Sun Microsystems, Inc. ("Permission to use, copy, modify, and distribute this
software is freely granted, provided that this notice is preserved."); float conversion by Ian Lance Taylor, Cygnus Support.
"""
from fdlibm_powf import F, w_of, f_of, s32

ONE = F(1.0)
PIO4 = f_of(0x3f490fda)
PIO4LO = f_of(0x33222168)
T = [f_of(w) for w in (0x3eaaaaab, 0x3e088889, 0x3d5d0dd1, 0x3cb327a4, 0x3c11371f, 0x3b6b6916, 0x3abede48, 0x3a1a26c8,
                       0x398137b9, 0x38a3f445, 0x3895c07a, 0xb79bae5f, 0x37d95384)]
PIO2_1, PIO2_1T = f_of(0x3fc90f80), f_of(0x37354443)
PIO2_2, PIO2_2T = f_of(0x37354400), f_of(0x2e85a308)


def _a(x, y): return F(x + y)
def _s(x, y): return F(x - y)
def _m(x, y): return F(x * y)
def _d(x, y): return F(x / y)


def kernel_tanf(x, y, iy):
    hx = s32(w_of(x)); ix = hx & 0x7fffffff
    if ix < 0x31800000:                                    # |x| < 2^-28
        if int(x) == 0:
            if (ix | (iy + 1)) == 0: return _d(ONE, abs(x))
            return x if iy == 1 else _d(-ONE, x)
    big = ix >= 0x3f2ca140                                 # |x| >= 0.6744
    if big:
        if hx < 0: x = -x; y = -y
        z = _s(PIO4, x); w = _s(PIO4LO, y)
        x = _a(z, w); y = F(0.0)
    z = _m(x, x)
    w = _m(z, z)
    r = _a(T[1], _m(w, _a(T[3], _m(w, _a(T[5], _m(w, _a(T[7], _m(w, _a(T[9], _m(w, T[11]))))))))))
    v = _m(z, _a(T[2], _m(w, _a(T[4], _m(w, _a(T[6], _m(w, _a(T[8], _m(w, _a(T[10], _m(w, T[12])))))))))))
    s = _m(z, x)
    r = _a(y, _m(z, _a(_m(s, _a(r, v)), y)))
    r = _a(r, _m(T[0], s))
    w = _a(x, r)
    if big:
        v = F(float(iy))
        return _m(F(float(1 - ((hx >> 30) & 2))), _s(v, _m(F(2.0), _s(x, _s(_d(_m(w, w), _a(w, v)), r)))))
    if iy == 1: return w
    z = f_of(w_of(w) & 0xfffff000)                         # compute -1/(x+r) accurately
    v = _s(r, _s(z, x))
    t = a = _d(-ONE, w)
    t = f_of(w_of(t) & 0xfffff000)
    s = _a(ONE, _m(t, z))
    return _a(t, _m(a, _a(s, _m(t, v))))


def rem_pio2f(x):
    hx = s32(w_of(x)); ix = hx & 0x7fffffff
    if ix <= 0x3f490fd8: return 0, x, F(0.0)
    if ix < 0x4016cbe4:                                    # |x| < 3pi/4: n = +-1
        if hx > 0:
            z = _s(x, PIO2_1)
            if (ix & 0xfffffff0) != 0x3fc90fd0:
                y0 = _s(z, PIO2_1T); y1 = _s(_s(z, y0), PIO2_1T)
            else:
                z = _s(z, PIO2_2); y0 = _s(z, PIO2_2T); y1 = _s(_s(z, y0), PIO2_2T)
            return 1, y0, y1
        z = _a(x, PIO2_1)
        if (ix & 0xfffffff0) != 0x3fc90fd0:
            y0 = _a(z, PIO2_1T); y1 = _a(_s(z, y0), PIO2_1T)
        else:
            z = _a(z, PIO2_2); y0 = _a(z, PIO2_2T); y1 = _a(_s(z, y0), PIO2_2T)
        return -1, y0, y1
    raise NotImplementedError("tanf: |x| >= 3*pi/4 not modelled (%r)" % x)


def tanf(x):
    x = F(x)
    ix = w_of(x) & 0x7fffffff
    if ix <= 0x3f490fda: return kernel_tanf(x, F(0.0), 1)
    if ix >= 0x7f800000: return F(x - x)
    n, y0, y1 = rem_pio2f(x)
    return kernel_tanf(y0, y1, 1 - ((n & 1) << 1))
