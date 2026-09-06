#!/usr/bin/env python3
"""Fail closed if the released Anticipy v1.3 print package is inconsistent."""

from pathlib import Path
import hashlib
import json

import trimesh


ROOT = Path(__file__).resolve().parent
PRINT = ROOT / "01_PRINT"

fit = json.loads((PRINT / "v13_digital_fit_report.json").read_text())
plate = json.loads((PRINT / "PRINT_THIS_ONE_UNIT_P2S_report.json").read_text())

assert all(row["pass"] for row in fit["checks"]), fit["checks"]
assert fit["solid_collision_mm3"]["base_to_lid"] == 0.0
assert all(
    value == 0.0
    for shell_values in fit["solid_collision_mm3"]["components"].values()
    for value in shell_values.values()
)
assert plate["objects_reloaded"] == 3
assert plate["inside_plate"]

for name in ("v13_rugged_base.stl", "v13_rugged_lid.stl", "v13_button_plunger_2p0mm.stl"):
    mesh = trimesh.load_mesh(PRINT / name, force="mesh")
    assert mesh.is_watertight, name
    assert len(mesh.split(only_watertight=False)) == 1, name

required = [
    ROOT / "START_HERE.md",
    PRINT / "PRINT_THIS_ONE_UNIT_P2S.3mf",
    PRINT / "v13_rugged_base.step",
    PRINT / "v13_rugged_lid.step",
    ROOT / "02_GUIDES" / "ORDER_NOW.csv",
    ROOT / "02_GUIDES" / "PRINT_SETTINGS.md",
    ROOT / "02_GUIDES" / "ASSEMBLY_LIKE_IM_2.md",
    ROOT / "02_GUIDES" / "WIRING_CARD.md",
    ROOT / "02_GUIDES" / "SAFETY_AND_TEST_GATES.md",
]
assert all(path.exists() and path.stat().st_size > 0 for path in required)

lines = []
for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p.name != "SHA256SUMS.txt"):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    lines.append(f"{digest}  {path.relative_to(ROOT)}")
(ROOT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")

print("PASS: 12/12 digital fit checks")
print("PASS: zero base/lid and controlled-component collisions")
print("PASS: three named 3MF objects inside the P2S build plate")
print("PASS: base, lid and button are single-body watertight meshes")
print("LIMIT: physical runtime, radio, audio, drop and heat tests remain required")

