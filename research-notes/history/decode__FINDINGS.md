<!-- source: decode/FINDINGS.md | scrubbed -->

# Findings and engineering assessment

**Historical assessment:** [docs/PROJECT_STATE.md](docs__PROJECT_STATE.md) now owns the current evidence classifications, hardware baseline, uncertainties and roadmap. Service-manual evidence and binary/source qualifications added there supersede this earlier snapshot.

This record separates directly observed evidence from interpretation. It does not claim a complete model of the SP-16 or a deployable modification process.

## Confirmed findings

| Finding | Local evidence | What it establishes |
|---|---|---|
| Updates decode to ISO 9660 with Rock Ridge; versions are 1.50 and 1.60 | `output/image{1,2}/report.json`, `audit.json`, and `iso/images/release.txt` | Readable, validated baseline firmware containers and internal version agreement. See STATUS.md for crypto details. |
| The extracted kernels identify Linux 3.0.101 | `report.json` → `uImage`; `iso/images/uImage` | Kernel image identity and valid header/data CRCs. This does not establish that supplied source reproduces either binary. |
| Boot configuration uses U-Boot commands and NAND partitions, with kernel A/B selection | [1.60 fw_env.txt] `output/image2/iso/images/fw_env.txt` (evidence not published) | Intended boot commands and partition configuration shipped in the update. Not a readback of a physical unit's current environment. |
| BusyBox supplies init; inittab starts rcS and other board scripts | [1.60 inittab] `output/image2/payloads/rootfs4/etc/inittab` (evidence not published), `payloads/rootfs4/sbin/init` symlink, [rcS] `output/image2/payloads/rootfs4/etc/rc.d/rcS` (evidence not published) | Main userspace initialization entry points. Installed service scripts alone do not prove a service runs. |
| rc.local starts /root/pdj/apl_start; that script launches EP085_Main_R | [rc.local] `output/image2/payloads/rootfs4/etc/rc.d/rc.local` (evidence not published) near line 66; [apl_start] `output/image2/payloads/pdj/pdj/apl_start` (evidence not published) near lines 452–475 | Directly evidenced application launch chain, including a testmode branch. No launch was performed. |
| EP085_Main_R is an approximately 12 MB, dynamically linked, 32-bit ARM EABI5 ELF executable marked stripped | `file` inspection of [1.60 application] `output/image2/payloads/pdj/pdj/EP085_Main_R` (evidence not published) | Compiled application is present. Most internal symbol/debug information is absent; runtime symbols/strings may still remain. No original application source has been identified in the material inspected. |
| Launcher loads snd-din-midi and midi_thru | [apl_start] `output/image2/payloads/pdj/pdj/apl_start` (evidence not published), near lines 399–406 | MIDI-related kernel module setup in the startup script. It does not explain application MIDI semantics or prove hardware behavior. |
| Separate panel firmware payloads exist | `output/image{1,2}/iso/images/PANELCOM1.mot` and `PANELCOM2.mot` | Motorola S-record files are preserved; their protocols and feature responsibilities have not been analyzed. |
| Supplied platform material includes Linux, U-Boot, BusyBox sources and build scripts | `../extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/`, `make_linux`, `config/platform/imx/imx6_defconfig.dev` | Source/build starting points exist; inspection showed an i.MX6Q configuration. Build reproducibility and exact correspondence to 1.50/1.60 are unverified. |
| Supplied initramfs source prepares a RAM-backed root, mounts SquashFS components and switches to init | `../extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/init`, particularly lines 270 onward and 476–549 | Evidence of the supplied platform's boot design. This initramfs has not been extracted from and compared with each update's kernel. |

The ELF interpreter's reported GNU/Linux ABI minimum (2.6.31) is not the running kernel version. Kernel identification comes from the uImage, not that ELF tag.

## Interpretation and readiness

- **Broad platform architecture: supported by evidence.** We can describe the intended boot configuration, Linux userspace layout and application startup. We have not observed a running unit or verified every boot branch.
- **Sampler internals: unresolved.** EP085_Main_R is the launched application and a likely focus for sampler/UI feature research. How audio, sequencing, UI, storage and panel control are divided between it, libraries, drivers and other processors remains unproven.
- **Extraction is not source recovery.** Disassembly can expose machine instructions; decompilation can approximate higher-level logic. Neither guarantees original names, comments, types or correct behavioral interpretation. No application-wide disassembly/decompilation has been completed here.
- **Offline script/configuration/asset edits: plausible starting work.** A specific target and its consumers must be identified before changing anything. No such patch has been made or tested.
- **Additional utilities/services: plausible but unvalidated.** ABI/toolchain compatibility, launch/persistence, available resources and interference with audio workloads would need testing.
- **Sampler/sequence/effect features: not yet estimable reliably.** There is no evidence here of a supported plugin or extension interface. Targeted investigation is needed before judging implementation effort or feasibility.
- **Firmware deployment: not ready.** Decryption and wrapper CRC verification do not demonstrate all update acceptance checks, a faithful re-encoder/repacker, bootability, or a recovery procedure. A/B kernel labels do not by themselves prove safe rollback.

## Open questions

1. What exact behavior does the user want to change, and how will success be measured?
2. Which code/resource/configuration path implements that behavior?
3. Can the supplied source and toolchain reproduce relevant components for either firmware?
4. How do the main application, audio/MIDI drivers and panel controllers communicate?
5. What runtime/debug access is actually available on the user's hardware?
6. Can an unchanged image be repacked equivalently, and what checks does the complete updater apply?
7. What backup, recovery and test procedure can be demonstrated before deployment?

## Effort estimates discussed — planning judgments only

These are rough engineering-effort ranges, not measurements or promised completion dates. Access/setup delays and the chosen feature may change them substantially; phases overlap and should not be summed mechanically.

| Work | Preliminary range |
|---|---|
| Initial static application map | Several hours to 2 days |
| Trace one bounded feature | 2–10 days |
| Establish runtime observations | Several days to weeks, depending on access |
| Implement a modification | Hours to weeks, depending on scope |
| Validate/package a candidate | Several days to weeks |
| Substantial new sequencer, effect or UI feature | Potentially weeks to months; feasibility unknown |
| Comprehensive application understanding | Many months or longer; not required for most targeted changes |

Recommended assessment approach: choose one feature, produce a bounded feasibility report with evidence and unresolved dependencies, then revise the estimate. No active reverse-engineering workstream has been started.
