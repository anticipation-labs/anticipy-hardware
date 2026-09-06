# Orientation

For someone who has never seen this project. No prior context assumed.

If you already know the project, skip to [`HARDWARE_STATE.md`](HARDWARE_STATE.md).

---

## 1. What the product is

Anticipy is a small wearable pendant. It listens passively, pulls tasks out of ordinary
conversation, and acts on them without anyone issuing a command. No wake word, no "hey Anticipy".

Physically, the device needs to do four things:

1. **Hear.** MEMS microphones feeding the processor over PDM (a digital mic interface).
2. **Remember.** Compress audio and store it locally, so it keeps working when the phone is out of
   range. The target is 16 to 20 hours of offline audio.
3. **Talk to the phone.** Bluetooth Low Energy, streaming live audio and then backfilling in order
   whatever it recorded while disconnected.
4. **Nudge you.** A small vibration motor, so the device can signal without a screen or a speaker.

Plus a battery that lasts 16 hours and an enclosure small enough to wear. Target size is
51 × 21 × 11 mm and under 20 grams.

## 2. Where the project actually is

Blunt version: **the design work is real, the product has never been built.**

- No custom circuit board has ever been fabricated. Not one.
- Nothing has been physically tested. Every battery-life, storage and acoustic number in this
  repository is arithmetic on a page, not a measurement from a bench.
- There is a working proof unit built on an off-the-shelf dev board (see §4, "XIAO"), and firmware
  has genuinely run on it. That is the extent of what physically exists.
- Three different custom boards were started. None were finished.

What *is* strong: the process discipline. There are release gates, factory acceptance rules, an
end-of-line test specification, checksummed manifests and an explicit refusal to produce
fabrication files before the design is ready. That is unusually rigorous for this stage and worth
preserving.

## 3. How to get the files

```bash
git lfs install                                                          # once per machine
git clone https://github.com/anticipation-labs/anticipy-hardware.git
cd anticipy-hardware
shasum -a 256 -c 99_MANIFESTS/SHA256SUMS.txt | grep -v ': OK$'           # should print nothing
```

If you don't have Git LFS and don't want it, this still works and gets you everything except two
large superseded mesh files:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/anticipation-labs/anticipy-hardware.git
```

Install LFS with `brew install git-lfs` on macOS, or `apt install git-lfs` on Debian/Ubuntu.

**To open the files you'll actually care about:**

| Format | Open with |
|---|---|
| `.kicad_pcb`, `.kicad_sch`, `.kicad_pro` | [KiCad](https://www.kicad.org/) 7 or later, free |
| `.step`, `.stp` | Any CAD tool: Fusion 360, FreeCAD, SolidWorks, or macOS Preview for a quick look |
| `.stl`, `.3mf` | A slicer such as Bambu Studio, PrusaSlicer or Cura. `.3mf` files are pre-arranged print plates. |
| `.scad` | [OpenSCAD](https://openscad.org/), free. This is *parametric* source: change a number, regenerate the geometry. |
| `.uf2`, `.hex` | Firmware images. Don't flash anything yet, see §6. |
| `.dxf`, and the aluminium cap PDF | 2D drawings for a machinist |

## 4. Vocabulary

You will hit these constantly and nothing else explains them.

**Board names.** These are the four generations of custom circuit board, and the naming is the most
confusing thing in the project:

- **R0** is the first real custom board. It is the furthest along: 45 of its 46 signal nets have
  copper traces drawn, after 31 commits of routing work.
- **R0B** is a revision of R0, and it is the one the most recent package calls the "controlling
  checkpoint". It has **zero** copper traces on it. Nothing is routed. Despite the name suggesting
  progress, it is behind R0.
- **EVT-A** is a separate board from a late-August package built around a different processor.
  Superseded.
- **R1** is the current target. It does not exist. There is a brief and nothing else.

**Other terms:**

- **XIAO** is a Seeed Studio nRF52840 dev board with a microphone built in. It's the off-the-shelf
  part the working proof unit is built from. Not the product, but the only thing that runs today.
- **nRF52840 / nRF54L15 / ESP32-S3** are microcontrollers with built-in Bluetooth. The project has
  used all three at different points. See `CONTRADICTIONS.md` §1.
- **EVT** (Engineering Validation Test) is the first small batch of real boards, built to find
  design faults. The plan is three EVT units before any larger run.
- **DFM** (Design For Manufacture) is the factory's review that a design can actually be built.
  We're waiting on one right now, and it's blocking (§5).
- **DRC / ERC** are KiCad's automated design-rule and electrical-rule checks.
- **Gerber / ODB++ / drill / pick-and-place** are the output files a PCB factory needs. **We have
  none of these anywhere, deliberately.** Their absence is the correct state, not an oversight.
- **EOL test** (End Of Line) is the per-unit test run at the factory before a device ships.
- **UF2 / DFU** are firmware image formats and the over-the-air update mechanism.
- **PDM** is the digital interface the microphones use.
- **QSPI NOR vs serial NAND** are two different kinds of flash memory. This matters more than it
  sounds: NAND needs error correction, bad-block management and power-loss-safe writes in firmware.
  NOR doesn't. Swapping between them is real software work, not a BOM line change. Our current
  brief asks for NOR; our controlling board fits NAND.

## 5. The one thing on a clock

There is a live order at JLCPCB, a Chinese PCB fabricator, and it is stuck.

Order `W2026083114248171` / PCBA `SMT026083160845`. JLCPCB reported that part `C526821` did not
match the pads on our board and they couldn't assemble it. We asked for `C190799` as a
replacement. They said they'd proceed and asked us to wait.

Nobody has confirmed that the replacement part's footprint, pin-1 orientation or net mapping are
correct, and no final DFM has come back. Worse, the email record does not establish which version
of our KiCad files was actually uploaded, and there are two different files both called "R0".

**Do not let assembly be approved until someone competent checks the footprint against the final
DFM.** Full detail in [`../07_PROCUREMENT/JLCPCB_STATUS_2026-09-05.md`](../07_PROCUREMENT/JLCPCB_STATUS_2026-09-05.md).

## 6. Two traps to avoid in week one

**Don't trust a file called `anticipy.uf2`.** There is a firmware image formally classified
`UNVERIFIED_DO_NOT_FLASH` (sha256 `2e78015e…`, 624,640 bytes) sitting under that clean-looking name
in ten different working directories on Omar's machine, next to a build receipt that describes a
completely different 509,440-byte binary. Only use images from
[`../05_FIRMWARE/IMAGES/`](../05_FIRMWARE/IMAGES/), where every file is renamed by date and status.

**Don't build to the most convincing brief.** `01_CURRENT_TARGET_R1/` contains two briefs. The
longer, more detailed, more specific one (`Anticipy_PROD_R1_Flux_Build_Brief.md`) is **superseded**
and the original package never labelled it as such. The real requirement set is
`Anticipy_Hardware_Development_Brief_2026-09-04.md`. This trap already caught one reader.

## 7. Repository layout

Numbered so the reading order is forced. Fabrication-readiness is written into the folder names, so
nothing that isn't releasable sits in a path that reads as releasable.

| Folder | What it holds |
|---|---|
| `00_START_HERE/` | This file, plus current state, contradictions, glossary and provenance |
| `01_CURRENT_TARGET_R1/` | The live requirement set. Your assignment. |
| `02_PROTOTYPE_XIAO/` | The working proof unit: wiring, enclosure CAD, assembly evidence |
| `03_PCB/` | All four board generations, each in a status-marked folder |
| `04_MECHANICAL/` | Enclosure CAD, print plates, the one machinist drawing, superseded meshes |
| `05_FIRMWARE/` | Source, protocol and threat-model docs, images, device recovery kit |
| `06_FACTORY_AND_QA/` | Release process, QA fixtures, test evidence |
| `07_PROCUREMENT/` | BOMs, order sheets, the live JLCPCB status |
| `08_HISTORICAL_PACKAGES/` | All 15 original packages, byte-for-byte. Never edit. |
| `99_MANIFESTS/` | Checksums and a full file inventory |

Folders `01` through `07` are a curated working view. Folder `08` is the evidence. Every file in the
working view also exists in `08`, byte-identical. If they ever disagree, `08` is correct.

## 8. Suggested first week

1. Read [`HARDWARE_STATE.md`](HARDWARE_STATE.md), then [`CONTRADICTIONS.md`](CONTRADICTIONS.md).
   The second one is the important one. Seventeen places where our own documents disagree.
2. Deal with the JLCPCB order, or consciously decide to pause it.
3. Open R0 in KiCad (`03_PCB/R0_ROUTING_HISTORY_NOT_FOR_FAB/`) and R0B beside it, and work out
   whether R0B was a deliberate fresh start or a mistake. That decides whether weeks of routing
   work are banked or thrown away. The R0 folder also contains a custom autorouter someone wrote
   (`tools/route_board.py`) and a restorable 31-commit history in `R0_ROUTING_HISTORY.bundle`.
4. Decide NOR vs NAND vs managed NAND for storage, because it determines firmware scope.
5. Pick one enclosure lineage. Four exist. The OpenSCAD one in
   `04_MECHANICAL/OPENSCAD_SHELL_PROGRAM_v5.1/` is the only *parametric* source, so it's the only
   one that can be re-driven to a new size without starting over.
6. Look at the firmware haptics gap. We specify a haptic driver and motor; no firmware source tree
   contains any code that drives them.

## 9. Where this came from

Assembled 2026-09-06 from a sweep of every hardware file on one machine. 15 separate packages were
merged, because no single one was complete: the most recent package held only 74 of 411 unique CAD
and fabrication artifacts. Nothing was moved or deleted at source. Method and per-source
accounting in [`PROVENANCE.md`](PROVENANCE.md).
