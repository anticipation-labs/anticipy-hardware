# Incoming inspection plan

Nothing enters assembly until it has a receiving record, supplier lot, quantity, revision and disposition. Mixed or unidentified lots stay physically separated.

## Receiving record fields

- Purchase order and line.
- Supplier and packing-slip number.
- Anticipy work order and phase.
- Manufacturer part number/revision.
- Supplier lot/date code.
- Quantity received, accepted, rejected and quarantined.
- Inspection equipment ID and calibration due date.
- Inspector ID and UTC timestamp.
- Linked photo/report/non-conformance number.

## PCBA incoming check

| Check | EVT 10 | DVT 35 | PVT 230 | Acceptance |
|---|---:|---:|---:|---|
| Count/revision/serial trace | 100% | 100% | 100% | Matches released work order; no duplicate serial |
| Package/MSL/ESD condition | 100% | 100% | 100% | Dry-pack/indicator and ESD packaging acceptable where required |
| Visual workmanship/polarity | 100% | 100% | 100% | No missing, shifted, tombstoned, reversed, bridged or damaged part |
| Supplier AOI/X-ray/e-test records | lot | lot | lot | Required reports name this PCB revision and lot |
| Board outline/thickness/warpage | 100% | first 10 + each panel | first 10 + one per panel | Released drawing limits; limits are currently blocked pending PCB release |
| Pogo fixture PCBA test | 100% | 100% | 100% | Pass `EOL_TEST_SPEC.md` PCBA subset before battery installation |

## Battery incoming check

The present battery placeholder is not approved. Receiving cannot begin until `BAT-ANT-200-001` has a signed drawing and matching safety/transport documents.

| Check | Frequency | Acceptance |
|---|---:|---|
| Correct MPN, revision and lot | 100% | Matches released approved-pack drawing |
| Pouch, tabs, PCM, leads and insulation visual | 100% | No dent, puncture, swelling, corrosion, exposed conductor, crushed edge, smell or wetness |
| Polarity and open-circuit voltage | 100% using keyed fixture | Released polarity; voltage within supplier shipping/receiving band |
| NTC response | 100% | Matches released 10 kOhm NTC circuit and receiving temperature band |
| Finished envelope and lead exit | EVT 100%; DVT first 10 + every lot; PVT first 10 + one per 20 | No dimension exceeds 26.0 × 12.5 × 6.0 mm and released lead envelope |
| Weight | EVT 100%; DVT/PVT first 10 + every lot | Within approved supplier drawing |
| Documentation | every lot | Applicable UN38.3 test summary, safety evidence, MSDS and lot trace available |

Any damaged, swollen, reversed or undocumented battery causes immediate lot quarantine. It is never forced into a shell or “tested to see if it works.”

## Enclosure and cap incoming check

| Check | Frequency | Acceptance |
|---|---:|---|
| Part/revision/material/finish/lot | 100% label trace | Matches released mechanical drawing and approved finish chip |
| Critical go/no-go fit gauge | 100% | PCB, battery, motor, button, acoustic and closure features accept the controlled gauge without force |
| Overall hard envelope | EVT 100%; DVT first 10 + every cavity/build; PVT first 10 + one per 20 | Finished closed assembly can remain within 51.0 × 21.0 × 11.0 mm |
| Cosmetic surface | 100% for first 230 PVT | No sharp edge, burr, crack, exposed fibre, objectionable sink/tool mark, colour/texture mismatch or finish damage under released cosmetic standard |
| Seam/registration features | EVT 100%; DVT/PVT first 10 + one per 20 | Released datum/feature limits; currently blocked pending DFM drawing |
| Chain attachment | EVT 100%; DVT/PVT first 10 + one per 20 | No crack, burr or undersized ligament; sample lot passes released pull/abrasion test |

## Motor, acoustic parts, adhesives and seals

- Match exact released MPN/material and supplier lot.
- Verify motor dimensions, lead exit and adhesive/retainer configuration against its controlled drawing.
- Keep left/right acoustic components identified if they differ.
- Verify membrane integrity and contamination-free handling.
- Record adhesive/seal manufacture date, expiry, storage condition and required cure window.
- Reject folded, stretched, contaminated or liner-damaged die cuts.
- Do not use expired or out-of-storage-condition material.

## Non-conforming material

1. Label and physically quarantine it.
2. Create a non-conformance record with photos and measurements.
3. Do not sort/rework/use-as-is without written disposition.
4. If supplier sorting is authorized, preserve the original lot and record every serial/quantity affected.
5. Feed repeated defects into the lot-stop rules before assembly resumes.

