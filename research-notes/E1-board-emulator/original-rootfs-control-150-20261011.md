<!-- research-note: experiments/original-rootfs-control-150-20261011/HANDOFF.md | thread E1 | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Original rootfs and persistent boot comparison — held 1.50 — October 11, 2026

**PARTIAL: original storage boot and application launch are demonstrated through an explicit SD adapter.** The request-off control, VM-only diagnostic continuation, and fresh retained-state cold boot all executed original `switch_root`, rootfs init/services, `apl_start`, and application launch. All stopped at an absent AK4458 audio device, observed application SIGSEGV, and absent MTD12 reserve4 recovery storage. The relationship between the audio error and SIGSEGV is not proved. No usable UI or faithful SP16 board boot was achieved. Work is stopped; no successor, monitor or hardware action was created.

Question: can an original-rootfs control traverse consequential pre-start decisions, and does a failed diagnostic change the subsequent represented persistent boot behavior?

## Completed study preservation first

Preserved only `experiments/persistent-boot-update-150-20261011/`. Content commit **98e42d5cebd6e4c166dfab8d0ed4bdc99414bb7f** changed 3,001 scoped paths; exact blob/mode readback found 2,983 regular files, 18 symlinks, 553,763,738 bytes. Receipt/correction commit **36b08427fa3e71e7e3c0b8d1752ee8614c551289** changed six scoped paths; final exact readback found 2,988 regular files, 18 symlinks, 554,932,850 bytes. Index remained empty and unrelated work untouched. This new study is separate and uncommitted. [Receipts] `evidence/preservation.json` (evidence not published), [selection, gaps and full limits] `../persistent-boot-update-150-20261011/preservation/README.md` (evidence not published).

The first staging assertion failed because Git omitted 756 nested dependency sources; my shell erroneously continued to commit. The correction preserves their exact content/link text/modes in a scoped archive, with every member independently read back against disk. Executable QEMU, owned libraries/Python packages, source archives, baselines, retained state, bindings/configuration, all raw run records/failures and original handoff are retained. Duplicate expanded source/build objects/caches and dependency Git metadata are accounted for and omitted.

External original firmware/GPL inputs, macOS/Apple/Homebrew toolchain, system libraries, PCRE2 and Python remain dependencies. Absolute Mach-O install paths/Python symlinks need deliberate relocation. Git retains bytes/executable bits/link text, not full modes, sparse allocation, times, ACL/xattrs, inode state, empty directories or live state. Local Git is not off-device backup. No new key dump was created.

## Selected route and identity

Reused unchanged task-local **QEMU 10.0.14** binary SHA256 `e3a7e2e5d3c5c409ec76dff17c425587d3e38116173842c5f9132fcc2241476d`, with its retained GLib/intl libraries. Loaded original 1.50 kernel `uImage`, SHA256 `f9a5931feb0bf11b3e64b74e2a874b5cf58f0927204e890273f5e8def2a3566b`. [Runtime] `evidence/runtime-built.json` (evidence not published), [kernel] `evidence/kernel-input.json` (evidence not published), [package/route pins] `evidence/route.json` (evidence not published), [critical original files] `evidence/critical-originals.json` (evidence not published), [effective code/input pins] `evidence/final-code-input-pins.json` (evidence not published).

The held kernel's in-memory IKCONFIG confirms ext4/UBIFS/GPMI support but no built-in block2mtd, mtdram or nandsim. The actual QEMU i.MX6 model lacks GPMI/BCH NAND support; original APBH probe also fails. A full controller/ECC/MTD implementation was rejected as open-ended for this bounded question. Original `/init` already has an SD/ext4 branch, so that was selected. [Held config] `input/held-kernel.config` (evidence not published), [held init] `input/held-init` (evidence not published).

Profile **VM150-ORIGINAL-SD-ADAPTER-1** uses one 512 MiB ordinary raw file: synthetic FAT16 p1 at 1 MiB/16 MiB, ext4 p2 at 17 MiB/495 MiB, and CRC-valid environment at offset 0xc0000/8192 bytes. Original guest `mkfs.ext4` created a journal; original tar/squashfs/copy assembled the four held rootfs archives, pdj under `/root`, and original SFS contents under `/usr/{lib,bin,share}`. Construction ended with sync and filesystem unmount; that is not successful application boot. [Immutable baseline] `evidence/baseline.json` (evidence not published), [builder serial] `logs/builder3/serial.txt` (evidence not published).

QEMU's duplicate SD bus names prevented distinct CLI routing. Explicit guest aliases map `/dev/mmcblk1` to mmcblk0 and `/dev/mmcblk1p1` to mmcblk0p2, with an added rootfs udev rule. The original environment configuration and boot scripts retain their bytes. This combines internal FAT and SD-rootfs roles behind one model; it is not physical eMMC/SD independence or NAND semantics. [Backend qualification] `evidence/backend-qualified.json` (evidence not published).

Retained debugger substitutions skip backlight at 0x800089a8 and return -ENODEV from GPU init 0x8002394c. One new model configuration writes emulated SRC_SBMR1=0x60 through QEMU's physical-memory debugger mode after initialization, verifies exact readback and returns to virtual mode. Original `bootmod` then reports MMC. This simulates a declared boot input; no bootloader or authentic kernel-bank selection ran. [Binding/correction] `evidence/bootmode-correction.json` (evidence not published), [used access/coverage slices] `evidence/used-storage-slices.json` (evidence not published), [slice method] `../../.agents/skills/sp16-feature-trace/references/slice-contracts.md` (evidence not published).

Environment fields are constructed: rootfs=sd, mmcdev=/dev/mmcblk1p1, usb_versionup=off, ubifs_formatted=true, ubifs_data_update=false, aplstart=on, kernel_bank=A, loopback network fields. Original readers acquire them from live virtual storage; no inaccessible init cache is seeded. The RAM bootstrap supplies the original caller's volatile request-file contract because the unchanged SPI helper fails. Only the diagnostic arm overrides that volatile file to on; it never persists an on request. Actual init prints on there, showing that the failed background helper did not override it before entry.

## Matched original execution and persistence

Every final arm has the same 300-second cap and early stop at the original post-fault/recovery checkpoint `Listening on port 2345`. The original application and guest debug helper are inside the isolated guest; no host TCP endpoint is exposed.

| Arm | Actual checkpoint |
| --- | --- |
| control3 | Request off/no USB; MMC; original rootfs init, pre-start and app launch; dependency checkpoint at **66.94 s**. |
| diagnostic | Same baseline; volatile request on/file-backed USB; diagnostic and original caller; same continuation checkpoint at **76.75 s**. |
| cold | New process/reset CPU/RAM, no USB/volatile trigger, exact post-diagnostic internal file; request off, ext4 journal recovery, same checkpoint at **65.23 s**. |

[Control qualification] `evidence/control-checkpoint.json` (evidence not published), [actual outcomes] `evidence/outcome.json` (evidence not published), [control serial] `logs/control3/serial.txt` (evidence not published), [diagnostic serial] `logs/diagnostic/serial.txt` (evidence not published), [cold serial] `logs/cold/serial.txt` (evidence not published).

MMC mode selects original secondary-updater/data branches. The synthetic rootfs contains no `nandupdate`, so stock SD flashing is untested/unexecuted. FAT p1 presence deliberately avoids original eMMC formatting. NAND/UBI format flags and factory data are not qualified by the constructed values. Original Xorg also reports missing XKB resources and a segfault. Original reserve4 formatting/attach/mount attempts fail because MTD12 is absent; no success substitute was installed.

Reused unchanged VM-only carrier/diagnostic, with no stock flasher, pre_update, firmware images or replacement libraries. Original USB discovery, checker, crypto loop, ISO mount and caller executed. Child printed BEGIN/REFUSED; one RAM-only echo immediately after original saved `$?` observed **shell wait status 2**, preserving its return/error consequences. Raw encoded waitpid status was not captured. Actual queried framebuffer is 1024×768, 16 bpp, pitch2048, incompatible with required 800×480/pitch1600; exact refusal branch remains uninstrumented. No frame COMPLETE or usable panel rendering was observed.

| Compared with immutable baseline | Changed bytes | Internal FAT | Ext4 | Environment |
| --- | ---: | ---: | ---: | ---: |
| control3 | 622,479 | 423 | 622,056 | 0 |
| diagnostic before cold | 649,170 | 423 | 648,747 | 0 |
| diagnostic after cold | 650,057 | 423 | 649,634 | 0 |

USB changed one FAT access-date byte at offset33394, 00→21. Cold changed 163,903 bytes relative to the retained post-diagnostic snapshot; differences overlap and totals are not additive. Exact contiguous ranges and hashes are retained, with bounded hex for long ranges. [Control changes] `evidence/control3-comparison.json` (evidence not published), [diagnostic changes] `evidence/diagnostic-comparison.json` (evidence not published), [cold changes] `evidence/diagnostic-after-cold-comparison.json` (evidence not published). All environment CRCs stayed valid and request stayed off. Cold input SHA equals the exact retained post-diagnostic SHA; no baseline/RAM restoration or flag repair occurred. Internal filesystem changes also occur in the no-update control; they are not by themselves diagnostic damage. Individual write syscalls/file attribution were not traced.

## Failures, cleanup and conclusion

Retained failures: invalid QOM bus path; SD read-only restriction; ambiguous multiple-card attachment; missing guest p2 node; mkfs journal ENOENT fixed by actual mount-table link; existing RAM nodes defeating initial aliases; generic loader not producing MMC mode; unsuccessful background observer gate across switch_root; and two cold-preparation ceiling refusals plus a missing-config supervisor start before any guest spawn. Independent mapped app/library hashes are absent because that observer missed its gate; original content is bound by package identities, assembly and actual execution, not an invented receipt.

Effective commands are in `input/*.command.json`, `logs/*/command.json`, and `runs/*/command.json`; raw stdout/stderr/results remain with each arm. Unchanged finite group supervision bounds guests to300 seconds, outer315, with resource/output limits, private unused Unix sockets, no credentials, no network backend or real device passthrough. Own planning ceiling was revised from00:33:35Z through00:34:35Z to a final fixed00:37:00Z before cold launch to retain the full cap; failed preparations launched no firmware. [Adjustment/failures] `evidence/ceiling-adjustment.json` (evidence not published). All owned groups were reaped, no workers/sockets remain, original runtime/kernel and immutable baseline pins match, prior tracked study is unchanged, index is empty. [Cleanup] `evidence/cleanup-final.json` (evidence not published). Host termination is not clean guest completion.

This resolves original-rootfs bootability through the declared SD adapter and shows no update-request re-entry after this volatile-trigger/return2 diagnostic in represented persistent state. It does not prove healthy application startup/UI, real held-key acquisition, physical flash/ECC/torn-write behavior, boot-bank selection, MCU state or unit recovery. The older retained-on cold result was seeded on and remains separate. No new retained-on or fault arm was run. More full-board work would require actual AK4458/audio and reserve4/NAND support; it is not justified as an automatic continuation of this completed storage test.
