# Fit, battery, motor, and driver gate

Use a 0.01 mm caliper, current-limited supply, multimeter, photographs, and the
printed gauges. A web listing and a CAD pass are not release measurements.

## Shell and board

| Measurement | Required | Actual |
|---|---:|---:|
| Cavity length | >=47.8 mm | |
| Width at all four XIAO corners | >=18.2 mm | |
| Floor to face underside, centre and both ends | record; nominal 8.0 mm before band | |
| Board identity | XIAO nRF52840 Sense, no headers | |
| Selected primary screw band | nominal / loose; fingertip seat only | |
| Body holes | 2.2 mm preferred; 3/32 in allowed; never >2.4 mm | |
| M2 screw/post stack | clamps; no bottoming, sharp point or hook interference | |
| Face closes with no component load | yes | |
| USB-C plug enters without moving PCB | yes | |
| Straight microphone path and gasket | open, no leak around mic | |

Photograph the empty body, face hooks, USB/microphone features, measured board,
and the complete dry-fit before soldering.

## Battery body and lead route

Every answer must be yes:

- Manufacturer, complete MPN, lot/date code, and exact-model datasheet match.
- Finished **pack body** including PCM, wrap, seams, and folded tabs passes the
  selected layout without mixing: primary <=25 x 10 x 5.5 mm, Renata target
  <=24 x 10 x 5.5 mm, or named DTP401525 Plan B <=25.3 x 15 x 4.0 mm.
- Leads, splice/connector, bend radius, and strain relief separately pass the
  explicit dry-fit route without pressing, rubbing, or pulling the pouch.
- Integrated protection covers over-charge, over-discharge, over-current, and
  short circuit.
- The exact datasheet maximum charge rating exceeds the **measured worst-case**
  battery-branch current from USB insertion, bootloader, and application, with
  engineering margin. The application target is nominally 50 mA.
- Exact-model UN38.3 test summary is archived before transport; IEC/UL evidence
  is recorded precisely, without turning a datasheet statement into a
  certification claim.
- Polarity and connector pinout are metered and photographed; wire colour and
  connector keying are never trusted.
- Pack is same-lot, flat, odourless, undamaged, stable, and within the exact
  datasheet's accepted receiving voltage range.

The documented target is Renata ICP501022UPM / 100640. The manufacturer
datasheet reports a safety circuit, maximum 24 x 10 x 5.5 mm, 80 mAh nominal,
40 mA normal and 80 mA maximum charge, and states IEC 62133 certification. The
matching UN38.3 summary identifies ICP501022UPM and reports T1-T8 passed. Local
physical stock is not confirmed. Lee PID160959/PID8834 remain unqualified
counter candidates and are rejected without every gate.

SparkFun PRT-13853/Data Power DTP401525 is a conditional geometry, not a
released cell. Its specification reports protection, 110 mAh, 22 mA standard
charge, 110 mA maximum continuous charge and maximum T/W/L/L2 values of
4.0/15.0/25.0/25.3 mm. This packet lacks a matching received-lot UN38.3
summary. CAD leaves only 0.15 mm nominal shelf clearance and full antenna-zone
overlap: use both `PLAN_B` gauges and reject friction, a pouch witness, failed
closure/RF/charge/thermal test, or thickness over 4.00 mm. Lee PID8834 is not
proved equivalent and cannot borrow these documents.

Never install a donor earbud/drone/vape cell, a raw RC cell, a generic BMS on
an undocumented pouch, or any cell requiring pressure, folding, sanding,
rewrapping, or direct pouch soldering.

## Coin motor

- Ordered target is Vybronics VCLP1020B002L from DigiKey order 101304421.
- Finished motor body must pass its tolerance gauge: diameter <=10.2 mm and
  thickness <=2.3 mm.
- Lee PID10431 is a delivery fallback only. It needs its separate
  `FALLBACK_ONLY` 10 x 2.7 mm gauge, the exact active-low P-FET circuit/UF2 pair,
  and full identity/current/duty qualification.
- Record maker/MPN, rated voltage, free-run current, startup/stall peak on a
  current-limited 3.0 V supply, and duty limit.
- The selected transistor, flyback diode, 3V3 rail, and wire must exceed the
  measured current with margin.
- Run haptic with audio and BLE; reject reset, RF loss, microphone buzz,
  rubbing, heat, or movement.
- With the Renata 100640 and Lee fallback, combined board-plus-motor draw must
  be <=160 mA peak and <=80 mA continuous, with no reset or heat. This combined
  system gate supersedes any motor-only current shortcut.

The exposed-rotor barrel PID104281 has no qualified guard in this packet and is
**not a Unit 001 shipping fallback**.

## Driver island

Primary parts are ordered AO3400A, 1N4148W-HF, 100 ohm and 100 kohm SMD parts
wired exactly as `ASSEMBLY.md` specifies. Axial parts do not fit. The
fully soldered, cleaned, strain-relieved, and insulated island must pass
`MEASURE_MAX_finished_driver_island_8x4x2.stl` without friction. Verify the
exact MOSFET and diode pinouts and current ratings. The side-strip layout has
only 0.2 mm nominal wall margin; Plan B has 0.40 mm nominal hard-part gaps.
Real no-load closure is mandatory.

The only packaged local driver alternative is Lee PID170433 NTR4101P,
PID20011 BAS16 and PID17426 10 kohm wired as the separate P-channel high-side
circuit. It requires the active-low UF2 under
`02_FIRMWARE/LOCAL_NTR4101P_FALLBACK_DO_NOT_MIX/`. Verify received manufacturer
markings and pinouts. Never use that UF2 on AO3400A/NMOS hardware or the primary
active-high UF2 on the Lee circuit.

## No-load closure

1. Gauge every finished part separately.
2. Install <=0.05 mm floor insulation, battery, relaxed lead route, motor,
   driver, safety bridge, XIAO, optional button, and microphone gasket.
3. Keep all hard parts, joints, wire crossings, and adhesive off both broad
   battery faces and pouch edges.
4. Put 0.05 mm witness film over the cell and each board/driver high point.
5. Drop and slide the face with fingertip pressure only.
6. Reopen. Any ridge, pouch mark, board movement, wire pinch, damaged film, or
   latch/bond load needed to overcome a component is a failure.

## Powered gate

Start on a current-limited bench supply with the cell disconnected. Verify no
short and correct 3V3. Connect the qualified pack through an inline meter.
Measure charging from USB insertion through bootloader/application and through
termination/recharge. Repeat open and closed while streaming and pulsing the
haptic. Stop on reset, odour, swelling, unstable voltage, or shell/cell rise of
10 C or more above ambient.
