# Anticipy ordered-shell recovery v0.2

## Use this version

The first 4.00 mm recovery was withdrawn after an independent audit found
collisions with the historical body's internal shelf and the face hooks.
Version 0.2 fixes those problems and uses a **4.50 mm-rise mid-band**.

The corrected generator imports the packaged exact historical body and face
STEP solids. Its final report records **1,424** boolean intersection values
with a 0.0 mm3 maximum for:

- nominal and loose mid-bands against the body;
- the four-hook vertical drop at 13 positions and lock slide at 21 positions,
  against both bands and every modeled component/layout;
- XIAO, battery, motor, 8 x 4 x 2 mm driver, and safety bridge against body, band, face,
  and one another;
- 12, 15, 24, and 25 mm battery layouts with the sealed coin motor;
- a conditional DTP401525-class 25.3 x 15 x 4.0 mm layout with the driver
  rotated into the battery/motor gap;
- the full 11.29 x 4.03 mm swept barrel-motor measurement reference; it is not
  a Unit 001 fallback because no qualified rotor guard is included.
- the separate Renata-only M2 screw-retained band, keyed posts, full-height
  drill axes, and conservative countersink envelopes against the ordered body,
  face, components, and both antenna-window regions.

The screw-retention audit also requires a positive collision with Plan B's
rotated driver. That deliberate rejection prevents the two layouts from being
mixed.

This is a CAD result against the repository's historical reference solids.
The physical printed or ordered shell still must pass its gauges and no-load
closure.

## Finished size

- Original historical body and recessed face: 51 x 22 x 10 mm.
- Recovered nominal outside size: **51 x 22 x 14.5 mm**.
- Main internal height: 12.5 mm.
- Maximum controlled battery-body envelope: **25 x 10 x 5.5 mm finished**,
  including PCM, wrap, seams, and folded tabs. Leads/interconnect are routed
  and dry-fit separately.
- Conditional named DTP401525 layout: **25.3 x 15 x 4.0 mm maximum** including
  the drawing's L2 dimension. It has only 0.15 mm nominal clearance below the
  historical shelf and is not a generic wide-cell authorization.
- XIAO official STEP envelope: 22.482 x 17.780 x 4.460 mm.
- Ordered Vybronics VCLP1020B002L motor tolerance envelope:
  **10.2 mm diameter x 2.3 mm**.
- Renata-only screw architecture motor mechanical envelope:
  **10.2 mm diameter x 2.7 mm**. This includes the listed Lee PID10431 body,
  but does not qualify its electrical identity, current or duty.

The band adds only a narrow perimeter seam. The historical body and face remain
the large visible surfaces whether they arrive as ordered nylon or are printed
from the supplied exact-reference STL files.

## Print now

Print these in black PETG or PETG-HF:

1. If no shell is physically present, print **two** of
   `out/PRINT_FULL_SHELL_body_exact_historical_geometry.stl` and **two** of
   `out/PRINT_FULL_SHELL_hooked_face_exact_historical_geometry.stl`. The first
   pair is sacrificial for drilling, hook fit, sanding and abuse tests.
2. `out/PRIMARY_RENATA_ONLY_M2_screw_retained_midband_rise_4p50mm_nominal.stl`
   and its loose-tongue alternative.
3. `out/PRINT_TWO_PRIMARY_RENATA_ONLY_M2_keyed_retainer_posts_HEAD_DOWN.stl`
4. `out/PRIMARY_RENATA_ONLY_M2_body_drill_marking_jig_USB_NOTCH.stl`
5. `out/PRINT_DECK_DOWN_then_FLIP_battery_safety_bridge.stl`
6. `out/mic_drill_jig_usb_end_notched.stl`
7. `out/BENCH_ONLY_xiao_plan_fit_gauge.stl`
8. the lower layout gauge matching the battery and motor selected at the
   counter;
9. the individual maximum-envelope battery, XIAO, and motor gauges.
10. `out/MEASURE_MAX_finished_driver_island_8x4x2.stl`.

For the conditional PRT-13853/DTP401525 geometry, print both
`PLAN_B_MEASURE_MAX_DTP401525_total_25p3x15x4.stl` and
`PLAN_B_BENCH_ONLY_lower_fit_gauge_DTP401525_Vybronics_driver_rotated.stl`.
The existing mid-band and bridge do not change. The Lee PID8834 listing is not
proof that it is a DTP401525 and must not be put in this wider layout unless
its exact received identity and complete dimensions independently match.

### Bambu P1S settings

- 0.4 mm nozzle.
- 0.12 mm layers for bands and microphone jig.
- 0.16 mm layers for bridge and gauges.
- Five wall loops, six top/bottom layers, 40% gyroid.
- Arachne walls and thin-wall detection on; supports off.
- Add a 3 mm brim to each band; seam at the USB end.
- Put the band's locating tongue on the plate.
- Put the safety bridge's broad deck on the plate, then flip it for assembly.
- Print the full body as modeled with its flat exterior back on the plate and
  the cavity open upward. Print the hooked face as modeled with its broad
  exterior face on the plate and hooks upward. In slicer preview, add painted
  support only under true horizontal ledges; keep supports out of hook, slide,
  USB, microphone and screw interfaces.

Let the parts cool on the plate. Use the nominal band only if it seats fully
with fingertip pressure; otherwise try the loose tongue. Never force either
into the shell.

## No-adhesive Renata-only closure

For a mechanically retained Unit 001 using only Renata ICP501022UPM / part
100640 and a gauged motor within the 10.2 x 10.2 x 2.7 mm envelope, follow
`PRIMARY_RENATA_ONLY_SCREW_RETENTION.md`. Print the named screw band, the
two-post head-down file, the USB-notched body marking jig, and the dedicated
maximum motor gauge. This is a
separate architecture: do not print or install either adhesive-only band and
do not use the conditional wide-cell Plan B or barrel-motor layout.

The target fastener is two M2 x 10 mm flat countersunk screws. Lee's Electronic
PID6836 is the local candidate; its online finish is unspecified. The jig only
transfers the two centres. The empty body gets 2.2 mm preferred
clearance holes; an ordinary 3/32 inch (2.381 mm) bit is allowed because the
audit passes through 2.4 mm. The printed posts contain 1.6 mm blind pilots;
countersink only until each actual 90 degree flat head is flush.

## Battery/motor layouts

| Battery envelope | Preferred motor position | Notes |
|---|---|---|
| 12 x 10 x 5.5 mm max | Vybronics 10.2 x 2.3 mm max at USB-side end | Best RF clearance, least runtime |
| 15 x 10 x 5.5 mm max | Vybronics 10.2 x 2.3 mm max at USB-side end | Some antenna overlap; test |
| 24 x 10 x 5.5 mm max | Vybronics 10.2 x 2.3 mm max at antenna-side end | Fits documented Renata ICP501022UPM envelope; battery lies under antenna, so RF test is mandatory |
| 25 x 10 x 5.5 mm max | Vybronics 10.2 x 2.3 mm max at antenna-side end | Primary universal maximum gauge; RF test mandatory |
| DTP401525 25.3 x 15 x 4.0 mm max | Vybronics at antenna end; driver rotated 4 x 8 x 2 mm between them | Conditional Plan B only; 0.15 mm shelf gap, 0.40 mm hard-part gaps and full antenna overlap; exact gauge/no-load/RF tests mandatory |

The bridge pads sit on the historical internal shelf rather than passing
through it. Its deck clears a true 5.5 mm pack on 0.05 mm floor insulation by
0.40 mm. Reusing it with the 4.0 mm Plan B cell leaves 1.90 mm below the deck;
no new bridge is required in CAD. The PCB cannot load the pouch.

The finished insulated SMD motor-driver envelope is 8 x 4 x 2 mm. It has only
0.2 mm nominal wall margin, so its individual gauge and physical no-load close
are hard gates. Axial diodes and through-hole resistors do not fit.

## Physical release measurements

Record caliper photographs before soldering:

| Item | Required result |
|---|---:|
| Actual cavity length | at least 47.8 mm |
| Width at all XIAO corners | at least 18.2 mm |
| Floor-to-face height at centre and both ends | record actual |
| Finished battery | passes selected gauge without friction |
| Ordered Vybronics motor | no more than 10.2 mm diameter x 2.3 mm finished |
| Lee PID10431 fallback | passes screw-layout CAD only if the finished body passes the dedicated 10.2 x 2.7 mm max gauge; electrical/thermal/RF qualification remains mandatory |
| Driver island | fully insulated assembly passes 8 x 4 x 2 mm gauge |
| Barrel reference | may be measured, but no qualified guard exists; not for Unit 001 |
| XIAO with solder/wires | passes supplied XIAO gauge |
| Face hook slide | drops and slides without component or band load |

The battery must also have an exact manufacturer/MPN, integrated protection,
permission for at least 50 mA CC/CV charging to 4.20 V, verified polarity, and
a matching UN38.3 test summary. A seller's dimensions alone are not approval.
SparkFun PRT-13853/DTP401525 provides a documented geometric/electrical
reference, but this packet does not contain a matching UN38.3 summary for the
received lot. Lee PID8834 lacks proof that it is the same product.

## Assembly essentials

1. Flash/test the XIAO on USB with the battery disconnected.
2. Dry-fit the empty body, chosen band, and face. If using the separate
   Renata-only screw closure, complete its empty-body drill coupon and post
   retention gates before electronics enter the shell.
3. Add 0.05 mm electrical floor insulation.
4. Install the qualified battery without broad-face pressure and leave a
   relaxed lead loop.
5. Bond a gauged coin motor inside the audited 10.2 x 10.2 x 2.7 mm envelope
   to rigid structure. Do not use the exposed-rotor barrel reference in Unit
   001.
6. Build one labelled, matched SMD-only driver. For ordered DigiKey parts use
   the documented AO3400A low-side circuit and active-high firmware. For local
   Lee PID10431/NTR4101P/BAS16/10 kohm parts use the documented P-channel
   high-side circuit and active-low firmware. Gauge the fully insulated
   8 x 4 x 2 mm island; never power a motor from GPIO and never mix the two
   circuit/firmware pairs.
7. Put the bridge pads on the shelf and the XIAO on no more than 0.10 mm
   insulated adhesive outside the antenna zone.
8. Transfer the real USB and microphone positions; deburr and gasket.
9. Close first with witness film and fingertip pressure only.
10. Run the full electrical, thermal, RF, audio, drop, rattle, privacy, and
    cosmetic release record before bonding/packing.

## Files and regeneration

- `out/FIT_REPORT.json` contains exact arithmetic and boolean audit values.
- `out/EXACT_historical_body_face_recovery_assembly.step` is the complete
  reference assembly.
- `out/PRIMARY_RENATA_ONLY_M2_screw_retention_reference.step` is the separate
  mechanical-closure reference assembly, not Plan B.
- `out/PRIMARY_RENATA_ONLY_MEASURE_MAX_coin_motor_10p2x2p7.{step,stl}`
  controls the screw-layout motor envelope.
- `out/*.step` and `out/*.stl` are the manufacturing and gauge files.
- `out/SHA256SUMS.txt` records all generated artifact hashes.

The source package includes `reference/alu_body.step` and
`reference/alu_face_front_v3.step`, so it regenerates without a sibling repo.
Run `python generate_recovery.py`. Any change producing an intersection above
1e-6 mm3 aborts generation. STL and JSON outputs are byte-reproducible; STEP
export bytes may contain timestamps, so compare imported geometry, not bytes.
