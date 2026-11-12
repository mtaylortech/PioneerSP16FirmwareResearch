"""Owner-targeted advisory expiry; the independent process watchdog is retained.

Start from the outer probe greenlet, before starting Qiling. SIGALRM never
raises into whichever guest greenlet happens to be running. It only latches
expiry and requests an emulator stop. gevent.Timeout targets the starting
greenlet and delivers DeadlineExpired when execution next reaches the hub.
Native code that never returns/yields still requires the independent watchdog.
"""
import math
import signal
import time

import gevent


class DeadlineExpired(TimeoutError):
    pass


class _OwnerTimeout(gevent.Timeout):
    def __init__(self, seconds, guard):
        self.guard = guard
        super().__init__(seconds, guard.exception)

    def _on_expiration(self, owner, exception):
        self.guard._mark("outer_timer")
        # Notification errors cannot prevent the targeted owner exception.
        self.guard._notify()
        super()._on_expiration(owner, exception)


class OuterDeadline:
    def __init__(self, seconds, *, request_stop=None, on_expire=None):
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError("positive finite advisory seconds required")
        self.seconds = float(seconds)
        self.request_stop = request_stop
        self.on_expire = on_expire
        self.exception = DeadlineExpired("Bounded startup-probe wall-clock deadline reached")
        self.expired = False
        self.sources = []
        self.stop_errors = []
        self.notification_error = None
        self.notified = False
        self.owner = None
        self.started = None
        self.timer = None
        self.previous_handler = None
        self.closed = False

    def _mark(self, source):
        self.expired = True
        self.sources.append({"source": source, "monotonic": time.monotonic()})
        if self.request_stop is not None:
            try:
                self.request_stop()
            except Exception as error:
                self.stop_errors.append({"source": source, "error": repr(error)})

    def _signal(self, *_unused):
        # Do not emit diagnostics or throw an exception from a worker greenlet.
        self._mark("SIGALRM")

    def _notify(self):
        if self.notified:
            return
        self.notified = True
        if self.on_expire is not None:
            try:
                self.on_expire()
            except Exception as error:
                self.notification_error = repr(error)

    def start(self):
        if self.owner is not None or self.closed:
            raise RuntimeError("deadline instance may be started only once")
        if signal.getitimer(signal.ITIMER_REAL) != (0.0, 0.0):
            raise RuntimeError("existing ITIMER_REAL timer must not be replaced")
        self.owner = gevent.getcurrent()
        self.started = time.monotonic()
        self.previous_handler = signal.getsignal(signal.SIGALRM)
        self.timer = _OwnerTimeout(self.seconds, self)
        try:
            signal.signal(signal.SIGALRM, self._signal)
            # Timeout.start captures the current outer owner, never a guest.
            self.timer.start()
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        except BaseException:
            self.close()
            raise
        return self

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.timer is not None:
            self.timer.close()
        if self.previous_handler is not None:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self.previous_handler)

    def check(self):
        """Cover natural Qiling return racing the owner timer at the same yield."""
        if gevent.getcurrent() is not self.owner:
            raise RuntimeError("deadline.check must run in the starting owner")
        if self.expired or time.monotonic() >= self.started + self.seconds:
            if not self.expired:
                self._mark("owner_return_check")
            self._notify()
            raise self.exception

    def summary(self):
        return {"seconds": self.seconds, "started_monotonic": self.started,
                "expired": self.expired, "sources": self.sources,
                "stop_errors": self.stop_errors,
                "notification_error": self.notification_error,
                "notified": self.notified,
                "closed": self.closed, "owner_targeted": True,
                "independent_watchdog_required": True,
                "owner_current": gevent.getcurrent() is self.owner,
                "owner_dead": getattr(self.owner, "dead", None),
                "outer_timer_pending": self.timer.pending if self.timer else None,
                "alarm_remaining": signal.getitimer(signal.ITIMER_REAL)[0],
                "alarm_handler_matches": signal.getsignal(signal.SIGALRM) == self._signal}
