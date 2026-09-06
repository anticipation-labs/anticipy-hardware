# 1.2 m low-spin free-drop release

## The non-negotiable geometry

The two 2020 masts hold the release head at a measured height. They do **not** guide the product while it falls. Below the three fingers is an unobstructed 80 mm fixture opening and at least a 200 x 200 mm guarded free-fall corridor.

## Stand

1. Bolt two 1500 mm 2020 extrusions to a 600 x 600 x 18 mm weighted base with metal brackets.
2. Add a rigid 2020 crossbar and diagonal metal braces.
3. Tether the mast to a wall or rigid bench. Ballast alone is not sufficient.
4. Mount the collet body horizontally to the crossbar with metal L-brackets through its four mounting holes.
5. Install the full polycarbonate fall/rebound guard.
6. Put a fresh 300 x 300 x 18 mm plywood target directly on level concrete at the guard centre.

## Collet

1. Install three guide caps at 90, 210 and 330 degrees. Use washers and nyloc nuts.
2. Install an M4 heat-set insert axially into each finger’s inner bore. Install an M4 x 30 nylon screw and locknut; cover only the final face with smooth PTFE tape or a POM cap.
3. Slide one finger under each guide. It must move at least 35 mm under spring force with no binding.
4. Connect matched extension springs from each finger outer hole to its body anchor. Measured pull at the closed position must match within 10%.
5. Install three polished M4 guide rods through the body and common latch plate. Collars set the lowered and 10 mm lifted positions.
6. In the lowered position, each latch stop block sits immediately outside one closed finger and prevents the spring opening it.
7. Tie three equal-length low-stretch cords from the latch plate to the three outside holes of the printed three-cord yoke. Connect the yoke centre hole to one 12 V pull solenoid above the opening. Hang a ruler from each plate attachment point and trim the cords until the unloaded yoke is level within 0.5 mm.
8. Pulse the solenoid from a fused, guarded ARM + momentary DROP box. Add a flyback diode. Never exceed the solenoid maker’s duty cycle.

The plate must rise parallel. Measure all three guide points: lift mismatch may not exceed 0.5 mm, and every finger must retract at least 35 mm.

## Setting one of 26 orientations

1. Copy `drop_orientation_map.csv` for the DUT serial.
2. Put the named pose key on a small lab jack beneath the collet.
3. Raise it until the pendant centre line aligns with the three nylon tips. The pose key automatically points the named face, edge or corner down.
4. Lift the common latch plate, push all three fingers inward, and lower the plate behind them.
5. Adjust the three nylon tips until they just hold the inert dummy/product at its centre of mass. Use equal light contact. Lock the nuts.
6. Lower the lab jack at least 20 mm and remove the pose key completely.
7. Verify the product hangs freely and no tip touches the button, microphone ports, chain hole or seam.

Re-measure the 1.200 m drop from the **intended impact point on the product** to the target, not from the collet body. Allow +/-2 mm.

## Thirty-release qualification with the inert dummy

Use an inert dummy weighted to production mass. Film side-on at 240 fps against a contrast grid.

Each release passes only if:

- All three fingers visibly start retracting in the same 240 fps frame.
- Every finger clears the dummy by at least 10 mm before it falls 15 mm.
- No fixture part or cord touches the dummy after release.
- The dummy remains inside the free-fall corridor.
- Angular change during the first 0.5 m is no more than 5 degrees.
- Height is 1200 +/-2 mm.

Any miss means change spring matching, clean/ream the guide, rebalance the three lift cords or replace the contact faces. Do not average failed releases away.

## DUT sequence

For the 26-drop engineering sequence, use all rows of `drop_orientation_map.csv`: six faces, twelve edges and eight corners. After every drop:

1. Wait and observe from outside the guard.
2. If the unit is hot, swollen, leaking, hissing, smoking, dented at the battery or has opened, stop and follow the battery quarantine procedure.
3. Otherwise inspect seam/sharp edges, record result, and run the defined short functional check.
4. Replace a damaged target before the next drop.

Do not recharge a drop-test unit until it has completed the written post-test battery inspection.
