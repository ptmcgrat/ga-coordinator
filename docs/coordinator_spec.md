# Coordinator specification

**Project:** 0, Coordinator (controller)
**Document version:** 0.8, 2026-10-26 (0.1: first draft; 0.2: panel versions and releases; 0.3: data organization reopened; downloads by accession; 0.4: lab environment recorded; data organization settled; code delivery convention; first code base; 0.5: install commands printed in the conversation; specifications shared as files; 0.6: first real downloads recorded; rclone single-file fix; 0.7: ecogroups and relatedness context; species table; 0.8: P1 downloaded; chromosome labels and accessions)
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
| tools seen | git 2.50.1, Python 3.13.11, rclone at `/usr/local/bin/rclone` | git 2.27.0, rclone v1.57.0-DEV, Python 3.9.18, conda 24.11.3 (channels bioconda, conda-forge, defaults); no docker, singularity or mamba; NCBI reachable; in conda environment `ga-coord`: NCBI `datasets` 18.39.0; rclone 1.57 has `--immutable` (checked) |
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
6. **The install commands are always printed in the conversation** with the zip; the owner
   should never have to open `INSTRUCTIONS.md` to find them (the file repeats them).
7. **Every specification document is shared directly as a file** the owner can read in the
   browser (the coordinator specification, and each project specification when it is
   issued), not only inside a zip.

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

| species | code | assemblies | ecogroup (section 4b) | notes |
|---|---|---|---|---|
| *Maylandia zebra* | MZ | 6 | mbuna | GCF_041146795.1 (NMK-2024a, male) is the **reference** |
| *Astatotilapia calliptera* | AC | 3 | generalist (stands in for the ancestor) | ancestral arrangement, with MZ |
| *Copadichromis virginalis* | CV | 3 | utaka | |
| *Diplotaxodon limnothrissa* | DT | 3 | Diplotaxodon (pelagic) | |
| *Mchenga conophoros* | MC | 3 | shallow benthic | |
| *Rhamphochromis longiceps* | RC | 2 | Rhamphochromis (pelagic) | |
| *Aulonocara* sp. 'chitande type north' (Yellow Head) | YH | 3 | deep benthic (true deep clade) | XY on LG10; the female assemblies should be X/X |
| *Aulonocara stuartgranti* | AS | 2 | deep benthic | homozygous for the LG10 sex-determination core |

The eight species cover all seven ecogroups of the Lake Malawi radiation. The ecogroups and
the relatedness between them are in section 4b and in `config/species_context.tsv`.

**Supplementary sequences** (held beside the panel, not part of it; listed in
`config/supplementary_sequences.tsv`): the YH LG10 **Y haplotig** (h2tg000014l), not on
NCBI, copied unchanged from Dropbox `CichlidSequencingData/2026_Nikesh/Chromosome10s/YH_Y.fasta`
as `YH_LG10Y`. The X haplotig is not copied: the YH panel assemblies carry X.

**Fields per assembly:** id, species, sample, sex, accession (GenBank, and RefSeq
if annotated), submitter, release date, level, contig N50, haplotype status
(collapsed diploid / haplotype-resolved / haplotig), chromosome accessions (LG2,
LG9, LG10, LG11, LG13, LG20, the six inversion chromosomes; held in the companion table
`config/panel_chromosomes_P1.tsv`), annotation available, repeat annotation status,
arrangement per chromosome (filled from project 2b's registered arrangement table).

**Chromosome labels and lengths (observed in the P1 download, 2026-10-26)**
- The companion table `config/panel_chromosomes_P1.tsv` gives, per assembly, the accession NCBI labels
  LG2, LG9, LG10, LG11, LG13 and LG20. It is generated from the `provenance.json` files by
  `scripts/panel_chromosomes.py`, so it can be regenerated and checked.
- **Two label styles.** 17 assemblies are labelled `LG1`–`LG20`, `LG22`, `LG23` (no LG21; the reference has
  22 chromosomes). The other 8 (`AC_SAMEA123396440`, `AC_SAMEA123396441`, `AC_fAstCal68`,
  `AS_SAMEA123396442`, `AS_Sanger`, `DT_SAMEA123396444`, `MZ_SAMEA123396453`, `MZ_SAMEA123396454`) use
  plain numbers 1–20, 22, 23, the same set. That a number is the same chromosome as the reference's LG
  is a **working assumption** (the label set and the four longest chromosomes, 3, 7, 23 and 6, agree);
  alignment must confirm it. Accession order is not a guide to labels: in `AS_Sanger`, label 9 is
  `NC_138960.1`, after label 23's `NC_138958.1`.
- The inferred LG10 accessions in the panel notes (CV, DT, MC, RC, YH) match NCBI's labels in the
  RefSeq assemblies.
- **Lengths** (label length in Mb; every chromosome is within a few Mb across assemblies except the
  following; these are observations, not interpretations, and assembly completeness may explain some):
  - **LG2:** the reference is 48.8 Mb; the 24 other assemblies range 38.5–42.3 Mb.
  - **LG3:** varies 1.8-fold, 58.7–105.3 Mb (reference 64.4). The reference is *not* an outlier on LG3.
  - **LG20:** 17.8 Mb (`MC_MC3m`) and 20.3 Mb (`CV_CV2f`), against 35–42 Mb in most; 46.1 (`CV_CV4f`) and
    44.5 (`DT_004f`) are longer. In every assembly LG20 is one sequence.
  - **LG10:** `YH_YH2f` 28.4 Mb, `YH_YH1m` 36.5 Mb, the others 34.0–42.1.
  - **LG9, LG11, LG13:** `MZ_UMD2025` is short on LG9 (29.6), LG11 (33.6) and LG13 (31.6); LG9 is 42–45 Mb
    in `MZ_NMetZ`, `MZ_MZ4f` and `MC_MC3m` against about 37 in most; LG11 is 43.6 in `YH_YH2f`.

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

## 4b. Relatedness and ecogroups

Context for every project. Sources: Malinsky et al. 2018 (*Nature Ecology & Evolution* 2:1940),
Blumer et al. 2025 (*Science*, 12 June 2025) and Kumar et al. 2025 (*eLife* 104923). The group
assignments of the panel species are in `config/species_context.tsv` (validated by
`ga_common.species`); *Mchenga*, *A. stuartgranti* and *Aulonocara* 'chitande type north' were
assigned by the owner and agree with Kumar et al. The inversion columns of that table are
**literature expectations, not results**: project 2b's arrangement table holds the results.

**How closely related**
- The radiation is young and its sequences are very close: average divergence between species
  pairs is about 0.1–0.25% (Malinsky), and divergence of 134 individuals from the *M. zebra*
  reference is 0.19–0.27%. This is SNP-level divergence. None of the three papers measures
  repeat content or structural divergence between species, which is what projects 1, 2a and 2b
  will measure.
- The three subradiations split from a generalist, *Astatotilapia*-like lineage in quick
  succession: pelagic (*Rhamphochromis* and *Diplotaxodon*) first, then the benthic radiation
  (shallow benthic, deep benthic, utaka), then mbuna. Malinsky puts the splits at about
  390–460 thousand years ago (95% intervals about 300–990 ka, assuming 3 years per generation;
  likely underestimates because of later gene flow); fossil-calibrated work puts the origin of
  the radiation at 700–800 ka.
- *A. calliptera* is sister to mbuna in whole-genome trees yet stands for the generalist
  ancestor. It is not an outgroup.
- **Relationships are not a single tree.** 62% of species trios violate a bifurcating tree
  (Malinsky), and Blumer et al. suggest the benthics arose by hybridization between
  *Diplotaxodon* and *A. calliptera* lineages. A group-level statement about closeness is a
  summary, not a guarantee for any pair of assemblies.

**Inversions (six rearrangements; Kumar et al. 2025, Blumer et al. 2025)**
- On LG2, LG9, LG10, LG11, LG13 and LG20, each roughly 10–20 Mb (Kumar gives the largest as
  20.6 Mb in one place and 22.9 Mb in another), together over 10% of the genome. The inversions
  on LG11 and LG20 are tandem doubles; on LG20, *Rhamphochromis* carries only the first (left)
  arm. They are called against the *M. zebra* GT3a reference, which carries the ancestral state of
  all six.
- Expected state of the panel species (`ancestral` = as in the reference):

| species | LG2 | LG9 | LG10 | LG11 | LG13 | LG20 |
|---|---|---|---|---|---|---|
| MZ (mbuna), AC (generalist) | anc | anc | anc | anc | anc | anc |
| RC (*Rhamphochromis*) | anc | anc | anc | anc | anc | left arm only |
| DT (*Diplotaxodon*) | anc | inv | anc | inv | anc | inv |
| CV (utaka), MC (shallow benthic) | anc | segregating | anc | segregating | anc | inv |
| AS (deep benthic, no deep-water inversions) | anc | segregating | anc | segregating | anc | inv |
| YH (deep benthic, true deep clade) | inv | inv | inv | inv | inv | inv |

- LG2, LG10 and LG13 inversions are common in deep benthics and rare in shallow benthics and
  utaka, but not all deep benthics carry them: *A. stuartgranti* does not. The LG10 inversion is
  linked to an XY sex-determination system in some deep benthics (YH).
- Kumar et al. note an error or polymorphism in the *M. zebra* reference on LG2.

**What this means for projects (context, not design)**
- 1, Repeats: the panel spans all seven ecogroups, so a library build set can span them. Whether
  one shared library is adequate is untested.
- 2a, Alignment: expect near-identical sequence with large rearrangements. Pairwise alignments to
  MZ and the graph must be able to represent inversions of 10–20 Mb on six chromosomes; a panel
  species can differ from the reference on LG9, LG11 and LG20 as well as LG2, LG10 and LG13.
- 2b, Structure: the table above is a prior, not a result.

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
  the shared account has the same access to the data root. Measured on 2026-10-26: the 25 assemblies of
  P1 and the Y haplotig total 85 files and 7.348 GiB in Dropbox (a genome is about 300 MB compressed; each
  took about a minute to fetch).

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
| `panel_chromosomes` | 0 | TSV | companion to `panel`: accession of LG2, LG9, LG10, LG11, LG13, LG20 per assembly, generated by `scripts/panel_chromosomes.py` |
| `panel` | 0 | TSV | the assembly panel (section 4), with its panel version; validator in `ga_common.panel` (0.1.0) |
| `species_context` | 0 | TSV | ecogroup and expected inversion state per species code (section 4b); validator in `ga_common.species` (0.2.0) |
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
  (the tags `common-v0.1.0` and `common-v0.2.0` are created by the owner when installing
  `coordinator_001` and `coordinator_004`).
- **Version 0.2.0** (delivered in `coordinator_004`; 0.1.0 was in `coordinator_001`) holds: `paths` (the data layout and the
  machine profiles), `panel` (reader and validator), `provenance`, `throttle`, `bgzf`
  (BGZF writer), `seqio` (FASTA and GFF3 helpers), `rclone` (wrapper) and `species` (the species-context
  reader and validator). It holds no contract parsers yet.
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
   data root and its Dropbox mapping, throttling options, who may work on the
   repository (one person at a time), and that install commands are printed in the
   conversation and specifications are shared as files.
10. **Relatedness context**: the part of section 4b that bears on the project (ecogroups,
   expected divergence, expected inversions), stated as context, not as results.

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
| 2026-10-26 | Install commands are always printed in the conversation, and every specification is shared directly as a file readable in the browser (owner's request); recorded in section 3a (items 6 and 7) and in the template (section 10, item 9). |
| 2026-10-26 | Single-file copies from Dropbox are made without rclone filters (rclone 1.57 refuses a filter together with a single-file copy); directory copies keep the filter that excludes fetch scratch folders. Found when the first supplementary copy failed on mzebra; fixed in `coordinator_003`. |
| 2026-10-26 | Ecogroups of the panel species (owner): *Mchenga conophoros* is a shallow benthic; *Aulonocara stuartgranti* is a deep benthic (a rocky *Aulonocara* in Blumer et al.); *Aulonocara* 'chitande type north' is a deep benthic of the true deep clade. Kumar et al. agree. |
| 2026-10-26 | Ecogroups and expected inversion states are held in a separate species table (`config/species_context.tsv`, common library 0.2.0), not as new columns of the panel, so the `panel` contract is unchanged. The inversion columns are literature expectations, not results. |
| 2026-10-26 | Six inversions, on LG2, 9, 10, 11, 13 and 20 (Kumar et al. 2025), replace the earlier working assumption of five (Blumer et al.): LG20 is a tandem double inversion that Blumer et al. mention but do not count among their five. |
| 2026-10-26 | P1 downloaded and pushed to Dropbox (25 assemblies; 85 files with the Y haplotig; 7.348 GiB). |
| 2026-10-26 | Chromosome accessions of the six inversion chromosomes are held in a generated companion table (`config/panel_chromosomes_P1.tsv`), not in the panel; plain-number labels are taken as the reference's LG numbers as a working assumption until alignment confirms them. An earlier remark that the reference's LG3 is an outlier is withdrawn: LG3 varies 1.8-fold across assemblies. |
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
| Are the plain numbers 1–23 in the 8 assemblies without `LG` labels the same chromosomes as the reference's LG1–LG23? (working assumption; alignment to confirm) | 2a, 2b | no |
| Where do short-read data, RNA data, registered outputs, release records and the registry live? | 0, 4, B | when the first of them is needed |
| Where does the Blumer2025 VCF live? | 5 | when needed |
| The panel's `arrangement_` columns cover LG2, LG10 and LG13 only, but there are inversions on LG9, LG11 and LG20 too: keep arrangement in the panel (add columns) or only in project 2b's table? | 0, 2b | no |
| Is `/home` on mzebra backed up, and is there a disk quota? | 0 | no |
| Why is LG20 only 17.8–20.3 Mb in `MC_MC3m` and `CV_CV2f` (35–42 Mb in most assemblies)? Is part of LG20 elsewhere in those assemblies? | 2a, 2b | no |
| Does `docs/genome_panel.md` (a readable description of the panel) still need writing, now that the TSV is the panel? | 0 | no |

---

## 14. Status

- Panel P1 selected (25 assemblies, `config/genome_panel_P1.tsv`, validated by
  `ga_common.panel`); not yet downloaded.
- Data organization settled (section 5). Lab environment recorded (section 3a).
- First code base written (`coordinator_001`, common library 0.1.0): paths, panel,
  provenance, throttle, BGZF, rclone wrapper, `scripts/fetch.py`, `scripts/sync.py`, tests.
  Installed on mzebra (environment `ga-coord`); its 49 tests pass there.
- **Panel P1 downloaded (2026-10-26, mzebra):** all 25 assemblies were fetched by accession, with GFF3
  for the 8 annotated ones, and passed every fetch check (23 fetched in one run, none failed; the first two
  earlier). Together with the Y haplotig `YH_LG10Y` (one sequence, `h2tg000014l`, 27,689,011 bases) this is
  85 files, all pushed to Dropbox `GenomeAlignments/Genomes/` (7.348 GiB; a push of already-present
  files is skipped, not overwritten). Chromosome labels and lengths: section 4.
- `coordinator_002` (specification v0.5) changed only the specification, `docs/DELIVERY.md` and
  `VERSION`. `coordinator_003` (specification v0.6) added the rclone fix and quieter tests; it is installed on
  mzebra. `coordinator_004` (specification v0.7) added the species table and `ga_common` 0.2.0 and is installed on
  mzebra. `coordinator_005` (this specification, v0.8) adds `config/panel_chromosomes_P1.tsv` and its generator.
- Project 1 (Repeats) specification drafted for discussion with the owner
  (`repeats_001`, revised through `repeats_004`); its inputs (the P1 genomes) are now available.
  Project 2a (Alignment) specification drafted for discussion (`alignment_001`, revised in `alignment_002`).
- No releases yet; R1 will be the first complete run on P1.
- No contracts (beyond `panel`), registry entries or contract parsers yet.
- The pilot `chr10sv` code remains in use until projects replace it.
