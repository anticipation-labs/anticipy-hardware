# Anticipy exact v0.6 KiCad correction audit

## Outcome

The controlled production basis is the existing `pcb_release/anticipy_evt_a` project: nPM1300, two IM69D128S microphones, W25N04KV storage, DRV2605L haptics, and the 37.5 mm × 14.0 mm × 0.60 mm outline. The older v0.9 BQ24075/AP2112 concept is obsolete and was not used.

No modified PCB is represented here as production-safe. The exact checkpoint is unrouted, KiCad ERC/DRC cannot be run in this environment, and the U1 host circuit has not received an independent nRF54L15 reference-design review. Fabrication remains **HOLD — NO GERBERS**.

## Baseline audit

| Check | Exact checkpoint result |
|---|---:|
| Board envelope | 37.5 mm × 14.0 mm overall bounds |
| Board thickness / copper layers | 0.60 mm / 4 |
| U1 gate | 0 copper pads |
| SW1 gate | 0 copper pads |
| J3 gate | 0 copper pads |
| Routed board segments | 0 |
| Vias | 0 |
| Copper zones | 0 |
| ERC / DRC | Not run; `kicad-cli` unavailable |
| Gerber/drill artifacts | None |

The original files are KiCad 8 serialized S-expressions that KiCad 9 is expected to open and upgrade. A real KiCad 9 open/save/ERC/DRC smoke test is still required; changing only the file version header would not be valid validation.

## Exact gate corrections

### 1. U1: Raytac AN54LV-15

Replace `BL54L15U_PINMAP_GATE` with a controlled `AN54LV-15` symbol and footprint derived from Raytac's public AN54LV-15 v1.1 specification and current recommended-pad guide.

- Body: 6.4 mm × 8.4 mm × 1.5 mm.
- Pad count: 55 total.
- Host lands: 45 lands at 0.50 mm × 0.30 mm, plus ten antenna-end GND lands at 0.46 mm × 0.30 mm.
- Pin assignments: pads 1, 15, 31, 40, 42, 44–55 are GND; pad 20 is `VDD_NRF`; pads 9/11/43 are `SWDIO`/`SWDCLK`/`NRESET`. Pads 28 and 30 are `DCC` and `DECD` and require a reference-circuit review before the design can be released.
- Place the module rotated so its integrated antenna faces the RF nose. At the current U1 center (89.4, 97.7), a 90° rotation puts the body approximately at X=85.2…93.6, Y=94.5…100.9 and points the antenna toward −X.
- Extend the all-layer no-copper/no-plane region beneath the module's 2.9 mm antenna end. The existing X=78.5…85.0 nose annotation alone does not cover the antenna portion under a rotated module.
- Remove or mark DNP `ANT1`, `C_RF1`, `L_RF1`, and `L_RF2`; AN54LV-15 contains its own antenna, so the old external RF feed/match network must not remain populated.

Proposed firmware-net assignment for review (it must be frozen in both symbol and footprint before routing):

| Existing net | AN54LV-15 pad / function |
|---|---|
| `3V0` | 20 / VDD_NRF |
| `SWDIO_TO_U1_PAD_TBD` | 9 / SWDIO |
| `SWCLK_TO_U1_PAD_TBD` | 11 / SWDCLK |
| `RESET_TO_U1_PAD_TBD` | 43 / NRESET |
| `QSPI_CS_TO_U1_PAD_TBD` | 10 / P2.05 |
| `QSPI_CLK_TO_U1_PAD_TBD` | 17 / P2.01 |
| `QSPI_IO0_TO_U1_PAD_TBD` | 24 / P2.02 |
| `QSPI_IO1_TO_U1_PAD_TBD` | 14 / P2.04 |
| `QSPI_IO2_TO_U1_PAD_TBD` | 26 / P2.03 |
| `QSPI_IO3_TO_U1_PAD_TBD` | 12 / P2.00 |
| `PMIC_SDA_TO_U1_PAD_TBD` | 35 / P1.13 |
| `PMIC_SCL_TO_U1_PAD_TBD` | 34 / P1.15 |
| `PDM_DATA_TO_U1_PAD_TBD` | 21 / P1.07 |
| `PDM_CLK_TO_U1_PAD_TBD` | 22 / P1.06 |
| `BUTTON_TO_U1_PAD_TBD` | 36 / P1.14 |
| `STATUS_LED_TO_U1_PAD_TBD` | 37 / P1.12 |

The remaining PMIC GPIO, UART, and haptic assignments must be captured in a reviewed firmware pin-allocation table rather than inferred during layout.

### 2. SW1: Littelfuse/C&K PTS841GMSMTRLFS

Replace the Alps zero-pad gate with `PTS841GMSMTRLFS` using the public PTS841 land drawing.

- Variant `GM`: 180 ± 50 gf, no locating pegs, no ESD pin.
- Four copper lands only; do not add peg holes or pad 5.
- Land size: 1.20 mm × 0.60 mm.
- Land centers relative to footprint origin: pin 1 (−2.00, −0.90), pin 2 (+2.00, −0.90), pin 3 (−2.00, +0.90), pin 4 (+2.00, +0.90), subject to the KiCad-side mirroring/orientation convention.
- Pins 1 and 2 are internally common; pins 3 and 4 are internally common. Connect 1/2 to `BUTTON_TO_U1_PAD_TBD` and 3/4 to GND.
- Retain the mechanical requirement that the actuator faces +KiCad Y / −mechanical-CAD Y, then check the side-wall plunger stack and courtyard in mechanical CAD.

### 3. J3/M1: 7 mm wired motor termination

Replace the proprietary FPC/hot-bar zero-pad gate with a two-wire serviceable termination and strain relief. This is a project-controlled land, not a motor-manufacturer-verified footprint.

- Two copper termination pads, `HAPTIC_OUT_P` and `HAPTIC_OUT_M`, with unambiguous polarity silkscreen.
- Two separate non-plated wire-routing/strain-relief holes between the solder joints and the motor scallop; do not share one hole where the leads can abrade together.
- Keep holes and copper clear of the board edge by the selected fabricator's 0.60 mm-board rules.
- Freeze pad/hole dimensions only after the actual motor wire diameter and insulation OD are measured. A reasonable engineering prototype starting point is 1.2 mm × 1.8 mm solder lands and 0.8 mm NPTH holes, followed by a pull test and flex-cycle test.
- Update the symbol from an FPC connector to a polarized off-board motor, and document lead color, polarity, adhesive/strain-relief process, and motor lot.

This correction eliminates the **zero-copper** condition but does not close the mechanical/process qualification gate.

## Storage recommendation

Do not silently substitute `MKDV4GCL-ABF` in this exact checkpoint. Treat it as a controlled Rev B option (JLC C51966232, LGA-8 6 mm × 8 mm, approximately 481 MB usable as currently reported) because its public pinout, recommended land, power-up behavior, SPI/SD protocol, and firmware driver have not been verified in this audit. If selected, create a separate symbol/footprint variant, confirm whether its orientation and exposed/ground pad differ from W25N04KV, and rerun power-integrity and firmware validation.

## Required release sequence

1. Import the controlled AN54LV-15 symbol/footprint and its antenna keepout; remove the external antenna network.
2. Perform a schematic review of VDD, DCC, DECD, reset, debug, decoupling, and every firmware-assigned GPIO.
3. Import the PTS841GMSMTRLFS four-pad footprint and update the switch symbol pin groups.
4. Freeze the wired-motor pad/hole geometry from measured wire samples and approve the strain-relief process.
5. Update PCB from schematic in KiCad 9, resolve courtyard/keepout conflicts, route all nets, add reviewed planes/pours, and inspect return paths.
6. Run unfiltered ERC and DRC in KiCad 9. Archive the reports separately from the text-structure audit.
7. Only after reviews pass, generate fabrication data using KiCad—not hand-authored or placeholder Gerbers.

## Source artifacts retained with this audit

- `docs/sources/AN54LV-15_Ver1.1_spec.pdf`
- `docs/sources/AN54LV-15_recommended_pad_20260702.pdf`
- `docs/sources/AN54LV_footprint_design_260730.zip`
- `docs/sources/pts841.pdf`

These are reference inputs. Their presence does not by itself validate a translated KiCad footprint.
