# Firmware evolution 1.20 → 1.60, recovered from the binaries

What changed between official releases, read directly out of the shipped
applications — not from the release notes. For every official release we ran the
RTTI class extractor (see [`../symbols/README.md`](../symbols/README.md)) over
that release's `EP085_Main_R` and compared the recovered class sets. When a class
first appears, the feature it implements was (almost certainly) added in that
release; when a class disappears, it was removed or renamed.

> **Confidence.** This is *class-level* evidence: presence/absence of a C++ class
> and its demangled name. It is strong for "a component with this name exists in
> this release", and a well-supported inference for "this is when the feature
> arrived". It is **not** proof of exact behaviour — that needs the method bodies.
> The vendor descriptions below are quoted from `firmware/release-notes.json`
> (Pioneer/AlphaTheta change history) and are used only to corroborate.

Full per-class, per-version address matrix:
[`../symbols/classes-crossversion.csv`](../symbols/classes-crossversion.csv)
(every class with its vtable address in each release it appears in).

## Class count per release

| Release | Date | Classes recovered | New classes | Vendor summary |
|---|---|---:|---:|---|
| 1.20 | 2016-11-17 | 109 | (baseline) | MIDI, LFO, effects, audio rendering, slice editing |
| 1.30 | 2017-02-02 | 117 | **+13** | AS-1 tracks, pad scales, track filter routing, scene exchange |
| 1.31 | 2017-07-27 | 117 | **0** | bug fixes only |
| 1.40 | 2017-11-21 | 120 | **+9** | copying, track swapping, undo; 64 s samples |
| 1.50 | 2018-06-07 | 124 | **+4** | live sampling |
| 1.60 | 2019-10-03 | 124 | **0** | second-track effects, MIDI forwarding |

Two of these rows are findings in themselves:

- **1.31 added no classes** — consistent with a pure bug-fix release, exactly as
  the change history describes. A good sanity check on the method.
- **1.60 added no classes** — its features ("second track effects", "MIDI
  forwarding") were implemented by **extending existing classes** (e.g. the FX
  units and `MidiSender`), not by adding new ones. So a 1.50→1.60 comparison is a
  *method-body* diff, not a new-component hunt.

## What each release introduced (recovered classes ↔ vendor features)

### 1.30 — AS-1 / Dave Smith, scales, MIDI
New classes include **`DaveSmithManager`** (joining the existing `DaveSmithUnit`),
`SetScaleMidiViewController`, `prj::ScaleDataMidi`, `prj::MidiModeData`,
`prj::MidiOtherData`, `BankSelectPopupWidgetController`,
`ProgramChangePopupWidgetController`, `SceneBpmChangePopupWidgetController`,
`DsfSendOutputSelector`, `Device::Gpio`, `ScenePackId::SourceId`.

This pins the **"AS-1 tracks"** feature to the `DaveSmith*` classes (the AS-1 is
Dave Smith's analog voice), and the pad-scale / MIDI-mode work to the new
`*ScaleMidi*` and `prj::Midi*Data` classes.

### 1.31 — fixes only
No new classes (and none removed). The reported fixes were changes inside
existing code.

### 1.40 — copy / swap / undo, sequencer rework
New: **`SceneEditor`** (whose methods are `copyAndPasteAsync`, `swapAsync`,
`resetAsync`, `prepareToEdit`/`finishedEdit`), **`ScenePatternSwitcher`**,
**`ScenePatternManager`**, the `SceneManager*ViewController` family, and a **new
`Sequencer`** class. The old `Ep085_Sequencer`, `SceneManager` and
`AsyncSceneEditor` disappear here — i.e. the sequencer/scene engine was **rewritten**
in 1.40, which is where the vendor's "copying, track swapping and undo" landed.

### 1.50 — live sampling
New: **`LiveSampling`** (`startLiveRec`, `stopLiveRec`, `saveRecordedSample`,
`setLoopAfterRecMode`, …), `LiveRecFileWriter`, `LiveSamplingWaveFormViewController`,
`LiveSampling::AsyncNotifier`. Exactly matches the one-line vendor note, "Added
live sampling".

### 1.60 — extensions, no new components
No new classes. "Second track effects" and "MIDI forwarding" were added inside
existing classes (FX units, `MidiSender`, routing data). To document 1.60's
changes, diff the **bodies** of those classes between the 1.50 and 1.60 maps.

## Classes removed or renamed by 1.60

Present in an earlier release but gone from 1.60 (11): `Ep085_Sequencer`,
`AsyncSceneEditor`, `SceneManager`, `SceneManagerPopupWidgetController`,
`DaveSmithUnit`, `TrackMixerUnit`, `AudioSourceOperationThread`, `MemoryFSThread`,
`FxMasterDuckerViewController`, `TestModeView`, `RbxUnitTestRunner`. Most are
rename/rework pairs (e.g. `Ep085_Sequencer`→`Sequencer`,
`DaveSmithUnit`→`DaveSmithManager`, `SceneManager`→`SceneEditor`/`ScenePatternManager`,
`RbxUnitTestRunner`→`infra::RbxUnitTestRunner`).

## How to use this

- To **port a finding** between firmware versions, look the class up in
  `classes-crossversion.csv` and read its vtable address for the target release.
- To **find where a feature lives**, find the release that introduced it above,
  then open that class in [`../symbols/classes-1.50.md`](../symbols/classes-1.50.md)
  or [`classes-1.60.md`](../symbols/classes-1.60.md) for its methods and addresses.
- To **study a release's changes**, diff the method bodies of the classes it
  touched (new classes for 1.30/1.40/1.50; existing classes for 1.31/1.60).

Regenerate the whole matrix with `extract_architecture.py` over each release's
binary; see [`../symbols/README.md`](../symbols/README.md).
