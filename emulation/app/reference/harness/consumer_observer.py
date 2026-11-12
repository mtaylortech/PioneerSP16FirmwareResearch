"""Sparse read-only original completion consumer and progress-popup transition.

Hooks execute before instructions. Entries, calls, saved LR and restored SP are
checked independently. Worker receipts come from the unchanged live-validated
CompletionObserver. Result 1/no saved file is never classified as a failure.
No prerequisite file is written and no input is sent by this observer.
"""
import collections
import struct

ENTRY = 0x25f000
POINTS = (ENTRY, 0x25f044, 0x25f04c, 0x25f058, 0x25f05c,
          0x25f060, 0x25f074, 0x25f09c, 0x25f108,
          0x25f110, 0x25f114, 0x25f120, 0x25f124,
          0x25f130, 0x25f134, 0x25f13c, 0x25f140,
          0x25f03c, 0x25f040)
POPUP_POINTS = (0x25ec94, 0x25ecac, 0x25ed98, 0x25eda4, 0x25eda8,
                0x25edb0, 0x25edb4, 0x25edc8, 0x25edcc,
                0x25edd0, 0x25edd4, 0x25eca8)
CALLS = {0x25f110: (0x69769c, 'cancel_completion_timer'),
         0x25f120: (0x69c37c, 'schedule_zero_100ms'),
         0x25f130: (0x69c37c, 'schedule_one_50ms'),
         0x25f13c: (0x25ec44, 'show_progress_false'),
         0x25eda4: (None, 'popup_component'),
         0x25edb0: (0x7c1644, 'remove_popup'),
         0x25edc8: (None, 'popup_visibility_false'),
         0x25edd0: (0x2ee918, 'release_controller_state')}


class ConsumerObserver:
    def __init__(self, emit, discovery, producer):
        self.emit, self.discovery, self.producer = emit, discovery, producer
        self.hooks, self.frames, self.calls = {}, {}, {}
        self.counts = collections.Counter()
        self.records, self.signatures = [], {}
        self.latest, self.acceptance, self.retired = None, None, False

    def validate(self, q, address, size=4):
        raw = b''.join(self.discovery.expected(address+i) for i in range(0, size, 4))
        if bytes(q.mem.read(address, size)) != raw:
            raise RuntimeError('Consumer original bytes differ ' + hex(address))
        return raw

    def hook(self, q, address):
        if address not in self.hooks:
            self.validate(q, address)
            self.hooks[address] = q.hook_address(lambda guest, a=address: self.visit(guest, a), address)

    def install(self, q):
        # Validate complete selected control flow, including unhooked instructions
        # and the countdown literal. Hook only boundaries/gates and matched returns.
        for address, size in ((0x25eff8, 428), (0x25ec44, 408)):
            self.validate(q, address, size)
        for address in POINTS:
            self.hook(q, address)
        self.emit('consumer_hooks_validated', read_only=True, points={hex(a): self.discovery.expected(a).hex() for a in POINTS},
                  downstream_deferred_until_selected_call=True,
                  countdown_pointer=hex(struct.unpack('<I', self.discovery.expected(0x25f1a4))[0]))

    def record(self, kind, signature=None, **row):
        self.counts[kind] += 1
        n = self.counts[kind]
        if signature is not None:
            prior = self.signatures.get(kind)
            self.signatures[kind] = signature
            if n > 3 and prior == signature and n % 128:
                return
        receipt = dict(kind=kind, count=n, **row)
        self.records.append(receipt)
        self.emit(kind, count=n, **row)

    def state(self, q, owner):
        data = bytes(q.mem.read(owner+0x12c, 0x1c))
        return dict(owner=hex(owner), submitted=data[0], completed=data[1],
                    result=struct.unpack_from('<I', data, 4)[0],
                    popup=hex(struct.unpack_from('<I', data, 0x14)[0]),
                    bytes_12c_148=data.hex(),
                    controller_queue_f0_f8=bytes(q.mem.read(owner+0xf0, 8)).hex())

    def producer_match(self, owner):
        records = self.producer.records
        entries = [r for r in records if r['kind'] == 'original_completion_listener_entry'
                   and r['frame']['target'] == 0x25dfc4 and r['frame']['listener']-0x124 == owner
                   and r.get('matched_thread_sp_arguments_lr')]
        if not entries:
            return None
        frame = entries[-1]['frame']
        stores = [r for r in records if r['kind'] == 'original_listener_state_store' and r['thread'] == frame['thread']]
        exact = {}
        for pc, offset, size, value in ((0x25dfd0, 0x130, 4, struct.pack('<I', frame['result_argument']).hex()),
                                       (0x25dfd4, 0x12d, 1, '01')):
            hits = [r for r in stores if r['pc'] == hex(pc) and r['address'] == hex(owner+offset)
                    and r['size'] == size and r['after'] == value]
            if not hits:
                return None
            exact[hex(pc)] = hits[-1]
        returns = [r for r in records if r['kind'] == 'original_completion_listener_return'
                   and r['frame'] == frame and r.get('matched_thread_sp')]
        enclosing = [r for r in records if r['kind'] == 'original_resume_return'
                     and r['frame']['thread'] == frame['thread']
                     and r['frame']['listener'] == frame['listener']
                     and r['frame']['manager'] == frame['manager'] and r.get('matched_thread_sp')]
        if not returns or not enclosing:
            return None
        return dict(frame=frame, stores=exact, listener_return=returns[-1], enclosing_return=enclosing[-1],
                    no_file_is_not_failure=True, result_is_not_success_predicate=True)

    def vector(self, q, owner):
        manager = q.mem.read_ptr(owner+0x128)
        count = q.mem.read_ptr(manager+0x30)
        if count > 256:
            raise RuntimeError('Popup component vector exceeds observation bound')
        array = q.mem.read_ptr(manager+0x28)
        return dict(manager=hex(manager), count=count,
                    members=[hex(q.mem.read_ptr(array+4*i)) for i in range(count)])

    def frame(self, q, popup=False):
        tid, r = q.os.thread_management.cur_thread.id, q.arch.regs
        f = self.frames.get(tid)
        if f is None:
            return None
        expected = f['entry_sp']-40-(40 if popup else 0)
        if r.sp != expected or r.r4 != f['owner']:
            raise RuntimeError('Consumer body thread/SP/owner mismatch')
        return f

    def call(self, q, address, f):
        r, tid = q.arch.regs, q.os.thread_management.cur_thread.id
        target, name = CALLS[address]
        from resource_application_observer import caller_transfer
        kind, decoded = caller_transfer(address, self.validate(q, address))
        if target is not None:
            if (kind, decoded) != ('arm_bl', target):
                raise RuntimeError('Consumer selected direct call differs')
        else:
            target = r.r3
            offset = 0x14 if address == 0x25eda4 else 8
            if kind != 'arm_blx_register' or target & 3 or q.mem.read_ptr(q.mem.read_ptr(r.r0)+offset) != target:
                raise RuntimeError('Consumer popup vtable target mismatch')
        owner = f['owner']
        args = [r.read('r'+str(i)) for i in range(4)]
        expected = {0x25f110: [owner+0x110, 2], 0x25f120: [owner+0x110, 0, 100],
                    0x25f130: [owner+0x110, 1, 50], 0x25f13c: [owner, 0],
                    0x25eda4: [f.get('popup', 0)],
                    0x25edb0: [q.mem.read_ptr(owner+0x128), f.get('component', 0)],
                    0x25edc8: [f.get('popup', 0)+0xc, 0], 0x25edd0: [owner]}[address]
        if args[:len(expected)] != expected:
            raise RuntimeError('Consumer selected call arguments mismatch ' + name)
        key = (tid, address+4)
        if key in self.calls:
            raise RuntimeError('Overlapping consumer selected call')
        raw = self.validate(q, target, 128)
        call = dict(name=name, call=hex(address), target=hex(target), thread=tid, sp=r.sp,
                    arguments=args, entry_observed=False, target_bytes=raw.hex(),
                    target_instructions=[dict(address=hex(i.address), bytes=i.bytes.hex(), mnemonic=i.mnemonic, operands=i.op_str)
                                         for i in q.arch.disassembler.disasm(raw, target)])
        if name == 'remove_popup':
            call['before_vector'] = self.vector(q, owner)
        if name == 'popup_visibility_false':
            call['component_before128'] = bytes(q.mem.read(r.r0, 128)).hex()
        if name == 'release_controller_state':
            call['state_before'] = self.state(q, owner)
        self.calls[key] = call
        self.hook(q, target)
        if name == 'show_progress_false':
            f['popup_sp'] = r.sp
            for a in POPUP_POINTS:
                self.hook(q, a)
        self.record('original_consumer_call', **call)

    def visit(self, q, address):
        tid, r = q.os.thread_management.cur_thread.id, q.arch.regs
        if tid != self.discovery.main_tid:
            return
        # Dynamic callee entry comes before the callee's stack adjustment.
        for (thread, return_pc), call in list(self.calls.items()):
            if tid == thread and address == int(call['target'], 16):
                if (r.sp, r.lr, [r.read('r'+str(i)) for i in range(3)]) != (call['sp'], return_pc, call['arguments'][:3]):
                    raise RuntimeError('Consumer actual callee entry frame mismatch')
                call['entry_observed'] = True
                self.record('original_consumer_callee_entry', name=call['name'], target=call['target'],
                            thread=tid, sp=r.sp, matched_thread_sp_arguments_lr=True)
                return
        if address == ENTRY:
            if r.r1 != 2:
                self.counts['other_timer_events'] += 1
                return
            if tid in self.frames:
                raise RuntimeError('Overlapping main completion consumer frame')
            self.validate(q, r.lr)
            state = self.state(q, r.r0)
            f = dict(thread=tid, owner=r.r0, entry_sp=r.sp, caller=r.lr, before=state,
                     producer=self.producer_match(r.r0), stages=[], call_returns={})
            if f['producer'] and state['result'] != f['producer']['frame']['result_argument']:
                raise RuntimeError('Consumer state differs from matched worker result')
            self.frames[tid] = f
            self.hook(q, r.lr)
            self.record('original_consumer_entry', signature=(state['completed'], bool(f['producer'])),
                        thread=tid, owner=hex(r.r0), entry_sp=r.sp, caller=hex(r.lr), state=state,
                        matched_main=True, producer_matched=bool(f['producer']))
            return
        f = self.frames.get(tid)
        if f is None:
            return
        if address == f['caller']:
            if r.sp != f['entry_sp'] or not f.get('saved_return_matched'):
                raise RuntimeError('Consumer enclosing return frame mismatch')
            f['after'] = self.state(q, f['owner'])
            self.latest = f
            self.frames.pop(tid)
            selected = 'zero_countdown' in f['stages']
            self.record('original_consumer_return', signature=(tuple(f['stages']), selected),
                        frame=f, matched_thread_saved_lr_restored_sp=True)
            if selected:
                required = set(name for target, name in CALLS.values())
                calls = f['call_returns']
                removed = calls.get('remove_popup', {}).get('component_removed', False)
                self.acceptance = dict(passed=bool(f['producer'] and f.get('popup_type_valid') and removed
                    and not f.get('popup_error') and required <= calls.keys()
                    and f.get('popup_saved_return_matched')),
                    frame=f, original_completion_state_evidence=True if f['producer'] else False,
                    popup_removed=removed, completed_startup_proved=False,
                    interpretation='Original main consumer completion path and downstream popup state; input usability remains unproved.')
                self.record('original_consumer_acceptance', evidence=self.acceptance)
                for handle in self.hooks.values():
                    q.hook_del(handle)
                self.hooks.clear()
                self.retired = True
                self.emit('consumer_details_retired', reason='selected original completion path returned; acceptance evidence and any missing transitions retained')
            return
        call = self.calls.get((tid, address))
        if call:
            if r.sp != call['sp'] or not call['entry_observed']:
                raise RuntimeError('Consumer call return lacks matched actual entry/SP')
            if call['name'] == 'show_progress_false' and not f.get('popup_saved_return_matched'):
                raise RuntimeError('Popup return lacks matched saved LR')
            if call['name'] == 'popup_component':
                f['component'] = r.r0
            if call['name'] == 'remove_popup':
                after = self.vector(q, f['owner'])
                call['after_vector'] = after
                component = hex(f['component'])
                call['component_removed'] = (component in call['before_vector']['members']
                                             and component not in after['members']
                                             and after['manager'] == call['before_vector']['manager']
                                             and after['count'] == call['before_vector']['count']-1
                                             and after['members'] == [p for p in call['before_vector']['members'] if p != component])
            if call['name'] == 'popup_visibility_false':
                call['component_after128'] = bytes(q.mem.read(call['arguments'][0], 128)).hex()
            if call['name'] == 'release_controller_state':
                call['state_after'] = self.state(q, f['owner'])
            call['return_result'] = r.r0
            call['matched_thread_sp_entry'] = True
            f['call_returns'][call['name']] = call
            self.calls.pop((tid, address))
            self.record('original_consumer_call_return', call=call)
            return
        if address == 0x25f040:
            if r.sp != f['entry_sp']-16 or q.mem.read_ptr(r.sp+12) != f['caller']:
                raise RuntimeError('Consumer saved return/SP mismatch')
            f['saved_return_matched'] = True
            return
        if address == 0x25eca8:
            if r.sp != f['popup_sp']-20 or q.mem.read_ptr(r.sp+16) != 0x25f140:
                raise RuntimeError('Popup saved return/SP mismatch')
            f['popup_saved_return_matched'] = True
            self.record('original_consumer_popup_before_pop', thread=tid, sp=r.sp, saved_lr='0x25f140', matched=True)
            return
        popup = address in POPUP_POINTS
        self.frame(q, popup=popup)
        if address in CALLS:
            self.call(q, address, f)
            return
        if address == 0x25f044:
            if r.r0 != f['owner']:
                raise RuntimeError('Consumer flag owner mismatch')
            f['flag'] = q.mem.read_ptr(f['owner']+0x12c) >> 8 & 255
        elif address == 0x25f04c:
            z = bool(r.cpsr & (1 << 30))
            if r.r3 != f['flag'] or z != (f['flag'] == 0):
                raise RuntimeError('Consumer completion flag gate mismatch')
            f['stages'].append('flag_unset' if z else 'flag_set')
        elif address == 0x25f058:
            pointer = struct.unpack('<I', self.discovery.expected(0x25f1a4))[0]
            if r.r0 != pointer or r.r5 != q.mem.read_ptr(pointer+4):
                raise RuntimeError('Consumer countdown pointer/value mismatch')
            f['countdown'] = r.r5
        elif address == 0x25f05c:
            if bool(r.cpsr & (1 << 30)) != (f['countdown'] == 0):
                raise RuntimeError('Consumer countdown gate mismatch')
        elif address == 0x25f060:
            if f.get('countdown') == 0:
                raise RuntimeError('Consumer countdown selected wrong destination')
            f['stages'].append('countdown_pending')
        elif address == 0x25f074:
            pointer = struct.unpack('<I', self.discovery.expected(0x25f1a4))[0]
            before = f['countdown']
            after = q.mem.read_ptr(pointer+4)
            # SUBGT/STRGT use signed comparison; negative values do not decrement.
            expected = before-1 if 0 < before < 0x80000000 else before
            if after != expected or r.r5 != expected:
                raise RuntimeError('Consumer countdown write mismatch')
            f['countdown_after'] = after
        elif address == 0x25f09c:
            if f.get('flag') != 0:
                raise RuntimeError('Consumer unset flag destination mismatch')
        elif address == 0x25f108:
            if f.get('flag') != 1 or f.get('countdown') != 0 or not f['producer']:
                raise RuntimeError('Consumer selected readiness path lacks matched producer/flag/countdown')
            f['stages'].append('zero_countdown')
        elif address == 0x25ec94:
            f['popup_error'] = True
        elif address == 0x25ecac:
            f['popup_type_valid'] = True
            f['popup'] = q.mem.read_ptr(f['owner']+0x140)
        elif address == 0x25ed98:
            if r.r6 != 0 or not f.get('popup_type_valid'):
                raise RuntimeError('Consumer popup false destination mismatch')
            f['stages'].append('popup_false')
        classification = ('unset' if f.get('flag') == 0 else
                          'zero' if f.get('countdown') == 0 else 'pending')
        self.record('original_consumer_boundary_'+hex(address), signature=(classification, bool(f['producer'])),
                    thread=tid, sp=r.sp, owner=hex(f['owner']), flag=f.get('flag'),
                    countdown=f.get('countdown'), countdown_after=f.get('countdown_after'),
                    stages=list(f['stages']))

    def summary(self):
        return dict(counts=dict(self.counts), pending_frames=self.frames, pending_calls=list(self.calls.values()),
                    latest=self.latest, acceptance=self.acceptance, retired=self.retired,
                    read_only=True, input_sent=False, prerequisite_written=False)
