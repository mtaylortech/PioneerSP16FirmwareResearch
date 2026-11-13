# SP-16 application architecture (firmware 1.50 & 1.60)

A readable map of the Pioneer TORAIZ SP-16's main application, `EP085_Main_R`,
reconstructed **statically** from the shipped binaries. Both the **1.50** and
**1.60** releases are mapped; the recovered class set is **identical** between
them (124 classes, none added or removed), so the structure below applies to
both — only the hex addresses differ per version. It is meant as an
orientation for anyone reading the code for the first time — what the big
pieces are, what they are called, and where the interesting ones live.

> **How solid is this?** The application is a C++ program built on the
> [JUCE](https://juce.com) framework. It is compiled and its classic symbol
> table is stripped, **but the C++ run-time type information (RTTI) survives**:
> every polymorphic class leaves its name and virtual-table in the binary. We
> demangle those names and walk each class's `type_info → vtable` to recover
> virtual-method **entry addresses**. The class names and the addresses are
> therefore *directly derived facts*, not guesses (several were spot-checked
> against their ARM prologues). What we add on top — grouping classes into
> subsystems, and the narrative of how they interact — is **informed inference
> from the names and signatures**, and is marked as such. Nothing here was run;
> no hardware or emulator was involved.
>
> **Everything below is firmware 1.50** — the release this SP-16 runs, decoded
> from the official 1.50 update (`EP085_Main_R`, 11,993,612 bytes, SHA-256
> `075cff7a…`). The newer **1.60** release is a *different* binary
> (12,000,396 bytes, SHA-256 `3d1392a6…`); the class structure is almost
> certainly the same, but **every hex address must be re-bound per version** —
> do not reuse a 1.50 address on 1.60 or vice-versa. Regenerate with the script
> in [`../symbols/README.md`](../symbols/README.md) against your own extracted
> binary.

Full inventory (both releases): [`../symbols/classes-1.50.md`](../symbols/classes-1.50.md)
and [`../symbols/classes-1.60.md`](../symbols/classes-1.60.md) — 124 application
classes each, with vtable/method addresses; machine-readable
[`classes-1.50.json`](../symbols/classes-1.50.json) /
[`classes-1.60.json`](../symbols/classes-1.60.json).

---

## The shape of the program

The binary is a ~12 MB ARM (ARMv7-A, little-endian) JUCE application, image base
`0x8000`. Alongside Pioneer's own code it statically links JUCE, ICU
(internationalisation), a compact language detector, and the usual C++ runtime.
Pioneer's own classes fall into a small number of subsystems:

| Subsystem | What it is | Representative classes |
|---|---|---|
| **MIDI & Sync** | MIDI in/out, clock following, tempo | `MidiClockInterpreter`, `MidiSender`, `AlsaClient::MidiInputThread`, `MidiCc1/2ViewController` |
| **Sequencer / Pattern / Scene** | the step sequencer, patterns, scenes, song/section arrangement | `Sequencer`, `SectionSequencer`, `ScenePatternSwitcher`, `ScenePatternManager`, `SceneEditor`, `RealtimeTriggerHandler` |
| **Sampling / Audio / DSP** | the voice/player engine, live sampling, slicing, LFO, envelopes, filter | `HexaTrackAudioSystem`, `PlayerUnit`, `LiveSampling`, `LfoProcessor`, `PeakDetectorUnit`, `DaveSmithManager`, `AudioRenderingManager` |
| **Mixer / FX / Send / Routing** | the mixer, insert FX, sends, output routing | `CompositeFxUnit`, `FxInsert*ViewController`, `DsfSendOutputSelector`, `HeadphoneRouter`. The DSP classes (`InsertFxProcessor`, `EffectBase` and its effects) have RTTI but are not in this class map: see [effects/](effects/README.md) (1.60) |
| **Project / File / Storage** | the saved-project data model and load/save | the entire `prj::` namespace, `prj::UndoManager`, `BrowseViewController` |
| **UI / View / Panel / Encoder** | touchscreen views, widgets, popups | the `*ViewController` / `*WidgetController` family |

The **`prj::` namespace is the on-disk project model** — effectively the schema
of a saved SP-16 project:

```
prj::ProjectData
 ├─ prj::SceneData            ├─ prj::SequencerData      ├─ prj::TrackData
 ├─ prj::SliceData            ├─ prj::PlaybackData       ├─ prj::SendData
 ├─ prj::RoutingData          ├─ prj::TrackRoutingData   ├─ prj::EffectData
 ├─ prj::LfoData              ├─ prj::AmpEnvelopeData    ├─ prj::ArrangementData
 ├─ prj::ScaleData / ScaleDataMidi
 ├─ prj::MidiInOutData / MidiModeData / MidiNoteData / MidiCc1Data / MidiCc2Data / MidiOtherData
 ├─ prj::RibbonPitchSettingData / RibbonUserSettingData
 └─ prj::UndoManager
```

Each takes a `prj::Config const&` in its constructor, which suggests a
schema-versioned, config-driven (de)serialiser — a good first target for anyone
wanting to read or write `.dat` project files without the hardware.

---

## Flagship: the MIDI clock / sync path

This is the machinery behind the behaviour where the SP-16,
fed a steady external clock (e.g. 160.0 BPM), displays and drifts around it
(160.1 / 160.2).

The relevant class is literally named **`MidiClockInterpreter`**, and the
recovered methods tell the story of *how* the SP-16 follows an external clock:

- `MidiClockInterpreter::startSyncMode()` — enter external-sync mode.
- `MidiClockInterpreter::setMidiNudgeOnUp(bool)`
- `MidiClockInterpreter::setMidiNudgeOnDown(bool)` — a **nudge** mechanism:
  rather than hard-locking to each incoming clock tick, the interpreter nudges
  its internal tempo up or down toward the incoming rate.

A nudge-based follower is a classic design, and it also explains the symptom:
a nudging estimator **settles toward** the true tempo instead of snapping to it,
so a rock-steady 160.0 source reads as 160.1→160.2 while the loop converges and
hunts. That is a plausible, name-supported reading — **not** a confirmed
root-cause; confirming it means reading the bodies at the addresses below.

Downstream, tempo and transport live in the sequencer:

- `Sequencer::setCurrentTransportPpq(double)` — the transport position is kept
  in **PPQ (pulses per quarter-note) as a `double`**, i.e. continuous, not
  integer steps.
- `Sequencer::setCurrentTransportStepIndex(int)`, `Sequencer::setMetronomeMode(bool)`.

And MIDI output is centralised in **`MidiSender`**:

- `MidiSender::sendMessageToCurrentDevice(juce::MidiMessage const&, bool)`
- `MidiSender::sendMessageToCurrentDevice(juce::MidiBuffer const&, bool)`

**Where to read next (1.50 addresses).** From
[`../symbols/classes-1.50.json`](../symbols/classes-1.50.json):

| Class | vtable (1.50 / 1.60) | first virtual method (1.50 / 1.60) |
|---|---|---|
| `MidiClockInterpreter` | `0x844734` / `0x846edc` | `0x13ac08` / `0x141cac` |
| `MidiSender` | `0x8457d8` / `0x848200` | `0x142948` / `0x148974` |
| `Sequencer` | `0x85b78c` / `0x85e4dc` | `0x18a2a0` / `0x195d3c` |

A successor investigating the drift should disassemble `MidiClockInterpreter`
(start at its vtable, follow `startSyncMode` and the nudge setters) and the
code that computes the displayed BPM from incoming clock deltas. This is pure
static work and needs no hardware.

---

## Subsystem notes (and how they map to community feature requests)

The recovered method names line up strikingly well with the feature requests
and bug reports in the community thread. This section is a reading guide, not a
claim that any change is safe or easy.

**Pattern chaining** → `ScenePatternSwitcher::switchSceneAndPattern(int, int, bool)`,
`ScenePatternSwitcher::setSwitchable(bool)`, `ScenePatternSwitcher::cancelIfPossible()`.
The reported "chained pattern repeats once before advancing" behaviour is
consistent with a switch that is only honoured at a scene/pattern boundary
(`cancelIfPossible` suggests a pending switch that can still be cancelled before
the boundary). Pair with `ScenePatternManager` (per-scene BPM/colour).

**Step probability / conditional trigs** (and the "fires twice on step 1" bug)
→ `RealtimeTriggerHandler::triggerSound(...)` / `stopSound(...)` and
`Sequencer::setStepSequenceDataTriggerType(int, int, TriggerType)`. The
per-step trigger type is first-class in the sequencer data model, so condition
evaluation lives around `RealtimeTriggerHandler`.

**Step copy / copy-whole-bar** → `SceneEditor::copyAndPasteAsync(...)` with
four overloads (`Pattern`/`Scene`/`Sequence`/`Track` edit parameters), plus
`prepareToEdit` / `finishedEdit` / `resetAsync` / `swapAsync`. The edit model
is already structured and asynchronous.

**Pattern length / longer patterns** → `Sequencer::setPatternLength(int)`,
`Sequencer::setPreCountLength(int)`, and `SectionSequencer` (song-mode sections
with fixed BPM and repeat counts: `insertSectionSequence`, `setFixedBpm`,
`setRepeatCount`).

**Quantized record** → `Sequencer::recSequence()`, `Sequencer::quantize(int)`,
`Sequencer::setPreCountMode(bool)`.

**FX send pre/post + routing** → `prj::SendData`, `prj::RoutingData`,
`prj::TrackRoutingData`, and `DsfSendOutputSelector`. The persisted routing
model is where a per-track pre/post flag would live.

**The Dave Smith analog filter question** ("is the filter in the digital
path?") → there is a dedicated **`DaveSmithManager`** with
`assignToMaster()`, `assignToTrack(int, SendTrackSource)`,
`setSendTrackSource(...)` and `setMode(...)`. The filter is managed as an
**assignable send destination** (master or a chosen track/source), which is
consistent with the community observation that you resample *through* it — i.e.
it sits on a routable send, with conversion around it, not inline on every
track's digital path. (Name-level evidence; read the class to confirm.)

**Normalize / rendering** → `PeakDetectorUnit::addPeakData/removePeakData`
(peak analysis — the basis for a normalise gain) and
`AudioRenderingManager::executeJobAsyncImpl(AudioRenderingJob*)` (an async
offline render path). These are the firmware-side counterparts to the host
normalize tool already in [`../tools/normalization/`](../tools/normalization/).

**Live sampling / looping / slicing** → `LiveSampling` (`startLiveRec`,
`stopLiveRec`, `setLoopAfterRecMode`, `setNudgeSamplesInRing`,
`saveRecordedSample`), `PlayerUnit` (per-voice: start/end/loop samples, pitch,
stretch mode, reverse, attack/release curves), and `prj::SliceData`.

**LFO / envelope (second-LFO requests)** → `LfoProcessor` (`setLfoType`,
`setDestination`, `setSpeed`, `setSync`, `setTriggerMode`, `setDepth`) and the
persisted `prj::LfoData` / `prj::AmpEnvelopeData`.

**The audio engine** is `HexaTrackAudioSystem` ("hexa" = the six tracks), with
`switchToSamplerMode()` / `switchToRendererMode()`, `muteAllOutput(bool)` and
`muteExternalInput(bool)`.

---

## What this is not

- Not a decompilation and not source. These are names, signatures and addresses;
  the method *bodies* still have to be read in a disassembler.
- Not a claim that any feature can be added safely. Understanding where code
  lives says nothing about how to modify, repack or install firmware — that is
  explicitly out of scope for this project (see [`../DISCLAIMER.md`](../DISCLAIMER.md)).
- Not version-portable. 1.50 addresses only.

## Reproduce / extend

The extractor and RTTI-walker are described in
[`../symbols/README.md`](../symbols/README.md). Point them at your own lawfully
obtained, hash-verified binary. To extend the map: read method bodies at the
recovered addresses, confirm or correct the inferred roles, and record findings
per class with the version and address bound to each claim.
