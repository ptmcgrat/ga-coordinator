"""Thin, strict wrapper around the rclone command line.

Errors are raised with rclone's own message (nothing is swallowed). Transfers
use `copy` with --immutable: files that already exist and are identical are
skipped; an existing file that differs is an error, never overwritten.
"""

from __future__ import annotations

import os
import re
import subprocess

MIN_VERSION = (1, 57, 0)        # the version found on mzebra (spec section 3a)
ENV_BINARY = "GA_RCLONE"


class RcloneError(RuntimeError):
    pass


def binary():
    return os.environ.get(ENV_BINARY, "rclone")


def parse_version(text):
    m = re.search(r"rclone v?([0-9]+)\.([0-9]+)\.([0-9]+)", text)
    if not m:
        raise RcloneError("cannot read an rclone version from %r" % text[:80])
    return tuple(int(x) for x in m.groups())


def version(bin_=None):
    try:
        p = subprocess.run([bin_ or binary(), "version"], capture_output=True, text=True, timeout=60)
    except OSError as e:
        raise RcloneError("cannot run rclone (%s). Install it or set %s" % (e, ENV_BINARY))
    if p.returncode != 0:
        raise RcloneError("rclone version failed: %s" % p.stderr.strip())
    return parse_version(p.stdout)


def require_version(minimum=MIN_VERSION, bin_=None):
    v = version(bin_)
    if v < minimum:
        raise RcloneError("rclone %s is older than the required %s"
                          % (".".join(map(str, v)), ".".join(map(str, minimum))))
    return v


def run(args, bin_=None):
    cmd = [bin_ or binary()] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RcloneError("%s\n  exit %d: %s" % (" ".join(cmd), p.returncode, p.stderr.strip()))
    return p


def lsf(path, bin_=None):
    """Names inside a remote or local directory; [] if it does not exist."""
    cmd = [bin_ or binary(), "lsf", path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode == 0:
        return [x for x in p.stdout.splitlines() if x]
    if p.returncode == 3 or "directory not found" in p.stderr:
        return []
    raise RcloneError("%s\n  exit %d: %s" % (" ".join(cmd), p.returncode, p.stderr.strip()))


def transfer_flags(throttle=None, dry_run=True):
    flags = ["--immutable", "-v", "--exclude", ".ga_tmp_*/**"]
    if dry_run:
        flags.append("--dry-run")
    if throttle is not None:
        if throttle.max_jobs:
            flags += ["--transfers", str(throttle.max_jobs), "--checkers", str(throttle.max_jobs)]
        if throttle.threads:
            flags += ["--multi-thread-streams", str(throttle.threads)]
        if throttle.bwlimit:
            flags += ["--bwlimit", throttle.bwlimit]
    return flags


def copy(src, dst, throttle=None, dry_run=True, bin_=None):
    """rclone copy src -> dst (a directory or one file's folder). Returns CompletedProcess."""
    return run(["copy", src, dst] + transfer_flags(throttle, dry_run), bin_)


def copyto(src, dst, throttle=None, dry_run=True, bin_=None):
    """rclone copyto: copy one file to an exact destination path."""
    return run(["copyto", src, dst] + transfer_flags(throttle, dry_run), bin_)
