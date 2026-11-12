# tools/decode — SP-16 firmware update decryption

| File | Status | Platform |
|---|---|---|
| `upd_decrypt.py` | **Use this.** Portable rewrite of the decryption step. Re-tested 2026-11-11 on all six releases (1.20, 1.30, 1.31, 1.40, 1.50, 1.60): each output ISO matched the SHA-256 recorded by the original research (see `docs/firmware-reference.md`). A wrong key is rejected and no output is written. | Any OS, Python 3.8+, `pip install cryptography` |
| `decode.py` | Original research decoder (decrypt + full extraction + audit). Published unchanged for provenance. | macOS only; expects the original research folder layout |

## You need to supply two things yourself

1. **The firmware update** (`TORAIZSP16.UPD`), downloaded from the official
   AlphaTheta support site. Check its SHA-256 against
   `docs/firmware-reference.md`.
2. **The AES key file.** This repository does not contain it. Pioneer published
   it in the SP-16 GPL source release: inside `pioneerdj_tsp.tar.gz`, open
   `initramfs.tar.gz` and take `initramfs/usr/local/pdj/aes256.key`. (The
   research worked from a copy of that GPL release; where Pioneer currently
   offers it is not recorded — see `docs/open-questions.md`.)

## Steps

```sh
pip install cryptography
python3 upd_decrypt.py --key-file aes256.key --input TORAIZSP16.UPD --output sp16.iso \
    --expected-iso-sha256 6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb   # 1.60
# extract the ISO (Rock Ridge names):
7z x sp16.iso -osp16-iso        # or: bsdtar -xf sp16.iso -C sp16-iso
# inside images/: rootfs*.tar.gz, pdj.tar.gz (the application), bin/lib/share .sfs
unsquashfs -d lib sp16-iso/images/lib.sfs
```

Notes from the research (see `docs/firmware-format.md` for detail):

- Host extraction does **not** preserve the original file modes (sticky/setgid
  bits and some 0775/0664 modes are lost on macOS). If you ever build a boot
  tree or repack, take modes/owners from the original tar/SquashFS metadata.
- Five special device/FIFO entries per image are metadata only.
- Decryption + CRC verification does not prove you could build an update the
  device would accept. Do not flash anything based on this tool.

## The project's reasoning for publishing this decoder (not legal advice)

The `.UPD` encryption is arguably a "technological measure" under U.S. DMCA
§1201. The project's position, which you should evaluate for your own
jurisdiction:

- The tool contains **no key and no firmware**. It reproduces a documented
  format so that owners can inspect firmware they lawfully obtained.
- The key it expects is one **the manufacturer itself distributed** in its GPL
  source release.
- The purpose is research and **interoperability** with an instrument whose
  last firmware update was 1.60 (2019) (compare §1201(f), the reverse-engineering
  for interoperability exception, and equivalent provisions such as Article 6
  of the EU Software Directive).

This reasoning may not hold in every jurisdiction or every case; it is not a
guarantee that publishing or using the tool is lawful where you are. If a
rights holder objects, the maintainers intend to respond to the request.
See `../../DISCLAIMER.md`.
