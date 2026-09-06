# Anticipy no-custom-PCB founder EVT firmware

## The decision

Use the **Seeed XIAO nRF52840 Sense + Adafruit 5769 Audio BFF + microSD** path for the four-day unit.

This is the shortest reliable path because Omi already publishes:

- this exact two-board circuit and a photographed assembly guide;
- Zephyr firmware for the XIAO's microphone, Opus audio, BLE streaming, button, SD storage, backlog transfer, battery reporting and haptic command;
- an iPhone app that speaks the same BLE protocol.

Do **not** switch this four-day build to the Adafruit XTSD board. XTSD is mechanically attractive, but it creates a new wiring/firmware variant that has not been exercised by Omi's DK2 build.

## Exact hardware-to-firmware map

| Job | Part / pin |
|---|---|
| Microphone | XIAO Sense onboard PDM microphone |
| Live iPhone stream | XIAO BLE, Omi audio service `19B10000-...` |
| Offline memory | Audio BFF microSD: D0 chip-select, D8 clock, D9 MISO, D10 MOSI |
| Button | Momentary button between D7/P1.12 and GND; active-low with the nRF52840 internal pull-up |
| Haptic | D6/P1.11 to a transistor driver; **never connect the motor directly to D6** |
| Battery | Protected 3.7 V 500 mAh LiPo on XIAO battery pads |
| Charging/flash | XIAO USB-C |

The Audio BFF's speaker circuitry remains on the ready-made board, but the four-day Anticipy unit does not need a physical speaker.

The upstream Omi DK2 guide puts its button across D4 and D5. Do **not** copy that one detail: those pins are the Sense board's I2C pair and share the onboard IMU bus. Anticipy's overlay moves the button to otherwise-unused D7, leaving D4/D5 untouched. D6 remains the separate haptic-control output.

## What this copy changes

This folder starts from Omi DevKit 2 firmware revision 2.0.10 and makes narrow founder-EVT fixes:

1. A missing/bad SD card no longer stops Bluetooth from starting.
2. The audio-file initialization use-after-free is fixed.
3. The one-file legacy backlog is created deterministically.
4. Short SD reads/writes and a corrupt saved offset are rejected safely.
5. The final BLE backlog packet no longer causes unsigned underflow.
6. A failed BLE notification no longer advances the download pointer.
7. Merely connecting a phone no longer disables offline capture before an audio/storage subscription exists.
8. The 440-byte offline blocks now preserve every encoded frame and zero-pad only unused space.
9. The button is moved off the D4/D5 IMU/I2C pair to D7/P1.12, active-low to ground.

`python3 host_checks.py` currently passes randomized pack/unpack tests for 10,000 frames, capacity arithmetic, the pin map and those source regressions.

## Build and flash

There are two reproducible build routes. Use GitHub Actions if the local computer does not already have Docker.

### Route A — GitHub builds the UF2

1. Create a new private GitHub repository and upload the **contents of this folder at the repository root**.
2. Open the repository's **Actions** tab.
3. Select **Build Anticipy EVT firmware** and press **Run workflow**.
4. Wait for the green check, open the run, and download the `anticipy-evt-uf2` artifact.
5. Verify the included SHA-256, then flash `Anticipy_EVT_NoPCB.uf2` using steps 5–7 below.

The workflow pins nRF Connect SDK 2.7.0, Zephyr SDK 0.16.5, West 1.3.0, Ubuntu 22.04 and the ARM toolchain. The workflow file and `west.yml` are included in this folder. This route has been syntax-checked here, but it has **not yet been run on GitHub Actions**.

### Route B — Omi's Docker build

1. Install and open Docker Desktop.
2. Put this folder at `omi/firmware/devkit` inside a clean checkout of [BasedHardware/omi](https://github.com/BasedHardware/omi).
3. From the repository root, run:

   ```bash
   chmod +x omi/firmware/scripts/build-docker.sh
   ./omi/firmware/scripts/build-docker.sh --clean
   ```

4. Confirm that `omi/firmware/build/docker_build/zephyr.uf2` exists.
5. Connect the bare XIAO by USB-C. Double-tap its tiny reset button. A drive named `XIAO-SENSE` appears.
6. Copy `zephyr.uf2` onto `XIAO-SENSE`. It reboots automatically.
7. Flash and test **before** soldering the battery and before sealing the case.

This environment did not contain Docker/NCS, so the edited firmware has **not yet been compiled here**. Do not call the UF2 released until the Docker build succeeds.

## Four-day go/no-go test

Run these in order on the actual assembled electronics:

| Gate | Pass means |
|---|---|
| Five cold boots | advertises as `Omi DevKit 2` every time |
| SD removed | BLE still advertises and streams |
| 60-minute live stream | phone receives continuous decodable Opus audio |
| Phone away for 20 hours | SD backlog exists and decodes after reconnect |
| Interrupted backlog drain | reconnect resumes from the saved 440-byte boundary |
| 16-hour battery run | unit stays alive; measured average is at most **26.56 mA** with the 15% reserve |
| 100 button presses | all register, no double-trigger |
| 1,000 haptic pulses | no reset, SD error, or brownout |

Passing a short test is not proof of 16-hour runtime or 20-hour retention. Those two timed gates must run on real hardware.

## Capacity, in toddler words

The recorder makes about 4,100 bytes each second. Twenty hours plus 15% safety space is under 350 MB, so a genuine 32 GB high-endurance microSD has vastly more room than required. The memory size is easy; power stability, SD reliability and successful backfill are the real tests.

## Source basis

- Omi's published hardware guide: `omi/hardware/triangle v2 w memory/README.md` in the upstream repository
- Omi SD boot blocker: [issue #9771](https://github.com/BasedHardware/omi/issues/9771)
- XIAO pin map: [Seeed XIAO nRF52840 guide](https://wiki.seeedstudio.com/XIAO_BLE/)
- Audio BFF pin map: [Adafruit Audio BFF guide](https://learn.adafruit.com/adafruit-audio-bff?view=all)
