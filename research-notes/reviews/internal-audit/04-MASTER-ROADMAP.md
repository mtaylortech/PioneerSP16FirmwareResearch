<!-- source: ../PioneerSP16Review/04-MASTER-ROADMAP.md | scrubbed -->

# Stage 4 — Master engineering roadmap

Proposed for independent review. October 9, 2026, America/Chicago.

Revision 2 addresses the [Stage 5 required corrections] `Review/05-REQUIRED-CORRECTIONS.md` (evidence not published), [audit] `Review/05-ROADMAP-AUDIT.md` (evidence not published) and [advisory recommendation] `Review/05-APPROVAL-RECOMMENDATION.md` (evidence not published). Their verdict applies to the original submission; it is not approval of this revision. Stage 1–3 evidence and Stage 5 records remain unchanged.

This document gives review instructions and proposed capability gates for the Pioneer SP-16 project. It is **not an approved execution plan**. No milestone authorizes implementation, experiments, hardware access, flashing, changes to engineering records, or dispatch to another chat. Work described below would require a subsequent, explicitly scoped execution decision in the main project. The main project was read-only during this review; no subagents were launched.

## Strategic destination and planning basis

The destination is useful new operating-system functionality on a physical SP-16, with the instrument functions selected for preservation, a repeatable delivery mechanism, and recovery appropriate to the changed state. Adding a feature to retained userspace may satisfy a functional requirement without replacing Linux. Application replacement, Linux/BSP replacement, and a different OS are separate architectural branches. None has earned implementation commitment yet.

The recommended initial hypothesis is to retain the shipped bootloader, Linux/BSP, and panel firmware while finding the smallest suitable feature boundary. A supported data or external interface earns preference when it actually supplies the selected behavior; a bounded original-app change is the next candidate. Replacing the application on retained Linux is the principal alternative when private application invariants become too broad. Platform replacement requires a demonstrated platform requirement.

Sources reviewed:

- Stage 1: [inventory] `Review/01-PROJECT-INVENTORY.md` (evidence not published), [baseline] `Review/01-TECHNICAL-BASELINE.md` (evidence not published), [gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published).
- Stage 2: [audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published), [contradictions] `Review/02-CONTRADICTION-REGISTER.md` (evidence not published), [validation requirements] `Review/02-VALIDATION-REQUIREMENTS.md` (evidence not published).
- Stage 3: [architecture assessment] `Review/03-ARCHITECTURE-ASSESSMENT.md` (evidence not published), [options] `Review/03-STRATEGIC-OPTIONS.md` (evidence not published), [recommended direction] `Review/03-RECOMMENDED-DIRECTION.md` (evidence not published).

B/G, F/C/R, and X references retain their Stage 1, Stage 2, and Stage 3 meanings. K references identify the companion [risk register] `Review/04-RISK-REGISTER.md` (evidence not published). The [dependency map] `Review/04-DEPENDENCY-MAP.md` (evidence not published) defines joins and route conditions; [next actions] `Review/04-PRIORITIZED-NEXT-ACTIONS.md` (evidence not published) decomposes the nearest gates. This roadmap synthesizes the reviewed outputs; it does not recertify the live engineering or archive trees.

## Present technical baseline

| Capability | Accepted boundary | Planning consequence |
|---|---|---|
| Held 1.50/1.60 firmware decoding | Stage 2 independently reproduced complete decryption to retained ISOs, outer regular content and primary tar content/link agreement | Preserve originals and use source containers as assembly authority. Publisher acquisition provenance remains open. |
| Linux metadata | 60 tar-directory mode differences independently reproduced; 22 SFS-file differences recorded; special entries represented as metadata | Host trees are research fixtures, not validated Linux image sources. |
| Application analysis | Original 1.60 ARM32 ELF and localized startup/UI/encoder maps are byte-backed | Useful for scoped boundary research; proprietary source and whole-instrument contracts remain unavailable. |
| Application execution | Saved original-app initialization/dispatch, owned HOME, Track 2 selection and HOME→MIXER are verified under material emulator substitutions | Retain these milestones. They do not demonstrate shipped-kernel boot or physical readiness. |
| Send | Two accepted same-owner snapshots retain value zero; conditional encoder path is statically mapped | No legal live parameter mutation or new feature is demonstrated. Send continuation is optional, selected by feature relevance. |
| Audio and timing | Null PCM calls exist; installed clock/timer contracts are defective; affinity is unenforced | No real audio, physical latency, CPU headroom or instrument stability claim is available. |
| Builds and delivery | Historical BSP/toolchain, packaging and A/B clues exist | Matching builds, usable execution route, repack acceptance and hardware recovery remain unverified. |
| Preservation | Local Git and same-disk archives cover portions of the environment | Complete independent restoration and off-device preservation remain unverified; final archive state was indeterminate in prior reviews. |

Stage 2 controls the quantitative correction: 281→441 resource returns occurred over **140.072 seconds after font completion**, not the Stage 1 245-second description. This is one intermediate-count comparison, not a general speedup. No earlier record is amended here.

## Milestone model and evidence rules

**ER — exploratory research** resolves a consequential unknown and may conclude that a route is unsuitable. **EI — enabling infrastructure** supplies a reusable test, execution, recovery or build capability. **TD — technical demonstration** proves a bounded behavior, with explicit limits. **PQ — production-quality engineering** proves supported operation, installation, compatibility and maintenance. Mixed milestones identify their transition. Research completion can be a well-evidenced rejection; a functional milestone can pass only when its stated capability is demonstrated.

For every future consequential experiment, the proposed evidence contract is: identified inputs and source revision; actual runtime/overlays; effective bounds; primary input/state/output receipts; faults and missing finals retained; separate outcomes for **observation validity, milestone attainment, observation completion, and cleanup** (R10). A copied summary, zero process exit, static byte match, UI pixel change or successful cleanup cannot substitute for another outcome. An independent reviewer should accept, reject, or request more evidence at each gate; advancement is never automatic.

Acceptance thresholds must be specified before observing candidate results. M01 sets feature limits; M03/M05 measure the stock reference and support justified tolerances. A missing threshold or required evidence leaves a gate pending. Negative research results should narrow routes rather than trigger indefinite investigation.

No calendar or person-effort estimate is defensible from the reviewed record: the first feature, unit access and delivery route are unknown. Existing roughly 600-second emulator observations describe past run bounds, not engineering effort. Near-term investigations are bounded by questions, artifacts and stop decisions. Re-estimation becomes useful when the selected mechanism, interfaces, candidate costs and validation scope have evidence; a conditional M06 selection alone does not supply an estimate basis.

Before sustained feasibility work, the human owner must choose an investment tranche: allowed questions/routes, a resource or effort ceiling, and a review point with stop, scope-reduction, access-acquisition or architecture-pivot outcomes. No ceiling is invented here. Each renewal needs an owner decision and a new decision-changing question; a tranche grants no experiment or implementation authority (RC08).

## Staged readiness and exposure contracts

Partial gates below are acceptance subsets of one authoritative milestone/package, not competing packages. A subset can pass only with its own evidence; passing one does not mark the whole milestone complete.

| Contract | Required evidence and use |
|---|---|
| **M02-P — Preservation** | Indispensable inputs/raw evidence identified and protected in a usable recovery location. Off-device preservation is a deliverable; broad historical reconstruction is not a prerequisite for the first stock capture. |
| **M02-C — Capture readiness** | Actual source-bound method, relevant independent controls, truthful four-outcome reporting, input/identity/connection conditions and effective bounds. Required before new consequential observations. |
| **M02-R — Reference reproduction** | Independent restoration/reproduction of the relevant reference using the selected method. First M03 acquisition may supply that reference. Required before candidate/reference acceptance that relies on reproducibility; emulator replay only if that emulator is used. Full M02 additionally verifies off-device recoverability. |
| **M05-A — Architecture admission evidence** | M01 workload; measured stock configuration/capacity/deadlines; minimal measured candidate costs or justified conservative bounds; what stock work is consumed or replaced; excluded costs, instrumentation effects, integration unknowns, reserved margin and reopening thresholds declared before reading the admission result. No generic CPU percentage or universal margin is assumed. |
| **M05-Q — Integrated qualification** | Actual integrated candidate, required concurrent stock behavior, real affected interfaces and target deadline/resource measurements. Closes unresolved costs at the selected substrate/M07/M08 joins. Stock idle headroom, emulator results and isolated benchmarks cannot pass it. Full M05 requires applicable A and Q evidence. |
| **H — Active hardware readiness** | Before each active code/device/boot trial: candidate failure domain; an evidenced stop/reset/return-to-stock path independent of that failing component; finite trial and loss-of-observability/operator-stop conditions; intervention owner; controlled device handoff and supported electrical/audio/output/gain/codec/clock envelope, with appropriate isolated capture connections. Account for mounted stock storage and peripheral state affected by reset/power cycle. Passive stock capture needs only applicable observation/connection controls. H is independent of persistent recovery and remains required for volatile trials. |
| **M09-Q — Route/recovery qualification** | Exact route and write/failure scope; faithful artifacts/metadata when used; protected unit-specific state; independently demonstrated restoration appropriate to that scope; actual unchanged-route acceptance on a suitable recoverable target or applicable existing receipts. Encode equality is separate from real acceptance. |
| **M09-T — Per-trial persistent admission** | Before every persistent attempt, bind exact candidate/container/installer hashes and eligible unit/release to allowlisted content/metadata changes, all relevant checks/destinations, actual/possible candidate-dependent effects and an applicable qualified backup/restoration/interruption envelope. Requalify changed route, structure, destination or failure assumptions; reuse unaffected qualification. No small diff inherits generic approval. |

M09 requirements follow actual exposure. A confined reversible data-file change needs qualified backup/restoration for that data scope; it does not automatically require a NAND repacker. A modified update with broad writes inherits the entire write/recovery scope. A launcher/configuration installed persistently is a persistent route even when its executable runs from RAM. H cannot be satisfied by a candidate's graceful exit alone or by assuming a power cycle is harmless. Intervention tests and operating-envelope evidence require separately authorized hardware work; no deliberate crash or destructive test is ordered here.

M06 may select a **conditional feasibility branch** from M01, M02-P/C and available M05-A/access evidence, specifying the mandatory next discriminator and withheld commitments. Substantial feature implementation requires the selected mechanism/substrate proof and applicable M02-R; physical feature acceptance additionally joins M04, H and M05-Q. This permits minimal mechanism/cost probes before broad commitment without certifying an unproved architecture. BE/BF may establish M04's execution evidence through their verified alternate boot route; successful stock-userspace execution is not an extra requirement for those branches.

## Stage 5 correction disposition

“Addressed” below means the proposal contract is revised and internally read back. It does not mean the underlying capability is demonstrated or that an independent reviewer has approved this revision. No correction is declared inapplicable without an explicit product/route decision.

| Correction | Planning disposition | Proposed accountable role | Contract locator / affected gate |
|---|---|---|---|
| RC01 | Addressed; P/C permit initial acquisition, R follows it | Roadmap owner / evidence-method reviewer | Staged readiness; M02/M03; dependency walk; P02/P04/P07 |
| RC02 | Addressed; admission bounds and integrated proof distinct | Architecture/performance reviewer | M05-A/Q; M05/M06/M08; P08/P10; K12 |
| RC03 | Addressed; actual intervention/envelope evidence still open | Hardware-session owner / safety reviewer | H; active M04/M05/BM/BD/BE/BF/M07/M08; P07/P11; K18 |
| RC04 | Addressed; every persistent candidate admitted before exposure | Installation/recovery owner / candidate integrator | M09-Q/T; persistent preconditions; P09; K16 |
| RC05 | Addressed; product choice pending, both routes represented | Product/release owner | M10-P/N→M11; dependency map; P12 |
| RC06 | Addressed; mandatory selected mechanism discriminator | Firmware/reverse-engineering reviewer | BM; M05 ledger/M06/M07; P10/P11; K06 |
| RC07 | Addressed; second feature tests a declared reuse claim | Architecture/acceptance reviewer | M12 acceptance; P12; K13 |
| RC08 | Addressed; owner-selected ceiling/review point remains pending | Human project owner / program reviewer | Investment tranche above; prioritized-actions review rules; K13 |

## Capability sequence

| Gate | Capability earned | Class | Present disposition |
|---|---|---|---|
| M01 | One testable feature and preservation boundary | ER | Open: no selected first feature |
| M02 | Recoverable, truthful evidence and selected test environment | EI | Partial assets; gate open |
| M03 | Identified unit, observable stock boot and reference behavior | ER/EI | Documentary/static leads only |
| M04 | Verified permitted execution of changed code at the selected layer | TD/EI | Open |
| M05 | Admission evidence, then integrated interface/resource qualification | ER/TD | Partial static knowledge only |
| M06 | Conditional architecture decision with explicit commitment gates | ER | Conditional Stage 3 preference only |
| BM | Selected A/B/C attachment/data/change mechanism demonstrated | EI/TD | Open; standalone execution is insufficient |
| BD / BE / BF | Additional substrate capability for a replacement branch | EI/TD | Dormant until justified |
| M07 | Controlled new feature behavior in a validated test environment | TD | Open |
| M08 | First functioning custom feature on an SP-16 | TD | Open; principal first delivery gate |
| M09 | Faithful install artifact and independent recovery for its write scope | EI/PQ | Open; preparation may start early |
| M10 | Selected persistent or non-installed delivery survives lifecycle/failure qualification | TD/PQ | Open; product choice pending |
| M11 | Supported, reproducible production release | PQ | Open |
| M12 | Repeatable capability to add further OS/instrument functions | PQ | Long-term, definition revisited after M08 |

Numbers identify gates, not a mandatory serial schedule. M09 moves ahead of any earlier gate that would require persistent changes. BD/BE/BF are alternatives, not a queue of three rewrites.

## M01 — Define the first feature and compatibility contract

1. **Objective/significance:** Convert the OS ambition into one observable instrument behavior and a preserved-function boundary. This prevents architecture choice by backlog momentum (F01/R01; X01).
2. **Prerequisites:** Reviewed baseline and an explicit product decision by the project director; actual feature and unit availability are not assumed.
3. **Workstreams:** Product acceptance, feature-boundary analysis, compatibility and validation design.
4. **Deliverables:** One selected before/after scenario; input→state→processing/output→storage map; preserved and intentionally excluded functions; target release/unit class; distribution intent; measurable feature/regression tests; alternative feature if the primary route is infeasible.
5. **Acceptance:** Each expected result has an observable oracle. Persistence, audio/timing, panel, project-file and original workflow requirements are explicit or explicitly inapplicable. Feature selection is endorsed separately; no open decision silently becomes an implementation assumption.
6. **Evidence:** Requirements-to-observation table, existing byte/document locators for candidate boundaries, and a list distinguishing demonstrated dependencies from hypotheses. A selected MIDI policy or effect is an example only until chosen.
7. **Risks:** K01 scope ambiguity; K06 cosmetic/state-only results mistaken for functionality; K10 unbounded compatibility obligations.
8. **Dependencies:** Starts from the baseline; feeds M04–M12. Does not require finishing Send, rebuilding Linux or choosing the final OS.
9. **Parallel opportunities:** Unit/access inventory, preservation inventory, and static acceptance-chain analysis can start while the feature is selected. Feature-specific traces wait for the selection.
10. **Replan conditions:** No product choice; requirement changes from local policy to new engine; preservation of all original functions becomes mandatory; deployment audience changes. Re-open this contract and downstream scope rather than extend the backlog.

## M02 — Establish a recoverable and truthful test capability

1. **Objective/significance:** Make the evidence used for architectural decisions reproducible and fail explicitly when its contracts are violated (R02/R05/R10/R13/R14).
2. **Prerequisites:** Baseline source locators. M01 selects which runtime needs restoration; preservation inventory and the reporting contract may start beforehand.
3. **Workstreams:** Evidence preservation, environment restoration, observation/reporting design, necessary harness contract repairs.
4. **Deliverables:** One selected package/dependency manifest; separate M02-P, M02-C and M02-R receipts; off-device preservation/restoration evidence; four-outcome reporting; independent relevant controls; scoped substitutions/fixes.
5. **Acceptance:** P protects indispensable inputs/evidence and C validates the actual capture method. These permit first M03 reference acquisition. R independently restores/reproduces the acquired reference before comparisons relying on reproducibility. Full M02 verifies required content/types/links/metadata and off-device recovery. Required-check failure cannot appear as validity success; all receipts bind actual sources. A hardware-only method does not require emulator replay.
6. **Evidence:** Restore comparisons and failed-metadata disposition; one independent reference replay/capture; missing-final/early-stop/wrong-owner/delayed-response/worker-fault controls; installed clock/timer evidence only where the chosen inference needs it. Preserve historical defective results as history. Reconcile archival ownership and final batch status before relying on it.
7. **Risks:** K02 evidence loss, K07 stale/circular reporting, K08 clock defects, K14 archive/path drift. Local Git does not cover ignored inputs/runtimes/raw evidence.
8. **Dependencies:** M02-P/C precede first M03 acquisition and new consequential observations; M03 may supply R's reference. M02-R precedes candidate/reference acceptance relying on reproduction. Full selected-method recovery/reproduction precedes M11. Static studies can start earlier; irrelevant emulator restoration is not a predecessor.
9. **Parallel opportunities:** Preservation/restore work, independent oracle review and static feature analysis are separable. One owner integrates each runtime package; no parallel shared mutable guests or databases.
10. **Replan conditions:** Missing irreplaceable inputs, restore failures affecting execution, package identity mismatch, or a selected question outside emulator fidelity. Switch method or narrow the claim; do not repair every Linux contract by default.

## M03 — Establish the actual instrument and stock reference

1. **Objective/significance:** Replace documentary architecture assumptions with unit-specific boot, storage and relevant stock behavior (R03; X02/X07).
2. **Prerequisites:** Available suitable SP-16 and separately authorized observation access; M02-P/C and applicable connection controls; M01 for feature-specific reference coverage. M02-R is not required to acquire its first reference. Existing inventory collection can start earlier.
3. **Workstreams:** Hardware/access characterization, boot/storage observation, stock audio/panel characterization, unit-state inventory.
4. **Deliverables:** Unit/board/release identity; documented access and electrical requirements; actual stock boot trace; environment/mount/device inventory; relevant stock input/output captures; calibration/identity state locations and readback limitations.
5. **Acceptance:** Actual boot chain and relevant readiness conditions are observed, including initialization errors and missing devices. Accessible surfaces are classified as observation-only, execution-capable, or unknown. Storage claims derive from unit observations; required stock behavior supplies a repeatable reference. No persistent changes are needed for this gate.
6. **Evidence:** Unit-linked console/boot receipts, mounts/device identities, relevant real panel events, and known-stimulus audio captures with format/rate/channels/routing when audio is affected. Boot banner and HOME alone cannot satisfy readiness.
7. **Risks:** K03 unavailable access; K04 actual policy unknown; K05 calibration/storage assumptions; K09 proprietary interfaces. A documented UART/JTAG/U-Boot command is a lead, not working access.
8. **Dependencies:** Supplies the reference for M02-R and target facts for M04/M05/M09. All physical success claims require the applicable target evidence; offline software proof does not require unit acquisition. Without a unit M08 cannot pass.
9. **Parallel opportunities:** Feature maps, updater checks, preservation and source lineage need not wait. Compatible stock observations can share one controlled hardware session.
10. **Replan conditions:** No suitable unit, inaccessible observation route, mismatch with held release, stock instability, or unexpected per-unit state. Rebaseline the target and limit physical claims; avoid substituting generic ARM-board success.

## M04 — Establish a permitted executable foothold

1. **Objective/significance:** Prove that code or changed data can run at the layer needed by the selected feature. This closes a fundamental feasibility risk before deep feature implementation (R08; X03).
2. **Prerequisites:** M01 layer hypothesis, M02-P/C, applicable M03 unit/access/policy evidence, and H for active hardware. Every persistent attempt requires M09-Q/T beforehand; no-write trials do not require a repacker. A selected BE/BF boot demonstration can supply this gate's route-specific execution evidence without an unrelated stock-userspace foothold.
3. **Workstreams:** Complete acceptance-chain analysis, legitimate delivery/launch mechanism, ABI/loader test, side-effect containment and return-to-stock observation.
4. **Deliverables:** Checks and destinations for container/component/boot/runtime boundaries; chosen mechanism and exact side effects; harmless identity-reporting program or functional data-load equivalent; successful execution/exit receipts and return-to-stock procedure.
5. **Acceptance:** Actual changed code/data executes through the claimed permitted route, with intended identity, controlled effects and return to stock. H is evidenced before exposure, including intervention if the candidate cannot tear down. Classify executable/launcher and data writes separately. A console banner or CRC parser pass cannot qualify. Standalone execution does not prove app attachment; passing userspace execution leaves replacement-boot policy open.
6. **Evidence:** Shipped-byte/source correspondence where applicable, observed unit policy, identity/output and loader/ABI receipts, write-scope observations, faults and teardown. No fuse changes or presumed authentication bypass form part of this proposal.
7. **Risks:** K04 acceptance restrictions; K05 hidden writes; K09 exclusive resources; K11 source/ABI mismatch.
8. **Dependencies:** Applicable M03 facts→route-specific M04; M04 enables target probes and M08. M09-Q/T precede persistent M04. Conditional M06 may select its probe earlier; BE/BF can establish M04 during their own admitted boot proof. Static write/recovery analysis does not require an already successful foothold.
9. **Parallel opportunities:** Offline package analysis and feature code-boundary study can proceed independently. Hardware execution uses one session owner.
10. **Replan conditions:** Restriction at the required layer, undetected persistent side effects, no compatible runtime, or reliance on normal application startup for supposed recovery. Compare another legitimate route/layer; leave physical feasibility unresolved if none is demonstrated.

## M05 — Prove affected interfaces and resource feasibility

1. **Objective/significance:** Establish the input, state, processing, persistence and hardware contracts the feature would actually use; distinguish local modification from independently reusable platform support (R03–R06/R09/R11; X06/X07/X09/X10).
2. **Prerequisites:** M01 and M02-P/C for admission analysis; M03 for stock target measurements. Custom on-unit cost/interface probes require route-specific M04, H and M09-Q/T if persistent. M02-R precedes reproducibility-dependent comparisons. Full implementation is not prerequisite to M05-A.
3. **Workstreams:** Selected panel/MIDI/control transport, ownership/deferred state, audio/codec/analog routing if affected, file/schema semantics, resource/timing measurements, component source lineage.
4. **Deliverables:** Affected-interface and selected modification-mechanism ledger; legal stock state/output trace where relevant; M05-A resource ledger separating measured/bounded/unknown costs; M05-Q integrated receipts; component/build ledger and independently reusable interface evidence for selected replacement branches.
5. **Acceptance:** A admits only a bounded investigation/conditional architecture: workload/configuration, measured stock capacity, representative candidate cost or justified conservative bound, excluded/replaced work, integration unknowns, reserved margin and rejection thresholds are explicit. If no meaningful bound exists, resource-dependent commitment remains pending and selects a smaller discriminator. Q later requires integrated legal state/output, required device ownership and actual target deadlines/resources under M01 load. Only affected contracts are required. An isolated benchmark or stock idle margin does not prove integrated compliance.
6. **Evidence:** Before admission, bounded prototype/representative processing tests or conservative bounds, stock measurements and instrumentation limits; separately scoped minimal target cost probe when needed. At Q, correlated input/owner/deferred/processing/output and actual clock/rate/buffer/underrun/load receipts, relevant persistence and selected substrate transactions. Mechanism proof belongs to BM or the selected substrate, distinct from stock state knowledge. No invented panel packet/direct RAM write counts as physical input.
7. **Risks:** K06 incorrect mechanism, K08 invalid timing, K09 hidden initialization/exclusivity/analog controls, K10 persistence incompatibility, K12 inadequate headroom.
8. **Dependencies:** M05-A feeds conditional M06 and minimal probes. M05-Q closes integrated unknowns at selected substrate/M07/M08 joins and is mandatory for target compliance/M08. It is not required before constructing the candidate. Rebuilding applies only to components that must change; an unavailable stock-userspace probe does not itself reject an alternative boot branch.
9. **Parallel opportunities:** Static input/state tracing, build lineage, packaging metadata and test-oracle development can run independently. Device ownership and audio timing observations integrate serially on the unit.
10. **Replan conditions:** Feature requires broad opaque state, unusable device sharing, unavailable proprietary component, insufficient resources, or mismatch between visible UI state and processing. Reduce scope, alter algorithms or compare D; evaluate E only for a demonstrated platform limitation.

## M06 — Select an architecture and demonstration route

1. **Objective/significance:** Commit the next technical demonstration to evidence-supported scope; stop non-discriminating research (R01/R12; Stage 3 options A–F).
2. **Prerequisites:** M01, M02-P/C and available M05-A/access evidence for conditional branch selection. Physical feasibility remains conditional until route-specific M04 and required target evidence exist. Substantial feature work additionally requires M02-R where comparisons rely on it and selected BM/BD/BE/BF mechanism proof. Minimal mechanism/cost/substrate probes may be selected before these proofs, under separately authorized scoped prerequisites.
3. **Workstreams:** Architecture comparison, compatibility tradeoffs, dependency selection, risk review and scoped effort planning.
4. **Deliverables:** One recommended option A/B/C/D/E/F; exact retained/replaced layers; delivery/write scope; rejected alternatives and evidence; remaining hypotheses; M07/M08 test design; scoped work decomposition and estimate basis.
5. **Acceptance:** Record the decision as conditional or supported by demonstrated mechanism/substrate evidence. Each indispensable interface has proof or a mandatory bounded gate; A/B/C require applicable BM, not merely a standalone utility and stock setter trace. Material cost unknowns withhold resource-dependent commitment; margins/rejection thresholds are predeclared and M05-Q must close integrated costs. No assumed plugin API, separate DSP or automatic rollback substitutes for evidence. Selecting a feasibility branch authorizes neither broad implementation nor hardware execution.
6. **Evidence:** Feature-boundary, acceptance/access, interface/resource and build ledgers linked to primary results; comparison of local change against D; measured platform reason for E/F if proposed.
7. **Risks:** K01 uncontrolled scope, K13 sunk-cost branch selection, K04/K09 concealed dependencies.
8. **Dependencies:** Conditional M06 selects BM for A/B/C, BD for D, BE for E or BF for F. Applicable mechanism proof precedes substantial M07 work; M04/H/M05-Q join physical M08. BE/BF prove their own execution route rather than depend on stock-userspace access. M09-Q/T precede each persistent probe; remaining integration costs can reopen this decision.
9. **Parallel opportunities:** Non-mutating comparison studies can precede the gate. A conditional selection commits only to a bounded discriminator; substantial feature work waits for applicable mechanism/substrate proof and admission evidence. Avoid expanding alternative substrate studies beyond their decision-changing question.
10. **Replan conditions:** New evidence contradicts the chosen interface, recovery/write scope grows, feature contract changes, or local patch boundaries expand into broad reconstruction. Re-open the option decision; incomplete tracing alone is not evidence that rewriting wins.

## BM — Demonstrate the selected modification mechanism (options A/B/C)

1. **Objective/significance:** Close the attachment/data/change boundary between execution access and new functionality. A standalone program and stock setter trace do not jointly prove that new behavior can attach to the original application (RC06).
2. **Prerequisites:** M01, M02-P/C and conditional M06 selection; exact candidate/runtime/reference identities and relevant M05-A interface evidence. Reproduction-dependent comparisons need M02-R. On-unit probes require route-specific M04, H and M09-Q/T if persistent. A scoped off-device proof can precede unit access but leaves physical mechanism acceptance open.
3. **Workstreams:** Actual data loading for A; execution/coexistence/interfaces for independent B; actual loaded interception/ownership/ABI for interposing B; version-bound change or new-code loading/entry/return for C.
4. **Deliverables:** One smallest reversible mechanism probe, independently checked change/attachment manifest, loaded-path receipt, return/error/ownership evidence and claim limits. Record irrelevant subtests as inapplicable with the selected mechanism reason; an independent companion needs no internal hook proof.
5. **Acceptance:** A reaches the functional data boundary with its real constraints. Independent B proves necessary coexistence/interfaces. Interposing B actually intercepts the required call/control boundary. In-place C proves valid target/version/bytes and accepted execution of the affected path. Added-code C proves executable placement/loading, control transfer/return and applicable ARM mode/ABI/relocations/memory/cache/thread contracts. A no-op or identity attachment establishes mechanism only, not M07/M08 functionality.
6. **Evidence:** Actual loaded original/candidate identities, legal stimulus and exact data/control/entry/return observations, independent negative/error cases and clean removal. State the environment of proof; emulator interception does not certify device loading or real timing.
7. **Risks:** K04 runtime acceptance, K06 incorrect mechanism, K07 circular observers, K11 ABI/source gaps, K18 active intervention/output constraints.
8. **Dependencies:** Conditional M06→applicable BM→substantial M07 for A/B/C. M08 requires proof at the physical claimed boundary, whether obtained separately or with the integrated feature. BD/BE/BF carry equivalent selected-substrate obligations for replacement routes. No generic extension API/framework is required.
9. **Parallel opportunities:** Independent ABI/change review and feature oracle development; one integration owner binds each probe. Minimal cost probes may share the mechanism session when bounds and attribution remain valid.
10. **Replan conditions:** No usable data boundary, interception misses the actual path, added code cannot load/return correctly, unknown ownership or unacceptable side effects. Re-open the selected mechanism or M06; do not expand into broad feature implementation to compensate for an unproved attachment.

## BD — Independently usable instrument substrate on retained Linux (option D)

1. **Objective/significance:** Demonstrate that a replacement application can use shipped hardware support without relying on hidden original-app initialization.
2. **Prerequisites:** Conditional M06 selects D; M02-P/C, relevant M03/M05-A and route-specific M04 for target execution; H and M09-Q/T if persistent. M02-R is required for reproduction-dependent comparisons. Offline source assessment can start earlier; M05-Q closes integrated costs during substrate/feature qualification.
3. **Workstreams:** ABI/toolchain, app lifecycle, exclusive device handoff, audio/panel/display/MIDI and storage adapters, minimal instrument engine.
4. **Deliverables:** Replacement skeleton on retained Linux; selected adapters and initialization sequence; one stock-reference playback/control transaction; original-app stop/restart and state separation procedure; reduced-function compatibility contract if agreed.
5. **Acceptance:** The skeleton independently owns and initializes required devices, produces the reference output, handles selected input and restores stock operation. A diagnostic PCM/panel probe alone does not prove a sampler, sequencer or whole instrument; remaining M01 functions are explicitly assigned to M07/M10/M11.
6. **Evidence:** On-unit driver/codec/panel transactions, meaningful audio where affected, ABI manifests, ownership/error/restart receipts and compatibility gap ledger.
7. **Risks:** K09 undocumented initialization and vendor dependencies; K10 project/function compatibility; K11 toolchain; K12 scheduling/headroom.
8. **Dependencies:** M06→BD→M07 for D. Retained kernel source rebuilding is required only if this branch changes it.
9. **Parallel opportunities:** Separate adapters and offline engine/oracle work; shared device integration remains under one owner.
10. **Replan conditions:** Substrate depends on inseparable proprietary app behavior, required formats/functions exceed accepted replacement scope, or driver reuse fails. Compare scoped interface reconstruction against feature value; do not automatically replace Linux.

## BE — Recoverable replacement Linux/BSP substrate (option E)

1. **Objective/significance:** Prove the platform-level requirement on this product's board before committing the feature to a new Linux stack.
2. **Prerequisites:** Conditional M06 selects E with an evidenced platform requirement; M02-P/C, relevant M03/M05-A and R06 builds; actual alternate-boot acceptance; H; M09-Q/T if persistent. Its admitted boot demonstration may establish route-specific M04. Stock-userspace foothold is not mandatory. M02-R precedes reproduction-dependent comparisons; M05-Q closes integrated costs before physical feature acceptance.
3. **Workstreams:** Board port, boot/initramfs/storage, selected driver porting, toolchain/reproducible builds, retained-app ABI or replacement-app substrate, recovery.
4. **Deliverables:** Bootable identified platform artifact; selected board driver and mount assembly; preserved calibration; actual target input/audio reference tests; application compatibility result; measured comparison for the triggering platform requirement.
5. **Acceptance:** The actual SP-16 boots through the verified route, uses required devices and storage correctly, and meets the measured platform requirement. Generic i.MX6 boot does not pass. If retaining the proprietary app, original initialization and required behavior run under its actual ABI; if replacing it, BD-equivalent independent substrate evidence is required here.
6. **Evidence:** Clean relevant builds and explained source/binary correspondence, target boot and interface traces, reference comparisons, policy/recovery receipts, driver error paths and resource measurements.
7. **Risks:** K04 boot authentication, K05 recovery/storage, K09 missing drivers, K11 source/ABI gaps, K12 timing regressions.
8. **Dependencies:** M06→BE→M07 for E. Its recovery preparation can precede BE; platform write scope may invalidate a userspace-only M09 result and require a wider one.
9. **Parallel opportunities:** Component lineage, driver-port prototypes, userspace compatibility and offline feature logic. Final board boot/storage/audio integration is a shared boundary.
10. **Replan conditions:** Platform need is resolved on retained Linux; driver/calibration gaps are prohibitive; original-app compatibility expands scope; alternate boot is blocked. Return to D/C where requirements permit.

## BF — Different-OS instrument slice (option F)

1. **Objective/significance:** Demonstrate that abandoning Linux supplies a required benefit worth recreating OS and board support.
2. **Prerequisites:** Conditional M06 selects F using a measured requirement alternatives cannot reasonably meet; M02-P/C, relevant M03/M05-A and actual branch boot policy; H; M09-Q/T if persistent; explicit function boundary. BF may establish route-specific M04 without stock-userspace execution. M02-R and M05-Q are required at their applicable comparison/integration joins.
3. **Workstreams:** OS scheduling/services, memory/storage/display/USB as required, audio/MIDI/panel drivers, instrument processing and toolchain.
4. **Deliverables:** Recoverably booted board slice with all interfaces indispensable to the first feature; deterministic control→output path; comparison against retained Linux for the claimed benefit; inventory of omitted instrument functions.
5. **Acceptance:** Target measurements meet M01 deadlines/behavior and substantiate the triggering benefit. Required peripheral error handling and return to stock work. RTOS branding, benchmark loops or a generic board demo do not pass.
6. **Evidence:** Actual boot/policy/recovery traces, driver and scheduling measurements under representative load, meaningful output, build identities and comparison records.
7. **Risks:** K05 enlarged recovery scope, K09 hardware reconstruction, K10 loss of original capabilities, K12 unproved timing advantage, K13 rewrite scope.
8. **Dependencies:** M06→BF→M07 for F. BE is not automatically prerequisite; F has its own board-support and recovery obligations.
9. **Parallel opportunities:** Isolated driver/service development and offline algorithm tests after interfaces are fixed. Whole-board timing and storage integrate jointly.
10. **Replan conditions:** No measured benefit, essential devices unavailable, function reduction unacceptable, or retained Linux can meet requirements. Reject F rather than perpetuate it as a distant assumed destination.

## M07 — Demonstrate a controlled new functional behavior

1. **Objective/significance:** Prove the selected feature exists in changed software/data and produces the specified consequence, separating modification feasibility from hardware delivery (X08; R01/R04/R09/R10).
2. **Prerequisites:** M01, M02-P/C/R for reference comparisons, relevant M05-A, conditional M06 alignment and applicable BM/BD/BE/BF mechanism proof in the claimed environment before substantial implementation. Offline mechanism/prototype work may precede hardware access and prove software behavior only. On-unit trials additionally require M04, H and M09-Q/T if persistent; actual target costs close at M05-Q/M08.
3. **Workstreams:** Smallest feature implementation, legitimate input/state path, processing/persistence integration, controlled comparison and focused regressions.
4. **Deliverables:** Isolated reversible candidate, exact change manifest, original/candidate comparison, tests for feature edges and preserved affected behavior; explicit emulator/native/target limitations.
5. **Acceptance:** Candidate meets M01 functional oracle and differs from the unchanged reference as intended. Legal input drives applied state and meaningful output; the observer cannot inject the expected answer. Required local regressions pass. A relabelled screen, original Send edit or new program that prints its identity is not a new instrument feature.
6. **Evidence:** Version-bound original/candidate inputs, primary control/state/buffer/output chain, independently derived negative cases, required storage checks and four-outcome results. Timing claims use a valid method; emulated success is scoped software proof.
7. **Risks:** K06 hidden invariants; K07 observer self-confirmation; K08 fidelity; K10 persistence; K13 excessive patch scope.
8. **Dependencies:** Software proof can precede physical route/substrate proof when its environment supports the claim; simulated interfaces leave hardware feasibility open. M08 joins M07 with actual selected mechanism/substrate, M04/H/M05-Q and applicable M09-T. M07/M08 may share one controlled on-unit experiment when all criteria are evidenced.
9. **Parallel opportunities:** Candidate logic, independent test oracle, packaging/recovery preparation and bounded branch adapter work. One owner binds the final candidate and test package.
10. **Replan conditions:** Mutation only changes presentation, private-state reconstruction widens substantially, simulated contracts dominate results, or required regressions fail. Repair the specific mechanism or re-open M06; one failed hook does not disprove all localized changes.

## M08 — First functioning custom feature on a physical SP-16

1. **Objective/significance:** Deliver the first bounded new behavior on the instrument. This is the earliest gate that can claim a functioning custom SP-16 feature.
2. **Prerequisites:** M01, applicable M02-P/C/R, M03 target reference, route-specific M04, M05-A/Q, M06 and physical selected BM/BD/BE/BF proof, M07 behavior, and H. Each persistent trial requires M09-Q/T for its exact exposure. A no-write route can pass without a repacker, while still requiring intervention and supported outputs.
3. **Workstreams:** Candidate loading, physical input/output integration, relevant real-time/resource checks, targeted regressions and return to stock.
4. **Deliverables:** Exact feature candidate run on the identified unit; physical acceptance record; unchanged-stock comparison; defined limits and reproduction steps; successful teardown/restoration receipt.
5. **Acceptance:** Legal physical/control input causes the new specified state/output through real affected devices; feature edges and preserved regressions pass. Integrated concurrent load meets predeclared M01/M05-Q deadlines/margins; provisional cost bounds cannot qualify. H is established before the trial and return to stock is observed. Persistence is claimed only when tested. Repeat in a fresh launch/session; broader reliability belongs to M11. Null PCM does not qualify audio.
6. **Evidence:** Unit/firmware/candidate identity, launch and actual input traces, applied-state and physical output, resource/deadline measurements, regression results, faults and independent reviewer readback of primary evidence.
7. **Risks:** K04 route restrictions, K05 hidden writes, K09 real hardware mismatch, K10 stock regressions, K12 headroom.
8. **Dependencies:** Functional join of M07 with M03/M04/M05 and branch evidence. M09 can be independent of M08 only on a verified volatile route. M08 informs production scope and M12 direction.
9. **Parallel opportunities:** Offline implementation/oracles and install/recovery preparation; final hardware integration, resource ownership and restore are coordinated serially.
10. **Replan conditions:** No viable route, persistent writes discovered, stock reference fails, hardware output diverges or deadlines cannot be met. Re-open M04/M05/M06 and explicitly stop the affected hardware trial; emulator success remains useful but cannot close M08.

## M09 — Establish faithful installation and independent recovery

1. **Objective/significance:** Make the chosen write scope installable and recoverable even when the changed application/kernel cannot start. This is enabling work for every persistent trial, not a reward after feature completion (R07/R08/R14; X04/X05).
2. **Prerequisites:** M01 scope, M02-P/C preservation/capture and relevant M03 state; candidate route/write map from static analysis or M04 preparation. Feature success is not required. Qualification uses separately authorized suitable recoverable hardware and H for active tests; exposing irreplaceable state is not a method of discovering recovery.
3. **Workstreams:** Source-authoritative metadata assembly, encoding/repacking or alternate installer, complete checks/destination routing, unit backup, storage/ECC/OOB/UBI/calibration interpretation, failure/interruption recovery.
4. **Deliverables:** M09-Q reusable route/acceptance/write/recovery evidence; unchanged transform and faithful container assembly if used; actual unchanged-route acceptance or equivalent existing receipts; unit backup/restoration evidence; M09-T exact per-trial applicability receipt before every persistent exposure.
5. **Acceptance:** Q proves actual unchanged-route acceptance or cites applicable existing evidence, independently of encode equality. For repacking, unchanged ISO→UPD equals held bytes and consequential container metadata/content/layering differences are intentional and explained. Restoration works without the changed component for every affected state class. Before each persistent exposure T binds exact candidate/container/installer/unit, allowlisted changes/checks/destinations, candidate-dependent effects and qualified backup/restoration/interruption scope. File/service/data routes use equivalent scope-specific checks, not a needless UPD rebuild. Entry alone is not restoration.
6. **Evidence:** Actual unchanged-route acceptance receipts, independent source metadata comparisons, distinct encode/container checks, complete relevant routing, unit-specific restore interpretation and tested applicable failures; exact T receipt before every exposed candidate. Reuse valid unchanged qualification; changed structure/routing/failure assumptions trigger requalification. Model destructive cases first; do not deliberately brick irreplaceable hardware.
7. **Risks:** K04 incomplete acceptance, K05 recovery/unique data, K15 metadata drift, K16 undisclosed broad writes. A/B kernel names cover neither shared rootfs nor panel state automatically.
8. **Dependencies:** M09-Q plus exact M09-T precede every persistent M04/BM/BD/BE/BF/M07/M08 trial. Before the first modified installation, actual unchanged-route acceptance must already be demonstrated on a suitable target or by applicable retained receipts; do not add redundant reflashing. M10 binds its final pilot too, but earlier candidates are never deferred to M10. Requalify changed artifact/routing/failure assumptions; reuse valid unchanged evidence. Non-installed M10 needs only the recovery scope of any actual persistent data effects.
9. **Parallel opportunities:** Offline encoding/container fidelity, updater control-flow analysis and backup interpretation. Recovery hardware sessions need one owner and cannot race feature trials.
10. **Replan conditions:** Unexplained metadata/routing difference, inaccessible backup, restore mismatch, recovery depends on broken candidate, larger write scope or no suitable recoverable test target. Block persistent exposure and retain volatile exploration only if actually available.

## M10 — Qualify the selected delivery pilot

1. **Objective/significance:** Convert M08 into repeatable delivery and lifecycle behavior under the owner's selected product intent; persistence is not silently required.
2. **Prerequisites:** M08, M01 delivery/compatibility choice, M02-R comparisons, H and eligible unit. M10-P requires M09-Q/T installation/recovery; M10-N requires that scope only for actual persistent data effects. No installed launcher/configuration can use N to evade persistent admission.
3. **Workstreams:** Persistent install/startup integration for P, or repeatable acquisition/manual launch for N; state integrity, restart/relaunch, intervention, compatibility and focused qualification.
4. **Deliverables:** Exact pilot/launch manifest; P installation/boot/feature cycle or N acquisition/launch/fresh-stock-restart/relaunch cycle; state/save/reload as applicable; failure/intervention/restoration receipts; explicit excluded automatic-start/install capabilities and support limits.
5. **Acceptance:** P's exact installed artifact is accepted and works after cold restart, with qualified rollback/state policy. N's exact artifact is repeatedly acquired/launched on fresh stock sessions, handles candidate failure through H and preserves affected state; no installed-firmware or automatic-start claim is inherited. Both meet advertised behavior, eligibility, data integrity and relevant regressions. Any untested interruption scope limits resilience claims.
6. **Evidence:** P installer/boot/rollback or N launch/restart/relaunch receipts; exact identities, pre/post state, failure intervention, compatibility and regression results. Persistent data writes on N bind the applicable M09-T scope.
7. **Risks:** K05 calibration/storage loss; K10 migration/compatibility; K16 installer blast radius; K12 long-workload faults.
8. **Dependencies:** M08 plus the chosen M10-P or M10-N contract→M11. M09-Q/T are mandatory for P and actual persistent effects on N, not for an otherwise no-write product. Reuse matching M08 evidence; both paths still require lifecycle/failure qualification.
9. **Parallel opportunities:** Qualification-oracle design, documentation, reproducible-build work and offline migration testing; installations and recovery on one unit remain serial.
10. **Replan conditions:** Boot/installation variability, broader overwritten state, irreversible migrations, restart-only failure, or supported release/board differences. Narrow supported configurations and repair before production qualification.

## M11 — Qualify a maintainable production release

1. **Objective/significance:** Earn a supported-release claim with reproducible artifacts, defined compatibility, operational reliability and recovery.
2. **Prerequisites:** Applicable M10-P or M10-N, full selected-method M02 recovery/reproduction, finalized M01 support/distribution scope and justified workloads/limits from M03/M05-Q/M08/M10. A non-installed product needs equivalent launch/lifecycle qualification, not a persistent pilot.
3. **Workstreams:** Clean build/patch generation, release provenance, regression automation where useful, timing/resource reliability, installation/recovery compatibility, support and maintenance.
4. **Deliverables:** Independently reproducible release artifact; feature and preserved-function suite; justified load/stability campaign; eligibility checks; selected installation or acquisition/launch/intervention guidance and applicable recovery; limitations; provenance/distribution review; maintenance/version policy.
5. **Acceptance:** Independent reproduction yields release bytes or explains nondeterministic differences at an agreed boundary. Advertised functions/configurations and predeclared sustained workloads have evidence, with real audio/timing/storage where required. Applicable restoration and H intervention are tested; unsupported configurations fail explicitly. N release claims exclude installation/automatic start unless qualified via P. Distribution uses a reviewed legitimate form; extraction does not establish rights.
6. **Evidence:** Clean-environment reconstruction, target regressions/load and liveness/resources/deadlines; applicable install/recovery or acquisition/launch/relaunch/intervention matrix; preserved data, rejected incompatibilities and independent review.
7. **Risks:** K10 compatibility, K11 unreproducible builds, K12 reliability/resources, K17 distribution provenance/rights, K05 recovery gaps.
8. **Dependencies:** Either qualified M10-P or M10-N→M11; installation/recovery claims and checks apply to actual selected exposure. Full original-function replacement is required only if advertised/selected; excluded functions remain explicit. No arbitrary soak duration, unit count or zero-risk claim substitutes for evidence.
9. **Parallel opportunities:** Independent reproduction, oracle/release review and documentation; multiple units may support future testing only after resource/access/ownership constraints are resolved.
10. **Replan conditions:** Qualification detects new failure classes, distribution/support scope expands, regressions exceed accepted limits or source/runtime dependencies cannot be preserved. Re-open affected gates and revise advertised support.

## M12 — Establish a repeatable path to broader OS functionality

1. **Objective/significance:** Move from one feature to an engineering capability for successive OS/instrument functions, using demonstrated interfaces and recovery rather than repeated opaque patch exploration.
2. **Prerequisites:** M08 informs architecture direction; M11 precedes a production claim for this capability. A separately reviewed next-feature portfolio and measured constraints select the scope.
3. **Workstreams:** Stable extension/adaptation boundaries, modular state/control/processing/storage, version compatibility, platform lifecycle, test infrastructure and selected next functions.
4. **Deliverables:** Documented capability envelope and interfaces; second distinct functional vertical slice; reusable build/install/recovery/test path; bounded migration/version policy; decision on retained userspace, D, E or F for remaining objectives.
5. **Acceptance:** Before choosing the second feature, declare the reuse/maintenance claim. Exercise a materially different dependency or supported version/state condition relevant to that claim; record new reverse engineering, adapters and changes to shared contracts. Independently reproduce physical acceptance/regressions without observer writes. If both features test only one narrow interface, advertise only that envelope; add no unrelated hardware to inflate the test. Complete replacement-OS claims still require BE/BF and the agreed whole instrument suite.
6. **Evidence:** Two feature traces, actual interface/version/recovery tests, regression comparisons and measured maintenance/platform limits; explicit supported and unresolved functionality.
7. **Risks:** K13 accumulating brittle patches; K09 broad peripheral obligations; K10 format/API evolution; K11 platform lineage; K12 headroom.
8. **Dependencies:** M08→portfolio reassessment; M11→production qualification of M12. Architecture pivot re-enters M06 and BD/BE/BF with applicable M09 scope; reuse valid evidence, do not skip new-layer gates.
9. **Parallel opportunities:** Independent features once shared interfaces/state/ownership are stable; regression/release integration retains one authority.
10. **Replan conditions:** Each addition needs broad private-state reconstruction, platform lifecycle requirements change, measured constraints favor replacement, or retained functions no longer fit the agreed scope. Reassess the architecture using new evidence; a full OS rewrite is not automatically the endpoint.

## Critical path and near-term priority

There is no defensible duration-weighted critical path yet. The **logical critical path to M08** is the convergence of a selected functional requirement and valid test method, an actual usable execution route, and affected-interface/resource feasibility, followed by architecture selection, any selected replacement substrate, and a physically validated changed behavior.

For the preferred retained-platform route: **M02-P/C → first M03 acquisition → M02-R** runs alongside **M01 + M05-A → conditional M06 → selected BM/BD proof → M07**. The physical join is **M03 + route-specific M04 + H + physical selected mechanism/substrate + M05-Q + M07 → M08**. M09-Q/T precede each persistent exposure. BE/BF can supply route-specific M04 through their own admitted boot proof. Software comparisons requiring reproduction wait for M02-R; initial stock capture does not. The dependency map details these joins and M10-P/N delivery alternatives.

The immediate priorities are feature selection, indispensable evidence preservation/truthful testing, real-unit/access characterization, acceptance/write-scope analysis, and the smallest affected-interface discriminator. Additional HOME/MIXER proof, broad Send continuation, emulator throughput, all-effects reconstruction, complete BSP rebuilding and full-system emulation are not milestone prerequisites unless they resolve a named requirement or gate.

## Independent review disposition

Reviewers should first assess M01's required product decisions, M02's selected-method scope, unit availability, the legitimacy and side effects of candidate routes, the persistent-write gate, and the conditions that justify D/E/F. Then assess whether acceptance evidence is sufficient and narrowly scoped at each join. Open strategic decisions remain explicit; this review does not invent answers or authorize a next engineering task.

The proposal ends with these four documents. No implementation, engineering-record amendment, prompt dispatch, hardware action or subagent launch follows from their creation.
