# ---------------------------------------------------------------------------
# SP-16 open research — original research script, published unchanged below.
#
# Two-pass whole-recording, linked-channel peak normalization core for PCM16/24 WAV (exact rational gain, ties-to-even rounding, no dither, exact silence preserved, unsupported forms refused).
#
# Original path: experiments/normalization-host-core-20261011/core.py
# Original SHA-256 (before this header): 6bd11f5cc74a54069dee9ea26f196a1fd9d0b6c2b559128a2ee5a3e850cf92ad
# License: MIT. Host-side tool only: it does not run on, or modify, the SP-16.
# ---------------------------------------------------------------------------
"""Disposable host development PCM core. No Keep, selected-original or preview API."""
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import os
from pathlib import Path
import stat
import struct


class Refused(ValueError):
    pass


@dataclass(frozen=True)
class Parameters:
    # All choices required. These are caller-supplied examples, not product defaults.
    ceiling: Fraction              # fraction of symmetric signed full scale 2**(bits-1)
    rounding: str                  # nearest_even or toward_zero
    near_peak: Fraction            # same full-scale unit; inclusive threshold
    near_action: str               # unchanged or refuse
    max_gain: Fraction | None      # None explicitly means unlimited
    bits: tuple[int, ...]
    channels: tuple[int, ...]
    rates: tuple[int, ...]
    max_frames: int
    max_bytes: int
    block_frames: int

    def validate(self):
        if not isinstance(self.ceiling, Fraction) or not 0 < self.ceiling <= 1:
            raise Refused('explicit exact ceiling in (0,1] required')
        if self.rounding not in ('nearest_even', 'toward_zero'):
            raise Refused('unsupported rounding')
        if not isinstance(self.near_peak, Fraction) or not 0 <= self.near_peak < 1:
            raise Refused('invalid near threshold')
        if self.near_action not in ('unchanged', 'refuse'):
            raise Refused('explicit near action required')
        if self.max_gain is not None and (not isinstance(self.max_gain, Fraction) or self.max_gain <= 0):
            raise Refused('invalid maximum gain')
        if not self.bits or any(x not in (16, 24, 32) for x in self.bits):
            raise Refused('development core supports signed PCM16/24/32 only')
        if not self.channels or not self.rates or any(x <= 0 for x in (*self.channels, *self.rates)):
            raise Refused('explicit positive geometry envelope required')
        if min(self.max_frames, self.max_bytes, self.block_frames) <= 0:
            raise Refused('explicit finite limits required')


def fixture_path(root, path):
    root, path = Path(root).absolute(), Path(path).absolute()
    owned = Path(__file__).resolve().parent
    if root == owned or owned not in root.parents:
        raise Refused('fixture root must be inside this owned experiment directory')
    if root.is_symlink() or root.resolve() != root:
        raise Refused('fixture root cannot have symlink components')
    if path == root or root not in path.parents:
        raise Refused('only disposable owned fixture paths permitted')
    if any(x.is_symlink() for x in (path, *path.parents)):
        raise Refused('symlink refused')
    if path.parent.resolve() != path.parent:
        raise Refused('unresolved fixture parent')
    return path


def digest(f):
    f.seek(0)
    h = hashlib.sha256()
    while data := f.read(65536):
        h.update(data)
    return h.hexdigest()


def header(f, p):
    size = os.fstat(f.fileno()).st_size
    if size > p.max_bytes or size < 12:
        raise Refused('file-size envelope')
    f.seek(0)
    lead = f.read(12)
    if lead[:4] != b'RIFF' or lead[8:] != b'WAVE' or struct.unpack('<I', lead[4:8])[0] + 8 != size:
        raise Refused('only complete little-endian RIFF/WAVE; no trailing bytes')
    chunks, geometry, audio = [], None, None
    pos = 12
    while pos < size:
        f.seek(pos)
        raw = f.read(8)
        if len(raw) != 8:
            raise Refused('incomplete chunk header')
        tag, length = struct.unpack('<4sI', raw)
        end = pos + 8 + length + (length & 1)
        if end > size:
            raise Refused('incomplete chunk or padding')
        if tag == b'fmt ':
            if geometry is not None or length != 16:
                raise Refused('duplicate/extended format unsupported')
            code, ch, rate, byte_rate, align, bits = struct.unpack('<HHIIHH', f.read(16))
            if code != 1 or bits not in p.bits or ch not in p.channels or rate not in p.rates:
                raise Refused('encoding/geometry envelope')
            if align != ch * (bits // 8) or byte_rate != rate * align:
                raise Refused('inconsistent format geometry')
            geometry = (ch, rate, align, bits)
        elif tag == b'data':
            if audio is not None:
                raise Refused('multiple audio chunks unsupported')
            audio = (pos + 8, length)
        elif tag == b'LIST':
            if length < 4 or f.read(4) != b'INFO':
                raise Refused('only INFO list preservation supported')
        elif tag not in (b'JUNK', b'PAD ', b'cue ', b'smpl'):
            # Peak/loudness/checksum/unknown chunks may become invalid after gain.
            raise Refused('unsupported preservation chunk: ' + repr(tag))
        chunks.append((tag, pos, end))
        pos = end
    if geometry is None or audio is None or audio[1] % geometry[2]:
        raise Refused('missing format/audio or incomplete frame')
    frames = audio[1] // geometry[2]
    if frames > p.max_frames:
        raise Refused('frame envelope')
    return geometry, audio, frames, chunks


def samples(f, audio, geometry, block_frames):
    ch, rate, align, bits = geometry
    width = bits // 8
    f.seek(audio[0])
    remaining = audio[1]
    while remaining:
        raw = f.read(min(remaining, align * block_frames))
        if not raw or len(raw) % align:
            raise Refused('short/incomplete audio read')
        remaining -= len(raw)
        yield [int.from_bytes(raw[i:i+width], 'little', signed=True) for i in range(0, len(raw), width)]


def copy_exact(src, dst, count):
    while count:
        raw = src.read(min(count, 65536))
        if not raw:
            raise Refused('incomplete input while copying')
        write_exact(dst, raw)
        count -= len(raw)


def write_exact(dst, raw):
    view = memoryview(raw)
    while view:
        n = dst.write(view)
        if n is None or n <= 0:
            raise Refused('output made no progress')
        view = view[n:]


def normalize_fixture(root, source, output, p):
    """Two-pass, no input writes. An exclusively created disposable output only.

    Requires caller-controlled immutable fixtures; mutation detection is a host
    control, not an adversarial concurrent-writer or selected-original protocol.
    Partial output is retained on error for diagnosis; never reported complete.
    """
    p.validate()
    source, output = fixture_path(root, source), fixture_path(root, output)
    if source == output or output.exists():
        raise Refused('output must be absent and distinct')
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as src:
        before = os.fstat(src.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise Refused('only unshared regular disposable input')
        geometry, audio, frames, chunks = header(src, p)
        identity = digest(src)
        peak = max((abs(s) for block in samples(src, audio, geometry, p.block_frames) for s in block), default=0)
        full_scale = 1 << (geometry[3] - 1)
        # Symmetric representable ceiling avoids positive overflow at exact 0 dBFS.
        target = min(int(p.ceiling * full_scale), full_scale - 1)
        if target <= 0:
            raise Refused('ceiling below one representable sample unit')
        if peak == 0:
            gain, reason = Fraction(1), 'silence'
        elif Fraction(peak, full_scale) <= p.near_peak:
            if p.near_action == 'refuse':
                raise Refused('near-silence refused by explicit parameter')
            gain, reason = Fraction(1), 'near-unchanged'
        else:
            gain, reason = Fraction(target, peak), 'normalize'
            if p.max_gain is not None and gain > p.max_gain:
                gain, reason = p.max_gain, 'amplification-capped'
        dst_fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        output_peak, count = 0, 0
        with os.fdopen(dst_fd, 'wb', buffering=0) as dst:
            src.seek(0)
            copy_exact(src, dst, audio[0])
            width = geometry[3] // 8
            if gain == 1:
                src.seek(audio[0])
                copy_exact(src, dst, audio[1])
                output_peak, count = peak, frames * geometry[0]
            blocks = () if gain == 1 else samples(src, audio, geometry, p.block_frames)
            for block in blocks:
                encoded = bytearray()
                for sample in block:
                    exact = sample * gain
                    value = round(exact) if p.rounding == 'nearest_even' else int(exact)
                    if not -full_scale <= value <= full_scale - 1:
                        raise Refused('overflow; never clamp')
                    # Unchanged near-silence intentionally does not enforce target.
                    if reason not in ('near-unchanged', 'silence') and abs(value) > target:
                        raise Refused('ceiling exceeded; never clamp')
                    encoded.extend(value.to_bytes(width, 'little', signed=True))
                    output_peak = max(output_peak, abs(value))
                    count += 1
                write_exact(dst, encoded)
            src.seek(audio[0] + audio[1])
            copy_exact(src, dst, before.st_size - src.tell())
            if dst.tell() != before.st_size or count != frames * geometry[0]:
                raise Refused('output incomplete')
        after = os.fstat(src.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) or digest(src) != identity:
            raise Refused('fixture changed during processing; output unqualified')
    return dict(input_sha256=identity, geometry=geometry, frames=frames,
                input_peak=peak, output_peak=output_peak, target=target,
                gain=str(gain), reason=reason, samples=count, complete=True)
