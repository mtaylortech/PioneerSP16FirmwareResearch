# Effects (FX) and mixer in firmware 1.60

How the TORAIZ SP-16 application processes audio from each track to the outputs: the
insert, master and send effects, the mixer, the send/return bus, the master bus, the
output stage and the headphone router. Each effect has its own page: the full
algorithm, every parameter formula, the object layout, the 1.60 addresses and a
pure-Python model. Someone who wants to reimplement or study an SP-16 effect should
be able to rebuild it from its page and its model alone.

**Scope: firmware 1.60 only.** Every address is a virtual address in the 1.60
`EP085_Main_R` (12,000,396 bytes, SHA-256
`3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`, image base `0x8000`).
Every address is wrong for every other version. A few facts carried over from earlier
1.50 work are marked **[1.50]** and have not been re-located in 1.60. No firmware bytes,
no disassembly and no decompiled listings are reproduced here. Read
[DISCLAIMER.md](../../DISCLAIMER.md) first.

## How to use these pages

- Start with [signal-flow.md](signal-flow.md): the whole engine end to end, with every
  stage's position, gain law and block size.
- Then read the page of the effect you care about. Each page has the same sections:
  summary, where it sits, signal flow, parameter table, state and object layout, 1.60
  addresses, lifecycle (activation, reset, bypass, type switching, SYNC), quirks,
  validation evidence, unknowns and the model file.
- The models are in [tools/fx/](../../tools/fx/). They are plain Python with no
  dependencies beyond the standard library. A few need an input that you supply from
  your own 1.60 files (see each model's entry in the tools README).
- **Labels.** **confirmed** = shown in the code and checked (for algorithms:
  bit-exact in emulation, see [below](#how-the-effects-were-validated)); **likely** =
  strong evidence, not proven; **guess** = plausible. Unlabelled statements on these
  pages are confirmed.
- **Finding IDs.** Every claim carries a finding ID (`F0xx`, `F1xx`, `F2xx`). The IDs
  refer to the scrubbed research ledger
  [research-notes/F-effects/findings-ledger.md](../../research-notes/F-effects/findings-ledger.md),
  which records the evidence and how it was checked. Open questions have `H0xx` IDs
  (see [open-questions.md](../open-questions.md#effects)).
- **"Bit-exact"** always means **bit-exact to the 1.60 routine run in a single-function
  emulator**. Nothing here was measured on a physical SP-16.

## Status

"Reconstructed" means all of the following: signal flow, every parameter's
normalised-value → internal-value formula, object layout, 1.60 addresses, lifecycle,
and a Python model that is bit-exact to the emulated routine. Each page still lists
what is unknown.

### Effects

Index = position in the processor's effect array (Insert array / Master and Send
array). The Master and Send processors build the same ten classes in the same order
(F019, F173).

| Effect | Class (RTTI) | Insert | Master / Send | Status | Findings | Page |
|---|---|---|---|---|---|---|
| Chorus | `Chorus` + kernel `c_chorus` | 0 | 2 | **Reconstructed** | F054, F057–F062 | [chorus.md](chorus.md) |
| Flanger | `Flanger` + kernel `c_flanger` | 1 | 3 | **Reconstructed** | F054, F063–F068 | [flanger.md](flanger.md) |
| 2-band EQ | `ParametricEqualizer` | 2 | 4 | **Reconstructed** | F038–F044, F150, F153 | [parametric-eq.md](parametric-eq.md) |
| Multi-mode filter | `MultiModeFilter` | 3 | 5 | **Reconstructed** | F032–F037, F150, F175 | [multimode-filter.md](multimode-filter.md) |
| Delay (Insert) | `InsertFxDelay` | 4 | — | **Reconstructed** | F075–F079 | [insert-delay.md](insert-delay.md) |
| Delay (Master, Send) | `SendFxDelay` | — | 0 | **Reconstructed**; a different algorithm from the Insert delay | F080, F115–F120 | [send-delay.md](send-delay.md) |
| Reverb | `SendFxReverb` (`Reverb9NXSBase`) | — | 1 | **Reconstructed**; an own design, not JUCE's Freeverb | F121–F127 | [send-reverb.md](send-reverb.md) |
| LoFi | `LoFi` | 5 | 6 | **Reconstructed** | F026–F031, F150, F152 | [lofi.md](lofi.md) |
| Distortion | `Distortion` + kernel `c_distortion` | 6 | 8 | **Reconstructed** | F069–F074 | [distortion.md](distortion.md) |
| Compressor | `InsertFxCompressor` / `SendFxCompressor` (core `FxCompressor`) | 7 | 7 | **Reconstructed**; the Master/Send one adds a 2 ms look-ahead | F081–F087 | [compressor.md](compressor.md) |
| Phaser | `Phaser` | 8 | 9 | **Reconstructed** | F045–F050 | [phaser.md](phaser.md) |
| Ducker | `Ducker` | 9 | — | **Reconstructed** at slot 25 and through the trigger host; it has no audio key: the sequencer's note triggers drive it | F088–F094, F192–F201 | [ducker.md](ducker.md) |
| Shared oscillator | (no vtable) | — | — | **Reconstructed** | F051–F055 | [oscillator.md](oscillator.md) |
| Performance-FX LoFi | `PerformanceFxLoFi` | — | — | **Never constructed in 1.60.** The class and its algorithm exist (modelled, bit-exact), but nothing builds it, so it never runs on the device | F128–F130 | [lofi.md](lofi.md#performance-fx-lofi-never-constructed) |
| Limiter, Ring mod, Tremolo, Auto pan, Auto wah, Vinyl brake, Trans, Roll | — | — | — | **No DSP class.** These names are items in the FX select popup, but no effect class exists for them. Whether the popup shows them is open (H066) | F131 | — |

All twelve effect algorithms above (thirteen models, counting the two compressor
contexts) were also run **end to end through the real shared wrapper (slot 18)**,
bit-exact (F149, F151). The Master and Send processors were driven with all ten types
(F154).

### Shared infrastructure and mixer stages

| Stage | Main classes | Status | Findings | Page |
|---|---|---|---|---|
| Whole signal flow | — | **Mapped end to end** | F095–F114, F187–F191, F209–F213 | [signal-flow.md](signal-flow.md) |
| EffectBase interface | `EffectBase` (32-slot vtable) | **Reconstructed**: slot roles, object layout, no factory | F138–F143 | [effectbase.md](effectbase.md) |
| Slot-18 wrapper (activation gate, dry/wet, post-stage HPF, skip/clamp, type switch) | `EffectBase`, `EffectInOutGain` | **Reconstructed**, model bit-exact | F144–F149 | [effectbase.md](effectbase.md) |
| Slot-27 resets | per effect | **Reconstructed** | F150 | each effect page |
| Insert, Master, Send FX processors (type switch, bypass, disable, tempo feed) | `InsertFxProcessor`, `MasterFxProcessor`, `SendFxProcessor` | **Reconstructed**, model bit-exact | F016–F019, F154–F158, F176–F182 | [fx-processors.md](fx-processors.md) |
| Track mixing (insert position, pan, mute, send tap, fader, bus sums) | `TrackUnit`, `MultiTrackUnit` | **Reconstructed** for normal audio; denormal parity through the real output selectors is open (H053) | F095–F101 | [signal-flow.md](signal-flow.md#track-strip) |
| Analog-filter (DSF) send/return loop | `TrackUnit` routing mode, `DaveSmithManager` | **Reconstructed** on the digital side; run-time reachability of the loop modes is *likely*, not proven (H093, H094) | F187–F191 | [signal-flow.md](signal-flow.md#analog-filter-loop) |
| Send bus, return fader, master bus, master fader | `CompositeFxUnit`, `SendFxUnit`, `MasterOutUnit` | **Reconstructed**, model bit-exact | F102–F108 | [signal-flow.md](signal-flow.md#send-bus-and-master-bus) |
| Device output stage | `AudioDeviceOutputUnit` | **Reconstructed**, model bit-exact | F109–F114 | [signal-flow.md](signal-flow.md#device-output-stage) |
| Main-output selector and headphone router | `Output12Router`, `HeadphoneRouter`, `HeadphoneUnit` | **Reconstructed**, model bit-exact given the monitor inputs | F209–F213 | [signal-flow.md](signal-flow.md#main-output-and-headphones) |
| Parameter plumbing (FxParamIndex → slot 14, enum converters, `prj::EffectData` defaults, what the UI can reach, SYNC conversion, UI step law) | parameter managers, view controllers | **Reconstructed** for the paths listed; LFO modulation and step locks not done (H068, H003/H070) | F159–F172, F183–F186 | [parameters.md](parameters.md) |
| Numerics (soft-float ABI, FPSCR, libm, denormals) | — | **Settled** for the modelled routines | F021, F202–F208 | [numerics.md](numerics.md) |
| Live input, THRU monitoring, ALSA copy stage, codecs | `DeviceInputUnit`, `MultiTrackUnit` input units, ALSA thread | **Not reconstructed** (out of scope) | — | H015, H017, H054, H059 |
| Analog filter itself | — | **Out of scope**: analog hardware, controlled not computed | — | H008 |

## How effects work in the 1.60 app (overview)

- **Where the DSP runs.** All effects and mixing are ordinary ARM code inside
  `EP085_Main_R`, on the i.MX6 CPU, inside the JUCE ALSA device callback. The
  application has no FX offload device (F010, F013, F015; checked for the application
  binary only, H017). Everything is 32-bit float; conversion to integer happens after
  the graph, in the ALSA path (F014; that conversion itself was not checked, H015).
- **Block size and rate.** The app requests 44,100 Hz and 64-frame buffers (F014).
  Every FX processor calls its effect once per block with a hard-coded count of 64
  (F010, F154). That one ALSA period is one 64-frame callback is *likely* (H016).
- **One object per type.** Each FX processor builds one object of every effect type in
  its constructor and selects by array index. There is no factory and no registry: an
  effect type is compiled into at least five places per processor and parameter
  manager (F016, F141, F143).
- **Type switching is sequential, not a crossfade.** The old effect fades to dry over
  147 samples at 44.1 kHz (160 at 48 kHz). At the first block where it reports
  finished, the processor swaps in the new effect and activates it (F149, F154).
- **Shared wrapper.** Every effect's audio routine (vtable slot 25) is called only from
  the shared slot-18 wrapper, which adds the activation gate, the input fade and the
  dry/wet mix, plus a 10 Hz high-pass post-stage for six of the effects (Chorus,
  Flanger, multi-mode filter, LoFi, Distortion, Phaser; F139, F141, F144–F149).
- **Two inserts per track.** In 1.60 every track type has two insert slots, FX1 and
  FX2, in series (F132–F136).
- **Tempo feed.** Before every block the processors send the current tempo (clamped to
  1…999 BPM) as parameter 7 to the tempo-synced effects: Insert Chorus, Flanger, Delay,
  Phaser and Ducker (F017); Master/Send Delay, Chorus, Flanger and Phaser (F156).

The details are on the infrastructure pages: [effectbase.md](effectbase.md),
[fx-processors.md](fx-processors.md), [parameters.md](parameters.md) and
[numerics.md](numerics.md).

## How an effect type is selected

Each FX processor builds **one object of every effect type** in its constructor and
keeps them in a list owned by `FxProcessorBase` (data `+0x80`, count `+0x88`) (F016).
Nothing is constructed later: there is no factory, and switching type changes an index
(F141).

- `InsertFxProcessor` (ctor `0x118b0c`): current index at `+0xa4`, pending at `+0xa8`,
  both −1 (no effect) after construction (F017). Master and Send use `+0xa0` / `+0xa4`
  (F019, F154).
- `setFxType` is processor vtable slot 47 (Insert `0x11735c`, Master `0x1132e4`, Send
  `0x11a254`). It sets the pending index and starts the old effect's fade-out (slot 6).
  `processBlock` swaps pending into current at the first block where the old effect
  reports (slot 9) that it has finished, then activates the new one. The change is
  **sequential**: fade to dry over 147 samples, swap, fade in; it is not an overlapping
  crossfade (F149, F154).
- The parameter manager translates a stored **effect ID** into an array index:
  Insert table at `0x843d98`, Master/Send tables at `0x8436e0` / `0x8445c8` (F018,
  F019). Array order is **not** effect-ID order.

| Index | Insert effect (effect ID) | Master and Send effect |
|---|---|---|
| 0 | Chorus (4) | Delay (`SendFxDelay`) |
| 1 | Flanger (6) | Reverb (`SendFxReverb`) |
| 2 | 2-band EQ (8) | Chorus |
| 3 | Multi-mode filter (10) | Flanger |
| 4 | Delay (1) | 2-band EQ |
| 5 | LoFi (14) | Multi-mode filter |
| 6 | Distortion (12) | LoFi |
| 7 | Compressor (16) | Compressor (`SendFxCompressor`) |
| 8 | Phaser (18) | Distortion |
| 9 | Ducker (20) | Phaser |
| −1 | Off (any other ID) | Off |

The Master processor's "Delay", "Reverb" and "Compressor" run the `SendFx*` classes
(F019). The Send FX can be Off or any of the same ten types; Send and Master type
selection are identical (F173). The names in the table are the type-name strings
written into `prj::EffectData` (F018). The on-screen labels were not checked (H019).

## The EffectBase interface

Every effect derives from `EffectBase` (vtable `0x841fb8`, 32 slots). All 15 concrete
effects share one vtable layout with a fixed override pattern (F009, F138). These are
the slots that matter for reimplementing an effect (F139):

| Slot (byte offset) | Role | Evidence |
|---|---|---|
| 5, 6, 7, 8, 9 | Activation and fade control through the `EffectInOutGain` gate at `[e+0xc8]`: slot 5 activates (and calls slot 27), slot 6 starts the fade-out, slot 9 reports whether the gate is still active | F022, F144, F145, F149 |
| 10 | Retrigger (Chorus, Distortion, Flanger, Phaser) | F046, F138 |
| 14 (`+0x38`) | `setParameter(index, value)`, shared `0x105d24` (overridden by Chorus, Distortion, Flanger). The value is a float in a **core register** (soft-float calling convention) | F011, F021, F025, F138 |
| 18 (`+0x48`) | Shared wrapper `0x106de4`, never overridden; the only caller of slot 25 | F009, F139 |
| 23–26 | Pure virtual in the base; overridden by all 15 concrete effects (with 0, 1 and 27) | F009, F138 |
| 25 (`+0x64`) | **Per-effect audio entry** `int process(this, float* L, float* R, int n)`, n ≤ 64 | F010 |
| 26 | Updates the dry/wet pair: wet at `+0x14`, dry at `+0x10` | F149 (per-effect laws) |
| 27 | Reset; called on every activation | F150 |

What slot 18 does around every effect (these stages are **not** inside the per-effect
models; `tools/fx/effectbase.py` models them, F149):

1. **Activation.** Until the effect's in/out gate has been started, slot 18 returns with
   the buffers untouched. Gains ramp linearly over 147 samples at 44.1 kHz (160 at
   48 kHz) (F144, F149).
2. **Skip and clamp** (`+0xa8…+0xb8`): a 147/160-sample dry skip after activation and a
   stop clamp. Only the Insert compressor uses it, because its constructor leaves the
   flag set (F148, H074).
3. **Dry copy, input fade and slot 25.** The input is copied, faded in on activation
   (`0x1074c4`), and slot 25 runs on the copy (F146).
4. **Post-stage `0x106c88`**: SignalGate → first-order high-pass → SignalGate, set to
   10 Hz by the processors (F147). The processors switch it on only for Chorus,
   Flanger, the multi-mode filter, LoFi, Distortion and Phaser; never for the 2-band
   EQ, the delays, the compressors, the Ducker or the Reverb (F141).
5. **Dry/wet mix `0x10770c`**: L = L·dry + copy·wet, with the gate's ramps (F146).

Two rules apply to every effect built on the shared parameter objects:

- **Change detection.** A new value is applied only if it differs from the parameter's
  last value. Each constructor sets a "last" value (often 0.5). Setting exactly that
  value before the first block does nothing (F026).
- **Normalised values.** Continuous parameters arrive as 0…1. Choice parameters arrive
  as a float that is truncated to an integer (F026). The exceptions are the tempo
  parameters, which receive the BPM value itself (F045).

## Shared building blocks

| Block | 1.60 address | Used by | Notes |
|---|---|---|---|
| `LinearParameter` / `ToggleParameter` | vtables `0x840ac8` / `0x840b20` | all | 0x5c-byte parameter objects; change detection `0xf0ffc` (F026, F045) |
| `SignalGate` | vtable `0x840e40`, ctor `0xf4e5c` | LoFi, MMF, PEQ, post-stage | linear fade, 132 samples (3 ms) in these effects (F029, F147) |
| `IirFilter` → `IirLpf/Hpf/Bpf2ndOrder`, `IirOff` | process `0xe16dc` | LoFi, MMF, PEQ | bilinear biquads, direct form I, NEON with L/R in two lanes (F027, F028) |
| `IirFilter2` → `LowShelvingFilter`, `PeakingFilter` | vtable `0x83bc60` | PEQ | Zölzer boost forms (F040) |
| GainRamp (no RTTI name) | `0xe8900` / `0xe895c` / `0xe89f0` | MMF, PEQ, mixer | linear gain ramp over N samples (F033, F035, F096) |
| `MuteSmoother` | ctor `0xe7fd8` | processors, mixer, outputs | linear mute ramp (F154) |
| Oscillator (no vtable) | ctor `0x100af0`, process `0x101bdc` | Phaser, Chorus, Flanger; also `LfoProcessor` | seven waveforms (F051–F054) |

The Phaser does **not** use the RTTI `LFO` class (F007, F047). The delay, reverb,
compressor and ducker blocks are described on their own pages.

## How the effects were validated

The algorithms were found by static analysis (RTTI recovery, disassembly, decompilation),
and each result was read again by a separate review pass. Every claim was then tested
by **single-function emulation**: the real 1.60 machine code, run one routine at a time
in the unicorn emulator (F020).

- **Loader.** The main executable's two load segments are mapped from the file at their
  1.60 addresses. The device's own 1.60 `libm.so.6` and `libgcc_s.so.1` are mapped and
  relocated. Every other import is either served by a listed stub (allocation,
  `memcpy`/`memmove`/`memset`, static-init helpers) or traps by name, so nothing
  unexpected runs silently.
- **Construction.** Each effect, processor or mixer unit is built with its real
  constructor after the static initialisers it depends on, with the arguments the
  firmware passes (F056, F141, F154).
- **Comparison.** Parameters are set through the real setters. The real routine and the
  Python model run on the same input (impulses, silence, sines, seeded noise, steps,
  denormals, extreme values), and the outputs are compared as raw float32 bits. Stored
  coefficients and object fields are compared with the model's state.
- **Review.** A second, independent pass re-ran every comparison and reproduced the
  recorded output hashes. It added its own cases (random parameter walks, odd block
  sizes, mid-run changes, out-of-range values) and planted deliberate errors in each
  model, to show that the comparison catches them.
- **Determinism.** Runs are bit-identical across independent emulator instances,
  processes and host machines, and do not depend on heap or stack fill (F020). An
  independent review re-ran a sample of the verifiers on a different operating system
  and CPU and reproduced their recorded hashes.

What this **shows**: for the tested settings and signals, the documented formulas and
the models reproduce exactly what the original 1.60 routines compute, given the same
object state. It also confirms the object layouts that the code reads and writes.

What it does **not** show:

- **Behaviour on a physical SP-16.** Nothing was measured on hardware. Every
  "bit-exact" result compares an own-code model with emulated 1.60 functions inside
  stubbed surroundings.
- **Everything around the emulated routines.** Threading, the ALSA copy stage, the
  codecs and the analog stages were not emulated (H015, H017).
- **Inputs nobody tested.** Settings and signals outside the tested sets are covered
  only by the reasoning on each page.
- **Fresh-heap contents on the device.** A few routines read memory their constructor
  never wrote (oscillator quirks, F051, H036).

What earlier versions of these pages listed as open and is now settled:

- **Floating-point mode.** The device runs every audio thread with FPSCR flush-to-zero
  **off**, default-NaN off and round-to-nearest, the same as the emulator (F202–F205).
  The NEON vector helpers flush denormals in hardware anyway; the models follow both
  behaviours.
- **Host maths library.** The models no longer call the host's `tan`, `pow`, `exp` or
  `log10f`. They use own correctly rounded routines (`crmath.py`) and fdlibm-derived
  `log10f`, which equal the emulated 1.60 libm on every tested argument (F206–F208).
- **Master and Send contexts.** Both processors were driven with all ten types,
  bit-exact (F154–F156).
- **Resets.** The slot-27 resets of LoFi, MMF and PEQ are modelled (F150).

Emulator caveats (F020): library pages are mapped read-write-execute; a NULL pointer
plus an offset ≥ `0x8000` lands in mapped code instead of faulting. On one macOS host,
unicorn could not start inside a restricted sandbox, because its start-up cache-size
query raised an illegal-instruction fault; a small shim emulated that single host
instruction. Results were identical with other shim values and on Linux without it.

## Known gaps for reimplementers

The research stopped at a fixed scope ("reconstruct the 1.60 FX DSP algorithms"). These
are the items a faithful reimplementation of the instrument would still need, most
important first. Each one has a suggested next test in
[open-questions.md → Effects](../open-questions.md#effects).

1. **LFO → FX parameter modulation (H068).** The track LFO can address FX parameters
   (destination ids 100–155 for FX1 and 200–255 for FX2, F135). How the modulation is
   applied to an effect parameter was not traced.
2. **Per-step FX parameter locks (H003, H070).** The sequencer can lock FX parameters per
   step. The 1.60 lock reader has a *likely* lead (F159), but the lock path was outside
   the milestone.
3. **Which FX the popup actually offers, with names and order (H066, H019).** The popup
   string list has 20 items, eight of them without a DSP class (F131). What each context
   shows, and the on-screen names, were not checked.
4. **Denormal parity through the real output selectors (H053).** The track-mix model is
   bit-exact on normal audio; with denormal input, 24,797 samples differ through the real
   selectors (F101). This matters only for bit-exact tails.
5. **Phaser retrigger on sequencer start (H032)** and **Insert Delay warm-up silence on the
   device (H045).** Both behaviours are modelled; when the device triggers them is open.
6. **Compressor look-ahead reachability (H088, H090).** The Insert compressor's
   look-ahead has no UI writer; whether project load or reload can set it is open (F167,
   F169).
7. **Analog-filter loop modes at run time (H093, H094).** The digital side is modelled;
   whether the filter on/off setters and the return gate are reached at run time is open
   (F188, F189).
8. **The ALSA copy stage from graph channels to the three DACs (H015).** Needed only for a
   complete input/output map.

## Using and citing

- Docs and the symbol table are CC BY 4.0. The models in [tools/fx/](../../tools/fx/)
  are MIT, except for the third-party notices kept in some files and one file under
  a different licence: `tools/fx/glibc_expf.py` is LGPL-2.1-or-later
  ([LICENSE-LGPL-2.1](../../LICENSE-LGPL-2.1)). See
  [NOTICE.md](../../NOTICE.md). Cite as *SP-16 firmware research,
  `docs/effects/<page>`, finding F0xx, firmware 1.60 (`EP085_Main_R` SHA-256
  `3d1392a6…5464`)*.
- Function addresses with confidence levels:
  [symbols/fx-functions-1.60.csv](../../symbols/fx-functions-1.60.csv).

## Continuing the work

The method that worked for every reconstructed stage, in order:

1. Build the object with its real constructor in a single-function emulator. Log which
   parameters it registers (name, index, object offset, "last" value).
2. Read the audio routine and its callees in a disassembler. Write down the per-sample
   signal flow with an address for each stage.
3. Set each parameter through its real setter at several values (0, 0.1, 0.3, 0.5, 0.7,
   0.9, 1). Read the stored coefficients back and fit closed-form formulas. Keep a
   formula *likely* until it matches bit for bit.
4. Write a pure-Python model and compare it with the real routine sample by sample on
   impulses, sine and noise, including mid-run parameter changes. Then try to break it:
   random walks, odd block sizes, edge values, and deliberate model errors.
5. Test at least one alternative explanation and record what was refuted.

The research process itself (two separate passes, a worker and a reviewer, with written
success criteria) is described in
[research-notes/methods/worker-critic-research-loop.md](../../research-notes/methods/worker-critic-research-loop.md).
Keep every claim bound to the 1.60 addresses. Keep the confirmed/likely/guess labels. Do
not commit firmware bytes, tables copied from firmware data, or disassembly listings (see
[CONTRIBUTING.md](../../CONTRIBUTING.md)).
