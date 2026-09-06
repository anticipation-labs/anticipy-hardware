# PCBA factory handoff

## Status

This folder contains an RFQ and capability package only. It is not a fabrication release.

## Planned build

- 12 four-layer PCBAs.
- Approximately 45.8 x 18.0 x 0.80 mm.
- Components on top side only for one SMT reflow pass.
- Rear battery and haptic motor installed by hand only after programming and bare-PCBA test.
- Build exactly two first articles, then hold the other ten pending written release.

## Files the factory will receive after engineering release

- Release README and checksums.
- Gerber ZIP.
- PTH/NPTH drill ZIP and drill map.
- Fabrication drawing and approved stack-up.
- Released BOM with sourcing and substitution controls.
- CPL/pick-and-place CSV.
- Top and rear assembly drawings.
- Schematic PDF and IPC-356 netlist.
- PCBA STEP.
- Programming/test instructions and firmware hash.
- First-article test plan.

## Required factory confirmations

- 0.80 mm four-layer high-Tg FR-4 is physically in stock.
- 5/5 mil, 0.20/0.45 mm standard through-vias, and two 0.16/0.36 mm USB fanout vias are accepted.
- GCT USB4500 mid-mount slots are accepted.
- Exact 90-ohm USB geometry and panel coupon/TDR will be provided.
- 0201, QFN exposed pad, WSON exposed pad, one top-side stencil, and one reflow pass are supported.
- AOI and X-ray of exposed-pad devices are available.
- No substitution or CAM edit occurs without written approval.
- Two first articles can be assembled and the remaining ten held.

