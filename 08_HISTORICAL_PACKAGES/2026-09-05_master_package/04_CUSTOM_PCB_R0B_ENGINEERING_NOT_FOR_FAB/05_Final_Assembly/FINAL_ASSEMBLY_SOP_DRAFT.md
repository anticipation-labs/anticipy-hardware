# Final assembly SOP - draft

Status: planning document only. Final adhesive, torque, cure, acoustic, and test values must come from the released mechanical package.

## Inputs per unit

- One passed and serialized PCBA.
- One approved protected three-wire battery.
- One tested haptic motor.
- One polycarbonate centre.
- One front and one rear aluminum face.
- Light pipe and button actuator.
- Acoustic mesh for both microphones.
- Electrical insulation/battery liner.
- Anti-rattle foam and strain relief.
- Released adhesives and cleaning materials.
- Bail/chain hardware and packaging.

## Assembly order

1. Verify the serial number, PCBA test record, firmware hash, battery lot, motor lot, and enclosure revision.
2. Inspect microphones, USB connector, antenna region, pogo pads, and solder joints. Quarantine contamination or damage.
3. Program and electrically test through the rear pogo fixture while BT1 and M1 are absent.
4. Measure battery polarity and NTC. Hand-solder BT1 in the frozen order: pin 1 VBAT, pin 2 NTC, pin 3 GND.
5. Add released insulation and strain relief. Confirm the battery cannot touch exposed copper or move toward the antenna.
6. Hand-solder M1 with documented polarity. Add strain relief and mechanical isolation.
7. Retest power, USB, BLE, microphones, storage, motion, LED, button, and haptic before closing.
8. Install the PCBA/battery/motor subassembly into the polycarbonate centre without forcing or bending.
9. Install acoustic mesh, light pipe, button actuator, foam, and seals. Keep adhesive and debris away from microphone ports, USB, and antenna zone.
10. Attach front and rear aluminum faces using the released adhesive pattern and cure process.
11. Run shake/rattle, visual-gap, USB insertion, button, light-pipe, microphone, BLE, charge, thermal, storage/backfill, and runtime tests.
12. Record every result against the serial number. Clean and package only passed units.

## Stop conditions

Stop for smoke, odor, swelling, heat, unstable current, incorrect polarity, damaged microphone, short, programming failure, reset, data corruption, RF loss, audio blockage, rattle, adhesive intrusion, or any unrecorded deviation.

