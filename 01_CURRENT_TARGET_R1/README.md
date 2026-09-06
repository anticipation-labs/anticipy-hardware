# 01 — Current target (R1)

**Status: brief only. This board does not exist yet.**

> ### ⚠️ One file in this folder is superseded and is not marked as such
>
> `Anticipy_PROD_R1_Flux_Build_Brief.md` (2026-08-29) is **NOT the current requirement set**,
> despite sitting in a folder called "current requirements". The master package's own supersession
> notice says so explicitly:
>
> > The earlier Flux build brief, R0A source tree, 49 x 20 mm layout, removable microSD concept,
> > and all experimental autorouter outputs are **deliberately excluded from the active handoff**.
> > — `08_HISTORICAL_PACKAGES/2026-09-05_master_package/04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/99_Superseded_Notice/SUPERSEDED_FILES_NOTICE.md`
>
> The Flux brief is exactly that brief, with exactly that 49 × 20 mm layout and that microSD
> concept. It carries no supersession banner of its own. It is kept here because it is the most
> detailed electrical brief on record and much of it is still useful — but **every number in it
> must be checked against the Rev 1 brief below before use.**

## The actual current requirement set

**`Anticipy_Hardware_Development_Brief_2026-09-04.md` / `.docx`** — "Custom PCB and investor-ready
metal wearable | Rev 1 | September 4, 2026". This is the assignment.

| | |
|---|---|
| Size | **51 × 21 × 11 mm** target. Do not exceed +10 % per axis without written approval. |
| Weight | **≤ 20 g** target. Flag any design above 25 g before fabrication. |
| Battery | 16 h runtime |
| Local storage | **QSPI NOR flash**, sized from the actual codec. Plan **512 MB**. |
| Offline capacity | 16–20 h |
| Connectivity | BLE live audio, commands, status, reconnect, **ordered backfill** |
| Haptics | App can command a short, discreet vibration |
| MCU | **Not locked.** "nRF52840-compatible starting point"; module vs bare SoC is listed as an *open question* |
| Programming | SWD access, serial identity, test pads |

Delivery is staged through **Checkpoints A/B/C/D** with per-unit acceptance gates and defined stop
conditions — all specified in the brief itself.

## Files here

| File | Status |
|---|---|
| `Anticipy_Hardware_Development_Brief_2026-09-04.md` / `.docx` | **Current.** The `.docx` is the original; the `.md` is a faithful conversion for grepping. |
| `Anticipy_PROD_R1_Flux_Build_Brief.md` | **Superseded** — see banner above |
| `Anticipy_Hardware_CAD_Brief_v1.pdf` | Superseded CAD brief |
| `Anticipy_Full_Handoff_Guide.pdf` | Handoff guide |
| `HARDWARE_SYSTEM_MAP.md` | One-page block diagram. Note it labels storage "QSPI flash" while the R0B BOM actually fits serial **NAND** — see contradictions. |

## Before you build to this

See [`../00_START_HERE/CONTRADICTIONS.md`](../00_START_HERE/CONTRADICTIONS.md). The short version:
four different enclosure envelopes exist across the record, the storage technology is stated three
different ways, and the MCU is not actually locked despite one superseded brief naming a specific
module.
