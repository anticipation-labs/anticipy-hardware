#!/usr/bin/env python3
"""Fail the release if any generated fixture STL is not a printable solid."""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import sys

import numpy as np
import trimesh


ROOT = Path(__file__).resolve().parent
STL_DIR = ROOT / "stl"
REPORT = ROOT / "reports" / "mesh_verification.json"
MAX_BUILD_MM = np.array([256.0, 256.0, 256.0])


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    files = sorted(STL_DIR.glob("*.stl"))
    if not files:
        print("FAIL: no STL files found; run generate_fixtures.py first", file=sys.stderr)
        return 2

    rows = []
    failures = []
    for path in files:
        mesh = trimesh.load_mesh(path, force="mesh", process=True)
        components = mesh.split(only_watertight=False)
        extents = np.asarray(mesh.extents, dtype=float)
        finite = bool(np.isfinite(mesh.vertices).all() and np.isfinite(mesh.faces).all())
        degenerate = int(np.count_nonzero(mesh.area_faces < 1e-10))
        checks = {
            "finite": finite,
            "watertight": bool(mesh.is_watertight),
            "winding_consistent": bool(mesh.is_winding_consistent),
            "is_volume": bool(mesh.is_volume),
            "positive_volume": bool(mesh.volume > 1.0),
            "one_connected_body": len(components) == 1,
            "zero_degenerate_faces": degenerate == 0,
            "fits_P2S_build_volume_in_some_axis_aligned_orientation": bool(
                np.all(np.sort(extents) <= np.sort(MAX_BUILD_MM))
            ),
        }
        passed = all(checks.values())
        if not passed:
            failures.append(path.name)
        rows.append(
            {
                "file": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "connected_bodies": int(len(components)),
                "extents_mm": [round(float(v), 3) for v in extents],
                "volume_mm3": round(float(mesh.volume), 3),
                "degenerate_faces": degenerate,
                "checks": checks,
                "pass": passed,
            }
        )

    payload = {
        "result": "PASS" if not failures else "FAIL",
        "stl_count": len(files),
        "failure_count": len(failures),
        "failed_files": failures,
        "scope": (
            "Geometry/manifold/build-volume checks only. This does not validate print quality, "
            "release timing, drop spin, structural strength, electrical safety, or calibration."
        ),
        "meshes": rows,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"{payload['result']}: {len(files)} STL files; {len(failures)} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
