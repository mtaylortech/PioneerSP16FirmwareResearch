<!-- source: engineering-reviews/2026-10-08-runtime-limit-persistence.md | scrubbed -->

# Runtime-limit persistence review — October 8, 2026

The recurring 180-second limit comes from an old planning default being carried into new instructions, generated prompts and copied launchers. It is not a demonstrated emulator or firmware ceiling. A separate hard-coded watchdog limit also prevents the new 600-second plan from receiving its full window.

This review launched no firmware, display, watchdog or helper process and changed no runtime code. The current user requested an explanation. Only this review, its index entry and the focused arithmetic evidence were saved, following the current AGENTS.md review-retention instruction.

## Evidence and causal chain

1. The historical [parent-initialization draft] `<experiments/offline-review-20261008-01/PARENT_INITIALIZATION_DRAFT.md:9>` (evidence not published) proposes 180 seconds as a scope/budget choice; it does not derive that value from a technical constraint. The later [experiment-loop prompt] `<docs/NEXT_SESSION_PROMPT-20261008-EXPERIMENT-LOOP.txt:141>` (evidence not published) embeds it in a thirty-minute, up-to-six-attempt session.
2. Current [AGENTS.md] `<AGENTS.md:11>` (evidence not published) still says: “Reuse the existing 180-second observation default unless the current user scope authorizes another bound.” The exception permits longer runs, but the persisted default continues to steer newly generated plans.
3. Longer requests were recorded and used. The [font-cache A4 scope update] `<experiments/full-font-cache-20261008-1614-a4/session-clock.json:11>` (evidence not published) explicitly records a user request for five-minute tests. The later [throughput recovery configuration] `<experiments/startup-throughput-20261008-recovery/session-clock.json:4>` (evidence not published) uses 295 seconds with independent 300/303/305 deadlines. [README.md] `../README.md` (evidence not published) retains actual five-minute run results.
4. The [CSV retry preparation] `<experiments/csv-pointer-20261008-retry/prepare.py:23>` (evidence not published) explicitly replaces `--seconds 295` with `--seconds 180`, replaces launch-window allowances, and installs 185/188/190 deadlines. Its [authorization record] `<experiments/csv-pointer-20261008-retry/session-clock.json:6>` (evidence not published) says the user selected “Run the next bounded local test (180-second default).” This is a concrete reversion, rather than a runtime unable to execute longer.
5. The latest completed comparison inherits [hard-coded `--seconds 180`] `<experiments/post-font-counted-quantum-20261008-repeat/common/run_once.py:10>` (evidence not published), [185/188/190 watchdog deadlines] `<experiments/post-font-counted-quantum-20261008-repeat/common/run_once.py:89>` (evidence not published), and [fixed enclosing session allowances] `<experiments/post-font-counted-quantum-20261008-repeat/execute_arm.py:11>` (evidence not published). Changing the probe duration alone would leave the earlier watchdog cutoff intact.
6. The [post-font engineering review] `<engineering-reviews/2026-10-08-post-font-counted-quantum.md:88>` (evidence not published) proposes 180 seconds again for subsequent experiments. Inspection of chat “Measure post-font main-thread quanta” shows those values in the generated four-experiment prompt. After the user challenged the three-minute limit, the assistant explicitly acknowledged carrying the established budget forward and generated a revised 300/600-second plan. The recent executed comparison prompts themselves explicitly specify 180 seconds; those runs followed their immediate instructions. The failure is the recurring short default in the planning/prompt chain, not evidence that every launcher ignored a direct longer bound.

## Additional defect in the active longer-run preparation

The new [launcher generator] `<experiments/revised-startup-20261008/prepare_arm.py:15>` (evidence not published) accepts 300/600 seconds and derives +5/+8/+10 shutdown offsets. Its [execution wrapper] `<experiments/revised-startup-20261008/execute_arm.py:12>` (evidence not published) increases the enclosing session allowance. However, [preparation copies the old watchdog unchanged] `<experiments/revised-startup-20261008/prepare_arm.py:32>` (evidence not published).

That [watchdog's guest-spawn path] `<experiments/post-font-counted-quantum-20261008-repeat/treatment/supervision/watchdog.py:317>` (evidence not published) always calls `tighten()` with `started + 300/303/305`. [tighten()] `<experiments/post-font-counted-quantum-20261008-repeat/treatment/supervision/watchdog.py:287>` (evidence not published) takes the minimum of existing and supplied deadlines. Therefore an armed 605/608/610 configuration is silently shortened to approximately 300/303/305 at guest spawn. A requested 300-second observation with 305/308/310 grace is also shortened to 300/303/305, risking termination before native finalization.

The [focused arithmetic control] `../experiments/runtime-limit-review-20261008/deadline-arithmetic.stdout.json` (evidence not published) executes only the exact AST-extracted `tighten()` method, with time relative to guest spawn. Results:

| Observation requested | Armed TERM/KILL/reap | After guest-spawn clamp |
| --- | --- | --- |
| 180 seconds | 185/188/190 | 185/188/190 |
| 300 seconds | 305/308/310 | 300/303/305 |
| 600 seconds | 605/608/610 | 300/303/305 |

The [new launcher controls] `<experiments/revised-startup-20261008/launcher_controls.py:7>` (evidence not published) inspect the arguments sent to `set_deadlines()` but do not exercise the watchdog's subsequent spawn-time tightening. Their passing result therefore does not validate the effective ten-minute deadline.

## Confidence, limits and next action

High confidence in the on-disk limit propagation and deadline arithmetic. Chat history supports the recent prompt-generation chain. This review does not reconstruct every earlier longer-run request, prove an internal model motivation, or claim the active longer-run guest actually reached this cutoff. Another chat was preparing the longer plan during inspection, so this is a checkpoint of its files, not a completed-runtime verdict.

For future work, use the user's selected observation duration as one configuration value and derive probe, launch gates, session allowance and watchdog deadlines from it. Replace the fixed spawn-time 300/303/305 clamp only in a fresh working supervisor; retain finite session containment, ownership checks and cleanup. Before a longer guest, use an inert owned-child control to verify effective deadlines after actual spawn for both 300 and 600 seconds, rather than checking only outgoing arguments. Do not launch extra original-app guests outside the active plan's attempt budget. Preserve completed evidence and update the current default/next-plan text so the obsolete three-minute proposal is not regenerated.
