# Primary Renata-only M2 screw retention

## Use exactly this architecture

This closure uses the historical body and hooked-face geometry, either as the
ordered nylon parts or as the supplied full-shell black PETG prints. It does
not rely on a structural shell-to-band adhesive. It is only for:

- Renata ICP501022UPM / part 100640, finished envelope no larger than
  24 x 10 x 5.5 mm;
- a finished coin motor no larger than the screw-layout mechanical envelope
  of 10.2 mm diameter x 2.7 mm;
- the ordinary 8 x 4 x 2 mm driver location.

That conservative motor envelope includes the ordered Vybronics
VCLP1020B002L maximum (10.2 x 2.3 mm) and the Lee PID10431 listing
(10.0 x 2.7 mm). This is mechanical CAD qualification only: Lee still needs
received-part gauging plus maker, current, duty, polarity, matched-driver,
thermal, audio, haptic and BLE/RF release tests.

It is incompatible with the 25.3 x 15 x 4.0 mm Plan B, its rotated driver,
the barrel-motor layout, and both adhesive-only band files.

## Print three closure files and the motor gauge

1. `PRIMARY_RENATA_ONLY_M2_screw_retained_midband_rise_4p50mm_nominal.stl`
2. `PRINT_TWO_PRIMARY_RENATA_ONLY_M2_keyed_retainer_posts_HEAD_DOWN.stl`
3. `PRIMARY_RENATA_ONLY_M2_body_drill_marking_jig_USB_NOTCH.stl`
4. `PRIMARY_RENATA_ONLY_MEASURE_MAX_coin_motor_10p2x2p7.stl`

Use the loose-tongue screw-band file only if the nominal tongue will not seat
with fingertip pressure. Print the two-post file twice so one post can be a
sacrificial thread-forming coupon and two undamaged posts remain for the unit.
Print PETG/PETG-HF with a 0.4 mm nozzle, 0.12 mm
layers, five walls, six top/bottom layers, 100% infill for the two posts, and
supports off. Put the band tongue down, the posts' square heads down, and the
jig broad face down. Reject stringing or missing walls inside either 1.6 mm
post pilot.

## Hardware and tools

- Two M2 x 10 mm, 90 degree flat countersunk screws plus spares. Local
  candidate: Lee's Electronic PID6836, `SCREW M2X10MM FLAT COUNTERSUNK
  10PCS/PKG`; the listing does not state finish or included angle, so inspect
  both at the counter and reject a head that does not seat in the 90 degree
  test countersink.
- 1.0 mm and 2.2 mm sharp drill bits. If an exact 2.2 mm bit is unavailable,
  a standard 3/32 inch (2.381 mm) bit is allowed; never exceed 2.4 mm.
- 90 degree countersink used by hand or at very low speed.
- M2 x 0.4 tap if available; otherwise the exact screw may hand-form the
  printed 1.6 mm pilot only after a sacrificial-post test passes.
- Pin vise, deburring blade, vacuum, calipers, eye protection, and clamp blocks
  that do not crush or distort the shell.

## Drill the empty body

1. Remove the face, antenna-window insert, battery, PCB, motor, and every wire.
   The first attempt must be a sacrificial body, not the investor unit.
2. Put the jig over the body's outside back. Point the jig's notch toward the
   USB end. The CAD centres are x=+11.0 mm, y=+3.0 and -3.0 mm.
3. Transfer both centres through the jig's 1.0 mm holes. Remove the jig; it is
   a marker, not a final drill bushing.
4. Back the floor with a flat sacrificial block. Drill each centre straight
   through at 1.0 mm, then enlarge only the empty body to 2.2 mm preferred,
   or 3/32 inch (2.381 mm). Never exceed the audited 2.4 mm diameter.
5. From the outside, form a shallow 90 degree countersink. Test the actual
   screw repeatedly and stop the instant its head is flush. The CAD checks a
   conservative 4.0 mm maximum envelope; 4.0 mm is not a machining target.
6. Deburr both sides, vacuum, wipe, and inspect with magnification. No plastic
   or metal swarf may remain before a battery returns.

## Prepare and assemble the posts

1. On a spare printed post, hand-thread the exact M2 screw into the 1.6 mm
   blind pilot. If the post splits, whitens, strips, lets the screw wobble, or
   makes the 10 mm screw bottom before clamping, stop and reprint/rework.
2. Seat the selected screw band in the body with fingertip pressure. Insert one
   keyed post from inside through each square ear socket; the large square head
   sits above the ear and the shaft reaches the floor.
3. Insert both screws from the outside back. Alternate half-turns until both
   post heads just seat and the band cannot lift. Do not use extra torque to
   correct a fit problem.
4. Confirm both screw heads are flush, neither post touches the Renata cell,
   gauged coin motor, XIAO, driver, face, or antenna-window insert, and the
   face still drops and slides freely.

## Mechanical release gate

Before electronics are installed, the retained empty shell must survive 100
vigorous hand shakes, torsion by hand, repeated face removal/reinstallation,
and a controlled 1 m drop sequence onto a protected hard surface without band
lift, screw rotation, cracking, whitening, rattle, or thread damage. Repeat the
inspection, electrical, charge/thermal, closed-case BLE/RF, audio, haptic, and
drop tests after final assembly. Any loosening or battery contact is a reject,
not a request for more torque.

The generated exact-shell audit records zero unintended overlap across 1,424
checks. Its dedicated 10.2 x 10.2 x 2.7 mm motor audit records 0.0 mm3 against
the exact shell body and face-motion path, screw band, battery, bridge, XIAO,
antenna keepout, driver, each post and each full-height 2.4 mm drill axis. The
smallest reported Z clearance is 2.47 mm to the bridge. Both conservative
2.4 mm drill axes cross 4.5239 mm3 of exact body-floor material,
the 4.0 mm countersink envelopes miss the through antenna opening and its
flange recess, and the posts deliberately collide with Plan B's rotated driver
by 32.2775 mm3.
