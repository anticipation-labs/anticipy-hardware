# Anticipy pendant v1.0 — start here

## The tiny answer

There are **two different builds** in this folder:

1. `01_PRINT_NOW` is the bigger lab version you can print on the Bambu P2S and assemble from ready-made boards.
2. `02_PRODUCTION_CAD` + `03_PRODUCTION_PCB` are the PLAUD-size customer version. That version needs one custom circuit board.

Do not mix the two. The big one proves the recorder. The small one becomes the product.

## What is actually finished

| Item | Controlled result | Meaning |
|---|---:|---|
| PLAUD NotePin S limit | 51 × 21 × 11 mm; 17.4 g | The hard comparison target |
| Print-now lab body | 66.2 × 27.2 × 14.2 mm | Fits the allowed +30% lab envelope |
| Exact-size production CAD | 50.5 × 20.68 × 10.8 mm | Digitally fits below the PLAUD limit |
| Production mass plan | 12.63 g nominal; 14.52 g with 15% reserve | Still below the 17.4 g limit; must be weighed physically |
| Offline storage requirement | 414 MB usable | Covers 20 hours at 5,000 B/s plus 15% |
| Battery requirement | 200 mAh and no more than 10.625 mA average | Covers 16 hours with 15% energy reserve; must be measured |
| Mechanical CAD checks | 23/23 pass; 16 STEP solids; zero modeled positive-volume intersections | Geometry is coherent, not physically qualified |
| PCB status | Editable KiCad engineering checkpoint | Not yet a routed, DRC-clean Gerber release |
| Firmware status | Compiles and a UF2 is supplied | Lab-only until a real pendant and iPhone pass every test |

## Tonight

1. Open `01_PRINT_NOW/Anticipy_v09_five_units_P2S.3mf` in Bambu Studio.
2. Print **one base, one lid, and all three little button plungers** in your PLA Silk+.
3. Use `01_PRINT_NOW/PRINT_AND_ASSEMBLE_P2S.md` exactly.
4. Do not put a battery in it yet. Dry-fit the printed dummy pieces first.
5. An experienced adult handles the LiPo, soldering, first power-up and checkout.

The little squares and circles visible in Bambu Studio are **fit gauges**. They
stand in for the battery, board, button, motor and haptic parts so you can check
the shell before risking electronics.

For the customer-size CAD, use only the gauges named
`battery_27x12.5x6` and `radio_AN54LV_8.4x6.4x1.5`. Any older 26 mm battery
or 6.3 × 7.9 mm radio gauge is obsolete and is excluded from the final ZIP.

## The production answer

The customer-sized unit uses:

- a tough molded polycarbonate inner chassis;
- a brushed/anodized 5052-H32 aluminum face;
- one shaped 4-layer PCB;
- a pre-certified Bluetooth module;
- two MEMS microphones;
- 4-Gbit managed local storage;
- a protected 200 mAh pouch cell with a temperature sensor;
- one side button and one 7 mm haptic motor.

The plastic chassis is an egg carton. Every part has its own seat, stop, keeper, tape, gasket or strain relief. The aluminum face is cosmetic and impact-sharing; it is not allowed to crush the battery or cover the Bluetooth antenna.

## What may be ordered

- **Lab parts:** may be placed in carts after checkout shows acceptable arrival dates.
- **Three custom EVT boards:** only after routing, ERC, DRC, assembler DFM and the signed battery drawing close.
- **Customer batch:** only after the three EVT units pass audio, BLE, 20-hour backlog, 16-hour battery, charging, drop, rattle, button, haptic, privacy and thermal tests.

The folder is deliberately honest: it contains no fake Gerbers and no claim that a computer-only check makes a wearable safe for customers.

## Open these next

| File | Job |
|---|---|
| `DECISION_CARD.md` | one-page answer and exact sequence |
| `COST_AND_TIMELINE.md` | current money and schedule truth |
| `01_PRINT_NOW/PRINT_AND_ASSEMBLE_P2S.md` | Bambu print and lab assembly |
| `01_PRINT_NOW/PRINT_MATERIAL_AND_FINISH.md` | what to use in the P2S and how to get the metal look |
| `HOW_IT_STAYS_SOLID.md` | simple no-rattle assembly explanation |
| `02_PRODUCTION_CAD/production_internal_layout.png` | picture showing what goes where |
| `03_PRODUCTION_PCB/README.md` | exact PCB state and remaining gates |
| `04_FIRMWARE/BUILD_STATUS.md` | what the current firmware really does |
| `05_QA_FIXTURES/README.md` | rattle and drop-test tools |
| `06_FACTORY/README.md` | controlled 3 → 10 → 35 → production ramp |
| `08_REPORTS/ELECTRICAL_AUDIT.md` | storage, battery, circuit and bench-test truth |
| `08_REPORTS/PRODUCTION_CANDIDATE_BOM.csv` | exact candidate parts and each purchase gate |
| `RELEASE_STATUS.md` | pass/fail evidence and blockers |

## Safety and privacy

The current lab firmware stores plaintext audio. Use only synthetic or explicitly permitted test audio. Rotate any password previously pasted into an AI chat, and never send a password or credit-card number in chat.
