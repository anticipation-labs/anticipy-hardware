#!/usr/bin/env python3
"""Generate the Anticipy ANT-PROD-R0 EVT KiCad PCB.

Run with the system Python shipped with KiCad:
    /usr/bin/python3 generate_board.py

This generator deliberately keeps the board reproducible. Manufacturer-library
footprints are used where KiCad supplies them; the four small footprints that
are not in KiCad 7 are generated from their manufacturer drawings below.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import pcbnew


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Anticipy_PROD_R0_EVT.kicad_pcb"
FP_ROOT = Path("/usr/share/kicad/footprints")


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def vec(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


board = pcbnew.BOARD()
board.GetDesignSettings().SetCopperLayerCount(4)
board.GetDesignSettings().SetBoardThickness(mm(0.8))


def add_net(name: str) -> pcbnew.NETINFO_ITEM:
    net = pcbnew.NETINFO_ITEM(board, name)
    board.Add(net)
    return net


NET_NAMES = [
    "GND", "VBUS", "VBUSOUT", "VBAT", "NTC", "VSYS", "3V_MAIN",
    "3V_SD", "3V_MIC", "LDO2_OUT", "SW1", "SW2", "VSET1", "VSET2",
    "USB_CC1", "USB_CC2", "USB_D+", "USB_D-", "I2C_SCL", "I2C_SDA",
    "PMIC_INT", "ACC_INT1", "ACC_INT2", "PDM_CLK", "PDM_DATA",
    "PDM_DATA_MIC1", "PDM_DATA_MIC2", "SD_SCK_MCU", "SD_SCK_CARD",
    "SD_MOSI_MCU", "SD_MOSI_CARD", "SD_MISO_MCU", "SD_MISO_CARD",
    "SD_CS", "SD_DETECT", "USER_BTN", "HAPTIC_PWM", "HAPTIC_GATE",
    "HAPTIC_NEG", "LED_BLUE_K", "LED_RED_K", "SWDIO",
    "SWDCLK", "RESET", "UART_TX", "UART_RX",
]
NET = {name: add_net(name) for name in NET_NAMES}


def load_fp(lib: str, name: str, ref: str, value: str, x: float, y: float,
            rot: float = 0.0, bottom: bool = False) -> pcbnew.FOOTPRINT:
    fp = pcbnew.FootprintLoad(str(FP_ROOT / f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"Footprint not found: {lib}:{name}")
    fp.SetReference(ref)
    fp.SetValue(value)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(rot)
    board.Add(fp)
    if bottom:
        fp.Flip(fp.GetPosition(), False)
    return fp


def add_smd_pad(fp: pcbnew.FOOTPRINT, number: str, x: float, y: float,
                sx: float, sy: float, shape=pcbnew.PAD_SHAPE_ROUNDRECT) -> pcbnew.PAD:
    pad = pcbnew.PAD(fp)
    pad.SetNumber(str(number))
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(shape)
    if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
        pad.SetRoundRectRadiusRatio(0.18)
    pad.SetSize(vec(sx, sy))
    pad.SetPosition(vec(x, y))
    pad.SetPos0(vec(x, y))
    pad.SetLayerSet(pad.SMDMask())
    fp.Add(pad)
    return pad


def add_npth(fp: pcbnew.FOOTPRINT, x: float, y: float, diameter: float) -> pcbnew.PAD:
    pad = pcbnew.PAD(fp)
    pad.SetNumber("")
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE)
    pad.SetSize(vec(diameter, diameter))
    pad.SetDrillSize(vec(diameter, diameter))
    pad.SetPosition(vec(x, y))
    pad.SetPos0(vec(x, y))
    pad.SetLayerSet(pad.UnplatedHoleMask())
    fp.Add(pad)
    return pad


def custom_fp(ref: str, value: str, x: float, y: float, rot: float = 0.0) -> pcbnew.FOOTPRINT:
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(ref)
    fp.SetValue(value)
    board.Add(fp)
    return fp


def place_custom(fp: pcbnew.FOOTPRINT, x: float, y: float, rot: float = 0.0) -> None:
    # Newly-created pad coordinates are absolute until the footprint is moved.
    # Add all local geometry at the origin, then rotate and translate as one item.
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(vec(x, y))


def add_outline_box(fp: pcbnew.FOOTPRINT, width: float, height: float) -> None:
    pts = [(-width / 2, -height / 2), (width / 2, -height / 2),
           (width / 2, height / 2), (-width / 2, height / 2)]
    for a, b in zip(pts, pts[1:] + pts[:1]):
        shape = pcbnew.FP_SHAPE(fp)
        shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
        shape.SetStart(vec(*a))
        shape.SetEnd(vec(*b))
        shape.SetLayer(pcbnew.F_SilkS)
        shape.SetWidth(mm(0.12))
        fp.Add(shape)


def fp_npm1300(ref: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    # Nordic QEAA: QFN32, 5 x 5 mm, 0.5 mm pitch, 3.5 mm exposed pad.
    fp = load_fp("Package_DFN_QFN", "QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm",
                 ref, "NPM1300-QEAA-R7", x, y)
    return fp


def fp_mic(ref: str, x: float, y: float, rot: float = 0.0) -> pcbnew.FOOTPRINT:
    # Infineon PG-TLGA-5-2. Copper pads follow Fig. 13; 0.60 mm PCB sound hole.
    fp = custom_fp(ref, "IM69D128SV01XTMA1", x, y, rot)
    add_outline_box(fp, 2.65, 3.50)
    # Origin is package centre. Pin positions are bottom-view manufacturer coordinates.
    add_smd_pad(fp, "1", +0.8375, +1.1585, 0.75, 0.54)
    add_smd_pad(fp, "2", +0.8375, +0.3365, 0.75, 0.54)
    add_smd_pad(fp, "3", -0.8375, +1.1585, 0.75, 0.54)
    add_smd_pad(fp, "4", -0.8375, +0.3365, 0.75, 0.54)
    # Pin 5 is the annular GND terminal around the sound port. Four pads approximate
    # the manufacturer annular recommendation without covering the acoustic hole.
    for dx, dy in [(0, -0.91), (+0.74, -0.36), (0, +0.19), (-0.74, -0.36)]:
        add_smd_pad(fp, "5", dx, dy, 0.62, 0.30)
    add_npth(fp, 0, -0.36, 0.60)
    place_custom(fp, x, y, rot)
    return fp


def fp_led(ref: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    # Kingbright APHB1608LVBDSEKJ3C, recommended 0.5 x 0.4 mm lands.
    fp = custom_fp(ref, "APHB1608LVBDSEKJ3C", x, y)
    add_outline_box(fp, 1.6, 0.8)
    add_smd_pad(fp, "1", +0.60, +0.35, 0.50, 0.40)  # blue cathode
    add_smd_pad(fp, "2", -0.60, +0.35, 0.50, 0.40)  # blue anode
    add_smd_pad(fp, "3", +0.60, -0.35, 0.50, 0.40)  # red cathode
    add_smd_pad(fp, "4", -0.60, -0.35, 0.50, 0.40)  # red anode
    place_custom(fp, x, y)
    return fp


def fp_tpd2(ref: str, x: float, y: float, rot: float = 0.0) -> pcbnew.FOOTPRINT:
    # TI DRT (S-PDSO-N3) official land pattern 4211172/A.
    # Three 0.30 mm square lands; 0.70 mm column, 1.15/0.85 mm row spacing.
    fp = custom_fp(ref, "TPD2EUSB30DRTR", x, y, rot)
    add_outline_box(fp, 1.0, 0.8)
    add_smd_pad(fp, "1", +0.35, -0.575, 0.30, 0.30)
    add_smd_pad(fp, "2", +0.35, +0.575, 0.30, 0.30)
    add_smd_pad(fp, "3", -0.35, +0.275, 0.30, 0.30)
    place_custom(fp, x, y, rot)
    return fp


def fp_solder_3(ref: str, value: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    fp = custom_fp(ref, value, x, y)
    add_outline_box(fp, 4.0, 2.2)
    for n, px in enumerate((-1.25, 0.0, 1.25), 1):
        add_smd_pad(fp, str(n), px, 0, 0.8, 1.4)
    place_custom(fp, x, y)
    return fp


def fp_solder_2(ref: str, value: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    fp = custom_fp(ref, value, x, y)
    add_outline_box(fp, 3.0, 2.2)
    add_smd_pad(fp, "1", -0.75, 0, 0.8, 1.4)
    add_smd_pad(fp, "2", +0.75, 0, 0.8, 1.4)
    place_custom(fp, x, y)
    return fp


def fp_testpad(ref: str, value: str, x: float, y: float) -> pcbnew.FOOTPRINT:
    fp = custom_fp(ref, value, x, y)
    add_smd_pad(fp, "1", 0, 0, 1.0, 1.0, pcbnew.PAD_SHAPE_CIRCLE)
    place_custom(fp, x, y)
    return fp


# ---- Placement -----------------------------------------------------------

# Rotate 270 degrees so the ceramic-antenna keepout is at the right board edge.
U1 = load_fp("RF_Module", "Raytac_MDBT50Q", "U1", "MDBT50Q-1MV2", 61.0, 30.0, 270)
U2 = fp_npm1300("U2", 31.2, 30.0)
U3 = load_fp("Package_LGA", "LGA-12_2x2mm_P0.5mm", "U3", "LIS2DW12TR", 48.0, 36.1)
U4 = fp_tpd2("U4", 25.8, 30.0, 90)
MIC1 = fp_mic("MIC1", 38.0, 22.3, 0)
MIC2 = fp_mic("MIC2", 51.0, 22.3, 0)
J1 = load_fp("Connector_USB", "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
             "J1", "USB4105-GF-A", 20.6, 30.0, 270)
J2 = load_fp("Connector_Card", "microSD_HC_Molex_104031-0811",
             "J2", "104031-0811", 43.0, 30.2, 0, bottom=True)
SW_USER = load_fp("Button_Switch_SMD", "SW_SPST_B3U-1000P", "SW1", "B3U-1000P", 31.0, 37.0)
LED1 = fp_led("LED1", 27.0, 37.2)
Q1 = load_fp("Package_TO_SOT_SMD", "SOT-23", "Q1", "AO3400A", 37.0, 37.0, 180)
D1 = load_fp("Diode_SMD", "D_SOD-323", "D1", "1N4148W-HF", 40.2, 37.0)
BT1 = fp_solder_3("BT1", "LiPo_1S_PROTECTED_NTC", 45.0, 37.4)
M1 = fp_solder_2("M1", "VCLP1020B002L", 34.5, 37.0)

L1 = load_fp("Inductor_SMD", "L_Murata_DFE201610P", "L1", "2.2uH CIGT201610EH2R2MNE", 37.0, 27.2)
L2 = load_fp("Inductor_SMD", "L_Murata_DFE201610P", "L2", "2.2uH CIGT201610EH2R2MNE", 37.0, 32.8)


def add_r(ref: str, value: str, x: float, y: float, rot: float = 0,
          bottom: bool = False) -> pcbnew.FOOTPRINT:
    return load_fp("Resistor_SMD", "R_0402_1005Metric", ref, value, x, y, rot, bottom)


def add_c(ref: str, value: str, x: float, y: float, size: str = "0402", rot: float = 0,
          bottom: bool = False) -> pcbnew.FOOTPRINT:
    names = {"0402": "C_0402_1005Metric", "0603": "C_0603_1608Metric", "0805": "C_0805_2012Metric"}
    return load_fp("Capacitor_SMD", names[size], ref, value, x, y, rot, bottom)


# nPM1300 reference passives, arranged close to the relevant pins.
C1 = add_c("C1", "1uF 16V X7R", 35.7, 29.0, "0603")
C2 = add_c("C2", "10uF 10V X5R", 27.0, 27.3, "0603", 90)
C3 = add_c("C3", "10uF 10V X5R", 29.0, 30.0, "0603", 90, bottom=True)
C4 = add_c("C4", "10uF 10V X5R", 27.0, 32.7, "0603", 90)
C5 = add_c("C5", "1uF 10V X7R", 35.7, 31.0, "0603")
C6 = add_c("C6", "2.2uF 16V X7R EMK107BB7225KA-T", 31.2, 30.0, "0603", bottom=True)
C7 = add_c("C7", "10uF 10V X5R", 39.5, 27.2, "0603", 90)
C8 = add_c("C8", "10uF 10V X5R", 39.5, 32.8, "0603", 90)
C9 = add_c("C9", "10uF 10V X5R", 29.0, 24.0, "0603", 90)
C10 = add_c("C10", "10uF 10V X5R", 30.8, 24.0, "0603", 90)
C11 = add_c("C11", "10uF 10V X5R", 32.6, 24.0, "0603", 90)
C12 = add_c("C12", "10uF 10V X5R", 34.4, 24.0, "0603", 90)
C13 = add_c("C13", "100nF 6.3V X7R", 34.8, 34.1)
C14 = add_c("C14", "100nF 6.3V X7R C0402C104M4RAC7867", 27.2, 28.0, rot=90, bottom=True)
C15 = add_c("C15", "100nF 6.3V X7R C0402C104M4RAC7867", 27.2, 30.0, rot=90, bottom=True)
C16 = add_c("C16", "100nF 6.3V X7R C0402C104M4RAC7867", 27.2, 32.0, rot=90, bottom=True)
C17 = add_c("C17", "1uF MIC BYPASS", 40.8, 22.3, "0603")
C18 = add_c("C18", "1uF MIC BYPASS", 53.8, 22.3, "0603")
C19 = add_c("C19", "10uF MCU BULK", 53.8, 35.8, "0603")
C20 = add_c("C20", "100nF ACC BYPASS", 50.0, 36.1)
C21 = add_c("C21", "47uF SD BULK", 38.4, 38.0, "0805", bottom=True)
C22 = add_c("C22", "100nF SD BYPASS", 35.8, 38.0, bottom=True)
C23 = add_c("C23", "100nF MOTOR", 39.0, 35.2)
C24 = add_c("C24", "47uF MOTOR BULK", 33.1, 38.0, "0805", bottom=True)

R1 = add_r("R1", "10k I2C", 32.5, 34.2)
R2 = add_r("R2", "10k I2C", 30.7, 34.2)
R3 = add_r("R3", "330k 1% BUCK1=2.7V START", 28.8, 35.0, bottom=True)
R4 = add_r("R4", "150k 1% BUCK2=3.0V", 30.8, 35.0, bottom=True)
R5 = add_r("R5", "5.1k USB CC1", 24.0, 23.7)
R6 = add_r("R6", "5.1k USB CC2", 26.0, 23.7)
R7 = add_r("R7", "100k SD CS PULLUP", 41.0, 38.0, bottom=True)
R8 = add_r("R8", "22R SD SCK", 43.2, 38.0, bottom=True)
R9 = add_r("R9", "22R SD MOSI", 45.4, 38.0, bottom=True)
R10 = add_r("R10", "22R SD MISO", 47.6, 38.0, bottom=True)
R11 = add_r("R11", "100k BUTTON PULLUP", 32.3, 35.5)
R12 = add_r("R12", "100R HAPTIC GATE", 36.7, 38.6)
R13 = add_r("R13", "100k HAPTIC PULLDOWN", 38.5, 38.6)
R14 = add_r("R14", "100R MIC1 DATA", 41.2, 23.3)
R15 = add_r("R15", "100R MIC2 DATA", 54.2, 23.3)

# Seven pogo pads: SWD plus serial diagnostics.
TEST_NETS = [("TP1", "SWDIO"), ("TP2", "SWDCLK"), ("TP3", "RESET"),
             ("TP4", "3V_MAIN"), ("TP5", "GND"), ("TP6", "UART_TX"), ("TP7", "UART_RX")]
TESTS = []
for i, (ref, name) in enumerate(TEST_NETS):
    tp = fp_testpad(ref, name, 49.5 + i * 1.5, 38.3)
    tp.Flip(tp.GetPosition(), False)
    TESTS.append(tp)


def set_net(fp: pcbnew.FOOTPRINT, pad_number: str, name: str) -> None:
    pads = [p for p in fp.Pads() if p.GetNumber() == str(pad_number)]
    if not pads:
        raise KeyError(f"{fp.GetReference()} pad {pad_number} missing")
    for pad in pads:
        pad.SetNet(NET[name])


def set_many(fp: pcbnew.FOOTPRINT, mapping: dict[str, str]) -> None:
    for pad, net in mapping.items():
        set_net(fp, pad, net)


# Raytac authoritative application pin map.
set_many(U1, {
    "1": "GND", "2": "GND", "15": "GND", "33": "GND", "55": "GND",
    "28": "3V_MAIN", "30": "3V_MAIN", "32": "VBUS",
    "34": "USB_D-", "35": "USB_D+", "16": "I2C_SDA", "19": "I2C_SCL",
    "38": "PDM_CLK", "39": "PDM_DATA", "37": "SD_SCK_MCU", "36": "SD_MOSI_MCU",
    "29": "SD_MISO_MCU", "27": "SD_CS", "45": "SD_DETECT", "24": "HAPTIC_PWM",
    "22": "USER_BTN", "41": "PMIC_INT", "44": "ACC_INT1", "43": "ACC_INT2",
    "40": "RESET", "51": "SWDIO", "53": "SWDCLK", "21": "UART_TX", "20": "UART_RX",
})

# Nordic nPM1300 QEAA pin map from official reference schematic.
set_many(U2, {
    "1": "3V_MAIN", "2": "GND", "3": "SW1", "4": "VSYS", "5": "SW2",
    "6": "GND", "7": "PMIC_INT", "12": "3V_MAIN", "13": "I2C_SDA",
    "14": "I2C_SCL", "15": "USER_BTN", "16": "VSET2", "17": "VSET1",
    "18": "NTC", "19": "VBAT", "20": "VSYS", "21": "VBUS",
    "22": "VBUSOUT", "23": "USB_CC1", "24": "USB_CC2", "25": "LED_BLUE_K",
    "26": "LED_RED_K", "28": "VSYS", "29": "3V_MIC", "30": "VSYS",
    "31": "LDO2_OUT", "32": "3V_SD", "33": "GND",
})

# LIS2DW12 I2C wiring, official pins 1..12.
set_many(U3, {"1": "I2C_SCL", "2": "3V_MAIN", "3": "GND", "4": "I2C_SDA",
              "6": "GND", "7": "GND", "8": "GND", "9": "3V_MAIN",
              "10": "3V_MAIN", "11": "ACC_INT2", "12": "ACC_INT1"})

set_many(U4, {"1": "USB_D+", "2": "USB_D-", "3": "GND"})
for mic, lr, data_net in ((MIC1, "GND", "PDM_DATA_MIC1"), (MIC2, "3V_MIC", "PDM_DATA_MIC2")):
    set_many(mic, {"1": "3V_MIC", "2": "PDM_CLK", "3": data_net, "4": lr, "5": "GND"})

for p in ("A1", "A12", "B1", "B12", "S1"):
    set_net(J1, p, "GND")
for p in ("A4", "A9", "B4", "B9"):
    set_net(J1, p, "VBUS")
for p in ("A6", "B6"):
    set_net(J1, p, "USB_D+")
for p in ("A7", "B7"):
    set_net(J1, p, "USB_D-")
set_net(J1, "A5", "USB_CC1")
set_net(J1, "B5", "USB_CC2")

set_many(J2, {"2": "SD_CS", "3": "SD_MOSI_CARD", "4": "3V_SD", "5": "SD_SCK_CARD",
              "6": "GND", "7": "SD_MISO_CARD", "9": "SD_DETECT", "10": "GND", "11": "GND"})
set_many(SW_USER, {"1": "USER_BTN", "2": "GND"})
set_many(LED1, {"1": "LED_BLUE_K", "2": "VSYS", "3": "LED_RED_K", "4": "VSYS"})
set_many(Q1, {"1": "HAPTIC_GATE", "2": "GND", "3": "HAPTIC_NEG"})
set_many(D1, {"1": "HAPTIC_NEG", "2": "3V_MAIN"})
set_many(BT1, {"1": "VBAT", "2": "NTC", "3": "GND"})
set_many(M1, {"1": "3V_MAIN", "2": "HAPTIC_NEG"})
set_many(L1, {"1": "3V_MAIN", "2": "SW1"})
set_many(L2, {"1": "3V_SD", "2": "SW2"})


def passive(fp: pcbnew.FOOTPRINT, a: str, b: str) -> None:
    set_many(fp, {"1": a, "2": b})


for fp, a, b in [
    (C1, "VBUS", "GND"), (C2, "VSYS", "GND"), (C3, "VSYS", "GND"),
    (C4, "VSYS", "GND"), (C5, "VBUSOUT", "GND"), (C6, "VBAT", "GND"),
    (C7, "3V_MAIN", "GND"), (C8, "3V_SD", "GND"), (C9, "VSYS", "GND"),
    (C10, "3V_MIC", "GND"), (C11, "VSYS", "GND"), (C12, "LDO2_OUT", "GND"),
    (C13, "3V_MAIN", "GND"), (C14, "VSYS", "GND"), (C15, "VSYS", "GND"),
    (C16, "VSYS", "GND"), (C17, "3V_MIC", "GND"), (C18, "3V_MIC", "GND"),
    (C19, "3V_MAIN", "GND"), (C20, "3V_MAIN", "GND"), (C21, "3V_SD", "GND"),
    (C22, "3V_SD", "GND"), (C23, "3V_MAIN", "HAPTIC_NEG"),
    (C24, "3V_MAIN", "GND"),
    (R1, "3V_MAIN", "I2C_SCL"), (R2, "3V_MAIN", "I2C_SDA"),
    (R3, "VSET1", "GND"), (R4, "VSET2", "GND"),
    (R5, "USB_CC1", "GND"), (R6, "USB_CC2", "GND"),
    (R7, "3V_SD", "SD_CS"), (R8, "SD_SCK_MCU", "SD_SCK_CARD"),
    (R9, "SD_MOSI_MCU", "SD_MOSI_CARD"), (R10, "SD_MISO_CARD", "SD_MISO_MCU"),
    (R11, "3V_MAIN", "USER_BTN"), (R12, "HAPTIC_PWM", "HAPTIC_GATE"),
    (R13, "HAPTIC_GATE", "GND"), (R14, "PDM_DATA_MIC1", "PDM_DATA"),
    (R15, "PDM_DATA_MIC2", "PDM_DATA"),
]:
    passive(fp, a, b)

for fp, (_, name) in zip(TESTS, TEST_NETS):
    set_net(fp, "1", name)


# ---- Board outline and manufacturing notes ------------------------------

def add_segment(x1: float, y1: float, x2: float, y2: float, layer=pcbnew.Edge_Cuts,
                width: float = 0.10) -> None:
    seg = pcbnew.PCB_SHAPE(board)
    seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
    seg.SetStart(vec(x1, y1))
    seg.SetEnd(vec(x2, y2))
    seg.SetLayer(layer)
    seg.SetWidth(mm(width))
    board.Add(seg)


# 49 x 20 mm preliminary true capsule: x=20..69, y=20..40, end radius=10 mm.
points = []
for i in range(17):
    ang = math.radians(-90 + i * 180 / 16)
    points.append((59.0 + 10.0 * math.cos(ang), 30.0 + 10.0 * math.sin(ang)))
for i in range(17):
    ang = math.radians(90 + i * 180 / 16)
    points.append((30.0 + 10.0 * math.cos(ang), 30.0 + 10.0 * math.sin(ang)))
for a, b in zip(points, points[1:] + points[:1]):
    add_segment(*a, *b)

# Antenna keepout boundary and acoustic-hole identifiers on Dwgs.User.
for a, b in [((65.0, 20.5), (65.0, 39.5)), ((65.0, 20.5), (68.5, 20.5)),
             ((65.0, 39.5), (68.5, 39.5))]:
    add_segment(*a, *b, layer=pcbnew.Dwgs_User, width=0.20)


def add_text(text: str, x: float, y: float, layer=pcbnew.F_SilkS, size: float = 0.8) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(vec(x, y))
    item.SetLayer(layer)
    item.SetTextHeight(mm(size))
    item.SetTextWidth(mm(size))
    item.SetTextThickness(mm(0.12))
    board.Add(item)


for fp in board.GetFootprints():
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)

for label, x, y, layer in [
    ("J1 USB", 22.8, 36.8, pcbnew.F_SilkS), ("U2 PMIC", 31.2, 32.9, pcbnew.F_SilkS),
    ("MIC1", 38.0, 20.8, pcbnew.F_SilkS), ("MIC2", 51.0, 20.8, pcbnew.F_SilkS),
    ("LED", 27.0, 38.6, pcbnew.F_SilkS), ("SW", 31.0, 38.6, pcbnew.F_SilkS),
    ("MOTOR", 34.0, 38.7, pcbnew.F_SilkS), ("BAT", 45.0, 39.0, pcbnew.F_SilkS),
    ("U3 ACC", 48.0, 38.7, pcbnew.F_SilkS), ("U1 RADIO", 61.0, 38.8, pcbnew.F_SilkS),
    ("J2 microSD", 43.0, 39.0, pcbnew.B_SilkS),
]:
    add_text(label, x, y, layer, 0.45)
add_text("ANT-PROD-R0 EVT", 24.0, 22.0, pcbnew.F_SilkS, 0.45)
add_text("ANTENNA - NO COPPER / BATTERY / METAL", 66.8, 30.0, pcbnew.Dwgs_User, 0.45)

# Conservative but dense-board-capable prototype rules: 5/5 mil and 0.20 mm
# finished drills. These are supported by mainstream prototype fabs on 4 layers.
default_nc = board.GetAllNetClasses()["Default"]
default_nc.SetClearance(mm(0.127))
default_nc.SetTrackWidth(mm(0.127))
default_nc.SetViaDiameter(mm(0.45))
default_nc.SetViaDrill(mm(0.20))
board.GetDesignSettings().m_MinClearance = mm(0.127)
board.GetDesignSettings().m_TrackMinWidth = mm(0.127)
board.GetDesignSettings().m_ViasMinSize = mm(0.45)

pcbnew.SaveBoard(str(OUT), board)

# Export a machine-readable connection table from the generated board.
with (ROOT / "pad_net_report.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(["reference", "value", "pad", "net", "x_mm", "y_mm", "side"])
    for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
        for pad in fp.Pads():
            pos = pad.GetPosition()
            writer.writerow([
                fp.GetReference(), fp.GetValue(), pad.GetNumber(), pad.GetNetname(),
                f"{pcbnew.ToMM(pos.x):.4f}", f"{pcbnew.ToMM(pos.y):.4f}",
                "B" if fp.IsFlipped() else "F",
            ])

print(f"Generated {OUT}")
print(f"Footprints: {len(board.GetFootprints())}; nets: {board.GetNetCount()}")
