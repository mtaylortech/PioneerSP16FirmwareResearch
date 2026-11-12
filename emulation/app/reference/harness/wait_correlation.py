"""Single-use syscall generations, independent of reused wrapper stack frames."""
class WaitCorrelation:
    def __init__(self):
        self.frames = {}; self.calls = {}; self.next_frame = 0; self.next_call = 0
        self.consumed = 0
    def enter(self, tid, sp, caller):
        self.next_frame += 1
        row = dict(frame_generation=self.next_frame, sp=sp, caller=caller)
        self.frames[tid] = row
        return row
    def begin(self, tid, sp, sequence):
        old = self.calls.get(tid)
        if old and not old.get('consumed'):
            raise RuntimeError('Unconsumed selected syscall generation')
        self.next_call += 1
        frame = self.frames.get(tid)
        row = dict(syscall_generation=self.next_call, frame_generation=frame['frame_generation'] if frame else None,
                   sequence=sequence, sp=sp, consumed=False, completion=None, immediate=None)
        self.calls[tid] = row
        return row
    def immediate(self, tid, generation, result):
        row = self.calls[tid]
        if row['syscall_generation'] != generation or row['completion'] is not None:
            raise RuntimeError('Immediate result generation differs')
        row['immediate'] = result
    def complete(self, tid, generation, completed):
        row = self.calls[tid]
        if row['syscall_generation'] != generation or row['consumed'] or row['completion'] is not None or row['immediate'] is not None:
            raise RuntimeError('Deferred completion generation reused or differs')
        row['completion'] = completed
    def resume(self, tid, sp, r0):
        row = self.calls.get(tid)
        if row is None or row['consumed']: return None
        frame = self.frames.get(tid)
        if sp != row['sp'] or (frame and frame['frame_generation'] != row['frame_generation']):
            raise RuntimeError('Selected syscall resumption frame/generation differs')
        if row['completion'] is not None: expected = row['completion']['result']
        elif row['immediate'] is not None: expected = row['immediate']
        else: raise RuntimeError('Selected syscall resumed before completion')
        if r0 != expected & 0xffffffff: raise RuntimeError('Selected live resumption R0 differs')
        row['consumed'] = True; self.consumed += 1
        return dict(row)
