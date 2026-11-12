"""Independent, read-only ownership postflight. No signals or runtime imports.

Checks the full table against an independently requested PID table. Numeric
PIDs/PGIDs alone never establish ownership; ps lstart has second resolution.
An unobservable identity/group is uncertainty, never a clean verdict.
"""
from __future__ import annotations

import argparse
import datetime
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time

PS = '/bin/ps'
FIELDS = 'pid=,ppid=,pgid=,lstart=,stat='
DISPLAY_PATHS = ('/private/tmp/.X11-unix/X16', '/private/tmp/.X16-lock', '/private/tmp/p16008x')


def parse_table(output):
    rows = {}
    for line in output.splitlines():
        fields = line.split()
        if len(fields) != 9:
            raise ValueError('Incomplete/malformed process row: ' + line[:120])
        pid, ppid, pgid = map(int, fields[:3])
        if pid <= 0 or ppid < 0 or pgid < 0 or pid in rows:
            raise ValueError('Invalid/duplicate process identity')
        start = ' '.join(fields[3:8])
        datetime.datetime.strptime(start, '%a %b %d %H:%M:%S %Y')
        rows[pid] = dict(pid=pid, ppid=ppid, pgid=pgid, start=start, stat=fields[8])
    return rows


def owned_records(attempt, launcher, events):
    """Read recorded ownership, without believing saved absence/reaped flags."""
    closure = attempt.get('closure') or {}
    records, errors = [], []
    seen = set()

    def add(role, row, start_key='start', dedicated=False):
        try:
            pid = int(row['pid'])
            pgid = int(row.get('pgid', pid if dedicated else 0))
            if pid <= 0 or pgid < 0:
                raise ValueError('invalid PID/PGID')
            start = row.get(start_key)
            if start:
                start = ' '.join(start.split())
                datetime.datetime.strptime(start, '%a %b %d %H:%M:%S %Y')
            key = (role, pid, start, pgid)
            if key not in seen:
                records.append(dict(role=role, pid=pid, pgid=pgid, start=start,
                                    dedicated_group=dedicated))
                seen.add(key)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append('Invalid recorded ' + role + ': ' + str(exc))

    if not closure:
        errors.append('Final owned closure is missing')
    for role in ('owner', 'watchdog'):
        pid = closure.get(role + '_pid', launcher.get('owner_pid' if role == 'owner' else 'pid'))
        launched_pid = launcher.get('owner_pid' if role == 'owner' else 'pid')
        if pid != launched_pid:
            errors.append('Launcher/final ' + role + ' identity disagrees')
        identity = closure.get(role + '_identity') or {}
        if identity and identity.get('pid') != pid:
            errors.append('Saved ' + role + ' identity PID disagrees')
        add(role, dict(identity, pid=pid), dedicated=role == 'watchdog')
    groups = closure.get('groups')
    descendants = closure.get('tracked_descendants')
    if not isinstance(groups, list) or not isinstance(descendants, list):
        errors.append('Final group/descendant inventory is missing')
    for group in groups or []:
        add(group.get('role', 'unnamed-group'), group, 'start_identity', True)
    for row in descendants or []:
        add('tracked:' + row.get('role', 'unnamed'), row)
    # Include every recorded transient census helper, even one reported reaped.
    # Historical events without lstart remain explicitly unresolved if present.
    completed_helpers = {(e.get('pid'), e.get('started_monotonic')): e for e in events
                         if e.get('event') == 'process_table_helper'}
    for event in events:
        if event.get('event') in ('process_table_helper_started', 'process_table_helper', 'process_table_helper_unreaped'):
            completed = completed_helpers.get((event.get('pid'), event.get('started_monotonic')), event)
            identity = completed.get('identity') or {}
            if identity and identity.get('pid') != event['pid']:
                errors.append('Census-helper event/saved identity PID disagrees')
            add('census-helper', dict(identity, pid=event['pid'], pgid=event.get('pgid', event['pid'])), dedicated=True)
    if not events:
        errors.append('Watchdog event inventory is missing/empty')
    expected = [('display', attempt.get('display')), ('display-observer', attempt.get('display_observer')),
                ('guest', attempt.get('guest')), ('drawable-input', attempt.get('drawable_input'))]
    recorded_roles = {(r['role'], r['pid']) for r in records}
    for role, row in expected:
        if row and (role, row.get('pid')) not in recorded_roles:
            errors.append('Launched role absent from final inventory: ' + role)
    return records, errors


def assess_processes(records, full, targeted):
    matches, recycled, unresolved, groups, descendants = [], [], [], [], []
    # Independent views must agree for every recorded PID. A race is uncertainty.
    for pid in {r['pid'] for r in records}:
        if identity_key(full.get(pid)) != identity_key(targeted.get(pid)):
            unresolved.append(dict(pid=pid, reason='Full and targeted process views disagree'))
    anchors = {}
    for record in records:
        current = full.get(record['pid']) or targeted.get(record['pid'])
        if current is None:
            continue
        if not record['start']:
            unresolved.append(dict(record=record, current=current, reason='Recorded start identity unavailable'))
        elif current['start'] == record['start']:
            matches.append(dict(record=record, current=current))
            anchors[current['pid']] = current
        else:
            recycled.append(dict(record=record, current=current))
    for record in records:
        if not record['dedicated_group'] or not record['pgid']:
            continue
        members = [r for r in full.values() if r['pgid'] == record['pgid']]
        if not members:
            continue
        leader = full.get(record['pgid'])
        if leader and record['pid'] == record['pgid'] and record['start'] and leader['start'] != record['start']:
            # A new leader in the same numeric group proves the old group was recycled.
            continue
        if any(r['pid'] in anchors for r in members):
            groups.append(dict(role=record['role'], pgid=record['pgid'], members=members))
            anchors.update({r['pid']: r for r in members})
        else:
            unresolved.append(dict(role=record['role'], pgid=record['pgid'], members=members,
                                   reason='Numeric group exists without a matching recorded identity'))
    # Catch descendants created after the last saved tracking sample. A recycled
    # parent is never an anchor. Session-changing tracked children match by PID/start.
    while True:
        added = [r for r in full.values() if r['pid'] not in anchors and r['ppid'] in anchors]
        if not added:
            break
        descendants.extend(added)
        anchors.update({r['pid']: r for r in added})
    return dict(identity_matches=matches, recycled_pids=recycled, unresolved=unresolved,
                owned_group_members=groups, current_descendants=descendants,
                passed=not (matches or unresolved or groups or descendants))


def identity_key(row):
    # State/parent may change between reads; they do not identify PID reuse.
    return (row['pid'], row['start'], row['pgid']) if row else None


def path_census(paths):
    results = {}
    for value in paths:
        try:
            s = os.lstat(value)
            results[value] = dict(exists=True, uid=s.st_uid, gid=s.st_gid,
                                  mode=oct(stat.S_IMODE(s.st_mode)), type=stat.S_IFMT(s.st_mode),
                                  is_symlink=stat.S_ISLNK(s.st_mode))
        except FileNotFoundError:
            results[value] = dict(exists=False)
        except OSError as exc:
            results[value] = dict(exists=None, error=type(exc).__name__ + ': ' + str(exc))
    return results


def collect_command(argv, output, name, deadline=None):
    record = dict(argv=argv, stdout=name + '.stdout.txt', stderr=name + '.stderr.txt')
    env = dict(os.environ, LC_ALL='C', LANG='C')
    try:
        timeout = 10 if deadline is None else min(10, deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError('Session deadline reached before census command')
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        record['pid'] = proc.pid
        try:
            out, err = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()  # Our exact unreaped read-only census child only.
            out, err = proc.communicate(timeout=2)
            record['error'] = 'Census timeout; exact census child killed/reaped'
        record.update(exit=proc.returncode, reaped=proc.returncode is not None)
    except (OSError, subprocess.SubprocessError) as exc:
        out, err = '', str(exc)
        record.update(error=type(exc).__name__, exit=None, reaped=False)
    (output / record['stdout']).write_text(out)
    (output / record['stderr']).write_text(err)
    return record, out, err


def run(attempt_dir, output, deadline=None):
    output.mkdir(parents=True, exist_ok=True)
    result = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  monotonic=time.monotonic(), scope='Read-only independent postflight',
                  attempt=str(attempt_dir), commands=[], errors=[], passed=False)
    try:
        clock_path = attempt_dir / 'session-clock.json'
        if deadline is None and clock_path.exists():
            deadline = float(json.loads(clock_path.read_text())['process_stop_monotonic'])
        if deadline is not None and not math.isfinite(deadline):
            raise ValueError('Nonfinite session deadline')
        result['session_stop_monotonic'] = deadline
        def command(argv, name):
            return collect_command(argv, output, name) if deadline is None else collect_command(argv, output, name, deadline)
        attempt = json.loads((attempt_dir / 'attempt-supervision.json').read_text())
        owned = attempt_dir / 'supervision/attempt-owned'
        launcher = json.loads((owned / 'launcher.json').read_text())
        events = [json.loads(line) for line in (owned / 'events.jsonl').read_text().splitlines()]
        records, errors = owned_records(attempt, launcher, events)
        result.update(records=records)
        result['errors'].extend(errors)
        paths = list(DISPLAY_PATHS)
        for key in ('control_socket', 'private_socket_directory'):
            value = launcher.get(key)
            if not value or not Path(value).is_absolute():
                result['errors'].append('Missing/invalid private endpoint: ' + key)
            else:
                paths.append(value)
        result['paths'] = path_census(['/private/tmp/.X11-unix'] + paths)
        cmd, out, err = command([PS, '-axo', FIELDS], 'processes-postflight')
        result['commands'].append(cmd)
        if cmd.get('error') or cmd['exit'] != 0 or err.strip():
            raise ValueError('Global process census unavailable or diagnostic output')
        full = parse_table(out)
        # Reject empty/truncated census missing the checker or its exact ps child.
        if os.getpid() not in full or cmd['pid'] not in full:
            raise ValueError('Global process census is incomplete: required sentinels absent')
        targeted = {}
        pids = sorted({r['pid'] for r in records})
        for n in range(0, len(pids), 100):
            batch = pids[n:n + 100]
            cmd, out, err = command([PS, '-p', ','.join(map(str, batch)), '-o', FIELDS], 'owned-pids-' + str(n // 100))
            result['commands'].append(cmd)
            if cmd.get('error') or err.strip() or cmd['exit'] not in (0, 1):
                raise ValueError('Targeted owned census unavailable or diagnostic output')
            rows = parse_table(out)
            if (cmd['exit'] == 0 and not rows) or (cmd['exit'] == 1 and rows) or not set(rows).issubset(batch):
                raise ValueError('Incomplete/inconsistent targeted owned census')
            targeted.update(rows)
        # A leader/recorded child may be gone while an untracked group member
        # survives. Query every private PGID independently of the full table.
        grouped = {}
        pgids = sorted({r['pgid'] for r in records if r['dedicated_group'] and r['pgid']})
        for n in range(0, len(pgids), 100):
            batch = pgids[n:n + 100]
            cmd, out, err = command([PS, '-g', ','.join(map(str, batch)), '-o', FIELDS], 'owned-groups-' + str(n // 100))
            result['commands'].append(cmd)
            if cmd.get('error') or err.strip() or cmd['exit'] not in (0, 1):
                raise ValueError('Targeted owned group census unavailable')
            rows = parse_table(out)
            if (cmd['exit'] == 0 and not rows) or (cmd['exit'] == 1 and rows) or any(r['pgid'] not in batch for r in rows.values()):
                raise ValueError('Incomplete/inconsistent targeted owned group census')
            grouped.update(rows)
        selected = {pid: r for pid, r in full.items() if r['pgid'] in pgids}
        if {pid: identity_key(r) for pid, r in selected.items()} != {pid: identity_key(r) for pid, r in grouped.items()}:
            raise ValueError('Full and independent owned group censuses disagree')
        result['processes'] = assess_processes(records, full, targeted)
        cmd, out, err = command(['/usr/sbin/lsof', '-nP', '-iTCP:6016', '-sTCP:LISTEN', '-Fpn'], 'tcp-postflight')
        result['commands'].append(cmd)
        if cmd.get('error') or err.strip() or cmd['exit'] not in (0, 1) or (cmd['exit'] == 0 and not out.strip()) or (cmd['exit'] == 1 and out.strip()):
            raise ValueError('TCP census unavailable/inconsistent')
        result['tcp'] = out
        shared = result['paths']['/private/tmp/.X11-unix']
        result['shared_directory_valid'] = (shared.get('exists') is True and shared.get('uid') == 0
            and shared.get('mode') == '0o1777' and shared.get('type') == stat.S_IFDIR and not shared.get('is_symlink'))
        result['private_endpoints_absent'] = all(result['paths'][p].get('exists') is False for p in paths)
        result['passed'] = bool(not result['errors'] and result['processes']['passed'] and
            result['shared_directory_valid'] and result['private_endpoints_absent'] and not out.strip())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result['errors'].append(type(exc).__name__ + ': ' + str(exc))
    result['verdict'] = 'pass' if result['passed'] else 'fail_or_unverified'
    result['limits'] = ['ps lstart identities have second resolution.',
        'Unrecorded children that changed session and lost their ancestry between saved samples are outside recorded ownership coverage.',
        'This checks presence at census time; it does not replace owned shutdown/reaping.']
    (output / 'endpoint-postflight-initial.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--stop-at', type=float, help='Absolute session monotonic ceiling; otherwise use fresh session-clock.json when present')
    args = parser.parse_args()
    result = run(args.attempt.resolve(), (args.output or args.attempt).resolve(), args.stop_at)
    print(json.dumps(dict(passed=result['passed'], verdict=result['verdict'], errors=result['errors']), indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
