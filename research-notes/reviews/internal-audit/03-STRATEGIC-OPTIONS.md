<!-- source: ../PioneerSP16Review/03-STRATEGIC-OPTIONS.md | scrubbed -->

# Stage 3 — Strategic options

Review date: October 9, 2026, America/Chicago. This is a comparison for future architectural decisions, not an implementation roadmap or experiment authorization. Sources and capability boundaries follow the [architecture assessment] `Review/03-ARCHITECTURE-ASSESSMENT.md` (evidence not published) and [Stage 2 audit] `Review/02-INDEPENDENT-AUDIT.md` (evidence not published).

## How to compare the options

No target feature or compatibility acceptance boundary has been selected (F01/R01). Consequently, the rankings below are conditional judgments, not validated effort estimates, probabilities or completion percentages. Feasibility distinguishes a credible mechanism from demonstrated deployment. Complexity means the amount of new behavior/interfaces that must be implemented and validated. Expected value means useful new instrument behavior relative to effort and uncertainty. Reversibility distinguishes removing a software change from recovering a failed persistent update.

“Modified firmware” can range from changing resources to changing the kernel. “Replacement OS” can mean new userspace on an existing BSP, modern Linux with ported board support, or a completely different execution platform. These scopes should never share a single feasibility estimate.

## Comparison: feasibility, evidence, effort and risk

| Option | Relative feasibility | Supporting evidence | Implementation complexity | Principal technical risk |
|---|---|---|---|---|
| A — Change supported configuration/resources, retaining original application and platform | Best candidate for a behavior actually expressed in data; ineffective for an absent algorithm/control path | Extracted resources/scripts and original resource-driven UI behavior; no selected data-only feature demonstrated | Low for a proven declarative behavior; rises if schemas/invariants are hidden | A cosmetic/data edit is mistaken for functionality; app rejects data or persistence corrupts state. |
| B — Add a companion process or selectively interpose an existing userspace boundary | Plausible for an independent utility or a verified controllable interface; unproved for internal sampler/effects features | Linux process model, dynamic linkage/imports; **no demonstrated IPC/plugin/extension interface** | Low–medium for isolated services; high for undocumented internal control | Device exclusivity, initialization order, races, unsupported symbol/ABI behavior or no usable control boundary. |
| C — Patch or extend a bounded original application path, retaining platform | Strongest candidate for localized internal behavior; still unproved on device | Original ELF, byte-backed maps and attributable loaded UI behavior; source unavailable | Medium for local policy changes; high for new algorithms, data structures or broad UI/persistence changes | Hidden invariants, ARM ABI/relocations, thread/state ownership and regression effects. |
| D — Replace the application/UI/audio engine on the shipped Linux/BSP, retaining boot and panel firmware | Credible middle option if interfaces are recoverable; not demonstrated | Shipped ALSA/X11/runtime stack, BSP and panel-interface clues | High: implement selected instrument functions and hardware initialization/ownership contracts | Proprietary driver/library dependencies, calibration, audio routing and project compatibility. |
| E — Replace Linux/rootfs with a maintained Linux platform and new or retained application | Plausible platform project; presently less evidenced than retaining vendor BSP | Documentary i.MX6Q platform and held historical driver/source trees | Very high if board drivers need porting; retained app adds ABI/library compatibility work | Boot restrictions, missing vendor interfaces, driver behavior changes and expanded regression surface. |
| F — Replace with an RTOS/bare-metal or otherwise substantially new OS and instrument stack | Least supported; requires requirements that justify abandoning Linux | Hardware roles only; no demonstrated alternate board/audio/panel stack | Highest: memory/storage/USB/display/audio/MIDI/panel and instrument scheduling/services | Recreating working board support and recovery while losing vendor software reuse; no measured need or timing advantage. |

The existing userspace emulator is a research option supporting A–D, not an additional on-device deployment architecture. Full-system emulation would likewise be a research investment, not delivery of a feature to an SP-16.

## Comparison: value, reversibility and dependencies

| Option | Expected value | Reversibility | Major dependencies | Unresolved assumptions |
|---|---|---|---|---|
| A | High return for the narrow class of data-defined behavior; low if it only changes appearance | High in an offline copy or reversible overlay; persistent installation still requires recovery | Resource schema, valid feature behavior, delivery and metadata fidelity | The desired capability already exists in code and is exposed by data. |
| B | High for isolated utilities; potentially low for deep DSP/control features | High if launched/stopped without persistent changes; process side effects and deployment still matter | Executable access, compatible ABI, proven IPC/interposition boundary, ownership and resource budget | The app exports usable control or can coexist with the service; dynamic linking alone does not prove this. |
| C | High for selected local changes; can degrade quickly as patch scope expands | Patch bytes can be restored offline; board rollback depends on what the update overwrites | Exact binary version, known insertion/change point, state/thread contract, packaging or alternate load route | A stable small boundary exists, new code can be loaded safely, and intended regressions can be tested. |
| D | High long-term control if substantial new behavior is needed; large initial validation burden | Good with a supported volatile/alternate launch; poor if persistent shared state is overwritten | Usable existing drivers/libs, complete affected peripheral contracts, new instrument engine, recovery | Vendor support is independently reusable; required original features/file formats can be preserved or consciously reduced. |
| E | High only if platform lifecycle, driver/resource requirements or broad system control justify it | Conditional on an independently recoverable alternate boot; replacing shared storage increases risk | Board port, boot acceptance, source lineage, calibration/storage, peripheral drivers; app ABI if retained | A current kernel supports this board sufficiently; old vendor interfaces are portable and originals remain usable. |
| F | Potential value for a deliberately narrow instrument with measured scheduling constraints; low current information-adjusted value | Lowest if it replaces boot/storage/panel as well; potentially better with a verified independent boot path | All E hardware dependencies plus replacement OS services and instrument stack | Linux is the limiting factor; alternate OS improves the required behavior enough to justify recreating support. |

The categories describe code scope, not guaranteed deployment risk. A one-byte application change installed through an updater that also rewrites boot/panel state may be less reversible than a large replacement application launched from a supported temporary environment.

## What each option would need to earn a preference

**A: establish actual functional leverage in data.** Resource strings and UI layouts are not evidence that a new audio/control capability can be enabled. Prefer A only when a selected before/after behavior can be traced to declarative data and tested against state/output/persistence. If code lacks the feature, exit this option rather than accumulating cosmetic changes.

**B: prove the boundary before designing the service.** A separate process avoids rewriting a sampler only if the feature is independent or a real control/data boundary exists. Library interposition might reach imported calls, but internally linked/inlined behavior and thread ownership may prevent useful control. A safe coexistence test and one real interface transaction are more decisive than a broad hook framework. Never assume access to the panel or audio device can be shared.

**C: demonstrate one bounded change with meaningful output.** Existing static UI maps make C a reasonable candidate; they do not demonstrate new-code loading or a successful modification. A tightly scoped reference-versus-change test should prove the original state's application mechanism, the change's effect and relevant regressions. Binary patching becomes a poor architecture when each feature requires reconstructing large opaque ownership/persistence systems. At that point compare D rather than treating every new patch as inevitable.

**D: establish the platform as an independently usable hardware substrate.** This option avoids recreating low-level drivers while removing dependence on proprietary application internals. It still requires the initialization that the app currently performs, complete affected panel/codec/analog contracts and a new sampler/sequencer/UI for the required feature set. A simple audio/panel probe on retained Linux proves a substrate, not an instrument. D may win if requirements are broad and compatibility can be reduced deliberately; neither condition is established.

**E: identify a platform-level reason.** A new kernel might be justified by a required driver, platform maintenance requirement or a measured limitation that cannot reasonably be addressed in retained Linux. No such reason is presently demonstrated. A modern generic i.MX6 board boot is not a port of this product. Reusing the proprietary application also preserves its old ABI and behavioral constraints while adding platform risk. Modernization should be evaluated against an explicit requirement, not assumed to deliver new sampler functionality.

**F: demonstrate why a substantially different OS matters.** There is no evidence that Linux is the bottleneck or that RTOS/bare-metal will improve the selected behavior. Real-time suitability requires measured deadlines and complete I/O contracts, not an OS label. F may be rational for a reduced-function instrument or a measured requirement that alternatives cannot meet. It does not currently earn implementation commitment.

## Deployment mechanisms are a separate decision

| Candidate mechanism | Available evidence | Strategic implication |
|---|---|---|
| Original update path with rebuilt package | Known decryption/containers/CRCs; acceptance/routing/round trip not proved | Potential distributable route for A–F, but not ready. Required integrity checks and write scope must be mapped. |
| Existing Linux launches replacement/companion software from a permitted location | Static launch chain and persistent-storage clues | Could reduce boot changes. Writable/executable access and startup/control policy remain unknown. |
| U-Boot boots a temporary or alternative image | Static NAND/MMC/network commands | Could reduce flash exposure if actually usable without persistent environment writes. Console/access/authentication are unknown. |
| Physical debug/service recovery | Manual/platform leads; no unit demonstration | Candidate fallback, not a deployable procedure or guaranteed escape from authentication. |

No mechanism can be selected on present evidence. Authentication restrictions at one layer may leave other legitimate routes usable; absent restrictions in one supplied source tree do not prove absence on a fused unit or in the release binary. A modified-container parser pass cannot substitute for boot/application acceptance. R03/R07/R08 remain scope-specific requirements.

## Preferred comparison outcome

For a localized feature, investigate **A or B if a real suitable boundary exists; otherwise C**, retaining the original platform. This is a preference for minimizing unproven interfaces, not a claim that the options are deployable or that the cheapest-looking change will be maintainable.

Keep **D** as the leading replacement alternative. Prefer it over an expanding series of opaque patches if required behavior is broad, independently usable hardware interfaces are proven, and the necessary replacement/compatibility scope is acceptable. Keep **E** conditional on demonstrated platform requirements. **F** receives no current implementation recommendation.

Feature scope, executable access, recovery, actual hardware contracts and resource headroom can reverse this ranking. The [recommended direction] `Review/03-RECOMMENDED-DIRECTION.md` (evidence not published) gives the smallest experiments intended to resolve those decisions. They are decision proposals, not a build/deployment sequence.
