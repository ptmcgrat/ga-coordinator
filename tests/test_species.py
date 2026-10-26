import tempfile
import unittest
from pathlib import Path

import support
from ga_common import panel as gpanel
from ga_common import species as sp

TSV = support.CONFIG_DIR / "species_context.tsv"
PANEL = support.CONFIG_DIR / "genome_panel_P1.tsv"


def mutated(fn):
    lines = TSV.read_text().splitlines()
    header, rows = lines[0].split("\t"), [l.split("\t") for l in lines[1:]]
    fn(header, rows)
    f = Path(tempfile.mkdtemp()) / "s.tsv"
    f.write_text("\n".join("\t".join(r) for r in [header] + rows) + "\n")
    return sp.read_species_context(f)


class SpeciesTest(unittest.TestCase):
    def test_real_table_is_valid_and_covers_the_panel(self):
        rows = sp.read_species_context(TSV)
        errors, warnings = sp.validate_species_context(rows, gpanel.read_panel(PANEL))
        self.assertEqual((errors, warnings), ([], []))
        self.assertEqual(len(rows), 8)

    def test_panel_covers_all_seven_ecogroups(self):
        rows = sp.read_species_context(TSV)
        self.assertEqual(set(r["ecogroup"] for r in rows), set(sp.ECOGROUPS))

    def test_owner_assignments(self):
        by = {r["species_code"]: r for r in sp.read_species_context(TSV)}
        self.assertEqual(by["MC"]["ecogroup"], "shallow_benthic")
        self.assertEqual(by["AS"]["ecogroup"], "deep_benthic")
        self.assertEqual(by["YH"]["ecogroup"], "deep_benthic")
        self.assertEqual(by["MZ"]["ecogroup"], "mbuna")
        # reference and ancestor carry no inversions; YH carries all six
        for c in ("MZ", "AC"):
            self.assertTrue(all(by[c][k] == "ancestral" for k in sp.INV_COLUMNS))
        self.assertTrue(all(by["YH"][k] == "inverted" for k in sp.INV_COLUMNS))
        self.assertEqual(by["RC"]["inv_LG20"], "left_arm_only")

    def test_errors(self):
        i = sp.COLUMNS.index
        rows = mutated(lambda h, r: r[0].__setitem__(i("ecogroup"), "swimmers"))
        self.assertTrue(any("ecogroup" in e for e in sp.validate_species_context(rows)[0]))
        rows = mutated(lambda h, r: r[0].__setitem__(i("subradiation"), "pelagic"))
        self.assertTrue(any("belongs to subradiation" in e for e in sp.validate_species_context(rows)[0]))
        rows = mutated(lambda h, r: r[1].__setitem__(i("inv_LG9"), "maybe"))
        self.assertTrue(any("inv_LG9" in e for e in sp.validate_species_context(rows)[0]))
        rows = mutated(lambda h, r: r[1].__setitem__(i("species_code"), r[0][0]))
        self.assertTrue(any("duplicate" in e for e in sp.validate_species_context(rows)[0]))
        rows = mutated(lambda h, r: r.pop())            # drop AS
        self.assertTrue(any("AS has no row" in e for e in
                            sp.validate_species_context(rows, gpanel.read_panel(PANEL))[0]))


if __name__ == "__main__":
    unittest.main()
