# ANT-PROD-R0B preliminary placement coordinates

Coordinate system is the KiCad board workspace, millimetres. This is the
placement input to the generator and remains subject to DRC and enclosure STEP
collision review.

## Outline and mechanical regions

- Board spans global x 20.0..65.8 and y 21.0..39.0: 45.8 x 18.0 mm.
- Left end has rounded shoulders and two support horns around the USB opening.
- The GCT USB U-cutout runs from x 20.0 to 26.2 and y 25.38 to 34.62.
- Right end uses compact shoulders and a vertical radio edge so the rectangular
  certified module remains fully supported inside the 18 mm PCB width.
- Exterior coordinates are approximately board coordinates minus (18.0, 19.5).
- Rear battery body envelope: x 27.05..53.05, y 22.25..37.75; installed height
  including protection and insulation is 4.8 mm maximum.
- Rear motor body envelope: 10.0 mm diameter centred at x 60.55, y 32.50.
- Raytac exact all-layer antenna keepout is inherited from its manufacturer
  footprint. With U1 at 0 degrees it occupies x 53.55..65.95 and
  y 21.75..25.50 along the top-right edge.

## Major placement

| Ref | Centre (x, y) | Rotation | Design reason |
|---|---:|---:|---|
| J1 | 20.0, 30.0 | +90 | Footprint origin is the straight PCB edge; local +Y points right/inboard |
| U4 | 28.2, 30.0 | -90 / 270 | ESD data pads face the USB contacts; GND pad faces inward |
| U6 | 28.9, 23.1 | 0 | CC1/CC2 ESD protection beside the USB connector |
| D2 | 28.4, 32.75 | 0 | VBUS shunt protection beside the USB connector |
| U2 | 35.2, 28.6 | 180 | Origin of transformed Nordic config-4 revision-1.2 power cell |
| MIC1 | 46.3, 23.9 | 0 | Front top-port with direct enclosure acoustic well |
| MIC2 | 51.2, 23.9 | 0 | 4.9 mm spacing; no PCB acoustic holes |
| U5 | 48.2, 30.7 | 0 | Soldered 4-Gbit SLC NAND near radio |
| U1 | 59.75, 29.50 | 0 | Antenna faces the top-right polycarbonate RF window |
| M1 rear pads | 54.4, 33.0 | -90 | Post-PCBA haptic wire termination |
| Motor rear envelope | 60.55, 32.50 | 0 | 10 mm adhesive disc clear of antenna in plan view |
| U3 | 51.3, 36.45 | 0 | Accelerometer below NAND |
| SW1 | 30.0, 36.3 | 0 | Edge-accessible ship-hold/reset plunger |
| LED1 | 34.0, 36.7 | 0 | Red/blue indicator centred on 1.0 mm light-pipe target |
| BT1 rear pads | 54.4, 28.8 | -90 | Three battery leads after bare-PCBA test |
| TP1..TP9 rear | x 35.0..47.0, y 30.0 | 0 | 1.0 mm pogo targets on 1.50 mm pitch, tested before battery install |
| TP10..TP14 rear | x 35.0..41.0, y 31.5 | 0 | Additional VSYS, VBUSOUT, 3V_FLASH, 3V_MIC and PMIC_INT diagnostic pads |
| R10/R11 | 60.3/61.8, 38.0 | 0 | Raytac-required 27 ohm USB series pair below U1 |
| C25/C26 | 58.5/63.5, 38.0 | 0 | Raytac local VDD/VBUS bulk capacitors below U1 |
| C21/C27 | 49.8/51.5, 38.2 | 0 | Two accelerometer 100 nF bypass capacitors below U3 |

## Placement checks before routing

1. Confirm the USB4500 footprint origin, 6.20 mm U-cutout, plated slots, and
   6.75 mm contact-land centres against GCT drawing revision A1.
2. Obtain assembly-house DFM approval for the exact Nordic reference-cell
   placement, 0201 assembly capability, and connector-adjacent protection parts.
3. Confirm the rear motor and battery envelopes remain outside the Raytac
   all-layer antenna keepout in the complete enclosure STEP.
4. Keep the two nPM1300 switch nodes and inductors on the top layer and as short
   as physically possible; never route a switch node beneath a microphone.
5. Use an insulating battery liner and tent vias inside the rear battery/motor
   envelopes as the fabricator allows; no exposed copper may contact either.
6. Generate and inspect the complete PCBA STEP before enclosure release.
