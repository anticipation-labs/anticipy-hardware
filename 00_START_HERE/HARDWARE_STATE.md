# Hardware state — as of 2026-09-06

One page. What is actually true, what is merely designed, and what is only claimed.

---

## Fabrication state: HOLD

There is **no released manufacturing file set** anywhere in this repository — no Gerber, no ODB++,
no drill file, no pick-and-place, no assembly drawing, no final populated STEP, no final enclosure
drawing set. The 2026-08-28 Execution package verified this deliberately and recorded it as a pass:

```
PASS | PCB fabrication hold preserved | segments=0, vias=0, zones=0
PASS | no misleading Gerbers | none
FABRICATION STATE: HOLD — NO GERBERS
```

That is the correct state. It is not an oversight.

---

## What physically exists

| Thing | Status | Evidence |
|---|---|---|
| XIAO nRF52840 Sense proof unit | Built, **on physical-test hold** | `02_PROTOTYPE_XIAO/` |
| Printed enclosure shells | Printed, fit-checked digitally | `04_MECHANICAL/PRINT_READY/` |
| Custom PCB (any revision) | **Never fabricated** | — |
| Firmware running on a device | Yes — one image was pulled back off a device on 2026-07-24 | `05_FIRMWARE/DEVICE_RECOVERY/CURRENT-from-device-20260724.uf2` |

## What has been verified digitally only

From the 2026-08-28 Execution package (`08_HISTORICAL_PACKAGES/2026-08-28_execution_v1.0/`):

- Production envelope **50.500 × 20.680 × 10.800 mm** — *see contradictions, this conflicts with the newer brief*
- Full production STEP: 16 solids, zero positive-volume intersections
- Production mechanical checks: 23/23 pass
- Main product STL: 11/11 watertight, one connected body each
- QA fixtures: 42 STL, 45 STEP, 26 drop orientations, 59 acceptance checks
- Storage arithmetic: `5,000 B/s × 72,000 s × 1.15 = 414,000,000 B` required; ~481 MB usable candidate

## What has NOT happened

No physical audio, RF, battery, charge, thermal, drop, rattle, chain-pull, sweat/ingress,
haptic, button or privacy testing on a sealed unit. Every runtime and acoustic number in this
repository is calculated, not measured.

---

## The only clock currently running

A **live JLCPCB order** exists and is not electrically cleared:

- Web order `W2026083114248171`, PCBA order `SMT026083160845`, reference `13417400A`
- JLCPCB reported part `C526821` did not match the PCB pads and could not be assembled
- Replacement `C190799 / MX25L25645GM2I-08G` was requested, **subject to an unverified check**
  of SOP-8 208/209 mil footprint, pin-1 orientation and net mapping
- JLCPCB said they would proceed and asked the customer to wait
- **No final DFM has been attached.** The footprint/pin/net check has not been confirmed passed
- The email record does **not** prove which local KiCad revision was uploaded

**Do not approve assembly** until the final DFM is reviewed and C190799 orientation and net
mapping are confirmed. Full detail: [`../07_PROCUREMENT/JLCPCB_STATUS_2026-09-05.md`](../07_PROCUREMENT/JLCPCB_STATUS_2026-09-05.md).

---

## Board revisions at a glance

| Revision | Exists as | Unrouted | Verdict |
|---|---|---|---|
| R0 (`ANT-PROD-R0 EVT`) | KiCad + 31 commits of routing history | 23 non-GND, 36 GND | Furthest routed by far — 45 of 46 signal nets carry copper. Not released. |
| R0B | KiCad checkpoint, 45.8 × 18.0 mm, soldered NAND | **Zero copper** — `grep -c '(segment'` returns 0 | Named the "controlling checkpoint", but nothing on it is routed at all. |
| EVT-A (`anticipy_evt_a`) | KiCad, deliberate fab hold | n/a — no copper laid | Different processor. Superseded. |
| R1 | A brief only | — | **Does not exist.** This is the target. |

---

## The current target (R1)

From `01_CURRENT_TARGET_R1/Anticipy_Hardware_Development_Brief_2026-09-04.md` — "Rev 1,
September 4, 2026". This is the assignment:

- **Size:** **51 × 21 × 11 mm** target, +10 % per axis maximum without written approval
- **Weight:** ≤ **20 g**; flag anything above 25 g before fabrication
- **Runtime:** 16 hours
- **Local storage:** **QSPI NOR flash**, sized from the actual codec — plan **512 MB**
- **Offline capacity:** 16–20 hours
- **Connectivity:** BLE live audio, commands, status, reconnect, ordered backfill
- **Haptics:** app-commanded short discreet vibration
- **MCU:** **not locked** — "nRF52840-compatible starting point"; module vs bare SoC is an
  explicitly open question
- **Delivery:** Checkpoints A/B/C/D with per-unit acceptance gates and defined stop conditions

> ⚠️ Do **not** take specs from `Anticipy_PROD_R1_Flux_Build_Brief.md`, even though it sits in the
> same folder and is more detailed. The package's own supersession notice excludes it — along with
> its 49 × 20 mm layout and microSD concept — from the active handoff. Its 56 × 23 × 12 mm
> enclosure and Raytac `MDBT50Q-1MV2` are **not** the current target.

---

## Honest summary

The **documentation and process discipline are strong** — release gates, factory acceptance rules,
EOL test specs and checksum manifests all exist and are unusually rigorous for this stage.

The **engineering is not converged.** Three custom boards were started and none finished. The
board named the "controlling checkpoint" (R0B) has zero copper on it, while the one treated as
older (R0) is nearly routed. The current brief does not lock an MCU, asks for NOR flash while the
controlling board fits NAND, and sits in a folder alongside a superseded brief that contradicts it
on size, storage and module — with no banner saying so. No board has been fabricated, nothing has
been physically tested, and a live factory order is waiting on an unverified part substitution.

Read [`CONTRADICTIONS.md`](CONTRADICTIONS.md) next.
