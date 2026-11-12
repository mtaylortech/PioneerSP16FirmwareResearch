#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below
# this header.
#
# Hardened single-release extraction entry point. Reuses decode.py parsing and key handling; refuses unsafe archive names; never executes extracted code. Depends on the research layout.
#
# Original path in the research tree: firmware/tools/extract.py
# Original SHA-256 (before this header was added): a68b93e08c719cb7ae9dda95506876d6b53ade14fe64caf79dda9f029c11c70e
# License: MIT (see repository LICENSE). No firmware or key is included.
# ---------------------------------------------------------------------------
"""Explicit, non-destructive SP16 extraction using the retained decoder primitives."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import zlib

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('sp16_decoder', ROOT/'decode/decode.py')
dec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dec)


def relative(p):
    return p.resolve().relative_to(ROOT).as_posix()


def run(argv, stage, label, commands, allowed=(0,)):
    argv = list(map(str, argv))
    r = subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=180,
                       env={**os.environ, 'LC_ALL':'C', 'TZ':'UTC'})
    (stage/'logs'/f'{label}.stdout.txt').write_bytes(r.stdout)
    (stage/'logs'/f'{label}.stderr.txt').write_bytes(r.stderr)
    commands.append(dict(argv=[a.replace(str(stage), '$STAGING').replace(str(ROOT), '$ROOT') for a in argv],
                         exit_code=r.returncode, stdout=f'logs/{label}.stdout.txt', stderr=f'logs/{label}.stderr.txt'))
    dec.require(r.returncode in allowed, f'{label} failed: {r.returncode}')
    return r.stdout.decode()


def extract(src, expected, digest, stage, out):
    # Resolve only the parents so a dangling destination symlink cannot evade refusal.
    stage = stage.parent.resolve()/stage.name
    out = out.parent.resolve()/out.name
    src = src.resolve()
    for p in (stage, out):
        relative(p)
        dec.require(not os.path.lexists(p), f'Destination must be absent: {p}')
    dec.require(stage != out and stage not in out.parents and out not in stage.parents,
                'Staging and output must be separate non-nested directories')
    dec.require(out.parent.is_dir() and stage.parent.is_dir(), 'Create parent directories explicitly first')
    data = src.read_bytes()
    dec.require(dec.sha(data) == digest, 'Input SHA-256 disagreement')
    cipher, trailer = data[:-20], data[-20:]
    dec.require(trailer[:11] == b'LIVESAMPLER', 'Unexpected update trailer')
    version = trailer[11:16].split(b'\0')[0].decode()
    dec.require(version == expected, 'Expected/trailer version disagreement')
    dec.require(zlib.crc32(cipher) == struct.unpack('<I', trailer[16:])[0], 'Ciphertext CRC disagreement')
    stage.mkdir()
    (stage/'logs').mkdir()
    commands = []
    report = dict(schema_version=1, status='partial', input=relative(src), input_sha256=digest,
                  input_bytes=len(data), trailer_version=version, parameters=dec.PARAMETERS,
                  output=relative(out), staging=relative(stage), commands=commands,
                  decoder_sha256=dec.file_sha(ROOT/'decode/decode.py'), entrypoint_sha256=dec.file_sha(Path(__file__)))
    try:
        decoded = dec.AES().decode(cipher)
        records, info = dec.iso_records(decoded, len(cipher))
        (stage/'decoded.iso').write_bytes(decoded)
        dec.require(dec.file_sha(stage/'decoded.iso') == dec.sha(decoded), 'Decoded ISO write disagreement')
        report.update(decoded_sha256=dec.sha(decoded), filesystem=info, ciphertext_crc_valid=True)
        tree = stage/'iso'
        tree.mkdir()
        # Validated extent reads; no mounting, external archive extraction or code execution.
        for r in sorted(records, key=lambda r:(len(Path(r['path']).parts), r['path'])):
            p = tree/r['path']
            dec.require(all(not a.is_symlink() for a in p.parents), 'ISO link ancestor')
            if stat.S_ISDIR(r['mode']):
                p.mkdir()
            elif stat.S_ISREG(r['mode']):
                with p.open('xb') as f:
                    start=r['extent']*2048
                    f.write(decoded[start:start+r['size']])
        for r in records:
            if stat.S_ISLNK(r['mode']):
                p=tree/r['path']
                dec.require(all(not a.is_symlink() for a in p.parents), 'ISO link ancestor')
                p.symlink_to(r['target'])
        dec.verify_iso(decoded, records, tree)
        dec.save(stage/'iso-manifest.json', records)
        report['iso_all_file_bytes_and_symlinks_verified']=True
        report['version_metadata']={p.name:p.read_text() for p in sorted((tree/'images').iterdir())
                                    if p.name.endswith('.rev') or p.name=='release.txt'}
        dec.require(report['version_metadata']['release.txt'].strip()==expected, 'Decoded release disagreement')
        report['uImage']=dec.uimage_check(tree/'images/uImage')
        report['tools']={'python':sys.version.split()[0], 'unsquashfs':run(['unsquashfs','-version'],stage,'unsquashfs-version',commands,(0,1)).splitlines()[0],
                         'ISO':'retained iso_records + bounded extent extraction', 'tar':'Python tarfile + retained extract_tar/audit_tar'}
        payloads=stage/'payloads'
        payloads.mkdir()
        report['archives']={}
        for archive in sorted((tree/'images').glob('*.tar.gz')):
            dest=payloads/archive.name.removesuffix('.tar.gz')
            result=dec.extract_tar(archive,dest)
            dec.save(stage/(archive.name+'.metadata.json'),result.pop('metadata'))
            result['audit']=dec.audit_tar(archive,dest)
            result['source_sha256']=dec.file_sha(archive)
            report['archives'][archive.name]=result
        for archive in sorted((tree/'images').glob('*.sfs')):
            header=archive.read_bytes()[:96]
            dec.require(struct.unpack_from('<I',header)[0]==0x73717368 and struct.unpack_from('<HH',header,28)==(4,0)
                        and struct.unpack_from('<H',header,20)[0]==1, 'Unsupported SquashFS')
            dec.require(96<=struct.unpack_from('<Q',header,40)[0]<=archive.stat().st_size,'SquashFS length')
            listing=run(['unsquashfs','-lln','-full','-UTC','-no-progress',archive],stage,archive.stem+'-metadata',commands)
            dec.require(not any(line.startswith(('c','b','p','s')) for line in listing.splitlines()),
                        'Special SquashFS entries require metadata-only extraction support')
            run(['unsquashfs','-strict-errors','-no-progress','-processors','2','-mem','64M','-d',payloads/archive.stem,archive],stage,archive.stem+'-extract',commands)
            report['archives'][archive.name]=dict(source_sha256=dec.file_sha(archive), source_listing='logs/'+archive.stem+'-metadata.stdout.txt',
                                                  hardlink_groups=dec.hardlink_groups(payloads/archive.stem), strict_errors=True)
        entries=dec.inventory(payloads)
        dec.save(stage/'payload-manifest.json',entries)
        report['payload_counts']={k:sum(e['type']==k for e in entries) for k in ('file','directory','symlink','special')}
        report['limitations']=['Payload slots are separate; no installed-root overlay inferred.',
                              'No nested archive expansion, firmware execution or mounting.',
                              'Host modes/owners are not source metadata; retain source archives and metadata listings.',
                              'ISO parser exposes mode/links but not Rock Ridge uid/gid/timestamps.']
        report['status']='extracted'
        dec.save(stage/'report.json',report)
        # Atomic directory rename refuses any existing destination, including one created during work.
        dec.require(not os.path.lexists(out),'Output appeared during extraction')
        stage.rename(out)
        print(f'{expected}: extracted to {relative(out)}',flush=True)
    except BaseException as e:
        report.update(status='failed',error=f'{type(e).__name__}: {e}')
        dec.save(stage/'report.json',report)
        raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('input','expected-version','expected-sha256','staging','output'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args()
    extract(Path(a.input),a.expected_version,a.expected_sha256,Path(a.staging),Path(a.output))

if __name__=='__main__':
    main()
