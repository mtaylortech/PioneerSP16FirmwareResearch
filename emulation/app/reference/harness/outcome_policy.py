"""Deadline expiry and execution failure are independent facts."""
def final_outcome(outcome, deadline_reached, guest_exit_code=None):
    result = dict(outcome)
    if deadline_reached and result.get('status') != 'exception':
        result = dict(status='bounded_stop', reason=result.get('reason','requested wall-clock deadline'),
                      guest_exit_code=guest_exit_code)
    result['deadline_reached'] = bool(deadline_reached)
    return result


def launch_failed(report):
    outcome = report.get('native_outcome')
    return bool(not report.get('native_final_present') or not isinstance(outcome, dict)
                or outcome.get('status') == 'exception' or report.get('exception')
                or report.get('cleanup_failure') or any(report.get('endpoints', {}).values())
                or report.get('closure', {}).get('failure'))
