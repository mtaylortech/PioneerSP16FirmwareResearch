# Notice — what is licensed, and what is not

## The contributors' own work

| Material | License |
|---|---|
| Original code: `tools/**`, `emulation/**` and `symbols/*.py`, `symbols/*.java` (everything in `tools/fx/` except the one file below) | MIT — see [LICENSE](LICENSE) |
| `tools/fx/glibc_expf.py` only: own re-implementation of the glibc 2.13 `e_expf.c` algorithm, distributed under the LGPL because of that origin; its accurate tables are **not** included (read at run time from the user's own 1.60 `libm.so.6`) | LGPL-2.1-or-later — see [LICENSE-LGPL-2.1](LICENSE-LGPL-2.1) |
| Original prose: `README.md`, `NOTICE.md`, `DISCLAIMER.md`, `CONTRIBUTING.md`, `docs/**`, and the prose in each `README.md` | CC BY 4.0 — see [LICENSE-docs](LICENSE-docs) |
| The label data `symbols/labels-1.60.{json,csv}`, `symbols/annotations-reviewed-1.60.json`, `symbols/partial-structures-1.60.txt`, `symbols/fx-functions-1.60.csv` (names, addresses, types inferred by the analysts) | CC BY 4.0 |

These licenses cover **only** material this project's contributors authored, and
grant no rights the contributors do not have.

## Third-party notice kept in project code

`tools/fx/fdlibm_powf.py`, `tools/fx/fdlibm_tanf.py` and `tools/fx/fdlibm_sincosf.py`
are Python transliterations of the public fdlibm single-precision algorithms, as
shipped in glibc 2.13. `tools/fx/glibc_log10.py` is an own re-implementation of the
fdlibm double-precision `e_log10.c` algorithm (as shipped in glibc 2.13) on top of a
correctly rounded natural log. `tools/fx/ducker.py` contains an own port of the fdlibm
float `e_log10f.c` / `e_logf.c` algorithms (glibc 2.13). None of them contains firmware
bytes. The fdlibm notice, which each of these files repeats and which must be preserved:

> Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
> Developed at SunPro, a Sun Microsystems, Inc. business.
> Permission to use, copy, modify, and distribute this software is freely granted,
> provided that this notice is preserved.

The single-precision conversion is credited to Ian Lance Taylor, Cygnus Support. The
project's own changes to these files are MIT. `tools/fx/crmath.py` is the project's own
code (high-precision series in Python's `decimal` module), with no third-party source.

`tools/fx/glibc_expf.py` (LGPL-2.1-or-later, see the table above) carries its own
licence header.

The effect models do **not** include three firmware-derived tables: the 8192-entry
table that the oscillator's random waveform reads from the firmware's `.data`, the
glibc `expf` accurate tables of the 1.60 `libm.so.6`, and the 1024-entry OutputVolume
table of `EP085_Main_R`. Users supply them from their own copy of the firmware (see
`tools/fx/README.md`).


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
