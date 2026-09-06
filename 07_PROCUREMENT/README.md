# 07 — Procurement

**There is a live order in this folder. It is the only clock currently running on this project.**

## Live: JLCPCB order, not electrically cleared

Read [`JLCPCB_STATUS_2026-09-05.md`](JLCPCB_STATUS_2026-09-05.md) in full. Summary:

| | |
|---|---|
| Web order | `W2026083114248171` |
| PCBA order | `SMT026083160845` |
| Reference | `13417400A` |
| Problem | Part `C526821` did not match the PCB pads; JLCPCB could not assemble it |
| Requested replacement | `C190799 / MX25L25645GM2I-08G` |
| JLCPCB response | Will proceed; customer asked to wait; orientation must be checked in the final DFM |

### The open gate

- No final DFM has been attached
- The footprint / pin-1 / net-mapping check has **not** been confirmed as passed
- The email record **does not prove which local KiCad revision was uploaded** — and there are two
  different files both called "R0" (see [`../03_PCB/README.md`](../03_PCB/README.md))

**Do not approve assembly, and do not approve `C526821` or an unpopulated memory position**, until
the final DFM is reviewed and C190799's SOP-8 208/209 mil footprint, pin-1 orientation and net
mapping are verified by the hardware engineer.

## Cost and quantity material

| File | What it is |
|---|---|
| `PURCHASE_QUANTITIES.csv` | Execution v1.0 purchase quantities |
| `2026-08-28_tuesday_evt_BUY_12.csv` | 12-unit buy list |
| `2026-08-28_tuesday_evt_COST_CEILING.md` | Cost ceiling |
| `2026-08-27_v07_FOUR_DAY_ORDER_SHEET.csv` | Four-day build order sheet |
| `2026-08-28_execution_COST_AND_TIMELINE.md` | Cost and timeline |
| `anticipy-hardware-sourcing.docx` | Sourcing notes |

## Build and handoff guides

`Anticipy_Pendant_Manufacturing_Brief.pdf`, `Anticipy_Unit_001_Owner_Shopping_and_Hardware_Build_Brief.pdf`,
`Anticipy_Pendant_Guide.pdf`, `Anticipy_BUILD_GUIDE_LegoStyle.pdf`, `Anticipy_Build_Guide_VISUAL.pdf`,
`Anticipy_v0_Build_Guide.pdf`, `Anticipy_Hardware_CAD_Brief_v1.pdf`.

These are PDFs and DOCX and were catalogued by filename and context rather than parsed in full.
Confirm their contents before relying on them for a purchase decision.

## Schedule reality

From Execution v1.0, and still the most honest statement on record:

- Ready-made-board lab parts: ~5–10 business days after checkout
- Three custom EVT units: no responsible fixed date until the board and battery gates close;
  best case roughly **3–7 weeks**, not a promise
- **A customer batch in two weeks is not supported by the present evidence**
