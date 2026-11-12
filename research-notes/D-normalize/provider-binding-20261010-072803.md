<!-- research-note: experiments/provider-binding-20261010-072803/HANDOFF.md | thread D | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Offline 1.50 provider binding — October 10, 2026

**Complete: the context-provider gap in 06B is closed for the mapped HexaTrackAudioSystem construction route.** Ghidra and independent original-byte checks establish how the SAVE & REPLACE manager receives the provider. This is static evidence, not observed runtime assignment or normalization behavior. No guest was necessary, and no physical SP-16 was accessed.

Question: does the save route's editor/referrer context `+0x4344` select the HexaTrackAudioSystem `+0x200` interface? The owner authorized this one offline trace within 16 minutes, subsequently permitting an emulated guest if needed. The revised [proposal](../history/handoffs/07-OBSERVATION-PROPOSAL.md) and preserved [06B](../history/handoffs/06B-TRACK-ASSIGNMENT.md) define its scope. No adjacent project-flush investigation began.

## Original and tools

Held input [EP085_Main_R] `../../decode/output/image1/payloads/pdj/pdj/EP085_Main_R` (evidence not published): 11,993,612 bytes, SHA-256 `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`, checked before investigation and in final verification. ARM32 little-endian ET_EXEC. Ghidra 12.1.4 imported this exact ELF with relocations enabled, library loading disabled and global autoanalysis disabled; focused disassembly/decompilation used ARM:LE:32:v8/default and image base `0x8000`. Saved [separate 1.50 project] `projects/SP16_1_50_provider.gpr` (evidence not published), program `/EP085_Main_R`, leaves the historical 1.60 project intact.

Original-byte search/verification uses the installed emulation environment's Python, Capstone and pyelftools. The emulation environment was used as offline tooling; the firmware was never executed. Final [Ghidra identity and exports] `exports/corrected-constructor/program-identity.txt` (evidence not published), [verification] `verification.json` (evidence not published) and [table data] `exports/window-init-table.json` (evidence not published) are the decisive receipts. Pseudocode signatures/types remain inferred; original register/stack instructions govern the argument chain below.

## Checked pointer chain

Let A be the enclosing application object, H the constructed audio-system owner, C the newly allocated context, W the window controller, V the SamplingEditViewController and M the SamplingEditManager.

| Edge | Original 1.50 instructions / result |
|---|---|
| Audio owner | `0x56f940` calls constructor `0x1b68a4`; `0x56f944` stores H at `A+0x2c` on the Hexa branch. Constructor `0x1b68dc–0x1b690c` installs interface vtable `0x8611a8` at `H+0x200`. |
| **Missing store resolved** | In `0x56dc80`, allocation at `0x56dd38–0x56dd3c` supplies C (0x4350 bytes). `0x56dd40` loads H from `A+0x2c`; `0x56dd54–0x56dd58` adjusts non-null H by `+0x200`. `0x56ded8–0x56def0` forms index **0x4340 + 1 + 3 = 0x4344** and stores that pointer into C. The null branch stores null, not a fabricated owner. |
| Context publication | `0x56f148` stores C at `A+0x68`; a replacement branch can dispose of the old context and reload the published C. |
| Window context | `0x56f1d0–0x56f1e4` passes `A+0x68` into `0x318c70`; `0x318ca4` retains that argument and `0x318d2c` stores C at `W+0x44`. |
| Same window reaches view factory | `0x31eb50 → 0x31ea7c` runs the initializer table at `0xb774bc`. Entry 31 at `0xb775b4` is `0x324190` with zero object adjustment. The table dispatch preserves W as the receiver. |
| View-controller context | `0x3241bc–0x3241c4` passes `W+0x44` as r3 to `0x28f508`. That constructor spills it at `0x28f518`, then calls base `0x2ec1bc`; base stack load `0x2ec238` and store `0x2ec248` install C at `V+0x24`. Stack accounting is 36-byte register save plus 12-byte locals in the base. |
| Manager context | `0x3247a8` calls factory `0x28e208` with V. `0x28e22c` reads `V+0x24`; `0x28e248` passes C at caller stack +0xc to constructor `0x28dc2c`. Its 36-byte register save plus 60-byte locals make `0x28dc3c` (stack +0x6c) that same argument; `0x28dc54` stores C at **M+4**. RTTI identifies SamplingEditManager through name `0x8852f8`, typeinfo `0x885310` and primary vtable `0x884b70`. |
| Save consumes that binding | `0x28bc54–0x28bc60` passes M to `0x2f8ed0`; `0x2f8ed8` reads M+4. Getter `0x329614–0x32961c` returns C+0x4344. Its virtual track → parameter-manager → setter chain is the original route mapped in 06B. |

This establishes the constructor-to-save connection previously missing. It does not claim every possible application mode/provider uses HexaTrackAudioSystem, exclude later pointer replacement, establish a particular live instance, or prove that the busy setter accepts a save. Project flush activation/destinations and completion/reset/reader-refresh effects remain the two separate gaps in 06B.

## Verification, failures and cleanup

Independent [verifier] `scripts/verify_bytes.py` (evidence not published) passes **3,456 checks**, including all **3,407 instruction byte pairs in eleven final Ghidra exports**, exact pointer-chain instructions, interface/table data and rejection controls for wrong release, altered decisive bytes and incorrect offset arithmetic. The input remains unchanged. These counts measure static correspondence, not firmware progress.

Preserved failures: the first search script was named `inspect.py`, shadowing Python's standard `inspect` module during Capstone import; [stderr] `logs/scan.stderr.txt` (evidence not published) retains the circular-import failure. Renaming it to [trace_bytes.py] `scripts/trace_bytes.py` (evidence not published) resolved that tooling fault. The [first Ghidra launch] `logs/import/result.json` (evidence not published) exited 1 when its launcher attempted to save Java settings outside the writable workspace. [Raw failure] `logs/import/stderr.txt` (evidence not published) is retained; redirecting Java user-home/settings/cache/temp into this experiment permitted the import. No approval escalation or instrument access occurred.

Early guessed Ghidra entries `0x1b67e4`, `0x1b68d0`, `0x56f800` and `0x5703f0` produced partial/misbounded functions. Their discovery exports remain retained and excluded from the final chain. The final pass removed these provisional entries and recreated the true audio constructor at `0x1b68a4`; its verified body now reaches the actual return at `0x1b6b54`. The field search also decoded data in an executable segment; candidates were leads checked against bounded original instructions, not an exhaustive whole-program writer proof.

Each Ghidra call used the [owned finite runner] `scripts/run_ghidra.py` (evidence not published), 180 seconds for import and 120 seconds for later passes, 20 seconds per decompilation, with bounded TERM/KILL/reaping. Effective commands, environment, source hashes, raw stdout/stderr and results are under [logs] `logs/` (evidence not published); all twelve owned process groups are absent and no project lock remains. The failed launch remains a failed launch despite successful cleanup. Timeout termination was not exercised. No guest endpoints or physical connections were created.

Four outcomes: **evidence validity passed; narrow static binding established; requested trace complete; owned tooling cleanup/evidence preservation passed.** No firmware-native final applies because firmware did not run.

**Next test:** a separately selected offline trace of callers that flush the changed `PlaybackData.audioSourceUrl` into project files, distinguishing explicit/automatic save and actual destinations. Reuse this 1.50 project and binding; physical SP-16 access is not required. No custom normalization implementation, guest launch or remaining analysis scope follows automatically from this completed question.

**Closeout:** first clock `2026-10-10 07:28:03 UTC`; final verification/save at `2026-10-10 07:41:42 UTC`, **819/960 seconds elapsed** before final delivery. All required trace work, byte checks, preservation and owned cleanup are complete. The allowance closes here; unused time grants no adjacent trace. [Final result] `result.json` (evidence not published) records source identities, commands, four outcomes and resolving handoff links.

## Assigned-analysis archive readiness — October 10, 2026

**Ready to archive; no assigned obligation remains.** The requested [assignment closeout review] `../../engineering-reviews/2026-10-10-ghidra-provider-binding-assignment-closeout.md` (evidence not published) proposes its index entry for the coordinator; this closeout changes no shared README/index or canonical project.

The saved `projects/SP16_1_50_provider.gpr`, program `/EP085_Main_R`, reopened with `-readOnly -noanalysis`: [receipt] `logs/closeout-reopen/reopen-receipt.txt` (evidence not published) confirms all eleven saved listings exactly match the final exports, corrected constructor retains return `0x1b6b54`, and four provisional entries remain absent. [Focused ELF checks] `logs/closeout-reopen/focused-original-check.json` (evidence not published) confirm decisive stores/getter, interface slot and factory entry, unchanged original identity and retained export hashes. The prior full verifier was reused, not rerun. New [check script] `scripts/ProviderCloseoutCheck.java` (evidence not published), [runner] `scripts/run_closeout.py` (evidence not published), commands/settings and raw logs are preserved under `logs/closeout-reopen/`; [result] `logs/closeout-reopen/result.json` (evidence not published) records 4.786 seconds, owned group absent and no project locks. No firmware launched or other session was stopped.

Integration: supersede only 06B's conditional provider gap; use final exports, not discovery entries or inferred prototypes. Preserve release 1.50 attribution; do not transplant addresses into canonical 1.60. Project-flush activation/destinations and completion/reader refresh remain future questions, not unfinished obligations. No conflicting finding is known within this assignment's checked evidence. Optional continuation: separately select a ≤16-minute offline trace of one project serialization-to-file activation/path, preserving original branches, destinations and failure handling. No permission or unused time carries forward.
