# Release status — 2026-08-29

## Green: digitally verified

- Exact-size production envelope: **50.500 × 20.680 × 10.800 mm**.
- Full production STEP: **16 solids** and **zero positive-volume intersections**.
- Production mechanical checks: **23/23 pass**, including a 16-solid exported-STEP regression.
- Main product STL files: **11/11 watertight, one connected body each**.
- P2S package: **3 plates and 14 printable objects**.
- QA fixtures: **42 STL, 45 STEP, 26 drop orientations and 59 acceptance checks**.
- Lab firmware: clean compile; UF2/ELF hashes match the supplied manifest.
- Storage arithmetic: `5,000 bytes/s × 72,000 s × 1.15 = 414,000,000 bytes`.

## Yellow: engineering candidate

- The exact shell, component placement, seals, retention and mass budget.
- A 200 mAh battery meeting the controlled maximum pack drawing.
- Raytac AN54LV-15 pre-certified nRF54L15 radio module.
- MK Founder MKDV4GCL-ABF 4-Gbit managed SD NAND.
- Dual Infineon IM69D128S microphones, Nordic nPM1300 and TI DRV2605L.
- Littelfuse/C&K PTS841 side button and Vybronics VC0720B015F wired motor.

These are good candidates, not permission to build customer stock.

## Red: must close before fabrication/customer shipment

1. Update the editable board to the final module, managed memory, switch and motor lands.
2. Correct DRV2605L A2/REG: it is a 1.8 V regulator output with its own 1 µF bypass, not the 3V0 rail.
3. Resolve every radio-module pad/net, route all copper and run unfiltered KiCad ERC and DRC.
4. Obtain assembler DFM approval and inspect the populated STEP in the enclosure.
5. Obtain a supplier-signed battery drawing including PCM, 10 kΩ NTC, wire exit, polarity, 27 × 12.5 × 6.0 mm finished maximum, UN38.3 and IEC 62133-2 evidence.
6. Fabricate only three EVT PCBAs.
7. Run real audio, BLE, storage, battery, charge, haptic, button, thermal, RF, drop, rattle, chain-pull, sweat/ingress and privacy tests.
8. Build and compile the production nRF54L15 firmware and iPhone client; the supplied nRF52840 UF2 is for the larger lab unit.

## Schedule truth

- Ready-made-board lab parts: about **5–10 business days after checkout**, controlled by Seeed transit and LiPo ground shipping.
- Three custom EVT units: no responsible fixed date until the board and battery gates close; a best-case engineering range is roughly **3–7 weeks**, not a promise.
- A customer batch in two weeks is not supported by the present evidence. The release sequence in `06_FACTORY` is the shortest path that does not gamble the whole lot.

## Meaning

This package finishes the **digital design and execution handoff**. It does not pretend that unbuilt hardware has passed physical tests.
