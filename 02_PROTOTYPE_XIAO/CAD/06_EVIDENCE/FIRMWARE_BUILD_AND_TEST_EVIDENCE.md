# Firmware build and static-test evidence

## Primary candidate — ordered DigiKey low-side hardware

- Release label: `HOLD_FOR_PHYSICAL_RELEASE_TEST_Anticipy_0.9.3_owner2_live_50mA.uf2`
- Size: 528,384 bytes
- SHA-256: `f246fc79ff9925fb427585e8babf4fe106ea1ad1c32a82b2c4351d3cc55ea5d6`
- Board target: `xiao_ble/nrf52840/sense`
- Application revision: `0.9.3-wed-live-bh-owner2`
- NCS: v2.7.0, commit `5cb85570ca43`
- Zephyr: commit `100befc70c74`
- Toolchain: Zephyr SDK 0.16.5, GCC 12.2.0
- GPIO polarity: active-high
- Required circuit: ordered Vybronics VCLP1020B002L with
  AO3400A/1N4148W-HF/100 ohm/100 kohm low-side driver

Clean build directories `candidate_live_owner_c` and
`candidate_live_owner_d` produced byte-identical UF2 files. Source host checks
for baseline invariants and owner-lock invariants pass.

## Separate local fallback — never mix with primary

> **The fallback UF2 is only for the Lee PID170433 NTR4101P P-channel
> high-side circuit. Flashing it on the primary AO3400A/NMOS circuit can leave
> the motor energized when software believes it is off.**

- Folder: `LOCAL_NTR4101P_FALLBACK_DO_NOT_MIX/`
- Release label:
  `HOLD_FOR_PHYSICAL_RELEASE_TEST_Anticipy_0.9.3_owner2_live_50mA_LOCAL_NTR4101P_ACTIVE_LOW.uf2`
- Size: 528,384 bytes
- SHA-256: `54b12eefb226d886ae374043ad2e5e409f5301956940de8bb13f76d084d14299`
- GPIO polarity: active-low
- Required circuit: NTR4101P source to 3V3, drain to motor+, motor- to GND,
  D0 to gate, 10 kohm gate-to-3V3 pull-up, BAS16 cathode to motor+

Clean builds `local_pfet_active_low_a` and `_b` produced byte-identical UF2
files. Both generated DTS files are byte-identical and show pin 2 flags 1. The
only source delta changes `GPIO_ACTIVE_HIGH` to `GPIO_ACTIVE_LOW`; its exact
patch and full evidence are packaged in the fallback folder.

## What static inspection proves

- One BLE connection and one stored bond.
- Zero-bond boots open a 120-second commissioning window.
- D7 owner-reset input and D0 haptic output are compiled in.
- Live Opus audio and nominal 50 mA application charge configuration.
- microSD/filesystem/SPI and offline audio-backlog application paths disabled.
- Audio, button, haptic, and application DFU-trigger paths check the stored
  owner connection.

## What static inspection does not prove

It does not prove iPhone compatibility, physical charge current, bootloader
behavior from USB insertion, motor-driver safety, closed-shell audio/RF,
system-off/wake, runtime, thermal behavior, or physical owner isolation.
Copying a UF2 alone also does not erase an old bond or external QSPI contents.

The commissioning link is encrypted after pairing but the 120-second window
does not authenticate the human. Bluetooth privacy, APPROTECT lock,
signed/verified boot, and bootloader authorization are not established. This
is why **both** binaries remain explicitly held until `QA_RELEASE.md` passes.
