# SP-16 project & sample file format — CONFIRMED against a real project

How the SP-16 stores a project and its per-sample metadata. **This is no longer
inferred:** it was validated by parsing a real `.prj` project byte-for-byte
(756,128 bytes, consumed exactly) and the accompanying `.wav.dat` files, with the
parser shipped in [`../tools/project/parse_project.py`](../tools/project/parse_project.py).
Verified on firmware 1.50 data; the 1.60 container is identical.

> **What was confirmed vs. still open.** Container, compression, the JUCE
> ValueTree encoding, and the full node/field schema (31 node types, real field
> names and types) are **confirmed** from a real file. Still open: the internal
> layout of a few packed blobs — `PatternData.Steps` (the versioned step binary),
> and the `params` / `grids` / `channelNo` arrays — which are identified but not
> yet field-decoded. No firmware bytes are reproduced here; all example values
> come from a commercial sample pack's project.

## Container

A project file (`.prj`) is **not** a ZIP. It is:

```
bytes 0..7      "vltrgzip"                 8-byte ASCII magic
bytes 8..EOF    zlib stream (0x78 0x01 …)  →  inflate  →  JUCE binary ValueTree
```

So: strip the 8-byte magic, `zlib`-inflate the rest, and parse the result as a
JUCE `ValueTree`. (The `ProjectArchiver`/`ZipFile` path seen in the binary is a
*separate* export format — "Save As Package" / scene archive — not the plain
`.prj` save.)

Per-sample metadata files (`<sample>.wav.dat`) are the **same ValueTree encoding
but uncompressed** (no `vltrgzip` magic) — root node `SampleAdjunctData`.

## JUCE binary ValueTree encoding (how to read the inflated bytes)

Each node, recursively:

1. node **type** — UTF-8 string, NUL-terminated
2. **property count** — JUCE "compressed int" (`len` byte, then `len` LE bytes)
3. each property: **name** (NUL-terminated string) + **value** (`var`, below)
4. **child count** — compressed int
5. each child — recurse

A `var` is: a compressed int `N` (= 1 + payload length), then if `N>0` a 1-byte
**type marker** and `N-1` payload bytes. Markers in this build:

| Marker | Type | Payload |
|---|---|---|
| (N=0) | void / undefined | — |
| 1 | int | 4 bytes LE |
| 2 | bool `true` | 0 |
| 3 | bool `false` | 0 |
| 4 | double | 8 bytes LE |
| 5 | string | UTF-8 (`N-1` bytes) |
| 6 | int64 | 8 bytes LE |
| 7 | array | nested (count + vars) |
| 8 | binary (MemoryBlock) | raw |

This is the stock JUCE format; `parse_project.py` implements it in ~40 lines.

## The project tree (confirmed schema)

Root is **`ProjectData`**. Full machine-readable schema (all 31 node types, every
field + type):
[`../tools/project/project-schema-1.50.json`](../tools/project/project-schema-1.50.json).
The shape:

```
ProjectData                      (1)   global settings
├─ SceneData × 16                      one per scene (colourIndex, name, bpm)
│  ├─ TrackData × 16                   16 tracks per scene  (256 total)
│  │  ├─ PlaybackData                  sample playback (see below)
│  │  ├─ AmpEnvelopeData               attack/hold/release, curves, velocity
│  │  ├─ SequencerData                 retrigger count/speed, offset, transpose
│  │  ├─ SliceData                     grids(array), nGrids, windowOffset
│  │  ├─ ScaleSetting / ScaleSettingMidi
│  │  ├─ InsertFx × 2                  effectType, params(array), filter types
│  │  ├─ SendData                      sendChannel, sendAmount
│  │  ├─ LfoData                       speed, depth, destination, type, sync…
│  │  └─ MidiTrackData
│  │     ├─ MidiNoteData               note1-4, velocity, length
│  │     ├─ MidiCc1Data / MidiCc2Data  per-param CC number / value / active
│  │     ├─ MidiOtherData              bank select msb/lsb, program change
│  │     └─ MidiModeData               midimode
│  ├─ PatternData × 4                  Steps(binary), Length, TrackMutes, TrackSolos
│  ├─ SendFx / MasterFx                effectType, params(array), filter types
│  └─ RoutingData → TrackRoutingData × 16
├─ ArrangementData                     length, Sections(binary)
├─ RibbonData → UserSetting ×2 (Item ×8), PitchSetting
└─ MidiSettingData → Input, Output     bUseClock/StartStop/NoteCC/SongPosition, channelNo
```

### Selected confirmed fields (real values from the test project)

**`ProjectData`** (20 fields): `masterVolume`,`headphoneVolume`,`sendTrackVolume`,
`monitorVolume` (ints), `bDaveSmithFilter` (bool), `daveSmithRouteMode`/
`daveSmithSendMode` (strings, e.g. `DaveSmithRouteMode_Master`), `swingRate`,
`projectBpm` (double, e.g. `131.0`), `patternQuantizeUnit`, `padQuantizeUnit`,
`sceneIndex`, `patternIndex`, `projectFilePath` (e.g.
`/mnt/emmc/PIONEER DJ SAMPLER/Projects/…`), **`versionNo`**, **`minorVersionNo`**.

**`TrackData`** (9): `trackMode` (`Sample`…), `triggerMode` (`OneShot`…),
`chokeGroup`, `volume`, `pan`, `soloSetting`, `muteSetting`, `colourIndex`,
`instrument` (`Off`…).

**`PlaybackData`** (9): `startSample`, `loopStartSample`, `lengthSample`,
`bLoop`, `bReverse`, `pitchCent`, `stretchMode`, **`audioSourceUrl`** (sample
reference, e.g. `$Int0/%Tmp/TGOLD_Kick_01.wav` — `$Int0` = internal storage,
`%Tmp` = a path alias), `bBypass`.

**`LfoData`** (10): `speed` (double), `depth`, `phaseOffset`, `destination`,
`type` (`Sine`…), `triggerMode`, `triggerOn`, `sync`, `randStartNum`, `bypass`.

**`MidiSettingData → Input`/`Output`**: `bUseClock`, `bUseStartStop`,
`bUseNoteCC`, `bUseSongPosition` (bools) + `channelNo` (array) — the device's
MIDI clock/transport routing (useful alongside a MIDI-implementation chart).

## `SampleAdjunctData` (`.wav.dat`) — confirmed

Uncompressed ValueTree, root `SampleAdjunctData`, 3 fields:

| Field | Type | Meaning (inferred) |
|---|---|---|
| `bar` | double | sample length in bars at its native tempo (e.g. `0.25`) |
| `bpm` | double | detected/declared sample BPM (`0.0` = unset) |
| `sampleNum` | int | sample identifier |

Example (a one-shot kick): `bar=0.25, bpm=0.0, sampleNum=20671`.

## Still to decode (identified, not yet field-exact)

### `PatternData.Steps` — the step matrix (decoded)

`Steps` is a **zlib stream** (`0x78 0x9c`). Every pattern inflates to a **fixed
155,648 bytes**, laid out as a dense matrix:

```
155,648 = 64 steps × 16 tracks × 152-byte record      (step-major: step*16*152 + track*152)
```

(The fixed capacity matches the binary's `infra::Matrix<prj::StepData, …>`; a
16- or 32-step pattern still allocates all 64 slots.) It is read/written by the
versioned `prj::StepDataFormat::readStepData` / `readStepDataForVer`
(**kVersionNo 1 and 2**; `StepData version error!` otherwise).

**The 152-byte per-step/per-track record:**

| Offset | Size | Field (confidence) |
|---|---|---|
| 0 | int32 | trigger / first value — **empty = `-127`**, set when the step is programmed |
| 4 | int32 | second value — **empty = `-126`**, set when programmed |
| 8 | int32 | constant `15` (`0x0f`) — flags/param-count (inferred) |
| 12 … 151 | 35 × float32 | **parameter-lock slots** (default value `1.0f`, bit-OR'd with the slot's parameter index — see below) |

`152 = 12 + 35×4`. The 35 slots are **not** a flat list — each slot's default
value is `0x3f800000 | index` (i.e. `1.0f` carrying its parameter index in the
low byte), which reveals the layout directly from an empty step:

```
slot  0 … 22   index 0..22    → ParamIndex    (the 23 "main" lockable params)
slot 23 … 28   index 5..10    → FxParamIndex  for FX unit 1
slot 29 … 34   index 5..10    → FxParamIndex  for FX unit 2
```

This matches the firmware exactly: `Sequencer::setStepSequenceDataIndividuallyAsFloat`
has one overload taking **`ParamIndex`** and one taking **`(int fxUnit, FxParamIndex)`**
— so a step stores a lock value for each `ParamIndex` plus six `FxParamIndex`
values for *each* of the two FX units. Each lock defaults to nominal (`1.0`); a
programmed lock overwrites its slot.

The 23 `ParamIndex` params are the per-step-lockable track parameters documented
in [midi-implementation.md](midi-implementation.md) — Track (volume, pan, time-
stretch, loop, trigger-mode, send, mute), Playback (pitch, start, loop-start,
length), Amp-envelope (velocity, attack, hold, release), Sequence (offset,
retrigger count, retrigger speed) and LFO (speed, depth, phase); the `FxParamIndex`
5-10 are each FX unit's Parameter 1-6. The block structure, slot count, index of
every slot, and the two enums are **confirmed**; the only residual is the exact
name bound to each of the 23 `ParamIndex` ordinals (the CC map fixes the *set*,
not the enum's internal order). That last naming is a one-export refinement:
program a single step, change one parameter by a known amount, re-export, and the
changed slot names itself.

Read the matrix with `zlib.decompress(steps_bytes)` → 155,648 bytes, indexed
`step*2432 + track*152` (+ `12 + slot*4` for a lock).
- **`ArrangementData.Sections`** — a small binary blob (song arrangement).
- **`params` arrays** (InsertFx/SendFx/MasterFx), **`grids`** (SliceData slice
  points), **`channelNo`** (MIDI) — JUCE `var` arrays; element layout not yet
  enumerated.

## Tooling

[`../tools/project/parse_project.py`](../tools/project/parse_project.py) parses a
`.prj` (inflates `vltrgzip`+zlib) or a `.wav.dat`, and prints the tree or a JSON
schema (`--schema`). [`project-schema-1.50.json`](../tools/project/project-schema-1.50.json)
is the full generated schema. To make a project file on a computer, write the
inverse: build the ValueTree, serialize, `zlib`-compress, prepend `vltrgzip`.
