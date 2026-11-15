# Effects findings ledger (firmware 1.60) — scrubbed research notes

> **Editor's note.** This is the effects research ledger as it stood at the pinned research commits (cycles 001–009 in the first
> merge; cycles 010–042, findings F057–F213, added in the second merge),
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
  semantics when force = 0; slot 27 0x107fa8 (decompile only: re-applies params, clears the current kind's biquad taps; **corrected by F150:** applies pending changes only) and slots 23/24
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
- Not done: slot 27 0x10a7ec (static only: re-applies params, clears the current stage's taps in each band; **corrected by F150:** applies pending changes only; now modelled); slots 23/24 (0x10a4c8/0x10a4d0)
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
  **Corrected for Chorus by F058 (cycle 010):** depth scale = 0.1·rint(10 + 90v), phase = rint(180v)/380 cycles; Flanger mappings still `likely`.

**F055 — Chorus and Flanger are oscillator-modulated delay lines.** `confirmed` (kernel re-statements bit-exact against emulation)
- Chorus (c_chorus slot 19 0xfe710): the oscillator L/R output is the **delay time in samples** of one tap per channel into a ring buffer
  of fs/10 + block = 4474 samples; write then read at idx − d with **linear interpolation**; wet only (no feedback, no dry path; dry/wet is
  EffectBase). Delay = offset + amp·(smoothed sine) = 0.2 … 2·amp + 0.2 samples. Start-up: output gain +0xe8 stays 0 until the ring has
  wrapped once, then rises linearly over ≈ 3.3 ms (step (1 − g)/(0.0033·fs)); blocks 0–68 at 64 samples are exactly 0.
  **Corrected by F060 (cycle 010):** the rise is a per-block 44 % approach with snap (full gain at block 76), not one linear ramp.
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

## Chorus end-to-end (Insert index 0; also Master/Send index 2) — cycle 010 (H033)

Evidence for F057–F062: kb/cycles/010.md (Worker + Critic), `harness/H033_chorus_model.py` (run `python -B
harness/H033_chorus_model.py --out DIR` → `RESULT: 0 failed checks`, 12 PASS; `h033_report.txt` sha256 09032fa8…6052, `h033.json`
a04fce64…c286, sorted concatenated `*.f32` (38 files) ef54794e…ce3d; `--mutants` 7/7 caught, `h033_mutants.txt` bc99eae1…e446; all reproduced
byte-identically by the critic), `tools/fx/chorus.py` (reuses `osc.py`). Critic probes (1,079 extra read-backs, 12 extra end-to-end runs,
slot-18 dry/wet checks, aligned Insert/Master/Send diff) in `<critic scratch run>` (scratch, not kept). H021/H023/H026/H028/H031 harnesses
still pass with their recorded hashes. All addresses 1.60.

**F057 — Chorus parameters and when they apply.** `confirmed`
- Slot 14 0x116224 (always returns 0): 0 RATE (LinearParameter id 0, +0x1bc, 0…1), 6 SYNC (ToggleParameter id 6, +0x218), 7 BPM (LinearParameter
  id 7, +0x240, 1…999, 120): stored, applied at the **next slot 25** with F026 change detection (equal to the stored copy +0x2a0/+0x2a4/+0x2a8 →
  not applied; any change sets dirty +0x2ac and re-runs the rate computation once). 1 DEPTH, 2 PHASE, 3 DEPTH SCALE: no Parameter object,
  applied **immediately** via kernel slots 5 0xfed90 / 6 0xfec34 / 7 0xfeecc. 5 MIXRATIO: plain float +0x29c (ctor 1.0, no clamp). 4 and ≥ 8:
  ignored (no case).
- Insert defaults (slot 52 0x118a9c case 0, emulated bits): Rate 19/99 (→ 2.0 Hz), Depth 1.0, Phase 0, Depth scale 0, Mixratio 0, Sync 0; BPM is
  fed every block by processBlock (F017). Before the first block RATE 0.5 equals the ctor copy, so the kernel keeps its ctor rate 0.1 Hz.
- Slot 26 0x115a38 (end of every slot 25): EffectBase wet +0x14 = Mixratio, **dry +0x10 = 1.0 always**.
- `likely` (capstone, not emulated): slot 15 0x116140 getParameter (RATE/SYNC/BPM from their objects; 1/2/3 via kernel getters 11/12/13; 4 → 0;
  5 → +0x29c).

**F058 — Chorus parameter formulas.** `confirmed` (157 worker + 1,079 critic read-backs, 0 mismatches)
- Shared quantiser ("BasicParamSpec", assert string at 0x349800): i = rint(F(lo + F(v·(hi − 1 − lo)))) (`vmla.f32`, not fused; rint via
  +1.5·2^52 in double, round half even). {lo, hi} come from small code helpers: 0x349778 {1,101}, 0x3497e0 {0,10}, 0x349cac {0,101},
  0x349cf8 {0,181}, 0x349d48 {10,101}. 0x349778/0x349798 are **code, not tables** (correcting the cycle-009 label).
- Rate, Sync off: Hz = 0.1f·rint(1 + 99v) → 0.1…10 Hz in 0.1 Hz steps (0x349798 = i·0.1f). Sync on: i = rint(9v), (a, b) from the halfword table
  0xf61f50 = (16,1),(8,1),(4,1),(2,1),(1,1),(3,4),(1,2),(1,4),(1,8),(1,16); Hz = F(F(F(b·BPM)/a)·F(1/60)), i.e. one cycle per 16, 8, 4, 2, 1, 3/4,
  1/2, 1/4, 1/8, 1/16 beats; i > 9 → assert log + index 2. The table is in `.bss` and filled only by the `.init_array` entry 0x6cb20 (straight-line
  stores 0x6cbe0–0x6ce8c, r4 = 0xf61f18); readers 0x349858 (Chorus) and 0x349aa0. Kernel slot 3 0xfeb10 clamps |Hz| to 0.00104167…64, then
  Osc_setFrequency (999 BPM: i ≥ 7 hits the 64 Hz clamp; BPM 0 → floor; negative BPM → |Hz|).
- Depth d = rint(100v) clamped 0…100 (+0x10); depth scale s = 0.1f·rint(10 + 90v) (1.0…10.0 from v ∈ [0,1]) clamped [1, 100] (+0x18).
  t = F(F(d·s)·0.01f); only if 0 ≤ t ≤ 100: amp = F(F(F(t·fs)·0.001)·0.5), offset = amp + 0.2 (oscillator +0x00/+0x04). Delay = offset +
  amp·sine = 0.2…2·amp + 0.2 samples; UI range max (d 100, s 10) amp 220.5 → 441.2 samples = 10.0 ms (s up to 100 via v ≥ 11: 4410 samples,
  emulated by the critic).
- Phase deg = rint(180v) clamped 0…180 (+0x14); R-channel offset φ = deg·(1/380) cycles (literal 0x3b2c7692; deg > 180 → 9/19), so the maximum
  R lead is 0.4737 cycle = **170.5°, not 180°**. That a /380 rather than /360 divisor is a firmware slip is `guess`; the value is `confirmed`.
- Model validity: finite v with rint < 2^31 (|v| ≫ 1, e.g. phase v = 1e9 or 3.4e38, diverges or raises in `chorus.py`; unreachable from 0…1).
- Corrects F054's `likely` mappings (depth scale is not 1 + 9v; phase is not index·0.45/19).

**F059 — Chorus object and c_chorus kernel layout.** `confirmed` (57 fields model = emulation after every block, worker and critic runs)
- Chorus (0x2b0): EffectBase (ctor 0x1067d8; +0x10 dry, +0x14 wet); +0x1b8 → kernel; +0x1bc RATE (0x5c B); +0x218 SYNC (0x28 B); +0x240 BPM
  (0x5c B); +0x29c Mixratio; +0x2a0/+0x2a4/+0x2a8 rate/sync/BPM copies (0.5/0/120); +0x2ac dirty byte.
- c_chorus (0x100; ctor 0xff008(k, block 64, fs 44100)): +0x04 fs; +0x08 block (the kernel always processes this many samples, slot 25 passes
  no n); +0x0c rate Hz (0.1); +0x10 depth (100); +0x14 phase deg; +0x18 depth scale (1.0); +0x1c 0; +0x20 slot-9 value (unused by Chorus);
  +0x28 oscillator (0x98 B, F051); +0xc0 ring length int(fs/10) + block = 4474; +0xc4/+0xc8 → ring L/R; +0xcc write index; +0xd0/+0xd4 →
  oscillator output buffers; +0xd8 = 1/(0.0033·fs); +0xdc = −that; +0xe0 retrigger byte; +0xe1 byte (slots 16/17, cleared by ctor 0xff0cc;
  no effect on the output); +0xe2 reset byte (ctor 1); +0xe4 slot-9 side value; +0xe8 output gain; +0xec gain target; +0xf0 per-sample step;
  +0xf4 snap tolerance 0.01645; +0xf8 ring-full flag.
- Chorus vtable 0x842920 overrides: 0/1 dtors 0x115be0/0x116758, 10 retrigger 0x115a4c (→ kernel slot 18), 14 0x116224, 15 0x116140,
  23/24 0x115a68/0x115a70 (return 0), 25 0x115d70, 26 0x115a38, 27 0x115a14 (→ kernel slot 2 (64, 44100)); the rest are EffectBase.
- c_chorus vtable 0x841ba0: 2 0xfe6f4 → 0xfe59c re-allocate and zero ring/osc buffers; 3 setRateHz; 5/6/7 depth/phase/scale; 16/17 0xfe2c8/0xfe2e4
  set/clear +0xe1; 18 0xfe300 retrigger; 19 0xfe710 process (all `confirmed`). `likely` (capstone only): 4 0xfebc4 setPeriodMs (100…10000 ms,
  unused by Chorus), 8/14 0xfabc4/0xfabf4 return 0 (shared with c_distortion), 9 0xfe4a0 (+0x20 = rint(100v), +0xe4), 10–13 0xfe450/0xfe400/
  0xfe3b0/0xfe360 normalised getters rate/depth/phase/scale, 15 0xfe310 getter of +0x20.

**F060 — Chorus kernel algorithm; start-up fade is per-block exponential.** `confirmed`
- c_chorus slot 19 per block: reset flag +0xe2 → write index 0, ring zeroed, full flag 0, Osc_resetPhase(0), flag cleared; retrigger +0xe0 →
  Osc_resetPhase(0), cleared; oscillator fills `block` delay values per channel; per sample: ring[w] = x, y = linear interpolation at w − d
  (wraps by +4474), w += 1, first wrap sets the full flag; after the sample loop target = full ? 1 : 0 and step = (target − g)·(1/(0.0033 fs)) is
  applied linearly over the **next** block, then g snaps to the target if within 0.01645.
- **Corrects F055:** the start-up gain is not one linear 3.3 ms ramp. Each block covers 64/145.5 = 44 % of the remaining distance (g = 0.4398,
  0.6861, 0.8242, 0.9015, 0.9448, 0.9691, 0.9827 at the ends of blocks 69…75, snap to 1.0 at block 76). Blocks 0–68 (after the priming block) are 0.
- Chorus slot 27 0x115a14 (reset, from EffectBase slot 5, F022) only re-allocates/zeroes ring and oscillator buffers; it does not reset write
  index, full flag or gain. Slot 10 0x115a4c sets the retrigger (oscillator counter restarts next block). External callers of slot 10 and kernel
  slots 16/17: not found (H032).
- `tools/fx/chorus.py` is bit-exact to emulated slot 25 (with the per-block tempo feed): worker 38 runs × 160 blocks (778,240 samples;
  10 settings × impulse/sine/noise, Sync at 87.5/120/200/999 BPM, mid-run changes of every index, retrigger, reset, two tempo-change runs), critic
  12 more (delays to 4410 samples, BPM 1 and 133.37, six random parameter/tempo storms × 260 blocks); max error 0, state and final ring equal.
  Refuted alternatives: unquantised rate, phase /360, dry = 1 − mix, ring without +block, unquantised depth scale, linear fade-in, reversed sync table.

**F061 — Chorus output = dry at unity + Mixratio × wet.** `confirmed` (slot-18 emulation, worker and critic)
- Slot-25 output is the wet signal only (identical for Mixratio 0/0.5/1). At slot-18 level (activation slots 9/5/7, EffectBase post-stage 0x106c88
  neutralised) out = F(in + F(mix·wet)) bit-exact (critic, mix 0.25 and 1.5); out == in exactly in all mute blocks 0–68, also with the 10 Hz
  post-stage active and with delayed activation. The dry signal is **never reduced**; there is no crossfade.
- A mid-run Mixratio change glides linearly at 1/147 per sample (≈ 3.3 ms) at the output (EffectBase 0x10770c ramping the gate's wet target);
  so the law above is the steady state. The glide and the 10 Hz post-stage belong to the EffectBase model (H014/H022), not `chorus.py`.

**F062 — Master and Send build the identical Chorus.** `confirmed` for construction
- c_chorus ctor 0xff008 is called from 0x114de0 (MasterFxProcessor ctor 0x114bc0), 0x118c40 (Insert) and 0x11be0c (SendFxProcessor ctor
  0x11bbe4); the 67–68-instruction blocks Insert 0x118b5c, Master 0x114cfc, Send 0x11bd28 are identical after resolving literals (worker and
  critic, independent alignments). An emulated Master-built object gives output identical to the Insert-built one (100 noise blocks).
- Not settled: Master/Send slot-52 defaults for Chorus (index 2, F019) and whether their processBlock feeds the tempo (param 7) to it.

## Flanger end-to-end (Insert index 1; built identically in Master/Send) — cycle 011 (H034)

Evidence for F063–F068: kb/cycles/011.md (Worker + Critic), `harness/H034_flanger_model.py` (run `python -B
harness/H034_flanger_model.py --out DIR` → `RESULT: 0 failed checks`, 14 PASS; `h034_report.txt` sha256 a9713642…c019, `h034.json`
861a3234…913b, sorted concatenated `*.f32` (41 files) b00781e5…be46; `--mutants` 8/8 caught, `h034_mutants.txt` 45647c8f…2de4; all reproduced
byte-identically by the critic), `tools/fx/flanger.py` (reuses `osc.py` and `chorus.LinParam/Toggle/rint_idx` unchanged). Critic probes
(knee, storms, long feedback, tempo, retrigger/reset clusters, kernel slot 3 direct, Insert/Master/Send-built objects) in
`<critic scratch run>` (scratch, not kept). H021/H023/H026/H028/H031/H033 harnesses still pass with their recorded hashes. All addresses 1.60.

**F063 — Flanger parameters and when they apply.** `confirmed`
- Slot 14 0x1163f0 (always returns 0): 0 RATE (LinearParameter id 0, +0x1bc), 6 SYNC (ToggleParameter id 6, +0x218), 7 BPM (LinearParameter id 7,
  +0x240, 1…999, 120): applied at the **next slot 25** with F026 change detection (copies +0x2a0/+0x2a4/+0x2a8, dirty +0x2ac). 1 DEPTH, 2 PHASE,
  3 DEPTH SCALE, **4 FEEDBACK**: applied immediately via kernel slots 5 0xfffd4 / 6 0xffe68 / 7 0x100104 / **8 0xff694**. 5 MIXRATIO: float +0x29c
  (ctor **0**, no clamp). ≥ 8 ignored.
- **Corrects the cycle-009 functions entry:** FEEDBACK goes to kernel **slot 8** (0xff694), not slot 4. Kernel slot 4 0xfff50 is setPeriodMs
  (ms clamped [100, 10000], stored into the rate field +0x0c, Osc_setPeriodMs) and no Flanger method calls it (vcall scan of slots 10/14/15/25/26/27);
  external generic callers not excluded (H032).
- Insert defaults (slot 52 0x118a9c case 1, emulated bits): Rate 19/99 (→ 0.20 Hz), Depth 1.0, Phase 0, Depth scale 0 (→ 0.1), Feedback 0,
  Mixratio 0, Sync 0; BPM fed every block (F017). With these defaults the delay is only 0.2…4.61 samples. That the UI/project overrides them is `guess`.
- Slot 26 0x1159d4: dry +0x10 = 1.0, wet +0x14 = Mixratio (instruction-identical to Chorus slot 26). `likely` (not emulated): slot 15 0x1162f0
  getParameter via kernel getters 11–14.

**F064 — Flanger parameter formulas.** `confirmed` (289 worker read-backs + critic direct/boundary checks, 0 mismatches)
- Same BasicParamSpec quantiser as F058, i = rint(F(lo + F(v·(hi − 1 − lo)))). Spec helpers: rate 0x349e30 {1,101} → 0x349e50 i·0.01f; sync
  0x349e9c {0,7} → 0x349eb8 (halfword pairs at 0xf61f78; check `cmp #6; bls` is unsigned, so i > 6 or i < 0 → assert log + index 4); depth 0x34a254
  {0,101}; phase 0x34a2a0 {0,181}; scale 0x34a2f0 {1,71} → 0x34a310 i·0.1f; feedback 0x34a358 {0,100}; kernel slot 9 0x34a3a8 {0,101}.
- Rate, Sync off: Hz = 0.01f·rint(1 + 99v) → **0.01…1.00 Hz** (10× slower than Chorus). Sync on: i = rint(6v), (a, b) = (64,1),(32,1),(16,1),(8,1),
  (4,1),(2,1),(1,1) → one cycle per 64…1 beats; Hz = F(F(F(b·BPM)/a)·F(1/60)). The 7-entry table 0xf61f78 is filled by the same `.init_array`
  block as Chorus's (0x6cbe0–0x6ce8c). Kernel slot 3 0xffdc4 clamps |Hz| to 0.00026041671 (0x3988888a)…128 Hz (Chorus 0.00104…64).
- Depth d = rint(100v) clamped 0…100; depth scale s = 0.1f·rint(1 + 69v) = 0.1…7.0 clamped (ctor 2.0); t = F(F(d·s)·0.01f), t < 0 → 0 (no upper
  check); amp = F(F(F(fs·t)·0.001)·0.5), offset = amp + 0.2; delay = 0.2…2·amp + 0.2 samples, max (d 100, s 7) 308.87 samples = 7.0 ms.
  Refines F054's `likely` "0.1 + 7v".
- Phase: identical code to Chorus (deg = rint(180v), R offset deg/380 cycles, F058).
- **Feedback:** i = rint(99v) → fb = F(i·0.01f), i > 99 → 0.98999995 (0x3f7d70a3), i < 0 → 0; +0x10c written only if 0 ≤ fb < 1, +0x1c = i.
  **Positive only, 0…0.99 in 0.01 steps — no negative feedback.**
- Model validity: finite v with rint < 2^31; the out-of-range sync assert path (v outside ≈ [−0.083, 1.083]) is not emulable (unstubbed vsprintf)
  and is modelled from the disassembly only.

**F065 — Flanger object and c_flanger kernel layout.** `confirmed` (66 fields model = emulation after every block)
- Flanger (0x2b0): same layout as Chorus (F059) except Mixratio ctor 0.
- c_flanger (0x118; ctor 0x100234(k, block 64, fs 44100)): +0x04 fs, +0x08 block, +0x0c rate Hz (0.1), +0x10 depth (100), +0x14 phase deg,
  +0x18 depth scale (2.0), +0x1c feedback index, +0x20 slot-9 value, +0x28 oscillator (0x98 B, sine, ctor amp 44.1/offset 44.3), +0xc0 ring length
  fs·7/1000 + block = 372, +0xc4/+0xc8 → rings, +0xcc write index, +0xd0/+0xd4 last read index L/R, +0xd8/+0xdc → delay buffers, +0xe0/+0xe4 →
  per-sample gain buffers, +0xe8/+0xec/+0x110 fade constants (**never read by slot 19**), +0xf0 retrigger byte, +0xf1 byte (slots 16/17, no output
  effect), +0xf2 reset byte (ctor 1), +0xf4/+0xf8 previous pre-gain output L/R, +0xfc slot-9 fraction (unused), +0x10c feedback.
  The 372-sample ring length is a read-back fact; it is not observable in the output (max delay 308.9 < 372).
- Flanger vtable 0x8429a8 overrides: 0/1 dtors 0x115c70/0x1166c0, 10 0x1159e8 (→ kernel 18), 14 0x1163f0, 15 0x1162f0, 23/24 0x115a04/0x115a0c
  (return 0), 25 0x115f58, 26 0x1159d4, 27 0x1159b0 (→ kernel slot 2 (64, 44100)).
- c_flanger vtable 0x841c10: 2 0xff990 → 0xff798 re-allocate/zero rings + 4 buffers; 3 0xffdc4 setRateHz; 4 0xfff50 setPeriodMs; 5/6/7 depth/phase/
  scale; 8 0xff694 feedback; 9 0xff598 (+0x20/+0xfc, unused); 16/17 0xff370/0xff38c set/clear +0xf1; 18 0xff3a8 retrigger; 19 0xff9ac process
  (`confirmed`); 10–15 0xff548…0xff3b8 normalised getters (`likely`).

**F066 — Flanger kernel algorithm.** `confirmed`
- c_flanger slot 19 per block: reset flag +0xf2 → indices 0, rings zeroed, y_prev 0, flag cleared (**no oscillator phase reset**); retrigger +0xf0
  → Osc_resetPhase(0); oscillator fills 64 delay values per channel; per sample r = w − trunc(d) (+372 if < 0), ring[w] = F(x + F(y_prev·fb)),
  w += 1, fr = d − trunc(d), y = F(F((1 − fr)·ring[r]) + F(fr·ring[r − 1])), y_prev = y (**pre-gain feedback**); then y ·= g(d) with
  g(d) = F(F(1 + F(d·0.013154167)) − 0.6314) for d ≤ 48 (strict: 47.999996 → slope, 48.000126 → 1) else 1 — continuous at the knee, 0.3686 at d = 0.
  Wet only. **No start-up mute or fade** (block 0 already has output; unlike c_chorus F060). No limiter (peak ≈ 6 at fb 0.99).
- Slot 27 0x1159b0 re-allocates/zeroes rings and buffers but keeps write index, y_prev and feedback. Slot 10 sets the retrigger.
- `tools/fx/flanger.py` is bit-exact to emulated slot 25 with the per-block tempo feed: worker 41 runs × 160 blocks (839,680 samples; 11
  settings × impulse/sine/noise incl. fb 0.99 at max delay, Sync at 1/87.5/120/999 BPM, feedback v −0.5/1.5, plus 4 event runs × 2 with mid-run
  changes, retrigger, reset, tempo changes), critic ≈ 0.9 M more (knee straddling, 1,500-block knee run, 5 random storms × 400 blocks, 1,000-block
  fb 0.99 run, BPM changed every block); max error 0, state equal. Refuted: feedback after the gain, linear 0.99v feedback, knee scaling with depth,
  Chorus rate law, integer delay, reversed sync table, unquantised depth scale.
- Limits: bit-exactness assumes a zero-filled heap for the oscillator counters (+0x80 and the resync counter +0x68, H036) and FPSCR FZ = 0; with
  FZ = 1 the fb-0.99 silence tail diverges once |y| < ~1.8e-37 (first divergence measured; inaudible; F020 caveat).

**F067 — Flanger output = dry at unity + Mixratio × wet.** `confirmed`
- Slot-25 output is identical for Mixratio 0/0.5/1; at slot-18 level (activation slots 9/5/7, 0x106c88 neutralised) out == F(in + F(mix·wet)) in
  2,560/2,560 samples for mix 0, 0.25 and 1; a crossfade law is off by up to 0.25/1. Same law as Chorus (F061).

**F068 — Master and Send build the identical Flanger.** `confirmed` for construction
- c_flanger ctor 0x100234 is called from 0x114f58 (MasterFxProcessor ctor), 0x118db8 (Insert), 0x11bf84 (SendFxProcessor ctor); blocks Insert
  0x118cd8–0x118de0, Master 0x114e78–0x114f80, Send 0x11bea4–0x11bfac are instruction-identical (66 instructions, literals resolved). Insert-,
  Master- and Send-built objects give identical output, bit-exact to `flanger.py` (worker Master, critic all three).
- Not settled: Flanger's index in the Master/Send arrays, their slot-52 defaults and tempo feed (H037).

## Distortion end-to-end (Insert index 6; built identically in Master/Send) — cycle 013 worker / cycle 014 critic (H035)

Evidence for F069–F074: kb/cycles/013.md `## Worker` (copied verbatim into kb/cycles/014.md), kb/cycles/014.md `## Critic`
(all criteria CONFIRMED). Harness `harness/H035_distortion_model.py` (`python -B harness/H035_distortion_model.py --out <dir>`
→ `RESULT: 0 failed checks`, report sha256 29a5598b…b95b, json 7c0b94bc…4c00, sorted 53 `*.f32` c2ad7973…82f0; `--mutants` 8/8 caught,
85cf0b7c…1707; worker and critic hashes identical). Models: `tools/fx/distortion.py`, `tools/fx/glibc_expf.py` (own code; the glibc
2.13 expf tables are read at run time from `decoded/lib/libm.so.6`). Critic fuzz: 921,600 more samples bit-exact (random/out-of-range values, hard
clip, NaN/Inf, random resets, 0xA5 heap). Regression H021/H023/H026/H028/H031/H033/H034 unchanged.

**F069 — Distortion parameters (slot 14 0x1164d8).** `confirmed` (engine side); UI names partly `likely`/`guess`
- No Parameter objects. The inline block (0x119060–0x1190ec) only zeroes six stored values at +0x1bc…+0x1d0 (three 8-byte stores).
  Slot 14 applies every index **immediately**, stores v at +0x1bc + 4i, returns 0, ignores i ≥ 6. Slot 15 0x115a78 returns the stored copies.
- Index map (jump table @0x1164f4): 0 → dB = 40v → kernel 0xfa614 (drive); 1/2/3 → kernel slots 5/6/7 (output LPF / HPF / pre-clip LPF) with
  f = (float)(20·pow(10.0, (double)(3v))), i.e. 20 Hz…20 kHz; 4 → kernel slot 8 (dynamics threshold) with raw v; 5 → kernel slot 9 (100.0, unused by
  process) then EffectBase **wet +0x14 = v, dry +0x10 = 1 − v** (no clamp).
- Change detection is in the kernel setters: each one skips a value equal to its change copy (+0x0c…+0x1c, raw unclamped value); poke test confirmed.
- Insert slot-52 case-6 defaults: (0, 0.0), (1, 1.0), (2, 0.0), (3, 1.0), (4, 0.0), (5, 1.0), i.e. drive 0 dB, blend 0, both LPFs 20 kHz, HPF 20 Hz
  (clamped to 50), threshold 0 (auto-gain off), Mixratio 1 → **fully wet, dry 0**.
- UI integer domains used by slot 52 (critic, static, 0x118350 via table 0x117450; range functions 0x34bef8/0x34bee4, 0x34bf58/0x34bf40,
  0x34c018/0x34c000, 0x34c0d8/0x34c0c0, 0x34c198/0x34c180, 0x34c1e8/0x34c1d0): index 0 0…80 (0.5 dB steps), 1/2/3 0…1000, 4 0…100, 5 0…100.
  That the UI uses the same domains is `likely`. The engine itself does not quantise.
- UI names (strings 0x87faf0…: DRIVE, LO FREQ, HI FREQ, DYNAMICS, TONE, MIX RATIO; FxParamIndex 35…40 → slot-14 indices 0…5 via 0x843d98+0x78/+0xc0):
  DRIVE = 0, MIX RATIO = 5, DYNAMICS = 4, LO FREQ = 2 (HPF) `likely`; HI FREQ = 3 (pre-clip LPF), TONE = 1 (output LPF) `guess` (→ H042).

**F070 — Distortion coefficient formulas.** `confirmed` (385 emulated read-backs, 0 mismatches; literals checked in code)
- Drive (0xfa614): drive = powf(10, F(dB·0.05)) (×1…×100 for 0…40 dB); blend = 0 for dB ≤ 0, else min(F(dB·0.05), 1) (full from v = 0.5).
- Cutoffs (kernel slots 5/6/7, e.g. HPF 0xfa234): fc = clamp(f, 50, 20000); a = expf(F(F(fc·−2π)·F(1/fs))), b = 1 − a. Output LPF +0xc4/+0xc8,
  HPF +0xd8/+0xdc, pre-LPF +0xec/+0xf0; clamped cutoffs at +0xd4/+0xe8/+0xfc.
- Threshold (kernel slot 8 0xfa07c): hi T = clamp(v, 0, 1), lo = T·0.70794576 (−3 dB). Init T = 0.1.
- Auto-gain constants (init 0xfa36c): inc = expf(1/(0.1·fs)) (+100 ms e-fold), dec = expf(−1/(0.003·fs)) (3 ms), hold = fs/50 = 882 samples,
  gain range [1, 100]. Init coefficients use 1/fs·(−125663.71) / 1/fs·(−314.159), which round differently from the setters' (fc·−2π)·1/fs.
- libm oracle = emulated 1.60 libm: pow(10, y) is correctly rounded here (0/2000; host math.pow differs in 1/2000); powf = fdlibm (0/2000);
  **bit-exact coefficients need the glibc 2.13 expf** (glibc_expf 0/3000 and 0/20,000; a correctly rounded expf differs in 1/3000). Its accurate
  tables are not correctly rounded exp values, so the model reads them from the local libm at run time.

**F071 — Distortion object and c_distortion kernel layout.** `confirmed` (62 fields model = emulation after every block)
- Distortion (0x1d8): EffectBase (+0x10 dry, +0x14 wet); +0x1b8 → kernel; +0x1bc…+0x1d0 stored values 0…5. Vtable 0x842898 overrides 0/1 dtors
  0x115d00/0x116670, 10 0x115bc8 (return 0), 14 0x1164d8, 15 0x115a78, 23/24 (return 0), 25 0x115d48, 26 0x115bc4 (`bx lr`), 27 0x115b0c.
- c_distortion (0x138, ctor 0xfa568(k, 64, 44100)): +0x04 fs, +0x08 block, +0x0c drive-dB copy, +0x10/+0x14/+0x18 out/HPF/pre cutoff copies,
  +0x1c threshold copy, +0x20 slot-9 value, +0x28 oscillator (0x98 B, sine 1 Hz, never run), +0xc0 1/fs, +0xc4/+0xc8 out-LPF a/b, +0xcc/+0xd0
  out-LPF state, +0xd4 out cutoff, +0xd8/+0xdc HPF a/b, +0xe0/+0xe4 HPF state, +0xe8 HPF cutoff, +0xec/+0xf0 pre-LPF a/b, +0xf4/+0xf8 pre-LPF state,
  +0xfc pre cutoff, +0x100 block, +0x104 drive, +0x108/+0x10c hi/lo threshold, +0x110 gain, +0x114/+0x118 inc/dec, +0x11c/+0x120 hold reload/counter,
  +0x124 slot-9 fraction, +0x128 0, +0x12c 1/(0.01 fs), +0x130 byte (slots 16/17), +0x134 blend. Not read by process: +0x20, +0x124, +0x128, +0x12c,
  +0x130. +0x24 is never written (heap content).
- c_distortion vtable 0x8418a0: 0/1 dtors 0xfa520/0xfa540; 2 0xfa4f4 re-init (→ init 0xfa36c; block or fs ≤ 0 → drive = −1, return 0); 5/6/7
  0xfa2d0/0xfa234/0xfa198 cutoff setters; 8 0xfa07c threshold; 9 0xfa0e8; 16/17 0xfa154/0xfa174 set/clear +0x130 (if drive ≥ 0); 3, 4, 10–15, 18, 19
  are c_effect_base defaults (0x841830). Process 0xfa78c is non-virtual (only caller 0x115d5c). 0xfa694/0xfa70c have no direct callers (`likely` dead).

**F072 — Distortion algorithm (c_distortion process 0xfa78c, per 64-sample block, in place).** `confirmed`
1. HPF: lp = b·x + a·lp, y = x − lp. 2. Pre-clip LPF: y = b·x + a·y. 3. Stereo-linked auto-gain: x ·= g; m = max(|L|, |R|) of the **post-gain**
   samples; m ≥ T → g ·= dec (clamp ≥ 1), hold := reload; lo ≤ m < T → hold := reload; m < lo → after the 882-sample hold, g ·= inc (clamp ≤ 100).
   T = 0 means the gain never rises (auto-gain off).
4. Shaper: u = x·drive; |u| > 1 → ±1; else s = 1.5u − 0.5u³, w = blend·(1 − |s|)³, out = (1 − w)·s + w·**u³** (the blend goes towards the raw cube, not
   the hard clip). 5. ×0.7. 6. Output LPF (after the ×0.7).
- Every multiply-add is non-fused. Small-signal gain at drive 0 is 1.05. With blend 1 (≥ 20 dB drive) quiet signals follow 0.7·u³ (a dead zone,
  `likely` audible as gating/crossover distortion; the auto-gain can lift quiet input into the clipper). No modulation (the oscillator is never run).
- **Mixratio is a crossfade**: at slot-18 level out = F(F((1 − v)·in) + F(v·y)) in 2560/2560 samples (v = 0, 0.3, 1); the Chorus/Flanger unity-dry
  law (F061/F067) fails. Unlike Chorus/Flanger.
- `tools/fx/distortion.py` is bit-exact to emulated slot 25: worker 53 runs (1,141,760 samples; 9 settings × impulse / low and high sine /
  noise / silence × 160 blocks; gain limits 1 and 100 reached; mid-run changes of every index, resets, slots 10/16/17, kernel slot 9), plus 921,600
  critic fuzz samples. Refuted alternatives (each caught): blend towards the hard clip, weight (1 − |s|)², ×0.7 after the output LPF, detector on
  the pre-gain sample, per-channel gain, LPF before HPF, unclamped cutoffs, blend = dB/40.
- Limits: assumes FPSCR FZ = 0 (H038; only sub-1e-38 tails could differ). The EffectBase Mixratio glide and post-stage 0x106c88 are outside the model (H022).

**F073 — Distortion start-up, reset, retrigger.** `confirmed` (emulated)
- No start-up mute, fade or gate (first block 128/128 non-zero).
- Slot 27 0x115b0c = kernel slot 2 (64, 44100), a full re-init (filter states 0, gain 1, hold 882, drive 1, init cutoffs/threshold), then slot 14
  (i, stored value) for i = 0…5. Because of the change copies, only a parameter equal to its init value is skipped. EffectBase slot 5 (activation,
  F022) enters slot 27 once, so activation clears the filter/envelope state. Slot 10 (retrigger) returns 0 and changes nothing. If kernel slot 2
  fails (block or fs ≤ 0), drive = −1 and process returns 0 without touching the buffers.

**F074 — Master and Send build the identical Distortion.** `confirmed` for construction
- c_distortion ctor 0xfa568 is called from 0x11523c (MasterFxProcessor ctor), 0x11909c (Insert), 0x11c268 (SendFxProcessor ctor). The 36-instruction
  blocks 0x115200 / 0x119060 / 0x11c22c are instruction-identical (literals resolved). Objects from each give identical output (60 noise blocks).
- Not settled: Distortion's Master/Send array index and slot-52 defaults (H037).
- Publication note (critic): `tools/fx/glibc_expf.py` closely re-implements glibc's LGPL `e_expf.c` and has no licence/credit notice yet. It
  needs the same credit/licence review as the fdlibm ports before anything is published [Editor's note: published under LGPL-2.1-or-later as tools/fx/glibc_expf.py; see NOTICE.md.].

**F075 — InsertFxDelay parameters.** `confirmed` (cycle 015 worker + critic; `harness/H039_insert_delay_model.py`, emulated ctor 0x103488)
- The ctor registers 8 Parameters at obj +0x30c + 0x5c·i: 0 DelayTime 0..1 (ctor 0.75), 1 Feedback (0), 2 HiCut (1.0), 3 LowCut (0), 4 Spread (0),
  5 Mixratio (0), 6 SYNC (ToggleParameter; only v ≥ 1 or v ≤ 0 accepted, else return 3), 7 BPM 1..999 (120). Slot 14 is EffectBase 0x105d24
  (store only); indices 0–5, 7 return 0, ≥ 8 return 3. **Nothing applies immediately:** at the next slot 25, slot 26 (mix) runs, then slot 33 →
  slot 32, which consumes SYNC → BPM → DelayTime (F026 change detection, dirty flag +0x5c8) → Feedback → HiCut. **LowCut (3) and Spread (4) are
  never read** (static 0x102f30 + emulated: output identical for 0/0, 1/1, 0.5/0.25).
- Insert slot-52 case 4 defaults: DelayTime 49/99 (→ 500 ms), Feedback 0.7, HiCut 1.0, Mixratio 0 (wet 0, inaudible as for Chorus/Flanger),
  SYNC 0. BPM fed every block as parameter 7 (F017). The DelayEchoBaseSingleDelay base (+0x1b8, ctor 0x104774) registers its own DelayTime
  (1..1000) and FeedbackGain (0..1) objects at +0x1e4/+0x240; slot 14 cannot reach them and the Insert path never reads them.
- UI: strings at 0x87fab4 "DELAY TIME / DELAY FEEDBACK / DELAY HI CUT / DELAY MIX RATIO"; FxParamIndex 46–49 are the only entries for Insert
  index 4, → slot-14 indices 0, 1, 2, 5 (`confirmed` static); label → index by table order is `likely`. LowCut/Spread/SYNC have no FxParamIndex.
- Quirk: if DelayTime is never changed from its ctor value, the module keeps its ctor 50 ms; a BPM change then sets dirty and recomputes
  from the stored copy 0.5 → 505 ms (emulated, critic).

**F076 — InsertFxDelay formulas.** `confirmed` (emulated read-back sweeps, 0 mismatches; constants checked in 0x102f30/0x102ebc)
- Free time: ms = (float)rint_even(F(10 + F(v·990))) → 10…1000 ms in 1 ms steps, > 1000 clamps (setDelay 0xec9bc); D = trunc(F(F(ms·0.001f)·fs))
  samples (500 → 22050, 10 → 441, 1000 → 44100). **Integer delay; no interpolation** (the interpolating read 0xeaa84 always sees fr = 0).
- Sync: i = rint(5v) → beats 1/8, 1/4, 1/2, 3/4, 1, 2 (`.bss` table 0xf61fb4 filled by `.init_array` 0x6cb20; index 6 = 64/1 is a fallback);
  ms = F(F(F(F(num/den)·1000)·60)/BPM), clamped to [10, 1000].
- Feedback: g = F(rint(100v)·0.01f) = 0…1.00 in 0.01 steps (unclamped above 1), reached by a 147-sample linear SmoothFloat ramp (+0x2a0).
- HiCut: step = trunc_u32(F(999v)) + 1, clamped 1…1000; target 2000·m^(step−1) Hz, m = 10^(1/999) (double), i.e. 2–20 kHz; glides one step
  (×m or ÷m, accumulated in double) per 1/3 ms; fc = max(5, min(cut, 22050)); IirLpf1stOrder bilinear (t = tan(π·fc/fs), b0 = b1 = d/(d+1),
  a1 = (d−1)/(d+1), in double), recomputed every block.
- Mixratio (slot 26 0x102ebc): v < 0.75 → wet = F(v·1.3333334f), dry = 1; v ≥ 0.75 (and NaN) → wet = 1, dry = F(1 + F((v−0.75)·−4)).
  At slot-18 level (post-HPF 0x106c88 neutralised) out = F(F(dry·in) + F(wet·y)) at 9 values (worker 3 + critic 6); a plain crossfade and
  unity-dry both fail. This differs from Chorus/Flanger (unity dry) and Distortion (crossfade).
- Bit-exactness needs correctly rounded tan/pow (checked against the emulated 1.60 libm: tan 1504 args, pow 1000; host `math.tan` differs in 559).

**F077 — InsertFxDelay object, delay module and ring layout.** `confirmed` (47 fields model = emulation after every block, worker + critic fuzz)
- InsertFxDelay (new 0x5d0; device site 0x118f50 calls ctor 0x103488(obj, 44100, 64)): EffectBase +0x10 dry / +0x14 wet; +0x1b8
  DelayEchoBaseSingleDelay (secondary vt 0x841d10): +0x1bc block, +0x1c4 → 7×block scratch floats, +0x1c8 fs, +0x1d0 1/fs, +0x29c →
  DelayModuleStereo, +0x2a0 feedback SmoothFloat (N 147), +0x2c4/+0x2e8 SmoothFloats unused on the Insert path; +0x30c…+0x5b8 the 8 Parameters;
  +0x5b8 → HiCut container; +0x5bc SYNC copy, +0x5c0 BPM copy, +0x5c4 time copy (0.5), +0x5c8 dirty.
- DelayModuleStereo (vt 0x840010, new 0x8c, ctor 0xec734(m, fs, block, maxms 1000)): +0x20 ms (ctor 50), +0x24 D, +0x28/+0x2c/+0x30 pending
  flag/ms/D, +0x34 SignalGate (vt 0x840e40, N 147, starts closed), +0x7c warm, +0x7d full, +0x80 counter, +0x84 maxms, +0x88 = 1 (interp read).
- RingBuffer (vt 0x83e5c0, ctor 0xea2a4): interleaved stereo float, **trunc(maxms·0.001·fs) + 2500 = 46,600 frames** (depends on fs, not block
  size); +0x18 buffer, +0x1c write index, +0x28 read position (double).
- HiCut container (stepped filter, new 0x48, ctor 0xf3ce4(c, LPF, 1st order, fs, 1000 steps, 1/3 ms, 2000, 20000)) holding an IirLpf1stOrder
  (vt 0x840dd8). Vtable 0x841c80 overrides: 0/1 dtors, 23 0x1032ac / 24 0x103204 (set fs / block size, `likely`), 25 0x102cc0, 26 0x102ebc,
  27 0x102d04, 32 0x102f30, 33 0x102d3c; the rest is EffectBase. Secondary 0x841d10: 4 0x103d20 reset, 5 0x102d34 → slot 33, 8 0x102f28 → slot 32;
  slots 2/3 (0x103920/0x103890) roles open.

**F078 — InsertFxDelay algorithm (slot 25 0x102cc0 → slot 26, slot 33 0x102d3c, per 64-sample block).** `confirmed`
- y = gate(ring[w − D]) → HiCut LPF → **out = y (wet only)**, ring[w] = in + g·y, i.e. **feedback is taken after the HiCut filter**
  (NEON, flush-to-zero arithmetic). EffectBase then mixes dry/wet by F076.
- Delay-time change: setDelay marks the new time pending and closes the module gate (147-sample fade-out); the read is split so the fade
  ends at a chunk boundary, the read pointer jumps to the new delay, and the gate fades back in. **No glide, no pitch effect, no buffer clear.**
- `tools/fx/insert_delay.py` is bit-exact to emulated slot 25: worker 55 runs (5,373,440 samples; 10 settings × impulse/sine/noise/silence,
  10–1000 ms, feedback 0…1.0, sync at 60/87.5/120/133.37/999 BPM, 5 event runs), critic 16 random fuzz runs × 2000 blocks (4,096,000 samples,
  2,431 mid-run events incl. resets) plus edge cases (fb 1.0/1.2/3.0 to overflow incl. NaN bit patterns, denormal tails, per-block time/SYNC
  changes); max error 0, state and ring equal. Hashes: report bde7d958…43ca, json dc699809…893c, 55 f32 cba3fdab…4632.
  Refuted alternatives: feedback before HiCut, jump without fade, chunk-based warm-up counter, unquantised time, zeroing reset, HiCut
  without glide, crossfade mix, fractional delay, LowCut/Spread affecting audio.

**F079 — InsertFxDelay start-up, reset, retrigger.** `confirmed` (emulated at slot-25 level)
- Warm-up gate: the module gate opens (147-sample fade-in) only after the read chunk in which the counter reaches D; the counter adds the whole
  request n once per inner chunk (0xecb78), so it over-counts in fade-split blocks. With Insert defaults an impulse at t = 0 lands in the muted
  window and, since the gated signal is also the feedback source, **the delay stays silent** (0 non-zero samples in 1100 blocks); an impulse at
  t = 192 echoes at 22242.
- Slot 27 0x102d04 = slot 32, then 0x103d20 (module reset 0xec94c: commits a pending delay, rewinds ring indices write 0 / read −D, closes the
  gate, zeroes counter/warm/full; ramps snapped). **Ring samples are kept** (46,600 non-zero frames before and after), so stale pre-reset audio
  can leak after reset + delay changes (emulated; a zeroing-reset model differs in 1611 samples). HiCut state kept. EffectBase slot 5 (activation)
  runs slot 27. Slot 10 = EffectBase 0x10594c (returns 2, no state change).
- `likely` (static only): DelayTime v < ≈ −0.0096 gives D = 0 and slot 33's chunk loop would not advance (hang); unreachable from the 0…1 UI range.

**F080 — SendFxDelay (also Master "Delay") does not use the InsertFxDelay delay module.** `confirmed` for the static callee sets and maxms (worker + critic re-check); that it is a dual cross-fed algorithm is `likely` (→ H043). **Superseded by F115–F120 (cycle 021):** one shared L/R time on the parameter path; the "cross" gain pair is the Spread matrix before output and feedback.
- SendFxDelay process 0x104a30 runs two mono delay lines (0xec494/0xec4bc/0xec6d4, `likely` class DelayModule vt 0x840028) with separate L/R
  smoothed gains, a cross/feedback gain pair and two stepped filters inside the feedback loop (0xf438c); strings DelayTimeLch/Rch,
  FeedbackGainLch/Rch; maxms 4000.0 (0x841fa8). Shared with InsertFxDelay: RingBuffer 0xea2a4/0xea670, stepped filter 0xf3ce4/0xf41ac/0xf438c,
  SmoothFloat 0xf5b9c, vec add 0x578a6c. Not shared: DelayModuleStereo 0xec734/0xec9bc/0xecaf4/0xecd2c/0xec94c and reads 0xeaa84/0xea77c.


## InsertFxCompressor end-to-end (Insert index 7; FxCompressor core shared with SendFxCompressor) — cycle 016 (H040)

**F081 — InsertFxCompressor parameters.** `confirmed` (cycle 016 worker + critic; `harness/H040_compressor_model.py`, emulated ctor 0xf8a20 → 0xf7584)
- The ctor registers 14 Parameter objects at obj +0x1b8 + 0x5c·k. The EffectBase parameter vector at obj+4 is the slot-14 index map (critic):
  **0 Threshold, 1 Ratio, 2 Attack, 3 Release, 4 Gain, 5 Mixratio** (LinearParameter 0..1; ctor 1.0, 0, 1.0, 1.0, 0.5, 0), **6 LookAhead**
  (ToggleParameter +0x498: v ≥ 1 → on, v ≤ 0 → off, 0 < v < 1 → return 3, unchanged), **7 Knee** (0), **8 LevelDetect** (choice, stores trunc(v);
  1 = RMS, every other integer = peak), 9–13 ViewInputLevelL/R, ViewRatio, ViewOutputLevelL/R (meters written by slot 25, not on the audio path).
  Correction by the critic: the worker's "LookAhead unreachable, index 6 returns 3" is refuted (emulated on Insert and Send).
- Slot 14 is EffectBase 0x105d24 (store only); slot 15 0x1059c4 is a getter. **Nothing applies immediately:** each slot 25 re-reads every
  parameter (Parameter_getFloat 0xf0898; no F026 change detection). Only Threshold/Ratio/Knee have last-value copies (+0x788/+0x78c/+0x784,
  `!=`); a change resets the ramp length +0x6a8 to max(n, 44).
- Insert slot-52 case 7 defaults (emulated): Threshold 1.0 (0 dB), Ratio 0 (1:1), Attack 0 (0.05 ms), Release 0 (10 ms), Gain 0 (0 dB),
  Mixratio 1.0, Knee 0, LevelDetect 0 (peak) — **the default compressor is neutral**. No tempo feed: processBlock jump table 0x11694c case 7 →
  0x116a64 (critic, static).
- FxParamIndex tables (0x843d98+0x78/+0xc0): Insert index 7 appears only at FxParamIndex 50–55 → slot-14 indices 0–5 (`confirmed`, static,
  worker + critic). LookAhead/Knee/LevelDetect have no FxParamIndex, so **on the device the Insert compressor is `likely` hard-knee peak**
  (open whether another path writes 6/7/8 → H047). **Corrected by F163:** manager paths do write 6/7/8; device values undecided. UI strings 0x877a77…: COMPRESSOR RATIO / ATTACK / RELEASE / THRESHOLD / OUTPUT GAIN /
  MIX RATIO (label → index by name `likely`).

**F082 — InsertFxCompressor formulas.** `confirmed` (call-site read-back sweeps in 0xf8c40, 0 mismatches; range helpers 0x34b640…0x34b850 static)
- Index q = rint_even(F(lo + F(v·(hi−1−lo)))), unclamped. Threshold T = q(−52, 1) dB → −52…0 dB in 1 dB steps. Ratio R = F(q(10, 301)·0.1f) →
  1.0…30.0 in 0.1 steps (gain computer uses F(1/R)). Knee K = F(18v) dB (knee width 2K = 0…36 dB; K ≤ 0 acts as hard knee). Gain G = q(0, 51) dB
  → 0…50 dB; makeup = powf(10, F(G·0.05f)) (fdlibm).
- Attack i = q(1, 0x3fc) → ms = F(i·0.05f) for i ≤ 20 (0.05…1.0 ms) else i − 19 (2…1000 ms); **no values between 1.0 and 2.0 ms** (critic read-back
  0.85, 0.9, 0.95, 1.0, 2.0, 3.0 ms). Per-sample fall factor a = expf(−F(1/F(F(ms·fs)·0.001f))) (glibc 2.13 expf).
- Release ms = q(10, 0xfa1) → 10…4000 ms; per-sample rise factor r = expf(+F(1/F(F(ms·fs)·0.001f))).
- Mixratio (slot 26 0xf7380, run at the end of every gain stage): **dry = F(1 − v), wet = F(v·makeup)** — a crossfade with the make-up gain on the
  wet path. At slot-18 level (post-HPF 0x106c88 neutralised) out = F(F((1−v)·in) + F(v·makeup·y)) at 7 non-trivial values (worker 3, critic 4);
  unity-dry and crossfade-without-makeup fail.
- libm: the 1.60 double `log10` is **not correctly rounded** (81/1504 args differ from a correctly rounded log10); own port
  `tools/fx/glibc_log10.py` (fdlibm e_log10 algorithm, Sun notice) matches the emulated 1.60 libm in 1504 + 7,959 args. Also needs fdlibm
  powf and glibc expf (`tools/fx/fdlibm_powf.py`, `glibc_expf.py`). Licence review needed before publication (as F074).

**F083 — Compressor detector and gain computer.** `confirmed` (emulated; bit-exact model + 9 refuted mutants)
- Feed-forward, stereo-linked, **one detector level per 64-sample block** from the input. Peak (0xf8b88): max over the block of max(|L|,|R|),
  floor 1e-8, and the 1-based index of the maximum. "RMS" (inline in slot 25): ring of 132 = trunc(3 ms·fs) values of max(L², R²), sum in double,
  level = F(√(max mean in block)·√2), floor 1e-8.
- Gain computer in dB: L = F(20·log10(level)); static curve y = L + (1/R − 1)(L − T + W/2)²/(2W) inside the knee (W = 2K), hard knee for K = 0;
  g_t = powf(10, F((L − y)·−0.05f)); L ≤ −160 dB → g_t = 1.
- Target: an attack happens when g_t < 1 and g_t ≤ 1.4125376·target (+3 dB hysteresis): target = min(target, g_t), hold = min(trunc(Rl·fs/4000),
  441) samples (release/4, at most 10 ms; critic: 110/220/441 for 10/20/≥40 ms), ramp length = in-block index of the detector maximum. Otherwise
  the hold counts down by n; when expired the target is multiplied by e (+8.69 dB per block), capped at g_t and 1, ramp length max(n, 44).
- Gain smoothing in the gain domain: geometric ramp to the target over the ramp length (k = powf(target/gain, 1/ramp)), then a per-sample slew
  limit (fall ≤ ×a, rise ≤ ×r per sample) → **constant dB/ms slopes of nominally 8.69 dB per attack/release time** (actual slope from the
  float-rounded factor, ≤ ~1.2 % off at 4000 ms). out = gain·in on both channels. No delay in the Insert: the in-block ramp anticipates the block
  peak by up to 63 samples.
- Refuted alternatives (worker mutants, critic re-ran with identical counts): plain peak for RMS, unlinked (L-only) detector, feedback detector,
  hard knee, no slew limiter, target jump at block start, no hold, RMS without √2, unity-dry mix.

**F084 — FxCompressor / InsertFxCompressor layout and vtables.** `confirmed` for the 49 fields compared after every block (worker + critic fuzz, zero and 0xA5 heap)
- EffectBase +0x10 dry / +0x14 wet; Parameters +0x1b8…+0x68b; +0x68c slope, +0x690 knee point (dB), +0x694 current gain, +0x698 makeup, +0x69c fs,
  +0x6a0 → detector buffer, +0x6a4 block level, +0x6a8 ramp length / peak index; meters +0x6ac/+0x6c4/+0x6e0/+0x6f8 (6 words each: cur, floor 1e-8,
  ceil 2, decay −1 dB/block, hold 6 blocks, counter), +0x6dc minimum gain; look-ahead +0x710 (89) … +0x72c (1/147); RMS +0x730 (132), +0x734 pos,
  +0x738 1/132, +0x73c ring, +0x740 sum (double), +0x768/+0x76c; +0x748 LevelDetect copy, +0x74c LookAhead copy; +0x750 level dB, +0x754 hold
  counter, +0x758 hold length, +0x75c target, +0x760 → ramp buffer, +0x764 release ms, +0x770 e, +0x774 1/e, +0x778/+0x77c written only by
  0xf7fc8 (no xrefs, no pointer to it: `likely` dead); +0x784/+0x788/+0x78c last knee/threshold/ratio. SendFxCompressor (0x798) adds +0x790/+0x794.
- Vtables 0x841590 / 0x841618 / 0x8416a0 (32 slots) differ only in slots 0/1 (dtors) and 25. Overrides: 23/24/28/29/30 return 0 (`likely`: no
  re-init on fs/block change), 25 process, 26 0xf7380 mix, 27 0xf7fb8 reset; the rest EffectBase. Base slot 25 0xf8050 (not a Ghidra function) has
  no LevelDetect read / meters and is never a built object's slot (`likely` unused). Only scalar VFP (no NEON), no FPSCR writes.

**F085 — InsertFxCompressor end-to-end model.** `confirmed`
- `tools/fx/compressor.py` is bit-exact to emulated slot 25 0xf8718: worker 79 Insert runs (1,853,440 samples; 10 settings × impulse/
  3 sine levels/noise/level steps/silence covering ratio 1–30, threshold −52…0, attack 0.05…1000 ms, release 10…4000 ms, knee 0…18, gain 0/6/50 dB,
  Mixratio 0/0.5/1, RMS; 2 all-parameter event runs × 3 signals; 3 random-event runs), critic 20 fuzz runs (3,251,200 samples, 15,397 events incl.
  out-of-range values and index 6, 482 resets, threshold-tracking sines, denormals, 0xA5 heap); max error 0, full state equal after every block.
  Hashes: report 88ae0286…f8ba, json c1581413…4299, 83 f32 716e131c…f893, regress 3045b6cc…fa3e (H021–H039 reproduced).
- Known model gap (critic): ratio index 0 (v ≈ −0.0362…−0.0328, out of range) raises ZeroDivisionError where the device computes 1/0 = +inf; a
  one-line IEEE fix made those runs bit-exact (not yet applied, → H048).
- FPSCR caveat: emulation uses FZ = 0 and the compressor is scalar VFP, so denormal-input outputs depend on the device FZ (H038; inaudible).

**F086 — Compressor start-up and reset.** `confirmed` (emulated)
- No start-up mute/fade/gate: gain starts at 1 and ramps inside the first block. Slot 27 0xf7fb8 → 0xf7e38 sets gain = makeup = target = 1,
  minimum gain 1, hold 0, RMS sum and counter 0, release copy 10 ms, meters to floor, clears the look-ahead line; it **keeps** the RMS ring samples,
  position, ramp length, slope/point and last-value copies. EffectBase slot 5 → 0x10623c → slot 27 → slot 26 (mix uses makeup 1 until the next
  block). Slot 10 = EffectBase 0x10594c (returns 2, no change). Ctor quirk: hold length +0x758 is computed before +0x764 is set (emulated 0).

**F087 — SendFxCompressor = same core + 2 ms look-ahead.** `confirmed`
- Send slot 25 0xf8270 calls the same 0xf8b88/0xf8c40/0xf9490 with the same inline RMS code, plus ToggleParameter_getByte 0xf0814 (LookAhead) and an
  89-slot delay line (88 samples ≈ 2 ms) with a 1/147-per-sample linear crossfade between undelayed and delayed input; the detector sees the
  undelayed input, the gain is applied to the crossfaded signal. The real-ctor Send object (0xf8a40, vptr 0x8416a0) matches `Compressor.process_send`
  bit-exactly (worker 4 runs, critic 6 runs ≈ 742 k samples, incl. LookAhead toggled via slot-14 index 6). On the Insert, LookAhead has no audible
  effect (0xf8718 never refreshes +0x74c; 120 blocks identical on/off). Send/Master defaults and who writes index 6 remain open (→ H037/H047).

**F088 — Ducker has no audio key: it is a sequencer-trigger gain envelope.** `confirmed` (cycle 017 worker + critic; `harness/H041_ducker_model.py`, ProcRig emulation of the real processBlock 0x116860, InsertFxProcessor slot 54 0x11684c, InsertFxParameterManager slot 2 0x1263f4 and TriggerEraser slot 5 0x130cac)
- Slot 25 0xf6ef4 takes only (this, L, R, n) and reads no other buffer. The gain trace (out/in) is identical for DC, noise and level steps and
  stays equal with inf/NaN inputs. A 4× louder own input does not duck. With SYNC on at any BPM (1…999) and no trigger, nothing changes. Self-key,
  external audio key and free-running tempo envelope are all refuted.
- Trigger path: InsertFxParameterManager slot 2 0x1263f4 `(mgr, offset, type)` (primary base `ITriggerAndParameterReceiver`) forwards only
  types **11 and 15** (`cmp r2,#0xb; cmpne r2,#0xf`) to `mgr+0x1c` → vt+0xd8 = **InsertFxProcessor slot 54 0x11684c**, which calls
  TriggerTable_set 0x1310c4(table = proc+0x98, row = proc+0xa0, offset): flag[row] = 1, offset[row] = offset. The table is {int *flag, int *offset,
  int count} = processor ctor arg 3 (`sys+0x57c` at the creation site 0x1bbd78). TriggerEraser (vt 0x844bf8) slot 5 0x130cac → 0x1310f4 clears it.
  Manager slot 2 also stores the offset at mgr+0x88 and sets byte +0x86 = 1 for every type (role unknown, not used by the Ducker).
- processBlock jump table 0x11694c sends only index 9 to 0x116974, which every block: slot14(7, tempo clamped 1…999); slot15(10) = SOURCE, row =
  rint(SOURCE) (round half to even, 0x1169f4…0x1169fc); slot14(8, (float) flag[row]) via 0x1310dc; slot14(9, (float) offset[row]) via 0x1310e8;
  then slot 18. Insert slot 52 case 9 sets SOURCE = (float) proc+0xa0 (@0x117888), so by default the Ducker follows its **own track's** triggers;
  SOURCE 0…16 selects another row. Emulated: ducks start exactly at the selected row's trigger sample; other rows, event type 12 and tempo changes
  do not duck. proc+0xa0 = processor ctor arg 1 = track index (`likely`); 17 rows = 16 tracks + 1 (`guess`); callers of receiver slot 2 and the
  meaning of types 11/15 not traced (→ H049).
- **Tool caveat:** Ghidra/REA pseudocode of the update routine 0xf6630 drops the whole TRIGGER branch (0xf6944…0xf6980) as unreachable (it misses
  the out-parameter write of ToggleParameter_getByte 0xf0814). Use disassembly/emulation for this function.

**F089 — Ducker parameters.** `confirmed` (names from ctor strings; on-screen labels and FxParamIndex rows not checked → H051)
- Slot-14 indices (Parameters at +0x1b8 + 0x5c·k; toggles 0x28 long): 0 ATTACK (Linear 0…1, ctor 0.5), 1 ATTACKCURVE (0…1, 0.5), 2 RELEASE (0…1, 0.5),
  3 RELEASECURVE (0…1, 0.5), 4 NONE (0…1, 0; never read), 5 DEPTH (0…1, 0), 6 SYNC (Toggle +0x3e0), 7 BPM (Linear 1…999, 120; fed by the processor),
  8 TRIGGER (Toggle +0x464; fed by the processor), 9 OFFSET (Choice +0x48c, 0…64; fed), 10 SOURCE (Choice +0x4e8, 0…16; read by the processor, not
  the DSP). Indices 11/12 return 3. Slot 14 (EffectBase 0x105d24) only stores; everything applies at the next slot 25 via update 0xf6630 with
  F026-style change detection.
- Insert slot-52 case-9 defaults: ATTACK 0.03 (30 ms), ATTACKCURVE 0.5, RELEASE 0.0374880 (≈ 0.3 s), RELEASECURVE 0.5, DEPTH 1.0, SYNC 0, SOURCE = own
  track. The ctor leaves Na = 44 and both steps 1.0 until ATTACK/RELEASE/SYNC/BPM change.
- **No Mixratio:** slot 26 0xf6188 sets EffectBase dry +0x10 = 0, wet +0x14 = 1 (wet only).

**F090 — Ducker formulas.** `confirmed` (72 read-back probes, 0 mismatches; F = round to float)
- Free (SYNC off): A = F(fs·ATTACK) (0…1 s), Na = 1 if A < 1 else trunc(A); attack step F(1/Na). Rl = F(F(fs·RELEASE)·8) (0…8 s); release step =
  F(1/max(F(fs·0.001), Rl)) (≥ 1 ms).
- Sync: q = F(F(F(fs·0.25)·60)/BPM) samples per 1/16 note; A = q·TA[rint(127·ATTACK)], Rl = q·TR[rint(127·RELEASE)] (index round half to even);
  TA 0x841118 = 128 floats 0…4 sixteenths, TR 0x841318 = 128 floats 0.25…32 sixteenths (model restates them as decimal segments; harness asserts all
  256 equal to 1.60).
- Curves: c = (float) pow(100.0, F(2v) − 1) ∈ [0.01, 100], c = 1 at v = 0.5. DEPTH used as stored.
- libm: 1.60 `pow` = correctly rounded on 2498 args; 1.60 `log10f` = fdlibm float algorithm (own port in `ducker.py`; host F(log10) differs on 220 of
  2504 args).

**F091 — Ducker envelope algorithm.** `confirmed` (emulated; bit-exact model + 9 refuted mutants)
- State +0x594: 0 idle → trigger (skip OFFSET samples first; OFFSET 64 skips the whole block; > 64 keeps it pending; negative starts at once) →
  1 attack (0xf69e4) → 2 release (0xf6c6c) → 0. Gain g applied identically to L and R (stereo-linked, input-independent).
- Attack runs exactly Na samples. Control points every 11 samples (fewer at the end): x += 11/Na (≤ 1), target = (1−D) + D·(1 − (c^x−1)/(c−1)) (c^x−1 in
  double, result float; if |c−1| ≤ 2⁻²³: (1−D) + D(1−x)); per-sample increment (target − g)/count. No hold: release starts at once.
- Release: x −= 1/Rl per sample; at control points y = min(1, 1 − x + 11/Rl), target = (1−D) + D·(c^y−1)/(c−1) (linear: (1−D) + D·y), count =
  clamp(trunc(x·Rl), 1, 11). When x ≤ 0: g = 1, idle.
- Retrigger: in release, x := attack phase whose curve value equals g: log10f(((c−1)(1−g)+D)/D)/log10f(c) (linear (1−g)/D; 0 if the argument ≤ 0; kept if
  D ≤ 2⁻²³); in attack only the sample counter restarts (x continues, clamps at 1, so the floor 1−D lasts longer). One trigger per block; a TRIGGER held on
  across blocks fires once (edge: update writes TRIGGER back off via 0xf0614). With D = 1 the gain can dip slightly below 0 (−1.8e−17).
- Refuted mutants: curves ignored, control point every sample / every 22, exponential release, retrigger from x = 0, OFFSET ignored, level-sensitive
  TRIGGER, unlinked R, hold after attack.

**F092 — Ducker layout and vtable.** `confirmed` for the 45 fields compared after every block (zero and 0xA5 heap: ctor initialises all of them)
- +0x544 attack v, +0x548 release v, c_a, c_r, D, sync byte, bpm, +0x560 trigger byte, +0x564 offset, dirty byte, g, attack increment, release increment,
  +0x578 control counter, +0x57c/+0x57d attack-/release-done bytes, phase x, attack step, release step, Na, +0x590 attack sample counter, +0x594 state.
  EffectBase fs +0x90, dry +0x10, wet +0x14.
- Vtable 0x841098: 0/1 dtors 0xf7138/0xf7250; 23 0xf6178 returns 4; 24 0xf6180 returns 0 (roles unknown); 25 0xf6ef4 process; 26 0xf6188 dry 0/wet 1;
  27 0xf69a8 → update 0xf6630; 28–30 shared return-0 stubs; rest EffectBase (slot 18 = 0x106de4). 0xf69b8 = non-virtual copy of the trigger code, no
  callers (`likely` dead).

**F093 — Ducker end-to-end model.** `confirmed` (scope: slot 25 output)
- `tools/fx/ducker.py` is bit-exact to emulated slot 25: worker 57 runs (1,344,000 samples; 10 settings × impulse/sine/noise/steps/silence, tempos
  1/87.5/120/133/999, "beat" and "dense" trigger patterns, 2 parameter/tempo/SYNC/reset event runs, 3 random-event runs), critic 40 slot-25 fuzz runs
  (1,024,000 samples, 18 with 0xA5 heap, out-of-range curves/depth, offsets 0/1/63/64/65/100/−3, inf/NaN/denormal/3e38 inputs) and 16 processor-level
  runs (307,200 samples through real processBlock/slot 54/manager slot 2/eraser with an independently tracked table); max error 0, full state equal after
  every block. Hashes: report 5f54333e…ca79, json f8656fcd…bbe5, 57 f32 01334f1c…7b58, regress be46f3a1…3d2e (H021–H040 reproduced).
- At the processor (slot 18) output the shared EffectBase post-stage 0x106c88 (≈ 10 Hz HPF, `likely`) still applies; with it neutralised the rest of slot 18
  is wet-only apart from a ≤ 1.7e-6 activation crossfade in the first 3 blocks and ≤ 1.1e-38 denormal flushing in 0x10770c (`likely` NEON) (critic; → H044).

**F094 — Ducker start-up and reset.** `confirmed` (emulated)
- No start-up mute/fade in slot 25 (no trigger → block unchanged). Slot 27 0xf69a8 only re-runs the parameter update: a reset or EffectBase slot-5
  activation (0x10623c → 0xf69a8 → 0xf6630 → 0xf6188) does not stop a duck in progress. Slot 10 = EffectBase default (returns 2, no change).

## Track mixing (TrackUnit / MultiTrackUnit) — cycle 018 (H009)

Evidence for F095–F101: kb/cycles/018.md (Worker + Critic), `harness/H009_track_mix.py`, `tools/fx/track_mix.py`
(`python -B harness/H009_track_mix.py --out DIR` → `RESULT: 0 failed checks`, 16 PASS; worker and critic byte-identical: report
9f1dc126…cda6, json 47a28721…73d0, sorted 42-file f32 98769095…631d; `--regress` h009_regress.txt 32ff5ff1…85d9, H021–H041 reproduced).
Emulation runs the real TrackUnit::processBlock, Pan, Volume, Mute, both smoothers, the four MultiTrackUnit routing builders, SimpleTwoMixUnit
and CompositeFxUnit::processBlock; the player, LFO, inserts, meter, renderer and (worker only) OutputSelectors are stand-ins, and the mute
update 0x1ca3c8 is replaced by setting its output flags. The critic re-ran with the real OutputSelector code (0xe6b8c) and the real routing
setter 0x1ca0dc (scratch scripts outside the repo) and fuzzed 1,228,800 more samples.

**F095 — Per-track chain and stage order.** `confirmed` (static build chain + emulated call order, re-checked by the critic)
- Build: HexaTrackAudioSystem 0x1bc7c8 → `new(0x568)` MultiTrackUnit ctor 0x1c67e4, then per track `constructTrack` 0x1bacec (assert string
  "TrackUnit* HexaTrackAudioSystem::constructTrack(int)") → TrackUnit (`new(0x628)`, ctor 0x1cceb0 @0x1bad38) + LfoProcessor, MIDI param
  manager/formatter, PlayerUnit + PlayerParameterManager, and per insert slot InsertFxProcessor ctor 0x118b0c @0x1bbd80 + InsertFxParameterManager
  ctor 0x12864c @0x1bbda0 → addInsert 0x1c9874 @0x1bbf44 (+0xe8[slot] manager, +0xf4[slot] processor); addTrack 0x1c4390 @0x1bc880. Closes the
  F013 gap.
- TrackUnit (vt 0x864cac, 6 in / 6 out) processBlock 0x1ca58c, in order: clear graph buffer → PlayerUnit (+0xcc) renders ch0/1 →
  OutputSelector +0x10c → copy main → ch4/5 → OutputSelector +0x110 → insert FX slot 0…n−1 (InsertFxProcessor processBlock 0x116860) →
  OutputSelector +0x118 (ch4/5) → Mute#2 +0x130 (ch4/5) → OutputSelector +0x114 → **Pan** +0x128 → **Mute#1** +0x12c → copy main → ch2/3 →
  **VolumeKnob** +0x138 (send level, ch2/3) → **VolumeFader** +0x134 (main) → meter +0x13c → AudioRenderer +0x108 → MIDI formatter.
- All in float on the CPU inside the device callback (TrackUnits run inline or on the parallel AudioWorker threads via MultiTrackUnit's manager).
  Solo has no stage of its own (mute flags only, not traced).
- **Track routing mode** (critic, real code): TrackUnit 0x1ca0dc(mode) (from slot 101 0x1ca218) sets the OutputSelectors via setSelection
  0xe6ff4 and stores the mode at +0x61c. Mode 0: main = fx(source), ch4/5 = raw source. Mode 1 (+0x110 → (2,3)): main = fx(ext +0x608),
  ch4/5 = raw source. Mode 2 (+0x118, +0x114 → (2,3)): ch4/5 = post-insert main, main = ext +0x608 (after the inserts, before Pan). That this
  is the analog (DSF) filter loop pre/post the insert FX is `likely`; that +0x608 is the analog return is `guess` (writer 0x1c9a54 caller not
  traced). +0x10c's selection ([main, ext +0x604]) is not set by 0x1ca0dc (open).

**F096 — Track fader (volume) law.** `confirmed` (128/128 table entries, independently by worker and critic; 14 read-back values)
- VolumeFader slot 13 0xe9e48 = table 0x83e050[index], index 0…127 (struct clamp; Volume slot 5 range {0,128}): 0 → 0; 1…9 → −54, −50, −48,
  −46, −45, −44, −43, −42, −41 dB; 10…100 → (i/100)²; 101…127 → 2^(ln(i/100)/ln 1.27) (127 = ×2, +6.02 dB). Index 100 = 0 dB (ctor default; the
  real value is `prj::TrackData` "volume", int +0x30). `(i/100)^2.9` differs on 27 entries.
- Applied by Volume::processBlock 0xe9b70 → GainSmoother setTarget 0xe895c → applyStereo 0xe89f0; L = R.
- **Send level** = VolumeKnob slot 13 0xe9f08 → 0x34e660 = table[i] × 0.5 (127 → 1.0, 100 → 0.5; ctor index 0). Source field TrackData+0x68[0]+0x28
  is a `guess`.
- **Ramp:** linear, exactly 100 samples: step = F((target − current)·F(1/100)), gain used then incremented, gain := target at the end; it starts
  after the parameter's sample offset (struct +0x10) and crosses block boundaries. Same GainSmoother (0x24 bytes, ctor 0xe8900) for fader, send
  and both pan channels.

**F097 — Track pan law.** `confirmed` (disassembly of 0xe9594 by both; 13 emulated read-backs)
- Linear **balance** with 0 dB centre, range −64…+64 (Pan slot 5 {−64,65} → struct clamp): p < 0 → L = 1, R = (64+p)·(1/64); p > 0 →
  L = (64−p)/64, R = 1; p = 0 → (1, 1). Separate 100-sample ramps for L (+0x88) and R (+0x8c). No cross-feed (L-only source at +64 → silence).
  Value from TrackData "pan" (+0x34). Pan clamps value+mod only when the struct's modOn byte is set; normal writers clamp.
- Refuted alternatives (emulated mutants, 91,239 mismatches each): constant-power sin/cos, √ law, linear with −6 dB centre.

**F098 — Track bus summing and MultiTrackUnit channel layout.** `confirmed` (real routing builders + real SimpleTwoMixUnit with 4 real TrackUnits;
0 blocks differ from the model)
- MultiTrackUnit (vt 0x864570; 6 in / 16 out; processBlock 0x1c4ff8) runs each TrackUnit on its own 6-ch buffer, then four routing builders:
  0x1c4448 → out0/1 = Σ track ch0/1 (main, post-fader) → SimpleTwoMixUnit +0xe8; 0x1c4668 → out2/3 = Σ track ch2/3 (send) → SimpleTwoMixUnit +0xec;
  0x1c4888 → every track ch0/1 → AssignableUnit +0xe4 (out6…13, assignable/individual outs); 0x1c4dd8 → out4/5 = **the selected track's** ch4/5 (corrected cycle 037, F190: a selector, not Σ) →
  DsfSendOutputSelector +0xf0 (analog/DSF send; pre-insert in modes 0/1, post-insert in mode 2, F095).
- SimpleTwoMixUnit::processBlock 0x1535f8: float `addFrom(…, gain 1.0)` in track order; normalise flag +0x90 = 0 from the MultiTrackUnit ctor
  (@0x1c6ce8/0x1c6d24) → **no headroom scaling** (the unused flag would apply 1/(N+1)).
- Graph: out0/1 → CompositeFxUnit +0xa4 → MasterFxUnit; out2/3 → +0x13c → SendFxUnit (connections @0x1be3ec/@0x1be448, pairs 0xf53c44 → 0xf53868,
  0xf53c50 → 0xf53874).
- Not traced: MultiTrackUnit's own-input units +0xf4 (on in0–3, its ch0/1 → out14/15) and +0xf8 (in0/1), `likely` the input/THRU path; the other
  graph connections (→ H010).

**F099 — Send tap position.** `confirmed` (real call order + mutants)
- One send per track: ch2/3 = main **after the inserts, Pan and Mute#1, before the fader**, × send level (F096). A muted track sends nothing; pan
  affects the send; the fader does not. Mutants "send post-fader" (60,823) and "fader before the insert" (70,166) fail. In modes 1/2 the tapped
  signal is the selected (+0x608) path.

**F100 — Track mixing object layouts and writers.** `confirmed` for fields exercised by emulation; slot roles `likely` where noted
- TrackUnit (0x628): +0xc8 PlayerParameterManager, +0xcc PlayerUnit, +0xd0/+0xd4 LfoProcessor, +0xe0/+0xe4 MIDI manager/formatter, +0xb8 insert
  count, +0xe8… managers, +0xf4… processors, +0x108 renderer, +0x10c/+0x110/+0x114/+0x118 OutputSelectors, +0x11c/+0x120/+0x124 pan/volume/send
  parameter structs, +0x128 Pan, +0x12c/+0x130 Mute, +0x134 VolumeFader, +0x138 VolumeKnob, +0x13c meter, buffers +0x43c main / +0x4d4 send / +0x56c
  pre, +0x604/+0x608 external 2-ch buffers (setters 0x1c9a4c/0x1c9a54), +0x60c gate byte (0 → both mutes on = silent; also gates TrackData
  write-back), +0x61c routing mode 0/1/2 (Mute#2 open iff ≠ 0). 0x1ca3c8: main Mute on unless +0x60c ≠ 0, TrackData+0x39 == 0 and mode ≠ "Midi"
  (static, `likely` for the TrackData field roles).
- Parameter struct (0x24, ctor 0x1c3b70): +0 useAlt, +1 modOn, +4 value, +8 alt (p-lock), +0xc LFO mod, +0x10 sample offset, +0x14/+0x18 range,
  +0x1c/+0x20 clamp. processBlock passes (useAlt ? alt : value) [+ mod, clamped if modOn] with the offset to IVolume/IPan slot 3, then zeroes the offset.
- Writers: TrackUnit slot 66 0x1c8988 setVolume(v, offset) (67/68 pan/send twins, `likely`); slot 78 0x1c8328 parameter receiver (ids 13 volume,
  14 pan, 15 send → alt value, offset, useAlt = 1; `likely` sequencer p-locks); slot 79 0x1c7a90 LFO destination; slot 77 0x1c7a68 clears useAlt.
- Pan (0x98; vptrs 0x83d540/0x83d570): +0x88/+0x8c smoothers, +0x90 pan, +0x94 offset; slots 2/3 set 0xe98cc/0xe98d4. Volume (0x98): +0x88 smoother,
  +0x8c index, +0x90 offset; slots 2/3 set 0xe86e0/0xe86f0, 8 gain 0xe870c, 9 dB 0xe877c, 13 index→gain. Mute (0x88): +0x80 MuteSmoother (0x20,
  ctor 0xe7fd8, 128-sample fade; setMuted 0xe8050, apply 0xe808c), +0x84 on. OutputSelector (0xa0, vt 0x83cb90, processBlock 0xe6b8c, setSelection
  0xe6ff4): +0x84 mono-dup, +0x88 GainSmoother(128), +0x8c/+0x90 target pair, +0x94/+0x98 current pair, +0x9c async. SimpleTwoMixUnit (0xa0, ctor
  0x153844): +0x80 channel count 2(N+1), +0x88/+0x8c destinations, +0x90 normalise flag, +0x94 scale.
- Mixing is not offloaded: the Volume/Pan setters only store fields; the gains and sums are present in the emulated float buffers.

**F101 — Track mix model.** `confirmed` (scope: routing mode 0, normal audio)
- `tools/fx/track_mix.py` is bit-exact to the emulated TrackUnit::processBlock + summing: worker 41 runs (1,102,080 samples; 7 settings incl.
  0/127 fader, hard L/R, mid-run fader/pan/send/mute events with offsets 0…99), critic fuzz 1,228,800 samples (offsets up to 250, real and fake
  selectors, 0–2 inserts), 0 differ.
- Denormals: JUCE copyWithMultiply 0x5792c8 flushes denormals in its NEON part (first 4·⌊k/4⌋ samples of a constant-gain segment) and keeps them in
  the scalar tail; the model handles this for Pan/Volume, but **not** for the four real OutputSelector ×1.0 passes (critic: 24,797 of 645,120
  denormal-input samples differ with real selectors; 0 of 860,160 on normal audio). Modes 1/2 are not modelled.

## Cycle 019 — H010 send bus, return and master chain (critic-confirmed)

Evidence for F102–F108: kb/cycles/019.md (Worker + Critic), `harness/H010_send_bus.py`, `tools/fx/bus_mix.py`, `harness/lib/symwalk.py`.
Re-run: `python -B harness/H010_send_bus.py --out <dir>` → `RESULT: 0 failed checks` (14 PASS); `h010_report.txt` 8ed30f0b…7a85,
`h010.json` 49848d76…5a9d, sorted 30-file f32 b04bf76d…9435 (worker run_f/run_g and critic re-run identical); `--regress` → H009 + H021…H041
reproduced (`h010_regress.txt` f7a63fbf…be8e).

**F102 — Product graph connections.** `confirmed` (capstone + symwalk, 30 rows asserted in the harness; critic whole-.text caller scan)
- Primitives: connectPair 0x1b61bc (per channel: canConnect 0x5fae80 → addConnection 0x5ff2c4, JUCE AudioProcessorGraph); MIDI 0x1b7380;
  input helpers 0x1b7480/0x1b76a0/0x1b77b0/0x1b7590 (audioIn pairs 0,1/2,3/4,5/6,7); output helpers 0x1b78c0 (→ out 0,1 **and** 12,13),
  0x1b7ab0…0x1b7ef0 (→ out 2,3 … 10,11). Only three builders wire graphs: the base build 0x1b6284 (device/IO/resample nodes, runs first and
  then calls slot 55 @0x1b6db8), the product build HexaTrackAudioSystem slot 55 0x1bc8d4, and the factory test graph TestModeAudioSystem slot 55 0x5376c8.
- 0x1bc8d4 connections (src → dst): audioIn (0,1)/(2,3)/(4,5) → MTU (0,1)/(2,3)/(4,5); audioIn (0,1) → liveSampling; MTU (0,1) → CFX (0,1)
  @0x1be3ec; MTU (2,3) → CFX (2,3) @0x1be448; **CFX (0,1) → masterOut (0,1) @0x1be9a0; CFX (2,3) → masterOut (2,3) @0x1bea04**; MTU (14,15) →
  masterOut (4,5) @0x1bea5c; masterOut (2,3) → headphone (0,1); audioIn (2,3) → headphone (2,3); MTU (6,7)…(12,13) → headphone (4,5)…(10,11);
  audioIn (0,1) → headphone (11,12) (so headphone in11 has two sources, MTU ch13 and audioIn ch0, summed by JUCE — `likely` quirk);
  masterOut (0,1) → masterAssignableSelector (0,1); MTU (6,7) → selector (2,3); selector → dsfDriveMaster; MTU (4,5) → dsfDriveSend;
  dsfDriveMaster → deviceOut (0,1) and (12,13); MTU (8,9)/(10,11)/(12,13) → deviceOut (2,3)/(4,5)/(6,7); headphone → deviceOut (8,9);
  dsfDriveSend → deviceOut (10,11); plus 3 MIDI connections. No path feeds the Send return into the Master FX input.
- Graph-end nodes (critic correction): sys+0x3bc = DeviceInputUnit graph node (ctor 0x1ade60), sys+0x3c0 = **AudioDeviceOutputUnit** graph
  node (ctor 0x1ae7dc, 7 pairs, 14 in / 14 out), both made by 0x1b6284. (Cycle 020 correction, F114: 0x3bc/0x3c0 are the node handles; the unit
  objects are at sys+0x3b4 / sys+0x3b8.) So dsfDriveMaster → deviceOut (12,13) is not refused (`likely` feeds the resample recorder);
  the resample player feeds deviceInput (4,5) (`likely`; its "→ MTU in4/5" continuation is refuted in cycle 037, F189: MTU in4/5 carries device in2/3, the DSF return).
- Nodes (class, ctor, in/out, processBlock): MultiTrackUnit 0x1c67e4 6/16 0x1c4ff8; LiveSampling 0x13d7e8 2/?; CompositeFxUnit 0x1aa808 4/4
  0x1a94cc; MasterOutUnit (vt 0x862a58) 0x1b2398 6/4 0x1b2150; HeadphoneUnit (vt 0x862898) 0x1b17b0 14/2 0x1b10ec; masterAssignableSelector =
  Output12Router (vt 0x862b54) 0x1b2d8c 4/2 0x1b2610; dsfDriveMaster/Send = DaveSmithDriveUnit (vt 0x834088) 0xc3ed0 2/2 0xc3ce8.
  Selector pairs sys+0x50c/+0x514 = (0,1)/(2,3), written only in the HexaTrackAudioSystem ctor 0x1c2cac (`likely` constant).

**F103 — CompositeFxUnit does no mixing.** `confirmed` (real 0x1a94cc emulated, inline and pooled, 4 settings)
- processBlock 0x1a94cc points view +0xa4 at graph ch0/1 and view +0x13c at ch2/3 (setDataToReferTo 0x576afc, no copy) and runs MasterFxUnit
  (+0x8c) on ch0/1 and SendFxUnit (+0x90) on ch2/3 in place — inline, or as two jobs on the ParallelAudioProcessingManager (+0x94; job runner
  0x153980). Output: out0/1 = Master FX output, out2/3 = Send FX return. No summing, no gain, nothing crosses between the pairs.

**F104 — One stereo send bus; SendFxUnit and its return fader.** `confirmed`
- Exactly one send bus: one MTU send pair (out2/3), one CompositeFxUnit Send view, one SendFxProcessor. (H010's "small number of buses" → one.)
- SendFxUnit::processBlock 0x1b3068: SendFxProcessor (+0x8c) → **return VolumeFader** (+0x90, ctor 0xe9e5c, initial index 100) → meter (+0x80).
  Gain = the F096 fader table (0 → 0, 1 → 0.00199526, 50 → 0.25, 71 → 0.5041, 100 → 1, 115 → 1.49977, 127 → 2.0), 100-sample linear ramp from the
  sample offset (emulated 7 values + a 100→60 step at offset 17, bit-exact).
- SendFxProcessor::processBlock 0x119994: a MuteSmoother (+0xa8) on the send bus *before* the effect is muted when pending == −1 ("Off") or
  disabled byte +0x9e ≠ 0; fade 1 → 0 over 132 samples (length rint(sr·0.001·3) from prepareToPlay 0x119bd8 @0x11a1e8; critic re-derived it
  statically, the harness passes 132), then zeros. So an Off/disabled Send FX leaks no dry signal.
- No dry path outside the effect: the return is whatever the selected effect's EffectBase slot 18 leaves in the send buffer (its own Mixratio law).

**F105 — Send/Master FX-mode switch (mechanism).** `confirmed` statically (critic); audible effect on Master `likely`
- CompositeFxUnit +0x1f8 FX mode (prj::RoutingData+0x2c, strings "EffectModeSend" = 0 / "EffectModeMaster" = 1; task 0x1a9c54, routing handlers
  0x1aa060/0x1aa240) → 0x1a9888 indexes tables 0x861840 = [1,0,0] and 0x861844 = [0,1,0] and calls Send/Master parameter manager slot 9 0x11cafc
  (flag ^ 1) → FxProcessorBase 0x112a08 (stores +0x9e; on disable calls the current effect's slot 6 (1.0) fade-out). Mode Send: Send on, Master off;
  Master: the reverse; mode > 1: both off. `likely` (not emulated): a disabled MasterFxProcessor (0x112acc has no mute) passes the main bus dry.
- SendFxParameterManager slot 32 0x12bc84 names the same 10 types as Master plus "Off" (`likely`: any of the 10 can be the Send FX; index mapping → H020).

**F106 — MasterOutUnit: the return is summed after the Master FX; no limiter.** `confirmed` (real 0x1b2150 + SimpleTwoMixUnit + VolumeFader emulated)
- MasterOutUnit::processBlock 0x1b2150 (6 in / 4 out): SimpleTwoMixUnit(6, normalise 0) +0x80 → out0 = in0 + in2 + in4, out1 = in1 + in3 + in5 at
  gain 1.0 (NEON adds, order ch0+ch2+ch4) — i.e. Master FX output + Send return + MTU out14/15 → **master VolumeFader** +0x84 (F096 table, 100-sample
  ramp; bound by VolumeProxy @0x1be8d4 to ProjectManager+0x1bc) → PeakDetectorUnit +0x88 → AudioRenderer +0x90 (read-only tap, `likely`) → out2/3 :=
  copy of out0/1 (headphone feed). DC check on indices 0/10/50/100/112/127.
- The full order is therefore: tracks → MTU main sum → Master FX ‖ MTU send sum → Send FX → return fader; then **main + return + MTU14/15 → master
  fader**. H010's "returned before Master FX and the Limiter" is refuted: the return is added after the Master FX, and no stage on the CPU master
  path limits or clips (Output12Router = selector crossfade; DaveSmithDriveUnit = gain + ClipMeter vt 0x83c0c8 whose processBlock 0xe4d90 only
  reads levels; AudioDeviceOutputUnit = volume/attenuator/mute). The float→int conversion in the ALSA path was not checked.

**F107 — DSF drive gain.** `confirmed` (real DSFDrive slot 13 0xe85e8, 7 indices)
- DaveSmithDriveUnit 0xc3ce8: DSFDrive (+0x88, Volume subclass vt 0x83d310) gain = 1 + 3·(i/1023)², i 0…1023 (0 to +12.04 dB; ctor 0 → 1.0;
  bypass byte +0x94 → 1.0), 100-sample ramp, then clip meter (+0x8c). Used for dsfDriveMaster (selector output → deviceOut 0/1) and dsfDriveSend
  (MTU out4/5 → deviceOut 10/11).

**F108 — Bus model and object layouts.** `confirmed` (model) / layout fields as exercised or asserted
- `tools/fx/bus_mix.py` (own code; reuses `track_mix.py`) is bit-exact to the emulated chain CompositeFxUnit → real SendFxUnit → real
  MasterOutUnit: 7 settings × {impulse, sine, noise, steps} × 60 blocks × 64 frames with mid-run return/master fader changes = 860,160
  channel-samples, 0 differ. Stand-in boundary: the Master/Send FX processors are Python callables; meters/renderer are logging fakes.
  (The worker's C7 mutants are model-vs-mutant only; the placement proof is F102 + F103 + F106.)
- Layouts: CompositeFxUnit (new 0x200, vt 0x861854): +0x8c MasterFxUnit, +0x90 SendFxUnit, +0x94 pool or 0, +0x98 RoutingData, +0x9c/+0xa0 jobs,
  +0xa4 Master view, +0x13c Send view, +0x1d4/+0x1e0 MIDI, +0x1f8 FX mode. SendFxUnit (vt 0x862e28): +0x80 meter, +0x84 LevelMeterSource, +0x88
  SendFxParameterManager, +0x8c SendFxProcessor, +0x90 return VolumeFader (getter 0x1b3574). MasterFxUnit (vt 0x862978): +0x80 manager, +0x84
  processor (processBlock 0x1b1b80 = processor only). MasterOutUnit (new 0x130): +0x80 SimpleTwoMixUnit(6), +0x84 VolumeFader (getter 0x1b2600),
  +0x88 PeakDetector, +0x8c LevelMeterSource, +0x90 AudioRenderer, +0x94 view. VolumeProxy (ctor 0xe78ac(target, int* src)): +0x14 target, +0x18
  source; ctor calls target slot 2 with *src. Return fader bound to ProjectManager+0x1c4 (sys+0x554), master fader to PM+0x1bc (sys+0x558),
  headphone VolumeKnob to PM+0x1c0 (`likely` roles of the PM fields).

## Cycle 020 — H055 device output stage (critic-confirmed)

Evidence for F109–F114: kb/cycles/020.md (Worker + Critic), `harness/H055_device_out.py`, `tools/fx/device_out.py`.
Re-run: `python -B harness/H055_device_out.py --out <dir>` → `RESULT: 0 failed checks` (8 PASS); `h055_report.txt` 4863e9d3…8cfbf0f (corrected in cycle 021; was mis-typed …cbf0f),
`h055.json` e1b2d811…57921, sorted 9-file f32 29998cdd…18c1b (worker runs e/f and critic re-run identical); `--regress` → H010, H009, H021…H041
reproduced (`h055_regress.txt` 711de066…dcac). Emulation boundary: real 1.60 code except the JUCE AudioProcessor ctor 0x5f9e00 and
setPlayConfigDetails 0x5f9e90 (recording stubs; touch only base fields below +0x80).

**F109 — AudioDeviceOutputUnit is the last stage of every output.** `confirmed` (real ctor 0x1ae7dc + processBlock 0x1ae3e4 emulated)
- 7 stereo pairs, 14 in / 14 out, in place. processBlock: for each pair p, a 2-channel view (0x576afc) of ch 2p/2p+1 → OutputVolume[p]
  (sub-object +8, slot 5 0xe9b68 → Volume::processBlock 0xe9b70) → FixedAttenuator[p] (0xe87f8); then BulkMuteUnit (0x1aec8c) on all 14
  channels. No channel crosses, no pair skips a stage (both counts 7).
- No clip, limiter or integer conversion in the unit's code (no ssat/usat/vmax/vmin; only s32→f32 vcvt for counts); emulated output reached
  1.70 unclipped. Floats go on to the JUCE ALSA device (float→int there unchecked, H015).
- Base graph 0x1b6284 (symwalk; critic spot-checked node identities): audioIn (0,1)/(2,3) → deviceInput (0,1)/(2,3); resamplePlayer (0,1) →
  deviceInput (4,5); deviceOut (0,1)…(10,11) → JUCE audioOutputProcessorNode (0,1)…(10,11) @0x1b69e4…0x1b6b4c; **deviceOut (12,13) →
  digitalResampleRecorder (0,1) @0x1b6b7c**; graph config 4 in / 12 out. With F102: device ch 0/1 = master (dsfDriveMaster), 2–7 = MTU 8–13
  (assignable), 8/9 = headphones, 10/11 = DSF send; pair 6 = internal master copy to the resample recorder.

**F110 — OutputVolume law.** `confirmed` (real slot 13 on all 1024 indices; processBlock DC + step)
- OutputVolume = Volume(1023, 100) (0xe993c → 0xe9d28), vt 0x83d658, table pointer +0x94 = 0x83d750 (1024 × u16, 0…32767, monotonic).
  Gain = float(t[i]) × float(1/32767) (literal 0x38000100). t[0] = 0 (mute), t[1] = 206 (−44.03 dB), 100 → −32.38 dB, 256 → −24.39, 512 → −14.22,
  768 → −6.77, 900 → −2.52, 1000 → −0.19, 0 dB from 1008 to 1023.
- Hand-drawn piecewise-linear taper in 16-index groups (steps at 16k+10/16k+11 are real); not dB-linear, no power law (p = 2/3/4 miss by
  2,438–5,388 codes). `device_out.py` reads the table from the target at run time (hash-checked; no firmware bytes in the repo).
- Change: linear ramp over exactly 100 samples from the parameter's sample offset (same GainSmoother as F096); an offset > 64 holds across the
  block boundary.
- Volume base (shared by every Volume subclass): slot 2 0xe86e0 writes only the index (+0x8c); slot 3 0xe86f0 writes index and offset (+0x90);
  processBlock never clears +0x90 (ctor zeroes it). So a slot-2 change after a slot-3 change with offset ≠ 0 reuses the old offset (emulated).
  Irrelevant for OutputVolume (its only writer uses slot 2); `bus_mix.Fader`/`track_mix` reset the offset per block and would differ only for a
  writer mixing slot 3 (offset ≠ 0) and slot 2 (→ H060).

**F111 — FixedAttenuator: compiled-in −0.5 on the 12 DAC channels.** `confirmed`
- Gain is a constant from code, not config or calibration: 0x5712cc builds a 24-word struct (product: word 17 = 2.0f @0x57147c, words 18–23 =
  0.5f @0x571414…0x571430; factory test build TestModeAudioSystem 0x53cf54: 1.0f), passed to HexaTrackAudioSystem 0x1c2cac → AudioSystemBase ctor
  0x1b8198 memcpy(sys+0x204, cfg, 0x60) @0x1b81c4–0x1b81e0 (so sys+0x248 = 2.0, sys+0x24c…0x260 = 0.5). 0x1b6284 passes these floats (pair 6
  reuses +0x24c) and flag bytes 1,1,1,1,1,1,0 (@0x1b676c…0x1b6798); the ctor flips the sign (`eor #0x80000000` @0x1ae91c) for flagged pairs.
- Emulated gain: **−0.5 on pairs 0–5 (device ch 0–11), +0.5 on pair 6** (resample feed). FixedAttenuator (vt 0x83d428) has no setter.
- `guess`: the −6 dB / inverted polarity is undone by inverting analog output stages; word 17 (2.0f) goes to DeviceInputUnit ctor 0x1ade60 (+0x44)
  — a ×2 input gain is `guess` (→ H059).

**F112 — BulkMuteUnit: 64-sample linear mute of all outputs, triggered by the renderer-mode switch.** `confirmed` (law emulated; triggers static)
- BulkMuteUnit(7, 64) (ctor 0x1af1b0, vt 0x8622e0): one MuteSmoother (0xe7fd8, len 64) per pair. Mute 0x1aeee4 (target +0x8d = 1, +0x90 = 2) /
  unmute 0x1aef3c (target 0, +0x90 = 0). processBlock 0x1aec8c: settled muted → clear (silence); settled unmuted → nothing; otherwise run the
  smoothers and adopt the target only when all reach the +0x90 state, then notify listeners.
- Mute g = 1 − k/64 (k = 0…63) then 0; unmute g = k/64 then 1. Built muted, but the AudioDeviceOutputUnit ctor unmutes it, so the first block
  adopts "unmuted" with **no fade** (start-up state: unmuted). Reversal before adoption: unmute during a mute fade jumps back to full level; the
  next mute resumes from the stale gain; a mute during an unmute fade cuts at once (emulated, model matches).
- Callers (all accounted for): mute ← only HexaTrackAudioSystem::muteAllOutput 0x1c10f4; unmute ← AudioDeviceOutputUnit ctor and 0x1c126c.
  0x1c10f4 (direct on the audio thread, else posts Task vt 0x863c7c run 0x1c1290) ← HexaTrackAudioSystem::processBlock 0x1c12a0 state machine on
  sys+0x564: state 4 → unmute @0x1c132c, state-6 path → mute @0x1c178c. sys+0x564 = 6 from switchToRendererMode (slot 108 0x1ba784 @0x1ba7ec),
  = 1 from switchToSamplerMode (slot 107 0x1ba964). Meaning "outputs fade out for the offline renderer (bounce/export)" is `likely`; the
  intermediate states are not traced (→ H061).

**F113 — What drives OutputVolume: OutputVolumeController on one panel pot.** `confirmed` (code read by both, emulated with real objects)
- getVolume(type) = HexaTrackAudioSystem slot 87 0x1b93f0 (IAudioSystem slot 41 thunk 0x1b93e8): types 0–5 → OutputVolume pairs 0, 1, 2, 3, 4, 6
  (thunks 0x1b9430…0x1b946c → 0x1ae614); pair 5 (DSF send) has no getter and is never changed (stays 1023 = 0 dB); types 6/7/8 → master-fader,
  return-fader, headphone-knob VolumeProxies (sys+0x5bc/+0x5b8/+0x5c0).
- 0x1ae614 is reached only from those thunks; a whole-.text scan for [rX,#0x3b8] finds no other path to an OutputVolume pointer. The only
  getVolume(0…5) user is **OutputVolumeController** (vt 0x866158, ctor 0x1d1308, built once in 0x1e6aa8 @0x1e6c08). It registers on
  UIInputManager (singleton 0xf6e380) for **UIVolume id 1** (0x556204, `mov r1,#1` @0x1d13c0); listener 0x1d12d4 → apply 0x1d1210 via slot 2 only:
  v == 0 → OutputVolume [0], [1…4], [6] = 0; v > 0 → [0] = [6] = 1023, [1…4] = v.
- So the one pot sets the level of the three assignable output pairs and the headphones together; it only gates the main out and the resample
  feed (mute at 0, otherwise full). H055's "MASTER and PHONES pots drive OutputVolume[0]/[4]" is **refuted**. "masterVolume"/"headphoneVolume"
  are project fields for the 128-step faders (F106/F108), not OutputVolume; no MIDI path to OutputVolume found (`likely` absent).
- UIVolume (vt 0x931780): exactly three, ids 0, 1, 2, made in 0x559d8c (init 0x55eea8), range 0…1023 (10-bit pots), 4-tap moving average.
  update 0x55ef10 clamps to [+0xe, +0x10] and, when byte +5 is set (ids 0 and 1, not 2), maps through a u16 curve at 0x9317a8: near-identity with
  dead zones (raw 0–3 → 0, raw 1020–1023 → 1023), so the main-out mute engages over the bottom 4 raw codes (critic, static). Value at +0x12.
- Other UIVolume listeners: DaveSmithController (vt 0x865c58, ids 0 and 2), plus five registered on all three (EncoderTestPage factory test
  0x54960c, power-manager observer 0x56433c, IUIAutoStandbyController 0x564f60…, unnamed 0x566930 / 0x566f24); none reaches OutputVolume.
- Which physical knob is UIVolume id 1 (MASTER or PHONES) is `guess` (needs a unit check, not done).

**F114 — Device-output object layouts and model.** `confirmed` (fields read in code or exercised); model bit-exact
- AudioDeviceOutputUnit (new 0x170, vt 0x8621f8; object at **sys+0x3b8** @0x1b67f4, graph node sys+0x3c0): +0x80 pair count; +0x84…+0x9c
  attenuator floats; +0xa0…+0xa7 sign flags; +0xa8 channel count; +0xac/+0xb0/+0xb4 OutputVolume* array; +0xc4/+0xc8/+0xcc FixedAttenuator* array;
  +0xd0 BulkMuteUnit*; +0xd4 view. Getters 0x1ae614 (OutputVolume by pair), 0x1ae62c (BulkMuteUnit). DeviceInputUnit object at **sys+0x3b4**
  (@0x1b6878; node sys+0x3bc).
- Volume/OutputVolume (0x98; vt 0x83d658, +8 sub-vt 0x83d698): +0x88 GainSmoother*, +0x8c index, +0x90 offset (persists), +0x94 u16 table. Slots:
  2 set index 0xe86e0, 3 set index+offset 0xe86f0, 4 get 0xe86e8, 5 range {0,1024}, 6 = 1023 0xe9990, 8 gain 0xe870c, 11 processBlock 0xe9b70,
  13 table gain 0xe9914. FixedAttenuator (0x88): +0x80 signed gain. BulkMuteUnit (0xb0): +0x80 pairs, +0x84 channels, +0x88 len 64, +0x8c current,
  +0x8d target, +0x90 wanted smoother state, +0x94… MuteSmoother* array, +0xa0/+0xa8 listeners. OutputVolumeController (0x2c): +4 IAudioSystem*,
  +8 UIInputManager*, +0xc/+0x10 restore 1023, +0x14…+0x28 OutputVolume* pairs 0,1,2,3,4,6. UIVolume (0x28): +4, +5 curve flag, +8 id, +0xe/+0x10
  clamp, +0x12 value, +0x14, +0x18 filter, +0x1c… listeners; slot 5 addListener 0x55ed64, slot 6 removeListener 0x55ec2c.
- AudioSystemBase config sys+0x204 (0x60 bytes): +0x204/+0x208 graph in/out (4/12), +0x248 2.0f, +0x24c…+0x260 0.5f (product).
- `tools/fx/device_out.py` (own code; reuses `track_mix`): bit-exact to the emulated unit on 7 settings × {impulse, sine, noise, steps} ×
  60 blocks × 64 frames × 14 ch = 1,505,280 channel-samples + 8,960 denormal (NEON flush matched), 0 differ; critic fuzz (random cfg/flags,
  slot 2/3 mid-ramp, mute/unmute reversals) 286,720 channel-samples, 0 differ.

## Cycle 021 — H043 SendFxDelay end-to-end (Send index 0 / Master "Delay" index 0; critic-confirmed)

Evidence for F115–F120: kb/cycles/021.md (Worker + Critic), `harness/H043_send_delay_model.py`, `tools/fx/send_delay.py`.
Re-run: `python -B harness/H043_send_delay_model.py --jobs 7 --out <dir>` → `RESULT: 0 failed checks` (31 PASS, ≈ 2.5 min);
`h043_report.txt` 29227f2c…4b8b, `h043.json` 0f8fe70a…8ba1, 92 sorted f32 b6b3f9b5…53a6f (worker runs b/c/d and critic re-run byte-identical);
`--regress` → H055, H010, H009, H021…H041 reproduced (`h043_regress.txt` 0962b163…7c29). Critic extra: own fuzz (14 seeds × 3000 blocks =
5,376,000 samples, random mid-run writes to all indices with v in [−1, 3], resets, BPM walks, NaN/overflow, denormals, Master defaults), random
block lengths 1…64, 0xA5-filled heap: all bit-exact. Emulation boundary: real 1.60 code and libm; stubs memcpy/memset/new only; the
assert/log 0x4f782c in the sync-table reader's out-of-range branch is skipped (statically falls to `mov r0,#6` @0x34a4b8).

**F115 — SendFxDelay parameters, defaults and tempo feed.** `confirmed` (emulated ctor 0x1054ac(obj, 44100, 64) + slot-14 map + slot 52; decompile 0x104e98)
- Slot 14 = EffectBase 0x105d24 (store only); 8 Parameters at +0x3f0 + 0x5c·i: 0 DelayTime (0…1, ctor 0.5), 1 Feedback (0), 2 HiCut (1.0),
  3 LowCut (0), 4 Spread (0), 5 Mixratio (0), 6 SYNC (ToggleParameter +0x618; only v ≤ 0 or v ≥ 1 accepted, else return 3), 7 BPM (1…999, ctor
  120); index ≥ 8 → 3. Nothing applies immediately: all take effect in the next slot 25 (0x104e90 → 0x104e98).
- F026-style change detection only on SYNC, BPM and DelayTime (dirty byte +0x6b8); Feedback, HiCut, LowCut, Spread, Mixratio re-read every
  block. A DelayTime write equal to the ctor value 0.5 before the first block is never applied (lines stay at the base ctor 1.0 ms = 44 samples).
- Unlike InsertFxDelay (F075), **LowCut and Spread are live** (every index 0…5 and 7 changes DSP state).
- The base DelayEchoBase also registers DelayTimeLch +0x2c / DelayTimeRch +0x88 (1…4000 ms, ctor 1.0) and FeedbackGainLch +0xe4 / Rch +0x140
  (0…1, ctor 0); slot 14 cannot reach them (F117).
- Slot-52 case 0 (Send 0x11a3a8, Master 0x113438): DelayTime 0.122807 (= (500−10)/3990 → 500 ms), Feedback 0.7, HiCut 1.0, LowCut 0, Spread 0,
  SYNC 0; **Mixratio Send 1.0 (wet only; spec getter @0x11a584, emulated) vs Master 0.5 (literal @0x113610; dry 1, wet 0.667)** — the only difference.
- Tempo: Send (jump table 0x119a40) and Master (0x112b4c) processBlocks send indices {0, 2, 3, 9} to a feed block that writes slot 14 index 7 =
  tempo clamped to 1…999 (literals 0x119bd4 / 0x112cb8 = 999.0) every block before slot 18 (800/800 feeds emulated in both).

**F116 — SendFxDelay parameter formulas.** `confirmed` (9 emulated read-back sweeps, full state compared, 0 mismatches; critic static re-check)
- Free time: ms = rint_even(10 + 3990·v) (range spec 0x34a428 = (10, 4001)) → 10…4000 ms, 1 ms steps; setDelay clamps > 4000; samples =
  trunc(F(ms·0.001f)·fs) (500 ms → 22050, 4000 → 176400); the **same** value to both lines.
- Sync: i = rint(7v) (spec 0x34a478 = (0, 8)) → 1/8, 1/4, 1/2, 3/4, 1, 2, 4, 8 beats (`.bss` 0xf61f94, `.init_array` 0x6cb20); i outside 0…7
  → index 6 = 4 beats; ms = F(F(F(num/den)·1000)·60)/BPM clamped to [10, 4000] in 0x104e98.
- Feedback: g = v, **unquantised and unclamped** (1.2 stays 1.2), same on L and R, via 147-sample linear SmoothFloat ramps (+0x1a4/+0x1c8)
  (Insert rounds to 0.01, F076).
- Spread: direct target F(1 − v), cross target v (147-sample ramps +0x1ec/+0x210).
- HiCut: step = trunc(999v) + 1 (1…1000), fc = 2000·10^((step−1)/999) Hz (2–20 kHz), IirLpf1stOrder (vt 0x840dd8), 1 step per 1/3 ms glide.
- LowCut: x = 1 − v, step = trunc(999·(1 − x⁴)) + 1, fc = 1000^((step−1)/999) Hz (1–1000 Hz; v 0.25 → 111.7 Hz, 0.5 → 646.9 Hz), IirHpf1stOrder
  (vt 0x840db8); coefficients use fc floored at 5 Hz (5.0f at 0x83bc40), so v ≤ ≈ 0.0645 (step ≤ 233) all sound identical.
- Mixratio: v < 0.75 → dry 1, wet F(v·1.3333334); else wet 1, dry 1 − 4(v − 0.75) (InsertFxDelay law, F076); slot 13 0x1049e8 copies +0x6a4/+0x6a8
  to EffectBase +0x10/+0x14. The slot-18 sum itself was not measured for this class (shared EffectBase 0x106de4).

**F117 — SendFxDelay signal flow (refines F080).** `confirmed` (decompile 0x104a30 + bit-exact emulation + 8 rejected mutants)
- Two **mono** DelayModules (vt 0x840028, ctor 0xec0fc from DelayEchoBase ctor 0x104408), stereo input (L → left line, R → right line). Per chunk
  (length from the left module 0xec494): yL, yR = integer-sample reads; Spread matrix L' = d·yL + x·yR, R' = d·yR + x·yL (0xf5b9c ×2, 0x578a6c ×2);
  then HiCut LPF (+0x69c), then LowCut HPF (+0x6a0), both 0xf438c; **output = (L', R') wet only**; lines written with inL + fbL·L', inR + fbR·R'.
  So the cross-feed is the Spread matrix, before the output and before the feedback tap, and feedback is taken after both filters. Spread 1 =
  ping-pong (L impulse, 300 ms: first on R at +13,230 samples, then on L). With a static Spread the matrix and the filters commute; the order shows
  only in rounding and during Spread ramps.
- **Separate L/R times refuted on the parameter path:** every Param_set of DelayTimeLch (+0x2c) in 0x104e98 (0x1050f8, 0x10515c, 0x1051e4) is
  followed by one of DelayTimeRch (+0x88) with the same callee-saved s16; no other direct writer in 0x103e00…0x105800; the only other setDelay
  caller 0x103d64 is DelayEchoBase slot 8, overridden by 0x104ce4. The class itself handles unequal L/R times (emulated by direct writes); a
  generic by-name parameter access was not excluded (`guess`, no such caller known).
- Ring = trunc(4000·0.001·fs) + 2500 = **178,900 frames per line** (stereo-interleaved RingBuffer, lane 0 used); integer read (fraction always 0).
- A delay change does not glide: both gates fade out over 147 samples, both read pointers jump (D_L = D_R), gates fade in; ring not cleared.

**F118 — SendFxDelay object layout and vtables.** `confirmed` (64 fields compared after every block of every run) / roles as marked
- SendFxDelay (new 0x6c0; primary vt 0x841ea8, secondary 0x841eec at +0x238): +4 block, +8 scratch count 7, +0xc scratch, +0x10 fs, +0x18 1/fs
  (slot 23 0x1052c0); base Parameters +0x2c/+0x88/+0xe4/+0x140 (writer 0x104e98, reader 0x104ce4); +0x19c/+0x1a0 DelayModule L/R; SmoothFloats
  +0x1a4 fbL, +0x1c8 fbR, +0x1ec direct, +0x210 cross (target +0xc); +0x238 EffectBase; +0x3f0…+0x69b the 8 Parameters; +0x69c HiCut / +0x6a0 LowCut
  SteppedIirFilter containers (new 0x48, ctor 0xf3ce4: 2000/20000/1000 and 1/1000/1000); +0x6a4 dry, +0x6a8 wet, +0x6ac SYNC copy, +0x6b0 BPM copy,
  +0x6b4 time copy, +0x6b8 dirty.
- DelayModule (mono): same layout as DelayModuleStereo (F077): +0x20 ms, +0x24 D, +0x28…+0x30 pending, +0x34 SignalGate N 147, +0x7c/+0x7d/+0x80
  warm/full/counter, +0x84 maxms 4000, +0x88 interp flag 1. Routines: ctor 0xec0fc, setDelay 0xec384, reset 0xec314, nextChunk 0xec494, read
  0xec4bc, write 0xec6d4.
- Primary vt 0x841ea8: 0/1 dtors, 5 process 0x104a30, 8 apply base params 0x104ce4, 9 0x104e6c (sets DelayTime +0x3f0; role `guess`), 10 reset
  0x104a04 (slot 8 + slot 4), 11 set fs 0x1052c0 (`likely`), 12 0x105228 (`likely` block size), 13 copy mix 0x1049e8, 14 update + process
  0x104e98; slots 2, 3, 4 (0x104108 line reset), 6, 7 inherited from DelayEchoBase 0x841de0 (roles of 2/3/6/7 open). Secondary 0x841eec: EffectBase
  0/1 dtors, 11 → 0x104e6c, 23 → 0x1052c0, 24 → 0x105228, 25 → 0x104e98, 26 → 0x1049e8, 27 → 0x104a04; slot 10 = EffectBase default (return 2),
  slot 18 = shared 0x106de4.

**F119 — SendFxDelay start-up, reset and edge cases.** `confirmed` (emulated at slot-25 level) unless marked
- Warm-up gate as F079: with Send defaults an impulse at t = 0 never echoes; at t = 192 it echoes at 22,242.
- Slot 27 0x1049fc → 0x104a04 = slot 8 (0x104ce4) + 0x104108 (slot 8 again, 0xec314 on both modules, all four SmoothFloats snapped via 0xf5584):
  rings rewound (write 0, read −D), gates closed, counters zeroed, **ring samples and filter states kept**, pending Parameter changes **not**
  consumed. EffectBase slot 5 (e, 0, 0) runs slot 27. Slot 10 (retrigger) does nothing.
- 50 ms first-delay quirk: if the first delay applied after construction equals the module ctor value 50 ms, setDelay is a no-op and the first
  echo comes after the full ring (192 + 178,900 samples ≈ 4.06 s) until the time changes; not a heap artefact (0xA5 test). An activation reset
  before the first block removes it (echo at 192 + 2205), and both processors reset at block 0, so on the device it is `guess` (likely never).
- Out-of-domain (not reachable through the processor, `likely`/as tested): DelayTime v ≤ ≈ −0.00238 → D = 0 → slot 25 never returns; slightly
  negative v gives 1…9 ms; |v| ≳ 5.4e5 → rint wrap → hang. Model limits: BPM 0 (firmware → 4000 ms) and NaN DelayTime raise in the model; NaN BPM
  counts as a change in the model (`chorus.LinParam`) but not in firmware 0xf0ffc.

**F120 — Send vs Master Delay object and the model.** `confirmed`
- Same class, identical construction: 0x114bfc (Master) and 0x11bc28 (Send) both `new(0x6c0)` → 0x1054ac(obj, 44100, 64) → store obj+0x238.
  Defaults differ only in Mixratio (F115). Real Send (0x119994) and Master (0x112acc) processBlocks around a real SendFxDelay (Send mute smoother
  neutralised; 800 noise blocks, sync 1/2 beat, BPM 120 → 90 → 133.37): slot-25 output = model, state equal every block, in both.
- One static difference: activation calls EffectBase slot 5 with (e, 0, 0) on Send (@0x119b28) and (e, 0, 1) on Master (@0x112c1c); with 1,
  0x10623c skips the reset if EffectBase byte +0xa8 ≠ 0. No observed effect (+0xa8 = 0 at block 0 in both); meaning of +0xa8 open (`likely` harmless).
- `tools/fx/send_delay.py` (own code; reuses `insert_delay`/`chorus` blocks): bit-exact to emulated slot 25 in 92 runs (12 settings × 6
  signals incl. 4000 ms fb 1.0 over 5800 blocks, ping-pong, sync at 87.5/120/133.37/999 BPM, fb 1.2, plus 5 mid-run-change runs × 4 signals), 16,384,000
  samples, max error 0, state and rings equal; no error source (NEON flush-to-zero adds and correctly rounded tan/pow reproduced).

## Cycle 022 — H005 SendFxReverb end-to-end (Send index 1 / Master "Reverb" index 1; critic-confirmed)

Evidence for F121–F127: kb/cycles/022.md (Worker + Critic), `harness/H005_send_reverb_model.py`, `tools/fx/send_reverb.py`.
Re-run: `python -B harness/H005_send_reverb_model.py --jobs 7 --out <dir>` → `RESULT: 0 failed checks` (24 PASS, ≈ 3 min);
`h005_report.txt` 099e46ae…c53f, `h005.json` a6c1e847…f304, 66 sorted f32 9d751574…91fa (worker run_a/run_b and critic re-run identical);
`--regress` → H043 full run + H043 `--regress` (H055, H010, H009, H021…H041) all recorded hashes reproduced. Critic extra: own fuzz (21 seeds,
≈ 3.2 M samples, Send and Master defaults, ≈ 4,300 random parameter changes incl. boundary values, resets, loud/denormal/DC input): bit-exact,
state and all 14 rings equal. Emulation boundary: real 1.60 code and libm; stubs memcpy/memset/new only; powf modelled with `fdlibm_powf`;
the clamp+log 0x11031c was never triggered (in-range values only).

**F121 — SendFxReverb is not juce::Reverb / Freeverb (H005 refuted).** `confirmed`
- No Freeverb tuning arrays in the file (int16/int32 1116…1617 / 556…225: 0 hits); the tunings appear only as movw immediates in JUCE library
  code FUN_00585680 (0x585690…0x585c14), which is `likely` juce::Reverb::setSampleRate. Its caller 0x5755ec is slot 2 of vt 0x933118
  (typeinfo 0x93398c `N4juce17ReverbAudioSourceE`, confirmed); its other caller 0x582cbc has no callers and no vt reference (owner `guess`).
- None of the reverb vtables or direct-call targets of the reverb code 0x10e2e0…0x112680 lies in 0x582c00…0x586100; no 0.015f/0.28f in that
  range. `juce::Reverb` has no RTTI; only ReverbAudioSource does. Freeverb IR vs real IR: correlation −0.015, first arrival 1116 vs 952 samples.

**F122 — Reverb9NXS signal flow.** `confirmed` (static + bit-exact state equality over ~100 fields every block)
- Slot 25 0x111730 → own slot 32 0x1120c4 (mix, slot 26, room, LPF step) → Reverb9NXSBase (R9, sub-object +0x1b8) slot 18 0x10e2e0: room
  re-target (slot 7 0x10e540), slot 17 = SFR slot 33 0x11185c (comb coefficients) every block, chunk loop slot 8 0x10e34c (chunks end where the
  room takes a step; slot 6 0x10e4d8 steps the room).
- Per chunk (R9 slot 9 0x10e418), in place on L/R, **true stereo** (no mono sum), no modulation/LFO:
  PreDelay (SFR slot 34 0x1117f0 → 0x11138c; write first, then read at (w+1)−D, linear interpolation) → ×inGain (slot 11 0x10fcf4) →
  IirLpf1stOrder 14 kHz → IirHpf1stOrder 80 Hz → **5 parallel stereo combs** (slot 12 0x10e924, 0x110b88 each, all fed the same (L, R),
  outputs summed with NEON FTZ add 0x578a6c) → **2 series stereo allpasses** (slot 13 0x10fd28, 0x1100d0; y = ring[w−D] − g·x,
  ring[w] = x + g·y, g 0.7, fixed truncated delays 6.979|8.240 ms and 22.740|21.479 ms = 307|363 and 1002|947 samples at 44.1 kHz).
- Comb 0x110b88 per sample: D glides as a double; idx = trunc(w − D) (**integer read, no interpolation**); y = g·ring[idx]; **output tap = y
  before the damping filter**; feedback through the damping LPF (inside the loop) and an L/R matrix:
  ringL[w] = in + a·fL + b·fR, ringR[w] = in + b·fL + a·fR.
- Comb delays = s × {22.09375|38.666668, 39.916668|23.229168, 23.854168|40.864582, 41.5|24.802082, 21.5|23.885418} ms (L|R; table 0x842408),
  s = 0.2 + 0.171·(1.01 + 0.02306·room)². Room 50: 974/1705, 1760/1024, 1052/1802, 1830/1093, 948/1053 samples; room 1: 362…700;
  room 100: 1972…3807. All ring lengths 4454 samples (101 ms at 44.1 kHz; scale with fs).
- Output gain: SFR slot 26 0x11169c writes EffectBase wet = wet × 0.70795 (R9 +0x84, −3 dB, set by R9 init slot 16 0x10eae0); before activation
  it is 0. How the shared EffectBase slot-18 sum uses it for this class was not measured separately.

**F123 — SendFxReverb parameters, defaults and feeds.** `confirmed`
- 6 LinearParameters (0…1) at +0x244 + 0x5c·i, registered by ctor 0x1123d0: 0 PRE DELAY (0.5), 1 ROOM SIZE (0.5), 2 REVERB TIME (0),
  3 COMB FILTER LPF (0), 4 LR SWAP SPREAD (0), 5 MIX RATIO (0).
- Slot 14 = EffectBase 0x105d24: accepts 0…5 (6, 7, 12, 0xffffffff return 3); **stores only — everything takes effect at the next slot 25**;
  no F026-style change detection (effective changes filtered by integer room compare +0x60 vs +0x64 and the comb setters' equality tests).
- Slot-52 defaults for index 1 (Send 0x11baa8 → case 0x11a860; Master 0x114ad4): PRE DELAY 0, ROOM 49/99 (→ room 50), REVERB TIME 49/99,
  LPF 0, SPREAD 0, **MIX Send 1.0 / Master 0.5**.
- No per-block feed: jump tables Send 0x119a40 / Master 0x112b4c route index 1 to 0x119aac / 0x112bc8; tempo feed covers only {0, 2, 3, 9};
  real processBlock rigs logged 0 tempo calls and 0 slot-14 feeds in 300 blocks.

**F124 — SendFxReverb formulas.** `confirmed` (59 sweep steps with full state equal, 56 direct calls of slot 33 over REVERB TIME × room,
140 calls of glide-time 0x111780; constants re-read statically by the critic)
- PRE DELAY: ms = 100·v clamped to [0.1, 100]; samples = fs·ms/1000; a change glides linearly over 44,100 samples (1 s), interpolated read.
- ROOM SIZE: roomSet = trunc(1 + 99v) (1…100); the current room steps ±1 per chunk of t ms, t = 40 − ⅔·|Δ| (floor 20) with ⅔ ms slew of the
  previous t; each step re-targets the comb delays, which glide over t ms (truncated read → zipper/pitch artefacts during a glide).
- REVERB TIME: x = 1 + 99v; T60 = 1.740863 − 0.2255314x + 0.016808311x² − 3.3391331e-4x³ + 2.872803e-6x⁴ s (table 0x8425f8); for v ≤ 0.09,
  T = 0.1 + 10·v·T. Examples: v 0 → 0.1 s, 0.09 → 0.873, 0.0901 → 0.860 (dip at the blend edge), 0.3 → 3.55, 49/99 → 8.70, 1 → 100.6 s.
  Comb gain g = 10^(−3·d_ms/(1000·T)) (fdlibm powf). Input gain: 0.2 for 0 ≤ v ≤ 0.5137255, then 0.2 − 0.1·2.0564518·(v − 0.5137255)
  (0.1 at v = 1); 0 for v < 0 or v > 1.
- COMB FILTER LPF: step = trunc_u32(1 + 99(1 − v)) (v 0 → 100, ≥ 0.99 → 1); damping cut-off 2000·9^((step−1)/99) Hz (2…18 kHz; 18 kHz = fmax at
  44.1 kHz); one-pole LPF per comb, gliding one step per ⅓ ms (stepped container 0xf3ce4/0xf41ac/0xf438c).
- LR SWAP SPREAD s, per comb (a straight, b swapped; 132-sample ramps): s < 0.2: c1 (1−5s, 0), c2–c4 (1, 0), c5 (0, 5s); then in each 0.2 band
  one comb fades its straight gain out while the previous one fades its swapped gain in (table in kb/cycles/022.md C3). **At SPREAD 0 comb 5 has
  a = b = 0 (no feedback, a pure delay tap)**, and no L↔R leak exists (L-only input → R exactly 0).
- MIX RATIO: same law as SendFxDelay: v < 0.75 → dry 1, wet 4v/3; else wet 1, dry 1 − 4(v − 0.75); wet then × 0.70795 (F122).
- Ramp quirk (critic): a comb's spread/gain/delay ramps share one counter but keep per-channel increments, so a channel whose target did not
  change keeps its stale increment until the counter expires, then snaps (e.g. c1.a transiently −0.37 in the spread sweep). Reproduced by the model.

**F125 — Reverb object layouts and vtables.** `confirmed` for fields (compared every block) / vtable roles `likely` unless emulated
- SendFxReverb (new 0x478): EffectBase +0…+0x1b7 (dry +0x10, wet +0x14); R9 sub-object +0x1b8; Parameters +0x244…+0x46b; dry +0x46c,
  wet +0x470; ReverbPreDelay* +0x474.
- Reverb9NXSBase (relative): +4 block, +8 scratch count 4, +0xc scratch, +0x10 fs, +0x18 1/fs; +0x1c LPF*, +0x20 HPF*; +0x24…+0x34 comb*[5];
  +0x38…+0x48 damping container*[5]; +0x4c/+0x50 allpass*[2]; +0x54 fs flag; +0x58 fmax; +0x5c room cur, +0x60 set, +0x64 target;
  +0x68/+0x6c range 1/100; +0x70 glide ms; +0x74/+0x78 chunk N / remaining; +0x7c idle; +0x80 inGain; +0x84 outGain 0.70795; +0x88 LPF step.
- ReverbCombFilter (0xc8), ReverbAllPassFilter (0x60), ReverbPreDelay (0x68): field maps in kb/cycles/022.md C4 (rings, write index, warm-up
  count/threshold/fade, delays as doubles, gain/spread ramps).
- SFR primary vt 0x842618 [36]: 23 setSampleRate 0x1116c4, 25 process 0x111730, 26 copy mix 0x11169c, 27 reset 0x11208c (emulated),
  32 updateParams 0x1120c4, 33 calcCombCoefs 0x11185c, 34 preDelay 0x1117f0, 35 glideTime 0x111780. Secondary 0x8426b0 overrides R9 slots
  4/10/15/17 with thunks to SFR 35/34/32/33. R9 vt 0x842380 [19]: 2 setSampleRate 0x10f224, 6 step room, 7 apply room, 8 chunk loop,
  9 chunk, 11 in gain, 12 combs, 13 allpasses, 16 init 0x10eae0, 17 base table-driven coefficients 0x10e5f8 (10 rodata tables
  0x83ec20…0x83fa30 by room; overridden, unused by SendFxReverb), 18 process; slots 3/14/15 `guess`.

**F126 — SendFxReverb start-up, reset and edge cases.** `confirmed` (emulated at slot-25 level) unless marked
- Warm-up gate: comb and allpass **outputs** are gated until count > ring length (4454 samples), then fade in over 3 ms; the first output
  appears at block 69 (≈ 101 ms) after activation whatever the input. Ring **writes are not gated**: an input is lost only if it reaches the
  combs earlier than ≈ 4455 − (longest comb delay) samples after activation (≈ 60 ms at room 50, depends on room and pre-delay); an impulse at
  sample 3000 (68 ms) is heard at almost full level (critic table, cycle 022).
- Without the activation reset the reverb is silent forever (LPF/HPF coefficients, allpass delays/gains and outGain are set only by R9 slot
  16 via slot 27 or slot 23). EffectBase slot 5 (e,0,0) and (e,0,1) both run slot 27 once on a fresh object; both processBlocks reset once at block 0.
- Slot 27 0x11208c = slot 32 + R9 reset 0x10fae0 (init, coefficients, IIR states cleared, combs 0x110940 snapped with w/count/fade 0, damping
  containers 0xf40f8, allpasses 0x11001c, room cur = target, t = 40) + PreDelay reset 0x1112b8. **Rings are not cleared** (clears only in the
  ctors); with PRE DELAY 0 the gate overwrites the comb/allpass rings before opening, so the old tail never resurfaces; with PRE DELAY 100 ms stale
  pre-delay content does reach the combs. Slot 10 (EffectBase default 0x10594c) returns 2 and changes nothing.
- Comb glide time stays at the ctor value 100 ms until the first ROOM change (reset does not touch it), so REVERB TIME gain ramps take 4410
  samples until then, t (20–40 ms) after.
- Parameter changes never clear buffers (ROOM: delay glide; PRE DELAY: 1 s glide; REVERB TIME: gain ramps; LPF: ⅓-ms steps; SPREAD: 3 ms ramps).
- Pre-delay one-past-end read: at PRE DELAY 0.1/0.2/0.3/0.4/0.6/0.8/0.9 the target is just above an integer, and once per ring cycle the read
  position rounds to 4454.0, so 0x11138c (no bounds check) reads the float after its ring at full weight. Emulator and model use 0.0 there;
  with a heap word 0.747 (0x3f fill) the output differs (26,638 samples, max 0.062). Device effect: `guess` (depends on the heap).

**F127 — Send vs Master Reverb object and the model.** `confirmed`
- Same class, identical construction: 0x114c88 (Master) and 0x11bcb4 (Send) `new(0x478)` → 0x1123d0(obj, 44100, 64). Defaults differ only in MIX.
  Real Send and Master processBlocks around a real SendFxReverb (300 noise blocks, ROOM change at 150): slot-25 output = model, state equal
  every block, 1 activation reset, no feeds.
- `tools/fx/send_reverb.py` (own code; numeric constants only; reuses lofi/chorus/insert_delay/send_delay/fdlibm_powf blocks): bit-exact
  to emulated slot 25 in 66 runs (9 settings × 6 signals incl. all-min, all-max, boundary values, 1200-block tail; 3 event runs × 4 signals),
  4,684,800 samples, max error 0, state and rings equal; plus the critic's 3.2 M fuzz samples. Mutants caught: mono-summed input, damping
  outside the loop, interpolated comb read, spread ignored, no delay glide, Freeverb comb lengths, allpass g 0.5, fixed input gain, no warm-up
  gate, integer pre-delay read.

## Cycle 023 — H064 Performance FX / PerformanceFxLoFi (critic-confirmed)

Evidence for all: kb/cycles/023.md (Worker, Critic); `harness/H064_perf_fx.py --out DIR` → `RESULT: 0 failed checks (33 PASS)`
(h064_report.txt ebbd3fde…624d, re-run by the critic with identical hashes); `--regress` → all recorded hashes reproduced; model
`tools/fx/perf_lofi.py`.

**F128 — PerformanceFxLoFi is the only Performance-FX DSP class, and it is never constructed in 1.60.** `confirmed` (static, main binary)
- RTTI closure of EffectBase (critic, own script): 15 descendants; `17PerformanceFxLoFi` (typeinfo 0x841b14, si, base EffectBase) is the only
  `PerformanceFx*` name in the binary. Vtable 0x8419d8, 33 slots: own slots 0/1 (dtors 0xfdef8/0xfe0dc), 23 0xfdbfc and 24 0xfdc04 (both
  `return 0`), 25 0xfc434, 26 0xfac70, 27 0xfb02c, new slot 32 0xfacec; slots 2–22 and 28–31 are the EffectBase entries (same as LoFi).
- Ctor 0xfd1f8(this, fs, block) calls EffectBase ctor 0x1067d8. The value 0xfd1f8/0xfd1f9 occurs nowhere in the file (any alignment, either
  byte order); no bl/b, movw/movt, literal or pc-relative (incl. `add rX, pc, rY`) formation reaches it; REA `xrefs 0xfd1f8` → []. The vtable
  0x8419d8 is materialised only in the ctor and the two dtors (literal uses 0xfd220/0xfdf04/0xfe0e8), so no inlined construction exists.
  No fall-through into the ctor (0xfd1dc ends in `pop {r4, pc}`). Not a dynamic export; in the 1.60 rootfs "PerformanceFx" occurs only in
  EP085_Main_R (the rootfs*.tar.gz archives were not searched inside).
- Insert/Master/Send FX processor ctors 0x118b0c / 0x114bc0 / 0x11bbe4 build LoFi (ctor 0xfd640), never this class. So it has no owner and no
  place in the audio graph; on the device none of its parameters is ever set. Left-over/unused code: `likely`.

**F129 — PerformanceFxLoFi algorithm: a one-knob LoFi built from LoFi's blocks, not the LoFi kernel.** `confirmed` (emulated)
- Slot 25 0xfc434: own param apply 0xfc278 → filter container A (+0x330, LPF) 0xfbb70 → crusher 0xfaf28 (+0x32c; only if bits ≤ 31) → inline
  sample-and-hold (+0x328) → filter container B (+0x334, HPF) 0xfbb70 → vcall slot 26 (every block); returns 0. No call to the LoFi kernel
  0xfbf64, no preamp 0xfb6e4, no position gate 0xf521c, no filter-position switch. Shared with LoFi: LinearParameter (vt 0x840ac8), filter
  container ctor 0xfc5e4 / process 0xfbb70, crusher 0xfaf28.
- Layout (ctor writes up to +0x349; real size unknown, never allocated): +0x1b8/+0x214/+0x270/+0x2cc LinearParameters; +0x328 S&H (new 0x18);
  +0x32c crusher (new 0xc); +0x330/+0x334 filter containers (new 0x44 each; pending type 1 = LPF / 0 = HPF); +0x338 LEVEL, +0x33c REDUCTION,
  +0x340 CUTOFFMAX, +0x344 RESONANCE (ctor 0, 0, 0.5, 0.5); bytes +0x348 S&H-dirty, +0x349 filter-dirty.
- Parameters (slot 14; index ≥ 4 returns 3), all 0…1; 320/320 emulated read-backs match. L = LEVEL, R = REDUCTION, C = CUTOFFMAX, Q = RESONANCE:
  - bits b = 12·(5/12)^(2L) (double pow) for L < 0.5, else 5; int = round(b); scale = powf(2, b)·0.5, inv = 1/scale.
  - S&H hold = max(1, L·44.1·R) samples (44.1 is a constant, not derived from fs: a 48 kHz ctor still matches).
  - LPF fc = 20000·0.015^((1−C)·L); HPF fc = 20·400^(C·L). C splits the single LEVEL sweep between closing the LPF and raising the HPF.
  - q = 0.707107 + 7.2928929·Q; if fc > 2500: q·(20000−fc)/17500 (floor 0.707107); if fc < 700: q·(fc−20)/680 (floor 0.1); stored only on a
    change ≥ FLT_EPSILON; cutoff/Q glide through the LoFi step ramp (F028) in each container.
  - Slot 26 wet w = clamp((L − 4/255)/(33/255), 0, 1); EffectBase +0x14 = w, +0x10 = 1 − w. `guess`: the /255 steps point to an 8-bit
    controller as the intended source.
  - Ctor last-values 0/0.5/0.5/0.5 mean LEVEL 0 or the others at 0.5 set before the first block are never applied (as F026).
- Slot 27 0xfb02c (reset): reloads L/R, clears the S&H hold, sets S&H step and phase = max(1, L·44.1·R), recomputes the crusher, clears both
  containers' current sub-filter history, reloads C/Q, runs slot 32, clears both dirty flags. Slots 5–9/18/22 inherited (= LoFi).
- "Same code as LoFi, different defaults" refuted: different callees; mutant with LoFi's filters-last order differs in 7,673 samples.

**F130 — `tools/fx/perf_lofi.py` is bit-exact to emulated PerformanceFxLoFi slot 25.** `confirmed`
- Worker: 10 settings/event runs × {sine, noise, impulse train, silence, L-only} × 60 blocks × 64 = 50 runs, 384,000 samples, 0 differ, full
  state (~70 fields) equal after every block; heap 0xA5 identical; resets at blocks 10/30/31 match.
- Critic (seeds 4242/99/31337): random per-block changes of all four parameters, edge values of L (0, 1e-7, 4/255±, 37/255, 0.5±1 ulp, 1),
  ±6 input at RESONANCE 1, denormals, block sizes 1…64 with reset, fs 48000 / block 128, heap 0xFF: 0 differing samples, 0 state diffs.
- Limits: the model is undefined for inf/NaN input (Python `math.trunc` raises; the firmware's vcvt saturates); emulated blocks longer than
  the ctor block size fault in the filter (0xfbad0: scratch buffers sized by the ctor block).

**F131 — The FxSelectPopupWidget list has 20 items incl. VINYL BRAKE, TRANS, ROLL, which have no DSP class.** `confirmed` (strings/xrefs);
interpretation `likely`
- Items: (unnamed), CHORUS, FLANGER, PHASER, RING MOD, TREMOLO, AUTO PAN, AUTO WAH, DISTORTION, LO-FI, REVERB, 2 BAND EQ, FILTER, COMPRESSOR,
  LIMITER, DUCKER, VINYL BRAKE (0x8c2b84), TRANS (0x8c2bcc), ROLL (0x8c2c10) ("SELECT FX", icons p6101…p6120); referenced from 0x3bec88 and
  0x3c237c (~10.6 kB each, REA xrefs 0x3c0df4/0x3c44e0, 0x3c1164/0x3c4850).
- RING MOD, TREMOLO, AUTO PAN, AUTO WAH, LIMITER, VINYL BRAKE, TRANS and ROLL have no EffectBase class (F128 closure, F018/F019). `likely`: a
  generic or planned UI list; whether the popup shows them, and whether ROLL/TRANS are realised outside EffectBase (sequencer note repeat,
  ribbon), is open (H066). The touch-strip classes (RibbonController, NoteRepeatModeRibbonController, PitchModeRibbonController,
  UserModeRibbonController, RibbonDataManager, prj::RibbonUserSettingData) are UI/sequencer classes, not EffectBase DSP (`likely`).

**F132 — 1.60 "FX2 on SAMPLE/THRU": FX2 is insert slot 1, and 1.60 raises the inserts per track from 1 to 2 for all track types.**
`confirmed` (cycle 024 worker + critic; `harness/H006_fx2_routing.py`; 1.50 baseline `app-1.50.elf` SHA-256 075cff7a…5ce2, catalog line 327)
- LiveSamplerApplication builds a 24-word HexaTrackAudioSystem config on its stack. AudioSystemBase ctor (1.50 0x1ac27c / 1.60 0x1b8198)
  copies 0x60 bytes to sys+0x204. Only word +0x28 (= sys+0x22c) differs: 1.50 `mov r2,#1`@0x56f894 → `str r2,[sp,#0x80]`@0x56f8d0;
  1.60 `mov r1,#2`@0x571408 → `str r1,[sp,#0x80]`@0x571448 (worker symbolic walk, critic checked all 24 words by hand). new(HTAS) 0x740 → 0x758.
- constructTrack 0x1bacec (1.50 0x1aeb18 area) reads `ldr r5,[r0,#0x22c]` (1.50 0x1aeb24 / 1.60 0x1bacf8) → TrackUnit config word 0 →
  TrackUnit +0xb8 (ctor 0x1cceb0 @0x1ccf2c; slot 53 0x1c7880 getter) = the insert-loop bound. The loop builds InsertFxProcessor (call
  1.50 0x1afbac / 1.60 0x1bbd80) + InsertFxParameterManager (0x1afbc8 / 0x1bbda0) and stores them via addInsert 0x1c9874 into TrackUnit
  +0xf4[i] / +0xe8[i]. One ctor call site per version, nothing writes sys+0x22c at run time, and no track-type branch on the path.
- So 1.50 had exactly one InsertFxProcessor per track (any type); 1.60 builds two on every track. FX2 = slot 1. MIDI tracks also get both,
  disabled by setTrackType (F134).

**F133 — CompositeFxUnit, setFxMode, TrackUnit, the graph wiring and every modelled DSP routine are unchanged 1.50 → 1.60.** `confirmed`
- Masked function diff (harness; 27,390 pairs: 26,787 same / 261 imm / 342 struct). CompositeFxUnit ctor 0x1aa808 (1.50 0x19ea50),
  processBlock 0x1a94cc (0x19d714), FX-mode 0x1a9888 (0x19dad0), task 0x1a9c54 (0x19de9c), handlers 0x1aa060/0x1aa240 (0x19e2a8/0x19e488),
  vtable 52/52, `CompositeFxUnit::setFxMode(CompositeFxMode)` task class vt 0x861714 (1.50 0x85e95c) 4/4; Send/Master/MasterOutUnit
  processBlock; TrackUnit vtable 103/103 incl. processBlock 0x1ca58c, setTrackType, addInsert, ctor; the graph build 0x1bc8d4 (1.50 0x1b06fc)
  makes the same 26 connections with identical arguments. 44/44 modelled DSP entry points/kernels same (EffectBase slot 18 0x106de4, LoFi, MMF,
  PEQ, Phaser, Chorus, Flanger, Distortion, InsertFxDelay, compressors, Ducker, SendFxDelay, SendFxReverb, PerformanceFxLoFi, the three FX
  processors' processBlock, 0xe8228, setFxType 0x11735c); 1.50 IirFilter process = **0xdfd0c** (the harness report's 0xdfac0 is wrong).
- Critic strict re-check over 402 pairs (roots + callees to depth 3: callee identity, real movw/movt values and pointed-to data, pointer
  literals as strings/code/data): no hidden semantic change; only relocated addresses.
- Harness limits (critic): the built-in masking hides all movw/movt immediates, drops callee identity, does not hash pointed-to string
  contents, treats any literal in the image range as a pointer, and `status()` substitutes the containing function for non-start addresses
  (H072). The strict re-check, not the harness alone, carries this finding.
- Other 1.50→1.60 differences on audio-adjacent code, not FX routing (`likely`): HexaTrackAudioSystem processBlock 0x1c12a0 (1.50 0x1b4e6c)
  — two bracket calls now via member +0x5a8 slot +0x10 instead of +0x590/+0x28 (@0x1c13b0/0x1c1874); MultiTrackUnit processBlock 0x1c4ff8
  no longer skips the MTU +0xfc unit when MidiBuffer +0x528 is empty (MIDI path); LfoViewController s0 + 6 slots (FX2 LFO destinations).

**F134 — UI and track type: the FX2 menu items open the slot-1 effect only in 1.60.** `confirmed` (menu-id ↔ track-type assignment `likely`)
- Track type: prj::TrackData +0x24 juce::String "Sample"/"Thru"/"Midi" → 0/1/2 by 0x1cb034 (1.50 0x1becd4); TrackUnit setTrackType 0x1cb584
  (1.50 0x1bf224) stores it at TrackUnit +0x614, points OutputSelector +0x10c at the external input +0x604 for Thru, and calls every insert
  manager's slot 9 with disable 0 (Sample/Thru) or 1 (Midi). Same code in both versions.
- TrackMenuViewController item → view 0x29af60 (1.50 0x298e0c; identical 31-row table): items 5/6 = FX1/FX2 (SAMPLE menu), 10/11 = FX1/FX2
  (THRU menu); MIDI menus have no FX item. 1.50 `cmp r6,#6; cmpne r6,#0xb; beq 0x298e70` → empty view name; 1.60 `bne 0x29b390; add r0,r7,#0x20;
  mov r1,#1; bl 0x300f70` (getInsertFxType(ctx, slot 1)) → `FxInsert<Type>View`. setFx2Image 0x47a3ec (1.50 0x477d48): 0 callers in 1.50,
  2 in 1.60 (0x29ccac, 0x29d0dc). Changed TrackMenuVC functions: 0x29aa98, 0x29af60, 0x29ccac, 0x29d0dc (1.50 0x298ab0/0x298e0c/0x29ab48/0x29ae70).
- Strings: 1.50 LFO destination names "FX > …" (55) → 1.60 "FX1 > …" (55) + "FX2 > …" (55), plus "FX2" (static init 0x55904).
- Project data unchanged: prj::TrackData / EffectData / TrackRoutingData / ProjectData vtables (294 slots) masked-same; no new data-key strings.

**F135 — InsertFxParameterManager knows its slot; modulation ids 200–255 address FX2.** `confirmed` (static both sides + emulation E1)
- Ctor 1.60 0x12864c(this, slot, track, cfg, proc): +0x3c = slot, +0x40 = track (new 0x98); 1.50 0x126c78(this, track, cfg, proc): +0x3c =
  track (new 0x94). Caller passes the insert-loop index. The other fields shift by 4 (imm-only slot differences).
- Slots 57/58 (id → effect index / id → sub-slot, 0x126320 / 0x12633c): range check `cmp r1,#0x37` → `#0x9b`; tables 1.60 0x843ea0 / 0x843f40
  (1.50 0x842260 / 0x842298) grow 56 → 156 B: ids 200–255 = exact copy of 100–155, 156–199 = −1 (emulated over ids 0–299 in both versions).
- Slot 10 0x129b34 (per-block update, 1.50 0x12812c) 1.60 adds at 0x129f08–0x129f34: destination id +0x5c → slot (100–155 → 0, 200–255 → 1,
  else −1) and applies the modulation only if it equals +0x3c. 0x1287a4 is an unreferenced out-of-line copy of that rule.

**F136 — FX2 sits in series after FX1; the track model needs no change.** `confirmed`
- TrackUnit code unchanged (F133), so per F095: main → OutputSelector +0x110 → FX1 (slot 0) → FX2 (slot 1) → OutputSelector +0x118 / Mute#2 →
  +0x114 → Pan → Mute#1 → send tap → fader; call order manager[0] s10 → processor[0] → manager[1] s10 → processor[1].
- Real 1.60 TrackUnit::processBlock (H009 rig, stand-in nonlinear inserts) with 1 and 2 inserts: 24 blocks × 6 ch × 64 each, 0 mismatches vs
  `tools/fx/track_mix.py` with `[fx1]` / `[fx1, fx2]`; reversed-order mutant 4,310 mismatches (worker; critic reproduced). `track_mix.py`
  and `bus_mix.py` unchanged.

**F137 — MasterTempoQualityManager now counts active inserts.** `confirmed` (code, emulated both versions, 70 cases); role `likely`
- constructTrack 1.60 @0x1bc00c registers each InsertFxProcessor with sys+0x610 via 0x1a91b0 (1.60-only append, one caller).
- s5 0x1a8e68 (1.50 0x19d258): 1.50 → Low iff reverb selected && active players > 12; 1.60 → score = 8·reverb + #inserts (vt+0xb8 ≠ −1) +
  2·#players; Low iff score ≥ 33; on change notifies the +0x90 list (vt+8). "Reverb selected" = 0x1a9c78 (Send or Master processor slot 46 == 1).
  `likely`: Low/High is the time-stretch ("master tempo") quality, i.e. a CPU-load heuristic, not an FX/mix change.

## Cycle 025 — H011 the effect plug-in interface (EffectBase) and how effects are created (critic-confirmed)

Evidence for all: kb/cycles/025.md (Worker, Critic); `harness/H011_effect_interface.py --out DIR` → `RESULT: 0 failed checks` (20 PASS;
h011_report.txt 35597b73…25a5, h011.json 1d88a2e3…fbef, slot_matrix.txt b29fcb85…c702; worker ×3 and critic re-run identical). Critic
re-checked with its own capstone pass over all of `.text` (2.13 M instructions, exidx function starts), vtable scan from the 0x106de4 words,
bl/literal/movw-movt and operator-new-size censuses, and its own emulation variants (mode 1, +0xa8 = 1).

**F138 — All 15 effects share one 32-slot EffectBase vtable layout; the override pattern is fixed.** `confirmed`
- 16 `.rodata` words equal 0x106de4 (slot 18) = 16 EffectBase-family groups (EffectBase + 15 concrete, = F128); plus 3 second-base groups
  (InsertFxDelay @−440, SendFxDelay primary DelayEchoBase, SendFxReverb @−440). 19/19 groups identical to cycle 001's output.
- Overridden by all 15: slots 0, 1, 23, 24, 25, 26, 27. Slot 10 by Chorus, Distortion, Flanger, Phaser; slot 11 by SendFxDelay only (its
  EffectBase vtable 0x841eec, ott −568); slots 14/15 by Chorus, Distortion, Flanger. No other slot of 2–22 / 28–31 is overridden; 18 never.
  Extra slots: InsertFxDelay 32/33 (0x102f30/0x102d3c), PerformanceFxLoFi 32 (0xfacec), SendFxReverb 32–35 (0x1120c4/0x11185c/0x1117f0/0x111780).
- No base slot body is ever called by direct `bl` (critic: 0 direct calls for slots 1–31); every use is virtual.

**F139 — EffectBase slot roles and signatures (1.60).** `confirmed` unless marked; soft-float (floats in core registers, F011)
| slot | role | signature | caller(s) |
|---|---|---|---|
| 0 / 1 | complete / deleting dtor | (this) | slot 1 only from FxProcessorBase dtor 0x1127a4 @0x112810 |
| 2 | isSampleRateSupported | int(this, fs): 1 for 44100/48000/96000 | slot 3 |
| 3 | setSampleRate | int(this, fs): 0 ok, 3 unsupported; +0x90 = fs; slot 23(new, old); re-init if running | processor s3 (prepare) 0x117094/0x113174/0x11a088 |
| 4 | setBlockSize | int(this, n): 3 if n ≤ 0; +0x94 = +0x9c = n, realloc copy buffer; slot 24(n) | processor s3 0x1170d4/0x1131b4/0x11a0c8 |
| 5 | start/activate | int(this, float, int honourSkip): arms 147-sample skip if +0xa8; resets HPF/SignalGates; slots 27, 26, 31; gate → state 2 | processBlock 0x116b74/0x112c34/0x119b40 (Insert passes (e, 0, 1)) |
| 6 | stop (fade out) | void(this, float): arms 147-sample clamp if +0xa8; slot 31; gate → state 0; slot 28 | setFxType 0x1173a0/0x113328/0x11a298; FxProcessorBase setDisabled 0x112a40, s50 0x11279c |
| 7 / 8 | start variants (when processor +0x9d ≠ 0 / = 0) | slot 29 or 30 hooks, gate state 1 / 2 | processBlock 0x116ba4/0x112c64/0x119b70 and 0x116ac0/0x112cb0/0x119bb8 |
| 9 | isRunning | int(this) = EffectInOutGain 0x1079d0 | processBlock 0x1168ec/0x112b10/0x119ae8; Master/Send s46 |
| 10 | retrigger | int(this), base returns 2 | FxProcessorBase s49 @0x112774 |
| 13 | getNumParameters | (end − begin)/4 of vector +4 | none found (`likely` unused) |
| 14 | setParameter | int(this, idx, float): 3 if idx out of range, else Parameter vt+0x10 | processor s52 defaults, processBlock tempo/trigger feed, FxProcessorBase s29 0x1126f4 / 0x112924 |
| 15 | getParameter | int(this, idx, float* out), no range check | FxProcessorBase s21 0x112728, 0x11295c; Insert processBlock 0x1169e8 |
| 18 | dispatcher | int(this, L, R, n) | processBlock 0x116a7c/0x112be0/0x119ac4 only |
| 19 | getName | "EFFECT BASE", never overridden | none found |
| 20 | getMix | sret {dry, wet}: slot 26 then +0x10/+0x14 | none found |
| 21 | setCopyMixPath | gate +0xd0 = arg; only other writer EffectInOutGain ctor (1) → copy path always on (`likely`) | none found |
| 22 | setSkipClampEnable | +0xa8 = arg | processor ctors, 29 sites, all r1 = 0 (see F141) |
| 23 / 24 | onSampleRateChanged(new, old) / onBlockSizeChanged(n) — pure | int | slots 3 / 4 |
| 25 | process — pure | int(this, L, R, n) | slot 18 @0x106ecc / 0x106f14 only |
| 26 | updateMix — pure | void(this): writes +0x10 dry, +0x14 wet | slots 5, 20 and every concrete slot 25 |
| 27 | reset | int(this), base returns 0 | slot 5 @0x106318 |
| 28 / 29 / 30 | stop / start-1 / start-2 hooks, return 0, never overridden | int(this) | slots 6 / 7 / 8 |
| 31 | rebuildGateTargets | from mode +0x98 and dry/wet | slots 5–8 |
- Slots 11, 12 (return 2; 11 overridden by SendFxDelay), 16 (getParameterInfo, 5-word sret; `likely`), 17 (Parameter +0x14) have no caller in
  the effect/processor/manager code scanned; "no caller" for 11–13, 16, 17, 19–21 is `likely` (an untyped whole-`.text` vcall census cannot
  type objects). FxProcessorBase vtable 0x842790 (55 slots) exposes no effect pointer (critic).

**F140 — EffectBase object layout; sizeof = 0x1b8; ctor 0x1067d8(this, fs, block, mode).** `confirmed`
- sizeof 0x1b8 (440): dtor member loop over [+0x128, +0x1b8); vmi second base at +440 in InsertFxDelay 0x841d48 / SendFxReverb 0x842710;
  SendFxDelay has EffectBase at +568; Distortion new 0x1d8 = 0x1b8 + 0x20 kernel; ctor writes nothing ≥ +0x1b8 (emulated, 0xA5 heap).
- 4th ctor argument = gate mode, stored at +0x98 (0x106808). All 19 `bl 0x1067d8`: mode 1 for InsertFxDelay (0x1034ac), SendFxDelay (0x105504),
  SendFxReverb (0x1123fc); 0 for the other 16 (processors build Chorus/Flanger/Distortion inline with (44100, 64, 0)).
| off | field |
|---|---|
| +0x00 | vptr |
| +0x04…+0x0f | std::vector<Parameter*> (subclass ctors register parameters) — slots 13–17 |
| +0x10 / +0x14 | dry (1.0) / wet (0.0), written by slot 26 |
| +0x18…+0x8f | 5 gate target records × 0x18, rebuilt by slot 31 |
| +0x90 / +0x94 / +0x98 | fs / block size / gate mode |
| +0x9c / +0xa0 / +0xa4 | copy-buffer length / 2 channels / float[2·len] (planar L then R) |
| +0xa8 | byte skip/clamp enable (ctor 1; slot 22) |
| +0xac/+0xb0, +0xb4/+0xb8 | skip armed/count, clamp armed/count; count = (int)(f32(3.3333333·0.001)·fs) = 147 @44.1 k, 160 @48 k |
| +0xbc/+0xc0/+0xc4 | second buffer len/ch/ptr (0/0/null) |
| +0xc8 | EffectInOutGain* (new 0xd4, ctor 0x10711c, vt 0x842078; +0xd0 = 1 copy path) |
| +0xcc/+0xcd, +0xd0 | post-stage HPF requested/current; cutoff 10.0 (clamped ≥ 5 Hz) |
| +0xd8…+0x127 | IirHpf1stOrder (vt 0x840db8) |
| +0x128 / +0x170 | 2 × SignalGate (vt 0x840e40, 0x48 each) |
- **Slot-25 contract:** `int process(this, float* L, float* R, int n)` in place on planar float32. Default (copy) path: L = [+0xa4], R = L + 4·[+0x9c]
  (EffectBase copy buffer); in-place on the caller's buffers only if slot 21 clears gate +0xd0. n ≤ 64 (45 after a skip, 19 at a clamp end).
  Return 0 → slot 18 runs post-stage + dry/wet mix into the caller's buffers; non-zero → slot 18 returns it and the caller's buffers stay dry
  (processBlock ignores slot 18's value). Input to slot 25 = the caller's block bit-exact in gate modes 0 and 2; **in mode 1 it is ramped**
  (F142).

**F141 — No factory: every effect is built once, eagerly, in the three processor ctors, and selected by array index.** `confirmed`
- All 19 EffectBase-ctor calls and every concrete ctor call lie in the effect ctors or the processor ctors Insert 0x118b0c / Master 0x114bc0 /
  Send 0x11bbe4; vptr literals only in own ctor/dtor or a processor ctor; operator new 0x102e8 sizes 0x2b0/0x478/0x4a0/0x4b8/0x4f0/0x598/0x5d0/
  0x6c0/0x790/0x798 only in the processor ctors. Each processor ctor: 13 `new` calls, no pc-writing instruction (straight-line, no type switch).
- Selection = setFxType(index) into the array (F017); emulated setFxType ×2 + 40 processBlock: 0 heap allocations, 0 EffectBase ctor entries.
- Destruction only via FxProcessorBase dtor 0x1127a4 (backward list walk, slot 1), from the processor dtors (Insert 0x117228/0x118aac, Send
  0x11a20c/0x11bab8, Master 0x11329c/0x1132bc).
- Build chain (critic): processor ctors ← HexaTrackAudioSystem vt slot 55 graph build 0x1bc8d4 (only reference: vtable word 0x863e7c) ← base
  graph build 0x1b6284 ← 0x5712cc (tail call @0x5713d4) ← 0x571d24 = LiveSamplerApplication vt slot 5 (0x932804). So effects are built at
  application start; whether slot 55 is ever re-invoked (wholesale rebuild) is open (H073).
- Host-side ctor step per effect: slot 22(e, 0) for every effect **except Insert index 7 (InsertFxCompressor)** (Insert 9 sites, Master 10,
  Send 10; critic finding, own census: no other +0xa8 writer than slot 22 0x1059b0 and the ctor 0x1068ac). So Insert FX 7 keeps +0xa8 = 1:
  with Insert's slot 5(e, 0, 1) its slot 25 is skipped for the first 147 samples after activation (output = input, then the 147-sample
  crossfade) and processing stops 147 samples after slot 6 (critic emulation: n per block [45, 64, …]). Audible effect on the device untested.
- Then 0x106c7c(e, 1, 10.0f) (post-stage HPF on) for Chorus, Flanger, MMF, LoFi, Distortion, Phaser only (Insert indices 0,1,3,5,6,8; Master/
  Send 2,3,5,6,8,9; 18 sites); never for PEQ, delays, compressors, Ducker, Reverb.

**F142 — EffectBase wrapper behaviour (slot 18 + gate), validated with a stub effect.** `confirmed` (emulated; laws analytic)
- Stub = real EffectBase ctor object, vtable copy in guest memory with own slots 23–27; driven through real 0x106de4 and through the real
  InsertFxProcessor setFxType 0x11735c / processBlock 0x116860 (stand-in processor fields). Nothing written outside guest memory.
- Post-stage = one-pole 10 Hz HPF (IirHpf1stOrder): DC 0.5 decays to 0.0130398 at sample 2559 vs analytic 0.0130482 (upgrades F024).
- Activation: linear 147-sample dry→wet output crossfade in·(1 − t/147) + wet·t/147 (max |diff| 6.3e-7); steady state =
  f32(f32(dry·in) + f32(wet·y)), 384/384 bit-exact. Stop: the mirror, then slot 9 returns 0.
- Gate mode 1 (InsertFxDelay, SendFxDelay, SendFxReverb): additionally the **effect's input** is ramped in over 147 samples on activation
  (in/caller = t/147, critic measured) and out on stop — the 0x1074c4 fade of H044/cycle 015. The combined law out = in·(1 − t/147) +
  wet(in·t/147)·t/147 fits within 5.9e-7 (critic fit; `likely` as an exact law until modelled, H044).
- FX type change is sequential, not a crossfade: setFxType calls the old effect's slot 6; it fades to dry over 147 samples; the swap happens
  when slot 9 returns 0 (3 blocks later), then the new effect gets slots 5 and 7 and fades in (peaks 0.680/0.876/1.000/0.954; stand-in
  processor). Blocks before/after equal a direct slot-18 drive bit-exactly.

**F143 — Host registration points: an effect type is compiled into ≥ 5 places per processor/manager; no runtime registry.** `confirmed`
for items 1–5; roles of items 6 `likely`/`guess`
1. Processor ctor build list (order = index) + slot 22 / 0x106c7c steps (F141). List count +0x88 bounds lookups.
2. Processor slot 52 defaults: 10-case jump tables Insert @0x117448 (body 0x117434), Master @0x113408, Send @0x11a378, each calling slot 14.
3. processBlock per-index feed: Insert table @0x11694c ({0,4} → 0x116ad4, {1,8} → 0x116b28, {9} → 0x116974, else 0x116a64); Master @0x112b44 /
   Send @0x119a38 cases {0,2,3,9} (Delay, Chorus, Flanger, Phaser; that they feed tempo is `likely`, H037).
4. Slot 45 load table: Insert 0x842be0 [19,21,22,19,24,26,30,22,26,14]; Master 0x842a78 = Send 0x842d10 [31,167,19,21,22,20,22,31,22,27]; `cmp #9`.
5. Manager slot 32 name/setFxType switch: Insert @0x128838, Master @0x123818, Send @0x12bcbc; slot 53/54 tables 0x843d98 (+0x50), 0x8436e0,
   0x8445c8 (F018/F019).
6. Manager per-index switches (**roles settled by F162/F163:** s34 = SYNC toggle, s50 = UI integer range), role not established at the time: s34 (Insert @0x126d18 cases 0/1/4/8/9; Master @0x120924 / Send @0x12b42c cases 0/2/3/9;
   tempo/sync `likely`), s50 (Insert @0x12647c, Master @0x120248, Send @0x12ad50; 10 cases × 6-case sub-switches; FX-lock sub-slots `guess`),
   Insert s10 0x129b34 @0x129d50 (9 cases, none for Distortion; modulation `guess` per case), others (Insert s38/59/61/65/73, Master s38/s41).
7. Data/UI: FxParamIndex tables, slot 57/58 tables (F135), FxSelectPopupWidget items (F131), view controllers — not re-derived.
- H011 verdict: (a) one virtual interface — **confirmed**, but it is EffectBase alone (FxProcessorBase is the host) and wider than
  init/set-param/reset/process: a new effect implements dtor, 23, 24, 25, 26 (usually 27; optionally 10, 14/15, slots ≥ 32), registers its
  Parameters in the +4 vector, and picks gate mode 0/1 in the ctor; the host decides +0xa8 and the HPF. (b) factory keyed by effect type —
  **refuted**. (c) extension point — **partly**: sufficient on the audio side (stub runs bit-exactly through the real host), but adding a type
  needs host code/data in items 1–5 (+6–7); there is no registry or plug-in table.

## Cycle 026 — H044 the common EffectBase slot-18 wrapper, modelled bit-exactly (critic-confirmed)

Evidence for F144–F149: kb/cycles/026.md (Worker C1–C6, Critic); harness `harness/H044_effectbase_wrapper.py`, model
`tools/fx/effectbase.py`; run `python -B harness/H044_effectbase_wrapper.py --out harness/out/H044` → `RESULT: 0 failed checks`
(14 PASS lines), output hashes c3 b7f91882…a019, c4 47c85123…4d03, c4_ext 6909f55b…d8ee, c5 526c2b9f…2b32 (reproduced by the critic and
under `PYTHONHASHSEED=999`). Critic's own fuzz: 40 seeds × 220 blocks (fs 44.1/48/96 k, ctor modes 0/1/2/3/5, n 0…64, random events) + 31
"realistic" seeds, all bit-exact with internal state equal after every block.

**F144 — SmoothFloat and the EffectInOutGain gate state machine.** `confirmed` (decompile + bit-exact emulation)
- SmoothFloat (0x24 bytes): setSmoothingTime 0xf5a00 N = trunc(f32(f32(ms·0.001f)·f32(fs))) → 147 @44.1 k, 160 @48 k, 320 @96 k (ms =
  3.3333333); setTarget 0xf5668: no-op if |target − old| < FLT_EPSILON, else step = f32(f32(target − cur)·f32(1/N)), remaining = N; getBlock
  0xf55a4 emits cur then cur = f32(cur + step) (accumulated sum, first sample = start value), snapping to target when `remaining` runs out;
  0xf5584 snaps cur = target. For 0 → 1: g[1] = 0.00680272, g[146] = 0.99319804 (exact t/N ramp is refuted: max 8.9e-7).
- EffectInOutGain (new 0xd4, ctor 0x10711c): +0x1c current, +0x20 transitioning, +0x24 target, +0x28/+0x2c pending flag/state, +0x30…+0x44
  pending record, SmoothFloats input +0x48 / dry +0x6c / wet +0x90, +0xc0/+0xc4 dry/wet copied from e+0x10/+0x14 every block, +0xc8 = 1
  only for ctor mode 1, +0xd0 copy-path byte. Model ctor state equals the emulated ctor field by field at 44.1 and 48 kHz.
- start 0x107310(gate, state, rec): on the copy path only stores the pending (state, record) (last call before slot 18 wins).
  applyPending 0x107374 (top of slot 18): drop if pending == current target; else, if a transition runs, current := old target and all three
  SmoothFloats freeze; transitioning = 1, target = new, setSmoothingTime(3.333 ms), per gain record mode 0 → snap, 1 → setTarget (ramp).
  isRunning 0x1079d0 (slot 9): current = target → current; current 0 → target; target 0 → current (runs until the stop fade ends); 1 ↔ 2 → 1;
  else 0. End of transition (tail of 0x10770c): all three idle → current := target, transitioning = 0. reset 0x1072bc (slot 5): current =
  target = 0, snap gains to record R0.

**F145 — Gate target records per ctor mode; slots 5–8; modes 2 and ≥ 3.** `confirmed`
- Slot 31 0x105d78 builds 5 records (in, dry, wet; each mode snap/ramp) at e+0x18…: R0 reset (mode 0: in 1, dry 1, wet 0; mode 1: in 0),
  R1 slot 5 → state 2 (mode 0: in ramp 1, dry snap := slot-5 arg, wet snap 0; mode 1: in snap 0, dry snap, wet ramp → wet), R2 slot 6 →
  state 0 (dry ramp → slot-6 arg, wet ramp → 0; mode 1 also in ramp → 0), R3 slot 7 → state 1 (dry/wet ramp → e+0x10/+0x14; mode 1 also in
  ramp → 1), R4 slot 8 → state 2 (dry → 1, wet → 0 in mode 0; mode 1: in → 0, dry → 1, wet snap → wet).
- Slot 5 = slot 27, 26, 31, R1.dry := arg, reset(R0), start(2, R1), arms the skip if its 3rd arg ≠ 0 and +0xa8 ≠ 0; slot 6 = arm clamp
  (if +0xa8), 31, R2.dry := arg, start(0, R2); slot 7 = 31, start(1, R3); slot 8 = 31, start(2, R4).
- Ctor mode 2 has its own branch but behaves exactly like mode 0 (R0 snaps the input gain to 1 first); modes ≥ 3 keep the ctor records and
  fade the wet in one block (64 samples) late. No 1.60 effect uses modes 2/3+ (F140).
- Slot 8 in mode 1 (input muted, dry → 1, wet follows e+0x14 = a tail ring-out) is shown only through gate state, never on audio with a
  stateful effect: `likely`.

**F146 — Mode-1 input fade 0x1074c4 and the mix 0x10770c (exact laws).** `confirmed`
- 0x1074c4 (copy path only): input gain idle 1 → nothing; |g| < FLT_EPSILON → memset 0; idle other → vector × scalar 0x579178; ramping →
  getBlock into the gate scratch, then vector × vector 0x579018 on both channels. Mode 0/2: input held at 1 (slot-25 input raw). Mode 1:
  0 → 1 over 147 samples on activation, 1 → 0 on stop.
- 0x10770c(gate, L, R, cL, cR, n): if not transitioning, state 1 → dry.setTarget(+0xc0), wet.setTarget(+0xc4); state 2 with +0xc8 → wet only.
  So a slot-26 dry/wet change glides over 147 samples and waits while an activation/stop transition runs. Then L,R ·= dry, copy ·= wet,
  L += cL (idle shortcuts |g−1| < ε skip, |g| < ε memset). NEON (flush-to-zero) for groups of 4, VFP for the n % 4 tail.
- Per sample: out = f32(f32(x·d_t) + f32(S25(f32(x·i_t))·w_t)) with i_t ≡ 1 outside mode 1; two roundings (single-rounding variant refuted).
  The activation/stop crossfades (F142) are this mechanism with the R1/R3 and R2 targets.

**F147 — Post-stage 0x106c88 exactly: SignalGate → IirHpf1stOrder → SignalGate.** `confirmed` (upgrades F024/F142)
- Chain: SignalGate +0x128 → IirHpf1stOrder +0xd8 → SignalGate +0x170; gates are SmoothFloat gates with N following fs (147 / 160).
- 0x106c7c(e, on, fc) only writes request +0xcc and fc +0xd0; the switch takes effect at the next post-stage call or at slot 5 (copies +0xcc
  → +0xcd). On: fc = max(5, min(+0xd0, fs/2)), coefficients, gates setTarget(open); off: gates close; the stage is skipped while off and both
  gates idle-closed. A runtime toggle therefore fades the wet out over 147 samples (A·B) then jumps to unfiltered, or fades in through the HPF.
  On the device 0x106c7c runs only in the processor ctors (F141), so only the slot-5 path occurs (`likely`).
- Coefficients 0xe1aa0 (double): w = (tan(fc·π/fs)·(1/2π))·2π; b0 = f32(1/(w+1)), b1 = −b0, a1 = f32((w−1)/(w+1)); 10 Hz/44.1 k: b0
  0.999288142, a1 −0.998576283 (12 fc/fs pairs bit-equal to emulation; the path without 1/2π·2π is refuted). Process 0xe1490 (NEON, flush-to-
  zero): y = b0·x + b1·x[−1] − a1·y[−1]. Slot 5 zeroes the HPF state and snaps the gates open (HPF on) or closed.

**F148 — Skip/clamp (+0xa8…+0xb8) and the Insert COMPRESSOR start delay (H074).** `confirmed` (emulation; device audibility `guess`)
- Only if +0xa8 ≠ 0. Count = trunc(f32(f32(3.3333333·0.001f)·fs)) = 147 / 160. In slot 18 after applyPending/isRunning: while skip > n the block
  stays untouched and the gate does not advance; otherwise L/R/n are offset by the remaining skip (n = 45 @44.1 k, 32 @48 k). Clamp (armed by
  slot 6): while clamp > n normal; otherwise n := clamp (first `clamp` samples copied, processed, mixed; rest dry) and disarm.
- Slot-25 return ≠ 0: post-stage and mix skipped, buffers dry, gate does not advance (a transition stalls). In-place path (slot 21(0)): no
  fade, post-stage or mix.
- Real InsertFxCompressor (Insert leaves +0xa8 = 1, F141): output = input bit-exactly for samples 0…147 after every activation, first
  difference at 148; every other insert (and the compressor model with +0xa8 = 0) differs from sample 1. So Insert COMPRESSOR alone starts
  147 samples (3.3 ms @44.1 k) late.
- Stop: every insert stops processing 147 samples after slot 6 (its fade-out ends there). The clamp makes that end sample-accurate and changes
  the output only when the slot-6 dry target ≠ 1 (critic no-clamp mutant: 19/31 seeds differ, max ≈ 1.0, with random arguments; 0/31 with
  1.0). All five 1.60 slot-6 call sites pass 1.0f (0x1173a0, 0x113328, 0x11a298, 0x112a40, 0x11279c), so the stop clamp is inaudible on the
  device. The "147-sample late stop" consequence in F141/H074 is refuted.
- The skip/clamp is a sub-block alignment of activation start and stop end only; not parameter/tempo alignment (H012 clause refuted).

**F149 — `tools/fx/effectbase.py` reproduces the real wrapper end to end.** `confirmed`
- Pure Python, own code, no emulator/firmware access (constants hard-coded, checked by the harness against 1.60 literals); injectable slots
  25/26/27; slots 5–9, 21, 22, 31, 0x106c7c; fs 44.1/48 k (96 k works).
- Stub effect through real 0x106de4: 50 cases × 200 blocks (modes 0/1/2/3, HPF on/off/toggle/clamps, +0xa8 0/1, fs 44.1/48 k, activation at 0
  and mid-run, stop and re-activation, dry/wet changes, slot-25 return ≠ 0, in-place, DC/impulse/sine/denormal noise), 1.28 M samples bit-exact
  with returns, slot-25 inputs and internal state; plus the critic fuzz. Caveat: 4 worker cases are dry pass-throughs (state-only evidence).
- Real effects through real slot 18 (Insert-ctor state per F141), composed with the per-effect slot-25 models: bit-exact (25600/25600, also
  under the critic's alternative timings/signals) for Chorus, Flanger, InsertFxDelay (mode 1), Distortion, InsertFxCompressor (+0xa8 = 1),
  Phaser, Ducker, SendFxDelay, SendFxReverb, SendFxCompressor. PEQ, MMF, LoFi are bit-exact until their first re-activation, then drift (max
  7.8e-3 / 4.3e-3 / 5.6e-4) because those models lack slot 27; with the emulated slot 27 replaced by the base slot 27 they are bit-exact.
  This also shows Insert's slot 5(e, 0, 1) calls the effect's slot 27 on every re-activation.
- Slot-26 laws used (bit-exact in composition): Chorus/Flanger dry 1, wet Mixratio; LoFi/MMF/Phaser dry 1 − v, wet v; PEQ and Ducker dry 0,
  wet 1; InsertFxDelay piecewise (F078); SendFxDelay copies its stored +0x6a4/+0x6a8 (1/0 until its first slot 25); SendFxReverb piecewise
  × 0.70795 (F122); compressors dry 1 − v, wet v·makeup. "Dry stays 1.0" (F061) is Chorus/Flanger-specific.
- Processor level: the model's `InsertProcessor` matches the real setFxType 0x11735c / processBlock 0x116860 bit-exactly (stand-in
  processor fields, real MuteSmoother) through 5 → 7 → 3 → 7 → 5 → Off → 7 (compressor at 7) and the critic's schedules (rapid changes,
  re-select during fade-out, compressor stopped inside its skip, +0x9d = 0 → slot 8 swaps after 1 block). Each swap happens at the first
  block where slot 9 = 0 (3 blocks after setFxType); from Off, setFxType takes effect at once.
- **Limits:** valid only for an enabled, non-bypassed processor: processBlock also runs 0xe8050/0xe8228 on processor byte +0x9c (decompile:
  [corrected by F157: 132 samples, not 128] 128-sample linear crossfade processed ↔ dry copy, `likely`; never exercised by the worker; +0x9c = 1 → 18946/25600 exact) and +0x9e
  (disable: no slots 5/7/8 after a swap; 0x112a08 sets it and calls slot 6(1.0f); +0x9e = 1 → 20572/25600). Master/Send processors not
  driven; slot-3 sample-rate change while running not modelled; host `math.tan` checked only for 12 fc/fs pairs (H029).

## Cycle 027 — H076 / H025 slot-27 resets of LoFi, MMF and PEQ; 13/13 effects end-to-end bit-exact (critic-confirmed)

Evidence for F150–F153: kb/cycles/027.md (Worker C1–C6, Critic); harness `harness/H076_slot27_reset.py`; models `tools/fx/lofi.py`,
`mmf.py`, `peq.py` (`reset()`, `clear_taps()`), `harness/H044_effectbase_wrapper.py` (`build_generic` uses the model resets); run
`python -B harness/H076_slot27_reset.py --out harness/out/H076/final` → `RESULT: 0 failed checks` (16 PASS); h076_report.txt
5f4fe838…1137, h076.json eb11bad9…f48e, composition outputs c4_comp_outputs.f32 11fe2c44…fe34 (reproduced by the critic). Regressions H021,
H023, H026, H044 and H064 reproduce their recorded hashes. Critic's own fuzz (`<critic scratch run>`, not kept): 3 effects ×
fs 44.1/48 k × 5 seeds × 200 blocks, random parameters incl. type/kind changes while stopped or fading, random stop/re-activation: 30/30
bit-exact (768,000 samples, output + wrapper + full effect state); wrong-reset mutants fail every run.

**F150 — Slot 27 (reset) of LoFi 0xfb5a4, MultiModeFilter 0x107fa8, PEQ 0x10a7ec.** `confirmed` (decompile by worker and critic + heap-write
log of the real routine + 17 field-level state dumps, LoFi 162 / MMF 302 / PEQ 386 fields as raw bits)
- All three: (1) call the effect's own parameter-apply routine (LoFi 0xfb20c, MMF 0x107d18, PEQ 0x10a4f0; the same routine slot 25 starts
  with), which consumes **pending changes only** — nothing is re-applied when none is pending; (2) zero the tap memory of the **current**
  stage only (LoFi sub-filter container +0x14; MMF kind: 0–2 one biquad, 3–5 both cascaded biquads, kind 6 nothing; PEQ per band +0x18:
  types 0–2 IirFilter2 taps via 0xe2cf8 (+0x7c…+0x88), types 3/4 IirFilter taps); out-of-range index → null (PEQ type 5, `likely`);
  (3) LoFi only: sample-and-hold holds := 0 and phase := step (step read after the apply, so a pending REDUCTION gives the new step);
  (4) return 0. Vtable slot-27 entries: LoFi 0x841ad4, MMF 0x842124, PEQ 0x842204 (vptr + 0x6c).
- Not touched: coefficients/fc/Q, SignalGates, GainRamps, glide state (a glide interrupted by a stop continues after re-activation), LoFi
  preamp ramp, crusher, FILTERPOSITION, non-current stages (their stale taps stay; critic: state-only in one MMF fuzz seed).
- Refuted alternatives (each by ≥ 1 case): no reset; clear all stages; PEQ clear the pending stage; snap glides/GainRamp; LoFi phase := 0 or
  1.0, holds kept.
- On the Insert path the apply inside slot 27 is output-neutral (slot 25 runs straight after it and does the same apply); it is a state fact.
- Corrects F035/F042 "slot 27 re-applies params" → "applies pending changes only, clears the current stage's taps". Settles H025.

**F151 — 13/13 modelled effects are bit-exact end to end through the real slot 18.** `confirmed`
- With the F150 `reset()` models, the H044 c4_ext table is 13/13 bit-exact (25,600/25,600 each, state/slot-9 diffs 0); the emulated-output
  hash 6909f55b is unchanged, so only the model side was missing. 27 new composition cases (PEQ/MMF/LoFi × 3 settings × noise/sine/impulse,
  220 blocks, 3 slot 5 → 27 calls each, changes while stopped and glides running at the stop): 760,320 samples, max |diff| 0. Critic fuzz at
  44.1 and 48 kHz: 30/30.
- Limits as F149: enabled, non-bypassed Insert processor ctor state; Master/Send processors not driven; host libm residual (F044/H029).
- Model corrections (no output depends on them): LoFi Insert RESONANCE default = f32(5/98) = 0.0510204099; the IirFilter2 ctor leaves
  Q = 0.70710678118654746 and placeholder coefficients, overwritten before any stage is processed.

**F152 — LoFi output dropout after every activation.** `confirmed` in emulation (device audibility `likely`)
- Slot 27 sets S&H phase := step with holds 0, so the wet path outputs 0 for ⌊step⌋ samples after slot 5. With MIXRATIO 1 the dry part is
  gone after the activation crossfade, leaving exact digital silence of ⌊step⌋ − F samples starting at +F, F = 147 @44.1 k / 160 @48 k
  (44.1 k: REDUCTION 0.2 → 103, 0.1 → 354, 0.05 → 564, 0 → 855 samples = 19.4 ms; 48 k: 385 and 930). Same at the first activation and at
  every re-activation, any filter type, noise or sine. No gap when step ≤ F (REDUCTION ≈ ≥ 0.28 at 44.1 k; 0.3 measured). With MIXRATIO v < 1
  the output during the gap is exactly the dry share (1 − v) (0.5 and 0.75 measured).

**F153 — PEQ start-up quirk (F039) is reduced, not hidden, by the activation fade.** `confirmed` in emulation (device "once per object
lifetime" `likely`, audibility `guess`)
- PEQ defaults, DC 0.5 through the real slot 18: min out/in after the *first* activation 0.6544 (−3.68 dB) at sample +76 @44.1 k (analytic
  (1 − t/147) + (t/132)²·t/147 at t = 132/√3) and 0.6536 at +83 @48 k; after any re-activation 1.0000 (slot 27 leaves the gates open). LoFi
  at defaults shows the same one-time dip (rms 0.83/0.75 at first activation, 1.00 at re-activation); MMF not separable at its default level.
  Evidence against H030's "inaudible" premise; H030's UI half untested.

## Cycle 028 — H077 / H056 / H037 / H014: Master and Send FX processors modelled bit-exactly (critic-confirmed)

Evidence for F154–F158: kb/cycles/028.md (Worker C1–C7, Critic); harness `harness/H077_master_send_proc.py`, model
`tools/fx/fx_processors.py` (MuteSmoother incl. 0xe8228 crossfade, MasterProcessor, SendProcessor, InsertProcessorFull); run
`python -B harness/H077_master_send_proc.py --out harness/out/H077/run3 --jobs 5` → `RESULT: 0 failed checks`; output hashes
c3m 6a4831a4…0264, c3s 3784449b…34af, c4 b7ae13f4…55ce, c5 7fc3a191…c91c, c6b 42e42dfe…9ad1 (reproduced by the critic, and under
`PYTHONHASHSEED=7 --jobs 3`). Rig: real processor ctors (Master 0x114bc0, Send 0x11bbe4, Insert 0x118b0c, building all 10 effects + slot 52),
real prepareToPlay (0x112cd0 / 0x119bd8 / 0x116bc4), real setFxType / processBlock / 0x112a08 / 0x1129b4. Stand-ins: tempo provider at
+0x94 (vt+0x1c hook), JUCE 0x5f9e90 skipped (return value unused, critic), pthread stubs, bus buffer object (read only at +0xc, critic).
H076 regression (and its H021/H023/H026/H044 sub-regressions) reproduce their recorded hashes; no existing model file was edited.
Critic's own tests (`<critic scratch run>`, not kept): all-type disable 40/40, random schedules incl. raw +0x9d toggles and tempos
0/−3/999.5/5000 30/30, Insert bypass fuzz 10/10 (control without bypass fails), real prepareToPlay mute N at 22.05/44.1/48/96 kHz.

**F154 — Master and Send FX processors: differences from Insert processBlock 0x116860.** `confirmed` (decompile/disasm + bit-exact emulation)
- Offsets: Master/Send current +0xa0, pending +0xa4 (Insert +0xa4/+0xa8; Insert +0xa0 = ctor arg 1). Tempo provider +0x94 (FxProcessorBase
  ctor 0x1128cc). MuteSmoother: Insert +0x144 (bypass), Send +0xa8 (input mute), Master none. Block size n = 64 hard-coded.
- **Master 0x112acc** = Insert minus the input copy and the post-slot-18 bypass stage: poll slot 9 when current ≥ 0, swap at 0, then slot 5(e,0,1)
  and slot 7(e,0) (+0x9d ≠ 0) or slot 8, only if pending ≥ 0 and +0x9e = 0; feed; slot 18; return.
- **Send 0x119994** (no Ghidra function there; read with capstone) = Master plus an input mute before everything: flag =
  `pending == −1 ? 1 : (+0x9e ? 1 : +0x9d ^ 1)` → 0xe8050(+0xa8, flag) → 0xe808c in place; and it polls/swaps only if current ≥ 0 **and**
  +0x9e = 0. Slot 5 is (e, 0, 0); irrelevant because the real Master/Send ctors leave +0xa8 = 0 on all 10 effects.
- setFxType Master 0x1132e4 = Send 0x11a254 (identical code), same as Insert 0x11735c apart from offsets; the old effect gets slot 6(1.0f) on
  every call while current ≠ −1 (a change during a fade-out re-arms it; the intermediate type is never activated).
- Ctor state: Master/Send +0x9c/+0x9d/+0x9e = 0/1/**1** — both start disabled until the FX-mode routing calls 0x112a08(p, 0) (F105); Insert 0/1/0.
  Off (current −1): Master leaves the bus untouched; Send mutes it; Insert still runs its bypass crossfade stage.
- MuteSmoother (0xe7fd8 ctor / 0xe8050 setMuted / 0xe808c process): N = roundToInt(f32(f32((int)fs)·0.001f)·3) (3 ms: 66/132/144/288 at
  22.05/44.1/48/96 kHz, real prepareToPlay); setMuted: remaining := N − remaining, step ±1/N; process: out = f32(in·g), g accumulated in float;
  end muted → zero-fill, unmuted → g = 1 idle. Insert/Send create it only while the pointer is null, so the *first* prepareToPlay fixes N.
  The Send smoother is created unmuted, so a Send that starts in Off passes one 132-sample decaying ramp of the bus after prepareToPlay.
- Model: `tools/fx/fx_processors.py` (pure Python), composed with `effectbase.EffectBase` and the per-effect models: 60 type-matrix cases
  (both processors × 10 types × noise/sine/impulse × 200 blocks) + 8 FX-change schedules (Off→type, change during fade-out, →Off; 240 blocks):
  68/68 bit-exact in outputs, processor state, slot 5–8/14 call log and wrapper state every block; none is a dry pass-through.
- **H077 confirmed**: the effectbase wrapper generalises unchanged; only the processor shells differ as above.
- Not modelled: the +0x9d setter 0x1129bc (reached via thunk 0x11caf4; if +0x90 ≠ 0 stores +0x9d and, if +0x9e = 0, directly calls the pending
  effect's slot 7(e, 0) or slot 8; reader 0x11cae0); the Insert Ducker (index 9) feed inside `InsertProcessorFull`; non-integer fs.

**F155 — Disabling a processor (0x112a08): Master passes dry, Send returns silence.** `confirmed` in emulation (all 10 types each)
- Master disabled: old effect slot 6(1.0f) 147-sample fade to dry; output == input bit-exactly from sample 147 after 0x112a08(p, 1) (delay and
  reverb tails are cut, not left to ring). While disabled Master still polls: a setFxType swaps `current` at once without slots 5/7/8.
- Send disabled (or Off): input ramped to 0 over 132 samples, the effect's fade ends at 147 → output exactly 0.0 from sample 147 (132 when
  the wet path is already silent). While disabled Send neither polls slot 9 nor swaps.
- Re-enable (0x112a08(p, 0)) calls nothing itself; at the next block slot 9 = 0 → swap → slot 5 + slot 7 = full re-activation incl. slot 27
  (e.g. SendFxReverb warm-up restarts); Send adds a 132-sample unmute ramp. A quick off→on during the fade-out does not cancel it: the effect
  fades to dry and re-activates ~3 blocks later.
- With F105: FX mode Send → Master FX path passes the main bus dry (H056 confirmed); FX mode Master → Send FX return is digital silence;
  mode > 1 → both. Device audibility `likely`; whether anything upstream skips calling a disabled processor is not emulated (F105 static: no).

**F156 — Master/Send tempo feed and slot-52 defaults.** `confirmed`
- processBlock feeds, once per block and to the *current* effect (also while it fades out before a swap), slot 14(e, 7, clamp(f32(tempo), 1, 999))
  for Master/Send indices {0 SendFxDelay, 2 Chorus, 3 Flanger, 9 Phaser} (jump tables @0x112b4c / @0x119a40; clamp literal 999.0); tempo =
  +0x94 vt+0x1c (double → float). Audible only with SYNC on (removing the feed: free Chorus unchanged; synced Chorus/Delay differ). 8 sync
  cases bit-exact (tempo 120/140/60.5/2000→999/0.1→1).
- Chorus slot-52 defaults are identical on Insert (case 0 @0x117478), Master (case 2 @0x113ac8) and Send (case 2 @0x11aaa8), **including
  Mixratio 0** — same getter pairs (Mixratio 0x349dc8/0x349db0), index 6 = 0: [(0, 0.191919), (1, 1.0), (2, 0), (3, 0), (5, 0), (6, 0)].
  Flanger, PEQ, MMF, LoFi, Distortion, Phaser defaults Insert = Master = Send; compressor M/S = Insert plus (6, 0.0). Master vs Send differ only
  in Delay and Reverb Mixratio (0.5 vs 1.0). "Chorus on Master/Send outputs dry" holds at the processor defaults only; whether the parameter
  manager/project overwrites them on the device is untested.
- H037 confirmed with correction (feed exists and also covers the Delay; defaults equal *including* Mixratio).

**F157 — Insert processor bypass (+0x9c) is a 132-sample linear crossfade to the dry copy.** `confirmed` (emulated, 4 + 10 fuzz cases)
- Setter 0x1129b4 (`strb r1,[r0,#0x9c]`); read only by Insert processBlock (Master/Send never load +0x9c). Insert copies the input to +0xb8
  before slot 18, then 0xe8050(+0x144, +0x9c) and 0xe8228: per sample L = f32(f32(dry·(1−g)) + f32(g·L)), g from the MuteSmoother (1 →
  0 over N = 132 @44.1 k / 144 @48 k); once fully bypassed L := dry copy (memcpy). The effect keeps running behind the bypass. Output ==
  dry input from sample 132 after 0x1129b4(p, 1). **Corrects F149 / H014 / functions.md "128 samples".**
- Quirk: on an Off insert the ramp changes the signal by ≤ 1 ulp (54 samples, max rel 1.06e-7) — double rounding of dry·(1−g)+g·dry.
- Callers of 0x1129b4: 0x11cfe4 (manager method, guarded by its byte +0x24) and 0x129e58 (Insert manager, value = byte +0x29 of a per-slot
  struct); device meaning (FX on/off button) `guess`. Settles H014's remaining clause.

**F158 — Corrections to earlier findings.** `confirmed`
- F149 "+0x9c … 128-sample linear crossfade" → 132 samples @44.1 k (3 ms law, F157).
- F105 "`likely` a disabled MasterFxProcessor passes the main bus dry" → `confirmed` (F155).
- H037's "Chorus defaults equal Insert except Mixratio" → equal including Mixratio (F156).

## Parameter managers: FxParamIndex → slot 14 (1.60) — cycle 029 (H004)

Evidence for F159–F163: kb/cycles/029.md (Worker + Critic), `harness/H004_fxparam_map.py` (`python -B harness/H004_fxparam_map.py
--out harness/out/H004` → 39 PASS, 0 failed; h004.json f3a052aa…cd72, fxparam_map.csv aa16baa2…1bff, reproduced by the critic). Code read by
capstone disassembly + REA `read_bytes` (REA Ghidra has no functions at the manager addresses; a decompile there silently falls back to a
*file offset* — do not trust it). Real IFPM ctor 0x12864c + real InsertFxProcessor; stand-ins: prj::EffectData + holder, processor s54.

**F159 — FxParamIndex 0–71 is an Insert-only flat list; 55 valid rows map one-to-one onto (effect, slot-14 index 0–5).** `confirmed`
- InsertFxParameterManager (IFPM, vt 0x84407c) s55 0x1262e8 = `i ≤ 71u ? (int8)[0x843d98+0x78+i] : −1` (FxParamIndex → Insert effect index)
  and s56 0x126304 = same at +0xc0 (→ sub-slot = slot-14 index). Critic re-read both tables; a guest patch of T_sub[4] moved the lock.
- −1 effect on 17 rows (11–22, 56–60); −1 sub on 13 rows (14, 15, 17–22, 56–60); rows 11/12/13/16 have no effect but sub 0/1/2/5.
  55 valid rows → 55 distinct (effect, sub) pairs, 0 duplicates. Never sub ≥ 6.
- Map (f → Insert index/class → slot-14 indices): 0–4 → 0 Chorus {0,1,2,3,5}; 5–10 → 1 Flanger 0–5; 23–28 → 5 LoFi 0–5; 29–34 → 2 PEQ 0–5;
  35–40 → 6 Distortion 0–5; 41–45 → 3 MMF {0,1,2,3,5}; 46–49 → 4 InsertFxDelay {0,1,2,5}; 50–55 → 7 Compressor 0–5; 61–66 → 8 Phaser 0–5;
  67–71 → 9 Ducker {2,3,0,1,5} (RELEASE, RELEASECURVE, ATTACK, ATTACKCURVE, DEPTH). Full per-row table with names, modulation ids and s50
  ranges in kb/cycles/029.md C1 and `harness/out/H004/fxparam_map.csv`.
- Modulation tables (s57/s58, F135) cover the same 55 pairs (id 154 the only gap), in a different order: modulation id ≠ 100 + FxParamIndex.
- MasterFxParameterManager (vt 0x8437ec) and SendFxParameterManager (vt 0x8446d4): s6 and s10 are `bx lr`, s55–s58 `return 0` (not −1) —
  no FxParamIndex tables (`confirmed`); "FxParamIndex is Insert-only" `likely` at manager level.
- Other users (static, roles `likely`): 72-case switch @0x1de6dc (fn 0x1de684) builds a `UserModeFloatParameter` (vt 0x868600) for exactly
  the 55 valid rows; 0x351c70 / 0x3535dc have the [1.50] R003 49-case set and read step words via int8 table 0x8ab198 (= T_sub on all 55
  valid rows) → H003 lead.

**F160 — Insert manager value path: the normalised value reaches slot 14 unchanged; no effect-type check.** `confirmed` (emulated)
- Sink: FxProcessorBase s29 0x1126dc(proc, idx, v) → pending effect (`proc+0x90`) slot 14(idx, v); 0x112924(proc, eff, idx, v) → array[eff]
  slot 14 (bounds-checked). Both identity.
- Lock: IFPM s6 0x1263c0(this, _, f, v): sub = s56(f); +0x68[sub] = v, +0x80[sub] = 1 — no s55 call, no float op. Applied only after a trigger
  (s2 0x1263f4 sets +0x86 for every event type; processor s54 only for 11/15): next s10 0x129b34 sends, for k = 0…5, slot 29(k, locked ?
  lock : ED[k]) and clears flags — unlocked parameters snap back to EffectData each trigger. 576/576 runs (72 rows × 8 values incl. 1.5,
  −0.25; critic: NaN, denormal, FLT_MAX, −inf) bit-exact; a lock for another effect's row lands on the *current* effect's sub (11/11).
  Whether the sequencer filters by effect type before s6 is open.
- Edit: IFPM s27 0x126c0c(this, v, k): ED[k] = v + edit flag; next s10 sends slot 29(k, ED[k]) once (480/480). k is not bounds-checked
  (static). Critic: pending edit flags survive the trigger branch, so an edit made before a trigger overwrites that trigger's lock one block
  later (emulated).
- Modulation: s13 0x126434 stores id/amount; end of every s10: if slot(id) == +0x3c and s57(id) == pending → slot 29(s58(id),
  clamp01(f32(+0x44[sub] + amount))) — the only clamp on the Insert path (330/330; critic: FX2 manager id 244 → Phaser, id 144 ignored).
- Reload: s51 0x126394 → +0x25; next s10: setFxType(s52(type Identifier)), slot 29(k, ED[k]) k = 0…5, then per-type extras (F161).
  An unexercised second path (+0x30 ≠ 0, @0x129b70/0x129e5c) calls s54 on old/new type and 0x12ac24 (listener, `likely`).
- Quirk: s6 with a −1-sub row writes +0x64 and byte +0x7f (index −1), corrupting the sub-5 lock's top byte: lock sub 5 = 1.0 then a −1 row →
  slot 14(5) gets 0x01800000 (4.7e−38). Reachability from the sequencer unknown (`guess`: not reachable).

**F161 — Master/Send managers write slot 14 immediately; per-type extras on reload.** `confirmed` (s27 emulated 240/240 each; s51 static)
  **Correction (cycle 030, F166):** the s51 extras list below is incomplete — Master/Send also send SYNC 6 to Flanger and Phaser, MMF 7, LoFi 7 and Compressor 8.
- Base s27 0x11ce58(this, v, k): ED[k] = v and immediately slot 29(k, v) (no flag, no per-block update). Identity incl. 1.25 / −0.5.
- s51 reload (Master 0x121174 / Send 0x12de8c): ED[k] → slot-14 index k (Chorus and MMF skip 4); Delay 6 and Chorus 6 = SYNC byte (Flanger
  and Phaser get none); PEQ 6/7, MMF 6, LoFi 6 = enum; Compressor 6 = byte ED+0x28, 7 = enum; Master s38 adds Compressor 8 (static only).

**F162 — Values the manager generates (index ≥ 6 and SYNC/tempo).** `confirmed` code (Insert emulated with stand-in converters); formulas open
- SYNC index 6 = float(byte ED+0x28) (Insert Chorus/Flanger/Delay/Phaser/Ducker). Enum indices = float(int name-converter(Identifier)) (IFPM
  slots 60–74): PEQ 6/7, MMF 6/7, LoFi 6/7, Compressor 7 Knee (s72) / 8 LevelDetect (s70), Ducker 10 SOURCE; written by reload and s38
  0x127928. Compressor 6 LookAhead = float(byte) via s36 0x126b68 (Insert, only when pending == 7). Converter name tables not decoded.
- s34 0x126c90 = SYNC toggle: stores ED+0x28, reads tempo 0x112a48(proc), re-maps the time value (sub 0; Ducker subs 0 and 2) between free and
  beat units through the integer range, writes it to ED and slot 14, then index 6 = float(sync); types {0,1,4,8,9} only. Exact conversion
  not derived.
- s50 0x126458(sret, this, k) returns a constant integer pair [lo, hi) per (pending type, k ≤ 5), (0, 100) otherwise; the pairs match the
  known UI domains (Distortion drive 0:81, PEQ gain −30:16, Q 1:101) → role "UI integer range" `likely`; quantisation v = (i − lo)/(hi − 1 − lo)
  `likely` (pattern in s34 / 0x3535dc, not emulated through a UI). Per-row pairs in kb/cycles/029.md C1.
- BPM (index 7) and Ducker 8/9 come from the processor (F017/F088/F156), not the manager.

**F163 — Formula hand-off and corrections.** `confirmed`
- For every Insert effect and every FxParamIndex row (and Master/Send sub-slot k) the parameter manager passes the normalised value to slot 14
  bit-exactly, so the per-effect slot-14 models (`harness/models/*.py`, F025–F129) already give normalised → coefficient. Manager-side
  exceptions: modulation clamp01, SYNC/enum/LookAhead generation, the s34 sync re-map (F162).
- F081's statement that LookAhead/Knee/LevelDetect have no FxParamIndex stays true, but its conclusion "on the device the Insert compressor is
  `likely` hard-knee peak" no longer follows (manager paths s36/s38/reload write 6/7/8; device values undecided → H047). Same for F075 /
  SendFxDelay LowCut/Spread/SYNC (H062): manager paths exist.
- F143 item 6 / H075 roles: s34 = SYNC toggle, s50 = UI integer range — not FX-lock sub-slot maps.

## Enum converters and `prj::EffectData` defaults (1.60) — cycle 030 (H083)

Evidence: kb/cycles/030.md (Worker C1–C5, Critic), `harness/H083_enum_defaults.py --out harness/out/H083` → `RESULT: 0 failed checks`
(31 PASS; h083.json 617db292…39cd, h083_report.txt 3e0d3247…d3b4, e2e_table.csv 5fad1a63…7304; critic re-run identical, plus own
probes p1–p16). Capstone + unicorn; REA has no functions at the manager slots. Real JUCE Identifier/String ctors and string pool; stand-ins
(holder layout read from code, unused Config argument, __cxa_guard / mutex stubs) shown not to affect results.

**F164 — One shared set of enum name-converters, manager slots 59–74.** `confirmed` (static decode = emulation on 41 names per slot)
- Slots 59–74 are the same words in the base (0x8430cc), Insert (0x84407c), Master (0x8437ec) and Send (0x8446d4) vtables. Even slot:
  (this, const Identifier*) → int, by pointer-compare against function-static pooled Identifiers; odd slot: int → name (inverse).
  Matching is exact and case-sensitive; Identifiers built from a C string or from a juce::String give the same pooled pointer.
- Maps (name → int; unknown/empty/"FilterTypeOff" → default):
  - s60 0x11e138 → PEQ 6 (ED+0x2c) and 7 (ED+0x30): LowShelving 0, HighShelving 1, Peaking 2, LowPass 3, HighPass 4; default 0.
  - s62 0x11e9ac → MMF 6 FILTERTYPE (+0x2c): LowPass 0, HighPass 1, BandPass 2, LowPass24 3, HighPass24 4, BandPass24 5; default 6.
  - s64 0x11d038 → MMF 7 FILTERDB (+0x30): FilterOrder1 0, FilterOrder2 1, FilterOrder4 2; default 0.
  - s66 0x11df88 → LoFi 6 FILTERTYPE (+0x2c): HighPass 0, LowPass 1, BandPass 2; default 3 (= off, F026).
  - s68 0x11d940 → LoFi 7 FILTERPOSITION (+0x30): FilterPositionPre 0, FilterPositionPost 1; default 2.
  - s70 0x11d818 → Compressor 8 LevelDetect (+0x30): LevelDetectPeak 0, LevelDetectRMS 1; default 0.
  - s72 0x11d6f0 → Compressor 7 Knee (+0x2c): CompressorKneeHard 0, CompressorKneeSoft 1; default 0.
  - s74 0x11f3f4 → Ducker 10 SOURCE (+0x2c, Insert only): SourceTrack1…16 → 0…15; default 0 (incl. "SourceTrackNone").
  (Filter names are "FilterType…" strings.) Odd slots return "FilterTypeOff" / "FilterOrder2" / "LevelDetectPeak" / "CompressorKneeHard" /
  "SourceTrackNone" for out-of-range ints; even(odd(i)) = i for every producible i.
- Feeds `confirmed` by static call-site scan (Insert s10, Master/Send s51 → 0x112924) and by real s38 / reload with non-default names
  (e.g. "FilterTypeLowPass24" → MMF 6 = 3.0, "LevelDetectRMS" → Comp 8 = 1.0, "SourceTrack16" → Ducker 10 = 15.0).
- Consequences (`confirmed` code level): the name path never yields PEQ type 5 (F038 crash type unreachable by names); Knee is only
  v ∈ {0, 1} (hard, or K = 18 dB); MMF "…24" names give 3/4/5, which the real MMF turns into filter kind 6 = **no filter** (critic emulated,
  consistent with F033) — 24 dB slope comes only from FILTERDB 0/2. Whether the UI ever stores the "…24" names: `guess` (no).

**F165 — `prj::EffectData` ctor and defaults; selecting a type (s32) copies the live effect.** `confirmed` (code + emulation)
- Ctor **0x359d1c**(this, const String& nodeName, const prj::Config&), sizeof 0x64; vt 0x8ac720 slot 0 0x371578 / slot 1 0x371ccc are the
  complete / deleting dtors. 3 callers: 0x35ceb8 (loop "InsertFx"+n, in 0x35cb30), 0x35e170 "SendFx" and 0x35e32c "MasterFx" (PatternData
  0x35de70). Config is never read.
- Layout/defaults (same for all names/contexts): +8 node Identifier; +0xc Array of 6 property binders (0x371d2c); +0x24 type = "Off";
  +0x28 byte = 0 (SYNC / LookAhead); +0x29 byte = 0; +0x2c = +0x30 = "FilterTypeOff"; six params +0x34+8k = (Identifier "None", 0.0f).
- Reloading that default: s52("Off") = −1 → setFxType(−1), 0 slot-14 calls (FX slot off).
- Manager s32 applyFxType (Insert 0x1287d4, Master 0x1237cc, Send 0x12bc84)(this, effectId): writes the type name to +0x24, calls
  setFxType(index) (0x11735c does not reset parameters), then **reads the newly selected effect's live values back** via processor slot 21
  0x1126fc (pending effect +0x90) → effect slot 15: floats k = 0…5 → +0x38+8k; SYNC/LookAhead byte = (get(6) ≥ 0.5) → +0x28 (the getter
  returns the stored truncated value); enums = odd converter(roundToInt(get(idx))) → +0x2c/+0x30 (JUCE roundToInt, 1.5·2^52 trick @0x128d50:
  round-half-even, Knee 0.5 → Hard). 0 slot-14 calls. Not a fixed per-type table (20 edited-value runs; critic: other effect current).
- Ducker SOURCE default = own track: processor slot 52 sets SOURCE = float(proc+0xa0) (F089), so s32 stores "SourceTrack(n+1)".
- Whether "new project" loads a template file instead of these ctor defaults: open (`likely` not; ProjectManager 0x33dd78 / ProjectData
  ctor 0x339448 not traced) → H085.

**F166 — Reload round trip reproduces every slot-52 default; F161 corrected.** `confirmed` (emulated, 30/30 types, three contexts)
- Fresh ctor ED → real s32(effectId) → real s51(0) (→ s10 on Insert): reload calls setFxType(type) and every index slot 52 sets receives
  its slot-52 default bit-exactly (216-row table e2e_table.csv). By construction this is a round trip; it shows converters, byte and
  rounding are lossless at the defaults. Extra sends without a slot-52 value (Insert Chorus 4, MMF 4, InsertFxDelay 3/4, Ducker 4) re-send
  the effect's own (unused) value.
- **F161 correction:** Master/Send s51 sends SYNC index 6 (ED+0x28) to Delay, Chorus, **Flanger and Phaser**; PEQ 6/7, **MMF 6/7**,
  **LoFi 6/7**; Compressor 6 (byte +0x28), 7 (s72) **and 8 (s70)** (sites Master 0x1223c4/0x1225d8/0x122864, Send 0x12f0c8/0x12f2dc/0x12f568).
  Insert sends no index 6 to the compressor.
- s51 with r1 ≠ 0 first resets every effect to slot-52 defaults (Master/Send processor vt+0xd0 = slot 52, Insert vt+0xd4 = slot 53 per
  effect), then does the same ED reload; final values = ED (critic, emulated). On that path the Insert compressor's index 6 is re-defaulted.
- Ducker SOURCE is lossy outside 0…15 (16.0 → "SourceTrackNone" → 0.0).

**F167 — Byte +0x28 carry-over: SYNC can become compressor LookAhead.** `confirmed` (code level, emulated in all three contexts)
- +0x28 is SYNC for Delay/Chorus/Flanger/Phaser/Ducker and LookAhead for the compressor; s32(Compressor) does not refresh it. A Master/Send
  Delay, Flanger, Phaser or Chorus with SYNC on, then s32(Compressor) → next reload sends Compressor 6 = 1.0 (look-ahead on) although the
  live compressor had 0. Master/Send Compressor LookAhead is also not read back by s32 (an edited 1.0 reloads as the stale byte). Insert
  unaffected. Device reachability depends on the UI callers of s32 (not traced, → H086).
- H047/H062 consequences: on a fresh project (`likely`, conditional on H085) Compressor 6/7/8 = 0/0/0 (look-ahead off, hard knee, peak) and
  SendFxDelay 3/4/6 = 0/0/0 (5 Hz floor, no spread, free time). "No path writes them" is refuted at code level (s38 sets Soft/RMS; s27/s34
  write any k / SYNC; s32/reload carry live values); whether the device UI ever introduces non-default values is open (→ H086).

## UI → parameter-manager calls: what the device UI can reach (1.60) — cycle 031 (H086)

Evidence for all items: kb/cycles/031.md (Worker C1–C5, Critic), `harness/H086_ui_manager_calls.py` + `harness/lib/armflow.py`,
`python -B harness/H086_ui_manager_calls.py --out harness/out/H086` → `Stage C: 41 cases, 0 failed`; critic re-run gave the same
four output hashes (stageA 6ec011de…500a, stageB 231be35b…d80f, stageD 4e8b6dda…222d, h086.json 7a012303…b28) and checked the
load-bearing addresses with its own capstone scripts and REA (`read_bytes 0x844280`, `search_bytes 5c223000` → 0, `xrefs 0x30225c` → []).

**F168 — UI route to the managers: ModelInterface → audio root → IEffector (manager + 0x14).** `confirmed` (static, critic re-decoded)
- View controllers, their button handlers and `ParameterBox*WidgetController` knobs call static `ModelInterface::*` wrappers with
  `ctrl+0x20` = ControllerDataReferrer. root = `[[ref+4]+0x4344]` (0x32b664); `[ref+4]+0x54` = track, `+0x74` = FX slot (1/2 Insert FX1/FX2,
  0 Send/Master).
- Insert: root (HexaTrackAudioSystem secondary vtable 0x863f74, ott −0x200) vt+0x10(track) → TrackUnit vt+0x24(slot−1) → 0x1c7890 =
  `TrackUnit+0xe8[i] + 0x14`. Send/Master: root vt+0x70 → 0x1b9510 (SendFxUnit sys+0x604, +0x88 SFPM, +0x14); vt+0x74 → 0x1b94f0
  (MasterFxUnit sys+0x608, +0x80 MFPM, +0x14); vt+0x90 → 0x1b94c0 = `CompositeFxUnit(sys+0x698) mode != 1` → Send if true, Master if mode 1.
  So every "SendMaster" UI write goes to the Send manager unless the composite FX mode is 1.
- IEffector secondary vtables (Insert 0x844270, Master 0x8439e0, Send 0x8448c8, base 0x8432c0; 27 thunks `sub r0,#0x14; b <primary slot>`):
  +0x10 → s27 setParam(v, k), +0x24 → s32 setFxType, +0x2c → s34 SYNC, +0x34 → s42 bypass, +0x3c → s36 LookAhead, +0x44 → s38
  setEnum(Identifier, which); getters +0x0c s50, +0x18 s29, +0x28 s33, +0x30 s35, +0x40 s37, +0x4c s39, +0x50 s41; +0x60/+0x64 = s46/s47.
  **s51 (reload) is not in IEffector.**
- Coverage: 762 root-fetch sites (582 `bl 0x32b664` + 180 inline `movw #0x4344`) in 509 functions → 82 IEffector calls, 31 setter calls in
  22 wrappers; the effector pointer is never stored; no direct calls to manager setters outside the thunks; 186 call sites of the wrappers
  (popup s32 sites: 26, critic count). Not covered by construction: UI → unit/track *method* → manager *primary* vcall (critic: not
  exhaustively excluded; sequencer/MIDI/LFO writers are separate paths).

**F169 — Compressor UI: Knee and LevelDetect reachable in all contexts; LookAhead only on Send/Master.** `confirmed` (static + emulated)
- Insert: FxInsertCompressorViewController::Handler_0/_1 (0x236970/0x236980 → 0x3022f4) send s38("LevelDetectPeak"/"LevelDetectRMS", which 1);
  Handler_2 (0x236a00 → 0x3025c4) toggles s38("CompressorKneeHard"/"CompressorKneeSoft", which 0). Insert s38 0x127928 lands which 0 →
  ED+0x2c → slot-14 index 7 (Knee), which 1 → ED+0x30 → index 8 (LevelDetect).
- Send/Master: FxMasterCompressorViewController::Handler_0 (0x234790 → 0x2ff434 → s36 toggle), Handler_1/_2 (Peak/RMS), Handler_3 (Knee).
  Master s36 0x120808 writes ED+0x28 and calls 0x112924(proc, 7, 6, v) when the current effect is the compressor.
- **Insert LookAhead has no UI writer:** the only Insert IE+0x3c call is in 0x30225c, which has no branch, no 4-byte pointer (any form),
  no jump-table word and no REA xref anywhere; its getter 0x3022ac is also unreferenced. The Insert compressor view has 4 handler classes
  (Master: 5).
- Handlers are bound: their vtables are stored by the controller ctors, which are called only from view factories referenced by a .data
  view table (0xb78f7c / 0xb78f74). Run-time visibility of the buttons not read (`likely` visible).

**F170 — Knob dispatch and the Send/Master Delay and Reverb knobs.** `confirmed` (code; widget run-time flags unread)
- ParameterBox base `didChangeEncoderValue` 0x2c004c (jump table 0x2c00f4) dispatches encoder n = 1…6 to box vtable slot 17+n
  (vt+0x48+4(n−1)) only if widget[n−1] exists, is visible (+0x68 bit 1) and enabled (+0xc8). Each slot = `if getFxType == gate:
  paramStep(ctx, k, kind, delta)` (Insert 0x316a10, Send/Master 0x313ecc → IE+0x10 s27); the step is integer i = current + delta·mult on the
  s50 range, mult from 0x311aa0 (a per-kind step-size multiplier: 1, 3, 4, 5, 6, 10, 36, 49, 50, 99, 100), v = (i−lo)/(hi−1−lo).
- Master/Send Delay box (vt 0x896914, gate type 0): enc 1 Time k0, 2 Feedback k1, 3 HiCut k2, **4 LoCut k3** (slot 21 0x2cfb54,
  LoCutSendMaster widget), **5 Spread k4** (slot 22 0x2cfb20, ParameterSpreadSendMasterWidget vt 0x8deea4 built by 0x4a9e78), 6 mix k5.
  SYNC: FxMaster{Delay,Chorus,Flanger,Phaser}ViewController::Handler_0 → 0x23e9bc → IE+0x2c s34(!current).
- Master/Send Reverb box (vt 0x891954, gate 2): **enc 1 PreDelay k0**, 2 RoomSize k1, 3 RevTime k2, **4 "Damping" k3** (= comb-filter LPF),
  **5 Spread widget k4** (= LR swap spread), 6 mix k5.
- Insert Delay: Time k0, Feedback k1, HiCut k2, (none at 4/5), mix k5; SYNC button FxInsert{Delay,Chorus,Flanger,Phaser}VC::Handler_0,
  FxInsertDuckerVC::Handler_1, FxLimiterVC::Handler_1 → 0x229180 → Insert s34 toggle.
- Other boxes (k per encoder 1…6): Insert Compressor 1,2,3,0,4,5; Master/Send Compressor 1,2,3,0,4,5; MMF (Insert & M/S) 0,1,2,3,—,5;
  LoFi 0…5; Distortion 0,2,3,4,1,5 (HiFreq = k3, Tone = k1, LoFreq = k2); Master/Send 2-band EQ 2,0,1,5,3,4; Insert Ducker 0,1,2,3,—,5.
  Box ↔ layout pairing `likely`. Insert 2-band EQ, Chorus, Flanger, Phaser layouts not tabulated (k lists in stageB_callers.tsv).
- Labels are PNG skin images (`pNNNN_…png`), not strings; names above are widget class names.

**F171 — Enum values the UI sends.** `confirmed` (static + emulated)
- MMF FILTERTYPE: LowPass / HighPass / BandPass / Off only (selector 1/0/2/else); FILTERDB: FilterOrder2 / FilterOrder4 only. The "…24"
  filter names and "FilterOrder1" are referenced only by the converters (0x11d1e8, 0x11e9ac, 0x11d038, 0x11de00) and the ED ctor 0x359d1c.
- LoFi FILTERTYPE: LowPass / HighPass / BandPass / Off; POSITION: FilterPositionPre / Post.
- PEQ band type (Insert and Master/Send, which = band): selector 0 HighPass, 1 LowPass, 2 Peaking, 3 HighShelving, 4 LowShelving; 5 → no
  call (the F038 crash type is unreachable from the UI).
- Ducker SOURCE: n → "SourceTrack(n+1)" for 0…15, else "SourceTrackNone".
- FX popup (FxSelectPopupWidgetController handlers → s32): Off, Chorus, Flanger, Phaser, Distortion, LoFi, Delay, Reverb (Send/Master only),
  2-band EQ, Filter, Compressor, Ducker (Insert 20; Send/Master 19, beyond the M/S table → `likely` Off); the other handlers call no type
  setter. Handler ↔ item text by list order: `likely`.
- F167 carry-over: both UI steps exist (SYNC on a Send/Master time effect, then COMPRESSOR from the popup); the processor receives the stale
  byte only at an s51 reload, whose callers are not UI (not traced).

**F172 — UI bypass and FX ON/OFF.** `confirmed` for the code chain; trigger attribution `likely`
- `ModelInterface::setEffectBypassMode` 0x2f8114 (called from TrackMenuViewController code 0x29bb40, 0x29c004) → IE+0x34 → s42 0x11cfc8 →
  (manager byte +0x24 guard) → 0x1129b4 at 0x11cfe4 = the F157 132-sample bypass crossfade.
- The +0x9d FX ON/OFF setter/reader thunks (IE+0x60 s46 0x11caf4, IE+0x64 s47 0x11cae0) have **no** calls on the UI root route.
- s38/s36/s42 return early when manager byte +0x24 = 0.

## Send FX type selection and SendFxUnit children — cycle 032 (H020)

Evidence for F173–F174: kb/cycles/032.md (Worker + Critic), `harness/H020_send_fx_types.py`
(`python -B harness/H020_send_fx_types.py --out harness/out/H020` → `RESULT: 22 passed, 0 failed checks`; h020.json 39fe0785…59b4,
h020_report.txt 170c4893…f4b6; critic re-run byte-identical, plus independent capstone/REA reads).

**F173 — The Send FX can be any of the 10 types or Off; Send and Master type selection are identical.** `confirmed` (static + emulated)
- SFPM (vt 0x8446d4) s32 0x12bc84(this, effectId): idx = s53(effectId) (0x12acf0: `effectId ≤ 17u ? T[effectId] : −1`, T = 0x8445c8, identical
  to Master 0x8436e0); if idx == processor pending (vt+0xc0 0x119980) → return with nothing written; else jump table 0x12bcc4: case c → ED+0x24 =
  name, setFxType(c) (SendFxProcessor vt+0xbc 0x11a254); names 0 "Delay", 1 "Reverb", 2 "Chorus", 3 "Flanger", 4 "FxType_2BandEQ",
  5 "FxType_MultiModeFilter", 6 "FxType_LoFi", 7 "FxType_Compressor", 8 "FxType_Distortion", 9 "FxType_Phaser"; default "Off" → setFxType(−1).
  s52 0x130668 (name → index, used by reload s51 0x12de8c) and s54 0x12ad08 (inverse of s53) give the same set. Nothing is rejected, remapped or
  absent compared with Master s32 0x1237cc / s52 0x125b70 (which compares "Delay" twice, harmless).
- setFxType 0x11a254 has no direct calls; its only data reference is vt slot 0x842dfc. Of all `ldr rX,[rY,#0xbc]; …; blx rX` sites in .text
  (79 by the critic's wider window; worker 77), only SFPM s32 (11) and s51 (11) reach the Send processor; the rest are other managers' own
  processors or non-FxProcessorBase objects (exclusion of every indirect site `likely`). The SendFxProcessor exists once (ctor 0x11bbe4, one
  call site 0x1b33f4); its pointer is held only at SendFxUnit+0x8c and SFPM+0x1c.
- Emulated (real SFPM s32 on the real SendFxProcessor, effectId −3…24 + 2 edge values, 2 start types): 60/60 Send and 60/60 Master runs match
  the static reading; s52 name lookups 23/23 and s51 reloads 23/23 match.
- UI: all 20 FxSelectPopupWidgetController handlers emulated in Send context feed SFPM s32 → all 10 types + Off are reachable. Popup
  onTransitioned 0x1f0bec maps the current effectId back to each handler's own row (jump table 0x1f0c40), so handler ↔ row ↔ effect is
  `confirmed` in code (printed row text = skin images, `likely`). Refines F171.
- Default: after the real ctor the Send processor is Off (current = pending = −1); the ED ctor default "Off" reloads as setFxType(−1). A new
  project's Send FX starts Off: `confirmed` in code, `likely` on the device (H085/H088 deferred).
- `likely` (critic's own read, cycle 032, not re-tested by the worker): popup row visibility per context is set by 0x3c5bcc (hide all via
  0x3beb44, then 0x3c5a5c per row; vt+0x2c = setVisible `likely`): Send/Master shows Off, Delay, Reverb, Chorus, Flanger, EQ, Filter, LoFi,
  Compressor, Distortion, Phaser (no Ducker row); Insert shows Off + 9 types + Ducker (no Reverb row).
- Milestone consequence: every Send type already has a bit-exact model (F026–F031, F032–F037, F038–F044, F045–F050, F057–F062, F063–F068,
  F069–F080, F081–F094/F087, F115–F120, F121–F127) and the Send processor shell is bit-exact for all 10 types (F154–F156).

**F174 — SendFxUnit children: one processor, a peak meter and the return fader; no further processors.** `confirmed` (static, RTTI)
- Ctor 0x1b3314 zeroes +0x80…+0x90 then stores: +0x80 @0x1b3390 new(0xa0) 0xe64e4 **PeakDetectorUnit** (vt 0x83c7a0); +0x84 @0x1b33d0 new(0x20)
  0xe5748 **LevelMeterSourceUnit** (vt 0x83c460); +0x8c @0x1b3408 new(0xb0) 0x11bbe4 **SendFxProcessor** (vt 0x842d40); +0x88 @0x1b3448 new(0x40)
  0x130bd4 **SendFxParameterManager** (vt 0x8446d4); +0x90 @0x1b347c new(0x98) 0xe9e5c **VolumeFader** (vt 0x83e380). Refines F104.
- No later re-pointing found in SendFxUnit vtable functions, after 109 `[…,#0x604]` loads, or in CompositeFxUnit code (`likely` overall; sweep by
  the worker only). SendFxUnit current-type getter 0x1b357c → processor slot 46.

**F175 — Master/Send MultiModeFilter (index 5) is the Insert MMF object: same ctor, arguments, vtable, setup and defaults; `mmf.py` covers it unchanged.** `confirmed` (static + emulated; scope 44.1 kHz, block 64, host libm)
Evidence: `kb/cycles/033.md` (Worker + Critic, all 5 criteria CONFIRMED). Harness `harness/H027_master_mmf.py`, run
`python -B harness/H027_master_mmf.py --out DIR --jobs 6` → `RESULT: 0 failed checks`; worker (two runs) and critic re-run
byte-identical (report 0255185a…a9f5, json bdbc7a74…bb11, c3_outputs.f32 fb77c6e9…d04c, c4_outputs.f32 ebeb8516…f451).
- MMF ctor 0x109e8c has exactly three call sites, one per processor ctor: Master @0x115084 (0x114bc0), Insert @0x118ee4 (0x118b0c), Send
  @0x11c0b0 (0x11bbe4); no pointer to it exists in the file. The build window is word-identical in all three: new(0x4a0), fs 44100, block 64,
  no extra argument; EffectBase ctor 0x1067d8 gets mode 0 (ctor falls back to 44100 if fs ≤ 0). vptr 0x8420b8 (`15MultiModeFilter`) is
  stored only by the MMF ctor/dtor, so all 32 slots (14 0x105d24, 18 0x106de4, 22 0x1059b0, 25 0x108ee4, 26 0x107b30, 27 0x107fa8) are shared.
- Post-construction calls identical: slot 22(e, 0), then 0x106c7c(e, 1, 10.0f) (Master @0x115468 / @0x115564). Default cases Insert s53
  0x117d08, Master s52 0x114110, Send s52 0x11aca4 make the same 10 getter calls and slot-14 sequence 0,1,2,3,5,6(0),7(1.0f) (Send inlines
  the shared tail). prepareToPlay/enable do not touch the object. The canonical object graph (0x4a0 object + 101 reachable heap objects,
  4,770 bytes, pointers canonicalised) is word-identical across Insert, Master and Send; the critic showed one slot-14 write gives a 1-word diff.
- Defaults are **identical**, not "different" (corrects the H027 wording; agrees with F156) and equal `mmf.INSERT_DEFAULTS`.
- Real Master 0x112acc / Send 0x119994 with the ctor-built index-5 object vs `fx_processors` + `effectbase` + `mmf.py`: 102/102 cases bit-exact
  (17 non-default settings: every UI kind LP/HP/BP/Off × Order2/4, cutoff/Q/mix/gain/glide extremes, one mid-run change, one route through the
  real manager base s27 0x11ce58 (48/48 calls → one slot-14(k, v) each), one on/off/type switch exercising slot 27; × noise/sine/impulse × 200
  blocks), plus 302 MMF state fields every 10 blocks (0 diffs). Critic's own fuzz: 16/16 random Master/Send cases with mid-run changes bit-exact.
  Negative controls (cutoff +1e-6, a poked state word, four wrong model variants) all fail.
- Values the UI never sends (Master): 28/28 bit-exact; FILTERTYPE 3/4/5/7/−1 = Off; FILTERDB 0 = 3 = Order4; fractional values truncate
  (2.7 / 1.9 → BPF Order2). The two-biquad kinds 3–5 are UI-reachable via Order4.
- Not run: fs 48 kHz; the s51 enum route for FILTERTYPE/FILTERDB (set via slot 14 here; F166 covers the reload); s27 on a stand-in manager
  object around the real code. H029 (host libm) and H038 (FTZ) caveats unchanged.

## Cycle 034 — H079 the +0x9d setter 0x1129bc (FX ON/OFF start mode): modelled, but dormant in 1.60 (critic-confirmed)

Evidence for F176–F178: `kb/cycles/034.md` (Worker, Critic, Worker round 2, Critic round 2). Harnesses `harness/H079_fx_onoff.py`
(`python -B harness/H079_fx_onoff.py --out DIR --jobs 6` → `RESULT: 0 failed checks`, 13 PASS; worker two runs and critic re-run
byte-identical: h079_report.txt f319f458…ae96e, h079.json 93d6b544…7726, c3_outputs.f32 ccc863bc…3db7c, c3f_outputs.f32 90128ff2…f128c,
c4_traces.json c38a9542…25f5d9) and `harness/H079_r2_propagate.py` (`--out DIR` → `RESULT: 0 failed checks`, 9 PASS; report 872829e0…953b,
json bb9ed35e…4cbb, reproduced by the critic). Model: `tools/fx/fx_processors.py` `_FxProcessor.set_start_mode(v)` / `get_start_mode()`
(additive); H077 re-run with the extended model keeps all five recorded hashes.

**F176 — 0x1129bc semantics and model.** `confirmed` (capstone, asserted per instruction; emulated bit-exact)
- 0x1129bc(proc, v): if pending-effect pointer +0x90 == 0 → return, **nothing stored** (value lost while Off); else `strb v → +0x9d`
  (+0x9e read before the store); if +0x9e ≠ 0 (disabled) → return; else v ≠ 0 (full 32-bit test) → (+0x90) slot 7(e, 0), v == 0 → slot 8(e).
  No old-value check (re-sending calls the slot again). +0x90 is the current effect in steady state and the new pending one during a type
  change, never the fading old one.
- Thunks: 0x11caf4 = `r0 = [mgr+0x1c]; b 0x1129bc`; reader 0x11cae0 = byte [[mgr+0x1c]+0x9d]; IEffector adjustors 0x11caec / 0x11cad8 =
  `sub r0,#0x14; b`. They are primary slots 46/47 (vt+0xb8/+0xbc) of FxParameterManagerBase 0x8430cc, Master 0x8437ec, Insert 0x84407c,
  Send 0x8446d4 (+ construction vtables 0x843b4c / 0x8443e4 / 0x844a34) and IEffector +0x60/+0x64 (slots 24/25) of 0x8432c0 / 0x8439e0 /
  0x844270 / 0x8448c8. FPMB: ITriggerAndParameterReceiver at +0, IEffector at +0x14; no JUCE base, so nothing else can dispatch to them.
- +0x9d accesses in processor/manager code (ARM word sweep; Thumb/ldm/register-offset forms not swept): ctor 0x112914 (writes 1), setter
  0x1129d0, readers Master pB 0x112c38, Insert pB 0x116b78, Send pB 0x119b44 (slot 7/8 choice) and 0x119b84 (input-mute flag, `eor #1`),
  reader thunk 0x11cae4.
- Real setter (via real vtable words s46 / IE+0x60 and direct) mid-run on real Insert/Master/Send processors vs the extended model: worker
  70-case matrix (schedules: enabled 1→0/0→1, while disabled, during a type change, during fade-out to Off / disable, Off; types incl.
  SendFxDelay, SendFxReverb, InsertFxDelay, both compressors, Chorus, LoFi) + 12 fuzz cases; critic 15 more cases (Flanger, PEQ, MMF,
  Distortion, Phaser on all three processors, with bypass, tempo, type-change and triple-set schedules): **97/97 bit-exact** in outputs,
  processor state, both readers, slot-call log and wrapper state every block. 11 worker + 3 critic wrong-setter mutants all fail.
- Model valid for v ∈ {0, 1}: with v = 2 the Send input MuteSmoother 0xe8050 gets 2 ^ 1 = 3 and re-arms every block (the model normalises).
  Nothing in 1.60 sends any value (F178).

**F177 — What +0x9d does to the signal.** `confirmed` in emulation (44.1 kHz)
- +0x9d = 0 → slot 8 (F145 record R4, gate state 2), **not** an "instant start" (corrects the H079 wording): "effect off, tails ring out".
  Gate mode 0 effects (Chorus, LoFi, compressors, …): input keeps reaching the effect, wet output fades out → output == dry input
  bit-exactly from sample 147 (Master/Insert); internal state (envelope, LFO) keeps tracking. Mode 1 (delays, reverb): effect input closed,
  dry at unity, existing tails decay normally.
- Send additionally mutes its input (132 samples @44.1 k): non-time effects → exactly 0.0 from sample 147 (132 Compressor); delay/reverb →
  only the decaying tail.
- +0x9d → 1 → slot 7: wet fades back in; Master/Insert mode-0 effects equal the untouched run bit-exactly from block +3; Send and time effects
  keep a lasting difference (state saw silence / delay memory).
- A type activated while +0x9d = 0 starts with slot 5 + slot 8 (output dry on Master/Insert, 0.0 on Send) until slot 7.
- Distinct from bypass +0x9c (132-sample crossfade to the dry copy, effect still running, F157) and disable +0x9e (slot 6 fade, tails cut,
  Send silent, F155).

**F178 — Nothing in 1.60 drives +0x9d; the UI "FX ON/OFF" is a logging stub.** `confirmed` (static)
- No direct branch, pointer word (incl. Thumb-bit variants) or member-function pointer to 0x1129bc / the thunks other than the vtables; no
  `bx rN` (except `bx lr`), `ldr pc` or `mov lr,pc` forms exist in .text.
- Type propagation from the only manager allocation sites — Master 0x1b1dcc (MasterFxUnit ctor 0x1b1d30 → +0x80), Send 0x1b3434 (SendFxUnit
  ctor 0x1b3314 → +0x88), Insert 0x1bbda0 (TrackUnit factory 0x1bacec → TrackUnit +0xe8[slot] via 0x1c9874, HexaTrackAudioSystem +0x65c[n],
  Sequencer [[sys+0x598]+0x1d0] table) — through registers, stack, arguments, returns, arrays, holders (sys+0x604/+0x608/+0x620, 0x1aa808)
  and getters (0x1b1e58, 0x1b3564, 0x1c7890, 0x1b94f0, 0x1b9510): 1,584 functions, 215 manager/IEffector call sites, **0** reach vt+0xb8/
  +0xbc or IE+0x60/+0x64 (positive control: all 56 manager → processor setFxType calls found). A type-free net over 378 candidate sites: 0
  hits. Critic closed the gaps: 1,067 capstone-truncated function tails (5 unanalysed sites checked by hand), one stack-spilled site
  0x60fec4 (library `this`), member-function-pointer listener calls (thunks not in listener sub-vtables, no matching PMF). Library-area sites
  rest on the structural argument (FPMB has no JUCE base). 0x1aa808 calls manager slot 9 (+0x9e enable/disable path), not +0x9d.
- `ModelInterface::setSendMasterFxOnOff` 0x300e30 and `setInsertFxOnOff` 0x304470 only format "<name>(<v>)" (String(int) 0x62d868 →
  0x61df88) and print it (0x647ca0); no indirect call. Getters 0x300eb4 / 0x3044f4 = `mov r0,#0; bx lr`. Handlers
  FxMasterViewControllerBase::Handler_2 0x23da9c and FxInsertViewControllerBase::Handler 0x228734 toggle a display byte (+0x13d / +0x139)
  and call the stub. A skin graphic `f_1_p5187_fxonoff` (0x8d9f20) is attached to FxPanelWidget [this+0xcc] in 0x493650 / 0x4944b0, so the
  button is `likely` drawn; whether it is shown on the device is unread.
- Consequence for the milestone: +0x9d stays at its ctor value 1 on Insert, Master and Send (`confirmed` static; that no other code writes
  +0x9d rests on the F176 region sweep). `set_start_mode` is a documented, modelled, dormant path.

## Cycle 035 — H080 Insert FX bypass sources: per-scene EffectData "bBypass", track-menu F5/F6, re-applied on scene change (critic-confirmed)

Evidence for F179–F182: `kb/cycles/035.md` (Worker, Critic). Harness `harness/H080_bypass_sources.py`
(`python -B harness/H080_bypass_sources.py --out DIR --jobs 6` → `RESULT: 0 failed checks`, 39 PASS; worker two runs (different
`--jobs` / PYTHONHASHSEED) and critic re-run byte-identical: h080_report.txt ec41f530…4980, h080.json 8b044d06…c9f9, c4_outputs.f32
9020d25d…b074, prop/h079_r2.json bb9ed35e…4cbb (= cycle-034 hash), prop/h079_r2_report.txt 872829e0…953b; harness file ee5183bb…7727).
REA `xrefs` 0x1129b4 / 0x11cfc8 / 0x129b34 / 0x2f8114 / 0x2f81d8 (worker and critic). No model file edited.

**F179 — The bypass setter 0x1129b4 has exactly two callers; both are Insert-manager code.** `confirmed` (static)
- Only direct `bl` 0x11cfe4 (in s42 0x11cfc8) and 0x129e58 (in InsertFxParameterManager s10 0x129b34, Insert vt 0x84407c slot 10, word
  0x8440a4 its only reference); no pointer word (incl. |1), literal or movw/movt pair; REA agrees. Limit: Thumb / register-offset forms not swept.
- s42 0x11cfc8(mgr, v): manager +0x24 = 0 → return, nothing written; else 0x1129b4([mgr+0x1c], v) (own processor, v unchanged), then
  EffectData[*[holder+8]]+0x29 := v (holder [mgr+0x20] = `SwitchableObject<prj::EffectData,17>`; index > 16 asserts and still stores). Same
  function in slot 42 of all 7 manager vtable groups; IE+0x34 adjustor 0x11cfc0 (`sub r0,#0x14; b s42`) in the 4 IEffector sub-vtables.
- s43 0x11cf58 (IE+0x38, adjustor 0x11cf50): returns 0 if +0x24 = 0, else the stored ED+0x29 (not processor +0x9c).
- s10 0x129b34 (per-block update, called only by TrackUnit vt slot 5 0x1ca58c @0x1ca988, every block for each insert slot): +0x24 = 0 →
  return; +0x25 = 0 → no reload; else +0x25 := 0, setFxType(s52(ED type)), slot-29 values, then 0x1129b4([mgr+0x1c], ED[cur]+0x29) at
  0x129e58. Every reload path reaches 0x129e58 (post-dominance, incl. type Off; critic re-checked with out-of-range edges reported: 0; s10
  has one exit 0x129f3c).

**F180 — Insert bypass state is the project property `bBypass` = prj::EffectData +0x29, one per scene per insert slot.** `confirmed`
(static) for the binder and the scene index; writer list `likely`-exhaustive
- Writers of ED+0x29: s42 @0x11d00c (UI), ED ctor 0x359d1c @0x359f68 (:= 0), property binder load 0x3589e8 @0x358a94 (key "bBypass"),
  reset 0x3568fc, copyFrom 0x3554f0; save 0x35859c and print 0x356f60 only read it. 31 other `strb …,#0x29` sites carry no EffectData
  marker (`likely` other classes); no wider `#0x28` store in EffectData code (critic).
- The holder index `*[holder+8]` is the **scene** index: ScenePatternSwitcher ctor 0x18b8bc stores +8/+0xc/+0x10 from [owner+0x8c/+0x90/+0x94]
  and is stored at owner+0x9c; ScenePatternDataSet ctor 0x183504 stores [owner+0x90] at +8; both `SceneSwitchable<prj::EffectData>`
  (vptrs 0x859be8 / 0x859c00) take holder+8 := dataset+8 (critic, `confirmed` for every SceneSwitchable<EffectData> built there; that
  [mgr+0x20] is one of them and +8 is never re-pointed: `likely`).
- 17 objects = 16 scenes + 1 dummy: `SwitchableObject<prj::EffectData,17>::setToReferToDummy` 0x186cc8 (vt slot 2, words 0x859bf0 /
  0x859c08; no direct caller) sets T[i] := 16 (b ≠ 0) or i in the table at holder+0x50, changing which EffectData s42 writes and s43/s10 read.
  Its callers are not traced (H091, deferred).

**F181 — Who sets the manager inputs, and when the stored bypass reaches the processor.** `confirmed` (static + emulated)
- Manager +0x24 ("attached / data valid"; s10, s36, s38, s42, s43 do nothing when 0): 14 writers, all in manager code (byte and, per critic,
  word/half/double/stm sweeps; propagation hook of all widths finds none outside manager code; 2 hits at 0x5f9e24 / 0x5f9ea0 are
  juce::AudioProcessor ctor/setter on the FX units, over-approximations): base ctors 0x11fa0c / 0x11fad4 (:= 1, +0x25 := 0, +0x38 :=
  objectIndex); ISceneEditListener slots (FxParameterManagerBase +0x10) := 0 (0x11c9e8 also fades the pending effect out via processor vt+0xc8
  0x112780; 0x11ca40, 0x11ca54, IFPM 0x126360 / 0x126374 / 0x126388) or := 1 + s51(1) (0x11ca18; 0x11cbd4 / 0x11cc08 if [arg+8] == +0x38;
  IFPM 0x126a74 / 0x126ab4 / 0x126af4 if edited track == +0x40 or −1). Slot ↔ SceneEditor event names `guess`.
- +0x25 (reload request): ctors := 0, s51 0x126394 @0x1263b8 := 1 (f ≠ 0 first calls processor vt+0xd4 0x117280, slot-52 defaults), s10 := 0.
  s51 is reached only from the listener slots above and IScenePatternSwitchListener slot 2 0x11cc3c (FxParameterManagerBase +0xc).
- `ScenePatternSwitcher::switchSync` 0x18bbb8 stores the new scene/pattern index, then calls each listener: scene changed → vt+0xc (r1 =
  old scene; default 0xc6e98 → slot 2 0x11cc3c: if +0x24 and old ≠ current → s51(0)); same scene → vt+0x14 (→ `bx lr`, no reload).
  So the stored bypass (with the type and slot-29 values) is applied **on a scene change, not on a pattern change within a scene**, and at
  the end of SceneEditor edits, at the start of the next audio block. Project-load → reload sequence not traced (`likely` via these routes;
  0x18a144 / 0x18a384 rebuild data set and switcher).
- Emulated (real InsertFxProcessor 0x118b0c + IFPM ctor 0x12864c + real EffectData ctor, real IE+0x34 / s42 / s32 / s27 / listener slots via
  ctor-written sub-vptrs / s51 / s10 / processBlock; stand-ins: UI handlers, ModelInterface, switchSync, holder, binder): 14/14 cases bit-exact
  against `fx_processors.py` (243,200 samples, 6 types + Off; output bits, processor state incl. +0x9c, slot events, wrapper state), 14/14
  hand-derived +0x9c / ED+0x29 expectations met (UI on/off; s42 ignored while +0x24 = 0; reload re-applies bBypass; scene switch changes type
  and bypass; pattern switch and stored byte without reload change nothing). Refuted alternatives (6/6 fail): model without the logged bypass
  calls; "stored bBypass applied every block".

**F182 — The device bypass control and Master/Send.** `confirmed` code chain; on-screen naming `likely`
- `TrackMenuViewController::onFunction5Button` 0x29bd94 / `onFunction6Button` 0x29bb0c → `ModelInterface::setEffectBypassMode` 0x2f8114(ref,
  slot 0 / 1, s43-result XOR 1) → root vt+0x10(track = [[ref+4]+0x54], current track) → TrackUnit vt+0x24(slot) → IE+0x34 → s42: a toggle
  of FX1 (F5) / FX2 (F6) bypass of the current track. Only for track-type cases 0/1 (`likely` Sample/Thru) and only while the per-track byte
  model+0x40e1+track (getter 0x2f81b8) is set, else the buttons open a view; cases 2/3 (`likely` MIDI): F5 toggles `setMidiCcBypassMode`,
  F6 nothing.
- The per-track byte is written only by 0x2f81d8 (`byte := !byte`), from 0x2d5684 (`GlobalSectionTrackMenuWidgetController` Handler_1,
  vtable word 0x897b0c) and unreferenced 0x2d68d8; refresh 0x49f4c4 lights widget +0xd0, built in 0x49ea88 from skin
  `ot_1_p0021_indicator` next to a part from `f_1_p0172_bypass` → `likely` a "BYPASS" mode button in the track menu (device not inspected).
- Only Insert managers are reachable from IE+0x34; Master/Send s10 is `bx lr`, their s51 has no 0x1129b4 route. A real s42(1) on Master
  distortion / Send LoFi / Master LoFi writes +0x9c and bBypass but the output is bit-identical without it: **inaudible** (F157).
- Consequence for the milestone: a user "FX bypass" on an Insert is the F157 132-sample (44.1 kHz) crossfade to dry with the effect
  still running, toggled live from the track menu or switched per scene. Not +0x9d (F178), not the FX ON/OFF stub.

## Cycle 036 — H082 SYNC toggle conversion, UI step law, SHIFT fine steps, on-screen formatter (critic-confirmed, two rounds)

**F183 — SYNC toggle s34 (Insert 0x126c90, Master 0x1208ac, Send 0x12b3b4): what it does.** `confirmed` (static + emulated, 9233 + 9100 cases)
- Prologue: manager +0x24 == 0 → return; else `strb` direction → ED+0x28 first (old SYNC byte never read; the UI passes !current), type via
  processor vt+0xc0, tempo T = 0x112a48 = max(f32(provider double), 0.5) (Insert adds a dead `T < 0.1 → 0.1`). Cases: Insert {0,1,4,8,9},
  Master/Send {0,2,3,9}; other types return with no call. Free→sync and sync→free use different helpers/literals for every type.
- The stored v is turned into the integer step of the mode being left, i = roundToInt(f32(lo) + f32(v·f32(hi−1−lo))), converted to
  Hz / ms / beats at the tempo of the press, snapped to the nearest step of the new mode, output v' = f32(f32(j−lo')/f32(hi'−1−lo'))
  clamped to [0,1]; v' → ED+0x38 (Ducker RELEASE also ED+0x48) and slot 14 index 0 (Ducker 0 and 2), then index 6 := f32(sync).
- Arithmetic (all float32, non-fused): rate free→sync y = f32(T/60)·f32(1/Hz) beats/cycle, sync→free Hz = f32(T/60)·f32(1/beats);
  delay free→sync beats = (ms·f32(T/60))·0.001, sync→free ms = (beats·f32(60/T))·1000; Ducker sixteenths = ms·f32(f32(T·0.004)/60),
  ms = (sixteenths·f32(60000/T))·0.25. Free steps by JUCE roundToInt (round-half-even, exact halves emulated 62.5→62, 187.5→188);
  Ducker by truncation (`vcvt.s32.f32`) to 0.1 ms. Nearest division by linear midpoints f32(f32(f_k+f_{k+1})·0.5) (asc chains `x < mid`,
  desc `x > mid`); Ducker by binary search, first k with T[k]+1e−4 > x. Stored v is clamped to [0,1] before conversion for all types
  except the Ducker. Double-precision tempo factor refuted (20 discriminating cases at 0.1-BPM tempos).
- In sync mode the effect follows tempo changes itself; a free value produced by SYNC off is frozen at the press-time tempo.
  Round trip off→on→off returns the start only when it sat on a division (e.g. @120 BPM Chorus 8/100 steps, Insert Delay 6/991);
  on→off→on is exact unless the free range clamps (@20 BPM Insert Delay 2/6, Send Delay 5/8, Ducker 83/128 and 77/128).
- Model: `tools/fx/sync_convert.py` (`s34(ctx, case, ed0, ed2, sync, bpm)`, `convert(fam, v, sync, T)`), bit-exact on all
  emulated cases. Out-of-range Ducker inputs (not UI-reachable, `likely`) are not modelled.

**F184 — Seven time-parameter families (BasicParamSpec helpers, shared by s34, s50, the UI step code and the formatter).** `confirmed`
| family (used by) | free [lo,hi) → value | sync range | sync divisions (index 0…n−1) |
|---|---|---|---|
| chorus (Ins 0, M/S 2) | 1:101, i·0.1 Hz | 0:10 | beats/cycle 16,8,4,2,1,3/4,1/2,1/4,1/8,1/16 |
| flanger (Ins 1, M/S 3) | 1:101, i·0.01 Hz | 0:7 | 64,32,16,8,4,2,1 |
| phaser (Ins 8, M/S 9) | 1:1001, i·0.01 Hz | 0:12 | 64…1,3/4,1/2,1/4,1/8,1/16 |
| insert_delay (Ins 4) | 10:1001, i ms | 0:6 | beats 1/8,1/4,1/2,3/4,1,2 |
| send_delay (M/S 0) | 10:4001, i ms | 0:8 | 1/8,1/4,1/2,3/4,1,2,4,8 |
| ducker_attack (Ins 9 sub 0) | 0:10001, i·0.1 ms | 0:128 | sixteenths table 0x8a9b20 (= ducker.TA) |
| ducker_release (Ins 9 sub 2) | 1:80001, i·0.1 ms | 0:128 | sixteenths table 0x8a9d20 (= ducker.TR) |
- Fraction tables are .bss u16 num/den at 0xf61f18 + 4·idx (chorus 0xf61f50, flanger 0xf61f78, phaser 0xf61fcc, insert delay 0xf61fb4,
  send delay 0xf61f94), filled by .init_array code 0x6cbe0…0x6ce8c. Real s50 after a toggle returns the entered mode's range (28/28; s50
  tests the effect's live SYNC > 0.5 via 0x11295c). Effect quantity of every free step equals the existing slot-14 models.

**F185 — UI knob step law (0x316a10 Insert, 0x313ecc Send/Master) and the SHIFT fine step.** `confirmed` code (emulated 1920 + 720 +
1176 cases); physical premises `likely`
- i = roundToInt(lo + v·(hi−1−lo)) on the family range of the current mode, i' = clamp(i + m·delta, lo, hi−1) with the clamp bounds from
  IE s50 (critic: the family range is used for i and the output, the s50 range only as clamp bound), output v = (i'−lo)/(hi−1−lo) → s27.
- m = 1 in sync mode. In free mode: Send/Master m = 1 iff SHIFT held; Insert m = 1 iff (DM+0x60 == 0 and DM+0x64 ≠ −1 ? DM+0x68 : SHIFT held);
  otherwise m = 0x311aa0(kind, i, delta) (coarse: chorus/flanger/phaser 4–5 steps, Insert Delay 10/50 ms, Send Delay 10/50/100,
  Ducker attack 49/50/100, release 99/100/1000).
- DM = `ControllerDataManager` (only new(0x4350), 0x56f8b0; vtables 0x932890 / 0x9328a8; ctor +0x60 = 0, +0x64 = −1, +0x68 = 0).
  DM+0x434c = `UIInputManager` singleton *(0xf6e380) (ctor 0x556044); `0x5560bc(cfg, i)` = hardware button i of 37; item 6 = button id 6
  = **SHIFT** (factory-test map 0x54a9c8 / string "SHIFT"; TransportController 0x1d1828 handles ids 6…9); vt+0xc 0x55ae54 = held state,
  written only by setRawState 0x55b26c from the panel input routine 0x55767c.
- DM+0x64 = held step index (SequenceModeStepController 0x1e2c64, −1 on release); DM+0x60 = active step sub-controller (StepController
  0x1e3924 / 0x1e3bd0; 0 = sequence mode); DM+0x68 toggled by each SHIFT press while a step is held (0x1d1a18), cleared on step release
  (0x1e30b0). No preference, project field or file load writes them (sweep coverage in kb/cycles/036.md; residual indirect-writer gap `likely` none).
- Reachable values: every integer step of the current mode's range — sync mode with the encoder alone; free mode while holding SHIFT, or
  with a step held after one SHIFT press; encoder alone in free mode moves on the coarse grid. `likely` (not traced): the panel delivers
  SHIFT as id 6 (0x55767c not emulated) and one detent gives |delta| = 1 (no acceleration).
- Encoder path 0x2c004c (one VC class checked) passes delta unchanged to the per-knob handler → step routine; no SHIFT intercept.
  ModelInterface helpers 0x3041fc (SHIFT held, 11 callers) / 0x304224 (step held ? DM+0x68 : SHIFT, 14 callers) use the same fine rule elsewhere.

**F186 — On-screen value formatter.** `confirmed` (address and format strings); per-caller role `likely`
- 0x314d4c (Insert) / 0x31235c (Send/Master) return the current step i and build the text: free rate "%.1f" (chorus) / "%.2f" (flanger,
  phaser) Hz; sync rates and delays "%d/%d" (fraction num/den); Ducker "%.1f" ms free / "%.2f" sixteenths sync; free delay ms via
  0x62d868(String*, int) (`likely` juce::String(int)). ~280 / ~300 ViewController call sites + one in each step routine. Unit suffixes not
  traced (`guess`: skin images, F170).

Evidence for F183–F186: `kb/cycles/036.md` (Worker, Critic, Worker round 2, Critic round 2). Harnesses `harness/H082_sync_convert.py`
(`python -B harness/H082_sync_convert.py --out DIR` → `RESULT: 0 failed checks`, 23 PASS; worker two runs and critic re-run
byte-identical: h082_report.txt 50d669ad…12c3, h082.json a34baa5c…a30d, c2_cases.csv 74787aed…2e7a2f) and `harness/H082_step_mode.py`
(`--out DIR` → 0 failed checks; step_mode_report.txt 3ea3ef08…0602, step_mode.json 91315ff0…bb03, worker ×2 and critic identical).
Model `tools/fx/sync_convert.py` (new, additive). Critic own fuzz: 9100 s34 cases, 720 step cases, 0 mismatches.

## Analog-filter (DSF) loop position in the track path (1.60) — cycle 037, findings F187–F191

Evidence for F187–F191: `kb/cycles/037.md` (Worker, Critic). Harness `harness/H052_dsf_loop.py` (`python -B harness/H052_dsf_loop.py
--out DIR` → `RESULT: 0 failed checks`, 9 PASS; worker ×2 and critic re-run byte-identical: h052_report.txt 0c5c2bc7…04d3, h052.json
5772983c…1c30, sorted 14-file f32 df86e5fe…803c). Model additions in `tools/fx/track_mix.py` (`OutputSelector`, `ROUTING`, `RoutedTrack`,
`dsf_apply`; additive, H009 F101 hashes 9f1dc126…cda6 / 47a28721…73d0 / 98769095…631d reproduced by worker and critic). Real code emulated:
TrackUnit::processBlock 0x1ca58c, OutputSelector 0xe6b8c / setSelection 0xe6ff4 with the firmware ctor arguments, slot 101 0x1ca218 → 0x1ca0dc,
thunk 0x1ca210, DaveSmithManager apply 0xc64b0, AudioDeviceInputUnit ctor 0x1ade60 / processBlock 0x1ad590. Critic random-schedule fuzz:
640 blocks / 245,760 samples, 0 differences (modes-swapped mutant: 2,414 differ). The analog filter itself stays out of scope (H008).

**F187 — Routing mode = Dave Smith filter send/return loop of one track.** `confirmed` (real code emulated; model bit-exact)
- TrackUnit slot 101 0x1ca218 = `TrackUnit::setSendSource(IDaveSmithSendSource::SendSource)` (RTTI base `20IDaveSmithSendSource` at +0xa8,
  secondary vtable 0x864fbc slot 2 = thunk 0x1ca210; task RTTI string 0x864b64); slot 102 0x1ce944 = getter (+0x61c). Values other than 0/1/2 do nothing.
- **Mode 0:** main = FX(source); ch4/5 (DSF send) = source but Mute#2 closed (send silent). **Mode 1 "Pre FX":** ch4/5 = source (to the filter);
  main = FX(+0x608 return) — the inserts process the filtered signal. **Mode 2 "Post FX":** ch4/5 = FX(source) (post-insert to the filter);
  main = +0x608 return, inserted after the inserts and before Pan → Mute#1 → send tap → fader. Send (ch2/3) taps the selected main path in all modes.
- Selections (0x1ca0dc): mode 1 → +0x110 (2,3), +0x118 (0,1), +0x114 (0,1); mode 2 → +0x110 (0,1), +0x118 (2,3), +0x114 (2,3); mode 0 → all (0,1).
- **Switch behaviour:** every changed OutputSelector fades the old path linearly 1 → 0 over 128 samples, then the new path 0 → 1 over the next 128
  (a 256-sample dip through silence, not an overlapping crossfade; also when switched mid-fade). Mutants (modes swapped 18,590; instant/overlap
  switch 2,560; "+0x604 is the return" 12,282 differing samples) fail.

**F188 — Who sets the mode, and the device setting behind it.** `confirmed` (static + 96/96 emulated grid of 0xc64b0); reachability `likely`
- Writers of +0x61c: the TrackUnit ctors 0x1cceb0/0x1cdb18 (0), slot 101 (direct, or re-posted as a task with the same value off the audio
  thread), and the IDaveSmithSendSource thunk, whose only found caller is DaveSmithManager apply 0xc64b0.
- 0xc64b0(route, sendSource, sendTrack, filter): calls MultiTrackUnit+0x80 (IDaveSmithSendSourceSelector) slot 2(sendTrack); if route = 1 (Track)
  and filter ≠ 0: track `sendTrack` gets table 0x834ac8[sendSource] = [1, 2] (sendSource ≥ 2 → 0), all other tracks 0; else all tracks 0.
  So at most one track at a time is in mode 1 or 2.
- Source: `SwitchableObject<prj::RoutingData, 17>` (reader 0xc4508, writer 0xc65dc): +0x30 byte `bDaveSmithFilter`, +0x34 `daveSmithRouteMode`
  ("DaveSmithRouteMode_Master"/"_Track" → 0/1), +0x38 `daveSmithSendMode` ("DaveSmithSendMode_PreFx"/"_PostFx" → 0/1), +0x3c int `daveSmithSendTrack`.
  Not prj::TrackData. The "FilterPosition"/"FilterPositionPre/Post" strings belong to the LoFi effect (LoFi ctor 0xfd640, FxPM s67/s68,
  ModelInterface LoFi setters, EffectData ctor 0x359d1c), not to this routing.
- UI: Mixer view popup **"ANALOG FILTER SETTING"** — "Insert Track" (Master, Track 1…16) → assignToMaster / assignToTrack(i); "Insert Order"
  (Pre FX / Post FX) → setSendTrackSource(0/1) (callback 0x26b6ac, display 0x26d170; MixerViewController +0x6ac = IDaveSmithManager).
- DaveSmithManager (vt 0x83482c, new(0x118), ctor 0xc5d24 from HexaTrackAudioSystem slot 55 0x1bc8d4; bases IAudioProcessor, IDaveSmithManager
  +0x80, GpioCallback +0x84, IScenePatternSwitchListener +0x88, ISceneEditListener +0x8c) holds a pending state (+0xd0 route, +0xd4 source,
  +0xd8 track, +0xdc filter). `likely` (static only): its processBlock 0xc6be0 applies a change by mute return (0x1ae2bc(1)) → wait → apply 0xc64b0
  + DSF drive bypass bytes → wait +0xfc blocks → unmute → write RoutingData; pending state reloaded on project load and scene/pattern switch / scene edit.
- `likely`: that modes 1/2 are reachable at run time — they need `bDaveSmithFilter` ≠ 0, and no caller of the filter on/off setters
  (IDaveSmithManager slots 3/4) was found (only RoutingData load is known); the generic slot-2 vcall on IDaveSmithSendSource was not swept program-wide.

**F189 — The two external buffers.** `confirmed` (static + emulated AudioDeviceInputUnit); gate state `likely`
- MultiTrackUnit prepare 0x1c5dc0 gives **every** TrackUnit +0x604 = MTU+0x100 (setter 0x1c9a4c @0x1c6008) and +0x608 = MTU+0x198 (0x1c9a54
  @0x1c6014), both 2-channel. MultiTrackUnit::processBlock 0x1c4ff8 first copies MTU in0/1 → +0x100 and MTU in4/5 → +0x198, then runs the
  tracks: same callback, no software block delay.
- **+0x604 = audio input** (MTU in0/1), used as the main source of THRU tracks: OutputSelector +0x10c is set only by setTrackType 0x1cb584
  ("Thru" → (2,3) = +0x604; "Sample"/"Midi" → (0,1)).
- **+0x608 = DSF return:** AudioDeviceInputUnit (ctor 0x1ade60, 6 in / 8 out, processBlock 0x1ad590) out4/5 = device input ch2/3 (8/8 emulated
  blocks bit-equal, static re-read agrees) → MTU in4/5. 0x1ae2bc(1/0) fades the return to 0 within 44 samples / restores it. `likely`: device
  ch2/3 is the ALSA capture device "dsf_return" (device list 0x58b064). `likely`: the return is open in normal use — AudioDeviceInputUnit slot 45
  0x1ad4e4 also writes the out4/5 gate (+0xa4 → +0x84 := 1 only when arg2 = 1 and arg1 ≠ 0); no caller found, emulation used the ctor default (open).
- Refutes the cycle-019 continuation "resample player → MTU in4/5": device in4/5 reaches only AudioDeviceInputUnit out2/3 (via +0x308 and its
  +0xa0 selector).

**F190 — DSF send = one selected track (correction to F098).** `confirmed` (static, critic)
- DsfSendOutputSelector (typeinfo 0x8350d8, vtable 0x834ee0) slot 5 0xc7748 = OutputSelector +0x84 (vt 0x83cb90, processBlock 0xe6b8c) then mute
  +0x88 (setMuteState 0xc7ccc). The builder 0x1c4dd8 hands it [out4, out5, T0 ch4, T0 ch5, T1 ch4, …]; MultiTrackUnit::setSendSourceIndex 0x1c4308
  (= IDaveSmithSendSourceSelector slot 2) selects pair ((i+1)·2, (i+1)·2+1) for i ≥ 0 and mutes for i < 0 (0xc7eac selectSourceChannelPair).
  So MTU out4/5 is the selected track's ch4/5 (with the 128-sample selector fade on change), not Σ of all tracks.

**F191 — Where the inserts sit (signal path summary).** `confirmed` (from F187–F190)
- Normal track: source (player, or audio input for THRU) → FX1 → FX2 → Pan → Mute → send tap → fader. With the analog filter assigned to that track:
  Pre FX = source → [DAC → analog filter → ADC] → FX1 → FX2 → Pan…; Post FX = source → FX1 → FX2 → [analog filter] → Pan…. The digital side
  adds no block delay; the analog round-trip latency (ALSA/codec) is not determined. Master route (filter on the master) is H008 scope, not traced.

## Ducker trigger senders and event types (1.60) — cycle 038 (F192–F197)

Evidence for all: `kb/cycles/038.md` (Worker + Critic); `harness/H049_rtti.py`, `harness/H049_vcall_scan.py`,
`harness/H049_trigger_senders.py` (`python -B harness/H049_trigger_senders.py --out harness/out/H049` → `RESULT: 0 failed checks`,
report sha256 c3303c1b…1a73; critic re-run identical; critic extra cases `<critic scratch run>`, not in the repo).

**F192 — `ITriggerAndParameterReceiver` slot 2 implementers.** `confirmed` (RTTI closure of typeinfo 0x842f48, critic re-run identical)
- Slot 2 (vt+8, `(this, offset, type)`): InsertFxParameterManager 0x1263f4 (types 11/15 → processor slot 54, F088); FxParameterManagerBase and the
  **Master/Send managers 0x11fcd0 = `bx lr`** (Master/Send FX never receive triggers); PlayerParameterManager base no-op 0x11fc44 (the player is
  triggered through slot 3); LfoProcessor (+0x90) thunk 0x131634 → 0x13163c; MidiTrackOutputFormatter 0x14bdf4; TrackUnit (+0xa0) thunk
  0x1c7a60 → 0x1c7a68 (clears the three p-lock useAlt bytes).

**F193 — One sender chain: the Sequencer's per-track receiver table.** `confirmed` (static provenance + emulation E1, 378 cases, 0 mismatches)
- Sequencer ctor 0x19484c allocates the table (new 0x284 @0x1951b4, ctor 0x1995b4) at **Sequencer+0x1d0**; per track t: +4[t] ITrack (TrackUnit+0x80),
  +0x44[t]/+0x84[t] player receivers, **+0xc4+8t / +0xc8+8t = FX1 / FX2 InsertFxParameterManager**, +0x144[t] LfoProcessor+0x90, +0x184[t]
  TrackUnit+0xa0, +0x1c4/+0x204/+0x244[t] MIDI objects. Filled only by HexaTrackAudioSystem constructTrack 0x1bacec (sys+0x598 = Sequencer).
- Only reader that calls receivers: dispatcher **0x199ae0** (T, offset, StepData*); its only caller is **Sequencer::processStep 0x19412c**, whose only
  callers are **Sequencer::processBlock 0x191218** (IAudioProcessor slot 5 of vt 0x85e4dc, 5 sites) and **Sequencer::setRealTimeSequenceData
  0x1901b8** (IRealTimeSequenceEditor slot 5 via thunk 0x1901b0, 5 sites). 0x1263f4: one vtable word (0x844084), no direct callers; TriggerTable_set
  0x1310c4 only from 0x11685c.
- Completeness rests on **object provenance** (T and the HTAS IFPM array sys+0x65c have no other readers; slot-2 vtable words), not on the
  armflow vt+8 call census: that census does **not** see the dispatcher's own register-indexed slot-2 calls (0x199d84/0x199f04/0x19a054) (critic).
  0x144eac (constant 11) is a 4-argument MIDI-CC-style parameter setter (value·/127), not a receiver call (critic, `confirmed`).

**F194 — Event values passed to the Insert managers.** `confirmed` unless marked
- type r2 = **StepData+8 verbatim** (@0x199b00), offset r1 = dispatcher r1 verbatim; except that both managers get **8** when the track is **muted**
  (`moveq r2,sb / movne r2,#8` 0x199d7c/0x199d80/0x199efc; test = ITrack slot 12 → TrackUnit+0xdc = ITrackMixer +0x90 → 0x1c83f4 = TrackData
  byte +0x39, printed `muteSetting`; full vtable chain checked by the critic). MIDI tracks (TrackUnit+0x614 = 2) skip both managers. LFO, TrackUnit
  and MIDI receivers get the unchanged (offset, type); mute does not change them. p-lock forwarding uses manager vt+0x18, never slot 2.
- StepData header: +0 track index (−127 or 0…15, `m_trackIndex`), +4 step index (−126 or 0…63, `m_stepIndex`), +8 trigger type;
  `prj::StepData::checkValidity` 0x3546d8 keeps types {0, 8, 9, 10, 11, 12, 15} (mask 0x9f01), else 15.
- Labels: **15 = FULL trigger, 11 = HALF trigger** `likely` (LfoProcessor slot 2 0x13163c fires on 15 for mode "Full Trigger" and on 11/15 for
  "Full & Half Trigger"; step-pad colour helper 0x3115c4 maps 15→0, 11→1, 8→2 `confirmed`; none of the 125 StepData ctor 0x350600 call sites
  builds 11, so HALF comes only from stored step data). 8 = parameter-lock-only step `likely`; 0 = no trigger `likely`; 9/10/12 no producer found (`guess`: unused).
- Producers: pattern steps (collected by 0x19386c only if programmed — track ≠ −127 and step ≠ −126; unprogrammed steps are never dispatched)
  carry their stored type; RealtimeTriggerHandler::triggerSoundInternal 0x16b768 builds StepData type **15** (`confirmed` static; its callers
  — pads, MIDI in — not traced); retrigger repeats (RETRIGGER) copy the track's last step and set type **15** (0x191554/0x19155c, `confirmed`
  static); HALF steps do not start a retrigger (FULL bit test `ubfx r7,type,#2,#1` @0x194158).

**F195 — Sample offset of a trigger.** `confirmed` at instruction level; meaning of Δ and L `likely`
- Pattern and stored realtime steps, and retrigger repeats: offset = **clamp(trunc(n·Δ/L), 0, n−1)** (0x191e44…0x191e88, 0x1914c4…0x191518;
  n = block size seq+0x250, Δ = step time − block start from 0x1937a0 incl. loop wrap, L = block length in ppq seq+0x258) → **0…63** for the
  64-sample block. Pending realtime list and realtime hits while stopped: offset **0**. Realtime releases (type 0): blocksize−1. The Ducker
  OFFSET value 64 is never produced by these senders.

**F196 — Dispatch count and context.** `confirmed` where emulated (E1 dispatcher, E2 processStep); thread and graph order `likely`
- One dispatch per programmed step whose time falls in the block (including type 0/8 and muted tracks, which do not duck), one per FULL retrigger
  repeat, one per realtime hit. At most one (flag, offset) per track row survives a block: the **later dispatch in processBlock order** wins
  (not the larger offset; E1: offsets 10 then 40 → 40; critic: a muted later step does not overwrite).
- A realtime FULL step identical to the track's last stored FULL step (0x351174: same track, type, locks except params 4 and 10) is **dropped**
  unless byte seq+0xe2c+0xa0t is set (E2). Purpose `guess` (avoid double hits) → H096.
- A HALF step arriving while a retrigger runs writes its param-11 value into the running retrigger record count (0x1941dc–0x194200, critic static) → H096.
- `likely`: all of this runs inside Sequencer::processBlock on the audio thread, order pending/pattern steps → retrigger loop → task drain
  (0x1916cc/0x1916f0/0x1916fc). setRealTimeSequenceData from another thread posts a Task drained at the end of the next processBlock; from the
  bound audio thread it runs directly (0x190214); with an unbound task box it drops the event (0x1901e0) (critic).
- `likely`: the Sequencer is in the pre-processing chain sys+0x3ac, MIDI-connected upstream of multiTrackUnit, so the dispatch precedes the
  Insert processors of the same callback (relies on JUCE graph ordering; not read for this build → H050).

**F197 — What makes a Ducker duck.** `confirmed` (E3: real InsertFxProcessor processBlock 0x116860 + real Ducker vs `tools/fx/ducker.py`;
worker 9 cases × 10,240 samples + critic 8 cases, 81,920 samples; 0 differences)
- A Ducker ducks on **every FULL or HALF trigger of its SOURCE track** (default its own track, F088): programmed sequencer steps at their sample
  position in the block, each FULL retrigger repeat, and realtime/pad hits (sample 0 of the next block when stopped). It does **not** duck for
  parameter-lock-only steps, empty or type-0 steps, a **muted** source track, MIDI tracks, or any audio level. `tools/fx/ducker.py` needs
  no change; host rule: row = source track, flag/offset written by F193–F196, last dispatch in a block wins, rows cleared per callback (H050).
- Incidental for H050 (not tested): the trigger table is built with count **16** (`mov r1,#0x10; bl 0x130d54` @0x1bcf78/0x1bcf80), not 17;
  TriggerEraser (sys+0x580) sits in the post-processing chain sys+0x3b0 (`likely`). → settled in F198–F201 (cycle 039).

## Ducker trigger host rule: table, rows, callback order (1.60) — cycle 039 (F198–F201)

Evidence for F198–F201: kb/cycles/039.md (Worker, Critic, Worker round 2, Critic round 2); `harness/H050_trigger_host.py`
(`python -B harness/H050_trigger_host.py --out <dir>` → `RESULT: 0 failed checks`, report f3986a1d…dd1e; 202 instruction assertions,
censuses, unicorn emulation of the real table ctor/accessors/eraser, the real InsertFxProcessor ctor and the real processBlock 0x116860 + Ducker +
IFPM slot 2 + eraser) and `harness/H050_r2_checks.py` (`--out <dir>` → `RESULT: 0 failed checks`, report 3afba2be…704a; static). Both re-run by the
critic with identical hashes. Supersedes the "17 rows" guess of F088 and the incidental H050 notes in F196/F197.

**F198 — The Ducker trigger table has 16 rows (one per track), no bounds check.** `confirmed` (worker + critic; static + emulation)
- Created once in HTAS slot 55 0x1bc8d4: `new 0xc` @0x1bcf70, `mov r1,#0x10` @0x1bcf78, TriggerTable_ctor 0x130d54 @0x1bcf80, stored sys+0x57c @0x1bcf94.
  Layout `{int *flag +0, int *offset +4, int count +8}`; ctor stores count and allocates two `new int[count]` (0x109fc), both zeroed.
- set 0x1310c4 / getFlag 0x1310dc / getOffset 0x1310e8 are bare `[base, row, lsl #2]` accesses (no clamp); clear 0x1310f4 zeroes rows 0…count−1.
  Sole callers: ctor ← 0x1bcf80; set ← 0x11685c (Insert slot 54); getFlag ← 0x116a04, getOffset ← 0x116a40 (processBlock 0x116860);
  clear ← 0x130cb0 (TriggerEraser slot 5 0x130cac). One TriggerEraser (ctor 0x130d24 ← 0x1bcfc0, +0x80 = table, stored sys+0x580).
- Ducker row index = rint(SOURCE) via the 1.5·2^52 trick (0x1169f0…0x116a00, 0x116a2c…0x116a3c), unclamped. A row ≥ 16 would read past the
  arrays; what it returns on the device depends on the heap allocator (`guess`; the emulator's value flag[16] = offset[0] is an artefact, not device behaviour).

**F199 — Row = track index; FX1 and FX2 of a track share one row.** `confirmed`
- HTAS config built in LiveSamplerApplication: 16 tracks (`mov r6,#0x10` @0x571404 → sys+0x210), 2 inserts per track (sys+0x22c).
  buildMultiTrackUnit 0x1bc7c8 loops t = 0…15 → constructTrack 0x1bacec (t kept at [sp,#0x1c], single writer @0x1bad04, no alias) → for each insert
  slot: InsertFxProcessor ctor 0x118b0c(p, t, sys+0x578, sys+0x57c) @0x1bbd80 → `+0xa0 = t` @0x118b40, base 0x1128cc `+0x94 = tempo` @0x112908,
  `+0x98 = table` @0x11290c. Real ctor emulated for t = 0, 7, 15.
- These 32 are the only InsertFxProcessors (ctor single caller; vptr 0x842c10 only in ctor/dtor pools); SAMPLE/THRU FX2 is slot 1 of the same loop.
  The table exists before any track is built.
- SOURCE = 16 (Choice range 0…16) is not reachable from any writer found: the only index-10 slot-14 write in all of .text is 0x1178b4 (slot 52 case 9,
  value float(+0xa0) = 0…15); the IFPM forwarder path writes index 10 only at 0x127a00 from the s74 converter (0…15); slot 29 never uses index 10.
  `likely`: ~248 register-index vt+0x38 sites outside 0xe0000…0x135000 (UI/JUCE ranges) are unclassified (→ H099).

**F200 — Callback order: Sequencer (pre chain) → all 32 Insert processors (multiTrackUnit, workers joined) → TriggerEraser (post chain), once per
graph render.** `confirmed` (round 2 removed the JUCE-default dependency)
- HTAS processBlock 0x1c12a0 calls juce::AudioProcessorGraph::processBlock 0x5f91fc at most once per path; 0x5f91fc runs `ops[i]` sequentially
  (graph+0x148, count +0x150).
- buildRenderingSequence 0x5fe3a4: JUCE 3.1.1 insertion ordering (each node inserted before the first ordered node it is an input to; recursive
  isAnInputTo 0x602ba0, depth entries−1), then one loop over ordered nodes 0…n−1 calling createRenderingOpsForNode 0x604a10, which only appends
  (inline appends + Array::add 0x604950); the local ops array is swapped into graph+0x148 @0x5fec9c…0x5feca8. So op order = node order.
- Edges (added once in the build; the connection removers 0x1b7404, 0x1b7508…0x1b7f78 have no callers or pointer words): MIDI pre → resamplePlayer →
  deviceInput → liveSampling → MTU and masterOut → deviceOutput → resampleRecorder → post (canConnect 0x5fae80: all endpoint classes accept/produce MIDI);
  audio MTU out(0,1)/(2,3) → CompositeFx in(0,1)/(2,3), CompositeFx out(0,1)/(2,3) → MasterOut in(0,1)/(2,3), MTU out(14,15) → MasterOut in(4,5).
  Channel counts from the ctors (setPlayConfigDetails 0x5f9e90): MultiTrackUnit 6 in / 16 out, CompositeFxUnit 4/4, MasterOutUnit 6 in / 4 out; all
  10 channel links pass canConnect; later setPlayConfigDetails calls re-pass the same counts. The insertion order is a topological order, so
  pre-chain node < MTU node < post-chain node.
- Chains (ProcessorChain, ctor 0x1b8a00, processBlock 0x1b8aec runs members' vt+0x14 in vector order; insert 0x1b8c54, no remove path): Sequencer
  sys+0x598 only in the pre chain sys+0x3ac (0x1bd95c); post chain sys+0x3b0 = [TriggerEraser sys+0x580 (0x1bd97c), sys+0x60c (0x1bf3c0)].
- multiTrackUnit's ParallelAudioProcessingManager run 0x1539c0 (MTU+0x98 = sys+0x5cc via 0x1c4408) runs its own job list and spins nanosleep
  (0x153a5c…0x153a70) until all workers report done, so every Insert processor finishes inside the MTU node.

**F201 — Ducker host rule.** `confirmed` for triggers dispatched in the Sequencer's pre-chain node (pattern steps, retriggers, queued realtime
events): in callback k, row t = (1, offset of the last FULL/HALF event of track t dispatched in k) or (0, 0); every Ducker with SOURCE = t (FX1 or FX2
of any track) sees it in k; the eraser clears all 16 rows after the inserts, so it is gone in k+1.
- Emulated (worker): 6 real Duckers on one real 16-row table, 32 managers, events through real IFPM slot 2, real eraser once per callback vs
  `tools/fx/ducker.py` fed by this rule: 0 of 69,120 samples differ; shuffled processor order byte-identical. Critic, own schedule (5 Duckers,
  offsets 62/63, back-to-back blocks, later-smaller wins, type 8 ignored): 0 of 8,960 per Ducker. Alternative orders (dispatch after the inserts,
  erase before them) never duck; no erase → flags stick.
- H049 E3 (9 cases) with ProcRig `ROWS = 16, REAL_TABLE = True` (new flags in `harness/H041_ducker_model.py`; defaults keep the legacy 17-row stand-in
  and reproduce the H041/H049 hashes) is byte-identical (88101ee3…6d6e). `tools/fx/ducker.py` unchanged.
- Open edge (INCONCLUSIVE, `guess` that it never happens): setRealTimeSequenceData 0x1901b8 dispatches directly when called on the thread bound by the
  last Sequencer::processBlock (bind helper 0x504b58 @0x1916f0). A direct call between the MTU node and the eraser would be erased unseen; one after the
  post chain is seen in k+1. No such caller found (→ H098). `likely` (critic static): the Sequencer box is unbound until the first processBlock
  (box ctor 0x50553c zeroes +0x18), so realtime events before that are dropped.

## FPSCR on the 1.60 audio threads (cycle 040, H038)

Evidence for F202–F205: kb/cycles/040.md (Worker + Critic); `harness/H038_fpscr_census.py`
(`python -B harness/H038_fpscr_census.py --out DIR`, ~15 s, output digest dded7f1fc4d9a806, reproduced by the critic); REA
`search_bytes` 100ae10e/ff0fff0f and e1ee100a/ffffff0f over the whole loaded image (0 matches, `complete: true`). The critic's extra checks
(all-ELF scan, relocation scan, extended libm run, kernel uImage) used scratch scripts in `<critic scratch run>` that are not
kept in `harness/` (→ deferred H101); their commands and outputs are recorded in the Critic section.

**F202 — The main 1.60 binary never writes FPSCR.** `confirmed`
- No `vmsr`/`fmxr` to any VFP system register and no `mcr p10/p11, 7` in any PT_LOAD of `EP085_Main_R_fw160` (ARM at every aligned word,
  strict `vmsr fpscr` pattern at every byte offset ARM and every halfword offset Thumb-2; capstone sweep 2,981,538 ARM instructions; worker
  and critic independently; REA search 0). The image has no Thumb code (0 of 21,438 exidx entries Thumb, 0 `blx #imm`).
- All 5,302 FPSCR reads are `vmrs APSR_nzcv, fpscr` (flag transfer after `vcmp`); no FPSCR read into a core register, so no read-modify-write.
- `.ARM.attributes`: ABI_FP_denormal = 1 (IEEE denormals), ABI_FP_number_model = 3, VFPv3 + NEON. No FP-environment imports (`fe*`,
  `__setfpucw`, setjmp/longjmp), `__fpu_control` not defined. The binary is JUCE v3.1.1 (string at file offset 0xaa4cd4); no FTZ code path exists.
- Corrects F020's "`likely`" note on `vmsr fpscr` to `confirmed`.

**F203 — No code mapped into the EP085 process can set FZ or DN.** `confirmed` (census and masks); `likely` only for PIC-internal
address-taking without a relocation (moot: every writer only restores or clears).
- Of the 25 DT_NEEDED objects, only 11 functions write FPSCR: libm `feclearexcept`, `fesetexceptflag`, `fesetround`, `feholdexcept`, `fesetenv`,
  `fedisableexcept`, `feenableexcept`; libc `__setfpucw`, `__longjmp`, `____longjmp_chk`; ld.so `__longjmp`. libpthread, libasound,
  libstdc++, libgcc_s, libtcmalloc: 0. Critic scan of every ELF32 in the 1.60 image2 payload (≈ 940 files incl. NSS, gconv, ALSA plug-ins,
  X11) adds only `liboil-0.3.so` (not linked, not named) and `bin/perf` (separate program).
- Masks: `fesetround` touches only RMode (bits 22–23); `feholdexcept` clears traps/flags; `fesetenv` = `(cur & 0x0e08e0e0) | (env & 0xf1f71f1f)`
  (FE_DFL_ENV clears FZ); `__setfpucw(set)` same mask, runs only from libc `_init` 0x176ac if `__fpu_control` (0) ≠ dl_fpu_control, and writes
  FZ = 0; `__longjmp` restores the word the same thread's setjmp saved.
- The main binary reaches writers only through libm `expf` (19 `bl` sites to PLT 0x103fc, e.g. 0xf7cf8): `__ieee754_expf` 0x23260 holds →
  `fesetround(RN)` → `fesetenv` in one straight-line block (0x232ec–0x233a4); overflow/underflow/NaN/inf branches return earlier with no vmsr.
  Emulated real 1.60 libm: worker 30/30 expf calls, critic 1,224 calls of 21 functions × 8 entry FPSCR states (incl. errno paths): bits 22–25
  never change.
- No runtime code generation (the one `mmap` 0x6468bc uses prot 1/3; `syscall` sites are gettid); no LD_PRELOAD / ld.so.preload; `apl_start`
  launches `/root/pdj/EP085_Main_R` directly.

**F204 — All EP085 threads, including ALSAThread and the AudioWorker threads, run with FPSCR FZ = 0, DN = 0, round-to-nearest.** `confirmed`
- 1.60 kernel `uImage` (`Linux-3.0.101-2790-gc248ed7`, same as the rootfs modules directory; decompressed in memory only by the critic):
  `vfp_notifier` 0x52ee3c FLUSH case (exec) 0x52ef34 zeroes the thread VFP state and sets fpexc = 0x40000000, **fpscr = 0**; COPY case (clone)
  0x52eeb4 copies the parent's VFP state. Pioneer's GPL source of the same build agrees (`vfp_thread_flush` = FPSCR_ROUND_NEAREST;
  FPSCR_FLUSHTOZERO unused). The kernel's other FPSCR writes are the exception/lazy-restore paths (0x52eb74, 0x52f0b0); signal delivery saves
  and restores the interrupted FPSCR.
- With F202/F203, FPSCR stays 0 in bits 22–25 for the process lifetime (only NZCV and sticky flags change).

**F205 — The models' FPSCR = 0 emulation assumption is the device behaviour.** `confirmed`
- `harness/lib/emu.py` runs guests with FPSCR = 0; the setting reaches the guest (own hand-encoded `vmul.f32`: normal×normal → denormal gives
  0x000116c2 with FZ = 0 and 0 with FZ = 1; `vmsr`/`vmrs` round trip exact; NEON `vmul.f32 d` flushes in both). So scalar-VFP denormal paths keep
  denormals exactly as modelled (e.g. the F066 Flanger fb-0.99 silence tail, Compressor denormal inputs, VFP tails of copyWithMultiply 0x5792c8),
  and NEON paths flush as already modelled. No rig or model change. Remaining FZ caveats in F020, F044-era limits and the Flanger/Compressor
  findings are settled by this.

## Host-libm independence of the coefficient models (1.60) — cycle 041 (F206–F208, H029)

Evidence for F206–F208: `kb/cycles/041.md` (Worker + Critic, all 5 criteria CONFIRMED). Harness `harness/H029_libm_exact.py`
(run `python -B harness/H029_libm_exact.py --out DIR` → `RESULT: 0 failed checks`, report SHA-256 c6c75ae1…20b1, h029.json
c2a31901…bba1, reproduced byte-identically by the critic; the pre-change column needs `harness/out/H029/oldmodels/` = `git show
480108e:harness/models/*.py`). Real `decoded/lib/libm.so.6` (SHA-256 c6109cde…9d3e) emulated with unicorn. All addresses 1.60.

**F206 — The 1.60 glibc 2.13 double `tan`, `pow`, `exp` return correctly rounded results; `log10f` is fdlibm.** `confirmed`
- PLT stubs (.rel.plt; REA `address_name`): tan 0x10e58, pow 0x11698, exp 0x1144c, log10f 0x10ab0 (also sqrt 0x10210, sqrtf 0x10ef4, powf 0xff40).
- Worker, on the argument forms the firmware builds (tan((double)fc·π/fs) at 44.1/48/96 kHz, pow(10, gdB/20), pow(10, F(gdB·0.05f)),
  pow(1000, v), pow(1000.0000610351562, v), PerfLoFi bases, exp(−2π·10000/fs) for fs 8000…192000, log10f of ratios/multipliers, plus random):
  tan 15,018/15,018, pow 13,503/13,503, exp 12,501/12,501 correctly rounded (prec-90 decimal reference); log10f 9,205/10,802.
  macOS host `math` differs from 1.60 in tan 4,830, pow 9, exp 21, log10f 1,597 cases.
- Critic, about 26k more arguments: tan at 11 sample rates 8…192 kHz and edge cutoffs (16,588, host differs in 5,219), 25 tan and 22 pow
  near-halfway cases mined from 1.2 M candidates (down to 4e-7 ulp from a tie), UI-step lattices (4,922), exp at 6 rates, log10f near 1:
  own replacements = emulated 1.60 in every case.
- Own replacements (no firmware bytes): `tools/fx/crmath.py` `tan`, `pow`, `exp` (decimal, prec 60, one rounding) and
  `fdlibm_powf.log10f` (fdlibm-derived, Sun notice kept; credit required before publication as F044): **0 mismatches** on all tested args.
- Limits: `crmath.pow` is wrong on exact double midpoints (critic T4: pow((2^27−1)·2^-26, 2)); the modelled bases and exponent ranges cannot
  produce one (`likely`, argued, not exhaustive). `crmath.tan` valid for |x| ≲ 1e40. Neither limit is reached by the models.

**F207 — LoFi, MMF, PEQ, PerfLoFi, EffectBase HPF and Phaser models no longer use host libm and match the emulated 1.60 coefficient
routines in 62,000 random settings.** `confirmed`
- 19 host-libm call sites switched (one-token swaps: `math.tan/pow/exp` → crmath, LoFi/MMF `log10f` → fdlibm); each mapped to a direct `bl`
  to the PLT stub (e.g. tan @0xe1be8/0xe1cd0/0xe1ddc/0xe2470/0xe2570/0xe1ac8, pow @0xe2b44/0xe2c04/0xfb3d8/0xfb430/0xfb530/0x107de0/
  0x107eac/0x107f70/0x1091ec, exp @0x10d978, log10f @0xfba10…0xfba84, 0x13818/0x1385c). Inventory in kb/cycles/041.md criterion 1.
- Stress (real 1.60 routine + real libm in unicorn vs model, float32 coefficient words / step counts / multipliers): biquad calcCoefs
  0xe1bb8/0xe1ca0/0xe1d88 (12,000 at 44.1/48/96 k), 1st-order HPF 0xe1aa0 (10,000), PEQ configure 0xe2ab4 (6,000, 44.1 k) and calcCoefs
  0xe2440/0xe2540 (4,000 at 48/96 k), LoFi ramp setup 0xfb994 (5,000), MMF 0x108570 + 0x108608 (5,000), LoFi apply 0xfb20c (4,000), MMF apply
  0x107d18 (3,000), PerfLoFi apply 0xfc278 + 0xfacec (3,000), PEQ gain law (10,000): **0 mismatches**.
- Old host-libm models (git 480108e): 0 wrong float32 words or step counts in the same 62,000 settings; only 2/6,000 PEQ configure settings
  stored a 1-ulp different double p. The F044 residual was real at double precision but never reached a float32 coefficient in this sample.
- No regression: H021, H023, H026, H027, H028, H031, H044, H064, H076, H077 (timing text only), H079 (worker and critic) and H005, H035, H039,
  H040, H043 (worker) all `RESULT: 0 failed checks` with outputs byte-identical to the pre-change baseline. H026 line 510 comparator now
  calls host `math.log10` explicitly (the expression the old `lofi.log10f` computed; critic: test not weakened).
- Trap test (critic, all modules incl. fdlibm_powf / glibc_log10 / crmath; range-end and random parameters; Phaser at 5 rates): 0 host
  transcendental calls.

**F208 — The F044 host-libm caveat is closed for these models; remaining residuals.** `confirmed` unless marked
- Remaining `math.*` in models: IEEE-exact sqrt/sqrtf; the track_mix static table (checked exhaustively by H009); exact powers of two;
  fdlibm_powf / glibc_log10 special-value fallbacks (`likely` unreachable; 0 calls in the critic's trap run, not exhaustive); osc `HostLibm`
  (optional backend, default `OwnLibm`); device_out dB printout (diagnostics).
- `osc.OwnLibm.expf` is correctly rounded, not glibc-exact; it equals the emulated 1.60 expf on the reachable 50 Hz init argument at six
  rates and 3,000 random setSmoothingHz arguments (worker and critic) — residual `likely` nil in normal use.
- Side note, pre-existing: `Phaser(fs=22050)` raises NotImplementedError in `fdlibm_tanf` (|x| ≥ 3π/4) — a model range limit at a
  non-default rate (→ H102, deferred).

## Cycle 042 — H057 headphone mix and main-output selector (critic-confirmed; H057 REFUTED as stated)

Evidence: kb/cycles/042.md (Worker, Critic); `harness/H057_headphone.py` + `tools/fx/headphone_mix.py`;
`python -B harness/H057_headphone.py --out <dir>` → `RESULT: 0 failed checks` (S, C1, C1b, C2a, C2b, C3, C4, C5),
h057_report.txt 1775dace…d44c, h057.json 211f997e…e6e4, sorted f32 ef5dfaca…077a (worker run_e/run_f, critic run1 identical);
critic `--blocks 4000`: 512,000 + 512,000 samples, 0 mismatches. All addresses 1.60.

**F209 — HeadphoneRouter replaces HeadphoneUnit ch0/1 with one selected input pair; nothing is mixed with in0/1.** `confirmed` (static + emulated)
- HeadphoneRouter (new 0x148, vt 0x8624dc, RTTI `15HeadphoneRouter`/`16IHeadphoneRouter`, ctors 0x1b0918 and 0x1b0af4) owns an OutputSelector
  +0xa0 = ctor 0xe6ee4(7 pairs, async 1, monoDup 1, xfade 128); its processBlock (vt slot 10 0x1af3d8) runs the selector **in place** on the
  14-channel HeadphoneUnit buffer: the selected pair overwrites ch0/1.
- setHeadphoneSource 0x1afbac(index): index = position in enum table 0xf62138 (paramId 0x0d000001, static init 0x6cb20): 0 CueMaster,
  1 Cue12, 2 Cue34, 3 Cue56, 4 Cue78, 5…12 Cue1…Cue8. With router byte +0x98 = 1: CueMaster/Cue12 → (2,3); Cue34/56/78 → (6,7)/(8,9)/(10,11);
  Cue1 = (2,−), Cue2 = (−,3), Cue3…Cue8 = single channels 6…11 (mono, duplicated to both sides). (+0x98 = 0 would give CueMaster (0,1),
  Cue12 (4,5), Cue1/2 4/5.) Only CueMaster sets +0x140 = 1 (getter 0x1b0ce4). Stores +0xa4 = index, writes the index back to RoutingData+0x28;
  unknown index: no selection change.
- Every HeadphoneRouter-method writer of +0x98 stores 1 (0x1b099c, 0x1b0b88, callback 0x1af61c @0x1af63c; critic whole-.text store scan).
  Consequence: **HeadphoneUnit in0/1 (MasterOutUnit out2/3, the post-master-fader copy, F102/F106) is never heard in 1.60** — `likely`
  (≈130 other `strb …,#0x98]` sites lie in other classes' functions, not individually typed).
- Switching: 128-sample linear fade-out of the old pair, then 128-sample fade-in of the new one (a dip, not an overlap). Quirk (real code,
  OutputSelector vt 0x83cb98 slot 3 0xe6b8c): re-selecting the current pair during its fade-out leaves the selector at gain 0 until the next
  change. Setter 0xe6ff4 only stores the target (direct or async Task).

**F210 — HeadphoneUnit::processBlock 0x1b10ec law.** `confirmed` (real ctor 0x1b17b0 + prepareToPlay 0x1b0d94 + processBlock emulated)
- Ctor args from the graph build @0x1bea60…0x1bea88: +0x90 = BufferedAudioProcessor(0, &sys+0x6b4) (sys+0x5f0; sys+0x6b4 = 6-channel buffer;
  sys+0x5f4 = mode-1 BufferedAudioProcessor on the same buffer is handed to RecMonitorUnit ctor 0x1ac134), +0x94 = RecMonitorUnit (sys+0x5d0)
  +0x80 = IMonitorMixer.
- Order: router (ch0/1 := selected pair) → cue buffer +0x13c cleared and filled by +0x90 → three MuteSmoothers +0x130/+0x134/+0x138
  (0xe7fd8(44, 0)) on cue pairs (0,1)/(2,3)/(4,5), each **added to ch0/1 at gain 1.0** (0x578dc8) → MuteCrossfadeSmoother +0x1d4 via
  0xe8228(ms, ch0, ch1, ch11, ch12) → VolumeKnob +0x8c slot 11 → PeakDetector +0x84.
- Steady state: L = in[a] + cue0 + cue2 + cue4, R = in[b] + cue1 + cue3 + cue5 ((a,b) = selected pair). Gates: all unmuted unless the source is
  CueMaster (+0x140); then gate k muted = IMonitorMixer slot 4(k, 0) (0x1abd60). Gate fade linear over 44 samples (fixed). Crossfade: linear,
  out = dry·(1−g) + g·(ch11/12), length `(int)(sr × 0.001)` (44 @ 44.1 kHz, 48 @ 48 kHz), driven by IMonitorMixer slot 8 = RecMonitorUnit byte
  +0x420. VolumeKnob: ctor 0xe9f10 Volume(0,100), gain = F096 table[i] × 0.5 (127 → 1.0, 100 → 0.5, 50 → 0.125, 1 → 0.000997631, 0 → 0),
  100-sample ramp from the slot-3 sample offset (offset persists), bound by VolumeProxy @0x1bec64 to [sys+0x550] (PM+0x1c0 headphoneVolume,
  `likely`). in0, in1 and in13 never reach the output.
- +0x420's only writer in .text is slot 7 0x1acb70; the only caller found passes 0 (UI page-change 0x31c174 @0x31c304…0x31c318); RecMonitorUnit's
  ctor does not initialise it (heap content). Crossfade to the audio input dormant in 1.60 — `likely`.
- Doubly fed in11 (MTU ch13 + audio input ch0, F102) is R of Cue78, the source of Cue8 and the crossfade's dry L; summed by the JUCE graph —
  `likely` (→ H106). Monitor-pair identities `guess` (→ H105); content of in2/3 (DeviceInputUnit out2/3) in normal use `guess` DSF return (→ H104).

**F211 — Headphone source reachable from the UI: 10 or 12 values depending on the output mode.** `confirmed` (UI handler emulated; stubs checked against real code)
- Path: OutputSettingViewController popup handler 0x26fa50 (15 call sites; "HP CUE", getHpCuePopupListRow 0x2720dc) → ControllerData::
  setHeadphoneSource 0x2f6be4 (v → index identity for 0…12, other values → CueMaster) → IAudioSystem slot 39 getHeadphoneRouter (thunk 0x1b9488
  → sys+0x69c) → router slot 2 0x1b0770 (async Task 0x1b0760 off the audio thread) → 0x1afbac. Ctors apply RoutingData+0x28 at start-up;
  RoutingData listeners 0x1af5a0/0x1af6b0/0x1af72c/0x1af7a8 re-apply it (project/scene change `likely`).
- Output mode "M + 6ch" (Master): rows → {CueMaster, Cue34, Cue56, Cue78, Cue3…Cue8}; "8ch" (4Assign): {Cue12, Cue34, Cue56, Cue78,
  Cue1…Cue8}. Changing the mode auto-corrects: → Master turns Cue12/Cue1/Cue2 into CueMaster; → 4Assign turns CueMaster into Cue12. No MIDI
  path found (`likely` absent).

**F212 — Output12Router picks master or MTU out6/7 for the main output.** `confirmed` (real ctor + selection + processBlock emulated)
- processBlock 0x1b2610 = OutputSelector +0x8c (0xe6ee4(2, 1, 1, 0x80)) slot 5 on [master out0/1, MTU out6/7]. Selection 0x1b28f8(value, force):
  RoutingData+0x24 enum (paramId 0x0d000000, table 0xf62130): 0 "Master" → (0,1), 1 "4Assign" → (2,3); other values keep the selection.
  Callers: ctors 0x1b2d8c @0x1b2e78 and 0x1b2efc @0x1b2ff0, four RoutingData listeners 0x1b2bbc/0x1b2c30/0x1b2ca4/0x1b2d18 (force 1),
  setOutputMode 0x1b2d84 (force 0) ← IAudioSystem slot 37 (thunk 0x1b94a8) ← ControllerData::setOutputMode 0x2f6518 ← 0x26fa50 (output-mode
  rows "M + 6ch"/"8ch"). Switch = 128 + 128-sample dip, same re-select quirk as F209.

**F213 — Headphone and main output path, end to end.** `confirmed` unless marked
- Headphones: one selected pair (F209: CueMaster/Cue12 = DeviceInputUnit out2/3 (content `guess`), Cue34/56/78 = MTU out 8…13 assignable
  outs, Cue1…Cue8 one channel dual-mono) + three RecMonitorUnit monitor pairs at unity (gated only in CueMaster) → optional crossfade to
  audio input in11/12 (dormant `likely`) → VolumeKnob → HeadphoneUnit out0/1 → deviceOut (8,9) → OutputVolume[4] → FixedAttenuator −0.5 →
  BulkMute (F109–F113). The master-fader copy MasterOutUnit out2/3 → HeadphoneUnit in0/1 is wired but unused (`likely`).
- Main: MasterOutUnit out0/1 (after master fader) or MTU out6/7 → Output12Router (F212) → dsfDriveMaster (F107) → deviceOut (0,1) and (12,13)
  (resample recorder) → output stage (F109–F113).
- Model: `tools/fx/headphone_mix.py` (HeadphoneUnit + Output12Router) bit-exact vs the emulated 1.60 routines given the cue-source and
  IMonitorMixer inputs (harness fakes = stated boundary); alternatives (master copy mixed in, gates for every source, no-fade switch,
  132-sample crossfade, CueMaster = in0/1) all mismatch (C5).
