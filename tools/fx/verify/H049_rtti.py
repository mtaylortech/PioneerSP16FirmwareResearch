#!/usr/bin/env python3
"""H049 step 1 — RTTI closure of ITriggerAndParameterReceiver: every class with it as a (transitive) base, the sub-object offset,
each vtable group and the receiver's slots 0..N in each group. Read-only on target/ (1.60). Own code.
Run: .venv/bin/python -B harness/H049_rtti.py --out harness/out/H049
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE)
import sp16img                                                 # noqa: E402
from H011_effect_interface import Rtti                        # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H049"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = sp16img.Image(); rt = Rtti(im)
    roots = [t for t, v in rt.ti.items() if v["name"] == "28ITriggerAndParameterReceiver"]
    assert len(roots) == 1, roots
    root = roots[0]
    cl = rt.closure(root)
    lines = ["root typeinfo 0x%x %s; closure %d classes" % (root, rt.ti[root]["name"], len(cl))]
    res = {}
    for ti, off in sorted(cl.items(), key=lambda x: rt.ti[x[0]]["name"]):
        nm = rt.name(ti)
        groups = [g for g in rt.groups if g[1] == ti]
        res[nm] = {"typeinfo": hex(ti), "recv_off": off, "groups": []}
        lines.append("%s ti=0x%x receiver sub-object at +0x%x bases=%s" % (
            nm, ti, off, [(rt.name(b) if b in rt.ti else hex(b or 0), hex(o or 0)) for b, o in rt.ti[ti]["bases"]]))
        for ott_a, _ti, ott, apt in groups:
            sl = rt.slots(apt)
            res[nm]["groups"].append({"ap": hex(apt), "ott": ott, "slots": [hex(x) for x in sl]})
            if -ott == off:
                lines.append("   group ap=0x%x ott=%d (receiver group) slots0-5=%s n=%d" % (apt, ott, [hex(x) for x in sl[:6]], len(sl)))
            else:
                lines.append("   group ap=0x%x ott=%d n=%d" % (apt, ott, len(sl)))
    # root's own vtable(s)
    for g in rt.groups:
        if g[1] == root:
            lines.append("root vtable ap=0x%x slots=%s" % (g[3], [hex(x) for x in rt.slots(g[3])]))
    open(os.path.join(a.out, "rtti.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(res, open(os.path.join(a.out, "rtti.json"), "w"), indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
