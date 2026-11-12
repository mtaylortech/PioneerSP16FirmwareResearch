<!-- source: engineering-reviews/2026-10-08-expose-dispatch-decision.md | scrubbed -->

# Expose dispatch and the next rendering decision — October 8, 2026

1. **Result and new knowledge.** The cycle answered whether natural Expose reaches original dispatch. Raw payload identity, original instruction bytes and thread/SP matching establish delivery for `0x200009` at 250.386s and callback `0x817cf0` return at 250.388s. This advances knowledge beyond the previous ten untyped event returns. Constructor/storage/ioctl progress repeated; 1,314 resource returns did not extend the frontier. Both exact drawable buffers are entirely zero. Full startup, drawing and input response remain unproved; no input was sent. No controlled speed or observer-overhead comparison was performed. [Raw trace] `../experiments/natural-dispatch-retry-20261008/run-1/supervision/guest.stdout.txt` (evidence not published), [pixel/receipt evidence] `../experiments/natural-dispatch-retry-20261008/result-verification.json` (evidence not published).

2. **Failures and contradictions.** Native deadline/final records are still absent; owned SIGTERM at 604.998s produced exit -15. Cleanup passed, but neither the pre-expiry timer sample nor passing synthetic controls identifies the cause. Earlier fixture omissions and null-read failure remain preserved; the complete fixture now recovers startup. Two callback returns are unrecorded because a 16-visit cap counts a shared loop address, not completed calls; this does not invalidate the retained Expose return. README’s latest frontier agrees with the evidence; stale claims in its preceding-failure paragraph needed qualification. [Handoff] `../experiments/natural-dispatch-retry-20261008/HANDOFF.md` (evidence not published), [shutdown] `../experiments/natural-dispatch-retry-20261008/run-1/attempt-supervision.json` (evidence not published).

3. **Decision.** Retain the complete fixture, corrected ARM32 statfs, invalid-descriptor ioctl guard and cooperative-main as a diagnostic condition. General scheduling reliability remains unresolved. Fixture reconstruction, constructor re-proving and broad natural-event enumeration leave the critical path. Prioritize the internal Expose-to-render chain; longer observation alone has no demonstrated benefit.

4. **One next experiment.** Locate the first missing boundary between window-context lookup and redraw. Add read-only, byte-validated XFindContext result/output-pointer receipts, per-window Expose entry and virtual-redraw target/call/return; retain both painting sites and exact drawable captures. Match thread/SP/event identity and correct the shared-return cap. [Static chain] `../experiments/natural-dispatch-retry-20261008/per-window-instructions.json` (evidence not published), [redraw call] `../experiments/natural-dispatch-retry-20261008/expose-helper-instructions.json` (evidence not published).

5. **Efficiency.** Retire general payload/filter hooks after the selected Expose is matched; cap receipts by completed frames. The shared return point accumulated 744 visits for eight retained returns. That is measured redundant observation, not measured CPU overhead. Control only changed matching/cap contracts; investigate the actual stop failure with a focused non-firmware stop-path control before claiming clean guest completion. Reuse unchanged validation.

Next-test plan:

| Evidence | Decision enabled |
| --- | --- |
| Context lookup fails or dispatch stops before virtual redraw | Investigate the observed context-registration or dispatch gate. |
| Virtual redraw runs | Follow its actual target to the first rendering/transfer gate; if pixels appear, use remaining observation to verify persistence. |

Keep **one 600-second observation within the established 20-minute ceiling**, with independent TERM/KILL/reap at observation +5/+8/+10 seconds, retained guards, unused endpoints/private credentials and ownership-aware postflight. Stop for an actual fault or identity mismatch. Current guest authorization is consumed; no work is underway, and this review launches nothing. A subsequent execution request can continue here.
