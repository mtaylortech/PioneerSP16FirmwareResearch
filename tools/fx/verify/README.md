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
| `H021`, `H023`, `H026`, `H028`, `H031` | LoFi, multi-mode filter, 2-band EQ, Phaser, oscillator vs the models (`H026` updated for the PEQ reset) | F026–F056 |
| `H033`, `H034`, `H035`, `H039`, `H040`, `H041` | Chorus, Flanger, Distortion, Insert Delay, Compressor, Ducker vs the models | F057–F094 |
| `H043`, `H005` | Send/Master Delay and Reverb vs the models | F080, F115–F127 |
| `H064_perf_fx.py` | Performance-FX LoFi: never constructed; model | F128–F131 |
| `H006_fx2_routing.py` | FX2 on Sample/Thru tracks: 1.50 → 1.60 masked function comparison (needs a 1.50 ELF too) | F132–F137 |
| `H011_effect_interface.py`, `H044_effectbase_wrapper.py` | EffectBase interface, no factory; slot-18 wrapper vs `effectbase.py` | F138–F149 |
| `H076_slot27_reset.py` | Slot-27 resets of LoFi, MMF, PEQ; 13/13 effects end to end | F150–F153 |
| `H077_master_send_proc.py`, `H027_master_mmf.py`, `H020_send_fx_types.py` | Master/Send processors vs `fx_processors.py`; Master/Send MMF; Send FX types | F154–F158, F173–F175 |
| `H004_fxparam_map.py`, `H083_enum_defaults.py`, `H086_ui_manager_calls.py` | FxParamIndex → slot 14; enum converters and `prj::EffectData` defaults; UI reach | F159–F172 |
| `H079_fx_onoff.py`, `H079_r2_propagate.py`, `H080_bypass_sources.py` | `+0x9d` start mode (dormant); Insert bypass sources | F176–F182 |
| `H082_sync_convert.py`, `H082_step_mode.py` | SYNC conversion vs `sync_convert.py`; UI step law, SHIFT | F183–F186 |
| `H009_track_mix.py`, `H010_send_bus.py`, `H052_dsf_loop.py` | Track mixing, send bus and master chain, analog-filter loop vs the mixer models | F095–F108, F187–F191 |
| `H055_device_out.py`, `H057_headphone.py` | Device output stage; headphone router and main-output selector | F109–F114, F209–F213 |
| `H049_rtti.py`, `H049_vcall_scan.py`, `H049_trigger_senders.py`, `H050_trigger_host.py`, `H050_r2_checks.py` | Ducker trigger senders and host rule (static census + emulation) | F192–F201 |
| `H038_fpscr_census.py` | FPSCR writers in the main binary, its libraries and the thread start path | F202–F205 |
| `H029_libm_exact.py` | `crmath` / fdlibm ports vs the emulated 1.60 libm | F206–F208 |
| `lib/emu.py`, `lib/sp16img.py`, `lib/darwin_ctr_fix.py` | emulator, static image helper, macOS host shim | — |
| `lib/armflow.py`, `lib/symwalk.py` | static ARM flow helpers and symbol/vtable walker used by the newer scripts | — |

## Environment variables (three scripts)

Two scripts had a constant that pointed into a private folder of the research host. In
the published copies that constant reads an environment variable instead (logged in
[research-notes/EDIT-LOG.md](../../../research-notes/EDIT-LOG.md)); nothing else in those
scripts was changed.

| Variable | Script | What to point it at | If unset |
|---|---|---|---|
| `SP16_APP150_ELF` | `H006_fx2_routing.py` | your own 1.50 application ELF (SHA-256 checked by the script) | falls back to `tools/fx/target/app-1.50.elf`; exits with a message if that does not exist |
| `SP16_CLASSES_XVER_CSV` | `H006_fx2_routing.py` | `symbols/classes-crossversion.csv` of this repository | falls back to that file (found relative to the script); exits with a message if missing |
| `SP16_IMAGE2_LIBDIR` | `H038_fpscr_census.py` | the `lib/` folder of your own 1.60 root filesystem, for libraries missing from `decoded/lib/` | falls back to `tools/fx/decoded/image2-lib`; if that does not exist, those libraries are reported as absent |

The docstrings of the newer scripts mention research cycle logs (`kb/cycles/…`) and
output folders (`harness/out/…`) of the research workspace. Those are not published;
the conclusions are in the docs and the findings ledger.

Not published: the SHA-256 of the 1.60 `libm.so.6` / `libgcc_s.so.1` (the harness prints them at run time).
