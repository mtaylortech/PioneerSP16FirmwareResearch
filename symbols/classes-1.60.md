# Application class map — firmware 1.60 (`EP085_Main_R`)

Recovered C++ class/method names and vtable code offsets for the SP-16's main
application, extracted **statically** from the shipped 1.60 binary. No firmware
bytes are reproduced here — only names and addresses derived from them.

- **Binary:** `EP085_Main_R`, 12,000,396 bytes, SHA-256 `3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464`
- **Image base:** `0x8000` · **Arch:** ARM:LE:32 (ARMv7-A)
- **Method:** the app is a JUCE C++ program whose RTTI `type_info` names survive in
  `.rodata`. We demangle those names and walk each class's `type_info` → vtable to
  recover the virtual-method entry addresses. See [`README.md`](README.md) and the
  regeneration script for exactly how.
- **Confidence:** class names and vtable/virtual-method **addresses** are directly
  derived and were spot-checked against ARM function prologues. The *grouping* into
  subsystems below is our editorial classification. Non-virtual methods are not listed.
- **Version:** all addresses are **1.60**. On 1.60 (and other releases) the class
  layout is expected to be the same but **every address must be re-bound** — see
  `../docs/architecture.md`.

**124 application classes** recovered (plus 26 third-party/library classes not listed here: ICU, JUCE internals, libstdc++).

Columns: **vtable** = virtual-table address · **m0** = first virtual-method address · **#v** = virtual-method slots read · **named** = demangled method signatures recovered (see `classes-1.60.json` for the full per-class list).


## MIDI & Sync  (13)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `LiveSampling::AsyncNotifier` | `0x8465c0` | `0x13cfb8` | 7 | 1 |
| `MidiCc1ViewController` | `0x880154` | `0x265ee4` | 8 | 1 |
| `MidiCc2ViewController` | `0x880cec` | `0x26abcc` | 8 | 1 |
| `MidiClockInterpreter` | `0x846edc` | `0x141cac` | 8 | 3 |
| `MidiSender` | `0x848200` | `0x148974` | 8 | 2 |
| `SetScaleMidiViewController` | `0x87713c` | `0x234190` | 8 | 1 |
| `prj::MidiCc1Data` | `0x8abe28` | `0x3717b0` | 8 | 1 |
| `prj::MidiCc2Data` | `0x8ac100` | `0x3717f8` | 8 | 1 |
| `prj::MidiInOutData` | `0x8ac628` | `0x3718d0` | 8 | 1 |
| `prj::MidiModeData` | `0x8abcb0` | `0x371888` | 8 | 1 |
| `prj::MidiNoteData` | `0x8abd08` | `0x371768` | 8 | 1 |
| `prj::MidiOtherData` | `0x8ac428` | `0x371840` | 8 | 1 |
| `prj::ScaleDataMidi` | `0x8aba78` | `0x37196c` | 8 | 1 |

## Sequencer / Pattern / Scene  (21)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `ArrangerViewController` | `0x87d1cc` | `0x252a38` | 8 | 1 |
| `BpmQuantizePopupWidgetController` | `0x86a124` | `0x1ec5a0` | 8 | 1 |
| `GlobalSectionAssignWidgetController` | `0x896d1c` | `0x2d1678` | 8 | 1 |
| `GlobalSectionHomeWidgetController` | `0x8971c4` | `0x2d4aa0` | 8 | 1 |
| `GlobalSectionProjectWidgetController` | `0x897884` | `0x2d52b8` | 8 | 1 |
| `GlobalSectionTrackMenuWidgetController` | `0x897c14` | `0x2d7188` | 8 | 1 |
| `RealtimeTriggerHandler` | `0x855734` | `0x16d000` | 8 | 6 |
| `SceneBpmChangePopupWidgetController` | `0x8691cc` | `0x1e873c` | 8 | 1 |
| `SceneEditor` | `0x8591fc` | `0x17cad8` | 8 | 17 |
| `SceneManagerSequenceViewController` | `0x870c44` | `0x20b508` | 8 | 1 |
| `SceneManagerTrackViewController` | `0x870324` | `0x203bf0` | 8 | 1 |
| `SceneManagerViewController` | `0x871a64` | `0x218b50` | 8 | 1 |
| `ScenePackId::SourceId` | `0x8a3698` | `0x33938c` | 8 | 1 |
| `ScenePatternManager` | `0x85c28c` | `0x189ed4` | 8 | 5 |
| `ScenePatternSwitcher` | `0x85cabc` | `0x18b4c8` | 8 | 3 |
| `SectionSequencer` | `0x85d664` | `0x18e370` | 8 | 8 |
| `SequenceViewController` | `0x88776c` | `0x29543c` | 8 | 1 |
| `Sequencer` | `0x85e4dc` | `0x195d3c` | 8 | 27 |
| `prj::ArrangementData` | `0x8b2ba0` | `0x3714ec` | 8 | 1 |
| `prj::SceneData` | `0x859af8` | `0x188900` | 8 | 1 |
| `prj::SequencerData` | `0x8ab830` | `0x3716d8` | 8 | 1 |

## Sampling / Audio / DSP  (30)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `AmpEnvelopeViewController` | `0x87c9d4` | `0x24f8b4` | 8 | 1 |
| `AssignableUnit` | `0x8630f4` | `0x1b3e80` | 8 | 1 |
| `AudioEditor` | `0x8320bc` | `0x0b7190` | 8 | 6 |
| `AudioRenderingManager` | `0x857000` | `0x174784` | 8 | 1 |
| `AudioSourceHelper` | `0x832d70` | `0x0bf8c8` | 2 | 6 |
| `CompositeFxUnit` | `0x861854` | `0x1aa590` | 8 | 1 |
| `DaveSmithManager` | `0x83482c` | `0x0c5504` | 8 | 6 |
| `DsfSendOutputSelector` | `0x834ee0` | `0x0c782c` | 8 | 2 |
| `FxInsertMultiModeFilterViewController` | `0x879014` | `0x23d100` | 8 | 1 |
| `FxMasterMultiModeFilterViewController` | `0x878934` | `0x23ab90` | 8 | 1 |
| `GridSlicePopupWidgetController` | `0x86c60c` | `0x1f6234` | 8 | 1 |
| `HeadphoneRouter` | `0x8624dc` | `0x1af8d4` | 8 | 1 |
| `HexaTrackAudioSystem` | `0x863da0` | `0x1c1e30` | 8 | 4 |
| `LfoProcessor` | `0x8451ec` | `0x131ac4` | 8 | 9 |
| `LfoViewController` | `0x87f3e4` | `0x261da4` | 8 | 1 |
| `LiveSampling` | `0x8465ec` | `0x13d138` | 8 | 8 |
| `LiveSamplingWaveFormViewController` | `0x86f654` | `0x1ff3b8` | 8 | 1 |
| `PeakDetectorUnit` | `0x83c7a0` | `0x0e5f00` | 8 | 2 |
| `PlayerUnit` | `0x84a788` | `0x161054` | 8 | 24 |
| `PresetSampleCopyTestPage` | `0x92e9d8` | `0x538da8` | 8 | 5 |
| `RecMonitorUnit` | `0x861c48` | `0x1aae64` | 8 | 2 |
| `RenderAudioViewController` | `0x88487c` | `0x28b7d0` | 8 | 1 |
| `SampleAdjunctDataManager` | `0x8b3dd8` | `0x376a00` | 8 | 1 |
| `SamplingEditViewController` | `0x886d2c` | `0x2911a0` | 8 | 1 |
| `SetSliceViewController` | `0x88810c` | `0x297208` | 8 | 1 |
| `WaveFormDetailWidgetController` | `0x89cfec` | `0x2f0524` | 8 | 1 |
| `dat::SampleAdjunctData` | `0x8b3c30` | `0x378ff0` | 8 | 1 |
| `prj::AmpEnvelopeData` | `0x8ab670` | `0x371548` | 8 | 1 |
| `prj::LfoData` | `0x8b2ae0` | `0x37142c` | 8 | 1 |
| `prj::SliceData` | `0x8ab928` | `0x3716a0` | 8 | 1 |

## Mixer / FX / Send / Routing  (27)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `FxInsert2BandEqViewController` | `0x879d54` | `0x240c80` | 8 | 1 |
| `FxInsertChorusViewController` | `0x87b81c` | `0x2494dc` | 8 | 1 |
| `FxInsertCompressorViewController` | `0x878294` | `0x238788` | 8 | 1 |
| `FxInsertDelayViewController` | `0x87bd6c` | `0x24acd8` | 8 | 1 |
| `FxInsertDuckerViewController` | `0x87316c` | `0x2219d4` | 8 | 1 |
| `FxInsertFlangerViewController` | `0x87ad7c` | `0x246434` | 8 | 1 |
| `FxInsertLofiViewController` | `0x8767bc` | `0x22f86c` | 8 | 1 |
| `FxInsertNoSelectViewController` | `0x874d1c` | `0x227ecc` | 8 | 1 |
| `FxInsertPhaserViewController` | `0x8737ac` | `0x223600` | 8 | 1 |
| `FxInsertViewControllerBase` | `0x873284` | `0x2218b4` | 5 | 1 |
| `FxLimiterViewController` | `0x87e73c` | `0x25db24` | 8 | 1 |
| `FxMaster2BandEqViewController` | `0x87a2dc` | `0x2430d8` | 8 | 1 |
| `FxMasterChorusViewController` | `0x87b2cc` | `0x247b78` | 8 | 1 |
| `FxMasterCompressorViewController` | `0x877b5c` | `0x236574` | 8 | 1 |
| `FxMasterDelayViewController` | `0x87c2dc` | `0x24c524` | 8 | 1 |
| `FxMasterFlangerViewController` | `0x87a82c` | `0x244970` | 8 | 1 |
| `FxMasterLofiViewController` | `0x875ff4` | `0x22cf90` | 8 | 1 |
| `FxMasterNoSelectViewController` | `0x874734` | `0x2275b0` | 8 | 1 |
| `FxMasterPhaserViewController` | `0x873cfc` | `0x224f8c` | 8 | 1 |
| `FxMasterViewControllerBase` | `0x873e14` | `0x224e6c` | 5 | 1 |
| `FxReverbViewController` | `0x87422c` | `0x2266c4` | 8 | 1 |
| `FxSelectPopupWidgetController` | `0x86b42c` | `0x1f5524` | 8 | 1 |
| `MixerViewController` | `0x881c6c` | `0x26f650` | 8 | 1 |
| `prj::EffectData` | `0x8ac720` | `0x371578` | 8 | 1 |
| `prj::RoutingData` | `0x8b2b70` | `0x371498` | 8 | 1 |
| `prj::SendData` | `0x8ab428` | `0x3715d0` | 8 | 1 |
| `prj::TrackRoutingData` | `0x857798` | `0x180b6c` | 8 | 1 |

## Track  (3)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `TrackMenuViewController` | `0x888d44` | `0x2a9480` | 8 | 1 |
| `TrackUnit` | `0x864cac` | `0x1cc4f0` | 8 | 8 |
| `prj::TrackData` | `0x8575c8` | `0x180b20` | 8 | 1 |

## Project / File / Storage  (8)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `BankSelectPopupWidgetController` | `0x8697a4` | `0x1e9ee8` | 8 | 1 |
| `BrowseViewController` | `0x87dc1c` | `0x256ed0` | 8 | 1 |
| `IProjectManager` | `0x8a57c4` | `0x343c3c` | 2 | 1 |
| `LiveRecFileWriter` | `0x845ce8` | `0x137758` | 7 | 1 |
| `ProjectManager` | `0x8a7aa4` | `0x3407bc` | 8 | 12 |
| `prj::ProjectData` | `0x8b2b40` | `0x3393e0` | 8 | 1 |
| `prj::UndoManager` | `0x8b45a4` | `0x37aae4` | 8 | 3 |
| `ui::UsbStorageManager` | `0x8b5588` | `0x380888` | 8 | 8 |

## UI / View / Panel / Encoder  (19)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `CautionManager` | `0x8a2570` | `0x32aa2c` | 2 | 3 |
| `ColorAdjustView` | `0x92f25c` | `0x53a050` | 8 | 4 |
| `DoubleColumnWithSubItemListTableWidgetController` | `0x86adac` | `0x1f06d4` | 8 | 1 |
| `HardMuteController` | `0x865f48` | `0x1d07d0` | 7 | 3 |
| `InputStringPopupWidgetController` | `0x86ca0c` | `0x1f7bbc` | 8 | 1 |
| `MessagePopupWidgetController` | `0x86ce94` | `0x1f900c` | 8 | 1 |
| `OutputSettingViewController` | `0x88243c` | `0x273988` | 8 | 1 |
| `PlaybackViewController` | `0x882b04` | `0x275714` | 8 | 1 |
| `ProgramChangePopupWidgetController` | `0x86d3c4` | `0x1f9db4` | 8 | 1 |
| `ProgressBarWindowPopupWidgetController` | `0x86d6f4` | `0x1fa698` | 8 | 1 |
| `RibbonSettingViewController` | `0x886134` | `0x28d340` | 8 | 1 |
| `SetScaleViewController` | `0x877014` | `0x23400c` | 8 | 1 |
| `SoftwareKeyboardPopupWidgetController` | `0x86e1c4` | `0x1fda9c` | 8 | 1 |
| `TestModeController` | `0x92f7cc` | `0x549a9c` | 8 | 1 |
| `TouchDetector` | `0x928c40` | `0x4f6600` | 7 | 3 |
| `ViewControllerManager` | `0x8a1c44` | `0x31c3c8` | 8 | 4 |
| `prj::RibbonPitchSettingData` | `0x8ac5a8` | `0x371994` | 8 | 1 |
| `prj::RibbonUserSettingData::Item` | `0x8ac500` | `0x371618` | 8 | 1 |
| `prj::ScaleData` | `0x8ab9d0` | `0x371944` | 8 | 1 |

## Infrastructure  (2)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `Device::Gpio` | `0x8b4ef8` | `0x37e05c` | 2 | 2 |
| `infra::RbxUnitTestRunner` | `0x92a280` | `0x506e58` | 5 | 1 |

## Other  (1)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `prj::PlaybackData` | `0x8ab4d8` | `0x371518` | 8 | 1 |

## Selected recovered method signatures

Full demangled signatures for classes most relevant to current community work.


**`MidiClockInterpreter`**
- `MidiClockInterpreter::setMidiNudgeOnDown(bool)`
- `MidiClockInterpreter::setMidiNudgeOnUp(bool)`
- `MidiClockInterpreter::startSyncMode()`

**`MidiSender`**
- `MidiSender::sendMessageBlockToCurrentDevice(juce::MidiBuffer const&, bool)`
- `MidiSender::sendMessageToCurrentDevice(juce::MidiMessage const&, bool)`

**`Sequencer`**
- `Sequencer::deleteIndependentParameter(int, int, ModuleIndex)`
- `Sequencer::deleteIndependentParameter(int, int, ParamIndex)`
- `Sequencer::deleteIndependentParameter(int, int, int, FxParamIndex)`
- `Sequencer::deleteStepSequenceData(int, int)`
- `Sequencer::playPauseSequence(bool)`
- `Sequencer::processStepShift(int, int)`
- `Sequencer::quantize(int)`
- `Sequencer::recSequence()`
- `Sequencer::setCurrentTransportPpq(double)`
- `Sequencer::setCurrentTransportStepIndex(int)`
- `Sequencer::setMetronomeMode(bool)`
- `Sequencer::setPatternLength(int)`
- `Sequencer::setPreCountLength(int)`
- `Sequencer::setPreCountMode(bool)`
- `Sequencer::setRealTimeSequenceData(prj::StepData&, bool)`
- `Sequencer::setStepSequenceData(prj::StepData const&)`
- `Sequencer::setStepSequenceDataIndividuallyAsFloat(int, int, ParamIndex, float, ValueChangeTypeToNextStepData)`
- `Sequencer::setStepSequenceDataIndividuallyAsFloat(int, int, int, FxParamIndex, float, ValueChangeTypeToNextStepData)`
- `Sequencer::setStepSequenceDataIndividuallyAsIndex(int, int, ParamIndex, int, bool, ValueChangeTypeToNextStepData)`
- `Sequencer::setStepSequenceDataIndividuallyAsIndex(int, int, int, FxParamIndex, int, bool, ValueChangeTypeToNextStepData)`
- `Sequencer::setStepSequenceDataIndividuallyOnlyIndex(int, int, ParamIndex, int, ValueChangeTypeToNextStepData)`
- `Sequencer::setStepSequenceDataTriggerType(int, int, TriggerType)`
- `Sequencer::setStepShiftArea(int, IStepSequenceEditor::StepShiftArea)`
- `Sequencer::setToIgnoreStepSequence(int, bool)`
- `Sequencer::setToIgnoreStepSequenceForUndo(bool)`
- `Sequencer::setTranspose(int, int)`
- `Sequencer::stopSequence()`

**`PlayerUnit`**
- `PlayerUnit::AllSceneTrackUnload_AfterStop()`
- `PlayerUnit::InstLoad_AfterStop()`
- `PlayerUnit::ProjectLoad_AfterStop()`
- `PlayerUnit::setAttackCurve_Linear_PUnit(Amplifier::eCurveSetting)`
- `PlayerUnit::setAttackIndex_PUnit(float)`
- `PlayerUnit::setAudioSource_PUnit(AbstractReader*)`
- `PlayerUnit::setBypassMode_PUnit(bool)`
- `PlayerUnit::setEndSamples_PUnit(int)`
- `PlayerUnit::setHoldIndex_PUnit(float)`
- `PlayerUnit::setLoopMode_PUnit(bool)`
- `PlayerUnit::setLoopStartSamples_PUnit(int, int)`
- `PlayerUnit::setNowPlayPositionSamples_PUnit(int)`
- `PlayerUnit::setPitchCent_PUnit(int)`
- `PlayerUnit::setQuantOffset_PUnit(int)`
- `PlayerUnit::setReleaseCurve_Linear_PUnit(Amplifier::eCurveSetting)`
- `PlayerUnit::setReleaseIndex_PUnit(float)`
- `PlayerUnit::setReversePlay_PUnit(bool)`
- `PlayerUnit::setStartSamples_PUnit(int)`
- `PlayerUnit::setStretchModePitchSpeed_PUnit(IPlayer::enum_TimeStretchMode, int, float)`
- `PlayerUnit::setSyncMode_PUnit(bool)`
- `PlayerUnit::setVelocity_PUnit(int)`
- `PlayerUnit::stop_PUnit(int, bool)`
- `PlayerUnit::triggerAmp_PUnit(int, bool)`
- `PlayerUnit::trigger_PUnit(int)`

**`SceneEditor`**
- `SceneEditor::copyAndPasteAsync(PatternEditParameter const&, PatternEditParameter const&)`
- `SceneEditor::copyAndPasteAsync(SceneEditParameter const&, SceneEditParameter const&)`
- `SceneEditor::copyAndPasteAsync(SequenceEditParameter const&, SequenceEditParameter const&)`
- `SceneEditor::copyAndPasteAsync(TrackEditParameter const&, TrackEditParameter const&, bool)`
- `SceneEditor::finishedEdit(SceneEditor::EditType, PatternEditParameter const&, PatternEditParameter const&)`
- `SceneEditor::finishedEdit(SceneEditor::EditType, SceneEditParameter const&, SceneEditParameter const&)`
- `SceneEditor::finishedEdit(SceneEditor::EditType, SequenceEditParameter const&, SequenceEditParameter const&)`
- `SceneEditor::finishedEdit(SceneEditor::EditType, TrackEditParameter const&, TrackEditParameter const&, bool)`
- `SceneEditor::prepareToEdit(SceneEditor::EditType, PatternEditParameter const&, PatternEditParameter const&)`
- `SceneEditor::prepareToEdit(SceneEditor::EditType, SceneEditParameter const&, SceneEditParameter const&)`
- `SceneEditor::prepareToEdit(SceneEditor::EditType, SequenceEditParameter const&, SequenceEditParameter const&)`
- `SceneEditor::prepareToEdit(SceneEditor::EditType, TrackEditParameter const&, TrackEditParameter const&, bool)`
- `SceneEditor::resetAsync(PatternEditParameter const&)`
- `SceneEditor::resetAsync(SceneEditParameter const&)`
- `SceneEditor::resetAsync(SequenceEditParameter const&)`
- `SceneEditor::resetAsync(TrackEditParameter const&, bool)`
- `SceneEditor::swapAsync(TrackEditParameter const&, TrackEditParameter const&, bool)`

**`ScenePatternSwitcher`**
- `ScenePatternSwitcher::cancelIfPossible()`
- `ScenePatternSwitcher::setSwitchable(bool)`
- `ScenePatternSwitcher::switchSceneAndPattern(int, int, bool)`

**`ScenePatternManager`**
- `ScenePatternManager::clearSceneBpm(int)`
- `ScenePatternManager::onProjectDataAboutToReplace(prj::ProjectData&)`
- `ScenePatternManager::onProjectDataReplaced()`
- `ScenePatternManager::setSceneBpm(int, double)`
- `ScenePatternManager::setSceneColour(int, int)`

**`RealtimeTriggerHandler`**
- `RealtimeTriggerHandler::holdParameters(juce::Array<IParameterHoldable::Param, juce::DummyCriticalSection, 0>*)`
- `RealtimeTriggerHandler::holdParameters(juce::Array<IParameterHoldable::Param, juce::DummyCriticalSection, 0>*, int, bool)`
- `RealtimeTriggerHandler::releaseParameters()`
- `RealtimeTriggerHandler::releaseParameters(int)`
- `RealtimeTriggerHandler::stopSound(int, bool)`
- `RealtimeTriggerHandler::triggerSound(int, int, int, int, int, int, IMultiTrackSoundGenerator::TriggerSoundType)`

**`LiveSampling`**
- `LiveSampling::saveRecordedSample(int, ILiveSampling::SavedDeviceID)`
- `LiveSampling::setLSMode(bool)`
- `LiveSampling::setLoopAfterRecMode(bool)`
- `LiveSampling::setNudgeSamplesInRing(int, int)`
- `LiveSampling::setRecLength(infra::Fraction<unsigned short>)`
- `LiveSampling::startLiveRec(int)`
- `LiveSampling::stopLiveRec(int, int)`
- `LiveSampling::unloadTrack(int)`

**`PeakDetectorUnit`**
- `PeakDetectorUnit::addPeakData(PeakData*, int)`
- `PeakDetectorUnit::removePeakData(PeakData*)`

**`DaveSmithManager`**
- `DaveSmithManager::assignToMaster()`
- `DaveSmithManager::assignToTrack(int)`
- `DaveSmithManager::assignToTrack(int, IDaveSmithManager::SendTrackSource)`
- `DaveSmithManager::setMode(IDaveSmithManager::Mode)`
- `DaveSmithManager::setSendTrackIndex(int)`
- `DaveSmithManager::setSendTrackSource(IDaveSmithManager::SendTrackSource)`

**`LfoProcessor`**
- `LfoProcessor::setBypassMode(bool)`
- `LfoProcessor::setDepth(int)`
- `LfoProcessor::setDestination(ILfoProcessor::LfoDestination)`
- `LfoProcessor::setLfoType(ILfoProcessor::LfoType)`
- `LfoProcessor::setOffset(int)`
- `LfoProcessor::setSpeed(float)`
- `LfoProcessor::setSync(bool)`
- `LfoProcessor::setTriggerMode(ILfoProcessor::LfoTriggerMode)`
- `LfoProcessor::setTriggerOnTrigger(ILfoProcessor::LfoTriggerOn)`
