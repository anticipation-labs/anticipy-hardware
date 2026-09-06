# Anticipy founder-EVT BLE / iPhone handoff

All Anticipy application characteristics require an encrypted BLE link. The current prototype uses LE Secure Connections Just Works bonding; see `SECURITY_RELEASE_GATES.md`.

## Live audio

| Item | Value |
|---|---|
| Service | `19B10000-E8F2-537E-4F6C-D104768A1214` |
| Audio data | `19B10001-E8F2-537E-4F6C-D104768A1214` (read + notify) |
| Codec | `19B10002-E8F2-537E-4F6C-D104768A1214` (read) |
| Codec ID | `20` = Opus, 16 kHz, mono |
| PCM per encoded frame | 160 samples = 10 ms |
| Target bitrate | fixed 16 kb/s; DTX enabled |

Each notification value is:

| Byte(s) | Meaning |
|---|---|
| 0–1 | frame ID, unsigned 16-bit little-endian, wraps |
| 2 | fragment index, starts at zero |
| 3… | raw Opus packet bytes |

The EVT waits until ATT MTU is at least 100. At the fixed 16 kb/s target, normal encoded packets are about 20 bytes and therefore fit in one notification with fragment index zero. The firmware uses the real `bt_gatt_get_mtu(conn) - 3` notification limit; it no longer mistakes Link Layer data length for ATT MTU.

Pass each Opus packet separately to Anticipy's upload path. For local libopus decoding: create a 16 kHz, one-channel decoder and call `opus_decode(..., frame_size=160, decode_fec=0)` once per packet.

## Offline storage and backfill

| Item | Value |
|---|---|
| Service | `30295780-4301-EABD-2904-2849ADFEAE43` |
| Command + data notification | `30295781-4301-EABD-2904-2849ADFEAE43` |
| Status read | `30295782-4301-EABD-2904-2849ADFEAE43` |

Status read is 8 bytes:

| Byte(s) | Meaning |
|---|---|
| 0–3 | current audio-file size, uint32 little-endian |
| 4–7 | firmware's last persisted transfer offset, uint32 little-endian |

The iPhone should trust its own durably committed offset, not byte 4–7. The firmware value is only periodically checkpointed.

Commands are written to the command characteristic:

| Command | Bytes |
|---|---|
| Read/resume file 1 | `[0, 1, offset_be_3, offset_be_2, offset_be_1, offset_be_0]` |
| Delete file 1 | `[1, 1]` (destructive; do not send until server upload is committed) |
| Clear directory | `[2, 1]` (destructive) |
| Stop transfer | `[3, 1]` or six-byte form |
| Heartbeat reset | `[50, 1]` |

One-byte notifications are control results:

| Value | Meaning |
|---:|---|
| 0 | command accepted |
| 3 | invalid file |
| 4 | empty file |
| 5 | offset beyond file |
| 6 | invalid command |
| 100 | transfer complete |
| 200 | logical file clear complete; not cryptographic/forensic erasure of plaintext flash sectors |

Any notification longer than one byte is raw file data. Concatenate data notifications in arrival order. Notifications may be 440 bytes on a large-MTU central or smaller on an iPhone; each is capped at ATT MTU minus three. The firmware avoids one-byte data fragments.

Split the concatenated stream into **exactly 440-byte records**. A record contains repeated:

```text
[opus_length_u8][raw_opus_packet...]
```

The first zero length ends the record; the rest is padding. Reject a record if a length crosses byte 440.

## Crash-safe resume rule

1. Subscribe to storage notifications.
2. Read status.
3. Open the local sink and truncate it down to a multiple of 440.
4. Send READ with that local byte count.
5. Reassemble notification pieces until a complete 440-byte record exists.
6. Write and fsync that whole record.
7. Only then advance the committed offset by 440.
8. If BLE drops, repeat from step 1 using the committed offset.

The firmware rounds every requested offset down to a 440-byte boundary. BLE notifications themselves are unacknowledged, so committing smaller pieces is unsafe; the full-record rule prevents holes after a disconnect.

## Ordering and time limitations

Records are returned in file order and frames are in capture order. The current EVT has no epoch timestamps, boot/session identifier or cryptographic record counter. The iPhone may estimate relative time as 10 ms per frame working backward from reconnect, but it cannot prove absolute time or distinguish an SD that was cleared and reused. Add time sync plus a unique file/session generation before a customer release.

## Button and haptic

| Job | Service | Characteristic | Data |
|---|---|---|---|
| Button | `23BA7924-0000-1000-7450-346EAC492E92` | `23BA7925-0000-1000-7450-346EAC492E92` notify/read | first byte: 1 single, 2 double, 3 long, 4 down, 5 up |
| Haptic | `CAB1AB95-2EA5-4F4D-BB56-874B72CFC984` | `CAB1AB96-2EA5-4F4D-BB56-874B72CFC984` write | 1=20 ms, 2=50 ms, 3=250 ms |

## Omi compatibility

The live UUIDs, three-byte live header and codec ID 20 match Omi's public client. Backfill is only wire-compatible when the client reassembles smaller notifications into 440-byte records. `ios_test_client/AnticipyBLEClient.swift` is the exact reference implementation for that step.
