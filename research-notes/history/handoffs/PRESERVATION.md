<!-- source: docs/handoffs/2026-10-11-host-normalization-director-review/PRESERVATION.md | scrubbed -->

# Saved review instructions — preservation only — October 11, 2026

`PROMPT.txt` is the saved prompt for a future host-normalization Director review. It is preserved as instructions, not as a completed engineering review or an accepted result. No review, tests, implementation, firmware or hardware action was performed by this closeout. Existing supporting records within this directory are included unchanged; external references remain dependencies.

Selection and exact actual Git blob/mode readback are recorded in the original-rootfs study's `preservation/` receipts. Only these two selected scopes are committed. Git retains bytes, executable bits and link text, not full filesystem metadata, empty directories or live state. Local Git is not off-device backup. Commit IDs and counts follow in the receipt commit and final response.

Content commit **3d733144d5d678f302c162b20529b415b0a7f3cc** contains this scope with 2 regular files, zero symlinks, 15,131 bytes; both exact blob content and executable modes passed readback. The pre-existing saved record is `PROMPT.txt` (14,287 bytes); this preservation note is the only added supporting record. No review was performed. [Complete readback] `../../../experiments/original-rootfs-control-150-20261011/preservation/CONTENT_READBACK.json` (evidence not published) and [selection/dependencies] `../../../experiments/original-rootfs-control-150-20261011/preservation/MANIFEST.json` (evidence not published) retain the actual selection and limits. The receipt commit follows the content commit in local Git history; its ID and final-tree counts are recorded in the closeout response.
