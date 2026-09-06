#!/usr/bin/env python3
"""Re-open and independently validate the Anticipy v09 release artifacts."""

from pathlib import Path
import hashlib
import json
import math
import zipfile

from cadquery import importers
import trimesh


ROOT = Path(__file__).resolve().parent
FIT = json.loads((ROOT / "v09_fit_report.json").read_text())
PLATE_REPORT = json.loads((ROOT / "Anticipy_v09_five_units_plate_report.json").read_text())

out = {
    "validation_date": "2026-08-28",
    "status": "PASS_DIGITAL_ONLY",
    "fit_checks": {
        "passed": sum(bool(c["pass"]) for c in FIT["checks"]),
        "total": len(FIT["checks"]),
        "failed": [c["name"] for c in FIT["checks"] if not c["pass"]],
    },
    "finished_body_mm": FIT["finished_device_body_mm"],
    "mass_estimate_g": FIT["mass_estimate_g"],
    "primary_meshes": {},
    "step_solids": {},
    "five_unit_3mf": {},
    "print_orientation_downward_horizontal_area_mm2": {},
    "sha256": {},
    "physical_gates_still_required": [
        "caliper fit of delivered stack and pack",
        "sliced preview and one calibration print",
        "sealed audio/BLE/storage tests",
        "16h runtime and 20h backlog tests",
        "shake and inspectable drop tests",
    ],
}

for filename in ("v09_compact_base.stl", "v09_compact_lid.stl", "v09_lanyard_clip.stl"):
    mesh = trimesh.load_mesh(ROOT / filename, force="mesh")
    out["primary_meshes"][filename] = {
        "watertight": bool(mesh.is_watertight),
        "bodies": len(mesh.split(only_watertight=False)),
        "positive_volume": bool(mesh.volume > 0),
        "volume_mm3": round(float(mesh.volume), 3),
        "bounds_mm": [round(float(x), 3) for x in mesh.extents],
    }
    oriented = mesh.copy()
    if "lid" in filename:
        oriented.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
    oriented.apply_translation([0, 0, -oriented.bounds[0, 2]])
    unsupported = (oriented.face_normals[:, 2] < -0.70) & (oriented.triangles_center[:, 2] > 0.25)
    out["print_orientation_downward_horizontal_area_mm2"][filename] = round(
        float(oriented.area_faces[unsupported].sum()), 3
    )

for filename in ("v09_compact_base.step", "v09_compact_lid.step", "v09_lanyard_clip.step"):
    model = importers.importStep(str(ROOT / filename))
    bounds = model.val().BoundingBox()
    out["step_solids"][filename] = {
        "solids": len(model.solids().vals()),
        "bounds_mm": [round(bounds.xlen, 3), round(bounds.ylen, 3), round(bounds.zlen, 3)],
    }

plate_file = ROOT / "Anticipy_v09_five_units_P2S.3mf"
scene = trimesh.load_scene(plate_file)
combined = scene.to_geometry()
geometries = list(scene.geometry.values())
out["five_unit_3mf"] = {
    "zip_package": zipfile.is_zipfile(plate_file),
    "objects": len(geometries),
    "all_watertight": all(g.is_watertight for g in geometries),
    "all_positive_volume": all(g.volume > 0 for g in geometries),
    "xy_bounds_mm": [
        [round(float(v), 3) for v in combined.bounds[0, :2]],
        [round(float(v), 3) for v in combined.bounds[1, :2]],
    ],
    "inside_256mm_plate": bool(
        (combined.bounds[0, :2] >= 0).all() and (combined.bounds[1, :2] <= 256).all()
    ),
    "model_mass_g_at_1p25_density": PLATE_REPORT["model_geometry_mass_at_1p25_g_per_cm3_g"],
}

hashed_files = (
    "generate_v09_compact.py",
    "make_v09_five_unit_plate.py",
    "validate_v09_release.py",
    "v09_compact_base.stl",
    "v09_compact_lid.stl",
    "v09_lanyard_clip.stl",
    "v09_compact_base.step",
    "v09_compact_lid.step",
    "v09_lanyard_clip.step",
    "Anticipy_v09_five_units_P2S.3mf",
    "v09_fit_report.json",
    "Anticipy_v09_five_units_plate_report.json",
    "PRINT_AND_ASSEMBLE_P2S.md",
)
for filename in hashed_files:
    out["sha256"][filename] = hashlib.sha256((ROOT / filename).read_bytes()).hexdigest()

hard_pass = (
    not out["fit_checks"]["failed"]
    and all(v["watertight"] and v["bodies"] == 1 and v["positive_volume"] for v in out["primary_meshes"].values())
    and all(v["solids"] == 1 for v in out["step_solids"].values())
    and out["five_unit_3mf"]["zip_package"]
    and out["five_unit_3mf"]["objects"] == 30
    and out["five_unit_3mf"]["all_watertight"]
    and out["five_unit_3mf"]["all_positive_volume"]
    and out["five_unit_3mf"]["inside_256mm_plate"]
)
out["status"] = "PASS_DIGITAL_ONLY" if hard_pass else "FAIL"
(ROOT / "v09_release_validation.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
raise SystemExit(0 if hard_pass else 1)
