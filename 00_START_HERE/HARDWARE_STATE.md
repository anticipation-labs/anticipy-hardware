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
| R0 (`ANT-PROD-R0 EVT`) | KiCad + 31 commits of routing history | 23 non-GND, 36 GND | Furthest routed. Not released. |
| R0B | KiCad checkpoint | 176 connections | The master package's headline board. Behind R0 on routing. |
| EVT-A (`anticipy_evt_a`) | KiCad, deliberate fab hold | n/a — no copper laid | Different processor. Superseded. |
| R1 | A brief only | — | **Does not exist.** This is the target. |

---

## The current target (R1)

From `01_CURRENT_TARGET_R1/Anticipy_PROD_R1_Flux_Build_Brief.md` (2026-09-04):

- **MCU/BLE:** Raytac `MDBT50Q-1MV2` (nRF52840) — pre-certified module, chosen to stay in the same
  software family as the Founder units
- **Microphones:** 2 × Infineon `IM69D128SV01XTMA1`, 3 V PDM, 69 dB SNR
- **Battery:** 1-cell protected LiPo, target **250–300 mAh**, 10 kΩ NTC lead
- **Capacity goal:** ≥ 20 hours offline audio
- **Runtime goal:** 16 hours — requires measured average < 12.5 mA on a 200 mAh cell before
  conversion and aging margin
- **PCB envelope:** 49.0 × 20.0 × 0.8 mm preliminary; finished enclosure 56.0 × 23.0 × 12.0 mm
- **Scope:** 25-unit pilot, later 100-unit batch. The 10 Founder units stay on XIAO nRF52840 Sense
  so this work does not block the seven-day Founder build.

---

## Honest summary

The **documentation and process discipline are strong** — release gates, factory acceptance rules,
EOL test specs and checksum manifests all exist and are unusually rigorous for this stage.

The **engineering is not converged.** Three custom boards were started, none finished, and the
newest brief restarts a fourth on a different processor than the most complete package assumed.
No board has been fabricated and nothing has been physically tested. A live factory order is
sitting on an unverified part substitution.

Read [`CONTRADICTIONS.md`](CONTRADICTIONS.md) next.
