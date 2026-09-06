#!/usr/bin/env python3
"""Export Specctra DSN for FreeRouting and import routed sessions.

Run with KiCad's bundled Python:
    python export_dsn.py            # writes Anticipy_PROD_R0_EVT.dsn
    python export_dsn.py import X.ses  # imports a routed FreeRouting session
"""
import sys
from pathlib import Path

try:
    import wx
    _app = wx.App(False)
except Exception:
    pass

import pcbnew

ROOT = Path(__file__).resolve().parent
BOARD = ROOT / "Anticipy_PROD_R0_EVT.kicad_pcb"

board = pcbnew.LoadBoard(str(BOARD))

if len(sys.argv) > 2 and sys.argv[1] == "import":
    ses = Path(sys.argv[2]).resolve()
    ok = board.ImportSpecctraSession(str(ses))
    print("session import:", "OK" if ok else "FAILED")
    pcbnew.SaveBoard(str(BOARD), board)
    print(f"saved {BOARD}")
else:
    out = ROOT / "Anticipy_PROD_R0_EVT.dsn"
    ok = pcbnew.ExportSpecctraDSN(board, str(out))
    print("dsn export:", "OK" if ok else "FAILED", "->", out)
