# SPDX-License-Identifier: LGPL-2.1-or-later
#
# SP-16 firmware research, tools/fx. This one file is NOT under the MIT licence of the rest of tools/fx/.
# It is an own re-implementation of the algorithm of glibc 2.13 sysdeps/ieee754/flt-32/e_expf.c. Because of that
# origin it is distributed under the GNU Lesser General Public License, version 2.1 or (at your option) any later
# version; see LICENSE-LGPL-2.1 at the repository root. It contains no firmware bytes. Its two accurate tables
# (__exp_atable, __exp_deltatable) are NOT included and must never be added: load_tables() reads them at run time
# from your own copy of the 1.60 libm.so.6. compressor.py and distortion.py import this file.
#
# This library is free software; you can redistribute it and/or modify it under the terms of the GNU Lesser General
# Public License as published by the Free Software Foundation; either version 2.1 of the License, or (at your option)
# any later version. This library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public
# License for more details.
"""Own Python re-implementation of the glibc 2.13 single-precision exp (sysdeps/ieee754/flt-32/e_expf.c, the published
table-driven algorithm: n = round(x / ln 2), t = multiple of 1/512 nearest to the remainder, 2^n * A[t] * e^(dx + delta[t])
with a 2nd-degree polynomial in double, rounded once to float).

The 1.60 libm `expf` is this algorithm. It is not always correctly rounded (about 1 in 1,500-3,000 arguments differs by
1 ulp from crmath.expf), so bit-exact effect models whose coefficients come from expf of arbitrary arguments need it.
Its two accurate tables (`__exp_atable`, 355 doubles; `__exp_deltatable`, 178 floats) are not reproducible from a formula
(Gal-style accurate-table values), so they are NOT copied here: `load_tables()` reads them at run time from the local
1.60 libm (default: decoded/lib/libm.so.6 in the research-folder layout (the model sat in harness/models/ next to target/ and decoded/; in this repo pass the path explicitly, see tools/fx/README.md); call load_tables(path) with the path to your own
1.60 libm.so.6), the same convention as the oscillator random table (F053). Without the
tables, `expf` falls back to the correctly rounded crmath.expf.
"""
import os, struct
import crmath as CR

_ctypes_f = None
def _F(x):
    return struct.unpack("<f", struct.pack("<f", x))[0]

M_1_LN2F = _F(1.44269502163)          # float constant 1/ln 2
M_LN2 = 0.6931471805599452862         # double ln 2
THREEp22 = 12582912.0
THREEp42 = 13194139533312.0
HIMARK = 88.72283935546875
LOMARK = -103.972084045410
_A = None
_DT = None


def load_tables(libm_path=None):
    """Read __exp_atable / __exp_deltatable from the local 1.60 libm by symbol (no bytes are stored in this file)."""
    global _A, _DT
    import lief
    here = os.path.dirname(os.path.abspath(__file__))
    libm_path = libm_path or os.path.join(os.path.dirname(os.path.dirname(here)), "decoded", "lib", "libm.so.6")
    e = lief.parse(libm_path); raw = open(libm_path, "rb").read()
    syms = {s.name: s for s in e.symbols}
    def off(va):
        for s in e.segments:
            if s.type == lief.ELF.Segment.TYPE.LOAD and s.virtual_address <= va < s.virtual_address + s.physical_size:
                return s.file_offset + va - s.virtual_address
    a, d = syms["__exp_atable"], syms["__exp_deltatable"]
    assert a.size == 355 * 8 and d.size == 178 * 4
    _A = struct.unpack_from("<355d", raw, off(a.value))
    _DT = struct.unpack_from("<178f", raw, off(d.value))
    return True


def loaded(): return _A is not None


def expf(x):
    x = _F(x)
    if _A is None or not (x < HIMARK and x > LOMARK):
        return CR.expf(x)                                 # tables absent, or overflow/underflow range (not reached)
    n = _F(_F(x * M_1_LN2F) + THREEp22)
    n = _F(n - THREEp22)
    dx = x - n * M_LN2
    t = dx + THREEp42
    t -= THREEp42
    dx -= t
    tval = int(t * 512.0)
    delta = -_DT[tval] if t >= 0 else _DT[-tval]
    ex2 = _A[tval + 177] * (2.0 ** int(n))               # exponent field += n (exact for the reached range)
    x22 = (0.5000000496709180453 * dx + 1.0000001192102037084) * dx + delta
    return _F(x22 * ex2 + ex2)
