# PCBA RFQ and panel requirements

**RFQ state: usable for capability/lead-time discussion only. Purchase release is blocked by the missing files in `FACTORY_UPLOAD_MANIFEST.csv`.**

## Quantities to quote separately

| Phase | Required good assembled PCBAs | Rule |
|---|---:|---|
| EVT-A | 10 | No automatic follow-on order |
| DVT | 35 | Quote now; release only after EVT ECO and acceptance |
| PVT | 230 | Quote now; release only after DVT/compliance gates; 230 is 15% above the 200-good-unit customer target |

The supplier must state panel input quantity, expected assembly attrition, allowed over/under-run and the guaranteed number of electrically accepted PCBAs. Anticipy is purchasing accepted assemblies, not merely panels started.

## Board direction to quote

- Product: `ANT-PCB-EVT-A`, revision to be frozen in the released files.
- Four copper layers.
- 0.60 mm finished thickness.
- ENIG direction, subject to written assembler compatibility review.
- Shaped concept: 31.0 × 14.0 mm main region joined to a 6.5 × 6.5 mm RF nose.
- Double-sided SMT is expected; quote it explicitly.
- Smallest/fine-pitch packages include nPM1300 WLCSP and DRV2605L DSBGA; quote X-ray inspection explicitly.
- Controlled 50-ohm RF path and manufacturer-approved stack-up are required; do not calculate impedance from the concept STEP.
- No unapproved component substitutions.

The released fabrication drawing, Gerbers and stack-up—not this text—will be authoritative when they exist.

## Panel proposal required from assembler

The assembler must return a marked panel drawing before production showing:

1. panel dimensions and board count;
2. tooling rails and rail width;
3. global and local fiducials;
4. tooling holes;
5. breakaway-tab or routing locations;
6. board origin, rotation and pick-and-place origin;
7. coupon/impedance-test location, if required;
8. assembly-side sequence;
9. depanelization method and permitted edge witness;
10. traceability marking location.

No tab, mouse bite, tooling copper or rail feature may intrude into the antenna keep-out, microphone acoustic interfaces, charging interfaces or a controlled cosmetic edge. The tiny product board must be panelized; loose-board handling is not an accepted assumption.

## Quote must break out

- PCB fabrication price and fabrication business days.
- SMT/NPI setup price and assembly business days.
- Components by exact manufacturer ordering code.
- Part sourcing lead time and inventory reservation duration.
- Customer-consigned-part fees and receiving time.
- Stencil/paste charges.
- X-ray, AOI and any first-article charges.
- Programming and power-on test charges.
- Fixture/NRE charges.
- Panelization/depanelization charges.
- Rework/failed-unit policy and yield reporting.
- Packaging, MSL handling/baking and dry-pack charges.
- Express freight, duties/tax terms and delivery estimate to Vancouver.
- Quote validity and any non-cancellable/non-returnable material.

Fabrication time, assembly time, component procurement time and transit time must be stated separately. Marketing lead time is not an accepted delivery commitment.

## Material and process confirmations

The factory must confirm in writing:

- proposed 0.60 mm four-layer stack-up and thickness tolerance;
- finished copper and ENIG specification;
- solder-mask registration and minimum dam compatible with the released design;
- finished routing/profile tolerance;
- via construction and fill/cap requirements, if any;
- WLCSP/DSBGA/LGA placement capability;
- X-ray coverage and acceptance method;
- reflow profile compatibility with every moisture-sensitive part;
- panel flatness/warpage limits;
- electrical bare-board test method;
- IPC workmanship class to be stated in the quote;
- cleaning/no-clean process and ionic-contamination controls;
- serialized traceability from finished PCBA to panel, date code and component lot.

## First-article hold

For every new PCB revision:

1. Assemble only the agreed first-article quantity.
2. Send top/bottom optical and required X-ray evidence.
3. Run the supplied safe power-on and test script.
4. Hold the remainder until Anticipy records written first-article acceptance.

No photo approval can waive a released drawing, polarity, placement or electrical requirement.

## Files required before any paid PCBA release

- Gerber X2 and NC drill.
- IPC-356 netlist.
- Complete released BOM with DNI and approved alternates.
- Centroid/pick-and-place file.
- Top/bottom paste data.
- Fabrication, stack-up/impedance and assembly drawings.
- Panel drawing approved by both parties.
- Populated board STEP aligned to the controlled origin.
- Unfiltered ERC and DRC reports with zero unexplained findings.
- Supplier DFM report with every issue closed.
- Released firmware, hash and programming instruction.
- Released test-point map and power-on/EOL procedure.
- Approved battery interface drawing even if the battery is fitted later.

If one required file is absent, status remains `MISSING_BLOCKING` and the supplier must not fabricate from an earlier email attachment or mechanical STEP.

