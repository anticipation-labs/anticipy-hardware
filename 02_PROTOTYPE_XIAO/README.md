# 02 — XIAO prototype

The proof unit: a Seeed **XIAO nRF52840 Sense** dev board with an onboard PDM microphone,
streaming live audio to the iPhone app. **This is a proof path, not the product**, and it is
currently on physical-test hold.

The 10 Founder units stay on this architecture so that custom-PCB work does not block the
seven-day Founder build.

## What is here

- `00_START_HERE.md`, `00_FOLDER_STATUS.md` — the prototype's own entry points
- `01_FIRMWARE/` — the release-test image, held pending physical validation
- `03_CAD_STEP/`, `02_CAD_PRINT/` — enclosure geometry
- `04_QA/` — QA material
- `CAD/` — the full XIAO CAD set: `PRINT_THESE/`, `REFERENCE_ONLY_STEP/`, `SOURCE/`,
  `04_ASSEMBLY/`, `06_EVIDENCE/`, `FIT_REPORT.json`, `CAD_SHA256SUMS.txt`

## The haptic circuit — get this right

From the "No-Lee's" reference wiring:

| From | To |
|---|---|
| XIAO `D0` | 100 Ω resistor → N-MOSFET gate (AO3400A or equivalent) |
| MOSFET gate | 100 kΩ resistor → GND |
| MOSFET source | XIAO GND |
| MOSFET drain | Motor negative |
| XIAO `3V3` | Motor positive |
| Flyback diode cathode (stripe) | Motor positive / 3V3 |
| Flyback diode anode | Motor negative / MOSFET drain |

> **Never connect the motor directly to `D0`.** It will damage the pin.

Note also that **no firmware in this repository actually drives the haptic motor** — see
[`../05_FIRMWARE/README.md`](../05_FIRMWARE/README.md). The circuit is specified; the software
to use it does not exist yet.

## Still required

The battery, motor, driver and closed enclosure all need real measurements and release testing on
a sealed unit. Nothing here has been physically validated.
