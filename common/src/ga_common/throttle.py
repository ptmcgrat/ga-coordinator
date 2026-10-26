"""Throttling options shared by every script.

Nothing is capped by default. A limit is applied only when asked for, on the
command line or through an environment variable (command line wins):

    --threads N      GA_MAX_THREADS   CPU threads used inside one job
    --max-jobs N     GA_MAX_JOBS      jobs (e.g. assemblies, transfers) at once
    --bwlimit RATE   GA_BWLIMIT       transfer bandwidth, rclone syntax (e.g. 20M)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

ENV_THREADS = "GA_MAX_THREADS"
ENV_JOBS = "GA_MAX_JOBS"
ENV_BWLIMIT = "GA_BWLIMIT"


def _positive(value, what):
    if value is None or value == "":
        return None
    try:
        n = int(value)
    except (TypeError, ValueError):
        raise ValueError("%s must be a whole number, got %r" % (what, value))
    if n < 1:
        raise ValueError("%s must be at least 1, got %r" % (what, value))
    return n


@dataclass(frozen=True)
class Throttle:
    threads: Optional[int] = None
    max_jobs: Optional[int] = None
    bwlimit: Optional[str] = None

    @classmethod
    def resolve(cls, threads=None, max_jobs=None, bwlimit=None, environ=None):
        env = os.environ if environ is None else environ
        t = threads if threads is not None else env.get(ENV_THREADS)
        j = max_jobs if max_jobs is not None else env.get(ENV_JOBS)
        b = bwlimit if bwlimit else env.get(ENV_BWLIMIT)
        return cls(_positive(t, "threads"), _positive(j, "max jobs"), b or None)

    def thread_count(self, default=None):
        """Threads to use: the limit if set, else `default`, else all CPUs."""
        if self.threads is not None:
            return self.threads
        if default is not None:
            return default
        return os.cpu_count() or 1

    def job_count(self, default=1):
        """Jobs at once: the limit if set, else `default`."""
        return self.max_jobs if self.max_jobs is not None else default


def add_arguments(parser, bandwidth=False):
    """Add --threads and --max-jobs (and optionally --bwlimit) to an argparse parser."""
    g = parser.add_argument_group("throttling (no limit unless given)")
    g.add_argument("--threads", type=int, default=None,
                   help="max CPU threads per job (env %s)" % ENV_THREADS)
    g.add_argument("--max-jobs", type=int, default=None,
                   help="max jobs running at once (env %s)" % ENV_JOBS)
    if bandwidth:
        g.add_argument("--bwlimit", default=None,
                       help="max transfer bandwidth, rclone syntax, e.g. 20M (env %s)" % ENV_BWLIMIT)
    return g


def from_args(args):
    return Throttle.resolve(getattr(args, "threads", None),
                            getattr(args, "max_jobs", None),
                            getattr(args, "bwlimit", None))
