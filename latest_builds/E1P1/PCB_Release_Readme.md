# E1P1 PCB manufacturing release - 9 September 2026

**This is the corrected E1P1 data release for prototype PCB fabrication and assembly.** Use this package as a unit; it supersedes the earlier oval E1 PCB files. It does not qualify a finished wearable or promise a delivery date.

Open `pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pro` in KiCad 10.0.6. The matching PCB and schematic are beside it, with the required local libraries. The released PCB SHA-256 is `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`.

## What is finished in this release

- U4 USB protection moved from (28.50,30.00) to (28.15,29.45) mm. Its three local front-copper branches were repaired; the main USB pair, all vias, board outline and antenna keepouts are preserved. The U4/C1 negative courtyard exception was removed.
- U2 signal-pad mask expansion is now 0.050 mm, providing 0.100 mm nominal mask dams. U4 mask expansion is now 0.050 mm to match TI's land-pattern guidance. Matching footprint libraries were updated.
- All 137 vias are specified epoxy-filled and copper-capped, IPC-4761 Type VII. This is required because 14 via bores intersect fitted solder copper/paste and 15 intersect mask openings. The four USB connector mounting slots stay open.
- Exact component selections are closed: U4 TPD2EUSB30ADRTR; C13 C0603X5R1E104K030BB; C17/C19/C22 C1005X7R1C104K050BC; C23 GRM21BR60J476ME01L. C20's metadata is updated but remains DNP. Three documented tape/reel aliases were also incorporated.
- The selected external battery is now named consistently: Jauch LP561836JU+PCM+2 WIRES 50MM, 350 mAh minimum. Charging remains disabled in the bench firmware.
- Fresh Gerbers, drills, IPC-D-356 netlist, placement coordinates, exact SMT BOM, fitted-only paste, native schematic and PCB STEP are included.

## Verification

Native KiCad: **0 DRC violations, 0 unconnected items, 0 schematic parity issues, 0 ERC violations**. No ignored DRC/ERC categories and no individual DRC/ERC exclusions. The documented Nordic reference-cell courtyard rules remain; maximum-body checks and placement assumptions are recorded, rather than pretending these rules are absent.

Independent saved-copper connectivity: **45 of 45 named nets PASS**. Population: **47 machine-fitted references**, 44 top and 3 bottom; BOM, placement and paste contain the same exact set. There are 69 native references, including test pads, net ties, external wiring pads and DNP parts. Independent metadata audit: 2,643 checks pass. The case delta audit passes 145 checks for the moved/reselected parts with maximum-body and assembly allowances.

The board is **45.75 x 17.88 x 0.8 mm**, four layers. It does **not** fit the requested 30 x 14 x 8 mm overall product envelope. Its tested mechanical relationship is to the existing 56 x 35 x 14.8 mm oval case study, not to a newly miniaturized case. No claim of an absolute smallest possible PCB is made.

## Give the manufacturer

1. `E1P1_Fabrication_and_Assembly.pdf` plus `pcb/manufacturing/` in full: fabrication specification, Gerbers, plated drill file, zero-hole NPTH file, IPC netlist, fitted BOM, DNP list, placement CSV, via-filling coordinates, external assembly BOM and STEP. The single PDF contains the schematic, both assembly views, all copper layers, full fitted-placement index and plated drill map.
2. `pcb/electrical/` for native source review and local libraries. Gerbers and drill files control fabrication; the STEP includes nominal component envelopes and is not an electrical manufacturing master.
3. Read `pcb/manufacturing/Fabrication_and_Assembly_Specification.md` before quoting. This design requires filled/capped vias, 0201 assembly and controlled-impedance processing; a generic cheap four-layer order with ordinary tented vias is not equivalent.

The manufacturer must return an actual stackup/CAM plan meeting the written dimensions and 90-ohm coupon acceptance. That is a normal fabrication process check, not an unresolved component selection. Do not silently substitute parts, remove antenna keepouts, move copper, or omit via fill/cap to reduce cost.

## Parts and physical completion

The complete exact SMT list contains 27 MPN groups and 940 fitted pieces for 20 boards. Current supplier observations cover 26 groups in sufficient quantity, including two-board spares. **U1 radio modules are the supply exception:** current marketplace stock is only 14 with about 14-day dispatch. Carrier records show 25 ordered modules delivered in British Columbia, but the usable count and arrival at an assembler are unverified. Count and consign those modules or allocate another exact-MPN source before promising 20 assembled boards. See `sourcing/` for timestamped links; no stock is reserved and no order has been placed.

Release the first articles for electrical bring-up before customer use. Physical power, USB signal quality, RF, acoustic, motor-current and charging tests have not been run. The existing bench firmware supports supervised bring-up/live audio; complete offline NAND recording/recovery/backfill, qualified charging, signed updates and device ownership remain separate unfinished product work. The supplied PCB files do not establish 16-hour runtime, 24-hour retention, or failure-free customer operation.

Earlier packages were not changed. No supplier files were uploaded, no supplier message was sent, and no purchase was placed in this pass.
