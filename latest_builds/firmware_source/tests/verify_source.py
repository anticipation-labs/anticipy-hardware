#!/usr/bin/env python3
"""Verify the preserved application and optionally the separately supplied HEX."""
import argparse
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--hex", type=Path, help="Optional released first-power HEX")
args = parser.parse_args()
manifest = json.loads((root / "provenance/Application_Source_Manifest.json").read_text())
relationship = json.loads((root / "Source_Image_Relationship.json").read_text())
expected_paths = sorted(row["path"] for row in manifest)
actual_paths = sorted(str(p.relative_to(root / "app")) for p in (root / "app").rglob("*") if p.is_file())
failures = []
if expected_paths != actual_paths:
    failures.append("Application file set differs from the preserved manifest")
rows = []
for row in sorted(manifest, key=lambda row: row["path"]):
    path = root / "app" / row["path"]
    if not path.is_file() or path.is_symlink():
        failures.append("Missing or symlinked file: " + row["path"])
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows.append(row["path"] + "\t" + digest)
    if digest != row["sha256"]:
        failures.append("Hash mismatch: " + row["path"])
tree_sha = hashlib.sha256("\n".join(rows).encode()).hexdigest()
if tree_sha != relationship["source_tree_sha256"]:
    failures.append("Application tree hash mismatch")
hex_sha = None
if args.hex:
    if not args.hex.is_file():
        failures.append("HEX not found: " + str(args.hex))
    else:
        hex_sha = hashlib.sha256(args.hex.read_bytes()).hexdigest()
        if hex_sha != relationship["released_hex_sha256"]:
            failures.append("HEX hash differs from the released bench image")
print(json.dumps({"status": "FAIL" if failures else "PASS", "application_file_count": len(rows), "source_tree_sha256": tree_sha, "hex_checked": bool(args.hex), "hex_sha256": hex_sha, "failures": failures}, indent=2))
raise SystemExit(1 if failures else 0)
