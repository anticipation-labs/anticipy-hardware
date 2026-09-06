# ANT-PROD-R0 route status — 2026-08-30 (honest)

## What is true right now

The board file `Anticipy_PROD_R0_EVT.kicad_pcb` contains a fully placed board
with copper routed on 45 of 46 signal nets (GND is plane-only by design).
A 3D render confirms visible, continuous routing across all regions.

## What is NOT fabrication-grade yet

The last full DRC run reports:
- 36 GND unconnected links (plane stitching gaps; the In1 plane pour would close most)
- 23 non-GND unconnected links (one pad-pair each on: USB D+/D-, SW1/SW2,
  VBAT, USB_CC1, USER_BTN, 3V_MAIN, VSYS, VBUS, I2C, SWD, RESET, SD_SCK_MCU)
- Clearance/short violations introduced by the automated repair passes

## How it was produced

A purpose-built negotiated-congestion maze router (`tools/route_board.py`,
PathFinder-style soft costs + rip-up), written because FreeRouting 2.0.1
headless cannot save output and KiCad 10's Specctra export segfaults on
this machine. The router converged to ~39 nets cleanly; the remaining nets
were closed by escape-via fanouts, dogbones, and hand-run bridges
(`tools/` scripts + git history v1..v43).

## Shortest honest paths to a fab-grade board

1. FreeRouting GUI (10 minutes of human time): open
   `Anticipy_PROD_R0_EVT.dsn`, autoroute, save session. Then re-verify
   with DRC. Its router is far more mature than the in-session one.
2. A focused session finishing DRC one class at a time (shorts first,
   then clearance, then the 23 pad-pair bridges).

## Not fake-done

No gerbers were exported. No fab package was generated. The release gates
in RELEASE_GATES.md remain unchecked. The rule "no Gerbers until DRC is
clean" was respected.
