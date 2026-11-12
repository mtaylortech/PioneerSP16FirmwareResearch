# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below.
#
# The adopted numerical profile (-1 dBFS sample-peak target, mono/stereo, 44.1/48/96 kHz, files up to 50,000,000 bytes).
#
# Original path: experiments/normalization-host-core-20261011/profile.py
# Original SHA-256 (before this header): 3fa7152be9dc95feff3fd95259abeb19443495c41183ff6edba6e45085ff264a
# License: MIT. Host-side tool only: it does not run on, or modify, the SP-16.
# ---------------------------------------------------------------------------
"""Owner-selected initial profile, October 11, 2026. Host fixtures only."""
from decimal import Decimal, localcontext
from fractions import Fraction
from core import Parameters

MAX_BYTES = 50_000_000  # decimal MB; includes RIFF headers and metadata


def owner_profile(block_frames=4096):
    # Precision error is far below one sample unit at either supported depth.
    # Integer targets: PCM16 29204; PCM24 7476354. Independently pinned in tests.
    with localcontext() as ctx:
        ctx.prec = 80
        amplitude = Decimal(10) ** (Decimal(-1) / Decimal(20))
    return Parameters(Fraction(amplitude), 'nearest_even', Fraction(0), 'unchanged',
                      None, (16, 24), (1, 2), (44100, 48000, 96000),
                      MAX_BYTES // 2, MAX_BYTES, block_frames)
