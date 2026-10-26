"""Reader and validator for config/species_context.tsv: ecogroup and expected
inversion state per species code (spec section 4b).

The inversion columns are LITERATURE EXPECTATIONS (Kumar 2025, Blumer 2025,
Malinsky 2018), not results. Project 2b's registered arrangement table holds results.
"""

from __future__ import annotations

import csv

COLUMNS = ["species_code", "species", "ecogroup", "subradiation", "group_source",
           "inv_LG2", "inv_LG9", "inv_LG10", "inv_LG11", "inv_LG13", "inv_LG20", "notes"]
INV_COLUMNS = [c for c in COLUMNS if c.startswith("inv_")]

# ecogroup -> subradiation (Malinsky 2018; Blumer 2025; Kumar 2025)
ECOGROUPS = {
    "mbuna": "mbuna",
    "generalist": "ancestral_generalist",
    "rhamphochromis": "pelagic",
    "diplotaxodon": "pelagic",
    "utaka": "benthic",
    "shallow_benthic": "benthic",
    "deep_benthic": "benthic",
}
INV_STATES = {"ancestral", "inverted", "left_arm_only", "variable", "unknown"}


class SpeciesError(ValueError):
    pass


def read_species_context(path):
    with open(path, newline="") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader, None)
        if header != COLUMNS:
            raise SpeciesError("%s: unexpected columns %s" % (path, header))
        rows = []
        for n, rec in enumerate(reader, start=2):
            if not rec or all(c == "" for c in rec):
                continue
            if len(rec) != len(COLUMNS):
                raise SpeciesError("%s line %d: %d fields, expected %d" % (path, n, len(rec), len(COLUMNS)))
            rows.append(dict(zip(COLUMNS, [c.strip() for c in rec])))
    if not rows:
        raise SpeciesError("%s has no rows" % path)
    return rows


def validate_species_context(rows, panel=None):
    """Return (errors, warnings). With a Panel, every panel code must have a row."""
    errors, warnings, seen = [], [], set()
    for r in rows:
        c = r["species_code"]
        if not c:
            errors.append("a row has no species_code")
        if c in seen:
            errors.append("duplicate species_code %s" % c)
        seen.add(c)
        eg = r["ecogroup"]
        if eg not in ECOGROUPS:
            errors.append("%s: ecogroup %r not in %s" % (c, eg, sorted(ECOGROUPS)))
        elif r["subradiation"] != ECOGROUPS[eg]:
            errors.append("%s: ecogroup %s belongs to subradiation %s, not %r"
                          % (c, eg, ECOGROUPS[eg], r["subradiation"]))
        for col in INV_COLUMNS:
            if r[col] not in INV_STATES:
                errors.append("%s: %s=%r not in %s" % (c, col, r[col], sorted(INV_STATES)))
        if not r["group_source"]:
            errors.append("%s: group_source is empty" % c)
    if panel is not None:
        by = {r["species_code"]: r for r in rows}
        for code in sorted(set(p["code"] for p in panel.rows)):
            if code not in by:
                errors.append("panel code %s has no row" % code)
        for p in panel.rows:
            r = by.get(p["code"])
            if r and r["species"] != p["species"]:
                errors.append("%s: species %r differs from the panel's %r" % (p["code"], r["species"], p["species"]))
        for code in sorted(set(by) - set(p["code"] for p in panel.rows)):
            warnings.append("species_code %s is not in panel %s" % (code, panel.version))
    return errors, warnings
