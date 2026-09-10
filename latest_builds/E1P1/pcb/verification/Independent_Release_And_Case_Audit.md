# Independent release metadata and oval-case delta review

The released component choices are consistent in the native design and assembly documents. **2,643 metadata checks pass, with zero failures.** The updated USB protector position and selected maximum capacitor dimensions also clear the existing oval enclosure and modeled assembly details: **145 additional geometric checks pass, with zero intersections.**

## File scope and exact counts

- Current PCB SHA-256: `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`.
- Schematic SHA-256: `763bbfa78953252aa27d7553bfb6abf9cb398650fb0bdceafd0432aee5e44021`.
- 69 PCB references correspond to 69 physical/virtual schematic references; three schematic-only power flags do not have footprints.
- 47 references are machine-fitted. The remaining 22 comprise 3 external final-assembly parts (BT1/M1/TH1), 3 explicit DNP parts (C20/MIC2/R9), 14 test points and 2 net ties.
- All 19 selected MPN updates match between native PCB, schematic, embedded schematic symbols, external symbol/footprint libraries and BOMs. Procurement grouping and twenty-board quantities cover exactly the 47 machine-fitted references.
- The stale D1 packaging value, C20 voltage label and battery-unselected schematic note found in the first review were corrected and rechecked. The selected Jauch pack is named and charging remains disabled pending physical qualification.

The source change log intentionally retains old part numbers as history. That is not an instruction to purchase the old parts. No stale old MPN was found in current electronics/manufacturing selection files during this audit.

## Actual case-fit delta

U4 moved from native XY (28.50, 30.00) to (28.15, 29.45) mm. All other component poses and the 45.75×17.88×0.8 mm board outline remain unchanged. The shell stays the existing 56×35×14.8 mm oval case candidate. This audit does not claim a 30×14×8 mm product.

Maximum body sizes checked were U4 1.25×1.05×0.50 mm including the drawing's permitted mold-flash allowance, C23 2.20×1.45×1.45 mm, and each selected TDK0402 capacitor 1.05×0.55×0.55 mm. Each was then enlarged by an additional 0.20 mm per XY side and 0.20 mm above its maximum height for an assembly allowance study. Those enlarged guards clear the shell, rear support geometry, battery, motor, wires/joints, thermistor, controls, lightpipe, acoustic gasket, fasteners and retention details.

C23 has the smallest physical body-to-front-shell distance, **0.4272 mm**; its enlarged guard still clears. U4's physical body-to-front-shell distance is **2.8270 mm**. These are computed minimum distances to the exact CAD solids, not assumed vertical roof gaps.

The existing case STEP remains unchanged, SHA-256 `4be21a70c57f13895fe3332e3ac481fb47b7efede24154236cf1ce396f735c6d`. Its assembly view still depicts the earlier U4 position, so the newly exported current PCB STEP should be used for electronics viewing. This delta review proves geometric clearance for the changes without silently replacing the old case release.

## Limits

The 145 new checks compare the changed component guards against the mechanical assembly. Component-to-component solder, placement, nozzle and rework clearance belong to the independent electrical assembly audit, not this case calculation. Molded/printed tolerances, wire specifications, adhesive compression, screw retention, microphone response, RF and battery/charging behavior still require physical testing. A clean file comparison or CAD intersection result cannot establish those properties.

Machine-readable evidence: `Independent_Metadata_Audit.json`, `Selected_Parts_Oval_Case_Clearance.json`, `Updated_PCB_Mechanical_Contract.json`. Workspace reproducibility readers (require the original oval package at the stated path plus KiCad/CadQuery runtimes; not standalone supplier scripts): `audit_metadata.py`, `extract_current_contract.py`, `verify_mechanical_changes.py`. They perform no native PCB/SCH edits and never execute the old case builder's export/write block.
