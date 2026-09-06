# Wiring card

Do not use the physical left/middle/right order of a transistor from memory.
Read `E`, `B`, and `C` from the exact PN2222ATA datasheet and verify with a
multimeter before applying battery power.

| Job | XIAO nRF52840 Sense pin | Connect to |
|---|---|---|
| SD chip select | D6 / P1.11 | Adafruit 5683 TX/CS |
| SD clock | D8 / P1.13 | BFF SCK |
| SD to XIAO | D9 / P1.14 | BFF MISO |
| XIAO to SD | D10 / P1.15 | BFF MOSI |
| SD power | 3V3 and GND | BFF 3V and GND |
| Button | D7 / P1.12 | button, then GND |
| Haptic control | D0 / P0.02 | 1 kOhm resistor, then PN2222 base |
| Battery | BAT+ / BAT- | protected 3.7 V BBM 602535 cell |

Haptic switch:

1. D0 goes through 1 kOhm to transistor base.
2. 100 kOhm goes from base to ground.
3. Transistor emitter goes to ground.
4. Transistor collector goes to motor negative.
5. Motor positive goes to 3.3 V.
6. Flyback diode goes across the motor; the marked end goes to 3.3 V.
7. 100 nF goes across the motor.
8. 100 uF goes across 3.3 V and ground, matching polarity.

Before connecting the motor, first test D0 with a multimeter and a simple LED
load.  Before connecting the battery, power the open board by USB and verify the
3.3 V and ground rails.

