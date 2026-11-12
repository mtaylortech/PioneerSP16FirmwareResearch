"""Observer-side API for the independent process owner in watchdog.py.

Absolute deadlines use this host's time.monotonic() clock. Never pass UTC epochs.
This class owns only the watchdog direct child; the watchdog owns runtime groups.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import select
import socket
import subprocess
import sys
import tempfile
import time

from .runtime_limits import ObservationLimits


class WatchdogClient:
    def __init__(self, root, proc, socket_path):
        self.root = Path(root).resolve()
        self.proc = proc
        self.socket_path = Path(socket_path)

    @classmethod
    def start(cls, root, session_stop_at, python=None, ready_deadline=None, observation_seconds=None):
        limits = ObservationLimits(observation_seconds)
        session_deadlines = limits.session_deadlines(session_stop_at)
        root = Path(root).resolve()
        root.mkdir(parents=True, exist_ok=False)
        socket_dir = Path(tempfile.mkdtemp(prefix="p16wd-", dir="/private/tmp"))
        socket_dir.chmod(0o700)
        socket_path = socket_dir / "control.sock"
        argv = [str(python or sys.executable), "-u", str(Path(__file__).with_name("watchdog.py")),
                "--root", str(root), "--owner-pid", str(os.getpid()),
                "--session-stop-at", str(float(session_stop_at)), "--socket-path", str(socket_path),
                "--observation-seconds", str(limits.observation_seconds)]
        # Logs use exclusive paths. Environment is inherited privately; no
        # environment values or authentication cookie bytes are recorded here.
        with (root / "watchdog.stdout").open("xb") as out, (root / "watchdog.stderr").open("xb") as err:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                    start_new_session=True, close_fds=True)
        (root / "launcher.json").write_text(json.dumps({"argv": argv, "pid": proc.pid,
            "pgid": proc.pid, "owner_pid": os.getpid(), "started_monotonic": time.monotonic(),
            "session_stop_at": session_stop_at, "control_socket": str(socket_path),
            "configuration": limits.configuration(), "session_deadlines": session_deadlines,
            "private_socket_directory": str(socket_dir)}, indent=2)+"\n")
        client = cls(root, proc, socket_path)
        def startup_cleanup():
            # No runtime spawn was sent. After reaping our exact watchdog child,
            # remove only the endpoint in the private directory we created.
            proc.wait(timeout=1)
            socket_path.unlink(missing_ok=True)
            if socket_dir.exists():
                socket_dir.rmdir()
            (root / "startup-failure.json").write_text(json.dumps({
                "watchdog_pid": proc.pid, "exit_code": proc.returncode,
                "watchdog_reaped": True, "runtime_launch_sent": False,
                "control_endpoint_remaining": socket_path.exists(),
                "control_directory_remaining": socket_dir.exists()}, indent=2)+"\n")
        deadline = min(ready_deadline or time.monotonic()+3, session_stop_at-5)
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                startup_cleanup()
                raise RuntimeError("watchdog exited during startup; inspect " + str(root))
            if socket_path.exists():
                try:
                    client.snapshot(deadline)
                    return client
                except BaseException:
                    # No runtime launch request has been sent. This exact
                    # direct watchdog child is the only possible owned process.
                    proc.terminate()
                    try:
                        proc.wait(timeout=1)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=1)
                    startup_cleanup()
                    raise
            time.sleep(min(0.02, max(0, deadline-time.monotonic())))
        # Startup may have failed before opening its endpoint. No runtime launch
        # has been sent, so killing/reaping this exact child is safe.
        proc.terminate()
        try:
            proc.wait(timeout=1)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=1)
        startup_cleanup()
        raise TimeoutError("watchdog endpoint not ready within absolute startup deadline")

    def request(self, request, deadline):
        try:
            return self._request(request, deadline)
        except (EOFError, OSError, TimeoutError) as exc:
            # A clean stop may close its endpoint before a queued response is
            # flushed. Snapshot may race a natural guest exit similarly. Only
            # authoritative closed state plus the actual watchdog wait/reap can
            # recover those two read/stop operations. Never recover spawn: its
            # missing reply leaves an uncertain launch that must be preserved.
            if request.get("op") not in ("stop", "snapshot"):
                raise
            try:
                state = self.read_state()
            except (OSError, ValueError):
                raise exc
            if not state.get("closed") or state.get("phase") != "closed":
                raise
            result = self.wait_closed(deadline)
            record = {"op": request["op"], "monotonic": time.monotonic(),
                      "transport_error": type(exc).__name__ + ": " + str(exc),
                      "authoritative_closed_state": True,
                      "watchdog_exit_code": result["watchdog_exit_code"],
                      "watchdog_reaped": result["watchdog_reaped"]}
            with (self.root / "closed-response-recoveries.jsonl").open("a") as log:
                log.write(json.dumps(record)+"\n")
            return result

    def _request(self, request, deadline):
        if time.monotonic() >= deadline:
            raise TimeoutError("control request deadline already reached")
        payload = (json.dumps(request)+"\n").encode()
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.setblocking(False)
        try:
            try:
                conn.connect(str(self.socket_path))
            except BlockingIOError:
                pass
            sent = 0
            received = bytearray()
            while time.monotonic() < deadline:
                timeout = max(0, min(0.05, deadline-time.monotonic()))
                readable, writable, _ = select.select([conn], [conn] if sent < len(payload) else [], [], timeout)
                if writable:
                    count = conn.send(payload[sent:])
                    sent += count
                if readable:
                    chunk = conn.recv(65536)
                    if not chunk:
                        raise EOFError("watchdog control endpoint closed before reply")
                    received.extend(chunk)
                    if len(received) > 4194304:
                        raise RuntimeError("watchdog response too large")
                    if b"\n" in received:
                        result = json.loads(bytes(received).split(b"\n", 1)[0])
                        if not result["ok"]:
                            raise RuntimeError(result["error"])
                        return result["result"]
            raise TimeoutError("absolute control request deadline")
        finally:
            conn.close()

    def spawn(self, role, argv, cwd, stdout, stderr, deadline, env=None, attempt=False):
        return self.request({"op": "spawn", "role": role, "argv": list(map(str, argv)),
                             "cwd": str(cwd), "stdout": str(stdout), "stderr": str(stderr),
                             "env": env, "attempt": attempt}, deadline)

    def set_deadlines(self, term_at, kill_at, reap_at, deadline):
        return self.request(dict(op="deadlines", term_at=term_at, kill_at=kill_at, reap_at=reap_at), deadline)

    def snapshot(self, deadline):
        return self.request({"op": "snapshot"}, deadline)

    def stop(self, reason, deadline, failure=False):
        return self.request({"op": "stop", "reason": reason, "failure": failure}, deadline)

    def read_state(self):
        return json.loads((self.root / "state.json").read_text())

    def wait_closed(self, deadline):
        # Always inspect/reap an already exited child once, even if the absolute
        # deadline just elapsed while its final control response was closing.
        while True:
            code = self.proc.poll()
            if code is not None:
                state = self.read_state()
                state["watchdog_exit_code"] = code
                state["watchdog_reaped"] = True
                state["control_endpoint_remaining"] = self.socket_path.exists()
                state["control_directory_remaining"] = self.socket_path.parent.exists()
                (self.root / "client-closure.json").write_text(json.dumps(state, indent=2)+"\n")
                if not state.get("closed"):
                    raise RuntimeError("watchdog ended without confirmed closure")
                return state
            if time.monotonic() >= deadline:
                break
            time.sleep(min(0.025, max(0, deadline-time.monotonic())))
        raise TimeoutError("watchdog/owned-process closure unconfirmed by absolute wait deadline; essential cleanup still required")
