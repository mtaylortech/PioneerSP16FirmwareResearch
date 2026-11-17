# TORAIZ SP-16 firmware research

Reverse-engineering notes, tools, and symbols for the **Pioneer DJ TORAIZ
SP-16** sampler. This is an ongoing, independent research project into the
SP-16's firmware and internal architecture. Findings are published here openly,
with confidence labels, as the work progresses.

The research may make future tools, firmware modifications or other
developments possible, but none is guaranteed: there is no committed schedule,
and a complete custom firmware release may never happen. This is research, not
a product. If you find it useful, you can
[support the research](#support-the-research).

> **No Pioneer firmware, keys, or binaries are in this repository.** Firmware is
> referenced by version and SHA-256 only. **Read [DISCLAIMER.md](DISCLAIMER.md)
> before using anything here** — everything is provided as-is, at your own risk,
> and this is not legal advice.

## What this is (and isn't)

It **is**: a verified description of the firmware update format and a portable
decoder; a six-release hash catalog; analyst symbols for the 1.60 application;
an honest, confidence-labelled account of what was and wasn't learned about
boot, UI, "Normalize", and USB/updater behaviour; a working host-side WAV
normalizer; reconstructions of the 1.60 audio engine (all twelve live effects, the shared
`EffectBase` wrapper, the FX processors, the mixer, the buses, the output stage and the
headphone router), with Python models bit-exact to the 1.60 routines run in a
single-function emulator; and reusable methods.

It **isn't**: recovered application source, a replacement OS, deployable
modified firmware, or anything tested on real hardware. Most dynamic findings
come from emulation and are labelled as such.

## Start here

- [docs/findings.md](docs/findings.md) — what was learned, each with a
  confidence label. **Read the labels literally.**
- [docs/firmware-format.md](docs/firmware-format.md) — the `.UPD` format.
- [docs/project-format.md](docs/project-format.md) — **the project & sample file format, CONFIRMED** against a real `.prj`: `vltrgzip`+zlib JUCE ValueTree, 31 node types with real field names, plus a working parser ([tools/project/parse_project.py](tools/project/parse_project.py)). The route to reading/editing SP-16 projects on a computer.
- [docs/midi-implementation.md](docs/midi-implementation.md) — **MIDI implementation chart** (send/receive, the 35-CC map, ports/sync), compiled from Pioneer's 1.60 addendum and cross-confirmed against the firmware's `MidiSettingData`/`MidiCc` data.
- [docs/firmware-reference.md](docs/firmware-reference.md) — versions + hashes +
  where to get firmware.
- [docs/hardware.md](docs/hardware.md) — hardware facts, access leads, and risk.
- [docs/storage.md](docs/storage.md) — **how the unit stores and moves files:** NAND vs eMMC, USB storage mode, the eMMC layout and first-boot format, how saving/moving/resume work, and what a failed save looks like (1.50; 1.60 identical).
- [docs/architecture.md](docs/architecture.md) — **application class maps (1.50 & 1.60):** the sequencer, sampler, MIDI/sync and project-file subsystems recovered from the binary, with the MIDI clock/sync path written up in detail. Backed by [symbols/classes-1.50.md](symbols/classes-1.50.md) and [symbols/classes-1.60.md](symbols/classes-1.60.md).
- [docs/effects/](docs/effects/README.md) — **how the 1.60 audio engine and effects work:** a status table of every Insert/Master/Send effect and mixer stage, the [signal flow](docs/effects/signal-flow.md) from track to DAC and headphones, the `EffectBase` wrapper, the FX processors, parameter plumbing and numerics, and one page per effect (Chorus, Flanger, 2-band EQ, multi-mode filter, Insert Delay, Send Delay, Reverb, LoFi, Distortion, Compressor, Phaser, Ducker, shared oscillator), each with a bit-exact Python model in [tools/fx/](tools/fx/README.md) (start with its quickstart).
- [docs/version-evolution.md](docs/version-evolution.md) — **what changed between firmware 1.20→1.60**, recovered from the binaries: which classes/features each release added (AS-1 in 1.30, copy/swap/undo in 1.40, live sampling in 1.50), with a per-version address matrix ([symbols/classes-crossversion.csv](symbols/classes-crossversion.csv)).
- [docs/open-questions.md](docs/open-questions.md) — where it stopped and the
  next steps.
- [emulation/](emulation/) — run the original 1.50 kernel and rootfs in stock
  QEMU, and the reference harness for the 1.60 application emulator.

## Layout

```
docs/        findings, firmware format, firmware reference, hardware, storage,
             effects/ (1.60 FX), open questions
tools/       decode/ (portable + original decoder), firmware/ (catalog + Ghidra
             pilot scripts), ghidra/ (1.60 analysis scripts), normalization/
             (host WAV normalizer), contracts/ (ARM32 trace helpers),
             fx/ (pure-Python models of the 1.60 effects and mixer, plus
             verify/, the emulation harness as reference code)
emulation/   board/ (runnable 1.50 QEMU board emulator) and app/ (reference
             code for the 1.60 application emulator)
symbols/     inferred labels for EP085_Main_R 1.60 (JSON/CSV), reviewed
             annotations, partial structs, disassembly + pseudocode listings for 256
             functions, an FX function/address table (fx-functions-1.60.csv),
             and a Ghidra import script
research-notes/  scrubbed lab notes behind the findings: ~90 experiment
             write-ups by thread, engineering reviews, project history,
             reusable methods, a cross-cutting LESSONS.md, and F-effects/
             (the effects findings ledger)
```

## Research notes

[`research-notes/`](research-notes/) holds the raw, scrubbed lab notes behind
the curated docs: what was tried, what held up, and where each thread stopped.
Start with [`research-notes/README.md`](research-notes/README.md) for the
thread-by-thread index and
[`research-notes/LESSONS.md`](research-notes/LESSONS.md) for the transferable
lessons and dead ends. Every note was path- and identity-scrubbed; links to
unpublished evidence are marked as such
([EDIT-LOG](research-notes/EDIT-LOG.md),
[LINK-REWRITE-LOG](research-notes/LINK-REWRITE-LOG.csv)).

## Reproducing the decode (you supply firmware + key)

```sh
pip install cryptography
python3 tools/decode/upd_decrypt.py \
    --key-file aes256.key \
    --input TORAIZSP16.UPD \
    --output sp16-1.60.iso \
    --expected-iso-sha256 6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb
```

The key is **not** included; Pioneer published it in the SP-16 GPL source
release. See [tools/decode/README.md](tools/decode/README.md).

## Contributing to the research

Help is welcome from people with experience in any of these:

- ARM assembly and reverse engineering
- embedded Linux
- C/C++ development
- digital signal processing
- firmware analysis and emulation
- testing, documentation and technical validation

You don't need to program to help. SP-16 owners can contribute by sharing the
project, discussing the findings, reporting device behaviour that others can
reproduce (say which firmware version you run), or putting the project in touch
with people who have the skills above.

[docs/open-questions.md](docs/open-questions.md) lists where each thread stopped,
with suggested next steps. Issues and pull requests are welcome. Before you
contribute, read [CONTRIBUTING.md](CONTRIBUTING.md): above all, never post
firmware, keys, device images or anything derived from them.

## Support the research

This project is independently funded. If you want to support it, you can do so
on Ko-fi: **[ko-fi.com/mtaylortech](https://ko-fi.com/mtaylortech)**.
Contributions help cover the ongoing costs of research tools, development
software, analysis and documentation.

Support is entirely optional. It funds continued investigation; it does not buy
a product, and it does not guarantee any feature, milestone or custom firmware
release. Everything published here stays open whether or not anyone
contributes.

## Licenses

- Code (`tools/`, `emulation/`, `symbols/*.py`, `symbols/*.java`): **MIT** — [LICENSE](LICENSE),
  except `tools/fx/glibc_expf.py`: **LGPL-2.1-or-later** — [LICENSE-LGPL-2.1](LICENSE-LGPL-2.1)
- Docs, label data and the FX function table: **CC BY 4.0** — [LICENSE-docs](LICENSE-docs)
- These cover only the contributors' own work. Pioneer firmware/GPL components
  and the derived disassembly listings are **not** relicensed — see
  [NOTICE.md](NOTICE.md) and [DISCLAIMER.md](DISCLAIMER.md).

## Status

Active, independent research, with no committed schedule. This project is not
affiliated with or endorsed by Pioneer DJ / AlphaTheta. Contributions and forks
are welcome ([CONTRIBUTING.md](CONTRIBUTING.md)).
