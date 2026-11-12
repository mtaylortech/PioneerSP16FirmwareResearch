<!-- source: decode/STATUS.md | scrubbed -->

Canonical project knowledge: [docs/PROJECT_STATE.md](docs__PROJECT_STATE.md); this file tracks extraction status only.

Objective: Complete — two validated, readable firmware trees, including nested file-level archives.
Handoff: Read [README.md] `README.md` (evidence not published), [FINDINGS.md] `FINDINGS.md` (evidence not published) and [PROCESS.md] `PROCESS.md` (evidence not published) for architectural findings, assessments, open questions and continuation workflow.
Command: `python3 decode/decode.py`. Recheck saved ISO/base payload trees: `python3 decode/decode.py --audit` (regenerates nested outputs and audit reports).
Requirements: macOS Python 3, system CommonCrypto/bsdtar, installed unsquashfs 4.7.5.

Confirmed facts:
- Updater uses `losetup -e aes -N -p 0`, offset 0. Bundled losetup: -N branch 0x8cec; xgetpass 0x9624 stops at LF/NUL; set_loop 0x9acc copies 31 raw bytes into a zeroed 32-byte key. No hash/hex decoding. Key never logged.
- Supplied cryptoloop.c: AES-256-CBC; independent 512-byte sectors; IV = LE32(sector) + 12 zero bytes. Plaintext trailer is 20 bytes; check_sig 0x85d8–0x8614 establishes CRC32 over preceding ciphertext.
- The sole decoding hypothesis passed BOTH 128 KiB samples before full processing: ISO descriptor terminator, both-endian metadata, 20 directories/113 records each, dot records and extent bounds. ISO lengths exactly match encrypted payload lengths; both wrapper CRCs pass.
- image1 = TORAIZSP16VER150.UPD, internal version 1.50 / app Rev.6284. image2 = TORAIZSP16.UPD, internal version 1.60 / app Rev.6550. Trailer and images/release.txt agree.

Completion evidence:
- Each output has decoded.iso, iso/, payloads/, nested/, report.json, audit.json and manifests. Input and decoded SHA-256 hashes are recorded in the reports.
- Follow-up audit re-decrypted originals and compared saved ISOs; verified every ISO file's bytes, 26 symlinks and 19 subdirectories against source records. No missing/mismatched firmware entries. Finder .DS_Store extras are explicitly recorded, not treated as firmware.
- All ten primary tar containers: exact member sets, regular/sparse contents, symlink targets and hardlinks checked directly against archive members; gzip CRCs pass.
- All six SquashFS containers: fresh strict extraction compared against saved path sets, SHA-256, modes, symlinks and hardlink groups. Unique inode counts match each superblock: bin 376, lib 4,396, share 5,357 per image. Both kernel uImage header/data CRCs pass.
- Base payload regular files: 12,232 / 12,228; symlinks: 715 each. Outer ISO regular files: 68 each. Previous repeat decode produced identical ISO/payload manifests.
- NEW: 386 nested containers expanded per image: 384 gzip font files, one gzip documentation file and one Python test tar archive. Saved under nested/ using source paths plus .extracted; gzip output is named content. Nested output hashes and source/container mappings are saved and verified. No unsupported file-level container signatures found among those checked.

Limitations:
- Five special entries per image are metadata-only: dev/tty (5:0), dev/console (5:1), dev/null (1:3), plus testtar.tar's character device 3-CHRTYPE (1:3) and FIFO 6-FIFOTYPE. Linux nodes occur in rootfs3 for image1 / rootfs1 for image2. Original archives and all special-entry metadata remain saved.
- Host ownership/timestamps/xattrs are not guaranteed preserved. Symlink targets are preserved verbatim and may need the intended Linux layout. Payloads remain separate.
- Audit covers file-level containers and common archive signatures; it does not carve archives from executable/kernel/bootloader/raw-binary interiors. No firmware executed or application reverse engineering performed.

Current blocker: None. Next action: None required for this extraction scope.


## October 8, 2026 — current qualification of mode checking

The earlier SquashFS mode-check statement compares two host extractions; it does not establish original source-mode preservation. [Independent F02] `<Review/INDEPENDENT_TECHNICAL_REVIEW-2026-10-08.md>` (evidence not published) is reproduced by the [new read-only source-versus-host report] `../experiments/offline-review-20261008-01/modes/README.md` (evidence not published), which reads all ten tar modes/offsets and six SquashFS source listings and compares host lstat without extraction.

image2 rootfs4: ./tmp 01777→0755 (decompressed tar header 1201664), ./var/tmp 0777→0755 (4608), ./var/ftp/pub 02777→0755 (6656). Both releases lose sticky/setgid bits at the corresponding directories; six bin files 0775→0755 and five BDF fonts 0664→0644 per release also differ. There are 60 differing tar directories and 22 SFS regular files in total. The 1,430 macOS symlink mode differences form a separate platform-semantics class; every compared target matches.

Readable bytes/paths/targets remain supported. Original container metadata is required for any Linux boot tree or repack; host modes and a second same-host extraction are insufficient. No baseline permission or output changed. Historical output/checksum snapshots remain unchanged, and no bootability, updater acceptance or missing-UI cause is inferred. [Dated current-state correction] `../experiments/offline-review-20261008-01/CURRENT_CORRECTION.md` (evidence not published).
