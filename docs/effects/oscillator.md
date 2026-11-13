# Shared modulation oscillator, and its role in Chorus and Flanger

Part of [Effects in firmware 1.60](README.md). Findings F047 and F051–F056 in the
[findings ledger](../../research-notes/F-effects/findings-ledger.md). Models:
[tools/fx/osc.py](../../tools/fx/osc.py), [tools/fx/crmath.py](../../tools/fx/crmath.py)
and [tools/fx/fdlibm_sincosf.py](../../tools/fx/fdlibm_sincosf.py).

## Summary

The SP-16 effects share one small modulation oscillator. It is a 0x98-byte object with
**no vtable**, so it does not appear in any RTTI class list. It is **not** the RTTI
`LFO` class (F047). It is **fully reconstructed**: seven waveforms, timing, phase
offset, amplitude/offset, output smoother and sine resync. The Python model is
**bit-exact to the 1.60 code run in a single-function emulator** in 56 runs (3,650
process calls, 423,204 samples) and 68 review cases, with every object field equal
after every call (F053).

| User (1.60) | Waveform | Role | Evidence |
|---|---|---|---|
| Phaser (`0x10d654`) | 1 triangle | all-pass coefficient sweep | F047, [phaser.md](phaser.md) |
| `c_chorus` (`0xff008`) | 0 sine | **delay time** of a modulated delay line | F054, F055 |
| `c_flanger` (`0x100234`) | 0 sine | **delay time** of a feedback delay line | F054, F055 |
| `c_distortion` (`0xfa568`) | 0 sine | built, but **never run** | F054 |
| `LfoProcessor` (`0x135da0`, not an FX class) | any 0–6 (*likely*) | sequencer LFO; uses a mono path not modelled here | F054 |

## Waveforms and timing

Per sample: c += 1; if c ≥ P, then c −= P (float32); x = wave(c). After the loop, per
block: the resync check, then out = offset + amplitude·x, then (unless smoothing is
off) a one-pole smoother y = a·out + b·y per channel (F052).

- **Period:** P = fs/f − 1, so the true period is P samples (P ≥ 1). `init` uses fs.
  `setFrequency` uses a **literal 44100** (F047).
- **Stereo:** R is the same formula at c + φ·P (wrapped), so **R leads by φ cycles**.

| # | Waveform | Formula (k = slope) | Initial counter |
|---|---|---|---|
| 0 | sine | double-precision recursion y = 2cos w·y₁ − y₂; L = (float)(sin w·y), clamped to ±1; R = cos 2πφ·L − (float)(y₁ − y·cos w)·sin 2πφ | L[i] = sin((i + 2)w) |
| 1 | triangle | k = 4f/fs; x = c·k − 1 for c ≤ P/2, else 3 − c·k | c = P/4 |
| 2 | saw | k = −2f/fs; x = 1 + c·k (falling from 1 to ≈ −1) | c = 0 |
| 3 / 4 / 5 | pulse | duty d = 1/2, 1/4, 1/8: x = +1 if c ≤ d·P, else −1 | c = 0 |
| 6 | random | sample-and-hold of table[(index + offset) mod 0x2000], one new value per period | — |

- **Sine resync.** About once per second (when the resync counter `+0x68` passes fs),
  the sine's amplitude is renormalised: v = clamp(y₁·sin w), y₁ = v/sin w,
  y₂ = cos(±acos v − w)/sin w. A model without this diverges right after the first
  renormalisation, at sample 44,539 (F052).
- **Random.** The leading channel draws a new value at its wrap: R if φ < 0.5,
  otherwise L. The lagging channel takes the leader's previous value at its own wrap.
  The index runs 0…0x2000, so an offset of 0x2000 reads the word just after the table
  (a denormal) (F052).
- **Invalid waveform** (7, −1, 100): `init` returns 0 and sets the waveform to −1.
  `process` then returns 0 and leaves the buffers untouched. `init` with f = 0 or
  fs ≤ 0 also returns 0 (F052).
- **Setters** (F052). setFrequency keeps the phase fraction (c := c·P_new/P_old; the
  sine state is recomputed phase-continuously); f = 0 enters **hold** mode (output
  frozen; only `init` clears it). resetPhase(φ) jumps: triangle c = (φ + ¼)·P (0.25 =
  peak); saw, pulse and random c = φ·P; the sine restarts as cos(2πφ + n·w).
  setPhaseOffset(φ) wraps φ into [0, 1) and moves R only.
- The negative-step branches of triangle and pulse, and the positive-step branch of
  saw, are unreachable because f is floored at a positive value (*likely*).

### The random table (input, not included)

Waveform 6 reads **8192 float32 values stored in the firmware's initialised `.data`
at `0xb70e50`** (uniform in [−1, 1)). Only the constructor references the table
(F051). It is a static table, not a run-time random generator: patching it changes the
emulated output accordingly, and glibc `rand()` matched 0 of 1,000 values. The table is
firmware data, so it is **not published or reconstructed here**. The model takes it as
an argument; see [tools/fx/README.md](../../tools/fx/README.md#input-you-must-supply-the-random-waveform-table).

## Object layout and API (0x98 bytes, no vptr)

| Offset | Contents (F051) |
|---|---|
| `+0x00` / `+0x04` | amplitude (init 1) / offset (init 0) |
| `+0x08` | id, from the global counter `0xb70e4c` (initial value 1, post-incremented by the constructor) |
| `+0x0c` | waveform 0…6 (−1 = invalid) |
| `+0x10` | frequency Hz (floor 0.0044100005) |
| `+0x18` | 1/fs (double) |
| `+0x20` | step (double): sine 2πf/fs, triangle 4f/fs, saw −2f/fs, pulse/random f/fs |
| `+0x28` / `+0x30` / `+0x38` | sine cos w / 2cos w / sin w (doubles); pulse duty at `+0x28` |
| `+0x40` / `+0x48` | sine y[n] / y[n−1] (doubles); other waves: phase position (hold mode) / random held L |
| `+0x50` / `+0x54` | R phase offset (sine: cos 2πφ / sin 2πφ; random: held R) |
| `+0x58` / `+0x5c` | smoother a = 1 − b, b = expf(−2π·hz/fs) (init **50 Hz**) |
| `+0x60` / `+0x64` | smoother state L / R |
| `+0x68` / `+0x6c` | resync counter / period (= fs) |
| `+0x70` / `+0x78` | hold flag / smoother-off flag (doubles) |
| `+0x80` / `+0x84` | counter c / period P |
| `+0x88` / `+0x8c` | random offset / random index 0…0x2000 |
| `+0x90` | → random table `0xb70e50` |

Entry points emulated and modelled (F051):

| Address | Entry |
|---|---|
| `0x100af0` | constructor `(osc, wave, freq, fs)`: calls `init` **first**, then stores the table pointer and id |
| `0x100710` | `init` |
| `0x100b28` | init from period in ms |
| `0x101090` / `0x101320` | setFrequency / setPeriodMs (f = 1000/ms; 0 returns 0) |
| `0x1017d4` / `0x101440` | setPhaseOffset / resetPhase |
| `0x1019d8` / `0x1019e4` / `0x1019f0` / `0x102cb0` | setAmplitude / setOffset / setSmoothingHz / setSmoothingOff |
| `0x102c50` | setRandomOffset |
| `0x101b30` | resync (sine only) |
| `0x101bdc` | process `(osc, bufL, bufR, n)` |
| `0x100b5c` | setWaveform. The same value is a no-op (confirmed); a new value converts the phase position (*likely*, not modelled) |

Read in disassembly or decompiled code only, not emulated (*likely*): `processMono`
`0x1025d4` (LfoProcessor only), `0x1015c8` (re-init from ms/phase/amplitude), getters
`0x100b54`/`0x1012f8`/`0x101620`/`0x1016dc`, and smoothing helpers
`0x101a70`/`0x101ab8`.

### Quirks: memory the constructor never writes

Confirmed in emulation (F051):

- `init` computes the resync phase (`+0x68` = id·448 mod fs) from the id word **before**
  the constructor writes it, i.e. from uninitialised heap. This only shifts the moment
  of the first sine renormalisation.
- `init` for waveform 6 reads the table pointer `+0x90` before the constructor stores
  it. In the emulator this is a NULL read at `0x1008ec`; on the device it reads
  uninitialised memory. So waveform 6 is only usable by re-initialising an existing
  object, which is what `LfoProcessor` does.
- `init` does **not** write the counter `+0x80` for the sine. If that heap word held a
  huge positive float or +inf, the wrap loop would never end. The emulator hung with a
  `0x7F7F7F7F` heap fill. Chorus clears the counter on its first block (resetPhase);
  Flanger and `LfoProcessor` do not.

That fresh heap is zero on the device, making these harmless, is a *guess* (H036).

## Math library

The sine path calls the 1.60 glibc 2.13 libm (F052):

- Double `sin`, `cos` and `acos` are correctly rounded (glibc dbl-64). `crmath.py`
  computes them to ~50 digits with Python's `decimal` and rounds once. It matched
  1,600 / 1,600 / 1,000 cases.
- Float `sinf`/`cosf` are fdlibm and not correctly rounded. `fdlibm_sincosf.py`
  matched 1,500 / 1,500 each; the host math differs.
- glibc `expf` is not always correctly rounded (1 in 1,504 random arguments differs by
  1 ulp), but the real setSmoothingHz path matched the model in 4,006 settings.

## Chorus and Flanger

The full Chorus and Flanger effects are **not** reconstructed yet (H033, H034). What
is confirmed is their core: both are **oscillator-modulated delay lines**, and their
kernels were re-stated bit-exactly against emulation (F055).

| | Chorus (`c_chorus` slot 19 `0xfe710`) | Flanger (`c_flanger` slot 19 `0xff9ac`) |
|---|---|---|
| Oscillator setup (F054) | sine, setFrequency 0.1 Hz, amplitude = 0.0005·fs (22.05), offset = amplitude + 0.2, phase offset 0, smoother 50 Hz | sine, amplitude = 0.001·fs (44.1), offset 44.3, no phase offset |
| What the oscillator drives | **delay time in samples** of one tap per channel | delay time in samples |
| Ring buffer | fs/10 + block = 4,474 samples | 7·fs/1000 + block = 372 samples |
| Read | write, then read at index − d with linear interpolation | out = (1 − fr)·buf[r] + fr·buf[r − 1] |
| Feedback | none | line input = in + y_prev·fb (`+0x10c`); y_prev = the previous **pre-gain** output of that channel |
| Output | wet only (dry/wet is in EffectBase). Output gain `+0xe8` stays 0 until the ring has wrapped once, then rises linearly over ≈3.3 ms. At 64-sample blocks, blocks 0–68 are exactly 0 | × g(d) = d·0.013154167 + 1 − 0.6314 for d ≤ 48 samples, else 1 |
| Delay range | 0.2 … 2·amplitude + 0.2 samples | (as set by amplitude/offset) |

Parameter paths that are known (F054): Chorus slot 25 `0x115d70` passes rate changes
to kernel slot 3 `0xfeb10` (clamped 0.00104…64 Hz), which calls setFrequency. Slot 14
`0x116224` routes index 1 to depth (kernel slot 5 `0xfed90`), index 3 to depth scale
(slot 7 `0xfeecc`), both giving amplitude = depth·scale·0.01·0.0005·fs and offset =
amplitude + 0.2, and index 2 to phase (slot 6 `0xfec34`). Retrigger (`+0xe0`) and a
reset flag set by the constructor (`+0xe2`) call resetPhase(0). Flanger mirrors this
through `0x115f58`, `0xffdc4`, `0xfffd4`/`0x100104`, `0xffe68` and retrigger `+0xf0`.
*Likely*, from four readbacks: Chorus depth scale v → 1 + 9v, Flanger v → 0.1 + 7v,
phase v → index·0.45/19 cycles. Chorus and Flanger, like the Phaser, have an Insert
default Mixratio of 0 (F054).

**Construction** (F056). Chorus, Flanger and Distortion are built **inline** in the
`InsertFxProcessor` constructor (`0x118b50–0x118c64`, `0x118cd8–0x118ddc`,
`0x119060–0x1190ec`). These instruction ranges were emulated, then the Insert
initialisation and tempo feed, then slot 25 (Chorus 120 blocks, Flanger 120,
Distortion 16): the output was non-trivial and identical across runs. Chorus registers
RATE (index 0), SYNC (index 6) and BPM (index 7, 1…999, default 120). Its kernel
(`new(0x100)`) sits at `+0x1b8`.

**Evidence** (F055): Python re-statements of both kernels, fed the emulated oscillator
buffers, were bit-exact. The worker pass covered 15,360 of 15,360 samples each at the
Insert defaults. The review pass covered 17,920 of 17,920 each at non-default settings
(Flanger feedback 0.79/0.94, delays 1.1…281 samples; Chorus delays 0.17…437; L ≠ R;
mid-run changes). Refuted: the oscillator as an amplitude modulator, a constant delay,
and feedback taken after the gain. These re-statements are not separate published
models.

**Still missing** (H033, H034): the full parameter formulas (rate tables at
`0x349778`/`0x349798`, Sync, depth/scale/phase, Flanger feedback mapping) and an
end-to-end slot-25 model for each.

**Distortion** (H035): its oscillator is built but never run. No oscillator call
appears in any `c_distortion` vtable target, and emulation recorded 0 process calls
(F054). Its processing (`0xfa78c`) is *likely*, from decompiled code only: a one-pole
high-pass, a one-pole low-pass, an auto-gain envelope, drive, a blend of a ±1 clip and
a cubic soft clip 1.5x − 0.5x³, ×0.7, then an output low-pass (F056).

## Validation evidence

- **Oscillator model** (F053). Worker pass: 56 runs, 3,650 process calls, 423,204
  samples. They covered all waveforms, slow/fast/non-integer periods, phase,
  amplitude/offset, smoothing on/off/changed, variable n, every setter mid-run, hold,
  resync and invalid waveforms. Outputs, return codes and every field matched after
  every call, max error 0.
- **Review** (F053): 68 more cases (re-init at 48 kHz, Nyquist, f > fs, negative or
  floored f, n = 0…4096, random setter storms) and 27 garbage-fill runs, all exact.
  Planted errors caught: period fs/f, pulse R = L, smoother swap, random wrap.
- The Phaser comparison still passed with its earlier hashes after this work (F053).

## Unknowns

- `setWaveform` with a new value and the mono path (`LfoProcessor`) are not modelled
  (F053).
- Whether fresh heap is zero on the device (H036).
- Chorus/Flanger parameter formulas and end-to-end models (H033, H034); Distortion
  (H035).
