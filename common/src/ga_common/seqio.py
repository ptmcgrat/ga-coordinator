"""Small sequence-file helpers (no external dependencies)."""

from __future__ import annotations

import gzip
import json


def open_text(path):
    p = str(path)
    if p.endswith((".gz", ".bgz")):
        return gzip.open(p, "rt")
    return open(p)


def fasta_lengths(path):
    """[(name, length)] in file order. name = first word of the header line."""
    out, name, n = [], None, 0
    with open_text(path) as fh:
        for line in fh:
            if line.startswith(">"):
                if name is not None:
                    out.append((name, n))
                head = line[1:].strip().split()
                name, n = (head[0] if head else ""), 0
            else:
                if name is None and line.strip():
                    raise ValueError("%s: sequence data before the first header" % path)
                n += len(line.strip())
        if name is not None:
            out.append((name, n))
    return out


def gff_sequence_regions(path):
    """{name: (start, end)} from the '##sequence-region' lines at the top of a GFF3."""
    out = {}
    with open_text(path) as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            if line.startswith("##sequence-region"):
                f = line.split()
                if len(f) >= 4:
                    out[f[1]] = (int(f[2]), int(f[3]))
    return out


def read_jsonl(path):
    rows = []
    with open_text(path) as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows
