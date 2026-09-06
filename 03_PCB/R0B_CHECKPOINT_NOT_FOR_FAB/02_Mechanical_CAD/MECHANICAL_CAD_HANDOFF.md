# Mechanical CAD handoff

## Objective

Create a manufacturable rounded-capsule enclosure no larger than 51.0 x 21.0 x 11.0 mm around the released Anticipy PCBA, exact protected battery, 10 mm haptic motor, light pipe, microphone paths, USB-C, button, and chain/bail interface.

## Inputs available now

- Provisional 45.8 x 18.0 mm board-only STEP.
- Provisional board-outline DXF.
- Placement PNG/SVG.
- Electrical requirements and antenna keepout rules.
- Provisional battery and motor envelopes in KiCad.

These are early packaging inputs only. The current STEP exports at 0.82 mm and contains no component bodies. Do not release tooling, aluminum, or final fit from it.

## Inputs required before final release

- Engineer-released PCBA STEP with maximum-height component bodies.
- Exact battery STEP and controlled maximum-tolerance drawing.
- Motor drawing and wire exit.
- Button travel/force and access target.
- USB connector insertion envelope and tolerance.
- LED emitting centre and light-pipe optical requirements.
- Microphone port centres, supplier keepout, mesh and acoustic targets.
- Exact Raytac antenna keepout and polymer-only external zone.

## Material architecture

- Front: 0.60 mm brushed 5052-H32 aluminum.
- Centre: injection-grade polycarbonate geometry; EVT may be printed in polycarbonate if tolerances are verified.
- Rear: 0.60 mm brushed 5052-H32 aluminum.
- Antenna end: polycarbonate only.
- Internal: flame-retardant electrical insulation, battery liner, anti-rattle foam, acoustic mesh, light pipe, controlled adhesive, and strain relief.

## Required CAD outputs

1. `ANT-PROD-R0B_ENCLOSURE_ASSEMBLY.step`
2. `ANT-PROD-R0B_EXPLODED_ASSEMBLY.step`
3. `ANT-PROD-R0B_POLYCARBONATE_CENTRE.step`
4. `ANT-PROD-R0B_POLYCARBONATE_CENTRE.3mf`
5. `ANT-PROD-R0B_FRONT_ALUMINUM.dxf`
6. `ANT-PROD-R0B_REAR_ALUMINUM.dxf`
7. `ANT-PROD-R0B_ANTICIPY_MARKING.dxf`
8. `ANT-PROD-R0B_LIGHT_PIPE.step`
9. `ANT-PROD-R0B_BUTTON_ACTUATOR.step`
10. `ANT-PROD-R0B_MECHANICAL_DRAWING.pdf`
11. `ANT-PROD-R0B_EXPLODED_ASSEMBLY.pdf`
12. `ANT-PROD-R0B_MECHANICAL_BOM.csv`
13. `ANT-PROD-R0B_TOLERANCE_AND_ADHESIVE_SPEC.pdf`

## Design checks

- No aluminum, battery, motor, magnet, bail, chain hardware, or conductive coating enters the antenna zone.
- Battery cannot bend, slide, rattle, touch exposed copper, or move toward the antenna after swelling and adhesive creep.
- USB plug reaches full insertion in both orientations without levering the PCB.
- Button is repeatable and cannot remain pressed after a drop.
- Red/blue LED aligns with the light pipe without leaking into the microphones.
- Microphone ports remain clean, short, symmetric, sealed, and protected by acoustic mesh.
- Motor is mechanically isolated enough to avoid unacceptable microphone noise.
- Enclosure can be assembled and reopened during EVT without destroying the PCBA.
- Both sealed first articles pass RF, acoustic, charge, thermal, drop, rattle, and runtime tests.

