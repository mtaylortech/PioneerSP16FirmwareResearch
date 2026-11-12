<!-- E2: summary-only per owner decision. Entries written from docs/findings.md
     wording, NOT copied from the underlying notes. The notes themselves are not
     published. -->
# Thread E2 — updater / USB / diagnostic (1.50 line): summary only

These six 1.50 studies examined the USB-A update path, closed-unit USB
visibility, and the VM-only ARM diagnostic. By the owner's decision they are
**not published as notes**; this page summarizes them at the level already in
[`docs/findings.md`](../docs/findings.md). The board boot-to-app-launch work
they informed is published and runnable in
[`emulation/board/`](../emulation/board/); the USB/diagnostic arm is not
included there.

What the public findings already state about this area: the USB-A updater
checks a package marker and CRC32 before mounting and running its `update`
program — **not** cryptographic authentication — and **no** command shell or
arbitrary-code loading was shown. In the emulator, a VM-only ARM diagnostic
wrote tags to and read bytes back from the guest framebuffer, and a fresh
no-USB boot of the retained disk reached the same checkpoint. Physical
scanout, NAND recovery, and any deployable modified firmware remain unproven.
No repack the device would accept was demonstrated.

| note (not published) | topic | status |
|---|---|---|
| updater-acceptance-activation-150 | updater acceptance / activation path | summary only |
| updater-first-write-recovery-compatibility-150 | first writes, interruption, carrier compatibility | summary only |
| usb-visibility-access-150 | closed-unit USB visibility and access | summary only |
| diagnostic-entry-return-contract-150 | diagnostic entry and return contract | summary only |
| diagnostic-frame-preflight-150 | host frame, viewing window, preflight | summary only |
| diagnostic-host-prototype-150 | host-only diagnostic reference | summary only |

Why summary-only: this material concerns update acceptance and running a custom
diagnostic in the emulated device. Publishing the step detail adds device-attack
surface without adding research value beyond what `docs/findings.md` and
`emulation/board/` already establish. A future maintainer who wants them must
decide that explicitly.
