#!/usr/bin/env python3
"""Offline consistency checks for the Anticipy QA-fixture package."""

from __future__ import annotations

import csv
import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
REQUIRED = [
    "README.md", "SAFETY.md", "PRINT_SETTINGS.md", "WIRING.md",
    "ASSEMBLY_RATTLE.md", "ASSEMBLY_DROP.md", "BOM.csv",
    "acceptance_test_template.csv", "drop_orientation_map.csv",
    "generate_fixtures.py", "verify_meshes.py", "rattle_audio_score.py",
    "qa_acceptance.py", "USAGE_EXAMPLES.md",
    "firmware/rattle_cradle_controller/rattle_cradle_controller.ino",
    "firmware/drop_release_controller/drop_release_controller.ino",
    "reports/fixture_manifest.json", "reports/mesh_verification.json",
]


def read_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    if errors:
        print("FAIL\n" + "\n".join(errors))
        return 1

    for script in ("generate_fixtures.py", "verify_meshes.py", "rattle_audio_score.py", "qa_acceptance.py"):
        try:
            ast.parse((ROOT / script).read_text(), filename=script)
        except SyntaxError as exc:
            errors.append(f"Python syntax: {exc}")

    manifest = json.loads((ROOT / "reports/fixture_manifest.json").read_text())
    mesh = json.loads((ROOT / "reports/mesh_verification.json").read_text())
    stls = sorted((ROOT / "stl").glob("*.stl"))
    steps = sorted((ROOT / "step").glob("*.step"))
    if manifest.get("printed_part_count") != 42:
        errors.append("fixture manifest does not contain 42 printed parts")
    if mesh.get("result") != "PASS" or mesh.get("stl_count") != 42:
        errors.append("mesh verification is not PASS for exactly 42 STL files")
    if len(stls) != 42:
        errors.append(f"expected 42 STL files, found {len(stls)}")
    if len(steps) < 44:  # 42 parts plus closed/released/fixture assembly views
        errors.append(f"expected at least 44 STEP files, found {len(steps)}")

    orientations = read_csv("drop_orientation_map.csv")
    if len(orientations) != 26:
        errors.append(f"expected 26 drop orientations, found {len(orientations)}")
    ids = [row.get("orientation_id", "") for row in orientations]
    if len(set(ids)) != len(ids):
        errors.append("drop orientation IDs are not unique")
    for row in orientations:
        key = ROOT / row.get("pose_key_stl", "")
        if not key.is_file():
            errors.append(f"orientation pose key missing: {key.name}")

    bom = read_csv("BOM.csv")
    item_ids = [row.get("item_id", "") for row in bom]
    if len(item_ids) != len(set(item_ids)):
        errors.append("BOM item IDs are not unique")
    if not {"rattle", "drop", "shared"}.issubset({row.get("fixture") for row in bom}):
        errors.append("BOM does not cover rattle, drop and shared groups")

    acceptance = read_csv("acceptance_test_template.csv")
    test_ids = [row.get("test_id", "") for row in acceptance]
    if len(acceptance) != 59 or len(test_ids) != len(set(test_ids)):
        errors.append("acceptance template must contain 59 unique tests")

    for sketch in (
        ROOT / "firmware/rattle_cradle_controller/rattle_cradle_controller.ino",
        ROOT / "firmware/drop_release_controller/drop_release_controller.ino",
    ):
        source = sketch.read_text()
        if source.count("{") != source.count("}"):
            errors.append(f"unbalanced braces in {sketch.relative_to(ROOT)}")
        if "INPUT_PULLUP" not in source:
            errors.append(f"missing fail-open input strategy in {sketch.relative_to(ROOT)}")

    result = "PASS" if not errors else "FAIL"
    report = {
        "result": result,
        "stl_count": len(stls),
        "step_count": len(steps),
        "drop_orientation_count": len(orientations),
        "bom_line_count": len(bom),
        "acceptance_test_count": len(acceptance),
        "errors": errors,
        "note": "Firmware receives host-side structural checks here; flash and bench-test it on the exact controller before fixture use.",
    }
    (ROOT / "reports/package_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
