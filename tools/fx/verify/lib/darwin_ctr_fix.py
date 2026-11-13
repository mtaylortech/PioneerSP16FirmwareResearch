"""Host workaround (macOS arm64 only): emulate `mrs Xt, CTR_EL0` on SIGILL.

On the owner's Mac a user-mode read of the AArch64 cache-type register CTR_EL0 raises SIGILL (checked: a 2-instruction
`mrs x0, ctr_el0; ret` stub dies with SIGILL while `mrs x0, dczid_el0` works). Unicorn 2.1.4's QEMU `init_cache_info()`
executes that instruction on the first mem_map, so the emulator cannot start. This module installs a SA_SIGINFO SIGILL handler that,
only when the faulting instruction is `mrs Xt, ctr_el0` (0xd53b0020 | t), writes a fixed CTR value to Xt and skips the
instruction. Any other SIGILL restores the default action and re-faults (normal crash).

The value reports 64-byte I- and D-cache lines (IminLine = DminLine = 4). QEMU uses these only as the step for host cache
maintenance on its JIT buffer; a step no larger than the real line size (Apple silicon: 64/128 B) is safe. It does not affect
guest (ARMv7) semantics. This is a host-side fix only. It changes nothing in the target, the sandbox or the permissions.
"""
import ctypes, platform, struct, sys

CTR_VALUE = 0x8444c004
_installed = False
_keep = []

# darwin arm64 layouts
# struct __darwin_ucontext: uc_onstack(int@0) uc_sigmask(u32@4) uc_stack(24@8) uc_link(ptr@32) uc_mcsize(@40) uc_mcontext(ptr@48)
# struct __darwin_mcontext64: __es (far u64, esr u32, exception u32 = 16 B), then __ss: x[29] @16, fp @248, lr @256, sp @264, pc @272
_UC_MCONTEXT = 48
_SS_X0 = 16
_SS_PC = 272
SIGILL = 4
SA_SIGINFO = 0x40


class _Sigaction(ctypes.Structure):
    _fields_ = [("handler", ctypes.c_void_p), ("mask", ctypes.c_uint32), ("flags", ctypes.c_int)]


def install():
    global _installed
    if _installed or sys.platform != "darwin" or platform.machine() != "arm64":
        return False
    libc = ctypes.CDLL(None, use_errno=True)
    HANDLER = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p)

    def handler(sig, info, uap):
        mc = ctypes.c_uint64.from_address(uap + _UC_MCONTEXT).value
        pc_addr = mc + _SS_PC
        pc = ctypes.c_uint64.from_address(pc_addr).value
        insn = ctypes.c_uint32.from_address(pc).value
        if (insn & 0xffffffe0) == 0xd53b0020:          # mrs Xt, ctr_el0
            t = insn & 0x1f
            if t != 31:
                ctypes.c_uint64.from_address(mc + _SS_X0 + 8 * t).value = CTR_VALUE
            ctypes.c_uint64.from_address(pc_addr).value = pc + 4
            return
        dfl = _Sigaction(0, 0, 0)                       # SIG_DFL: let the real fault crash the process
        libc.sigaction(SIGILL, ctypes.byref(dfl), None)

    cb = HANDLER(handler)
    _keep.append(cb)
    act = _Sigaction(ctypes.cast(cb, ctypes.c_void_p).value, 0, SA_SIGINFO)
    libc.sigaction.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
    rc = libc.sigaction(SIGILL, ctypes.byref(act), None)
    if rc != 0:
        raise OSError(ctypes.get_errno(), "sigaction failed")
    _installed = True
    return True
