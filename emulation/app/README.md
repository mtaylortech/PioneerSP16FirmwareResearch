# emulation/app — original 1.60 application emulator (REFERENCE CODE)

> **This is reference code. It will not run as-is.** It is the exact harness
> that produced the research's application-emulation results, published so a
> skilled successor can see *how* it was done and adapt it. Host paths have
> been replaced with `<RESEARCH_ROOT>` / `<HOME>` placeholders, the guest
> filesystem is not included, and it was built on macOS. Read
> [../../DISCLAIMER.md](../../DISCLAIMER.md).

## What it achieved (emulator only)

Pioneer's unchanged firmware 1.60 sampler application (`EP085_Main_R`,
SHA-256 `3d1392a6…`) running in **user-mode ARM emulation** (Qiling on
Unicorn), with its own original libraries, against a real X server:

- **Startup:** the application initializer (`0x571d24`) returned and main
  dispatch (`0x69afc0`) was reached at about **262 s**; the first stable
  **800×480 HOME** screen was captured at about **285 s** and stayed
  pixel-identical through a 600 s observation.
- **Input:** one tagged TRACK-2 click was consumed by original handling and
  changed the selection; a tagged HOME→MIXER tap produced the 16-fader Mixer.
- **Audio threads:** the original ALSA library opened playback/capture through
  a *null* PCM plugin and kept writing/reading — API activity, not audio.

Limits: this is not a board, not a kernel, and not a playable sampler. Audio,
devices, timers and some syscalls are substituted; the baseline's timing
semantics are known to be defective; threads are scheduled cooperatively; a
stop at the deadline is not a clean shutdown. See `docs/findings.md`.

## How it works

`run_once.py` → `probe.py` loads the ARM ELF from a guest root filesystem with
Qiling and installs fixtures and sparse observers. The important adaptations,
each found by a failure documented in the research:

| Problem in the emulator | Fix in the harness |
|---|---|
| Original loader could not find `libX11.so.6` | expose the guest's `/usr/lib/*.so*` at `/lib/*` (`--library-aliases`) |
| Heap growth collided with the dynamic loader | relocate the loader to `0x70000000` (`--high-loader`) |
| No `hw:ak4458audio` device → app read address 0 | map `alsa-null.conf` so ALSA uses its null PCM plugin (`--null-audio`) |
| Null capture opens `/dev/full` | provide regular files for `/dev/null` (empty) and `/dev/full` (64 KiB of zeros) |
| ARM TLS register handling | `--correct-arm-tls` |
| X11 display | a host X server (Xvfb from an XQuartz package on macOS) reached through a socket fixture (`local_display.py`, `--local-display`) |
| Startup stalled under default scheduling | cooperative main-thread execution (`--cooperative-main`) with `--post-font-count 313370` |
| `sched_setaffinity` | recorded and returned `ENOSYS` (requested core placement is logged, not enforced) |
| `vfork` | deliberately denied as a safety guard (not a firmware failure) |

Observers (`*_observer.py`) hook specific original addresses to record
milestones; several check a few **original instruction bytes** before
installing a hook, so a wrong binary is refused. Every address is valid **only**
for the 1.60 binary above.

The last successful run used:

```
python -B -u run_once.py --seconds 600 --cooperative-main --post-font-count 313370
```

## Files

```
reference/harness/    the run folder minus the guest filesystem: the prepared
                      seed with the later lifecycle overlay applied on top
                      (probe.py, run_once.py, postflight_native.py,
                      supervision/ were replaced; lifecycle_observer.py,
                      async_readiness.py, lifecycle-map.json and
                      lifecycle-validation.json were added), exactly as the
                      research assembled it
reference/launcher/   how one live run was prepared and launched
                      (prepare_run.py, launch_run.py), checked (verify_result.py)
                      and previewed (xwd_preview.py)
```

`plt-symbols.json` is the application's import table (names → PLT addresses),
`xlib-layout.json` the X11 structure offsets the observers rely on, and
`static/mapping.json` address bindings from static analysis.

## What you would need to adapt

1. **Guest root filesystem** from your own decoded 1.60 firmware: extract
   `rootfs1..4.tar.gz`, copy the SquashFS contents to `/usr/bin`, `/usr/lib`,
   `/usr/share`, and extract `pdj.tar.gz` under `/root` (the application lives at
   `/root/pdj/EP085_Main_R`). Place it at `harness/rootfs/`. Mind the file-mode
   caveat in `docs/firmware-format.md`.
2. **Fixtures:** create `harness/null-device` (empty) and `harness/full-device`
   (65,536 zero bytes).
3. **Python 3.10** with **Qiling 1.4.6, Unicorn 2.1.4, Capstone 5.0.9,
   pyelftools 0.33** (and gevent). Qiling's eager Keystone import may fail; the
   harness has a fallback for that.
4. **An X server** with `xkbcomp` (the research used Xvfb from an XQuartz
   package; `xkbcomp-wrapper.sh` shows the library-path shim it needed), and
   replace every `<RESEARCH_ROOT>` / `<HOME>` placeholder.
5. Expect to debug: the harness was only ever run on one macOS machine. On
   Linux, native Xvfb and different library versions will need small changes.
   Unicorn crashed with SIGILL under a restricted sandbox on macOS in the
   research; it ran normally outside it.

## Licensing

The harness is the project's own code (MIT). It **imports** Qiling
(GPL-2.0), Unicorn, Capstone and pyelftools, none of which are included. The
Qiling installation used by the research was verified unmodified (all 683
installed files match pip's record). If you redistribute this harness together
with Qiling, consider the GPL's terms for the combination. A few original
instruction-byte guards appear in the observers (see DISCLAIMER.md on
firmware-derived material).
