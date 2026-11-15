# SP-16 firmware research, tools/fx. Own code (MIT, see LICENSE at the repository root); contains no firmware bytes.
"""Correctly rounded elementary functions (own code, no firmware bytes), computed with Python's decimal module at ~50
significant digits and rounded once to IEEE double (or float32).

Why: the 1.60 oscillator calls glibc 2.13 libm `sincos`, `cos`, `acos` (dbl-64, IBM Accurate Mathematical Library, which
returns correctly rounded results) and `expf`. The host's math module is not correctly rounded (macOS libm differs from
the emulated 1.60 libm in a few % of cases), so a bit-exact model needs correctly rounded values. Checked against the
emulated 1.60 libm by tools/fx/verify/H031_osc_model.py (section C3 libm).
tan / pow / exp (double) were added later (F206, H029) for the LoFi / MMF / PEQ / PerfLoFi / EffectBase / Phaser coefficient
steps; tools/fx/verify/H029_libm_exact.py checks them against the emulated 1.60 libm `tan` / `pow` / `exp` (section B).
Note: expf below is correctly rounded, but glibc 2.13 expf is not always (use glibc_expf.py where bit-exactness matters).
"""
import decimal
import math
import struct
from decimal import Decimal as D

_CTX = decimal.Context(prec=60, rounding=decimal.ROUND_HALF_EVEN)


def _pi():
    with decimal.localcontext(_CTX) as c:
        c.prec += 5
        # Machin: pi = 16 atan(1/5) - 4 atan(1/239)
        def atan_inv(n):
            x = D(1) / n; x2 = x * x; s = x; t = x; k = 1
            while True:
                t = -t * x2; k += 2; d = t / k
                if abs(d) < D(10) ** -(c.prec + 2): break
                s += d
            return s
        p = 16 * atan_inv(5) - 4 * atan_inv(239)
    return +p


PI = _pi()


def _reduce(x):
    """x (Decimal) -> r in [-pi, pi] with x = r + 2k*pi."""
    k = (x / (2 * PI)).to_integral_value(rounding=decimal.ROUND_HALF_EVEN)
    return x - 2 * PI * k


def _sin_cos(x):
    with decimal.localcontext(_CTX) as c:
        r = _reduce(D(x))
        r2 = r * r; s = r; t = r; k = 1
        eps = D(10) ** -(c.prec + 2)
        while True:
            t = -t * r2 / ((k + 1) * (k + 2)); k += 2
            if abs(t) < eps: break
            s += t
        co = D(1); t = D(1); k = 0
        while True:
            t = -t * r2 / ((k + 1) * (k + 2)); k += 2
            if abs(t) < eps: break
            co += t
        return s, co


def sin(x): return float(_sin_cos(x)[0]) if x != 0.0 else x
def cos(x): return float(_sin_cos(x)[1])
def sincos(x): s, c = _sin_cos(x); return (float(s) if x != 0.0 else x), float(c)


def _atan(z):
    """atan of a Decimal in high precision (argument reduction to |z| < 0.2)."""
    with decimal.localcontext(_CTX) as c:
        c.prec += 10
        sign = -1 if z < 0 else 1; z = abs(z); inv = False
        if z > 1: z = 1 / z; inv = True
        k = 0
        while z > D("0.2"):                                   # atan z = 2 atan(z / (1 + sqrt(1 + z^2)))
            z = z / (1 + (1 + z * z).sqrt()); k += 1
        z2 = z * z; s = z; t = z; n = 1; eps = D(10) ** -(c.prec + 2)
        while True:
            t = -t * z2; n += 2; d = t / n
            if abs(d) < eps: break
            s += d
        s = s * (2 ** k)
        if inv: s = PI / 2 - s
        return +(sign * s)


def acos(x):
    if x == 1.0: return 0.0
    if x == -1.0: return float(PI)
    if not -1.0 < x < 1.0: return float("nan")
    with decimal.localcontext(_CTX) as c:
        d = D(x)
        r = PI / 2 - _atan(d / (1 - d * d).sqrt())               # acos x = pi/2 - asin x
        return float(r)


def _f32(x): return struct.unpack("<f", struct.pack("<f", x))[0]


def expf(x):
    """float32 exp, correctly rounded to float32 (decimal -> nearest float32 via an exact double intermediate check)."""
    with decimal.localcontext(_CTX) as c:
        v = D(x).exp()
    # round the Decimal directly to float32: find the nearest float32 neighbours of the double approximation
    u = struct.unpack("<I", struct.pack("<f", _f32(float(v))))[0]     # v > 0, so neighbours are u +- 1
    cands = [struct.unpack("<f", struct.pack("<I", w))[0] for w in (u - 1, u, u + 1)]
    return min(cands, key=lambda cc: (abs(D(cc) - v), struct.unpack("<I", struct.pack("<f", cc))[0] & 1))


def tan(x):
    """Correctly rounded double tan (glibc 2.13 dbl-64 tan is correctly rounded). Accurate for |x| up to ~1e40 (PI has 65 digits);
    the models only reach |x| < pi/2."""
    if x == 0.0: return x
    with decimal.localcontext(_CTX) as c:
        y = D(x)
        k = (y / PI).to_integral_value(rounding=decimal.ROUND_HALF_EVEN)
        r = y - k * PI                                            # tan has period pi
        r2 = r * r; s = r; t = r; n = 1
        eps = D(10) ** -(c.prec + 2)
        while True:
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2
            if abs(t) < eps: break
            s += t
        co = D(1); t = D(1); n = 0
        while True:
            t = -t * r2 / ((n + 1) * (n + 2)); n += 2
            if abs(t) < eps: break
            co += t
        return float(s / co)


def pow(x, y):
    """Correctly rounded double pow for finite x > 0 and finite y (glibc 2.13 dbl-64 pow is correctly rounded), EXCEPT when the
    exact result is a double midpoint (e.g. pow((2^27-1)*2^-26, 2)): exp(y*ln x) at 60 digits can land on the wrong side of the tie
    (found in independent review, F206). The modelled bases/exponents cannot produce such a midpoint (likely). Other operands raise."""
    if y == 0.0 or x == 1.0: return 1.0
    if not (x > 0.0 and math.isfinite(x) and math.isfinite(y)): raise ValueError("crmath.pow: unsupported operands %r, %r" % (x, y))
    with decimal.localcontext(_CTX):
        return float((D(y) * D(x).ln()).exp())


def exp(x):
    """Correctly rounded double exp (glibc 2.13 dbl-64 exp is correctly rounded); finite x."""
    if not math.isfinite(x): raise ValueError("crmath.exp: non-finite operand %r" % x)
    with decimal.localcontext(_CTX):
        return float(D(x).exp())
