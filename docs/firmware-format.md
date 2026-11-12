# Firmware update (.UPD) format

This describes the on-disk format of a `TORAIZSP16*.UPD` update file, as
established by decrypting all six held releases and cross-checking against the
GPL source Pioneer shipped. Confidence is high for the decode path (it is
reproducible and every output was verified); it is lower for the full set of
checks the on-device updater applies, which was not fully traced.

## Overall layout

```
byte 0                                             payload_end        EOF
+--------------------------------------------------+-------------------+
| AES-256-CBC ciphertext of an ISO 9660 image      | 20-byte trailer   |
| (512-byte sectors, each decrypted independently) |                   |
+--------------------------------------------------+-------------------+
```

| Field / parameter | Value (verified on the held inputs) |
|---|---|
| Payload offset | 0 |
| Ciphertext length | multiple of 512 (and of 2048); e.g. 99,495,936 for 1.60 |
| Cipher | AES-256-**CBC**, re-initialised independently for **every 512-byte sector**; no padding removal |
| Sector IV | `LE32(sector_index) ‖ 12 zero bytes`; sector 0 is at file start |
| Key source | Pioneer's GPL release: `pioneerdj_tsp.tar.gz` → `initramfs.tar.gz` → `initramfs/usr/local/pdj/aes256.key` |
| Key handling | read bytes up to the first LF or NUL, take at most 31 raw bytes, zero-pad to 32. **No** hex decode, **no** hash |
| Trailer bytes 0–10 | ASCII `LIVESAMPLER` |
| Trailer bytes 11–15 | version string, e.g. `1.60\0` |
| Trailer bytes 16–19 | little-endian IEEE CRC32 over the **entire ciphertext** |

The decrypted payload is a standard ISO 9660 image with Rock Ridge extensions:
primary volume descriptor at offset 32,768 (`\x01CD001\x01`), volume label
`UsbAuto`, 2048-byte blocks.

This format is implemented, with commentary, in
[`tools/decode/upd_decrypt.py`](../tools/decode/upd_decrypt.py).

## How this was established (evidence, not guesswork)

- The updater's own `losetup` uses `aes` with offset 0; its key routine copies
  up to 31 raw bytes into a zeroed 32-byte buffer (no hashing). The supplied
  `cryptoloop.c` sets AES-256-CBC with per-512-byte-sector IVs of
  `LE32(sector) ‖ 12 zero bytes`.
- A single decoding hypothesis passed **both** 128 KiB samples before any full
  run (ISO descriptors, both-endian metadata, directory records, extent bounds),
  both wrapper CRC32s passed, and every decrypted file was verified.
- The first 16 ciphertext bytes happen to be identical across releases
  (`579f4973b282113059cc30c3913eb802`). This is **encrypted data, not a magic
  header** — do not treat it as a format signature.

## What is inside the ISO

Top level of the decrypted 1.60 ISO (113 entries in total, from the research's
ISO manifest; 1.50 has the same structure):

```
update            the updater program (unstripped ARM ELF) run from the USB stick
pre_update.sh     updater pre-step script
mot2bin           helper used for the panel-controller (.mot) images
UPDATEAGAIN.rgb565, gui/   updater screen images and font
usr/lib/, lib/    libraries the updater itself uses (DirectFB, GAL, freetype, png, zlib, ...)
images/
  uImage                 Linux 3.0.101 kernel (valid header/data CRCs)
  u-boot.bin.nand        U-Boot bootloader (2009.08-svn)
  fw_env.txt             U-Boot environment: boot commands, MTD partition map
  release.txt            internal release string
  app.rev, system.rev    application and system revision strings
  subucom.rev, subucom1.rev, subucom2.rev   sub-controller revision strings
  PANELCOM1.mot, PANELCOM2.mot   panel-controller firmware (Motorola S-record)
  rootfs1..4.tar.gz      root filesystem, in four tar chunks
  pdj.tar.gz             the application: EP085_Main_R + apl_start + helpers
  bin.sfs, lib.sfs, share.sfs    SquashFS 4.0 (zlib, 128 KiB blocks)
```

So the update is self-contained: the USB stick carries both the new images and
the program that installs them. The updater's internal write/verify logic was
**not** traced. Which `rootfs` chunk holds which content, and the slot meaning,
shifts around release 1.50 — compare versions carefully.

## Important caveats

- **Host extraction is not source-faithful for metadata.** Extracting on macOS
  loses some permission bits: sticky/setgid directories (`/tmp` 01777, `/var/tmp`
  0777, `/var/ftp/pub` 02777 → 0755), six binaries per release 0775→0755, and
  five BDF fonts 0664→0644. There are ~60 differing tar directories and ~22
  differing SquashFS files in total across both releases studied. **Any boot
  tree or repack must take modes/owners/links from the original container
  metadata, not from host `stat`.**
- **Five special entries per image are metadata only** (`dev/tty` 5:0,
  `dev/console` 5:1, `dev/null` 1:3, plus a char device and a FIFO in a nested
  test tar). They are not materialised on extraction.
- **Decryption + CRC success does NOT mean an update you build would be
  accepted.** The full set of acceptance checks inside the on-device updater was
  not traced. The decoder enforces the 11-byte `LIVESAMPLER` marker, which is
  stricter than the original's 4-byte check — validated for these inputs, not
  proven to reproduce every acceptance condition. **Do not flash anything based
  on this.**
- Whether this one key applies to releases beyond the ones held, or to all
  hardware revisions, is **unknown**.
