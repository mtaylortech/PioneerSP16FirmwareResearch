"""Sparse read-only main layout wrapper/getter frames and actual caller returns.

Getter entries are prospective until a matched layout wrapper return establishes
the observed call chain. Conditional POP callbacks only count when CPSR Z is set.
No guest state, scheduler, syscall stop or translation cache is changed here.
"""
import collections
import struct
import time

PREFIX = '/root/gui/Resource/skin16/layout/'
WRAPPER_ENTRY = 0x646364
WRAPPER_CONDITIONAL_POP = 0x646374
WRAPPER_NORMAL_POP = 0x646388
GETTER_ENTRY = 0x4f55f0
GETTER_POP = 0x4f562c
GETTER_CALL = 0x4f56c0
GETTER_CALLER = 0x4f56c4
POINT_BYTES = {
    WRAPPER_ENTRY: bytes.fromhex('10402de9'),
    0x64636c: bytes.fromhex('0ffeffeb'),
    WRAPPER_CONDITIONAL_POP: bytes.fromhex('1080bd08'),
    WRAPPER_NORMAL_POP: bytes.fromhex('1080bde8'),
    GETTER_ENTRY: bytes.fromhex('f04f2de9'),
    0x4f55f8: bytes.fromhex('84d04de2'),
    0x4f5628: bytes.fromhex('84d08de2'),
    GETTER_POP: bytes.fromhex('f08fbde8'),
    GETTER_CALL: bytes.fromhex('274305eb'),
    GETTER_CALLER: bytes.fromhex('008050e2'),
}


def caller_transfer(address, data):
    instruction = struct.unpack('<I', data)[0]
    if (instruction >> 24) & 0xf == 0xb and instruction >> 28 != 0xf:
        offset = instruction & 0xffffff
        if offset & 0x800000:
            offset -= 0x1000000
        return 'arm_bl', (address + 8 + offset * 4) & 0xffffffff
    if instruction & 0x0ffffff0 == 0x012fff30:
        return 'arm_blx_register', None
    return 'unresolved_transfer', None


class LayoutChainObserver:
    def __init__(self, emit, started, discovery):
        self.emit = emit
        self.started = started
        self.discovery = discovery
        self.installed = {}
        self.observation_handles = []
        self.wrapper_frames = []
        self.getter_frames = []
        self.completed_wrappers = []
        self.completed_getters = []
        self.counts = collections.Counter()
        self.path_counts = collections.Counter()
        self.wrapper_caller_counts = collections.Counter()
        self.getter_caller_counts = collections.Counter()
        self.seen = set()
        self.read_errors = []
        self.frame_sequence = 0
        self.gate_observed = False
        self.getter_wrapper_caller_confirmed = False

    def gate(self, q):
        return (self.discovery.main_tid is not None
                and q.os.thread_management.cur_thread.id == self.discovery.main_tid
                and any(row.get('entry') == '0x71ce28' and row.get('matched_return')
                        for row in self.discovery.completed))

    def context(self, q):
        return {'host_elapsed': round(time.monotonic() - self.started, 6),
                'thread': q.os.thread_management.cur_thread.id,
                'pc': hex(q.arch.regs.arch_pc), 'lr': hex(q.arch.regs.lr),
                'sp': hex(q.arch.regs.sp)}

    def checked_bytes(self, q, address):
        expected = self.discovery.expected(address)
        if bytes(q.mem.read(address, 4)) != expected:
            raise RuntimeError('Layout chain loaded bytes differ ' + hex(address))
        return expected

    def install_point(self, q, address, name):
        expected = self.checked_bytes(q, address)
        if address in self.installed:
            if name not in self.installed[address]['roles']:
                self.installed[address]['roles'].append(name)
            return
        self.installed[address] = {'roles': [name], 'bytes': expected.hex()}
        self.observation_handles.append(q.hook_address(lambda guest: self.checkpoint(guest, address), address))

    def install(self, q):
        if self.installed:
            raise RuntimeError('Layout chain observer already installed')
        for address, expected in POINT_BYTES.items():
            if self.checked_bytes(q, address) != expected:
                raise RuntimeError('Layout chain original boundary differs ' + hex(address))
        for address, name in (
                (WRAPPER_ENTRY, 'wrapper_entry'),
                (WRAPPER_CONDITIONAL_POP, 'wrapper_conditional_pop'),
                (WRAPPER_NORMAL_POP, 'wrapper_normal_pop'),
                (GETTER_ENTRY, 'getter_entry'), (GETTER_POP, 'getter_pop')):
            self.install_point(q, address, name)
        self.emit('layout_chain_hooks_installed', read_only=True, main_only=True,
                  matched_font_manager_return_gate=True,
                  points={hex(a): b.hex() for a, b in POINT_BYTES.items()},
                  conditional_pop_requires_cpsr_z=True, nested_getter_frames=True,
                  old_access_helper_hooks_absent=True, scheduling_changes=False,
                  original_app_sha256=self.discovery.app_sha256)

    def learn_caller(self, q, caller, function, entry):
        if caller & 3:
            raise RuntimeError('Layout chain caller is not ARM aligned')
        call_bytes = self.checked_bytes(q, caller - 4)
        self.checked_bytes(q, caller)
        kind, target = caller_transfer(caller - 4, call_bytes)
        role = function + '_caller_return'
        fresh = caller not in self.installed or role not in self.installed[caller]['roles']
        self.install_point(q, caller, role)
        transfer = {'call_address': hex(caller - 4), 'call_bytes': call_bytes.hex(),
                    'call_kind': kind, 'call_target': hex(target) if target is not None else None,
                    'direct_target_matches_entry': target == entry if target is not None else None}
        self.installed[caller].setdefault('transfers', {})[function] = transfer
        if fresh:
            self.emit('layout_chain_caller_learned', function=function,
                      caller=hex(caller), caller_bytes=self.installed[caller]['bytes'], **transfer)

    def next_frame(self, q, function):
        self.frame_sequence += 1
        return {'sequence': self.frame_sequence, 'function': function,
                'entry_sp': q.arch.regs.sp, 'caller': q.arch.regs.lr,
                'ready': False, 'pop_observed': False, 'entry_context': self.context(q)}

    def wrapper_enter(self, q):
        if not self.gate(q):
            return
        self.gate_observed = True
        self.counts['main_post_manager_wrapper_entries'] += 1
        try:
            object_pointer = q.arch.regs.r0
            path_pointer = struct.unpack('<I', bytes(q.mem.read(object_pointer, 4)))[0]
            path = q.mem.string(path_pointer)
        except Exception as ex:
            self.counts['path_read_errors'] += 1
            if len(self.read_errors) < 3:
                row = {'context': self.context(q), 'error': repr(ex)[:200]}
                self.read_errors.append(row)
                self.emit('layout_chain_path_read_error', **row)
            return
        if not path.startswith(PREFIX):
            return
        if self.wrapper_frames:
            previous = self.wrapper_frames[-1]
            if (previous['entry_sp'] == q.arch.regs.sp and previous['caller'] == q.arch.regs.lr
                    and previous['path'] == path):
                self.counts['duplicate_wrapper_entries'] += 1
                return
        self.learn_caller(q, q.arch.regs.lr, 'wrapper', WRAPPER_ENTRY)
        frame = self.next_frame(q, 'wrapper')
        frame.update(path=path, string_object=hex(object_pointer), path_pointer=hex(path_pointer),
                     getter_frame_sequence=None, getter_sp_relation_matches=False)
        if self.getter_frames and frame['caller'] == GETTER_CALLER:
            getter = self.getter_frames[-1]
            frame['getter_frame_sequence'] = getter['sequence']
            frame['getter_sp_relation_matches'] = frame['entry_sp'] == getter['entry_sp'] - 168
        self.wrapper_frames.append(frame)
        self.counts['layout_wrapper_entries'] += 1
        self.path_counts[path] += 1
        self.wrapper_caller_counts[hex(frame['caller'])] += 1
        self.sparse('wrapper_entry', (path, frame['caller']), frame=frame)

    def wrapper_before_pop(self, q, address):
        if not self.gate(q) or not self.wrapper_frames:
            return
        if address == WRAPPER_CONDITIONAL_POP and not (q.arch.regs.cpsr & (1 << 30)):
            self.counts['wrapper_conditional_pop_not_taken'] += 1
            return
        frame = self.wrapper_frames[-1]
        saved = struct.unpack('<I', bytes(q.mem.read(q.arch.regs.sp + 4, 4)))[0]
        frame.update(pop_observed=True, pop_address=hex(address), saved_caller=hex(saved),
                     ready=q.arch.regs.sp == frame['entry_sp'] - 8 and saved == frame['caller'],
                     before_pop_context=self.context(q))
        self.counts['wrapper_conditional_pops' if address == WRAPPER_CONDITIONAL_POP
                    else 'wrapper_normal_pops'] += 1
        if not frame['ready']:
            self.counts['mismatched_wrapper_pops'] += 1

    def getter_enter(self, q):
        if not self.gate(q):
            return
        self.gate_observed = True
        if self.getter_frames:
            previous = self.getter_frames[-1]
            if previous['entry_sp'] == q.arch.regs.sp and previous['caller'] == q.arch.regs.lr:
                self.counts['duplicate_getter_entries'] += 1
                return
        self.learn_caller(q, q.arch.regs.lr, 'getter', GETTER_ENTRY)
        frame = self.next_frame(q, 'getter')
        frame.update(layout_wrapper_confirmed=False, layout_paths=[],
                     depth=len(self.getter_frames) + 1,
                     return_storage=hex(q.arch.regs.r0),
                     server_object=hex(q.arch.regs.r1), identifier_object=hex(q.arch.regs.r2),
                     entry_interpretation='prospective until linked matched layout wrapper return')
        self.getter_frames.append(frame)
        self.counts['getter_entries'] += 1
        self.getter_caller_counts[hex(frame['caller'])] += 1
        self.counts['max_getter_depth'] = max(self.counts['max_getter_depth'], frame['depth'])
        self.sparse('getter_entry', (frame['caller'], frame['depth']), frame=frame)

    def getter_before_pop(self, q):
        if not self.gate(q) or not self.getter_frames:
            return
        frame = self.getter_frames[-1]
        saved = struct.unpack('<I', bytes(q.mem.read(q.arch.regs.sp + 32, 4)))[0]
        frame.update(pop_observed=True, saved_caller=hex(saved),
                     ready=q.arch.regs.sp == frame['entry_sp'] - 36 and saved == frame['caller'],
                     before_pop_context=self.context(q))
        self.counts['getter_pops'] += 1
        if not frame['ready']:
            self.counts['mismatched_getter_pops'] += 1

    def returned(self, q):
        if not self.gate(q):
            return
        for function, frames, completed in (
                ('wrapper', self.wrapper_frames, self.completed_wrappers),
                ('getter', self.getter_frames, self.completed_getters)):
            if not frames or q.arch.regs.arch_pc != frames[-1]['caller']:
                continue
            frame = frames.pop()
            frame.update(restored_sp_matches=q.arch.regs.sp == frame['entry_sp'],
                         matched_return=bool(frame['ready'] and q.arch.regs.sp == frame['entry_sp']),
                         return_r0=q.arch.regs.r0, return_context=self.context(q))
            self.counts[function + ('_matched_returns' if frame['matched_return']
                                    else '_unmatched_returns')] += 1
            if function == 'wrapper':
                frame['getter_callsite_confirmed'] = bool(
                    frame['matched_return'] and frame['caller'] == GETTER_CALLER)
                if frame['getter_callsite_confirmed']:
                    self.getter_wrapper_caller_confirmed = True
                    self.counts['confirmed_getter_wrapper_returns'] += 1
                    if frame['getter_sp_relation_matches']:
                        for getter in reversed(self.getter_frames):
                            if getter['sequence'] == frame['getter_frame_sequence']:
                                getter['layout_wrapper_confirmed'] = True
                                if frame['path'] not in getter['layout_paths']:
                                    getter['layout_paths'].append(frame['path'])
                                break
                    else:
                        self.counts['unlinked_getter_wrapper_returns'] += 1
                key = (frame['path'], frame['caller'])
            else:
                frame['matched_layout_getter_return'] = bool(
                    frame['matched_return'] and frame['layout_wrapper_confirmed'])
                if frame['matched_layout_getter_return']:
                    self.counts['matched_layout_getter_returns'] += 1
                key = (frame['caller'], tuple(frame['layout_paths']))
            completed.append(frame)
            self.sparse(function + '_return', key, result=frame,
                        force=not frame['matched_return'])

    def sparse(self, kind, key, force=False, **values):
        seen = (kind, key)
        if force or seen not in self.seen:
            self.seen.add(seen)
            self.emit('layout_chain_' + kind, **values)

    def checkpoint(self, q, address):
        if address == WRAPPER_ENTRY:
            self.wrapper_enter(q)
        elif address in (WRAPPER_CONDITIONAL_POP, WRAPPER_NORMAL_POP):
            self.wrapper_before_pop(q, address)
        elif address == GETTER_ENTRY:
            self.getter_enter(q)
        elif address == GETTER_POP:
            self.getter_before_pop(q)
        self.returned(q)

    def summary(self, detail=True):
        return {'read_only': True, 'main_only': True, 'prefix': PREFIX,
                'matched_font_manager_return_gate_observed': self.gate_observed,
                'getter_wrapper_caller_confirmed': self.getter_wrapper_caller_confirmed,
                'counts': dict(self.counts), 'path_counts': dict(self.path_counts),
                'wrapper_caller_counts': dict(self.wrapper_caller_counts),
                'getter_caller_counts': dict(self.getter_caller_counts),
                'installed': {hex(a): values for a, values in self.installed.items()},
                'pending_wrapper_frames': self.wrapper_frames,
                'pending_getter_frames': self.getter_frames,
                'completed_wrapper_returns': self.completed_wrappers if detail else None,
                'completed_getter_returns': self.completed_getters if detail else None,
                'path_read_errors': self.read_errors, 'scheduling_changes': False,
                'outer_resource_constructor_completion_established': False}
