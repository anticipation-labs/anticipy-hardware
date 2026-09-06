# ANT-PROD-R0B-EVT routing candidates

Status: **independent engineering candidates; not fabrication release.**

The clean native main board remains the authoritative placement/netlist base
and has 176 raw unconnected items. Each candidate below starts independently
from that same base. They are not cumulative and must not be merged by blindly
copying copper. The receiving engineer must consolidate them with full-board
DRC/connectivity review and then peer-review the resulting routing.

| Candidate | Saved/reloaded DRC | Unconnected | What it proves | Open review |
|---|---:|---:|---|---|
| USB | 0 | 149 | Reversible J1 fanout, USB data/CC/VBUS protection, R10/R11, equal-length data pair | Actual 0.80 mm fab stack, 90-ohm geometry, 0.36/0.16 mm CAM acceptance, layer transitions and rear-side copper |
| PMIC/power | 0 | 134 | Nordic-aligned switch/output loops, local bypasses, VSYS backbone and net-tie returns | U2 exposed-pad GND/thermal solution and U2.21-to-C1.1 VBUS remain open; peer review mandatory |
| Audio/storage | 0 | 152 | PDM microphone links, serial-NAND signal links, channel select and selected local power branches | FLASH_SCK has four vias; storage firmware/ECC/power-loss proof and SI/clock limit remain open |

## USB candidate

- Board: `reports/USB_ROUTED_CANDIDATE.kicad_pcb`
- Reproducer: `route_usb_full_stage_r0b.py`
- Evidence: `reports/USB_ROUTED_CANDIDATE_SUMMARY.txt`, DRC report and route CSV.
- D+ copper length: 45.073538 mm; D-: 45.073669 mm; planar skew:
  0.000131 mm, excluding the matched resistor bodies.
- Nominal candidate width/gap: 0.127/0.127 mm. This is not an impedance
  authorization; the fabricator must calculate it from the real material/Dk
  stack and return coupon/TDR evidence.
- Vias: 22 total; exactly two 0.36/0.16 mm reversible-contact fanout vias and
  twenty 0.45/0.20 mm standard vias. No non-GND In1 copper.
- Candidate uses B.Cu and In2.Cu for portions of USB/CC/VBUS routing. Review
  battery-side solder-mask coverage, return paths, stubs and layer transitions.

## PMIC/power candidate

- Board: `reports/POWER_ROUTED_CANDIDATE.kicad_pcb`
- Reproducer: `route_pmic_power_cell_r0b.py`
- Evidence: `reports/power_routed_candidate_summary.txt`, DRC reports and route
  manifest.
- Vias: 18, all 0.45/0.20 mm. No non-GND In1 copper. B.Cu signal copper is
  limited to three PVSS1 return segments between C7.2 and NT1.1.
- The four attempted U2 exposed-pad vias were rejected by DRC and are absent.
  The receiving engineer and assembler must agree on a DRC-clean thermal/GND
  design and whether filled/capped via-in-pad or relocated dogbones are used.
- The protected VBUS connection from U2.21 to C1.1 remains open.

## Audio/storage candidate

- Board: `reports/AUDIO_STORAGE_ROUTED_CANDIDATE.kicad_pcb`
- Router source for review: `route_audio_storage_clean_candidate.py`. It
  contains later unverified ground-stage edits and is **not** a verified exact
  reproducer of the saved checkpoint; the saved board/report/manifest are the
  authority.
- Evidence: `reports/audio_storage_routed_candidate_drc.txt` and
  `reports/audio_storage_routes.csv`.
- Vias: 26, all 0.45/0.20 mm. Non-GND copper is on F.Cu and In2.Cu only; no
  B.Cu or In1 signal tracks.
- `FLASH_SCK` is 14.094 mm and currently changes layer four times. Keep initial
  EVT bring-up at or below 8 MHz until hardware margin and signal-quality tests
  justify a change. This is a conservative debug ceiling, not a production
  signal-integrity release.
- Local microphone/flash ground escapes are not included.
- The MX35LF4GE4AD is serial NAND rather than transparent QSPI NOR. Hardware
  presence is not proof of offline storage: firmware must implement the NAND
  command path, ECC, bad-block handling, power-loss recovery, filesystem and
  sustained audio-write tests.

## Consolidation gate

The next engineer should replay each deterministic stage against a fresh main
board, resolve copper conflicts in priority order (PMIC loops, USB, audio/
storage, low-speed, rails, then GND), and demand after every step:

- zero new DRC violations;
- a strictly decreasing ratsnest count;
- no non-GND In1 copper;
- no copper/vias/components inside the Raytac all-layer keepout;
- no duplicate track/via geometry; and
- fresh saved/reloaded DRC and connectivity reports.

Only the final consolidated board may be considered for release, and only after
zero unconnected items, KiCad 8+ ERC, DFM/impedance approval, battery closure,
full PCBA 3D review and peer sign-off.
