#!/usr/bin/env python3
"""H004 — FxParamIndex 0-71 -> effect index / slot-14 index, and the parameter-manager -> processor -> effect slot-14 value path.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and
never stored; outputs are our own derived numbers. Emulation is guest-memory only; nothing is written outside --out.

Sections (criteria of kb/cycles/029.md):
  C1 static tables: InsertFxParameterManager (IFPM) slots 55/56 tables 0x843e10 / 0x843e58 (= 0x843d98+0x78/+0xc0), slots 57/58
     modulation tables 0x843ea0 / 0x843f40; the code that indexes them (capstone patterns + emulated slot calls); the 72-row map;
     the one-to-one test; the 72-case switches that key on FxParamIndex elsewhere in .text.
  C2 static value path: every FxProcessorBase 0x112924(proc, effect, idx, value) call site in IFPM s10 / s38 and Master/Send s51 / s38,
     with the EffectData source of the value; Master/Send manager slots 6/10/55-58 = base no-ops.
  C3 Insert emulation: REAL InsertFxProcessor (ctor 0x118b0c via harness/H077 EmuProc) + REAL IFPM ctor 0x12864c, slots 6 / 2 / 10 /
     27 / 13 / 51 / 36 / 34 / 50; logs every effect slot-14 entry. Stand-ins (declared): EffectData object and its SwitchableObject holder;
     processor slot 54 0x11684c (Ducker trigger-source hook) is skipped; on the reload path s52 0x12802c (juce::Identifier type name ->
     index) and the enum converters (manager slots 60-74) return harness-chosen values (Identifier/StringPool not emulated).
  C4 Master/Send emulation: REAL Master/Send processors (EmuProc) + base slot 27 0x11ce58 on a stand-in manager (+0x1c proc, +0x20
     holder, +0x24 enabled); Master/Send slots 6 / 10 / 55-58 called and checked inert.
  C5 alternatives: scaling/clamping on the way (refuted by bit-exact identity incl. out-of-range), type filter on the lock path,
     "slot-14 index = FxParamIndex - group start", "modulation id = 100 + FxParamIndex".
Run: .venv/bin/python -B harness/H004_fxparam_map.py --out DIR
"""
import argparse, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u, u2f                                       # noqa: E402
from sp16img import Image                                      # noqa: E402

# ------------------------------------------------------------------------------------------------------------------ addresses (1.60)
T_BASE = 0x843d98                      # effectId->index (20 ints) ; +0x50 inverse ; +0x78 FxParamIndex->effect ; +0xc0 ->sub-slot
T_EFF, T_SUB = T_BASE + 0x78, T_BASE + 0xc0
MOD_EFF, MOD_SUB = 0x843ea0, 0x843f40  # slots 57/58: id-100 -> effect / sub-slot (156 entries)
VT = {"insert": 0x84407c, "master": 0x8437ec, "send": 0x8446d4, "base": 0x8430cc}
IFPM = dict(ctor=0x12864c, s2=0x1263f4, s6=0x1263c0, s10=0x129b34, s13=0x126434, s27=0x126c0c, s36=0x126b68, s51=0x126394,
            s52=0x12802c, s55=0x1262e8, s56=0x126304, s57=0x126320, s58=0x12633c)
PROC_SET_CUR, PROC_SET_IDX = 0x1126dc, 0x112924          # FxProcessorBase slot 29 (vt+0x74) / helper (proc, effect, idx, v)
BASE_S27 = 0x11ce58                                         # FxParameterManagerBase slot 27 (Master/Send)
PROC_S54_INSERT = 0x11684c                                  # Insert processor slot 54 (receiveTrigger types 11/15)

INS_NAMES = ["Chorus", "Flanger", "ParametricEqualizer", "MultiModeFilter", "InsertFxDelay", "LoFi", "Distortion",
             "InsertFxCompressor", "Phaser", "Ducker"]
# slot-14 parameter names per Insert effect index, from kb/findings.md (F025/F032/F041/F045/F057/F063/F069/F075/F081/F089)
P = {
    0: {0: "RATE", 1: "DEPTH", 2: "PHASE", 3: "DEPTH SCALE", 5: "MIXRATIO", 6: "SYNC", 7: "BPM"},
    1: {0: "RATE", 1: "DEPTH", 2: "PHASE", 3: "DEPTH SCALE", 4: "FEEDBACK", 5: "MIXRATIO", 6: "SYNC", 7: "BPM"},
    2: {0: "B1 FREQUENCY", 1: "B1 GAIN", 2: "B1 Q", 3: "B2 FREQUENCY", 4: "B2 GAIN", 5: "B2 Q", 6: "BAND1 TYPE", 7: "BAND2 TYPE"},
    3: {0: "CUTOFF", 1: "GAIN", 2: "Q", 3: "GLIDE", 4: "NONE (never read)", 5: "MIXRATIO", 6: "FILTERTYPE", 7: "FILTERDB"},
    4: {0: "DelayTime", 1: "Feedback", 2: "HiCut", 3: "LowCut (never read)", 4: "Spread (never read)", 5: "Mixratio", 6: "SYNC", 7: "BPM"},
    5: {0: "PREAMP", 1: "REDUCTION", 2: "BITDEPTH", 3: "CUTOFF", 4: "RESONANCE", 5: "MIXRATIO", 6: "FILTERTYPE", 7: "FILTERPOSITION"},
    6: {0: "drive (dB = 40v)", 1: "output LPF", 2: "HPF", 3: "pre-clip LPF", 4: "dynamics threshold", 5: "mix (wet v, dry 1-v)"},
    7: {0: "Threshold", 1: "Ratio", 2: "Attack", 3: "Release", 4: "Gain", 5: "Mixratio", 6: "LookAhead", 7: "Knee", 8: "LevelDetect"},
    8: {0: "Rate", 1: "Width", 2: "Phase", 3: "Frequency", 4: "Feedback", 5: "Mixratio", 6: "Sync", 7: "Bpm"},
    9: {0: "ATTACK", 1: "ATTACKCURVE", 2: "RELEASE", 3: "RELEASECURVE", 4: "NONE (never read)", 5: "DEPTH", 6: "SYNC", 7: "BPM",
        8: "TRIGGER", 9: "OFFSET", 10: "SOURCE"},
}
VALUES = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, -0.25, 0.3333333432674408]    # >= 5 in range + 2 out of range + one non-dyadic
R003_150 = sorted(set(range(0, 11)) | set(range(23, 35)) | set(range(41, 46)) | set(range(50, 55)) | set(range(56, 72)))  # REFERENCE.md


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u & 0x80000000 else u
def s8(b): return b - 256 if b > 127 else b


# ===================================================================================================================== C1 / C2 static
def static_part(im, P_, check):
    J = {}
    rd = lambda a, n: im.data[im.off(a):im.off(a) + n]
    eff = [s8(b) for b in rd(T_EFF, 72)]; sub = [s8(b) for b in rd(T_SUB, 72)]
    meff = [s8(b) for b in rd(MOD_EFF, 156)]; msub = [s8(b) for b in rd(MOD_SUB, 156)]
    id2idx = [s32(im.u32(T_BASE + 4 * i)) for i in range(20)]
    J.update(eff=eff, sub=sub, mod_eff=meff, mod_sub=msub, effectid_to_index=id2idx)
    # --- the code that indexes the tables (instruction patterns, capstone) ---
    def txt(a, n): return ["%s %s" % (i.mnemonic, i.op_str) for i in im.disasm(a, a + 4 * n)]
    s55, s56 = txt(IFPM["s55"], 5), txt(IFPM["s56"], 5)
    check(s55 == ["cmp r1, #0x47", "ldrls r3, [pc, #0xc]", "mvnhi r0, #0", "addls r1, r3, r1", "ldrsb r0, [r1, #0x78]".replace("ldrsb", "ldrsbls")]
          and im.u32(IFPM["s55"] + 0x18) == T_BASE,
          "IFPM slot 55 0x1262e8 = (FxParamIndex <= 71u) ? (int8)T[0x843d98+0x78+i] : -1  (vtable 0x84407c word %d)" % 55)
    check(s56 == ["cmp r1, #0x47", "ldrls r3, [pc, #0xc]", "mvnhi r0, #0", "addls r1, r3, r1", "ldrsbls r0, [r1, #0xc0]"]
          and im.u32(IFPM["s56"] + 0x18) == T_BASE, "IFPM slot 56 0x126304 = (i <= 71u) ? (int8)T[0x843d98+0xc0+i] : -1")
    s6 = txt(IFPM["s6"], 12)
    check(s6[:7] == ["mov r1, r2", "ldr r2, [r0]", "push {r3, r4, r5, lr}", "mov r5, r3", "ldr r3, [r2, #0xe0]", "mov r4, r0", "blx r3"]
          and s6[7:11] == ["mov r2, #1", "add r3, r4, r0", "add r4, r4, r0, lsl #2", "strb r2, [r3, #0x80]"] and s6[11] == "str r5, [r4, #0x68]",
          "IFPM slot 6 0x1263c0 (this, _, FxParamIndex, value): sub = slot56(FxParamIndex); +0x80[sub] = 1; +0x68[4*sub] = value "
          "(no slot-55 effect check, no transform)")
    vt_ok = all(im.u32(VT["insert"] + 4 * k) == a for k, a in ((6, IFPM["s6"]), (10, IFPM["s10"]), (13, IFPM["s13"]), (27, IFPM["s27"]),
                                                              (55, IFPM["s55"]), (56, IFPM["s56"]), (57, IFPM["s57"]), (58, IFPM["s58"])))
    check(vt_ok, "IFPM vtable 0x84407c slots 6/10/13/27/55/56/57/58 = 0x1263c0/0x129b34/0x126434/0x126c0c/0x1262e8/0x126304/0x126320/0x12633c")
    # --- literal-pool / data references to the tables: only s53..s56 (base) and s57/s58 ---
    lo, hi = im.sec[".text"]; o0 = im.off(lo); W = struct.unpack_from("<%dI" % ((hi - lo) // 4), im.data, o0)
    refs = {t: [hex(lo + 4 * i) for i, w in enumerate(W) if w == t] for t in (T_BASE, T_EFF, T_SUB, MOD_EFF, MOD_SUB)}
    J["table_literal_refs"] = refs
    check(refs[T_BASE] == ["0x1262c8", "0x1262e4", "0x126300", "0x12631c"] and refs[T_EFF] == [] and refs[T_SUB] == []
          and refs[MOD_EFF] == ["0x126338"] and refs[MOD_SUB] == ["0x126354"],
          ".text literal words: 0x843d98 only in IFPM s53/s54/s55/s56 pools; no direct +0x78/+0xc0 pointer; 0x843ea0/0x843f40 only in s57/s58")
    # --- Master/Send manager slots 6/10/55..58 are base no-ops ---
    noop = {}
    for w in ("master", "send"):
        noop[w] = {k: hex(im.u32(VT[w] + 4 * k)) for k in (6, 10, 55, 56, 57, 58)}
    J["master_send_slots"] = noop
    check(all(noop[w][6] == "0x11fccc" and noop[w][10] == "0x11fcc8" and noop[w][55] == "0x11fdd8" and noop[w][56] == "0x11fde0"
              and noop[w][57] == "0x11fde8" and noop[w][58] == "0x11fdf0" for w in noop)
          and txt(0x11fccc, 1) == ["bx lr"] and txt(0x11fcc8, 1) == ["bx lr"]
          and all(txt(a, 2) == ["mov r0, #0", "bx lr"] for a in (0x11fdd8, 0x11fde0, 0x11fde8, 0x11fdf0)),
          "Master 0x8437ec / Send 0x8446d4: slot 6 = slot 10 = `bx lr`, slots 55-58 = `return 0` (no FxParamIndex tables on Master/Send)")
    # --- 72-case switches on FxParamIndex elsewhere ---
    ins = []
    for fn_lo, fn_hi in ((0x1de684, 0x1dfadc), (0x351c70, 0x3533bc), (0x3535dc, 0x353a10)):
        ins += im.disasm(fn_lo, fn_hi)
    sw = {}
    for k, i in enumerate(ins):
        if i.mnemonic == "cmp" and i.op_str.endswith("#0x47") and k + 1 < len(ins) and ins[k + 1].mnemonic == "ldrls" and "pc, [pc" in ins[k + 1].op_str:
            jt = ins[k + 1].address + 8; tg = [im.u32(jt + 4 * c) for c in range(72)]
            dflt = max(set(tg), key=tg.count)
            sw[hex(i.address)] = [c for c in range(72) if tg[c] != dflt]
    J["switch72"] = sw
    valid = [i for i in range(72) if eff[i] >= 0]
    check(sw.get("0x1de6dc") == valid, "switch @0x1de6dc (fn 0x1de684, builds UserModeFloatParameter(kind 1, FxParamIndex)) has a case "
          "exactly for the %d rows with T_eff >= 0" % len(valid))
    check(sw.get("0x351c8c") == R003_150 and sw.get("0x353614") == R003_150,
          "switches @0x351c8c (fn 0x351c70) and @0x353614 (fn 0x3535dc) have exactly the [1.50] R003 49-case set (H003 lead)")
    case_args = {}
    for c in valid:
        t0 = im.u32(0x1de6e8 + 4 * c); r = {}
        for x in im.disasm(t0, t0 + 40):
            mm_ = re.match(r"(r[12]), #(0x[0-9a-f]+|\d+)$", x.op_str)
            if x.mnemonic == "mov" and mm_: r[mm_.group(1)] = int(mm_.group(2), 0)
            if x.mnemonic == "mov" and x.op_str == "r2, r1": r["r2"] = r.get("r1")
            if x.mnemonic == "bl" and x.op_str != "#0x102e8": r["bl"] = x.op_str; break
        case_args[c] = (r.get("r1"), r.get("r2"), r.get("bl"))
    check(all(case_args[c] == (1, c, "#0x1ddf44") for c in valid),
          "every one of the 55 cases does new(0x18) then 0x1ddf44(obj, kind 1, id = FxParamIndex, ...)")
    tin = im.cstr(im.u32(im.u32(0x868600 - 4) + 4), 60)
    ctor_vt = [i for i in im.disasm(0x1ddf44, 0x1ddf60) if i.mnemonic == "ldr" and "pc" in i.op_str]
    check(tin == "22UserModeFloatParameter" and im.u32(0x1ddf4c + 8 + 0x34) == 0x868600 and len(ctor_vt) == 1,
          "0x1ddf44 (called by every case of the @0x1de6dc switch) installs vtable 0x868600 = typeinfo name %r" % tin)
    # sequencer-side lock table used by the 72-case reader 0x3535dc (ldrsb [0x8ab188 + 0x10 + f]); compare with the manager table
    rdr = ["%s %s" % (i.mnemonic, i.op_str) for i in im.disasm(0x3535dc, 0x353608)]
    seqT = [s8(b) for b in rd(0x8ab198, 72)]
    diff = [f for f in range(72) if seqT[f] != sub[f]]
    J["seq_lock_table_0x8ab198"] = seqT; J["seq_vs_manager_sub_diff"] = diff
    check(im.u32(0x3535ec + 8 + 0x418) == 0x8ab188 and "ldrsbls ip, [ip, #0x10]" in rdr and "add r1, r1, #0x1a" in rdr
          and all(seqT[f] == sub[f] for f in range(72) if eff[f] >= 0),
          "reader 0x3535dc: word = rec[0x1a + 6*unit + Tseq[f]], Tseq = int8 @0x8ab198; Tseq equals the manager T_sub on all 55 valid rows; "
          "differs only at %s" % diff)
    # --- C2: every 0x112924 call site in the managers: (effect, idx, value source) ---
    calls = im.direct_calls()
    def sites(fn):
        s, e = im.func_of(fn); out = []
        for a in sorted(x for x, t, k in calls if t == PROC_SET_IDX and s <= x < e):
            r1 = r2 = src = None
            for x in reversed(im.disasm(a - 4 * 24, a)):
                op = x.op_str
                if r1 is None and x.mnemonic == "mov" and op.startswith("r1, #"): r1 = int(op[5:], 0)
                if r2 is None and x.mnemonic == "mov" and op.startswith("r2, #"): r2 = int(op[5:], 0)
                if r2 is None and x.mnemonic == "mov" and op == "r2, r1": r2 = "r1"
                m = re.match(r"r3, \[r3, #(0x[0-9a-f]+)\]$", op)
                if src is None and x.mnemonic in ("ldr", "ldrb") and m: src = "%s ED+%s" % ("float" if x.mnemonic == "ldr" else "byte", m.group(1))
                if src is None and x.mnemonic == "blx": src = "enum converter"
                if x.mnemonic in ("bl", "b") and x.address != a and "0x4f782c" not in op: break
            out.append((hex(a), r1, r1 if r2 == "r1" else r2, src))
        return out
    C2 = {nm: sites(fn) for nm, fn in (("insert_s10", 0x129b34), ("insert_s38", 0x127928), ("master_s51", 0x121174),
                                        ("send_s51", 0x12de8c), ("master_s38", 0x1232fc), ("send_s38", 0x130000))}
    J["c2_sites"] = C2
    six = lambda lst: all(src == "float ED+%s" % hex(0x38 + 8 * idx) for _, e_, idx, src in lst if isinstance(idx, int) and idx <= 5)
    for w in ("master_s51", "send_s51"):
        L = C2[w]
        check(len(L) == 66 and six(L) and sorted(set(e_ for _, e_, _, _ in L)) == list(range(10)),
              "%s: 66 direct sets, every slot-14 index 0..5 is fed from EffectData float +0x38+8*index (identity sub-slot -> index)" % w)
    J["master_send_s51_map"] = {w: {e_: sorted(set((idx, src) for _, ee, idx, src in C2[w] if ee == e_)) for e_ in range(10)}
                                for w in ("master_s51", "send_s51")}
    check(C2["master_s51"] and [(e_, i) for _, e_, i, _ in C2["master_s51"]] == [(e_, i) for _, e_, i, _ in C2["send_s51"]],
          "Master s51 and Send s51 set the same (effect, slot-14 index) sequence")
    return J


# ===================================================================================================================== C3 Insert rig
class InsertRig:
    """Real InsertFxProcessor (H077 EmuProc) + real IFPM ctor, stand-in EffectData + SwitchableObject holder."""
    def __init__(self, slot=0):
        import H077_master_send_proc as H77
        self.H77 = H77
        self.x = x = H77.EmuProc("insert"); e = self.e = x.e
        self.extra_s14 = []
        # make sure every effect's slot-14 entry is watched (H077 watches 0x105d24 and the 3 overrides)
        self.s14_fns = sorted(set(e.u32(e.u32(o) + 0x38) for o in x.objs))
        for a in self.s14_fns:
            if a not in H77.SLOT14:
                e.add_watch(a, lambda em: x.s14.append(("other@0x%x" % em.uc.reg_read(emu.LR), em.r(0), em.r(1), em.r(2))))
        self.s54 = []
        def skip54(em):
            self.s54.append((em.r(1),)); em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
        e.add_watch(PROC_S54_INSERT, skip54)
        self.setfx = []
        e.add_watch(0x11735c, lambda em: self.setfx.append(s32(em.r(1))))
        # stand-ins: EffectData (6 floats at +0x38 + 8i, sync byte +0x28, bypass +0x29, enum Identifiers +0x2c/+0x30)
        self.ed = ed = e.malloc(0x100, "stand-in EffectData"); e.wr(ed, b"\0" * 0x100)
        self.holder = h = e.malloc(0x80, "stand-in SwitchableObject<EffectData,17>"); e.wr(h, b"\0" * 0x80)
        idxw = e.malloc(4); e.w32(idxw, 0); e.w32(h + 8, idxw); e.w32(h + 0x50, 0); e.w32(h + 0xc, ed)
        self.m = m = e.malloc(0x98, "new IFPM"); e.wr(m, b"\0" * 0x98)
        e.call(IFPM["ctor"], m, slot, 0, h, stack_args=(x.p,))
        self.ctor_fields = dict(proc=e.u32(m + 0x1c), holder=e.u32(m + 0x20), en=e.rd(m + 0x24, 1)[0], r25=e.rd(m + 0x25, 1)[0],
                                slot=e.u32(m + 0x3c), vptr=e.u32(m))
        self.hooks = {}
        self.n55 = 0
        e.add_watch(IFPM["s55"], lambda em: setattr(self, "n55", self.n55 + 1))

    def set_ed(self, vals):
        for i, v in enumerate(vals): self.e.w32(self.ed + 0x38 + 8 * i, f2u(v))
    def ed_bits(self): return [self.e.u32(self.ed + 0x38 + 8 * i) for i in range(6)]
    def set_type(self, t): self.x.set_fx_type(t)
    def pending(self): return s32(self.e.u32(self.x.p + 0xa8))
    def clear(self): self.x.s14.clear(); self.s54.clear(); self.setfx.clear()
    def log(self): return [(self.x.idx_of.get(o, hex(o)), s32(i), b) for _, o, i, b in self.x.s14]
    def s6(self, f, v): self.e.call(IFPM["s6"], self.m, 0, f & 0xffffffff, f2u(v))
    def s2(self, off, typ): self.e.call(IFPM["s2"], self.m, off, typ)
    def s10(self): self.e.call(IFPM["s10"], self.m, 0)
    def s27(self, v, sub): self.e.call(IFPM["s27"], self.m, f2u(v), sub)
    def s13(self, ident, amt): self.e.call(IFPM["s13"], self.m, ident, 0, f2u(amt))
    def hook_ret(self, addr, fn):
        """Replace the function at addr by a Python stand-in returning fn(emu)."""
        def h(em):
            em.setr(0, fn(em) & 0xffffffff); em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
        if addr in self.hooks: self.hooks[addr][0] = h
        else:
            box = [h]; self.hooks[addr] = box
            self.e.add_watch(addr, lambda em, box=box: box[0](em))


def c3_insert(Js, check, R):
    eff, sub = Js["eff"], Js["sub"]; meff, msub = Js["mod_eff"], Js["mod_sub"]
    rig = InsertRig(slot=0); e = rig.e; J = {"ctor": rig.ctor_fields, "s14_fns": [hex(a) for a in rig.s14_fns]}
    check(rig.ctor_fields["proc"] == rig.x.p and rig.ctor_fields["holder"] == rig.holder and rig.ctor_fields["en"] == 1
          and rig.ctor_fields["r25"] == 0 and rig.ctor_fields["vptr"] == VT["insert"],
          "real IFPM ctor 0x12864c: +0x1c = processor, +0x20 = holder, +0x24 enabled = 1, +0x25 = 0, vptr 0x84407c")
    # --- emulated table slots vs static bytes ---
    em_tab = {}
    for nm in ("s55", "s56"):
        em_tab[nm] = [s32(e.call(IFPM[nm], rig.m, i & 0xffffffff)[0]) for i in range(-4, 90)]
    exp55 = [eff[i] if 0 <= i < 72 else -1 for i in range(-4, 90)]; exp56 = [sub[i] if 0 <= i < 72 else -1 for i in range(-4, 90)]
    check(em_tab["s55"] == exp55 and em_tab["s56"] == exp56, "emulated IFPM s55/s56 over i = -4..89 equal the static bytes (-1 outside 0..71)")
    em57 = [s32(e.call(IFPM["s57"], rig.m, i)[0]) for i in range(0, 300)]; em58 = [s32(e.call(IFPM["s58"], rig.m, i)[0]) for i in range(0, 300)]
    check(all(em57[i] == (meff[i - 100] if 100 <= i <= 255 else -1) and em58[i] == (msub[i - 100] if 100 <= i <= 255 else -1)
              for i in range(300)), "emulated IFPM s57/s58 over ids 0..299 equal the static tables (ids 100..255)")
    rig.n55 = 0
    base = [0.11, 0.22, 0.33, 0.44, 0.55, 0.66]
    baseb = [f2u(v) for v in base]

    # ---------------- T1: lock path s6 -> s2(trigger) -> s10, every FxParamIndex x values, matching effect type -------------
    rows = []; t1_ok = 0; t1_n = 0
    for f in range(72):
        t = eff[f] if eff[f] >= 0 else 0
        rig.set_type(t); rig.set_ed(base)
        per = []
        for v in VALUES:
            rig.clear(); rig.s6(f, v); rig.s2(0, 15); rig.s10()
            got = rig.log()
            sb = sub[f]
            exp = [(t, k, (f2u(v) if k == sb else baseb[k])) for k in range(6)]
            ok = got == exp and rig.s54 == [(0,)]
            # -1 sub rows: the store goes to +0x7f / +0x64 (out of the 6-slot arrays), so no lock is applied
            t1_n += 1; t1_ok += ok
            per.append({"v": v, "ok": ok, "logged": [(a, b, "%08x" % c) for a, b, c in got] if not ok else None,
                        "lock_idx": sb, "lock_bits": "%08x" % f2u(v)})
            if sb < 0:   # clear the stray byte so later rows are not affected
                e.wr(rig.m + 0x7f, b"\0"); e.w32(rig.m + 0x64, 0)
        rows.append({"f": f, "type": t, "row_eff": eff[f], "sub": sub[f], "runs": per})
    J["t1"] = rows
    firstrow = {}
    for f in range(72):
        if eff[f] >= 0: firstrow.setdefault(eff[f], f)
    disc = sum(1 for r in rows if r["row_eff"] >= 0 and r["f"] - firstrow[r["row_eff"]] != r["sub"]
               for x in r["runs"] if x["ok"])
    J["t1_runs_refuting_group_offset"] = disc
    check(disc > 0, "T1 discriminates: %d logged runs put the lock at T_sub[f], not at FxParamIndex - group start" % disc)
    check(t1_ok == t1_n,"T1 lock path (real s6 -> s2(type 15) -> s10): %d/%d runs (72 rows x %d values) log exactly 6 slot-14 calls on "
          "the current effect: (sub, value bits) for sub = T_sub[f], ED base for the other 5; values unchanged incl. 1.5 / -0.25" %
          (t1_ok, t1_n, len(VALUES)))
    # stray writes of the -1 rows
    f_m1 = [f for f in range(72) if sub[f] < 0]
    rig.set_type(0); e.w32(rig.m + 0x64, 0); e.wr(rig.m + 0x7c, struct.pack("<f", 0.0))
    rig.s6(f_m1[0], 0.75)
    stray = (e.u32(rig.m + 0x64), e.rd(rig.m + 0x7f, 1)[0])
    check(stray == (f2u(0.75), 1), "s6 with a T_sub = -1 row (FxParamIndex %d) writes +0x64 = value and byte +0x7f = 1 (index -1 of the "
          "+0x68 / +0x80 arrays)" % f_m1[0])
    # quirk: a -1 row after a sub-5 lock corrupts the sub-5 value's top byte
    f5 = next(f for f in range(72) if sub[f] == 5 and eff[f] == 0)
    rig.set_ed(base); rig.clear(); rig.s6(f5, 1.0); rig.s6(f_m1[0], 0.5); rig.s2(0, 15); rig.s10()
    q = rig.log()
    J["quirk_m1_after_sub5"] = [(a, b, "%08x" % c) for a, b, c in q]
    check(q and q[5] == (0, 5, 0x01800000), "quirk: lock FxParamIndex %d (sub 5) = 1.0, then a -1 row -> slot 14(5) receives 0x01800000 "
          "(%.3g) instead of 1.0" % (f5, u2f(0x01800000)))
    e.wr(rig.m + 0x7f, b"\0"); e.w32(rig.m + 0x64, 0)
    # no trigger -> no apply; trigger type other than 11/15 -> +0x86 still set (apply happens), processor s54 not called
    rig.set_ed(base); rig.clear(); rig.s6(0, 0.9); rig.s10()
    nolog = rig.log()
    rig.clear(); rig.s2(0, 8); rig.s10()
    t8 = rig.log(); s54_8 = list(rig.s54)
    check(nolog == [] and t8 and t8[0] == (0, 0, f2u(0.9)) and s54_8 == [],
          "a lock is held until a trigger: s6 then s10 alone -> 0 slot-14 calls; s2(type 8) then s10 -> applied (processor s54 only for 11/15)")
    # ---------------- T2: mismatched effect type -------------
    mm = []
    for f in (0, 5, 23, 29, 35, 41, 46, 50, 61, 67, 71):
        u = (eff[f] + 3) % 10
        rig.set_type(u); rig.set_ed(base); rig.clear(); rig.s6(f, 0.875); rig.s2(0, 15); rig.s10()
        got = rig.log()
        mm.append({"f": f, "row_eff": eff[f], "current": u, "logged": [(a, b, "%08x" % c) for a, b, c in got]})
        ok = got == [(u, k, f2u(0.875) if k == sub[f] else baseb[k]) for k in range(6)]
        mm[-1]["ok"] = ok
    J["t2"] = mm
    check(all(r["ok"] for r in mm), "T2 mismatched type: 11/11 locks of another effect's FxParamIndex are applied to the CURRENT effect's "
          "sub-slot T_sub[f] (no effect-type check on the lock path) -> alternative 'manager filters by T_eff' refuted")
    # ---------------- T3: UI/edit path s27(value, sub) -> s10 -------------
    t3 = []; t3_ok = 0
    for t in range(10):
        rig.set_type(t)
        for k in range(6):
            for v in VALUES:
                rig.set_ed(base); rig.clear(); rig.s27(v, k)
                pre = rig.log(); edv = rig.ed_bits()[k]
                rig.s10(); got = rig.log()
                ok = pre == [] and edv == f2u(v) and got == [(t, k, f2u(v))]
                t3_ok += ok
                if not ok: t3.append({"t": t, "k": k, "v": v, "pre": pre, "got": got})
    J["t3_fail"] = t3
    check(t3_ok == 10 * 6 * len(VALUES), "T3 edit path (real s27 -> s10): %d/%d: s27 stores ED+0x38+8k = value and sets flag +0x8c+k; "
          "the next s10 makes exactly one slot-14 call (k, value) on the current effect, bit-exact" % (t3_ok, 10 * 6 * len(VALUES)))
    # disabled manager (+0x24 = 0): s27 ignored, s10 returns at once
    e.wr(rig.m + 0x24, b"\0"); rig.set_ed(base); rig.clear(); rig.s27(0.9, 0); rig.s6(0, 0.9); rig.s2(0, 15); rig.s10()
    dis = (rig.log(), rig.ed_bits()[0])
    e.wr(rig.m + 0x24, b"\1"); e.wr(rig.m + 0x80, b"\0" * 7)
    check(dis == ([], baseb[0]), "with +0x24 = 0 (slots 20/22/24 clear it) s27 stores nothing and s10 sends nothing")
    # ---------------- T4: modulation path s13(id, amount) -> s10 -------------
    t4 = {"n": 0, "ok": 0, "fail": [], "mismatch_calls": 0, "slot_mismatch_calls": 0}
    amts = [-1.0, -0.3, 0.0, 0.3, 0.45, 1.0]
    LOW = u2f(e.u32(0x12aa40 + 8 + 0x150)); J["mod_low_clamp_literal"] = LOW
    for ident in range(100, 156):
        te, ks = meff[ident - 100], msub[ident - 100]
        if te < 0: continue
        rig.set_type(te); rig.set_ed(base)
        rig.clear(); rig.s27(base[ks], ks); rig.s10()          # establishes +0x44[ks] (applied base)
        for a in amts:
            rig.clear(); rig.s13(ident, a); rig.s10(); got = rig.log()
            s = u2f(f2u(base[ks])) + u2f(f2u(a)); s = u2f(f2u(s))
            s = LOW if s < 0 else (1.0 if s > 1.0 else s)
            ok = got == [(te, ks, f2u(s))]
            t4["n"] += 1; t4["ok"] += ok
            if not ok: t4["fail"].append((ident, a, got))
        # mismatched type: no call
        rig.set_type((te + 1) % 10); rig.clear(); rig.s13(ident, 0.3); rig.s10(); t4["mismatch_calls"] += len(rig.log())
        # id of the other slot (200+): manager slot 0 ignores it
        rig.set_type(te); rig.clear(); rig.s13(ident + 100, 0.3); rig.s10(); t4["slot_mismatch_calls"] += len(rig.log())
    rig.s13(0, 0.0)
    J["t4"] = t4
    J["s55_entries_T1_T4"] = rig.n55
    check(rig.n55 == 0, "IFPM s55 (FxParamIndex -> effect) was entered %d times during T1-T4 (lock, mismatch, edit, modulation paths)" % rig.n55)
    check(t4["ok"] == t4["n"] and t4["mismatch_calls"] == 0 and t4["slot_mismatch_calls"] == 0,
          "T4 modulation (real s13 -> s10): %d/%d: slot 14(s58(id), clamp01(f32(base + amount))) on the current effect every s10; "
          "0 calls when s57(id) != current type; 0 calls for ids 200-255 in the slot-0 manager" % (t4["ok"], t4["n"]))
    # ---------------- T5: reload path (s51 -> +0x25) with s52 / enum converters as stand-ins -------------
    conv_slots = {60: 0x11e138, 62: 0x11e9ac, 64: 0x11d038, 66: 0x11df88, 68: 0x11d940, 70: 0x11d818, 72: 0x11d6f0, 74: 0x11f3f4}
    for k, a in conv_slots.items():
        assert e.u32(VT["insert"] + 4 * k) == a
    t5 = {}
    for t in range(10):
        rig.hook_ret(IFPM["s52"], lambda em, t=t: t)
        for n_, (k, a) in enumerate(conv_slots.items()):
            rig.hook_ret(a, lambda em, n_=n_: 2 + n_)          # converter slot 60+2n -> int 2+n (stand-in)
        rig.set_ed(base); e.wr(rig.ed + 0x28, b"\1")
        rig.set_type((t + 5) % 10); rig.clear()
        e.call(IFPM["s51"], rig.m, 0); rig.s10()
        got = rig.log(); sf = list(rig.setfx)
        t5[t] = {"setFxType": sf, "calls": [(a_, b_, "%08x" % c_) for a_, b_, c_ in got]}
    J["t5"] = t5
    six_ok = all(t5[t]["setFxType"] == [t] and [(a, b) for a, b, _ in t5[t]["calls"][:6]] == [(t, k) for k in range(6)]
                 and [c for _, _, c in t5[t]["calls"][:6]] == ["%08x" % b for b in baseb] for t in range(10))
    check(six_ok, "T5 reload (real s51(0) -> s10, s52 stand-in): setFxType(type) then slot 14(k, ED[k]) for k = 0..5 on that effect, bit-exact")
    extras = {t: [(b, c) for _, b, c in t5[t]["calls"][6:]] for t in range(10)}
    J["t5_extras"] = extras
    exp_extra = {0: [(6, f2u(1.0))], 1: [(6, f2u(1.0))], 4: [(6, f2u(1.0))], 8: [(6, f2u(1.0))],
                 2: [(6, f2u(2.0)), (7, f2u(2.0))], 3: [(6, f2u(3.0)), (7, f2u(4.0))], 5: [(6, f2u(5.0)), (7, f2u(6.0))],
                 7: [(7, f2u(8.0)), (8, f2u(7.0))], 9: [(6, f2u(1.0)), (10, f2u(9.0))], 6: []}
    check(all(extras[t] == [(i, "%08x" % b) for i, b in exp_extra[t]] for t in range(10)),
          "T5 extras after the 6 floats: SYNC byte ED+0x28 -> index 6 as float(byte) for Chorus/Flanger/Delay/Phaser/Ducker; enum Identifiers "
          "ED+0x2c/+0x30 -> float(converter) for PEQ 6/7 (s60), MMF 6 (s62) / 7 (s64), LoFi 6 (s66) / 7 (s68), Compressor 7 Knee (s72) / "
          "8 LevelDetect (s70), Ducker 10 SOURCE (s74); Distortion none")
    e.wr(rig.ed + 0x28, b"\0")
    # ---------------- T6: s36 (sync byte) -------------
    t6 = {}
    for t in range(10):
        rig.set_type(t); rig.clear(); e.call(IFPM["s36"], rig.m, 1); t6[t] = rig.log()
    J["t6"] = {t: [(a, b, "%08x" % c) for a, b, c in v] for t, v in t6.items()}
    check(all(t6[t] == ([(7, 6, f2u(1.0))] if t == 7 else []) for t in range(10)) and e.rd(rig.ed + 0x28, 1)[0] == 1,
          "s36(byte) stores ED+0x28 and sends slot 14 only for the Compressor (index 6 LookAhead = float(byte)); other types wait for s34/reload")
    # ---------------- T7: s34 (SYNC toggle, H075) -------------
    t7 = {}
    for t in range(10):
        for sync in (1, 0):
            rig.set_type(t); rig.set_ed([0.5, 0.22, 0.5, 0.44, 0.55, 0.66]); rig.clear(); rig.x.bpm = 120.0
            e.call(0x126c90, rig.m, sync)
            got = rig.log(); edb = rig.ed_bits()
            t7["%d/%d" % (t, sync)] = {"calls": [(a, b, "%08x" % c, round(u2f(c), 7)) for a, b, c in got],
                                       "ed": [round(u2f(x), 7) for x in edb], "ed28": e.rd(rig.ed + 0x28, 1)[0]}
    J["t7"] = t7
    types_with_calls = sorted(set(int(k.split("/")[0]) for k, v in t7.items() if v["calls"]))
    idx_used = sorted(set(b for v in t7.values() for _, b, _, _ in v["calls"]))
    ed_match = all(all(v["ed"][b] == c4 for a, b, c, c4 in v["calls"] if b <= 5) for v in t7.values())
    check(types_with_calls == [0, 1, 4, 8, 9] and set(idx_used) <= {0, 2, 6} and ed_match
          and all(v["ed28"] == int(k.split("/")[1]) for k, v in t7.items()),
          "T7 s34(sync) (H075): stores ED+0x28; only Chorus/Flanger/Delay/Phaser/Ducker get slot-14 calls, indices %s; every re-mapped "
          "time value is also written back to ED (sub 0, Ducker 0 and 2)" % idx_used)
    # ---------------- T8: s50 per-sub-slot descriptor (H075) -------------
    t8 = {}
    sret = e.malloc(16)
    for t in range(10):
        rig.set_type(t)
        for k in range(7):
            e.wr(sret, b"\xee" * 8); e.call(0x126458, sret, rig.m, k)
            lo_, hi_ = struct.unpack("<ii", e.rd(sret, 8)); t8["%d/%d" % (t, k)] = (lo_, hi_)
    J["t8"] = t8
    check(all(t8["%d/6" % t] == t8["%d/6" % 0] for t in range(10)),
          "T8 s50(sret, mgr, sub) returns an 8-byte pair per (current type, sub 0..5); sub 6 -> the default pair %s for every type" % (t8["0/6"],))
    R["insert_rig"] = rig
    return J


# ===================================================================================================================== C4 Master/Send
def c4_master_send(check):
    import H077_master_send_proc as H77
    J = {}
    for which in ("master", "send"):
        x = H77.EmuProc(which); e = x.e
        ed = e.malloc(0x100); e.wr(ed, b"\0" * 0x100)
        h = e.malloc(0x80); e.wr(h, b"\0" * 0x80); iw = e.malloc(4); e.w32(iw, 0); e.w32(h + 8, iw); e.w32(h + 0x50, 0); e.w32(h + 0xc, ed)
        m = e.malloc(0x100); e.wr(m, b"\0" * 0x100); e.w32(m, VT[which]); e.w32(m + 0x1c, x.p); e.w32(m + 0x20, h); e.wr(m + 0x24, b"\1")
        n = ok = 0; fails = []
        for t in range(10):
            x.set_fx_type(t)
            for k in range(6):
                for v in (0.3, 1.0, 1.25, -0.5):
                    x.s14.clear(); e.call(BASE_S27, m, f2u(v), k)
                    got = [(x.idx_of.get(o), s32(i), b) for _, o, i, b in x.s14]
                    good = got == [(t, k, f2u(v))] and e.u32(ed + 0x38 + 8 * k) == f2u(v)
                    n += 1; ok += good
                    if not good: fails.append((t, k, v, got))
        # inert slots on the real vtable
        x.s14.clear(); rets = {}
        for k in (6, 10, 55, 56, 57, 58):
            rets[k] = s32(e.call(e.u32(VT[which] + 4 * k), m, 3, 4, f2u(0.5))[0])
        inert = (x.s14 == [] and all(rets[k] == 0 for k in (55, 56, 57, 58)))
        J[which] = {"n": n, "ok": ok, "fails": fails[:10], "inert_rets": rets, "inert": inert}
        check(ok == n, "%s: base slot 27 0x11ce58(value, k) -> ED+0x38+8k = value and IMMEDIATELY slot 14(k, value) on the pending effect: "
              "%d/%d (10 types x 6 k x 4 values incl. 1.25/-0.5), bit-exact, no s10 needed" % (which, ok, n))
        check(inert, "%s: real vtable slots 6/10 (no-op) and 55-58 (return 0) send no slot-14 call" % which)
    return J


# ===================================================================================================================== C5 alternatives + table
def alternatives(Js, J3, check):
    eff, sub = Js["eff"], Js["sub"]; meff, msub = Js["mod_eff"], Js["mod_sub"]
    # group-offset model: idx = f - first row of the group
    first = {}
    for f in range(72):
        if eff[f] >= 0 and eff[f] not in first: first[eff[f]] = f
    grp = sum(1 for f in range(72) if eff[f] >= 0 and f - first[eff[f]] != sub[f])
    check(grp > 0, "alternative 'slot-14 index = FxParamIndex - group start' refuted: %d valid rows differ (e.g. Chorus 4 -> 5, Ducker 67 -> 2)" % grp)
    # modulation id = 100 + FxParamIndex ?
    same = sum(1 for k in range(56) if k < 72 and (meff[k], msub[k]) == (eff[k], sub[k]))
    pairs_f = {(eff[f], sub[f]): f for f in range(72) if eff[f] >= 0}
    pairs_m = {(meff[k], msub[k]): 100 + k for k in range(56) if meff[k] >= 0}
    check(same < 56 and set(pairs_m) <= set(pairs_f),
          "alternative 'modulation id = 100 + FxParamIndex' refuted (%d/56 ids agree); every modulation (effect, sub) pair is also a "
          "FxParamIndex pair (%d of %d)" % (same, len(pairs_m), len(pairs_f)))
    return {"group_offset_mismatches": grp, "mod_same_as_f": same, "fx_pairs_without_mod_id": sorted(
        [pairs_f[p] for p in set(pairs_f) - set(pairs_m)])}


def mapping_table(Js):
    eff, sub = Js["eff"], Js["sub"]; meff, msub = Js["mod_eff"], Js["mod_sub"]
    mod_of = {(meff[k], msub[k]): 100 + k for k in range(56) if meff[k] >= 0}
    rows = []
    for f in range(72):
        t, k = eff[f], sub[f]
        rows.append({"f": f, "eff": t, "class": INS_NAMES[t] if t >= 0 else "-", "s14": k,
                     "name": P[t].get(k, "?") if t >= 0 and k >= 0 else "-", "mod_id": mod_of.get((t, k)) if t >= 0 else None})
    return rows


# ===================================================================================================================== main
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H004"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; fails = []; J = {}
    def Pr(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        Pr("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = Image()
    Pr("== C1/C2 static (target sha %s)" % im_sha(im))
    Js = static_part(im, P, check); J["static"] = Js
    rows = mapping_table(Js); J["map"] = rows
    eff, sub = Js["eff"], Js["sub"]
    m1_eff = [f for f in range(72) if eff[f] < 0]; m1_sub = [f for f in range(72) if sub[f] < 0]
    pairs = [(eff[f], sub[f]) for f in range(72) if eff[f] >= 0 and sub[f] >= 0]
    dup = len(pairs) - len(set(pairs))
    Pr("  rows with T_eff = -1: %d %s; rows with T_sub = -1: %d %s; rows with T_eff = -1 but T_sub >= 0: %s" % (
        len(m1_eff), m1_eff, len(m1_sub), m1_sub, [f for f in m1_eff if sub[f] >= 0]))
    check(dup == 0 and len(pairs) == 55, "one-to-one: %d valid rows map to %d distinct (effect, slot-14 index) pairs, %d duplicates" %
          (len(pairs), len(set(pairs)), dup))
    per = {t: sorted(sub[f] for f in range(72) if eff[f] == t) for t in range(10)}
    Pr("  slot-14 indices reachable per Insert effect via FxParamIndex: %s" % {INS_NAMES[t]: v for t, v in per.items()})
    for w in ("insert_s10", "insert_s38", "master_s38", "send_s38"):
        Pr("  %s 0x112924 sites (site, effect, idx, source): %s" % (w, Js["c2_sites"][w]))
    Pr("== C3 Insert emulation"); R = {}
    J["c3"] = c3_insert(Js, check, R)
    t8 = J["c3"]["t8"]
    for r in rows:
        r["ui_pair"] = t8.get("%d/%d" % (r["eff"], r["s14"])) if r["eff"] >= 0 and r["s14"] >= 0 else None
    Pr("  T7 s34 calls (type/sync: [(effect, idx, value)]): %s" % {k: [(a, b, c4) for a, b, _, c4 in v["calls"]]
                                                                    for k, v in J["c3"]["t7"].items() if v["calls"]})
    Pr("  T8 s50 pairs (type: [sub0..sub5]): %s" % {t: [t8["%d/%d" % (t, k)] for k in range(6)] for t in range(10)})
    Pr("== C4 Master/Send emulation")
    J["c4"] = c4_master_send(check)
    Pr("== C5 alternatives")
    J["c5"] = alternatives(Js, J["c3"], check)
    Pr("== derived 72-row map: f | T_eff | class | slot-14 idx | parameter | modulation id | s50 pair")
    for r in rows:
        Pr("  %2d | %2d | %-19s | %2d | %-22s | %-4s | %s" % (r["f"], r["eff"], r["class"], r["s14"], r["name"], r["mod_id"], r["ui_pair"]))
    Pr("RESULT: %d failed checks" % len(fails))
    J.pop("insert_rig", None)
    blob = json.dumps(J, sort_keys=True, default=str, indent=1).encode()
    open(os.path.join(a.out, "h004.json"), "wb").write(blob)
    tab = "\n".join("%d,%d,%s,%d,%s,%s,%s" % (r["f"], r["eff"], r["class"], r["s14"], r["name"], r["mod_id"], "%d:%d" % tuple(r["ui_pair"]) if r["ui_pair"] else "-") for r in rows).encode()
    open(os.path.join(a.out, "fxparam_map.csv"), "wb").write(b"f,eff,class,s14,name,mod_id,s50_lo:hi\n" + tab + b"\n")
    txt = "\n".join(rep).encode(); open(os.path.join(a.out, "h004_report.txt"), "wb").write(txt)
    print("sha256 h004.json %s\nsha256 fxparam_map.csv %s\nsha256 h004_report.txt %s" % (
        sha(blob), sha(b"f,eff,class,s14,name,mod_id,s50_lo:hi\n" + tab + b"\n"), sha(txt)))
    return 1 if fails else 0


def im_sha(im): return sha(im.data)[:12]


if __name__ == "__main__":
    sys.exit(main())
