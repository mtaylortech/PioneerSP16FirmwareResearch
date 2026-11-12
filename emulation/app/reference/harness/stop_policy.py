"""Established intentional denial classification; vfork guard remains unchanged."""
def decisive_event(event):
    if event.get('kind') in ('lifecycle_mismatch','invalid_memory','timer_observer_error','timer_futex_error','worker_failure_owned_stop','synchronous_emulator_exception_context','emulator_exception_context','original_x11_event_payload_error','original_input_handler_error'):
        return True
    if event.get('kind') == 'denied_host_operation':
        # Both held E30 and this partial run report this successfully denied
        # request. Keep the guest deny handler unchanged. No vfork is allowed.
        return event.get('syscall') != 'ql_syscall_vfork'
    return False
