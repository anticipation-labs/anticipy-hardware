# Every-unit end-of-line test specification

## Status

The sequence is defined, but numeric acoustic, RF, charge/current, seam and fixture thresholds remain `TBD_BLOCKING` until EVT/DVT data and the approved battery/closed enclosure exist. The test program must refuse release when a required limit or result is blank.

## Fixture requirements

- Keyed nest that cannot load the chain hole, button or battery pouch.
- Pogo interface to released charging/test contacts only.
- Current/voltage measurement with recorded calibration.
- BLE reference radio at a fixed geometry.
- Controlled acoustic source and fixture microphones/reference level.
- Camera or operator-assisted LED/cosmetic verification.
- Button actuator with controlled travel/force.
- Haptic/rattle accelerometer or contact sensor.
- Barcode/2D-code scan tied to one test session.
- Golden passing unit and known-failing fixture self-test artifact.

At the start of each shift, revision change, fixture repair or calibration event, run fixture self-test and the golden unit. If the baseline falls outside its released control band, stop and quarantine results since the last known-good check.

## Test order

| Seq. | Test ID | Action | Every-unit acceptance |
|---:|---|---|---|
| 10 | `IDENTITY` | Scan serial and read hardware/firmware identity | Unique serial; exact released PCB/BOM/mechanical/firmware/test revisions and hashes |
| 20 | `VISUAL` | Inspect exterior, ports, button, charging area and chain hole | No sharp edge, burr, crack, blocked port, exposed adhesive, finish damage or wrong label |
| 30 | `DIMENSION_MASS` | Measure controlled envelope and mass | ≤51.0 × 21.0 × 11.0 mm and ≤17.4 g; released seam/flush limits pass |
| 40 | `BATTERY_NTC` | Read battery voltage and NTC temperature | Released pack voltage/temperature relationship; no open/short/reverse indication |
| 50 | `BOOT_CURRENT` | Boot through controlled supply/charge interface | No overcurrent, reset loop or abnormal heating; numeric release band `TBD_BLOCKING` |
| 60 | `CHARGE` | Apply released charging input for defined interval | Correct detection/current/termination-state/temperature behavior; numeric band `TBD_BLOCKING` |
| 70 | `FLASH_ID_CAPACITY` | Read flash ID/geometry and managed usable capacity | Exact released flash; verified usable audio capacity ≥414,000,000 bytes |
| 80 | `FLASH_CRC` | Write/read test patterns to allocated factory region | All CRCs pass; no unexpected new bad block; factory region retired/cleared per released procedure |
| 90 | `MIC_LEFT` | Play controlled acoustic sweep/tone and record left channel | Amplitude/frequency/noise/gasket-leak limits `TBD_BLOCKING` against released golden baseline |
| 100 | `MIC_RIGHT` | Repeat right channel and channel-balance check | Released per-channel and balance limits `TBD_BLOCKING` |
| 110 | `BLE_ID_CONNECT` | Advertise, connect, bond/authenticate as factory mode permits | Correct identity; connect within released time; no unauthorized production-audio access |
| 120 | `BLE_RF` | Measure RSSI/packet result at fixed fixture geometry | Closed-unit numeric RF band `TBD_BLOCKING` |
| 130 | `RECORD_STREAM` | Record local audio while streaming live for released short cycle | Continuous frames; rate ≤5,000 bytes/s averaged over defined qualification content; no reset/overflow |
| 140 | `DISCONNECT_BACKFILL` | Force phone loss, continue locally, reconnect and drain | All known segments arrive once, in order, with matching frame/sample sequences and CRC |
| 150 | `POWER_RECOVERY` | Execute released safe power-interruption test mode | Older committed segment remains readable; bounded tail/gap explicitly recorded; no sequence reuse |
| 160 | `BUTTON_SHORT` | Controlled short press | One bookmark and one short haptic; no private/reboot action |
| 170 | `BUTTON_3S` | Hold/release in 3-to-<12-second window | Private mode toggles once; two short haptics; no reboot/short action |
| 180 | `BUTTON_12S` | Hold at least 12 seconds | Orderly sync/reboot and three haptics; 3-second action not executed |
| 190 | `HAPTIC_100` | Execute 100 released haptic events | Correct sensor response; zero reset, corruption, loose-motor signature or unexplained audio event |
| 200 | `LED` | Exercise every released state | Correct visibility/colour/current; no unacceptable acoustic-port light leak; numeric optical band if used |
| 210 | `RATTLE` | Run controlled orientation/shake signature | No audible/tactile free motion; fixture signature within released golden band `TBD_BLOCKING` |
| 220 | `POST_TEST_CURRENT_TEMP` | Record final current, voltage and temperature | No abnormal drift/heat; released bands pass |
| 230 | `DATA_AUDIT` | Validate tester row and referenced raw artifacts | No missing required field; timestamps/serial/revisions consistent; raw evidence retained |
| 240 | `FINAL_RESULT` | Calculate disposition | Pass only when every required test is PASS and no `TBD_BLOCKING`, open NCR or lot stop exists |

## Every-unit burn-in

Every EVT/DVT unit and every PVT unit intended for shipment runs at least the released integrated burn-in cycle in parallel racks after closure. Until DVT freezes a different evidence-backed duration, use a **60-minute minimum** with continuous local recording, live BLE, at least one disconnect/backfill and representative button/haptic operation. Record reset count, dropped/corrupt segments, current/temperature extrema and post-burn-in rattle/seam result.

The full 20-hour storage and 16-hour battery requirements are separate qualification tests. A short EOL/burn-in pass does not claim either endurance requirement.

## Data integrity

- `EOL_RESULTS_TEMPLATE.csv` is one row per complete test attempt.
- Retest creates another attempt number; it never overwrites the failed row.
- Raw audio/CRC/RSSI/current/temperature artifacts use the serial and attempt in their filenames.
- Tester clocks use UTC.
- Factory cannot manually change FAIL to PASS. Authorized disposition occurs outside the immutable tester output and links the NCR/rework record.

