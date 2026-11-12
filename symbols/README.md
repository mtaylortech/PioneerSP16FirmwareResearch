# symbols/ — analyst labels and disassembly for EP085_Main_R (firmware 1.60)

Everything here applies to **one exact binary**:

| Field | Value |
|---|---|
| File | `EP085_Main_R` (main sampler application, from `pdj.tar.gz` in the update) |
| Firmware | 1.60 (app `Rev.6550`) |
| Size | 12,000,396 bytes |
| SHA-256 | `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464` |
| Ghidra language / base | `ARM:LE:32:v8`, image base `0x8000`, ARM (not Thumb) for the listed routines |

**Addresses are wrong for every other firmware version.** Version 1.50's
application (`075cff7a…`) differs; do not apply these labels to it.

## Files

| File | What it is |
|---|---|
| `labels-1.60.json` | 136 labels (75 functions/labels + 61 resolved imports), with priority, rationale, alternate names seen in earlier passes, and the research file each came from. |
| `labels-1.60.csv` | Same, as CSV. |
| `labels-1.60.ImportSymbolsScript.txt` | `name address` lines for Ghidra's stock `ImportSymbolsScript.py` (imports omitted). |
| `annotations-reviewed-1.60.json` | 26 reviewed annotation entries (22 distinct addresses; some addresses were annotated twice) with written rationale. These are the priority-1 labels. |
| `partial-structures-1.60.txt` | Partial analyst views of `LiveSamplerApplication`, `MessageManager`, `MessageQueue` and others. Unknown offsets are left undefined. |
| `SP16ImportLabels.java` | Ghidra script (plain Java, no Python setup): checks the program SHA-256, then applies the labels and rationale comments. Works in the GUI and headless. **Tested** 2026-11-11 with Ghidra 12.1.4. |
| `listings/` | 512 files for 256 functions: `<addr>.asm.txt` (disassembly) and `<addr>.inferred.c` (decompiler pseudocode), plus `index.json` with each file's provenance and hash. |

## How confident are these names?

- Every name is **inferred**. None is an original source name. The binary is
  stripped; names come from RTTI strings that survive in the binary (e.g.
  `LiveSamplerApplication`, `UIThread`, `MainWindow`, `ControllerDataManager`),
  diagnostic strings (e.g. `Settings::Settings()`), imported-library calls, and
  behaviour.
- **Priority 1** (22): reviewed annotations with a written rationale.
- **Priority 2**: names from the final refined export pass.
- **Priority 3**: names from parallel investigation rounds (UI paths, Send
  widget, input routes). Treat as working hypotheses.
- Names carry the address as a suffix (`sp16_initialise_00571d24`) so a wrong
  guess can be renamed without losing the anchor.
- `juce_*` names reflect that the app's message loop and window handling look
  like the JUCE C++ framework on X11. This is an interpretation from structure
  and call patterns, not a confirmed library identification.
- Function prototypes/signatures in the pseudocode are analyst conventions.

## How to use

1. Obtain firmware 1.60 yourself from the official source (see
   `docs/firmware-reference.md`) and extract `EP085_Main_R` with
   `tools/decode/`. Check its SHA-256 matches the table above.
2. In Ghidra: import it as ELF, language `ARM:LE:32:v8`, base `0x8000`, and
   run auto-analysis. The original project enabled ELF relocation modelling and
   disabled library loading; enabling relocation modelling avoids a wrong
   PLT/no-return inference that was hit early on.
3. Add this folder to Ghidra's script directories (Script Manager → Manage
   Script Directories), run `SP16ImportLabels.java` and select
   `labels-1.60.json`. Headless:
   ```sh
   analyzeHeadless <project_dir> <project_name> -import EP085_Main_R \
       -scriptPath /path/to/symbols \
       -postScript SP16ImportLabels.java /path/to/symbols/labels-1.60.json
   ```
   Alternatively, Ghidra's stock `ImportSymbolsScript.py` accepts the `.txt`
   file (names only, no comments; needs Ghidra's Python support).

**Tested result (2026-11-11, Ghidra 12.1.4, fresh import + full
auto-analysis):** all 75 non-import labels applied and verified at their
addresses, all 22 rationale comments present, 0 failures. Only 17 of the 75
addresses are function entries after stock auto-analysis; the other 58 are
applied as plain labels. The research created many of those functions by
hand. If you want them as functions, create a function at the label (Ghidra:
`F`) and the name carries over.

## About the listings — rights notice

The `listings/` files are machine output derived from Pioneer's copyrighted
program. They are published as research commentary and to support
interoperability study. **They are not covered by this repository's MIT or
CC BY 4.0 licenses.** You can regenerate them from your own copy of the
firmware with the steps above. See `../DISCLAIMER.md`.

## What is missing

- The native Ghidra project (with its types, comments and three partial
  structure types) is **not** included: native databases embed the firmware.
  Everything portable from it is in this folder.
- No labels yet for firmware 1.50, even though some research (Normalize reader
  cache, USB/updater) used 1.50. Those projects exist only as native databases
  in the original research; exporting their symbols is an open task.

---

## Class map (new): `classes-1.50.*` + `extract_architecture.py`

In addition to the hand-reviewed labels above, this folder now ships a
**machine-recovered class map** of the application, for **both 1.50 and 1.60**
(the 1.50 files are shown below; 1.60 files use the same layout with a `-1.60`
suffix). The class set is identical between the two releases — only addresses
differ:

- `classes-1.50.md` — 124 application classes grouped by subsystem, each with
  its vtable address, first virtual-method address, and counts. Human-readable.
- `classes-1.50.csv` — the same as a table.
- `classes-1.50.json` — the full machine-readable map, including every
  recovered **demangled method signature** per class and all virtual-method
  addresses.
- `extract_architecture.py` — the standalone, path-free regenerator.

**How it works.** `EP085_Main_R` is a stripped JUCE C++ program, but its
run-time type information (RTTI) survives: each polymorphic class leaves its
mangled `type_info` name in `.rodata`. The script demangles those names
(`c++filt`) and walks `type_info → vtable` to recover virtual-method entry
addresses, which were spot-checked against ARM function prologues. It reads the
binary **read-only** and emits only names and addresses — **no firmware bytes**.

**Regenerate (e.g. for 1.60 or another release):**

```
python3 extract_architecture.py /path/to/your/EP085_Main_R out_dir/
```

It parses the ELF program headers itself, so it is not hard-wired to one
release — but **every address it prints is specific to the binary you feed it.**
Do not reuse a 1.50 address on another version.

See [`../docs/architecture.md`](../docs/architecture.md) for the narrative map,
including the MIDI clock/sync path.

**Which binary is which (verified against `firmware/catalog.json`):**

| Release | `EP085_Main_R` size | SHA-256 (head) | mapped here |
|---|---|---|---|
| **1.50** | 11,993,612 | `075cff7a…` | yes — `classes-1.50.*` |
| **1.60** | 12,000,396 | `3d1392a6…` | yes — `classes-1.60.*` |

`labels-1.60.json` and the `listings/` legitimately describe the **1.60** binary
(`3d1392a6…`); the class map here is the **1.50** binary (`075cff7a…`).
