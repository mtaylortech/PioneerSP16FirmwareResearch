<!-- source: docs/handoffs/2026-10-10-revision2-sequence/01-FEATURE-CONTRACT.md | scrubbed -->

# P01 / M01 — Recorded-sample normalization contract

**Status: READY FOR NEXT STEP**  
**Owner-selected first feature: add a working peak-normalization feature for a sample recorded on the SP-16.**  
**Actual sequence root: docs/handoffs/2026-10-10-revision2-sequence**  
**Actual handoff: docs/handoffs/2026-10-10-revision2-sequence/01-FEATURE-CONTRACT.md**  
Updated October 10, 2026, America/Chicago. Later chats must prominently record this actual root.

## Current owner direction and provenance

The owner's latest direction explicitly replaces the timing-first plan: “Can we not worry about MIDI timing right now and just worry about creating a normalization feature that works? Can we rewrite everything to just go after adding a normalization feature?” This authorizes rewriting this sequence's two planning handoffs around normalization. Normalization is the first outcome, rather than an automatic fallback from an unsuccessful timing investigation.

Carry forward the original owner-selected normalization workflow and preservation decisions below. The product philosophy favors a few functions done well over adding many options. No specific original function has been selected for removal. Initial modification of the existing software is acceptable; a full OS replacement is not required or selected by the request to rewrite the plan.

Sequencer/audio/MIDI timing improvement, MPC3000 comparisons, the new 1 ms timing guarantee and the 60-second stable-timing observation are deferred from this first milestone. Existing playback, sequencing and MIDI/sync behavior remain part of the preservation boundary. Deferral is not a claim that timing is fixed or that existing functions may regress.

Prompt 1 and Prompt 2 remain planning scopes. The latest request revises these handoffs; no source/tool/firmware change, test, guest/hardware launch, build/install, Git mutation, delegation, publication or cross-chat dispatch occurs in this rewrite. Reference roadmaps remain unchanged.

## Selected feature contract

| Field | Owner selection or remaining unknown |
|---|---|
| Useful behavior | Normalize a sample recorded on the SP-16, producing an actual uniformly scaled recording that can be kept permanently or discarded. A new label or playback gain alone is insufficient. |
| Trigger and workflow | Select sample → press Normalize → choose Keep or Discard. Never apply normalization automatically. |
| Processing | Peak-normalize the whole recording with one uniform scale factor. Preserve waveform shape and stereo balance; no compression or introduced clipping. Silence remains unchanged. |
| Target peak | Owner's example: a recording at approximately −6 dB is raised to approximately 0 dB, possibly −0.1 dB. **Unknown before numerical acceptance tests:** exact ceiling and allowable error. Neither value is chosen silently. |
| Keep | Permanently rewrite the selected sample file and close the function. A separate output copy or volatile-only result does not satisfy this workflow. |
| Discard | Leave the original file and original audio intact. Processing or preview must not cause a permanent change before Keep. |
| First-version transport | Stopping playback during normalization is acceptable. Seamless processing during playback is not required for this first version. |
| Persistence | Kept audio must remain changed after ordinary reload/restart. Discarded audio must remain original. Executable installation/relaunch is a separate, unresolved delivery question. |
| Original functions | Entire existing OS remains usable, with no selected original-function exclusions: playback, sampling/recording, sequencing, effects, MIDI/sync, panel/touch/LEDs, analog filter and project/file workflows where present. |
| Data compatibility | Retain original project/sample formats and ordinary load/save workflows. Keep changes the selected audio by design; unrelated files, project data, sample timing/length and musical event positions are preserved. |
| Target | Physical SP-16 instrument family. **Unknown:** primary unit/release, access, exact sample fixture, storage destination and legitimate delivery route. Held 1.60 research is not automatically the selected release. |
| Distribution | Eventual distribution remains intended; form, support envelope and release qualification remain unknown. No publication occurs here. |
| Stock/custom distinction | Actual stock support for this exact workflow is unknown. Inspect before claiming a new capability; an existing stock operation alone cannot prove custom integration. |
| Named fallback | Internal sample deletion through a sample-file listing and Delete button, as previously selected. It is retained but not activated; it cannot satisfy normalization acceptance. |

## Numerical and state interpretation

**Proposed oracle, not an implementation choice:** For decoded samples x across the whole recording and all channels, let P be the maximum absolute sample value and C the selected peak ceiling. For non-silent audio, a uniform factor g = C/P gives the expected normalized values g × x, subject to the supported representation and declared quantization tolerance. Use the same gain for both stereo channels. Silence remains unchanged.

Declare the exact ceiling, supported encodings/sizes, numerical error and near-silence policy before testing. Do not introduce a compressor, limiter, automatic trimming, sample-rate conversion or different per-channel gain as substitutes for the selected behavior. File-format metadata and representation constraints require source-bound checks before a write.

**Unresolved integration semantics:** treatment of shared sample references, currently loaded buffers and subsequent playback; preview storage/lifetime; cancellation/errors; interrupted Keep and safe replacement of the selected file. A failed or partial write must not be reported as a successful Keep. Recovery/write prerequisites are specific to the actual candidate exposure; no safe-write implementation is assumed.

## Requirements-to-observation matrix

This is a planning contract, not an executable test plan. Freeze fixture/target identities, expected audio, numeric limits and failure policies before the corresponding authorized tests.

| Requirement | Stimulus | Observable distinction | Remaining prerequisite |
|---|---|---|---|
| Actual peak normalization | Select a known non-silent recording and Normalize | Whole-recording sample values follow one expected gain; peak reaches the declared ceiling within tolerance; no introduced clipping, shape change or stereo imbalance | Exact ceiling/error, formats, sample sizes and independent file/audio oracle |
| Silence and near silence | Normalize declared silent and very quiet fixtures | Silence unchanged; near-silence handling follows the declared policy, without accidental data damage | Near-silence threshold/policy and finite supported envelope |
| Keep | Normalize, choose Keep, then reopen/reload | Selected file permanently contains the accepted normalized audio; function closes; ordinary playback uses it | Actual selected-file identity, write boundary, loaded-buffer/shared-reference policy |
| Discard | Normalize, choose Discard, then reopen/reload | Original selected file and original audio remain intact | Independent before/after file and decoded-audio comparisons |
| Restart persistence | Keep or Discard, then fresh launch/reload | Kept normalization persists; discarded recording remains original | Delivery/restart method and controlled fixtures |
| Applied playback | Play the selected recording after Keep and after Discard | Playback corresponds to the appropriate normalized/original audio, with unchanged length and intended routing | Valid playback observation; null PCM or a UI image alone is insufficient |
| Error/interruption | Applicable cancellation, storage failure or interrupted Keep | Defined handling preserves usable state; partial writes/faults remain failures | Candidate-specific error policy, storage/recovery and separately authorized controls |
| Preservation | Exercise relevant original sample/project and instrument workflows | Existing formats, unrelated files, sequencing and required functions remain usable | Concrete regression reference/coverage before qualification |
| Custom-feature attribution | Compare stock and identified candidate with legal input | Actual new workflow and file/audio change attributed to candidate behavior | Stock baseline, mechanism/loading evidence and independent observations |

A numerical file-processing test can establish processing behavior in its stated environment. It does not by itself prove the original SP-16 UI integration, playback, device loading or whole-instrument preservation. Successful Keep, Discard, reload and actual playback are separate required observations.

## Current evidence boundary

Saved [README] `README.md` (evidence not published) and [latest experiment handoff] `experiments/panel-record-contract-20261009/HANDOFF.md` (evidence not published) report mapped original startup and selected HOME/Track/MIXER responses. Panel transport preparation remains uninstalled/live-unvalidated. Send editing, real audio, physical boot and broad instrument usability remain unproved; recorded failures, missing finals and excluded async findings are retained.

These records establish no normalization algorithm, sample write path, Keep/Discard integration or working custom normalization feature. This rewrite reruns no evidence.

## Approved planning identities

Chat 1 recorded all four documents matching the approved Revision 2 identities. Chat 2 rechecked the master roadmap and prioritized actions and obtained the same identities. These are saved inspection results, not a new full audit or proof of feasibility.

| Reference-only document | Approved identity |
|---|---|
| [04-MASTER-ROADMAP.md] `Review/04-MASTER-ROADMAP.md` (evidence not published) | e78fc1b090da2a942075e14783b042bbc93dce0c7aeea4786fb35d3370fd170d |
| [04-DEPENDENCY-MAP.md] `Review/04-DEPENDENCY-MAP.md` (evidence not published) | 9a37752b5f9eba19cdeace2de6e1bb3b98cc5fbb4be9ac2ed9f908f1c9efc495 |
| [04-PRIORITIZED-NEXT-ACTIONS.md] `Review/04-PRIORITIZED-NEXT-ACTIONS.md` (evidence not published) | 2fa1f75ed45da843fe44d9f4b160ec896591be1ad6d65f357082e1ba07408dfa |
| [04-RISK-REGISTER.md] `Review/04-RISK-REGISTER.md` (evidence not published) | 0f2bdd48c6970b71d0ff339e0aa632cc121aa28dc58a025695833909650d19fb |

## Superseded timing decisions — reference only

Earlier owner choices selected sample-audio plus outgoing MIDI-note/clock timing, with every interval within 1 ms of ideal and full-observation spread at most 1 ms; incoming-sync numerical qualification was not selected. These requirements are deferred, not active normalization gates.

The prior MPC3000 research recorded a 96-division quarter-note grid in the [operator's manual](https://www.mpcstuff.com/content/MPC_Manuals/MPC3000_manual.pdf), Roger Linn's distinction between intended swing and execution variation in his [interview](https://www.attackmagazine.com/features/interview/roger-linn-swing-groove-magic-mpc-timing/), and [Innerclock's published setup-specific results](https://innerclocksystems.com/litmus/) of 12 audio samples and 26 MIDI-note samples at 48 kHz (0.250 ms and approximately 0.542 ms) under external clock. Those saved observations do not establish SP-16 timing, outgoing MPC clock performance or universal guarantees. No new research or measurements occurred in this rewrite.

## Handoff to subsequent planning steps

- **Actual root:** docs/handoffs/2026-10-10-revision2-sequence.
- **Selected first feature:** recorded-sample peak normalization, Select → Normalize → Keep/Discard, with permanent selected-file rewrite only on Keep.
- **Preservation:** existing OS/functions/formats remain usable; stopping playback is acceptable for normalization's first version. No full OS rewrite is selected.
- **Deferred:** timing improvement and its 1 ms/60-second qualification work; ordinary original timing/MIDI functionality remains preserved.
- **Fallback:** internal sample deletion, not activated.
- **Unknown before relevant tests:** target/release/access, stock support, ceiling/error and format envelope, shared-reference/buffer semantics, safe Keep/error/recovery, actual integration/playback and regression coverage.
- **Planning status:** READY FOR NEXT STEP. The revised [feasibility tranche] `02-FEASIBILITY-TRANCHE.md` (evidence not published) records the carried-forward budget. No feature success, implementation or runtime authority is claimed.

**Scope record:** Original chat 1 performed read-only evidence/document inspection, owner-requested web research and created this contract. Chat 2 inspected records, verified two cited identities and created its tranche. The owner's latest request authorized rewriting these two handoffs around normalization. This rewrite changes those two planning files only; it performs no feature analysis, code/tool/firmware change, tests, runtime/hardware, Git mutation, delegation or cross-chat activity.
