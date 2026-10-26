import os
import tempfile
import unittest
from pathlib import Path

import support
from ga_common import paths as gp


class PathsTest(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.saved = dict(os.environ)
        os.environ["HOME"] = self.home.name
        os.environ.pop("GA_PROFILE", None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.saved)
        self.home.cleanup()

    def load(self, profile):
        return gp.Paths.load(profile=profile, config_dir=support.CONFIG_DIR)

    def test_mzebra_maps_apps_to_temp(self):
        p = self.load("mzebra")
        self.assertEqual(p.data_root, Path(self.home.name) / "Temp" / "GenomeAlignments")
        self.assertEqual(p.repos_root, Path(self.home.name) / "GenomeAlignments")

    def test_remote_root_is_exact(self):
        self.assertEqual(self.load("mzebra").remote_root,
                         "ptm_dropbox:/CoS/BioSci/BioSci-McGrath/Apps/GenomeAlignments")

    def test_laptop_has_no_data_root(self):
        p = self.load("laptop")
        self.assertIsNone(p.data_root)
        with self.assertRaises(gp.PathsError):
            p.local("genome_dir", assembly_id="MZ_MZ4f", accession_version="GCA_057381975.1")

    def test_kinds(self):
        p = self.load("mzebra")
        k = dict(assembly_id="MZ_MZ4f", accession_version="GCA_057381975.1")
        self.assertEqual(p.rel("genome_fasta", **k), "Genomes/MZ_MZ4f/GCA_057381975.1/genome.fna.gz")
        self.assertEqual(p.rel("genome_annotation", **k), "Genomes/MZ_MZ4f/GCA_057381975.1/annotation.gff3.gz")
        self.assertEqual(p.rel("genome_provenance", **k), "Genomes/MZ_MZ4f/GCA_057381975.1/provenance.json")
        self.assertEqual(p.rel("repeat_manifest", version="RI_v1"), "RepeatInformation/versions/RI_v1/MANIFEST.yaml")
        self.assertEqual(p.rel("repeat_masked_dir", version="RI_v2", assembly_id="AC_fAstCal68"),
                         "RepeatInformation/versions/RI_v2/masked/AC_fAstCal68")
        self.assertEqual(p.remote("repeat_library_dir", version="RI_v1"),
                         "ptm_dropbox:/CoS/BioSci/BioSci-McGrath/Apps/GenomeAlignments/RepeatInformation/versions/RI_v1/library")
        self.assertTrue(str(p.local("genome_dir", **k)).endswith("Temp/GenomeAlignments/Genomes/MZ_MZ4f/GCA_057381975.1"))

    def test_bad_keys(self):
        p = self.load("mzebra")
        for bad in ("../x", "a/b", "", ".hidden", "a b"):
            with self.assertRaises(gp.PathsError):
                p.rel("genome_dir", assembly_id=bad, accession_version="GCA_1.1")
        with self.assertRaises(gp.PathsError):
            p.rel("genome_dir", assembly_id="MZ_MZ4f")
        with self.assertRaises(gp.PathsError):
            p.rel("repeat_manifest", version="v1")
        with self.assertRaises(gp.PathsError):
            p.rel("nonsense")

    def test_relpath_validation(self):
        for bad in ("/abs", "../up", "a/../b", "~/x", "a\\b", "", "   "):
            with self.assertRaises(gp.PathsError, msg=bad):
                gp.clean_relpath(bad)
        self.assertEqual(str(gp.clean_relpath("Genomes//MZ_MZ4f/")), "Genomes/MZ_MZ4f")

    def test_version_root(self):
        v = gp.version_root
        self.assertEqual(str(v("Genomes/MZ_MZ4f/GCA_057381975.1")), "Genomes/MZ_MZ4f/GCA_057381975.1")
        self.assertEqual(str(v("Genomes/MZ_MZ4f/GCA_057381975.1/genome.fna.gz")), "Genomes/MZ_MZ4f/GCA_057381975.1")
        self.assertEqual(str(v("RepeatInformation/versions/RI_v1/masked/X")), "RepeatInformation/versions/RI_v1")
        self.assertIsNone(v("Genomes"))
        self.assertIsNone(v("Genomes/MZ_MZ4f"))
        self.assertIsNone(v("RepeatInformation/versions"))
        self.assertIsNone(v("Other/a/b/c"))

    def test_profile_selection_and_local_override(self):
        cfg = Path(self.home.name) / "config"
        cfg.mkdir()
        (cfg / "paths.yaml").write_text((support.CONFIG_DIR / "paths.yaml").read_text())
        with self.assertRaises(gp.PathsError):            # no profile chosen
            gp.Paths.load(config_dir=cfg)
        os.environ["GA_PROFILE"] = "laptop"
        self.assertEqual(gp.Paths.load(config_dir=cfg).profile_name, "laptop")
        os.environ.pop("GA_PROFILE")
        (cfg / "local.yaml").write_text("profile: student\nprofiles:\n  student:\n    temp_root: /scratch/me\n")
        p = gp.Paths.load(config_dir=cfg)
        self.assertEqual(p.profile_name, "student")
        self.assertEqual(p.data_root, Path("/scratch/me/GenomeAlignments"))
        self.assertIn("mzebra", p.config["profiles"])     # base profiles survive the merge
        with self.assertRaises(gp.PathsError):
            gp.Paths.load(profile="nope", config_dir=cfg)

    def test_apps_remote(self):
        p = self.load("mzebra")
        self.assertEqual(p.apps_remote("CichlidSequencingData/x/y.fasta"),
                         "ptm_dropbox:/CoS/BioSci/BioSci-McGrath/Apps/CichlidSequencingData/x/y.fasta")
        with self.assertRaises(gp.PathsError):
            p.apps_remote("../x")


if __name__ == "__main__":
    unittest.main()
