# Quarantine: unverified custom image

`anticipy-unverified-2e78015e.uf2` is preserved so its bytes and history cannot
quietly change. It is **not approved for flashing** and is deliberately named so
it cannot be mistaken for a release.

Known facts:

- The copy observed at `/Users/omarebrahim/Downloads/anticipy.uf2` and the copy
  in the donor repository at commit
  `bb9ff6f47cdb6993c3a0e37bcd7673867b6f7dfd` are byte-identical.
- That donor commit adds only compiled firmware artifacts and proof prose; it
  does not add the source or build logs that produced them.
- The UF2 targets the Nordic nRF52840 family, spans application addresses
  `0x27000..<0x73400`, and contains 1,220 256-byte payload blocks.
- Embedded diagnostic strings include `Anticipy`, `Anticipy Pendant`, and
  `Zephyr OS v3.6.99-100befc70c74`. Strings are forensic clues, not proof of
  runtime behavior or source identity.
- It differs from the official Omi v2.0.1 release UF2: custom size 624,640 and
  SHA-256 `2e7801...`; official size 622,592 and SHA-256 `b1b326...`. All 1,216
  overlapping UF2 payload blocks differ, and the custom image has four extra
  blocks.
- The sibling legacy DFU package in the donor repo declares application version
  `0xffffffff` and contains no demonstrated modern signed/versioned policy.

Run `python3 firmware/scripts/verify_quarantine.py` to verify the checked-in
bytes and UF2 structure against `manifest.json`. The verifier's success means
"quarantine bytes unchanged," never "safe" or "flashable."
