# Anticipy hardware master package

Prepared: 2026-09-05

## Start here

This package separates three different hardware states that must not be mixed:

1. **Current product target** — the September 4 hardware development brief. This is what the new hardware engineer is being asked to design.
2. **XIAO prototype reference** — printable enclosure CAD, wiring, fit gauges and assembly evidence for the XIAO nRF52840 Sense proof unit. It is still on physical-test hold.
3. **Custom-PCB engineering checkpoint** — editable KiCad schematic/PCB source and mechanical board references. It is **not fabrication-ready**: the R0B PCB still reports 176 unconnected pads and has unresolved battery, stack-up, enclosure and firmware gates.

## What to open

| Need | Open |
|---|---|
| Current engineer assignment | `01_CURRENT_REQUIREMENTS/Anticipy_Hardware_Development_Brief_2026-09-04.docx` |
| One-page map of the hardware | `HARDWARE_SYSTEM_MAP.md` |
| No-Lee's XIAO wiring | `02_XIAO_NO_LEES_REFERENCE/00_START_HERE.md` |
| Printable XIAO enclosure | `03_XIAO_ALL_CAD/PRINT_THESE/` |
| Editable/reference XIAO STEP files | `03_XIAO_ALL_CAD/REFERENCE_ONLY_STEP/` |
| XIAO CAD generator source | `03_XIAO_ALL_CAD/SOURCE/generate_recovery.py` |
| Native custom-PCB schematic | `04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/01_Electrical_Source/Anticipy_PROD_R0B_EVT.kicad_sch` |
| Native custom-PCB layout | `04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/01_Electrical_Source/Anticipy_PROD_R0B_EVT.kicad_pcb` |
| PCB pin map and draft BOM | `04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/01_Electrical_Source/R0B_PINMAP.md` and `BOM_DRAFT_DO_NOT_PROCURE.csv` |
| Board-only STEP/DXF | `04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/02_Mechanical_CAD/` |
| PCB placement drawing | `04_CUSTOM_PCB_R0B_ENGINEERING_NOT_FOR_FAB/01_Electrical_Source/Reports/placement.svg` |
| JLCPCB status | `08_JLCPCB_ORDER_STATUS/JLCPCB_STATUS_2026-09-05.md` |
| Original source archives | `09_SOURCE_ARCHIVES/` |

## Red-line warning

Do not upload folders `04`, `05`, `06`, or `07` to a PCB or mechanical factory as a production release. They contain engineering checkpoints, routing experiments, or historical reconstruction files. There is no released Gerber/ODB++, drill, pick-and-place, assembly drawing, final PCBA STEP, or final enclosure drawing set in this package.

The JLCPCB order in the email record is a separate active order. The emails do not prove that its uploaded manufacturing files match the R0B source collected here.

## File provenance

The files were collected from the saved Anticipy handoff packages dated August 29 through September 4 and the current Anticipy hardware brief. `FILE_INDEX_SHA256.csv` records every packaged file and its hash.
