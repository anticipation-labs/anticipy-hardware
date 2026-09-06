#!/usr/bin/env python3
"""Build a generic 3MF plate containing five Anticipy v0.9 print sets.

The 3MF stores millimetre geometry and placement only.  Open it in Bambu
Studio, choose the P2S 0.4 mm printer and apply the settings documented in
PRINT_AND_ASSEMBLE_P2S.md before slicing.  It intentionally contains no
machine-bound G-code.
"""

from copy import deepcopy
from pathlib import Path
import json
import math

import numpy as np
import trimesh
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


ROOT = Path(__file__).resolve().parent
OUT = ROOT
OUT.mkdir(exist_ok=True)


def load_flat(filename: str, flip_x: bool = False) -> trimesh.Trimesh:
    mesh = trimesh.load_mesh(ROOT / filename, force="mesh")
    if flip_x:
        # The lid's smooth exterior goes on the bed.  Its lip, acoustic
        # chimney and retention pockets then grow upward without support.
        mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    mesh.apply_translation([0, 0, -mesh.bounds[0, 2]])
    return mesh


base_master = load_flat("v09_compact_base.stl")
lid_master = load_flat("v09_compact_lid.stl", flip_x=True)
backplate_master = load_flat("v09_lanyard_clip.stl")
plunger_masters = {
    length: load_flat(f"v09_button_plunger_{length.replace('.', 'p')}mm.stl")
    for length in ("1.7", "1.9", "2.1")
}

# Five 66.2 x 27.2 mm bases and five lids fit comfortably inside the P2S's
# official 256 x 256 mm build volume.  An 8 mm nominal gap leaves room for
# skirts/brims and reduces heat accumulation around the small walls.
base_centres = [(42, 28), (116, 28), (190, 28), (79, 66), (153, 66)]
lid_centres = [(42, 104), (116, 104), (190, 104), (79, 142), (153, 142)]
backplate_centres = [(30, 184), (78, 184), (126, 184), (174, 184), (222, 184)]

scene = trimesh.Scene()
manifest = []


def add(mesh: trimesh.Trimesh, name: str, centre_xy):
    item = mesh.copy()
    current = item.bounds.mean(axis=0)
    item.apply_translation([centre_xy[0] - current[0], centre_xy[1] - current[1], -item.bounds[0, 2]])
    scene.add_geometry(item, node_name=name, geom_name=name)
    manifest.append({
        "name": name,
        "centre_xy_mm": list(centre_xy),
        "bounds_mm": [round(float(v), 3) for v in item.extents],
    })


for index, centre in enumerate(base_centres, start=1):
    add(base_master, f"unit_{index}_base", centre)
for index, centre in enumerate(lid_centres, start=1):
    add(lid_master, f"unit_{index}_lid_exterior_face_down", centre)
for index, centre in enumerate(backplate_centres, start=1):
    add(backplate_master, f"unit_{index}_lanyard_backplate", centre)

# Print all three captive-plunger lengths for each unit.  Dry-fit the shortest
# first and use only the shortest one that gives a positive click without
# holding the XIAO button down.
start_x, start_y = 25, 215
for unit in range(1, 6):
    for variant, length in enumerate(("1.7", "1.9", "2.1")):
        add(plunger_masters[length], f"unit_{unit}_plunger_{length}mm", (start_x + (unit - 1) * 44 + variant * 10, start_y))

plate_bytes = scene.export(file_type="3mf")
(OUT / "Anticipy_v09_five_units_P2S.3mf").write_bytes(plate_bytes)

# Re-open the exported plate as an independent package check.
reloaded = trimesh.load_scene(OUT / "Anticipy_v09_five_units_P2S.3mf")
combined = reloaded.to_geometry()
plate_bounds = combined.bounds
report = {
    "printer": "Bambu Lab P2S, 0.4 mm nozzle",
    "official_build_volume_mm": [256, 256, 256],
    "objects_expected": 30,
    "objects_reloaded": len(reloaded.geometry),
    "plate_xy_bounds_mm": [[round(float(plate_bounds[0, 0]), 3), round(float(plate_bounds[0, 1]), 3)],
                           [round(float(plate_bounds[1, 0]), 3), round(float(plate_bounds[1, 1]), 3)]],
    "plate_inside_256_mm": bool(plate_bounds[0, 0] >= 0 and plate_bounds[0, 1] >= 0 and
                                plate_bounds[1, 0] <= 256 and plate_bounds[1, 1] <= 256),
    "geometry_only_no_gcode": True,
    "model_geometry_volume_mm3": round(float(combined.volume), 3),
    "model_geometry_mass_at_1p25_g_per_cm3_g": round(float(combined.volume) / 1000.0 * 1.25, 2),
    "load_at_least_filament_g_including_brims_and_retry_allowance": 80,
    "placements": manifest,
}
(OUT / "Anticipy_v09_five_units_plate_report.json").write_text(json.dumps(report, indent=2) + "\n")

# Human-readable top-view check.  This is a placement drawing, not a sliced
# toolpath preview.
fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=180)
palette = {"base": "#737b87", "lid": "#a7acb4", "lanyard": "#c5a04b", "plunger": "#2f8a72"}
for item in manifest:
    x, y = item["centre_xy_mm"]
    w, h, _ = item["bounds_mm"]
    kind = "base" if "_base" in item["name"] else "lid" if "_lid" in item["name"] else "lanyard" if "lanyard" in item["name"] else "plunger"
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=palette[kind], edgecolor="#222", lw=0.55))
ax.add_patch(Rectangle((0, 0), 256, 256, fill=False, edgecolor="#111", lw=1.4))
ax.set_xlim(-4, 260); ax.set_ylim(-4, 260); ax.set_aspect("equal")
ax.set_title("Anticipy v0.9 · five-unit P2S plate", weight="bold")
ax.set_xlabel("millimetres"); ax.set_ylabel("millimetres")
ax.grid(alpha=0.12)
fig.tight_layout()
fig.savefig(OUT / "Anticipy_v09_five_units_plate_layout.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

if report["objects_reloaded"] != report["objects_expected"] or not report["plate_inside_256_mm"]:
    raise SystemExit("3MF plate verification failed: " + json.dumps(report, indent=2))

print(json.dumps(report, indent=2))
