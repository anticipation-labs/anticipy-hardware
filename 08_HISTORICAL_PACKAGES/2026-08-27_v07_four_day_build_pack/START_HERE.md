# Anticipy four-day no-custom-PCB prototype

## The answer

**Yes, one finished founder prototype can be built in four days if the critical parts are physically available on Day 1.**

This version uses two ready-made circuit boards like Lego blocks. It does not require a newly designed circuit board:

1. Seeed XIAO nRF52840 Sense: microphone, processor, Bluetooth, USB-C charging.
2. Adafruit Audio BFF #5769: microSD storage interface.
3. Protected 500 mAh battery: power.
4. Button: bookmark/control input.
5. Low-current motor plus transistor: haptic buzz.
6. Bambu P2S printed PETG body: holds everything still.

## Honest finished size

| Item | Four-day prototype | PLAUD NotePin S reference |
|---|---:|---:|
| Size | **76 × 33 × 19 mm** | 51 × 21 × 11 mm |
| Mass | **36.9 g estimate; 42.4 g with 15% uncertainty** | 17.4 g |
| Custom PCB | No | Production electronics |

The bigger body is the price of using ready-made boards and leaving real assembly clearance. Reaching the PLAUD envelope later requires one compact custom PCB.

## Do this first

1. Open `FOUR_DAY_ORDER_SHEET.csv` and order the spare-backed quantities.
2. For the battery, use the listed BBM protected **602535 / 500 mAh / 6 × 25 × 35 mm** part. If BBM misses Day 1, the order sheet includes an Amazon search fallback; accept only a listing that explicitly shows protection, the exact dimensions, and a Day-1 delivery date. Buy one battery route, not both.
3. Accept an order only when checkout shows a delivered date that leaves the electronics in hand on Day 1. Stock alone is not a delivery promise.
4. Reserve the two 32 GB cards for local Vancouver pickup.
5. In Bambu Studio, print `mechanical/P2S_v07_fit_gauges.3mf` first.
6. After measuring the real battery and boards, print `mechanical/P2S_v07_nopcb_retained.3mf` in PETG HF.
7. Build and test the electronics outside the shell before inserting the battery.
8. Follow `mechanical/V07_PRINT_AND_ASSEMBLY_GUIDE.md`, then the firmware gates in `firmware/FOUR_DAY_FIRMWARE.md`.

## Four-day clock

| Day | Finished result |
|---|---|
| Day 1 | Parts measured; fit gauges and shell printed; XIAO and storage work over USB. |
| Day 2 | Microphone, Bluetooth, storage, button and haptic pass on the open bench. Firmware UF2 is compiled and flashed. |
| Day 3 | Battery installed; wires restrained; carrier and four-screw lid closed; no-rattle check passes. Start the 16-hour battery test. |
| Day 4 | Battery result reviewed; backlog resumes after interruption; button/haptic/rattle tests pass. Run the separate 20-hour storage test in parallel on the spare electronics set. |

Two electronics sets are intentional. The final unit can run the 16-hour battery test while the spare open set runs the 20-hour phone-away storage test. Running those tests one after another would not fit the four-day window.

## What must pass before calling it working

- Five cold boots.
- One hour of decodable live Bluetooth audio.
- Twenty hours recorded with the phone absent, then recoverable after reconnect.
- A backlog transfer that resumes after interruption.
- Sixteen hours on the sealed 500 mAh battery; average draw at or below 26.56 mA.
- 100 button presses without doubles.
- 1,000 haptic pulses without reset or corrupt storage.
- Sixty-second six-axis shake with no sound or moving part.
- Empty/inert-shell 1 m handling test before any live-battery impact work.

Until the physical unit passes those gates, storage capacity and battery arithmetic are estimates, not proof.

## No-rattle design

The battery sits in a four-sided cradle with soft edge pads. The two boards clip into a removable carrier, the motor sits in its own cup, the driver cluster has four fences and a strap, wires have three strain-relief anchors, and four M2 screws close the lid. Nothing is allowed to float, and the lid never squeezes the broad face of the pouch battery.

## Safety

The user is a beginner. An experienced adult should supervise soldering and the first battery connection. Verify battery polarity with a multimeter, never solder to pouch foil, never force the lid, never charge a worn/swollen/hot pouch, and test recordings only with everyone informed and consenting.

## Current release truth

- Mechanical CAD: generated; ten digital fit checks pass; 3MF archives validate.
- Firmware source patch: host/static checks pass; reproducible GitHub Actions and Docker build paths included.
- Firmware binary: not compiled in this environment.
- Hardware: not purchased, soldered or physically tested here.
- Delivery: supplier stock is verified; the West Vancouver delivered date remains controlled by checkout.

That means the design work is ready, but the four-day calendar is not guaranteed until checkout confirms the parts arrive in time.

## Primary sources

- Seeed XIAO nRF52840 Sense: https://wiki.seeedstudio.com/XIAO_BLE/
- Adafruit Audio BFF: https://learn.adafruit.com/adafruit-audio-bff?view=all
- Omi DevKit 2 hardware guide: https://docs.omi.me/doc/hardware/DevKit2
- PLAUD NotePin dimensions: https://support.plaud.ai/hc/en-us/articles/53770668740761-What-is-the-difference-between-Plaud-NotePin-and-NotePin-S
- Apple Bluetooth restoration limits: https://developer.apple.com/library/archive/qa/qa1962/_index.html
