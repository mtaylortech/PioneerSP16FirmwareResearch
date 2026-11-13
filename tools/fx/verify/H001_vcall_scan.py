#!/usr/bin/env python3
"""H001 helper: list virtual-call sites (ldr Rx,[Ry,#off] ... blx Rx within 4 insns) and immediate r3 values set before
each, inside the .ARM.exidx extent of each given function VA. Usage: H001_vcall_scan.py --out DIR VA [VA...]"""
import argparse, bisect, os, re, struct, capstone
HERE = os.path.dirname(os.path.abspath(__file__)); T = os.path.join(os.path.dirname(HERE), "target", "EP085_Main_R_fw160")
ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H001")); ap.add_argument("va", nargs="+")
a = ap.parse_args(); data = open(T, "rb").read()
EX_LO, EX_HI = 0xb3dc94, 0xb3dc94 + 0x29df0          # .ARM.exidx (readelf/lief, see H001_fx_rtti_vtables.py)
w = lambda va: struct.unpack_from("<I", data, va - 0x8000)[0]
starts = []
for x in range(EX_LO, EX_HI, 8):
    o = w(x) & 0x7fffffff; o = o - 0x80000000 if o & 0x40000000 else o; starts.append((x + o) & 0xffffffff)
starts = sorted(set(starts)); md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
L = []
for s in a.va:
    va = int(s, 16); end = starts[bisect.bisect_right(starts, va)]
    ins = list(md.disasm(data[va - 0x8000:end - 0x8000], va)); out = []
    for i, x in enumerate(ins):
        m = re.match(r"(\w+), \[(\w+), #(0x[0-9a-f]+)\]", x.op_str)
        if x.mnemonic == "ldr" and m:
            for y in ins[i + 1:i + 5]:
                if y.mnemonic == "blx" and y.op_str == m.group(1):
                    r3 = [z.op_str for z in ins[max(0, i - 6):i + 5] if z.mnemonic == "mov" and z.op_str.startswith("r3, #")]
                    out.append("vcall@0x%x off=%s slot=%d %s" % (y.address, m.group(3), int(m.group(3), 16) // 4,
                                                                 ("r3=" + r3[-1][4:]) if r3 else "")); break
    L.append("fn 0x%x..0x%x (%d insns): %s" % (va, end, len(ins), "; ".join(out) or "no vcalls"))
os.makedirs(a.out, exist_ok=True); open(os.path.join(a.out, "vcall_scan.txt"), "a").write("\n".join(L) + "\n"); print("\n".join(L))
