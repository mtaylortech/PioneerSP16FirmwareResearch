#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below
# this header.
#
# Helper for building/validating feature-trace records used with slice_contracts.py.
#
# Original path in the research tree: .agents/skills/sp16-feature-trace/scripts/trace_records.py
# Original SHA-256 (before this header was added): 1ae14af0cd0ab417408d4c566a360fa7162301c7fbcf47b93fa5ded2dd96d4fe
# License: MIT (see repository LICENSE). No firmware or key is included.
# ---------------------------------------------------------------------------
"""Read-only identity and record checks; no artifact execution or dependencies."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import sys


def identity(path):
    digest = hashlib.sha256()
    size = 0
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
            size += len(chunk)
    return {'path': str(Path(path).resolve()), 'sha256': digest.hexdigest(), 'size': size}


def validate(record, root, verify_hashes=False):
    errors = []
    root = Path(root).resolve()

    def check(condition, message):
        if not condition:
            errors.append(message)

    def fields(obj, spec, label):
        if not isinstance(obj, dict):
            errors.append(f'{label}: expected object')
            return False
        for key, typ in spec.items():
            v = obj.get(key)
            check(key in obj and isinstance(v, typ) and
                  not (typ is int and isinstance(v, bool)), f'{label}.{key}: wrong/missing type')
            if typ is str:
                check(isinstance(v, str) and bool(v.strip()), f'{label}.{key}: empty string')
        return True

    def strings(value, label):
        check(isinstance(value, list) and all(isinstance(x, str) and x.strip() for x in value),
              f'{label}: expected nonempty strings in array')

    def local(path, label, available=True):
        if not isinstance(path, str) or not path.strip():
            errors.append(f'{label}: missing path')
            return None
        p = Path(path)
        if p.is_absolute() or '..' in p.parts:
            errors.append(f'{label}: must be repository-relative without traversal')
            return None
        target = (root / p).resolve()
        if not target.is_relative_to(root):
            errors.append(f'{label}: resolved path escapes repository')
            return None
        if available:
            check(target.is_file(), f'{label}: file unavailable: {path}')
        return target

    def array(name):
        value = record.get(name, [])
        return value if isinstance(value, list) else []

    header = dict(schema_version=int, investigation_id=str, date=str, objective=str,
                  completion_criteria=list, status=str, firmware_version=str, environment=dict,
                  confidence=dict)
    for name in ('artifacts', 'evidence', 'functions', 'relationships', 'findings', 'unknowns',
                 'contradictions', 'validation', 'next_experiments', 'attempts', 'limitations'):
        header[name] = list
    if not fields(record, header, 'trace'):
        return errors
    check(record.get('schema_version') == 1, 'unsupported schema_version')
    check(record.get('status') in ('answered', 'partial', 'unresolved'), 'invalid status')
    try:
        datetime.date.fromisoformat(record.get('date', ''))
    except (TypeError, ValueError):
        errors.append('date must be ISO YYYY-MM-DD')
    check('REPLACE_WITH_' not in json.dumps(record), 'unfilled template values')
    for name in ('completion_criteria', 'unknowns', 'limitations'):
        strings(record.get(name), name)
    check(bool(record.get('completion_criteria')), 'completion_criteria must not be empty')

    ids = {}
    for name in ('artifacts', 'evidence', 'functions', 'findings', 'validation'):
        collection = {}
        for row in array(name):
            if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'].strip():
                errors.append(f'{name}: missing id/object')
                continue
            check(row['id'] not in collection, f'{name}: duplicate id {row["id"]}')
            collection[row['id']] = row
        ids[name] = collection

    def refs(row, label, required=False):
        links = row.get('evidence_ids')
        strings(links, f'{label}.evidence_ids')
        if not isinstance(links, list):
            return
        if required:
            check(bool(links), f'{label}: supporting evidence required')
        for link in links:
            check(isinstance(link, str) and link in ids['evidence'], f'{label}: dangling evidence {link}')

    for key, row in ids['artifacts'].items():
        if not fields(row, dict(id=str, path=str, sha256=str, size=int, role=str, available=bool), key):
            continue
        check(bool(re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', '')))), f'{key}: invalid sha256')
        check(isinstance(row.get('size'), int) and row['size'] >= 0, f'{key}: invalid size')
        target = local(row.get('path'), key, row.get('available') is True)
        if verify_hashes and row.get('available') is True and target and target.is_file():
            observed = identity(target)
            check(observed['sha256'] == row.get('sha256') and observed['size'] == row.get('size'),
                  f'{key}: artifact identity mismatch')

    env = record.get('environment')
    if fields(env, dict(tools=list, configuration=dict, limitations=list), 'environment'):
        strings(env.get('limitations'), 'environment.limitations')
        if isinstance(env.get('tools'), list):
            for tool in env['tools']:
                fields(tool, dict(name=str, version=str), 'tool')

    for key, row in ids['evidence'].items():
        fields(row, dict(id=str, artifact_id=(str, type(None)), path=str, locator=str,
                         command=dict, rea_evidence_id=(str, type(None)), limitations=list), key)
        if row.get('artifact_id') is not None:
            check(row.get('artifact_id') in ids['artifacts'], f'{key}: dangling artifact')
        local(row.get('path'), key)
        check(bool(row.get('command')), f'{key}: provenance command/arguments required')
        strings(row.get('limitations'), f'{key}.limitations')

    for key, row in ids['functions'].items():
        fields(row, dict(id=str, artifact_id=str, address=(str, type(None)), address_space=str,
                         mode=str, name=str, name_source=str, body_ranges=list, evidence_ids=list), key)
        check(row.get('artifact_id') in ids['artifacts'], f'{key}: dangling artifact')
        entry = row.get('address')
        check(entry is None or bool(re.fullmatch(r'0x[0-9a-fA-F]+', str(entry))), f'{key}: invalid address')
        ranges = row.get('body_ranges')
        contains_entry = False
        if isinstance(ranges, list):
            for bounds in ranges:
                try:
                    start, end = bounds['start'], bounds['end']
                    if not all(isinstance(a, str) and re.fullmatch(r'0x[0-9a-fA-F]+', a) for a in (start, end)):
                        raise ValueError('range address')
                    check(int(start, 16) <= int(end, 16), f'{key}: reversed body range')
                    contains_entry |= entry is not None and int(start, 16) <= int(entry, 16) <= int(end, 16)
                except (KeyError, TypeError, ValueError):
                    errors.append(f'{key}: malformed body range')
            if ranges:
                check(contains_entry, f'{key}: entry not in body ranges')
        refs(row, key, required=entry is not None)

    levels = ('high', 'medium', 'low', 'unknown')
    kinds = ('artifact-observed', 'static-supported', 'runtime-observed', 'inferred', 'hypothesis', 'unknown')
    for key, row in ids['findings'].items():
        fields(row, dict(id=str, kind=str, statement=str, evidence_ids=list, rationale=str,
                         confidence=str, limits=list), key)
        check(row.get('kind') in kinds, f'{key}: invalid finding kind')
        check(row.get('confidence') in levels, f'{key}: invalid confidence')
        refs(row, key, required=row.get('kind') in kinds[:4])
        strings(row.get('limits'), f'{key}.limits')

    for row in array('relationships'):
        if not fields(row, dict(from_function=str, to_function=(str, type(None)), type=str,
                               site=str, status=str, details=str, evidence_ids=list), 'relationship'):
            continue
        check(row.get('from_function') in ids['functions'], 'relationship: dangling from_function')
        check(row.get('to_function') is None or row.get('to_function') in ids['functions'],
              'relationship: dangling to_function')
        check(row.get('status') in ('supported', 'inferred', 'unresolved'), 'relationship: invalid status')
        refs(row, 'relationship', required=row.get('status') != 'unresolved')
    for row in array('contradictions'):
        if fields(row, dict(statement=str, evidence_ids=list, effect=str), 'contradiction'):
            refs(row, 'contradiction', required=True)

    for key, row in ids['validation'].items():
        fields(row, dict(id=str, status=str, procedure=dict, result=(str, type(None)), evidence_ids=list), key)
        state = row.get('status')
        check(state in ('passed', 'failed', 'not-run', 'blocked'), f'{key}: invalid validation status')
        check(bool(row.get('procedure')), f'{key}: missing validation procedure')
        if state in ('passed', 'failed'):
            check(isinstance(row.get('result'), str) and bool(row['result'].strip()), f'{key}: actual result required')
        elif state in ('not-run', 'blocked'):
            check(row.get('result') is None, f'{key}: unexecuted validation cannot have actual result')
        refs(row, key, required=state in ('passed', 'failed'))

    confidence = record.get('confidence')
    if fields(confidence, dict(level=str, justification=str), 'confidence'):
        check(confidence.get('level') in levels, 'invalid overall confidence')
    for row in array('next_experiments'):
        fields(row, dict(question=str, method=str, expected_discriminator=str, requires=list,
                         runtime_authorized=bool), 'next experiment')
        if isinstance(row, dict):
            strings(row.get('requires'), 'next experiment.requires')
    for row in array('attempts'):
        if fields(row, dict(query=dict, scope=str, result=str, evidence_ids=list,
                            repeat_reason=(str, type(None))), 'attempt'):
            check(bool(row.get('query')), 'attempt: empty query')
            refs(row, 'attempt')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    ident = sub.add_parser('identity')
    ident.add_argument('path', type=Path)
    ident.add_argument('--expect', help='Expected lowercase SHA-256; mismatch returns nonzero')
    report = sub.add_parser('validate')
    report.add_argument('path', type=Path)
    report.add_argument('--root', required=True, type=Path)
    report.add_argument('--verify-hashes', action='store_true')
    args = parser.parse_args()
    try:
        if args.action == 'identity':
            output = identity(args.path)
            errors = [] if args.expect is None or output['sha256'] == args.expect else ['artifact identity mismatch']
        else:
            output = {'record': str(args.path.resolve()), 'hashes_checked': args.verify_hashes}
            errors = validate(json.loads(args.path.read_text()), args.root, args.verify_hashes)
    except (OSError, ValueError, TypeError) as exc:
        output, errors = {}, [f'{type(exc).__name__}: {exc}']
    output.update(valid=not errors, errors=errors)
    print(json.dumps(output, indent=2, sort_keys=True))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
