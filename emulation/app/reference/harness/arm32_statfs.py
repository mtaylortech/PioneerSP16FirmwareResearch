"""Working ARM32 filesystem ABI fixture and sparse original storage boundaries."""
import hashlib
import struct
from pathlib import Path

FIELDS = (0xef53, 4096, 16384, 8192, 8192, 4096, 2048,
          0x12345678, 0x9abcdef0, 255, 4096, 0, 0, 0, 0, 0)
PAYLOAD = struct.pack('<16I', *FIELDS)
LIBC_POINTS = {0xb52a8: '70402de9', 0xb52c0: '000050e3', 0xb5304: '7080bde8'}
APP_POINTS = (0x2acb00, 0x2aee08, 0x2aee0c, 0x3296bc)


class Arm32Statfs:
    def __init__(self, emit, discovery, libc_path):
        self.emit = emit
        self.discovery = discovery
        self.libc_path = Path(libc_path)
        self.frames = {}
        self.queries = 0

    def context(self, q):
        return dict(thread=q.os.thread_management.cur_thread.id,
                    pc=hex(q.arch.regs.arch_pc), sp=hex(q.arch.regs.sp),
                    lr=hex(q.arch.regs.lr))

    def write(self, q, kind, argument, buf):
        # Existing success/synthetic-filesystem semantics are retained. Only the
        # ARM32 output contract is replaced; no host filesystem query is made.
        if q.arch.bits != 32:
            raise RuntimeError('ARM32 statfs fixture used outside 32-bit guest')
        self.queries += 1
        try:
            following = bytes(q.mem.read(buf + 64, 32))
        except Exception:
            following = None
        try:
            q.mem.write(buf, PAYLOAD)
            result = 0
        except Exception:
            result = -14
        after = bytes(q.mem.read(buf + 64, 32)) if following is not None else None
        self.emit('arm32_statfs_query', syscall=kind, argument=argument,
                  buffer=hex(buf), write_bytes=64 if result == 0 else 0,
                  result=result, adjacent_32_bytes_unchanged=(after == following)
                  if following is not None else None,
                  adjacent_before=following.hex() if following is not None else None,
                  adjacent_after=after.hex() if after is not None else None,
                  packed_fields=list(FIELDS), metadata='fixed synthetic filesystem fixture',
                  context=self.context(q), sequence=self.queries)
        return result

    def statfs(self, q, path, buf):
        try:
            name = q.mem.string(path)
        except Exception:
            return -14
        return self.write(q, 'statfs', name, buf)

    def fstatfs(self, q, fd, buf):
        return self.write(q, 'fstatfs', fd, buf)

    def install_syscalls(self, q):
        q.os.set_syscall(99, self.statfs)
        q.os.set_syscall(100, self.fstatfs)
        self.emit('arm32_statfs_fixture_installed', syscall_numbers=[99, 100],
                  output_bytes=len(PAYLOAD), output_format='<16I',
                  statfs64_overridden=False, fixed_fields=list(FIELDS))

    def install_boundaries(self, q):
        libc = self.libc_path.read_bytes()
        bases = set()
        for start, end, permissions, label, *_ in q.mem.map_info:
            if 'libc-2.13' in label or 'libc.so.6' in label:
                if bytes(q.mem.read(start, 16)) == libc[:16]:
                    bases.add(start)
        if len(bases) != 1:
            raise RuntimeError('Unique original libc mapping required for statvfs')
        base = bases.pop()
        checked = {}
        for offset, expected in LIBC_POINTS.items():
            actual = bytes(q.mem.read(base + offset, 4)).hex()
            if libc[offset:offset + 4].hex() != expected or actual != expected:
                raise RuntimeError('Original statvfs hook bytes differ')
            checked[hex(base + offset)] = actual
            q.hook_address(lambda guest, offset=offset: self.libc_boundary(guest, offset), base + offset)
        for address in APP_POINTS:
            expected = self.discovery.expected(address)
            if bytes(q.mem.read(address, 4)) != expected:
                raise RuntimeError('Original storage boundary bytes differ')
            checked[hex(address)] = expected.hex()
            q.hook_address(lambda guest, address=address: self.app_boundary(guest, address), address)
        self.emit('storage_boundaries_installed', original_bytes=checked,
                  libc_base=hex(base), libc_sha256=hashlib.sha256(libc).hexdigest(),
                  read_only=True)

    def app_boundary(self, q, address):
        if q.os.thread_management.cur_thread.id != self.discovery.main_tid:
            return
        details = {}
        if address == 0x2aee08:
            details = dict(path=q.mem.string(q.arch.regs.r0), output=hex(q.arch.regs.r1))
        if address == 0x2aee0c:
            details = dict(statvfs_return=q.arch.regs.r0)
        self.emit('original_storage_boundary', address=hex(address),
                  context=self.context(q), **details)

    def libc_boundary(self, q, offset):
        tid = q.os.thread_management.cur_thread.id
        if offset == 0xb52a8:
            frame = dict(entry_sp=q.arch.regs.sp, caller=q.arch.regs.lr,
                         path=q.mem.string(q.arch.regs.r0), output=q.arch.regs.r1,
                         entry_context=self.context(q), saved_frame_matches=False)
            self.frames[tid] = frame
            holder = {}
            def returned(guest):
                if guest.os.thread_management.cur_thread.id != tid:
                    return
                current = self.frames.get(tid)
                if current is not frame:
                    return
                frame.update(matched_return=bool(frame['saved_frame_matches'] and
                                                guest.arch.regs.sp == frame['entry_sp']),
                             return_value=guest.arch.regs.r0,
                             return_context=self.context(guest),
                             output_bytes=bytes(guest.mem.read(frame['output'], 72)).hex())
                self.emit('original_statvfs_return', frame=frame)
                del self.frames[tid]
                guest.hook_del(holder['hook'])
            holder['hook'] = q.hook_address(returned, frame['caller'])
            self.emit('original_statvfs_entry', frame=dict(frame))
        elif tid in self.frames:
            frame = self.frames[tid]
            if offset == 0xb52c0:
                self.emit('original_statvfs_after_statfs', result=q.arch.regs.r0,
                          context=self.context(q), path=frame['path'])
            elif offset == 0xb5304:
                saved = struct.unpack('<4I', bytes(q.mem.read(q.arch.regs.sp, 16)))
                frame['saved_frame_matches'] = (q.arch.regs.sp == frame['entry_sp'] - 16
                                                and saved[-1] == frame['caller'])
                self.emit('original_statvfs_before_pop', saved_words=list(saved),
                          saved_frame_matches=frame['saved_frame_matches'], context=self.context(q))
