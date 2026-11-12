<!-- research-note: experiments/host-normalization-integration-20261011/HANDOFF.md | thread D | scrubbed, links rewritten; see EDIT-LOG.md / LINK-REWRITE-LOG.csv -->

# Disposable host normalization integration — October 11, 2026

**HOST_INTEGRATION_OK within the disposable host subset.** Select → whole-recording Normalize → real candidate submission, displayed gain and original comparison → settled preview → exact same-selected-path Keep or original-preserving Discard is connected. Human listening remains **NOT_CONFIRMED**; this does not satisfy physical/adopted-product preview acceptance.

[Outcome/envelopes] `OUTCOME.json` (evidence not published), [45 initial focused controls] `acceptance-1791702917099553000.results.json` (evidence not published), [8 supplemental controls] `supplemental-1791703067272053000.results.json` (evidence not published), and [actual terminal command stream] `interactive-events-1791703127335441000.json` (evidence not published) retain separate results. Supplemental cases correct preview-gated mutation coverage and independently reject forged PCM/wrong samples. No broad suite rerun.

Exactly two owned transaction children were SIGKILLed at their real pipe handshakes: [before rename] `logs/crash-before_rename-1791702926254738000.receipt.json` (evidence not published) and [after rename, before directory sync/result] `logs/crash-after_rename-1791702929268816000.receipt.json` (evidence not published). Fresh recovery and one repeated recovery per case preserve transaction material identity/bytes. Before rename remains original/unchanged; after rename verifies the normalized target and later sync/refresh retry. The historical postrename sync acknowledgment stays missing. Process kill is not power loss.

The final [joined result] `final-loaded-identities-1791703277902106000.result.json` (evidence not published) uses immutable Candidate.data, a frozen generation/Job/source/selection/transaction record, and a private wrapper validating the candidate **under the component's pinned flock**. Unchanged transaction.main retains exception reconciliation/descriptor cleanup. Fresh verification runs in a new process importing no production components, computes all expected samples from predeclared ORIGINAL samples, checks geometry/metadata/pads/attributes and the independently decoded full candidate plus accepted audition prefix, and requires new controller waveform publication acknowledgment. Old source FD bytes remain old; successful Keep invalidates the old inode binding.

Final dimensions: `commit=true; sync=ok; component refresh=ok; fresh PCM=ok; controller publication=ok; human listening=NOT_CONFIRMED`. Sync-fault controls report `COMMITTED_DURABILITY_UNCERTAIN`; wrong-generation publication reports `COMMITTED_PCM_REFRESH_FAILED` while retaining the component's `HOST_COMMIT_AND_REFRESH_OK`. No rollback/Discard undo is claimed.

Implemented intersection: complete basic PCM16 mono/stereo 44.1/48/96 kHz WAV ≤1,048,576 bytes; exact opaque JUNK, LIST/INFO, cue/smpl metadata/pads; ordinary supported attributes and allowlisted binary xattrs; no ACL entries/flags/special bits; new owned mode0700 APFS namespace and participating writers. Six source formats passed numerical/capture joins. Actual stereo native submission used 44.1 kHz on Bitwig Connect's existing 12-channel/24-bit physical route. 48/96 kHz native preview was refused. No global audio settings changed. System mixer/physical conversions and DAC/listening are unqualified.

The final helper independently hashes accepted PCM off the callback. Its 11,025-frame audition hash matches the candidate prefix. Whole-recording gain is `7301/1075` (+16.6395 dB), from a late peak outside that prefix; full normalized peak 29204. EOF and real explicit-stop controls both record AudioQueue stop/disposal separately from process reaping. The deliberate missing-stop mock retains an unresolved memory lease and blocks Keep; it creates no native queue and receives no invented acknowledgment.

Runnable commands (normal host CoreAudio access is required; sandbox query returned device0 and is retained):

```sh
SP16_HOST_EXP=experiments/host-normalization-integration-20261011
python3 -B "$SP16_HOST_EXP/supervise.py" interactive --bound-seconds 180
python3 -B "$SP16_HOST_EXP/supervise.py" check --bound-seconds 300
python3 -B "$SP16_HOST_EXP/supervise.py" recover final-loaded-identities-1791703276566440000 --bound-seconds 60
```

Interactive: `list`; `select manual-b-1791703074653676000`; `normalize`; wait for READY; `status`; `original`; wait for settlement; `preview`; `stop`; `keep` **or** `discard`; `close`. EOF/timeouts terminate finitely. Each Keep consumes that instance's namespace; reuse is refused, and another precreated fresh labeled instance has its own selected.wav. A future `check` command creates new fixtures and two crash joins; it is not an automatic continuation. No persistent-path multi-transaction support is claimed.

[Source pins] `source-pins.json` (evidence not published), [exact final identities] `final-source-identities.json` (evidence not published), [retained attempt source versions] `versions/` (evidence not published), [compiler/SDK/interpreter/helper identities] `toolchain.json` (evidence not published), and raw per-child argv/env/cwd/stdout/stderr/cleanup in [logs] `logs/` (evidence not published) bind this result. Initial CLI parsing failure, sandbox route failure, and final-census parser failure remain retained. Initial preparation source snapshots were not all captured; acceptance and subsequent changed-adapter source versions are preserved.

[Final cleanup] `final-cleanup.json` (evidence not published): 139 recorded owned PIDs and 11 owned groups independently absent; no inspection/PermissionError, owned endpoint or unsettled native queue. The completed dependencies' seven required source hashes and corrected ACL oracle pin remain unchanged. No shared README/index/AGENTS, Git state, source package, original sample, guest or firmware was changed. [Exact owned-file list] `OWNED_FILES.txt` (evidence not published) covers this directory only.

Remaining: attributable human listening confirmation; mono native playback beyond source/capture checks; any changed native route; full PCM24/50 MB profile and broader metadata/adjuncts; original 1.60 stable scene/model source reconciliation, owned SimplePlayer candidate lifetime/native callback settlement, target Keep/all-holder/player/waveform freshness; target storage/media power loss and physical/delivery qualification. Smallest next host step, only if selected, is finite listening confirmation on this existing route. Instrument integration stays deferred under the owner's zero-member observation decision. No successor work started.
