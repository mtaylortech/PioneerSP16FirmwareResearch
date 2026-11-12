<!-- source: docs/handoffs/2026-10-08-independent-review/EVIDENCE_INDEX.md | scrubbed -->

# Pioneer TORAIZ SP-16 existing evidence index

This **current index, 2026-10-08**, points to retained material at ``. All paths in code formatting are relative to that root. The index does not certify an earlier run. New handoff files are separate from the pre-existing research and are excluded from the baseline [full current inventory] `CURRENT_FILE_INVENTORY.csv` (evidence not published).

Use [HANDOFF.md] `HANDOFF.md` (evidence not published) for review scope, [CLAIM_LEDGER.md] `CLAIM_LEDGER.md` (evidence not published) for claim-to-source mapping, and [EXPERIMENT_LEDGER.md] `EXPERIMENT_LEDGER.md` (evidence not published) for attempt-level evidence. [EVIDENCE_PATHS.csv] `EVIDENCE_PATHS.csv` (evidence not published) is a 669-row navigation subset. The full inventory includes every copied guest/rootfs, installed emulator package, expanded source dependency and symlink; the smaller subset deliberately omits those bulk trees. [DIRECTORY_SUMMARY.csv] `DIRECTORY_SUMMARY.csv` (evidence not published) provides counts and logical bytes by directory group.

## Instructions and research records

| Existing material | What to inspect | Qualification |
|---|---|---|
| [README.md] `../../../README.md` (evidence not published) | Existing entry point and current research status | Agent-maintained; not a user-instruction transcript. |
| [docs/PROJECT_STATE.md](../docs__PROJECT_STATE.md) | V01–V45 findings, current handoff, hypotheses/backlog, version/source/runtime boundaries | Secondary canonical synthesis; source artifacts control evidentiary strength. |
| [docs/EVIDENCE_LEDGER.md](../docs__EVIDENCE_LEDGER.md) | E01–E30 source taxonomy and provenance | Catalog of sources rather than a proof of every nearby claim. |
| [docs/PROJECT_CHANGELOG.md](../docs__PROJECT_CHANGELOG.md) | Dated consolidation, runtime, correction and archive decisions | Narrative chronology, not a complete command/exit audit trail. |
| `docs/NEXT_SESSION_PROMPT-20261008*.txt` and `.sha256` | Proposed scope, task queue, stop rules, exclusions and requested outcomes | Only a corresponding human invocation authorizes execution. Several versions coexist. |
| `experiments/handoff-preparation-20261008-095741/` and `...-105321/` | Before-doc snapshots, exact saved prompts, readiness checks and document archives | Preserve superseded text and ordering; hashes of a proposal do not prove execution. |
| Experiment `history-before/`, `history/`, `.diff`, and archive members | Earlier states of canonical docs, probes, fixes and session plans | Original versions and failed alternatives remain reviewable. Full inventory resolves every path. |
| `decode/README.md`, `PROCESS.md`, `FINDINGS.md`, `STATUS.md` | Earlier algorithm, acquisition assumptions, extraction checkpoints and limitations | Some broad early language is superseded by narrower canonical claims. |

The new [INSTRUCTIONS_AND_DECISIONS.md] `INSTRUCTIONS_AND_DECISIONS.md` (evidence not published), [HISTORY_SOURCES.json] `HISTORY_SOURCES.json` (evidence not published) and [REQUEST_AND_SCOPE.md] `REQUEST_AND_SCOPE.md` (evidence not published) distinguish direct human text, agent proposals, historical chat summaries and current retrieval limits. The license notice `ResearchSourceFiles/A041E1CA-5D79-4EC1-99A5-75F927A07D3A.txt` is **vendor licensing text**, not user instructions.

## Original inputs and vendor evidence

| Material | Location and use | Limits |
|---|---|---|
| Firmware originals | `ResearchSourceFiles/TORAIZSP16VER150.UPD`, `TORAIZSP16.UPD` | Held 1.50/1.60 only; no original ZIP, flash dump or publisher-authentication receipt. |
| Platform and BSP archive originals/parts | `ResearchSourceFiles/pioneerdj_tsp.tar.gz*`, `L3.0.35_4.1.0_130816_source.tar.gz*`, `L3.0.101_4.1.1_141016_source.tar.gz*` | Preserve assembled outputs and numbered input parts. Part-concatenation checks are recorded in `docs/TRANSFORMATIONS.json`. |
| Codec/patch/doc bundles | `ResearchSourceFiles/IMX_MMCODEC*`, `ltib_patch.tar.gz`, `ltib_patch/`, `L3.0.35_4.1.0_docs.tar.gz` | Broad vendor dependencies, including packaged binaries; no release rebuild established. The two CODA archive copies have the same current hash. |
| Service documentation | [928c4c.pdf] `../../../ResearchSourceFiles/928c4c.pdf` (evidence not published), extracts/renders under `decode/tmp/consolidation/service-page-*` | Manufacturer content in a third-party PDF; documentary board identification, not measured unit behavior. |
| User manual, update guide, release history | `ResearchSourceFiles/TORAIZ_SP-16_manual_EN.pdf`, `TORAIZ SP-16 Firmware Update Guide - AlphaTheta Help Center.pdf`, `TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf` | Intended operation/release dates; not implementation, update testing or source-code proof. Text/page JSON under `decode/tmp/consolidation/`. |
| License/source metadata | Vendor `.txt` notice; `copyright/` (157 regular files); `extracted/` | Package notices are not proof of application use. Generic BusyBox/Linux labels conflict with exact shipped versions. |
| Original extraction history | [ResearchSourceFiles/extraction-report.json] `../../../ResearchSourceFiles/extraction-report.json` (evidence not published); [RECOVERED_EXTRACTION_HISTORY.json] `RECOVERED_EXTRACTION_HISTORY.json` (evidence not published); [recovered script provenance] `recovered-extractor/PROVENANCE.json` (evidence not published) | Earlier workspace records did not locate the extractor. This handoff recovered genuine historical command records and current `/tmp` script copies; special-entry omissions, code-version bindings and a current FIFO still need qualification. |

Exact byte lengths, SHA-256 values and acquisition notes are in [KEY_ARTIFACT_IDENTITIES.md] `KEY_ARTIFACT_IDENTITIES.md` (evidence not published). All expanded source file identities are available in the full CSV. Key paths are inventoried but their bytes/digests are withheld.

The current external copies of `/tmp/sp16_extract_recursive.py` and `/tmp/sp16_extract_verify.py` are preserved under `recovered-extractor/` without execution. Their current hashes/source mtimes belong to the new provenance record, not the original workspace snapshot or an invented historical run. Retrieved historical command records retain original statuses and available outputs with retrieval limits.

## Decoder and static outputs

| Material | Location | Review use |
|---|---|---|
| Custom decoder/auditor | [decode/decode.py] `../../../decode/decode.py` (evidence not published) | Inspect cryptoloop assumptions, stricter trailer-marker rule, container support, extraction omissions, overwrite behavior and audit independence. |
| Derived decoded containers | `decode/output/image{1,2}/decoded.iso` and `iso/` | Original-to-output comparisons, update/pre-update scripts, primary components and embedded version labels. Never execute updater scripts as part of review. |
| Expanded firmware | `decode/output/image{1,2}/payloads/` and `nested/` | Separate tar/SquashFS layers, app/resources, libraries, nested gzip/test/archive contents; not a bootable merged Linux image. |
| Reports and exact manifests | `decode/output/summary.json`, `audit-summary.json`; per-image `report.json`, `audit.json`, `iso-manifest.json`, `payload-manifest.json`, `nested/report.json`, `nested/manifest.json`, tar metadata JSON | Source extents, path/link sets, hashes, exit codes, inode/hardlink counts and metadata-only entries. |
| Raw audit/extraction outputs | `decode/tmp/*.audit.log`, `*.sfs.extract.log`, `*.iso-extract.log`, `*.nested-candidates.json`, `before-rerun.json`, `consolidation/latest-audit.log`, `part-validation.json` | Historical logs/checkpoints, tool help, omitted entries and failures. Saved logs have incomplete surrounding shell provenance; do not invent exit codes. |
| Binary annotations | `decode/tmp/losetup.disasm`, `check_sig.disasm`; `docs/EVIDENCE_SNAPSHOT.json` | ARM addresses, inspection commands/outputs, ELF imports and banners. |
| Transformation provenance | docs/TRANSFORMATIONS.json `docs/TRANSFORMATIONS.json` (evidence not published) | Input/output identities, operation names/commands and manifest references for 25 grouped transformations. |
| Historical static inventory | `docs/ARTIFACT_INVENTORY.md` / `.json` | 108 selected artifacts; predates runtime work. Original files preserved; new inventory is separate. |

## Runtime harnesses and experiments

| Session | Existing runbook and primary outputs | Failures or review challenges |
|---|---|---|
| E24 original startup, October 7 | [emulation-20261007/README.md] `../../../experiments/emulation-20261007/README.md` (evidence not published); `probe.py`, `prepare_rootfs.py`, `rootfs/`, `dependencies.json`, `startup-summary.json`, `*-result.json`, `logs/` | Filesystem/link/loader/brk setup failures, unavailable hardware, null read, user-reported host crash. Exact intermediate code snapshots are incomplete. |
| E25 synthetic audio/thread baseline | [emulation-20261008/README.md] `../../../experiments/emulation-20261008/README.md` (evidence not published); `initial-probe.py`, `probe.py`, `alsa-{original,null}.conf`, device fixtures, PLT map, `*-result.json`, `session-summary.json`, `logs/` | TLS correction; IPC/epoll/affinity substitutions; null PCM; worker timeout conflicts with one successful-looking summary. |
| E27 initial display | [emulation-display-20261008-004011/README.md] `../../../experiments/emulation-display-20261008-004011/README.md` (evidence not published); server/local-display/probe scripts, `display-attempt*.json`, `display-01-result.json`, `partial-summary.json`, `attempt-history.json`, `logs/`, `captures/` | Xvfb startup retries, signature check alternatives, cookie access failure, unauthenticated rejection, alarm failing to stop all workers, no native final retry JSON. |
| E28 authentication/nonblocking | [emulation-display-20261008-011849/README.md] `../../../experiments/emulation-display-20261008-011849/README.md` (evidence not published); attempt-specific script snapshots, launch commands, `auth-*` evidence/supervision, flag reproducer, `logs/`, `captures/` | First host launch failure; Linux/Darwin flag mismatch; valid API returns with zero server children/black captures; partial final retry. |
| E29 request-buffer diagnostics | [emulation-display-20261008-101605/README.md] `../../../experiments/emulation-display-20261008-101605/README.md` (evidence not published); `xlib-layout.json*`, Xlib/XCB disassembly `.txt`, `display_diagnostics.py*`, `targeted-correction.json`, both `buffer-natural-*` results/supervision, `logs/`, `captures/` | Return-hook collision and corrected retry; original 36-byte request remains queued; observed 1×1 InputOnly request is not a drawable UI. |
| E30 latest startup progression | [emulation-startup-20261008-105916/README.md] `../../../experiments/emulation-startup-20261008-105916/README.md` (evidence not published); `startup_trace.py`, `startup-binary-analysis.json`, focused callers/disassemblies, `session-summary.json`, `startup-natural-01-events-from-console.json`, `startup-natural-01-supervision.json`, `logs/`, `captures/` | Capped counts and partial native stop; completed initialization work observed, causal wait/completion unproven. Missing native final result is preserved. |

Each session also has preparation/copy provenance, integrity/verification records, authorization/clock/launch records where retained, root manifests and process-state/close records. These bind different moments; a current script hash is not automatically the identity used by every earlier attempt. See the experiment ledger for precise raw filenames and recorded exit status.

Installed Qiling/Unicorn/native dependencies are retained under `experiments/emulation-20261007/tools/venv/`. `requirements-resolved.txt`, install logs, package metadata and `docs/EMULATION_HANDOFF_VALIDATION.json` describe the environment. Original 1.60 libraries are copied into each working root; null audio config, aliases, ordinary-file devices, tmp/cache files and mapped socket/auth paths alter that guest environment. All current paths are included in the full inventory.

## Tests, validators and decision records

Project verification consists primarily of decoder container/source audits, dependency/root integrity checks, display guards, flag reproducer, supervision checks and archive member comparisons. `decode/tmp/consolidation/{build_inventory,validate_docs,verify_emulation_handoff}.py` and per-session `verify_integrity.py`, `validate_session.py`, `check_display_guards.py` are retained. Their saved JSON outputs are historical snapshots. Some overwrite canonical reports or rely on old source counts; inspect before running and redirect outputs in an independent copy.

Vendor/standard-library test fixtures exist throughout `extracted/`, firmware payloads and installed dependencies. Their presence does not establish a test run or pass. `prepare_rootfs.py` omits every `unit_tests` directory; special-device/FIFO fixtures are also limited. No working-instrument, hardware-audio, updater/recovery, feature-modification or complete release-build test result is established. All known substitutions and test exclusions are detailed in [SUBSTITUTIONS_AND_REPRODUCTION.md] `SUBSTITUTIONS_AND_REPRODUCTION.md` (evidence not published).

`session-authorization.json`, saved user prompts, `session-journal.json`, `attempt-history.json`, correction JSON/diffs, `status-report-timing.json`, session summaries and before-doc snapshots retain decisions, failed attempts and proposed follow-ups. They should be read alongside raw evidence, especially where a narrative says “verified” or “returned.”

## Archives and preservation evidence

| Existing archive area | Contents and qualification |
|---|---|
| [session-archive-20261008-010249] `../../../experiments/session-archive-20261008-010249/README.md` (evidence not published) | Earlier runtime/history archive, including emulator environment; member manifest/status/verification retained. |
| [session-archive-20261008-011849] `../../../experiments/session-archive-20261008-011849/README.md` (evidence not published) | Authentication/nonblocking session snapshot with closing validation and restoration dependencies. |
| [session-archive-20261008-101605] `../../../experiments/session-archive-20261008-101605/README.md` (evidence not published) | Request-buffer session; initial/corrected diagnostics and exact evidence with external report manifest. |
| [session-archive-20261008-105916] `../../../experiments/session-archive-20261008-105916/README.md` (evidence not published) | Latest startup session; exact partial console evidence, supervision and correction records. |
| `experiments/emulation-display-20261008-004011/archive-audit/` | Historical read-only archive checker, audit report and raw check records. |

Archives are on the same disk. Original source/firmware and the host Python framework remain external restoration dependencies where documented. Existing member comparisons do not establish successful restored execution. Current container hashes are in the identity appendix; this handoff did not extract or replay the archives.
