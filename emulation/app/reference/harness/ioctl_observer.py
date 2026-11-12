"""Sparse observation of the guarded ioctl and its original caller continuation."""
from ioctl_fixture import guarded_ioctl


class IoctlObserver:
    def __init__(self, emit, discovery):
        self.emit = emit
        self.discovery = discovery
        self.followed = False

    @staticmethod
    def context(q):
        return dict(thread=q.os.thread_management.cur_thread.id,
                    pc=hex(q.arch.regs.arch_pc), lr=hex(q.arch.regs.lr),
                    sp=hex(q.arch.regs.sp), r0=hex(q.arch.regs.r0))

    def call(self, q, fd, cmd, arg):
        selected = fd == 0xffffffff and cmd == 0x8927 and not self.followed
        if not selected:
            return guarded_ioctl(q, fd, cmd, arg)
        self.followed = True
        before = bytes(q.mem.read(arg, 40))
        context = self.context(q)
        caller = q.arch.regs.lr
        if caller != 0x5232a0:
            raise RuntimeError('Selected ioctl original caller differs')
        checked = {}
        for address in (caller, caller + 4):
            expected = self.discovery.expected(address)
            actual = bytes(q.mem.read(address, 4))
            if actual != expected:
                raise RuntimeError('Original ioctl caller bytes differ')
            checked[hex(address)] = actual.hex()
        self.emit('ioctl_caller_bytes', original_bytes=checked, read_only=True)
        result = guarded_ioctl(q, fd, cmd, arg)
        self.emit('guarded_ioctl_result', fd=hex(fd), cmd=hex(cmd), arg=hex(arg),
                  ifreq_name=before[:16].split(b'\0', 1)[0].decode('ascii'),
                  result=result, ifreq_40_bytes_unchanged=before == bytes(q.mem.read(arg, 40)),
                  context=context)
        for address in (caller, caller + 4):
            holder = {}
            def boundary(guest, address=address, holder=holder):
                if guest.os.thread_management.cur_thread.id != context['thread']:
                    return
                self.emit('original_ioctl_caller' if address == caller else
                          'original_ioctl_caller_subsequent',
                          address=hex(address), context=self.context(guest),
                          previous_instruction_executed=checked[hex(caller)]
                          if address == caller + 4 else None)
                guest.hook_del(holder['hook'])
            holder['hook'] = q.hook_address(boundary, address)
        return result
