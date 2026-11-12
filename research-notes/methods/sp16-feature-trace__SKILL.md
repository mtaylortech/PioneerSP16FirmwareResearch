<!-- source: .agents/skills/sp16-feature-trace/SKILL.md | scrubbed -->

---
name: sp16-feature-trace
description: Trace a Pioneer SP-16 firmware feature from a scoped question through binary functions, data and call relationships, behavioral reconstruction, and an evidence-linked report with validation and next experiments. Use for feature-level firmware research; use sp16-static-investigation for a small standalone static contract question and sp16-continuation for handoffs.
---

# SP-16 feature trace

Produce a defensible feature explanation that another session can reproduce and audit. Treat the requested feature as the scope, not permission to execute firmware or implement a replacement.

Resolve the repository root from this skill's location (`../../..`), then read its `AGENTS.md`, `README.md`, and latest relevant handoff. Honor current user limits and existing authorization; historical allowances do not renew. Search prior findings before new analysis. Keep original firmware, installed runtimes, completed reports and databases unchanged. Use read-only access or a fresh working copy; never execute extracted firmware/scripts directly on the macOS host.

## A. Prepare the question

State one narrow objective, completion criteria, candidate release/binaries, and a stopping boundary. Search relevant `experiments/`, `ghidra/`, `engineering-reviews/`, and `decode/` records with `rg`; do not regenerate broad inventories. Read [methodology] `references/methodology.md` (evidence not published) for scope, search discipline and reconstruction.

Bind selected artifact paths, SHA-256, size, internally supported firmware version, and version evidence. Record tool versions, loader/base/mode/relocation settings and limits. `scripts/trace_records.py identity PATH [--expect SHA256]` streams the hash without altering the artifact. Unknown identity/version/mode stays explicit; an identity mismatch stops claims about that artifact until resolved.

## B. Investigate the smallest useful family

Read [tooling] `references/tooling.md` (evidence not published) when selecting an analysis route. Prefer available, suitable REA operations; use actual tool schemas and availability, not assumed commands. Reuse checked exports/corrected Ghidra projects where they already answer the question. REA is optional: absence must not block an investigation that existing Ghidra or byte/disassembly evidence can answer.

For low-level static work, reuse [sp16-static-investigation] `../sp16-static-investigation/SKILL.md` (evidence not published) if present. This skill's methodology retains the essential invariants if that sibling is unavailable. Follow candidate strings/constants, callers/callees, xrefs, pointer/field stores, control/data flow and interfaces only as needed. Record query, search boundary, result and reason for any repeat. Cached decompilation needs a concrete reason to be regenerated. Missing/default function boundaries and omitted tool facets are unknowns, not proof of absence.

## C–D. Reconstruct and validate

Classify every finding as artifact observation, static support, runtime observation, inference, hypothesis or unknown. Explain inputs/outputs, state transitions, initialization order, dependencies, interfaces and failure paths where evidenced. Decompiler names/types/prototypes remain inferred unless independently established. Preserve unresolved indirect targets and contradictions.

For a layout-backed observer or executable reconstruction, use the [slice contract method] `references/slice-contracts.md` (evidence not published): consume existing provenance, check actual access/receiver joins, and separate mechanical layout checks from independent behavioral comparison. Read it only when those claims affect the selected question.

Check decisive new joins against original bytes and alternate paths or existing runtime evidence. Record what actually ran and its result; proposed tests are `not-run`. Static relationships do not prove executed delivery or hardware behavior. A runtime test may proceed within current bounded authorization, with the project’s supervision/guards/ownership-aware cleanup; otherwise recommend it. This skill adds no runtime, hardware, flashing, installation, network, publishing or deployment permission.

Stop when criteria are supported, the first decisive missing edge prevents further conclusions, the selected limit is reached, or another bounded search would repeat an unproductive approach without new evidence. Report partial/unresolved results honestly and select the smallest experiment likely to discriminate the remaining explanations.

## E. Preserve a reviewable result

Use a fresh `experiments/feature-trace-<topic>-<timestamp>/` directory, or the current investigation directory. Keep raw commands/tool arguments, meaningful outputs, failures, selected code/config identities and any owned cleanup there. Export REA evidence before closing resources opened here; retain native evidence IDs **and** local evidence paths/locators.

Write `FEATURE_TRACE.md` from [the report template] `assets/feature-trace.md` (evidence not published) and `trace.json` from [the record template] `assets/trace.json` (evidence not published). Read [report contract] `references/report-contract.md` (evidence not published) for fields and evidence checks. Validate with `python3 <skill>/scripts/trace_records.py validate <trace.json> --root <repo>`; add `--verify-hashes` when checking selected artifact correspondence. This checks records and references, not truth or analysis completeness.

Write one short `HANDOFF.md` linking the report, raw evidence, remaining unknown and next test. Do not duplicate the report into ledgers. Apply current README/review indexing rules only when their conditions apply; a feature trace does not require a separate engineering review. Explain results and limits in the final reply and show how the next experiment advances the requested feature.
