"""Conservative input prerequisite assessment; pure function, no file writes.

Call only on fresh live consumer receipts and independently verified owned
drawable observations. Synthetic controls do not authorize input or firmware.
The existing input helper repeats live ownership/geometry and pixel checks.
"""
def assess(consumer, pixels):
    a = consumer.get('acceptance') or {}
    f = a.get('frame') or {}
    calls = f.get('call_returns') or {}
    names = ('cancel_completion_timer', 'schedule_zero_100ms', 'schedule_one_50ms',
             'show_progress_false', 'popup_component', 'remove_popup',
             'popup_visibility_false', 'release_controller_state')
    original = bool(a.get('passed') and a.get('original_completion_state_evidence')
                    and a.get('popup_removed') and f.get('saved_return_matched')
                    and f.get('popup_saved_return_matched') and f.get('popup_type_valid')
                    and not f.get('popup_error') and f.get('producer')
                    and all(calls.get(n, {}).get('matched_thread_sp_entry')
                            and calls[n].get('entry_observed') for n in names))
    region = pixels.get('exact_region') or []
    stable = bool(pixels.get('ownership_verified') and pixels.get('current_original_returned_xid')
                  and pixels.get('viewable_input_output') and len(region) == 4 and region[2:] == [800,480]
                  and pixels.get('nonblack_pixels', 0) > 0
                  and pixels.get('sample_count', 0) >= 2 and pixels.get('stable')
                  and pixels.get('pixel_sha256') and pixels.get('fresh_live_observations'))
    checks = dict(original_main_consumer_and_downstream_state=original, stable_exact_owned_pixels=stable)
    return dict(passed=all(checks.values()), checks=checks,
                original_completion_state_evidence=a if original else None,
                owned_pixel_evidence=pixels if stable else None,
                file_absence_is_failure=False, completed_startup_proved=False,
                input_response_proved=False, input_sent=False,
                limits='Prerequisite for conditional diagnostic input only. Original usability and full startup remain open.')
