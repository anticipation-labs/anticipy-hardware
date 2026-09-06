#!/usr/bin/env python3
"""Route a DRC-clean miscellaneous-signal subset for Anticipy R0B.

This candidate stage is deliberately narrow.  It touches only the explicitly
listed low-speed miscellaneous nets and can be composed after the frozen,
rotated-U4 placement baseline.  Power rails, GND, USB, QSPI, PDM, RF and PMIC
switch nodes are outside its authority.

Each proposed connection is committed provisionally, the GND zones are
refilled, and KiCad DRC plus the live ratsnest are re-evaluated.  A route is
rolled back unless DRC remains at zero and the unconnected count falls.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import shutil

import pcbnew

from route_remaining_r0b import (
    POLICY,
    Connection,
    PadRef,
    count_unconnected,
    fill_ground_zones,
    footprints,
    plan_connection,
    remove_items,
    resolve_pad,
    write_drc,
)
from routing_primitives_r0b import (
    PlannedSegment,
    PlannedVia,
    RoutePlan,
    RouteSafetyError,
    commit_route_plan,
    ensure_in1_ground_plane,
    point,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
DEFAULT_OUTPUT = (
    ROOT / "route_temp" / "Anticipy_PROD_R0B_EVT_misc_clean.kicad_pcb"
)
DEFAULT_REPORT = ROOT / "reports" / "misc_clean_r0b_drc.txt"
DEFAULT_BASELINE_REPORT = ROOT / "reports" / "misc_clean_r0b_baseline_drc.txt"
DEFAULT_MANIFEST = ROOT / "route_temp" / "misc_clean_routes.csv"


# These are ordered from local/least constrained to long or cross-board.
# RESET/NTC are intentionally attempted last because the rear test/battery
# pads can require a layer transition.  Failed attempts are rolled back.
CONNECTIONS: tuple[Connection, ...] = (
    Connection("I2C_SDA_U2_U3", PadRef("U2", "13"), PadRef("U3", "4")),
    Connection("LED_RED_K", PadRef("U2", "26"), PadRef("LED1", "3")),
    Connection("LED_BLUE_K", PadRef("U2", "25"), PadRef("LED1", "1")),
    Connection("ACC_INT2", PadRef("U3", "11"), PadRef("U1", "49")),
    Connection("RESET_TEST", PadRef("U1", "40"), PadRef("TP3", "1")),
    Connection("NTC_BATTERY", PadRef("U2", "18"), PadRef("BT1", "2")),
)

FORBIDDEN_NAMES = {
    "GND",
    "VBUS",
    "VBUSOUT",
    "VBAT",
    "VSYS",
    "3V3",
    "3V3_PERIPH",
    "SW1",
    "SW2",
    "PVSS",
    "HAPTIC_NEG",
}
FORBIDDEN_PREFIXES = ("USB_", "FLASH_", "PDM_", "RF_", "XTAL")


def build_reviewed_manual_plan(
    connection: Connection, start: pcbnew.PAD, goal: pcbnew.PAD
) -> RoutePlan | None:
    """Return the two reviewed multi-layer escape plans, if requested.

    The coordinates are coupled to the frozen R0B placement and are still
    fully preflighted by ``commit_route_plan`` before mutation.  Hard-coded
    endpoints make any placement drift fail visibly rather than silently
    producing disconnected copper.
    """

    expected_endpoints = {
        "LED_RED_K": ((33.9500, 31.0375), (34.6000, 37.0500)),
        "NTC_BATTERY": ((32.7625, 27.3500), (54.4000, 28.8000)),
    }
    expected = expected_endpoints.get(connection.label)
    if expected is None:
        return None

    def pad_xy(pad: pcbnew.PAD) -> tuple[float, float]:
        position = pad.GetPosition()
        return pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)

    actual = (pad_xy(start), pad_xy(goal))
    for actual_point, expected_point in zip(actual, expected):
        if any(abs(a - e) > 0.0005 for a, e in zip(actual_point, expected_point)):
            raise RuntimeError(
                f"{connection.label}: frozen endpoint moved: {actual}, "
                f"expected {expected}"
            )

    if connection.label == "LED_RED_K":
        # Escape above the PMIC on F.Cu, cross the congested LED corridor on
        # In2.Cu, and return beside LED1.  No via-in-pad is used.
        segments = (
            ((33.9500, 31.0375), (33.9500, 31.7875), pcbnew.F_Cu),
            ((33.9500, 31.7875), (33.7000, 31.7875), pcbnew.F_Cu),
            ((33.7000, 31.7875), (34.1000, 32.1875), pcbnew.In2_Cu),
            ((34.1000, 32.1875), (34.1000, 37.5500), pcbnew.In2_Cu),
            ((34.1000, 37.5500), (34.6000, 37.0500), pcbnew.F_Cu),
        )
        vias = ((33.7000, 31.7875), (34.1000, 37.5500))
    else:
        # Leave the PMIC to the upper-left on F.Cu, change layers in open
        # copper, then run on B.Cu directly to the rear battery thermistor pad.
        segments = (
            ((32.7625, 27.3500), (31.7625, 27.3500), pcbnew.F_Cu),
            ((31.7625, 27.3500), (30.7625, 26.3500), pcbnew.F_Cu),
            # Stay in the open upper B.Cu corridor until clear of the USB and
            # PMIC ground-via field, then approach BT1.2 horizontally.
            ((30.7625, 26.3500), (49.0000, 26.3500), pcbnew.B_Cu),
            ((49.0000, 26.3500), (49.0000, 28.8000), pcbnew.B_Cu),
            ((49.0000, 28.8000), (54.4000, 28.8000), pcbnew.B_Cu),
        )
        vias = ((30.7625, 26.3500),)

    return RoutePlan(
        net_name=str(start.GetNetname()),
        segments=[
            PlannedSegment(point(a), point(b), layer, POLICY.default_width_mm)
            for a, b, layer in segments
        ],
        vias=[
            PlannedVia(
                point(location),
                POLICY.via_diameter_mm,
                POLICY.via_drill_mm,
            )
            for location in vias
        ],
        endpoint_pads=(start, goal),
        note=f"reviewed frozen-placement route for {connection.label}",
    )


def copy_project_companions(input_path: Path, output_path: Path) -> None:
    """Make the temporary board independently verifiable by KiCad."""
    source_stem = input_path.with_suffix("")
    output_stem = output_path.with_suffix("")
    for suffix in (".kicad_dru", ".kicad_pro"):
        source = source_stem.with_suffix(suffix)
        if source.is_file():
            shutil.copyfile(source, output_stem.with_suffix(suffix))

    source_table = input_path.parent / "fp-lib-table"
    if source_table.is_file():
        shutil.copyfile(source_table, output_path.parent / "fp-lib-table")
    source_pretty = input_path.parent / "Anticipy_R0B.pretty"
    output_pretty = output_path.parent / "Anticipy_R0B.pretty"
    if source_pretty.is_dir():
        shutil.copytree(source_pretty, output_pretty, dirs_exist_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("--output must differ from --input")

    requested_nets = {connection.label for connection in CONNECTIONS}
    if len(requested_nets) != len(CONNECTIONS):
        raise RuntimeError("Duplicate miscellaneous route labels")

    board = pcbnew.LoadBoard(str(args.input))
    if board is None:
        raise RuntimeError(f"Could not load {args.input}")
    if board.GetCopperLayerCount() != 4:
        raise RuntimeError("R0B miscellaneous stage requires four copper layers")

    raw_unconnected = count_unconnected(board)
    fill_ground_zones(board)
    baseline_unconnected = count_unconnected(board)
    baseline_drc, baseline_report_unconnected = write_drc(
        board, args.baseline_report
    )
    if baseline_drc != 0:
        raise RuntimeError(
            f"Refilled baseline has {baseline_drc} DRC violations; refusing routing"
        )
    if baseline_report_unconnected != baseline_unconnected:
        raise RuntimeError("Connectivity API and baseline DRC report disagree")

    mapping = footprints(board)
    accepted: list[dict[str, object]] = []
    rejected: list[dict[str, str]] = []
    current_unconnected = baseline_unconnected

    for index, connection in enumerate(CONNECTIONS, start=1):
        start = resolve_pad(mapping, connection.start)
        goal = resolve_pad(mapping, connection.goal)
        start_net = str(start.GetNetname())
        if (
            int(start.GetNetCode()) <= 0
            or int(start.GetNetCode()) != int(goal.GetNetCode())
        ):
            raise RuntimeError(
                f"{connection.label}: endpoints no longer share a real net"
            )
        if start_net in FORBIDDEN_NAMES or start_net.startswith(FORBIDDEN_PREFIXES):
            raise RuntimeError(
                f"{connection.label}: forbidden net entered miscellaneous stage: "
                f"{start_net}"
            )

        try:
            plan = build_reviewed_manual_plan(connection, start, goal)
            if plan is None:
                method, plan = plan_connection(board, start, goal)
            else:
                method = "reviewed-multilayer"
        except RouteSafetyError as exc:
            reason = str(exc).splitlines()[0]
            rejected.append({"label": connection.label, "reason": reason})
            print(f"reject {connection.label}: {reason}", flush=True)
            continue

        before_items = set(item.m_Uuid.AsString() for item in board.GetTracks())
        try:
            items = commit_route_plan(board, plan, policy=POLICY)
        except RouteSafetyError as exc:
            reason = str(exc).splitlines()[0]
            rejected.append({"label": connection.label, "reason": reason})
            print(f"reject {connection.label}: {reason}", flush=True)
            continue
        fill_ground_zones(board)
        proposed_unconnected = count_unconnected(board)
        step_report = args.report.with_name(
            f"{args.report.stem}_step_{index:02d}{args.report.suffix}"
        )
        proposed_drc, report_unconnected = write_drc(board, step_report)
        if proposed_drc != 0 or proposed_unconnected >= current_unconnected:
            remove_items(board, items)
            reason = (
                f"rollback: DRC 0->{proposed_drc}, ratsnest "
                f"{current_unconnected}->{proposed_unconnected}, report "
                f"ratsnest {report_unconnected}"
            )
            rejected.append({"label": connection.label, "reason": reason})
            print(f"reject {connection.label}: {reason}", flush=True)
            continue
        if report_unconnected != proposed_unconnected:
            remove_items(board, items)
            raise RuntimeError(
                f"{connection.label}: connectivity API and DRC report disagree"
            )

        after_items = set(item.m_Uuid.AsString() for item in board.GetTracks())
        new_item_count = len(after_items - before_items)
        if new_item_count != len(items):
            raise RuntimeError(
                f"{connection.label}: committed item accounting mismatch"
            )
        accepted.append(
            {
                "label": connection.label,
                "net": start_net,
                "from": connection.start.label,
                "to": connection.goal.label,
                "method": method,
                "segments": len(plan.segments),
                "vias": len(plan.vias),
                "length_mm": f"{plan.track_length_mm:.4f}",
                "unconnected_before": current_unconnected,
                "unconnected_after": proposed_unconnected,
            }
        )
        current_unconnected = proposed_unconnected
        print(
            f"accept {connection.label}: {method}, {len(plan.segments)} segments, "
            f"{len(plan.vias)} vias, ratsnest={current_unconnected}, DRC=0",
            flush=True,
        )

    fill_ground_zones(board)
    ensure_in1_ground_plane(board, POLICY)
    final_unconnected = count_unconnected(board)
    final_drc, final_report_unconnected = write_drc(board, args.report)
    if final_drc != 0 or final_report_unconnected != final_unconnected:
        raise RuntimeError(
            "Final miscellaneous candidate failed closed: "
            f"DRC={final_drc}, API ratsnest={final_unconnected}, "
            f"report ratsnest={final_report_unconnected}"
        )

    # The stage may not contain any newly routed forbidden net or In1 track.
    source = pcbnew.LoadBoard(str(args.input))
    source_ids = {item.m_Uuid.AsString() for item in source.GetTracks()}
    for item in board.GetTracks():
        if item.m_Uuid.AsString() in source_ids:
            continue
        name = str(item.GetNetname())
        if name == "GND":
            continue
        if name in FORBIDDEN_NAMES or name.startswith(FORBIDDEN_PREFIXES):
            raise RuntimeError(f"Stage created forbidden copper on {name}")
        if not isinstance(item, pcbnew.PCB_VIA) and item.GetLayer() == pcbnew.In1_Cu:
            raise RuntimeError("Stage created a signal track on In1.Cu")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    copy_project_companions(args.input, args.output)

    fieldnames = (
        "label",
        "net",
        "from",
        "to",
        "method",
        "segments",
        "vias",
        "length_mm",
        "unconnected_before",
        "unconnected_after",
    )
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(accepted)

    print(f"input={args.input}")
    print(f"output={args.output}")
    print(f"report={args.report}")
    print(f"manifest={args.manifest}")
    print(f"unconnected_before_raw={raw_unconnected}")
    print(f"unconnected_before_refilled={baseline_unconnected}")
    print(f"unconnected_after={final_unconnected}")
    print(f"accepted_connections={len(accepted)}")
    print(f"rejected_connections={len(rejected)}")
    print(f"drc_violations={final_drc}")
    for row in rejected:
        print(f"rejected={row['label']}: {row['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
