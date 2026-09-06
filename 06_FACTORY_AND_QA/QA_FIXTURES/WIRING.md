# Low-voltage wiring

An experienced adult should wire and inspect both fixtures. Use only enclosed, CSA/cUL-listed low-voltage adapters. No mains wiring belongs in either fixture.

## Rattle cradle

| From | To | Note |
|---|---|---|
| 12 V adapter + | 1 A fuse, then TMC2209 VM | Fuse first |
| 12 V adapter - | TMC2209 GND and Nano GND | One common logic ground |
| Nano D3/D4/D5 | STEP/DIR/EN on TMC2209 | EN is active-low |
| Nano D6 | Home switch to GND | Firmware expects LOW at home |
| Nano D7 | Normally-closed guard switch to GND | Open guard reads HIGH |
| Nano D8 | Momentary START to GND | Internal pull-up is enabled |
| Nano D9 | Normally-closed STOP loop to GND | Opening stops motion |
| Nano D10 | Optional recorder marker input/LED | HIGH during quiet sample |
| Driver A1/A2/B1/B2 | NEMA17 coils | Confirm coil pairs with meter |

Set the TMC2209 current limit using its maker's procedure and the actual motor rating. Begin low. The guard and stop loop should also interrupt driver enable in hardware; firmware is only a second layer.

## Drop release

| From | To | Note |
|---|---|---|
| 12 V adapter + | Fuse, then solenoid + | Size fuse to solenoid maker data |
| Solenoid - | MOSFET switched output | Logic-level, rated module |
| Flyback diode | Across solenoid coil | Cathode/stripe toward +12 V |
| Nano D9 | MOSFET logic input | Never connect the coil to D9 |
| Nano D6 | Normally-closed guard to GND | Open guard must also break coil supply in hardware |
| Nano D7 | Guarded ARM switch to GND | Maintained switch |
| Nano D8 | Momentary DROP switch to GND | One release per arm cycle |
| Nano D10 | READY LED through resistor | Optional panel indicator |

The included drop controller limits a command to 250 ms. Reduce that number if the chosen solenoid has a shorter rated pulse. Do not increase it above the maker's rating.
