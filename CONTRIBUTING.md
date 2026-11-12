# Contributing

The original researcher is **not continuing this project**. It is published as
an archived research snapshot so that someone else can understand it and carry
it forward. Forks and independent continuations are welcome. There is no promise
of maintenance, review, or response.

## The one rule that matters most

**Never commit anything that contains Pioneer firmware, or anything derived from
it, or the key.** Concretely, never add to this repository:

- `.UPD` updates, decrypted `.iso` images, extracted filesystems, `EP085_Main_R`
  or any other firmware binary, `.mot` panel firmware;
- the `aes256.key` file, its bytes in any encoding, or a hash of those bytes;
- device disk images (`.raw`, `.img`, `.qcow2`, SD/eMMC dumps), framebuffer
  captures of the running firmware;
- Ghidra native databases (`.rep/`, `.gpr`, `.gbf`, `.gzf`) or IDA databases
  (`.idb`, `.i64`) — they embed the firmware bytes.

Reference firmware by **version + SHA-256 + official download location** instead
(see `docs/firmware-reference.md`). The `.gitignore` blocks the common cases,
but it is a safety net, not a substitute for checking what you stage.

## If you continue the reverse engineering

- Keep the honest-uncertainty style: say whether a claim is *demonstrated in an
  emulator*, a *static finding*, *prepared but unrun*, *partial*, or *unknown*.
  Do not promote an emulator result to a hardware fact.
- Symbol names and types in `symbols/` are **inferred**, not ground truth. If you
  correct one, update `symbols/labels-1.60.json` (the source of truth) and
  regenerate the derived files.
- The symbol addresses are valid for firmware **1.60** (`EP085_Main_R`,
  SHA-256 `3d1392a6…`) only. Do not apply them to another version.

## Scope of any contribution

By contributing you confirm you have the right to contribute the material and
agree to license your code under MIT and your prose under CC BY 4.0 (the repo
licenses). Do not contribute firmware-derived material under those licenses.

## Reporting a rights concern

If you are a rights holder and believe something here should not be published,
please open an issue or contact the maintainer in the repository profile; the
intent is to resolve it promptly.
