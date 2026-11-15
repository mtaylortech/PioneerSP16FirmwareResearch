# Numerics for a bit-exact reimplementation (firmware 1.60)

Part of [Effects and mixer in firmware 1.60](README.md). This page lists the
floating-point facts a reimplementation needs to reproduce the 1.60 effects and mixer
bit for bit: the calling convention, the FPSCR mode on the audio threads, denormal
handling in scalar VFP and NEON code, rounding helpers, and which maths-library routines
are and are not correctly rounded. Findings F009–F011, F020, F021, F044, F146, F202–F208
and the libm notes in the effect findings, in the
[findings ledger](../../research-notes/F-effects/findings-ledger.md). Models:
[crmath.py](../../tools/fx/crmath.py), [fdlibm_powf.py](../../tools/fx/fdlibm_powf.py),
[fdlibm_tanf.py](../../tools/fx/fdlibm_tanf.py),
[fdlibm_sincosf.py](../../tools/fx/fdlibm_sincosf.py),
[glibc_expf.py](../../tools/fx/glibc_expf.py) and
[glibc_log10.py](../../tools/fx/glibc_log10.py), plus the `log10f` port inside
[ducker.py](../../tools/fx/ducker.py).

## Summary

- The app is built for **VFPv3 + NEON** with the **soft-float base calling
  convention**: float and double arguments and results travel in core registers
  (r0–r3), not in s/d registers (F011, F021, F202).
- **FPSCR is never changed on the audio threads.** Every thread of the app runs with
  flush-to-zero **off** (FZ = 0), default-NaN **off** (DN = 0) and **round to
  nearest**. This is the same mode the emulator used, so the models' assumption is the
  device behaviour (F202–F205).
- So **scalar VFP code keeps denormals**, while **NEON code always flushes denormals
  to zero** (ARMv7 NEON ignores FPSCR.FZ). Several routines mix the two: a NEON body
  for groups of four samples and a VFP tail. The models follow both behaviours
  (F146, F205).
- Arithmetic is float32 with a rounding after **every** operation. Multiply-accumulate
  is **not fused** (F183, F146). Some coefficient steps are computed in double and
  stored as float32 (each effect page says which).
- The 1.60 root filesystem ships **glibc 2.13** (F044). Its double `tan`, `pow`, `exp`,
  `sin`, `cos`, `acos` are **correctly rounded**; its float `powf`, `log10f`, `tanf`,
  `sinf`, `cosf`, `expf` and its double `log10` are **not**. The models use own
  correctly rounded routines for the first group and own re-implementations of the
  glibc/fdlibm algorithms for the second. **No model calls the host's maths library**
  for a value that reaches the output (F206–F208).

## Calling convention

- Floats pass in core registers (soft-float base AAPCS), both in the app and in the
  1.60 libm. Examples (F021): `pow` at `0xfb3d8` passes x in r0:r1 and y in r2:r3 and
  returns in r0:r1; `log10f` at `0x13818` passes its argument in r0 (`movt r0,#0x4248`
  = 50.0f) and returns in r0; the slot-14 setter receives its float in r2
  (`vmov r2, s15` at `0x116b18`/`0x116b20`); `0x106c7c` receives 10.0f in r2. Nine
  call sites were checked in total.
- The real 1.60 libm reads core registers too: `pow` starts by moving r0–r3 into d9/d8,
  and `log10f` moves r0 into s16 (F021).
- An emulation harness must therefore pass floats in core registers. With s0/d0/d1
  zeroed at each call, `pow` and `log10f` results matched at 0 ulp (F021).
- `.ARM.attributes` of the main binary: ABI_FP_denormal = 1 (IEEE denormals),
  ABI_FP_number_model = 3, VFPv3 + NEON (F202).

## FPSCR on the audio threads

**The main binary never writes FPSCR** (F202, confirmed). No `vmsr`/`fmxr` to any VFP
system register and no `mcr p10/p11` exists in any loadable segment (a sweep of
2,981,538 ARM instructions plus a byte-wise pattern search, done twice independently).
The image has no Thumb code. All 5,302 FPSCR reads are `vmrs APSR_nzcv, fpscr`, the
flag transfer after a compare, so there is no read-modify-write of the mode bits. There
are no FP-environment imports (`fe*`, `__setfpucw`, setjmp/longjmp), and the binary
(JUCE v3.1.1) has no flush-to-zero code path. This corrects the *likely* in F020 to
confirmed.

**No library mapped into the process sets FZ or DN** (F203, confirmed for the census and
the masks). Of the 25 needed libraries, only 11 functions write FPSCR: libm
`feclearexcept`, `fesetexceptflag`, `fesetround`, `feholdexcept`, `fesetenv`,
`fedisableexcept`, `feenableexcept`; libc `__setfpucw`, `__longjmp`,
`____longjmp_chk`; ld.so `__longjmp`. Each only restores or clears:

- `fesetround` touches only the rounding-mode bits 22–23; `feholdexcept` clears traps
  and flags; `fesetenv` with the default environment clears FZ.
- `__setfpucw` runs only from libc's `_init`, and only if `__fpu_control` (0) differs
  from the loader's value; it writes FZ = 0.
- `__longjmp` restores the word the same thread's setjmp saved.
- The main binary reaches these writers only through libm `expf` (19 call sites to the
  PLT stub `0x103fc`). Inside, glibc's `__ieee754_expf` holds the environment, sets
  round-to-nearest and restores it in one straight-line block. Emulating the real 1.60
  libm: 30 of 30 `expf` calls (worker) and 1,224 calls of 21 functions from 8 entry
  FPSCR states (review): bits 22–25 never changed.

That address-taking without a relocation inside a library could reach a writer is
*likely* not possible and in any case moot: every writer only restores or clears
(F203).

**The kernel starts every thread with FPSCR = 0** (F204, confirmed). The 1.60 kernel
(Linux 3.0.101) zeroes the thread's VFP state on exec, with FPSCR = 0, and copies the
parent's VFP state on clone. Its other FPSCR writes are the exception and lazy-restore
paths; signal delivery saves and restores the interrupted FPSCR. The published kernel
source of the same build agrees (round-to-nearest; the flush-to-zero flag is unused).

**Result** (F204, F205): every thread of the app, including the ALSA thread and the
AudioWorker threads, runs with FZ = 0, DN = 0 and round-to-nearest for its whole
lifetime. Only the condition flags and the sticky exception flags change. The emulator
also runs guests with FPSCR = 0, and a hand-encoded test showed the setting reaches the
guest: a normal × normal product giving a denormal returns `0x000116c2` with FZ = 0 and
0 with FZ = 1; NEON `vmul.f32` flushes in both modes (F205).

## Denormals: scalar VFP versus NEON

ARMv7 NEON arithmetic always flushes denormal inputs and results to zero, whatever
FPSCR.FZ says. Scalar VFP arithmetic follows FPSCR, and FZ is 0 on the device. A
bit-exact model must know which unit each routine uses (F205).

| Routine | Unit | Denormals | Finding |
|---|---|---|---|
| `IirFilter` biquad process `0xe16dc` (LoFi, MMF, PEQ) | NEON, L/R in two lanes | flushed | F027 |
| EffectBase post-stage high-pass process `0xe1490` | NEON | flushed | F147 |
| EffectBase dry/wet mix `0x10770c` | NEON for groups of 4, VFP for the n % 4 tail | flushed in the NEON part, kept in the tail | F146 |
| JUCE `copyWithMultiply` `0x5792c8` (pan, volume, output selectors) | NEON for the first 4·⌊k/4⌋ samples of a constant-gain segment, scalar tail | flushed in the NEON part, kept in the tail | F101 |
| Phaser kernel `0x10cf40` | NEON, L/R lanes | flushed | F046 |
| Insert Delay read/feedback path | NEON | flushed | F078 |
| Send Delay adds; Send Reverb comb-sum add `0x578a6c` | NEON | flushed | F120, F122 |
| Flanger feedback path; Compressor; most per-sample effect code | scalar VFP | **kept** | F066, F085, F205 |

Consequences (F205):

- The Flanger's silence tail at feedback 0.99 decays through denormals as modelled. With
  FZ = 1 it would diverge once |y| < about 1.8e−37; the device uses FZ = 0, so the
  model holds (F066, F205).
- Compressor outputs for denormal input follow scalar VFP with FZ = 0, as modelled
  (F085, F205).
- The models implement the NEON flush with small helpers (`ftz`, `nmul`, `nadd`,
  `nsub` in `lofi.py`; `neon_mul`, `neon_add` in `track_mix.py`).
- One known gap: the track-mix model does not model the four `OutputSelector` ×1.0
  passes through `copyWithMultiply`. On denormal input 24,797 of 645,120 samples differ
  through the real selectors; on normal audio 0 of 860,160 differ (F101, H053). This
  matters only for bit-exact denormal tails.

## Rounding and conversion helpers

| Operation | 1.60 code pattern | Behaviour | Model |
|---|---|---|---|
| JUCE `roundToInt` | convert to double, add 1.5·2^52, take the low word | round half to **even** for \|x\| < 2^31 (62.5 → 62, 187.5 → 188) | `round(float(x))` (`sync_convert.round_to_int`, `rint` helpers) (F165, F183) |
| Float → int truncation | `vcvt.s32.f32` | toward zero, **saturating**; NaN → 0 | `ducker.trunc` (F183) |
| Double `trunc` | libm `trunc` | exact | `math.trunc` (F020, F027) |
| Float ops | one VFP instruction each | rounded to float32 after each operation; `vmla` not fused | `F(x)` = `ctypes.c_float` round trip (F183) |
| Mix `0x10770c` | two products and a sum | out = f32(f32(x·d) + f32(y·w)): two roundings | `effectbase.py` (F146) |

A single-rounding variant of the mix and a double-precision tempo factor in the SYNC
conversion were both refuted (F146, F183).

## Maths library: what is correctly rounded

The 1.60 root filesystem ships glibc 2.13 (F044). The emulator maps the device's own
1.60 `libm.so.6` and `libgcc_s.so.1`, so every result below compares an own routine
with the real 1.60 libm run in a single-function emulator.

| Routine (PLT stub in the app) | 1.60 implementation | Correctly rounded? | Model routine | Evidence |
|---|---|---|---|---|
| double `tan` (`0x10e58`) | glibc dbl-64 | **yes** | `crmath.tan` | 15,018/15,018 + about 16,600 review cases (F206) |
| double `pow` (`0x11698`) | glibc dbl-64 | **yes** | `crmath.pow` | 13,503/13,503 + review (F206); Ducker 2,498 args (F090) |
| double `exp` (`0x1144c`) | glibc dbl-64 | **yes** | `crmath.exp` | 12,501/12,501 (F206) |
| double `sin`, `cos`, `acos`, `sincos` | glibc dbl-64 (IBM Accurate Mathematical Library) | **yes** | `crmath` | 1,600/1,600, 1,600/1,600, 1,000/1,000 (F052) |
| `sqrt` (`0x10210`), `sqrtf` (`0x10ef4`) | IEEE | exact | `math.sqrt` | F206, F208 |
| float `powf` (`0xff40`) | fdlibm (glibc 2.13 `e_powf.c`) | **no**: 13,718/16,000 correctly rounded, max 6 ulp | `fdlibm_powf.powf` | 4,503/4,503 + 16,000/16,000 equal to 1.60 (F044) |
| float `log10f` (`0x10ab0`) | fdlibm (`e_log10f.c` on `e_logf.c`) | **no**: 7,838/9,000, max 2 ulp | `fdlibm_powf.log10f`; own port in `ducker.py` | 3,002/3,002 + 9,000/9,000 (F044); Ducker 2,504 args (F090) |
| float `tanf` (`0x104c8`) | fdlibm | **no** | `fdlibm_tanf.tanf` | 5,221/5,221 + 10,055 (F048) |
| float `sinf`, `cosf` | fdlibm | **no** | `fdlibm_sincosf` | 1,500/1,500 each (F052) |
| float `expf` (`0x103fc`) | glibc 2.13 table-driven `e_expf.c` | **no**: about 1 in 1,500–3,000 arguments differs by 1 ulp | `glibc_expf.expf` (tables from your libm) | 3,000/3,000 and 20,000/20,000 (F070); 30/30 (F203) |
| double `log10` | fdlibm `e_log10.c` algorithm on a correctly rounded `log` | **no**: 81/1,504 differ by 1 ulp | `glibc_log10.log10` | 1,504 + 7,959 args (F082) |

The host's maths library is not a substitute. On the macOS host, `math` differed from
1.60 in `tan` 4,830, `pow` 9, `exp` 21 and `log10f` 1,597 of the worker's cases (F206).
A PEQ variant built on the host `powf` matched only 284 of 2,048 samples (F044).

### Which model needs which routine

| Model | Routines | Finding |
|---|---|---|
| `lofi.py` | `crmath.tan`, `crmath.pow`, `fdlibm_powf.log10f` | F207 |
| `mmf.py` | `crmath.pow`, `fdlibm_powf.log10f` (through `lofi`) | F207 |
| `peq.py` | `crmath.tan`, `crmath.pow`, `fdlibm_powf.powf`, `log10f` | F044, F207 |
| `perf_lofi.py` | `crmath.pow`, `fdlibm_powf.powf` | F207 |
| `effectbase.py` (post-stage HPF) | `crmath.tan` | F147, F207 |
| `phaser.py` | `crmath.exp`, `fdlibm_tanf.tanf`, `fdlibm_powf.powf` | F048, F207 |
| `osc.py` (and so `chorus.py`, `flanger.py`, `distortion.py`) | `crmath` sin/cos/acos, `fdlibm_sincosf`, `crmath.expf` | F052, F208 |
| `distortion.py` | `glibc_expf.expf`, `fdlibm_powf.powf` | F070 |
| `compressor.py` | `glibc_expf.expf`, `glibc_log10.log10`, `fdlibm_powf.powf` | F082 |
| `ducker.py` | own correctly rounded `pow`, own `log10f` port | F090 |
| `insert_delay.py`, `send_delay.py` | own correctly rounded double `tan` and `pow` (decimal, inside `insert_delay.py`) | F076, F120 |
| `send_reverb.py` | the same `tan` (through `insert_delay`), `fdlibm_powf.powf` (comb gains) | F124 |

### Host-libm independence (F206–F208)

Earlier versions of several models called the host's `math.tan`,
`math.pow`, `math.exp` and a host-based `log10f`. All 19 such call sites were replaced
by one-token swaps to `crmath` and `fdlibm_powf.log10f`, and each was mapped to a
direct call to the matching PLT stub in the firmware (F207). Then the real 1.60
coefficient routines with the real libm were compared with the models in 62,000 random
settings, comparing float32 coefficient words, step counts and multipliers: biquad
coefficients (12,000 at 44.1/48/96 kHz), first-order high-pass (10,000), PEQ
configure (6,000) and coefficients (4,000), LoFi ramp setup (5,000) and apply (4,000),
MMF (5,000 + 3,000), PerfLoFi apply (3,000) and the PEQ gain law (10,000): **0
mismatches** (F207).

The old host-libm models got 0 float32 words or step counts wrong in the same 62,000
settings; only 2 of 6,000 PEQ configure settings stored a double that differed by 1 ulp.
So the earlier residual (F044) was real in double precision but did not reach a float32
coefficient in this sample (F207). A trap run in which every host transcendental call
raised found 0 host calls in any model, across range-end and random parameters and the
Phaser at five sample rates (F207). Every earlier verifier still passed with
byte-identical outputs (F207).

Remaining uses of `math.*` in the models (F208): IEEE-exact `sqrt`/`sqrtf`; the
track-mix static table (checked exhaustively); exact powers of two; special-value
fallbacks in `fdlibm_powf` and `glibc_log10` (*likely* unreachable; 0 calls in the trap
run, not exhaustive); the optional `HostLibm` back-end of `osc.py` (the default is
`OwnLibm`); and a dB printout in `device_out.py` (diagnostics only).

`osc.OwnLibm.expf` is correctly rounded, not glibc-exact. It equals the emulated 1.60
`expf` on the reachable 50 Hz smoothing initialisation at six sample rates and in 3,000
random smoothing settings, so the residual is *likely* nil in normal use (F208, F052).

### Limits of the own routines

| Routine | Limit | Reached by a model? |
|---|---|---|
| `crmath.pow` | wrong on exact double midpoints (for example pow((2^27 − 1)·2^−26, 2)) | *likely* not: the modelled bases and exponent ranges cannot produce one (argued, not exhaustive) (F206) |
| `crmath.tan` | valid for \|x\| ≲ 1e40 | no (F206) |
| `fdlibm_tanf` | \|x\| < 3π/4, else NotImplementedError | the Phaser at fs = 22,050 Hz reaches x = 2.85 and fails (H102). At 44.1 kHz the Phaser reaches \|x\| ≤ 1.42 |
| `fdlibm_sincosf` | \|x\| ≤ 2^7·π/2 | no (the oscillator reaches \|x\| < 2π) |
| `fdlibm_powf` | finite positive x, finite y; special values only partly | no (F044, F208) |
| `glibc_log10`, `ducker.log10f` | finite positive (normal) arguments | no |
| `glibc_expf` | outside about −103.97 < x < 88.72 falls back to `crmath.expf` | no |

## Inputs and licences of the libm models

- `crmath.py` is own code (Python `decimal` at 60 digits, one final rounding). Its
  mentions of glibc and the IBM library say what it matches, not what it copies.
- `fdlibm_powf.py`, `fdlibm_tanf.py`, `fdlibm_sincosf.py`, `glibc_log10.py` and the
  `log10f` port in `ducker.py` are own Python re-implementations of the published
  fdlibm algorithms. They keep Sun's fdlibm notice. See [NOTICE.md](../../NOTICE.md).
- `glibc_expf.py` is an own re-implementation of the glibc 2.13 `e_expf.c` algorithm. It
  is distributed under **LGPL-2.1-or-later** because of that origin
  ([LICENSE-LGPL-2.1](../../LICENSE-LGPL-2.1)); everything else in `tools/fx/` is MIT.
  Its two accurate tables (`__exp_atable`, 355 doubles; `__exp_deltatable`, 178 floats)
  are **not** in the file and cannot be derived from a formula. `load_tables(path)`
  reads them at run time, by symbol, from **your own 1.60 `libm.so.6`** (it needs the
  `lief` package). Without the tables, `expf` falls back to the correctly rounded
  `crmath.expf`, which differs from 1.60 in about 1 of 3,000 arguments (F070).
  `compressor.py` loads the tables when it first builds its constants, so it needs the
  libm; `distortion.py` uses whatever is loaded and otherwise falls back.

## 1.60 code map

| Address | What it is |
|---|---|
| `0x10e58`, `0x11698`, `0x1144c` | PLT stubs: `tan`, `pow`, `exp` (double) |
| `0xff40`, `0x10ab0`, `0x104c8`, `0x103fc` | PLT stubs: `powf`, `log10f`, `tanf`, `expf` |
| `0x10210`, `0x10ef4` | PLT stubs: `sqrt`, `sqrtf` |
| `0xfb3d8`, `0x13818`, `0x116b18`, `0x1194c8` | soft-float call sites checked (F021) |
| `0xe16dc` | NEON biquad process |
| `0xe1490` | NEON first-order high-pass process (EffectBase post-stage) |
| `0x10770c` | EffectBase dry/wet mix (NEON body, VFP tail) |
| `0x5792c8` | JUCE `copyWithMultiply` (NEON body, scalar tail) |
| `0x578a6c` | NEON add used by the reverb comb sum |
| libm `0x23260` | `__ieee754_expf` (holds and restores the FP environment) |

## Validation evidence

- **FPSCR** (F202–F205): the census script's output digest `dded7f1fc4d9a806` was
  reproduced by the review; a full-image byte search found 0 FPSCR writes. The review
  added an all-ELF scan of the 1.60 root filesystem payload (about 940 files: only an
  unlinked `liboil` and the separate `perf` program write FPSCR), a relocation scan, an
  extended libm run and a read of the kernel's VFP thread code. Those extra review
  scripts are not part of the published verifiers (H101).
- **Libm** (F206, F207): `H029_libm_exact.py` reported 0 failed checks (report
  `c6c75ae1…20b1`, reproduced byte-identically by the review) against the real 1.60
  `libm.so.6` emulated in unicorn. The review added about 26,000 arguments, including
  tan at 11 sample rates, 25 tan and 22 pow cases near a rounding tie mined from 1.2
  million candidates (down to 4e−7 ulp from a tie), UI-step lattices and `log10f` near
  1: the own routines equal the emulated 1.60 libm in every case.
- **fdlibm and glibc ports** (F044, F048, F052, F070, F082, F090): case counts in the
  table above.

All results are bit-exact to the 1.60 routine run in a single-function emulator.
Nothing was measured on a physical SP-16.

## Unknowns

- **Denormal parity of the track mix through the real output selectors** (H053).
- **Phaser at 22.05 kHz** (H102): a model range limit at a non-default rate.
- **Compressor ratio index 0** (H048): out-of-range v ≈ −0.036…−0.033 makes the model
  divide by zero where the device computes 1/0 = +inf.
- **Infinite or NaN input** (H067): the models raise where the firmware's `vcvt`
  saturates.
- **Review-only FPSCR checks** (H101): porting the review's extra scans into the
  published verifiers.

See [open-questions.md → Effects](../open-questions.md#effects).
