<!-- source: .agents/skills/sp16-feature-trace/references/report-contract.md | scrubbed -->

# Durable record contract (version 1)

Use `FEATURE_TRACE.md` for the explanation and `trace.json` for auditable records, linked from a short `HANDOFF.md`. All JSON fields in the template are required; empty arrays mean none established, not an exhaustive absence finding. Use null only where stated. A partial/unresolved report is valid; invented filler is not.

Paths in artifacts/evidence are repository-relative (no `..`, absolute paths or URLs), with locators such as line numbers, JSON keys, instruction ranges or file offsets. Copy new outputs into the investigation directory; original artifacts/prior evidence can remain in place. If an original is absent, keep its known expected hash/path, set `available: false`, explain in limitations, and limit claims to available retained evidence. If its identity was never established, omit the artifact/function records, explain the missing path/hash in unknowns, and retain only provisional hypotheses; never invent a hash to fill a field. External sources may be cited in Markdown but cannot substitute for local binary evidence. IDs are unique within their collection; function/relationship/finding/test/attempt references resolve to evidence IDs. SHA-256 is lowercase 64-digit hex; addresses are hex strings in the declared address space. Tools may add extension fields without changing required meanings.

| Record | Required content |
| --- | --- |
| Header | `schema_version: 1`, investigation ID, dated objective, completion criteria, `status` answered/partial/unresolved, supported firmware version string (or `unknown`) |
| artifacts | ID, path, SHA-256, size, role, available boolean; identity/version claims have evidence in the report |
| environment | tools with name/version, configuration object, limitations array; actual provider/profile, loader, mode/base and relevant flags in configuration |
| evidence | ID, artifact ID or null for tool/log-only evidence, local path, locator, exact command/tool arguments object, native REA evidence ID or null, limitations |
| functions | ID, artifact ID, hex entry or null when unresolved, address space, mode, name, name provenance, inclusive body ranges, evidence IDs; empty ranges explicitly mean unknown coverage |
| relationships | from function ID, to function ID or null, type, call/data site, status supported/inferred/unresolved, details, evidence IDs |
| findings | ID, kind, statement, evidence IDs, rationale, confidence high/medium/low/unknown, limits |
| unknowns | Explicit unresolved questions as strings |
| contradictions | statement, evidence IDs and effect on conclusions; empty only if none encountered |
| validation | ID, status passed/failed/not-run/blocked, repeatable procedure object, actual result string or null for unexecuted tests, evidence IDs |
| confidence | Overall level and justification, without upgrading inference to observation |
| next_experiments | question, method, expected discriminator, required evidence/permissions, `runtime_authorized` boolean derived from current scope; recommendation does not grant it |
| attempts | query/arguments object, search scope, result, evidence IDs, repeat reason string or null |
| limitations | Missing dependencies, gaps, unavailable records, adapters and confidence limits |

Finding kinds are `artifact-observed`, `static-supported`, `runtime-observed`, `inferred`, `hypothesis`, `unknown`. The first four require local evidence; hypotheses/unknowns can have none but require rationale. Runtime findings must cite actual retained runtime evidence and distinguish emulator/adapters/physical unit in the statement/environment. A validator cannot establish that a supplied log is truly runtime evidence or that the reasoning is sound.

Executed passed/failed validation requires actual result and evidence. `not-run`/`blocked` uses null result and explains the proposal/block in procedure or limitations. Mark command invocation as executed only if it actually ran; preserve failed commands/output. Keep raw results separate from analyst interpretations.

Run `python3 <skill>/scripts/trace_records.py validate <report>/trace.json --root <repo>`. This checks required types/enums, ID joins, file existence/containment, function ranges, evidence obligations and test status consistency. `--verify-hashes` also rehashes available selected artifacts. `identity PATH --expect SHA256` fails on mismatch and does not create files. Both print JSON to stdout and nonzero on rejection. These utilities use Python's standard library only, never execute an artifact, and do not validate semantic correctness, original-byte disassembly correspondence, report prose or completeness; apply the investigation's focused original-byte verifier and reviewer judgment.

For an independent audit, start from artifacts, decisive evidence locators and commands before reading proposed interpretations. Test claims against contrary branches and missing joins. Preserve native REA evidence IDs alongside resolvable paths; do not count two tools backed by one database as independent proof.

For a used layout/model slice, link its consumed layout, transition/coverage table and comparison contract in the existing report/validation records; [slice contracts] `slice-contracts.md` (evidence not published) defines their scope. Keep original comparison `not-run` with null result when matching captures are missing, and label synthetic controls separately. Passing mechanics cannot upgrade a finding's evidence class or qualify lifetime, release, fresh audio or Keep. A one-member capture cannot satisfy a broader roster coverage claim.
