# Anticipy v1.0 mechanical re-audit

Date: 2026-08-29  
Audited package: `release_v10/Anticipy_Execution_v1.0/02_PRODUCTION_CAD`  
Scope: independent regeneration, STEP/BRep audit, collision checks, PTS841/motor corrections, aluminum drawing, and thin-feature review.

## Decision

**The updated model is a valid exact-size EVT/DFM mechanical candidate. It is still HOLD for factory tooling or a claim of rattle-free/drop-qualified production.**

The prior PTS841 orientation/envelope error, motor maximum envelope, motor pocket/shelf/keeper starting geometry, battery-to-motor planning gap, aluminum-cap depiction, and exported-STEP regression gate are corrected. The remaining mechanical blockers are the still-subscale PCB/cradle retention details, unclosed min/nom/max tolerance stacks, and physical qualification.

## Independent results

- Ran `generate_cad_v10.py` in a new temporary directory: **23/23 gates passed**.
- The regenerated primary STL bounds, volumes, and face counts exactly match the package outputs.
- Imported `production_full_assembly.step` independently with OpenCascade: **16/16 valid BRep solids**.
- Exact finished STEP AABB: **50.500 x 20.680 x 10.800 mm**.
- Nominal headroom to 51 x 21 x 11 mm: **0.500 x 0.320 x 0.200 mm**.
- Headroom after the source's one-sided `+0.15 mm per finished dimension` rule: **0.350 x 0.170 x 0.050 mm**. Z is therefore very tight.
- Pairwise exact Boolean audit: **zero positive-volume solid intersections**.
- All seven released enclosure/button meshes are watertight and one connected body each.

The STEP contains the expected physical envelopes:

| Solid | Independently measured STEP bounds |
|---|---:|
| Chassis | 50.500 x 20.500 x 10.800 mm |
| Aluminum cap | 38.425 x 20.000 x 0.800 mm |
| Polymer RF cap | 11.425 x 20.000 x 0.800 mm |
| Placement PCB | 37.500 x 14.000 x 0.600 mm |
| Controlled battery pack | 27.000 x 12.500 x 6.000 mm |
| AN54LV-15 module | 8.400 x 6.400 x 1.500 mm |
| PTS841 nominal body | 3.500 X x 3.600 Y x 1.250 Z mm |
| VC0720 maximum can | 7.100 diameter x 2.100 mm |

## Prior-issue closure

### 1. PTS841 axes, maximum body, and land: corrected

- The placed nominal body is now `3.50 X x 3.60 Y x 1.25 Z`, with Y as the side-actuation direction.
- Validation uses a separate `4.85 x 3.60 x 1.45 mm` terminal/body/maximum-height envelope.
- Validation also uses a separate `5.20 x 3.60 mm` PCB land-span envelope.
- The 15%-expanded maximum and land envelopes stay on the shaped PCB with **0.080 mm** residual to its Y edge.
- The 15%-expanded land envelope clears the shifted haptic-driver reserve by **0.075 mm**; no overlap remains.
- The captive shaft has the intended **0.20 mm nominal rest gap** to the modeled body edge.

This closes the former CAD error. Actual actuator datum, preload, force, travel (`0.2 +/-0.1 mm`), and over-travel still require a measured switch sample and a released tolerance stack.

### 2. Motor maximum, pocket, shelf, keeper, and battery gap: corrected as EVT starting geometry

- The assembly uses the published maximum can envelope, diameter **7.10 mm** x **2.10 mm**.
- Pocket ID is **7.30 mm**, giving **0.20 mm diametral / 0.10 mm radial** nominal clearance.
- Shelf and bridge are **0.60 mm** thick; pocket wall is **0.60 mm**; crash-stop keeper Z thickness is **0.40 mm**.
- PCB scallop R4.30 leaves **0.2175 mm** beyond `1.15 x` the maximum motor radius.
- Battery-to-maximum-can XY gap is **0.500 mm** nominal and **0.300 mm** after the complete modeled 0.20 mm cradle travel.
- The maximum can has zero positive-volume collision with the chassis and touches the crash-stop keeper at its top datum as intended.

This closes the former nominal CAD conflict. Mold shrink/tolerance, keeper strain, motor-wire routing/strain relief, PSA tolerance, and haptic-cycle qualification remain open. The 15%-expanded motor has only **0.0165 mm** residual to the nominal cavity boundary; that proves mathematical containment of the stated planning envelope, not extra manufacturing clearance beyond it.

### 3. Aluminum PDF: depiction corrected, manufacturing drawing still preliminary

The PDF and DXF now agree: the controlled aluminum blank is **38.425 x 20.000 mm**, X `-13.425..25.000`, with the full pendant shown only as a dashed reference. The PDF calls out the split datum, 0.15 mm seam, 0.80 mm 5052-H32 material, clear anodize, grain, VHB, and preliminary status.

Before vendor release it still needs a real drawing revision with chain-hole diameter/location datums, profile/flatness/flushness tolerances, edge-break limits, coating/anodize class, bond-face masking/qualification, and inspection criteria. The file correctly labels itself **PRELIMINARY**.

### 4. STEP regression: corrected

The generator now checks the exported STEP itself for:

- exactly 16 solids;
- exact 50.500 x 20.680 x 10.800 mm AABB; and
- zero pairwise positive-volume intersections.

An isolated rebuild reproduced those results and the same total solid volume.

### 5. Thin features: motor features improved, overall issue not fully closed

The motor shelf/wall/keepers were raised to useful starting dimensions. Several other molded retention features remain below the prior DFM starting minima:

| Remaining feature | Source thickness |
|---|---:|
| Battery cradle rails | 0.40 mm |
| Cradle-to-shell bridges | 0.35 mm Z |
| PCB ledges | 0.35 mm Z |
| PCB snap stems | 0.35 mm transverse |
| PCB snap hook | 0.12 mm Z |
| PCB end stops | 0.20 mm X |
| Acoustic annular boss | 0.14 mm Z |
| Button membrane model | 0.18 mm (LSR envelope only) |

These features survive the CAD Boolean and the STL is connected, but that is not a molding, PA12, or PLA Silk printability proof. The 0.12 mm hook in particular is below one stock 0.4 mm FDM extrusion and cannot be treated as functional in a PLA Silk print.

## Rattle/drop interpretation

The nominal STEP has no penetrating collisions, but several intended interfaces are exactly touching: chassis-to-PCB, chassis-to-motor keeper, every PCB-mounted package, and plunger-to-boot. The battery has modeled cradle free play and depends on controlled tape; the PCB depends on an unmodeled compressed gasket; the cap depends on an unmodeled VHB die-cut. Therefore the geometry is internally consistent, but it does **not** independently prove no rattle, no squeeze, seal performance, or drop survival.

Required closure evidence remains:

1. thicken/redesign the PCB hooks, ledges, end stops, cradle bridges/rails, and acoustic boss for the selected process;
2. release min/nom/max compression and clearance stacks for PCB gasket, battery tape/swelling, motor pocket/PSA/keepers, button boot/plunger/switch, and cap/VHB/flushness;
3. perform physical rattle, vibration, 1.2 m multi-face drop, chain pull, sweat, temperature, leak, and teardown tests;
4. obtain vendor DFM/mold-flow and a signed controlled battery-pack drawing.

## Package hygiene

The obsolete 26 mm battery and old 6.3 x 7.9 mm radio gauges identified during
the audit were removed before packaging. The only current gauges are the
**27 x 12.5 x 6 mm battery** and **AN54LV-15 8.4 x 6.4 x 1.5 mm radio** files.

## Bottom line

**Exact-size placement and nominal collision status: PASS.**  
**Good enough for EVT/DFM review: PASS.**  
**Good enough to promise rattle-free, drop-proof customer production: HOLD until the thin retention features, real tolerance stacks, vendor DFM, and physical tests close.**

Primary dimensional evidence: Littelfuse/C&K PTS841 datasheet in `07_SOURCES`; Raytac AN54LV-15 official product/design data at <https://www.raytac.com/product/ins.php?index_id=169>; Vybronics VC0720B015F official product/drawing at <https://www.vybronics.com/coin-vibration-motors/with-brushes/v-c0720b015f>.
