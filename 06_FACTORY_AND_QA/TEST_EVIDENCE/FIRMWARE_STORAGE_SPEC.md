# Anticipy pendant v0.4 firmware and storage requirements

## Status and scope

This document is a requirements contract, not an implementation claim. The build pack does not yet contain production-ready Anticipy firmware or an iOS application.

It defines the behavior that must be implemented and verified for:

- the XIAO nRF52840 Sense founder pilot with Adafruit XTSD storage; and
- the later compact production board with raw SPI NAND plus Anticipy bad-block/ECC/storage management.

The product has two separate endurance requirements:

1. **Storage:** retain and recover at least 20 continuous hours while the phone is unavailable.
2. **Battery:** operate for at least 16 continuous hours in the sealed unit under the specified worst-case workload.

Passing storage-capacity arithmetic is not the same as passing either physical endurance test.

## Locked audio format

| Item | v0.4 requirement |
|---|---|
| capture | PDM microphone, 16,000 samples/s, mono |
| working samples | signed 16-bit PCM |
| Opus frame | 160 samples / 10 ms |
| codec | Opus, voice signal, restricted-low-delay application |
| bitrate | 32 kbit/s constrained VBR |
| DTX | off |
| FEC | off for V1 unless a measured BLE-loss test justifies it |
| segment duration | 60 seconds nominal; close early on private mode, orderly shutdown or fault |
| storage design rate | 5,000 bytes/s including frame and container overhead |
| capture policy | continuous; silence is retained |
| VAD | metadata only; it must not suppress, delete or time-compress V1 audio |

The encoded output must remain at or below the 5,000-byte/s design rate when averaged over the 20-hour worst-case storage test. Quiet audio, music, wind, overlapping speakers and continuous speech are all part of codec qualification.

Raw PCM is permitted only for bench bring-up. It is not the shipping format and must not be used to claim battery life or backlog-transfer performance.

## Storage capacity rule

At the locked design rate:

```text
5,000 bytes/s x 72,000 s x 1.15 = 414,000,000 bytes
```

The storage implementation must expose at least 414 MB of verified usable audio capacity after filesystem metadata, reserved recovery space, bad blocks, wear-management space and all other overhead.

- The 4 GB founder-pilot XTSD has sufficient nominal capacity, subject to the physical 20-hour test.
- The production design requires 512 MiB nominal raw SPI NAND and must prove at least 414 MB remains safely usable after its management/reserve. A 256 MB part does not meet this requirement.

## Anticipy recording container

Raw concatenated Opus packets are not a standard `.opus` file. Anticipy must use a versioned binary container with the extension `.antrec` unless a valid Ogg Opus implementation is deliberately selected later.

### Segment names and state

```text
/audio/<device_id>_<session_id>_<segment_sequence>.antrec
/state/index_a.bin
/state/index_b.bin
/state/device_state.bin
```

The persisted segment sequence is unsigned 64-bit and never resets during ordinary reboot. A random 128-bit session ID separates boot sessions. The two index copies each carry a generation number and CRC; recovery chooses the newest valid copy and reconciles it against the audio directory.

### Segment header fields

Every segment begins with these fields in an explicitly documented byte order:

| Field | Requirement |
|---|---|
| magic | four-byte `ANT1` |
| format version | integer; incompatible changes increment it |
| header length | total header bytes |
| device ID | stable pseudonymous device identifier |
| session ID | random 128-bit boot/session identifier |
| segment sequence | persisted unsigned 64-bit sequence |
| codec | Opus |
| sample rate / channels | 16,000 / 1 |
| frame samples | 160 |
| bitrate mode | 32 kbit/s constrained VBR, DTX off |
| start sample | unsigned 64-bit continuous sample counter |
| monotonic start | device monotonic microseconds |
| UTC mapping | optional phone-provided UTC anchor plus mapping generation |
| key ID and nonce prefix | required for encrypted customer builds |
| flags | private transition, recovery, clock mapping and fault flags |
| header CRC32 | corruption detection for the complete header |

### Audio-frame record fields

Each encoded frame is independently parseable and contains:

- record type and record length;
- unsigned 64-bit frame sequence;
- unsigned 64-bit start-sample counter;
- monotonic timestamp or an unambiguous derivation from the segment header;
- Opus payload length and payload;
- flags, including haptic-active and recovered-after-reset indicators; and
- record CRC32.

BLE fragmentation adds a segment sequence, frame sequence, fragment index and fragment count. A 16-bit transport counter alone is insufficient because it wraps during a normal working day.

### Event records

The same timeline supports CRC-protected event records for:

- bookmark;
- haptic start and stop;
- private-mode start and stop;
- phone UTC mapping change;
- low battery, storage fault and reboot reason;
- acknowledged range; and
- an explicit `OVERWRITTEN_RANGE` with first/last sample and sequence whenever retention policy discards audio older than the guaranteed window.

### Segment trailer

A cleanly closed segment ends with:

- valid frame count;
- final sample counter;
- aggregate payload CRC32;
- close reason; and
- trailer CRC32.

CRC detects accidental corruption; it is not a security mechanism. Customer builds additionally require authenticated encryption.

## Durable-local-first data path

The local recording is the source of truth. Successful live BLE transmission must never disable or replace the local copy.

```text
microphone -> Opus frame -> local writer/source of truth
                              |-> best-effort live BLE copy
                              `-> verified foreground backlog transfer
```

Every encoded frame must enter the storage-owned write queue before it is eligible for the live BLE queue. The queues are independent: storage backpressure may reduce or pause live delivery, but BLE backpressure must never suppress local recording.

The implementation must bound and document the maximum unflushed audio window. It must sync often enough that an abrupt power loss loses no more than one second of new audio, never damages an older committed segment, and produces an explicit recovery/gap record when any tail cannot be salvaged.

Local recording continues when:

- no phone is connected;
- BLE is connected but the audio characteristic is not subscribed;
- a BLE notification cannot be queued or confirmed;
- the iOS app is backgrounded, suspended, force-quit or rebooting;
- the phone has no internet/server connection; or
- backlog transfer is paused.

When BLE remains available but the server is unavailable, the iPhone must also write a durable local write-ahead log. Device acknowledgement and cloud acknowledgement are separate states.

## Required operating states

| State | Required behavior |
|---|---|
| BOOT | start BLE independently, mount storage, recover state, report any storage fault and open a segment when safe |
| LIVE_AND_LOCAL | record locally and send a best-effort live copy |
| LOCAL_ONLY | continue local recording when live delivery is unavailable |
| BACKFILL | preserve live/local capture while sending the oldest closed unacknowledged segment |
| PRIVATE | stop microphone capture, close the current segment and persist a private-state event |
| STORAGE_NEAR_FULL | reclaim acknowledged segments oldest-first while preserving the recovery reserve |
| STORAGE_ROLLING | apply the explicit 20-hour retention rule below and persist any overwritten range |
| STORAGE_FAULT | keep BLE alive, report the fault and use live-only mode only when doing so is safe and truthful |
| LOW_BATTERY | close/sync the segment, persist state and enter controlled sleep before brown-out |

Storage mount or recovery failure must not prevent BLE from advertising. Corrupt media must never be silently reformatted.

## Atomic local write requirements

The implementation may choose FAT for XTSD and a different managed-NAND backend for production, but both backends must provide equivalent behavior:

1. Create a temporary segment with a unique device/session/sequence identity.
2. Write and validate the header.
3. Append complete frame/event records while checking every open, write and sync result.
4. Bound the unflushed window to one second or less.
5. Write and sync the trailer when the segment closes.
6. Atomically expose the segment as committed.
7. Update the older index copy, sync it, then advance its generation.

On reboot, the device must retain every older committed segment, salvage only a structurally valid prefix of the newest temporary segment, record any missing range and avoid filename or sequence reuse.

## Foreground backlog protocol

Large backlog transfer is a foreground iOS operation. Background live BLE remains best effort; the product must not promise invisible background draining.

1. The foreground app requests the oldest unacknowledged segment and its manifest.
2. The pendant sends resumable chunks containing offset, length and chunk CRC.
3. Live/local capture retains priority over backfill.
4. The phone writes to a temporary file in durable application storage.
5. The phone flushes the file, verifies header/trailer, complete-file CRC, frame count and sample range, then atomically registers the segment.
6. Only then does the phone return an acknowledgement containing device ID, session ID, segment sequence and complete-file CRC.
7. The pendant persists the acknowledgement. It may reclaim that segment only when space is needed.

An interruption resumes from a verified offset or restarts the same segment. Duplicate chunks and acknowledgements are idempotent. The device never deletes audio merely because BLE reported that a packet was sent.

## Full-storage retention policy

The guaranteed retention window is the newest 20 continuous hours.

1. Reclaim acknowledged segments first.
2. Never overwrite unacknowledged audio younger than 20 hours.
3. Once the oldest unacknowledged audio is older than 20 hours, the device may reclaim it only after durably recording an `OVERWRITTEN_RANGE` event and setting a persistent data-loss/fault flag.
4. If capacity or corruption reaches the emergency reserve before any segment is eligible under rule 3, close the current segment, signal the fault and stop local capture. Do not silently overwrite protected audio or claim recording continues.
5. Clear the persistent fault only after the phone has received the gap record and the user-visible software has acknowledged the condition.

Low/high watermarks and the protected metadata/recovery reserve must be fixed in the implementation and exercised by fault-injection tests.

## Button and haptic requirements

| Input or event | Required response |
|---|---|
| short press | bookmark current sample/segment and give one short buzz |
| release after at least 3 seconds but before 12 seconds | toggle PRIVATE and give two short buzzes |
| hold for at least 12 seconds | close/sync the segment, persist the reboot reason, perform an orderly system reboot and give three short buzzes |
| phone reconnect | one soft buzz only when enabled in user settings |
| storage or low-battery fault | one long warning buzz when power permits, then preserve state |

A 12-second hold must not also execute the 3-second action. Button debounce and all thresholds are firmware requirements, not inherited Omi behavior.

Every haptic interval must generate sample-aligned start/stop events so later processing can identify motor contamination. The motor must use a validated external driver and remain off during boot/reset; it must never be powered directly by an MCU GPIO.

## Power and health supervision

- The measured low-battery threshold must allow the active segment and state indexes to close before any MCU or storage brown-out.
- Backfill must not begin below the configured battery threshold; prefer a full 20-hour drain while charging.
- Log boot reason, reset count, battery voltage, storage errors, queue overruns and worker-health failures.
- Microphone, codec, storage writer and active transport each publish a progress counter.
- A software supervisor feeds the hardware watchdog only when every worker required by the current state is advancing.
- The hardware watchdog is the final backstop, not the normal 12-second-button reboot mechanism.

## Security and privacy requirements

CRC alone is insufficient for an ambient recorder.

Customer builds require:

- Bluetooth LE Secure Connections bonding and encrypted/authenticated GATT access;
- per-device authorization for audio read, acknowledgement, delete, private and reboot commands;
- authenticated encryption at rest for audio and sensitive state, with unique nonces and protected per-device keys;
- signed firmware/DFU images, anti-rollback and a recoverable update path;
- a deliberate, authenticated factory-reset/key-erasure flow;
- no unauthenticated command that can delete recordings or change privacy state; and
- no audio files in an iOS cache location that the operating system may evict.

An unencrypted/unbonded founder pilot may be used only as a controlled engineering unit and must not be represented as customer-ready.

## Acceptance tests

### Twenty-hour storage and recovery

This test may use controlled external power so it measures storage independently of battery capacity.

1. Record 20 continuous hours with the phone absent using worst-case speech/noise content.
2. Verify every segment, frame sequence and sample counter; total decoded duration must match the reference recorder within one frame.
3. Verify the total stored rate, including metadata, remains within the 5,000-byte/s design budget.
4. Foreground the iOS app and drain the complete backlog while new live/local recording continues.
5. Verify no gap, duplicate, early deletion or time compression and record drain duration, phone temperature and pendant energy cost.

### Sixteen-hour battery endurance

Run the final sealed unit on battery only for 16 continuous hours with:

- continuous worst-case audio encoding;
- local safety recording enabled;
- live BLE connected and subscribed;
- representative iPhone reconnects and server outages; and
- representative button/haptic use.

The unit passes only if it remains functional, preserves all audio, completes orderly low-battery handling and stays within the design's 15% usable-capacity reserve and thermal limits.

### Fault, recovery and protocol tests

1. Remove or corrupt storage: BLE still boots/streams, reports a storage fault and never autoformats.
2. Inject failures into open, write, sync, close, commit, index and acknowledgement steps; older committed segments always survive.
3. Cut power at every transaction stage and repeat random cuts for at least 100 boots.
4. Stall storage and BLE independently for 500 ms and five seconds; no loss is silent and every gap is explicit.
5. Connect BLE without subscribing to audio; local recording continues.
6. Lock the iPhone for at least two hours and force BLE interruptions; local fallback covers every permanent live gap.
7. Disable internet for at least two hours while BLE remains connected; the iPhone WAL retains every frame and later uploads it.
8. Kill, background and reboot the app at every backlog stage; foreground recovery resumes idempotently.
9. Fill storage beyond 20 hours; the exact rolling/full policy executes and every overwritten range is reported.
10. Force counters near wrap and reboot repeatedly; no device/session/segment/frame identity collides.
11. Exercise at least 1,000 noisy/bouncing button actions; bookmarks are singular and 3-/12-second actions never overlap.
12. Exercise at least 1,000 haptic patterns during audio, storage and BLE activity; no reset, corruption or unsafe rail droop occurs and every interval is timestamped.
13. Freeze microphone, codec, writer and transport workers independently; supervision detects each within its documented bound.
14. Verify an unpaired client cannot read audio or issue acknowledgement, delete, private or reboot commands.

No runtime, backlog, lossless-recovery, background-streaming or security claim may be made until its corresponding test has a retained log and passing artifact for the exact hardware and firmware hash.

## Pinned Omi reference and reuse boundary

Pin the upstream reference to [Omi DevKit2 release `Omi_DK2_v2.0.10`](https://github.com/BasedHardware/omi/releases/tag/Omi_DK2_v2.0.10). Record the resolved upstream commit and preserve the MIT license notice in the Anticipy source tree; never build production artifacts from a floating upstream branch.

Reuse or adapt these Omi areas:

- `omi/firmware/devkit`: nRF52840/Zephyr build structure, PDM microphone patterns and Opus integration;
- the live Omi BLE audio service/codec-discovery protocol where compatible;
- `app/ios/Runner/Ble/OmiBleManager.swift`: CoreBluetooth restoration and reconnection patterns;
- Omi's phone-local write-ahead-log architecture; and
- the Flutter device-connector structure.

Do not reuse unchanged:

- the DevKit2 board overlay or pin assignment;
- `omi/firmware/devkit/src/sdcard.c`;
- `omi/firmware/devkit/src/storage.c`;
- the legacy storage-sync parser, acknowledgement or clear/delete path;
- the stock button state machine;
- the stock haptic/speaker coupling or direct-GPIO assumption;
- the stock watchdog-feed strategy; or
- any claim that iOS provides uninterrupted background BLE or background backlog draining.

The founder-pilot firmware requires a new Anticipy devicetree overlay/config for its documented D1/D2/D3/D8/D9/D10 wiring and must disable the unused Omi speaker/I2S functions. The compact BL54L15µ production board is a separate port with a new board definition, power configuration and managed-NAND backend; Omi DevKit2 firmware will not run on it unchanged.
