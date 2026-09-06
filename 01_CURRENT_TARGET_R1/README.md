# 01 — Current target (R1)

**Status: brief only. This board does not exist yet.**

This is the live requirement set, dated **2026-09-04** — the newest hardware documents on the
machine. Everything else in this repository is either a prototype, a superseded design, or history.

## What is here

| File | What it is |
|---|---|
| `Anticipy_Hardware_Development_Brief_2026-09-04.md` / `.docx` | The assignment given to the incoming hardware engineer |
| `Anticipy_PROD_R1_Flux_Build_Brief.md` | The R1 board brief: parts, rails, pin-map rules, layout constraints, acceptance gates |
| `Anticipy_Hardware_CAD_Brief_v1.pdf` | Mechanical CAD brief |
| `Anticipy_Full_Handoff_Guide.pdf` | Handoff guide |
| `HARDWARE_SYSTEM_MAP.md` | One-page system block diagram |

## The target in one table

| | |
|---|---|
| MCU / BLE | Raytac `MDBT50Q-1MV2` (nRF52840), pre-certified module |
| Microphones | 2 × Infineon `IM69D128SV01XTMA1`, 3 V PDM, 69 dB SNR |
| Battery | 1-cell protected LiPo, **250–300 mAh**, 10 kΩ NTC lead |
| Storage goal | ≥ 20 hours offline audio (414 MB) |
| Runtime goal | 16 hours — needs measured average < 12.5 mA on a 200 mAh cell |
| PCB envelope | 49.0 × 20.0 × 0.8 mm preliminary |
| Enclosure | 56.0 × 23.0 × 12.0 mm finished |
| Batch | 25-unit pilot, then 100 units. Founder units stay on XIAO. |

## Before you build to this

Two things in this folder conflict with the rest of the repository:

1. **The processor.** This brief says nRF52840. The most complete package on disk
   (`08_HISTORICAL_PACKAGES/2026-08-28_execution_v1.0`) is built around nRF54L15. No document
   records the decision to revert.
2. **The enclosure size.** 56.0 × 23.0 × 12.0 mm here versus 50.5 × 20.68 × 10.8 mm in
   Execution v1.0 — against which all 23/23 mechanical checks were run.

See [`../00_START_HERE/CONTRADICTIONS.md`](../00_START_HERE/CONTRADICTIONS.md).
