"""Streaming BGZF writer (the block-gzip format that samtools/tabix index).

A BGZF file is also an ordinary multi-member gzip file, so gzip/zcat read it.
Plain gzip, by contrast, cannot be indexed by `samtools faidx`.
Format: SAM/BAM specification, section 4.1.
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from concurrent.futures import ThreadPoolExecutor

BLOCK_INPUT = 0xFF00            # 65280 input bytes per block
EOF_BLOCK = bytes.fromhex("1f8b08040000000000ff0600424302001b0003000000000000000000")


def block(data, level=6):
    """One BGZF block holding `data` (at most BLOCK_INPUT bytes)."""
    if len(data) > BLOCK_INPUT:
        raise ValueError("BGZF block input too large")
    comp = zlib.compressobj(level, zlib.DEFLATED, -15)
    body = comp.compress(data) + comp.flush()
    bsize = len(body) + 25      # 18 header + 8 footer - 1
    head = struct.pack("<4BI2BH2BHH", 0x1F, 0x8B, 8, 4, 0, 0, 0xFF, 6,
                       ord("B"), ord("C"), 2, bsize)
    tail = struct.pack("<II", zlib.crc32(data) & 0xFFFFFFFF, len(data))
    return head + body + tail


def compress(src, dst, threads=1, level=6, batch_blocks=64):
    """Compress the binary file object `src` into path `dst` as BGZF.

    Returns (sha256 of the uncompressed bytes, bytes in, bytes out).
    Memory use is bounded by batch_blocks blocks. `threads` blocks are
    compressed in parallel (zlib releases the GIL).
    """
    threads = max(1, int(threads))
    sha = hashlib.sha256()
    n_in = n_out = 0
    pool = ThreadPoolExecutor(max_workers=threads) if threads > 1 else None
    try:
        with open(dst, "wb") as out:
            while True:
                chunks = []
                for _ in range(batch_blocks):
                    c = src.read(BLOCK_INPUT)
                    if not c:
                        break
                    # read() on a buffered file may return fewer bytes than asked
                    while len(c) < BLOCK_INPUT:
                        more = src.read(BLOCK_INPUT - len(c))
                        if not more:
                            break
                        c += more
                    chunks.append(c)
                if not chunks:
                    break
                for c in chunks:
                    sha.update(c)
                    n_in += len(c)
                blocks = pool.map(lambda c: block(c, level), chunks) if pool \
                    else (block(c, level) for c in chunks)
                for b in blocks:
                    out.write(b)
                    n_out += len(b)
            out.write(EOF_BLOCK)
            n_out += len(EOF_BLOCK)
    finally:
        if pool:
            pool.shutdown()
    return sha.hexdigest(), n_in, n_out


def compress_file(src_path, dst, threads=1, level=6):
    with open(src_path, "rb") as fh:
        return compress(fh, dst, threads=threads, level=level)


def is_bgzf(path):
    """True if the file starts with a BGZF block header and ends with the EOF block."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(18)
            fh.seek(-len(EOF_BLOCK), 2)
            tail = fh.read()
    except (OSError, ValueError):
        return False
    return (len(head) == 18 and head[:4] == b"\x1f\x8b\x08\x04"
            and head[12:14] == b"BC" and tail == EOF_BLOCK)
