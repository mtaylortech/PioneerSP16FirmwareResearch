#!/usr/bin/env python3
"""H082 round 2 — what selects the fine (m = 1) vs coarse (m = 0x311aa0) encoder step in the FX step routines.

Target: target/EP085_Main_R_fw160 (1.60, SHA-256 3d1392a6…5464), read-only. Own code only: firmware bytes are read at run time,
never stored; outputs are derived facts (addresses, offsets, counts, hashes). Emulation is guest-memory only.

Question (kb/cycles/036.md, Critic C4): in 0x316a10 (Insert) / 0x313ecc (Send/Master) the multiplier m is 1 when
CFG(DM+0x434c) item 6 vt+0xc != 0 (Insert: when DM+0x60 != 0 or DM+0x64 == -1; else the byte DM+0x68 decides).
  S1 static (capstone, asserted): DM class + ctor defaults, CFG = UIInputManager singleton, item list = UIButton array,
     item 6 = hardware button id 6, UIButton vt+0xc = state byte +0xd, writers of +0xd, id 6 = SHIFT (two independent
     id->name maps), TransportController SHIFT handler (DM+0x68 toggle / DM+0x5c), writers of DM+0x60/+0x64/+0x68
     (whole-.text linear sweep, every candidate classified).
  S2 emulation (unicorn): real UIInputManager impl ctor + button init + array fill -> array[6]; real UIButton setRawState ->
     vt+0xc; real TransportController handler on id 6 -> DM+0x68 / +0x5c; real step routines with CFG item 6 = a REAL
     UIButton object (SHIFT up/down) and DM+0x60/+0x64/+0x68 combinations -> observed m at the merge point and s27 value.
Run: .venv/bin/python -B harness/H082_step_mode.py --out DIR      (default harness/out/H082/step_mode)
"""
import argparse, hashlib, json, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(HERE, "lib")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "models"))
import darwin_ctr_fix                                          # noqa: E402
darwin_ctr_fix.install()
import emu                                                     # noqa: E402
from emu import f2u                                            # noqa: E402
from sp16img import Image                                      # noqa: E402
import sync_convert as SC                                      # noqa: E402

DM_CTOR_FN, DM_NEW, DM_SIZE, DM_VT2 = 0x56f7f4, 0x56f8b0, 0x4350, 0x9328a8
CFG_GLOBAL, UIM_CTOR, UIM_VT, IMPL_CTOR, IMPL_SIZE = 0xf6e380, 0x556044, 0x931288, 0x556880, 0x103c
GET_BUTTON, BTN_VT, BTN_CTOR, BTN_INIT, BTN_SETRAW, BTN_REGISTER, ARRAY_FILL, INPUT_POLL = \
    0x5560bc, 0x9313a8, 0x55b0f8, 0x55b1a4, 0x55b26c, 0x559d8c, 0x55803c, 0x55767c
TEST_SWITCH, TEST_JT = 0x54a9c8, 0x54a9f4
TRANSPORT_HANDLER, TRANSPORT_JT, TRANSPORT_VT_SLOT = 0x1d1828, 0x1d1854, 0x86626c
STEPCTRL_W60, STEPCTRL_W60B, SEQSTEP_HANDLER, SEQSTEP_PRESS = 0x1e3924, 0x1e3bd0, 0x1e34e8, 0x1e2c64
STEP = {"insert": 0x316a10, "sendmaster": 0x313ecc}
MERGE = {"insert": 0x316b74, "sendmaster": 0x31402c}           # r0 = step multiplier m here (both paths join)
STEP_MULT = 0x311aa0
LABELS = {0xa8: "BACK", 0xb8: "FAVORITE", 0xc8: "TRACK", 0xd8: "MUTE", 0xe8: "SLICE", 0xf8: "SCALE", 0x108: "SHIFT", 0x118: "REC",
          0x128: "STOP", 0x138: "PLAY", 0x148: "SCENE", 0x158: "PATTERN", 0x168: "HOLD", 0x178: "MODE", 0x198: "USB STOP",
          0x1a8: "ACTIVE"}
LABELS.update({0x1b8 + 0x10 * k: "STEP %d" % (k + 1) for k in range(16)})
LABELS.update({0x2b8 + 0x10 * k: "BAR %d" % (k + 1) for k in range(4)})


def sha(b): return hashlib.sha256(b).hexdigest()
def s32(u): return u - (1 << 32) if u & 0x80000000 else u


def cls_at(im, vt):
    try:
        return im.cstr(im.u32(im.u32(vt - 4) + 4), 80)
    except Exception:                                          # noqa: BLE001
        return None


def dis(im, a, b):
    return [(i.address, i.mnemonic, i.op_str) for i in im.disasm(a, b)]


def sweep(im):
    """Linear capstone sweep of all of .text; undecodable words are skipped one at a time. Returns [(addr, mn, op)]."""
    lo, hi = im.sec[".text"]; out = []; a = lo
    while a < hi:
        n = 0
        for (ad, sz, mn, op) in im.md.disasm_lite(im.data[im.off(a):im.off(hi)], a):
            out.append((ad, mn, op)); n += 1
        a = (out[-1][0] + 8) if n else a + 4
    return out


def track_offsets(im, lo, hi, objreg, watch):
    """Constant-offset tracker over a straight-line range: regs holding obj+const or const; logs stores to obj+watch."""
    R = {objreg: ("obj", 0)}; hits = []
    def val(s):
        s = s.strip()
        return ("c", int(s[1:], 0) & 0xffffffff) if s.startswith("#") else R.get(s)
    def add(a, b, sg=1):
        if a is None or b is None: return None
        if a[0] == "c" and b[0] == "c": return ("c", (a[1] + sg * b[1]) & 0xffffffff)
        if a[0] == "obj" and b[0] == "c": return ("obj", a[1] + sg * b[1])
        if a[0] == "c" and b[0] == "obj" and sg == 1: return ("obj", a[1] + b[1])
        return None
    for ad, m, op in dis(im, lo, hi):
        ops = [x.strip() for x in op.split(",")]
        if m in ("bl", "blx"):
            for r in ("r0", "r1", "r2", "r3", "ip", "lr"): R.pop(r, None)
            continue
        if m in ("mov", "movw", "mvn") and len(ops) == 2:
            v = val(ops[1])
            if m == "mvn" and v and v[0] == "c": v = ("c", ~v[1] & 0xffffffff)
            R[ops[0]] = v; continue
        if m in ("add", "sub") and len(ops) == 3:
            R[ops[0]] = add(val(ops[1]), val(ops[2]), 1 if m == "add" else -1); continue
        mm = re.match(r"(str\w*|ldr\w*) (\w+), \[(\w+)(?:, (#?-?\w+))?\]$", m + " " + op)
        if mm:
            b = R.get(mm.group(3)); off = val(mm.group(4)) if mm.group(4) else ("c", 0)
            ea = add(b, off) if b else None
            if ea and ea[0] == "obj" and ea[1] in watch and mm.group(1).startswith("str"):
                hits.append((ad, m, op, ea[1]))
            if mm.group(1).startswith("ldr"): R[mm.group(2)] = None
            continue
        if ops and re.match(r"r\d+$|sb|sl|fp|ip|lr", ops[0]) and not m.startswith(("cmp", "cmn", "tst", "teq", "b", "v", "push", "pop", "str", "stm")):
            R[ops[0]] = None
    return hits


# ============================================================================================================================ S1
def s1_static(im, check, J, Pr):
    # --- DM = ControllerDataManager --------------------------------------------------------------------------------------------
    L = dis(im, DM_NEW - 4, DM_NEW + 4)
    check(L[0][1:] == ("movw", "r0, #0x4350") and L[1][2] == "#0x102e8" and im.plt().get(0x102e8) == "_Znwj",
          "S1 DM allocation: 0x%x `movw r0,#0x4350` + operator new (0x%x) inside 0x%x" % (DM_NEW - 4, DM_NEW, DM_CTOR_FN))
    nm = cls_at(im, DM_VT2)
    check(nm == "21ControllerDataManager", "S1 DM vtable 0x%x (stored at DM+8 by the ctor) typeinfo name = %r" % (DM_VT2, nm))
    hits = track_offsets(im, 0x56f8d4, 0x570da4, "r4", {0x60, 0x64, 0x68, 0x4344, 0x4348, 0x434c})
    got = {o: (hex(a), op) for a, m, op, o in hits}
    J["dm_ctor_stores"] = got
    ctx = {a: (m, op) for a, m, op in dis(im, 0x56f8c0, 0x56f950)}
    ok = (set(got) == {0x60, 0x64, 0x68, 0x4344, 0x4348, 0x434c} and ctx[0x56f8c0] == ("mvn", "r2, #0") and ctx[0x56f8c4] == ("mov", "r3, #0")
          and ctx[0x56f928] == ("str", "r3, [r4, #0x60]") and ctx[0x56f948] == ("str", "r2, [r4, #0x64]")
          and ctx[0x56f92c] == ("strb", "r3, [r4, #0x68]"))
    check(ok, "S1 DM ctor defaults: +0x60 := 0 (0x56f928), +0x64 := -1 (0x56f948), +0x68 := 0 byte (0x56f92c); +0x4344/+0x4348/+0x434c "
              "stored at %s" % [got.get(o) for o in (0x4344, 0x4348, 0x434c)])
    L = dis(im, 0x56f898, 0x56f8a4) + dis(im, 0x56fa74, 0x56fa78)
    check(L[0][2].startswith("r7, [pc") and im.u32(0x56f898 + 8 - 0x18) == CFG_GLOBAL and L[2][2] == "r5, [r7]" and L[-1][2] == "r5, [r4, r2]",
          "S1 DM+0x434c := r5 = *(0x%x) (ldr r5,[r7] at 0x56f8a0; str at 0x56fa74)" % CFG_GLOBAL)
    # --- CFG = UIInputManager singleton --------------------------------------------------------------------------------------
    L = dis(im, 0x570e78, 0x570e98)
    check(("mov", "r0, #0xc") in [(m, o) for _, m, o in L] and ("bl", "#0x%x" % UIM_CTOR) in [(m, o) for _, m, o in L]
          and ("str", "r5, [r7]") in [(m, o) for _, m, o in L],
          "S1 *(0x%x) is created lazily: new(0xc) + ctor 0x%x, stored at 0x570e94" % (CFG_GLOBAL, UIM_CTOR))
    check(cls_at(im, UIM_VT) == "14UIInputManager", "S1 CFG class: vtable 0x%x typeinfo %r; ctor allocates impl new(0x103c), ctor 0x%x -> +8"
          % (UIM_VT, cls_at(im, UIM_VT), IMPL_CTOR))
    L = [(m, o) for _, m, o in dis(im, GET_BUTTON, GET_BUTTON + 0x1c)]
    check(L[:6] == [("ldr", "r3, [r0, #8]"), ("ldr", "r2, [r3, #0xc]"), ("cmp", "r1, r2"), ("ldrlo", "r3, [r3, #4]"),
                    ("movhs", "r0, #0"), ("ldrlo", "r0, [r3, r1, lsl #2]")],
          "S1 0x%x(cfg, i) = impl(+8)->array(+4)[i] if i < count(+0xc) else 0" % GET_BUTTON)
    # --- items are UIButton; vt+0xc -----------------------------------------------------------------------------------------
    check(cls_at(im, BTN_VT) == "8UIButton" and im.u32(BTN_VT + 0xc) == 0x55ae54 and im.u32(BTN_VT + 8) == 0x55ae4c
          and [(m, o) for _, m, o in dis(im, 0x55ae54, 0x55ae5c)] == [("ldrb", "r0, [r0, #0xd]"), ("bx", "lr")]
          and [(m, o) for _, m, o in dis(im, 0x55ae4c, 0x55ae54)] == [("ldr", "r0, [r0, #8]"), ("bx", "lr")],
          "S1 UIButton vtable 0x%x: vt+8 = 0x55ae4c (return +8 = id), vt+0xc = 0x55ae54 (return byte +0xd = state)" % BTN_VT)
    calls = im.direct_calls()
    by = lambda t: [s for s, y, k in calls if y == t and k == "bl"]
    init_sites = by(BTN_INIT); raw_sites = by(BTN_SETRAW)
    check(len(init_sites) == 37 and {im.func_of(s)[0] for s in init_sites} == {BTN_REGISTER}
          and len(raw_sites) == 37 and {im.func_of(s)[0] for s in raw_sites} == {INPUT_POLL}
          and not by(0x55b144) and not by(0x55b208),
          "S1 UIButton writers of +0xd: init 0x%x (37 calls, all in 0x%x; sibling inits 0x55b144/0x55b208 have no caller) and "
          "setRawState 0x%x (37 calls, all in the panel-input routine 0x%x)" % (BTN_INIT, BTN_REGISTER, BTN_SETRAW, INPUT_POLL))
    L = dis(im, 0x559e28, 0x559e3c)
    check([(m, o) for _, m, o in L] == [("mov", "r2, r4"), ("mov", "r3, r4"), ("add", "r0, r6, #0x19c"), ("mov", "r1, #6"),
                                         ("bl", "#0x%x" % BTN_INIT)] and ("mov", "r4, r2") in [(m, o) for _, m, o in dis(im, 0x559de4, 0x559dec)],
          "S1 button impl+0x19c is initialised with id 6, initial state r2 = 0 and input filter r3 = 0 (none): +0xd follows the raw state")
    L = [(m, o) for _, m, o in dis(im, BTN_SETRAW, BTN_SETRAW + 0x70)]
    check(("strb", "r1, [r5, #0xe]") in L and ("ldr", "r0, [r5, #0x18]") in L and ("strb", "r6, [r5, #0xd]") in L,
          "S1 setRawState 0x%x: +0xe := raw; filter +0x18 (null here) else logical = raw; +0xd := logical; observers notified" % BTN_SETRAW)
    # --- id 6 = SHIFT ----------------------------------------------------------------------------------------------------------
    L = [(m, o) for _, m, o in dis(im, TEST_SWITCH, TEST_SWITCH + 0x2c)]
    check(("ldr", "r3, [r3, #8]") in L and ("cmp", "r0, #0x24") in L, "S1 TestModeController raw-button handler 0x%x switches on getId() 0..36" % TEST_SWITCH)
    idmap = {}
    for cid in range(37):
        t = im.u32(TEST_JT + 4 * cid); offs = []
        for a, m, o in dis(im, t, t + 0x40)[:14]:
            mm = re.search(r"r4, #(0x[0-9a-f]+)\]", o)
            if mm: offs.append(int(mm.group(1), 16))
            if m in ("b", "bx") or m.startswith("pop"): break
        idmap[cid] = LABELS.get(offs[0] - 5) if offs else None
    J["button_id_names_testpage"] = idmap
    check(idmap[6] == "SHIFT" and idmap[7] == "REC" and idmap[8] == "STOP" and idmap[9] == "PLAY",
          "S1 test-page map (case k writes the state byte +5 of the label record whose ctor string is known): id 6 -> %r; full map %s"
          % (idmap[6], {k: v for k, v in idmap.items() if v}))
    # labels: ctor string per record (independent of the switch)
    rec = {}
    lst = dis(im, 0x550b4c, 0x551b7c)
    for k, (a, m, o) in enumerate(lst):
        mm = re.match(r"r1, \[pc, #(0x[0-9a-f]+)\]$", o)
        if m == "ldr" and mm:
            s = im.cstr(im.u32(a + 8 + int(mm.group(1), 16)), 20)
            for a2, m2, o2 in lst[k + 1:k + 6]:
                m3 = re.match(r"r0, r6, #(0x[0-9a-f]+)$", o2)
                if m2 == "add" and m3: rec.setdefault(int(m3.group(1), 16), s); break
    check(rec.get(0x108) == "SHIFT" and all(rec.get(o) == n for o, n in LABELS.items() if not n.startswith(("STEP", "BAR"))),
          "S1 test-page ctor 0x550b4c builds record +0x108 from the string %r (all 16 named records match the table)" % rec.get(0x108))
    # observer registrations (button index per registering function)
    regs = {}
    ins_ = {}
    for s in by(0x556154):
        f = im.func_of(s)[0]; v = None
        for a, m, o in reversed(dis(im, s - 0x20, s)):
            if o.startswith("r1,"):
                mm = re.match(r"r1, #(0x[0-9a-f]+|\d+)$", o); v = int(mm.group(1), 0) if mm and m in ("mov", "movw") else "reg"; break
        regs.setdefault(f, []).append(v)
    J["button_observer_registrations"] = {hex(f): v for f, v in sorted(regs.items()) if len(v) < 8}
    check(sorted(regs.get(0x1d1da0, [])) == [6, 7, 8, 9] and sorted(x for x in regs.get(0x1d1bc8, []) if x != "reg" and x is not None) == [6, 8, 9],
          "S1 addButtonObserver 0x556154 sites: 0x1d1da0 registers ids %s and 0x1d1bc8 %s (TransportController: SHIFT, REC, STOP, PLAY); "
          "PadController 0x1d5698 %s (TRACK..SCALE); RibbonController 0x1dd5a0 %s (HOLD, MODE)" % (
              regs.get(0x1d1da0), regs.get(0x1d1bc8), regs.get(0x1d5698), regs.get(0x1dd5a0)))
    # --- TransportController SHIFT handler -----------------------------------------------------------------------------------
    check(im.u32(TRANSPORT_VT_SLOT) == TRANSPORT_HANDLER and cls_at(im, 0x866264) == "19TransportController"
          and [im.u32(TRANSPORT_JT + 4 * k) for k in range(4)] == [0x1d19e4, 0x1d1958, 0x1d1920, 0x1d1868],
          "S1 TransportController vt 0x866264 slot 2 (= IUIButtonObserver vt+8, called on a state change) = 0x%x; switch on id-6: "
          "case id 6 -> 0x1d19e4" % TRANSPORT_HANDLER)
    L = [(m, o) for _, m, o in dis(im, 0x1d19e4, 0x1d1a28)]
    check(L == [("ldr", "r3, [r4, #0x10]"), ("ldr", "r3, [r3, #0x81c]"), ("ldr", "r2, [r3, #0x60]"), ("cmp", "r2, #0"),
                ("bne", "#0x1d1a20"), ("ldr", "r1, [r3, #0x64]"), ("cmn", "r1, #1"), ("beq", "#0x1d1a20"), ("cmp", "r6, #0"),
                ("popeq", "{r3, r4, r5, r6, r7, pc}"), ("ldrb", "r1, [r3, #0x68]"), ("cmp", "r1, #0"), ("moveq", "r2, #1"),
                ("strb", "r2, [r3, #0x68]"), ("pop", "{r3, r4, r5, r6, r7, pc}"), ("strb", "r6, [r3, #0x5c]"),
                ("pop", "{r3, r4, r5, r6, r7, pc}")],
          "S1 SHIFT handler 0x1d19e4: DM = [[this+0x10]+0x81c]; if DM+0x60 == 0 and DM+0x64 != -1: on press toggle byte DM+0x68; "
          "otherwise DM+0x5c := pressed")
    # --- X+0x81c (used by the hardware controllers) is the same ControllerDataManager -------------------------------------
    A_ = [(m, o) for _, m, o in dis(im, 0x570cd4, 0x570ce8)]; B_ = [(m, o) for _, m, o in dis(im, 0x1e68e8, 0x1e68ec)]
    C_ = [(m, o) for _, m, o in dis(im, 0x1e6ab4, 0x1e6ad0)]
    check(("mov", "r1, r4") in A_ and ("bl", "#0x1e68b0") in A_ and B_ == [("str", "r5, [r4, #0x850]")]
          and ("ldr", "ip, [r0, #0x850]") in C_ and ("str", "ip, [r4, #0x840]") in C_ and ("add", "r8, r4, #0x24") in C_,
          "S1 the new DM (r4 in 0x56f7f4) is passed to 0x1e68b0 (new(0x854)) and stored at +0x850; controller setup 0x1e6aa8 copies it to "
          "+0x840 = (context X = this+0x24)+0x81c -- so [X+0x81c] in Transport/Step controllers is that DM")
    ins = sweep(im)
    newsz = []
    plt = im.plt(); news = {a_ for a_, n_ in plt.items() if n_ in ("_Znwj", "_Znaj", "malloc", "calloc")}
    for k, (a_, m_, o_) in enumerate(ins):
        if m_ == "bl" and int(o_[1:], 16) in news:
            for a2, m2, o2 in reversed(ins[max(0, k - 8):k]):
                if o2.startswith("r0,"):
                    if m2 in ("mov", "movw") and o2 == "r0, #0x4350": newsz.append(a_)
                    break
    check(newsz == [DM_NEW], "S1 allocation sweep: the only `r0 = 0x4350` + new/malloc site in .text is %s (one ControllerDataManager "
          "instance; the ViewController ref+4 DM and the controller [X+0x81c] DM are that object -- likely)" % [hex(x) for x in newsz])
    # --- writers of DM+0x60/+0x64/+0x68 (whole-.text sweep) ---------------------------------------------------------------
    lo, hi = im.sec[".text"]
    J["sweep"] = dict(instructions=len(ins), text_words=(hi - lo) // 4)
    byf = {}
    for x in ins: byf.setdefault(im.func_of(x[0])[0], []).append(x)
    cands = []
    for f, Lf in byf.items():
        if not any(re.search(r"#0x43(18|44|48|4c)$|#0x81c\]$", o) for _, _, o in Lf): continue
        for a, m, o in Lf:
            if m.startswith("str") and re.search(r"\[\w+, #(0x60|0x64|0x68)\]$", o): cands.append((f, a, m, o))
    J["dm_store_candidates"] = [(hex(f), hex(a), m, o) for f, a, m, o in cands]
    dm_sites = {0x56f928: "ctor +0x60 := 0", 0x56f948: "ctor +0x64 := -1", 0x56f92c: "ctor +0x68 := 0",
                0x1d1a18: "TransportController SHIFT (id 6) press while a step is held: +0x68 toggle",
                0x1e3a20: "StepController button handler: +0x60 := index (0..3) of the active step sub-controller",
                0x1e3ca0: "StepController 0x1e3bd0: +0x60 := 0",
                0x1e2d6c: "SequenceModeStepController step press: +0x64 := step index", 0x1e2fa0: "same, +0x64 := step index",
                0x1e3040: "same, +0x64 := -1", 0x1e309c: "same (release): +0x64 := -1", 0x1e30b0: "same (release): +0x68 := 0",
                0x1e31e8: "same, +0x64 := step index", 0x1e3380: "same, +0x64 := step index"}
    rows = []
    for f, a, m, o in cands:
        prev = dis(im, max(f, a - 0x40), a)
        base = re.search(r"\[(\w+),", o).group(1)
        via = None
        for a2, m2, o2 in reversed(prev):
            if o2.startswith(base + ",") and m2.startswith("ldr"): via = o2; break
            if o2.startswith(base + ","): via = m2 + " " + o2; break
        dm = a in dm_sites
        rows.append((hex(f), hex(a), o, via, dm_sites.get(a, "not DM (base is %s)" % (via or base))))
    J["dm_store_classified"] = rows
    dm_rows = [r for r in rows if not r[4].startswith("not DM")]
    # 0x1e3a20 (str r1 -> +0x60): r1 reaches the store on several paths; every load of r1 in 0x1e3924 is `ldr r1, [rX, #0x81c]`
    # (two exceptions, read by hand: 0x1e3b2c r1 = [r4+0x1c] is only compared, then 0x1e3994 -> 0x1e39b8/0x1e3b04/0x1e3b40 reload r1;
    #  0x1e3b40 r1 = [r4+0x20] is the X pointer, dereferenced at 0x1e3b48 `ldr r1, [r1, #0x81c]`)
    r1_loads = [(a_, o) for a_, m_, o in dis(im, STEPCTRL_W60, 0x1e3bc8) if m_.startswith("ldr") and o.startswith("r1,")]
    ok_r1 = bool(r1_loads) and all(o.endswith("#0x81c]") or a_ in (0x1e3b2c, 0x1e3b40) for a_, o in r1_loads)
    ok_dm = ok_r1 and all((r[3] or "").endswith("#0x81c]") for r in dm_rows if r[0] not in ("0x56f7f4",) and r[1] != "0x1e3a20")
    Pr("    (0x1e3924: %d loads of r1, all `[rX, #0x81c]`: %s)" % (len(r1_loads), ok_r1))
    check(len(dm_rows) == len(dm_sites) and ok_dm and all(not (r[3] or "").endswith("#0x81c]") for r in rows if r[4].startswith("not DM")),
          "S1 writers sweep: %d instructions over .text (%d words); %d stores to +0x60/+0x64/+0x68 in DM-touching functions, %d are DM "
          "(base loaded from [X+0x81c] or the ctor), %d other objects/stack" % (len(ins), (hi - lo) // 4, len(rows), len(dm_rows), len(rows) - len(dm_rows)))
    for r in rows: Pr("    %s %s %-24s via %-28s %s" % r)
    # ModelInterface-style writers (ref+4 -> DM, then store +0x60/+0x64/+0x68 within 12 instructions): none are DM
    mi = []
    for k, (a, m, o) in enumerate(ins):
        mm = re.match(r"(\w+), \[(\w+), #4\]$", o)
        if m != "ldr" or not mm: continue
        for a2, m2, o2 in ins[k + 1:k + 14]:
            if m2.startswith("str") and re.match(r"\w+, \[%s, #(0x60|0x64|0x68)\]$" % mm.group(1), o2): mi.append(a2)
            if re.match(r"%s," % mm.group(1), o2) and not m2.startswith(("str", "cmp")): break
            if m2 in ("bl", "blx", "b", "bx") or m2.startswith("pop"): break
    J["ref4_pattern_sites"] = [hex(x) for x in mi]
    check(not (set(mi) & set(dm_sites)), "S1 alternative writer path [ref+4]->+0x60/64/68 (ModelInterface style): %d sites %s, none DM "
          "(checked by hand: 0x561394/0x5613a8 table fill on another object, 0x5be900.. / 0x5bfbdc.. other objects, 0xe0148 a 3-way flag copy)"
          % (len(mi), [hex(x) for x in mi]))
    return ins


# ============================================================================================================================ S2
def stub_threads():
    for nm in ("pthread_mutex_lock", "pthread_mutex_unlock", "pthread_mutex_init", "pthread_mutex_destroy", "pthread_mutexattr_init",
               "pthread_mutexattr_settype", "pthread_mutexattr_destroy", "pthread_mutexattr_setprotocol"):
        emu.STUBS.setdefault(nm, (lambda e: e.setr(0, 0), "H082r2: no-op"))
    emu.STUBS.setdefault("__cxa_guard_acquire", (lambda e: e.setr(0, 0 if e.u32(e.r(0)) & 1 else 1), "H082r2: ARM EABI guard"))
    emu.STUBS.setdefault("__cxa_guard_release", (lambda e: e.w32(e.r(0), 1), "H082r2: set guard bit"))


def s2_button_array(check, J):
    """Real impl ctor (PadCalibration file read skipped), real button registration up to its first file access, real array fill."""
    from unicorn import arm_const as A
    stub_threads()
    e = emu.Emu()
    impl = e.malloc(IMPL_SIZE); e.wr(impl, bytes(IMPL_SIZE))
    e.add_watch(0x556c4c, lambda em: em.uc.reg_write(A.UC_ARM_REG_PC, 0x556cd8))          # stand-in: "no calibration file" path
    e.call(IMPL_CTOR, impl)
    def _cal(em):                                                                       # stand-in: calibration var -> 0x100
        em.setr(0, 0x100); em.uc.reg_write(A.UC_ARM_REG_PC, 0x55a100)
    e.add_watch(0x55a0f0, _cal)
    reg_err = None
    try:
        e.call(BTN_REGISTER, impl, 0)
    except emu.EmuAbort as ex:
        reg_err = str(ex)[:90]
    e.call(ARRAY_FILL, impl)
    arr, n = e.u32(impl + 4), e.u32(impl + 0xc)
    items = [(e.u32(arr + 4 * i) - impl, e.u32(e.u32(arr + 4 * i) + 8), e.u32(e.u32(arr + 4 * i))) for i in range(n)]
    J["s2_array"] = dict(n=n, item6=hex(items[6][0]), registration_stop=reg_err)
    check(n == 37 and items[6] == (0x19c, 6, BTN_VT) and all(it == (0xac + 0x28 * i, i, BTN_VT) for i, it in enumerate(items)),
          "S2 real UIInputManager impl: array(+4) has %d UIButtons, array[i] = impl+0xac+0x28*i with id i; item 6 = impl+0x%x, id %d, vt 0x%x "
          "(registration ran its 37 button inits, then stopped at %r -- after the buttons, irrelevant here)" % (n, items[6][0], items[6][1], items[6][2], reg_err))
    # setRawState -> vt+0xc
    b6 = impl + 0x19c; seq = []
    for raw in (1, 0, 1, 1, 0):
        e.call(BTN_SETRAW, b6, raw)
        seq.append(e.call(e.u32(e.u32(b6) + 0xc), b6)[0])
    check(seq == [1, 0, 1, 1, 0], "S2 real setRawState(id 6, raw) then real vt+0xc: raw 1,0,1,1,0 -> %s (vt+0xc = SHIFT held now)" % seq)
    return e


def s2_transport(check, J):
    stub_threads()
    e = emu.Emu()
    btn = e.malloc(0x28); e.wr(btn, bytes(0x28)); e.call(BTN_CTOR, btn); e.call(BTN_INIT, btn, 6, 0, 0)
    dm = e.malloc(DM_SIZE); e.wr(dm, bytes(DM_SIZE)); x = e.malloc(0x900); e.wr(x, bytes(0x900)); e.w32(x + 0x81c, dm)
    this = e.malloc(0x40); e.wr(this, bytes(0x40)); e.w32(this + 0x10, x)
    out = []
    for d60, d64 in ((0, -1), (0, 5), (2, -1), (1, 3)):
        e.w32(dm + 0x60, d60); e.w32(dm + 0x64, d64); e.wr(dm + 0x5c, b"\0"); e.wr(dm + 0x68, b"\0")
        trace = []
        for pressed in (1, 0, 1, 0, 1):
            e.call(TRANSPORT_HANDLER, this, btn, pressed)
            trace.append((e.rd(dm + 0x5c, 1)[0], e.rd(dm + 0x68, 1)[0]))
        out.append(((d60, d64), trace))
    J["s2_transport"] = out
    want = {(0, -1): [(1, 0), (0, 0), (1, 0), (0, 0), (1, 0)], (0, 5): [(0, 1), (0, 1), (0, 0), (0, 0), (0, 1)],
            (2, -1): [(1, 0), (0, 0), (1, 0), (0, 0), (1, 0)], (1, 3): [(1, 0), (0, 0), (1, 0), (0, 0), (1, 0)]}
    check(all(want[k] == t for k, t in out), "S2 real TransportController handler 0x%x on a real UIButton id 6, press/release x5, "
          "(DM+0x5c, DM+0x68) after each: %s" % (TRANSPORT_HANDLER, out))


def s2_step(check, J, Pr):
    import H086_ui_manager_calls as H86
    import H077_master_send_proc as H77
    from unicorn import arm_const as A
    rig = H86.Rig(); e = rig.e
    for i_ in range(13): e.setr(i_, 0)
    e.setr(4, 0xf61f18); e.uc.reg_write(emu.SP, emu.STACK_BASE + emu.STACK_SIZE - 0x1000)
    e.uc.emu_start(H77.FRAC_INIT[0], H77.FRAC_INIT[1])                                 # real fraction tables (as H082 C4)
    for a in (0x7c1644, 0x7ccc24, 0x2ee918, 0x2ee9a0, 0x1ea258, 0x392a84): rig.skip(a)
    e.add_watch(0x647ca0, lambda em: (em.setr(0, 0), em.uc.reg_write(A.UC_ARM_REG_PC, em.uc.reg_read(A.UC_ARM_REG_LR))))
    # CFG item 6 := a REAL UIButton (real vtable 0x9313a8, real init with id 6, real setRawState)
    btn = e.malloc(0x28); e.wr(btn, bytes(0x28)); e.call(BTN_CTOR, btn); e.call(BTN_INIT, btn, 6, 0, 0)
    tbl = e.u32(rig.cfg + 8); arr = e.u32(tbl + 4); e.w32(arr + 4 * 6, btn)
    seen = []; stop = []
    def _merge(em):
        seen.append(s32(em.r(0)))
        if stop: em.uc.emu_stop()                       # Insert step-held p-lock path: stop right after m (sequencer not modelled)
    for m_ in MERGE.values(): e.add_watch(m_, _merge)
    ref = rig.ctrl + 0x20
    rows = [("insert", 0, 0, "chorus"), ("insert", 11, 0, "insert_delay"), ("insert", 61, 0, "phaser"), ("insert", 69, 0, "ducker_attack"),
            ("send", 0, 0, "chorus"), ("send", 11, 0, "send_delay"), ("master", 5, 0, "flanger")]
    combos = [(0, -1, 0), (0, -1, 1), (1, -1, 0), (2, 4, 0), (3, 7, 1), (0, 5, 0), (0, 5, 1)]
    n = 0; bad = []; summary = {}
    for ctx, kind, k, fam in rows:
        Fm = SC.FAMILIES[fam]; lo, hi = Fm["free"][1]
        for d60, d64, d68 in combos:
            for shift in (0, 1):
                for i0 in (lo, lo + 1, (lo + hi) // 2, hi - 3):
                    for delta in (1, -1, 3):
                        e.call(BTN_SETRAW, btn, shift)
                        e.w32(rig.dm + 0x60, d60); e.w32(rig.dm + 0x64, d64 & 0xffffffff); e.wr(rig.dm + 0x68, bytes([d68]))
                        e.w32(rig.dm + 0x74, 1 if ctx == "insert" else 0); rig.send_mode = 0 if ctx == "master" else 1
                        v = SC.norm_of(lo, hi, i0)
                        rig.state.update(param=v, sync=0, rng=(lo, hi))
                        del seen[:]
                        held = ctx == "insert" and d60 == 0 and d64 != -1
                        stop[:] = [1] if held else []
                        try:
                            got = rig.run(STEP["insert" if ctx == "insert" else "sendmaster"], ref, k, kind, delta & 0xffffffff)
                        except emu.EmuAbort:
                            if not held: raise
                            got = []
                        fine = bool(d68) if held else bool(shift)
                        m_exp = 1 if fine else s32(e.call(STEP_MULT, kind, i0, delta & 0xffffffff)[0])
                        s27 = [f2u(g["value"]) for g in got if g["off"] == 0x10]
                        exp27 = [] if held else [SC.fbits(SC.norm_of(lo, hi, min(max(i0 + m_exp * delta, lo), hi - 1)))]
                        n += 1
                        ok = seen == [m_exp] and s27 == exp27
                        summary.setdefault((ctx, fam, "held" if held else "normal", fine), set()).add(m_exp)
                        if not ok: bad.append((ctx, fam, d60, d64, d68, shift, i0, delta, seen, m_exp, s27, exp27))
    J["s2_step"] = dict(n=n, bad=[str(b) for b in bad[:10]], m_by_case={"%s/%s/%s/fine=%d" % k_: sorted(v_) for k_, v_ in sorted(summary.items())})
    check(n >= 500 and not bad, "S2 real step routines (Insert 0x316a10, Send/Master 0x313ecc) with CFG item 6 = real UIButton id 6: %d cases "
          "(7 rows x 7 DM+0x60/+0x64/+0x68 combos x SHIFT up/down x 4 start steps x 3 deltas): m observed at the merge point = 1 iff "
          "(Insert and DM+0x60 == 0 and DM+0x64 != -1 ? DM+0x68 : SHIFT held), else 0x311aa0(kind,i,delta); s27 value = (i+m*delta) "
          "normalised (none on the step-held p-lock path): %d bad %s" % (n, len(bad), bad[:2]))
    for k_, v_ in sorted(J["s2_step"]["m_by_case"].items()): Pr("    m %-40s %s" % (k_, v_))
    # alternative: m depends on DM+0x68 also in the normal case / on SHIFT in the held case -> count disagreeing observations
    alt = sum(1 for (ctx, fam, mode, fine), ms in summary.items() if mode == "held" and not fine and 1 in ms)
    check(alt == 0, "S2 alternative 'SHIFT also forces fine while a step is held': refuted if no held/coarse case ever had m = 1 (%d found)" % alt)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=os.path.join(HERE, "out", "H082", "step_mode"))
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rep = []; J = {}; fails = []
    def Pr(s=""): rep.append(s); print(s, flush=True)
    def check(c, msg):
        Pr(("[PASS] " if c else "[FAIL] ") + msg)
        if not c: fails.append(msg)
    im = Image()
    Pr("H082 round 2: fine/coarse step selector. target sha256 %s" % sha(im.data))
    s1_static(im, check, J, Pr)
    s2_button_array(check, J)
    s2_transport(check, J)
    s2_step(check, J, Pr)
    Pr("RESULT: %d failed checks" % len(fails))
    with open(os.path.join(a.out, "step_mode.json"), "w") as f: json.dump(J, f, indent=1, sort_keys=True, default=str)
    with open(os.path.join(a.out, "step_mode_report.txt"), "w") as f: f.write("\n".join(rep) + "\n")
    for nm in ("step_mode_report.txt", "step_mode.json"):
        print("  %s %s" % (nm, sha(open(os.path.join(a.out, nm), "rb").read())))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
