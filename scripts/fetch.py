#!/usr/bin/env python3
"""fetch: download assemblies by accession and record their provenance.

    python scripts/fetch.py panel         [--panel P1] (--all | --ids ID,ID) [--go]
    python scripts/fetch.py supplementary [--ids ID,ID] [--go]

`panel` fetches panel assemblies with NCBI Datasets, by accession and accession
version:  datasets download genome accession <acc> --include genome,gff3,seq-report
`supplementary` copies sequences that are not on NCBI (config/supplementary_sequences.tsv)
from Dropbox, unchanged.

Each assembly lands in  <data root>/Genomes/<assembly_id>/<accession_version>/
  genome.fna.gz          BGZF-compressed (indexable); original checksums in provenance
  annotation.gff3.gz     if annotated
  sequence_report.jsonl  NCBI's sequence report, as received
  provenance.json        accession, files, date, tool versions, checksums, names + lengths

Safe by default: DRY RUN unless --go. A folder is built in a scratch folder and
moved into place only when every check passed; an existing folder is never
touched. Sequence names are kept exactly as received.

Checks before a folder is published (spec section 9): the NCBI md5sum.txt, FASTA
names and lengths against NCBI's sequence report, and against the GFF3
##sequence-region lines; and a read-back of the compressed file.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import ga_common  # noqa: F401
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "common" / "src"))

import ga_common                                   # noqa: E402
from ga_common import bgzf, panel as gpanel         # noqa: E402
from ga_common import paths as gpaths, provenance   # noqa: E402
from ga_common import rclone, seqio, throttle       # noqa: E402

ENV_DATASETS = "GA_DATASETS"
_print_lock = threading.Lock()


class FetchError(RuntimeError):
    pass


def say(msg):
    with _print_lock:
        print(msg, flush=True)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def select_accession(row, prefer="auto"):
    """Which accession to download. auto: RefSeq if the assembly is annotated, else GenBank."""
    gb, rs = row["accession_genbank"], row["accession_refseq"]
    if prefer == "genbank":
        return gb
    if prefer == "refseq":
        if not rs:
            raise FetchError("%s has no RefSeq accession" % row["id"])
        return rs
    return rs if (row["annotated"] == "yes" and rs) else gb


def roundtrip_sha256(path):
    h = hashlib.sha256()
    with gzip.open(path, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stored_entry(name, role, stored_path, original_path, original_name, sha_uncompressed):
    return {
        "name": name, "role": role,
        "bytes": os.path.getsize(stored_path),
        "sha256": provenance.sha256_file(stored_path),
        "compression": "bgzf",
        "original_name": original_name,
        "original_bytes": os.path.getsize(original_path),
        "original_sha256": provenance.sha256_file(original_path),
        "sha256_uncompressed": sha_uncompressed,
    }


def compress_checked(original, dst, threads):
    """BGZF-compress `original` to `dst`, then read it back and compare checksums."""
    sha, _, _ = bgzf.compress_file(original, dst, threads=threads)
    if not bgzf.is_bgzf(dst):
        raise FetchError("%s is not valid BGZF after writing" % dst)
    if roundtrip_sha256(dst) != sha:
        raise FetchError("read-back of %s does not match the original data" % dst)
    return sha


def verify_md5sum_txt(root):
    """Check files listed in NCBI's md5sum.txt. Returns files verified, or None if no md5sum.txt."""
    f = Path(root) / "md5sum.txt"
    if not f.is_file():
        return None
    n = 0
    for line in f.read_text().splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        digest, name = parts[0], parts[1].strip().lstrip("*")
        target = Path(root) / name
        if target.is_file():
            if provenance.md5_file(target) != digest:
                raise FetchError("md5 mismatch for %s (NCBI md5sum.txt)" % name)
            n += 1
    return n


def find_one(root, patterns, what, required=True):
    found = []
    for pat in patterns:
        found += sorted(Path(root).rglob(pat))
    found = sorted(set(found))
    if len(found) > 1:
        raise FetchError("more than one %s in the NCBI download: %s" % (what, [str(x) for x in found]))
    if not found:
        if required:
            raise FetchError("no %s in the NCBI download" % what)
        return None
    return found[0]


def compare_with_report(seqs, report_rows):
    """FASTA (name, length) against NCBI's sequence report. Returns (sequence records, problems)."""
    by_acc = {}
    for r in report_rows:
        for key in ("refseqAccession", "genbankAccession"):
            if r.get(key):
                by_acc[r[key]] = r
    records, problems = [], []
    for name, length in seqs:
        r = by_acc.get(name)
        rec = {"name": name, "length": length}
        if r is None:
            problems.append("%s is not in NCBI's sequence report" % name)
        else:
            rec["ncbi_length"] = r.get("length")
            for src, dst in (("chrName", "chr_name"), ("assignedMoleculeLocationType", "molecule_type"),
                             ("role", "role"), ("sequenceName", "sequence_name")):
                if r.get(src) is not None:
                    rec[dst] = r[src]
            if r.get("length") is not None and int(r["length"]) != length:
                problems.append("%s: FASTA length %d != NCBI sequence report %s" % (name, length, r["length"]))
        records.append(rec)
    if len(report_rows) != len(seqs):
        problems.append("FASTA has %d sequences, NCBI's sequence report %d" % (len(seqs), len(report_rows)))
    return records, problems


def compare_with_gff(seqs, regions):
    problems = []
    lengths = dict(seqs)
    for name, (start, end) in regions.items():
        if name not in lengths:
            problems.append("GFF3 names %s, which is not in the FASTA" % name)
        elif start != 1 or end != lengths[name]:
            problems.append("%s: GFF3 sequence-region %d-%d, FASTA length %d" % (name, start, end, lengths[name]))
    return problems


def datasets_bin():
    return os.environ.get(ENV_DATASETS, "datasets")


def publish(tmp, target):
    if target.exists():
        raise FetchError("%s appeared while fetching; not overwriting" % target)
    os.replace(str(tmp), str(target))


# --------------------------------------------------------------------------
# one NCBI assembly
# --------------------------------------------------------------------------

def fetch_assembly(row, paths, threads, prefer="auto"):
    aid, gb = row["id"], row["accession_genbank"]
    acc = select_accession(row, prefer)
    target = paths.local("genome_dir", assembly_id=aid, accession_version=gb)
    if (target / "provenance.json").is_file():
        return {"id": aid, "status": "skipped", "detail": "already fetched"}
    if target.exists():
        raise FetchError("%s exists without provenance.json (an interrupted copy?). "
                         "Inspect it and remove it by hand; it is never overwritten." % target)
    tmp = target.parent / (".ga_tmp_" + gb)
    try:
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        want_gff = acc.startswith("GCF_")
        include = "genome,gff3,seq-report" if want_gff else "genome,seq-report"
        zpath = tmp / "ncbi.zip"
        cmd = [datasets_bin(), "download", "genome", "accession", acc, "--include", include,
               "--filename", str(zpath)]
        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0 or not zpath.is_file():
            raise FetchError("datasets failed (exit %d): %s" % (p.returncode, (p.stderr or p.stdout).strip()[:500]))
        ex = tmp / "extract"
        with zipfile.ZipFile(zpath) as z:
            z.extractall(ex)
        md5_n = verify_md5sum_txt(ex)

        fna = find_one(ex, ["*_genomic.fna", "*.fna"], "genome FASTA")
        gff = find_one(ex, ["*.gff", "*.gff3"], "GFF3 annotation", required=want_gff)
        rep = find_one(ex, ["sequence_report.jsonl"], "sequence report")

        seqs = seqio.fasta_lengths(fna)
        if not seqs:
            raise FetchError("the genome FASTA has no sequences")
        records, problems = compare_with_report(seqs, seqio.read_jsonl(rep))
        gff_ok = None
        if gff is not None:
            gp = compare_with_gff(seqs, seqio.gff_sequence_regions(gff))
            gff_ok = not gp
            problems += gp
        if problems:
            raise FetchError("checks failed: " + "; ".join(problems[:8]) + (" ..." if len(problems) > 8 else ""))

        files = []
        sha = compress_checked(fna, tmp / "genome.fna.gz", threads)
        files.append(stored_entry("genome.fna.gz", "genome", tmp / "genome.fna.gz", fna, fna.name, sha))
        if gff is not None:
            sha = compress_checked(gff, tmp / "annotation.gff3.gz", threads)
            files.append(stored_entry("annotation.gff3.gz", "annotation", tmp / "annotation.gff3.gz", gff, gff.name, sha))
        shutil.copyfile(rep, tmp / "sequence_report.jsonl")
        files.append({"name": "sequence_report.jsonl", "role": "sequence_report",
                      "bytes": os.path.getsize(tmp / "sequence_report.jsonl"),
                      "sha256": provenance.sha256_file(tmp / "sequence_report.jsonl"),
                      "original_name": rep.name})

        rec = provenance.new_record(
            kind="genome", assembly_id=aid, accession_requested=gb, accession_fetched=acc,
            source={"type": "ncbi-datasets", "command": " ".join(cmd),
                    "download_bytes": os.path.getsize(zpath),
                    "download_sha256": provenance.sha256_file(zpath)},
            tools={"datasets": provenance.tool_version(datasets_bin()),
                   "ga_common": ga_common.__version__,
                   "python": sys.version.split()[0]},
            files=files, sequences=records,
            checks={"lengths_match_sequence_report": True,
                    "gff_regions_match_fasta": gff_ok,
                    "ncbi_md5sum_files_verified": md5_n,
                    "compressed_readback_matches": True},
            panel_accession_genbank=gb)
        os.remove(zpath)
        shutil.rmtree(ex)
        provenance.write_provenance(tmp, rec)
        publish(tmp, target)
        return {"id": aid, "status": "fetched", "detail": "%s -> %s (%d sequences)" % (acc, target, len(seqs))}
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# one supplementary sequence (not on NCBI)
# --------------------------------------------------------------------------

def read_supplementary(path):
    with open(path, newline="") as fh:
        return [dict((k, (v or "").strip()) for k, v in r.items())
                for r in csv.DictReader(fh, delimiter="\t")]


def fetch_supplementary(row, paths, threads, bin_=None):
    sid, version = row["id"], row["version_label"]
    target = paths.local("genome_dir", assembly_id=sid, accession_version=version)
    if (target / "provenance.json").is_file():
        return {"id": sid, "status": "skipped", "detail": "already fetched"}
    if target.exists():
        raise FetchError("%s exists without provenance.json; not overwriting" % target)
    source = paths.apps_remote(row["source_path"])
    tmp = target.parent / (".ga_tmp_" + version)
    try:
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(parents=True)
        original = tmp / "original"
        rclone.copyto(source, str(original), dry_run=False, bin_=bin_)
        if not original.is_file():
            raise FetchError("rclone did not deliver %s" % source)
        seqs = seqio.fasta_lengths(original)
        if not seqs:
            raise FetchError("%s has no sequences" % source)
        names = [n for n, _ in seqs]
        expected = row.get("expected_name", "")
        found = (any(expected in n for n in names)) if expected else None
        if expected and not found:
            say("WARNING %s: expected sequence name %r not among %s" % (sid, expected, names))
        sha = compress_checked(original, tmp / "genome.fna.gz", threads)
        files = [stored_entry("genome.fna.gz", "genome", tmp / "genome.fna.gz", original,
                              Path(row["source_path"]).name, sha)]
        rec = provenance.new_record(
            kind="supplementary", assembly_id=sid, accession_requested=version, accession_fetched=version,
            source={"type": "dropbox-copy", "path": source, "description": row.get("description", ""),
                    "notes": row.get("notes", "")},
            tools={"rclone": ".".join(map(str, rclone.version(bin_))),
                   "ga_common": ga_common.__version__, "python": sys.version.split()[0]},
            files=files, sequences=[{"name": n, "length": l} for n, l in seqs],
            checks={"expected_name_found": found, "compressed_readback_matches": True,
                    "single_sequence": len(seqs) == 1})
        os.remove(original)
        provenance.write_provenance(tmp, rec)
        publish(tmp, target)
        return {"id": sid, "status": "fetched", "detail": "%s -> %s (%d sequence(s): %s)"
                % (source, target, len(seqs), ", ".join(names))}
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# command line
# --------------------------------------------------------------------------

def run_jobs(jobs, th, label):
    """jobs: list of (id, callable(threads)). Returns exit code."""
    n_jobs = th.job_count(default=1)
    per_job = th.thread_count(default=max(1, (os.cpu_count() or 1) // n_jobs))
    say("%s: %d item(s), %d at once, %d thread(s) each" % (label, len(jobs), n_jobs, per_job))
    failed = 0

    def one(job):
        jid, fn = job
        try:
            r = fn(per_job)
        except (FetchError, rclone.RcloneError, OSError, ValueError, FileExistsError) as e:
            say("FAILED  %s: %s" % (jid, e))
            return False
        say("%-8s %s: %s" % (r["status"].upper(), r["id"], r["detail"]))
        return True

    with ThreadPoolExecutor(max_workers=n_jobs) as pool:
        for ok in pool.map(one, jobs):
            failed += 0 if ok else 1
    say("%d failed" % failed if failed else "all done")
    return 1 if failed else 0


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=None)
    sub = ap.add_subparsers(dest="command", required=True)
    sp = sub.add_parser("panel", help="fetch panel assemblies from NCBI")
    sp.add_argument("--panel", default="P1", help="panel version (default P1)")
    sp.add_argument("--panel-file", default=None, help="explicit panel TSV (default config/genome_panel_<panel>.tsv)")
    g = sp.add_mutually_exclusive_group(required=True)
    g.add_argument("--all", action="store_true")
    g.add_argument("--ids", help="comma-separated assembly ids")
    sp.add_argument("--prefer", choices=["auto", "refseq", "genbank"], default="auto",
                    help="auto = RefSeq when the assembly is annotated, else GenBank")
    sp.add_argument("--go", action="store_true", help="really download (default is a dry run)")
    throttle.add_arguments(sp)
    sp = sub.add_parser("supplementary", help="copy non-NCBI sequences from Dropbox")
    sp.add_argument("--ids", default=None, help="comma-separated ids (default: all listed)")
    sp.add_argument("--file", default=None, help="explicit TSV (default config/supplementary_sequences.tsv)")
    sp.add_argument("--go", action="store_true")
    throttle.add_arguments(sp)
    return ap


def main(argv=None, paths=None):
    args = build_parser().parse_args(argv)
    try:
        paths = paths or gpaths.Paths.load(profile=args.profile)
        if paths.data_root is None:
            raise gpaths.PathsError("profile %r has no local data root; fetch must run on a machine "
                                    "with one (e.g. mzebra)" % paths.profile_name)
        th = throttle.from_args(args)
        cfg = paths.config_dir

        if args.command == "panel":
            pfile = args.panel_file or str(Path(cfg) / ("genome_panel_%s.tsv" % args.panel))
            pan = gpanel.read_panel(pfile)
            errors, warnings = gpanel.validate_panel(pan)
            for w in warnings:
                say("panel warning: " + w)
            if errors:
                for e in errors:
                    say("panel ERROR: " + e)
                return 2
            ids = pan.ids() if args.all else [x.strip() for x in args.ids.split(",") if x.strip()]
            unknown = [i for i in ids if i not in pan.ids()]
            if unknown:
                say("ERROR: not in panel %s: %s" % (pan.version, ", ".join(unknown)))
                return 2
            plan = []
            for i in ids:
                row = pan.get(i)
                acc = select_accession(row, args.prefer)
                target = paths.local("genome_dir", assembly_id=i, accession_version=row["accession_genbank"])
                state = "already fetched" if (target / "provenance.json").is_file() else \
                    ("BLOCKED: folder exists without provenance" if target.exists() else "to fetch")
                plan.append((i, row, acc, target, state))
            for i, row, acc, target, state in plan:
                say("%-20s %-16s %s  [%s]" % (i, acc, target, state))
            if not args.go:
                say("DRY RUN: nothing downloaded. Add --go to fetch.")
                return 0
            if provenance.tool_version(datasets_bin()) is None:
                say("ERROR: NCBI 'datasets' not found (conda env ga-coord, or set %s)" % ENV_DATASETS)
                return 2
            jobs = [(i, (lambda t, row=row: fetch_assembly(row, paths, t, args.prefer)))
                    for i, row, acc, target, state in plan]
            return run_jobs(jobs, th, "fetch panel %s" % pan.version)

        rows = read_supplementary(args.file or str(Path(cfg) / "supplementary_sequences.tsv"))
        if args.ids:
            want = [x.strip() for x in args.ids.split(",")]
            rows = [r for r in rows if r["id"] in want]
            missing = set(want) - set(r["id"] for r in rows)
            if missing:
                say("ERROR: not listed: %s" % ", ".join(sorted(missing)))
                return 2
        for r in rows:
            target = paths.local("genome_dir", assembly_id=r["id"], accession_version=r["version_label"])
            state = "already fetched" if (target / "provenance.json").is_file() else "to fetch"
            say("%-12s %s -> %s  [%s]" % (r["id"], paths.apps_remote(r["source_path"]), target, state))
        if not args.go:
            say("DRY RUN: nothing copied. Add --go to fetch.")
            return 0
        rclone.require_version()
        jobs = [(r["id"], (lambda t, r=r: fetch_supplementary(r, paths, t))) for r in rows]
        return run_jobs(jobs, th, "fetch supplementary")
    except (gpaths.PathsError, gpanel.PanelError, rclone.RcloneError, ValueError, OSError) as e:
        say("ERROR: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
