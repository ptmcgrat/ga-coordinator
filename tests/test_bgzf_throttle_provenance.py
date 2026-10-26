import gzip
import io
import os
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401
from ga_common import bgzf, provenance, throttle


class BgzfTest(unittest.TestCase):
    def roundtrip(self, data, threads=1):
        d = tempfile.mkdtemp()
        dst = os.path.join(d, "x.gz")
        sha, n_in, n_out = bgzf.compress(io.BytesIO(data), dst, threads=threads)
        return dst, sha, n_in, n_out

    def test_roundtrip_and_format(self):
        data = (b">chr\n" + b"ACGT" * 100000 + b"\n") * 3        # several blocks
        dst, sha, n_in, n_out = self.roundtrip(data)
        self.assertTrue(bgzf.is_bgzf(dst))
        with open(dst, "rb") as fh:
            self.assertEqual(gzip.decompress(fh.read()), data)    # plain gzip tools can read it
        self.assertEqual(n_in, len(data))
        self.assertEqual(n_out, os.path.getsize(dst))
        import hashlib
        self.assertEqual(sha, hashlib.sha256(data).hexdigest())

    def test_threads_give_identical_bytes(self):
        data = os.urandom(300000) + b"A" * 500000
        a = self.roundtrip(data, 1)[0]
        b = self.roundtrip(data, 4)[0]
        self.assertEqual(Path(a).read_bytes(), Path(b).read_bytes())

    def test_empty_and_plain_gzip(self):
        dst = self.roundtrip(b"")[0]
        self.assertTrue(bgzf.is_bgzf(dst))
        self.assertEqual(gzip.decompress(Path(dst).read_bytes()), b"")
        plain = os.path.join(tempfile.mkdtemp(), "p.gz")
        with gzip.open(plain, "wb") as fh:
            fh.write(b"hello")
        self.assertFalse(bgzf.is_bgzf(plain))


class ThrottleTest(unittest.TestCase):
    def test_no_limit_by_default(self):
        t = throttle.Throttle.resolve(environ={})
        self.assertEqual((t.threads, t.max_jobs, t.bwlimit), (None, None, None))
        self.assertEqual(t.job_count(default=3), 3)
        self.assertGreaterEqual(t.thread_count(), 1)

    def test_env_and_cli_precedence(self):
        env = {"GA_MAX_THREADS": "8", "GA_MAX_JOBS": "2", "GA_BWLIMIT": "10M"}
        t = throttle.Throttle.resolve(environ=env)
        self.assertEqual((t.threads, t.max_jobs, t.bwlimit), (8, 2, "10M"))
        t = throttle.Throttle.resolve(threads=3, environ=env)
        self.assertEqual(t.threads, 3)
        self.assertEqual(t.thread_count(default=99), 3)

    def test_invalid(self):
        for bad in ({"GA_MAX_JOBS": "0"}, {"GA_MAX_THREADS": "many"}):
            with self.assertRaises(ValueError):
                throttle.Throttle.resolve(environ=bad)


class ProvenanceTest(unittest.TestCase):
    def rec(self):
        return provenance.new_record(
            "genome", "MZ_MZ4f", "GCA_1.1", "GCA_1.1", {"type": "ncbi-datasets"}, {"datasets": "x"},
            [{"name": "genome.fna.gz", "role": "genome", "bytes": 1, "sha256": "ab"}],
            [{"name": "s", "length": 1}], {"ok": True})

    def test_write_validate_refuse_overwrite(self):
        d = tempfile.mkdtemp()
        path = provenance.write_provenance(d, self.rec())
        self.assertEqual(provenance.read_provenance(path)["assembly_id"], "MZ_MZ4f")
        with self.assertRaises(FileExistsError):
            provenance.write_provenance(d, self.rec())

    def test_invalid_record(self):
        r = self.rec()
        del r["files"]
        self.assertTrue(provenance.validate_provenance(r))
        with self.assertRaises(ValueError):
            provenance.write_provenance(tempfile.mkdtemp(), r)

    def test_checksums(self):
        f = Path(tempfile.mkdtemp()) / "a"
        f.write_bytes(b"abc")
        self.assertEqual(provenance.sha256_file(f),
                         "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertEqual(provenance.md5_file(f), "900150983cd24fb0d6963f7d28e17f72")


if __name__ == "__main__":
    unittest.main()
