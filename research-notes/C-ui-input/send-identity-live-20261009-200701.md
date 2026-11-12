<!-- research-note: experiments/send-identity-live-20261009-200701/HANDOFF.md | thread C | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Known-entry-only Send diagnostic — October 9, 2026

**Inspection passed: two original same-owner listener snapshots, a full 600.380s observation and clean owned closure.** Exactly one fresh guest and one gated HOME→MIXER tap were used; no Send input, encoder, retry or replacement guest. This allowance is consumed and closed. Async-model findings remain incomplete/unverified/excluded, positive mutation readiness remains **unready**, and startup-gates stays paused.

Question: does the corrected Send identity contract match actual loaded operands, and what listeners belong to the selected widget and owned component chain?

The private navigation copy received only the four sources/two receipts from the [fresh offline package] `../send-identity-inspection-20261009/HANDOFF.md` (evidence not published), plus relocation repairs, fresh authorization and owned state. [Integration identities/original hook checks] `inspection-integration.json` (evidence not published) matched; unchanged runtime, timing, guards, input gate and supervision were reused. Loaded original app/libc/libpthread identities matched. The first [preflight] `preflight-occupied/endpoint-preflight-initial.json` (evidence not published) found another diagnostic's occupied endpoints and launched nothing. This attempt waited without touching that owner, retained its original 1,200s session clock and reran [preflight] `preflight-after-wait.stdout.json` (evidence not published) after release. Launch-to-postflight used 759.211s including that wait; guest supervision retained independent 605/608/610s bounds.

Fresh startup readiness at 268.935s and two owned HOME captures opened the known-entry gate. Exactly two tagged press/release packets for `(600,60)` were consumed and their original handlers returned; the MIXER handler returned at **335.931718s**. The owned binding and seven original getter/descriptor hook sites validated. Live identity operands were retained before the checks:

| Operand | Actual loaded word |
| --- | --- |
| Widget vtable | `0x8eb95c` |
| W+0x84 identifier and `0xf6c700` construction cell | both `0x18fb3388` |
| W+4 component name and `0xf6ab44` press-name cell | both `0x017b12e8` |

These are raw loaded words, not dereferenced guest strings. Construction identity and component name are distinct; the corrected contract accepted them. This supports the correction in this guest; it does not reconstruct the missing RAM operands from the earlier failed guest.

[Two live snapshots] `listener-snapshots.json` (evidence not published) at **340.775751s** and **347.757197s**, 6.982s apart, retain the same MixerController/view/controller/footer/widget/CDM/thread/unit/parameter owners, original getter/descriptor returns, normal selected-channel-0 context and enabled/unsuspended widget. Send is **0**, actual bounds **0–127**, UI range **0–128**. Custom listeners are empty. Eight owned components contain exactly one recursive footer listener; its motion target is original `0x753778`, and widget motion is original `0x7535ec`, both loaded `bx lr`. Loaded target bytes match the original file. This supports the narrow no-extra-listener prediction within the inspected chain. Desktop/global storage remains unresolved; no universal absence of touch editing is claimed. All inspection hooks retired after the second sample.

Six original-owned **800×480 MIXER** captures are pixel-identical from **375.301100s** through **595.080884s**. Fresh raw trees/window attributes and original returned XID `0x200009` bind them to this guest. [Visual receipt] `mixer-visual.json` (evidence not published), [preview] `mixer-full-preview.png` (evidence not published) and original XWDs show sixteen channel faders with Send Amount 0. No setter/task activity or Send gesture occurred; no changed value, Send application, audio or mutation-rendering claim follows.

[Sixteen live evidence checks] `result.json` (evidence not published) passed. The [native final] `run-1/send-identity-live-20261009-200701-run-1-result.json` (evidence not published) records a bounded stop at 600.380s. [Owned closure] `run-1/supervision/attempt-owned/client-closure.json` (evidence not published) records direct-child/watchdog reaping and absent private control endpoints; [independent postflight] `run-1/endpoint-postflight-initial.json` (evidence not published) passed with runtime endpoints absent. Historical cleanup failures and second-resolution/unrecorded-child limits remain preserved.

Raw evidence: [guest stdout] `run-1/supervision/guest.stdout.txt` (evidence not published)/[stderr] `run-1/supervision/guest.stderr.txt` (evidence not published), [identity receipts] `identity-operands.json` (evidence not published), [input consumption] `run-1/drawable-input-consumed.json` (evidence not published), [display observations] `run-1/display-observations.json` (evidence not published), [effective command/result] `command-result.json` (evidence not published), [supervision/identities] `run-1/attempt-supervision.json` (evidence not published), [analysis command] `analysis-command.json` (evidence not published)/[stdout] `analysis.stdout.txt` (evidence not published). Source fixtures, offline/private results and prior consumed evidence were preserved.

Next action: use these saved runtime recipients and bounds for focused offline input-route work before selecting any positive mutation test. Transport, legal editing, async application and owned edit rendering remain unresolved. Do not resume/reconstruct the excluded async assignment. Any later guest/input requires a new explicit allowance; none remains here.
