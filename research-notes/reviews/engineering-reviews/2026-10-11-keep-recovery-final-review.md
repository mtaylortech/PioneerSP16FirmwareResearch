<!-- source: engineering-reviews/2026-10-11-keep-recovery-final-review.md | scrubbed -->

# Keep recovery final focused review — October 11, 2026

Verbatim retained review from [Review/SP16_KEEP_RECOVERY_FINAL_REVIEW_INSTRUCTIONS-2026-10-11.txt] `Review/SP16_KEEP_RECOVERY_FINAL_REVIEW_INSTRUCTIONS-2026-10-11.txt` (evidence not published). The review checkpoint predates the correction; see [corrected oracle handoff] `../experiments/keep-recovery-acl-verifier-fix-20261011/HANDOFF.md` (evidence not published).

```text
SP16 KEEP RECOVERY — FINAL FOCUSED REVIEW INSTRUCTIONS
October 11, 2026, America/Chicago

Instructions to myself and the owner/coordinator reviewing this result

VERDICT
Accept the implemented primitive and saved evidence as support for the limited
disposable macOS/APFS host transaction and process-kill recovery result, with the
verifier caveat below. A narrow disposable host normalization workflow may rely
on it conditionally. No blocking transaction defect was identified within the
trusted, participating-writer, one-transaction-per-private-namespace contract.
This is not acceptance of integrated instrument Keep or the full adopted host
normalization profile. Do not describe the 84 passing cases as 84 repaired
successes: 38 are expected unresolved recovery refusals.

There is one confirmed, nonblocking verifier robustness defect (F1). Correct it
before using that oracle for a new qualification claim. There is no evidence
that the untested ACL error affected the existing saved run; do not retroactively
declare that run failed or imply that its oracle excludes every ACL API fault.

REVIEW AUTHORITY AND COMPLETED WORK
The designated file was absent and this file is the only review artifact written.
Read Review/AGENTS.md and the supplied
SP16_DIRECTOR_CURRENT_STATE_HANDOFF-2026-10-11.txt. Main project access was read-only.
No implementation, source import/execution, qualification rerun, tests/builds,
Git mutation, firmware/guest/hardware run, external message, additional chat,
subagent, preservation, archival or automatic continuation was performed. The
active member observation and closed core/skill scopes were not reopened.
Read-only utility scripts parsed saved JSON and hashed/inspected selected files;
they did not import or execute the reviewed package or reproduce its suite.

Review root, used below as R:
experiments/keep-recovery-qualification-20261011
All R-relative evidence references mean this exact absolute root.

F1 — CONFIRMED VERIFIER DEFECT; NO OBSERVED TRANSACTION FAILURE
Location:
experiments/keep-recovery-qualification-20261011/verify.py:47
The successful-ACL-pointer branch sets has_acl from acl_get_entry(...) == 0.
Every other return is consequently treated as no ACL, without checking errno.
A -1 result with an unexpected inspection error can be accepted as absence.
The primitive's separate adapter is stricter:
experiments/keep-recovery-qualification-20261011/platform_io.py:60
through line 67 accepts the documented local end-of-list EINVAL and otherwise
raises on a negative result. The final verifier snapshot has the same defect;
its hash equals the inspected verify.py hash.

Impact: a future oracle run can falsely report a mandatory attribute inspection
as successful. This is a confirmed source-code error-handling gap, not evidence
that an ACL-bearing candidate was committed or that such an error occurred here.
The saved unsupported_acl/acl-setup.json records successful ACL creation, and
unsupported_acl/transaction.result.json records acl_present=true and refusal
before staging. The five existing false-claim controls do not inject this API
failure. The primitive's fail-closed adapter and that actual refusal support
retaining the existing limited verdict with the explicit caveat.

Concrete proposed prompt for the main project, only if the owner selects repair:
"Preserve the completed Keep recovery package and all accepted/failed receipts.
In a versioned derivative, make the independent verifier fail closed when
acl_get_entry returns an unexpected result/error. Clear errno immediately before
that call; distinguish an actual first entry, the supported Darwin empty-list
result, and all other failures. Keep the verifier independent of platform_io,
transaction and qualify. Add focused controls for entry present, supported empty
ACL, NULL/ENOENT, NULL/unexpected error, and non-NULL/-1/unexpected error. The last
two must produce explicit verification failure, never acl_present=false. Save
new source pins and bounded verifier receipts under fresh names; retain the
existing final-verification.json and its exact source snapshot. No transaction
matrix rerun, firmware work or profile expansion is needed merely for this
verifier correction. Report the distinction between original qualification and
the corrected oracle." This review does not execute or dispatch that prompt.

EVIDENCE SUPPORTING ACCEPTANCE
1. Namespace and selection confinement. transaction.py:84-93 uses validated
basenames, O_NOFOLLOW, exclusive creation, regular/single-link/same-device checks.
transaction.py:217-238 opens ancestors relative to retained directory FDs without
following symlinks, checks directory identity/owner/mode0700, marker binding and
the pinned single-link mode0600 lock, then takes nonblocking flock. Selection is
bound to the caller's complete snapshot at lines 329-334 and rechecked by both
pathname and held FD at lines 368-369. Alias/root/lock mismatch controls are
declared in qualify.py:164-165 and materialized at lines 215-225. These checks
depend on trusted configuration and namespace administration; they do not close
a race with an arbitrary writer. cooperating_writer/contender.result.json
records REFUSED/errno35 while the first writer holds the pinned lock.

2. Backup, candidate and commit ordering. transaction.py:339-374 validates and
preserves the complete backup before checked sync/close, writes intent exclusively
and syncs its directory, validates full staged bytes and WAV geometry/opaque
chunks, preserves attributes, syncs/closes stage, writes ready bound to the
intent digest and stage identity, syncs precommit directory, rechecks source,
then directly renames. There is no target predelete, rollback or EXDEV fallback.
platform_io.py:80-97 refuses unsupported attributes and checks exact readback
after descriptor-based preservation. wav at transaction.py:23-48 compares exact
non-data chunk bytes including padding and refuses unsupported geometry/chunks.

3. Saved boundary identities agree with code. In run-2/crash_before_rename,
selected.wav remains inode64371905 with original SHA256
0894f97732367d2aa38dc87d7d5a03e2edee69da7bbcde9a5f65267e9cdfed22;
candidate.stage.wav is inode64371917 with candidate SHA256
1bc496e08d23dee23335328a5a1ccb739c4b31785856df069e04d4438b6ce8e4.
Its config/intent/ready and pre-crash snapshot bind those identities.
In crash_after_rename, target is ready-bound inode64371948 and stage is absent.
The paused-child snapshot, raw transaction.stdout.jsonl:60-62 and SIGKILL receipt
agree. Recovery uses distinct PIDs6813/6817 after killed transaction PID6807,
retries file/directory synchronization, and records later host refresh success.
Selected live hashes/inodes still match those saved states. Partial-backup and
complete-unsynced-intent boundaries correctly distinguish unresolved intent
construction from independently verified unchanged-original recovery.

4. Independent outcome dimensions. transaction.py:276-285 and 377-438 keep
commit, sync and refresh separate. sync_and_refresh_fail/transaction.result.json
and recovery-1.result.json retain commit=true, sync=uncertain, refresh=failed.
post_directory_close_closed remains committed durability uncertainty despite
the earlier successful fsync. Missing/wrong/failed refresh remains committed
refresh failure. refresh retries a matching retained acknowledgment's sync/close
instead of inferring historical sync from readable bytes (lines 300-312).
The held original FD is intentionally old; its original digest and reopened
candidate digest are distinct. The host refresh adapter proves host reopen only.

5. Close ownership and FD reuse. transaction.py:164-185 retires ownership before
one real close and does not blindly retry its number on error. Synthetic
still-owned errors leave ownership for one noninjected cleanup close. In
stage_close_closed/transaction.stdout.jsonl:47 the sentinel actually reuses
old FD6; the result records reused_fd_sentinels_intact=[true]. In
stage_close_owned/transaction.stdout.jsonl:46 and :53 the injected error calls
no OS close and cleanup later closes that still-owned FD once. These are adapter
controls, not manufactured real kernel/media close failures. Cleanup results
are separate evidence and must be consumed by a downstream caller.

6. Fresh recovery and conservative refusal. transaction.py:392-438 classifies
from strict duplicate-key-rejecting intent/ready records, pinned source and
backup identity/attributes/hash, reopened target and retained stage. It does not
read prior result files or operation logs to decide commit. Verified original
is left untouched; verified candidate is never rolled back. Malformed records,
foreign/corrupt/missing backup, conflicting ready and unrelated target refuse.
same_candidate_wrong_inode has the exact candidate bytes on inode64372424 while
retained-committed-candidate.wav remains ready-bound inode64372419; recovery
refuses. Selected recovery-1/recovery-2 inspection records agree for target,
backup, stage, intent, ready and acknowledgment identities/bytes/declared attrs.
No recovery rename appears in the inspected implementation or decisive logs.

7. Oracle and failures. verify.py does not import the transaction, runner or
attribute adapter. It independently decodes samples/chunks and reads actual
files, attributes and saved immediate inspections against separately declared
case expectations. final-verification.json records 84/84, no failures, and five
rejected false outcome/commit/attribute/digest/expected-target claims. This is
credible independent implementation evidence, subject to F1; independence does
not imply that every possible oracle defect has been excluded. Retain run-1:
its attempted special-mode fixture actually remained0640 and committed, so its
claimed refusal failed. run-2 uses actual sticky mode01640 and refuses. Retain
run-1-verification.json (72 failures), run-1-verification-2.json (one genuine
fixture-expectation failure), run-2-verification.json (partial-backup oracle
assumption failure), run-2-verification-2.json, prerequisite-failures.json and
host-test.tmp. No later pass erases these failures.

8. Pins and bounded cleanup. Current transaction/platform_io/qualify hashes
match their run-2/sources snapshots and closeout pins. Accepted SHA256 values:
transaction.py e74dd9b8885445d90bdef156b4f003b85183372ae0cb52ae4f7ae4d1c3057e13
platform_io.py 166fd2587e62a6846599fd9381f33574c39145015d234c5ef46f1cb24dedae5f
qualify.py a30da20aa1d5f6cc1ae8808cf6b22021a8a1da0df877cad4194ad6df7f72cbd6
verify.py 9ceba753de152a62e04aae67f80c782e5ab94765f159ff2885edd163dde7318c
verify_owned.py afdf4803095dd63f834caa10d3a12847351730a80fc85935f508b364b47bf964
Final verifier snapshot/launch/receipt/report agree on its accepted hash. The
run-2 launch pins an earlier verifier08943422...; that is preserved history,
not a transaction source mismatch. run-2.receipt.json records the independently
bounded300s suite, elapsed10.02s, return0, reaped and no residual group. The final
20s-bound oracle records elapsed0.470s, return0, reaped and no residual group.
Decisive child receipts record actual signal9, finite bounds, reaping and PID
absence; recovery commands use fresh processes. This review relies on recorded
cleanup and performs no fresh process census or observation polling.

CONDITIONAL DOWNSTREAM INSTRUCTIONS
If the owner selects a disposable host integration, prepare a fresh derivative
workflow and retain this primitive as a scoped dependency. Require all of these:
- Private pinned mode0700 namespace, trusted stored root/lock/transaction/selected
  identities, one transaction per namespace, same-device single-link regular
  files, supported attributes, and all writers honoring the same pinned lock.
- Bind the supplied candidate to the exact processed preview approved for Keep.
  The primitive accepts supplied PCM; it does not verify normalization math or
  prove that the user previewed that candidate. Do not use its host ack as proof
  of audible preview, waveform reload or firmware holder freshness.
- Restrict inputs to the bounded PCM16 contract and expose unsupported inputs as
  refusals. Keep normalization numerical validation and adopted input-profile
  validation separate. This code's rate validator accepts8000-192000Hz; the
  workflow must enforce the adopted44.1/48/96kHz profile itself.
- Read every outcome dimension, current identity and cleanup receipt. Preserve
  committed uncertainty and refresh failure, and retain unresolved state for
  explicit review. Do not retry transact in a populated namespace, delete its
  records, restore the backup, or infer success from readable candidate bytes.
  After a missing transaction result, use fresh-process recovery under the same
  independently retained configuration and lock. A later sync acknowledgment
  does not supply the missing historical acknowledgment.
- Correct F1 before using a new oracle run to claim qualification. Qualification
  of new input sizes/geometries needs focused new evidence; the current saved
  successful fixture is528 bytes,96 stereo frames, PCM16/48kHz/mode0640. Static
  validator support for mono and<=1MiB is not an empirical matrix of that domain.

Concrete proposed integration prompt, only if selected by the owner:
"Build the disposable host Normalize -> processed preview -> Keep/Discard
workflow in a fresh derivative using the preserved Keep recovery primitive only
within its pinned private namespace and supported PCM16/attribute contract.
Bind selected-source identity and approved-preview candidate digest to each
transaction. Refuse unsupported inputs explicitly; preserve all commit/sync/
refresh/cleanup dimensions and retained recovery evidence. Keep existing
qualified core math dependencies separate and unchanged. Correct the independent
ACL oracle error handling as specified in F1 before new qualification claims.
Use only focused integration/input controls selected for this derivative; keep
original evidence and failures immutable. Do not claim PCM24/50MB, arbitrary
writers, power-loss persistence or instrument ownership/reload qualification.
Report actual accepted inputs and remaining prerequisites." This review grants
no execution authority and sends no prompt.

EXCLUSIONS, CONFIDENCE LIMITS AND PRESERVATION PREREQUISITES
Do not generalize SIGKILL with a live filesystem into disk-write loss/reordering,
power failure, physical-media persistence or target storage. Host fsync/
F_FULLFSYNC/directory acceptance is recorded host-call acknowledgment only.
Advisory flock excludes participating writers only. Original file holders remain
old after rename; actual producer settlement, holder release, model/adjunct
preservation and fresh firmware PCM/player/waveform acknowledgment are separate
unqualified obligations. PCM24,50,000,000-byte files, the full normalization
profile, all permitted ordinary modes/ownership combinations, mono/size/rate
boundary coverage, disk-full/media faults, recovery-process kill boundaries and
arbitrary namespace administration were not qualified by the inspected cases.
No repeated Keep in a reused namespace is supported. These are limits, not
confirmed failures in the successful fixture regime.

The review read all implementation source and focused decisive evidence; it did
not independently re-read every passing case/artifact or run a second oracle.
External reference pages in SOURCES.md were not re-fetched. Exact XNU platform
semantics outside this ordinary Darwin FD scope are not newly qualified here.
No preservation or archival was performed; the package remains uncommitted.

Before relying on a preserved dependency, have the authorized main-project
writer preserve the complete OWNED_FILES.txt scope, exact sources, fixtures,
configs, raw logs, retained transaction materials, launch/cleanup receipts,
final verifier snapshot and all failed attempts. Record real symlink/hardlink
relationships and platform attributes; Git content alone does not restore
inodes, mtimes, ACLs or xattrs. Preserve original saved identity receipts as
historical evidence, never use those stale inode/root pins as a new live config
after relocation. Identify local Darwin/Python/APFS dependencies and link this
review without editing its owned file. Do not assume the earlier focused backup
contains these later outputs. Preservation and archive remain owner-selected
next work, not completed work or automatic continuations of this review.

STOP
The focused verdict is supported; no new investigation is selected. Stop for
owner/coordinator review. Do not message another chat or inspect the changing
member-observation outputs.
```
