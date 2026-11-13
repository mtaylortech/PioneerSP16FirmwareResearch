# Research notes

Scrubbed working notes from the SP-16 firmware research, published so a
successor can see what was tried, what held up, and where each thread stopped.
These are **raw lab notes**, not polished findings — for the curated version
read [`../docs/findings.md`](../docs/findings.md) first, then come here for the
detail behind a specific claim.

Every note was copied from the research tree and scrubbed: absolute paths
rewritten, owner identity removed, links to unpublished evidence turned into
plain text marked `(evidence not published)`. See
[`EDIT-LOG.md`](EDIT-LOG.md) and [`LINK-REWRITE-LOG.csv`](LINK-REWRITE-LOG.csv)
for every change. No firmware, key, or binary is included anywhere.

## How to read the status labels

Each note below has a **status assigned by the editor** (not taken from the
note's own wording — most notes had no uniform status line). Labels, with the
only values used:

- **demonstrated-in-emulator** — shown to work in QEMU/Qiling, with stated limits.
- **static finding** — established by reading disassembly/strings, not by running.
- **host tool** — a tool or harness that runs on the research host, not the device.
- **prepared-not-run** — set up and ready, execution not performed.
- **partial** — some arms succeeded, others blocked; see the note.
- **blocked** — stopped at a named obstacle.
- **failed** — the attempt did not achieve its goal.
- **superseded** — later work replaced this.

Where a note's own outcome was unclear, the label is the editor's best read and
the entry says so. Nothing here asserts a result the note did not support.

## Contents

- **A — firmware catalog & tooling** · **B — 1.60 app-emulation startup** ·
  **C — UI / input** · **D — normalize** · **E1 — board-emulator sources** ·
  **F — effects (1.60)** below.
- [`E2-updater-usb-diagnostic-SUMMARY.md`](E2-updater-usb-diagnostic-SUMMARY.md)
  — six 1.50 updater/USB/diagnostic studies, **summary only** (owner decision).
- [`NO-WRITEUP-FOLDERS.md`](NO-WRITEUP-FOLDERS.md) — 45 experiment folders with
  no write-up (attempt/variant runs, early emulation, session archives).
- [`reviews/`](reviews/) — 52 engineering decision reviews + an internal
  adversarial audit. [`history/`](history/) — project state, evidence ledger,
  changelog and older handoffs (historical synthesis; older than some results).
  [`methods/`](methods/) — reusable skill methodology. [`LESSONS.md`](LESSONS.md)
  — cross-cutting lessons and dead ends.

---

## F — Effects (1.60) (1 note)

The evidence behind [`../docs/effects/`](../docs/effects/README.md), from an automated
worker/critic research loop (nine cycles, one hypothesis each, every result re-run by
an independent review pass). Published as the findings ledger, plus the method write-up [`methods/worker-critic-research-loop.md`](methods/worker-critic-research-loop.md). The nine per-cycle
logs are **not** published: their conclusions, refuted alternatives and evidence hashes
are all in the ledger, and the logs are mostly process (tool sessions, scratch paths)
(evidence not published).

| note | question → result | status (editor-assigned) |
|---|---|---|
| [findings-ledger](F-effects/findings-ledger.md) | How does the 1.60 app process effects, and can each effect be reconstructed bit-exactly? → Audio path, effect selection and the `EffectBase` interface established. LoFi, multi-mode filter, 2-band EQ, Phaser and the shared oscillator reconstructed, with Python models bit-exact to the routines run in a single-function emulator. Chorus/Flanger cores confirmed; other effects not started. | demonstrated-in-emulator (single function); static finding for the call chain |


## A — Firmware catalog & tooling (6 notes)

| note | question → result | status (editor-assigned) |
|---|---|---|
| [firmware-catalog](A-firmware-tooling/firmware-catalog-20261010.md) | Can the six releases be bound to verified hashes and compared without touching firmware? → Six verified release bindings, four extractions, five component comparisons, a 1.30→1.31 reader pilot; no firmware/emulator/repack run. | static finding |
| [feature-trace-skill](A-firmware-tooling/feature-trace-skill-20261010.md) | Can a reusable feature-trace workflow reuse static tools while preserving artifact identity and honest validation? → Implemented and validated as a repo skill. | host tool |
| [rea-ghidra-comparison](A-firmware-tooling/rea-ghidra-comparison-20261010-202454.md) | Does REA 6.3.0 reproduce the corrected Ghidra results? → All 524 reference byte pairs and four function bodies match; default analysis didn't repeat one earlier consolidation. Keep both workflows. | host tool |
| [rea-marginal-workflow](A-firmware-tooling/rea-marginal-workflow-20261010-205205.md) | Does REA give an end-to-end discovery speedup? → No accepted speedup; both default imports missed required functions. Retain REA for interactive queries only. | host tool |
| [sp16-skill-contracts](A-firmware-tooling/sp16-skill-contracts-20261011.md) | Can an ARM32 declaration + effect contract catch a layout mistake while keeping missing evidence visible? → Delivered a stdlib layout/comparison helper + skill diff. | host tool |
| [sp16-skill-context-fix](A-firmware-tooling/sp16-skill-context-fix-20261011.md) | Can malformed context or JSON type changes falsely match in `slice_contracts.compare`? → Three pre-correction false matches reproduced, then fixed. | host tool |

## E1 — Board-emulator sources (3 notes)

These are the three studies the published
[`emulation/board/`](../emulation/board/) consolidates. One passage about
producing the VM-only update carrier was replaced with a one-line summary
(logged in [`EDIT-LOG.md`](EDIT-LOG.md)); the boot/persistence results are
intact.

| note | question → result | status (editor-assigned) |
|---|---|---|
| [persistent-boot-update](E1-board-emulator/persistent-boot-update-150-20261011.md) | Can the original 1.50 kernel + USB update path run in a virtual board? → Discovery, checker, decrypt loop, ISO mount and the original diagnostic caller executed; a faithful, usable UI was not reached. | partial |
| [original-rootfs-control](E1-board-emulator/original-rootfs-control-150-20261011.md) | Does original storage boot + app launch reproduce under an explicit SD adapter? → Yes through the adapter; control, diagnostic and cold-boot arms all reached the same absent-MTD checkpoint. | partial |
| [arm-drawing-retention](E1-board-emulator/arm-drawing-retention-150-20261011.md) | Can the VM diagnostic draw to and read back the framebuffer, and does state survive a cold boot? → Draw/readback/retention demonstrated for the declared framebuffer; app continuation partial. | partial |

## C — UI / input (17 notes)

Single-input emulator experiments on the 1.60 app: HOME/MIXER navigation, the
Send footer, and panel/record paths. Most pair a `-preparation` note (offline
setup) with a `-live` note (one authorized guest run). Several Send-mutation
and async-model items were deliberately left unready or excluded; the notes say
so and the labels follow them.

| note | question → result | status (editor-assigned) |
|---|---|---|
| [input-response-preparation](C-ui-input/input-response-preparation-20261009.md) | Bind fresh readiness + stable HOME to a one-input gate while false verifiers fail the process? → Implemented firmware-free in an independent copy. | prepared-not-run |
| [input-response-live](C-ui-input/input-response-live-20261009.md) | Does one tagged Track-2 click reach original handling and change selection? → Yes. | demonstrated-in-emulator |
| [mixer-navigation-preparation](C-ui-input/mixer-navigation-preparation-20261009.md) | Does one reversible HOME→MIXER tap reach the handler and draw the Mixer screen? → Static prep complete; live run passed and closed. | prepared-not-run |
| [mixer-navigation-live](C-ui-input/mixer-navigation-live-20261009-180208.md) | Same question, live. → One tap consumed exactly, reached the original control and drew the Mixer screen (600 s guest). | demonstrated-in-emulator |
| [mixer-send-preparation](C-ui-input/mixer-send-preparation-20261009.md) | Ready a channel-1 Send-amount mutation test? → 56 offline checks pass; the positive mutation test remains unready. | prepared-not-run |
| [mixer-send-live](C-ui-input/mixer-send-live-20261009-193048.md) | Does the Send-amount gesture reach the original setter and redraw? → One authorized guest + gesture ran; see note for outcome. | partial |
| [mixer-send-roster-preparation](C-ui-input/mixer-send-roster-preparation-20261009.md) | Take two same-owner Send-footer identity snapshots offline? → Prep complete. | prepared-not-run |
| [mixer-send-roster-live](C-ui-input/mixer-send-roster-live-20261009-200343.md) | Which mapped listeners belong to the active Send footer? → One guest ran; zero Send listeners captured in the window (see note). | partial |
| [send-identity-inspection](C-ui-input/send-identity-inspection-20261009.md) | Offline Send-identity package; is live integration validated? → Prep complete; live unvalidated, mutation readiness withheld. | prepared-not-run |
| [send-identity-live](C-ui-input/send-identity-live-20261009-200701.md) | Capture two same-owner listener snapshots live? → Passed; full 600 s observation, clean closure. | demonstrated-in-emulator |
| [panel-record-contract](C-ui-input/panel-record-contract-20261009.md) | Validate a panel queue/read/epoll adapter offline? → 78 + 39 checks pass; adapter uninstalled/live-unvalidated. | prepared-not-run |
| [panel-delivery-preparation](C-ui-input/panel-delivery-preparation-20261009.md) | Ready the panel overlay + mutation? → 36 controls pass; overlay uninstalled, mutation unready. | prepared-not-run |
| [panel-passive-live](C-ui-input/panel-passive-live-20261009-225409.md) | Passive Send snapshot during a guest run? → Observed registrations, but failed on an observer integration bug; stopped early. | failed |
| [panel-passive-corrected-live](C-ui-input/panel-passive-corrected-live-20261009-230743.md) | Re-run after the fix? → Passed; 600 s, 24 checks, one gated tap, clean shutdown. | demonstrated-in-emulator |
| [persistent-home-input](C-ui-input/persistent-home-input-20261009.md) | Locate the first missing delivery/dispatch boundary for one click after stable pixels? → Sole attempt failed before emulator construction. | failed |
| [persistent-home-input-retry](C-ui-input/persistent-home-input-retry-20261009.md) | Retry. → Guest completed 600 s, bounded-stop/exit 0, clean closure. | demonstrated-in-emulator |
| [parallel-send-integration](C-ui-input/parallel-send-integration-20261009.md) | Resolve the positive Send edit via an async model? → Unresolved; async assignment hit a safety restriction, findings excluded as unverified. | blocked |

## B — 1.60 app-emulation startup (38 notes)

The largest thread: driving the 1.60 application forward under Qiling/QEMU from
launch toward a drawable UI, one bounded observation at a time. Recurring
sub-topics are startup scheduling/quanta, font-cache completion, the
layout/Expose/paint chain, futex/timer waits, and worker-completion lifecycle.
The headline across the thread: **startup was advanced a long way and many
boundaries were verified statically and in-emulator, but a faithful, usable,
drawable UI was never reached.**

| note | question → result | status (editor-assigned) |
|---|---|---|
| [arm32-statfs](B-app-startup/arm32-statfs-20261008.md) | Does fixing ARM32 statfs/fstatfs let storage init return and reach drawable output? → Filesystem repair passed in both guests; main reached an original boundary, no drawable UI. | partial |
| [atomic-startup-session](B-app-startup/atomic-startup-20261008-session.md) | What causes the fast whole-main failure; can scheduling advance startup? → Two observations; neither resolved it (see note). | partial |
| [audit-remediation](B-app-startup/audit-remediation-20261009.md) | Prepare a trustworthy bounded observation of the startup lifecycle. → Firmware-free harness + controls prepared; nothing ran. | prepared-not-run |
| [startup-throughput](B-app-startup/startup-throughput-20261008.md) | Can one bounded run spend much more time advancing startup? → Yes: 20 ms slices through the font scan, then restore larger quanta. | demonstrated-in-emulator |
| [efficiency-review](B-app-startup/efficiency-review-20261008.md) | Retain earlier startup, check repeatability, separate emulator exceptions from expiry. → Repeatability checked; broad-mode fault captured. | static finding |
| [drawable-input](B-app-startup/drawable-input-20261008.md) | Do enclosing returns lead to drawable output/input in the guest window? → Init advanced, then a captured fault prevented completion. | blocked |
| [ioctl-continuation](B-app-startup/ioctl-continuation-20261008.md) | Does the invalid-descriptor ioctl guard let the caller return and the window paint? → Guard returned; main consumed ten X events; no paint. | partial |
| [expose-chain](B-app-startup/expose-chain-20261008.md) | Where does Expose stop between XFindContext, dispatch and redraw? → It doesn't stop there; one Expose reached every boundary. | static finding |
| [natural-dispatch](B-app-startup/natural-dispatch-20261008.md) | Which event types/callbacks run after guarded ioctl? → Untested; the sole guest failed before that phase. | failed |
| [natural-dispatch-retry](B-app-startup/natural-dispatch-retry-20261008.md) | Retry. → A natural 800×480 Expose reached byte-validated callbacks. | demonstrated-in-emulator |
| [cooperative-font](B-app-startup/cooperative-font-20261008.md) | Can cooperative early/font scheduling preserve progress without async stops? → Yes in this bounded pair; retain the approach. | demonstrated-in-emulator |
| [cooperative-select](B-app-startup/cooperative-select-20261008.md) | Does cooperative select execute the pending redraw? → Select completes, but no paint/non-black UI; dirty region remains. | partial |
| [csv-pointer-retry](B-app-startup/csv-pointer-20261008-retry.md) | Does UTF conversion get an unaligned allocation, or lose alignment before publication? → See note (alignment trace). | static finding |
| [deadline-layout-chain](B-app-startup/deadline-layout-chain-20261008.md) | Can 5-minute observations finalize reliably; which code loads skin layouts? → Two guests; layout loader identified. | static finding |
| [full-font-cache](B-app-startup/full-font-cache-20261008-1614.md) | Can full font discovery complete within 180 s? → Not met here; a 5-minute config saved for later. | partial |
| [full-font-cache-next](B-app-startup/full-font-cache-20261008-1614-next-20261008-1712.md) | Does the finite 20 ms main-only font-scan slice complete discovery? → Yes, within 180 s; all faces returned 0. | demonstrated-in-emulator |
| [full-font-cache-pixel](B-app-startup/full-font-cache-20261008-1614-pixel-20261008-1658.md) | Reproducible? → Full font discovery passed within 180 s twice. | demonstrated-in-emulator |
| [layout-access](B-app-startup/layout-access-20261008-1715.md) | Which callers check skin layout paths after the font-manager return? → All 33 checks returned through one address; decoded the branch. | static finding |
| [milestone-following](B-app-startup/milestone-following-20261008.md) | Does the enclosing routine return and continue into later construction? → Matched return and genuine caller continuation. | static finding |
| [post-font-counted-quantum](B-app-startup/post-font-counted-quantum-20261008.md) | Does a 10× larger post-font main slice advance resource construction + the FxMasterLofiView constructor? → Unresolved; control stalled during fonts. | partial |
| [post-font-counted-quantum-repeat](B-app-startup/post-font-counted-quantum-20261008-repeat.md) | Repeat. → Partial performance gain; retain treatment. | partial |
| [quantum-replication](B-app-startup/quantum-replication-20261008.md) | Does the larger post-font count again extend progress? → Inconclusive (order effect; see note). | partial |
| [startup-lifecycle-preparation](B-app-startup/startup-lifecycle-preparation-20261009.md) | Distinguish completed init from responsive HOME with a pending frame? → Firmware-free mapping through factory/vtable slots. | static finding |
| [startup-lifecycle-live](B-app-startup/startup-lifecycle-live-20261009-165946.md) | Verify the startup boundary in a no-input guest? → Yes: initializer returned at 262 s, continuation executed. | demonstrated-in-emulator |
| [parent-initialization](B-app-startup/parent-initialization-20261008-141426.md) | Parent-init runtime experiment. → Incomplete; a vfork-denial predicate stopped the guest. | blocked |
| [parent-prompt-preparation](B-app-startup/parent-prompt-preparation-20261008-01.md) | Save a self-contained prompt + estimate for the next parent-init run. → Prepared. | prepared-not-run |
| [parent-stop-policy](B-app-startup/parent-stop-policy-20261008-145156.md) | Does the top-level parent helper complete? → Yes: returned into its caller at 171 s. | demonstrated-in-emulator |
| [post-parent-startup](B-app-startup/post-parent-startup-20261008-150354.md) | After parent init, is full startup/drawable UI reached? → Parent init + constructor completed; full startup unconfirmed. | partial |
| [practical-startup](B-app-startup/practical-startup-20261008-1542.md) | Do wider startup constructors return and resource loading progress? → 5 of 6 attempts reached main; full startup/UI unconfirmed. | partial |
| [project-manager-futex](B-app-startup/project-manager-futex-20261009.md) | Does honoring ProjectManager's finite WAIT advance project loading? → Expiry + worker continuation established; load completion not. | partial |
| [timer-futex](B-app-startup/timer-futex-20261009.md) | Does honoring the Juce Timer finite FUTEX_WAIT resume painting? → Timer processing + original non-black painting resumed; full startup not. | partial |
| [supervisor-cadence](B-app-startup/supervisor-cadence-20261008.md) | Can supervision cost less while keeping prompt child detection + bounded shutdown? → A/B with inert helpers; cadence validated. | host tool |
| [supervisor-request-queue](B-app-startup/supervisor-request-queue-20261009.md) | Which request boundary advances/blocks project loading? → The observed request swapped, dispatched and returned (resume request). | static finding |
| [worker-resume-completion](B-app-startup/worker-resume-completion-20261009.md) | Follow main async submission into worker completion before tagged input? → Guest completed 600 s, bounded-stop, clean closure. | demonstrated-in-emulator |
| [completion-consumer-preparation](B-app-startup/completion-consumer-preparation-20261009.md) | Ready the no-file worker-completion consumer test? → Decision saved; prep complete. | prepared-not-run |
| [completion-consumer-live](B-app-startup/completion-consumer-live-20261009.md) | Does main accept the no-file worker completion and set readiness? → Yes, in original execution, at 255 s. | demonstrated-in-emulator |
| [completion-listener-integration](B-app-startup/completion-listener-integration-20261009.md) | Does the lifetime correction install + dispatch the listener with matched returns? → Eight firmware-free controls pass. | prepared-not-run |
| [runtime-limit-fix](B-app-startup/runtime-limit-fix-20261008.md) | Does observation duration survive the watchdog spawn path and launch gates? → Removes stale offsets; gates pass. | host tool |

## D — Normalize (33 notes)

A deep static trace of the 1.50/1.60 "Normalize whole recording → Keep" path:
how a changed `PlaybackData`/sample reaches persistent project storage, and the
save/activation, editor-lifecycle, and reader-cache machinery around it. Most
notes are time-boxed static tranches that "stop at the first decisive gap" —
an honest-stopping discipline (see [`LESSONS.md`](LESSONS.md)). The integrated
Keep transaction was modeled on the host but never proved on firmware.

| note | question → result | status (editor-assigned) |
|---|---|---|
| [project-flush](D-normalize/project-flush-20261010-075605.md) | When does a changed `audioSourceUrl` reach persistent storage, and via which destinations? → Explicit Save reaches recursive serialization; destinations mapped. | static finding |
| [provider-binding](D-normalize/provider-binding-20261010-072803.md) | Close the context-provider gap for the HexaTrack construction route? → Closed; Ghidra + original-byte checks establish how SAVE & REPLACE gets its provider. | static finding |
| [reader-reopen](D-normalize/reader-reopen-20261010-081156.md) | After sample assignment, does the player reload the reader, and does same-path replacement yield fresh audio? → Static chain connects assignment to reload; same-path caveat. | static finding |
| [reader-cache-fixture](D-normalize/reader-cache-fixture-20261010-082651.md) | After replacing a sample, do readers produce fresh decoded audio? → Original ARM reader/cache reproduces the stale same-path cache behavior. | static finding |
| [normalization-save-activation-step05](D-normalize/normalization-save-activation-20261010-step05.md) | Which branches persist the changed reference on Save activation? → Bounded static activation result. | static finding |
| [normalization-save-control-step05b](D-normalize/normalization-save-control-20261010-step05b.md) | Save-control discovery tranche. → Completed; verification included. | static finding |
| [normalization-save-op5-identity-step05c](D-normalize/normalization-save-op5-identity-20261010-step05c.md) | Save op-5 identity tranche. → Discovery closed within the allowance. | static finding |
| [normalization-save-menu-item-step05d](D-normalize/normalization-save-menu-item-20261010-step05d.md) | Save menu-item path. → Bounded static result. | static finding |
| [normalization-save-list-input-step05e](D-normalize/normalization-save-list-input-20261010-step05e.md) | How does the Project controller receive the event; what permits row activation? → Partial; core direct delivery mapped. | partial |
| [normalization-save-encoder-task-step05f](D-normalize/normalization-save-encoder-task-20261010-step05f.md) | Bind the encoder array to objects, follow the press Task to the Project receiver. → Both offline chains qualified. | static finding |
| [normalization-auto-deferred-step06](D-normalize/normalization-auto-deferred-20261010-step06.md) | Which branches persist the same changed reference (6-body matrix)? → Accepted for stated scope. | static finding |
| [normalization-destinations-step07](D-normalize/normalization-destinations-20261010-step07.md) | Where do accepted project/resume routes write? → Destination ledger done; full confinement blocked. | partial |
| [normalization-writer-results-step08](D-normalize/normalization-writer-results-20261010-step08.md) | What do connected writers check/ignore? → Bounded result; stream error handling + durability unresolved. | partial |
| [normalization-stream-keep-services-step08b](D-normalize/normalization-stream-keep-services-20261010-step08b.md) | Design basis for integrated Keep? → Recommends an audio-only same-path transaction; Keep unproved. | static finding |
| [normalization-real-owner-stop-release-step09a](D-normalize/normalization-real-owner-stop-release-20261010-step09a.md) | Owner stop/release edge for a selected symbol. → Static tranche; stopped at a decisive missing edge. Step 09 partial. | partial |
| [normalization-editor-unload-listener-step09b](D-normalize/normalization-editor-unload-listener-20261010-step09b.md) | Does the editor +0x100 unload listener connect to admission? → Stopped at first decisive gap. | partial |
| [normalization-scheduler-contract-step09c](D-normalize/normalization-scheduler-contract-20261010-step09c.md) | What does the scheduler at 0x0bd554 (+0x10) do? → Stopped at first decisive gap. | partial |
| [normalization-task-completion-exclusion-step09d](D-normalize/normalization-task-completion-exclusion-20261010-step09d.md) | Does the completion machinery expose an editor-accessible hook? → Stopped at first decisive gap. | partial |
| [normalization-ack-gate-review-step09e](D-normalize/normalization-ack-gate-review-20261010-step09e.md) | Does the candidate ack + matching-load gate cover producers and preserve lifetime? → Static-only review. | static finding |
| [normalization-pending-editor-load-settlement-step09f](D-normalize/normalization-pending-editor-load-settlement-20261010-step09f.md) | Pending editor-load settlement. → Static tranche (see successor handoff). | partial |
| [normalization-editor-lifecycle-admission-step09g](D-normalize/normalization-editor-lifecycle-admission-20261010-step09g.md) | Editor-lifecycle admission edge. → Bounded discovery. | partial |
| [normalization-owner-roster-contract-step09h](D-normalize/normalization-owner-roster-contract-20261010-step09h.md) | Owner/roster contract. → Bounded discovery tranche. | partial |
| [normalization-lifecycle-decision](D-normalize/normalization-lifecycle-decision-20261010.md) | Lifecycle-integration decision point. → Current approach blocked (recorded). | blocked |
| [normalization-member-observation](D-normalize/normalization-member-observation-20261011.md) | Capture roster members in the construction window. → Zero members present; defer integrated firmware work. | blocked |
| [normalization-native-preview-boundary](D-normalize/normalization-native-preview-boundary-20261011.md) | Does native SimplePlayer candidate admission/playback settle? → ARM caller ran; admission/playback/stop unproved. | partial |
| [normalization-host-core](D-normalize/normalization-host-core-20261011.md) | Host core model of the transaction. → Saved locally, uncommitted; host-only. | host tool |
| [host-normalization-integration](D-normalize/host-normalization-integration-20261011.md) | End-to-end Select→Normalize→Keep on the host subset? → HOST_INTEGRATION_OK within the disposable host subset. | host tool |
| [keep-fault-probe](D-normalize/keep-fault-probe-20261010-065129.md) | Transaction fault model. → Eight host cases pass independent verification; not a shipped ARM impl. | host tool |
| [keep-recovery-qualification](D-normalize/keep-recovery-qualification-20261011.md) | Qualify the Keep recovery primitive. → 84/84 cases pass in the declared envelope. | host tool |
| [keep-recovery-acl-verifier-fix](D-normalize/keep-recovery-acl-verifier-fix-20261011.md) | Can the oracle tell empty ACLs from inspection faults? → verify.py changed only ACL inspection; dependency preserved. | host tool |
| [sample-lifecycle-reconstruction](D-normalize/sample-lifecycle-reconstruction-20261010.md) | Connect accepted lifecycle slices into a version-matched reconstruction? → First sparse roster observation attempted. | partial |
| [sample-lifecycle-observer-coverage](D-normalize/sample-lifecycle-observer-coverage-20261011.md) | Cover the 1.60 sample-lifecycle observer. → See note. | partial |
| [observer-callback-readiness-review](D-normalize/observer-callback-readiness-review-20261011.md) | Does the coverage repair make the result-2 callback comparison ready? → No; prepared but not installed/repinned. | prepared-not-run |
