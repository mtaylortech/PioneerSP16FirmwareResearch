<!-- source: ../PioneerSP16Review/INDEPENDENT_TECHNICAL_REVIEW-2026-10-08.md | scrubbed -->

# Pioneer SP16 independent technical review and review instructions

Review date: **October 8, 2026, America/Chicago**. Target: ``. Reviewer artifacts: `Review`. This assessment concerns the held 1.50 and 1.60 updates, the retained extraction and emulation records, and readiness for the next milestone. It is also the instruction record for follow-up review. The user's read-only boundary governs the main project. No repair, firmware execution, live emulation, hardware action, source build, publication, or message to another chat was performed.

## A What can be relied on and milestone readiness

**The decoding and readable-file extraction foundation is supported. The original application has recorded, narrowly scoped startup progress. A working virtual instrument, replacement OS, and safe modified-firmware deployment are not established.**

Independent current checks reproduce both decoded ISOs from all ciphertext sectors, verify the ISO file/link contents, outer archive bytes, all six SquashFS regular-file streams, and the recorded nested expansions. They also expose source permission loss in the host trees. Those trees are useful for reading and analysis; they are not faithful boot-filesystem or repacking inputs merely because their byte audits pass.

The latest saved startup evidence supports return from original XCreateWindow into continued allocation/reset initialization, an unchanged queued 36-byte request, zero observed server children, and black server-root captures. Some “completed function” totals overstate what before-instruction return hooks directly measure. This does not negate the observed progression.

| Stage | Assessment at this review |
|---|---|
| Recognition and interpretation of the two held UPD containers | Supported for these exact bytes and versions; acquisition authenticity unresolved |
| Correct readable-file extraction | Supported for checked file bytes/paths/targets; source metadata fidelity is limited |
| Unchanged repacking | Unresolved; no repacker/repacked image acceptance demonstrated |
| Valid modified packaging and updater acceptance | Unresolved; CRC/decryption do not establish acceptance or authenticity |
| Executable identification | Supported: original 1.60 app is ELF32 little-endian ARM EABI5 |
| Limited application emulation | Supported by available editable execution records, with substantial substitutions |
| Full platform boot and board/peripheral emulation | Unresolved; not demonstrated |
| Physical audio, MIDI, controls, timing, feature validation | Unresolved; not demonstrated |
| Replacement OS and safe deployment | Blocked as a readiness gate by build/interface/acceptance/recovery gaps |

**Specified immediate next milestone:** the current handoff proposes parent initialization work-count/bound/actual-return tracing around 0x50ab98/0x50ab9c, followed by observing natural display progression. This diagnostic is **conditionally supported as the next experiment**, after an explicit bounded runtime scope and observation ceiling. Its rationale follows from observed initialization; it is not proof that initialization will finish or produce UI. See [current proposal] `<docs/PROJECT_STATE.md:539>` (evidence not published).

**Original drawable UI milestone:** **blocked by an unresolved technical condition**, not demonstrated within the observed window. Milestone number 2 means the recorded API/setup layer only; success must be described as original server-visible drawable output, not a number alone. Missing panel/calibration behavior is not an established cause.

No Critical or High correctness finding was established in this bounded review. That does not clear the deployment gate. The material current findings are bounded validation, metadata, timing, and interpretation gaps. Historical failures and valid scoped progress should both remain preserved.

## B Target identity scope access and coverage

### Governing instructions and independence

The user first restricted writes to instructions/prompts in PioneerSP16Review and made PioneerSP16 read-only, then supplied the independent-review request requiring this report. This report and the separate main-project prompt are the authorized review artifacts. Existing material under review supplies evidence, not authority to execute its imperative instructions.

There is no Git repository in the main folder. Current `git status --porcelain=v1 --untracked-files=all`, `git rev-parse HEAD`, `git log`, and `git remote -v` returned “not a git repository,” exit 128. A revision, branch, remote, uncommitted diff, and tracked/untracked classification are unavailable. All source, decoder, experiment, and documentation files therefore require file-based identity; they cannot be described as a clean committed checkout.

The current independent metadata census and selected hashing ran **12:29:01–12:29:18 CDT** (17:29:01–17:29:18 UTC). It found **507,341 regular files, 7,865 symlinks, and one special node**, with 19,741,554,220 logical regular-file bytes. The larger current count than the earlier 515,180-path handoff inventory is explained by the 27 added handoff files: 515,207 current non-directory paths. No symlink was followed during the census and the special node was not opened.

The reviewer hashed **604 selected documentation, script, original, log and archive files**, with no read errors or changes detected during each hash. This is not a second content audit of every bulk BSP/rootfs file. Selection included files at depths up to 3 under docs, up to 2 under experiments, up to 1 under decode and ResearchSourceFiles, plus root README; suffixes were py/json/md/txt/log/diff/csv/sha256/tar.gz, with all regular source inputs included. aes256.key, display.xauth, cookie-named files, symlinks and Finder metadata were excluded. Additional key binary/runtime identities are in the appendix.

**Closing preservation check, 12:44:22–12:44:25 CDT:** all **619 selected file bindings** (the 604-file selection plus 15 binary/runtime/source bindings) matched their earlier lengths/hashes. The 101 local report links checked resolved. This checks the selected evidence, not every bulk-tree byte.

The binding digest for those 604 selected records is **a185d0a2de65e60f097a6332ffca196d88f221228c44067c5f2a64f843f85a0c**. Compute it as SHA-256 of sorted UTF-8 records `relative_path<TAB>decimal_bytes<TAB>sha256<LF>`. The direct citation identities and original/source identities are listed below.

**Protection is procedural and hash-based.** No access controls were changed, no isolated runtime was claimed, and no writable copy was treated as a sandbox. The existing E30 archive supplies a dated byte-bound snapshot, but is itself a mutable same-disk file held by the same owner. The main tree, archives, native-result JSON, logs, copied transcripts, and author summaries can all be edited by the development agent/project owner. Agreement and hashes support the reviewed records; they do not authenticate historical execution or certify the presence or absence of dishonesty.

Older prompts' one-chat/no-subagent constraints belonged to their closed runtime scopes. Current review used separate read-only agent passes for container evidence, runtime evidence, and consistency. Their agreement is not independent confirmation by itself; the evidence below identifies independent calculations and shared tools. No reviewed prompt grants standing replay permission. No binding conflict prevented the unaffected read-only checks.

### Artifact classes and origins

- **Held originals:** ResearchSourceFiles UPDs, PDFs, source/codec bundles and numbered parts. Original download ZIPs, firmware acquisition URLs/receipts and publisher hashes were not found. Their byte identities are supported; publisher provenance is unresolved.
- **Derived source:** three assembled tar.gz files and extracted BSP trees. Ordered parts match the assembled files byte for byte. That verifies assembly, not the completeness/authenticity of the source release.
- **Derived firmware:** decoded.iso, ISO trees, separate payload trees, nested trees and metadata/manifests under decode/output/image1 and image2.
- **Analysis/execution records:** decoder reports, disassembly, console PROBE records, native results, supervisor records, editable summaries, histories and author handoff.
- **Patches/substitutions:** host harness/fixture changes and portable Xvfb changes. No reviewed modified firmware UPD or replacement-OS build was established.

Exact input identities:

| Input | Version and lineage | Bytes | SHA-256 |
|---|---|---:|---|
| TORAIZSP16VER150.UPD | Held original; internal 1.50; app Rev.6284 | 99,493,908 | 11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a |
| TORAIZSP16.UPD | Held original; internal 1.60; app Rev.6550 | 99,495,956 | ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4 |
| image1 decoded.iso | Derived 1.50 ISO | 99,493,888 | 534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b |
| image2 decoded.iso | Derived 1.60 ISO | 99,495,936 | 6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb |
| image2 EP085_Main_R | Derived original app | 12,000,396 | 3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464 |

Source versions include Pioneer platform material, Freescale L3.0.35/4.1.0/130816 and L3.0.101/4.1.1/141016, U-Boot 2009.08 and BusyBox 1.20.2. Both held kernel headers name Linux-3.0.101-2790-gc248ed7; their hashes differ. Broad version correspondence does not identify a reproducible exact release build. Proprietary sampler application source was not established in the supplied release.

Available origin references identify documents, not acquisition of the held firmware: the local service PDF metadata points to [ManualsLib's TSP-16 manual](https://www.manualslib.com/manual/2050267/Pioneer-Dj-Tsp-16.html); the saved official update guide footer points to [AlphaTheta article 4414382699929](https://support.alphatheta.com/en-US/articles/4414382699929). These URLs were read from local PDFs and are not receipts.

New primary-source checks retrieved [NXP IMX6DQCEC Rev.6, November 2018](https://www.nxp.com/docs/en/data-sheet/IMX6DQCEC.pdf), pp. 1, 3, and indexed text from [Samsung K4B4G1646D Rev.1.03, August 2014](https://download.semiconductor.samsung.com/resources/data-sheet/DS_K4B4G1646D-BC-I_Rev103-0.pdf), ordering table. NXP explicitly lists MCIMX6Q5EYM10AD as i.MX 6Quad, 1 GHz speed grade. Samsung's exact BCMA row identifies a 4-Gbit 256M×16 device, so two manual-listed chips imply **1 GiB nominal installed capacity**. This is a documented-part inference; active clocks, actual unit population, usable RAM and performance remain unmeasured. Direct Samsung PDF open failed twice; its primary-domain indexed table was available, so visual/table/full-PDF verification remains a coverage limitation. No external firmware was fetched.

### Inventory and actual coverage

| Area | Independent coverage | Remaining limits |
|---|---|---|
| Instructions/history | User request, root/decoder/canonical docs, dated prompts, retained authorization/history excerpts and handoff compared | Selected history exports are editable retrieval records; no complete platform transcript or intermediate approval history acquired |
| UPD/ISO | Entire ciphertext sector comparison, trailer CRCs, independent ISO/Rock Ridge traversal | Shared CommonCrypto primitive with supplied decoder; no authenticity or updater acceptance |
| Outer and nested payloads | Ten gzip/tar streams, six SFS listings/content streams, 386 recorded nested expansions per release | Python tar/gzip and unsquashfs are shared format libraries; malformed-parser correctness is not independently proven |
| Application/control flow | ELF header/segments, selected original instruction bytes/BL targets, E25/E30 raw PROBE events, trees and raw XWD pixels | No application-wide feature map/decompilation, complete CFG, dynamic rerun, 1.50 runtime comparison or full memory trace |
| Validation/scripts | Decoder mutation paths, E30 summarizer/validator, return hooks, display guard tests, emulator clock/thread code | No exhaustive audit of all vendor tools or every installed emulator syscall |
| Preservation | 26 handoff-manifest files; E30 archive streamed against 34,185 external records | Confidential member contents excluded; other archives only identities/dependencies reviewed; no restore or off-device backup |
| Hardware/manuals | Relevant service/update/release-history pages extracted; primary part datasheets checked as described | No unit access, device passthrough, physical measurements, flash/recovery work |

## C Findings ordered by impact

### F01 Medium Summary predicates can certify missing or wrongly attributed initialization evidence

**Issue:** E30 summarization does not require the claimed allocation/reset checkpoint chain, consistent main thread, phase order or observed caller returns. Some server/capture collections can also be empty.

**Exact evidence:** [summarize_evidence.py:27–38] `<experiments/emulation-startup-20261008-105916/summarize_evidence.py:27>` (evidence not published) gathers any checkpoint names; line 38 hardcodes diagnostic_success=True and the full control-flow classification. [validate_session.py:46–49] `<experiments/emulation-startup-20261008-105916/validate_session.py:46>` (evidence not published) trusts prior status fields and the summary's success/milestone values. Register counts at lines 21–23 test documentation structure.

**Current bounded counterexample:** the inspected, I/O-free predicates and dictionary expression at source lines 27–36 and 38 were executed in memory with one actual begin event, one valid saved buffer snapshot, one unrelated checkpoint assigned to another thread, and the alarm event; server observations/captures were empty. They returned diagnostic_success=true and “VERIFIED continued main-thread data initialization.” Required allocation/reset evidence was absent. Full script main, capture conversion and writes were not run.

**Affected claims:** C07, C08, C10 and automated certification generally. **Consequence:** a later failed/incomplete dataset can get a positive result. The real saved run still has independently reviewed progression; this is not falsification of that run.

**Smallest correction:** in new main-project validation code, require version/input identity, nonempty required observations, exact checkpoint predicates, same runtime main thread, appropriate order, and explicit post-return proof for completed-call wording. Missing or contradictory evidence must fail. Keep historical output files unchanged. Apply the omission/wrong-thread/empty-observation control above as an expected failure.

### F02 Medium Readable extraction loses source mode bits while host-relative re-extraction passes

**Issue:** host trees do not preserve all original permissions, including Linux sticky/setgid directory bits. A second extraction on the same host can reproduce the loss and pass the audit.

**Exact evidence:** [tar directory extraction] `<decode/decode.py:244>` (evidence not published) mkdirs directories without restoring m.mode; file chmod at line 256 keeps only ordinary bits and forces owner-read. [tar audit] `<decode/decode.py:340>` (evidence not published) checks directory type, not mode. [SquashFS audit] `<decode/decode.py:464>` (evidence not published) compares a second host extraction to the saved host inventory. [status wording] `<decode/STATUS.md:18>` (evidence not published) reports modes checked against that extraction. [canonical limitations] `<docs/PROJECT_STATE.md:178>` (evidence not published) names ownership/timestamps/xattrs but omits permission-bit loss.

| Exact source and member | Original | Host tree | Source locator |
|---|---:|---:|---|
| image2 iso/images/rootfs4.tar.gz, ./tmp | 01777 | 0755 | Decompressed tar header 1,201,664; [metadata:970] `<decode/output/image2/rootfs4.tar.gz.metadata.json:970>` (evidence not published) |
| Same archive, ./var/tmp | 0777 | 0755 | Header 4,608; [metadata:85] `<decode/output/image2/rootfs4.tar.gz.metadata.json:85>` (evidence not published) |
| Same archive, ./var/ftp/pub | 02777 | 0755 | Header 6,656; [metadata:121] `<decode/output/image2/rootfs4.tar.gz.metadata.json:121>` (evidence not published) |
| Both releases bin.sfs, bootmod | 0775 | 0755 | Raw source listing; image2 [host manifest:283] `<decode/output/image2/payload-manifest.json:283>` (evidence not published) |
| Both releases share.sfs, fonts/bdf/Pioneer_ISO8859_18.bdf | 0664 | 0644 | Raw source listing; image2 [host manifest:56386] `<decode/output/image2/payload-manifest.json:56386>` (evidence not published) |

There are 11 ordinary SFS-file mode differences per release: six bin files and five BDF fonts. Tar directory mode differences are image1 rootfs2=10/rootfs3=13/rootfs4=8; image2 rootfs2=13/rootfs4=16. macOS symlink mode differences are separately host semantics; link targets match. Source offsets above refer to decompressed tar headers, not compressed-file offsets.

**Affected claim:** C03. **Consequence:** reading/file-byte claims remain valid, but generating a Linux root or repack from host stat metadata can serialize wrong permissions. Missing UI causality was not established.

**Smallest correction:** add a new source-mode-versus-host report and qualification. For future packaging, use original container metadata rather than host modes. Do not regenerate the historical baseline or retroactively claim a bootable root.

### F03 Medium Installed guest clock_gettime has wrong units and ignores clock identity

**Issue:** the installed Qiling handler uses host wall time for all clock IDs and writes microseconds into a timespec nanosecond field.

**Exact evidence:** [Qiling helper:28–35] `<experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py:28>` (evidence not published) uses datetime.now().timestamp() and multiplies the fraction by 1e6. [clock_gettime:77–81] `<experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py:77>` (evidence not published) ignores clock_id. The latest [console:1272] `<experiments/emulation-startup-20261008-105916/logs/startup-natural-01-console.log:1272>` (evidence not published) calls clock_gettime(clock_id=1). [Linux clock_gettime documentation](https://man7.org/linux/man-pages/man3/clock_gettime.3.html) specifies nanoseconds and CLOCK_MONOTONIC's distinct monotonic semantics.

**Independent arithmetic:** at deliberately chosen wall timestamp 1700000000.5, inspected code gives ARM32 little-endian bytes 00f1536520a10700, fields (1700000000,500000). Correct REALTIME fields are (1700000000,500000000), bytes 00f153650065cd1d. The fractional component is 1000× too small for timespec. This calculation is not a historical returned value. The shared gettimeofday helper's microsecond scaling is appropriate for timeval; that interface does not have the same units defect.

**Affected claims:** C06, C09 and any guest-time-dependent causality. **Consequence:** faithful guest timing is not established; unexplained waits/timing must not be attributed to hardware. Host monotonic elapsed times, original instruction checkpoints and queued bytes remain usable. The defect's role in missing UI is unresolved.

**Smallest check:** new offline controlled-provider tests for REALTIME, MONOTONIC, fractional samples, second transitions and invalid IDs; inspect serialized ARM fields/status independently. Preserve installed runtime and baseline. Any later correction belongs in a separately scoped copied harness with a one-condition comparison.

### F04 Medium Return-instruction visits are described as completed functions

**Issue:** the handoff reports at least 75 completed reset functions, but the exact count is a hook visit before the return instruction executes.

**Exact evidence:** [Current Handoff:533] `<docs/PROJECT_STATE.md:533>` (evidence not published) reports “at least75 completed functions by76.467846s.” [startup_trace.py:48–60] `<experiments/emulation-startup-20261008-105916/startup_trace.py:48>` (evidence not published) increments/emits within the address hook. [original disassembly:78] `<experiments/emulation-startup-20261008-105916/deadline_caller-disassembly.txt:78>` (evidence not published) has pop {r4,r5,r6,r7,r8,pc} at 0x3546d4. [console:22147] `<experiments/emulation-startup-20261008-105916/logs/startup-natural-01-console.log:22147>` (evidence not published) is the 75th visit. No subsequent 75th caller-return observation is retained. The 0x353d04 allocation checkpoint is similarly a return-instruction address.

**Affected claim:** precise numeric completion clause in C08; the generalized continued-initialization claim remains supported. Changing-object later invocations corroborate earlier returns, and loop-completion visits independently show useful progress.

**Consequence:** the reported count has stronger semantics than its measurement; it cannot establish parent completion or a fully completed final call.

**Smallest correction:** append a dated clarification of “return-instruction checkpoint visits”; keep the old trace/counts. Observe actual caller/post-return at 0x50ab9c in any future scoped diagnostic and distinguish it from reaching the callee's return instruction.

### F05 Low Malformed-path negative tests fail an earlier ownership condition

**Issue:** path controls do not isolate the endpoint guard.

**Exact evidence:** [fake descriptor table] `<experiments/emulation-startup-20261008-105916/check_display_guards.py:22>` (evidence not published) starts empty; [path tests:28–30] `<experiments/emulation-startup-20261008-105916/check_display_guards.py:28>` (evidence not published) pass fd3 without an owned socket. [connect guard:99] `<experiments/emulation-startup-20261008-105916/local_display.py:99>` (evidence not published) rejects an unowned fd first. Removing the path comparison would not cause these cases to fail. Domain and descriptor-reuse controls remain meaningful. This is a static test-logic finding; the supplied test was not executed.

**Affected claim:** C10's negative-control coverage. **Consequence:** “passed path negatives” does not establish path-specific protection. No observed endpoint escape was found.

**Smallest correction:** track the same fake socket in fixture.descriptors[3] and guest fd3, then require malformed family/path/abstract-name cases to avoid its connect method; add an exact allowed-path positive mock. Keep fake fixtures labeled as test inputs.

### F06 Medium historical gap Earlier return/exit-zero result coexists with worker failure

**Issue:** null-duplex's success-like process result did not represent clean guest termination.

**Exact evidence:** [native result:15–18] `<experiments/emulation-20261008/null-duplex-result.json:15>` (evidence not published) says returned/exit_code=0. [console:7128–7145] `<experiments/emulation-20261008/logs/null-duplex-console.log:7128>` (evidence not published) preserves worker TimeoutError before that result. Installed [thread manager] `<experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/thread.py:618>` (evidence not published) joins main_thread with raise_error=True, while workers can terminate separately. The exact intermediate runner is not bound by the current probe.py: its historical traceback line differs from the retained current implementation.

**Affected claim:** clean-stop interpretation of C06, plus historical run-code binding. **Status:** present [runbook correction] `<experiments/emulation-20261008/README.md:41>` (evidence not published) already preserves and corrects the interpretation; this is not an unresolved claim of current clean shutdown.

**Consequence/correction:** preserve both old records. Separate host process status, worker exceptions, ql.run outcome and clean guest shutdown. Keep independent host supervision for new runtime work. No missing historical runner/log may be reconstructed.

## D Claim ledger contradictions and reproduction

### Claim ledger

“Historical execution supported” below means supported by the available editable records, not authenticated externally. “Independent” means a separately written calculation/comparison; shared format/crypto libraries are explicitly qualified. No native application/board rerun occurred.

| ID and precise version-qualified claim | Supporting and challenging evidence; type | Assessment and verification | Historical execution; dependencies; consequence and smallest check |
|---|---|---|---|
| C01 Held UPDs are the local 1.50/1.60 inputs identified above | Input bytes/trailers and decoded release labels; static. Publisher receipts/ZIPs absent | Supported local identity by fresh SHA/length/trailer calculations R01; origin unresolved | Acquisition unverifiable. Depends on retained originals; wrong origin changes target applicability. Obtain an independent official copy/receipt without replacing originals |
| C02 Sector AES model reconstructs both held ISOs | All 194,324/194,328 sector comparisons; supplied cryptoloop source CBC/LE32 IV; static/independent calculation | Supported within these versions R01. Separate sector implementation, shared CommonCrypto primitive | Earlier full decoder command chronology partly unverifiable; new check not proof of old run. Depends on held key/model; next challenge is another crypto primitive/known-answer sector, without printing key |
| C03 Supported ISO/archive file bytes and targets were extracted correctly | 113 ISO records/release, ten tar streams, six SFS streams, 386 nested expansions/release; static. Source-mode differences F02 | Supported readable bytes/targets R02–R03; contradicted if expanded to faithful source metadata | Generated reports/artifacts support extraction results; exact original invocation/history partly unverifiable. Depends on shared parsers. Wrong metadata affects repack/boot; check source modes explicitly |
| C04 Trailer/uImage checksums establish local consistency | Trailer IEEE CRC32 f1679304/6f3bb5a2; uImage header/data CRCs; check_sig disassembly | Supported R01/R04; CRC negative rejects in-memory bit flip. Does not establish cryptographic signature or full acceptance | Checker execution not rerun, historical hardware acceptance not applicable. Depends on checksum model; inspect later updater acceptance before packaging |
| C05 Original image2 app is ELF32 LE ARM EABI5 ET_EXEC | Direct header/segments, e_machine40, e_flags0x5000002, entry0xb5cc8; static | Supported R06; app identity independently matches | Not applicable to execution. ABI loader/platform still substituted. Wrong mapping invalidates hooks; verify PT_LOAD file mapping and loaded bytes |
| C06 E25 corrected-TLS run records synthetic duplex API startup and 17 threads | Raw 925 PROBE records/native result; sampled opens returning 0 and transfers of 64 frames. Null-duplex worker failure F06; synthetic I/O and capped returns | Supported recorded API samples/counters; hardware audio, every transfer success and clean shutdown unresolved R07 | Supported by available records; exact earlier intermediate runner binding partly unverifiable. Depends on null PCM/TLS/fixtures; preserve worker errors and final host status |
| C07 E30 records original XOpenDisplay/XCreateWindow returning | Raw console entry/main and return progression; original ELF words; recorded execution/static | Supported recorded API layer R06–R08; F01 prevents treating summary boolean as independent proof | Supported by available records; no live rerun. Depends on authenticated local transport/loader/TLS. Actual server acceptance remains unresolved; observe matching server resource naturally |
| C08 E30 continues initialization, with queued request unchanged | 1,129 parsed PROBE records; changing objects; 66 snapshots; 16×64 reset loop instructions; recorded execution/static | Supported progression R08. Exact “75 completed” clause overstated F04; total parent bound/completion unresolved | Supported by available records; native final absent. Depends on observer semantics/guest environment. Next check is actual parent work bound and caller return |
| C09 Permanent hardware wait explains missing UI, or real completion time is established | No primary causal wait or completion evidence; clock defect F03, trace overhead, synthetic readiness challenge | Unresolved; not promoted to success. Host duration only R08 | Not applicable to unexecuted causal proposal. Wrong inference drives broad bypasses. Use counted parent completion/one-condition checks before attributing hardware |
| C10 Display guard tests certify full endpoint containment | Fake tests and implemented owns/path/domain checks; static/simulation; F05 | Supported selected negative branches, unresolved full native containment/path-test coverage | Saved fake-test report exists; tests not independently rerun. Depends on descriptor ownership. Use tracked descriptor negative and positive mock controls |
| C11 Original drawable UI exists | All 17 retained root-tree samples0; two all-zero raw XWD pixel payloads; recorded execution/static | Unresolved eventual UI; contradicted if asserted for this bounded observation R08 | Available records support no observed UI within window; cannot prove permanent absence. Depends on natural flush/map/draw; capture matching original drawable content |
| C12 E30 stopped around78s despite worker alarm and has no native final JSON | Raw alarm/checkpoints and supervision exit−15/78.013007; recorded execution | Supported records R08; final native counters/PC unknown | Supported by available records; saved process-state check not current live host audit. Depends on supervisor; later test authoritative process-tree stop in a new scope |
| C13 Source assemblies are exact concatenations; sources reproduce shipped software | Three complete byte comparisons R05; kernel/source versions/config/build scripts; static | Concatenations supported; exact shipped build correspondence unresolved | Earlier concatenation commands unverifiable; source extractor recovered copies/history do not bind every revision. Wrong build correspondence affects OS work; compare shipped config/initramfs/patch/toolchain chain |
| C14 Manual-listed CPU/RAM parts have documented rated properties | Local service PDF p49; NXP exact part table; Samsung primary indexed row; documentation/inference | Supported 1 GHz speed grade and inferred1 GiB nominal installed RAM; active unit/usable RAM/performance unresolved R10 | Historical datasheet research not authenticated by saved assertions; new verification is current. Wrong performance inference affects feature budgets; obtain active/unit/workload measurements separately |
| C15 E30 archive preserves its listed members and is a tested portable backup | Current archive SHA and34,185 member comparison; external dependencies; static | Member/metadata preservation supported R09 excluding3 private contents; restore/off-device/portability unresolved | Archive creation supported by records; restored execution not performed. Depends on base macOS/Python/prior archives; static restore check is smallest next preservation check |
| C16 Modified UPD or replacement OS is ready for hardware/feature validation | Original updater chain/write scripts; no modified package, accepted repack, exact build, interface or recovery evidence | Unresolved capability; readiness blocked, no deployment recommendation | Not applicable: no such execution shown. Depends on selected feature, acceptance, storage/recovery. Establish a concrete architecture/gate plan before implementation/writes |

Binary/source locators for C02/C04: [supplied cryptoloop.c:69,147–160] `<extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/linux-3.0.101/drivers/block/cryptoloop.c:69>` (evidence not published); [retained check_sig] `<extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/check_sig>` (evidence not published) VA0x85d8 subtracts20, VA0x85ec–0x85f4 checks marker, VA0x8608–0x8614 calculates/compares CRC. [decrypt_update.sh:35,39,43–46] `<extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/decrypt_update.sh:35>` (evidence not published) sets up/mounts the encrypted loop, changes libraries, then runs ./update. These are bounded static observations; the later updater's complete acceptance/write logic was not traced.

### Contradiction and supersession register

| ID | Both passages/versions/scopes | Resolution and consequence |
|---|---|---|
| K01 | Current Handoff [line533] `<docs/PROJECT_STATE.md:533>` (evidence not published):75 completed; original disassembly return at [line78] `<experiments/emulation-startup-20261008-105916/deadline_caller-disassembly.txt:78>` (evidence not published) and raw before-instruction checkpoint | Semantic overstatement F04; append clarification. Continued initialization remains valid |
| K02 | null-duplex result returned/exit0 versus worker TimeoutError in its same raw console; current runbook line41 corrects it | Different outcome layers, previously overinterpreted; corrected current interpretation F06. Preserve historical gap |
| K03 | Original [display request:57–65] `<experiments/emulation-display-20261008-004011/archive-audit/authorized-session-request.txt:57>` (evidence not published) defines API/display/output steps; later [invoked prompt:13–25] `<docs/NEXT_SESSION_PROMPT-20261008-105321.txt:13>` (evidence not published) explicitly requires drawable original output | Criterion clarification with numbering drift, not a successful UI claim. Use full words; neither output criterion was met |
| K04 | Historical decode no-execution/feature-first text; [historical marker] `<decode/PROCESS.md:3>` (evidence not published) and [explicit supersession] `<docs/PROJECT_STATE.md:388>` (evidence not published) distinguish later bounded emulator priorities | Explicit scope change, not current conflict. Neither old nor later closed windows authorize replay now |
| K05 | Earlier comparison answer cites CPU/RAM datasheets in [retained selected history] `<docs/handoffs/2026-10-08-independent-review/HISTORY_SOURCES.json>` (evidence not published); canonical [no datasheet reviewed] `<docs/EVIDENCE_LEDGER.md:48>` (evidence not published) says none reviewed | Documentary provenance inconsistency; cannot conclude actual old browsing occurred. New primary verification supports rated part facts; no 25× measured performance claim |
| K06 | Source BSP setup names3.0.35 while shipped kernel names3.0.101; held source collection contains both | Different BSP stages/versions with unresolved integration chain; not proof of matched build or deceit |
| K07 | STATUS mode-check sentence versus raw source/host modes and omission from PROJECT_STATE178 | Host-relative test is true within its narrow meaning; source-mode equivalence is not. Add explicit limitation F02 |
| K08 | Earlier unknown extractor location versus handoff's recovered copies/history | New discovery improves availability; current bytes do not authenticate every historical revision. Preserve old gap and date recovery |

No circular summary citation was accepted as primary proof. For example, success fields from session-summary/validation were checked against raw records and original bytes. History retrieval records, copied transcripts and author-maintained notes are distinguishable from native console/result records but remain locally editable.

### Reproduction results and controls

All below are **current checks on October 8**; their outcomes were obtained during this review. None proves a missing earlier run occurred. Own inline review calculations wrote no output/code files in the main tree. Process-return status for successful review Python commands was0 unless otherwise noted.

| ID | Input through method/tool to observed result | What this establishes and limits |
|---|---|---|
| R01 | Read UPD bytes/key privately; normalize key as bundled losetup -N does (first LF/NUL, at most 31 raw bytes, zero-pad to 32 bytes; no hex/hash conversion); independent sector loop with IV LE32(i mod2^32)+12zero bytes, AES256-CBC,512-byte reset; compare each sector directly to held ISO |194,324/194,328 sectors, zero differences; original/ISO SHA/lengths as above. Shared CommonCrypto crypto primitive; no signature/acceptance/historical-run proof |
| R02 | Own ISO/Rock Ridge traversal from held ISO, compare content slices to saved files and source link targets |113 records,20 dirs including root,68 files,26 links per release; no byte/link mismatches. No full alternate ISO implementation certification |
| R03 | Standard-library gzip/tar full streams and source-member comparisons; unsquashfs4.7.5 -lln/-cat -strict-errors -no-wildcards to stdout, compare held payload bytes; nested source/output comparison |All 10 outer tar and 6 SFS sources, 385 gzip + 1 tar nested per release checked. SFS regular paths bin 274 / lib 3,872 / share 5,393 per release; no byte differences. Source hardlink inode mapping not reconstructed independently; unique counts 376 / 4,396 / 5,357 agree. Mode loss F02 retained |
| R04 | Own trailer/uImage CRC calculations; ciphertext byte0 XOR1 in memory only |Both originals pass; modified CRCs9da5224f/c69beba9 differ from storedf1679304/6f3bb5a2. Expected negative observed. ARM checker/updater not executed |
| R05 | Stream numbered parts against assembled original file without creating a concatenation; full byte equality and incremental SHA |Pioneer308,402,609; newer Freescale326,771,262; older Freescale1,112,825,754 bytes match. Exact hashes appendix. Not exact vendor-build proof |
| R06 | Own struct ELF32/PT_LOAD parsing and ARM BL immediate calculation from original app bytes |e_machine40, entry0xb5cc8; file offset=VA−0x8000 for cited code. VA0x6980f0/file0x6900f0 bytesf5dfe5eb→BL0x100cc;0x353c7c/file0x34bc7c bytese3f0ffeb→BL0x350010;0x350364/file0x348364 bytes1eff2fe1→bx lr. Names are analyst assignments |
| R07 | Independently parse raw E25 PROBE lines, compare saved native result; inspect thread exception behavior |925 parsed records, no JSON failure/invalid_memory event; sampled opens/transfers and17 threads supported; worker TimeoutError preserved. API-entry counters do not establish every successful transfer |
| R08 | Parse raw E30 1,129 PROBE records; independently decode protocol buffer; inspect17raw tree files and2raw XWDs; compare supervision |Zero JSON failures;66identical post-return36-byte buffers; opcode1/len9/window0x200001/parent0x42/1×1/class2/mask0x800. Trees 0 children. Each XWD 800×480 has 1,536,000 all-zero pixel bytes, SHA626db8bea999709c8faead0ec9d60025604676fcc44130abe6c1168b90989b3b. Alarm then continued main; exit−15/78.013007s host stop. No native final reconstructed |
| R09 | SHA-check26 handoff manifest entries; stream E30 tar.gz in r\|gz against external manifest, no extraction, member/type/mode/uid/gid/link/size/hash comparisons |34,185 members;32,181 nonconfidential files hashed,601,072,025 bytes;3 confidential contents skipped;0 missing/duplicate/mismatch.3.638 seconds streaming. Caps: 40,000 members / 2 GiB total / 256 MiB per member / 50 seconds. Archive identity8361c34e7da5adb4cfb9591e00fe5265041a7bef5adaa5c4497c0cd95c684904. No restored run |
| R10 | pypdf read full relevant local service p49/61, guide p1–3, change-history p1; primary NXP PDF open/screenshot p3 and Samsung indexed table |Manual part/storage/updater-label statements and publication/build-date distinction supported. Direct Samsung and OpenGroup fetches failed; Linux man-pages provided clock semantics instead. No physical-unit confirmation |
| R11 | Inspected AST-selected summarizer predicates/dict expression executed only in memory; omitted required chain/wrong thread/empty observations |Positive diagnostic classification persists, expected failure absent F01. No fullscript/write/conversion/guest run |
| R12 | Independent timespec arithmetic and original source inspection |Wrong timespec fraction/clock-ID handling established F03; no historical returned timestamp captured |

unsquashfs stat/list/cat subprocesses exited0 with empty stderr. Its -version banner printed4.7.5 (2026/03/01) and exited1; that banner status is not an extraction failure.

Direct mode reproduction is a read-only instruction:

```sh
/opt/homebrew/bin/unsquashfs -lln -strict-errors 'decode/output/image2/iso/images/bin.sfs' bootmod
ls -ld 'decode/output/image2/payloads/bin/bootmod'
```

For the tar examples, iterate members of image2/iso/images/rootfs4.tar.gz with Python tarfile without extracting, and compare m.mode/m.offset with lstat of the corresponding payloads/rootfs4 path. This source-driven check exposes the host normalization that a second extraction can hide.

### Substitutions and execution bounds

The recorded runtime is userspace execution under Qiling/Unicorn on macOS, not booting the shipped kernel or emulating the SP-16 board.

| Mechanism | Effect and evidentiary boundary |
|---|---|
| Loader address0x70000000/library aliases | Avoids emulated address/library layout obstacles; does not reproduce original loader/platform |
| ALSA null configuration with original libasound | Permits synthetic playback/capture opens and sampled64-frame returns; supplies no physical sound, DSP correctness, latency or MIDI |
| Regular null/full fixtures and copied mutable guest root | Supplies selected device/file behavior and carries state; neither Linux nodes nor original storage are reproduced |
| ARM TLS helper hook returns current c13_c0_3 via LR | Corrects documented mismatch model; improved run supports it, but no independent ablation proves it as sole allocator-fault cause |
| Local socketpairs/nonblocking IPC and limited epoll fixture | Supplies readiness/scheduling behavior; full kernel synchronization is not validated |
| Affinity handler returns ENOSYS while logging masks | Shows requested placement/names; not actual parallel cores/utilization/workload completeness |
| Authenticated X0→X16 Unix translation, names and fcntl corrections | Establishes the exact local transport observed; generalized syscall/socket fidelity and malformed-path test coverage remain limited |
| Denied fork/vfork/exec/general network/mount/reboot | Bounds selected emulator calls; latest vfork denial is observed. Static guards and a writable root alone are not complete host containment |
| Qiling signal/prctl/madvise/futex/time/unsupported syscall defaults | Synthetic/incomplete Linux behavior remains, including F03 and missing-return defaults noted in handoff; not every handler/call effect audited |
| Permanent18original-byte validated main checkpoints; capped PLT/log samples | Supports sampled control/data progression. Return hooks precede execution, output capped, --fast omits block trace, durations exclude deferred scheduling; observer overhead unmeasured |
| Portable Xvfb executable ad-hoc signatures and two compiler-path byte replacements | Host tool patches, separately recorded in portable-display-changes.json/xkb-relocation.json; original firmware bytes unchanged |

There were no forced XFlush/XMapWindow calls, panel/calibration bypass, original application patch, real-audio fixture, board/device passthrough or hardware write demonstrated in the reviewed latest session. Test fake memory/descriptor objects do not demonstrate actual socket/native-protocol behavior. Unit-test payload exclusion from runtime preparation is a scoped packaging choice, not proof that those tests passed.

Saved decoder --audit is mutating: it replaces tmp/nested outputs and rewrites reports/summary. Saved archive builders/validators have fixed destinations and historical runtime cutoffs are expired. They were inspected rather than run. Original [pre_update.sh] `<decode/output/image2/iso/pre_update.sh:14>` (evidence not published) changes firmware environment/NAND; [make_linux] `<extracted/pioneerdj_tsp/pioneerdj_tsp/make_linux:35>` (evidence not published) includes removal/install/device writes. No vendor script should be treated as safe because it sits in a source tree.

Hardware deployment would affect at least declared NAND firmware/environment and potentially component-specific updater storage. The full routing/write/acceptance logic and per-unit layout remain unresolved. The manuals identify NAND, eMMC and M1/M2 storage roles, but a stock USB updater is not established as recovery from a nonbooting update path. No write is recommended here.

### Unreviewed and historical gaps

No exhaustive review of all 515,207 paths, all emulator syscalls, every vendor build script, or the full proprietary application was performed. No complete independent source-hardlink graph, vendor-authenticity proof, firmware signature/acceptance model, release build, full platform boot, physical observation, or archive-restored execution was obtained. Original firmware acquisition receipts and some intermediate E24/E25 code/command records remain missing. E27/E28/E30 native-final gaps remain historical gaps.

Local hashes and the new comparisons cannot reconstruct earlier execution. The lack of a standalone old log or an unsuccessful old rerun does not prove dishonesty; this review does not certify its absence. Static/manual evidence, recorded execution, simulation and inference remain separately scoped in the ledger.

## E Priority next actions and completion criteria

1. **Make diagnostic certification evidence-driven and clarify counters.** In a new main-project change, require the raw checkpoint/thread/order/nonempty-output predicates; fix tracked-descriptor controls; append a dated return-visit clarification. **Complete when** the real frozen trace validates within its narrow scope and missing-chain/wrong-thread/empty-observation/broken-path controls fail for the intended reason. Historical output remains unchanged.
2. **Describe extraction metadata accurately.** Produce a new read-only source-versus-host mode inventory and update current guidance to require original metadata for any future root/repack. **Complete when** sticky/setgid and11 SFS ordinary-file differences/release are observable in the report, with readable-byte correctness preserved and no baseline rewrite.
3. **Validate the guest timing contract offline.** Inspect controlled ARM fields for clock IDs, units, normalization, invalid-ID behavior and second boundaries; record any future harness override separately. **Complete when** independently predicted fields/status match for REALTIME/MONOTONIC and gettimeofday remains correctly distinguished. This alone does not establish UI causality.
4. **Prepare the smallest parent-completion experiment.** Draft a separately scoped runtime plan for counts/bounds/actual caller return and subsequent natural display work, with an agreed ceiling, low observer overhead, independent process supervision and fixture/timing caveats. **Complete when** a submitted/authorized new run either observes parent completion and ensuing natural behavior or gives bounded remaining-work/stop evidence. Do not extend the ceiling or force a success path.
5. **Define feature/OS and deployment gates before choosing implementation.** Ask for one concrete missing feature when entering that phase, map its likely application/kernel/peripheral dependencies, and document exact build/update acceptance/storage/recovery prerequisites. **Complete when** each prerequisite has observable evidence or an explicit unresolved status, and the architecture decision follows that evidence. No full replacement OS or write is implied by today's startup progress.

The companion prompt is ready for the user to submit to the main SP16 project. It is not sent automatically and does not grant this review chat authority to modify the main folder.

## Appendix Current byte identities for review instructions

These are current length/SHA-256 bindings, not acquisition or historical-execution certificates. All paths below are relative to ``; originals, derived artifacts and analysis files retain their classes above. Original/source acquisition URLs are unresolved except for separately identified document/tool references. Numbered source parts and assemblies are included to preserve version/origin distinctions.

| Relative artifact path | Bytes | SHA-256 |
|---|---:|---|
| [README.md] `<README.md>` (evidence not published) | 2,104 | e7671537281bfac6bb0ba4e3a5438347f40b61c51c4bbe1af0f3ea8b507d13a0 |
| [ResearchSourceFiles/928c4c.pdf] `<ResearchSourceFiles/928c4c.pdf>` (evidence not published) | 21,012,381 | ed1e026f73a57945819ab2df38b2c5adb8700ecdbd942d0c3421505c9fd215a2 |
| [ResearchSourceFiles/A041E1CA-5D79-4EC1-99A5-75F927A07D3A.txt] `<ResearchSourceFiles/A041E1CA-5D79-4EC1-99A5-75F927A07D3A.txt>` (evidence not published) | 52,127 | fc751f4e861df92c12e3aec1f423bb26c4af57ecce1dba1ef524b3218cf68a0f |
| [ResearchSourceFiles/IMX_MMCODEC_3.0.101_4.1.1_Bundle.tar.gz] `<ResearchSourceFiles/IMX_MMCODEC_3.0.101_4.1.1_Bundle.tar.gz>` (evidence not published) | 14,049,950 | c138c00cfc3cea4d278c1be24613011f9c52b263d33fb5acc2613a5238d116e5 |
| [ResearchSourceFiles/IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA 2.tar.gz] `<ResearchSourceFiles/IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA 2.tar.gz>` (evidence not published) | 62,012,124 | d875d1916d25290366105ddf19997327ff52b9873e3dfd2f2af4a321a47c6099 |
| [ResearchSourceFiles/IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA.tar.gz] `<ResearchSourceFiles/IMX_MMCODEC_3.0.35_4.1.0_BUNDLE_CODA.tar.gz>` (evidence not published) | 62,012,124 | d875d1916d25290366105ddf19997327ff52b9873e3dfd2f2af4a321a47c6099 |
| [ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz] `<ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz>` (evidence not published) | 326,771,262 | df1f4ff7876ad70dbc55475fd1548eb0198e2bb45beccdcf48e9213e87eeede4 |
| [ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz.00] `<ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz.00>` (evidence not published) | 209,715,200 | 580d76ade49071ef1d2762a32cc4ec3bd94373cb506d5472a2c00a841b46fa30 |
| [ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz.01] `<ResearchSourceFiles/L3.0.101_4.1.1_141016_source.tar.gz.01>` (evidence not published) | 117,056,062 | 153206d854f06cc1ab80a046810eccae6f7a559ce66ad4347f462f6c6b400bb4 |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz>` (evidence not published) | 1,112,825,754 | f4da4aae3499f440e2120800b63108626c59b2ecc06b6eaaf6c086894836d2fe |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.00] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.00>` (evidence not published) | 209,715,200 | 1061ce7c8e017809bddddc6b18d2213dcc0421ea3736f9dd7ad6985a0e0ae483 |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.01] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.01>` (evidence not published) | 209,715,200 | 295539cee4a5b14c66e6f053e8ff6c8cd83099610615e2260eb9090e6ddfa6fe |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.02] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.02>` (evidence not published) | 209,715,200 | 678f9934abec5e19520fd1d448b807ae0dec13433156d51e10d7035888f1535e |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.03] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.03>` (evidence not published) | 209,715,200 | fdfd58da2aa21e54d3a2fe8937b696a41c14fb7467be3418ad1ba89935bb53fe |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.04] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.04>` (evidence not published) | 209,715,200 | 596a96adf4e236d4746687fc4ba730ce07d6ac5db6112ec33171e70a7b463903 |
| [ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.05] `<ResearchSourceFiles/L3.0.35_4.1.0_130816_source.tar.gz.05>` (evidence not published) | 64,249,754 | 9e13eb56b29b58bb1db09fbcabf0adb13f9d1c4231431a30bfd8a58eabb41436 |
| [ResearchSourceFiles/L3.0.35_4.1.0_docs.tar.gz] `<ResearchSourceFiles/L3.0.35_4.1.0_docs.tar.gz>` (evidence not published) | 15,493,412 | 98f21d27f935df440ba384ceaa5fe0d2620e5c80ebfd6f3407bcc24abc7f8480 |
| [ResearchSourceFiles/TORAIZ SP-16 Firmware Update Guide - AlphaTheta Help Center.pdf] `<ResearchSourceFiles/TORAIZ SP-16 Firmware Update Guide - AlphaTheta Help Center.pdf>` (evidence not published) | 294,705 | 1ec084551810615d1b3bcf3853d33b5613f068810957d07cab481cbaa742f799 |
| [ResearchSourceFiles/TORAIZSP16.UPD] `<ResearchSourceFiles/TORAIZSP16.UPD>` (evidence not published) | 99,495,956 | ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4 |
| [ResearchSourceFiles/TORAIZSP16VER150.UPD] `<ResearchSourceFiles/TORAIZSP16VER150.UPD>` (evidence not published) | 99,493,908 | 11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a |
| [ResearchSourceFiles/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf] `<ResearchSourceFiles/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf>` (evidence not published) | 151,630 | add4317727db32afccb6e8f6982a6efe58504af57413cceb682843c139a69b8f |
| [ResearchSourceFiles/TORAIZ_SP-16_manual_EN.pdf] `<ResearchSourceFiles/TORAIZ_SP-16_manual_EN.pdf>` (evidence not published) | 1,613,814 | 3e4492a03b973615aca996a76de26f442ba97ad62370c10ee73cb9d96841bb60 |
| [ResearchSourceFiles/extraction-report.json] `<ResearchSourceFiles/extraction-report.json>` (evidence not published) | 3,213,267 | 562d2e1b55ed634b5da6a6477fb270963f63b817181be2b681fde867a575fdd1 |
| [ResearchSourceFiles/ltib_patch.tar.gz] `<ResearchSourceFiles/ltib_patch.tar.gz>` (evidence not published) | 3,765 | 769b1032b79beaab41cde80f6d642f9f552c711ed88c39664a7448be38e1bb5e |
| [ResearchSourceFiles/pioneerdj_tsp.tar.gz] `<ResearchSourceFiles/pioneerdj_tsp.tar.gz>` (evidence not published) | 308,402,609 | 6fc0b3d9ac09993fc9d8e5b7e979a7c1bd21ff4f58c4ca8f056c1d1a06f971dc |
| [ResearchSourceFiles/pioneerdj_tsp.tar.gz.00] `<ResearchSourceFiles/pioneerdj_tsp.tar.gz.00>` (evidence not published) | 209,715,200 | 4120b655a9f4333a8583666ca32fd4830430da72ca637dbc25983ca073baf82a |
| [ResearchSourceFiles/pioneerdj_tsp.tar.gz.01] `<ResearchSourceFiles/pioneerdj_tsp.tar.gz.01>` (evidence not published) | 98,687,409 | 4bb938d3ed0ae37bd36b34c4f9556077e68ceb4049c16c6313732f7fe0077d95 |
| [decode/STATUS.md] `<decode/STATUS.md>` (evidence not published) | 3,743 | 180d0179b508d8a364e4773d49ae7f9aa2f76e333c68136ceb5cec36db466061 |
| [decode/decode.py] `<decode/decode.py>` (evidence not published) | 29,478 | 5b59766bf54289e67759e97f00410c33188e16515979a9427fa3e5f31c7c3dc3 |
| [docs/EVIDENCE_LEDGER.md] `<docs/EVIDENCE_LEDGER.md>` (evidence not published) | 23,764 | 0ce52bd9ceccd7ec35ec302adef4b55b8114707266d5308c30df8493ca7d8afe |
| [docs/PROJECT_CHANGELOG.md] `<docs/PROJECT_CHANGELOG.md>` (evidence not published) | 17,765 | 8794b3a2e8c0a87f7caca26d29e4b3122a5db517fa602a24556db5228a83ba9b |
| [docs/PROJECT_STATE.md] `<docs/PROJECT_STATE.md>` (evidence not published) | 85,549 | 018743e5b20308c7c86c03cb460eefac21e5dcccf3dcc241216eb3ac52ef0593 |
| [docs/handoffs/2026-10-08-independent-review/CURRENT_FILE_INVENTORY.csv] `<docs/handoffs/2026-10-08-independent-review/CURRENT_FILE_INVENTORY.csv>` (evidence not published) | 135,487,303 | 8393eaf4ad23a7fbcc64a2a11d619b0181b9305b95e3f97e90b45c26aa023527 |
| [docs/handoffs/2026-10-08-independent-review/HANDOFF.md] `<docs/handoffs/2026-10-08-independent-review/HANDOFF.md>` (evidence not published) | 13,776 | 5ed09a85f451c8b85bf91864a2d9e2e2d5ec2f387991313182c5634530b22713 |
| [docs/handoffs/2026-10-08-independent-review/HANDOFF_FILES.sha256] `<docs/handoffs/2026-10-08-independent-review/HANDOFF_FILES.sha256>` (evidence not published) | 2,419 | e823ed8b0e1d9efc66cf48aa8063f172ce25fb31457c1d1d05ae834b6d06a522 |
| [docs/handoffs/2026-10-08-independent-review/KEY_ARTIFACT_IDENTITIES.csv] `<docs/handoffs/2026-10-08-independent-review/KEY_ARTIFACT_IDENTITIES.csv>` (evidence not published) | 42,855 | 9c7ef87562f11bf2aca2544f9badeb12a77f5e31002ee2bbdaaab410d12eca41 |
| [experiments/emulation-startup-20261008-105916/check_display_guards.py] `<experiments/emulation-startup-20261008-105916/check_display_guards.py>` (evidence not published) | 2,209 | 4d9a4a1e73dca6d46da7577dcfeacdab41a35354e6b9d01daa4c0cc64dd862f4 |
| [experiments/emulation-startup-20261008-105916/local_display.py] `<experiments/emulation-startup-20261008-105916/local_display.py>` (evidence not published) | 8,354 | 5d4da2c2bb79bc265c6168134dbbca3d457f806251a22b70791db7efa32556d0 |
| [experiments/emulation-startup-20261008-105916/logs/startup-natural-01-console.log] `<experiments/emulation-startup-20261008-105916/logs/startup-natural-01-console.log>` (evidence not published) | 2,863,771 | 8945226d013b10fe8adfa142d6d8afbc4715e421e3d2f9e8baaa89fabc5c429b |
| [experiments/emulation-startup-20261008-105916/startup-natural-01-events-from-console.json] `<experiments/emulation-startup-20261008-105916/startup-natural-01-events-from-console.json>` (evidence not published) | 355,867 | 7ebb0e56d1db1d8eb16a4d2593069606fab8743b407aea20b776581ad56c1f6e |
| [experiments/emulation-startup-20261008-105916/startup-natural-01-supervision.json] `<experiments/emulation-startup-20261008-105916/startup-natural-01-supervision.json>` (evidence not published) | 6,972 | 2d77f5480cd6549e74e50a908a57402dd51fc0980532dfdf07330c19658e50dd |
| [experiments/emulation-startup-20261008-105916/startup_trace.py] `<experiments/emulation-startup-20261008-105916/startup_trace.py>` (evidence not published) | 5,573 | df059b134c96c10d9ff3fa647f9967a87b3b4eea4fbc49b3b1fae41e6ef6a82d |
| [experiments/emulation-startup-20261008-105916/summarize_evidence.py] `<experiments/emulation-startup-20261008-105916/summarize_evidence.py>` (evidence not published) | 6,552 | 70f76b0741cb358b214b10c7ade5cf0a3276f79dc2508a24576c3eb47c686660 |
| [experiments/emulation-startup-20261008-105916/validate_session.py] `<experiments/emulation-startup-20261008-105916/validate_session.py>` (evidence not published) | 5,484 | fc9db0564c94d2ae48bdc0c75d88a92e82e25de6009144a70b5be4769290a6c4 |
| [experiments/session-archive-20261008-105916/archive-manifest.json] `<experiments/session-archive-20261008-105916/archive-manifest.json>` (evidence not published) | 13,902,954 | b66683e63ce750e8b4e1a5652a03206b2d4f2edcdf50975879813c9bd7e28e61 |
| [experiments/session-archive-20261008-105916/sp16-startup-session-20261008-105916.tar.gz] `<experiments/session-archive-20261008-105916/sp16-startup-session-20261008-105916.tar.gz>` (evidence not published) | 219,886,099 | 8361c34e7da5adb4cfb9591e00fe5265041a7bef5adaa5c4497c0cd95c684904 |
| [decode/output/image1/decoded.iso] `<decode/output/image1/decoded.iso>` (evidence not published) | 99,493,888 | 534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b |
| [decode/output/image2/decoded.iso] `<decode/output/image2/decoded.iso>` (evidence not published) | 99,495,936 | 6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb |
| [decode/output/image2/payloads/pdj/pdj/EP085_Main_R] `<decode/output/image2/payloads/pdj/pdj/EP085_Main_R>` (evidence not published) | 12,000,396 | 3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464 |
| [decode/output/image1/iso/images/uImage] `<decode/output/image1/iso/images/uImage>` (evidence not published) | 4,727,400 | f9a5931feb0bf11b3e64b74e2a874b5cf58f0927204e890273f5e8def2a3566b |
| [decode/output/image2/iso/images/uImage] `<decode/output/image2/iso/images/uImage>` (evidence not published) | 4,732,596 | 267b074ee1c762b57455d48c0e1b812c6e1379b47978ab3ccf85382b448b99cb |
| [decode/output/image2/iso/images/rootfs4.tar.gz] `<decode/output/image2/iso/images/rootfs4.tar.gz>` (evidence not published) | 1,871,918 | a0ba9fdc3190e3ef73f78f56fa92b99b7ff49a88ef4054ee4032b7bcafa9fb13 |
| [decode/output/image1/iso/images/bin.sfs] `<decode/output/image1/iso/images/bin.sfs>` (evidence not published) | 6,844,416 | 55e650753dc31539b12325ed55f7ab97722d7a2059f4f98e5aea40b42f361bc0 |
| [decode/output/image2/iso/images/bin.sfs] `<decode/output/image2/iso/images/bin.sfs>` (evidence not published) | 6,844,416 | 8174047877b7a38721543cd3902b75a68d99d9143f63b442715378134111567e |
| [decode/output/image1/iso/images/share.sfs] `<decode/output/image1/iso/images/share.sfs>` (evidence not published) | 12,136,448 | 1622ac26bb402e369c336761d3586cb862921f100c70f2db596c2309f3523069 |
| [decode/output/image2/iso/images/share.sfs] `<decode/output/image2/iso/images/share.sfs>` (evidence not published) | 12,136,448 | a54081bf21e9fbac37feb7d82e484628e522cf1a5a3734e5d6f128df106aa039 |
| [experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py] `<experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py>` (evidence not published) | 2,644 | edc39a1299e631588b1617600e019afbcf8c3f106eb0495c4c27aea39e4f08d7 |
| [experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/thread.py] `<experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/thread.py>` (evidence not published) | 22,106 | cc9956327a43a060df478f7229056750577b7d1a8d93e76d6149d177803ad12a |
| [extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/linux-3.0.101/drivers/block/cryptoloop.c] `<extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/linux-3.0.101/drivers/block/cryptoloop.c>` (evidence not published) | 5,005 | 907fa8961172f8e10474fbbe71653030cdd2d189e1dd338cfa79e17c814fc967 |
| [extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/check_sig] `<extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/check_sig>` (evidence not published) | 8,905 | 217835e2a5903a9b68905635416c7ea5e234d6550bd7d324350c9513b929ac11 |
| [extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/decrypt_update.sh] `<extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/decrypt_update.sh>` (evidence not published) | 1,117 | ea787d489d740ac75e17e99d0c09879e636ab1db8548e8f8aa8e397fd5fbb9c7 |
