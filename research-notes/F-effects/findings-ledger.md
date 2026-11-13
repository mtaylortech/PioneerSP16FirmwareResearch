# Effects findings ledger (firmware 1.60) — scrubbed research notes

> **Editor's note.** This is the effects research ledger as it stood at the pinned research commit (cycles 001–009),
> copied for traceability: every `F0xx` ID cited in [`docs/effects/`](../../docs/effects/) is defined here with its
> evidence. It is a raw lab record, not a polished document; read [`docs/effects/README.md`](../../docs/effects/README.md)
> first. Edits are limited to private paths, private folder names and owner references, and are logged in
> [`../EDIT-LOG.md`](../EDIT-LOG.md); no claim or label was changed.
>
> - `harness/models/*.py` are published as [`tools/fx/*.py`](../../tools/fx/).
> - Other `harness/…` scripts are published unchanged in [`tools/fx/verify/`](../../tools/fx/verify/README.md). `kb/cycles/…` cycle notes, `kb/functions.md`, and run outputs (`harness/out/…`, critic scratch runs)
>   belong to the unpublished research workspace **(evidence not published)**. The function table is published as
>   [`symbols/fx-functions-1.60.csv`](../../symbols/fx-functions-1.60.csv); open hypotheses as
>   [`docs/open-questions.md` → Effects](../../docs/open-questions.md#effects).
> - `target/…` and `decoded/lib/…` are the researcher's local copies of the 1.60 application and libraries; they are not
>   included (see [`docs/firmware-reference.md`](../../docs/firmware-reference.md)).
> - Hash prefixes such as `95cc5e6a…6cc3` identify emulator/report outputs, not firmware.
> - Entries R001–R005 are **[1.50]** facts carried from earlier work and have **not** been re-located to 1.60.


Each entry: claim, label, evidence (command → output, or a source file with its own evidence).
1.60 addresses unless marked **[1.50]**. Seeded 2026-11-12 (setup, before cycle 001).

## Target and environment (1.60)

**F001 — Target identities.** `confirmed`
- `target/EP085_Main_R_fw160`: 12,000,396 B, SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`.
- `target/TORAIZSP16_ver160.UPD`: 99,495,956 B, SHA-256 `ff1cc60c4b6e2a3793196486826e78eb223e2f86cd95b5c968f6fca3ade537a4`.
- Evidence: `sha256sum target/*`, matching the project's recorded hashes. The UPD hash also appears under release 1.60 in the project's firmware catalog (published as [docs/firmware-reference.md](../../docs/firmware-reference.md)).

**F002 — Main binary format.** `confirmed`
- 32-bit LE ARM ELF, EABI5, dynamically linked (`/lib/ld-linux.so.3`), GNU/Linux 2.6.31, stripped.
- ELF entry 0xb5cc8. This is the ELF entry, not the "mapped main entry" 0xb3ac4 in the earlier 1.60 analysis handoff ([research-notes/history](../history/analysis__ghidra-1.60-20261009__HANDOFF.md)).
- First PT_LOAD at vaddr 0x8000, so the Ghidra image base is 0x8000.
- Sections: .text 0x116f8 (size 0x8205b0); .rodata 0x831cb0 (0x29207c); .data 0xb70e20; .bss 0xb816b0 (0x3ed5dc).
- 20 DT_NEEDED libraries: libX11, libXext, libasound, libdl, libfreetype, libpthread, librt, libcld, ICU 51 (7 libs),
  libtcmalloc, libstdc++, libm, libgcc_s, libc.
- Evidence: `file`, plus a Python ELF header/section/dynamic parse (2026-11-12).

**F003 — CPU / ABI attributes.** `confirmed` (attributes)
- `readelf -A`: Tag_CPU_name "7-A", Tag_CPU_arch v7, Thumb-2, Tag_FP_arch VFPv3, Tag_Advanced_SIMD_arch NEONv1,
  Tag_ABI_HardFP_use Deprecated. No Tag_ABI_VFP_args tag is present.
- Use Ghidra language `ARM:LE:32:v7` for local headless runs. REA in Claude Code uses Ghidra's automatic choice (`ARM:LE:32:v8`),
  because REA does not allow a fixed language ID together with its checkpoint directory. `likely`: v8 (AArch32) decodes
  this v7 code identically; recheck any instruction-level surprise against a v7 import. Prior projects differ: the earlier 1.60 analysis handoff used `v8`;
  the storage study behind docs/storage.md used `v7` (evidence not published).
- `likely`: float arguments are passed in core registers (soft-float base AAPCS, inferred from the absent VFP_args tag). **Now `confirmed` by F021 (cycle 004).**
  Emulation harnesses must not assume hard-float. This is unverified at call sites.

**F004 — 1.60 shared libraries for emulation.** `confirmed`
- The `EP085_Main_R` in the researcher's local 1.60 decoder output has the same SHA-256 as F001, so that output is the 1.60 extraction (evidence not published).
- The 21 libraries (20 DT_NEEDED plus ld-linux.so.3) were copied with symlinks dereferenced into a local, git-ignored `decoded/lib/` (33 MB)
  from the installed-system payloads: `payloads/rootfs1/lib` (glibc 2.13, libstdc++ 6.0.16, libgcc_s) and `payloads/lib` (the rest).
  The updater ISO copies were not used.
- Every copy is byte-identical to its source (`cmp`). Hashes were recorded locally (evidence not published).

## FX inventory (1.60)

**F005 — Recovered FX classes are UI-side only.** `confirmed`
- The 1.60 class map (124 classes; published as [symbols/classes-1.60.json](../../symbols/classes-1.60.json)) holds 26 FX-related classes: 23 Fx*ViewController classes
  (Insert/Master × 2BandEq, Chorus, Compressor, Delay, Flanger, Lofi, MultiModeFilter, NoSelect, Phaser, plus bases;
  Insert-only Ducker; FxReverbViewController, FxLimiterViewController), FxSelectPopupWidgetController, `CompositeFxUnit` and
  `prj::EffectData`. Addresses are in kb/functions.md (published as symbols/fx-functions-1.60.csv).
- Re-verified: all 26 vtables have typeinfo at vtable−4, and the typeinfo name string matches (Python/lief check, 26/26 OK).
- **No DSP/processing class is in the map.** The binary's typeinfo name strings also include
  FxProcessorBase, InsertFxProcessor, MasterFxProcessor, SendFxProcessor, EffectBase, c_effect_base, EffectInOutGain,
  InsertFxDelay, InsertFxCompressor, SendFxDelay, SendFxReverb, SendFxCompressor, FxCompressor, PerformanceFxLoFi,
  MasterFxUnit, SendFxUnit, InsertFxParameterManager, MasterFxParameterManager, SendFxParameterManager and FxParameterManagerBase
  (`strings -n 6 | grep` on the target). Their vtables have not been located (H001).
- The binary has FxInsertDistortionViewController and FxMasterDistortionViewController name strings, but the class map has
  no Distortion classes. The 124-class map is therefore incomplete for FX.

**F006 — 1.60 release-note FX change.** `confirmed` (Pioneer document)
- `target/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.pdf` (`pdftotext`). The only FX item in 1.60 is that the
  second FX module (FX2) can be used on SAMPLE and THRU tracks.
- Earlier FX additions: 1.20 added LO-FI, DISTORTION and COMPRESSOR for track insert FX and master FX. 1.30 added PHASER
  (track and master FX), DUCKER (track FX), and the analog filter as a per-track insert.

## Carried from references — **[1.50], confirmed there, NOT yet re-located to 1.60**

Source: an unpublished 1.50 reference workspace (T2 static study; its public results are in [docs/project-format.md](../../docs/project-format.md)). Use only after H003 re-locates them.
- **R001** Step lock word = `[vct:2 | value22 signed | idx:8]`, `value22 = round(v*2097151)`. Empty = packed −32768 sentinel
  (`0x3f800000|idx`).
- **R002** FX lock slot = `23 + 6·unit + T[fxIdx]`. T = 72 signed bytes at [1.50] 0x8a8fa0, mapping FxParamIndex 0–71 to sub-slot 0–5.
  Two FX units (slots 23–28, 29–34).
- **R003** FX AsIndex writer [1.50] 0x34f3f0 switches on fxIdx 0–71. 49 non-default cases: 0–10, 23–34, 41–45, 50–54, 56–71.
  The reader switch is at [1.50] 0x350d98.
- **R004** `likely` (1.50): FxParamIndex is one flat list of per-effect-type parameters (~14 groups).
- **R005** The storage paths are identical in 1.60 (59/59 anchors, storage study T7 §5, evidence not published; summarised in [docs/storage.md](../../docs/storage.md)). Their matching method, an addresses-only
  instruction mask plus string and call-edge agreement, is the template for re-locating FX functions.

## FX processing classes (1.60) — cycle 001 (H001)

Evidence for F007–F011: kb/cycles/001.md (Worker + Critic), `harness/H001_fx_rtti_vtables.py`, `harness/H001_slot_align.py`,
`harness/H001_vcall_scan.py`, `harness/H001_disasm.py` (`python harness/H001_*.py --out DIR`; worker and critic outputs
byte-identical: fx_classes.json 95cc5e6a…6cc3, typeinfo_all.json f1eabaf3…bffda, f005_summary.txt e2112ce3…d5ba). Critic re-checked
typeinfo bytes, COPY relocs, PLT stubs and ten vtables independently (REA read_bytes + own lief/capstone).

**F007 — RTTI/vtables for all F005 processing classes exist in 1.60.** `confirmed`
- Typeinfo vptrs (R_ARM_COPY + 8): `__class_type_info` 0xb81800, `__si_class_type_info` 0xb81948, `__vmi_class_type_info` 0xb81748.
  Binary is non-PIE; dynamic relocs are only COPY/GLOB_DAT/JUMP_SLOT, so .rodata vtables hold final absolute values in the file.
- 2374 typeinfo objects, 8195 vtable groups in the binary. 20/20 F005 names have a typeinfo and ≥1 vtable. Per-class addresses in kb/functions.md (published as symbols/fx-functions-1.60.csv).
- ~30 further DSP classes not in the class map or F005: EffectBase children Chorus, Distortion, Ducker, Flanger, LoFi, MultiModeFilter,
  ParametricEqualizer, Phaser; kernels c_distortion, c_chorus, c_flanger; building blocks under `SamplingRateAndBufferSizeVariable`
  (DelayEchoBase*, DelayModule*, SmoothingDelayModule, LFO, SignalGate, Reverb9NXSBase, ReverbAllPassFilter, ReverbCombFilter, ReverbPreDelay);
  IIR filters (IirFilter → Iir{Lpf,Hpf}{1st,2nd}Order, IirBpf2ndOrder, IirOff; IirFilter2 → High/LowShelvingFilter, PeakingFilter);
  Parameter → ToggleParameter, LinearParameter, FxBeatParameter.
- No dedicated Distortion *processor* class exists for Insert/Master; distortion is the generic `Distortion`/`c_distortion`.
- FxParameterManagerBase additionally has 9 **construction vtables** (e.g. 0x843b4c, 0x843c84, 0x8443e4, 0x844a34), slot-identical to the
  primary 0x8430cc and referenced from VTTs (e.g. 0x843a60). (Critic finding, checked by critic.)

**F008 — FX class inheritance (1.60).** `confirmed` (si/vmi base fields)
```
juce::AudioProcessor ← IAudioProcessor ← ILoadEstimableAudioProcessor ← FxProcessorBase ← {Insert,Master,Send}FxProcessor
                                                                     ← MasterFxUnit, SendFxUnit
EffectBase ← Chorus, Distortion, Ducker, Flanger, LoFi, PerformanceFxLoFi, MultiModeFilter, ParametricEqualizer, Phaser,
             FxCompressor ← {Insert,Send}FxCompressor,
             InsertFxDelay (+DelayEchoBaseSingleDelay @+440), SendFxReverb (+Reverb9NXSBase @+440),
             SendFxDelay (primary DelayEchoBase; EffectBase @+568)
c_effect_base ← c_distortion, c_chorus, c_flanger   (kernels held by Distortion/Chorus/Flanger at this+0x1b8)
SamplingRateAndBufferSizeVariable ← EffectInOutGain, DelayEchoBase*, Reverb9NXSBase, Reverb{AllPass,Comb}Filter, ReverbPreDelay, delay modules, LFO, SignalGate
FxParameterManagerBase (vmi: ITriggerAndParameterReceiver, ISequencerTransport::Listener, ILfoProcessor::Listener,
  IScenePatternSwitchListener, ISceneEditListener, IEffector, IEffector::IListener) ← {Insert,Master,Send}FxParameterManager
ISceneEditListener, IScenePatternSwitchListener —virtual→ infra::ExistenceConfirmable (offset_flags 0xfffff403; non-polymorphic)
```

**F009 — Vtable end rule (1.60).** `confirmed`
- A vtable runs from its address point while each word is a code pointer (.text or a .plt stub such as `__cxa_pure_virtual` 0x11098);
  it ends at the first non-code word (next ott 0x0, an ASCII typeinfo name, a negative secondary ott) or where another typeinfo/vtable group starts.
- Reproduces all 26 class-map address points; 135 class/base pairs with no derived vtable shorter than its base. Class-map "8 slots" is a
  truncation (CompositeFxUnit has 52). Does not model vbase/vcall-offset words (harmless for ends).
- EffectBase (0x841fb8, 32 slots): 0/1 dtors; 2–22 and 28–31 base implementations (only 10, 11, 14, 15 overridden anywhere); 23–26
  `__cxa_pure_virtual`, overridden by all 15 concrete effects; 27 overridden by all; 18 never overridden.

**F010 — FX audio call chain (1.60, static).** `confirmed`
- Insert/Master/SendFxProcessor slot 5 (juce processBlock position; pure in IAudioProcessor) = 0x116860 / 0x112acc / 0x119994. Each makes
  exactly one call to the current effect's EffectBase slot 18 (+0x48) with `(effect, ch[0], ch[1], 0x40)`, ch = `*(AudioBuffer+0xc)`.
  0x40 is a **hard-coded sample count** (64): 0x100-byte memcpy per channel for a dry copy; the buffer's own size field is not read.
  InsertFxProcessor picks the effect as `this+0x80[this+0xa4]`, then calls 0xe8228(…, 0x40) (post-effect mix; role untested).
- EffectBase slot 18 = 0x106de4 (shared by all 16 EffectBase-family vtables) dispatches to **slot 25 (+0x64)** at 0x106ec8 and 0x106f10.
- **EffectBase slot 25 is the per-effect-type audio entry**: `int processEntry(this, float* L, float* R, int n)` (returns an int the
  dispatcher uses). n ≤ 64, **not always 64**: the dispatcher can skip the call (0x106f88, when n < [this+0xb0] with [this+0xa8]/[+0xac] set),
  advance pointers and shorten n by [this+0xb0] (0x106e24–0x106e48), or clamp n to [this+0xb8] when [this+0xb4] (0x106f20).
- Two dispatcher paths: in place on the caller's buffers (0x106efc–0x106f14, when `[[this+0xc8]+0xd0]==0`), or on internal copies at this+0xa4
  followed, if slot 25 returned 0, by 0x106c88 and 0x10770c(ctx, L, R, copyL, copyR, n) writing back (crossfade = `guess`).
- Slot 25 is often a thin wrapper; the per-sample DSP is in callees (LoFi → 0xfbf64; Phaser → 0x10d260; SendFxReverb → own slot 32 then
  Reverb9NXSBase @this+0x1b8 +0x48; InsertFxDelay → own slot 33; Chorus/Flanger → c_chorus/c_flanger slot 19 (+0x4c) with (L,R,L,R);
  Distortion → 0xfa78c(kernel, L,R,L,R)).
- Not promoted: "L/R processed in place" (`likely`); "slot 18 is slot 25's only caller" (untested); slot 26 = wet/dry update and
  slot 27 = reset (`likely`, worker only); c_effect_base slot 19 = kernel process (`likely`).

**F011 — Soft-float argument passing at a real call site.** `confirmed` (updates F003)
- InsertFxProcessor: the slot-14 parameter setter receives its float in r2 (`vmov r2, s15` @0x116b18); a double returns in r0:r1
  (`vmov d16, r0, r1` @0x116ae8). Emulation harnesses must pass floats in core registers. (Critic, cycle 001, capstone.)
- Tool note, `likely` (worker observation, not critic-checked): a bare `0x…` that is not a Ghidra function silently falls back to a file-offset reading in `procedure_pseudo_code`
  (0x105f2c returned FUN_0010df00). Always pass `ram:0x…`.

## Audio callback path (1.60) — cycle 002 (H002)

Evidence for F012–F015: kb/cycles/002.md (Worker + Critic), `harness/H002_alsa_imports.py`, `harness/H002_chain.py` (168 assertions,
0 failed), `harness/H002_disasm.py`, `harness/lib/sp16img.py` (`python harness/H002_chain.py --out DIR`; worker and critic
outputs byte-identical: chain_checks.txt f7fbee5e…b3e7, alsa_imports.txt 789e909c…3946, format_table.txt 59fc8452…c051). Critic
re-checked PLT names via lief GOT decoding, 13 vtables + typeinfos, every vptr/field store on the chain, and the hw_params argument values
with its own capstone code, plus REA `inspect_native_instruction` at ram:0x1a96fc / ram:0x1b1b98.

**F012 — The audio render loop is JUCE's ALSA thread in the app.** `confirmed`
- libasound PCM PLT stubs: writei 0xfd90, writen 0x10780, readi 0x10c9c, readn 0x113c8, wait 0x105a0, avail_update 0xfde4,
  hw_params set_format 0x10d8c / set_channels 0x101c8 / set_rate_near 0x10af8 / set_periods_near 0x11518 / set_period_size_near 0x10edc;
  pthread_create 0x11278, nanosleep 0x116bc. All PCM callers are in the JUCE `juce_linux_ALSA.cpp` region 0x589000–0x591000.
- Transfers: writei @0x58e2b0 / writen @0x58e004 in `writeToOutputDevice` 0x58df80; readi @0x58dc6c / readn @0x58dd0c in
  `readFromInputDevice` 0x58dbb0. Loop = `ALSAThread::run` 0x58e394 (vtable 0x936000 slot 2; typeinfo `juce::(anonymous)::ALSAThread`).
- Thread start: ALSAAudioIODevice::open 0x590320 → startThread(9) @0x590c00 → launchThread 0x646ef4 → `pthread_create(…, 0x6682ac, this)`
  @0x646f18 → threadEntryPoint 0x6680b8 → run() vt+8 @0x66811c. Object provenance: createDevice 0x58c224 stores vptr 0x936000 at
  device+0x18 (@0x58c364).
- Three output PCMs: `hw:ak4458audio,0`, `hw:ak4452audio,0`, `hw:ak4452audio,1`.
- Loop order per iteration (critic): snd_pcm_wait ×3, avail_update ×3, **writeToOutputDevice ×3** (0x58e8ec/0x58e944/0x58e99c), *then* the
  device callback (@0x58e4b0), *then* a Pioneer copy stage (0x5775c8 ×3 on per-PCM buffers at thread+0x2a0/+0x3d0/+0x500; ~16 calls of
  0x577d5c from the callback buffer thread+0x208). So output rendered in iteration k is written in iteration k+1. Roles of 0x5775c8
  (clear) / 0x577d5c (copyFrom) are `likely`; the channel map is not decoded (H015).

**F013 — Static call chain ALSA thread → Master/Send FX processors.** `confirmed` (every edge a direct `bl` or a virtual call whose
object's vptr store / field store is shown)
```
ALSAThread::run 0x58e394 → callback vt+8 @0x58e4b0 (callback at thread+0x130, stored by ALSAAudioIODevice::start 0x589ab8 @0x589b04)
→ AudioDeviceManager::CallbackHandler 0x59971c → audioDeviceIOCallbackInt 0x591f48 → callbacks[i] vt+8 @0x5920a8/0x5920f8
→ AudioProcessorPlayerChild (vtable 0x8635c8; slot 2 = juce AudioProcessorPlayer::audioDeviceIOCallback 0x60b560)
   [registered by AudioSystemBase::start 0x1b5b84: setProcessor @0x1b5bec, addAudioCallback @0x1b5bf8]
→ processor vt+0x14 @0x60b6b8 → HexaTrackAudioSystem::processBlock 0x1c12a0 (vtable 0x863da0, typeinfo 0x8640a8, ctor 0x1c2cac)
→ bl juce::AudioProcessorGraph::processBlock 0x5f91fc @0x1c140c → renderingOps[i] vt+8 @0x5f9294
→ ProcessBufferOp::perform 0x601f90 (vtable 0xaa3ad0) → [op+8]=node processor vt+0x14 @0x602010
→ CompositeFxUnit::processBlock 0x1a94cc → MasterFxUnit 0x1b1b80 (vt+0x14 @0x1a96fc inline | job 0x153980 @0x153990 pooled)
   → [MasterFxUnit+0x84] vt+0x14 @0x1b1b98 → MasterFxProcessor processBlock 0x112acc
→ SendFxUnit 0x1b3068 (@0x1a9714 inline | pooled) → [SendFxUnit+0x8c] vt+0x14 @0x1b308c → SendFxProcessor processBlock 0x119994
```
- Graph build = HexaTrackAudioSystem slot 55 0x1bc8d4: 8 named nodes via addNamedNode 0x1b6020 (multiTrackUnit +0x6a0, liveSampling +0x5a0,
  compositeFxUnit +0x698, masterOutUnit +0x6a4, headphoneUnit +0x69c, masterAssignableSelector +0x6a8, dsfDriveMaster +0x6ac,
  dsfDriveSend +0x6b0). MasterFxUnit ctor 0x1b1d30 → +0x608 (@0x1bdc68); SendFxUnit ctor 0x1b3314 → +0x604 (@0x1bdd5c);
  `CompositeFxUnit(master, send, pool=[+0x5cc])` @0x1bdeb4 → +0x698.
- CompositeFxUnit ctor 0x1aa808: vptr 0x861854; +0x8c = MasterFxUnit, +0x90 = SendFxUnit, +0x94 = pool. It passes its **own internal
  buffers** to the units (this+0xa4 Master, this+0x13c Send), filled from the incoming channels via 0x576afc (critic).
- MasterFxUnit ctor stores new(0xa8)+MasterFxProcessor ctor 0x114bc0 (vptr 0x842aa8 @0x114be4) at +0x84 (@0x1b1da0). SendFxUnit ctor stores
  new(0xb0)+SendFxProcessor ctor 0x11bbe4 (vptr 0x842d40 @0x11bc10) at +0x8c (@0x1b3408). Later re-pointing of these fields not swept (low risk).
- Threading: a `ParallelAudioProcessingManager` (vtable 0x849190, ctor 0x153e98, built unconditionally @0x1bc970 → +0x5cc before the
  CompositeFxUnit) runs in slot 5 0x1539c0: own slot 6 (assign jobs), wake workers, run its own job list on the calling thread (@0x153a30),
  then spin on `nanosleep(1000 ns)` until all four `ParallelAudioProcessingWorkerThread`s ("AudioWorkerSC3/SC4/RC3/RC4", vtable 0x849288)
  are done. So FX units run on the ALSA thread or a worker thread, but always inside the same device callback. Per-block assignment by
  load estimate (vt+0xb4) is `likely` (0x1541fc not read).
- InsertFxProcessor route (multiTrackUnitNode → 0x1bc7c8 → 0x1bacec → InsertFxProcessor ctor 0x118b0c @0x1bbd80) not traced (H009).

**F014 — Device/buffer format at the ALSA boundary.** `confirmed` unless marked
- App request: AudioSystemBase ctor @0x1b8300–0x1b8314 → 0x1b5e0c stores AudioDeviceSetup sampleRate = 44100.0 (+8) and bufferSize = 64
  (+0x10), then calls AudioDeviceManager::initialise 0x5961b8. That these values reach ALSA open unchanged is **`likely`** (hop through
  0x5961b8 not traced; rate list is runtime).
- `ALSADevice::setParameters` 0x58eea0 (Pioneer-extended, extra `flag` arg): access RW_INTERLEAVED (3) with NONINTERLEAVED (4) fallback;
  periods = 2; period_size_near = bufferSize; rate_near = rate; channels = flag ? 2·ch : ch; formats tried from table 0x936058 in order
  FLOAT_LE, FLOAT_BE, S32_LE, S32_BE, S24_3LE, S24_3BE, S24_LE, S16_LE, S16_BE, except `flag` forces S16_LE.
- In open 0x590320: when r8 == 0 (0x590924), channel cap 8 and flag = 1, else cap 2 and flag = 0. That r8 is the output-device index
  (so device 0 gets 16 × S16) is `guess`. Negotiated format is runtime-only.
- Float→int conversion is in writeToOutputDevice 0x58df80 (`vcvt.s32.f32` @0x58e164, converter vcalls @0x58e19c/0x58dfe4), downstream of
  all FX; the graph and FX work on float AudioSampleBuffers. 1 ALSA period = 1 callback = 64 frames = 1 FX block: `likely`.

**F015 — No FX offload device in the 1.60 application.** `confirmed` for the app binary only
- juce::AudioIODeviceType and juce::AudioIODevice each have exactly one subclass (ALSA); no JACK; 0 hits for fpga, sharc, blackfin, c674,
  dsp56, /dev/mem, rpmsg, remoteproc. `/dev` nodes: backlight, cdc_spi2.0, dac_spi4.0, din_midi, fb0, gpiodrv, mmcblk0p1, mtd12, null,
  sda, subucom_spi0.1, ttymxc1, ubi_ctrl. "dsp" only as the C++ namespace `dsp::` (TimeStretch, SamplingRateConverter).
- `DsfHipassDac::writeData` 0x384a38 writes one 2-byte word per call (control, not audio). Single `mmap` call site 0x6468bc in JUCE code.
- Together with F010/F013: the FX DSP is CPU code on the path that produces the ALSA PCM output. Not examined: kernel AK4458/AK4452 driver,
  codec register setup, service manual (no PDF tool on the research host) → H017.

## FX type selection (1.60) — cycle 003 (H013)

Evidence for F016–F019: kb/cycles/003.md (Worker + Critic), `harness/H013_fx_array.py` (26 assertions, 0 failed;
`python harness/H013_fx_array.py --out DIR`; worker and critic outputs byte-identical: h013_report.txt c1568cfb…d7af7d472,
h013.json 3bea32ca…893f616). Critic re-checked with its own ELF reader + capstone and REA xrefs (ram:0x11735c, ram:0x842c10, ram:0x84407c).

**F016 — Each FX processor owns one object per FX type, built in its constructor.** `confirmed`
- The list lives in **FxProcessorBase** (ctor 0x1128cc zeroes it): data +0x80, capacity +0x84, count +0x88; also +0x8c = array[current],
  +0x90 = array[pending], +0x94/+0x98 = ctor args, +0x9c = 0, +0x9d = +0x9e = 1 (flags; roles open).
- InsertFxProcessor ctor 0x118b0c (vptr 0x842c10 @0x118b44; only caller @0x1bbd80 in 0x1bacec) appends 10 objects; append i = index i:

| i | class (RTTI vptr) | new size | ctor |
|---|---|---|---|
| 0 | Chorus 0x842920 (+0x1b8 c_chorus, ctor 0xff008) | 0x2b0 | inline (EffectBase ctor 0x1067d8) |
| 1 | Flanger 0x8429a8 (+0x1b8 c_flanger, 0x100234) | 0x2b0 | inline |
| 2 | ParametricEqualizer 0x842198 | 0x4a0 | 0x10baec |
| 3 | MultiModeFilter 0x8420b8 | 0x4a0 | 0x109e8c |
| 4 | InsertFxDelay 0x841c80 | 0x5d0 | 0x103488 |
| 5 | LoFi 0x841a68 | 0x4b8 | 0xfd640 |
| 6 | Distortion 0x842898 (+0x1b8 c_distortion, 0xfa568) | 0x1d8 | inline |
| 7 | InsertFxCompressor 0x841618 | 0x790 | 0xf8a20 (→ FxCompressor 0xf7584) |
| 8 | Phaser 0x8422b8 | 0x4f0 | 0x10d654 |
| 9 | Ducker 0x841098 | 0x598 | 0xf61a0 |

- No null slot and no "no effect" object; "Off" is index −1. All 10 classes distinct. InsertFxProcessor has no subclass (typeinfo 0x842d04
  referenced only by its vtable). No vtable method of InsertFxProcessor re-points the list; non-virtual writers elsewhere unswept (`likely` none).
- After the build the ctor calls own slot 52 (0x118a9c → 0x117434, a 10-way switch setting normalised parameter defaults: role `likely`).

**F017 — Current/pending FX index and setFxType (InsertFxProcessor).** `confirmed`
- **+0xa4 = current index, +0xa8 = pending index** (both −1 from the ctor). processBlock 0x116860 reads both (@0x1168bc/0x1168c0); if
  current ≥ 0 it calls array[current] slot 9 (+0x24) @0x1168ec, and when that returns 0 sets current := pending (@0x116900). It skips the
  effect when current ≥u count (@0x11692c, so −1 = bypass), else runs `array[current]->slot18(L, R, 0x40)` (@0x116934 / 0x116a7c).
- **setFxType = vtable slot 47, 0x11735c `(this, int n)`** (only reference: vtable entry 0x842ccc). If n == pending: return. If current ≠ −1:
  old effect slot 6 (+0x18)(e, 1.0f), pending := n, or −1 if n < 0 (@0x1173b0/0x1173d0), +0x90 = array[n] (0 if n ≥ count). If current == −1:
  current = pending = n **verbatim** (no n<0 normalisation on this branch; @0x11741c). Only observed caller passes 0..9 or −1.
- Getters: slot 46 0x119900 → +0xa4; slot 48 0x116838 → +0xa8. Other writers of +0xa4/+0xa8: none found by a heuristic whole-.text sweep (`likely`).
- `guess` (not promoted as fact): slot 9 = "still fading out", slot 6 = start fade-out, slots 5/7/8 = start/fade-in. Slot 8's second
  argument on the switch-in path is unset (unknown).
- processBlock feeds the tempo (+0x94 vt+0x1c, clamped 1.0..999.0) as parameter 7 to indices {0,4}, {1,8}, {9} only (jump table
  @0x11694c) — exactly the five classes whose ctors name a "BPM"/"Bpm" parameter. Slot 45 0x11681c returns table 0x842be0[current] =
  [19,21,22,19,24,26,30,22,26,14] (else 1): `likely` the per-effect load estimate (vt+0xb4 in F013).

**F018 — Insert FX: effectId → index → type name.** `confirmed` (class ↔ name string ↔ effectId; on-screen labels not checked)
- InsertFxParameterManager (vtable 0x84407c) slot 32 0x1287d4 `(this, effectId)`: index = slot 53 0x1262b0 = `T[effectId−1]` for
  1 ≤ effectId ≤ 20, else −1 (T @0x843d98 = 4,−1,−1,0,−1,1,−1,2,−1,3,−1,6,−1,5,−1,7,−1,8,−1,9; inverse slot 54 0x1262cc, T+0x50 =
  4,6,8,10,1,14,12,16,18,20). Returns if index == processor pending; else a 10-way switch @0x128838 writes a static type-name String into
  `prj::EffectData` and calls `processor->setFxType(index)` (identity); default setFxType(−1) "Off".
- manager+0x1c is the InsertFxProcessor built beside it: 0x1bacec `new(0x148); bl 0x118b0c` @0x1bbd80 → `str r7,[sp]` @0x1bbd98 →
  manager ctor 0x12864c @0x1bbda0 → FxParameterManagerBase ctor 0x11fa0c stores arg 4 at +0x1c (@0x11fa78).

| index | class | name string | effectId |
|---|---|---|---|
| 0 | Chorus | "Chorus" | 4 |
| 1 | Flanger | "Flanger" | 6 |
| 2 | ParametricEqualizer | "FxType_2BandEQ" | 8 |
| 3 | MultiModeFilter | "FxType_MultiModeFilter" | 10 |
| 4 | InsertFxDelay | "FxType_InsertDelay" | 1 |
| 5 | LoFi | "FxType_LoFi" | 14 |
| 6 | Distortion | "FxType_Distortion" | 12 |
| 7 | InsertFxCompressor | "FxType_Compressor" | 16 |
| 8 | Phaser | "FxType_Phaser" | 18 |
| 9 | Ducker | "FxType_Ducker" | 20 |
| −1 | none | "Off" | any other |

- So the H013 wording "built in FX-type order" is **refuted**: array order ≠ effectId order; the manager translates.
- No insert type lacks a DSP object; no class serves two insert types; the analog filter is not among them.

**F019 — Master and Send FX processors use the same pattern.** `confirmed` (critic spot-check + harness assertions)
- Offsets shifted by 4: **+0xa0 = current, +0xa4 = pending** (−1 from ctor: Master 0x114bc0 @0x114be0/0x114be8, Send 0x11bbe4
  @0x11bc04/0x11bc08; Send also stores +0xa8). setFxType = slot 47 (Master 0x1132e4, Send 0x11a254); swap in processBlock (Master
  @0x112bf0, Send @0x119afc). Slots 5/46/47/48: Master 0x112acc/0x113398/0x1132e4/0x112cbc; Send 0x119994/0x11a308/0x11a254/0x119980.
- Both build 10 objects in the same order: 0 SendFxDelay (new 0x6c0, ctor 0x1054ac, stored as obj+0x238 = its EffectBase sub-object),
  1 SendFxReverb (0x478, 0x1123d0), 2 Chorus, 3 Flanger, 4 ParametricEqualizer, 5 MultiModeFilter, 6 LoFi, 7 SendFxCompressor (0x798, 0xf8a40),
  8 Distortion, 9 Phaser. So **Master "Delay"/"Reverb"/"Compressor" run the SendFx* classes** (RTTI).
- MasterFxParameterManager slot 32 0x1237cc: case j → setFxType(j) with names Delay, Reverb, Chorus, Flanger, FxType_2BandEQ,
  FxType_MultiModeFilter, FxType_LoFi, FxType_Compressor, FxType_Distortion, FxType_Phaser; default "Off" (harness assertion; critic re-ran
  it but did not decode the strings independently). Master/Send slot-53 tables 0x8436e0 / 0x8445c8 are identical, `T[effectId]` for 0..17:
  Delay 0, Reverb 2, Chorus 3, Flanger 5, 2BandEQ 7, MMF 9, Distortion 11, LoFi 13, Compressor 15, Phaser 17.
- `likely`: one shared effectId enum, with Insert passing id+1. Send-manager name strings not decoded; which type(s) the Send unit selects is open (H020).

## Single-function emulation (1.60) — cycle 004 (H007)

Evidence for F020–F025: kb/cycles/004.md (Worker + Critic), `harness/H007_effect_emu.py` with `harness/lib/emu.py` and
`harness/lib/darwin_ctr_fix.py` (`python harness/H007_effect_emu.py --out DIR` → `RESULT: 0 failed checks`, 20 PASS).
Worker runs (final3/final4) and critic runs (<critic scratch run>) are byte-identical: h007_report.txt 0d7199ac…45bc,
h007.json ca4af40b…da81, concatenated *.f32 8d0e7279…354b. The critic's neutralisation experiments (hook a function to return 0) were in
<critic scratch run> (not kept).

**F020 — A real 1.60 insert effect (LoFi) runs under unicorn end to end.** `confirmed`
- Loader: both main PT_LOADs are mapped from the file with their segment permissions. The real 1.60 `decoded/lib/libm.so.6` and
  `libgcc_s.so.1` are mapped and relocated. Every JUMP_SLOT is served by a listed Python stub (new/new[]/malloc bump allocator, free no-op,
  memcpy/memmove/memset, ios_base::Init/__aeabi_atexit) or by a real-library export (pow, log10f, tan and trunc were reached).
  Anything else traps by name. GLOB_DAT and R_ARM_COPY data abort on access. Abort self-tests pass.
- LoFi needs the `.init_array` static initialiser **0x137cc** run first: it sets 0xf52ebc = 17.0 and the globals read at 0xfc604/0xfc60c.
- Object: `new(0x4b8)`, then `0xfd640(obj, 44100, 64)` (the args of the InsertFxProcessor ctor call @0x118fec). The vptr is 0x841a68.
  Insert init for index 5, as in ctor 0x118b0c: slot 22 (e, 0) @0x1193d0; `0x106c7c(e, 1, 10.0f)` @0x1194c8 (stores +0xcc = 1,
  +0xd0 = 10.0); slot 52 0x118a9c (case 5 reads only processor +0x80/+0x88).
- Determinism: impulse, late impulse, silence and 1 kHz sine, 16 × 64 stereo samples, are bit-identical on independent emulators and
  processes. Pre-filling the heap with 0xA5 and the stack with 0x5A does not change the output.
- Known gaps: library pages are RWX; NULL+offset ≥ 0x8000 lands in mapped .text; read-before-write is tracked for .bss only; FPSCR = 0
  (the main ARM .text has no `vmsr fpscr`, `likely`); denormals follow QEMU's VFPv3/NEON model; the processor-level dry copy, 0xe8050
  and the post-mix 0xe8228 are not run.
- Host: unicorn 2.1.4 cannot start on the macOS research host (inside a restricted sandbox) without `harness/lib/darwin_ctr_fix.py`, because a user-mode `mrs ctr_el0` raises
  SIGILL. The fix emulates only that host instruction. A different cache value gives the same output hash, so the guest is unaffected.

**F021 — Floats pass in core registers (soft-float base AAPCS), app and libm.** `confirmed` (settles the F003 `likely`; extends F011)
- App call sites: pow @0xfb3d8 (x in r0:r1, y from `vmov r2,r3,d16`, result `vmov d17,r0,r1`), log10f @0x13818 (`movt r0,#0x4248`,
  result `vmov s14,r0`), slot 14 @0x116b20 (`vmov r2,s15`), 0x106c7c @0x1194c8 (`movt r2,#0x4120`, 10.0f in r2). 9 sites in total.
- The real 1.60 libm reads core registers too: `pow` starts `vmov d8,r2,r3; vmov d9,r0,r1`, and `log10f` starts `vmov s16,r0`.
- Emulation: with s0/d0/d1 = 0 at each call, pow/log10f results in r0(:r1) match host math at 0 ulp.

**F022 — Effect activation: slot 18 passes audio through until the EffectInOutGain gate is started.** `confirmed`
- EffectBase holds an `EffectInOutGain` gate at [e+0xc8] (ctor 0x10711c, vptr 0x842078). Slot 18 0x106de4 tests gate byte +0xd0
  (@0x106e00), then 0x107374 (apply pending target) and 0x1079d0 (active state). If the gate is inactive, it returns 0 with the
  buffers untouched.
- processBlock 0x116860: slot 9 (0x1059bc → 0x1079d0) is called once per block (@0x1168ec). If it returns 0: current := pending
  (@0x116900); if processor byte +0x9e == 0 (@0x11691c), slot 5 (e, 0, 1) @0x116b74, then slot 7 (e, 0) @0x116ba4 if +0x9d ≠ 0,
  otherwise slot 8. Slot 5 0x10623c resets the effect (slots 27/26/31) and calls 0x107310(gate, 2, e+0x30). Slot 7 0x105c58 calls
  0x107310(gate, 1, e+0x60).
- **+0x9e is cleared at the end of the InsertFxProcessor ctor** (`strb #0,[r4,#0x9e]` @0x1195f0). So a freshly built processor activates
  its effect on the first block. The other +0x9e writers are the FxProcessorBase ctor @0x112918 (=1) and 0x112a08 @0x112a1c; 0x112a08(proc, 1)
  also calls the current effect's slot 6 (e, 1.0f). +0x9d is written by 0x1129bc.
- LoFi (index 5) takes jump-table case 0x116a64: slot 18 (e, L, R, 0x40) @0x116a7c, with no tempo feed.
- Not established: the meaning of gate states 1/2, the fade law and its length (H018), and the "+0x9e = FX off" role (`likely`).

**F023 — After activation slot 18 runs the copy-and-mix path; dry/wet is applied in EffectBase.** `confirmed` (refines F010)
- With gate +0xd0 ≠ 0: memcpy L/R to [e+0xa4] / [e+0xa4]+4·[e+0x9c], then 0x1074c4, then slot 25 on the copies (@0x106ec8/0x106ecc). If
  slot 25 returns 0 (@0x106f40): 0x106c88(e, cL, cR, n), copy e+0x10..+0x17 → gate+0xc0, then 0x10770c(gate, L, R, cL, cR, n). The
  in-place path (0x106efc/0x106f10) runs only when +0xd0 == 0. Counts in emulation: 0x106ec8 ×2, 0x106f10 ×0 per 2 blocks.
- MIXRATIO = 0 (set through slot 14) gives the input bit-exact, **even with LoFi slot 25 neutralised**. So the wet = 0 bypass is in the
  EffectBase mix (0x10770c, fed by e+0x10/+0x14), not in LoFi code. That e+0x10/+0x14 is the wet/dry pair written by LoFi slot 26 is `likely`.

**F024 — EffectBase post-stage 0x106c88 filters every insert effect's wet signal (~10 Hz high-pass).** `confirmed` (stage); filter type `likely`
- 0x106c88 reads +0xcc/+0xd0, which 0x106c7c(e, 1, 10.0f) sets during Insert init. With it neutralised, a late impulse gives
  `1 0 0 0 0`. With it live: `0.999288 −0.0014227 …`, and a residual sine difference of rms ≈ 0.0036 at LoFi defaults.
- `likely`: a one-pole high-pass with fc = +0xd0 = 10 Hz (1 − π·10/44100 = 0.999288; −2π·10/44100 = −0.001425).
- Consequence for algorithm work: isolate an effect by calling slot 25 directly or by neutralising 0x106c88 and 0x10770c.

**F025 — LoFi parameters through EffectBase slot 14, observed effects.** `confirmed` (observations); formulas `likely`
- **Corrected by F026/F031 (cycle 005):** "FILTERTYPE 0 and 3 give the same output" and "BITDEPTH/REDUCTION 0.5 leave the output
  unchanged" are artefacts of the test setup. A value equal to the parameter's ctor "last" value, set before the first block, is never
  applied (F026). Once applied, type 0 is a 2nd-order HPF, BITDEPTH 0.5 gives 9 bits and REDUCTION 0.5 gives 1395 Hz. FILTERTYPE 1/2 =
  LPF/BPF and the cutoff formula are now `confirmed` (F028).
- Setter: EffectBase slot 14 0x105d24(e, index, float) → parameter vtable 0x840ac8 +0x10. LoFi applies changes in 0xfb20c and slot 26
  at the next slot 25. Index → parameter: 0 PREAMP, 1 REDUCTION, 2 BITDEPTH, 3 CUTOFF, 4 RESONANCE, 5 MIXRATIO, 6 FILTERTYPE; 7
  FILTERPOSITION is `likely`.
- Insert defaults (slot 52 case 5, normalised): PREAMP 0, BITDEPTH 1, REDUCTION 1, CUTOFF 0.566, RESONANCE 0.0510204, MIXRATIO 1,
  FILTERTYPE 3, FILTERPOSITION 1.
- Each of BITDEPTH 0, REDUCTION 0 (sample-and-hold, 854 repeated samples), PREAMP 1, and FILTERTYPE 1 or 2 changes the output. Each
  change disappears when LoFi slot 25 0xfc0f4 is neutralised, so they are LoFi's. FILTERTYPE 0 and 3 give the same output. Type 1
  responds like a low-pass and type 2 like a band-pass (`likely`).
- The block-0/1 attenuation at defaults (rms gain 0.81/0.75 through slot 18; 0.108/0.612 calling slot 25 directly) comes from LoFi
  slot 25's own start-up, not from the gate.
- `likely` (one point): LoFi filter cutoff = 20·1000^CUTOFF Hz ([obj+0x4a4]+0x18 = 997.769 at CUTOFF 0.566; pow @0xfb3d8).

## LoFi algorithm (Insert index 5; also Master/Send index 6) — cycle 005 (H021)

Evidence for F026–F031: kb/cycles/005.md (Worker + Critic), `harness/H021_lofi_model.py` and the own-code model `tools/fx/lofi.py`
(`python -B harness/H021_lofi_model.py --out DIR` → `RESULT: 0 failed checks`). Worker runs fin_a/fin_b and the critic run
<critic scratch run> are byte-identical: h021_report.txt 9273c853…2677, h021.json f3316770…d839, concatenated *.f32 86f8975a…74a4.
The critic's extra cases (<critic scratch run> clipping to ±1e4, denormals, odd block sizes, 48-block random parameter
walks, out-of-range values, NaN/inf) and mutation tests (mut.py: 4 deliberate model errors, each caught) were not kept in the repo.

**F026 — Parameter change detection: a slot-14 value equal to the ctor "last" value is not applied.** `confirmed`
- `Parameter_consumeChange` 0xf0ffc: choice parameters (kind +0x10 == 0) compare ints last +0x40 / current +0x44; float parameters (kind 1)
  compare last +0x24 / current +0x28 within ±FLT_MIN. `LinearParameter_setValue` 0xf0874 (slot 4) stores floats at +0x28 unclamped and
  choices at +0x44 = (int)v.
- LoFi ctor "last" values: every float parameter 0.5, FILTERTYPE 0, FILTERPOSITION 2. So a value equal to these, set before the first
  block, never reaches the DSP state. Harnesses must apply the defaults with one block before setting test values. `likely`: every
  effect built on these Parameter objects behaves the same.

**F027 — LoFi slot-25 signal flow.** `confirmed` (REA decompile + capstone, critic re-check, bit-exact emulation match)
- Slot 25 0xfc0f4: 0xfb20c applies changed parameters; the position SignalGate [obj+0x4a8] (132-sample linear fade = round(3 ms·fs)) handles
  FILTERPOSITION swaps (+0x4b0 := +0x4ac when the gate is closed, or mid-block when a fade-out ends, @0xfc180/0xfc1ec); then 0xfbf64; then
  slot 26 if MIXRATIO changed (@0xfc170). Returns 0. No other gain or clip in slot 25; dry/wet and the 10 Hz HPF follow in EffectBase (F023/F024).
- 0xfbf64: position-gate gain on the input (0xf521c @0xfbf7c), then by +0x4b0 (@0xfbf84):
  - +0x4b0 ≠ 0: preamp/clipper 0xfb6e4 → crusher 0xfaf28 (only if bits < 32) → sample-and-hold (inline 0xfbfc4–0xfc010) → filter 0xfbb70.
  - +0x4b0 == 0: filter → preamp → crusher → sample-and-hold.
  So FILTERPOSITION 0 = filter first; 1 and 2 = filter last (identical output). UI labels `guess`.
- Preamp 0xfb6e4: y = clip(x, ±1/g)·(1 + 0.2g)·0.8333333 (float32), g ramping linearly to its target over 44 samples. Small-signal gain
  (1 + 0.2g)/1.2 = 0…+26.8 dB; output ceiling (1 + 0.2g)/(1.2g) falls from 1.0 to 0.173 as g rises (critic correction).
- Crusher 0xfaf28: y = s·(trunc(2^b·√|x|)·2^−b)², s = sign(x) (x > 0 → +1, else −1); trunc in double via libm. Odd-symmetric truncation
  of the √-companded magnitude (plain rounding / plain truncation refuted on a −1…+1 ramp).
- Sample-and-hold: phase φ, step s = fs/rate. If φ < 1: φ += s, hold := x, output x; else output hold. Then φ −= 1. No interpolation.
- Filter 0xfbb70 [obj+0x4a4] (ctor 0xfc5e4, 0x44 B) holds 4 sub-filters in this order (RTTI): 0 `IirHpf2ndOrder` (vt 0x840c48),
  1 `IirLpf2ndOrder` (0x840c28), 2 `IirBpf2ndOrder` (0x841918), 3 `IirOff` (0x841938, process `bx lr`). Its own SignalGate (+0xc,
  132 samples) is applied after the sub-filter (@0xfbe50).
- Biquad process 0xe16dc: direct form I, NEON with L/R in two lanes: v = x + k·y_prev (k = +0x24 = 0 in LoFi);
  y = b0·v + b1·v1 + b2·v2 − a1·y1 − a2·y2, in that order. On a type switch, flag +0x48 makes 0xe1844 re-filter the last 4 inputs with the
  new coefficients.

**F028 — LoFi parameter → coefficient formulas.** `confirmed` (79/79 readbacks bit-exact at v ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9, 1})
| idx | parameter | formula | stored at |
|---|---|---|---|
| 0 | PREAMP | g = 10^((v·42)·0.05f) (float32 steps), 1…125.89; inc = (g − g_cur)/44 | [+0x498]+4, +0xc |
| 1 | REDUCTION | rate = round((float)(1000.0000610351562^v · 44.1f)) = 44…44100 Hz; step = fs/rate (1.0 if rate > fs) | [+0x4a0]+0xc |
| 2 | BITDEPTH | b = [1..16, 24, 100][round(17·v)] (table 0x841988); 2^b and 2^−b stored; b ≥ 32 → crusher skipped | [+0x49c]+0/+4/+8 |
| 3 | CUTOFF | fc = 1000^v·20 Hz (20 Hz…20 kHz), clamped to [5, fs/2] in the sub-filter | [+0x4a4]+0x18 |
| 4 | RESONANCE | Q = 0.2f + 9.8f·v (0.2…10; default 0.0510204 → 0.7); stored only if it changes by ≥ FLT_EPSILON | [+0x4a4]+0x28 |
| 5 | MIXRATIO | wet = v, dry = 1 − v (slot 26 0xfaef4) | EffectBase +0x14 / +0x10 |
| 6 | FILTERTYPE | t = (int)v, ignored unless 0 ≤ t ≤ 3; 0 HPF, 1 LPF, 2 BPF, 3 Off; switch crossfades through the filter gate | [+0x4a4]+0x10 → +0x14 |
| 7 | FILTERPOSITION | p = (int)v; immediate if filter Off, else position-gate fade | +0x4ac → +0x4b0 |
- Coefficients (computed in double, stored float32), w = tan(π·fc/fs):
  - HPF 0xe1bb8: b0 = b2 = 1/D, b1 = −2/D; LPF 0xe1ca0: b0 = b2 = w²/D, b1 = 2b0; both D = 1 + w/Q + w², a1 = 2(w² − 1)/D, a2 = (1 − w/Q + w²)/D.
  - BPF 0xe1d88: f = w/2π, f_lo = (f/2)(√(4 + 1/Q²) − 1/Q), f_hi = f_lo + f/Q, B = 2π(f_hi − f_lo), W² = 4π²·f_hi·f_lo;
    b0 = B/(1 + B + W²), b1 = 0, b2 = −b0, a1 = 2(W² − 1)/(1 + B + W²), a2 = (1 − B + W²)/(1 + B + W²). If Q ≤ 0.01 it sets Q = 0.01 and
    calls the log/assert routine 0x4f782c with "Q > 0.01" from `IirFilter::calcCoefBpf2ndOrder` (reachable only for RESONANCE < ≈ −0.019).
  - All three bit-exact against the model on 7 type/CUTOFF/RESONANCE combinations.
- Cutoff/Q smoothing (0xfb994): exponential steps, one per 44.1 samples (accumulator +0x38), multipliers from static init 0x137cc:
  0xf52ec0 = 1000^(1/250), 0xf52ec4 its inverse, 0xf52ec8 = 50^(1/100), 0xf52ecc its inverse. Steps = round(|log10(target/cur)/log10(mult)|) + 1.
  A cutoff jump needing > 38 steps fades the filter gate out, jumps, and fades back in. Coefficients are recomputed after each step chunk.

**F029 — LoFi object layout (0x4b8 bytes).** `confirmed` (emulated dumps; writers from disassembly, critic spot-checked)
- +0x1b8 + 0x5c·k: 8 LinearParameter objects (vt 0x840ac8) in the order PREAMP, BITDEPTH, REDUCTION, CUTOFF, RESONANCE, MIXRATIO,
  FILTERTYPE, FILTERPOSITION (+0x1b8 … +0x43c); fields as in F026.
- +0x498 preamp (0x14: N = 44, target g, current g, inc, steps left); +0x49c crusher (0xc: bits (ctor 32), 2^b, 2^−b); +0x4a0
  sample-and-hold (0x18: fs, fs, phase (ctor 1.0), step, held L, held R); +0x4a4 filter container (0x44: sub-filter vector data/cap/count = 4,
  SignalGate +0xc, pending/current type +0x10/+0x14 (ctor 3/3), cutoff target/current +0x18/+0x1c (ctor 1000), multiplier +0x20, steps +0x24,
  Q target/current +0x28/+0x2c (ctor 0.7), multiplier +0x30, steps +0x34, samples to next step +0x38, max steps +0x3c, bytes +0x40 recompute /
  +0x41 dirty); +0x4a8 position SignalGate (0x48); +0x4ac / +0x4b0 FILTERPOSITION pending / current (ctor 1/1).
- IirFilter sub-object (0x50, ctor 0xe1edc): +4 Nyquist, +8 fs, +0xc fc, +0x10..+0x1c 4 taps of {vL, vR, yL, yR}, +0x20 y_prev, +0x24 k,
  +0x28..+0x38 b0 b1 b2 a1 a2, +0x40 Q (double, ctor 1/√2), byte +0x48 re-seed flag.
- SignalGate (vptr 0x840e40, ctor 0xf4e5c, setFadeSamples 0xf505c, setClosedNow 0xf50b8): fs/block/1/fs at +0x10/+0x14/+0x18; ramp at +0x1c
  (state +0x20, current +0x24, target +0x28, inc +0x2c, remaining +0x30, ms +0x34 (role unknown), N +0x38, 1/N +0x3c); off 0.0 +0x40, on 1.0 +0x44.

**F030 — A pure-Python LoFi model is bit-exact to the emulated 1.60 slot 25.** `confirmed`
- `tools/fx/lofi.py` (own code; imports only ctypes and math; float32 by rounding double results through ctypes.c_float). 13 settings × 4
  signals × 16 blocks × 64 stereo: 52/52 runs bit-exact, covering FILTERTYPE 0–3, FILTERPOSITION 0/1/2, intermediate BITDEPTH/REDUCTION,
  PREAMP > 0 and mid-run changes. The critic added 30+ bit-exact cases (see section header) and showed the comparison catches deliberate
  model errors.
- Limits: the model uses the host libm (pow/tan/log10/trunc); BITDEPTH > ≈1.03 raises IndexError (table overrun not modelled); BPF Q ≤ 0.01
  log path not modelled; slot 27 reset not modelled; the VFP (non-NEON) paths keep denormals because emulated FPSCR = 0 (device FZ setting
  `likely` 0, F020); NEON flush-to-zero is modelled.

**F031 — LoFi start-up attenuation = two closed 132-sample gates in series.** `confirmed`
- The position gate and the filter gate are both built closed (`SignalGate_setClosedNow` 0xf50b8) and each opens on the first slot 25 as a
  linear 0 → 1 ramp over 132 samples (inc 1/132 in float32, 0xf55a4). Output = x·(n/132)² for n < 132. Per-block rms gain on a 1 kHz sine:
  0.1084, 0.6116, 0.999, 1.0 (emulation = model = formula), matching F025.

## MultiModeFilter algorithm (Insert index 3; also Master index 5) — cycle 006 (H023)

Evidence for F032–F037: `kb/cycles/006.md` (Worker + Critic, all 7 criteria CONFIRMED). Harness `harness/H023_mmf_model.py`, run
`python -B harness/H023_mmf_model.py --out DIR` → `RESULT: 0 failed checks`; worker and critic outputs byte-identical
(`h023_report.txt` sha256 9c33b389…25eb, concatenated `*.f32` 5ccbbf43…2baa). Model `tools/fx/mmf.py`. Emulation calls slot 25
0x108ee4 directly on an object built by the real ctor 0x109e8c(obj, 44100, 64) after `.init_array` entry 0x13a28 and the H007 Insert init.

**F032 — MultiModeFilter parameters.** `confirmed` (ctor registration hooks on 0xf1850/0xf1a00; slot-14 index map; Insert-default readback)
| idx | name | object offset | kind | ctor "last" | Insert default (slot 52, index 3) |
|---|---|---|---|---|---|
| 0 | CUTOFF | +0x1b8 | float 0..1 | 0.5 | 0.566 (997.77 Hz) |
| 1 | GAIN | +0x214 | float 0..1 | 0.5 | 2/3 (0 dB) |
| 2 | Q | +0x270 | float 0..1 | 0.5 | 5/98 (Q 0.7) |
| 3 | GLIDE | +0x2cc | float 0..1 | 0 | 0 |
| 4 | NONE | +0x328 | float 0..1 | 0 | 0 — registered, never read by processing (critic scan: only ctor/dtor touch +0x328) |
| 5 | MIXRATIO | +0x384 | float 0..1 | 0 | 1 |
| 6 | FILTERTYPE | +0x3e0 | choice 0..6 | 6 | 0 (LPF) |
| 7 | FILTERDB | +0x43c | choice 0..2 | 0 | 1 (12 dB) |
- Slot-14 index 8 changes nothing and returns 3. Index order differs from LoFi (F025): here 1 = GAIN, 2 = Q.
- Trap (F026): the filter container is built as kind 0 (LPF 12 dB) while FILTERTYPE's "last" value is 6, so FILTERTYPE 6 set before the
  first block is not applied and an LPF keeps running.

**F033 — MultiModeFilter signal flow.** `confirmed` (code + bit-exact emulation)
- Slot 25 0x108ee4, per block: 0x107d18 apply changed params (order CUTOFF, Q, GAIN, GLIDE, then FILTERTYPE+FILTERDB → 0x107c24) →
  0x108808 filter container [+0x498] (L, R, n) → 0xe89f0 GainRamp [+0x49c] in place → slot 26 0x107b30 if MIXRATIO changed (wet = v at
  EffectBase +0x14, dry = 1 − v at +0x10). Returns 0. No drive/saturation, LFO or envelope. EffectBase dry/wet and 10 Hz post-stage follow (F023/F024).
- Filter kinds (container 0x10913c, 7 stages of 0xc bytes built by 0x1080a0): 0/1/2 = one `IirLpf/Hpf/Bpf2ndOrder` biquad (12 dB/oct);
  3/4/5 = two cascaded identical biquads of the same type, each with Q' = √Q (`vsqrt.f64` @0x107b6c in 0x107b64) (24 dB/oct); 6 = no filter
  (no object; ramping skipped).
- Selection 0x107c24: t = FILTERTYPE, d = FILTERDB, both already truncated to int by slot-14 setValue (the rounding inside 0x107c24 is a
  no-op). t ∈ {0, 1, 2} → kind t if d == 1 else t + 3; any other t → 6. So FILTERTYPE 0 LPF / 1 HPF / 2 BPF / ≥ 3 or < 0 off;
  FILTERDB 1 = 12 dB, 0 and 2 (and any other value) = 24 dB (0 and 2 give identical output). UI labels for 3..6 and dB 0/2: `guess`.
- Biquads: shared DF-I NEON process 0xe16dc with the LoFi bilinear coefficient routines 0xe1ca0/0xe1bb8/0xe1d88 (F027/F028); cutoff
  clamped to [5 Hz, Nyquist] per stage. Coefficients bit-exact to `lofi.Biquad`.
- Smoothing (0x108608 setup + step loop in 0x108808): exponential cutoff/Q steps, one every 44.1 samples; cutoff multiplier 1000^(1/G)
  (+0x48, inverse +0x4c), Q multiplier 50^(1/100) (globals 0xf52ef4/0xf52ef8, static init 0x13a28). Step counts
  round(|log10(ratio)/log10(mult)|) + 1. A gated jump (filter SignalGate fades out over 132 samples, cutoff jumps, gate reopens) happens only
  when cut_steps > G·152/1000 and the GLIDE flag +0x42 == 0, i.e. only at GLIDE 0 (G = 64) and for ≥ 10 steps (ratio ≥ ≈2.50). A kind switch
  crossfades through the same gate.
- Output gain (GainRamp, ctor 0xe8900(obj, N = 132, 1.0), 0x24 bytes): GAIN change → linear ramp current → target over 132 samples
  (float32 inc (new − cur)/132, 0xe895c); otherwise multiply by current gain via 0x5792c8 (NEON ×4 with FTZ, VFP tail). Applied after the filter
  (gain-before-filter variant refuted: 7/2048 samples match).
- Start-up: only the filter gate, built closed, opening linearly over 132 samples on block 0 (cold rms gain 0.183, 0.491, 0.700, 0.714 on a
  1 kHz sine; 0.714 = steady LPF 997.8 Hz Q 0.7).

**F034 — MultiModeFilter parameter → coefficient formulas.** `confirmed` (118/118 readbacks exact at v ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9, 1};
critic re-read literals 9.8f, 0.2f, 45f, 0.05f, 64f, FLT_EPSILON @0x107f90–0x107fa4, 152.0/1000.0 @0x1087c8/0x1087d0, 44.1f @0x108760)
| idx | parameter | formula (float32 unless noted) | stored at |
|---|---|---|---|
| 0 | CUTOFF | fc = (float)pow(1000.0, v)·20 = 20 Hz…20 kHz | [+0x498]+0x18 (dirty +0x41) |
| 1 | GAIN | dB = v·45 − 30 (−30…+15 dB, 0 dB at v = 2/3); g = (float)10^(dB·0.05f); 132-sample linear ramp | [+0x49c]+4 target, +0 inc |
| 2 | Q | Q = 0.2f + v·9.8f (0.2…10), stored without LoFi's ≥ ε change test; 24 dB stages use √Q | [+0x498]+0x28; stage +0x40 |
| 3 | GLIDE | G = (1 + 8v)·64 = 64…576; flag = |G − 64| ≥ FLT_EPSILON; m = 10^(log10f(1000)/G), 1/m. Glide ≈ G/3 ms per decade (21.3 ms at 0, 107 at 0.5, 192 at 1) | [+0x498]+0x44, +0x42, +0x48, +0x4c |
| 4 | NONE | unused | — |
| 5 | MIXRATIO | wet = v, dry = 1 − v | EffectBase +0x14 / +0x10 |
| 6, 7 | FILTERTYPE, FILTERDB | kind per F033; pending := kind; gate fade when kind ≠ current | [+0x498]+0x10 → +0x14 at swap |
Readbacks: GAIN 0 → 0.0316228, 1 → 5.623413; GLIDE 0.5 → G 320, m 1.0218214; Q 1 → 10; 24 dB stage Q 7.06 → 2.657066.

**F035 — MultiModeFilter object layout (0x4a0 bytes).** `confirmed` (emulated dumps; writers from disassembly, critic checked)
- +0x1b8 + 0x5c·k: 8 LinearParameter objects (vt 0x840ac8), order as F032.
- +0x498 filter container (0x50, ctor 0x10913c): +0/+4/+8 stage vector (data, cap 8, count 7); +0xc SignalGate (vt 0x840e40, 132 samples);
  +0x10 pending / +0x14 current kind (ctor 0/0); +0x18/+0x1c cutoff target/current (ctor 1000); +0x20 cutoff multiplier; +0x24 cutoff steps;
  +0x28/+0x2c Q target/current (ctor 0.7); +0x30 Q multiplier; +0x34 Q steps; +0x38 samples to next step; +0x3c max steps; bytes +0x40
  recompute, +0x41 dirty, +0x42 glide on; +0x44 G (ctor 64); +0x48/+0x4c step multipliers (ctor 1000^(1/64) = 1.113974 / 0.897687).
  Same field order as the LoFi container 0xfc5e4 (F029) for +0x0..+0x41, plus +0x42..+0x4c.
- Stage (0xc, ctor 0x1080a0): +0 kind, +4 biquad 1, +8 biquad 2 or 0. Biquad = IirFilter 0x50 (F029).
- +0x49c GainRamp (0x24): +0 inc, +4 target, +8 current (ctor 1.0), +0xc samples left, +0x10 N = 132, +0x14 1/N, +0x18 delay, byte +0x1c
  idle/accept (ctor 1), +0x20 state (0 hold, 1 ramp, 2 delayed start). MMF always passes delay 0, force 1.
- Not understood: container +0x20 before the first setup (uninitialised; never read before being written, `likely`); GainRamp idle byte
  semantics when force = 0; slot 27 0x107fa8 (decompile only: re-applies params, clears the current kind's biquad taps) and slots 23/24
  (0x107b20/0x107b28) not emulated.

**F036 — A pure-Python MultiModeFilter model is bit-exact to the emulated 1.60 slot 25.** `confirmed`
- `tools/fx/mmf.py` (own code; imports only `math` and `lofi`; reuses `lofi.Param`, `SignalGate`, `Biquad`). 12 settings × 4 signals
  (impulses, 1 kHz sine, seeded noise) × 16 blocks × 64 stereo: 48/48 bit-exact, covering all 7 kinds, intermediate CUTOFF/Q/GAIN/GLIDE and
  mid-run changes. Critic added 17 bit-exact cases (8 random walks of 48 blocks changing all parameters, GAIN retarget every block, type/dB
  switch every block, GLIDE edges 0/1e-9/1e-7/1e-6, ±1e4 and denormal inputs, finite out-of-range values) and showed deliberate model errors are
  caught (GAIN span, FILTERDB 2 = 12 dB, FILTERTYPE 3 = LPF24; Q' = Q and gain-before-filter variants).
- Limits: block size n must not exceed the ctor block size (64 on the device; larger n diverges, rebuilt for 256 it is bit-exact for 1–256);
  negative Q untestable (emulator lacks `__errno_location`); slot 27 not modelled; host libm; device FPSCR FZ setting unknown (F020).

**F037 — Shared DSP blocks: MultiModeFilter vs LoFi.** `confirmed`
- MMF uses LinearParameter (vt 0x840ac8, 8 objects), SignalGate (vt 0x840e40, 1 filter gate) and IirLpf/Hpf/Bpf2ndOrder (vt 0x840c28 /
  0x840c48 / 0x841918; 3 + 6 objects) with the same layouts and formulas as LoFi. It does not use IirOff (0x841938).
- It does **not** reuse the LoFi filter container 0xfc5e4: it has its own class (ctor 0x10913c, process 0x108808, ramp setup 0x108608)
  implementing the same algorithm plus glide and two-stage cascades. It adds GainRamp (0xe8900 / 0xe895c / 0xe89f0) and vec_mulScalarTo
  0x5792c8. GainRamp is also called from 0x10afd4 and 0x10c208 (ParametricEqualizer range), 0x152e94/0x153284 and 0xe6xxx/0xe9xxx code:
  shared use beyond MMF is `likely`, owners not identified.

## ParametricEqualizer (2-band EQ) algorithm (Insert index 2; also Master index 4) — cycle 007 (H026)

Evidence for F038–F044: `kb/cycles/007.md` (Worker + Critic, all 7 criteria CONFIRMED). Harness `harness/H026_peq_model.py`, run
`python -B harness/H026_peq_model.py --out DIR` → `RESULT: 0 failed checks`; worker runs (r2/r3) and the critic run
<critic scratch run> byte-identical (`h026_report.txt` ed20422f…93e9, `h026.json` fa2ebab6…fbfd, concatenated sorted `*.f32`
a3cb6985…8f58). Models `tools/fx/peq.py` and `tools/fx/fdlibm_powf.py`. Emulation calls slot 25 0x10ae70 directly on an object
built by the real ctor 0x10baec(obj, 44100, 64) after `.init_array` entry 0x13aa8 and the H007 Insert init. Critic's 47 extra cases and 11
mutants (<critic scratch run>) were not kept in the repo.

**F038 — ParametricEqualizer parameters.** `confirmed` (ctor registration hooks 0xf1850/0xf1a00; name strings 0x842268…0x8422a4; slot-14 map)
| idx | name | object offset | kind | ctor "last" | Insert default (slot 52, index 2) |
|---|---|---|---|---|---|
| 0 | B1FREQUENCY | +0x1b8 | float 0..1 | 0.5 | 0.566 (997.77 Hz) |
| 1 | B1GAIN | +0x214 | float 0..1 | 0.5 | 2/3 (0 dB) |
| 2 | B1Q | +0x270 | float 0..1 | 0.5 | 6/99 (Q 0.7) |
| 3 | B2FREQUENCY | +0x2cc | float 0..1 | 0.5 | 0.566 |
| 4 | B2GAIN | +0x328 | float 0..1 | 0.5 | 2/3 |
| 5 | B2Q | +0x384 | float 0..1 | 0.5 | 6/99 |
| 6 | BAND1TYPE | +0x3e0 | choice 0..5 | 5 | 0 (low shelf) |
| 7 | BAND2TYPE | +0x43c | choice 0..5 | 5 | 1 (high shelf) |
- Slot-14 index 8 changes nothing and returns 3. **No mix parameter**: slot 26 0x10a4d8 stores dry 0.0 / wet 1.0 at EffectBase +0x10/+0x14
  and slot 25 calls it every block.
- Type 5 (the ctor "last" value and the registered maximum) and any negative integer type have **no stage**: the swap 0x10c098–0x10c0c8
  indexes the stage vector only if type <u count (5), else reads [0+0xc] → null read (emulator fault, pc 0x10c0c8). Device crash `likely`;
  whether the UI can send 5 is `guess`. On-screen type labels not checked (`guess`: low shelf / high shelf / peak / LPF / HPF).

**F039 — ParametricEqualizer signal flow.** `confirmed` (REA pseudocode + own disassembly + call trace + bit-exact emulation)
- Slot 25 0x10ae70: 0x10a4f0 apply changed params (order B1F, B1G, B1Q, B2F, B2G, B2Q, TYPE1, TYPE2) → band 1 `0x10c208([+0x498], L, R, n)`
  → band 2 `0x10c208([+0x49c], L, R, n)` → slot 26. Returns 0. **The bands are in series** (parallel variant refuted: 2/2048 samples).
- Each band (0x64 B, ctor 0x10afd4) holds 5 stages (0x10 B, ctor 0x10a928) and runs exactly one, selected by type:
  | type | filter | output gain after the filter |
  |---|---|---|
  | 0 | `LowShelvingFilter` (vt 0x83bcc0), +gain dB | 1.0 |
  | 1 | `LowShelvingFilter` with **−gain** dB | 10^(gain/20) → net **high shelf** (= Zölzer HF-shelf boost form, critic algebra) |
  | 2 | `PeakingFilter` (vt 0x83bcf0), +gain dB | 1.0 |
  | 3 | `IirLpf2ndOrder` (vt 0x840c28), 12 dB/oct | 10^(gain/20) |
  | 4 | `IirHpf2ndOrder` (vt 0x840c48), 12 dB/oct | 10^(gain/20) |
- Band process 0x10c208: 0x10abdc ramp setup → by gate state: fading out (old stage + GainRamp on the remaining fade samples, gate, swap
  0x10c070, new stage on the rest); **closed** (only after construction: swap, then the gate only — block **not filtered and no output gain**);
  open/fading in: chunk loop with one glide step per 44.1 samples, stage filter (vt slot 2) then the band GainRamp (0xe89f0, N = 44) per
  chunk. Then the band SignalGate (0xf521c, 132 samples) over the whole block.
- Start-up: both band gates are built closed, so block 0 = x·(n/132)² (two gates in series, as LoFi F031); rms gain 0.1084, 0.6116, 0.999,
  1.0 on a 1 kHz sine at cold defaults. The unfiltered first block happens once per object lifetime (slot 27 0x10a7ec does not touch the
  gates, static read): `likely`; whether the EffectInOutGain fade-in masks it on the device is untested.

**F040 — IirFilter2 family (peaking / shelving), new shared block.** `confirmed`
- IirFilter2 base (vt 0x83bc60, 0x90 B, ctor 0xe2df0): +4 fs (int), +8 fc (limits +0xc 1.0 / +0x10 Nyquist), +0x18 Q double (ctor 1/√2;
  limits +0x20 0.01 / +0x28 20), +0x38 p = V − 1 double (limits −1 / 100), +0x58 gain dB double (limits −80 / +40), byte +0x78 re-seed flag,
  +0x7c..+0x88 four tap pairs {x, y} per lane, +0x8c coefficients b0 b1 b2 a1 a2 (duplicated per L/R lane).
- Slot 6 0xe2ab4 configure(fc, Q, gain_dB, flag) (no Ghidra function): each value stored **only if within its limits** (out of range or NaN
  keeps the old value; clamping variant refuted by mutation), p = pow(10, gain/20) − 1, then slot 9 coefficients, then +0x78 = flag.
- Slot 2 0xe34d8 → slot 8 0xe27b8: DF-I, NEON with L/R lanes, y = b0·x + b1·x1 + b2·x2 − a1·y1 − a2·y2 in that order; no k·y_prev term;
  re-seed (re-filter the last 4 inputs with new coefficients) when +0x78 is set and Q > 0. 0xe2cf8 clears the taps.
- Coefficients (double, stored float32), K = (tan(fc·π/fs)·(1/2π))·2π, V = 10^(g/20), D = (K/Q + 1) + K²:
  - Low shelf 0xe2540 (ctor 0xe311c): b0 = ((√V·K/Q + 1) + V·K²)/D, b1 = (2K²·V − 2)/D, b2 = (V·K² + (1 − √V·K/Q))/D, a1 = (2K² − 2)/D,
    a2 = ((1 − K/Q) + K²)/D. DC gain V, Nyquist 1.
  - Peaking 0xe2440 (ctor 0xe30e4): b0 = ((V·K/Q + 1) + K²)/D, b1 = a1 = (2K² − 2)/D, b2 = ((1 − V·K/Q) + K²)/D, a2 = ((1 − K/Q) + K²)/D.
    Gain V at fc.
  - Both are Zölzer's **boost** forms with 1/Q in place of √2, used unchanged for cuts (RBJ cookbook refuted, max |coef diff| 0.012–0.152;
    Zölzer cut form refuted by mutation). Consequence (critic, from the formula): a cut is narrower than a boost of the same Q — half-gain
    bandwidth at 1 kHz ±12 dB: Q 0.7 3.30 vs 1.01 oct, Q 2 1.38 vs 0.36, Q 7 0.41 vs 0.10.

**F041 — ParametricEqualizer parameter formulas and glide.** `confirmed` (70/70 readbacks at v ∈ {0, 0.1, 0.3, 0.5, 0.7, 0.9, 1}; 10/10
settled coefficient sets; critic re-read literals)
| idx | parameter | formula (float32) | stored at (band = [+0x498] / [+0x49c]) |
|---|---|---|---|
| 0 / 3 | BxFREQUENCY | f = powf(1000f, v)·20f (libm powf, F044), 20 Hz…20 kHz | band+0x1c target |
| 1 / 4 | BxGAIN | dB = v·45 − 30 (−30…+15, 0 dB at 2/3) | band+0x44 target |
| 2 / 5 | BxQ | Q = 0.1f + v·9.9f (0.1…10, 0.7 at 6/99; literals 0x10a7e0/0x10a7e4) | band+0x30 target |
| 6 / 7 | BANDxTYPE | t = (int)v; gate fade + swap if t ≠ current | band+0x14 pending → +0x18 current |
- LPF/HPF stages: the F028 bilinear formulas, fc clamped to [5 Hz (0x83bc40), Nyquist]. Output gain (types 1/3/4) = (float)pow(10, g·0.05f).
- Glide, one step per 44.1 samples (0x10abdc / 0x10c208): frequency ×powf(10, 0.012f) = 1000^(1/250) or inverse; Q ×powf(10, 0.02f) or
  inverse (globals 0xf52f00/04/08/0c from static init 0x13aa8); gain ±0.04 dB (0x10add0/4). Step counts = **trunc**(|log10f(t/c)/log10f(m)|) + 1,
  gain trunc(|Δ dB|·25) + 1 (rounding variant refuted). Gated jump (gate out, all targets set, gate in) when freq steps > 38, Q steps > 70 or
  gain steps > 250 (doubles 0x10adb8/c0/c8, `bgt`). Each glide step re-targets the band GainRamp (44-sample linear); at a swap types 1/3/4 set
  the output gain at once (GainRamp_setNow 0xe9358), types 0/2 ramp to 1.0.

**F042 — ParametricEqualizer object layout (0x4a0 B).** `confirmed` (emulated dumps, 38 band fields equal the model; offsets spot-checked by critic)
- +0x1b8 + 0x5c·k: 8 LinearParameter (order F038). +0x498 / +0x49c → band 1 / band 2.
- Band (0x64): +0/+4/+8 stage vector (data, cap 8, count 5); +0xc → SignalGate (132, built closed); +0x10 → GainRamp (0x24, N 44, F035 layout);
  +0x14/+0x18 pending/current type (ctor 0/0); +0x1c/+0x20/+0x24/+0x2c freq target/current (ctor 1000)/multiplier/steps; +0x30/+0x34/+0x38/+0x40
  Q target/current (ctor 0.7)/multiplier/steps; +0x44/+0x48/+0x4c/+0x54 gain dB target/current (ctor 0)/step ±0.04/steps; +0x58 samples to next
  step; +0x5c max steps; bytes +0x60 recompute, +0x61 step now (set only when the counters were 0; overwrite variant refuted), +0x62 dirty.
  +0x28/+0x3c/+0x50: no access found (`likely` padding).
- Stage (0x10): +0 IirFilter (types 3/4), +4 IirFilter2 (types 0–2), +8 the band's GainRamp, +0xc type.
- Not done: slot 27 0x10a7ec (static only: re-applies params, clears the current stage's taps in each band); slots 23/24 (0x10a4c8/0x10a4d0)
  return 4 (meaning unknown).

**F043 — A pure-Python ParametricEqualizer model is bit-exact to the emulated 1.60 slot 25.** `confirmed`
- `tools/fx/peq.py` (own code, no firmware bytes; reuses `lofi.Param/SignalGate/Biquad`, `mmf.GainRamp`, and `fdlibm_powf`). Worker:
  12 settings × 4 signals × 16 blocks × 64 stereo, 48/48 bit-exact, every type in both bands, mid-run changes of every parameter. Critic: 47 more
  bit-exact cases (random walks, changes every block, odd type values, type switch every block, ±1e4 and denormal inputs, out-of-range values,
  n = 1…63) and 11 mutants all caught (2 only by targeted tests).
- Limits: host double `tan`/`pow` (see F044); n ≤ ctor block size; type 5 not modelled (raises); slot 27 not modelled; device FPSCR (F020).

**F044 — The 1.60 libm `powf`/`log10f` are fdlibm (glibc 2.13), not correctly rounded; host double `tan`/`pow` differ slightly.** `confirmed`
- Emulated real 1.60 libm `powf` (PLT 0xff40) = own `tools/fx/fdlibm_powf.py` in 4503/4503 (worker) and 16000/16000 (critic) cases; correctly
  rounded in only 13718/16000 (max 6 ulp). `log10f` (PLT 0x10ab0): 3002/3002 and 9000/9000; correctly rounded 7838/9000 (max 2 ulp).
  glibc version: `strings decoded/lib/libc.so.6` → "GNU C Library stable release version 2.13". A host-powf PEQ variant matches 284/2048 samples.
- Double routines (critic): the device `tan` differs from the macOS host `tan` by 1 ulp in 1958/6000 PEQ arguments (glibc is the correctly
  rounded one); `pow(10, x)` differs in 27/20000. 0/6000 random (fc, Q, gain) sets gave a different float32 coefficient. So lofi.py, mmf.py and
  peq.py carry a small (`likely` < 1e-4 per coefficient set) residual risk from host double libm; LoFi/MMF also use host `log10f` for step counts.
- `fdlibm_powf.py` is a transliteration of the public fdlibm source (`e_powf.c`/`e_logf.c`/`e_log10f.c`, Sun licence asks its notice be kept):
  credit and notice required before any publication. [Editor's note: kept in tools/fx/ and listed in NOTICE.md.]

## Phaser (Insert index 8 / Master index 9) — cycle 008 (H028)

Evidence for F045–F051: kb/cycles/008.md (Worker + Critic), `harness/H028_phaser_model.py` (run `python -B
harness/H028_phaser_model.py --out DIR` → `RESULT: 0 failed checks`; `h028_report.txt` sha256 1810c080…9d227e, sorted concatenated `*.f32`
cf14c39c…5bd7, reproduced byte-identically by the critic), `tools/fx/phaser.py`, `tools/fx/fdlibm_tanf.py`. All addresses 1.60.

**F045 — Phaser parameters, defaults and tempo feed.** `confirmed`
- Registered by ctor 0x10d654 (obj, fs, block): id 0 Rate +0x220, 1 Width +0x27c, 2 Phase +0x2d8, 3 Frequency +0x334, 4 Feedback +0x390,
  5 Mixratio +0x3ec (LinearParameter, 0…1, ctor defaults 0.5 / 1 / 0 / 0 / 0.5 / 1), 6 Sync +0x448 (ToggleParameter vt 0x840b20, off),
  7 Bpm +0x470 (LinearParameter 1…999, default 120). Slot-14 index = id; index 8 → ret 3. Names at 0x842350…0x842374 (Rate, Width, Phase,
  Frequency, Bpm), 0x841d84 Feedback, 0x8417a4 Mixratio, 0x88b42c Sync.
- ToggleParameter setter 0xf0738: v ≥ 1 on, v ≤ 0 off, 0 < v < 1 unchanged + ret 3; consumeChange 0xf0858 compares bytes +0x24/+0x25.
- Insert defaults (InsertFxProcessor slot 52 case 8): Rate 199/999 (2.00 Hz), Width 1, Phase 0, Frequency 1 (18 kHz), Feedback 0,
  **Mixratio 0** (so fully dry at the processor's own defaults; a UI/project override is `guess`), Sync 0.
- Tempo: InsertFxProcessor processBlock case 0x116b28 (shared by indices 1 and 8) clamps [proc+0x94]→vt+0x1c() to 1…999 and calls slot 14
  (e, 7, BPM) every block before slot 18 — Bpm receives the BPM value, not a normalised value. With Sync on, Rate selects a beat division.

**F046 — Phaser signal flow (slot 25 0x10d630 → 0x10d260, kernel 0x10cf40).** `confirmed` (code read by worker and critic; bit-exact emulation)
- Per block: retrigger flag +0x4ec (slot 10 0x10cb38) → oscillator resetPhase(0.25) (restart at peak); if Rate || Bpm || Sync changed
  (short-circuit, so later flags survive to the next block) → period update 0x10df00 and coefficient ramp +0x1d8 := 3·block (192);
  Phase changed → setPhaseOffset(Phase·0.5), ramp restart; oscillator 0x101bdc fills n control values per channel (L, R); Frequency || Width
  changed → new corners, ramp restart; coefficient target per channel from the **last** oscillator sample u ∈ [0,1]:
  w = lo + (hi − lo)·u³, a_t = (w − 1)/(w + 1); a moves **linearly per sample** to a_t (over the ramp count if > 0, else over n).
  Feedback target 0.99·Feedback with its own 192-sample linear ramp (+0x1dc). Then slot 26 0x10cb48 (wet = Mixratio, dry = 1 − Mixratio)
  every block; returns 0.
- Kernel 0x10cf40 (NEON, L/R lanes, flush-to-zero), per sample: s = (1−p)·y + p·s (one-pole LPF of the previous output, p = exp(−2π·10000/fs));
  x = in + fb·s; **6 identical first-order all-passes** in series (v = x − a·z; x = a·v + z; z = v; one coefficient per channel);
  g = 0.7 − ((a − a_lo)/(a_hi − a_lo))·0.2 (level compensation 0.7 at the 100 Hz end … 0.5 at the 20 kHz end); out = (in + x)·g; y = out.
- Stereo: separate a/z/s/y per channel; one oscillator, R phase offset = Phase·180°; feedback amount shared. No SignalGate, GainRamp or
  filter blocks; no start-up gate (block 0 fully processed; ramps start from ctor a = a_hi, fb = 0.495).
- Reset slot 27 0x10cf30 → 0x10cb78: ramp counters −1, oscillator re-init with the current period, resetPhase(0.25), phase offset, corners,
  fb := target, all filter states 0, oscillator run for 1 sample to seed a; parameter change flags are not consumed.
- Alternatives refuted by emulation (critic re-ran): 4 stages, feedback from the last all-pass, linear (not cubic) curve, sine LFO, L/R offset 0,
  per-block stepped coefficient. Frozen-coefficient notches 625/2326/7832 Hz match 6-stage theory 628/2324/7826 Hz.

**F047 — Phaser uses a shared vtable-less oscillator, not the RTTI `LFO` class.** `confirmed` (callers); other waveforms `likely`
- Oscillator object (0x98 B, [+0x21c]; no vptr, word 0 = amplitude): ctor 0x100af0 → init 0x100710, process 0x101bdc, setFrequency 0x101090
  (period P = **44100**/f − 1 with a literal 44100, not fs; counter rescaled; f ≤ 0.00441 → P = 9999998), setPeriodMs 0x101320 (f = 1000/ms),
  setPhaseOffset 0x1017d4, resetPhase 0x101440, setSmoothingHz 0x1019f0, setOffset 0x1019e4, setAmplitude 0x1019d8, setSmoothingOff 0x102cb0,
  resync 0x101b30.
- Callers of 0x100af0: c_distortion 0xfa568, c_chorus 0xff008, c_flanger 0x100234, Phaser 0x10d654, 0x135da0. Callers of 0x101bdc: c_chorus
  slot 19 0xfe710, c_flanger 0xff9ac, Phaser 0x10cb78 / 0x10d260 (REA; critic re-listed).
- Phaser config: waveform 1 = triangle (slope k = 4f/fs, counter c wraps at P; x = c·k − 1 if c ≤ P/2 else 3 − c·k), amplitude 0.5, offset 0.5
  (output 0…1), smoothing off. Waveforms 0 (sine, recursive sincos), 2 (saw), 3–5 (pulse-like), 6 (random table 0xb70e50): decompile only, `likely`.
- Phaser uses LinearParameter 0x840ac8 ×7 and ToggleParameter 0x840b20; no SignalGate/IirFilter/IirFilter2/GainRamp (H024).

**F048 — Phaser parameter formulas.** `confirmed` (70/70 slot-14 readbacks, 48/48 synced periods at 4 tempi, critic walks)
| id | parameter | formula (float32; rint = round half even) | stored at |
|---|---|---|---|
| 0 | Rate, Sync off | Hz = rint(1 + 999v)·0.01 (0.01…10 Hz); ms = 1000/Hz | +0x4cc; osc +0x10, +0x84 |
| 0 | Rate, Sync on | i = rint(11v); ms = (60000/Bpm)·(64, 32, 16, 8, 4, 2, 1, 3/4, 1/2, 1/4, 1/8, 1/16)[i] beats (table 0xf61fcc; i > 11 asserts) | +0x4cc |
| 1 | Width | lo_f = f − (1 − (1 − w)²)·(f − 100); lo = max(tanf(π·lo_f/fs), tanf(π·100/fs)) | +0x4d0; +0x208 |
| 2 | Phase | R offset = Phase/2 cycle (0…180°) | +0x4d4; osc +0x50 |
| 3 | Frequency | f = powf(60, rint(256v)/256)·300 (300 Hz…18 kHz, 257 steps); hi = min(tanf(π·f/fs), tanf(π·20000/fs)) | +0x4d8; +0x20c |
| 4 | Feedback | fb = 0.99·v, 192-sample linear ramp | +0x4dc target, +0x1e0 |
| 5 | Mixratio | wet = v, dry = 1 − v (EffectBase) | +0x14/+0x10; +0x4e0 |
| 7 | Bpm | tempo 1…999, used only with Sync on (but any change restarts the ramp) | +0x470; +0x4e8 |
- Frequency = upper sweep corner, Width = depth down to 100 Hz (Width 0 = no sweep). Rate tables 0x34c220/0x34c240, sync 0x34c28c/0x34c2a8,
  frequency 0x34c8a8/0x34c8c8. The sync table is filled by `.init_array` entry 0x6cb20 (store block 0x6cbe0–0x6ce8c, constants only).
- 1.60 libm `tanf` (PLT 0x104c8) = fdlibm `tanf` (`tools/fx/fdlibm_tanf.py`) in 5221/5221 harness + 10055 scratch cases; host tan agrees
  in 5020/5221; it matters at Frequency indices 204, 212, 248. `fdlibm_tanf.py` transliterates public fdlibm source: Sun notice kept,
  credit required before any publication (as F044). [Editor's note: done, see NOTICE.md.]

**F049 — Phaser object layout (0x4f0 B).** `confirmed` (model = emulated state in all worker and critic runs)
- +0x1b8 fs; +0x1bc ramp length 3·block; +0x1c0/+0x1c4 t_lo = tan(π·100/fs) / t_hi = tan(π·20000/fs); +0x1c8/+0x1cc a_lo/a_hi; +0x1d0/+0x1d4
  gains 0.5/0.7; +0x1d8/+0x1dc coefficient/feedback ramp counters (−1 idle); +0x1e0 feedback current; +0x1e4/+0x1e8 previous output y L/R;
  +0x1ec/+0x1f0 coefficient a L/R; [+0x1f4] → 6×(L,R) all-pass states (0x30 B); +0x1f8/+0x1fc LPF p / 1−p; +0x200/+0x204 LPF state L/R;
  +0x208/+0x20c current lo/hi corners; +0x210 copy of t_lo (`likely` unused); +0x214/+0x218 → oscillator buffers float[block]; +0x21c →
  oscillator; +0x220 + 0x5c·k (k 0..5), +0x448, +0x470 parameters; +0x4cc…+0x4e0 period ms / Width / Phase / Frequency / fb target /
  Mixratio copies; +0x4e4 Sync copy (byte), +0x4e8 Bpm copy, +0x4ec retrigger flag (byte).
- Vtable 0x8422b8 overrides: 0/1 dtors 0x10e074/0x10e1a4, 10 retrigger 0x10cb38, 23/24 0x10def0/0x10def8 (return 0), 25 0x10d630,
  26 0x10cb48, 27 0x10cf30.

**F050 — A pure-Python Phaser model is bit-exact to the emulated 1.60 slot 25.** `confirmed`
- `tools/fx/phaser.py` (own code, no firmware bytes; reuses `lofi.py`, `fdlibm_powf.py`, new `fdlibm_tanf.py`). Worker: 12 settings ×
  4 signals, 64 blocks × 64 stereo (one 160 blocks), 48/48 bit-exact incl. all 12 sync divisions, 4 tempi, mid-run changes, retrigger/reset.
  Critic: 297/297 random walks (~2.1 M samples; n 1…64, tempo changes, retrigger/reset, near-denormal input), ctor (44100,32/128) and
  (48000/96000, 64) all bit-exact (supports the literal-44100 period quirk); heap-fill and FPSCR FZ probes insensitive; 4 mutants caught.
- Limits: out-of-range v or BPM sent straight to slot 14 can reach a firmware assert (not emulated) or the model's tanf range limit
  (|x| ≥ 3π/4); n ≤ ctor block; non-triangle waveforms not modelled; Master context (index 9) not exercised. Docstring calls the
  oscillator "LFO" — reword before publication (it is not the RTTI `LFO` class). [Editor's note: docstrings reworded in tools/fx/phaser.py; the Python class name is unchanged.]

## Shared oscillator (all waveforms) and its role in Chorus / Flanger / Distortion — cycle 009 (H031)

Evidence for F051–F056: kb/cycles/009.md (Worker + Critic), `harness/H031_osc_model.py` (run `python -B
harness/H031_osc_model.py --out DIR` → `RESULT: 0 failed checks`, 17 PASS; `h031_report.txt` sha256 3fcde046…d6ac, sorted concatenated
`*.f32` 2be562d2…406f, reproduced byte-identically by the critic), `tools/fx/osc.py`, `tools/fx/fdlibm_sincosf.py`,
`tools/fx/crmath.py`; critic probes (68 extra oscillator cases, 4,006 smoothing settings, 28 garbage-fill runs, Chorus/Flanger at
non-default settings) in `<critic scratch run>` (scratch, not kept). H028 harness still passes with cycle-008 hashes. All addresses 1.60.

**F051 — Oscillator object layout and API (0x98 B, no vptr).** `confirmed` (every field model = emulation after every call)
- +0x00/+0x04 amplitude (init 1) / offset (init 0), out = off + amp·x; +0x08 id (from global counter 0xb70e4c, `.data` initial 1,
  post-incremented by ctor 0x100af0); +0x0c waveform 0..6 (−1 = invalid); +0x10 frequency Hz (floor 0.0044100005); +0x18 f64 1/fs;
  +0x20 f64 step (sine 2πf/fs, tri 4f/fs, saw −2f/fs, pulse/random f/fs); +0x28/+0x30/+0x38 f64 sine cos w / 2cos w / sin w (pulse: +0x28
  duty); +0x40/+0x48 f64 sine y[n]/y[n−1] (other waves: +0x40 phase position for hold mode; random: +0x48 held L); +0x50/+0x54 R phase offset
  (and sine sin 2πφ / random held R); +0x58/+0x5c smoother a = 1 − b, b = expf(−2π·hz/fs) (init **50 Hz**); +0x60/+0x64 smoother state L/R;
  +0x68/+0x6c resync counter / period (= fs); +0x70 f64 hold flag; +0x78 f64 smoother-off flag; +0x80/+0x84 counter c / period P;
  +0x88 random offset (setRandomOffset 0x102c50) / +0x8c random index 0…0x2000; +0x90 → random table 0xb70e50; +0x14/+0x94 padding.
- Entry points (emulated and modelled): ctor 0x100af0 (calls init 0x100710 **first**, then stores +0x90 table and +0x08 id), initPeriodMs
  0x100b28, setFrequency 0x101090, setPeriodMs 0x101320 (f = 1000/ms; 0 → returns 0), setPhaseOffset 0x1017d4, resetPhase 0x101440,
  setAmplitude 0x1019d8, setOffset 0x1019e4, setSmoothingHz 0x1019f0, setSmoothingOff 0x102cb0, setRandomOffset 0x102c50, resync 0x101b30,
  process 0x101bdc(osc, bufL, bufR, n); setWaveform 0x100b5c same-value = no-op (`confirmed`).
- `likely` (disassembly/decompile only, not emulated): setWaveform with a new value (converts the phase position), processMono 0x1025d4
  (LfoProcessor only), initMsPhaseAmp 0x1015c8, getters 0x100b54/0x1012f8/0x101620/0x1016dc, 0x1018cc, smoothMono/Stereo 0x101a70/0x101ab8,
  0x101b24, 0x102c10/0x102c2c/0x102c3c, 0x102c58/0x102c8c/0x102c94.
- Quirks (`confirmed` in emulation): init computes the resync phase +0x68 = id·448 mod fs from the id word **before** the ctor writes it
  (uninitialised heap; only shifts when the first sine renormalisation happens). init case 6 dereferences +0x90 before the ctor stores it
  (emulator: NULL read at 0x1008ec; on the device the read is of uninitialised memory, undefined — so waveform 6 is only reachable by
  re-initialising an existing object, as LfoProcessor does). init does **not** write the counter +0x80 for the sine; if that heap word is a
  huge positive float or +inf, the wrap loop in Osc_process never ends (emulated hang with fill 0x7F7F7F7F). Chorus clears it on its first
  block (resetPhase), Flanger and LfoProcessor do not; on the device fresh heap is probably zero (`guess`).
- Random table 0xb70e50: 8192 float32 in initialised `.data` (uniform in [−1, 1)), only referenced by the ctor (0x100b08); a static table,
  not a runtime PRNG (`confirmed`: patching the table changes the emulated output accordingly; glibc rand() matches 0/1000).

**F052 — Oscillator waveforms and timing.** `confirmed` (bit-exact model; two unreachable branches `likely`)
- Per sample: c += 1; if c ≥ P, c −= P (float32); x = wave(c); per block after the loop: resync check; then out = off + amp·x and, unless
  smoothing is off, y = a·out + b·y per channel. Output is per sample. **P = fs/f − 1** (init uses fs; setFrequency the literal 44100, F047),
  so the true period is P samples; P ≥ 1. R = same formula at c + φ·P (wrapped), i.e. R leads by φ cycles.
- 0 sine: double-precision recursion y = 2cos w·y1 − y2, L = (float)(sin w·y) clamped ±1, R = cos 2πφ·L − (float)(y1 − y·cos w)·sin 2πφ;
  from init L[i] = sin((i+2)w); about once per second (+0x68 passes fs) the amplitude is renormalised (v = clamp(y1·sin w), y1 = v/sin w,
  y2 = cos(±acos v − w)/sin w). Without the resync a model diverges right after the first renormalisation (sample 44,539).
- 1 triangle: k = 4f/fs, x = c·k − 1 for c ≤ P/2 else 3 − c·k; init c = P/4. 2 saw: k = −2f/fs, x = 1 + c·k (falling 1 → ≈ −1); init c = 0.
  3/4/5 pulse: duty d = 1/2, 1/4, 1/8, x = +1 if c ≤ d·P else −1. 6 random: sample-and-hold of table[(idx + off) mod 0x2000], one new value
  per period; the leading channel (R if φ < 0.5, else L) draws, the lagging one takes the leader's previous value at its own wrap. Index runs
  0…0x2000, so offset 0x2000 reads the word after the table (a denormal).
- Waveform out of range (7, −1, 100): init returns 0, +0x0c = −1, process returns 0 and leaves buffers untouched. init with f = 0 or fs ≤ 0
  returns 0.
- setFrequency keeps the phase fraction (c := c·P_new/P_old; sine y1/y2 recomputed phase-continuously); f = 0 → hold mode (output frozen
  at the current phase position; only init clears it; the saw in hold shows the sign-inverse value). resetPhase(φ) jumps: triangle
  c = (φ + ¼)·P (0.25 = peak), saw/pulse/random c = φ·P, sine restarts as cos(2πφ + n·w). setPhaseOffset(φ) wraps φ into [0, 1) and moves R only.
- 1.60 libm: double sin/cos/acos are correctly rounded (glibc dbl-64; `tools/fx/crmath.py` 1600/1600, 1600/1600, 1000/1000); sinf/cosf
  are fdlibm (`tools/fx/fdlibm_sincosf.py` 1500/1500 each; host math differs). glibc expf is not always correctly rounded (1/1504
  random arguments differ by 1 ulp), but the real setSmoothingHz path matched the model in 4,006 settings (critic).
- `likely`: negative-step branches of triangle/pulse and the positive-step branch of saw (unreachable: f is floored positive).

**F053 — A pure-Python oscillator model is bit-exact to the emulated 1.60 code.** `confirmed`
- `tools/fx/osc.py` (own code; the random table is passed in, read from `target/` at run time, never copied). Worker: 56 runs, 3,650
  process calls, 423,204 samples, all waveforms, slow/fast/non-integer periods, phase, amplitude/offset, smoothing on/off/changed, variable n,
  every setter mid-run, hold, resync, invalid waveforms — outputs, return codes and all fields equal after every call, max error 0. Critic:
  68 more cases (fs 48000 re-init, Nyquist, f > fs, negative/floored f, n 0…4096, random setter storms) and 27 garbage-fill runs, all exact.
  Mutants (period fs/f, pulse R = L, smoother swap, random wrap) caught.
- Limits: setWaveform (new value) and processMono not modelled; `fdlibm_sincosf.py` transliterates public fdlibm: Sun notice kept, credit
  required before any publication (as F044/F048). [Editor's note: done, see NOTICE.md.] `phaser.py` keeps its own triangle-only oscillator (unchanged; H028 still bit-exact).

**F054 — Who uses the oscillator, and how it is configured.** `confirmed` (emulated call logs + REA decompile); LfoProcessor control `likely`
- c_chorus ctor 0xff008 (kernel new 0x100): Osc_ctor(+0x28, 0 sine, 1 Hz, 44100), setWaveform(0), setFrequency(0.1), amp = 0.0005·fs
  (22.05), offset = amp + 0.2, setPhaseOffset(0), smoother on at 50 Hz. Later: Chorus slot 25 0x115d70 → kernel slot 3 0xfeb10 (rate,
  clamp 0.00104…64 Hz) → setFrequency; slot 14 0x116224: index 1 → kernel slot 5 0xfed90 (depth), 3 → slot 7 0xfeecc (depth scale), both
  amp = depth·scale·0.01·0.0005·fs, offset = amp + 0.2; 2 → slot 6 0xfec34 → setPhaseOffset; kernel slot 19 0xfe710: reset flag +0xe2 (set
  by ctor) / retrigger +0xe0 → resetPhase(0).
- c_flanger ctor 0x100234 (kernel new 0x118): same but amp = 0.001·fs (44.1), offset 44.3, no setPhaseOffset. Flanger slot 25 0x115f58 →
  kernel slot 3 0xffdc4 → setFrequency; slots 5/7 0xfffd4/0x100104 amp/offset; slot 6 0xffe68 phase; slot 19 0xff9ac retrigger +0xf0 → resetPhase(0).
- c_distortion ctor 0xfa568 (kernel new 0x138): Osc_ctor(+0x28, 0, 1 Hz, 44100) and nothing else — the oscillator is **never run** (no
  oscillator call in any c_distortion vtable target; 0 Osc_process calls in emulation).
- Phaser: F047. LfoProcessor (RTTI `12LfoProcessor`, vt 0x8451ec, ctor 0x135da0): Osc_ctor(new 0x98, 0, 1 Hz, 44100), setSmoothingOff(1);
  not an FX class. `likely` (decompile): re-inits with any waveform 0–6 via 0x134fc4/0x1015c8 and updates via 0x134e14; uses processMono.
- Insert defaults (slot 52): Chorus and Flanger Mixratio (slot-14 index 5) = 0, as Phaser (F045); a UI/project override is `guess`.
  `likely` (4 read-backs, not swept): Chorus depth scale v → 1 + 9v, Flanger v → 0.1 + 7v; phase v → index·0.45/19 cycles.

**F055 — Chorus and Flanger are oscillator-modulated delay lines.** `confirmed` (kernel re-statements bit-exact against emulation)
- Chorus (c_chorus slot 19 0xfe710): the oscillator L/R output is the **delay time in samples** of one tap per channel into a ring buffer
  of fs/10 + block = 4474 samples; write then read at idx − d with **linear interpolation**; wet only (no feedback, no dry path; dry/wet is
  EffectBase). Delay = offset + amp·(smoothed sine) = 0.2 … 2·amp + 0.2 samples. Start-up: output gain +0xe8 stays 0 until the ring has
  wrapped once, then rises linearly over ≈ 3.3 ms (step (1 − g)/(0.0033·fs)); blocks 0–68 at 64 samples are exactly 0.
- Flanger (c_flanger slot 19 0xff9ac): same delay-time role, ring 7·fs/1000 + block = 372 samples, out = (1 − fr)·buf[r] + fr·buf[r − 1];
  **feedback**: line input = in + y_prev·fb (+0x10c), y_prev = the previous **pre-gain** output of that channel (+0xf4/+0xf8); then output
  × g(d) = d·0.013154167 + 1 − 0.6314 for d ≤ 48 samples, else 1.
- Evidence: Python re-statements fed with the emulated oscillator buffers are bit-exact: worker 15,360/15,360 samples each (Insert
  defaults), critic 17,920/17,920 each at non-default settings (Flanger feedback 0.79/0.94, delays 1.1…281 samples, Chorus delays
  0.17…437, L ≠ R, mid-run changes). Refuted: oscillator as amplitude modulator, constant delay, feedback taken after the gain.
- Not yet reconstructed: full parameter formulas (rate table 0x349778/0x349798, Sync, depth/scale/phase mappings, Flanger feedback
  mapping) and an end-to-end slot-25 model → H033/H034.

**F056 — Chorus, Flanger and Distortion are built inline in the InsertFxProcessor ctor 0x118b0c and can be emulated.** `confirmed`
- Chorus 0x118b50–0x118c64: new(0x2b0); EffectBase ctor 0x1067d8(obj, 44100, 64, 0); vptr 0x842920; LinearParameter 0xf1850 "RATE" id 0
  at +0x1bc (default 0.5); ToggleParameter 0xf1800 "SYNC" id 6 at +0x218; "BPM" id 7 at +0x240 (1…999, 120); +0x29c = 1.0, +0x2a0 = 0.5,
  +0x2a8 = 120.0; kernel new(0x100) → c_chorus ctor 0xff008(kernel, 64, 44100) → +0x1b8. Flanger 0x118cd8–0x118ddc: same with vptr
  0x8429a8, +0x29c = 0, kernel new(0x118) → 0x100234. Distortion 0x119060–0x1190ec: new(0x1d8), 0x1067d8, vptr 0x842898, kernel new(0x138)
  → 0xfa568, three 8-byte stores at +0x1bc/+0x1c4/+0x1cc, no parameter registrations in this block.
- `harness/H031_osc_model.py` runs exactly these instruction ranges in unicorn, then the H007 Insert init and tempo feed, and calls slot 25
  directly: Chorus 120 blocks, Flanger 120, Distortion 16, non-trivial and identical across two runs (critic re-ran 140-block runs).
- Distortion process 0xfa78c (`likely`, decompile only): one-pole HPF, one-pole LPF, auto-gain envelope (+0x110, 1…100), drive (+0x104),
  clip ±1 plus cubic soft clip 1.5x − 0.5x³ blended by (1 − |y|)³·(+0x134), ×0.7, output one-pole LPF → H035.
