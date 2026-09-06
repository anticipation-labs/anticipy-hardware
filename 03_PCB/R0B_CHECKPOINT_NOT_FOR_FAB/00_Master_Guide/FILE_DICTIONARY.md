# File dictionary and handoff map

## Files present now

| File/type | Meaning | Primary user | Status |
|---|---|---|---|
| `.kicad_pro` | KiCad project settings | PCB engineer | Editable WIP |
| `.kicad_sch` | Electrical schematic | PCB engineer/firmware | Editable WIP |
| `.kicad_pcb` | Board outline, placement and future routing | PCB engineer | Editable WIP, unrouted |
| `.kicad_dru` | PCB design rules | PCB engineer | WIP |
| `.pretty/*.kicad_mod` | Custom footprints | PCB engineer/assembler | Must be verified |
| `BOM_DRAFT_DO_NOT_PROCURE.csv` | Draft part list | PCB engineer/procurement | Not procurement-released |
| `pad_net_report.csv` | Pin/net cross-check data | PCB engineer | Engineering reference |
| `verify_project_r0b.py` | Structural/release verifier | PCB engineer | Reports 176 unrouted items |
| `placement.png/.svg` | Visual component placement | All engineering roles | Provisional |
| `PROVISIONAL_BOARD_ONLY.step` | 3D bare-board solid only | Mechanical engineer | Provisional, 0.82 mm export |
| `PROVISIONAL_BOARD_OUTLINE.dxf` | 2D board outline | Mechanical engineer | Provisional |

## Files that must be created before fabrication

| Required file | What it does | Creator |
|---|---|---|
| Release README with checksums | Locks revision and file set | PCB engineer |
| Gerber ZIP | Defines every manufactured PCB layer | PCB engineer |
| PTH/NPTH drill ZIP | Defines holes and slots | PCB engineer |
| Fabrication drawing | Defines material, finish, tolerances, impedance and notes | PCB engineer |
| Approved stack-up | Defines real four-layer construction and USB geometry | Factory + PCB engineer |
| Released BOM | Controls procurement and substitutions | PCB engineer/procurement |
| CPL CSV | Controls placement X/Y/rotation/side | PCB engineer |
| Assembly drawings | Controls orientation and special process | PCB engineer |
| IPC-356 | Electrical netlist for CAM/test | PCB engineer |
| PCBA STEP | Enables component collision review | PCB engineer |
| Programming/test package | Controls firmware and factory test | Firmware + PCB engineer |

## Files that must be created before enclosure/tooling release

| Required file | What it does | Creator |
|---|---|---|
| Exact battery STEP/drawing | Controls battery fit and safety | Battery supplier + engineer |
| Enclosure assembly/exploded STEP | Controls complete mechanical fit | Mechanical engineer |
| Polycarbonate centre STEP/3MF | Controls structural centre | Mechanical engineer |
| Aluminum front/rear DXF | Controls sheet cutting | Mechanical engineer |
| Marking DXF | Controls ANTICIPY mark | Mechanical engineer |
| Mechanical drawing/BOM | Controls materials, tolerances and parts | Mechanical engineer |
| Assembly traveler | Controls sequence, adhesive, cure and inspection | Mechanical + final assembler |

## What to send when

- Send the entire ZIP now to the accountable PCB engineer.
- Send the master guide, mechanical folder and placement files now to the mechanical engineer.
- Send RFQs now to factories for capacity review only.
- Send final manufacturing outputs only after Gate 0 is signed.
- Send final assembly outputs only after both open-board first articles pass.

