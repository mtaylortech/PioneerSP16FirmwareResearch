# tools/fx — pure-Python models of the SP-16 1.60 effects and mixer

Our own Python models of every reconstructed effect, the shared `EffectBase` wrapper,
the three FX processors, the mixer, the buses, the device output stage and the
headphone router of the TORAIZ SP-16 **firmware 1.60** application (`EP085_Main_R`).
Each model was written from the analysis in [`../../docs/effects/`](../../docs/effects/README.md).
Each one is **bit-exact to the 1.60 routine run in a single-function emulator** on the
test signals and parameter settings listed on its page. None of them has been compared
with audio recorded from a real SP-16.

**No firmware is included.** The models hold no firmware bytes, no disassembly and no
decompiled code. They contain only the numeric constants of the algorithms (ranges,
short tables, literals) as described in the docs. Three larger firmware-derived tables
are **inputs you supply** from your own 1.60 files; they are never stored here (see
[below](#inputs-you-must-supply)).

**Licences.** Everything in `tools/fx/` is MIT ([../../LICENSE](../../LICENSE)), with
two exceptions:

- `glibc_expf.py` is **LGPL-2.1-or-later** ([../../LICENSE-LGPL-2.1](../../LICENSE-LGPL-2.1)).
  It is an own re-implementation of the glibc 2.13 `e_expf.c` algorithm and is
  distributed under the LGPL because of that origin. Its two accurate tables are **not**
  included; they are read at run time from your own 1.60 `libm.so.6`.
  `compressor.py` and `distortion.py` import it.
- The `fdlibm_*.py` files, `glibc_log10.py` and the `log10f`/`logf` port inside
  `ducker.py` follow the public fdlibm algorithms and carry Sun's fdlibm notice, which
  must be kept (see [../../NOTICE.md](../../NOTICE.md)).

## Quickstart (no user-supplied input)

Run from the repository root. This builds the Chorus as the processors build it and
runs its audio entry (slot 25) on a generated 440 Hz sine:

```python
# Quickstart: run the Chorus model on a generated 440 Hz sine (no user-supplied input needed).
import hashlib, math, struct, sys
sys.path.insert(0, "tools/fx")                     # run from the repository root
from chorus import Chorus

fs, n = 44100, 64
ch = Chorus()                                      # 0x2b0-byte Chorus as the processors build it
ch.reset()                                         # slot 27, as on every activation
ch.set_param(1, 0.5)                               # DEPTH
ch.set_param(5, 1.0)                               # MIXRATIO (used by the EffectBase mix, not by slot 25)
out, t = [], 0
for b in range(120):                               # 120 blocks of 64 samples = 174 ms
    L = [math.sin(2 * math.pi * 440 * (t + i) / fs) * 0.5 for i in range(n)]
    R = list(L)
    ch.process(L, R)                               # slot 25: in place, wet signal only
    out += L + R
    t += n
first = next(i for i, x in enumerate(out) if x != 0.0) // (2 * n)
rms = math.sqrt(sum(x * x for x in out[-2 * n * 10:]) / (2 * n * 10))
print("first non-zero block:", first)
print("RMS of the last 10 blocks: %.6f" % rms)
print("SHA-256 of the float32 output:", hashlib.sha256(struct.pack("<%df" % len(out), *out)).hexdigest()[:16])
```

Output of the code above, saved to a file and run with `python3 -B` from the repository root
(Python 3, macOS, 2026-11-14):

```
first non-zero block: 69
RMS of the last 10 blocks: 0.355921
SHA-256 of the float32 output: 408d8763de5e27c5
```

Blocks 0–68 are silent because the Chorus keeps its output gain at 0 until its delay
ring has wrapped once ([chorus.md](../../docs/effects/chorus.md), F060). The output is
the wet signal only; the dry/wet mix happens in the `EffectBase` wrapper
(`effectbase.py`).

## Model index

"Imports" lists the other files of this folder a model needs. Everything else is the
Python standard library (`ctypes`, `math`, `struct`, `decimal`); no numpy.

### Effects (slot 25 and their parameter paths)

| File | Models (1.60) | Findings | Inputs it needs | Imports | Page |
|---|---|---|---|---|---|
| `chorus.py` | `Chorus` + kernel `c_chorus` (Insert 0, Master/Send 2) | F057–F062 | none | `osc` | [chorus.md](../../docs/effects/chorus.md) |
| `flanger.py` | `Flanger` + kernel `c_flanger` (Insert 1, Master/Send 3) | F063–F068 | none | `osc`, `chorus` | [flanger.md](../../docs/effects/flanger.md) |
| `peq.py` | `ParametricEqualizer` (2-band EQ; Insert 2, Master/Send 4), with reset (slot 27) | F038–F044, F150, F153 | none | `lofi`, `mmf`, `crmath`, `fdlibm_powf` | [parametric-eq.md](../../docs/effects/parametric-eq.md) |
| `mmf.py` | `MultiModeFilter` (Insert 3, Master/Send 5), with reset | F032–F037, F150, F175 | none | `lofi`, `crmath` | [multimode-filter.md](../../docs/effects/multimode-filter.md) |
| `insert_delay.py` | `InsertFxDelay` (Insert 4); also the shared ring buffer, `DelayModuleStereo`, HiCut | F075–F079 | none | `lofi`, `chorus` | [insert-delay.md](../../docs/effects/insert-delay.md) |
| `send_delay.py` | `SendFxDelay` (Master/Send 0) | F080, F115–F120 | none | `lofi`, `chorus`, `insert_delay` | [send-delay.md](../../docs/effects/send-delay.md) |
| `send_reverb.py` | `SendFxReverb` / `Reverb9NXSBase` (Master/Send 1) | F121–F127 | none | `lofi`, `chorus`, `insert_delay`, `send_delay`, `fdlibm_powf` | [send-reverb.md](../../docs/effects/send-reverb.md) |
| `lofi.py` | `LoFi` (Insert 5, Master/Send 6), with reset; also the shared LinearParameter, SignalGate and IirFilter biquads | F025–F031, F150–F153, F206–F208 | none | `crmath`, `fdlibm_powf` | [lofi.md](../../docs/effects/lofi.md) |
| `distortion.py` | `Distortion` + kernel `c_distortion` (Insert 6, Master/Send 8) | F069–F074 | the `expf` tables for full bit-exactness (optional; see below) | `osc`, `glibc_expf`, `fdlibm_powf` | [distortion.md](../../docs/effects/distortion.md) |
| `compressor.py` | `FxCompressor` core as run by `InsertFxCompressor` and `SendFxCompressor` (Insert 7, Master/Send 7), incl. the Send look-ahead | F081–F087 | the `expf` tables (**required**; see below) | `fdlibm_powf`, `glibc_expf`, `glibc_log10` | [compressor.md](../../docs/effects/compressor.md) |
| `phaser.py` | `Phaser` (Insert 8, Master/Send 9), with its own triangle-only oscillator copy | F045–F050 | none | `lofi`, `crmath`, `fdlibm_powf`, `fdlibm_tanf` | [phaser.md](../../docs/effects/phaser.md) |
| `ducker.py` | `Ducker` (Insert 9): trigger-driven gain envelope; own `log10f`/`logf` port | F088–F094, F192–F201 | none (triggers are parameters you set) | none | [ducker.md](../../docs/effects/ducker.md) |
| `perf_lofi.py` | `PerformanceFxLoFi`: **never constructed in 1.60**, modelled for completeness | F128–F130 | none | `lofi`, `crmath`, `fdlibm_powf` | [lofi.md](../../docs/effects/lofi.md#performance-fx-lofi-never-constructed) |

### Shared infrastructure, processors and mixer

| File | Models (1.60) | Findings | Inputs it needs | Imports | Page |
|---|---|---|---|---|---|
| `osc.py` | The shared vtable-less oscillator: 7 waveforms, smoother, phase offset, resync | F051–F056 | the random table, **only for waveform 6** | `crmath`, `fdlibm_sincosf` | [oscillator.md](../../docs/effects/oscillator.md) |
| `effectbase.py` | `EffectBase` slot-18 wrapper: `EffectInOutGain` gate, input fade, skip/clamp, post-stage HPF, dry/wet mix, lifecycle slots; any effect model plugs in as slot 25/26/27 | F138–F149 | none | `lofi`, `crmath` | [effectbase.md](../../docs/effects/effectbase.md) |
| `fx_processors.py` | `MasterFxProcessor`, `SendFxProcessor` and the full Insert processor: setFxType, processBlock, bypass, disable, start mode, `MuteSmoother` | F154–F158, F176–F178 | none | `lofi` (effects passed in as `effectbase` objects) | [fx-processors.md](../../docs/effects/fx-processors.md) |
| `sync_convert.py` | Parameter-manager SYNC toggle (slot 34), the time/rate parameter specs, the UI step law | F183–F186 | none | `ducker` | [parameters.md](../../docs/effects/parameters.md) |
| `track_mix.py` | `TrackUnit` / `MultiTrackUnit`: insert position, pan, mutes, send tap, fader, bus sums | F095–F101 | none | none | [signal-flow.md](../../docs/effects/signal-flow.md#track-strip) |
| `bus_mix.py` | `CompositeFxUnit`, `SendFxUnit` return fader, `MasterOutUnit`, DSF drive gain | F102–F108 | none | `track_mix` | [signal-flow.md](../../docs/effects/signal-flow.md#send-bus-and-master-bus) |
| `device_out.py` | `AudioDeviceOutputUnit`: OutputVolume, FixedAttenuator (−0.5), BulkMute | F109–F114 | the OutputVolume table (for any OutputVolume gain) | `track_mix` | [signal-flow.md](../../docs/effects/signal-flow.md#device-output-stage) |
| `headphone_mix.py` | `HeadphoneUnit` + `HeadphoneRouter` cue mix, `Output12Router` main-output selector | F209–F213 | none (monitor pairs are inputs you pass) | `track_mix`, `fx_processors` | [signal-flow.md](../../docs/effects/signal-flow.md#main-output-and-headphones) |

### Maths libraries (match the 1.60 glibc 2.13 libm)

| File | Models | Findings | Inputs it needs | Imports | Page |
|---|---|---|---|---|---|
| `crmath.py` | Correctly rounded double `sin`/`cos`/`acos`/`tan`/`pow`/`exp` and float `expf` (own code, `decimal`) | F052, F206–F208 | none | none | [numerics.md](../../docs/effects/numerics.md) |
| `fdlibm_powf.py` | fdlibm `powf`/`logf`/`log10f` (not correctly rounded) | F044 | none | none | [numerics.md](../../docs/effects/numerics.md) |
| `fdlibm_tanf.py` | fdlibm `tanf` | F048 | none | none | [numerics.md](../../docs/effects/numerics.md) |
| `fdlibm_sincosf.py` | fdlibm `sinf`/`cosf` | F052 | none | none | [numerics.md](../../docs/effects/numerics.md) |
| `glibc_log10.py` | glibc 2.13 double `log10` (fdlibm algorithm on a correctly rounded `log`; not correctly rounded) | F082 | none | none | [numerics.md](../../docs/effects/numerics.md) |
| `glibc_expf.py` | glibc 2.13 table-driven `expf` (not always correctly rounded). **LGPL-2.1-or-later** | F070, F082, F206 | the `expf` tables | `crmath`; `lief` to read the tables | [numerics.md](../../docs/effects/numerics.md) |

## Using a model

The modules import each other by bare name, so run from this folder or put it on
`sys.path`. Each effect processes one stereo block per call (64 samples on the device),
in place or returning new lists, as its docstring says. Parameter indices are the ones
the 1.60 code uses internally (`EffectBase` vtable slot 14); they are listed on each
effect's page and are not necessarily the on-screen knob order.

```python
import sys; sys.path.insert(0, "tools/fx")
from lofi import LoFi

m = LoFi()                 # fs = 44100, block = 64, as the 1.60 app builds it
m.insert_defaults()        # the InsertFxProcessor defaults for this effect
L, R = m.process([0.0] * 64, [0.0] * 64)   # apply the defaults with one block first
m.set_param(2, 0.5)        # parameter index 2 (BITDEPTH) = 0.5 -> 9 bits
L, R = m.process(L_in, R_in)               # two lists of 64 floats -> new lists
```

Traps that carry over from the firmware:

- **Change detection.** A parameter value equal to its constructor "last" value is
  never applied (F026). Apply the defaults and process one block before setting test
  values, as above.
- **Tempo.** On the device the processors send the current BPM (clamped 1…999) to
  parameter 7 of the tempo-synced effects before every block (F017, F156). Call
  `set_param(7, bpm)` yourself if you use SYNC.
- **Reset.** The processors call slot 27 (`reset()`) on every activation. Some effects
  need it before the first block (the Reverb is silent without it, F126).
- **The wrapper.** The per-effect models are slot 25 only. The activation fade, the
  dry/wet mix and (for six effects) the 10 Hz post-stage high-pass are in
  `effectbase.py`; the type switch, bypass and disable are in `fx_processors.py`. See
  [effectbase.md](../../docs/effects/effectbase.md).

## Inputs you must supply

These are firmware data. They are **not included and must not be added here.** Read them
from your own copy of the 1.60 files (check the `EP085_Main_R` SHA-256
`3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464` against
[docs/firmware-reference.md](../../docs/firmware-reference.md) first). Never commit
those files.

| Input | Used by | How to pass it | Without it |
|---|---|---|---|
| Oscillator random table: 8192 float32 at `.data` `0xb70e50` of `EP085_Main_R` (F051) | `osc.py` waveform 6 only | `table=` (8193 floats: the table plus the word after it, which an index quirk can reach) | waveforms 0–5 work; waveform 6 cannot run. Chorus and Flanger do not need it |
| glibc `expf` tables `__exp_atable` (355 doubles) and `__exp_deltatable` (178 floats) of the 1.60 `libm.so.6` | `glibc_expf.py`, hence `compressor.py` and `distortion.py` | `glibc_expf.load_tables(path_to_your_libm)` **before** building a `Compressor`; needs `pip install lief` | `compressor.py` cannot be built (it loads the tables on first use). `distortion.py` falls back to `crmath.expf`, which differs from the 1.60 `expf` in about 1 in 3,000 arguments |
| OutputVolume table: 1024 × u16 at `0x83d750` of `EP085_Main_R` (F110) | `device_out.py` | `device_out.load_table(path_to_your_EP085_Main_R)` (hash-checked) | OutputVolume gains cannot be computed; the rest of the stage works |

**Default paths use the research-folder layout.** Where a model has a default path
(`glibc_expf.load_tables()` → `decoded/lib/libm.so.6`, `device_out.load_table()` →
`target/EP085_Main_R_fw160`), it resolves relative to where the models sat in the
research workspace, which here is the repository root. Pass the path explicitly. The
`.gitignore` blocks `target/`, `decoded/`, `*.so.*` and `EP085_Main_R*`, but check what
you stage anyway.

## What the models do not cover

These limits are stated on each doc page. In short:

- **Block size.** `n` must not exceed the block size the object was built with (64).
- **Out-of-range values** that make the firmware read past a table, read through a
  missing stage or assert (LoFi BITDEPTH > ≈1.03, PEQ band type 5). The models raise an
  error instead.
- **Not modelled.** The oscillator's `setWaveform` with a new value and its mono path
  (`LfoProcessor`); waveforms other than the triangle in `phaser.py`; LFO → FX parameter
  modulation and per-step FX locks (open, H068, H003/H070); the ALSA copy stage and the
  codecs (H015).
- **Floating-point mode.** The device runs its audio threads with FPSCR flush-to-zero
  off (F202–F205). The models do the same for scalar VFP code; NEON paths flush
  denormals, as the hardware does. See [numerics.md](../../docs/effects/numerics.md).
- **Maths library.** The models no longer use the host's `tan`, `pow`, `exp` or
  `log10f`. They use `crmath.py` and the fdlibm/glibc ports, which equal the emulated
  1.60 libm on every tested argument (F206–F208).
- **Fresh heap.** A few routines read memory their constructor never writes; the models
  assume zero (H036).

## Verifying against the firmware

The bit-exact claims come from running the real 1.60 machine code, one function at a
time, in the unicorn emulator, with the device's own 1.60 `libm.so.6` and
`libgcc_s.so.1`. A model-versus-emulation harness drove the original routine and the
Python model with the same inputs and compared every output sample. It also compared
object state and stored coefficients. Independent review re-ran each comparison,
added cases and planted deliberate model errors, which were caught.

That harness is published as reference code in [`verify/`](verify/README.md) (research
layout, not re-tested in this layout). It only runs with your own copies of the 1.60
files. To check a model yourself without it:

1. Obtain and decode 1.60 yourself (see [tools/decode/](../decode/)). Verify the
   `EP085_Main_R` hash.
2. Load it in an emulator at its ELF virtual addresses (image base `0x8000`). Map the
   1.60 libm and libgcc and resolve the imports the effect reaches (`pow`, `powf`,
   `expf`, `log10`, `log10f`, `tan`, `tanf`, `trunc`, memory allocation and copies).
3. Build the effect with its real constructor `(obj, 44100, 64)` after running the
   `.init_array` entries listed on its page. Apply the Insert defaults, then call
   vtable slot 25 directly on 64-sample stereo blocks. Pass floats in **core
   registers**: the app uses the soft-float calling convention (F021).
4. Feed the same blocks and parameter changes to the model and compare the outputs
   as raw float32 bits.

The docs give every address and argument needed. The emulation adaptations that were
needed are described in [docs/effects/README.md](../../docs/effects/README.md#how-the-effects-were-validated).
