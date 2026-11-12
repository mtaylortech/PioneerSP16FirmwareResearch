"""Independent owner of explicitly launched disposable process groups.

The observer is a client, never this process's event loop. Only argv supplied by
the local authenticated-by-filesystem client can be launched. Absolute monotonic
deadlines are shortened, never extended. No guest/firmware mutation occurs here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import selectors
import signal
import socket
import subprocess
import sys
import time
import traceback

try:
    from .runtime_limits import ObservationLimits, validate_deadlines
except ImportError:  # Direct watchdog subprocess entry point.
    from runtime_limits import ObservationLimits, validate_deadlines


def stamp():
    return {"monotonic": time.monotonic(), "utc": datetime.now(timezone.utc).isoformat()}



def census_helper_identity(out, pid):
    """Record the helper's row from its existing census; never add a query."""
    for line in out.decode('utf-8', 'replace').splitlines():
        fields = line.split()
        if len(fields) == 9 and fields[0] == str(pid):
            try:
                return dict(pid=int(fields[0]), ppid=int(fields[1]), pgid=int(fields[2]),
                            start=' '.join(fields[3:8]), stat=fields[8])
            except ValueError:
                return None
    return None


def periodic_table_max_wait(phase, until_boundary):
    if until_boundary <= 0:
        return 0.1
    return min(0.5 if phase == "running" else 0.2, max(0.01, until_boundary - 0.02))


class Owner:
    def __init__(self, root, owner_pid, stop_at, socket_path, observation_seconds=None):
        self.limits = ObservationLimits(observation_seconds)
        self.session_deadlines = self.limits.session_deadlines(stop_at)
        self.root = Path(root).resolve()
        self.owner_pid = owner_pid
        self.socket_path = Path(socket_path)
        self.deadlines = dict(self.session_deadlines)
        self.groups = []
        self.known = {}
        self.phase = "running"
        self.stop_reason = None
        self.failure = False
        self.ps_calls = 0
        self.latest_table = {}
        self.table_at = 0.0
        self.owner_start = None
        self.pending_table = None
        self.census_unavailable_since = None
        self.census_failures = 0
        self.attempt_launched = False
        self.events = (self.root / "events.jsonl").open("x", buffering=1)
        self.emit("watchdog_started", pid=os.getpid(), owner_pid=owner_pid,
                  argv=sys.argv, deadlines=self.deadlines, executable=sys.executable,
                  configuration=self.limits.configuration(), session_deadlines=self.session_deadlines)
        self.emit("containment_limits", details=[
            "This watchdog reaps only direct children. macOS provides no Linux child-subreaper adoption here.",
            "Orphan descendants are verified absent/zombie in process-table observations; their final reaping belongs to init.",
            "A descendant that changes session and becomes orphaned between process-table samples may escape census.",
            "Ownership uses direct Popen handles, unique new process groups, continuous group existence, and ps lstart identity (second resolution).",
            "No exhaustive native-containment or all-descendant-reaping claim is made."])

    def emit(self, event, **fields):
        self.events.write(json.dumps(dict(stamp(), event=event, **fields), sort_keys=True) + "\n")

    def save(self, closed=False):
        value = dict(stamp(), watchdog_pid=os.getpid(), owner_pid=self.owner_pid,
                     owner_identity=self.latest_table.get(self.owner_pid),
                     watchdog_identity=self.latest_table.get(os.getpid()),
                     phase=self.phase, stopping_condition=self.stop_reason,
                     failure=self.failure, deadlines=self.deadlines,
                     configuration=self.limits.configuration(), session_deadlines=self.session_deadlines,
                     attempt_launched=self.attempt_launched, ps_calls=self.ps_calls,
                     groups=[{k: v for k, v in g.items() if k not in ("proc", "files")} for g in self.groups],
                     tracked_descendants=list(self.known.values()), closed=closed,
                     all_direct_children_reaped=all(g["proc"].returncode is not None for g in self.groups),
                     closure_kind="direct leaders reaped; tracked descendant exit/absence verified; init owns orphan reaping")
        temp = self.root / "state.tmp"
        temp.write_text(json.dumps(value, indent=2) + "\n")
        os.replace(temp, self.root / "state.json")
        return value

    def table(self, max_wait=0.2):
        # The helper is a direct child in its own group, with a bounded wait. No
        # command lines or environment (in particular auth cookies) are read.
        argv = ["/bin/ps", "-axo", "pid=,ppid=,pgid=,lstart=,stat="]
        start = time.monotonic()
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                start_new_session=True)
        self.ps_calls += 1
        self.emit("process_table_helper_started", pid=proc.pid, pgid=proc.pid,
                  started_monotonic=start)
        timed_out = False
        try:
            out, err = proc.communicate(timeout=max(0.001, max_wait))
        except subprocess.TimeoutExpired:
            timed_out = True
            # This exact helper has no children and is still an unreaped child;
            # its PID cannot be reused while we retain the Popen child handle.
            proc.kill()
            try:
                out, err = proc.communicate(timeout=0.2)
            except subprocess.TimeoutExpired:
                self.emit("process_table_helper_unreaped", argv=argv, pid=proc.pid)
                raise RuntimeError("process-table helper failed to reap after SIGKILL")
        self.emit("process_table_helper", argv=argv, pid=proc.pid, pgid=proc.pid,
                  identity=census_helper_identity(out, proc.pid),
                  direct_child_reaped=proc.returncode is not None,
                  exit_code=proc.returncode, timed_out=timed_out,
                  started_monotonic=start, finished_monotonic=time.monotonic(),
                  stderr=err.decode("utf-8", "replace")[:1000])
        if timed_out or proc.returncode:
            raise RuntimeError("bounded process-table query failed")
        return self.accept_table(out)

    def accept_table(self, out):
        rows = {}
        for line in out.decode("utf-8", "replace").splitlines():
            fields = line.split()
            if len(fields) < 9:
                raise RuntimeError("unexpected ps row: " + line[:100])
            pid, ppid, pgid = map(int, fields[:3])
            rows[pid] = {"pid": pid, "ppid": ppid, "pgid": pgid,
                         "start": " ".join(fields[3:8]), "stat": fields[8]}
        self.latest_table = rows
        self.table_at = time.monotonic()
        return rows

    def periodic_table(self, max_wait):
        """Poll one exact helper without blocking shutdown deadlines or controls."""
        now = time.monotonic()
        if self.pending_table is None:
            argv = ["/bin/ps", "-axo", "pid=,ppid=,pgid=,lstart=,stat="]
            proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    start_new_session=True)
            self.ps_calls += 1
            self.emit("process_table_helper_started", pid=proc.pid, pgid=proc.pid,
                      started_monotonic=now)
            self.pending_table = dict(proc=proc, argv=argv, started=now,
                                      expires=now + max_wait, timed_out=False)
        query = self.pending_table
        proc = query['proc']
        if now >= query['expires'] and not query['timed_out'] and proc.poll() is None:
            proc.kill()  # Exact unreaped helper, never a stale process-table PID.
            query['timed_out'] = True
            query['reap_by'] = now + 0.2
        try:
            out, err = proc.communicate(timeout=0.001)
        except subprocess.TimeoutExpired:
            if query.get('timed_out') and now >= query['reap_by']:
                raise RuntimeError('process-table helper failed to reap after SIGKILL')
            return None
        self.pending_table = None
        self.emit('process_table_helper', argv=query['argv'], pid=proc.pid, pgid=proc.pid,
                  identity=census_helper_identity(out, proc.pid),
                  direct_child_reaped=proc.returncode is not None,
                  exit_code=proc.returncode, timed_out=query['timed_out'],
                  started_monotonic=query['started'], finished_monotonic=time.monotonic(),
                  stderr=err.decode('utf-8', 'replace')[:1000], asynchronous=True)
        if query['timed_out'] or proc.returncode:
            self.census_unavailable_since = self.census_unavailable_since or now
            self.census_failures += 1
            self.emit('census_temporarily_unavailable', failures=self.census_failures,
                      unavailable_since=self.census_unavailable_since, stale_snapshot_not_used=True)
            if self.census_failures >= 3 or now - self.census_unavailable_since >= 2:
                self.request_stop('persistent bounded census unavailability', failure=True)
            return None
        table = self.accept_table(out)
        if self.census_unavailable_since is not None:
            self.emit('census_recovered', failures=self.census_failures,
                      unavailable_seconds=now-self.census_unavailable_since)
        self.census_unavailable_since = None
        self.census_failures = 0
        return table

    def deadline_signal(self, sig):
        # No process-table wait is allowed ahead of an absolute boundary send.
        if getattr(self, 'census_unavailable_since', None) is not None or time.monotonic()-self.table_at > 0.6:
            self.fallback_direct_signals(sig)
        else:
            self.signal_all(sig)

    def census(self, table):
        # Track lineage beyond a group's leader. Session-changing children are
        # signaled individually only when their exact observed identity matches.
        changed = True
        while changed:
            changed = False
            for pid, row in table.items():
                source = next((g for g in self.groups if row["pgid"] == g["pgid"] and not g["closed"]), None)
                parent = self.known.get(row["ppid"])
                if source is None and parent and parent["start"] == table.get(row["ppid"], {}).get("start"):
                    source = next(g for g in self.groups if g["role"] == parent["role"])
                if source and pid not in self.known:
                    self.known[pid] = dict(row, role=source["role"], first_seen=time.monotonic(),
                                           last_seen=time.monotonic(), leader=pid == source["pid"],
                                           vanished=False, signal_history=[])
                    self.emit("owned_process_observed", process=self.known[pid])
                    changed = True
        for pid, known in list(self.known.items()):
            row = table.get(pid)
            if row and row["start"] == known["start"]:
                known.update(last_seen=time.monotonic(), ppid=row["ppid"], pgid=row["pgid"], stat=row["stat"])
            elif not known["vanished"]:
                known["vanished"] = True
                self.emit("owned_process_absent", pid=pid, role=known["role"], previous_identity=known["start"])
        for g in self.groups:
            g["proc"].poll()  # waitpid(WNOHANG) reaps the direct leader.
            if g["exit_code"] is None and g["proc"].returncode is not None:
                g["exit_code"] = g["proc"].returncode
                g["reaped_at"] = time.monotonic()
                self.emit("direct_child_reaped", role=g["role"], pid=g["pid"], exit_code=g["exit_code"])
            members = [r for r in table.values() if r["pgid"] == g["pgid"]]
            g["last_members"] = members
            live = [r for r in members if not r["stat"].startswith("Z")]
            if not members and g["proc"].returncode is not None:
                if not g["closed"]:
                    g["closed"] = True
                    g["closed_at"] = time.monotonic()
                    self.emit("owned_group_absent", role=g["role"], pgid=g["pgid"])
            g["live_members"] = live

    def ownership(self, g, table):
        members = [r for r in table.values() if r["pgid"] == g["pgid"]]
        if g["closed"]:
            if members:
                return False, "closed group identifier reappeared; refusing signal"
            return True, "already absent"
        leader = table.get(g["pid"])
        if leader and (leader["pgid"] != g["pgid"] or leader["start"] != g["start_identity"]):
            return False, "leader identity or group mismatch"
        # start_new_session gave a fresh session/PGID. Its identifier remains
        # owned while any group member exists; unrelated sessions cannot join.
        for row in members:
            known = self.known.get(row["pid"])
            if not known or known["start"] != row["start"] or known["role"] != g["role"]:
                return False, "unregistered group member identity"
        return True, "direct launch in new session; observed member identities match"

    def permission_recheck(self, g, exc, known=None):
        """A denied send is benign only after fresh evidence of owned exit."""
        evidence = {"error": repr(exc), "fresh_recheck": True}
        try:
            table = self.table(max_wait=0.1)
            self.census(table)
            if known is None:
                ok, reason = self.ownership(g, table)
                live = [r for r in table.values() if r["pgid"] == g["pgid"] and not r["stat"].startswith("Z")]
                exited = ok and not live
                evidence.update(ownership_ok=ok, ownership_reason=reason, fresh_live_members=live)
            else:
                row = table.get(known["pid"])
                exited = not row or row["start"] != known["start"] or row["stat"].startswith("Z")
                evidence["fresh_identity"] = row
            evidence["result"] = "permission_denied_after_owned_exit" if exited else "permission_denied_owned_live"
            if not exited:
                self.failure = True
        except Exception as recheck_exc:
            self.failure = True
            evidence.update(result="permission_denied_recheck_failed", recheck_error=repr(recheck_exc))
        return evidence

    def signal_all(self, sig):
        # One snapshot, one ownership pass, then all sends; no per-role waits.
        table = self.latest_table
        batch = []
        if time.monotonic() - self.table_at > 0.6:
            table = self.table()
            self.census(table)
        for g in self.groups:
            ok, reason = self.ownership(g, table)
            item = dict(role=g["role"], pgid=g["pgid"], signal=signal.Signals(sig).name,
                        ownership_ok=ok, ownership_reason=reason, members=g["last_members"])
            if not ok:
                self.failure = True
                item["result"] = "refused"
            elif g["live_members"]:
                try:
                    os.killpg(g["pgid"], sig)
                    item["result"] = "sent"
                except ProcessLookupError:
                    item["result"] = "absent_at_send"
                except PermissionError as exc:
                    item.update(self.permission_recheck(g, exc))
                    table = self.latest_table
                item["sent_monotonic"] = time.monotonic()
                g["signals"].append(item.copy())
            else:
                item["result"] = "no_live_member"
            batch.append(item)
        escaped = []
        for pid, known in list(self.known.items()):
            if known["leader"] or known["vanished"] or known["stat"].startswith("Z"):
                continue
            original = next(g for g in self.groups if g["role"] == known["role"])
            if known["pgid"] == original["pgid"]:
                continue
            row = table.get(pid)
            if row and row["start"] == known["start"]:
                details = {}
                try:
                    os.kill(pid, sig)
                    result = "sent"
                except ProcessLookupError:
                    result = "absent_at_send"
                except PermissionError as exc:
                    details = self.permission_recheck(original, exc, known=known)
                    result = details["result"]
                    table = self.latest_table
                evidence = dict(pid=pid, signal=signal.Signals(sig).name, result=result,
                                identity=row, sent_monotonic=time.monotonic())
                evidence.update(details)
                escaped.append(evidence)
                known["signal_history"].append(evidence)
        self.emit("signal_batch", signal=signal.Signals(sig).name, groups=batch, tracked_escaped=escaped,
                  snapshot_monotonic=self.table_at)

    def request_stop(self, reason, failure=False):
        self.stop_reason = self.stop_reason or reason
        self.failure = self.failure or failure
        now = time.monotonic()
        self.deadlines = {"term_at": min(self.deadlines["term_at"], now),
                          "kill_at": min(self.deadlines["kill_at"], now + 3),
                          "reap_at": min(self.deadlines["reap_at"], now + 5)}
        self.emit("early_stop_requested", reason=reason, failure=failure, deadlines=self.deadlines)

    def fallback_direct_signals(self, sig):
        """No ps dependency: signal only a still-unreaped exact direct child group."""
        evidence = []
        for g in self.groups:
            proc = g["proc"]
            if proc.poll() is not None:
                g["exit_code"] = proc.returncode
                continue
            try:
                actual = os.getpgid(proc.pid)
                if actual != g["pgid"]:
                    evidence.append(dict(role=g["role"], pid=proc.pid, result="refused_group_mismatch", actual_pgid=actual))
                    continue
                os.killpg(actual, sig)
                evidence.append(dict(role=g["role"], pid=proc.pid, pgid=actual, result="sent",
                    ownership="exact unreaped direct Popen child; observed current dedicated PGID"))
            except ProcessLookupError:
                evidence.append(dict(role=g["role"], pid=proc.pid, result="already_exited"))
            except PermissionError as exc:
                details = self.permission_recheck(g, exc)
                evidence.append(dict(role=g["role"], pid=proc.pid, pgid=g["pgid"], **details))
        self.emit("fallback_direct_signal_batch", signal=signal.Signals(sig).name, groups=evidence)

    def tighten(self, values):
        proposed = validate_deadlines(values)
        new = validate_deadlines({k: min(self.deadlines[k], proposed[k], self.session_deadlines[k]) for k in proposed})
        self.deadlines = new
        self.emit("deadlines_tightened", deadlines=new)

    def spawn(self, request):
        if self.phase != "running" or time.monotonic() >= self.deadlines["term_at"]:
            raise RuntimeError("launch after stop rejected")
        role = request["role"]
        if not isinstance(role, str) or not role or any(g["role"] == role for g in self.groups):
            raise ValueError("unique nonempty role required")
        if request.get("attempt") and self.attempt_launched:
            raise RuntimeError("second guest attempt rejected")
        # Validate again at the actual launch boundary, before output files or
        # Popen. The independent session ceiling can only shorten these limits.
        limits = ObservationLimits(self.limits.observation_seconds)
        validate_deadlines(self.session_deadlines)
        validate_deadlines(self.deadlines)
        argv = request["argv"]
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise ValueError("argv must be a nonempty string list")
        # Paths and env come from the owner. Never record env values: callers
        # separately preserve their approved nonsecret effective configuration.
        files = []
        for name in ("stdout", "stderr"):
            path = Path(request[name]).resolve()
            if self.root.parent not in path.parents:
                raise ValueError("process output must stay in new experiment root")
            files.append(path.open("xb"))
        started = time.monotonic()
        self.emit("launch_requested", role=role, argv=argv, cwd=request.get("cwd"),
                  attempt=bool(request.get("attempt")), started_monotonic=started)
        if request.get("attempt"):
            self.attempt_launched = True
            self.tighten(limits.deadlines(started))
        proc = subprocess.Popen(argv, cwd=request.get("cwd"), env=request.get("env"),
                                stdin=subprocess.DEVNULL, stdout=files[0], stderr=files[1],
                                start_new_session=True, close_fds=True)
        g = dict(role=role, argv=argv, cwd=request.get("cwd"), pid=proc.pid, pgid=proc.pid,
                 started_monotonic=started, created_utc=datetime.now(timezone.utc).isoformat(),
                 proc=proc, files=files, signals=[], exit_code=None, reaped_at=None,
                 closed=False, start_identity=None, last_members=[], live_members=[],
                 stdout=request["stdout"], stderr=request["stderr"], attempt=bool(request.get("attempt")))
        self.groups.append(g)
        self.emit("process_launched", **{k: v for k, v in g.items() if k not in ("proc", "files")})
        table = self.table()
        leader = table.get(proc.pid)
        if leader:
            if leader["ppid"] != os.getpid() or leader["pgid"] != proc.pid:
                raise RuntimeError("direct launched child ownership contradiction")
            g["start_identity"] = leader["start"]
        self.census(table)
        if g["start_identity"] is None and g["live_members"]:
            # A leader can exit before ps. Group allocation still comes from
            # our Popen. Preserve this limitation instead of inventing a leader
            # identity; descendant membership is separately recorded.
            self.emit("leader_exited_before_identity_snapshot", role=role, pid=proc.pid)
        self.save()
        return {"pid": proc.pid, "pgid": proc.pid, "started_monotonic": started,
                "deadlines": self.deadlines, "role": role,
                "observation_seconds": limits.observation_seconds,
                "session_deadlines": self.session_deadlines}

    def handle(self, request):
        op = request["op"]
        if op == "spawn":
            return self.spawn(request)
        if op == "deadlines":
            self.tighten(request)
            return self.deadlines
        if op == "snapshot":
            return self.save()
        if op == "stop":
            self.request_stop(request.get("reason", "owner requested stop"), request.get("failure", False))
            return self.save()
        raise ValueError("unknown operation")

    def closure(self):
        direct_reaped = all(g["proc"].returncode is not None for g in self.groups)
        live_tracked = [v for v in self.known.values() if not v["vanished"] and not v["stat"].startswith("Z")]
        live_groups = [g for g in self.groups if g["live_members"]]
        return direct_reaped and not live_tracked and not live_groups

    def run(self):
        address = self.socket_path
        if address.exists():
            raise RuntimeError("control endpoint occupied")
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        listener.bind(str(address))
        address.chmod(0o600)
        listener.listen(8)
        listener.setblocking(False)
        selector = selectors.DefaultSelector()
        selector.register(listener, selectors.EVENT_READ)
        connections = {}
        next_scan = 0.0
        overrun_reported = False
        try:
            while True:
                now = time.monotonic()
                for g in self.groups: g["proc"].poll()
                if self.phase == "running":
                    ended = next((g for g in self.groups if g["attempt"] and g["proc"].returncode is not None), None)
                    if ended:
                        self.request_stop("guest leader exited", failure=False)
                # Boundary signals precede new process-table queries. Recent
                # cached identities were refreshed before the 0.25s margin.
                if self.phase == "running" and now >= self.deadlines["term_at"]:
                    self.stop_reason = self.stop_reason or "absolute monotonic observation deadline"
                    self.phase = "term"
                    self.emit("deadline_reached", phase="term", due=self.deadlines["term_at"], delay=now-self.deadlines["term_at"])
                    self.deadline_signal(signal.SIGTERM)
                if self.phase == "term" and now >= self.deadlines["kill_at"]:
                    self.phase = "kill"
                    self.emit("deadline_reached", phase="kill", due=self.deadlines["kill_at"], delay=now-self.deadlines["kill_at"])
                    self.deadline_signal(signal.SIGKILL)
                # Refresh before phase boundaries. Table queries are bounded,
                # and client reads/writes are always nonblocking.
                boundary = self.deadlines["term_at"] if self.phase == "running" else self.deadlines["kill_at"] if self.phase == "term" else self.deadlines["reap_at"]
                until_boundary = boundary - now
                if self.pending_table is not None or (now >= next_scan and (until_boundary > 0.25 or until_boundary <= 0)):
                    table = self.periodic_table(max_wait=periodic_table_max_wait(self.phase, until_boundary))
                    if table is not None:
                        self.census(table)
                        next_scan = time.monotonic() + 0.1
                        owner = table.get(self.owner_pid)
                        if self.owner_start is None and owner:
                            self.owner_start = owner["start"]
                        if not owner or owner["stat"].startswith("Z") or owner["start"] != self.owner_start:
                            if self.phase == "running":
                                self.request_stop("owner process exited or identity changed", failure=True)
                now = time.monotonic()
                if self.phase != "running" and self.census_unavailable_since is None and self.pending_table is None and self.closure():
                    self.phase = "closed"
                    self.emit("closure_verified", reaping="all direct leaders reaped; recorded descendants absent or zombies",
                              within_deadline=time.monotonic() <= self.deadlines["reap_at"],
                              elapsed_over_reap=max(0.0, time.monotonic()-self.deadlines["reap_at"]))
                    self.save(closed=True)
                    break
                if now >= self.deadlines["reap_at"] and not overrun_reported:
                    overrun_reported = True
                    self.failure = True
                    self.emit("closure_deadline_failed", due=self.deadlines["reap_at"], actual=now,
                              reason="owned process closure not confirmed; essential cleanup continues")
                if overrun_reported and now >= next_scan:
                    self.deadline_signal(signal.SIGKILL)
                self.save()
                events = selector.select(timeout=0.025)
                for key, mask in events:
                    if key.fileobj is listener:
                        conn, _ = listener.accept()
                        conn.setblocking(False)
                        connections[conn] = {"buffer": bytearray(), "output": None, "expires": time.monotonic()+1}
                        selector.register(conn, selectors.EVENT_READ)
                    else:
                        conn = key.fileobj
                        state = connections[conn]
                        try:
                            if mask & selectors.EVENT_READ:
                                chunk = conn.recv(65536)
                                if not chunk:
                                    raise EOFError()
                                state["buffer"].extend(chunk)
                                if len(state["buffer"]) > 1048576:
                                    raise ValueError("control request too large")
                                if b"\n" in state["buffer"]:
                                    request = {}
                                    try:
                                        request = json.loads(bytes(state["buffer"]).split(b"\n", 1)[0])
                                        result = {"ok": True, "result": self.handle(request)}
                                    except Exception as exc:
                                        result = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}
                                        self.emit("control_request_error", error=result["error"])
                                        if request.get("op") == "spawn":
                                            self.request_stop("launch/control exception", failure=True)
                                    state["output"] = bytearray((json.dumps(result)+"\n").encode())
                                    selector.modify(conn, selectors.EVENT_WRITE)
                            if mask & selectors.EVENT_WRITE:
                                count = conn.send(state["output"])
                                del state["output"][:count]
                                if not state["output"]:
                                    raise EOFError()
                        except (EOFError, OSError, ValueError):
                            selector.unregister(conn)
                            conn.close()
                            del connections[conn]
                for conn, state in list(connections.items()):
                    if time.monotonic() >= state["expires"]:
                        selector.unregister(conn)
                        conn.close()
                        del connections[conn]
        except BaseException as exc:
            self.failure = True
            self.emit("watchdog_exception", error=repr(exc), traceback=traceback.format_exc())
            if self.pending_table is not None:
                helper = self.pending_table['proc']
                if helper.poll() is None: helper.kill()
                helper.communicate(timeout=0.2)
                self.emit('pending_census_helper_reaped_on_exception', pid=helper.pid, exit_code=helper.returncode)
                self.pending_table = None
            self.request_stop("watchdog exception", failure=True)
            # Cleanup continues independently even when serving controls fails.
            self.fallback_direct_signals(signal.SIGTERM)
            sent_kill = False
            while True:
                now = time.monotonic()
                if now >= self.deadlines["kill_at"]:
                    self.fallback_direct_signals(signal.SIGKILL)
                    sent_kill = True
                try:
                    self.census(self.table(max_wait=0.1))
                    self.signal_all(signal.SIGKILL if sent_kill else signal.SIGTERM)
                    if self.closure():
                        self.phase = "closed"
                        self.emit("closure_verified_after_exception", within_deadline=time.monotonic() <= self.deadlines["reap_at"])
                        self.save(closed=True)
                        break
                except BaseException as cleanup_exc:
                    # A second failed ps does not abandon exact direct children.
                    # Keep safe fallback signaling and retry the identity census.
                    self.emit("essential_cleanup_retry", error=repr(cleanup_exc))
                    self.phase = "cleanup_retry"
                    self.save()
                if now >= self.deadlines["reap_at"] and not overrun_reported:
                    overrun_reported = True
                    self.emit("closure_deadline_failed", reason="exception cleanup/census overran deadline; essential cleanup continues")
                time.sleep(0.05)
        finally:
            for conn in connections:
                conn.close()
            selector.close()
            listener.close()
            # Only our own bound endpoint is removed. No display/shared files.
            if address.exists():
                address.unlink()
            address.parent.rmdir()
            for g in self.groups:
                for f in g["files"]:
                    f.close()
            self.events.close()
        return 2 if self.failure else 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--owner-pid", required=True, type=int)
    parser.add_argument("--session-stop-at", required=True, type=float)
    parser.add_argument("--socket-path", required=True)
    parser.add_argument("--observation-seconds", type=int, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.session_stop_at) or args.session_stop_at <= time.monotonic()+5:
        raise SystemExit("fresh future absolute monotonic stop deadline required")
    owner = Owner(args.root, args.owner_pid, args.session_stop_at, args.socket_path, observation_seconds=args.observation_seconds)
    def interrupted(signum, frame):
        owner.request_stop("watchdog received " + signal.Signals(signum).name, failure=True)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    raise SystemExit(owner.run())


if __name__ == "__main__":
    main()
