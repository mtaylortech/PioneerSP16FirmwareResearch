"""Sparse read-only original libc fseek contention and selected futex evidence."""
import collections
import hashlib
import struct
import time
from pathlib import Path

from elftools.elf.elffile import ELFFile
from unicorn.arm_const import UC_ARM_REG_C13_C0_3

LIBC_SHA256 = "f6f89d7ff0cba74f683db6eee7b9a08231eb3501113ba831755ddbc88b8c6288"
BUSY = 0x621a0
LOCK_HELPER = 0xd0a70
FILE_LOCK = 0x48
TLS_SELF_DELTA = 0x4c0
# These are validation points, not installed hooks.
LAYOUT_POINTS = (0x62084, 0x62088, 0x6208c, 0x62090, 0x64d7c, BUSY)


class StdioLockObserver:
    def __init__(self, emit, started, discovery, libc_path):
        self.emit, self.started, self.discovery = emit, started, discovery
        self.libc_path = Path(libc_path)
        self.libc_sha256 = hashlib.sha256(self.libc_path.read_bytes()).hexdigest()
        if self.libc_sha256 != LIBC_SHA256:
            raise RuntimeError("Original stdio libc identity differs")
        with self.libc_path.open("rb") as source:
            elf = ELFFile(source)
            self.segments = [(s["p_vaddr"], s.data()) for s in elf.iter_segments() if s["p_type"] == "PT_LOAD"]
        self.base = None
        self.validated = {}
        self.counts = collections.Counter()
        self.locks = {}
        self.pending = {}
        self.last_emitted = {}
        self.errors = []

    def expected(self, offset, size=4):
        for start, data in self.segments:
            if start <= offset and offset+size <= start+len(data):
                return data[offset-start:offset-start+size]
        raise RuntimeError("Stdio validation point outside original libc")

    def install(self, q):
        candidates = set()
        for start, end, permissions, label, *_ in q.mem.map_info:
            if "libc-2.13" not in label and "libc.so.6" not in label:
                continue
            try:
                if bytes(q.mem.read(start, 16)) == self.expected(0, 16):
                    candidates.add(start)
            except Exception:
                continue
        if len(candidates) != 1:
            raise RuntimeError("Unique loaded original libc ELF mapping required")
        base = candidates.pop()
        checked = {}
        for offset in LAYOUT_POINTS:
            expected = self.expected(offset)
            if bytes(q.mem.read(base+offset, 4)) != expected:
                raise RuntimeError("Loaded stdio observation bytes differ "+hex(base+offset))
            checked[hex(base+offset)] = expected.hex()
        word = struct.unpack("<I", self.expected(BUSY))[0]
        displacement = word & 0xffffff
        if displacement & 0x800000:
            displacement -= 0x1000000
        if word & 0xff000000 != 0xeb000000 or BUSY+8+4*displacement != LOCK_HELPER:
            raise RuntimeError("Original fseek contention BL target differs")
        self.base, self.validated = base, checked
        q.hook_address(self.contention, base+BUSY)
        self.emit("stdio_lock_observer_installed", libc_sha256=self.libc_sha256,
                  libc_base=hex(base), validated_bytes=checked,
                  hook=hex(base+BUSY), read_only=True,
                  scope="main pending-font-scan fseek contention; selected lock futex wait/wake")

    def main_scan(self, q):
        return (self.discovery.main_tid is not None
                and q.os.thread_management.cur_thread.id == self.discovery.main_tid
                and "original_font_scan" in self.discovery.frames)

    def context(self, q):
        current = q.os.thread_management.cur_thread
        tls = q.arch.regs.c13_c0_3
        return {"host_elapsed": round(time.monotonic()-self.started, 6),
                "thread": current.id, "pc": hex(q.arch.regs.arch_pc),
                "lr": hex(q.arch.regs.lr), "sp": hex(q.arch.regs.sp),
                "current_tls_register": hex(tls),
                "current_self_from_tls": hex((tls-TLS_SELF_DELTA) & 0xffffffff)}

    def lock_words(self, q, address):
        lock, count, owner = struct.unpack("<III", bytes(q.mem.read(address, 12)))
        return {"lock_address": hex(address), "lock": lock,
                "recursive_count": count, "owner": hex(owner)}

    def thread_candidates(self, q):
        tm = q.os.thread_management
        known = list(tm.threads)
        if tm.main_thread not in known:
            known.append(tm.main_thread)
        rows = []
        for thread in known:
            if thread is None:
                continue
            row = {"thread": thread.id, "status": str(thread.status)}
            tls = getattr(thread, "tls", None)
            if isinstance(tls, int):
                row.update(stored_tls=hex(tls), stored_self=hex((tls-TLS_SELF_DELTA) & 0xffffffff))
            try:
                if thread.saved_context is not None:
                    saved = thread.saved_context.reg_read(UC_ARM_REG_C13_C0_3)
                    row.update(saved_tls=hex(saved), saved_self=hex((saved-TLS_SELF_DELTA) & 0xffffffff))
            except Exception as error:
                row["saved_tls_error"] = repr(error)
            rows.append(row)
        return sorted(rows, key=lambda row: row["thread"])

    def sparse_emit(self, kind, key, **row):
        now = time.monotonic()
        self.counts[kind] += 1
        count = self.counts[kind]
        if count <= 3 or now-self.last_emitted.get(key, 0) >= 5:
            self.last_emitted[key] = now
            self.emit(kind, count=count, **row)

    def contention(self, q):
        if not self.main_scan(q):
            return
        try:
            file_pointer, lock_pointer = q.arch.regs.r4, q.arch.regs.r0
            actual_lock = q.mem.read_ptr(file_pointer+FILE_LOCK)
            if actual_lock != lock_pointer:
                raise RuntimeError("fseek FILE lock pointer/register mismatch")
            words = self.lock_words(q, lock_pointer)
            candidates = self.thread_candidates(q)
            owner = words["owner"]
            row = {"file_pointer": hex(file_pointer), "file_descriptor": q.mem.read_ptr(file_pointer+0x38),
                   "lock_words": words, "context": self.context(q),
                   "register_self": hex(q.arch.regs.r7),
                   "register_self_matches_tls": q.arch.regs.r7 == (q.arch.regs.c13_c0_3-TLS_SELF_DELTA) & 0xffffffff,
                   "thread_self_candidates": candidates,
                   "owner_matches_threads": [r["thread"] for r in candidates if owner in (r.get("stored_self"), r.get("saved_self"))],
                   "scan_face": self.discovery.ft_pending.get("scan", {}).get("path")}
            self.locks[lock_pointer] = row
            self.sparse_emit("stdio_fseek_contention", ("contention", lock_pointer), **row)
        except Exception as error:
            self.errors.append(repr(error))
            self.emit("stdio_lock_observation_error", error=repr(error))

    def syscall_enter(self, name="futex"):
        def callback(q, *values):
            if name != "futex" or len(values) < 3:
                return
            address, op, value = values[:3]
            operation = op & 0x7f
            if address not in self.locks or operation not in (0, 1, 9, 10):
                return
            try:
                row = {"address": hex(address), "operation": op,
                       "operation_kind": "wait" if operation in (0, 9) else "wake", "value": value,
                       "arguments": list(values), "context": self.context(q),
                       "lock_words": self.lock_words(q, address)}
                tid = q.os.thread_management.cur_thread.id
                self.pending[tid] = row
                self.sparse_emit("stdio_selected_futex_enter", ("futex", address, tid, operation), **row)
            except Exception as error:
                self.errors.append(repr(error))
                self.emit("stdio_lock_observation_error", error=repr(error))
        return callback

    def syscall_exit(self, name="futex"):
        def callback(q, *values):
            if name != "futex":
                return
            tid = q.os.thread_management.cur_thread.id
            row = self.pending.pop(tid, None)
            if row is not None:
                self.sparse_emit("stdio_selected_futex_exit", ("exit", row["address"], tid),
                                 entry=row, result=values[-1] if values else None, context=self.context(q),
                                 note="held futex wait return0 precedes deferred gevent Event.wait; not evidence of wake")
        return callback

    def summary(self):
        return {"read_only": True, "scheduling_changes": False,
                "libc_sha256": self.libc_sha256, "libc_base": hex(self.base) if self.base is not None else None,
                "validated_bytes": self.validated, "counts": dict(self.counts),
                "selected_locks": {hex(k): v for k, v in self.locks.items()},
                "pending_selected_syscalls": self.pending, "errors": self.errors}
