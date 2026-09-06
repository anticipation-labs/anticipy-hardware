# Corrected shell-recovery CAD evidence

- Generator SHA-256:
  `2e723cb60e1d104ed61905e05d2f3b950333bb9277fb6ee238384e65926b73ac`
- Packaged historical body/face references byte-match the pulled repository
  source.
- Two clean generator runs produce byte-identical `FIT_REPORT.json` and all 29
  packaged STL files.
- All 29 generated STLs are closed/watertight, manifold, outward-oriented, and contain no
  degenerate triangles.
- All 35 generated STEP files import as valid OCC geometry; repeated solid/face/edge
  counts, volume, area, and bounds match. STEP bytes themselves can vary because
  the exporter writes timestamp/presentation metadata.
- The enforced report contains 1,424 intersection values: body/bands, 13 face
  drop positions, 21 face lock-slide positions, every part against body/band/
  locked face, every part pair, and the full face motion against all five parts
  across the primary, four standard-battery/Vybronics layouts and conditional
  DTP401525/Vybronics/rotated-driver layout.
- Maximum modeled overlap: `0.0 mm3`; abort tolerance: `1e-6 mm3`.
- Full-shell PETG exports are watertight and consistently wound. Body STL:
  `0abcfd7c83ffdd6b96833dc71c48fb1688978f8e369c1f4ad038f19de9d5ff81`;
  hooked-face STL:
  `cc34568c306975b87e6c9c711e100d7e796b84ea5e0da9ab8d8b4785f32e7c83`.
- The dedicated screw-layout motor audit qualifies a conservative
  10.2 x 10.2 x 2.7 mm mechanical envelope at the existing centre with zero
  collision against body, full face motion, band, battery, bridge, XIAO,
  antenna keepout, driver, posts, and drill axes. It covers the listed Lee
  PID10431 body dimension; received-part electrical qualification remains a
  separate physical gate.

The primary physical closure is the Renata-only M2 screw-retained band with
keyed posts and body marking jig. CAD permits 2.2 mm preferred or 3/32 inch
(2.381 mm) body holes and audits through 2.4 mm; physical drilling and abuse
tests remain mandatory.

This is **CAD PASS / physical qualification required**. The side-strip driver
has only 0.2 mm nominal wall margin. Conditional DTP401525 geometry has 0.15 mm
nominal shelf clearance, 0.40 mm adjacent-hard-part gaps and full antenna-zone
overlap. Actual printed shell,
battery body/leads, solder/wires, and closure must pass gauges and RF/no-load
tests.
