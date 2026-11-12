<!-- source: .agents/skills/sp16-static-investigation/SKILL.md | scrubbed -->

---
name: sp16-static-investigation
description: Answer bounded shipped-SP16 firmware questions through static disassembly, decompilation, call/field/ownership mapping and contract investigation, excluding ordinary source review and firmware execution.
---

# SP16 static investigation

Recover one question, selected source and permitted scope from the request, [AGENTS.md] `../../../AGENTS.md` (evidence not published), [README] `../../../README.md` (evidence not published) and latest relevant handoff. These govern authorization and workspace boundaries; this skill expands neither. Reuse completed discoveries. Stop at a supported answer, first decisive missing edge or selected limit, reserving time for verification, owned cleanup and reporting. Historical allowances do not renew.

Bind the selected ELF/release, analysis image and effective configuration. Separate held firmware, emulated runtime and physical-unit claims. Reuse suitable corrected Ghidra evidence or available REA tooling without requiring a switch, fresh import, upgrade or repeated comparison. Preserve completed databases through read-only access or a fresh working copy. The [comparison procedure] `../../../experiments/rea-ghidra-comparison-20261010-202454/HANDOFF.md` (evidence not published) illustrates source correspondence, corrected boundaries and loader distinctions.

Follow the smallest necessary caller/callee/field family. Establish entries, body coverage and actual ARM/Thumb context; tool language labels alone do not establish mode. Support decisive joins with original instructions, registers, stack arguments, pointer stores, tables and relevant relocations. Decompiler types/prototypes and database signatures remain inferred. Leave unbound indirect calls unresolved; linkage names do not establish execution of imported implementations.

Independently check decisive new instruction/data exports against original file-backed PT_LOAD mappings: `p_offset + (address - p_vaddr)`, bounded by `p_filesz`. Account explicitly for loader fixups; neither universal base subtraction nor BSS supplies original file bytes. Reuse unchanged verification helpers and completed checks. Inspect correspondence and coverage: exit zero or record counts alone are insufficient.

Separate submission, admission, execution, callback, completion, destruction and ownership. Task IDs, request returns, queue disappearance and no-op listeners prove neither settlement nor release. Trace deferred producer records separately from worker queues; admission drain, delete-without-execute cleanup and worker return need their own joins to release acknowledgment and captured-object lifetime. The [scheduler/lifetime example] `../../../experiments/normalization-pending-editor-load-settlement-20261010-step09f/HANDOFF.md` (evidence not published) shows this discipline. An unbound candidate edge establishes neither an observed stock defect nor stock-wide absence.

If a decisive answer uses a layout or host model, consult the [slice contract method] `../sp16-feature-trace/references/slice-contracts.md` (evidence not published) when available. Consume existing offsets, bind access width and receiver/phase to original locators, distinguish raw access from ABI layout, and keep unknown extent/type/lifetime partial. Model comparison needs independent matching original expectations and effects; missing capture is `NOT-RUN`, synthetic agreement is mechanics only. Link the used slice from the same concise handoff; this does not require another report or runtime launch.

Retain query/export provenance, effective configuration, verification limits, failures, missing receipts and relevant owned cleanup. Finish with one short handoff: question, method/change, supported result, evidence links, remaining unknown and smallest next discriminator. Apply maintained README/review rules without duplicating ledgers or requiring a review for every investigation. Keep volatile results and next actions in maintained handoffs.
