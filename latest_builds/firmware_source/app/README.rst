Anticipy E1P1 BUCK2-main first-article firmware
==============================================

Target: corrected custom Anticipy E1P1 four-layer PCB, Raytac MDBT50Q nRF52840, nPM1300,
one Same Sky PDM microphone, Macronix MX35LF4GE4AD NAND. NCS2.7.0,
board anticipy_e1/nrf52840, prj.conf. This source is not a XIAO image.

Build from an installed NCS2.7.0 workspace with absolute source/build paths::

  west build -b anticipy_e1/nrf52840 /path/to/firmware -d /path/to/build

The supplied HEX starts at address0; ELF includes debug symbols. No UF2,
USB DFU, OTA, or bootloader is supplied. Program only the E1 target through
SWD with target reference3.0V, SWDIO, SWDCLK, GND and optional RESET. Do not
power the target simultaneously from a debugger output and its own supply.
First flash is a supervised current-limited bench operation.

Implemented
-----------

BUCK2 keeps the common3.0V MCU/NAND supply always on. BUCK1 is the unloaded
2.5V auxiliary and is turned off after regulator initialization (TP12 off).
Do not flash this image onto the older BUCK1-main E1 board, and do not use
the older E1 firmware on corrected E1P1.

 PMIC initialization and readback, mic power
control with synchronized shutdown, HF-clock management,100ms PDM warm-up,
32kbps CBR CELT Opus, encrypted fresh BLE subscription gating, bounded
transport queues, red100ms/400ms recording pulse, battery voltage estimate,
custom TDK curve8307 temperature conversion, non-destructive NAND ID probe,
30s main-thread watchdog and RTT diagnostics. REG1 DC/DC is enabled using
the inductor inside the Raytac module; VDDH REG0 is not enabled.

Prototype limits
----------------

Charging remains DISABLED. Its40mA/4.2V candidate configuration and custom
NTC thresholds require a confirmed protected200mAh pack and physical
sensor/fault/thermal tests before any enablement. No NAND write/erase,
offline recording, encrypted storage, backfill, haptics or USB data stack is
implemented in this image. No physical board has been flashed or tested.

One encrypted persisted bond is not owner authentication. The first nearby
central can claim an unbonded unit; first enrollment is a controlled lab
operation. Consumer ownership transfer/physical enrollment and signed update
architecture remain product release gates. Battery percent is uncalibrated;
no runtime claim follows from compilation. Phone timestamps are estimated
arrival-time audio positions, not a synchronized pendant RTC.

The bundled source retains upstream notices. CMakeLists.txt is the authority
for compiled files; unused legacy source helpers are ancestry, not enabled
E1 recovery or transport features. See ../receipts/verification.json and test receipts
in the E1P1 firmware package for exact binaries and measured software results.
