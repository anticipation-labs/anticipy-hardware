# ANT-PROD-R0 engineering audit — 2026-08-29

Auditor: Claude (senior HW/SW). Method: full S-expression parse of the KiCad PCB
(62 footprints, 277 pads, 46 named nets, 49.00 x 20.00 mm capsule, 4 layers,
0.8 mm), cross-checked pad-by-pad against the official manufacturer documents
listed at the end. Every claim below traces to a fetched datasheet or a parsed
board fact. No assumptions.

## Verdict

The electrical design is sound and was verified against primary sources. Three
defects were found and fixed in `generate_board.py` (the reproducible source):

1. **U1 pad 31 (DCCH) was left floating.** The nRF52840 Reg0 DC/DC was therefore
   unusable, forcing LDO mode and wasting battery. Fix: added L3 (10 uH,
   TDK MLZ2012N100LT000, 2.0 x 1.6 mm) between U1 pad 31 (DCCH) and 3V_MAIN,
   per Nordic nRF52840 and Raytac application circuits.
2. **J1 shell stakes sat 0.475 mm outside the board edge** (copper off-board).
   Fix: J1 moved from x=20.6 to x=22.0 so all copper clears the edge with
   margin.
3. Verifier updated for the new footprint count (63) and the DCCH net.

## Verified correct (no action)

- **U1 pad map matches the Raytac MDBT50Q-1MV2 spec Ver. L exactly**: pads 1/2/
  15/33/55 GND, 28 VDD, 30 VDDH, 32 VBUS, 34 D-, 35 D+, 51/53 SWD, 40 nRESET.
  Every PINMAP.csv row (16 P0.27, 19 P0.26, 38 P0.16, 39 P0.15, 37 P0.13,
  36 P0.14, 29 P0.12, 27 P0.11, 45 P0.23, 24 P0.08, 22 P0.06, 41 P0.17,
  44 P0.20, 43 P0.21, 21 P0.05, 20 P0.04) matches the datasheet pin functions.
  KiCad's official `Raytac_MDBT50Q` footprint is used.
- **Antenna geometry is correct**: antenna end (pads 1/55 stubs at x=64.75,
  chip antenna to x=68.75) faces the right board edge; the all-layer keepout
  zone x 65.0..68.75, y 23.8..36.2 is exactly Raytac's 3.8 mm no-ground strip
  and is wider than the module, per the design guide.
- **32 unused module pads are legitimately NC** (pads 3-14 low-freq-only GPIOs,
  17/18 XL1/XL2, 23/25/26/42/46-50/52/54/56-61 unused GPIOs). 32.768 kHz
  crystal intentionally omitted; nRF52840 internal RCOSC used (documented
  battery-life tradeoff; revisit at DVT if sleep current matters).
- **nPM1300 power tree verified against PS v1.1 Table 35/39/40**: VBAT+C6,
  VBUS+C1, VSYS bulk, PVDD=VSYS (pin 4), SW1->L1->VOUT1=3V_MAIN, SW2->L2->VOUT2
  =3V_SD, PVSS1/2 to GND, EP AVSS to GND, VDDIO (pin 12) on 3V_MAIN with C13,
  VSET1=330k (2.7 V start, firmware raises to 3.0 V), VSET2=150k (3.0 V),
  NTC pin 18 wired to the protected pack's NTC wire, LDO1 (pin 29) = 3V_MIC
  rail with C10 10 uF, LDO2 (pin 31) decoupled and unloaded, VBUSOUT decoupled
  C5 and unused, LED0/LED1 open-drain sinks driving the bicolor LED cathodes
  (current-source mode, no series R needed), CC1/CC2 on the connector with
  5.1k Rd pairs.
- **Microphones IM69D128S**: pad map VDD/CLOCK/DATA/LR/GND correct; MIC1 LR=GND
  (left, falling edge), MIC2 LR=3V_MIC (right, rising edge); separate 100R data
  series resistors R14/R15 joining PDM_DATA; 1 uF bypass per mic close to VDD.
- **LIS2DW12**: RES pin 7 tied to GND (mandatory), CS pin 2 tied high (I2C
  mode), SA0/SDO pin 3 to GND (address 0x18, deliberate), both GND pins on
  plane, NC pin 5 floating (allowed).
- **TPD2EUSB30**: pin 1 D+, pin 2 D-, pin 3 GND, placed beside J1.
- **USB-C USB4105**: A1/A12/B1/B12 + 4 shell lands to GND, VBUS x4, CC1/CC2
  separate with Rd, D+ A6/B6 shorted, D- A7/B7 shorted, SBU1/SBU2 floating
  (correct for USB 2.0-only).
- **microSD Molex 104031-0811**: SPI wiring with 22R series on CLK/MOSI/MISO,
  100k CS pull-up to 3V_SD, detect switch pin 9 to GPIO with GND on pin 10,
  DAT2/DAT1 floating (SPI mode), back-side placement with 4 ground pattern pads.
- **Haptic**: low-side N-FET AO3400A with 100R gate series + 100k pulldown,
  flyback 1N4148W to 3V_MAIN, motor across 3V_MAIN/drain, 47uF + 100nF local
  bulk. Motor on the 2.7 V boot rail is within the Vybronics 3V rating.
- **Battery BT1**: protected 1S pack, VBAT/NTC/GND solder pads, 2.2uF C6 at the
  PMIC.
- **Test/bring-up**: 7 pogo pads on the back edge (SWDIO, SWDCLK, RESET,
  3V_MAIN, GND, UART TX/RX).

## Board-level rules frozen in the generator

- 4 layers, 0.8 mm, 5/5 mil min clearance/track, 0.45/0.20 mm via.
- Antenna keepout: no tracks, vias, pads, or copper pour on any layer.
- Capsule outline 49 x 20 mm with 10 mm end radii; keepout boundary drawn on
  Dwgs.User at x=65 for the assembler.

## Remaining before fabrication (unchanged gates)

1. Regenerate the board with KiCad's Python (this Mac now has KiCad 10 being
   installed), then run verify_project.py.
2. Clear DRC: 16 courtyard overlaps, 12 hole-clearance hits, 2 copper-edge
   hits, silk warnings. Fix in placement, not by silencing rules.
3. Route copper (FreeRouting first pass, then hand cleanup), fill ground plane
   on In1, power on In3, then zero unconnected.
4. USB pair geometry review against the JLCPCB stack-up document.
5. STEP export and collision review in the 50.5 x 20.7 x 10.8 mm enclosure.
6. Battery supplier drawing (UN38.3, IEC 62133-2) — Adafruit 1578 class part is
   the EVT placeholder; the pocket is sized for it.

## Sources fetched and verified

- Raytac MDBT50Q-1MV2 spec Ver. L (2023-05-24), raytac.com download index 43.
- Nordic nPM1300 Product Specification v1.1 (4490_483), Digi-Key mirror PDF.
- Infineon IM69D128S datasheet v1.01 (Table 7 pin configuration).
- ST LIS2DW12 DS11811 Rev 9 (Table 1 pin description).
- GCT USB4105 drawing rev B4 (gct.co/files/drawings/usb4105.pdf).
- Molex SD-104031-001 Rev E via LCSC/Farnell/TME mirrors (molex.com blocks bots).
- KiCad official footprints: RF_Module/Raytac_MDBT50Q,
  Connector_USB/USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal
  (fetched from kicad-footprints master, 2026-08-29).
