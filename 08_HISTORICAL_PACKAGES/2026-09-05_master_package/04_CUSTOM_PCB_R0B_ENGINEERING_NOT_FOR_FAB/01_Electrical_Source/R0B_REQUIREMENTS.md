# ANT-PROD-R0B EVT requirements

Status: engineering work in progress; **not approved for fabrication**.

## Frozen product envelope

- Finished product: no larger than 51.0 x 21.0 x 11.0 mm.
- Similar rounded-capsule proportions to PLAUD NotePin S; no copied private CAD.
- Target mass: under 20 g.
- Polycarbonate structural centre with 0.60 mm brushed 5052-H32 aluminum faces.
- The top-right exterior over the antenna is polycarbonate only: no aluminum,
  battery, motor, magnet, bail, chain hardware, or conductive coating.
- PCB copper is allowed under the module's non-antenna circuitry, but no copper,
  vias, components, or pours may enter Raytac's exact all-layer antenna keepout.

## PCB architecture

- Maximum PCB: 47.0 x 18.0 x 0.8 mm, four copper layers. R0B is 45.8 x 18.0 mm,
  leaving 3.0 mm total width inside the 51 x 21 mm product exterior.
- Layer intent: L1 components, PMIC loops, QSPI and PDM; L2 uninterrupted
  ground; L3 controlled-impedance USB corridor and power away from that
  corridor; L4 low-speed signals and ground fill.
- Only ordinary plated through-vias; no blind, buried, or laser vias. Standard
  vias are 0.45/0.20 mm pad/drill. Exactly two USB reversible-contact fanout
  vias are 0.36/0.16 mm and remain a written fabricator-CAM acceptance gate.
- Raytac MDBT50Q-1MV2 certified nRF52840 module at rotation 0 with its antenna
  keepout against the top board edge.
- Nordic NPM1300-QEAA-R charger/PMIC.
- GCT USB4500-03-1-A USB-C mid-mount receptacle for a 0.80 mm PCB.
- TPD2EUSB30DRTR USB D+/D- ESD protection.
- Two 27 ohm series elements between the connector-side USB pair and Raytac,
  as required by the Raytac reference circuit.
- TPD2E2U06DCKR CC1/CC2 ESD protection and ESD441DPYR VBUS protection at J1.
- Macronix MX35LF4GE4AD-Z4I, 4-Gbit SLC serial NAND, 8 x 6 mm WSON.
- Two Same Sky CMM-3424DT-26165-TR front-side, top-port PDM microphones.
- ST LIS2DW12TR accelerometer.
- B3U-1000P user button, low-current red/blue LED under 1 mm light pipe,
  AO3400A motor driver, 1N4148WS-7-F flyback diode, and VCLP1020B002L motor.
- SWD, reset, power, UART, and factory-test pads.
- All reflow parts are on the front for one assembly pass. The 14 pogo targets,
  battery wire lands, and haptic wire lands are on the rear. The battery and
  motor are installed only after bare-PCBA programming and test.

## Battery gate

- The battery is **not selected**. `BT1` is a geometry and connectivity
  placeholder marked `BATTERY-TBD-3WIRE`; it is not an orderable BOM item.
- Maximum installed envelope: 26.0 x 15.5 x 4.8 mm including protection,
  tolerance, insulation, folded tabs, and aged swelling allowance.
- Three short wires: VBAT, 10 kohm NTC, GND. Pin order is frozen as
  `1=VBAT, 2=NTC, 3=GND` at the PCB solder lands.
- Battery body is x=27.05..53.05 mm and y=22.25..37.75 mm in board coordinates.
  It has a 0.50 mm horizontal gap to the Raytac all-layer antenna keepout and
  must not move into that gap after swelling, tolerance, or adhesive creep.
- Do not buy a battery, enable charging, or release enclosure tooling until the exact configured
  pack drawing, polarity, electrical limits, UN38.3/IEC 62133/MSDS evidence, and
  physical sample are reviewed.

## Electrical invariants

- No external 5.1 kohm CC resistors; USB CC1/CC2 go directly to nPM1300.
- Raytac VBUS input (pin 32) uses protected `VBUSOUT`, not raw VBUS.
- J1-side `USB_D+` / `USB_D-` pass through U4 and 27 ohm R10/R11 before
  becoming `USB_MCU_D+` / `USB_MCU_D-` at Raytac pins 35/34.
- Physical button connects only nPM1300 `SHPHLD` to GND. MCU detects the event
  using the PMIC interrupt; SHPHLD is never tied directly to an MCU GPIO.
- nPM1300 PVSS1 and PVSS2 are distinct schematic nets joined to GND only through
  local net-tie footprints beside their switching loops.
- BUCK1 starts at 2.7 V using 330 kohm VSET and firmware raises it to 3.0 V.
- BUCK2 starts at 3.0 V using 150 kohm VSET.
- nPM1300 LED sinks drive the red/blue cathodes; anodes connect to VSYS.
- Haptic flyback polarity: diode cathode to 3V_MAIN, anode to HAPTIC_NEG.
- NAND firmware must implement ECC, bad-block management, power-fail handling,
  and a tested filesystem. Raw capacity alone is not working storage.

## Release gates

- Editable native KiCad schematic, PCB, and project files.
- Schematic/PCB net equivalence, explicit no-connects, and reviewed pin maps.
- Manufacturer-checked symbols, footprints, and maximum-height envelopes.
- Zero unconnected items and zero KiCad DRC errors.
- PMIC high-current loops reviewed against Nordic reference design.
- USB D+/D- routed to the fabricator-calculated 90 ohm differential geometry
  over continuous L2 ground; request panel coupon and TDR report.
- Exact BOM with manufacturer part numbers and approved alternates.
- Gerber, PTH/NPTH drill, IPC-356, BOM, CPL, assembly/fabrication drawings,
  paste, STEP, programming instructions, and first-article test plan.
- Exact battery drawing/sample and full enclosure collision/acoustic/RF review.
- Two PCBAs assembled and bench-approved before the remaining ten are released.

## Five-day manufacturing boundary

Canadian Circuits publicly demonstrates four layers, 5/5 mil capability,
controlled impedance, rapid bare-board service, and prototype assembly. Its
published standard four-layer stack is 1.6 mm, however. A 0.8 mm four-layer
stack, USB geometry, material availability, assembly slot, X-ray/AOI, and the
two-board customer hold all require written acceptance before a five-day clock
is credible. A new revision cannot honestly be promised as ten validated sealed
products without successful first articles.
