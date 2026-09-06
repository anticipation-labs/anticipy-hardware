# Anticipy founder-EVT firmware, in plain English

> **LAB ONLY — DO NOT CUSTOMER-SHIP:** microSD audio is plaintext. Record only synthetic or explicitly non-sensitive test audio until authenticated encryption at rest is implemented and physically tested.

## What this is

This is the flashable software for the **no-custom-PCB prototype**:

- Seeed XIAO nRF52840 Sense (the processor, Bluetooth and microphone);
- Adafruit product 5683 microSD BFF (offline memory);
- one button on D7;
- one MOSFET-driven vibration motor on D0;
- one protected 250 mAh LiPo.

It compiles to a UF2. It is an engineering-test build, not customer-release firmware.

## What the little boards do

1. The XIAO microphone hears sound at 16 kHz.
2. The XIAO shrinks it into 10 ms Opus packets at a fixed 16 kb/s target.
3. When an encrypted iPhone connection is subscribed, packets go live over BLE.
4. When live streaming is unavailable, packets are packed into 440-byte records on microSD.
5. On reconnect, the iPhone asks for old records from its last safely saved 440-byte boundary.

Opus DTX makes silence cheaper, but it does not remove time from the recording. There is no separate speech/no-speech event API yet.

## Exact wires

| Job | XIAO pin | Adafruit 5683 / external part |
|---|---|---|
| SD chip select | D6 / P1.11 | BFF default `TX` CS pad |
| SD clock | D8 / P1.13 | SCK |
| SD data to XIAO | D9 / P1.14 | MISO |
| SD data from XIAO | D10 / P1.15 | MOSI |
| Button | D7 / P1.12 | momentary switch to GND |
| Haptic | D0 / P0.02 | MOSFET gate, never the motor directly |
| Battery | BAT/GND pads | protected 3.7 V LiPo |

The 5683 default CS really is its TX pad. The haptic had to move to D0 so the two jobs do not fight for D6.

## Flash it

1. Keep the battery and motor disconnected for the first flash.
2. Plug the XIAO into USB-C.
3. Double-tap the tiny reset switch; the `XIAO-SENSE` drive appears.
4. Copy `Anticipy_Founder_EVT_v0.9.0.uf2` to that drive.
5. Wait for the board to reboot.
6. Test the bare electronics before soldering them into the shell.

The USB-C bootloader and charger are on the XIAO itself. The application has USB logging disabled to save power.

## What is proven here

- The complete C firmware compiles with pinned NCS 2.7.0 / Zephyr 3.6.99-ncs2 and Zephyr SDK 0.16.5.
- A UF2 is generated.
- Host tests round-trip 10,000 random stored frames.
- Host tests prove the 20-hour worst-case capacity arithmetic and MTU-safe resume logic.
- Pin conflicts, encrypted GATT permissions, bond persistence settings and the official XIAO battery-sense polarity are statically checked.

## What the physical unit must still prove

- microphone audio really decodes;
- the specific microSD mounts, writes and survives unplug/reboot cycles;
- power-cut loss is measured under both active speech and DTX silence (the same byte cache spans much longer during quiet audio);
- a real iPhone receives live and backfilled audio;
- every button press and haptic pulse works;
- average current is at most **13.28 mA** for a 250 mAh cell to clear 16 hours with 15% reserve;
- the unit survives the full mechanical and timed tests.

Do not record private customer audio with this EVT: the SD file is plaintext. See `SECURITY_RELEASE_GATES.md`.

## Important scope truth

The file has space for far more than 20 hours, but it is currently an append-only file, not a rolling 20-hour circular buffer. The iPhone can resume it in order, but there are no absolute timestamps or file-generation IDs. Those items, SD encryption, authenticated first pairing and real hardware validation are customer-release gates—not optional polish.
