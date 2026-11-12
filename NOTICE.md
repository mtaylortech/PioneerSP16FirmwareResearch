# Notice — what is licensed, and what is not

## The contributors' own work

| Material | License |
|---|---|
| Original code: `tools/**`, `emulation/**` and `symbols/*.py`, `symbols/*.java` | MIT — see [LICENSE](LICENSE) |
| Original prose: `README.md`, `NOTICE.md`, `DISCLAIMER.md`, `CONTRIBUTING.md`, `docs/**`, and the prose in each `README.md` | CC BY 4.0 — see [LICENSE-docs](LICENSE-docs) |
| The label data `symbols/labels-1.60.{json,csv}`, `symbols/annotations-reviewed-1.60.json`, `symbols/partial-structures-1.60.txt` (names, addresses, types inferred by the analysts) | CC BY 4.0 |

These licenses cover **only** material this project's contributors authored, and
grant no rights the contributors do not have.

## Material NOT covered by those licenses

- **Pioneer DJ / AlphaTheta firmware, software, assets, manuals, and
  trademarks.** None of it is included here. It is referenced by version and
  SHA-256 only. All rights remain with the rights holder.
- **The disassembly / decompiled listings** in `symbols/listings/`
  (`*.asm.txt`, `*.inferred.c`). These are derived from Pioneer's copyrighted
  program and are published as research commentary and for interoperability
  study, not under MIT or CC BY. See [DISCLAIMER.md](DISCLAIMER.md).
- **The GPL/BSP open-source components** shipped inside the firmware (Linux,
  U-Boot, BusyBox, ALSA, GStreamer, and others). Each keeps its own upstream
  license. Per-package license/attribution pages for these components are not
  reproduced in this repository; consult the upstream projects and the
  manufacturer's own open-source disclosure.
- **Third-party tools** used during the research (Ghidra, QEMU, Qiling/Unicorn,
  Capstone, pyelftools, pyfatfs, an X server, and others). Not included; each
  has its own license. The emulators call stock, unmodified QEMU and Qiling
  (Qiling and QEMU are GPL-2.0).

## Trademarks

"Pioneer", "TORAIZ", and "SP-16" are trademarks of their respective owners and
are used here only to identify the product studied (nominative use). No
affiliation or endorsement is implied.
