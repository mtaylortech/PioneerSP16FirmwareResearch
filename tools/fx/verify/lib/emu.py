"""Single-function unicorn emulator for target/EP085_Main_R_fw160 (1.60). Shared by harness/H007_*.py and later cycles.

Loader model (a minimal, explicit dynamic linker):
  * Main ELF PT_LOAD segments are mapped at their 1.60 VAs from the file bytes (read-only file access; target/ is never written).
    Segment permissions are kept (R|X text/rodata is not writable). .bss is zero (loader semantics).
  * Selected real 1.60 shared libraries from decoded/lib/ (default: libm.so.6, libgcc_s.so.1) are mapped at fixed bases and
    relocated (R_ARM_RELATIVE / GLOB_DAT / JUMP_SLOT / ABS32).
  * Every import of the main binary (JUMP_SLOT in .got) and of the loaded libraries is resolved by name, in this order:
      1. an explicit Python stub in STUBS (heap and mem* functions that live in libc/libstdc++/libtcmalloc, which are not loaded);
      2. an export of a loaded real library;
      3. otherwise a *trap*: calling it aborts the run with the trap name, PC and LR.
    Python stubs and unresolved functions sit in a trap page filled with `bx lr`; a code hook runs the stub before `bx lr`.
    Unresolved data imports (GLOB_DAT) point into an unmapped region, so any use faults.
  * R_ARM_COPY ranges in the main .bss (libstdc++/libc data objects copied at load time) are poisoned: any access aborts.
  * Any unmapped / protection fault, interrupt (svc) or instruction-limit hit aborts with the faulting PC.
  * Reads of main .bss words never written during the run are recorded (static-initialiser state we do not model).
VFP/NEON: CPU model Cortex-A9, CPACR cp10/cp11 full access, FPEXC.EN = 1, FPSCR = 0 (Linux default: round-to-nearest, no FZ/DN).
"""
import hashlib, os, struct, bisect, math
import lief
import darwin_ctr_fix
darwin_ctr_fix.install()     # host workaround: unicorn's init reads CTR_EL0, which traps on the owner's Mac (see module doc)
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_UNMAPPED, UC_HOOK_MEM_PROT, \
    UC_HOOK_INTR, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC, UC_PROT_ALL, \
    UC_MEM_READ_UNMAPPED, UC_MEM_WRITE_UNMAPPED, UC_MEM_FETCH_UNMAPPED
from unicorn import arm_const as A

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TARGET = os.path.join(ROOT, "target", "EP085_Main_R_fw160")
LIBDIR = os.path.join(ROOT, "decoded", "lib")
SHA = "3d1392a61323e73ea4f2fddef8fe9e0142add7a6f6fab79ab0eb0d5396555464"

PAGE = 0x1000
TRAP_BASE, TRAP_SIZE = 0x3f000000, 0x10000          # executable `bx lr` slots, one per import name
DATA_TRAP_BASE = 0xdead0000                          # unmapped: unresolved data imports
SENTINEL = 0x3e000000                                # return address for top-level calls
HEAP_BASE, HEAP_SIZE = 0x50000000, 0x04000000
STACK_BASE, STACK_SIZE = 0x7f000000, 0x00100000
LIB_BASES = {"libm.so.6": 0x40000000, "libgcc_s.so.1": 0x41000000}
BX_LR = struct.pack("<I", 0xe12fff1e)

R = [getattr(A, "UC_ARM_REG_R%d" % i) for i in range(13)]
SP, LR, PC = A.UC_ARM_REG_SP, A.UC_ARM_REG_LR, A.UC_ARM_REG_PC


def f2u(x): return struct.unpack("<I", struct.pack("<f", x))[0]
def u2f(u): return struct.unpack("<f", struct.pack("<I", u & 0xffffffff))[0]
def d2u(x): return struct.unpack("<Q", struct.pack("<d", x))[0]
def u2d(u): return struct.unpack("<d", struct.pack("<Q", u))[0]


class EmuAbort(Exception):
    pass


def _pages(lo, hi):
    return lo & ~(PAGE - 1), (hi + PAGE - 1) & ~(PAGE - 1)


class Emu:
    def __init__(self, libs=("libm.so.6", "libgcc_s.so.1"), heap_fill=0, insn_limit=200_000_000, vfp=True):
        data = open(TARGET, "rb").read()
        assert hashlib.sha256(data).hexdigest() == SHA, "target hash mismatch"
        self.elf = lief.parse(TARGET)
        self.uc = uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        uc.ctl_set_cpu_model(A.UC_CPU_ARM_CORTEX_A9)
        self.insn_limit = insn_limit
        self.error = None
        self.hits = {}            # import name -> {"served": str, "count": n, "first_lr": addr}
        self.trap_name = {}       # trap addr -> name
        self.served = {}          # name -> how served
        self.allocs = []          # (addr, size, kind)
        self.frees = []
        self.bss_written = set(); self.bss_rbw = {}   # bss read-before-write: word addr -> first PC
        self.watch = {}           # pc -> callback(emu) (code hooks at chosen addresses)
        self.lib_exports = {}     # name -> addr (with thumb bit)
        self.lib_ranges = []      # (lo, hi, libname)

        # --- main image ---------------------------------------------------------------------------------
        for s in self.elf.segments:
            if s.type != lief.ELF.Segment.TYPE.LOAD: continue
            lo, hi = _pages(s.virtual_address, s.virtual_address + s.virtual_size)
            perm = UC_PROT_READ | (UC_PROT_WRITE if s.has(lief.ELF.Segment.FLAGS.W) else 0) | \
                (UC_PROT_EXEC if s.has(lief.ELF.Segment.FLAGS.X) else 0)
            uc.mem_map(lo, hi - lo, perm)
            uc.mem_write(s.virtual_address, data[s.file_offset:s.file_offset + s.physical_size])
        sec = {x.name: (x.virtual_address, x.virtual_address + x.size) for x in self.elf.sections if x.name}
        self.sec = sec
        self.bss = sec[".bss"]
        self.copy_ranges = sorted((r.address, r.address + max(r.symbol.size, 4), r.symbol.name)
                                  for r in self.elf.dynamic_relocations if "COPY" in str(r.type))
        # --- trap page, sentinel, heap, stack -------------------------------------------------------------
        uc.mem_map(TRAP_BASE, TRAP_SIZE, UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_write(TRAP_BASE, BX_LR * (TRAP_SIZE // 4))
        uc.mem_map(SENTINEL, PAGE, UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_write(SENTINEL, BX_LR * (PAGE // 4))
        uc.mem_map(HEAP_BASE, HEAP_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        if heap_fill:
            uc.mem_write(HEAP_BASE, bytes([heap_fill]) * HEAP_SIZE)
        self.heap_top = HEAP_BASE
        uc.mem_map(STACK_BASE, STACK_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        self._ntrap = 0; self._ndtrap = 0
        # --- real libraries -------------------------------------------------------------------------------
        for name in libs:
            self._load_lib(name, LIB_BASES[name])
        for name in libs:
            self._relocate_lib(name)
        # --- main imports ---------------------------------------------------------------------------------
        for r in self.elf.pltgot_relocations:
            nm = r.symbol.name if r.has_symbol else "?"
            uc.mem_write(r.address, struct.pack("<I", self._resolve_func(nm, "main")))
        for r in self.elf.dynamic_relocations:
            if "GLOB_DAT" in str(r.type):
                uc.mem_write(r.address, struct.pack("<I", self._data_trap(r.symbol.name)))
        # --- CPU state: VFP/NEON on -----------------------------------------------------------------------
        if vfp:
            uc.reg_write(A.UC_ARM_REG_C1_C0_2, uc.reg_read(A.UC_ARM_REG_C1_C0_2) | (0xf << 20))
            uc.reg_write(A.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(A.UC_ARM_REG_FPSCR, 0)
        # --- hooks ----------------------------------------------------------------------------------------
        uc.hook_add(UC_HOOK_CODE, self._h_trap, begin=TRAP_BASE, end=TRAP_BASE + TRAP_SIZE - 1)
        uc.hook_add(UC_HOOK_MEM_UNMAPPED, self._h_unmapped)
        uc.hook_add(UC_HOOK_MEM_PROT, self._h_prot)
        uc.hook_add(UC_HOOK_INTR, self._h_intr)
        uc.hook_add(UC_HOOK_MEM_WRITE, self._h_bss_w, begin=self.bss[0], end=self.bss[1] - 1)
        uc.hook_add(UC_HOOK_MEM_READ, self._h_bss_r, begin=self.bss[0], end=self.bss[1] - 1)
        self._watch_hook = None
        # count every entry into a real-library import the main binary resolved (so the import report covers them too)
        self._real_entry = {}
        for nm, how in self.served.items():
            if how.startswith("real"):
                addr = self.lib_exports[nm][0] & ~1
                self._real_entry.setdefault(addr, nm)
        for addr in self._real_entry:
            uc.hook_add(UC_HOOK_CODE, self._h_real, begin=addr, end=addr)

    # ===================================================================================================
    # loader
    def _load_lib(self, name, base):
        path = os.path.join(LIBDIR, name)
        raw = open(path, "rb").read()
        e = lief.parse(path)
        hi_all = 0
        for s in e.segments:
            if s.type != lief.ELF.Segment.TYPE.LOAD: continue
            lo, hi = _pages(base + s.virtual_address, base + s.virtual_address + s.virtual_size)
            hi_all = max(hi_all, hi)
            try:
                self.uc.mem_map(lo, hi - lo, UC_PROT_ALL)
            except UcError:   # overlapping page with previous segment: already mapped
                pass
            self.uc.mem_write(base + s.virtual_address, raw[s.file_offset:s.file_offset + s.physical_size])
        self.lib_ranges.append((base, hi_all, name))
        self.__dict__.setdefault("_libs", {})[name] = (e, base, hashlib.sha256(raw).hexdigest())
        for s in e.dynamic_symbols:
            if s.shndx != 0 and s.value and s.name and s.name not in self.lib_exports:
                if s.type in (lief.ELF.Symbol.TYPE.FUNC, lief.ELF.Symbol.TYPE.GNU_IFUNC):
                    self.lib_exports[s.name] = (base + s.value, name)

    def _relocate_lib(self, name):
        e, base, _ = self._libs[name]
        for r in list(e.dynamic_relocations) + list(e.pltgot_relocations):
            t = str(r.type); a = base + r.address
            if "RELATIVE" in t:
                v = struct.unpack("<I", self.uc.mem_read(a, 4))[0]
                self.uc.mem_write(a, struct.pack("<I", (v + base) & 0xffffffff))
                continue
            sym = r.symbol if r.has_symbol else None
            nm = sym.name if sym else "?"
            if sym is not None and sym.shndx != 0:            # defined in this lib
                S = base + sym.value
            elif "JUMP_SLOT" in t or (sym is not None and sym.type == lief.ELF.Symbol.TYPE.FUNC):
                S = self._resolve_func(nm, name)
            else:                                             # undefined data / untyped GLOB_DAT, ABS32
                S = self._data_trap(nm)
            if "ABS32" in t:
                v = struct.unpack("<I", self.uc.mem_read(a, 4))[0]
                S = (S + v) & 0xffffffff
            self.uc.mem_write(a, struct.pack("<I", S))

    def _resolve_func(self, nm, who):
        if nm in STUBS:
            self.served[nm] = "python stub: " + STUBS[nm][1]
            return self._trap(nm)
        if nm in self.lib_exports:
            addr, lib = self.lib_exports[nm]
            self.served[nm] = "real 1.60 %s @0x%x" % (lib, addr)
            return addr
        return self._trap(nm)

    def _trap(self, nm):
        for a, n in self.trap_name.items():
            if n == nm: return a
        a = TRAP_BASE + 4 * self._ntrap; self._ntrap += 1
        assert self._ntrap < TRAP_SIZE // 4
        self.trap_name[a] = nm
        return a

    def _data_trap(self, nm):
        a = DATA_TRAP_BASE + 0x10 * self._ndtrap; self._ndtrap += 1
        self.trap_name[a] = "data:" + nm
        return a

    # ===================================================================================================
    # hooks
    def _abort(self, msg):
        if self.error is None:
            self.error = msg
        self.uc.emu_stop()

    def _h_trap(self, uc, addr, size, _):
        nm = self.trap_name.get(addr)
        lr = uc.reg_read(LR)
        if nm is None or nm not in STUBS:
            self._abort("unlisted import %r called (trap 0x%x, LR 0x%x)" % (nm, addr, lr)); return
        h = self.hits.setdefault(nm, {"served": self.served[nm], "count": 0, "first_lr": lr})
        h["count"] += 1
        STUBS[nm][0](self)

    def _h_real(self, uc, addr, size, _):
        nm = self._real_entry[addr]; lr = uc.reg_read(LR)
        h = self.hits.setdefault(nm, {"served": self.served[nm], "count": 0, "first_lr": lr})
        h["count"] += 1

    def _h_unmapped(self, uc, access, addr, size, value, _):
        kind = {UC_MEM_READ_UNMAPPED: "read", UC_MEM_WRITE_UNMAPPED: "write", UC_MEM_FETCH_UNMAPPED: "fetch"}.get(access, access)
        nm = None
        for a, n in self.trap_name.items():
            if a <= addr < a + 0x10 and n.startswith("data:"): nm = n
        self._abort("unmapped %s at 0x%x (size %d) pc=0x%x lr=0x%x%s" % (kind, addr, size, uc.reg_read(PC), uc.reg_read(LR),
                                                                   " [%s]" % nm if nm else ""))
        return False

    def _h_prot(self, uc, access, addr, size, value, _):
        self._abort("protection fault (access %d) at 0x%x pc=0x%x" % (access, addr, uc.reg_read(PC)))
        return False

    def _h_intr(self, uc, intno, _):
        self._abort("interrupt/svc %d at pc=0x%x" % (intno, uc.reg_read(PC)))

    def _copy_hit(self, addr):
        i = bisect.bisect_right(self.copy_ranges, (addr, 0xffffffff, "")) - 1
        if i >= 0 and self.copy_ranges[i][0] <= addr < self.copy_ranges[i][1]:
            return self.copy_ranges[i][2]
        return None

    def _h_bss_w(self, uc, access, addr, size, value, _):
        c = self._copy_hit(addr)
        if c: self._abort("write to R_ARM_COPY import data %s at 0x%x pc=0x%x" % (c, addr, uc.reg_read(PC))); return
        for w in range(addr & ~3, addr + size, 4): self.bss_written.add(w)

    def _h_bss_r(self, uc, access, addr, size, value, _):
        c = self._copy_hit(addr)
        if c: self._abort("read of R_ARM_COPY import data %s at 0x%x pc=0x%x" % (c, addr, uc.reg_read(PC))); return
        w = addr & ~3
        if w not in self.bss_written and w not in self.bss_rbw:
            self.bss_rbw[w] = uc.reg_read(PC)

    def _h_watch(self, uc, addr, size, _):
        cb = self.watch.get(addr)
        if cb: cb(self)

    def add_watch(self, addr, cb):
        """Run cb(emu) before the instruction at addr executes (e.g. to log registers at a call site)."""
        self.watch[addr] = cb
        self.uc.hook_add(UC_HOOK_CODE, self._h_watch, begin=addr, end=addr)

    # ===================================================================================================
    # helpers
    def malloc(self, n, kind="malloc"):
        n = max(int(n), 1)
        a = (self.heap_top + 15) & ~15
        if a + n > HEAP_BASE + HEAP_SIZE: raise EmuAbort("heap exhausted")
        self.heap_top = a + n
        self.allocs.append((a, n, kind))
        return a

    def r(self, i): return self.uc.reg_read(R[i])
    def setr(self, i, v): self.uc.reg_write(R[i], v & 0xffffffff)
    def u32(self, a): return struct.unpack("<I", self.uc.mem_read(a, 4))[0]
    def w32(self, a, v): self.uc.mem_write(a, struct.pack("<I", v & 0xffffffff))
    def f32(self, a): return u2f(self.u32(a))
    def rd(self, a, n): return bytes(self.uc.mem_read(a, n))
    def wr(self, a, b): self.uc.mem_write(a, bytes(b))
    def floats(self, a, n): return list(struct.unpack("<%df" % n, self.rd(a, 4 * n)))
    def set_floats(self, a, xs): self.wr(a, struct.pack("<%df" % len(xs), *xs))
    def sreg(self, i): return self.uc.reg_read(getattr(A, "UC_ARM_REG_S%d" % i))
    def dreg(self, i): return self.uc.reg_read(getattr(A, "UC_ARM_REG_D%d" % i))

    def call(self, addr, *args, stack_args=()):
        """AAPCS call with core-register integer/soft-float args (r0-r3, then stack). Returns (r0, r1)."""
        uc = self.uc
        sp = STACK_BASE + STACK_SIZE - 0x100
        if stack_args:
            sp -= 4 * len(stack_args); sp &= ~7
            for k, v in enumerate(stack_args): self.w32(sp + 4 * k, v)
        regs = list(args)
        assert len(regs) <= 4
        for i, v in enumerate(regs): self.setr(i, v)
        uc.reg_write(SP, sp)
        uc.reg_write(LR, SENTINEL)
        self.error = None
        try:
            uc.emu_start(addr | 0, SENTINEL, count=self.insn_limit)
        except UcError as ex:
            if self.error is None: self.error = "UcError %s pc=0x%x" % (ex, uc.reg_read(PC))
        if self.error is None and uc.reg_read(PC) != SENTINEL:
            self.error = "stopped at pc=0x%x before return (instruction limit %d?)" % (uc.reg_read(PC), self.insn_limit)
        if self.error:
            raise EmuAbort("call 0x%x: %s" % (addr, self.error))
        return self.r(0), self.r(1)

    def vcall(self, obj, slot, *args):
        vt = self.u32(obj)
        return self.call(self.u32(vt + 4 * slot), obj, *args)

    def import_report(self):
        return [(nm, h["served"], h["count"], h["first_lr"]) for nm, h in sorted(self.hits.items())]

    def lib_hashes(self):
        return {n: v[2] for n, v in self._libs.items()}


# =======================================================================================================
# Explicit Python stubs (functions from libc / libstdc++ / libtcmalloc, which are not loaded). Each runs before `bx lr`.
def _ret(e, v): e.setr(0, v)

def _new(e):     _ret(e, e.malloc(e.r(0), "new"))
def _newa(e):    _ret(e, e.malloc(e.r(0), "new[]"))
def _malloc(e):  _ret(e, e.malloc(e.r(0), "malloc"))
def _calloc(e):
    n = e.r(0) * e.r(1); a = e.malloc(n, "calloc"); e.wr(a, b"\0" * n); _ret(e, a)
def _realloc(e):
    p, n = e.r(0), e.r(1); a = e.malloc(n, "realloc")
    if p:
        old = [s for (x, s, k) in e.allocs if x == p]
        if old: e.wr(a, e.rd(p, min(old[-1], n)))
    _ret(e, a)
def _free(e):    e.frees.append(e.r(0))
def _memcpy(e):
    d, s, n = e.r(0), e.r(1), e.r(2)
    if n: e.wr(d, e.rd(s, n))
    _ret(e, d)
def _memset(e):
    d, c, n = e.r(0), e.r(1) & 0xff, e.r(2)
    if n: e.wr(d, bytes([c]) * n)
    _ret(e, d)
def _strlen(e):
    a = e.r(0); n = 0
    while e.rd(a + n, 1) != b"\0": n += 1
    _ret(e, n)

STUBS = {
    "_Znwj": (_new, "operator new(size): bump allocator, no reuse"),
    "_Znaj": (_newa, "operator new[](size): bump allocator"),
    "malloc": (_malloc, "bump allocator"),
    "calloc": (_calloc, "bump allocator + zero fill"),
    "realloc": (_realloc, "bump allocate + copy old block"),
    "free": (_free, "no-op (recorded)"),
    "_ZdlPv": (_free, "operator delete: no-op (recorded)"),
    "_ZdaPv": (_free, "operator delete[]: no-op (recorded)"),
    "memcpy": (_memcpy, "byte copy"),
    "memmove": (_memcpy, "byte copy (via temporary)"),
    "memset": (_memset, "byte fill"),
    "strlen": (_strlen, "byte scan"),
    # only reached from static initialisers (run_static_init); both are irrelevant to DSP state
    "_ZNSt8ios_base4InitC1Ev": (lambda e: None, "std::ios_base::Init ctor (iostreams): no-op"),
    "__aeabi_atexit": (lambda e: _ret(e, 0), "register static dtor: no-op, returns 0"),
}


def init_array(emu):
    lo, hi = emu.sec[".init_array"]
    return [emu.u32(a) for a in range(lo, hi, 4)]
