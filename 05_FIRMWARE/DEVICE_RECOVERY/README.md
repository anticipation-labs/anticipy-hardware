# Anticipy pendant — restore kit

**Purpose:** put the pendant back to a known-good, *recoverable* state if a firmware change goes wrong.

Built 2026-07-24. Verify the folder with:

```bash
cd ~/anticipy-pendant-restore && shasum -a 256 -c MANIFEST.sha256
```

---

## What this restores to

`image/zephyr.uf2` — 549,376 B, sha256 `437dc9e3…` — the 0001-lineage development build.

**Why this image and not a "better" one:** it is the only image we hold that provably contains the
**Nordic Legacy DFU service** (`00001530-1212-EFDE-1523-785FEABCD123` / control point `…1531`).
That was confirmed by disassembling `dfu_control_point_write_handler` at `0x566ea` in
`image/zephyr.elf`:

```
cmp r3,#0x1 / ldrb r3,[r2] / cmp r3,#0x6 / mov.w r3,#0x40000000 / movs r2,#0xa8 / str.w r2,[r3,#0x51c] / bl __NVIC_SystemReset
```

`0x4000051C` is `NRF_POWER->GPREGRET`. Writing the single byte `0x06` to `…1531` sets the magic and
reboots. The characteristic is `BT_GATT_PERM_WRITE` (no encryption) and the build has
`# CONFIG_BT_SMP is not set`, so it cannot be crypto-gated.

**That door is the whole reason this is the restore target.** A "safer" image without it would be
unrestorable on a board whose RESET button we will not press.

Known defects in this image, accepted deliberately for a restore target: memory-safety issues in the
SD/storage path, no link encryption, and that same DFU control point is an unauthenticated remote
reset for anyone in radio range. It is a *rescue* image, not a product image.

---

## What is NOT in this kit, and why

`dfu-package/` is **empty except a placeholder**. A Legacy-DFU package built from *this* image does
not exist yet. Do **not** substitute one from `anticipation-builds/` — all three images on this
machine differ:

| image | `zephyr.bin` | sha256 (first 8) | hatches |
|---|---|---|---|
| **this kit** (0001-lineage) | 274,468 B | `b7cddedb` | BLE DFU only |
| `ota-prepared` (0002) | 238,404 B | `6b6785df` | **none** — quarantined |
| `ota-recoverable` | 253,456 B | `fe4bc7d7` | 1200-baud USB only — quarantined |

Both of the latter are in
`~/anticipation-builds/firmware-authorized-flash-20260723-07/DO-NOT-SEND/` with a `WHY.txt`.

**To build the missing package**, use `adafruit-nrfutil` against `image/zephyr.hex`, and loosen the
init packet to `device_revision 0xFFFF` / `softdevice_req 0xFFFE`. Both existing zips pin
`device_revision 52840` / `softdevice_req 291` (`0x123`), which the bootloader may reject outright.

---

## How to restore

1. **Get into the bootloader.** Write one byte `0x06` to `…1531` over BLE. The device reboots with
   `GPREGRET = 0xA8`.
   **Know this first:** `0xA8` is **BLE-OTA-only with no timeout**. It does *not* enumerate USB, and
   it never returns to the application on its own. With the LiPo soldered on there is no
   power-cycle escape. Only knock on this door holding a validated package.
2. **Confirm you landed.** In bootloader mode the device advertises as `AdaDFU`. (If a UF2 volume
   appears instead — `XIAO-SENSE`, VID `0x2886` / PID `0x0045` — you are in the friendlier `0x57`
   mode and can simply drag `image/zephyr.uf2` onto it.)
3. **Push the package** with the already-built, already-verified flasher:

```bash
~/anticipation-builds/firmware-authorized-flash-20260723-07/macos-nordic-dfu-flasher/dist/Anticipy\ DFU\ Flasher.app/Contents/MacOS/anticipy-dfu --zip PACKAGE.zip --expect-sha256 SHA --validate-only
```

Drop `--validate-only` and add `--target-id <uuid> --execute` to actually flash.
`--validate-only` never initializes CoreBluetooth.

---

## The floor under everything

If no software route works, the pendant is still **not** dead. The Adafruit bootloader lives outside
every UF2 write boundary, an invalid application self-mounts as a UF2 drive with no timeout, and the
XIAO exposes **SWD / RST / GND on bottom-side 2.54 mm pads**. A ~$4 Raspberry Pi Pico running
`picoprobe`, or any CMSIS-DAP probe, can reflash from bare metal via `pyocd` / `openocd`.

That path needs no soldering to the board itself — only contact with the pads.

---

## Read-only recon tool

`tools/recon/Anticipy Pendant Recon.app` — connects, discovers **all** GATT services, reads only the
codec and battery characteristics, and prints a JSON `RESULT` line with the full service map. It
contains no `writeValue` call anywhere.

```bash
"~/anticipy-pendant-restore/tools/recon/Anticipy Pendant Recon.app/Contents/MacOS/omi-probe" 30
```

macOS requires a signed bundle with `NSBluetoothAlwaysUsageDescription` for CoreBluetooth access — a
bare CLI binary is denied silently, which is why this is wrapped as an app.
