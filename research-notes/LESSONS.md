# Lessons

Cross-cutting lessons from the SP-16 research, each pointing at the notes it
comes from. These are the transferable part: methods that worked, dead ends,
and mistakes worth not repeating. They describe emulation and static-analysis
research on a device the researcher owned; nothing here is a recipe for
modifying a unit, and no firmware or key is included.

## Methods that paid off

**Finite instruction-count slices beat open-ended runs.** The single most
useful scheduling trick was to run the identified main thread in small finite
quanta (≈20 ms / tens of thousands of instructions) through the font scan,
then restore larger quanta afterward. It reliably advanced startup where
free-running stalled. See
[startup-throughput](B-app-startup/startup-throughput-20261008.md),
[full-font-cache-next](B-app-startup/full-font-cache-20261008-1614-next-20261008-1712.md),
[full-font-cache-pixel](B-app-startup/full-font-cache-20261008-1614-pixel-20261008-1658.md).

**Cooperative scheduling instead of asynchronous timed stops.** Letting the
original code reach cooperative yield points, rather than interrupting it on a
timer, preserved construction progress. See
[cooperative-font](B-app-startup/cooperative-font-20261008.md); the limit of
the technique shows in
[cooperative-select](B-app-startup/cooperative-select-20261008.md), where
select completed but no paint followed.

**Honor the firmware's own futex/timer waits.** Treating `FUTEX_WAIT` on named
JUCE timers / ProjectManager as contracts to satisfy — not obstacles to skip —
resumed timer processing and the first original non-black painting. See
[timer-futex](B-app-startup/timer-futex-20261009.md),
[project-manager-futex](B-app-startup/project-manager-futex-20261009.md).

**Static-byte verification alongside every emulator claim.** Function bodies
were confirmed by matching reference instruction bytes, not just by behavior,
which caught tool disagreements. See
[rea-ghidra-comparison](A-firmware-tooling/rea-ghidra-comparison-20261010-202454.md),
[layout-access](B-app-startup/layout-access-20261008-1715.md),
[provider-binding](D-normalize/provider-binding-20261010-072803.md).

**Stop at the first decisive gap.** The Normalize thread's discipline was to
run a time-boxed static tranche and stop honestly at the first missing edge
rather than guess across it. It keeps the unknowns visible. See the
`step09a–09h` notes under [D — Normalize](README.md#d--normalize-33-notes),
e.g.
[scheduler-contract-step09c](D-normalize/normalization-scheduler-contract-20261010-step09c.md).

## Dead ends and things that cost time

**False "exit 0" verifiers.** Several harnesses reported success while the real
work hadn't happened; building verifiers that can actually fail (with
deliberate false cases) was necessary. See
[sp16-skill-context-fix](A-firmware-tooling/sp16-skill-context-fix-20261011.md),
[keep-recovery-qualification](D-normalize/keep-recovery-qualification-20261011.md),
[keep-recovery-acl-verifier-fix](D-normalize/keep-recovery-acl-verifier-fix-20261011.md).

**Observer mis-attribution and premature retirement.** Passive observers that
hooked the wrong lifetime reported absence that wasn't real, or tore down too
early. See
[panel-passive-live](C-ui-input/panel-passive-live-20261009-225409.md) (failed
on an observer integration bug) vs its corrected re-run
[panel-passive-corrected-live](C-ui-input/panel-passive-corrected-live-20261009-230743.md),
and
[observer-callback-readiness-review](D-normalize/observer-callback-readiness-review-20261011.md).

**Missing native finals.** Guests that ended on expiry rather than a mapped
native return left the boundary unproven; distinguishing a real stop from a
timeout mattered. See
[natural-dispatch](B-app-startup/natural-dispatch-20261008.md) (failed before
the phase) vs
[natural-dispatch-retry](B-app-startup/natural-dispatch-retry-20261008.md).

**Order effects in A/B quantum tests.** Running treatment before control, or
vice versa, changed the outcome and made results inconclusive. See
[post-font-counted-quantum](B-app-startup/post-font-counted-quantum-20261008.md),
[quantum-replication](B-app-startup/quantum-replication-20261008.md).

**Host model ≠ device proof.** The Keep/Normalize transaction worked as a host
Python model but was never shown on firmware; keeping that distinction explicit
avoided over-claiming. See
[host-normalization-integration](D-normalize/host-normalization-integration-20261011.md),
[normalization-host-core](D-normalize/normalization-host-core-20261011.md),
[normalization-member-observation](D-normalize/normalization-member-observation-20261011.md).

## Things that are version-bound (read before reusing an address)

Addresses and offsets differ between 1.50 and 1.60; a boundary verified in one
line does not transfer to the other without re-checking. The board/USB work is
1.50 ([E1](README.md#e1--board-emulator-sources-3-notes)); most app-startup and
Normalize addresses are 1.60/1.50-specific and are stated per note. The
firmware catalog is the anchor for which release a finding belongs to. See
[firmware-catalog](A-firmware-tooling/firmware-catalog-20261010.md) and
[`../docs/firmware-reference.md`](../docs/firmware-reference.md).

## The honest bottom line

Across ~90 experiments, startup was pushed a long way and many boundaries were
nailed down, but **a faithful, usable, drawable UI and authentic hardware
behaviour were never achieved** — in either the app emulator or the board
emulator. The value here is the mapped boundaries, the methods above, and the
clearly-marked gaps, not a finished emulator. See
[`../docs/findings.md`](../docs/findings.md) and
[`../docs/open-questions.md`](../docs/open-questions.md).
