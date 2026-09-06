# Release and QA gates

## Gate 0 - engineering release

- [ ] Exact battery MPN, drawing, STEP, protection, NTC, polarity, compliance evidence, sample, and stock approved.
- [ ] Every symbol, pin map, footprint, polarity, height, and acoustic port reviewed.
- [ ] PMIC loops and grounds reviewed against Nordic reference.
- [ ] Fabricator returns and Anticipy approves the 0.80 mm stack-up and 90-ohm USB geometry.
- [ ] 0.80/0.82 mm thickness discrepancy closed.
- [ ] Zero unconnected items.
- [ ] Zero unresolved ERC, DRC, or net-equivalence issues.
- [ ] Final PCBA STEP passes enclosure/battery/motor/USB/button/LED/microphone/antenna collision review.
- [ ] Released BOM, CPL, Gerbers, drills, IPC-356, fab/assembly drawings, STEP, test files, and checksums agree.

## Gate A - release remaining ten PCBAs

Both FA-001 and FA-002 must pass:

- [ ] Revision, checksum, material, dimensions, electrical test, AOI, and X-ray evidence.
- [ ] Unpowered short/continuity/isolation checks.
- [ ] Current-limited power-up and all rail measurements.
- [ ] SWD program/verify, device ID, serial, reset, UART, I2C, PMIC interrupt, and button.
- [ ] USB power/data in both orientations.
- [ ] BLE advertising, security, control, and transfer.
- [ ] Both microphone channels, quiet/tone/speech, BLE coexistence, and haptic-noise test.
- [ ] NAND identity, ECC, bad blocks, write/read/hash, power-fail recovery, secure erase, and near-capacity behavior.
- [ ] LED, haptic, accelerometer, and approved battery/charge tests.
- [ ] No open deviation or missing measurement.

## Gate B - sealed-unit release

Both sealed first articles must pass:

- [ ] Fit and retention with no collision, rattle, chafe, or exposed battery risk.
- [ ] Microphone acoustic response and contamination inspection.
- [ ] USB insertion, button travel, and light-pipe alignment.
- [ ] Sealed-device BLE range/RSSI/packet-loss limits.
- [ ] Charge, thermal, drop, shake, overnight recording, backfill, secure reset, and runtime tests.
- [ ] Complete traceability: PCB lot, battery lot, motor lot, firmware hash, enclosure revision, serial, and test record.

## Approval rule

Verbal approval is not release. The approval must identify the exact revision, file checksums, two passing first-article serials, known deviations, and approver.

