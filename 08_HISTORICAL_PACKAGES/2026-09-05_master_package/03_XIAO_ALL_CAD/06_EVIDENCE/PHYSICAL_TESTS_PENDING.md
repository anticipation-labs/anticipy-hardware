# Physical tests pending for Unit 001

This file is intentionally red until a named builder records evidence. CAD and
static firmware verification cannot replace these checks.

- [ ] Printed PETG body, hooked face, and headerless XIAO measured and photographed.
- [ ] Exact battery label/lot/documents/polarity/OCV/finished dimensions pass.
- [ ] Battery lead route and strain relief dry-fit without pouch pressure.
- [ ] Exact motor and finished SMD driver pass size/current/thermal checks; the
      labelled active-high/active-low firmware matches its exact circuit.
- [ ] Empty sacrificial body passes the Renata-only jig, 2.2–2.4 mm hole,
      90-degree countersink, screw/post clamp and mechanical-abuse gates.
- [ ] Complete unpowered stack closes with clean witness film and fingertip
      pressure through the face's real drop-and-slide motion.
- [ ] Full erase, intended TestFlight version, Phone A ownership/reconnect,
      Phone B rejection, live audio, haptic, and recovery pass.
- [ ] Battery-branch charge current is measured through bootloader,
      application, termination, and recharge and is within the exact pack
      limit with margin.
- [ ] Closed-case RF/audio/runtime/thermal/system-off/wake tests pass.
- [ ] Lee/Renata fallback, if selected, stays <=160 mA combined peak and <=80
      mA combined continuous with no reset or heat.
- [ ] Shake, twist, drop, USB handling, reopen inspection, and final cosmetics
      pass with no pouch mark or seam movement.

Only a completely initialled `QA_RELEASE.md` changes Unit 001 from HOLD to
PASS. Units 002-012 remain blocked until that first unit passes unchanged.
