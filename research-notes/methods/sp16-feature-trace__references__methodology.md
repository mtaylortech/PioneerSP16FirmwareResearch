<!-- source: .agents/skills/sp16-feature-trace/references/methodology.md | scrubbed -->

# Feature investigation methodology

## Preparation and search memory

Translate a broad feature into one observable question: for example, which original routine constructs the display window and which call transfers control into event dispatch? Separate display construction, rendering, input delivery and physical display operation. Define what evidence would answer the chosen question and what remains outside scope.

Start with the maintained README and latest relevant handoff. Search feature vocabulary, UI strings, device paths, class/symbol names and already known addresses in relevant text exports/reports. Record reused findings with their original release/hash, evidence and limits. Older extraction reports help locate the binary and internally verified version; they do not override current authorization. Archived/ignored inputs may be unavailable on a fresh checkout: report this and use matching retained exports for historical-reference claims, rather than silently substituting another release.

Keep a compact attempts array in `trace.json`: query/arguments, searched files or database family, outcome, evidence IDs, and reason for a repeat. Search negatives cover only the stated boundary. After an unproductive approach, change the seed, consult a related dependency, or stop with the missing evidence; do not repeat identical whole-program searches. Prefer existing findings over fresh imports and batch adjacent queries when appropriate. No fixed number of bodies or administrative timing ledger is required.

## Identity and function boundaries

For each selected original and analysis image, record path, size and SHA-256. Record the internal-version source separately from filenames. If a working/loaded image differs, bind both identities and explain changes. Do not transfer addresses between releases based on similar names.

Record format, supported architecture, endianness, address space, loader, image base, compiler specification, library-loading/relocation settings, tool versions and decompiler options. Do not infer processor/hardware solely from a directory name. For each function record binary identity, entry, actual body ranges, instruction mode and name provenance (original symbol, tool-generated or analyst-assigned). A continuation or literal pool need not be a function entry. For unknown boundaries/mode, use explicit null/unknown and limit claims to inspected bytes.

For file-backed ELF PT_LOAD segments, original offset is `p_offset + (VA - p_vaddr)` and the entire checked range must lie inside `p_filesz`. BSS has no original file bytes. Universal base subtraction is invalid. Account for documented loader fixups/relocations when comparing loaded bytes; a mismatch must be explained, not masked. Reuse unchanged project verifiers rather than importing their experiment-specific assumptions blindly.

## Targeted tracing and reconstruction

Use strings/constants as seeds, then bind their references to instructions and relevant callers/fields. Trace direct calls, conditional branches, returns and failure paths. At indirect/virtual calls bind receiver provenance, slot/table bytes, object construction, and actual target where possible. Leave unbound edges unresolved. Data references are not a proved data-flow relationship; verify stores, loads, register/stack arguments and value lifetime.

Describe ABI inputs, outputs and side effects without claiming recovered pseudocode is source. Keep database signatures separate from decompiler parameters and instruction-supported register use. For stateful features distinguish submission, admission, execution, callback, completion, destruction and ownership. A request return, empty queue or no-op listener does not prove release/settlement. Trace producer/deferred records and consumers separately when relevant.

Interface claims need an evidence chain from imported symbol/syscall/device path/register access to its arguments and caller. A symbol or filename alone does not establish physical hardware behavior. Map initialization prerequisites, sequencing, model/data structures, errors and cleanup only within inspected coverage; absence of a call in selected bodies is not stock-wide absence.

Where field layouts or executable models support a decisive claim, follow [slice contracts] `slice-contracts.md` (evidence not published). Keep offsets in existing provenance and resolve them into a consumed declaration, with original access widths and receiver/subobject/construction phase. A raw access is not a recovered C ABI member. A faithful instruction account and a readable behavioral account may help for a difficult routine; retain exact arithmetic, side effects and original locators without requiring a second whole-program export.

## Validation and confidence

Corroborate decisive conclusions using alternate paths, original instructions, source-to-export checks, previously retained runtime receipts or a controlled test within current scope. Two REA/Ghidra renderings of the same Ghidra database are not independent evidence. Byte correspondence checks content, not semantic correctness or complete xref/function recall.

Keep contradictions side by side with locators and effects on the claim. Distinguish artifact facts, static control/data flow, observed emulation, modeled adapters and physical-device observations. Identify adapters, environmental substitutions, truncation and missing records. A tool exit of zero is insufficient without required outputs and coverage. Never turn an unperformed test into verification.

Assign confidence per finding and overall: high/medium/low/unknown with rationale and limits. A directly verified instruction can have high confidence while its proposed purpose remains medium/low. Completed local phases stay completed; a missing downstream milestone does not reopen them. End with one prioritized discriminator, its expected outcomes and the evidence/authorization it requires.
