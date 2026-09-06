# Provenance

Where every file in this repository came from, and how the consolidation was verified.

Assembled **2026-09-06** from a machine-wide audit of `/Users/omarebrahim`.

---

## Method

1. Swept the entire home directory for hardware-shaped files — by name (`pendant`, `hardware`,
   `firmware`, `pcb`, `kicad`, `gerber`, `bom`, `enclosure`, `xiao`, `nrf52`) and by extension
   (`.step .stl .3mf .stp .f3d .dxf .uf2 .hex .kicad_* .brd .sch`). 2,476 raw candidates.
2. Filtered false positives — language toolchains, package caches, video projects. 2,348 remained.
3. Isolated CAD/fab/firmware binaries: **572 files → 424 unique by SHA-256 content hash**, of which
   55 were 2–3 byte files named `.step` under `anticipy-web-claude/Anticipy/state/` (browser
   automation step counters, not CAD — excluded). **411 real unique artifacts.**
4. Hashed the master package and cross-referenced. Result below.
5. Copied all eight source packages verbatim into `08_HISTORICAL_PACKAGES/`, then built the
   curated `01`–`07` view from them.
6. Verified every source blob survived the copy.

## The finding that shaped this structure

Cross-referencing the 411 unique CAD/fab artifacts against the master package:

```
unique CAD/fab artifacts machine-wide : 411
  ...present in the master package     :  74
  ...existing ONLY outside it          : 337   (334.8 MB)
```

**The "master package" contained 18 % of the project's unique hardware artifacts.** It was the
most *recent* assembly, not the most *complete* one. That is why this repository consolidates
eight packages rather than adopting one.

Exclusive content per source — blobs found in that package and nowhere else:

| Source | Files | Size | Blobs found **only** here |
|---|---:|---:|---:|
| `execution_v1.0` | 505 | 53.4 MB | **243** |
| `master_package` | 218 | 36.5 MB | 190 |
| `v07_four_day_build_pack` | 298 | 9.4 MB | 77 |
| `tuesday_evt_v0.1` | 295 | 11.4 MB | 40 |
| `pendant_device_restore` | 44 | 9.6 MB | 29 |
| `48h_v13` | 283 | 10.0 MB | 26 |
| `r0_kicad_with_git_history` | 25 | 1.0 MB | 14 |
| `firmware_dev_not_for_flash` | 23 | 8.3 MB | 10 |

`execution_v1.0` holds more exclusive content than the master package. Discarding it in favour of
the newer package would have lost the entire factory release process, the QA fixture set and the
only real firmware source tree.

---

## Source map

| Archived as | Original location |
|---|---|
| `08_.../2026-09-05_master_package` | `~/Downloads/Anticipy_Hardware_Master_Package_2026-09-05` |
| `08_.../2026-08-29_r0_kicad_with_git_history` | `~/Downloads/Anticipy_PROD_R0_EVT_KiCad` |
| `08_.../2026-08-28_execution_v1.0` | `~/Downloads/Anticipy_Execution_v1.0` |
| `08_.../2026-08-28_tuesday_evt_v0.1` | `~/Downloads/Anticipy_Tuesday_EVT_v0.1` |
| `08_.../2026-08-28_48h_v13` | `~/Downloads/Anticipy_48h_v13` |
| `08_.../2026-08-27_v07_four_day_build_pack` | `~/Downloads/Anticipy_v07_four_day_complete_build_pack` |
| `08_.../2026-07-24_pendant_device_restore` | `~/anticipy-pendant-restore` |
| `08_.../2026-07-23_firmware_dev_not_for_flash` | `~/Downloads/Anticipy-Firmware-Development-NOT-FOR-FLASH-20260723-437dc9e3` |
| `05_FIRMWARE/DOCS/` | `~/Anticipy-0707/firmware` (README, BUILD, PROTOCOL, THREAT-MODEL, upstream.lock.json, protocol/, development-receipts/) |
| `04_MECHANICAL/SUPERSEDED_AND_MOCKUPS/` | loose files in `~/Downloads`, `~/Desktop`, `~/Documents` |
| `07_PROCUREMENT/*.pdf`, `*.docx` | loose files in `~/Downloads` |

**Nothing was moved or deleted.** Every original remains where it was; this repository holds copies.

## Notes on specific sources

- **`Anticipy_v07_four_day_complete_build_pack`** existed twice in Downloads (the second as
  `… 2`). The two were byte-identical apart from a `.DS_Store`. Only one was archived.
- **`Anticipy_Hardware_Master_Package_2026-09-05.zip`** and `… (1).zip` are byte-identical
  (`sha256 d39a1a00866b90885c4270016ad78ee5b4a191c5d33cdcece0909b2117a60c32`). The extracted
  folder already in Downloads matched the zip exactly — 218 files, no discrepancy.
- **`2026-08-29_r0_kicad_with_git_history`** retains its `.git` directory — 31 commits, branch
  `main`, **no remote**. This is the only version-controlled hardware artifact found on the machine
  and its history existed nowhere else. It also had uncommitted changes to `.kicad_pcb`,
  `.kicad_pro` and an untracked `tools/final_build.py`; these were preserved as-is, uncommitted.
- **`CURRENT-from-device-20260724.uf2`** was pulled off a physical device. It is the only
  artifact here that is evidence of what actually ran on hardware.

---

## Integrity verification

```
source unique blobs   : 908
archived unique blobs : 908
missing from archive  :   0
```

The consolidated repository holds **2,489 files / 953 unique blobs**. Files outnumber blobs
because `01`–`07` is a curated view over the same content archived in `08`.

Re-verify at any time:

```bash
cd ~/Anticipy-Hardware && shasum -a 256 -c 99_MANIFESTS/SHA256SUMS.txt
```

## What was deliberately excluded

- `~/anticipation-builds` (6.4 GB, 124,989 files) — a Zephyr/nRF Connect SDK **build tree**, not an
  archive. The distinct firmware images it contained were extracted into `05_FIRMWARE/IMAGES/`;
  the toolchain, checkouts and intermediate objects were not copied.
- `~/Anticipy-0707/firmware/.build` and `.cache` — build output and a vendored copy of
  `BasedHardware/omi`, reproducible from `upstream.lock.json`.
- Nordic SDK, Zephyr board-support and Arduino bootloader `.hex` files found inside those trees —
  third-party toolchain artifacts, not Anticipy firmware.
- 55 files named `.step` under `~/anticipy-web-claude/Anticipy/state/` — browser-automation step
  counters that matched the CAD extension filter by coincidence.
