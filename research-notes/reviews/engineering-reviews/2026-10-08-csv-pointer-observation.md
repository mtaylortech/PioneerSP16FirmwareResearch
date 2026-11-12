<!-- source: engineering-reviews/2026-10-08-csv-pointer-observation.md | scrubbed -->

# CSV pointer observation and next experiments

Review date: October 8, 2026, America/Chicago. Archived from the engineering review delivered in this chat. Reviewed experiments: `csv-pointer-20261008` and `csv-pointer-20261008-retry`.

This cycle produced a useful diagnostic, but **did not explain the earlier fault or advance the completed-startup/usable-UI milestone**. The corrected observation worked; the causal experiment remained inconclusive.

The review examined retained code, raw events, native finals, cleanup records and pixel captures. Pointer relationships were recomputed from recorded registers and captured pixels were decoded. These are checks of existing evidence, **not independent runtime replications**. No new experiment was executed for the review.

**The original objective and expectations**

The immediate question was whether the CSV conversion received an already misaligned allocation at `0x62c530`, or whether its pointer changed before publication at `0x62c55c`. The broader goal remained completed original application startup and usable display output.

Before execution, the intended discriminator was clear:

- Misaligned allocation return: investigate allocation and preceding execution.
- Aligned allocation followed by a different publication pointer: investigate the intervening conversion.
- Aligned values throughout a fault-free run: historical fault provenance remains unresolved.

There was no documented reason to expect the fault to recur in this particular run. Nor was a recurrence rate or number of healthy repetitions defined as evidence of reliability. The experiment therefore had a clear observation objective, but a causal conclusion depended on reproducing the failure.

**What actually happened**

| Experiment | Hypothesis / expected result | Observed result | Assessment |
| --- | --- | --- | --- |
| `csv-pointer-20261008` | The CSV-open gate would activate boundary capture. | The real mapper returned `ql_syscall_open`; the filter expected `open`. Zero boundary observations. Watchdog stop at approximately 62 seconds; native final missing. | **Failed instrumentation.** Cleanup succeeded, but this attempt did not answer the question. |
| Native boundary controls | Capture supplied aligned and misaligned values without changing original boundary instructions. | Both recorded controls passed. They executed the original `MOV` and `STR`; the control supplied the allocation register and manually constructed `r6`. | **Passed limited controls.** They did not exercise the allocator or complete conversion routine. |
| `csv-pointer-20261008-retry`, first parse | Observe allocation/publication alignment during the implicated pre-font CSV parse. | 370 allocation returns, 374 publication visits, 67 `100%` publications; all aligned and consistent with allocation plus eight. No fault. | **Observation passed; causal result inconclusive.** |
| Retry, six later CSV parses | Capture remained available when the CSV reopened. | Another 2,220 allocation/publication pairs were aligned. | **Additional observations**, under post-font counted scheduling; not six independent reproductions of the failing condition. |
| Retry, remaining startup | Continue through the existing bound and observe original progress/output. | Font scan returned at 35.571 seconds; 307 matched resource returns; latest resource access `LS_L_660.csv`. Native bounded stop. Three black captures. | **Bounded observation completed. Startup/UI milestone unachieved.** |

Evidence: [failed-attempt stdout] `../experiments/csv-pointer-20261008/supervision/guest.stdout.txt` (evidence not published), [failed-attempt supervision] `../experiments/csv-pointer-20261008/attempt-supervision.json` (evidence not published), [control implementation] `../experiments/csv-pointer-20261008-retry/controls.py` (evidence not published), [retry raw stdout] `../experiments/csv-pointer-20261008-retry/supervision/guest.stdout.txt` (evidence not published), [native final] `../experiments/csv-pointer-20261008-retry/csv-pointer-20261008-retry-result.json` (evidence not published).

**What we learned, with confidence limits**

| Finding | Confidence | Practical implication |
| --- | --- | --- |
| All 2,590 recorded allocation returns and 2,594 publication visits were four-byte aligned. | **Verified within this recorded execution.** | The earlier misalignment was absent at these observed boundaries. |
| Every publication could be associated with a recorded allocation having the same thread, source, destination and stack context; `r6 = allocation + 8`. | **Strongly Supported.** Arithmetic was recomputed from raw registers. | No observed alignment change occurred between these two boundaries. |
| Four publication boundaries were revisited on resumed timed slices, with unchanged pointer and prior destination contents. | **Verified observation.** | Boundary visits cannot be counted as completed stores. |
| These four visits demonstrate a completed store being replayed. | **Unsupported.** | The destination still contained its preceding value; the evidence does not establish completed-store replay. |
| Observer cost changed the interleaving enough to suppress the historical fault. | **Tentative.** | This is plausible, but there was no matched observer-on/off comparison. |
| The historical bad pointer originated in allocation rather than a later copy. | **Unresolved.** | Neither explanation was selected by this run. |
| Captured display output remained black. | **Verified for the three captures.** | No usable original UI was established. |

The publication hook runs **before** `STR r6,[r5]`. It records an intended pointer and the preceding destination value; it does not independently verify the completed store or subsequent copying. The observer also reinstalls its hooks on every later `LS_ColorList.csv` open. Those limits follow directly from the [observer implementation] `../experiments/csv-pointer-20261008-retry/conversion_observer.py` (evidence not published). The [captured-display evidence] `../experiments/csv-pointer-20261008-retry/display-classification.json` (evidence not published) confirms zero nonblack pixels in all three 800×480 captures.

No intermittent fault hypothesis was disproven. The experiment also did not validate allocator reliability, timed scheduling reliability, or the entire string-copy chain.

**What went correctly and what failed**

The corrected mapper filter captured the selected conversion boundaries with original instruction bytes preserved. Recording effective slice context made the extra publication visits interpretable. The healthy guest continued through fonts and resource construction, and wrote a native `bounded_stop` final. Separate host postflight checks supported owned shutdown and endpoint removal. Those mechanisms should be reused. [Cleanup records] `../experiments/csv-pointer-20261008-retry/attempt-supervision.json` (evidence not published), [native postflight] `../experiments/csv-pointer-20261008-retry/endpoint-postflight-initial.json` (evidence not published).

The first launch failed because the synthetic gate control used a simplified syscall name rather than the actual mapper output. That implementation error escaped the controls. Future gate controls should exercise the real callback-to-mapper path.

The corrected test still lacked observation after publication and at the actual copy call. Its fault-free result could not locate the historical first bad value. Reopening the CSV six times extended coverage, but did not turn one guest into seven independent reliability trials.

The first attempt's missing final remains a real limitation. Successful owned cleanup does not make it clean guest completion. Likewise, the retry launcher's zero exit status confirms supervision success, not application startup success.

**What surprised us and how much progress this represents**

The unexpected findings were the four repeated pre-store visits and seven separate CSV observation windows. Both matter because they invalidate naïve interpretations of event totals: 2,594 visits are not 2,594 distinct completed publications, and seven parses are not seven independent executions.

The cycle reduced uncertainty about the **healthy observed conversion path** and improved the diagnostic needed for a future recurrence. It did not identify a repair, establish a new enclosing constructor return, demonstrate a resource frontier beyond the previous best run, or produce original drawable UI.

The six later healthy parses offered limited additional value for the original pre-font fault question. Another unchanged fault-free repetition would likely have similarly limited causal value. The critical path is now the remaining resource phase, alongside the known uncertainty in timed startup scheduling.

**Four proposed experiments**

These are prospective plans; none had been started at this review checkpoint.

1. **Post-font finite counted-quantum comparison — High priority, recommended next.**

   **Objective:** Determine whether main-thread scheduling limits progress through original resource construction.

   **Hypothesis:** A larger finite counted quantum after fonts may advance original resource boundaries sooner. This is tentative; slice counts alone do not establish scheduling overhead as the dominant cost.

   **Procedure:** Prepare two fresh copies from the same seed. Keep early/fonts scheduling identical. After validated font-scan epilogue `0x706d04`, compare main count **31,337** against **313,370**. Preserve workers, explicit nondefault execution requests, guards, originals and matching observations. Record sparse enclosing constructor entry/pop/caller boundaries, including `0x4007a4 → 0x4013ac → 0x324388`.

   **Expected observations:** Earlier matched constructor return or greater validated resource progress within the same bound.

   **Alternatives:** No improvement suggests this quantum change is ineffective; regression or worker starvation rejects it. More helper returns alone remain supporting evidence.

   **Success criteria:** A correctly matched enclosing constructor return earlier than control is the primary result. Resource-prefix advancement without constructor completion is a partial performance result, not completed startup.

   **Resources/risk:** Existing runtime, seed, observer framework and watchdog. No hardware scope. Main risk is altered fairness; retain finite counts and independent shutdown.

2. **Cooperative scheduling through early startup and fonts — High priority.**

   **Objective:** Determine whether the early-startup gain can survive removal of asynchronous timed stops.

   **Hypothesis:** The existing syscall-boundary candidate can preserve useful startup progress while avoiding the demonstrated native timer-replay mechanism.

   **Procedure:** Compare supported timed scheduling against cooperative main scheduling through the validated font epilogue, then restore identical post-font counted scheduling. Reuse native candidate evidence; test any newly added phase limiter and reversion before firmware use.

   **Expected observations:** Successful original font discovery, preserved worker service and continued resource progress.

   **Alternatives:** Long CPU-only stretches, starvation, lock waits or major regression make the candidate unsuitable. A healthy run would not establish general reliability.

   **Success criteria:** Original scan completion and useful matched progress within 180 seconds, with preserved dispatch/guards and no unexplained stall.

   **Resources/risk:** [Existing candidate] `../experiments/atomic-startup-20261008-session/syscall_boundary_quantum.py` (evidence not published) and supervision. Cooperative slices have an advisory duration; CPU-only execution may exceed it.

3. **Complete the CSV source chain — Medium priority; becomes High if the fault recurs.**

   **Objective:** Locate the first observed misaligned value in a failing execution.

   **Hypothesis:** Alignment may change after the current publication boundary; alternatively, allocation may already be wrong on the failing path.

   **Procedure:** Restrict capture permanently to the first pre-font CSV parse. Retain `0x62c530`/`0x62c55c`, and add conversion return `0x3852a0` and copy-call boundary `0x3852ac`. Record the completed source cell at `sp+4`, destination and synchronous original fault context.

   **Expected observations:** A recurrence exposes the earliest divergent boundary.

   **Alternatives:** Misaligned allocation redirects investigation upstream; aligned publication followed by a bad completed source redirects it downstream. Another healthy chain remains inconclusive about historical provenance.

   **Success criteria:** Locate the first bad boundary in the **same failing execution**, without bypassing `LDREX`.

   **Resources/risk:** Existing ELF and capture tools. Main risk is observation perturbing recurrence; keep capture narrow.

4. **Follow completed resource construction into original drawing — Medium priority, conditional.**

   **Objective:** Identify the first remaining boundary between resource completion and visible, responsive UI.

   **Hypothesis:** Once resource construction returns, a later main-state/display transition explains the missing output.

   **Procedure:** After a matched enclosing return is observed, follow sparse main-state and existing display API/server observations. Correlate drawable ownership, map/draw activity and pixels. Test local input response only after an original drawable exists.

   **Expected observations:** An owned drawable with original pixels and an observable response to input.

   **Alternatives:** Constructor completion without draw activity redirects attention to later state progression; drawing calls with black output redirect attention to drawable/protocol contents.

   **Success criteria:** Original drawable output plus response—not merely a child window or changed root pixels.

   **Resources/risk:** Existing private display and capture tools. No physical hardware or external network required.

**The single next action**

The recommendation is **experiment 1: the matched post-font counted-quantum comparison**, ahead of another attempt merely to reproduce the CSV fault.

The latest native final records **14,840 post-font main slices**, no post-font boost, and resource work still pending at expiry. That justifies testing a finite scheduling change; it does not prove the change will help. This experiment directly measures the phase currently preventing the startup milestone while preserving the demonstrated early-startup condition.

The executable plan is:

1. Create a common working harness with identical sparse constructor observations in both arms; retire CSV diagnostics after the first parse.
2. Validate constructor bytes, caller transfer and frame matching. Check the quantum wrapper preserves worker and explicit nondefault execution settings.
3. Run fresh control and treatment arms, each with **180-second observation and independent 185/188/190-second TERM/KILL/reap limits**.
4. Compare font completion, matched constructor returns, validated resource prefixes, worker service, display evidence and cleanup.
5. Reject the treatment if it regresses progress, starves required workers or produces unexplained faults. If both arms miss the constructor, report that milestone as unresolved; do not substitute callback savings for startup completion.

This changes one experimental scheduling condition. A better result would justify retaining it for further startup work; an ineffective result would redirect effort toward the original resource computations.

**Final engineering assessment**

- **What we expected:** A discriminator between bad allocation and later pointer change.
- **What actually happened:** Healthy observed pointers; the historical fault did not recur.
- **What succeeded:** Corrected boundary capture and bounded supervision.
- **What failed:** The first mapper gate, and the attempt to resolve fault provenance.
- **What surprised us:** Repeated pre-store visits and repeated CSV reopening.
- **What we learned:** The recorded healthy path preserved allocation-plus-eight alignment.
- **What remains uncertain:** Historical corruption origin, scheduling reliability, enclosing resource completion and usable UI.
- **How much closer we are:** Better diagnostics; no new startup/UI milestone.
- **The single most important test next:** A matched post-font finite counted-quantum comparison, judged by original constructor progress.
