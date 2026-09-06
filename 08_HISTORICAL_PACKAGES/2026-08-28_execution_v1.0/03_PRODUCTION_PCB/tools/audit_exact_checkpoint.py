#!/usr/bin/env python3
"""Read-only audit of the exact-size Anticipy v0.6 KiCad checkpoint.

The script deliberately does not edit the source checkpoint, run fabrication
outputs, or represent structural parsing as KiCad ERC/DRC.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


BASELINE = Path(__file__).resolve().parents[1]
OUT = BASELINE / "reports" / "EXACT_V06_AUDIT.txt"


def balanced_forms(text: str, marker: str) -> list[str]:
    forms: list[str] = []
    cursor = 0
    while True:
        start = text.find(marker, cursor)
        if start < 0:
            return forms
        depth = 0
        quoted = False
        escaped = False
        for pos in range(start, len(text)):
            char = text[pos]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    forms.append(text[start : pos + 1])
                    cursor = pos + 1
                    break
        else:
            raise ValueError(f"unbalanced form beginning at byte {start}")


def footprint_inventory(board: str) -> dict[str, dict[str, object]]:
    inventory: dict[str, dict[str, object]] = {}
    for form in balanced_forms(board, '  (footprint "'):
        ref_match = re.search(r'\(property "Reference" "([^"]+)"', form)
        value_match = re.search(r'\(property "Value" "([^"]*)"', form)
        lib_match = re.match(r'\s*\(footprint "([^"]+)"', form)
        if not (ref_match and value_match and lib_match):
            continue
        pads = balanced_forms(form, "    (pad ")
        copper = [p for p in pads if "np_thru_hole" not in p]
        inventory[ref_match.group(1)] = {
            "library": lib_match.group(1),
            "value": value_match.group(1),
            "pads": len(pads),
            "copper_pads": len(copper),
        }
    return inventory


def main() -> int:
    board_path = BASELINE / "anticipy_evt_a.kicad_pcb"
    sch_path = BASELINE / "anticipy_evt_a.kicad_sch"
    manifest_path = BASELINE / "design_manifest.json"
    required = [board_path, sch_path, manifest_path, BASELINE / "anticipy_evt_a.kicad_pro"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise SystemExit("missing source files: " + ", ".join(missing))

    board = board_path.read_text(encoding="utf-8")
    schematic = sch_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = footprint_inventory(board)
    gates = {ref: inventory[ref] for ref in ("U1", "SW1", "J3")}

    segments = len(re.findall(r"^  \(segment\b", board, re.MULTILINE))
    vias = len(re.findall(r"^  \(via\b", board, re.MULTILINE))
    zones = len(re.findall(r"^  \(zone\b", board, re.MULTILINE))
    gerber_suffixes = {".gbr", ".ger", ".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo", ".drl"}
    fabrication = sorted(
        str(path.relative_to(BASELINE))
        for path in BASELINE.rglob("*")
        if path.is_file() and path.suffix.lower() in gerber_suffixes
    )
    kicad_cli = shutil.which("kicad-cli")

    architecture_checks = {
        "37.5 x 14.0 mm manifest": manifest.get("board", {}).get("overall_size_mm") == [37.5, 14.0],
        "0.60 mm board": manifest.get("board", {}).get("thickness_mm") == 0.6 and "(thickness 0.6)" in board,
        "four copper layers": manifest.get("board", {}).get("layers") == 4,
        "nPM1300 U5": inventory.get("U5", {}).get("value") == "nPM1300-CAAA",
        "dual IM69D128S": inventory.get("U2", {}).get("value") == "IM69D128S" and inventory.get("U3", {}).get("value") == "IM69D128S",
        "W25N04KV U4": inventory.get("U4", {}).get("value") == "W25N04KVZEIR",
        "DRV2605L U6": inventory.get("U6", {}).get("value") == "DRV2605LYZFR",
    }

    lines = [
        "ANTICIPY EXACT v0.6 PCB READ-ONLY AUDIT",
        "=======================================",
        f"Source: {BASELINE}",
        "Source files modified: NO",
        "Fabrication outputs generated: NO",
        "",
        "Architecture identity",
    ]
    lines.extend(f"  {'PASS' if ok else 'FAIL'}  {label}" for label, ok in architecture_checks.items())
    lines += ["", "Three zero-copper release gates"]
    for ref, info in gates.items():
        lines.append(
            f"  {ref}: {info['library']} | {info['value']} | "
            f"physical pads={info['pads']}, copper pads={info['copper_pads']}"
        )
    lines += [
        "",
        "Connectivity / fabrication state",
        f"  Board-level routed segments: {segments}",
        f"  Board-level vias: {vias}",
        f"  Copper zones: {zones}",
        f"  Gerber/drill files present: {len(fabrication)}",
        f"  kicad-cli available: {'YES (' + kicad_cli + ')' if kicad_cli else 'NO'}",
        f"  Schematic still embeds U1_GATE: {'YES' if 'Anticipy:U1_GATE' in schematic else 'NO'}",
        "",
        "Verdict",
        "  STRUCTURAL AUDIT: PASS" if all(architecture_checks.values()) else "  STRUCTURAL AUDIT: FAIL",
        "  ROUTED: NO" if segments == 0 else "  ROUTED: PARTIAL/YES (manual review required)",
        "  ERC: NOT RUN",
        "  DRC: NOT RUN",
        "  DRC-CLEAN: NOT CLAIMED / NO",
        "  FABRICATION: HOLD - NO GERBERS",
        "",
        "This result is a text/structure audit only. It is not a substitute for opening the project in",
        "KiCad 9, updating the PCB from the corrected schematic, routing, and running unfiltered ERC/DRC.",
    ]
    if fabrication:
        lines += ["", "Unexpected fabrication files:", *[f"  {name}" for name in fabrication]]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all(architecture_checks.values()) and not fabrication else 1


if __name__ == "__main__":
    raise SystemExit(main())
