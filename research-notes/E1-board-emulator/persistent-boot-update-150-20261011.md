<!-- research-note: experiments/persistent-boot-update-150-20261011/HANDOFF.md | thread E1 | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Persistent boot/update feasibility — held 1.50 — 2026-10-11

**Result:** the original kernel and USB update path executed in a partial virtual board, including discovery, checker, decrypting loop, ISO mount, and the original diagnostic caller. A faithful SP16 boot and drawable, usable original UI remain unachieved. The diagnostic printed `BEGIN` / `REFUSED`; no frame completion was observed. The caller reported update failure and continued into the already-failing rootfs boot path. Investigation ended after one fresh cold boot from the retained internal files with USB removed. No further launches are scheduled.

Question: can the held firmware boot from persistent virtual media, execute a file-backed USB diagnostic through original code, and then cold boot from the exact retained state?

## Preservation completed first

Only the completed `diagnostic-frame-preflight-150-20261011` study was preserved. Content commit `65b21572a66cefd11019d60317c822ff4e4fc0d0` changed 187 paths, with readback of 186 regular files, one symlink and 5,299,572 regular-file bytes. Receipt commit `e41df65d77d8196d27bad9920a3179e5a193213e` changed two receipt paths; its completed directory tree reads back as 187 regular files, one symlink, 5,300,092 bytes. The initial and final Git index were empty; unrelated work was untouched. This new study remains uncommitted. [Receipt summary] `evidence/preservation.json` (evidence not published), [full preservation receipt] `../diagnostic-frame-preflight-150-20261011/PRESERVATION.md` (evidence not published).

Git preserves content, executable bits and symlink text, not filesystem metadata or running state. These are local commits, with external original/GPL/runtime dependencies; they are not an off-device backup.

## Runtime and explicit substitutions

No suitable QEMU installation existed. Built task-local QEMU 10.0.14 ARM system emulation with GLib 2.82.5, Meson 1.8.3 and the installed Apple toolchain. No global runtime configuration changed. [Runtime pin] `evidence/runtime-built.json` (evidence not published), [downloads] `evidence/downloads.json` (evidence not published), [source extraction] `evidence/source-extraction.json` (evidence not published), [code/input pins] `evidence/code-input-pins.json` (evidence not published).

Loaded original `decode/output/image1/iso/images/uImage`, Linux 3.0.101-2790-gc248ed7, SHA256 `f9a5931feb0bf11b3e64b74e2a874b5cf58f0927204e890273f5e8def2a3566b`. QEMU binary SHA256 `e3a7e2e5d3c5c409ec76dff17c425587d3e38116173842c5f9132fcc2241476d`. Both pins matched again at closeout.

Unmodified direct-kernel boot failed at backlight initialization before `/init`. Skipping that call exposed a Galcore initialization stall. The partial profile uses two sparse debugger substitutions: at bound call `0x800089a8`, advance PC by four and set r0=0; at `gpu_init=0x8002394c`, return to LR with -ENODEV. Original kernel bytes were not changed. Display/GPU operations bypassed by these substitutions are not validated. [Backlight binding] `evidence/backlight-bypass-binding.json` (evidence not published), [GPU binding] `evidence/gpu-binding.json` (evidence not published), [boot3 events] `logs/boot3/events.json` (evidence not published).

The external RAM cpio bootstrap reads the original `fw_printenv`, creates volatile `/usb_versionup`, and executes original `/init`. This substitutes missing SPI request acquisition; the original `subucom_read` still runs and fails. Its RAM `/etc/fw_env.config` changes only SD path `/dev/mmcblk1` to `/dev/mmcblk0`, where the original reader accesses the actual virtual block medium. [Full profile and persistent-object limits] `evidence/baseline-profile2.json` (evidence not published).

The two 32 MiB internal SD images contain synthetic CRC-valid environment records, including `rootfs=nfs`, `usb_versionup=on`, and `kernel_bank=A`. They are not unit snapshots. No bootloader/bank selection, GPMI/BCH/NAND system/data storage, faithful eMMC, MCU flash or working display hardware was supplied. QEMU [SabreLite documentation](https://www.qemu.org/docs/master/system/arm/sabrelite.html) and the actual 10.0.14 model/source inventory support partial i.MX6 exploration, not SP16 board equivalence. [Actual model inventory] `evidence/qtree.txt` (evidence not published).

## Observations and persistence

| Arm | Actual result |
| --- | --- |
| boot1 | Original kernel panicked at backlight; host stopped at 287.36 s. |
| boot2c | Backlight bypass reached Galcore initialization; bounded observation ended at 270 s. |
| boot3 | Two substitutions reached original `/init` at 10.57 s; missing rootfs led to panic at 19.37 s. |
| control | Original SD mapping prevented request acquisition; bounded bootstrap retries failed. |
| control2 | Corrected partial profile, no USB: original `/init` at 11.85 s, USB-update checkpoint at 14.75 s. |
| diagnostic | Same fixed internal baseline plus file-backed USB: original `/init` at 10.83 s; actual diagnostic and caller executed; rootfs panic at 21.35 s. |
| cold | New QEMU process, no RAM restore or USB, exact retained diagnostic internal files: `/init` at 11.12 s, `usb_versionup=on`, USB-update checkpoint at 14.03 s. Stopped at checkpoint. |

The VM-only update carrier is described in docs/findings.md at a high level; its composition and the reuse of firmware sector crypto are omitted here. (summarized per owner E1 guard) The diagnostic is a static ARM ELF, requires a supported framebuffer contract, prints refusal otherwise, and always exits 2. [Media manifest] `evidence/media-manifest.json` (evidence not published), [diagnostic manifest] `evidence/diagnostic-manifest.json` (evidence not published), [source] `input/diagnostic.S` (evidence not published).

Actual serial showed `VM-ONLY VM150 BEGIN`, `VM-ONLY VM150 REFUSED`, `update.sh error`, and `error_code = 2`, followed by NFS mount/switch_root failure and kernel panic. Refusal cause and exact wait status were not independently instrumented. Expected absent-library copy errors and `LOOP_CLR_FD` failure remain in raw evidence. Nonzero diagnostic return did not prevent original boot continuation. [Diagnostic serial] `logs/diagnostic/serial.txt` (evidence not published), [cold serial] `logs/cold/serial.txt` (evidence not published), [outcome] `evidence/outcome.json` (evidence not published).

Internal images changed by **zero bytes**, including after cold boot. USB changed by **two bytes at offset 33394** (`0000` → `4b5d`), in its FAT access-date metadata. Attribution is to the original Linux USB/FAT/update path as a whole; individual writes were not traced. Stored request stayed on; stored bank text does not prove selected bank. [Exact comparisons] `evidence/persistent-comparison.json` (evidence not published), [post-cold hashes] `evidence/cleanup-final.json` (evidence not published).

## Bounds, failures, cleanup and remaining question

Every original-kernel attempt was independently supervised at ≤300 seconds; early checkpoints stopped failed/completed questions. Effective commands/configurations and raw stdout/stderr remain under `input/`, `runs/`, and `logs/`. Runtime had no network backend, hardware passthrough or physical USB, with unused private owned Unix debugger endpoints, finite group termination/reaping, and output/resource bounds. Host exit zero means QEMU was reaped, not clean guest shutdown. [Final cleanup] `evidence/cleanup-final.json` (evidence not published): all recorded groups absent, zero owned running workers, zero debugger sockets, immutable baselines/pins intact, preservation directory clean, index empty.

Retained harness/setup failures: initial download file-size limit; excluded external X11 archive symlink; invalid configure option; missing GDB server option; sandbox Unix-socket bind denial; media builder dependency/assembler/link corrections; and an unqualified boot2c reconnect reply. Those failures are separate from original firmware behavior. Initial sandbox `ps` denial was resolved with a narrowly filtered authorized census. Download hashes were retained; independent GPG signature verification was not performed.

Remaining question is full-board feasibility, particularly persistent NAND/rootfs and display/MCU support. The partial profile can answer scoped caller/flag questions, but it cannot establish normal application startup, safe device deployment, physical recovery, power-loss behavior or usable UI. Further board reconstruction needs a separately selected scope; none was launched or scheduled. Session overran while building/adapting this partial emulator; work stopped after the retained-state cold check and essential cleanup.
