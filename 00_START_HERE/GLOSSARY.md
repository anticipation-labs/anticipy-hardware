# Glossary

Names that appear across these files without ever being defined in one place.

---

## Board revisions

| Term | Meaning |
|---|---|
| **R0** / `ANT-PROD-R0 EVT` | The first custom Anticipy board. KiCad project `Anticipy_PROD_R0_EVT`. Has 31 commits of routing history (v21 → v43) driving unconnected nets from 199 down to 23 non-GND. |
| **R0B** | Revision B of R0. 45.8 × 18.0 mm, four-layer, nominal 0.80 mm. 70 electrical references, 223 source-of-truth pins, 176 connections unrouted. The master package's headline board. |
| **EVT-A** / `anticipy_evt_a` | A separate board from the 2026-08-28 Execution package, targeting nRF54L15. Deliberately held at zero copper (0 segments, 0 vias, 0 zones) so no misleading Gerbers could be produced. |
| **R1** | The current target board. **Does not exist yet** — a brief only. Sometimes written "Anticipy Production PCB R1" or "R1 Flux". |
| **EVT** | Engineering Validation Test — the first small build of real boards used to find design faults. Anticipy's plan is three EVT units before any larger lot. |
| **P2S** | A print plate naming prefix used in the mechanical files (e.g. `P2S_v07_nopcb_retained.3mf`, `P2S_plate_3_51mm_mechanical_fit.3mf`). |

## Build packages

Each was a self-contained handoff produced on a given date. All eight are preserved verbatim in
`08_HISTORICAL_PACKAGES/`.

| Package | Date | What it was for |
|---|---|---|
| `firmware_dev_not_for_flash` | 2026-07-23 | Firmware development artifacts, explicitly marked not to flash |
| `pendant_device_restore` | 2026-07-24 | Recovery images, including one pulled **off a live device** |
| `v07_four_day_build_pack` | 2026-08-27 | Four-day build: order sheet, wiring card, mechanical, firmware |
| `48h_v13` | 2026-08-28 | 48-hour sprint: print files, guides, lab-only firmware |
| `tuesday_evt_v0.1` | 2026-08-28 | "Tuesday" EVT attempt: strict EVT plates, aluminium template, cost ceiling |
| `execution_v1.0` | 2026-08-28 | **The most complete package.** Production CAD, EVT-A PCB, firmware source, QA fixtures, factory release process |
| `r0_kicad_with_git_history` | 2026-08-29 | The R0 KiCad project *with its git history* — the routing record |
| `master_package` | 2026-09-05 | The most recent assembly; leads with the R1 brief and the R0B checkpoint |

## Hardware parts

| Term | Meaning |
|---|---|
| **XIAO nRF52840 Sense** | Seeed Studio dev board used for the proof/Founder units. Has an onboard PDM microphone. Not the production part. |
| **Raytac MDBT50Q-1MV2** | Pre-certified nRF52840 module specified by the R1 brief. |
| **Raytac AN54LV-15** | Pre-certified nRF54L15 module specified by Execution v1.0. See `CONTRADICTIONS.md` #1. |
| **nPM1300** | Nordic power-management IC — charger and power path. |
| **DRV2605L** | TI haptic driver. Note its A2/REG pin is a **1.8 V regulator output** needing its own 1 µF bypass — it is **not** the 3V0 rail. This is a recorded red-list correction. |
| **IM69D128S** | Infineon PDM microphone, 69 dB SNR, 3 V compatible (avoids 1.8 V level translation). |
| **MKDV4GCL-ABF** | MK Founder 4-Gbit managed SD NAND. Exposes ~481 MB usable against a 414 MB requirement. |
| **VC0720B015F** | Vybronics wired vibration motor. |
| **PTS841** | C&K / Littelfuse side button. |
| **"No-Lee's" reference** | The name used for the reference haptic wiring diagram for the XIAO build. |

## Process and status terms

| Term | Meaning |
|---|---|
| **DFM** | Design For Manufacture — the fab's review that a design can actually be built. The live JLCPCB order is waiting on one. |
| **DRC / ERC** | Design Rule Check / Electrical Rule Check — KiCad's automated correctness passes. |
| **EOL test** | End Of Line test — the per-unit test run at the factory before a unit ships. Spec is in `06_FACTORY_AND_QA/FACTORY_RELEASE_PROCESS/EOL_TEST_SPEC.md`. |
| **Lot stop** | A rule that halts an entire production batch when a defect rate is exceeded. |
| **Traveler** | The per-unit record that follows a device through assembly, capturing who did what. |
| **`NOT_FOR_FAB`** | Path marker: this design must not be sent to a fabricator as a production release. |
| **`HOLD_FOR_PHYSICAL_RELEASE_TEST`** | Filename marker: this firmware is awaiting physical validation and must not ship. |
| **`LAB_ONLY`** | Filename marker: for bench use on a development unit, not a customer device. |
| **Green / Yellow / Red** | Execution v1.0's status scheme — green = digitally verified, yellow = engineering candidate, red = must close before fabrication. |

## Units and numbers worth memorising

- **414 MB** — offline audio storage required for 20 hours (`5,000 B/s × 72,000 s × 1.15`)
- **481 MB** — usable capacity of the candidate 4-Gbit managed NAND
- **12.5 mA** — average current a 200 mAh cell can sustain for 16 h before derating
- **10.625 mA** — the same figure with 85 % derating applied
- **50.500 × 20.680 × 10.800 mm** — Execution v1.0 production envelope
- **56.0 × 23.0 × 12.0 mm** — R1 brief finished enclosure (these conflict; see `CONTRADICTIONS.md` #2)
