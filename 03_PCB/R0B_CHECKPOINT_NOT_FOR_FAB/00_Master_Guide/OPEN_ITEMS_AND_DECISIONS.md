# Open items and decisions

## P0 - blocks fabrication

| Decision/item | Required evidence | Owner | Status |
|---|---|---|---|
| Exact battery | MPN, max drawing/STEP, protection, 10k NTC, polarity, limits, UN38.3, IEC 62133 evidence, MSDS, sample, stock | PCB lead + Anticipy | Open |
| Complete PCB routing | Zero unconnected items and reviewed routes | PCB lead | 176 open connections |
| PMIC review | Schematic and layout signed against Nordic reference | PCB lead | Open |
| 0.80 mm stack-up | Fabricator drawing, Dk, copper, dielectric, USB geometry | PCB lead + factory | Open |
| Thickness discrepancy | Explain/resolve 0.80 mm target versus 0.82 mm board-only STEP | PCB lead + mechanical | Open |
| Final PCBA STEP | All maximum-height components and interface bodies | PCB lead | Open |
| Factory package | Gerbers, drills, IPC-356, BOM, CPL, drawings, checksums | PCB lead | Open |

## P0 - blocks first-article bring-up

| Decision/item | Required evidence | Owner | Status |
|---|---|---|---|
| Production/factory firmware | Reproducible source, binary, hash, flash/verify commands | Firmware lead | Open |
| NAND plan | ECC, bad blocks, filesystem, recovery and secure erase proven | Firmware lead | Open |
| Pogo fixture | Drawing, pin map, programmer and test connections | PCB + firmware | Open |
| Numeric test limits | Rail, ripple, current, audio, RF, thermal and runtime limits | PCB + firmware | Open |

## P1 - blocks sealed units

| Decision/item | Required evidence | Owner | Status |
|---|---|---|---|
| Final enclosure | STEP, 3MF, DXFs, drawings, mechanical BOM | Mechanical lead | Open |
| Acoustic system | Mesh, port geometry, adhesive keepout, test limits | Mechanical + audio | Open |
| Antenna system | Polymer-only region and sealed-unit RF acceptance | PCB + mechanical | Open |
| Adhesive/seal process | Exact product, pattern, cure, rework and inspection | Mechanical + assembler | Open |
| Final integration owner | Named local technician, equipment, schedule and cost | Anticipy | Open |

## Decision log template

For every choice, record:

- Decision ID and date/time.
- Exact part/file/revision.
- Options considered.
- Evidence and test result.
- Decision and owner.
- Downstream files that must be updated.
- Whether a new revision/checksum is required.

