# PCB checkpoint status

The old zero-copper candidates below are deliberate stop signs, not the v1.0
component choice. Replace them according to
`../03_PRODUCTION_PCB/V1_CORRECTION_ORDER.md`; never fabricate this checkpoint
as-is.

**State: ENGINEERING REFERENCE ONLY — NOT A FABRICATION RELEASE.**

The controlled checkpoint is `../03_PRODUCTION_PCB/anticipy_evt_a_kicad_checkpoint.zip`. It is useful for electrical/placement review and for completing the missing vendor data, routing and verification work. It is not one of the missing release outputs represented by `PCB001` through `PCB014` in `FACTORY_UPLOAD_MANIFEST.csv`.

## What exists

- Editable native KiCad project, schematic and PCB checkpoint.
- Four-layer, 0.60 mm nominal board outline measuring 37.50 × 14.00 mm overall.
- 55 named nets, 81 placed footprints/courtyards and all 47 non-test board references represented in the connected schematic.
- 25 automated structural checks passing with zero structural failures.
- Two 0.60 mm microphone acoustic holes, test pads and the controlled haptic-motor scallop.

## Why fabrication remains blocked

1. U1 Ezurio `453-00224R` has a deliberate zero-copper placeholder until its controlled vendor pad map is obtained and verified.
2. SW1 Alps has a deliberate zero-copper placeholder until its controlled delivery drawing/pad map is obtained and verified.
3. J3, the JYC720FDRL FPC/hot-bar connection, has a deliberate zero-copper placeholder until its controlled vendor land drawing is obtained and verified.
4. The board is intentionally unrouted.
5. KiCad ERC and DRC have not been run; the checkpoint includes explicit `ERC_NOT_RUN.txt` and `DRC_NOT_RUN.txt` records.
6. Gerbers, drill data, IPC-356, paste, complete released BOM, centroid, fabrication/assembly drawings, panel drawing and DFM closure are absent.
7. Battery approval, remaining exact orderable passives/LED, RF tuning, released firmware and physical qualification remain open.

## Permitted factory use

- Engineering review of architecture and placement.
- Early component-availability review.
- Capability/DFM discussion that does not create tooling or start fabrication.
- Quoting engineering work needed to close the gates.

## Prohibited factory use

- Do not generate or infer missing pads, copper, routing, Gerbers or drill data.
- Do not order PCBs, stencils, production components or assembly from this checkpoint.
- Do not treat a structural-parser pass as ERC, DRC, signal-integrity, RF or production qualification.
- Do not build customer units.

The PCB can move from checkpoint to EVT release only after controlled U1/SW1/J3 data are verified, the board is fully routed, native KiCad ERC/DRC pass with reviewed reports, the complete orderable BOM and fabrication set exist, assembler DFM is closed, and the release authorization is signed.
