<!-- source: docs/handoffs/2026-10-10-revision2-sequence/06A-AUDIOEDITOR-POSTSAVE.md | scrubbed -->

# P06 follow-up — AudioEditor post-save adjunct-data effects

**Status: STATIC OBJECT BINDING RESOLVED; LOCAL PERSISTENT EFFECTS MAPPED.** Target behavior, durable success, recovery and execution readiness remain unproved.  
**Actual root:** `docs/handoffs/2026-10-10-revision2-sequence`  
**Actual output:** `docs/handoffs/2026-10-10-revision2-sequence/06A-AUDIOEDITOR-POSTSAVE.md`  
October 10, 2026, America/Chicago.

**Finding:** in the mapped held 1.50 construction route, `AudioEditor+0x1a8` is a **SampleAdjunctDataManager**, implementing `ISampleAdjunctDataManager`. Its post-save slots `+0x10/+0x14` persist sample adjunct metadata at **the complete audio destination filename followed by `.dat`**. For an ordinary absolute destination `/…/recording.wav`, the sidecar is `/…/recording.wav.dat`, not `/…/recording.dat`. Both slots can delete and regenerate an existing sidecar. The editor's earlier rejection of an existing audio destination does **not** reject an existing sidecar. Thus the stock save envelope includes another potentially pre-existing file, its metadata and the filesystem effects of removal/creation/writing.

The service is not a project-save callback in this traced edge. Its local persistent operations are sidecar file operations; separate track-assignment/project effects in [06] `06-ACCEPTANCE-WRITES.md` (evidence not published) remain open. This distinction does not establish that a physical unit resolves the same bytes, paths or aliases, or that a future custom route has this complete effect set.

## Authority, identities and method

The owner reviewed Prompt 6 and explicitly renewed **another 16 minutes, read-only, review at report completion; no construction or execution**, to resolve this one service edge. This is a scoped follow-up, not execution of Prompt 7 or construction of an observation proposal/candidate. The reviewed [06] `06-ACCEPTANCE-WRITES.md` (evidence not published) remains unchanged. This new handoff is the sole saved artifact for the renewal.

AGENTS.md, README.md and 06 supplied current scope and prior evidence. Inspection used existing shell tools and the installed `experiments/emulation-20261007/tools/venv/bin/python -B`, pyelftools and Capstone in inline read-only analysis. Original ARM code and project/runtime scripts were not executed. Direct-branch and field-store scans supplied leads, which were checked in bounded original disassembly; literal pools and vtables were inspected as data, not asserted to be instructions. No source build was used as implementation evidence.

**Primary bytes:** [held 1.50 app] `../../../decode/output/image1/payloads/pdj/pdj/EP085_Main_R` (evidence not published), 11,993,612 bytes, SHA-256 **`075cff7a874e6eb319faa1c8cb74c7dd7d1534220550b589bbe652c37ba65ce2`**, checked at opening and after analysis. Original-container correspondence, ELF declaration and physical-release limits are retained in 06. All locators here are ARM virtual addresses in this identified ELF's first load segment, **file offset = VA − `0x8000`**. No 1.60 addresses were transferred. Dynamic relocation/symbol inspection independently binds PLT `open=0x108a0`, `write=0x1006c`, `fsync=0x11344`, `close=0x1072c`, `remove=0x10654`, `rmdir=0x114b8`, `lseek=0x10c78`, `towlower=0x10888`, `strlen=0x10c18`.

**S** below denotes inspected original bytes; **I** denotes interpretation supported by those bytes and original RTTI/keys; **U** denotes an unresolved boundary. There is no new runtime receipt.

## Concrete owner and dispatch binding

| Link | Original evidence | Result / limit |
|---|---|---|
| Allocate service → owner field | `0x1b173c–0x1b175c`: allocate `0x128` bytes, call constructor `0x37471c` at `0x1b1748`, store the object at owner `+0x5b0`. | **S** concrete allocated service on this construction route. Owner replacement/deletion logic follows; this is not a global claim about every possible construction route. |
| Owner → editor constructor | `0x1b2368–0x1b2390`: load owner `+0x5b0` into `r6`, allocate `0x1d8` bytes, supply `r1=44100`, `r2` from owner `+0x5c4` with `+0x80` adjustment if non-null, and **`r3=r6`**, then call `0x0b5cac`. Editor is stored at owner `+0x59c` after construction. | **S** service pointer is passed unchanged, with no service-interface subobject adjustment. |
| Constructor → `+0x1a8` | `0x0b5cd4` saves `r3` in `fp`; `0x0b5ee8` stores `fp` at editor `+0x1a8`. The separate constructor variant `0x0b59a4` stores a stack argument there at `0x0b5bc4`; its caller was not bound in this focused trace. | **S** closes the identified owner-to-editor pointer chain; **U** other variant's owner and actual loaded physical instance. |
| Service type / primary vtable | Constructor `0x374760–0x374780` installs primary vtable **`0x8b1be0`**. Its RTTI at `0x8b1fac`, name pointer `0x8b1f90`, reads `24SampleAdjunctDataManager`; base descriptor names `25ISampleAdjunctDataManager` at `0x8b1b10`. Thread-name literal `0x8b2064` is `SampAdjDMgr`. | **S** original type and interface correspondence, independently of guessed function names. |
| Post-save slot binding | Vtable entry `0x8b1bf0` (`+0x10`) is **`0x375050`**; `0x8b1bf4` (`+0x14`) is **`0x374b18`**. Editor calls them at `0x0b7588` / `0x0b7394`. | **S** two concrete post-save methods, rather than an opaque virtual service. |
| Arguments and choice | Editor flag `+0x1d0` selects slot `+0x14` when nonzero, `+0x10` when zero. Destination object is editor `+0x14c` in `r7`, passed at stack offset 0; `end−start` is passed at stack offset 4. A double from `+0x1c8` (slot `+0x14`) or `+0x1b0` (slot `+0x10`) is passed in `r2/r3`. | **S** call ABI and requested range count, not independent proof of samples actually written. **I** BPM versus bar setters, bound to serialized keys below. |

The editor constructor initializes `+0x1c8` to double 120 and `+0x1d0` to 1 (`0x0b5ed8–0x0b5ef8`). Editor setters `0x0b46f4` and `0x0b47b0` store bar/BPM-derived doubles and switch the flag at `0x0b4758` / `0x0b480c`; they do not directly write files in the inspected bodies. Actual values at a particular save remain U.

Representative byte anchors: `0x1b1748=f30b07eb`; `0x1b175c=b04587e5`; `0x1b2380=441c0ae3 0420a0e1 0630a0e1 0050a0e1 450efceb`; `0x0b5cd4=03b0a0e1`; `0x0b5ee8=a8b184e5`; `0x0b7390=14109ee5 31ff2fe1`; `0x0b7584=10109ee5 31ff2fe1`. Vtable data `0x8b1bd8–0x8b1bf4` is `00000000 ac1f8b00 80413700 54423700 a0403700 88553700 50503700 184b3700`.

## Post-save path and data effects

Let **D** be the audio destination supplied by the editor. The service first constructs a JUCE file/path object from D (`0x6573b4 → 0x656f54`); the latter contains absolute/relative/tilde handling. **D′** means that resulting file path. Actual working directory, mounts, symlinks, hard links and physical storage are U. The derived sidecar **A** is `D′ + ".dat"` through string concatenation (`0x62dc68 → 0x62cf1c`), then file/path assignment `0x65737c`. This is suffix append, not extension replacement.

| Stage | Slot `+0x14` / BPM locator | Slot `+0x10` / bar locator | Effects / classification |
|---|---|---|---|
| Lock and format check | `0x374b18–0x374c4c` | `0x375050–0x375184` | **S** acquire service lock `+0x118`; check filename ending `.wav/.aiff/.aif` through `0x630e74`, which compares backwards with `towlower`. Unsupported suffix returns 4 before sidecar work. This is a name check, not audio-content validation. |
| Sidecar derivation | `0x374c6c–0x374ca8` | `0x3751a4–0x3751e0` | **S** append service `+0x110`, initialized to literal `.dat` through constructor `0x3747ac–0x3747c0` / initialization `0x374944–0x37494c`; assign A to service `+0x10c`, then check existence. Service `+0x120` triggers an additional string-comparison helper; its return is ignored and it does not substitute another path in these methods. |
| A absent, parameter zero | `0x374cb4–0x374cc4` | `0x3751ec–0x3751fc` | **S** return zero without creating A. Audio D was already written by the editor; service success therefore does not imply that a sidecar exists. |
| A absent, parameter nonzero | `0x374cc8–0x374d7c` | `0x375200–0x3752b4` | **S** construct fresh `dat::SampleAdjunctData`, assign selected double and supplied sample count, serialize to a new tree, check available space against `0x41`, create an output stream with `0x8000` buffer, serialize, flush and destroy. Return zero after non-null output creation without checking serialization/flush status. |
| A already exists | `0x374d80–0x374e38` | `0x3752b8–0x375370` | **S** compare with service's active read path `+0x108`; same path returns 1. Otherwise open A, read a serialized tree (`0x68ba84`), populate fresh adjunct data (`0x509734`), destroy input stream, **attempt deletion of A** using `0x644b58`. Removal result is ignored. No separate existing-sidecar rejection. |
| Existing A, parameter zero | `0x374e3c–0x374e7c` | `0x375374–0x3753b4` | **S** deletion attempt has already occurred; returns zero with no rewrite. Thus zero can mean intentional metadata removal, including attempted removal that failed. |
| Existing A, parameter nonzero | `0x374e80–0x374f14` | `0x3753b8–0x37544c` | **S** update the selected field, clear the other double to zero, replace sample count, generate a new tree, check space and recreate/write A. Deletion precedes the space/open checks. No atomic rename or retained backup is visible. |
| Return/reset | `0x374bec–0x374c48` | `0x375124–0x375180` | **S** clear active write-path string and release lock; restore the saved service byte `+0x125` on ordinary branch completion. These volatile resets do not restore a deleted or partially written sidecar. |

**Data binding:** constructor `0x3762f8` names root `SampleAdjunctData` (`0x8b2070`), initializes bar `+0x28=1.0`, BPM `+0x30=0.0`, sample count `+0x38=0`, and registers three converter objects. Their original vtables at `0x8b1a68/0x8b1a90/0x8b1ab8` bind serialization/deserialization for **`bar`**, **`bpm`**, **`sampleNum`**. Key bindings are at `0x375f00`, `0x376098`, `0x375fd0`; serialization methods include `0x375e88`, `0x376128`, `0x375f58`. Slot `+0x14` sets BPM and zeros bar; slot `+0x10` sets bar and zeros BPM, in both new and replacement cases. Both store the caller's requested `end−start` as sampleNum.

`0x508fd0` builds a tree from the adjunct object's registered converters; `0x689c34 → 0x6900a4` writes tree names, property counts/values and children through stream methods. **I:** this is binary JUCE ValueTree-style adjunct serialization, not an audio stream or an XML-file write. Exact emitted bytes, round-trip behavior, malformed-input handling and preservation of unrecognized prior keys are not certified. The service regenerates a tree from its known data object; it does not prove byte-preserving metadata migration.

The scratch adjunct object's vtable `0x8b1a38` uses default no-op/status hooks at `0x1714c0–0x1714e8`; its registered converters operate on these fields. No project/settings/NAND/environment/panel write call was identified in the inspected post-save methods and these bound data conversions. **This narrows this service edge only.** Broader app completion, track setter and startup effects stay as recorded in 06; absence of a local call is not a physical storage or alias exclusion.

## Failure, durability and cleanup consequences

1. **Existing metadata can be lost before an error reply.** A is removed before the subsequent space check or output creation. A failure can leave the newly written audio subsequently removed by the editor and the old adjunct metadata missing. This is not a transaction over audio plus sidecar.
2. **Failed removal can produce append behavior.** Shared output constructor `0x64c760` checks existence, opens an existing file with raw flags 2 and seeks to end; an absent file is opened with flags `0x42`, mode `0x1a4`. On the usual Linux interpretation these are read/write and read/write-create, without exclusive creation or truncation. If A removal fails, or another actor recreates A, serialization can append to the surviving file. Filesystem races, aliases and actual target semantics remain U.
3. **Zero is not durable-success evidence.** Both slots invoke serialization, stream slot `+8` (flush `0x64ec68`) and deleting destructor, then set reply zero without inspecting the stream's error state. Flush writes buffered data and calls `fsync`; errors are stored at stream `+0x10`. That state is not tested by these callers. Flush/destructor handling does not certify complete positive short writes either. No readback oracle or error-injection receipt exists.
4. **Retry is not bounded locally.** Existing A matching active read path or failing to open can return 1. Editor loops at `0x0b73d0` / `0x0b75c4`, sleeping through `0x643c3c` and calling again while reply is 1. These local poll loops show neither a finite retry ceiling nor a cancel-byte check. This is static reachability, not an observed hang; a later admitted observation still needs independent finite containment.
5. **Editor failure cleanup does not restore A.** A nonzero terminal service reply reaches audio deletion at `0x0b7614`, whose return is ignored. This branch has no adjunct restoration or matching A deletion. Reachable service reply 3 (output open failure) maps to editor reply 6, reply 4 (unsupported suffix) to 11, reply 6 (space check) to 7; the full jump table also maps 2→5 and 5→11. Numerical mappings are S; enum names are not invented. A write/flush error may escape these numerical failures and still reach zero.

Deletion anchors: slot `+0x14` calls `0x644b58` at **`0x374e38`**; slot `+0x10` at **`0x375370`**. The helper attempts `rmdir` for a directory or `remove` otherwise (`0x644b58–0x644ba4`). New-write anchors `0x374d30` and `0x375268` respectively are `0b00a0e1 0410a0e1 bd530ceb` / `0b00a0e1 0410a0e1 6f520ceb`, followed by flush/destructor virtual calls and `0040a0e3` (zero result). Existing rewrite uses the same unchecked sequence at `0x374ee8` / `0x375420`.

## Revised exposure envelope and next question

| State | Mapping now established | Admission / recovery limit |
|---|---|---|
| Audio D and parents | Prior stock copy/create and directory operations in 06 still apply. | Copy failure is still ignored; selected-original Keep and safe Discard remain unproved. |
| **Sidecar A = D′ + `.dat`** | Additional persistent create/write, read/delete/rewrite or zero-parameter delete; may pre-exist even when D did not. | Q/T must bind A, aliases, prior existence/content/metadata and independent restoration. Preserve audio and adjunct together; include error/interruption windows before/after deletion and buffered write. |
| Filesystem metadata / storage | Sidecar operations alter directory entries and filesystem state at the resolved path. | Actual mount/media, permissions, directory effects, symlinks/hard links and interference are unknown. A's spelling is not proof of a harmless storage class. |
| Service/editor state | Locks, active paths, bytes and temporary trees are volatile; possible retry loop. | Successful unlock/destruction is not persistent cleanup. Finite intervention remains missing for an admitted trial. |
| Track references / project persistence | **Not resolved by this service trace.** Prior successful-save/replace branch separately invokes `0x2f8ed0`. | No inference that all stock-save effects are now bounded; project/loaded-buffer/reference consequences remain U. |
| Delivery, unit acceptance, startup / unique data | No new mechanism or exposure selected. | 06's actual unit correspondence, BM/H, conditional inherited startup and M09-Q/T gaps remain. No gate passed through static sidecar mapping. |

**Decision changed:** remove the opaque-service blocker for this identified stock route and add **pre-existing adjunct sidecars** to the persistent write/restore envelope. A future Normalize/Keep implementation cannot equate stock save zero with a verified audio-and-metadata commit. It must decide how to preserve/update adjunct semantics and independently verify resulting files; this report selects no implementation.

**One next read-only uncertainty:** the concrete track/sample model behind `0x2f8ed0` and its virtual slot `+8`, reached after successful SAVE & REPLACE at `0x28bc60`, and whether that branch causes additional persistent project/reference changes. The smallest discriminator is to bind that returned model's owner/vtable and trace the setter and its notifications. The completed service trace need not be repeated. This next question is proposed only; the current renewal ends with this report. Physical access/identity and any later exposure still need their applicable prior gates. No runtime duration, fixture, operator, controls or launch is selected here.

## Scope and renewed-allowance closeout

Only this handoff was written. Reviewed 06, historical evidence, original firmware/app/libraries, installed runtime and reference review files remain unchanged. No candidate, tool/source edit, export/database, package, build, test execution, guest/runtime, hardware, restore, Git operation, delegation, cross-chat message or external-network action occurred. Read-only host analysis commands are the method, not execution of original firmware or a proposed experiment. Raw tool output remains in this chat's tool transcript; no separate raw-export artifact is claimed.

No new tooling or firmware failure occurred in this renewal. Initial broad scans/disassembly produced literal/data leads, and interpretations above use checked function/data boundaries. Prior Prompt 6 tooling failures and all earlier consumed allowances remain recorded in 06; unused time is not pooled.

**Renewed allowance:** first recorded clock `2026-10-10 06:42:30 UTC` (01:42:30 Chicago). Charge 15 seconds for opening commentary/pre-clock preparation and a final save/verification/response reserve in the closeout below. Total ceiling is 960 seconds; review is due at report completion. No automatic renewal follows.

**Closed at report completion:** last accounting clock `2026-10-10 06:50:06 UTC`; measured elapsed 456 seconds + 15 seconds opening preparation + 45 seconds charged for final save, verification and response = **516/960 seconds debited**. **444 seconds remain unspent**, with no automatic continuation. This renewal is closed for owner review now. No construction or execution is authorized by this report.
