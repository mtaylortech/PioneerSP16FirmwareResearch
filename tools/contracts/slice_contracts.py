#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below
# this header.
#
# ARM32 structure-slice contract checker: compares declared partial layouts with observed traces using strict types. It checks declarations; it cannot discover ownership or prove a model matches firmware.
#
# Original path in the research tree: .agents/skills/sp16-feature-trace/scripts/slice_contracts.py
# Original SHA-256 (before this header was added): 9faab40cbad393dc75971471dc8cb952a5ccf57f6da59c9ae580fdfb883b3986
# License: MIT (see repository LICENSE). No firmware or key is included.
# ---------------------------------------------------------------------------
"""Small mechanical checks, not ABI recovery, lifetime proof or a trace oracle."""
import argparse
import json
import math
from pathlib import Path
import re
import sys


def number(value):
    if type(value) is int:
        return value
    if isinstance(value, str):
        import re
        if re.fullmatch(r'(0x[0-9a-fA-F]+|[0-9]+)', value):
            return int(value, 16 if value.startswith('0x') else 10)
    raise ValueError('expected integer or unsigned decimal/hex string (not bool)')


def layout(record):
    errors, unknown = [], []
    try:
        if not isinstance(record, dict):
            raise ValueError('layout must be an object')
        if number(record['pointer_width']) != 4:
            errors.append('ARM32 pointer_width must be 4')
        if record['endianness'] != 'little' or record['mode'] not in ('ARM', 'Thumb'):
            errors.append('selected ARM32LE context missing/wrong')
        for key in ('receiver', 'subobject', 'phase', 'extent_status', 'lifetime_status'):
            if not isinstance(record[key], str) or not record[key].strip():
                errors.append(key + ': missing declaration')
        adjustment = number(record['receiver_adjustment'])
        if adjustment < 0:
            errors.append('receiver adjustment negative')
        extent = record['extent']
        if extent is None:
            unknown.append('object extent unknown; no complete bounds claim')
        elif number(extent) <= 0 or record['extent_status'] != 'supported':
            errors.append('extent must be positive and supported')
        if record['lifetime_status'] != 'supported':
            unknown.append('lifetime ' + record['lifetime_status'])
        fields = record['fields']
        if not isinstance(fields, list) or not fields:
            raise ValueError('nonempty fields required')
        intervals, names = [], set()
        for field in fields:
            if not isinstance(field, dict):
                raise ValueError('field must be an object')
            name = field['name']
            if not isinstance(name, str) or not name or name in names:
                raise ValueError('field names must be nonempty and unique')
            names.add(name)
            offset, width = number(field['offset']), number(field['access_width'])
            if offset < 0 or width <= 0 or offset + width > 2**32:
                errors.append(name + ': impossible range')
            if extent is not None and offset + width > number(extent):
                errors.append(name + ': exceeds supported extent')
            if field['type'] not in ('pointer', 'scalar', 'unknown'):
                errors.append(name + ': unsupported type declaration')
            if field['type'] == 'pointer' and width != 4:
                errors.append(name + ': ARM32 pointer access must be 4')
            if field['type_status'] not in ('supported', 'inferred', 'unknown'):
                errors.append(name + ': invalid type status')
            if field['type_status'] != 'supported' or field['type'] == 'unknown':
                unknown.append(name + ': type ' + field['type_status'])
            if field['access_kind'] not in ('raw', 'abi'):
                errors.append(name + ': declare raw access or ABI member')
            if field['packing'] not in ('unknown', 'unpacked', 'packed'):
                errors.append(name + ': invalid packing declaration')
            alignment = field['alignment']
            if alignment is not None:
                alignment = number(alignment)
                if alignment <= 0 or alignment & (alignment - 1):
                    errors.append(name + ': alignment must be positive power of two')
                elif field['access_kind'] == 'abi' and field['packing'] != 'packed' and offset % alignment:
                    errors.append(name + ': violates declared ABI alignment')
            if field['access_kind'] == 'abi' and (alignment is None or field['packing'] == 'unknown'):
                unknown.append(name + ': ABI alignment/packing unknown')
            for key in ('subobject', 'phase', 'original_locator'):
                if not isinstance(field[key], str) or not field[key].strip():
                    errors.append(name + ': missing ' + key)
            overlap = field['overlap']
            if overlap is not None and (not isinstance(overlap, dict) or
                    overlap.get('kind') not in ('union', 'subobject', 'construction-phase') or
                    not isinstance(overlap.get('group'), str) or not overlap['group'].strip() or
                    not isinstance(overlap.get('reason'), str) or not overlap['reason'].strip()):
                raise ValueError(name + ': malformed overlap declaration')
            for prior, start, end in intervals:
                if offset < end and start < offset + width:
                    other = prior['overlap']
                    allowed = overlap is not None and other is not None and overlap['kind'] == other['kind'] and overlap['group'] == other['group']
                    if allowed and overlap['kind'] == 'construction-phase':
                        allowed = field['phase'] != prior['phase']
                    if not allowed:
                        errors.append(name + ': undeclared overlap with ' + prior['name'])
            intervals.append((field, offset, offset + width))
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return dict(status='invalid' if errors else 'partial' if unknown else 'valid',
                errors=errors, unknown=unknown)


def _json_value(value):
    """Accept only finite JSON data; Python bool is a separate scalar type."""
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(_json_value(item) for item in value)
    if type(value) is dict:
        return all(type(key) is str and _json_value(item) for key, item in value.items())
    return False


def _strict_json_equal(left, right):
    """No coercion: parsed int and float are distinct; object order is incidental."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_strict_json_equal(left[key], right[key]) for key in left)
    if type(left) is list:
        return len(left) == len(right) and all(_strict_json_equal(a, b) for a, b in zip(left, right))
    return left == right


def compare(contract, actual):
    """Compare a closed, normalized slice. Expectations must be supplied independently."""
    errors = []
    try:
        if not isinstance(contract, dict) or not isinstance(actual, dict):
            raise ValueError('comparison inputs must be objects')
        context_keys = ('version', 'sha256', 'slice', 'receiver', 'adapters')
        for label, record in (('contract', contract), ('actual', actual)):
            for key in context_keys:
                if key not in record:
                    errors.append(label + '.' + key + ': missing context')
                    continue
                value = record[key]
                if key == 'adapters':
                    valid = type(value) is dict and _json_value(value)
                elif key == 'sha256':
                    valid = type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value) is not None
                else:
                    valid = type(value) is str and bool(value.strip())
                if not valid:
                    errors.append(label + '.' + key + ': malformed context')
        for key in context_keys:
            if key in contract and key in actual and not _strict_json_equal(contract[key], actual[key]):
                errors.append(key + ': context mismatch (strict types/values)')
        incidental = contract['incidental_keys']
        if not isinstance(incidental, list) or any(x not in ('timestamp', 'sequence') for x in incidental):
            raise ValueError('only timestamp/sequence may be incidental')
        expected, events = contract['events'], actual['events']
        if not isinstance(expected, list) or not expected or not isinstance(events, list):
            raise ValueError('nonempty expected events and actual array required')
        def index(rows, normalize=False):
            by_id, positions = {}, {}
            for i, row in enumerate(rows):
                if not isinstance(row, dict) or not isinstance(row.get('id'), str) or not row['id'] or row['id'] in by_id:
                    raise ValueError('missing/duplicate/malformed event id')
                by_id[row['id']] = {k: v for k, v in row.items() if not normalize or k not in incidental}
                positions[row['id']] = i
            return by_id, positions
        wanted, _ = index(expected)
        got, positions = index(events, True)
        if wanted.keys() != got.keys():
            errors.append('missing/extra events')
        for key in wanted.keys() & got.keys():
            # JSON serialization preserves bool versus numeric distinctions.
            if json.dumps(wanted[key], sort_keys=True) != json.dumps(got[key], sort_keys=True):
                errors.append(key + ': wrong event/result/effect')
        edges = contract['before']
        if not isinstance(edges, list):
            raise ValueError('partial ordering must be an array')
        for edge in edges:
            if not isinstance(edge, list) or len(edge) != 2 or any(x not in wanted for x in edge) or edge[0] == edge[1]:
                raise ValueError('malformed order edge')
            if all(x in positions for x in edge) and positions[edge[0]] >= positions[edge[1]]:
                errors.append('required order violated: ' + ' < '.join(edge))
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
    return dict(status='rejected' if errors else 'matched', errors=errors,
                qualification='mechanics only; original evidence authority is caller-supplied')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('layout', 'compare'))
    parser.add_argument('declaration', type=Path)
    parser.add_argument('actual', type=Path, nargs='?')
    args = parser.parse_args()
    try:
        declaration = json.loads(args.declaration.read_text())
        if args.operation == 'layout':
            result = layout(declaration)
        else:
            if args.actual is None:
                raise ValueError('compare requires actual trace')
            result = compare(declaration, json.loads(args.actual.read_text()))
    except (OSError, ValueError) as exc:
        result = dict(status='invalid', errors=[str(exc)])
    print(json.dumps(result, indent=2))
    return 1 if result['status'] in ('invalid', 'rejected') else 0


if __name__ == '__main__':
    sys.exit(main())
