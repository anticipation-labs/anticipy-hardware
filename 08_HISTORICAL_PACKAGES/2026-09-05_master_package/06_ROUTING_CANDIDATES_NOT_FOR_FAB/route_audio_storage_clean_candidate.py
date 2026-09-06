#!/usr/bin/env /usr/bin/python3
"""Build a fail-closed QSPI/PDM routing candidate for Anticipy R0B.

This is an independently composable routing *stage*, not a fabrication
release.  It routes only the serial-NAND QSPI bus, the two-microphone PDM bus,
and a small reviewed set of local 3V_FLASH/3V_MIC branches.  The USB neck, PMIC
switch cells, RF keepout, and every other net are outside this script's
authority.

Short microphone branches remain on F.Cu.  Longer module-facing QSPI/PDM
trunks may change to In2.Cu through ordinary production vias.  B.Cu and In1.Cu
are both forbidden for signal tracks; In1.Cu remains a solid GND reference
plane.  Every accepted connection must reduce KiCad's live ratsnest by exactly
one while preserving a zero-violation DRC report.  The script writes only to
caller-selected candidate/report/manifest paths and never modifies its input
board.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
from dataclasses import dataclass
import math
from pathlib import Path
import re
import shutil
from typing import Iterator, Sequence

import pcbnew

from route_signal_stage_r0b import endpoint, find_pad
from routing_primitives_r0b import (
    PlannedSegment,
    PlannedVia,
    RoutePlan,
    RouteSafetyError,
    RoutingPolicy,
    commit_route_plan,
    connect_pad_centers,
    ensure_in1_ground_plane,
    make_polyline_plan,
    route_astar_low_speed,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
DEFAULT_OUTPUT = ROOT / "reports" / "AUDIO_STORAGE_ROUTED_CANDIDATE.kicad_pcb"
DEFAULT_REPORT = ROOT / "reports" / "audio_storage_routed_candidate_drc.txt"
DEFAULT_BASELINE_REPORT = ROOT / "reports" / "audio_storage_routed_baseline_drc.txt"
DEFAULT_MANIFEST = ROOT / "reports" / "audio_storage_routes.csv"

DRC_RE = re.compile(r"\*\* Found (\d+) DRC violations \*\*")
UNCONNECTED_RE = re.compile(r"\*\* Found (\d+) unconnected pads \*\*")

SIGNAL_WIDTH_MM = 0.127

# Explicit pad chains are frozen to the source-of-truth schematic.  A changed
# pin/net mapping fails loudly in endpoint().
SIGNAL_CHAINS: dict[str, list[tuple[str, str]]] = {
    "PDM_DATA_MIC1": [("MIC1", "4"), ("R8", "1")],
    "PDM_DATA_MIC2": [("MIC2", "4"), ("R9", "1")],
    "PDM_CLK": [("MIC1", "3"), ("MIC2", "3"), ("U1", "38")],
    "PDM_DATA": [("R8", "2"), ("R9", "2"), ("U1", "39")],
    "FLASH_SCK": [("U5", "6"), ("U1", "42")],
    "FLASH_IO0": [("U5", "5"), ("U1", "43")],
    "FLASH_IO1": [("U5", "2"), ("U1", "46")],
    "FLASH_IO2": [("U5", "3"), ("U1", "45")],
    "FLASH_IO3": [("U5", "7"), ("U1", "47")],
    "FLASH_CS": [("U5", "1"), ("R7", "2"), ("U1", "44")],
}

# Constrained microphone endpoints are closed first.  The QSPI order then
# works from the outer Raytac castellations inward.
SIGNAL_ORDER = (
    "PDM_DATA_MIC1",
    "PDM_DATA_MIC2",
    "PDM_CLK",
    "PDM_DATA",
    "FLASH_IO1",
    "FLASH_IO3",
    "FLASH_IO2",
    "FLASH_IO0",
    "FLASH_CS",
    "FLASH_SCK",
)

# Route these local pairs first on F.Cu.  All remaining signal-chain links use
# reviewed multi-layer A* proposals with critical-net routing explicitly
# enabled; each proposal is still preflighted and then independently DRC gated.
TOP_ONLY_LINKS = {
    ("PDM_DATA_MIC1", "MIC1", "4", "R8", "1"),
    ("PDM_DATA_MIC2", "MIC2", "4", "R9", "1"),
    ("PDM_CLK", "MIC1", "3", "MIC2", "3"),
    ("PDM_DATA", "R8", "2", "R9", "2"),
}

# Frozen, DRC-reviewed F.Cu polylines for the four microphone-local links.
# They are kept explicit so this stage can compose after GND/USB routing
# without relying on GridRouter's intentionally ground-only input contract.
TOP_POLYLINES: dict[
    tuple[str, str, str, str, str], tuple[tuple[float, float], ...]
] = {
    ("PDM_DATA_MIC1", "MIC1", "4", "R8", "1"): (
        (45.875, 24.575), (45.750, 24.700), (45.750, 25.000),
        (45.250, 25.500), (45.250, 25.750), (45.750, 26.250),
        (46.250, 26.250), (46.250, 26.260), (46.790, 26.800),
    ),
    ("PDM_DATA_MIC2", "MIC2", "4", "R9", "1"): (
        (50.775, 24.575), (50.750, 24.600), (50.750, 25.000),
        (50.500, 25.250), (50.250, 25.250), (50.250, 26.000),
        (50.750, 26.000), (51.000, 26.250), (51.040, 26.250),
        (51.590, 26.800),
    ),
    ("PDM_CLK", "MIC1", "3", "MIC2", "3"): (
        (45.875, 23.225), (46.050, 23.050), (46.050, 22.800),
        (46.300, 22.550), (50.350, 22.550), (50.600, 22.800),
        (50.600, 23.050), (50.775, 23.225),
    ),
    ("PDM_DATA", "R8", "2", "R9", "2"): (
        (47.810, 26.800), (48.360, 27.350), (52.060, 27.350),
        (52.610, 26.800),
    ),
}


@dataclass(frozen=True)
class LocalPowerConnection:
    label: str
    start_ref: str
    start_pad: str
    goal_ref: str
    goal_pad: str
    width_mm: float
    rationale: str


@dataclass(frozen=True)
class GroundEscape:
    label: str
    reference: str
    pad_number: str
    dx_mm: float
    dy_mm: float
    rationale: str


@dataclass(frozen=True)
class GroundLink:
    label: str
    reference: str
    start_pad: str
    goal_pad: str
    rationale: str


# These are branch connections inside the flash/microphone load cells.  The
# long PMIC-to-load rail trunks are intentionally deferred to the power stage.
LOCAL_POWER_CONNECTIONS: tuple[LocalPowerConnection, ...] = (
    LocalPowerConnection(
        "FLASH_LOCAL_BULK",
        "U5", "8", "C18", "1", 0.127,
        "Flash VCC to its adjacent 1 uF local bulk capacitor",
    ),
    LocalPowerConnection(
        "FLASH_LOCAL_HF_BYPASS",
        "U5", "8", "C17", "1", 0.127,
        "Flash VCC branch to its adjacent 100 nF bypass capacitor",
    ),
    LocalPowerConnection(
        "FLASH_CS_PULLUP_FEED",
        "C17", "1", "R7", "1", 0.127,
        "Local flash rail to the chip-select pull-up",
    ),
    LocalPowerConnection(
        "MIC1_LOCAL_BYPASS",
        "C19", "1", "MIC1", "1", 0.127,
        "MIC1 supply pad to its adjacent 100 nF bypass capacitor",
    ),
    LocalPowerConnection(
        "MIC2_LOCAL_BYPASS",
        "C20", "1", "MIC2", "1", 0.127,
        "MIC2 supply pad to its adjacent 100 nF bypass capacitor",
    ),
    LocalPowerConnection(
        "MIC2_SELECT_HIGH",
        "MIC2", "1", "MIC2", "2", 0.15,
        "Short local tie setting MIC2 channel SELECT high",
    ),
)


# Each escape was preflighted against the frozen R0B placement and the routed
# QSPI/PDM geometry.  Offsets are relative to the exact pad centre, avoiding
# float-rounding changes in generated KiCad coordinates.  The U5 exposed-pad
# via is the one intentional via-in-pad and must be epoxy filled/capped (VIPPO)
# by the prototype fabricator; no microphone land uses via-in-pad.
GROUND_ESCAPES: tuple[GroundEscape, ...] = (
    GroundEscape("MIC1_GND_RIGHT", "MIC1", "6", +0.625, 0.0,
                 "Right perimeter ground pad to solid In1 ground"),
    GroundEscape("MIC1_GND_LEFT", "MIC1", "8", -0.550, 0.0,
                 "Left perimeter ground pad to solid In1 ground"),
    GroundEscape("MIC2_GND_RIGHT", "MIC2", "6", +0.575, 0.0,
                 "Right perimeter ground pad to solid In1 ground"),
    GroundEscape("MIC2_GND_LEFT", "MIC2", "8", -0.550, 0.0,
                 "Left perimeter ground pad to solid In1 ground"),
    GroundEscape("C19_GND", "C19", "2", 0.0, +0.700,
                 "MIC1 bypass return to solid In1 ground"),
    GroundEscape("C20_GND", "C20", "2", -0.750, -0.750,
                 "MIC2 bypass return to solid In1 ground"),
    GroundEscape("U5_PIN4_GND", "U5", "4", -0.700, 0.0,
                 "Serial-NAND ground pin to solid In1 ground"),
    GroundEscape("U5_EP_GND_VIPPO", "U5", "9", 0.0, -0.400,
                 "Filled/capped exposed-pad via to solid In1 ground"),
    GroundEscape("C17_GND", "C17", "2", +0.650, +0.650,
                 "Flash high-frequency bypass return to solid In1 ground"),
    GroundEscape("C18_GND", "C18", "2", -0.850, 0.0,
                 "Flash local bulk return to solid In1 ground"),
)

GROUND_LINKS: tuple[GroundLink, ...] = (
    GroundLink("MIC1_INNER_GND", "MIC1", "2", "6",
               "Inner ground pad joined to right perimeter ground"),
    GroundLink("MIC1_TOP_GND", "MIC1", "7", "8",
               "Top perimeter ground joined around acoustic keepout"),
    GroundLink("MIC1_BOTTOM_GND", "MIC1", "5", "6",
               "Bottom perimeter ground joined around acoustic keepout"),
    GroundLink("MIC2_TOP_GND", "MIC2", "7", "6",
               "Top perimeter ground joined around acoustic keepout"),
    GroundLink("MIC2_BOTTOM_GND", "MIC2", "5", "6",
               "Bottom perimeter ground joined around acoustic keepout"),
)


def power_policy(width_mm: float) -> RoutingPolicy:
    return RoutingPolicy(
        default_width_mm=width_mm,
        clearance_mm=0.127,
        edge_clearance_mm=0.50,
        via_diameter_mm=0.45,
        via_drill_mm=0.20,
        astar_grid_mm=0.25,
        astar_via_cost_mm=3.0,
        astar_max_nodes=60_000,
        allowed_track_layers=(pcbnew.F_Cu, pcbnew.In2_Cu),
        forbidden_track_layers=(pcbnew.In1_Cu, pcbnew.B_Cu),
    )


def critical_signal_policy(grid_mm: float = 0.25) -> RoutingPolicy:
    return RoutingPolicy(
        default_width_mm=SIGNAL_WIDTH_MM,
        clearance_mm=0.127,
        edge_clearance_mm=0.50,
        via_diameter_mm=0.45,
        via_drill_mm=0.20,
        astar_grid_mm=grid_mm,
        astar_via_cost_mm=1.50,
        astar_max_nodes=150_000,
        allowed_track_layers=(pcbnew.F_Cu, pcbnew.In2_Cu),
        forbidden_track_layers=(pcbnew.In1_Cu, pcbnew.B_Cu),
    )


def count_unconnected(board: pcbnew.BOARD) -> int:
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    return int(connectivity.GetUnconnectedCount(False))


def fill_ground_zones(board: pcbnew.BOARD) -> None:
    found: set[int] = set()
    for zone in board.Zones():
        if zone.GetIsRuleArea() or str(zone.GetNetname()) != "GND":
            continue
        layer = int(zone.GetLayer())
        if layer in (pcbnew.In1_Cu, pcbnew.B_Cu):
            zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            found.add(layer)
    if found != {pcbnew.In1_Cu, pcbnew.B_Cu}:
        raise RuntimeError("expected GND zones on In1.Cu and B.Cu")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    count_unconnected(board)
    ensure_in1_ground_plane(board, power_policy(0.15))


def write_drc(board: pcbnew.BOARD, report: Path) -> tuple[int, int]:
    report.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.WriteDRCReport(
        board, str(report), pcbnew.EDA_UNITS_MILLIMETRES, False
    ):
        raise RuntimeError(f"KiCad did not write DRC report {report}")
    text = report.read_text(encoding="utf-8", errors="replace")
    drc_match = DRC_RE.search(text)
    unconnected_match = UNCONNECTED_RE.search(text)
    if drc_match is None or unconnected_match is None:
        raise RuntimeError(f"could not parse KiCad DRC report {report}")
    return int(drc_match.group(1)), int(unconnected_match.group(1))


def iter_pairs(items: Sequence[object]) -> Iterator[tuple[object, object]]:
    yield from zip(items, items[1:])


def copy_project_companions(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    input_stem = input_path.with_suffix("")
    output_stem = output_path.with_suffix("")
    for suffix in (".kicad_dru", ".kicad_pro"):
        source = input_stem.with_suffix(suffix)
        if not source.is_file():
            raise RuntimeError(f"missing project companion {source}")
        shutil.copyfile(source, output_stem.with_suffix(suffix))
    source_table = input_path.parent / "fp-lib-table"
    if source_table.is_file():
        shutil.copyfile(source_table, output_path.parent / "fp-lib-table")
    source_pretty = input_path.parent / "Anticipy_R0B.pretty"
    output_pretty = output_path.parent / "Anticipy_R0B.pretty"
    if source_pretty.is_dir():
        shutil.copytree(source_pretty, output_pretty, dirs_exist_ok=True)


def remove_items(
    board: pcbnew.BOARD,
    items: Sequence[pcbnew.BOARD_CONNECTED_ITEM],
) -> None:
    for item in reversed(items):
        board.Remove(item)
    fill_ground_zones(board)


def add_reviewed_top_polyline(
    board: pcbnew.BOARD,
    net_name: str,
    start_ref: str,
    start_pad: str,
    goal_ref: str,
    goal_pad: str,
) -> tuple[list[pcbnew.BOARD_CONNECTED_ITEM], float]:
    key = (net_name, start_ref, start_pad, goal_ref, goal_pad)
    points = TOP_POLYLINES.get(key)
    if points is None:
        raise RuntimeError(f"missing reviewed top polyline for {key}")
    start = find_pad(board, start_ref, start_pad)
    goal = find_pad(board, goal_ref, goal_pad)
    if str(start.GetNetname()) != net_name or str(goal.GetNetname()) != net_name:
        raise RuntimeError(f"reviewed polyline endpoint net changed for {key}")
    start_xy = (
        pcbnew.ToMM(start.GetPosition().x), pcbnew.ToMM(start.GetPosition().y)
    )
    goal_xy = (
        pcbnew.ToMM(goal.GetPosition().x), pcbnew.ToMM(goal.GetPosition().y)
    )
    if math.dist(start_xy, points[0]) > 0.001 or math.dist(goal_xy, points[-1]) > 0.001:
        raise RuntimeError(f"reviewed polyline endpoint moved for {key}")
    policy = critical_signal_policy(0.25)
    plan = make_polyline_plan(
        board,
        net_name,
        points,
        pcbnew.F_Cu,
        width_mm=SIGNAL_WIDTH_MM,
        policy=policy,
        endpoint_pads=(start, goal),
        note=f"reviewed top-layer {net_name} local branch",
    )
    return commit_route_plan(board, plan, policy=policy), plan.track_length_mm


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE_REPORT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    args.input = args.input.resolve()
    args.output = args.output.resolve()
    args.report = args.report.resolve()
    args.baseline_report = args.baseline_report.resolve()
    args.manifest = args.manifest.resolve()
    if args.input == args.output:
        parser.error("--output must differ from --input")

    board = pcbnew.LoadBoard(str(args.input))
    if board is None:
        raise RuntimeError(f"could not load {args.input}")
    if board.GetCopperLayerCount() != 4:
        raise RuntimeError("audio/storage stage requires four copper layers")
    permitted_prior_nets = {"GND", "USB_D+", "USB_D-"}
    prior_track_counts = Counter(str(item.GetNetname()) for item in board.GetTracks())
    unexpected_prior = set(prior_track_counts) - permitted_prior_nets
    if unexpected_prior:
        raise RuntimeError(
            "audio/storage stage accepts only prior GND/USB routing; found "
            + ", ".join(sorted(unexpected_prior))
        )

    raw_unconnected = count_unconnected(board)
    fill_ground_zones(board)
    baseline_unconnected = count_unconnected(board)
    baseline_drc, report_unconnected = write_drc(board, args.baseline_report)
    if baseline_drc != 0 or report_unconnected != baseline_unconnected:
        raise RuntimeError(
            "filled baseline failed closed: "
            f"DRC={baseline_drc}, API ratsnest={baseline_unconnected}, "
            f"report ratsnest={report_unconnected}"
        )

    accepted: list[dict[str, object]] = []
    rejected_power: list[tuple[str, str]] = []
    current_unconnected = baseline_unconnected
    step = 0

    # Local bypass branches are routed before high-speed signals.  Their
    # current loops must remain local; allowing later signal routes to force
    # long detours would defeat the purpose of the decouplers.
    mapping = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for connection in LOCAL_POWER_CONNECTIONS:
        if connection.label in {"MIC1_LOCAL_BYPASS", "MIC2_LOCAL_BYPASS"}:
            continue
        step += 1
        start_fp = mapping.get(connection.start_ref)
        goal_fp = mapping.get(connection.goal_ref)
        if start_fp is None or goal_fp is None:
            raise RuntimeError(f"{connection.label}: missing footprint")
        start = start_fp.FindPadByNumber(connection.start_pad)
        goal = goal_fp.FindPadByNumber(connection.goal_pad)
        if start is None or goal is None:
            raise RuntimeError(f"{connection.label}: missing endpoint pad")
        if int(start.GetNetCode()) <= 0 or int(start.GetNetCode()) != int(goal.GetNetCode()):
            raise RuntimeError(f"{connection.label}: endpoints do not share a real net")
        local_policy = power_policy(connection.width_mm)
        try:
            plan = connect_pad_centers(
                board,
                start,
                goal,
                width_mm=connection.width_mm,
                policy=local_policy,
                commit=False,
            )
            if not isinstance(plan, RoutePlan):
                raise RuntimeError("power preflight unexpectedly committed copper")
        except RouteSafetyError:
            try:
                plan = route_astar_low_speed(
                    board,
                    start,
                    goal,
                    layers=(pcbnew.F_Cu,),
                    width_mm=connection.width_mm,
                    policy=local_policy,
                    force_critical_net=True,
                    commit=False,
                )
                if not isinstance(plan, RoutePlan):
                    raise RuntimeError("power A* unexpectedly committed copper")
            except RouteSafetyError as exc:
                reason = str(exc).splitlines()[0]
                rejected_power.append((connection.label, reason))
                print(f"[{step:02d}] defer {connection.label}: {reason}")
                continue

        items = commit_route_plan(board, plan, policy=local_policy)
        fill_ground_zones(board)
        proposed_unconnected = count_unconnected(board)
        step_report = args.report.with_name(
            f"{args.report.stem}_step_{step:02d}{args.report.suffix}"
        )
        proposed_drc, drc_unconnected = write_drc(board, step_report)
        if (
            proposed_drc != 0
            or proposed_unconnected != current_unconnected - 1
            or drc_unconnected != proposed_unconnected
        ):
            remove_items(board, items)
            reason = (
                f"rollback: DRC 0->{proposed_drc}, ratsnest "
                f"{current_unconnected}->{proposed_unconnected}, "
                f"report ratsnest={drc_unconnected}"
            )
            rejected_power.append((connection.label, reason))
            print(f"[{step:02d}] defer {connection.label}: {reason}")
            continue

        accepted.append({
            "stage": "local_power",
            "label": connection.label,
            "net": str(start.GetNetname()),
            "from": f"{connection.start_ref}.{connection.start_pad}",
            "to": f"{connection.goal_ref}.{connection.goal_pad}",
            "layer": "F.Cu",
            "width_mm": f"{connection.width_mm:.3f}",
            "segments": len(plan.segments),
            "vias": len(plan.vias),
            "length_mm": f"{plan.track_length_mm:.3f}",
            "unconnected_before": current_unconnected,
            "unconnected_after": proposed_unconnected,
            "rationale": connection.rationale,
        })
        current_unconnected = proposed_unconnected
        print(
            f"[{step:02d}] accept {connection.label}: "
            f"length={plan.track_length_mm:.3f} mm, "
            f"ratsnest={current_unconnected}, DRC=0"
        )

    signal_links: list[tuple[str, object, object]] = []
    for net_name in SIGNAL_ORDER:
        chain = SIGNAL_CHAINS[net_name]
        endpoints = [endpoint(board, ref, pad, net_name) for ref, pad in chain]
        signal_links.extend((net_name, start, goal) for start, goal in iter_pairs(endpoints))
    signal_links.sort(
        key=lambda item: (
            (
                item[0], item[1].reference, item[1].pad_number,
                item[2].reference, item[2].pad_number,
            ) not in TOP_ONLY_LINKS,
            SIGNAL_ORDER.index(item[0]),
        )
    )

    for net_name, start, goal in signal_links:
            step += 1
            link_key = (
                net_name, start.reference, start.pad_number,
                goal.reference, goal.pad_number,
            )
            start_pad = find_pad(board, start.reference, start.pad_number)
            goal_pad = find_pad(board, goal.reference, goal.pad_number)
            top_only = link_key in TOP_ONLY_LINKS
            if top_only:
                added, length = add_reviewed_top_polyline(
                    board,
                    net_name,
                    start.reference,
                    start.pad_number,
                    goal.reference,
                    goal.pad_number,
                )
                route_layers = "F.Cu"
                via_count = 0
            else:
                signal_policy = critical_signal_policy(0.25)
                plan = route_astar_low_speed(
                    board,
                    start_pad,
                    goal_pad,
                    layers=(pcbnew.F_Cu, pcbnew.In2_Cu),
                    width_mm=SIGNAL_WIDTH_MM,
                    policy=signal_policy,
                    force_critical_net=True,
                    commit=False,
                )
                if not isinstance(plan, RoutePlan):
                    raise RuntimeError("critical-net A* unexpectedly committed copper")
                added = commit_route_plan(board, plan, policy=signal_policy)
                length = plan.track_length_mm
                layers_used = sorted({int(segment.layer) for segment in plan.segments})
                route_layers = "/".join(pcbnew.LayerName(layer) for layer in layers_used)
                via_count = len(plan.vias)
            # Refill the solid planes after every possible through-via so the
            # DRC evaluates current antipads rather than stale zone geometry.
            fill_ground_zones(board)
            proposed_unconnected = count_unconnected(board)
            step_report = args.report.with_name(
                f"{args.report.stem}_step_{step:02d}{args.report.suffix}"
            )
            proposed_drc, drc_unconnected = write_drc(board, step_report)
            if (
                proposed_drc != 0
                or proposed_unconnected != current_unconnected - 1
                or drc_unconnected != proposed_unconnected
            ):
                remove_items(board, added)
                raise RuntimeError(
                    f"{net_name} {start.reference}.{start.pad_number}->"
                    f"{goal.reference}.{goal.pad_number} failed closed: "
                    f"DRC 0->{proposed_drc}, ratsnest "
                    f"{current_unconnected}->{proposed_unconnected}, "
                    f"report ratsnest={drc_unconnected}"
                )
            accepted.append({
                "stage": "signal",
                "label": net_name,
                "net": net_name,
                "from": f"{start.reference}.{start.pad_number}",
                "to": f"{goal.reference}.{goal.pad_number}",
                "layer": route_layers,
                "width_mm": f"{SIGNAL_WIDTH_MM:.3f}",
                "segments": len(added),
                "vias": via_count,
                "length_mm": f"{length:.3f}",
                "unconnected_before": current_unconnected,
                "unconnected_after": proposed_unconnected,
                "rationale": "Dedicated QSPI/PDM clock or data connection",
            })
            current_unconnected = proposed_unconnected
            print(
                f"[{step:02d}] accept {net_name}: "
                f"{accepted[-1]['from']}->{accepted[-1]['to']}, "
                f"length={length:.3f} mm, ratsnest={current_unconnected}, DRC=0"
            )

    # The microphone VDD and PDM-data pads swap left/right order between each
    # microphone and its adjacent C19/C20/R8/R9 row.  The data traces therefore
    # claim F.Cu first; each VDD branch makes one short In2.Cu crossover using
    # two ordinary 0.45/0.20 mm vias.  This preserves the PDM return path over
    # solid In1.Cu and avoids a via in any microphone land.
    for connection in LOCAL_POWER_CONNECTIONS:
        if connection.label not in {"MIC1_LOCAL_BYPASS", "MIC2_LOCAL_BYPASS"}:
            continue
        step += 1
        start = mapping[connection.start_ref].FindPadByNumber(connection.start_pad)
        goal = mapping[connection.goal_ref].FindPadByNumber(connection.goal_pad)
        if start is None or goal is None:
            raise RuntimeError(f"{connection.label}: missing endpoint pad")
        local_policy = power_policy(connection.width_mm)
        plan = route_astar_low_speed(
            board,
            start,
            goal,
            layers=(pcbnew.F_Cu, pcbnew.In2_Cu),
            width_mm=connection.width_mm,
            policy=local_policy,
            force_critical_net=True,
            commit=False,
        )
        if not isinstance(plan, RoutePlan):
            raise RuntimeError("microphone power A* unexpectedly committed copper")
        items = commit_route_plan(board, plan, policy=local_policy)
        fill_ground_zones(board)
        proposed_unconnected = count_unconnected(board)
        step_report = args.report.with_name(
            f"{args.report.stem}_step_{step:02d}{args.report.suffix}"
        )
        proposed_drc, drc_unconnected = write_drc(board, step_report)
        if (
            proposed_drc != 0
            or proposed_unconnected != current_unconnected - 1
            or drc_unconnected != proposed_unconnected
        ):
            remove_items(board, items)
            raise RuntimeError(
                f"{connection.label} failed closed: DRC 0->{proposed_drc}, "
                f"ratsnest {current_unconnected}->{proposed_unconnected}, "
                f"report ratsnest={drc_unconnected}"
            )
        layers_used = sorted({int(segment.layer) for segment in plan.segments})
        accepted.append({
            "stage": "local_power",
            "label": connection.label,
            "net": str(start.GetNetname()),
            "from": f"{connection.start_ref}.{connection.start_pad}",
            "to": f"{connection.goal_ref}.{connection.goal_pad}",
            "layer": "/".join(pcbnew.LayerName(layer) for layer in layers_used),
            "width_mm": f"{connection.width_mm:.3f}",
            "segments": len(plan.segments),
            "vias": len(plan.vias),
            "length_mm": f"{plan.track_length_mm:.3f}",
            "unconnected_before": current_unconnected,
            "unconnected_after": proposed_unconnected,
            "rationale": connection.rationale,
        })
        current_unconnected = proposed_unconnected
        print(
            f"[{step:02d}] accept {connection.label}: "
            f"length={plan.track_length_mm:.3f} mm, "
            f"vias={len(plan.vias)}, ratsnest={current_unconnected}, DRC=0"
        )

    ground_policy = power_policy(SIGNAL_WIDTH_MM)
    for escape in GROUND_ESCAPES:
        step += 1
        pad = mapping[escape.reference].FindPadByNumber(escape.pad_number)
        if pad is None or str(pad.GetNetname()) != "GND":
            raise RuntimeError(f"{escape.label}: endpoint is not a GND pad")
        origin = pad.GetPosition()
        via_position = pcbnew.VECTOR2I(
            origin.x + pcbnew.FromMM(escape.dx_mm),
            origin.y + pcbnew.FromMM(escape.dy_mm),
        )
        segments: list[PlannedSegment] = []
        if not pad.GetEffectiveShape(pcbnew.F_Cu).Collide(via_position, 0):
            segments.append(
                PlannedSegment(
                    origin,
                    via_position,
                    pcbnew.F_Cu,
                    SIGNAL_WIDTH_MM,
                )
            )
        plan = RoutePlan(
            net_name="GND",
            segments=segments,
            vias=[PlannedVia(via_position, 0.45, 0.20)],
            endpoint_pads=(pad,),
            note=escape.rationale,
        )
        added = commit_route_plan(board, plan, policy=ground_policy)
        fill_ground_zones(board)
        proposed_unconnected = count_unconnected(board)
        step_report = args.report.with_name(
            f"{args.report.stem}_step_{step:02d}{args.report.suffix}"
        )
        proposed_drc, drc_unconnected = write_drc(board, step_report)
        if (
            proposed_drc != 0
            or proposed_unconnected != current_unconnected - 1
            or drc_unconnected != proposed_unconnected
        ):
            remove_items(board, added)
            raise RuntimeError(
                f"{escape.label} failed closed: DRC 0->{proposed_drc}, "
                f"ratsnest {current_unconnected}->{proposed_unconnected}, "
                f"report ratsnest={drc_unconnected}"
            )
        via_x = pcbnew.ToMM(via_position.x)
        via_y = pcbnew.ToMM(via_position.y)
        accepted.append({
            "stage": "local_ground",
            "label": escape.label,
            "net": "GND",
            "from": f"{escape.reference}.{escape.pad_number}",
            "to": f"VIA@{via_x:.3f}/{via_y:.3f}",
            "layer": "F.Cu/via/In1.Cu-zone",
            "width_mm": f"{SIGNAL_WIDTH_MM:.3f}",
            "segments": len(segments),
            "vias": 1,
            "length_mm": f"{plan.track_length_mm:.3f}",
            "unconnected_before": current_unconnected,
            "unconnected_after": proposed_unconnected,
            "rationale": escape.rationale,
        })
        current_unconnected = proposed_unconnected
        print(
            f"[{step:02d}] accept {escape.label}: "
            f"ratsnest={current_unconnected}, DRC=0"
        )

    for link in GROUND_LINKS:
        step += 1
        start = mapping[link.reference].FindPadByNumber(link.start_pad)
        goal = mapping[link.reference].FindPadByNumber(link.goal_pad)
        if start is None or goal is None:
            raise RuntimeError(f"{link.label}: missing microphone ground pad")
        try:
            plan = connect_pad_centers(
                board,
                start,
                goal,
                width_mm=SIGNAL_WIDTH_MM,
                policy=ground_policy,
                commit=False,
            )
        except RouteSafetyError:
            plan = route_astar_low_speed(
                board,
                start,
                goal,
                layers=(pcbnew.F_Cu,),
                width_mm=SIGNAL_WIDTH_MM,
                policy=ground_policy,
                commit=False,
            )
        if not isinstance(plan, RoutePlan):
            raise RuntimeError("microphone ground preflight unexpectedly committed copper")
        added = commit_route_plan(board, plan, policy=ground_policy)
        fill_ground_zones(board)
        proposed_unconnected = count_unconnected(board)
        step_report = args.report.with_name(
            f"{args.report.stem}_step_{step:02d}{args.report.suffix}"
        )
        proposed_drc, drc_unconnected = write_drc(board, step_report)
        if (
            proposed_drc != 0
            or proposed_unconnected != current_unconnected - 1
            or drc_unconnected != proposed_unconnected
        ):
            remove_items(board, added)
            raise RuntimeError(
                f"{link.label} failed closed: DRC 0->{proposed_drc}, "
                f"ratsnest {current_unconnected}->{proposed_unconnected}, "
                f"report ratsnest={drc_unconnected}"
            )
        accepted.append({
            "stage": "local_ground",
            "label": link.label,
            "net": "GND",
            "from": f"{link.reference}.{link.start_pad}",
            "to": f"{link.reference}.{link.goal_pad}",
            "layer": "F.Cu",
            "width_mm": f"{SIGNAL_WIDTH_MM:.3f}",
            "segments": len(plan.segments),
            "vias": 0,
            "length_mm": f"{plan.track_length_mm:.3f}",
            "unconnected_before": current_unconnected,
            "unconnected_after": proposed_unconnected,
            "rationale": link.rationale,
        })
        current_unconnected = proposed_unconnected
        print(
            f"[{step:02d}] accept {link.label}: "
            f"length={plan.track_length_mm:.3f} mm, "
            f"ratsnest={current_unconnected}, DRC=0"
        )

    fill_ground_zones(board)
    ensure_in1_ground_plane(board, power_policy(0.15))
    final_track_counts = Counter(str(item.GetNetname()) for item in board.GetTracks())
    for prior_net, prior_count in prior_track_counts.items():
        if final_track_counts[prior_net] != prior_count:
            raise RuntimeError(f"audio/storage stage altered prior {prior_net} routing")
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            if (
                abs(pcbnew.ToMM(track.GetWidth()) - 0.45) > 0.0005
                or abs(pcbnew.ToMM(track.GetDrillValue()) - 0.20) > 0.0005
            ):
                raise RuntimeError("audio/storage stage used a non-standard via")
        elif int(track.GetLayer()) in (pcbnew.In1_Cu, pcbnew.B_Cu):
            raise RuntimeError("audio/storage stage placed a track on In1.Cu or B.Cu")
        if str(track.GetNetname()) not in (
            set(SIGNAL_CHAINS) | {"3V_FLASH", "3V_MIC"} | permitted_prior_nets
        ):
            raise RuntimeError(
                f"audio/storage stage touched forbidden net {track.GetNetname()}"
            )

    final_unconnected = count_unconnected(board)
    final_drc, final_report_unconnected = write_drc(board, args.report)
    if (
        final_drc != 0
        or final_unconnected != current_unconnected
        or final_report_unconnected != final_unconnected
    ):
        raise RuntimeError(
            "final audio/storage candidate failed closed: "
            f"DRC={final_drc}, API ratsnest={final_unconnected}, "
            f"expected={current_unconnected}, report={final_report_unconnected}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    copy_project_companions(args.input, args.output)
    fieldnames = tuple(accepted[0].keys())
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(accepted)

    print(f"input={args.input}")
    print(f"output={args.output}")
    print(f"report={args.report}")
    print(f"manifest={args.manifest}")
    print(f"raw_unconnected={raw_unconnected}")
    print(f"filled_baseline_unconnected={baseline_unconnected}")
    print(f"final_unconnected={final_unconnected}")
    print(f"accepted_routes={len(accepted)}")
    print(f"deferred_local_power_routes={len(rejected_power)}")
    print(f"drc_violations={final_drc}")
    for label, reason in rejected_power:
        print(f"deferred={label}: {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
