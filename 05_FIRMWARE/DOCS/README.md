# Anticipy firmware evidence track

**Status: live-stream-only source candidate; not built and not flash-ready.**
Nothing in this directory authorizes a write to the attached pendant. The
authoritative Anticipy delta has source-level and host-test evidence only. It
still needs an exact pinned NCS build, independent review, physical calibration,
and spare-board validation.

This directory separates the evidence:

1. `upstream.lock.json` pins the official BasedHardware/Omi v2.0.1 source to an
   immutable commit and source-tree object.
2. `replacement/patches/0002-anticipy-source-safety.patch` is the one
   authoritative cumulative delta. The older `0001` patch is historical review
   evidence and is never chained into materialization.
3. `replacement/replacement.lock.json` binds the patch, complete post-patch
   content tree, critical files, and explicit behavior/non-claim contract.
4. `scripts/materialize_replacement.py` exports the locked upstream tree,
   applies only `0002`, verifies it, and emits a deterministic source receipt.
5. `quarantine/` holds an unrelated downloaded UF2 as forensic evidence only.
   It is not an output of this pipeline and must not be flashed.

## Candidate behavior

The selected devkit-v2 source is intentionally narrow:

- It exposes the existing live Opus audio service plus standard Battery and
  Device Information services. It does not compile the legacy offline-storage,
  NFC, speaker, button, alternate-board, application USB/serial, or application
  DFU surfaces.
- Audio and CCC access require an encrypted BLE link. LE Secure Connections,
  settings-backed bonding, and a single bond are configured. This is still
  **not owner authentication**: pairing is Just Works, there is no physical
  enrollment/erase gesture, no owner allowlist, and no MITM proof. A first
  nearby central can take the only bond/connection slot.
- Capture remains off until the current encrypted connection performs a fresh
  audio-CCC write. Restored CCC state from settings is not consent. The
  audio-control thread revalidates the same current connection, fresh
  authorization, and active subscription immediately before PDM start and
  again before committing the stream active.
- Unsubscribe, disconnect, codec failure, notification failure, or microphone
  fault clears active state and drives the serialized stop path. PDM buffers
  are scrubbed only after bounded asynchronous-stop confirmation. A stop that
  cannot be confirmed fails closed and keeps the blue recording indicator lit
  rather than claiming silence.
- Advertising readiness is published before the initial controller start. A
  failed initial start is reported to the caller but still enters recovery; a
  disconnect does the same. Bounded fast attempts are followed by continuing
  five-second retries, so a transient controller fault does not silently strand
  the device.
- The battery divider calculation preserves the full resistor ratio and the
  first successful percentage is published immediately, then smoothed every
  15 seconds per connection. The voltage curve is an uncalibrated development
  estimate. Startup measurement failure blocks advertising; a runtime
  measurement failure disconnects rather than publishing `0%` or a normal-
  looking stale value.
- Device Information advertises the model `Anticipy Pendant`, but firmware
  revision advertising is disabled because no truthful release version exists.

The audio UUIDs, codec ID 20, and legacy three-byte notification header remain
compatible. The sender derives payload capacity from the negotiated ATT MTU,
requires ATT MTU 100 or greater, caps a 320-byte Opus frame at four
notifications, and advances sequence/offset state only after successful notify.
See `PROTOCOL.md`.

## What has and has not been verified

Host tests compile and execute the pure battery smoother, divider math, and
fragment-state helpers with strict warnings and sanitizers when available.
They also verify exact patch scope, locked hashes, deletion of legacy surfaces,
and deterministic full-tree materialization. These tests are not an embedded
Zephyr build and prove nothing about radio, microphone, power, bootloader,
indicator visibility, iOS background behavior, or the attached hardware.

No embedded build of these final bytes was run in this lane. In particular, the
selected settings/NVS partition and the CELT-only link closure still require
proof from the exact pinned NCS/Zephyr toolchain. No artifact, release SBOM,
signature, flash, or hardware result exists.

The attached device was previously observed only as a Zephyr CDC application
device, not as a mounted UF2 bootloader. Its exact installed bytes, board
revision, bootloader, recovery policy, and microphone/battery wiring remain
unproved. The custom quarantined UF2 does not match the observed application USB
revision and has no matching source/build record.

## Safe local verification

Run from the repository root:

```bash
python3 -m unittest discover -s firmware/tests -p 'test_*.py'
python3 firmware/scripts/verify_quarantine.py
python3 firmware/scripts/fetch_upstream.py
python3 firmware/scripts/materialize_replacement.py \
  --destination firmware/.build/source/anticipy-v2.0.1
python3 firmware/scripts/build_candidate.py --probe
```

The probe is read-only. These commands do not grant permission to build against
an unreviewed dependency tree or to flash hardware.

## Release blockers

- Build the exact locked source with the pinned NCS/Zephyr/toolchain inputs and
  independently reproduce the artifact, receipt, and complete frozen-manifest
  SBOM.
- Confirm the settings partition, CELT-only link closure, board target, and
  warning-free compilation.
- Add a physical first-owner enrollment window, authenticated/OOB pairing or a
  documented equivalent, owner allowlisting, and a physical bond-erase/recovery
  gesture.
- Provision and prove signed, versioned, rollback-protected boot/update and
  recovery paths with keys outside source control.
- Calibrate the battery curve and validate divider/wiring on the physical board.
- Test first on a recoverable spare, then verify indicator/mute semantics,
  60-second capture, packet loss, sequence wrap, disconnect/reconnect,
  phone-lock/background behavior, thermal/power behavior, and recovery with a
  real iPhone.

`BUILD.md` defines the reproducibility boundary. `THREAT-MODEL.md` records why
encrypted bonding is useful but still insufficient for production ownership.
