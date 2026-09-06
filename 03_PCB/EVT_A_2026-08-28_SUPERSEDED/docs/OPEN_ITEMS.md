# Open items — ordered by dependency

## 1. Import the three missing vendor land patterns

1. Sign in to Ezurio support and download the official files for **453-00224R**: datasheet, PCB footprint/DXF or Altium library, schematic symbol, 3D model and development-kit schematic.
2. Cross-check pad names against both the datasheet and development-kit schematic.
3. Replace `U1`’s zero-copper placeholder and map every `_TO_U1_PAD_TBD` net.
4. Obtain Alps Alpine’s controlled SKSCLCE010 delivery drawing and replace `SW1`’s zero-copper side-switch placeholder.
5. Obtain JIE YI’s controlled JYC720FDRL FPC/hot-bar land drawing and approved temperature/pressure/time window; replace `J3`’s zero-copper landing-zone placeholder.

This is the shortest safe route. A guessed radio pad can destroy the radio, prevent programming or quietly ruin RF performance.

## 2. Freeze the physical interfaces

- Battery: signed supplier drawing, actual maximum dimensions, wire exit, red/black/NTC order, protection PCB, 10 kΩ curve, UN38.3, IEC 62133-2 and MSDS.
- Charging: select the exact magnetic pogo/puck, polarity, current source behavior, magnets and ESD exposure.
- Motor: use the selected **JYC720FDRL** (manufacturer family `JYC0720FDRL`); verify 3 V behavior, resistance, startup/stall current, FPC clocking, hot-bar land/finish, weld-pull strength and rigid-pocket/keeper fit from controlled drawings and samples.
- Button: measure plunger stack, pre-travel, full travel and sealed-membrane force.
- LED: select exact MPN/current and close the light-pipe/aperture stack.

## 3. Complete circuit values and routing

- Copy Nordic Config 4 placement and switching loops; preserve separate 1.8 V and 3.0 V outputs.
- Freeze exact capacitor/resistor MPNs with voltage-bias derating.
- Route 3.0 V digital power, NAND QSPI, shared dual-mic PDM, I²C haptic/PMIC, charge input and debug.
- Keep PMIC switch nodes, motor current and RF away from both microphones.
- Add continuous ground references except inside the controlled RF nose.
- Import the selected fab’s real 0.60 mm four-layer stack-up and update DRC/impedance rules.

## 4. Run electronic and mechanical release checks

- Unfiltered KiCad ERC: zero unexplained issues.
- Unfiltered KiCad DRC: zero unexplained issues.
- Independent pin/footprint review.
- Fully populated STEP aligned to enclosure datum.
- 15% detailed component-courtyard check, component maximum heights and explicit Z tolerance stack.
- Assembler DFM resolved.
- Closed-unit VNA tuning and acoustic-port review.

## 5. Build only three EVT boards

Use the safe bring-up procedure. Measure storage, BLE, audio, charge, haptic, thermal, 16-hour battery life and 20-hour recoverable backlog before any production order.
