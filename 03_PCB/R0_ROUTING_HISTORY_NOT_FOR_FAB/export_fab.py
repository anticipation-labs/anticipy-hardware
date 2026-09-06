#!/usr/bin/env python3
"""Guarded fabrication exporter.

This script intentionally refuses to export while KiCad reports any error and
until an electrical/mechanical reviewer creates APPROVED_FOR_FAB.txt containing:
    ANT-PROD-R0 APPROVED
"""

from pathlib import Path
import shutil
import subprocess
import sys

import pcbnew


ROOT = Path(__file__).resolve().parent
BOARD = ROOT / "Anticipy_PROD_R0_EVT.kicad_pcb"
APPROVAL = ROOT / "APPROVED_FOR_FAB.txt"
REPORT = ROOT / "release_drc_report.txt"
OUT = ROOT / "FAB_OUTPUT"

if not APPROVAL.exists() or APPROVAL.read_text().strip() != "ANT-PROD-R0 APPROVED":
    sys.exit("BLOCKED: signed electrical/mechanical approval token is absent.")

board = pcbnew.LoadBoard(str(BOARD))
pcbnew.WriteDRCReport(board, str(REPORT), pcbnew.EDA_UNITS_MILLIMETRES, True)
errors = REPORT.read_text(errors="replace").count("Severity: error")
if errors:
    sys.exit(f"BLOCKED: KiCad DRC still reports {errors} errors. See {REPORT}.")

if OUT.exists():
    sys.exit(f"BLOCKED: {OUT} already exists; archive/review it before another export.")

OUT.mkdir()
commands = [
    ["kicad-cli", "pcb", "export", "gerbers", "-o", str(OUT) + "/", str(BOARD)],
    ["kicad-cli", "pcb", "export", "drill", "-o", str(OUT) + "/", str(BOARD)],
    ["kicad-cli", "pcb", "export", "pos", "--format", "csv", "--units", "mm",
     "-o", str(OUT / "Anticipy_PROD_R0_EVT_positions.csv"), str(BOARD)],
    ["kicad-cli", "pcb", "export", "step", "-o",
     str(OUT / "Anticipy_PROD_R0_EVT.step"), str(BOARD)],
]
for command in commands:
    subprocess.run(command, check=True)

shutil.copy2(REPORT, OUT / REPORT.name)
print(f"Exported approved fabrication package to {OUT}")
