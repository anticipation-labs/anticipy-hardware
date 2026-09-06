#!/usr/bin/env python3
"""Dependency-free integrity and release-state check for Anticipy v1.0."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


checks: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str) -> None:
    checks.append((name, bool(condition), detail))


required = [
    "START_HERE.md",
    "DECISION_CARD.md",
    "RELEASE_STATUS.md",
    "01_PRINT_NOW/Anticipy_v09_five_units_P2S.3mf",
    "01_PRINT_NOW/PROTOTYPE_CART_5_UNITS.csv",
    "02_PRODUCTION_CAD/production_full_assembly.step",
    "02_PRODUCTION_CAD/production_fit_report.json",
    "03_PRODUCTION_PCB/anticipy_evt_a.kicad_pcb",
    "03_PRODUCTION_PCB/V1_CORRECTION_ORDER.md",
    "04_FIRMWARE/Anticipy_Founder_EVT_v0.9.0.uf2",
    "05_QA_FIXTURES/validate_package.py",
    "06_FACTORY/FACTORY_UPLOAD_MANIFEST.csv",
    "07_SOURCES/MKDV4GCL-ABF_datasheet.pdf",
    "08_REPORTS/PRODUCTION_CANDIDATE_BOM.csv",
]
missing = [name for name in required if not (ROOT / name).is_file()]
check("required package files", not missing, ", ".join(missing) or "all present")

fit = json.loads((ROOT / "02_PRODUCTION_CAD/production_fit_report.json").read_text())
fit_checks = fit.get("checks", [])
check(
    "production mechanical checks",
    len(fit_checks) == 23 and all(row.get("pass") for row in fit_checks),
    f"{sum(bool(row.get('pass')) for row in fit_checks)}/{len(fit_checks)} pass",
)
finished = fit.get("nominal_finished_envelope_including_button_mm")
check("PLAUD-size envelope", finished == [50.5, 20.68, 10.8], str(finished))
storage = fit.get("storage", {})
check(
    "20-hour storage math",
    abs(float(storage.get("required_MB", 0)) - 414.0) < 0.001
    and abs(float(storage.get("usable_budget_MB", 0)) - 481.0) < 0.001,
    str(storage),
)

lab = json.loads((ROOT / "01_PRINT_NOW/v09_release_validation.json").read_text())
lab_fit = lab.get("fit_checks", {})
check(
    "print-now digital validation",
    lab.get("status") == "PASS_DIGITAL_ONLY"
    and lab_fit.get("passed") == lab_fit.get("total") == 27,
    f"{lab_fit.get('passed')}/{lab_fit.get('total')} pass",
)

pcb = (ROOT / "03_PRODUCTION_PCB/anticipy_evt_a.kicad_pcb").read_text(errors="replace")
segments = len(re.findall(r"^  \(segment\b", pcb, re.MULTILINE))
vias = len(re.findall(r"^  \(via\b", pcb, re.MULTILINE))
zones = len(re.findall(r"^  \(zone\b", pcb, re.MULTILINE))
check("PCB fabrication hold preserved", segments == vias == zones == 0, f"segments={segments}, vias={vias}, zones={zones}")
fab_suffixes = {".gbr", ".ger", ".gtl", ".gbl", ".gts", ".gbs", ".drl"}
fab_files = [p for p in (ROOT / "03_PRODUCTION_PCB").rglob("*") if p.suffix.lower() in fab_suffixes]
check("no misleading Gerbers", not fab_files, ", ".join(p.name for p in fab_files) or "none")

firmware_hash = sha256(ROOT / "04_FIRMWARE/Anticipy_Founder_EVT_v0.9.0.uf2")
check(
    "lab UF2 identity",
    firmware_hash == "de31edba36d077338b6fb1649782a68cce61e89c01a68cdfd9749c2ffc011f44",
    firmware_hash,
)

with (ROOT / "06_FACTORY/FACTORY_UPLOAD_MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))
reference_rows = [row for row in rows if row["status"] == "REFERENCE_ONLY"]
blocking_rows = [row for row in rows if row["status"] == "MISSING_BLOCKING"]
reference_ok = True
for row in reference_rows:
    path = (ROOT / "06_FACTORY" / row["relative_path"]).resolve()
    reference_ok &= path.is_file() and path.stat().st_size == int(row["size_bytes"]) and sha256(path) == row["sha256"]
check("factory reference identities", reference_ok and len(reference_rows) == 9, f"{len(reference_rows)} references")
check("factory blockers exposed", len(blocking_rows) == 22, f"{len(blocking_rows)} blockers")

failed = [name for name, passed, _ in checks if not passed]
for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")
print(f"\nRESULT: {len(checks) - len(failed)}/{len(checks)} package checks passed")
print("FABRICATION STATE: HOLD — NO GERBERS")
raise SystemExit(1 if failed else 0)
