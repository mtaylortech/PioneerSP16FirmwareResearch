"""Check guest descriptors before delegating to the installed ioctl handler."""
from qiling.os.posix.syscall.ioctl import ql_syscall_ioctl


def guarded_ioctl(q, fd, cmd, arg):
    # ARM registers deliver unsigned 0xffffffff for failed descriptor -1.
    # Invalid/closed descriptors must return EBADF without indexing or I/O.
    if not 0 <= fd < len(q.os.fd) or q.os.fd[fd] is None:
        return -9
    return ql_syscall_ioctl(q, fd, cmd, arg)
