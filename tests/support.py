"""Test helpers: sys.path setup, a fake rclone, a fake NCBI datasets, a Paths factory."""

import json
import os
import stat
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "common" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ga_common import paths as gpaths  # noqa: E402

CONFIG_DIR = ROOT / "config"

FAKE_RCLONE = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Stand-in for rclone: remote 'ptm_dropbox:/x' is the folder $FAKE_DROPBOX/x."""
    import json, os, shutil, sys
    args = sys.argv[1:]
    with open(os.environ["FAKE_RCLONE_LOG"], "a") as fh:
        fh.write(json.dumps(args) + "\\n")
    def real(p):
        return os.path.join(os.environ["FAKE_DROPBOX"], p.split(":", 1)[1].lstrip("/")) if p.startswith("ptm_dropbox:") else p
    cmd = args[0] if args else ""
    dry = "--dry-run" in args
    if cmd == "version":
        print("rclone v" + os.environ.get("FAKE_RCLONE_VERSION", "1.57.0-DEV")); sys.exit(0)
    pos = [a for a in args[1:] if not a.startswith("-")]
    # drop values of flags that take one
    skip = {"--transfers", "--checkers", "--multi-thread-streams", "--bwlimit", "--exclude"}
    pos, i = [], 1
    while i < len(args):
        if args[i] in skip: i += 2; continue
        if args[i].startswith("-"): i += 1; continue
        pos.append(args[i]); i += 1
    if cmd == "lsf":
        d = real(pos[0])
        if not os.path.isdir(d):
            sys.stderr.write("directory not found\\n"); sys.exit(3)
        for n in sorted(os.listdir(d)):
            print(n + ("/" if os.path.isdir(os.path.join(d, n)) else ""))
        sys.exit(0)
    if cmd in ("copy", "copyto"):
        src, dst = real(pos[0]), real(pos[1])
        if cmd == "copyto" and "--exclude" in args:      # real rclone 1.57 refuses this
            sys.stderr.write("Can't limit to single files when using filters: " + pos[0] + "\\n"); sys.exit(1)
        if not os.path.exists(src):
            sys.stderr.write("directory not found\\n"); sys.exit(3)
        sys.stderr.write("NOTICE: would copy\\n" if dry else "INFO: copied\\n")
        if dry: sys.exit(0)
        if cmd == "copyto":
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(dst) and open(dst,"rb").read() != open(src,"rb").read():
                sys.stderr.write("ERROR: immutable file modified\\n"); sys.exit(9)
            shutil.copyfile(src, dst); sys.exit(0)
        for r, _, fs in os.walk(src):
            for f in fs:
                s = os.path.join(r, f); d = os.path.join(dst, os.path.relpath(s, src))
                os.makedirs(os.path.dirname(d), exist_ok=True)
                if os.path.exists(d) and open(d,"rb").read() != open(s,"rb").read():
                    sys.stderr.write("ERROR: immutable file modified\\n"); sys.exit(9)
                shutil.copyfile(s, d)
        sys.exit(0)
    sys.stderr.write("fake rclone: unsupported " + cmd + "\\n"); sys.exit(2)
''')

FAKE_DATASETS = textwrap.dedent('''\
    #!/usr/bin/env python3
    """Stand-in for NCBI datasets: writes a zip laid out like a real genome download."""
    import hashlib, json, os, sys, zipfile
    a = sys.argv[1:]
    with open(os.environ["FAKE_DATASETS_LOG"], "a") as fh:
        fh.write(json.dumps(a) + "\\n")
    if a == ["--version"]:
        print("datasets version: 18.99.0"); sys.exit(0)
    mode = os.environ.get("FAKE_DATASETS_MODE", "ok")
    if mode == "fail":
        sys.stderr.write("Error: assembly not found\\n"); sys.exit(1)
    acc = a[a.index("accession") + 1]
    include = a[a.index("--include") + 1].split(",")
    out = a[a.index("--filename") + 1]
    refseq = acc.startswith("GCF_")
    names = ["NC_900001.1", "NC_900002.1"] if refseq else ["CM900001.1", "CM900002.1"]
    seqs = {names[0]: "ACGT" * 50 + "NN", names[1]: "TTGCA" * 30}
    fna = "".join(">%s Fake chromosome\\n%s\\n" % (n, s) for n, s in seqs.items())
    rows = []
    for n, s in seqs.items():
        L = len(s) + (5 if (mode == "badlen" and n == names[0]) else 0)
        rows.append({("refseqAccession" if refseq else "genbankAccession"): n, "length": L,
                     "chrName": "LG" + n[-3], "assignedMoleculeLocationType": "Chromosome", "role": "assembled-molecule"})
    base = "ncbi_dataset/data/%s/" % acc
    files = {base + acc + "_FakeAsm_genomic.fna": fna,
             base + "sequence_report.jsonl": "".join(json.dumps(r) + "\\n" for r in rows),
             "ncbi_dataset/data/assembly_data_report.jsonl": "{}\\n", "README.md": "fake\\n"}
    if "gff3" in include:
        files[base + "genomic.gff"] = "##gff-version 3\\n" + "".join(
            "##sequence-region %s 1 %d\\n" % (n, len(s)) for n, s in seqs.items()) + \\
            "%s\\tRefSeq\\tgene\\t1\\t10\\t.\\t+\\t.\\tID=g1\\n" % names[0]
    md5 = "".join("%s  %s\\n" % (hashlib.md5(v.encode()).hexdigest(), k) for k, v in files.items() if k.startswith(base))
    with zipfile.ZipFile(out, "w") as z:
        for k, v in files.items():
            z.writestr(k, v)
        z.writestr("md5sum.txt", md5)
''')


def make_tool(directory, name, source):
    p = Path(directory) / name
    p.write_text(source)
    p.chmod(p.stat().st_mode | stat.S_IXUSR)
    return p


class Sandbox:
    """A temp folder with fake rclone/datasets, a fake Dropbox, and a Paths for profile 'test'."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.dropbox = self.root / "dropbox"
        self.dropbox.mkdir()
        self.rclone_log = self.root / "rclone.log"
        self.datasets_log = self.root / "datasets.log"
        make_tool(self.bin, "rclone", FAKE_RCLONE)
        make_tool(self.bin, "datasets", FAKE_DATASETS)
        self.saved = dict(os.environ)
        os.environ.update({
            "GA_RCLONE": str(self.bin / "rclone"), "GA_DATASETS": str(self.bin / "datasets"),
            "FAKE_DROPBOX": str(self.dropbox), "FAKE_RCLONE_LOG": str(self.rclone_log),
            "FAKE_DATASETS_LOG": str(self.datasets_log),
        })
        for k in ("FAKE_DATASETS_MODE", "FAKE_RCLONE_VERSION", "GA_MAX_THREADS", "GA_MAX_JOBS",
                  "GA_BWLIMIT", "GA_PROFILE"):
            os.environ.pop(k, None)
        self.data_root = self.root / "data" / "GenomeAlignments"
        cfg = {"dropbox": {"remote": "ptm_dropbox:", "apps_root": "/CoS/BioSci/BioSci-McGrath/Apps",
                           "data_dir": "GenomeAlignments"},
               "profiles": {"test": {"data_root": str(self.data_root)},
                            "nodata": {"repos_root": "~/x"}}}
        self.paths = gpaths.Paths(cfg, "test", CONFIG_DIR)
        self.nodata_paths = gpaths.Paths(cfg, "nodata", CONFIG_DIR)
        # remote data root inside the fake dropbox
        self.remote_data = self.dropbox / "CoS/BioSci/BioSci-McGrath/Apps/GenomeAlignments"

    def rclone_calls(self):
        if not self.rclone_log.exists():
            return []
        return [json.loads(l) for l in self.rclone_log.read_text().splitlines()]

    def datasets_calls(self):
        if not self.datasets_log.exists():
            return []
        return [json.loads(l) for l in self.datasets_log.read_text().splitlines()]

    def close(self):
        os.environ.clear()
        os.environ.update(self.saved)
        self.tmp.cleanup()
