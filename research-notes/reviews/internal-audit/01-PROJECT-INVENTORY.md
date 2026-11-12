<!-- source: ../PioneerSP16Review/01-PROJECT-INVENTORY.md | scrubbed -->

# Stage 1 — Project inventory

Review date: October 9, 2026, America/Chicago. This is a review record for future project work, not an implementation instruction or a new roadmap. The intended destination is a modified or replacement SP-16 operating system with new functionality. The demonstrated project is presently a firmware extraction, static analysis, and original-application emulation research environment.

## Assessment

The project has decoded two updates, identified the intended Linux platform and startup chain, and made the unchanged firmware 1.60 application initialize, render HOME, select Track 2, and navigate to MIXER in a modified emulator. Recent raw evidence supports these accomplishments. There is no demonstrated replacement OS, modified product feature, physical boot, real audio/DSP validation, deployable repack, or recovery procedure.

The principal recent failure concerns Send Amount observation and input preparation. Two attempts stopped on observer assertions before establishing an edit. A separate subsequent inspection successfully captured original Send identity and listener state, but did not change a parameter. Static encoder and rendering maps are useful research assets, not a completed input-to-audio or input-to-rendered-edit capability.

Read [technical baseline] `Review/01-TECHNICAL-BASELINE.md` (evidence not published) for the claim register and independently checked evidence; read [evidence gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published) for contradictions, failures, and missing evidence.

## Scope and method

Local repository discovery, directory/file enumeration, Git history and configuration reads, document/outcome searches, source inspection, saved JSON/log analysis, original ELF byte comparisons, CRC/hash recomputation, XWD payload inspection, and visual inspection of milestone previews were read-only. No decoder, project test, build, formatter, package installer, emulator, Ghidra runner, vendor script, or hardware operation was launched. No subagent, implementation task, or message to another chat was created. Only these three new review documents were written.

Coverage is comprehensive at the project/workstream level, with deeper primary-evidence checks for consequential claims. It is not an exhaustive line-by-line audit of every vendor source file, copied rootfs, historical log, native Ghidra database, or earlier conversation. Historical reports and duplicated snapshots were indexed as provenance, rather than counted as independent confirmations. Excluded partial async findings were not reconstructed or adopted.

The filesystem is not a frozen snapshot: the separate chat **Reduce active research folder** was active during discovery. Its archive helper and records changed while being examined. The directory sizes and counts below are observations from this review window, not a completed storage audit or a final archive census.

## Source inventory and access

| Repository/directory/source | Examination | Access and qualification |
|---|---|---|
| [PioneerSP16]() | README, AGENTS, local Git metadata/history, directory inventory; all research areas below | Readable. Treated strictly as read-only. One local baseline commit; no configured remote observed. |
| [PioneerSP16Review] `Review` (evidence not published) | Existing independent review, UI-blocker review, adversarial audit, saved review evidence, three main-project prompts, local Git history | Readable. Dedicated review workspace; these documents supplement existing records without replacing them. |
| [ResearchSourceFiles] `ResearchSourceFiles` (evidence not published) | Both UPDs; PDFs; source archive/part inventory; legacy extraction report | UPD bytes and local manuals available. No fresh vendor download or authenticity comparison. Some redundant assembled sources are subjects of ongoing archival work. |
| [decode] `decode` (evidence not published) | Decoder source, STATUS/FINDINGS/README/PROCESS, both report/audit/manifests, ISOs, release files, kernels, application, panel payloads, boot/startup scripts | Available. Original containers retained. Host extraction metadata is not Linux-faithful. Decoder/audit commands mutate outputs and were not run. |
| [extracted] `extracted` (evidence not published) | Eight top-level source bundles; focused Pioneer BSP/build/configuration, cryptoloop and initramfs evidence | Available during discovery; some bundles are archival candidates. Selected source review, not an exhaustive BSP audit or build. |
| [copyright] `copyright` (evidence not published) | Directory/file inventory and relationship to existing package/license ledger | License/package evidence, not proof that every package executes or matches release binaries. No legal conclusions made. |
| [docs] `docs` (evidence not published) | State/ledger/inventory/validation/transformation records, dated prompts, independent-review handoff, recovered extractor provenance, storage records | Available. Historical state is explicitly superseded for runtime status; old “canonical/current” wording can mislead. |
| [engineering-reviews] `engineering-reviews` (evidence not published) | Index, 41 Markdown files indexed, workstream outcome/decision review; focused startup/UI/Send/architecture records read | Available. Decisions and summaries used to locate primary evidence, not substituted for it. |
| [experiments] `experiments` (evidence not published) | 96 top-level directories; handoff/outcome census, historical runbooks and archives; selected harnesses, verifiers, controls, manifests, raw logs, finals, supervision and captures | Available with active archival movement. Deep reads concentrated on extraction qualifications, emulation conditions, milestones, and failures. An experiment directory is not necessarily a guest attempt. |
| [ghidra] `ghidra` (evidence not published) | Shared project/provenance/settings, startup exports, private UI/Send studies, integration records, encoder route raw evidence | Text exports available; databases present. No database reopening in this stage. Existing reopen receipts are historical evidence. Startup-gates is paused; async partial work remains excluded. |
| [analysis/ghidra-1.60-20261009] `analysis/ghidra-1.60-20261009` (evidence not published) | Earlier project handoff, provenance and retained unrelocated-PLT diagnosis | Available. Earlier tool failure is preserved, distinct from corrected shared-project results. |
| [Ghidra installation] `<HOME>/Code_Projects/ghidra_12.1.4_PUBLIC` (evidence not published) | Installation layout and project installation/settings receipts | Readable tool distribution, not another SP-16 engineering repository. No tool executable launched. |
| [PioneerSP16Archive] `Archive` (evidence not published) | Active-folder-reduction batch directories, owner/status/interruption records and archive layout | Readable. Same-disk archive is in progress; restore metadata checks have failed. Compressed contents not exhaustively restored/rechecked here. |
| `` | Existence check; legacy references in historical records and chat metadata | Does not exist. Current root uses `Code_Projects`. Legacy absolute paths can be historical evidence without being executable/current links. |
| `/private/tmp/sp16_extract_recursive.py`, `/private/tmp/sp16_extract_verify.py` | Recovery provenance and repository copies | Historical recovery is documented. Current external originals were not relied on; retained copies exist in the independent-review handoff. Complete earlier revision/command binding remains limited. |
| Codex/ChatGPT project and chat metadata | Project listing, latest 50 unarchived chats, all 89 returned archived Codex entries over two pages; 67 archived entries have SP-16/review cwd | Three SP-16 project entries resolve to two local folders. Metadata is supplementary. Selected extraction and prior research conversations read; complete transcripts/older turns were not all retrieved. No chat was messaged. |
| Public source distribution | Official GPL/LGPL page opened and SP-16 section inspected | Available. SP-16 section is labeled **Version 1.30 — April 13, 2017** and lists source bundles. Listed filenames include `pioneerdj_tsp_rzx`, unlike held `pioneerdj_tsp`; exact packaging relationship unverified. [Official source listing](https://www.pioneerdj.com/en/support/open-source-code-distribution/gnu-open-source-license/). |
| Public firmware pages | Previously cited official product firmware page and regional archive opened | Product page returned HTTP 403. Regional page was readable and lists 1.50, linking onward for downloads; no binary fetched. Regional publication date differs from release-history date and is not substituted for it. [Regional listing](https://pioneer-india.in/download-center/firmwares/toraiz-sp-16/). |
| Vendor internal SVN referenced by `system.rev` | Identifier read in both firmware reports | Historical build metadata, not an accessible checked-out repository. Credentials/access and release history unavailable to this review; no connection attempted. |
| Hardware, NAND/eMMC readbacks, external backups, proprietary application source, CI | Sought through project inventory/records | No verified primary artifacts located for these capabilities. This means unestablished in examined evidence, not proven nonexistent everywhere. |

Other sibling Ensoniq/EPS projects were visible in the directory and app inventory; no evidence identifies them as SP-16 repositories, so their engineering internals were outside scope. No second local SP-16 implementation repository or remote Git origin was found. A selected Page was not present; no cloud Page evidence was silently assumed accessible.

### Scale and provenance

The initial main-folder Git baseline is `82b0ddf87f4a5dd2750b4428dc62d8286aaffab9` (**Initial local research baseline**, October 9 at 21:11 CDT), branch `main`, with 9,532 tracked paths observed. Earlier October 7–9 experimentation is represented by files, logs, manifests and handoffs, not experiment-by-experiment commits. The review repository contains `a9257a2` (initial reports/evidence) and `5b703a0` (storage-reduction prompt). No review commit was made in this stage.

The main `.gitignore` deliberately excludes original packages, extracted vendor trees, rootfs copies, runtime installations, native Ghidra databases, raw logs/captures, credentials, and selected large text records. Seven milestone preview images are allowlisted. A clone of this Git repository alone cannot reproduce the complete research environment or evidence corpus.

A research-document census found 242 Markdown paths across docs (14), engineering-reviews (41), experiments (168), ghidra (17), and analysis (2), excluding guest/vendor/runtime/cache trees. Counts include duplicate historical snapshots and inherited handoffs. Initial approximate disk allocation was ResearchSourceFiles 3.6G, extracted 10G, experiments 25G, decode 930M, ghidra 774M, analysis 293M and docs 212M. These `du` figures were sampled during concurrent archiving, are rounded host allocation, and are not unique logical evidence size.

## What has actually been accomplished

| Workstream | Accomplishment | Evidence strength and limit |
|---|---|---|
| Update decoding/extraction | Both held 1.50/1.60 updates decoded; coherent ISO, eight primary payload containers per release, file/link manifests, nested expansions and saved audits | Strong artifact-backed result; current hashes/CRCs checked. Full extraction audit not replayed. Special nodes and mode fidelity qualified. |
| Hardware/platform characterization | Intended i.MX6Q/Linux/BusyBox/U-Boot, startup chain, storage organization, main/panel processor roles documented | Primary shipped scripts/configuration and manual evidence. Actual unit population, boot state and clocks unobserved. |
| Original ELF execution | Entry/main, thread creation, synthetic ALSA startup and sampled 64-frame returns | Raw records plus source/fixture identities. No real audio or CPU benchmark. Earlier worker deadline exception preserved. |
| Emulator adaptation | Loader relocation/library mapping, per-thread TLS helper, authenticated local X display, flag translation, ARM32 statfs, invalid-fd ioctl, cooperative scheduling/select, selected finite futex waits | Working research machinery, with source and controls. Partial syscall/device emulation, retained clock defects and historical faults remain. |
| Initialization/resources | Parent/enclosing returns, full original font discovery, resource/layout progress, original Expose/redraw and painting chain | Historical call/frame/byte evidence; recent initializer/dispatch results supersede earlier incomplete startup reports. |
| Persistent HOME/readiness | Worker/main completion correlation, popup removal and stable original 800×480 HOME; later mapped startup return and dispatch | Verified within bounded software-emulation conditions. No physical boot or all-subsystem readiness assertion. |
| Track selection | Single tagged Track 2 click consumed and handled; label/outline change and stable selected captures | Verified end-to-end UI interaction in the recorded guest. Two exact button events; 3,420 changed pixels independently checked. |
| Mixer navigation | Tagged HOME→MIXER tap, original callbacks/returns, distinct sixteen-fader output and stable captures | Verified UI navigation; no fader/mute/pan/audio behavior demonstrated. |
| Ghidra/static analysis | Reusable corrected 1.60 project; startup/UI paths; Send identity, display, input listener and conditional encoder path maps | Original-byte-backed partial reverse engineering. Inferred names/types are not recovered source. |
| Send diagnostics | Correct identity/name distinction and two same-owner original listener/parameter snapshots | Verified inspection, value remained zero. No edit/setter/application/rendered-edit proof. |
| Evidence/controls | Saved commands, source identities, negative controls, supervision/cleanup receipts, retained failures and Git baseline | Material reproducibility assets. Controls validate harness contracts; they do not count as original-firmware milestones. |

## Current and deferred work

“Current” distinguishes an implemented/observed state from the next action stated in a document. No SP-16 guest is established as actively running by this review; completed guest sessions have consumed allowances and saved closure. This stage did not perform a live process census.

| Work | Recorded state at review |
|---|---|
| Original startup/HOME/Track/Mixer discovery | Completed at the narrow verified boundaries above; earlier handoff next actions are historical. |
| Send Amount mutation | **Unready.** Pointer eligibility, legal transport, full deferred application and owned edit rendering unresolved. |
| Encoder-3 input route | Latest accepted offline trace completed. Existing README selects examining emulator panel read/delivery and sparse ownership/gate evidence. This is recorded continuation, not a new Stage 1 plan. |
| Send roster failure correction | 13-control return-owner correction exists separately, uninstalled/live-unvalidated. Later independent inspection answers its narrow roster question without retroactively fixing the failed guest. |
| Guest clock correction | 51 recorded offline clock/dispatcher checks; separate opt-in source exists, uninstalled in milestone conditions. |
| Startup-gates study | Explicitly paused; partial tooling/missing-status/context-write records retained. |
| Async model assignment | Stopped/incomplete after a recorded cybersecurity restriction; no accepted final artifacts, excluded from integrated claims. |
| Static UI path research | Private completed mapping, including Mixer→HOME and track-volume candidates. Full live paths/audio behavior not demonstrated; not equivalent to shared integration. |
| Active-folder reduction | Separate active chat, archive batches/restore checks underway; not a finished or verified backup. |
| BSP builds, source-to-binary matching, feature changes, repack, physical deployment/recovery | Deferred/unknown; no demonstrated implementation, build, acceptance or hardware result. |

## Existing plans reviewed, without a replacement roadmap

`decode/FINDINGS.md` contains preliminary effort ranges and feature-first feasibility suggestions; these are historical planning judgments. `docs/PROJECT_STATE.md` sections 15–16 contain unknowns and a deferred backlog for feature mapping, updater routing, matching source builds and recovery. Dated `NEXT_SESSION_PROMPT*` files describe earlier bounded experiment scopes. Engineering reviews record evolving decisions from rendering to readiness, Track, lifecycle, Mixer, Send and encoder-route inspection. Root README is the latest runtime frontier and selected continuation; historical “next test” paragraphs are not simultaneously active commitments.

The review workspace's main-project prompts are proposed changes/instructions, not proof that the main project performed them. The storage prompt is associated with a separately active task; the older review and UI prompts must be reconciled with subsequent primary results. No feasibility estimate for a modified or replacement OS has been established by these plans.

## Experiment-directory census

The appendix below inventories observed top-level experiment directories. Linked handoffs/runbooks explain scope; directories without one are subordinate arms, working copies, preparation, or archival records and cannot independently establish success. Outcome confidence comes from the baseline and gaps registers, not directory names.

| Experiment directory | Available entry record |
|---|---|
| [arm32-statfs-20261008] `experiments/arm32-statfs-20261008` (evidence not published) | [HANDOFF.md] `experiments/arm32-statfs-20261008/HANDOFF.md` (evidence not published) |
| [atomic-startup-20261008-correction] `experiments/atomic-startup-20261008-correction` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [atomic-startup-20261008-diagnostic] `experiments/atomic-startup-20261008-diagnostic` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [atomic-startup-20261008-session] `experiments/atomic-startup-20261008-session` (evidence not published) | [HANDOFF.md] `experiments/atomic-startup-20261008-session/HANDOFF.md` (evidence not published) |
| [audit-remediation-20261009] `experiments/audit-remediation-20261009` (evidence not published) | [HANDOFF.md] `experiments/audit-remediation-20261009/HANDOFF.md` (evidence not published) |
| [completion-consumer-live-20261009] `experiments/completion-consumer-live-20261009` (evidence not published) | [HANDOFF.md] `experiments/completion-consumer-live-20261009/HANDOFF.md` (evidence not published) |
| [completion-consumer-preparation-20261009] `experiments/completion-consumer-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/completion-consumer-preparation-20261009/HANDOFF.md` (evidence not published) |
| [completion-listener-integration-20261009] `experiments/completion-listener-integration-20261009` (evidence not published) | [HANDOFF.md] `experiments/completion-listener-integration-20261009/HANDOFF.md` (evidence not published) |
| [cooperative-font-20261008] `experiments/cooperative-font-20261008` (evidence not published) | [HANDOFF.md] `experiments/cooperative-font-20261008/HANDOFF.md` (evidence not published) |
| [cooperative-select-20261008] `experiments/cooperative-select-20261008` (evidence not published) | [HANDOFF.md] `experiments/cooperative-select-20261008/HANDOFF.md` (evidence not published) |
| [csv-pointer-20261008] `experiments/csv-pointer-20261008` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [csv-pointer-20261008-retry] `experiments/csv-pointer-20261008-retry` (evidence not published) | [HANDOFF.md] `experiments/csv-pointer-20261008-retry/HANDOFF.md` (evidence not published) |
| [deadline-layout-chain-20261008] `experiments/deadline-layout-chain-20261008` (evidence not published) | [HANDOFF.md] `experiments/deadline-layout-chain-20261008/HANDOFF.md` (evidence not published) |
| [deadline-layout-chain-20261008-a1] `experiments/deadline-layout-chain-20261008-a1` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [deadline-layout-chain-20261008-a2] `experiments/deadline-layout-chain-20261008-a2` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [drawable-input-20261008] `experiments/drawable-input-20261008` (evidence not published) | [HANDOFF.md] `experiments/drawable-input-20261008/HANDOFF.md` (evidence not published) |
| [efficiency-review-20261008] `experiments/efficiency-review-20261008` (evidence not published) | [HANDOFF.md] `experiments/efficiency-review-20261008/HANDOFF.md` (evidence not published) |
| [efficiency-review-20261008-diagnostic] `experiments/efficiency-review-20261008-diagnostic` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [efficiency-review-20261008-repeat] `experiments/efficiency-review-20261008-repeat` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [emulation-20261007] `experiments/emulation-20261007` (evidence not published) | [README.md] `experiments/emulation-20261007/README.md` (evidence not published) |
| [emulation-20261008] `experiments/emulation-20261008` (evidence not published) | [README.md] `experiments/emulation-20261008/README.md` (evidence not published) |
| [emulation-display-20261008-004011] `experiments/emulation-display-20261008-004011` (evidence not published) | [README.md] `experiments/emulation-display-20261008-004011/README.md` (evidence not published) |
| [emulation-display-20261008-011849] `experiments/emulation-display-20261008-011849` (evidence not published) | [README.md] `experiments/emulation-display-20261008-011849/README.md` (evidence not published) |
| [emulation-display-20261008-101605] `experiments/emulation-display-20261008-101605` (evidence not published) | [README.md] `experiments/emulation-display-20261008-101605/README.md` (evidence not published) |
| [emulation-startup-20261008-105916] `experiments/emulation-startup-20261008-105916` (evidence not published) | [README.md] `experiments/emulation-startup-20261008-105916/README.md` (evidence not published) |
| [expose-chain-20261008] `experiments/expose-chain-20261008` (evidence not published) | [HANDOFF.md] `experiments/expose-chain-20261008/HANDOFF.md` (evidence not published) |
| [four-hour-efficiency-review-20261008] `experiments/four-hour-efficiency-review-20261008` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614] `experiments/full-font-cache-20261008-1614` (evidence not published) | [HANDOFF.md] `experiments/full-font-cache-20261008-1614/HANDOFF.md` (evidence not published) |
| [full-font-cache-20261008-1614-a1] `experiments/full-font-cache-20261008-1614-a1` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-a2] `experiments/full-font-cache-20261008-1614-a2` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-a3] `experiments/full-font-cache-20261008-1614-a3` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-a4] `experiments/full-font-cache-20261008-1614-a4` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-c1] `experiments/full-font-cache-20261008-1614-c1` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-c2] `experiments/full-font-cache-20261008-1614-c2` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-c3] `experiments/full-font-cache-20261008-1614-c3` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [full-font-cache-20261008-1614-next-20261008-1712] `experiments/full-font-cache-20261008-1614-next-20261008-1712` (evidence not published) | [HANDOFF.md] `experiments/full-font-cache-20261008-1614-next-20261008-1712/HANDOFF.md` (evidence not published) |
| [full-font-cache-20261008-1614-pixel-20261008-1658] `experiments/full-font-cache-20261008-1614-pixel-20261008-1658` (evidence not published) | [HANDOFF.md] `experiments/full-font-cache-20261008-1614-pixel-20261008-1658/HANDOFF.md` (evidence not published) |
| [handoff-preparation-20261008-095741] `experiments/handoff-preparation-20261008-095741` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [handoff-preparation-20261008-105321] `experiments/handoff-preparation-20261008-105321` (evidence not published) | [README.md] `experiments/handoff-preparation-20261008-105321/README.md` (evidence not published) |
| [input-response-live-20261009] `experiments/input-response-live-20261009` (evidence not published) | [HANDOFF.md] `experiments/input-response-live-20261009/HANDOFF.md` (evidence not published) |
| [input-response-preparation-20261009] `experiments/input-response-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/input-response-preparation-20261009/HANDOFF.md` (evidence not published) |
| [ioctl-continuation-20261008] `experiments/ioctl-continuation-20261008` (evidence not published) | [HANDOFF.md] `experiments/ioctl-continuation-20261008/HANDOFF.md` (evidence not published) |
| [layout-access-20261008-1715] `experiments/layout-access-20261008-1715` (evidence not published) | [HANDOFF.md] `experiments/layout-access-20261008-1715/HANDOFF.md` (evidence not published) |
| [milestone-following-20261008] `experiments/milestone-following-20261008` (evidence not published) | [HANDOFF.md] `experiments/milestone-following-20261008/HANDOFF.md` (evidence not published) |
| [mixer-navigation-live-20261009-180208] `experiments/mixer-navigation-live-20261009-180208` (evidence not published) | [HANDOFF.md] `experiments/mixer-navigation-live-20261009-180208/HANDOFF.md` (evidence not published) |
| [mixer-navigation-preparation-20261009] `experiments/mixer-navigation-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/mixer-navigation-preparation-20261009/HANDOFF.md` (evidence not published) |
| [mixer-send-live-20261009-193048] `experiments/mixer-send-live-20261009-193048` (evidence not published) | [HANDOFF.md] `experiments/mixer-send-live-20261009-193048/HANDOFF.md` (evidence not published) |
| [mixer-send-preparation-20261009] `experiments/mixer-send-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/mixer-send-preparation-20261009/HANDOFF.md` (evidence not published) |
| [mixer-send-roster-live-20261009-200343] `experiments/mixer-send-roster-live-20261009-200343` (evidence not published) | [HANDOFF.md] `experiments/mixer-send-roster-live-20261009-200343/HANDOFF.md` (evidence not published) |
| [mixer-send-roster-preparation-20261009] `experiments/mixer-send-roster-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/mixer-send-roster-preparation-20261009/HANDOFF.md` (evidence not published) |
| [natural-dispatch-20261008] `experiments/natural-dispatch-20261008` (evidence not published) | [HANDOFF.md] `experiments/natural-dispatch-20261008/HANDOFF.md` (evidence not published) |
| [natural-dispatch-retry-20261008] `experiments/natural-dispatch-retry-20261008` (evidence not published) | [HANDOFF.md] `experiments/natural-dispatch-retry-20261008/HANDOFF.md` (evidence not published) |
| [offline-review-20261008-01] `experiments/offline-review-20261008-01` (evidence not published) | [README.md] `experiments/offline-review-20261008-01/README.md` (evidence not published) |
| [parallel-send-integration-20261009] `experiments/parallel-send-integration-20261009` (evidence not published) | [HANDOFF.md] `experiments/parallel-send-integration-20261009/HANDOFF.md` (evidence not published) |
| [parent-initialization-20261008-141426] `experiments/parent-initialization-20261008-141426` (evidence not published) | [HANDOFF.md] `experiments/parent-initialization-20261008-141426/HANDOFF.md` (evidence not published) |
| [parent-prompt-preparation-20261008-01] `experiments/parent-prompt-preparation-20261008-01` (evidence not published) | [HANDOFF.md] `experiments/parent-prompt-preparation-20261008-01/HANDOFF.md` (evidence not published) |
| [parent-stop-policy-20261008-145156] `experiments/parent-stop-policy-20261008-145156` (evidence not published) | [HANDOFF.md] `experiments/parent-stop-policy-20261008-145156/HANDOFF.md` (evidence not published) |
| [persistent-home-input-20261009] `experiments/persistent-home-input-20261009` (evidence not published) | [HANDOFF.md] `experiments/persistent-home-input-20261009/HANDOFF.md` (evidence not published) |
| [persistent-home-input-retry-20261009] `experiments/persistent-home-input-retry-20261009` (evidence not published) | [HANDOFF.md] `experiments/persistent-home-input-retry-20261009/HANDOFF.md` (evidence not published) |
| [post-font-counted-quantum-20261008] `experiments/post-font-counted-quantum-20261008` (evidence not published) | [HANDOFF.md] `experiments/post-font-counted-quantum-20261008/HANDOFF.md` (evidence not published) |
| [post-font-counted-quantum-20261008-repeat] `experiments/post-font-counted-quantum-20261008-repeat` (evidence not published) | [HANDOFF.md] `experiments/post-font-counted-quantum-20261008-repeat/HANDOFF.md` (evidence not published) |
| [post-parent-startup-20261008-150354] `experiments/post-parent-startup-20261008-150354` (evidence not published) | [HANDOFF.md] `experiments/post-parent-startup-20261008-150354/HANDOFF.md` (evidence not published) |
| [practical-startup-20261008-1542] `experiments/practical-startup-20261008-1542` (evidence not published) | [HANDOFF.md] `experiments/practical-startup-20261008-1542/HANDOFF.md` (evidence not published) |
| [practical-startup-20261008-1542-a1] `experiments/practical-startup-20261008-1542-a1` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [practical-startup-20261008-1542-a2] `experiments/practical-startup-20261008-1542-a2` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [practical-startup-20261008-1542-a3] `experiments/practical-startup-20261008-1542-a3` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [practical-startup-20261008-1542-a4] `experiments/practical-startup-20261008-1542-a4` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [practical-startup-20261008-1542-a5] `experiments/practical-startup-20261008-1542-a5` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [practical-startup-20261008-1542-a6] `experiments/practical-startup-20261008-1542-a6` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [project-manager-futex-20261009] `experiments/project-manager-futex-20261009` (evidence not published) | [HANDOFF.md] `experiments/project-manager-futex-20261009/HANDOFF.md` (evidence not published) |
| [quantum-replication-20261008] `experiments/quantum-replication-20261008` (evidence not published) | [HANDOFF.md] `experiments/quantum-replication-20261008/HANDOFF.md` (evidence not published) |
| [revised-startup-20261008] `experiments/revised-startup-20261008` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [revised-startup-20261008-analysis] `experiments/revised-startup-20261008-analysis` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [runtime-limit-fix-20261008] `experiments/runtime-limit-fix-20261008` (evidence not published) | [HANDOFF.md] `experiments/runtime-limit-fix-20261008/HANDOFF.md` (evidence not published) |
| [runtime-limit-review-20261008] `experiments/runtime-limit-review-20261008` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [send-identity-inspection-20261009] `experiments/send-identity-inspection-20261009` (evidence not published) | [HANDOFF.md] `experiments/send-identity-inspection-20261009/HANDOFF.md` (evidence not published) |
| [send-identity-live-20261009-200701] `experiments/send-identity-live-20261009-200701` (evidence not published) | [HANDOFF.md] `experiments/send-identity-live-20261009-200701/HANDOFF.md` (evidence not published) |
| [session-archive-20261008-010249] `experiments/session-archive-20261008-010249` (evidence not published) | [README.md] `experiments/session-archive-20261008-010249/README.md` (evidence not published) |
| [session-archive-20261008-011849] `experiments/session-archive-20261008-011849` (evidence not published) | [README.md] `experiments/session-archive-20261008-011849/README.md` (evidence not published) |
| [session-archive-20261008-101605] `experiments/session-archive-20261008-101605` (evidence not published) | [README.md] `experiments/session-archive-20261008-101605/README.md` (evidence not published) |
| [session-archive-20261008-105916] `experiments/session-archive-20261008-105916` (evidence not published) | [README.md] `experiments/session-archive-20261008-105916/README.md` (evidence not published) |
| [session-archive-20261008-parent-141426] `experiments/session-archive-20261008-parent-141426` (evidence not published) | [README.md] `experiments/session-archive-20261008-parent-141426/README.md` (evidence not published) |
| [session-archive-20261009-cooperative-select] `experiments/session-archive-20261009-cooperative-select` (evidence not published) | [README.md] `experiments/session-archive-20261009-cooperative-select/README.md` (evidence not published) |
| [startup-lifecycle-live-20261009-165946] `experiments/startup-lifecycle-live-20261009-165946` (evidence not published) | [HANDOFF.md] `experiments/startup-lifecycle-live-20261009-165946/HANDOFF.md` (evidence not published) |
| [startup-lifecycle-preparation-20261009] `experiments/startup-lifecycle-preparation-20261009` (evidence not published) | [HANDOFF.md] `experiments/startup-lifecycle-preparation-20261009/HANDOFF.md` (evidence not published) |
| [startup-throughput-20261008] `experiments/startup-throughput-20261008` (evidence not published) | [HANDOFF.md] `experiments/startup-throughput-20261008/HANDOFF.md` (evidence not published) |
| [startup-throughput-20261008-baseline] `experiments/startup-throughput-20261008-baseline` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [startup-throughput-20261008-main] `experiments/startup-throughput-20261008-main` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [startup-throughput-20261008-recovery] `experiments/startup-throughput-20261008-recovery` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [supervisor-cadence-20261008] `experiments/supervisor-cadence-20261008` (evidence not published) | [HANDOFF.md] `experiments/supervisor-cadence-20261008/HANDOFF.md` (evidence not published) |
| [supervisor-request-queue-20261009] `experiments/supervisor-request-queue-20261009` (evidence not published) | [HANDOFF.md] `experiments/supervisor-request-queue-20261009/HANDOFF.md` (evidence not published) |
| [syscall-boundary-startup-20261008] `experiments/syscall-boundary-startup-20261008` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [syscall-boundary-startup-20261008-retry] `experiments/syscall-boundary-startup-20261008-retry` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [timer-futex-20261009] `experiments/timer-futex-20261009` (evidence not published) | [HANDOFF.md] `experiments/timer-futex-20261009/HANDOFF.md` (evidence not published) |
| [ui-timer-review-20261009] `experiments/ui-timer-review-20261009` (evidence not published) | No top-level handoff/runbook; subordinate source/results inspected through its family records |
| [worker-resume-completion-20261009] `experiments/worker-resume-completion-20261009` (evidence not published) | [HANDOFF.md] `experiments/worker-resume-completion-20261009/HANDOFF.md` (evidence not published) |
