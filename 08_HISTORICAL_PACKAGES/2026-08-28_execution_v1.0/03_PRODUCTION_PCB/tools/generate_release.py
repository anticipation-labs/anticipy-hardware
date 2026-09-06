#!/usr/bin/env python3
"""Generate the Anticipy EVT-A KiCad design checkpoint.

This generator is intentionally deterministic.  It emits native KiCad S-expression
files, but it does not claim that KiCad ERC/DRC has run.  Unknown vendor pad maps
remain copper-free release gates instead of being guessed.
"""

from __future__ import annotations

import csv
import json
import math
import re
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = "anticipy_evt_a"


def q(value: object) -> str:
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def uid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://anticipy.ai/pcb/evt-a/{seed}"))


NETS = [
    "GND", "CHG_5V", "VBAT", "BAT_NTC", "VBUS", "VBUSOUT", "VSYS",
    "1V8", "3V0", "SW_BUCK1", "SW_BUCK2", "VSET1", "VSET2",
    "LDO1_OUT", "LDO2_OUT", "CC1_NC", "CC2_NC", "SHPHLD",
    "PMIC_SDA_TO_U1_PAD_TBD", "PMIC_SCL_TO_U1_PAD_TBD",
    "PMIC_GPIO0_TO_U1_PAD_TBD", "PMIC_GPIO1_TO_U1_PAD_TBD",
    "PMIC_GPIO2_TO_U1_PAD_TBD", "PMIC_GPIO3_TO_U1_PAD_TBD",
    "PMIC_LED0", "PMIC_LED1", "PMIC_LED2",
    "FLASH_VDD", "QSPI_CS_TO_U1_PAD_TBD", "QSPI_CLK_TO_U1_PAD_TBD",
    "QSPI_IO0_TO_U1_PAD_TBD", "QSPI_IO1_TO_U1_PAD_TBD",
    "QSPI_IO2_TO_U1_PAD_TBD", "QSPI_IO3_TO_U1_PAD_TBD",
    "PDM_CLK_TO_U1_PAD_TBD", "PDM_DATA_TO_U1_PAD_TBD",
    "MIC_A_VDD", "MIC_B_VDD", "HAPTIC_REG",
    "HAPTIC_SDA_TO_U1_PAD_TBD", "HAPTIC_SCL_TO_U1_PAD_TBD",
    "HAPTIC_EN_TO_U1_PAD_TBD", "HAPTIC_OUT_P", "HAPTIC_OUT_M",
    "BUTTON_TO_U1_PAD_TBD", "STATUS_LED_TO_U1_PAD_TBD", "STATUS_LED_A",
    "RF_FEED_TO_U1_PAD_TBD", "RF_MATCH_A", "RF_MATCH_B",
    "SWDIO_TO_U1_PAD_TBD", "SWCLK_TO_U1_PAD_TBD", "RESET_TO_U1_PAD_TBD",
    "UART_TX_TO_U1_PAD_TBD", "UART_RX_TO_U1_PAD_TBD",
]
NET_CODE = {name: i + 1 for i, name in enumerate(NETS)}


def fp_text(kind: str, text: str, x: float, y: float, layer: str, hide: bool = False) -> str:
    hidden = " hide" if hide else ""
    return (
        f'    (fp_text {kind} {q(text)} (at {x:.4f} {y:.4f}) (layer {q(layer)}){hidden}\n'
        f'      (effects (font (size 0.65 0.65) (thickness 0.10))'
        f'{" (justify mirror)" if layer.startswith("B.") else ""}) (tstamp {uid(kind+text+str(x)+str(y))}))\n'
    )


def pad(num: str, x: float, y: float, sx: float, sy: float, net: str | None,
        layer: str = "B.Cu", shape: str = "roundrect", pad_type: str = "smd",
        drill: float | None = None, rr: float = 0.20) -> str:
    if pad_type == "np_thru_hole":
        layers = '"*.Cu" "*.Mask"'
        drill_s = f" (drill {drill:.4f})"
        shape = "circle"
    else:
        layers = f'{q(layer)} {q(layer.replace("Cu", "Paste"))} {q(layer.replace("Cu", "Mask"))}'
        drill_s = ""
    net_s = "" if net is None else f" (net {NET_CODE[net]} {q(net)})"
    rr_s = f" (roundrect_rratio {rr:.3f})" if shape == "roundrect" else ""
    return (
        f'    (pad {q(num)} {pad_type} {shape} (at {x:.4f} {y:.4f}) '
        f'(size {sx:.4f} {sy:.4f}){drill_s} (layers {layers}){rr_s}{net_s} '
        f'(tstamp {uid("pad"+num+str(x)+str(y)+str(net))}))\n'
    )


def rect_lines(w: float, h: float, layer: str, width: float = 0.10) -> str:
    x, y = w / 2, h / 2
    pts = [(-x, -y, x, -y), (x, -y, x, y), (x, y, -x, y), (-x, y, -x, -y)]
    return "".join(
        f'    (fp_line (start {x1:.4f} {y1:.4f}) (end {x2:.4f} {y2:.4f}) '
        f'(stroke (width {width:.3f}) (type default)) (layer {q(layer)}) '
        f'(tstamp {uid(layer+str(i)+str(w)+str(h))}))\n'
        for i, (x1, y1, x2, y2) in enumerate(pts)
    )


def footprint(ref: str, value: str, x: float, y: float, w: float, h: float,
              pads: list[str], description: str, library_id: str,
              courtyard: tuple[float, float] | None = None,
              extra: str = "", attrs: str = "smd", side: str = "B") -> str:
    cw, ch = courtyard or (w + 0.50, h + 0.50)
    cu, silk, fab, crtyd = f"{side}.Cu", f"{side}.SilkS", f"{side}.Fab", f"{side}.CrtYd"
    mirror = " (justify mirror)" if side == "B" else ""
    out = (
        f'  (footprint {q("Anticipy:" + library_id)} (layer {q(cu)}) '
        f'(at {x:.4f} {y:.4f}) (tstamp {uid("fp"+ref)})\n'
        f'    (property "Reference" {q(ref)} (at 0 {-h/2-0.7:.4f} 0) (layer {q(silk)}) '
        f'(effects (font (size 0.65 0.65) (thickness 0.10)){mirror}))\n'
        f'    (property "Value" {q(value)} (at 0 {h/2+0.7:.4f} 0) (layer {q(fab)}) hide '
        f'(effects (font (size 0.65 0.65) (thickness 0.10)){mirror}))\n'
        f'    (attr {attrs})\n'
        f'    (fp_text user {q(description)} (at 0 0) (layer {q(fab)}) '
        f'(effects (font (size 0.45 0.45) (thickness 0.07)){mirror}) '
        f'(tstamp {uid("desc"+ref)}))\n'
        + rect_lines(w, h, fab)
        + rect_lines(cw, ch, crtyd, 0.05)
        + extra
        + "".join(pads)
        + "  )\n"
    )
    return out


def npm_pads() -> list[str]:
    pin_net = {
        "A1": "PMIC_LED0", "A2": "PMIC_LED1", "A3": "PMIC_LED2",
        "A4": "LDO1_OUT", "A5": "LDO2_OUT", "A6": "GND", "A7": "GND",
        "B1": "VBUS", "B2": "VBUS", "B3": "CC2_NC", "B4": "1V8",
        "B5": "3V0", "B6": "1V8", "B7": "SW_BUCK1",
        "C1": "VSYS", "C2": "VSYS", "C3": "VBUSOUT",
        "C4": "PMIC_GPIO3_TO_U1_PAD_TBD", "C5": "PMIC_GPIO2_TO_U1_PAD_TBD",
        "C6": "3V0", "C7": "VSYS",
        "D1": "VBAT", "D2": "VBAT", "D3": "BAT_NTC", "D4": "SHPHLD",
        "D5": "CC1_NC", "D6": "PMIC_GPIO0_TO_U1_PAD_TBD", "D7": "SW_BUCK2",
        "E1": "VSET2", "E2": "VSET1", "E3": "PMIC_SCL_TO_U1_PAD_TBD",
        "E4": "3V0", "E5": "PMIC_SDA_TO_U1_PAD_TBD",
        "E6": "PMIC_GPIO1_TO_U1_PAD_TBD", "E7": "GND",
    }
    result = []
    letters = "ABCDE"
    # Official reference Gerber: 0.4191 mm x-pitch, 0.4394 mm y-pitch, 0.21082 mm aperture.
    for row, letter in enumerate(letters):
        for col in range(7):
            num = f"{letter}{col+1}"
            px = (col - 3) * 0.4191
            py = (row - 2) * 0.4394
            result.append(pad(num, px, py, 0.2108, 0.2108, pin_net[num], shape="circle"))
    return result


def make_board() -> str:
    header = f'''(kicad_pcb (version 20240108) (generator pcbnew)
  (general (thickness 0.6))
  (paper "A4")
  (title_block (title "Anticipy EVT-A exact-size pendant") (date "2026-08-28")
    (rev "EVT-A CHECKPOINT") (company "Anticipy")
    (comment 1 "NOT FOR FABRICATION: U1, SW1 and J3 vendor land maps gated")
    (comment 2 "Four layers, 0.60 mm; stack-up requires selected fab approval"))
  (layers
    (0 "F.Cu" signal)
    (2 "In1.Cu" power "GND")
    (4 "In2.Cu" power "POWER")
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (44 "Edge.Cuts" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
    (50 "User.1" user "RF Keepout")
  )
  (setup (pad_to_mask_clearance 0))
  (property "FAB_STATUS" "HOLD - NO GERBERS")
  (property "BOARD_DATUM" "KiCad (100,100) = mechanical CAD (0,0); Ky=100-CADy")
'''
    nets = '  (net 0 "")\n' + ''.join(f'  (net {i} {q(n)})\n' for n, i in NET_CODE.items())
    fps: list[str] = []
    # Account-gated Ezurio pad map: deliberate zero-copper mechanical placeholder.
    fps.append(footprint("U1", "453-00224R", 89.4, 97.7, 6.3, 7.9, [],
                         "PINMAP GATE / NO COPPER PADS", "BL54L15U_PINMAP_GATE",
                         courtyard=(7.245, 9.085), attrs="exclude_from_pos_files exclude_from_bom"))
    # Two official bottom-port PDM microphone footprints; 0.6 mm acoustic NPTH.
    mic_pads_a = [
        pad("1", -0.75, 0.411, 0.75, 0.54, "MIC_A_VDD"),
        pad("2", -0.75, -0.411, 0.75, 0.54, "PDM_CLK_TO_U1_PAD_TBD"),
        pad("3", 0.838, -0.411, 0.838, 0.54, "PDM_DATA_TO_U1_PAD_TBD"),
        pad("4", 0.838, 0.411, 0.838, 0.54, "GND"),
        pad("5", 0, 0, 1.725, 1.725, "GND", shape="circle"),
        pad("", 0, 0, 0.6, 0.6, None, pad_type="np_thru_hole", drill=0.6),
    ]
    mic_pads_b = [
        pad("1", -0.75, 0.411, 0.75, 0.54, "MIC_B_VDD"),
        pad("2", -0.75, -0.411, 0.75, 0.54, "PDM_CLK_TO_U1_PAD_TBD"),
        pad("3", 0.838, -0.411, 0.838, 0.54, "PDM_DATA_TO_U1_PAD_TBD"),
        pad("4", 0.838, 0.411, 0.838, 0.54, "3V0"),
        pad("5", 0, 0, 1.725, 1.725, "GND", shape="circle"),
        pad("", 0, 0, 0.6, 0.6, None, pad_type="np_thru_hole", drill=0.6),
    ]
    fps.append(footprint("U2", "IM69D128S", 87.2, 105.2, 3.5, 2.65, mic_pads_a,
                         "PDM MIC A / LR=GND", "IM69D128S", courtyard=(4.025, 3.0475)))
    fps.append(footprint("U3", "IM69D128S", 113.8, 94.8, 3.5, 2.65, mic_pads_b,
                         "PDM MIC B / LR=3V0", "IM69D128S", courtyard=(4.025, 3.0475)))
    # 8x6 WSON SPI NAND; EP is electrically unconnected by vendor and tied to board GND here.
    flash_nets = {
        "1": "QSPI_CS_TO_U1_PAD_TBD", "2": "QSPI_IO1_TO_U1_PAD_TBD",
        "3": "QSPI_IO2_TO_U1_PAD_TBD", "4": "GND",
        "5": "QSPI_IO0_TO_U1_PAD_TBD", "6": "QSPI_CLK_TO_U1_PAD_TBD",
        "7": "QSPI_IO3_TO_U1_PAD_TBD", "8": "FLASH_VDD", "9": "GND",
    }
    flash_pads = []
    for i in range(4):
        flash_pads.append(pad(str(i+1), -3.75, -1.905 + i*1.27, 0.50, 0.48, flash_nets[str(i+1)]))
        flash_pads.append(pad(str(8-i), 3.75, -1.905 + i*1.27, 0.50, 0.48, flash_nets[str(8-i)]))
    flash_pads.append(pad("9", 0, 0, 3.4, 4.3, "GND", rr=0.05))
    fps.append(footprint("U4", "W25N04KVZEIR", 98.3, 97.6, 8.0, 6.0, flash_pads,
                         "4-Gbit SPI NAND", "WSON8_8x6_W25N04KV", courtyard=(9.2, 6.9)))
    fps.append(footprint("U5", "nPM1300-CAAA", 106.2, 95.8, 3.0775, 2.3775, npm_pads(),
                         "35-ball WLCSP / official map", "WLCSP35_nPM1300_CAAA",
                         courtyard=(3.5391, 2.7341)))
    drv_nets = {
        "A1": "HAPTIC_EN_TO_U1_PAD_TBD", "A2": "HAPTIC_REG", "A3": "HAPTIC_OUT_P",
        "B1": "GND", "B2": "HAPTIC_SDA_TO_U1_PAD_TBD", "B3": "GND",
        "C1": "HAPTIC_SCL_TO_U1_PAD_TBD", "C2": "3V0", "C3": "HAPTIC_OUT_M",
    }
    drv_pads = []
    for ri, letter in enumerate("ABC"):
        for ci in range(3):
            num = f"{letter}{ci+1}"
            drv_pads.append(pad(num, (ci-1)*0.5, (ri-1)*0.5, 0.25, 0.25, drv_nets[num], shape="circle"))
    fps.append(footprint("U6", "DRV2605LYZFR", 104.8, 104.7, 1.5, 1.5, drv_pads,
                         "HAPTIC DRIVER", "DSBGA9_DRV2605L", courtyard=(1.9, 1.9)))
    # Antenna and tuning network. Values are only Johanson evaluation values, not final product values.
    ant_extra = (
        '    (fp_text user "PIN1 FEED INBOARD" (at 0 -2.2) (layer "B.SilkS") '
        '(effects (font (size 0.45 0.45) (thickness 0.08)) (justify mirror)) '
        f'(tstamp {uid("ant-pin1")}))\n'
    )
    fps.append(footprint("ANT1", "2450AT18A0100001E", 79.55, 100.0, 1.6, 3.2,
                         [pad("1", 0, -1.85, 1.0, 0.8, "RF_MATCH_B"),
                          pad("2", 0, 1.85, 1.0, 0.8, None)],
                         "2.4 GHz chip antenna", "2450AT18A0100001E", courtyard=(1.84, 3.68), extra=ant_extra))
    fps.append(footprint("C_RF1", "DNP/TUNE (eval 1.0pF)", 82.15, 100.0, 1.0, 0.5,
                         [pad("1", -0.55, 0, 0.55, 0.55, "RF_FEED_TO_U1_PAD_TBD"),
                          pad("2", 0.55, 0, 0.55, 0.55, "RF_MATCH_A")],
                         "RF SERIES SLOT", "0402_RF", courtyard=(1.15, 0.575)))
    fps.append(footprint("L_RF1", "DNP/TUNE (eval 2.7nH)", 83.25, 101.0, 0.5, 1.0,
                         [pad("1", 0, -0.55, 0.55, 0.55, "RF_MATCH_A"),
                          pad("2", 0, 0.55, 0.55, 0.55, "GND")],
                         "RF SHUNT SLOT", "0402_RF", courtyard=(0.575, 1.15)))
    fps.append(footprint("L_RF2", "DNP/TUNE (eval 3.9nH)", 84.15, 100.0, 1.0, 0.5,
                         [pad("1", -0.55, 0, 0.55, 0.55, "RF_MATCH_A"),
                          pad("2", 0.55, 0, 0.55, 0.55, "RF_MATCH_B")],
                         "RF SERIES SLOT", "0402_RF", courtyard=(1.15, 0.575)))
    # Side-actuated switch selected to match the side-wall plunger. Formal delivery drawing remains gated.
    # The zero-pad envelope is placed with actuator facing board-outward (+KiCad Y / -mechanical-CAD Y).
    fps.append(footprint("SW1", "SKSCLCE010", 100.0, 104.95, 3.5, 3.55, [],
                         "SIDE PUSH OUTWARD +Y / PADMAP GATE", "SKSCLCE010_PADMAP_GATE",
                         courtyard=(4.025, 4.0825), attrs="exclude_from_pos_files exclude_from_bom"))
    # Electrical interfaces: battery, charge pogo, and off-board FPC ERM motor.
    fps.append(footprint("J1", "BAT-ANT-200-001 3-wire", 93.5, 105.2, 4.6, 2.2,
                         [pad("1", -1.6, 0, 1.0, 1.6, "VBAT"),
                          pad("2", 0, 0, 1.0, 1.6, "BAT_NTC"),
                          pad("3", 1.6, 0, 1.0, 1.6, "GND")],
                         "+ NTC - / supplier gate", "BATTERY_WIRE_PADS", courtyard=(5.29, 2.53)))
    fps.append(footprint("J2", "MAGNETIC POGO 5V", 108.7, 105.6, 3.6, 1.8,
                         [pad("1", -1.1, 0, 1.3, 1.3, "CHG_5V"),
                          pad("2", 1.1, 0, 1.3, 1.3, "GND")],
                         "CHARGE +5V / GND", "CHARGE_PADS", courtyard=(4.14, 2.07)))
    # JYC720FDRL is the selected off-board FPC motor. The manufacturer confirms a
    # double-sided welding-pad FPC intended for hot-bar attachment, but the public
    # catalog page does not publish the controlled FPC pad geometry. Keep this
    # reserved landing-zone envelope copper-free until that drawing/process arrives.
    fps.append(footprint("J3", "JYC720FDRL FPC hot-bar land gate", 111.0, 102.8, 2.8, 1.6,
                         [], "FPC HOT-BAR LAND / NO COPPER",
                         "JYC720FDRL_HOTBAR_LAND_GATE", courtyard=(3.22, 1.84),
                         attrs="exclude_from_pos_files exclude_from_bom"))
    # Official nPM buck inductors.  Footprint is a conservative 2.0 x 1.6 land placeholder for DFM review.
    for ref, xx, yy, a, b in [
        ("L1", 112.2, 99.4, "SW_BUCK1", "1V8"),
        ("L2", 109.6, 94.0, "SW_BUCK2", "3V0"),
    ]:
        fps.append(footprint(ref, "2.2uH CIGT201610EH2R2MNE", xx, yy, 2.0, 1.6,
                             [pad("1", -0.8, 0, 0.8, 1.4, a), pad("2", 0.8, 0, 0.8, 1.4, b)],
                             "NORDIC REF INDUCTOR", "CIGT201610", courtyard=(2.3, 1.84)))
    # Required exact-value resistors from Nordic Config 4; manufacturer ordering code remains open.
    for ref, val, xx, yy, a, b in [
        ("R3", "47k", 103.5, 97.52, "VSET1", "GND"),
        ("R4", "150k", 104.7, 97.52, "VSET2", "GND"),
        ("R1", "10k", 105.9, 97.52, "3V0", "PMIC_SDA_TO_U1_PAD_TBD"),
        ("R2", "10k", 107.1, 97.52, "3V0", "PMIC_SCL_TO_U1_PAD_TBD"),
        ("R_FLASH_PWR", "0R", 97.2, 101.7, "3V0", "FLASH_VDD"),
        ("R_MIC_A", "0R", 88.7, 103.1, "3V0", "MIC_A_VDD"),
        ("R_MIC_B", "0R", 111.7, 96.7, "3V0", "MIC_B_VDD"),
        ("R_LED", "OPEN", 102.0, 93.55, "STATUS_LED_TO_U1_PAD_TBD", "STATUS_LED_A"),
        ("R_CHG", "0R", 111.5, 106.3, "CHG_5V", "VBUS"),
    ]:
        fps.append(footprint(ref, val, xx, yy, 1.0, 0.5,
                             [pad("1", -0.55, 0, 0.55, 0.55, a), pad("2", 0.55, 0, 0.55, 0.55, b)],
                             "0402 MPN OPEN", "R_0402_OPEN", courtyard=(1.15, 0.575)))
    # Local bypass caps. Exact value is controlled; exact ordering codes are still open.
    cap_defs = [
        ("C1", "1uF/25V", 108.3, 97.52, "VBUS", "GND"),
        ("C2", "10uF", 104.0, 98.35, "VSYS", "GND"),
        ("C3", "10uF", 105.95, 98.35, "VSYS", "GND"),
        ("C4", "10uF", 107.9, 98.35, "VSYS", "GND"),
        ("C5", "1uF", 109.5, 97.52, "VBUSOUT", "GND"),
        ("C6", "2.2uF EMK107BB7225KA-T", 109.85, 98.35, "VBAT", "GND"),
        ("C7", "10uF", 104.0, 99.4, "1V8", "GND"),
        ("C8", "10uF", 105.95, 99.4, "3V0", "GND"),
        ("C9", "10uF", 107.9, 99.4, "LDO1_OUT", "GND"),
        ("C10", "10uF", 109.85, 99.4, "LDO2_OUT", "GND"),
        ("C13", "100nF", 110.7, 97.52, "3V0", "GND"),
        ("C14", "100nF C0402C104M4RAC7867", 103.5, 100.5, "VSYS", "GND"),
        ("C15", "100nF C0402C104M4RAC7867", 104.7, 100.5, "VSYS", "GND"),
        ("C16", "100nF C0402C104M4RAC7867", 105.9, 100.5, "VSYS", "GND"),
        ("C_U4A", "100nF", 94.2, 101.7, "FLASH_VDD", "GND"),
        ("C_U4B", "1uF", 95.7, 101.7, "FLASH_VDD", "GND"),
        ("C_U2", "100nF", 90.0, 105.2, "MIC_A_VDD", "GND"),
        ("C_U3", "100nF", 113.0, 97.3, "MIC_B_VDD", "GND"),
        ("C_U6A", "1uF REG", 102.8, 103.7, "HAPTIC_REG", "GND"),
        ("C_U6B", "1uF VDD", 102.8, 105.0, "3V0", "GND"),
    ]
    for ref, val, xx, yy, a, b in cap_defs:
        size = (1.6, 0.8) if "10uF" in val or "2.2uF" in val else (1.0, 0.5)
        fps.append(footprint(ref, val, xx, yy, *size,
                             [pad("1", -size[0]/2+0.2, 0, 0.45, size[1], a),
                              pad("2", size[0]/2-0.2, 0, 0.45, size[1], b)],
                             "CAP MPN OPEN", "C_OPEN", courtyard=(size[0]*1.15, size[1]*1.15)))
    # Charge input ESD (DPY X1SON) and a low-current LED footprint candidate.
    fps.append(footprint("D1", "TPD1E10B06DPYR", 106.0, 106.4, 1.0, 0.6,
                         [pad("1", -0.30, 0, 0.30, 0.50, "CHG_5V"),
                          pad("2", 0.30, 0, 0.30, 0.50, "GND")],
                         "CHARGE ESD", "X1SON2_DPY", courtyard=(1.15, 0.69)))
    fps.append(footprint("D2", "LED MPN OPEN", 100.0, 93.55, 1.6, 0.8,
                         [pad("1", -0.65, 0, 0.6, 0.7, "STATUS_LED_A"),
                          pad("2", 0.65, 0, 0.6, 0.7, "GND")],
                         "STATUS LED / OPTICS GATE", "LED_1608_OPEN", courtyard=(1.84, 0.92)))
    # 0.65-mm bare test pads. They deliberately expose every bring-up interface.
    tp_nets = [
        "GND", "CHG_5V", "VBUS", "VBAT", "BAT_NTC", "VSYS", "1V8", "3V0", "FLASH_VDD",
        "QSPI_CS_TO_U1_PAD_TBD", "QSPI_CLK_TO_U1_PAD_TBD",
        "QSPI_IO0_TO_U1_PAD_TBD", "QSPI_IO1_TO_U1_PAD_TBD",
        "QSPI_IO2_TO_U1_PAD_TBD", "QSPI_IO3_TO_U1_PAD_TBD",
        "PDM_CLK_TO_U1_PAD_TBD", "PDM_DATA_TO_U1_PAD_TBD", "MIC_A_VDD", "MIC_B_VDD",
        "PMIC_SDA_TO_U1_PAD_TBD", "PMIC_SCL_TO_U1_PAD_TBD",
        "HAPTIC_SDA_TO_U1_PAD_TBD", "HAPTIC_SCL_TO_U1_PAD_TBD", "HAPTIC_EN_TO_U1_PAD_TBD",
        "HAPTIC_REG", "HAPTIC_OUT_P", "HAPTIC_OUT_M", "BUTTON_TO_U1_PAD_TBD",
        "STATUS_LED_TO_U1_PAD_TBD",
        "SWDIO_TO_U1_PAD_TBD", "SWCLK_TO_U1_PAD_TBD", "RESET_TO_U1_PAD_TBD",
        "UART_TX_TO_U1_PAD_TBD", "UART_RX_TO_U1_PAD_TBD",
    ]
    for i, n in enumerate(tp_nets, 1):
        xx = 88.0 + (i % 12) * 2.15
        yy = 94.0 + (i // 12) * 1.55
        fps.append(footprint(f"TP{i}", n, xx, yy, 0.65, 0.65,
                             [pad("1", 0, 0, 0.65, 0.65, n, layer="F.Cu", shape="circle")],
                             "TOP TEST / INSULATE BEFORE CAP", "TP_0P65", courtyard=(0.78, 0.78), side="F"))
    # Board graphics and physical no-metal annotations.
    graphics = '''
  (gr_text "EVT-A / HOLD / NO GERBERS" (at 99.0 92.2) (layer "B.SilkS")
    (effects (font (size 0.8 0.8) (thickness 0.12)) (justify mirror))
    (tstamp 73d2fb40-3b1a-5df2-bd49-45b11523f11d))
  (gr_text "RF 6.5x6.5: NO METAL EXCEPT ANT+MATCH" (at 81.75 95.8) (layer "User.1")
    (effects (font (size 0.45 0.45) (thickness 0.08)))
    (tstamp 4db7f82c-1a34-58cb-a2d0-853494a4ce58))
  (gr_rect (start 78.5 96.75) (end 85.0 103.25)
    (stroke (width 0.15) (type dash)) (fill none) (layer "User.1")
    (tstamp 137c0e90-9b42-5c4b-8fda-91282cce44f9))
  (gr_circle (center 116.9 104.8) (end 121.0 104.8)
    (stroke (width 0.15) (type dash)) (fill none) (layer "Dwgs.User")
    (tstamp 3bce1e19-7b93-5ea2-8a5c-ec4de9abf497))
  (gr_text "JYC720FDRL POCKET / FPC LAND GATE" (at 112.5 108.0) (layer "Dwgs.User")
    (effects (font (size 0.45 0.45) (thickness 0.08)))
    (tstamp f4d28d13-47cf-5a2c-af4a-7bf8c97c6697))
'''
    # Retained candidate outline: 31x14 main + 6.5x6.5 nose, with a 4.10-mm concave motor scallop.
    outline = '''
  (gr_line (start 78.5 96.75) (end 85 96.75) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 6a8b35df-ec1d-5337-b404-1fc89ca90f4e))
  (gr_line (start 85 96.75) (end 85 93) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 5af8b3f0-ac4c-5ba3-a601-d1b9db5fca43))
  (gr_line (start 85 93) (end 116 93) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 247aebd3-5b7e-53a2-8fd1-1f6cc7da0bd8))
  (gr_line (start 116 93) (end 116 100.8) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp de958cc2-c67b-578e-b8b2-c370335ad152))
  (gr_arc (start 116 100.8) (mid 113.1103 103.2400) (end 113.4408 107) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 679b1703-56cb-559d-9cea-cee54a731753))
  (gr_line (start 113.4408 107) (end 85 107) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 449d8d77-0b0d-5b31-a197-f9cb34fe69fb))
  (gr_line (start 85 107) (end 85 103.25) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp 67e55d7b-7a90-5392-a8bb-eeaa859e5adf))
  (gr_line (start 85 103.25) (end 78.5 103.25) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp cdd670c7-c3fa-5ebf-a8b5-8eb79063af68))
  (gr_line (start 78.5 103.25) (end 78.5 96.75) (stroke (width 0.10) (type default)) (layer "Edge.Cuts") (tstamp cb6b4eb9-724b-5584-be2b-742c51209c0b))
'''
    # No routing or pours are emitted: completion would be dishonest while U1 pad map is gated.
    return header + nets + ''.join(fps) + graphics + outline + ')\n'


def sch_symbol_definition(name: str, ref_prefix: str, pins: list[tuple[str, str, str]]) -> str:
    """Return an embedded symbol with exact pin names/numbers and a simple rectangular body."""
    left = [p for p in pins if p[2] != "out"]
    right = [p for p in pins if p[2] == "out"]
    rows = max(len(left), len(right), 2)
    body_h = max(10.16, (rows + 1) * 2.54)
    out = f'''    (symbol {q("Anticipy:"+name)}
      (pin_names (offset 0.8))
      (exclude_from_sim no) (in_bom yes) (on_board yes)
      (property "Reference" {q(ref_prefix)} (at 0 {-body_h/2-2.54:.3f} 0) (effects (font (size 1.27 1.27))))
      (property "Value" {q(name)} (at 0 {-body_h/2-5.08:.3f} 0) (effects (font (size 1.27 1.27))))
      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
      (symbol {q(name+"_0_1")}
        (rectangle (start -10.16 {-body_h/2:.3f}) (end 10.16 {body_h/2:.3f})
          (stroke (width 0) (type default)) (fill (type background))))
      (symbol {q(name+"_1_1")}\n'''
    for side, plist in (("left", left), ("right", right)):
        for i, (num, pname, ptype) in enumerate(plist):
            yy = (i - (len(plist)-1)/2) * 2.54
            if side == "left":
                px, angle = -12.70, 0
            else:
                px, angle = 12.70, 180
            electrical = {"power_in": "power_in", "power_out": "power_out", "out": "output",
                          "input": "input", "bidi": "bidirectional", "passive": "passive"}.get(ptype, "passive")
            out += (
                f'        (pin {electrical} line (at {px:.3f} {yy:.3f} {angle}) (length 2.54) '
                f'(name {q(pname)} (effects (font (size 1.0 1.0)))) '
                f'(number {q(num)} (effects (font (size 1.0 1.0)))))\n'
            )
    out += '      )\n    )\n'
    return out


def make_schematic() -> str:
    # Pins are (number, name/net, electrical type). Labels at the instance pin endpoints create named nets.
    parts = [
        ("U1_GATE", "U", [], "U1", "453-00224R / PINMAP GATE", 45, 50),
        ("NPM1300_CAAA", "U", [
            ("A1","PMIC_LED0","out"),("A2","PMIC_LED1","out"),("A3","PMIC_LED2","out"),
            ("A4","LDO1_OUT","out"),("A5","LDO2_OUT","out"),("A6","GND","power_in"),("A7","GND","power_in"),
            ("B1","VBUS","power_in"),("B2","VBUS","power_in"),("B3","CC2_NC","bidi"),("B4","1V8","power_in"),
            ("B5","3V0","power_in"),("B6","1V8","input"),("B7","SW_BUCK1","out"),
            ("C1","VSYS","power_out"),("C2","VSYS","power_out"),("C3","VBUSOUT","power_out"),
            ("C4","PMIC_GPIO3_TO_U1_PAD_TBD","bidi"),("C5","PMIC_GPIO2_TO_U1_PAD_TBD","bidi"),
            ("C6","3V0","input"),("C7","VSYS","power_in"),("D1","VBAT","power_in"),("D2","VBAT","power_in"),
            ("D3","BAT_NTC","input"),("D4","SHPHLD","bidi"),("D5","CC1_NC","bidi"),
            ("D6","PMIC_GPIO0_TO_U1_PAD_TBD","bidi"),("D7","SW_BUCK2","out"),
            ("E1","VSET2","input"),("E2","VSET1","input"),("E3","PMIC_SCL_TO_U1_PAD_TBD","input"),
            ("E4","3V0","power_in"),("E5","PMIC_SDA_TO_U1_PAD_TBD","bidi"),
            ("E6","PMIC_GPIO1_TO_U1_PAD_TBD","bidi"),("E7","GND","power_in"),
        ], "U5", "nPM1300-CAAA", 90, 85),
        ("W25N04KV", "U", [("1","QSPI_CS_TO_U1_PAD_TBD","input"),("2","QSPI_IO1_TO_U1_PAD_TBD","bidi"),
             ("3","QSPI_IO2_TO_U1_PAD_TBD","bidi"),("4","GND","power_in"),("5","QSPI_IO0_TO_U1_PAD_TBD","bidi"),
             ("6","QSPI_CLK_TO_U1_PAD_TBD","input"),("7","QSPI_IO3_TO_U1_PAD_TBD","bidi"),("8","FLASH_VDD","power_in"),
             ("9","GND","passive")], "U4", "W25N04KVZEIR", 150, 55),
        ("IM69D128S_A", "U", [("1","MIC_A_VDD","power_in"),("2","PDM_CLK_TO_U1_PAD_TBD","input"),
             ("3","PDM_DATA_TO_U1_PAD_TBD","out"),("4","GND","input"),("5","GND","power_in")],
             "U2", "IM69D128S MIC A", 150, 95),
        ("IM69D128S_B", "U", [("1","MIC_B_VDD","power_in"),("2","PDM_CLK_TO_U1_PAD_TBD","input"),
             ("3","PDM_DATA_TO_U1_PAD_TBD","out"),("4","3V0","input"),("5","GND","power_in")],
             "U3", "IM69D128S MIC B", 150, 130),
        ("DRV2605L", "U", [("A1","HAPTIC_EN_TO_U1_PAD_TBD","input"),("A2","3V0","out"),
             ("A3","HAPTIC_OUT_P","out"),("B1","GND","input"),("B2","HAPTIC_SDA_TO_U1_PAD_TBD","bidi"),
             ("B3","GND","power_in"),("C1","HAPTIC_SCL_TO_U1_PAD_TBD","input"),("C2","3V0","power_in"),
             ("C3","HAPTIC_OUT_M","out")], "U6", "DRV2605LYZFR", 210, 55),
        ("ANTENNA", "AE", [("1","RF_MATCH_B","input"),("2","NC_MECH","passive")],
             "ANT1", "2450AT18A0100001E", 210, 100),
        ("CHARGE_ESD", "D", [("1","CHG_5V","bidi"),("2","GND","bidi")],
             "D1", "TPD1E10B06DPYR", 210, 130),
        ("BATTERY_IF", "J", [("1","VBAT","power_out"),("2","BAT_NTC","out"),("3","GND","power_out")],
             "J1", "BAT-ANT-200-001 / SUPPLIER GATE", 45, 105),
        ("CHARGE_IF", "J", [("1","CHG_5V","power_out"),("2","GND","power_out")],
             "J2", "MAGNETIC POGO / SOURCE GATE", 45, 135),
        ("MOTOR_IF", "J", [("1","HAPTIC_OUT_P","input"),("2","HAPTIC_OUT_M","input")],
             "J3", "JYC720FDRL FPC / HOT-BAR LAND GATE", 45, 160),
        ("SW_GATE", "SW", [("TBD_A","BUTTON_TO_U1_PAD_TBD","passive"),("TBD_B","GND","passive")],
             "SW1", "SKSCLCE010 SIDE PUSH / PADMAP GATE", 90, 160),
    ]
    passive_specs = [
        ("L1","L","2.2uH CIGT201610EH2R2MNE","SW_BUCK1","1V8"),
        ("L2","L","2.2uH CIGT201610EH2R2MNE","SW_BUCK2","3V0"),
        ("R1","R","10k pull-up / MPN OPEN","3V0","PMIC_SDA_TO_U1_PAD_TBD"),
        ("R2","R","10k pull-up / MPN OPEN","3V0","PMIC_SCL_TO_U1_PAD_TBD"),
        ("R3","R","47k VSET1 / MPN OPEN","VSET1","GND"),
        ("R4","R","150k VSET2 / MPN OPEN","VSET2","GND"),
        ("R_FLASH_PWR","R","0R flash isolation","3V0","FLASH_VDD"),
        ("R_MIC_A","R","0R mic A isolation","3V0","MIC_A_VDD"),
        ("R_MIC_B","R","0R mic B isolation","3V0","MIC_B_VDD"),
        ("R_LED","R","LED current set / VALUE OPEN","STATUS_LED_TO_U1_PAD_TBD","STATUS_LED_A"),
        ("R_CHG","R","0R charge isolation","CHG_5V","VBUS"),
        ("C1","C","1uF 25V / MPN OPEN","VBUS","GND"),
        ("C2","C","10uF / MPN OPEN","VSYS","GND"),
        ("C3","C","10uF / MPN OPEN","VSYS","GND"),
        ("C4","C","10uF / MPN OPEN","VSYS","GND"),
        ("C5","C","1uF / MPN OPEN","VBUSOUT","GND"),
        ("C6","C","2.2uF EMK107BB7225KA-T","VBAT","GND"),
        ("C7","C","10uF / MPN OPEN","1V8","GND"),
        ("C8","C","10uF / MPN OPEN","3V0","GND"),
        ("C9","C","10uF / MPN OPEN","LDO1_OUT","GND"),
        ("C10","C","10uF / MPN OPEN","LDO2_OUT","GND"),
        ("C13","C","100nF / MPN OPEN","3V0","GND"),
        ("C14","C","100nF C0402C104M4RAC7867","VSYS","GND"),
        ("C15","C","100nF C0402C104M4RAC7867","VSYS","GND"),
        ("C16","C","100nF C0402C104M4RAC7867","VSYS","GND"),
        ("C_U4A","C","100nF / MPN OPEN","FLASH_VDD","GND"),
        ("C_U4B","C","1uF / MPN OPEN","FLASH_VDD","GND"),
        ("C_U2","C","100nF / MPN OPEN","MIC_A_VDD","GND"),
        ("C_U3","C","100nF / MPN OPEN","MIC_B_VDD","GND"),
        ("C_U6A","C","1uF REG","HAPTIC_REG","GND"),
        ("C_U6B","C","1uF VDD","3V0","GND"),
        ("C_RF1","C","DNP/TUNE; eval 1.0pF","RF_FEED_TO_U1_PAD_TBD","RF_MATCH_A"),
        ("L_RF1","L","DNP/TUNE; eval 2.7nH","RF_MATCH_A","GND"),
        ("L_RF2","L","DNP/TUNE; eval 3.9nH","RF_MATCH_A","RF_MATCH_B"),
        ("D2","D","STATUS LED / MPN OPEN","STATUS_LED_A","GND"),
    ]
    for idx, (ref, prefix, value, net_a, net_b) in enumerate(passive_specs):
        col, row = divmod(idx, 12)
        parts.append((f"{prefix}_{ref}_BLOCK", prefix,
                      [("1",net_a,"passive"),("2",net_b,"passive")],
                      ref, value, 260 + col*55, 35 + row*15))
    # Build unique library symbols by pin signature.
    lib_defs: dict[str, tuple[str, list[tuple[str,str,str]]]] = {}
    for name, prefix, pins, *_ in parts:
        lib_defs[name] = (prefix, pins)
    root_uuid = uid("schematic-root")
    out = f'''(kicad_sch (version 20231120) (generator eeschema)
  (uuid {root_uuid})
  (paper "A3")
  (title_block (title "Anticipy EVT-A electrical architecture") (date "2026-08-28")
    (rev "EVT-A CHECKPOINT") (company "Anticipy")
    (comment 1 "Labels are electrical connections; U1/SW1/J3 land maps deliberately gated"))
  (lib_symbols
'''
    for name, (prefix, pins) in lib_defs.items():
        out += sch_symbol_definition(name, prefix, pins)
    out += '  )\n'
    for idx, (name, prefix, pins, ref, value, x, y) in enumerate(parts):
        inst_uid = uid(f"sch-{ref}")
        left = [p for p in pins if p[2] != "out"]
        right = [p for p in pins if p[2] == "out"]
        rows = max(len(left), len(right), 2)
        body_h = max(10.16, (rows + 1) * 2.54)
        out += f'''  (symbol (lib_id {q("Anticipy:"+name)}) (at {x:.3f} {y:.3f} 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no) (uuid {inst_uid})
    (property "Reference" {q(ref)} (at {x:.3f} {y-body_h/2-2.54:.3f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" {q(value)} (at {x:.3f} {y-body_h/2-5.08:.3f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "" (at {x:.3f} {y:.3f} 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "" (at {x:.3f} {y:.3f} 0) (effects (font (size 1.27 1.27)) hide))
'''
        # Instance pin UUIDs, followed by labels exactly at pin connection endpoints.
        for num, _, _ in pins:
            out += f'    (pin {q(num)} (uuid {uid(ref+"-pin-"+num)}))\n'
        out += f'''    (instances (project {q(PROJECT)} (path {q("/"+root_uuid+"/"+inst_uid)} (reference {q(ref)}) (unit 1))))
  )
'''
        for side, plist in (("left", left), ("right", right)):
            for i, (num, pname, _ptype) in enumerate(plist):
                yy = y + (i - (len(plist)-1)/2) * 2.54
                xx = x - 12.70 if side == "left" else x + 12.70
                angle = 180 if side == "left" else 0
                justify = " (justify right bottom)" if side == "left" else " (justify left bottom)"
                out += (
                    f'  (label {q(pname)} (at {xx:.3f} {yy:.3f} {angle}) '
                    f'(effects (font (size 0.9 0.9)){justify}) (uuid {uid(ref+num+pname+"label")}))\n'
                )
    notes = [
        (35, 25, "DESIGN CHECKPOINT — NOT FOR FABRICATION"),
        (35, 30, "U1, SW1 and J3 contain NO COPPER PADS until official module/button/FPC land drawings are imported."),
        (35, 35, "All labels with _TO_U1_PAD_TBD stop at named test pads. No guessed module pinout exists."),
        (35, 185, "POWER: 5V pogo → nPM1300 → 3V0 digital rail; optional 1V8 rail. Do not tie buck outputs."),
        (35, 190, "STORAGE: W25N04KVZEIR = 4 Gbit raw NAND. Firmware must handle ECC, bad blocks, power loss, and reserve."),
        (35, 195, "RF: Johanson network values are tune slots only. Closed-enclosure VNA work is mandatory."),
    ]
    for i, (x, y, text) in enumerate(notes):
        out += f'  (text {q(text)} (exclude_from_sim no) (at {x} {y} 0) (effects (font (size 1.2 1.2))) (uuid {uid("note"+str(i))}))\n'
    out += f'  (sheet_instances (path "/" (page "1")))\n)\n'
    return out


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def extract_balanced_forms(text: str, marker: str) -> list[str]:
    """Extract balanced S-expression forms beginning with marker, respecting quoted strings."""
    forms: list[str] = []
    start = 0
    while True:
        pos = text.find(marker, start)
        if pos < 0:
            break
        depth = 0
        quoted = False
        escaped = False
        end = pos
        for end in range(pos, len(text)):
            ch = text[end]
            if quoted:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    quoted = False
                continue
            if ch == '"':
                quoted = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    forms.append(text[pos:end + 1])
                    start = end + 1
                    break
        else:
            raise RuntimeError(f"Unbalanced form beginning {marker!r} at byte {pos}")
    return forms


def write_embedded_libraries(board_text: str, schematic_text: str) -> None:
    """Write reusable native libraries from the exact forms embedded in the project."""
    # The directory is generator-owned; remove stale renamed footprints deterministically.
    for stale in (ROOT / "libraries/Anticipy.pretty").glob("*.kicad_mod"):
        stale.unlink()
    wanted = {"U1", "U2", "U4", "U5", "U6", "ANT1", "SW1", "J3"}
    for form in extract_balanced_forms(board_text, '(footprint "Anticipy:'):
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', form)
        name_match = re.match(r'\(footprint "Anticipy:([^"]+)"', form)
        if not ref_match or not name_match or ref_match.group(1) not in wanted:
            continue
        name = name_match.group(1)
        standalone = re.sub(
            r'^\(footprint "Anticipy:[^"]+"',
            f'(footprint "{name}" (version 20240108) (generator pcbnew)',
            form,
            count=1,
        )
        standalone = re.sub(r'\s+\(at [-+0-9.]+ [-+0-9.]+\)', '', standalone, count=1)
        write_text(ROOT / f"libraries/Anticipy.pretty/{name}.kicad_mod", standalone + "\n")

    # Reuse the embedded definitions so symbol pin maps cannot drift from the schematic.
    lib_start = schematic_text.index("  (lib_symbols")
    # All symbol definitions inside this block begin with six spaces in generated text.
    symbol_forms = extract_balanced_forms(schematic_text[lib_start:], '    (symbol "Anticipy:')
    cleaned = []
    for form in symbol_forms:
        cleaned.append(form.replace('(symbol "Anticipy:', '(symbol "', 1))
    symbol_lib = '(kicad_symbol_lib (version 20231120) (generator kicad_symbol_editor)\n' + "\n".join(cleaned) + '\n)\n'
    write_text(ROOT / "libraries/Anticipy.kicad_sym", symbol_lib)


def make_manifest() -> dict:
    return {
        "project": PROJECT,
        "status": "EVT-A design checkpoint; fabrication prohibited",
        "board": {
            "thickness_mm": 0.6,
            "layers": 4,
            "cad_to_kicad": "Kx=100+CADx; Ky=100-CADy",
            "overall_bounds_mm": [78.5, 93.0, 116.0, 107.0],
            "overall_size_mm": [37.5, 14.0],
            "rf_nose_mm": [6.5, 6.5],
            "motor_scallop": {"center": [116.9, 104.8], "radius_mm": 4.1},
        },
        "major_blocks": [
            {"ref":"U1","center":[89.4,97.7],"size":[6.3,7.9],"margin":1.15,"gate":"PINMAP"},
            {"ref":"U4","center":[98.3,97.6],"size":[8.0,6.0],"margin":1.15},
            {"ref":"U5","center":[106.2,95.8],"size":[5.6,4.8],"margin":1.15,"note":"system reserve"},
            {"ref":"U6","center":[104.8,104.7],"size":[3.8,3.2],"margin":1.15,"note":"system reserve"},
            {"ref":"U2","center":[87.2,105.2],"size":[3.5,2.65],"margin":1.15},
            {"ref":"U3","center":[113.8,94.8],"size":[3.5,2.65],"margin":1.15},
            {"ref":"ANT1","center":[79.55,100.0],"size":[1.6,3.2],"margin":1.15},
            {"ref":"SW1","center":[100.0,104.95],"size":[3.5,3.55],"margin":1.15,
             "gate":"PADMAP","note":"actuator faces +KiCad Y / -mechanical CAD Y"},
        ],
        "required_nets": NETS,
        "gated_footprints": {"U1": 0, "SW1": 0, "J3": 0},
        "verified_pad_counts": {"U2": 6, "U3": 6, "U4": 9, "U5": 35, "U6": 9, "ANT1": 2},
        "release_gates": [
            "Import official Ezurio 453-00224R footprint, symbol, pinout and host schematic; then route.",
            "Obtain Alps SKSCLCE010 formal delivery drawing; replace the zero-pad side-push envelope and couple it to the measured plunger stack.",
            "Obtain the controlled JYC720FDRL FPC/hot-bar drawing and approved process window; replace J3's zero-pad landing-zone gate.",
            "Approve exact battery supplier drawing, wire polarity, NTC, protection and certifications.",
            "Select exact passive/LED orderable MPNs and obtain assembly DFM for 0.60-mm four-layer board.",
            "Re-export the retained mechanical PCB STEP/DXF with the motor scallop; the earlier straight-edge STEP is superseded.",
            "Complete routing, pours, impedance/stack-up, ERC, DRC, RF VNA tuning and physical EVT tests.",
        ],
    }


def make_bom_rows() -> list[list[str]]:
    return [
        ["U1","1","Ezurio","453-00224R","BL54L15U BLE module","6.3x7.9x1.75 mm","HOLD: official account-gated pad map not imported"],
        ["U2,U3","2","Infineon","IM69D128S","69 dB SNR bottom-port PDM microphone","3.5x2.65x1.0 mm","PIN/FOOTPRINT VERIFIED; acoustic stack open"],
        ["U4","1","Winbond","W25N04KVZEIR","4-Gbit SPI NAND","8-WSON 8x6","PIN/FOOTPRINT VERIFIED; raw NAND firmware required"],
        ["U5","1","Nordic Semiconductor","nPM1300-CAAA","PMIC / charger","35-ball WLCSP","PIN/FOOTPRINT/REFERENCE TOPOLOGY VERIFIED"],
        ["U6","1","Texas Instruments","DRV2605LYZFR","Haptic driver","9-DSBGA","PIN MAP VERIFIED; assembly land review open"],
        ["ANT1","1","Johanson Technology","2450AT18A0100001E","2.4 GHz chip antenna","3.2x1.6x1.3 mm","VERIFIED; final match requires closed-unit VNA"],
        ["C_RF1","1","Johanson Technology","QSCF500Q1R0B1GV001T","1.0 pF evaluation match candidate","0402","DNP/TUNE; not a final product value"],
        ["L_RF1","1","Johanson Technology","LRC0402CS2N7GV001T","2.7 nH evaluation shunt candidate","0402","DNP/TUNE; not a final product value"],
        ["L_RF2","1","Johanson Technology","LRC0402CS3N9GV001T","3.9 nH evaluation series candidate","0402","DNP/TUNE; not a final product value"],
        ["L1,L2","2","Samsung Electro-Mechanics","CIGT201610EH2R2MNE","2.2 uH buck inductor","2016 metric","EXACT Nordic Config 4 reference BOM"],
        ["C6","1","Taiyo Yuden","EMK107BB7225KA-T","2.2 uF X7R 16 V","0603","EXACT Nordic Config 4 reference BOM"],
        ["C14,C15,C16","3","KEMET","C0402C104M4RAC7867","100 nF X7R 16 V 20%","0402","EXACT Nordic Config 4 HF-decoupling BOM; board placement open"],
        ["D1","1","Texas Instruments","TPD1E10B06DPYR","Bidirectional charge-input ESD","2-X1SON DPY","PIN/PACKAGE VERIFIED; land DFM review"],
        ["SW1","1","Alps Alpine","SKSCLCE010","Side-push tactile switch, 1.6 N, 0.2 mm travel","3.5x3.55x1.25 mm","BODY/ORIENTATION VERIFIED; formal delivery drawing/pad map gate"],
        ["J3/M1","1","JIE YI Electronics","JYC720FDRL (family JYC0720FDRL)","3 V FPC coin ERM motor; hot-bar attachment","7 mm dia x 2 mm","OFF BOARD; exact FPC land and hot-bar process drawing gate; J3 has zero copper"],
        ["J1/BT1","1","TBD","BAT-ANT-200-001","Protected 1S 200 mAh, 10k NTC","max 26x12.5x6 mm","CONTROLLED PLACEHOLDER; supplier/certification gate"],
        ["R3","1","OPEN","OPEN","47k VSET1","0402","VALUE VERIFIED from Nordic Config 4; MPN open"],
        ["R4","1","OPEN","OPEN","150k VSET2","0402","VALUE VERIFIED from Nordic Config 4; MPN open"],
        ["R1,R2","2","OPEN","OPEN","10k TWI pull-ups","0402","VALUE VERIFIED from Nordic Config 4; MPN open"],
        ["R_FLASH_PWR,R_MIC_A,R_MIC_B,R_CHG","4","OPEN","OPEN","0 ohm debug/isolation","0402","ENGINEERING CHOICE; MPN open"],
        ["R_LED","1","OPEN","OPEN","Status LED current-set resistor","0402","VALUE OPEN until exact LED/current budget is frozen"],
        ["C1-C5,C7-C10,C13,C_U2,C_U3,C_U4A,C_U4B,C_U6A,C_U6B","16","OPEN","OPEN","Reference/bypass capacitors as schematic","0402/0603","VALUES CONTROLLED; exact MPNs and derating open"],
        ["D2","1","OPEN","OPEN","Low-current status LED","1608 metric candidate","OPTICAL/MPN/current gate"],
    ]


def main() -> None:
    for d in ("libraries/Anticipy.pretty", "bom", "docs", "reports"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    board_text = make_board()
    schematic_text = make_schematic()
    write_text(ROOT / f"{PROJECT}.kicad_pcb", board_text)
    write_text(ROOT / f"{PROJECT}.kicad_sch", schematic_text)
    write_embedded_libraries(board_text, schematic_text)
    write_text(ROOT / f"{PROJECT}.kicad_pro", json.dumps({
        "board": {}, "boards": [], "cvpcb": {}, "erc": {}, "libraries": {},
        "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
        "net_settings": {"classes": [], "meta": {"version": 3}},
        "pcbnew": {}, "schematic": {}, "text_variables": {
            "FAB_STATUS": "HOLD - NO GERBERS", "REVISION": "EVT-A CHECKPOINT"
        }
    }, indent=2) + "\n")
    write_text(ROOT / f"{PROJECT}.kicad_dru", '''(version 1)
(rule "EVT-A minimum copper clearance"
  (constraint clearance (min 0.1000mm)))
(rule "EVT-A minimum track width"
  (constraint track_width (min 0.1000mm)))
(rule "EVT-A minimum via"
  (constraint via_diameter (min 0.3000mm))
  (constraint hole_size (min 0.1500mm)))
(rule "WLCSP local clearance candidate"
  (condition "A.Reference == 'U5'")
  (constraint clearance (min 0.0800mm)))
''')
    write_text(ROOT / "fp-lib-table", '(fp_lib_table (lib (name "Anticipy")(type "KiCad")(uri "${KIPRJMOD}/libraries/Anticipy.pretty")(options "")(descr "Anticipy controlled footprints")))\n')
    write_text(ROOT / "sym-lib-table", '(sym_lib_table (lib (name "Anticipy")(type "KiCad")(uri "${KIPRJMOD}/libraries/Anticipy.kicad_sym")(options "")(descr "Anticipy controlled symbols")))\n')
    manifest = make_manifest()
    write_text(ROOT / "design_manifest.json", json.dumps(manifest, indent=2) + "\n")
    with (ROOT / "bom/EVT_A_BOM.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["References","Qty","Manufacturer","MPN","Description","Package","Verification/status"])
        writer.writerows(make_bom_rows())
    # Explicit non-results make it impossible to mistake a parser check for KiCad ERC/DRC.
    write_text(ROOT / "reports/ERC_NOT_RUN.txt", "NOT RUN: kicad-cli is not installed in this runtime. No ERC result is claimed.\nOpen the project in KiCad after importing the gated U1/SW1/J3 vendor definitions and run unfiltered ERC.\n")
    write_text(ROOT / "reports/DRC_NOT_RUN.txt", "NOT RUN: kicad-cli is not installed in this runtime. No DRC result is claimed.\nThe board is intentionally unrouted while the U1 and J3 land maps are gated; Gerbers must not be generated.\n")


if __name__ == "__main__":
    main()
