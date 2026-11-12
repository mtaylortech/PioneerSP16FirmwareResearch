<!-- source: ../PioneerSP16Review/04-RISK-REGISTER.md | scrubbed -->

# Stage 4 — Risk register

Proposed for independent review. October 9, 2026, America/Chicago.

Revision 2 incorporates the unchanged [Stage 5 corrections] `Review/05-REQUIRED-CORRECTIONS.md` (evidence not published). The sole RC01–RC08 disposition table is in the master roadmap. Planning contracts are corrected; product decisions and physical closure evidence remain open. M02-P/C/R, M05-A/Q, H, BM, M09-Q/T and M10-P/N refer to its staged contracts.

This register gives review instructions for risks to the proposed Pioneer SP-16 roadmap. It authorizes no mitigation work, hardware action, engineering-record amendment, delegation or communication. All controls below are proposals for later scoped authorization. Milestones are defined in the [master roadmap] `Review/04-MASTER-ROADMAP.md` (evidence not published); ordering is in the [dependency map] `Review/04-DEPENDENCY-MAP.md` (evidence not published) and [next actions] `Review/04-PRIORITIZED-NEXT-ACTIONS.md` (evidence not published).

## Register conventions

Evidence classifications describe the present fact or uncertainty, not a calculated failure probability. **Known defect** means an inspected condition violates a necessary contract within its stated scope. **Unverified dependency** means the required capability has not been demonstrated. **Indeterminate** means available evidence cannot distinguish explanations. **Conditional exposure** means the risk applies only to the selected architecture/support/distribution scope.

Priorities:

- **Decision blocker:** Can invalidate the first-feature route or prevent a meaningful architecture choice.
- **Exposure blocker:** Must close before persistent state or irreplaceable assets are exposed.
- **Validation blocker:** Must close for the particular claim/method to be accepted.
- **Qualification risk:** May leave a technical demonstration valid while preventing production support or wider scope.

These priorities overlap and do not imply probability scores. No reviewed evidence supports numerical likelihood, cost, schedule reserve or risk burndown percentage. Suggested accountable roles are future ownership recommendations, not assignments. No risk is marked closed solely because a planned milestone addresses it.

## Risk index

| ID | Risk / present evidence state | Priority | Closure or scope gate | Future accountable role |
|---|---|---|---|---|
| K01 | First feature and preservation boundary undefined — unverified requirement | Decision blocker | M01, revisited M06/M12 | Product/technical director |
| K02 | Indispensable research assets cannot be independently restored — unverified recovery | Exposure/validation blocker | M02 | Evidence/environment custodian |
| K03 | Suitable unit/access not demonstrated — unverified dependency | Decision blocker | M03 | Hardware-session owner |
| K04 | Permitted execution and complete acceptance unknown — unverified dependency | Decision/exposure blocker | M04; BE/BF policy; M09/M10 | Acceptance/deployment owner |
| K05 | Recovery fails or unit-specific state is lost — unverified dependency | Exposure blocker | M09; M10 scoped failures | Recovery/hardware owner |
| K06 | Execution/state knowledge is mistaken for attachment or new behavior — mechanism unverified | Decision/validation blocker | BM; M05/M07/M08 | Feature integration owner |
| K07 | Stale source, circular controls and false success reporting — known defects | Validation blocker | M02 and every experiment | Experiment-package owner |
| K08 | Emulated clocks/device semantics invalidate required inference — known scoped defects | Validation blocker when method relies on them | M02/M05/M07; target timing at M08 | Runtime/measurement owner |
| K09 | Hardware support cannot be reused independently — unverified dependency | Decision/qualification risk | M05; BD/BE/BF | Interface/platform owner |
| K10 | Required original functions/project state regress — unverified compatibility | Decision/qualification risk | M01/M07–M11 | Compatibility/validation owner |
| K11 | Required source/build/ABI cannot be reproduced — unverified correspondence | Conditional decision/qualification risk | M05; BD/BE/BF; M11 | Build/platform owner |
| K12 | Preliminary budgets mistaken for integrated deadlines — unverified performance | Decision/qualification risk | M05-A/Q; M08/M11 | Processing/performance owner |
| K13 | Research or patch scope expands without useful capability — evidenced workflow exposure | Decision/qualification risk | M06, repeat reviews, M12 | Technical program director |
| K14 | Archive/record/path drift causes wrong evidence authority — known drift; archive aggregate indeterminate | Validation/preservation risk | M02 and each package | Evidence/integration custodian |
| K15 | Rebuilt image inherits invalid host metadata — known extraction fidelity defect | Exposure blocker for assembly | M09; BE/BF | Image assembly owner |
| K16 | Small change triggers broad hidden update writes — unverified routing | Exposure blocker | M04 classification, M09/M10 | Installation/recovery owner |
| K17 | Distribution inputs/rights/provenance unsuitable — origin unverified; conditional exposure | Qualification risk | M02 provenance; M11 distribution review | Release/provenance owner |
| K18 | Active trial lacks independent intervention or bounded physical outputs — unverified readiness | Exposure blocker for active hardware, including volatile | H before active M04/M05/BM/branches/M07/M08/M09 tests | Hardware-session owner / safety reviewer |

## K01 — Undefined functional destination and compatibility scope

**Basis:** G15; F01/R01; Stage 3 X01 and options. There is no selected first feature, exact observable acceptance or preserved-function contract. The long-term OS ambition is insufficient to choose a layer.

**Failure mode/consequence:** Work optimizes emulator completeness or rewrites a platform without delivering useful behavior. Application replacement is underestimated if all original functions/formats are silently required.

**Trigger/replanning:** Proposed implementation has no input/state/output oracle; “new OS” expands to sampler, panel and bootloader without agreement; compatibility/distribution requirements change.

**Proposed controls:** M01 selects one vertical feature, target, persistence and preserved/excluded functions. M06 compares layers against that contract; M12 revisits broader scope using demonstrated capabilities. P01 is the next proposed action.

**Closure evidence:** A separately endorsed contract and requirements-to-observation matrix with testable results and explicit decisions. Numerical thresholds cannot remain missing when their acceptance is tested.

**Residual/branch effect:** A contract does not prove feasibility. New requirements reopen affected interface, delivery and regression gates. Current status: open; no feature is selected by this register.

## K02 — Loss or non-restorability of indispensable research assets

**Basis:** G16/G17; F11/F15/R14; C22/C23. Local Git excludes originals, raw evidence, runtimes/rootfs and databases. Same-disk archives were incomplete/indeterminate at prior checkpoints; restore metadata failures do not themselves prove byte loss.

**Failure mode/consequence:** A future checkout cannot reproduce accepted evidence or a candidate; cleanup/storage work removes the sole usable input/environment. Lost evidence can force rediscovery or make a claim unverifiable.

**Trigger/replanning:** Missing original bytes/dependencies, no independently accessible off-device backup, unexplained consequential restore differences, or conflicting storage operations.

**Proposed controls:** P02/M02 coordinate with the custodian and protect indispensable assets at P; C supplies ready truthful capture. Initial M03 acquisition may provide R's reference, so do not require reproduction of that reference first. Independently restore/reproduce before comparisons relying on it; full M02 verifies off-device recovery. Preserve failed receipts and consequential metadata distinctions; avoid overlapping archives.

**Closure evidence:** Selected asset/environment manifests, independent off-device recovery and separate content/type/link/required-metadata verification plus reference replay/capture.

**Residual/branch effect:** Restoration proves only tested coverage. Old unbound execution revisions remain qualified. Hardware-first work need not restore irrelevant emulator copies. Current status: open; final archival state not recertified here.

## K03 — No usable unit or physical observation route

**Basis:** G04/G05; F02/R03; X02. Documentary parts, intended boot scripts and software maps exist; actual unit identity/access/boot are unestablished in reviewed evidence.

**Failure mode/consequence:** Software proof is promoted to physical feasibility, or engineering commits to drivers/deployment that cannot be tested on the target.

**Trigger/replanning:** Unit unavailable, stock boot unhealthy, inaccessible console/service route, unknown electrical connection or target differs from held release.

**Proposed controls:** P03 inventories actual availability/access first. M03 observes stock identity, boot, relevant mounts/devices and behavior. Keep documentary leads separate from working command access.

**Closure evidence:** Unit-linked access and stock-reference receipts adequate for the selected feature, with exact read-only observation limits.

**Residual/branch effect:** Access is not execution, authentication policy or recovery. Without access, M08 remains unavailable; only bounded offline work can pass its own research gates. Current status: open.

## K04 — No permitted execution route or incomplete acceptance model

**Basis:** G14; F04/R08; C08; X03. Decryption/CRCs are verified; complete updater/version/destination checks, actual unit policy, userspace execution and alternate boot permission are not.

**Failure mode/consequence:** A parser-valid package is rejected later, code cannot run, or policy at one layer is wrongly generalized to all layers. Feasible userspace changes may be missed, while a replacement boot path may be assumed.

**Trigger/replanning:** Untraced acceptance branch, observed required-layer restriction, incompatible loader/ABI, or proposed route depends on an undocumented bypass.

**Proposed controls:** P06 traces the whole relevant chain using shipped artifacts and unit policy. M04 demonstrates harmless changed execution through a legitimate route. BE/BF separately prove boot-layer acceptance; M09/M10 qualify installation. No fuse changes or authentication bypass is assumed.

**Closure evidence:** Actual identity-bound execution at the selected layer and side-effect classification; full relevant checks/routing and actual install acceptance for persistent claims.

**Residual/branch effect:** Passing one layer leaves other layers unknown. Reject only the affected route unless evidence is broader; no viable route stops physical delivery. Current status: open, no signature presence/absence asserted.

## K05 — Non-independent recovery and loss of unique unit state

**Basis:** B13/G14; F04/R03/R08; X05. Declared NAND banks and default update status do not demonstrate rollback; geometry/ECC/OOB/UBI/calibration/environment readback and restoration are absent.

**Failure mode/consequence:** Candidate breaks the software needed by the stock updater; restoration uses the wrong NAND interpretation; shared identity/calibration/project/panel state cannot be recovered.

**Trigger/replanning:** Recovery depends on the changed component, backup cannot be accessed/restored, recovery entry is mistaken for restoration, write scope grows, or no safe recoverable test arrangement exists.

**Proposed controls:** M09-Q maps exact state and proves independent scoped restoration; M09-T binds every exact persistent candidate/installer/unit before exposure. Confined data-file changes need their data recovery scope; a broad updater needs all affected state. H separately protects intervention/output for active trials, including recovery tests. Model failures first; never manufacture a brick. M10-P/N qualify actual selected lifecycle and persistent effects.

**Closure evidence:** Unit-specific backup interpretation and observed restoration/rollback under defined failure/write cases, independent of what can fail. Raw dump equality alone cannot certify cross-method NAND restoration.

**Residual/branch effect:** Recovery is scope-specific; kernel/panel/bootloader changes can require new mechanisms. If unclosed, persistent exposure is blocked; a separately verified wholly volatile route can remain viable. Current status: open.

## K06 — Wrong ownership/mechanism or UI-only feature proof

**Basis:** G08–G10; F08/F09/R09; C03–C05/C19; X06/X08. Static encoder bytes and two value-zero Send snapshots are accepted; legal input, deferred application, processing and changed output remain unverified.

**Failure mode/consequence:** A standalone utility and stock setter observation leave the attachment between them unproved. Wrong widget/shared return, identifier conflation or observer write creates false evidence; a patch changes display without processing or violates private invariants.

**Trigger/replanning:** Actual operands disagree, worker→owner contract is missing, no applied-state/output correlation, result is cosmetic, or a local change needs broad private reconstruction.

**Proposed controls:** P05/P08 trace selected ownership/gates/transport. Conditional M06 requires BM before substantial A/B/C work: real data loading, independent coexistence/interfaces, loaded interception or exact accepted in-place/added-code integration as applicable. Added-code proof covers relevant ARM mode/ABI/relocation/memory/cache/thread entry/return. A no-op probe establishes mechanism only. M05/M07/M08 separately prove legal applied state and new meaningful output, with independent controls and actual frame/thread operands. Excluded async material remains excluded.

**Closure evidence:** Selected BM attachment/data/change proof, distinct from execution access and stock state knowledge; then legal input→request→owner/deferred application→processing/state→defined new output and relevant regressions. Independent companion needs no irrelevant hook; emulator mechanism proof cannot certify physical loading. One-count edits need not change quantized fill; use the appropriate oracle.

**Residual/branch effect:** One path does not establish all listeners/panel controls. Broad invariants can favor D, but one failed hook does not prove C impossible. Current status: open.

## K07 — Source-binding defects, circular controls and false aggregate success

**Basis:** F08/F12/R10; C02–C05/C11–C14. Corrected Send source differs from its saved validation hash; historical controls share the wrong identifier premise; zero exits coexist with failed checks/worker faults; send summaries conflict with primary evidence.

**Failure mode/consequence:** Wrong code is considered validated, a negative case confirms the implementation's mistake, or milestone/cleanup/transport success hides invalid observations and missing duration/finals.

**Trigger/replanning:** Manifest hash mismatch, required validity false with pass summary, unlogged expected/actual operands, missing final, ineffective watchdog or helper/guest send disagreement.

**Proposed controls:** P04/M02 freeze actual identities, derive controls independently and report validity/milestone/observation completion/cleanup separately. Capture actual inputs and effective bounds; keep primary packet/consume/handler evidence above short-window summaries. One integration owner binds each package.

**Closure evidence:** Actual revision-bound controls, focused relevant runtime evidence and failure-propagation cases. Regenerate stale receipts only in future authorized work; never relabel historical validation.

**Residual/branch effect:** Correct new reporting does not repair missing historical evidence. Retain narrow primary results that survive the defects. Applies to hardware capture tools as well as the emulator. Current status: known defects; corrective validation pending.

## K08 — Incorrect timing/device contracts invalidate inference

**Basis:** F03/F06/R05; C07/C13. Installed clock ignores domain and uses incorrect nanosecond units; setitimer is success-only; affinity returns ENOSYS; null/regular-file fixtures do not implement real hardware readiness.

**Failure mode/consequence:** Timing-sensitive candidate seems correct under false clocks/readiness, or host delays/RSS are diagnosed as instrument problems. Scoped futex repair is overstated as full Linux fidelity.

**Trigger/replanning:** Claim uses unvalidated guest time/timer/thread semantics, API counts as audio proof, synthetic file readiness as device transport, or an uninstalled correction as live evidence.

**Proposed controls:** At M02/M05 correct and validate only contracts required by the chosen inference, or use actual target/native/isolated evidence. P08/M08 measure real deadlines/output. Keep original defective condition identifiable; investigate causality before attributing delays/faults.

**Closure evidence:** Required units/domains/timer/futex/select ownership/race/error behavior under actual source revision, followed by relevant runtime result; physical timing/audio receipts for hardware claims.

**Residual/branch effect:** Passing a scoped wrapper does not certify Linux generally. Host monotonic ordering remains usable within defective guest conditions. If the emulator is not used for the claim, its defects need not block the physical route. Current status: known scoped defects; broader fidelity unknown.

## K09 — Proprietary initialization or peripheral contracts prevent reuse

**Basis:** G06/G07; F02/F03/F09/R03/R04; X07/X09. Shipped ALSA/X11/BSP and manual roles are present; complete panel/codec/analog/calibration initialization and device ownership are not operationally established.

**Failure mode/consequence:** Companion races the original app; replacement app cannot initialize independent support; new BSP loses proprietary routing, pads/LEDs/touch or analog-filter control. A signal-flow “DSP” label is treated as a separate programmable chip.

**Trigger/replanning:** Driver probe depends on hidden app state, exclusive device sharing fails, protocol is incomplete, required proprietary binary cannot run, or digital processing is substituted for physical analog control.

**Proposed controls:** M05 establishes selected real interface and ownership. BD proves independent retained-Linux initialization; BE/BF prove affected ports/services. Keep panel firmware and known hardware support unless requirements justify replacement.

**Closure evidence:** Actual required interface initialization, legal transactions, output and failure/restart behavior independent of the original app for replacement branches; explicit affected-interface coverage.

**Residual/branch effect:** One panel event/PCM probe is not a full instrument. Reconstruction cost must be compared against feature value and accepted scope; missing support does not automatically favor a new kernel. Current status: open.

## K10 — Instrument-function and project compatibility regressions

**Basis:** G11; F01/F03/R01/R04; Stage 3 D/E/F comparison. Only selected UI interactions and empty-project completion are demonstrated; populated project compatibility, sampling/sequencing/effects/MIDI remain unverified.

**Failure mode/consequence:** New feature works while selected original workflows fail, projects corrupt or migration cannot be reversed. Replacement scope omits mandatory behavior.

**Trigger/replanning:** M01 preserved-function list grows; changed format/schema, thread/state ownership or restart behavior breaks reference tests; replacement requires unexpectedly broad compatibility.

**Proposed controls:** M01 defines preservation/exclusion and formats; M07/M08 run affected regressions; M10 verifies installed restart/data transitions and reversible migration where needed; M11 qualifies all advertised functions/configurations.

**Closure evidence:** Requirement-linked original/candidate results on meaningful populated data and real affected interfaces, with save/reload/restart/migration/rollback checks where required.

**Residual/branch effect:** Untested functions are not implicitly supported. Full original compatibility materially enlarges D/E/F; agreed reduced scope can change their feasibility. Current status: open; no broad regression suite is claimed to exist.

## K11 — Required build/source/ABI correspondence is unavailable

**Basis:** G02/G03; F05/R06; C09. Historical BSP/toolchain exist; public source listing 1.30 versus held 1.50/1.60 has unresolved packaging/lineage. Proprietary application source is unavailable.

**Failure mode/consequence:** Necessary component cannot be rebuilt/ported, artifact differs inexplicably, retained app fails under new libraries/kernel, or a release cannot be reconstructed.

**Trigger/replanning:** Missing patches/generated inputs/proprietary dependencies, shared banner mistaken for correspondence, incompatible ARM ABI, nondeterminism without explanation or a generic BSP build treated as target proof.

**Proposed controls:** P08/M05 component-level lineage/build ledger. Build only components required by the selected route in an isolated future scope. BD/BE/BF validate actual ABI/ports; M11 independently reproduces release or deterministic patch generation.

**Closure evidence:** Relevant clean builds from identified inputs, explained correspondence to the component relied upon, actual runtime ABI behavior and reproducible candidate construction. Exact binary equality is strongest; justified semantic/section differences must be explicit.

**Residual/branch effect:** Runtime binary reuse may leave source correspondence open without blocking A/B/C/D at that scope. E/F incur additional source/port obligations. Current status: open and conditional on what must change.

## K12 — Inadequate real-time/resource headroom or sustained reliability

**Basis:** G12; F03/F06/F13/R04/R05/R11; C10/C15/C16. One 281→441 count pair over 140.072 seconds exists; replication was inconclusive. Emulator RSS growth 533→2,147 MiB is observed, with cause indeterminate and no target counterpart.

**Failure mode/consequence:** Feature misses audio/sync deadlines, underruns under realistic load, exhausts memory/storage or fails after sustained operation. A scheduler rewrite is selected without proving an OS bottleneck.

**Trigger/replanning:** Target deadline violations, growth beyond agreed limits, repeatability/ordering sensitivity, native/worker faults, or benchmark inference relies on null PCM/emulator RSS/core requests.

**Proposed controls:** M05-A records M01 concurrent workload/configuration, measured stock capacity/deadlines, minimal measured candidate costs or justified conservative bounds, consumed/replaced stock work, instrumentation/excluded costs and integration unknowns. Declare reserved margin and reopening thresholds before results. A scoped cost probe may precede full implementation after its method/mechanism prerequisites; target exposure additionally needs execution/H and Q/T only if persistent. No meaningful bound leaves resource-dependent M06 commitment pending. M05-Q at substrate/M07/M08 integration measures actual concurrent target workload and costs; M11 adds justified sustained liveness/load qualification. Reduce algorithm/scope before platform escalation where appropriate.

**Closure evidence:** A distinguishes measured/bounded/unknown costs and conditional admission, never integrated compliance. Q actual target clock/rate/buffer/concurrent load/underrun/resource results meet predeclared limits and close unknowns before M08. Stock idle headroom, isolated algorithm tests or emulator results alone cannot do so. Later M11 evidence supports its larger envelope; faults/incomplete arms remain visible.

**Residual/branch effect:** A bounded demo does not prove indefinite stability or all workloads. OS replacement requires a measured platform reason, not a timing label. No safe concurrent-guest capacity is inferred. Current status: open; growth cause indeterminate.

## K13 — Sunk-cost research, brittle patch accumulation and rewrite scope

**Basis:** F14/R12; Stage 3 marginal-value/sunk-cost assessment. Repeated initialization, overlapping packages and obsolete continuation work are evidenced; precise total waste/staffing savings are not.

**Failure mode/consequence:** Program keeps completing Send/UI/emulator tasks or adds opaque patches without improving delivery feasibility. Alternatively, a rewrite inherits every unknown at once without a measured requirement.

**Trigger/replanning:** Repeat lacks a new discriminating question; multiple packages disagree; “finish emulator then OS” becomes mandatory; local changes require broad private-state reconstruction; platform branch selected by prior investment.

**Proposed controls:** P05/P10/M06 require question, minimum dependency, decisive observation and stop decision. Before sustained work the owner selects an investment tranche with route/questions, resource/effort ceiling and review point; pending investigations cannot renew it. At expiry review stop/narrow/acquire-access/pivot. M12 declares the reuse claim before feature two and tests a materially different relevant dependency/condition, recording new reverse engineering/shared-contract changes. Narrow claims if both features only test one interface. Compare D when patch burden expands; keep one package/acceptance authority.

**Closure evidence:** Owner-selected tranche and documented review/renewal/stop outcome; decision-changing results; selected architecture satisfies requirements; second-feature evidence tests the declared reuse boundary rather than feature count. Resource ceilings are spending constraints, not delivery forecasts or execution authority. No numerical efficiency claim without comparator.

**Residual/branch effect:** Some repetition is needed for controlled comparisons and independent restoration. Treat this as an ongoing governance risk, not a permanently closed technical fact. Current status: open exposure.

## K14 — Evidence authority, archival and path drift

**Basis:** F15/R13/R14; C20–C24. Superseded “current” records, legacy `Code Projects` paths and active archive moves are documented. Prior archive aggregates were indeterminate.

**Failure mode/consequence:** Future engineer selects obsolete next work, follows absent paths or uses a copied summary without primary evidence. A changing tree is incorrectly certified as an atomic snapshot.

**Trigger/replanning:** Primary locator absent/moved, same claim has competing authorities, old source hash/commands silently translated, archive status lacks final dispositions or baseline revision differs.

**Proposed controls:** M02 records one dated selected capability/evidence contract with explicit path mapping and actual identities; reconcile with archive owner. Future proposals point to raw evidence and preserve original command history. This roadmap does not edit old records.

**Closure evidence:** Independently resolvable primary locators, actual package hashes and restoration mapping; a reviewer distinguishes historical/superseded/accepted/excluded/paused scopes.

**Residual/branch effect:** Authority is maintained per revision, not guaranteed forever. Stage 2's corrected performance window governs future comparisons; older records stay intact. Current status: known drift; aggregate archive state not re-audited.

## K15 — Host metadata contaminates target images

**Basis:** B07; F07/R07; C01. Source-authoritative comparison shows 60 tar-directory mode losses and 22 recorded SFS-file differences; device/FIFO entries are metadata-only on the host. Same-host audits can pass despite these losses.

**Failure mode/consequence:** Repacked rootfs lacks sticky/setgid/modes, ownership, required nodes or layering, causing boot/service/security/storage failures unrelated to the intended feature.

**Trigger/replanning:** Candidate derived directly from fixture metadata, unexplained type/mode/owner/link/node discrepancy, host-relative re-extraction used as assembly proof or missing persistent-layer semantics.

**Proposed controls:** P09/M09 assemble in a suitable future isolated environment from original archive metadata and actual layering; compare every consequential difference. Keep encryption equality separate from semantic container fidelity.

**Closure evidence:** Original-versus-assembled paths/types/content/modes/ownership/link groups/required attributes/nodes and layering agree except reviewed intentional changes. Explain nondeterministic container bytes and their acceptance implications.

**Residual/branch effect:** Not every runtime binary-only or volatile route needs rootfs reconstruction. It is mandatory before relying on a rebuilt target image. Correct metadata alone does not prove acceptance or recovery. Current status: known defect in fixture fidelity.

## K16 — Installer write scope exceeds the feature scope

**Basis:** F04/R08; C08; Stage 3 delivery comparison. Update destination/routing and shared-state behavior are unverified; panel payloads being unchanged between releases does not prove the updater skips them.

**Failure mode/consequence:** A small app change also rewrites kernel, environment, shared rootfs, calibration or panel state, invalidating narrow rollback and exposing a much larger failure domain.

**Trigger/replanning:** Complete routing analysis discovers additional writes, actual behavior diverges from the map, normal boot depends on altered shared state or “volatile” program writes persistent data.

**Proposed controls:** P06/M04 classify actual effects; M09-Q qualifies actual unchanged-route acceptance and every destination/recovery envelope, separate from encode equality. Reuse valid existing acceptance receipts rather than reflash stock redundantly. Before every persistent attempt M09-T binds exact candidate/container/installer identities, eligible unit/release, allowlisted content/metadata differences, relevant checks/routing, possible candidate-dependent state effects and qualified backup/restoration/interruption coverage. Prefer a proven smaller route. Final M10 binding does not defer earlier admission.

**Closure evidence:** Applicable unchanged-route acceptance and complete qualified write/restoration scope, plus an exact pre-exposure T receipt for the earliest and every subsequent persistent attempt. Requalify changed structure/route/destination/failure assumptions, reusing unaffected evidence. Candidate hashes alone do not prove applicability; small code changes grant no waiver.

**Residual/branch effect:** Changed route/artifact can reopen scope even when the feature code is identical. If scope cannot be bounded, persistent trials stop; small code diff is no waiver. Current status: open.

## K17 — Input authenticity and intended distribution are not established

**Basis:** G01/G02; F11/R14; C08/C09. Held bytes are internally consistent and locally identified; independent publisher acquisition matching is unverified. Proprietary originals and recovered analysis are distinct from redistributable source. Distribution intent is not selected.

**Failure mode/consequence:** Release uses the wrong reference origin or includes material unsuitable for the intended distribution, preventing a supported release even if a private technical demo works.

**Trigger/replanning:** Official reference does not match held bytes, acquisition/source lineage cannot be explained, intended audience expands, or release packaging depends on redistributing proprietary artifacts without a reviewed basis.

**Proposed controls:** M02/P02 retain acquisition/provenance qualifications and seek independently matched legitimate reference inputs where available. M01 specifies audience; M11 reviews component provenance/licenses and a suitable distribution form, such as user-supplied originals plus reproducible changes when appropriate. Specific legal conclusions are outside this technical review.

**Closure evidence:** Identified reference origin and explained match/discrepancy; release inventory and independently reviewed distribution basis appropriate to the chosen scope.

**Residual/branch effect:** Hash equality identifies bytes, not publisher authorship or distribution rights. Local experiments and public release have different exposure. Current status: origin open; release exposure conditional.

## K18 — Volatile or active trials lack independent intervention and output limits

**Basis:** Stage 5 A03/RC03; F02/R03 and documentary hardware roles. No-write classification and graceful teardown do not demonstrate what can intervene after candidate, device owner, console, kernel or boot path failure. Actual reset and output envelope remain unverified; no hardware damage is asserted.

**Failure mode/consequence:** Candidate hangs or monopolizes a device, produces uncontrolled output or loses observability; its teardown cannot run. Reset/power-cycle affects mounted stock state even though software was loaded into RAM.

**Trigger/replanning:** No intervention independent of the failing component, undefined device handoff or codec/clock/gain/output limits, lost observations or exceeded trial envelope. Unsupported connection or reset effects invalidate readiness.

**Proposed controls:** H before each active code/device/boot/recovery trial: failure domain, evidenced applicable stop/reset/stock-return path and owner; finite bounds and observability/operator-stop conditions; supported electrical/audio/output/gain/clock transactions and appropriate isolated capture connections; stock storage/peripheral effects of reset. Passive capture uses only applicable observation/connection controls. Establish applicability in separately authorized scope without deliberately crashing or altering irreplaceable state.

**Closure evidence:** Protocol and actual intervention/operating-envelope evidence appropriate to what may fail, available before exposure; device ownership/handoff and return-to-stock constraints are explicit. A successful candidate exit or zero persistent writes cannot close H alone.

**Residual/branch effect:** H is distinct from M09-Q/T restoration and remains mandatory for no-write/RAM-boot trials. A broader privilege/device/failure scope requires rechecking H. Current status: open; planning requirement added, actual evidence pending.

## Risk interactions and review order

1. K01 determines which K06/K09/K10/K11/K12 obligations actually apply. Clarify it before committing to deep implementation.
2. K02 and K14 protect the basis for every later conclusion. Handle indispensable preservation without duplicating an existing archive operation.
3. K03/K04 control on-unit execution feasibility; K18 independently gates active intervention/output scope, including no-write routes. Emulator repairs cannot substitute for these.
4. K05/K15/K16 form the persistent join: qualified Q scope plus exact T before exposure. Encryption equality, recovery entry or a generic procedure does not admit a candidate.
5. K07 and K08 govern the validity of K06/K12 evidence. Synthetic controls or a false clock can create a misleading positive result.
6. K09 and K11 dominate replacement branches; K10 expands with preserved functions. A new OS adds these obligations rather than removing them.
7. K12 and K10 may permit M08's bounded demo while blocking M11's broader support. Label the surviving claim precisely.
8. K13 remains active: review the owner-selected effort tranche, information value of each repeat and claim-specific second-feature reuse. Pending work cannot renew its own ceiling.
9. K17 affects source confidence and production distribution scope. No publisher authentication or rights conclusion is invented from internal CRC success.

The independent reviewer should challenge closure evidence and residual scope at each milestone, especially access/execution and persistent recovery. This register does not close risks, assign work or approve mitigations. The proposal stops for review.
