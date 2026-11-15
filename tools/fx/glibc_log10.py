# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
# Parts follow the public fdlibm algorithm; Sun's fdlibm notice is quoted below and must be preserved (see NOTICE.md).
"""Own Python re-implementation of the double-precision log10 of glibc 2.13 (sysdeps/ieee754/dbl-64/e_log10.c, the classic
fdlibm algorithm: log10(x) = y*log10_2hi + (y*log10_2lo + ivln10*log(m)), with x = 2^y * m and m in [1, 2) or [0.5, 1) for
negative exponents), on top of a correctly rounded natural log (glibc 2.13's dbl-64 __ieee754_log is the IBM Accurate
Mathematical Library routine, which returns correctly rounded results).

The 1.60 libm `log10` is NOT correctly rounded (F082: 81 of 1504 arguments differ by 1 ulp from a correctly rounded
log10), so the compressor model's level detector (L = 20 log10(level)) needs this algorithm for bit-exact results. Written from
the published algorithm description (the fdlibm constants below are the published values; Sun's fdlibm notice: "Developed at
SunPro, a Sun Microsystems, Inc. business. Permission to use, copy, modify, and distribute this software is freely granted,
provided that this notice is preserved."). Contains no firmware bytes. Covers finite positive x (the only case reached).
"""
import decimal, math, struct
from decimal import Decimal as D

two54 = 1.80143985094819840000e+16
ivln10 = 4.34294481903251816668e-01
log10_2hi = 3.01029995663611771306e-01
log10_2lo = 3.69423907715893078616e-13
_CTX = decimal.Context(prec=60, rounding=decimal.ROUND_HALF_EVEN)


def cr_log(x):
    """Correctly rounded natural log (double)."""
    with decimal.localcontext(_CTX):
        return float(D(x).ln())


def _words(x):
    u = struct.unpack("<Q", struct.pack("<d", x))[0]
    return u >> 32, u & 0xffffffff


def _from_words(hi, lo):
    return struct.unpack("<d", struct.pack("<Q", ((hi & 0xffffffff) << 32) | lo))[0]


def log10(x):
    x = float(x)
    if not (x > 0.0) or math.isinf(x) or math.isnan(x):
        return math.log10(x) if x > 0 else (-math.inf if x == 0 else math.nan)
    hx, lx = _words(x); k = 0
    if hx < 0x00100000:                                  # subnormal
        k -= 54; x *= two54; hx, lx = _words(x)
    k += (hx >> 20) - 1023
    i = 1 if k < 0 else 0
    hx = (hx & 0x000fffff) | ((0x3ff - i) << 20)
    y = float(k + i)
    x = _from_words(hx, lx)
    z = y * log10_2lo + ivln10 * cr_log(x)
    return z + y * log10_2hi
