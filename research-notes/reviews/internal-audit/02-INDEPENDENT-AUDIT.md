<!-- source: ../PioneerSP16Review/02-INDEPENDENT-AUDIT.md | scrubbed -->

# Stage 2 — Independent technical audit

To: Project Director. Review date: October 9, 2026, America/Chicago.

This is an independent assessment and instruction record for future review. It authorizes no engineering changes, firmware execution, deployment, or communication to another chat. Companion records: [contradictions] `Review/02-CONTRADICTION-REGISTER.md` (evidence not published) and [validation requirements] `Review/02-VALIDATION-REQUIREMENTS.md` (evidence not published).

## Director's assessment

**Reported decoding and limited original-application UI progress are technically defensible. Progress toward a modified or replacement SP-16 operating system with new functionality is not yet demonstrated.** The available evidence supports a useful research harness, not a functioning virtual instrument or deployable firmware.

The strongest positive results survived independent checks: both updates decrypt exactly to the retained ISOs; outer ISO file contents and all ten primary tar payloads agree with retained files; original application lifecycle instructions match raw observations; HOME, Track 2 selection and MIXER have attributable retained output. The investigation did not find evidence requiring rejection of these narrow milestones.

The consequential weaknesses are missing instrument-level acceptance criteria, no real audio or board boot validation, incomplete peripheral/OS contracts, no matching build/repack/recovery proof, and an unproved input-to-parameter application path. Additional weaknesses concern circular synthetic tests, stale validation receipts, inconsistent outcome reporting, incomplete historical execution provenance, and untested whole-environment restoration.

**One Stage 1 quantitative statement is contradicted:** its 281→441 resource-return comparison is described as a common 245-second window. The cited primary comparison specifies **140.072 seconds after font completion**, within approximately 180-second native observations. The counts and 56.9% arithmetic survive; the duration does not. Other Stage 1 capability qualifications generally hold up.

No finding below treats missing evidence as proof that a capability is impossible, that firmware is fraudulent, or that the overall program has failed.

## Classification and priority

| Classification | Meaning |
|---|---|
| Verified | Direct bytes, inspected source, or retained primary observations substantiate the precise claim. Saved execution evidence is not a fresh execution. |
| Provisionally supported | Evidence supports the interpretation, but an important attribution, semantic, provenance or reproducibility condition remains open. |
| Unverified | Required supporting demonstration was not located in the examined material. |
| Contradicted | Specific evidence conflicts with the stated proposition; the proposition and its scope are identified. |
| Indeterminate | Available evidence cannot distinguish consequential competing explanations. |

High priority affects objective feasibility, instrument correctness, deployment, or preservation of indispensable evidence. Medium priority affects experiment validity, research decisions or reproducibility. Ordering reflects impact, not chronological order. Requirement IDs refer to the companion validation document.

## Findings by impact

### F01 — The ultimate objective has no demonstrated product acceptance boundary

**High; unverified:** modified/replacement OS capability, new instrument functionality and a defensible completion percentage. Stage 1 identifies this ultimate objective, while the main project describes extraction/emulation milestones and says no modification target has been selected. README establishes front-end progress but explicitly leaves physical boot, audio and deployment open. [E01, E02]

This is an objective-to-evidence gap, not a contradiction between two successful UI observations. There is no selected feature specification, observable instrument acceptance suite or demonstrated modification mechanism from which to infer feasibility, effort or distance to completion. “Firmware extracted” and “application initialized” cannot stand in for that evidence. Resolve through R01, then the applicable feature/audio/platform/deployment requirements. Do not infer that every BSP component must be rebuilt for every possible feature; that depends on the selected architecture.

### F02 — Application startup does not establish board or operating-system startup

**Verified:** the inspected harness constructs Qiling with the application ELF and copied rootfs, rather than booting the shipped kernel. **Unverified:** kernel boot, original driver operation, physical processor/peripheral initialization and whole-instrument readiness. Shipped `fw_env.txt`, inittab and launcher support an intended boot chain, not observed execution of it. [E03, E04]

The static startup status/mode loop can exhaust its bounded iterations and continue, as the retained startup map explicitly acknowledges. Calling it an all-devices-ready barrier would be **contradicted** by that control flow. Successful initializer return and HOME are valid front-end boundaries; missing peripherals may still be bypassed, unavailable or subject to untested branches. Actual unit storage, calibration, environment and release initramfs correspondence remain open. Resolve through R03 and R06; retain the front-end result under R02 without upgrading its scope.

### F03 — Synthetic PCM calls provide no audio/DSP validation

**Verified:** original-library PCM calls execute under a null fixture; selected transfer returns are 64 frames. **Unverified:** audible processing, sample integrity, sequencer timing, effect algorithms, codec operation and latency. The active configuration replaces `pcm.!hw` with `type null`, and the harness substitutes regular files for `/dev/null` and `/dev/full`. [E03, E05]

The earlier absent hardware PCM failure and later null success answer different questions. Counts of read/write calls do not certify every return, buffer contents, sample clocks, underruns or meaningful audio output. Requested core masks are also observations, not enforced affinity: the inspected handler returns -38 and records `emulated=False`. Consequently, physical multicore utilization and a hardware performance comparison are unverified. Resolve through R04 and R05. Service-manual assignment of audio processing to MAIN supports a starting hypothesis; it does not identify a particular effect implementation or a separate DSP processor. [E04]

### F04 — Deployment and recovery remain independent, unclosed technical dependencies

**Unverified; high:** unchanged-image round trip, modified-image acceptance, update routing, physical boot after an update, preservation of unit-specific data and demonstrated recovery. Valid ciphertext CRCs, uImage CRCs, known encryption and named A/B banks do not establish these capabilities. [E04, E06]

No examined successful artifact closes the complete updater acceptance path or demonstrates restoration after an interrupted/failed update. The partition declarations and service-manual NAND/calibration roles make unit-specific data an explicit dependency. A replacement OS would additionally need the relevant board drivers, panel/analog control, audio clocks and persistent-storage semantics. These obstacles are unclosed, not proven insurmountable. Resolve through R07 and R08 after R01 selects the deployment scope.

### F05 — GPL/BSP availability does not establish release source or build reproducibility

**Verified:** historical platform sources/build scripts exist, with Linux 3.0.101, U-Boot 2009.08 and historical toolchain references. **Unverified; high:** correspondence to held 1.50/1.60 releases, complete relevant sources, working toolchain/dependency environment and successful matching builds. [E04, E07]

The manufacturer's inspected public SP-16 source section is labeled Version 1.30, April 13, 2017 and uses `pioneerdj_tsp_rzx` filenames; held source packaging uses `pioneerdj_tsp`. That discrepancy is a provenance question, not proof that the source is unusable or wrong. [Manufacturer source listing](https://www.pioneerdj.com/en/support/open-source-code-distribution/gnu-open-source-license/). The proprietary application source has not been located. A shared kernel banner cannot prove binary equality or source correspondence. Resolve through R06, including a component-specific assessment of what the selected objective actually requires.

### F06 — Timing defects invalidate fidelity and hardware-performance inferences

**Verified; high:** installed `clock_gettime` ignores clock ID and derives `tv_nsec` by multiplying fractional wall time by 10^6. Installed `setitimer` returns success without timer/signaling implementation. The separate clock correction is not installed in the milestone condition. [E08, E02]

The fractional field compresses subsecond time by a factor of 1,000; it does not simply make all elapsed time 1,000 times slower, since whole seconds still advance. Wall time is also substituted for distinct clock domains. This conflicts with the documented clock interfaces. [Linux clock documentation](https://man7.org/linux/man-pages/man2/clock_gettime.2.html). **Indeterminate:** whether these defects explain observed startup/input delays, late memory growth or any individual failure. Host monotonic timestamps still support observation duration and event ordering; they do not establish guest timing correctness.

Named finite futex correction is deliberately limited to two threads and a verified wrapper PC/LR, with other operations delegated. Its relative timeout handling is consistent with the selected FUTEX_WAIT contract, but this is not complete futex/signal conformance. [E03; Linux FUTEX_WAIT documentation](https://man7.org/linux/man-pages/man2/FUTEX_WAIT.2const.html). Resolve through R05 before timing-sensitive or reliability conclusions.

### F07 — “Validated extraction” must exclude faithful Linux metadata

**Verified:** decoding and retained content substantially agree. **Contradicted; high:** interpreting passed historical audits as proof that the host trees preserve source permissions or constitute faithful boot/repack trees. Independent tar-header comparison reproduces **60 directory mode differences** across the ten primary tar containers. For image2 rootfs4: `tmp` 01777→0755, `var/tmp` 0777→0755 and `var/ftp/pub` 02777→0755. [E06, E09]

The decoder creates directories without restoring their modes; its tar audit checks directory type but not mode. The SquashFS audit compares two host extractions, allowing consistently lost source metadata to pass. The prior source-listing comparison records 22 further regular-file mode differences; that SFS census was inspected, not freshly rerun. Linux device entries are retained as metadata rather than usable host nodes. These limitations do not negate verified bytes/paths/targets, and no evidence proves they caused an observed UI failure. Resolve through R07 before deriving a Linux image or repack from host trees.

### F08 — Send preparation passed circular controls and still has a stale validation binding

**Verified; high:** the retained historical control explicitly places the synthetic widget identifier and `0xf6ab44` at the same value. Original construction evidence distinguishes identifier cell `0xf6c700` from Component-name cell `0xf6ab44`. The controls therefore reproduced the observer's mistaken premise instead of independently challenging it. A reported 59 checks did not establish readiness. [E10]

The attempted gesture run stops on the new observer assertion at 382.803695 seconds, before a Send gesture or setter, and has no native final. The exact failed RAM operands were not recorded: identifier conflation is **provisionally supported** as an explanation, not a proved root cause of that assertion. A separate roster failure at a shared POP belongs to another widget and also lacks a native final. Neither demonstrates an original firmware defect. [E11]

Fresh readback also confirms the corrected preparation's saved `send_observer.py` hash is `6f573780…a9bcf`, while current source is `6c0d1b64…75aa0`. Its launcher checks this identity and should reject the mismatch; launch readiness is **contradicted**, not evidence of silent unsafe acceptance. Later successful inspection does not validate the older failed package or its separate uninstalled fix. Resolve through R09 and R10 before reusing that package.

### F09 — Send and encoder maps do not close parameter application or hardware input

**Verified:** two original same-owner snapshots match raw log events exactly and both show value 0. The accepted encoder evidence's 98 instruction records and 25 data cells freshly match the original ELF. **Provisionally supported:** the conditional static panel/encoder/footer route. **Unverified; high:** live delivery, worker-to-owner handling, eligibility/clamps, setter/application/completion, owned changed rendering and audio consequence. [E12, E13]

The raw notification slot +0x14 and conditioned editing slot +0x10 are distinct; conflating them produces an incorrect no-op inference. Conversely, two no-op motion targets and inspected empty local listeners do not establish that every pointer/global input path is incapable of editing. The static route requires a complete 128-byte panel record, registered callback, loaded owners and thread conditions. A desktop X11 click does not validate the physical panel protocol. Excluded partial async findings were not reconstructed or adopted. Resolve through R09 and R04; count static mapping as knowledge, not executed editing.

### F10 — The narrow UI milestone is real; repeatability and broader usability remain qualified

**Verified; medium:** retained evidence demonstrates mapped application initializer/enclosing return, subsequent main dispatch, selected fresh completion acceptance, HOME, one Track selection and HOME→MIXER navigation. Stage 2 freshly matched 29 lifecycle hook points in each of three raw runs to the original ELF, with zero mismatches. Lifecycle raw lines 2624/2627/2632/3168 contain return/dispatch/readiness at 262.070216/262.070366/262.072164/269.429529 seconds. [E14]

Track's two packet/consumption/handler/return chains match raw events, and before/after XWD readback gives 3,420 changed pixels with half-open box [18,318,364,402]. Visual previews show the expected selection. MIXER raw lines 3592/3593 contain navigation/handler returns at 348.666955/348.667076 seconds; independent raw payload hashes distinguish HOME and MIXER. [E15, E16]

**Provisionally supported:** reproduction under the retained evolved harness. Related later runs corroborate initialization/MIXER; none is an independent clean-environment replay performed in this audit. Static HOME/MIXER samples establish persistence at sample times, not continuous liveness, playback or interactive stability. Bounded stop/exit 0 is harness termination, not natural application shutdown. Resolve through R02 and objective-specific acceptance under R01/R04. Older black/InputOnly negatives are superseded only for the later UI boundary, not rewritten as historical successes.

### F11 — Evidence authenticity is supported by consistency, not fully authenticated provenance

**Verified; high:** held update hashes, trailer/kernel CRCs, exact in-memory decryption, archive contents and several raw-event/summary relationships agree. **Unverified:** independent publisher identity of the held UPDs, complete earlier executed-revision provenance, and restoration of the entire required environment. [E06, E17]

Hash equality establishes identity to a reference, not the origin or contemporaneous truth of that reference. Logs, manifests and summaries largely come from the same engineering workflow; duplicates are not independent witnesses. Recovered extractor copies are useful, but recovery timestamps/current bytes do not identify every earlier executed revision. The checks found no affirmative evidence of fabricated results; absence of independent authentication is not evidence of fabrication. Resolve through R10 and R14, including official acquisition matching and representative independent replay. Preserve the provenance distinction when using “verified.”

### F12 — Success and input fields are unreliable when read without their scope

**Verified; medium:** historical consumer verification records false ownership checks while the verifier process returns 0. Corrected-TLS raw logs contain a worker TimeoutError alongside a bounded-stop/guest-exit-0 summary. Later code/control improvements do not repair those historical receipts. [E05, E18]

The successful Send inspection also has a substantive aggregate inconsistency: supervision says `conditional_input.input_sent=false` with `Capture failed or predates readiness`; the helper says `input_sent=true`, and tagged raw original consumption/handling demonstrates navigation. **Contradicted:** treating supervision's field as proof that no input occurred. **Indeterminate:** exact cause of the aggregate/capture error. The validated navigation and snapshots survive this reporting defect. [E12]

Other apparent conflicts are scope differences: a lifecycle-only observer's `full_startup_proved=False` is compatible with a composite assessment joining readiness and pixels. None proves physical boot. Resolve through R10; outcome aggregation must distinguish diagnostic validity, milestone attainment, observation completion and cleanup.

### F13 — Performance and memory claims need narrower interpretation; Stage 1 misstates one window

**Verified; medium:** one retained pair reports 281 versus 441 matched resource returns and 56.9395% more returns. **Contradicted:** Stage 1's “common 245s window” for that cited pair. `comparison.common_post_font_seconds` is **140.07205191699904**; native observations are 180.074551/180.115529 seconds. This correction changes reproducibility details without reversing the observed count difference. [E01, E19]

**Unverified:** general speed/reliability improvement or equivalent improvement in startup completion. The pair did not reach the selected constructor boundary. Reversed-order replication is inconclusive: control SIGBUS occurred before the treatment condition activated, and supervision revisions differed. The crash cannot reject the unactivated quantum. [E19]

**Verified:** sampled Mixer guest RSS grows from about 533 MiB at 44 seconds to 2,147 MiB at 583.951 seconds. **Indeterminate:** leak, emulator cache growth, instrumentation retention, guest allocation or a mixture. A static screen is insufficient steady-state evidence, and these samples do not establish a safe parallel-guest capacity. Resolve through R11.

### F14 — Repeated initialization and overlapping integration created demonstrable inefficiency

**Verified; medium:** separate worker, consumer, input, lifecycle, Mixer, failed Send/roster and successful inspection cycles repeatedly traverse initialization, often for a few adjacent observations. The Send workflow retained multiple corrected/frozen packages, and testing consumed an old premise already challenged in preceding static analysis. This is evidence of dependency/integration inefficiency. [E10, E11, E20]

Some repetition was necessary to isolate faults and preserve explicitly bounded scopes; controlled replication is not waste. The five-hour status record also distinguishes preparation/review work from new live milestones. **Unverified:** a precise total of wasted time, savings from a different staffing arrangement or a claim that all administration was unnecessary. Turn duration is not active engineering time, and disk allocation is not unique research value. Resolve through R12: justify each repeat by the uncertainty it closes, and ensure accepted prerequisite evidence governs the next frozen package.

### F15 — Historical “canonical/current” records and active storage operations limit record authority

**Verified; medium:** `PROJECT_STATE.md` still contains no-Git and older missing-UI statements beneath a supersession notice; extraction notes retain scope-specific no-execution statements. Main Git now has the October 9 baseline and no remote. Legacy `Code Projects` references do not name the current `Code_Projects` workspace. These are record/navigation defects, not evidence that the newer milestones are false. [E02, E17]

**Unverified; high preservation impact:** an off-device backup or fully tested research-environment restore. Git deliberately excludes originals, runtimes, rootfs, databases and raw logs/captures. The same-disk archive status includes xattr/setxattr restore failures and partial/retained states. **Indeterminate:** overall final archive completeness or data loss; the live tree is not an atomic snapshot and individual completed batches cannot certify all batches. [E21]

Resolve through R13 and R14. Do not replace historical artifacts, silently translate their recorded commands, or interpret one late Git commit as experiment-by-experiment provenance.

## Independent verification performed in Stage 2

All operations against engineering material were read-only. No saved decoder/verifier, project test, build, formatter, installer, Ghidra runner, emulator, vendor script or hardware operation was executed. No subagents or corrective engineering were started. Ad hoc Python used standard-library reads and CommonCrypto through ctypes; it did not import project modules or write source/output trees. Only the three requested review documents were created.

| Check | Result and boundary |
|---|---|
| Held updates and ISOs | Fresh SHA-256 matches Stage 1; both ciphertext/trailer CRCs pass. |
| Complete decryption | 194,324 sectors for 1.50 and 194,328 for 1.60 decrypted in memory using the held key's documented raw-byte handling. Zero sectors differ from saved ISOs. No key bytes/digest disclosed. This reproduces the transform; it does not authenticate publisher origin. |
| Outer ISO regular files | All 68 per release match saved manifest SHA-256, recorded source extent bytes and extracted ISO files. Manifest-directed check, not a new independent ISO-directory parser. |
| Primary tar payloads | All regular contents and symlink targets in all ten containers agree; no primary tar hardlinks occur. Directory mode comparison independently yields 60 differences. No extraction/node creation. |
| Linux kernels | Both uImage header/data CRCs pass. No boot or source rebuild. |
| Application identity | Original 1.60 ELF is 12,000,396 bytes, SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`; inspected lifecycle guest copy agrees. |
| Lifecycle source bytes | 29 points per run in lifecycle, Mixer and successful Send inspection; 87 comparisons, zero mismatches. These are repeated points, not 87 unique discoveries. |
| Encoder static bytes | 98 instruction and 25 cell records match original PT_LOAD bytes. Semantics/loaded execution separately qualified. |
| Track attribution | Saved packet/consumption/call/return arrays match raw log events: two each. XWD pixel difference independently reproduced; half-open bounding box agrees. |
| Retained display captures | XWD header/stride/payload-length and pixel hashes recomputed for lifecycle, Mixer and inspection capture sets. Stable HOME hash `7c665b7e…d71`; stable MIXER hash `1e19b61b…609`. Counts of all captures include supporting duplicates; milestone assessments use their selected owned timed subsets. HOME/MIXER/Track previews visually inspected. |
| Send inspection | Both saved snapshot objects exactly equal raw events; both values remain zero. |
| Prepared source binding | Corrected Send observer disagrees with its saved validation hash. Launcher source contains the enforcing comparison. No launcher executed. |

A first readback script failed only while serializing tuple-keyed capture counts; the corrected read-only reporting pass completed. This was an audit-tool output error, not a firmware result. Full SquashFS/nested re-expansion, every exported assembly file, database reopening, all earlier transcripts and current process census were not performed. Selected contemporaneous cleanup receipts were reviewed, not recertified by a live census. No whole-tree immutability certificate is implied.

## Source register

Paths use the actual workspace root. Relative member names quoted above remain as recorded evidence.

| ID | Inspected source / principal locator |
|---|---|
| E01 | [Stage 1 inventory] `Review/01-PROJECT-INVENTORY.md` (evidence not published), [baseline] `Review/01-TECHNICAL-BASELINE.md` (evidence not published), [gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published). |
| E02 | [README] `README.md` (evidence not published), [PROJECT_STATE](../../history/docs__PROJECT_STATE.md), [AGENTS] `AGENTS.md` (evidence not published). |
| E03 | [Lifecycle probe] `experiments/startup-lifecycle-live-20261009-165946/run-1/probe.py:557` (evidence not published), adjacent `timed_futex.py`, `cooperative_select.py`, `arm32_statfs.py`, `ioctl_fixture.py`, `alsa-null.conf`. |
| E04 | [Boot environment] `decode/output/image2/iso/images/fw_env.txt` (evidence not published), rootfs4 `etc/inittab`/`etc/rc.d/rc.local`, pdj `apl_start`; [startup map] `ghidra/STARTUP.md` (evidence not published); [retained service-manual text] `decode/tmp/consolidation/service-page-49.txt` (evidence not published); [architecture review] `engineering-reviews/2026-10-09-firmware-architecture-effects-knowledge.md` (evidence not published). Manual claims are documentary, not physical inspection. |
| E05 | [Corrected-TLS result] `experiments/emulation-20261008/corrected-tls-result.json` (evidence not published), [raw log] `experiments/emulation-20261008/logs/corrected-tls-console.log:117817` (evidence not published), [audio fixture] `experiments/startup-lifecycle-live-20261009-165946/run-1/alsa-null.conf` (evidence not published). |
| E06 | [Decoder] `decode/decode.py:226` (evidence not published), both `decode/output/image{1,2}/report.json`, `audit.json`, `iso-manifest.json`, `decoded.iso`, original `ResearchSourceFiles/*.UPD`, ISO `images/uImage` and five `*.tar.gz` payloads per release. |
| E07 | [Build script] `extracted/pioneerdj_tsp/pioneerdj_tsp/make_linux` (evidence not published), adjacent `ltib_common.sh`, `config/platform/imx/imx6_defconfig.dev`; manufacturer listing linked in F05. |
| E08 | [Installed clocks] `experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py:28` (evidence not published), [setitimer] `experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/posix/syscall/time.py:55` (evidence not published), [remediation handoff] `experiments/audit-remediation-20261009/HANDOFF.md` (evidence not published). |
| E09 | [Source-mode report] `experiments/offline-review-20261008-01/modes/README.md` (evidence not published), adjacent source listings/member records; original tar headers and host lstat independently reread. |
| E10 | [Historical Send controls] `experiments/mixer-send-preparation-20261009/identifier-contract-correction-20261009/before/offline_controls.py` (evidence not published), [validation receipt] `experiments/mixer-send-preparation-20261009/prepared/lifecycle-validation.json` (evidence not published), corrected adjacent observer and [launcher] `experiments/mixer-send-preparation-20261009/prepare_authorized_run.py:17` (evidence not published). |
| E11 | [Failed Send result] `experiments/mixer-send-live-20261009-193048/result.json` (evidence not published), raw run-1 stdout; [roster context] `experiments/mixer-send-roster-live-20261009-200343/failure-context-summary.json` (evidence not published), result/raw log. |
| E12 | [Send snapshots] `experiments/send-identity-live-20261009-200701/listener-snapshots.json` (evidence not published), [raw log] `experiments/send-identity-live-20261009-200701/run-1/supervision/guest.stdout.txt:3764` (evidence not published), `run-1/attempt-supervision.json`, `run-1/supervision/drawable-input-observations/result.json`, result/captures. |
| E13 | [Encoder evidence] `ghidra/encoder3-panel-route-20261009/evidence.json` (evidence not published), [handoff including receipt discrepancy] `ghidra/encoder3-panel-route-20261009/HANDOFF.md` (evidence not published), original ELF. |
| E14 | [Lifecycle raw log] `experiments/startup-lifecycle-live-20261009-165946/run-1/supervision/guest.stdout.txt:2624` (evidence not published), result/native final/display records/captures. |
| E15 | [Track analysis] `experiments/input-response-live-20261009/verification/input-response-analysis.json` (evidence not published), raw run-1 stdout, periodic-3/4 XWDs and before/after previews. |
| E16 | [Mixer raw log] `experiments/mixer-navigation-live-20261009-180208/run-1/supervision/guest.stdout.txt:3592` (evidence not published), result, timing, captures and `performance-*.json`. |
| E17 | Recovered extractor provenance `docs/handoffs/2026-10-08-independent-review/recovered-extractor/PROVENANCE.json` (evidence not published), main Git log/remotes and [.gitignore] `.gitignore` (evidence not published). |
| E18 | [Retained consumer verification failure] `experiments/completion-consumer-live-20261009/verification-attempt-1/result-verification.json` (evidence not published), retained verifier/failure and [handoff] `experiments/completion-consumer-live-20261009/HANDOFF.md` (evidence not published). |
| E19 | [Quantum comparison] `experiments/post-font-counted-quantum-20261008-repeat/comparison.json:4` (evidence not published), adjacent handoff/raw arms; [inconclusive replication] `experiments/quantum-replication-20261008/HANDOFF.md` (evidence not published). |
| E20 | [Workflow audit] `engineering-reviews/2026-10-09-parallel-chat-workflow-adversarial-audit.md` (evidence not published), [five-hour status] `engineering-reviews/2026-10-09-five-hour-project-status.md` (evidence not published), [invalid longer observation] `experiments/milestone-following-20261008/HANDOFF.md` (evidence not published). These retrospective judgments were checked against selected primary failures, not adopted wholesale. |
| E21 | [Same-disk archive status] `Archive/2026-10-09-active-folder-reduction-9b5acd38/status.json` (evidence not published), main Git exclusions and Stage 1 archival qualifications. No restore or archive mutation performed. |

### Evidence identity anchors

SHA-256 identifies the bytes read, not independent authorship or acquisition provenance.

| Artifact | SHA-256 |
|---|---|
| Stage 1 inventory | `d70335272b065b7e854e792ed8ffc9435decde6ba399c09e73adb9f41180b042` |
| Stage 1 baseline | `b0657c061b1f26a43d8eb8df78fbcacd22b33a13ac8bede3d21de963b85d43de` |
| Stage 1 gaps | `d8ccab21d22250ce5f150aef702c9f31aacdf210bbdf625bec664cc509e17a80` |
| Lifecycle raw stdout | `32fce86a7fb05c2c105abc9d1ee49b3daa00508764bfee3ba2de8e319463c9ca` |
| Mixer raw stdout | `db8cab4f7efd0c60a79f67c05d1560e93b5cc8435909b4f09060da3c62bd428a` |
| Successful Send-inspection raw stdout | `1ecd24ef3f88d94ebd54beba417c82bea6341b7c42eed96739d1dfe691d147aa` |
| Inspected decoder | `5b59766bf54289e67759e97f00410c33188e16515979a9427fa3e5f31c7c3dc3` |
| Held 1.50 UPD | `11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a` |
| Held 1.60 UPD | `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4` |
| Fresh decrypted / held 1.50 ISO | `534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b` |
| Fresh decrypted / held 1.60 ISO | `6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb` |

The audit is complete at these evidence boundaries. The Project Director should retain the verified research milestones and require the relevant validation before approving broader progress claims. Corrective engineering has not begun.
