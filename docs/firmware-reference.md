# Firmware reference

This project includes **no firmware**. Use this table to identify and verify
copies you obtain yourself, from official sources only:

- Pioneer DJ / AlphaTheta "Downloads (Firmware, Driver etc.)" hub:
  `https://support.pioneerdj.com/hc/en-us/categories/4416162439065-Resources-Downloads`
- The SP-16 product page, which Pioneer's 1.50 announcement used as its
  download link: `https://www.pioneerdj.com/product/music-production/toraiz-sp-16/`
- Official firmware change history (source of the dates below):
  `https://downloads.support.alphatheta.com/firmwares/music-production/TORAIZ_SP-16/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf`

These links were found on Pioneer's own pages on 2026-11-11. Whether every
older version is still downloadable from them was **not** checked.

## Releases

Six update files were studied. For each, the SHA-256 is of the raw
`TORAIZSP16*.UPD` as distributed. "App rev" and "build date" are read from the
decrypted image's own metadata, not from filenames or file timestamps.

| Ver | Release date | App rev | App build (UTC in file) | `.UPD` bytes | `.UPD` SHA-256 |
|---|---|---|---|---|---|
| 1.20 | 2016-11-17 | Rev.5296 | 2016-11-11 18:19:15 | 98,668,564 | `c1c77707c1a223fb09e6be32deb34bd2f7af7d333b340052ace10eae2ed8d8e4` |
| 1.30 | 2017-02-02 | Rev.5770 | 2017-01-30 19:57:49 | 99,219,476 | `6bb85a6638cee13411d8b3bfb603256194fd0c91bf92ee1ff51774ca76dbbde4` |
| 1.31 | 2017-07-27 | Rev.5815 | 2017-07-14 17:25:16 | 99,219,476 | `34cb5a861f8af001ed2b557e60c13b943f12dd15e594fbb04b50c8d1a1611dee` |
| 1.40 | 2017-11-21 | Rev.6076 | 2017-11-15 15:38:56 | 99,338,260 | `0d4f2792736f0bab92ac8014018d8593a5ddc6d7e95d4f56b5ca5f7c00ec3fe3` |
| 1.50 | 2018-06-07 | Rev.6284 | 2018-05-14 16:34:00 | 99,493,908 | `11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a` |
| 1.60 | 2019-10-03 | Rev.6550 | 2019-09-25 10:18:48 | 99,495,956 | `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4` |

Vendor-described changes (not independently verified against the binaries):
1.20 added MIDI, LFO, effects, audio rendering and slice editing; 1.30 added
AS-1 tracks, pad scales and scene exchange; 1.31 was a fix release (sample
assignment defaults, note-off on stop, scene copy, grid settings); 1.40 added
copy/track-swap/undo and 64-second samples; 1.50 added live sampling; 1.60 added
second-track effects and MIDI forwarding.

## Decrypted ISO hashes (for `--expected-iso-sha256`)

After decryption with `tools/decode/upd_decrypt.py`, the ISO should hash to:

| Ver | decrypted ISO SHA-256 |
|---|---|
| 1.20 | `0a7abc21f450ba8e90110ae3074ae15b18b2d3b6b5543e00e36ddf36430c829d` |
| 1.30 | `c51297acc55d3686c72a05d90b4ca1316f1b0da75e8ba0d335f48b7ff9e42dd5` |
| 1.31 | `e5f80e0717cf171ce8176a5f2eea91ff9781ff440176922b51029b90b986b3c6` |
| 1.40 | `9339cedf90bd3c8665c337fc275ebdc6469fbb0b021de13c1e4de284794aba97` |
| 1.50 | `534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b` |
| 1.60 | `6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb` |

## Application binary identities

The launched application is `EP085_Main_R` (ARM 32-bit, inside `pdj.tar.gz`):

| Ver | `EP085_Main_R` bytes | SHA-256 |
|---|---|---|
| 1.20 | 10,724,172 | `aed3450fb3fb79e49a335c2cab923c9bc6e67062bd85e2155495c34e3a10e4a7` |
| 1.30 | 11,172,172 | `c460a7018345a793a3def3a44c8d50e1a37e04a66e2ce58f29ed58bc47192a08` |
| 1.31 | 11,171,172 | `57f4dc3de6db666ffcd610df1465dbf3cf91023913ca6530a8f09fafa05368a2` |
| 1.40 | 11,676,132 | `b9ddfebf6e9a0586d66a4682dabeafa504f42d3af721f3b32a4c827720d63ee1` |
| 1.50 | 11,993,612 | `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2` |
| 1.60 | 12,000,396 | `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464` |

The `symbols/` labels apply to the **1.60** binary only.

## Uncertainty / provenance notes

- **Acquisition URLs and any publisher-published hashes are UNKNOWN.** The
  research held the `.UPD` files but did not record where each was downloaded or
  an official hash to check them against. The SHA-256 values above are of the
  held copies; treat them as "what this research used", and re-verify against the
  official download when you obtain your own.
- All six kernels self-identify as `Linux-3.0.101-2790-gc248ed7`; identical
  version strings do **not** prove identical kernels.
