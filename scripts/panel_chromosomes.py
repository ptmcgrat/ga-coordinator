#!/usr/bin/env python3
"""panel_chromosomes: print the companion table of chromosome accessions for a panel.

    python scripts/panel_chromosomes.py [--panel P1] > config/panel_chromosomes_P1.tsv

One row per panel assembly, in panel order. For each of the inversion chromosomes
(LG2, LG9, LG10, LG11, LG13, LG20) it gives the accession of the sequence that NCBI's
sequence report labels with that chromosome. Reads the provenance.json files under the
data root; changes nothing. Labels are the submitters': NCBI uses 'LG2' in some assemblies
and a plain '2' in others (label_style LG / num). That a number is the same chromosome as
the reference's LG is a working assumption until alignment confirms it.

Warnings (a label missing or on more than one sequence) go to stderr.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import ga_common  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common" / "src"))

from ga_common import panel as gpanel            # noqa: E402
from ga_common import paths as gpaths, throttle   # noqa: E402

CHROMOSOMES = ["2", "9", "10", "11", "13", "20"]
HEADER = ["panel_version", "assembly_id", "label_style"] + ["LG" + c for c in CHROMOSOMES]


def label_of(seq):
    lab = str(seq.get("chr_name", ""))
    return lab[2:] if lab.startswith("LG") else lab


def row_for(assembly_id, panel_version, provenance, warn=lambda m: None):
    by = {}
    for s in provenance["sequences"]:
        by.setdefault(label_of(s), []).append(s["name"])
    style = "LG" if any(str(s.get("chr_name", "")).startswith("LG") for s in provenance["sequences"]) else "num"
    cells = []
    for c in CHROMOSOMES:
        names = by.get(c, [])
        if not names:
            warn("%s: no sequence labelled %s" % (assembly_id, c))
            cells.append("-")
        else:
            if len(names) > 1:
                warn("%s: label %s is on %d sequences (%s)" % (assembly_id, c, len(names), ",".join(names)))
            cells.append(",".join(names))
    return [panel_version, assembly_id, style] + cells


def build(pan, paths, warn=lambda m: None):
    rows = []
    for r in pan.rows:
        f = paths.local("genome_provenance", assembly_id=r["id"], accession_version=r["accession_genbank"])
        if not f.is_file():
            raise FileNotFoundError("%s: not fetched yet (%s)" % (r["id"], f))
        with open(f) as fh:
            rows.append(row_for(r["id"], pan.version, json.load(fh), warn))
    return rows


def main(argv=None, paths=None, out=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--panel", default="P1")
    ap.add_argument("--profile", default=None)
    throttle.add_arguments(ap)       # accepted for consistency; this script is single-threaded
    args = ap.parse_args(argv)
    out = out or sys.stdout
    try:
        paths = paths or gpaths.Paths.load(profile=args.profile)
        if paths.data_root is None:
            raise gpaths.PathsError("profile %r has no local data root" % paths.profile_name)
        pan = gpanel.read_panel(str(Path(paths.config_dir) / ("genome_panel_%s.tsv" % args.panel)))
        rows = build(pan, paths, warn=lambda m: print("warning: " + m, file=sys.stderr))
    except (gpaths.PathsError, gpanel.PanelError, FileNotFoundError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    out.write("\t".join(HEADER) + "\n")
    for r in rows:
        out.write("\t".join(r) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
