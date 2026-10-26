import os
import unittest

import support
import sync


class SyncTest(unittest.TestCase):
    def setUp(self):
        self.sb = support.Sandbox()
        self.out = []

    def tearDown(self):
        self.sb.close()

    def run_sync(self, *argv):
        self.out = []
        return sync.main(list(argv), out=self.out.append, paths=self.sb.paths)

    def text(self):
        return "\n".join(self.out)

    def make_local_version(self):
        d = self.sb.data_root / "Genomes/MZ_MZ4f/GCA_057381975.1"
        d.mkdir(parents=True)
        (d / "genome.fna.gz").write_bytes(b"data")
        (d / "provenance.json").write_text("{}")
        return d

    def test_where(self):
        self.assertEqual(self.run_sync("where", "Genomes/MZ_MZ4f/GCA_057381975.1"), 0)
        t = self.text()
        self.assertIn(str(self.sb.data_root / "Genomes/MZ_MZ4f/GCA_057381975.1"), t)
        self.assertIn("ptm_dropbox:/CoS/BioSci/BioSci-McGrath/Apps/GenomeAlignments/Genomes/MZ_MZ4f/GCA_057381975.1", t)
        self.assertIn("version folder: Genomes/MZ_MZ4f/GCA_057381975.1", t)

    def test_push_is_dry_run_by_default(self):
        self.make_local_version()
        self.assertEqual(self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1"), 0)
        self.assertIn("DRY RUN", self.text())
        copy = [c for c in self.sb.rclone_calls() if c[0] == "copy"][0]
        self.assertIn("--dry-run", copy)
        self.assertIn("--immutable", copy)
        self.assertFalse(self.sb.remote_data.exists())

    def test_push_go_then_second_push_notes_existing_version(self):
        self.make_local_version()
        rel = "Genomes/MZ_MZ4f/GCA_057381975.1"
        self.assertEqual(self.run_sync("push", rel, "--go"), 0)
        self.assertTrue((self.sb.remote_data / rel / "genome.fna.gz").is_file())
        self.assertEqual(self.run_sync("push", rel, "--go"), 0)
        self.assertIn("already exists at the destination", self.text())
        # a changed file is refused (the fake rclone behaves like --immutable)
        (self.sb.data_root / rel / "genome.fna.gz").write_bytes(b"changed")
        self.assertEqual(self.run_sync("push", rel, "--go"), 1)
        self.assertIn("immutable", self.text())
        self.assertEqual((self.sb.remote_data / rel / "genome.fna.gz").read_bytes(), b"data")

    def test_pull_go(self):
        rel = "RepeatInformation/versions/RI_v1"
        (self.sb.remote_data / rel).mkdir(parents=True)
        (self.sb.remote_data / rel / "MANIFEST.yaml").write_text("panel_version: P1\n")
        self.assertEqual(self.run_sync("pull", rel), 0)                       # dry run
        self.assertFalse((self.sb.data_root / rel).exists())
        self.assertEqual(self.run_sync("pull", rel, "--go"), 0)
        self.assertTrue((self.sb.data_root / rel / "MANIFEST.yaml").is_file())

    def test_single_file_push_uses_copyto(self):
        d = self.make_local_version()
        self.assertEqual(self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1/provenance.json", "--go"), 0)
        self.assertEqual([c[0] for c in self.sb.rclone_calls() if c[0].startswith("copy")], ["copyto"])

    def test_throttle_flags_forwarded(self):
        self.make_local_version()
        self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1", "--max-jobs", "3", "--threads", "2", "--bwlimit", "5M")
        copy = [c for c in self.sb.rclone_calls() if c[0] == "copy"][0]
        for flag, val in (("--transfers", "3"), ("--checkers", "3"), ("--multi-thread-streams", "2"), ("--bwlimit", "5M")):
            self.assertEqual(copy[copy.index(flag) + 1], val)

    def test_env_throttle(self):
        self.make_local_version()
        os.environ["GA_MAX_JOBS"] = "4"
        self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1")
        copy = [c for c in self.sb.rclone_calls() if c[0] == "copy"][0]
        self.assertEqual(copy[copy.index("--transfers") + 1], "4")

    def test_no_limits_by_default(self):
        self.make_local_version()
        self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1")
        copy = [c for c in self.sb.rclone_calls() if c[0] == "copy"][0]
        for flag in ("--transfers", "--bwlimit", "--multi-thread-streams"):
            self.assertNotIn(flag, copy)

    def test_rejects_escape_and_missing(self):
        for bad in ("../etc", "/abs/path", "a/../../b"):
            self.assertEqual(self.run_sync("push", bad, "--go"), 2, bad)
        self.assertEqual(self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1", "--go"), 2)
        self.assertIn("nothing at", self.text())
        self.assertEqual(self.sb.rclone_calls(), [])           # rclone never ran

    def test_old_rclone_refused(self):
        self.make_local_version()
        os.environ["FAKE_RCLONE_VERSION"] = "1.50.0"
        self.assertEqual(self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1", "--go"), 1)
        self.assertIn("older than the required", self.text())

    def test_scratch_folders_excluded(self):
        self.make_local_version()
        self.run_sync("push", "Genomes/MZ_MZ4f/GCA_057381975.1")
        copy = [c for c in self.sb.rclone_calls() if c[0] == "copy"][0]
        self.assertEqual(copy[copy.index("--exclude") + 1], ".ga_tmp_*/**")


if __name__ == "__main__":
    unittest.main()
