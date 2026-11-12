<!-- research-note: experiments/practical-startup-20261008-1542/HANDOFF.md | thread B | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Practical startup experiments — October 8, 2026

**Wider startup constructors returned and later resource loading progressed; full startup and original drawable UI remain unconfirmed.** Six fresh original-app attempts were consumed. Five reached original main; A3 stopped during loader preparation. Original firmware/app/libraries and installed runtime were unchanged.

| Attempt | Changed condition | Actual result |
| --- | --- | --- |
| [A1] `../practical-startup-20261008-1542-a1/attempt-supervision.json` (evidence not published) | Sparse downstream observation | Subsequent constructor → `0x18a238` at101.486s; wider constructor → `0x1b6dc0` at123.945s, both saved-PC/restored-SP matched. Natural XCB flush124.419s. |
| [A2] `../practical-startup-20261008-1542-a2/attempt-supervision.json` (evidence not published) | Font offset/EOF observations | ISO EOF; BIG5 advances normally in original FreeType, about2.18MB/5.26MB by176.92s. Over75,000 invalid Autoip receives. |
| [A3] `../practical-startup-20261008-1542-a3/attempt-supervision.json` (evidence not published) | Intended receive pacing | Harness failure before main:200ms process-table query timed out. Watchdog2/launcher1; intended comparison did not execute. |
| [A4] `../practical-startup-20261008-1542-a4/attempt-supervision.json` (evidence not published) | Bounded query correction; pacing retry | Query correction worked. Pacing gate did not match libpthread wrapper:0 paced receives. BIG5 about2.16MB; no pacing effect claimed. |
| [A5] `../practical-startup-20261008-1542-a5/attempt-supervision.json` (evidence not published) | Corrected, validated receive gate | All658 observed receives paced10ms, identical-1 error. BIG5 reaches4.08MB by176.79s; about1.87× A2 progress, with host variation limiting causal attribution. |
| [A6] `../practical-startup-20261008-1542-a6/attempt-supervision.json` (evidence not published) | Latin-only font-discovery fixture | Unchanged original ISO font reaches97,860-byte EOF by116.17s; no BIG5 open. Main proceeds through original layouts/pictures and offscreen pixel/string work; still loading pad-button PNGs at175.032s. |

The receive fixture preserves the held invalid-descriptor return and all networking guards. Its final gate validates132 loaded original libpthread bytes, syscall PC/LR, worker name, invalid FD and saved application return `0x51d07c`. A6 additionally maps a separate fontconfig file to scan an identical ISO8859 font copy; CJK coverage is reduced. Neither condition forces display calls. The held clock remains unchanged.

Natural X11 output created the original1×1 InputOnly child. A2/A4/A5/A6 have post-return black root captures; A1 has only its initial capture. No `XMapWindow`/`XPutImage` or usable original pixels were observed. A6 final sampled main at172.448s: PC `0x626ed4`, LR `0x627110`, SP `0x7ff3c450`, no pending sampled main syscall. The final175.032s path is `skin16/picture/p0005_padbtn_3fcs_tr.png`. This is progressing skin-resource construction, not an established persistent wait.

All owned processes/endpoints were independently confirmed absent after every attempt; helpers closed by session minute26.77. A3 retains its real watchdog-query failure. The earlier PermissionError handling was corrected in new copies: fresh owned absence recovers an exit race; still-live/ownership/query failures remain failures and other groups still receive shutdown. Focused controls:6 permission cases, one native owned-group TERM/KILL/reap check,5 census-deadline cases, and13 final receive-gate cases. Prior controls were reused.

Native bounded final records exist only for A1 and A6. No observed `ql.run` return or clean guest completion is certified. Advisory worker/main TimeoutErrors and host termination remain distinct. Missing A2–A5 final records remain missing.

Runtime-to-owned-closure total: 893.245s; cleanup after recorded stop requests: 0.823s. Total through final reporting timestamp: 1777.1s (29.62min); no overrun. First exact clock was recorded at20:42:33 UTC /15:42:33 CDT after the initial request/README read; deadlines conservatively include20 additional seconds, not a fabricated exact first-action time. A6 launched at minute23.845, before the24-minute cutoff. See [exact timing/closure] `session-summary.json` (evidence not published).

Next smallest test: retire per-open image-path output, match the outer skin-resource loader return and count completed images sparsely while retaining A6’s explicitly limited font fixture. Do not repeat completed parent stages or change clocks without timing evidence. Full original font coverage remains a separate cache/startup question.

Raw stdout/stderr, effective argv/environment, source identities, byte checks and cleanup are inside each linked attempt. Each has `result-summary.json` and `process-census-after-runtime.json`; completed display runs also have `display-classification.json`. [Short experiment log] `EXPERIMENT_LOG.md` (evidence not published), [native cleanup control] `native-cleanup-control/driver-result.json` (evidence not published), and [changed tools/controls] `tools/` (evidence not published) remain local. No archive, upload, hardware, build or repack work was performed.
