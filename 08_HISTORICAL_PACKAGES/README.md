# 08 — Historical packages

**Do not edit anything in this folder.** It is the provenance record. Every file in `01`–`07` also
exists here, byte-identical. If the curated view and this archive ever disagree, this archive wins.

Fifteen sources, preserved verbatim as found on 2026-09-06.

| Folder | Date | What it was |
|---|---|---|
| `00_ORIGINAL_ZIPS/` | — | The original `.zip` deliverables, sealed and unextracted |
| `2026-04_esp32s3_prior_generation/` | 2026-04/05 | **The prior hardware generation.** XIAO ESP32-S3 + INMP441 + TP4056. KiCad schematic, OpenSCAD enclosure, pin map, assembly guide, and the **only packaging spec and manufacturing-order document in the whole audit**. |
| `2026-07-23_firmware_dev_not_for_flash/` | 2026-07-23 | Firmware development artifacts, marked not-for-flash |
| `2026-07-24_pendant_device_restore/` | 2026-07-24 | Restore kit incl. an image read **off a live device**, resolved devicetree, five on-air BLE logs |
| `2026-07-24_pendant_recovery_images/` | 2026-07-24 | The A/B recovery pair built to test the 32.768 kHz crystal hypothesis |
| `2026-07-24_dual_hatch_builds/` | 2026-07-24 | Build receipts, logs, source and DFU packages for the four dual-hatch variants |
| `2026-08-19_anticipy_shell_openscad/` | 2026-08-19 | The parametric OpenSCAD enclosure program, v1 → v5.1 |
| `2026-08-19_anticipy_design_ds_bundle/` | 2026-08-19 | Design-system bundle incl. the XIAO hardware spec |
| `2026-08-27_v07_four_day_build_pack/` | 2026-08-27 | Four-day build: order sheet, wiring card, mechanical, firmware |
| `2026-08-28_48h_v13/` | 2026-08-28 | 48-hour sprint: print files, guides, lab-only firmware |
| `2026-08-28_tuesday_evt_v0.1/` | 2026-08-28 | Strict EVT plates, aluminium template, cost ceiling, release gates |
| `2026-08-28_execution_v1.0/` | 2026-08-28 | **The most complete package.** Production CAD, EVT-A PCB, firmware source, QA fixtures, factory release process |
| `2026-08-29_r0_kicad_with_git_history/` | 2026-08-29 | The R0 KiCad project **with its 31-commit routing history**. No remote — this was the only copy. |
| `2026-08-28_p2s_v07_enclosure/` | 2026-08-28 | The P2S_v07 enclosure generation and a 50.5 × 20.5 mm production layout concept |
| `2026_firmware_provenance_lane/` | 2026 | The authoritative firmware provenance and safety track: protocol, threat model, build spec, upstream patches, SBOM tooling, quarantine record |
| `2026-09-05_master_package/` | 2026-09-05 | The most recent assembly; leads with the R1 brief and the R0B checkpoint |

## Why fifteen and not one

The 2026-09-05 "master package" was the newest assembly, but not the most complete. Measured by
SHA-256 across every unique CAD/fab artifact on the machine:

```
unique CAD/fab artifacts machine-wide : 411
  present in the master package        :  74   (18 %)
  existing only outside it             : 337
```

`execution_v1.0` alone holds **243 blobs found nowhere else** — more than the master package's 190.
Adopting the newest package as the archive would have discarded the entire factory release
process, the QA fixture set, the only machinist drawing pair, and the only real firmware source
tree.

## Duplicates resolved during consolidation

- `Anticipy_v07_four_day_complete_build_pack` existed twice in Downloads; the copies were
  byte-identical apart from a `.DS_Store`. One archived.
- `Anticipy_Hardware_Master_Package_2026-09-05.zip` and `… (1).zip` are byte-identical
  (`sha256 d39a1a00…`). The already-extracted folder matched the zip exactly.
- One firmware binary (`anticipy.uf2`) had 21 copies scattered across the machine; `anticipy.hex`
  had 15. One of each was kept, in `../05_FIRMWARE/IMAGES/`.
