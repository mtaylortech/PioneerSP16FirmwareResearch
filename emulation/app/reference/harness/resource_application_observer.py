"""Sparse, read-only main-thread resource application entry/return observation."""
import collections
import struct
import time

ENTRY = 0x38fb1c
POP = 0x38fcb4
POINT_BYTES = {
    ENTRY: bytes.fromhex('00c091e5'),
    0x38fb20: bytes.fromhex('f0452de9'),
    0x38fb28: bytes.fromhex('44d04de2'),
    0x38fb74: bytes.fromhex('33ff2fe1'),
    0x38fb78: bytes.fromhex('98119fe5'),
    0x38fcb0: bytes.fromhex('44d08de2'),
    POP: bytes.fromhex('f085bde8'),
}


def caller_transfer(address, data):
    word = struct.unpack('<I', data)[0]
    if (word >> 24) & 15 == 11 and word >> 28 != 15:
        displacement = word & 0xffffff
        if displacement & 0x800000:
            displacement -= 0x1000000
        return 'arm_bl', (address + 8 + displacement * 4) & 0xffffffff
    if word & 0x0ffffff0 == 0x012fff30:
        return 'arm_blx_register', None
    return 'unresolved_transfer', None


class ResourceApplicationObserver:
    def __init__(self, emit, started, discovery, clock=time.monotonic):
        self.emit, self.started, self.discovery, self.clock = emit, started, discovery, clock
        self.installed = {}
        self.observation_handles = []
        self.callers = {}
        self.frames = []
        self.samples = []
        self.return_sequence = []
        self.last_return = None
        self.counts = collections.Counter()
        self.caller_counts = collections.Counter()
        self.return_counts = collections.Counter()
        self.last_aggregate = clock()
        self.manager_return_seen = False

    def gate(self, q):
        if self.discovery.main_tid is None or q.os.thread_management.cur_thread.id != self.discovery.main_tid:
            return False
        if not self.manager_return_seen:
            self.manager_return_seen = any(
                row.get('entry') == '0x71ce28' and row.get('matched_return')
                for row in self.discovery.completed)
        return self.manager_return_seen

    def checked(self, q, address):
        expected = self.discovery.expected(address)
        if bytes(q.mem.read(address, 4)) != expected:
            raise RuntimeError('Resource application loaded bytes differ ' + hex(address))
        return expected

    def hook(self, q, address):
        if address not in self.installed:
            self.installed[address] = self.checked(q, address).hex()
            self.observation_handles.append(q.hook_address(lambda guest: self.checkpoint(guest, address), address))

    def install(self, q):
        if self.installed:
            raise RuntimeError('Resource application observer already installed')
        for address, expected in POINT_BYTES.items():
            if self.checked(q, address) != expected:
                raise RuntimeError('Resource application original bytes differ ' + hex(address))
        self.hook(q, ENTRY)
        self.hook(q, POP)
        self.emit('resource_application_hooks_installed', main_only=True, read_only=True,
                  original_app_sha256=self.discovery.app_sha256,
                  points={hex(a): b.hex() for a, b in POINT_BYTES.items()},
                  matched_font_manager_return_gate=True, scheduling_changes=False)

    def learn(self, q, caller):
        if caller in self.callers:
            return
        if caller & 3:
            raise RuntimeError('Resource application caller is not ARM aligned')
        call_bytes = self.checked(q, caller - 4)
        caller_bytes = self.checked(q, caller)
        kind, target = caller_transfer(caller - 4, call_bytes)
        self.callers[caller] = {
            'caller': hex(caller), 'caller_bytes': caller_bytes.hex(),
            'call_address': hex(caller - 4), 'call_bytes': call_bytes.hex(),
            'call_kind': kind, 'call_target': hex(target) if target is not None else None,
            'direct_target_matches_entry': target == ENTRY if target is not None else None,
        }
        self.hook(q, caller)
        self.emit('resource_application_caller_learned', **self.callers[caller])

    def context(self, q):
        return {'host_elapsed': round(self.clock() - self.started, 6),
                'thread': q.os.thread_management.cur_thread.id,
                'pc': hex(q.arch.regs.arch_pc), 'sp': hex(q.arch.regs.sp),
                'lr': hex(q.arch.regs.lr)}

    def enter(self, q):
        sp, caller = q.arch.regs.sp, q.arch.regs.lr
        if self.frames and self.frames[-1]['entry_sp'] == sp and self.frames[-1]['caller'] == caller:
            self.counts['duplicate_entries'] += 1
            return
        self.learn(q, caller)
        self.counts['entries'] += 1
        self.caller_counts[hex(caller)] += 1
        frame = {'sequence': self.counts['entries'], 'entry_sp': sp, 'caller': caller,
                 'depth': len(self.frames) + 1, 'pop_observed': False, 'ready': False,
                 'entry_context': self.context(q)}
        self.frames.append(frame)
        self.counts['max_depth'] = max(self.counts['max_depth'], len(self.frames))
        if frame['sequence'] <= 3 or self.caller_counts[hex(caller)] == 1:
            self.emit('resource_application_entry', frame=dict(frame))

    def before_pop(self, q):
        if not self.frames:
            self.counts['pop_without_frame'] += 1
            return
        frame = self.frames[-1]
        saved = struct.unpack('<I', bytes(q.mem.read(q.arch.regs.sp + 24, 4)))[0]
        frame.update(pop_observed=True, saved_caller=hex(saved),
                     ready=q.arch.regs.sp == frame['entry_sp'] - 28 and saved == frame['caller'],
                     before_pop_context=self.context(q))
        self.counts['pops'] += 1
        if not frame['ready']:
            self.counts['mismatched_pops'] += 1

    def returned(self, q, address):
        if not self.frames or address != self.frames[-1]['caller']:
            return
        frame = self.frames[-1]
        if not frame['pop_observed']:
            self.counts['caller_without_pop'] += 1
            return
        self.frames.pop()
        frame.update(restored_sp_matches=q.arch.regs.sp == frame['entry_sp'],
                     matched_return=bool(frame['ready'] and q.arch.regs.sp == frame['entry_sp']),
                     return_context=self.context(q), return_r0=q.arch.regs.r0)
        key = 'matched_returns' if frame['matched_return'] else 'unmatched_returns'
        self.counts[key] += 1
        caller = hex(frame['caller'])
        self.return_counts[caller] += 1
        self.last_return = frame
        self.return_sequence.append({k:frame[k] for k in ("sequence","caller","depth","entry_sp","matched_return","return_context")})
        first = self.return_counts[caller] == 1
        if len(self.samples) < 32 and (frame['sequence'] <= 3 or first or not frame['matched_return']):
            self.samples.append(frame)
        if frame['sequence'] <= 3 or first or (not frame['matched_return'] and self.counts[key] <= 3):
            self.emit('resource_application_return', result=frame)

    def checkpoint(self, q, address):
        if not self.gate(q):
            return
        # Process a learned caller first, in case the destination is itself an entry.
        self.returned(q, address)
        if address == ENTRY:
            self.enter(q)
        elif address == POP:
            self.before_pop(q)
        now = self.clock()
        if now - self.last_aggregate >= 5:
            self.last_aggregate = now
            self.emit('resource_application_progress', host_elapsed=round(now - self.started, 6),
                      counts=dict(self.counts), caller_counts=dict(self.caller_counts),
                      return_counts=dict(self.return_counts), pending_depth=len(self.frames))

    def summary(self, detail=True):
        return {'main_only': True, 'read_only': True, 'scheduling_changes': False,
                'font_manager_return_seen': self.manager_return_seen,
                'counts': dict(self.counts), 'caller_counts': dict(self.caller_counts),
                'return_counts': dict(self.return_counts),
                'installed': {hex(a): b for a, b in self.installed.items()},
                'callers': list(self.callers.values()), 'pending_frames': list(self.frames),
                'completed_samples': list(self.samples) if detail else None,
                'last_return': self.last_return, 'return_sequence': self.return_sequence if detail else None,
                'outer_constructor_completion_established': False}
