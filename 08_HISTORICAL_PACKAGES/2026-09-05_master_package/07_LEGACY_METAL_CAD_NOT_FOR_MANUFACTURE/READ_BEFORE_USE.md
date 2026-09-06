# STOP - historical shell reconstruction only

These files are included so the ordered geometry can be investigated and
compared when Xometry supplies its original uploads. They are **not released
for manufacture or batch assembly**.

## Provenance

- Private repository: `omize10/Anticipy`
- Devin PR: `#19`, open and unmerged
- Historical source commit: `23b5cec95f542efdfe00fc7b5edeaeb1def5746c`
- Generator Git blob: `16bbec7cb7aefbbe151e13df81bdf0e5b6ac7a73`
- Generator output names: `alu_body.step` and `alu_face_front_v3.step`

The STEP/DXF outputs were not committed to GitHub. They were regenerated from
the proven generator, so their geometry and names are useful evidence, but
their bytes cannot be matched to the files uploaded to Xometry until Xometry
returns its copies.

## Blocking findings

- `alu_body.step` measures 51 x 22 x 10 mm.
- `alu_face_front_v3.step` measures 47.8 x 20.3 x 2 mm and contains two
  disconnected solids. The second is a detached 0.9 mm-long end sliver.
- Later Devin commit `50b45b69ca862bb614f3e81c19ad597fa801e9f1`
  states that the 11 mm custom-PCB enclosure did not close because the stack
  height was budgeted incorrectly.
- Current PR-head CAD is a different custom-PCB shell: 51 x 25 x 12.86 mm or
  51 x 25 x 13.86 mm. It is not a XIAO Friday Core enclosure.
- A nominal 22.481981 mm XIAO plus the listed 25 mm battery length totals
  47.481981 mm inside a reconstructed 48 mm cavity. The remaining 0.518019 mm
  does not establish room for pack tolerance, protection-board overhang,
  wires, bend radius, or assembly clearance.

Use the delivered nylon shell itself as the authority. Build one open-shell
canary, measure the complete protected cell and connector, and never force the
face closed over a LiPo pouch.
