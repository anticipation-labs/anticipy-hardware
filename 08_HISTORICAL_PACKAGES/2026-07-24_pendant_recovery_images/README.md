# Anticipy pendant — two dual-hatch images, side by side

Built 2026-07-24. **Neither has been flashed. Nothing has been written to the
pendant.** Both are byte-identical in behaviour except for one thing: which
32.768 kHz low-frequency clock source the BLE stack is told to use.

Both images carry **both** software routes back into the Adafruit nRF52
bootloader, so neither one can lock the device out:

| hatch | trigger | GPREGRET magic |
|---|---|---|
| cable | USB CDC-ACM set to 1200 baud, then DTR deasserted | `0x4000051C <- 0x57` |
| wireless | write `0x06` to BLE char `00001531-1212-EFDE-1523-785FEABCD123` | `0x4000051C <- 0xA8` |

---

## Try **A** first

`A-TRY-FIRST-dual-hatch-rc-internal-RC.uf2`
`A-TRY-FIRST-dual-hatch-rc-nrf52-legacy-ota.zip`

**What it is:** the dual-hatch image with the low-frequency clock moved from the
external 32.768 kHz crystal (LFXO) to the on-die RC oscillator (LFRC).

**Why it goes first:** the pendant's symptom is that the BLE radio never comes
up while USB stays alive. That symptom points at `bt_enable()` failing, and the
most likely reason is upstream of it, inside MPSL:

- The parent image (`B`) never pinned a clock source, so Zephyr's Kconfig
  default applied — `CLOCK_CONTROL_NRF_K32SRC_XTAL`, the external crystal.
  The board files do not pin it either; this was a default, not a decision.
- `nrf/subsys/mpsl/init/mpsl_init.c` hands that straight to `mpsl_init()`, with
  `skip_wait_lfclk_started = false` (because `CONFIG_SYSTEM_CLOCK_NO_WAIT` is
  not set). **MPSL therefore waits for the crystal to report started.**
- A crystal that never starts is a hard stop right there — and Zephyr 3.4
  ignores a failed `mpsl_init` in its `SYS_INIT` slot, so it fails *silently*.
  That is exactly the "USB alive, radio dead" signature on the bench.

Image `A` removes the external crystal from the boot path entirely. The LFRC is
on-die and cannot fail to start. If the crystal is the fault, `A` is the image
that brings the radio back.

**Cost of A:** higher sleep current (the LFRC needs an HFXO-referenced
calibration every 4–8 s) and a wider connection receive window (500 ppm declared
vs 50 ppm). Battery life will be measurably worse. That is a fine trade for a
recovery image and a poor one for production.

---

## Keep **B** as the control

`B-dual-hatch-xtal-crystal.uf2`
`B-dual-hatch-xtal-nrf52-legacy-ota.zip`

**What it is:** the original verified dual-hatch image, crystal-based
(`CLOCK_CONTROL_NRF_K32SRC_XTAL`, 50 ppm).

**Why keep it:** it is the control arm. If the crystal turns out to be healthy,
`B` is the better long-term image — lower power, tighter timing. And if `A`
fails *in exactly the same way* as `B`, that is real information: the fault is
not the LFXO, and the search should move to the MPSL/SDC flash region, brown-out
behaviour, or the RF front end.

---

## Reading the outcome

| result | what it means |
|---|---|
| `A` advertises, `B` did not | LFXO is dead or not starting. Hypothesis confirmed. Stay on `A`, or fix the crystal and move back to `B`. |
| `A` also fails to advertise | The LFXO is **not** the fault. Do not keep iterating on clock config — go look at the MPSL/SDC region, power/brown-out, and the antenna path. |
| `A` advertises but drops connections | Look at the 500 ppm accuracy declaration and the calibration cadence first (see `RC_BUILD_RECEIPT.json` → `minimum_lf_clock_accuracy`). |

---

## What was actually verified about A

Everything below was checked against the **built binary**, not the source:

- Both hatch UUIDs `00001530` / `00001531` present — **raw little-endian
  128-bit byte scan** of the reassembled UF2 payload, 1 occurrence each.
  A `strings | grep` check on this image returns **zero** hits for `1530`.
  That is a false negative. Only the byte scan is trustworthy here.
- `CONFIG_UART_LINE_CTRL=1` in `autoconf.h` (the cable hatch depends on it).
- `0x57` write to `0x4000051C` in `recovery_poll` @ `0x3970e`, after
  `usb_dc_detach` and `watchdog_feed`.
- `0xA8` write to `0x4000051C` in `enter_ota_bootloader` @ `0x38bd4`, after
  `watchdog_feed`, followed by `dsb` and the `SCB->AIRCR` reset.
- UF2 family `0xADA52840`, range `0x00027000 .. 0x00065400`, contiguous,
  ending 551,936 bytes below the `0x000EC000` ceiling.
- Audio contract intact: `19B10000` / `19B10001` / `19B10002` each present once.
- `main()` still calls `recovery_usb_start` **first**, before `led_start`, so a
  failing LED cannot take the cable hatch down with it.
- The RC path is genuinely linked: `mpsl_calibration_work_handler` and
  `calibration_work` are in the symbol table, re-armed every 131,072 ticks
  (4000 ms).
- Machine code in `mpsl_lib_init_sys` @ `0x4cadc` builds the MPSL clock config
  as `source=0` (RC), `rc_ctiv=16`, `rc_temp_ctiv=2`, `accuracy_ppm=500` — the
  values MPSL documents as recommended, and exactly the sdc_init() accuracy
  limit.
- DFU package parsed by Nordic's own `IOS-DFU-Library` via the existing flasher
  with `--validate-only`. `--execute` was never passed and no Bluetooth
  operation was attempted.

Full detail: `../dual-hatch-rc-20260724/RC_BUILD_RECEIPT.json`

## What was NOT verified

**Neither image has been run on hardware.** The receipts prove what is *in* the
images. They prove nothing about what the device does when it boots one. The
LFXO diagnosis remains a hypothesis — a well-supported one, but a hypothesis.

---

## Provenance

| file | sha256 |
|---|---|
| `A-TRY-FIRST-dual-hatch-rc-internal-RC.uf2` | `b6395fab…973b41cc` |
| `A-TRY-FIRST-dual-hatch-rc-nrf52-legacy-ota.zip` | `77ee2d67…8ced4d91` |
| `B-dual-hatch-xtal-crystal.uf2` | `f1c9011a…b7369c6937` |
| `B-dual-hatch-xtal-nrf52-legacy-ota.zip` | `e861aa9c…200db7c9` |

Full values in `SHA256SUMS.txt`. Verify with `shasum -a 256 -c SHA256SUMS.txt`.

Source trees, build logs and receipts:

- A → `/Users/omarebrahim/anticipation-builds/dual-hatch-rc-20260724/`
- B → `/Users/omarebrahim/anticipation-builds/dual-hatch-20260724/`

Both were built in the digest-pinned Nordic container
`sha256:f50c51b711bbb3f502496c4b83e88dda778420fb83327d4791f9bc0e34916d01`
against the same pinned NCS workspace (zephyr `2e2523ef`, nrf `1fae141f`).
No image was pulled and no `docker prune` was run.
