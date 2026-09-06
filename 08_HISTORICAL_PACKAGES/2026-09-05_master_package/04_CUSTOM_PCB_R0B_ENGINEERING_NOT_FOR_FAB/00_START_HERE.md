# Anticipy production hardware handoff - START HERE

Release: `ANT-PROD-R0B-EVT-HANDOFF-2026-08-29`

## The one-sentence status

This is a real, editable KiCad engineering checkpoint for a compact Anticipy pendant, but it is **not ready to fabricate** because 176 PCB connections remain unrouted, the production battery is not selected, the enclosure is not released, and no production firmware binary is included.

## Current verified facts

| Item | Current state |
|---|---|
| Product exterior limit | 51.0 x 21.0 x 11.0 mm maximum |
| PCB outline | 45.8 x 18.0 mm |
| PCB architecture | 4 copper layers |
| KiCad target thickness | 0.80 mm |
| Provisional board-only STEP thickness | 0.82 mm; engineer/fabricator must reconcile |
| Electrical references | 70 |
| Source-of-truth pins checked | 223 |
| KiCad DRC geometry violations | 0 |
| Unrouted PCB connections | **176 - fabrication blocked** |
| Battery | **TBD - hard gate** |
| Enclosure | Mechanical brief only; final STEP/DXF not released |
| Firmware | Requirements only; production binary not included |

## Read these first

1. `00_Master_Guide/Anticipy_Full_Handoff_Guide.pdf`
2. `00_Master_Guide/Anticipy_Full_Handoff_Guide.docx`
3. `00_Master_Guide/Anticipy_Project_Control.xlsx`
4. `06_Quality_and_Release/FABRICATION_BLOCKED.txt`
5. `01_Electrical_Source/ENGINEER_SCOPE_OF_WORK.md`

## Who receives what

| Recipient | Send now | Do not send as a production release |
|---|---|---|
| Senior PCB engineer | Entire ZIP | Nothing is hidden; the package is explicitly WIP |
| Mechanical CAD engineer | Master guide plus `02_Mechanical_CAD` | Do not treat provisional STEP/DXF as final tooling geometry |
| Firmware engineer | `03_Firmware` plus schematic and pin map | No production flashing is authorized yet |
| PCBA factory | `04_Manufacturing/RFQ_*` only for capability and schedule review | Do not send Gerbers or issue a purchase order because they do not exist as a released set |
| Final integration technician | `05_Final_Assembly` for planning | Do not assemble customer units until two first articles pass |

## The required chain

1. PCB engineer finishes and reviews the design.
2. Fabricator confirms the 0.80 mm stack-up and USB impedance geometry.
3. Engineer releases a dated manufacturing ZIP with checksums.
4. PCBA factory builds exactly two first articles.
5. Engineer and firmware lead bring up and test those two boards.
6. Mechanical engineer freezes the enclosure around the released PCBA and selected battery.
7. Final assembler builds and seals two complete units.
8. Only after both pass may the remaining ten be released.

## Hard warning

Do not upload the current KiCad board to a factory and click order. A clean DRC violation count does not mean the board is routed. KiCad separately reports 176 unconnected items.

