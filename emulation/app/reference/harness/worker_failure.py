"""Contain failures of every installed Linux worker, including sched_cb errors."""
import traceback
class WorkerFailures:
    def __init__(self, emit): self.emit = emit; self.failures = []; self.installed = False
    def install(self, q):
        from qiling.os.linux.thread import QlLinuxThread
        original = QlLinuxThread._run
        ledger = self
        def contained(thread):
            try: return original(thread)
            except Exception as error:
                if thread.ql is q:
                    row = dict(thread=thread.id, type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
                    ledger.failures.append(row)
                    ledger.emit('worker_failure_owned_stop', **row)
                    # _run has left Unicorn before reaching this handler.
                    q.emu_stop(); q.os.thread_management.stop()
                raise
        QlLinuxThread._run = contained
        self.original = original; self.installed = True
    def outcome(self, outer):
        if not self.failures: return outer
        return dict(status='exception', type=self.failures[0]['type'], message=self.failures[0]['message'],
                    source='worker', outer_outcome=outer, worker_failures=self.failures)
    def close(self):
        if self.installed:
            from qiling.os.linux.thread import QlLinuxThread
            QlLinuxThread._run = self.original; self.installed = False
