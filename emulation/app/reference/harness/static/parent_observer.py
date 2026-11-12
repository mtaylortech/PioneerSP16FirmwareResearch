"""Bounded permanent, byte-validated, read-only original-parent observations.

All counters are in memory. Initial completed chains are retained (first three),
then one aggregate progress event at most per five host seconds. This module
never writes guest memory/registers, stops execution, or invokes display work.
"""
from pathlib import Path
import collections
import hashlib
import json
import struct
import time


class ParentObserver:
    def __init__(self, emit, started, app_path):
        self.emit = emit
        self.started = started
        self.app_path = Path(app_path)
        self.mapping = json.loads(Path(__file__).with_name('mapping.json').read_text())
        if hashlib.sha256(self.app_path.read_bytes()).hexdigest() != self.mapping['original_app_sha256']:
            raise RuntimeError('Parent observer original application SHA256 mismatch')
        self.points = {int(a, 16): row for a, row in self.mapping['points'].items()}
        self.omitted_points = {a: self.points.pop(a) for a in (0x354640, 0x354658, 0x353c80)}
        self.main_tid = None
        self.sequence = 0
        self.counts = collections.Counter()
        self.parents = []
        self.parent_serial = 0
        self.reset_serial = 0
        self.allocation_serial = 0
        self.allocations = []
        self.allocation_pending = None
        self.last_progress = time.monotonic()
        self.progress_gate = lambda: True
        self.last_complete_reset_chain = None
        self.last_reset_chain_candidate = None
        self.last_complete_parent_chain = None
        self.last_complete_allocation_chain = None
        self.last_allocation_chain_candidate = None
        self.first_reset_chains = []
        self.first_allocation_chains = []
        self.last_local_context = None

    def identify_main(self, q):
        self.main_tid = q.os.thread_management.cur_thread.id
        self.emit('parent_main_identified', thread=self.main_tid,
                  source='runtime original main entry', pc=hex(q.arch.regs.arch_pc))

    def install(self, q):
        for address, row in self.points.items():
            if bytes(q.mem.read(address, 4)).hex() != row['bytes']:
                raise RuntimeError('Original parent checkpoint bytes differ ' + hex(address))
        for address, row in self.points.items():
            q.hook_address(self.checkpoint(address, row['name']), address)
        self.emit('parent_observer_installed', schema='pioneer-parent-observer-v1',
                  app_sha256=self.mapping['original_app_sha256'],
                  checkpoints={hex(a): {'name': r['name'], 'bytes': r['bytes']}
                               for a, r in self.points.items()},
                  read_only=True, permanent=True, event_progress_interval_seconds=5,
                  initial_complete_chain_limit=3, parent_stack_limit=64,
                  unknown_global_reset_total=True, omitted_per_element_checkpoints={hex(a):r['name'] for a,r in self.omitted_points.items()})

    def read(self, q, address, size):
        if not (0 <= address <= 0xffffffff and 0 < size <= 40 and address + size <= 0x100000000):
            self.counts['invalid_read_range'] += 1
            return {'address': hex(address), 'size': size, 'error': 'invalid bounded range'}
        try:
            if not q.mem.is_mapped(address, size):
                raise ValueError('range is not mapped')
            data = bytes(q.mem.read(address, size))
            if len(data) != size:
                raise ValueError('short read')
            return {'address': hex(address), 'size': size, 'hex': data.hex()}
        except Exception as ex:
            self.counts['read_failures'] += 1
            return {'address': hex(address), 'size': size, 'error': str(ex)[:240]}

    def header(self, q, obj):
        row = self.read(q, obj, 40)
        if 'hex' in row:
            data = bytes.fromhex(row['hex'])
            row.update(preceding_bound_s32=struct.unpack_from('<i', data, 20)[0],
                       subsequent_bound_s32=struct.unpack_from('<i', data, 32)[0],
                       preceding_table=hex(struct.unpack_from('<I', data, 12)[0]),
                       subsequent_table=hex(struct.unpack_from('<I', data, 24)[0]))
        return row

    def context(self, q, stage, **extra):
        return {'stage': stage, 'sequence': self.sequence,
                'host_elapsed': round(time.monotonic() - self.started, 6),
                'thread': q.os.thread_management.cur_thread.id,
                'pc': hex(q.arch.regs.arch_pc), 'lr': hex(q.arch.regs.lr),
                'sp': hex(q.arch.regs.sp),
                'registers': {n: hex(q.arch.regs.read(n)) for n in
                              ('r0', 'r1', 'r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r10')},
                **extra}

    def parent_at_body(self, q):
        if self.parents and q.arch.regs.sp == self.parents[-1]['entry_sp'] - 40:
            return self.parents[-1]
        return None

    def reset_stage(self, q, name, frame, valid, reason=None):
        chain = frame['pending_reset']
        row = self.context(q, name, reset_invocation=chain['reset_invocation'],
                           parent_invocation=frame['parent_invocation'],
                           parent_object=hex(frame['object']),
                           matrix_object=hex(chain['matrix_object']),
                           call_sp=hex(chain['call_sp']), target=hex(chain['target']),
                           matched=bool(valid), reason=reason)
        if name in ('matrix_entry354604', 'matrix_loop_complete354674', 'matrix_before_pop3546d4'):
            row['matrix_header'] = self.read(q, chain['matrix_object'], 40)
            if 'hex' in row['matrix_header']:
                data = bytes.fromhex(row['matrix_header']['hex'])
                row['outer_bound_u8'] = data[0]
                row['inner_bound_u8'] = data[1]
                chain['dimensions'] = [data[0], data[1]]
        if name == 'matrix_before_pop3546d4':
            row['saved_caller_read'] = self.read(q, q.arch.regs.sp + 20, 4)
            if row['saved_caller_read'].get('hex') != '9cab5000':
                row['matched'] = False
                row['reason'] = 'saved caller read absent or differs from 0x50ab9c'
        chain['stages'].append(row)
        self.counts['stage_' + name] += 1
        if not row['matched']:
            self.counts['reset_stage_mismatch'] += 1
        return row

    def checkpoint(self, address, name):
        def callback(q):
            if self.main_tid is None or q.os.thread_management.cur_thread.id != self.main_tid:
                return
            self.sequence += 1
            self.counts[name] += 1
            sp = q.arch.regs.sp
            if address == 0x50aaf4:
                self.parent_serial += 1
                if len(self.parents) >= 64:
                    self.counts['parent_stack_drops'] += 1
                    raise RuntimeError('Bounded parent frame stack overflow')
                frame = {'parent_invocation': self.parent_serial, 'object': q.arch.regs.r0,
                         'entry_sp': sp, 'caller': q.arch.regs.lr,
                         'depth': len(self.parents), 'pending_reset': None,
                         'reset_returns': 0, 'return_ready': False}
                if frame['caller'] not in self.points:
                    self.counts['parent_caller_outside_static_candidates'] += 1
                frame['entry'] = self.context(q, 'parent_entry50aaf4',
                    parent_invocation=frame['parent_invocation'], parent_object=hex(frame['object']),
                    entry_sp=hex(sp), expected_caller=hex(frame['caller']), depth=frame['depth'],
                    parent_header=self.header(q, frame['object']))
                self.parents.append(frame)
            elif address == 0x50ab98:
                frame = self.parent_at_body(q)
                if frame is None or frame['object'] != q.arch.regs.r5 or q.arch.regs.r0 != frame['object']:
                    self.counts['reset_call_without_matching_parent'] += 1
                else:
                    self.reset_serial += 1
                    target = q.arch.regs.r3
                    adjust = 36 if target == 0x354f74 else 0
                    chain = {'reset_invocation': self.reset_serial,
                             'parent_invocation': frame['parent_invocation'],
                             'parent_object': hex(frame['object']),
                             'matrix_object': frame['object'] + adjust,
                             'call_sp': sp, 'target': target, 'stages': [],
                             'parent_header': self.header(q, frame['object'])}
                    frame['pending_reset'] = chain
                    self.reset_stage(q, 'callsite50ab98', frame,
                                     target in (0x354f74, 0x354604),
                                     None if target in (0x354f74, 0x354604) else 'unmapped target adjustment')
            elif address in (0x354604, 0x354674, 0x3546d4):
                frame = self.parents[-1] if self.parents else None
                chain = frame['pending_reset'] if frame else None
                if not chain:
                    self.counts['matrix_stage_without_call'] += 1
                else:
                    expected_sp = chain['call_sp'] if address == 0x354604 else chain['call_sp'] - 24
                    actual_obj = q.arch.regs.r0 if address == 0x354604 else q.arch.regs.r6
                    valid = (actual_obj == chain['matrix_object'] and sp == expected_sp and
                             (address != 0x354604 or q.arch.regs.lr == 0x50ab9c))
                    stage = {0x354604: 'matrix_entry354604', 0x354674: 'matrix_loop_complete354674',
                             0x3546d4: 'matrix_before_pop3546d4'}[address]
                    self.reset_stage(q, stage, frame, valid,
                                     None if valid else 'matrix object, LR or SP mismatch')
            elif address == 0x50ab9c:
                frame = self.parent_at_body(q)
                chain = frame['pending_reset'] if frame else None
                if not chain:
                    self.counts['reset_return_without_call'] += 1
                else:
                    self.reset_stage(q, 'reset_caller_continuation50ab9c', frame,
                                     q.arch.regs.r5 == frame['object'] and sp == chain['call_sp'])
                    stages = [r['stage'] for r in chain['stages']]
                    chain['complete'] = stages == ['callsite50ab98', 'matrix_entry354604',
                        'matrix_loop_complete354674', 'matrix_before_pop3546d4',
                        'reset_caller_continuation50ab9c'] and all(r['matched'] for r in chain['stages'])
                    self.counts['matched_reset_returns' if chain['complete'] else 'unmatched_reset_returns'] += 1
                    frame['reset_returns'] += int(chain['complete'])
                    self.last_reset_chain_candidate = chain
                    if chain['complete']:
                        self.last_complete_reset_chain = chain
                    if len(self.first_reset_chains) < 3:
                        self.first_reset_chains.append(chain)
                        self.emit('parent_observer_initial_chain',
                                  complete_reset_chain=chain if chain['complete'] else None,
                                  reset_chain_candidate=chain,
                                  counters=dict(self.counts))
                    frame['pending_reset'] = None
            elif address == 0x50ac88:
                frame = self.parents[-1] if self.parents else None
                if frame:
                    saved = self.read(q, sp + 24, 4)
                    valid = sp == frame['entry_sp'] - 28 and saved.get('hex') == struct.pack('<I', frame['caller']).hex()
                    frame['before_pop'] = self.context(q, 'parent_before_pop50ac88',
                        parent_invocation=frame['parent_invocation'], parent_object=hex(frame['object']),
                        entry_sp=hex(frame['entry_sp']), expected_caller=hex(frame['caller']),
                        saved_caller_read=saved, matched=valid)
                    frame['return_ready'] = valid
            elif address == 0x35e068:
                self.allocation_serial += 1
                enclosing_header = self.read(q, q.arch.regs.r6, 24)
                enclosing_bound = None
                if 'hex' in enclosing_header:
                    enclosing_bound = struct.unpack_from('<i', bytes.fromhex(enclosing_header['hex']), 8)[0]
                self.allocation_pending = {'allocation_invocation': self.allocation_serial,
                    'object': q.arch.regs.r0, 'entry_sp': sp,
                    'enclosing_input': hex(q.arch.regs.r6),
                    'enclosing_index_r8': q.arch.regs.r8,
                    'enclosing_bound_s32': enclosing_bound,
                    'enclosing_header': enclosing_header, 'stages': [self.context(q,
                    'allocation_callsite35e068', allocation_invocation=self.allocation_serial,
                    allocation_object=hex(q.arch.regs.r0), entry_sp=hex(sp), matched=True)]}
            elif address == 0x353bc4:
                chain = self.allocation_pending
                if chain:
                    chain['stages'].append(self.context(q, 'allocation_entry353bc4',
                        allocation_invocation=chain['allocation_invocation'],
                        allocation_object=hex(chain['object']), entry_sp=hex(chain['entry_sp']),
                        matched=q.arch.regs.r0 == chain['object'] and sp == chain['entry_sp'] and q.arch.regs.lr == 0x35e06c))
                    self.allocations.append(chain)
                    self.allocation_pending = None
                else:
                    self.counts['allocation_entry_without_call'] += 1
            elif address in (0x353cbc, 0x353d04):
                chain = self.allocations[-1] if self.allocations else None
                if chain:
                    valid = q.arch.regs.r4 == chain['object'] and sp == chain['entry_sp'] - (48 if address == 0x353cbc else 36)
                    row = self.context(q, 'allocation_matrix_complete353cbc' if address == 0x353cbc else 'allocation_before_pop353d04',
                        allocation_invocation=chain['allocation_invocation'], allocation_object=hex(chain['object']),
                        entry_sp=hex(chain['entry_sp']), matched=valid)
                    if address == 0x353d04:
                        row['saved_caller_read'] = self.read(q, sp + 32, 4)
                        row['matched'] = valid and row['saved_caller_read'].get('hex') == '6ce03500'
                    chain['stages'].append(row)
            elif address == 0x35e06c:
                chain = self.allocations[-1] if self.allocations else None
                if chain:
                    chain['stages'].append(self.context(q, 'allocation_caller_continuation35e06c',
                        allocation_invocation=chain['allocation_invocation'], allocation_object=hex(chain['object']),
                        entry_sp=hex(chain['entry_sp']), matched=sp == chain['entry_sp'] and q.arch.regs.r0 == chain['object']))
                    chain['complete'] = [r['stage'] for r in chain['stages']] == ['allocation_callsite35e068',
                        'allocation_entry353bc4', 'allocation_matrix_complete353cbc', 'allocation_before_pop353d04',
                        'allocation_caller_continuation35e06c'] and all(r['matched'] for r in chain['stages'])
                    self.counts['matched_allocation_returns' if chain['complete'] else 'unmatched_allocation_returns'] += 1
                    self.last_allocation_chain_candidate = chain
                    if chain['complete']:
                        self.last_complete_allocation_chain = chain
                    if len(self.first_allocation_chains) < 3:
                        self.first_allocation_chains.append(chain)
                        self.emit('parent_observer_initial_allocation_chain',
                                  complete_allocation_chain=chain if chain['complete'] else None,
                                  allocation_chain_candidate=chain,
                                  counters=dict(self.counts))
                    self.allocations.pop()
            # A static caller candidate proves a parent return only after the
            # matching entry, saved-PC before-pop read and exact entry SP.
            frame = self.parents[-1] if self.parents else None
            if frame and frame['return_ready'] and address == frame['caller'] and sp == frame['entry_sp']:
                row = self.context(q, 'parent_caller_continuation', parent_invocation=frame['parent_invocation'],
                    parent_object=hex(frame['object']), entry_sp=hex(frame['entry_sp']), matched=True)
                chain = {'parent_invocation': frame['parent_invocation'], 'depth': frame['depth'],
                         'parent_object': hex(frame['object']), 'caller': hex(frame['caller']),
                         'stages': [frame['entry'], frame['before_pop'], row],
                         'matched_reset_returns': frame['reset_returns'], 'complete': True}
                self.last_complete_parent_chain = chain
                self.counts['matched_parent_returns'] += 1
                if frame['depth'] == 0:
                    self.counts['matched_top_level_parent_returns'] += 1
                    if self.counts['matched_top_level_parent_returns'] <= 3:
                        self.emit('parent_observer_initial_parent_return', complete_parent_chain=chain,
                                  counters=dict(self.counts))
                self.parents.pop()
            if address in (0x50ab18, 0x50ab7c, 0x50ab8c, 0x50abc0, 0x50ac94, 0x50ac98, 0x50ac1c):
                self.last_local_context = self.context(q, name)
            now = time.monotonic()
            if now - self.last_progress >= 5 and self.progress_gate():
                self.last_progress = now
                self.emit('parent_observer_progress', **self.summary(q))
        return callback

    def summary(self, q=None):
        current_context = None
        main_registers_valid = False
        if q is not None:
            try:
                current_context = self.context(q, 'summary_current_thread')
                main_registers_valid = current_context['thread'] == self.main_tid
            except Exception as ex:
                current_context = {'error': str(ex)[:240], 'main_registers_valid': False}
        pending = []
        for frame in self.parents[-4:]:
            item = {'parent_invocation': frame['parent_invocation'], 'parent_object': hex(frame['object']),
                    'entry_sp': hex(frame['entry_sp']), 'expected_caller': hex(frame['caller']),
                    'depth': frame['depth'], 'matched_reset_returns': frame['reset_returns'],
                    'return_ready': frame['return_ready'], 'pending_reset_chain': frame['pending_reset']}
            if q is not None:
                item['parent_header'] = self.header(q, frame['object'])
            pending.append(item)
        matrix = None
        if q is not None and self.parents and self.parents[-1]['pending_reset']:
            chain = self.parents[-1]['pending_reset']
            matrix = {'matrix_object': hex(chain['matrix_object']),
                      'header': self.read(q, chain['matrix_object'], 40),
                      'main_registers_valid': main_registers_valid,
                      'outer_index_r8': q.arch.regs.r8 if main_registers_valid else None,
                      'inner_index_r5': q.arch.regs.r5 if main_registers_valid else None,
                      'stride_offset_r4': q.arch.regs.r4 if main_registers_valid else None,
                      'read_scope': 'shared matrix bytes; indices only when current thread is runtime main'}
        return {'schema': 'pioneer-parent-observer-v1', 'runtime_main_tid': self.main_tid,
                'summary_current_context': current_context, 'main_registers_valid': main_registers_valid,
                'sequence': self.sequence, 'counters': dict(self.counts),
                'active_parent_depth': len(self.parents), 'pending_parent_frames': pending,
                'pending_parent_frames_omitted': max(0, len(self.parents) - 4),
                'pending_allocation': self.allocations[-1] if self.allocations else self.allocation_pending,
                'complete_reset_chain': self.last_complete_reset_chain,
                'last_reset_chain_candidate': self.last_reset_chain_candidate,
                'complete_parent_chain': self.last_complete_parent_chain,
                'complete_allocation_chain': self.last_complete_allocation_chain,
                'last_allocation_chain_candidate': self.last_allocation_chain_candidate,
                'last_local_context': self.last_local_context, 'matrix_progress': matrix,
                'read_only': True, 'global_reset_total': None,
                'omitted_per_element_checkpoints': {hex(a):r['name'] for a,r in self.omitted_points.items()},
                'scope': 'matched local call chains and recursive parent helper; application ancestor completion unknown'}
