<!-- research-note: experiments/cooperative-font-20261008/HANDOFF.md | thread B | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Cooperative early/font comparison — October 8, 2026

**Question:** can cooperative early/font scheduling preserve original font and construction progress while avoiding asynchronous timed stops? **Result: yes in this bounded pair; retain cooperative early/fonts plus finite post-font count 313,370 for the conditional drawable-following guest.** This is a startup-progress/reliability-condition choice, not an early-phase speedup or general reliability claim.

Both fresh same-seed guests used one common sparse observation set and the same accepted post-font count. Control used supported timed early/fonts; treatment used the [phase-limited existing syscall-boundary candidate] `common/syscall_boundary_quantum.py` (evidence not published), reverting at validated `0x706d04`. Workers, TLS, explicit execution requests, original results/exceptions/instructions and execution/network guards remained preserved. The copied timed wrapper's exact timeout=0 boost gate preserves explicit timeouts without changing ordinary timed scheduler requests. [Prepared controls and limitations] `PREPARATION_HANDOFF.md` (evidence not published), [focused controls] `controls.json` (evidence not published), [effective control] `control/attempt-supervision.json` (evidence not published) / [treatment] `treatment/attempt-supervision.json` (evidence not published) commands, code identities and actual deadlines.

All times below are **guest-process-relative**; raw event `elapsed` values are probe-relative and slightly shorter.

| Observation | Timed control | Cooperative treatment |
| --- | --- | --- |
| All five original BDFs / 17 scan faces / matched font frame | Pass | Pass |
| Font return | 43.030s | 44.508s |
| Matched active `0x40d6e8 → 0x40df28 → 0x322b40` return | 192.908s | 202.430s |
| Genuine caller execution at `0x322b44` | 192.908s | 202.430s |
| Matched selected `0x4007a4 → 0x4013ac → 0x324388` return | 232.879s | 241.428s |
| Matched resources in common 255.685665s after fonts | 807 | 823 |
| Ordered unique layout paths in common window | 39 | 39 |
| Configured observation / native final elapsed | 300s / 300.740s | 300s / 300.127s |
| Root captures | Three black | Three black |

Treatment extends the full control 807-return caller/depth prefix; both reach the identical 39-path prefix ending `LS_L_618.csv`. These totals support useful resource progress. Cooperative font completion is 1.478s later; active/selected enclosing returns are 9.523/8.549s later. Both nevertheless cross relevant enclosing completion and original main continuation, advancing beyond the previous unresolved boundaries. [Full comparison, timestamped streams, frames and observations] `comparison.json` (evidence not published), [offline analysis] `analyze.py` (evidence not published), [stdout] `analysis.stdout.txt` (evidence not published).

Required workers 2004/2005/2006/2014 received slices in every observed common-window interval. Minimum increments were 23/15/16/23 control and 57/38/38/57 treatment; this establishes sparse service only. No synchronous exception or unexplained fault was observed. Treatment recorded 166,969 original dispatcher returns, 22,774 early/font main dispatcher returns and 866 advisory syscall stops. Its longest completed cooperative `emu_start` stretch was **4.336s** before fonts; font-phase maximum was 0.327s. These include syscall work/waits and observers. Exact CPU-only/wait decomposition is unmeasured; 20ms remains advisory. Two repeated font-phase PC spans of about five seconds preceded successful font completion and do not establish a persistent wait.

Both native outcomes are `bounded_stop`, preceding fresh independent 305/308/310 TERM/KILL/reap deadlines. Owned closure, direct-child/watchdog reaping, private control removal and independent [control postflight] `control/endpoint-postflight-initial.json` (evidence not published) / [treatment postflight] `treatment/endpoint-postflight-initial.json` (evidence not published) passed. Guest launch-to-reap was 301.737/300.638s. Actual absolute deadlines and finalization timing remain in the linked supervision records. Raw [control stdout] `control/supervision/guest.stdout.txt` (evidence not published)/[stderr] `control/supervision/guest.stderr.txt` (evidence not published) and [treatment stdout] `treatment/supervision/guest.stdout.txt` (evidence not published)/[stderr] `treatment/supervision/guest.stderr.txt` (evidence not published) are retained. Preparation failures remain in [preparation-results.json] `preparation-results.json` (evidence not published); two original guests launched, with no replacement guests.

Only original `XOpenDisplay`/`XCreateWindow` API activity and one 1×1 InputOnly child were established. No map/draw API activity, owned nonblack original drawable, usable UI or attributable input response was established. Input was not injected.

**Next test / uncertainty:** the relevant enclosing return plus subsequent main execution now satisfies the conditional drawable investigation prerequisite. A distinct bounded follow-up should follow later main continuation and original private-server drawing/drawable ownership, then apply one scoped input only after identifying an original drawable. Retain cooperative early/fonts and count 313,370 for that test, with independent finite supervision. One healthy pair does not establish timed-corruption provenance, general reliability or low-latency worker fairness.
