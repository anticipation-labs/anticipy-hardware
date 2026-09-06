# Anticipy durability and rattle test plan

## Release principle

No CAD file can prove a sealed wearable survives a day or a floor drop. The design becomes proven only when closed, recording units pass controlled tests and are then opened for internal inspection.

IEC 60068 supplies standard test methods, not one universal wearable severity. The levels below are Anticipy's proposed internal acceptance profile and must be reviewed with the selected test lab.

## Baseline every qualification sample

Before abuse, record mass to 0.01 g, seam gap at eight points, photos, microphone sensitivity/noise, BLE/RF, charge/current, button/haptic, flash CRC and a rattle recording. Repeat the same measurements after each test.

## Qualification matrix

| Test | Samples and severity | Pass condition |
|---|---|---|
| Product drop | 5 powered/recording units; 1.2 m; 6 faces, 12 edges and 8 corners onto 18 mm plywood over concrete | No reset/data loss, seam opening, exposed cell, sharp edge, structural crack or new rattle; all functions pass; seam change no more than 0.10 mm |
| Abuse margin drop | 3 separate units; one 1.5 m drop on each face | Same functional/safety requirements; cosmetic scuff allowed, structural damage not allowed |
| Shock | 5 units; IEC 60068-2-27 method; proposed 30 g, 11 ms half-sine, 3 shocks in both directions of each axis | No internal shift, damaged solder, cell damage, reset or new rattle |
| Vibration | 5 units; IEC 60068-2-6 method; proposed 10-150 Hz, 20 sweeps per axis, lab-reviewed severity | No fastener/PSA/gasket movement; mic sensitivity within 3 dB and current within 10%; no rattle |
| Tumble | 5 units; 100 falls in a 0.5 m padded plywood drum | Same drop pass rules |
| Button | 5 sealed units; 100,000 servo presses at 1-2 Hz | Events equal fixture actuations; no stick/miss/double event; force shift no more than 30%; repeat ingress |
| Haptic | 5 units; 50,000 cycles, 0.5 s on/1.5 s off | Current and acceleration stay within 20%; no debond, reset, corrupted recording or rattle |
| Splash prescreen | 5 powered units; proposed IPX4 local screen, 10 L/min from all directions for 5 min | Zero visible internal water, corrosion or functional loss; mass gain no more than 0.02 g; accredited test required before an IP claim |
| Sweat/humidity | 5 units; artificial perspiration plus 40 C/90-95% RH for 96 h | No finish/seam/button/mic damage or electrical drift; repeat splash screen |
| Thermal | 5 units; 20 unpowered cycles from -10 to 50 C, then a 16 h worst-case run at 35 C | No data gap/reset; runtime at least 16 h; cell within supplier limits; proposed skin-facing surface gate no more than 42 C at 25 C ambient |
| Battery retention | Open sacrificial drop/vibration survivors at controlled SOC | Cell remains seated with no dent, crease, abrasion, tab strain, leak or swelling outside supplier drawing |
| Chain eye | 50 N static for 60 s plus 10 N for 10,000 cycles; lab/safety review required | No crack, sharp edge or seam movement; breakaway clasp releases at its defined safe load |
| Shipping package | Local screen, then ISTA 3A parcel validation | Product still passes full functional, cosmetic, seam and rattle inspection |

Never deliberately short, crush, puncture or overcharge a pouch cell in a home or office. Battery abuse testing belongs with an accredited lab. Do not recharge a mechanically damaged test cell.

## Rattle test

### Local engineering screen

Build a slow motorized cradle that rotates the finished pendant through repeatable orientations while a contact microphone records impacts. Establish the mean and variation from known-good units; investigate any new impulse at least 6 dB over the qualified golden-unit envelope.

### Factory 100% screen

Every finished serial number receives the same fixed motion profile in a padded turner. The product microphones and an external contact sensor record the motion. Software compares peak impulses and spectral energy with the golden-unit limit; an outlier is opened, corrected and fully retested.

Rattle detection is paired with unit mass. A missing gasket, excess adhesive or wrong part often changes weight even when the unit is quiet.

## Every-unit factory checks

- firmware hash and unique serial
- sleep, record and transmit current
- both microphones and acoustic path
- BLE connection and signal level
- NAND write/read/CRC
- button five times and haptic five times
- charging and NTC simulation
- 30-minute record/burn-in
- weight, finished dimensions and seam at defined points
- automated rattle turner
- cosmetic and sharp-edge inspection

## Lot release

For the first 200, randomly select at least ten units from the PVT lot for destructive/long qualification work. Any fire/thermal event, battery damage, exposed conductor, water-to-PCB path, structural seam opening or recording/data-loss failure stops the lot and triggers root-cause correction plus affected retesting.

ISO 2859-1 sampling may later control noncritical cosmetic inspection. Safety-critical features are never accepted only by statistical sampling.

## Low-cost local fixtures

| Fixture | Planning cost | Job |
|---|---:|---|
| Guided drop rig and plywood target | CAD 80-150 | Repeatable orientation and height |
| NEMA17 rotating cradle plus contact mic | CAD 60-120 | Rattle screen |
| Servo/cam plus load cell | CAD 40-80 | Button cycle/force test |
| Accelerometer/piezo nest | CAD 20-40 | Haptic amplitude trend |
| Flowmeter/nozzle/turntable | CAD 80-150 | Splash prescreen only |
| 0.01 g scale, feeler gauges and pull scale | CAD 60-100 | Weight, seams and chain load |

Calibrated shock, vibration, ingress and certification claims still use a lab.

## Primary references

- IEC 60068-2-31 rough handling/free fall: <https://webstore.iec.ch/en/publication/516>
- IEC 60068-2-27 shock: <https://webstore.iec.ch/en/publication/514>
- IEC 60068-2-6 vibration: <https://webstore.iec.ch/en/publication/544>
- IEC 60529 ingress protection: <https://www.iec.ch/ip-ratings>
- IEC 62133-2 battery safety: <https://webstore.iec.ch/en/publication/70017>
- ISTA 3A parcel procedure: <https://ista.org/test_procedures.php>
- ISO 2859-1:2026: <https://www.iso.org/standard/85464.html>
- C&K PTS841GMSMTRLFS side-push switch: <https://www.littelfuse.com/products/switches/tactile-switches/pts841>
- Vybronics VC0720B015F wired motor: <https://www.vybronics.com/coin-vibration-motors/with-brushes/v-c0720b015f>
