# SP-16 firmware research, tools/fx. Python transliteration of the public fdlibm algorithm (no firmware bytes).
# fdlibm notice (must be preserved):
#   Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
#   Developed at SunPro, a Sun Microsystems, Inc. business.
#   Permission to use, copy, modify, and distribute this software is freely granted,
#   provided that this notice is preserved.
#   Conversion to float by Ian Lance Taylor, Cygnus Support.
# The project's own changes are MIT (see LICENSE at the repository root).
"""Own Python re-implementation of the classic fdlibm single-precision sine and cosine (the public algorithm of glibc's
sysdeps/ieee754/flt-32/s_sinf.c, s_cosf.c, k_sinf.c, k_cosf.c and the medium-size path of e_rem_pio2f.c, as shipped in
glibc 2.13 on the SP-16 1.60 root filesystem). The 1.60 oscillator's setPhaseOffset (0x1017d4) calls libm `cosf`/`sinf`
for the sine waveform; they are not correctly rounded, so a bit-exact model needs the same algorithm (docs/effects/oscillator.md).

Written from the published algorithm description; it contains no firmware bytes. The constants are the published fdlibm
values (the project's unpublished harness checks that each occurs in the 1.60 libm.so.6). Each float32 operation is computed in
double and rounded to float32 (exact for + - * /). Covers finite |x| <= 2^7*pi/2 (the oscillator reaches |x| < 2*pi);
larger arguments raise NotImplementedError.
Credit: fdlibm, Copyright (C) 1993 by Sun Microsystems, Inc. ("Permission to use, copy, modify, and distribute this
software is freely granted, provided that this notice is preserved."); float conversion by Ian Lance Taylor, Cygnus Support.
"""
from fdlibm_powf import F, w_of, f_of, s32
from fdlibm_tanf import rem_pio2f as _rem_small

ONE, HALF = F(1.0), F(0.5)
C = [f_of(w) for w in (0x3d2aaaab, 0xbab60b61, 0x37d00d01, 0xb493f27c, 0x310f74f6, 0xad47d74e)]
S = [f_of(w) for w in (0xbe2aaaab, 0x3c088889, 0xb9500d01, 0x3638ef1b, 0xb2d72f34, 0x2f2ec9d3)]
INVPIO2 = f_of(0x3f22f984)
PIO2_1, PIO2_1T = f_of(0x3fc90f80), f_of(0x37354443)
PIO2_2, PIO2_2T = f_of(0x37354400), f_of(0x2e85a308)
PIO2_3, PIO2_3T = f_of(0x2e85a300), f_of(0x248d3132)
NPIO2_HW = [0x3fc90f00, 0x40490f00, 0x4096cb00, 0x40c90f00, 0x40fb5300, 0x4116cb00, 0x412fed00, 0x41490f00]
CONSTANTS = C + S + [INVPIO2, PIO2_1, PIO2_1T, PIO2_2, PIO2_2T, PIO2_3, PIO2_3T]


def _a(x, y): return F(x + y)
def _s(x, y): return F(x - y)
def _m(x, y): return F(x * y)


def kernel_cosf(x, y):
    ix = w_of(x) & 0x7fffffff
    if ix < 0x32000000 and int(x) == 0: return ONE
    z = _m(x, x)
    r = _m(z, _a(C[0], _m(z, _a(C[1], _m(z, _a(C[2], _m(z, _a(C[3], _m(z, _a(C[4], _m(z, C[5])))))))))))
    if ix < 0x3e99999a:
        return _s(ONE, _s(_m(HALF, z), _s(_m(z, r), _m(x, y))))
    qx = F(0.28125) if ix > 0x3f480000 else f_of(ix - 0x01000000)
    hz = _s(_m(HALF, z), qx)
    a = _s(ONE, qx)
    return _s(a, _s(hz, _s(_m(z, r), _m(x, y))))


def kernel_sinf(x, y, iy):
    ix = w_of(x) & 0x7fffffff
    if ix < 0x32000000 and int(x) == 0: return x
    z = _m(x, x)
    v = _m(z, x)
    r = _a(S[1], _m(z, _a(S[2], _m(z, _a(S[3], _m(z, _a(S[4], _m(z, S[5]))))))))
    if iy == 0: return _a(x, _m(v, _a(S[0], _m(z, r))))
    return _s(x, _s(_s(_m(z, _s(_m(HALF, y), _m(v, r))), y), _m(v, S[0])))


def rem_pio2f(x):
    hx = s32(w_of(x)); ix = hx & 0x7fffffff
    if ix < 0x4016cbe4: return _rem_small(x)
    if ix > 0x43490f80: raise NotImplementedError("rem_pio2f: |x| > 2^7*pi/2 not modelled (%r)" % x)
    t = abs(x)
    n = int(_a(_m(t, INVPIO2), HALF))
    fn = F(float(n))
    r = _s(t, _m(fn, PIO2_1))
    w = _m(fn, PIO2_1T)
    if n < 32 and n - 1 < len(NPIO2_HW) and (ix & 0xffffff00) != NPIO2_HW[n - 1]:
        y0 = _s(r, w)
    else:
        j = ix >> 23
        y0 = _s(r, w)
        i = j - ((w_of(y0) >> 23) & 0xff)
        if i > 8:
            t2 = r; w = _m(fn, PIO2_2); r = _s(t2, w)
            w = _s(_m(fn, PIO2_2T), _s(_s(t2, r), w))
            y0 = _s(r, w)
            i = j - ((w_of(y0) >> 23) & 0xff)
            if i > 25:
                t2 = r; w = _m(fn, PIO2_3); r = _s(t2, w)
                w = _s(_m(fn, PIO2_3T), _s(_s(t2, r), w))
                y0 = _s(r, w)
    y1 = _s(_s(r, y0), w)
    if hx < 0: return -n, -y0, -y1
    return n, y0, y1


def sinf(x):
    x = F(x); ix = w_of(x) & 0x7fffffff
    if ix <= 0x3f490fd8: return kernel_sinf(x, F(0.0), 0)
    if ix >= 0x7f800000: return F(x - x)
    n, y0, y1 = rem_pio2f(x)
    q = n & 3
    if q == 0: return kernel_sinf(y0, y1, 1)
    if q == 1: return kernel_cosf(y0, y1)
    if q == 2: return -kernel_sinf(y0, y1, 1)
    return -kernel_cosf(y0, y1)


def cosf(x):
    x = F(x); ix = w_of(x) & 0x7fffffff
    if ix <= 0x3f490fd8: return kernel_cosf(x, F(0.0))
    if ix >= 0x7f800000: return F(x - x)
    n, y0, y1 = rem_pio2f(x)
    q = n & 3
    if q == 0: return kernel_cosf(y0, y1)
    if q == 1: return -kernel_sinf(y0, y1, 1)
    if q == 2: return -kernel_cosf(y0, y1)
    return kernel_sinf(y0, y1, 1)
