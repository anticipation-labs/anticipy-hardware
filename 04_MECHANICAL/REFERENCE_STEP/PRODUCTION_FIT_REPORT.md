# Anticipy v1.0 retained mechanical fit report

Classification: **retention-complete CAD candidate**. It models the structural cap/seal, battery cradle, motor shelf/pocket/keeper, PCB scallop/snaps, vent seats, button plunger and chain boss, but it is not a schematic, routed PCB, Gerber release, certified battery, physically qualified seal or retail-production approval.

The 15% reserve is applied to every modeled XY placement envelope. Z clearances, finished dimensional tolerance, mass, RF keepout, cap overlap, storage and power are checked separately.

1. **PASS — finished envelope below hard maximum:** finished nominal 50.5 x 20.68 x 10.8; +0.15 tolerance remains below 51.0 x 21.0 x 11.0 mm
2. **PASS — chain geometry:** 4.2 mm hole; 1.15 mm nominal end wall
3. **PASS — all modeled items fit with 15% XY reserve:** all clear
4. **PASS — component courtyards fit shaped PCB with 15% XY reserve:** all clear
5. **PASS — actual 3-D component collision check:** no solid overlaps
6. **PASS — chassis/support versus component collision check:** no chassis, ledge or locator overlaps
7. **PASS — 15%-expanded same-layer collision check:** no expanded courtyard overlaps
8. **PASS — RF mechanical keepout:** 15%-expanded AN54LV antenna end clears controlled battery/motor and is 3.058 mm from aluminum; copper DRC and closed-device RF test still required
9. **PASS — front-cap split:** zero overlap; 0.15 mm seam
10. **PASS — retained structural cap stack:** 0.05 recess + 0.80 aluminum + 0.15 VHB; 1.15 bond land
11. **PASS — battery and motor worst-case planning separation:** 0.500 mm controlled-pack to maximum-can gap; 0.300 mm after full cradle travel
12. **PASS — PCB motor scallop clearance:** R4.30 leaves 0.218 mm beyond 1.15 x maximum can radius
13. **PASS — motor pocket assembly clearance:** 0.200 mm diametral clearance; 0.60 mm shelf; molder tolerance and keeper strain remain open
14. **PASS — GAW337 vent-seat depth:** 0.38 mm exterior recess plus local annular boss
15. **PASS — explicit vertical gaps:** battery 1.00-7.00; motor 7.25-9.35; lowest component 7.95; PCB 9.45-10.05; rear inner 10.20
16. **PASS — placed motor STEP Z bounds:** STEP motor 7.25-9.35; intended 7.25-9.35
17. **PASS — 20-hour backlog arithmetic:** needs 414 MB incl. 15%; design budget 481 MB usable
18. **PASS — 16-hour battery requirement calculated:** theoretical 85%-capacity ceiling 10.625 mA; use <=10.0 mA conservative production target until pack/cold/aging tests close
19. **PASS — mass planning ceiling:** shell CAD 3.79 g; 12.69 g total budget; 14.60 g with 15%; physical weigh-in required
20. **PASS — direct dual-microphone geometry:** 28.6 mm spacing; direct PCB/rear ducts
21. **PASS — print/export meshes watertight:** production_chassis.stl=True, production_aluminum_cap.stl=True, production_rf_cap.stl=True, production_print_front.stl=True, production_visual_pebble.stl=True, production_button_plunger.stl=True, production_button_boot.stl=True
22. **PASS — one connected body per enclosure part:** production_chassis.stl=1, production_aluminum_cap.stl=1, production_rf_cap.stl=1, production_print_front.stl=1, production_visual_pebble.stl=1, production_button_plunger.stl=1, production_button_boot.stl=1
23. **PASS — exported STEP regression:** 16 solids; 50.500 x 20.680 x 10.800 mm; 0 positive-volume overlaps

A digital PASS only proves the stated CAD/math check. RF tuning, battery runtime, acoustics, weight, thermal behavior, chain pull and sealing require physical prototypes.
