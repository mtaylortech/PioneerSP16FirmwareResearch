# Insert, Master and Send FX processors

Part of [Effects and mixer in firmware 1.60](README.md). Findings F010, F016–F019,
F105, F141, F143, F149 and F154–F158, F176–F182 in the
[findings ledger](../../research-notes/F-effects/findings-ledger.md). Model:
[tools/fx/fx_processors.py](../../tools/fx/fx_processors.py).

## Summary

An **FX processor** hosts one effect slot. It owns one object of every effect type it
can run, selects one by index, drives its lifecycle and calls the shared
[EffectBase wrapper](effectbase.md) once per 64-sample block. There are three
processor classes:

- `InsertFxProcessor`: one per insert slot (two per track, FX1 and FX2).
- `MasterFxProcessor`: one, on the main bus.
- `SendFxProcessor`: one, on the send bus.

All three share `FxProcessorBase` and almost the same `setFxType` and processBlock. They
differ in a few stages: Insert has a **bypass crossfade**, Send has an **input mute**,
Master has neither (F154). Three flag bytes control them: **bypass `+0x9c`**,
**start mode `+0x9d`** (dormant in 1.60) and **disable `+0x9e`** (F155, F157, F176–F178).

The model `fx_processors.py` (with `effectbase.py` and the per-effect models) is
**bit-exact to the 1.60 routines run in a single-function emulator**: 68 / 68
type-matrix and type-change cases, all 10 types disabled, 97 / 97 start-mode cases and
14 / 14 bypass cases (F154, F155, F176, F181). Nothing was measured on an SP-16.

## Where they sit

- Each track has two `InsertFxProcessor`s in series, FX1 then FX2, after the output
  selectors and before pan (F136; see [signal-flow.md](signal-flow.md#track-strip)).
- `MasterFxProcessor` runs in place on the main sum; `SendFxProcessor` runs in place on
  the send sum. The Send return is added after the Master FX
  ([signal-flow.md](signal-flow.md#send-bus-and-master-bus), F103, F106).
- The FX mode ("EffectModeSend" / "EffectModeMaster") enables one of Master and Send
  through the disable flag (F105, F155).

## Object fields

`FxProcessorBase` fields (constructor `0x1128cc`) (F016, F154):

| Offset | Contents |
|---|---|
| `+0x80` / `+0x84` / `+0x88` | Effect list: data / capacity / count (10) |
| `+0x8c` | Pointer to the `current` effect (written at the swap, and by setFxType from Off) |
| `+0x90` | Pointer to the `pending` effect |
| `+0x94` | Tempo provider; its vtable `+0x1c` returns the tempo as a double (BPM) |
| `+0x9c` | **Bypass** byte (ctor 0). Read only by the Insert processor |
| `+0x9d` | **Start mode** byte (ctor 1). Nothing in 1.60 changes it (F178) |
| `+0x9e` | **Disable** byte. Ctor: Insert 0, Master 1, Send 1 |

Per-processor offsets (F017, F019, F154):

| | Insert | Master | Send |
|---|---|---|---|
| Constructor | `0x118b0c` (new 0x148) | `0x114bc0` | `0x11bbe4` (new 0xb0) |
| Vtable | `0x842c10` | — | `0x842d40` |
| current / pending index | `+0xa4` / `+0xa8` | `+0xa0` / `+0xa4` | `+0xa0` / `+0xa4` |
| Other | `+0xa0` = ctor arg 1 (track index, *likely*); dry copy `+0xb8`; bypass `MuteSmoother` `+0x144` | — | input `MuteSmoother` `+0xa8` |
| processBlock (slot 5) | `0x116860` | `0x112acc` | `0x119994` |
| setFxType (slot 47) | `0x11735c` | `0x1132e4` | `0x11a254` |
| prepareToPlay | `0x116bc4` | `0x112cd0` | `0x119bd8` |

Both indices are −1 (Off) after construction. The effect array order per processor is
in [README.md](README.md#status) (F016, F019).

## processBlock

All three run on 64 frames, a hard-coded count (F010, F154). In order:

**Insert `0x116860`** (F017, F022, F149, F157):

1. Copy the input to the dry buffers at `+0xb8`. Set the bypass `MuteSmoother` to the
   bypass byte `+0x9c`.
2. If current ≥ 0, call the current effect's slot 9. If it returns 0: current :=
   pending. If pending ≥ 0 and `+0x9e` = 0: slot 5(e, 0, 1), then slot 7(e, 0) if `+0x9d`
   ≠ 0, else slot 8.
3. If 0 ≤ current < count: the per-index feed (below), then slot 18(e, L, R, 64).
4. The bypass crossfade `0xe8228` between the processed block and the dry copy.

**Master `0x112acc`** = Insert without the input copy and without the bypass stage
(F154). Poll slot 9 when current ≥ 0; swap at 0; slot 5(e, 0, 1) and slot 7 or 8 only if
pending ≥ 0 and `+0x9e` = 0; feed; slot 18; return.

**Send `0x119994`** = Master plus an input mute before everything (F154):

1. Mute flag = 1 if pending = −1; else 1 if `+0x9e` ≠ 0; else `+0x9d` XOR 1. Set the
   input `MuteSmoother` `+0xa8` to it and run it in place.
2. Poll slot 9 and swap only if current ≥ 0 **and** `+0x9e` = 0. Slot 5 is called as
   (e, 0, 0).
3. Feed, slot 18.

The third slot-5 argument only arms the EffectBase skip, and the Master/Send
constructors clear `+0xa8` on all ten effects, so the (e, 0, 0) vs (e, 0, 1) difference
has no effect (F154; H063 refuted).

**Off** (current −1): Master leaves the bus untouched; Send mutes it; Insert still runs
its bypass crossfade stage (F154).

## setFxType (slot 47)

Master `0x1132e4` and Send `0x11a254` are identical code; Insert `0x11735c` differs only
in offsets (F017, F154):

- If n = pending: return.
- If current = −1: current = pending = n (verbatim, no normalisation of n < 0), and both
  effect pointers := array[n] (0 if n ≥ count). The type takes effect at once.
- Otherwise: the old effect gets **slot 6(1.0f)** (start fade-out); pending := n, or −1
  if n < 0; `+0x90` := array[n] or 0.

The old effect gets slot 6 on **every** call while current ≠ −1. A change during a
fade-out re-arms it, and the intermediate type is never activated (F154).

### Sequence of a type change

A type change is **sequential, not an overlapping crossfade** (F142, F149, F154):

1. setFxType: old effect slot 6; it fades to dry over 147 samples (160 at 48 kHz).
2. Each block: slot 9 of the old effect. The swap happens at the first block where it
   returns 0, three blocks after setFxType.
3. The new effect gets slot 5 (which calls its slot-27 reset) and slot 7, and fades in
   over 147 samples.

On a stand-in Insert processor the four blocks after a swap peaked at 0.680, 0.876,
1.000 and 0.954 (F142). With `+0x9d` = 0 the swap happens after one block, and slot 8
runs instead of slot 7 (F149).

## The three flags

| | Bypass `+0x9c` | Start mode `+0x9d` | Disable `+0x9e` |
|---|---|---|---|
| Processors | Insert only | all three | all three |
| Setter | `0x1129b4` | `0x1129bc` | `0x112a08` |
| Who sets it in 1.60 | Insert manager: track menu F5/F6 and scene reload (F179–F182) | **nobody** (F178) | FX-mode routing (F105) |
| Effect keeps running? | **yes**, behind the crossfade | gate mode 0: yes, wet fades out | no: slot-6 fade, then not polled (Send) |
| Output | 132-sample crossfade to the dry copy | Master/Insert: dry after 147 samples; Send: 0.0 | Master: dry; Send: 0.0 |
| Findings | F157 | F176–F178 | F155 |

### Bypass `+0x9c` (Insert)

Setter `0x1129b4` stores the byte; only the Insert processBlock reads it (F157). Per
sample:

```math
L = \mathrm{f32}\!\left(\mathrm{f32}\!\left(\mathrm{dry}\cdot(1-g)\right) + \mathrm{f32}(g\cdot L)\right)
```

g comes from the bypass `MuteSmoother` and goes 1 → 0 over N = **132 samples at
44.1 kHz** (144 at 48 kHz). Once fully bypassed, L := the dry copy (memcpy). The effect
keeps running behind the bypass. Output equals the dry input from sample 132 after
`0x1129b4(p, 1)` (F157). This corrects the earlier "128 samples" (F158).

Quirk: on an Off insert the ramp changes the signal by at most 1 ulp (54 samples, max
relative 1.06e-7), from the double rounding of dry·(1 − g) + g·dry (F157).

### Disable `+0x9e`

`0x112a08(p, flag)`: if `+0x9e` already equals flag, return. Otherwise store it; on
disable, call the current effect's slot 6(1.0f). Re-enable calls nothing itself
(F105, F155).

- **Master disabled:** the effect fades to dry over 147 samples; the output equals the
  input bit for bit from sample 147. Delay and reverb tails are cut, not left to ring.
  While disabled, Master still polls: a setFxType swaps `current` at once, without
  slots 5/7/8 (F155).
- **Send disabled (or Off):** the input ramps to 0 over 132 samples and the effect's
  fade ends at 147, so the output is exactly 0.0 from sample 147 (132 when the wet path
  is already silent). While disabled, Send neither polls slot 9 nor swaps (F155).
- **Re-enable:** at the next block slot 9 = 0 → swap → slot 5 + slot 7, a full
  re-activation including slot 27 (for example the Send Reverb warm-up restarts). Send
  adds a 132-sample unmute ramp. A quick off → on during the fade-out does not cancel
  it: the effect fades to dry and re-activates about three blocks later (F155).
- **FX mode** (CompositeFxUnit `+0x1f8`): mode Send enables Send and disables Master, so
  the main bus passes dry; mode Master does the reverse, so the Send return is digital
  silence; mode > 1 disables both (F105, F155). Device audibility *likely*. Whether
  anything upstream skips calling a disabled processor was not emulated (statically:
  no, F105).
- Master and Send are constructed **disabled** (`+0x9e` = 1) until the FX-mode routing
  calls `0x112a08(p, 0)` (F154).

### Start mode `+0x9d` (dormant)

`0x1129bc(p, v)`: if the pending effect pointer `+0x90` is 0, return without storing
(the value is lost while Off). Otherwise store v; if disabled, return; else call the
pending effect's slot 7(e, 0) if v ≠ 0, slot 8 if v = 0. There is no old-value check
(F176).

What it would do (F177): v = 0 runs slot 8, "effect off, tails ring out". It is **not**
an instant start. Gate mode 0 effects keep receiving input but their wet output fades
out: the output equals the dry input from sample 147 (Master, Insert). Mode 1 effects
(delays, reverb) close their input and let tails decay. Send also mutes its input. v = 1
fades the wet back in.

**Nothing in 1.60 calls the setter** (F178, `confirmed` static). The UI "FX ON/OFF"
functions (`ModelInterface::setSendMasterFxOnOff` `0x300e30`, `setInsertFxOnOff`
`0x304470`) only format and log a message, and their getters return 0. So `+0x9d` stays
at its constructor value 1 on all processors. The model's `set_start_mode` is a
documented, dormant path. Whether the FX ON/OFF button is shown on the device was not
read (*likely* drawn, F178).

### MuteSmoother

Used by the Insert bypass and the Send input mute (F154): constructor `0xe7fd8`,
setMuted `0xe8050`, process `0xe808c`, crossfade `0xe8228`.

- N = roundToInt(f32(f32((int)fs)·0.001f)·3): 3 ms, **66 / 132 / 144 / 288** samples at
  22.05 / 44.1 / 48 / 96 kHz, set by prepareToPlay.
- setMuted: remaining := N − remaining, step ±1/N. process: out = f32(in·g), g
  accumulated in float. At the muted end it zero-fills; unmuted, g = 1 idle.
- Insert and Send create it only while the pointer is null, so the **first**
  prepareToPlay fixes N.
- The Send smoother is created unmuted, so a Send that starts Off passes one 132-sample
  decaying ramp of the bus after prepareToPlay (F154).

## Per-index parameter feed (tempo)

Before slot 18, processBlock feeds the current effect by its index (F017, F088, F143,
F156). It also feeds an effect that is fading out before a swap.

| Processor | Indices fed | What |
|---|---|---|
| Insert | 0 Chorus, 4 Delay, 1 Flanger, 8 Phaser | slot 14(e, 7, clamp(f32(tempo), 1, 999)) |
| Insert | 9 Ducker | tempo as above, then the trigger table: SOURCE row → TRIGGER (8) and OFFSET (9); see [ducker.md](ducker.md) |
| Master, Send | 0 Delay, 2 Chorus, 3 Flanger, 9 Phaser | slot 14(e, 7, clamp(f32(tempo), 1, 999)) |

The tempo is read from the provider at `+0x94` (double → float) and clamped to 1…999
BPM. Insert table `0x11694c`; Master `0x112b4c`, Send `0x119a40`. The feed matters only
with SYNC on: removing it leaves a free-running Chorus unchanged, while a synced Chorus
or Delay differs. Eight sync cases (tempo 120, 140, 60.5, 2000 → 999, 0.1 → 1) are
bit-exact (F156). SYNC itself is on [parameters.md](parameters.md).

## Slot-52 defaults

After building the effects, each processor constructor calls its own slot 52, a 10-case
switch that sets normalised defaults on every effect through slot 14 (F016, F143, F156).
The parameter manager's reload with r1 ≠ 0 calls the same defaults again before
re-applying the project's values (F181). Per-effect values are on each effect page.
Across processors (F156):

- Chorus, Flanger, PEQ, MMF, LoFi, Distortion and Phaser defaults are identical on
  Insert, Master and Send, **including Chorus Mixratio 0**.
- The Master/Send compressor = the Insert compressor plus (index 6, 0.0).
- Master and Send differ only in the Delay and Reverb Mixratio: **0.5 on Master, 1.0 on
  Send**.
- "Chorus on Master/Send outputs dry" therefore holds at the processor defaults only.
  Whether the parameter manager or the project overwrites them on the device is
  untested (F156).

## Insert bypass sources (summary)

Details are on [parameters.md](parameters.md) (F179–F182). In short:

- The bypass setter has exactly two callers, both Insert parameter-manager code: the
  manager's slot 42 (from the UI) and its per-block update slot 10 (from reload) (F179).
- The stored state is the project property `bBypass` = `prj::EffectData` `+0x29`, one
  per scene per insert slot (16 scenes + 1 dummy) (F180).
- It reaches the processor live from the track menu, and on a **scene** change (not a
  pattern change within a scene) at the start of the next block (F181).
- The device control: track-menu F5 toggles FX1 bypass and F6 toggles FX2 bypass of
  the current track, on Sample and Thru tracks (*likely*), when the track menu's bypass
  mode is on (F182; on-screen naming *likely*).
- Master and Send have no audible bypass: their manager can write `+0x9c`, but their
  processors never read it (F157, F182).

## Load estimate (slot 45)

Slot 45 returns a per-index number from a 10-entry table, `likely` the effect's CPU
load estimate (F017, F143): Insert `0x842be0` = [19, 21, 22, 19, 24, 26, 30, 22, 26, 14];
Master `0x842a78` = Send `0x842d10` = [31, 167, 19, 21, 22, 20, 22, 31, 22, 27]; 1 for
Off.

## 1.60 code map

| Address | What it is |
|---|---|
| `0x1128cc` | FxProcessorBase constructor (tempo provider at `+0x94`) |
| `0x1127a4` | FxProcessorBase destructor (destroys every effect) |
| `0x118b0c` / `0x114bc0` / `0x11bbe4` | Insert / Master / Send constructor (build 10 effects, slot 52) |
| `0x116860` / `0x112acc` / `0x119994` | Insert / Master / Send processBlock |
| `0x11735c` / `0x1132e4` / `0x11a254` | Insert / Master / Send setFxType (slot 47) |
| `0x119900`, `0x116838` | Insert slot 46 (current) / slot 48 (pending) getters |
| `0x116bc4` / `0x112cd0` / `0x119bd8` | Insert / Master / Send prepareToPlay |
| `0x117434` (table `0x117448`) / `0x1133f4` (`0x113408`) / `0x11a364` (`0x11a378`) | Slot-52 defaults |
| `0x11694c` / `0x112b44` / `0x119a38` | Per-index feed tables |
| `0x1129b4` | Bypass setter (`+0x9c`) |
| `0x1129bc` | Start-mode setter (`+0x9d`); reader `0x11cae0`; manager thunk `0x11caf4` |
| `0x112a08` | Disable (`+0x9e`); from manager slot 9 `0x11cafc` |
| `0xe7fd8` / `0xe8050` / `0xe808c` / `0xe8228` | MuteSmoother ctor / setMuted / process / crossfade with dry |
| `0x112774` | FxProcessorBase slot 49 → effect slot 10 (retrigger) |
| `0x1126dc` / `0x1126fc` | FxProcessorBase slot 29 / 21: slot 14 / 15 on the pending effect |

## Validation evidence

- **Insert processor** (F149): the model's `InsertProcessor` matches the real setFxType
  and processBlock bit-exactly through 5 → 7 → 3 → 7 → 5 → Off → 7 and an independent
  set of schedules (rapid changes, re-select during fade-out, compressor stopped inside
  its skip, `+0x9d` = 0).
- **Master and Send** (F154): real processor constructors (all 10 effects + slot 52),
  real prepareToPlay, setFxType, processBlock, disable and bypass. 60 type-matrix cases
  (both processors × 10 types × noise/sine/impulse × 200 blocks) and 8 FX-change
  schedules (240 blocks): 68 / 68 bit-exact in output, processor state, slot 5–8/14 call
  log and wrapper state every block. None is a dry pass-through. Hashes c3m `6a4831a4…`,
  c3s `3784449b…`, c4 `b7ae13f4…`, c5 `7fc3a191…`, c6b `42e42dfe…`, reproduced by the
  independent review.
- **Independent tests** (F154): all-type disable 40 / 40, random schedules including raw
  `+0x9d` toggles and tempos 0 / −3 / 999.5 / 5000 30 / 30, Insert bypass fuzz 10 / 10 (a
  control without bypass fails), real prepareToPlay mute lengths at 22.05 / 44.1 / 48 /
  96 kHz.
- **Disable** (F155): all 10 types on each processor.
- **Start mode** (F176): 97 / 97 bit-exact cases on all three processors (hashes
  c3_outputs `ccc863bc…`, c3f_outputs `90128ff2…`); 14 wrong-setter variants all fail.
- **Bypass sources** (F181): 14 / 14 cases through the real manager code bit-exact
  against `fx_processors.py` (243,200 samples, 6 types + Off; output hash
  `9020d25d…`); 6 / 6 refuted alternatives fail.
- Verifier scripts (reference only, need your own 1.60 files):
  `tools/fx/verify/H077_master_send_proc.py`, `H079_fx_onoff.py`,
  `H079_r2_propagate.py`, `H080_bypass_sources.py`.

## Unknowns

- The Insert Ducker feed (index 9) is not in `fx_processors.py`; its
  `InsertProcessorFull` raises an error for it. The Ducker page and model describe the
  feed (F088).
- Whether the FX ON/OFF button is shown on the device, and what the user sees when
  pressing it (F178).
- Device audibility of the FX-mode switch (*likely*, F155).
- Who calls the scene-dummy redirect (H091), and the exact project-load reload
  sequence (*likely*, F181).
- Whether the processors are ever rebuilt (H073).
- Non-integer sample rates and a sample-rate change while running are not modelled
  (F149, F154).
- See [open-questions.md](../open-questions.md#effects).

## Model

[tools/fx/fx_processors.py](../../tools/fx/fx_processors.py): pure Python, own code, no
firmware bytes. It contains `MuteSmoother`, `MasterProcessor`, `SendProcessor` and
`InsertProcessorFull` (with the bypass stage). Effects are
[effectbase.py](../../tools/fx/effectbase.py) `EffectBase` objects wrapping the
per-effect slot-25 models. `set_disabled`, `set_start_mode`, `set_bypass` and
`set_fx_type` follow the setters above; `feed(idx, eb, bpm)` is a caller-supplied
function that writes slot 14 index 7 on the per-effect model. The default tempo
provider returns 120 BPM.
