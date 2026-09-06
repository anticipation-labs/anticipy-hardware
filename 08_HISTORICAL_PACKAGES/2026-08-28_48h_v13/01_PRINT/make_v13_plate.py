#!/usr/bin/env python3
"""Create one clearly named Bambu P2S plate for Anticipy v1.3."""

from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
import trimesh


ROOT = Path(__file__).resolve().parent


def flat(filename: str, flip_x: bool = False) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(ROOT / filename, force="mesh")
    if flip_x:
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    mesh.apply_translation([0, 0, -mesh.bounds[0, 2]])
    return mesh


parts = {
    "ANTICIPY_BASE": flat("v13_rugged_base.stl"),
    "ANTICIPY_LID": flat("v13_rugged_lid.stl", flip_x=True),
    "ANTICIPY_BUTTON": flat("v13_button_plunger_2p0mm.stl"),
}

placements = {
    "ANTICIPY_BASE": (72, 128),
    "ANTICIPY_LID": (174, 128),
    "ANTICIPY_BUTTON": (128, 176),
}

scene = trimesh.Scene()
manifest = []
for name, mesh0 in parts.items():
    mesh = mesh0.copy()
    x, y = placements[name]
    centre = mesh.bounds.mean(axis=0)
    mesh.apply_translation([x - centre[0], y - centre[1], -mesh.bounds[0, 2]])
    scene.add_geometry(mesh, node_name=name, geom_name=name)
    manifest.append({
        "name": name,
        "centre_xy_mm": [x, y],
        "extents_mm": [round(float(v), 3) for v in mesh.extents],
    })

output = ROOT / "PRINT_THIS_ONE_UNIT_P2S.3mf"
output.write_bytes(scene.export(file_type="3mf"))
reload = trimesh.load_scene(output)
combined = reload.to_geometry()
report = {
    "printer": "Bambu Lab P2S, 0.4 mm nozzle",
    "plate_mm": [256, 256],
    "objects_expected": 3,
    "objects_reloaded": len(reload.geometry),
    "inside_plate": bool(
        combined.bounds[0, 0] >= 0 and combined.bounds[0, 1] >= 0 and
        combined.bounds[1, 0] <= 256 and combined.bounds[1, 1] <= 256
    ),
    "placements": manifest,
}
(ROOT / "PRINT_THIS_ONE_UNIT_P2S_report.json").write_text(json.dumps(report, indent=2) + "\n")
if report["objects_reloaded"] != 3 or not report["inside_plate"]:
    raise SystemExit(json.dumps(report, indent=2))

fig, ax = plt.subplots(figsize=(7, 7), dpi=180)
ax.add_patch(Rectangle((0, 0), 256, 256, fill=False, edgecolor="#111", lw=1.4))
ax.add_patch(FancyBboxPatch((72 - 36, 128 - 16.5), 68, 33,
                            boxstyle="round,pad=0,rounding_size=8",
                            facecolor="#8f887e", edgecolor="#222"))
ax.add_patch(Circle((72 - 34, 128), 5, facecolor="#8f887e", edgecolor="#222"))
ax.add_patch(Circle((72 - 34, 128), 2, facecolor="white", edgecolor="#222"))
ax.add_patch(FancyBboxPatch((174 - 34, 128 - 16.5), 68, 33,
                            boxstyle="round,pad=0,rounding_size=8",
                            facecolor="#b6aa99", edgecolor="#222"))
ax.add_patch(Circle((128, 176), 2.2, facecolor="#333", edgecolor="#111"))
ax.text(72, 104, "BASE", ha="center", fontsize=8, weight="bold")
ax.text(174, 104, "LID", ha="center", fontsize=8, weight="bold")
ax.text(128, 184, "BUTTON", ha="center", fontsize=8, weight="bold")
ax.set(xlim=(-3, 259), ylim=(-3, 259), aspect="equal")
ax.set_title("Anticipy v1.3 — one unit, three parts")
ax.set_xlabel("millimetres")
ax.set_ylabel("millimetres")
ax.grid(alpha=0.08)
fig.tight_layout()
fig.savefig(ROOT / "PRINT_THIS_ONE_UNIT_P2S_preview.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

print(json.dumps(report, indent=2))
