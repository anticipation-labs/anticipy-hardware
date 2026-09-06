#!/usr/bin/env python3
"""Structural verification for the Anticipy EVT board.

Run with KiCad's Python environment:
    /usr/bin/python3 verify_project.py
"""

from pathlib import Path
import sys

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD_PATH = ROOT / "Anticipy_PROD_R0_EVT.kicad_pcb"
REPORT_PATH = ROOT / "drc_unrouted_report.txt"

board = pcbnew.LoadBoard(str(BOARD_PATH))
failures: list[str] = []


def require(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
require(len(footprints) == len(board.GetFootprints()), "duplicate footprint references")
require(len(footprints) == 62, f"expected 62 footprints, found {len(footprints)}")
require(board.GetCopperLayerCount() == 4, "board must use four copper layers")
require(abs(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()) - 0.8) < 0.001,
        "board thickness must be 0.8 mm")


def pad_net(reference: str, pad_number: str) -> str:
    pads = [p for p in footprints[reference].Pads() if p.GetNumber() == pad_number]
    require(bool(pads), f"{reference} pad {pad_number} missing")
    return pads[0].GetNetname() if pads else ""


for ref, pin, expected in [
    ("U2", "17", "VSET1"), ("U2", "16", "VSET2"),
    ("U2", "2", "GND"), ("U2", "6", "GND"),
    ("U4", "1", "USB_D+"), ("U4", "2", "USB_D-"), ("U4", "3", "GND"),
    ("U1", "38", "PDM_CLK"), ("U1", "39", "PDM_DATA"),
]:
    actual = pad_net(ref, pin)
    require(actual == expected, f"{ref} pad {pin}: expected {expected}, got {actual}")

all_nets = {net.GetNetname() for net in board.GetNetInfo().NetsByNetcode().values()}
require("PVSS1" not in all_nets and "PVSS2" not in all_nets,
        "obsolete floating PVSS nets must not exist")
require({"VSET1", "VSET2"}.issubset(all_nets), "VSET nets missing")
require(abs((footprints["U1"].GetOrientationDegrees() % 360.0) - 270.0) < 0.01,
        "Raytac module must keep antenna toward right board edge")

pcbnew.WriteDRCReport(board, str(REPORT_PATH), pcbnew.EDA_UNITS_MILLIMETRES, True)
drc = REPORT_PATH.read_text(errors="replace")
error_count = drc.count("Severity: error")
unconnected_count = drc.count("[unconnected_items]")

if failures:
    print("STRUCTURAL CHECK: FAILED")
    for failure in failures:
        print(f"- {failure}")
    sys.exit(1)

print("STRUCTURAL CHECK: PASSED")
print(f"Footprints: {len(footprints)}; nets: {board.GetNetCount()}; layers: 4; thickness: 0.8 mm")
print(f"FABRICATION CHECK: BLOCKED ({error_count} DRC errors; {unconnected_count} unconnected items)")
print(f"DRC report: {REPORT_PATH}")
