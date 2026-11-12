# Disclaimer, risk notice, and legal position

Read this before using anything in this repository. By using it you accept the
terms below. **This is not legal advice.**

## No warranty

Everything here — documentation, findings, tools, scripts, symbols and
listings — is provided **"as is" and "as available", without warranty of any
kind**, express or implied, including accuracy, completeness, merchantability,
fitness for a particular purpose, safety, or non-infringement. The findings may
be incomplete, outdated, or wrong. Most of this work was done in substituted
software environments (emulators and host fixtures), **not on physical
hardware**. A result described as "demonstrated" means "demonstrated in the
stated environment" — not that a real instrument behaves the same way.

## You act entirely at your own risk

If you choose to act on any of this information, **you alone are responsible for
the outcome.** The authors and contributors accept **no liability** for any
damage to equipment, loss of data, loss of money, personal injury, or any other
loss or claim arising from use of this material, to the fullest extent
permitted by law.

Modifying firmware, opening the enclosure, attaching debug hardware, or flashing
a device can **permanently destroy it (brick it)**, can expose you to electrical
hazards, and will almost certainly **void any warranty**. A device can be damaged
beyond economical repair. Recovery is not guaranteed to be possible.

**Verify before you act.** Treat every finding here as a lead to confirm, not a
fact to rely on. Check it against primary sources and your own testing before
changing anything on a device you care about. Prefer a spare/disposable unit for
anything invasive.

## Not legal advice; your responsibility to comply with the law

Nothing here is legal advice. Laws on reverse engineering, circumvention of
technical protection measures, and firmware modification vary by country (in the
United States, for example, Section 1201 of the DMCA). **You are responsible for
complying with the laws that apply to you.** If in doubt, consult a qualified
lawyer. For U.S. researchers, the EFF Coders' Rights Project publishes general
background.

## No affiliation; trademarks

This is an independent, community research project. It is **not affiliated with,
authorized by, sponsored by, or endorsed by** Pioneer DJ, AlphaTheta,
NXP/Freescale, the Ghidra project, or any other named party. "TORAIZ", "SP-16",
and "Pioneer" are used only to identify the product under study (nominative
use). All trademarks belong to their respective owners.

## No firmware, keys, or binaries are included

This repository contains **no Pioneer firmware images, no decryption key, no
extracted firmware binaries, and no device disk images.** Firmware is referenced
only by version, SHA-256 hash, and official download location. To reproduce the
decoding work you must obtain the firmware yourself from the official source and
supply the key from Pioneer's own published GPL source release.

## The decoder and the disassembly listings

- **The decoder** (`tools/decode/`) reads an AES key that *you* supply from
  Pioneer's own GPL-licensed source tree; it does not contain that key. It is
  published to enable study of, and interoperability with, lawfully obtained
  firmware. See `tools/decode/README.md`.
- **The disassembly and decompiled listings** (`symbols/listings/`) are derived
  from Pioneer's copyrighted program. They are published as research commentary
  and for interoperability study and are **not** covered by this project's MIT
  or CC BY licenses; they remain subject to the original rights holder's
  copyright. If the rights holder objects, the intent is to remove disputed
  material promptly on request. To report an issue, open a repository issue or
  contact the maintainer listed in the repository profile.
