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
5. **Reconstruct another effect.** Four 1.60 effects and the shared oscillator are
   done, with a repeatable recipe ([effects/README.md](effects/README.md#continuing-the-work)).
   Chorus and Flanger are closest (their cores are confirmed); see [Effects](#effects).
   Needs your own 1.60 binary and a single-function emulator, no hardware.
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
| Effects | Chorus/Flanger/Distortion/Delay/Reverb/Compressor/Ducker algorithms; the effect-switch fade; mixer, send levels and Send FX types. | Open. LoFi, multi-mode filter, 2-band EQ, Phaser and the shared oscillator reconstructed (emulator-validated); see [Effects](#effects). |
| Storage | Live NAND environment; eMMC boot-area contents; whether real units pass the first-boot format check; on-unit confirmation of the predicted boot sector and resume behaviour. Parked: `resumeProject` caller, `ProjectManager` ops +0x58/+0x60 and check `0x3391a0`, ten listing callers, the `.wav.dat` append case. | Open. Static/emulated picture in [storage.md](storage.md); NAND env needs a receive-only serial console; the rest needs a unit session. |

## Effects

Where the 1.60 effects work stopped. The status of every effect is in the table in
[effects/README.md](effects/README.md#status); the evidence is in the
[findings ledger](../research-notes/F-effects/findings-ledger.md). Each item below is
an open hypothesis with its ID, its current label, and the test that would settle it.
All addresses are 1.60 unless marked **[1.50]**. "Emulator" means the single-function
method described in [effects/README.md](effects/README.md#how-the-effects-were-validated):
it needs your own 1.60 `EP085_Main_R`, `libm.so.6` and `libgcc_s.so.1`. "Static" means a
disassembler is enough.

### Effects not yet reconstructed

- **H033 — Chorus** (*likely*). It is one linear-interpolated delay tap per channel in
  a 4,474-sample ring. The delay is driven by the smoothed sine oscillator, and the
  output is muted until the ring is full (see
  [oscillator.md](effects/oscillator.md#chorus-and-flanger)). **Next test (emulator):**
  build Chorus with the inline construction range `0x118b50–0x118c64`. Sweep every
  parameter through slot 14 at ≥ 5 values and read back the kernel and oscillator
  fields. Derive the rate (tables `0x349778`/`0x349798`), Sync, depth, depth-scale and
  phase formulas. Then write an end-to-end model and compare it with slot 25
  (`0x115d70`) on impulse, sine and noise, including tempo changes.
- **H034 — Flanger** (*likely*). A 372-sample modulated delay with pre-gain feedback
  and a delay-dependent gain. **Next test (emulator):** as H033, including the
  feedback mapping from parameter 4 to kernel field `+0x10c`. Construction range
  `0x118cd8–0x118ddc`, slot 25 `0x115f58`.
- **H035 — Distortion** (*guess*). Read from decompiled code only: high-pass →
  low-pass → auto-gain envelope → drive → clip/soft-clip blend → ×0.7 → output
  low-pass, with no modulation. **Next test (emulator):** construction range
  `0x119060–0x1190ec`. No parameters are registered in that block, so first find
  where they are registered. Then sweep slot 14 (`0x1164d8`), read `0xfa78c`, and
  model it.
- **H005 — Reverb** (*guess*). The Master/Send reverb (`SendFxReverb` + `Reverb9NXSBase`)
  might wrap JUCE's Freeverb-style `juce::Reverb`. **Next test (static):** search code
  and read-only data for the Freeverb tunings (comb lengths 1116, 1188, 1277, 1356,
  1422, 1491, 1557, 1617; all-pass 556, 441, 341, 225; stereo spread 23). Follow any
  hits into `SendFxReverb` (slot 25 `0x111730`).
- **No hypothesis yet:** Delay (`InsertFxDelay` `0x103488`, `SendFxDelay` `0x1054ac`),
  Compressor (`FxCompressor` `0xf7584`), Ducker (`0xf61a0`) and the performance-FX
  LoFi (`0xfc434`). The LoFi recipe in
  [effects/README.md](effects/README.md#continuing-the-work) applies to each.

### The shared wrapper and effect switching

- **H022** (*guess*). The `EffectBase` post-stage (`0x106c88`), mix (`0x10770c`) and
  dry/wet pair are common to all Insert effects. If so, one model of slot 18 wraps
  every per-effect slot-25 model. **Next test (emulator):** run slot 18 with slot 25
  neutralised on LoFi and on one other effect. Fit the high-pass and the mix law.
- **H014** (*open*). `0xe8228` is the post-effect dry/wet or bypass mix that the
  processors apply after slot 18. `0x10770c`/`0x106c88` are the dispatcher's
  write-back. **Next test (emulator):** read `0xe8228` and run it on constant buffers
  with known mix values.
- **H018** (*guess*). Switching effect type is a crossfade. `setFxType` starts a
  fade-out on the old effect (slot 6), `processBlock` keeps running it while slot 9
  reports "still active", then swaps in the new one and fades it in (slots 5/7/8).
  Processor flags `+0x9d`/`+0x9e` gate this. **Next test (emulator):** call setFxType
  plus a few `processBlock`s on one effect, logging slot-9 returns and the output
  envelope. This gives the activation fade's shape and length.
- **H012** (*open*). Slot 18 is slot 25's only caller, and its skip/offset/clamp fields
  (`+0xa8…+0xb8`) implement sub-block alignment. **Next test (static, then
  emulator):** sweep the code for calls through `[vtable+0x64]` on effect objects,
  find the writers of `+0xb0`/`+0xb8`, then run `0x106de4` with those fields set.
- **H025** (*likely*). LoFi reset (slot 27 `0xfb5a4`) clears the filter taps and the
  held samples and sets the phase to the step. **Next test (emulator):** run slot 5 →
  slot 27 after processing, dump the state, and extend `tools/fx/lofi.py`.

### Mixer, sends and routing

- **H009** (*open*). Track volume, pan and summing happen in software, in float, in
  the same audio path, with inserts between the track source and the mixer.
  **Next test (static):** follow the multi-track node from the graph build
  (`0x1bc8d4` → `0x1bc7c8` → `0x1bacec`, which builds each `InsertFxProcessor`). Find
  where volume and pan are applied, the summing buffers, and the order of insert,
  fader and sends.
- **H010** (*open*). Sends are per-track levels into a few shared send buses, returned
  into the master bus before the Master FX and limiter; pre/post-fader is fixed in
  code. **Next test (static):** find where send levels are applied relative to the
  fader (needs H009) and where returns are summed.
- **H020** (*open*). Which effect types the Send unit actually uses. Its processor
  builds all 10 Master classes (F019). **Next test (static):** decode the Send
  parameter manager's type names, find callers of the Send processor's `setFxType`
  (`0x11a254`), and identify the objects at `SendFxUnit` `+0x80`/`+0x90`.
- **H006** (*open*). The 1.60 "FX2 on SAMPLE/THRU tracks" change is in routing code
  (`CompositeFxUnit` / FX-mode methods), not in any DSP routine. **Next test
  (static):** compare those method bodies between 1.50 and 1.60 with an
  address-insensitive match.
- **H015** (*open*). The copy stage after the device callback routes graph channels to
  the three DAC outputs, and device 0 is the 8-channel output. **Next test (static):**
  decode the arguments of the `0x577d5c` calls in `0x58e4c0–0x58e718` and tie the loop
  index in `0x590320` to the PCM names.
- **H016** (*open*, low priority). The app's 44,100 Hz / 64-frame request reaches ALSA
  unchanged, so one period = one callback = one FX block. **Next test (static):**
  trace `AudioDeviceManager::initialise` `0x5961b8` to the device open.
- **H017** (*open*, low priority). No DSP stage exists below the app either: the kernel
  codec drivers only move PCM. **Next test (static):** inspect the 1.60 kernel's
  AK4458/AK4452 drivers and codec register setup.
- **H008** (*guess*). The analog (Dave Smith) filter and the AS-1 path are analog
  hardware, controlled rather than computed, so they are outside the DSP work. **Next
  test (static):** find the filter's control path. It should write a control interface
  rather than process audio buffers. `DaveSmithManager` is in the class map.

### Parameters, presets and the UI

- **H019** (*open*). The effect IDs come from the project data (`prj::EffectData`) and
  the FX select popup, whose list gives the on-screen names of the 10 Insert and 10
  Master types. **Next test (static):** trace the callers of the Insert parameter
  manager's slot 32 (`0x1287d4`) and of the Master equivalent (`0x1237cc`). Read the
  `FxSelectPopupWidgetController` item table.
- **H030** (*guess*). The 2-band EQ's unfiltered first block is hidden on the device by
  the activation fade, and its UI offers only types 0–4 (type 5 crashes, F038).
  **Next test:** run the EQ through slot 18 with the activation path (emulator). Read
  the 2-band EQ view controllers' type list (static).
- **H032** (*guess*). Phaser retrigger (slot 10) is driven by sequencer start or
  pattern restart, and the Insert default Mixratio of 0 is overridden by a project or
  UI default. **Next test (static):** find callers of slot 10 (`[vtable+0x28]`). Read
  `prj::EffectData` defaults and the Phaser view controller's initial values.
- **H003** (*open*). The **[1.50]** FX step-lock machinery exists unchanged in 1.60 at
  shifted addresses: a 72-byte table at [1.50] `0x8a8fa0`, writers [1.50]
  `0x34f314`/`0x34f3f0`, and a reader at [1.50] `0x350d98`. See
  [project-format.md](project-format.md). **Next test (static):** an address-insensitive
  match of those functions against 1.60. Confirm the table bytes match and the
  49-case switch is the same. Lead (*guess*): 72-byte tables at `0x843d98`+0x78 and
  +0xc0.
- **H004** (*open*). The 72 FX parameter indices group one-to-one onto effect types and
  their parameters. **Next test:** join the 1.60 switch cases (after H003) with the
  view controllers' parameter tables and the setters, then run the setters on sample
  values (emulator).

### Interface and numerics

- **H011** (*open*). Every effect implements one virtual interface, and a factory keyed
  by effect type creates them. That interface would be the extension point for new
  effects. **Partly answered:** each processor constructs all 10 effects up front
  and switches by index (F016). That nothing re-points the list later is *likely*,
  because non-virtual writers were not swept (F017). **Next test
  (static):** align all effect vtables slot by slot and document the full contract
  (slots 5–10, 14, 18, 22–27, 31).
- **H024** (*open*). The building blocks (`SignalGate`, the `IirFilter` family,
  `LinearParameter`) are shared beyond the reconstructed effects. **Next test
  (static):** list every store of their vtable pointers and every call to their
  constructors (`0xf4e5c`, `0xe1edc`, `0xf1850`/`0xf1a00`), with the owning classes.
- **H027** (*likely*). The Master-context multi-mode filter (index 5) is the same class
  with different defaults only. **Next test (emulator):** build it through the Master
  processor path (ctor `0x114bc0`) and compare its output with `tools/fx/mmf.py`. The
  same check is worth doing for the EQ, LoFi and Phaser.
- **H029** (*likely*). Replacing the host's double `tan`/`pow` (and LoFi/MMF's host
  `log10f`) with glibc-2.13-exact routines keeps all models bit-exact and removes the
  last residual risk. **Next test:** implement them (or call the emulated 1.60 libm)
  and run ≥ 10,000 random coefficient sets.
- **H036** (*guess*). The oscillator's reads of memory its constructor never wrote are
  harmless on the device, because fresh allocations are zero. **Next test (static):**
  identify the allocator used for the effect kernels and `LfoProcessor`, and whether
  it zeroes memory.

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
