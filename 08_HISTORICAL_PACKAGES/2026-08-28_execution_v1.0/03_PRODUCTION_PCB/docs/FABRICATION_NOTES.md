# Fabrication and assembly notes

## Controlled today

- Four copper layers.
- 0.60 mm nominal finished thickness.
- ENIG is the preferred finish for the WLCSP/DSBGA checkpoint.
- Exact Edge.Cuts candidate: 31 × 14 mm main region, 6.5 × 6.5 mm RF nose and retained motor scallop.
- All populated electronics are on the cavity-facing side of the board.
- Bring-up test pads are on the opposite side to avoid cavity-side placement collisions; cover them with controlled insulating film before installing any conductive cap.
- KiCad candidate rules: 0.10 mm general clearance/track, 0.30/0.15 mm via/drill, and a local 0.08 mm WLCSP clearance candidate.

These candidate rules are **not a fab capability claim**. Replace them with the selected manufacturer’s controlled 0.60 mm four-layer stack-up and assembly rules before routing/release.

## RF rules

- The 6.5 × 6.5 mm nose is a no-metal/no-unrelated-copper region.
- Only the intended antenna, RF feed and matching structures may enter it.
- The aluminum cap, battery, motor, magnets and conductive finish must stay out of the three-dimensional antenna volume.
- Johanson evaluation match values are reference-only tune slots. Closed-enclosure VNA tuning is mandatory.

## Audio rules

- Each IM69D128S uses one 0.60 mm PCB sound hole.
- Each microphone requires its own aligned shell port, compression gasket/duct and contamination membrane.
- Do not share a leaky acoustic cavity between microphones.
- Keep PMIC switching, RF and haptic current away from microphone and PDM paths.
- Firmware must mark/blank haptic-contaminated audio intervals.

## Assembly stop conditions

Do not make paste, Gerbers, drills, IPC-356 or centroid outputs until:

1. U1, SW1 and J3 official land patterns replace the zero-pad gates; J3 must use the supplier-approved JYC720FDRL hot-bar process.
2. Routing and planes are complete.
3. Exact passives, battery, charge interface, motor and LED are frozen.
4. Unfiltered ERC/DRC and independent pin review pass.
5. Full STEP/Z-stack and selected-assembler DFM pass.
