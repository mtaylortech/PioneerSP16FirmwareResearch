"""Selected redraw clipping, dirty rectangles and deferred initialization queue."""
import struct
import time

POINTS = {0x7fd140:'clipped_state_gate', 0x7fd150:'rectangle_collection_call',
          0x7fd154:'rectangle_collection_return', 0x7fd17c:'initialization_call',
          0x7fd180:'initialization_return', 0x4ffc80:'rectangle_collection_entry',
          0x500060:'empty_collection_branch', 0x4ffe48:'append_rectangle_last_store',
          0x500078:'empty_collection_count_store', 0x4ffe4c:'collection_epilogue',
          0x69bf5c:'initialization_entry', 0x69bfec:'existing_initialization_state',
          0x69c10c:'new_queue_service_construction', 0x69bfc8:'queue_head_publication',
          0x69bfd8:'queue_service_signal_call', 0x637edc:'queue_signal_entry',
          0x637f0c:'condition_signal_call'}


class RedrawObserver:
    def __init__(self, emit, started, discovery):
        self.emit, self.started, self.discovery = emit, started, discovery
        self.selected = None; self.records = []; self.handles = {}; self.pending = {}; self.complete = False
        self.collection = None; self.state = None

    def memory(self, q, pointer, size):
        try: return bytes(q.mem.read(pointer, size)).hex() if pointer else None
        except Exception as ex: return dict(read_error=repr(ex))

    def rectangle(self, q, pointer):
        raw = bytes(q.mem.read(pointer, 16))
        return dict(pointer=hex(pointer), bytes=raw.hex(), xywh=list(struct.unpack('<4i', raw)))

    def object_state(self, q):
        obj = int(self.selected['object'], 16)
        ptr = q.mem.read_ptr(obj + 0x34, 4)
        return dict(object=hex(obj), width=q.mem.read_ptr(obj+0x48, 4), height=q.mem.read_ptr(obj+0x4c, 4),
                    pointer34=hex(ptr), pointer34_bytes=self.memory(q, ptr, 0x40), derived_state8=q.mem.read_ptr(ptr+8, 4) if ptr else None)

    def collection_state(self, q, pointer):
        data, capacity, count = struct.unpack('<3I', bytes(q.mem.read(pointer, 12)))
        return dict(object=hex(pointer), data=hex(data), capacity=capacity, count=count,
                    rectangles=self.memory(q, data, 16*min(count, 8)) if count else None, capture_limit=8)

    def record(self, name, q, **extra):
        row = dict(boundary=name, thread=q.os.thread_management.cur_thread.id, pc=hex(q.arch.regs.arch_pc),
                   sp=hex(q.arch.regs.sp), lr=hex(q.arch.regs.lr), elapsed=time.monotonic()-self.started,
                   event_sha256=self.selected['event_sha256'], read_only=True, **extra)
        self.records.append(row); self.emit('redraw_boundary', **row)

    def activate(self, q, call, event):
        self.selected = dict(call, thread=event['thread'], event_sha256=event['event_sha256'])
        if call['target'] != '0x7fd0d0':
            raise RuntimeError('Selected redraw target changed; inspect original target before launch')
        for addr, name in {0x7fd0d0:'target_entry', **POINTS}.items():
            expected = self.discovery.expected(addr); actual = bytes(q.mem.read(addr, 4))
            if actual != expected: raise RuntimeError('Redraw loaded bytes differ '+hex(addr))
            self.handles[addr] = q.hook_address(lambda guest, a=addr: self.visit(guest, a), addr)
        self.emit('redraw_observer_activated', points={hex(a):self.discovery.expected(a).hex() for a in self.handles}, selected=self.selected, read_only=True)

    def visit(self, q, a):
        if self.complete or q.os.thread_management.cur_thread.id != self.selected['thread']: return
        name = 'target_entry' if a == 0x7fd0d0 else POINTS[a]
        sp = q.arch.regs.sp
        if a == 0x7fd0d0:
            self.state = self.object_state(q)
            self.record(name, q, object_state=self.state, rectangle=self.rectangle(q, q.arch.regs.r1))
        elif a == 0x7fd140:
            self.record(name, q, object_state=self.object_state(q), rectangle=self.rectangle(q, sp+0x10),
                        derived_r3=q.arch.regs.r3, state_r4=hex(q.arch.regs.r4))
        elif a == 0x7fd150:
            self.collection = q.arch.regs.r0
            row = dict(collection=self.collection_state(q, self.collection), rectangle=self.rectangle(q, q.arch.regs.r1))
            self.pending[(a+4, sp)] = row; self.record(name, q, **row)
        elif a == 0x7fd17c:
            row = dict(state_object=hex(q.arch.regs.r0), delay_argument=q.arch.regs.r1,
                       state_bytes=self.memory(q, q.arch.regs.r0, 0x40))
            self.pending[(a+4, sp)] = row; self.record(name, q, **row)
        elif a in (0x7fd154, 0x7fd180):
            row = self.pending.pop((a, sp), None)
            if row: self.record(name, q, call=row, matched_thread_sp=True, result=hex(q.arch.regs.r0),
                                object_state=self.object_state(q), collection=self.collection_state(q, self.collection) if self.collection else None)
        elif a in (0x4ffc80, 0x500060, 0x4ffe48, 0x500078, 0x4ffe4c):
            if not self.collection: return
            self.record(name, q, collection=self.collection_state(q, self.collection), registers={r:hex(q.arch.regs.read(r)) for r in ('r0','r1','r2','r3','r6','r7')})
        else:
            self.record(name, q, registers={r:hex(q.arch.regs.read(r)) for r in ('r0','r1','r2','r3','r4','r5','r6')},
                        state_bytes=self.memory(q, int(self.state['pointer34'], 16), 0x40),
                        queue_service_bytes=self.memory(q, q.arch.regs.r5, 0xe8) if a in (0x69bfc8,0x69bfd8) else None)

    def retire(self, q):
        self.complete = True
        for handle in self.handles.values(): q.hook_del(handle)
        self.handles = {}
        self.emit('redraw_selected_observations_complete', pending=list(self.pending.values()), records=len(self.records), interior_hooks_retired=True)

    def summary(self):
        return dict(enabled=True, selected=self.selected, records=self.records, pending=list(self.pending.values()), completed=self.complete)
