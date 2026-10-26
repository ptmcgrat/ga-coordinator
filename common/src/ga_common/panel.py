"""Reader and validator for the assembly panel (contract `panel`, TSV).

One file per panel version: config/genome_panel_P1.tsv, ...
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass

COLUMNS = [
    "panel_version", "id", "species", "code", "sample", "sex", "accession_genbank",
    "accession_refseq", "annotated", "submitter", "released", "level", "contig_N50_Mb",
    "haplotype_status", "role", "repeatmasker", "arrangement_LG2", "arrangement_LG10",
    "arrangement_LG13", "notes",
]

REFERENCE_ACCESSION = "GCF_041146795.1"     # MZ, the reference (spec section 4)
MIN_N50_MB = 20.0                           # selection rule (spec section 4)
SEXES = {"male", "female", "unknown"}
HAPLOTYPE_STATUS = {"collapsed diploid", "haplotype-resolved", "haplotig"}

_GCA = re.compile(r"^GCA_([0-9]{9})\.([0-9]+)$")
_GCF = re.compile(r"^GCF_([0-9]{9})\.([0-9]+)$")
_VERSION = re.compile(r"^P[0-9]+$")
_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


class PanelError(ValueError):
    pass


@dataclass
class Panel:
    version: str
    rows: list
    path: str = ""

    def ids(self):
        return [r["id"] for r in self.rows]

    def get(self, assembly_id):
        for r in self.rows:
            if r["id"] == assembly_id:
                return r
        raise KeyError(assembly_id)

    def reference(self):
        return [r for r in self.rows if "reference" in r["role"].split(";")][0]


def read_panel(path):
    """Read a panel TSV. Raises PanelError if the header or row shape is wrong."""
    with open(path, newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        try:
            header = next(reader)
        except StopIteration:
            raise PanelError("%s is empty" % path)
        if header != COLUMNS:
            raise PanelError("%s: unexpected columns.\n  found:    %s\n  expected: %s"
                             % (path, header, COLUMNS))
        rows = []
        for n, rec in enumerate(reader, start=2):
            if not rec or all(c == "" for c in rec):
                continue
            if len(rec) != len(COLUMNS):
                raise PanelError("%s line %d: %d fields, expected %d" % (path, n, len(rec), len(COLUMNS)))
            rows.append(dict(zip(COLUMNS, [c.strip() for c in rec])))
    if not rows:
        raise PanelError("%s has no assemblies" % path)
    versions = sorted(set(r["panel_version"] for r in rows))
    if len(versions) != 1:
        raise PanelError("%s mixes panel versions: %s" % (path, versions))
    return Panel(versions[0], rows, str(path))


def validate_panel(panel, min_n50=MIN_N50_MB, reference_accession=REFERENCE_ACCESSION):
    """Return (errors, warnings), both lists of strings. No errors = valid."""
    errors, warnings = [], []
    rows = panel.rows
    if not _VERSION.match(panel.version):
        errors.append("panel_version %r should look like P1" % panel.version)

    seen_id, seen_acc, species_code = {}, {}, {}
    for r in rows:
        i = r["id"]
        for f in ("id", "species", "code", "accession_genbank", "level", "haplotype_status", "sex"):
            if not r[f]:
                errors.append("%s: field %s is empty" % (i or "?", f))
        if i in seen_id:
            errors.append("duplicate id %s" % i)
        seen_id[i] = True
        if r["code"] and not i.startswith(r["code"] + "_"):
            errors.append("%s: id should start with its code %s_" % (i, r["code"]))
        if r["species"] and species_code.setdefault(r["species"], r["code"]) != r["code"]:
            errors.append("%s: species %s has two codes (%s, %s)"
                          % (i, r["species"], species_code[r["species"]], r["code"]))

        gb, rs = r["accession_genbank"], r["accession_refseq"]
        m = _GCA.match(gb)
        if not m:
            errors.append("%s: accession_genbank %r is not GCA_#########.#" % (i, gb))
        if rs:
            m2 = _GCF.match(rs)
            if not m2:
                errors.append("%s: accession_refseq %r is not GCF_#########.#" % (i, rs))
            elif m and m.group(1) != m2.group(1):
                warnings.append("%s: GenBank %s and RefSeq %s have different numbers" % (i, gb, rs))
        for acc in (gb, rs):
            if acc:
                if acc in seen_acc:
                    errors.append("%s: accession %s also used by %s" % (i, acc, seen_acc[acc]))
                seen_acc[acc] = i

        if r["annotated"] not in ("yes", "no"):
            errors.append("%s: annotated must be yes or no, got %r" % (i, r["annotated"]))
        elif (r["annotated"] == "yes") != bool(rs):
            errors.append("%s: annotated=%s but accession_refseq is %s"
                          % (i, r["annotated"], "set" if rs else "empty"))
        if r["sex"] not in SEXES:
            errors.append("%s: sex %r not in %s" % (i, r["sex"], sorted(SEXES)))
        if r["haplotype_status"] not in HAPLOTYPE_STATUS:
            errors.append("%s: haplotype_status %r not in %s" % (i, r["haplotype_status"], sorted(HAPLOTYPE_STATUS)))
        if not _DATE.match(r["released"]):
            errors.append("%s: released %r is not YYYY-MM-DD" % (i, r["released"]))
        try:
            n50 = float(r["contig_N50_Mb"])
            if n50 < min_n50:
                errors.append("%s: contig N50 %.2f Mb is below the selection rule (%.0f Mb)" % (i, n50, min_n50))
        except ValueError:
            errors.append("%s: contig_N50_Mb %r is not a number" % (i, r["contig_N50_Mb"]))

    refs = [r for r in rows if "reference" in r["role"].split(";")]
    if len(refs) != 1:
        errors.append("exactly one assembly must have role 'reference', found %d" % len(refs))
    elif refs[0]["accession_refseq"] != reference_accession:
        errors.append("reference %s has RefSeq %r, expected %s"
                      % (refs[0]["id"], refs[0]["accession_refseq"], reference_accession))
    return errors, warnings
