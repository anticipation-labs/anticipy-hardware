# Firmware threat model and release gates

## Protected assets

- Ambient and bystander speech.
- The user's control of capture and expectation that the blue indicator matches
  microphone hardware state.
- Device ownership, bond recovery, and availability.
- Firmware authenticity, version, rollback policy, recovery path, and signing
  keys.
- Session boundaries: audio from an old connection must not enter a new one or
  be reconstructed as real speech after loss/reorder.

## Adversaries and failures

- A nearby central attempts to pair first, occupy the only connection, restore
  an old CCC, or keep the legitimate phone unavailable.
- A link disconnect, CCC revocation, codec/notify fault, or asynchronous PDM
  stop races capture state.
- Packets are lost, duplicated, reordered, truncated, or joined across
  reconnects.
- A malicious, stale, mismatched, or untraceable image is installed through the
  unknown bootloader/recovery path.
- ADC, board wiring, or an uncalibrated voltage curve produces a plausible but
  incorrect battery value.
- An operator mistakes a host test, source receipt, old local build, or
  quarantined UF2 for physical safety evidence.

## Controls in the locked source candidate

- The selected source is live-stream-only. Offline storage, removable
  filesystem, legacy application DFU, NFC, button, speaker, alternate-board,
  and unused application USB/serial paths are removed or excluded.
- Audio value reads and CCC access require BLE encryption. The configuration
  enables LE Secure Connections, settings-backed bonding, NVS, and one paired
  device.
- A restored bonded CCC is not recording consent. Capture requires a fresh CCC
  write bound to the exact current connection; the same identity,
  authorization, and subscription are checked immediately before PDM start, at
  active-state commit, and before every explicit notification retry.
- Disconnect/revocation clears active state. One control thread owns microphone
  start/stop, and PDM buffers are not scrubbed until asynchronous stop is
  confirmed. Failure to confirm stop keeps the recording indicator
  conservatively lit.
- PCM, encoded frames, fragment state, and Opus state use connection/audio
  epochs and are reset between sessions. Notification sequence/offset state
  advances only after success.
- Initial advertising and post-disconnect failures enter continuing recovery
  after bounded fast retry bursts; a transient controller/resource error does
  not cause permanent silent abandonment.
- Startup battery failure blocks advertising. Runtime battery failure
  disconnects rather than emitting `0%` or a normal-looking stale percentage.

These controls materially reduce the raw upstream attack surface. They are
source claims only until the exact pinned embedded build and physical tests
pass.

## Residual release blockers

| Finding | Current evidence | Consequence | Required gate |
|---|---|---|---|
| No authenticated owner enrollment | Secure Connections uses Just Works; there is no physical enrollment gesture, OOB/MITM proof, or owner allowlist | The first nearby central can become the sole stored bond; encryption is not ownership | Add a short physical enrollment window plus authenticated/OOB proof or an equivalent reviewed control |
| No physical bond erase/recovery | One persisted bond is configured but no user gesture erases it | Lost phone or hostile first bond can lock out the user | Add a deliberate hold gesture, visible acknowledgement, bond/secret erase, and tested recovery |
| Connectable advertising remains open | `BT_LE_ADV_CONN`, one connection, continuing recovery | Unknown centrals can consume availability even if protected GATT access later fails | Filter/allowlist outside enrollment and rate-limit churn |
| Settings storage is not build-proved | NVS/settings options are selected, but the final pinned Zephyr build has not run | Bond persistence or partition placement may fail at compile/runtime | Prove the exact partition and settings backend in the locked build and on a spare |
| Boot/update trust is unknown | Application DFU is removed, but the attached bootloader and immutable trust root have not been read or verified | Physical/UF2 access may install stale or malicious bytes | Provision signed, product/board-bound, rollback-protected boot/update and recovery |
| Legacy audio framing is ambiguous | Three-byte header has no frame length, end bit, session ID, timestamp, or application authentication tag | Loss at a frame tail is unknowable; stream boundaries depend on receiver policy | Keep fail-closed receiver now; introduce a versioned authenticated successor |
| Indicator and PDM quiescence are unproved on hardware | Source orders LED and microphone state conservatively | GPIO polarity, wiring, DMA, or driver behavior may differ on the pendant | Validate every capture/stop/fault path with instrumentation on a recoverable board |
| Battery percentage is uncalibrated | Divider math is corrected, but voltage points are generic | A plausible percentage can mislead the user | Measure board divider and discharge curve; define uncertainty/temperature policy |
| No final artifact provenance | Final source has no embedded build, replica match, release SBOM, or signature | Review cannot be tied to executable bytes | Reproduce with the pinned toolchain and complete frozen dependency manifest |
| Quarantined UF2 lacks provenance | Binary does not come from this pipeline | Its behavior and update authority are unknowable | Keep quarantined; never use it to skip the release gates |

## Minimum ownership design

1. A factory-new or explicitly erased pendant advertises enrollment only during
   a short window opened by a physical gesture with unmistakable feedback.
2. Bind the stored owner identity to authenticated/OOB pairing or another
   independently reviewed proof. Document any hardware-driven limit; do not
   call Just Works owner authentication.
3. Outside enrollment, allow only the owner identity. Do not identify an owner
   by the advertised name, service UUID, mutable address, or phone-provided
   string.
4. Provide a physical bond/secret erase gesture with a safe hold duration,
   visible acknowledgement, rate limiting, and tested lost-phone recovery.
5. Keep capture consent scoped to the current encrypted owner session. Drive
   the indicator from actual microphone lifecycle and retain the conservative
   fail-lit behavior whenever stop cannot be proved.
6. Store no raw audio in this MVP. Log only bounded diagnostic counters and
   truthful versions, never speech or secrets.

AccessorySetupKit may improve iOS discovery and authorization UX, but it cannot
replace BLE/device ownership, a physical enrollment action, or authenticated
firmware.

## Signed and versioned update requirements

- Use a reviewed secure bootloader with a release public key in the trust root;
  keep private signing keys outside Git and ordinary CI logs.
- Sign each image and bind product, exact board revision, semantic version,
  security counter, source commit, dependency lock, toolchain digest, image
  size, and SHA-256.
- Enforce product/board match, signature validation, monotonic security counter,
  and rollback rejection before boot.
- Make development and production roots visibly and cryptographically distinct.
- Test that recovery also authenticates images; a successful UF2 copy is not
  trust evidence.
- Archive source/build receipts, complete frozen manifest/SBOM, public keys,
  signatures, and post-flash readback/version evidence.

## Physical validation gates

Use a spare/recoverable board first. Record markings, bootloader identity,
current firmware evidence, power behavior, and hashes before any write. Then
test first-owner theft resistance, unknown-central connection churn, bond erase,
fresh-CCC consent, revocation during start and notify retry, indicator behavior,
PDM-stop timeout, 60-second capture, loss/reorder and sequence wrap,
disconnect/reconnect, phone lock/background relaunch, battery calibration,
rollback rejection, and recovery. The quarantined image cannot satisfy any of
these gates.
