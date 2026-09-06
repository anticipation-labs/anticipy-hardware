#!/usr/bin/env python3
"""Deterministic checks for the strict-size Anticipy EVT handoff."""

from pathlib import Path
import csv
import hashlib
import json

import cadquery as cq
import pdfplumber
import trimesh


ROOT = Path(__file__).resolve().parent
EXPECTED_UF2 = "de31edba36d077338b6fb1649782a68cce61e89c01a68cdfd9749c2ffc011f44"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


results = {}

report = json.loads((ROOT / "strict_evt_fit_report.json").read_text())
results["fit_checks_pass"] = all(item["pass"] for item in report["checks"])
results["finished_body_mm"] = report["finished_body_mm"]
results["inside_10_percent_ceiling"] = all(
    actual <= limit
    for actual, limit in zip(report["finished_body_mm"], report["hard_10_percent_ceiling_mm"])
)

for filename, expected_bodies in (
    ("anticipy_strict_evt_12_frame_plate.stl", 12),
    ("anticipy_strict_evt_12_accessory_sets_plate.stl", 36),
    ("anticipy_strict_evt_12_button_fit_plate.stl", 12),
):
    mesh = trimesh.load_mesh(ROOT / filename, process=True)
    pieces = list(mesh.split(only_watertight=False))
    results[filename] = {
        "body_count": len(pieces),
        "expected_body_count": expected_bodies,
        "all_watertight": all(piece.is_watertight for piece in pieces),
        "minimum_z_mm": round(float(mesh.bounds[0][2]), 4),
        "bounds_mm": (mesh.bounds[1] - mesh.bounds[0]).round(4).tolist(),
    }

assembly = cq.importers.importStep(str(ROOT / "anticipy_strict_evt_nominal_assembly.step"))
bounds = assembly.val().BoundingBox()
results["nominal_assembly_step_bounds_mm"] = [
    round(bounds.xlen, 3),
    round(bounds.ylen, 3),
    round(bounds.zlen, 3),
]

uf2 = ROOT / "firmware_lab_only" / "Anticipy_Founder_EVT_v0.9.0.uf2"
results["uf2_sha256"] = sha256(uf2)
results["uf2_checksum_matches"] = results["uf2_sha256"] == EXPECTED_UF2

with pdfplumber.open(ROOT / "anticipy_strict_evt_aluminum_template.pdf") as pdf:
    page = pdf.pages[0]
    horizontal_mm = sorted(
        round(abs(line["x1"] - line["x0"]) * 25.4 / 72, 3)
        for line in page.lines
        if abs(line["y1"] - line["y0"]) < 0.01
    )
    results["aluminum_pdf"] = {
        "pages": len(pdf.pages),
        "has_exact_50mm_calibration_line": 50.0 in horizontal_mm,
        "text_present": len(page.extract_text() or "") > 200,
    }

with (ROOT / "BUY_12.csv").open(newline="") as stream:
    bom = list(csv.DictReader(stream))
batteries = [row for row in bom if "LiPo" in row["part"]]
results["battery_release_hold_present"] = (
    len(batteries) == 1 and batteries[0]["state"] == "HOLD_UNTIL_PHYSICALLY_VERIFIED"
)

plate_ok = all(
    value["body_count"] == value["expected_body_count"]
    and value["all_watertight"]
    and value["minimum_z_mm"] >= -0.001
    for key, value in results.items()
    if key.endswith("plate.stl")
)
results["all_digital_checks_pass"] = all(
    (
        results["fit_checks_pass"],
        results["inside_10_percent_ceiling"],
        plate_ok,
        results["nominal_assembly_step_bounds_mm"] == [56.0, 23.0, 12.0],
        results["uf2_checksum_matches"],
        results["aluminum_pdf"]["pages"] == 1,
        results["aluminum_pdf"]["has_exact_50mm_calibration_line"],
        results["aluminum_pdf"]["text_present"],
        results["battery_release_hold_present"],
    )
)

(ROOT / "FINAL_DIGITAL_AUDIT.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))

if not results["all_digital_checks_pass"]:
    raise SystemExit("Anticipy EVT package verification failed")
