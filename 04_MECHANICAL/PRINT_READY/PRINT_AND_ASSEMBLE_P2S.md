# Anticipy v0.9: P2S print and no-PCB assembly

This is the four-day **engineering prototype**: XIAO nRF52840 Sense, Adafruit
5683 microSD BFF, exact Jauch LP502030JH+PCM+2 WIRES 50MM 250 mAh pack
(32.0 x 21.0 x 5.4 mm), B3U-1000P button, haptic motor and a controlled
12 x 8 x 3 mm hand-wired driver envelope. It is not waterproof, drop-certified or a
customer-production release.

## The one file to open

Open `Anticipy_v09_five_units_P2S.3mf` in Bambu Studio. It is in this same
`mechanical` folder and contains five
bases, five correctly flipped lids, five lanyard backplates, and all three
button-plunger lengths for every unit.  It contains geometry and placement,
not printer-bound G-code.

## P2S / PLA Silk+ settings

| Bambu Studio field | Set this |
|---|---|
| Printer | Bambu Lab P2S, 0.4 mm nozzle |
| Filament | Bambu PLA Silk+ preset |
| Nozzle | 235 °C first and later layers |
| Layer height | 0.16 mm; 0.20 mm first layer |
| Wall generator | Arachne |
| Wall loops | 4 |
| Top / bottom shells | 6 / 6 |
| Infill | 40% gyroid |
| Outer / top surface speed | 50 mm/s |
| Inner wall speed | 100 mm/s maximum |
| Support | Off |
| Brim | 3 mm outer brim, 0.10 mm gap |
| Seam | Aligned; paint it onto the USB side |
| Print order | By layer, not by object |

Use the official Silk+ preset for plate temperature and cooling because that
changes with the build plate.  Open the P2S door or top for PLA.  If the spool
has popped or strung, dry it at 55 °C for 8 h before the important plate.
Bambu's official guidance recommends 235 °C and a 50 mm/s outer wall for the
best gloss: <https://wiki.bambulab.com/en/x1/manual/printing-with-silk-filaments>

The base prints floor-down.  The 3MF has already flipped the lid so its smooth
outside face is on the bed and all internal pockets grow upward.  The verified
meshes need no supports; the base only has two small, approximately 10 mm
bridges above the USB opening.

First print **unit_1_base, unit_1_lid_exterior_face_down and the three
unit_1_plunger objects**. In Bambu Studio, select every other object in the
Objects panel, right-click, and choose **Do Not Print**. Dry-close unit 1. Only
then enable and print the remaining four sets. PLA Silk+ is attractive but brittle and
heat-sensitive; do not leave this prototype in a hot car.

## Material and consumables for five units

| Buy | Quantity | What it does |
|---|---:|---|
| Bambu PLA Silk+ 1.75 mm | 1 spool | About 60–80 g including brim and retries |
| 3M 9495LE / 300LSE, 0.17 mm | 1 small sheet or roll | Battery, motor, driver and lanyard primary bond |
| Polyimide tape, 10 mm wide | 1 roll | Independent safety straps and wire strain relief |
| 0.5 mm tinned solid copper wire | 1 m | Fourteen short, low-profile XIAO-to-BFF pad bridges |
| 1.0 and 1.5 mm heat-shrink tube | 1 m each | Individual battery-lead splices and joint insulation |
| PORON 4701-30, 0.79 and 1.57 mm | 1 small sheet of each | Select-to-fit microphone gasket; side cushions only |
| MG Chemicals 1035 neutral-cure RTV | 1 tube | Four board corner stakes and optional seam dots |
| M1.4 x 5 mm thread-forming screws | 12 | Two per enclosure plus two spares |
| Breakaway 2 mm lanyards + 6 mm split rings | 5 | Wear test; never use a non-breakaway neck cord |
| 90%+ isopropyl alcohol + lint-free swabs | 1 set | Adhesive surface preparation |
| 0.9–1.0 mm pin drill + hand pin vise | 1 | Clean printed screw pilots; no powered drill near cell |
| 0.6–0.7 mm pin drill + hand pin vise | 1 | Hand-clear the three 1.0 mm mic apertures if first-layer squish leaves flash |
| Flush cutters, fine tweezers, 600-grit paper | 1 set | Trim/smooth only; never sand near installed electronics |
| Digital calipers, 0.01 mm display | 1 | Measure the finished board stack and printed fit |

3M describes 9495LE as a 170 µm, double-coated polyester tape using its 300LSE
adhesive: <https://multimedia.3m.com/mws/media/2366195O/3m-double-coated-tape-9495le.pdf>.
Rogers describes 4701-30 as a very soft compression-control foam:
<https://www.rogerscorp.com/elastomeric-material-solutions/poron-industrial-polyurethanes/poron-4701-30>.
MG 1035 is neutral cure and intended for sensitive electronics:
<https://mgchemicals.com/products/adhesives/silicone-adhesive/rtv-glue/>.

## Prototype charging rule

Charge only while an adult is watching, on a nonflammable surface. Never charge
the pendant while it is worn; unplug USB before any wear, shake, audio or drop
test. Stop immediately for heat, swelling, smell, damaged wrap or unstable
charging. A customer-production design needs a documented cell-temperature/NTC
strategy and charger qualification; this hand-built prototype does not supply
that proof.

## Assembly: one simple order

1. **Print and dry-fit the empty case.** The lip must seat without force. If it
   is tight, remove only the high spots with 600-grit paper.  Clean the two
   screw pilots by hand and test M1.4 x 5 screws without the battery present.
   Hold the lid to a light: all three 1.0 mm microphone holes must be open. If
   one has only a thin PLA skin, clear it from the outside by hand with a
   0.6–0.7 mm pin; do not enlarge the finished hole and do not use a power drill.
2. **Make the 7.0 mm board sandwich.** With no USB cable and no battery, solder
   a red 30 AWG pigtail to XIAO BAT+ and black to BAT-, then cover those pad
   joints with polyimide. Put XIAO and BFF **backs facing each other**, exactly
   as Adafruit specifies, with same-name edge pads aligned and 0.20–0.25 mm PET
   electrical insulation between the backs (cut away only at the edge pads).
   Route the red/black battery pigtails directly out one side; no wire may run
   between the two board backs.
   Do not use the supplied plastic headers. Bridge all fourteen aligned edge
   pads with short 0.5 mm tinned solid-wire pieces; solder, trim flush, inspect
   every neighbour for shorts, and meter-check 3V-to-GND before USB. The BFF's
   uncut default TX jumper becomes XIAO D6/P1.11 chip-select. The finished
   stack—including solder and insulation—must measure no more than
   17.8 x 21.0 x 7.0 mm with digital calipers; rework it if it does not. The
   supplied dummy STL is a solid CAD envelope reference, not a physical gauge.
   This is fine-pitch
   soldering: use an experienced assembler if you cannot make clean joints.
3. **Wire the external button while there is no battery.** Connect B3U-1000P
   between XIAO D7/P1.12 and GND, leave a short lid service loop, then insulate
   both joints. Do not use the XIAO reset button as the user button.
4. **Build and wire the haptic circuit while there is no battery.** Draw a
   measured 12 x 8 mm rectangle on paper. Lay the AO3416, SOD-123 diode, 1210
   capacitor and three 0805 parts inside it, solder the insulated cluster and
   connect its motor and XIAO leads exactly as shown on the wiring card. The
   finished cluster—including solder and wire exits—must stay within
   12 x 8 x 3 mm; rebuild it if it does not.
5. **USB-test the complete electronics.** Insert microSD and prove audio, BLE,
   storage, the external button and haptic motor. Unplug USB. Fix every fault
   now; do not connect the battery until all five functions pass.
6. **Join the battery one wire at a time.** Put the pouch on a fire-resistant
   bench, confirm Jauch polarity with a meter, and keep bare lead ends separated.
   Slide heat-shrink onto black; make and fully insulate its inline splice to
   BAT- first. Only after no conductor remains exposed, repeat for red/BAT+.
   Never cut or strip both pouch leads at once; keep soldering heat at the wire
   end, at least 40 mm from the pouch. Meter-check polarity at the XIAO before
   power. This permanent splice is the selected connection; after this step,
   perform **no more soldering** on this unit.
7. **Clean every bonding spot.** Wipe printed plastic and component backs with
   isopropyl alcohol and let them dry completely.
8. **Install the exact Jauch battery in the base.** The hard cradle opening is
   deliberately 37.20 x 24.55 mm: it accepts a full +15% pack envelope plus
   0.20 mm per side. The real 32.0 x 21.0 mm pack therefore has 2.60 mm end
   clearance and 1.775 mm side clearance on each side. Put two narrow 9495LE
   strips under its flat face, away from the PCM/protection tail. Centre it with
   soft 1.5–1.8 mm PORON strips only along the side edges (or three stacked
   0.5 mm foam strips per side), then add two relaxed polyimide straps. Do not
   add rigid shims and do not squeeze or cover its broad faces; the free space
   above it is swelling allowance. Point the pack's PCM/wire tail toward +X,
   the XIAO end with the centred 5 mm rail opening. Route both 50 mm leads
   through that opening, then along the molded perimeter—not across the pouch
   face—and keep every bend radius at least 3 mm.
9. **Install the XIAO/BFF stack.** USB-C faces the side opening, the nRF52840
   microphone faces the lid, and the BFF/microSD faces the tray. The board
   fences provide about 0.25 mm nominal side clearance; they are not a +15%
   hard bay. Dry-fit the measured stack and lightly sand only printed high spots
   until it seats without force. Add four tiny
   MG 1035 corner fillets between the board edge/fences and tray.  Keep RTV away
   from the microphone, antenna, USB and microSD.  Cure open for 24 h.
10. **Build the lid without soldering.** Insert the 1.7 mm captive plunger from
   inside. Bond the already-wired B3U switch actuator-up in its pocket. If it
   does not click, try 1.9 and then 2.1 mm; use the shortest that clicks without
   staying pressed. Bond the already-wired motor and driver in their printed
   pockets with 9495LE. Route 30 AWG leads through
   the printed low wire notches—two on the driver guard and one on the motor
   ring—then bridge each pocket with an independent polyimide strap. No wire may
   cross over a guard wall or sit between the wall and lid during closure.
11. **Make the microphone gasket.** Measure the hard gap with the actual board.
   Cut a 6 x 5 mm PORON ring with a 4.2 x 3.2 mm clear centre.  Pick a thickness
   about 0.2–0.3 mm greater than the measured gap.  The foam touches gently; the
   printed chimney must never hard-contact a component.
12. **Tame the wires.** Leave one short service loop for the lid and tape the
   wires to the perimeter every 10–15 mm.  Nothing crosses a screw post, the
   battery face, microphone duct or antenna.  No free wire span exceeds 20 mm.
13. **Close it.** Confirm the button returns and the mic gasket is only lightly
    compressed.  Install two M1.4 x 5 screws by hand.  Stop when the seam closes;
    do not crush the tiny posts. Do not add RTV seam dots yet: the first six
    drops require reopening the case after every impact.
14. **Add the breakaway lanyard.** This printed backplate and its protruding tab
    are an external test accessory; they are intentionally excluded from the
    controlled 66.2 x 27.2 x 14.2 mm body envelope. With 0.17 mm tape it makes
    the thickest wearable test assembly approximately 15.97 mm, before the
    lanyard ring. Its tab also makes the printed wearable assembly approximately
    80.2 mm long before the ring; the bare electronic body remains 66.2 mm.
    Bond the flat backplate to the rear with
    9495LE, with its tab beyond the top end.  Press firmly, then leave it 72 h
    before a pull or drop test.  Attach a 6 mm split ring and breakaway cord.

## Rattle and drop gate

Do not call a unit finished until it passes all of these:

- 60 seconds of hand shaking on each of six axes: no audible or felt movement.
- 100 button presses, 100 haptic pulses and 20 USB insertions.
- One-minute audio playback: no enclosure buzz, muffling or tape noise.
- BLE stream, SD removal/reconnect and backlog transfer after final closure.
- 16-hour sealed runtime test and a separate 20-hour offline-storage test.
- After adhesive cure: screw-close, make one powered-off 1 m drop on one face
  onto 12 mm plywood over concrete, reopen, and inspect the pouch and wiring.
  Repeat for all six faces; stop immediately
  for a dent, smell, heat, swelling, torn wrap or cracked cell pocket.
- Only after all six inspectable drops pass, add four pinhead-size MG 1035 seam
  dots and cure 24 h. To test the sealed state, use one sacrificial unit for the
  remaining edge/corner drops and open it only after its final drop.

Passing this is an engineering result, not certification.  Geometry is verified;
physical print fit, battery runtime, RF, acoustics and impacts cannot be promised
before the five real builds are measured.

## Production enclosure recommendation (50–200 units)

Use a **PA12 MJF structural chassis**, not PLA and not a metal shell carrying
loads.  Add optional **0.3–0.4 mm 5052-H32 aluminum cosmetic front/back caps**.
The caps are bonded to recessed PA12 ledges and never carry the chain load.

- Leave an 8–10 mm PA12 RF window at the antenna end: no aluminum cap, battery,
  screw or long ground conductor over that zone.
- Anchor the bail through a metal eyelet into a broad PA12 load-spreading boss.
- Locate the PCB with three hard datums plus one soft stop, then use three screws
  into inserts; this prevents rocking without over-constraining it.
- Put 0.17 mm PSA under the pouch, low-force PORON only at its edges, a pull tab,
  and 0.8–1.0 mm free swelling space above the broad face.
- Use a production pack with a qualified NTC/temperature-sensing path and prove
  charger cutoffs across normal, hot, cold, open-sensor and shorted-sensor tests.
- Bond the haptic motor to a stiff PA12 rib with 9495LE and add a molded keeper
  or screwed strap.  Keep the motor and all fasteners off the pouch envelope.
- Mold wire channels and strain-relief hooks so no wire can sweep or slap a wall.
- Add 0.6–0.8 mm corner ribs, at least 1 mm PCB-to-wall impact clearance, boss
  gussets, and a tongue-and-groove seam.  Use an acoustic ePTFE mic membrane;
  claim no ingress rating until it is tested.
- Run six-face, twelve-edge and eight-corner drops on production-intent shells,
  then vibration, button, audio, RF and charge tests again.

PA12 carries every screw, battery, PCB, motor and bail load.  Aluminum supplies
the cool metal feel only; that separation is what keeps the device quiet after
a full day of motion and after a drop.
