# Firmware handoff

## Status

No production firmware binary is included. This document defines the firmware work needed for R0B bring-up and release.

## Platform

- MCU/radio: nRF52840 in Raytac MDBT50Q-1MV2.
- Power/charger: Nordic nPM1300 over I2C.
- Audio: two PDM microphones on shared clock with separate data source paths.
- Storage: Macronix MX35LF4GE4AD-Z4I 4-Gbit SLC serial NAND.
- Motion: LIS2DW12 over I2C with two interrupts.
- USB: nRF52840 USB 2.0 device through protected D+/D-.
- BLE: secure control and live/stored audio transfer.

## Required behaviors

- Boot safely at the R0B power defaults; raise BUCK1 from 2.7 V to 3.0 V only after the nPM1300 is identified and configured.
- Configure charging only after the exact battery profile and NTC are approved.
- Record each microphone channel, verify channel assignment, and support ambient recording without a button press.
- Implement audio framing, timestamps, corruption recovery, and backfill to iPhone.
- Implement raw NAND ECC, bad-block discovery/management, wear strategy, power-fail recovery, filesystem, secure erase, and near-capacity behavior.
- Support authenticated BLE provisioning, transfer, reset, and firmware update.
- Support USB data and recovery/programming diagnostics.
- Read motion/orientation and motion interrupts.
- Drive red/blue status patterns through nPM1300 LED sinks.
- Drive haptic patterns through the MOSFET and avoid audio corruption/resets.
- Read button events through the nPM1300 interrupt path, not a direct MCU GPIO.
- Expose factory self-tests and measurement logs.

## Required firmware deliverables

1. Source repository and reproducible build instructions.
2. Locked toolchain/SDK versions.
3. Pin-map header matching `R0B_PINMAP.md`.
4. Factory-test image and production image.
5. `.hex` or `.bin` plus SHA-256 hashes.
6. SWD flash/verify command.
7. Serial-number and provisioning method.
8. Factory test command list and machine-readable pass record.
9. Power-mode table with measured current limits.
10. BLE service/protocol specification.
11. Storage format/recovery specification.
12. Secure reset and firmware-update specification.
13. Known-issues and rollback procedure.

## Bring-up order

1. Power rails and PMIC identity.
2. SWD erase/program/verify and UART logging.
3. I2C scan, nPM1300, and accelerometer.
4. USB enumeration in both cable orientations.
5. BLE advertising, connect, security, and transfer.
6. Microphone capture and channel validation.
7. NAND identity, ECC, bad-block scan, write/read/hash.
8. LED, button, and haptic.
9. Approved battery/NTC and charging.
10. Sealed-unit audio, RF, storage, runtime, and power-fail testing.

