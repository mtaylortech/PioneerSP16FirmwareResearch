# emulation/board — partial SP-16 board emulator (firmware 1.50)

Boots Pioneer's **original, unmodified 1.50 Linux kernel** under **stock QEMU**
(the built-in `sabrelite` i.MX6Q reference board), installs the original root
filesystem onto a synthetic SD disk using the firmware's own guest tools, then
boots that disk through the stock init scripts until the sampler application
launches.

> **Read [../../DISCLAIMER.md](../../DISCLAIMER.md).** This runs Pioneer code
> inside an emulator only. It never touches real hardware. It is research
> tooling, not a working instrument.

## What you get (and what you don't)

**Demonstrated in the research (emulator):** original kernel boot → stock
`switch_root` → rootfs services → `apl_start` → application launch, stopping at
a repeatable checkpoint about 65–77 s into each boot:

- the AK4458 audio device is missing (`No such device (-19)`),
- the application receives **SIGSEGV**,
- the recovery path finds no `/dev/mtd12`,
- `apl_start` falls through to `Listening on port 2345`.

**Not achieved:** a usable UI, audio, the SP-16's own bootloader or bank
selection, NAND/UBI storage, the panel/MCU controllers, or anything resembling
board fidelity. The SABRE Lite board is a *related* i.MX6 board, not an SP-16.
Whether the SIGSEGV is caused by the missing audio device was **not** proven.

## How it works

1. **`build-disk`** creates a 512 MiB raw disk: MBR, FAT16 partition 1 (1 MiB,
   16 MiB, the "internal" area), empty partition 2 (17 MiB, 495 MiB, rootfs), and
   a CRC-valid U-Boot environment record at offset `0xC0000` with constructed
   values (`rootfs=sd`, `usb_versionup=off`, …). These values are invented to
   select the SD branch; they are **not** a snapshot of any real unit. It also
   writes an initrd carrying the eight original 1.50 packages plus a small
   install script.
2. **`install-rootfs`** boots the original kernel with that initrd. The
   firmware's own `mkfs.ext4`, `tar` and SquashFS support format partition 2
   and install the four rootfs archives, `pdj.tar.gz` under `/root`, and the
   `lib/bin/share` SquashFS contents under `/usr`. It adds one udev rule plus two
   symlinks so the stock scripts' `mmcblk1` device names resolve to QEMU's
   single SD card (QEMU's duplicate SD bus names prevented attaching two
   cards). The result is saved read-only as `work/baseline.raw`.
3. **`control NAME`** copies the baseline and boots it. A tiny bootstrap reads
   the environment with the stock `fw_printenv`, runs the stock `bootmod`, and
   hands over to the stock `/init`.
4. **`cold NAME --from OTHER`** boots a previously used disk again, unchanged,
   to see whether retained state alters the boot.

### The three interventions (valid for the 1.50 kernel ONLY)

The kernel bytes are never modified. QEMU starts paused, and the tool uses
QEMU's GDB stub on a private Unix socket to make three changes before letting
it run:

| Where | What | Why |
|---|---|---|
| `0x800089a8` (backlight init call) | skip the call: PC+4, r0=0 | QEMU has no SP-16 backlight; the kernel stalled here |
| `0x8002394c` (`gpu_init`) | return `-ENODEV` to the caller without running it | the Vivante/Galcore GPU init stalls with no hardware |
| `0x020D8004` (`SRC_SBMR1`) | write `0x60` | makes the stock `bootmod` helper report **MMC** boot so the SD branch is taken; QEMU's generic loader write did not survive to that point |

`check` refuses to continue unless `images/uImage` is the exact 1.50 kernel
(SHA-256 `f9a5931f…`), because these addresses are wrong for any other build.

## Requirements

- **QEMU 10.0.x with the ARM system emulator** (`--target-list=arm-softmmu`).
  The research used 10.0.14, built from source on macOS (Apple silicon). Other
  versions are untested; device and bus names can change between releases.
  Minimal build used by the research:
  ```sh
  ./configure --target-list=arm-softmmu --disable-default-features \
      --enable-tcg --enable-system --disable-user --disable-tools \
      --disable-docs --disable-guest-agent --enable-fdt=internal
  ninja -C build qemu-system-arm
  ```
  (It needed a recent GLib; the research built GLib 2.82.5 locally and passed
  its paths through `qemu_env`.)
- **Python 3.8+** and **`pip install pyfatfs`** (used only to format the FAT16
  partition).
- **Decoded firmware 1.50.** Decrypt it with
  [`../../tools/decode/upd_decrypt.py`](../../tools/decode/upd_decrypt.py) and
  extract the ISO; point `images_dir` at its `images/` folder. `check` verifies
  `uImage` and all eight packages against the 1.50 hashes.
- About **1.2 GB** free disk space per few runs (512 MiB baseline + a copy per
  boot).

## Steps

```sh
cp config.example.json config.json      # then edit the three paths
python3 sp16_board.py check             # must print READY
python3 sp16_board.py build-disk
python3 sp16_board.py install-rootfs    # a few minutes; saves work/baseline.raw
python3 sp16_board.py control run1      # ~1-2 min; prints the checkpoint markers
python3 sp16_board.py cold run2 --from run1   # optional: boot run1's disk again
```

Each boot writes `work/logs/<name>/serial.txt` (the guest console),
`events.json`, `command.json`, `mmio.log` (QEMU unimplemented-device log) and
`markers.json`. `control` and `cold` exit 0 only if the research checkpoint was
reproduced.

## Differences from the original research scripts

This is a consolidation of three October 2026 studies (persistent-boot-update,
original-rootfs-control, arm-drawing-retention), whose scrubbed notes are
published under [`../../research-notes/E1-board-emulator/`](../../research-notes/E1-board-emulator/).
It encodes the **final** working recipe from them. Deliberately left out:

- the **USB update / diagnostic-drawing arm** and its `VM-ONLY` update carrier:
  that carrier was produced with the real firmware key and cannot be published;
- a background "observer" inside the guest, which never worked across
  `switch_root` in the research;
- a patched copy of the firmware's `decrypt_update.sh` used only by the USB arm;
- the research's session-ceiling assertions and separate resource-limited
  process supervisor. This tool keeps a per-boot deadline (`boot_seconds`) and
  terminates/kills QEMU when done. QEMU runs with `-nic none`, no device
  passthrough, and only the files you configure.

The disk layout, environment record and installer archive this tool builds
were checked against the research: partition table, environment record and the
84 MB installer archive are byte-identical; the FAT16 partition differs only in
its random volume serial number and label timestamp.

## Validation status

- **Offline:** `check` and `build-disk` verified against the research's own
  artifacts (2026-11-11).
- **Full run with this tool: verified 2026-11-11** on macOS (Apple silicon),
  QEMU 10.0.14, firmware 1.50. Every step passed and both boots reproduced all
  nine checkpoint markers:

  | Step | Result | Time to checkpoint |
  |---|---|---|
  | `install-rootfs` | rootfs installed by the firmware's own tools | 264 s |
  | `control run1` | all 9 markers, stop at `Listening on port 2345` | 185 s |
  | `cold run2 --from run1` | all 9 markers on the retained disk | 146 s |

  The research's own scripts reached the same checkpoint in about 65–77 s per
  boot. The milestones are identical; the slower times in this run were not
  investigated (emulation speed depends on the host and its load).
- The baseline disk's SHA-256 differs from the research's, as expected:
  `mkfs.ext4` and the FAT formatter write fresh random identifiers and
  timestamps each time.

License: MIT (code). See [../../NOTICE.md](../../NOTICE.md).
