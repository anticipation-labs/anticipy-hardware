# Finish the PCB without Flux

## Free tools

| Job | Tool | Cost |
|---|---|---:|
| Schematic/PCB editing, DRC, Gerbers, drill, BOM/PnP | KiCad | Free/open source |
| Optional first-pass autorouting | FreeRouting | Free/open source |
| Version history | Git | Free/open source |
| Board viewing by a factory | KiCad Gerber Viewer or any CAM viewer | Free |

FreeRouting is an assistant, not an electrical reviewer. Its session must be
imported into KiCad, manually cleaned, and independently checked.

## Continue from this checkpoint

1. Open `Anticipy_PROD_R0_EVT.kicad_pcb` in KiCad PCB Editor.
2. Confirm the exact factory stack-up before finalizing impedance-sensitive USB traces.
3. Route the PMIC first: VSYS, SW1/L1/VOUT1, SW2/L2/VOUT2, VBAT, VBUS, and all local grounds.
4. Add dense ground vias at U2 exposed pad, PVSS pins, input/output capacitors, USB ESD ground, microphones, and radio ground pads.
5. Route USB D+/D- as a short differential pair from J1 through U4 to U1; avoid stubs.
6. Route PDM clocks/data and microSD SPI away from the two microphone acoustic ports.
7. Route I2C, interrupts, button, haptic, LED, SWD, and UART.
8. Fill inner layer 2 as uninterrupted ground. Use inner layer 3 for power and low-speed routing only where it does not split USB/PDM return paths.
9. Keep the Raytac antenna zone completely free of copper, vias, battery, and enclosure metal.
10. Run KiCad DRC, inspect every warning, and produce a DRC report.
11. Import the final PCB STEP into the enclosure with the exact battery STEP and verify every clearance.
12. Only after `RELEASE_GATES.md` is signed may fabrication files be exported.

## FreeRouting round trip

The included DSN is the clean board exchange file. In FreeRouting, load the DSN,
route, and save a `.ses` session. In KiCad use **File > Import > Specctra Session**.
Do not overwrite the clean generated board until the imported route has been
saved under a new review filename and passes DRC.

## Factory export after approval

KiCad can export:

- Gerbers for all copper, mask, paste, and silkscreen layers
- Excellon drill files
- component position CSV
- IPC-356 netlist
- STEP model

No paid Flux subscription is required for any of those outputs.
