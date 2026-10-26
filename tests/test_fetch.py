import contextlib
import gzip
import io
import json
import os
import unittest
from pathlib import Path

import support
import fetch
from ga_common import bgzf, provenance, seqio

ACC = "GCA_057381975.1"          # MZ_MZ4f, not annotated
ACC_ANN = "GCA_041146795.1"      # MZ_NMK2024a, annotated (RefSeq GCF_041146795.1)


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.sb = support.Sandbox()

    def tearDown(self):
        self.sb.close()

    def run_fetch(self, *argv, paths=None):
        with contextlib.redirect_stdout(io.StringIO()):          # keep test output quiet
            return fetch.main(list(argv), paths=paths or self.sb.paths)

    def folder(self, aid, acc):
        return self.sb.data_root / "Genomes" / aid / acc

    def test_dry_run_changes_nothing(self):
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f,MZ_NMK2024a"), 0)
        self.assertFalse(self.sb.data_root.exists())
        self.assertEqual(self.sb.datasets_calls(), [])

    def test_fetch_two_assemblies(self):
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f,MZ_NMK2024a", "--go"), 0)
        # unannotated: GenBank accession, no gff3 requested
        plain, ann = self.folder("MZ_MZ4f", ACC), self.folder("MZ_NMK2024a", ACC_ANN)
        self.assertEqual(sorted(p.name for p in plain.iterdir()),
                         ["genome.fna.gz", "provenance.json", "sequence_report.jsonl"])
        self.assertEqual(sorted(p.name for p in ann.iterdir()),
                         ["annotation.gff3.gz", "genome.fna.gz", "provenance.json", "sequence_report.jsonl"])
        calls = {c[c.index("accession") + 1]: c for c in self.sb.datasets_calls() if "accession" in c}
        self.assertEqual(calls[ACC][calls[ACC].index("--include") + 1], "genome,seq-report")
        self.assertEqual(calls["GCF_041146795.1"][calls["GCF_041146795.1"].index("--include") + 1],
                         "genome,gff3,seq-report")
        # the stored genome is BGZF and holds the original sequence
        self.assertTrue(bgzf.is_bgzf(plain / "genome.fna.gz"))
        self.assertEqual(seqio.fasta_lengths(plain / "genome.fna.gz"), [("CM900001.1", 202), ("CM900002.1", 150)])
        self.assertTrue(bgzf.is_bgzf(ann / "annotation.gff3.gz"))
        # provenance
        rec = provenance.read_provenance(plain / "provenance.json")
        self.assertEqual(provenance.validate_provenance(rec), [])
        self.assertEqual((rec["accession_requested"], rec["accession_fetched"]), (ACC, ACC))
        self.assertTrue(all(rec["checks"][k] for k in ("lengths_match_sequence_report", "compressed_readback_matches")))
        self.assertGreater(rec["checks"]["ncbi_md5sum_files_verified"], 0)
        genome = [f for f in rec["files"] if f["name"] == "genome.fna.gz"][0]
        self.assertEqual(genome["sha256"], provenance.sha256_file(plain / "genome.fna.gz"))
        self.assertEqual(genome["sha256_uncompressed"], genome["original_sha256"])
        self.assertEqual([(s["name"], s["length"], s["ncbi_length"]) for s in rec["sequences"]],
                         [("CM900001.1", 202, 202), ("CM900002.1", 150, 150)])
        rec2 = provenance.read_provenance(ann / "provenance.json")
        self.assertEqual((rec2["accession_requested"], rec2["accession_fetched"]), (ACC_ANN, "GCF_041146795.1"))
        self.assertTrue(rec2["checks"]["gff_regions_match_fasta"])
        # no scratch left behind
        self.assertEqual([p.name for p in plain.parent.iterdir()], [ACC])

    def test_rerun_skips_and_never_touches(self):
        self.run_fetch("panel", "--ids", "MZ_MZ4f", "--go")
        f = self.folder("MZ_MZ4f", ACC) / "provenance.json"
        before = f.read_bytes()
        downloads = lambda: [c for c in self.sb.datasets_calls() if "download" in c]
        n = len(downloads())
        self.assertEqual(n, 1)
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f", "--go"), 0)
        self.assertEqual(f.read_bytes(), before)
        self.assertEqual(len(downloads()), n)                    # nothing downloaded again

    def test_folder_without_provenance_is_not_overwritten(self):
        d = self.folder("MZ_MZ4f", ACC)
        d.mkdir(parents=True)
        (d / "stray.txt").write_text("keep me")
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f", "--go"), 1)
        self.assertEqual((d / "stray.txt").read_text(), "keep me")

    def test_prefer_genbank_for_annotated(self):
        self.run_fetch("panel", "--ids", "MZ_NMK2024a", "--prefer", "genbank", "--go")
        call = [c for c in self.sb.datasets_calls() if "accession" in c][0]
        self.assertEqual(call[call.index("accession") + 1], ACC_ANN)
        self.assertEqual(call[call.index("--include") + 1], "genome,seq-report")

    def test_length_mismatch_blocks_publication(self):
        os.environ["FAKE_DATASETS_MODE"] = "badlen"
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f", "--go"), 1)
        self.assertFalse(self.folder("MZ_MZ4f", ACC).exists())
        self.assertEqual(list((self.sb.data_root / "Genomes" / "MZ_MZ4f").iterdir()), [])   # no scratch

    def test_datasets_failure(self):
        os.environ["FAKE_DATASETS_MODE"] = "fail"
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f", "--go"), 1)
        self.assertFalse(self.folder("MZ_MZ4f", ACC).exists())

    def test_unknown_id_and_no_data_root(self):
        self.assertEqual(self.run_fetch("panel", "--ids", "NOPE"), 2)
        self.assertEqual(self.run_fetch("panel", "--all", paths=self.sb.nodata_paths), 2)

    def test_two_jobs_with_throttle(self):
        self.assertEqual(self.run_fetch("panel", "--ids", "MZ_MZ4f,AC_SAMEA123396441", "--go",
                                        "--max-jobs", "2", "--threads", "2"), 0)
        self.assertTrue((self.folder("AC_SAMEA123396441", "GCA_988222555.1") / "provenance.json").is_file())

    def test_supplementary_copy(self):
        src = self.sb.dropbox / "CoS/BioSci/BioSci-McGrath/Apps/CichlidSequencingData/2026_Nikesh/Chromosome10s"
        src.mkdir(parents=True)
        original = b">h2tg000014l len=100\n" + b"ACGT" * 25 + b"\n"
        (src / "YH_Y.fasta").write_bytes(original)
        self.assertEqual(self.run_fetch("supplementary"), 0)               # dry run
        self.assertFalse(self.sb.data_root.exists())
        self.assertEqual(self.run_fetch("supplementary", "--go"), 0)
        d = self.folder("YH_LG10Y", "h2tg000014l")
        self.assertEqual(gzip.decompress((d / "genome.fna.gz").read_bytes()), original)   # unchanged
        self.assertTrue(bgzf.is_bgzf(d / "genome.fna.gz"))
        rec = provenance.read_provenance(d / "provenance.json")
        self.assertEqual(rec["kind"], "supplementary")
        self.assertTrue(rec["checks"]["expected_name_found"])
        self.assertEqual(rec["sequences"], [{"name": "h2tg000014l", "length": 100}])
        self.assertEqual(rec["files"][0]["original_name"], "YH_Y.fasta")
        self.assertIn("Apps/CichlidSequencingData/2026_Nikesh/Chromosome10s/YH_Y.fasta", rec["source"]["path"])
        self.assertEqual(sorted(p.name for p in d.iterdir()), ["genome.fna.gz", "provenance.json"])
        copyto = [c for c in self.sb.rclone_calls() if c[0] == "copyto"][0]
        self.assertNotIn("--exclude", copyto)
        self.assertIn("--immutable", copyto)
        self.assertEqual(self.run_fetch("supplementary", "--go"), 0)       # rerun: skipped

    def test_supplementary_missing_source(self):
        self.assertEqual(self.run_fetch("supplementary", "--go"), 1)
        self.assertFalse(self.folder("YH_LG10Y", "h2tg000014l").exists())


if __name__ == "__main__":
    unittest.main()
