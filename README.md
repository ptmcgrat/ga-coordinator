# ga-coordinator (project 0)

Coordinator of the Lake Malawi cichlid genome structure system: the specification,
the assembly panel, fetching and syncing data, provenance, and the common library.
The authority on all of it is `docs/coordinator_spec.md`.

## What is here (code version in `VERSION`)

| path | what |
|---|---|
| `docs/coordinator_spec.md` | the specification (always replaced whole) |
| `config/genome_panel_P1.tsv` | assembly panel P1 (25 assemblies) |
| `config/species_context.tsv` | ecogroup and expected inversion state per species (literature expectations, not results) |
| `config/supplementary_sequences.tsv` | sequences not on NCBI (the YH LG10 Y haplotig) |
| `config/paths.yaml` | machine profiles (`mzebra`, `laptop`) and the Dropbox location |
| `config/local.example.yaml` | copy to `config/local.yaml` (untracked) to choose a profile or override paths |
| `common/` | package `ga_common` 0.2.0: `paths`, `panel`, `species`, `provenance`, `throttle`, `bgzf`, `seqio`, `rclone` |
| `scripts/fetch.py` | download assemblies by accession (NCBI Datasets) and write provenance |
| `scripts/sync.py` | move data between the data root and Dropbox (rclone) |
| `tests/` | `python -m unittest discover -s tests` |
| `docs/DELIVERY.md` | how code zips are installed (laptop, GitHub, server) |

## Where data lives

The **data root** is Dropbox `Apps/GenomeAlignments`, mirrored on mzebra at
`~/Temp/GenomeAlignments` (anything under Dropbox `Apps/` maps to `~/Temp/`).
Repositories are somewhere else: `~/GenomeAlignments/<repo>`, outside Dropbox.

```
<data root>/Genomes/<assembly_id>/<accession_version>/{genome.fna.gz, annotation.gff3.gz,
                                                       sequence_report.jsonl, provenance.json}
<data root>/RepeatInformation/versions/RI_vN/{MANIFEST.yaml, library/, masked/<assembly_id>/}
```

Never build these paths by hand. Ask `ga_common.paths`:

```python
from ga_common.paths import Paths
p = Paths.load()            # profile from GA_PROFILE or config/local.yaml
p.local("genome_fasta", assembly_id="MZ_MZ4f", accession_version="GCA_057381975.1")
p.remote("repeat_manifest", version="RI_v1")
```

## Setup (server)

```bash
cd ~/GenomeAlignments/ga-coordinator
conda env create -f environment.yml && conda activate ga-coord
pip install -e common
cp config/local.example.yaml config/local.yaml      # profile: mzebra
python -m unittest discover -s tests
```

## Use

Everything is a **dry run unless `--go`** is given.

```bash
python scripts/fetch.py panel --ids MZ_MZ4f            # plan only
python scripts/fetch.py panel --ids MZ_MZ4f --go       # download, check, publish
python scripts/fetch.py panel --all --go --max-jobs 2 --threads 8
python scripts/fetch.py supplementary --go             # the YH Y haplotig, from Dropbox

python scripts/sync.py where Genomes/MZ_MZ4f/GCA_057381975.1
python scripts/sync.py push  Genomes/MZ_MZ4f/GCA_057381975.1           # dry run
python scripts/sync.py push  Genomes/MZ_MZ4f/GCA_057381975.1 --go
python scripts/sync.py pull  RepeatInformation/versions/RI_v1 --go
```

**Throttling.** Nothing is limited unless asked: `--threads N` (`GA_MAX_THREADS`),
`--max-jobs N` (`GA_MAX_JOBS`), and for transfers `--bwlimit 20M` (`GA_BWLIMIT`).
Fetch downloads one assembly at a time unless `--max-jobs` is raised.

**Safety.** A fetched folder is built in a scratch folder and moved into place only
after every check passed. Existing folders and files are never overwritten or deleted:
fetch skips what is already there, and sync uses `rclone copy --immutable`.

## Rules for working here

- One person works on a repository at a time (the server account is shared).
- Everything produced is committed at once; GitHub is the backup.
- No machine-specific paths in committed files: use `config/local.yaml`.
- Python 3.9 is the minimum for `common/`.
