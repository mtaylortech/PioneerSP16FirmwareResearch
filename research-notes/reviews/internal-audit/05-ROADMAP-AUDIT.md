<!-- source: ../PioneerSP16Review/05-ROADMAP-AUDIT.md | scrubbed -->

# Stage 5 — Adversarial roadmap audit

Review date: October 9, 2026, America/Chicago. Advisory verdict: **APPROVE WITH CONDITIONS**.

The proposed strategy is defensible: choose a useful feature, establish an actual execution route, retain hardware support where justified, and earn physical functionality before production claims. The proposal is not yet sufficiently precise for adoption as an executable milestone contract. This review identifies **six Major findings and two Minor findings; no Critical finding is established**. The Major findings require correction before their affected gates begin. Only the human project owner may authorize adoption or subsequent work.

This assessment applies the perspectives of a principal firmware engineer, embedded-systems architect, reverse-engineering specialist and technical program auditor. These are analytical perspectives used by one reviewer, not four independent witnesses. No subagents were launched. The review changed neither the roadmap nor historical evidence and initiated no implementation, firmware execution, test suite, build, hardware operation or prompt dispatch.

Companion documents: [required corrections] `Review/05-REQUIRED-CORRECTIONS.md` (evidence not published) and [approval recommendation] `Review/05-APPROVAL-RECOMMENDATION.md` (evidence not published).

## Evidence and review boundary

The submission comprises the [master roadmap] `Review/04-MASTER-ROADMAP.md` (evidence not published), [dependency map] `Review/04-DEPENDENCY-MAP.md` (evidence not published), [prioritized actions] `Review/04-PRIORITIZED-NEXT-ACTIONS.md` (evidence not published) and [risk register] `Review/04-RISK-REGISTER.md` (evidence not published). The authoritative dependency table takes precedence over its diagram; that precedence matters to A01.

The review compared the submission with Stage 1's [baseline] `Review/01-TECHNICAL-BASELINE.md` (evidence not published), [inventory] `Review/01-PROJECT-INVENTORY.md` (evidence not published) and [gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published); Stage 2's [audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published), [contradictions] `Review/02-CONTRADICTION-REGISTER.md` (evidence not published) and [requirements] `Review/02-VALIDATION-REQUIREMENTS.md` (evidence not published); and Stage 3's [assessment] `Review/03-ARCHITECTURE-ASSESSMENT.md` (evidence not published), [options] `Review/03-STRATEGIC-OPTIONS.md` (evidence not published) and [direction] `Review/03-RECOMMENDED-DIRECTION.md` (evidence not published).

Selected original engineering evidence was reread: the [historical deployment gates] `experiments/offline-review-20261008-01/ARCHITECTURE_DEPLOYMENT_GATES.md` (evidence not published), [architecture/effects review] `engineering-reviews/2026-10-09-firmware-architecture-effects-knowledge.md` (evidence not published), [Send inspection handoff] `experiments/send-identity-live-20261009-200701/HANDOFF.md` (evidence not published), [panel preparation] `experiments/panel-delivery-preparation-20261009/HANDOFF.md` (evidence not published), [application loader] `experiments/startup-lifecycle-live-20261009-165946/run-1/probe.py:557` (evidence not published), [null PCM configuration] `experiments/startup-lifecycle-live-20261009-165946/run-1/alsa-null.conf:611` (evidence not published), [installed clock implementation] `experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py:28` (evidence not published), [boot environment] `decode/output/image2/iso/images/fw_env.txt` (evidence not published) and [service-manual device/state description] `decode/tmp/consolidation/service-page-49.txt:12` (evidence not published). Earlier independent reviews were consulted with their dated limits retained.

This is an audit of the proposal against the reviewed baseline, not a new certification of every changing project/archive file. Stage 2's verified extraction/UI results are accepted within their scope; decryption, captures and live guests were not replayed. The inspected loader still loads an application directly, the PCM configuration routes hardware PCM to null, and the clock source still uses the defective fractional scale. Those source observations support the roadmap's qualifications; they establish no causal diagnosis or physical performance result. Historical black-screen and no-Git statements are not treated as current facts.

The reviewed Stage 4 byte identities are:

| Document | SHA-256 |
|---|---|
| 04-MASTER-ROADMAP.md | `9a1fe10af92a4983c11ad37dc3e5ba9bc9e6c657f5e6f4ea4b0d39b66d9e487e` |
| 04-DEPENDENCY-MAP.md | `87aa3dde0069952631e8021499de3ccc86dd585a0163a5015a3c0631437a0f65` |
| 04-PRIORITIZED-NEXT-ACTIONS.md | `b0f0b9750bc687df2e8db1c107fe5a5d5c6429363bdf8ce3afb1bc29f691085e` |
| 04-RISK-REGISTER.md | `5c29bcc4901d2b438eb591b4b22e531933cc4a4929b21a485da84d6d99580f41` |

Hashes identify the submission; they do not authenticate publisher origin or historical execution.

## Finding register

| ID | Rank | Material weakness | Affected scope |
|---|---|---|---|
| A01 | Major | M02 completion and M03 capture readiness are inconsistently joined | M02/M03; hardware-first scheduling |
| A02 | Major | Candidate resource admission and candidate qualification are insufficiently separated | M05/M06; resource-sensitive branches |
| A03 | Major | Volatile classification does not supply crash intervention or an output-safety contract | Active M04/M05, BD/BE/BF, M07/M08 hardware trials |
| A04 | Major | Persistent route qualification is not explicitly bound to each first changed artifact before exposure | M09 and every persistent trial; M10 |
| A05 | Major | Production qualification unconditionally requires a persistent pilot | M10/M11 for a deliberately non-installed product |
| A06 | Major | A stand-alone foothold and stock state trace can bypass proof of the selected application-modification mechanism | Option C and any B interposition path |
| A07 | Minor | A second distinct feature need not meaningfully challenge the claimed reusable architecture | M12 |
| A08 | Minor | Question-based stopping rules lack a program-level feasibility spending limit | P01–P10; repeated pending investigations |

The findings concern missing or ambiguous contracts. They are not allegations that unstarted milestones have already failed. Known open risks explicitly represented in Stage 4 are not counted again merely because they are open.

## A01 — Major: split measurement readiness from reference reproduction

**Evidence.** M02 acceptance includes independent reproduction of a relevant reference, permitting a stock capture/probe method for a hardware-first route. Its dependency paragraph then requires M02 for new consequential runtime conclusions in M03–M08. M03 requires the M02 observation contract and produces the actual stock reference. Meanwhile, the authoritative dependency table requires only the M02 capture contract for M03. Compare [M02/M03 contracts] `Review/04-MASTER-ROADMAP.md:79` (evidence not published) with the [table] `Review/04-DEPENDENCY-MAP.md:58` (evidence not published). P02 also combines restoration and reference reproduction in its exit evidence. [P02] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:48` (evidence not published).

**Consequence.** A coordinator treating M02 as one completed predecessor can wait for a hardware reference that M03 is supposed to acquire, or restore/replay an irrelevant emulator to get past the gate. The table supplies a valid partial-contract interpretation, so this is **not an unavoidable dependency cycle**. The inconsistency nevertheless makes the capability sequence unreliable and can add nonessential restoration work to the physical critical path.

**Correction.** Define explicit M02 acceptance subsets: indispensable preservation; method/capture readiness; and independent reference reproduction. Permit a bounded M03 reference acquisition after the applicable first two subsets pass; let M03's evidence supply the reference for the third. Require full applicable reproduction before conclusions that depend on it. Align the master, table, diagram and P02/P04/P07 with that interpretation. Do not waive preservation of indispensable assets or truthful capture.

**Closure.** A hardware-first dependency walk reaches the first stock capture without prior hardware-reference reproduction or emulator restoration, then shows exactly where independent reproduction becomes mandatory. The emulator route retains its own replay requirement.

## A02 — Major: do not certify candidate feasibility from stock headroom

**Evidence.** M05 must deliver a measured workload budget and accept target resource/deadline support for the selected workload before M06 architecture selection. M07's feature implementation and the replacement substrates follow M06. Offline prototypes may start early, but the proposal does not clearly define which pre-M06 on-target candidate cost probe is allowed, how representative it must be, or which resource claim remains provisional. [M05/M06] `Review/04-MASTER-ROADMAP.md:118` (evidence not published), [M07] `Review/04-MASTER-ROADMAP.md:183` (evidence not published). K12 asks for both stock and bounded candidate budgets, without resolving that distinction. [K12] `Review/04-RISK-REGISTER.md:196` (evidence not published). Stage 3 X10 likewise calls for a stock workload and bounded candidate workload; Stage 2 F03/F13 establishes that null PCM, requested affinity and emulator RSS supply neither. [X10] `Review/03-RECOMMENDED-DIRECTION.md:126` (evidence not published), [F03] `Review/02-INDEPENDENT-AUDIT.md:47` (evidence not published).

**Consequence.** M05 can be delayed until substantial candidate/port work exists, undermining its feasibility purpose. Alternatively, stock idle CPU or an isolated algorithm benchmark may be accepted as proof that the integrated candidate fits. Thread contention, buffer copies, interrupt/driver costs and storage activity may consume the apparent margin. A provisional estimate can then appear to be a passed feasibility gate.

**Correction.** Separate measured stock capacity, bounded candidate cost evidence and integrated candidate qualification. Before M06, require only the evidence needed to admit the selected architecture: a predeclared relevant workload, a measured or explicitly conservative candidate cost bound, named integration uncertainties and reserved margin tied to M01. Allow separately scoped minimal cost probes where necessary; do not require a complete feature or port. Mark M06 admission conditional on the remaining integration costs. M07/M08 and the selected substrate must close those costs using the actual integrated workload before hardware capability claims pass.

**Closure.** The M05 ledger states what was measured, what was bounded, instrumentation effects, remaining unknowns and the failure threshold that reopens M06. It cannot label stock measurements alone as candidate deadline compliance. No invented universal margin or benchmark is required.

## A03 — Major: volatile trials still need independent intervention and bounded outputs

**Evidence.** M04 and M08 exempt verified wholly volatile routes from M09; Route V defines the exception through persistent exposure. Teardown and return to stock are required outcomes, but no explicit prelaunch contract establishes what can stop a hung candidate or constrain unsafe physical output. BE/BF can exercise changed privileged software through a volatile boot. [M04] `Review/04-MASTER-ROADMAP.md:105` (evidence not published), [M08] `Review/04-MASTER-ROADMAP.md:196` (evidence not published), [Route V] `Review/04-DEPENDENCY-MAP.md:82` (evidence not published), [BE/BF] `Review/04-MASTER-ROADMAP.md:157` (evidence not published). P03 covers electrical characterization of access connections, and K09 covers ownership, but neither supplies active-test output limits. The service-manual evidence identifies main-processor audio/control roles, several converters and panel-mediated gain/power functions; actual control/reset behavior remains unproved. [P03] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:62` (evidence not published), [device roles] `decode/tmp/consolidation/service-page-49.txt:31` (evidence not published).

**Consequence.** A temporary process or RAM-booted kernel could hang, monopolize devices or generate uncontrolled output without writing firmware. A successful graceful exit of an identity program does not establish intervention after loss of the application, console or kernel. This is a plausible failure exposure, **not evidence of actual hardware damage or an unusable reset mechanism**.

**Correction.** Add a scope-specific active-hardware readiness condition independent of persistent recovery: demonstrated external stop/reset or return-to-stock mechanism appropriate to the component that may fail; finite observation and operator stop conditions; controlled device handoff; and output/clock/gain limits for affected hardware. For audio probes, start with a bounded captured signal and an appropriate isolated test connection before exposing listening equipment. Explain any power-cycle effects on already mounted stock storage. Apply only the controls relevant to the trial; passive observation does not require full NAND restoration.

**Closure.** Before active exposure, a reviewer can identify the intervention path that survives candidate failure, the permitted physical operating envelope and the evidence supporting both. A graceful candidate exit or absence of persistent writes cannot close this condition by itself.

## A04 — Major: bind recovery and assembly qualification before the first persistent candidate

**Evidence.** M09 correctly precedes every persistent trial and requires scoped restoration. However, it says the feature-specific final installation artifact binds at M10. P09 similarly places the final changed artifact's actual installation/operation at M10. M04/M07/M08 may already make persistent changes. [M09] `Review/04-MASTER-ROADMAP.md:209` (evidence not published), [P09] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:144` (evidence not published), [M10] `Review/04-MASTER-ROADMAP.md:222` (evidence not published). Per-run R10 identities are required, and K16 acknowledges changed-artifact risk, but the gate lacks an explicit candidate-to-qualified-write/recovery-scope join before each earlier persistent exposure. [K16] `Review/04-RISK-REGISTER.md:252` (evidence not published). The original engineering gate also calls for unchanged-package acceptance before a modified package. [original deployment gates] `experiments/offline-review-20261008-01/ARCHITECTURE_DEPLOYMENT_GATES.md:12` (evidence not published).

**Consequence.** A team may qualify an unchanged encoder/container and a generic recovery procedure, then apply a different early installer/candidate believing M09 is closed. That candidate may have different component routing, metadata or persistent side effects. Even if its hashes are recorded, its recovery coverage has not thereby been proved. Deferring actual unchanged-route acceptance also makes a first modified-update rejection ambiguous between packaging and modification failure.

**Correction.** Keep final pilot binding at M10, but require a per-trial binding before **every** persistent attempt: exact candidate and installer identities, intended content/metadata differences, destination/write map, unit eligibility, candidate-dependent persistent effects and a matching accepted recovery envelope. First establish the unchanged installation route's actual acceptance on a suitable independently recoverable target, or cite equivalent existing acceptance evidence; keep this distinct from ISO encryption equality. Where that cannot be done safely, retain the route as pending. Reuse unchanged qualification rather than reflashing or retesting everything for every code edit; requalify only changed acceptance/write/failure assumptions.

**Closure.** The earliest persistent M04 or M07 has a candidate-specific pre-exposure receipt. M09 coverage cannot be borrowed from another unit, installer or narrower write scope without an explicit applicability argument. M10 still earns integrated pilot functionality and lifecycle qualification.

## A05 — Major: a non-installed release should not require persistent installation

**Evidence.** M01 selects persistence requirements, M04 permits volatile delivery, and M08 can demonstrate a feature without a distributable updater. Nevertheless M10 is a persistent engineering pilot and M11 unconditionally depends on M10; the authoritative table and diagram repeat that edge. [M01] `Review/04-MASTER-ROADMAP.md:66` (evidence not published), [M10/M11] `Review/04-MASTER-ROADMAP.md:222` (evidence not published), [dependency table] `Review/04-DEPENDENCY-MAP.md:73` (evidence not published). Stage 3 explicitly treats legitimate temporary Linux/alternate launch mechanisms as candidate delivery options. [deployment mechanisms] `Review/03-STRATEGIC-OPTIONS.md:51` (evidence not published).

**Consequence.** A deliberately temporary, manually launched product can never reach supported-release status under the current graph without unnecessary persistent writes and their recovery burden. The plan quietly adds a product requirement that M01 was supposed to decide. If persistence is selected, the current M10 path remains appropriate.

**Correction.** Make delivery qualification branch on M01: a persistent pilot uses the current M09/M10 obligations; a genuinely non-installed product qualifies repeatable launch, fresh stock restart and relaunch, affected-state preservation, failure intervention, eligibility and advertised behavior through an equivalent nonpersistent gate. Both feed M11. Persistently storing a launcher or configuration is still persistence and must be classified honestly. Do not waive reliability, artifact reproduction or compatibility because the product is temporary.

**Closure.** The dependency walk can reach M11 for an expressly selected non-installed product while meeting all applicable support tests, without claiming automatic startup, installed firmware or untested persistence. If M01 requires persistence, record this correction as inapplicable to that selected route.

## A06 — Major: prove the actual modification mechanism, not merely Linux execution

**Evidence.** M04 may pass with an identity-reporting stand-alone program; M05 may pass with a legal stock state/output transaction. M06 then sends A/B/C toward M07, while only D/E/F have explicit additional substrate gates. [M04] `Review/04-MASTER-ROADMAP.md:105` (evidence not published), [M05/M06] `Review/04-MASTER-ROADMAP.md:118` (evidence not published), [branch prerequisites] `Review/04-DEPENDENCY-MAP.md:67` (evidence not published). M06 permits named gates for indispensable interfaces, which is a useful safeguard, but does not mandate evidence of the selected C insertion/change mechanism or B interposition mechanism. Stage 3 explicitly says executable access does not establish safe new-code loading or an extension API. [option C] `Review/03-STRATEGIC-OPTIONS.md:30` (evidence not published), [B/C comparison] `Review/03-STRATEGIC-OPTIONS.md:41` (evidence not published). The successful engineering inspection records unchanged original bytes and no setter or Send mutation; it is not integration evidence. [inspection limits] `experiments/send-identity-live-20261009-200701/HANDOFF.md:19` (evidence not published).

**Consequence.** Two real successes—launching a utility and observing a stock setter—can leave the crucial interface between them unproved. A feature may require code space, relocation, ABI/thread-safe entry, runtime acceptance or symbol interception that is unavailable. Substantial feature work could start before discovering that its proposed attachment mechanism fails.

**Correction.** Require an explicit mechanism discriminator before substantial M07 implementation for the selected route. For an in-place patch, establish the exact version, valid instruction/data change, accepted loading and affected path. If new code is needed, prove the actual loading/insertion/return mechanism and relevant ARM execution mode, ABI, relocation, memory/cache and thread ownership contracts. For interposition, demonstrate interception of the needed boundary and coexistence rather than relying on dynamic linkage. Use the smallest reversible, separately scoped working-copy probe; a no-op mechanism test earns infrastructure evidence only. A independent companion that requires no app integration need not perform an irrelevant hook test.

**Closure.** M06 identifies whether the mechanism is proved or assigns a mandatory bounded gate before feature implementation expands. The mechanism receipt is distinct from M07's meaningful new behavior and M08's physical feature. This does not require a general plugin framework or whole-application reconstruction.

## A07 — Minor: choose the second feature to test reuse rather than merely count features

**Evidence.** M12 requires a second distinct function, reproducible use of established contracts and evidenced maintenance targets, but does not specify how the second feature discriminates stable reuse from another nearby special case. [M12] `Review/04-MASTER-ROADMAP.md:248` (evidence not published). K13 treats repeated extension as evidence of maintained interfaces, while the architecture assessment warns against accumulating opaque patches. [K13] `Review/04-RISK-REGISTER.md:210` (evidence not published), [sunk-cost assessment] `Review/03-ARCHITECTURE-ASSESSMENT.md:95` (evidence not published).

**Consequence.** Two useful but adjacent changes can meet a feature count while revealing little about the claimed broader capability envelope. This does not invalidate either feature; it weakens the inference about reusable architecture.

**Correction and closure.** Before M12, state which reuse/maintenance claim the second feature tests. Choose a feature that exercises a materially different dependency or version/state condition within the advertised envelope, or narrow the envelope to the interfaces actually tested. Record newly required reverse engineering, adapters and shared-interface changes. Do not manufacture a whole-platform extension requirement.

## A08 — Minor: add bounded feasibility investment without inventing a schedule

**Evidence.** The roadmap rightly declines unsupported estimates, describing near-term bounds as questions, artifacts and stop decisions. P06 allows a small set of credible routes, but no program-level time/attempt/resource limit decides how long successive unresolved routes may be pursued. [planning basis] `Review/04-MASTER-ROADMAP.md:42` (evidence not published), [P06] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:104` (evidence not published), [effort boundary] `Review/04-PRIORITIZED-NEXT-ACTIONS.md:210` (evidence not published). Stage 2 F14 establishes real repeated-initialization/integration inefficiency, while declining a numerical waste estimate. [F14] `Review/02-INDEPENDENT-AUDIT.md:117` (evidence not published).

**Consequence.** Every individual trial can be bounded while the overall feasibility program stays pending indefinitely. Architecture reconsideration or obtaining physical access may be delayed by a succession of locally reasonable investigations.

**Correction and closure.** Have the owner choose a feasibility investment tranche before sustained work: allowed questions/routes, resource or effort ceiling, review point and stop/pivot outcome. These are spending constraints, not predicted completion dates. Reuse each accepted result; renew the tranche only for a stated decision-changing uncertainty. No numerical ceiling is invented by this audit.

## Coverage of the twelve requested challenges

| Challenge | Assessment |
|---|---|
| 1. Assumption-based milestones | A02/A06 identify places where weaker evidence can masquerade as feasibility; open unit/build/recovery risks are otherwise explicit. |
| 2. Missing dependencies | A01/A03/A04/A06 require explicit capture, intervention, candidate and mechanism joins. |
| 3. Firmware/hardware realism | Userspace emulation is correctly scoped; A03/A06 cover remaining volatile/integration assumptions. |
| 4. Verification/acceptance | A02/A04/A06 tighten claim-specific oracles and evidence applicability. |
| 5. Work without objective value | Broad Send/UI/effects/emulator/BSP work is correctly deferred; A01/A05 prevent new unnecessary prerequisites. |
| 6. Premature implementation | M01–M06 generally prevent it; A02/A06 clarify minimal probes before substantial commitment. |
| 7. Recovery/regression/safety | Persistent recovery and affected regressions are present; A03/A04 identify remaining pre-exposure gaps. |
| 8. Duplication/sequencing | One package owner and shared compatible observations are sensible; A01/A05/A08 reduce residual repetition and forced work. |
| 9. Critical-path shortening | Split M02; perform only necessary mechanism/cost probes; keep a nonpersistent qualification branch; see below. |
| 10. Architecture justification | Retained-platform preference is provisional and D/E/F triggers are justified; A06 requires the missing mechanism discriminator. |
| 11. Known uncertainties/audit findings | Most F/R/K issues are carried forward accurately, including metadata loss, stale Send binding, clock defects and 140.072-second correction. |
| 12. Superficial milestone success | Explicit software/physical/production separation is strong; A02/A04/A06/A07 close remaining narrower-success loopholes. |

## Critical path, architecture and approval implications

There is no measured basis for declaring a unique fastest architecture or a duration-weighted critical path. The strongest route remains **feature definition plus usable unit/access and execution evidence**, joined with the affected input/output and resource contracts. The critical-path improvements recommended here preserve those dependencies:

- Allow first stock observation after capture readiness and indispensable preservation, then use it to complete independent reference reproduction.
- Use static acceptance/write analysis and existing maps before a new guest; choose only the minimal mechanism and cost probes that change the architecture decision.
- Share compatible stock observations in one controlled session and combine M07/M08 evidence when all criteria are met. Keep independent reproduction and changed-condition comparisons separate where needed.
- Insert M09 before the earliest persistent exposure and bind each candidate to its qualified scope. Do not complete a repacker for a route that does not use one.
- Qualify an intentionally non-installed product without forcing persistence. Reassess implementation size only after the selected mechanism, affected interfaces and remaining uncertainty are identified.

The proposal correctly avoids assuming proprietary source, a plugin API, JUCE effects, a separate DSP, complete panel protocol, source-release equivalence or automatic A/B rollback. It neither schedules a kernel rewrite as the inevitable endpoint nor mistakes original Send editing for new functionality. These safeguards should remain.

The ultimate product boundary is still a human decision. A functional userspace modification may satisfy selected requirements; it cannot be reported as a replacement kernel/OS. If the owner requires a complete replacement system, BE/BF and the agreed instrument-function suite remain mandatory. No present evidence proves any branch deployable, and the existing feature/unit/access unknowns do not become closed through conditional approval.

**Final verdict: APPROVE WITH CONDITIONS.** The strategy merits conditional endorsement; its operational contracts need A01–A06 corrected or explicitly resolved as inapplicable before the corresponding work begins. A07/A08 improve later planning without blocking approval. This verdict authorizes nothing. Only the human project owner may adopt the roadmap. Review ends with the three Stage 5 documents.
