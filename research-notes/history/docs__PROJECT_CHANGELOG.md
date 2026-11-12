<!-- source: docs/PROJECT_CHANGELOG.md | scrubbed -->

# Project changelog

## 2026-10-07 — canonical evidence consolidation (America/Chicago)

Captured the completed two-image decryption/extraction/audit, the earlier OS/application readiness assessment, supplied source/build materials, service/user/update documentation, historical negative results and unresolved modification prerequisites. No application feature investigation, firmware execution, hardware work, Linux rebuild or new external research was started.

Created:

- `docs/PROJECT_STATE.md`: canonical synthesis with 36 VERIFIED finding IDs, 3 parked hypotheses, 0 active hypotheses, component/partition model, evidence boundaries, commands, actionable priorities and Current Handoff.
- `docs/EVIDENCE_LEDGER.md`: 23 source entries with provenance, reliability, scope and retained URLs where known.
- `docs/ARTIFACT_INVENTORY.md` and `.json`: sizes/SHA-256 for 108 selected original/source/derived/evidence files, including every top-level supplied file except Finder metadata; no key bytes/digest.
- `docs/EVIDENCE_SNAPSHOT.json`: bounded binary-header/import/banner observations, versions, ISO component extents and source-part validation.
- `docs/TRANSFORMATIONS.json`: 25 grouped input/output transformation records and manifest references.
- `docs/VALIDATION.json`: final document/path/hash/provenance validation results.
- Root `README.md`: discoverable entry point to the canonical handoff.

Updated `decode/README.md`, `STATUS.md`, `FINDINGS.md` and `PROCESS.md` to point to the canonical state and keep earlier extraction/process history subordinate. The decoder implementation was unchanged in this consolidation. The existing `--audit` command was rerun, refreshing generated audit/nested records; both inputs passed. Small documentation helpers, PDF text/renders and a fresh audit log are under `decode/tmp/consolidation/`.

Corrections and clarified uncertainties:

- Distinguish file-level extraction completeness from source recovery or binary-interior unpacking; record firmware special-entry omissions separately from the older source-extraction omissions.
- Distinguish CRC/marker integrity from cryptographic authenticity and full updater acceptance.
- Preserve generic license vs binary-version discrepancies (BusyBox), old source-script vs kernel version differences, boot target/config naming differences, release vs build dates, and ELF ABI minimum vs actual kernel identity.
- Incorporate manual-documented exact chip identifiers/storage/controller roles, while leaving actual hardware geometry, enabled CPU state and physical-unit confirmation unknown.
- Preserve MAIN/apl/SUB mappings as unresolved despite strong naming hints; do not import any unsourced DJS-1000 behavior.
- Mark earlier time estimates as unmeasured planning judgments, not promises; no target feature or active hypothesis experiment exists.
- Confirm split-source archive reconstruction and duplicate CODA archive identity with actual hashes. Exact firmware acquisition URLs and publisher hash verification remain unknown.

The workspace layout was preserved. No Git commit, remote publication or backup was created. Validation details are in `VALIDATION.json`; source-to-output audit details remain under `decode/output/`.

## 2026-10-07/08 — two bounded application-emulation sessions

The first user-authorized 15-minute window began October 7 at 23:46:13, reached the unchanged 1.60 application's entry/main, and saved the missing-ALSA/null-pointer startup failure. The additional 15-minute window began October 8 at 00:04:10, established synthetic duplex audio, observed affinity requests and 17 threads, localized a later tcmalloc fault, and corrected the emulator's ARM TLS helper. The final saved run lasted 76.216 seconds, deadline-stopped, with zero recorded guest memory faults. Original application/library bytes remained unchanged. E24/E25 retain the setup failures, intermediate results, workarounds and limitations; no Linux VM, full-board boot, physical audio or instrument validation occurred.

## 2026-10-08 — closing persistent handoff

Updated PROJECT_STATE.md, EVIDENCE_LEDGER.md, the two experiment reports and root navigation. Preserved one canonical Current Handoff, replaced obsolete feature-first/startup-failure guidance, and separated requested affinity, synthetic audio and bounded stability from unproved hardware behavior. Added the exact runtime/launch/permission recipe, fixture purposes/limits, failed-attempt table, integrity boundaries, clean-root state and one proposed display milestone.

Preserved the original static validation as VALIDATION-20261007.json and copied the user-supplied host crash report into the first experiment's logs so the project no longer depends on chat attachment access. Updated the documentation checker for 40 findings / 26 evidence sources and experiment links; added a static emulation-handoff checker/report. Historical experiment verification snapshots were not rewritten: only their README hashes are superseded by the explicit documentation revisions. No experiment, firmware audit, extraction, installation or new research was performed. Closing checks read source/copy bytes, saved results, package metadata, launch syntax and host process state; no project emulator/installer process remained. No Git commit, remote publication or backup was created.

## 2026-10-08 — bounded original-display investigation (00:40–01:00 CDT)

Created experiments/emulation-display-20261008-004011 with a complete isolated root/harness/config set. Verified an authenticated contained Xvfb :16 using an extracted official XQuartz 2.8.6 package, without installing it system-wide. Scoped socket fixture allows only guest X0 to local X16; one targeted address-translation correction resolved a getpeername exception. The retry returned null from XOpenDisplay because mapper-only Xauthority access failed; server rejected the unauthenticated setup. No original window was created or captured. Preserved failed setup attempts, launch, logs, partial summary, hashes and boundary checks.

The retry's alarm fired at 76.002404 seconds but did not stop remaining workers; SIGTERM stopped it before the reserved closing interval, leaving no native final JSON. The display supervisor and child exited. Original baseline harness/results/library bytes and checksum snapshots remain unchanged; new-root 12,840-entry comparison and 26 ELF identities passed. Updated the single Current Handoff and E27 around the authentication blocker plus independent process-deadline requirement. The user corrected temporary socket-directory ownership; automatic approval review rejected a proposed shared-directory symlink and it was not executed. No panel simulation, feature change, real-audio test, VM/kernel build or hardware deployment occurred.

## 2026-10-08 — user-requested archival audit after the display session

Verified every previously saved closing-record checksum and fresh process/socket state without restarting an emulator or display. Preserved the exact original session request, user administrator-action provenance, ordered attempted/resolved/remaining blockers, root-copy provenance and the temporary documentation helper. Corrected stale project navigation/priority/history wording, distinguished historical validation reports from current checks, corrected AudioEditor's observed naming time to 79.638589 seconds, and explicitly recorded the original closing documentation's 34.682-second overall-budget overrun (all runtime processes stopped before the reserved cutoff). Historical snapshots and measured harness/results remain unchanged; pre-edit documents are retained in the new archive-audit directory.

Created a private local tar archive of all three emulation directories (including the complete installed venv and original roots/tools/logs), current project docs/navigation and validation helpers. A member manifest plus a full content/link/mode comparison verifies its saved contents; confidential key/cookie bytes are compared directly without emitting their digests. This is a same-disk archive, not remote/off-device backup or a machine-independent runtime. The macOS base Python framework and original static research inputs remain external. Archive restore must use a separate directory and a future runtime session must supply fresh labels/deadlines and fix the recorded cookie-access blocker.


## 2026-10-08 — authentication visibility and original display API progress (01:18:49–01:48:49 CDT)

User authorized a 30-minute session with experiments stopped by minute 25 and final five minutes reserved. Used one chat, no subagents. Created emulation-display-20261008-011849 as a complete copy of the prior root/harness/config/display set. Reused the existing venv and contained XQuartz resources; no downloads, installs or firmware changes. Preserved the previous Current Handoff verbatim as dated history and retained one new Current Handoff, E28, V41/V42 and parked H04.

Server-only attempt failed because the helper was prepared one directory too deep; log preserved, private path corrected. First guest verified actual cookie access=0 but blocked in host read before XOpenDisplay returned. Preserved complete native result, host stack sample and exact code. A local socket reproducer identified stock fcntl64 passing Linux nonblocking flags directly to Darwin. One display-only correction/retry retained all baseline flags and tested getpeername translation. Fresh authenticated setup status=1; original XOpenDisplay returned 0x17de000 and XCreateWindow returned 0x200001. No later display write/flush/map was observed, all server-root trees had zero children, and root captures were black. Milestone 2 achieved; milestone 3 and buffering cause remain unresolved. No panel input, real audio, later feature research or forced mapping was executed.

Retry alarm at 76.004691 s stopped only a worker; independent host supervision SIGTERM/reaped the exact guest at 78.013921 s. Native retry final JSON/counters/PC absent; partial logs retained and labeled. Original 17-thread/synthetic audio startup recurred in sampled logs, with no recorded invalid_memory; no long-term stability claim. All runtime stopped at 01:26:40.327 CDT before the required cutoff. Private helper removed, exact PIDs/endpoints checked; shared socket directory retained empty.

Verified 12,840 original root entries plus only the new private cookie, 26 selected ELFs, both UPDs and 67,729 historical records. Previous archive checksum remains unchanged. New private archive/manifest/checksum/member verifier preserve this complete experiment and updated documentation, with exact prior-archive restoration dependency for the venv/older history. External verification/session-close reports record actual archive status and final timing; no self-referential archive claim or off-device backup claim. Historical manifests/checksums and all originals remain intact.


## 2026-10-08 — efficient next-chat prompt preparation (09:57 CDT)

Documentation-only, up-to-five-minute user-requested handoff preparation. Created docs/NEXT_SESSION_PROMPT-20261008-095741.txt with project purpose, E24–E28 progress, the original Display-buffer/server-delivery question, exact retained baseline/corrections, expired-deadline/helper prerequisites, selective reading, task queue, 30-minute ceiling, early-completion rules, three-minute reports, limited retries, configuration/provenance/logging and verified archive requirements. Updated only the Current Handoff's next-prompt pointer; retained earlier prompts and one Current Handoff. No guest/server run, dependency change, firmware modification or later-stage authorization. Pre-edit state/changelog, hashes, path/content checks and a small document-only archive are retained in experiments/handoff-preparation-20261008-095741. Prior runtime archives and historical validation snapshots remain unchanged; their document snapshots predate this explicit revision.

## 2026-10-08 — original request identified in libxcb (10:16 CDT session)

Executed the direct user's up to 30-minute display/preservation task queue in one chat without subagents. Derived ARM Display fields and real flush/map entry addresses from the shipped libX11 ELF and verified loaded bytes before read-only hooks. Complete isolated copy retained all auth/nonblocking/TLS/audio/IPC/epoll baseline fixtures and existing runtime; fresh cookie/deadlines/helper per server. No new dependency, firmware patch, forced flush/map or panel input.

First bounded probe exposed a snapshot-hook collision: the existing API-return callback removes itself from Qiling's live hook list, skipping the next diagnostic callback. Preserved exact first source/layout/result. One targeted retry used binary-verified pre-unlock/return instructions and derived the separate shipped libxcb output buffer. Original36-byte CreateWindow 0x200001 transfers from Xlib into libxcb at return and persists identically at 73s and final 76s, sequence 7/written 6/error 0. No later library flush/map/send entry or display write; all trees0 children and black root images. Request is1×1/InputOnly. Diagnostic success, milestone 2 only; natural startup wait and original drawable UI remain open. H04 buffering observation resolved; reduced parked hypotheses to 3 and added V43/V44/E29.

Both complete native JSON files record bounded-stop outcomes and no memory faults; host reaped guests without signals at 76.381/76.245s. New probes observed 15/7 threads including main, so the earlier 17-thread measured baseline remains distinct and preserved. Runtime stopped 10:25:58.540 CDT; no further guest launch. Verified12,841 previous root file/link entries except fresh cookie,26 ELFs,both updates, 101,912 historical records and both prior archive digests. All eight scoped PIDs/endpoints gone; exact private helper removed and root-owned1777 shared directory empty.

Retained prior Current Handoff as dated history and its exact standalone copy; one new Current Handoff describes the precise queued-request blocker and proposed main-thread wait trace. Created a new private same-disk archive with complete new experiment/docs/history and external member/checksum/content/link/mode verification, referencing both unchanged prior archives. Final verification/status/timing are in the external closing reports; frozen archive members are not edited. No off-device backup or portable restored execution claimed.

## 2026-10-08 — next-worker prompt and handoff readiness (10:53 CDT)

Documentation-only follow-up requested by the user, with a five-minute response limit. Created NEXT_SESSION_PROMPT-20261008-105321.txt for another up-to30-minute, one-chat/no-subagents session. It advances from the verified queued libxcb request to bounded main-thread control-flow/wait localization and permits at most one directly evidenced narrow fixture correction/retry. Retains all original-byte, scope, timing, process, authentication and archive boundaries. Explicitly warns against rerunning historical mutator/build/validator scripts or regenerating the incomplete early layout. A sampled deadline PC and missing panel opens remain clues rather than causal findings; milestone3 requires drawable original output.

Added a discoverable latest-prompt pointer to the single Current Handoff. Preserved pre-edit docs and a verified small documentation snapshot/readiness report in experiments/handoff-preparation-20261008-105321. E29 native results/runtime artifacts and all prior archives remain unchanged. Current docs postdate those frozen snapshots. No guest/server launch or later research stage was performed. Handoff is ready for a worker with this workspace and existing macOS runtime; off-device backup and tested portable restoration remain separate gaps.


## 2026-10-08 — main startup progression and preservation (10:59:16 CDT)

User invoked NEXT_SESSION_PROMPT-20261008-105321.txt for up to30 minutes, one chat/no subagents. Created a complete emulation-startup-20261008-105916 copy and byte-validated18 permanent main-filtered checkpoints/selected syscall boundaries, retaining all fast-mode/baseline/display corrections and both-buffer snapshots. One independently supervised probe demonstrates main returning from original CreateWindow through698500, continuing large allocation initialization and then16×64 data-reset loops on changing objects. Capped records show actual completed calls/returns through76.467846s; no persistent causal wait or narrow defect explaining absent UI established. Original InputOnly request remains identical in libxcb, sequence7/written6/error0; no later library/display write/flush/map, server child or originalUI. Diagnostic success; milestone2 highest; milestone3 open. No correction/retry, panel/input stage, bypass or forced display calls.

Worker alarm at76.023029s did not stop main. Independent hostSIGTERM/reap stopped exact guest at78.013007s; native finalJSON absent, console data labeled partial, finalPC/counters not invented. All runtime stopped11:04:56.796CDT. Verified12,841 root entries except freshcookie,26ELFs,bothUPDs,136,116 historical records and allthree exact dependency archive digests; scopedPIDs/endpoints clear,private helperremoved,sharedroot1777 directoryempty. Preserved mutable fixtures/empty directories, script/config diffs/hashes and previous docs. Replaced the single Current Handoff, addedE30/V45 and corrected operational priorities to measuring parent initialization work/completion. New private same-disk archive saves complete useful new evidence and updateddocs; external full verification/actual close reports avoid self-reference. Original firmware/library/runtime/history/archives unchanged; no restored execution or off-device backup claim.


## 2026-10-08 — offline correction after independent technical review

Direct user submitted the main-project correction prompt. Added experiments/offline-review-20261008-01 with new evidence-driven frozen-E30 verifier/negative controls, source-mode-versus-host report, controlled ARM32 copied clock tests, tracked fake descriptor/path controls and separate historical outcome layers. Recorded actual commands/exits, expected-negative failures and code/input identities. Broader continued initialization survives; exact495/75 counters are return-instruction checkpoint visits. Source sticky/setgid and ordinary mode losses are explicit. Held clock defects reproduce; gettimeofday retains its microsecond contract; only the offline proposed correction passes timespec/source/invalid-ID contracts. Broken endpoint comparison makes relevant fake controls fail. Null-duplex returned/exit0 and worker TimeoutError both remain preserved; no missing historical runner or native final was reconstructed.

Appended dated corrections to current navigation/state/ledger/extraction guidance, preserving every pre-edit byte in place and exact standalone copies. Added a draft for parent work/bound/actual caller0x50ab9c followed by bounded natural display observation, plus unresolved feature/architecture/build/proprietary interface/update/storage/recovery gates. The draft does not grant runtime authority. New before/after preservation checks cover historical paths/content with explicit private-content exclusions; archives/manifests, original firmware/source/output/runtime/console/supervision/checksum records and prior dated handoffs remain unchanged. No original app, emulator engine, display server, guest, vendor scripts, installation, firmware/hardware action, endpoint change or publication occurred. [Dated correction] `../experiments/offline-review-20261008-01/CURRENT_CORRECTION.md` (evidence not published); [check/command index] `../experiments/offline-review-20261008-01/README.md` (evidence not published).


## 2026-10-08 — self-contained parent-experiment prompt and takeover handoff

Created NEXT_SESSION_PROMPT-20261008-PARENT-INITIALIZATION.txt and experiments/parent-prompt-preparation-20261008-01 with the direct request, durable context, read-only peer review, exact pre-edit document copies, actual command/identity/readiness records and a saved prompt copy. The next chat can work without this conversation. Estimate is 45–75 minutes overall, with three-minute real progress updates, a 75-minute initial work ceiling, runtime cutoff minute 60, latest launch minute 56, one 180-second observation and 185-second owned-process closure. Unknown/failed/unexecuted results and overruns must be explicit; no fabricated success or automatic runtime extension/retry.

Static review found additional supervisor preparation required for group-wide independent deadline enforcement. Prompt distinguishes actual reset-callee return at0x50ab9c from whole-parent completion and permits unknown broader bounds with a validated local diagnostic. Appended latest navigation/state and E32 without rewriting prior bytes. Frozen E31 artifacts, historical runtime/archives and earlier prompt/checksum files remain unchanged. No original app, Qiling/Unicorn, Xvfb, guest, hardware or endpoint action occurred; the future supervisor/trace changes were not implemented here.


## October 8, 2026 — E33 parent attempt stopped by controller policy

Prepared static recursive-parent/caller mapping and a permanent read-only observer in a fresh complete copied fixture. Implemented independent process-group supervision and retained first-suite early-exit response failure before six corrected controls passed; ten observer and required four verifier negatives passed. One native attempt reached actual post-CreateWindow caller but the new blanket denied-operation stop rule interrupted the established guarded vfork path. Guest closure3.070427s; no retry/native final. Real certification fails missing chain. Preserved all200,051 compared prior paths, exact document beforebytes and new partial evidence.

See [standalone result] `../experiments/parent-initialization-20261008-141426/HANDOFF.md` (evidence not published), [unintegrated controlled proposal] `../experiments/parent-initialization-20261008-141426/proposal/offline-results.json` (evidence not published), [future-scope brief] `NEXT_SESSION_PROMPT-20261008-PARENT-STOP-POLICY.txt` (evidence not published) and [archive actual status] `../experiments/session-archive-20261008-parent-141426/README.md` (evidence not published). This diagnostic leaves the parent question explicitly incomplete.
