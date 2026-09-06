# 03 — PCB

**NOTHING IN THIS FOLDER MAY BE SENT TO A FABRICATOR AS A PRODUCTION RELEASE.**

There is no released Gerber, ODB++, drill file, pick-and-place or assembly drawing anywhere in
this repository. Three custom boards were started. None were finished. A fourth is specified but
not designed.

## The four revisions

| Folder | Board | State |
|---|---|---|
| `R1_TARGET_NOT_YET_DESIGNED/` | R1 | Empty by design. The brief lives in `../01_CURRENT_TARGET_R1/`. |
| `EVT_A_2026-08-28_SUPERSEDED/` | `anticipy_evt_a`, 37.5 × 14 mm four-layer, **nRF54L15** | Deliberate fabrication hold: 0 segments, 0 vias, 0 zones. No copper was ever laid, specifically so no misleading Gerbers could exist. Superseded by the R1 brief. |
| `R0B_CHECKPOINT_NOT_FOR_FAB/` | R0B, 45.8 × 18.0 mm four-layer, 0.80 mm | 70 electrical references, 223 pins, **176 connections unrouted**. The master package's headline board. |
| `R0_ROUTING_HISTORY_NOT_FOR_FAB/` | R0 / `ANT-PROD-R0 EVT` | **The furthest-routed board.** 45 of 46 signal nets carry copper. 31 commits of history (v21 → v43) driving unconnected nets from 199 down to 23 non-GND. |

## Read this before touching R0

`R0_ROUTING_HISTORY_NOT_FOR_FAB/` contains a **live `.git` repository with no remote**. Its 31
commits are the only version-controlled hardware history found on the machine, and they existed
nowhere else before this consolidation. It also carries uncommitted changes to `.kicad_pcb` and
`.kicad_pro`, plus an untracked `tools/final_build.py`. These were preserved exactly as found.

It includes `tools/route_board.py` — a purpose-written negotiated-congestion autorouter. That is
weeks of work and it exists only here.

## The R0 ambiguity

There are **two different files both called the R0 board**:

| | Master package copy | This git repository |
|---|---|---|
| `.kicad_pcb` sha256 | `64a4931f0fc455cd…` | `c086bae9fedc9a55…` |
| DRC timestamp | 2026-08-30 02:28:59 | 2026-08-29 18:04:35 |
| DRC violations | 134 | 4 |

The master package's copy was generated later by an automated run (its DRC header references a
sandbox path) and is **less** routed. Establish which is canonical before anyone uploads "R0"
anywhere — especially given the live JLCPCB order, whose email record does not prove which
revision was uploaded.

## Ordering note

`R0` is *more* complete than `R0B`, despite the naming. Either R0B discarded R0's routing work
or the master package's framing is wrong. Nothing on disk explains which.
