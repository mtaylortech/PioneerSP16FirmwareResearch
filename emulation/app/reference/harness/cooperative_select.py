"""ARM32 Linux select: readiness now, cooperative wait only after context save."""
import errno
import select
import struct
import time
from gevent.select import select as cooperative_wait
from unicorn.arm_const import UC_ARM_REG_R0


def signed32(value):
    return struct.unpack('<i', struct.pack('<I', value & 0xffffffff))[0]


class CooperativeSelect:
    def __init__(self, emit, names, wait=cooperative_wait, poll=select.select):
        self.emit, self.names, self.wait, self.poll = emit, names, wait, poll
        self.counts = {}; self.states = {}; self.seen = {}

    def record(self, tid, phase, row, verbose):
        self.counts[phase] = self.counts.get(phase, 0) + 1
        self.states[tid] = dict(phase=phase, **row)
        if verbose:
            self.emit('select_wait_state', thread=tid, thread_name=self.names.get(tid), phase=phase, **row)

    def install(self, q):
        q.os.set_syscall('_newselect', self.call)
        self.emit('cooperative_select_registered', syscall='_newselect', context_contract='emu_stop; installed thread.save; sched_cb; saved r0 completion', pacing_enabled=False)

    def call(self, q, nfds, readfds, writefds, exceptfds, timeout):
        begin = time.monotonic(); tid = q.os.thread_management.cur_thread.id
        nfds = signed32(nfds)
        if nfds < 0:
            return -errno.EINVAL
        nfds = min(nfds, len(q.os.fd))  # Linux caps to descriptor table capacity.
        size = ((nfds + 31) // 32) * 4
        ptrs = (readfds, writefds, exceptfds)
        pairs = []; tv = None
        try:
            if timeout:
                sec, usec = struct.unpack('<ii', bytes(q.mem.read(timeout, 8)))
                if sec < 0 or usec < 0:
                    return -errno.EINVAL
                tv = sec + usec / 1000000.0  # Linux normalizes tv_usec >= 1e6.
            for ptr in ptrs:
                raw = bytes(q.mem.read(ptr, size)) if ptr and size else b''
                selected = []
                for fd in range(nfds):
                    if raw and raw[fd // 8] & (1 << (fd % 8)):
                        entry = q.os.fd[fd]
                        if entry is None:
                            return -errno.EBADF
                        try: hostfd = entry.fileno()
                        except (OSError, ValueError, AttributeError): return -errno.EBADF
                        if hostfd < 0:
                            return -errno.EBADF
                        selected.append((fd, hostfd))
                pairs.append(selected)
        except (struct.error, Exception) as ex:
            # Only guest-memory accesses above are allowed to reach this path.
            self.emit('select_argument_error', thread=tid, error=repr(ex))
            return -errno.EFAULT
        hosts = [list(dict.fromkeys(h for _, h in group)) for group in pairs]
        args = dict(nfds=nfds, pointers=[hex(p) for p in ptrs], guest_fds=[[f for f, _ in g] for g in pairs],
                    host_fds=hosts, timeout_pointer=hex(timeout), timeout_seconds=tv,
                    timeout_bytes=bytes(q.mem.read(timeout, 8)).hex() if timeout else None)
        key = (tid, tuple(tuple(f for f, _ in g) for g in pairs), tv)
        self.seen[key] = self.seen.get(key, 0) + 1
        verbose = self.seen[key] <= 3
        self.record(tid, 'handler_entry', args, verbose)

        def finish(ready, result=None):
            elapsed = time.monotonic() - begin
            if result is None:
                result = 0
                for ptr, group, selected in zip(ptrs, pairs, ready):
                    if ptr and size:
                        out = bytearray(size)
                        for fd, hostfd in group:
                            if hostfd in selected:
                                out[fd // 8] |= 1 << (fd % 8); result += 1
                        q.mem.write(ptr, bytes(out))
            if timeout:
                remain = max(0.0, tv - elapsed)
                micros = int(remain * 1000000)
                q.mem.write(timeout, struct.pack('<ii', micros // 1000000, micros % 1000000))
            return result, elapsed

        def host_error(ex):
            return -getattr(ex, 'errno', None) if getattr(ex, 'errno', None) else -errno.EBADF if isinstance(ex, ValueError) else -errno.EIO

        try: ready = self.poll(*hosts, 0)
        except (OSError, ValueError) as ex:
            result, elapsed = finish(([], [], []), host_error(ex))
            self.record(tid, 'immediate_error', dict(arguments=args, result=result, host_seconds=elapsed, error=repr(ex)), True)
            return result
        if any(ready) or tv == 0:
            result, elapsed = finish(ready)
            self.record(tid, 'immediate_completion', dict(arguments=args, result=result, host_seconds=elapsed), verbose)
            return result
        thread = q.os.thread_management.cur_thread
        q.emu_stop()

        def deferred(current):
            if current is not thread or current.saved_context is None:
                raise RuntimeError('select wait requires the calling thread saved context')
            self.record(tid, 'deferred_wait_begin', dict(arguments=args, saved_context=True), verbose)
            try:
                # No emulated registers are live here. The scheduler saved this
                # context before invoking us; other threads may now run.
                ready = self.wait(*hosts, None if tv is None else max(0.0, tv - (time.monotonic() - begin)))
                result, elapsed = finish(ready)
            except (OSError, ValueError) as ex:
                result, elapsed = finish(([], [], []), host_error(ex))
            current.saved_context.reg_write(UC_ARM_REG_R0, result & 0xffffffff)
            self.record(tid, 'deferred_completion', dict(arguments=args, result=result, host_seconds=elapsed,
                        wake_source='descriptor_ready' if result > 0 else 'timeout' if result == 0 else 'host_errno',
                        saved_return_r0=hex(current.saved_context.reg_read(UC_ARM_REG_R0)), context_updated=True), verbose)
        thread.sched_cb = deferred
        self.record(tid, 'handler_return_pending', dict(arguments=args, result_placeholder=0, deferred_complete=False), verbose)
        return 0

    def summary(self):
        return dict(enabled=True, counts=self.counts, thread_states=self.states, contract='ARM32; deferred saved-context completion')
