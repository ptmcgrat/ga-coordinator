# Coordinator specification

**Project:** 0, Coordinator (controller)
**Document version:** 0.4, 2026-10-26 (0.1: first draft; 0.2: panel versions and releases; 0.3: data organization reopened; downloads by accession; 0.4: lab environment recorded; data organization settled; code delivery convention; first code base)
**Owner:** McGrath lab
**Status:** draft for discussion; not yet in use

This is the single specification document for the coordinator. Everything that
defines the coordinator's job lives here. The working instructions given to the
coordinator stay fixed; this document carries everything that changes, and is
always updated as a whole.

---

## Working instructions (fixed)

1. This document is the authority on the coordinator's job. Read it in full at the
   start of every session.
2. Relay, record and register; do not design other projects' work. Each project
   designs its own work with the owner.
3. All communication between projects passes through the coordinator. Projects
   never contact each other.
4. Accept from projects only blocking items and integration requests.
5. Change this document only by reissuing it whole, with a new version number and a
   dated entry in the decision log.
6. Every registered output names the panel version it was built from; every result
   belongs to a release. Releases, once made, are never changed.

---

## 1. Purpose and scope

The coordinator holds the specification of the whole system for comparing
chromosome structure, variants and their consequences across 25–30 Lake Malawi
cichlid assemblies.

**The coordinator does:**
- define the projects, their roles, and what each consumes and produces;
- own the **assembly panel** and the **sample sheets** (short-read and RNA data);
- download data, record where it lives, and keep provenance and checksums;
- define the **file formats (contracts)** that pass between projects;
- keep the **registry** of every project output and its version, and record which
  versions each project uses;
- version the **panel**, and assemble **releases**: complete, consistent runs of
  the system on one panel version (section 4a);
- relay questions between projects and record the answers;
- maintain the **common library** (parsers, writers and validators for the contract
  formats);
- integrate a project's outputs when the owner decides it is ready.

**The coordinator does not:**
- run analyses, or decide a project's methods;
- review a project's code or intermediate work;
- carry any project's internal details beyond its registered outputs.

---

## 2. Projects

| id | project | job | consumes (registered outputs) | produces |
|---|---|---|---|---|
| 0 | Coordinator | specification, panel, data, contracts, registry, common library | — | panel, sample sheets, fetched data, contracts, registry |
| 1 | Repeats | one shared repeat library; masking of every assembly | assemblies | library; repeat annotation per assembly |
| A | Annotation | gene models in every assembly by liftover (LiftOn from MZ and the annotated assemblies), with orthology | assemblies; NCBI annotations | gene models per assembly; unlifted and partial genes; extra copies |
| 2a | Alignment | pairwise alignments of every assembly to MZ; pangenome graph | assemblies; repeat annotation | PAF per assembly; graph (unclipped) |
| 2b | Structure | centromeres; arrangement of each assembly; inversion breakpoints (located by pairwise alignment, characterized locally, confirmed by reads); assembly-error flags; arrays and rapidly evolving regions; Y10-specific changes | alignments; assemblies; repeats; gene models; long reads | arrangement table; breakpoint tables and analyses; artefact flags; array copy tables |
| 3 | Variant finder | SNVs, indels, transposon insertions, small CNVs and inversions across all assemblies, polarized | graph and alignments; arrangement table; repeats; gene models | multi-assembly VCF; genotyping candidates |
| 4 | Genotyper | genotypes of the variant catalogue in short-read data | variant catalogue; short reads | genotypes per individual; junction genotypes |
| B | Expression interface | ASE SNV panels; summaries of expression and ASE data from the external RNA pipeline; files for future transposon–gene analyses | variants; genotypes; gene models; external expression results | SNV panels; gene-level ASE and expression summaries |
| 5 | Analyzer | interpretation: inverted-haplotype enrichment, lineages, selection tests, insertion effects | all of the above; external datasets | results tables |
| C | Reports | findings pages, figures, browser | results | shareable pages and figures |

---

## 3. How projects work with the coordinator

**Rules**
1. **One document per project.** Each project keeps a single specification
   document (template in section 10). It is always replaced whole, never patched in
   pieces.
2. **All communication through the coordinator.** A question for another project is
   sent to the coordinator, which relays it and records the answer here (section 12).
3. **No micromanaging.** Each project owns one repository and designs its work with
   the owner. Only blocking items come to the coordinator, until the owner decides
   there is enough progress to integrate.
4. **Plan before code.** Each project agrees its plan (outputs, formats, checks)
   with the owner, and records it in its specification document, before writing code.
5. **Code is delivered as numbered zips** and installed as described in section 3a.
   Every project specification carries this convention (section 10, item 9).
6. **Every script takes throttling options** (section 3a).

**What a project sends the coordinator**
- **Blocking item:** a missing input, a format question, or a decision that affects
  another project. Stated as: what is needed, from whom, why it blocks.
- **Integration request** (when the owner decides): the outputs, their contract
  version, their location, and the checks they passed.

**What the coordinator sends a project**
- the registered inputs it may use, with versions and locations;
- answers to its blocking items;
- notice when a registered input it uses gets a new version.

---

## 3a. Lab environment and delivery

Recorded 2026-10-26 from the owner's answers and from output pasted by the owner.
Items marked *(unconfirmed)* were inferred and are not relied on.

**People**
- The owner (the professor) runs Claude in the browser on his laptop, downloads the
  code Claude produces, and syncs it to GitHub. Students work on the projects.
- One person works on one repository at a time. This is the rule that prevents
  conflicts; there is no other protection.

**Machines**

| | laptop (owner) | server |
|---|---|---|
| name | — | `mzebra.ebb.gatech.edu` |
| system | macOS 26.6.1, Apple Silicon (arm64) | Red Hat Enterprise Linux 8.3, kernel 4.18 |
| capacity | — | 96 cores, 503 GiB RAM, shared (several sessions logged in at once), no job scheduler: jobs run directly |
| disk | — | `/home` 7.0 T, about 3.6 T free on 2026-10-26; no quota seen *(unconfirmed)*; whether `/home` is backed up is unknown |
| tools seen | git 2.50.1, Python 3.13.11, rclone at `/usr/local/bin/rclone` | git 2.27.0, rclone v1.57.0-DEV, Python 3.9.18, conda 24.11.3 (channels bioconda, conda-forge, defaults); no docker, singularity or mamba; NCBI reachable |
| account | owner's | `bio-mcgrath-dropbox`, **shared by all students**; home `/home/ad.gatech.edu/bio-mcgrath-dropbox` |
| repositories | `~/GenomeAlignments/<repo>`, outside Dropbox | `~/GenomeAlignments/<repo>` |
| data | none (data lives on the server and in Dropbox) | `~/Temp/GenomeAlignments` (the data root, section 5) |

Students use a similar method on their own laptops, in a location of their choosing.
Where analyses run is each project's choice; no project may assume the server.

**Where things are kept**
- **Dropbox is the authoritative copy of data.** **GitHub is the authoritative copy of
  code.** Server working copies are regenerable.
- Repositories are kept outside Dropbox on every machine, so Dropbox never syncs
  `.git` folders. Everything produced is committed at once; GitHub is the backup.
- **Rule:** anything under Dropbox `Apps/` is mirrored under `~/Temp/` on mzebra.
  The data root is therefore Dropbox `Apps/GenomeAlignments` and `~/Temp/GenomeAlignments`.
  The repositories (code) are a different place, `~/GenomeAlignments/<repo>`.
- Data moves between server and Dropbox with rclone, through the remote
  `ptm_dropbox:` configured on the server. Paths start `ptm_dropbox:/CoS/BioSci/BioSci-McGrath/Apps/`.
  Dropbox is case-insensitive. The remote's access token is shared by everyone who uses
  the account; this is recorded, not decided here.

**GitHub**
- Account `ptmcgrat`; repositories are reached by SSH (`git@github.com:ptmcgrat/<repo>.git`).
- The server authenticates as `ptmcgrat` with a key in the shared account, so commits
  made on the server appear under that account.
- The server receives code by `git pull`.
- Coordinator repository: `ga-coordinator` *(name assumed; set in the instructions
  of each zip)*.

**Delivery of code (applies to every project the coordinator manages)**
1. Each set of files for a repository is one zip, named `<project>_NNN.zip`, numbered
   per project (`coordinator_001.zip`, `repeats_001.zip`).
2. The zip holds `MANIFEST.txt` (files added, replaced, to delete), `INSTRUCTIONS.md`
   and `files/` (whole files, never patches). The number is also written in the
   repository's `VERSION` file, so the installed number can be checked.
3. On the laptop: `git pull`; unzip the named file into a temporary folder; copy
   `files/` over the repository with `rsync` excluding `.git`, `config/local.yaml` and
   any file committed from the server; remove the files listed under DELETE with
   `git rm`; check `VERSION`; `git status`; commit; push.
4. On the server: `git pull`.
5. Browsers rename repeated downloads (`name (1).zip`); the instructions always name the
   exact file and check `VERSION` afterwards.

**Throttling.** Every script produced takes `--threads` and `--max-jobs` (environment
variables `GA_MAX_THREADS`, `GA_MAX_JOBS`); scripts that transfer data also take
`--bwlimit` (`GA_BWLIMIT`). Nothing is limited unless asked, except that the fetch script
fetches one assembly at a time by default (NCBI is asked politely); `--max-jobs N`
raises it.

---

## 4. Assembly panel

The panel is held in `config/genome_panel_P1.tsv` (machine-readable; one file per panel
version, so earlier panels stay available). **Current panel version: P1** (25 assemblies,
2026-10). Selection rule: chromosome-level (or complete) assemblies, contig N50 of at
least 20 Mb; one entry per assembly; superseded versions dropped. The common library
validates the panel (`ga_common.panel`).

| species | code | assemblies | notes |
|---|---|---|---|
| *Maylandia zebra* | MZ | 6 | GCF_041146795.1 (NMK-2024a, male) is the **reference** |
| *Astatotilapia calliptera* | AC | 3 | ancestral arrangement, with MZ |
| *Copadichromis virginalis* | CV | 3 | |
| *Diplotaxodon limnothrissa* | DT | 3 | |
| *Mchenga conophoros* | MC | 3 | |
| *Rhamphochromis longiceps* | RC | 2 | |
| *Aulonocara* sp. 'chitande type north' (Yellow Head) | YH | 3 | XY on LG10; the female assemblies should be X/X |
| *Aulonocara stuartgranti* | AS | 2 | homozygous for the LG10 sex-determination core |

**Supplementary sequences** (held beside the panel, not part of it; listed in
`config/supplementary_sequences.tsv`): the YH LG10 **Y haplotig** (h2tg000014l), not on
NCBI, copied unchanged from Dropbox `CichlidSequencingData/2026_Nikesh/Chromosome10s/YH_Y.fasta`
as `YH_LG10Y`. The X haplotig is not copied: the YH panel assemblies carry X.

**Fields per assembly:** id, species, sample, sex, accession (GenBank, and RefSeq
if annotated), submitter, release date, level, contig N50, haplotype status
(collapsed diploid / haplotype-resolved / haplotig), chromosome accessions (LG2,
LG10, LG13), annotation available, repeat annotation status, arrangement per
chromosome (filled from project 2b's registered arrangement table).

**Reference and ancestry:** all results are reported in MZ (GCF_041146795.1)
coordinates. MZ and *A. calliptera* carry the ancestral arrangement of each
chromosome; where MZ alone differs from every other assembly, it is flagged as a
likely MZ assembly error, not interpreted.

---

## 4a. Versions and releases

The analysis will be rerun as more genomes become available. Three kinds of
version keep every result traceable to the genomes and code that made it.

| version | what it identifies | changes when |
|---|---|---|
| **Panel** (P1, P2, …) | the exact list of assemblies, each by accession *and* accession version (e.g. GCA_057381975.1) | an assembly is added or dropped, or a new accession version replaces one |
| **Release** (R1, R2, …) | one complete, consistent run of the system on one panel: a frozen set of registered output versions, one per contract | the owner decides to make a release (usually after a new panel, or a significant project update) |
| **Project output** (per contract) | one output of one project | the project registers a new output; it always names the panel version it was built from |

**Releases**
- A release record lists: release id, date, panel version, reference, and the
  registered output version used for every contract.
- Releases are **immutable**. A correction makes a new release, never an edit of an
  old one. Earlier releases stay available for comparison.
- Minor releases (R1.1, R1.2) are allowed for project updates on the same panel;
  a new panel always starts a new release number (P2 → R2).

**The reference within a release series**
- MZ GCF_041146795.1 stays the reference for every release while it is in use.
  Changing the reference (a new MZ assembly version, say) changes every coordinate
  and is recorded as a **major break**, with the coordinate translation registered
  as an output of its own.

**What a new panel requires from each project**

| project | rerun when assemblies are added |
|---|---|
| 1. Repeats | per the library policy (open question): frozen library, mask new assemblies only; or rebuilt library, re-mask all |
| A. Annotation | new assemblies only (unless a source annotation changed) |
| 2a. Alignment | pairwise: new assemblies only; graph: rebuilt with all assemblies |
| 2b. Structure | all assemblies (orientation and breakpoint calls use consensus across assemblies) |
| 3. Variant finder | all assemblies, from the new graph |
| 4. Genotyper | all samples, against the new catalogue |
| B, 5, C | rerun on the new release |

**Stable identifiers across releases**
- Assemblies: by accession and accession version.
- Variants: by MZ chromosome, position and alleles (after normalization), so the
  same variant has the same identity in every release.
- Breakpoints, inversions and arrays: named by chromosome and MZ position (e.g.
  `LG13_inv_2.40-23.07`); a call that moves becomes a new identity, recorded in the
  release comparison.

**Release comparison.** Each release after R1 comes with a short summary against
the previous one: assemblies added or removed; inversions, breakpoints and
arrangements that changed; variants and genotypes gained or lost. Calls that stay
stable as genomes are added are themselves evidence that they are real.

---

## 5. Data: how it is fetched and organized

**Decided (principles)**
- **Accessions are the source of truth.** Assemblies are fetched by accession and
  accession version with NCBI Datasets, e.g.
  `datasets download genome accession GCA_057381975.1 --include genome,gff3,seq-report`.
  Download locations are not stored; they follow from the accession.
- **Every fetched file gets a provenance record:** accession, files received, date,
  tool version, checksum, and the chromosome names and lengths from NCBI's sequence
  report.
- **Projects find data through the registry,** never through hard-coded paths, so the
  layout can change without changing any project. Until the registry holds entries
  (section 7), data is located through one function of the common library
  (`ga_common.paths`), which is the only place the layout is written down.
- **Data belonging to a release is never overwritten.**

**Decided (2026-10-26): organization**
- **Scope:** whole genomes (the earlier question "whole genomes or LG2, LG10, LG13 first"
  is answered: whole genomes).
- **Where:** the **data root** `GenomeAlignments`, in Dropbox `Apps/` (authoritative) and
  mirrored on mzebra at `~/Temp/GenomeAlignments` (working copy, regenerable). The
  laptop holds no data. Repositories are elsewhere (section 3a).
- **Layout, keyed to the panel's assembly ids and accession versions:**

```
<data root>/
  Genomes/
    <assembly_id>/                    e.g. MZ_MZ4f
      <accession_version>/            the GenBank accession version, e.g. GCA_057381975.1
        genome.fna.gz                 BGZF-compressed (indexable)
        annotation.gff3.gz            if annotated
        sequence_report.jsonl         NCBI's sequence report, as received
        provenance.json               accession, files, date, tool versions, checksums, names/lengths
  RepeatInformation/
    versions/
      RI_v1/
        MANIFEST.yaml                 panel version, assemblies used to BUILD the library,
                                      assemblies MASKED, command, tool versions, date
        library/                      the shared repeat library
        masked/<assembly_id>/         RepeatMasker .out, BED, masked genome
      RI_v2/ ...
```

- **Naming:** folders and files are keyed to the panel's assembly ids (e.g. `MZ_MZ4f`)
  and accession versions. Sequence names inside files are kept exactly as received;
  nothing is renamed.
- **Versions:** a **version folder is never overwritten** (`Genomes/<id>/<accession_version>`
  and `RepeatInformation/versions/RI_vN`). A change is a new version. The panel version
  does not appear in the `Genomes` layout (a genome is keyed by accession version); it is
  named in every `MANIFEST.yaml` and in every registered output. The library build set and
  the masked set are recorded separately in `MANIFEST.yaml`, so one library can be applied
  to a different subset.
- **Which accession is downloaded:** RefSeq when the assembly is annotated (it carries the
  GFF3), otherwise GenBank; the folder is always named by the GenBank accession version and
  `provenance.json` records which accession was fetched. *(Proposed default; see section 13.)*
- **Compression:** FASTA and GFF3 are stored BGZF-compressed so `samtools faidx` and
  `tabix` work. The checksums of the files as NCBI delivered them are kept in
  `provenance.json`, together with the checksum of the uncompressed content.
- **Fetch checks before a folder appears:** NCBI's `md5sum.txt`; FASTA names and lengths
  against NCBI's sequence report; FASTA lengths against the GFF3 `##sequence-region`
  lines; read-back of the compressed file. A folder is built in a scratch folder and moved
  into place only when all checks pass.
- **Sync:** `scripts/sync.py` moves a path between the data root and Dropbox. It is a dry
  run unless `--go` is given, never overwrites or deletes (rclone `copy --immutable`: an
  existing file that differs is an error), and warns when a version folder already exists
  at the destination.
- **Size, backup, access:** Dropbox and GitHub are what get backed up; the server's working
  copies are regenerable; whether `/home` on mzebra is backed up is unknown. Everyone with
  the shared account has the same access to the data root. An estimate, not measured: 25
  whole genomes of about 1 Gb each need roughly 25 GB uncompressed.

**Existing data and what happens to it**

| what | decision |
|---|---|
| Dropbox `CichlidSequencingData/Genomes/*_NCBI/` (old annotations and genomes) | redundant, since genomes are fetched by accession; not moved, not registered, not deleted by the coordinator |
| Dropbox `CichlidSequencingData/2026_Nikesh/` (pilot experiments) | not used, except one file: the YH Y haplotig (section 4) |
| `2026_Nikesh/BamSlices/` | dropped; whole genomes make slices unnecessary |
| RepeatModeler family table `RepeatModeler_TE.xlsx` | recreated by project 1; the old library is not needed |
| Blumer et al. 2025 SNPs (`chr10.vcf.gz`) | deferred until needed. The path recorded earlier on the server (`~/Temp/TreeFamData/Data/Blumer2025/chr10.vcf.gz`) was checked on 2026-10-26: the folder exists, holds only `coding` and `inversions`, and no `chr10.vcf.gz`. The location is to be decided by the owner when it is needed |
| Short-read data | deferred (not yet organized) |
| RNA-seq data | not yet discussed; deferred |
| the pilot repository `chr10sv` and its `data/` and `results/` | to be replaced; not depended on |

**Not yet placed in the layout** (left out until their project needs them): short-read and
RNA data; other projects' registered outputs; release records; the registry itself.

---

## 6. Contracts: formats passed between projects

Each contract has an id, a version, an owning project, and a validator in the
common library. Draft list; exact fields to be agreed with each owning project.

| contract | owner | format | content |
|---|---|---|---|
| `panel` | 0 | TSV | the assembly panel (section 4), with its panel version; validator in `ga_common.panel` (0.1.0) |
| `release` | 0 | YAML | release record: id, date, panel version, reference, output version per contract (location per the data organization) |
| `samples` | 0 | TSV | short-read and RNA samples: id, species, sex, arrangements, data location |
| `repeats` | 1 | RepeatMasker `.out` + BED | per assembly: interval, class, family, divergence |
| `genes` | A | GFF3 | per assembly: gene models with source gene id; table of unlifted / partial genes |
| `alignment` | 2a | PAF (+ `cs` tag) | each assembly against MZ |
| `graph` | 2a | GFA | pangenome graph, unclipped |
| `arrangement` | 2b | TSV | assembly, chromosome, arrangement, confidence |
| `breakpoints` | 2b | TSV | breakpoint id, MZ interval, location in every assembly, carrier junctions, mechanism, genes |
| `artefacts` | 2b | BED | flagged regions per assembly (MZ-only, MZ-specific orientation, likely misassemblies) |
| `variants` | 3 | VCF | multi-assembly, MZ coordinates, each assembly a sample; INFO: type, transposon class, ancestral/derived, arrangement |
| `genotypes` | 4 | VCF | per individual |
| `ase_panel` | B | VCF/BED | SNVs selected for a comparison |
| `expression` | B | TSV | gene-level expression and ASE summaries |

**Gap:** the shared repeat library is an output of project 1 (section 2) but no contract
lists it (section 13).

**Coordinate conventions** (in every contract): MZ chromosome accessions
(NC_1351xx); 1-based, inclusive in TSV and VCF; 0-based, half-open in BED and PAF,
as those formats define.

---

## 7. Registry

One entry per registered output. Projects use only registered outputs, by version.

| output | contract (version) | project | version | panel | location | checks passed | registered | used by | in releases |
|---|---|---|---|---|---|---|---|---|---|
| *(none yet)* | | | | | | | | | |

---

## 8. Common library

- Lives in the coordinator's repository as its own package (`common/`, package
  `ga_common`), with its own version. **Minimum Python: 3.9** (the server's base
  Python; the laptop has 3.13). The coordinator scripts run in the conda environment
  `ga-coord` (`environment.yml`).
- Contains readers, writers and validators for every contract, and coordinate-frame
  conversions (MZ, assembly-native, reverse-stored assemblies).
- Projects install a pinned version:
  `pip install "git+https://github.com/ptmcgrat/ga-coordinator.git@common-v<x.y.z>#subdirectory=common"`
  (the tag `common-v0.1.0` is created by the owner when installing `coordinator_001`).
- **Version 0.1.0** (delivered in `coordinator_001`) holds: `paths` (the data layout and the
  machine profiles), `panel` (reader and validator), `provenance`, `throttle`, `bgzf`
  (BGZF writer), `seqio` (FASTA and GFF3 helpers) and `rclone` (wrapper). It holds no
  contract parsers yet.
- The parsers follow in a later version, starting from the pilot `chr10sv` modules
  `paf.py`, `genes.py`, `repeatmasker.py` and `util.py` (they parse as Python 3.9;
  behaviour is not yet tested here). `vcf.py` is **not** taken: it depends on pilot-specific
  modules and will be redeveloped in another repository.
- The pilot's `FileManager` is not reused (hostname-dependent mirror folder, Google
  credentials needed at start, no dry run, no overwrite protection).

---

## 9. Checks the coordinator performs

- **On fetching data:** checksum recorded; sequence names and lengths match the
  source (e.g. chromosome accession lengths match the NCBI annotation). Implemented in
  `scripts/fetch.py` (section 5).
- **On registering an output:** it validates against its contract version, its
  inputs are registered versions, and they come from the same panel version.
- **On making a release:** every contract has a registered output built from the
  release's panel, and the release comparison is written.
- **On a new version of a registered output:** every project that uses it is
  notified.

---

## 10. Template for every project's specification document

1. **Purpose and scope**: what the project does, and explicitly what it doesn't.
2. **Inputs**: each by registered output and version (and the panel version it was built
   from); never another project's internals.
3. **Outputs**: files, contract versions, locations.
4. **Methods**: the agreed approach, and why.
5. **Checks**: how outputs are validated before integration.
6. **Decisions**: dated log, with reasons.
7. **Open questions**: blocking ones marked.
8. **Status**: where the project stands; what is ready to integrate.
9. **Environment and delivery**: the lab environment and the delivery of code (section 3a):
   repository location on laptop and server, numbered zips, `git pull` on the server,
   data root and its Dropbox mapping, throttling options, and who may work on the
   repository (one person at a time).

---

## 11. Decision log

| date | decision |
|---|---|
| 2026-10 | The work is split into projects (0, 1, A, 2a, 2b, 3, 4, B, 5, C), each owning one repository. |
| 2026-10 | All communication passes through the coordinator; projects plan before coding; only blocking items are escalated. |
| 2026-10 | MZ GCF_041146795.1 is the reference coordinate system; MZ and *A. calliptera* carry the ancestral arrangement. |
| 2026-10 | Panel of 25 assemblies (MZ 6, AC 3, CV 3, DT 3, MC 3, RC 2, YH 3, *A. stuartgranti* 2). |
| 2026-10 | Variants come from a pangenome graph; a benchmark against the validated chr10 X/Y callset is held in reserve. |
| 2026-10 | Breakpoints are located by pairwise alignment to MZ, characterized by local comparisons (best local ancestor, not automatically MZ), and confirmed by independent assemblies and reads. |
| 2026-10 | Gene models by liftover (LiftOn) from MZ and the annotated assemblies. |
| 2026-10 | One shared repeat library for all assemblies, keeping existing family names. (Questioned 2026-10-26: the family table is to be recreated; see section 13.) |
| 2026-10 | RNA-seq is processed by the separate expression pipeline; project B designs ASE panels and summarizes results. |
| 2026-10 | The common library lives in the coordinator's repository as a separately versioned package. |
| 2026-10 | Assemblies are fetched by accession (NCBI Datasets), with provenance; projects find data through the registry; the data organization itself is reopened for discussion. |
| 2026-10 | The analysis is versioned for reruns: panel versions (P1 = the current 25 assemblies), immutable releases (R1 = the first complete run on P1), every output naming its panel; stable identifiers keyed to MZ positions and accessions; MZ GCF_041146795.1 fixed as reference within a release series. |
| 2026-10-26 | Lab environment recorded (section 3a): Dropbox authoritative for data, GitHub for code; analyses run on mzebra (projects keep flexibility about where); the server account is shared and the rule is one person per repository. |
| 2026-10-26 | Repositories live outside Dropbox on every machine (`~/GenomeAlignments/<repo>`), because everything produced is committed at once and GitHub is the backup. |
| 2026-10-26 | Anything under Dropbox `Apps/` is mirrored under `~/Temp/` on mzebra; the data root is `GenomeAlignments` (Dropbox `Apps/GenomeAlignments`, mzebra `~/Temp/GenomeAlignments`). |
| 2026-10-26 | Data organization settled (section 5): whole genomes; `Genomes/<assembly_id>/<accession_version>/` and `RepeatInformation/versions/RI_vN/`; version folders never overwritten; sequence names kept as received. The repeat folder is named `RepeatInformation`. |
| 2026-10-26 | Old `CichlidSequencingData/Genomes/*_NCBI/`, `2026_Nikesh/` and `BamSlices/` are not part of the new system; the one exception is the YH Y haplotig, copied unchanged as supplementary sequence `YH_LG10Y`. The X haplotig is not copied. |
| 2026-10-26 | Genomes and annotations are stored BGZF-compressed, with the checksums of the original files kept in provenance. |
| 2026-10-26 | Short-read data, RNA data and the Blumer2025 VCF are deferred. |
| 2026-10-26 | Code is delivered as numbered zips (`<project>_NNN.zip`) with a manifest and instructions; the server receives code by `git pull`; every project specification carries this convention. |
| 2026-10-26 | Every script takes throttling options (`--threads`, `--max-jobs`, `--bwlimit` where data is transferred); no limit by default. |
| 2026-10-26 | Common library minimum Python 3.9; coordinator scripts run in conda environment `ga-coord`; the pilot `FileManager` is not reused; `vcf.py` is not carried over and will be redeveloped in another repository. |
| 2026-10-26 | Panel files are named per version (`config/genome_panel_P1.tsv`), resolving the earlier mismatch between sections 4 and 14. |

---

## 12. Relayed questions and answers

| date | from | to | question | answer |
|---|---|---|---|---|
| *(none yet)* | | | | |

---

## 13. Open questions

| question | affects | blocking |
|---|---|---|
| **Which accession is fetched for annotated assemblies:** RefSeq (default in `fetch.py`, carries the GFF3) or GenBank? Confirm the default | 0, A, 1 | no |
| **The first real download is untested:** the fetch script is tested against a stand-in for `datasets` laid out as an NCBI download is expected to be; the first `--go` on mzebra confirms the real layout | 0 | before the P1 download |
| Contract for the shared repeat library (project 1 output, no contract listed) | 1, 0 | before project 1's first integration |
| Does the shared library keep the existing family names, now that the family table is recreated? | 1 | no |
| How the shared library is built (which genomes, RepeatModeler with `-LTRStruct`?) | 1 | no |
| Where project 1's tools run, and how long jobs are kept alive on the shared server (owned by project 1) | 1 | no |
| Repeat library policy for new panels: frozen (mask new genomes only) or rebuilt (re-mask all)? | 1, all downstream | before P2 |
| What triggers a new release: every new panel, or a minimum number of new genomes? | 0 | no |
| Minigraph-Cactus or PGGB? | 2a, 3 | no |
| Which raw long reads are available for junction checks? | 2b | no |
| Exact fields of each contract | 0, all | per project, before its first integration |
| Sex and haplotype status for assemblies where NCBI records none | 0, 3 | no |
| Confirm the inferred LG10 accessions of CV, DT, MC, RC, YH (the sequence reports of the first downloads will show them) | 0 | no |
| Where do short-read data, RNA data, registered outputs, release records and the registry live? | 0, 4, B | when the first of them is needed |
| Where does the Blumer2025 VCF live? | 5 | when needed |
| Is `/home` on mzebra backed up, and is there a disk quota? | 0 | no |
| Does `docs/genome_panel.md` (a readable description of the panel) still need writing, now that the TSV is the panel? | 0 | no |

---

## 14. Status

- Panel P1 selected (25 assemblies, `config/genome_panel_P1.tsv`, validated by
  `ga_common.panel`); not yet downloaded.
- Data organization settled (section 5). Lab environment recorded (section 3a).
- First code base written (`coordinator_001`, common library 0.1.0): paths, panel,
  provenance, throttle, BGZF, rclone wrapper, `scripts/fetch.py`, `scripts/sync.py`, tests.
  It passes its tests against stand-ins for rclone and `datasets`; it has not yet been
  installed or run on mzebra, and nothing has been downloaded.
- Project 1 (Repeats) specification drafted for discussion with the owner
  (`repeats_001`); its inputs wait for the P1 download.
- No releases yet; R1 will be the first complete run on P1.
- No contracts (beyond `panel`), registry entries or contract parsers yet.
- The pilot `chr10sv` code remains in use until projects replace it.
