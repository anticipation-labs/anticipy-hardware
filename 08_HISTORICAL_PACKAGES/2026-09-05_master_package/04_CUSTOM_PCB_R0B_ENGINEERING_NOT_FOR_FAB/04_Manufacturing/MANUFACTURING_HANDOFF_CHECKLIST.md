# ANT-PROD-R0B EVT manufacturing handoff checklist

Status: engineering checklist only. **R0B is not approved for fabrication or
assembly.** Routing, connectivity, DRC, enclosure, battery, and first-article
release gates still apply.

## What the manufacturing files mean

- **PCB**: the unpopulated four-layer board made from the Gerber and drill
  files.
- **BOM (bill of materials)**: the controlled spreadsheet listing every part
  to buy and place, including reference designator, quantity per board,
  description/value, manufacturer, exact manufacturer part number (MPN),
  approved alternate, footprint, and assembly side. The BOM is not the PCB.
- **CPL (component placement list)**: the pick-and-place coordinates,
  rotations, sides, and reference designators used by the assembly machine.
- **PCBA**: the PCB after the BOM parts have been placed and soldered.
- **Enclosure CAD**: separate mechanical files used by the polycarbonate and
  aluminum suppliers. PCB Gerbers cannot manufacture the enclosure.

## Controlled release bundle

Create one dated, revision-locked ZIP. The cover README must give the exact
release name, SHA-256 checksums, units, coordinate origin, approved software
revision, and Anticipy engineering contact. Do not mix files from R0 or R1.

| Required file | Purpose / required content | Release status |
|---|---|---|
| `ANT-PROD-R0B_EVT_README.pdf` | Revision, quantity, 0.80 mm/four-layer notes, file index, checksums, contacts, special processes, and explicit two-PCBA hold | Not released |
| `ANT-PROD-R0B_EVT_GERBERS.zip` | L1/L2/L3/L4 copper, top/bottom solder mask, top paste, top/bottom silkscreen as used, and Edge.Cuts; RS-274X/X2 | Not generated for fabrication |
| `ANT-PROD-R0B_EVT_DRILLS.zip` | Separate plated and non-plated Excellon drill/rout files plus drill map; USB4500 plated slots identified | Not generated for fabrication |
| `ANT-PROD-R0B_EVT_FAB_DRAWING.pdf` | Finished architecture: 45.8 x 18.0 x 0.80 mm, with production tolerances stated on the drawing; ENIG, stack-up, copper, mask, impedance, slots, panel notes, and IPC class | Not generated |
| `ANT-PROD-R0B_EVT_STACKUP.pdf` | Fabricator-returned, Anticipy-approved symmetric stack, actual dielectric/Dk, copper, USB trace width/gap, and 90-ohm differential coupon | Awaiting fabricator acceptance |
| `ANT-PROD-R0B_EVT_BOM.csv` | Exact MPNs, quantities, alternates, do-not-substitute flags, source/consign status, and fitted/DNI status | `reports/ANT-PROD-R0B_EVT_BOM_DRAFT.csv` generated; battery and all alternates remain blocked; not procurement-released |
| `ANT-PROD-R0B_EVT_CPL.csv` | Ref, centre X/Y in mm, rotation, side; same origin/rotation convention as assembly drawing | `reports/ANT-PROD-R0B_EVT_CPL_DRAFT.csv` generated for 52 top placements; assembler convention review pending |
| `ANT-PROD-R0B_EVT_ASSEMBLY_TOP.pdf` | Top-view polarity/orientation, pin-1 marks, USB slots, microphone ports, LED, and special inspection callouts; all reflow parts are top-side for one reflow pass | Not generated |
| `ANT-PROD-R0B_EVT_ASSEMBLY_REAR.pdf` | Rear pogo-pad map and rear hand-solder locations for BT1 battery and M1 motor; show that pogo testing/programming occurs before battery installation | Not generated |
| `ANT-PROD-R0B_EVT_SCHEMATIC.pdf` | Electrical reference for DFM/debug; must match the PCB netlist | A2 draft generated and visually reviewed; net equivalence passes; KiCad 8+ ERC still required |
| `ANT-PROD-R0B_EVT_IPC356.ipc` | Netlist for bare-board electrical test and CAM comparison | Not generated |
| `ANT-PROD-R0B_EVT_PCBA.step` | Maximum-height component and connector collision model | Not generated/reviewed |
| `ANT-PROD-R0B_EVT_PROGRAM_TEST.pdf` | SWD fixture map, firmware filename/hash, configuration, serialization, test commands, limits, and pass-record format | Not generated |
| `ANT-PROD-R0B_EVT_FIRST_ARTICLE_TEST_PLAN.pdf` | Approved version of `FIRST_ARTICLE_TEST_PLAN.md` | Draft only |

Native KiCad project files and the exact custom footprint library must accompany
the engineering archive. They are not a substitute for the frozen production
outputs above.

## Fabricator and assembler confirmation before purchase order

- [ ] Confirm in writing that 0.80 mm four-layer high-Tg FR-4 is in stock and
  compatible with the GCT USB4500-03-1-A mid-mount geometry.
- [ ] Return the exact symmetric stack-up and calculated USB D+/D- L1 geometry
  for 90 ohm differential impedance over continuous L2 ground.
- [ ] Confirm 5/5 mil, 0.20 mm finished through-drill with 0.45 mm pad, ENIG,
  0201, QFN exposed pad, WSON exposed pad, plated USB slots, and panel method.
- [ ] Confirm one top-side stencil, top-side placement, and a single reflow pass;
  BT1 and M1 are rear-side post-reflow hand-solder operations, not reflow parts.
- [ ] Confirm 100% bare-board electrical test, DFM/check plots, panel coupon and
  TDR report, solder-paste inspection, AOI, and X-ray of U2/U5 exposed pads.
- [ ] Identify every CAM, footprint, stencil, rotation, or BOM substitution
  proposal. No silent correction or substitution is authorized.
- [ ] Confirm the assembly sequence: build exactly FA-001 and FA-002, then hold
  the other ten PCBAs unassembled until Anticipy gives written release.
- [ ] Confirm the fastest realistic time for the two first articles and the ten
  held assemblies separately. A five-day target is not a quality waiver.

## Materials and ownership

| Item | Responsible party | Handoff rule |
|---|---|---|
| Bare PCBs, stencil, solder paste, reflow and standard SMT parts | Canadian Circuits / named PCBA assembler | Source only against the released BOM and approved AVL; provide lot/date-code and substitution record |
| Raytac U1 and any allocation-limited SMT part | As agreed on purchase order | Do not assume availability; mark `assembler sourced` or `Anticipy consigned` on the released BOM |
| Exact protected three-wire battery, MPN TBD | **Anticipy consigned** | This is a procurement and release gate: the public candidates audited so far are not approved. Supply and approve the exact configured pack drawing with maximum tolerances, integral protection, polarity `1=VBAT, 2=10k NTC, 3=GND`, electrical/thermal limits, UN38.3, IEC 62133 evidence, MSDS, lot traceability, stock confirmation, and tested samples; hand-solder BT1 on the rear only after rear-pogo programming and bare-PCBA tests |
| VCLP1020B002L haptic motor | **Anticipy consigned** | Supply tested motors; assembler hand-solders M1 on the rear with documented polarity/strain relief after the single top-side reflow pass and PCBA inspection |
| Firmware and programming credentials/files | Anticipy | Provide immutable binary, SHA-256, configuration, test image if separate, and serial-number allocation |
| Polycarbonate structural centre, light pipe, acoustic mesh and insulation | Enclosure/final-assembly supplier | Manufacture or procure from released mechanical drawings/specifications; not part of the PCB Gerber package |
| 0.60 mm brushed 5052-H32 aluminum faces | Metal supplier | Supplier provides certified sheet and finish unless the purchase order explicitly says customer-supplied material |
| Final adhesive, battery liner, anti-rattle foam, seals, bail/chain and packaging | Final assembler | Procure only from the mechanical BOM; record lot and adhesive cure process |

Do not ship loose aluminum or polycarbonate to the PCB fabricator unless it has
explicitly accepted final product assembly as a separate quoted operation.

## Receiving and build controls

- [ ] Reconcile the released BOM quantity against 12 assemblies plus stated
  attrition. Quarantine wrong MPNs, polarity, package, or date code.
- [ ] Verify the custom USB, microphone, LED, battery-land, and motor-land
  footprints against manufacturer drawings and one physical sample.
- [ ] Verify stencil reductions and paste apertures for U2 QFN exposed pad and
  U5 WSON exposed pad before paste release.
- [ ] Verify all SMT/reflow components are on the top side. Run one top-side
  reflow pass; do not place BT1 or M1 in the oven.
- [ ] Check DFM and CAM plots against the released KiCad source, Gerbers,
  IPC-356 netlist, and drill files before authorizing fabrication.
- [ ] Record panel ID, PCB lot, paste lot, reflow profile, inspection results,
  component lots, firmware hash, and serial number for FA-001 and FA-002.
- [ ] Inspect, program, and electrically test through the rear TP1-TP14 pogo pads
  while they remain exposed. Only afterward hand-solder rear BT1 and M1 and
  follow the released post-reflow assembly traveller.
- [ ] Protect both front-side top-port microphones from flux, wash fluid,
  conformal coating, adhesive, foam, and debris. Do not ultrasonic-clean them.
- [ ] Fit Raytac U1 at KiCad rotation 0 with its antenna at the top board edge.
  Maintain its exact all-layer keepout and the corresponding polymer-only
  enclosure region; no battery, motor, metal, magnet, bail, or conductive
  coating may enter it.

## Hard release gates

No fabrication release while any of these is true:

- schematic/PCB net mismatch, any unconnected item, or any unresolved KiCad DRC
  violation;
- missing footprint/pin-map review, PMIC high-current-loop review, or USB
  fabricator geometry/stack-up approval;
- missing released Gerbers, PTH/NPTH drills, BOM, CPL, fab/assembly drawings,
  IPC-356, STEP, firmware/test package, or matching checksums;
- missing exact protected three-wire battery MPN, controlled drawing, integral
  protection details, sample, 10 kohm NTC, electrical/thermal limits, polarity,
  UN38.3, IEC 62133 evidence, MSDS, or procurement approval; or
- unresolved enclosure, acoustic, battery, component-height, USB, or antenna
  collision.

No remaining-ten assembly release until **both** first articles pass every Gate
A item in `FIRST_ARTICLE_TEST_PLAN.md` and Anticipy sends written approval. No
customer release until the sealed-unit Gate B tests also pass.
