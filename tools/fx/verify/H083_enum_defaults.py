#!/usr/bin/env python3
"""H083 — FX parameter-manager enum name-converters (manager vtable slots 59-74) and the default prj::EffectData.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: Pioneer bytes are read at run time and
never stored; outputs are our own derived numbers and the name strings the converters compare against. Emulation is guest memory
only; nothing is written outside --out and no image is built.

Sections (criteria of kb/cycles/030.md):
  C1 converters. Static: the four manager vtables (base 0x8430cc, Insert 0x84407c, Master 0x8437ec, Send 0x8446d4) share slots 59-74;
     a pattern decoder reads each even slot (name -> int: function-static juce::Identifier built from a C string by 0x666e84, copied by
     0x627ba0, pointer-compared with the argument, then `beq`/`moveq`/`adc` to a constant) and gives the name -> int map + default;
     a site scan finds which (effect, slot-14 index) each converter feeds in Insert s10 / s38, Master/Send s51 / s38.
     Emulation: REAL juce::Identifier(const char*) 0x666e84 (real JUCE StringPool, pthread mutex stubbed), REAL even slots on every
     listed name + unknown names, REAL odd slots (int -> name) over ints -3..20, round trip.
  C2 EffectData defaults. REAL prj::EffectData ctor 0x359d1c(this, juce::String name, Config) (callers: TrackData-side 0x35cb30
     "InsertFx"+n, PatternData 0x35de70 "SendFx" / "MasterFx"); fields read back. REAL manager slot 32 (applyFxType: Insert 0x1287d4,
     Master 0x1237cc, Send 0x12bc84) on a REAL processor (H077 EmuProc) + REAL manager ctor: EffectData after each type.
  C3 end-to-end. REAL s51 -> (Insert) s10 with the REAL converters and REAL s52 on (a) the ctor-default EffectData and (b) the
     EffectData written by s32 for every type; slot-14 calls logged and compared with the processor's slot-52 defaults.
Stand-ins (declared): SwitchableObject<EffectData,17> holder (+8 -> index word 0, +0x50 = 0, +0xc -> EffectData; layout from the
operator-> code in s10/s32), Config argument of the EffectData ctor (never read: zero block), Insert processor slot 54 0x11684c
(Ducker trigger hook) skipped if reached; __cxa_guard_acquire/release (ARM EABI guard bit 0), pthread mutex functions (no-op).
Run: .venv/bin/python -B harness/H083_enum_defaults.py --out DIR
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


def _guard_acq(e):
    g = e.r(0); e.setr(0, 0 if e.u32(g) & 1 else 1)


def _guard_rel(e):
    e.w32(e.r(0), 1)


emu.STUBS.setdefault("__cxa_guard_acquire", (_guard_acq, "H083 stub: ARM EABI guard, returns 1 iff bit 0 clear"))
emu.STUBS.setdefault("__cxa_guard_release", (_guard_rel, "H083 stub: sets guard bit 0"))
for _nm in ("pthread_mutex_lock", "pthread_mutex_unlock", "pthread_mutex_init", "pthread_mutex_destroy", "pthread_mutexattr_init",
            "pthread_mutexattr_settype", "pthread_mutexattr_destroy", "pthread_mutexattr_setprotocol"):
    emu.STUBS.setdefault(_nm, (lambda e: e.setr(0, 0), "H083 stub: no-op, returns 0"))
emu.STUBS.setdefault("pthread_self", (lambda e: e.setr(0, 1), "H083 stub: returns 1"))

import H077_master_send_proc as H77                            # noqa: E402  (adds its own pthread stubs with setdefault)

# ------------------------------------------------------------------------------------------------------------------ addresses (1.60)
VT = {"base": 0x8430cc, "insert": 0x84407c, "master": 0x8437ec, "send": 0x8446d4}
ID_CTOR, ID_COPY, ID_DTOR = 0x666e84, 0x627ba0, 0x6280c8       # juce::Identifier(const char*), copy ctor, dtor
STR_CTOR = 0x64a3fc                                            # juce::String(const char*)
ED_CTOR, ED_DTOR, ED_VT, ED_SIZE = 0x359d1c, 0x371578, 0x8ac720, 0x64
EMPTY_TEXT = 0xaa8988                                          # juce empty-string text (Identifier of "" / null)
MGR = {"insert": dict(ctor=0x12864c, s10=0x129b34, s32=0x1287d4, s38=0x127928, s51=0x126394, s52=0x12802c, s53=0x1262b0),
       "master": dict(ctor=0x1260f0, s10=None, s32=0x1237cc, s38=0x1232fc, s51=0x121174, s52=0x125b70, s53=0x1201e8),
       "send": dict(ctor=0x130bd4, s10=None, s32=0x12bc84, s38=0x130000, s51=0x12de8c, s52=0x130668, s53=0x12acf0)}
SETIDX = 0x112924                                              # FxProcessorBase (proc, effect, idx, value) -> array[effect] slot 14
PROC_S54_INSERT = 0x11684c
# even (name -> int) / odd (int -> name) slot pairs and their meaning (effect names: F018/F019 order)
PAIRS = {60: (59, "PEQ band type"), 62: (61, "MMF FILTERTYPE"), 64: (63, "MMF FILTERDB (order)"), 66: (65, "LoFi FILTERTYPE"),
         68: (67, "LoFi FILTERPOSITION"), 70: (69, "Compressor LevelDetect"), 72: (71, "Compressor Knee"), 74: (73, "Ducker SOURCE")}
INS_NAMES = ["Chorus", "Flanger", "PEQ", "MMF", "InsertFxDelay", "LoFi", "Distortion", "InsertFxCompressor", "Phaser", "Ducker"]
MS_NAMES = ["SendFxDelay", "SendFxReverb", "Chorus", "Flanger", "PEQ", "MMF", "LoFi", "SendFxCompressor", "Distortion", "Phaser"]
UNKNOWN = ["", "Bogus", "None", "Off", "FilterTypeoff", "SourceTrack0", "SourceTrack17"]


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u & 0x80000000 else u


# ===================================================================================================================== C1 static
def _lit(im, ins):
    m = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", ins.op_str)
    if ins.mnemonic in ("ldr", "ldrne", "ldreq") and m:
        return m.group(1), im.u32(ins.address + 8 + int(m.group(2), 0))
    return None, None


def _static_names(im, ins):
    """{static Identifier address: C string} from `ldr r0,=G ; ldr r1,="s" ; bl 0x666e84` (any order within 3 instructions)."""
    G = {}
    for k, i in enumerate(ins):
        if i.mnemonic == "bl" and i.op_str == "#0x%x" % ID_CTOR:
            r = {}
            for j in range(k - 1, max(k - 4, -1), -1):
                reg, v = _lit(im, ins[j])
                if reg in ("r0", "r1") and reg not in r: r[reg] = v
            if "r0" in r and "r1" in r: G[r["r0"]] = im.cstr(r["r1"], 64)
    return G


def decode_name2int(im, fn):
    """Pattern decoder for an even slot: returns (ordered [(name, value, form)], default, helper map)."""
    s, e = im.func_of(fn); ins = im.disasm(s, e)
    G = _static_names(im, ins)
    helper = {}
    for i in ins:                                              # helpers returning a function-static Identifier (Ducker 10..16)
        if i.mnemonic == "bl":
            t = int(i.op_str[1:], 16)
            if t in (ID_CTOR, ID_COPY, ID_DTOR) or t < 0x11c000 or t > 0x121000: continue
            hs, he = im.func_of(t)
            if hs != t: continue
            hins = im.disasm(hs, he); HG = _static_names(im, hins)
            if len(HG) == 1: helper[t] = next(iter(HG.items()))
    at = {i.address: k for k, i in enumerate(ins)}
    def ret_at(a):
        for _ in range(4):
            x = ins[at[a]]
            m = re.match(r"r0, #(0x[0-9a-f]+|\d+)$", x.op_str)
            if x.mnemonic == "mov" and m: return int(m.group(1), 0)
            if x.mnemonic == "b": a = int(x.op_str[1:], 16); continue
            return None
    copies = []
    for k, i in enumerate(ins):
        if i.mnemonic == "bl" and i.op_str == "#0x%x" % ID_COPY:
            src = None
            for j in range(k - 1, max(k - 4, -1), -1):
                reg, v = _lit(im, ins[j])
                if reg == "r1": src = G.get(v); break
                if ins[j].mnemonic == "mov" and ins[j].op_str == "r1, r0" and ins[j - 1].mnemonic == "bl":
                    src = helper.get(int(ins[j - 1].op_str[1:], 16), (None, None))[1]; break
            copies.append((k, src))
    out = []; default = None
    for n, (k, name) in enumerate(copies):
        end = copies[n + 1][0] if n + 1 < len(copies) else len(ins)
        val = form = None
        for j in range(k + 1, min(end, k + 14)):
            x = ins[j]
            if x.mnemonic == "cmp":
                y = ins[j + 1]
                z2 = ins[j + 2]
                imm = lambda q: int(q.op_str.split("#")[1], 0)
                if y.mnemonic == "beq": val, form = ret_at(int(y.op_str[1:], 16)), "beq"
                elif y.mnemonic == "moveq": val, form = imm(y), "moveq"
                elif y.mnemonic == "movne" and z2.mnemonic == "moveq": val, form, default = imm(z2), "movne/moveq", imm(y)
                if form == "moveq" and z2.mnemonic == "movne": default = imm(z2)
                if form == "beq":                         # fall-through: first `mov r0,#v` after the branch in layout order
                    for z in ins[j + 2:j + 40]:
                        m = re.match(r"r0, #(0x[0-9a-f]+|\d+)$", z.op_str)
                        if z.mnemonic == "mov" and m: default = int(m.group(1), 0); break
                        if z.mnemonic == "rsbs": default = 0; break
                        if z.mnemonic == "bl" and z.op_str == "#0x%x" % ID_COPY: default = None; break
                break
            if x.mnemonic == "rsbs" and ins[j + 1].mnemonic == "adc":
                val, form, default = 1, "eq->1 (rsbs/adc)", 0; break
            m = re.match(r"r0, #(0x[0-9a-f]+|\d+)$", x.op_str)
            if x.mnemonic == "mov" and m:
                val, form = int(m.group(1), 0), "merged with default"; default = val; break
        out.append((name, val, form))
    return out, default, sorted(set(G.values()) | set(v[1] for v in helper.values()))


def feed_sites(im, fn):
    """Even-slot converter vcalls (`ldr rX,[rY,#0xf0..0x128]` then `blx rX`) in fn; from the blx, follow straight-line code and
    unconditional `b` (shared tails) to the next 0x112924(proc, effect, idx, v) call; effect/idx = the last `mov r1/r2,#` on that
    walk (r1-r3 are clobbered by the converter, so they must be set after it). Source = the `add r1, rX, #0x2c/#0x30` before blx."""
    s, e = im.func_of(fn); ins = im.disasm(s, e); at = {i.address: k for k, i in enumerate(ins)}; res = []
    for k, i in enumerate(ins):
        m = re.match(r"(\w+), \[(\w+), #(0x[0-9a-f]+)\]$", i.op_str)
        if not (i.mnemonic == "ldr" and m and int(m.group(3), 16) in range(0xf0, 0x12c, 8)): continue
        reg = m.group(1); slot = int(m.group(3), 16) // 4
        kb = next((j for j in range(k + 1, min(k + 40, len(ins))) if ins[j].mnemonic == "blx" and ins[j].op_str == reg), None)
        if kb is None: continue
        src = None
        for z in ins[k:kb]:
            mm = re.match(r"r1, r\d+, #(0x2c|0x30)$", z.op_str)
            if z.mnemonic == "add" and mm: src = "ED+" + mm.group(1)
        r1 = r2 = None; j = kb + 1; steps = 0; done = False
        while j < len(ins) and steps < 60 and not done:
            z = ins[j]; steps += 1
            if z.mnemonic == "mov" and z.op_str.startswith("r1, #"): r1 = int(z.op_str[5:], 0)
            if z.mnemonic == "mov" and z.op_str.startswith("r2, #"): r2 = int(z.op_str[5:], 0)
            if z.mnemonic == "mov" and z.op_str == "r2, r1": r2 = r1
            if z.mnemonic == "bl" and z.op_str == "#0x%x" % SETIDX:
                res.append((hex(i.address), slot, r1, r2, src)); done = True; break
            if z.mnemonic == "b":
                t = int(z.op_str[1:], 16)
                if t not in at: break
                j = at[t]; continue
            if z.mnemonic in ("bl", "blx", "pop", "bx"): break
            j += 1
        if not done: res.append((hex(i.address), slot, None, None, src))
    return res


# ===================================================================================================================== emulation rigs
class Juce:
    """Real JUCE Identifier / String objects in a guest."""
    def __init__(self, e): self.e = e
    def cstr(self, s):
        c = self.e.malloc(len(s) + 1); self.e.wr(c, s.encode() + b"\0"); return c
    def ident(self, s):
        d = self.e.malloc(4); self.e.call(ID_CTOR, d, self.cstr(s)); return d
    def string(self, s):
        d = self.e.malloc(4); self.e.call(STR_CTOR, d, self.cstr(s)); return d
    def text(self, p):
        if p == 0: return None
        return self.e.rd(p, 80).split(b"\0")[0].decode("latin1")
    def name_at(self, a): return self.text(self.e.u32(a))


def read_ed(e, J, ed):
    return {"vt": hex(e.u32(ed)), "node_name": J.name_at(ed + 8), "type": J.name_at(ed + 0x24), "b28_sync": e.rd(ed + 0x28, 1)[0],
            "b29": e.rd(ed + 0x29, 1)[0], "id2c": J.name_at(ed + 0x2c), "id30": J.name_at(ed + 0x30),
            "params": [(J.name_at(ed + 0x34 + 8 * k), "%08x" % e.u32(ed + 0x38 + 8 * k)) for k in range(6)]}


class Rig:
    """REAL processor (H077 EmuProc) + REAL manager ctor + REAL EffectData ctor; stand-in holder."""
    def __init__(self, which, node="InsertFx0"):
        self.which = which; M = MGR[which]; self.M = M
        self.x = x = H77.EmuProc(which); e = self.e = x.e; self.J = J = Juce(e)
        for a in sorted(set(e.u32(e.u32(o) + 0x38) for o in x.objs)):
            if a not in H77.SLOT14:
                e.add_watch(a, lambda em: x.s14.append(("other@0x%x" % em.uc.reg_read(emu.LR), em.r(0), em.r(1), em.r(2))))
        self.s54 = []
        if which == "insert":
            def skip54(em):
                self.s54.append(em.r(1)); em.uc.reg_write(emu.PC, em.uc.reg_read(emu.LR))
            e.add_watch(PROC_S54_INSERT, skip54)
        self.setfx = []
        e.add_watch(H77.PROC[which]["setfx"], lambda em: self.setfx.append(s32(em.r(1))))
        cfg = e.malloc(0x200, "stand-in prj::Config (not read)"); e.wr(cfg, b"\0" * 0x200)
        self.ed = ed = e.malloc(ED_SIZE, "new(0x64) prj::EffectData"); e.wr(ed, b"\xcc" * ED_SIZE)
        e.call(ED_CTOR, ed, J.string(node), cfg)
        self.ed_ctor = read_ed(e, J, ed)
        self.h = h = e.malloc(0x80, "stand-in SwitchableObject<EffectData,17>"); e.wr(h, b"\0" * 0x80)
        iw = e.malloc(4); e.w32(iw, 0); e.w32(h + 8, iw); e.w32(h + 0x50, 0); e.w32(h + 0xc, ed)
        self.m = m = e.malloc(0x100, "new manager"); e.wr(m, b"\0" * 0x100)
        if which == "insert": e.call(M["ctor"], m, 0, 0, h, stack_args=(x.p,))
        else: e.call(M["ctor"], m, h, x.p)
        self.ctor_fields = dict(vptr=hex(e.u32(m)), proc=e.u32(m + 0x1c) == x.p, holder=e.u32(m + 0x20) == h, en=e.rd(m + 0x24, 1)[0],
                                r30=e.u32(m + 0x30))
    def s14_log(self):
        return [(self.x.idx_of.get(o, hex(o)), s32(i), "%08x" % b) for _, o, i, b in self.x.s14]
    def clear(self): self.x.s14.clear(); self.setfx.clear(); self.s54.clear()
    def reload(self):
        """s51(0) then (Insert) s10: the per-block update that applies the reload flag."""
        e = self.e; e.call(self.M["s51"], self.m, 0)
        if self.M["s10"]: e.call(self.M["s10"], self.m, 0)
    def effect_id_for(self):
        """{effect index: smallest effectId with s53(effectId) == index} (emulated s53)."""
        r = {}
        for eid in range(0, 64):
            t = s32(self.e.call(self.M["s53"], self.m, eid)[0])
            if t >= 0 and t not in r: r[t] = eid
        return r


# ===================================================================================================================== C1
def c1(im, check):
    J1 = {}
    same = all(im.u32(VT[w] + 4 * k) == im.u32(VT["base"] + 4 * k) for w in VT for k in range(59, 75))
    J1["slots"] = {k: hex(im.u32(VT["base"] + 4 * k)) for k in range(59, 75)}
    check(same, "vtables base 0x8430cc / Insert 0x84407c / Master 0x8437ec / Send 0x8446d4 share slots 59-74 (one converter set "
          "for all three managers): %s" % J1["slots"])
    stat = {}
    for ev in PAIRS:
        a = im.u32(VT["base"] + 4 * ev)
        chain, dflt, names = decode_name2int(im, a)
        stat[ev] = {"addr": hex(a), "chain": chain, "default": dflt, "strings": names}
    J1["static"] = stat
    check(all(all(v is not None and n is not None for n, v, _ in s["chain"]) and s["default"] is not None for s in stat.values()),
          "static pattern decoder resolved every compare (name, constant) and the default of all 8 even slots")
    # feed sites
    fs = {}
    for w in ("insert", "master", "send"):
        for fnm in ("s10", "s38", "s51"):
            fn = MGR[w][fnm]
            if fn and not (w == "insert" and fnm == "s51"): fs["%s_%s" % (w, fnm)] = feed_sites(im, fn)
    J1["feed_sites"] = fs
    # emulation
    x = H77.EmuProc("insert"); e = x.e; Jc = Juce(e)
    allnames = sorted(set(n for s in stat.values() for n in s["strings"]))
    J1["all_names"] = allnames
    em = {}; ok_all = True; probes = allnames + UNKNOWN
    idents = {n: Jc.ident(n) for n in probes}
    J1["empty_identifier_text"] = hex(e.u32(idents[""]))
    for ev, (od, meaning) in PAIRS.items():
        a = im.u32(VT["base"] + 4 * ev); ao = im.u32(VT["base"] + 4 * od)
        got = {n: s32(e.call(a, 0, idents[n])[0]) for n in probes}
        smap = {n: v for n, v, _ in stat[ev]["chain"]}
        exp = {n: smap.get(n, stat[ev]["default"]) for n in probes}
        inv = {}
        for i in range(-3, 21):
            r0 = e.call(ao, 0, i & 0xffffffff)[0]; inv[i] = Jc.name_at(r0)
        rt = {i: got.get(inv[i], s32(e.call(a, 0, Jc.ident(inv[i]))[0])) for i in inv}
        table = {n: got[n] for n in stat[ev]["strings"]}
        em[ev] = {"meaning": meaning, "odd": hex(ao), "name_to_int": table, "unknown": {n: got[n] for n in UNKNOWN},
                  "int_to_name": inv, "round_trip": rt}
        ok = got == exp
        ok_all &= ok
        check(ok, "slot %d %s (%s): emulated name->int on %d names (%d table + %d unknown) = static decode %s; default/unknown -> %s" % (
            ev, stat[ev]["addr"], meaning, len(probes), len(stat[ev]["strings"]), len(probes) - len(stat[ev]["strings"]),
            {n: v for n, v in sorted(table.items(), key=lambda t: (t[1], t[0]))}, stat[ev]["default"]))
    J1["emulated"] = em
    # odd-slot inverse: every int with a distinct name round-trips
    rt_ok = {}
    for ev, d in em.items():
        valid = sorted(set(v for v in d["name_to_int"].values()))
        rt_ok[ev] = all(d["round_trip"][i] == i for i in valid)
    check(all(rt_ok.values()), "odd slots (int -> name) invert the even slots on every int the even slot can produce: "
          "even(odd(i)) == i for all reachable i (per slot %s)" % rt_ok)
    J1["imports"] = e.import_report()
    return J1


# ===================================================================================================================== C2 static
def c2_static(im, check):
    s, e = im.func_of(ED_CTOR); ins = im.disasm(s, e); T = {i.address: "%s %s" % (i.mnemonic, i.op_str) for i in ins}
    G = _static_names(im, ins)
    J = {"ctor_static_names": {hex(k): v for k, v in sorted(G.items())}}
    check(im.u32(0x359d90 + 8 + 0xf9c) == ED_VT and T[0x359d94] == "str r3, [r8], #0x24",
          "ctor 0x359d1c stores vtable 0x8ac720 (the only other users of the literal are the two dtors 0x371578 / 0x371ccc)")
    check(G.get(0xf53064) == "Off" and G.get(0xf52f6c) == "FilterTypeOff" and G.get(0xf62a0c) == "None",
          "ctor function-static Identifiers: 0xf53064 = \"Off\" (copied to 0xf62a14 -> +0x24 type), 0xf52f6c = \"FilterTypeOff\" "
          "(-> 0xf62a24 / 0xf62a2c -> +0x2c / +0x30), 0xf62a0c = \"None\" (+0x34+8k names; pair 0xf62a34 = (\"None\", 0.0))")
    check(T[0x359f0c] == "mov r7, #0" and T[0x359f24] == "strb r7, [r4, #0x28]" and T[0x359f68] == "strb r3, [r4, #0x29]"
          and [x for x in im.disasm(0x34acb8, 0x34acc8)][0].op_str == "r0, #0",
          "ctor: +0x28 (SYNC/LookAhead byte) = 0; +0x29 = static byte 0xf62a1c = bool(0x34acb8()) where 0x34acb8 = `mov r0,#0`")
    floats = [a for a, t in T.items() if re.match(r"str r3, \[r4, #0x(38|40|48|50|58|60)\]$", t) and 0x35a07c <= a < 0x35a2a4]
    check(len(floats) == 6, "ctor: six param floats +0x38+8k stored from the static pair's float word (6 stores %s)" % [hex(a) for a in floats])
    J["callers"] = {"0x35ceb8": "0x35cb30 loop: String(\"InsertFx\") + String(n)", "0x35e170": "PatternData 0x35de70: \"SendFx\"",
                    "0x35e32c": "PatternData 0x35de70: \"MasterFx\""}
    calls = sorted(hex(x) for x, t, k in im.direct_calls() if t == ED_CTOR)
    check(calls == ["0x35ceb8", "0x35e170", "0x35e32c"], "0x359d1c has exactly 3 direct callers %s (Insert 'InsertFx'+n, 'SendFx', "
          "'MasterFx'); none passes a type" % calls)
    return J


# ===================================================================================================================== C2 / C3
def c2_c3(check, J1):
    out = {}
    for which in ("insert", "master", "send"):
        node = {"insert": "InsertFx0", "master": "MasterFx", "send": "SendFx"}[which]
        rig = Rig(which, node); e = rig.e; Jj = rig.J; x = rig.x
        names = INS_NAMES if which == "insert" else MS_NAMES
        R = {"ctor_fields": rig.ctor_fields, "ed_ctor": rig.ed_ctor}
        check(rig.ctor_fields["proc"] and rig.ctor_fields["holder"] and rig.ctor_fields["en"] == 1 and rig.ctor_fields["vptr"] == hex(VT[which]),
              "%s: real manager ctor 0x%x: vptr %s, +0x1c = processor, +0x20 = holder, +0x24 = 1, +0x30 = %d" % (
                  which, MGR[which]["ctor"], rig.ctor_fields["vptr"], rig.ctor_fields["r30"]))
        # (a) reload with the ctor-default EffectData
        idx_off = s32(e.call(MGR[which]["s52"], rig.m, rig.ed + 0x24)[0])
        rig.clear(); rig.reload()
        R["reload_default_ed"] = {"s52(type)": idx_off, "setFxType": list(rig.setfx), "slot14": rig.s14_log(),
                                  "pending": s32(e.u32(x.p + x.P["pend"]))}
        # s52 on every type name the processors know (real Identifiers)
        # (b) s32 per type, then reload
        eid = rig.effect_id_for(); R["effect_id_for_index"] = eid
        per = {}
        for t in range(10):
            # fresh EffectData again (ctor) so every type starts from the device default
            e.call(ED_CTOR, rig.ed, Jj.string(node), e.malloc(0x200))
            x.set_fx_type(-1); rig.clear()
            e.call(MGR[which]["s32"], rig.m, eid[t])
            after32 = read_ed(e, Jj, rig.ed); s14_32 = rig.s14_log(); sf32 = list(rig.setfx)
            rig.clear(); x.set_fx_type(-1); rig.clear()
            rig.reload()
            log = rig.s14_log()
            dflt = {idx: "%08x" % b for idx, b in x.defaults[t]}
            got = {}
            for o, idx, b in log:
                if o == t: got[idx] = b
            cmp = {idx: (got.get(idx), dflt.get(idx), got.get(idx) == dflt.get(idx)) for idx in sorted(set(got) | set(dflt))}
            per[t] = {"name": names[t], "effectId": eid[t], "ed_after_s32": after32, "s32_slot14": s14_32, "s32_setFxType": sf32,
                      "reload_setFxType": list(rig.setfx), "reload_slot14": log, "compare": cmp, "s54": list(rig.s54)}
        R["per_type"] = per
        ctor_ok = (R["ed_ctor"]["type"] == "Off" and R["ed_ctor"]["b28_sync"] == 0 and R["ed_ctor"]["b29"] == 0
                   and R["ed_ctor"]["id2c"] == "FilterTypeOff" and R["ed_ctor"]["id30"] == "FilterTypeOff"
                   and R["ed_ctor"]["params"] == [("None", "00000000")] * 6 and R["ed_ctor"]["node_name"] == node)
        check(ctor_ok, "%s: REAL EffectData ctor(\"%s\"): type \"Off\", +0x28 = 0, +0x29 = 0, +0x2c = +0x30 = \"FilterTypeOff\", six params "
              "(\"None\", 0.0)" % (which, node))
        rd = R["reload_default_ed"]
        check(rd["s52(type)"] == -1 and rd["setFxType"] == [-1] and rd["slot14"] == [] and rd["pending"] == -1,
              "%s: reload (s51%s) of the ctor-default EffectData: s52(\"Off\") = -1 -> setFxType(-1), 0 slot-14 calls (FX off)" % (
                  which, " -> s10" if MGR[which]["s10"] else ""))
        no14 = all(p["s32_slot14"] == [] and p["s32_setFxType"] == [t] for t, p in per.items())
        check(no14, "%s: s32 (applyFxType) for all 10 types: exactly setFxType(type) and 0 slot-14 calls (it only reads the effect)" % which)
        eq = {t: all(ok for i, (g, d, ok) in p["compare"].items() if d is not None) for t, p in per.items()}
        extra = {t: sorted(i for i, (g, d, ok) in p["compare"].items() if d is None) for t, p in per.items()}
        miss = {t: sorted(i for i, (g, d, ok) in p["compare"].items() if g is None) for t, p in per.items()}
        R["reload_extra_indices"] = extra; R["reload_missing_indices"] = miss
        check(all(eq.values()) and all(p["reload_setFxType"] == [t] for t, p in per.items()),
              "%s: s32(type) then reload: setFxType(type) and every slot-14 value whose index slot 52 sets equals the slot-52 default "
              "bit-exactly, 10/10 types; indices sent without a slot-52 default: %s; slot-52 indices not re-sent: %s" % (
                  which, {t: v for t, v in extra.items() if v}, {t: v for t, v in miss.items() if v}))
        # ---- alternative: s32 writes a fixed per-type table (not the live effect state) -> change live state first
        alt = {}
        probes = {"insert": [(7, 0, 0.5), (7, 7, 1.0), (7, 8, 1.0), (9, 10, 5.0), (9, 10, 16.0), (2, 6, 3.0), (5, 6, 2.0), (3, 7, 2.0)],
                  "master": [(7, 7, 1.0), (7, 8, 1.0), (7, 6, 1.0), (0, 3, 0.25), (0, 4, 0.75), (0, 6, 1.0)],
                  "send": [(7, 7, 1.0), (7, 8, 1.0), (7, 6, 1.0), (0, 3, 0.25), (0, 4, 0.75), (0, 6, 1.0)]}[which]
        for t, idx, v in probes:
            e.call(ED_CTOR, rig.ed, Jj.string(node), e.malloc(0x200))
            x.set_fx_type(-1); x.set_param(t, idx, v); rig.clear()
            e.call(MGR[which]["s32"], rig.m, eid[t]); ed = read_ed(e, Jj, rig.ed)
            x.set_fx_type(-1); rig.clear(); rig.reload()
            got = [b for o, i, b in rig.s14_log() if o == t and i == idx]
            alt["%d/%d=%g" % (t, idx, v)] = {"ed": ed, "reload": got}
            if idx in dict(x.defaults[t]): x.set_param(t, idx, u2f(dict(x.defaults[t])[idx]))   # restore the slot-52 value
        R["alt_live_state"] = alt
        # ---- SYNC/LookAhead byte carry-over: s32(type with SYNC = 1 live) then s32(Compressor) then reload
        e.call(ED_CTOR, rig.ed, Jj.string(node), e.malloc(0x200))
        st = 0; x.set_fx_type(-1); x.set_param(st, 6, 1.0); rig.clear()
        e.call(MGR[which]["s32"], rig.m, eid[st]); b1 = e.rd(rig.ed + 0x28, 1)[0]
        x.set_fx_type(-1); e.call(MGR[which]["s32"], rig.m, eid[7]); b2 = e.rd(rig.ed + 0x28, 1)[0]
        x.set_fx_type(-1); rig.clear(); rig.reload()
        la = [b for o, i, b in rig.s14_log() if o == 7 and i == 6]
        x.set_param(st, 6, u2f(dict(x.defaults[st]).get(6, 0)))
        R["carry_over"] = {"from_type": st, "b28_after_first": b1, "b28_after_compressor_s32": b2, "reload_comp_idx6": la}
        # ---- s38 (this, Identifier*, which): which converter / index per (type, which), emulated over every converter name
        probe = J1["all_names"] + ["Bogus"]
        pid = {n: Jj.ident(n) for n in probe}
        maps = {ev: {n: d["name_to_int"].get(n, d["unknown"].get(n)) for n in probe} for ev, d in J1["emulated"].items()}
        for ev, d in J1["emulated"].items():
            for n in probe:
                if maps[ev][n] is None: maps[ev][n] = s32(e.call(e.u32(VT["base"] + 4 * ev), 0, pid[n])[0])
        s38 = {}
        for t in range(10):
            for wh in (0, 1):
                x.set_fx_type(t); outv = {}; idxs = set(); fld = None
                for n in probe:
                    rig.clear(); e.call(MGR[which]["s38"], rig.m, pid[n], wh)
                    lg = [(o, i, b) for o, i, b in rig.s14_log()]
                    for o, i, b in lg: idxs.add((o, i))
                    outv[n] = [u2f(int(b, 16)) for o, i, b in lg]
                    f = set(k for k, a in (("+0x2c", 0x2c), ("+0x30", 0x30)) if Jj.name_at(rig.ed + a) == n)
                    fld = f if fld is None else fld & f
                if not idxs: continue
                conv = [ev for ev in maps if all(outv[n] == [float(maps[ev][n])] for n in probe)]
                s38["%d/%d" % (t, wh)] = {"targets": sorted(idxs), "converter_slot": conv,
                                         "ed_field": sorted(fld)}
        R["s38"] = s38
        e.call(ED_CTOR, rig.ed, Jj.string(node), e.malloc(0x200)); x.set_fx_type(-1)
        out[which] = R
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H083"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; fails = []; J = {}
    def Pr(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        Pr("  [%s] %s" % ("PASS" if c else "FAIL", msg))
        if not c: fails.append(msg)
    im = Image()
    Pr("== C1 converters (target sha %s)" % sha(im.data)[:12])
    J["c1"] = J1 = c1(im, check)
    for k, v in J1["feed_sites"].items():
        Pr("  feed sites %s (site, slot, effect, idx, source): %s" % (k, v))
    for ev, d in J1["emulated"].items():
        Pr("  slot %d/%d %s: int->name %s" % (ev, PAIRS[ev][0], d["meaning"], {i: n for i, n in d["int_to_name"].items()}))
    Pr("== C2 EffectData ctor (static)")
    J["c2_static"] = c2_static(im, check)
    Pr("== C2/C3 EffectData + s32 + reload (emulated)")
    J["c23"] = J23 = c2_c3(check, J1)
    for w, R in J23.items():
        Pr("  %s ctor ED: %s" % (w, R["ed_ctor"]))
        Pr("  %s reload with ctor ED: %s" % (w, R["reload_default_ed"]))
        for t, p in R["per_type"].items():
            ed = p["ed_after_s32"]
            Pr("  %s t%d %-18s s32: type=%s sync=%d b29=%d id2c=%s id30=%s params=%s | s32 slot14 %d | reload cmp %s" % (
                w, t, p["name"], ed["type"], ed["b28_sync"], ed["b29"], ed["id2c"], ed["id30"], [b for _, b in ed["params"]],
                len(p["s32_slot14"]), {i: (g, d, ok) for i, (g, d, ok) in p["compare"].items()}))
        Pr("  %s carry-over: %s" % (w, R["carry_over"]))
        Pr("  %s s38 (type/which -> targets, converter slot, ED field): %s" % (w, R["s38"]))
        for k, v in R["alt_live_state"].items():
            ed = v["ed"]
            Pr("  %s alt live-state %s: ED sync=%d id2c=%s id30=%s params=%s -> reload %s" % (
                w, k, ed["b28_sync"], ed["id2c"], ed["id30"], [b for _, b in ed["params"]], v["reload"]))
    rows = ["context,effect_index,effect,slot14_index,ed_path_value_bits,ed_path_value,slot52_default_bits,equal"]
    for w, R in J23.items():
        for t, p in R["per_type"].items():
            for i, (g, d, ok) in sorted(p["compare"].items()):
                rows.append("%s,%d,%s,%d,%s,%s,%s,%s" % (w, t, p["name"], i, g, "" if g is None else repr(u2f(int(g, 16))), d,
                                                        "n/a (no slot-52 value)" if d is None else ok))
    tab = ("\n".join(rows) + "\n").encode()
    open(os.path.join(a.out, "e2e_table.csv"), "wb").write(tab)
    Pr("RESULT: %d failed checks" % len(fails))
    blob = json.dumps(J, sort_keys=True, default=str, indent=1).encode()
    open(os.path.join(a.out, "h083.json"), "wb").write(blob)
    txt = "\n".join(rep).encode(); open(os.path.join(a.out, "h083_report.txt"), "wb").write(txt)
    print("sha256 h083.json %s\nsha256 h083_report.txt %s\nsha256 e2e_table.csv %s" % (sha(blob), sha(txt), sha(tab)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
