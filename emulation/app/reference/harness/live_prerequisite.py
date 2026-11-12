"""Read-only current-run evidence binding; no process, socket, helper or input APIs.

Publication is explicit and exclusive. Future orchestration must supply fresh
human-authorized input session fields. Offline controls cannot grant permission.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import struct
import time
from display_observer import pixel_summary, window_attributes
from readiness_policy import assess
from stop_policy import decisive_event

SCOPE = 'exact original guest-created InputOutput drawable'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(run, name):
    path = run / name
    require(path.resolve().is_relative_to(run), 'Evidence escapes current run')
    require(not path.is_symlink(), 'Symlink evidence is not current-run evidence')
    return path


def read(run, name):
    path = local(run, name)
    require(path.stat().st_size <= 32 * 1024 * 1024, 'Oversized evidence')
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def fresh(value, now, age):
    return finite(value) and 0 <= now - value <= age


def matching(events, receipt):
    return next((e for e in events if all(e.get(k) == v for k, v in receipt.items())), None)


def evaluate(run, *, now=None, xid=None):
    """Assess raw current evidence, rejecting closed/stale/partial/foreign state."""
    run = Path(run).resolve()
    now = time.monotonic() if now is None else now
    require(finite(now), 'Finite monotonic time required')
    clock = read(run, 'session-clock.json')
    require(clock.get('input_authorized') is True and clock.get('authorized_guest_attempts') == 1
            and clock.get('max_conditional_tagged_interactions') == 1
            and isinstance(clock.get('authorization'), str) and clock['authorization'].strip()
            and re.fullmatch(r'[0-9a-f-]{36}', clock.get('input_session_id', '')),
            'Fresh explicit runtime/input authorization binding missing')
    require(clock.get('observation_seconds') == 600 and clock.get('total_budget_seconds') == 1200,
            'Retain 600s observation within fresh 1200s session')
    launcher = read(run, 'supervision/attempt-owned/launcher.json')
    state = read(run, 'supervision/attempt-owned/state.json')
    require(state.get('phase') == 'running' and not state.get('closed')
            and not state.get('failure') and not state.get('stopping_condition')
            and fresh(state.get('monotonic'), now, 2), 'Supervision not fresh, running and healthy')
    require(state['watchdog_pid'] == launcher['pid'] and state['owner_pid'] == launcher['owner_pid'],
            'Owner/watchdog mismatch')
    groups = {g['role']: g for g in state['groups']}
    require(all(role in groups and groups[role].get('exit_code') is None
                and not groups[role].get('closed') and groups[role].get('live_members')
                for role in ('guest', 'display', 'display-observer')), 'Owned runtime groups not live')
    guest = groups['guest']
    start = guest['started_monotonic']
    require(finite(start) and launcher['started_monotonic'] <= start <= now,
            'Guest does not belong to fresh supervision')
    require(Path(guest['stdout']).resolve() == local(run, 'supervision/guest.stdout.txt'),
            'Guest log is not current owned stdout')
    require(launcher['session_stop_at'] == clock['process_stop_monotonic']
            and 0 < launcher['session_stop_at'] - launcher['started_monotonic'] <= 1200,
            'Session containment differs')
    for name, offset in (('term_at', 605), ('kill_at', 608), ('reap_at', 610)):
        deadline = state['deadlines'][name]
        require(finite(deadline) and abs(deadline - start - offset) <= 1
                and deadline <= launcher['session_deadlines'][name], 'Independent bounds differ')
    require(now + 20 < state['deadlines']['term_at'], 'Too late for bounded interaction')
    require(not (run / 'drawable-input-consumed.json').exists(), 'Interaction already consumed')
    attempt = read(run, 'attempt-consumed.json')
    require(attempt['argv'] == guest['argv'] and launcher['started_monotonic'] <= attempt['created']['monotonic'] <= start,
            'Attempt identity differs')
    log = local(run, 'supervision/guest.stdout.txt')
    require(log.stat().st_size <= 64 * 1024 * 1024, 'Guest log exceeds bounded scan')
    events = []
    # Incomplete last line is allowed while the guest appends; complete malformed
    # records fail closed. No historical summary or native final is substituted.
    for line in log.read_text().split('\n')[:-1]:
        if line.startswith('PROBE '):
            event = json.loads(line[6:])
            require(finite(event.get('host_monotonic')) and start <= event['host_monotonic'] <= now,
                    'Raw receipt is outside current guest lifetime')
            require(not events or event['probe_sequence'] > events[-1]['probe_sequence'], 'Raw sequence regressed')
            require(not decisive_event(event), 'Raw fault/guard evidence withholds input')
            events.append(event)
    require(events and fresh(events[-1]['host_monotonic'], now, 5), 'No fresh guest progress receipt')
    require(all(any(e['kind'] == name for e in events) for name in
                ('consumer_hooks_validated', 'completion_hooks_validated', 'original_event_pump_hooks_validated')),
            'Required current original hook validation missing')
    acceptance = next((e for e in reversed(events) if e['kind'] == 'original_consumer_acceptance'), None)
    require(acceptance is not None, 'Original consumer acceptance not yet observed')
    a = acceptance['evidence']
    f = a.get('frame') or {}
    producer = f.get('producer') or {}
    pf = producer.get('frame') or {}
    require(pf.get('listener', 0) - 0x124 == f.get('owner') and pf.get('target') == 0x25dfc4,
            'Producer owner/target mismatch')
    receipts = [dict(kind='original_completion_listener_entry', frame=pf, matched_thread_sp_arguments_lr=True),
                producer.get('listener_return') or {}, producer.get('enclosing_return') or {},
                *producer.get('stores', {}).values()]
    require(len(receipts) == 5 and all(r and matching(events, r) for r in receipts), 'Producer raw receipts partial/mismatched')
    require(all(matching(events, r)['host_monotonic'] < acceptance['host_monotonic'] for r in receipts),
            'Producer must precede consumer')
    for pc, offset, size in (('0x25dfd0', 0x130, 4), ('0x25dfd4', 0x12d, 1)):
        r = producer['stores'][pc]
        require(r['thread'] == pf['thread'] and r['address'] == hex(f['owner'] + offset) and r['size'] == size,
                'Producer store attribution differs')
    require(f.get('flag') == 1 and f.get('countdown') == 0
            and matching(events, dict(kind='original_consumer_entry', thread=f['thread'], owner=hex(f['owner']),
                                     entry_sp=f['entry_sp'], caller=hex(f['caller']), state=f['before'],
                                     matched_main=True, producer_matched=True)),
            'Original main entry/flag/countdown attribution missing')
    require(producer['stores']['0x25dfd0']['after'] == struct.pack('<I', pf['result_argument']).hex()
            and producer['stores']['0x25dfd4']['after'] == '01'
            and producer['listener_return'].get('matched_thread_sp') is True
            and producer['enclosing_return'].get('matched_thread_sp') is True, 'Producer store/return contract differs')
    require(matching(events, dict(kind='original_consumer_return', frame=f,
                                 matched_thread_saved_lr_restored_sp=True)), 'Consumer matched raw return missing')
    require(assess({'acceptance': a}, {})['checks']['original_main_consumer_and_downstream_state'],
            'Original downstream readiness failed')
    for name, call in f['call_returns'].items():
        require(call['thread'] == f['thread'] and matching(events, dict(kind='original_consumer_call_return', call=call)),
                'Downstream actual call/return differs: ' + name)
        require(matching(events, dict(kind='original_consumer_callee_entry', name=name, target=call['target'],
                                     thread=call['thread'], sp=call['sp'], matched_thread_sp_arguments_lr=True)),
                'Downstream raw callee entry missing: ' + name)
    display = read(run, 'display-observations.json')
    require(not display.get('stopping'), 'Display observation stopping')
    captures = [c for c in display.get('captures', []) if c.get('scope') == SCOPE]
    require(len(captures) >= 2, 'Two owned samples not yet observed')
    selected = captures[-2:]
    by_sequence = {e['probe_sequence']: e for e in events}
    for c in selected:
        require(c.get('exit_code') == 0 and c.get('reaped') is True and not c.get('root_capture')
                and acceptance['host_monotonic'] <= c['started_monotonic'] <= c['finished_monotonic'] <= now,
                'Capture failed or predates readiness')
        if xid is not None:
            require(c['window'] == hex(xid), 'Wrong input XID')
        actual = pixel_summary(local(run, c['path']))
        require(all(c.get(k) == actual[k] for k in ('pixel_sha256', 'nonblack_pixels', 'width', 'height')),
                'Pixel record differs from raw capture')
        require(actual['width'] == 800 and actual['height'] == 480 and actual['nonblack_pixels'] > 0,
                'Exact nonblack 800x480 pixels required')
        ownership = c.get('ownership') or {}
        source = by_sequence.get(ownership.get('probe_sequence'), {})
        request = ownership.get('request')
        require(ownership.get('source') == 'byte_validated_original_XCreateWindow_returned_XID_and_request'
                and source.get('kind') == 'display_buffer_snapshot'
                and source.get('host_monotonic') == ownership.get('host_monotonic')
                and source.get('thread') == ownership.get('thread')
                and source.get('returned_window') == c['window'] and request
                and request.get('name') == 'CreateWindow' and request.get('matches_returned_id') is True
                and request.get('window') == c['window']
                and request in source.get('requests', []) + source.get('xcb', {}).get('requests', []),
                'Current original XID provenance differs')
        tree_rows = [r for r in display.get('observations', []) if r.get('stdout') == c['correlated_tree']
                     and r.get('exit_code') == 0 and r.get('reaped') is True]
        require(tree_rows and 0 <= c['started_monotonic'] - tree_rows[-1]['finished_monotonic'] <= 10,
                'Current owned tree receipt missing/stale')
        tree = local(run, c['correlated_tree']).read_text()
        require(c['window'] in re.findall(r'^\s*(0x[0-9a-fA-F]+)\s+.*:\s+.*\d+x\d+', tree, re.M), 'Original XID absent from tree')
        details = [r for r in display.get('drawable_observations', []) if r.get('window') == c['window']
                   and r.get('exit_code') == 0 and r.get('reaped') is True
                   and 0 <= c['started_monotonic'] - r['finished_monotonic'] <= 10]
        require(details, 'Owned attributes missing/stale')
        detail = max(details, key=lambda r: r['finished_monotonic'])
        attrs = window_attributes(local(run, detail['stdout']).read_text(), c['window'])
        require(attrs == c.get('attributes') and attrs['exact_id_matches'] and attrs['class'] == 'InputOutput'
                and attrs['map_state'] == 'IsViewable', 'Raw owned attributes differ')
    first, last = selected
    require(0 < last['started_monotonic'] - first['finished_monotonic'] <= 60
            and fresh(last['finished_monotonic'], now, 10)
            and (first['window'], first['pixel_sha256']) == (last['window'], last['pixel_sha256']),
            'Owned pixels not fresh and stable')
    pixels = dict(ownership_verified=True, current_original_returned_xid=True, viewable_input_output=True,
                  exact_region=[0, 0, 800, 480], nonblack_pixels=last['nonblack_pixels'], sample_count=2,
                  stable=True, pixel_sha256=last['pixel_sha256'], fresh_live_observations=True,
                  window=last['window'])
    assessment = assess({'acceptance': a}, pixels)
    require(assessment['passed'] is True, 'Required readiness/pixel verdict failed')
    binding = dict(run=str(run), run_inode=run.stat().st_ino, input_session_id=clock['input_session_id'],
                   clock_sha256=sha(local(run, 'session-clock.json')), attempt_sha256=sha(local(run, 'attempt-consumed.json')),
                   owner_pid=state['owner_pid'], watchdog_pid=state['watchdog_pid'], guest_pid=guest['pid'],
                   guest_started_monotonic=start, guest_start_identity=guest['start_identity'],
                   stdout_inode=log.stat().st_ino, term_at=state['deadlines']['term_at'])
    references = dict(acceptance_sequence=acceptance['probe_sequence'], acceptance_sha256=hashlib.sha256(
                      json.dumps(acceptance, sort_keys=True).encode()).hexdigest(),
                      captures=[dict(path=c['path'], raw_sha256=sha(local(run, c['path'])),
                                     window=c['window'], finished_monotonic=c['finished_monotonic']) for c in selected])
    return dict(schema=1, passed=True, assessed_monotonic=now, expires_monotonic=min(now+10, binding['term_at']-20),
                binding=binding, references=references, **{k: v for k, v in assessment.items() if k != 'passed'})


def publish(run, record):
    """Write once after raw assessment. Never used by offline controls on prepared/."""
    run = Path(run).resolve()
    current = evaluate(run)
    require(all(current[k] == record[k] for k in ('binding', 'references')), 'Evidence changed before publication')
    with (run / 'completion-prerequisite.json').open('x') as output:
        json.dump(current, output, indent=2)
        output.write('\n')
    return current


def validate_for_send(run, xid, *, now=None):
    """Recompute raw gate immediately before send; summary booleans cannot grant it."""
    run = Path(run).resolve()
    now = time.monotonic() if now is None else now
    record = read(run, 'completion-prerequisite.json')
    require(record.get('schema') == 1 and record.get('passed') is True
            and fresh(record.get('assessed_monotonic'), now, 10)
            and finite(record.get('expires_monotonic')) and now < record['expires_monotonic'],
            'Bound prerequisite missing, stale or failed')
    actual = evaluate(run, now=now, xid=xid)
    require(all(record.get(k) == actual[k] for k in ('binding', 'references', 'checks',
                'original_completion_state_evidence', 'owned_pixel_evidence')), 'Bound prerequisite differs from current raw evidence')
    return record
