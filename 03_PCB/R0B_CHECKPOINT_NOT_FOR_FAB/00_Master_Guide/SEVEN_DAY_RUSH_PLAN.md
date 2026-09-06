# Seven-day rush plan

## Goal

Attempt to produce 12 custom-PCB EVT assemblies, with two first articles built and tested before the remaining ten. The practical success target is one to five working units in seven days. Ten sealed and polished units remain schedule-risky because revision-one PCB, battery, firmware, and enclosure work are still open.

## Staffing

- One accountable senior PCB engineer.
- One firmware/bring-up engineer.
- One mechanical CAD engineer.
- One PCBA factory project owner.
- One final integration technician; two stations preferred after first-article release.
- One Anticipy decision owner who can approve or stop work immediately.

## Schedule

| Day | PCB/electrical | Mechanical | Firmware/test | Manufacturing/integration |
|---|---|---|---|---|
| 0 | Engineer accepts scope; review blockers | Start packaging study | Freeze bring-up plan | Send RFQs; reserve capacity |
| 1 | Battery decision; footprint review; complete routing; DRC/net checks | Develop centre/face concepts around provisional geometry | Create minimal bench image, self-tests, SWD plan | Factory returns stack-up, geometry, stock and schedule |
| 2 | Release only if all Gate 0 checks pass | Update from released PCBA STEP and battery | Release hashed FA firmware/test instructions | Start two first articles; print enclosure prototypes |
| 3 | Support DFM/CAM and answer exceptions | Fit/tolerance review | Prepare fixture, scripts, iPhone/BLE tools | Fabricate/assemble FA-001/FA-002 |
| 4 | Lead current-limited bring-up | Correct mechanical issues found | Test rails, USB, BLE, audio, storage, motion, LED, haptic | Factory supplies inspection evidence |
| 5 | Close faults or issue remaining-ten release | Freeze enclosure after FA evidence | Freeze passed firmware hash | Assemble remaining ten only if both FAs pass |
| 6 | Support integration faults | Produce/finish parts | Sealed-unit regression | Integrate two sealed first articles |
| 7 | Final disposition | Final mechanical corrections | Overnight/runtime/backfill review | Integrate remaining passed units, serialize, clean, package |

## Daily decision gates

- End of Day 1: Can the board be released without waivers?
- End of Day 2: Did the factory accept the exact technology and files?
- End of Day 4: Did both open-board first articles pass?
- End of Day 6: Did both sealed first articles pass?

If any answer is no, preserve the hardware and continue the EVT correction loop. Do not convert an engineering failure into a pass to protect the calendar.

