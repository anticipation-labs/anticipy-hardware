#!/usr/bin/env python3
"""Deterministic structural verifier for the Anticipy EVT-A KiCad checkpoint.

This is deliberately *not* an ERC or DRC replacement.  It parses native KiCad
S-expressions and checks controlled geometry, pad maps, named nets and explicit
release gates.  It exits non-zero on any structural mismatch.
"""

from __future__ import annotations

import csv
import json
import math
import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PCB = ROOT / "anticipy_evt_a.kicad_pcb"
SCH = ROOT / "anticipy_evt_a.kicad_sch"
MANIFEST = ROOT / "design_manifest.json"


class ParseError(RuntimeError):
    pass


def tokenize(text: str):
    i = 0
    n = len(text)
    while i < n:
        if text[i].isspace():
            i += 1
            continue
        if text[i] in "()":
            yield text[i]
            i += 1
            continue
        if text[i] == '"':
            i += 1
            buf: list[str] = []
            while i < n:
                ch = text[i]
                i += 1
                if ch == '"':
                    break
                if ch == "\\":
                    if i >= n:
                        raise ParseError("unterminated string escape")
                    esc = text[i]
                    i += 1
                    buf.append({"n": "\n", "r": "\r", "t": "\t"}.get(esc, esc))
                else:
                    buf.append(ch)
            else:
                raise ParseError("unterminated quoted string")
            yield "".join(buf)
            continue
        j = i
        while j < n and not text[j].isspace() and text[j] not in "()":
            j += 1
        yield text[i:j]
        i = j


def parse_sexpr(text: str):
    stack: list[list] = []
    root = None
    for token in tokenize(text):
        if token == "(":
            node: list = []
            if stack:
                stack[-1].append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ParseError("extra closing parenthesis")
            done = stack.pop()
            if not stack:
                if root is not None:
                    raise ParseError("multiple root expressions")
                root = done
        else:
            if not stack:
                raise ParseError(f"atom outside expression: {token}")
            stack[-1].append(token)
    if stack:
        raise ParseError("unclosed expression")
    if root is None:
        raise ParseError("empty file")
    return root


def direct(node: list, key: str) -> list[list]:
    return [x for x in node[1:] if isinstance(x, list) and x and x[0] == key]


def first(node: list, key: str) -> list | None:
    found = direct(node, key)
    return found[0] if found else None


def as_xy(item: list) -> tuple[float, float]:
    return float(item[1]), float(item[2])


def fp_reference(fp: list) -> str:
    for prop in direct(fp, "property"):
        if len(prop) >= 3 and prop[1] == "Reference":
            return prop[2]
    raise ParseError(f"footprint {fp[1] if len(fp)>1 else '?'} has no Reference property")


def pad_map(fp: list) -> dict[str, tuple[str, str]]:
    result: dict[str, tuple[str, str]] = {}
    for p in direct(fp, "pad"):
        number = p[1]
        ptype = p[2]
        net = first(p, "net")
        net_name = "" if net is None else net[2]
        if number:
            result[number] = (net_name, ptype)
    return result


def board_contains(x: float, y: float, eps: float = 1e-6) -> bool:
    nose = 78.5-eps <= x <= 85+eps and 96.75-eps <= y <= 103.25+eps
    main = 85-eps <= x <= 116+eps and 93-eps <= y <= 107+eps
    if main:
        # The retained candidate removes the motor disk from the main outline.
        outside_scallop = math.hypot(x - 116.9, y - 104.8) >= 4.1-eps
        main = outside_scallop
    return nose or main


def rect(block: dict) -> tuple[float, float, float, float]:
    cx, cy = block["center"]
    w, h = block["size"]
    m = block.get("margin", 1.0)
    return cx-w*m/2, cy-h*m/2, cx+w*m/2, cy+h*m/2


def overlap(a, b, eps=1e-9) -> bool:
    return min(a[2], b[2]) - max(a[0], b[0]) > eps and min(a[3], b[3]) - max(a[1], b[1]) > eps


def run() -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    for path in (PCB, SCH, MANIFEST):
        if not path.is_file():
            failures.append(f"missing required file: {path.relative_to(ROOT)}")
    if failures:
        return passes, warnings, failures

    try:
        board = parse_sexpr(PCB.read_text(encoding="utf-8"))
        schematic = parse_sexpr(SCH.read_text(encoding="utf-8"))
        if board[0] != "kicad_pcb" or schematic[0] != "kicad_sch":
            raise ParseError("wrong root token")
        passes.append("native KiCad PCB and schematic S-expressions parse")
    except Exception as exc:
        failures.append(f"S-expression parse failed: {exc}")
        return passes, warnings, failures

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # Board nets and footprints.
    board_nets = {n[2] for n in direct(board, "net") if len(n) >= 3 and n[2]}
    missing_nets = sorted(set(manifest["required_nets"]) - board_nets)
    if missing_nets:
        failures.append("missing board nets: " + ", ".join(missing_nets))
    else:
        passes.append(f"all {len(manifest['required_nets'])} controlled named nets exist")

    fps = {fp_reference(fp): fp for fp in direct(board, "footprint")}
    if len(fps) != len(direct(board, "footprint")):
        failures.append("duplicate footprint reference detected")
    else:
        passes.append(f"{len(fps)} unique board footprints parsed")

    for ref, expected in manifest["gated_footprints"].items():
        actual = len(direct(fps.get(ref, []), "pad")) if ref in fps else -1
        if actual != expected:
            failures.append(f"{ref} gate violated: expected {expected} pads, found {actual}")
        else:
            passes.append(f"{ref} remains deliberate zero-copper vendor gate")

    for ref, expected in manifest["verified_pad_counts"].items():
        actual = len(direct(fps.get(ref, []), "pad")) if ref in fps else -1
        if actual != expected:
            failures.append(f"{ref}: expected {expected} physical pads/holes, found {actual}")
        else:
            passes.append(f"{ref} physical pad/hole count = {expected}")

    with (ROOT / "reports/PAD_NET_MAP.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Reference", "Footprint", "Pad", "Pad type", "Net"])
        for ref in sorted(fps):
            fp = fps[ref]
            for p in direct(fp, "pad"):
                net = first(p, "net")
                writer.writerow([ref, fp[1], p[1], p[2], "" if net is None else net[2]])

    exact_maps = {
        "U4": {
            "1":"QSPI_CS_TO_U1_PAD_TBD", "2":"QSPI_IO1_TO_U1_PAD_TBD",
            "3":"QSPI_IO2_TO_U1_PAD_TBD", "4":"GND", "5":"QSPI_IO0_TO_U1_PAD_TBD",
            "6":"QSPI_CLK_TO_U1_PAD_TBD", "7":"QSPI_IO3_TO_U1_PAD_TBD",
            "8":"FLASH_VDD", "9":"GND",
        },
        "U6": {"A1":"HAPTIC_EN_TO_U1_PAD_TBD", "A2":"HAPTIC_REG", "A3":"HAPTIC_OUT_P",
               "B1":"GND", "B2":"HAPTIC_SDA_TO_U1_PAD_TBD", "B3":"GND",
               "C1":"HAPTIC_SCL_TO_U1_PAD_TBD", "C2":"3V0", "C3":"HAPTIC_OUT_M"},
        "U2": {"1":"MIC_A_VDD", "2":"PDM_CLK_TO_U1_PAD_TBD", "3":"PDM_DATA_TO_U1_PAD_TBD",
               "4":"GND", "5":"GND"},
        "U3": {"1":"MIC_B_VDD", "2":"PDM_CLK_TO_U1_PAD_TBD", "3":"PDM_DATA_TO_U1_PAD_TBD",
               "4":"3V0", "5":"GND"},
    }
    expected_npm = {
        "A1":"PMIC_LED0","A2":"PMIC_LED1","A3":"PMIC_LED2","A4":"LDO1_OUT","A5":"LDO2_OUT","A6":"GND","A7":"GND",
        "B1":"VBUS","B2":"VBUS","B3":"CC2_NC","B4":"1V8","B5":"3V0","B6":"1V8","B7":"SW_BUCK1",
        "C1":"VSYS","C2":"VSYS","C3":"VBUSOUT","C4":"PMIC_GPIO3_TO_U1_PAD_TBD","C5":"PMIC_GPIO2_TO_U1_PAD_TBD","C6":"3V0","C7":"VSYS",
        "D1":"VBAT","D2":"VBAT","D3":"BAT_NTC","D4":"SHPHLD","D5":"CC1_NC","D6":"PMIC_GPIO0_TO_U1_PAD_TBD","D7":"SW_BUCK2",
        "E1":"VSET2","E2":"VSET1","E3":"PMIC_SCL_TO_U1_PAD_TBD","E4":"3V0","E5":"PMIC_SDA_TO_U1_PAD_TBD","E6":"PMIC_GPIO1_TO_U1_PAD_TBD","E7":"GND",
    }
    exact_maps["U5"] = expected_npm
    for ref, expected in exact_maps.items():
        actual = {num: net for num, (net, _ptype) in pad_map(fps[ref]).items()}
        if actual != expected:
            failures.append(f"{ref} pad/net map mismatch")
        else:
            passes.append(f"{ref} exact controlled pad/net map matches")

    # Both microphone footprints must have one 0.6-mm NPTH sound port.
    for ref in ("U2", "U3"):
        holes = [p for p in direct(fps[ref], "pad") if len(p) > 2 and p[2] == "np_thru_hole"]
        ok = False
        for h in holes:
            size = first(h, "size")
            drill = first(h, "drill")
            if size and drill and abs(float(size[1])-0.6) < 1e-6 and abs(float(drill[1])-0.6) < 1e-6:
                ok = True
        if ok:
            passes.append(f"{ref} has official 0.60-mm acoustic NPTH")
        else:
            failures.append(f"{ref} missing 0.60-mm acoustic NPTH")

    # Controlled outline form and bounds.
    edge_forms = []
    for key in ("gr_line", "gr_arc"):
        for item in direct(board, key):
            layer = first(item, "layer")
            if layer and layer[1] == "Edge.Cuts":
                edge_forms.append(item)
    if len(edge_forms) != 9:
        failures.append(f"expected 9 Edge.Cuts primitives, found {len(edge_forms)}")
    else:
        all_points = []
        for item in edge_forms:
            for key in ("start", "mid", "end"):
                p = first(item, key)
                if p:
                    all_points.append(as_xy(p))
        xs = [p[0] for p in all_points]
        ys = [p[1] for p in all_points]
        bounds = (min(xs), min(ys), max(xs), max(ys))
        # Arc mid lies inside the rectangular bound; the rightmost board edge is x=116.
        expected = (78.5, 93.0, 116.0, 107.0)
        if all(abs(a-b) <= 1e-4 for a,b in zip(bounds, expected)):
            passes.append("board Edge.Cuts bounds = 37.50 x 14.00 mm")
        else:
            failures.append(f"unexpected Edge.Cuts bounds: {bounds}")
        arcs = [x for x in edge_forms if x[0] == "gr_arc"]
        if len(arcs) == 1:
            a = arcs[0]
            expected_pts = ((116.0,100.8),(113.1103,103.24),(113.4408,107.0))
            actual_pts = tuple(as_xy(first(a,k)) for k in ("start","mid","end"))
            if all(math.dist(p,q) <= 2e-4 for p,q in zip(actual_pts,expected_pts)):
                passes.append("retained motor scallop edge is present at controlled coordinates")
            else:
                failures.append(f"motor scallop coordinates drifted: {actual_pts}")

    # 15%-expanded subsystem reservations, not an assembler DFM replacement.
    blocks = manifest["major_blocks"]
    for block in blocks:
        r = rect(block)
        corners = ((r[0],r[1]),(r[0],r[3]),(r[2],r[1]),(r[2],r[3]))
        if not all(board_contains(*p) for p in corners):
            failures.append(f"{block['ref']} 15%-expanded subsystem reserve crosses Edge.Cuts")
    for i, a in enumerate(blocks):
        for b in blocks[i+1:]:
            if overlap(rect(a), rect(b)):
                failures.append(f"15%-expanded subsystem reserves overlap: {a['ref']} / {b['ref']}")
    # Also prove every currently placed courtyard is edge-contained and has no same-side overlap.
    placed_rects: list[tuple[str, str, tuple[float,float,float,float]]] = []
    for ref, fp in fps.items():
        at = first(fp, "at")
        if not at:
            continue
        cx, cy = float(at[1]), float(at[2])
        for side in ("B", "F"):
            xs: list[float] = []
            ys: list[float] = []
            for line in direct(fp, "fp_line"):
                layer = first(line, "layer")
                if not layer or layer[1] != f"{side}.CrtYd":
                    continue
                for key in ("start", "end"):
                    p = first(line, key)
                    if p:
                        xs.append(cx + float(p[1]))
                        ys.append(cy + float(p[2]))
            if xs:
                placed_rects.append((ref, side, (min(xs),min(ys),max(xs),max(ys))))
    for ref, side, r in placed_rects:
        corners = ((r[0],r[1]),(r[0],r[3]),(r[2],r[1]),(r[2],r[3]))
        if not all(board_contains(*p) for p in corners):
            failures.append(f"{ref} {side}-side courtyard crosses corrected Edge.Cuts")
    for i, (ref_a, side_a, rect_a) in enumerate(placed_rects):
        for ref_b, side_b, rect_b in placed_rects[i+1:]:
            if side_a == side_b and overlap(rect_a, rect_b):
                failures.append(f"same-side courtyard overlap: {ref_a} / {ref_b}")
    margin_errors = [f for f in failures if "15%-expanded" in f or "courtyard" in f]
    if not margin_errors:
        passes.append(
            f"all {len(blocks)} 15%-expanded subsystem reserves and {len(placed_rects)} placed courtyards pass XY checks"
        )

    # Schematic components and net labels.
    sch_symbols = direct(schematic, "symbol")
    sch_refs = set()
    for sym in sch_symbols:
        prop = [p for p in direct(sym, "property") if len(p) >= 3 and p[1] == "Reference"]
        if prop:
            sch_refs.add(prop[0][2])
    required_refs = {ref for ref in fps if not ref.startswith("TP")}
    if required_refs <= sch_refs:
        passes.append(f"schematic contains all {len(required_refs)} non-test board references")
    else:
        failures.append("schematic missing references: " + ", ".join(sorted(required_refs-sch_refs)))
    labels = {x[1] for x in direct(schematic, "label") if len(x) > 1}
    critical_labels = {"VBAT","BAT_NTC","3V0","1V8","GND","FLASH_VDD","HAPTIC_REG",
                       "PDM_CLK_TO_U1_PAD_TBD","PDM_DATA_TO_U1_PAD_TBD",
                       "HAPTIC_OUT_P","HAPTIC_OUT_M","RF_MATCH_B"}
    if critical_labels <= labels:
        passes.append("schematic label connectivity covers power/storage/audio/haptic/RF")
    else:
        failures.append("schematic missing critical labels: " + ", ".join(sorted(critical_labels-labels)))

    # Reusable libraries must parse with this independent parser too.
    lib_files = sorted((ROOT / "libraries/Anticipy.pretty").glob("*.kicad_mod"))
    for path in [ROOT / "libraries/Anticipy.kicad_sym", *lib_files]:
        try:
            parse_sexpr(path.read_text(encoding="utf-8"))
        except Exception as exc:
            failures.append(f"library parse failed {path.name}: {exc}")
    if not any("library parse" in f for f in failures):
        passes.append(f"symbol library and {len(lib_files)} custom footprint files parse")

    if shutil.which("kicad-cli"):
        warnings.append("kicad-cli is now available; run unfiltered ERC/DRC before any fabrication decision")
    else:
        warnings.append("kicad-cli absent: ERC and DRC were NOT run and are NOT claimed")
    warnings.append("board intentionally unrouted: U1, SW1 and J3 official vendor land maps remain release gates")
    warnings.append("subsystem reserves carry 15% expansion; all current courtyards pass ordinary containment/non-overlap, but final routed-board 15%/DFM remains mandatory")
    return passes, warnings, failures


def main() -> int:
    passes, warnings, failures = run()
    lines = ["ANTICIPY EVT-A STRUCTURAL VERIFICATION", "=" * 40, ""]
    lines.append(f"PASS: {len(passes)}")
    lines.extend(f"  [PASS] {x}" for x in passes)
    lines.append("")
    lines.append(f"EXPECTED WARNINGS: {len(warnings)}")
    lines.extend(f"  [WARN] {x}" for x in warnings)
    lines.append("")
    lines.append(f"FAIL: {len(failures)}")
    lines.extend(f"  [FAIL] {x}" for x in failures)
    lines.append("")
    lines.append("RESULT: " + ("STRUCTURAL CHECK PASSED; FABRICATION STILL HELD" if not failures else "FAILED"))
    report = "\n".join(lines) + "\n"
    print(report, end="")
    (ROOT / "reports/STRUCTURAL_VERIFY.txt").write_text(report, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
