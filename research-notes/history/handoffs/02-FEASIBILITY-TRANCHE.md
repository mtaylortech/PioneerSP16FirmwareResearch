<!-- source: docs/handoffs/2026-10-10-revision2-sequence/02-FEASIBILITY-TRANCHE.md | scrubbed -->

# P02 — Normalization feasibility tranche

**Status: READY FOR NEXT STEP**  
**Actual output root: docs/handoffs/2026-10-10-revision2-sequence**  
**Actual handoff: docs/handoffs/2026-10-10-revision2-sequence/02-FEASIBILITY-TRANCHE.md**  
Updated October 10, 2026, America/Chicago.

The active first feature is **recorded-sample peak normalization**, per the revised [feature contract] `01-FEATURE-CONTRACT.md` (evidence not published). The owner's latest direction replaces timing-first work with adding a working normalization feature. This rewrite carries forward the established budget and review preferences; it does not start analysis, construct a candidate or launch tests.

## Owner selections and provenance

The retained normalization workflow is Select sample → Normalize → Keep/Discard. Use one uniform gain over the complete recording, preserve waveform shape/stereo balance, introduce no clipping and leave silence unchanged. Keep permanently rewrites the selected sample file and closes the function; Discard preserves the original file/audio. Playback may stop during processing. The existing OS/functions and sample/project formats remain usable. Eventual distribution is intended; full OS replacement is not mandatory or selected.

The owner subsequently selected explicit deliverables and elapsed time as the budget basis; no more than 15 minutes per individual future test unless there is a specific reason for longer; review choices of narrowing scope or considering a different technical approach; use of available sources, including online sources; and review when the report is complete. The initially selected 12-minute feasibility-report budget was explicitly increased to **16 minutes** by the owner's later request on October 10, 2026.

The explicit request to rewrite the plan for normalization changes the question and report subject. The current 16-minute ceiling, source permission, review choices and general per-test limit apply. The earlier 60-second stable-timing observation, MPC comparison and new timing guarantees are deferred. No 60-second normalization test duration is invented.

The product preference is a handful of functions done well rather than many new options. No particular original function is selected for removal. Internal sample deletion remains the named, inactive fallback; it does not replace normalization without a separate owner decision.

## Permitted later questions and routes

The decision-changing question is whether a bounded addition/modification to SP-16 software can deliver the selected normalization workflow, and what missing evidence prevents selecting the smallest credible next test.

Within the later read-only tranche, assess only what is indispensable to that question:

- What existing evidence or available sources establish stock normalization support and the selected sample/file/UI boundary?
- Can the complete selected recording be identified and decoded/scaled without changing its format or unrelated data?
- What attachment, loaded-buffer/shared-reference and selected-file-write boundaries would be needed for Normalize, Keep and Discard?
- What remains unknown about ceiling/accuracy, storage failures/recovery, actual playback and relevant regressions, and what smallest subsequent test would discriminate a candidate route?

These are research questions, not answered findings or an architecture choice. Permitted methods are focused read-only local/static inspection and available source/web research under a later submitted analysis scope. Compare a data/service/localized application change only when evidence makes it relevant to normalization. No presumed API, writable route or safe-write mechanism is accepted without evidence.

## Exclusions

Timing optimization, MIDI-clock qualification, MPC groove comparison, broad Send continuation, extra-feature catalogues and broad OS/platform replacement are outside this first tranche. Whole-machine emulation or rebuilding is not a default prerequisite; it needs a normalization-specific decision-changing reason and review if it exceeds the selected scope.

Current Prompt 2 is planning only. The owner's latest rewrite request authorizes editing these two sequence handoffs; the review folder and other project records remain unchanged. No source/tool/firmware changes, restoration, code/candidate construction, tests/builds/installations, runtime/hardware, Git mutation, delegation, purchase, publication or message dispatch follows. Permission to consult online sources in later analysis does not require web research during this rewrite.

## Ceiling, accounting and review

| Field | Recorded selection |
|---|---|
| Ceiling | **One brief normalization feasibility report within 16 minutes (960 seconds) total elapsed time.** This is a limit on effort, not a completion estimate or promise of a working feature. |
| Deliverable | Report the available evidence and limits, the smallest supported normalization route or unresolved route question, missing acceptance/integration/write/recovery prerequisites, and the smallest proposed next test. Include narrow/pivot options. The report may leave feasibility unresolved. |
| Accounting | The later separately authorized feasibility-stage clock starts at commencement and includes preparation, source reading, analysis and reporting. Pauses add no elapsed allowance. This planning rewrite precedes that stage. |
| Consumed | **0 of 960 seconds** in the future feasibility stage; no sustained feature analysis has begun. |
| Remaining | **960 seconds and one report** before that stage starts. Record actual consumption when it runs. |
| Equipment/resources | No purchases, paid-service or equipment-spending allowance is authorized. Research time is distinct from spending. |
| Review | At report completion. If the ceiling is reached first, stop sustained investigation and report available findings/unknowns then; success is not required for review. |
| Review choices | Narrow the scope or consider a different technical route/architecture. Neither may silently discard the Keep/Discard behavior or original-function preservation contract. |
| Future individual tests | Normally no more than **15 minutes**, unless a specific reason supports longer. This is a retained constraint for separately authorized tests, not permission to run one. An enclosing total limit remains controlling. |

Successful normalization, virtualization startup and physical integration are not required outputs of this read-only tranche. Do not turn the owner's desired functioning feature into an unlimited setup or implementation allowance.

## Later preparatory fit

| Step | Fit and limit |
|---|---|
| Chat 3 indispensable preservation-record reconciliation | May proceed under its own submitted scope, even with test-specific unknowns. No restoration or sustained feasibility analysis; it does not start this future stage's clock. |
| Focused stock/sample/reference and observation-contract inspection | Fits the later 16-minute tranche when needed to assess actual normalization behavior and evidence. Prefer existing records; no live acquisition here. |
| Read-only sample/UI/file boundary and candidate-route assessment | Fits only the selected normalization question and report budget. Record missing mechanism/write/recovery evidence rather than constructing it. |
| Numerical acceptance, Keep/Discard, error and playback test design | A smallest-test proposal fits the report. Exact peak ceiling/error, formats, buffers/references and failure policy must be fixed before applicable tests. |
| Candidate implementation, fixture construction, controls, guest or physical tests, persistent writes | Requires separately submitted scope and applicable execution/preservation/recovery prerequisites. This document grants none. |

## Renewal and stop rule

Stop sustained investigation at 960 seconds. Report the established evidence, actual consumption, unresolved questions and narrow/pivot choices. An unexpected dependency needing a new route, spending, greater effort or changed preservation boundary triggers review before expansion.

Renewal requires **an explicit owner decision, a new decision-changing uncertainty, and renewed finite questions/routes, limits/accounting and review point**. Unresolved tracing cannot renew its own allowance. A read-only feasibility decision does not authorize construction or execution of a candidate. A route selection remains conditional until applicable mechanism, access, cost and recovery evidence exists.

## Reference identities and evidence limits

[AGENTS.md] `AGENTS.md` (evidence not published), [README.md] `README.md` (evidence not published) and its [latest experiment handoff] `experiments/panel-record-contract-20261009/HANDOFF.md` (evidence not published) were read. Existing startup/UI progress proves neither normalization nor real playback/sample persistence.

The prior Chat 2 read-only identity check matched Chat 1's approved references:

| Reference-only document | Approved and observed SHA-256 |
|---|---|
| [Master roadmap] `Review/04-MASTER-ROADMAP.md:48` (evidence not published) | e78fc1b090da2a942075e14783b042bbc93dce0c7aeea4786fb35d3370fd170d |
| [Prioritized actions] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:9` (evidence not published) | 2fa1f75ed45da843fe44d9f4b160ec896591be1ad6d65f357082e1ba07408dfa |

Those rules require a bounded owner tranche before sustained analysis, prefer the smallest discriminating investigation, and distinguish conditional [M06 selection] `Review/04-MASTER-ROADMAP.md:170` (evidence not published) from demonstrated mechanisms or implementation authority. No reference roadmap is edited or newly audited during this rewrite.

## Handoff to chat 3

- **Actual root:** docs/handoffs/2026-10-10-revision2-sequence.
- **Actual path:** docs/handoffs/2026-10-10-revision2-sequence/02-FEASIBILITY-TRANCHE.md.
- **Feature:** working recorded-sample normalization, with permanent selected-file change on Keep and original-file/audio preservation on Discard.
- **Tranche:** READY FOR NEXT STEP for later read-only normalization feasibility; one report within 16 elapsed minutes, including preparation/reporting. **0 consumed / 960 seconds remaining.**
- **Review:** report completion or mandatory stop at the cap; narrow or consider a different approach. No spending authorized.
- **Pending test decisions:** target/release/access and stock support; exact peak ceiling/error, format/size and near-silence envelope; shared-reference/buffer behavior; safe Keep/error/recovery; loading/UI integration, actual playback and regression coverage.
- **Deferred:** timing improvement, its 1 ms guarantee and 60-second timing observation. Existing sequencing/MIDI functionality remains preserved.
- **Next boundary:** Chat 3 may reconcile existing indispensable preservation records under its own submitted scope; it must not restore assets or begin sustained feasibility analysis. Prompt 3 is not dispatched.

**Scope record:** Chat 2 inspected local records, checked the two cited identities and wrote its handoff. The latest owner request authorized revising both sequence handoffs around normalization. This rewrite changes only those two planning files. No feature analysis, code/tool/firmware change, tests, runtime/hardware, Git mutation, delegation, cross-chat message, spending or new web research occurred. The future feasibility-stage clock has not started.
