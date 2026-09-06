# Anticipy f717 local firmware runtime evidence — NO-GO

Captured on 2026-07-23 from candidate
`f717c7fe8b713e7911d7ed9eb2e0bc0e053884ee` and trusted-control
head `b7641f22ac6710f7e85e30a6ee99493cd93fe00a`.

## Outcome

No current Anticipy firmware artifact was produced. Nothing in this receipt is
approved for flashing.

The exact locked NCS workspace and public inputs were prepared successfully,
but the first offline runtime attempt stopped before compilation because the
digest-pinned Nordic image did not contain an external `xz` executable.
Commit `68262d4eb995d77d56d33fca8465f36359e4c760` replaced that dependency
with a trusted, hash-bound CPython/lzma/tarfile extractor.

The one permitted fresh retry then:

1. verified and extracted both locked XZ archives;
2. built and installed locked zlib;
3. configured and compiled CPython 3.10.14;
4. reached CPython `make install`;
5. failed closed when `ensurepip` inherited Nordic's bootstrap
   `PYTHONHOME=/root/ncs/toolchains/7795df4459/usr/local`, redirected Python
   3.10 to the toolchain's Python 3.8 prefix, and could not import
   `encodings`.

The candidate phase did not run. `candidate-build` is empty; there is no
candidate process log, runtime observation, SBOM, ELF, HEX, BIN, UF2, map,
package, reproducibility comparison, signature, flash approval, or hardware
write.

Commit `b7641f22ac6710f7e85e30a6ee99493cd93fe00a` now unsets inherited
`PYTHONHOME` before any child process and fails closed if it remains present.
The repair is independently reviewed and repository-tested, but the
no-third-runtime-execution boundary remains in force. A future execution needs
explicit new authorization and entirely fresh output directories.

## Bound inputs

```text
f717c7fe8b713e7911d7ed9eb2e0bc0e053884ee  candidate Git commit
1fae141fc6713dd331b797fc96c90dc84552242d  NCS nrf commit
2e2523efe52a7ac89f0567b8798fd857b1e71ae3  Zephyr commit
ee9892562648f074e3c6b59d508127d81fa21010  Omi source commit
sha256:f50c51b711bbb3f502496c4b83e88dda778420fb83327d4791f9bc0e34916d01  Nordic image
a20d7a500132a9216db77374779d5fb218feef4beb3b309c8310d0673e70a5ad  public-input receipt
0f439f881430912d9d57ab84c7f76501222a93805affc2e914be479055045a81  pristine toolchain metadata
```

The fresh NCS preparation froze 45 active projects and 45 credential-free
repository URLs. Runtime and candidate containers were specified with
`--network=none`, `--pull=never`, no device mount, no credentials, a read-only
root, read-only source/NCS/toolchain inputs, all capabilities dropped,
`no-new-privileges`, and phase-specific writable output directories.

This Mac's Docker VM has 8 CPUs and about 8.2 GB RAM. It cannot satisfy the
official trusted-control minimum of 16 GiB RAM and 40 GiB free storage, so even
a successful local build would remain development evidence, not a production
replica.

## Failure evidence

```text
ffe3c8d20b7dc11e4296496c632bbaad8c2b723e90394ca815af5e81825f994c  first runtime/XZ failure log
0556bf527b76c8feb2ece6df5575f41b6443ec3129f2bbe38319b93a042139eb  successful NCS preparation log
ede38e7e6efb4a1257db27224a502aa33ad42eb18bb379f50a8dcc087b45492c  runtime2 outer log
408650475560661c81830c624a7399679a0720251e7bb1a16438b57973b5b761  runtime2 Python build log
```

The partial runtime contains 7,760 entries and the partial runtime-build tree
contains 5,441 entries. They are contaminated failure evidence and must never
be resumed or used as candidate inputs.

## Repair verification

- Trusted firmware-control tests: 73/73 passed.
- Additional extractor review: 25/25 unsafe archive cases refused.
- Exact pinned CPython 3.8.2 executable, `tarfile.py`, `lzma.py`, and
  `_lzma.so` hashes match the bootstrap lock.
- Both locked archives match size/SHA-256 and use XZ CRC64.
- The `PYTHONHOME` regression executes the real initialization prefix under a
  hostile inherited value and proves that a child Python sees neither the
  variable nor a redirected prefix.
- Two independent P0/P1 reviews returned GO for the source repairs and NO-GO
  for any additional execution or flash.
- Final repository gate log:
  `a14f75e35bb3821eb73e2e06fcef757d74f9eb656ed7404ab20c58f8e05ec1bd`.
  It ended `ALL CHECKS GREEN`.

## Physical truth

The attached USB device still identifies only as generic Zephyr `USB_DEV`,
VID:PID `2FE3:0100`, at `/dev/cu.usbmodem1101`. It is not mounted as a UF2
bootloader, and USB descriptors do not identify its exact flash bytes.

The two local `anticipy*.uf2` downloads are byte-identical at
`2e78015e01d2c5c5f8b5a3b3b827ff2b763992218137bc5e5c989725b7e4dc8a`.
They remain binary-only, unverified, and **DO NOT FLASH**.

No serial session, reset, bootloader transition, BLE connection, pairing,
microphone use, firmware build, firmware artifact, device erase, or flash
occurred in this run. Physical BLE advertisement, GATT/Opus audio, battery,
reconnect, recovery, secure update, rollback protection, enrollment, and
pendant haptics remain unproved or unimplemented.
