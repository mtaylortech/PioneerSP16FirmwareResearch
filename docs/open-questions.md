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
5. **Improve the symbol set.** `symbols/` covers 1.60 startup + Mixer/Send. Label
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
| Storage | Live NAND environment; eMMC boot-area contents; whether real units pass the first-boot format check; on-unit confirmation of the predicted boot sector and resume behaviour. Parked: `resumeProject` caller, `ProjectManager` ops +0x58/+0x60 and check `0x3391a0`, ten listing callers, the `.wav.dat` append case. | Open. Static/emulated picture in [storage.md](storage.md); NAND env needs a receive-only serial console; the rest needs a unit session. |

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
