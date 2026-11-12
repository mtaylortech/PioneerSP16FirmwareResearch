"""A5 corrected local gate for the observed libpthread cancellation recv path.

A4 used app LR 0x51d07c and never matched: actual syscall PC/LR were
0x90244a44/0x90244a34. This replacement derives those addresses from the
loaded original libpthread mapping, verifies its recv wrapper, and also checks
the saved app return at SP+4 (push six registers, then pop the four arguments).
Invalid descriptors still return held literal -1; no host socket is created.
"""
import math
from pathlib import Path


class InvalidRecvPacer:
    THREAD_NAME = 'autoip_recv_arp'
    APP_RETURN = 0x51d07c
    RECV_START = 0xea00
    RECV_SIZE = 132
    SYSCALL_PC_OFFSET = 0xea44
    SYSCALL_LR_OFFSET = 0xea34
    NR_OPEN = 1024

    def __init__(self, recv, recvfrom, sleep, delay=0.01):
        if not math.isfinite(delay) or delay <= 0:
            raise ValueError('finite positive cooperative pacing delay required')
        self.receivers = {'recv': recv, 'recvfrom': recvfrom}
        self.sleep = sleep
        self.delay = delay
        self.thread_names = {}
        self.paced_counts = {}
        self.mapping = None
        self.last_saved_app_return = None

    def install(self, q, library_path=None):
        from elftools.elf.elffile import ELFFile
        source = Path(library_path or Path(__file__).with_name('rootfs')/'lib/libpthread.so.0')
        with source.open('rb') as f:
            elf = ELFFile(f)
            symbol = next(s for s in elf.get_section_by_name('.dynsym').iter_symbols() if s.name == 'recv')
            if symbol['st_value'] != self.RECV_START or symbol['st_size'] != self.RECV_SIZE:
                raise RuntimeError('Original libpthread recv symbol differs')
            segment = next(s for s in elf.iter_segments() if s['p_type']=='PT_LOAD'
                           and s['p_vaddr'] <= self.RECV_START < s['p_vaddr']+s['p_filesz'])
            offset = self.RECV_START - segment['p_vaddr']
            expected = segment.data()[offset:offset+self.RECV_SIZE]
        candidates = sorted({a for a,b,perm,label,*other in q.mem.map_info
                             if 'libpthread' in label and bytes(q.mem.read(a,4)) == b'\x7fELF'})
        if len(candidates) != 1:
            raise RuntimeError('Unique loaded libpthread ELF mapping required')
        base = candidates[0]  # Held ELF's first PT_LOAD has p_vaddr == 0.
        address = base+self.RECV_START
        actual = bytes(q.mem.read(address,self.RECV_SIZE))
        if actual != expected:
            raise RuntimeError('Loaded original libpthread recv wrapper bytes differ')
        self.mapping = {'source':str(source), 'base':hex(base), 'wrapper_address':hex(address),
                        'wrapper_size':self.RECV_SIZE, 'expected_bytes':expected.hex(),
                        'actual_bytes':actual.hex(), 'matches':True,
                        'syscall_pc':hex(base+self.SYSCALL_PC_OFFSET),
                        'syscall_lr':hex(base+self.SYSCALL_LR_OFFSET)}
        return dict(self.mapping)

    def observe_thread_name(self, q, name):
        self.thread_names[q.os.thread_management.cur_thread.id] = name

    def _call(self, kind, q, sockfd, *arguments):
        current = q.os.thread_management.cur_thread
        invalid = sockfd not in range(self.NR_OPEN) or q.os.fd[sockfd] is None
        scoped = (self.mapping is not None
                  and self.thread_names.get(current.id) == self.THREAD_NAME
                  and q.arch.regs.arch_pc == int(self.mapping['syscall_pc'],16)
                  and q.arch.regs.lr == int(self.mapping['syscall_lr'],16))
        if invalid and scoped:
            saved_return = q.mem.read_ptr(q.arch.regs.sp+4)
            self.last_saved_app_return = hex(saved_return)
            scoped = saved_return == self.APP_RETURN
        if not invalid or not scoped:
            return self.receivers[kind](q, sockfd, *arguments)
        key = kind + ':' + str(current.id)
        self.paced_counts[key] = self.paced_counts.get(key, 0) + 1
        q.emu_stop()
        # Same held epoll fixture pattern: sleep only after context is saved.
        current.sched_cb = self._scheduled_sleep
        return -1

    def _scheduled_sleep(self, current):
        return self.sleep(self.delay)

    def recv(self, q, sockfd, buf, length, flags):
        return self._call('recv', q, sockfd, buf, length, flags)

    def recvfrom(self, q, sockfd, buf, length, flags, addr, addrlen):
        return self._call('recvfrom', q, sockfd, buf, length, flags, addr, addrlen)

    def summary(self):
        return {'fixture':'invalid_autoip_recv_cooperative_pacing', 'gate_revision':'A5 observed libpthread PC/LR plus saved application return',
                'thread_name':self.THREAD_NAME, 'mapping':self.mapping,
                'saved_app_return_expected':hex(self.APP_RETURN), 'last_saved_app_return':self.last_saved_app_return,
                'delay_seconds':self.delay, 'paced_counts':dict(self.paced_counts),
                'preserved_invalid_result':-1, 'host_socket_created':False}
