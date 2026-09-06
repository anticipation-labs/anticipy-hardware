# Assembly card

An adult, experienced microsoldering technician must do the electrical work. Never solder, puncture, bend sharply or clamp the pouch cell.

## Build unit 1 first

1. Print one `anticipy_strict_evt_polymer_frame.stl`, one bridge, two RF noses and one plunger.
2. Measure the real XIAO/BFF stack and cell with calipers. Stop if the cell exceeds 25 × 20 × 5 mm or the board stack exceeds 17.8 × 21.4 × 7.5 mm.
3. With battery and motor disconnected, flash `firmware_lab_only/Anticipy_Founder_EVT_v0.9.0.uf2` over USB-C.
4. Format the microSD card FAT32 and insert it.
5. Mount the BFF against the back of the XIAO without headers. Keep the two boards insulated and use the shortest possible solder links.
6. Connect the button and haptic cluster exactly as below.
7. Test the bare electronics. Connect the protected cell last.
8. Dry-fit the shell. Nothing hard may touch or press on the cell.
9. Test the closed unit before applying permanent face adhesive.

## Exact signals

| Job | XIAO pin | Other end |
|---|---|---|
| SD chip select | D6 / P1.11 | BFF TX/CS, factory jumper unchanged |
| SD clock | D8 / P1.13 | BFF SCK |
| SD data to XIAO | D9 / P1.14 | BFF MISO |
| SD data from XIAO | D10 / P1.15 | BFF MOSI |
| Button | D7 / P1.12 | Momentary switch, then GND |
| Haptic control | D0 / P0.02 | 100 ohm resistor, then MOSFET gate |
| Battery | BAT+ / BAT- | Protected 3.7 V pouch; verify polarity twice |

## Haptic cluster

- 100 kilohms from MOSFET gate to GND.
- MOSFET source to GND.
- MOSFET drain to motor negative.
- Motor positive to 3.3 V.
- Diode stripe to 3.3 V; other end to MOSFET drain.
- 0.1 uF across the motor.
- 47 uF across 3.3 V and GND near the motor.
- Insulated finished cluster must fit inside 8 × 5 × 1.5 mm.

The XIAO antenna, microphone and LED all live under the printed RF nose. Do not replace that nose with metal or metallic paint.
