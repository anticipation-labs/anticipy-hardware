# Anticipy v1.0 mechanical CAD audit

> **Superseded correction audit:** this report found the PTS841, motor-pocket,
> aluminum-drawing and regression-test problems in the earlier v1.0 candidate.
> Those P0 digital corrections were applied afterward. Read
> `MECHANICAL_V10_REAUDIT.md` for the current state; the physical/DFM gates in
> this report still apply.

Date: 2026-08-29  
Controlling package: `release_v10/Anticipy_Execution_v1.0/02_PRODUCTION_CAD`  
Audited source: `generate_cad_v10.py`  
Audited assembly: `production_full_assembly.step`

## Release decision

**Mechanical release remains HOLD.** The regenerated v1.0 assembly is a valid, collision-free exact-size CAD candidate, and the Raytac module plus 27 mm controlled battery envelope fit the stated v1.0 layout. It is not yet a production-releasable fit package because:

1. the PTS841 is modeled with its 3.60 and 3.50 mm axes swapped relative to the side-actuation direction and omits the 4.85 mm terminal span, 5.20 mm land span, and 1.45 mm maximum height;
2. the VC0720B015F pocket is line-to-line at the motor's published maximum diameter and several retention features are only 0.10-0.15 mm thick;
3. the battery-to-motor nominal gap falls to about 0.05 mm after only motor maximum diameter and permitted cradle movement are applied;
4. the aluminum manufacturing PDF depicts the full 50.5 x 20.5 body rather than the actual 38.425 x 20.0 mm aluminum blank exported in DXF; and
5. min/nom/max closure, PCB preload, motor, cap-flushness, molding, and adhesive stacks are not released.

The design is suitable for an EVT/DFM handoff after the corrections below. Do not call it drop-proof, rattle-free, sealed, or production-ready until physical units pass the existing qualification plan.

## Independent digital results

| Check | Independent result | Verdict |
|---|---:|---|
| Generator | 21/21 checks pass from a clean copied run | Pass, subject to gate blind spots below |
| Full-package verifier | 10/10 package checks pass; fabrication remains HOLD | Pass |
| Factory skeleton verifier | 9 references valid; 22 blockers remain explicit | Pass/HOLD |
| STEP import | 16 valid BRep solids | Pass |
| STEP AABB | **50.500 x 20.680 x 10.800 mm** | Pass |
| Hard-limit nominal headroom | **0.500 x 0.320 x 0.200 mm** vs 51 x 21 x 11 | Pass |
| Headroom after the source's +0.15 mm finished-size tolerance | **0.350 x 0.170 x 0.050 mm** | Pass, very tight in Z |
| STEP pairwise Boolean common | No positive-volume intersections | Pass |
| Exact contacts | chassis-PCB, chassis-motor, PCB-mounted packages, plunger-boot | Tolerance-sensitive, not a physical proof |
| Enclosure meshes | Watertight, one body each | Pass |
| DXF aluminum blank bounds | **38.425 x 20.000 mm**, X = -13.425 to 25.000 | Correct geometry |
| Aluminum PDF depiction | Full 50.5 x 20.5 body reference is drawn as the cap | Fail for vendor release |

The STEP nominal bounds are X `[-25.25, 25.25]`, Y `[-10.43, 10.25]`, and Z `[0, 10.8]`. The one-sided 0.18 mm button boot sets the 20.68 mm width. On a centered 21 mm width datum it leaves only 0.07 mm on the boot side, although total nominal width headroom is 0.32 mm.

The `+0.15 mm` rule must be specified as a tolerance on each **finished overall dimension**, not as +/-0.15 mm on each surface. A per-surface interpretation can add 0.30 mm and would invalidate the depth budget.

## Replacement-envelope verdicts

| Replacement | v1.0 modeled result | 15% result | Production verdict |
|---|---|---|---|
| Raytac AN54LV-15, 8.4 x 6.4 x 1.5 | Module center `(-15.40, 0.00, 8.70)`; nominal X `-19.60..-11.20`, Y `-3.20..3.20` | Expanded X `-20.23..-10.57`, Y `-3.68..3.68`; shaped-PCB pass with a minimum 0.07 mm residual | **Envelope pass.** RF still needs exact copper/metal keepout DRC, Raytac review, and VNA test |
| Raytac antenna/no-ground region, 2.9 x 6.4 | Center `(-18.15, 0, 8.85)` correctly maps the left 2.9 mm end of the module | Nominal gap to aluminum start is 3.275 mm; 15%-expanded keepout gap is 3.058 mm | **Mechanical keepout pass**, but replace the hard-coded RF gate with geometry intersection |
| PTS841, 3.6 x 3.5 x 1.25 nominal | Source uses `[3.60 X, 3.50 Y, 1.25 Z]` while the plunger acts along Y | This swapped box passes by 0.0375 mm. Correct `[3.50 X, 3.60 Y]` at the same center protrudes 0.020 mm beyond the PCB after expansion | **Fail as modeled.** Correct axis mapping and use terminal/height/land envelopes |
| Vybronics VC0720B015F, nominal dia. 7 x 2 | Nominal motor and assembly position match | Cavity pass; R4.10 PCB scallop exceeds 1.15 x nominal radius by only 0.075 mm | **Nominal pass, tolerance/retention fail.** Published max is dia. 7.1 x 2.1 mm |
| LP571225, nominal 25 x 12 x 5.7 | Bare cell sits inside controlled `27 x 12.5 x 6.0` pack; cradle ID is 27.4 x 12.9 | Controlled pack individually passes the cavity's 15% XY test | **Pass conditional on a signed protected-pack drawing** covering PCM, leads, NTC, insulation, and aged maximum |

### What “15% reserve” actually means here

The generator expands modeled XY footprints about their centers by 1.15 for cavity containment, board containment, and nominal-Z same-layer courtyard checks. It does **not**:

- create 15% physical free play in cradles or pockets;
- expand Z heights;
- prove pairwise separation between battery and motor when their nominal Z bands do not overlap; or
- replace supplier min/max dimensions, placement tolerances, PCB fabrication tolerances, molding shrink, PSA thickness, or battery swelling limits.

That interpretation is reasonable for early layout planning, but the report should say “15% XY planning/courtyard reserve” rather than imply a complete 15% tolerance stack.

## Required CAD and generator corrections

### P0 — correct before the next STEP is called v1.0 production CAD

#### 1. Model the PTS841 in its actual side-actuation orientation

In `generate_cad_v10.py`, replace the nominal body mapping with:

```python
BUTTON = {
    "name": "Littelfuse C&K PTS841GMSMTRLFS side-push switch",
    "size": [3.50, 3.60, 1.25],   # X transverse, Y actuation axis
    "center": [0.00, -4.85, 8.825],
}
```

Add separate validation-only envelopes anchored to the PCB underside at Z = 9.45 mm:

```python
BUTTON_MAX = {
    "size": [4.85, 3.60, 1.45],  # terminal span, body/actuation length, max height
    "center": [0.00, -4.85, 8.725],
}
BUTTON_LAND_X = 5.20
BUTTON_TRAVEL_MIN, BUTTON_TRAVEL_NOM, BUTTON_TRAVEL_MAX = 0.10, 0.20, 0.30
```

Use `BUTTON_MAX`, not the nominal body, in 3-D and 15%-expanded component-collision gates. Add a separate PCB land/courtyard gate using the 5.20 mm manufacturer land span.

At Y = -4.85, the correctly oriented 15%-expanded body ends at Y = -6.92 and retains 0.08 mm to the 14 mm board edge. To preserve the source's intended 0.20 mm rest gap while keeping the outside end of the shaft at Y = -10.25, change the shaft to:

```python
button_shaft = cq.Workplane("XY").box(2.20, 3.40, 0.85).translate(
    (0.0, -8.55, 8.825)
)
```

Keep the flange/head/boot datums fixed to the wall. Then validate the actuator datum from the C&K 3-D model and real samples; a body bounding-box edge is not a substitute for a force/travel stack.

The 15%-expanded 4.85 mm terminal envelope overlaps the current haptic-driver reserve at X = 4.80 by 0.6394 mm2. The 5.20 mm land envelope is more conservative. Move:

```python
HAPTIC_DRIVER["center"][0] = 5.25
```

At X = 5.25, the 15%-expanded 5.20 mm land envelope retains 0.075 mm to the expanded driver reserve. Re-run the routed-PCB courtyard/land DRC with actual packages before release.

#### 2. Add VC0720B015F maximum and assembly envelopes

The supplier drawing gives dia. `7.0 +/-0.1 mm`, thickness `2.0 +/-0.1 mm`, leads `12 +/-2 mm`, strip `1.5 +/-0.5 mm`, and an approximately dia. 6 x 0.05 mm supplied adhesive disc. Add:

```python
MOTOR_MAX = {
    "size": [7.10, 7.10, 2.10],
    "center": [motor_x, motor_y, 7.25 + 2.10 / 2],  # bottom datum retained
}
MOTOR_SCALLOP_R = 4.30
```

R4.10 leaves only 0.0175 mm radial clearance beyond `1.15 x` the maximum 3.55 mm radius. R4.30 leaves 0.2175 mm.

The current pocket inner diameter is 7.10 mm, exactly equal to the maximum can diameter: zero assembly clearance. Use a released inner datum of at least dia. 7.20 mm; dia. 7.30 mm is a better starting target before molder tolerance review. Do not keep the current 0.10 mm annular wall. Replace it with drafted discrete lugs located away from the battery and chain boss, with at least 0.6-0.8 mm printable/toolable section.

Increase the motor shelf/bridge from 0.15 mm to at least 0.60 mm and the 0.10 mm keeper lips to at least 0.40 mm in Z, then redesign their flex length and root radii rather than simply thickening the existing short tabs. Keep the 0.05 mm motor PSA as a controlled die-cut, secondary to rigid retention.

Rename `fpc_exit` to a wire exit and model the full `14 mm` maximum lead reach, bend radius, channel, strain-relief point, and solder/connector termination. The selected motor is wired, not FPC.

#### 3. Restore a worst-case battery-to-motor clearance

Current nominal pack-to-can XY gap is 0.300 mm. With the maximum motor radius it is 0.250 mm. If the 27 mm maximum pack uses the cradle's 0.20 mm rightward clearance, only about **0.050 mm** remains before molding/placement tolerance.

A minimally disruptive starting coordinate is:

```python
MOTOR["center"] = [17.15, -4.90, 8.25]
```

This raises the simple worst-case gap above to about 0.300 mm, while a 1.15-expanded nominal motor still fits the cavity with about 0.074 mm residual and the present R3.65 pocket outer radius remains about 0.144 mm from the chain-boss outer radius. These are still small; use them only as a starting point for a signed tolerance stack and re-run exact chassis Booleans after the lug/shelf redesign.

Do not shrink the 27 x 12.5 x 6.0 controlled battery envelope back to the nominal pouch body. The battery change in v1.0 is correct.

### P1 — manufacturing and closure corrections

#### 4. Correct the aluminum drawing

`production_aluminum_cap_outline.dxf` has the correct aluminum blank bounds: X `-13.425..25.000`, Y `-10..10`, or **38.425 x 20.000 mm**. `production_aluminum_cap_drawing.pdf` instead draws and dimensions the full **50.5 x 20.5 mm body** and can be mistaken for a full metal face, despite the RF split.

Regenerate the PDF from `al_cap` itself. Show:

- the 38.425 x 20.000 aluminum blank as the controlled outline;
- the X = -13.425 cut edge;
- the 0.15 mm seam and separate polymer RF cap;
- the chain-hole location relative to aluminum datums;
- edge break, flatness, grain direction, anodize class, masked/qualified bond surface, and dedicated profile/flushness tolerances.

Keep the full body only as a phantom/reference outline.

#### 5. Release a real cap registration and flushness stack

The design has a useful 0.25 mm radial profile inset, polymer perimeter rim, 1.15 mm bond land, 0.15 mm VHB, and continuous chassis underlap. However, the aluminum face is only 0.05 mm behind the polymer front plane while the preliminary cap drawing calls out +/-0.10 mm general profile tolerance. That does not guarantee the polymer remains proud in worst case.

Either:

- increase nominal face recess to at least 0.15-0.20 mm and re-stack the battery/motor/PCB Z positions; or
- keep the 0.05 mm nominal only with a dedicated, much tighter cap-seat/PSA/flatness tolerance that guarantees a positive polymer proud condition.

Add molded registration keys or a stepped shear datum at the aluminum and RF-cap split. The current flat VHB bond and 0.05 mm perimeter running clearance do not alone prove impact registration or cosmetic seam control.

#### 6. Replace sub-process-thickness retention details

Current critical sections include a 0.10 mm motor wall, 0.10 mm motor keepers, 0.12 mm PCB hooks, 0.15 mm motor shelf/bridge, 0.20 mm end stops, and 0.35 mm snap stems/bridges. These are concept geometry, not robust Bambu, PA12, or injection-molded features.

For the next DFM model, use these starting minima before supplier review:

| Feature class | PLA Silk+ / 0.4 mm nozzle starting minimum | PA12 MJF/SLS starting minimum | Molded PC starting minimum |
|---|---:|---:|---:|
| freestanding wall/rib | 0.8 mm | 0.8 mm | 0.6-0.8 mm plus draft |
| horizontal shelf/web | 0.6 mm | 0.6-0.8 mm | 0.6-0.8 mm with radiused root |
| snap/keeper thickness | 0.6 mm with useful flex length | 0.8 mm, supplier reviewed | strain-derived; typically >=0.6 mm with root radius |
| tiny Z feature | >=0.36 mm at 0.12 mm layers | >=0.5 mm | tool/process dependent |

These are starting values, not material allowables. Run snap strain, knit-line, sink, warpage, and mold-flow review on the final PC design.

### P2 — generator/report hygiene

1. Remove stale v0.6 gauges from the v1.0 CAD directory:
   - `production_dummy_battery_26x12.5x6.step/.stl`
   - `production_dummy_radio_6.3x7.9x1.75.step/.stl`
2. Replace the hard-coded old RF rectangle in `production_internal_layout.png` with `ANTENNA_KEEP`; the image currently shows a 6.5 x 6.5 region.
3. Move the hard-coded `radio` label from `(-10.6, 2.3)` to the current module center.
4. Update the button comment that still names `SKSCLCE010`.
5. Replace the RF test `if al_start < -15.0` with exact intersection/distance against the AN54 antenna/no-ground polygon and a named minimum-metal-clearance requirement.
6. Update the RF PASS text; it still says `6.5 x 6.5 mm` and refers to a separate feed/antenna that v1.0 removed.
7. Add a STEP regression gate for 16 solids, exact AABB, valid solids, and zero positive-volume pair intersections so the exported assembly—not only source primitives—is verified.

## Closure, rattle, and drop assessment

Positive concepts are present: a battery cradle and pull-tab path, motor shelf/pocket/keepers, PCB ledges/locators/snaps, a captive plunger and boot, an impact rim, continuous bond land, and a chain boss. Exact STEP Booleans show no solid collision.

The same STEP also has intended zero-distance contacts at chassis-PCB, chassis-motor, all PCB-mounted packages, and plunger-boot. Those interfaces require min/nom/max compression and clearance drawings. Without them, a manufactured unit can alternate between squeeze, rattle, and non-contact even though nominal CAD is collision-free.

Release evidence still required:

- PCB datum and gasket compression stack including 0.6 mm board warp/tolerance;
- battery pack maximum-in-service and swelling clearance, with teardown after drop/vibration;
- motor can/PSA/pocket/keeper/wire tolerance and 50,000-cycle haptic test;
- button membrane/preload/travel/over-travel/force stack and 100,000 presses;
- cap VHB die-cut, surface preparation, press fixture, dwell, seam, peel/shear, sweat, and temperature cycling;
- 1.2 m multi-orientation drop, shock, vibration, tumble, rattle-turner, and destructive sample inspection;
- chain pull/abrasion with the actual chain and breakaway hardware.

## Print and production route

### Bambu P2S with PLA Silk+

The 50.5 x 20.68 x 10.8 mm parts are far inside the P2S 256 mm cubic build volume. The primary shell meshes are watertight. The current fine retention geometry is not reliably reproduced with a stock 0.4 mm nozzle: 0.10-0.15 mm walls/webs are below one extrusion width and at or below one 0.12-0.20 mm layer.

Use PLA Silk+ only for appearance/hand-feel and early envelope trials unless the thin features are redesigned to the minima above. Print at 100% scale, cavity up, with Arachne, 0.12 mm layers, at least three wall loops, and inspect the slice around every keeper, snap, chain eye, and button opening. The 0.18 mm button-boot STL is an LSR envelope, not a printable watertight seal. A tougher non-silk PLA is preferable for functional closure/drop coupons because silk formulations generally trade appearance for mechanical consistency.

### PA12 plus aluminum

PA12 MJF/SLS is appropriate for bridge prototypes and low-volume DFM samples after thin-feature redesign. It is not a drop-in production substitute for Makrolon 2407: porosity, moisture uptake, surface roughness, sweat sealing, dimensional drift, and VHB adhesion need finishing and coupons.

The preferred scale route remains:

1. injection-molded Makrolon 2407 chassis/RF structure with draft, radii, uniform walls, and toolable retention;
2. laser/chemically cut or stamped 0.8 mm 5052-H32 aluminum face using the corrected 38.425 x 20.0 outline;
3. deburr, grain, clear anodize, and protect/qualify the bond surface;
4. die-cut 0.15 mm VHB 5906F in a controlled continuous ring;
5. fixture-controlled alignment/pressure/dwell, then seam, pull, rattle, drop, sweat, and temperature validation.

## Evidence and commands

- Clean copied generator run: `python generate_cad_v10.py` -> 21/21 PASS.
- Package verifier: `python verify_package.py` -> 10/10 PASS, fabrication HOLD.
- Factory verifier: `python validate_factory_release.py` -> structural PASS, 22 release blockers.
- Independent CadQuery/OpenCascade import: 16 valid solids, exact 50.500 x 20.680 x 10.800 mm AABB, zero positive-volume pairwise intersections.
- Independent Shapely checks quantified AN54, PTS841, microphone, antenna-metal, battery, and motor margins above.
- Visual inspection: `production_internal_layout.png` and rendered `production_aluminum_cap_drawing.pdf`.

Primary component sources used for tolerance interpretation:

- Raytac AN54LV-15 product/specification and official footprint guide: <https://www.raytac.com/product/ins.php?index_id=169>
- Littelfuse/C&K PTS841 datasheet: local evidence `work/littelfuse_pts841/PTS841_datasheet.pdf`
- Vybronics VC0720B015F product and drawing: <https://www.vybronics.com/coin-vibration-motors/with-brushes/v-c0720b015f>
- Bambu P2S specifications: <https://bambulab.com/en/p2s/specs>
- Bambu silk-filament guidance: <https://wiki.bambulab.com/en/x1/manual/printing-with-silk-filaments>

## Bottom line

The 51 x 21 x 11 mm goal survives the v1.0 replacements. AN54LV-15 and the 27 mm controlled battery envelope fit without growing the exterior. The present STEP is internally consistent and collision-free. The PTS841 model and motor tolerance/retention geometry are the two real CAD blockers; correct them, fix the vendor aluminum drawing, replace sub-process-thickness details, then regenerate and repeat the exact STEP/15%/tolerance audit before EVT release.
