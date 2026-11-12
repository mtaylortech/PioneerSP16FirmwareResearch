# How the SP-16 stores and moves files

This page explains where the TORAIZ SP-16 keeps its data, what happens in USB
mass-storage mode, how the internal eMMC is laid out and first formatted, and how
saving, moving, copying and "resume" work — including what a failed save looks
like on the unit.

**Basis and labels.** Findings come from static analysis of firmware **1.50**
(`EP085_Main_R`, SHA-256
`075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`), its shell
scripts and the GPL BusyBox 1.20.2 source, plus one emulation run of the
first-boot format using the stock 1.50 kernel and the firmware's own
BusyBox/udev. Addresses are 1.50 unless stated. Each claim is labelled:

- **confirmed** — seen in code (or a script line), or exactly matched;
- **likely** — strong indirect evidence;
- **guess** — plausible, unproven;
- **in emulation** — observed in QEMU, which is **not** a result from a real unit;
- **prediction** — what a real unit should show; not yet checked on hardware.

No firmware bytes, disassembly or disk images are reproduced here. Nothing on
this page is an instruction to modify a unit; see [DISCLAIMER.md](../DISCLAIMER.md).

**1.60 behaves the same.** Every storage function traced here (59 of 59) is
identical in 1.60 apart from addresses — **confirmed** (addresses-only
comparison, matching sizes, call edges and strings). Key 1.60 addresses are
listed in [§9](#9-firmware-160).

---

## 1. Two stores

| Store | What it holds | Exposed over USB? |
|---|---|---|
| **NAND** (256 MiB raw flash) | Boot loader and environment, two kernel slots (A/B), root filesystem, the application, and a UBIFS `data` volume (`mtd7` → `/root/data`) holding settings and touch/pad calibration. Partition map declared in `fw_env.txt`. | **No** — never exported (confirmed, scripts). |
| **eMMC** (~7.8 GB) | Your files: projects, samples, rendered audio, scenes, and the resume file. One FAT32 partition, mounted at `/mnt/emmc`. | **Yes**, as a whole disk (§2). |

- Mount options for the eMMC partition: `vfat`, read-write, `dmask=000,fmask=000`,
  `shortname=mixed`, `utf8`, `noatime`, `usefree` — **confirmed** (1.50 scripts).
- Top-level folder: `PIONEER DJ SAMPLER/`, containing `Samples`, `RenderedAudio`,
  `System`, `Scenes` and `Projects` — **observed** on one 1.50 unit over USB.
  The resume files live in `System/` (§7).

## 2. USB mass-storage mode

- Entering USB storage mode (`usb_gadget.sh`) **unmounts `/mnt/emmc`** and
  exports the **entire eMMC block device** (`/dev/mmcblk0`) to the computer as a
  writable disk — **confirmed** (script). The computer is then writing the
  unit's FAT32 filesystem directly, at block level; the unit is not mediating.
- USB MIDI and USB storage are **mutually exclusive** gadget modes; the eMMC is
  remounted when storage mode ends — **confirmed** (script).
- Because the whole disk is exported, the computer also sees the partition table
  and the unused sectors before the partition (§3).
- A computer may add its own metadata files (for example macOS dot-files).
  Because they start with `.`, the unit's own lists ignore them (§5) — **likely**.
- The unit does **not** reformat or repair the eMMC on its own once a partition
  exists (the format step runs only when partition 1 is missing, §3) —
  **confirmed** from script logic. So a filesystem damaged or reformatted from a
  computer is not automatically fixed by the unit.

## 3. eMMC layout and the first-boot format

On boot, `apl_start` formats the eMMC only if partition 1 does not exist
(`format_mmc`, `apl_start` l.147–191; trigger at l.223) — **confirmed**.

**Partition table** — **confirmed** (code), and matched exactly **in emulation**:

- BusyBox `fdisk` on this kernel sees a 4-head × 16-sector geometry, so it places
  partition 1 at **LBA 16** (8 KiB in), sized "whole disk − 16 sectors".
- The partition type byte is **0x83** ("Linux"), not a FAT type, because the
  script never sets one — **likely** from the script, observed **in emulation**.
- **Sectors 1–15 are never written** by product code; they keep whatever the eMMC
  held — **likely** (code), zero **in emulation** on a blank card.

**Filesystem** — `mkfs.vfat` on the unit is the **BusyBox 1.20.2** applet, not
dosfstools; its `-c` (bad-block check) and `-F 32` options have no effect in that
build — **confirmed** (rootfs link + source). The resulting boot sector is
recognisable by:

| Field | Value | Label |
|---|---|---|
| OEM name | `mkdosfs` | confirmed (source); in emulation |
| Hidden sectors | **0** (not 16, despite starting at LBA 16) | confirmed (source); in emulation |
| Backup boot sector | **3** | confirmed (source); in emulation |
| Drive number | **0x00** | confirmed (source); in emulation |
| Reserved sectors / FATs / media | 6 / 2 / 0xF8 | confirmed (source); in emulation |
| Heads / sectors per track | 4 / 16 | in emulation (real kernel geometry) |
| Volume label | empty (11 NUL bytes) | confirmed (source); in emulation |
| Volume ID | the format time; the script resets the clock to **2016-01-01 00:00** just before formatting (l.219–220), so it is ≈ `0x5685C180` plus a few seconds | confirmed (code); in emulation |

The size-dependent fields (sectors per cluster, FAT size, cluster count) follow
BusyBox 1.20.2's sizing rules; predicted values for a real unit are in §8.

**Clock note.** The unit resets its clock to 2016-01-01 at **every** boot
(`apl_start` l.220) — **confirmed**. File times written by the unit are therefore
roughly "time since boot", not real dates.

**Do not run the test scripts.** The root filesystem also ships Freescale
`unit_tests/autorun-mmc*.sh` scripts that would erase the eMMC. Product scripts
do not reference them — **likely**. They are noted here only so nobody runs them
by accident.

## 4. First-boot timing dependency

What the code does — **confirmed** (1.50 `apl_start`):

- After `fdisk` writes the new table (l.171–180), the script checks for the
  partition device node `/dev/mmcblk0p1` **immediately**, with no wait or retry
  (l.182). The node is created asynchronously by `udevd` after the kernel
  re-reads the table. (The else-branch message reads "is not.wait.", but no wait
  is performed.)
- If the node is not there yet, `format_mmc` returns **without running mkfs**.
  Partition 1 then exists but is unformatted, and because the format only runs
  when partition 1 is missing, **later boots do not retry** (l.223) — confirmed
  from the script logic. Mounting `/mnt/emmc` would then fail — **likely**.

What is known about real units:

- **In emulation**, with the firmware's own udev, the check ran before the node
  appeared in both runs. Emulated timing is **not** evidence about real hardware
  (emulator speed, missing boot services and real eMMC write latency all change
  it).
- **On a real unit the outcome is unknown.** At least one 1.50 unit has a FAT32
  partition at LBA 16, so either the check succeeded there or the eMMC was
  formatted some other way (factory or computer). The boot-sector fingerprints in
  §3 can tell those apart (§8, P7).

## 5. How saving a project works

Project writer `0x50a7c4` (1.50) — **confirmed** unless noted:

1. If `<name>.prj` already exists, the project is written to a **fixed** hidden
   staging name, `.<name>.prj`, beside it (built at `0x6587c8`). A new project is
   written directly.
2. A leftover `.<name>.prj` from an earlier failure **cannot corrupt** the new
   save: it is deleted first (`0x5079fc` → `0x507bc4`), and the output stream is
   also rewound and truncated before the first byte (`0x50a8c0`, `0x50a910`).
3. The staged data is **flushed and fsync'ed** (`FileOutputStream::flush`
   `0x64ec68`) before anything is replaced.
4. The old `<name>.prj` is deleted, then the staging file is renamed into place.
   The directory itself is not synced on this path (except an optional global
   `sync()` at `0x50a9ec`).

**Not atomic.** Step 4's delete-then-rename leaves a window. If the rename fails
after the old file was deleted, the writer reports failure and **keeps the
hidden staging file** (`0x50aa14`). The project then exists only as
`.<name>.prj`.

**What that looks like on the unit.** Every on-device project list and file
browser skips names starting with `.` (5 listing sites; JUCE's ignore-hidden flag;
the hidden test is `name[0] == '.'`) — **confirmed**. So such a project **appears
deleted** on the unit, although its data is intact — visibility **likely**
(strong).

**Recovering it.** Over USB storage mode the file is visible on a computer that
shows hidden files (macOS Finder: Cmd+Shift+.). Copy it off and rename it without
the leading dot. **Caution:** saving another project under the same name on the
unit first will delete and rewrite the staging file — it does not recover the old
data — **confirmed** (step 2 above).

**Sample sidecars (`.wav.dat`)** are written in place, without staging
(`0x374b1c` / `0x375054`). The rewrite path deletes the old file first and
ignores the result, and does not truncate — **likely** safe in practice. If that
delete ever failed while the file stayed writable, a second tree could be
appended and the old values would probably load — **guess**; no trigger is known.

## 6. Moving and copying files

The unit uses stock JUCE file operations — **confirmed**:

- A move (`moveFileTo` `0x64dc70` → `0x64dbc4`) first tries a plain `rename`
  (`0x64dbd8`), which is the whole operation within one volume.
- Only if `rename` fails does it **copy then delete** (`copyInternal`
  `0x64da50`, 16 KiB buffer). In practice that means moves between a USB stick
  and internal storage — **likely** (cross-filesystem rename fails).
- The copy **deletes any existing destination first**, does **not** fsync, and
  checks that the copy succeeded before closing.

## 7. Resume ("last memory")

- `System/data.rsm` is the resume file. It is a normal project file (same
  container and schema as `.prj`; see [project-format.md](project-format.md)) —
  **likely** (strong).
- It is normally a **byte copy** of the `.prj` just saved or loaded (dispatcher
  `0x33e99c` → `copyFileTo` `0x33eaf0`). It is re-serialized instead only for a
  `.tpkg` package or when there is no file to copy — **confirmed**.
- Resume is **always on**: the enable flag defaults to 1 and the
  delete-after-resume flag to 0, from build-time constants (`0x356a04` →
  constructor `0x33feb4`), with no setter found — **confirmed**. It is **not** a
  user setting — **likely** (strong).
- `System/resuming` is an **empty directory** used as a crash guard around the
  boot-time resume load (`ProjectManager::resumeProject` `0x3397c8`) —
  **confirmed** (intent **likely**):
  - it is created just before `data.rsm` is loaded and removed right after;
  - if it is **already present** when resume starts — meaning the previous resume
    load never finished — the app logs `resume file was broken!`, does **not**
    load `data.rsm`, moves it to `System/crashed/data.rsm` (replacing an older
    one) and removes the guard.
  - No save, load, shutdown or standby path touches it — **confirmed**. Resume
    runs at boot — **likely** (the static caller is a virtual call, not found).

## 8. Predictions for a real unit (not yet checked)

These follow from the code; each states what would refute it. They are expected
to be checked in a planned session on a real unit, and this page will be updated
with the results.

| # | Prediction | Basis | Refuted if… |
|---|---|---|---|
| P1 | Re-saving a project while a stale `.<name>.prj` exists gives a normal, loadable `<name>.prj` of the new size, with no staging file left | confirmed (static) | the result is larger than a fresh save, fails to load, or stale bytes remain |
| P2 | `System/resuming` is absent on a unit at rest; `System/crashed/` is absent unless a resume has failed | likely | `resuming` exists after a clean boot, or is a regular file |
| P3 | Creating an empty `System/resuming` folder over USB, then rebooting, means no project is resumed, `data.rsm` moves to `System/crashed/`, and the folder is removed | likely | the project still resumes, or `crashed/` is not created |
| P4 | Right after a save, `System/data.rsm` is byte-identical to the saved `.prj` | confirmed path; likely in practice | they differ |
| P5 | A `.<x>.prj` file copied into the projects folder over USB does not appear on the unit | confirmed (5 sites) | it is listed |
| P6 | No on-device setting disables resume | likely | a menu option stops resume |
| P7 | The boot sector at LBA 16 shows OEM `mkdosfs`, 8 sectors/cluster, 6 reserved, hidden 0, backup boot 3, drive 0x00, volume ID ≈ `0x5685C1xx`; for a 15,269,888-sector eMMC also total 15,269,872 sectors and FAT size 14,883 | confirmed (source); in emulation | OEM differs, hidden = 16, backup = 6 or drive = 0x80 (a different formatter); a volume ID far from 2016-01-01; or a different FAT size for that disk size |
| P8 | P1–P7 hold identically on 1.60 | confirmed (static, 59/59) | any differs between units on 1.50 and 1.60 |

For a 15,269,888-sector eMMC whose sectors 1–15 are zero, the predicted SHA-256 of
sectors 0–15 is
`05b2f7ac42241375fe8b77f2e868937fa45ba53154868d232b03e350aeea2584`
(prediction). If the gap is not zero, compare sector 0 alone.

Other predicted unit values (15,269,888-sector disk, at format time): 1,905,012
clusters, 1,905,011 free; FAT copies at LBA 22 and 14,905; data area at LBA
29,788; 4 unused sectors at the end of partition 1.

## 9. Firmware 1.60

Behaviour is identical to 1.50 (see the note at the top). Selected 1.60 addresses: project writer `0x50c044`,
staging prepare `0x50927c`, `FileOutputStream` open `0x64e300`, rewind `0x6508b0`,
truncate `0x64e198`; `resumeProject` `0x33c048`, resume defaults `0x359284`,
resume dispatcher `0x34121c`; listers `0x27de5c`, `0x27e388`, `0x27eb44`,
`0x42ffbc`, `0x4301e8`.

## 10. What is not known

- The live contents of the NAND environment (the only low-risk route identified
  is a receive-only serial console).
- The contents of the eMMC boot areas (`mmcblk0boot0/1`). The kernel exposes them
  read-only if present; nothing in the product uses them and they are not part of
  the USB export.
- **RPMB:** kernel 3.0.101 has no RPMB support at all — **confirmed**.
- Whether real units pass the first-boot check (§4), and how a given unit was
  actually formatted.
- The exact volume-ID offset, the free-cluster count after use, and the eMMC's
  real sector size (512 assumed — likely).
- Parked: the caller of `resumeProject`; the names of two `ProjectManager`
  operations (vtable +0x58/+0x60) and the check at `0x3391a0`; ten further
  directory-listing callers not reviewed; the `.wav.dat` append case.
