"""One explicit observation configuration; finite independent session containment."""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time

DEADLINE_NAMES = ('term_at', 'kill_at', 'reap_at')
SUPERVISION_FILES = ('runtime_limits.py', 'watchdog.py', 'supervisor.py')


def finite_number(value, name):
    if type(value) not in (int, float):
        raise ValueError(name + ' must be a finite number')
    try:
        result = float(value)
    except OverflowError:
        raise ValueError(name + ' must be a finite number') from None
    if not math.isfinite(result):
        raise ValueError(name + ' must be a finite number')
    return result


def validate_deadlines(values):
    if any(name not in values for name in DEADLINE_NAMES):
        raise ValueError('three finite absolute monotonic deadlines required')
    result = {name: finite_number(values[name], name) for name in DEADLINE_NAMES}
    if not result['term_at'] <= result['kill_at'] <= result['reap_at']:
        raise ValueError('deadline order term <= kill <= reap required')
    return result


@dataclass(frozen=True)
class ObservationLimits:
    observation_seconds: int

    def __post_init__(self):
        if type(self.observation_seconds) is not int or self.observation_seconds <= 0:
            raise ValueError('explicit positive integer observation_seconds required')
        finite_number(self.observation_seconds + 200, 'observation duration and allowance')

    @property
    def offsets(self):
        return dict(zip(DEADLINE_NAMES, (self.observation_seconds + grace for grace in (5, 8, 10))))

    @property
    def launch_window_seconds(self):
        return 120

    @property
    def session_allowance_seconds(self):
        # Existing setup window plus observation/closure and 70s setup reserve.
        return self.launch_window_seconds + self.offsets['reap_at'] + 70

    def deadlines(self, started):
        started = finite_number(started, 'started_monotonic')
        return validate_deadlines({name: started + offset for name, offset in self.offsets.items()})

    def session_deadlines(self, stop_at):
        stop_at = finite_number(stop_at, 'session_stop_at')
        if stop_at <= time.monotonic() + 5:
            raise ValueError('fresh future absolute monotonic session stop deadline required')
        return validate_deadlines(dict(term_at=stop_at - 5, kill_at=stop_at - 2, reap_at=stop_at))

    def require_budget(self, now, stop_at, *, before_setup=False):
        now = finite_number(now, 'now')
        stop_at = finite_number(stop_at, 'session_stop_at')
        needed = self.offsets['reap_at'] + (10 if before_setup else 0)
        if now + needed >= stop_at:
            raise ValueError(f'Authorized total budget conflict: {self.observation_seconds}s observation '
                             f'requires more than {needed}s remaining including setup/closure; '
                             f'only {stop_at - now:.3f}s remain. Observation was not shortened.')

    def configuration(self):
        return dict(observation_seconds=self.observation_seconds, deadline_offsets=self.offsets,
                    launch_window_required_seconds=self.offsets['reap_at'] + 10,
                    guest_window_required_seconds=self.offsets['reap_at'],
                    launch_window_seconds=self.launch_window_seconds,
                    enclosing_session_allowance_seconds=self.session_allowance_seconds)


def verify_tested_supervision(directory, record_path):
    directory = Path(directory)
    record = json.loads(Path(record_path).read_text())
    if not record.get('passed') or not record.get('actual_guest_spawn_controls_passed'):
        raise ValueError('Corrected actual guest-spawn supervision controls did not pass')
    for name in SUPERVISION_FILES:
        key = 'supervision/' + name
        actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
        if record.get('code_identities', {}).get(key) != actual:
            raise ValueError('Tested supervision identity differs: ' + name)
    return record
