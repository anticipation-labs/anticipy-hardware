# Anticipy full hardware handoff guide

Release: `ANT-PROD-R0B-EVT-HANDOFF-2026-08-29`

## 1. What this package is

This package gives a senior electrical engineer, mechanical designer, firmware engineer, PCBA factory, and final assembler one controlled source of truth for turning the Anticipy custom-PCB concept into working EVT units.

It includes the editable KiCad project, custom footprints, draft BOM, pin map, verified board outline, provisional board-only STEP/DXF, engineering scope, manufacturing RFQs, firmware requirements, assembly plan, QA gates, and ready-to-send messages.

It does not pretend unfinished items are finished. The board is not fabrication-ready, the battery is not selected, and the final enclosure CAD and firmware binary do not exist yet.

## 2. Plain-English definitions

- **PCB**: the bare green circuit board.
- **BOM**: bill of materials, meaning the shopping list of electronic parts.
- **PCBA**: the PCB after the electronic parts have been soldered onto it.
- **Schematic**: the electrical map showing what connects to what.
- **PCB layout**: the physical placement and copper traces on the board.
- **Gerbers**: factory images of every PCB layer.
- **Drill files**: instructions for every plated hole, slot, and non-plated cut.
- **CPL or pick-and-place file**: the X/Y position, rotation, and side for every machine-placed part.
- **STEP**: a 3D CAD model used for collision and enclosure design.
- **DXF**: a 2D cutting profile, often used for sheet metal or outline transfer.
- **EVT**: engineering validation test, the first hardware revision used to prove the design works.

The PCB is not the BOM. The BOM is not the enclosure. The PCBA factory does not automatically create a finished pendant.

## 3. Frozen product intent

Anticipy is a camera-free wearable Bluetooth audio pendant. The device is intended to record ambient audio, store audio when offline, transfer live and stored data to an iPhone, indicate state using a tiny red/blue light, provide haptic feedback, detect motion/wear state, and support secure reset and factory programming.

| Requirement | Frozen target |
|---|---|
| Finished exterior | 51.0 x 21.0 x 11.0 mm maximum |
| Shape | Rounded capsule with proportions similar to PLAUD NotePin S; no copied private CAD |
| Mass | Target under 20 g |
| Centre structure | Polycarbonate |
| Front and rear faces | 0.60 mm brushed 5052-H32 aluminum |
| Radio region | Polycarbonate only over antenna; no metal, battery, motor, magnet, chain hardware, or conductive coating |
| Camera | None |
| PCB | 45.8 x 18.0 mm current outline; 4-layer; 0.80 mm production target |

## 4. Current electrical architecture

The R0B design uses:

- Raytac MDBT50Q-1MV2 nRF52840 radio/processor module.
- Nordic nPM1300 charger and power-management IC.
- Two Same Sky PDM microphones.
- Macronix 4-Gbit SLC serial NAND.
- ST LIS2DW12 accelerometer.
- USB-C with data, CC, and VBUS protection.
- Red/blue status LED, user button, haptic driver, factory pogo pads, battery lands, and motor lands.

The battery is a placeholder only. The required pack must be protected, three-wire, include a 10 kohm NTC, and fit within a maximum installed envelope of 26.0 x 15.5 x 4.8 mm including protection, insulation, folded tabs, tolerance, and swelling allowance.

## 5. Honest engineering status

The automated R0B verifier reports:

- 4 copper layers.
- 45.8 x 18.0 mm geometric outline.
- 70 electrical references.
- 223 source-of-truth pins checked.
- 0 geometric DRC violations.
- **176 unrouted PCB connections.**
- 0.50 mm provisional battery-to-antenna gap.
- 2.00 mm conservative motor-to-antenna gap.

Therefore, this is a strong starting package, not a factory release.

## 6. Who does what

### Senior PCB engineer

The senior PCB engineer owns the electrical design until a release package exists. They must review every symbol and footprint, reconcile the 0.80/0.82 mm thickness issue, select or approve the exact battery, manually complete routing, review the nPM1300 loops against Nordic's reference, obtain the fabricator's impedance stack-up, run final ERC/DRC/net-equivalence checks, create a PCBA STEP, generate manufacturing outputs, and support first-board bring-up.

### PCBA factory

The factory supplies or fabricates the bare PCB, sources approved SMT parts, prints solder paste, places components, reflows, inspects, programs/tests if quoted, and returns assembled PCBAs. The factory should build exactly two first articles and hold the other ten until written release.

### Mechanical CAD engineer

The mechanical engineer designs the polycarbonate centre, aluminum faces, button actuator, light pipe, microphone acoustic wells, USB opening, battery retention, motor retention, chain/bail interface, sealing, and assembly strategy around the released PCBA STEP and exact battery STEP.

### Final integration technician

The final technician receives tested PCBAs, batteries, motors, enclosure parts, firmware, assembly drawings, adhesives, insulation, acoustic mesh, and QA forms. They install the rear hand-solder parts, insulate and strain-relieve them, close the enclosure, cure adhesives, and run sealed-unit tests.

## 7. What each recipient receives

### PCB engineer package

- Native KiCad `.kicad_pro`, `.kicad_sch`, `.kicad_pcb`, and `.kicad_dru`.
- Custom `.pretty` footprint library and `fp-lib-table`.
- Draft BOM, pin map, pad/net report, verifier, design generator, requirements, placement plan, stack-up request, and current DRC report.
- Nordic nPM1300 reference-layout archive.
- Exact scope of work and release checklist.

### Mechanical CAD package

- Product envelope and material strategy.
- Provisional board-only STEP and board-outline DXF.
- PCBA placement image and interface requirements.
- Required CAD deliverable list.

The provisional files are for early packaging studies only. The final enclosure must use the engineer-released PCBA STEP and exact battery STEP.

### PCBA factory package

Before release, the factory may receive only the RFQ and stack-up request. After release, it receives one locked ZIP containing Gerbers, drills, BOM, CPL, assembly drawings, fab drawing, stack-up, IPC-356, schematic PDF, PCBA STEP, programming instructions, firmware hash, and first-article test plan.

### Final assembly package

- Released PCBA and battery STEP files.
- Complete enclosure STEP and exploded STEP.
- Polycarbonate production STEP/3MF.
- Aluminum front/rear/marking DXFs.
- Mechanical BOM.
- Adhesive and cure specification.
- Assembly traveler.
- Firmware and test instructions.
- Per-unit serial and QA record.

## 8. Materials and who supplies them

The pendant is a sandwich:

1. A 0.60 mm brushed 5052-H32 aluminum front face.
2. A polycarbonate centre frame that holds and electrically isolates the hardware.
3. The tested PCBA, protected battery, motor, insulation, foam, light pipe, and acoustic mesh.
4. A 0.60 mm brushed 5052-H32 aluminum rear face.
5. A polymer-only radio zone over the antenna.

You do not normally ship raw aluminum to the PCB engineer. The engineer specifies interfaces. The metal shop normally supplies certified aluminum sheet and cuts it from released DXFs. The PCBA factory supplies PCB laminate, copper, solder mask, finish, stencil, paste, and approved SMT parts unless the purchase order says Anticipy will consign a part. Anticipy should consign the exact approved battery and haptic motor for the first batch.

## 9. Seven-day rush attempt

The seven-day clock is a target, not a promise.

| Day | Required outcome |
|---|---|
| Day 0 | Hire PCB lead; send RFQs; freeze decision owner; select battery candidate; reserve factory capacity |
| Day 1 | Complete schematic/footprint review, routing, stack-up negotiation, mechanical interface review, and release-candidate checks |
| Day 2 | Release manufacturing package only if every gate passes; factory starts two first articles; mechanical CAD continues around released PCBA |
| Day 3 | Fabrication/assembly; firmware bench image and pogo fixture ready; enclosure prototypes printed |
| Day 4 | Bring up FA-001 and FA-002; measure rails; program; test USB, BLE, microphones, storage, motion, LED, and haptic |
| Day 5 | If both pass, release remaining ten PCBAs; freeze enclosure and cut/print parts |
| Day 6 | Integrate and seal first two complete pendants; run acoustic/RF/charge/runtime tests |
| Day 7 | Finish remaining units only if the first two sealed units pass; serialize, clean, and package |

One to five working EVT units in a week may be possible with immediate engineering and a first-spin success. Ten polished sealed units in one week cannot be guaranteed.

## 10. Release sequence

The only safe sequence is:

1. Engineering release candidate.
2. Zero unconnected items and zero unresolved DRC errors.
3. Fabricator-reviewed 0.80 mm stack-up and 90-ohm USB geometry.
4. Exact battery approved.
5. Manufacturing package checksummed and signed.
6. Two first articles manufactured.
7. Both pass Gate A bench testing.
8. Written `RELEASE REMAINING TEN` approval.
9. Two sealed first articles pass Gate B.
10. Customer release.

## 11. Immediate owner actions

- Send the complete ZIP to one accountable senior PCB engineer.
- Send the factory RFQ immediately, but do not issue fabrication files or a purchase order.
- Make battery selection the first engineering decision.
- Assign one mechanical CAD owner and one firmware/bring-up owner.
- Reserve access to a current-limited bench supply, oscilloscope, DMM, SWD programmer, USB test host, BLE phone, audio stimulus, and pogo fixture.
- Use the project-control workbook to record one owner and deadline for every open gate.

## 12. What is deliberately missing

The following files cannot honestly be supplied yet because the design has not reached that stage:

- Released Gerbers and drills.
- Released BOM and CPL.
- Final PCBA STEP with all components.
- Exact battery STEP and approved battery MPN.
- Final enclosure STEP, production 3MF, and aluminum DXFs.
- Production firmware binary and SHA-256.
- Final programming fixture drawing and test software.

Their required filenames and acceptance rules are included so the responsible engineer knows exactly what must be produced.

