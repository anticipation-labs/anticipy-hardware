# Smooth oval E1 — mechanical fit candidate

The selected shape is **56 × 35 × 14.8 mm nominal**, with a curved crown, rounded edges and rear-only recessed screws. It contains the existing E1 circuit and the selected protected battery candidate. **It does not meet the 30 × 14 × 8 mm target.** It is shorter and slightly thinner than the old enclosure, but wider. This is a checked prototype geometry, not a manufacturing release or a qualified wearable.

This regeneration updates the actual assembled U4 position and displays the selected C23 maximum body (2.20 × 1.45 × 1.45 mm), plus the selected TDK 0402 and TI USB-protector maximum envelopes. Their fit checks include an extra 0.20 mm per XY side and above the maximum body.

## What is inside

- Native E1 PCB: **45.75 × 17.88 × 0.8 mm**, final released component positions, including U4 at native X28.15/Y29.45. Native source SHA-256: `78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36`.
- Jauch **LP561836JU+PCM+2 WIRES50MM** protected pack: **350 mAh minimum / 370 mAh typical**, complete maximum body **38.5 × 18.5 × 6.0 mm after cycling**. Capacity is not a demonstrated 16-hour runtime. [Manufacturer drawing](https://www.jauch.com/downloadfile/5bf529acf2902e0e6585a358571c3a4c8/350mah_-_lp561836ju_1s1p_2_wire_50mm.pdf).
- Existing 10 mm haptic motor, inside a **10.6 mm diameter × 2.7 mm installation gauge**; a separate thermistor attachment gauge; battery, motor and thermistor wiring.
- The actual USB-C connector (charging disabled in the current firmware), top-port microphone, LED and switch stay at their PCB locations. This is not a different charging-contact architecture.

The pack installation volume adds 0.35 mm per side and 0.05 mm at its top/bottom. The nominal pack bottom is Z1.50 mm, its installation guard starts at Z1.45 mm, and the floor ends at Z1.20 mm. The resulting 0.25 mm floor gap supports a procurement ceiling of **0.20 mm compressed thickness** for removable electrically insulating retention adhesive, leaving 0.05 mm to the guard. Select and physically test the actual adhesive and pack seating process; the gap is not a qualified adhesive specification. Its metal body stays outside the native antenna exclusion rectangle. This does not prove RF performance with the wearer, shell, finish or chain.

## Dimensions and why it is this size

The battery, motor and antenna exclusion determine the width. A bounded screen tested **2,450** combinations of length, width, battery position and body center before the full CAD check. Widths 32–34.5 mm did not pass that particular screen with these clearances and this smooth-oval profile. **This is not proof of the worldwide smallest possible design.** A smaller PCB/radio or different cell/motor arrangement would be a new design exercise.

The old main body was 60 × 26 × 15 mm; its full modeled assembly reached 64.3 × 26 × 15.5 mm. Its battery was only an unselected 27 × 12.5 × 6 mm gauge. The new real protected pack is substantially larger. Filled exterior volumes are approximately 23.06 cm³ old and 24.34 cm³ new (about **5.5% more**), excluding small attachment/button projections; these are not plastic-material volumes. Those comparisons belong to the archived oval feasibility package; this handoff regenerates its same shell geometry against the final PCB.

## Fit and closure

`Oval_E1_Checks.json` records **2,826 passing geometric checks with zero failures**, including component allowances, all routed harness gauges, native solder pads, PCB guides, shell clearances, microphone passage, antenna metal exclusion and the button travel envelope. All four printable/optical parts are single valid solids. Exact intended wire-terminal joins and the microphone foam compression allowance are named explicitly; there is no general collision exemption.

- PCB underside: Z = 9.1 mm; top: 9.9 mm. Four rear support arms carry it. A guide follows its actual outline with **0.35 mm side clearance**; four upper compliant pads restrain vertical movement.
- Rear fasteners: **two M2 × 4 mm underhead screws**, maximum head **4.0 mm diameter × 1.3 mm height**. Heads sit in 4.4 mm recesses. The 1.6 mm pilot holes require an M2 tap or a supplier-approved threaded process in 5.6 mm polymer pillars. No screw SKU, torque or pullout life is yet qualified.
- Maximum screw-tip Z is 5.35 mm: **3.75 mm below the PCB underside**. Smallest screw-to-pack installation clearance is **1.60 mm**; closest screw-to-expanded-component clearance is **2.37 mm**. See `Oval_Mechanical_Details.json`.
- The actual USB-C mouth is **3.7 mm behind the nominal short-end center surface**. The 11.4 × 7.1 mm passage clears the declared 10.8 × 6.5 mm cable-overmould gauge. A larger real cable may not fit.
- A 2 mm bore reaches from the short-end exterior to the internal textile-knot gauge. Thread and knot the cord before closing; the removable external loop is not modeled or included in body dimensions. Cord retention and pullout are unqualified.
- The microphone bore is 1.2 mm at native X46.3/Y23.12. The 0.4 mm free foam gasket reserves up to 0.2 mm compression for the extra microphone mounting-height allowance. Acoustic response and leak sealing need a physical test.
- The button has a 4 mm retaining collar and 1.4 mm contact nose. The tested 0.50 mm motion includes 0.30 mm nominal free travel plus a **provisional** 0.20 mm switch-actuation allowance. Verify the exact switch stroke/force before manufacturing.
- The lightpipe has an internal collar and an adhesive annulus. Its optical material, adhesive and surface finish remain to be selected. This is not waterproof construction.

## Harness and assembly

Battery leads use a **1.2 mm outside-diameter / 2 mm centerline-bend-radius** routing gauge. Motor leads use 0.5 mm / 1 mm; sensor leads use 0.5 mm / 0.75 mm. These are explicit planning dimensions, not supplier guarantees. The battery drawing specifies 50 ± 5 mm AWG26 leads but does not dimension exit coordinates, insulation diameter or bend radius. The assembly shop must confirm these gauges, trim insulated factory leads to the approved lengths, and provide strain relief; **do not modify the cell tabs or protection board**. The specified TDK B57540G1103F000 glass bead is 0.8 mm maximum diameter × 1.4 mm maximum length. Its insulated attachment gauge is **2 × 1.4 × 1.0 mm**. Each lead stays straight for at least **4.7 mm from the glass end** before a bend of at least **0.75 mm radius**, exceeding the drawing’s 4.3 mm no-bend distance. Validate the final insulation/tape process and thermal contact. [TDK drawing](https://product.tdk.com/system/files/dam/doc/product/sensor/ntc/ntc_element/data_sheet/50/db/ntc/ntc_glass_enc_sensors_g1540.pdf).

1. Obtain professionally assembled and electrically tested E1 PCBA; program and verify it while access is open.
2. Fit the lightpipe and its retaining adhesive, button and microphone gasket to the front shell. Fit the upper PCB capture pads.
3. Place the protected pack and motor in the rear cavity using supplier-approved removable electrically insulating adhesive no thicker than 0.20 mm compressed beneath the battery. Validate the motor attachment separately within its mounting guard. Attach the NTC to the broad cell face; preserve the documented insulation and routing space.
4. Terminate the six wires at **BT1 battery, M1 motor and TH1 thermistor** pads with the polarity from the electrical schematic. Inspect and electrically test the joints before closing.
5. Seat the PCB on the four supports, within its guide. Verify that no wire is pinched. Lower the front shell; confirm microphone-gasket engagement and button return. Install the two recessed screws with a tested torque.
6. Run charging-temperature, recording, storage/backfill, BLE, microphone, LED, haptic, button, drop and runtime tests. Passing CAD checks does not replace these tests.

## Files to use

- `Oval_E1_Assembly_FIT_CANDIDATE.step`: actual assembled coordinates, component envelopes and all modeled mechanical parts.
- `Oval_E1_Exploded_VIEW_ONLY.step`: separated presentation positions only; never use this file as an assembly datum.
- `Front_Oval_Shell.step`, `Rear_Service_Cover.step`, `Button_Plunger.step`: editable individual print parts; matching STL files are provided.
- `Oval_E1_Three_Print_Parts_GEOMETRY_ONLY.3mf`: the three opaque parts arranged separately in millimetres. **No printer, material or support settings are embedded.**
- `Clear_Lightpipe.step` / `.stl`: separate optical part, requiring clear material; not included with the opaque parts in the 3MF.
- `Oval_E1_Port_and_Controls.png`, `Oval_E1_Exploded_Labeled.png`: annotated actual-CAD views.
- `CAD_Rebuild_Receipt.json`, `CAD_File_Manifest.json`, `Lightpipe_Export_Checks.json`: input hash linkage, regenerated STEP validity, output hashes and the separate optical mesh check.
- `Print_Export_Checks.json`: STEP reimport, one-solid checks, watertight meshes and sampled mesh-to-CAD surface deviations. Only zero-area triangles at surface poles are removed; no holes or features are invented.

For a fit print use **unfilled nonconductive polymer**. Gold in the render is display color, not an approved paint or metal coating. A print shop must choose orientation and removable supports for the curved shell and internal guides; do not print the whole assembly STEP. The rear cover can rest on its flat exterior. The front needs support/orientation review, and small pilots/ports may require measured finishing. Print one fit coupon/unit before a batch. CNC machining is not yet reviewed for access to all internal ribs and retention features.

The bundled contract is locked to the final PCB SHA above. Keep the immutable PCB release beside this handoff, or provide its `pcb/` directory alongside `cad/`. Rebuild with Python 3.12, CadQuery 2.6.x, NumPy, Matplotlib, Shapely and trimesh:

```sh
python cad/build_oval_e1.py
python cad/package_print_parts.py
python cad/render_details.py
python cad/validate_cad_handoff.py
```

The builder does not modify the native PCB. Supplier tolerances, battery charging/thermal behavior, RF, acoustic response, fastener life, adhesive retention and end-to-end firmware behavior remain release gates.
