# Anticipy E1P1 — Boston build handoff, 9 September 2026

Use this package for the current custom E1P1 prototype. It contains the released PCB, matching oval case geometry, exact component checklist, programming image and researched rush-manufacturing plan. It supersedes the older oval review package for this build. Files are prepared; no supplier slot or Saturday delivery is booked.

## Open these first

- **See the product:** `cad/Oval_E1_Port_and_Controls.png` and `cad/Oval_E1_Exploded_Labeled.png`.
- **Open the PCB and schematic:** `pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pro` in KiCad 10.0.6. The board and schematic are beside it. Keep the local libraries with the project.
- **Read the circuit and fabrication drawings:** `E1P1_Fabrication_and_Assembly.pdf`.
- **See the assembled case:** `cad/Oval_E1_Assembly_FIT_CANDIDATE.step`.
- **Buy only missing parts:** `procurement/Missing_Parts.csv`; its companion notes distinguish purchase/delivery records from physically counted stock. Do not buy the full BOM again without checking owned quantities.
- **Manufacturing and delivery:** `logistics/Manufacturing_Saturday_Plan.md`.

## Dimensions and matching files

The PCB is **45.75 × 17.88 × 0.8 mm**. The oval shell is **56 × 35 × 14.8 mm nominal**. The case contains the selected protected Jauch LP561836JU+PCM+2 WIRES 50MM battery, motor and routed wire allowances. **This design does not meet the requested 30 × 14 × 8 mm product size.**

The native PCB SHA-256 is `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`. The case was regenerated against this exact PCB, including the moved USB protection part and selected component body limits. See the CAD contract and verification receipts. No copper was altered while packaging this handoff.

## What to give each shop

**PCB fabrication/assembly shop:** `pcb/manufacturing/` in full, the PDF, `pcb/electrical/` for native review, and the exact missing/consigned-part list. This is four-layer 0.8 mm FR-4/ENIG, with **all 137 vias epoxy-filled, planarized and copper-capped (IPC-4761 Type VII)**, controlled-impedance USB and 47 fitted SMT references per board. The four USB mounting slots remain open. Do not order a generic tented-via tier. Ask for 20 passing assemblies plus appropriate scrap/feeder allowance; two first articles should pass before completing the balance. The quantity file includes two additional-board spares, but this is not a guaranteed yield allowance.

**Case printer:** `cad/Front_Oval_Shell.step`, `Rear_Service_Cover.step`, `Button_Plunger.step` and their STLs. `Oval_E1_Three_Print_Parts_GEOMETRY_ONLY.3mf` holds those three opaque pieces in millimetres; it is not sliced G-code. `Clear_Lightpipe.step` / `.stl` is a fourth, separate optical piece requiring clear material. Read `cad/Mechanical_Handoff.md` for supports, fit, screw pilots, insulation, adhesive and acoustic details. Print unfilled nonconductive polymer; gold in the pictures is display color. Do not print the whole assembled or exploded STEP as one solid.

**Final integrator:** both shop packages, `programming/`, the external wiring/BOM files in `pcb/manufacturing/`, the CAD harness contract and the procurement checklist. Use the specified battery/motor/sensor polarities and inspect/test the open assembly before closure.

## What is verified, and what is still unfinished

The released copper has **0 native DRC violations, 0 unconnected items, 0 schematic parity issues and 0 ERC violations**. Independent saved-copper checks connect all 45 named nets. The CAD has passing geometric checks against the stated component/harness allowances. These are computer checks, not physical tests.

The supplied firmware is for supervised first-power and live-audio bring-up. **Charging is disabled. Complete offline NAND recording/recovery/backfill, qualified charging, signed updates and device ownership remain unfinished.** No assembled E1 unit has demonstrated 16-hour runtime, 24-hour recording retention, charging temperature, radio range, acoustic quality or drop performance. This package is not a qualified customer-wearable release; purchasing parts and assembling boards will not by itself finish that firmware work.

The target is 20 engineering prototypes, at least 15 working, in Boston by Saturday 12 September. The plan needs a manufacturer to accept the complete rush job, usable radio modules at that assembler, physical first-article success, and a booked recipient handoff. BU's normal mailroom can add 24–72 hours after a carrier delivery scan. The logistics file gives current phone numbers and the fastest routes found, without claiming an unaccepted quote or delivery promise.

`PCB_Release_Readme.md` and `RELEASE_STATUS.json` preserve the PCB release scope. `SHA256SUMS` and `HANDOFF_MANIFEST.json` identify the final contents of this combined handoff.
