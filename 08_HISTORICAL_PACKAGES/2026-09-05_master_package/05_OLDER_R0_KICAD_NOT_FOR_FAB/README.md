# Anticipy ANT-PROD-R0 EVT PCB

This is an editable, reproducible KiCad source package for the custom Anticipy
PCB. It does not require Flux or a paid PCB-design service.

## Current state

| Area | State |
|---|---|
| Electrical architecture and pin map | Frozen for EVT review |
| Component footprints and net assignments | Generated and checked against manufacturer documents |
| Board outline | Preliminary 49 x 20 mm capsule, 0.8 mm, four layers |
| Component placement | Complete enough for routing; remaining courtyard warnings require human review |
| Copper routing | **Not complete**; the latest free-router experiment reached eight unrouted connections |
| KiCad DRC | **Not passing** because routing is incomplete |
| Enclosure/battery collision check | Blocked until production battery dimensions and enclosure STEP are supplied |
| Gerber release | **Blocked; do not fabricate this revision** |

The Founder 10 build remains the separate XIAO-module design. This custom board
is for the later pilot/production path.

## Open the design

Install KiCad 7 or later and open:

`Anticipy_PROD_R0_EVT.kicad_pcb`

The board is generated from `generate_board.py`, which is the reproducible
electrical/placement source. Run it with the Python interpreter bundled with
KiCad on Linux:

```bash
/usr/bin/python3 generate_board.py
```

The clean generated board has no traces. `Anticipy_PROD_R0_EVT.dsn` can be
opened in FreeRouting for an assisted first pass, then returned to KiCad as a
Specctra session. All routes must still be reviewed and checked in KiCad.

## Architecture

- Raytac MDBT50Q-1MV2 certified nRF52840 module
- Nordic nPM1300 battery charger and power-management IC
- USB-C device/charging connector with CC resistors and low-capacitance ESD protection
- Two Infineon IM69D128S PDM microphones
- LIS2DW12 accelerometer
- Molex push-pull microSD socket
- User button, low-current red/blue indicator, vibration motor driver
- Battery, NTC, SWD, reset, and UART service pads

BUCK1 starts at 2.7 V using a 330 kOhm VSET resistor; firmware must raise it to
3.0 V after startup. BUCK2 starts at 3.0 V using 150 kOhm. This avoids asking
nPM1300 to start at an unsupported resistor-selected BUCK1 voltage.

## Files

- `generate_board.py` — deterministic board generator
- `Anticipy_PROD_R0_EVT.kicad_pcb` — editable KiCad PCB
- `Anticipy_PROD_R0_EVT.dsn` — FreeRouting exchange file
- `pad_net_report.csv` — every pad and assigned net
- `BOM.csv` — EVT bill of materials and sourcing status
- `PINMAP.csv` — firmware-facing pin map
- `INDICATOR_BEHAVIOR.md` — red/blue LED meanings
- `FREE_TOOLCHAIN_WORKFLOW.md` — how to finish without Flux
- `RELEASE_GATES.md` — exact conditions before fabrication
- `verify_project.py` — structural and safety checks
- `preview/` — top and bottom placement images

## Non-negotiable release rule

Do not generate or order from Gerbers until all of these are true:

1. Zero unconnected items in KiCad DRC.
2. Zero clearance, drill, solder-mask, and copper-to-edge errors.
3. USB D+/D- are length/geometry reviewed and the ESD part is beside the connector.
4. PMIC buck loops match Nordic's reference-layout intent.
5. Antenna keepout contains no copper, battery, aluminum, or ground fill.
6. Exact enclosure and protected battery STEP models pass collision review.
7. A qualified PCB reviewer signs the release checklist.

This package is an EVT engineering source checkpoint, not a fabrication release.
