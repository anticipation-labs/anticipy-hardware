# Serialized assembly traveler

Create one traveler per physical device before any assembly. The same serial appears on the unit, PCBA test result, EOL row, rework record and final disposition. Never reuse a scrapped serial.

## Traveler header

| Field | Required value |
|---|---|
| Traveler ID | `ANT-TRV-<work-order>-<device-serial>` |
| Device serial | Unique controlled serial |
| Phase | EVT / DVT / PVT |
| Work order / lot | Controlled work order and lot |
| PCB/PCBA revision | Exact released revision |
| BOM revision | Exact released revision |
| Mechanical revision | Exact released revision |
| Firmware version and SHA-256 | Exact released binary |
| Factory-test version and SHA-256 | Exact released tester |
| Battery MPN/revision/lot | Exact approved pack |
| Motor lot | Supplier lot |
| Enclosure/cap lots | Supplier/process lots |
| Acoustic/adhesive lots and expiry | Exact membrane/gasket/adhesive records |
| Fixture/station IDs | IDs plus calibration due date |
| Assembly operator(s) | Controlled operator IDs |

If any header field is blank, mismatched or `TBD`, place the unit in HOLD before assembly.

## Line clearance

Before the first unit of every work order:

- Remove all prior-revision parts, labels, firmware and work instructions from the station.
- Scan the released work order and current file hashes.
- Verify fixtures are in calibration and pass self-test/golden-unit verification.
- Verify battery-safe area, current-limited supply, ESD controls and quarantine bins are ready.
- Build and fully accept one first article, then five consecutive units, before unrestricted lot continuation.

## Assembly sequence

Each line creates one event row in `ASSEMBLY_TRAVELER_LOG.csv`.

| Seq. | Step ID | Operation | Required evidence / acceptance |
|---:|---|---|---|
| 10 | `KIT_VERIFY` | Scan all controlled inputs | Every MPN/revision/lot matches traveler; adhesives in date |
| 20 | `PCBA_VISUAL` | Inspect received PCBA | Correct revision/serial; no damage, missing/reversed/shifted part |
| 30 | `PCBA_SAFE_POWER` | Current-limited first power without battery | No short/abnormal current/heat; rail checks pass released limits |
| 40 | `PROGRAM` | Program bootloader/firmware/device identity | Read-back/hash/signature and unique identity pass |
| 50 | `PCBA_FUNCTION` | Run open-board pogo test | Flash, both microphones/interfaces, BLE, button input, LED and haptic output pass PCBA subset |
| 60 | `CHASSIS_PREP` | Inspect/clean chassis and cap | Correct lot; no debris, burr, crack, sharp edge or blocked aperture |
| 70 | `ACOUSTIC_INSTALL` | Install membranes/gaskets in keyed fixture | Correct side/orientation; flat, clean, unwrinkled and within controlled compression position |
| 80 | `BUTTON_LIGHT_INSTALL` | Install plunger/membrane/lightpipe if released | Keyed orientation; free travel; no pinch; optical path seated |
| 90 | `MOTOR_INSTALL` | Install motor in released board-side retainer/isolator | Motor cannot move; leads in channel; motor never bears on battery pouch |
| 100 | `PCBA_INSTALL` | Seat PCBA on released locators/retainer | Board fully seated without bow; mic ports aligned; no antenna keep-out intrusion |
| 110 | `BATTERY_IQC_CONFIRM` | Re-scan and inspect approved battery | Correct polarity/voltage/NTC; no damage/swelling; approved dimensions/lot |
| 120 | `BATTERY_INSTALL` | Place battery in compliant cradle/pull-tab retention | No force, crease, broad-face clamp, wire pinch or motor/PCB pressure; service pull tab accessible if specified |
| 130 | `WIRE_DRESS` | Route all leads through released channels/strain relief | Nothing crosses seam, antenna, mic duct, button travel or sharp edge |
| 140 | `PRE_CLOSE_TEST` | Power and run short functional test | Both mics, BLE, storage, button, LED, haptic and charging sense pass; no reset |
| 150 | `CLOSE_AND_SEAL` | Apply released seal and close in controlled fixture | Correct adhesive/gasket/energy/force/time/cure recipe; shell never forced closed |
| 160 | `CURE_HOLD` | Maintain specified pressure and cure | Start/end time, fixture and conditions logged; no handling before release time |
| 170 | `CLOSED_VISUAL_DIMENSION` | Inspect closed product | Hard envelope ≤51.0 × 21.0 × 11.0 mm; mass ≤17.4 g; released seam/cosmetic limits pass |
| 180 | `EOL` | Run complete `EOL_TEST_SPEC.md` | One complete passing EOL row written against this serial |
| 190 | `BURN_IN` | Run every-unit phase-defined recording/streaming burn-in | No reset, loss, corruption, overheating, rattle or seam change; duration logged |
| 200 | `FINAL_INSPECTION` | Clean, inspect, rattle screen and verify label | No free motion, contamination, damage, exposed adhesive or sharp edge |
| 210 | `DISPOSITION` | Accept / rework / quarantine / scrap | Authorized disposition and linked records |
| 220 | `PACK` | Package only a released unit | Correct accessory/label/serial and transport-compliant packaging |

`CLOSE_AND_SEAL` remains blocked until the retention and seal drawings/process recipe listed in `MECHANICAL_OPEN_ITEMS.md` are physically validated and released.

## Rework rule

- Failed units leave the normal line and enter a controlled rework traveler.
- Record failure code, NCR, original measurement, rework instruction/revision, operator and replacement part lot.
- After rework, rerun the failed step and every downstream step, including complete EOL.
- Never rework or reuse a damaged/swollen pouch cell.
- Rework count remains attached to the serial; a pass never erases failure history.

## Final record package per serial

The traveler is complete only when it links:

1. incoming lots;
2. all step-event rows;
3. programming record;
4. EOL result;
5. burn-in/sample qualification result;
6. NCR/rework history;
7. final disposition; and
8. pack/ship record if released.

