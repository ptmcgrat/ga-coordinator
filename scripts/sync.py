#!/usr/bin/env python3
"""sync: move data between this machine's data root and Dropbox (rclone).

    python scripts/sync.py where RELPATH
    python scripts/sync.py pull   RELPATH [--go]
    python scripts/sync.py push   RELPATH [--go]

RELPATH is relative to the data root, e.g. Genomes/MZ_MZ4f/GCA_057381975.1
or RepeatInformation/versions/RI_v1.

Safe by default:
  * DRY RUN unless --go is given (shows what rclone would do).
  * Files that already exist and are identical are skipped; an existing file
    that differs is an error. Nothing is ever overwritten or deleted.
  * Version folders (Genomes/<id>/<accession>, RepeatInformation/versions/RI_vN)
    are announced as such when they already exist at the destination.
  * RELPATH must stay inside the data root (no '..', no absolute paths).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import ga_common  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common" / "src"))

from ga_common import paths as gpaths      # noqa: E402
from ga_common import rclone, throttle      # noqa: E402


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=None, help="machine profile (default: GA_PROFILE or config/local.yaml)")
    sub = ap.add_subparsers(dest="command", required=True)
    for name, help_ in (("where", "print the local and Dropbox location of RELPATH"),
                        ("pull", "Dropbox -> this machine"),
                        ("push", "this machine -> Dropbox")):
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("relpath", help="path relative to the data root")
        if name != "where":
            sp.add_argument("--go", action="store_true", help="really transfer (default is a dry run)")
            sp.add_argument("--file", action="store_true",
                            help="RELPATH is one file (pull needs this; push detects it)")
            throttle.add_arguments(sp, bandwidth=True)
    return ap


def main(argv=None, out=print, paths=None):
    args = build_parser().parse_args(argv)
    try:
        paths = paths or gpaths.Paths.load(profile=args.profile)
        rel = gpaths.clean_relpath(args.relpath)
        local = paths.local_from_rel(str(rel))
        remote = paths.remote_from_rel(str(rel))
        vroot = gpaths.version_root(str(rel))

        if args.command == "where":
            out("relpath : %s" % rel)
            out("local   : %s" % local)
            out("dropbox : %s" % remote)
            out("version folder: %s" % (vroot if vroot else "no (not a version path)"))
            return 0

        th = throttle.from_args(args)
        dry = not args.go
        is_file = args.file or (args.command == "push" and local.is_file())
        if args.command == "push":
            if not local.exists():
                out("ERROR: nothing at %s" % local)
                return 2
            src, dst = str(local), remote
        else:
            src, dst = remote, str(local)

        rclone.require_version()
        out("%s %s %s" % ("DRY RUN" if dry else "TRANSFER", args.command, rel))
        out("  from: %s" % src)
        out("  to  : %s" % dst)
        if vroot is not None:
            dest_root = paths.remote_from_rel(str(vroot)) if args.command == "push" \
                else str(paths.local_from_rel(str(vroot)))
            existing = rclone.lsf(dest_root)
            if existing:
                out("  NOTE: version folder %s already exists at the destination. Identical files "
                    "are skipped; any file that differs stops the transfer. Versions are never "
                    "overwritten; to change something, make a new version." % vroot)
        fn = rclone.copyto if is_file else rclone.copy
        p = fn(src, dst, throttle=th, dry_run=dry)
        log = (p.stderr or "").strip()
        if log:
            out(log)
        out("done (dry run: nothing was transferred; add --go to transfer)" if dry else "done")
        return 0
    except (gpaths.PathsError, ValueError) as e:
        out("ERROR: %s" % e)
        return 2
    except rclone.RcloneError as e:
        out("ERROR (rclone): %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
