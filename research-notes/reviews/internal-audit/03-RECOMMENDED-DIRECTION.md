<!-- source: ../PioneerSP16Review/03-RECOMMENDED-DIRECTION.md | scrubbed -->

# Stage 3 — Recommended direction

Review date: October 9, 2026, America/Chicago. This record recommends architectural decisions and bounded feasibility experiments for future authorization. It is not an implementation roadmap. No engineering artifact, emulator, build, hardware state or other chat is changed by these recommendations.

## Preferred strategy and confidence

Reorient the project around **a selected instrument feature and a demonstrably usable, recoverable execution route**. Keep the original boot/platform/panel stack as the default hypothesis, investigate the smallest functional userspace change, and preserve application replacement on retained Linux as the principal alternative.

Confidence is high that this is a better decision process than continuing unbounded emulator/UI completion. Confidence is moderate that retaining existing hardware support will reduce new interface work. Confidence is low in any particular deployable modification or replacement design because executable access, recovery, real peripheral behavior, audio and the target feature remain unestablished.

The architectural objective is not “finish the emulator, then build the OS.” It is to establish where desired behavior belongs, whether it can execute on the instrument, and which existing components are worth retaining. Existing research tools may support those questions without becoming product dependencies.

Read the [architecture assessment] `Review/03-ARCHITECTURE-ASSESSMENT.md` (evidence not published) for evidence/constraint analysis and [strategic options] `Review/03-STRATEGIC-OPTIONS.md` (evidence not published) for the full comparison. F/R references identify the [Stage 2 audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published) and [validation requirements] `Review/02-VALIDATION-REQUIREMENTS.md` (evidence not published).

## Decisions justified now

- Retain the verified decoding, original bytes, localized maps and attributed HOME/Track/Mixer evidence as reusable research assets. Preserve the original containers as assembly authority.
- Treat userspace emulation as a selective analysis tool. Require each further investment to identify an unresolved decision, necessary contracts, discriminating observation and stopping condition.
- Favor retaining shipped hardware support while exploring localized changes. Separate replacing an application from replacing its platform and from replacing panel firmware.
- Give hardware execution/access, acceptance boundaries and recovery higher strategic priority than additional adjacent UI demonstrations.
- Evaluate application replacement if required features exceed credible local patch boundaries. Do not insist on retaining the proprietary application because it already runs in the harness.
- Keep physical audio/timing validation distinct from synthetic transfers and UI pixels. Keep local code reversibility distinct from update/recovery reversibility.

## Decisions the evidence does not yet support

No final selection among a companion process, original-app patch, replacement application or replacement OS is justified. No extension API, fully usable BSP, enabled/disabled secure boot, safe bank rollback, working alternative boot path or deployable repacker has been demonstrated. No reliable cost, date, probability or percentage complete can be assigned.

The desired first feature, required original feature set, project-file compatibility and distribution target also remain product decisions. For example, a new MIDI policy and a new effect engine can occupy different software layers; these examples are not selected requirements. The existing Send investigation is a possible mechanism probe, not a mandate to make Send the first deliverable.

## Investigation disposition

This table ranks information value; it is not a scheduled sequence or assignment of work.

| Disposition | Investigation | Reason and boundary |
|---|---|---|
| Accelerate | Feature/compatibility acceptance definition | Without it, architecture complexity and emulator relevance cannot be judged (R01). |
| Accelerate | Available unit, observation/access and execution-route assessment | Affects every on-device option; begin with existing/manual/static evidence before proposing physical actions (R03/R08). |
| Accelerate | Complete relevant updater/authentication/write-range and recovery analysis | Decoding success is far ahead of safe deployment knowledge (F04). Scope it to the candidate delivery route. |
| Accelerate | Selected peripheral/audio substrate and applied-state path | Distinguishes local modification from application replacement; observe meaningful output rather than more null calls. |
| Accelerate where required | Correct timing contracts and truthful result/source binding | Needed for new timing-sensitive or mutation evidence, not to retroactively erase accepted historical runs (R05/R09/R10). |
| Accelerate preservation only | Verify indispensable off-device evidence/environment recovery | Avoid losing high-value assets during architectural change; reconcile existing archive ownership rather than start overlapping storage work (R14). |
| Continue selectively | Byte-backed static analysis and one bounded loaded-state experiment | Useful where it resolves the selected feature/acceptance/interface question. |
| Postpone | Broad effects reconstruction, populated project compatibility, all-control mapping | Activate only to meet selected behavior/compatibility requirements. A replacement preserving all functions may eventually need them. |
| Postpone | Full matching BSP/toolchain reconstruction | Investigate lineage now; require builds only for components the candidate design changes or depends on rebuilding (R06). |
| Postpone | Kernel modernization, RTOS port, panel rewrite, whole-machine emulation | No present requirement demonstrates sufficient benefit to accept their expanded dependency burden. |
| Discontinue as milestones | Repeated unchanged HOME/Mixer/roster proof and old Send preparation reuse | Already answered narrow questions or stale source bindings; restore/replay and new-state tests have different legitimate purposes. |
| Replace | Open-ended emulator completeness/throughput pursuit | Use question-specific contracts, native/physical observations or isolated tests when they resolve the same decision more directly. |
| Replace | Competing packages and repeated handoff integration | Use one accepted evidence contract and one integration owner for each consequential experiment. |

## Smallest decisive experiments

These are proposed experiments, not executable prompts, launch allowances or a roadmap. A negative result can be decisive for one route without proving all routes impossible. Static evidence may narrow a choice; final physical feasibility cannot be certified without the relevant unit observations. Existing artifacts should answer a question before generating new runtime evidence.

### X01 — Locate one feature at a software boundary

**Question:** Does the desired behavior belong to declarative data, an external/control boundary, a local app path, or a broad replacement subsystem?

**Minimum investigation:** Obtain one chosen before/after behavior, preserved functions and output/persistence acceptance criteria. Trace only its input, state ownership, application/processing and storage dependencies using existing shipped bytes/maps. Avoid a whole-application class census.

**Discriminator:** An identified data/control/local path with bounded dependencies favors options A/B/C. Extensive missing state/engine behavior makes D worth comparing. A proven kernel/driver limitation makes E relevant. An incomplete trace remains unknown; it does not automatically favor rewriting. This is the smallest product-and-static exercise that makes an architecture choice meaningful (R01/R09).

### X02 — Characterize actual access and stock boot

**Question:** Is a unit available, and what observation/execution surfaces actually exist?

**Minimum investigation:** First collect an existing unit/access inventory and retained stock boot records. If absent, propose one separately authorized observation session: inspect the documented connector/test-point route and electrical requirements, capture stock boot without persistent changes, and read only the accessible environment/mount/device identity information. Do not infer a usable JTAG/UART/network route from `fw_env.txt`.

**Discriminator:** A verified console or stock Linux access channel makes subsequent volatile tests concrete. No access leaves on-device conclusions conditional and raises the value of service-interface investigation. A console banner alone does not prove command execution, recovery or authentication policy. No unit access should trigger a limit on deployability claims, not endless emulator expansion (R03).

### X03 — Determine the acceptance boundary that affects the chosen change

**Question:** What actually prevents or permits changed code at the selected layer?

**Minimum investigation:** Trace complete validation and destination routing for that layer in shipped updater/boot artifacts, with supplied sources used only after correspondence checks. Identify container, version/target, component integrity/authentication and runtime checks separately. Use actual unit read-only policy/status evidence where required and available; do not program fuses or alter environment. If static checks establish a supported route, propose one harmless temporary program that reports its identity and exits through that route, under separate authorization.

**Discriminator:** Observed execution of that program establishes a bounded executable foothold, not deployment or peripheral support. An authenticated restriction rejects that route/layer unless a legitimate accepted mechanism exists. A signed bootloader alone leaves later userspace policy unresolved. Missing evidence remains unknown. A CRC-only parser result closes neither complete acceptance nor boot (R08).

### X04 — Prove packaging reversibility offline

**Question:** Can original image structure be reproduced faithfully, and can a selected change be localized?

**Minimum investigation:** In a future authorized isolated workspace, re-encode the held ISO unchanged and compare to its original UPD; separately rebuild only the container needed by the candidate change from original metadata and compare entries. Verify contents/types/modes/ownership/links/required nodes and layering. Keep encryption round trip distinct from rebuilding an ISO/rootfs.

**Discriminator:** Exact unchanged encryption equality validates that transform. A semantically faithful container validates only that assembly scope; nondeterministic differences need explicit explanation. Unexplained metadata or routing differences block repack-based deployment. Neither result proves updater acceptance. Do not generate a candidate from the current macOS tree's metadata (R07/R08).

### X05 — Establish recovery independently of normal startup

**Question:** Can the proposed write scope be restored if the new software cannot boot?

**Minimum investigation:** Map exactly what the chosen install changes and what recovery itself requires. Verify a unit-specific backup and its storage/ECC/OOB/calibration interpretation. Under separate hardware authorization, demonstrate entry into the proposed independent recovery route and recovery of a narrowly scoped test state on an appropriate recoverable test target. Require the route to function without the changed application/kernel when those can fail.

**Discriminator:** Observed restoration covers only the tested failure/write scope. A nonpersistent recovery-entry check proves entry only; it cannot certify NAND restoration or power-loss rollback. If the smallest restoration test would jeopardize irreplaceable state, the decision remains blocked for persistent deployment and favors volatile exploration. Do not deliberately brick a unit to compensate for an undefined procedure (R08).

### X06 — Test one legal parameter application

**Question:** Can original input reach applied state through a usable modification boundary?

**Minimum investigation:** Reuse accepted identity/static evidence. After correcting the necessary package binding and observation contracts, propose one bounded legal input with baseline→request→owner-thread/deferred application→state→output correlation. Send/encoder 3 is eligible only if the complete transport and gates are established; do not invent a record or substitute a direct RAM write and call it physical input.

**Discriminator:** A correct applied-state transition establishes that path, not a new feature, physical panel compatibility or audio correctness. A UI-only change does not prove DSP application. Failure locates a missing transport/gate/owner contract rather than proving patching infeasible. Stop expanding Send work if it does not resolve the chosen feature's architecture (R09/R10).

### X07 — Establish meaningful original audio and one reusable peripheral contract

**Question:** Is audio processing observable, and can retained Linux support a replacement application?

**Minimum investigation:** Capture stock audio for one known sample or deterministic stimulus with format/rate/channels/routing recorded. Separately identify the selected driver's initialization/ABI and observe one real panel event/control transaction. If a safe executable route exists, propose a temporary bounded audio or panel probe on retained Linux, with the original app relinquishing any exclusive device ownership and without changing calibration/panel firmware.

**Discriminator:** Stock audio establishes a reference. Captured non-null emulator buffers may establish selected digital behavior, but not physical timing. A successful real probe demonstrates the tested substrate and favors D; app-specific hidden initialization or exclusive proprietary dependencies increases D's burden. One input record does not establish LEDs/touch/full panel control or the analog-filter protocol (R03/R04).

### X08 — Demonstrate one bounded changed behavior

**Question:** Does a plausible local modification actually deliver the selected feature?

**Minimum investigation:** Once X01 supplies a bounded candidate and a suitable validated execution environment exists, compare one reversible changed userspace copy against its original reference using the feature's observable output and a small relevant regression set. Use input-driven applied state, not an observer writing the answer. Maintain exact version/ABI/thread/persistence assumptions.

**Discriminator:** A passing local functional change strengthens C/A/B at that scope. Failure due to wide opaque invariants strengthens the case to examine D, but one failed hook does not prove C impossible. Emulated success remains a software proof until actual hardware acceptance and behavior are observed (R01/R04/R09).

### X09 — Bound platform reuse or replacement cost

**Question:** Are the drivers/components needed by D/E available and compatible enough to reuse?

**Minimum investigation:** Compare release binary interfaces/configuration with supplied source for one indispensable component, such as the selected panel or audio driver. Identify missing proprietary code and generated inputs. Build that component in a future isolated authorized environment only if rebuilding it matters; a complete LTIB rebuild is not the minimum experiment.

**Discriminator:** Proven runtime reuse favors D even if exact source rebuilding remains open. Source/interface correspondence supports a scoped port investigation for E but not whole-board compatibility. Missing implementation narrows what must be retained or reverse engineered. Shared banners/filenames do not settle correspondence (R06).

### X10 — Measure resource and timing feasibility on the actual target

**Question:** Is there sufficient CPU/memory/I/O headroom for the selected new behavior?

**Minimum investigation:** Measure one representative stock hardware workload and a bounded candidate workload through a verified execution route. Record effective clocks, sample/buffer deadlines, underruns and memory attributable to relevant processes. Correct required clock/timer contracts before using an emulator for any timing-sensitive supporting claim.

**Discriminator:** Meeting defined deadlines supports the candidate architecture at that load; exceeding them prompts algorithm/interface changes before an OS rewrite. Compare alternative OS scheduling only if a measured OS bottleneck is implicated. Emulator RSS and 64-frame null calls cannot answer this question (R04/R05/R11).

The experiments are dependency constrained: feature validation needs X01; physical probes need access and a supported execution route; persistent writes need suitable recovery; audio timing claims need meaningful audio and correct clocks. They need not be run in numerical order or all be run. Select only those that discriminate a live architectural decision, with the four validity/milestone/observation/cleanup outcomes preserved under R10.

## Parallel engineering opportunities without duplicated work

No subagents are launched by this review. Future parallel work is useful when outputs are independent evidence contracts with an explicit integration boundary.

| Potential workstream | Independent output | Required dependency / integration rule |
|---|---|---|
| Feature boundary analysis | Input/state/output/persistence map for one selected behavior, with original-byte locators | Needs the chosen specification; cannot declare hardware acceptance. |
| Update and boot acceptance analysis | Check coverage, destinations, write scope and unknown policy list | Separate offline analysis from unit measurements; one owner consolidates the complete acceptance claim. |
| Driver/source lineage analysis | One component's source/binary/ABI correspondence and missing dependencies | Does not need new UI runs; must identify the required component from the candidate scope. |
| Stock hardware characterization | Unit boot/audio/panel/state receipts | One hardware-session owner manages the unit, device ownership and recovery conditions. |
| Harness contract/reproducibility assessment | Version-bound conditions and necessary contract fixes/restore evidence | Reuse accepted milestones; no competing packages or simultaneous runtime integration. |

Static feature, acceptance and driver analyses can proceed independently against immutable identified inputs. Hardware observations feed all three. Mutation testing consumes their accepted contracts and should have one package/integration owner. Parallel studies should use separate exports/working copies and merge evidence into a single authoritative record; they should not edit one live Ghidra database, share mutable guest state, race updates or run multiple speculative guests against the same resources.

Do not treat the sampled RSS as proof that parallel guests fit. Combine adjacent compatible observations in one bounded authorized session when it reduces repeated startup without compromising attribution. Keep independent replication and controlled comparisons separate when their evidence requires it. Recovery, broad input compatibility and audio acceptance cannot be partitioned into success claims that hide missing shared dependencies.

## Conditions that would change the recommendation

If a suitable configuration or external control boundary is demonstrated, prefer it to a binary patch. If local patches require broad reconstruction of private state/engine/persistence, and retained hardware interfaces are usable, favor application replacement. If a verified platform requirement cannot be met by retained Linux, reassess modern Linux/BSP replacement. Consider a different OS only after its requirements and measured value justify recreating board support.

If no viable execution route or acceptable recovery can be established, report on-device feasibility as unresolved or blocked for that route and constrain research accordingly. If the required peripherals cannot be reused, compare the cost of their reconstruction against the actual feature value before committing to D/E/F. These outcomes may invalidate the preferred hypothesis; the current architecture has no entitlement to survive them.

Architectural recommendations stop here. No implementation roadmap, engineering prompt dispatch, corrective work, runtime experiment or hardware action follows from this assessment.
