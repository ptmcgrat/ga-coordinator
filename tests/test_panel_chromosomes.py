import io
import json
import re
import unittest
from pathlib import Path

import support
import panel_chromosomes as pc
from ga_common import panel as gpanel

TSV = support.CONFIG_DIR / "panel_chromosomes_P1.tsv"
PANEL = support.CONFIG_DIR / "genome_panel_P1.tsv"
ACC = re.compile(r"^(NC_|NW_|CM|OZ|CP)[0-9]+\.[0-9]+$")


def read_table():
    lines = TSV.read_text().splitlines()
    header = lines[0].split("\t")
    return header, [dict(zip(header, l.split("\t"))) for l in lines[1:]]


class CommittedTable(unittest.TestCase):
    def test_covers_the_panel_in_order_with_valid_accessions(self):
        header, rows = read_table()
        self.assertEqual(header, pc.HEADER)
        pan = gpanel.read_panel(PANEL)
        self.assertEqual([r["assembly_id"] for r in rows], pan.ids())
        for r in rows:
            self.assertEqual(r["panel_version"], "P1")
            self.assertIn(r["label_style"], ("LG", "num"))
            for c in pc.CHROMOSOMES:
                self.assertRegex(r["LG" + c], ACC, "%s LG%s" % (r["assembly_id"], c))
        seen = [r["LG" + c] for r in rows for c in pc.CHROMOSOMES]
        self.assertEqual(len(seen), len(set(seen)))                 # no accession repeated

    def test_annotated_assemblies_use_refseq_names(self):
        _, rows = read_table()
        by = {r["assembly_id"]: r for r in rows}
        pan = gpanel.read_panel(PANEL)
        for p in pan.rows:
            expect_nc = p["annotated"] == "yes"
            self.assertEqual(by[p["id"]]["LG10"].startswith("NC_"), expect_nc, p["id"])

    def test_reference_matches_the_sequence_report_seen_on_mzebra(self):
        ref = [r for r in read_table()[1] if r["assembly_id"] == "MZ_NMK2024a"][0]
        self.assertEqual((ref["LG2"], ref["LG10"], ref["LG13"]), ("NC_135168.1", "NC_135176.1", "NC_135179.1"))


class Generator(unittest.TestCase):
    def setUp(self):
        self.sb = support.Sandbox()

    def tearDown(self):
        self.sb.close()

    def write_prov(self, aid, acc, seqs):
        d = self.sb.data_root / "Genomes" / aid / acc
        d.mkdir(parents=True)
        (d / "provenance.json").write_text(json.dumps({"assembly_id": aid, "sequences": seqs}))

    def test_row_for_both_label_styles_and_problems(self):
        warns = []
        lg = {"sequences": [{"name": "NC_%d.1" % n, "length": 1, "chr_name": "LG%d" % n} for n in (2, 9, 10, 11, 13, 20)]}
        self.assertEqual(pc.row_for("A_x", "P1", lg, warns.append),
                         ["P1", "A_x", "LG", "NC_2.1", "NC_9.1", "NC_10.1", "NC_11.1", "NC_13.1", "NC_20.1"])
        num = {"sequences": [{"name": "OZ%d.1" % n, "length": 1, "chr_name": str(n)} for n in (2, 9, 10, 11, 13)]
               + [{"name": "OZa.1", "length": 1, "chr_name": "20"}, {"name": "OZb.1", "length": 1, "chr_name": "20"}]}
        row = pc.row_for("B_y", "P1", num, warns.append)
        self.assertEqual(row[2], "num")
        self.assertEqual(row[-1], "OZa.1,OZb.1")
        self.assertEqual(len(warns), 1)
        self.assertEqual(pc.row_for("C_z", "P1", {"sequences": []}, warns.append)[3:], ["-"] * 6)

    def test_main_prints_the_table_and_reports_missing_data(self):
        out = io.StringIO()
        self.assertEqual(pc.main(["--panel", "P1"], paths=self.sb.paths, out=out), 2)    # nothing fetched
        pan = gpanel.read_panel(PANEL)
        for r in pan.rows:
            self.write_prov(r["id"], r["accession_genbank"],
                            [{"name": "%s_%d" % (r["id"], n), "length": 1, "chr_name": "LG%d" % n} for n in (2, 9, 10, 11, 13, 20)])
        out = io.StringIO()
        self.assertEqual(pc.main(["--panel", "P1", "--threads", "2"], paths=self.sb.paths, out=out), 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0].split("\t"), pc.HEADER)
        self.assertEqual(len(lines), 26)
        self.assertEqual([l.split("\t")[1] for l in lines[1:]], pan.ids())


if __name__ == "__main__":
    unittest.main()
