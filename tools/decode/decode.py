#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below
# this header.
#
# Original research decoder: decrypts, extracts and audits SP-16 .UPD updates (ISO, tar, SquashFS, nested gzip). macOS-only (uses CommonCrypto via ctypes, bsdtar, unsquashfs). Expects the original research layout: ResearchSourceFiles/ for inputs and extracted/pioneerdj_tsp/... for the key. For portable decryption use upd_decrypt.py beside this file.
#
# Original path in the research tree: decode/decode.py
# Original SHA-256 (before this header was added): 5b59766bf54289e67759e97f00410c33188e16515979a9427fa3e5f31c7c3dc3
# License: MIT (see repository LICENSE). No firmware or key is included.
# ---------------------------------------------------------------------------
"""Decode the two supplied SP-16 updates, without running firmware or mounting images.
macOS: Python 3 stdlib, system CommonCrypto/bsdtar, and unsquashfs (squashfs-tools).
Run from any directory: python3 /path/to/PioneerSP16/decode/decode.py
Use --audit to check saved outputs and expand nested file-level containers in place.
Outputs are replaced only after both samples pass. Original inputs are read-only.
"""
import ctypes
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import subprocess
import tarfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TMP = HERE / 'tmp'
OUT = HERE / 'output'
KEY = ROOT / 'extracted/pioneerdj_tsp/pioneerdj_tsp/initramfs.tar.gz.extracted/initramfs/usr/local/pdj/aes256.key'
INPUTS = ['TORAIZSP16VER150.UPD', 'TORAIZSP16.UPD']
PARAMETERS = dict(cipher='AES-256-CBC', sector_bytes=512,
    iv='LE32(sector number modulo 2^32) + 12 zero bytes', payload_offset=0,
    key_handling='Read until first LF/NUL; copy at most 31 raw bytes; zero-pad to 32. No hex decoding or hash.',
    trailer_bytes=20, trailer_crc='IEEE CRC32 over encrypted payload; stored little-endian')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def save(p, obj):
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def remove_generated_tree(p):
    # ISO directories may be read-only. Never follow firmware symlinks.
    for base, dirs, _ in os.walk(p, followlinks=False):
        os.chmod(base, os.stat(base).st_mode | 0o700)
    shutil.rmtree(p)


def command(args, log=None):
    r = subprocess.run([str(a) for a in args], env={**os.environ, 'LC_ALL': 'C'},
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if log:
        log.write_bytes(r.stdout)
    require(r.returncode == 0, f'{args[0]} failed ({r.returncode}); see {log}')
    return r.stdout.decode('utf-8', 'replace')


class AES:
    def __init__(self):
        # Exact bundled losetup -N semantics: xgetpass 0x9624, set_loop 0x9acc.
        line = KEY.read_bytes().split(b'\n', 1)[0].split(b'\0', 1)[0]
        self.key = line[:31].ljust(32, b'\0')
        self.lib = ctypes.CDLL('/usr/lib/libSystem.B.dylib')
        self.f = self.lib.CCCrypt
        self.f.restype = ctypes.c_int32
        self.f.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32,
            ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

    def decode(self, data):
        require(len(data) % 512 == 0, 'Payload is not sector aligned')
        result = bytearray(len(data))
        buf = ctypes.create_string_buffer(512)
        moved = ctypes.c_size_t()
        for off in range(0, len(data), 512):
            iv = struct.pack('<I', (off // 512) & 0xffffffff) + bytes(12)
            code = self.f(1, 0, 0, self.key, 32, iv, data[off:off+512], 512,
                          buf, 512, ctypes.byref(moved))
            require(code == 0 and moved.value == 512, 'CommonCrypto decryption failed')
            result[off:off+512] = buf.raw
        return bytes(result)


def both(data, off, n):
    a = int.from_bytes(data[off:off+n], 'little')
    b = int.from_bytes(data[off+n:off+2*n], 'big')
    require(a == b, 'ISO both-endian field mismatch')
    return a


def safe_name(name):
    p = PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts, f'Unsafe archive name: {name!r}')
    return p


def iso_records(data, volume_bytes):
    """Validate ISO directory structure independently of bsdtar; resolve Rock Ridge names."""
    pvd = data[32768:34816]
    require(pvd[:7] == b'\x01CD001\x01', 'Missing primary volume descriptor')
    require(both(pvd, 128, 2) == 2048, 'Unsupported ISO block size')
    require(both(pvd, 80, 4) * 2048 == volume_bytes, 'ISO volume length mismatch')
    require(both(pvd, 120, 2) == both(pvd, 124, 2) == 1, 'Unsupported volume set')
    terminated = False
    for off in range(32768, min(len(data), 65536), 2048):
        d = data[off:off+2048]
        require(d[1:7] == b'CD001\x01', 'Invalid volume descriptor sequence')
        if d[0] == 255:
            terminated = True
            break
    require(terminated, 'Missing ISO descriptor terminator')

    def susp(raw, depth=0):
        require(depth < 8, 'Excessive Rock Ridge continuation')
        entries = []
        while len(raw) >= 4 and raw[0]:
            n = raw[2]
            require(4 <= n <= len(raw), 'Invalid SUSP length')
            entry, raw = raw[:n], raw[n:]
            if entry[:2] == b'CE':
                block, off, size = (both(entry, i, 4) for i in (4, 12, 20))
                start = block * 2048 + off
                require(start + size <= len(data), 'Continuation outside decoded sample')
                entries += susp(data[start:start+size], depth+1)
            else:
                entries.append(entry)
        return entries

    root = pvd[156:190]
    todo = [('', both(root, 2, 4), both(root, 10, 4))]
    seen, records = set(), []
    while todo:
        parent, extent, size = todo.pop(0)
        require(extent not in seen, 'Directory cycle or alias')
        seen.add(extent)
        start = extent * 2048
        require(start + size <= len(data), 'Directory outside decoded sample')
        d = data[start:start+size]
        pos, dot = 0, []
        while pos < size:
            n = d[pos]
            if not n:
                pos = (pos // 2048 + 1) * 2048
                continue
            require(n >= 34 and pos % 2048 + n <= 2048 and pos+n <= size, 'Bad directory record')
            r = d[pos:pos+n]
            pos += n
            ex, length = both(r, 2, 4), both(r, 10, 4)
            require(ex*2048 + length <= volume_bytes, 'File extent outside volume')
            require(both(r, 28, 2) == 1 and r[1] == r[26] == r[27] == 0, 'Unsupported ISO layout')
            require(not r[25] & 128, 'Multi-extent files unsupported')
            namelen = r[32]
            require(33+namelen <= len(r), 'Truncated name')
            name = r[33:33+namelen]
            if name in (b'\0', b'\1'):
                dot.append(name)
                if name == b'\0':
                    require(ex == extent and length == size, 'Bad self directory record')
                continue
            attrs = susp(r[33+namelen+(1-namelen % 2):])
            rrname = b''.join(a[5:] for a in attrs if a[:2] == b'NM')
            name = (rrname or name).decode('utf-8')
            require('/' not in name and name not in ('.', '..'), 'Bad ISO filename')
            path = (parent + '/' + name).lstrip('/')
            safe_name(path)
            px = next((a for a in attrs if a[:2] == b'PX'), None)
            mode = both(px, 4, 4) if px else (stat.S_IFDIR if r[25] & 2 else stat.S_IFREG)
            rec = dict(path=path, extent=ex, size=length, mode=mode)
            if stat.S_ISLNK(mode):
                parts = []
                for a in (a for a in attrs if a[:2] == b'SL'):
                    require(a[4] == 0, 'Continued symlink unsupported')
                    x = 5
                    while x < len(a):
                        flags, sz = a[x:x+2]
                        text = a[x+2:x+2+sz].decode()
                        require(flags in (0, 2, 4, 8), 'Unsupported symlink component')
                        parts.append({2: '.', 4: '..', 8: ''}.get(flags, text))
                        x += 2+sz
                rec['target'] = '/'.join(parts)
            records.append(rec)
            if r[25] & 2:
                require(stat.S_ISDIR(mode), 'ISO/Rock Ridge type mismatch')
                todo.append((path, ex, length))
        require(dot[:2] == [b'\0', b'\1'], 'Missing dot directory records')
    require(len({r['path'] for r in records}) == len(records), 'Duplicate ISO paths')
    return records, dict(format='ISO 9660 with Rock Ridge', volume_label=pvd[40:72].decode().strip(),
        volume_bytes=volume_bytes, directories=len(seen), records=len(records))


def verify_iso(data, records, tree, allow_finder_metadata=False):
    for r in records:
        p = tree / r['path']
        mode = r['mode']
        if stat.S_ISREG(mode):
            require(p.is_file() and not p.is_symlink(), f'Missing regular file: {p}')
            start = r['extent']*2048
            r['sha256'] = sha(data[start:start+r['size']])
            require(p.stat().st_size == r['size'] and file_sha(p) == r['sha256'], f'File differs: {p}')
        elif stat.S_ISLNK(mode):
            require(p.is_symlink() and os.readlink(p) == r['target'], f'Symlink differs: {p}')
        elif stat.S_ISDIR(mode):
            require(p.is_dir() and not p.is_symlink(), f'Missing directory: {p}')
        else:
            raise ValueError(f'Unsupported ISO entry: {p}')
    expected = {r['path'] for r in records}
    actual = {p.relative_to(tree).as_posix() for p in tree.rglob('*')}
    extras = actual - expected
    require(not extras or (allow_finder_metadata and all(PurePosixPath(p).name == '.DS_Store' for p in extras)),
            'Unexpected extracted ISO entries')
    return sorted(extras)


def extract_tar(src, dest):
    """Extract regular files first, then links; represent device nodes in metadata only."""
    dest.mkdir()
    metadata, links, skipped = [], [], []
    # Force gzip EOF/CRC validation, including any bytes after tar end markers.
    with src.open('rb') as f:
        compressed = f.read(2) == b'\x1f\x8b'
    if compressed:
        with gzip.open(src, 'rb') as f:
            while f.read(1024*1024):
                pass
    with tarfile.open(src, 'r:*') as tf:
        for m in tf:
            rel = safe_name(m.name)
            p = dest / str(rel)
            record = dict(path=str(rel), mode=m.mode, uid=m.uid, gid=m.gid,
                          mtime=m.mtime, type=m.type.decode(), size=m.size)
            metadata.append(record)
            if m.isdir():
                p.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                p.parent.mkdir(parents=True, exist_ok=True)
                require(not p.exists(), f'Duplicate tar file: {p}')
                h = hashlib.sha256()
                with tf.extractfile(m) as inp, p.open('xb') as out:
                    for chunk in iter(lambda: inp.read(1024*1024), b''):
                        out.write(chunk)
                        h.update(chunk)
                record['sha256'] = h.hexdigest()
                require(p.stat().st_size == m.size and file_sha(p) == record['sha256'], f'Tar file differs: {p}')
                os.chmod(p, (m.mode & 0o777) | 0o400)
            elif m.issym() or m.islnk():
                record['target'] = m.linkname
                links.append((m, p))
            else:
                record.update(devmajor=m.devmajor, devminor=m.devminor)
                skipped.append(record.copy())
        # Parents are existing real directories; never traverse extracted links during writes.
        for m, p in links:
            require(not p.exists() and not p.is_symlink(), f'Link collision: {p}')
            require(all(not x.is_symlink() for x in p.parents if x != dest.parent), 'Link parent is a symlink')
            p.parent.mkdir(parents=True, exist_ok=True)
            if m.issym():
                p.symlink_to(m.linkname)
            else:
                target = dest / str(safe_name(m.linkname))
                require(target.is_file() and not target.is_symlink(), 'Invalid hardlink')
                os.link(target, p)
    return dict(entries=len(metadata), skipped=skipped, metadata=metadata)


def inventory(tree):
    records = []
    for p in sorted(tree.rglob('*')):
        st = p.lstat()
        r = dict(path=p.relative_to(tree).as_posix(), mode=stat.S_IMODE(st.st_mode))
        if p.is_symlink():
            r.update(type='symlink', target=os.readlink(p))
        elif p.is_file():
            r.update(type='file', bytes=st.st_size, sha256=file_sha(p))
        elif p.is_dir():
            r.update(type='directory')
        else:
            r.update(type='special', raw_mode=st.st_mode)
        records.append(r)
    return records


def uimage_check(p):
    data = p.read_bytes()
    magic, hc, timestamp, size, load, entry, dc = struct.unpack('>7I', data[:28])
    require(magic == 0x27051956 and size == len(data)-64, 'Invalid uImage header/size')
    header = data[:4] + bytes(4) + data[8:64]
    require(zlib.crc32(header) == hc and zlib.crc32(data[64:]) == dc, 'uImage CRC mismatch')
    return dict(name=data[32:64].split(b'\0')[0].decode(), data_bytes=size, header_crc_valid=True, data_crc_valid=True)


def audit_tar(src, dest):
    """Compare every source member, including sparse files, links and omitted nodes."""
    expected, skipped, counts = set(), [], dict(files=0, directories=0, symlinks=0, hardlinks=0)
    with src.open('rb') as f:
        compressed = f.read(2) == b'\x1f\x8b'
    if compressed:
        with gzip.open(src, 'rb') as f:
            while f.read(1024*1024):
                pass
    with tarfile.open(src, 'r:*') as tf:
        for m in tf:
            rel = str(safe_name(m.name))
            p = dest / rel
            if not (m.isfile() or m.isdir() or m.issym() or m.islnk()):
                skipped.append(dict(path=rel, type=m.type.decode(), devmajor=m.devmajor, devminor=m.devminor))
                require(not p.exists() and not p.is_symlink(), f'Unexpected materialized special entry: {p}')
                continue
            if rel != '.':
                expected.add(rel)
            require(p.exists() or p.is_symlink(), f'Missing archive member: {p}')
            if m.isfile() or m.islnk():
                require(stat.S_ISREG(p.lstat().st_mode), f'Incorrect member type: {p}')
                h = hashlib.sha256()
                with tf.extractfile(m) as f:
                    for chunk in iter(lambda: f.read(1024*1024), b''):
                        h.update(chunk)
                require(file_sha(p) == h.hexdigest(), f'Archive content mismatch: {p}')
                if m.islnk():
                    require(os.path.samefile(p, dest / str(safe_name(m.linkname))), f'Hardlink mismatch: {p}')
                    counts['hardlinks'] += 1
                else:
                    require(p.stat().st_size == m.size, f'Archive size mismatch: {p}')
                    counts['files'] += 1
            elif m.issym():
                require(p.is_symlink() and os.readlink(p) == m.linkname, f'Symlink mismatch: {p}')
                counts['symlinks'] += 1
            else:
                require(stat.S_ISDIR(p.lstat().st_mode), f'Directory mismatch: {p}')
                counts['directories'] += 1
    actual = {p.relative_to(dest).as_posix() for p in dest.rglob('*')}
    extras = actual - expected
    require(not expected-actual and all(PurePosixPath(p).name == '.DS_Store' for p in extras),
            f'Tar path-set mismatch: {src.name}: missing={sorted(expected-actual)[:5]}, extra={sorted(extras)[:5]}')
    return dict(source_sha256=file_sha(src), matched_entries=len(expected), counts=counts, skipped=skipped,
                host_metadata_extras=sorted(extras))


def compare_inventory(expected, actual):
    paths = {r['path'] for r in expected}
    extras = [r for r in actual if r['path'] not in paths]
    require(all(PurePosixPath(r['path']).name == '.DS_Store' for r in extras), 'Unexpected non-firmware files')
    require(expected == [r for r in actual if r['path'] in paths], 'File inventory, content, mode or link mismatch')
    return [r['path'] for r in extras]


def hardlink_groups(tree):
    groups = {}
    for p in tree.rglob('*'):
        s = p.lstat()
        if stat.S_ISREG(s.st_mode):
            groups.setdefault((s.st_dev, s.st_ino), []).append(p.relative_to(tree).as_posix())
    return sorted(sorted(g) for g in groups.values() if len(g) > 1)


def container_kind(p):
    with p.open('rb') as f:
        h = f.read(512)
    if h.startswith(b'\x1f\x8b'):
        return 'gzip'
    if h[257:262] == b'ustar':
        return 'tar'
    for magic, kind in [(b'hsqs', 'squashfs'), (b'PK\x03\x04', 'zip'),
                        (b'070701', 'cpio'), (b'070702', 'cpio'), (b'070707', 'cpio'),
                        (b'\xfd7zXZ\0', 'xz'), (b'BZh', 'bzip2'), (b'!<arch>\n', 'ar')]:
        if h.startswith(magic):
            return kind
    return None


def expand_nested(image):
    """Expand file-level containers without carving or interpreting executable code."""
    stage = TMP / (image.name + '.nested-building')
    if stage.exists():
        remove_generated_tree(stage)
    stage.mkdir()
    records, unsupported = [], []
    queue = [(p, p.relative_to(image/'payloads')) for p in sorted((image/'payloads').rglob('*'))
             if stat.S_ISREG(p.lstat().st_mode)]
    scanned = 0
    for src, rel in queue:
        scanned += 1
        kind = container_kind(src)
        if kind is None:
            continue
        require(len(records) < 10000 and len(rel.parts) < 40, 'Nested archive expansion limit')
        dest = stage / (str(rel) + '.extracted')
        safe_name(dest.relative_to(stage).as_posix())
        dest.parent.mkdir(parents=True, exist_ok=True)
        record = dict(source=str(rel), format=kind, source_sha256=file_sha(src))
        if kind == 'gzip':
            dest.mkdir()
            output = dest / 'content'
            h = hashlib.sha256()
            size = 0
            with gzip.open(src, 'rb') as inp, output.open('xb') as out:
                for chunk in iter(lambda: inp.read(1024*1024), b''):
                    size += len(chunk)
                    require(size <= 512*1024*1024, 'Nested gzip expansion limit')
                    out.write(chunk)
                    h.update(chunk)
            require(file_sha(output) == h.hexdigest(), 'Nested gzip output mismatch')
            record.update(output=output.relative_to(stage).as_posix(), bytes=size, sha256=h.hexdigest(), crc_valid=True)
            queue.append((output, output.relative_to(stage)))
        elif kind == 'tar':
            result = extract_tar(src, dest)
            save(dest.parent / (dest.name + '.metadata.json'), result['metadata'])
            record.update(output=dest.relative_to(stage).as_posix(), audit=audit_tar(src, dest))
            queue.extend((p, p.relative_to(stage)) for p in sorted(dest.rglob('*'))
                         if stat.S_ISREG(p.lstat().st_mode))
        else:
            unsupported.append(record)
            continue
        records.append(record)
    save(stage/'manifest.json', inventory(stage))
    report = dict(scanned_regular_paths=scanned, expanded_containers=len(records), containers=records,
                  unsupported_containers=unsupported,
                  scope='File-level gzip/tar and listed common archive signatures. No carving inside executable, kernel, bootloader, or raw binary contents.')
    save(stage/'report.json', report)
    final = image/'nested'
    if final.exists():
        remove_generated_tree(final)
    stage.rename(final)
    return report


def audit():
    """Verify saved outputs against original sources, then save additional nested expansions."""
    TMP.mkdir(exist_ok=True)
    results = []
    for i, name in enumerate(INPUTS, 1):
        image = OUT / f'image{i}'
        prior = json.loads((image/'report.json').read_text())
        original = (ROOT/'ResearchSourceFiles'/name).read_bytes()
        require(sha(original) == prior['input_sha256'], 'Original update hash changed')
        require(zlib.crc32(original[:-20]) == struct.unpack('<I', original[-4:])[0], 'Update CRC failed')
        decoded = (image/'decoded.iso').read_bytes()
        require(sha(decoded) == prior['decoded_sha256'], 'Saved ISO hash changed')
        require(AES().decode(original[:-20]) == decoded, 'Saved ISO differs from original update decryption')
        records, info = iso_records(decoded, len(decoded))
        iso_extras = verify_iso(decoded, records, image/'iso', allow_finder_metadata=True)
        require(records == json.loads((image/'iso-manifest.json').read_text()), 'ISO manifest differs')
        payload_extras = compare_inventory(json.loads((image/'payload-manifest.json').read_text()), inventory(image/'payloads'))
        result = dict(image=image.name, input_sha256=sha(original), decoded_sha256=sha(decoded),
                      iso_entries_matched=len(records), archives={}, mismatches=[],
                      host_metadata_extras=dict(iso=iso_extras, payloads=payload_extras))
        for src in sorted((image/'iso/images').glob('*.tar.gz')):
            result['archives'][src.name] = audit_tar(src, image/'payloads'/src.name.removesuffix('.tar.gz'))
        for src in sorted((image/'iso/images').glob('*.sfs')):
            check = TMP / f'{image.name}.{src.stem}.audit'
            if check.exists():
                remove_generated_tree(check)
            command(['unsquashfs', '-strict-errors', '-no-progress', '-processors', '2', '-mem', '64M',
                     '-d', check, src], TMP/f'{image.name}.{src.stem}.audit.log')
            expected = inventory(check)
            actual = image/'payloads'/src.stem
            compare_inventory(expected, inventory(actual))
            links = hardlink_groups(check)
            require(links == hardlink_groups(actual), f'SquashFS hardlink mismatch: {src.name}')
            unique = {(p.lstat().st_dev, p.lstat().st_ino) for p in [check, *check.rglob('*')]}
            with src.open('rb') as f:
                header = f.read(96)
            inodes = struct.unpack_from('<I', header, 4)[0]
            require(len(unique) == inodes, f'SquashFS inode count mismatch: {src.name}')
            result['archives'][src.name] = dict(source_sha256=file_sha(src), matched_entries=len(expected),
                unique_inodes_matched=inodes, hardlink_groups_matched=len(links), strict_reextraction=True)
            remove_generated_tree(check)
        nested = expand_nested(image)
        result['nested'] = dict(expanded_containers=nested['expanded_containers'],
            unsupported_containers=nested['unsupported_containers'], report='nested/report.json')
        result['metadata_only_entries'] = [dict(archive=n, **r) for n,a in result['archives'].items() for r in a.get('skipped', [])]
        result['metadata_only_entries'] += [dict(archive=c['source'], **r) for c in nested['containers'] for r in c.get('audit',{}).get('skipped',[])]
        result['scope'] = nested['scope']
        result['status'] = 'passed' if not nested['unsupported_containers'] else 'passed_with_unsupported_containers'
        save(image/'audit.json', result)
        prior['audit_report'] = 'audit.json'
        prior['nested_extraction'] = result['nested']
        prior['all_metadata_only_entries'] = result['metadata_only_entries']
        save(image/'report.json', prior)
        results.append(result)
        print(f'{image.name}: source audit passed; {nested["expanded_containers"]} nested containers expanded; '
              f'{len(result["metadata_only_entries"])} special entries recorded as metadata', flush=True)
    save(OUT/'audit-summary.json', results)
    save(OUT/'summary.json', [json.loads((OUT/f'image{i}'/'report.json').read_text()) for i in (1, 2)])
    print('Audit complete. Saved ISO, payload and nested trees; see output/image{1,2}/audit.json.')


def main():
    TMP.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    require(shutil.which('bsdtar') and shutil.which('unsquashfs'), 'Need bsdtar and unsquashfs (brew install squashfs)')
    aes = AES()
    prepared = []
    # Checkpoint 2 is enforced for BOTH inputs before full decryption or extraction.
    for i, name in enumerate(INPUTS, 1):
        src = ROOT / 'ResearchSourceFiles' / name
        data = src.read_bytes()
        cipher, trailer = data[:-20], data[-20:]
        require(trailer[:11] == b'LIVESAMPLER', 'Unexpected update trailer')
        require(zlib.crc32(cipher) == struct.unpack('<I', trailer[16:])[0], 'Ciphertext CRC mismatch')
        sample = aes.decode(cipher[:128*1024])
        records, info = iso_records(sample, len(cipher))
        report = dict(input=str(src.relative_to(ROOT)), input_bytes=len(data), input_sha256=sha(data),
            trailer_version=trailer[11:16].split(b'\0')[0].decode(), ciphertext_crc32=f'{zlib.crc32(cipher):08x}',
            ciphertext_crc_valid=True, parameters=PARAMETERS, sample_bytes=len(sample), filesystem=info)
        prepared.append((i, cipher, records, report))
        print(f'image{i}: sample validated, {info["directories"]} directories / {len(records)} records', flush=True)
    summaries = []
    for i, cipher, records, report in prepared:
        stage = TMP / f'image{i}.building'
        if stage.exists():
            remove_generated_tree(stage)
        stage.mkdir()
        decoded = aes.decode(cipher)
        report['decoded_sha256'] = sha(decoded)
        iso = TMP / f'image{i}.iso'
        iso.write_bytes(decoded)
        full_records, _ = iso_records(decoded, len(cipher))
        require(full_records == records, 'Sample/full metadata mismatch')
        tree = stage / 'iso'
        tree.mkdir()
        command(['bsdtar', '-xf', iso, '-C', tree, '--no-same-owner'], TMP / f'image{i}.iso-extract.log')
        verify_iso(decoded, full_records, tree)
        save(stage / 'iso-manifest.json', full_records)
        report['iso_all_file_bytes_and_symlinks_verified'] = True
        report['uImage'] = uimage_check(tree / 'images/uImage')
        report['version_metadata'] = {p.name: p.read_text() for p in sorted((tree/'images').iterdir())
            if p.name.endswith('.rev') or p.name == 'release.txt'}
        require(report['version_metadata']['release.txt'].strip() == report['trailer_version'], 'Version metadata mismatch')
        payloads = stage / 'payloads'
        payloads.mkdir()
        report['archives'] = {}
        report['limitations'] = ['Linux ownership, timestamps and extended attributes are not reproduced on the host; archive originals are retained.',
            'Firmware symlink targets are preserved verbatim; absolute or cross-payload links may not resolve within an individual extracted tree.',
            'Payloads are extracted separately, not merged into a bootable filesystem. Kernel/bootloader and Motorola records remain files; no application reverse engineering.']
        for src in sorted((tree/'images').glob('*.tar.gz')):
            dest = payloads / src.name.removesuffix('.tar.gz')
            result = extract_tar(src, dest)
            save(stage / (src.name + '.metadata.json'), result.pop('metadata'))
            report['archives'][src.name] = result
        for src in sorted((tree/'images').glob('*.sfs')):
            header = src.read_bytes()[:96]
            magic, inodes, created, blocksize = struct.unpack('<4I', header[:16])
            compression, log, flags, ids, major, minor = struct.unpack('<6H', header[20:32])
            bytes_used = struct.unpack_from('<Q', header, 40)[0]
            require(magic == 0x73717368 and (major, minor) == (4, 0) and compression == 1, 'Unsupported SquashFS format')
            require(96 <= bytes_used <= src.stat().st_size, 'Invalid SquashFS size')
            dest = payloads / src.stem
            logpath = TMP / f'image{i}.{src.name}.extract.log'
            command(['unsquashfs', '-strict-errors', '-no-progress', '-processors', '2', '-mem', '64M',
                '-d', dest, src], logpath)
            report['archives'][src.name] = dict(format='SquashFS 4.0, little-endian, zlib', inodes=inodes,
                bytes_used=bytes_used, block_bytes=blocksize, extraction_exit_code=0,
                extraction_log=logpath.read_text())
        all_entries = inventory(payloads)
        save(stage / 'payload-manifest.json', all_entries)
        report['payload_counts'] = {kind: sum(r['type'] == kind for r in all_entries)
            for kind in ('file', 'directory', 'symlink', 'special')}
        report['skipped_entries'] = [dict(archive=a, **s) for a, r in report['archives'].items() for s in r.get('skipped', [])]
        report['complete_regular_files'] = True
        # Keep the decoded container with its evidence and extracted trees.
        iso.rename(stage / 'decoded.iso')
        save(stage / 'report.json', report)
        final = OUT / f'image{i}'
        if final.exists():
            remove_generated_tree(final)
        stage.rename(final)
        summaries.append(report)
        print(f'image{i}: version {report["trailer_version"]}; ISO byte-verified; payloads {report["payload_counts"]}; skipped {len(report["skipped_entries"])} device entries', flush=True)
    save(OUT / 'summary.json', summaries)
    print('Base extraction complete. Auditing saved trees and expanding nested containers next.')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', action='store_true', help='Audit saved trees and expand nested containers without regenerating base trees')
    args = parser.parse_args()
    if not args.audit:
        main()
    audit()
