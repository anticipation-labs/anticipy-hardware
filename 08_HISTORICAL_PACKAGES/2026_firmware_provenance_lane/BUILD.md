# Reproducible source and candidate-build receipts

## Current result

The Anticipy firmware customization and reviewed source-safety repairs are now
one cumulative source delta, not an unexplained binary.
`replacement/patches/0002-anticipy-source-safety.patch` applies by itself to
the exact BasedHardware/Omi commit and tree in `upstream.lock.json`.
`replacement/patches/0001-anticipy-name-and-battery.patch` is retained only as
historical review evidence; it is not authoritative and must not be applied
before or after `0002`. The materializer checks the upstream Git objects, the
single authoritative patch hash, every critical post-patch file, and the
complete materialized content tree before writing a deterministic source
receipt.

This is still a **source candidate**, not a flash-approved firmware image. The
final cumulative bytes have not been built as embedded firmware. A separate
one-machine offline development build of an earlier source state is recorded in
`development-receipts/2026-07-23-single-local-not-for-flash.md`; its warnings
and missing replica/SBOM/signature/hardware evidence mean it cannot validate
this repaired source. No UF2 was written to hardware. The quarantined custom
UF2 is not an output of this pipeline.

## Exact source delta

The cumulative patch preserves these compatibility behaviors:

- Advertises the complete BLE name `Anticipy` and reports the Device
  Information model `Anticipy Pendant`.
- Keeps the Omi audio service/data/codec UUIDs and codec ID 20 unchanged.
- Keeps the existing three-byte audio notification header, derives fragment
  capacity from the ATT MTU, rejects ATT MTU below 100, and limits a maximum
  320-byte Opus frame to four notifications.
- Publishes one successful standard Battery Service measurement before
  advertising and refreshes it immediately per connection, then every 15
  seconds while connected.
- Filters successful measured percentages with a fixed-point 3:1 exponential
  moving average. The first measurement is published unchanged, the filter is
  reset for each connection, and values are clamped to 0–100.

The selected image is now live-stream-only:

- Offline storage, FAT/disk, I2C sensor, I2S, SPI, NFC, speaker, button, legacy
  board configurations, application USB/serial, and application DFU code are
  disabled or removed from the authoritative source.
- Only the selected devkit-v2 configuration and overlay remain. Firmware
  revision advertising is disabled because no truthful release version exists.
- Audio and CCC access require encryption. LE Secure Connections, a single
  settings-backed bond, and NVS settings are configured, but Just Works pairing
  without physical enrollment, MITM proof, erase gesture, or owner allowlisting
  is explicitly **not** owner authentication.
- Capture requires a fresh CCC write from the exact current encrypted
  connection. Persisted CCC restoration cannot start PDM. A dedicated control
  thread revalidates connection identity, fresh authorization, and subscription
  before microphone start and before committing active state.
- Unsubscribe, disconnect, codec/notify failure, or PDM fault clears active
  state and enters one serialized stop path. DMA buffers are scrubbed only
  after bounded confirmation that asynchronous PDM stop completed.
- Advertising readiness is published before initial controller start.
  Initial-start failure is reported but enters the same recovery as a
  disconnect: a bounded fast retry burst followed by continuing delayed
  attempts instead of permanent abandonment.
- Battery divider arithmetic preserves the full ratio. Startup measurement
  failure blocks advertising; runtime measurement failure disconnects rather
  than publishing `0%` or a plausible stale percentage. The voltage-to-percent
  curve remains an uncalibrated development estimate.
- Shared connection state uses referenced handles. Queue and codec epochs keep
  prior-session PCM, encoded frames, and Opus predictor state out of a new
  connection.
- ATT fragmentation advances offset, sequence, and fragment index only after a
  successful notification and bounds retry work.
- Restricts the Opus build to the encoder/CELT surface required by the product,
  restores required fixed-point helpers, uses single-evaluation assertions,
  checks the fixed encoder allocation, and resets encoder state at each audio
  epoch.
- Promotes selected memory-safety diagnostics to compile errors.

Pure battery smoothing, divider arithmetic, and transport-fragment helpers are
compiled and run on the host with strict warnings and, when supported,
AddressSanitizer/UndefinedBehaviorSanitizer. The test suite also proves that
`0002` alone materializes the locked final source tree. This is source-level
evidence, not an NCS/Zephyr build or hardware validation.

The patch does not add haptic hardware support, secure first-owner enrollment,
authenticated/OOB pairing, a bond-erase gesture, a signed boot/update chain,
battery calibration, or any physical-hardware proof.

Materialize and verify it without compiling:

```bash
python3 firmware/scripts/fetch_upstream.py
python3 firmware/scripts/materialize_replacement.py \
  --destination firmware/.build/source/anticipy-v2.0.1
```

The output includes `ANTICIPY_SOURCE_RECEIPT.json`. The receipt has no machine
path or timestamp, so the same locked inputs produce the same receipt bytes.
`replacement/replacement.lock.json` is the review boundary for the patch and
post-patch tree.

## Explicit SDK and toolchain inputs

`replacement/toolchain.lock.json` pins:

- [nRF Connect SDK v2.5.0](https://github.com/nrfconnect/sdk-nrf/tree/1fae141fc6713dd331b797fc96c90dc84552242d)
  at commit `1fae141fc6713dd331b797fc96c90dc84552242d`, including the
  Git blob and SHA-256 of its `west.yml`.
- [Nordic's Zephyr fork](https://github.com/nrfconnect/sdk-zephyr/tree/2e2523efe52a7ac89f0567b8798fd857b1e71ae3)
  at commit `2e2523efe52a7ac89f0567b8798fd857b1e71ae3`.
- The `linux/amd64` Nordic toolchain container by immutable OCI digest. The
  human-readable `v2.5-branch` tag is recorded only as provenance and is never
  treated as a lock.
- Board, Kconfig file, and the checked-in devicetree overlay that actually
  exists at the Omi tag.

The NCS manifest contains inactive/private projects that are not build inputs
and cannot be fetched by this candidate. The builder therefore never asks West
to resolve or freeze the full manifest. It asks `west list` for active projects
only, then reads each active repository's exact local `HEAD` and clean status.
It emits `west-active-projects-frozen.tsv`: UTF-8, path-sorted, one
`path<TAB>40-lowercase-hex-HEAD<LF>` row per active project, including `nrf`.
The artifact SHA-256 and row count, `nrf/west.yml` SHA-256, and `.west/config`
SHA-256 are bound before and after the build, in the build receipt, and in the
SBOM. Credential-free active-project repository URLs are bound separately so
the SPDX packages remain attributable. Inactive projects are neither fetched
nor inspected.

This snapshot is deterministic evidence of the exact active workspace, not
external execution attestation or a signed dependency lock. Before a production
release it must be reviewed and bound to the external two-replica provenance.
Until then, the process remains a pinned candidate build rather than a
bit-for-bit production recipe.

## Quarantined candidate build control (implemented, not executed)

Do not copy this repository into an ad-hoc networked container and do not run a
candidate build from the attached pendant. The reviewed build design separates
public dependency fetching from the private candidate, executes the candidate
with networking disabled and no device mounts, and compares two independent
replica packages before accepting any bytes.

The exact reviewed candidate is
`5786f71b38b7a07ef5cb590159d77c4808059525`. Its
`firmware/scripts/build_candidate.py` SHA-256 is
`17139085ad0ca33c250f2aabb1fb986018cf905813606447bb4a6e5e4b1e218b`.
That candidate pins the actual `xiao_ble_sense` board, the raw and cached CMake
paths and types, and rejects aliases, remapped boards, duplicate or multivalue
inputs, control characters, and configuration drift.

A separate fail-closed control plane is preserved in the local worktree
`/Users/omarebrahim/anticipation-lanes/firmware-ci-signed` as native SSH-signed
commit `e69366ca3c992d22f16ac782eb719d0cc67a699b`, whose parent is current remote
`main` commit `2a513db2968ddde853c280c3ead2bfe8603c3993`. Its focused control suite is
29/29 green. The workflow SHA-256 is
`764662bdee9f53f892a33b55375bf55a45b621ca8d48c1695898a70338ce3287`.

That signed commit is **local only**. GitHub refused the HTTPS push because the
current OAuth token lacks workflow-write scope. No permission was broadened and
no browser upload was submitted. The workflow also deliberately requests the
unavailable runner label `anticipy-firmware-40gb`, refuses non-GitHub-hosted
runners before checkout, and the repository has no matching runner. The current
repository `main` is not a safe immutable trust root because it is unprotected
and has non-owner collaborators. Therefore the current decision is **NO PUSH
WORKAROUND, NO DISPATCH, NO ARTIFACT, NO FLASH**.

Before a build can run, the exact reviewed control bytes must be migrated into
an owner-only protected control repository and independently re-reviewed. It
then needs either two eligible organization larger hosted runners or two fresh
one-job JIT/ephemeral runners under that owner-only control. Changing the
current `github-hosted` guard, repository identity, workflow permission, or
runner design is a new security-sensitive change, not a clerical bypass.

The control requires each replica host to have at least 40 GiB free, three CPUs,
and 16 GiB available memory. Only a copied trusted fetch script and empty public
dependency/evidence directories enter the network-enabled container; it sees no
candidate checkout or GitHub token. Runtime construction and the candidate run
then execute with `--network=none`, read-only inputs, no devices, dropped
capabilities, no-new-privileges, and resource caps. Provider ZIPs are hashed
before safe extraction, and the independent replicas must match byte for byte.

`build_candidate.py` itself refuses to run unless all of the following agree
with the locks: upstream source, Anticipy patch, exact west topdir/config, NCS
commit, NCS manifest hash, Zephyr commit, every active west project present and clean,
required tools, ARM compiler, exact board/CMake inputs, and an explicit
container-digest declaration. It binds every active project path, repository,
and HEAD before the build, then verifies that those values, the local West
config, `nrf/west.yml`, and clean state did not change during the build. An
accepted replica would emit:

- the deterministic source receipt;
- canonical `west-active-projects-frozen.tsv`, its SHA-256, and project count;
- exact pre/post hashes for `nrf/west.yml` and `.west/config`;
- a deterministic SPDX 2.3 JSON SBOM whose packages bind the source overlay,
  exact active-project commits and repositories, the snapshot/config/manifest
  evidence, and digest-declared toolchain container,
  and whose files bind every emitted ELF/HEX/BIN/UF2/map artifact by SHA-256;
- exact tool versions and build command;
- all active west project paths, repositories, commits, and pre/post
  cleanliness evidence;
- complete build log and hash;
- sizes and SHA-256 values for emitted ELF/HEX/BIN/UF2/map files; and
- explicit `flash_approved: false` and `flash_performed: false` fields.

The SBOM is emitted only after the build, UF2, and pre/post SDK invariants pass.
The builder derives `SOURCE_DATE_EPOCH` from the locked upstream Git commit,
validates against a vendored official SPDX v2.3 Draft-07 schema, atomically
writes the document, rehashes the firmware artifacts, and records the final
SBOM SHA-256 in `ANTICIPY_BUILD_RECEIPT.json`. A failed build, missing validator,
schema drift, active-project/config/manifest drift, or artifact drift emits no
SBOM and cannot become an accepted candidate.

`--probe` includes this offline SBOM gate in `ready`. The generator contract is
`anticipy-firmware-spdx` 1.0.0 under exact CPython 3.10.14, `jsonschema` 4.26.0,
and PyYAML 6.0.3; a missing dependency or any version mismatch makes readiness
false. These identities are locked, recorded in the receipt and SPDX creators,
and included in a namespace derived from the complete canonical document body.
Every active west project must also carry a credential-free HTTPS repository
URL and exact Git commit. No path-only or `NOASSERTION` project provenance is
accepted.
Reserved SBOM/atomic-temporary output from a failed or contaminated build is
removed or causes the candidate to be refused, and every sensitive path rejects
symlinks in all existing ancestors.

The official schema is vendored as base64 so its decoded bytes remain identical
to `schemas/spdx-schema.json` from SPDX tag `v2.3`, commit
`aadf3b0b8dbbabdb4d880b0fc714255fea436ff7`, SHA-256
`239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b`.
Its immutable source URL and hash are in `replacement/spdx-schema.lock.json`;
runtime validation is offline and fails closed if Python `jsonschema` Draft-07
or PyYAML validation is unavailable. The SBOM classifies west repositories as
build inputs, not as a claim that every repository byte is linked or shipped.

The digest environment variable is an operator declaration, not an attestation.
The process cannot prove which OCI image contains itself, so the receipt labels
this fact `UNVERIFIED_OPERATOR_DECLARATION` and never records the expected digest
as an observed runtime fact. Production still needs externally generated,
verifiable OCI/CI provenance bound to the artifact hashes.
The SPDX inventory likewise is not a signature, reproducibility attestation,
flash approval, or physical-hardware proof.

The following local probe is read-only and does not fetch, build, sign, upload,
dispatch, flash, or touch hardware:

```bash
python3 firmware/scripts/build_candidate.py --probe
```

A passing repository verification and probe is not a release authorization.
The separately recorded local development package is explicitly not an
accepted candidate. No release SBOM, signed firmware, or flash-approved UF2
exists.

## Gates that source reproducibility does not solve

An Anticipy-owned release still requires all of these before any production
flash:

- identify the physical board revision and bootloader/recovery behavior;
- implement and review an Anticipy-owned signed boot/update chain with signing
  keys held outside source control, version policy, and rollback protection;
- prove the selected settings/NVS partition and CELT-only link closure in the
  exact pinned embedded build;
- implement authenticated first-owner enrollment, an owner allowlist,
  authenticated/OOB pairing or an equivalent documented control, physical bond
  removal, and a deliberate physical recovery flow;
- review and externally attest the canonical active-project snapshot and
  artifact receipt;
- bind artifact hashes to externally verifiable OCI/CI build provenance;
- calibrate the battery curve/divider against the physical board;
- test first on a recoverable spare, then prove BLE/audio/battery/recovery on the
  actual board and a real iPhone.

The source overlay is reviewable and repeatable. Its encrypted single-bond
transport is still not production owner authentication, and removing the
application DFU service does not prove the immutable bootloader or recovery
path secure.
