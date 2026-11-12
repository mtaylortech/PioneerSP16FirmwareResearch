# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below.
#
# Synthetic fixture suite: generates WAVs (including ~100 MB large cases), runs core + oracle, and checks deliberate failure/refusal cases. Usage: python3 check_fixtures.py RESULTS_DIR FIXTURES_DIR
#
# Original path: experiments/normalization-host-core-20261011/check_fixtures.py
# Original SHA-256 (before this header): 7543abaa427f13f3beba246d1869fd266b085cbf718af778b056fb8cd81b96cb
# License: MIT. Host-side tool only: it does not run on, or modify, the SP-16.
# ---------------------------------------------------------------------------
"""Finite fixture suite. Output oracle has no dependency on production code."""
from dataclasses import replace, asdict
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import sys
import wave

import core
import oracle
from profile import owner_profile, MAX_BYTES

BASE = Path(__file__).resolve().parent
RESULTS = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / 'results'
ROOT = Path(sys.argv[2]) if len(sys.argv) > 2 else BASE / 'fixtures'
assert BASE in RESULTS.absolute().parents and BASE in ROOT.absolute().parents
ROOT.mkdir(exist_ok=True)
RESULTS.mkdir(exist_ok=True)
records = []


def chunk(tag, body, pad=b'\xa5'):
    return tag + struct.pack('<I', len(body)) + body + (pad if len(body) % 2 else b'')


def wav(samples, bits, channels, rate, extras=(), code=1):
    width = bits // 8
    fmt = struct.pack('<HHIIHH', code, channels, rate, channels*width*rate, channels*width, bits)
    # Fixture serialization uses struct for PCM16/32; oracle24 has distinct decode.
    if bits in (16, 32):
        audio = struct.pack('<' + ('h' if bits == 16 else 'i')*len(samples), *samples)
    elif bits == 24:
        audio = b''.join(struct.pack('<I', s & 0xffffff)[:3] for s in samples)
    else:
        audio = bytes(samples)
    body = b'WAVE' + chunk(b'JUNK', b'abc') + chunk(b'fmt ', fmt)
    body += chunk(b'LIST', b'INFO' + chunk(b'INAM', b'test\0'))
    # Cue and sampler geometry are valid, unchanged frame positions, no peak cache.
    body += chunk(b'cue ', struct.pack('<I', 0))
    body += chunk(b'smpl', struct.pack('<9I', 0, 0, 1_000_000_000//rate, 60, 0, 0, 0, 0, 0))
    body += b''.join(chunk(t, b) for t, b in extras)
    body += chunk(b'data', audio) + chunk(b'PAD ', b'xyz')
    return b'RIFF' + struct.pack('<I', len(body)) + body


def run_case(name, samples, bits, ch, rate, p, gain, target=None):
    inp, out = ROOT / (name + '.in.wav'), ROOT / (name + '.out.wav')
    before = wav(samples, bits, ch, rate)
    inp.write_bytes(before)
    identity = (inp.stat().st_mode, inp.stat().st_mtime_ns, hashlib.sha256(before).hexdigest())
    receipt = core.normalize_fixture(ROOT, inp, out, p)
    checked = oracle.check(before, out.read_bytes(), samples, gain, p.rounding, target)
    assert (inp.stat().st_mode, inp.stat().st_mtime_ns, hashlib.sha256(inp.read_bytes()).hexdigest()) == identity
    assert receipt['output_peak'] == checked['decoded_peak']
    assert receipt['samples'] == checked['samples'] and receipt['complete']
    result = out.read_bytes()
    # Host Discard control: delete only owned processed fixture, input stays exact.
    out.unlink()
    assert inp.read_bytes() == before
    records.append(dict(name=name, kind='processing', oracle=checked, receipt=receipt, discard_input_exact=True))
    return result


def refusal(name, raw, p):
    inp, out = ROOT / (name + '.in.wav'), ROOT / (name + '.out.wav')
    inp.write_bytes(raw)
    try:
        core.normalize_fixture(ROOT, inp, out, p)
    except core.Refused as exc:
        assert not out.exists() and inp.read_bytes() == raw
        records.append(dict(name=name, kind='expected-refusal', reason=str(exc), input_exact=True))
    else:
        raise AssertionError('input should have been refused: ' + name)


def main():
    p = owner_profile()
    # Predeclared targets independent of production profile conversion/receipt.
    targets = {16: 29204, 24: 7476354}
    for bits in (16, 24):
        full = 2**(bits-1)
        for rate in (44100, 48000, 96000):
            for ch in (1, 2):
                scenarios = {
                    'silence': [0] * (11*ch),
                    'extrema': [-full, full-1, 0, 1, -1, full//4] * ch,
                    'asymmetric': [full//4, full//16, 0, -full//4, full//32, 0] * ch,
                    'nearzero': [0, 1, -1, 2, -2, 0] * ch,
                    'latepeak': [1, 0, -1, 0] * (19*ch) + [full-1, 0]*ch,
                }
                rng = random.Random(20261011 + bits + rate + ch)
                scenarios['random'] = [rng.randrange(-full, full) for _ in range(137*ch)]
                for label, values in scenarios.items():
                    source_peak = max(map(abs, values))
                    gain = Fraction(targets[bits], source_peak) if source_peak else Fraction(1)
                    outputs = []
                    for block in (1, 7, 4096):
                        name = f'owner-{bits}-{rate}-{ch}-{label}-block{block}'
                        outputs.append(run_case(name, values, bits, ch, rate, replace(p, block_frames=block), gain, targets[bits]))
                    assert outputs[0] == outputs[1] == outputs[2], 'stream boundaries changed output'
    # Explicit parameter alternatives remain development examples only.
    for bits in (16, 24, 32):
        full = 2**(bits-1)
        for ceiling in (Fraction(1), Fraction(1, 2), Fraction(9, 10)):
            for rule in ('nearest_even', 'toward_zero'):
                target = min(full-1, full*ceiling.numerator//ceiling.denominator)
                samples = [-full, full-1, 1, 3, 5, -1, -3, -5, 0, full//4]
                dev = replace(p, bits=(bits,), ceiling=ceiling, rounding=rule)
                run_case(f'dev-{bits}-{ceiling.numerator}-{ceiling.denominator}-{rule}', samples, bits, 2, 48000, dev, Fraction(target, full), target)
    run_case('empty', [], 16, 1, 44100, p, Fraction(1), targets[16])
    run_case('near-unchanged', [0, 1, -2, 0], 16, 2, 48000,
             replace(p, near_peak=Fraction(2, 32768)), Fraction(1))
    run_case('gain-capped-example', [0, 1, -2, 0], 16, 2, 48000,
             replace(p, max_gain=Fraction(3)), Fraction(3), targets[16])
    refusal('near-refused', wav([0, 1],16,1,44100), replace(p, near_peak=Fraction(2,32768), near_action='refuse'))
    good = wav([1,-2,3,0],16,2,44100)
    refusal('pcm8', wav([128,255],8,1,44100), p)
    refusal('pcm32-outside-owner-envelope', wav([1,-2],32,1,44100), p)
    refusal('float', wav([1,-2],32,1,44100,code=3), p)
    refusal('extensible', wav([1,-2],16,1,44100,code=65534), p)
    refusal('wrong-rate', wav([1,-2],16,1,22050), p)
    refusal('wrong-channels', wav([1,-2,0],16,3,44100), p)
    refusal('partial-frame', wav([1],16,2,44100), p)
    refusal('truncated', good[:-1], p)
    refusal('trailing', good+b'oldtail', p)
    refusal('frame-limit', good, replace(p,max_frames=1))
    refusal('file-limit', good, replace(p,max_bytes=len(good)-1))
    for tag in (b'PEAK',b'bext',b'fact',b'md5 ',b'ID3 ',b'zzzz'):
        refusal('unsupported-'+tag.hex(), wav([1,-2],16,1,44100,extras=((tag,b'unknown'),)), p)
    refusal('duplicate-data', wav([1,-2],16,1,44100,extras=((b'data',b'\0\0'),)), p)
    refusal('list-noninfo', wav([1,-2],16,1,44100,extras=((b'LIST',b'adtl'),)), p)
    for tag in (b'fmt ', b'data'):
        parts = oracle.chunks(good)
        body = b'WAVE'+b''.join(b for t,b in parts if t != tag)
        refusal('missing-'+tag.hex(), b'RIFF'+struct.pack('<I',len(body))+body, p)
    bad = bytearray(good)
    fmt_pos = bad.index(b'fmt ')+8
    struct.pack_into('<H',bad,fmt_pos+12,99)
    refusal('invalid-align', bytes(bad), p)
    # Exact 50,000,000-byte boundary; independent stdlib-wave oracle scans
    # known zero PCM in bounded blocks, rather than building a large sample list.
    large=ROOT/'limit-50MB.in.wav'; large_out=ROOT/'limit-50MB.out.wav'
    audio_size=MAX_BYTES-44
    with large.open('wb') as f:
        f.write(b'RIFF'+struct.pack('<I',MAX_BYTES-8)+b'WAVE')
        f.write(chunk(b'fmt ',struct.pack('<HHIIHH',1,2,96000,576000,6,24)))
        f.write(b'data'+struct.pack('<I',audio_size))
        f.truncate(MAX_BYTES)
    receipt=core.normalize_fixture(ROOT,large,large_out,p)
    assert receipt['gain']=='1' and receipt['frames']==8_333_326
    with wave.open(str(large_out),'rb') as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate(),w.getnframes())==(2,3,96000,8_333_326)
        total=0
        while raw:=w.readframes(4096):
            assert not any(raw), 'large zero fixture changed'
            total+=len(raw)
        assert total==audio_size
    def file_hash(path):
        h=hashlib.sha256()
        with path.open('rb') as f:
            while raw:=f.read(65536): h.update(raw)
        return h.hexdigest()
    assert large_out.stat().st_size==MAX_BYTES and file_hash(large)==file_hash(large_out)
    large_out.unlink()
    records.append(dict(name='50MB-exact-boundary',kind='processing',frames=8_333_326,
                        rate=96000,channels=2,bits=24,complete=True,input_output_sha256=file_hash(large)))
    over=ROOT/'limit-over.in.wav'
    with over.open('wb') as f: f.truncate(MAX_BYTES+1)
    try: core.normalize_fixture(ROOT,over,large_out,p)
    except core.Refused as exc:
        assert not large_out.exists()
        records.append(dict(name='50MB-plus-one-refused',kind='expected-refusal',reason=str(exc)))
    else: raise AssertionError('over size accepted')
    source = ROOT/'paths.in.wav'; source.write_bytes(good)
    out = ROOT/'paths.out.wav'
    for label, src, dst in [('same-path',source,source),('outside',source,BASE/'forbidden.wav')]:
        try: core.normalize_fixture(ROOT,src,dst,p)
        except core.Refused: records.append(dict(name=label,kind='expected-refusal'))
        else: raise AssertionError(label)
    try: core.normalize_fixture(BASE.parent,source,out,p)
    except core.Refused: records.append(dict(name='unowned-root',kind='expected-refusal'))
    else: raise AssertionError('unowned root')
    out.write_bytes(b'preserve-me')
    try: core.normalize_fixture(ROOT,source,out,p)
    except core.Refused: assert out.read_bytes()==b'preserve-me'
    else: raise AssertionError('existing output')
    out.unlink()
    for kind in ('symlink','hardlink'):
        alias=ROOT/(kind+'.wav')
        alias.symlink_to(source) if kind=='symlink' else os.link(source,alias)
        try: core.normalize_fixture(ROOT,alias,out,p)
        except core.Refused: assert not out.exists()
        else: raise AssertionError(kind)
        alias.unlink()
        records.append(dict(name=kind,kind='expected-refusal'))
    # Oracle must detect realistic wrong implementations, not only self-agreement.
    values=[100,-1000,0,200,10,-20]
    raw=wav(values,16,2,44100)
    gain=Fraction(2)
    correct=[200,-2000,0,400,20,-40]
    mutants={
        'one-channel-only':wav([200,-1000,0,200,20,-20],16,2,44100),
        'independent-channel-gain':wav([1000,-2000,0,400,100,-40],16,2,44100),
        'trim':wav(correct[:-2],16,2,44100),
        'resample-header':wav(correct,16,2,48000),
        'changed-silence':wav([200,-2000,1,400,20,-40],16,2,44100),
        'compression':wav([200,-500,0,400,20,-40],16,2,44100),
        'incomplete-output':wav(correct,16,2,44100)[:-2],
    }
    metadata=bytearray(wav(correct,16,2,44100));metadata[metadata.index(b'abc')]=ord('x')
    mutants['metadata-loss']=bytes(metadata)
    for label, mutant in mutants.items():
        try: oracle.check(raw,mutant,values,gain,'nearest_even')
        except (AssertionError, EOFError) as exc:
            records.append(dict(name='oracle-rejects-'+label,kind='oracle-negative',reason=str(exc)))
        else: raise AssertionError('oracle accepted '+label)
    class ShortWriter:
        def __init__(self): self.data=bytearray()
        def write(self,b): self.data.extend(b[:2]);return min(2,len(b))
    short=ShortWriter();core.write_exact(short,b'1234567');assert short.data==b'1234567'
    class NoProgress:
        def write(self,b): return 0
    try: core.write_exact(NoProgress(),b'x')
    except core.Refused: records.append(dict(name='zero-write',kind='injected-error-control'))
    else: raise AssertionError('zero-write')
    records.append(dict(name='positive-short-write',kind='injected-error-control'))
    # Injected host write failure must leave input exact, no completion receipt,
    # and an identifiable incomplete disposable output for diagnosis.
    failed=ROOT/'injected-write-failure.out.wav'
    original_write=core.write_exact
    def fail_write(dst,raw):
        dst.write(raw[:10])
        raise OSError('injected fixture write failure')
    core.write_exact=fail_write
    try:
        try: core.normalize_fixture(ROOT,source,failed,p)
        except OSError as exc:
            assert source.read_bytes()==good and failed.stat().st_size==10
            records.append(dict(name='incomplete-write-retained',kind='injected-error-control',
                                reason=str(exc),partial_bytes=10,input_exact=True))
        else: raise AssertionError('write failure reported complete')
    finally: core.write_exact=original_write
    report=dict(status='PASS',owner_profile={k:str(v) if isinstance(v,Fraction) else v for k,v in asdict(p).items()},
                product_acceptance='HOST PROCESSING ONLY; original UI/preview/Keep not run',
                checks=len(records),records=records)
    (RESULTS/'fixture-results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',checks=len(records),result=str(RESULTS/'fixture-results.json'))))


if __name__=='__main__':
    main()
