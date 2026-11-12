"""One optional connection: guest :0 -> authenticated local Xvfb :16.

No TCP/UDP, arbitrary Unix paths, or abstract namespace is allowed. This module
does not alter firmware bytes. All host descriptors remain nonblocking.
"""
from pathlib import Path
import errno
import os
import select
import socket
import stat
import struct
import time

GUEST_ENDPOINT = b'/tmp/.X11-unix/X0'
HOST_ENDPOINT = '/tmp/.X11-unix/X16'


def cookie_from_file(path):
    data = Path(path).read_bytes()
    pos = 0
    while pos < len(data):
        family = struct.unpack_from('>H', data, pos)[0]
        pos += 2
        values = []
        for _ in range(4):
            length = struct.unpack_from('>H', data, pos)[0]
            pos += 2
            values.append(data[pos:pos+length])
            pos += length
        address, number, name, cookie = values
        if family == 65535 and number == b'16' and name == b'MIT-MAGIC-COOKIE-1' and len(cookie) == 16:
            return name, cookie
    raise ValueError('No scoped display-16 MIT-MAGIC-COOKIE-1 record')


def verify_endpoint(auth_path):
    """Verify X11 setup, not merely an existing path or DISPLAY variable."""
    info = os.stat(HOST_ENDPOINT)
    if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.getuid():
        raise ValueError('Expected a local X16 socket owned by this host user')
    name, cookie = cookie_from_file(auth_path)
    pad = lambda value: value + b'\0' * (-len(value) % 4)
    request = struct.pack('<BBHHHHH', ord('l'), 0, 11, 0, len(name), len(cookie), 0) + pad(name) + pad(cookie)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(2)
        connection.connect(HOST_ENDPOINT)
        connection.sendall(request)
        reply = b''
        while len(reply) < 8:
            part = connection.recv(8-len(reply))
            if not part:
                raise RuntimeError('X server closed before setup header')
            reply += part
        status, reason_length, major, minor, units = struct.unpack('<BBHHH', reply)
        if status != 1:
            raise RuntimeError('X11 setup rejected: status=%d, reason_length=%d' % (status, reason_length))
    return {'endpoint': HOST_ENDPOINT, 'protocol_major': major,
            'protocol_minor': minor, 'setup_status': status,
            'setup_body_bytes': units * 4, 'authentication': 'MIT-MAGIC-COOKIE-1',
            'cookie_disclosed': False, 'guest_display': ':0', 'host_display': ':16'}


class LocalDisplayFixture:
    def __init__(self, factory, emit, sleep):
        self.factory = factory
        self.emit = emit
        self.sleep = sleep
        self.descriptors = {}
        self.setup_observed = set()
        self.setup_reply_observed = set()

    def owns(self, q, fd):
        return 0 <= fd < len(q.os.fd) and q.os.fd[fd] is self.descriptors.get(fd) and fd in self.descriptors

    def context(self, q):
        return {'pc': hex(q.arch.regs.arch_pc), 'lr': hex(q.arch.regs.lr),
                'registers': {name: hex(q.arch.regs.read(name)) for name in ('r0', 'r1', 'r2', 'r3')}}

    def socket(self, q, domain, socktype, protocol):
        # Linux ARM SOCK_NONBLOCK / SOCK_CLOEXEC may accompany SOCK_STREAM.
        if domain != 1 or socktype & 15 != 1 or socktype & ~(15 | 0x800 | 0x80000) or protocol != 0:
            self.emit('display_socket_denied', domain=domain, socktype=socktype,
                      protocol=protocol, result=-errno.EPERM, **self.context(q))
            return -errno.EPERM
        fd = next((i for i, item in enumerate(q.os.fd) if item is None), -1)
        if fd < 0:
            return -errno.EMFILE
        obj = self.factory(1, 1, 0)
        os.set_blocking(obj.fileno(), False)
        q.os.fd[fd] = obj
        self.descriptors[fd] = obj
        self.emit('display_socket', descriptor=fd, result=fd, **self.context(q))
        return fd

    def connect(self, q, fd, address, length):
        raw = bytes(q.mem.read(address, min(length, 110))) if 2 <= length <= 110 else b''
        path = raw[2:].split(b'\0', 1)[0]
        if not self.owns(q, fd) or raw[:2] != b'\1\0' or path != GUEST_ENDPOINT:
            self.emit('display_connect_denied', descriptor=fd, guest_path=path.decode('utf-8', 'replace'),
                      result=-errno.EPERM, **self.context(q))
            return -errno.EPERM
        obj = q.os.fd[fd]
        try:
            # One known local endpoint. Bounded connect, then nonblocking I/O.
            obj.socket.settimeout(0.5)
            obj.connect(HOST_ENDPOINT)
            result = 0
        except OSError as exc:
            result = -(exc.errno or errno.ETIMEDOUT)
        finally:
            obj.socket.setblocking(False)
        self.emit('display_connect', descriptor=fd, guest_path=path.decode(),
                  host_endpoint=HOST_ENDPOINT, result=result, **self.context(q))
        return result

    def readv(self, q, fd, vec, count):
        if not 0 <= count <= 1024:
            return -errno.EINVAL
        vectors = [struct.unpack('<II', bytes(q.mem.read(vec+i*8, 8))) for i in range(count)]
        total = sum(length for _, length in vectors)
        if total > 1048576:
            return -errno.EINVAL
        try:
            data = q.os.fd[fd].read(total)
        except OSError as exc:
            return -(exc.errno or errno.EIO)
        offset = 0
        for address, length in vectors:
            chunk = data[offset:offset+length]
            if chunk:
                q.mem.write(address, chunk)
            offset += len(chunk)
        return len(data)

    def socket_name(self, q, fd, address, length_ptr, peer):
        try:
            # Preserve the guest-visible endpoint instead of asking Qiling to
            # reverse-map an explicitly permitted host path outside rootfs.
            q.os.fd[fd].getpeername() if peer else q.os.fd[fd].getsockname()
        except OSError as exc:
            return -(exc.errno or errno.EIO)
        raw = b'\1\0' + (GUEST_ENDPOINT+b'\0' if peer else b'')
        capacity = q.mem.read_ptr(length_ptr)
        if capacity:
            q.mem.write(address, raw[:capacity])
        q.mem.write_ptr(length_ptr, len(raw))
        self.emit('display_socket_name', descriptor=fd, peer=peer,
                  result=0, **self.context(q))
        return 0

    def writev(self, q, fd, vec, count):
        if not 0 <= count <= 1024:
            return -errno.EINVAL
        vectors = [struct.unpack('<II', bytes(q.mem.read(vec+i*8, 8))) for i in range(count)]
        if sum(length for _, length in vectors) > 1048576:
            return -errno.EINVAL
        data = b''.join(bytes(q.mem.read(address, length)) for address, length in vectors)
        if fd not in self.setup_observed and len(data) >= 12 and data[0] in (ord("l"), ord("B")):
            self.setup_observed.add(fd)
            order = "<" if data[0] == ord("l") else ">"
            _, _, major, minor, name_length, cookie_length, _ = struct.unpack(order + "BBHHHHH", data[:12])
            self.emit("display_setup_metadata", descriptor=fd, protocol_major=major, protocol_minor=minor,
                      authorization_name_length=name_length, authorization_data_length=cookie_length,
                      cookie_disclosed=False, **self.context(q))
        try:
            return q.os.fd[fd].write(data)
        except OSError as exc:
            return -(exc.errno or errno.EIO)

    def poll(self, q, pointer, count, timeout):
        # Used only if the entire poll set consists of fixture descriptors.
        rows = [struct.unpack('<ihh', bytes(q.mem.read(pointer+i*8, 8))) for i in range(count)]
        end = time.monotonic() + (timeout / 1000 if timeout >= 0 else 2)
        while True:
            ready_count = 0
            for i, (fd, flags, _) in enumerate(rows):
                hostfd = q.os.fd[fd].fileno()
                read, write, error = select.select([hostfd] if flags & 1 else [],
                                                   [hostfd] if flags & 4 else [], [hostfd], 0)
                ready = (1 if read else 0) | (4 if write else 0) | (8 if error else 0)
                q.mem.write(pointer+i*8+6, struct.pack('<h', ready))
                ready_count += bool(ready)
            if ready_count or timeout == 0 or time.monotonic() >= end:
                return ready_count
            self.sleep(0.001)
