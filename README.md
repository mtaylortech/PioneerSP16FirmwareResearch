# TORAIZ SP-16 firmware research (open, unfinished)

Reverse-engineering notes, tools, and symbols for the **Pioneer DJ TORAIZ
SP-16** sampler, published so someone else can continue the work. The original
researcher is **not** continuing it. This is an archived research snapshot, not
a product.

> **No Pioneer firmware, keys, or binaries are in this repository.** Firmware is
> referenced by version and SHA-256 only. **Read [DISCLAIMER.md](DISCLAIMER.md)
> before using anything here** — everything is provided as-is, at your own risk,
> and this is not legal advice.

## What this is (and isn't)

It **is**: a verified description of the firmware update format and a portable
decoder; a six-release hash catalog; analyst symbols for the 1.60 application;
an honest, confidence-labelled account of what was and wasn't learned about
boot, UI, "Normalize", and USB/updater behaviour; a working host-side WAV
normalizer; and reusable methods.

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
- [docs/architecture.md](docs/architecture.md) — **application class maps (1.50 & 1.60):** the sequencer, sampler, MIDI/sync and project-file subsystems recovered from the binary, with the MIDI clock/sync path written up in detail. Backed by [symbols/classes-1.50.md](symbols/classes-1.50.md) and [symbols/classes-1.60.md](symbols/classes-1.60.md).
- [docs/version-evolution.md](docs/version-evolution.md) — **what changed between firmware 1.20→1.60**, recovered from the binaries: which classes/features each release added (AS-1 in 1.30, copy/swap/undo in 1.40, live sampling in 1.50), with a per-version address matrix ([symbols/classes-crossversion.csv](symbols/classes-crossversion.csv)).
- [docs/open-questions.md](docs/open-questions.md) — where it stopped and the
  next steps.
- [emulation/](emulation/) — run the original 1.50 kernel and rootfs in stock
  QEMU, and the reference harness for the 1.60 application emulator.

## Layout

```
docs/        findings, firmware format, firmware reference, hardware, open questions
tools/       decode/ (portable + original decoder), firmware/ (catalog + Ghidra
             pilot scripts), ghidra/ (1.60 analysis scripts), normalization/
             (host WAV normalizer), contracts/ (ARM32 trace helpers)
emulation/   board/ (runnable 1.50 QEMU board emulator) and app/ (reference
             code for the 1.60 application emulator)
symbols/     inferred labels for EP085_Main_R 1.60 (JSON/CSV), reviewed
             annotations, partial structs, disassembly + pseudocode listings for 256
             functions, and a
             Ghidra import script
research-notes/  scrubbed lab notes behind the findings: ~90 experiment
             write-ups by thread, engineering reviews, project history,
             reusable methods, and a cross-cutting LESSONS.md
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

## Licenses

- Code (`tools/`, `emulation/`, `symbols/*.py`, `symbols/*.java`): **MIT** — [LICENSE](LICENSE)
- Docs and label data: **CC BY 4.0** — [LICENSE-docs](LICENSE-docs)
- These cover only the contributors' own work. Pioneer firmware/GPL components
  and the derived disassembly listings are **not** relicensed — see
  [NOTICE.md](NOTICE.md) and [DISCLAIMER.md](DISCLAIMER.md).

## Status

Archived snapshot. Not affiliated with or endorsed by Pioneer DJ / AlphaTheta.
Contributions and forks welcome ([CONTRIBUTING.md](CONTRIBUTING.md)); no
maintenance is promised.
