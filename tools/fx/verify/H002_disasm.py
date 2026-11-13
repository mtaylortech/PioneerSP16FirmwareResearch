#!/usr/bin/env python3
"""H002 helper: annotated capstone listing (PLT names, literal values, strings) of the function starting at VA
(extent = next .ARM.exidx start) or of N instructions. Writes --out DIR/dis_<va>.txt. Asserts the target SHA-256.
Usage: .venv/bin/python harness/H002_disasm.py --out harness/out/H002 VA [N]"""
import argparse, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib"))
import sp16img
ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(sp16img.ROOT, "harness", "out", "H002"))
ap.add_argument("va"); ap.add_argument("n", nargs="?", type=int); a = ap.parse_args()
im = sp16img.Image(); va = int(a.va, 16)
L = sp16img.annotate(im, va, end=(va + 4 * a.n) if a.n else None)
os.makedirs(a.out, exist_ok=True); open(os.path.join(a.out, "dis_%x.txt" % va), "w").write("\n".join(L) + "\n")
print("\n".join(L))
