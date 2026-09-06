# Anticipy Production PCB R1

Status: engineering brief frozen for first Flux schematic pass  
Date: 2026-08-29  
Release ID: `ANT-PROD-R1`

## 1. Product goal

Build the first manufacturable custom PCB for the Anticipy wearable audio pendant. It must record ambient audio, store it when the phone is absent, synchronize it to an iPhone over Bluetooth Low Energy, charge over USB-C, give haptic feedback, and fit the frozen Anticipy enclosure.

This PCB is for the 25-unit pilot and later 100-unit production batch. The 10 Founder units continue on the XIAO nRF52840 Sense architecture so this work does not delay the seven-day Founder build.

## 2. Frozen mechanical envelope

| Item | Requirement |
| --- | --- |
| Finished enclosure | 56.0 × 23.0 × 12.0 mm |
| PCB target | 49.0 × 20.0 × 0.8 mm |
| PCB shape | Rounded capsule, exact outline to follow enclosure master |
| Layers | 4-layer FR-4 |
| Finish | ENIG |
| Battery pocket | Maximum 30 × 20 × 4.5 mm |
| Production battery | 1-cell protected LiPo, target 250 to 300 mAh, 10 kΩ NTC lead |
| Antenna region | Last 12 mm of enclosure must be polycarbonate with no aluminum over antenna |
| Component strategy | Mostly top-side assembly, battery below or behind PCB center |
| Acoustic openings | Two bottom-port microphone holes aligned to shell mesh and gaskets |

The earlier 21 × 18 mm PCB concept is rejected. It cannot carry the complete production system without risky board stacking.

## 3. Required user functions

- Automatic ambient audio capture. The main product behavior must not require pressing a button.
- 16 kHz, 16-bit mono audio as the first firmware target.
- Two microphones for later noise reduction and directionality. R1 firmware may start with one channel while retaining both footprints.
- Bluetooth Low Energy connection to iPhone.
- Live transfer when the phone is present.
- Offline recording and later backfill when the phone returns.
- At least 20 hours of offline audio capacity.
- USB-C charging, wired diagnostics, and firmware recovery.
- Battery state of charge and battery-health reporting.
- Haptic confirmation for power, pairing, and error states.
- One small button for pairing, reset, recovery, and diagnostics only.
- Motion sensing to distinguish worn, moving, and stationary states.
- Secure boot and signed device firmware update.
- Encrypted stored audio or per-device encryption keys before customer release.
- No camera.

## 4. Selected architecture

| Block | Preferred production part | Reason |
| --- | --- | --- |
| MCU and Bluetooth | Raytac `MDBT50Q-1MV2` | nRF52840, integrated antenna, USB, PDM, QSPI/SPI, pre-certified module, same MCU family as Founder unit |
| Power and charging | Nordic `NPM1300-QEAA-R` | USB-C-aware charger, power path, NTC, fuel gauge, ship mode, two buck rails and two LDO/load-switch rails |
| Microphones | 2 × Infineon `IM69D128SV01XTMA1` | Active 3 V-compatible PDM microphones, 69 dB SNR, avoids 1.8 V level translation |
| Storage | Low-profile push-push or push-pull microSD socket plus installed 8 or 16 GB industrial card | Reuses Founder storage firmware and easily exceeds 20-hour storage target |
| Motion | ST `LIS2DW12TR` | Low-power 3-axis accelerometer with activity and inactivity interrupts |
| USB-C | GCT `USB4105-GF-A` or footprint-compatible active equivalent | Compact USB 2.0 Type-C receptacle |
| USB ESD | TI `TPD2EUSB30DRTR` or approved equivalent | Low-capacitance protection for USB D+ and D- |
| Haptic | Off-board 3 V ERM coin motor | Mechanically isolated from microphones; driven by MOSFET and flyback diode |
| User input | Omron `B3U-1000P` or approved sealed equivalent | Small momentary button |
| Status | One low-current RGB or two-color LED | Charging, pairing, and fault indication through a light pipe |

### Rejected microphone for R1

The TDK T5838 has useful acoustic activity detection, but it operates at 1.65 to 1.98 V. Using it with a 3.0 V nRF and microSD system adds voltage translation and another failure mode. R1 uses dual IM69D128S microphones and software voice or acoustic activity detection. T5838 can be reconsidered for R2 after the core product works.

## 5. Power tree

```text
USB-C VBUS -> nPM1300 -> protected 1-cell LiPo with NTC
                      -> BUCK1 3.0 V: Raytac nRF52840 and digital logic
                      -> BUCK2 3.0 V: microSD and local bulk capacitance
                      -> LDO/LOAD1 3.0 V: microphones
                      -> LOAD2: haptic rail if current and noise tests pass
```

- Charge current must initially be limited to a battery-vendor-approved value. For a 250 to 300 mAh cell, begin at 100 mA unless its datasheet explicitly permits more.
- Use 47 to 100 µF local bulk capacitance at the microSD rail plus 100 nF high-frequency decoupling.
- Power-gate the microSD and microphones when safe.
- Measure real average current before claiming 16-hour runtime. A 200 mAh cell requires less than 12.5 mA average for 16 hours before conversion and aging margin.

## 6. Electrical interfaces

| Interface | Connection |
| --- | --- |
| PDM | nRF52840 PDM clock/data to both microphones with left/right selection configured per microphone datasheet |
| microSD | Dedicated SPI bus for R1, with CS pull-up and optional 22 to 33 Ω source resistors on fast lines |
| PMIC | I2C plus interrupt and ship-mode control |
| Accelerometer | Shared I2C bus plus dedicated motion interrupt |
| USB | nRF52840 native USB D+ and D-, series and ESD parts per Raytac/Nordic reference design |
| Haptic | GPIO to small N-MOSFET, gate resistor, pulldown, flyback diode, and motor noise capacitor |
| Button | GPIO with hardware pull and firmware debounce |
| Debug | SWDIO, SWDCLK, RESET, VREF, GND and optional UART TX/RX on pogo pads |

Flux must choose a conflict-free nRF52840 pin map only after checking the Raytac module pinout and Nordic peripheral restrictions. The final pin map becomes the authoritative firmware header.

## 7. PCB placement zones

1. Antenna end: Raytac module at board edge, exact copper and component keepout from Raytac design guide, no battery or aluminum above or below the antenna zone.
2. Audio center: two microphones spaced as far apart as practical, each directly above its acoustic PCB hole. Keep switching nodes, USB, microSD clock, haptic traces, and board edges away from microphone ports.
3. Storage center: microSD socket accessible during assembly but not customer-accessible after sealing.
4. Power and USB end: nPM1300, inductors, USB-C, protection, button, LED, and battery pads.
5. Test edge: gold pogo pads accessible before enclosure closure.

Use Layer 2 as an unbroken ground plane except where the antenna design guide requires a keepout. Use Layer 3 for power and slow signals. Do not route switching nodes beneath microphones or the antenna.

## 8. Manufacturing requirements

- Conservative starting rules: 5/5 mil trace and space, 0.20 mm finished vias, 0.45 mm pads, subject to the selected factory.
- 1 oz outer copper and 0.5 or 1 oz inner copper.
- Panel fiducials and at least three board fiducials if factory requests them.
- Clear pin-1 marks, polarity marks, microphone-port keepouts, test-pad labels, and antenna keepout notes.
- Exact manufacturer part numbers for every fitted item and named alternates for supply-risk parts.
- DNP options for second microphone, LED, and development pull resistors where useful.
- PCBA STEP model must be checked against the enclosure and battery before ordering.

## 9. Flux work sequence

Flux should receive one objective per message. Do not ask it to make the schematic, place the board, route it, and export manufacturing files in one request.

1. Read the blank/current project and record these requirements.
2. Build and review the block diagram and exact BOM.
3. Create and review the nPM1300 power and charging schematic.
4. Add Raytac MCU, USB, clocks, SWD, reset, and pin mapping.
5. Add PDM microphones, microSD, LIS2DW12, haptic, button, LED, and test points.
6. Run an official-datasheet and electrical-rule audit.
7. Import or draw the final mechanical board outline.
8. Place components and return placement screenshots or coordinates for review.
9. Route by subsystem, beginning with RF/USB/power, then audio and storage.
10. Clear DRC and unresolved-airwire errors.
11. Export Gerbers, drills, BOM, pick-and-place, schematic PDF, assembly drawings, STEP model, and pin map.

## 10. First Flux message

Paste this into the currently open blank Flux project, or send it through Flux MCP:

> Rename this blank project `Anticipy Production PCB R1`. Do not add, remove, place, or route components yet. Record the requirements in this brief as the project design requirements. Return only: (1) a system block diagram, (2) an interface and power-rail table, (3) a proposed exact BOM with active manufacturer part numbers, and (4) unresolved engineering questions or conflicts. Verify every proposed IC against an official current datasheet. Treat 49.0 × 20.0 × 0.8 mm as the preliminary PCB envelope, 56.0 × 23.0 × 12.0 mm as the finished enclosure, and reserve one board end for the Raytac antenna keepout. Do not invent pin assignments yet.

Attach this complete brief to the Flux project knowledge or paste its sections after the first message.

## 11. Release gates

The design is not ready to manufacture until all of these are true:

- One complete schematic review against official datasheets.
- Power-tree and charger calculations reviewed for the exact battery.
- All parts active, stocked, and sourceable for at least 125 units or replaced with approved alternates.
- DRC has zero unresolved errors and zero unrouted nets.
- Antenna keepout matches the Raytac integration guide.
- Microphone ports align with the enclosure and have no copper obstruction.
- PCBA STEP, battery, haptic motor, and enclosure pass a mechanical interference check.
- Gerbers are independently viewed and checked.
- Five assembled boards pass power, charging, USB, SWD, microphone, storage, BLE, haptic, motion, and 16-hour runtime tests before the 25-unit build is released.

## 12. Required production outputs

- Flux project and frozen revision identifier
- Schematic PDF
- Gerber and NC drill ZIP
- BOM with exact MPNs and alternates
- Pick-and-place CSV
- PCB fabrication notes and stack-up
- Assembly drawing
- PCBA STEP
- Authoritative firmware pin-map file
- Factory-test firmware and production firmware
- Pogo-jig test-point drawing
- Test procedure and acceptance limits

