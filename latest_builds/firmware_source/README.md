# E1P1 source for the released first-power image

This is the exact application source behind `Anticipy_E1P1_BUCK2_MAIN_FIRST_POWER.hex`, SHA-256 `32f07cc6a49089f5488ea34ace23362a1aee2d62906eb0dfbf6f122faeda38d7`. All 253 application files match the retained programming manifest. The HEX itself belongs in the adjacent handoff `programming` folder; it is not duplicated here.

**Supervised bench firmware only. Charging is disabled. Offline recording is not implemented. No physical board has been programmed or qualified by this handoff.**

## What is included

- `app/`: byte-preserved application, board definitions, configuration, embedded Opus sources and their notices, and host logic tests.
- `build.sh`: the same build invocation used by the source package.
- `tests/`: native-netlist/device-tree power-contract test and a source/image hash verifier.
- `provenance/`: matching application manifest, original build receipt, later programming receipt, generated configuration/device tree, and the current manufacturing schematic netlist. Generated text here is evidence, not source to edit.
- `Dependencies.json` and `Source_Image_Relationship.json`: environment and source/image linkage.

## Rebuild

Install the complete Nordic nRF Connect SDK **2.7.0** workspace and matching toolchain bundle **f8037e9b83** through Nordic tooling. The original build used Zephyr `v3.6.99-ncs2`, west 1.2.0, CMake 3.21.0 and Python 3.9.6. The [SDK release](https://github.com/nrfconnect/sdk-nrf/tree/v2.7.0) and its [dependency manifest](https://github.com/nrfconnect/sdk-nrf/blob/v2.7.0/west.yml) identify the upstream dependencies. This snapshot does not contain the SDK or compiler.

Run from this folder, setting actual absolute installation paths:

```sh
export ANTICIPY_NCS_ROOT=/absolute/path/to/ncs/v2.7.0
export ANTICIPY_TOOLCHAIN_ROOT=/absolute/path/to/ncs/toolchains/f8037e9b83
export ANTICIPY_E1P1_BUILD_ROOT="$PWD/build"
bash build.sh
```

The application target is `anticipy_e1/nrf52840`. `app/CMakeLists.txt` sets the board root to the application. `build.sh` builds into `$ANTICIPY_E1P1_BUILD_ROOT/target`; the resulting image is `target/zephyr/zephyr.hex` beneath that build root. The default installation paths in the script reflect the original Mac environment. On a different host, use the matching Nordic toolchain environment; its directory layout may require adapting the environment setup, not the application.

The existing target linked **278,692 bytes of flash and 177,244 bytes of RAM**. Those are linker allocations. This export does not rerun the target build or claim a relocated build will be byte-identical. The retained source, original HEX and retained build HEX were independently hashed and agree with the receipts. SDK worktree cleanliness and every SDK dependency commit were not separately audited in this export.

## Verify source and run the included checks

A Python 3 interpreter and a host C compiler (`clang` by default, or set `CC`) are sufficient for these checks:

```sh
python3 tests/verify_source.py
bash app/tests/run_firmware_tests.sh
python3 tests/check_power_contract.py provenance/target.dts provenance/current_native_netlist.xml
```

To verify a copied released HEX as well:

```sh
python3 tests/verify_source.py --hex ../E1P1/programming/Anticipy_E1P1_BUCK2_MAIN_FIRST_POWER.hex
```

After an actual rebuild, rerun the power-contract checker using the newly generated `build/target/zephyr/zephyr.dts` in place of the retained device tree. The 23 power checks establish revision pairing; host logic tests establish bounded transport/recovery behavior. Neither proves physical power rails, microphone audio, Bluetooth reliability or runtime. The broader phone/codec tests cited by the original build receipt are prior results; they require the separate product/iOS source and are not represented as self-contained tests in this snapshot.

## Correct board and current limits

Use only the E1P1 **BUCK2-main** circuit. BUCK2 supplies the 3.0 V main rail; BUCK1 is the unloaded 2.5 V auxiliary rail and is turned off after initialization. The older E1 BUCK1-main image is incompatible. The current manufacturing PCB SHA is `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`. Its updated netlist passes the same power contract; the original build receipt still names the earlier oval PCB geometry and is retained unchanged as historical build evidence.

This image implements PDM microphone capture, 16 kHz mono / 32 kbit/s Opus, encrypted BLE subscription gating, bounded queues, recording LED, power/temperature diagnostics, watchdog and a **non-destructive NAND ID probe**. It does not write or erase NAND. Disconnected audio retention is not implemented. Haptic behavior, USB data, signed updates and complete customer ownership are also not implemented. There is no bootloader or USB DFU.

The unchanged `app/README.rst` contains a superseded 200 mAh battery candidate note. For the current handoff, use the hardware BOM's exact protected Jauch 246501 pack (350 mAh minimum), separate temperature sensor and current assembly instructions. Neither that older note nor the inactive charger configuration authorizes charging. Battery calibration, charging faults/temperature, storage recovery, offline backfill, RF/acoustics, phone-device integration and 16-hour runtime require engineering work and physical validation.

Follow [the matching programming instructions](../E1P1/programming/Programming_Readme.md) for supervised first power and SWD programming. Begin with the battery disconnected and a reviewed current-limited supply. No programming operation is performed by any command in this source-export README.

## Source notices

Original file headers and `app/OPUS-1.2.1-LICENSE.txt` are preserved. No new blanket license is granted by this export. CMakeLists.txt is authoritative for compiled files; retained legacy helpers and unused codec files are source ancestry, not enabled features.
