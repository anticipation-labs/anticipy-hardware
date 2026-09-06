#!/usr/bin/python3
"""Independent release gate for the ANT-PROD-R0B EVT KiCad PCB.

Run this file with KiCad's system Python::

    /usr/bin/python3 verify_project_r0b.py

The script deliberately exits non-zero while routing or DRC work remains.  A
zero exit code means only that the machine-checkable board rules below pass;
it does not replace RF, battery, enclosure, or first-article validation.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import math
from pathlib import Path
import re
import sys

try:
    import pcbnew
except ImportError as exc:  # pragma: no cover - depends on the local KiCad install
    raise SystemExit(
        "pcbnew is unavailable. Run with KiCad's Python: "
        "/usr/bin/python3 verify_project_r0b.py"
    ) from exc

from design_spec_r0b import PARTS, PART_BY_REF, validate_spec


ROOT = Path(__file__).resolve().parent
DEFAULT_BOARD = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
DEFAULT_DRC_REPORT = ROOT / "reports" / "verify_project_r0b_drc.txt"

MAX_BOARD_WIDTH_MM = 47.0
MAX_BOARD_HEIGHT_MM = 18.0
TARGET_THICKNESS_MM = 0.8
DIMENSION_TOLERANCE_MM = 0.001
THICKNESS_TOLERANCE_MM = 0.01
EXPECTED_USB_PADS = {*(str(number) for number in range(1, 13)),
                     "S1", "S2", "S3", "S4"}
USB_SHELL_PADS = {"S1", "S2", "S3", "S4"}
ALLOWED_MECHANICAL_REFS = {"MH_BAT", "MH_MOTOR", "MH_BUTTON", "MH_LED"}
EXPECTED_REAR_ELECTRICAL_REFS = {
    "BT1", "M1", *(f"TP{number}" for number in range(1, 15)),
}
BATTERY_LENGTH_MM = 26.0
BATTERY_WIDTH_MM = 15.5
MOTOR_DIAMETER_MM = 10.0
PHYSICAL_TOLERANCE_MM = 0.01


def as_mm(value: int) -> float:
    return float(pcbnew.ToMM(value))


def format_list(values: list[str] | set[str] | tuple[str, ...]) -> str:
    return ", ".join(sorted(values, key=lambda item: (len(item), item)))


def get_footprints_by_reference(board: pcbnew.BOARD) -> tuple[
        dict[str, pcbnew.FOOTPRINT], Counter[str]]:
    footprints = list(board.GetFootprints())
    counts = Counter(fp.GetReference() for fp in footprints)
    return {fp.GetReference(): fp for fp in footprints}, counts


def pads_by_number(footprint: pcbnew.FOOTPRINT) -> dict[str, list[pcbnew.PAD]]:
    result: dict[str, list[pcbnew.PAD]] = defaultdict(list)
    for pad in footprint.Pads():
        result[str(pad.GetNumber())].append(pad)
    return result


def board_net_names(board: pcbnew.BOARD) -> set[str]:
    return {
        str(name)
        for name in board.GetNetInfo().NetsByName()
        if str(name)
    }


def is_banned_legacy_name(name: str) -> bool:
    """Reject names associated with the abandoned removable-SD/user-button design."""
    upper = name.upper().replace("-", "_").replace(" ", "_")
    if any(token in upper for token in (
        "MICROSD", "MICRO_SD", "USER_BTN", "USER_BUTTON", "LDO2_OUT",
    )):
        return True
    # Catch SD, SD_CLK, SD_MOSI, etc. without flagging valid names such as SDA,
    # SWDIO, or the word "SOLDER" in a descriptive field.
    return upper == "SD" or upper.startswith("SD_") or upper.endswith("_SD")


def footprint_position_mm(footprint: pcbnew.FOOTPRINT) -> tuple[float, float]:
    position = footprint.GetPosition()
    return as_mm(position.x), as_mm(position.y)


def oriented_rectangle(
    centre_x: float,
    centre_y: float,
    length: float,
    width: float,
    rotation_degrees: float,
) -> list[tuple[float, float]]:
    """Return the four corners of a centred physical envelope.

    The battery and motor envelopes are symmetric about both local axes, so a
    bottom-side mirror does not change the occupied polygon; only the reported
    footprint rotation and position are required.
    """
    angle = math.radians(rotation_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    corners: list[tuple[float, float]] = []
    for local_x, local_y in (
        (-length / 2.0, -width / 2.0),
        (+length / 2.0, -width / 2.0),
        (+length / 2.0, +width / 2.0),
        (-length / 2.0, +width / 2.0),
    ):
        corners.append((
            centre_x + local_x * cosine - local_y * sine,
            centre_y + local_x * sine + local_y * cosine,
        ))
    return corners


def rectangle_from_box(box: pcbnew.BOX2I) -> list[tuple[float, float]]:
    left = as_mm(box.GetX())
    top = as_mm(box.GetY())
    right = left + as_mm(box.GetWidth())
    bottom = top + as_mm(box.GetHeight())
    return [(left, top), (right, top), (right, bottom), (left, bottom)]


def polygon_bounds(
    polygon: list[tuple[float, float]],
) -> tuple[float, float, float, float]:
    xs = [point[0] for point in polygon]
    ys = [point[1] for point in polygon]
    return min(xs), min(ys), max(xs), max(ys)


def convex_polygons_overlap(
    first: list[tuple[float, float]],
    second: list[tuple[float, float]],
) -> bool:
    """Separating-axis overlap test; boundary contact counts as overlap."""
    for polygon in (first, second):
        for index, point in enumerate(polygon):
            next_point = polygon[(index + 1) % len(polygon)]
            edge_x = next_point[0] - point[0]
            edge_y = next_point[1] - point[1]
            axis_x, axis_y = -edge_y, edge_x
            first_projection = [x * axis_x + y * axis_y for x, y in first]
            second_projection = [x * axis_x + y * axis_y for x, y in second]
            if (max(first_projection) < min(second_projection)
                    or max(second_projection) < min(first_projection)):
                return False
    return True


def circle_overlaps_axis_aligned_box(
    centre_x: float,
    centre_y: float,
    radius: float,
    box_polygon: list[tuple[float, float]],
) -> bool:
    """Return true for physical intersection or boundary contact."""
    left, top, right, bottom = polygon_bounds(box_polygon)
    nearest_x = min(max(centre_x, left), right)
    nearest_y = min(max(centre_y, top), bottom)
    distance_squared = (
        (centre_x - nearest_x) ** 2 + (centre_y - nearest_y) ** 2
    )
    return distance_squared <= radius ** 2


def bbox_gap_mm(
    first: list[tuple[float, float]],
    second: list[tuple[float, float]],
) -> float:
    """Distance between axis-aligned bounding boxes (zero when overlapping)."""
    first_left, first_top, first_right, first_bottom = polygon_bounds(first)
    second_left, second_top, second_right, second_bottom = polygon_bounds(second)
    dx = max(second_left - first_right, first_left - second_right, 0.0)
    dy = max(second_top - first_bottom, first_top - second_bottom, 0.0)
    return math.hypot(dx, dy)


def fab_shape_bounds_mm(
    footprint: pcbnew.FOOTPRINT,
) -> tuple[float, float] | None:
    """Measure the centreline span of a mechanical envelope's Fab graphics."""
    expected_fab_layer = pcbnew.B_Fab if footprint.IsFlipped() else pcbnew.F_Fab
    points: list[tuple[float, float]] = []
    for item in footprint.GraphicalItems():
        if item.GetLayer() != expected_fab_layer or not hasattr(item, "GetShape"):
            continue
        try:
            start = item.GetStart()
            end = item.GetEnd()
        except (AttributeError, TypeError):
            continue
        points.extend(((as_mm(start.x), as_mm(start.y)),
                       (as_mm(end.x), as_mm(end.y))))
    if not points:
        return None
    left, top, right, bottom = polygon_bounds(points)
    return right - left, bottom - top


def find_all_layer_antenna_keepout(
    radio: pcbnew.FOOTPRINT,
) -> pcbnew.ZONE | None:
    """Locate the Raytac rule area that excludes copper/parts on all Cu layers."""
    candidates = [
        zone for zone in radio.Zones()
        if zone.GetIsRuleArea()
        and zone.GetDoNotAllowCopperPour()
        and zone.GetDoNotAllowFootprints()
        and zone.GetLayerSet().Contains(pcbnew.F_Cu)
        and zone.GetLayerSet().Contains(pcbnew.B_Cu)
    ]
    return candidates[0] if len(candidates) == 1 else None


def parse_drc_report(report_text: str) -> tuple[int, Counter[str], int, int]:
    violation_match = re.search(
        r"\*\* Found\s+(\d+)\s+DRC violations\s+\*\*", report_text
    )
    footprint_match = re.search(
        r"\*\* Found\s+(\d+)\s+Footprint errors\s+\*\*", report_text
    )
    if violation_match is None or footprint_match is None:
        raise ValueError("KiCad DRC report does not contain expected summary lines")
    # KiCad writes unrouted ratsnest entries as [unconnected_items] blocks after
    # the DRC violations. They are *not* included in the "DRC violations"
    # headline, so count them separately instead of inflating severity totals.
    blocks = re.split(r"(?=^\[[^\]\n]+\]:)", report_text, flags=re.MULTILINE)[1:]
    severities: Counter[str] = Counter()
    unconnected_blocks = 0
    drc_blocks = 0
    for block in blocks:
        kind_match = re.match(r"^\[([^\]]+)\]:", block)
        severity_match = re.search(
            r"Severity:\s*(error|warning|ignore)", block, flags=re.IGNORECASE
        )
        if kind_match is None or severity_match is None:
            raise ValueError("KiCad DRC report contains an unparseable violation block")
        if kind_match.group(1) == "unconnected_items":
            unconnected_blocks += 1
        else:
            drc_blocks += 1
            severities[severity_match.group(1).lower()] += 1

    headline_count = int(violation_match.group(1))
    if drc_blocks != headline_count:
        raise ValueError(
            f"KiCad DRC headline says {headline_count} violations but "
            f"{drc_blocks} non-ratsnest violation blocks were parsed"
        )
    return (
        headline_count, severities, int(footprint_match.group(1)),
        unconnected_blocks,
    )


def verify(board_path: Path, drc_report_path: Path) -> int:
    structural_errors: list[str] = []
    release_blockers: list[str] = []
    notes: list[str] = []

    spec_errors = validate_spec()
    structural_errors.extend(f"design spec: {message}" for message in spec_errors)

    if not board_path.is_file():
        print(f"FAIL: board file does not exist: {board_path}")
        return 2

    try:
        board = pcbnew.LoadBoard(str(board_path))
    except Exception as exc:
        print(f"FAIL: KiCad could not load {board_path}: {exc}")
        return 2

    # Stack-up and board envelope.
    copper_layers = int(board.GetCopperLayerCount())
    if copper_layers != 4:
        structural_errors.append(
            f"expected 4 copper layers, found {copper_layers}"
        )

    thickness_mm = as_mm(board.GetDesignSettings().GetBoardThickness())
    if abs(thickness_mm - TARGET_THICKNESS_MM) > THICKNESS_TOLERANCE_MM:
        structural_errors.append(
            f"expected {TARGET_THICKNESS_MM:.2f} mm board thickness, "
            f"found {thickness_mm:.4f} mm"
        )

    outline = pcbnew.SHAPE_POLY_SET()
    outline_valid = bool(board.GetBoardPolygonOutlines(outline))
    if not outline_valid or outline.OutlineCount() != 1:
        structural_errors.append(
            "Edge.Cuts must form exactly one closed, valid exterior outline; "
            f"KiCad reports valid={outline_valid}, outlines={outline.OutlineCount()}"
        )
        board_width_mm = float("nan")
        board_height_mm = float("nan")
    else:
        # SHAPE_POLY_SET.BBox() measures the geometric centreline outline and
        # therefore does not incorrectly add half the Edge.Cuts stroke width.
        outline_box = outline.BBox()
        board_width_mm = as_mm(outline_box.GetWidth())
        board_height_mm = as_mm(outline_box.GetHeight())
        if board_width_mm > MAX_BOARD_WIDTH_MM + DIMENSION_TOLERANCE_MM:
            structural_errors.append(
                f"board width {board_width_mm:.4f} mm exceeds "
                f"{MAX_BOARD_WIDTH_MM:.3f} mm maximum"
            )
        if board_height_mm > MAX_BOARD_HEIGHT_MM + DIMENSION_TOLERANCE_MM:
            structural_errors.append(
                f"board height {board_height_mm:.4f} mm exceeds "
                f"{MAX_BOARD_HEIGHT_MM:.3f} mm maximum"
            )

    footprints, ref_counts = get_footprints_by_reference(board)
    duplicate_refs = {ref for ref, count in ref_counts.items() if count != 1}
    if duplicate_refs:
        structural_errors.append(
            f"duplicate footprint references: {format_list(duplicate_refs)}"
        )

    expected_refs = set(PART_BY_REF)
    board_refs = set(footprints)
    missing_refs = expected_refs - board_refs
    if missing_refs:
        structural_errors.append(
            f"missing required footprints: {format_list(missing_refs)}"
        )
    if "J2" in board_refs:
        structural_errors.append("J2 is forbidden; R0B has only the J1 USB-C connector")
    unexpected_refs = board_refs - expected_refs - ALLOWED_MECHANICAL_REFS
    if unexpected_refs:
        structural_errors.append(
            f"unexpected footprints outside the frozen spec: {format_list(unexpected_refs)}"
        )

    # Every connected source-of-truth pin must exist on the footprint and carry
    # exactly the same named net. Explicit no-connect pins are intentionally
    # ignored here, as required; schematic equivalence checks own those markers.
    connected_pin_count = 0
    for part in PARTS:
        footprint = footprints.get(part.ref)
        if footprint is None:
            continue
        numbered_pads = pads_by_number(footprint)
        for pin in part.pins:
            if pin.net is None:
                continue
            connected_pin_count += 1
            matching_pads = numbered_pads.get(pin.number, [])
            if not matching_pads:
                structural_errors.append(
                    f"{part.ref} connected pin {pin.number} ({pin.name}) has no PCB pad"
                )
                continue
            actual_nets = {str(pad.GetNetname()) for pad in matching_pads}
            if actual_nets != {pin.net}:
                actual = format_list(actual_nets) if actual_nets else "<none>"
                structural_errors.append(
                    f"{part.ref} pad {pin.number}: expected net {pin.net}, "
                    f"found {actual}"
                )

    # Certified radio orientation. Rotation 0 places the Raytac all-layer
    # antenna keepout along the board's top edge in the current architecture.
    radio = footprints.get("U1")
    if radio is not None:
        radio_rotation = float(radio.GetOrientationDegrees()) % 360.0
        if min(abs(radio_rotation), abs(radio_rotation - 360.0)) > 0.01:
            structural_errors.append(
                f"U1 orientation must be 0 degrees; "
                f"found {radio.GetOrientationDegrees():.3f} degrees"
            )

    # USB-C footprint identity and plated shell stakes.
    usb = footprints.get("J1")
    if usb is not None:
        usb_pads = pads_by_number(usb)
        usb_pad_numbers = set(usb_pads)
        if usb_pad_numbers != EXPECTED_USB_PADS:
            missing = EXPECTED_USB_PADS - usb_pad_numbers
            extra = usb_pad_numbers - EXPECTED_USB_PADS
            if missing:
                structural_errors.append(
                    f"J1 missing USB pads: {format_list(missing)}"
                )
            if extra:
                structural_errors.append(
                    f"J1 has unexpected USB pads: {format_list(extra)}"
                )
        for shell_number in sorted(USB_SHELL_PADS):
            shell_pads = usb_pads.get(shell_number, [])
            if len(shell_pads) != 1:
                structural_errors.append(
                    f"J1 {shell_number} must be one plated shell pad; "
                    f"found {len(shell_pads)}"
                )
                continue
            shell_pad = shell_pads[0]
            drill = shell_pad.GetDrillSize()
            plated_through = shell_pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH
            through_copper = (
                shell_pad.GetLayerSet().Contains(pcbnew.F_Cu)
                and shell_pad.GetLayerSet().Contains(pcbnew.B_Cu)
            )
            if not plated_through or drill.x <= 0 or drill.y <= 0 or not through_copper:
                structural_errors.append(
                    f"J1 {shell_number} is not a drilled plated-through shell stake"
                )

    # Assembly side gate. Battery/motor wire pads and pogo test points are
    # intentionally rear-side post-reflow features. Every other electrical
    # footprint remains top-side for one-pass reflow assembly.
    rear_parts_on_wrong_side = [
        ref for ref in EXPECTED_REAR_ELECTRICAL_REFS
        if ref in footprints and not footprints[ref].IsFlipped()
    ]
    if rear_parts_on_wrong_side:
        structural_errors.append(
            "rear electrical footprints found on top: "
            f"{format_list(rear_parts_on_wrong_side)}"
        )
    top_parts_on_wrong_side = [
        ref for ref in expected_refs - EXPECTED_REAR_ELECTRICAL_REFS
        if ref in footprints and footprints[ref].IsFlipped()
    ]
    if top_parts_on_wrong_side:
        structural_errors.append(
            "top/reflow footprints found on rear: "
            f"{format_list(top_parts_on_wrong_side)}"
        )
    battery_envelope = footprints.get("MH_BAT")
    if battery_envelope is not None and not battery_envelope.IsFlipped():
        structural_errors.append("MH_BAT mechanical envelope must remain on the rear side")
    motor_envelope = footprints.get("MH_MOTOR")
    if motor_envelope is not None and not motor_envelope.IsFlipped():
        structural_errors.append("MH_MOTOR mechanical envelope must remain on the rear side")

    # Rear physical volumes must retain their frozen body sizes and must not
    # intrude into the Raytac footprint's exact all-layer antenna rule area.
    antenna_keepout = find_all_layer_antenna_keepout(radio) if radio else None
    if radio is not None and antenna_keepout is None:
        structural_errors.append(
            "U1 must contain exactly one all-layer copper/footprint antenna keepout"
        )

    antenna_polygon = (
        rectangle_from_box(antenna_keepout.GetBoundingBox())
        if antenna_keepout is not None else None
    )

    if battery_envelope is not None:
        expected_battery_value = (
            f"BATTERY_ENVELOPE_{BATTERY_LENGTH_MM:.1f}x{BATTERY_WIDTH_MM:.1f}"
        )
        if battery_envelope.GetValue() != expected_battery_value:
            structural_errors.append(
                "MH_BAT value must identify the frozen 26.0 x 15.5 mm body; "
                f"found {battery_envelope.GetValue()}"
            )
        battery_x, battery_y = footprint_position_mm(battery_envelope)
        battery_polygon = oriented_rectangle(
            battery_x, battery_y, BATTERY_LENGTH_MM, BATTERY_WIDTH_MM,
            float(battery_envelope.GetOrientationDegrees()),
        )
        expected_bounds = polygon_bounds(battery_polygon)
        expected_span = (
            expected_bounds[2] - expected_bounds[0],
            expected_bounds[3] - expected_bounds[1],
        )
        measured_span = fab_shape_bounds_mm(battery_envelope)
        if measured_span is None:
            structural_errors.append("MH_BAT has no measurable rear Fab body outline")
        elif any(abs(measured - expected) > PHYSICAL_TOLERANCE_MM
                 for measured, expected in zip(measured_span, expected_span)):
            structural_errors.append(
                "MH_BAT rear Fab outline is not the frozen physical envelope: "
                f"measured {measured_span[0]:.3f} x {measured_span[1]:.3f} mm"
            )
        if antenna_polygon is not None:
            if convex_polygons_overlap(battery_polygon, antenna_polygon):
                structural_errors.append(
                    "26.0 x 15.5 mm battery body overlaps/touches U1 antenna keepout"
                )
            else:
                notes.append(
                    "Battery-to-antenna keepout: PASS "
                    f"({bbox_gap_mm(battery_polygon, antenna_polygon):.3f} mm "
                    "axis-aligned gap)"
                )

    if motor_envelope is not None:
        expected_motor_value = f"MOTOR_ENVELOPE_D{MOTOR_DIAMETER_MM:.1f}"
        if motor_envelope.GetValue() != expected_motor_value:
            structural_errors.append(
                "MH_MOTOR value must identify the frozen 10.0 mm body; "
                f"found {motor_envelope.GetValue()}"
            )
        motor_x, motor_y = footprint_position_mm(motor_envelope)
        measured_span = fab_shape_bounds_mm(motor_envelope)
        if measured_span is None:
            structural_errors.append("MH_MOTOR has no measurable rear Fab body outline")
        elif any(abs(measured - MOTOR_DIAMETER_MM) > PHYSICAL_TOLERANCE_MM
                 for measured in measured_span):
            structural_errors.append(
                "MH_MOTOR rear Fab outline is not the frozen 10.0 mm circle: "
                f"measured {measured_span[0]:.3f} x {measured_span[1]:.3f} mm"
            )
        if antenna_polygon is not None:
            if circle_overlaps_axis_aligned_box(
                motor_x, motor_y, MOTOR_DIAMETER_MM / 2.0, antenna_polygon
            ):
                structural_errors.append(
                    "10.0 mm motor body overlaps/touches U1 antenna keepout"
                )
            else:
                motor_polygon = oriented_rectangle(
                    motor_x, motor_y, MOTOR_DIAMETER_MM, MOTOR_DIAMETER_MM, 0.0
                )
                notes.append(
                    "Motor-to-antenna keepout: PASS "
                    f"({bbox_gap_mm(motor_polygon, antenna_polygon):.3f} mm "
                    "conservative body-box gap)"
                )

    # The two buck ground returns must remain distinct until their explicit net
    # ties. Merely naming the footprints NT1/NT2 is not sufficient.
    for ref, expected_mapping in (
        ("NT1", {"1": "PVSS1", "2": "GND"}),
        ("NT2", {"1": "PVSS2", "2": "GND"}),
    ):
        footprint = footprints.get(ref)
        if footprint is None:
            continue
        mapping = {
            number: {str(pad.GetNetname()) for pad in pads}
            for number, pads in pads_by_number(footprint).items()
        }
        for number, expected_net in expected_mapping.items():
            if mapping.get(number) != {expected_net}:
                structural_errors.append(
                    f"{ref} pad {number} must be {expected_net}, found "
                    f"{format_list(mapping.get(number, {'<missing>'}))}"
                )
        if not footprint.IsNetTie():
            structural_errors.append(f"{ref} footprint is not marked as a KiCad net tie")

    # Check net names plus the identity fields most likely to preserve an old
    # removable-SD/user-button design by accident.
    named_items = set(board_net_names(board))
    for fp in footprints.values():
        named_items.update((
            fp.GetReference(), fp.GetValue(), fp.GetFPIDAsString(),
        ))
    banned_names = {name for name in named_items if is_banned_legacy_name(name)}
    if banned_names:
        structural_errors.append(
            f"forbidden legacy names present: {format_list(banned_names)}"
        )

    # Connectivity is computed from copper, pads, vias, and zones—not inferred
    # from the schematic. This number must reach zero before fabrication export.
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    unconnected_count = int(connectivity.GetUnconnectedCount(False))
    if unconnected_count:
        release_blockers.append(
            f"{unconnected_count} unrouted PCB connections remain"
        )

    drc_report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        drc_written = bool(pcbnew.WriteDRCReport(
            board, str(drc_report_path), pcbnew.EDA_UNITS_MILLIMETRES, True
        ))
    except Exception as exc:
        drc_written = False
        structural_errors.append(f"KiCad DRC execution failed: {exc}")

    drc_violations = -1
    drc_severities: Counter[str] = Counter()
    footprint_errors = -1
    report_unconnected_count = -1
    if not drc_written or not drc_report_path.is_file():
        structural_errors.append(
            f"KiCad did not write the DRC report: {drc_report_path}"
        )
    else:
        try:
            (
                drc_violations, drc_severities, footprint_errors,
                report_unconnected_count,
            ) = parse_drc_report(
                drc_report_path.read_text(encoding="utf-8", errors="replace")
            )
        except (OSError, ValueError) as exc:
            structural_errors.append(f"could not parse KiCad DRC report: {exc}")

    if (report_unconnected_count >= 0
            and report_unconnected_count != unconnected_count):
        structural_errors.append(
            "connectivity APIs disagree: ratsnest reports "
            f"{unconnected_count}, DRC report contains {report_unconnected_count} "
            "unconnected-item blocks"
        )

    if drc_violations > 0:
        release_blockers.append(
            f"KiCad DRC reports {drc_violations} violations "
            f"({drc_severities.get('error', 0)} errors, "
            f"{drc_severities.get('warning', 0)} warnings)"
        )
    if footprint_errors > 0:
        release_blockers.append(
            f"KiCad DRC reports {footprint_errors} footprint errors"
        )
    if drc_violations == 0 and footprint_errors == 0:
        notes.append("KiCad DRC report is clean")

    print("ANT-PROD-R0B PCB RELEASE VERIFICATION")
    print(f"Board: {board_path}")
    print(f"Stack-up: {copper_layers} copper layers, {thickness_mm:.3f} mm")
    print(f"Geometric outline: {board_width_mm:.3f} x {board_height_mm:.3f} mm")
    print(f"Frozen electrical references: {len(expected_refs)}")
    print(f"Connected source-of-truth pins checked: {connected_pin_count}")
    print(f"Unconnected PCB items: {unconnected_count}")
    if drc_violations >= 0 and footprint_errors >= 0:
        print(
            "DRC: "
            f"{drc_violations} violations / {footprint_errors} footprint errors; "
            f"severity errors={drc_severities.get('error', 0)}, "
            f"warnings={drc_severities.get('warning', 0)}"
        )
    print(f"DRC report: {drc_report_path}")

    if structural_errors:
        print("\nSTRUCTURAL CHECKS: FAIL")
        for message in structural_errors:
            print(f"  - {message}")
    else:
        print("\nSTRUCTURAL CHECKS: PASS")

    if release_blockers:
        print("\nFABRICATION RELEASE: BLOCKED")
        for message in release_blockers:
            print(f"  - {message}")
    elif structural_errors:
        print("\nFABRICATION RELEASE: BLOCKED by structural verification failures")
    else:
        print("\nFABRICATION RELEASE: PASS (machine-checkable PCB gates only)")

    if notes:
        print("\nADDITIONAL PHYSICAL CHECKS")
        for note in notes:
            print(f"  - {note}")

    if structural_errors:
        return 2
    if release_blockers:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--board", type=Path, default=DEFAULT_BOARD,
        help=f"KiCad board to verify (default: {DEFAULT_BOARD.name})",
    )
    parser.add_argument(
        "--drc-report", type=Path, default=DEFAULT_DRC_REPORT,
        help="path for the generated KiCad DRC text report",
    )
    args = parser.parse_args()
    return verify(args.board.resolve(), args.drc_report.resolve())


if __name__ == "__main__":
    sys.exit(main())
