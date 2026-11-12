"""Read-only matching of the active resource enclosing routine and continuation.

Every hook is an original instruction boundary. A before-pop observation alone
does not complete the frame; direct BL, entry, saved caller, restored SP and a
later original caller instruction are recorded separately.
"""
import collections
import struct
import time

from resource_application_observer import caller_transfer

ENTRY = 0x40d6e8
LOCAL_SUB = 0x40d6f8
LOCAL_ADD = 0x40df24
POP = 0x40df28
DIRECT_CALL = 0x322b3c
CALLER = 0x322b40
SUBSEQUENT = 0x322b44
POINTS = {
    ENTRY: 'f04f2de9', LOCAL_SUB: '94d04de2', LOCAL_ADD: '94d08de2',
    POP: 'f08fbde8', DIRECT_CALL: 'e9aa03eb', CALLER: '000054e3',
    SUBSEQUENT: '0600a0e1',
    # Static connection to the observed resource return at 0x40dee4.
    0x40dee0: '0d07feeb',
}


class ActiveEnclosingObserver:
    def __init__(self, emit, started, discovery, clock=time.monotonic):
        self.emit, self.started, self.discovery, self.clock = emit, started, discovery, clock
        self.frames, self.completed, self.continuations = [], [], []
        self.counts = collections.Counter()
        self.installed, self.pending_call = {}, None
        self.pending_continuations = []

    def install(self, q):
        if self.installed:
            raise RuntimeError('Active enclosing observer already installed')
        for address, expected in POINTS.items():
            if self.discovery.expected(address).hex() != expected or bytes(q.mem.read(address, 4)).hex() != expected:
                raise RuntimeError('Active enclosing original bytes differ ' + hex(address))
        kind, target = caller_transfer(DIRECT_CALL, bytes.fromhex(POINTS[DIRECT_CALL]))
        resource_kind, resource_target = caller_transfer(0x40dee0, bytes.fromhex(POINTS[0x40dee0]))
        if kind != 'arm_bl' or target != ENTRY or resource_kind != 'arm_bl' or resource_target != 0x38fb1c:
            raise RuntimeError('Active enclosing direct transfer differs')
        for address in (DIRECT_CALL, ENTRY, POP, CALLER, SUBSEQUENT):
            q.hook_address(lambda guest, address=address: self.checkpoint(guest, address), address)
            self.installed[hex(address)] = POINTS[address]
        self.emit('active_enclosing_hooks_installed', points={hex(a): h for a, h in POINTS.items()},
                  original_app_sha256=self.discovery.app_sha256, caller_transfer=kind,
                  caller_target=hex(target), resource_target=hex(resource_target),
                  main_only=True, read_only=True, scheduling_changes=False)

    def context(self, q):
        return dict(host_elapsed=round(self.clock() - self.started, 6),
                    thread=q.os.thread_management.cur_thread.id,
                    pc=hex(q.arch.regs.arch_pc), sp=hex(q.arch.regs.sp),
                    lr=hex(q.arch.regs.lr), r0=hex(q.arch.regs.r0))

    def checkpoint(self, q, address):
        if self.discovery.main_tid is None or q.os.thread_management.cur_thread.id != self.discovery.main_tid:
            return
        c = self.context(q)
        if address == DIRECT_CALL:
            self.counts['direct_calls'] += 1
            self.pending_call = dict(sp=q.arch.regs.sp, context=c)
            self.emit('active_enclosing_direct_call', context=c, target=hex(ENTRY))
        elif address == ENTRY:
            sp, caller = q.arch.regs.sp, q.arch.regs.lr
            if self.frames and self.frames[-1]['entry_sp'] == sp and self.frames[-1]['caller'] == caller:
                self.counts['duplicate_entries'] += 1
                return
            direct = self.pending_call
            direct_matches = bool(direct and direct['sp'] == sp and caller == CALLER)
            self.pending_call = None
            self.counts['entries'] += 1
            f = dict(sequence=self.counts['entries'], entry=hex(ENTRY), entry_sp=sp, caller=caller,
                     expected_caller_matches=caller == CALLER, direct_call_matches=direct_matches,
                     direct_call_context=direct['context'] if direct else None,
                     entry_context=c, ready=False, pop_observed=False)
            self.frames.append(f)
            if not direct_matches:
                self.counts['entry_call_mismatches'] += 1
            self.emit('active_enclosing_entry', frame=dict(f))
        elif address == POP:
            if not self.frames:
                self.counts['pop_without_frame'] += 1
                self.emit('active_enclosing_pop_without_frame', context=c)
                return
            f = self.frames[-1]
            saved = struct.unpack('<I', bytes(q.mem.read(q.arch.regs.sp + 32, 4)))[0]
            f.update(pop_observed=True, saved_caller=hex(saved),
                     pop_sp_matches=q.arch.regs.sp == f['entry_sp'] - 36,
                     saved_caller_matches=saved == f['caller'] == CALLER,
                     pop_context=c)
            f['ready'] = bool(f['direct_call_matches'] and f['pop_sp_matches'] and f['saved_caller_matches'])
            self.counts['pops'] += 1
            if not f['ready']:
                self.counts['mismatched_pops'] += 1
            self.emit('active_enclosing_before_pop', frame=dict(f))
        elif address == CALLER:
            if not self.frames:
                return
            f = self.frames[-1]
            if not f['pop_observed']:
                self.counts['caller_without_pop'] += 1
                self.emit('active_enclosing_caller_without_pop', context=c, sequence=f['sequence'])
                return
            self.frames.pop()
            f.update(restored_sp_matches=q.arch.regs.sp == f['entry_sp'],
                     matched_return=bool(f['ready'] and q.arch.regs.sp == f['entry_sp']),
                     return_context=c, subsequent_execution_observed=False)
            self.completed.append(f)
            self.counts['matched_returns' if f['matched_return'] else 'unmatched_returns'] += 1
            if f['matched_return']:
                self.pending_continuations.append(f)
            self.emit('active_enclosing_return', result=dict(f))
        elif address == SUBSEQUENT:
            # This hook is reached after the original CMP at CALLER executed.
            # Wrong thread, wrong SP, a before-pop or a sampled PC cannot satisfy it.
            for f in list(self.pending_continuations):
                if q.arch.regs.sp != f['entry_sp']:
                    self.counts['subsequent_sp_mismatches'] += 1
                    self.emit('active_enclosing_subsequent_mismatch', context=c, sequence=f['sequence'])
                    continue
                f.update(subsequent_execution_observed=True, subsequent_context=c)
                self.pending_continuations.remove(f)
                result = dict(sequence=f['sequence'], matched_return=True, entry=hex(ENTRY),
                              caller=hex(CALLER), subsequent=hex(SUBSEQUENT),
                              original_caller_instruction_executed=POINTS[CALLER], context=c)
                self.continuations.append(result)
                self.counts['matched_continuations'] += 1
                self.emit('active_enclosing_subsequent_execution', result=result)

    def summary(self):
        return dict(main_only=True, read_only=True, scheduling_changes=False,
                    counts=dict(self.counts), installed=dict(self.installed),
                    pending_direct_call=self.pending_call, pending_frames=list(self.frames),
                    completed_returns=list(self.completed), continuations=list(self.continuations),
                    relevant_completion_and_continuation_established=bool(self.continuations))
