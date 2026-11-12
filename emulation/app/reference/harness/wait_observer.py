"""Sparse wait receipts; delegates every installed futex/timing operation."""
import collections
import struct
import time
from qiling.const import QL_INTERCEPT
from qiling.os.posix.syscall.futex import ql_syscall_futex
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_R0


def compose_syscall(q, name, callback, intercept):
    key = 'ql_syscall_' + name
    hooks = q.os.posix_syscall_hooks[intercept]
    old = hooks.get(key)
    if old is None:
        q.os.set_syscall(name, callback, intercept)
    else:
        def combined(guest, *args):
            previous = old(guest, *args)
            if previous is not None:
                raise RuntimeError('observational composition requires no argument/result override')
            return callback(guest, *args)
        q.os.set_syscall(name, combined, intercept)


class WaitObserver:
    def __init__(self, emit):
        self.handler = ql_syscall_futex; self.timing_enforced = lambda *unused: False
        self.emit = emit; self.names = {}; self.states = {}; self.seen = collections.Counter()
        self.counts = collections.Counter(); self.wakes = {}; self.clocks = {}

    def name(self, q, option, arg2, arg3, arg4, arg5):
        if option == 15:
            tid = q.os.thread_management.cur_thread.id
            self.names[tid] = q.mem.string(arg2)
            self.emit('thread_name', thread=tid, name=self.names[tid], naming_only=True, pacer_name_delivery=False)

    def record(self, tid, phase, row, verbose):
        self.counts[phase] += 1; self.states[tid] = dict(phase=phase, thread_name=self.names.get(tid), **row)
        if verbose:
            self.emit('futex_wait_state', thread=tid, thread_name=self.names.get(tid), phase=phase, **row)

    def install(self, q):
        compose_syscall(q, 'prctl', self.name, QL_INTERCEPT.ENTER)
        compose_syscall(q, 'clock_gettime', self.clock, QL_INTERCEPT.EXIT)
        q.os.set_syscall('futex', self.futex)
        original = q.os.futexm.get_futex_wake_list
        def wake_list(guest, addr, number, bitset=0xffffffff):
            selected = original(guest, addr, number, bitset)
            source = guest.os.thread_management.cur_thread.id
            for target, event in selected:
                self.wakes[target.id] = dict(thread=source, thread_name=self.names.get(source), address=hex(addr), bitset=hex(bitset), selected_monotonic=time.monotonic())
            return selected
        q.os.futexm.get_futex_wake_list = wake_list
        self.emit('wait_observers_registered', futex='installed handler and unchanged sched_cb wrapped', names='prctl ENTER only; no pacer notification', clock='EXIT read-only', timing_repairs=False)

    def clock(self, q, clockid, pointer, result):
        tid = q.os.thread_management.cur_thread.id
        if result == 0:
            sec, nanos = struct.unpack('<ii', bytes(q.mem.read(pointer, 8)))
            row = dict(clockid=clockid, raw=bytes(q.mem.read(pointer, 8)).hex(), seconds=sec, nanoseconds_field=nanos)
            if (tid, clockid) not in self.clocks:
                self.emit('first_guest_clock', thread=tid, thread_name=self.names.get(tid), **row)
            self.clocks[(tid, clockid)] = row

    def futex(self, q, uaddr, op, val, timeout, uaddr2, val3):
        tid = q.os.thread_management.cur_thread.id; command = op & 127
        row = dict(operation=op, command=command, address=hex(uaddr), value=val, bitset=hex(val3),
                   private=bool(op & 128), clock_realtime=bool(op & 256), timeout_pointer=hex(timeout),
                   timeout_bytes=None, relative_seconds=None, absolute_guest_deadline=None,
                   deadline_semantics='relative' if command == 0 else 'absolute' if command == 9 else None,
                   pc=hex(q.arch.regs.arch_pc), lr=hex(q.arch.regs.lr))
        if timeout and command in (0, 9):
            raw = bytes(q.mem.read(timeout, 8)); sec, nanos = struct.unpack('<ii', raw)
            row['timeout_bytes'] = raw.hex(); row['timespec'] = [sec, nanos]
            row['relative_seconds' if command == 0 else 'absolute_guest_deadline'] = sec + nanos / 1000000000
            row['clockid'] = 0 if op & 256 else 1 if command == 9 else None
            if command == 0: row['observational_host_deadline'] = time.monotonic() + row['relative_seconds']
            elif (tid, row['clockid']) in self.clocks: row['last_guest_clock'] = self.clocks[(tid, row['clockid'])]
        key = (tid, uaddr, op, bool(timeout), val3 if command == 9 else None)
        self.seen[key] += 1; verbose = self.seen[key] <= 3
        begin = time.monotonic(); self.record(tid, 'handler_entry', row, verbose)
        thread = q.os.thread_management.cur_thread; before = thread.sched_cb
        result = self.handler(q, uaddr, op, val, timeout, uaddr2, val3)
        pending = thread.sched_cb is not before
        enforced = self.timing_enforced(q, op, timeout)
        self.record(tid, 'handler_return', dict(arguments=row, result=result, deferred_pending=pending,
                    handler_seconds=time.monotonic()-begin), verbose)
        if pending:
            callback = thread.sched_cb
            def deferred(current):
                self.record(tid, 'deferred_begin', dict(arguments=row, saved_context=current.saved_context is not None,
                            timeout_enforced_by_installed_handler=enforced if command in (0, 9) else None), verbose)
                callback(current)
                resumed = dict(pc=hex(current.saved_context.reg_read(UC_ARM_REG_PC)), r0=hex(current.saved_context.reg_read(UC_ARM_REG_R0)))
                self.record(tid, 'deferred_completion', dict(arguments=row, duration=time.monotonic()-begin,
                            wake_source=self.wakes.pop(tid, None), resumed_saved_state=resumed), verbose)
            thread.sched_cb = deferred
        return result

    def summary(self):
        return dict(enabled=True, names=self.names, counts=dict(self.counts), thread_states=self.states,
                    timing_behavior_unchanged=False, correction_scope="named Juce Timer and ProjectManager finite relative WAIT only", pacing_name_hook_enabled=False)
