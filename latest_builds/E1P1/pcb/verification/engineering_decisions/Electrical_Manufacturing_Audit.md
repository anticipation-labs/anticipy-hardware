# E1P1 electrical manufacturing closure — 9 September 2026

The local USB ESD placement tolerance problem and a narrow PMIC soldermask web were corrected in the new manufacturing release. Its final audited PCB SHA256 is `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`. Native all-track DRC, unrouted connections and schematic parity are all zero. These checks establish the tested CAD state; they do not establish assembly yield, runtime, acoustic performance, RF performance or wearable qualification.

Source: `outputs/Anticipy_E1P1_PCB_Manufacturing_Release_2026-09-09/pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb`. Original routed and oval releases were not edited. Parent-owned component ordering-code corrections are included in the final hash but are reviewed separately.

## Corrections made

- U4 moved from (28.50,30.00) to (28.15,29.45) mm without rotation. Only its local front-copper D+, D− and ground branches changed. Every via, non-front track, component other than U4, outline and keepout is unchanged. Native ground-region counts remain F/In1/In2/B = 8/2/6/5. All 45 nets pass separate filled-polygon connectivity, including FLASH_CS; the approximate centerline path tool's FLASH_CS limitation is not an unconnected net.
- The entire U4/C1 negative courtyard exception was removed. New positive courtyard separations are 0.070 mm to C1 and 0.050 mm to J1. No copper clearance was relaxed.
- U2 pins 1–32 now have 0.050 mm mask expansion instead of 0.0762 mm. Their 0.300 mm pads on 0.500 mm pitch now leave nominal 0.100 mm mask dams, formerly only 0.0476 mm. U2 exposed-pad mask and its nine paste windows remain unchanged. The matching local footprint was updated.
- U4's three pads now have 0.050 mm mask expansion, matching TI's non-soldermask-defined drawing. Its matching library was updated.
- Native global via filling/capping attributes now say yes, matching the mandatory process below. Geometry and electrical connectivity are unchanged by these fabrication attributes.

The TI DRT maximum body is 1.05 × 0.85 mm before permitted 0.10 mm flash on each side/end. Including flash and terminals gives the conservative 1.25 × 1.05 × 0.50 mm physical rectangle used here. At native −90° rotation, the old U4/C1 maximum-body gap was just 0.025 mm; assuming independent ±0.050 mm placement toward each other allows overlap. The repaired gap is 0.375 mm, leaving 0.275 mm after that assumed placement budget. The ±0.050 mm value is a planning assumption to confirm with the assembler. [TI package and land drawings, pages 26–27](https://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf).

## All remaining negative-courtyard pairs

The remaining exception is limited to twelve named pairs in the Nordic reference power cell. The table uses actual selected-family maximum body rectangles and native rotation/position, not the drawn courtyard or a scaled 3D model. Copper pads/fillets and placement nozzle/rework access require separate process acceptance.

| Pair | Maximum-body gap mm | Gap after assumed 0.05 mm placement each |
|---|---:|---:|
| C1 / C4 | 0.875 | 0.775 |
| C1 / C5 | 0.300 | 0.200 |
| C2 / C3 | 0.800 | 0.700 |
| C2 / C14 | 0.575 | 0.475 |
| C3 / C8 | 0.640 | 0.540 |
| C3 / C15 | 0.575 | 0.475 |
| C4 / C6 | 0.500 | 0.400 |
| C7 / C14 | 0.275 | 0.175 |
| C8 / C15 | 0.875 | 0.775 |
| C9 / C10 | 0.200 | 0.100 |
| R1 / R2 | 0.270 | 0.170 |
| R3 / R4 | 0.270 | 0.170 |

Maximum bodies: TDK C1608X7R1C105K080AC 1.70 × 0.90 × 0.90 mm; Murata GRM188R61E106MA73 1.80 × 1.00 × 1.00; Taiyo EMK107BB7225KA-T manufacturer-linked successor MSASE168BB7225KTNA01 1.80 × 1.00 × 1.00; KEMET C0402C104M4RAC 1.05 × 0.55 × 0.55; Yageo RC0201 0.63 × 0.33 × 0.26. Packaging-only suffix changes do not alter these bodies. Sources: [TDK exact part](https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C1608X7R1C105K080AC), [Murata exact family sheet](https://search.murata.co.jp/Ceramy/image/img/A01X/G101/ENG/GRM188R61E106MA73-01A.pdf), [Taiyo linked successor](https://ds.yuden.co.jp/TYCOMPAS/jp/detail?pn=MSASE168BB7225KTNA01&u=M), [KEMET dimensions and BB thickness](https://content.kemet.com/datasheets/KEM_C1002_X7R_SMD.pdf), [Yageo RC family](https://yageogroup.com/content/Resource%20Library/Datasheet/PYU-RC_51_ROHS_P.pdf).

All twelve pairs have positive maximum-body clearance under this screen. The scoped −0.75 mm courtyard rule is not permission to move these parts closer: acceptance applies to this frozen placement and BOM only. Re-run the body screen after any part or placement change.

## Required fabrication process

1. Four copper layers, nominal 0.80 mm FR-4, ENIG, outer 1 oz/inner 0.5 oz, the named stackup below or an explicitly solved equivalent. Do not substitute a generic 0.8 mm stackup without an impedance calculation.
2. **All 137 plated vias: nonconductive epoxy filled, planarized and copper capped on both ends, IPC-4761 Type VII.** This includes 128 nominal 0.200 mm pre-fill bores with 0.450 mm lands and nine nominal 0.304 mm bores with 0.6096 mm lands. The four J1 plated mounting slots must remain open. A filled/capped via no longer has an open finished hole; do not interpret its drill tool size as a required open bore. The attached coordinate CSV identifies every via in native KiCad coordinates.
3. Confirm flat, solderable caps and the supplier's cap/fill inspection and cross-section criteria. Soldermask tenting, bottom plugging, or an uncapped resin plug is not an equivalent process. [Manufacturer explanation of Type VII filling and capping](https://www.eurocircuits.com/what-is-via-filling/).
4. Routed panel with handling rails, fiducials and adequate support for two reflow passes on this thin, small board. Supplier determines panel construction, tab/depanel positions and tooling clear of the RF keepout and connector cutout. No unreviewed tabs through the antenna area.
5. Verify 0.100 mm U2 mask dams and registration; agree treatment of generic pads with zero explicit local mask margin. J1 is an intentional midmount edge connector; its scoped pad-to-edge exception is not a general board-edge waiver.

The all-via intersection screen finds **14 bores intersecting fitted SMT copper/paste and 15 intersecting component mask openings**. Besides the nine PMIC exposed-pad vias, locations include U2.32 at (36.95,31.50), C4.2 at (29.95,26.175), C6.2 at (28.85,25.50), C6.1 at (30.50,25.95), and U4.1 at (27.65,29.04). One additional U2 mask-only intersection is at (33.181819,31.418180). Ordinary tenting does not cover a via exposed inside a component mask opening. Requiring Type VII for all vias removes ambiguity over this set and future CAM interpretation; supplier availability/cost is not yet approved.

Nine U2 exposed-pad via coordinates (all nominal Ø0.304 mm): Cartesian product X={34.0,35.2,36.4} and Y={27.4,28.6,29.8} mm.

## Stencil and assembly recipe

Use only freshly exported paste for the **47 fitted references**, with C20, MIC2, R9 and manual test pads omitted. Fitted-only paste still includes U2's unnumbered thermal windows and C13's separate aperture pads. There are 223 nominal fitted paste apertures. U2 has nine 0.925 × 0.925 mm windows on a 3.5 × 3.5 mm exposed pad: 62.86% nominal coverage. All nine thermal via bores are beneath these windows, which reinforces the fill/cap requirement.

A proposed starting recipe is an **80 µm laser-cut/electropolished stencil and Type 5 lead-free SAC305 paste**, subject to assembler approval of paste chemistry, shelf life, SPI volume, aperture adjustments, reflow profile and microphone cleaning restrictions. This is a candidate process, not a qualified recipe. TI limits the DRT stencil to 0.1016 mm; do not use a blanket 120–150 µm stencil at U4. If the assembler prefers 100 µm, the current aperture geometry has the following calculated release ratios.

| Aperture | Area ratio, 80 µm | Area ratio, 100 µm |
|---|---:|---:|
| U4 rounded 0.30 × 0.30 pad, minimum of all fitted apertures | 0.994 | 0.795 |
| C13 0201 aperture | 1.118 | 0.894 |
| U2 peripheral lead aperture | 1.442 | 1.154 |
| U2 thermal window | 2.891 | 2.313 |
| D2 aperture | 1.219 | 0.975 |

Ratio = opening area/(opening perimeter × stencil thickness), using native rounded polygons. These exceed the TI drawing's 0.66 area-ratio guidance; they do not predict paste volume or tombstoning by themselves. A 100 µm stencil is only 1.6 µm below the TI maximum, so its positive thickness tolerance also matters. [TI DRT stencil drawing](https://www.ti.com/lit/ds/symlink/tpd2eusb30a.pdf).

Plan factory SMT/reflow and hidden-joint X-ray rather than hand-soldering all fitted electronics. Inspect both sides, verify connector stake soldering, keep acoustic ports unobstructed, then current-limit first power and program/test each assembly. Battery/motor harness assembly occurs after the board electrical test.

## Actual board and drill geometry

| Feature | Native measurement |
|---|---|
| Board bounding box | 45.75 × 17.88 mm; X20.00..65.75, Y21.10..38.98 |
| Nominal thickness | 0.80 mm |
| Tracks / vias | 1,310 / 137 |
| Smallest routed trace width | 0.127 mm; USB main pair 0.135 mm |
| Via land/drill | 128 × (0.450/0.200 mm), 9 × (0.6096/0.304 mm) |
| Smallest nominal via annulus | 0.125 mm |
| Plated connector slots | 2 × 0.60 × 1.40 mm and 2 × 0.60 × 1.80 mm |
| Total drilled plated features | 141; no NPTH features |
| Normal copper-edge rule | 0.30 mm, with explicit J1-only edge-pad exception |
| Connector cutout | 9.24 mm wide, Y25.38..34.62, back edge X26.20 |

The empty NPTH output is not evidence that nonplated holes exist. Supplier drill compensation, cap plating, slot tolerances and router radii must preserve the connector drawing. GCT specifies the connector for a nominal 0.8 mm board; its layout tolerance is not an unambiguous finished laminate-thickness tolerance. Confirm connector compatibility with the supplier's finished thickness. [GCT USB4500 drawing](https://gct.co/connector/usb4500).

The current published JLC process supports these nominal multilayer trace/drill features, but its ordinary sub-1-mm thickness tolerance is ±0.10 mm and controlled-impedance tolerance ±10%. Published capability is not approval of this complete job, its fill/cap process or delivery date. [JLC current capability table](https://jlcpcb.com/capabilities/pcb-capabilities).

## USB stackup and actual reference plane

The main USB route is **B.Cu over actual filled In2.Cu GND**, not B.Cu over In1.Cu. The named In2 keepout forbids signal tracks while allowing ground-zone fill; it protects the reference plane. Independently re-intersecting the current native saved copper gives zero missing In2 GND projection along D+ 33.742994 mm and D− 33.738732 mm in the x29.6..62.2 mm corridor.

Native stack, top to bottom in mm: F.Cu 0.035 / prepreg 0.0994 / In1 0.0152 / core 0.5000 / In2 0.0152 / prepreg 0.0994 / B.Cu 0.035. The prepregs are JLC04081H-3313, 3313 RC57%, nominal Dk4.1; core is NP-155F, nominal Dk4.48. Copper-plus-dielectric sum is 0.7992 mm. Soldermask display layers are separate; this arithmetic is not a thickness measurement. Actual main-pair reference dielectric height is **0.0994 mm**. [JLC published stackups](https://jlcpcb.com/impedance).

The prior live calculator receipt recorded 90 Ω with width0.1349/gap0.1501 mm for coplanar differential over L2 with side ground0.300 mm; its noncoplanar result was width0.1356/gap0.1501. Current width0.135/gap0.150 follows that model. Mirroring L1/L2 to B.Cu/In2 is a nominal engineering inference from the symmetric dielectric stack. The manufacturer's calculator uses effective etched/trapezoidal copper assumptions that differ from a literal rectangular 35 µm conductor, so the supplier must confirm the fabrication geometry. [Calculator guide](https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator).

**Manufacturing acceptance target: 90 Ω differential ±10% (81–99 Ω), approved actual stackup plus representative coupon/TDR and review of the actual channel's local discontinuities.** A coupon validates its representative trace/process; it does not independently certify connector, package, ESD or via discontinuities. The main run has a credible modeled basis for USB full speed. End-to-end functional reliability remains unmeasured.

Three ground-via annuli remain closer than the nominal 0.300 mm coplanar zone gap: (58.1813,33.6144) gap0.1355 mm; (30.0,31.3) gap0.2600; launch (28.71,29.96) gap0.1753. Connector duplicate-pin/ESD launches and MCU via antipads also have documented local return gaps. They are not represented by the uniform-line calculator. The supplier's field-solver/CAM review must consider them; do not describe the whole channel as uniformly verified 90 Ω. No new pair-corridor reroute was made during this assembly repair.

## Critical routes and release boundary

NAND and PDM retain mixed layers and local reference gaps; the saved geometry confirms connectivity but not crosstalk margins. The direct MIC1–R8 branch remains 3.470 mm without vias. The PMIC switching interconnects and antenna keepouts are unchanged. The current E1 firmware configuration's generic SPI device maximum is 8 MHz; this does not prove implemented four-bit QSPI storage or reliable offline retention. Those firmware/physical acceptance tasks remain separate.

Minimum physical checks before treating assemblies as working customer units: supply shorts and rails, current-limited boot, PMIC configuration and safe charging with the selected pack, programmer access, microphone audio and phone decoding, BLE streaming/reconnect, USB enumeration and sustained error-checked transfers, NAND recovery/offline backfill, indicator/motor, assembled-case RF/acoustics and measured runtime/temperature. CAD DRC cannot replace these tests.

## Evidence and reproduction

- `U4_Geometry_Freeze_Receipt.json`: only local copper/placement delta, all-net and ground-region checks.
- `u4_trial_gui_drc.rpt`, `u4_trial_verification/native_drc.json`: native filled-board checks.
- `final_finish_drc.json`: final metadata/mask/via-attribute native all-track DRC + schematic parity.
- `negative_courtyard_body_screen.json`, `corrected_U4_body_clearance.json`: every scoped exception against maximum body geometry.
- `native_manufacturing_geometry.json`, `all_vias_fitted_smt_intersection.json`, `All_137_Vias_Mandatory_Type_VII.csv`: pads, apertures, drills and all-via process list.
- `stencil_area_ratios.json`: every fitted aperture release calculation.
- `USB_actual_reference_confirmation.json`: direct filled-In2 reference confirmation.
- Prior model receipt: `outputs/Anticipy_E1P1_Routing_Closure_2026-09-08/E1P1_Routed_Prototype/research/supplier_source_receipt.json`; route limits: that package's `pcb/verification/Routing_Closure_Review.md`.

All dimensions are millimetres unless stated. This is a CAD/process engineering audit with two physical-layout/process improvements; it is not manufacturing acceptance or product qualification.
