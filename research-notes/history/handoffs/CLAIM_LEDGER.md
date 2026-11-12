<!-- source: docs/handoffs/2026-10-08-independent-review/CLAIM_LEDGER.md | scrubbed -->

# Independent-review claim ledger — 2026-10-08

This ledger is a **current read-only documentary review** of retained evidence. No decoder, emulator, vendor build script, firmware executable, or hardware experiment was run to prepare it. Existing hashes and results quoted below are historical records; fresh inventory/hashes in this handoff are labeled separately as current checks. A saved summary is a locator and interpretation, not an independent measurement or a reconstructed historical log.

All paths in code formatting are relative to ``. Historical source IDs E01–E30 and finding IDs V01–V45 refer to [the retained evidence ledger] `../../EVIDENCE_LEDGER.md` (evidence not published) and [project synthesis] `../../PROJECT_STATE.md` (evidence not published). Those documents retain their original classifications; the narrower claims below distinguish source statements, static inference, instrumented observation, and gaps. Observations are restricted to the exact inputs and substituted environments described. An observation made under a fixture is not automatically a claim about an original physical unit.

## Review identities and reading convention

| Scope label | Exact target and limits |
|---|---|
| F150 | `ResearchSourceFiles/TORAIZSP16VER150.UPD`, internally 1.50; historical recorded length 99,493,908 bytes and SHA-256 `11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a`. Derived `decode/output/image1/`. |
| F160 | `ResearchSourceFiles/TORAIZSP16.UPD`, internally 1.60; historical recorded length 99,495,956 bytes and SHA-256 `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4`. Derived `decode/output/image2/`. |
| A160 | F160 `payloads/pdj/pdj/EP085_Main_R`, 12,000,396 bytes, historical SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`; application emulation, not board/kernel boot. All retained runtime sessions target A160; no runtime validation of A150 is established. |
| Bsp | Supplied `pioneerdj_tsp` / Freescale archive trees, with Linux 3.0.101 and older 3.0.35 material. Broad platform/version agreement does not prove a source-to-shipped-binary match. |
| R24 / R25 | `experiments/emulation-20261007/` and `experiments/emulation-20261008/`: Python 3.10.1, Qiling 1.4.6, Unicorn 2.1.4, Darwin ARM host, library aliases/high interpreter address; R25 adds synthetic duplex PCM, local IPC/epoll fixtures and corrected ARM TLS. Exact run flags are in each `*-result.json.options`, runbook and launch evidence. |
| R27–R30 | Dated display/startup directories for E27–E30. They retain R25 substitutions plus a narrowly translated authenticated local display connection; each attempt has its own code/cookie/deadline identity. Latest R30 supervisor records macOS 14.8.9 ARM64, Python 3.10.1, Qiling 1.4.6, Unicorn 2.1.4, gevent 24.11.1, greenlet 3.5.6, Capstone 5.0.9 and pyelftools 0.33. See `experiments/emulation-startup-20261008-105916/startup-natural-01-supervision.json.runtime`, not the review host's current package state. |

For runtime claims, the highest-value sources are original console/Qiling logs and native result JSON where it exists, together with exact harness/options and supervisor records. `session-summary.json` and `*-events-from-console.json` are derivative. Counts from capped console output are lower bounds. Negative observations apply to the hooked paths, query times and recorded interval, not every possible execution path or future time.

The installed emulator also has consequential **implicit fallback behavior for unimplemented syscalls** (C28). A warning does not establish an ENOSYS return: the inspected branch can proceed without setting a guest return value. Retained progress therefore occurs under incomplete syscall semantics as well as explicitly cataloged fixtures.

## Input, decoder and extraction claims

### C01 — Held updates identify 1.50 and 1.60; publisher authenticity is unavailable

**Type:** observed local bytes / reported historical checks; V01, V34–V35, E01–E02/E08–E09. **Scope:** F150/F160 only.

**Evidence:** `decode/output/image{1,2}/report.json` fields `input`, `input_bytes`, `input_sha256`, `trailer_version`, and `version_metadata.release.txt`; original trailer is the last 20 bytes of each UPD. `iso/images/app.rev` reads Rev.6284 / Rev.6550; `system.rev` reports SVN revision 6285 / 6550 and BuildDate 2018-05-14 / 2019-09-25. Retained release-history PDF `ResearchSourceFiles/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf` states public dates 2018-06-07 / 2019-10-03. Static metadata is also in `docs/EVIDENCE_SNAPSHOT.json.images[]` selected by `image`.

**Limits/counterevidence:** acquisition URLs, original distribution ZIPs, acquisition times and publisher checksums are absent. A local digest identifies held bytes; it cannot attest their publisher origin. Build dates and public release dates measure different things. The old generic license's Linux 3.0/BusyBox v1.2 wording is not exact release evidence.

**Challenge/check:** independently inspect the held trailers and version files; compare with independently acquired official inputs/publisher attestations. A version disagreement or different official bytes would challenge the identity/provenance interpretation without erasing the observed local files.

### C02 — The held payloads decode with sector AES-256-CBC and the supplied key interpretation

**Type:** static inference corroborated by coherent full-output observations; V02–V04, E02–E05. **Scope:** F150/F160, the supplied losetup/cryptoloop implementation, and the macOS decoder.

**Evidence:** `decode/decode.py:27` declares parameters; lines 71–92 read the first LF/NUL-delimited key data, retain at most 31 raw bytes, zero-pad to 32 and decrypt independently per 512 bytes with IV `LE32(sector & 0xffffffff) || zero[12]`. `extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/decrypt_update.sh:22`–35 conditionally selects `-N` and passes stdin to `losetup -e aes`; no offset option is present. Saved `decode/tmp/losetup.disasm` has the `-N` branch at 0x8cec, xgetpass at 0x9624 and no-hash set_loop branch at 0x9acc. `.../BUILD/linux-3.0.101/drivers/block/cryptoloop.c:69`–90 supplies CBC/default key passing; lines 147–163 reset sector IV and increment it. Reports' `parameters` and `decoded_sha256` document successful held-output identities.

**Limits:** key bytes are deliberately excluded from this handoff. These sources do not prove a universal device/release key or every firmware encryption path. The two supplied updates could share one release-family scheme. This is a decoder, not a repacker. CommonCrypto plus the project's parser is one implementation; saved outputs do not make it an independently written decoder.

**Challenge/check:** independently implement the sector transform from the held source/binary instructions in an isolated copy and compare resulting ISOs/file extents to originals. Any necessary extra offset/hash/hex decode, differing output or failure of source extents would challenge the algorithm. Additional independently sourced releases would test generality.

### C03 — The wrapper contains a 20-byte marker/version/CRC trailer; full authenticity checks remain unresolved

**Type:** observed bytes and static interpretation; V05, E01/E03/E06. **Scope:** both held UPDs and supplied `check_sig`.

**Evidence:** each report's `ciphertext_crc32` is `f1679304` / `6f3bb5a2`, with `ciphertext_crc_valid=true`; `decode/decode.py:509`–515 splits the last 20 bytes, requires `LIVESAMPLER` and compares IEEE CRC32 over preceding ciphertext to trailer LE32 bytes16–19. `decode/tmp/check_sig.disasm` around 0x85d8 subtracts 20 and around 0x8608–0x8614 compares the computed CRC. Its marker comparison uses only four bytes, whereas the project decoder requires the full eleven-byte marker.

**Limits/counterevidence:** the executable's name `check_sig` does not establish cryptographic signatures. CRC integrity is not authenticity. The stricter decoder acceptance test is not an exact emulator of all vendor acceptance behavior. The later `decode/output/image2/iso/update` internal checks/dispatch have not been traced; absence of a further signature is unproved.

**Challenge/check:** trace the original checker and subsequent updater statically, distinguishing marker/CRC paths from cryptographic checks. A verified later authentication step disproves any broader “CRC is the only protection” claim. An isolated changed-marker input accepted by the vendor check but rejected by the decoder would confirm their known acceptance difference; no hardware write is needed or authorized.

### C04 — Decoded outer payloads are coherent ISO 9660/Rock Ridge containers with validated files and links

**Type:** historical generated observations, with static implementation and retained audit evidence; V06–V08, E02/E03/E20. **Scope:** both derived ISOs/trees, supported ISO records only.

**Evidence:** `report.json.filesystem` records ISO 9660 with Rock Ridge, label `UsbAuto`, volume bytes99,493,888 /99,495,936, 113 records and20 directories. PVD is at decoded offset32768 with `01 CD001 01` and2048-byte blocks (`decode/decode.py:109` onward). Each `audit.json` records `iso_entries_matched=113`, `mismatches=[]`, `status=passed`; `iso-manifest.json` gives individual path/extent/hash/link entries. `docs/TRANSFORMATIONS.json` entries named `ISO/Rock Ridge extraction` link the input ISO to exact manifest identity.

**Limits/historical gap:** `report.sample_bytes=131072`, `decode/PROCESS.md:8` and current integrated checks report successful samples before full processing; the original standalone `sample.py` and its complete historical console are not retained. `decode/tmp/before-rerun.json` records four pre-rerun manifest hashes, but by itself lacks timestamp, command, exit code and full before/after log. Current code or a fresh replay cannot recreate that missing historical context. The identical first16 ciphertext bytes are encrypted data, not established format magic.

**Challenge/check:** independently parse both saved ISOs and compare each original extent/link target to the extracted tree. A non-Finder extra, missing record, extent mismatch or incoherent volume declaration challenges completeness. Verify any historical repeatability assertion against retained manifests/logs rather than assuming a saved hash proves chronological order.

### C05 — Five tar/gzip and three SquashFS components per release were file-level audited

**Type:** historical extractor/auditor observations; V09–V10, E02–E03. **Scope:** the eight listed containers per held release.

**Evidence:** `report.json.archives` enumerates `pdj.tar.gz`, `rootfs1`–`rootfs4.tar.gz`, `bin.sfs`, `lib.sfs`, `share.sfs`. `audit.json.archives` records source SHA-256, member/entry matches and, for SquashFS, `strict_reextraction=true`, unique inodes376/4396/5357 and matched hardlink groups6/0/274. `report.json.archives[*.sfs]` records SquashFS4.0 little-endian zlib,131072-byte compression blocks and extraction exit0. Per-image extraction and audit logs remain under `decode/tmp/`. `decode/tmp/consolidation/latest-audit.log` reports both source audits passed,386 nested containers and5 special entries each.

**Limits/counterevidence:** initial bsdtar inability to read SquashFS is a tool-format failure, preserved in historical notes, not evidence of a bad decode. Finder `.DS_Store` extras are explicitly recorded in `audit.json.host_metadata_extras`; they are an exception to literal host-tree equality. Regular-path counts12,232 /12,228 include hardlink paths, while inode counts represent unique objects. The saved audit is not an independently implemented comparator, and it does not restore host ownership/timestamps/xattrs.

**Challenge/check:** independently inspect source member sets/gzip CRCs; extract SquashFS with a second suitable tool in a separate directory, then compare paths, contents, link groups and modes. Any mismatch outside documented host/metadata exceptions would challenge the audited result. Never execute archive contents for this check.

### C06 — Nested expansion and special-entry preservation are limited, explicitly scoped completeness claims

**Type:** observed historical inventories and omission records; V11–V12/V33, E02/E19. **Scope:** supported file-level nested signatures in F150/F160; separate earlier Bsp extraction report.

**Evidence:** `decode/output/image{1,2}/nested/report.json` records386 expanded containers (384 font gzips, one info gzip, one Python test tar), per-container identities and verification. `report.json.all_metadata_only_entries` / `audit.json.metadata_only_entries` record `dev/tty`, `dev/console`, `dev/null` in F150 rootfs3 / F160 rootfs1, plus Python `3-CHRTYPE` and `6-FIFOTYPE`. Original archives remain. `audit.json.scope` excludes executable/kernel/bootloader/raw interiors; `nested.unsupported_containers=[]` is scoped to the formats `decode/decode.py.container_kind` recognizes. `ResearchSourceFiles/extraction-report.json` separately reports4,678 operations and omission-bearing records773 initramfs nodes plus2 Python-test entries.

**Limits and recovered evidence:** “all supported regular files accessible” is reviewable; “every byte unpacked”, “all source recovered”, “bootable filesystem” or “no other nested format exists” is unsupported. The earlier canonical statement that the Bsp extractor was not located is now a dated gap: this handoff found `/tmp/sp16_extract_recursive.py` and `/tmp/sp16_extract_verify.py` outside the workspace and recovered genuine historical commandExecution records through chat retrieval. Current script copies/identities are not a historical code hash or a replay. Their implementations write the extraction report and trees, and must not be run within this read-only handoff. Historical records establish actual extractor completion and failed/interrupted verification attempts, but do not independently compare all output contents. Five-per-release omissions are not the773+2 Bsp omissions.

**Recovered-source locators:** [current extractor copy] `recovered-extractor/sp16_extract_recursive.py` (evidence not published), [current verifier copy] `recovered-extractor/sp16_extract_verify.py` (evidence not published), [copy provenance/current identities] `recovered-extractor/PROVENANCE.json` (evidence not published) and [genuine historical command records] `RECOVERED_EXTRACTION_HISTORY.json` (evidence not published). Historical recursive command`exec-8b4162c8-50ff-463f-8570-f80027f0a3fa` completed exit0/duration141596ms; its returned output is truncated at20,000 of25,121 characters. Report-correction command`exec-774a9278-6fd2-4944-947c-828d699c8c30` completed exit0 and reports773+2 omissions/final4,668 extracted count. Failed pkill exit3 and verifier`exec-0ded8d54-307c-47bc-b492-82f342efd38c` exit130/KeyboardInterrupt at open/read512 remain genuine failed attempts. Corrected verifier`exec-139cc502-3443-42fd-bb1c-ec372301a866` completed exit0 with scan0/no newly processed archives. Exit0 is process completion, not byte-validation of all4,678 records; scan0 is not replay of earlier operations. Consult exact preserved records for command text, output availability and truncation.

**Current-check counterrecord:** the dated handoff inventory and a read-only `lstat` during this review found a present FIFO (mode0644, logical length0) at `extracted/L3.0.35_4.1.0_130816_source/L3.0.35_4.1.0_130816_source/pkgs/Python-2.4.4.tar.bz2.extracted/Python-2.4.4/Lib/test/testtar.tar.extracted/6-FIFOTYPE`. It was not opened or read. This is a current-state difference from the historical special-omission report; it does not date its creation, prove the report false, identify which extraction created it, or establish historical faithful node reconstruction. Preserve both records and investigate provenance if node fidelity matters.

**Current static obstacle:** recovered recursive `discover` lines15–18 do not reject nonregular nodes before opening/read512; recovered verifier line15 adds `p.is_file()`. Encountering a FIFO in the recursive path can therefore block under normal FIFO semantics. This is a current code-based inference; the historical interrupted traceback does not identify the offending path and cannot establish that the present FIFO caused that earlier interruption. No such behavior was tested during this review.

**Challenge/check:** examine supported-signature detection for blind spots, inspect candidate binary interiors separately, compare raw source member lists against omission metadata and independently extract selected Bsp archives. Discovery of an unsupported/nested container challenges any universal completeness assertion while remaining compatible with the narrower scoped claim.

## Software, boot and hardware-document claims

### C07 — Both shipped kernels identify 3.0.101-2790-gc248ed7, but they differ byte-for-byte

**Type:** observed header/CRC/identity metadata; V13, E02/E18. **Scope:** F150/F160 `iso/images/uImage`.

**Evidence:** both `report.json.uImage` entries have `name=Linux-3.0.101-2790-gc248ed7`, `header_crc_valid=true`, `data_crc_valid=true`; data bytes4,727,336 /4,732,532. Exact identities are in `docs/ARTIFACT_INVENTORY.json` selected by path and `docs/EVIDENCE_SNAPSHOT.json.images[].kernel`.

**Limits:** same version name does not mean same binary/config/initramfs. Header metadata is not a running-kernel observation or a matching source build. The application's GNU/Linux2.6.31 ABI tag describes compatibility, not kernel release.

**Challenge/check:** independently parse uImage and CRCs, compare bytes, recover embedded boot material statically and compare to Bsp inputs. A matching version string alone cannot resolve source correspondence.

### C08 — A compiled ARM application and dynamic dependencies are present; original sampler source and feature map are unestablished

**Type:** static observations; feature-location proposition is inference only; V14–V15/H01, E18/E24–E25.

**Scope/evidence:** A150 is11,993,612 bytes, historical SHA-256 `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`; A160 identity above. `docs/EVIDENCE_SNAPSHOT.json.images[]` fields `application_file_output`, `application_needed`, `application_rpath` record stripped 32-bit little-endian ARM EABI5 executables, interpreter `/lib/ld-linux.so.3`, imports ALSA/X11/Xext/FreeType/libcld/ICU51/tcmalloc/standard runtimes and toolchain paths including armv7-a/softfp/neon. Localized ARM/PLT annotations exist in runtime directories; no Ghidra/IDA/Binary Ninja/radare project or application-wide decompilation was identified in the reviewed records.

**Limits:** imports and size do not allocate all sampler/sequencer/UI responsibilities. “Stripped” does not mean encrypted or unanalyzable. “No source identified in inspected material” is a scoped negative, not proof source never existed. H01 proposes EP085_Main_R/called libraries as likely feature locations; no selected requested feature is mapped or implemented.

**Challenge/check:** inspect ELF headers/dependency closure independently; select one actual feature and locate its consumers/functions/resources with version-qualified call/data evidence. Finding source or feature logic elsewhere would challenge the relevant absence/location inference.

### C09 — Shipped scripts describe BusyBox init and application/MIDI launch; they are not observed board startup

**Type:** observed script contents, inferred intended startup sequence; V16, E16. **Scope:** F160 scripts; F150 may be compared separately.

**Evidence:** `decode/output/image2/payloads/rootfs4/etc/inittab:2` invokes rcS; `etc/rc.d/rcS:33`–37 runs executable rc.local; `etc/rc.d/rc.local:66`–68 launches `/root/pdj/apl_start`; `payloads/pdj/pdj/apl_start:399`–406 loads snd-din-midi/midi_thru, and lines452–475 contain normal/testmode EP085_Main_R launches. The script also has environment-dependent branches.

**Limits:** runtime probes invoke A160 directly; they do not execute this complete boot chain. Included services/helpers such as telnet/gdbserver do not prove enabled/live access. MIDI module presence is not MIDI semantic or timing validation.

**Challenge/check:** independently follow script control/data dependencies and compare F150. A firmware environment branch disabling launch/services would disprove an unconditional startup interpretation; only separately authorized live evidence could establish device behavior.

### C10 — fw_env declares NAND partitions and A/B choices; actual geometry and rollback remain unknown

**Type:** observed configuration, inferred size arithmetic; V17, E17. **Scope:** held `iso/images/fw_env.txt`, not a physical environment readback.

**Evidence:** F160 `fw_env.txt:13` declares the sequential256MiB primary span plus overlapping block aliases; lines22,34–36 select kernel_bankA/B and NAND reads at0x500000 /0xF00000, each length0x500000. Lines28–31 define MMC/ext4/network/NFS alternatives; line40 selects NAND boot. F150 equivalent is retained. `docs/PROJECT_STATE.md:194`–214 derives offsets explicitly as arithmetic.

**Limits:** aliases must not be added to primary span; each named bank is10MiB but its configured read length is5MiB. Neither config text nor two bank names proves real capacity, ECC/OOB/bad-block geometry, active environment or safe rollback. `pre_update.sh` contains destructive commands and is evidence only; no backup/recovery demonstration exists.

**Challenge/check:** independently recalculate offsets and statically trace bank-selection/update-status logic. For a future separately authorized hardware phase, compare a non-destructive environment/NAND readback and a demonstrated recovery sequence; contradictory live settings would challenge deployed-layout claims.

### C11 — Supplied initramfs describes RAM-root/SquashFS/UBIFS construction; release-kernel equivalence is unresolved

**Type:** observed supplied-source statements; V18/H03, E15. **Scope:** Bsp `initramfs.tar.gz.extracted/initramfs/init`.

**Evidence:** lines270–329 include RAM-root and four tar reads at relative0/8/16/24MiB in mtd5 plus application archive from mtd6; lines395–472 handle misc UBI/UBIFS; lines476–483 mount lib/share/bin.sfs at `/usr/lib`, `/usr/share`, `/usr/bin`; line549 switch_roots through taskset to init. Other branches describe SD/ext4 and NFS boot.

**Limits:** these are conditional intended layouts in supplied source, never replayed in a firmware kernel boot. The source initramfs has not been recovered from and compared to both uImages; filesystem-support branches do not prove deployed ext4/NFS/UBIFS geometry.

**Challenge/check:** statically recover each kernel's embedded initramfs/config, compare exact bytes/scripts/options and document missing build inputs. A mismatch would challenge H03 without contradicting the source script's own contents.

### C12 — The service manual names main/storage/controllers; physical specifications remain qualified

**Type:** manufacturer-document statements preserved in a third-party PDF, not device observation; V19–V24, E07.

**Evidence:** `ResearchSourceFiles/928c4c.pdf` has72 PDF pages. PDFp49/printedp46 names MAIN IC2000 MCIMX6Q5EYM10AD and assigns main/USB-A/MIDI/audio processing; PDFpp7/13/49 name DDR3 IC2300/2301 K4B4G1646D-BCMA, NAND IC2601 MX30LF2G18AC-TI and eMMC IC3800 THGBMHG6C1LBAWL, with described storage roles. PDFpp28/30/49 name M1 IC8005 and M2 IC8008 R5F364AENFA-U0 and their switch/LED/pad/touch/gain roles. PDFp61/printedp58 shows MAIN system/apl/SUB1/SUB2 updater labels. Retained text/renders under `decode/tmp/consolidation/service-page-*` locate these passages; the PDF is primary for the statement.

**Limits and contrary historical record:** metadata points to a ManualsLib mirror; direct authenticated Pioneer acquisition is absent. The canonical blanket wording “No chip datasheet was reviewed” is too broad: a recovered earlier agent answer cites NXP's IMX6DQCEC processor datasheet and Samsung's K4B4G1646D-BC-I Rev103-0 RAM datasheet and infers1GB DDR3 / rated quad Cortex-A9 at1GHz. The exact answer is retained in `HISTORY_SOURCES.json.historical_agent_answers_challenging_canonical_documentation`, turn`01a119bc-a3b1-7312-bdc3-8e5d2ffae496`, message`msg_06c225cc3481a2a2016ac719fc6b4c8190a46b0bcf110432bb`. It establishes the agent's claims/citation targets, not verified source contents or applicability to the exact held board part. No retained datasheet copy or source-retrieval/tool-output record in this handoff establishes those specifications independently. Active clock/cores, usable capacity/boot reservations and physical unit measurements remain unknown. i.MX6Q platform agreement is strongly supported by manual/config/ARM bytes; generic codec/VPU material does not prove a dedicated SP-16 audio DSP.

**Challenge/check:** verify exact passages/page numbering, compare an authenticated manufacturer manual/datasheets and, only if newly scoped, the unit's part/readout evidence. A variant/revision document or different installed part would limit applicability.

### C13 — Source/build collection and package versions are held; reproducible shipped builds are not demonstrated

**Type:** observed source/script/notice contents; H03 remains inference; V25–V30, E12–E14/E21–E23.

**Evidence:** `extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/{linux-3.0.101,u-boot-2009.08,busybox-1.20.2}/`; `ltib_common.sh:5`–13 names `/home/iMX6/ltib`, GCC4.6.2/glibc2.13 Freescale-Linaro2011.12, `arm-none-linux-gnueabi-` and `arm-fsl-linux-gnueabi-`. `config/platform/imx/imx6_defconfig.dev:310`–349 sets MX6Q/CPU_V7; line426 preemption and1467–1469 ALSA PCM/raw MIDI. `make_boot:81` selects `mx6dl_sabresd_config`. `docs/EVIDENCE_SNAPSHOT.json.images[].busybox_banner` and `uboot_banner_fragments` record shipped1.20.2 /2009.08-svn. `copyright/` and `ResearchSourceFiles/ltib_patch/*.sh` list ALSA1.0.24.1/utils1.0.24.2, gst-fsl-plugins3.0.11 and older codec inputs.

**Counterevidence/gaps:** generic license notice BusyBoxv1.2 conflicts with exact banners; bsp_setup2 refers linux3.0.35 while held shipped headers say3.0.101; mx6dl target differs from MX6Q manual/config. Toolchain prefixes are distinct. The historical host guide describes Ubuntu9.04 with11.10 subsection, not the identified release host. No vendor build/patch script was run, matching kernel build made, proprietary source recovered or all dependencies established.

**Challenge/check:** independently trace branch/config selection and identify exact patch/config/toolchain closure before a separately authorized isolated build. Reproduced component bytes/configs would test H03; a source version label alone cannot.

### C14 — Assembled/duplicate source archives and panel payload equality are local byte-identity claims

**Type:** historical generated byte checks; V31–V32/V35–V36, E12/E18.

**Evidence:** `docs/EVIDENCE_SNAPSHOT.json.archive_concatenation_validation`, `decode/tmp/consolidation/part-validation.json` and the first three `docs/TRANSFORMATIONS.json` entries record ordered concatenation equality for pioneerdj_tsp, L3.0.101 and L3.0.35 source archives. `docs/ARTIFACT_INVENTORY.json` records equal62,012,124-byte SHA-256 `d875d1916d25290366105ddf19997327ff52b9873e3dfd2f2af4a321a47c6099` for the two IMX_MMCODEC3.0.35 CODA archives. Per-image PANELCOM1/2.mot selected inventory rows have equal cross-release hashes; `version_metadata.subucom1.rev` / `subucom2.rev` are5187 /3671 in both reports.

**Historical recovery:** `RECOVERED_EXTRACTION_HISTORY.json` retains genuine original assembly command`exec-db13ec5c-5053-4010-9f1c-058d9ccc760b`, exit0. This supplements the later part-equality checks with an executed historical command record; it still does not establish original download/authenticated publisher provenance or replace the recorded byte comparisons.

**Limits:** same bytes do not prove independent provenance or archive publisher authenticity. Unchanged panel payloads do not prove unchanged controller behavior with a changed application. SUB1↔M1/PANELCOM1 and SUB2↔M2/PANELCOM2 dispatch remains H02, supported only by naming/count/context.

**Challenge/check:** concatenate/hash in new temporary files or stream without replacing originals; compare panel bytes independently. Updater dispatch/write-destination evidence could confirm or disprove H02.

## Emulation and display claims

### C15 — Original A160 reaches entry/main and an initial null read under R24; hardware-cause diagnosis is limited

**Type:** instrumented runtime observation; V37, E24. **Scope:** `confirmed-startup` with aliases/high loader, no null PCM/display.

**Evidence:** `experiments/emulation-20261007/confirmed-startup-result.json` has application identity, options, elapsed5.2880807s, exception UC_ERR_MAP and final_pc0x58eebc. Its `events` record entry0xb5cc8/main0xb3ac4, names AudioSrcHelper0/FlashWriter/UIThread and invalid_memory address0, access19,size4, PC0x58eebc. Original console lines1247/1268 show entry/main; lines1801/1937 show `hw:ak4458audio,0` and snd_pcm_open−19; line1940 records the null read. Missing SPI/panel/etc paths also appear in the logs.

**Limits:** hardware PCM failure precedes the fault but timing alone does not prove complete root cause. R24 had import/native setup/search/loader failures before this guest path; those are distinct experiments. Interpreter address0x70000000 and library aliases are emulation substitutions. A160 execution is not booting SP-16 firmware/kernel or running all features.

**Challenge/check:** independently inspect the fault instructions/registers and unchanged input closure. Under newly authorized execution, vary one environmental defect with preserved original comparison; a repeat fault despite the corrected condition would challenge its causal explanation.

### C16 — Original library PCM calls succeed and return frames under null audio; playable audio/DSP correctness are unproved

**Type:** instrumented calls/returns under an explicit synthetic fixture; V38, E25. **Scope:** R25 `corrected-tls`, A160/original ALSA library with configuration routing hw names to null.

**Evidence:** `experiments/emulation-20261008/corrected-tls-result.json.events` contains snd_pcm_open return0 and sampled snd_pcm_writei/readi returns64. `api_counts` records playback16,911 and two capture counts5,635/5,633; `session-summary.json.final_probe.sampled_api_returns` is a compact derivative. Null behavior is documented by `alsa-original.conf`, modified guest `rootfs/usr/share/alsa/alsa.conf`, and supplied `.../alsa-lib-1.0.24.1/src/pcm/pcm_null.c`. The harness/runbook enumerate stream configuration and `/dev/null`/`/dev/full` handling needed for duplex success.

**Limits:** original library API paths are exercised; real converter, buffer content, sampling, sequencing, DSP quality, MIDI, underruns/latency or audible instrument output are not validated. A thread name “AudioWorker” is not proof of actual musical processing. Counts depend on cooperative scheduling/fast instrumentation and cannot measure physical utilization or performance.

**Challenge/check:** independently inspect fixture semantics and call hooks to verify returned64 originates in the original null plugin rather than a forced API result. A known audio-content/timing acceptance test on a faithfully modeled or separately authorized real environment would be needed for wider claims.

### C17 — The application requests thread CPU placement; placement/utilization is not implemented or measured

**Type:** observed syscall arguments; V39, E25. **Scope:** R25 A160 threads.

**Evidence:** `session-summary.json.cpu_affinity_requests` and original `corrected-tls-result.json.events[kind=cpu_affinity_request]` record main/UI→0, Juce ALSA→1, first ALSAInput/ProjectManager/AudioWorkerSC3→2 and second ALSAInput/AudioWorkerSC4→3. Harness `experiments/emulation-20261008/probe.py:199`–204 reads masks, sets `emulated=false` and returns−38/ENOSYS.

**Limits:** these are requests made by original code in this environment, not successful scheduling, active hardware core count, distribution of measured DSP workloads, utilization or throughput. R24 logs already warned sched_setaffinity unimplemented. Later diagnostic traces observe differing thread counts (R29 first15/retry7 vs R25 historical17 including main), so identical startup scheduling/total thread count is not guaranteed.

**Historical counterrecord:** `HISTORY_SOURCES.json.historical_agent_answers_challenging_canonical_documentation`, turn`01a119be-a1cd-7983-b460-f62a7969ac19`, preserves an earlier agent answer attributing broader class/interrupt roles to cores0–3 and citing `payloads/pdj/pdj/irq_smp_affinity` and `apl_start`. This is a claim and linked static evidence that warrants review; it is not a measured workload map or a physical scheduling observation. Independently inspect the scripts and any retained class/affinity annotations before accepting the answer's specific role assignments. Preserve its own explicit limits on per-track/effect/time-stretch distribution and unused capacity.

**Challenge/check:** independently decode mask bytes and align runtime IDs/names. Any claim about actual core execution needs a scheduler implementation and independent measurement; a differing mask or name attribution would challenge the request mapping.

### C18 — Qiling ARM TLS state mismatch is directly supported; its role in the allocator fault is strongly supported, not proven

**Type:** package-source static observation plus instrumented mismatch/corrected comparison; V40, E25.

**Evidence:** installed `.../qiling/arch/arm_utils.py` get_tls assembly reads the shared helper word; `.../qiling/os/linux/thread.py:482`–494 saves/restores c13_c0_3; `.../qiling/os/linux/syscall.py:70`–73 sets register and shared word. Harness `experiments/emulation-20261008/probe.py:207`–217 compares c13_c0_3 to0xffff0ff0 and returns current TLS through r0/LR at helper0xffff0fe0. `corrected-tls-result.json.tls_helper_counts` records111,121 calls/10,408 mismatches. `extended-runtime-result.json` has null reads at65.947104/69.401160s, PC0x91cbdeb8 in tcmalloc, and `logs/allocator-fault.txt` identifies the freelist dereference. Corrected run records no invalid_memory events to bounded stop.

**Limits/counterevidence:** firmware libraries were unchanged, but emulator behavior was corrected. One uncorrected/corrected bounded comparison is not a controlled proof excluding scheduler/input/timing alternatives. The runbook explicitly calls TLS fault causality “strongly supports”; no vendor allocator defect or physical memory-corruption conclusion follows. Later R29 mismatch counts70/68 differ from R25 without proving a stable failure rate.

**Challenge/check:** inspect installed source/helper bytes and state transitions independently. A controlled repeated comparison with identical inputs/options/scheduling and an isolated TLS correction could test causality if newly authorized. A fault recurring with correct per-thread TLS would challenge a sufficient-cause claim.

### C19 — One R25 run ended at a bounded deadline without recorded guest memory faults; clean shutdown/stability are unproved

**Type:** historical instrumented result; E25–E26. **Scope:** exactly `corrected-tls`, not subsequent partial runs.

**Evidence:** `corrected-tls-result.json.elapsed_seconds=76.2160203329986`, `outcome.status=bounded_stop`, `reason=requested wall-clock deadline`; events contain no invalid_memory; summary identifies17 named threads including main. Harness deliberately raises/catches a deadline condition, and the record's `guest_exit_code=0` is part of its result schema. Full console/Qiling logs and historical verification/checksums remain.

**Limits:** code0 in this deadline result does not mean the original application exited normally. Hook coverage cannot prove absence of every defect. Cooperative Qiling execution and synthetic audio make duration/counters unsuitable for hardware performance, timing or long-term stability. Later guest worker alarms did not always stop all threads, contradicting any universal reliability claim for the baseline's native alarm alone.

**Challenge/check:** review outcome construction and fault-hook coverage; distinguish host process termination from guest return. Longer/repeated independent runs, if separately authorized, would test stability rather than retrospectively improve this historical run's proof.

### C20 — R27 verified a local authenticated server but guest authentication failed; partial retry outcomes remain partial

**Type:** host/server and instrumented guest observations; E27. **Scope:** `experiments/emulation-display-20261008-004011/`.

**Evidence:** `display-verified.json` records authenticated local server setup. `display-01-result.json` retains getpeername Unix-path exception; `partial-summary.json.events` / `logs/display-02-console.log` show corrected connect0, guest access(`/root/display.xauth`,R_OK)=−1/EPERM, unauthenticated setup rejection and XOpenDisplay0; no XCreateWindow observed. `partial-summary.json` explicitly sets native_result_json_exists=false, final countersnull and latest_recorded_event_elapsed79.664204s; deadline event76.002404s occurred while workers continued.

**Limits:** host authentication success is not guest authentication success. Original native retry JSON/finalPC/total runtime are unavailable. Administratively corrected local socket ownership and the rejected, unexecuted shared-directory symlink are part of the failure/provenance history. Closing documentation overran its historical full deadline by34.682s, separately recorded; runtime was stopped before runtime cutoff.

**Challenge/check:** inspect Qiling access/path mapping and exact guest-root/mapped-cookie placement without disclosing cookie bytes. Raw setup/access events defeat any “authenticated guest worked in R27” claim. Later R28 correction does not rewrite R27's result.

### C21 — Actual-root cookie placement and display-only fcntl translation allow guest X setup/API progress under R28

**Type:** instrumented guest observation plus isolated host reproducer; V41–V42, E28. **Scope:** `experiments/emulation-display-20261008-011849/` with scoped cookie/local_display correction.

**Evidence:** `logs/auth-nonblock-03-console.log` / derivative events contain guest access0, setup status1, original XOpenDisplay0x17de000 and XCreateWindow0x200001. `fcntl-flag-check.json` shows Darwin socketpair initially nonblocking, guest flags0x802 clearing nonblocking when passed directly, and preserved nonblocking under scoped correction. Exact `fcntl_flag_check.py`, `local_display.py`, diffs and integrity record identify code. `auth-nonblock-03-supervision.json` records independent host78.013921s stop, SIGTERM/reap, exit−15. `auth-visible-02-result.json` preserves the previous complete native attempt.

**Limits:** the reproducer concerns an anonymous host socketpair, not physical SP-16 networking. Translation is limited to the tracked display fd; named/authenticated display fixture is not general Linux socket fidelity. Retry native finalJSON/finalPC/counters are absent. Original Xlib API return is not server acknowledgment/window/UI.

**Challenge/check:** inspect flag constants, guarded descriptor/domain/path translation and cookie equality/permissions; validate setup trace against original library calls. A cookie/path or fd misattribution would challenge authentication/correction attribution. No replay is authorized by preparing this ledger.

### C22 — Binary instructions support Xlib/XCB layout and trace entry addresses; symbolic field names remain interpretation

**Type:** static binary-derived offsets, runtime entry-byte/descriptor validation; V43, E29.

**Scope/evidence:** R29 `xlib-layout.json` concerns F160 libX11 SHA-256 `03a4cb9d73d4d6eefe5d8667e8a122e87c08458d986837c8abe4ffe54ba6f2fc` and libxcb SHA-256 `b3e5e0ada7073d4a4fb34ead18a4fcc223181fc21e673e678d50202aa501d009`. Fields `layout`, `derivation`, `entry_points`, `xcb.layout` and `xcb.derivation` connect offsets to ELF instructions: Display fd+8, request+0x60, buffer+0x68/bufptr+0x6c/bufmax+0x70, private+0x538→connection+8; XCB output+0x1104/length+0x2104/request+0x2108/written+0x210c. Saved `XConnectionNumber`, `XNextRequest`, `XOpenDisplay`, `_XGetXCBBuffer`, `_XPutXCBBuffer`, xcb inner send/flush disassemblies support arithmetic. Runtime `display_library_hooks` / snapshot fields record loaded entry-byte validation and tracked fd equality.

**Limits:** field names for allocated buffers/sequences are inferred from usage with high confidence; no source-ABI struct assumption should replace those exact shipped bytes. Wrong load bias/error-field interpretation, stale pointer, hook collision or descriptor reuse could corrupt the snapshots. An empty Xlib buffer alone does not prove a request reached the server.

**Challenge/check:** independently disassemble the exact ELFs, derive offsets and check runtime guards/code against saved bytes. A different instruction interpretation, missing fd ownership check or stale-pointer evidence would challenge snapshots.

### C23 — The initial CreateWindow moves into libxcb and remains queued during R29/R30; server acceptance is untested

**Type:** observed buffer bytes/counters and instrumented negative paths; V44, E29/E30.

**Evidence:** R29 `buffer-natural-02-result.json.events[kind=display_buffer_snapshot]`, or derivative summary's attempt`buffer-natural-02.snapshots`, shows36bytes at XCreateWindow_before_unlock1.628663s, then identical bytes in XCB at return instruction1.629064s, near stop73.002816s and final76.010376s. Payload begins `01000900...`, decoded as opcode1,length9, window0x200001,parent0x42, width1,height1,class2/InputOnly. XCB counters request7/written6/error0, length36; Xlib pending0 after transfer. R30 console lines1367/1371 and22148 independently retain same buffer/counters through76.467894s. Both have no later hooked library/display writes/flush/map/send and zero server-root children at query times.

**Counterevidence/limits:** R29 first probe missed the return snapshot because one mutable Qiling return-hook list interfered; its exact first code/logs survive and `targeted-correction.json` records permanent checkpoint retry. Initial display setup had legitimate writes/flushes before CreateWindow; the negative is **after** the original call. API return allocates a resource ID client-side; it is not server acceptance. InputOnly request cannot carry drawable UI pixels. No forced flush/map or server rejection/acceptance test occurred.

**Current read-only semantic cross-check:** held F160 `payloads/share/xcb/xproto.xml:614`–617 maps class2 to InputOnly. The supplied older X server source `extracted/L3.0.35_4.1.0_130816_source/L3.0.35_4.1.0_130816_source/pkgs/xorg-server-1.6.1.tar.bz2.extracted/xorg-server-1.6.1/dix/window.c:673`–674 classifies InputOnly as `UNDRAWABLE_WINDOW`. This supports the protocol interpretation; it is not proof that this exact older server source produced the contained Xvfb or that the request was accepted.

**Challenge/check:** decode the raw36bytes independently; review send/flush/write hook coverage and output-counter semantics. A post-call tracked send or acknowledged/window-tree record would contradict “remains queued” for its interval; eventual future flush is compatible with the bounded observation.

### C24 — The original main returns from CreateWindow and continues allocation/reset work; a causal hardware wait is unestablished

**Type:** observed checkpoints/registers/returns, inferred provisional function meaning; V45, E30. **Scope:** R30 `startup-natural-01`, main runtimeID2000,18 permanent byte-validated checkpoints.

**Evidence:** `startup-binary-analysis.json.regions` and exact saved disassemblies identify original instruction regions, including0x350010 bounded store initializer and0x354604 reset loops. `logs/startup-natural-01-console.log:1252` records checkpoint bytes; line1372 onward original return0x6980f4→0x698100/0x698104→saved/observed caller0x698500. Original console and `session-summary.json.progress` record at least270,337 allocation element returns at0x353c80 by58.506704s,495 whole returns0x353d04 by60.070817s; reset phase starts60.365249s at0x354604 with LR0x50ab9c. Lines22145/22147 record75th loop/function completion at0x354674/0x3546d4 by76.467846s, changing objects, dimensions16×64 and stride0x98. `startup_trace.py` defines filters/capping and snapshots.

**Limits/counterevidence:** derivative names “allocation/matrix/reset” are interpretive annotations, not vendor symbols or feature attribution. Capped counts are lower bounds; no final counters/PC exist. Total parent work bound/completion at vtable call0x50ab98 and eventual drawable work are unknown. Earlier sample PC0x350064/LR0x354658 was not evidence of blocking. Missing panel/calibration paths coexist but are not shown causal. ENTER/EXIT durations exclude deferred Qiling scheduling; one unpaired main write does not prove persistent wait.

**Challenge/check:** independently derive store loops/object offsets/call returns from original bytes, correlate checkpoints with raw log order and filters. A repeated identical object/path without real returns or incorrect main-ID filter would challenge progression. Measuring parent bound/return and natural subsequent display work is a proposal requiring a new scope, not an executed result.

### C25 — No original server-visible drawable window/UI is established; milestone2 is the supported endpoint

**Type:** instrumented negative observation and explicit success-criteria comparison; E28–E30.

**Evidence:** R28 `session-summary.json.milestones`, R29 summary and R30 `session-summary.json.highest_completed_milestone=2`, `milestone3_achieved=false`, `original_UI_capture=false`; corresponding supervisors record tree-query exit0/root_children0. R30 retains17 `logs/startup-natural-01-window-tree-*.txt` queries and raw `captures/*root.xwd`; derived PNG/summary reports uniformly black800×480 root pixels. Raw captures are server root output, not firmware-generated UI screenshots. C23's InputOnly request is still client-buffered.

**Limits:** finite sampled root-tree/capture intervals do not prove a window never existed at another time, elsewhere, or under a different environment. They do show the required server-visible drawable original window/captured output criterion was not evidenced. Display API return, synthetic audio and thread startup do not equal usable virtual instrument or complete SP-16 emulation.

**Challenge/check:** independently read the XWD pixel data and tree reports/capture timing; seek actual server acknowledgment/tree membership and original drawable output. Any valid retained original UI/window artifact within the claimed interval would directly challenge the negative; no synthetic host drawing should be substituted.

### C26 — Worker timeout does not guarantee process stop; R30 stopped by independent supervisor with absent native finalJSON

**Type:** observed alarm/continued logs and host supervision; E27/E28/E30.

**Evidence:** R30 console line22124 records native deadline_stop at76.023029s; main loop/function events continue to76.467846s at lines22145–22148. `startup-natural-01-supervision.json` records stopping_condition `Independent host guest deadline`, guest wall78.013007s, process_cleanup SIGTERM, exit−15 and reaped=true. R30 summary has native_final_json_present=false and states finalPC/counters unknown. R28 independent wall78.013921s and R27 continued partial console similarly preserve native-alarm failures. R29 is counterevidence to inevitability: both attempts have complete native bounded-stop results and host reaped without guest signals.

**Limits:** `*-events-from-console.json` extracts actual partial events; it is not replacement native JSON. Host supervision closes the host process lifetime, not original guest clean shutdown or display-cause diagnosis. Existing process-state reports are historical snapshots, not guarantees of current future process state.

**Challenge/check:** independently review alarm handler/gevent propagation and compare elapsed log/supervisor clocks and PID ownership. A final native result truly retained elsewhere would resolve its absence; reconstructing one from partial logs would not. Verify cleanup/provenance rather than silently interpreting deadline event as successful termination.

### C27 — Unchanged input/copy and preserved archive claims are documented snapshots, not remote backup/restoration proof

**Type:** historical inventory/byte-link/mode verification; E26–E30.

**Evidence:** `docs/EMULATION_HANDOFF_VALIDATION.json` records26 selected dependency ELFs and12,840 copied file/link entries per R24/R25 root; later per-session `integrity-verification.json` / `integrity-validation.json` record UPDs, original ELFs, source-copy/historical records and intentional fresh-cookie exceptions. R30 records12,841 file/link entries,26 ELFs,136,116 historical records and three dependency archives. `experiments/session-archive-20261008-105916/archive-verification.json`, `archive-manifest.json`, `restoration-dependencies.json`, `archive.sha256`, `session-close.json` identify frozen archive content/digest/dependencies and external checks; `superseded-initial-build/` preserves the first build rather than hiding it.

**Limits:** original identity assertions depend on manifest provenance/timing/coverage.26 ELFs do not include every future dlopen object. Root content/link comparison is not full boot fidelity; permissions/metadata coverage differs by checker. Archives are on the same disk; base macOS/Python/static inputs remain external; no relocated/restored runtime test or off-device backup is established. Current hashes can check surviving bytes, not prove bytes never changed before the earlier manifest.

**Challenge/check:** independently verify streamed archive members against external manifests and dependency archives, documenting modes/links/coverage. Actual restore in a fresh destination and off-device verification, if newly authorized, would establish stronger claims. Unexpected preserved-original differences challenge integrity; changed derived docs must be distinguished from original binaries.

### C28 — Unimplemented-syscall warnings do not establish reliable ENOSYS or success returns

**Type:** historical observed warning messages plus **current static code inference**, not a dynamically verified historical return-register result. **Scope:** held Qiling1.4.6 source and R24–R30 incomplete syscall paths.

**Evidence:** installed `experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/posix/posix.py:411`–415 warns for a missing syscall, raises only if `ql.debug_stop`, and otherwise performs no return-value assignment in that branch. R25 `logs/corrected-tls-console.log:1261`–1262 records unimplemented sched_getparam/getscheduler, line1342 sync, line1361 sched_getaffinity and lines31655–31657 sched_get_priority_min/max/setscheduler. R30 `logs/startup-natural-01-console.log:1265`–1266,1444,1468 retains corresponding warnings. Earlier startup records include unimplemented sched_setaffinity/epoll before scoped replacements. Later harness `probe.py:199`–204 **explicitly** returns−38 for intercepted sched_setaffinity; this is distinct from the installed implicit missing-syscall branch.

**Limits/implications:** current branch inspection suggests guest r0 may retain its input/previous value rather than receive Linux ENOSYS; no new dynamic experiment and no retained historical register-before/after evidence establishes each warned call's actual return. A missing scheduler implementation can therefore change original control flow or give misleading apparent success. Original binary progression/API calls remain observations within this substituted environment; they do not establish faithful Linux scheduler/priority/affinity/sync behavior, real-time timing or instrument correctness. Do not silently reclassify every “not implemented” warning as a tested negative errno.

**Challenge/check:** independently inspect the exact held syscall dispatch/return-setting code and interception precedence, including debug_stop state. Under a newly authorized runtime scope, capture syscall input/output registers and the original caller's branch, or specify faithful explicit errno/semantics before comparing outcomes. Evidence of a separate installed hook assigning a return for a given warned call would limit this inference; a future fixed emulator cannot retrospectively supply historical return proof.

## Unresolved propositions and unsupported extensions

| ID / proposition | Current status and support | Concrete challenge / resolving evidence |
|---|---|---|
| U01 — Most selected sampler/sequencer/UI feature logic belongs to A160/called libraries | Parked H01; launch chain/imports/main-processor role, no selected feature function map or implementation | Define user's exact behavior/acceptance criteria, then trace consumers/calls/resources in the exact release. Finding another responsible component disproves a universal app-location claim. |
| U02 — SUB1/PANELCOM1→M1, SUB2/PANELCOM2→M2; apl→application stage | Parked H02; matching names/two payloads/two controllers/labels | Statically prove updater dispatch/write target and version-stage association. Naming alone is insufficient. |
| U03 — Supplied Bsp can reproduce relevant shipped kernel/boot behavior | Parked H03; broad versions and init scripts agree, conflicting target/prefix/version records remain | Recover shipped initramfs/config; resolve exact patches/toolchain; produce independently compared isolated build under a separately authorized scope. |
| U04 — Missing panel/calibration makes startup wait or prevents flush | Unestablished. Missing paths are logged, while R30 main completes ongoing work | Trace actual consumer/wait/return dependency, measure parent completion and naturally subsequent display action. Do not establish it by injected panel success or forced flush. |
| U05 — Parent initialization eventually completes and produces drawable output | Unknown; continued progress observed through bounded interval, parent count/bound not measured | Count/bound/return at0x50ab98/0x50ab9c and allocation caller chain under new authorized ceiling. Any persisted loop/late fault can challenge eventual success. |
| U06 — Full updater accepts an unchanged re-encoded/custom update | Unknown; wrapper CRC/decode only, no repacker/acceptance/hardware installation result | Statically trace full verification and re-encode/repack byte equivalence in isolated derived outputs if newly scoped. Hardware acceptance/recovery is a separate authorization/evidence requirement. |
| U07 — Safe rollback, tested recovery, debug console, NAND/eMMC dump | Unknown; partition declarations/manual documentation only | Explicitly scoped non-destructive observations/dumps and a separately authorized demonstrated recovery procedure. No A/B-label inference closes this gap. |
| U08 — Universal key, DJS-1000 common format/platform result | Unknown; two local releases decoded; no held DJS-1000/cited community experiment identified | Independently sourced additional exact versions and preserved comparative artifacts; distinguish external claims from local reproduction. |
| U09 — Four physical cores fully used; CPU/RAM advantage or DSP performance ratio over MPC2500 | Unsupported in retained measured evidence. Earlier exact agent answer in `HISTORY_SOURCES.json` claimed1GB RAM and25× aggregate rated clock-cycle capacity with primary-source citation targets and explicitly disclaimed a measured25× performance ratio. Datasheet content/applicability and live capacity/clocks remain independently unverified in this handoff; request masks/manual parts do not measure utilization. | Recover/verify exact datasheets/board variants and active enabled-core/clock/RAM data, then match workload measurements. Rated aggregate clocks are not a throughput benchmark. |
| U10 — Complete virtual instrument or feature readiness; effort ranges are established | Unsupported. No original drawable UI, panel/input response, sample/sequence acceptance test, real audio, firmware modification or deployment | Sequential criteria with original output and behavior tests in scoped environments. Old hours/days/weeks/months ranges in `decode/FINDINGS.md:44`–58 are agent planning judgments, not measurements/commitments. |

## Historical contradictions and strongest counterevidence to carry forward

- `decode/PROCESS.md:11`, `FINDINGS.md:58` and static snapshots say no application execution/active deeper work; later E24–E30 document narrowly authorized execution. Preserve their dates/scopes rather than reading them as current claims or rewriting them.
- R28's `session-summary.json.interpretation` says pending **Xlib** request is plausible and no buffer snapshot exists. E29 disproves the simple Xlib-buffer assumption: post-return bytes are in **libxcb**; empty Xlib output alone would have led to a wrong send conclusion.
- E29's proposed causal startup wait was unresolved, and its sampled PC did not establish waiting. E30 records actual returns/changing objects and continued initialization, challenging a persistent-block/hardware-cause assertion.
- The initial E29 return-hook collision and its skipped snapshot remain material measurement failure evidence. The corrected retry is stronger for transfer timing; the first probe must not be silently relabeled equivalent.
- Null-audio capture support, local IPC/epoll, TLS return correction, flag/name translation, high loader, aliases, fast mode and security/operation rejections are all measurement conditions. “Unchanged firmware binaries” does not mean “unmodified original environment.” Review the substitution ledger before extending any result.
- Retained unimplemented-syscall warnings are paired with a current installed-code branch that may leave the return register unchanged; they do not prove ENOSYS or successful scheduler/sync semantics. This implicit fallback can affect startup control flow independently of explicit fixtures (C28).
- A corrected bounded run without memory faults challenges the earlier allocator failure as a vendor defect, while repeated worker-alarm failures challenge the native-timeout reliability assumption. R29 successful bounded native stops show the failure is conditional.
- Archive verification is preserved together with a superseded build; local archive presence is not restore validation or an off-device backup. Exact external dependencies are part of reproducing the environment.
- The retained static current-code audit is stronger for present file equality than `before-rerun.json` is for historical chronology. Standalone decoder sample/full scripts/logs and raw historical failed-binwalk/wrong-key/entropy/bruteforce records remain absent; no specific such trials can be asserted. The formerly missing source-extractor implementation is partly recovered as current `/tmp` copies plus genuine historical command records; preserve those as recovered evidence, not a new replay or complete proof of all source extraction contents.
- Canonical no-datasheet-reviewed wording is contradicted by a retained exact historical agent answer that cites NXP/Samsung specifications. Preserve the answer/source targets, distinguish reported research from independently retained primary evidence, and do not promote rated component values to active device measurements or performance benchmarks.

Recommended independent review starts with C01–C06 input/transform identity, C22–C26 measurement coverage/negative UI observations, and C18 TLS causal limits. No review recommendation in this document authorizes executing firmware, replaying emulation, running vendor scripts or writing hardware.
