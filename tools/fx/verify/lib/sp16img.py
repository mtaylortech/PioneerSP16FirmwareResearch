"""Shared static helpers for target/EP085_Main_R_fw160 (1.60). Read-only; asserts the target SHA-256.

Image: raw file words by VA, segment mapping, PLT stub -> import name (from .rel.plt JUMP_SLOT order),
.ARM.exidx function starts (extent = next start), and a whole-.text scan of direct ARM bl/blx/b immediates."""
import bisect, hashlib, os, struct
import capstone, lief

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TARGET = os.path.join(ROOT, "target", "EP085_Main_R_fw160")
SHA = "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"


class Image:
    def __init__(self, path=TARGET):
        self.data = open(path, "rb").read()
        assert hashlib.sha256(self.data).hexdigest() == SHA, "target hash mismatch"
        self.elf = lief.parse(path)
        self.segs = [(p.virtual_address, p.physical_size, p.file_offset)
                     for p in self.elf.segments if p.type == lief.ELF.Segment.TYPE.LOAD]
        self.sec = {s.name: (s.virtual_address, s.virtual_address + s.size) for s in self.elf.sections if s.name}
        self.md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
        self.md.detail = False
        self._plt = None; self._starts = None; self._calls = None

    def off(self, va):
        for v, sz, o in self.segs:
            if v <= va < v + sz:
                return o + va - v
        return None

    def u32(self, va):
        o = self.off(va)
        return None if o is None else struct.unpack_from("<I", self.data, o)[0]

    def cstr(self, va, n=200):
        o = self.off(va)
        if o is None: return None
        e = self.data.find(b"\0", o, o + n)
        return self.data[o:e if e >= 0 else o + n].decode("latin1")

    # --- PLT -------------------------------------------------------------------------------------------
    def plt(self):
        """{stub_va: name}. Each 12-byte ARM PLT stub loads its GOT slot; map GOT slot -> JUMP_SLOT symbol."""
        if self._plt is not None: return self._plt
        got2name = {}
        for r in self.elf.pltgot_relocations:
            got2name[r.address] = r.symbol.name if r.has_symbol else "?"
        lo, hi = self.sec[".plt"]
        res = {}
        rot = lambda w: ((w & 0xff) >> (2 * ((w >> 8) & 0xf)) | (w & 0xff) << (32 - 2 * ((w >> 8) & 0xf))) & 0xffffffff \
            if (w >> 8) & 0xf else w & 0xff
        for va in range(lo, hi - 8, 4):
            a, b, c = self.u32(va), self.u32(va + 4), self.u32(va + 8)
            # e28fc6xx add ip,pc,#imm ; e28ccaxx add ip,ip,#imm ; e5bcfxxx ldr pc,[ip,#imm]!
            if (a & 0xfffff000) == 0xe28fc000 and (b & 0xfffff000) == 0xe28cc000 and (c & 0xfffff000) == 0xe5bcf000:
                v = (va + 8 + rot(a) + rot(b) + (c & 0xfff)) & 0xffffffff
                if v in got2name: res[va] = got2name[v]
        self._plt = res
        return res

    # --- function starts ----------------------------------------------------------------------------
    def starts(self):
        if self._starts is not None: return self._starts
        lo, hi = self.sec[".ARM.exidx"]; s = []
        for x in range(lo, hi, 8):
            o = self.u32(x) & 0x7fffffff; o = o - 0x80000000 if o & 0x40000000 else o
            s.append((x + o) & 0xffffffff)
        self._starts = sorted(set(s)); return self._starts

    def func_of(self, va):
        s = self.starts(); i = bisect.bisect_right(s, va) - 1
        return (s[i], s[i + 1]) if 0 <= i < len(s) - 1 else (None, None)

    def disasm(self, va, end):
        return list(self.md.disasm(self.data[self.off(va):self.off(end)], va))

    # --- direct calls ---------------------------------------------------------------------------------
    def direct_calls(self):
        """List of (site, target, kind) for every aligned ARM word in .text that encodes bl/blx(imm)/b(cond) imm24.
        Purely bit-pattern based (fast); data words inside .text can produce false positives, so callers should
        check results against capstone at the site if they matter."""
        if self._calls is not None: return self._calls
        lo, hi = self.sec[".text"]; o0 = self.off(lo); n = (hi - lo) // 4
        words = struct.unpack_from("<%dI" % n, self.data, o0); out = []
        for i, w in enumerate(words):
            site = lo + 4 * i; cond = w >> 28; op = (w >> 24) & 0xf
            if op not in (0xa, 0xb): continue
            imm = w & 0xffffff; imm = imm - 0x1000000 if imm & 0x800000 else imm
            if cond == 0xf:   # blx imm (switches to thumb) - H bit = bit 24
                tgt = site + 8 + imm * 4 + ((w >> 23) & 2); kind = "blx"
            else:
                tgt = site + 8 + imm * 4; kind = "bl" if op == 0xb else "b"
            out.append((site, tgt & 0xffffffff, kind))
        self._calls = out; return out


def annotate(im, va, end=None, n=None):
    """Capstone listing of [va,end) (end defaults to next .ARM.exidx start) with annotations: PLT import names for
    direct branches, literal-pool words for `ldr Rx,[pc,#]` and the C string they point to when printable."""
    import re
    if end is None:
        end = im.func_of(va)[1] if im.func_of(va)[0] == va else im.starts()[__import__("bisect").bisect_right(im.starts(), va)]
    plt = im.plt(); L = []
    for i in im.disasm(va, end):
        t = "0x%x: %s %s" % (i.address, i.mnemonic, i.op_str)
        m = re.match(r"#(0x[0-9a-f]+)$", i.op_str)
        if i.mnemonic.startswith("b") and m:
            tg = int(m.group(1), 16)
            if tg in plt: t += "    ; <%s>" % plt[tg]
        m = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]", i.op_str)
        if i.mnemonic.startswith("ldr") and m:
            lit = i.address + 8 + int(m.group(2), 0); v = im.u32(lit)
            if v is not None:
                t += "    ; =0x%x" % v
                s = im.cstr(v, 80) if im.off(v) is not None else None
                if s and len(s) >= 3 and all(32 <= ord(c) < 127 for c in s): t += ' "%s"' % s
        L.append(t)
        if n and len(L) >= n: break
    return L


def const_sites(im, values):
    """{value: [site,...]} for each value materialised in .text either as an aligned literal-pool word or by an ARM
    movw/movt pair on the same register (movt within 8 instructions after movw). Bit-pattern scan, deterministic."""
    vals = set(values); res = {v: [] for v in vals}
    lo, hi = im.sec[".text"]; o0 = im.off(lo); n = (hi - lo) // 4
    W = struct.unpack_from("<%dI" % n, im.data, o0)
    for i, w in enumerate(W):
        if w in vals: res[w].append(("lit", lo + 4 * i))
        if (w & 0x0ff00000) == 0x03000000 and (w >> 28) != 0xf:       # movw
            rd = (w >> 12) & 0xf; lo16 = ((w >> 4) & 0xf000) | (w & 0xfff)
            for j in range(i + 1, min(i + 9, n)):
                x = W[j]
                if (x & 0x0ff00000) == 0x03400000 and ((x >> 12) & 0xf) == rd:   # movt same rd
                    v = (((x >> 4) & 0xf000) | (x & 0xfff)) << 16 | lo16
                    if v in vals: res[v].append(("movw", lo + 4 * i))
                    break
    return res


def litadd_sites(im, values, lo=None, hi=None, window=12):
    """Sites where `ldr rX,[pc,#]` loads literal L and an `add rY, rX, #imm` within `window` instructions yields
    L+imm in `values` (vtable pointers built from a shared literal base). Returns {value: [(ldr_site, add_site)]}."""
    import re
    vals = set(values); res = {v: [] for v in vals}
    lo = lo or im.sec[".text"][0]; hi = hi or im.sec[".text"][1]
    ins = im.disasm(lo, hi); regs = {}
    for k, i in enumerate(ins):
        m = re.match(r"(\w+), \[pc, #(-?0x[0-9a-f]+|-?\d+)\]$", i.op_str)
        if i.mnemonic == "ldr" and m:
            regs[m.group(1)] = (im.u32(i.address + 8 + int(m.group(2), 0)), k, i.address); continue
        m = re.match(r"(\w+), (\w+), #(0x[0-9a-f]+|\d+)$", i.op_str)
        if i.mnemonic == "add" and m and m.group(2) in regs:
            L, k0, a0 = regs[m.group(2)]
            if L is not None and k - k0 <= window and ((L + int(m.group(3), 0)) & 0xffffffff) in vals:
                res[(L + int(m.group(3), 0)) & 0xffffffff].append((a0, i.address))
    return res
