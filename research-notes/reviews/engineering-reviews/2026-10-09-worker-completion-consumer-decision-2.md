<!-- source: engineering-reviews/2026-10-09-worker-completion-consumer-decision-2.md | scrubbed -->

# Worker completion cycle: readiness remains the next decision

October 9, 2026 — America/Chicago. Follow-up review of the same completed cycle; no experiment launched. The guest allowance is consumed, and nothing is underway.

The cycle answered whether the corrected observer survives asynchronous submission and captures original worker completion/state. At **56.360s**, worker 2007 enters byte-validated **`0x25dfc4`**, writes result **1** at owner **+0x130** and completion flag **1** at **+0x12d**, then returns through matching listener/resume frames. These raw receipts close the earlier observation gap. They establish original execution provenance, without demonstrating further application progress beyond persistent HOME. [Latest handoff] `../experiments/worker-resume-completion-20261009/HANDOFF.md` (evidence not published), [raw stdout] `../experiments/worker-resume-completion-20261009/run-1/supervision/guest.stdout.txt` (evidence not published).

Native **600.225s bounded_stop/exit 0**, owned reaping and independent postflight pass. Exact **800×480 HOME** remains pixel-identical from **285.265–595.055s**, matching the prior frontier; resources remain **1,314**. Ten matched natural events support continued service. Completed startup, successful readiness and input response remain unproved; no input was sent. No controlled performance improvement was measured. [Native/pixel verification] `../experiments/worker-resume-completion-20261009/result-verification.json` (evidence not published).

Both resume-file predicates return zero, selecting the no-file result. **File absence is not an established startup failure or UI blocker.** Whether the application accepts this outcome remains unresolved; require original readiness semantics, without making saved-project restoration an additional objective. Consumer execution is unobserved. No new emulator/worker fault occurred; denied vfork remains a guard. The control payload assertion and erroneous closeout credential-deletion assertion are retained; neither invalidates original receipts or drawing. Earlier missing finals stay missing. The late cleanup TERM was `absent_at_send`, consistent with native completion. [State/static assessment] `../experiments/worker-resume-completion-20261009/completion-state-assessment.json` (evidence not published), [failure/closure links] `../experiments/worker-resume-completion-20261009/HANDOFF.md` (evidence not published).

Retain the lifetime correction, fixed seed and execution condition. Reject flag-only startup proof and speculative fixture repair. Worker-listener discovery leaves the critical path. The result agrees with current README and supersedes its historical missing-provenance checkpoint; README needs no update.

**One next experiment:** does the original consumer accept the no-file completion and establish readiness?

- Add sparse byte/frame-validated observations at **`0x25f044`**, its branch/countdown and **`0x25f108 → 0x25f13c`**, matching the producer owner and downstream state/visibility return.
- If original completion/readiness semantics and stable owned pixels pass, trace one conditional tagged Track 2 interaction through packet/gate, consumption, handler/state and pixels. Otherwise withhold input and isolate the first missing or failure transition.
- After **new explicit guest authorization**, retain **600s / fresh 20-minute session**, independent **605/608/610s** TERM/KILL/reap, guards, ownership checks and postflight. Stop for fault, byte/frame mismatch, guard breach, unrecoverable supervision or bound; static pixels alone do not justify early stopping.

**Efficiency:** combine consumer observation and conditional input in one initialization; keep minimal worker receipts and reuse unchanged validation. Control only changed consumer-hook contracts. Hook overhead remains suspected, not measured.
