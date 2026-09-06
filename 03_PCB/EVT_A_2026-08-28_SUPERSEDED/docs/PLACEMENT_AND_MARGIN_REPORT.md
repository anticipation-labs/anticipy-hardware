# Placement and 15% margin report

Coordinate mapping: KiCad `(100,100)` equals mechanical CAD `(0,0)`, with `Kx = 100 + CADx` and `Ky = 100 − CADy`.

| Block | KiCad center (mm) | Controlled physical/reserve size (mm) | 15% expanded size (mm) | Result |
|---|---:|---:|---:|---|
| U1 radio reserve | 89.40, 97.70 | 6.30 × 7.90 | 7.245 × 9.085 | Inside; no overlap |
| U4 NAND | 98.30, 97.60 | 8.00 × 6.00 | 9.20 × 6.90 | Inside; no overlap |
| U5 PMIC system reserve | 106.20, 95.80 | 5.60 × 4.80 | 6.44 × 5.52 | Inside; no overlap |
| U6 haptic system reserve | 104.80, 104.70 | 3.80 × 3.20 | 4.37 × 3.68 | Inside; no overlap |
| U2 microphone A | 87.20, 105.20 | 3.50 × 2.65 | 4.025 × 3.048 | Inside; no overlap |
| U3 microphone B | 113.80, 94.80 | 3.50 × 2.65 | 4.025 × 3.048 | Inside; no overlap |
| ANT1 | 79.55, 100.00 | 1.60 × 3.20 | 1.84 × 3.68 | Inside RF nose; no overlap |
| SW1 side-push envelope | 100.00, 104.95 | 3.50 × 3.55 | 4.025 × 4.083 | Inside; no overlap; copper gated |

The automated result covers these eight controlled subsystem reservations at 15% expansion and separately proves edge containment and same-side non-overlap for all 81 currently placed courtyards, including the top-side bring-up pads. It does not claim that final routed traces, vias, stencil apertures, FPC hot-bar lands or pick-and-place tolerances have passed assembler DFM. Repeat the detailed 15% check after the missing U1/SW1/J3 files are imported and routing is frozen.

## Side-button datum

Use mechanical-CAD center **(0.00, −4.95) mm**, which maps to KiCad **(100.00, 104.95) mm**. Keep the 3.50 mm switch width along CAD X, the 3.55 mm actuation depth along CAD Y, and point the actuator toward **CAD −Y / KiCad +Y**, directly at the side-wall plunger. This placement keeps the complete 15%-expanded 4.025 × 4.083 mm envelope inside the board; final copper/piercing features remain blocked until Alps’ formal delivery drawing is imported.

## Mechanical correction

The earlier placement-only STEP used a straight 31 × 14 mm main board and placed the motor over the battery region. This retained release candidate instead keeps the motor in its own rigid chassis pocket, applies no load to the pouch cell, and uses a concave PCB scallop centered at KiCad `(116.9,104.8)`, radius 4.10 mm.

The old STEP is therefore superseded for electronics release. Re-export a new populated STEP from this outline before enclosure sign-off.
