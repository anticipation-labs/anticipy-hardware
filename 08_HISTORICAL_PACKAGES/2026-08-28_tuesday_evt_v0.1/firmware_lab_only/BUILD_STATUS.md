# Build and verification status

> **LAB ONLY — DO NOT CUSTOMER-SHIP:** microSD audio is plaintext. Use synthetic or explicitly non-sensitive test audio only.

Status date: 2026-08-28 UTC

## Bottom line

The nRF52840 founder-EVT firmware is **compile-successful and flashable**. It is **not hardware-validated and not customer-release-ready**.

| Requirement | Implemented in source | Compiles | Host-checked | Real hardware / iPhone tested |
|---|---:|---:|---:|---:|
| 16 kHz mono XIAO PDM capture | Yes | Yes | Static only | No |
| Opus, 10 ms, 16 kb/s target, CBR | Yes | Yes | Static only | No |
| Opus DTX / internal voice detection | Yes | Yes | Static only | No |
| Encrypted BLE live notifications | Yes | Yes | Static only | No |
| Offline microSD when live is unavailable | Yes | Yes | Packing tested | No |
| 20 h storage capacity + 15% margin | Yes | Yes | **182,160,000 B** worst-case model | No timed run |
| MTU-safe ordered backlog transfer | Yes | Yes | Five MTUs + interrupted resume | No iPhone run |
| Button notifications | Yes | Yes | Pins/static | No |
| Haptic GPIO command | Yes | Yes | Pins/static | No |
| Bond persistence | Yes | Yes | Config/static | No |
| 16 h from 250 mAh | Unknown | N/A | Requires <=13.28 mA | No |
| Circular rolling 20 h retention | **No** | N/A | N/A | No |
| SD encryption at rest | **No** | N/A | Explicit blocker | No |
| MITM-safe first pairing | **No** | N/A | Explicit blocker | No |
| Absolute time / file-generation identity | **No** | N/A | Explicit blocker | No |

Additional reliability truth:

- a BLE notification returning success means “queued by the Bluetooth stack,” not “received and saved by the iPhone”; live frame IDs expose gaps, but this EVT has no live retransmission protocol;
- a notification that cannot be queued after three retries is now saved to SD, and audio also continues into SD while backlog transfer is active if live audio is not subscribed;
- live streaming and backlog transfer use equal-priority threads. Their real coexistence and throughput must pass the locked-iPhone hardware test;
- SD capacity is now gated by current file size rather than download offset, but retention is still append-only rather than a rolling circular 20-hour policy.

## Reproducible build

Pinned inputs:

- Nordic nRF Connect SDK: `v2.7.0`, commit `5cb85570ca43bc344d3145c2338128eacf4b48ec`
- Zephyr: commit `100befc70c74f7ec83dd8ac3171ee18eeddb4dbd`
- `hal_nordic`: commit `ab5cb2e2faeb1edfad7a25286dcb513929ae55da`
- Zephyr SDK: `0.16.5`
- board: `xiao_ble/nrf52840/sense`
- application config: `prj_xiao_ble_sense_devkitv2-adafruit.conf`
- devicetree overlay: `overlay/xiao_ble_sense_devkitv2-adafruit.overlay`

Build command from an initialized NCS workspace:

```bash
west build --pristine always \
  -b xiao_ble/nrf52840/sense \
  /absolute/path/to/source_nrf52840 \
  -d build/anticipy \
  -- \
  -DNCS_TOOLCHAIN_VERSION=NONE \
  -DCONF_FILE=prj_xiao_ble_sense_devkitv2-adafruit.conf \
  -DDTC_OVERLAY_FILE=/absolute/path/to/source_nrf52840/overlay/xiao_ble_sense_devkitv2-adafruit.overlay
```

Final clean compile footprint:

- flash: 292,552 B / 788 KiB (36.26%)
- RAM: 168,924 B / 256 KiB (64.44%)
- UF2: 585,216 B

## What the host checks actually prove

`python3 host_checks.py` proves deterministic software properties only:

- 10,000 randomized length-prefixed frames survive pack/unpack;
- fixed-rate capacity needs 158,400,000 B for 20 h, or 182,160,000 B with 15% margin;
- notification pieces never exceed ATT MTU at MTUs 23, 185, 247, 296 or 498;
- interrupted transfers recover from the last complete 440-byte record;
- one-byte data pieces cannot be confused with one-byte control codes;
- the selected SD, button and haptic pins do not overlap;
- application characteristics require an encrypted BLE link and bonds are saved;
- battery-divider enable polarity matches Seeed's documented active-low design.

They do not prove microphone polarity, SD electrical integrity, RF range, iOS background behavior, battery life, heat, sealing or drop survival.

## Hardware acceptance gates

Do not seal a unit until all rows pass:

| Gate | Pass condition |
|---|---|
| Cold boot | 10/10 boots advertise and record |
| Missing SD | BLE live stream still starts |
| Audio | known speech produces decodable 16 kHz mono Opus |
| Live | 60 min, no unexplained gaps or resets |
| Offline | phone absent 20 h, entire timeline drains and decodes |
| Resume | cut BLE at 10 random points; no missing or reordered 440-byte records |
| Power loss | 20 random power cuts; file mounts; measure loss under speech and DTX silence. The fixed 20-byte active-packet estimate is ~3.2 s, but tiny DTX packets can make the same cache span roughly 35 s of quiet time |
| Runtime | 16 h speaking/streaming profile; average <=13.28 mA |
| Button | 100/100 intentional presses, no phantom events |
| Haptic | 1,000 pulses, no brownout, SD fault or reset |
| iPhone background | locked phone + app backgrounded for 2 h without silent disconnect |

## Client status

`ios_test_client/AnticipyBLEClient.swift` is a source-complete CoreBluetooth handoff for live frames, storage reassembly/resume, button and haptic. No Swift/Xcode toolchain or iPhone was available here, so it is source-reviewed and protocol-matched, **not compiled or run**.

The public Omi app (BasedHardware/omi commit `0303fd24579f8e3d0a3b1c3d9e5ad99adf87a4d2`) recognizes codec ID 20 and the live BLE UUIDs. Its legacy SD downloader accepts only a single 440-byte notification, so it is not sufficient for iPhone-MTU-safe backfill without reassembly; the supplied minimal client implements that missing layer.
