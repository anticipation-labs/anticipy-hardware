# Security and privacy release gates

## What the EVT protects

- Every application GATT read, write and subscription requires link encryption.
- LE Secure Connections pairing is enabled.
- The phone bond is persisted in NVS across reboot.
- Only one paired device is configured.

## What it does not protect

### 1. The SD card is plaintext

`/audio/a01.txt` contains raw length-prefixed Opus records. Anyone who removes or reads the card gets the audio. BLE encryption does not protect a stolen SD card.

**Verdict: customer/founder audio release blocker.** Only synthetic or explicitly non-sensitive lab audio should be used with this build.

Production design:

- provision a unique random device key in protected internal flash;
- encrypt each independently recoverable storage chunk with AES-256-GCM or ChaCha20-Poly1305;
- use a never-repeated nonce built from a device/session ID plus monotonic chunk counter;
- authenticate sequence number, codec, timestamp and session ID as associated data;
- journal counters so a power cut cannot repeat a nonce;
- have the iPhone authenticate before decoding or acknowledging a chunk;
- test corruption, truncation, replay, reordered chunks, power loss and key-loss recovery.

Do not invent a key from a serial number, MAC address or fixed firmware secret.

### 2. First pairing is Just Works

The current no-screen/no-keyboard pendant establishes an encrypted LE Secure Connections bond, but the first pairing has no authenticated passkey or out-of-band identity. A nearby attacker during first pair could impersonate an endpoint.

**Verdict: prototype-only security.** Bonded reconnects are encrypted, but first-pair MITM resistance is not proven.

Production design:

- pairing is disabled by default;
- a long physical button hold opens a short pairing window;
- each unit ships with a unique QR/passkey or NFC out-of-band secret;
- the iPhone displays and verifies device identity;
- factory reset requires a deliberate physical sequence and erases bonds/keys;
- rate-limit failed attempts and log security state without logging audio.

### 3. No authenticated record identity

The append-only file has no session generation, timestamp, CRC or authentication tag. The iPhone can detect an impossible length inside a 440-byte block, but it cannot prove origin, freshness or completeness.

**Verdict: memory-integrity blocker.** Solve this with authenticated encrypted chunks and unique session metadata.

### 4. No rolling privacy limit

The EVT file keeps growing until explicitly deleted. It is not a 20-hour retention ring. A large card can retain far more history than the product promise.

**Verdict: retention-policy blocker.** Implement a tested segmented circular store that atomically deletes the oldest authenticated segment after the configured duration/space limit.

## Required security tests before customers

- pair while an active BLE attacker is present;
- verify pairing is impossible outside the physical window;
- remove the SD and confirm ciphertext reveals no audio or metadata beyond allowed fields;
- flip, delete, duplicate and reorder storage chunks; every manipulation must be rejected;
- power-cut during key/counter updates 1,000 times without nonce reuse;
- factory reset fully erases bond and device keys;
- lost-phone revocation and re-pairing work without exposing old audio;
- application background restoration never bypasses device identity checks.

## Reliability gate: live BLE has no delivery ACK

`bt_gatt_notify()` confirms that Zephyr accepted a notification for transmission; it does not prove that the iPhone saved the frame. Frame IDs let the client detect a gap, and immediate queue failures fall back to SD, but a packet lost after successful queueing is not retransmitted by this EVT.

**Verdict: customer-release reliability blocker.** Add an application-level sequence ACK/replay window or store a concurrent authenticated rolling copy, then prove live plus backfill on a locked iPhone under RF interference.
