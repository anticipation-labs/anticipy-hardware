# Anticipy Hardware

Consolidated hardware record for the Anticipy pendant — a wearable that listens passively,
pulls tasks out of conversation, and acts on them without commands.

**Assembled:** 2026-09-06 · **Files:** 3756 (1189 unique) · **Size:** ~656M B
**Sources consolidated:** 15 separate packages plus loose files and sealed original zips from
Downloads, Desktop and Documents.

---

## The one thing to read first

> **Nothing here is fabrication-ready. There is no released Gerber, ODB++, drill file,
> pick-and-place, assembly drawing or final enclosure drawing anywhere in this repository.**
>
> There is, however, a **live JLCPCB order** (`W2026083114248171` / `SMT026083160845`) with an
> **unresolved part substitution** awaiting DFM review. See [07_PROCUREMENT](07_PROCUREMENT/).
> That is the only clock currently running.

> ⚠️ **Do not flash `anticipy.uf2` from any `~/AnticipyFleet/*/firmware/` lane.** That file is the
> image formally classified `UNVERIFIED_DO_NOT_FLASH` (sha256 `2e78015e…`, 624,640 bytes), sitting
> under a clean name next to a build receipt that describes a *different* 509,440-byte image.
> Details: [`00_START_HERE/CONTRADICTIONS.md`](00_START_HERE/CONTRADICTIONS.md) §14.

**New to this project?** Read [`00_START_HERE/ORIENTATION.md`](00_START_HERE/ORIENTATION.md) first.
It assumes no prior context: what the product is, where it actually stands, how to open every file
type here, what the vocabulary means, and what to do in your first week.

Then read [`00_START_HERE/HARDWARE_STATE.md`](00_START_HERE/HARDWARE_STATE.md) — one page on what
is actually true today — followed by
[`00_START_HERE/CONTRADICTIONS.md`](00_START_HERE/CONTRADICTIONS.md), which lists **seventeen** places
where two documents in this repository disagree with each other. Read that **before** acting on any
single document, because several of them contradict each other on the processor, the enclosure
size and the state of the board.

---

## Folder map

| Folder | What it is | Fab status |
|---|---|---|
| [`00_START_HERE/`](00_START_HERE/) | Orientation for newcomers, state, contradictions, glossary, provenance | — |
| [`01_CURRENT_TARGET_R1/`](01_CURRENT_TARGET_R1/) | The live requirement set (2026-09-04). What the incoming engineer is asked to build. | Not designed yet |
| [`02_PROTOTYPE_XIAO/`](02_PROTOTYPE_XIAO/) | XIAO nRF52840 Sense proof unit — wiring, enclosure CAD, assembly evidence | Proof only, on physical-test hold |
| [`03_PCB/`](03_PCB/) | Every custom board design. Three exist. None are releasable. | **NOT FOR FAB** |
| [`04_MECHANICAL/`](04_MECHANICAL/) | Enclosure CAD — print-ready, reference STEP, superseded meshes | Print-ready ≠ production |
| [`05_FIRMWARE/`](05_FIRMWARE/) | Source, build/protocol/threat docs, distinct images, device recovery | Lab only |
| [`06_FACTORY_AND_QA/`](06_FACTORY_AND_QA/) | Factory release process, QA fixtures, test evidence | Process defined, not executed |
| [`07_PROCUREMENT/`](07_PROCUREMENT/) | BOMs, order sheets, sourcing, **live JLCPCB order status** | Active |
| [`08_HISTORICAL_PACKAGES/`](08_HISTORICAL_PACKAGES/) | All 12 source packages plus the original zips, preserved verbatim. Never edit. | Archive |
| [`99_MANIFESTS/`](99_MANIFESTS/) | `SHA256SUMS.txt`, `INVENTORY.csv` | — |

**Folders `01`–`07` are a curated working view. Folder `08` is the provenance record.**
Every file in `01`–`07` also exists in `08`, byte-identical. If the two ever disagree, `08` wins.

---

## The five board generations, decoded

This is the single most confusing thing in the project, so it is stated once, plainly:

| Name | What it actually is | Where | State |
|---|---|---|---|
| **R0** | `ANT-PROD-R0 EVT`. First custom board. Has 31 commits of routing history. | `03_PCB/R0_ROUTING_HISTORY_NOT_FOR_FAB/` | 23 non-GND nets still unconnected |
| **R0B** | Revision B of R0. The "engineering checkpoint" the master package leads with. | `03_PCB/R0B_CHECKPOINT_NOT_FOR_FAB/` | 176 connections unrouted |
| **EVT-A** | `anticipy_evt_a`. A *separate* board from the 2026-08-28 Execution package, targeting a **different processor**. | `03_PCB/EVT_A_2026-08-28_SUPERSEDED/` | Fabrication hold: 0 segments, 0 vias, 0 zones |
| **ESP32-S3** | The prior generation (April 2026). Different SoC, mic, charger and enclosure entirely. Holds the only packaging spec and manufacturing-order doc that exist. | `08_HISTORICAL_PACKAGES/2026-04_esp32s3_prior_generation/` | Superseded |
| **R1** | The current target. **Does not exist yet** — brief only. | `01_CURRENT_TARGET_R1/` | Not started |

R0 and R0B are not the same file, and the copy of R0 shipped inside the master package is **not**
the same file as the one in the R0 git repository. See `00_START_HERE/CONTRADICTIONS.md`.

---

## Working with this repository

### Cloning

```bash
git lfs install                                    # once per machine
git clone https://github.com/anticipation-labs/anticipy-hardware.git
```

Git LFS is required, but only barely — it is scoped to exactly **two** files, the oversized
superseded meshes under `04_MECHANICAL/SUPERSEDED_AND_MOCKUPS/OVERSIZED_MESHES_500mah_2026-08-22/`
(68.8 MB and 64.8 MB). Everything else is stored as ordinary git objects deliberately, so a clone
never depends on an LFS bandwidth quota. If LFS is unavailable, `GIT_LFS_SKIP_SMUDGE=1 git clone`
still gets you the entire repository minus those two superseded files.

### Byte fidelity

`.gitattributes` sets `* -text`, disabling all end-of-line conversion. This is not cosmetic: this
repository is a checksum-verified archive, and EOL rewriting would silently invalidate
`99_MANIFESTS/SHA256SUMS.txt` for every CSV that arrived with CRLF endings.

### The R0 routing history

The R0 KiCad project arrived as its own git repository with 31 commits and no remote. A nested
`.git` cannot be committed into a parent repository, so the history is preserved as a bundle:

```bash
cd 03_PCB/R0_ROUTING_HISTORY_NOT_FOR_FAB
git clone R0_ROUTING_HISTORY.bundle r0-history      # full 31-commit history, restored
```

`R0_ROUTING_HISTORY_COMMITS.txt` lists every commit, and
`R0_UNCOMMITTED_AT_ARCHIVE_TIME.txt` records the working-tree changes that were uncommitted when
this archive was made. Those uncommitted files are present in the folder as-is.

### What is deliberately not ignored

`.kicad_prl` and other KiCad per-user state arrived inside the original handoff packages and are
covered by the checksum manifest, so they are committed rather than ignored. Only `__pycache__`
bytecode and macOS `.DS_Store` files were removed.

---

## Verifying this folder

```bash
cd ~/Anticipy-Hardware && shasum -a 256 -c 99_MANIFESTS/SHA256SUMS.txt
```

`99_MANIFESTS/INVENTORY.csv` lists every file with its hash, size, date and owning folder.
