<!-- source: ../PioneerSP16Review/03-ARCHITECTURE-ASSESSMENT.md | scrubbed -->

# Stage 3 — Architecture assessment

Review date: October 9, 2026, America/Chicago. This is an architectural assessment and instruction record for future authorized investigation. It contains no implementation roadmap or authority to execute experiments. Only the three Stage 3 review documents are being written; the main project remains read-only.

## Architectural conclusion

The extraction, static reverse engineering and userspace emulation approach remains appropriate **as a research capability**. It is insufficient as the governing strategy for adding functionality to a physical SP-16. Continued development must be justified by the product decision it resolves, rather than by making progressively more of the original interface work in an emulator.

The strongest provisional strategy is to retain the shipped bootloader, kernel, board support and panel firmware while investigating the smallest userspace change that supplies a selected feature. This could be a resource/configuration change, a companion process, a bounded application patch, or eventually a replacement application. These are materially different commitments from replacing the kernel and hardware support. No available evidence yet proves any of them deployable.

A complete replacement OS remains a conditional option. It becomes attractive if essential features cannot be supplied within the original application/platform, or if maintaining those components is unacceptable. It is presently the option with the greatest number of unclosed dependencies. Existing investment in emulation does not justify preferring modification; lack of proprietary source does not justify preferring a rewrite.

## Evidence basis and interpretation

The controlling sources are the [Stage 1 baseline] `Review/01-TECHNICAL-BASELINE.md` (evidence not published), [inventory] `Review/01-PROJECT-INVENTORY.md` (evidence not published), [gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published), [Stage 2 audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published), [contradictions] `Review/02-CONTRADICTION-REGISTER.md` (evidence not published) and [validation requirements] `Review/02-VALIDATION-REQUIREMENTS.md` (evidence not published). B/G/F/C/R identifiers below refer to those documents. Verified means verified within their stated scope; historical execution is not a new replay or board observation.

Stage 2 takes precedence over the Stage 1 performance-window claim: 281→441 resource returns were measured over **140.072 seconds after font completion**, not 245 seconds. This does not establish a general speedup (F13/C10). The earlier architecture/effects report's incomplete-UI status is superseded by the accepted lifecycle/Track/Mixer evidence; its caution about unidentified effects remains applicable.

This stage reviewed those records and selected main-project architecture, boot and status documents. It did not repeat decryption, inspect every driver, reopen Ghidra, execute firmware or certify the changing archive tree. External checks confirm the manufacturer's source listing and the i.MX6 family's authentication capability; neither supplies SP-16 unit measurements.

## Reassessing the architecture from the objective

The objective is new functionality on the instrument. Its necessary evidence consists of: an observable feature; an executable change at the correct software boundary; a way to deliver/run it on the unit; correct operation of the affected hardware and existing functions; and recovery from failure. Application screenshots close only a small part of that chain.

The boot stack should be considered in separable layers:

| Layer | Evidence-backed state | Architectural implication |
|---|---|---|
| Physical board and boot ROM | Manual identifies an i.MX6Q main processor and panel MCUs; actual unit/access/security state unknown (B10–B11, G05) | A chip family is a starting point for investigation, not a working board port or access route. |
| U-Boot and storage | Held U-Boot/source, declared NAND partitions and A/B kernel choices (B13) | Retaining this layer may reduce disruption. Current environment, authentication and recovery must be measured separately. |
| Linux/BSP and root assembly | Shipped Linux 3.0.101 uImages; source/initramfs/scripts exist (B08, B12–B15) | Existing kernel/drivers are plausible reusable assets. Release correspondence and runtime contracts remain open. |
| Panel/codec/analog hardware interfaces | Documentary roles, original ALSA imports and partial panel read/dispatch trace (B11, B28) | A new application may reuse interfaces, but must reproduce initialization, calibration and resource ownership requirements. |
| Proprietary application | Original ARM32 ELF, shipped libraries, selected static and UI runtime paths (B14, B17–B29) | Localized modification is a credible research hypothesis. There is no recovered proprietary source or demonstrated extension API. |
| Packaging/update | Exact decryption and coherent contents; CRCs pass (F11) | Packaging is understood better than complete acceptance, destination routing or safe deployment (F04). |

Replacing a layer is justified by a requirement or demonstrated constraint in that layer. “Replacement OS” should not silently require rewriting the panel MCUs, bootloader, kernel, sampler, effects and UI together. Conversely, a replacement application retaining vendor Linux is an application replacement, and should be described precisely rather than credited as a full OS replacement.

## Which engineering decisions are supported

| Decision | Assessment | Limit or needed evidence |
|---|---|---|
| Retain original packages and use them as content/metadata authority | Strongly supported by F07/R07 | macOS host trees lose consequential Linux modes and represent devices only as metadata. |
| Use byte-backed static analysis with loaded-state confirmation | Supported by lifecycle and encoder checks (F09–F10) | Correct bytes do not prove inferred types, ownership, eligibility or executed application state. |
| Preserve shipped application/libraries as a reference | Supported by reproducible local identities and retained UI milestones | Publisher provenance and independent environment restoration remain separate (F11/F15). |
| Use userspace emulation for localized application questions | Demonstrated value: selected startup, navigation and identity inspection | Kernel, electrical interfaces, audio deadlines and recovery are outside its demonstrated scope. |
| Treat loader/TLS/syscall repairs as harness adaptations | Supported by inspected source and results | They do not become required patches to the original firmware. A harness failure is not automatically a device failure. |
| Reuse vendor Linux/BSP before replacing hardware support | Reasoned preference based on existing artifacts and documentary platform | No complete release-matching build or physical reuse demonstration exists. |
| Treat logical encoder 3 as a candidate input route | Byte-backed conditional static evidence (B28/F09) | Complete record delivery, worker-to-owner handling and parameter application are unproved. |
| Adopt JUCE DSP, a separate DSP firmware, plugin API, or full panel protocol | Unsupported | Imports, thread names, GUI assets and a signal-flow label do not establish these architectures (B30/R04). |
| Assume dual kernel banks provide rollback | Unsupported | Shared rootfs/application/environment/panel state may change independently; actual update behavior is unknown. |

## Emulation's marginal value

The harness has earned its place as a tool. It should cease being the default destination of all research. Its useful questions include locating an original parameter's owner, observing a legal state transition, following a selected processing buffer, and testing a bounded binary change against an unmodified reference.

The current fixture does not supply meaningful audio, real device readiness or valid timing fidelity. Null PCM, regular-file device substitutions, unenforced affinity, defective clocks and success-only timers constrain what it can establish (F03/F06, R04–R05). Long startup and growing host RSS increase experiment cost without proving comparable device behavior. Do not diagnose a device leak or hardware speed problem from these observations.

| Research method | Prefer when | Defer or reject when |
|---|---|---|
| Existing userspace harness | A selected application ambiguity needs actual loaded state and the required contracts are understood | The question is ROM policy, NAND recovery, codec clocks, electrical panel behavior or physical latency. |
| Static original-binary/source inspection | Control flow, registration, acceptance checks or driver ABI can discriminate options without execution | Loaded ownership, hardware state or runtime success is the disputed claim. |
| Isolated function/buffer test | A candidate algorithm has a known ABI, inputs and dependencies | Bypassing initialization/state would answer a different question and be reported as whole-instrument success. |
| Native ARM execution under a compatible Linux environment | A future comparison can reduce interpreter/syscall cost while retaining needed userspace ABI | A generic board is being treated as the SP-16; peripheral and timing equivalence remain unproved. |
| Instrument-side observation | Actual startup, drivers, panel records, audio or resources determine feasibility | Hardware access/recovery conditions needed for the proposed action are unavailable. |
| Full-system emulation | A specific boot/kernel question needs modeled devices and model cost is justified | It would require constructing a virtual SP-16 before learning whether the selected feature needs it. |

Full-system emulation is not an obligatory successor to Qiling. Native execution or physical observation may answer decisive questions with fewer artificial contracts. A whole-instrument emulator would be a substantial separate product whose value must be justified independently.

## Hardware, integrity and recovery constraints

The [shipped environment] `decode/output/image2/iso/images/fw_env.txt` (evidence not published) contains console `ttymxc0,115200`, `jtag=on`, NAND bank commands, MMC/network alternatives and `bootdelay=0`. These are static candidate leads. They prove neither accessible pads/ports, interactive console, usable Ethernet, enabled debug, available boot mode nor the current unit's environment.

There are at least four distinct acceptance boundaries: update-container checks; component/destination/version checks; bootloader/kernel authentication; and application/runtime integrity checks. Knowing sector encryption and recomputing CRCs does not close them. Nor does it prove that a signature exists. The i.MX6 family supports HABv4 authentication of the initial image and can extend trust to later components. Whether the SP-16 enables it, and which layers it covers, is unknown. A restriction on replacing U-Boot would not alone prove a restriction on changing userspace. [NXP AN4581, Rev. 2](https://community.nxp.com/pwmxy87654/attachments/pwmxy87654/imx-processors/194321/1/AN4581_2018.pdf).

Actual NAND geometry, ECC/OOB/bad-block handling, UBI layout, eMMC mounts, per-unit identity/calibration and update write ranges are dependencies, not details to reconstruct from generic offsets. A raw dump is not automatically restorable through a different NAND access method. A working stock updater may require a working application or kernel and therefore may not recover a nonbooting unit. Panel flashing introduces a separate recovery problem; identical panel payloads across releases favor investigating reuse before replacement, but do not guarantee compatibility with new main software.

Audio requires the actual codec/clock/routing contract, sample formats, duplex behavior and timing under load. Panel control includes more than one encoder: pads, LEDs, switches, touch, gain and other MCU-mediated functions must meet the selected compatibility boundary. The analog filter remains physical signal-processing hardware with an unresolved software-control interface; rewriting a digital filter does not supply its control contract (B11/B16/B30).

The historical source drop is useful, but not established as the held release's complete BSP. The official listing still identifies SP-16 Version 1.30 and `pioneerdj_tsp_rzx` bundles. This supports component-lineage investigation, not a release-equivalence claim. [Manufacturer source listing](https://www.pioneerdj.com/en/support/open-source-code-distribution/gnu-open-source-license/).

## Fundamental feasibility risks versus local research defects

| Unknown | Why it can change architecture | Smallest discriminator |
|---|---|---|
| A permitted executable delivery route | All on-device approaches require one; authenticated restrictions may affect only particular layers | Identify the complete relevant acceptance chain and actual unit policy; propose a harmless volatile execution test only where supported. |
| Recoverability and unit-specific state | Determines whether persistent experiments are tolerable | Establish recovery entry and the exact state/write scope; validate restoration independently of normal application startup. |
| Access to a unit and observable boot/interfaces | Without it, physical feasibility remains conditional regardless of UI progress | Obtain an existing unit/access inventory and stock boot evidence; do not presume ownership or console access. |
| Required proprietary peripheral dependencies | Can make application replacement or modern Linux substantially harder | Determine the initialization and ABI for the selected peripheral from shipped runtime and one stock observation. |
| Feature boundary and application entanglement | A small policy change and a new processing architecture have different costs | Map one explicitly selected feature from input through state to output and persistence. |
| Real timing/resource headroom | May preclude a chosen processing architecture even if it functions | Measure stock hardware and a representative bounded workload; host RSS cannot answer this. |
| Needed source/build correspondence | Can block kernel/driver replacement while leaving userspace options open | Compare only the components required by the candidate architecture. |

Missing Send operands, stale validation bindings, circular controls and reporting inconsistencies are serious experiment-validity defects. They do not establish fundamental impossibility. Similarly, unknown acquisition provenance and backup completeness affect confidence/preservation, but must not be confused with a demonstrated secure-boot block.

## Sunk-cost exposure

The following work may become sunk-cost commitment if continued without a decision-changing question:

- Completing Send Amount because it is the current continuation. It is useful only if it discriminates a needed input/state/patch mechanism; it is not itself new functionality.
- Repeatedly proving HOME, MIXER or unchanged rosters after their scope is already accepted. Independent restoration/replay or changed-condition validation is a different, justified purpose.
- Expanding UI class maps, listener inventories and render paths without a selected feature boundary.
- Pursuing scheduler throughput or emulator fidelity because substantial effort has already been invested in the harness. Corrections needed for a selected inference remain valuable; universal conformance is not required by the current objective.
- Building full machine emulation to preserve the existing research architecture, or rebuilding every open-source package merely because sources were extracted.
- Rewriting panel firmware, bootloader or all effects before demonstrating that retained components prevent the desired feature.
- Producing competing frozen packages, copied rootfs trees and handoffs as substitutes for accepted new evidence. Preserve indispensable records; duplication is not progress.

Past extraction, TLS, painting and identity work was productive within its scope. Sunk cost concerns the reason for further investment, not a retroactive claim that all earlier effort was waste. Preferred direction and experiment-level decision criteria appear in [recommended direction] `Review/03-RECOMMENDED-DIRECTION.md` (evidence not published); alternative architectures appear in [strategic options] `Review/03-STRATEGIC-OPTIONS.md` (evidence not published).
