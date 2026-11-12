# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below.
#
# Independent output oracle: re-decodes input/output and checks the gain/rounding envelope without importing core.py.
#
# Original path: experiments/normalization-host-core-20261011/oracle.py
# Original SHA-256 (before this header): 28c755c0af99c661e2a8e2ec0dfc7d8537af20280b678a55575f5ab1e3ed8078
# License: MIT. Host-side tool only: it does not run on, or modify, the SP-16.
# ---------------------------------------------------------------------------
"""Independent full-file decoded oracle; never imports the processing module.

Uses stdlib wave for geometry and decoding; expected arithmetic uses integer
quotient/remainder, not production Fraction rounding or production peak/gain.
Caller supplies predeclared expected gain/ceiling and generated source samples.
"""
from io import BytesIO
from fractions import Fraction
import struct
import wave


def decode(raw):
    with wave.open(BytesIO(raw), 'rb') as f:
        geometry = (f.getnchannels(), f.getframerate(), f.getsampwidth(), f.getnframes())
        pcm = f.readframes(f.getnframes())
        assert f.readframes(1) == b'', 'extra frame'
    width = geometry[2]
    if width == 2:
        values = list(struct.unpack('<' + 'h' * (len(pcm) // 2), pcm))
    elif width == 4:
        values = list(struct.unpack('<' + 'i' * (len(pcm) // 4), pcm))
    elif width == 3:
        values = []
        for a, b, c in zip(pcm[::3], pcm[1::3], pcm[2::3]):
            u = a + 256*b + 65536*c
            values.append(u - 16777216 if c >= 128 else u)
    else:
        raise AssertionError('oracle unsupported width')
    assert len(values) == geometry[0] * geometry[3], 'incomplete decoded output'
    return geometry, values


def expected(value, gain, rule):
    numerator = abs(value) * gain.numerator
    q, r = divmod(numerator, gain.denominator)
    if rule == 'nearest_even':
        if 2*r > gain.denominator or (2*r == gain.denominator and q % 2):
            q += 1
    elif rule != 'toward_zero':
        raise AssertionError('unknown oracle rule')
    return -q if value < 0 else q


def chunks(raw):
    assert raw[:4] == b'RIFF' and raw[8:12] == b'WAVE'
    declared = struct.unpack_from('<I', raw, 4)[0] + 8
    assert declared == len(raw), 'RIFF length mismatch'
    pos, result = 12, []
    while pos < len(raw):
        assert pos + 8 <= len(raw), 'chunk header truncated'
        size = struct.unpack_from('<I', raw, pos+4)[0]
        end = pos + 8 + size + size % 2
        assert end <= len(raw), 'chunk incomplete'
        result.append((raw[pos:pos+4], raw[pos:end]))
        pos = end
    return result


def check(before, after, known_samples, gain, rule, ceiling=None):
    g0, source = decode(before)
    g1, actual = decode(after)
    assert source == known_samples, 'fixture decoding disagrees with declared source'
    assert g0 == g1, 'geometry/rate/frame count changed'
    c0, c1 = chunks(before), chunks(after)
    assert len(before) == len(after) and len(c0) == len(c1), 'output length changed'
    for (t0, b0), (t1, b1) in zip(c0, c1):
        assert t0 == t1, 'chunk order changed'
        if t0 != b'data':
            assert b0 == b1, 'metadata/header/padding changed'
        else:
            assert b0[:8] == b1[:8], 'audio header changed'
            if (len(b0)-8) % 2:  # padded data chunk always even; actual size is in header
                raise AssertionError('unreachable odd chunk')
            size = struct.unpack_from('<I', b0, 4)[0]
            assert b0[8+size:] == b1[8+size:], 'audio padding changed'
    wanted = [expected(x, gain, rule) for x in known_samples]
    assert actual == wanted, 'decoded samples differ from independently declared gain'
    bound = Fraction(1, 2) if rule == 'nearest_even' else Fraction(1)
    errors = [abs(Fraction(y) - x*gain) for x, y in zip(known_samples, actual)]
    assert all(e <= bound if rule == 'nearest_even' else e < bound for e in errors)
    assert all(y == 0 for x, y in zip(known_samples, actual) if x == 0), 'silence changed'
    peak = max(map(abs, actual), default=0)
    if ceiling is not None:
        assert peak <= ceiling, 'ceiling exceeded'
    return dict(decoded_peak=peak, samples=len(actual), max_error=str(max(errors, default=Fraction(0))),
                gain=str(gain), geometry=g1, metadata_exact=True, complete=True)
