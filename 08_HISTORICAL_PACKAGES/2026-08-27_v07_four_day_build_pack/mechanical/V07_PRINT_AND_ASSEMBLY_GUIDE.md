# Anticipy v0.7 no-custom-PCB four-day prototype

## Release status

This package is a mechanically retained, hand-assembled founder prototype for the chosen Seeed XIAO nRF52840 Sense + Adafruit Audio BFF #5769 + protected 500 mAh architecture. It is **not** a customer-production, waterproof, drop-certified, or safety-certified release.

The honest closed envelope is **76.0 × 33.0 × 19.0 mm**. The finished-mass estimate is **36.9 g nominal and 42.4 g with 15% uncertainty**, before the chain. We do not claim the 51 × 21 × 11 mm target or a sub-30 g device with these off-the-shelf modules.

## What is retained so it cannot rattle

| Item | Hard location | Final preload / anti-rattle measure |
|---|---|---|
| Protected 602535 pouch | Four-sided lower cradle; open pull-tab and lead exit | Battery pull-tab tape on the floor plus 0.3–0.5 mm closed-cell edge pads; never compress the broad pouch faces |
| XIAO | Fenced bay and two tool-releasable edge clips on carrier | 0.2 mm PET/Kapton shims under only the PCB edges |
| Audio BFF | Separate fenced bay and two edge clips | 0.2 mm PET/Kapton shims under only the PCB edges |
| Carrier | Base ledges and end stops | Four lid pillars preload 0.2 mm edge pads; no load enters the battery |
| ERM motor | 10.3 mm printed cup and two hard keepers | Thin acrylic PSA disc on the cup floor |
| Haptic driver + bulk-cap cluster | Four hard XY fences beside the pouch | Thin 3M 300LSE/9448A PSA plus one removable Kapton cross-strap |
| Hard-off switch | Floor pocket, side-wall opening, wall-connected keeper | Thin edge shim only if the delivered body is loose |
| User button | Four-leg tower, platform and side fences | Thin PSA under the switch; guided plunger selected from three lengths |
| Wires | Defined floor exits and carrier pass-throughs | Three Kapton strain-relief points; no loose wire loop and no wire crossing the pouch face |
| Enclosure | Alignment lip and asymmetric bosses | Four M2 × 8 mm button-head screws, tightened in a cross pattern |

The 15% allowance is a **reserved assembly/placement keepout** around every controlled module, plus an upward 15% height check. It is not a deliberately loose 15% pocket. The hard pockets use printable clearances, and thin removable shims remove the last tolerance without letting a part move.

## Controlled mechanical envelopes

Measure the delivered parts with calipers before closing a live battery in the case. Never force a larger part into a pocket.

| Part | CAD envelope, mm | Location |
|---|---:|---|
| Protected 602535 500 mAh pouch | 35.0 × 25.0 × 6.0 | Lower cradle |
| Adafruit Audio BFF #5769 | 21.0 × 17.7 × 5.0 | Upper carrier, left |
| Headerless XIAO nRF52840 Sense, rotated | 17.8 × 21.0 × 3.2 | Upper carrier, right |
| Vybronics VCLP1020B002L | 10.0 diameter × 2.1 | Lower motor cup |
| Discrete haptic + low-profile 100 µF cluster | 11.0 × 7.0 × 6.0 | Lower fenced pocket |
| C&K OS102 hard-off switch | 8.6 × 4.3 × 4.7 | Lower side pocket |
| C&K KSC201 button | 6.2 × 6.2 × 3.5 | Left button tower |

The battery's 15%-expanded footprint alone is 40.25 × 28.75 mm. With walls and retention, that is why the old 67.9 × 26.3 × 12.8 mm concept cannot honestly contain this build.

## Print this on the Bambu P2S

Print the small fit-gauge plate first:

`P2S_v07_fit_gauges.3mf`

Then print the retained enclosure plate:

`P2S_v07_nopcb_retained.3mf`

Both plates are millimetre-scale, already oriented, and fit inside a 256 × 256 mm build area. They are geometry plates, so select the following profile in Bambu Studio before slicing:

| Setting | Value |
|---|---|
| Printer / nozzle | Bambu P2S / 0.4 mm nozzle |
| Filament | Bambu PETG HF Silver or Gray; dry per the spool instructions |
| Scale | 100.00% on all axes |
| Layer height | 0.16 mm; 0.20 mm first layer |
| Wall generator | Arachne |
| Wall loops | 5 |
| Top / bottom shells | 6 / 6 |
| Sparse infill | 40% gyroid |
| Supports | Off |
| Brim | Off; add a 3 mm outer brim only if the machine's first layer is unreliable |
| Elephant-foot compensation | 0.15 mm |
| Seam | Rear / aligned away from the mic and button openings |
| Temperatures and flow | Use the current Bambu PETG HF filament preset after calibration |

Do not auto-arrange or rotate the objects. The base prints open-side up, the lid prints exterior-face down, and the carrier prints flat. Inspect the sliced preview to confirm the four screw bosses, board clips, motor keepers, mic duct and button guide are present before pressing Print.

PLA is acceptable for the first inert fit check. Use PETG HF for the carried four-day prototype because its clips and screw bosses tolerate handling better; neither material makes the device production-certified.

## Assembly, in the exact order

1. **Print and measure the dummy gauges.** Confirm Bambu Studio did not rescale them. Check each with calipers. If an axis is more than 0.20 mm wrong, run the printer's calibration before the enclosure plate.
2. **Print the base, lid, carrier and three plungers.** Remove only hairs or elephant foot. Do not sand the board clips thinner.
3. **Dry-close the empty shell.** Install four M2 × 8 mm button-head screws by hand in a cross pattern. Each screw must enter straight, and the lip must close without a forced gap. Remove the screws.
4. **Bench-build and test the electronics outside the case.** The XIAO, Audio BFF, microSD, button, motor driver, hard switch and protected pouch must already record, store, vibrate and switch off before mechanical installation.
5. **Install the hard-off switch and user button.** Add only enough thin PSA/shim to remove motion. Route their wires through the nearest channel and add a Kapton strain-relief tab.
6. **Install the protected battery.** Apply a purpose-made battery pull-tab tape to the floor, place the pouch in the cradle, and add only soft edge pads. Keep the pouch flat. Do not glue over its broad top face, fold it, puncture it, or trap its leads.
7. **Install the motor and driver.** Bond the motor to its cup floor with a thin PSA disc. The controlled 11 × 7 × 6 mm driver assembly includes the transistor, 1 kΩ and 100 kΩ resistors, flyback diode, 100 nF ceramic and a low-profile 100 µF bulk capacitor. Bond that assembly inside its four fences and add one removable Kapton cross-strap. A tall radial capacitor is not accepted, and nothing may sit on the pouch.
8. **Fit the carrier.** It sits on the two long ledges and between the end stops. Add four 0.2 mm edge pads where the lid pillars will touch it.
9. **Clip in the Audio BFF and XIAO.** Put 0.2 mm PET/Kapton shims under PCB edges only, press one edge under its fences, then flex the two clips with a plastic tool. Do not press on the microphones, antenna, connector or components.
10. **Secure the wire harness.** Use three Kapton anchors: one at the battery-lead exit, one below the carrier, and one beside the board connector. Leave a gentle service bend, but no free loop. No wire may rub the pouch or cross the screw bosses.
11. **Gasket the microphone.** Place a roughly 0.3 mm closed-cell ring between the XIAO mic area and the printed mic boss. Keep the center hole open. Confirm the USB plug enters without pushing the board.
12. **Choose the button plunger.** Start with 4.0 mm. Use 4.3 or 4.6 mm only if the lid closes and the button is not preloaded. The correct plunger clicks cleanly and remains loose enough to return.
13. **Close the lid.** Photograph the open routing, inspect for pinched wires, then tighten the four M2 screws gently in a diagonal cross pattern. Stop when the seam is closed; do not crush the plastic bosses.
14. **Perform the no-rattle check.** With power off, rotate the pendant slowly through every axis and hand-shake it for 60 seconds. Any sound means reopen it and add a thin edge shim at the moving part—never tighten the lid harder against the battery.

## Safe four-day verification

1. Use inert printed gauges, not the live LiPo, for the first 1 m drop and floor-impact checks.
2. On the powered unit, run 100 haptic pulses, 50 button presses, 20 USB insertions and a 60-second six-axis shake.
3. Run a full recording/storage/back-sync test while the pendant lies on a non-flammable surface. Record battery runtime and enclosure temperature.
4. Carry it for a full day only after the pouch stays flat, cool and unmarked and the strain relief remains fixed.
5. Reopen it after the first day. Look for glossy rub marks, cut insulation, loose tape, screw-boss cracks or pouch impressions. Replace the relevant shim or printed part if any appears.

The shell has open USB, mic, button and switch interfaces. It is **not sealed or waterproof**. Live-battery drop qualification, RF/acoustic validation, charge safety, 16-hour runtime and 20-hour backlog/back-sync remain physical engineering gates; geometry alone cannot prove them.

## Digital fit evidence

The generator exits with failure if any release check fails. The current export passes all ten checks recorded in `v07_fit_report.json` and `V07_FIT_REPORT.md`, including zero solid interference between every controlled module and the printed structure, zero interference among base/carrier/lid, 15% XY keepouts, 15% seated-Z clearance, positive explicit gaps, watertight meshes and one positive printable body per part.
