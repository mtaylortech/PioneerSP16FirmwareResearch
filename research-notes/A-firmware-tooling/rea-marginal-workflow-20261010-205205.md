<!-- research-note: experiments/rea-marginal-workflow-20261010-205205/HANDOFF.md | thread A | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# REA marginal workflow evaluation — October 10, 2026

**Retain REA for interactive queries; retain the corrected stock Ghidra workflow for function recovery. No accepted end-to-end discovery speedup was demonstrated.** Both default imports missed the required scheduler and context-destructor functions. REA’s warm latency advantage comes from querying a live Java session instead of reopening a saved project; it is not a faster analysis engine. This was REA discovery followed by stock replay, not two independent discoveries.

The [predeclared question] `PREDECLARATION.md` (evidence not published) was whether the argument-0 deferred-submission record owns its task/task-box pointers, and whether removal executes or disposes of the task. Final family entries were not supplied beforehand; `0x17ed7c` and `0x5049c8` were discovered through scheduler/wrapper evidence. This relational holdout was not an independently curated secret oracle. Getter `0x329614` was the reused known control. The already-known admission-bookkeeping result receives no discovery credit.

Observed record behavior:

- `0x504558`: `r1` is preserved in `r7`; `r10` preserves the wrapper. At `0x5046d8`, `r6 = [r10+0xc]` obtains the box implementation. `operator_new(8)` at `0x5046dc` returns the record in `r0`. Stores at `0x5046f0/0x5046f4` write the task at record `+0` and box pointer at `+4`. These paths show raw pointer capture, with no box retain/clone call in the builder.
- `0x5041e8`: cross-thread admission calls box virtual slot `+0x10` with permission argument `2` at `0x5042d0`; zero returns with the record pending. Success clears record `+0` at `0x504318` before record deletion at `0x5043b0`. Same-thread paths can call task slot `+8` and slot `+4` before clearing the record. Thus successful removal does not perform a second task disposal through the cleared record.
- Fallback pool cleanup `0x5049c8` calls task slot `+4` at `0x504a04` for each non-null pending task, then deletes the record at `0x504a0c`. It does not call execution slot `+8` or release record `+4`. The recovered context destructor `0x17ed7c` has the same disposal pattern for its auxiliary pool, then calls unexamined helper `0x17ecd0`.

These instructions support pending-task disposal versus transfer on successful admission. Actual indirect task implementations, destructor side effects, per-thread shutdown through the unexamined helper, and the editor/box lifetime coupling remain unknown. This does not establish a legal nondestructive editor settlement route or complete the outstanding normalization/runtime/UI milestone.

| Entry | Role | REA/default stock | Independent instruction checks |
|---|---|---|---:|
| `0x5030b4` | Known scheduler seed | Both missing function; stock focused recovery succeeds | 133, focused only |
| `0x17ed7c` | Discovered context destructor | Both missing function; stock focused recovery succeeds | 31, focused only |
| `0x504558` | Record builder/wrapper | Matching body and listing | 246 |
| `0x5041e8` | Related flush/removal | Matching body and listing | 207 |
| `0x5049c8` | Discovered fallback pool cleanup | Matching body and listing | 27 |
| `0x329614` | Known getter | Matching body and listing; saved control agrees | 4 |

[Verification] `exports/verification.json` (evidence not published) checks original PT_LOAD bytes, every mnemonic/operand, native ARM context (`TMode=0`), and recovered bodies. All 484 recognized-function instructions and 164 focused-recovery instructions pass. All 123 recognized direct-flow targets and 42 additional focused targets match original decoding and reference exports. All 647 returned incoming references pass source-byte/literal checks. The 252 outgoing references also agree between the two default databases; 129 are data edges whose agreement is not an independent value-flow proof. Reference recall and independent completeness of new function boundaries were not measured. Missing functions stay failures. Database `undefined FUN_x()` signatures are distinguished from decompiler parameters: the getter uses `r0`, and the wrapper recovers three parameters despite its zero-argument database signature.

| Measurement | Seconds |
|---|---:|
| REA first import + failed seed query | 191.266 |
| REA logged default autoanalysis | 183 |
| Stock cold replay, including exports/save/cleanup | 193.357 |
| Stock logged default autoanalysis | 186 |
| REA repeated `0x5049c8` dossier queries, three | 0.01173 / 0.00993 / 0.01033 |
| Stock reopen/export with explicit matched decompiler options, three | 4.760 / 4.272 / 4.283 |
| Stock in-process cold extraction, four bodies combined | 0.121 |
| Existing corrected-project getter reopen, readOnly/noanalysis | 5.299 |
| Stock focused missing-entry recovery + six exports | 4.794 |
| Recovery operation inside that process | 0.0215 |
| Final byte/instruction/reference verifier | See [timings] `exports/timings.json` (evidence not published) |
| Independent cleanup/preservation check | 0.375 |

The live REA client occupied 422.553 seconds: 196.961 seconds inside 44 tool calls and 225.592 seconds of transport/polling/inspection/operator gaps. Hands-on preparation and idle time were not clocked separately, so no effort-saving or causal discovery-time claim is justified. Both matched accepted end-to-end times are missing because two required dossiers were absent. Focused recovery is a different stock profile and remains replay. Prior installation cost is excluded. Cold query is not directly equivalent to stock’s four-body batch plus project save. Repeated stock processes include JVM startup; its in-process extraction is already fast.

Retained REA is **6.3.0**, Ghidra **12.1.4**, Temurin **21.0.12.1**, bundled Node **24.19.0**. Both import original ELF SHA-256 `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2` (11,993,612 bytes), ELF loader, ARM:LE:32:v8/default, base `0x8000`, default global analysis, and zero additional libraries. REA reports 548 applied/31 unsupported relocations; code bytes independently match. Its ELF load-image verification operation remains unsupported. Initial stock decompiler initialization differed; explicit REA-equivalent options removed literal-pool differences. Remaining [matched-option diffs] `exports/00504558.matched-options.diff` (evidence not published) are focused-recovery names. The original cold and initial warm measurements retain that qualification.

Effective commands/bounds are in [REA client configuration] `raw/sdk/client-config.json` (evidence not published), [owned REA command] `logs/mcp-discovery/command.json` (evidence not published), and each `logs/native-*/effective.json`. Enclosing allowance: 1,800 seconds; REA owned run: 1,600 seconds; provider startup: 900; first caller: 960; later callers: 120; native cold: 900 and reopen/recovery: 120, capped by remaining session time with 60 seconds reserved. This chat had no REA tool catalog, so the installed SDK/local stdio transport was reused. No package, registration, or REA implementation changes.

New work used the adapted queued client, reused owned runner, stock exporter/launcher, focused recovery script, verifier and closeout script: seven scripts / 30,402 bytes at measurement close. There were 44 REA calls plus client stop and 11 stock process attempts. [Raw SDK evidence] `raw/sdk/` (evidence not published) is 26.49 MB; [exported Evidence] `exports/rea-evidence.json` (evidence not published) is 6.22 MB with all 35 unique expected records, exported before closing. Stock cold and focused exports are 238/288 KB. [Code identities] `setup/code-identities.json` (evidence not published), [coverage] `exports/evidence-coverage.json` (evidence not published), raw stdout/stderr and [retained failures] `logs/harness-failures.txt` (evidence not published) preserve provenance. The launcher ClassNotFoundException, missing-export exit-zero rejection, Python path/import mistakes, and verifier spelling failures are retained.

[Postflight passed] `exports/postflight.json` (evidence not published): 13 owned process groups absent, no owned live PIDs, socket/root gone, ephemeral REA project gone, and the new stock working project removed after export. Original ELF, selected prior exports, the original saved corrected project, and retained REA code are unchanged. No firmware/guest/hardware execution or outgoing chat messages occurred.

Next test, only if selected: reuse a saved corrected working project for a genuinely new family, pre-clock operator work and use the same live-session versus batch/reopen lifecycle. REA’s missing-boundary behavior still requires a practical recovery/import mechanism before it can replace the existing workflow.
