#!/usr/bin/env python3
"""Render the controlled board outline and 15%-expanded subsystem reservations."""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    m = json.loads((ROOT / "design_manifest.json").read_text())
    # Scallop arc clockwise from -102.68° to -212.47° in KiCad coordinates.
    arc = []
    for i in range(61):
        a = math.radians(-102.6804 + (-109.7870) * i / 60)
        arc.append((116.9 + 4.1 * math.cos(a), 104.8 + 4.1 * math.sin(a)))
    outline = [(78.5,96.75),(85,96.75),(85,93),(116,93),(116,100.8),*arc[1:],
               (85,107),(85,103.25),(78.5,103.25)]
    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=180)
    ax.add_patch(Polygon(outline, closed=True, facecolor="#E8EEF8", edgecolor="#183153", linewidth=2.0))
    ax.add_patch(Rectangle((78.5,96.75),6.5,6.5,fill=False,edgecolor="#D1495B",linewidth=1.6,linestyle="--"))
    ax.text(81.75,96.35,"6.5 × 6.5 mm RF no-metal nose",ha="center",va="bottom",fontsize=8,color="#A12636")
    colors = {"U1":"#496DDB","U4":"#6B4CC4","U5":"#ED8B32","U6":"#D1495B",
              "U2":"#2A9D8F","U3":"#2A9D8F","ANT1":"#E9C46A"}
    for b in m["major_blocks"]:
        cx, cy = b["center"]
        w, h = b["size"]
        mw, mh = w*b["margin"], h*b["margin"]
        ax.add_patch(Rectangle((cx-w/2,cy-h/2),w,h,facecolor=colors.get(b["ref"],"#888"),alpha=.75,edgecolor="#111"))
        ax.add_patch(Rectangle((cx-mw/2,cy-mh/2),mw,mh,fill=False,edgecolor=colors.get(b["ref"],"#555"),linestyle=":",linewidth=1.4))
        ax.text(cx,cy,b["ref"],ha="center",va="center",fontsize=8,fontweight="bold",color="white" if b["ref"]!="ANT1" else "#222")
    ax.add_patch(Circle((116.9,104.8),4.1,fill=False,edgecolor="#D1495B",linestyle="--",linewidth=1.2))
    ax.text(115.2,108.0,"4.10 mm motor-pocket scallop",ha="right",fontsize=8,color="#A12636")
    ax.text(97.25,91.8,"Anticipy EVT-A PCB checkpoint — 37.50 × 14.00 mm overall",ha="center",fontsize=12,fontweight="bold")
    ax.text(97.25,109.0,"Solid = controlled block  ·  dotted = 15% XY envelope  ·  drawing is placement evidence, not fabrication release",ha="center",fontsize=8)
    ax.set_xlim(76.8,120.7)
    ax.set_ylim(110.0,90.7)
    ax.set_aspect("equal")
    ax.set_xlabel("KiCad X (mm)")
    ax.set_ylabel("KiCad Y (mm)")
    ax.grid(alpha=.18)
    fig.tight_layout()
    fig.savefig(ROOT / "reports/PCB_PLACEMENT.png", bbox_inches="tight")
    fig.savefig(ROOT / "reports/PCB_PLACEMENT.svg", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
