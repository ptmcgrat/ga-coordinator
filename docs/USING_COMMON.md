# Using the coordinator's code from another project

For the students and assistants of the other projects (Repeats, Alignment, ...). Everything here is in the
coordinator repository, `ga-coordinator` (note the hyphen), cloned at `~/GenomeAlignments/ga-coordinator`
on the laptop and on mzebra.

## 1. What is where

```
ga-coordinator/                  the repository
  common/src/ga_common/          the common library: a Python package other projects install
  scripts/                       fetch.py, sync.py, panel_chromosomes.py: run from the repository, not installed
  config/                        paths.yaml, the panel, species_context.tsv, panel_chromosomes_P1.tsv, ...
  docs/                          coordinator_spec.md (the specification), this file, DELIVERY.md
```

One thing, several names: the folder is `common/`, Python imports it as `ga_common`, `pip` calls it `ga-common`,
and the specification calls it "the common library".

`ga_common` (version 0.2.1) holds: `paths` (where data lives), `panel` (the panel reader and validator), `species`
(the ecogroup table), `provenance`, `throttle`, `bgzf`, `seqio` (FASTA and GFF3 helpers) and `rclone`.

## 2. Install (Python 3.9 or newer)

On mzebra the coordinator repository is already cloned, so the simplest install uses it:

```bash
pip install -e ~/GenomeAlignments/ga-coordinator/common
python -c "import ga_common; print(ga_common.__version__)"       # 0.2.1
```

This follows whatever version of the coordinator repository is checked out. To pin a released version instead, install from
the tag (the server authenticates to GitHub with SSH, so the SSH form is the safe one; neither form has been tested against
real GitHub):

```bash
pip install "git+ssh://git@github.com/ptmcgrat/ga-coordinator.git@common-v0.2.1#subdirectory=common"
```

## 3. Tell it where the configuration is

`ga_common` needs the coordinator's `config/` folder (it holds `paths.yaml`). A normal `pip install` does not carry that
folder, so it looks in this order:

1. the environment variable `GA_CONFIG_DIR`, if set (used alone);
2. the `config/` folder of the repository it is running from, or of the directory you are in;
3. the standard location `~/GenomeAlignments/ga-coordinator/config`.

If your repositories are in the standard place you need do nothing. Otherwise:

```bash
export GA_CONFIG_DIR=~/path/to/ga-coordinator/config
export GA_PROFILE=mzebra          # which machine you are on: mzebra or laptop (or one you define in config/local.yaml)
```

`config/local.yaml` (untracked, in the coordinator's `config/` folder; copy `local.example.yaml`) can set the profile and
override any path. Nothing machine-specific is ever committed.

## 4. Examples

```python
from ga_common.paths import Paths
from ga_common import panel, species, throttle

p = Paths.load()                                   # profile from GA_PROFILE or config/local.yaml
fasta = p.local("genome_fasta", assembly_id="MZ_NMK2024a", accession_version="GCA_041146795.1")
gff   = p.local("genome_annotation", assembly_id="MZ_NMK2024a", accession_version="GCA_041146795.1")
dropbox = p.remote("genome_dir", assembly_id="MZ_NMK2024a", accession_version="GCA_041146795.1")

pan = panel.read_panel(str(p.config_dir / "genome_panel_P1.tsv"))
print(pan.version, len(pan.rows), pan.reference()["id"])          # P1 25 MZ_NMK2024a
for r in pan.rows:                                               # every assembly, with its accession version
    where = p.local("genome_fasta", assembly_id=r["id"], accession_version=r["accession_genbank"])

sp = species.read_species_context(str(p.config_dir / "species_context.tsv"))   # ecogroups and expected inversions
```

Rules: **never build a data path by hand**; ask `Paths`. The data folders are keyed by assembly id and accession version
(`Genomes/<assembly_id>/<accession_version>/`), and a version folder is never overwritten.

Throttling: every script takes `--threads` and `--max-jobs`; reuse the same options:

```python
import argparse
ap = argparse.ArgumentParser()
throttle.add_arguments(ap)               # adds --threads and --max-jobs (no limit unless given)
args = ap.parse_args()
th = throttle.from_args(args)            # th.threads, th.max_jobs
```

## 5. The scripts (run from the coordinator repository)

```bash
python ~/GenomeAlignments/ga-coordinator/scripts/sync.py where Genomes/MZ_NMK2024a/GCA_041146795.1
python ~/GenomeAlignments/ga-coordinator/scripts/sync.py push RepeatInformation/versions/RI_v1          # dry run
python ~/GenomeAlignments/ga-coordinator/scripts/sync.py push RepeatInformation/versions/RI_v1 --go
```

`sync.py` is a dry run unless `--go` is given and never overwrites (rclone `--immutable`). `fetch.py` is the coordinator's
download tool and is not for other projects.

## 6. What the library does not have yet

- **Layout and path kinds for other projects' outputs.** `ga_common.paths` knows `Genomes/` and `RepeatInformation/` only.
  A project that needs a new folder proposes it with the owner and sends the coordinator a blocking item; the coordinator
  then adds the paths (and the version-folder protection in `sync.py`).
- **Readers and validators for the contract formats** (PAF, GFA, repeat annotation, VCF, ...): they come after the owning project
  has agreed the fields.
- **Coordinate-frame conversions** (reference, assembly-native, reverse-stored assemblies).

## 7. Conventions

- Reference: *M. zebra* GCF_041146795.1 (`MZ_NMK2024a`); results are reported in its coordinates.
- 1-based, inclusive in TSV and VCF; 0-based, half-open in BED and PAF.
- Sequence names are exactly as NCBI delivered them (RefSeq `NC_...` for the 8 annotated assemblies, GenBank otherwise); NCBI's
  chromosome labels are the submitters', in two styles (`LG2` or `2`). See `config/panel_chromosomes_P1.tsv` and the specification.
- One person works on a repository at a time; code moves through GitHub; the server account is shared.

## 8. Check that it works

```bash
python - <<'PY'
from ga_common.paths import Paths
p = Paths.load()
print(p.profile_name, p.data_root, p.remote_root)
PY
```

This prints the profile, the local data root (`~/Temp/GenomeAlignments` on mzebra) and the Dropbox location. If it says
`config/paths.yaml not found`, set `GA_CONFIG_DIR` as in section 3.
