#!/usr/bin/env python3
"""H001 helper: capstone ARM disassembly of N instructions at a VA in target/EP085_Main_R_fw160 (local inspection only;
output goes to --out DIR/disasm_<va>.txt and stdout). Usage: H001_disasm.py --out DIR VA [N]"""
import argparse, os, struct, capstone, lief
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(os.path.dirname(HERE), "target", "EP085_Main_R_fw160")
ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H001"))
ap.add_argument("va"); ap.add_argument("n", nargs="?", type=int, default=40); a = ap.parse_args()
va = int(a.va, 16); data = open(T, "rb").read(); off = va - 0x8000  # first PT_LOAD: vaddr 0x8000 at file offset 0
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
L = ["0x%x: %s %s" % (i.address, i.mnemonic, i.op_str) for i in md.disasm(data[off:off + 4 * a.n], va)][:a.n]
os.makedirs(a.out, exist_ok=True); open(os.path.join(a.out, "disasm_%x.txt" % va), "w").write("\n".join(L) + "\n")
print("\n".join(L))
