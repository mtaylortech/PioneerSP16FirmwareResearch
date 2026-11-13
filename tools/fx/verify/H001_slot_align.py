#!/usr/bin/env python3
"""H001 helper: align vtable slots across sibling classes from fx_classes.json (output of H001_fx_rtti_vtables.py).
Usage: H001_slot_align.py --out DIR [--family NAME ...]  (reads DIR/fx_classes.json, writes DIR/align_<family>.txt)"""
import argparse, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES = {
 "EffectBase": ["EffectBase", "Chorus", "Distortion", "Ducker", "Flanger", "FxCompressor", "InsertFxCompressor",
                "SendFxCompressor", "LoFi", "PerformanceFxLoFi", "MultiModeFilter", "ParametricEqualizer", "Phaser",
                "InsertFxDelay", "SendFxDelay@-568", "SendFxReverb"],
 "c_effect_base": ["c_effect_base", "c_distortion", "c_chorus", "c_flanger"],
 "FxProcessorBase": ["IAudioProcessor", "ILoadEstimableAudioProcessor", "FxProcessorBase", "InsertFxProcessor",
                     "MasterFxProcessor", "SendFxProcessor", "MasterFxUnit", "SendFxUnit", "CompositeFxUnit"],
 "SRBSV": ["SamplingRateAndBufferSizeVariable", "EffectInOutGain", "DelayModule", "DelayModuleStereo",
           "SmoothingDelayModule", "ReverbAllPassFilter", "ReverbCombFilter", "ReverbPreDelay"],
 "DelayReverbBases": ["DelayEchoBase", "DelayEchoBaseSingleDelay", "Reverb9NXSBase", "InsertFxDelay@-440",
                      "SendFxReverb@-440", "SendFxDelay"],
 "FxParameterManager": ["FxParameterManagerBase", "InsertFxParameterManager", "MasterFxParameterManager",
                        "SendFxParameterManager"],
}
ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H001"))
ap.add_argument("--family", nargs="*", default=list(FAMILIES))
a = ap.parse_args()
cls = {c["name"]: c for c in json.load(open(os.path.join(a.out, "fx_classes.json")))}
for fam in a.family:
    cols = []
    for spec in FAMILIES[fam]:
        n, _, ott = spec.partition("@")
        if n not in cls: print("missing class", n); continue
        c = cls[n]; vt = [v for v in c["vtables"] if (int(ott) if ott else 0) == v["offset_to_top"]][0]
        cols.append((spec, vt))
    L = ["family %s" % fam, "cell = target [vfp/backbr/size]; '=' same as first column; '*' = __cxa_pure_virtual"]
    for spec, vt in cols:
        L.append("  %-24s ap=%s nslots=%d end: %s" % (spec, vt["address_point"], vt["n_slots"], vt["end_reason"]))
    mx = max(v["n_slots"] for _, v in cols)
    L.append("slot | " + " | ".join(s[:14] for s, _ in cols))
    for i in range(mx):
        row = []
        base = cols[0][1]["slots"][i]["target"] if i < len(cols[0][1]["slots"]) else None
        for _, vt in cols:
            if i >= len(vt["slots"]): row.append("-"); continue
            s = vt["slots"][i]
            if "import" in s: row.append("*" if s["import"] == "__cxa_pure_virtual" else s["import"]); continue
            if s["target"] == base and vt is not cols[0][1]: row.append("="); continue
            row.append("%s[%d/%d/%d]" % (s["target"][2:], s["vfp"], s["back_branches"], s["size"]))
        L.append("%3d | " % i + " | ".join(row))
    open(os.path.join(a.out, "align_%s.txt" % fam), "w").write("\n".join(L) + "\n")
    print("\n".join(L)); print()
