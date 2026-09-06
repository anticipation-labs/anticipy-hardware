# Unit 001 assembly

## Layout

- USB-C exits the existing USB end; XIAO microphone uses the drill-jig opening
  and closed-cell gasket.
- Give the XIAO antenna end the largest air gap. Keep battery PCM, motor,
  driver, wire bundles, and metal-backed adhesive away where the model allows.
- Battery and a gauged coin motor within the audited 10.2 x 10.2 x 2.7 mm
  envelope sit on <=0.05 mm electrical floor insulation.
- The printed bridge feet stand on rigid shell structure and keep the XIAO
  from loading the pouch.
- The finished insulated SMD driver island occupies the modeled 8 x 4 x 2 mm
  envelope and must pass its gauge. In the 15 mm-wide Plan B layout, rotate it
  to 4 x 8 x 2 mm between battery and motor as the supplied gauge shows.
- Nothing crosses a motor, USB path, face hook, acoustic path, or pouch edge.

## Haptic circuit A — primary ordered DigiKey path

| From | To |
|---|---|
| XIAO D0 | SMD 100 ohm, then AO3400A gate |
| AO3400A gate | SMD 100 kohm, then GND |
| AO3400A source | XIAO GND |
| AO3400A drain | Motor negative |
| XIAO 3V3 | Motor positive |
| 1N4148W-HF cathode / stripe | Motor positive / 3V3 |
| 1N4148W-HF anode | Motor negative / AO3400A drain |

Use the ordered DigiKey SMD parts after verifying received labels, packages and
pinouts. This circuit requires the primary active-high UF2 in
`02_FIRMWARE/CANDIDATE_DO_NOT_SHIP_UNTIL_QA/`. Never drive the motor directly
from D0.

## Haptic circuit B — Lee local fallback only

> **Choose A or B, label the unit, and never mix their firmware or wiring. The
> Lee high-side circuit requires the separate active-low UF2. On primary
> low-side hardware that binary can energize the motor in logical-off states.**

| From | To |
|---|---|
| NTR4101P source | XIAO 3V3 |
| NTR4101P drain | Lee PID10431 motor positive |
| Motor negative | XIAO GND |
| XIAO D0 | NTR4101P gate |
| 10 kohm pull-up | NTR4101P gate to XIAO 3V3 |
| BAS16 cathode | Motor positive / NTR4101P drain |
| BAS16 anode | Motor negative / GND |

Use only received and pinout-verified Lee PID170433 NTR4101P, PID20011 BAS16
and PID17426 10 kohm parts. Flash only the UF2 under
`02_FIRMWARE/LOCAL_NTR4101P_FALLBACK_DO_NOT_MIX/`. Before battery power, prove
that the motor stays off through boot, reset, disconnect, system-off and
watchdog recovery. With Renata 100640, reject combined board-plus-motor draw
over 160 mA peak or 80 mA continuous, any reset or heat. This is still a
physical-test fallback, not an approved silent substitution.

## Optional D7 button

A normally-open switch connects D7 to GND. Mount it to rigid structure and use
an aligned existing face feature. Omit it rather than cut a crooked hole or
load the battery. Owner2 commissions automatically for 120 seconds whenever it
boots with zero stored bonds; without D7, deliberate owner recovery requires a
controlled full SWD erase.

## Band retention — primary Renata-only path

Use the supplied screw-retained band, two keyed retainer posts and body marking
jig. Work on an **empty sacrificial body first**. Drill 2.2 mm preferred; a
3/32 inch (2.381 mm) body hole is allowed; never exceed 2.4 mm. Use the 90-degree
countersink only until the inspected M2 flat head is flush. Screw length is
accepted only when the actual stack clamps without bottoming, face-hook
interference or an inward sharp end. Follow
`01_CAD/PRIMARY_RENATA_ONLY_SCREW_RETENTION.md`. This geometry is Renata-only
and intentionally incompatible with the 15 mm-wide battery Plan B.

The documented adhesive process remains an alternate recovery process only;
it does not replace the primary screw-retention mechanical gate.

## Build order

1. Verify headerless XIAO nRF52840 Sense identity.
2. Select circuit A plus primary active-high UF2, or circuit B plus the separate
   active-low UF2. Label that choice. Full-erase, flash only the matched owner2
   candidate, commission privately, and prove app audio/haptic/owner behaviour
   on USB power.
3. Gauge shell, battery body, lead route, motor, insulated driver, and XIAO.
4. On an empty sacrificial body, drill/countersink with the jig, assemble the
   selected screw band and posts, and pass the empty-shell closure/abuse gate.
5. Assemble/inspect the SMD driver under magnification; continuity and
   current-limit test it before attaching the motor.
6. Apply <=0.05 mm floor insulation. Retain the cell only at protected tab/PCM
   end and cushioned sides; leave a relaxed lead loop.
7. Bond the selected gauged coin motor to rigid structure with a thin,
   electronics-safe, fully cured process. Never bond it to the cell. The Lee
   motor is mechanically eligible only after it passes the dedicated 10.2 x
   2.7 mm gauge and remains subject to every electrical/thermal/audio/RF gate.
8. Put bridge feet on rigid shelf, then mount XIAO with <=0.10 mm insulated
   transfer adhesive outside the antenna zone.
9. Transfer the real USB/microphone positions, minimally deburr, and fit the
   acoustic gasket/mesh without covering the microphone.
10. Add D7 only if alignment and closure are clean.
11. Install the keyed posts and selected M2 screws without any inward sharp
    point, wire/pouch contact or face-hook interference. Complete witness-film
    no-load closure before closing the removable face.
12. Run powered open-case tests, then the complete closed-case release record.

Keep adhesive out of microphone, USB, antenna, button, hooks, leads, and pouch.
