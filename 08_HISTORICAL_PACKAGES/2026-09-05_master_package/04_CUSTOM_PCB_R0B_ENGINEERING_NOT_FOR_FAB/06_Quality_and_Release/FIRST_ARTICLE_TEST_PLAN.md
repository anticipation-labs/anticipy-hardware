# ANT-PROD-R0B EVT first-article test plan

Status: draft engineering plan. **It does not release the current PCB for
fabrication.** Test limits that depend on final firmware, battery, stack-up, or
enclosure must be filled and approved before execution.

## Scope and hold instruction

Canadian Circuits / the assembler shall build exactly two first articles,
`FA-001` and `FA-002`. Keep the other ten PCBAs unassembled after bare-board
fabrication until Anticipy issues a written `RELEASE REMAINING TEN` notice that
identifies the release revision and both passing serial numbers.

The assembler shall return one complete test record per serial number, with raw
measurements, photos, AOI/X-ray files, instrument IDs, operator, date/time,
firmware SHA-256, PCB/panel lot, component lots, and every deviation. A blank,
assumed, skipped, or undocumented result is a failure.

## Required equipment and controlled inputs

- Current-limited bench supply and calibrated DMM; oscilloscope with suitable
  low-capacitance probes; USB-C power/data host; SWD programmer and pogo fixture.
- BLE test phone/computer and Anticipy test application; audio stimulus/speaker
  and quiet test fixture; known-good USB-C cables in both plug orientations.
- Released production firmware and, if needed, separate factory-test firmware,
  each with filename and SHA-256; serial-number allocation.
- Anticipy-approved, protected three-wire battery sample and controlled drawing;
  tested VCLP1020B002L motor; known-good acoustic/mechanical
  samples for Gate B.
- Approved test-limit sheet. If a numeric limit is not frozen, stop and request
  one; do not invent or waive it at the bench.

## Gate A — release of remaining ten PCBAs

Run every item on both FA-001 and FA-002.

### 1. Manufacturing evidence and visual inspection

- [ ] Released revision and file checksums match the traveller; no unauthorized
  CAM change, part substitution, repair, or rework.
- [ ] Bare-board electrical-test certificate and panel TDR report pass. USB
  differential impedance is 90 ohm within the released manufacturing tolerance.
- [ ] Board matches the 45.8 x 18.0 x 0.80 mm architecture within the released
  production tolerances. Outline, USB U-cutout, plated slots, finish and warpage
  are accepted against the fabrication drawing.
- [ ] Assembly evidence confirms all SMT parts were fitted on the top side in
  one top-side reflow pass. Rear BT1 and M1 were not exposed to reflow.
- [ ] AOI passes. X-ray confirms acceptable U2 QFN and U5 WSON exposed-pad
  soldering with no shorts, opens, excessive voiding, or displaced parts per
  the released workmanship criteria.
- [ ] Correct MPN, polarity/orientation and solder quality are verified for J1,
  U1-U5, MIC1/MIC2, LED1, D1, Q1, L1/L2, NT1/NT2 and all passives.
- [ ] Both microphone top ports are clean and unobstructed. Raytac U1 is at
  KiCad rotation 0 with the antenna at the top board edge; its keepout has no
  copper, via, component, rework wire, label, or conductive residue on any layer.

### 2. Unpowered electrical checks

- [ ] With no battery and no USB, inspect VBUS-to-GND, VBAT-to-GND, VSYS-to-GND,
  3V_MAIN-to-GND, 3V_FLASH-to-GND and 3V_MIC-to-GND. No hard short or unstable
  reading is permitted; record all stabilized measurements.
- [ ] Verify continuity and isolation through rear pogo pads TP1-TP14 against the
  released pin map while BT1 is still absent. Confirm NT1 alone ties PVSS1 to
  GND and NT2 alone ties PVSS2 to GND.
- [ ] Verify D1 polarity: cathode to 3V_MAIN, anode to HAPTIC_NEG. Verify BT1
  land order: `1=VBAT, 2=NTC, 3=GND`.

### 3. Controlled power-up and programming

- [ ] First power with the released current limit and no battery. Stop on
  current-limit entry, smoke, odor, unexpected heat, oscillation, or abnormal
  rail behaviour.
- [ ] Verify nPM1300 power sequencing. Before firmware changes it, BUCK1 starts
  at the design value of 2.7 V; after approved configuration, 3V_MAIN is
  3.0 V. BUCK2/3V_FLASH starts at 3.0 V. Record VSYS, VBUSOUT, 3V_MAIN,
  3V_FLASH and the programmed 3V_MIC value and ripple against released limits.
- [ ] Through the rear pogo fixture, SWD identifies the nRF52840,
  erases/programs/verifies the exact binary, and reads back the expected device
  ID. Apply the assigned serial number and save the programming log before the
  rear battery covers the pogo-access region.
- [ ] Reset, UART TX/RX, PMIC interrupt, I2C scan and LIS2DW12 identity/interrupt
  tests pass. The physical button exercises nPM1300 SHPHLD and firmware sees the
  PMIC interrupt; it is not accepted as a direct MCU-GPIO button.
- [ ] Record current in every released mode (off/ship, idle, BLE advertising,
  recording, storage write, transfer and haptic). Each must meet the approved
  firmware power budget; missing limits block release.

### 4. USB-C and protection

- [ ] In both USB-C plug orientations, VBUS and CC detection are correct, the
  unit powers without resets, and USB data enumerates using the released device
  identity.
- [ ] Exercise data transfer and repeated connect/disconnect. D+ and D- show no
  swapped/open line or corruption; U4 ESD device and connector stay physically
  sound. USB eye/compliance certification is outside this bench test and remains
  a later compliance gate.

### 5. BLE radio

- [ ] BLE advertises with the assigned identity, connects, bonds/authenticates
  as specified, exposes the expected services, accepts control commands, and
  transfers test data without disconnect or reset.
- [ ] Record open-board RSSI/packet-loss results at the released distances and
  orientations against a named golden-board or approved numeric limit. This is
  a functional check, not an RF certification claim.

### 6. Microphones and audio

- [ ] MIC1 and MIC2 are separately identifiable on the shared PDM bus; both
  respond to the controlled acoustic stimulus with expected channel assignment.
- [ ] Record silence/noise floor and a controlled tone or speech sample. Check
  gain, clipping, dropouts, clock/data integrity, channel mismatch and audible
  electrical interference against released limits.
- [ ] Repeat recording while BLE transfers data and while the haptic motor runs.
  No reset, data loss, unacceptable motor noise, or rail collapse is permitted.

### 7. NAND storage

- [ ] U5 is detected with the expected manufacturer/device identity and usable
  capacity. Firmware ECC, bad-block discovery/management and filesystem setup
  complete without error; record discovered factory bad blocks.
- [ ] Write, read back and hash-compare the released test data set. Power-cycle
  only at the approved fault-injection points, then verify recovery, previous
  file integrity and continued recording.
- [ ] Record/stop/restart, file listing, USB/BLE transfer, secure erase/reset and
  near-capacity behaviour pass the released storage protocol. Raw NAND presence
  alone is not a storage pass.

### 8. LED, haptic, button and accelerometer

- [ ] Drive LED red and blue separately and in the specified combined/status
  patterns. Confirm correct colour/polarity and no stuck LED or excess current.
- [ ] After rear-pogo programming/testing, hand-solder consigned M1 on the rear,
  add released strain relief, and exercise every haptic pattern. Verify Q1
  switching and D1 flyback action; no overheating, reset, or unacceptable audio
  contamination.
- [ ] Button short/long press, wake/ship behaviour and PMIC interrupt pass.
- [ ] Accelerometer identity, all axes, orientation, motion interrupt and idle
  behaviour pass the released functional limits.

### 9. Approved battery and charge test

Do not procure, connect, charge, or release this section until Anticipy has
accepted an exact protected three-wire pack that fits the controlled maximum envelope:
drawing, integral protection, polarity, voltage/current/temperature limits,
10 kohm NTC, UN38.3, IEC 62133 evidence, MSDS, lot traceability, and physical
sample. This is a hard procurement and release gate; a similar two-wire or
unprotected cell is not an alternate.

- [ ] Measure pack polarity before connection. After rear-pogo programming and
  bare-PCBA testing, hand-solder the pack to rear BT1 using released insulation
  and strain relief; NTC reading is plausible and stable.
- [ ] With the released charger configuration, test USB attach in both plug
  orientations, charge current regulation, NTC cold/hot response, termination,
  recharge, battery protection and battery-only operation against the exact
  pack limits.
- [ ] Log battery voltage, current and temperatures at the pack, nPM1300, USB
  connector and nearby components. Any swelling, odor, damage, unstable charge,
  excessive temperature or limit violation is an immediate stop and failure.

### Gate A decision

Both first articles must pass Sections 1-9 with no open deviation. Anticipy
reviews all evidence and either issues the written `RELEASE REMAINING TEN` notice
or a written hold/rework instruction. Verbal approval is not release.

## Gate B — sealed product/customer release

Run on both first articles after the final released enclosure and mechanical BOM
are available; repeat any affected Gate A test after enclosure installation.

- [ ] PCBA STEP and physical fit pass with no component, USB, button, LED/light
  pipe, battery, motor, microphone-well, bail or adhesive collision.
- [ ] Battery is isolated from copper by the released liner, cannot move or
  bend, and has 0.5 mm design clearance. Motor and wires cannot rattle or chafe.
- [ ] Both microphone acoustic paths use released mesh and remain unobstructed;
  sealed-unit audio meets the approved response/noise limits.
- [ ] USB-C insertion/retention and both plug orientations work through the
  final opening. Button and red/blue indicator are aligned and repeatable.
- [ ] The top-edge U1 antenna region is polymer-only and respects the exact
  all-layer keepout. BLE range/RSSI/packet loss pass the sealed-unit limits in
  worn and free-space orientations.
- [ ] Shake/rattle, controlled drop, charge, thermal, overnight recording,
  storage/backfill, BLE transfer and runtime tests all pass the released
  protocol with no reset, corruption, overheating, swelling, loose part or
  cosmetic damage.
- [ ] Firmware version/hash, serial number, battery/PCB lots and final test
  record are captured for each unit. Shipping and regulatory release remains
  subject to radio and lithium-battery compliance review.

## Immediate hard-stop conditions

Stop the build and keep all remaining units on hold for any of the following:

- wrong revision/checksum, unauthorized substitution/CAM edit, net mismatch,
  unconnected item, DRC error, or unresolved DFM exception;
- failed bare-board electrical test/TDR, visible defect, AOI/X-ray failure,
  solder bridge/open, damaged microphone, or antenna-keepout intrusion;
- hard short, unexpected current limit, wrong/unstable rail, programming failure,
  reset, excessive heat, smoke, odor, battery swelling/damage, or charger limit
  violation;
- failure of either first article in USB, BLE, audio, storage, LED, haptic,
  button, accelerometer, battery/charging, enclosure, antenna, or runtime tests;
  or
- missing measurement, missing numeric acceptance limit, undocumented rework,
  or incomplete traceability.

No failed item may be converted to a pass by schedule pressure. Diagnose,
document, revise, and repeat the affected test on both first articles before
release.
