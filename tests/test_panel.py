import tempfile
import unittest
from collections import Counter
from pathlib import Path

import support
from ga_common import panel as gp

P1 = support.CONFIG_DIR / "genome_panel_P1.tsv"


def mutate(fn):
    lines = P1.read_text().splitlines()
    header, rows = lines[0].split("\t"), [l.split("\t") for l in lines[1:]]
    fn(header, rows)
    d = tempfile.mkdtemp()
    f = Path(d) / "p.tsv"
    f.write_text("\n".join("\t".join(r) for r in [header] + rows) + "\n")
    return gp.read_panel(f)


def col(name):
    return gp.COLUMNS.index(name)


class PanelTest(unittest.TestCase):
    def test_p1_is_valid_and_matches_spec(self):
        p = gp.read_panel(P1)
        errors, warnings = gp.validate_panel(p)
        self.assertEqual((errors, warnings), ([], []))
        self.assertEqual(p.version, "P1")
        self.assertEqual(len(p.rows), 25)
        self.assertEqual(dict(Counter(r["code"] for r in p.rows)),
                         {"MZ": 6, "AC": 3, "CV": 3, "DT": 3, "MC": 3, "RC": 2, "YH": 3, "AS": 2})
        self.assertEqual(p.reference()["id"], "MZ_NMK2024a")
        self.assertEqual(p.reference()["accession_refseq"], "GCF_041146795.1")
        self.assertEqual(sum(1 for r in p.rows if r["annotated"] == "yes"), 8)

    def test_duplicate_id(self):
        p = mutate(lambda h, rows: rows[1].__setitem__(col("id"), rows[0][col("id")]))
        self.assertTrue(any("duplicate id" in e for e in gp.validate_panel(p)[0]))

    def test_bad_accession(self):
        p = mutate(lambda h, rows: rows[1].__setitem__(col("accession_genbank"), "GCA_12.1"))
        self.assertTrue(any("not GCA" in e for e in gp.validate_panel(p)[0]))

    def test_annotated_needs_refseq(self):
        p = mutate(lambda h, rows: rows[1].__setitem__(col("annotated"), "yes"))
        self.assertTrue(any("annotated=yes" in e for e in gp.validate_panel(p)[0]))

    def test_n50_rule(self):
        p = mutate(lambda h, rows: rows[1].__setitem__(col("contig_N50_Mb"), "12.5"))
        self.assertTrue(any("below the selection rule" in e for e in gp.validate_panel(p)[0]))

    def test_one_reference(self):
        p = mutate(lambda h, rows: rows[1].__setitem__(col("role"), "reference;ancestral"))
        self.assertTrue(any("exactly one" in e for e in gp.validate_panel(p)[0]))

    def test_id_prefix_and_sex(self):
        p = mutate(lambda h, rows: (rows[2].__setitem__(col("id"), "XX_bad"), rows[3].__setitem__(col("sex"), "?")))
        errs = gp.validate_panel(p)[0]
        self.assertTrue(any("should start with its code" in e for e in errs))
        self.assertTrue(any("sex" in e for e in errs))

    def test_shape_errors(self):
        d = Path(tempfile.mkdtemp())
        (d / "a.tsv").write_text("wrong\theader\n1\t2\n")
        with self.assertRaises(gp.PanelError):
            gp.read_panel(d / "a.tsv")
        lines = P1.read_text().splitlines()
        (d / "b.tsv").write_text("\n".join([lines[0], lines[1] + "\textra"]) + "\n")
        with self.assertRaises(gp.PanelError):
            gp.read_panel(d / "b.tsv")


if __name__ == "__main__":
    unittest.main()
