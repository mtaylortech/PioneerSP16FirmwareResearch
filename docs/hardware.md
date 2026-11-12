# Hardware access, testing, and risk

> **Read [DISCLAIMER.md](../DISCLAIMER.md) first.** This document describes
> *documented leads and documentary observations*, not tested procedures.
> Nothing here has been verified on a physical unit by this project. If you act
> on any of it, **you do so entirely at your own risk and on your own
> responsibility.** Hardware work can permanently destroy the device and can be
> physically hazardous. This is not legal advice.

## What is actually known about the hardware

All of this comes from the service manual, the GPL/BSP source, and the shipped
firmware — **not** from probing a unit:

- **SoC:** NXP i.MX6Q (MCIMX6Q5EYM10AD per the service manual); binaries are
  armv7-a. (Cortex-A9 is the expected core for this SoC family, but the research
  did not independently confirm core type, count, or clocks.)
- **OS:** Linux 3.0.101, U-Boot 2009.08-svn, BusyBox 1.20.2.
- **Storage:** named NAND and eMMC parts; firmware declares a 256 MiB NAND
  partition map (boot / env / kernel_a / kernel_b / rootfs / pdj / data / …) in
  `fw_env.txt`. Pad calibration and MAC data live in NAND per the manual.
  How the two stores are used, USB storage mode and the eMMC layout are in
  [storage.md](storage.md). Kernel 3.0.101 has no RPMB support; eMMC boot
  partitions, if present, are exposed read-only, unused by the product, and not
  part of the USB export.
- **Controllers:** two panel/sub MCUs (M1/M2); panel firmware ships as
  `PANELCOM1.mot` / `PANELCOM2.mot`.

The actual RAM/NAND/eMMC geometry, boot settings, and debug availability on any
specific unit are **unknown** — none were measured.

## Documented access leads (unverified)

These are *leads from documents*, each with a real gap before it becomes access:

| Surface | What the documents show | The gap |
|---|---|---|
| Factory test mode | Service manual (QRT1001; the research used a third-party online reproduction) documents a power-on key combo (HOLD + TRACK + step 1) that reaches diagnostics, and menus including calibration, storage format, and factory reset. | Information screens vs. write/adjust operations are different risk classes. No custom-code loader is documented. Unverified on any unit. |
| Serial console | `inittab` respawns a board console; `rc_mxc.S` selects a serial port from kernel args and starts getty at 115200; `fw_env.txt` names `ttymxc0` as console. | Connector/test-point location, electrical levels, pinout, installed config, and credentials are all unknown. A baud rate is not electrical compatibility. |
| Network debug | `apl_start` sets a Telnet debug flag to 0; an inetd config lists services. | Presence of config is not a running, reachable, or usable service. |
| Boot / alternate boot | `fw_env.txt` defines MMC and network boot and normal NAND boot; boot delay 0. | No interactive prompt, accepted alternate image, or firmware-preserving launch demonstrated. Changing the persistent environment is itself a write. |
| JTAG | A JTAG-related setting appears in `fw_env.txt`. | No established connector, enablement, or debugger session. |
| Vendor USB update | The official update guide documents USB firmware updating. | Normal updating does not demonstrate custom-package acceptance or recovery from a bad state. |

## Risk and "bricking"

Different failures need different recovery and are not interchangeable:

- An application hang may be cleared by restarting — **only if** persistent state
  and hardware are intact.
- Sample/project corruption, calibration changes, boot/firmware corruption, and
  physical/electrical damage are progressively worse and may be unrecoverable.
- The manual places unit-specific data (calibration, identity) in NAND and
  specifies main-board replacement for defective NAND. A generic firmware update
  package is **not** a full unit backup.

**No meaningful numerical "bricking probability" can be given, and this project
does not offer one.** Information-only use of documented stock screens carries
less expected exposure than persistent boot/flash writes, but nothing here is a
guarantee of safety or recoverability. Raw-flash writes, persistent-environment
changes, and wrong interface voltages are the most consequential hazards to
avoid in any first attempt.

Note also: the shipped `apl_start` contains conditional storage-format and
boot-environment write branches. They were read in text, never exercised. Do not
treat re-running a stock launcher as a "harmless" way to execute code — RAM-
resident code can still write files and issue privileged device operations.

## A sane, low-risk testing progression (if you must)

This is a *suggested ordering of risk*, not an endorsement to proceed. Each step
is the reader's own decision and responsibility.

1. **Output-only, off-device:** normalize/prepare samples on a computer, transfer
   them, and play them on a stock unit. Establishes format/playback
   compatibility; changes nothing on the device.
2. **Identify and observe:** confirm the installed release; if you ever attempt
   serial, a **receive-only** boot capture after verifying connector/electrical
   compatibility is the least-invasive first observation. It does not establish
   login and does not authorize sending commands.
3. **Temporary, RAM-only code** — only after command access and an independent
   recovery path are both established, on disposable inputs.
4. **Persistent changes** — only after delivery *and* recovery are demonstrated
   for the exact exposure, and preferably on a spare unit.

Keep known test material (silence, low peaks, unequal stereo, already-normalized,
long recordings) and capture audio and UI actions separately. Power-loss and
fault testing need their own, separately considered, scope.
