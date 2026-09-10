# E1P1 first-power bench image

Use **Anticipy_E1P1_BUCK2_MAIN_FIRST_POWER.hex** with the E1P1 BUCK2-main PCB in this package. This is the existing freshly linked diagnostic/live-audio bench firmware, not a finished offline-recording product. **Charging is disabled. No board has been programmed or physically tested for this handoff.**

HEX SHA-256: `32f07cc6a49089f5488ea34ace23362a1aee2d62906eb0dfbf6f122faeda38d7`.

Its original 9 September build used NCS 2.7.0, toolchain f8037e9b83, target `anticipy_e1/nrf52840`. The image matches that build receipt and retained build output; the dependency dry run reports no work required. All 23 firmware/native-netlist power checks pass against this package's current schematic. Exact source/build hashes are in `Programming_Receipt.json`.

## Five fixture connections

All five are 1 mm test pads on the **back copper side**. These are native KiCad XY coordinates; do not reverse the connection order by eye when viewing the back.

| J-Link signal | PCB pad | Net | Native XY, mm |
|---|---|---|---|
| SWDIO | TP1 | SWDIO → U1 pin 51 | 29.5, 35.0 |
| SWCLK | TP2 | SWDCLK → U1 pin 53 | 31.8, 35.0 |
| nRESET, optional | TP3 | RESET → U1 pin 40 | 34.1, 35.0 |
| VTref, sense input | TP4 | 3V_MAIN | 36.4, 35.0 |
| Ground | TP5 | GND | 38.7, 35.0 |

Use the probe adapter's documented signal mapping. **VTref senses the board's voltage; it does not power the board.** Do not apply 5 V to TP4. [SEGGER VTref documentation](https://kb.segger.com/VTref).

## First programming

1. Leave the external battery disconnected. Inspect the PCBA and check for shorts. Use a reviewed, current-limited 5 V bench input through a USB-C breakout/J1; verify the main rail at TP4 before connecting the probe. Do not connect a second uncontrolled power source.
2. Connect ground and the four remaining probe signals above. In J-Link Commander select `NRF52840_XXAA`, interface `SWD`, initially `1000` kHz. The physical RESET pad is optional: this HEX contains no UICR records, so confirm the module's reset-pin configuration before relying on TP3 as a hardware reset.
3. From the `programming` directory, an operator can launch `JLinkExe -device NRF52840_XXAA -if SWD -speed 1000 -AutoConnect 1` (`JLink.exe` on Windows), then enter:

```text
r
h
loadfile Anticipy_E1P1_BUCK2_MAIN_FIRST_POWER.hex
r
h
```

4. Confirm the tool reports successful programming/verification. `loadfile` performs verification by default. Keep the target halted until the rail checks are ready; then enter `g` and capture RTT logs. No programming command has been executed by this handoff. [SEGGER Commander instructions](https://kb.segger.com/J-Link_Commander).
5. Expect BUCK2/3V_MAIN at 3.0 V; BUCK1/TP12 is intentionally off after initialization. Check that microphone power follows capture state and charging remains off. Expected logs include `E1P1 BUCK2 main; BUCK1/TP12 off after init; charging disabled` and a non-destructive NAND identification result. Record actual measured rails/current and stop on abnormal behavior.

This image supports the bench PDM/Opus/BLE live-audio path and NAND identification only. **Offline NAND recording, ECC/bad-block recovery, encrypted backfill, signed OTA and customer ownership are incomplete.** There is no bootloader or USB DFU in this image. Battery charge qualification, physical audio/RF testing and measured 16-hour runtime remain unfinished; keep charging disabled when progressing beyond first power.
