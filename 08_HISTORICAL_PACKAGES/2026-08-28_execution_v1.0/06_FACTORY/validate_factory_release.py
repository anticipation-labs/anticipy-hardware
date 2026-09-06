#!/usr/bin/env python3
"""Read-only structural validation for the Anticipy factory-release skeleton."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(name: str) -> tuple[list[str], list[dict[str, str]]]:
    path = ROOT / name
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise AssertionError(f"{name}: missing header")
        rows = list(reader)
    return reader.fieldnames, rows


def validate_upload_manifest() -> tuple[int, int]:
    _, rows = read_csv("FACTORY_UPLOAD_MANIFEST.csv")
    present = 0
    blocking = 0
    ids: set[str] = set()

    for row in rows:
        item_id = row["item_id"]
        if item_id in ids:
            raise AssertionError(f"duplicate upload item_id: {item_id}")
        ids.add(item_id)
        status = row["status"]
        if status == "REFERENCE_ONLY":
            path = (ROOT / row["relative_path"]).resolve()
            if not path.is_file():
                raise AssertionError(f"missing reference file: {path}")
            actual_size = path.stat().st_size
            actual_hash = sha256(path)
            if actual_size != int(row["size_bytes"]):
                raise AssertionError(f"size mismatch for {path.name}")
            if actual_hash != row["sha256"]:
                raise AssertionError(f"hash mismatch for {path.name}")
            present += 1
        elif status == "MISSING_BLOCKING":
            if row["sha256"] != "TBD" or row["size_bytes"] != "TBD":
                raise AssertionError(f"blocking item has invented identity: {item_id}")
            blocking += 1
        else:
            raise AssertionError(f"unexpected manifest status {status!r}: {item_id}")

    if blocking == 0:
        raise AssertionError("manifest must expose absent blocking production files")

    pcb_checkpoint_ids = {
        "PCBREF001",
        "PCBREF002",
        "PCBREF003",
        "PCBREF004",
        "PCBREF005",
    }
    pcb_release_blockers = {f"PCB{number:03d}" for number in range(1, 15)}
    by_id = {row["item_id"]: row for row in rows}
    if not pcb_checkpoint_ids.issubset(by_id):
        raise AssertionError("manifest is missing one or more PCB checkpoint references")
    if not pcb_release_blockers.issubset(by_id):
        raise AssertionError("manifest is missing one or more PCB fabrication blockers")
    for item_id in pcb_checkpoint_ids:
        row = by_id[item_id]
        if row["status"] != "REFERENCE_ONLY" or row["target"] != "engineering_only":
            raise AssertionError(f"PCB checkpoint is not isolated as engineering-only: {item_id}")
    for item_id in pcb_release_blockers:
        if by_id[item_id]["status"] != "MISSING_BLOCKING":
            raise AssertionError(f"PCB fabrication gate was weakened: {item_id}")
    return present, blocking


def validate_quantities() -> int:
    _, rows = read_csv("PURCHASE_QUANTITIES.csv")
    ids: set[str] = set()
    for row in rows:
        item_id = row["item_id"]
        if item_id in ids:
            raise AssertionError(f"duplicate purchase item_id: {item_id}")
        ids.add(item_id)
        per = int(row["qty_per_unit"])
        expected = {
            "evt_10_required": per * 10,
            "dvt_35_required": per * 35,
            "pvt_230_required": per * 230,
        }
        for column, value in expected.items():
            if int(row[column]) != value:
                raise AssertionError(
                    f"quantity mismatch {item_id} {column}: {row[column]} != {value}"
                )

    finished = next(row for row in rows if row["item_id"] == "FINISHED_UNIT")
    if int(finished["pvt_230_required"]) != 230:
        raise AssertionError("PVT finished quantity must be 230")
    if 230 != 200 * 115 // 100:
        raise AssertionError("PVT 15% reserve arithmetic failed")
    return len(rows)


def validate_templates() -> None:
    traveler_header, traveler_rows = read_csv("ASSEMBLY_TRAVELER_LOG.csv")
    eol_header, eol_rows = read_csv("EOL_RESULTS_TEMPLATE.csv")
    if traveler_rows or eol_rows:
        raise AssertionError("factory CSV templates must not contain invented production data")
    if len(traveler_header) < 20:
        raise AssertionError("traveler schema unexpectedly incomplete")
    if len(eol_header) < 80:
        raise AssertionError("EOL schema unexpectedly incomplete")


def main() -> None:
    required = [
        "README.md",
        "FACTORY_UPLOAD_MANIFEST.csv",
        "PCB_RELEASE_CHECKPOINT.md",
        "PURCHASE_QUANTITIES.csv",
        "PCBA_RFQ_REQUIREMENTS.md",
        "INCOMING_INSPECTION.md",
        "SERIALIZED_ASSEMBLY_TRAVELER.md",
        "ASSEMBLY_TRAVELER_LOG.csv",
        "EOL_TEST_SPEC.md",
        "EOL_RESULTS_TEMPLATE.csv",
        "ACCEPTANCE_AND_LOT_STOP_RULES.md",
        "RELEASE_AUTHORIZATION_TEMPLATE.md",
    ]
    missing = [name for name in required if not (ROOT / name).is_file()]
    if missing:
        raise AssertionError(f"missing package files: {missing}")

    present, blocking = validate_upload_manifest()
    quantity_rows = validate_quantities()
    validate_templates()
    print("PASS: factory-release skeleton is structurally consistent")
    print(f"verified existing reference files: {present}")
    print(f"explicit missing/blocking release items: {blocking}")
    print(f"extended quantity rows checked: {quantity_rows}")
    print("manufacturing release remains HOLD until blocking files are replaced and approved")


if __name__ == "__main__":
    main()
