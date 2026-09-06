# Independent electrical audit

## Like you are two

The electrical idea is good enough to build **three experiments**. The present
green-board files are not ready for a factory because four important parts are
still represented by the wrong footprints/net map and no copper is routed.

## Decision

- Architecture: **GO for an EVT redesign**.
- Present KiCad files: **NO-GO for fabrication**.
- Gerbers: deliberately absent.
- Customer shipment: held until built units pass the electrical and firmware
  tests below.

## Controlled architecture

| Job | Candidate | Audit result |
|---|---|---|
| Bluetooth/MCU | Raytac AN54LV-15 / nRF54L15 | viable; official 55-pad map, keepout and firmware pins must replace the old U1 gate |
| Power/charge | Nordic nPM1300 | viable; follow Nordic reference layout and validate the exact cell/NTC model |
| Audio | two Infineon IM69D128S | viable; 69 dB-SNR PDM parts, but sealed acoustics and codec load need measurement |
| Local storage | MK Founder MKDV4GCL-ABF | preferred over raw NAND; 481 MB usable with ECC, bad-block, wear and power-fail management |
| Haptics | TI DRV2605L + wired 7 mm ERM | viable after the A2/REG circuit is corrected and motor supply/audio noise are tested |
| Button | PTS841GMSMTRLFS | viable after its controlled four-pad land and actuator orientation replace the placeholder |
| Battery | BAT-ANT-200-001 | custom hold; public LP571225 comparator has no NTC |

## Two exact circuit corrections

1. **DRV2605L A2/REG is wrong in the checkpoint.** A2 is the driver's 1.8 V
   regulator output and needs the datasheet's 1 uF bypass to ground. It must not
   be tied/labeled as 3V0. Use net name `HAPTIC_REG`.
2. Every radio net ending in `*_TO_U1_PAD_TBD` remains unresolved. Replace the
   old zero-pad U1 gate with the official Raytac symbol/footprint and a reviewed
   firmware pin-allocation table before routing.

## Storage proof

Controlled write budget:

`5,000 bytes/s × 72,000 seconds × 1.15 = 414,000,000 bytes`

The selected managed device exposes about 481,000,000 usable bytes, leaving
67,000,000 bytes, or about 16.2%, for filesystem, journal, encryption and
recovery overhead. That passes the present requirement. It does **not** pass a
separate demand to keep another 20% free; that would require at least 517.5 MB.

Required firmware behavior:

- append fixed-duration encrypted chunks;
- keep a checksummed index and recover after sudden power loss;
- continue recording while the phone is absent;
- resume BLE upload from the last acknowledged chunk;
- delete local audio only after the iPhone confirms durable receipt;
- preserve current recording bandwidth while old audio back-syncs.

MKDV4GCL-ABF LGA-8 SPI pins from the controlled datasheet are: 2 CS, 3 CLK,
4 GND, 5 MOSI, 6 MISO, 8 VDD; pins 1/7 are DAT2/DAT1. It is not footprint- or
protocol-compatible with the W25N04KV placeholder.

## Battery proof

With a 200 mAh rated cell and a 15% capacity reserve:

`200 mAh × 0.85 ÷ 16 h = 10.625 mA average ceiling`

Use **10.0 mA or less** as the engineering target until cold, aged-cell,
recording, BLE, haptic and back-sync tests close. The managed flash can draw up
to roughly 35 mA while writing, so firmware must buffer and burst; a parts-list
estimate cannot prove runtime.

The production pack must be supplier-signed at **27.0 × 12.5 × 6.0 mm maximum**
including PCM, insulation, weld tabs, leads and a 10 kΩ NTC, with correct
polarity plus pack-applicable UN38.3, IEC 62133-2 and SDS evidence.

## Bench tests before sealing three EVT units

1. Current at sleep, continuous record, BLE stream, local write, back-sync,
   haptic and charging.
2. Sixteen-hour worst-case runtime with 15% capacity reserve.
3. Twenty-hour offline capture, forced resets during writes, reconnect and
   byte-for-byte back-sync verification.
4. iPhone screen-off/background/reboot/Bluetooth-off recovery.
5. Dual-mic audio with motor pulses, charger attached, pocket rubbing and wind.
6. Charge temperature, rail droop, PMIC fault behavior and low-battery shutdown.
7. Closed-enclosure RF range/throughput and regulatory host-integration review.

## Primary evidence

- Nordic nPM1300: https://www.nordicsemi.com/Products/nPM1300
- TI DRV2605L datasheet: https://www.ti.com/lit/ds/symlink/drv2605l.pdf
- Infineon IM69D128S: https://www.infineon.com/part/IM69D128S
- Raytac AN54LV-15: https://www.raytac.com/product/ins.php?index_id=169
- Managed SD-NAND datasheet: https://datasheet.lcsc.com/datasheet/pdf/861dc17860b6ca6b6ed9c649f697f4e2.pdf?productCode=C51966232

Passing the arithmetic and architecture only authorizes finishing the board for
three EVT units. It does not prove 16 hours, 20 hours, reliable iPhone
background operation, RF compliance or customer safety.
