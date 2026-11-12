# SP-16 project & sample file format — CONFIRMED against a real project

How the SP-16 stores a project and its per-sample metadata. **This is no longer
inferred:** it was validated by parsing a real `.prj` project byte-for-byte
(756,128 bytes, consumed exactly) and the accompanying `.wav.dat` files, with the
parser shipped in [`../tools/project/parse_project.py`](../tools/project/parse_project.py).
Verified on firmware 1.50 data; the 1.60 container is identical.

> **What was confirmed vs. still open.** Container, compression, the JUCE
> ValueTree encoding, and the full node/field schema (31 node types, real field
> names and types) are **confirmed** from a real file, which also round-trips
> byte-for-byte through an independent writer. Still open: the fields of
> `ArrangementData.Sections` and `SliceData.grids` (both default/empty in the
> test project), and the parameter name behind each FX `params` slot. No firmware
> bytes are reproduced here; all example values come from a commercial sample
> pack's project.

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
│  │  ├─ SliceData                     grids(array, empty unless edited), nGrids, windowOffset
│  │  ├─ ScaleSetting / ScaleSettingMidi
│  │  ├─ InsertFx × 2                  effectType, params(array), filter types
│  │  ├─ SendData                      sendChannel, sendAmount
│  │  ├─ LfoData                       speed, depth, destination, type, sync…
│  │  └─ MidiTrackData
│  │     ├─ MidiNoteData               note1-4, velocity, length
│  │     ├─ MidiCc1Data / MidiCc2Data  per-param CC number / value / active
│  │     ├─ MidiOtherData              bank select msb/lsb, program change
│  │     └─ MidiModeData               midimode
│  ├─ PatternData × 4                  Steps(binary), Length, TrackMutes[16 bool], TrackSolos[16 bool]
│  ├─ SendFx / MasterFx                effectType, params(array), filter types
│  └─ RoutingData → TrackRoutingData × 16
├─ ArrangementData                     length, Sections(binary, zlib → 999 × 8 B)
├─ RibbonData → UserSetting ×2 (Item ×8), PitchSetting
└─ MidiSettingData → Input, Output     bUseClock/StartStop/NoteCC/SongPosition, channelNo[16]
```

Instance nodes carry a numeric suffix in the file (`SceneData0`…`SceneData15`,
`ArrangementData0`); the schema and this diagram use the base type name.

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

**What is confirmed vs. inferred.**

- **Confirmed (observed in a real 1.50 file):** the 152-byte record size, the
  35-slot count, and the bit pattern of each empty slot's default
  (`0x3f800000 | n`). The low bytes run 0–22 in slots 0–22, then 5–10 twice.
- **Likely (inference, no code seen yet):** that each low byte is the slot's enum
  value, i.e. slots 0–22 = `ParamIndex` 0–22 and slots 23–34 = `FxParamIndex`
  5–10 for FX unit 1 then FX unit 2. This rests on the two setter overloads
  above, and on the manual's six FX parameters per unit (CC 46–51, 63–68). No
  firmware code has yet been observed reading or writing these slots.
- **Likely:** a single `FxParamIndex` type with the FX unit passed separately
  (from the mangled names), so "FX slot *n*" probably means Parameter *n* of
  whichever effect is loaded. Not tested against tracks with different effects.

**Unknown.**

- **Which parameter each `ParamIndex` value is.** The manual's CC map
  ([midi-implementation.md](midi-implementation.md)) lists 21 step-lockable
  track parameters: Track (volume, pan, time-stretch, loop, trigger mode, send,
  mute), Playback (pitch, start, loop start, length), Amp envelope (velocity,
  attack, hold, release), Sequence (offset, retrigger count, retrigger speed)
  and LFO (speed, depth, phase). There are 23 `ParamIndex` slots, so **two are
  not accounted for**, and the CC map does not give the enum order.
- **What `FxParamIndex` 0–4 are.** Only 5–10 are stored per step.
- The manual's 35 CC receive rows include CC 0 and CC 32 (scene and pattern
  select), which are not step parameters. The match with the 35 slots is
  therefore a coincidence, not evidence.

A static attempt (Nov 2026) to name the ordinals from the firmware did **not**
recover the ordinal order. It found two converter functions on the sequencer's
step get/set path whose switches take a parameter-index argument and have
distinct cases for 7, 10, 23, 26–29, 54, 56 and 60–62, each branching to its own
small helper. These values equal the manual's CC numbers for the same
parameters, which suggests (**likely**, not confirmed) that the firmware numbers
its parameters internally the same way as the CC map. Not shown: that these
values come from received MIDI messages, or that the helpers read or write the
step record. The same switch also has cases 0–4 and a comparison against 71,
both unexplained. The ordinal→name map remains open.

One controlled export from a unit would settle the naming: program a single
step, change one parameter by a known amount, re-export, and the changed slot
names itself.

Read the matrix with `zlib.decompress(steps_bytes)` → 155,648 bytes, indexed
`step*2432 + track*152` (+ `12 + slot*4` for a lock).
### The `var` arrays (decoded)

A JUCE `var` array (stream marker `7`) is a compressed-int element count followed
by that many ordinary `var`s, which may themselves be arrays. Example: one FX
parameter slot is the 2-element array `[string "None", double 0.4]`. Every array
in the test project decoded with no leftover bytes.

- **FX `params`** (InsertFx/SendFx/MasterFx) — always **6 × `[string, double]`**
  (confirmed). The string is `"None"` in every slot, even for active effects, so
  it does **not** carry the parameter name. The doubles are 0–1 (float32 widened
  to double). *Likely* FX Parameter 1–6, each stored as a fixed-resolution
  fraction (observed denominators differ per effect/slot: /127, /99, /100, /7…),
  consistent with `value = step / (steps − 1)`. The parameter name behind each
  slot is **unknown** (needs one controlled export).
- **`SliceData.grids`** — array, **empty in all 256 tracks** of the test project
  even where `nGrids = 16`. *Likely* only user-moved slice points are stored;
  element layout **unknown**.
- **`MidiSettingData/{Input,Output}.channelNo`** — 16 ints, default `0..15`
  (confirmed). *Likely* one 0-based MIDI channel per track; whether it instead
  lists enabled channels is **unknown** (needs one export).
- **`PatternData.TrackMutes` / `TrackSolos`** — **16 bools per pattern**
  (confirmed), independent of `TrackData.muteSetting` (confirmed: 3 tracks muted
  at track level while all pattern mutes are off). *Likely* per-pattern mute/solo.

### `ArrangementData.Sections` — song arrangement (structure only)

`Sections` is a **zlib stream** (level 6) that inflates to **7,992 bytes = 999 ×
8-byte records** (confirmed). In the test project the arrangement is unused
(`bPlayArrangement = false`, `length = 1`) and every record holds the same
default (int32 `65536`, int32 `0`), so the two per-record fields **cannot be told
apart** and their meaning is **unknown**. `length` is *likely* the number of
sections in use. One export of a real arrangement would settle it.

## Tooling

[`../tools/project/parse_project.py`](../tools/project/parse_project.py) parses a
`.prj` (inflates `vltrgzip`+zlib) or a `.wav.dat`, and prints the tree or a JSON
schema (`--schema`). [`project-schema-1.50.json`](../tools/project/project-schema-1.50.json)
is the full generated schema. Writing has also been demonstrated: serialize the
ValueTree, `zlib`-compress the outer stream at level 1 (the inner
`Steps`/`Sections` blobs at level 6), and prepend the 8-byte `vltrgzip` magic.
With those levels a re-serialized project is **byte-identical** to the original
(verified on the test project and all 45 `.wav.dat`). Compressed ints are minimal
(`0` is the single byte `00`; bit 7 of the header byte marks a negative value). A
packaged writer tool is not included yet. Loading a computer-written file **on a
unit has not been tested**; a byte-identical rebuilt copy is the safest first
trial.
