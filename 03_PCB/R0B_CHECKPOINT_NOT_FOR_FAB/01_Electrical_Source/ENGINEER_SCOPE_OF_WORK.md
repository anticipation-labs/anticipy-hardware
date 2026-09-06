# Senior PCB engineer scope of work

## Assignment

Take `ANT-PROD-R0B` from engineering work-in-progress to an EVT fabrication release for 12 PCBAs, with a mandatory hold after two first articles.

## Starting point

- Editable KiCad schematic and PCB.
- Custom footprint library.
- 45.8 x 18.0 mm outline.
- Four-layer 0.80 mm target stack.
- 70 references and 223 checked design pins.
- 176 unrouted PCB connections.
- Draft BOM, pin map, requirements, placement plan, and Nordic reference archive.

## Required work

### Electrical review

- Review every schematic symbol, pin number, power pin, no-connect, polarity, and net label against the current manufacturer datasheet.
- Verify every footprint land pattern, exposed pad, paste aperture, maximum height, microphone port, USB shell slot, LED orientation, and module antenna keepout.
- Confirm the nPM1300 configuration, NTC circuit, buck startup values, charge limits, high-current grounds, and net ties against Nordic's reference.
- Confirm USB-C CC behavior, ESD topology, VBUSOUT connection, 27-ohm series resistors, and D+/D- polarity.
- Confirm the raw NAND choice is acceptable for the firmware schedule. If not, propose a lower-risk soldered storage part with a documented size, power, and firmware tradeoff.

### Mechanical and sourcing decisions

- Select or approve the exact protected three-wire battery before release.
- Obtain its maximum-tolerance STEP/drawing, protection details, NTC curve, polarity, voltage/current/temperature limits, UN38.3, IEC 62133 evidence, MSDS, lot traceability, and stock confirmation.
- Reconcile the KiCad 0.80 mm target with the board-only STEP export that measures 0.82 mm.
- Review the battery, motor, USB, button, LED, microphone, pogo, and antenna interfaces with the mechanical engineer.

### Layout completion

- Preserve an uninterrupted L2 ground reference.
- Keep all copper, components, and vias out of the Raytac all-layer antenna keepout.
- Route and review every connection manually; do not accept an autorouter result without net-by-net review.
- Keep nPM1300 switch loops and bypass paths compact and faithful to Nordic guidance.
- Route USB D+/D- as a controlled 90-ohm differential pair using the fabricator-approved stack-up and geometry.
- Review return paths, stitching, current density, via sizes, thermal reliefs, exposed pads, acoustic clearance, ESD placement, and test access.
- End with zero unconnected items and zero unresolved DRC errors.

### Release outputs

Produce:

1. Complete editable KiCad project.
2. Final released schematic and PCB.
3. Footprint and symbol verification record.
4. ERC, DRC, net-equivalence, and unconnected-item reports.
5. Gerber X2/RS-274X ZIP.
6. Separate PTH and NPTH Excellon drill ZIP plus drill map.
7. IPC-356 netlist.
8. Released BOM with approved alternates and DNI flags.
9. CPL/pick-and-place file with origin and rotation convention.
10. Fabrication drawing and approved stack-up drawing.
11. Top and rear assembly drawings.
12. Full PCBA STEP model with maximum-height bodies.
13. SWD/programming/test-pad drawing.
14. Manufacturing README with SHA-256 checksums.
15. Bring-up support for FA-001 and FA-002.

## Acceptance gates

No release until:

- Battery and enclosure interfaces are physically reviewed.
- The fabricator approves the exact 0.80 mm stack, minimum drill/pad, USB slots, controlled-impedance geometry, and rush schedule in writing.
- Every part is available, approved, or explicitly consigned.
- Zero unrouted connections remain.
- Zero unresolved ERC/DRC/net-equivalence issues remain.
- PMIC, USB, RF, acoustic, thermal, and manufacturing reviews are signed.
- Output files are regenerated from the final native source and checksummed together.

## Required response from candidate engineer

Confirm:

- Relevant nRF52/nPM1300, USB, RF module, compact wearable, and KiCad experience.
- Who personally performs layout and review.
- Start time and committed 24-36 hour engineering sprint availability.
- Availability for first-board bring-up.
- Fixed or capped estimate and what would stop the sprint.

