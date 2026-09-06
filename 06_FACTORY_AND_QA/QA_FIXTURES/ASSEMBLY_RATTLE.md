# Rattle cradle assembly and qualification

## What it does

The cassette holds the outside of the pendant still while gravity changes direction. If a battery, PCB, motor, wire or button part is loose inside, it moves and creates an impulse. The fixture deliberately moves slowly; it is not a vibration or tumble machine.

## Mechanical assembly

1. Print and inspect the base, two bearing towers, motor mount, rotor, cassette, axis adapter and TPU liners.
2. Press one 608-2RS bearing into each tower from the recessed face. The two recessed faces point toward the rotor. Do not hammer through the bearing balls; press the outer race.
3. Bolt the towers to the base loosely. Pass the 8 mm shaft through both bearings, align until it turns freely, then tighten tower bolts.
4. Install the 8 mm clamping hub and rotor at the shaft centre. Rotor runout at its edge must be no more than 0.5 mm by caliper/dial indicator.
5. Install the 60T pulley on the shaft outside the left bearing.
6. Install the NEMA17 mount so its 20T pulley is in the same plane. Fit the GT2 belt and move the motor mount until the belt cannot skip but can still be twisted approximately 90 degrees by two fingers at mid-span.
7. Install the Hall/home sensor where its magnet passes without contact.
8. Install the polycarbonate guard and normally-closed guard switch. Do not energize motion without the guard.
9. Place the TPU base liner into the cassette base. It must sit flat with no wrinkle or debris.
10. Place the inert dummy first, add the TPU lid liner, then the lid. Tighten four M3 screws evenly until the hard PETG faces seat. The hard stop sets compression; do not keep tightening.
11. Put a removable piezo/contact patch through the lid window onto the dummy shell. Use the same small piece of low-residue tape for every run. Route the cable close to the shaft axis with a loose service loop.

## Three required mount indexes

| Index | Mount | Axis parallel to shaft | Gravity sweep |
|---|---|---|---|
| A | Cassette directly on rotor | Pendant thickness | Length and width |
| B | Cassette on 90-degree adapter, long pattern | Pendant long axis | Width and thickness |
| C | Cassette on 90-degree adapter, rotated pattern | Pendant width | Length and thickness |

All three are required. One mount position can miss a part that is free only along the shaft axis.

## Controller wiring

Use `firmware/rattle_cradle_controller/rattle_cradle_controller.ino` and the pin table inside that file. Key rules:

- 12 V adapter to 1 A fuse, then motor driver.
- Common logic ground.
- Set TMC2209 motor current from the actual motor rating; start low.
- Normally-closed guard and stop loop.
- Firmware reverses between approximately -170 and +170 degrees, then pauses for the acoustic sample.

## Fixture qualification

Do this before testing production units:

1. **Empty fixture:** ten runs in each index. Nothing may contact the guard; no fastener may loosen.
2. **Solid dummy:** weight it to the production-unit mass and run ten times per index. Repeat-run peak variation must be 3 dB or less after excluding motor-motion windows.
3. **Known-good golden units:** at least three units, ten runs each. Save their WAV files by serial/index.
4. **Seeded challenge:** put a 2 mm steel bead inside a second inert hollow dummy, not inside a battery product. The analysis must reject it in all relevant axes.

Only after those four gates should `rattle_audio_score.py` be used as an acceptance screen. Investigate a DUT whose pause-window impulse is more than 6 dB above the qualified golden envelope. A failure is quarantined and opened; never “fix” it by tightening the cassette harder.

## Production run

1. Inspect DUT for swelling/damage. Reject damaged units before fixture entry.
2. Record serial, mass and mount index.
3. Seat cassette to hard stop.
4. Close guard.
5. Run ten reversal cycles in A, B and C.
6. Score each WAV against the same mount’s golden WAVs.
7. Pass only if all three mounts pass and there is no audible scrape/click on human review.
