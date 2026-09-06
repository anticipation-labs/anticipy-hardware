# 05 — Firmware

**Lab only. Nothing here is production firmware.**

This was the single largest gap in the original hardware packages: they shipped firmware
*binaries* and prose about them, but zero source, zero protocol specification, zero threat model,
zero build procedure and zero upstream pinning. All of that lives here now.

## Layout

| Folder | Contents |
|---|---|
| `DOCS/` | `PROTOCOL.md`, `THREAT-MODEL.md`, `BUILD.md`, `README.md`, `upstream.lock.json`, `protocol/` (executable frame protocol + fixtures), `development-receipts/` |
| `SOURCE/` | nRF52840 firmware source, debug tooling and an iOS test client (from Execution v1.0) |
| `IMAGES/` | One copy of each **distinct** firmware binary, renamed by date and status |
| `DEVICE_RECOVERY/` | The restore kit, including an image read back off a physical device, and the A/B recovery pair |

## Lineage — record this somewhere permanent

Anticipy firmware is a **fork of [BasedHardware/omi](https://github.com/BasedHardware/omi)**:

- Upstream: `v2.0.1-Omi`, commit `ee9892562648f074e3c6b59d508127d81fa21010`
- Path: `Friend/firmware/firmware_v1.0`
- Toolchain: NCS v2.5.0
- Applied as two named patches in `DOCS/../replacement/patches/`

**No hardware package records this.** It carries attribution and licensing obligations, and it
also vendors Opus 1.2.1. This should be stated explicitly wherever the firmware ships.

## The images

| File | Notes |
|---|---|
| `2026-09-04_anticipy_0.9.3_owner2_live_50mA_HOLD.uf2` | Newest. Name says it: held for physical release test. |
| `2026-08-28_anticipy_founder_evt_v0.9.0_LAB_ONLY.uf2` | Founder EVT lab image |
| `2026-07-24_dual-hatch-{base,rc,debug,secure}.uf2` | The dual-hatch recovery line. `secure` is the most production-appropriate (encrypted, bonded DFU control point) but has **no build receipt and no OTA package**, unlike base and RC. |
| `2026-07-23_zephyr_dev_NOT_FOR_FLASH.{uf2,hex}` | Development artifacts, explicitly not for flashing |
| `2026-07-20_anticipy.uf2`, `2026-07-21_anticipy.hex` | Earliest images. The `.uf2` reports version **1.0.5**. |

### Version numbering is incoherent

`1.0.5` (July) → `2.0.1` (July, candidate build) → `0.9.0` (August) → `0.9.3` (September).
The `2.0.x` numbers are inherited from upstream Omi; `0.9.x` is Anticipy's own scheme; `1.0.5` is
unexplained. **Sorting these by version number gives the wrong answer.** Sort by date.

## Two things that block shipping

1. **No haptic support exists in any firmware source tree.** A grep across all five source trees
   returns nothing, and every build receipt records `haptic_support_added: false`. Haptics are a
   core product requirement and a specified BOM line (DRV2605L + VC0720B015F). The firmware does
   not drive them.
2. **USB VID/PID are still Zephyr test defaults** (`0x2FE3` / `0x100`). Real identifiers are
   required before anything shippable.

## What actually ran on hardware

`DEVICE_RECOVERY/CURRENT-from-device-20260724.uf2` was read back off a physical pendant. It is the
only artifact in this repository that is evidence of what really executed on a device — everything
else is a build output that was never flashed. Every build receipt in the dual-hatch line records
`flash_performed: false`.

The restore kit also carries the fully-resolved Zephyr devicetree — the only as-built peripheral
and flash-partition map for the proof unit anywhere — plus five raw on-air BLE logs captured from
the physical pendant.

## Open, unresolved

- The A/B recovery pair exists to test one hypothesis: is the 32.768 kHz crystal dead?
  **No result was ever recorded.** No log, no follow-up build.
- The master package's `0.9.3` image (sha `f246fc79…`, NCS v2.7.0) has **no source tree anywhere**
  on the machine. The source for the newest firmware is missing.
