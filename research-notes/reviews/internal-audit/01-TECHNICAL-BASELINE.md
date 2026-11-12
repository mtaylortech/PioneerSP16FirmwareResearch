<!-- source: ../PioneerSP16Review/01-TECHNICAL-BASELINE.md | scrubbed -->

# Stage 1 — Technical baseline

Review date: October 9, 2026, America/Chicago. Companion [inventory] `Review/01-PROJECT-INVENTORY.md` (evidence not published) defines source coverage; [gaps] `Review/01-EVIDENCE-GAPS.md` (evidence not published) preserves limitations. This baseline is evidence and review guidance for future work; it authorizes no implementation or runtime action.

## Established capability boundary

The strongest demonstrated capability is **original firmware 1.60 application initialization and two attributable UI interactions under a modified ARM userspace emulator**. The application and selected shipped libraries retain original bytes. Emulator behavior, syscall contracts, filesystem/device fixtures, scheduler and host display support are modified or substituted. The shipped Linux kernel is not booted by this harness.

This supports targeted investigation of original application behavior. It does not demonstrate a complete virtual instrument, physical SP-16 boot, real DSP/audio correctness, modified firmware, a replacement OS, or a deployable update.

## Evidence classification

| Label | Meaning in this review |
|---|---|
| **V — verified** | Primary bytes, raw observations or documentary content substantiate the precise claim. Verification is scoped: documentary part identification is not physical inspection; saved emulator execution is not board execution. |
| **O — observed but unverified interpretation** | An event/measurement exists, but attribution, causality, completeness, reproducibility or generalization needed for the broader conclusion is missing. |
| **H — hypothesis** | Plausible interpretation or conditional prediction, not demonstrated behavior. |
| **A — unsupported assertion** | A positive claim would exceed available evidence. This identifies an inference to reject, rather than accusing every historical document of making it. |
| **U — unknown** | Evidence insufficient; no claim of impossibility or universal absence. |

“Reproducible” below distinguishes **independent readback performed in Stage 1**, **recorded prior validation with retained inputs/code/results**, and **live replay not performed**. Multiple copied exports, retrospective summaries, and synthetic controls are not independent firmware executions.

## Firmware identities and packaging

The following digests were freshly recomputed from held files. Original `.UPD` authenticity/acquisition provenance is a separate gap.

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| 1.50 `TORAIZSP16VER150.UPD` | 99,493,908 | `11204911bfe20bde86824fef9d77cccd56cfeef7d101cc643b7c96a4b1a45e0a` |
| 1.60 `TORAIZSP16.UPD` | 99,495,956 | `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4` |
| 1.50 `decoded.iso` | 99,493,888 | `534ad8c01f5f3079fc7a8e0e398e904ee5fe4877bf832653e7bffffe85d3608b` |
| 1.60 `decoded.iso` | 99,495,936 | `6087b00add12936c4fe3964d62c72e61a3c2475c24b95dd1022fd17f87fac4eb` |
| 1.60 `EP085_Main_R` | 12,000,396 | `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464` |

Sources: [1.50 report] `decode/output/image1/report.json` (evidence not published), [1.60 report] `decode/output/image2/report.json` (evidence not published), [original 1.60 ELF] `decode/output/image2/payloads/pdj/pdj/EP085_Main_R` (evidence not published). Both saved audit reports say passed with empty mismatch lists. That recorded audit validates supported content; it does not erase later source-mode discrepancies.

| ID | Finding | Classification, evidence and limit |
|---|---|---|
| B01 | Held releases identify internally as 1.50/app Rev.6284 and 1.60/app Rev.6550. Panel revisions are Rev.5187 / Rev.3671 in both. | **V.** Plaintext trailers and extracted release/revision files agree with reports. Filename alone was not used. [S01] |
| B02 | Payload decoding uses AES-256-CBC, independent 512-byte sectors, IV LE32(sector modulo 2^32)+12 zero bytes, payload offset zero. Key input stops at LF/NUL, copies at most 31 raw bytes and zero-pads to 32. | **V, recorded source/binary-backed extraction.** Decoder and shipped cryptoloop/updater evidence agree. Full decryption was not replayed in Stage 1; no key bytes/digest disclosed. [S02] |
| B03 | Both UPDs have a 20-byte plaintext `LIVESAMPLER` version/CRC trailer. Ciphertext IEEE CRC32 equals its stored LE32 value. | **V, freshly checked.** CRCs `f1679304` / `6f3bb5a2`. Integrity consistency does not prove cryptographic authenticity or full updater acceptance. [S01–S02] |
| B04 | Decoded files are ISO 9660/Rock Ridge containers, with five tar/gzip payloads and three SquashFS 4.0 little-endian zlib filesystems per release. | **V, retained reports/audits and coherent files.** Fresh ISO digests match historical reports. No fresh full ISO/path/source audit. [S01] |
| B05 | Saved base payload counts are 12,232/12,228 regular files, 715 symlinks per release; nested records report 386 expansions per image (384 font gzip, documentation gzip, test tar). | **V about recorded audit/count scope.** Not an independent re-expansion of every nested container in this review. [S01] |
| B06 | Five special entries per release are metadata-only across base and nested extraction: three device nodes plus a test character node/FIFO. | **V, records.** Original archives and metadata retained; host trees are not full Linux device trees. [S01] |
| B07 | Source-mode fidelity fails despite host-relative re-extraction success. | **V.** Prior read-only comparison reports 60 tar-directory and 22 SFS-file differences, separate from 1,430 symlink mode-semantic differences. Stage 1 independently read tar headers for image2 `tmp` 01777→0755, `var/tmp` 0777→0755, `var/ftp/pub` 02777→0755 at offsets 1,201,664/4,608/6,656. No chmod/extraction performed. [S03] |
| B08 | Both kernels are uImages named Linux-3.0.101-2790-gc248ed7; each header/data CRC passes. Their files are different according to retained identities. | **V, CRCs freshly checked; differences recorded.** Same name does not establish identical builds or reproducibility from supplied source. [S01] |
| B09 | PANELCOM1/2 S-record files are individually identical across releases. | **V, fresh hashes:** `36c8fab3b59bde8aebd27ae53d8bedba30a6e30b86fe04bd32ee78b7ee4da65e` and `b69add11e83a6d51d008856bf0e24edd3820a0c1651b0ce2070eb7cf977c7546`. No panel firmware execution or comprehensive protocol map. [S01] |

## Intended hardware and software architecture

| ID | Finding | Classification, evidence and limit |
|---|---|---|
| B10 | Service manual lists MAIN IC2000 MCIMX6Q5EYM10AD, two DDR3 devices K4B4G1646D-BCMA, NAND MX30LF2G18AC-TI, and eMMC THGBMHG6C1LBAWL. | **V documentary.** PDF page 49 / printed 46 inspected. Specific actual unit population, capacity available to software and active clock unmeasured. Earlier datasheet-based nominal-capacity inference is not a unit readback. [S04] |
| B11 | Manual assigns main/USB-A/MIDI control and audio processing to MAIN; M1/M2 use R5F364AENFA-U0, with M2 responsible for switches, encoders, touch, gain and pads. NAND/eMMC responsibilities are documented. | **V documentary.** No physical communication/control validation. A generic “DSP” signal-flow block does not identify a separate DSP chip. [S04] |
| B12 | Intended boot stack is U-Boot→Linux→BusyBox init→rcS/rc.local→apl_start→EP085_Main_R. | **V static.** Shipped inittab, rc.local and launcher directly inspected. Launcher loads snd-din-midi/midi_thru and has normal/testmode branches. No boot scripts executed. [S05] |
| B13 | `fw_env.txt` declares NAND layout, A/B kernel banks, NAND/MMC/network commands and normal boot defaults. Supplied initramfs describes RAM-root/SquashFS/UBI assembly. | **V static design evidence.** Not current hardware environment; supplied initramfs not shown identical to release-kernel initramfs. Two banks do not establish working rollback. [S05] |
| B14 | Main application is stripped, dynamically linked ARM32 little-endian EABI5; original imports include X11, ALSA, FreeType, ICU, libcld, allocator and standard runtimes. | **V ELF/artifacts.** Stage 1 independently checked machine=ARM, EABI flags and size/hash. Original RTTI/import/string information remains despite stripped internals. Proprietary application source not located. [S06] |
| B15 | Held source trees include Linux 3.0.101, U-Boot 2009.08 and BusyBox 1.20.2 with LTIB/build scripts; defconfig selects i.MX6Q, CPU_V7, preemption and ALSA PCM/raw MIDI. | **V source.** Selected config/scripts inspected. Toolchain scripts name GCC4.6.2/glibc2.13 Linaro2011.12. No successful matching build or release-specific source equivalence. Public drop is labeled 1.30. [S07] |
| B16 | 1.50 adds live sampling; 1.60 adds FX2 and MIDI routing changes. Operating manual describes digital insert effects and a discrete Dave Smith analog-filter circuit. | **V documentary, not reverse-engineered DSP.** Relevant local PDF pages read; 1.60 history dated October3,2019 and 1.50 June7,2018. Earlier manual is FX1-oriented. Algorithm/control protocol/sample-buffer processing remains unknown. [S04] |

## Experimental environment and substitutions

The historical runtime uses macOS ARM64, Python3.10.1, Qiling1.4.6 and Unicorn2.1.4 (saved version/requirements records). It loads the original app directly from a copied 1.60 rootfs. Stage 1 inspected the live-cycle probe's `Qiling([str(APP)], str(ROOT), ...)` construction and syscall/hook registrations. This is userspace binary emulation, not a machine/kernel boot.

| Condition | Evidence-backed status | Consequence |
|---|---|---|
| Loader/library layout | Loader relocated to `0x70000000`; missing `/lib` library paths mapped to shipped copied objects | Overcomes host/emulator loader problems; changes load environment, not guest application bytes. |
| TLS helper | Emulated ARM kernel-helper read supplies current thread `c13_c0_3`, replacing shared helper-word behavior | Addresses demonstrated per-thread TLS mismatch; does not prove every allocator/thread contract. |
| ALSA/device fixture | Original libasound uses null PCM; polling paths substitute regular empty/zero files | Silent synthetic transfers, no hardware timing/sound. Device-readiness/file-offset behavior differs from real nodes. |
| Local X11 | Private authenticated Xvfb/display tools, display-only fcntl flag translation and contained host support | Original X libraries and app draw, but display backend is substituted. Copied host tools were relocated/ad-hoc signed; “everything unchanged” is false. |
| ARM32 statfs/ioctl | Working ABI conversion and invalid-fd guard | Local emulator failures corrected; not a general implementation of all kernel interfaces. |
| Scheduling/select | Cooperative main/select plus post-font count313370 condition; sparse observation | Host durations are emulator/harness measurements; no hardware benchmark or low-latency proof. |
| Selected futex expiry | Named Juce Timer and ProjectManager verified finite relative WAIT paths receive saved-thread timeout/wake results | Live continuation/paint/loading progress shown. Other futex/timer contracts remain partial. |
| Clock | Installed `clock_gettime` uses wall datetime, multiplies fractional seconds by1e6, ignores clock ID; guest setitimer is a success-only stub | Verified timing defect. Separate correction remains uninstalled in milestone runs. Cause of startup/input delay is unproved. |
| Host execution/network controls | Fork/vfork/exec and external networking guarded; observed denied vfork preserved | A denied operation can be intentional containment, not original firmware failure. |
| Supervision | Latest runs record 600s native bounds and independent 605/608/610s TERM/KILL/reap inside1200s | Bounded stop is harness termination, not natural guest exit. Current cleanup evidence is stronger than earlier coverage. |

Sources: S08, S10–S13, S17–S18, S26–S27. Original app/library identities and material conditions must accompany any comparison. The inventory does not turn historical fixtures into authorization for a replay.

## Demonstrated runtime milestones

| ID | Accomplishment | Primary evidence and interpretation |
|---|---|---|
| B17 | Original entry/main and thread creation execute; null ALSA opens and sampled transfers return64 frames. | **V scoped API observations.** E25 final records16,911 writes and5,635/5,633 reads; call counts are not every-transfer success. 17 thread names/core requests recorded, affinity returns ENOSYS. A worker deadline TimeoutError coexists with the bounded-stop summary. Real audio, clean shutdown and actual core use are **U**. [S08] |
| B18 | Parent helper and enclosing construction, original font scan and subsequent resources complete under evolved conditions. | **V recorded frame/byte evidence.** Parent `0x50aaf4→0x342a74`; later enclosing returns; all five BDFs and17 scan faces; later1,314 resource returns. Neither a return-instruction visit nor resource count alone proves top-level startup. [S09–S10] |
| B19 | Correcting selected timer futex behavior permits original nonblack painting. | **V, one recorded changed-condition run.** Original `0x806840→0x805e38`, XPutImage callsite `0x806640`, matched returns, black-before/nonblack-after original drawable. Early observation stopped on observer failure. This supports the narrow correction/result, not general causality or stable instrument operation. [S12] |
| B20 | Persistent HOME and original no-file project completion are observed. | **V.** Worker resume request dispatch returns; later listener/state and main countdown1→0, eight downstream entry/return pairs, popup vector37→36 and hiding/controller release. Empty seed's absent resume files are not automatically a failure. [S13–S15] |
| B21 | Track1→Track2 responds to tagged input. | **V, raw+pixel readback.** Click(250,350), sent333.247s; press/release original XNextEvent consumption337.927/337.991s and matched `0x817cf0` handling by337.993s. Six selected captures through595.060s. Independent XWD comparison confirms3,420 changed pixels, bounding box[18,318,364,402]; preview visibly identifies Track2. [S16] |
| B22 | Mapped original startup returns, reaches main dispatch, accepts fresh async completion, and displays stable HOME in one guest. | **V, primary chain independently checked.** Initializer `0x571d24` return through`0x698548` at262.070216s; wrapper through`0xb4060`, result1 at262.070366s; dispatch boundary262.072164s; fresh readiness269.429529s. Raw log lines2624/2627/2632/3168. Native observation600.103793s; eight HOME captures284.889–594.731s. [S17] |
| B23 | HOME→MIXER handling and distinct output are demonstrated. | **V.** Fresh readiness261.663s; send331.732s; original consumption348.287/348.348s; thunk`0x2d4878`→handler`0x2d4348`, loaded navigation target`0x392100`, matched handler return348.667s and outer348.673s. Six complete Mixer captures374.934–594.663s. Raw handler return line3593. Native600.369311s. [S18] |
| B24 | Send identity/roster inspection succeeds without an edit. | **V.** Raw snapshots340.775751/347.757197s, lines3764/3920, identical to saved snapshot JSON. Matched controller/view/footer/widget/unit/parameter ownership; identifier cell`0xf6c700` differs from name cell`0xf6ab44`; inspected custom listeners empty, one recursive footer listener, two original motion targets no-op. Parameter0, min0/max127; display/UI range distinct. Desktop/global coverage unresolved. Native600.380244s; six stable Mixer captures. [S21] |

Stage 1 separately checked B22 lifecycle-byte points against original ELF in the lifecycle, Mixer and successful Send-inspection runs: **29 points each, zero mismatches**. Later Mixer and Send-inspection raw logs repeat lifecycle completion, strengthening the narrow initialization claim. The standalone observer's `full_startup_proved=False` reflects its lifecycle-only contract; the composite result additionally correlates same-run readiness and owned pixels. Neither field establishes physical/all-subsystem boot.

### Pixel reproducibility and timing limits

XWD parsing read25 big-endian header words, located data at header-size +12×color-count, checked payload length against height×stride, and recomputed SHA-256 over raw pixel bytes. The lifecycle run has eight identical HOME payloads, hash`7c665b7e7c8d1c846251f03f337420a6b904c3cbee02223a1dfbfc3234becd71`, plus one earlier different capture. Mixer navigation and Send inspection each have six complete Mixer payloads with hash`1e19b61b43809386bea6c3203b11227856f637a8034d25b470c343e178ccc609`. These hashes match the displayed state distinctions; independent ownership/tree/attribute receipts are saved separately in display-observations.

Track response handling occurs about4.7s after send; its first later changed capture does not measure exact redraw latency. Mixer changed pixels were first sampled0.285s after matched handler return; a complete Mixer was sampled26.267s after return, after a transitional3.05s sample. Those bounds are sampling observations, not precise paint durations or physical-device response times. Immediate helper-window negatives were superseded by full-run evidence.

## Static reverse engineering and feature knowledge

| ID | Discovery | Evidence status |
|---|---|---|
| B25 | Startup settings, UIThread, mode-dependent audio/MIDI objects,800×480 MainWindow and normal/rejection/exception branches mapped | **V static instructions; inferred purpose qualified.** Status/mode probe can exhaust30 iterations and proceed. It is not an established all-devices-ready barrier. [S22] |
| B26 | Navigation→activation→visibility/dirty propagation→timer/message dispatch→paint→XPutImage mapped; private Mixer→HOME and track-volume paths mapped | **V byte-backed static edges; runtime coverage partial.** Stage1 checked6,304 records in27 startup exports and29,085 records in209 private UI assembly files, zero mismatches. Historical UI verifier covers22,309 selected records; larger Stage1 count includes additional/repeated exports and is not29,085 unique discoveries. Bad boundaries/candidates retained. [S22,S24] |
| B27 | Send identifier conflation corrected; display decimal/fill/S-image routes mapped | **V static and later identity readback.** Interned construction identifier`ref_3_L_121` differs from Component name`Param3`; current preparation has56 synthetic controls. Signed decimal predicts one-count text change; float/raster fill can remain unchanged through quantization. Applied-state rendering remains **H/U**, not live verified. [S19,S21,S23] |
| B28 | Logical encoder3 is the supported editing candidate; producer/registration and a conditional active-footer dispatch are mapped | **V static mechanics; H about a successful future edit.** Panel opens`/dev/subucom_spi0.1`;128-byte read gate; conversion swaps six halfwords including+0x34; encoder3 observer registration resolved. Raw notification+0x14 reaches ViewManager no-op; conditioned editing+0x10 reaches`0x31a680`. Worker-thread deferred route/application remains unproved. [S25] |
| B29 | Reusable shared Ghidra project and Send batch integration exist | **V saved assets/receipts.** Shared `.gpr` and `.rep`, ARM:LE:32:v8/default, relocation modeling, original ELF base0x8000. Existing explicit reopen checks pass;33 annotations, four partial offset views,104-byte range body integrated. Stage1 did not reopen. Native database absent from Git. [S22–S23] |
| B30 | Original effect algorithms, processing order, coefficient generation, buffers, sample representation and audio verification remain unestablished | **U.** Names/assets/GUI/ALSA/JUCE threads are insufficient. “JUCE DSP implements the effects,” “separate DSP firmware,” or “plugin API exists” would be **A** without further evidence. [S04,S08,S24] |

Stage1 independently matched all **98 instruction-byte and25 data-cell records** in the accepted encoder trace to the original ELF. Literal pairs`0x9315e0=(0x14,1)` and`0x9315e8=(0x10,1)`, and target cells`0x8a1c58→0x1d1fe4` / `0x8a1c54→0x31a680`, agree. This does not validate loaded ownership, live worker-to-owner delivery, or a setter.

## Negative and uncertain results

The Send gesture run fails at382.803s on `SEND third registered Send Amount widget` before any Send helper, sample or setter. The combined assertion omitted actual failing operands, so its exact root cause is **U**; identifier role conflation is a supported static explanation, not a recovered RAM observation. The roster run fails at337.523s on `widget POP/saved LR`, with another widget inr4, before either snapshot. Both native finals are absent. Later successful independent inspection neither reconstructs their missing finals nor validates their uninstalled corrections. [S19–S21]

A one-pair post-font comparison showed281→441 resource returns at a common245s window (56.9% more), with longer validated path prefix. It is **V for that pair**, **O for a general speed/reliability improvement**. Reversed-order replication was inconclusive because control SIGBUS occurred before activation; timed broad-mode failures retain uncertain crash provenance. Mixer RSS samples show substantial late growth, but do not establish a leak, peak footprint or safe parallel-guest capacity. [S10,S18]

There is no demonstrated modified/replacement operating system, new instrument feature, real audio quality/latency, complete sequencer/sampler behavior, updater acceptance of a repack, or hardware recovery. These remain **U**, and asserting completion would be **A**.

## Reproducibility register

| Evidence class | Stage1 check | Reproduction limit |
|---|---|---|
| Original/update/ISO identity | Recomputed SHA-256; compared with report records | Does not authenticate acquisition/publisher. |
| UPD/kernel integrity | Ciphertext/trailer CRC and uImage header/data CRC recomputed | No decryption replay or updater/boot test. |
| Source metadata | Tar headers read directly; three source/host mode differences reproduced | Full source-mode census reused, not rerun. |
| Original/static instruction identity | ELF PT_LOAD address mapping; exported hex matched at addresses | Names/types/function boundaries/semantic interpretation separately qualified. |
| Runtime lifecycle | Read raw PROBE events and final; matched29 hook points in each of three runs | Saved observations, no new execution or all-subsystem invariant. |
| Input/pixels | Raw packet/handling records inspected; XWD hashes/difference recomputed; previews viewed | Single configured interactions, not broad usability or exact redraw latency. |
| Send inspection | Two saved snapshot events exactly equal raw log events; original static cells checked | No mutation/global-listener/deferred-application proof. |
| Cleanup | Closure/postflight/commands and current repair code/control records inspected | No new live census, no universal historical no-leak guarantee. |
| Harness/clock/observer controls | Source and recorded stdout/JSON/failures reviewed | No project controls executed; synthetic control counts are scoped to source identity. |
| Build/repack/hardware/audio | No successful evidence located | No reproduction claim. |

Read-only reproduction methods are ordinary SHA-256 streams, `zlib.crc32` with uImage header CRC word zeroed, ELF program-header address translation, raw PROBE JSON parsing, `tarfile.open(..., 'r:gz')` metadata reads, and XWD header/payload parsing. None requires importing project modules or running saved verifiers. Saved verifiers often write JSON and can copy themselves; they were inspected, not executed. Full decoder and `--audit` also write generated trees/reports and are outside this stage.

## Primary evidence register

Paths below identify starting artifacts and their adjacent raw records; linked handoffs supply navigation, while findings above identify the particular primary evidence actually used.

| Source | Artifact locations |
|---|---|
| S01 | [1.50 audit] `decode/output/image1/audit.json` (evidence not published), [1.60 audit] `decode/output/image2/audit.json` (evidence not published), reports/ISO/nested manifests beside them |
| S02 | [decoder] `decode/decode.py` (evidence not published), [cryptoloop] `extracted/pioneerdj_tsp/pioneerdj_tsp/BUILD/linux-3.0.101/drivers/block/cryptoloop.c` (evidence not published), decode/tmp static extraction records |
| S03 | [mode comparison] `experiments/offline-review-20261008-01/modes/README.md` (evidence not published), original rootfs4 tar versus payload host tree |
| S04 | [service manual] `ResearchSourceFiles/928c4c.pdf` (evidence not published) pp49/61, [operating manual] `ResearchSourceFiles/TORAIZ_SP-16_manual_EN.pdf` (evidence not published) pp3/38/39/46, [release history] `ResearchSourceFiles/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf` (evidence not published) p1, [update guide] `<ResearchSourceFiles/TORAIZ SP-16 Firmware Update Guide - AlphaTheta Help Center.pdf>` (evidence not published) pp1–3 |
| S05 | [fw_env] `decode/output/image2/iso/images/fw_env.txt` (evidence not published), [inittab] `decode/output/image2/payloads/rootfs4/etc/inittab` (evidence not published), [rc.local] `decode/output/image2/payloads/rootfs4/etc/rc.d/rc.local` (evidence not published), [apl_start] `decode/output/image2/payloads/pdj/pdj/apl_start` (evidence not published), supplied initramfs |
| S06 | [original ELF] `decode/output/image2/payloads/pdj/pdj/EP085_Main_R` (evidence not published), [original ELF verification] `ghidra/exports/independent-original-verification.json` (evidence not published) |
| S07 | [make_linux] `extracted/pioneerdj_tsp/pioneerdj_tsp/make_linux` (evidence not published), [toolchain definitions] `extracted/pioneerdj_tsp/pioneerdj_tsp/ltib_common.sh` (evidence not published), [defconfig] `extracted/pioneerdj_tsp/pioneerdj_tsp/config/platform/imx/imx6_defconfig.dev` (evidence not published) |
| S08 | [original startup] `experiments/emulation-20261007/README.md` (evidence not published), [synthetic audio runbook] `experiments/emulation-20261008/README.md` (evidence not published), corrected-tls-result.json and logs/corrected-tls-console.log beside it |
| S09 | [parent return] `experiments/parent-stop-policy-20261008-145156/HANDOFF.md` (evidence not published), [enclosing progress] `experiments/post-parent-startup-20261008-150354/HANDOFF.md` (evidence not published) |
| S10 | [font completion] `experiments/full-font-cache-20261008-1614-next-20261008-1712/HANDOFF.md` (evidence not published), [count comparison] `experiments/post-font-counted-quantum-20261008-repeat/comparison.json` (evidence not published), [failed replication] `experiments/quantum-replication-20261008/HANDOFF.md` (evidence not published) |
| S11 | [ARM32 statfs] `experiments/arm32-statfs-20261008/HANDOFF.md` (evidence not published), [ioctl] `experiments/ioctl-continuation-20261008/HANDOFF.md` (evidence not published), [Expose] `experiments/expose-chain-20261008/HANDOFF.md` (evidence not published), [select] `experiments/cooperative-select-20261008/HANDOFF.md` (evidence not published) |
| S12 | [first original painting] `experiments/timer-futex-20261009/HANDOFF.md` (evidence not published), run-1/timed_futex.py, supervision/guest.stdout.txt and captures beneath it |
| S13 | [persistent HOME/request queue] `experiments/supervisor-request-queue-20261009/HANDOFF.md` (evidence not published) |
| S14 | [worker completion] `experiments/worker-resume-completion-20261009/HANDOFF.md` (evidence not published) |
| S15 | [main consumer] `experiments/completion-consumer-live-20261009/HANDOFF.md` (evidence not published), result-verification.json and retained verification-attempt-1 |
| S16 | [Track evidence] `experiments/input-response-live-20261009/verification/input-response-analysis.json` (evidence not published), [raw log] `experiments/input-response-live-20261009/run-1/supervision/guest.stdout.txt` (evidence not published), captures and pixel-inspection beside it |
| S17 | [lifecycle result] `experiments/startup-lifecycle-live-20261009-165946/result.json` (evidence not published), [raw log] `experiments/startup-lifecycle-live-20261009-165946/run-1/supervision/guest.stdout.txt` (evidence not published), native final, display-observations and captures in run-1 |
| S18 | [Mixer result] `experiments/mixer-navigation-live-20261009-180208/result.json` (evidence not published), [raw log] `experiments/mixer-navigation-live-20261009-180208/run-1/supervision/guest.stdout.txt` (evidence not published), timing.json, visual/capture and performance records |
| S19 | [Send failure] `experiments/mixer-send-live-20261009-193048/result.json` (evidence not published), raw log/failure-analysis/full-verification.stderr; [current preparation] `experiments/mixer-send-preparation-20261009/HANDOFF.md` (evidence not published) |
| S20 | [roster failure] `experiments/mixer-send-roster-live-20261009-200343/result.json` (evidence not published), failure-context-summary and raw log; separate return-owner-correction in preparation |
| S21 | [inspection snapshots] `experiments/send-identity-live-20261009-200701/listener-snapshots.json` (evidence not published), [raw log] `experiments/send-identity-live-20261009-200701/run-1/supervision/guest.stdout.txt` (evidence not published), result/native final/display records |
| S22 | [startup explanation] `ghidra/STARTUP.md` (evidence not published), [export checks] `ghidra/exports/independent-original-verification.json` (evidence not published), refine exports, shared projects and provenance |
| S23 | [static Send batch] `ghidra/parallel-send-round-20261009/HANDOFF.md` (evidence not published), input/display/contract final evidence, integration/manifest.json and reopen logs; excluded model contributes no accepted technical conclusion |
| S24 | [private UI path map] `ghidra/parallel-ui-paths-20261009/HANDOFF.md` (evidence not published), verification.json and original assembly exports |
| S25 | [encoder original evidence] `ghidra/encoder3-panel-route-20261009/evidence.json` (evidence not published), raw slices, analysis.stdout/attempt-1.stderr; [listener route evidence] `ghidra/send-input-route-20261009/evidence.json` (evidence not published) |
| S26 | [installed clock source] `experiments/emulation-20261007/tools/venv/lib/python3.10/site-packages/qiling/os/linux/syscall.py` (evidence not published), [remediation] `experiments/audit-remediation-20261009/HANDOFF.md` (evidence not published), clock/cleanup/response/lifecycle control stdout and separate overlay |
| S27 | [lifecycle owned closure] `experiments/startup-lifecycle-live-20261009-165946/run-1/supervision/attempt-owned/client-closure.json` (evidence not published), attempt-supervision and endpoint-postflight-initial.json; analogous Mixer/inspection records |
| S28 | source extraction recovery `docs/handoffs/2026-10-08-independent-review/recovered-extractor/PROVENANCE.json` (evidence not published), genuine historical extraction commands/ledgers and retained scripts; these qualify older “extractor not located” statements |

