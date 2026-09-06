# Pendant hardware docs (moved off the website)

Moved here 2026-08-23 from the live site (anticipation-labs/Anticipy `main`,
`src/app/internal/...`) at Omar's request — the full build documentation
for the pendant was sitting on anticipy.ai behind only the /internal
passcode gate. This private repo is now the only home for it.

Each file is the verbatim Next.js page (self-contained TSX; all the
content is inline JSX, so it reads fine as text):

| file | was |
|---|---|
| hardware.page.tsx | /internal/docs/hardware — Firmware Design Doc (ESP32-S3 spec, pins, state machine, audio pipeline) |
| schematic.page.tsx | /internal/docs/schematic — PCB schematic, full pin mapping + design notes |
| assembly.page.tsx | /internal/docs/assembly — hand-solder guide, continuity checks, QA |
| packaging.page.tsx | /internal/docs/packaging — box spec, print specs |
| manufacturing.page.tsx | /internal/docs/manufacturing — JLCPCB/PCBWay/Bittele order guide |
| bom.page.tsx | /internal/docs/bom — bill of materials, prices, buy links |
| hardware-transfer.page.tsx | /internal/hardware-transfer — wearable→action-surface architecture handoff |
| _original-index.page.tsx | /internal/docs — the index as it was before the cut |

Still on the site on purpose: /internal/docs (index, hardware entries
removed), /internal/render (investor render), /internal/docs/pendant-upload
(the Web Serial flashing tool), /internal/docs/competitive. The KiCad and
OpenSCAD sources were never on the site — they live in anticipation-labs/Anticipy
`firmware/` (private).
