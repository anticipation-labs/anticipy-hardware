#!/usr/bin/env python3
"""Verify R0B spec -> native KiCad schematic -> exported netlist equivalence.

This is connectivity verification, not ERC.  KiCad 7 does not expose schematic
ERC through ``kicad-cli``.  If ``kicad-cli`` is absent, the script performs
deterministic/static checks and exits 2 unless ``--allow-static-only`` is set.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

from design_spec_r0b import PARTS, PROJECT, expected_nodes, validate_spec
from generate_schematic_r0b import OUT as SCHEMATIC, make_schematic


ROOT = Path(__file__).resolve().parent
DEFAULT_NETLIST = ROOT / "reports" / f"{PROJECT}.net.xml"


def exported_nodes(path: Path) -> dict[str, set[tuple[str, str]]]:
    root = ET.parse(path).getroot()
    result: dict[str, set[tuple[str, str]]] = {}
    nets = root.find("nets")
    if nets is None:
        raise ValueError(f"{path}: KiCad XML netlist has no <nets> section")
    for net in nets.findall("net"):
        name = net.attrib.get("name", "")
        # KiCad's XML exporter gives every explicitly no-connected pin a
        # synthetic one-node net.  The no-connect set is checked separately by
        # static_checks(); these are intentionally absent from the design NETS.
        if name.startswith("unconnected-("):
            continue
        # KiCad may prefix a root-sheet local-label net with one slash.
        if name.startswith("/") and "/" not in name[1:]:
            name = name[1:]
        result[name] = {
            (node.attrib["ref"], node.attrib["pin"])
            for node in net.findall("node")
        }
    return result


def compare(expected: dict[str, set[tuple[str, str]]],
            actual: dict[str, set[tuple[str, str]]]) -> list[str]:
    errors: list[str] = []
    for net in sorted(set(expected) | set(actual)):
        missing = expected.get(net, set()) - actual.get(net, set())
        extra = actual.get(net, set()) - expected.get(net, set())
        if net not in actual:
            errors.append(f"missing net {net}")
        if net not in expected:
            errors.append(f"unexpected net {net}")
        if missing:
            errors.append(f"{net}: missing nodes {sorted(missing)}")
        if extra:
            errors.append(f"{net}: unexpected nodes {sorted(extra)}")
    return errors


def static_checks(text: str) -> list[str]:
    errors = validate_spec()
    if text != make_schematic():
        errors.append("schematic is stale or was hand-edited; regenerate it")
    expected_nc = sum(pin.net is None for item in PARTS for pin in item.pins)
    actual_nc = text.count("  (no_connect (at ")
    if actual_nc != expected_nc:
        errors.append(f"explicit no-connect count {actual_nc}, expected {expected_nc}")
    expected_labels = sum(pin.net is not None for item in PARTS for pin in item.pins)
    actual_labels = text.count("  (label ")
    if actual_labels != expected_labels:
        errors.append(f"label count {actual_labels}, expected {expected_labels}")
    for forbidden in ("5.1k USB CC1", "5.1k USB CC2", "USB4105-GF-A", "microSD"):
        if forbidden in text:
            errors.append(f"obsolete R0 design token remains: {forbidden}")
    return errors


def export_netlist(schematic: Path, netlist: Path) -> tuple[bool, str]:
    cli = shutil.which("kicad-cli")
    if cli is None:
        return False, "kicad-cli is not installed in this runtime"
    netlist.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [cli, "sch", "export", "netlist", "--format", "kicadxml",
         "-o", str(netlist), str(schematic)],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode == 0, result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schematic", type=Path, default=SCHEMATIC)
    parser.add_argument("--netlist", type=Path, help="compare an existing KiCad XML netlist")
    parser.add_argument("--allow-static-only", action="store_true",
                        help="return success when KiCad CLI is unavailable")
    args = parser.parse_args()

    if not args.schematic.exists():
        args.schematic.write_text(make_schematic(), encoding="utf-8")
    text = args.schematic.read_text(encoding="utf-8")
    errors = static_checks(text)
    if errors:
        print("STATIC VERIFICATION FAILED", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print("Static spec/schematic checks: PASS")

    netlist = args.netlist or DEFAULT_NETLIST
    if args.netlist is None:
        ok, detail = export_netlist(args.schematic, netlist)
        if not ok:
            print(f"KiCad netlist export BLOCKED: {detail}", file=sys.stderr)
            print("No ERC claim is made. Run this script in a KiCad 7+ environment.",
                  file=sys.stderr)
            return 0 if args.allow_static_only else 2
        if detail:
            print(detail)
    if not netlist.exists():
        print(f"Netlist not found: {netlist}", file=sys.stderr)
        return 1
    errors = compare(expected_nodes(), exported_nodes(netlist))
    if errors:
        print("NET EQUIVALENCE FAILED", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"KiCad exported-net equivalence: PASS ({len(expected_nodes())} nets)")
    print("ERC status: NOT RUN (KiCad 7 CLI has no schematic ERC command)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
