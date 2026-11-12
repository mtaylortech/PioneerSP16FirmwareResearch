<!-- source: analysis/ghidra-1.60-20261009/HANDOFF.md | scrubbed -->

# SP-16 firmware 1.60 Ghidra analysis

October 9, 2026, America/Chicago. The original `EP085_Main_R` is imported into a dedicated Ghidra project, with the mapped startup initializer and callers labeled and bookmarked. Static analysis confirms the saved caller/return chain and identifies separate rejection paths. **Successful runtime startup remains unverified by this work. No firmware, emulator, display/input helper or target code was launched, and no input was sent.**

## Project and installation

The active project is [SP16_1_60_ELF.gpr] `projects/SP16_1_60_ELF.gpr` (evidence not published), containing `/EP085_Main_R`. In Ghidra, use File → Open Project, select that file, open the program, then navigate to `0x571d24`. Bookmarks under **Analysis → Startup lifecycle** mark the initializer, caller continuations, wrapper rejection branches and dispatch. `mapped_*` names are analyst labels; they are not recovered original source names.

The actual workspace is ``; the supplied `` no longer exists. Ghidra 12.1.4 is at `<HOME>/Code_Projects/ghidra_12.1.4_PUBLIC`. Temurin Java 21.0.12.1 ARM64 is at `/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home`. Both GUI and headless scripts exist. The ARM64 native decompiler resolves from `Ghidra/Features/Decompiler/build/os/mac_arm_64/decompile`; no installation changes were needed. [Installation receipt] `installation.json` (evidence not published), [resolved program metadata] `exports/program-metadata.json` (evidence not published).

The import uses ELF segment addresses, `ARM:LE:32:v8` with the default compiler profile, ELF relocations enabled and external library loading disabled. The language profile is Ghidra's decoder selection, not independent proof of the device CPU model. Imported external symbols remain abstractions; the project contains the main executable without library implementations.

## Original firmware and evidence

The [read-only import copy] `input/EP085_Main_R` (evidence not published) matches `decode/output/image2/payloads/pdj/pdj/EP085_Main_R`: **12,000,396 bytes**, SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`. `decode/README.md` maps image2 to 1.60, and `decode/output/image2/iso/images/release.txt` contains `1.60`. [Provenance] `provenance.json` (evidence not published) and [independent ELF verification] `exports/independent-static-verification.json` (evidence not published) record those checks. All **81** prior lifecycle address/byte pairs also match Ghidra's imported memory: [verification] `exports/mapped-byte-verification.json` (evidence not published).

Original update files, extracted application/libraries, historical runtime and completed experiment files were not edited. The [selected preservation receipt] `preservation-selected.json` (evidence not published) compares the original application, both updates and the consulted completed handoffs/maps before and after analysis; it is not a whole-history preservation audit. Ghidra relocation modeling changes its project representation of external references, not the source or import-copy bytes.

## Verified static control flow

“Verified static” means supported by original instruction bytes, ELF metadata or symbol/relocation records. It does not mean observed execution.

| Boundary | Evidence and consequence |
| --- | --- |
| Mapped main entry `0xb3ac4` | Stores factory `0x56e7bc` at global `0xf6e680`, then branches through `0xb40cc` into `0xb4034`. The entry is not a distinct `.ARM.exidx` start; unwind records may cover multiple functions. |
| Main call `0xb405c` | Loads object vtable slot `+0x30`. The factory stores vtable address point `0x9327f0`, whose slot is `0x7552b0`. That thunk branches to wrapper `0x69850c`, retaining caller continuation `0xb4060`. This resolution depends on the concrete receiver/vtable. |
| Wrapper call `0x698544` | Calls slot `+0x14`; the mapped vtable contains initializer `0x571d24`. Its mapped caller continuation is `0x698548`. |
| Initializer normal epilogue `0x57222c` | Restores nine saved registers after adding `0x9c` to SP. The mapped wrapper resumes at `0x698548`; it does not test the initializer's returned r0 as a success flag. |
| Wrapper normal epilogue `0x6985a4` | Shared by success and zero-return paths. Main compares r0 at `0xb4060`; only nonzero takes the branch at `0xb4068` to `0xb4090`, then calls dispatch at `0xb4094 → 0x69afc0`. |
| Dispatch `0x69afc0` | Contains imported `XPending` and `XNextEvent` calls. Its presence establishes an event-dispatch implementation, not live entry into that loop. |

[Original focused disassembly] `exports/focused-original-disassembly.txt` (evidence not published) and the address-named `*.asm.txt`/`*.json` exports support this chain. Incoming-reference lists include code and data references; a vtable pointer is not a demonstrated direct caller, and absent direct call references do not exclude indirect callers.

The wrapper has an early alternate rejection path at `0x6985a8 → 0x6985b8 → 0x6985a0`. For the saved concrete application vtable, however, its slot `+0x10` is `0x56e8ec`, which returns constant `1`; that concrete route bypasses the early rejection test. After the initializer returns, a nonzero manager byte at offset `+4` makes `0x698570` return zero through the same epilogue. Thus a return receipt alone cannot establish the success-side dispatch route. Exception cleanup calls to `__cxa_end_cleanup` are separate from these normal returns.

Inside the initializer, `0x571e90` sets a 30-pass counter. Each pass performs six indirect status calls after indexed lookups. The code requests an initial 30 ms sleep and up to thirty additional 1 ms sleeps through `0x6457dc`, whose original implementation calls `nanosleep`. This limits the local retry count if its callees return; it imposes no total startup deadline and identifies no runtime delay cause. Controller/status identities remain inferred.

The initializer passes `800` and `480` to `0x79be58` at `0x572120`; interpreting that callee as geometry setup is inferred from its implementation. At `0x5721e0`, the original PLT symbol is `statvfs` and the path bytes are `/mnt/emmc/`. Filesystem capacity values and the actual branch taken are unverified. [Focused facts] `exports/focused-static-facts.json` (evidence not published).

## Inferred pseudocode and retained analysis failure

Every `*.inferred.c` export is explicitly labeled **inferred pseudocode**. Parameter types, signatures, object names, indirect-call targets and high-level intent can be incomplete or wrong. Start with [initializer pseudocode] `exports/00571d24.inferred.c` (evidence not published), [wrapper pseudocode] `exports/0069850c.inferred.c` (evidence not published) and [main body pseudocode] `exports/000b4034.inferred.c` (evidence not published), checking the corresponding disassembly.

The initial import disabled relocations to compare raw bytes. Unresolved PLT stubs then collapsed onto the lazy resolver and acquired erroneous non-returning inference, truncating the initializer immediately after allocation/guard calls. That pass's “decompile completed” flags did not make its pseudocode usable. Its project `projects/SP16_1_60.gpr`, [logs and exports] `runs/initial-unrelocated/` (evidence not published) are retained. The active project enables ELF relocations and requires the initializer body to contain its independently verified normal epilogue before export. The allocator, guard acquire, XPending, statvfs and nanosleep imports now resolve to separate external symbols with returning semantics. Ghidra excludes some exception-only tails from its recovered function bodies; the focused original disassembly retains those regions.

The corrected import/export took **174.465 seconds**, identified **17,982 function candidates**, exported **26 selected functions** with completed decompilations, and saved successfully without hitting the 900-second analysis ceiling. This is not whole-binary validation. Invalid PNG/GIF heuristic diagnostics and pcode-flow warnings at `0x100234` and `0xff008` remain in the logs; the selected startup exports completed. These are static analyzer diagnostics, not firmware runtime faults.

## Commands and next static question

[Effective headless command] `logs/command.json` (evidence not published), [result] `logs/result.json` (evidence not published), raw [stdout] `logs/headless.stdout.txt` (evidence not published) and [stderr] `logs/headless.stderr.txt` (evidence not published), [function index] `exports/function-index.json` (evidence not published) and [validation] `validation.json` (evidence not published) describe the completed import/export. Scripts and Ghidra settings/cache/temp directories are contained here. [run_headless.py] `run_headless.py` (evidence not published) records the import; it refuses to overwrite an existing project. For further exports, process the saved project with `-process EP085_Main_R -noanalysis -readOnly`, the script path here, and `PioneerStartupExport.java` with a **fresh output directory** and the preserved lifecycle map as its two arguments.

**Next static question:** resolve the initializer's indirect status callees and the post-initializer manager flag's writers, then check whether nested initialization can reach the same dispatch routine. No exhaustive transitive call graph or runtime completion claim is established. The existing runtime prompt remains a separate authorization path; this setup does not activate it.
