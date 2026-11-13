# Method: a worker/critic loop for unattended reverse engineering


The effects research (see [`../../docs/effects/`](../../docs/effects/README.md)) was
done by an automated loop of AI coding agents running on the research machine, with
the owner reviewing between batches. This note records the method, because it is
reusable and because it explains how far the results can be trusted. The loop's own
configuration files are not published. They are specific to one machine and tool
setup, and they would not run elsewhere unchanged.

## Roles

- **Orchestrator** (one session per cycle). It picks the highest-value open hypothesis
  from a ledger, writes **success criteria before any testing**, delegates, reconciles
  the results, and is the only writer of the knowledge base: findings, hypotheses and
  the function table.
- **Worker.** Tests exactly one hypothesis. It writes or extends a harness script
  named after the hypothesis, runs it, and records what it ran, what it saw, and each
  criterion's status. It must test at least one alternative explanation, and must
  label every claim *confirmed*, *likely* or *guess*.
- **Critic.** Assumes the worker is wrong. It re-runs the worker's harness into its
  own scratch folder, re-checks key addresses in the disassembler, and looks for
  emulation artefacts (unmapped memory, stubbed hardware, wrong calling convention),
  confirmation bias, addresses from the wrong firmware version, and untested
  alternatives. It returns CONFIRMED / REFUTED / INCONCLUSIVE per criterion, and may
  append only its verdict section. It cannot edit code or other files.

If the verdicts disagree, there is **one** rebuttal round (the worker answers, the
critic re-checks), never more. Only claims the critic CONFIRMED are promoted to the
findings ledger. Everything else stays *likely* or *guess*.

## Guardrails that mattered

- **Pinned inputs.** The firmware files are checked against their SHA-256 before and
  after every cycle. The harnesses refuse any other file.
- **Allowed changes.** A post-cycle check accepts only changes to the knowledge base
  and harness paths. A pre-commit hook rejects binaries and firmware-derived paths.
- **Critic integrity.** A snapshot before the critic runs, verified afterwards, proves
  it changed nothing except appending its own section.
- **Stop conditions.** The loop stops by itself on: a safety-rule boundary (anything
  toward a modified or loadable image, update code or a device); a decision that
  belongs to the owner (written to an owner-questions file, which blocks the next
  cycle until answered); the same hypothesis inconclusive twice in a row; an unusable
  tool; or a failed integrity check.
- **No network, sandboxed writes, per-cycle budget and turn limits**, and local commits
  only. Nothing was pushed.
- **Publication rule.** The knowledge base gets short excerpts only: no long
  disassembly, decompiled listings or firmware bytes.

## What it produced, and what it caught

Nine cycles, one hypothesis each. They established the audio path, effect selection
and the `EffectBase` interface, then reconstructed four effects and the shared
oscillator bit-exactly. Things the structure caught that a single pass would likely
have missed:

- **A setup artefact presented as a finding.** An early cycle reported that two LoFi
  filter types sounded identical, and that 0.5 on two parameters changed nothing. The
  next cycle found the cause: the parameter objects ignore a value equal to their
  constructor's "last" value. Both observations were withdrawn (F025, F026).
- **Wrong library behaviour.** Bit-exact matching exposed that the device's
  single-precision `powf`, `log10f`, `tanf`, `sinf` and `cosf` are fdlibm and not
  correctly rounded. Models using host math were close but not exact (F044, F048,
  F052).
- **Planted errors.** For every model the critic introduced deliberate mistakes
  (wrong ranges, swapped orders, wrong stage counts) and showed that the comparison
  caught each one. A bit-exact match is only meaningful if the test can fail.

## Limits

- Everything is validated against the **emulated** original code, one function at a
  time. Nothing was measured on a physical unit.
- The critic is also an automated agent. Its independence is procedural (separate
  run, separate scratch space, adversarial instructions), not a second human.
- Cycle logs record tool sessions and scratch paths. Their conclusions and evidence
  hashes were carried into the findings ledger, which is what is published.
