# Anticipy Saturday Unit 001 — SAPA no-Lee's handoff

## Goal

Build **one clean, closed, rechargeable Anticipy first article by Saturday afternoon** from the supplied headerless XIAO nRF52840 Sense board. This packet supersedes every shopping list or instruction that depends on Lee's Electronics.

SAPA supplies the remaining first-article parts and fabrication. Send Omar a written materials + rush-labour estimate and a realistic completion time **before charging or starting billable work**. Photograph and count all owner-supplied boards at intake.

## Owner supplies tonight

- XIAO nRF52840 Sense boards.
- If physically present: the complete DigiKey box for sales order `101304421`, invoice `131823187`, FedEx `539111734891`. It contains the preferred Vybronics motor, AO3400A driver parts, button and battery leads. The build must still proceed from SAPA stock/equivalents if that box is absent.

## SAPA supplies

- One documented, protected 1-cell 3.7 V LiPo that is safe with the XIAO's 50 mA charger setting. Finished cell/PCM envelope must pass the supplied 24 x 10 x 5.5 mm gauge, with verified polarity and relaxed lead routing. No harvested or unprotected cell.
- One haptic motor within the supplied 10.2 x 10.2 x 2.3 mm gauge.
- A low-side active-high motor driver equivalent to the AO3400A circuit below, including flyback diode and gate resistors.
- Thin wire, <=0.05 mm electrical insulation, strain relief, electronics-safe mounting material, acoustic mesh/gasket and M2 retention hardware.
- Black PETG/PETG-HF and printing/finishing for a clean complete enclosure.

## Architecture — do not add extra boards

- XIAO onboard microphone records the audio.
- BLE streams live audio to the Anticipy iPhone app.
- The iPhone is the recorder. **No microSD is required.** A phone disconnect creates an audio gap.
- USB-C charges the installed battery.
- D0 commands the haptic driver. Never connect a motor directly to D0.

## Required haptic wiring for the supplied active-high UF2

| From | To |
|---|---|
| XIAO D0 | 100 ohm, then AO3400A/equivalent N-MOSFET gate |
| MOSFET gate | 100 kohm, then GND |
| MOSFET source | XIAO GND |
| MOSFET drain | Motor negative |
| XIAO 3V3 | Motor positive |
| Flyback diode cathode/stripe | Motor positive / 3V3 |
| Flyback diode anode | Motor negative / MOSFET drain |

Use only `01_FIRMWARE/HOLD_FOR_PHYSICAL_RELEASE_TEST_Anticipy_0.9.3_owner2_live_50mA.uf2`. Verify its SHA-256 against the included file. If SAPA changes the driver topology or polarity, stop and obtain a matching firmware build; do not guess.

## Build order

1. Measure the real battery, motor, driver island and XIAO. Reject anything that fails its gauge.
2. Print two body/face sets, both midband variants, two posts, the bridge, drill jig and all gauges. Start with the nominal band; use the loose band only if nominal does not seat with fingertip pressure.
3. Full-erase and flash one XIAO. On USB power, privately commission the intended iPhone and prove audio, haptic, reconnect and rejection of a second phone.
4. Build and inspect the active-high driver. Prove motor-off during boot/reset/disconnect and test it with current-limited bench power.
5. Drill and countersink an **empty sacrificial body** with the supplied jig. Confirm screws clamp without protruding inward.
6. Install floor insulation, protected battery, haptic and insulated driver. Motor mounts to rigid structure, never to the battery.
7. Put the safety bridge on rigid supports, then mount the XIAO above it. Keep metal, battery PCM, wires and adhesive away from the antenna end.
8. Add the microphone opening and acoustic gasket. Keep USB-C accessible.
9. Dry-close with witness film. Zero marks or pressure are allowed on the LiPo pouch. Then close and run `04_QA/NO_LEES_RELEASE_CHECK.md`.

## Definition of done

One cosmetically clean closed unit that cold-boots from battery, charges safely by USB-C, streams usable audio to the Anticipy iPhone app, reconnects to its owner phone, rejects a second phone, performs repeated haptic commands without reset/noise/heat, and passes the signed release check. If any physical, battery, app or radio gate fails, the unit remains **HOLD — DO NOT SHIP**.

