# tools/fx/verify — effects emulation harness (REFERENCE CODE, research layout)

The scripts that produced the "bit-exact" results in [`../../../docs/effects/`](../../../docs/effects/README.md):
single-function unicorn emulation of the original 1.60 routines, compared sample by sample with the models in
[`../`](../README.md). Published **unchanged** from the research workspace (MIT). They contain **no firmware
bytes**; every script reads your own files and checks the `EP085_Main_R` SHA-256
(`3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`) first.

**Not re-tested in this layout.** They ran on the research host (macOS and Linux) in a different folder layout:

- Put your own 1.60 files at `tools/fx/target/EP085_Main_R_fw160` and `tools/fx/decoded/lib/` (`libm.so.6`,
  `libgcc_s.so.1` from the same release's root filesystem). Both folders are git-ignored. **Never commit them.**
- The verifiers import the models from a `models/` folder; run with `PYTHONPATH=tools/fx`.
- Install `pip install -r tools/fx/verify/requirements.txt` (unicorn 2.1.4 was used). On macOS inside a
  restricted sandbox, `lib/darwin_ctr_fix.py` is needed (see the docs).
- **Always pass `--out` to a folder outside the repository.** `H001_disasm.py` / `H002_disasm.py` write
  disassembly of firmware functions there; that output must never be committed.
- Usage strings mention `.venv/bin/python harness/…`; read them as `python3 tools/fx/verify/…`.

Example: `PYTHONPATH=tools/fx python3 -B tools/fx/verify/H021_lofi_model.py --out /tmp/h021` — should end
`RESULT: 0 failed checks`.

| Scripts | Checks | Findings |
|---|---|---|
| `H001_*.py` | RTTI / vtable recovery | F007–F011 |
| `H002_*.py` | ALSA imports and audio call chain (168 assertions) | F012–F015 |
| `H013_fx_array.py` | FX processor effect arrays (26 assertions) | F016–F019 |
| `H007_effect_emu.py` | LoFi end to end, activation, dry/wet, post-stage | F020–F025 |
| `H021`, `H023`, `H026`, `H028`, `H031` | LoFi, multi-mode filter, 2-band EQ, Phaser, oscillator vs the models | F026–F056 |
| `lib/emu.py`, `lib/sp16img.py`, `lib/darwin_ctr_fix.py` | emulator, static image helper, macOS host shim | — |

Not published: the SHA-256 of the 1.60 `libm.so.6` / `libgcc_s.so.1` (the harness prints them at run time).
