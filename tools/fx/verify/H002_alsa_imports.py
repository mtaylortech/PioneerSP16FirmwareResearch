#!/usr/bin/env python3
"""H002 step 1 - libasound / thread imports of target/EP085_Main_R_fw160 (1.60) and their direct callers.

Deterministic static scan (asserts target SHA-256 via harness/lib/sp16img.py):
  * PLT stub -> import name: each 12-byte ARM stub (add ip,pc ; add ip,ip ; ldr pc,[ip,#]!) is decoded to its GOT slot,
    which is matched against the .rel.plt R_ARM_JUMP_SLOT relocations (545/545 stubs map).
  * Callers: every aligned .text word encoding bl/blx/b imm24 whose target is the stub (bit-pattern scan), each site
    re-decoded with capstone to drop data false positives; containing function = .ARM.exidx start <= site.
Outputs (only in --out DIR): alsa_imports.txt (all snd_* imports + callers), thread_imports.txt, alsa_imports.json
Usage: .venv/bin/python harness/H002_alsa_imports.py --out harness/out/H002
"""
import argparse, json, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import sp16img

ap = argparse.ArgumentParser()
ap.add_argument("--out", default=os.path.join(sp16img.ROOT, "harness", "out", "H002"))
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
im = sp16img.Image(); plt = im.plt()
callers = defaultdict(list)
for site, tgt, kind in im.direct_calls():
    if tgt in plt:
        ins = list(im.md.disasm(im.data[im.off(site):im.off(site) + 4], site))
        if not ins or ins[0].mnemonic not in ("bl", "blx", "b", "beq", "bne", "blt", "bge", "bgt", "ble", "bhi", "bls",
                                               "bcc", "bcs", "blo", "bhs", "bmi", "bpl", "blne", "bleq"):
            continue
        callers[tgt].append((site, im.func_of(site)[0], ins[0].mnemonic))

THREAD = ("pthread_create", "pthread_setschedparam", "pthread_attr_setschedparam", "pthread_attr_setschedpolicy",
          "sched_setscheduler", "pthread_attr_setinheritsched", "sched_get_priority_max", "sched_get_priority_min",
          "pthread_attr_setstacksize", "pthread_join", "open", "open64", "ioctl", "mmap", "mmap64", "dlopen", "dlsym",
          "poll", "select", "read", "write", "socket", "connect")
J = {}
for fname, pred in (("alsa_imports.txt", lambda n: n.startswith("snd_")), ("thread_imports.txt", lambda n: n in THREAD)):
    L = []
    for va, n in sorted(plt.items(), key=lambda x: x[1]):
        if not pred(n): continue
        cs = sorted(callers.get(va, []))
        J[n] = {"plt": hex(va), "callers": [[hex(s), hex(f) if f else None, k] for s, f, k in cs]}
        L.append("%-48s plt=0x%x  %d site(s)" % (n, va, len(cs)))
        for s, f, k in cs:
            L.append("    site 0x%x (%s) in fn 0x%x" % (s, k, f or 0))
    open(os.path.join(a.out, fname), "w").write("\n".join(L) + "\n")
    print("== %s: %d imports" % (fname, sum(1 for l in L if not l.startswith("    "))))
json.dump(J, open(os.path.join(a.out, "alsa_imports.json"), "w"), indent=1, sort_keys=True)
