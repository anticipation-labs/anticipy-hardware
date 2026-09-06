# ANT-PROD-R0B EVT fabrication and impedance request

Send this with the quote and require written acceptance or proposed changes.

## Board construction

- Rigid four-layer, high-Tg FR-4.
- Finished outline: maximum 47.0 x 18.0 mm compact capsule board inside a 51 x 21 mm product exterior.
- Finished thickness: 0.80 mm +/- 0.08 mm including copper. State whether
  solder mask is included in the thickness measurement.
- IPC-6012 Class 2; ENIG; green solder mask both sides.
- Symmetric construction to reduce warpage.
- L1 and L4: 1 oz finished copper; L2 and L3: 0.5 oz copper preferred.
- Minimum design rule: 0.127/0.127 mm (5/5 mil).
- Standard through via: 0.20 mm finished drill, 0.45 mm pad.
- USB reversible-contact fanout uses exactly two exceptional through-vias:
  0.16 mm finished mechanical drill with 0.36 mm pad. This is at the published
  rush process floor and requires written CAM acceptance; do not substitute a
  laser via or silently enlarge it because either change affects schedule or
  the adjacent USB copper.
- No blind, buried, stacked, or laser-drilled vias.
- Panelize with carrier rails and tooling/fiducials appropriate for a thin,
  narrow capsule board.

## Controlled impedance

- USB D+ and D- leave the connector/protection device on L1, then run together
  on L3 (In2.Cu) over continuous L2 ground, returning to L1 only at the radio
  module. There are no signal traces on L2.
- 90 ohm differential target, +/-10% manufacturing tolerance.
- Before CAM release, return:
  - exact laminate and Tg;
  - pressed dielectric thicknesses;
  - Dk used in the calculation;
  - finished copper thicknesses;
  - required USB trace width and pair gap;
  - complete Arkeo or equivalent stack-up drawing;
  - any proposed CAM width adjustment for written approval.
- Include a USB differential coupon on every panel and provide the TDR report.

## Rush acceptance questions

1. Is 0.80 mm four-layer material physically in stock?
2. Do 5/5 mil, standard 0.20/0.45 mm through-vias, and the two explicit
   0.16/0.36 mm USB fanout vias qualify for the rush clock?
3. Is the custom USB4500 mid-mount edge geometry accepted?
4. Can you reserve fabrication and assembly capacity before final files arrive?
5. Can you assemble exactly two first articles, perform AOI/X-ray, then hold the
   remaining ten until written release?
6. Are QFN exposed-pad, WSON, 0201 passives, and customer-consigned radio
   modules accepted for the rush build?
7. Will you provide 100% bare-board electrical test, DFM/check plots, AOI and
   X-ray reports, and the controlled-impedance TDR report?
8. What exact date/time will the two first articles be available for Surrey
   pickup, assuming approved files and consigned parts arrive Monday morning?

## Public capability basis

- Canadian Circuits publishes four-layer construction, but its public standard
  stack-up is 1.6 mm, so 0.8 mm requires confirmation:
  https://www.canadiancircuits.com/wp-content/uploads/2020/11/Sheet-Stack-Sheet-for-Website-Oct-2020.pdf
- It publishes impedance modelling, coupons, and TDR testing:
  https://www.canadiancircuits.com/pcb-services/impedance-control/
- It publishes 6 mil minimum mechanical drilling and notes that outsourced
  laser drilling adds time:
  https://www.canadiancircuits.com/capabilities/drill-capabilities/
- Published rapid lead times apply to PCB fabrication and depend on material,
  technology, and complete files; they are not a public guarantee of five-day
  double-sided PCBA:
  https://www.canadiancircuits.com/capabilities/lead-times/
