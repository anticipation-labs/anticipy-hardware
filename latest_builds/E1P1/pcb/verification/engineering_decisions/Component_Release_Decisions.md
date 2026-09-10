# E1 USB protector and 100 nF capacitor selection

Decision: use **TPD2EUSB30ADRTR at U4** and **C1005X7R1C104K050BC at C17, C19 and C22**. Update C20's optional part metadata to the same capacitor but **preserve C20 as DNP**. These are engineering selections for the existing E1 circuit. They do not establish physical USB/ESD qualification or whole-product readiness.

Reviewed 9 September 2026 against the oval E1 native netlist and mechanical contract. Original PCB SHA-256: `137bf2814371842fb071526d6b6c3c138dfceb2d92459d390f8d55ac541d3a44`. No PCB, schematic, component position or routing was changed by this independent review.

## Exact purchase identities

Stock was read from live supplier pages in Chrome at approximately 13:51 UTC on 9 September 2026, not inferred from cached search snippets. These are unallocated inventory observations, not delivery promises. No order was placed.

| Use | Manufacturer part | DigiKey US cut-tape order code | Live stock | Baseline for 20 boards |
|---|---|---|---:|---:|
| U4, one per board | Texas Instruments TPD2EUSB30ADRTR | 296-28153-1-ND | 80,460 | 20 |
| C17, C19, C22, three per board | TDK C1005X7R1C104K050BC | 445-4952-1-ND | 1,506,626 | 60 |
| C20, optional second microphone bypass | Same TDK capacitor | Same | Not required | 0; DNP |

The two selected lines total about **US$14.93 for twenty boards before spares, tax, freight, tariffs and assembly** at the displayed quantity breaks: 20 × $0.648 plus 60 × $0.0328. Assembly attrition and feeder leader quantities must be added by the assembler. DigiKey displayed a warning that high order volume may add one business day of processing.

The original TPD2EUSB30DRTR remains an active TI product but had **zero live stock at DigiKey US and Mouser US**. DigiKey showed 3,000 expected 16 September; Mouser showed a later December arrival. Cached search results incorrectly suggested immediate stock, so those counts were rejected. [DigiKey original](https://www.digikey.com/en/products/detail/texas-instruments/TPD2EUSB30DRTR/2193486), [Mouser original](https://www.mouser.com/ProductDetail/Texas-Instruments/TPD2EUSB30DRTR?qs=%2Fqzd9s%252BcLd6bPJi5HXCDvw%3D%3D), [DigiKey selected U4](https://www.digikey.com/en/products/detail/texas-instruments/TPD2EUSB30ADRTR/2520830), [DigiKey selected capacitor](https://www.digikey.com/en/products/detail/tdk-corporation/C1005X7R1C104K050BC/2093220).

## U4: compatible normal USB data operation, different DC fault limits

Both parts use DRT3 and identical connections: pin 1 D+, pin 2 D−, pin 3 ground. The native U4 connections are `/USB_D+`, `/USB_D-`, `/GND`; U4 has no VBUS connection. The existing 0.30 × 0.30 mm pads and 0.70/0.85 mm center spacing match TI's DRT land dimensions. No net, copper, pad or mechanical-envelope change is needed for the substitution. The package drawing gives a 1.05 × 0.85 mm maximum molded body, 1.05 mm lead span and 0.50 mm maximum height, excluding the drawing's additional permitted mold flash. The existing CAD assembly guard covers those tolerances.

| Datasheet parameter | Original TPD2EUSB30 | Selected TPD2EUSB30A |
|---|---:|---:|
| Recommended operating voltage | 0–5.5 V | 0–3.6 V |
| Absolute maximum DC input voltage | 6 V | 4 V |
| Breakdown minimum at 1 mA | 7 V | 4.5 V |
| Clamp maximum at 1 A | 8 V | 8 V |
| Typical IO-to-ground capacitance | 0.7 pF | 0.7 pF |
| IEC contact/air ESD component rating | ±8 kV / ±8 kV | ±8 kV / ±8 kV |

TI marks the selected part ACTIVE and MSL1/260°C. Its land-pattern drawing specifies a **stencil no thicker than 0.1016 mm** and nominal 0.05 mm mask opening beyond each pad. Preserve the land pattern; carry stencil and mask-process requirements into supplier DFM. [TI selected part](https://www.ti.com/product/TPD2EUSB30A/part-details/TPD2EUSB30ADRTR), [TI combined datasheet, sections 5–6 and DRT drawings](https://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf).

Nordic describes the nRF52840 USB data interface as supplied from its internal 3.3 V USB regulator; the regulator specification is 3.0–3.6 V. This supports using the selected 3.6 V protector on normal D+/D− signaling. It does **not** prove immunity to line overshoot or every cable. [Nordic USB supply specification](https://docs.nordicsemi.com/r/bundle/ps_nrf52840/page/power.html).

**Do not connect this part to VBUS or claim sustained VBUS-to-data fault protection.** Its 4 V DC absolute limit is below a 5 V USB supply. The lower breakdown provides a different pulse-clamping response, but neither the data sheet nor a clean PCB DRC proves the protected MCU survives a sustained DC short. Normal signal amplitudes, enumeration, hot-plug, cable variation and assembled-product ESD must be measured.

## Capacitors: verified 16 V part for the existing three fitted positions

TDK identifies C1005X7R1C104K050BC as **Production**, 100 nF ±10%, 16 V, X7R, with **1.00 ±0.05 × 0.50 ±0.05 × 0.50 ±0.05 mm** body dimensions. The original literal C1005X7R1A104K050BC was not verified as a valid orderable code. TDK's real older 10 V `…1A104K050BB` is NRND and names the chosen 16 V part as its recommended alternative, without guaranteeing interchangeability. Our selection is based on the actual E1 application as well as that recommendation. [TDK selected part](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1005X7R1C104K050BC), [TDK older 10 V part](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1005X7R1A104K050BB).

The existing generic IPC 0402 footprint has a 0.40 mm gap and 0.56 ×0.62 mm pads. It accepts this 1005 body; it is not identical to every dimension in TDK's example land recommendation. Keep copper fixed and use supplier stencil/fillet review for the existing land. The nominal STEP body is 1.0 ×0.5 ×0.5 mm; the oval CAD's 1.4 ×0.9 ×0.7 mm assembly guard already covers the new part's 1.05 ×0.55 ×0.55 mm maximum.

| Reference | Actual connection | Role |
|---|---|---|
| C17 | 3V_MAIN to GND | Local NAND supply bypass, alongside C18 |
| C19 | 3V_MIC to GND | Local microphone bypass, alongside C10 |
| C20 | 3V_MIC to GND | Optional microphone bypass; keep DNP |
| C22 | 3V_MAIN to HAPTIC_NEG | Across the motor terminals, not a ground bypass |

Three volts is 18.75% of the chosen voltage rating. That ratio alone says nothing about retained capacitance. X7R capacitance changes with DC voltage, temperature, aging and lot; a nominal 100 nF marking is not a guaranteed 100 nF in use. The manufacturer publishes a DC-bias and impedance characterization sheet as reference data, not production minimums. These are supplementary bypass/noise capacitors, not replacements for the larger regulator capacitors. [TDK characterization sheet](https://product.tdk.com/en/system/files/dam/doc/product/capacitor/ceramic/mlcc/charasheet/c1005x7r1c104k050bc.pdf).

A separate visual read of TDK's live reference graphs found approximately **92 nF at 3 V** (about 95–96 nF at 2 V and 88 nF at 4 V). The impedance curve is approximately 16 Ω at 100 kHz, 1.6–1.8 Ω at 1 MHz and has a 15–20 mΩ minimum around 30 MHz. These are rounded graph readings, not guaranteed specifications; the impedance plot does not explicitly state operating DC bias, so those impedance values must not be labeled “at 3 V.” They support retaining this part for supplementary high-frequency bypassing and motor-noise suppression, while the physical checks below establish actual rail and motor behavior.

For C22, diode D1 clamps HAPTIC_NEG toward 3V_MAIN during motor turn-off. The selected 16 V dielectric improves voltage headroom, while motor brush transients, harness inductance, local ringing and switching-current heating still depend on the physical build. Do not model this capacitor as an ideal transient suppressor or claim the higher voltage rating alone improves audio quality.

## Required physical confirmation, with these selections fixed

1. Inspect U4 orientation, solder joints, paste release and the ground-return connection on the first PCBA; confirm no D+/D− shorts or leakage before plugging in a host.
2. Measure D+/D− amplitudes and waveform quality, then enumeration and repeated hot-plug on representative USB cables and hosts. Conduct ESD tests on the assembled enclosure and port; a component ESD rating is not an enclosure test result.
3. Measure NAND and microphone supply droop/ripple at their pins during recording, NAND program/erase, BLE bursts and motor actuation. Check recovery after power interruptions and supply ramps.
4. Probe HAPTIC_NEG and the voltage across C22 during motor start, stop and PWM, including cold start and intended harness length. Confirm temperature rise, diode stress and microphone noise with motor pulses. Use the measured spectrum if a damping-network change is warranted.
5. Re-run native netlist/PCB parity and regenerate BOM, DNP list, positions and fabrication outputs after the parent applies the MPN/value metadata changes. Preserve C20's DNP flag and every unchanged pad/net.

These tests qualify the actual build; they are not requests for another component-selection approval.
