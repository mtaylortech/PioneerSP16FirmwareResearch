<!-- source: ../PioneerSP16Review/04-PRIORITIZED-NEXT-ACTIONS.md | scrubbed -->

# Stage 4 — Prioritized next actions

Proposed for independent review. October 9, 2026, America/Chicago.

Revision 2 incorporates [Stage 5 RC01–RC08] `Review/05-REQUIRED-CORRECTIONS.md` (evidence not published). The sole disposition table and M02-P/C/R, M05-A/Q, H, BM, M09-Q/T and M10-P/N definitions are in the master roadmap. Planning correction does not establish physical readiness or approve execution.

These are instructions for reviewing and preparing future engineering scopes, **not approved tasks or executable prompts**. No implementation, runtime, hardware action, engineering-record edit, delegation or message dispatch is authorized. The main project remains read-only. Milestone definitions are in the [master roadmap] `Review/04-MASTER-ROADMAP.md` (evidence not published); joins are in the [dependency map] `Review/04-DEPENDENCY-MAP.md` (evidence not published); K IDs refer to the [risk register] `Review/04-RISK-REGISTER.md` (evidence not published).

## Prioritization rule

Prioritize an action when it unlocks a required capability, resolves uncertainty capable of invalidating an architecture, has a feasible bounded method, or prevents loss of indispensable evidence. Prefer the smallest discriminating investigation over completing an adjacent backlog item. A rejected route can be a useful research result; it is not a functioning feature.

The order below ranks decision value, not a serial schedule. P01–P04 can overlap. M02-P/C permit initial stock reference acquisition; M02-R follows reference acquisition and precedes reproducibility-dependent comparisons. P10 may conditionally select a bounded mechanism/cost/substrate probe before P07/P08 completion; it cannot imply broad implementation commitment. Active hardware requires H; every persistent trial requires M09-Q and exact M09-T. Roles identify future accountability, not assigned people or launched agents.

Before sustained feasibility work, obtain an owner decision specifying allowed questions/routes, resource or effort ceiling and a review point. At the ceiling, review stop, narrower scope, acquiring unit/access or pivot options. Renewal requires a new decision-changing uncertainty and an owner decision. No number or delivery forecast is invented; this proposed spending control grants no experiment authority (RC08).

| Rank | Proposed action | Why now | Gate / risk | Class |
|---|---|---|---|---|
| P01 | Select one first feature and preserved-function contract | Determines architecture, meaningful output and all relevant tests | M01; K01/K10 | Exploratory research |
| P02 | Reconcile indispensable evidence preservation and restoration | Loss could invalidate future reproduction; Git excludes critical assets | M02; K02/K14 | Enabling infrastructure |
| P03 | Establish available unit, access and existing stock observations | Actual execution feasibility cannot be inferred from emulator progress | M03 preparation; K03/K04/K05 | Exploratory research |
| P04 | Specify a truthful, source-bound observation contract | Consequential future results need valid attribution and failure reporting | M02; K07/K08 | Enabling infrastructure |
| P05 | Trace the smallest selected feature boundary | Separates data/service/patch/replacement options before implementation | M01/M05 preparation; K06/K09/K13 | Exploratory research |
| P06 | Map complete relevant acceptance and actual candidate write scope | Distinguishes permitted execution from deployability; defines recovery burden | M04/M09 preparation; K04/K05/K16 | Exploratory research |
| P07 | Obtain stock target reference and test the permitted foothold | Closes actual unit/boot and changed-code feasibility at the right layer | M03/M04; K03/K04 | Enabling infrastructure / demonstration |
| P08 | Separate stock capacity, bounded candidate costs and integrated qualification | Permits minimal feasibility work without claiming integrated deadlines | M05-A/Q; K06/K08/K09/K12 | Exploratory research / demonstration |
| P09 | Qualify route/recovery and bind every exact persistent trial | Must precede the earliest persistent exposure, including first foothold | M09-Q/T; K05/K15/K16 | Enabling infrastructure |
| P10 | Select a conditional mechanism/substrate discriminator, then review commitment | Prevents substantial feature work with unproved attachment | M06/BM; K01/K06/K13 | Exploratory research decision |
| P11 | Prepare and separately authorize one controlled custom-feature demonstration | Converts decisions into meaningful software and physical proof | M07/M08 plus chosen branch; K06/K10/K12 | Technical demonstration |
| P12 | Reassess persistence, production and further OS scope after proof | Production costs and architecture direction become measurable | M10–M12; K10/K11/K12/K17 | Production-quality engineering |

P09 moves before any exposed P07/P08/P10/P11 probe with persistent effects and binds that exact candidate. P07 is stock acquisition followed by a route-specific foothold after acceptance analysis. A replacement branch can establish its foothold through admitted alternate boot without a stock-userspace program. Stock/static P08 starts earlier; active probes require H and their specific execution/recovery prerequisites.

## P01 — Establish the first feature contract

**Proposed accountable role:** Project director, with independent acceptance reviewer. **Prerequisites:** Stage 1–3 baseline. **Scope bound:** One feature and one primary target configuration, with a named fallback rather than a feature catalogue.

Prepare a decision brief that specifies:

1. The user's before/after instrument behavior, trigger, applied state and observable output. New MIDI/control policy, utility and audio processing are different examples, not selected requirements.
2. What must remain usable: playback, sampling/recording, sequencer, effects, MIDI/sync, panel/touch/LEDs, analog filter and project files, as applicable. Explicitly record exclusions.
3. Persistence and restart behavior; accepted data compatibility/migration; whether the first demonstration may be volatile.
4. Target unit/release and eventual audience: private research unit or distributable capability. A final deployment mechanism need not yet be chosen.
5. Passing/failed feature observations, edge/rejection cases, affected regressions and timing/audio limits. Unknown numeric thresholds must be resolved before the corresponding acceptance test.

**Reviewable output:** M01 contract plus requirements-to-observation matrix and the questions that remain for M03/M05.

**Exit evidence:** An independent reviewer can distinguish a useful new feature from a changed label, unchanged original parameter edit or emulator milestone. The director selects the behavior separately.

**Stop/replan:** If no feature is selected, restrict subsequent work to preservation, existing access inventory and general acceptance analysis. Do not select Send by default or begin broad OS implementation. If all original functions must survive a replacement, reflect that enlarged validation burden before comparing architectures.

## P02 — Preserve the capability to reproduce decisive evidence

**Proposed accountable role:** Evidence/environment custodian, coordinated with any existing archive owner. **Prerequisites:** Known asset locators; M01 for final runtime subset. **Scope bound:** Indispensable inputs, accepted evidence and one selected test environment; not every duplicate experiment tree.

Prepare an inventory linking original UPDs/containers, original app/libraries, key dependency without disclosure, source/tool identities, byte-backed maps, raw milestone logs/captures, material host dependencies and failed receipts to independently restorable storage. Separate Git-covered material from ignored assets. Preserve qualified acquisition provenance and historical revision gaps rather than inventing chronology.

First determine the final disposition of prior archival work and its owner. The prior sampled status was not an atomic completed inventory. Examine which metadata differences matter to execution/evidence and which are host-only attributes. Avoid overlapping storage reduction or moving assets as part of this roadmap review.

**Reviewable output:** Proposed minimal recoverable package, dependency manifest, off-device preservation location/availability, and restoration comparison specification. Restore/replay belongs to a future separately authorized isolated workspace.

**Exit evidence:** M02-P protects indispensable inputs/evidence in a usable recovery location. Together with P04's M02-C it permits first stock acquisition; it does not yet claim independently reproduced hardware reference. M02-R then restores/reproduces the selected acquired reference before comparisons relying on it. Full M02 includes independently accessible off-device preservation and consequential content/type/link/metadata restoration checks. A same-disk archive or Git checkout alone does not close full M02/R14.

**Stop/replan:** Missing originals/runtime dependencies, conflicting archive ownership or consequential restore failures keep restoration pending. Protect the assets first; change the test method when recovery would require disproportionate irrelevant emulator reconstruction.

## P03 — Resolve the actual unit and access frontier

**Proposed accountable role:** Hardware-session owner. **Prerequisites:** Existing inventory/records; new physical observation requires a separately defined session and M02 capture contract. **Scope bound:** One suitable unit and its actual observation/execution surfaces.

Prepare a unit inventory covering available model/board/release, stock health, access permissions, existing console/boot/readback records and suitable recoverable test arrangements. Determine what can be observed without persistent changes, and which documented test points/connectors need electrical characterization before connection. `ttymxc0,115200`, `jtag=on`, NAND bank commands and MMC/network boot strings are static leads only.

**Reviewable output:** Available/unavailable/unknown unit and access table; minimal proposed stock observation session; list of missing unit-specific state/boot facts.

**Exit evidence:** Actual unit identity and usable observation route; complete relevant stock boot/reference evidence at M03. A banner does not prove a command channel or recovery. Nominal chip capacity does not prove usable memory or NAND geometry.

**Stop/replan:** No unit or usable access leaves M08 blocked by missing physical evidence, while bounded offline discriminators may continue. A generic ARM board or growing emulator completeness is not a substitute. Mismatch with the held release reopens binary-specific assumptions.

## P04 — Freeze the consequential observation contract

**Proposed accountable role:** One experiment-package owner and independent oracle reviewer. **Prerequisites:** M01 selected inference for method-specific fixes; retained R10 defects can be assessed immediately. **Scope bound:** One upcoming consequential test, not universal harness fidelity.

Specify package/source/configuration/input/runtime identities, actual command and effective native/supervisor limits. Required reporting separates observation validity, milestone occurrence, observation completion and cleanup. Preserve expected containment denials, worker/observer/native faults, missing finals and actual send/consume/handler/state/output timestamps.

Define independent negative cases: unequal identifier/name values, another widget/reentrant shared-return visit, wrong thread/frame, required-check failure with process zero, delayed valid input, early watchdog stop and missing native final. Cases must challenge the observed contract rather than copy its premises.

If the chosen test relies on guest time, specify correct timespec units, clock domains, relevant timers/signals and selected futex/select ownership/race semantics before that inference. The opt-in clock correction is not installed evidence. If time is measured on the unit, do not impose universal emulator correction first.

**Reviewable output:** One future package contract, necessary correction list and controls derived from an independent source/oracle. The existing corrected Send source's stale validation receipt remains invalid; do not reuse it as launch-ready.

**Exit evidence:** M02-C source-bound method controls and applicable connection/bounds/error validation are ready for initial reference acquisition under M02-P/C. That acquisition can supply M02-R's independent reproduction input. Do not make C depend on reproducing a nonexistent reference. Required failures propagate correctly; method-specific runtime comparisons still need R.

**Stop/replan:** Hash mismatch, circular tests, failure-hidden success or an inference beyond selected method fidelity. Switch or narrow the method. Historical accepted HOME/Track/MIXER evidence is not erased by this gate.

## P05 — Map one feature across the narrowest usable boundary

**Proposed accountable role:** Feature-boundary analyst. **Prerequisites:** P01; immutable held original bytes/maps. **Scope bound:** One input→state→processing/output→persistence route and its actual prerequisites.

Start from accepted maps and shipped bytes. Determine whether behavior is already data-defined, independent enough for a companion, local enough for a bounded app change, or dependent on a broader engine. Record exact release/ABI, initialized owners, relevant gates/clamps, thread/deferred handoffs and storage schema. Compare against the selected acceptance oracle.

Use Send/encoder 3 only if it closes a required mechanism question. Its known identifier cell `0xf6c700` and Component-name cell `0xf6ab44` are distinct; two value-zero snapshots are not a mutation. The conditional static route still needs complete transport and worker-to-owner application. Excluded async partial findings remain excluded until independently established within a newly authorized scope.

**Reviewable output:** Bounded dependency map with original-byte locators; uncertain edges; one smallest loaded-state/hardware observation that would discriminate the architecture.

**Exit evidence:** Trace supports a candidate with testable applied-state/output consequences or identifies a specific unresolved dependency. A missing trace remains unknown; it does not prove D/E/F is preferable.

**Stop/replan:** Broad UI/listener/type census adds no decision value; static maps cannot supply physical ownership or audio timing; local scope expands into large opaque reconstruction. Compare D against explicit compatibility rather than continue patching indefinitely.

## P06 — Separate execution permission, acceptance and write scope

**Proposed accountable role:** Acceptance/deployment analyst. **Prerequisites:** P01 affected layer; P03 actual policy where available. **Scope bound:** One or at most a small set of credible delivery routes, each with a complete relevant chain.

Trace container checks, target/version/component routing, integrity/authentication where actually present, destination writes and runtime checks. Supplied source is supporting evidence only after correspondence checks. Separate initial boot authentication from later userspace execution. Treat legitimate Linux launch, alternate boot, stock update and service/debug routes as unproved candidates until observed.

Enumerate all potential writes: application/rootfs, NAND banks, environment, persistent eMMC/project data, calibration/identity and panel payloads. Determine whether a temporary program causes hidden persistent side effects. A/B bank labels cannot justify rollback of shared state.

**Reviewable output:** Acceptance/check coverage and candidate write maps; volatile/persistent/unknown classification; minimum harmless foothold and recovery test proposals.

**Exit evidence:** No untraced acceptance branch or destination needed by the chosen route is silently assumed. Actual permitted execution is established at P07/M04; artifact parser success alone does not close it.

**Stop/replan:** Required-layer restriction, route needs undocumented bypass, unknown broad writes or recovery relies on startup of the changed component. Compare another legitimate layer/route; move P09 before any persistent trial.

## P07 — Establish stock reference, then the harmless foothold

**Proposed accountable role:** Hardware-session owner with package owner supplying identified artifacts. **Prerequisites:** P03 availability/access and M02-P/C for first acquisition; P01 reference scope; P06 before changed execution. H precedes active trials; P09 supplies Q/T before any persistent exposure. M02-R follows first acquisition and precedes comparison/reproducibility claims. **Scope bound:** Stock observation and one selected-layer execution proof, not feature implementation.

Prepare two separately reviewable stages. First capture actual stock boot, relevant device/mount/calibration facts, one known-stimulus audio output when affected, and the selected panel/control reference. Then, only through a supported route, propose a harmless compatible program that reports identity and exits, or a bounded functional-data load for A. Record actual side effects and successful return to stock.

Before the active stage, specify failure domain and an independently evidenced stop/reset/stock-return path that survives it; intervention owner, finite bounds, observability loss and operator-stop triggers; affected device handoff and supported electrical/audio/gain/clock/output limits, using appropriate isolated capture connections. Record stock storage/peripheral effects of reset/power cycle. A graceful exit or no firmware writes does not establish H. Passive capture needs only applicable connection/observation controls. Alternate boot uses its own admitted policy/H/recovery scope rather than requiring unrelated stock-userspace execution.

**Reviewable output:** Stock/reference session proposal and foothold protocol, with exact inputs, expected receipts and teardown/failure handling. These documents themselves run neither.

**Exit evidence:** First M03 unit/reference from P/C, subsequent M02-R reproduction, and route-specific M04 changed execution with pre-exposure H and applicable Q/T. These are separate receipts. A standalone foothold leaves app attachment open until BM; compatible observations can share a controlled session without weakening attribution.

**Stop/replan:** Unsupported ABI, unexpected persistence, missing unit policy/readiness or inability to return to stock. No escalation from a failed harmless probe to a changed firmware update without M09.

## P08 — Close the affected interface and workload uncertainty

**Proposed accountable role:** Selected interface/processing engineer; hardware owner integrates observations. **Prerequisites:** P01/P05 and M02-P/C; P07/M03 for stock measurements. Minimal target probes require route-specific execution, H, selected mechanism prerequisites and M09-Q/T if persistent; reproduction-dependent comparisons require R. **Scope bound:** M01 workload and smallest representative interface/cost discriminator, not a complete feature/port.

For a local change, correlate baseline getter/input, original setter request, owner-thread/deferred application, processing state and meaningful output. For D/E/F, prove independent initialization/ownership of one indispensable real interface using retained support where possible, with original app exclusivity relinquished explicitly. Extend to all indispensable interfaces before the branch gate passes.

At M05-A, record measured stock effective clocks/configuration and required concurrent workload, resources/deadlines; minimal measured candidate costs or justified conservative bounds; whether new work consumes or replaces stock work; instrumentation effects, excluded costs and unknown integration. Declare reserved margin and reopening thresholds before reading the result. A separately scoped prototype/processing/cost probe may answer this without full implementation. If no meaningful bound is possible, resource-dependent commitment stays pending and selects a smaller discriminator. M05-Q later measures actual integrated concurrent target workload, including relevant driver/interrupt/copy/storage costs and overruns. Isolated benchmarks, idle headroom and emulator results cannot pass Q.

Identify source/toolchain correspondence only for components needing rebuild/change. Full LTIB reconstruction is not the first discriminator. Software buffer tests can prove selected algorithm behavior, not codec clocks or analog-filter control.

**Reviewable output:** M05 contract, baseline/candidate resource-budget method, retained-platform reuse result and component build/missing-dependency ledger.

**Exit evidence:** A clearly separates measured capacity, candidate cost bounds and unknowns for conditional M06. Q closes actual integrated applied-state/output/resources at selected substrate/M07/M08 joins before target compliance or M08 can pass. Mark partial evidence as partial. Null calls, core requests or emulator RSS supply neither physical capacity nor candidate deadline proof.

**Stop/replan:** Hidden proprietary initialization, incompatible device sharing, weak output oracle, insufficient headroom or missing indispensable code. Try a justified smaller algorithm/interface; use E/F only if a platform requirement is implicated.

## P09 — Qualify recovery before persistent exposure

**Proposed accountable role:** Installation/recovery owner. **Prerequisites:** P06 write scope, P03 unit/state, P02 preserved inputs, P04 validity; suitable recoverable arrangement and H for active restoration/qualification tests. **Scope bound:** Exact selected installation/write scope.

For a repack route, prepare unchanged ISO→UPD equality and separately source-authoritative container assembly checks. Compare paths/types/content/modes/owners/links/hardlinks/required timestamps/xattrs/nodes and actual layering; account for 60 tar-directory/22 recorded SFS-file discrepancies. Do not generate an image from macOS fixture metadata. For another installer, specify equivalent exact file/metadata/destination checks instead.

Prepare backup/restoration interpretation for actual NAND ECC/OOB/bad blocks, UBI/eMMC/environment/calibration and any panel effects. Distinguish readback, recovery entry, restoration and interrupted-install rollback. Model failure cases offline first. Recovery must survive failure of what the candidate changes; stock application startup is not an independent fallback for application failure.

**Reviewable output:** Reusable M09-Q route/checks/write/backup/recovery evidence and exact M09-T receipt for each proposed persistent trial. T binds candidate/container/installer identities, eligible unit/release, allowlisted content/metadata changes, all relevant destinations, candidate-dependent state effects and the applicable backup/restoration/interruption envelope. Confined data writes qualify that scope; broad updates qualify every destination they can affect.

**Exit evidence:** Q proves offline fidelity and independent recovery for the scope; before first modified installation it also has actual unchanged-route acceptance on a suitable recoverable target or equivalent retained receipts. Byte-equal ISO encoding alone is insufficient; do not reflash stock redundantly. Exact T must bind before every persistent foothold/branch/feature attempt, not first at M10. Requalify changed route/structure/destinations/failure assumptions and reuse unaffected evidence. M10 still qualifies the final pilot's functionality/restart/state/failures. No safe suitable arrangement leaves the route pending.

**Stop/replan:** Recovery entry only, unexplained metadata/routing differences, unprotected unique state, no suitable test arrangement, failed restoration or enlarged write scope. Permit no persistent exposure based on speculation; retain only a separately demonstrated volatile route.

## P10 — Make the architectural decision concrete

**Proposed accountable role:** Technical director and independent architecture reviewer. **Prerequisites:** M01, P/C and available M05-A/access ledger for conditional selection. Actual mechanism/substrate and execution/resource proofs constrain subsequent commitment. H/Q/T apply to exposed probes. **Scope bound:** One conditional route and its smallest discriminator, with rejection/reopening criteria; no automatic broad commitment.

Review A/B if data or a real independent control boundary supplies the feature; otherwise compare C with D. Prefer D when broad required behavior makes bounded patches implausible and vendor support is independently usable. Prefer E only for an actual platform requirement, and F only for measured benefit justifying board/service reconstruction. Record retained/replaced layers, required compatibility, delivery mechanism, unclosed branch gates and regressions.

For A/B/C, mandate BM before substantial feature work: actual functional data loading for A; independent execution/coexistence/interfaces for standalone B; actual loaded interception/ownership/ABI for interposing B; exact accepted in-place path change for C, or added executable loading/placement/entry/return with applicable ARM mode/ABI/relocation/memory/cache/thread contracts. Do not demand an irrelevant hook from independent B, a generic plugin system or proprietary source rebuilding. A no-op integration proves mechanism only. An emulator proof leaves on-device attachment acceptance open. D/E/F use their selected substrate gates; E/F may establish execution through admitted boot rather than stock-userspace access.

**Reviewable output:** M06 option decision proposal, nearest demonstration work decomposition and any evidence-based estimate range with assumptions. No range should be invented before relevant interfaces, route and validation effort are identified.

**Exit evidence:** Record conditional versus demonstrated decision, mandatory mechanism/cost/substrate discriminator and withheld broader commitments. Material candidate/integration unknowns remain conditional until Q and declared thresholds close them. Independent review and any execution authorization remain separate; the roadmap is neither.

**Stop/replan:** Selected route still depends on assumed access, plugin API, general emulator fidelity, automatic A/B rollback, missing ownership or unbounded replacement compatibility. Re-open the evidence question rather than disguise it as an implementation task.

## P11 — Prepare the first custom-feature demonstration

**Proposed accountable role:** One candidate integration owner, separate acceptance reviewer, hardware-session owner. **Prerequisites:** M01, P/C/R for reference comparisons, relevant M05-A and conditional M06 with applicable BM/selected substrate proof before substantial work. On-unit acceptance requires actual M03/M04/selected mechanism/substrate, H, M05-Q and exact Q/T if persistent. **Scope bound:** One feature and relevant comparison/regressions; offline software proof does not require unrelated target evidence.

Any subsequently prepared main-project prompt must specify isolated-copy/target scope, exact candidate and mechanism identity, legal state/output oracle, regressions, cost/qualification limits and applicable H/Q/T intervention/admission receipts. Preparing or sending an implementation prompt is outside this revision. A minimal mechanism/cost probe does not authorize a broad feature or port.

M07 software proof and M08 physical proof can share one controlled experiment if both contracts are evidenced. Repeating existing HOME/MIXER is necessary only for an affected regression or independent restoration, not as new functionality. Repeat the new physical feature in a fresh launch/session; reserve sustained qualification for M11.

**Reviewable output:** Concrete scoped demonstration proposal and evidence matrix; later authorized execution supplies candidate and results.

**Exit evidence:** M07 and M08 as defined in the roadmap. A working emulator feature remains software proof if physical acceptance is absent.

**Stop/replan:** Feature output differs only cosmetically, direct observer writes cause the result, physical state/timing diverges, persistence is discovered, or necessary stock regressions fail. Preserve valid narrower evidence and re-enter the affected gate.

## P12 — Expand only from demonstrated capability

**Proposed accountable role:** Program/release owner. **Prerequisites:** M08 and explicit product/support decisions; applicable M10-P or M10-N before M11. Q/T precede actual persistent effects. **Scope bound:** Selected delivery/reuse frontier rather than a speculative multi-year backlog.

After first hardware proof, determine remaining work for repeatable installation, restart/state integrity, full supported regressions, load/reliability limits, reproducible release, compatibility and distribution. Use the interface/workload evidence to justify campaign sizes and any effort ranges. Then select a second distinct feature to test the durability of shared contracts at M12.

If installed persistence is selected, qualify M10-P using Q/T and install/restart/rollback evidence. If the owner expressly selects a non-installed product, qualify M10-N through repeatable acquisition/launch, fresh stock restart/relaunch, affected-state integrity, H after candidate failure, eligibility and advertised behavior. Persistent launcher/configuration/automatic start belongs to P, even if code is RAM-loaded. Both paths retain M11 artifact reproduction, load/reliability and supported-function tests; N cannot claim installed firmware or automatic startup.

For M12 declare the reuse/maintenance claim before picking feature two. Exercise a materially different relevant dependency or supported version/state condition and record newly required reverse engineering/adapters/shared-contract changes. If both features only validate one narrow interface, advertise that envelope. Add no unrelated functions solely to enlarge the test (RC07).

**Reviewable output:** Re-estimated pilot/qualification proposal, supported configuration/function envelope, maintenance policy and next-feature decision. A complete replacement OS, if explicitly required, gets BE/BF and its whole selected instrument suite; it cannot inherit proof from a userspace demonstration.

**Exit evidence:** Qualified P or N delivery pilot plus M11 supported release, and claim-specific M12 reuse evidence. Product demonstration, selected delivery and supported release remain separate claims. No owner intent or actual capability is selected/closed by this revision.

**Stop/replan:** Qualification exposes new failure classes, support/distribution scope expands, every feature needs broad private reconstruction or measured platform limits change. Revisit M01/M06 and preserve valid prior results.

## Work to defer or discontinue as milestones

| Work | Proposed disposition | Reactivation condition |
|---|---|---|
| Unchanged HOME/MIXER/roster reruns | Do not count as forward feature progress | Independent restoration, changed-method validation or affected regression |
| Send continuation from old handoffs | Defer; stale package receipt cannot establish launch readiness | Selected feature requires this legal state path and complete relevant transport/gates are evidenced |
| Universal emulator syscall/timer/device fidelity | Defer | A named inference cannot be answered more directly and depends on that contract |
| Emulator throughput/RSS optimization | Defer as a program milestone | Measured research-resource bottleneck blocks the selected bounded test; valid comparisons can discriminate a remedy |
| Complete effects, panel and UI reconstruction | Defer | Chosen feature or preserved-function contract actually requires the additional surface |
| Full BSP/toolchain/package rebuild | Defer | Selected components must be rebuilt/changed, with source lineage evidence |
| Whole-machine emulation | No default successor milestone | Specific boot/kernel question and model effort have a demonstrated advantage over access/native/isolated observation |
| New Linux, RTOS, panel or bootloader rewrite | No default implementation commitment | M06 evidence justifies that layer and branch-specific policy/recovery gates are planned |
| New overlapping archives/copies/handoffs | Avoid duplication | Current custodian identifies a missing indispensable recoverability requirement |

## Effort and independent review boundary

The bounds above limit investigation scope, not forecast duration. The owner-selected investment tranche limits sustained effort without inventing delivery dates/probabilities; unresolved probes cannot renew it themselves. After meaningful mechanism/interface/cost evidence, estimate only the selected work and validation with explicit unknowns. Historical emulator observation duration is not implementation cost. Owner resource/route limits remain an open decision for future work.

Independent review should resolve the product choices, assess feasibility gates and write/recovery ordering, and decide whether any future action deserves a separate authorization. This document stops at proposing those actions. No prompt is sent and no implementation follows.
