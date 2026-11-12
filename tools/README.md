# tools/

All code here is MIT-licensed project work. **No firmware and no key are
included.** Scripts marked "original" are published unchanged (apart from a
provenance header) and depend on the original research folder layout; they
are here so you can see exactly how results were produced.

| Path | What | Runs standalone? |
|---|---|---|
| `decode/upd_decrypt.py` | Decrypt a `.UPD` to its ISO. See `decode/README.md`. | **Yes** (any OS, `cryptography`) |
| `decode/decode.py` | Original full decoder/extractor/auditor. | No — macOS + research layout |
| `firmware/corpus.py` | Original six-release catalog query/build tool. | No — needs unpublished local inventories |
| `firmware/extract.py` | Original hardened per-release extraction entry point. | No — research layout |
| `firmware/ghidra/*.java` | Ghidra scripts for the 1.30→1.31 function-correspondence pilot. | In Ghidra, with your own 1.30/1.31 binaries |
| `ghidra/*.java` | Ghidra scripts from the 1.60 startup / Send-widget static analysis. | In Ghidra, with your own 1.60 binary |
| `contracts/slice_contracts.py`, `trace_records.py` | ARM32 partial-layout contract checker and trace-record helper (methodology). | Yes (stdlib), with your own trace data |
| `normalization/` | Host-side WAV peak normalizer, independent oracle, 278-check synthetic fixture suite. See `normalization/README.md`. | **Yes** (Python stdlib) |

Labels and the import script for Ghidra are in `../symbols/`.

## Not included, and why

- **The QEMU / Qiling / Unicorn emulation harness.** It was built around
  copies of the firmware root filesystem, patched third-party tool trees
  (QEMU 10.0.14, GLib, XQuartz) and many one-off launchers with hardcoded
  paths. Publishing it would mean publishing firmware-derived disk images and
  large third-party trees. `docs/findings.md` describes what it achieved and
  how, so it can be rebuilt; this is listed as a gap in `docs/open-questions.md`.
- **The macOS Normalize preview/Keep prototype and the firmware-side
  reader/cache fixtures.** They depend on original ARM code bytes or the
  emulation harness. Their results are written up in `docs/findings.md`.
