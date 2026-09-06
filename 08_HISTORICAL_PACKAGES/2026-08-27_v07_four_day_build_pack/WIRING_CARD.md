# Anticipy no-custom-PCB wiring card

## Storage board

Wire the Adafruit Audio BFF exactly as its published XIAO pin map requires. Its microSD uses D0/D8/D9/D10; its unused speaker interface occupies D1/D2/D3. Do not place the boards on removable headers because the retained shell is cleared for low-profile direct wiring.

## Button

```text
XIAO D7 / P1.12 ---- momentary button ---- GND
```

Firmware supplies the pull-up. D4/D5 remain untouched for the onboard IMU/I2C bus.

## Haptic motor

```text
XIAO D6 / P1.11 -- 1k -- PN2222 base
PN2222 base -- 100k -- GND
PN2222 emitter -------- GND
PN2222 collector ------ motor negative
3V3 ------------------- motor positive

1N4148 across motor:
striped cathode -> motor positive
plain anode ----> motor negative

100nF ceramic directly across motor terminals
100uF 6.3V polymer across 3V3/GND near the motor/storage cluster
```

The 100 uF part is polarized. Follow its marked positive terminal. Verify the exact PN2222 lead order from the delivered manufacturer drawing; do not assume every TO-92 transistor has the same order.

## Battery and hard-off switch

```text
protected battery positive -> slide-switch common
slide-switch ON output ----> XIAO BAT+
protected battery negative -> XIAO BAT-/GND
```

The switch goes in the positive lead. USB can still power the XIAO while the switch is off; charging requires the switch on. Confirm battery polarity with a multimeter before soldering.

## Tiny test order

1. Flash the bare XIAO over USB.
2. Add the Audio BFF and verify write/read/CRC.
3. Add the D7 button and test 100 presses.
4. Add the D6 transistor/motor circuit and test 1,000 pulses while storage is active.
5. Add the protected battery last.
6. Install electronics only after all open-bench tests pass.

