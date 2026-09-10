# Anticipy E1P1 - fabrication and assembly specification

Issue: 2026-09-09. Prototype PCB/PCBA release. Native PCB SHA-256: `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`.

## Bare board

| Item | Requirement |
|---|---|
| Outline | Exactly supplied Edge.Cuts/Gerber, 45.75 x 17.88 mm bounding dimensions; preserve the USB cutout and antenna area. Outline routing tolerance target +/-0.10 mm. Do not scale. |
| Layers | F.Cu / In1.Cu / In2.Cu / B.Cu, in that order. |
| Material / thickness | FR-4, 0.80 mm nominal finished board, +/-0.08 mm maximum; JLC04081H-3313 basis below. Equivalent laminate requires matching dielectric geometry and measured impedance, not just matching layer count. |
| Copper | Native nominal outer 35 um; inner 15.2 um. Supplier accounts for plating and etch trapezoid in its impedance model and returns the final stackup. |
| Finish | ENIG on exposed pads; lead-free assembly. Green soldermask both sides; white silkscreen. |
| Copper features | Minimum routed track 0.127 mm. Standard copper clearance rule 0.127 mm. Minimum nominal via annulus 0.125 mm. No copper geometry edits without a reviewed replacement data set. |
| Vias | ALL 137 plated vias: nonconductive epoxy fill, planarize and copper cap, IPC-4761 Type VII. 128 bores at 0.200 mm / 0.450 mm lands; 9 bores at 0.304 mm / 0.6096 mm lands. Native filling/capping flags enabled. See coordinate CSV. Mask tenting alone is not acceptable. |
| Connector slots | Four plated slots at J1: two 0.600 x 1.400 mm and two 0.600 x 1.800 mm. Keep open and plated; do NOT epoxy-fill. Nominal drill/rout tool dimensions are in Excellon. No NPTH holes are present. |
| Mask | Use supplied masks. U2 pins 1-32 and U4 pins 1-3 expand 0.050 mm; U2 nominal interlead mask dam 0.100 mm. Other native expansions are preserved. CAM must retain exposed solderable pads and check its registration capability; do not blindly expand all openings. |
| Edge exception | J1 uses an intentional board-edge/cutout connector land pattern. Do not repair it by moving the connector or shrinking its pads. |
| Inspection | 100% bare-board electrical test against supplied IPC-D-356/netlist, AOI, dimensional report and filled-via/cap quality inspection. Supply impedance coupon results and a representative microsection/cap-process record. |

Nominal dielectric construction, excluding the approximately 10 um soldermask coating on each face:

| Order | Layer/material | Thickness mm | Nominal relative permittivity |
|---|---|---:|---:|
| 1 | F.Cu | 0.0350 | - |
| 2 | 3313 RC57% prepreg | 0.0994 | 4.10 |
| 3 | In1.Cu | 0.0152 | - |
| 4 | NanYa NP-155F core | 0.5000 | 4.48 |
| 5 | In2.Cu | 0.0152 | - |
| 6 | 3313 RC57% prepreg | 0.0994 | 4.10 |
| 7 | B.Cu | 0.0350 | - |

The nominal laminate/copper sum is 0.7992 mm; soldermask/finished thickness tolerances belong in the returned stackup. Do not interpret 0.7992 mm as a measured finished thickness.

## USB impedance and reference copper

USB is the nRF52840 full-speed USB data pair. The main B.Cu paired corridor uses 0.135 mm traces / 0.150 mm nominal edge spacing and approximately 33.74 mm paired length. Its actual saved reference is **In2.Cu filled ground across 0.0994 mm prepreg**. The In2 corridor keepout prohibits signal tracks while allowing ground-zone fill. Preserve it.

Acceptance: **90 ohms differential +/-10% (81-99 ohms)** on a representative fabrication coupon at the actual supplier stackup. The recorded JLC calculator result for the symmetric outer-layer geometry was 0.1349 mm width, 0.1501 mm gap, 0.300 mm coplanar side-ground gap for 90 ohms. The native pair matches those nominal dimensions. That model uses an effective 1.6 mil copper/trapezoid assumption, which the manufacturer must reconcile with its finished copper and etch process. It is not a measured board result.

Preserve continuous In2 ground, nearby return vias, pair spacing, and the 0.300 mm B.Cu ground-zone separation rule. Local connector launches, vias and nearby ground-via perturbations are not uniform transmission lines and require CAM/field-solver review. No global autorouting or panel-tab placement near the antenna. Coupon acceptance does not replace assembled-board USB enumeration and waveform checks.

## SMT assembly

- Populate exactly `Machine_Assembly_BOM.csv`: **47 references, 44 top / 3 bottom**. Use exact MPNs. `Do_Not_Place.csv`: C20, MIC2, R9. Net ties and test pads are copper features, not bought components. External BT1/M1/TH1 are fitted after reflow.
- Use the supplied `gerbers/*Paste*` files (fitted parts only), also duplicated in `assembly_stencil_nominal/`. Do not derive a fresh unfiltered stencil from every native test pad.
- Starting stencil specification: **80 um laser-cut, electropolished stainless**, Type 5 SAC305 paste. Keep the existing apertures; no blanket shrink. U4 manufacturer maximum stencil thickness is 101.6 um. The smallest screened aperture area ratio is about 0.994 at 80 um; C13 is about 1.118.
- U2 exposed pad is 3.5 x 3.5 mm with nine 0.925 x 0.925 mm paste windows: 62.86% nominal area coverage. All underlying vias must be filled/capped before paste printing.
- Machine placement capability: target +/-0.05 mm per part for the closely spaced PMIC reference cell. Maximum-body checks include capacitor/resistor tolerances and U4 mold-flash allowance. The repaired U4/C1 static worst-body gap is approximately 0.375 mm before placement tolerance.
- The assembler determines the profiled two-sided reflow sequence within every component's permitted limits; keep the acoustic port, switch and USB contact cavity free of flux, cleaning fluid and debris. Do not apply ultrasonic cleaning or direct compressed air to the microphone. Protect the bottom-port microphone opening during final assembly without sealing it shut.
- Inspect paste with SPI and every board with AOI. X-ray U2/U5 concealed solder joints and filled-via interfaces on first articles; verify solder wetting, bridging and void acceptance to the agreed IPC-A-610 Class 2 workmanship standard. Inspect USB shell-slot soldering and connector alignment. Profile first articles before committing the remaining batch.
- Panelization belongs to the assembler: add support/rails/fiducials outside the final outline, preserve antenna keepouts and connector cutout, and use routed depaneling to limit MLCC bending. Deliver individual boards within the specified outline; no forced bending at the PMIC capacitors.

## External assembly and first power

J1 USB-C is the physical power/data port at the cutout end. The selected firmware leaves charging disabled; plugging it in is not evidence that battery charging is qualified.

| Part | Board connections | Installation |
|---|---|---|
| Jauch LP561836JU+PCM+2 WIRES 50MM | BT1.1 = VBAT positive; BT1.2 = GND negative | Use protected pack leads; verify polarity with a meter. No soldering directly to pouch foil or cell tabs. |
| VCLP1020B002L motor | M1.1 = 3V_MAIN; M1.2 = HAPTIC_NEG | Insulate and strain-relieve the harness; keep away from microphone and antenna. |
| B57540G1103F000 external 10k NTC | TH1.1 = NTC; TH1.2 = GND | Electrically insulate sensor/leads and thermally couple to cell; do not bypass. This is separate from the two-wire pack. |

First article sequence: inspect unpowered boards; check shorts and polarity; keep battery disconnected; apply current-limited 5 V at J1 using a USB bench source; establish the 3.0 V MAIN rail and expected PMIC behavior; connect a voltage-sensing SWD probe to the test pads; program only the E1P1 BUCK2-main bench image; verify readback and reset. Do not drive VTref as a second power supply. Keep the cell disconnected until rails, polarity and charging-disabled behavior are verified.

Before releasing assembled units: test power sequencing/current, microphone audio, BLE reconnect/audio, NAND identity/read/write/erase with proper firmware, USB both orientations/hot-plug/waveform quality, LED/button/motor, RF with final case, and battery/NTC/charging behavior. No physical test has been run by this file review. Bench firmware does not yet implement full offline storage or production updates. These are prototype manufacturing files, not a consumer-product qualification certificate.

Source basis: TI TPD2EUSB30A DRT drawing and data sheet; Nordic nPM1300 reference cell; selected manufacturers' capacitor drawings; saved native PCB geometry and supplier calculator receipt. Detailed evidence is in `pcb/verification/` in the full release.
