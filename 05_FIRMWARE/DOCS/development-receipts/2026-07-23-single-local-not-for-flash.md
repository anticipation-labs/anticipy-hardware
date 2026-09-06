# Anticipy firmware development build — 2026-07-23

## Classification

This records one successful local, offline development build.

It is **not** a release, signed firmware, a production-candidate gate result,
an SPDX SBOM, an independent attestation, a two-replica result, authorization
to flash, or evidence from physical hardware. No pendant was flashed or
accessed. No BLE, battery, microphone, haptic, recovery, or secure-update
behavior was physically tested.

Stable evidence package:

`/Users/omarebrahim/Downloads/Anticipy-Firmware-Development-NOT-FOR-FLASH-20260723-437dc9e3`

Run this from that directory to verify every packaged file:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

The top-level `SHA256SUMS.txt` includes the corrected JSON receipt. Its own
SHA-256 is:

`b94720e23deac196804d32fdf1f5c883d3d7f30976e67984f262a7307f225988`

## Locked inputs

- Candidate commit:
  `5786f71b38b7a07ef5cb590159d77c4808059525`
- Signed control commit:
  `e69366ca3c992d22f16ac782eb719d0cc67a699b`
- Control lock SHA-256:
  `e5a30d8d87956baca76eac1a66af3f5317ef0ed04229268674bba70a8a2a56a3`
- Materialized source receipt SHA-256:
  `ba3a6fa71fd7262ad84bb3bcb96930644e6dfae45f4e5da2e477be61c5c95c1a`
- Materialized content-tree SHA-256:
  `cb066c79980475b14569dcb9555962e179edd8f941046f14f5e88b96a222d074`
- Source patch SHA-256:
  `78ce347d4df1a0a043a1d5ad607c9cff7be75b449c3105c6b202d8ab56dc3b66`
- Nordic nRF Connect SDK commit:
  `1fae141fc6713dd331b797fc96c90dc84552242d`
- Zephyr commit:
  `2e2523efe52a7ac89f0567b8798fd857b1e71ae3`
- Locked `west.yml` SHA-256:
  `aa1f2d23a024719b6bde72dc434cb844ed8a21fa415dd7b8ee6de51eecda7e93`
- Active-project inventory: 45 clean repositories, unchanged before and after
  the build; inventory SHA-256:
  `b4f80b87a1c92e743addaaf59d3f15a69684cf191f596ceb97ec6c6f9d7672e0`
- Toolchain image:
  `docker.io/nordicplayground/nrfconnect-sdk@sha256:f50c51b711bbb3f502496c4b83e88dda778420fb83327d4791f9bc0e34916d01`
- OCI config digest:
  `sha256:207d3b4bb50b2e6b4252c53d654c315f8960af1a2f7bcd5b26ed1b44c7f9fc29`
- Receipt generator SHA-256:
  `a1e00ebde3f81b5e946301dcf841cbdc826fea4f3c69db8c463c1889f3cc9879`

The signed control commit was verified with the owner's allowed-signers file.
All 11 candidate security files matched its control lock.

## West configuration correction

The canonical workspace `.west/config` remained on its original SHA-256
`cf1cf23eeb6d3d45215031bcc9c029ecb805497b6fc20b997f49f995c7895ea6`
and was part of the read-only `/ncs` mount.

The effective `/ncs/.west/config` was a separate writable overlay. The build
guard required that overlay to begin at the canonical hash above. West then
appended:

```ini
[zephyr]
base = zephyr
```

The observed post-build overlay SHA-256 is
`59620dc18f46833ec79da979b1869516220c11c4347b80b2d69c0b4c82bb2cce`.
The corrected JSON receipt keeps the canonical file and effective overlay as
two different facts.

## Build and isolation

The build ran from
`2026-07-23T08:49:07.21669217Z` through
`2026-07-23T08:54:12.434187423Z` and exited 0.

The container used:

- no network;
- no host devices;
- an immutable root filesystem;
- all Linux capabilities dropped;
- `no-new-privileges`;
- no privileged mode;
- a 6 GiB memory limit, 3 CPU limit, and 2,048 PID limit;
- bounded `tmpfs` mounts for the home directory, temporary files, and nrfutil
  logs.

The raw, selected container inspection is packaged as
`ANTICIPY_DEVELOPMENT_CONTAINER_INSPECTION_NOT_ATTESTED.json`, SHA-256
`fc54fac5a7230fcf1ecb57bf018e467ac6d674046cc39ee881ba1b6b15673d38`.
The build log SHA-256 is
`0271a7d97b970dd11da8122748ee477f09b971fec90af28521907a0ad4463e52`.

The exact in-container build command was:

```sh
west build --pristine -b xiao_ble_sense -d /development/output /candidate/firmware/.build/source/anticipy-v2.0.1 -- -DZEPHYR_BASE:PATH=/ncs/zephyr -DCONF_FILE:STRING=prj_xiao_ble_sense_devkitv2-adafruit.conf -DDTC_OVERLAY_FILE:STRING=overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay
```

No flash, debug, probe, serial, USB-device, or BLE command was run.

## Exact CMake inputs

`CMakeCache.txt`, SHA-256
`a4c599ba28b9ae37165a3be8ef0d7bdf25605e1259f18dc1c92381ac851eadf2`,
was checked for the following exact inputs:

- board: `xiao_ble_sense`;
- board directory: `/ncs/zephyr/boards/arm/xiao_ble`;
- source directory:
  `/candidate/firmware/.build/source/anticipy-v2.0.1`;
- configuration file, resolved relative to the source:
  `/candidate/firmware/.build/source/anticipy-v2.0.1/prj_xiao_ble_sense_devkitv2-adafruit.conf`;
- devicetree overlay, resolved relative to the source:
  `/candidate/firmware/.build/source/anticipy-v2.0.1/overlay/xiao_ble_sense_devkitv2-adafruit_module.overlay`;
- Zephyr base: `/ncs/zephyr`.

The board-definition Git tree OID was
`8703fc4ab1f5bb7dca23c679ba2c681b34067c22`.

## Artifacts and structural checks

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `zephyr.elf` | 5,240,756 | `0f4dc109c68549a86ae47f65f16716af9fc4255404ec375f462dafcf21bc6689` |
| `zephyr.hex` | 772,213 | `c0a6bde2319d36e3381b2b29279c5490063f75b7d1d1cf5e8cf5a5ebd8a2f4db` |
| `zephyr.bin` | 274,468 | `b7cddedb7010c68a56d126124a9906f9097236da609db5dd6c2d249665fd6506` |
| `zephyr.uf2` | 549,376 | `437dc9e33ef5ad86eaa25d8eccd593110c08569d68df64cb1efbfeadf536ad99` |
| `zephyr.map` | 1,525,047 | `f34011c1082e7718e38e5cdaa5efd14021c4e388ea0e4169bbaac2da64034ad1` |

The trusted signed-control UF2 validator accepted the file structure:

- family ID `0xada52840`;
- flags `0x00002000`;
- address range `0x00027000` through `0x0006a100` exclusive;
- 1,073 blocks;
- 256 payload bytes per block;
- 274,688 UF2 payload bytes.

This is a structural result only. It does not establish safe or functional
behavior on a physical pendant.

The ELF is 32-bit little-endian ARM executable data. Inspection found locked
symbols for battery broadcasting/smoothing, transport start, and audio-codec
reads. The compiled configuration and binary contain `Anticipy`,
`Anticipy Pendant`, the BLE peripheral and battery-service settings, and flash
load offset `0x27000`. These markers show that expected code and configuration
were linked; they do not prove physical BLE, audio, battery, or haptic behavior.

Reported image usage was 274,468 flash bytes and 210,160 RAM bytes.

## Receipts

- Corrected development receipt:
  `ANTICIPY_DEVELOPMENT_BUILD_RECEIPT_NOT_FOR_FLASH.json`, SHA-256
  `3ce8729448cd65bee80043e33f7f3d097c6fff13d7349a734f94d7b3f731763a`
- Development component inventory:
  `ANTICIPY_DEVELOPMENT_COMPONENT_INVENTORY_NOT_ATTESTED.json`, SHA-256
  `a26a28526f2106823f3039f178652e46eabd4e204897267cedc09ca1b2d1e58c`
- Container inspection:
  `ANTICIPY_DEVELOPMENT_CONTAINER_INSPECTION_NOT_ATTESTED.json`, SHA-256
  `fc54fac5a7230fcf1ecb57bf018e467ac6d674046cc39ee881ba1b6b15673d38`

The component inventory is intentionally not labeled an SPDX release SBOM
because a complete frozen manifest could not be produced.

## Incomplete production controls

The signed production constructor did not pass. Exact blockers observed:

- its read-only container contract blocks nrfutil log and toolchain-lock
  writes;
- `HOME=/home/ci` plus the host UID cannot access the embedded toolchain under
  `/root`;
- the image starts in an unrelated baked west workspace;
- `west init --mr` cannot use a raw commit as a `git clone --branch` value;
- an active-only west update cannot satisfy `west manifest --freeze`;
- inactive manifest entries include `nrf-802154`, which requested
  authentication, and `dragoon`, which points to an unavailable
  Nordic-internal Bitbucket host;
- the exact runtime constructor needs `zlib.h`, absent from the pinned
  environment.

Therefore there is no complete frozen manifest, release SPDX SBOM, signed
release receipt, independent attestation, production-candidate result,
two-replica result, or physical test result.

A requested same-host second development build was not completed. The bounded
launcher retries stopped before the build script ran, and the separate output
directory remained empty. This receipt makes no reproducibility claim.

## Independent safety triage

A separate read-only review classified the exact build as **NO-GO even for a
recoverable spare**. The 48 compiler diagnostics comprise 23 compile/config
noise warnings, 22 latent or disabled-feature warnings, and three active
storage-runtime warnings. More importantly, source and ELF inspection found
active defects outside that warning count:

- fresh-SD initialization frees a generated filename before passing it to
  `create_file()`;
- offline storage can copy codec frames up to 320 bytes into 79-byte payload
  slots;
- SD directory enumeration can write past `file_num_array[40]`;
- a 1–79 byte final storage packet can underflow the remaining-length counter;
- failed reads or BLE notifications can still advance download state;
- optional speaker initialization can return a false success before BLE
  advertising, battery setup, and the pusher start;
- mount and haptic failures are not handled before dependent work continues;
- the disabled speaker write path is unsafe if enabled; and
- application USB still uses Zephyr's generic testing identity.

The current CELT-only image happens to allocate a large enough Opus encoder
buffer, but its assertion macro discards the encoder-size result instead of
enforcing the bound. Disabled logging and SILK/Hybrid paths contain additional
latent type/prototype and array-bound hazards.

Before another build, fix the SD/storage memory and length defects, make
optional hardware failures unable to suppress BLE advertising, replace the
assertion macros with single-evaluation parenthesized forms, correct the
prototype/type/GPIO issues, compile only the selected Opus mode, and assign or
disable application USB identity. Require a warning-free build with relevant
warnings promoted to errors, sanitizer-backed host tests for SD/storage/codec
boundaries and injected failures, then recoverable-spare BLE/audio/battery/
haptic/recovery tests. Only a new artifact built from that reviewed source may
re-enter the release gate.

This triage did not edit source or access hardware. It strengthens the
classification: the packaged UF2 must not be flashed.

## Cleanup after handoff

Preserve:

- the stable 8.3 MiB evidence package in `Downloads`;
- this tracked receipt;
- the canonical candidate source, locks, signed control repository, and any
  separate iOS release artifacts.

After the exact current package passed an independent rereview and its complete
checksum manifest passed again, the following local-only data was removed
without losing the preserved development artifact:

- the 2.9 GiB active NCS workspace;
- the 169 MiB candidate worktree, using `git worktree remove` rather than
  deleting its directory directly;
- the 44 MiB development output after confirming the package checksum;
- both superseded 8.3 MiB package directories under the run-3 quarantine;
- the empty second-output directory and its writable west-config copy;
- the stopped failed `anticipy-fw-*` containers.

The detached candidate worktree was clean and was removed through
`git worktree remove`; its registration was pruned. The successful and failed
`anticipy-fw-*` containers, all three local-quarantine workspaces, and the
newly pulled pinned Nordic image were then removed. The stable package, this
receipt, canonical source/locks, signed control worktree, iOS archive/export/
IPA, Simulator runtime/data, and unrelated Docker images were preserved. The
package checksum passed again after cleanup, and free disk space rose to about
26 GiB.
