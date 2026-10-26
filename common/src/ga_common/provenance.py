"""Provenance records: how a fetched file came to be (spec section 5).

One provenance.json per fetched genome folder: accession, files received,
date, tool versions, checksums, and the sequence names and lengths.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone

SCHEMA = "ga-provenance-1"
REQUIRED = ["schema", "kind", "assembly_id", "accession_requested", "accession_fetched",
            "source", "fetched_utc", "tools", "files", "sequences", "checks"]
FILE_REQUIRED = ["name", "role", "bytes", "sha256"]


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def md5_file(path, chunk=1 << 20):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for b in iter(lambda: fh.read(chunk), b""):
            h.update(b)
    return h.hexdigest()


def tool_version(command, flag="--version"):
    """First line of `<command> --version`, or None if the tool is missing."""
    try:
        p = subprocess.run([command, flag], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    text = (p.stdout or p.stderr or "").strip().splitlines()
    return text[0].strip() if text else None


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def new_record(kind, assembly_id, accession_requested, accession_fetched, source,
               tools, files, sequences, checks, **extra):
    rec = {
        "schema": SCHEMA,
        "kind": kind,
        "assembly_id": assembly_id,
        "accession_requested": accession_requested,
        "accession_fetched": accession_fetched,
        "source": source,
        "fetched_utc": utc_now(),
        "tools": tools,
        "files": files,
        "sequences": sequences,
        "checks": checks,
    }
    rec.update(extra)
    return rec


def validate_provenance(rec):
    problems = []
    for k in REQUIRED:
        if k not in rec:
            problems.append("missing field %s" % k)
    if rec.get("schema") != SCHEMA:
        problems.append("schema is %r, expected %s" % (rec.get("schema"), SCHEMA))
    for f in rec.get("files", []):
        for k in FILE_REQUIRED:
            if k not in f:
                problems.append("file entry %s lacks %s" % (f.get("name", "?"), k))
    for s in rec.get("sequences", []):
        if "name" not in s or "length" not in s:
            problems.append("sequence entry %r lacks name or length" % (s,))
    return problems


def write_provenance(folder, rec):
    """Write folder/provenance.json. Refuses to replace an existing record."""
    problems = validate_provenance(rec)
    if problems:
        raise ValueError("invalid provenance: " + "; ".join(problems))
    path = os.path.join(str(folder), "provenance.json")
    if os.path.exists(path):
        raise FileExistsError(path)
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def read_provenance(path):
    with open(path) as fh:
        return json.load(fh)
