#!/usr/bin/env python3
"""
Parse a Pioneer TORAIZ SP-16 project (.prj) or per-sample adjunct file (.wav.dat).

A .prj is:  b"vltrgzip" (8-byte magic) + zlib-deflated JUCE binary ValueTree.
A .wav.dat is an *uncompressed* JUCE binary ValueTree (root "SampleAdjunctData").

This reads files the user owns; it reproduces no firmware. Pure Python, read-only.

Usage:
  python3 parse_project.py FILE            # pretty tree
  python3 parse_project.py FILE --schema   # JSON schema (node types/fields)
Verified against firmware 1.50 project data; 1.60 is the same container.
"""
import sys, struct, zlib, json, re, collections

# JUCE var stream markers (this build): 1 int, 2 boolTrue, 3 boolFalse,
# 4 double, 5 string, 6 int64, 7 array, 8 binary. var length 0 = void/undefined.
class Reader:
    def __init__(self, b): self.b, self.p = b, 0
    def string(self):
        e = self.b.index(b'\x00', self.p); v = self.b[self.p:e]; self.p = e+1
        return v.decode('utf-8', 'replace')
    def cint(self):
        n = self.b[self.p]; self.p += 1; neg = n & 0x80; n &= 0x7f; v = 0
        for i in range(n): v |= self.b[self.p] << (8*i); self.p += 1
        return -v if neg else v
    def var(self):
        nb = self.cint()
        if nb == 0: return None
        m = self.b[self.p]; pay = self.b[self.p+1:self.p+nb]; self.p += nb
        if m == 1: return struct.unpack('<i', pay[:4])[0]
        if m == 2: return True
        if m == 3: return False
        if m == 4: return struct.unpack('<d', pay[:8])[0]
        if m == 5: return pay.split(b'\x00')[0].decode('utf-8', 'replace')
        if m == 6: return struct.unpack('<q', pay[:8])[0]
        if m == 7: return {'__array__': pay.hex()}
        if m == 8: return {'__binary__': len(pay), 'hex': pay.hex()}
        return {'__marker__': m, 'hex': pay.hex()}

def read_tree(r):
    t = r.string(); np = r.cint(); props = []
    for _ in range(np): props.append((r.string(), r.var()))
    nc = r.cint(); kids = [read_tree(r) for _ in range(nc)]
    return {'type': t, 'props': props, 'children': kids}

def load(path):
    data = open(path, 'rb').read()
    raw = zlib.decompress(data[8:]) if data[:8] == b'vltrgzip' else data
    r = Reader(raw); root = read_tree(r)
    if r.p != len(raw): sys.stderr.write(f"warning: consumed {r.p}/{len(raw)}\n")
    return root

def typename(v):
    if isinstance(v, bool): return 'bool'
    if isinstance(v, int): return 'int'
    if isinstance(v, float): return 'double'
    if isinstance(v, str): return 'string'
    if v is None: return 'void'
    if isinstance(v, dict):
        return 'array' if '__array__' in v else ('binary' if '__binary__' in v else 'var')
    return type(v).__name__

def schema(root):
    S = collections.OrderedDict()
    def norm(t): return re.sub(r'\d+$', '', t)
    def walk(n):
        nt = norm(n['type']); s = S.setdefault(nt, {'count': 0, 'fields': collections.OrderedDict(), 'children': collections.Counter()})
        s['count'] += 1
        for k, v in n['props']:
            if k not in s['fields']: s['fields'][k] = typename(v)
        for c in n['children']: s['children'][norm(c['type'])] += 1
        for c in n['children']: walk(c)
    walk(root)
    return {nt: {'count': s['count'], 'fields': s['fields'], 'children': dict(s['children'])} for nt, s in S.items()}

def pretty(n, d=0, maxk=8):
    ps = ', '.join(f"{k}={v!r}" for k, v in n['props'][:12])
    print('  '*d + f"{n['type']} [{len(n['props'])}p {len(n['children'])}c] {ps}")
    for c in n['children'][:maxk]: pretty(c, d+1, maxk)
    if len(n['children']) > maxk: print('  '*(d+1) + f"… +{len(n['children'])-maxk} more")

if __name__ == '__main__':
    root = load(sys.argv[1])
    if '--schema' in sys.argv: print(json.dumps(schema(root), indent=1))
    else: pretty(root)
