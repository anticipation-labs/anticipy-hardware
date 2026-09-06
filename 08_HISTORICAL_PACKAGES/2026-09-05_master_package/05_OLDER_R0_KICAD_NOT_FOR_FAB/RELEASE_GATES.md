# ANT-PROD-R0 fabrication release gates

All boxes must be checked by name and date before a Gerber ZIP is created.

## Electrical

- [ ] KiCad DRC: zero unconnected items
- [ ] KiCad DRC: zero clearance, hole, mask, and edge errors
- [ ] USB D+/D- differential pair reviewed against selected factory stack-up
- [ ] nPM1300 buck loops and ground returns reviewed against Nordic reference layout
- [ ] VSET1 = 330 kOhm and VSET2 = 150 kOhm verified on source and assembled board
- [ ] ESD part pin 1 = D+, pin 2 = D-, pin 3 = GND verified
- [ ] Microphone footprints, 0.60 mm acoustic holes, and gasket keepouts verified
- [ ] microSD footprint and card-eject clearance verified
- [ ] Antenna copper and metal keepouts verified on every layer
- [ ] SWD programming and recovery path verified

## Mechanical

- [ ] Exact protected battery part selected with drawing, UN38.3, and protection data
- [ ] Exact battery STEP checked with 0.5 mm minimum pocket clearance
- [ ] PCBA STEP imported into final enclosure STEP
- [ ] USB opening, button, LED light pipe, microphones, bail, and card access checked
- [ ] Aluminum faces stop before antenna keepout
- [ ] No component or battery touches aluminum

## Prototype validation

- [ ] Five EVT PCBAs assembled first
- [ ] Power rails checked with current-limited supply before battery connection
- [ ] Charging temperature and charge current measured
- [ ] BLE tested in closed metal/polycarbonate enclosure
- [ ] Both microphones and SD recording tested
- [ ] Haptic noise checked in recorded audio
- [ ] Runtime, reset, brownout, card removal, and full-storage behavior tested
- [ ] One golden unit retained with serial, firmware hash, and test record

## Release signatures

Electrical reviewer: ____________________  Date: __________

Mechanical reviewer: ____________________  Date: __________

Anticipy release owner: _________________  Date: __________
