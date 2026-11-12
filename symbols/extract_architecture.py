#!/usr/bin/env python3
"""
Recover the SP-16 application's C++ class map from a decoded EP085_Main_R binary.

STATIC and READ-ONLY. Reads names and vtable/method *addresses* only; it never
writes or reproduces firmware bytes. The binary is a stripped JUCE C++ program
whose RTTI type_info names survive in .rodata; this script demangles them and
walks type_info -> vtable to recover virtual-method entry addresses.

Usage:
    python3 extract_architecture.py /path/to/EP085_Main_R out_dir/
Requires: c++filt (binutils) on PATH. Works on 1.50/1.60/etc (addresses differ).
Outputs: classes.csv, classes.json  (names + addresses, no firmware bytes)
"""
import sys, os, re, struct, json, subprocess, collections

def load_segments(data):
    # minimal 32-bit little-endian ELF program-header parse -> [(fileoff,vaddr,filesz)]
    assert data[:4] == b'\x7fELF' and data[4] == 1 and data[5] == 1, "not a 32-bit LE ELF"
    e_phoff, = struct.unpack_from('<I', data, 0x1c)
    e_phentsize, e_phnum = struct.unpack_from('<HH', data, 0x2a)
    segs = []
    for i in range(e_phnum):
        off = e_phoff + i*e_phentsize
        p_type, p_offset, p_vaddr, _paddr, p_filesz = struct.unpack_from('<IIIII', data, off)
        if p_type == 1 and p_filesz:          # PT_LOAD
            segs.append((p_offset, p_vaddr, p_filesz))
    return segs

def main():
    BIN, OUT = sys.argv[1], sys.argv[2]
    os.makedirs(OUT, exist_ok=True)
    data = open(BIN, 'rb').read()
    segs = load_segments(data)
    code_lo = min(v for _, v, _ in segs)      # image base
    def va2off(va):
        for fo, v0, sz in segs:
            if v0 <= va < v0+sz: return fo + (va-v0)
        return None
    def rd32(va):
        o = va2off(va)
        return struct.unpack_from('<I', data, o)[0] if o is not None and o+4 <= len(data) else None

    # 1) harvest mangled names from printable runs; demangle via c++filt (variant-tolerant)
    runs = re.findall(rb'[ -~]{5,}', data)
    tok = set()
    for r in runs:
        for m in re.finditer(r'_?Z[NL]?[0-9A-Za-z_]{3,}', r.decode('ascii', 'ignore')):
            tok.add(m.group(0))
    variants = set()
    for t in tok:
        core = t.lstrip('_')
        if core.startswith('Z'):
            variants.add('_'+core)
            st = re.sub(r'E[0-9]+[A-Za-z_][0-9A-Za-z_]*(_[0-9]+)?$', '', core)
            if st != core: variants.add('_'+st)
        else:
            variants.add('_Z'+core)
    variants = sorted(variants)
    out = subprocess.run(['c++filt'], input='\n'.join(variants),
                         capture_output=True, text=True).stdout.split('\n')
    methods = set()
    for raw, dem in zip(variants, out):
        if dem != raw and ('::' in dem or '(' in dem):
            methods.add(re.sub(r'^(typeinfo (name )?for |vtable for |construction vtable for )', '', dem))
    meth_by_cls = collections.defaultdict(list)
    classes = set()
    for m in methods:
        sig = re.sub(r'\(.*', '', m)
        cls = '::'.join(sig.split('::')[:-1]) if '::' in sig else sig
        if cls: classes.add(cls); meth_by_cls[cls].append(m)

    # 2) RTTI walk: class name string -> type_info -> vtable -> method addresses
    idx = collections.defaultdict(list)
    for fo, v0, sz in segs:
        for off in range(fo, fo+sz-3, 4):
            val, = struct.unpack_from('<I', data, off)
            if val: idx[val].append(v0 + (off-fo))
    def mangle_type(dn):
        toks = dn.split('::'); enc = ''.join(f'{len(t)}{t}' for t in toks)
        return enc if len(toks) == 1 else 'N'+enc+'E'
    def find_cstr(b):
        res, start = [], 0
        while True:
            i = data.find(b+b'\x00', start)
            if i < 0: break
            res.append(i); start = i+1
        return res
    LIB = ('std', 'icu_', '__', 'juce', 'CompactLangDet', 'LanguageCode', 'LanguageFromCode')
    code_hi = None  # derive .text top as the start of the first rodata-ish gap is hard; use image span
    code_hi = max(v0+sz for _, v0, sz in segs)
    bound = {}
    for c in [c for c in classes if not c.startswith(LIB)]:
        for noff in find_cstr(mangle_type(c).encode()):
            nva = next((v0+(noff-fo) for fo, v0, sz in segs if fo <= noff < fo+sz), None)
            if nva is None: continue
            done = False
            for ploc in idx.get(nva, []):
                ti = ploc-4
                for vloc in idx.get(ti, []):
                    ms = []
                    for k in range(1, 9):
                        mv = rd32(vloc+4*k)
                        if mv and code_lo <= (mv & ~1) < code_hi: ms.append(mv & ~1)
                        else: break
                    if ms:
                        bound[c] = {'vtable_va': vloc+4, 'methods': ms}; done = True; break
                if done: break
            if done: break

    # 3) emit (names + addresses only)
    allc = sorted(set(classes) | set(bound))
    rows = []
    for c in allc:
        if c.startswith(LIB): continue
        b = bound.get(c)
        rows.append([c, b and '0x%06x' % b['vtable_va'] or '',
                     b and '0x%06x' % b['methods'][0] or '',
                     len(b['methods']) if b else 0, len(meth_by_cls.get(c, []))])
    import csv
    with open(os.path.join(OUT, 'classes.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['class', 'vtable_va', 'first_method_va',
                                       'virtual_methods_seen', 'named_methods_recovered'])
        w.writerows(rows)
    jc = {c: {'vtable_va': bound[c]['vtable_va'] and '0x%06x' % bound[c]['vtable_va'],
              'virtual_method_vas': ['0x%06x' % m for m in bound[c]['methods']],
              'recovered_methods': sorted(meth_by_cls.get(c, []))}
          for c in bound}
    json.dump({'meta': {'binary': os.path.basename(BIN), 'bytes': len(data),
                        'image_base': '0x%x' % code_lo,
                        'method': 'RTTI vtable walk + .rodata demangling (static)'},
               'classes': jc}, open(os.path.join(OUT, 'classes.json'), 'w'), indent=1)
    print(f'classes recovered: {len(rows)}  rtti-bound: {sum(1 for r in rows if r[1])}')

if __name__ == '__main__':
    main()
