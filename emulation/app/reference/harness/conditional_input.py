"""Conditional bridge in existing owner loop; no new process or deadline owner."""
import json
from pathlib import Path
from live_prerequisite import evaluate, publish
from spawn_input_request import prepare


class ConditionalInput:
    def __init__(self, clock):
        self.enabled = clock.get('input_authorized') is True
        self.done = False
        self.last_samples = None
        self.status = dict(enabled=self.enabled, helper_requested=False, input_sent=False)

    def poll(self, run, python, spawn):
        if not self.enabled or self.done:
            return self.status
        run = Path(run).resolve()
        try:
            display = json.loads((run/'display-observations.json').read_text())
            samples = [c for c in display['captures'] if c.get('scope') == 'exact original guest-created InputOutput drawable']
            key = tuple(c.get('finished_monotonic') for c in samples[-2:])
            if len(key) < 2 or key == self.last_samples:
                return self.status
            self.last_samples = key
            record = evaluate(run)
        except (OSError, ValueError, KeyError, TypeError) as error:
            self.status['withheld_reason'] = type(error).__name__ + ': ' + str(error)
            return self.status
        # Publication and spawn are single-use, including an uncertain failure.
        self.done = True
        try:
            record = publish(run, record)
            xid = int(record['owned_pixel_evidence']['window'], 16)
            owned, socket, request, deadline = prepare(run, python, execute=True,
                interaction='click', xid=xid, x=250, y=350)
            self.status.update(prerequisite_bound=True, window=hex(xid), coordinates=[250, 350],
                               input_response_proved=False)
            self.status['helper_requested'] = True
            self.status['spawn_receipt'] = spawn(request, deadline)
        except Exception as error:
            self.status['withheld_reason'] = type(error).__name__ + ': ' + str(error)
            self.status['no_retry'] = True
        return self.status
