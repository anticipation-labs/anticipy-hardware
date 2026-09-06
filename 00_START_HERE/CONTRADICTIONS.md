# Contradictions

Seventeen places where two documents in this repository disagree. Each is stated with both sources so you
can judge for yourself. **Read this before acting on any single document.**

Every path below is relative to the repository root.

---

## 1. Which processor? nRF52840 vs nRF54L15

This is the most consequential disagreement, because it changes the module, the firmware, the
pin map and the certification path.

**The 2026-08-28 Execution package** commits to a next-generation part:

> Raytac AN54LV-15 pre-certified **nRF54L15** radio module
> — `08_HISTORICAL_PACKAGES/2026-08-28_execution_v1.0/RELEASE_STATUS.md`

> Build and compile the production **nRF54L15** firmware and iPhone client; the supplied
> nRF52840 UF2 is for the larger lab unit.
> — same file, red-list item 8

**The 2026-09-04 R1 brief** — seven days newer — specifies the previous generation:

> | MCU and Bluetooth | Raytac `MDBT50Q-1MV2` | **nRF52840**, integrated antenna, USB, PDM,
> QSPI/SPI, pre-certified module, same MCU family as Founder unit |
> — `01_CURRENT_TARGET_R1/Anticipy_PROD_R1_Flux_Build_Brief.md:52`

> Keep the **nRF52840** software family for the first custom board
> — `01_CURRENT_TARGET_R1/Anticipy_Hardware_Development_Brief_2026-09-04.md:145`

**But the MDBT50Q line comes from a superseded document.** The R1 Flux brief is explicitly
excluded from the active handoff (see §15). The *actual* current brief — Rev 1, 2026-09-04 — does
**not** lock a module at all:

> **MCU + BLE:** nRF52840-compatible starting point
> **MCU implementation:** nRF52840 module vs. bare SoC vs. another — listed as an *open question*
> — `01_CURRENT_TARGET_R1/Anticipy_Hardware_Development_Brief_2026-09-04.md:158, :487`

**Assessment:** the current position is "nRF52840-compatible family, part not yet chosen". The
nRF54L15 of Execution v1.0 is out; the specific Raytac MDBT50Q-1MV2 was never actually locked —
it was one superseded brief's proposal. **No document records the decision to leave nRF54L15.**

**Action:** write the decision down, and treat the module choice as genuinely open.

---

## 2. Which enclosure envelope?

**Four** envelopes are on record:

| Source | Envelope | Date | Standing |
|---|---|---|---|
| `01_CURRENT_TARGET_R1/Anticipy_Hardware_Development_Brief_2026-09-04.md:112` | **51 × 21 × 11 mm**, ≤ 20 g, +10 %/axis cap | 2026-09-04 | **Current** |
| `08_HISTORICAL_PACKAGES/2026-08-28_execution_v1.0/RELEASE_STATUS.md` | **50.500 × 20.680 × 10.800 mm** — 23/23 mechanical checks passed against this | 2026-08-28 | Superseded design line |
| `01_CURRENT_TARGET_R1/Anticipy_PROD_R1_Flux_Build_Brief.md:137` | **56.0 × 23.0 × 12.0 mm** enclosure; PCB 49.0 × 20.0 × 0.8 mm | 2026-08-29 | **Explicitly superseded** (§15) |
| `04_MECHANICAL/OPENSCAD_SHELL_PROGRAM_v5.1/` | **26.5 × 61.2 × 12.6 mm** flat pill tag | 2026-08-19 | Different form factor entirely |

The good news: the current 51 × 21 × 11 mm and Execution v1.0's 50.5 × 20.68 × 10.8 mm are close
enough that the production CAD is **plausibly reusable** — it sits inside the +10 %/axis tolerance.
The 56 × 23 × 12 mm figure that looks like the newest target is from the superseded Flux brief and
should be ignored.

**Consequence:** every STL and STEP in `04_MECHANICAL/REFERENCE_STEP/` was validated against
50.5 × 20.68 × 10.8. If R1's 56 × 23 × 12 is the real target, that CAD is **not** the production
geometry and its pass results are stale.

---

## 3. Which battery?

| Source | Capacity |
|---|---|
| Execution v1.0 (`RELEASE_STATUS.md`, yellow list) | **200 mAh** meeting the controlled maximum pack drawing |
| R1 brief (`:23`) | 1-cell protected LiPo, target **250 to 300 mAh**, 10 kΩ NTC lead |

**Not a contradiction:** the current-draw figures are consistent. R1 says a 200 mAh cell needs
`< 12.5 mA` average for 16 hours "before conversion and aging margin"; Execution says `≤ 10.625 mA`
— which is exactly 12.5 mA × 0.85, i.e. the same number with an 85 % derating applied. The two
documents agree on the physics and differ only on the chosen cell.

**But** the larger 250–300 mAh cell will not fit the smaller 50.5 × 20.68 × 10.8 envelope
without rework, which ties this to contradiction #2.

---

## 4. Two different R0 board files, both called R0

The master package ships a copy of the R0 KiCad board that is **not** the same file as the one in
the R0 git repository.

| | Master package copy | Git repository HEAD |
|---|---|---|
| Path | `03_PCB/R0_ROUTING_HISTORY_NOT_FOR_FAB/` is the git one; the master copy is at `08_HISTORICAL_PACKAGES/2026-09-05_master_package/05_OLDER_R0_KICAD_NOT_FOR_FAB/` | `08_HISTORICAL_PACKAGES/2026-08-29_r0_kicad_with_git_history/` |
| `.kicad_pcb` sha256 | `64a4931f0fc455cd…` | `c086bae9fedc9a55…` |
| DRC report timestamp | 2026-08-30 **02:28:59** | 2026-08-29 **18:04:35** |
| DRC violations | **134** | **4** |

The master package's copy was generated ~8 hours later and reports 134 violations against the git
version's 4. The DRC header in the master copy also references a sandbox path
(`/workspace/scratch/295a51172f48/…`), so it was produced by an automated run, not from this repo.

**Consequence:** "the R0 board" is ambiguous. If someone uploads "R0" to a fab, which file did
they send? This matters directly for the live JLCPCB order, where *"the email record does not
prove which local KiCad revision was uploaded"*.

---

## 5. Routing progress is stated backwards

The master package leads with R0B as the current engineering checkpoint and reports:

> the R0B PCB still reports **176 unconnected pads**
> — `08_HISTORICAL_PACKAGES/2026-09-05_master_package/00_READ_ME_FIRST.md`

But the R0 git history ends at:

> `v43: GND 36, non-GND 23`
> — `08_HISTORICAL_PACKAGES/2026-08-29_r0_kicad_with_git_history`, commit `496785f`

with a documented descent from 199 → 23 non-GND unconnected across commits v21–v43.

So the board the master package treats as *older and superseded* (R0) is **substantially further
routed** than the board it presents as the current checkpoint (R0B). Either R0B is a fresh
re-spin that discarded R0's routing work, or the master package's framing is wrong. Nothing in
the package explains which.

---

## 6. Version numbering is not monotonic

Firmware images in `05_FIRMWARE/IMAGES/`, by date:

| Date | Version label |
|---|---|
| 2026-07-23 | `anticipy-v2.0.1` (candidate build) |
| 2026-08-28 | `Anticipy_Founder_EVT_v0.9.0` |
| 2026-09-04 | `Anticipy_0.9.3_owner2_live_50mA` |

Version `2.0.1` predates `0.9.0` by five weeks. The `2.0.x` numbers appear to be inherited from
the upstream Omi firmware (`omi_dk2_2.0.10.uf2` is present in `~/Anticipy`), while `0.9.x` is
Anticipy's own scheme. Nothing states this. Anyone sorting by version number will pick the wrong
image.

---

## 7. Three parallel enclosure designs, all "current"

The processor split has a mechanical twin, and it is worse because the three designs are different
*form factors*, not variants:

| Lineage | Size | Source | Location |
|---|---|---|---|
| Ordered-shell recovery v0.2 | 51 × 22 × 14.5 mm body + 4.50 mm midband | Python recovery script | `02_PROTOTYPE_XIAO/CAD/` |
| `anticipy-shell` v5.1 | **26.5 × 61.2 × 12.6 mm** flat pill tag (33.4 × 80.7 × 16.2 mm storage build) | Parametric OpenSCAD | `04_MECHANICAL/OPENSCAD_SHELL_PROGRAM_v5.1/` |
| Execution v1.0 production CAD | **50.500 × 20.680 × 10.800 mm** | — | `04_MECHANICAL/REFERENCE_STEP/` |
| R1 brief | **56.0 × 23.0 × 12.0 mm** | — | `01_CURRENT_TARGET_R1/` |

A 26.5 × 61.2 mm flat tag and a 50.5 × 20.68 mm pebble are not the same product. The OpenSCAD
program is the only *parametric* source — the one design that could actually be re-driven to a new
envelope — and it was sitting loose on the Desktop, in none of the eight packages.

**Nobody has written down which enclosure is current.**

## 8. The firmware cannot drive the haptics

Haptics are a core product behaviour and a specified BOM line (TI `DRV2605L` driver + Vybronics
`VC0720B015F` motor). The XIAO reference even documents the exact MOSFET circuit.

But a grep across **all five firmware source trees** returns no haptic support, and every dual-hatch
build receipt records `haptic_support_added: false`.

The hardware is specified. The software to use it does not exist. Nothing in any hardware package
flags this.

## 9. The newest firmware has no source

The master package ships `Anticipy_0.9.3_owner2_live_50mA.uf2` (sha `f246fc79…`, 528,384 bytes,
NCS v2.7.0) as the reference XIAO image.

That hash appears nowhere else on the machine, and **no source tree that could produce it was
found**. The firmware lines that do have source (`anticipy-v2.0.1` → dual-hatch, NCS v2.5.0) are a
different lineage entirely — a grep of the master package for `dual-hatch`, `anticipy-v2.0.1`,
`GPREGRET`, `recovery_usb` or `1200 baud` returns zero files.

Two disconnected firmware lines exist and no document reconciles them.

## 10. Upstream lineage is undeclared

Anticipy firmware is a fork of **BasedHardware/omi** — `v2.0.1-Omi`, commit
`ee9892562648f074e3c6b59d508127d81fa21010`, path `Friend/firmware/firmware_v1.0` — and it vendors
Opus 1.2.1.

This is recorded only in `05_FIRMWARE/DOCS/upstream.lock.json` and `BUILD.md`, which came from a
firmware tree outside every hardware package. **No hardware package mentions it.** It carries
attribution and licensing obligations that should be stated wherever the firmware ships.

## 11. Loose ends that were never closed

- **The crystal test was never run.** The entire A/B recovery pair
  (`05_FIRMWARE/DEVICE_RECOVERY/ab_recovery_images_20260724/`) exists to answer one question — is
  the 32.768 kHz crystal dead? No result file, log or follow-up build exists anywhere.
- **Nothing was ever flashed.** Every build receipt in the dual-hatch line records
  `flash_performed: false` and `device-flash-evidence/` is empty.
- **USB VID/PID are Zephyr test defaults** (`0x2FE3` / `0x100`). Real identifiers are needed before
  shipping.
- **The `secure` dual-hatch variant** is the most production-appropriate (encrypted, bonded DFU
  control point) but is the only one with no build receipt and no OTA package.
- **A glued shell versus DFU recovery.** The enclosure is designed to be permanently glued; firmware
  recovery depends on 1200-baud USB touch and BLE DFU. If the radio fails inside a sealed unit,
  there is no documented way in.

## 12. A whole prior hardware generation is missing from the record

Before the nRF52840 line there was an **ESP32-S3 pendant**, designed April–May 2026:

- XIAO ESP32-S3 + INMP441 I2S MEMS microphone
- TP4056 / DW01A charger, LP402035 400 mAh LiPo, SK6812 indicator LED
- 40 × 25 mm two-layer 1.0 mm FR4, black HASL
- 38 × 25 × 11 mm, 18 g PETG enclosure

It has a KiCad schematic, a parametric OpenSCAD enclosure, a pin map, a hand-solder assembly guide
with QA checklist, a **packaging specification**, a JLCPCB/PCBWay ordering guide, and a BOM with
live supplier links and three volume pricing tiers.

Grepping the entire master package — every folder and all five source-archive zips — for `esp32`,
`inmp441`, `tp4056` or `sk6812` returns **zero hits**. The hardware record simply begins at the
nRF52840 line as if nothing preceded it.

It is correctly **superseded** and must never go to a fab as the current product. But it contains
two things that exist nowhere else in the entire audit:

- the **only packaging specification** on the machine
- the **only manufacturing-order / supplier-routing document** on the machine

Archived at `08_HISTORICAL_PACKAGES/2026-04_esp32s3_prior_generation/`.

## 13. The investor material describes a different device

The investor-facing exploded render specifies a **Nordic nRF5340** — a fifth processor, matching
none of the engineering artefacts (which use nRF52840/Raytac MDBT50Q, with nRF54L15 in Execution
v1.0 and ESP32-S3 in the prior generation).

It also describes the product as *"seamless & sealed, no ports"*. Every documented firmware
recovery path depends on a USB port: 1200-baud touch, and the DFU flows in
`05_FIRMWARE/DEVICE_RECOVERY/`. A sealed, portless device cannot be recovered by any method
currently on record.

Separately, the August 2026 Use of Funds — the only staged production plan on disk — quotes
**3,000 units at $60**, Bluetooth SIG $12K, FCC/ISED $10K, UN 38.3 $3K and a $20K tooling reserve.
Its own footnote states the $60 figure is *"pending a final supplier quotation"*, and the FCC/ISED
line is marked *"lab quote pending"*. No supplier quotation was found anywhere in the audit.

## 14. SAFETY: a quarantined image is circulating under a clean label

`anticipation-lanes` formally classifies one firmware image as **`UNVERIFIED_DO_NOT_FLASH`**
(sha256 `2e78015e…`, 624,640 bytes).

That exact image is present as `firmware/anticipy.uf2` in **all ten AnticipyFleet lanes**, under a
clean release-looking name with no quarantine marker.

Worse, `desk/firmware/BUILD_RECEIPT.json` describes a **509,440-byte** image (sha `f1c9011a…`),
but the `anticipy.uf2` sitting beside it in the same directory is the **624,640-byte quarantined
one**. The receipt does not describe the file it ships with.

**Anyone who flashes `anticipy.uf2` from a fleet lane, trusting its build receipt, flashes an image
formally marked do-not-flash.** Rename or remove those copies.

## 15. A superseded brief is filed as a current requirement

`01_CURRENT_TARGET_R1/Anticipy_PROD_R1_Flux_Build_Brief.md` sits in the folder the package tells
the engineer to read first, with no supersession banner. But the same package says elsewhere:

> The earlier Flux build brief, R0A source tree, **49 x 20 mm layout**, removable **microSD**
> concept, and all experimental autorouter outputs are deliberately excluded from the active
> handoff.
> — `.../04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/99_Superseded_Notice/SUPERSEDED_FILES_NOTICE.md`

The Flux brief *is* that brief, with that layout and that microSD concept. Anyone reading
`01_CURRENT_REQUIREMENTS` top-to-bottom builds the wrong device.

The same notice names the controlling checkpoint: **`ANT-PROD-R0B`, 45.8 × 18.0 mm, soldered NAND
storage**, with explicit fabrication blockers.

## 16. Storage technology is stated three different ways

| Source | Storage |
|---|---|
| Current brief (2026-09-04) | **QSPI NOR flash**, plan 512 MB |
| R0B BOM (the controlling checkpoint) | **Macronix MX35LF4GE4AD-Z4I** — 4-Gbit SLC serial **NAND**, needing ECC, bad-block and power-loss handling |
| `HARDWARE_SYSTEM_MAP.md` | "Local QSPI flash" |
| Flux brief (superseded) | Removable **microSD** socket + 8/16 GB card |
| Execution v1.0 | MK Founder **MKDV4GCL-ABF** managed SD NAND, ~481 MB usable |

NOR and NAND are not interchangeable. NAND needs an ECC layer, bad-block management and
power-loss-safe writes that NOR does not — that is firmware work, not a part swap. The current
brief asks for NOR; the controlling board fits NAND. And `03_XIAO_ALL_CAD/ARCHITECTURE_OPTIONS.md`
contains a section titled **"Why no microSD"**, directly contradicting the Flux brief beside it.

## 17. R0B is not partially routed — it has no copper at all

The master package describes R0B as having "176 unconnected pads", which reads like a board that
is mostly routed with 176 connections left.

It is not. `grep -c '(segment'` on `R0B.kicad_pcb` returns **0**. There are zero track segments on
the board. Nothing has been routed.

This makes the R0-versus-R0B ordering (§5) starker: R0 has 45 of 46 signal nets carrying copper
after 31 commits of routing work; R0B, the "controlling checkpoint", has none.

---

## Summary of what to fix

1. Write down the nRF52840-vs-nRF54L15 decision and its reason.
2. Pick one enclosure envelope and re-run or retire the mechanical verification.
3. Establish which R0 `.kicad_pcb` is canonical, and record which file went to JLCPCB.
4. Explain the R0 → R0B relationship, or fold R0's routing back in.
5. Adopt one firmware version scheme and stop inheriting upstream numbers.
6. Resolve the live JLCPCB part substitution before assembly is approved.
7. Pick one enclosure lineage; prefer the parametric OpenSCAD source, which can be re-driven.
8. Add haptic support to the firmware, or stop specifying a haptic driver and motor.
9. Find or rebuild the source for the 0.9.3 image, or stop treating it as the reference.
10. Declare the BasedHardware/omi fork and Opus vendoring wherever the firmware ships.
11. Run the crystal A/B test, or delete the recovery pair and stop citing it.
12. Fold the ESP32-S3 generation's packaging spec and manufacturing-order guide into the current
    record — they are the only ones that exist.
13. Reconcile the investor render (nRF5340, "sealed, no ports") with engineering reality, and get
    the supplier quotation the $60 unit cost depends on.
14. **Immediately** rename or remove the `UNVERIFIED_DO_NOT_FLASH` image from the ten fleet lanes.
15. Move the Flux brief out of `01_CURRENT_TARGET_R1/` or banner it, so nobody builds to a
    superseded 49 × 20 mm microSD design.
16. Decide NOR vs NAND vs managed NAND. It determines real firmware work, not just a BOM line.
17. Stop describing R0B as "176 unrouted" — it has zero copper. Either route it or start from R0.
