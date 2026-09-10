# C13 and C23: selected procurement substitutions

Engineering review: 9 September 2026. These are concrete selections for the E1P1 prototype release. This report does not alter the PCB or schematic, reserve inventory, place an order, or qualify the complete wearable.

## Selection

| Reference | Original MPN | Selected MPN | Decision |
|---|---|---|---|
| C13 | TDK C0603X5R1C104K030BC | **TDK C0603X5R1E104K030BB** | Keep 100 nF ±10%, X5R, 0201 and the existing land pattern; raise rated voltage from 16 V to 25 V. Availability-driven engineering substitution. |
| C23 | Yageo CC0805MKX5R5BB476 | **Murata GRM21BR60J476ME01L** | Keep 47 µF ±20%, 6.3 V, X5R and 0805. Manufacturer maximum height is 1.45 mm. Select a stocked exact MPN with documented operating-bias behavior. |

Both selections are nonpolarized MLCCs. No pin swap, net change, added part, or PCB outline change is needed for these substitutions. The release editor must update native schematic, board properties, library metadata, BOM and procurement sheets consistently, then rerun parity/ERC/DRC. C13's displayed value becomes `100nF 25V X5R`.

## Actual circuit evidence

Source board: `outputs/Anticipy_Oval_E1_2026-09-09/pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb`; SHA-256 verified in this pass: `137bf2814371842fb071526d6b6c3c138dfceb2d92459d390f8d55ac541d3a44`.

The companion `pcb/verification/native_netlist.xml` places **C13.1 and C23.1 on `/3V_MAIN`; both pin 2 connections are `/GND`**. C13 is the PMIC logic bypass; that same rail connects to U2 nPM1300 VDDIO pin 12 and BUCK2OUT pin 32. C23 is the haptic rail bulk capacitor; motor M1 pin 1 and flyback diode D1 cathode are also on this rail. C22 is a separate motor suppression component and is not replaced by this decision.

The shipped firmware device tree `firmware/app/boards/anticipy/anticipy_e1/anticipy_e1_nrf52840.dts`, line 31, programs BUCK2 minimum, maximum and initial voltage to **3,000,000 µV**, always on. Thus C13 and C23 normally see 3.0 V, not battery voltage or USB 5 V. This is a design/firmware contract, not a measured rail-voltage result. First power-up still must establish the actual voltage and startup behavior.

## C13 electrical and mechanical comparison

The [original TDK page](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C0603X5R1C104K030BC) and [selected TDK page](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C0603X5R1E104K030BB) both currently say **Production**. Earlier statements that the original is NRND are not supported by these current manufacturer pages. No manufacturer-mandated successor declaration was found.

Both are 100 nF ±10%, X5R (±15% over −55 to +85 °C), reflow parts, with body **0.60 ±0.03 × 0.30 ±0.03 × 0.30 ±0.03 mm**. Maximum body is therefore **0.63 × 0.33 × 0.33 mm** for either part. Terminal width is at least 0.10 mm and terminal spacing at least 0.20 mm. The replacement has 25 V rating versus 16 V, the same maximum 10% dissipation factor, and a published minimum insulation resistance of 5 GΩ versus 1 GΩ. The increased voltage rating does not itself guarantee effective capacitance.

Both exact manufacturers' interactive DC-bias plots were inspected. Approximate graphical readings at 3.0 V are **about 50 nF for the original 16 V part and about 60–70 nF for the selected 25 V part**. These are typical/reference graph values, not minimum guaranteed values; the page explicitly labels its graphs reference-only. This comparison supports the choice rather than assuming that every 100 nF 0201 capacitor behaves identically. TDK publishes the selected part's [precision SPICE model](https://product.tdk.com/system/files/dam/tvcl/capacitor/ceramic/mlcc/spice_p/commercial_general/c0603/c0603x5r1e104k030bb_p.mod) and [bias model](https://product.tdk.com/system/files/dam/tvcl/capacitor/ceramic/mlcc/hspice/commercial_general/c0603/c0603x5r1e104k030bb_b_hspice.mod); links were verified on the product page, but model-file contents were not fetched in this pass.

The native C13 footprint has copper pads 0.46 × 0.40 mm at ±0.32 mm, and separate paste apertures 0.318 × 0.36 mm at ±0.345 mm. Body fit is unchanged. This is the existing custom 0201 pad/paste choice; this report does not certify stencil yield or claim it is identical to TDK's recommended land dimensions. The assembler must use its validated 0201 stencil and placement process. Do not enlarge or move the capacitor merely to source this replacement.

## C23 electrical and mechanical evidence

The exact [Murata manufacturer specification](https://pim.murata.com/asset/pim4/ceramicCapacitorSMD/GRM21BR60J476ME01-01A-EN_PDF_CERAMICCAPACITORSMD), reference sheet dated **25 June 2026**, was visually read in the browser. Page 2 specifies **2.00 ±0.20 × 1.25 ±0.20 × 1.25 ±0.20 mm**, 47 µF ±20%, DC 6.3 V, X5R, −55 to +85 °C, flow/reflow. Maximum body is **2.20 × 1.45 × 1.45 mm**. End termination dimension is 0.2–0.7 mm; middle spacing is at least 0.7 mm. Packaging suffix **L** is 180 mm plastic tape, 8 mm tape width, 4 mm pitch, 3,000 pieces per reel. Cut tape from that exact MPN avoids a full-reel purchase.

The native C23 footprint has 1.00 × 1.45 mm copper/paste pads centered at ±0.95 mm: 0.90 mm inner gap, 1.90 mm center spacing, 2.90 mm outer span. Its courtyard is 3.40 × 1.96 mm. The selected maximum body fits this existing 0805 location; solder standoff remains additional to the 1.45 mm body height and must remain in the mechanical assembly allowance. This is an ordinary ceramic termination, not a flexible termination; avoid board bending during depaneling and enclosure assembly.

The actual part family **GRM21BR60J476ME01** was selected in [Murata SimSurfing](https://ds.murata.com/simsurfing/mlcc.html), database update **2 September 2026**, where it is in production. Its primary-source curves were generated and visually inspected:

| Model condition | Approximate graph reading | Meaning |
|---|---|---|
| Capacitance versus DC bias, 25 °C, AC 0.5 Vrms | About 49 µF at 0 V; **20 µF at 3.0 V**; 14 µF at 4 V; 8 µF near 6.3 V | A nominal 47 µF cannot be budgeted as 47 µF on this rail. |
| Precise series impedance model, **DC 3 V, 25 °C** | About **0.08–0.10 Ω at 100 kHz**; minimum in the low milliohm range near **1–2 MHz** | Useful local bulk/decoupling behavior; not a model of PCB via/trace parasitics. |
| Same model, real component of impedance R | Roughly **1.5–2.5 mΩ over 0.1–1 MHz** | Typical model ESR, not guaranteed worst-case ESR or assembly resistance. |

Values are rounded readings from graphs, not CSV-exact results, not guaranteed production minima and not a board simulation. CSV export was attempted, but the browser blocked the generated download; no fabricated numeric data file or successful downloaded model is claimed. The graph has no allowance for component tolerance, aging, solder stress or the board's wiring. The exact original Yageo DC-bias curve was not obtained, so no assertion is made that the Murata has superior capacitance under bias to that original.

Murata marks this part **Derating1**. Its [manufacturer explanation](https://www.murata.com/products/capacitor/ceramiccapacitor/help/caution?intcid5=com_xxx_xxx_cmn_hd_xxx) says the endurance test voltage is below 150% of rating. This label is not proof of a 50% rated-voltage operating prohibition. E1's 3.0 V nominal is 47.6% of the 6.3 V rating. Actual maximum rail voltage, ripple and temperature still must stay within the specification.

For perspective only, a capacitor alone supplying an assumed 100 mA load step for 100 µs would droop about **0.50 V with 20 µF**, versus 0.21 V if one incorrectly used the 47 µF nominal value. The actual buck regulator and the other parallel rail capacitors also supply this transient; neither calculation predicts the complete board. Measure main-rail droop during motor start, radio transmission and NAND writes on the first article. Do not call the motor transient qualified from nominal capacitance or DRC alone.

## Fresh procurement evidence

Stock was read from live product-page UI on 9 September 2026, approximately **13:50–13:55 UTC**. It is available website inventory, not reserved stock, not inventory already owned in Boston, and not a promised Saturday delivery.

| Reference | Distributor and exact order code | Live stock | USD unit price at quantity 20 | 20 fitted pieces | Optional 22-piece line |
|---|---|---:|---:|---:|---:|
| C13 | [DigiKey 445-13671-1-ND](https://www.digikey.com/en/products/detail/tdk-corporation/C0603X5R1E104K030BB/3950907), cut tape | **933,292** | **0.050** (10+ tier) | **1.00** | **1.10** |
| C23 | [DigiKey 490-GRM21BR60J476ME01LCT-ND](https://www.digikey.com/en/products/detail/murata-electronics/GRM21BR60J476ME01L/10703358), cut tape | **777** | **0.188** (10+ tier) | **3.76** | **4.14** rounded |

Two extras per reference are a transparent 10% planning allowance, not a promise of sufficient feeder leader or attrition material. The contract assembler may require larger cut-tape quantities or reel service. Prices exclude freight, taxes and assembly.

The original C23's live Mouser page showed **0 stock** during this pass, with a December incoming date and a long factory lead time. The earlier cached search count of approximately 24,952 must not be treated as fresh stock. Current Newark inventory was not verified; an old indexed quantity does not supersede live evidence. Choosing the above Murata closes the exact-purchasable-component selection for C23 without assuming an unavailable original will arrive.

## Release and first-article actions

1. Apply the two exact MPNs, manufacturer strings, C13 voltage value and datasheet links across native sources and release exports.
2. Keep the proven net identities and preserve existing pad locations; rerun electrical parity and DRC after the release editor's other changes.
3. Use the 1.45 mm C23 maximum body height plus solder clearance in the case stack. Have the assembler review the existing C13 0201 paste apertures with its actual stencil.
4. Purchase only after checking current stock and assembler-owned inventory; no inventory is allocated by this report.
5. First article: verify BUCK2 startup/steady 3.0 V, PMIC VDDIO behavior, and rail droop during the combined motor/radio/storage transient. These hardware tests remain necessary for either original or replacement parts.

**Decision:** implement these two substitutions in the prototype release. They resolve practical part selection while retaining the current circuit and package classes. They do not imply a physically tested or finished customer product.
