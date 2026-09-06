# Anticipy strict-size Tuesday EVT

This is an **Anticipy built from components**. It does not contain PLAUD hardware or any other finished recorder.

## The object

- Finished size: **56.0 × 23.0 × 12.0 mm**.
- User limit: 56.1 × 23.1 × 12.1 mm.
- Electronics: XIAO nRF52840 Sense + microSD BFF + protected 200 mAh cell + button + haptic motor.
- Exterior: brushed aluminum at the chain/battery end; color-matched nonconductive radio nose.
- The radio nose cannot be metal. Metal around the antenna would weaken Bluetooth.

## What is ready

- Printable frame, bridge, radio faces and button files.
- Exact-scale aluminum cutting template.
- Nominal assembly STEP file.
- Compile-successful UF2 firmware and source.
- A 12-frame printer plate so 12 attempts can yield 10.

## What is not ready

- No physical unit has been assembled.
- No iPhone has received its audio.
- The 16-hour runtime has not been measured.
- Stored audio is not encrypted yet.
- A source for 12 protected cells measuring no more than 25 × 20 × 5 mm is not verified.

Therefore this package is for an **engineering EVT**, not a customer shipment.

## Do this in order

1. Print **one** frame, bridge, two radio faces and a button plunger.
2. Buy and caliper-check **one** protected 502025 cell first.
3. Flash and bench-test one XIAO/BFF electronics stack.
4. Dry-fit and close unit 1 without squeezing the cell.
5. Only after unit 1 passes, print and assemble the other 11.

Start with `BUY_12.csv`, then `COST_CEILING.md`, `ASSEMBLY_CARD.md`, and `RELEASE_GATES.md`.
