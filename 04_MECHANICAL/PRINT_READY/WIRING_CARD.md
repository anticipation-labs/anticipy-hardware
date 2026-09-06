# Five-unit prototype wiring card

## Think of it like five toy blocks

- XIAO: the brain, Bluetooth radio, microphone and charger.
- microSD BFF: the memory-card holder.
- battery: the food.
- button: the finger input.
- motor: the buzz.

## Exact pins

| Function | XIAO nRF52840 Sense pin |
|---|---|
| microSD chip select | D6 / P1.11 |
| user button | D7 / P1.12 to GND |
| haptic MOSFET gate | D0 / P0.02 through 100 ohm |
| battery | red to BAT+, black to BAT- |

## Physical board sandwich

The Adafruit 5683 sits back-to-back with the XIAO. Do **not** use the tall
plastic headers. Before covering the XIAO battery pads, add insulated red/black
30 AWG pigtails to BAT+/BAT-. Separate the board backs with 0.20–0.25 mm PET
electrical insulation, align all same-name edge pads, and bridge all fourteen
pairs with short 0.5 mm tinned solid-wire pieces. Route the battery pigtails out
one side, never between the board backs. The uncut BFF TX jumper is XIAO
D6/P1.11. The soldered stack must remain within 17.8 x 21.0 x 7.0 mm and
must meter open-circuit from 3V to GND before USB is connected.

## Battery connection

There is no connector in v09. First test on USB, then unplug it. Confirm pouch
polarity with a meter. Inline-splice and fully heat-shrink the black/BAT- lead;
only then expose and splice red/BAT+. Never cut or strip both live pouch leads
at once, and keep the solder joint at least 40 mm from the pouch.

## Haptic wiring

1. D0 -> 100 ohm -> AO3416 gate.
2. 100 kohm from gate to ground.
3. AO3416 source to ground.
4. AO3416 drain to motor negative.
5. Motor positive to 3.3 V.
6. 1N5819 diode across the motor: stripe to 3.3 V, other end to drain.
7. 0.1 uF across the motor and 47 uF across 3.3 V/ground beside it.

Bench-test all electronics before the battery enters the printed shell. Check
battery polarity with a multimeter; never guess from wire colour alone.
