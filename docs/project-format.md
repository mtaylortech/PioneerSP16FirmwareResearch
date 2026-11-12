# SP-16 project & sample file format — CONFIRMED against a real project

How the SP-16 stores a project and its per-sample metadata. **This is no longer
inferred:** it was validated by parsing a real `.prj` project byte-for-byte
(756,128 bytes, consumed exactly) and the accompanying `.wav.dat` files, with the
parser shipped in [`../tools/project/parse_project.py`](../tools/project/parse_project.py).
Verified on firmware 1.50 data; the 1.60 container is identical.

> **What was confirmed vs. still open.** Container, compression, the JUCE
> ValueTree encoding, and the full node/field schema (31 node types, real field
> names and types) are **confirmed** from a real file, which also re-serializes
> byte-for-byte (an independent writer reproduced it exactly; that writer is not
> yet shipped here). Still open: the fields of
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
| 12 … 151 | 35 × packed 32-bit word | **parameter-lock slots** — each word is `[vct:2 | value:22 (signed) | idx:8]`, not a float; empty = the packed `-32768` sentinel (`0x3f800000 | idx`). See below. |

`152 = 12 + 35×4`. Slot layout:

```
slot  0 … 22   → ParamIndex 0..22   (the 23 "main" lockable params)
slot 23 … 28   → FX unit 1          (sub-slots 0..5)
slot 29 … 34   → FX unit 2          (sub-slots 0..5)
```

**Slot encoding (confirmed from the 1.50 record writers).** Each 32-bit slot is a
packed word `[vct:2 | value:22 (signed) | idx:8]`, **not** a float32. The low byte
is the parameter index; the 22-bit middle field is `value = round(v × 2097151)`
(2097151 = 2²¹−1 = 127 × 16513); the top 2 bits are a value-change type. The
"empty" word `0x3f800000 | idx` is the packed `-32768` *no-lock* sentinel — the
same bit pattern an earlier pass misread as float `1.0`. Writers (1.50):
`FUN_0034f054` (ParamIndex, AsFloat), `0x34f0e4` (AsIndex), `0x34ef94`
(OnlyIndex); FX: `0x34f314` (AsFloat), `0x34f3f0` (AsIndex). A ParamIndex lock is
stored at byte `12 + 4·idx` (confirmed). Cross-check: the one real project's six
slot-6 locks decode exactly to 8/127, 9/127, 10/127 and 11/127 (packed upper
fields `0x020408`, `0x024489`, `0x02850a`, `0x02c58b` = 8..11 × 16513).

**FX slots (confirmed).** `FxParamIndex` has a flat **0–71** domain (bound-checked
at `0x34f40c`); the FX AsIndex writer `0x34f3f0` maps it through a 72-entry
signed-byte table to a sub-slot 0–5, so a slot is `23 + 6·unit + T[fxIdx]`. The
earlier open item "`FxParamIndex` 0–4 unexplained" no longer applies. *Likely:*
`FxParamIndex` is one flat list of per-effect parameters.

**Value classes (confirmed code paths; meanings hedged).**

- Ordinals 5–7 are normalized 0–127 (`value = k/127`); ordinal 8 is 0–127, or a
  **12-step** range when the AsIndex flag is set.
- Ordinals 0, 4 and 9–22 store a raw 22-bit integer.
- Ordinals 1–3 split their value base-1,411,200 (= 44,100 × 32, i.e. 32 s at
  44.1 kHz): the low part in their own slot, the high part in companion slots
  16/17/18. *Likely:* 1–3 are START / LOOP START / LENGTH in samples.
  *Guess:* 16–18 are overflow (high-part) slots, not standalone parameters —
  which could absorb some of the "extra" ordinals beyond the 21 manual track CCs.

**Still unknown: which parameter each `ParamIndex` ordinal is.** Static analysis
(Nov 2026) confirmed all 23 ordinals have writers but found **no** table mapping
an ordinal to any other ID, so the names are not recoverable from the binary
alone. An earlier reading — that the sequencer dispatch is keyed on MIDI CC
numbers — was **wrong**: those 12 values are `FxParamIndex` values (0–71) that
merely overlap the CC list that was searched, and nothing ties them to received
MIDI. The manual's CC map ([midi-implementation.md](midi-implementation.md))
names 21 step-lockable track parameters but does not give the ordinal order.

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
