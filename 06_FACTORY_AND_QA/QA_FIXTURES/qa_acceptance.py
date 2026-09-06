#!/usr/bin/env python3
"""Evaluate a filled Anticipy fixture/DUT acceptance CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys


REQUIRED = {
    "fixture_id", "dut_serial", "test_group", "test_id", "metric", "unit",
    "lower_limit", "upper_limit", "expected_text", "actual", "critical", "notes", "evidence"
}


def yes(value: str) -> bool:
    return value.strip().upper() in {"Y", "YES", "TRUE", "1"}


def evaluate(row: dict[str, str]) -> tuple[str, str]:
    actual = row["actual"].strip()
    if not actual:
        return "INCOMPLETE", "actual is blank"
    expected = row["expected_text"].strip()
    lower = row["lower_limit"].strip()
    upper = row["upper_limit"].strip()
    if expected:
        passed = actual.casefold() == expected.casefold()
        return ("PASS", "text matched") if passed else ("FAIL", f"expected {expected!r}")
    try:
        number = float(actual)
        lo = float(lower) if lower else None
        hi = float(upper) if upper else None
    except ValueError:
        return "INVALID", "numeric test contains non-numeric value"
    if lo is None and hi is None:
        return "INVALID", "no expected_text or numeric limit"
    if lo is not None and number < lo:
        return "FAIL", f"below lower limit {lo:g}"
    if hi is not None and number > hi:
        return "FAIL", f"above upper limit {hi:g}"
    return "PASS", "within limit"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="filled acceptance CSV")
    parser.add_argument("--output-csv", type=Path, help="evaluated CSV path")
    parser.add_argument("--output-json", type=Path, help="summary JSON path")
    args = parser.parse_args()

    try:
        with args.csv_file.open(newline="", encoding="utf-8-sig") as stream:
            reader = csv.DictReader(stream)
            missing = REQUIRED - set(reader.fieldnames or [])
            if missing:
                raise ValueError("missing columns: " + ", ".join(sorted(missing)))
            rows = list(reader)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    if not rows:
        print("ERROR: acceptance CSV has no tests", file=sys.stderr)
        return 3

    counts = {"PASS": 0, "FAIL": 0, "INCOMPLETE": 0, "INVALID": 0}
    critical_failures = []
    for row in rows:
        result, reason = evaluate(row)
        row["result"] = result
        row["evaluation"] = reason
        counts[result] += 1
        if yes(row["critical"]) and result != "PASS":
            critical_failures.append({"test_id": row["test_id"], "result": result, "reason": reason})

    overall = "PASS"
    exit_code = 0
    if counts["INVALID"] or counts["INCOMPLETE"]:
        overall, exit_code = "INCOMPLETE", 2
    if counts["FAIL"]:
        overall, exit_code = "FAIL", 1

    summary = {
        "result": overall,
        "source": str(args.csv_file),
        "test_count": len(rows),
        "counts": counts,
        "critical_nonpasses": critical_failures,
    }
    fieldnames = list(rows[0].keys())
    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
