# tools/normalization — host-side WAV peak normalization (the "Normalize" study)

The SP-16 has no built-in "normalize sample" function. Part of the research
asked whether one could be added. That integration was **not** achieved (see
`docs/findings.md`, Normalize section), but the host-side numerical part was
finished and is useful on its own.

| File | Role |
|---|---|
| `core.py` | Two-pass normalizer: finds the single maximum absolute sample across the whole file and all channels, applies one exact rational gain to every channel, rounds to nearest with ties-to-even, no dither. Exact digital silence stays unchanged. Unsupported encodings, chunks or geometry are **refused**, not silently converted. |
| `profile.py` | The adopted settings: −1 dBFS sample-peak target; PCM16 and PCM24; mono/stereo; 44.1/48/96 kHz; files up to 50,000,000 bytes. Integer peak ceilings at −1 dBFS: 29204 (PCM16), 7476354 (PCM24). |
| `oracle.py` | Independent checker that re-decodes input and output itself (does not import `core.py`) and verifies the result is within half a sample unit of the exact target. |
| `check_fixtures.py` | Generates synthetic WAVs (including ~100 MB large cases) and runs 278 checks, including deliberate wrong-output and refusal cases. |
| `NUMERICAL_SPEC.md` | Why these choices; which were owner product decisions rather than industry standards. |

```sh
cd tools/normalization
python3 -B check_fixtures.py          # writes results/ and fixtures/ beside itself
```

Verified for this release: the published copies run standalone with Python
3.10 stdlib and report `PASS, 278 checks` (≈1.3 MB of scratch output in a
normal run; budget more if the large cases are kept).

Limits (from the research): this is a disposable-file host tool. It makes no
claim about safe in-place replacement of arbitrary files, preserving every WAV
metadata schema, or behaviour on the instrument. A separate macOS prototype
that wired this into a preview/Keep/Discard flow is described in the findings
but not published.
