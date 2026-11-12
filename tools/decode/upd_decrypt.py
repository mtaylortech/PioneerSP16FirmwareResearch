#!/usr/bin/env python3
"""Decrypt a Pioneer TORAIZ SP-16 firmware update (.UPD) into its ISO image.

Portable rewrite of the decryption step of the original research decoder
(decode.py, macOS-only). Works anywhere Python 3.8+ and the `cryptography`
package are available:   pip install cryptography

FORMAT (verified on releases 1.20-1.60, see docs/firmware-format.md):

    +-------------------------------------------+-----------------+
    | AES-256-CBC ciphertext of an ISO 9660     | 20-byte trailer |
    | image, 512-byte sectors, each sector      |                 |
    | decrypted independently                   |                 |
    +-------------------------------------------+-----------------+
    trailer:  bytes 0-10  b"LIVESAMPLER"
              bytes 11-15 version, e.g. b"1.60\\0"
              bytes 16-19 little-endian CRC32 of all ciphertext
    sector IV = LE32(sector_index) + 12 zero bytes (sector 0 = file start)

KEY: this script does NOT contain the key. Pioneer published it inside the
GPL source release for the SP-16 (pioneerdj_tsp.tar.gz -> initramfs.tar.gz ->
initramfs/usr/local/pdj/aes256.key). Pass that file with --key-file.
The updater's losetup reads it as: bytes up to the first LF or NUL, at most
31 raw bytes, zero-padded to 32. No hex decoding, no hashing.

The script never prints, logs or writes the key.

Usage:
    python3 upd_decrypt.py --key-file aes256.key --input TORAIZSP16.UPD \
        --output sp16-1.60.iso [--expected-iso-sha256 HEX]

Then extract the ISO with 7z / bsdtar / xorriso, and the *.sfs files inside
it with unsquashfs. See tools/decode/README.md.

License: MIT. See DISCLAIMER.md before use.
"""
import argparse
import hashlib
import struct
import sys
import zlib

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError:  # pragma: no cover
    sys.exit("This tool needs the 'cryptography' package: pip install cryptography")

SECTOR = 512
TRAILER = 20
MAGIC = b"LIVESAMPLER"


def load_key(path):
    """Reproduce the updater's key handling exactly (see module docstring)."""
    raw = open(path, "rb").read()
    line = raw.split(b"\n", 1)[0].split(b"\0", 1)[0]
    if not line:
        sys.exit("Key file is empty or starts with LF/NUL")
    return line[:31].ljust(32, b"\0")


def parse_trailer(data):
    if len(data) <= TRAILER or (len(data) - TRAILER) % SECTOR:
        sys.exit("Input size is not ciphertext(multiple of 512) + 20-byte trailer")
    cipher, trailer = data[:-TRAILER], data[-TRAILER:]
    if trailer[:11] != MAGIC:
        sys.exit("Trailer magic is %r, expected %r - not a stock SP-16 update"
                 % (trailer[:11], MAGIC))
    version = trailer[11:16].split(b"\0", 1)[0].decode("ascii", "replace")
    stored = struct.unpack("<I", trailer[16:20])[0]
    actual = zlib.crc32(cipher) & 0xFFFFFFFF
    if stored != actual:
        sys.exit("Ciphertext CRC32 mismatch: stored %08x, computed %08x"
                 % (stored, actual))
    return cipher, version, actual


def decrypt(cipher, key):
    out = bytearray(len(cipher))
    for off in range(0, len(cipher), SECTOR):
        iv = struct.pack("<I", (off // SECTOR) & 0xFFFFFFFF) + bytes(12)
        d = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
        out[off:off + SECTOR] = d.update(cipher[off:off + SECTOR]) + d.finalize()
    return bytes(out)


def check_iso(iso):
    # ISO 9660 primary volume descriptor at 32768: type 1, "CD001", version 1
    pvd = iso[32768:32768 + 7]
    if pvd != b"\x01CD001\x01":
        sys.exit("Decrypted data has no ISO 9660 primary volume descriptor - "
                 "wrong key or unsupported file")
    label = iso[32768 + 40:32768 + 72].decode("ascii", "replace").strip()
    return label


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--input", required=True, help="TORAIZSP16*.UPD")
    ap.add_argument("--output", required=True, help="where to write the ISO")
    ap.add_argument("--expected-iso-sha256",
                    help="optional: fail unless the decrypted ISO has this hash")
    a = ap.parse_args()

    data = open(a.input, "rb").read()
    print("input      %s  %d bytes  sha256 %s"
          % (a.input, len(data), hashlib.sha256(data).hexdigest()))
    cipher, version, crc = parse_trailer(data)
    print("trailer    LIVESAMPLER version %s, ciphertext CRC32 %08x OK" % (version, crc))

    iso = decrypt(cipher, load_key(a.key_file))
    label = check_iso(iso)
    digest = hashlib.sha256(iso).hexdigest()
    print("iso        %d bytes  volume label %r  sha256 %s" % (len(iso), label, digest))
    if a.expected_iso_sha256 and digest != a.expected_iso_sha256.lower():
        sys.exit("Decrypted ISO hash does not match --expected-iso-sha256")
    with open(a.output, "wb") as fh:
        fh.write(iso)
    print("wrote      %s" % a.output)


if __name__ == "__main__":
    main()
