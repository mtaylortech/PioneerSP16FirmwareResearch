"""Prepared narrow wiring correction; deliberately NOT installed in select trial."""
from qiling.const import QL_INTERCEPT
from wait_observer import compose_syscall

def install_pacer_names(q, pacer):
    def deliver(guest, option, arg2, arg3, arg4, arg5):
        if option == 15:
            pacer.observe_thread_name(guest, guest.mem.string(arg2))
    compose_syscall(q, 'prctl', deliver, QL_INTERCEPT.ENTER)
