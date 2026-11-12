<!-- source: .agents/skills/sp16-feature-trace/references/tooling.md | scrubbed -->

# Tool selection and repository reuse

This is routing guidance, not an installation recipe. Discover actual paths and tool schemas at use time. Local examples below were inspected during creation; consult maintained handoffs if they move. Never run old launchers solely because they are linked here: they may hard-code expired deadlines, output directories or artifact hashes.

## REA when available

Use the connected REA catalog and the installed `reverse-engineer-anything` skill if present. If availability/provider/session ownership is unclear, `binary_session {}` reports it without starting analysis. Do not replace or close an unrelated active target. Bind your selected local binary with the advertised `open_binary` schema and a suitable available provider. Compare the returned SHA-256 with your independently computed identity.

Observed REA 6.3.0 operations include `analyze_function`, `search_procedures`, `search_strings`, `procedure_callers`, `procedure_callees`, `procedure_references`, `read_function_instructions`, `read_bytes` and `export_evidence_bundle`. These names are examples to look for, not commands to invent if absent. Inspect current arguments/limitations before use. Keep one session for related queries to amortize import. Prefer a dossier or focused query over a whole-program inventory. Preserve complete inline Evidence, provider/profile/environment, omissions and evidence IDs. An evidence ID alone may expire with the session: export to a new local path before `close_binary` for resources you opened. No automatic annotation of completed databases.

The retained [REA comparison] `../../../../experiments/rea-ghidra-comparison-20261010-202454/HANDOFF.md` (evidence not published) and [marginal workflow test] `../../../../experiments/rea-marginal-workflow-20261010-205205/HANDOFF.md` (evidence not published) explain configuration and limitations. Default Ghidra-backed imports missed valid entries; focused stock recovery was required. Warm REA queries are convenient, but these measurements do not prove general analysis/discovery superiority. Missing fields/functions remain unknown; unsupported ELF load-image verification must not be reported as passed.

If REA is unavailable, proceed with existing verified exports, saved Ghidra or suitable static tools. Do not install packages, run `npx` auto-downloads, repair MCP registration or upgrade the toolchain merely to complete a trace. Consult the installed REA skill and [upstream documentation](https://github.com/morluto/rea) only for a selected integration change, honoring its scope and permissions.

## Existing Ghidra and static fallback

Locate configuration and identities through [ghidra/provenance.json] `../../../../ghidra/provenance.json` (evidence not published), [installation.json] `../../../../ghidra/installation.json` (evidence not published) and relevant handoffs. The repository has a corrected 1.60 project at `ghidra/projects/SP16_1_60_ELF.gpr`, program `EP085_Main_R_fw160`; a 1.50 example is `experiments/provider-binding-20261010-072803/projects/SP16_1_50_provider.gpr`, program `EP085_Main_R`. Verify these exist and match the chosen artifact; neither is a universal default release.

Read-only/noanalysis reopening avoids repeating global analysis. Use a copied project for entry recovery, context correction, annotations or other database edits. A focused recovery is a different analysis profile: record recovered ranges, mode and justification. Do not recover functions by blind disassembly across data/literal pools.

Existing exporters include `ghidra/scripts/SP16FocusedStartup.java` and `experiments/rea-marginal-workflow-20261010-205205/scripts/WorkflowExport.java`; the latter exports ranges, instructions/TMode, references and decompilation for 1.50 and intentionally checks that release's hash. Existing focused entry recovery is `.../scripts/FocusRepair.java`. Reuse/adapt a copy only after inspecting assumptions, arguments and output acceptance. Existing `ghidra/scripts/verify_static.py` and the marginal test's `scripts/verify.py` illustrate PT_LOAD correspondence and instruction checks; they are scoped experiment tools, not generic launch commands.

Without a working engine, use identity-verified prior exports and original bytes with available static parsers/disassemblers. Label reused observations as historical/reference evidence and disclose that new decompilation was unavailable. If neither bytes nor matching exports exist, finish unresolved with the missing dependency; do not fabricate routines or addresses.

## Storage and runtime boundary

`decode/README.md` maps extraction provenance. The retained original application paths are under `decode/output/image1/payloads/pdj/pdj/` and `image2/...`; check actual paths and internal-version records. Do not rerun the decoder as routine discovery: it regenerates outputs. `docs/storage/KEEP.json` and `INDEX.json` locate archived assets when required; restoration is a separate selected action.

Place fresh evidence in the investigation's directory. Trusted host analysis utilities can launch under finite bounds with owned cleanup; firmware execution uses the maintained emulation workflow only within current authorization. Read the actual selected runner before reusing it, including recorded cleanup failures and fixes. Skill invocation alone authorizes neither a guest nor hardware. Do not log credentials or extracted local keys.
