# Signal flow of the 1.60 audio engine

Part of [Effects and mixer in firmware 1.60](README.md). This page follows the audio
from each track's source to the converters and the headphone output. It gives every
stage's position, gain law and ramp, the graph channel numbers and the 1.60 addresses.
The effects themselves are on their own pages. Findings F095–F114, F187–F191 and
F209–F213 in the
[findings ledger](../../research-notes/F-effects/findings-ledger.md). All addresses are
1.60 virtual addresses.

## Summary

- Everything below runs in 32-bit float on the CPU, inside one JUCE audio callback per
  block (F013, F095). The app requests **44,100 Hz and 64-frame blocks** (F014); every FX
  processor processes exactly 64 samples per call (F010, F154). That one ALSA period is
  one callback is *likely* (H016).
- **Per track:** source → output selectors → **FX1 → FX2** → pan → mute → **send tap** →
  fader (F095, F136, F191).
- **Buses:** all tracks are summed at gain 1.0 with no headroom scaling into a main pair
  and a send pair (F098). Master FX runs on the main sum and Send FX on the send sum,
  in place (F103).
- **The Send FX return is added after the Master FX**, together with a further MTU pair,
  and then the master fader applies (F106). No stage on the CPU path limits or clips
  (F106, F109).
- **Outputs:** a main-output selector, the analog-filter drive stage, then a per-pair
  output volume, a fixed **−0.5** gain on every DAC channel and a bulk mute (F107,
  F109–F113, F212).
- **Headphones:** one selected input pair plus three monitor pairs (F209, F210, F213).

## Diagram

```
 per track t (TrackUnit 0x1ca58c, 16 tracks)
 ───────────────────────────────────────────
 PlayerUnit (sample/MIDI) ─┐
 audio input (THRU track) ─┴─ OutputSelector +0x10c ─┬─ main ── OutputSelector +0x110 ── FX1 ── FX2 ──
                                                     └─ ch4/5 (raw source, DSF send in mode 1)
   ── OutputSelector +0x118 (ch4/5 = post-insert, DSF send in mode 2) ── OutputSelector +0x114 (main or DSF return)
   ── Pan +0x128 ── Mute#1 +0x12c ──┬── VolumeKnob +0x138 (send level) ── track ch2/3 (send)
                                    └── VolumeFader +0x134 (track fader) ── track ch0/1 (main)

 MultiTrackUnit 0x1c4ff8 (6 in / 16 out)
 ───────────────────────────────────────
 Σ track ch0/1 (gain 1.0) ───────────── MTU out0/1 ──▶ CompositeFxUnit ch0/1 ── Master FX (in place)
 Σ track ch2/3 (gain 1.0) ───────────── MTU out2/3 ──▶ CompositeFxUnit ch2/3 ── Send FX (in place)
 selected track ch4/5 ───────────────── MTU out4/5 ──▶ dsfDriveSend
 each track ch0/1 (assignable) ──────── MTU out6…13
 own input units ─────────────────────── MTU out14/15 (likely input/THRU path, not traced)

 SendFxUnit 0x1b3068: SendFxProcessor ── return VolumeFader ── (meter)

 MasterOutUnit 0x1b2150
 ──────────────────────
 Master FX out + Send return + MTU out14/15 (gain 1.0) ── master VolumeFader ── out0/1
                                                                            └── copy → out2/3 (to headphone in0/1, unused)

 Output12Router 0x1b2610: [master out0/1 | MTU out6/7] ── dsfDriveMaster 0xc3ce8 ──▶ deviceOut (0,1) and (12,13)
 MTU out8/9, 10/11, 12/13 ───────────────────────────────────────────────────────▶ deviceOut (2,3), (4,5), (6,7)
 HeadphoneUnit 0x1b10ec ─────────────────────────────────────────────────────────▶ deviceOut (8,9)
 dsfDriveSend ───────────────────────────────────────────────────────────────────▶ deviceOut (10,11)

 AudioDeviceOutputUnit 0x1ae3e4, per pair: OutputVolume ── FixedAttenuator (−0.5; +0.5 on pair 6) ── BulkMute (all 14 ch)
 device ch 0/1 master · 2–7 assignable outs · 8/9 headphones · 10/11 analog-filter send · 12/13 resample recorder (internal)
```

Channel numbers in the diagram are graph channels. The graph connections are decoded
from the product graph builder `0x1bc8d4` (30 rows, F102) and the base builder
`0x1b6284` (F109).

## Track strip

Built per track by `HexaTrackAudioSystem::constructTrack` `0x1bacec`: a `TrackUnit`
(`new 0x628`, ctor `0x1cceb0`) with its `PlayerUnit`, `LfoProcessor`, MIDI managers and,
per insert slot, an `InsertFxProcessor` (ctor `0x118b0c`) and an
`InsertFxParameterManager` (ctor `0x12864c`) (F095). 1.60 builds **two insert slots for
every track type** (F132).

`TrackUnit::processBlock` `0x1ca58c` runs, in this order (F095):

| # | Stage | Object | Notes |
|---|---|---|---|
| 1 | Source | `PlayerUnit` (+0xcc) | renders track ch0/1. A THRU track takes the audio input instead (selector +0x10c, set by `setTrackType` `0x1cb584`) (F189) |
| 2 | Output selectors | `OutputSelector` +0x10c, +0x110 | +0x110 picks the main source: the track source, or the analog-filter return in mode 1 (F187) |
| 3 | Inserts | `InsertFxProcessor` slots 0…n−1, processBlock `0x116860` | FX1 then FX2, in series (F136) |
| 4 | Output selectors | +0x118 (ch4/5), Mute#2 +0x130, +0x114 | analog-filter send and return points (F187) |
| 5 | Pan | `Pan` +0x128 | linear balance, see below (F097) |
| 6 | Mute | Mute#1 +0x12c | 128-sample `MuteSmoother` (F100) |
| 7 | Send tap | copy → track ch2/3, `VolumeKnob` +0x138 | post-insert, post-pan, post-mute, **pre-fader** (F099) |
| 8 | Fader | `VolumeFader` +0x134 | track ch0/1 (F096) |
| 9 | Meter, renderer, MIDI formatter | +0x13c, +0x108 | read-only taps |

Gain laws (all with the same linear **100-sample ramp**: step = (target − current)/100,
starting at the parameter's sample offset and crossing block boundaries; F096):

- **Track fader** (`VolumeFader` slot 13 `0xe9e48`): table `0x83e050`, index 0…127.
  0 → silence; 1…9 → −54, −50, −48, −46, −45, −44, −43, −42, −41 dB;
  10…100 → (i/100)²; 101…127 → 2^(ln(i/100)/ln 1.27). Index 100 = 0 dB (the default),
  127 = ×2 (+6.02 dB) (F096).
- **Send level** (`VolumeKnob` slot 13 `0xe9f08`): the same table × 0.5, so 127 → 1.0 and
  100 → 0.5 (F096).
- **Pan** (`0xe9594`): linear balance, 0 dB in the centre, range −64…+64. For p < 0:
  L = 1, R = (64 + p)/64; for p > 0: L = (64 − p)/64, R = 1. No cross-feed: an L-only
  source panned to +64 is silent. Constant-power, square-root and −6 dB-centre laws were
  tested and refuted (F097).
- **Mute:** a muted track sends nothing; pan affects the send; the fader does not (F099).

Object layouts of `TrackUnit`, the 0x24-byte parameter struct (value, step-lock value,
LFO modulation, sample offset), `Pan`, `Volume`, `Mute` and `OutputSelector`, with their
writers, are in F100.

Model: `tools/fx/track_mix.py`, bit-exact to the emulated strip and summing for normal
audio (about 2.3 M samples) (F101). With denormal input, the real `OutputSelector`
×1.0 passes flush denormals in their NEON part, which the model does not reproduce
(24,797 of 645,120 denormal samples differ; 0 on normal audio) (F101, H053).

## Analog-filter loop

The routing mode at `TrackUnit` +0x61c, set by slot 101 `0x1ca218`
(`setSendSource`), is the send/return loop through the analog (Dave Smith) filter for
one track (F187):

| Mode | UI ("ANALOG FILTER SETTING") | DSF send (track ch4/5) | Main path |
|---|---|---|---|
| 0 | filter not on this track | source, but Mute#2 closed (silent) | FX(source) |
| 1 | Insert Order "Pre FX" | source | FX(filter return) |
| 2 | Insert Order "Post FX" | FX(source) | filter return, inserted after the inserts and before pan |

- The send tap (stage 7) always taps the selected main path (F187).
- Switching mode fades each changed selector to silence over 128 samples and then up
  over 128 samples: a **256-sample dip**, not an overlapping crossfade (F187).
- At most one track is in mode 1 or 2 at a time. `DaveSmithManager` (`0xc64b0`) sets
  the mode from the project's routing data (`bDaveSmithFilter`, `daveSmithRouteMode`,
  `daveSmithSendMode`, `daveSmithSendTrack`) (F188). The UI is the Mixer view popup
  "ANALOG FILTER SETTING": "Insert Track" (Master, Track 1…16) and "Insert Order"
  (Pre FX / Post FX) (F188).
- The return buffer (+0x608) is MTU in4/5, which is device input ch2/3, in the same
  callback: the digital side adds **no block delay**. The analog round-trip latency was
  not determined (F189, F191).
- The DSF send output MTU out4/5 is **the selected track's** ch4/5, not a sum of all
  tracks (F190, which corrects F098).
- That modes 1 and 2 are reachable at run time is *likely*: they need
  `bDaveSmithFilter` ≠ 0, and no caller of the filter on/off setters was found (F188,
  H093). Whether the return gate is ever closed is open (F189, H094). The filter itself
  is analog hardware and out of scope (H008).
- The "FilterPosition" strings belong to the LoFi effect, not to this loop (F188).

## Send bus and master bus

- **Bus sums** (`SimpleTwoMixUnit` `0x1535f8`): float additions at gain 1.0 in track
  order. A normalise flag that would apply 1/(N+1) exists but is 0, so there is **no
  headroom scaling** (F098).
- **CompositeFxUnit** `0x1a94cc` points two views at graph ch0/1 and ch2/3 and runs
  `MasterFxUnit` on ch0/1 and `SendFxUnit` on ch2/3, **in place**, inline or as two jobs
  on the parallel worker pool. It does no mixing (F103).
- **One stereo send bus** (F104). `SendFxUnit::processBlock` `0x1b3068`:
  `SendFxProcessor` → **return fader** (`VolumeFader`, same table and 100-sample ramp as
  the track fader, default 100 = 0 dB) → meter (F104). There is no dry path around the
  Send FX: the return is what the effect's own wrapper leaves in the send buffer (F104).
  An Off or disabled Send FX mutes its input over 132 samples and returns silence
  (F104, F155).
- **FX mode** (`CompositeFxUnit` +0x1f8, project routing data): "EffectModeSend" enables
  the Send FX and disables the Master FX; "EffectModeMaster" does the reverse (F105). A
  disabled Master FX passes the main bus dry (F155).
- **MasterOutUnit::processBlock** `0x1b2150`: out = Master FX output + Send return + MTU
  out14/15 at gain 1.0 → **master fader** (`VolumeFader`, F096 table, 100-sample ramp) →
  peak meter → renderer tap → out2/3 := copy of out0/1 (F106).
- So the order is: tracks → main sum → Master FX ‖ send sum → Send FX → return fader;
  then main + return + MTU14/15 → master fader. **There is no limiter on this path**
  (F106).

Model: `tools/fx/bus_mix.py`, bit-exact to the emulated CompositeFxUnit → SendFxUnit →
MasterOutUnit chain with stand-in FX processors (860,160 channel-samples) (F108).

## Main output and headphones

- **Output12Router** `0x1b2610` (the graph's "master assignable selector") picks the
  main output: output mode "Master" (`M + 6ch`) → master out0/1; "4Assign" (`8ch`) → MTU
  out6/7. A change is a 128 + 128-sample dip (F212).
- **DSF drive** (`DaveSmithDriveUnit` `0xc3ce8`): gain 1 + 3·(i/1023)² for i = 0…1023
  (0 to +12.04 dB), 100-sample ramp, default 1.0, then a clip meter that only reads
  levels. One instance on the main output (`dsfDriveMaster`), one on the DSF send
  (`dsfDriveSend`) (F107).
- **Headphones** (`HeadphoneUnit::processBlock` `0x1b10ec`, 14 inputs) (F209, F210):
  1. `HeadphoneRouter` replaces ch0/1 with **one** selected input pair. Sources:
     CueMaster or Cue12 → in2/3; Cue34/56/78 → the assignable outs (MTU 8…13);
     Cue1…Cue8 → one channel, duplicated to both sides (F209). In output mode "Master"
     the UI offers CueMaster, Cue34, Cue56, Cue78 and Cue3…Cue8; in "4Assign" it offers
     Cue12, Cue34, Cue56, Cue78 and Cue1…Cue8 (F211).
  2. Three monitor pairs from `RecMonitorUnit` are **added at gain 1.0**; with CueMaster
     each has a 44-sample gate (F210). Their identities (preview, metronome, input
     monitor) are a *guess* (H105).
  3. An optional crossfade to the audio input (in11/12), length (int)(fs × 0.001); it is
     *likely* dormant in 1.60 (F210).
  4. `VolumeKnob` (F096 table × 0.5, 100-sample ramp) → peak meter.
- The master-fader copy (MasterOutUnit out2/3 → headphone in0/1) is wired but never
  selected, so it is *likely* never heard (F209, F213). What in2/3 carries in normal use
  (the analog-filter return, i.e. the main output after the filter) is a *guess* (H104).
- Selector switches are a 128-sample fade-out and a 128-sample fade-in. Quirk:
  re-selecting the current pair during its fade-out leaves the selector at gain 0 until
  the next change (F209).

Model: `tools/fx/headphone_mix.py` (HeadphoneUnit and Output12Router), bit-exact given
the cue-source and monitor inputs (F213).

## Device output stage

`AudioDeviceOutputUnit` (ctor `0x1ae7dc`, processBlock `0x1ae3e4`) is the last stage
of every output: 7 stereo pairs, 14 channels, in place (F109).

| Device pair | Channels | Source |
|---|---|---|
| 0 | 0/1 | main output (`dsfDriveMaster`) |
| 1–3 | 2–7 | assignable outs (MTU out8…13) |
| 4 | 8/9 | headphones |
| 5 | 10/11 | analog-filter send (`dsfDriveSend`) |
| 6 | 12/13 | internal copy of the main output to the resample recorder |

Per pair: **OutputVolume** → **FixedAttenuator**; then **BulkMute** on all 14 channels
(F109).

- **OutputVolume**: index 0…1023, gain = table[i]/32767 from a 1024-entry
  hand-drawn taper (0 = mute, 1 = −44 dB, 100 = −32.4 dB, 512 = −14.2 dB, 1008…1023 =
  0 dB), 100-sample ramp (F110). The table is firmware data and is not reproduced; the
  model reads it from your own 1.60 binary (see [tools/fx/](../../tools/fx/)).
- **What drives it:** one panel pot (`UIVolume` id 1, through
  `OutputVolumeController`) sets the three assignable pairs and the headphones together,
  and only gates the main output and the resample feed (mute at 0, otherwise full).
  Pair 5 (DSF send) is never changed (F113). Which physical knob id 1 is (MASTER or
  PHONES) is a *guess* (F113).
- **FixedAttenuator**: a compiled-in constant, **−0.5 on pairs 0–5** (all 12 DAC
  channels: −6 dB and inverted polarity) and +0.5 on pair 6. That the inversion is
  undone by inverting analog stages is a *guess* (F111, H059).
- **BulkMute**: a 64-sample linear mute of all outputs, triggered only by the switch to
  and from the renderer mode (*likely* bounce/export); at start-up it is unmuted with no
  fade (F112).
- No clip, limiter or integer conversion happens in this unit; the floats go on to the
  JUCE ALSA device. The float-to-integer conversion there was not checked (F109, H015).

Model: `tools/fx/device_out.py`, bit-exact to the emulated unit (about 1.5 M
channel-samples plus denormal cases) (F114).

## What is not covered

- The ALSA copy stage that moves graph channels to the three DAC devices, and the
  codecs (H015, H017).
- The live-input, THRU and MultiTrackUnit input units that feed MTU out14/15 (H054), and
  the input gain stage (H059).
- The renderer-mode state machine that triggers the bulk mute (H061).
- The analog filter itself (H008).
