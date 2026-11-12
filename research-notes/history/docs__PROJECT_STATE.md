<!-- source: docs/PROJECT_STATE.md | scrubbed -->

# Pioneer TORAIZ SP-16 — canonical project state

**Workflow reset, October 8, 2026:** [README.md] `../README.md` (evidence not published) is now the live status and [AGENTS.md] `../AGENTS.md` (evidence not published) defines the streamlined workflow. This synthesis and its dated authority/next-step statements below are historical. The [latest post-parent run] `../experiments/post-parent-startup-20261008-150354/HANDOFF.md` (evidence not published) completed the parent and enclosing constructor; full startup/UI remains open. Do not repeat its completed phases or revive old administrative requirements by following an older handoff.

Current consolidation: **2026-10-08 (America/Chicago)**; initial static consolidation: 2026-10-07. Start with [Current Handoff](#current-handoff), then follow the evidence IDs into [EVIDENCE_LEDGER.md] `EVIDENCE_LEDGER.md` (evidence not published). This document is the canonical synthesis; the earlier `decode/` notes are supporting history. Raw originals and validated derived artifacts remain the evidence of record. This workspace has no `.git` directory; “repository” here means the local project folder, not a committed or backed-up Git repository.

## 1. Purpose and present scope

**Project objective:** reproducibly understand the firmware update format and software architecture of the **Pioneer DJ TORAIZ SP-16**, and determine how far its original application can run in a virtual environment with observable behavior. The first runtime question was “Can we run Pioneer’s original application, and what is the first obstacle?” Earlier CPU/RAM comparison and four-core workload questions motivate the research; no measured SP-16/MPC2500 performance ratio or complete DSP workload map is established. Long-term modification/feature work has been discussed; no modification target has been selected, implemented or deployed.

**VERIFIED project state:** both held SP-16 updates (internally 1.50 and 1.60) are decoded, extracted and audited. The latest read-only startup trace identifies runtime main2000 returning from original XCreateWindow and progressing through allocation then 16×64 data-reset loops, with completed call/return and changing-object evidence through76.467846s [E30]. This narrows the delay to observed continued initialization; no persistent causal wait or narrow defect explaining missing UI is established. The identical 36-byte initial CreateWindow remains queued in libxcb, request7/written6/error0, with no later display write/flush/map, server child or original UI. The request is1×1 InputOnly. Diagnostic success; milestone2 remains highest and milestone3 is open. E28/E29 authentication/nonblocking/buffer evidence and unchanged original app/library bytes are retained. E25's76.216-second synthetic-audio/corrected-TLS baseline remains historical; new traces are not replacement performance/stability baselines. No usable virtual instrument, physical-unit observation, flashing, Linux rebuild, repacking or tested recovery is established.

**Authority and working preferences:** latest direct user request invoked docs/NEXT_SESSION_PROMPT-20261008-105321.txt and authorized up to30 minutes from **10:59:16 CDT October8**, experiment cutoff11:24:16 and finish deadline11:29:16 [E30]. One chat, no subagents. ONE supervised read-only startup probe stopped/reaped by **11:04:56.796 CDT**, then the completed diagnostic queue moved immediately to preservation; no correction/retry was justified. Native final JSON is absent: worker alarm fired at76.023s, main continued, independent host SIGTERM/reap at78.013007s. Exact partial evidence is retained. Actual close is in the new archive's external session-close report. The scope is complete and gives no standing replay permission. Preserve original/historical inputs, installed runtime, measured baseline and all archives. No hardware deployment, vendor scripts, Linux rebuild, external guest networking, panel/input simulation, forced flush/map or broad application reverse engineering is authorized.

## 2. Evidence model and finding register

- **VERIFIED:** directly demonstrated by a named artifact, reproducible check or documentary statement. “The service manual lists chip X” verifies the document's statement, not the installed chip on the user's unit.
- **STRONGLY SUPPORTED:** multiple independent evidence items support an interpretation, but the specific behavior has not been demonstrated.
- **HYPOTHESIS:** a plausible, testable interpretation. Parked hypotheses are not active experiments.
- **UNKNOWN:** insufficient evidence; not an assertion that something is absent or impossible.

Every important technical statement below inherits an explicit classification or references an ID from this register. The register contains **45 VERIFIED findings**. There are **0 active hypotheses under test** and **3 parked hypotheses** in section 14. Counts are identifiers, not a claim that every sentence represents an independent experiment.

| ID | Level | Finding | Evidence |
|---|---|---|---|
| V01 | VERIFIED | Two held `.UPD` inputs identify versions 1.50 and 1.60 in their trailers and decoded release files; exact sizes/hashes are recorded. | E01, E02 |
| V02 | VERIFIED | Both update payloads successfully decrypt as AES-256-CBC cryptoloop data into coherent ISO filesystems, with file contents validated. | E02–E05 |
| V03 | VERIFIED | Bundled losetup -N uses input through first LF/NUL, copies at most 31 raw bytes into a zeroed 32-byte key; no hex decode or hash. | E04; addresses below |
| V04 | VERIFIED | CBC resets per 512-byte sector; IV is LE32(sector modulo 2^32) plus 12 zeros; encrypted payload begins at offset 0. | E03–E05 |
| V05 | VERIFIED | Both updates have a 20-byte plaintext trailer; IEEE CRC32 over preceding ciphertext matches its LE32 stored value. | E01, E03, E06 |
| V06 | VERIFIED | Decoded payloads are ISO 9660 with Rock Ridge, label UsbAuto, 2048-byte blocks; declared volume sizes equal payload lengths. | E02, E03 |
| V07 | VERIFIED | Both 128 KiB samples passed descriptor, both-endian field, directory, dot-record and extent checks before full processing. | E02, E03, E20 |
| V08 | VERIFIED | Full ISO files, symlink targets and source record sets match extracted trees; originals and saved ISOs passed the fresh audit. | E02, E03 |
| V09 | VERIFIED | Each ISO contains five gzip/tar payloads; source member sets, content, links and gzip CRCs were validated. | E02, E03 |
| V10 | VERIFIED | Each ISO contains three SquashFS 4.0 little-endian zlib images; fresh extraction matches saved trees, inode counts and hardlinks. | E02, E03 |
| V11 | VERIFIED | Each payload set contains 386 expanded nested containers: 384 font gzip files, one documentation gzip file, one Python test tar. | E02, nested reports |
| V12 | VERIFIED | Five special entries per update are preserved only as metadata, with original containers retained. | E02; section 6 |
| V13 | VERIFIED | Both uImages name Linux-3.0.101-2790-gc248ed7; their header/data CRCs pass, but the two kernel files have different bytes. | E02, E18, inventory |
| V14 | VERIFIED | Both EP085_Main_R files are stripped, dynamically linked, 32-bit little-endian ARM EABI5 executables using /lib/ld-linux.so.3. | E18 |
| V15 | VERIFIED | Main application dynamic headers expose imports including ALSA, X11, FreeType, ICU, libcld, tcmalloc and standard runtime libraries. | E18; full per-image import lists in snapshot |
| V16 | VERIFIED | Decoded startup scripts connect BusyBox init → rcS/rc.local → /root/pdj/apl_start → EP085_Main_R; launcher includes MIDI module setup. | E16 |
| V17 | VERIFIED | Shipped fw_env.txt declares NAND partitions and A/B kernel selection, alongside NAND/MMC/network boot command definitions. | E17 |
| V18 | VERIFIED | Supplied initramfs source includes raw NAND reads, RAM-root assembly, UBI/UBIFS misc storage and three SquashFS mounts before switch_root. | E15 |
| V19 | VERIFIED | Service manual lists MAIN IC2000 as MCIMX6Q5EYM10AD and assigns main/USB-A/MIDI control and audio processing to it. | E07 PDF p.49 / printed p.46 |
| V20 | VERIFIED | Service manual lists two DDR3 RAM devices, IC2300/IC2301, K4B4G1646D-BCMA. | E07 PDF pp.7,13,49 |
| V21 | VERIFIED | Service manual lists NAND IC2601 MX30LF2G18AC-TI and identifies firmware, MAC, pad calibration and project-setting storage. | E07 PDF pp.13,49 |
| V22 | VERIFIED | Service manual lists eMMC IC3800 THGBMHG6C1LBAWL for preset sounds/file data and project settings. | E07 PDF pp.7,13,49 |
| V23 | VERIFIED | Manual lists M1 IC8005 and M2 IC8008 as R5F364AENFA-U0; M1 covers LED/power-related switches, M2 covers switches/encoders/touch/pads/gain. | E07 PDF pp.28,30,49 |
| V24 | VERIFIED | Service manual updater illustration displays MAIN system, apl, SUB1 and SUB2 labels. | E07 PDF p.61 / printed p.58 |
| V25 | VERIFIED | Held platform release contains Linux 3.0.101, U-Boot 2009.08, BusyBox 1.20.2 trees plus LTIB configuration/build scripts. | E12, E13, E23 |
| V26 | VERIFIED | Build scripts identify GCC 4.6.2/glibc 2.13 Freescale-Linaro 2011.12 paths and two ARM cross-prefix forms. | E13; E18 RPATH corroboration |
| V27 | VERIFIED | Supplied defconfig enables MX6Q, CPU_V7, preemption, ALSA PCM and raw MIDI. | E14 |
| V28 | VERIFIED | Both extracted BusyBox binaries contain the banner BusyBox v1.20.2 (). | E18 |
| V29 | VERIFIED | Both bootloader payloads contain U-Boot 2009.08-svn banner fragments. | E18 |
| V30 | VERIFIED | Held licenses/source metadata include mtd-utils, ALSA, GStreamer and Freescale multimedia packages; integration scripts list exact package versions. | E11, E22, E23 |
| V31 | VERIFIED | Three assembled source archives are byte-identical to ordered concatenations of their preserved numbered parts. | E12; snapshot/inventory |
| V32 | VERIFIED | The two IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA archives (one named with “ 2”) are byte-identical. | inventory SHA-256 |
| V33 | VERIFIED | Legacy source extraction report records 4,678 archive operations, including two with 773 and 2 omitted special entries. | E19; this verifies the report, not an independent replay of all entries |
| V34 | VERIFIED | Official update guide describes ZIP→UPD distribution; release history dates 1.50 to 2018-06-07 and 1.60 to 2019-10-03. | E08, E09 |
| V35 | VERIFIED | Internal app revisions are 6284 / 6550; SUB1/SUB2 revision files are 5187 / 3671 in both images; build timestamps precede public release dates. | E02, E18 |
| V36 | VERIFIED | PANELCOM1.mot and PANELCOM2.mot are individually byte-identical across the two releases, despite different ISO offsets. | inventory; E18 |
| V37 | VERIFIED | The unchanged 1.60 application reached entry `0xb5cc8` and main `0xb3ac4` in Qiling with documented environment adjustments; created `AudioSrcHelper0`, `FlashWriter`, and `UIThread`; failed to open ALSA `hw:ak4458audio,0` and subsequently read address zero at `0x58eebc`. | E24; application startup only, not a working virtual SP-16 or proof of core affinity |
| V38 | VERIFIED | With the original ALSA library configured for its null plugin, the original application opens playback/capture and repeatedly calls audio read/write APIs; sampled transfers return 64 frames. The longer probe reaches project/audio-worker/network thread creation. | E25; silent synthetic I/O, no real audio quality/timing or complete instrument behavior established |
| V39 | VERIFIED | Original application requests core 0 for main/UI, core 1 for `Juce ALSA`, core 2 for the first `ALSAInput`, `ProjectManager` and `AudioWorkerSC3`, and core 3 for the second `ALSAInput` and `AudioWorkerSC4`. | E25; syscall mask observations; affinity is not implemented by the emulator and physical utilization is unmeasured |
| V40 | VERIFIED | Installed Qiling's ARM TLS helper reads a shared memory word while thread restoration changes the ARM TLS register; the final probe records differing shared/current-thread values and supplies the current register at the emulated kernel helper. | E25; emulator defect evidence and documented correction; final runtime outcome is in the session summary |
| V41 | VERIFIED | Placing the current scoped cookie in actual guest root root/display.xauth makes access return 0; guest setup status is 1. Stock fcntl64 passes Linux flags directly to Darwin and clears host nonblocking mode in a local reproducer; the display-only correction retains nonblocking mode. | E28; original firmware/library bytes unchanged |
| V42 | VERIFIED | Original XOpenDisplay returns 0x17de000 and original XCreateWindow returns 0x200001; all server-root tree queries show zero children. Independent host supervision stops/reaps the guest at 78.013921 s despite a worker alarm at 76.004691 s; no final native retry JSON exists. | E28; milestone 2 only, partial counters/final PC unknown; no original UI capture |
| V43 | VERIFIED | Shipped ARM libX11 instructions establish Display fd/request/buffer offsets and real library flush/map entry points; shipped libxcb instructions establish its separate 4096-byte output buffer and sequence counters. Live entry/checkpoint bytes and tracked descriptor equality validate the read-only snapshot locations. | E29; xlib-layout.json and saved disassemblies, no source-ABI assumption |
| V44 | VERIFIED | Original 36-byte CreateWindow request for 0x200001 transfers from Xlib to libxcb at return and remains identical at 73.002816s and final 76.010376s, request 7/written 6/error 0; no later traced library/display write or server child. Its requested geometry is1×1/class 2 InputOnly. | E29; diagnostic success, milestone 2 only; natural startup wait cause and server acceptance untested |
| V45 | VERIFIED | Runtime main2000 returns from original CreateWindow via0x698100/0x698104 to0x698500, then completes allocation and16×64 data-reset loops on changing objects through76.467846s while the identical request remains queued. Continued initialization is observed; persistent causal wait, total parent work/completion and eventual original UI remain unestablished. | E30; capped console counts are lower bounds; native final JSON absent; exact host supervision78.013007s |

## 3. Hardware and software baseline

| Area | Current conclusion and level | Boundary / source class |
|---|---|---|
| SoC | **VERIFIED V19:** manual's exact part is MCIMX6Q5EYM10AD. **STRONGLY SUPPORTED S01:** the shipped software uses the same i.MX6Q platform family represented by the manual and GPL configuration. | Service-manual mirror + GPL config + ARM binary evidence; no physical-unit readout. |
| CPU/ARM generation | **VERIFIED V14/V27/V39:** ARM EABI5 binaries; supplied CPU_V7 config; application RPATH includes armv7-a/softfp/neon; application requests cores 0–3 for specific threads. | **UNKNOWN:** actual enabled core count, clock and CPU feature state. Cortex-A9 is an expected i.MX6Q association, not independently established by a chip datasheet/CPU observation reviewed here. |
| RAM | **VERIFIED V20:** two named DDR3 parts. | **UNKNOWN:** aggregate usable RAM/boot reservation measured on the device. Do not silently infer a capacity from a part string without adding a datasheet/source. |
| NAND | **VERIFIED V21/V17:** named NAND chip; firmware declares a 256 MiB primary partition span. | Declared layout is not a physical capacity measurement; no NAND/OOB dump or per-unit bad-block map exists in reviewed artifacts. |
| eMMC | **VERIFIED V22:** named eMMC and manual-described storage purpose. | **UNKNOWN:** actual capacity/partition table/filesystem and contents of a physical unit. No eMMC dump. |
| Peripheral MCUs | **VERIFIED V23:** two identified M1/M2 controllers and manual functions. | Update payload-to-controller mapping still a parked hypothesis; no MCU disassembly or runtime protocol trace. |
| Bootloader | **VERIFIED V29/V25:** 2009.08-svn banner; 2009.08 source tree and Freescale 3.0.101/4.1.1 integration package. | **UNKNOWN:** exact source-to-shipped-binary reproducibility and console access. |
| Linux | **VERIFIED V13:** both kernel headers name 3.0.101-2790-gc248ed7; versions alone do not mean identical kernels. | Both 3.0.35/4.1.0 and 3.0.101/4.1.1 source inputs exist. No exact release kernel rebuild. |
| BusyBox / libc | **VERIFIED V28/V26:** BusyBox 1.20.2 banner; glibc 2.13 toolchain paths and libc-2.13.so in outer ISO libraries. | Generic notice says BusyBox v1.2; use actual binary identity for these releases. |
| LTIB | **VERIFIED V25/V26:** /home/iMX6/ltib build layout and Freescale-Linaro toolchain. E21 documents an Ubuntu 9.04-era host, with a later subsection. | Historical instructions, not the identified release build host or a tested modern build recipe. |
| mtd-utils / UBI | **VERIFIED V18/V30:** licenses list mtd-utils; scripts call nanddump/ubiattach/ubiformat and mount UBIFS. | **UNKNOWN:** exact shipped mtd-utils version and measured NAND state. Script presence does not make executing it safe. |
| ALSA | **VERIFIED V15/V27/V30/V38:** libasound import, PCM/raw-MIDI configuration, alsa-lib 1.0.24.1 / alsa-utils 1.0.24.2 metadata, and original-library PCM open/read/write calls observed under the null fixture. | Physical audio, MIDI runtime behavior, hardware latency and complete DSP processing remain unknown. Synthetic PCM transfer is not instrument validation. |
| Multimedia | **VERIFIED V30:** held gst-fsl-plugins 3.0.11, GStreamer 0.10-era components, codec/parser 3.0.11 and VPU wrapper 1.0.46 integration; older 3.0.7-2/1.0.35-2 inputs also present. | Package presence is not proof that the sampler uses every component. Dedicated audio DSP firmware remains **UNKNOWN**. |

**Source distinctions:** E07 is a third-party copy of manufacturer service documentation; E08–E11 are local manufacturer/support documents. E12–E15/E21–E23 are supplied GPL/BSP material. E01/E02/E16–E18 are update-derived evidence. No community-derived result has been adopted as an SP-16 fact.

## 4. Firmware and source inventory

The initial static selected-artifact size/hash inventory is [ARTIFACT_INVENTORY.md] `ARTIFACT_INVENTORY.md` (evidence not published) (108 records) and [JSON] `ARTIFACT_INVENTORY.json` (evidence not published). It covers every top-level supplied file except Finder metadata, both decoded ISOs, all primary `iso/images/` components, updater/application binaries and selected supporting evidence. Thousands of nested BSP packages are indexed by E19 rather than misrepresented as additional SP-16 releases. This 108-record inventory predates the runtime experiments; historical per-experiment verification files and [closing emulation validation] `EMULATION_HANDOFF_VALIDATION.json` (evidence not published) cover their separate artifacts. Do not silently expand or regenerate the original inventory.

### Canonical updates and decoded containers — VERIFIED V01/V06

| Held file | Internal version | Bytes | SHA-256 |
|---|---|---:|---|
| `ResearchSourceFiles/TORAIZSP16VER150.UPD` | 1.50 | 99,493,908 | `11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a` |
| `ResearchSourceFiles/TORAIZSP16.UPD` | 1.60 | 99,495,956 | `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4` |
| `decode/output/image1/decoded.iso` | 1.50 | 99,493,888 | `534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b` |
| `decode/output/image2/decoded.iso` | 1.60 | 99,495,936 | `6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb` |

Supplied `.UPD` originals were preserved; outputs are derived. Distribution ZIPs are described in E08 but are not present. Acquisition URLs/publisher hashes for these two held files are **UNKNOWN**. No other SP-16 release image, DJS-1000 image, modified `.UPD`, or physical flash dump was located in the reviewed target inventory. Release-history mentions of earlier versions do not establish possession.

### Supplied source/development inputs — VERIFIED V25/V31/V32

- `pioneerdj_tsp.tar.gz` plus `.00`–`.01`: platform source/build files and initramfs; assembled archive matches parts.
- `L3.0.101_4.1.1_141016_source.tar.gz` plus `.00`–`.01`: newer Freescale BSP inputs; assembled archive matches parts.
- `L3.0.35_4.1.0_130816_source.tar.gz` plus `.00`–`.05`: older BSP/dependencies; assembled archive matches parts.
- `L3.0.35_4.1.0_docs.tar.gz`: historical BSP host/reference documents.
- `IMX_MMCODEC_3.0.101_4.1.1_Bundle.tar.gz`: newer codec sources/binaries.
- `IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA.tar.gz` and `IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA 2.tar.gz`: identical copies, 62,012,124 bytes, SHA-256 `d875d1916d25290366105ddf19997327ff52b9873e3dfd2f2af4a321a47c6099`.
- `ltib_patch.tar.gz` and extracted `ResearchSourceFiles/ltib_patch/`: integration patches/scripts.

All have detailed hashes/status in the inventory. No new SHA-1/MD5 values were invented or computed; pre-existing BSP MD5 files remain package material. Source completeness/reproducibility is **UNKNOWN**, distinct from archive extraction status.

## TORAIZSP16.UPD Format

**VERIFIED V02–V06:** this is a sector-encrypted ISO payload followed by a small plaintext trailer, not a discovered partition-table container or a standard OpenSSL salted envelope.

```text
byte 0                                            payload_end     EOF
+-------------------------------------------------+----------------+
| AES-256-CBC ISO ciphertext; 512-byte sectors      | 20-byte trailer|
+-------------------------------------------------+----------------+
```

| Field / parameter | Proven value |
|---|---|
| Payload offset | 0 for both held inputs |
| Ciphertext length | 99,493,888 (1.50), 99,495,936 (1.60); multiples of 512 and 2048 |
| Cipher | AES-256, CBC reset independently for every 512 bytes; no padding removal |
| Sector IV | `LE32(sector_number & 0xffffffff) || 12 zero bytes`, sector 0 at file start |
| Local key source | `extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/usr/local/pdj/aes256.key` |
| Key interpretation | First line through LF/NUL; first 31 raw bytes, zero-pad to 32. No hex decoding, no hash. Key bytes are deliberately not recorded here. |
| Trailer bytes 0–10 | ASCII `LIVESAMPLER` |
| Trailer bytes 11–15 | `1.50\0` / `1.60\0` |
| Trailer bytes 16–19 | LE32 IEEE CRC32 over the entire ciphertext: `f1679304` / `6f3bb5a2` |
| Decoded PVD | Offset 32,768: descriptor type 1, `CD001`, version 1; label `UsbAuto`; block size 2048 |

E04 binary addresses: `main` -N branch 0x8cec; `xgetpass` 0x9624; no-hash `set_loop` branch 0x9acc. E05 sets default CBC and sector IV. E06 subtracts 20 bytes near 0x85d8 and compares computed CRC at 0x8608–0x8614. The original `check_sig` marker comparison uses only four bytes; the decoder additionally requires the full 11-byte marker. The decoder's stricter condition is validated for these inputs, not claimed to exactly reproduce every acceptance condition.

The first 16 ciphertext bytes happen to be identical (`579f4973b282113059cc30c3913eb802`); they are encrypted data, **not a format magic or plaintext header**. No entropy calculation was retained or required: coherent decoding, source matches, CRCs and file verification establish encryption directly. There is no retained evidence of a plaintext component table before encryption. Component offsets come from the decoded ISO directory records.

**UNKNOWN:** whether any further authenticity checks exist inside the later updater, whether a custom repacked update would be accepted, and whether this key applies beyond the two held releases. Using one supplied key for both held updates is proven; device-independence across all hardware/revisions is not.

## 6. Transformation chain and extraction status

**VERIFIED V07–V12:**

```text
held .UPD (no held original firmware ZIP)
  → ciphertext CRC + 20-byte trailer validation
  → both 128 KiB samples decoded and ISO structure validated
  → full decoded.iso
  → iso/ (Rock Ridge names, files and links)
  → payloads/{pdj,rootfs1,rootfs2,rootfs3,rootfs4,bin,lib,share}/
  → nested/ (additional gzip/tar contents)
```

[TRANSFORMATIONS.json] `TRANSFORMATIONS.json` (evidence not published) records 25 grouped operations, including three verified source-part concatenations, with exact inputs/hashes, commands or operation names, output paths, output-manifest hashes and validation details. Directory trees do not have a raw binary SHA-256: their referenced manifests enumerate per-file SHA-256, paths and link targets. Nested reports contain each gzip input/output hash; the nested tar uses its source hash and the referenced per-file manifest. Nothing requires recovering the chat transcript.

| Level | image1 / 1.50 | image2 / 1.60 | Validation |
|---|---:|---:|---|
| ISO regular files | 68 | 68 | SHA-256 of each extracted file equals its decoded source extent |
| ISO symlinks / subdirectories | 26 / 19 | 26 / 19 | Exact source record names, types, link targets; 20 directories including root |
| Primary payload regular paths | 12,232 | 12,228 | Tar source-member reads + fresh strict SquashFS extraction comparison |
| Primary payload symlinks / directories | 715 / 665 | 715 / 651 | Manifests and source checks; directory counts include payload roots |
| Nested containers expanded | 386 | 386 | Gzip CRC, content hashes, tar member/sparse/hardlink verification |
| Unsupported file-level signatures encountered | 0 | 0 | Among formats checked by `container_kind`; not an exhaustive proof of all possible formats |
| Special entries materialized | 0 | 0 | Five metadata-only entries per image listed below |

Remaining metadata-only entries per image:

- Linux `dev/tty` (5:0), `dev/console` (5:1), `dev/null` (1:3): image1 `rootfs3.tar.gz`, image2 `rootfs1.tar.gz`.
- Nested Python `testtar.tar`: character device `3-CHRTYPE` (1:3) and FIFO `6-FIFOTYPE`.

**Scope limitation:** all verified regular files/links from the supported file-level containers are accessible. It is inaccurate to say “every byte has been turned into readable source” or “all executable interiors are unpacked.” Kernel/bootloader/raw-binary interiors were not carved. Host ownership/timestamps/xattrs are not guaranteed, sparse/hardlink representations may differ where documented, absolute symlinks may not resolve outside the intended Linux layout, and separate rootfs archive trees have not been merged into a bootable image. Original containers remain present.

The separate historical GPL-source extraction report has additional omissions: 773 initramfs special entries and 2 test-archive entries. These are not failures in the two decoded firmware trees and are not covered by the “five per image” count. [V33, E19]

## 7. Filesystems and declared partitions

**VERIFIED V06/V10:** ISO payload begins at decrypted offset 0. SquashFS components start on ISO 2048-byte boundaries; their internal superblock is offset 0 within each extracted `.sfs`. Gzip/tar is an archive, not a filesystem partition. Full component extents/hashes are in E18 and each ISO manifest (`extent × 2048`).

| Component | 1.50 ISO offset | 1.60 ISO offset | File bytes (both) | Inodes (both) |
|---|---:|---:|---:|---:|
| `bin.sfs` | 6,803,456 | 10,186,752 | 6,844,416 | 376 |
| `lib.sfs` | 13,649,920 | 17,033,216 | 48,947,200 | 4,396 |
| `share.sfs` | 78,702,592 | 82,083,840 | 12,136,448 | 5,357 |

All three are SquashFS 4.0 little-endian, zlib, 131,072-byte compression blocks. Superblock `bytes_used` differs by release and is less than padded file size; exact values are in reports. Fresh strict extraction reproduced content/path/type/mode/symlink inventories and hardlink groups; unique inode counts matched superblocks. [V10]

**VERIFIED V17, configuration-only:** both `fw_env.txt` files declare the following primary MTD span. Offsets are arithmetic from the declared sequential sizes; this is not a parsed physical partition table.

| Index/name | Offset MiB | Length MiB |
|---|---:|---:|
| 0 boot | 0 | 3 |
| 1 reserve1 | 3 | 1 |
| 2 env | 4 | 1 |
| 3 kernel_a | 5 | 10 |
| 4 kernel_b | 15 | 10 |
| 5 rootfs | 25 | 32 |
| 6 pdj | 57 | 20 |
| 7 data | 77 | 20 |
| 8 reserve2 | 97 | 20 |
| 9 data_raw | 117 | 3 |
| 10 reserve3 | 120 | 10 |
| 11 misc | 130 | 118 |
| 12 reserve4 | 248 | 8 |

The declaration also includes overlapping access aliases: `block_boot` 0x500000 bytes at 0, `block_linux` 0xD000000 bytes at 0x500000, and `block_all` to the device end at 0. They must not be added to the primary 256 MiB span. Kernel boot commands read 0x500000 bytes at 0x500000 or 0xF00000, although each declared bank spans 10 MiB. These are recorded configuration values, not a demonstrated rollback mechanism.

**VERIFIED V18, supplied-source-only:** initramfs reads four rootfs tar chunks at relative offsets 0, 8, 16 and 24 MiB in mtd5, reads the application archive from mtd6, assembles a RAM-backed root, uses UBI/UBIFS for misc, mounts `lib.sfs` at `/usr/lib`, `share.sfs` at `/usr/share`, `bin.sfs` at `/usr/bin`, then switch_roots to init. The archive containing that source initramfs exists; no initramfs carved from either release kernel has been compared to it.

**UNKNOWN:** actual NAND/OOB layout and current contents on a device; actual UBI volume geometry; eMMC filesystem; presence of any deployed JFFS2/ext/cramfs partition. Source/config support or filesystem signatures alone must not be promoted to a verified physical filesystem. No mounting is needed for the established workflow; use userspace extraction commands in section 12.

## 8. Executable and application findings

**VERIFIED V14/V15/V16:** primary launched application is preserved at:

- 1.50: `decode/output/image1/payloads/pdj/pdj/EP085_Main_R`, 11,993,612 bytes, SHA-256 `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`.
- 1.60: `decode/output/image2/payloads/pdj/pdj/EP085_Main_R`, 12,000,396 bytes, SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`.

ELF: ARM 32-bit little-endian EABI5, dynamically linked, interpreter `/lib/ld-linux.so.3`, stripped. Its GNU/Linux 2.6.31 ABI tag is a compatibility marker, not the system's running kernel version. “Stripped” does not mean encrypted, absent, or impossible to analyze; names/debugging information have been removed, while machine code, runtime symbols and some strings remain. No original proprietary application source has been identified in the inspected source release.

Imports include `libX11.so.6`, `libXext.so.6`, `libasound.so.2`, `libfreetype.so.6`, `libcld.so.0`, ICU `.so.51` libraries, `libtcmalloc.so.4`, `libstdc++.so.6` and standard libc/libm/libdl/libpthread/librt/libgcc. Full per-version lists and RPATH are recorded in E18; RPATH includes LTIB and Freescale-Linaro armv7-a/softfp/neon library paths. Do not infer a complete UI architecture or realtime scheduling model from imports.

Decoded `inittab` calls rcS and board startup scripts; rcS calls rc.local; rc.local launches `/root/pdj/apl_start`, whose normal/testmode branches start `EP085_Main_R`. Launcher also loads `snd-din-midi` and `midi_thru`. Helpers such as `appcon`, `applog`, `gdbserver` and `with_core_app` are present; their existence does not prove debugger access, active services or supported extension points. [E16, manifests]

Tools actually used: `file` for formats/ELF identity; `strings` for bounded banners; `objdump -d` for supplied losetup/check_sig key/trailer behavior; `objdump -p` for static application dependencies; Qiling/Unicorn for bounded application execution; Capstone/pyelftools for localized offline ARM/PLT inspection. Entry `0xb5cc8`, main `0xb3ac4`, audio-startup boundaries and allocator-fault instructions have saved runtime/disassembly evidence. No Ghidra/radare2/Binary Ninja/IDA project, application-wide disassembly or decompiled feature map is recorded. Main `iso/update` executable is an unstripped ARM ELF, but its internal write/verification logic has not been traced. [E18/E20/E24/E25]

## 9. Component model and update labels

| Component | Current mapping / level | Remaining boundary |
|---|---|---|
| Bootloader | **VERIFIED:** `iso/images/u-boot.bin.nand` plus held U-Boot source [V25/V29] | Exact flashed placement/ECC behavior not observed |
| Linux | **VERIFIED:** `iso/images/uImage` [V13] | Matching build and embedded initramfs unverified |
| OS files | **VERIFIED:** four rootfs tar archives and three SquashFS containers [V09/V10] | Supplied-source mount model [V18]; no bootable merged output |
| Application/resources | **VERIFIED:** pdj.tar.gz contains launched executable, startup/helpers and resources [V14/V16] | Feature responsibilities internal to application unresolved |
| Panel firmware | **VERIFIED:** two Motorola S-record files, PANELCOM1/2.mot, and two SUB revision files [V35/V36] | Mapping to manual M1/M2 remains H02 |
| Calibration/identity | **VERIFIED documentary statement:** manual places pad calibration/MAC data in NAND [V21] | No per-device dump/data format or backup validation |
| Dedicated DSP firmware | **UNKNOWN** | Generic BSP VPU/codec material is insufficient evidence |
| Update metadata | **VERIFIED:** trailer version/CRC, release.txt, app.rev, system.rev, subucom*.rev [V01/V05/V35] | Full updater acceptance/dispatch logic unknown |

Manual labels themselves are **VERIFIED V24**. Exact code/component mappings for **MAIN system, apl, SUB1 and SUB2 remain UNKNOWN**. Application/system/subucom revision files and M1/M2 hardware make conventional mappings plausible (H01/H02), but naming similarity is not proof of updater dispatch.

## 10. Relationship to DJS-1000

### What is directly known about DJS-1000 in this project

**UNKNOWN / not established:** no held DJS-1000 update/dump or saved cited community report was found in the reviewed project inventory/notes. U-Boot access, flash dumping, AES keys, crypto-loop images and large executables on DJS-1000 are not recorded as verified comparative findings here. No behavior has been reproduced on that device in this work.

### What may apply to SP-16

No DJS-1000-derived technical conclusion is needed for the demonstrated SP-16 decoder. **VERIFIED V02–V06** rest on SP-16 input bytes, the supplied platform artifacts and validated outputs. Future comparative information must get its own evidence-ledger entry and reproduction status; it must not silently become an SP-16 fact. Source-script comments mentioning SmartDJ or other device names are not an attribution proof.

## 11. Pioneer GPL/BSP analysis and limitations

**VERIFIED V25–V30:** the useful source chain includes Linux 3.0.101, U-Boot 2009.08, BusyBox 1.20.2, LTIB platform profiles, initramfs scripts/tools, Freescale multimedia integration and historical 3.0.35 inputs. `make_linux` copies the supplied initramfs into LTIB and invokes ARM cross-compilation; `make_rootfs` invokes `./ltib --deploy`; `make_boot` selects NAND/MMC build flags, uses `mx6dl_sabresd_config` and renames its output accordingly. These scripts are evidence, not tested recipes.

`ltib_common.sh` names `/opt/freescale/usr/local/gcc-4.6.2-glibc-2.13-linaro-multilib-2011.12/fsl-linaro-toolchain`. Its `cross_compile` variable uses `arm-none-linux-gnueabi-`, while `set_toolchain` sets `arm-fsl-linux-gnueabi-`; both are recorded rather than harmonized without evidence. E21's historical host guide is titled Ubuntu 9.04 and contains a special Ubuntu 11.10 section. The actual compiler invocation/build host for each proprietary release is **UNKNOWN**.

**Conflicts/qualifications:**

- Generic license notice says BusyBox v1.2; supplied source and both shipped banners establish 1.20.2 for these binaries. The former is insufficient exact-version evidence.
- `bsp_setup2` points at linux-3.0.35; held platform source and shipped kernel headers identify 3.0.101. E22 shows newer BSP integration inputs, but no full historical build chain was reproduced.
- Boot script target name `mx6dl_sabresd_config` differs from MX6Q configuration/manual part identifiers. Do not infer the shipped SoC solely from that target label; no build was performed to resolve configuration aliases/customization.
- Build timestamps (1.50: 2018-05-14; 1.60: 2019-09-25) differ from release dates in E09; these are different metadata concepts, not contradictory version identities.
- ARM ELF ABI minimum 2.6.31 is not the shipped kernel version.

**UNKNOWN:** exact source-to-binary match, installed toolchain completeness and ability to reproduce any release. GPL collection does not establish availability of the proprietary sampler source, panel application source, all hardware documentation or all original build inputs. Service documentation improves hardware identification but does not close those gaps.

## 12. Reproducible commands

Run from the project root, ``. This section retains the static extraction/inspection workflow: only host utilities/Python are executed by these commands. The separately authorized application-emulation baseline and its native execution permissions are documented in the [runtime runbook] `../experiments/emulation-20261008/README.md#saved-baseline-launch-command--not-executed-during-closing` (evidence not published). Do not rerun extraction/audits merely to resume from unchanged saved evidence.

```sh
# Check saved trees against inputs; regenerate nested expansions/reports.
python3 decode/decode.py --audit

# Rebuild BOTH derived output trees, then audit. Replaces generated output.
python3 decode/decode.py

# Independently identify/hash the original updates.
shasum -a 256 ResearchSourceFiles/TORAIZSP16VER150.UPD ResearchSourceFiles/TORAIZSP16.UPD
file decode/output/image2/decoded.iso decode/output/image2/iso/images/uImage
file decode/output/image2/payloads/pdj/pdj/EP085_Main_R
objdump -p decode/output/image2/payloads/pdj/pdj/EP085_Main_R

# Reproduce the already-established key-handling disassembly; does not read the key.
objdump -d extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/sbin/losetup

# Read archive/filesystem metadata without mounting or executing it.
LC_ALL=C bsdtar -tf decode/output/image2/decoded.iso
unsquashfs -s decode/output/image2/iso/images/bin.sfs
```

Requirements: macOS CommonCrypto at `/usr/lib/libSystem.B.dylib`, Python 3.9+ syntax (tested with 3.10), system bsdtar/objdump, unsquashfs 4.7.5 installed after bsdtar demonstrably could not read SquashFS. No further dependency installation is required for current commands. `--audit` is not read-only: it recreates `nested/` and writes reports. It detects substantive base-tree mismatches but is not a general repair tool. Keep notes/patches outside generated output. No validated repack/flash command exists.

To check every consolidated artifact hash without re-extracting:

```sh
python3 - <<'PY'
import hashlib, json
from pathlib import Path
for r in json.loads(Path('docs/ARTIFACT_INVENTORY.json').read_text())['artifacts']:
    p = Path(r['path']); h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    assert p.stat().st_size == r['bytes'] and h.hexdigest() == r['sha256'], str(p)
print('All recorded artifact hashes match.')
PY
```

Generated report hashes identify the consolidation snapshot; a later legitimate decoder/audit update can change those records. Input hashes must remain stable. Refresh derived inventory provenance when outputs change intentionally.

## 13. Script and tool inventory

| Path / tool | Purpose, input → output | Trust/validation | Limits / disposition |
|---|---|---|---|
| `decode/decode.py` | Two known updates + local key → decoded containers, ISO/payload/nested trees and reports | Active; both samples, full source comparisons, CRCs, inode counts, links and prior repeatability checked | macOS-specific, no repack, fixed two-input scope, limited nested signatures, metadata-only nodes. Never execute extracted content. |
| `experiments/emulation-20261008/probe.py` | Guarded original-application execution with explicit loader/audio/IPC/epoll/TLS options → result JSON and logs | Current measured baseline; original app/libraries unchanged; final bounded trace retained [E25] | Native execution permissions needed; synthetic interfaces, no working display, cooperative scheduling; run only in a newly authorized runtime scope |
| `experiments/emulation-20261008/inspect_elf.py` | ARM ELF addresses → localized instructions, strings and PLT annotations | Saved audio/allocator disassembly corroborates fault events | Offline helper; does not provide a complete feature map |
| `experiments/emulation-20261008/prepare_rootfs.py` | Decoded 1.60 layers → separate guest copy and app-hash manifest | Both working roots compared against source at closing [E26] | Refuses overwrite; directory-relative paths; ignores unit_tests; not a booted Linux root |
| `decode/tmp/consolidation/verify_emulation_handoff.py` | Static harness, traces, manifests, copied roots and runtime metadata → `docs/EMULATION_HANDOFF_VALIDATION.json` | No import of native emulator or guest execution; checks launch options, original bytes, mutable state and process status | Run with existing venv Python; host process-list permission may be required; no stability test |
| Historical `decode/tmp/sample.py`, `full.py` | Earlier sample/full cryptoloop trials | Sole hypothesis succeeded; integrated into decoder | Superseded and removed; no need to recreate them. |
| `decode/tmp/audit-functions.txt` | Temporary staging for audit implementation | Integrated into decoder | Removed; not an alternative implementation. |
| `decode/tmp/consolidation/build_inventory.py` | Local documentation helper → selected hash inventory, snapshot, grouped transformations | Output hashes/paths checked in consolidation validation | Archival helper, not the firmware decoder. Uses explicit selected inputs and existing reports; rerunning can overwrite documentation inventory. |
| `decode/tmp/consolidation/validate_docs.py` | Saved inventory, transformations, Markdown and audits → `docs/VALIDATION.json` | Checks actual file hashes/sizes, local links/anchors, finding/source IDs and local key-material exclusion | Does not rerun firmware extraction or certify inaccessible chat history; run from any directory with Python 3.9+ |
| Original source-archive extractor | Earlier BSP recursive extraction → `extracted/`, extraction-report.json | Report retained with status/omissions | Implementation not located; not claimed reproducible from a retained custom script. Archives remain available for standard-tool inspection. |
| Vendor `bsp_setup*`, `make_*`, `ltib_common.sh`, `ResearchSourceFiles/ltib_patch/*.sh` | Historical source/patch/build/deploy support | Static review only | Not project-created/tested tools; hard-coded paths, deletion and flash/deploy commands. Do not run as a consolidation step. |
| Host file/strings/objdump/bsdtar/unsquashfs | Inspection/extraction | Specific established roles above | Listing a tool here does not claim Ghidra or other tools were used. |

Hash tables and reports, not filenames alone, identify trusted input/output pairs. No key bytes are stored in documentation or tool logs.

## 14. Failed approaches, negatives and hypotheses

### Recorded negative results

| Event | Result and what it establishes | Revisit condition |
|---|---|---|
| Existing bsdtar attempted to list extracted `bin.sfs` | “Unrecognized archive format.” Missing SquashFS support in that tool; not evidence of a bad decode. Installing unsquashfs resolved it. | Only if replacing the extractor/toolchain |
| Initial follow-up path-set audit | Flagged extra `.DS_Store` files. Inspection found no missing firmware entries; audit now explicitly records only those known Finder extras. | Investigate any different extra or missing path; do not broaden exclusions silently |
| Local default Python module probes | Crypto/cryptography/elftools/capstone/pycdlib were absent in the checked interpreters. CommonCrypto via ctypes supplied AES without installing a crypto package. | Environment change or a demonstrated missing analysis capability |
| Source archive and firmware special entries | Host extraction deliberately did not create Linux character devices/FIFOs. Preserved originals and explicit omission lists. | Only for a separately scoped faithful Linux filesystem reconstruction |
| No retained feature map/build/repacker | Startup/audio API traces now exist [E24/E25]; no complete feature map, sampling/sequencing validation, matching build, custom-update acceptance or recovery demonstration exists. | New scoped research, not an assumption of readiness |

**Historical evidence boundary:** the starting brief stated that neither update had yet decoded and legacy losetup key handling was unresolved. The recorded extraction work tested **one** evidence-backed hypothesis and it succeeded. No retained evidence substantiates earlier wrong-key trials, invalid filesystem candidates, failed binwalk runs, entropy measurements or speculative brute-force attempts. Do not invent them or treat “no prior successful decode” as evidence that any specific algorithm was disproved. Source extractor failure logs beyond E19 were not found.

**Runtime failure history:** the [runbook failure table] `../experiments/emulation-20261008/README.md#failed-approaches-fixes-and-retained-evidence` (evidence not published) preserves package/import setup failures, sandbox-sensitive Unicorn SIGILL, library search failure, heap/loader collision, hardware PCM failure, incomplete capture fixture, swallowed timeout, blocked local IPC, invalid panel descriptor and later tcmalloc fault. The final correction supports the TLS explanation; it does not prove physical memory corruption or a vendor allocator bug. Earlier fault baselines are historical, not current blockers.

### Parked hypotheses — none currently under test

| ID / level | Working proposition | Evidence supporting it | What would resolve it |
|---|---|---|---|
| H01 — HYPOTHESIS, parked | Most requested sampler/sequencer/UI feature logic will be in EP085_Main_R or libraries it calls. | Launch chain, size, imports and main-processor role in manual | A selected feature traced to resources/functions and, later if scoped, runtime behavior |
| H02 — HYPOTHESIS, parked | SUB1/PANELCOM1 maps to M1, and SUB2/PANELCOM2 to M2; apl denotes the pdj application update stage. | Naming, two revision files, two S-records, two manual controllers and updater labels | Updater dispatch/write destinations or an independently observed stage-to-controller correspondence |
| H03 — HYPOTHESIS, parked | Supplied platform source/build configuration is close enough to reconstruct relevant shipped kernel/boot behavior. | Matching broad versions/platform plus init/launcher structure | Matching kernel config/initramfs, resolved patches/toolchain and component comparison or reproducible build |


**Resolved H04 buffering observation:** E29 directly identifies the returned CreateWindow request queued in **libxcb**, after Xlib transfers it on unlock. E30 now observes main progressing through allocation/reset initialization; total parent work/completion and progression to later natural display work remain UNKNOWN. No specific panel/calibration dependency is established. See V43/V44.

Previous timing judgments (hours/days for an initial map, days/weeks for one small feature, weeks/months for substantial changes) were untested planning estimates. They are not evidence of feasibility or commitments. Replace them with a feature-specific estimate after a bounded investigation.

## 15. Prioritized open questions

| Priority / level | Question and why it matters | Current evidence | Resolving evidence |
|---|---|---|---|
| P0 — UNKNOWN | How much parent initialization work remains before natural drawable display work? | Main completes allocation then16×64 reset loops on changing objects while CreateWindow stays queued; no persistent causal wait established [E30] | Newly authorize minimal parent-loop count/bound/return tracing around0x50ab98/0x50ab9c and allocation caller; correlate actual completion with natural flush/map under an agreed ceiling; no forced display or panel fixture |
| P1 — UNKNOWN | Which exact modification feature should follow emulator bring-up? | General modification discussion; no selected feature | User-selected behavior and acceptance criteria; do not silently broaden runtime bring-up into feature RE |
| P1 — UNKNOWN | What implements that feature? Determines whether change is a resource/script patch or deeper binary work. | H01, imports, launch scripts | Version-qualified function/resource map with evidence and confidence |
| P1 — UNKNOWN | What exactly do MAIN/apl/SUB1/SUB2 update? Needed for accurate component routing. | V24/V35/V36, H02 | Updater dispatch and write-target mapping; no hardware write required for initial static work |
| P1 — UNKNOWN | Does held source initramfs/config match shipped kernels? Needed to trust boot/recovery conclusions. | V13/V18/V25–V27, H03 | Extraction/comparison of each kernel's embedded boot material and source configuration |
| P1 — UNKNOWN | Which checks govern full update acceptance/authenticity? Needed before a repacker can be considered sufficient. | Wrapper CRC and decrypt path established | Complete updater verification flow and unchanged-container repack validation; hardware acceptance remains separate |
| P2 — UNKNOWN | How do audio/MIDI/UI/panel subsystems communicate and meet timing requirements? Needed for feature safety/correctness. | Libraries, modules and documented controller roles | Scoped call/protocol mapping, later observations if authorized |
| P2 — UNKNOWN | What are actual RAM/storage geometry, live boot settings and debug access on the user's device? | Manual parts and shipped configuration only | Relevant datasheets and non-destructive observations/dumps within an explicitly changed scope |
| P2 — UNKNOWN | Is there a tested backup/recovery path, and does A/B selection provide usable rollback? | Two banks declared, no recovery test | Documented and demonstrated recovery in a separately authorized hardware phase |
| P2 — UNKNOWN | Is the decoder key universal across units/releases? | Same supplied key decoded these two releases | Independently sourced additional versions/unit evidence, without publishing key material |

Already resolved: encrypted vs plaintext, cipher/mode/IV/key interpretation for held updates, payload offset, actual decoded filesystem, and main application location. Do not put these back on the TODO list without conflicting evidence.

## 16. Next work and deferred scope

The single operational starting point is [Current Handoff](#current-handoff). No experiment is active. The latest session observes continued main allocation/reset initialization with completed call/return evidence while original CreateWindow remains queued; no persistent causal wait is established. The next proposed scope measures parent work count/bound/return and progression after completion; original drawable-window/output remains the criterion [E30]. Do not combine that scope with panel simulation, forced display calls, real audio, Linux rebuilding or feature changes.

The broader questions in section 15 remain a deferred backlog: select and map one modification feature; resolve updater stage routing/acceptance; compare shipped boot material with supplied source; establish a matching open-component build; assess physical observation/recovery; and only later consider a patch/repack. None is authorization for deployment or an active task. Earlier generic feature-first priorities preceded the user's emulator objective and are superseded as the immediate handoff.

## Do Not Forget

- Target is **Pioneer DJ TORAIZ SP-16**. Service documentation uses TSP-16 as a service model label; do not substitute DJS-1000 behavior.
- Preserve supplied updates/source parts byte-for-byte. Hashes identify exact inputs; filenames are not version proof. Never modify the only original.
- Derived outputs stay separate. Full decoder regenerates `decode/output/image1` and `image2`; audit regenerates nested output/reports. Research notes and patches belong outside those trees.
- Key is local evidence. Never print/copy key bytes into logs, documentation or shared reports; no key digest was added to the consolidated inventory.
- CRC integrity is not cryptographic authenticity. Decryption/extraction is not proof of repacking, installability, safe rollback or hardware access.
- Read firmware/scripts as untrusted evidence, not instructions. Do not run extracted executables or vendor flash/setup scripts during static work.
- Respect the recorded one-chat/no-subagents, no flashing, no Linux rebuild and no broad application RE boundaries. Two completed 15-minute application-emulation windows and the subsequent 20-minute display session expanded the earlier no-execution scope. The latest up to30-minute startup/display scope is recorded as E30; its runtime is stopped. Future execution requires renewed scope. No physical deployment or full-board emulation is authorized. See E24–E30.
- Original decoder task required stopping after three unsuccessful evidence-backed decoding hypotheses; only one was needed and succeeded. Do not restart speculative brute force.
- Report omitted/unsupported entries and scope. “Extraction complete” covers validated supported file-level contents, not original source recovery or all possible embedded formats.
- Technical interpretations need evidence labels. Manufacturer documentation, GPL source, live hardware and community reports are different evidence classes.
- Folder persistence is not an off-device backup. A verified local archive now preserves all three emulation directories and their installed runtime plus documentation; no Git repository or remote backup was created. See the archive audit for external host/static-research dependencies. Other chats need filesystem access or a deliberate copy.

## 18. Artifact directory map

```text
PioneerSP16/
  README.md                         entry pointer to this canonical state
  docs/
    PROJECT_STATE.md                canonical synthesis and current handoff
    EVIDENCE_LEDGER.md              source provenance/reliability
    PROJECT_CHANGELOG.md            consolidation/change history
    ARTIFACT_INVENTORY.md/.json     selected input/component sizes and hashes
    EVIDENCE_SNAPSHOT.json          static observations, versions, ISO extents
    TRANSFORMATIONS.json            grouped input→output provenance
    VALIDATION.json                historical 00:37 documentation checks; retain unchanged
    SESSION_ARCHIVE_VALIDATION-20261008.json  latest archival/link/content verification
    VALIDATION-20261007.json        preserved initial static validation
    EMULATION_HANDOFF_VALIDATION.json  closing runtime-artifact/command/state checks
  experiments/
    emulation-20261007/             historical first startup probe; shared tools/venv
    emulation-display-20261008-004011/  display session, all attempts, partial logs, archive audit
    session-archive-20261008-010249/  prior private verified snapshot; preserve unchanged
    emulation-display-20261008-011849/  cookie/flag correction, original API progress, partial logs
    session-archive-20261008-011849/  prior private display snapshot; unchanged
    emulation-display-20261008-101605/  binary buffer diagnosis, complete native results
    session-archive-20261008-101605/  latest private archive and external verification
    emulation-20261008/             current measured baseline, probe/config/fixtures
      README.md                    runtime runbook; links to single Current Handoff
      rootfs/                      mutable copied guest files, never original evidence
      *-result.json / logs/        preserved intermediate/final traces and disassembly
      verification.json            historical experiment snapshot; retain unchanged
  ResearchSourceFiles/              supplied UPDs, PDFs, notices, source archives/parts
    extraction-report.json         historical recursive source extraction index
    ltib_patch/                    supplied patches/scripts; not project decoder
  extracted/                       expanded source/BSP bundles and supplied initramfs
  copyright/                       per-package HTML copyright/source metadata
  decode/
    decode.py                      sole active decoder/extractor/auditor
    README.md / STATUS.md          extraction navigation and short status
    FINDINGS.md / PROCESS.md        earlier assessment/process history
    output/image1/                 validated firmware 1.50
    output/image2/                 validated firmware 1.60
      decoded.iso / iso/ / payloads/ / nested/ / reports and manifests
    tmp/                           disassemblies, logs, temporary experiments
      consolidation/               PDF text/renders, validation helper, fresh audit log
```

Layout retained. Do not relocate large source/output trees just to normalize names. `docs/` is the canonical knowledge layer; `decode/` remains the extraction implementation. Important source claims link to preserved originals, so temporary PDF renders/text need not be permanent dependencies.

## 19. Consolidation validation and corrected claims

[VALIDATION.json] `VALIDATION.json` (evidence not published) records historical 00:37 documentation checks: hashes, local links/anchors, finding IDs and key-material exclusion. [EMULATION_HANDOFF_VALIDATION.json] `EMULATION_HANDOFF_VALIDATION.json` (evidence not published) records runtime versions/paths, historical trace integrity, original/copy ELF identity, copied-root state, saved command compatibility and the closing process check. The initial static result is preserved as [VALIDATION-20261007.json] `VALIDATION-20261007.json` (evidence not published). A fresh decoder audit passed both images **during the October 7 initial consolidation**, logged in `decode/tmp/consolidation/latest-audit.log`; this closing pass reads that saved audit and does not rerun it. [E02/E03/E26]

Latest display-session checks are [new session validation] `../experiments/session-archive-20261008-101605/session-validation.json` (evidence not published), with separate [new archive verification] `../experiments/session-archive-20261008-101605/archive-verification.json` (evidence not published). Prior E28 checks remain [preserved] `../experiments/session-archive-20261008-011849/session-validation.json` (evidence not published). The previous archive checks remain preserved as [SESSION_ARCHIVE_VALIDATION-20261008.json] `SESSION_ARCHIVE_VALIDATION-20261008.json` (evidence not published); the reusable read-only checker and exact command are in the [archive audit] `../experiments/emulation-display-20261008-004011/archive-audit/ARCHIVE_AUDIT.md` (evidence not published). The earlier consolidation checkers have historical assumptions (including 26 sources, before E27) and overwrite their old reports. Preserve those reports and use the new checker for the current session; do not interpret an old passed snapshot as current validation.

Corrections captured rather than hidden:

- “Everything extracted” now explicitly means supported file-level contents, with five special entries per image retained as metadata and binary interiors outside scope.
- A passing signature-named checker is documented as marker/CRC verification; absence of other authentication is not claimed.
- Package versions, build dates, release dates and ELF ABI tags are distinct fields.
- Supplied source boot scripts are not silently treated as the exact initramfs inside either shipped kernel.
- M1/M2 identities are now service-manual-backed; exact SUB/update-payload routing is still not proven.
- Old estimates remain provisional judgments, not measured work or a promise of feature feasibility.
- Historic source extraction omissions are distinct from decoded firmware extraction omissions.
- No DJS-1000 community claim has been imported without a retained source.

## Historical Handoff — closing at 00:37 on October 8, 2026

**Historical snapshot from the 00:37 closing pass on October 8, 2026.** The bullets below preserve that earlier handoff; the following Current Handoff supersedes its next action.

- **Authorized work completed:** two 15-minute original-application emulation investigations, then documentation-only consolidation. No experiment is active or left running at the closing process check [E26]. Resume by reading, not by launching another probe automatically.
- **Latest verified baseline:** original firmware **1.60** app SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`; Qiling 1.4.6 / Unicorn 2.1.4 on macOS 14.8.9 ARM64 / Python 3.10.1; final second-session `probe.py` with library aliases, high loader, null audio, startup/affinity tracing, nonblocking local IPC, limited epoll, fast mode and corrected ARM TLS. The [final result] `../experiments/emulation-20261008/corrected-tls-result.json` (evidence not published) ran **76.216 seconds**, deadline-stopped, with **zero recorded guest memory faults**, 17 threads, 16,911 output-write calls and 5,635 / 5,633 capture-read calls; initially sampled transfers returned 64 frames. [V38–V40, E25]
- **What this means:** the original application and original ALSA library run through synthetic duplex audio startup and later project/audio-worker creation. Core 0–3 masks are application requests; the handler returns ENOSYS, so actual CPU utilization and complete DSP responsibilities remain unknown. A deadline stop is not clean shutdown or long-term stability. No playable instrument, physical sound, complete board boot or SP-16/MPC2500 benchmark is established.
- **Current obstacles:** XOpenDisplay returns null with general connection operations still denied; no original window/frame is recorded. SPI/panel/GPIO interfaces and per-device calibration/storage remain absent. The earlier tcmalloc fault is not observed in the corrected bounded run; TLS mismatch is a strongly supported explanation, not proof of indefinite stability.
- **Read next:** the [runtime runbook] `../experiments/emulation-20261008/README.md` (evidence not published), especially its [baseline options] `../experiments/emulation-20261008/README.md#baseline-corrections-and-substitutes` (evidence not published) and [saved launch command] `../experiments/emulation-20261008/README.md#saved-baseline-launch-command--not-executed-during-closing` (evidence not published); then the [session summary] `../experiments/emulation-20261008/session-summary.json` (evidence not published), final result above, and [closing validation] `EMULATION_HANDOFF_VALIDATION.json` (evidence not published). E24 documents historical setup/startup failures; E25 is the runtime baseline; E26 validates this closing handoff.
- **Starting command for a future authorized replay:** use the runbook's exact venv command with **all baseline options**, `--seconds 75`, an unused label and native execution permissions outside the restricted sandbox. The current `--linux-brk-failure` diagnostic is deliberately **off**. Keep original evidence and saved logs intact; root copies and audio fixture files may be changed by a new run. Closing comparison found 12,840 source entries identical in each root and no extra file/symlink entries, but subsequent runs require checking that state again.
- **Smallest useful next experiment, proposed only:** retain the entire corrected baseline and add a narrowly scoped local virtual-display connection, leaving panel modeling for later. Ask one question: **does the unchanged application open the display and create its first original window?** Within a fixed runtime budget, save XOpenDisplay's return, XCreateWindow events and a captured original window/frame. **Success:** non-null display plus original window creation and captured output; **otherwise:** record the first new failure with its return value/PC/trace. If no display endpoint is already available, preparing that prerequisite is a separate scoped step, not a reason to install/rebuild broadly or bypass all socket guards. No display connection or server was added in this closing pass.
- **Avoid duplicated work:** do not repeat decryption, extraction, dependency discovery, hardware-PCM failure, the default loader collision or blocked-IPC approach without a changed condition. Preserve the TLS correction and all measured fixtures; consult the runbook's failure table before changing them. No firmware/application/library bytes or emulator harness were changed during closing; documentation/check helpers and a preserved copy of the user crash report are the closing artifacts.

## Historical Handoff — after the 00:40–01:00 display session

**Single current handoff, October 8, 2026, after the 00:40–01:00 CDT display session.** [E27]

- **Achieved:** milestone 1, authenticated local X11 setup on contained Xvfb :16. **Not achieved:** XOpenDisplay non-null (actual return 0) or any original XCreateWindow/captured window. Socket connect itself returned zero.
- **Precise blocker:** access(/root/display.xauth, R_OK) returned -1/EPERM because Qiling access checks the actual rootfs path, while the cookie was supplied through fs_mapper only. A 12-byte unauthenticated setup reached the server, which rejected it. One targeted getpeername/getsockname translation correction was tested; no third probe was run.
- **Evidence:** [experiment report] `../experiments/emulation-display-20261008-004011/README.md` (evidence not published), [partial retry summary] `../experiments/emulation-display-20261008-004011/partial-summary.json` (evidence not published), [complete first failed result] `../experiments/emulation-display-20261008-004011/display-01-result.json` (evidence not published), [integrity validation] `../experiments/emulation-display-20261008-004011/integrity-validation.json` (evidence not published), [closing validation] `../experiments/emulation-display-20261008-004011/closing-validation.json` (evidence not published). Console/Qiling logs and zero-child window queries are linked in the report. No original window image exists.
- **Baseline preserved:** original 1.60 app/library bytes and the earlier measured harness remain intact: 76.216-second corrected-TLS run, 17 guest threads, zero recorded guest faults, synthetic duplex audio. Keep library aliases, high loader, null audio, startup/affinity tracing, nonblocking local IPC, limited epoll, fast mode and corrected ARM TLS; failed-brk diagnostic off. Existing Python 3.10.1/Qiling 1.4.6/Unicorn 2.1.4 venv and approved native execution remain required. [E25/E26]
- **New retry limitation:** alarm fired at 76.002404 seconds but worker exception did not terminate all threads. SIGTERM/exit 143 stopped the retry before the session's 17-minute experiment cutoff; no final native JSON. Partial trace has seven zero PCM-open returns, sampled 64-frame transfers, original thread set and later AudioEditor at 79.638589 seconds (18 including main, last PROBE at 79.664204 seconds), early corrected-TLS mismatch events and no recorded invalid_memory. Final counters and total native runtime are unknown. Do not call this another successful bounded baseline.
- **Process/mutable state:** all experimental processes stopped and checked. No experiment active. Root copied entries and 26 dependency ELF objects match saved originals; original measured evidence is unchanged. Downloaded verified XQuartz package and disposable portable display copies remain in the new experiment; no system-wide installation. Private cookie retained mode 0600. The user-created root-owned empty /private/tmp/.X11-unix remains; private compiler wrapper removed at closing. The past-dated display supervisor must receive a new deadline in a future session.
- **Smallest next experiment, proposed:** in a new complete working copy, place the experiment-only cookie at the real root/display.xauth path (0600) or correct access narrowly; verify guest access=0 and authenticated X11 setup. Add an independent host process timeout around 78 seconds. Then retain the measurable success criterion: XOpenDisplay non-null, original XCreateWindow, server-visible window and captured original output. A fresh label is mandatory; the saved launch is historical and would reproduce the known authentication failure.
- **Roadmap:** resume that authentication blocker first. Only after original window creation propose actual panel-driver identification and one observable UI response, then one sampling/sequencing behavior; real audio/timing later. No later stage was executed. Requested affinity is not utilization, null audio is synthetic, bounded execution is not long-term stability, and display creation is not complete SP-16 emulation.

**Archival follow-up:** [local archive and restoration index] `../experiments/session-archive-20261008-010249/README.md` (evidence not published), [ordered attempt history] `../experiments/emulation-display-20261008-004011/attempt-history.json` (evidence not published), [latest archive validation] `SESSION_ARCHIVE_VALIDATION-20261008.json` (evidence not published). Rootfs-copy provenance, the exact original request, temporary documentation helper, all earlier emulation directories and the installed venv are preserved. Experiments stopped within the runtime cutoff; initial closing documentation finished 34.682 seconds after the overall deadline, recorded explicitly. This follow-up ran no guest or display experiment.


## Historical Handoff — after the 01:18:49 display session

**Single current handoff — October 8, 2026, 01:18:49–01:48:49 CDT authorized display/preservation session.** [E28]

- **Achieved:** milestone 2. Guest access(/root/display.xauth, R_OK)=0; authenticated setup status=1. Original XOpenDisplay returned **0x17de000** at 1.537011 s. Original XCreateWindow returned **0x200001** at 1.537812 s. **Milestone 3 remains unachieved:** all server-root trees show zero children; only black server-root pixels were captured. No original UI/window output or working instrument is established.
- **Precise remaining observation/blocker:** no display fd-5 write after XCreateWindow and no sampled XFlush/XSync/XMapWindow call before independent termination. The returned ID never appears in server-root queries. H04 (buffered request / startup waiting before flush) is a hypothesis; no buffer snapshot proves it. Missing panel/calibration interfaces are logged, with causal role unknown. Do not disable authentication, broaden socket permissions or simulate panel behavior to bypass this gap.
- **Evidence:** [experiment report] `../experiments/emulation-display-20261008-011849/README.md` (evidence not published), [summary] `../experiments/emulation-display-20261008-011849/session-summary.json` (evidence not published), [retry console] `../experiments/emulation-display-20261008-011849/logs/auth-nonblock-03-console.log` (evidence not published), [host supervision] `../experiments/emulation-display-20261008-011849/auth-nonblock-03-supervision.json` (evidence not published), [integrity] `../experiments/emulation-display-20261008-011849/integrity-verification.json` (evidence not published), [process state] `../experiments/emulation-display-20261008-011849/process-state.json` (evidence not published). Partial logs are evidence; native auth-nonblock-03-result.json never existed. First guest's complete native JSON and failed server-only preparation are retained in the report.
- **Resolved and retained:** same current server cookie placed in actual guest root root/display.xauth, both copies mode 0600; mapped open/XAUTHORITY consistent. Display-only fcntl64 translates guest nonblocking semantics without passing Linux flags to Darwin; local reproducer and retry confirm the correction. Tested display-only getpeername/getsockname translation remains. The private helper belongs at /private/tmp/p16008x/xkbcomp, directly under that directory, not under bin. Fresh labels/cookie/server deadlines are mandatory in a new complete copy.
- **Baseline/integrity:** original 1.60 app and 26 selected ELFs, both supplied UPDs, old measured harness/results and 67,729 old manifest records match. New root has the same 12,840 original file/symlink entries plus only root/display.xauth. Keep library aliases, high loader, synthetic duplex audio, startup/affinity tracing, nonblocking IPC, limited epoll, fast mode and corrected ARM TLS; failed-brk diagnostic off. Python 3.10.1/Qiling 1.4.6/Unicorn 2.1.4 existing venv and approved native execution remain required. The original completed 76.216-second baseline is preserved [E25].
- **Retry limits:** 17 threads including main, seven sampled successful PCM opens and early 64-frame transfers, no recorded invalid_memory in partial logs. Worker alarm at 76.004691 s did not stop every worker. Independent host supervisor SIGTERM stopped and reaped exact guest at **78.013921 s**, exit -15; no SIGKILL needed. Native final counts/PC are unknown. This is not another completed native baseline or long-term stability demonstration.
- **Process/mutable state:** all recorded guest/server/supervisor PIDs stopped; runtime finished at **01:26:40.327 CDT**, before the minute-25 cutoff. X16 socket/lock and private helper are absent; TCP 6016 has no listener. Root-owned mode1777 shared socket directory remains empty. Current cookie retained privately; new empty guest storage directories are documented. Original/historical inputs and prior archive remain unchanged.
- **Archive/restoration:** [new private archive index] `../experiments/session-archive-20261008-011849/README.md` (evidence not published), [external verification] `../experiments/session-archive-20261008-011849/archive-verification.json` (evidence not published), [manifest] `../experiments/session-archive-20261008-011849/archive-manifest.json` (evidence not published), [checksum] `../experiments/session-archive-20261008-011849/archive.sha256` (evidence not published). Read the external verification report for actual build/verification status. It preserves the complete new experiment and updated handoff/history; installed venv/older history are restored from the unchanged prior archive, SHA-256 **b5707e6a30bd0ea3897ded8fd5551528b4a024958c70e4858e539a4e8e661cd8**. Same disk only; base macOS/Python framework and broad original static inputs remain external. External session-close report records final time/status; no archived member is edited after freezing.
- **Smallest next experiment, proposed only:** renew scope for a new complete bounded copy retaining cookie/nonblocking fixes and independent 78-second supervision. Save a **read-only original Display request-buffer snapshot at XCreateWindow return and near stop**, trace actual original-library flush/map entry and fd-5 writes. Measure whether CreateWindow remains queued or reaches the server. Success is an identifiable pending request/no flush, or server acknowledgement/tree evidence and captured original output; otherwise record the first counterexample/PC. Do not force mapping, inject panel input or silently extend runtime. [Latest ready-to-submit session prompt] `NEXT_SESSION_PROMPT-20261008-095741.txt` (evidence not published); [earlier session brief] `NEXT_SESSION_PROMPT-20261008-011849.txt` (evidence not published).
- **Roadmap and boundaries:** original server-visible window/output must precede actual panel-driver identification and one observable UI response; sampling/sequencing and real audio/timing follow later. No later stage executed. Requested affinity is not utilization; null audio is synthetic; bounded execution is not long-term stability; display creation is not complete SP-16 emulation.

## Historical handoff — October8, 2026, 10:16:05 CDT

**Historical E29 handoff; superseded by the single Current Handoff below.** [E29]

- **Achieved:** diagnostic success, highest completed milestone 2. Original XOpenDisplay=0x17de000, XCreateWindow=0x200001. **Milestone3 remains unachieved:** no server child or original UI capture. Captures are black server-root images.
- **Verified request path:** 36-byte opcode1/length9 CreateWindow at original pre-unlock at 1.628663s; original return instruction at 1.629064s transfers those identical bytes from Xlib to libxcb. At 73.002816s, deadline 76.002856s and final 76.010376s the libxcb request remains unchanged, request 7/written 6/error 0. No subsequent tracked fd5 write/writev or hooked real-library entry (flush/map/send included). Request0x200001 is 1×1 class 2 **InputOnly**; it cannot carry drawable UI pixels. **Classification: queued/unflushed**, server acceptance/rejection untested. H04's buffer observation is resolved; natural startup wait cause remains UNKNOWN.
- **Read first:** [report] `../experiments/emulation-display-20261008-101605/README.md` (evidence not published), [summary] `../experiments/emulation-display-20261008-101605/session-summary.json` (evidence not published), [binary offsets/addresses] `../experiments/emulation-display-20261008-101605/xlib-layout.json` (evidence not published), [retry native result] `../experiments/emulation-display-20261008-101605/buffer-natural-02-result.json` (evidence not published), [supervision] `../experiments/emulation-display-20261008-101605/buffer-natural-02-supervision.json` (evidence not published), [instrumentation correction] `../experiments/emulation-display-20261008-101605/targeted-correction.json` (evidence not published). Complete native results exist for both probes. First return snapshot was skipped by the mutable Qiling hook-list collision; exact first diagnostic/layout source and logs are preserved. Only one targeted retry occurred; installed Qiling was unchanged.
- **Derived rather than guessed:** Display fields are fd+8/request+0x60/buffer+0x68/bufptr+0x6c/bufmax+0x70/XCB-private+0x538; private+8 is XCB connection; libxcb output+0x1104, length+0x2104, request+0x2108, written+0x210c. Saved shipped ARM instructions support every field; live ELF base/entry bytes/buffer bounds/descriptor ownership were checked. Actual-library checkpoints replace competing one-shot return hooks. Retain both-buffer observations; an empty Display buffer alone does not establish that a request was sent.
- **Baseline retained:** all E25 options plus authenticated scoped Unix-only guest X0→host X16; current cookie actual-root/mapped copies mode 0600; display-only nonblocking/name translation; independent 78-second supervisor with TERM/KILL fallback and absolute cutoff. No forced flush/map, input injection or firmware/library patch. Both guests native-bounded-stopped near 76s, then host reaped without signals; server supervisors were terminated/reaped. First trace observed 15 total guest threads; retry 7; 17-thread baseline remains historical. Seven sampled PCM-open successes and zero recorded memory faults in each; these are instrumented display observations, not stability/performance validation.
- **Integrity/process:** [verification] `../experiments/emulation-display-20261008-101605/integrity-verification.json` (evidence not published) passes 12,841 root entries except intentional fresh cookie bytes, 26 original ELFs, both UPDs, 101,912 historical records and both prior archives. [Process check] `../experiments/emulation-display-20261008-101605/process-state.json` (evidence not published) confirms all eight recorded PIDs gone/reaped, X16 socket/lock absent, TCP 6016 unused, helper removed and root-owned mode 1777 shared directory empty. Runtime stopped **10:25:58.540 CDT**, before cutoff. Mutable fixtures/empty directories and code/config deltas are saved separately.
- **Archive/restoration:** [new private archive index] `../experiments/session-archive-20261008-101605/README.md` (evidence not published), [external verification] `../experiments/session-archive-20261008-101605/archive-verification.json` (evidence not published), [member manifest] `../experiments/session-archive-20261008-101605/archive-manifest.json` (evidence not published), [checksum] `../experiments/session-archive-20261008-101605/archive.sha256` (evidence not published), [actual closing time] `../experiments/session-archive-20261008-101605/session-close.json` (evidence not published). Frozen archive holds complete experiment plus documentation/history. Outer digest and full content/link/mode checks are outside it to avoid self-reference. E28 archive remains 93cb663dabb1aefe04751e148716d5309380446cc38af9281b4c9c6292315346; installed runtime/older history archive remains b5707e6a30bd0ea3897ded8fd5551528b4a024958c70e4858e539a4e8e661cd8. Base macOS/Python and broad static trees remain external; same-disk only, no restored runtime/off-device backup established.
- **Latest continuation prompt:** [30-minute startup/display session] `NEXT_SESSION_PROMPT-20261008-105321.txt` (evidence not published). It supersedes the earlier buffer-only prompt. This documentation-only preparation postdates the frozen E29 archive; its before/after docs and prompt are preserved separately in experiments/handoff-preparation-20261008-105321. The prompt becomes execution scope when submitted by the user to a new chat; writing it launches no runtime.
- **Smallest next experiment, proposed only:** newly authorize read-only main-thread control-flow/wait tracing immediately after original return PC 0x6980f4 until first blocking/waiting condition; correlate it with pending libxcb bytes. Retry native deadline sampled main PC 0x350064 / LR 0x354658, which does not by itself identify the causal wait. Do not assume missing panel/calibration is responsible or repeat the obsolete buffer-only prompt. No further runtime is authorized by this closed session or its saved launch.
- **Roadmap:** natural drawable original window/output precedes separately authorized panel-driver/input response, then sampling/sequencing and real audio/timing. None executed. Null audio is synthetic; affinity is requested placement, not utilization; bounded runtime is not stability; an InputOnly request or display API return is not complete emulation.


## Current Handoff

For current work, use [the live status] `../README.md` (evidence not published) and [latest experiment handoff] `../experiments/post-parent-startup-20261008-150354/HANDOFF.md` (evidence not published). Parent/constructor completion is established by the later run; the remaining question is downstream startup and drawable UI. The snapshot below is retained as history.

### Historical handoff — 10:59 session

**Single current handoff — October8, 2026, 10:59:16 CDT bounded startup/display/preservation session.** [E30]

- **Achieved:** diagnostic success; highest milestone2. Runtime main2000 returned from original CreateWindow0x200001 at1.696321s, through cleanup0x698100 and saved/observed caller0x698500. **Milestone3 remains unachieved:** zero server children; black server-root captures, no original UI.
- **Direct progression:** original data initializer0x350010 returns to allocation0x353c80; capped records show at least270,337 element returns by58.506704s and495 whole allocation returns0x353d04 by60.070817s. Distinct reset phase0x354604 starts60.365249s, LR0x50ab9c; changing object headers specify16×64, stride0x98. Actual0x354658 return,0x354674 loop completion(indices16/64) and0x3546d4 function return recur; at least75 completed functions by76.467846s. **VERIFIED continued initialization**, not a persistent causal wait. Counters are recorded lower bounds, not final totals. Parent work bound/completion and time to natural drawable display remain UNKNOWN; missing hardware causality is unproved.
- **Read first:** [report] `../experiments/emulation-startup-20261008-105916/README.md` (evidence not published), [summary] `../experiments/emulation-startup-20261008-105916/session-summary.json` (evidence not published), [original-byte analysis] `../experiments/emulation-startup-20261008-105916/startup-binary-analysis.json` (evidence not published), [read-only tracing] `../experiments/emulation-startup-20261008-105916/startup_trace.py` (evidence not published), [partial console-derived events] `../experiments/emulation-startup-20261008-105916/startup-natural-01-events-from-console.json` (evidence not published), [host supervision] `../experiments/emulation-startup-20261008-105916/startup-natural-01-supervision.json` (evidence not published).
- **Display correlation:** both-buffer snapshots through76.467894s retain identical36-byte CreateWindow, sequence7/written6/error0; Display buffer empty. No later traced library/display writes/flush/map/send; all17 tree queries zero children. Initial1×1 class2 InputOnly cannot carry drawable pixels. E29's full binary-derived Xlib/XCB layout and library checkpoints remain unchanged.
- **Exact scope and stop:** ONE new complete copied supervised probe; no correction/retry, installs, original patches, bypass, input or forced display calls. All baseline flags plus main-filtered18 permanent byte-validated checkpoints/selected syscall ENTER/EXIT retained, fast mode, seconds75, failed-brk off. Current scoped cookie actual-root/mapped copies equal0600, guest access0/setup1. Unix-only X0→X16, nonblocking/name correction, independent78s supervision and current absolute cutoff retained. **Native final JSON absent:** worker alarm76.023029s did not stop main; main checkpoints continued. Host SIGTERM/reap78.013007s, server reapedexit0. Preserve actual partial evidence; final PC/counters/outcome unknown. No defect explaining absent UI justifies retry. Handler ENTER/EXIT durations exclude deferred guest scheduling.
- **Preservation:** [integrity] `../experiments/emulation-startup-20261008-105916/integrity-verification.json` (evidence not published) passes12,841 root file/link entries except intentional fresh cookie,26 original ELFs,both UPDs,136,116 historical records and allthree dependency archives. [Process check] `../experiments/emulation-startup-20261008-105916/process-state.json` (evidence not published): allfour recordedPIDs gone/reaped, X16socket/lock absent,TCP6016 unused,private helper removed,shared directory root1777 empty. Runtime stopped11:04:56.796CDT, before cutoff. [Code/config/mutable state] `../experiments/emulation-startup-20261008-105916/preservation-details.json` (evidence not published) and exact history-before docs retained.
- **Archive:** [new private index] `../experiments/session-archive-20261008-105916/README.md` (evidence not published), [external full verification] `../experiments/session-archive-20261008-105916/archive-verification.json` (evidence not published), [member manifest] `../experiments/session-archive-20261008-105916/archive-manifest.json` (evidence not published), [outer checksum] `../experiments/session-archive-20261008-105916/archive.sha256` (evidence not published), [actual close] `../experiments/session-archive-20261008-105916/session-close.json` (evidence not published). Freeze complete useful new experiment and updated docs; reports remain outside archive to avoid self-reference. Exact unchanged dependency archives: E29 cf5bc9537dfe58c801aef1d7703cd18623d0ae21f8cef87507a2a9ede7129436; E28 93cb663dabb1aefe04751e148716d5309380446cc38af9281b4c9c6292315346; runtime/history b5707e6a30bd0ea3897ded8fd5551528b4a024958c70e4858e539a4e8e661cd8. Same-disk only; macOS/base Python/static originals external; restored/relocated execution and off-device backup not established.
- **Smallest next experiment, proposed only:** newly authorize minimal parent work count/bound/actual return around original0x50ab98/0x50ab9c and allocation caller chain. Measure remaining work and whether natural flush/map follows completion under an explicitly agreed observation ceiling. Do not assume panel/calibration causality, introduce panel/input fixtures or force display calls. This completed session provides no standing replay permission.
- **Roadmap:** original server-visible drawable output precedes separately authorized panel-driver/input response, sampling/sequencing and real audio/timing. None executed. Null audio is synthetic, requested affinity is not utilization, bounded tracing is not stability/performance validation or complete emulation.


## October 8, 2026 — current offline correction following independent review

This dated correction governs the interpretation of the preceding Current Handoff and V45 without rewriting that historical text. The direct user's submitted offline request supersedes expired runtime prompts as current authority. Only new offline validation/documentation and a draft next experiment were authorized here. No original app, Qiling/Unicorn engine, Xvfb, guest, vendor build/deployment/updater, package installation, historical runtime patch, firmware repack, hardware action, shared-endpoint change or publication occurred.

The [independent review] `<Review/INDEPENDENT_TECHNICAL_REVIEW-2026-10-08.md>` (evidence not published) is addressed in [new check artifacts and current correction] `../experiments/offline-review-20261008-01/CURRENT_CORRECTION.md` (evidence not published), with [command/code/input records] `../experiments/offline-review-20261008-01/README.md` (evidence not published). These are newly executed offline checks of earlier retained evidence, not a runtime rerun.

- **F01/F04:** [new evidence verifier] `../experiments/offline-review-20261008-01/trace/README.md` (evidence not published) requires identified version/input/code, raw ordered allocation/reset checkpoints, runtime-main ownership, nonempty server/capture evidence and actual caller continuation for completed-call wording. Frozen E30 retains supported continued main-thread initialization with partial console-derived data and no native final JSON. Required omission/wrong-thread/empty-evidence controls and the review's minimal false-positive dataset fail; contradiction and completion-overclaim controls are retained. 0x353d04 and 0x3546d4 hooks run before pop {...,pc}: the recorded lower bounds 495 and 75 mean **return-instruction checkpoint visits**. The 75th reset visit at 76.467846s is not an independently observed 75th caller return. Original element post-BL checkpoints and changing-object/loop evidence still support broader progression; all historical counters/traces remain unchanged. The new console/JSON comparison counts 1,128 PROBE events for the cited frozen bytes; the review's 1,129 prose count is a narrow census discrepancy, not changed trace evidence.
- **F02:** [source-mode report] `../experiments/offline-review-20261008-01/modes/README.md` (evidence not published) finds 60 tar-directory differences, including two sticky and two setgid losses, plus six bin and five BDF regular-file differences per release. image2 rootfs4 ./tmp is 01777→0755 at decompressed header 1201664, ./var/tmp 0777→0755 at4608, ./var/ftp/pub 02777→0755 at6656. All 1,430 compared symlink targets match; platform-specific symlink mode semantics are separate. Readable bytes/targets remain supported; Linux boot/repack must use original container metadata, not host stat or repeated same-host extraction. No baseline chmod/regeneration occurred.
- **F03/F05:** [copied fake/offline tests] `../experiments/offline-review-20261008-01/clock-guards/README.md` (evidence not published) reproduce the held clock units/source/invalid-ID defects and gettimeofday's separate correct microsecond contract. At1700000000.5 the held timespec fields are (1700000000,500000), while required REALTIME fields are (1700000000,500000000). A narrow offline proposal passes controlled contracts and was never installed. Endpoint negatives place the same fake socket in fixture.descriptors[3] and guest fd3, reach the intended guard and make no fake connect; exact allowed endpoint positive passes. Deliberately breaking the endpoint predicate makes relevant negative tests fail. These fake checks do not prove native containment or UI causality.
- **F06:** [outcome layers] `../experiments/offline-review-20261008-01/outcome-layers.json` (evidence not published) preserve null-duplex returned/exit0 alongside the worker TimeoutError. Host exit, worker failure, reported ql.run result and clean guest termination remain distinct. E30 host SIGTERM/reap at78.013007s does not supply a missing guest/native-final result. No historical runner or JSON was reconstructed.

The [smallest parent-initialization experiment draft] `../experiments/offline-review-20261008-01/PARENT_INITIALIZATION_DRAFT.md` (evidence not published) measures actual work/bounds and correlates0x50ab98 with actual caller observation0x50ab9c, then observes natural flush/map/drawable behavior within a proposed180-second window and185-second owned-process hard stop. It distinguishes callee return into the parent from the whole parent's return. Its bounds require separately submitted runtime authorization; this document launches nothing and permits no forced display/panel/calibration behavior.

The [architecture/deployment gate list] `../experiments/offline-review-20261008-01/ARCHITECTURE_DEPLOYMENT_GATES.md` (evidence not published) keeps concrete feature selection, exact release build/source correspondence, proprietary components/interfaces, original metadata packaging, updater acceptance/routing, affected storage and tested recovery unresolved. No example has become a requirement; original drawable UI, full platform boot, physical operation, feature validation and replacement-OS deployment remain unestablished. Before/after evidence census and exact pre-edit document copies are in the new validation directory; historical artifacts and dated handoffs remain preserved.


## October 8, 2026 — latest next-chat prompt preparation

Latest ready-to-submit prompt: [parent initialization and durable handoff] `NEXT_SESSION_PROMPT-20261008-PARENT-INITIALIZATION.txt` (evidence not published), with [standalone takeover context] `../experiments/parent-prompt-preparation-20261008-01/HANDOFF.md` (evidence not published) and [readiness record] `../experiments/parent-prompt-preparation-20261008-01/readiness-validation.json` (evidence not published). The user asked for realistic timing, no fabricated work/results, an explanation of missed estimates, three-minute updates and project-owned context for a new chat. This documentation-only preparation supersedes earlier next-prompt pointers; it does not alter the dated E31 correction or authorize execution merely by being stored.

Estimate for the next investigation: 45–75 minutes overall; initial work ceiling 75 minutes. One guest observation is capped at 180 seconds, all owned processes/endpoints must be stopped/reaped/verified by 185 seconds, with runtime ended by session minute 60 and the final 15 minutes reserved for closure. Latest launch is minute 56. If prerequisites cannot be verified in time, preserve a precise preflight-only handoff; do not force success, extend runtime or launch a retry.

New static review confirms the held supervisor cannot meet the proposed group-wide deadline by changing its constants: individual-PID signaling, sequential waits and post-stop observations require new copied group/watchdog/deadline controls. These are future implementation prerequisites. The prompt requires validated local call/return mapping while broader reset totals/whole-parent return may remain unknown. Frozen offline corrections, original/runtime/archive evidence and older prompts/checksums remain unchanged. No app/engine/server/guest/hardware/endpoint work occurred in this preparation. [E32]


## October 8, 2026 — E33 parent attempt stopped by controller policy

One authorized guest/private-display attempt was consumed; no retry. The new host controller treated intentional denied `ql_syscall_vfork` as fatal, although E30 has the same denial before continued initialization. This is an instrumentation/stop-policy mistake, not an established firmware/parent failure. Actual CreateWindow caller `0x698500` is retained; requested reset/parent counts, dynamic bounds and actual returns remain unknown. Real verifier correctly fails `MISSING_CHAIN`; native final/ql.run result/clean guest termination are absent or unestablished. The server tree and black capture both predate guest creation, so post-return server output is unobserved. This dated correction governs stale ready-to-submit/current-handoff language above while keeping it as history. Physical operation, selected-feature validation, builds, update acceptance and recovery remain future scope.

Read the [new standalone handoff] `../experiments/parent-initialization-20261008-141426/HANDOFF.md` (evidence not published), [actual runtime classification] `../experiments/parent-initialization-20261008-141426/classification/STATIC_RUNTIME.md` (evidence not published), [supervision audit] `../experiments/parent-initialization-20261008-141426/supervision/AUDIT.md` (evidence not published) and [display coverage] `../experiments/parent-initialization-20261008-141426/display-classification.json` (evidence not published). Guest creation-to-TERM was 2.862303s; group closure 3.070427s; cleanup after early stop 0.208879s. All recorded processes/endpoints/helper are absent in the later live census. First supervisor suite retained an early-exit EOF failure; corrected six-case suite and ten observer controls pass. Required four complete policy negatives pass. The exact held runtime/clock and original bytes remain unchanged; 200,051 preserved paths match before/after.

The [next-session brief] `NEXT_SESSION_PROMPT-20261008-PARENT-STOP-POLICY.txt` (evidence not published) proposes only host stop-classification correction while retaining denied-vfork guard and finite deadlines; saving it grants no launch authority. The [private same-disk archive index] `../experiments/session-archive-20261008-parent-141426/README.md` (evidence not published) points to actual external comparison/manifest/dependencies; archive status must be read there. Recorded clock begins14:14:26.111851CDT after initial uninstrumented reads; exact first-action duration is unavailable. [Status timing] `../experiments/parent-initialization-20261008-141426/status-updates.jsonl` (evidence not published) includes late updates; [final closure/time register] `../experiments/parent-initialization-20261008-141426/session-close.json` (evidence not published) is outside frozen archive members.
