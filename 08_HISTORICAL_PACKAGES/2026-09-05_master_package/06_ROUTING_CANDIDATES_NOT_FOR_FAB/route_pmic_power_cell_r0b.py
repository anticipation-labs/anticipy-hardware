#!/usr/bin/env /usr/bin/python3
"""Build the fail-closed R0B nPM1300/local-power routing candidate.

This script never overwrites the generated placement board.  It is pinned to
the post-ECO Config-4-compatible placement (C1-C10 rotated 180 degrees about
unchanged centroids).  Every reviewed copper group is kept only when it lowers
KiCad's live unconnected count and a fresh whole-board DRC remains at zero.

The result is a partial routing candidate, not a fabrication release.  In1.Cu
remains the uninterrupted GND reference plane.  All through vias are the R0B
standard 0.45/0.20 mm geometry.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import shutil

import pcbnew

from route_power_clean_candidate import (
    ManualCandidate,
    TrackSpec,
    ViaSpec,
    commit_manual_candidate,
    count_unconnected,
    fill_ground_zones,
    manual_length,
    remove_items,
    tracks,
    write_drc,
)
from routing_primitives_r0b import ensure_in1_ground_plane
from route_power_clean_candidate import policy


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
DEFAULT_OUTPUT = ROOT / "reports" / "POWER_ROUTED_CANDIDATE.kicad_pcb"
DEFAULT_REPORT = ROOT / "reports" / "power_routed_candidate_drc.txt"
DEFAULT_BASELINE = ROOT / "reports" / "power_routed_baseline_drc.txt"
DEFAULT_MANIFEST = ROOT / "reports" / "power_routed_candidate_manifest.csv"
DEFAULT_SUMMARY = ROOT / "reports" / "power_routed_candidate_summary.txt"

F = pcbnew.F_Cu
L3 = pcbnew.In2_Cu
B = pcbnew.B_Cu

EXPECTED_POSES = {
    "U2": (35.200, 28.600, 180.0),
    "L1": (41.900, 30.625, 90.0),
    "L2": (42.400, 27.575, 180.0),
    "C1": (29.500, 30.025, -90.0),
    "C2": (40.025, 30.150, -90.0),
    "C3": (40.025, 27.550, 90.0),
    "C4": (29.500, 27.400, 90.0),
    "C5": (30.700, 30.650, -90.0),
    "C6": (30.175, 25.500, 180.0),
    "C7": (40.700, 32.950, 180.0),
    "C8": (41.925, 25.750, 180.0),
    "C9": (33.400, 34.100, -90.0),
    "C10": (34.600, 34.100, -90.0),
    "C13": (35.800, 24.600, 90.0),
    "C14": (39.625, 31.900, 0.0),
    "C15": (39.625, 25.800, 0.0),
    "C16": (30.750, 27.675, 90.0),
    "NT1": (43.150, 33.500, 0.0),
    "NT2": (43.600, 23.500, 90.0),
}


@dataclass(frozen=True)
class Reviewed:
    route: ManualCandidate
    source: str
    destination: str
    rationale: str


def route(
    label: str,
    net: str,
    source: str,
    destination: str,
    parts: tuple[tuple[int, float, tuple[tuple[float, float], ...]], ...],
    *,
    vias: tuple[tuple[float, float], ...] = (),
    rationale: str,
) -> Reviewed:
    # Permit the visually compact single-layer spelling
    # ``(F, width, points)`` as well as a tuple of layer parts.
    if parts and isinstance(parts[0], int):
        parts = (parts,)  # type: ignore[assignment]
    copper: tuple[TrackSpec, ...] = ()
    for layer, width, points in parts:
        copper += tracks(net, points, width, layer)
    return Reviewed(
        ManualCandidate(
            label, net, source, destination, copper,
            tuple(ViaSpec(net, at) for at in vias), rationale,
        ),
        source,
        destination,
        rationale,
    )


ROUTES: tuple[Reviewed, ...] = (
    # Config-4-aligned buck input/switch cells.  The 0.15-mm necks are required
    # by the 0.50-mm QFN pitch; copper widens immediately outside the escape.
    route("BUCK_VSYS_TO_C2", "VSYS", "U2.4", "C2.1",
          ((F, .15, ((37.6375,28.8500),(38.2250,28.8500),(38.7500,29.3750),(39.1500,29.3750))),
           (F, .30, ((39.1500,29.3750),(40.0250,29.3750)))),
          rationale="Short top-copper Buck-1 VSYS input neck, widened at C2"),
    route("BUCK_VSYS_TO_C3", "VSYS", "U2.4 branch", "C3.1",
          ((F, .15, ((38.2250,28.8500),(38.7500,28.3250),(39.1500,28.3250))),
           (F, .30, ((39.1500,28.3250),(40.0250,28.3250)))),
          rationale="Short top-copper Buck-2 VSYS input branch, widened at C3"),
    route("PVSS1_INPUT_RETURN", "PVSS1", "U2.2", "C2.2",
          ((F, .15, ((37.6375,29.8500),(38.2250,29.8500),(39.0250,30.6500))),
           (F, .25, ((39.0250,30.6500),(39.7500,30.6500),(40.0250,30.9250)))),
          rationale="Config-4-compatible Buck-1 return escape to the rotated C2 end"),
    route("PVSS2_INPUT_RETURN", "PVSS2", "U2.6", "C3.2",
          ((F, .15, ((37.6375,27.8500),(38.2250,27.8500),(39.0250,27.0500))),
           (F, .25, ((39.0250,27.0500),(39.7500,27.0500),(40.0250,26.7750)))),
          rationale="Config-4-compatible Buck-2 return escape to the rotated C3 end"),
    route("SW1_REFERENCE_PATH", "SW1", "U2.3", "L1.2",
          ((F, .30, ((37.6375,29.3500),(38.2250,29.3500),(39.0250,30.1500),
                      (41.4400,30.1500),(41.8500,29.7400),(41.9000,29.9000)))),
          rationale="All-F.Cu transformed Config-4 Buck-1 switch path"),
    route("SW2_REFERENCE_PATH", "SW2", "U2.5", "L2.2",
          ((F, .30, ((37.6375,28.3500),(38.2250,28.3500),(39.0250,27.5500),
                      (41.5150,27.5500),(41.6750,27.5750)))),
          rationale="All-F.Cu transformed Config-4 Buck-2 switch path"),

    # Dedicated PVSS nets remain isolated until their explicit net ties.
    route("PVSS1_C2_TO_C14", "PVSS1", "C2.2", "C14.2",
          ((F, .25, ((40.0250,30.9250),(40.1050,31.0050),(40.1050,31.9000)))),
          rationale="Buck-1 high-frequency return join"),
    route("PVSS1_C14_TO_C7", "PVSS1", "C14.2", "C7.2",
          ((F, .25, ((40.1050,31.9000),(39.9250,32.9500)))),
          rationale="Buck-1 output-cap return island"),
    route("PVSS1_TO_NETTIE", "PVSS1", "C7.2", "NT1.1",
          ((F, .20, ((39.9250,32.9500),(39.3500,32.9500))),
           (B, .25, ((39.3500,32.9500),(40.0000,33.6000),(42.1500,33.6000),(42.6500,34.1000))),
           (F, .20, ((42.6500,34.1000),(42.6500,33.5000)))),
          vias=((39.3500,32.9500),(42.6500,34.1000)),
          rationale="Relocated NT1 forces one short B.Cu crossing; In1 remains GND"),
    route("PVSS2_C3_TO_C15", "PVSS2", "C3.2", "C15.2",
          ((F, .25, ((40.0250,26.7750),(40.1050,26.6950),(40.1050,25.8000)))),
          rationale="Buck-2 high-frequency return join"),
    route("PVSS2_C15_TO_C8", "PVSS2", "C15.2", "C8.2",
          ((F, .25, ((40.1050,25.8000),(41.1500,25.8000),(41.1500,25.7500)))),
          rationale="Buck-2 output-cap return island"),
    route("PVSS2_TO_NETTIE", "PVSS2", "C8.2", "NT2.1",
          ((F, .25, ((41.1500,25.7500),(41.9500,24.9500),(43.6000,24.9500),(43.6000,24.0000)))),
          rationale="Top-copper return to relocated NT2"),

    # Output-current paths stay wide and on F.Cu.  The Buck-2 VOUT sense/feed
    # uses In2 because the relocated NT/test grid prevents a planar crossing.
    route("BUCK1_L1_TO_C7", "3V_MAIN", "L1.1", "C7.1",
          ((F, .40, ((41.9000,31.3500),(41.9000,32.5250),(41.4750,32.9500)))),
          rationale="Wide short Buck-1 inductor-to-output-cap connection"),
    route("BUCK1_VOUT_SENSE", "3V_MAIN", "U2.1", "C7.1",
          ((F, .20, ((37.6375,30.3500),(38.1500,30.3500),(38.1500,33.7500),
                      (41.4750,33.7500),(41.4750,32.9500)))),
          rationale="Top-copper VOUT1 sense/feed around the C2/C14 island"),
    route("BUCK2_L2_TO_C8", "3V_FLASH", "L2.1", "C8.1",
          ((F, .40, ((43.1250,27.5750),(43.1250,26.1750),(42.7000,25.7500)))),
          rationale="Wide short Buck-2 inductor-to-output-cap connection"),
    route("BUCK2_VOUT_SENSE", "3V_FLASH", "U2.32", "L2.1",
          ((F, .20, ((36.9500,31.0375),(36.9500,33.5500),(37.0000,33.6000))),
           (L3, .25, ((37.0000,33.6000),(40.5000,33.6000),(43.6000,30.5000),(43.6000,27.5750))),
           (F, .25, ((43.6000,27.5750),(43.1250,27.5750)))),
          vias=((37.0000,33.6000),(43.6000,27.5750)),
          rationale="VOUT2 sense/feed on In2; no signal track is placed on In1"),

    route("VDDIO_LOCAL_BYPASS", "3V_MAIN", "U2.12", "C13.1",
          ((F, .15, ((35.4500,26.1625),(35.4500,25.2700),(35.8000,24.9200)))),
          rationale="Short nPM1300 VDDIO bypass connection"),
    route("VSYS_U20_TO_C16", "VSYS", "U2.20", "C16.1",
          ((F, .25, ((32.7625,28.3500),(30.9450,28.3500),(30.7500,28.1550)))),
          rationale="Local VSYS high-frequency bypass"),
    route("VSYS_C16_TO_C4", "VSYS", "C16.1", "C4.1",
          ((F, .30, ((30.7500,28.1550),(29.5000,28.1750)))),
          rationale="Local VSYS bulk branch"),
    route("VBUSOUT_LOCAL_BYPASS", "VBUSOUT", "U2.22", "C5.1",
          ((F, .25, ((32.7625,29.3500),(32.1000,29.3500),(31.5750,29.8750),(30.7000,29.8750)))),
          rationale="Short protected-output bypass after the capacitor ECO"),
    route("VBAT_LOCAL_BYPASS", "VBAT", "U2.19", "C6.1",
          ((F, .30, ((32.7625,27.8500),(32.1000,27.8500),(31.5000,27.2500),
                      (31.5000,26.0500),(30.9500,25.5000)))),
          rationale="Short battery-input bypass after the capacitor ECO"),
    route("LDO1_LOCAL_BYPASS", "3V_MIC", "U2.29", "C10.1",
          ((F, .20, ((35.4500,31.0375),(35.4500,32.4750),(34.6000,33.3250)))),
          rationale="Short LDO1/3V_MIC bulk-cap connection"),

    # One compact In2 VSYS tree joins the already-local top-copper islands.
    route("VSYS_LOCAL_BACKBONE", "VSYS", "U2.4/C2/C3", "U2.20/U2.28/C4/C9/C14/C15/C16",
          ((F, .25, ((32.7625,28.3500),(31.8000,28.3500))),
           (F, .20, ((34.9500,31.0375),(34.9500,31.5000),(34.2000,32.2500),(34.2000,32.3000))),
           (F, .20, ((39.1450,31.9000),(38.7000,32.3450),(38.7000,32.4000))),
           (F, .20, ((39.1450,25.8000),(38.6000,25.8000))),
           (F, .25, ((33.4000,33.3250),(33.4000,32.6000))),
           (L3, .30, ((31.8000,28.3500),(33.4000,29.9500),(33.4000,32.6000),
                       (34.2000,32.3000),(38.7000,32.4000))),
           (L3, .30, ((31.8000,28.3500),(33.4000,26.7500),(34.3500,25.8000),(38.6000,25.8000))),
           (L3, .30, ((31.8000,28.3500),(34.2000,28.3500),(34.7000,28.8500),(38.3000,28.8500)))),
          vias=((38.3000,28.8500),(31.8000,28.3500),(34.2000,32.3000),
                (38.7000,32.4000),(38.6000,25.8000),(33.4000,32.6000)),
          rationale="Joins local VSYS islands on In2 while preserving In1 GND"),

    # Local ground stitching.  EP vias are grouped so the electrical/thermal
    # stitch is retained by one connectivity+DRC decision.
    route("U2_EP_GND_VIAS", "GND", "U2.33", "In1/B GND planes", (),
          vias=((34.6000,28.0000),(35.8000,28.0000),(34.6000,29.2000),(35.8000,29.2000)),
          rationale="Four standard via-in-pad GND/thermal stitches; assembly review required"),
    route("C13_GND_STITCH", "GND", "C13.2", "GND planes",
          ((F, .25, ((35.8000,24.2800),(36.3000,24.2800)))), vias=((36.3000,24.2800),),
          rationale="VDDIO bypass return stitch"),
    route("C16_GND_STITCH", "GND", "C16.2", "GND planes",
          ((F, .25, ((30.7500,27.1950),(30.7500,26.5000)))), vias=((30.7500,26.5000),),
          rationale="VSYS HF bypass return stitch"),
    route("C9_C10_GND_BAR", "GND", "C9.2/C10.2", "GND planes",
          ((F, .25, ((33.4000,34.8750),(34.6000,34.8750))),
           (F, .25, ((34.0000,34.8750),(34.0000,35.4000)))), vias=((34.0000,35.4000),),
          rationale="Shared LDO/system-bulk ground-side bar only; positive nets remain separate"),
    route("C1_C5_GND_STITCH", "GND", "C1.2/C5.2", "GND planes",
          ((F, .25, ((29.5000,30.8000),(30.0000,31.3000))),
           (F, .25, ((30.7000,31.4250),(30.1250,31.4250),(30.0000,31.3000)))),
          vias=((30.0000,31.3000),), rationale="Shared charger-cap ground stitch"),
    route("C4_GND_STITCH", "GND", "C4.2", "GND planes",
          ((F, .25, ((29.5000,26.6250),(29.9500,26.1750)))), vias=((29.9500,26.1750),),
          rationale="VSYS bulk return stitch"),
    route("C6_GND_STITCH", "GND", "C6.2", "GND planes",
          ((F, .25, ((29.4000,25.5000),(28.8500,25.5000)))), vias=((28.8500,25.5000),),
          rationale="Battery bypass return stitch"),
    route("NT1_GND_STITCH", "GND", "NT1.2", "GND planes",
          ((F, .25, ((43.6500,33.5000),(44.0000,33.5000)))), vias=((44.0000,33.5000),),
          rationale="Single-point Buck-1 return-to-GND stitch"),
    route("NT2_GND_STITCH", "GND", "NT2.2", "GND planes",
          ((F, .25, ((43.6000,23.0000),(43.6000,22.6000)))), vias=((43.6000,22.6000),),
          rationale="Single-point Buck-2 return-to-GND stitch"),
)


def validate_placement(board: pcbnew.BOARD) -> None:
    if board.GetCopperLayerCount() != 4:
        raise RuntimeError("expected a four-layer board")
    if abs(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()) - 0.800) > 0.001:
        raise RuntimeError("expected the corrected 0.800-mm board stack")
    mapping = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for ref, expected in EXPECTED_POSES.items():
        fp = mapping.get(ref)
        if fp is None:
            raise RuntimeError(f"missing frozen footprint {ref}")
        p = fp.GetPosition()
        actual = (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y), fp.GetOrientationDegrees())
        angle_error = ((actual[2] - expected[2] + 180.0) % 360.0) - 180.0
        if abs(actual[0]-expected[0]) > .001 or abs(actual[1]-expected[1]) > .001 or abs(angle_error) > .01:
            raise RuntimeError(f"placement mismatch {ref}: expected {expected}, found {actual}")


def layer_names(candidate: ManualCandidate) -> str:
    names = {F: "F.Cu", L3: "In2.Cu", B: "B.Cu"}
    return "+".join(dict.fromkeys(names[t.layer] for t in candidate.tracks)) or "via-only"


def geometry(candidate: ManualCandidate) -> str:
    segments = [
        f"{pcbnew.LayerName(t.layer)}:{t.start[0]:.4f},{t.start[1]:.4f}->{t.end[0]:.4f},{t.end[1]:.4f}@{t.width_mm:.3f}"
        for t in candidate.tracks
    ]
    segments += [f"VIA:{v.at[0]:.4f},{v.at[1]:.4f}@{v.diameter_mm:.2f}/{v.drill_mm:.2f}" for v in candidate.vias]
    return ";".join(segments)


def copy_project_context(input_path: Path, output_path: Path) -> None:
    """Keep the saved candidate under the same R0B rules/exclusion context."""
    for suffix in (".kicad_dru", ".kicad_pro"):
        source = input_path.with_suffix(suffix)
        destination = output_path.with_suffix(suffix)
        if source.is_file() and source.resolve() != destination.resolve():
            shutil.copyfile(source, destination)
    table = input_path.parent / "fp-lib-table"
    if table.is_file():
        shutil.copyfile(table, output_path.parent / "fp-lib-table")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--baseline-report", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("--output must differ from --input")

    board = pcbnew.LoadBoard(str(args.input))
    validate_placement(board)
    raw = count_unconnected(board)
    fill_ground_zones(board)
    baseline = count_unconnected(board)
    baseline_drc, baseline_report_count = write_drc(board, args.baseline_report)
    if baseline_drc or baseline_report_count != baseline:
        raise RuntimeError(f"baseline failed closed: DRC={baseline_drc}, API={baseline}, report={baseline_report_count}")

    current = baseline
    rows: list[dict[str, object]] = []
    step_dir = args.report.parent / "power_routing_steps"
    step_dir.mkdir(parents=True, exist_ok=True)
    for index, reviewed in enumerate(ROUTES, 1):
        candidate = reviewed.route
        items = commit_manual_candidate(board, candidate)
        fill_ground_zones(board)
        proposed = count_unconnected(board)
        step_report = step_dir / f"{index:02d}_{candidate.label}.txt"
        drc, report_count = write_drc(board, step_report)
        accepted = drc == 0 and report_count == proposed and proposed < current
        before = current
        if not accepted:
            remove_items(board, items)
            proposed = current
        else:
            current = proposed
        rows.append({
            "index": index, "status": "ACCEPT" if accepted else "REJECT",
            "label": candidate.label, "net": candidate.net,
            "source": reviewed.source, "destination": reviewed.destination,
            "layers": layer_names(candidate), "segments": len(candidate.tracks),
            "vias": len(candidate.vias), "max_width_mm": max((t.width_mm for t in candidate.tracks), default=0),
            "length_mm": f"{manual_length(candidate):.4f}",
            "unconnected_before": before, "unconnected_after": proposed,
            "proposed_drc": drc, "geometry": geometry(candidate),
            "rationale": reviewed.rationale,
        })
        print(f"[{index:02d}/{len(ROUTES)}] {'accept' if accepted else 'reject'} {candidate.label}: {before}->{proposed}, DRC={drc}", flush=True)

    fill_ground_zones(board)
    ensure_in1_ground_plane(board, policy(.20))
    final = count_unconnected(board)
    final_drc, final_report_count = write_drc(board, args.report)
    if final_drc or final_report_count != final:
        raise RuntimeError(f"final failed closed: DRC={final_drc}, API={final}, report={final_report_count}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(args.output), board)
    copy_project_context(args.input, args.output)
    with args.manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    accepted_count = sum(row["status"] == "ACCEPT" for row in rows)
    rejected_count = len(rows) - accepted_count
    ep_row = next(row for row in rows if row["label"] == "U2_EP_GND_VIAS")
    accepted_bcu = [
        str(row["label"])
        for row in rows
        if row["status"] == "ACCEPT" and "B.Cu" in str(row["layers"])
    ]
    text = (
        "Anticipy R0B PMIC/power routing candidate\n"
        f"input={args.input}\noutput={args.output}\n"
        f"raw_unconnected={raw}\nrefilled_baseline_unconnected={baseline}\n"
        f"final_unconnected={final}\nunconnected_reduction={baseline-final}\n"
        f"accepted_groups={accepted_count}\nrejected_groups={rejected_count}\n"
        f"drc_violations={final_drc}\n"
        "in1_signal_tracks=0\nvia_geometry_mm=0.45/0.20\n"
        f"bcu_route_groups={','.join(accepted_bcu) or 'none'}\n"
        f"u2_ep_via_status={ep_row['status']} (not present in saved candidate)\n"
        "cam_gate=U2 exposed-pad GND/thermal connection must be rerouted around In2 VSYS, then reviewed as filled/capped via-in-pad or relocated dogbones before release.\n"
        "remaining_local_open=VBUS U2.21-to-C1.1 and U2.33 exposed-pad GND; global rail/test-point loads remain for later stages.\n"
        "release_status=PARTIAL CANDIDATE - NOT FABRICATION READY\n"
        "reference_limit=NT1/NT2 and R0B C9 function differ from Nordic Config 4; see manifest rationales.\n"
    )
    args.summary.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
