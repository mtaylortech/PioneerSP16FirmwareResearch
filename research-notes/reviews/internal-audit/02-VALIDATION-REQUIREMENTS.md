<!-- source: ../PioneerSP16Review/02-VALIDATION-REQUIREMENTS.md | scrubbed -->

# Stage 2 — Validation requirements

To: Project Director. Review date: October 9, 2026, America/Chicago.

These are evidence requirements and instructions for future review of authorized work. They are not an implementation plan, launch allowance, hardware/flashing permission or request to another chat. No requirement below was executed as corrective engineering in Stage 2. The [audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published) provides finding/source IDs; the [contradiction register] `Review/02-CONTRADICTION-REGISTER.md` (evidence not published) identifies conflicting propositions.

## Decision rules

Retain exact local decoding/content and limited original-application/UI milestones as established research progress. Withhold broader claims until the evidence matches their scope. There is no single “all tests pass” gate: front-end reproduction, real instrument behavior, source/build correspondence and deployment require different demonstrations.

Requirements are ranked by impact, not scheduled here. R01 selects the relevant objective and dependencies. R02/R09/R10 govern stronger emulator/feature claims. R03–R08 govern board, audio, build and deployment claims when selected. R13/R14 protect reviewability and recovery. An audio deadline claim must not precede valid timing; a deployment claim must not precede source-authoritative image assembly and recovery evidence.

## R01 — Define the actual product/feature objective

**High. Current classification: unverified. Resolves F01 and the scope of F02–F09. Sources: E01/E02.**

Before reporting implementation feasibility or completion, name the selected feature(s), exact observable behavior, intended execution target and compatibility constraints. State whether the deliverable is an original-app research harness, a modified original firmware feature, a Linux platform change or a replacement system. Identify which existing functionality must remain operational.

Required evidence: a bounded acceptance specification with input, expected state/output, persistence and regression expectations. Include audio/timing/peripheral expectations where relevant, not only screenshots. Choose the feature implementation boundary and identify dependencies that have actual evidence versus hypotheses.

Acceptance: a reviewer can distinguish a passing product result from a harness preparation milestone and assess the next validation against a specific objective. Do not assign percent complete or treat preliminary historic effort estimates as validated forecasts. Defining this requirement does not imply that every future feature must rebuild the whole OS.

## R02 — Reproduce the accepted front-end milestone from a recoverable package

**High for reproducibility; medium for further UI claims. Current: saved milestone verified; independent replay unverified. Resolves F10/F11; C17/C18. Sources: E03/E14–E17.**

A future authorized reproducer should be able to obtain the original 1.60 app and shipped libraries, fixed seed rootfs, actual runtime dependencies and all material overlays from a named package revision. State clock, loader/TLS, audio/device, statfs/ioctl, select, named futex, scheduler, X11 and containment conditions explicitly.

Required observations: original initializer entry/return and enclosing success with byte/thread/object/SP/saved-LR correlation; subsequent original dispatch; selected fresh producer/main acceptance; current returned original drawable ownership/geometry/attributes; attributable HOME output. For an input milestone, join exact tagged transport, original consumption, callback/return, state and owned pixels within one run. Keep application/observer faults and effective observation duration visible.

Acceptance: an independent replay reproduces the narrow milestone under the documented conditions, with raw evidence and a result that does not conflate host termination with natural guest exit. Related retained runs count as corroboration, not independent clean-environment replay. State repeatability failures rather than replacing missing/failed arms. A 600-second observation proves neither continuous liveness nor long-term stability.

## R03 — Establish board boot and relevant peripheral readiness separately

**High. Current: unverified beyond documentary/static architecture. Resolves F02/F04; C06. Sources: E03/E04.**

A board/OS claim requires the real shipped kernel or selected replacement kernel to execute in the claimed target, with identified bootloader, initramfs, boot arguments and actual storage/mount assembly. Verify correspondence of the release initramfs before treating the supplied source initramfs as the same object.

Required evidence: actual unit/target identity; boot console/trace; intended init/launcher completion; relevant driver initialization; writable/persistent mounts; audio clock/codec state; panel MCU communication and calibration dependencies; applicable analog-filter control; error/absence behavior. Record NAND geometry, bad-block/OOB handling and unit-specific environment/data when deployment requires them. Do not infer these from chip strings, a software memory map, requested affinity or `fw_env.txt` defaults.

Acceptance: the selected instrument readiness conditions are explicitly observed. Timeout-and-continue through the bounded startup loop must remain distinct from positive hardware readiness. Unselected peripherals can remain unknown if the claim clearly excludes them. Stage 2 grants no hardware access or boot attempt.

## R04 — Validate meaningful audio, DSP and instrument behavior

**High. Current: unverified. Resolves F03/F09; C07. Sources: E03/E04/E05/E12.**

Null PCM is suitable for a startup fixture, but cannot supply instrument validation. First identify a meaningful stimulus/output capture path and sample representation; distinguish original algorithm execution from sink/discard and generated-zero behavior.

Required evidence: deterministic input (for example an impulse or tone), exact sample rate/channel/format/buffer configuration, captured output and objective expected measurements. For the selected feature, bind legal parameter requests to applied state and the processing buffer path. Measure timing/underruns/glitches where the specification requires them. Document fidelity limits of an emulator-only observation.

Acceptance: original or modified selected behavior agrees with defined expected output, including relevant edge values and regression behavior. Test playback, sampling/recording, sequencing, MIDI/sync and save/reload only as required by R01, while keeping untested functions explicit. Rendering a fader or recording 64-frame API returns is insufficient. Do not claim a particular effect algorithm, JUCE DSP implementation, separate DSP firmware or plugin interface from names/imports/manual analogies alone.

## R05 — Establish the OS contracts needed for timing-sensitive claims

**High. Current: known defects verified; broader fidelity unverified. Resolves F03/F06/F13; C07/C13/C15/C16. Sources: E03/E08/E19.**

Required contract evidence should follow the actually exercised code paths and selected objective. At minimum, timing claims must account for correct timespec/timeval units, distinct supported clock domains, relevant timer/signaling behavior, error returns, thread save/restore and timeout/wake completion. Keep corrected and defective baseline conditions identifiable; a saved opt-in correction is not an installed/live-validated fix.

For selected futex/select paths, distinguish timeout, genuine wake/readiness, value mismatch, invalid arguments, thread/owner identity and cancellation. Cover wake/timeout races and the surrounding pthread wrapper's use of clock values when relevant. A scoped named wrapper correction must not be labeled full Linux futex fidelity.

The inspected statfs fixture supplies fixed synthetic filesystem fields for calls and `fstatfs` does not validate the descriptor before supplying them. Its corrected ARM32 layout is therefore not evidence of real filesystem capacity/type/error semantics. Regular empty/zero device files likewise do not implement hardware readiness, stream consumption, ioctl or FIFO behavior. Document these deliberate fixtures and verify any contract newly required by the selected feature.

Acceptance: focused evidence demonstrates the required contract under the actual runtime revision, followed by a relevant guest result when claiming live fidelity. Synthetic controls alone establish overlay behavior. Determine effects of corrections experimentally before attributing delay/crash/growth to them. Host elapsed-time ordering remains usable even while guest clocks are defective. Relevant primary interface definitions: [Linux clocks](https://man7.org/linux/man-pages/man2/clock_gettime.2.html), [FUTEX_WAIT](https://man7.org/linux/man-pages/man2/FUTEX_WAIT.2const.html).

## R06 — Resolve source lineage and the components that must be built

**High for OS/platform work. Current: unverified release correspondence/build. Resolves F02/F05; C09. Sources: E04/E07.**

Required evidence: source bundle origin/version/hash, packaging relationship (`pioneerdj_tsp`/`pioneerdj_tsp_rzx`), relevant patches/configuration, generated inputs, exact toolchain/sysroot, proprietary dependencies and external build tools. Separate public GPL/BSP content from proprietary app availability.

Acceptance: a clean build of the required component(s) succeeds from recorded inputs. Compare to shipped binaries using an explained correspondence method; bit equality is strongest, but explain nondeterministic metadata and compare relevant sections/configuration if exact equality is unattainable. A kernel banner, matching major version or successful unrelated BSP build does not close release equivalence. Unmatched/missing source components remain explicit constraints. If R01 permits binary modification without rebuilding a component, state that choice and its validation burden rather than claiming source recovery.

## R07 — Use original container metadata for image assembly and repacking

**High before any boot tree/repack claim. Current: byte content verified within Stage 2 coverage; host metadata fidelity contradicted. Resolves F07/F04; C01. Sources: E06/E09.**

Required evidence: compare candidate assembly against original source entries for paths, types, contents, symlink targets, hardlink groups, permissions including sticky/setgid/setuid where applicable, ownership, required timestamps/xattrs and device major/minor/FIFO definitions. Establish actual rootfs layering/mount order and how persistent/unit-specific data enters the system.

Acceptance: every consequential difference is intentional, explained and appropriate to the target Linux environment. In particular, resolve the 60 tar-directory/22 recorded SFS-file mode discrepancies, keeping macOS symlink-mode semantics separate. Metadata-only special nodes must be represented correctly where required by target execution. Preserve original archives as authority; a same-host re-extraction or successful byte checksum is insufficient. Do not blindly reproduce host filesystem metadata into a firmware image.

## R08 — Demonstrate packaging, complete acceptance and recovery at the selected scope

**High before deployment. Current: unverified. Resolves F04/F07/F11; C08. Sources: E04/E06.**

Required evidence: complete updater/container/routing acceptance map, unchanged-image encode/repack round trip, manifest/metadata agreement and identification of all checks actually reached. Explicitly distinguish ciphertext CRC, encryption consistency, version/target checks and any other discovered checks; do not invent a cryptographic signature requirement or assume no additional checks exist.

For deployment, require a unit-specific backup and restoration procedure covering relevant NAND/eMMC/environment/calibration and panel payload dependencies. Demonstrate bank selection, interruption/failure behavior and recovery by observations appropriate to the available hardware/test target. A/B names and `update_status=success` defaults are not a demonstrated rollback mechanism.

Acceptance: the selected update is accepted by the actual complete path and boots/operates under R01 acceptance, with demonstrated recoverability. Any hardware/flashing work needs its own future authorization and constraints. Nothing in this audit authorizes testing a candidate update on a physical unit.

## R09 — Close the legal input → application → state → output chain

**High for Send or comparable feature claims. Current: static route provisionally supported; live mutation unverified. Resolves F08/F09; C03–C05/C19. Sources: E10–E13.**

Required evidence: actual loaded identifier/name/vtable operands kept distinct; owning controller/view/footer/widget/unit/parameter; live recipient registration and thread identity; relevant eligibility/service/clamp values; legal input delivery; original getter baseline, setter request, applied-state/deferred completion and attributable output. Cover boundary and rejection behavior chosen under R01.

For panel-derived claims, establish the real descriptor/open/read/wakeup contract, complete 128-byte record and original conversion/callback registration. Distinguish raw +0x14 notification from conditioned +0x10 editing, and direct owner-thread handling from worker-to-owner delivery. Do not replace missing transport with invented packets or direct parameter writes and call that original input behavior. Excluded async partial work remains outside this evidence set.

Controls must include unequal identifier/name values and other-widget/reentrant/shared-return cases derived independently of the observer's assumed layout. Failure receipts must record actual versus expected operands and frame stage without fabricating missing historical values. Local roster coverage must not be extended to Desktop/global listeners without evidence.

Acceptance: one legally delivered interaction traverses the claimed original path, changes the correct parameter/applied state and yields the defined rendered/audio consequence. A one-count numeric change can occur without a visibly changed quantized fill; use appropriate state and numeric/fill/image ROIs rather than requiring every pixel class to move. Two value-zero snapshots or static byte agreement do not meet this requirement.

## R10 — Bind execution and report outcomes without false success

**High for consequential test validity. Current: mixed; explicit defects verified. Resolves F08/F11/F12; C02/C04/C05/C11–C14/C18/C22/C24. Sources: E10–E12/E17/E18/E20.**

Required evidence per consequential run: one frozen package revision; actual command/configuration; runtime and material overlay/dependency identities; seed/input identities; loaded original app/library and new hook-byte checks; raw stdout/stderr; effective supervision; observation/fault/end status; owned cleanup/postflight. Avoid requiring a full historical tree audit for each narrow experiment.

Acceptance reporting must expose four distinct facts: whether observations are valid, whether the selected milestone occurred, whether the requested observation completed, and whether cleanup completed. Return/process codes must agree with required-check validity or be explicitly described as transport/tool exits. Worker/observer/native faults and missing finals remain visible even when cleanup passes or some earlier boundaries were valid.

Test aggregate reporting against required-check failure, missing native final, early watchdog stop, expected contained operations, wrong owner/frame and delayed input response. Separate actual sending/server acceptance, guest consumption, handler/state and rendered response. Reconcile the successful inspection's supervision/helper discrepancy from retained primary events; do not discard the input because an aggregate field is wrong. Preserve historical code/results rather than altering them to match new expectations.

The corrected Send package's stale receipt must be regenerated against the accepted source revision in a future authorized work session before asserting launch readiness. Existing saved validation cannot be relabeled as validation of different source. Do not infer whole-library/environment immutability from 29 hook points or repeated app-only identities.

## R11 — Validate performance and reliability with a defined comparison

**Medium; high when used for audio deadlines or resource feasibility. Current: single-pair resource gain verified; general improvement unverified; growth cause indeterminate. Resolves F06/F13; C10/C15/C16. Sources: E16/E19.**

First use the correct retained metric: **281→441 matched returns over 140.072 seconds after font completion**, within approximately 180-second observations. Correct subsequent references to Stage 1's 245-second error without modifying original evidence. State event time origin (probe start, process creation, post-font, handler return) explicitly; these are not interchangeable.

For new performance claims, match seed, code, runtime, supervision, observation, host conditions and instrumentation; change the selected condition only. Predefine progress/time/resource metrics and retain completed control/treatment repetitions, including reversed order where justified. Do not replace a native-crashed arm with an invented result or attribute a crash to a condition not yet active. Do not promote percentage increase in an intermediate counter to equivalent startup speedup.

For memory/reliability, collect workload-specific time-series data beyond initialization and attribute retained memory to guest, emulator/JIT/cache, Python observers and host allocations where needed. Record faults and stability duration, define liveness beyond unchanged pixels, and distinguish RSS from guest usable RAM, unique physical footprint and peak. State what a long run actually validates.

Acceptance: completed matched comparisons support the claimed metric and its repeatability; actual audio timing additionally meets R04/R05. Existing samples do not justify a leak diagnosis or safe parallel-guest capacity.

## R12 — Make repeated research answer a new discriminating question

**Medium. Current: concrete integration/repetition inefficiency verified; total waste/speedup unverified. Resolves F14. Sources: E10/E11/E20.**

Before a repeat, name the unresolved question, minimum required dependencies, expected discriminating observation and how the answer changes the next decision. Reuse unchanged controls/runtime and accepted evidence where the claim permits; obtain new live evidence only where current owner/state/execution or a changed condition requires it.

Acceptance: an accepted static correction reaches the next frozen test package, with one owner of that package. Adjacent observations can share a future authorized initialization when compatible with that scope and its bounds; separate runs remain justified for controlled comparisons, altered conditions or independent replay. Reused exports/copied summaries are not new independent results.

Measure progress by newly closed uncertainty or acceptance boundary. If reporting efficiency, distinguish active work, elapsed turn time, waiting, copying/archiving, preparation and execution. Do not treat all review/cleanup as waste or claim net staffing speedup without a valid comparator. This is a future review criterion, not permission to coordinate or invoke other agents.

## R13 — Establish dated record authority and prevent rediscovery from stale status

**Medium. Current: authority/path drift verified. Resolves F13–F15; C10/C17/C20–C24. Sources: E01/E02/E13/E17/E20.**

Required evidence: one current capability boundary with dates, exact scope, accepted primary locators, material substitutions, retained failures and one selected unanswered question. Older “canonical/current/next test” records need an unmistakable historical/superseded designation in future current guidance; do not rewrite their underlying observations.

Acceptance: a new engineer can distinguish completed front-end work from unstarted product/deployment work, identify consumed/paused/excluded scopes, resolve `Code Projects` versus `Code_Projects`, and locate raw rather than only summarized evidence. Record source lineage and actual metric/time origin. Keep one concise decision/handoff per useful result and avoid duplicating every conclusion into multiple competing authorities.

Stage 1's timing error can be resolved by a dated correction referencing the existing primary comparison; a new guest would supply no needed evidence for that correction. This audit records the correction but changes no Stage 1 or main-project document.

## R14 — Authenticate inputs and demonstrate complete evidence/environment recovery

**High for preservation; medium for source-origin confidence. Current: local identities verified; official origin/complete restoration unverified; aggregate archive state indeterminate. Resolves F11/F15; C08/C22/C23. Sources: E06/E17/E21.**

Required evidence: original acquisition receipts or independently obtained official matching files, provenance dates/URLs and retained archive/firmware hashes. An internally coherent UPD can be decoded without independently authenticating its publisher origin. Source/package lineage must remain separate from current script availability.

List everything needed outside Git: original updates, key dependency without exposing it, extracted inputs, original rootfs/libs, Python framework/native libraries, Qiling/Unicorn/gevent versions and modifications, host display tools/relocation/signing support, databases if needed, raw captures/logs and actual source revisions. Distinguish real dependencies from optional/unexercised tools, including the fail-explicitly Keystone fallback. Record how legacy paths and external host dependencies resolve.

Acceptance: a recoverable snapshot with raw evidence and needed execution dependencies is restored and checked against content/type/link/required-metadata identities in a separate authorized location. A meaningful off-device backup is independently accessible. Explain unresolved xattr/setxattr differences by significance and preserve failed restore receipts; do not equate metadata failure with byte loss or assume same-disk archives/Git alone satisfy recovery. Current archive totals require a final batch-by-batch disposition, not a mid-operation census.

## Claims the Director can accept now

| Claim | Stage 2 disposition |
|---|---|
| Both held updates decode exactly to retained ISOs | Verified by fresh complete in-memory transform. Publisher authenticity remains separate. |
| Retained outer ISO regular contents and primary tar contents/targets agree | Verified within specified readback coverage. Full fresh SFS/nested/source-metadata audit not performed. |
| Host extracted trees preserve all Linux metadata | Contradicted. |
| Original 1.60 app reaches mapped initialization/dispatch and selected completion, with retained HOME/Track/Mixer behavior | Verified saved evidence under material emulator substitutions. Independent live replay remains unverified. |
| Corrected Send identity/listener inspection succeeds | Verified for two snapshots; both parameter values remain zero. |
| Static encoder/footer trace is byte-backed | Verified bytes; conditional semantics provisionally supported; live delivery/application unverified. |
| Real audio, board OS boot, new feature, matching build, deployable repack or recovery is demonstrated | Unverified in examined records. |
| The quantum condition provides a repeatable general speed/reliability improvement | Unverified; single-pair metric survives with corrected 140.072-second window. |
| Complete research evidence can be restored from Git or existing archives alone | Unverified; archive aggregate state indeterminate. |

Stage 2 is complete. These requirements are returned to the Project Director for subsequent scope and evidence decisions. No corrective work or further coordination follows from this delivery.
