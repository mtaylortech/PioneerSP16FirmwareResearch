# emulation/

Two independent ways the research ran Pioneer's original SP-16 software in
emulation. Neither is a working instrument; both run only in software and never
touch hardware. Read [../DISCLAIMER.md](../DISCLAIMER.md).

| Folder | What | Firmware | Status |
|---|---|---|---|
| [`board/`](board/) | Original kernel + root filesystem under stock QEMU (`sabrelite` i.MX6 board): boots through init and launches the app, stopping at a known missing-audio / SIGSEGV / missing-MTD checkpoint | 1.50 | **Runnable**, config-driven, rebuilds everything from your own decoded firmware |
| [`app/`](app/) | The sampler application alone in user-mode emulation (Qiling/Unicorn) with a real X server: startup to a stable HOME screen, TRACK and MIXER input | 1.60 | **Reference code only** — the exact research harness, not runnable as-is |

Both require firmware you obtain yourself and decode with
[`../tools/decode/upd_decrypt.py`](../tools/decode/upd_decrypt.py). Nothing
derived from firmware is included here: no disk images, root filesystems, or
binaries.
