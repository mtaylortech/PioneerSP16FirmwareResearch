# Findings

What this research established about the Pioneer TORAIZ SP-16, organised by
capability, with an honest confidence level on each. Read the confidence labels
literally.

**Confidence labels**
- **Verified** — reproducible from files, checked more than one way.
- **Supported (static)** — a defensible reading of the binary/scripts; not run.
- **Demonstrated (emulator)** — observed in a substituted software environment
  (QEMU/Qiling with stubbed audio/devices/timers), **not** on hardware.
- **Partial / Blocked / Unknown / Not attempted** — as written.

> A run completing, a host fixture passing, or a research scope being accepted
> does **not** establish the feature it was aiming at. Emulator behaviour is not
> hardware behaviour.

## Platform and hardware (from the firmware and the service manual)

- **Verified:** SoC is NXP i.MX6Q (manual part MCIMX6Q5EYM10AD); the shipped
  software targets the i.MX6Q family. Binaries are ARM EABI5, armv7-a/softfp/neon.
- **Verified:** Linux kernel self-identifies as `3.0.101-2790-gc248ed7`; U-Boot
  2009.08-svn; BusyBox 1.20.2; glibc 2.13 toolchain. ALSA (alsa-lib 1.0.24.1).
- **Verified (documentary):** named DDR3, NAND and eMMC parts; two panel/sub
  MCUs (M1/M2); pad calibration + MAC data live in NAND per the manual.
- **Unknown:** actual RAM/NAND/eMMC geometry, enabled core count/clocks, and
  anything about a specific physical unit. No device was read out; all hardware
  facts are from documents and the shipped image, not measurements.

## Firmware containers and versions

- **Verified:** six releases (1.20–1.60) decode to ISO 9660 / Rock Ridge with
  validated tar and SquashFS payloads. Format and hashes: see
  [firmware-format.md](firmware-format.md), [firmware-reference.md](firmware-reference.md).
- **Supported (static):** a cross-version function-correspondence *pilot* on
  1.30→1.31 looked at two "reader" candidates. One unload candidate was
  byte-identical; the load candidate differed at ten call sites. 298 instruction
  records matched the original ELF bytes. **Callee/receiver semantics and all
  other functions/versions were not established** — this was a pilot, not a diff.

## Boot and application startup

- **Verified (static):** boot chain is U-Boot → kernel (A/B kernel slots
  declared) → BusyBox init → `rcS` → `rc.local` → `/root/pdj/apl_start`, which
  launches `EP085_Main_R` (and loads `snd-din-midi`, `midi_thru`). `apl_start`
  has a test-mode branch.
- **Verified:** `EP085_Main_R` is a ~12 MB, 32-bit ARM, dynamically linked,
  stripped ELF. "Stripped" means names/debug info removed — machine code,
  runtime symbols and some strings remain. No original application source was
  found anywhere in the shipped material.
- **Demonstrated (emulator):** in one bounded 1.60 run, the application's
  initializer and wrapper returned, dispatch proceeded, and a stable 800×480
  HOME screen was produced and stayed pixel-identical through the observation.
  The environment stubs audio/devices/syscalls and has known timing defects. It
  is **not** authentic board boot or a playable sampler. Harness (reference
  code): [`emulation/app/`](../emulation/app/).
- **Demonstrated (emulator):** one tagged TRACK-2 input was consumed by original
  handling and changed the selection; a separate tagged HOME→MIXER tap reached
  original handlers and produced a distinct 16-fader Mixer screen. Redraw
  latency was not measured.
- **Partial:** on the Mixer "Send" control, the widget identity/listener and
  active ownership were pinned down (the input record is 128 bytes with a
  reflected 0x8408 checksum over 124 bytes; only type 1 reaches the input
  callback). **No** successful Send gesture, encoder parameter edit, or live
  panel-record delivery was demonstrated — preparation is not delivered input.

## The "Normalize" study (add a normalize-sample feature)

- **Working host tool (Verified on host):** a standalone WAV peak normalizer plus
  an independent oracle and a 278-check synthetic suite. One exact rational gain
  from the whole-file/all-channel peak, −1 dBFS target, ties-to-even rounding,
  exact silence preserved, unsupported inputs refused. Shipped here:
  [`tools/normalization/`](../tools/normalization/).
- **Supported (static):** 1.50 reader/cache behaviour — a same-path reload can
  return old cached PCM while another holder survives; releasing all holders
  lets fresh PCM load. Save/writer paths distinguish project serialization from a
  separate resume file; several writer paths have unchecked returns / incomplete
  late-error coverage, so "stock success" is not proof of a durable commit.
- **Blocked:** integrating normalize into the firmware's sample lifecycle. A full
  construction-window observation found **zero** roster members; the producer/
  owner/lifetime protocol needed for a legal all-owner reload was never pinned
  down. A separate disposable macOS prototype wired selection→normalize→preview→
  Keep/Discard in a small PCM16/APFS envelope, but human listening and DAC
  fidelity were never confirmed, and it is **not** firmware behaviour.

## USB, updater, and diagnostic emulation (1.50 line)

- **Supported (static):** observed USB-B MIDI/mass-storage gadget modes and the
  whole-eMMC export path; the USB-A updater checks a package marker + CRC32
  before mounting and running its `update` program. This is **not** cryptographic
  authentication, and **no** command shell or arbitrary code loading was shown.
- **Supported (static):** the 1.50 project save path — fixed hidden staging
  name, leftover-safe, fsync before replace, but not atomic; a failed final
  rename leaves the project only as a hidden dot-file, which the unit's lists
  don't show. Details: [storage.md](storage.md). 1.60 identical.
- **Supported (static):** resume — `System/data.rsm` is normally a byte copy of
  the last saved/loaded project, always on; an empty `System/resuming` directory
  guards the boot-time load and quarantines a broken resume file to
  `System/crashed/`. Details: [storage.md](storage.md).
- **Supported (static; matched in emulation):** the eMMC layout and first-boot
  format — partition 1 type 0x83 at LBA 16, BusyBox 1.20.2 FAT32 with
  recognisable boot-sector fields; the format check does not wait for the
  partition node (outcome on real units unknown). Details: [storage.md](storage.md).
- **Demonstrated (emulator), partial:** a QEMU build executed original
  kernel/init/rootfs/application paths using explicit SD aliases and
  backlight/GPU substitutions, reaching a repeatable checkpoint defined by
  missing audio, a SIGSEGV, and a missing MTD partition. A VM-only ARM diagnostic
  wrote tags to, and read bytes back from, the guest framebuffer, and a fresh
  no-USB boot of the retained disk reached the same checkpoint. **Physical
  scanout, a healthy UI, authentic board behaviour, NAND recovery, and any
  deployable modified firmware remain unproven.** The boot-to-app-launch part is
  reproducible with [`emulation/board/`](../emulation/board/) (the USB/diagnostic
  arm is not included).

## What was NOT achieved (so no one over-reads the above)

- No authentic hardware boot, no real audio/DSP, no broad instrument usability.
- No recovered application source, no replacement OS, no deployable modified
  firmware, no demonstrated repack the device would accept, no recovery/rollback
  proof.
- No work on a physical unit beyond the owner's report that theirs runs OS 1.5
  and boots/plays normally.

## Reusable methods (the transferable part)

Version-and-hash-bound evidence; conservative partial struct layouts; strict
typed trace comparison; raw-receipt correlation; independent supervision/cleanup
of emulator runs; separating emulator/harness failures from application
behaviour. The Ghidra scripts and the contract/trace helpers in
[`tools/`](../tools/) encode some of this.
