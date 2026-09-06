# Anticipy production electrical audit

Date: 2026-08-29  
Scope: legacy `FLUX_MASTER_PROMPT.md` / `PRODUCTION_BOM.csv`, plus the proposed production architecture `AN54LV-15 + nPM1300 + MKDV4GCL-ABF + 2x IM69D128S + DRV2605L`. This is a design audit, not a fabrication release.

## Executive decision

**NO-GO for PCB fabrication or production release. GO only for completing the schematic/PCB redesign and building a tightly controlled EVT spin after every fatal item below is closed.**

The proposed architecture is electrically plausible, and **MK Founder MKDV4GCL-ABF managed SD NAND is the preferred storage choice**. It is substantially safer than raw W25N04KV because it includes ECC, bad-block management, wear leveling, garbage collection, read-disturb handling, and data refresh. It is not a drop-in replacement, does not make the host filesystem power-fail atomic, and its capacity margin is narrow.

| Class | Finding | Exact release action |
|---|---|---|
| **Fatal** | The current U1 CAD object is the `453-00224R / BL54L15U_PINMAP_GATE` placeholder with unresolved `_TO_U1_PAD_TBD` nets, not a released AN54LV-15 implementation. | Replace it with a verified AN54LV-15 symbol and footprint; map every signal to an actual Raytac pad; run ERC/DRC and compare the generated pad/net report against the Raytac pin table. |
| **Fatal** | AN54LV-15 contains a chip antenna, while the current PCB still carries an external 2.4 GHz antenna/matching path and `RF_FEED_TO_U1_PAD_TBD`. | For **AN54LV-15**, delete the external antenna and matching network and enforce the Raytac antenna keep-out on every copper layer and against battery/metal. If an external antenna is required, select **AN54LV-K15** and redo RF layout and regulatory analysis. |
| **Fatal** | DRV2605L ball A2 is labeled `3V0` in the schematic but mapped to `HAPTIC_REG` in the PCB/pad map. A2 is the internal regulator output, not a supply input. | Connect A2 only to `HAPTIC_REG` and a 1 uF capacitor to GND. Connect C2/VDD to the haptic supply and its 1 uF plus 0.1 uF decoupling. |
| **Fatal** | The legacy prompt gives the wrong MKDV pinout. It places CMD/VDD/CLK/GND on the wrong pins. | Use the manufacturer pinout: 1 DAT2, 2 DAT3/CS, 3 CLK, 4 GND, 5 CMD/DI, 6 DAT0/DO, 7 DAT1, 8 VDD. In SPI mode: CS=2, SCLK=3, MOSI=5, MISO=6, GND=4, VDD=8; 1 and 7 are reserved. |
| **Fatal** | The MK package drawing depicts eight perimeter lands and a center feature labelled `9`, but the electrical pin table defines only pins 1-8 and the datasheet does not provide an unambiguous recommended PCB land pattern for that feature. | Obtain a controlled land-pattern drawing from MK Founder that explicitly states the electrical and paste treatment of pad/feature 9. Do not guess, and do not reuse a WSON-8 exposed-pad footprint. |
| **Fatal** | Changing from W25N04KV raw QSPI NAND/WSON-8 to MKDV4GCL-ABF managed SD NAND/LGA is a new interface and footprint. | Replace symbol and footprint, rename nets to SD/SPI, implement the SD/SPI initialization/command layer, and validate actual reported sector count. |
| **Fatal** | Battery pack, protection circuit, connector/polarity, NTC, charge current, and fuel-gauge model are not frozen. Runtime and charging safety therefore cannot be signed off. | Release a controlled battery drawing and signed cell/pack datasheet; freeze minimum capacity, maximum allowed charge current, PCM thresholds, exact 10 kOhm NTC, connector/polarity, temperature range, and nPM1300 fuel-gauge profile. |
| **Fatal** | No validated simultaneous-load or low-battery rail budget exists. The 3.0 V buck is rated 200 mA, but motor stall/overdrive, NAND write, radio/CPU, and microphone peaks have not been combined. | Measure the final actuator and use worst-case datasheet peaks; prove 3V0 remains within every load's minimum voltage during storage write + radio TX + haptic at cold/depleted battery. Move DRV2605L VDD to VSYS if the 3V buck cannot pass. |

## Component-by-component audit

### 1. Raytac AN54LV-15

Manufacturer status and package: Raytac presents AN54LV-15 as a current nRF54L15 module, 6.4 x 8.4 x 1.5 mm, 1.7-3.6 V, -40 to 105 C, with integrated chip antenna. Product page and current specification: [Raytac AN54LV-15 product](https://www.raytac.com/product/ins.php?index_id=169), [Raytac AN54LV-15 specification download](https://www.raytac.com/download/index.php?index_id=83).

Release requirements:

- Use an orderable packaging code, not only the model name: `MD-240A8-007` (PET tray), `MD-240A8-007A` (APET tray), `MD-240A8-007R` (13-inch reel), or `MD-240A8-007R7` (7-inch reel), as listed by Raytac.
- Pad 20/VDD_NRF requires the reference decoupling implementation; pad 28/DCC and the specified 4.7 uH network are required to use the DC/DC mode. Omitting it leaves the SoC in LDO operation and changes the runtime budget.
- Pads 32/33 are XL2/XL1. Either fit the 32.768 kHz crystal and tuned load network or explicitly freeze firmware to a supported internal LF clock configuration.
- Pad 43 is NRESET; pads 46-55 are ground for the chip-antenna variant. Implement the full ground and antenna keep-out geometry from the manufacturer drawing.
- The module exposes QSPI aliases, but MKDV4GCL only needs four SPI wires. One valid mapping is CS pad 10/P2.05, SCLK pad 17/P2.01, MISO pad 14/P2.04, MOSI pad 24/P2.02. Freeze this or another conflict-free mapping in both the CAD netlist and firmware devicetree.
- Preserve SWDIO pad 9, SWDCLK pad 11, NRESET, ground, and power on an accessible production/debug fixture.

Nordic's nRF54L15 PDM peripheral supports two microphones sharing one data line and the required PDM clock range, so the dual-microphone architecture is valid: [Nordic nRF54L15 PDM](https://docs.nordicsemi.com/r/bundle/ps_nrf54l15/page/pdm.html).

### 2. Nordic nPM1300

The architecture is valid: nPM1300 provides two 200 mA bucks and configurable 50 mA LDO / 100 mA load-switch resources, plus battery charger and fuel-gauge functions. Primary sources: [nPM1300 product](https://www.nordicsemi.com/Products/nPM1300), [buck specification](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/chapters/core_components/buck/doc/frontpage.html), [charger](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/chapters/charger.html), [pin assignments](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/pin.html), [ordering information](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/chapters/ordering_info/doc/ordering_info.html).

Corrections and gates:

- Use the full ordering MPN `nPM1300-CAAA-R` or `nPM1300-CAAA-R7`; `nPM1300-CAAA` alone does not define shipping packaging.
- Each buck requires a 2.2 uH inductor meeting Nordic's current, saturation, DCR, and tolerance limits, and at least 4 uF **effective** output capacitance after voltage, temperature, aging, and tolerance derating. The proposed Samsung `CIGT201610EH2R2MNE` is in mass production and comfortably meets the inductor limits: [Samsung component page](https://product.samsungsem.com/pi/CIGT201610EH2R2MN.do). Exact capacitor MPNs and DC-bias curves remain an open release gate.
- Freeze USB current negotiation/configuration. CC1/CC2 may be strapped per Nordic guidance, but the default input-current behavior must not be assumed to support a higher charge current before firmware configuration.
- Use the nPM1300 charger-required NTC characteristic: 10 kOhm at 25 C, 1%, B25/50=3380 K, 1%, or obtain Nordic approval for a different characterized network.
- Select charge current and termination from the signed battery maximum, not from nominal 200 mAh capacity alone. The nPM1300 default charge current is not the production setting.
- The 3.0 V buck and MK NAND both approach their lower operating limit near a depleted battery. Set and validate a power-fail/undervoltage policy high enough to stop recording and commit a recoverable boundary before rails fall out of specification. Nordic's power-fail warning is a short reaction window, not a substitute for an atomic storage design: [nPM1300 power-fail comparator](https://docs.nordicsemi.com/r/bundle/ps_npm1300/page/chapters/core_components/plw/doc/frontpage.html).
- Prefer powering `FLASH_VDD` through an unused nPM1300 load switch if available. This allows a guaranteed MK hard reset and prevents back-powering through SPI pins. Otherwise prove the selected rail and GPIO sequence meets the MK power-cycle limits.

### 3. MK Founder MKDV4GCL-ABF managed SD NAND

**Recommended final storage device**, conditional on footprint clarification and system power-cut qualification.

The manufacturer-issued Rev 2.1 datasheet identifies a 4 Gbit SLC managed NAND, 481 MByte usable capacity, 2.7-3.6 V, up to 50 MHz, 19 MB/s read and 9 MB/s write, 60k P/E endurance, and internal ECC/BBM/wear leveling/garbage collection/read-disturb handling/data refresh/power-fail management: [MK Founder MKDV4GCL-ABF datasheet, manufacturer-issued PDF hosted by LCSC](https://datasheet.lcsc.com/datasheet/pdf/861dc17860b6ca6b6ed9c649f697f4e2.pdf?productCode=C51966232).

Use this exact SPI wiring:

| MK pin | Function | Production net |
|---:|---|---|
| 1 | DAT2, reserved in SPI | NC/reserved; follow manufacturer pull guidance |
| 2 | DAT3/CS | `SD_CS_N` |
| 3 | CLK | `SD_SCLK` through a provisioned 22 ohm source resistor |
| 4 | GND | GND |
| 5 | CMD/DI | `SD_MOSI` |
| 6 | DAT0/DO | `SD_MISO` |
| 7 | DAT1, reserved in SPI | NC/reserved; follow manufacturer pull guidance |
| 8 | VDD | `FLASH_VDD`, 2.2 uF + 100 nF local bypass |

Provision 10-100 kOhm pulls on active command/data/chip-select signals as required by the selected host mode, then freeze populated values after signal-integrity and boot-state tests. Keep all host pins low or high-impedance while VDD is absent. Meet the datasheet's power-up and hard-reset timing; do not allow I/O back-power.

Lifecycle risk is **closeable, not yet closed**. The 2025 manufacturer-issued datasheet shows a current family, but it does not state a formal lifecycle class or PCN/EOL commitment. Distributor/JLC inventory is useful for procurement, but is not lifecycle evidence. Obtain MK Founder or authorized-channel written confirmation of product status, PCN/EOL notification, lot traceability, and controlled land-pattern revision.

Why not W25N04KV: Winbond's W25N04KV is raw QSPI NAND. It can ship with initial bad blocks and acquire more; the host must inspect ECC/program/erase status, retire blocks, obey page-programming rules, wear-level, and recover from interrupted updates. On-die ECC is not a filesystem, FTL, or power-loss strategy. Use it only if a production-proven raw-NAND FTL already exists and is power-cut qualified. Primary sources: [Winbond W25N-KV product family](https://www.winbond.com/hq/product/code-storage-flash/qspi-nand/w25n-kv/?__locale=en), [Winbond W25N04KV datasheet landing page](https://www.winbond.com/hq/support/documentation/downloadV2022.jsp?__locale=en&level=1&xmlPath=/support/resources/.content/item/DA00-W25N04KV.html).

### 4. Dual Infineon IM69D128S microphones

The electrical topology is valid. Infineon lists IM69D128S as an active/preferred PDM microphone; orderable OPN `IM69D128SV01XTMA1`, PG-TLGA-5-2, 3.5 x 2.65 x 1.0 mm, 1.62-3.6 V. Sources: [Infineon product page](https://www.infineon.com/part/IM69D128S), [Infineon datasheet](https://www.infineon.com/assets/row/public/documents/24/49/infineon-im69d128s-datasheet-en.pdf).

Pinout is 1 VDD, 2 CLOCK, 3 DATA, 4 LR, 5 GND. Tie one LR low and the other high so they drive opposite PDM edges, and share CLOCK/DATA. The current electrical ties are suitable, but the CAD symbol must call pin 4 `LR`, not `GND`. Place the manufacturer-required 1 uF bypass at each microphone and reserve 100 nF locally; provision the recommended data-line damping/termination footprints and select values from oscilloscope results. Firmware must allow at least the specified startup time before accepting valid samples.

### 5. Texas Instruments DRV2605L

TI lists DRV2605L active. Exact primary sources: [TI DRV2605L product](https://www.ti.com/product/DRV2605L), [TI datasheet](https://www.ti.com/lit/ds/symlink/drv2605l.pdf).

For the YZF DSBGA top view, the exact pinout is:

| Ball | Function | Required connection |
|---|---|---|
| A1 | EN | MCU control or defined enable state |
| A2 | REG | `HAPTIC_REG`; 1 uF to GND only |
| A3 | OUT+ | Actuator + |
| B1 | IN/TRIG | Explicit GND if unused, or MCU trigger |
| B2 | SDA | I2C SDA |
| B3 | GND | GND |
| C1 | SCL | I2C SCL |
| C2 | VDD | Haptic supply; 1 uF + 0.1 uF to GND |
| C3 | OUT- | Actuator - |

The fixed I2C address is 0x5A. Pull SDA/SCL only to a voltage no higher than DRV VDD; size the pull-ups within the TI range after total bus capacitance is known. Relabel B1 as `IN/TRIG` even if it is intentionally grounded. Freeze the exact ERM/LRA part, resistance/impedance, rated voltage, overdrive limit, and mechanical load; configure DRV registers from those controlled actuator limits.

## Storage and runtime math

The present production storage contract appears to be 5,000 bytes/s for 20 hours plus 15% overhead:

- Raw payload: `5,000 x 72,000 = 360,000,000 bytes`.
- With 15% overhead: `414,000,000 bytes`.
- Nominal MK usable capacity: `481,000,000 bytes`.
- Remaining capacity: `67,000,000 bytes`, or 13.93% of the device (16.18% relative to the required image).

This passes only if **414,000,000 bytes is the all-in, measured stored image**, including filesystem allocation, journals, encryption/authentication tags, headers, indexes, bad-record recovery, and reserved update/service space. Requiring another 15% free-device margin would require about 487.1 MB and fail; 20% would require 517.5 MB and fail. The legacy prompt's 16 kb/s/190.4 MB calculation is a different requirement and must not coexist as a source of truth.

The battery arithmetic is likewise simple but not yet validated:

- Ideal 200 mAh / 16 h = 12.5 mA average.
- At 85% usable capacity: 170 mAh / 16 h = 10.625 mA average.
- At 80% usable capacity: 160 mAh / 16 h = 10.0 mA average.

Use **10.0 mA battery-terminal average as the conservative production gate** until cold, aging, discharge-rate, protection-cutoff, conversion-efficiency, and minimum-pack-capacity data justify another number. Known component peaks do not close the budget: two IM69D128S can consume about 1.3 mA total in normal high-rate mode, MK NAND specifies up to 35 mA during write, and radio/CPU/haptic peaks remain duty-cycle dependent. The motor is the dominant unbounded peak until its exact part is selected.

## Required close-out tests

1. **CAD identity test:** replace U1 and NAND placeholders; produce a machine-generated pad/net table and check every BGA/LGA pad against the cited manufacturer pin table. Run clean ERC and DRC. Inspect solder-mask and paste apertures, especially MK feature 9 and all WLCSP/DSBGA lands.
2. **Power integrity:** at minimum battery voltage and cold temperature, capture 3V0, VSYS, FLASH_VDD, nPM reset/POF, U1 reset, and NAND CS/CLK while forcing NAND write + radio TX + maximum allowed haptic overdrive. Pass only with no rail/load-limit violation, reset, I/O back-power, or corrupted record.
3. **Storage capacity:** read the device-reported sector count on samples from multiple lots. With the final filesystem and record format, store and verify at least 414,000,000 bytes of production records continuously for 20 hours. Account for every metadata and reserved byte.
4. **Power-cut campaign:** use append-only, sequence-numbered, CRC-protected records with explicit commit boundaries. Randomly remove battery power during data append, allocation, metadata update, file rollover, deletion, and near-full operation for thousands of cycles. On reboot, mount without manual repair, preserve all committed records, discard/truncate only the partial tail, and resume recording.
5. **Battery/runtime:** test minimum-capacity production packs in a sealed production-like unit with worst-case audio codec settings, microphone clock, BLE reconnect/backfill schedule, storage flush policy, and normal haptic/UI use. Pass 16 hours with the frozen reserve requirement and no thermal/charge fault.
6. **Audio:** verify left/right edge identity, phase, microphone open/short detection, startup muting, PDM current mode, sealed-enclosure sensitivity/SNR/SPL, haptic electrical/acoustic crosstalk, and environmental ingress performance. A microphone's component-level IP rating does not establish the enclosure rating.
7. **Haptic:** characterize actuator resistance/impedance and stall/overdrive current across lot, voltage, and temperature; tune DRV2605L calibration and library values; verify no brownout, false trigger, I2C fault, or audible contamination.
8. **Charge/fuel gauge:** validate charge current, NTC thresholds, USB input limit, termination, ship mode, fuel-gauge accuracy, and protection behavior using the exact battery and connector polarity.

## Legacy prompt/BOM disposition

Do not patch the legacy `FLUX_MASTER_PROMPT.md` and `PRODUCTION_BOM.csv` line by line. They describe a materially different MDBT50Q/MKDV2/T3902/BQ24075/AP2112/discrete-ERM design and contain at least one fatal flash pinout error. Retire them as historical inputs, then generate a new schematic-controlled BOM and assembly output from the corrected architecture.

One specific legacy claim is stale: TDK currently presents T3902 as a production product, so “EOL” must not be stated without an official PCN/EOL notice: [TDK InvenSense T3902 product page](https://www.invensense.tdk.com/en-us/products/t3902). This does not make T3902 the recommended microphone; it only corrects the lifecycle statement.

## Release criteria

Fabrication may proceed only after all eight fatal rows in the executive table are closed with controlled evidence, the exact BOM contains orderable manufacturer MPNs and verified footprints, machine ERC/DRC is clean, and the power/storage test plans have named owners and pass/fail limits. Production release additionally requires successful multi-lot EVT/DVT power-cut, runtime, charging, RF, audio, haptic, and environmental results.
