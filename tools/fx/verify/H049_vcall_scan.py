#!/usr/bin/env python3
"""H049 step 2 — whole-.text census of virtual calls at vtable offset +8 (ITriggerAndParameterReceiver slot 2 position) with the
argument tags of r1 (offset) and r2 (type), using harness/lib/armflow.py (heuristic, path-insensitive value tags). Also a direct-call
census of the slot-2 implementations (0x1263f4, LfoProcessor 0x131634/0x13163c, MidiTrackOutputFormatter 0x14bdf4, TrackUnit thunk
0x1c7a60 / body 0x1c7a68, FPMB no-op 0x11fcd0, base no-op 0x11fc44) and every .rodata/.data word equal to one of them.
Read-only on target/ (1.60). Own code. Run: .venv/bin/python -B harness/H049_vcall_scan.py --out harness/out/H049 [--lo 0x.. --hi 0x..]
"""
import argparse, json, os, struct, sys, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib"))
import sp16img, armflow                                         # noqa: E402

SLOT2 = {0x1263f4: "IFPM_s2", 0x131634: "Lfo_s2_thunk", 0x13163c: "Lfo_s2", 0x14bdf4: "MidiTOF_s2", 0x1c7a60: "TrackUnit_s2_thunk",
         0x1c7a68: "TrackUnit_s2", 0x11fcd0: "FPMB_s2_noop", 0x11fc44: "Recv_s2_noop"}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H049"))
    ap.add_argument("--lo", type=lambda s: int(s, 0)); ap.add_argument("--hi", type=lambda s: int(s, 0))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    im = sp16img.Image(); fl = armflow.Flow(im)
    lo = a.lo or im.sec[".text"][0]; hi = a.hi or im.sec[".text"][1]
    # 1. direct references to slot-2 implementations
    direct = [(hex(s), hex(t), k, SLOT2[t]) for s, t, k in im.direct_calls() if t in SLOT2]
    words = []
    for va, sz, off in im.segs:
        n = sz // 4
        for i, w in enumerate(struct.unpack_from("<%dI" % n, im.data, off)):
            if w in SLOT2: words.append((hex(va + 4 * i), SLOT2[w]))
    # 2. vcall census
    starts = armflow.refined_starts(im, lo, hi); starts.append(hi)
    res = []; t0 = time.time(); nf = 0
    for k in range(len(starts) - 1):
        s, e = starts[k], starts[k + 1]
        if e - s > 0x8000: e = s + 0x8000
        try:
            evs = fl.analyse(s, e)
        except Exception as ex:                          # noqa: BLE001
            res.append(dict(func=hex(s), error=repr(ex))); continue
        nf += 1
        for ev in evs:
            if ev["kind"] == "vcall" and ev["off"] == 8:
                res.append(dict(func=hex(s), site=hex(ev["site"]), obj=ev["obj"],
                                r1=sorted(ev["args"].get("r1", [])), r2=sorted(ev["args"].get("r2", []))))
    dt = time.time() - t0
    const_r2 = [r for r in res if "r2" in r and any(x.startswith("C:") for x in r["r2"])]
    lines = ["direct calls/branches to slot-2 impls: %d" % len(direct)] + ["  %s -> %s %s %s" % d for d in direct]
    lines += ["data words equal to slot-2 impls: %d" % len(words)] + ["  %s %s" % w for w in words]
    lines += ["functions analysed %d in %.0f s; vcalls at +8: %d; with constant r2: %d" % (nf, dt, sum(1 for r in res if 'site' in r), len(const_r2))]
    for r in const_r2:
        lines.append("  %s site %s obj=%s r1=%s r2=%s" % (r["func"], r["site"], r["obj"], r["r1"], r["r2"]))
    open(os.path.join(a.out, "vcall8.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(dict(direct=direct, words=words, vcalls=res), open(os.path.join(a.out, "vcall8.json"), "w"), indent=0)
    print("\n".join(lines[:400]))


if __name__ == "__main__":
    main()
