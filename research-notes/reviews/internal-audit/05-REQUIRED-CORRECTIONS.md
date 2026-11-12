<!-- source: ../PioneerSP16Review/05-REQUIRED-CORRECTIONS.md | scrubbed -->

# Stage 5 — Required corrections

Review date: October 9, 2026, America/Chicago. Companion [audit] `Review/05-ROADMAP-AUDIT.md` (evidence not published) supplies evidence, consequences and severity. These are concrete instructions for a future authorized revision and its review. They do not modify Stage 4, authorize implementation or permit sending a prompt to another chat.

Six Major corrections are conditions of the advisory recommendation. Close each by a consistent contract revision and independent readback before its affected gate begins. A condition can be marked inapplicable only with a recorded product/route decision and the reason it removes that exposure. Unknown feasibility is not an applicability waiver. Historical evidence must remain unchanged.

## Required correction register

| Correction | Rank | Required before | Proposed future accountability | Closure artifact |
|---|---|---|---|---|
| RC01 / A01 | Major | Scheduling or closing M02/M03 | Roadmap owner and evidence-method reviewer | Consistent partial M02 contracts and hardware-first dependency walk |
| RC02 / A02 | Major | M05 resource-feasibility acceptance or M06 resource-dependent commitment | Architecture/performance reviewer | Measured/bounded/unknown resource ledger and integrated qualification join |
| RC03 / A03 | Major | Active on-unit code/device/boot trials | Hardware-session owner and safety reviewer | Applicable intervention/output-envelope readiness contract |
| RC04 / A04 | Major | Earliest persistent M04/branch/M07/M08 trial | Installation/recovery owner and candidate integrator | Exact per-trial candidate-to-qualified-scope binding |
| RC05 / A05 | Major | M01 delivery-path selection and M10/M11 qualification planning | Product/release owner | Route-specific production prerequisite or explicit persistent requirement |
| RC06 / A06 | Major | Substantial C or B-interposition implementation at M07 | Firmware/reverse-engineering reviewer | Selected mechanism feasibility gate, proof or explicit inapplicability |
| RC07 / A07 | Minor | M12 test design | Architecture/acceptance reviewer | Second-feature discriminator and bounded reuse claim |
| RC08 / A08 | Minor | Sustained feasibility investment | Human project owner/program reviewer | Chosen investigation tranche and review/stop decision |

Roles describe future accountability, not assignments or delegated work. Closure of a planning correction does not mean the underlying physical capability has been demonstrated.

## RC01 — Make M02's partial readiness explicit

**Revise:** M02/M03 in the master roadmap, their table/diagram joins, and P02/P04/P07. The master presently requires M02 for M03 conclusions while the authoritative table requires only its capture contract. [master] `Review/04-MASTER-ROADMAP.md:79` (evidence not published), [table] `Review/04-DEPENDENCY-MAP.md:58` (evidence not published).

Specify three separately reviewable subsets without creating new competing packages:

1. Preservation of indispensable inputs/evidence and a usable recovery location.
2. A source-bound, tested capture/reporting method ready to observe the selected reference, with applicable containment and hardware connection conditions.
3. Independent restoration/reproduction of the reference used for subsequent comparisons.

State that a separately authorized first M03 stock acquisition may consume subsets 1–2 and supply the reference needed by subset 3. Full relevant independent reproduction must precede comparisons claiming reproducibility. Keep emulator replay conditional on actually relying on that emulator.

**Acceptance:** The revised dependency walk reaches stock reference acquisition without requiring the reference to exist already. It also reaches independent reproduction before candidate/reference acceptance that relies on it. No diagram contradicts the authoritative table; no broad emulator restore is required for a hardware-only method. Do not conduct the acquisition or reproduction as part of a document correction.

## RC02 — Separate architecture admission from integrated performance proof

**Revise:** M05/M06/M07/M08, K12 and P08/P10. [M05] `Review/04-MASTER-ROADMAP.md:118` (evidence not published), [K12] `Review/04-RISK-REGISTER.md:196` (evidence not published).

Define the resource contract around the M01 workload rather than a generic CPU percentage:

- Stock target measurements: effective configuration/clocks, required concurrent behavior and resources/deadlines.
- Minimal candidate cost evidence: bounded prototype, representative processing test or justified conservative bound. Identify what it excludes and whether the candidate consumes or replaces stock work.
- Integration uncertainties and required reserved margin, selected before the admission result is read.
- A conditional M06 decision if material costs remain unresolved, with explicit rejection/reopening thresholds.
- Integrated candidate measurements at the appropriate substrate and M07/M08 joins. These close actual target behavior; preliminary budget estimates cannot do so.

Allow a separately scoped minimal on-target cost probe after its access, mechanism, safety and recovery prerequisites. Such a probe is feasibility work, not permission for a broad feature implementation or port. If no meaningful cost bound is possible, mark the relevant claim pending and choose a smaller discriminator.

**Acceptance:** A reviewer can distinguish measured capacity, measured candidate costs, conservative assumptions and untested integration. Stock idle headroom, an emulator result or an isolated benchmark cannot alone pass candidate deadline compliance. No full implementation is required merely to start M05. The plan identifies where unresolved costs must close; actual numbers await authorized measurements.

## RC03 — Add scope-specific active-hardware readiness

**Revise:** M04/M05, selected BD/BE/BF, M07/M08, Route V and applicable K risks. [volatile exception] `Review/04-DEPENDENCY-MAP.md:92` (evidence not published), [replacement substrate conditions] `Review/04-MASTER-ROADMAP.md:157` (evidence not published).

Keep two different obligations explicit: persistent state restoration under M09, and intervention/physical operating limits for any active hardware trial. Specify before launch:

1. What may fail: application, device owner, console, kernel or boot path.
2. The stop/reset/return-to-stock mechanism that remains available independently of that component, and how its applicability is established.
3. Finite trial bounds, loss-of-observability conditions, operator stop triggers and ownership of intervention.
4. Affected audio/output levels, gain, codec/clock configuration and device transactions that remain within the supported operating envelope; appropriate isolated capture/test connections where relevant.
5. Stock storage and peripheral state that a reset or power cycle might affect, even when the candidate is intended to be volatile.

This is a concrete pre-exposure condition, not an instruction to deliberately crash a kernel, modify fuses, interrupt irreplaceable storage or prove every imaginable fault. A passive stock capture needs only its applicable observation/connection controls; a privileged replacement boot needs broader intervention evidence.

**Acceptance:** The protocol survives a candidate that cannot execute its own teardown. Absence of persistent writes and one graceful exit are insufficient closure. Actual intervention evidence and electrical/output limits require a future separately authorized hardware scope; document revision alone does not supply them.

## RC04 — Require exact persistent-candidate admission before exposure

**Revise:** M09's dependency paragraph, M04/branch/M07/M08 preconditions, P09 and K16. Final pilot binding currently appears at M10 despite earlier persistent trials. [M09] `Review/04-MASTER-ROADMAP.md:209` (evidence not published), [P09 exit] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:152` (evidence not published).

Separate reusable route/recovery qualification from candidate-specific admission. The latter must join:

- Exact candidate, container and installer identities, plus eligible unit/release.
- Original-to-candidate allowlisted changes in content/metadata and all relevant destination/routing checks.
- Actual and possible candidate-dependent persistent effects, including project/schema/environment/calibration/panel state where implicated.
- The already qualified backup/restoration and interruption/failure envelope that covers this exact exposure.
- Explicit requalification triggers for changed route, destination, artifact structure or failure assumptions.

Before the first modified persistent installation, require actual acceptance of the unchanged route on a suitable recoverable target or equivalent existing demonstrated acceptance. An ISO→UPD byte-equal transform remains separate evidence. Do not add a redundant stock reflash if valid existing receipts already close the same route. If no suitable safe arrangement exists, the route stays pending.

**Acceptance:** The first persistent foothold or feature trial has an exact applicability receipt before execution. No candidate inherits generic M09 approval because its source diff is small. M10 retains final pilot functionality, restart/data and scoped failure qualification. This correction proposes no installation or destructive testing.

## RC05 — Make production delivery qualification conditional on product intent

**Revise:** M10/M11 and their diagram/table dependencies, P12 and Route V's continuation. [M10/M11] `Review/04-MASTER-ROADMAP.md:222` (evidence not published).

If M01 requires installed persistence, retain M09→persistent M10→M11. If the owner explicitly selects a non-installed product, provide an equivalent delivery-qualification path that proves repeatable artifact acquisition/launch, fresh stock restart and relaunch, relevant data/state integrity, intervention after trial failure, compatibility and advertised behavior. Both paths retain reproducible artifacts and M11 load/support qualification.

Classify any persistent launcher, configuration or automatic-start integration as a persistent route regardless of whether the feature executable is loaded into RAM. Describe excluded startup/persistence capabilities in product claims.

**Acceptance:** A genuinely non-installed supported product can reach M11 without a persistent pilot. Alternatively, record the owner's actual persistent-product choice and why the nonpersistent branch is inapplicable. This decision belongs to the human owner; the reviewer must not silently add persistence to M01.

## RC06 — Add the missing modification-mechanism discriminator

**Revise:** M05/M06's applicable interface ledger, the A/B/C path and P10/P11. [M06 prerequisites] `Review/04-MASTER-ROADMAP.md:131` (evidence not published), [Stage 3 mechanism uncertainty] `Review/03-STRATEGIC-OPTIONS.md:28` (evidence not published).

For the selected route, distinguish execution access, original state knowledge, attachment mechanism and new functionality. Require mechanism proof or a mandatory small gate before substantial implementation:

- A: the actual functional data-loading boundary and constraints; no cosmetic-resource surrogate.
- Independent B: usable separate execution and required coexistence/interfaces; no irrelevant internal hook test.
- Interposing B: actual interception of the needed call/control boundary under the loaded runtime, with ownership and relevant ABI contracts.
- C in-place: exact target/version/bytes, valid change and accepted execution of the affected path.
- C with added code: feasible executable placement/loading, control transfer/return, relevant ARM mode/ABI/relocations and memory/cache/thread contracts, with a bounded reversible integration test.

Do not require generic extension infrastructure or rebuild the proprietary application from nonexistent source. A smallest no-op/identity integration probe supplies mechanism evidence only; it cannot pass M07/M08 feature acceptance. A provisional architecture decision may select this probe while withholding broader implementation commitment.

**Acceptance:** The plan cannot send a deep feature implementation forward solely because a stand-alone utility runs and a stock getter/setter was observed. Its mechanism uncertainty is either demonstrably closed, assigned to a mandatory bounded discriminator or genuinely inapplicable. Existing Send snapshots remain no-mutation evidence.

## RC07 — Improve M12's reuse test

**Rank:** Minor; does not block adoption. [M12 acceptance] `Review/04-MASTER-ROADMAP.md:253` (evidence not published).

Name the reuse/maintenance claim before selecting the second feature. Exercise a materially different dependency or supported condition relevant to that claim; record new reverse engineering and changes to shared contracts. If the two features only validate one narrow interface, advertise that envelope rather than broader OS extensibility.

**Acceptance:** A second feature count cannot substitute for evidence of the claimed reuse boundary. Do not add unrelated hardware or functions solely to make the test larger.

## RC08 — Bound feasibility investment

**Rank:** Minor; does not block adoption. [scope-based bounds] `Review/04-MASTER-ROADMAP.md:44` (evidence not published), [P06 route scope] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:106` (evidence not published).

Ask the human owner to select a resource/effort tranche, candidate-route limit and review point before sustained feasibility work. Define stop, narrow-scope, acquire-access and architecture-pivot outcomes. Avoid invented delivery dates or probabilities. Existing attempt/session authorizations still apply; an investment tranche grants no additional execution authority.

**Acceptance:** Successive pending investigations cannot renew their own budget without an owner decision and a stated new discriminator.

## Review procedure and stop boundary

A future revision should amend the four Stage 4 proposal documents consistently and include one concise disposition table for RC01–RC08: addressed, explicitly inapplicable, or unresolved; proposed owner; evidence/contract locator; affected gate. Do not copy this review into competing authorities or alter historic results. Recheck only the changed contracts and their dependency walks, including hardware-first, emulator-assisted, persistent and non-installed paths and the selected replacement branch if relevant.

Document review closes planning ambiguities. Actual feature selection, resource measurements, accepted execution, intervention, restoration and hardware functionality remain separate open capabilities until their own authorized evidence exists. No corrective work, prompt preparation for implementation, dispatch or experiment was initiated by this delivery.
