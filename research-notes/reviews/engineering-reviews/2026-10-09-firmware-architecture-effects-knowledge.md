<!-- source: engineering-reviews/2026-10-09-firmware-architecture-effects-knowledge.md | scrubbed -->

# What we know about firmware architecture and effects

Reviewed October 9, 2026, America/Chicago, in response to a request to assess the research documentation and project history. Read-only evidence assessment; no guest, hardware, build or deployment action. Current runtime status comes from README and the latest timer handoff; historical PROJECT_STATE is used for static findings and their qualifications, not its superseded startup status.

## Assessment

We have a well-supported model of the update container, intended platform startup and selected original application paths. We do not yet have an implementation-level model of the sampler, sequencer or effects. Recent startup and rendering milestones improve our ability to investigate those features but do not themselves identify their algorithms.

| Area | Established knowledge | Confidence limit |
| --- | --- | --- |
| Firmware packaging | Held 1.50 and 1.60 updates decode using sector-reset AES-256-CBC into validated ISO filesystems; a 20-byte plaintext version/CRC trailer accompanies the ciphertext. Payloads contain rootfs archives, SquashFS libraries/resources, kernel, bootloader, application and panel firmware. | Decryption and CRC consistency do not prove all updater acceptance checks or a deployable repacker. |
| Platform startup | Shipped artifacts identify Linux 3.0.101, BusyBox and U-Boot. Extracted scripts connect init to rcS, rc.local, apl_start and EP085_Main_R. Supplied initramfs source describes RAM-root assembly and SquashFS mounts. | Supplied initramfs was not matched to a carved release initramfs; physical boot and exact source-to-binary reproduction are unverified. |
| Main application | EP085_Main_R is an approximately 12 MB stripped ARM32 executable with original machine code and dynamically linked libraries, including libstdc++, ALSA, X11 and FreeType. Localized instruction and runtime analysis is available. | Proprietary application source has not been identified. Library imports do not allocate every feature to a particular implementation or prove original source language throughout. |
| Audio/runtime organization | Original ALSA playback/capture open and read/write calls execute under a null fixture, with sampled 64-frame transfers. Original thread names and requested core masks include Juce ALSA, ALSAInput, ProjectManager and AudioWorkerSC3/4. | Null I/O is synthetic. Affinity is not enforced in the emulator; thread names and masks do not map individual effects, establish DSP correctness or measure physical CPU load. |
| UI | Original resource loading, constructor returns, natural event dispatch, timer service and XPutImage are matched. Exact 800×480 output shows HOME behind LOAD PROJECT / LOADING. | Full startup, project-load completion, persistence and input response remain unproved. Latest observation ended on an observer correlation failure; native zero exit is not clean completion. |

Sources: [static architecture and classifications](../../history/docs__PROJECT_STATE.md), [evidence ledger](../../history/docs__EVIDENCE_LEDGER.md), [synthetic audio runbook] `../experiments/emulation-20261008/README.md` (evidence not published), [current status] `../README.md` (evidence not published), [latest original painting handoff] `../experiments/timer-futex-20261009/HANDOFF.md` (evidence not published).

## Effects: what the evidence actually says

The operating manual documents insert effects and parameter modulation, and its signal-flow diagram places digital processing alongside a separate analog-filter path. Firmware change history documents added effects (including phaser, ducker, lo-fi, distortion and compressor) and the second FX module in 1.60. These are documentary evidence about product behavior and release capabilities, not recovered processing code. The held manual is an earlier FX1-oriented description; use the change history for later release additions.

The service manual assigns audio processing to MAIN IC2000, MCIMX6Q5EYM10AD. Together with the ARM application and audio-worker observations, this makes the main CPU/application audio path a reasonable starting hypothesis for digital-effect research. It does not establish the location or implementation of any particular effect, or rule out other processing components. A generic block labeled DSP in the operating manual does not by itself prove a separate DSP chip or dedicated DSP firmware.

The operating manual explicitly describes a discrete Dave Smith/Prophet-6 analog filter circuit. That filter's physical sound processing is distinct from a software digital-filter algorithm. Firmware can provide settings and routing, but our research has not traced its precise control protocol.

Sources: [operating manual extraction, printed pages 3, 38–39 and 46] `../decode/tmp/consolidation/TORAIZ_SP-16_manual_EN.txt` (evidence not published), [firmware change history] `../decode/tmp/consolidation/TORAIZ_SP-16-Firmware-Change-History-Ver160-en.txt` (evidence not published), [service-manual component roles, printed page 46] `../decode/tmp/consolidation/service-page-49.txt` (evidence not published).

We have not identified and validated a particular effect's audio processing routine, parameter-to-state mapping, sample representation, coefficient generation, delay buffers, reverb topology, processing order or SIMD use. We have not measured original effected audio against known input. Juce thread names establish named runtime components; they do not establish that effects use JUCE DSP implementations. GUI effect names, icons and CSV layouts likewise do not identify the sound-generating algorithm. No supported third-party effect/plugin extension interface has been established; the manual's DAW-plugin analogy is not API evidence. The GPL/BSP collection does not provide the identified proprietary sampler/effects source.

## Next research that would answer the effects question

Keep completed startup and usable original UI as the active runtime milestone. A subsequent focused effects investigation can select one simple digital effect, identify its selection/parameter data and binary references, follow those into the original audio-buffer processing path, and match a parameter change to processing-state changes. Validate the candidate with known audio input and output (for example, a delay with an impulse and measured repeats), after confirming a meaningful capture path rather than null I/O. Static analysis can begin before usable UI; usable UI would make parameter-driven runtime confirmation easier. This proposal is not a runtime or hardware authorization and carries no claimed effort estimate.

No selected-effect test has yet passed, no effects modification has been demonstrated, and build/repack/updater acceptance/recovery remain separate unresolved gates. See [architecture and deployment gates] `../experiments/offline-review-20261008-01/ARCHITECTURE_DEPLOYMENT_GATES.md` (evidence not published).
