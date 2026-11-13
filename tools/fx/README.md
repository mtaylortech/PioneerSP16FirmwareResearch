# tools/fx — pure-Python models of SP-16 1.60 effects

Our own Python models of four insert effects and the shared modulation oscillator in the
TORAIZ SP-16 **firmware 1.60** application (`EP085_Main_R`). Each model was written
from the analysis in [`../../docs/effects/`](../../docs/effects/). Each one is
**bit-exact to the 1.60 routine run in a single-function emulator** on the test
signals and parameter settings listed on its page. None of them has been compared with
audio recorded from a real SP-16.

**No firmware is included.** The models hold no firmware bytes, no disassembly and no
decompiled code. They contain only the numeric constants of the algorithms (ranges,
table values, literals) as described in the docs. Code is MIT ([../../LICENSE](../../LICENSE)).
The three `fdlibm_*.py` files also carry Sun's fdlibm notice, which must be kept (see
[../../NOTICE.md](../../NOTICE.md)).

## What each file reproduces

| File | Reproduces (1.60) | Validated against the emulated 1.60 code | Doc |
|---|---|---|---|
| `lofi.py` | `LoFi` effect, vtable slot 25 `0xfc0f4` and its parameter path. Also the shared blocks it uses: LinearParameter, SignalGate, IirFilter HPF/LPF/BPF biquads | 52/52 runs bit-exact, plus 30+ review edge cases (F030) | [lofi.md](../../docs/effects/lofi.md) |
| `mmf.py` | `MultiModeFilter`, slot 25 `0x108ee4`, plus GainRamp | 48/48 + 17 review cases (F036) | [multimode-filter.md](../../docs/effects/multimode-filter.md) |
| `peq.py` | `ParametricEqualizer` (2-band EQ), slot 25 `0x10ae70`, plus the IirFilter2 shelf/peak family | 48/48 + 47 review cases (F043) | [parametric-eq.md](../../docs/effects/parametric-eq.md) |
| `phaser.py` | `Phaser`, slot 25 `0x10d630`, including the tempo (BPM) feed. Has its own triangle-only copy of the oscillator | 48/48 + 297 random walks (F050) | [phaser.md](../../docs/effects/phaser.md) |
| `osc.py` | The shared vtable-less oscillator (ctor `0x100af0`, process `0x101bdc`): all 7 waveforms, smoother, phase offset, resync | 56 runs (423,204 samples) + 68 review cases, every field equal after every call (F053) | [oscillator.md](../../docs/effects/oscillator.md) |
| `fdlibm_powf.py` | glibc 2.13 (fdlibm) single-precision `powf`/`logf`/`log10f`, which are not correctly rounded | 4,503 + 16,000 `powf` and 3,002 + 9,000 `log10f` cases equal to the emulated 1.60 libm (F044) | [parametric-eq.md](../../docs/effects/parametric-eq.md#math-library) |
| `fdlibm_tanf.py` | glibc 2.13 (fdlibm) `tanf` | 5,221 harness + 10,055 extra cases (F048) | [phaser.md](../../docs/effects/phaser.md) |
| `fdlibm_sincosf.py` | glibc 2.13 (fdlibm) `sinf`/`cosf` | 1,500 + 1,500 cases (F052) | [oscillator.md](../../docs/effects/oscillator.md) |
| `crmath.py` | Correctly rounded double `sin`/`cos`/`acos` and float `expf`. Own code, using Python's `decimal` module | 1,600 / 1,600 / 1,000 cases equal to the 1.60 glibc double routines (F052) | [oscillator.md](../../docs/effects/oscillator.md) |

Dependencies: `lofi.py` ← `mmf.py` ← `peq.py`; `phaser.py` uses `lofi.py`,
`fdlibm_powf.py` and `fdlibm_tanf.py`; `osc.py` uses `crmath.py` and `fdlibm_sincosf.py`.
Standard library only (`ctypes`, `math`, `struct`, `decimal`); no numpy.

## Using a model

The modules import each other by bare name, so run from this folder or put it on
`sys.path`. Each effect processes one stereo block per call (64 samples on the device):

```python
import sys; sys.path.insert(0, "tools/fx")
from lofi import LoFi

m = LoFi()                 # fs = 44100, block = 64, as the 1.60 app builds it
m.insert_defaults()        # the InsertFxProcessor defaults for this effect
L, R = m.process([0.0] * 64, [0.0] * 64)   # apply the defaults with one block first
m.set_param(2, 0.5)        # parameter index 2 (BITDEPTH) = 0.5 -> 9 bits
L, R = m.process(L_in, R_in)               # two lists of 64 floats -> new lists
```

`MMF`, `PEQ` and `Phaser` have the same interface. The parameter indices are the
indices the 1.60 code uses internally (`EffectBase` vtable slot 14). They are listed
on each effect's page and are not necessarily the on-screen knob order.

Two traps carry over from the firmware:

- **Change detection.** A parameter value equal to its constructor "last" value is
  never applied (F026). Apply the defaults and process one block before setting test
  values, as above.
- **Phaser tempo.** On the device the Insert processor sends the current BPM to
  parameter 7 before every block (F045). Call `set_param(7, bpm)` yourself if you
  use Sync.

The oscillator is used directly:

```python
from osc import Osc
o, next_id = Osc.ctor(wave=1, freq=2.0, fs=44100, id_counter=1)   # triangle, 2 Hz
o.set_amplitude(0.5); o.set_offset(0.5)
L, R = o.process(64)
```

### Input you must supply: the random-waveform table

Waveform 6 (sample-and-hold "random") reads an **8192-entry float32 table stored in the
firmware's initialised `.data` at virtual address `0xb70e50`** (F051). The table is
firmware data, so it is **not included and must not be reconstructed here.** If you
need waveform 6, read it from your own copy of the 1.60 `EP085_Main_R`. Check the
file's SHA-256 against [docs/firmware-reference.md](../../docs/firmware-reference.md)
first. Then pass 8193 floats (the table plus the word that follows it, which an index
quirk can reach) as `table=`. The other six waveforms need no table.

## What the models do not cover

These limits are stated on each doc page. In short:

- **Block size.** `n` must not exceed the block size the object was built with (64).
- **Math library.** `lofi.py`, `mmf.py` and `peq.py` use the host's double `tan`/`pow`
  (and LoFi/MMF the host `log10f` for step counts). The 1.60 glibc can differ in the
  last bit. No test showed a difference in a stored coefficient, but a small residual
  risk remains (F044, open question H029).
- **Not modelled.** Reset (vtable slot 27) for LoFi, MMF and PEQ. Out-of-range
  parameter values that make the firmware read past a table, read through a missing
  stage or assert (LoFi BITDEPTH > ≈1.03, PEQ band type 5). The oscillator's `setWaveform` with a new value and its
  mono path. Waveforms other than the triangle in `phaser.py`.
- **Device floating-point mode.** The scalar VFP code is modelled without
  flush-to-zero (emulated FPSCR = 0, *likely* the device setting); NEON paths flush
  denormals, as the hardware does.
- **The shared EffectBase stages** (activation fade, dry/wet mix, ≈10 Hz post-stage
  high-pass) run *around* slot 25 and are **not** part of these models. See
  [docs/effects/README.md](../../docs/effects/README.md#the-effectbase-interface).

## Verifying against the firmware

The bit-exact claims come from running the real 1.60 machine code, one function at a
time, in the unicorn emulator, with the device's own 1.60 `libm.so.6` and
`libgcc_s.so.1`. A model-versus-emulation harness drove the original routine and the
Python model with the same inputs and compared every output sample. It also compared
object state and stored coefficients. Independent review re-ran each comparison,
added cases and planted deliberate model errors, which were caught.

That harness is published as reference code in [`verify/`](verify/README.md) (research layout, not re-tested there). It only runs with your own copies
of the 1.60 files: `EP085_Main_R` (SHA-256
`3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`, see
[docs/firmware-reference.md](../../docs/firmware-reference.md)) plus `libm.so.6` and
`libgcc_s.so.1` from the same release's root filesystem. To check a model yourself:

1. Obtain and decode 1.60 yourself (see [tools/decode/](../decode/)). Verify the
   `EP085_Main_R` hash.
2. Load it in an emulator at its ELF virtual addresses (image base `0x8000`). Map the
   1.60 libm and libgcc and resolve the imports the effect reaches (`pow`, `powf`,
   `log10f`, `tan`, `tanf`, `trunc`, memory allocation and copies).
3. Build the effect with its real constructor `(obj, 44100, 64)` after running the
   `.init_array` entries listed on its page. Apply the Insert defaults, then call
   vtable slot 25 directly on 64-sample stereo blocks. Pass floats in **core
   registers**: the app uses the soft-float calling convention (F021).
4. Feed the same blocks and parameter changes to the model and compare the outputs
   as raw float32 bits.

The docs give every address and argument needed. The emulation adaptations that were
needed are described in [docs/effects/README.md](../../docs/effects/README.md#how-the-effects-were-validated).
