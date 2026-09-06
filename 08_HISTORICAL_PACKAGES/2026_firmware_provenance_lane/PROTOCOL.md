# Pendant live-audio wire contract

This document describes the authoritative locked Anticipy source candidate, not
the quarantined UF2 and not the broader raw Omi firmware. The cumulative `0002`
patch preserves the three Omi audio UUIDs, codec ID 20, and three-byte
notification header while removing legacy application services and hardening
session/fragment handling. The historical `0001` patch is never chained into
materialization.

## Advertised and GATT surface

The complete advertised name is `Anticipy`. The primary advertisement contains
the live-audio service UUID; the scan response lists standard Battery and Device
Information services.

| Purpose | UUID | Candidate contract |
|---|---|---|
| Audio service | `19B10000-E8F2-537E-4F6C-D104768A1214` | primary service |
| Audio data | `19B10001-E8F2-537E-4F6C-D104768A1214` | encrypted read + notify |
| Audio CCC | standard descriptor | encrypted read/write; fresh write required for each connection |
| Codec identifier | `19B10002-E8F2-537E-4F6C-D104768A1214` | encrypted read; value `20` means Opus |
| Battery service/level | `180F` / `2A19` | standard percentage read/notify |
| Device Information | `180A` | model/manufacturer/hardware revision; firmware revision disabled |

There is no application DFU, offline-storage, accelerometer, speaker, NFC, or
haptic GATT service in the selected source.

Encrypted access and a persisted single bond are configured, but this is not
owner authentication. Pairing is Secure Connections Just Works: no physical
enrollment window, MITM/OOB proof, owner allowlist, or bond-erase gesture exists.
The advertised name, UUID, and BLE address must never be treated as owner
identity.

Capture requires an actual CCC write from the exact current encrypted
connection. A CCC restored from settings does not start capture. Current
identity, fresh authorization, and subscription are rechecked immediately
before microphone start, at stream-state commit, and before each explicit
notification retry.

## Audio before BLE fragmentation

- PDM samples are signed 16-bit mono PCM at 16,000 Hz.
- The codec consumes 160 samples per Opus packet, representing 10 ms.
- Opus uses restricted-low-delay, CELT-only mode, 32 kbit/s target, VBR on,
  complexity 3, no DTX, no in-band FEC, and no packet-loss compensation.
- An encoded frame is capped at 320 bytes.
- Encoder state and queued PCM/frames are reset at each audio epoch so one
  connection cannot contribute predictor or payload state to the next.

## Notification bytes and MTU

Every notification contains a three-byte application header followed by one or
more Opus bytes:

```text
byte 0      notification sequence, low byte
byte 1      notification sequence, high byte
byte 2      zero-based fragment index within the current Opus frame
byte 3..N   Opus bytes
```

The sequence is an unsigned little-endian 16-bit counter. It advances once per
successful BLE notification and wraps from `65535` to `0`. The fragment index
starts at zero for each Opus frame.

The sender uses the negotiated ATT MTU:

```text
notification value capacity = ATT MTU - 3
Opus payload capacity        = ATT MTU - 3 - 3
```

The first subtraction is ATT notification overhead; the second is this
protocol's header. ATT MTU below 100 is rejected. At MTU 100, a 320-byte Opus
frame is `94 + 94 + 94 + 38` bytes, so the source caps the maximum frame at four
notifications. Each notification has at most eight bounded attempts for
transient `EAGAIN`/`ENOMEM`; authorization is rechecked on every attempt, and
offset/sequence/fragment state advances only after success.

The format still has no frame length, end bit, timestamp, session identifier,
or application authentication tag. BLE link encryption/integrity protects the
active link, but it does not remove the framing ambiguity or prove owner
enrollment.

## Fail-closed receiver behavior

`protocol/frame_protocol.py` is the host reference:

1. Reject notifications shorter than four bytes, impossible fragment indices,
   and assembled frames over 320 bytes.
2. Ignore only an exact duplicate of the immediately preceding packet.
3. Require sequence continuity modulo 65,536 and fragment indices `0,1,2,...`.
4. On a gap, conflict, or out-of-order fragment, discard the pending frame and
   wait for a new fragment zero. Never concatenate across the error.
5. A valid new fragment zero ends the previous pending frame and starts the
   next.
6. On intentional stop/disconnect, flush only a valid pending frame and validate
   the Opus packet before forwarding; a lost trailing fragment is otherwise
   unknowable.
7. Reset all reassembly state between peripheral connections.

The fixtures cover normal framing, gaps, exact/conflicting duplicates,
out-of-order input, 16-bit wrap, malformed/oversize input, and final flush. They
are compatibility tests, not physical packet-delivery evidence.

## Required successor

A production successor should add a versioned session header, per-frame
sequence, total length or final-fragment marker, codec/sample metadata,
monotonic timestamp, and application integrity/authentication bound to the
authenticated owner session. Introduce it as a new characteristic or negotiated
version; never silently reinterpret these legacy bytes.
