# Acceptance criteria and lot-stop rules

## Pre-build release gate

EVT fabrication remains blocked until every `MISSING_BLOCKING` PCBA item in `FACTORY_UPLOAD_MANIFEST.csv` is released and hashed, the battery pack is approved, and an authorized release record names the exact revisions. DVT and PVT require their prior phase to pass and a new signed release.

## Finished-unit acceptance

| Category | Acceptance criterion | Current release state |
|---|---|---|
| Identity | Unique serial; exact PCB/mechanical/BOM/firmware/test revisions and material lots recorded | Schema ready |
| Size | Finished nominal 50.5 × 20.68 × 10.8 mm including button membrane; never above 51.0 × 21.0 × 11.0 mm | Requirement locked; physical proof open |
| Mass | ≤17.4 g finished; record actual mass | Requirement locked; physical proof open |
| Internal retention | No audible/tactile rattle; no free motion; no wire pinch; no load or adhesive transferred through the broad LiPo pouch | Mechanical design/physical proof open |
| Cosmetics/safety | Seam/flush within released drawing; no opening, burr, crack, exposed adhesive or sharp edge | Drawing/physical proof open |
| Storage capacity | ≥414,000,000 verified usable bytes for audio after reserves/overheads | Firmware/hardware proof open |
| Twenty-hour backlog | 20 continuous hours recovered with correct sequence, duration and CRC; no silent loss, duplicate or reorder | Physical proof open |
| Battery endurance | ≥16 continuous hours under the frozen sealed workload | Physical proof open |
| Current | Sealed workload average ≤10.625 mA for the defined 85%-of-200-mAh budget | Physical proof open |
| Audio | Both channels pass released golden-unit amplitude/frequency/noise limits; no unexplained haptic/rub contamination | Numeric EOL limits must freeze during DVT |
| BLE/RF | Identity/connect/reconnect/backfill pass; RSSI/range meets released closed-product limit | Numeric RF limit/tuning open |
| Button | Short/3-second/12-second actions work without double action or sticking | Firmware/mechanical proof open |
| Haptic | Defined patterns work; no reset, corruption or loose motor; 100-event unit test passes | Physical proof open |
| Charging | Correct current, voltage, NTC response and safe temperature under released battery profile | Battery/power design open |
| Recovery | Power-cut test preserves older committed data and records any bounded tail loss explicitly | Firmware proof open |
| Security | Customer firmware uses authenticated/encrypted BLE, encrypted storage, signed anti-rollback DFU and controlled key erase | Implementation proof open |
| Compliance | Required ISED/EMC/Bluetooth/battery/label/privacy evidence tied to exact shipped configuration | Open; blocks customers |

No `OPEN` or `TBD` threshold may be silently converted into a pass. It must be frozen by ECO and added to the factory test configuration.

## Phase acceptance

### EVT-A — 10 units

- All ten have complete travelers and every-unit EOL records.
- No safety-critical failure.
- Root cause and disposition exist for every failure/rework.
- Released sample set proves storage, battery, RF/audio, charging, recovery and mechanical abuse requirements.
- Exact ECO list is frozen before DVT purchasing is released.

### DVT — 35 units

- Production-intent PCB, battery, enclosure, gaskets, adhesives, firmware and assembly process.
- 100% traveler/EOL completeness.
- Mechanical retention, drop/shock/vibration, chain pull/abrasion, sweat/ingress, temperature and button/haptic endurance plans pass their defined sample sets.
- Compliance pre-scan findings are closed or have a written blocking plan.
- Numeric acoustic, RF, current, charging, seam and fixture limits are frozen before PVT.

### PVT — 230 units

- Actual intended vendors, panel, tooling, fixtures, work instructions, operators and packaging process.
- First-pass yield target ≥95%; rework yield reported separately.
- 100% serialized EOL pass for any unit considered shippable.
- At least 200 passed units remain after destructive qualification samples, retains, rejects and rework disposition.
- Required compliance/qualification and shipment evidence is complete before customer release.

PVT units are held inventory until the PVT lot-release record is signed. Passing EOL alone does not make a unit shippable.

## Immediate stop and quarantine

Stop the line immediately for any one of these:

- Smoke, flame, venting, swelling, puncture, abnormal battery heating, smell or reversed polarity.
- Wrong PCB/BOM/firmware/mechanical revision or unknown material lot.
- Duplicate/missing serial or test data written against the wrong serial.
- Fixture calibration expired, fixture self-test fails or golden unit no longer reproduces its baseline.
- Any part substitution, process change or rework method without an approved ECO/deviation.
- Finished device exceeds the hard size or mass limit.
- Shell cannot close without force or transfers pressure to the battery pouch.
- Any exposed conductor, sharp edge or charging short risk.

## Statistical/process stop triggers

Stop and quarantine the affected lot when any trigger occurs:

- Two consecutive occurrences of the same major functional or mechanical defect.
- Three occurrences of the same major defect anywhere in a lot.
- First-pass yield below 95% after at least 20 units, or below 95% in any subsequent rolling 20-unit window.
- Two rattle, opened-seam, loose-component or battery-restraint failures.
- One failed destructive sample that indicates a common safety/design mechanism rather than sample mishandling.
- Incoming critical dimension fails on first article or two sampled parts.
- Supplier AOI/X-ray/test evidence is missing or disagrees with Anticipy EOL results.

These are internal Anticipy stop rules, not a claim of a universal sampling standard.

## Restart rule

The line restarts only after:

1. all potentially affected material and serials are identified and quarantined;
2. root cause is written and reproduced;
3. corrective action/ECO or approved rework is documented;
4. fixture and instructions are updated where affected;
5. one first article and then five consecutive units pass the affected test plus all downstream tests; and
6. an authorized release record names the quarantined lot disposition.

No schedule or shipment date overrides a lot stop.
