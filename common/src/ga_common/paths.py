"""The data layout, defined in one place.

Nothing else builds a data path. Ask for an item by kind and keys:

    p = Paths.load()                                   # profile from GA_PROFILE / config
    p.local("genome_fasta", assembly_id="MZ_MZ4f", accession_version="GCA_057381975.1")
    p.remote("repeat_manifest", version="RI_v1")
    p.rel("genome_dir", assembly_id=..., accession_version=...)   # path under the data root

Layout under the data root (Dropbox Apps/GenomeAlignments, mirrored at
~/Temp/GenomeAlignments on mzebra):

    Genomes/<assembly_id>/<accession_version>/{genome.fna.gz, annotation.gff3.gz,
                                               sequence_report.jsonl, provenance.json}
    RepeatInformation/versions/<RI_vN>/{MANIFEST.yaml, library/, masked/<assembly_id>/}

Version folders are never overwritten (see version_root).
"""

from __future__ import annotations

import os
import re
from pathlib import Path, PurePosixPath

import yaml

PROFILE_ENV = "GA_PROFILE"
CONFIG_ENV = "GA_CONFIG_DIR"

_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_RI_VERSION = re.compile(r"^RI_v[0-9]+$")

# kind -> (relative path template, required keys)
KINDS = {
    "genome_dir": ("Genomes/{assembly_id}/{accession_version}",
                   ("assembly_id", "accession_version")),
    "genome_fasta": ("Genomes/{assembly_id}/{accession_version}/genome.fna.gz",
                     ("assembly_id", "accession_version")),
    "genome_annotation": ("Genomes/{assembly_id}/{accession_version}/annotation.gff3.gz",
                          ("assembly_id", "accession_version")),
    "genome_sequence_report": ("Genomes/{assembly_id}/{accession_version}/sequence_report.jsonl",
                               ("assembly_id", "accession_version")),
    "genome_provenance": ("Genomes/{assembly_id}/{accession_version}/provenance.json",
                          ("assembly_id", "accession_version")),
    "repeat_version_dir": ("RepeatInformation/versions/{version}", ("version",)),
    "repeat_manifest": ("RepeatInformation/versions/{version}/MANIFEST.yaml", ("version",)),
    "repeat_library_dir": ("RepeatInformation/versions/{version}/library", ("version",)),
    "repeat_masked_dir": ("RepeatInformation/versions/{version}/masked/{assembly_id}",
                          ("version", "assembly_id")),
}


class PathsError(RuntimeError):
    pass


def check_segment(value, what="name"):
    if not isinstance(value, str) or not _SEGMENT.match(value) or value in (".", ".."):
        raise PathsError("invalid %s %r (letters, digits, '.', '_', '-' only)" % (what, value))
    return value


def clean_relpath(rel):
    """Validate a path relative to the data root; return it as a PurePosixPath."""
    if not isinstance(rel, str) or not rel.strip():
        raise PathsError("empty path")
    if rel.startswith("/") or "\\" in rel or rel.startswith("~"):
        raise PathsError("path must be relative to the data root: %r" % rel)
    parts = [p for p in rel.split("/") if p != ""]
    if not parts:
        raise PathsError("empty path")
    for p in parts:
        check_segment(p, "path segment")
    return PurePosixPath(*parts)


def version_root(rel):
    """The version folder that contains `rel`, or None.

    Version folders are never overwritten:
      Genomes/<assembly_id>/<accession_version>
      RepeatInformation/versions/<RI_vN>
    """
    parts = clean_relpath(str(rel)).parts
    if len(parts) >= 3 and parts[0] == "Genomes":
        return PurePosixPath(*parts[:3])
    if len(parts) >= 3 and parts[0] == "RepeatInformation" and parts[1] == "versions":
        return PurePosixPath(*parts[:3])
    return None


def _deep_merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


DEFAULT_CONFIG_DIR = "~/GenomeAlignments/ga-coordinator/config"     # where the repositories live (spec section 3a)


def find_config_dir(explicit=None, environ=None):
    """Find the coordinator's config folder (the one holding paths.yaml).

    Order: the `explicit` argument; the GA_CONFIG_DIR environment variable (both are used alone,
    with no fallback); then the config folder of the repository this code runs from or the
    current directory sits in; then the standard location ~/GenomeAlignments/ga-coordinator/config.
    A normal `pip install` of ga_common does not carry the config folder along, so projects
    that install it rely on GA_CONFIG_DIR or on the standard location.
    """
    env = os.environ if environ is None else environ
    if explicit:
        cands = [Path(explicit)]
    elif env.get(CONFIG_ENV):
        cands = [Path(env[CONFIG_ENV]).expanduser()]
    else:
        cwd = Path.cwd().resolve()
        cands = [d / "config" for d in [cwd] + list(cwd.parents)]
        here = Path(__file__).resolve()
        cands += [d / "config" for d in here.parents]
        cands.append(Path(os.path.expanduser(DEFAULT_CONFIG_DIR)))
    for c in cands:
        if (c / "paths.yaml").is_file():
            return c
    raise PathsError("config/paths.yaml not found. Set %s to the coordinator repository's config folder "
                     "(standard location: %s)" % (CONFIG_ENV, DEFAULT_CONFIG_DIR))


class Paths:
    def __init__(self, config, profile, config_dir=None):
        self.config = config
        self.profile_name = profile
        self.config_dir = config_dir
        profiles = config.get("profiles") or {}
        if profile not in profiles:
            raise PathsError("unknown profile %r; known: %s" % (profile, ", ".join(sorted(profiles))))
        self.profile = profiles[profile] or {}
        d = config.get("dropbox") or {}
        for key in ("remote", "apps_root", "data_dir"):
            if not d.get(key):
                raise PathsError("paths.yaml: dropbox.%s is missing" % key)
        self.dropbox = d

    # -- loading -----------------------------------------------------------
    @classmethod
    def load(cls, profile=None, config_dir=None, environ=None):
        env = os.environ if environ is None else environ
        cdir = find_config_dir(config_dir, env)
        with open(cdir / "paths.yaml") as fh:
            cfg = yaml.safe_load(fh) or {}
        local = cdir / "local.yaml"
        if local.is_file():
            with open(local) as fh:
                cfg = _deep_merge(cfg, yaml.safe_load(fh) or {})
        chosen = profile or env.get(PROFILE_ENV) or cfg.get("profile")
        if not chosen:
            raise PathsError("no profile chosen: set %s, or `profile:` in config/local.yaml "
                             "(known: %s)" % (PROFILE_ENV, ", ".join(sorted(cfg.get("profiles") or {}))))
        return cls(cfg, chosen, cdir)

    # -- roots -------------------------------------------------------------
    @property
    def repos_root(self):
        r = self.profile.get("repos_root")
        return Path(r).expanduser() if r else None

    @property
    def data_root(self):
        """Local data root, or None if this profile has none."""
        if self.profile.get("data_root"):
            return Path(self.profile["data_root"]).expanduser()
        temp = self.profile.get("temp_root")
        if temp:
            return Path(temp).expanduser() / self.dropbox["data_dir"]
        return None

    @property
    def remote_root(self):
        """rclone path of the data root, e.g. ptm_dropbox:/CoS/.../Apps/GenomeAlignments"""
        apps = "/" + self.dropbox["apps_root"].strip("/")
        return "%s%s/%s" % (self.dropbox["remote"], apps, self.dropbox["data_dir"].strip("/"))

    def apps_remote(self, relative):
        """rclone path of something else under Dropbox Apps/ (e.g. a source to copy from)."""
        apps = "/" + self.dropbox["apps_root"].strip("/")
        rel = clean_relpath(relative)
        return "%s%s/%s" % (self.dropbox["remote"], apps, rel.as_posix())

    # -- items -------------------------------------------------------------
    def rel(self, kind, **keys):
        """Path of an item relative to the data root (POSIX string)."""
        if kind not in KINDS:
            raise PathsError("unknown kind %r; known: %s" % (kind, ", ".join(sorted(KINDS))))
        template, required = KINDS[kind]
        missing = [k for k in required if k not in keys]
        extra = [k for k in keys if k not in required]
        if missing or extra:
            raise PathsError("kind %r needs keys %s (missing %s, unexpected %s)"
                             % (kind, list(required), missing, extra))
        for k in required:
            check_segment(keys[k], k)
        if "version" in keys and not _RI_VERSION.match(keys["version"]):
            raise PathsError("repeat version must look like RI_v1, got %r" % keys["version"])
        return template.format(**keys)

    def local_from_rel(self, rel):
        root = self.data_root
        if root is None:
            raise PathsError("profile %r has no local data root (set temp_root or data_root)"
                             % self.profile_name)
        return root.joinpath(*clean_relpath(rel).parts)

    def remote_from_rel(self, rel):
        return "%s/%s" % (self.remote_root, clean_relpath(rel).as_posix())

    def local(self, kind, **keys):
        return self.local_from_rel(self.rel(kind, **keys))

    def remote(self, kind, **keys):
        return self.remote_from_rel(self.rel(kind, **keys))
