# Application class map — firmware 1.50 (`EP085_Main_R`)

Recovered C++ class/method names and vtable code offsets for the SP-16's main
application, extracted **statically** from the shipped 1.50 binary. No firmware
bytes are reproduced here — only names and addresses derived from them.

- **Binary:** `EP085_Main_R`, 11,993,612 bytes, SHA-256 `075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`
- **Image base:** `0x8000` · **Arch:** ARM:LE:32 (ARMv7-A)
- **Method:** the app is a JUCE C++ program whose RTTI `type_info` names survive in
  `.rodata`. We demangle those names and walk each class's `type_info` → vtable to
  recover the virtual-method entry addresses. See [`README.md`](README.md) and the
  regeneration script for exactly how.
- **Confidence:** class names and vtable/virtual-method **addresses** are directly
  derived and were spot-checked against ARM function prologues. The *grouping* into
  subsystems below is our editorial classification. Non-virtual methods are not listed.
- **Version:** all addresses are **1.50**. On 1.50 (and other releases) the class
  layout is expected to be the same but **every address must be re-bound** — see
  `../docs/architecture.md`.

**124 application classes** recovered (plus 26 third-party/library classes not listed here: ICU, JUCE internals, libstdc++).

Columns: **vtable** = virtual-table address · **m0** = first virtual-method address · **#v** = virtual-method slots read · **named** = demangled method signatures recovered (see `classes-1.50.json` for the full per-class list).


## MIDI & Sync  (13)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `LiveSampling::AsyncNotifier` | `0x863008` | `0x1c8aa8` | 7 | 1 |
| `MidiCc1ViewController` | `0x87e54c` | `0x263f00` | 8 | 1 |
| `MidiCc2ViewController` | `0x87f0e4` | `0x268be8` | 8 | 1 |
| `MidiClockInterpreter` | `0x844734` | `0x13ac08` | 8 | 3 |
| `MidiSender` | `0x8457d8` | `0x142948` | 8 | 2 |
| `SetScaleMidiViewController` | `0x875534` | `0x232310` | 8 | 1 |
| `prj::MidiCc1Data` | `0x8a9c30` | `0x36ef30` | 8 | 1 |
| `prj::MidiCc2Data` | `0x8a9f08` | `0x36ef78` | 8 | 1 |
| `prj::MidiInOutData` | `0x8aa430` | `0x36f050` | 8 | 1 |
| `prj::MidiModeData` | `0x8a9ab8` | `0x36f008` | 8 | 1 |
| `prj::MidiNoteData` | `0x8a9b10` | `0x36eee8` | 8 | 1 |
| `prj::MidiOtherData` | `0x8aa230` | `0x36efc0` | 8 | 1 |
| `prj::ScaleDataMidi` | `0x8a9880` | `0x36f0ec` | 8 | 1 |

## Sequencer / Pattern / Scene  (21)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `ArrangerViewController` | `0x87b5c4` | `0x250bc0` | 8 | 1 |
| `BpmQuantizePopupWidgetController` | `0x868514` | `0x1ea71c` | 8 | 1 |
| `GlobalSectionAssignWidgetController` | `0x894b7c` | `0x2d0260` | 8 | 1 |
| `GlobalSectionHomeWidgetController` | `0x895024` | `0x2d35e0` | 8 | 1 |
| `GlobalSectionProjectWidgetController` | `0x8956e4` | `0x2d3df8` | 8 | 1 |
| `GlobalSectionTrackMenuWidgetController` | `0x895a74` | `0x2d5cc8` | 8 | 1 |
| `RealtimeTriggerHandler` | `0x8525cc` | `0x160b1c` | 8 | 6 |
| `SceneBpmChangePopupWidgetController` | `0x8675bc` | `0x1e681c` | 8 | 1 |
| `SceneEditor` | `0x85631c` | `0x170708` | 8 | 17 |
| `SceneManagerSequenceViewController` | `0x86f034` | `0x209688` | 8 | 1 |
| `SceneManagerTrackViewController` | `0x86e714` | `0x201d70` | 8 | 1 |
| `SceneManagerViewController` | `0x86fe54` | `0x216cd0` | 8 | 1 |
| `ScenePackId::SourceId` | `0x8a14a0` | `0x336b0c` | 8 | 1 |
| `ScenePatternManager` | `0x8593d4` | `0x17e214` | 8 | 5 |
| `ScenePatternSwitcher` | `0x859c04` | `0x17f808` | 8 | 3 |
| `SectionSequencer` | `0x85a8cc` | `0x182768` | 8 | 9 |
| `SequenceViewController` | `0x885b64` | `0x293454` | 8 | 1 |
| `Sequencer` | `0x85b78c` | `0x18a2a0` | 8 | 27 |
| `prj::ArrangementData` | `0x8b09a8` | `0x36ec6c` | 8 | 1 |
| `prj::SceneData` | `0x856c40` | `0x17cc3c` | 8 | 1 |
| `prj::SequencerData` | `0x8a9638` | `0x36ee58` | 8 | 1 |

## Sampling / Audio / DSP  (30)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `AmpEnvelopeViewController` | `0x87adcc` | `0x24da34` | 8 | 1 |
| `AssignableUnit` | `0x86033c` | `0x1a80c8` | 8 | 1 |
| `AudioEditor` | `0x830464` | `0x0b57c0` | 8 | 6 |
| `AudioRenderingManager` | `0x853f10` | `0x168354` | 8 | 1 |
| `AudioSourceHelper` | `0x831118` | `0x0bdef8` | 2 | 6 |
| `CompositeFxUnit` | `0x85ea9c` | `0x19e7d8` | 8 | 1 |
| `DaveSmithManager` | `0x832bd4` | `0x0c3b34` | 8 | 6 |
| `DsfSendOutputSelector` | `0x833288` | `0x0c5e5c` | 8 | 2 |
| `FxInsertMultiModeFilterViewController` | `0x87740c` | `0x23b280` | 8 | 1 |
| `FxMasterMultiModeFilterViewController` | `0x876d2c` | `0x238d10` | 8 | 1 |
| `GridSlicePopupWidgetController` | `0x86a9fc` | `0x1f43b0` | 8 | 1 |
| `HeadphoneRouter` | `0x85f724` | `0x1a3b1c` | 8 | 1 |
| `HexaTrackAudioSystem` | `0x860fd8` | `0x1b5a00` | 8 | 4 |
| `LfoProcessor` | `0x8434dc` | `0x13008c` | 8 | 9 |
| `LfoViewController` | `0x87d7dc` | `0x25ff2c` | 8 | 1 |
| `LiveSampling` | `0x863034` | `0x1c8c28` | 8 | 8 |
| `LiveSamplingWaveFormViewController` | `0x86da44` | `0x1fd538` | 8 | 1 |
| `PeakDetectorUnit` | `0x83ab48` | `0x0e4530` | 8 | 2 |
| `PlayerUnit` | `0x8476f0` | `0x154b7c` | 8 | 24 |
| `PresetSampleCopyTestPage` | `0x92c908` | `0x537514` | 8 | 5 |
| `RecMonitorUnit` | `0x85ee90` | `0x19f0ac` | 8 | 2 |
| `RenderAudioViewController` | `0x882c74` | `0x2897e8` | 8 | 1 |
| `SampleAdjunctDataManager` | `0x8b1be0` | `0x374180` | 8 | 1 |
| `SamplingEditViewController` | `0x885124` | `0x28f1b8` | 8 | 1 |
| `SetSliceViewController` | `0x886504` | `0x295220` | 8 | 1 |
| `WaveFormDetailWidgetController` | `0x89adf4` | `0x2ee7c4` | 8 | 1 |
| `dat::SampleAdjunctData` | `0x8b1a38` | `0x376770` | 8 | 1 |
| `prj::AmpEnvelopeData` | `0x8a9478` | `0x36ecc8` | 8 | 1 |
| `prj::LfoData` | `0x8b08e8` | `0x36ebac` | 8 | 1 |
| `prj::SliceData` | `0x8a9730` | `0x36ee20` | 8 | 1 |

## Mixer / FX / Send / Routing  (27)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `FxInsert2BandEqViewController` | `0x87814c` | `0x23ee00` | 8 | 1 |
| `FxInsertChorusViewController` | `0x879c14` | `0x24765c` | 8 | 1 |
| `FxInsertCompressorViewController` | `0x87668c` | `0x236908` | 8 | 1 |
| `FxInsertDelayViewController` | `0x87a164` | `0x248e58` | 8 | 1 |
| `FxInsertDuckerViewController` | `0x87155c` | `0x21fb54` | 8 | 1 |
| `FxInsertFlangerViewController` | `0x879174` | `0x2445b4` | 8 | 1 |
| `FxInsertLofiViewController` | `0x874bb4` | `0x22d9ec` | 8 | 1 |
| `FxInsertNoSelectViewController` | `0x87310c` | `0x22604c` | 8 | 1 |
| `FxInsertPhaserViewController` | `0x871b9c` | `0x221780` | 8 | 1 |
| `FxInsertViewControllerBase` | `0x871674` | `0x21fa34` | 5 | 1 |
| `FxLimiterViewController` | `0x87cb34` | `0x25bcac` | 8 | 1 |
| `FxMaster2BandEqViewController` | `0x8786d4` | `0x241258` | 8 | 1 |
| `FxMasterChorusViewController` | `0x8796c4` | `0x245cf8` | 8 | 1 |
| `FxMasterCompressorViewController` | `0x875f54` | `0x2346f4` | 8 | 1 |
| `FxMasterDelayViewController` | `0x87a6d4` | `0x24a6a4` | 8 | 1 |
| `FxMasterFlangerViewController` | `0x878c24` | `0x242af0` | 8 | 1 |
| `FxMasterLofiViewController` | `0x8743e4` | `0x22b110` | 8 | 1 |
| `FxMasterNoSelectViewController` | `0x872b24` | `0x225730` | 8 | 1 |
| `FxMasterPhaserViewController` | `0x8720ec` | `0x22310c` | 8 | 1 |
| `FxMasterViewControllerBase` | `0x872204` | `0x222fec` | 5 | 1 |
| `FxReverbViewController` | `0x87261c` | `0x224844` | 8 | 1 |
| `FxSelectPopupWidgetController` | `0x86981c` | `0x1f36a0` | 8 | 1 |
| `MixerViewController` | `0x880064` | `0x26d66c` | 8 | 1 |
| `prj::EffectData` | `0x8aa528` | `0x36ecf8` | 8 | 1 |
| `prj::RoutingData` | `0x8b0978` | `0x36ec18` | 8 | 1 |
| `prj::SendData` | `0x8a9230` | `0x36ed50` | 8 | 1 |
| `prj::TrackRoutingData` | `0x854788` | `0x174998` | 8 | 1 |

## Track  (3)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `TrackMenuViewController` | `0x88713c` | `0x2a7108` | 8 | 1 |
| `TrackUnit` | `0x861eec` | `0x1c0190` | 8 | 8 |
| `prj::TrackData` | `0x8545b8` | `0x17494c` | 8 | 1 |

## Project / File / Storage  (8)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `BankSelectPopupWidgetController` | `0x867b94` | `0x1e7fc8` | 8 | 1 |
| `BrowseViewController` | `0x87c014` | `0x255058` | 8 | 1 |
| `IProjectManager` | `0x8a35cc` | `0x3413bc` | 2 | 1 |
| `LiveRecFileWriter` | `0x862808` | `0x1c3950` | 7 | 1 |
| `ProjectManager` | `0x8a58ac` | `0x33df3c` | 8 | 12 |
| `prj::ProjectData` | `0x8b0948` | `0x336b60` | 8 | 1 |
| `prj::UndoManager` | `0x8b23ac` | `0x378264` | 8 | 3 |
| `ui::UsbStorageManager` | `0x8b2f80` | `0x37c554` | 8 | 8 |

## UI / View / Panel / Encoder  (19)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `CautionManager` | `0x8a03c0` | `0x3289dc` | 2 | 3 |
| `ColorAdjustView` | `0x92d18c` | `0x538728` | 8 | 4 |
| `DoubleColumnWithSubItemListTableWidgetController` | `0x86919c` | `0x1ee850` | 8 | 1 |
| `HardMuteController` | `0x864338` | `0x1cea20` | 7 | 3 |
| `InputStringPopupWidgetController` | `0x86adfc` | `0x1f5d38` | 8 | 1 |
| `MessagePopupWidgetController` | `0x86b284` | `0x1f718c` | 8 | 1 |
| `OutputSettingViewController` | `0x880834` | `0x2719a4` | 8 | 1 |
| `PlaybackViewController` | `0x880efc` | `0x273730` | 8 | 1 |
| `ProgramChangePopupWidgetController` | `0x86b7b4` | `0x1f7f34` | 8 | 1 |
| `ProgressBarWindowPopupWidgetController` | `0x86bae4` | `0x1f8818` | 8 | 1 |
| `RibbonSettingViewController` | `0x88452c` | `0x28b358` | 8 | 1 |
| `SetScaleViewController` | `0x87540c` | `0x23218c` | 8 | 1 |
| `SoftwareKeyboardPopupWidgetController` | `0x86c5b4` | `0x1fbc1c` | 8 | 1 |
| `TestModeController` | `0x92d6fc` | `0x548174` | 8 | 1 |
| `TouchDetector` | `0x926b70` | `0x4f5050` | 7 | 3 |
| `ViewControllerManager` | `0x89f964` | `0x31a378` | 8 | 4 |
| `prj::RibbonPitchSettingData` | `0x8aa3b0` | `0x36f114` | 8 | 1 |
| `prj::RibbonUserSettingData::Item` | `0x8aa308` | `0x36ed98` | 8 | 1 |
| `prj::ScaleData` | `0x8a97d8` | `0x36f0c4` | 8 | 1 |

## Infrastructure  (2)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `Device::Gpio` | `0x8b3910` | `0x381124` | 2 | 2 |
| `infra::RbxUnitTestRunner` | `0x9281b0` | `0x5055d8` | 5 | 1 |

## Other  (1)

| Class | vtable | m0 | #v | named |
|---|---|---|---|---|
| `prj::PlaybackData` | `0x8a92e0` | `0x36ec98` | 8 | 1 |

## Selected recovered method signatures

Full demangled signatures for classes most relevant to current community work.


**`MidiClockInterpreter`**
- `MidiClockInterpreter::setMidiNudgeOnDown(bool)`
- `MidiClockInterpreter::setMidiNudgeOnUp(bool)`
- `MidiClockInterpreter::startSyncMode()`

**`MidiSender`**
- `MidiSender::sendMessageToCurrentDevice(juce::MidiBuffer const&, bool)`
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
