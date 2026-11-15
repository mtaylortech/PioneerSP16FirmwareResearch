# Open questions and next steps

Where the research stopped, and the smallest useful next step for each thread.
Nothing here is an instruction to act on a physical device; see
[DISCLAIMER.md](../DISCLAIMER.md).

## For a successor picking this up

The highest-value, lowest-risk continuations that need **no hardware**:

1. **Finish the cross-version function diff.** The 1.30→1.31 pilot (two reader
   candidates) is the seed. Extend it to a real version-to-version diff of
   `EP085_Main_R` using the Ghidra scripts in `tools/firmware/ghidra/` and your
   own extracted binaries. Bind every finding to a version + address.
2. **Map the updater's full acceptance checks.** The decode path and the
   marker+CRC32 are known; the complete set of checks the on-device `update`
   program applies (before any repack could be trusted) is not. Static only.
3. **Compare shipped kernels against the GPL source.** Confirm whether the held
   initramfs/config actually reproduces each release's `uImage`. This underpins
   any boot/recovery claim and is currently assumed, not shown.
4. **Push the board emulator further.** [`emulation/board/`](../emulation/board/)
   reproduces boot to application launch. The next questions are concrete:
   supply a fake AK4458 device or ALSA null configuration to see whether the
   SIGSEGV goes away, and model enough of the missing MTD/NAND to get past the
   recovery check. This is all software; no hardware is involved.
5. **Finish the effects around the DSP.** Every live 1.60 effect and the whole mixer
   are reconstructed, with a repeatable recipe
   ([effects/README.md](effects/README.md#continuing-the-work)). What is left is how the
   sequencer and the UI drive them: LFO modulation, per-step FX locks and the FX popup
   contents come first; see [Effects](#effects). Needs your own 1.60 binary and a
   single-function emulator, no hardware.
6. **Improve the symbol set.** `symbols/` covers 1.60 startup + Mixer/Send. Label
   more of the audio/MIDI/UI graph; correct inferred names/types as you verify
   them. Keep `symbols/labels-1.60.json` as the source of truth.

## Thread-by-thread open questions

| Thread | Open question | Status |
|---|---|---|
| Decoder key | Does the one key work beyond 1.50/1.60, and across hardware revisions? | Unknown. Same key decoded all six held releases; universality not shown. |
| Updater | Which checks govern full update acceptance/authenticity? | Unknown — needed before any repacker could be considered. |
| Repack | Can an unchanged image be repacked into an accepted update? | Not attempted. Container metadata fidelity (modes/owners) is a prerequisite. |
| Boot/recovery | Does A/B kernel selection give usable rollback? | Declared in `fw_env.txt`; never tested. |
| Components | What exactly do MAIN / apl / SUB1 / SUB2 update? | Unknown — needed for safe component routing. |
| Panel MCUs | Protocol/role of `PANELCOM1/2.mot`? | Not analysed (S-record files preserved by reference only). |
| Subsystems | How do audio/MIDI/UI/panel communicate and meet timing? | Unknown; only library/module inventory established. |
| Normalize | Legal all-owner sample reload in firmware (producer/lifetime protocol)? | Blocked; empty roster observed; host tool works, integration does not. |
| Startup | How much parent-init work remains before a natural drawable display? | Partial in emulator; no persistent causal wait established. |
| Effects | LFO → FX modulation, per-step FX locks, which FX the popup offers; a few edge behaviours on the device. | DSP done: every live effect, the wrapper, the processors, mixer, buses, output stage and headphones reconstructed (emulator-validated). Open items in [Effects](#effects). |
| Storage | Live NAND environment; eMMC boot-area contents; whether real units pass the first-boot format check; on-unit confirmation of the predicted boot sector and resume behaviour. Parked: `resumeProject` caller, `ProjectManager` ops +0x58/+0x60 and check `0x3391a0`, ten listing callers, the `.wav.dat` append case. | Open. Static/emulated picture in [storage.md](storage.md); NAND env needs a receive-only serial console; the rest needs a unit session. |

## Effects

Where the 1.60 effects work stopped. Every live effect, the shared `EffectBase` wrapper,
the FX processors and the whole mixer and output path are reconstructed, with
bit-exact models (status table in [effects/README.md](effects/README.md#status)). What
is left is mostly **around** the DSP: how the sequencer and the UI drive it. The evidence
is in the [findings ledger](../research-notes/F-effects/findings-ledger.md).

Each item below is an open hypothesis with its ID, its current label, and the test that
would settle it. All addresses are 1.60 unless marked **[1.50]**. "Emulator" means the
single-function method in
[effects/README.md](effects/README.md#how-the-effects-were-validated): it needs your own
1.60 `EP085_Main_R`, `libm.so.6` and `libgcc_s.so.1`. "Static" means a disassembler is
enough. The reference scripts in [tools/fx/verify/](../tools/fx/verify/README.md) show how
each earlier question was tested.

### What a reimplementer would miss first

These were put aside when the research was frozen at "reconstruct the 1.60 FX DSP
algorithms". An independent review named them as the gaps that matter most for a
faithful instrument. Most useful first.

1. **H068 — LFO → FX parameter modulation** (*likely*). Each track's LFO can target an
   effect parameter. The parameter manager has a destination field (`+0x5c`, written by
   manager slot 13), and destination ids 100–155 address FX1 and 200–255 address FX2
   through the manager's slot-57/58 tables (F135). How the LFO value is turned into a
   change of the effect parameter (added to the knob value? scaled? per block?) was not
   traced. **Next test (static, then emulator):** find every caller of manager vtable
   offset `+0x34` (slot 13) on Insert managers, starting from `LfoProcessor`
   (`0x135da0`) and `TrackUnit` slot 79. Then emulate manager slot 10 on the FX1 and the
   FX2 manager with ids 1xx and 2xx and record which effect parameter (slot 14 index) and
   which value arrives.
2. **H003 / H070 — Per-step FX parameter locks** (out of scope; a lead is *likely*). The
   sequencer can store an FX parameter value per step. In **[1.50]** the lock machinery
   is known (table `0x8a8fa0`, writers `0x34f314` / `0x34f3f0`, reader `0x350d98`; R002,
   R003). In 1.60, `0x351c70` / `0x3535dc` have the same 49-case set and read step words
   through the int8 table `0x8ab198`, which equals the manager's sub-slot table on all 55
   valid rows (F159). Whether the second FX unit in the step data drives FX2 locks is a
   *guess* (H070). **Next test (static):** confirm that `0x351c70` / `0x3535dc` are the
   1.60 counterparts of the [1.50] reader (addresses-only masked match), then follow the
   value they read to the parameter manager (slot 6, `vt+0x18`) and check the unit-1 path
   against FX2.
3. **H066 / H019 — Which effects the FX popup offers, under which names and in which
   order** (deferred). The popup's string list has 20 items, eight of them with no DSP
   class: Ring mod, Tremolo, Auto pan, Auto wah, Limiter, Vinyl brake, Trans, Roll (F131).
   **Already answered (F171):** the popup's handlers map to Off, Chorus, Flanger, Phaser,
   Distortion, LoFi, Delay, Reverb (Send/Master only), 2-band EQ, Filter, Compressor and
   Ducker; the other handlers call no type setter, so those items cannot select an
   effect. Which handler belongs to which visible item is *likely* only (by list order).
   **Still open:** whether the eight items without a class are shown at all, per context
   (Insert / Master / Send), and the exact on-screen labels and order. **Next test
   (static):** decompile the item-enable and item → effect-ID code in `0x3bec88` and
   `0x3c237c` (`FxSelectPopupWidgetController`) for each context, and tie each handler to
   its list row.
4. **H053 — Denormal parity through the real output selectors** (*likely*). The
   track-mix model is bit-exact on normal audio, but with denormal input 24,797 samples
   differ when the real `OutputSelector` code runs (F101). The device runs with
   flush-to-zero off (F202–F205), so denormals do occur. This matters only for bit-exact
   tails, not audibly. **Next test (emulator):** use the real `0xe6b8c` in the track-mix
   comparison instead of stand-ins, add its four ×1.0 NEON copy passes (which flush
   denormals) to `track_mix.py`, and re-run denormal and noise input in routing modes
   0, 1 and 2.
5. **H032 — Phaser retrigger on sequencer start** (*guess*). The Phaser restarts its
   oscillator at the peak when slot 10 is called (modelled, F046). Who calls it on the
   device (sequencer start, pattern restart?) is not known. **Next test (static):** find
   the callers of `EffectBase` slot 10 (virtual call `[vt+0x28]` on effect objects) from
   the processors, the parameter managers and the sequencer transport listeners.
6. **H045 — Insert Delay warm-up silence** (*guess*). After start-up or a reset, an echo
   source in the first D samples is muted and never re-enters through the feedback
   (modelled, F079; see [insert-delay.md](effects/insert-delay.md)). Whether this is
   audible depends on when the device activates or resets the effect. **Next test
   (static):** list the callers of slots 5 and 27 on the device (pattern start, FX type
   change, project load) from the processor and manager code.
7. **H088 / H090 — Can the compressor's look-ahead be switched on?** (*guess* /
   *likely*). The Insert compressor's LookAhead (slot-14 index 6) has no UI writer and
   the Insert reload sends no index 6 (F166, F169), so it is *likely* always off. On
   Send/Master, a SYNC byte left over from a time effect can become LookAhead at the next
   reload (F167). Which code calls that reload (manager slot 51, not in the UI interface)
   is open. **Next test (static):** list the virtual calls at primary-vtable `+0xcc` on
   manager objects (`TrackUnit +0xe8[i]`, `MasterFxUnit +0x80`, `SendFxUnit +0x88`) and
   their callers; for H090, trace the project-load property binders (H087) for byte
   `+0x28` of an Insert compressor's `prj::EffectData`.
8. **H093 / H094 — Is the analog-filter loop reachable at run time?** (*likely*). The
   digital side of the analog-filter send/return loop is modelled (F187–F191, see
   [signal-flow.md](effects/signal-flow.md#analog-filter-loop)). Whether the filter on/off
   setters (`IDaveSmithManager` slots 3/4) are called from the panel, and whether the
   return gate (`AudioDeviceInputUnit` slot 45 `0x1ad4e4`) opens when the loop is active,
   is open. **Next test (static, then emulator):** sweep `.text` for virtual calls at
   `vt+0xc` / `vt+0x10` on `IDaveSmithManager` objects and decode `GpioCallback`
   `0xc4324`; find the `vt+0xb4` caller and emulate `0x1ad4e4` for its four argument
   combinations.
9. **H015 — The copy stage from graph channels to the three DACs** (out of scope). After
   each callback, the ALSA thread copies graph output channels into the buffers of
   `hw:ak4458audio,0` and `hw:ak4452audio,0/1`. Needed only for a complete
   input/output map. **Next test (static):** decode the `(source channel, destination
   channel, n)` arguments of the copy calls (`0x577d5c`) at each call site in
   `0x58e4c0–0x58e718`, and tie the device loop index in `open` (`0x590320`) to the PCM
   names.

### Other open edges of the effects and mixer

- **H036 — Fresh heap on the device** (*guess*). A few routines read object memory their
  constructor never writes (oscillator counters, F051; Flanger, F066). The models assume
  zero. **Next test (static):** identify the allocator used for the effect kernels and
  whether it returns zeroed memory.
- **H030 — PEQ start-up dip** (*guess*, partly answered). The activation fade reduces
  the first-block quirk of the 2-band EQ to a −3.7 dB, ≈3 ms dip at the first activation
  only (F153); band type 5 is unreachable from the UI (F171). **Next test (emulator):**
  none needed for the DSP; whether the dip is audible needs a unit.
- **H073 — Are the effects ever rebuilt?** (*likely* no). Effects are built once at
  application start (F141). **Next test (static):** census of calls to the graph build
  (`0x1bc8d4` via `+0xdc`, `0x1b6284`, `0x5712cc`) from project load and audio-device
  restart.
- **H085 / H087 — What a new or loaded project sets** (*likely* / *guess*). A new
  project *likely* starts every FX slot "Off" (F165). Which fields a saved project
  restores is a *guess*. **Next test (static, then emulator):** trace `ProjectManager`
  slot 4 `0x33dd78` and the `ProjectData` constructor `0x339448` for any default-project
  load; decode the six `prj::EffectData` property binders (vtables `0x8ae640…0x8ae708`).
- **H091 — The 17th "dummy" `EffectData`** (*guess*). A scene can be redirected to a
  dummy record (`0x186cc8`), so bypass and type would come from it while redirected.
  **Next test (static):** find the `vt+8` calls on `SceneSwitchable<EffectData>` objects.
- **H092 — SHIFT and encoder steps** (*likely*). One detent with SHIFT gives the fine
  step (F185). **Next test (emulator):** feed a synthetic panel record for SHIFT and a
  detent to `0x55767c` and trace the delta into `0x2c004c`.
- **H096–H099 — Ducker trigger edge cases** (*guess* / *likely*). The trigger rule is
  reconstructed (F192–F201, [ducker.md](effects/ducker.md)). Open: the realtime-hit
  dedupe while recording (H096), which thread pad and MIDI hits arrive on (H097), whether
  any audio-thread node erases a realtime dispatch unseen (H098), and whether SOURCE = 16
  is reachable (H099). **Next tests (static):** callers of the `triggerSound` entry
  points and their threads; owners of the `setRealTimeSequenceData` vtable words;
  classification of the remaining slot-14 call sites with index 10.
- **H060 — Volume sample offsets across blocks** (*guess*). If any writer mixes the
  offset and plain setters on one volume object, the mixer models must keep the offset
  across blocks (F110). **Next test (static):** list slot-2/slot-3 calls on fader, pan
  and send objects.
- **H104–H106 — Headphone sources** (*guess* / *likely*). What the headphone input pair
  2/3 carries in normal use (H104), what the three monitor pairs are (H105), and whether
  the audio input's left channel leaks into a cue pair through a graph fan-in (H106).
  **Next tests:** trace the writer of `DeviceInputUnit +0xa0`; decompile
  `RecMonitorUnit` `0x1ac134`; decode the JUCE graph's fan-in handling for that node.
- **H095 — Line-input polarity** (*likely* inverted). **Next test (emulator):** DC per
  channel through `0x1ad590`.
- **H078, H100 — Sample-rate change while running** (*guess* / *likely*). `EffectBase`
  slot 3 `0x105f2c`: does it leave the wrapper as a fresh activation would (H078), and
  does it overwrite a saved register for the 11-parameter Ducker (H100)? **Next test
  (emulator):** run slot 3 from 44.1 to 48 kHz mid-run on a stub and on a Ducker.
- **H103 — A further `IirFilter2` subclass** (*guess*). `0xe2680` is *likely* the
  coefficient routine of a filter no modelled effect uses. **Next test (static):** resolve
  the vtable that holds `0x83bcb4` via RTTI.
- **H084 — Reload and lock races** (*guess*). **Next test (emulator):** the Insert
  manager reload with `+0x30 ≠ 0`; the FxParamIndex values the callers of manager slot 6
  can pass.

### Model and harness housekeeping

Small, known improvements; none changes a documented result.

- **H048:** IEEE division for the compressor's out-of-range ratio index 0 (removes the
  only known model crash).
- **H067:** saturating conversion for infinite or NaN input in the LoFi and
  Performance-FX LoFi crushers.
- **H102:** full-range argument reduction in `fdlibm_tanf.py` (the Phaser model fails at
  22.05 kHz; the device runs 44.1 kHz).
- **H081:** the Insert Ducker feed in the full Insert processor model.
- **H071:** confirm that the disabled inserts on MIDI tracks cost no DSP work.
- **H072, H101:** harden two static verifiers (`H006_fx2_routing.py`,
  `H038_fpscr_census.py`).
- **H024:** list every owner of the shared LoFi building blocks (partly done: F037,
  F040, F047).

### Outside the DSP scope

- **H008:** the analog filter is analog hardware, controlled, not computed.
- **H016, H017:** that one ALSA period is one 64-frame callback; that the codec drivers
  only move PCM. Low priority.
- **H054, H059:** the audio-input / THRU path and the input gain.
- **H058:** which panel pot drives `OutputVolumeController` (F113).
- **H061:** the renderer-mode state machine around the bulk mute (F112).
- **H069:** what the "master tempo" quality switch changes (F137).

### Answered since the first version of this list

One line per item; the page has the detail.

| ID | Question | Answered in |
|---|---|---|
| H033, H034 | Chorus, Flanger algorithms | [chorus.md](effects/chorus.md), [flanger.md](effects/flanger.md) (F057–F068) |
| H035 | Distortion | [distortion.md](effects/distortion.md) (F069–F074); H042 knob roles confirmed (F170) |
| H039, H043 | Insert Delay; Send/Master Delay | [insert-delay.md](effects/insert-delay.md), [send-delay.md](effects/send-delay.md) (F075–F080, F115–F120) |
| H005 | Reverb (refuted as "JUCE Freeverb"; an own design) | [send-reverb.md](effects/send-reverb.md) (F121–F127) |
| H040, H041 | Compressor; Ducker | [compressor.md](effects/compressor.md), [ducker.md](effects/ducker.md) (F081–F094) |
| H049, H050 | Ducker trigger senders and host rule | [ducker.md](effects/ducker.md) (F192–F201) |
| H064 | Performance FX | [lofi.md](effects/lofi.md#performance-fx-lofi-never-constructed): never constructed (F128–F130) |
| H011, H044, H074 | EffectBase interface, slot-18 wrapper, Insert compressor start delay | [effectbase.md](effects/effectbase.md) (F138–F149) |
| H022, H014, H018 | Activation fade, dry/wet law, post-stage high-pass | [effectbase.md](effects/effectbase.md) (F144–F149) |
| H025, H076 | Slot-27 resets | each effect page (F150) |
| H012, H037, H056, H077 | Type switching; Master and Send processors | [fx-processors.md](effects/fx-processors.md) (F154–F158) |
| H079, H080 | FX ON/OFF start mode (dormant); Insert bypass sources | [fx-processors.md](effects/fx-processors.md), [parameters.md](effects/parameters.md) (F176–F182) |
| H020, H027 | Send FX types; Master/Send multi-mode filter | [fx-processors.md](effects/fx-processors.md), [multimode-filter.md](effects/multimode-filter.md) (F173–F175) |
| H004, H083, H086, H082 | FxParamIndex → slot 14; enums and `prj::EffectData` defaults; UI reach; SYNC, step law | [parameters.md](effects/parameters.md) (F159–F172, F183–F186) |
| H009, H010, H055, H052, H057 | Track mixing; send bus and master; device output; analog-filter loop; headphones | [signal-flow.md](effects/signal-flow.md) (F095–F114, F187–F191, F209–F213) |
| H006 | FX2 on Sample/Thru tracks (refuted as stated: FX2 is insert slot 1 on every track type) | [effects/README.md](effects/README.md#how-effects-work-in-the-160-app-overview) (F132–F137) |
| H038, H029 | FPSCR flush-to-zero; host-libm independence | [numerics.md](effects/numerics.md) (F202–F208) |

## Questions only the original researcher / owner can answer

These were open on the research side and are recorded here so a successor knows
they are gaps, not oversights:

- **Firmware provenance:** exact download URLs and any publisher-published hashes
  for the held `.UPD` files were never recorded. A successor should re-download
  from the official source and re-verify against
  [firmware-reference.md](firmware-reference.md).
- **Target hardware:** the owner's unit runs **OS 1.5**; much of the emulation
  work targeted **1.60**. Physical claims must be bound to the actually-installed
  release. Board revision is unknown.
- **No off-device backup of the raw research was verified.** Large evidence
  (disk images, captures, native Ghidra databases) is deliberately **not** in
  this repository (see CONTRIBUTING.md); it exists only in the original private
  research tree.

## Things deliberately left out of this release

- Decoded firmware trees, `.UPD` files, `EP085_Main_R`, `.mot` panel firmware.
- Ghidra native project databases (`.rep`/`.gbf`) — excluded; the portable
  labels + import script in `symbols/` replace them.
- Guest disk images and framebuffer captures of the running firmware.
- Bundled third-party tool builds (QEMU, glib, XQuartz, Python). The emulator
  *code* is published in `emulation/`; you build or install the tools yourself.
- The USB update / diagnostic-drawing emulator arm, whose update carrier was
  produced with the real firmware key.
- Internal coordination notes and historical session prompts.

If you need any of those to continue, you will need to reproduce them yourself
from firmware you obtain and tools you install.
