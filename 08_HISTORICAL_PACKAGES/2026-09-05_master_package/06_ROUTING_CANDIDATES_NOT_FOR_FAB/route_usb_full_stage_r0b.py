#!/usr/bin/env /usr/bin/python3
"""Build the deterministic USB-only routing candidate for Anticipy R0B.

Authority is intentionally narrow: this stage may create copper only on GND,
VBUS, USB_CC1, USB_CC2, USB_D+/D-, and USB_MCU_D+/D-.  It routes the grouped
USB-C contacts through the protection parts and 27-ohm series resistors to the
Raytac module.  No unrelated net is touched and In1.Cu remains a GND zone.

The 0.127/0.127 mm USB geometry is provisional pending the fabricator's
0.8-mm stack-up/90-ohm field-solver result.  Exactly two 0.36/0.16 mm through
vias are allowed for the reversible Type-C fanout; every other via created by
this stage is 0.45/0.20 mm.  Output is withheld unless a fresh full-board DRC
is zero.  This remains a routing candidate, not a fabrication release.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
import re
import shutil

import pcbnew


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
DEFAULT_OUTPUT = ROOT / "reports" / "USB_ROUTED_CANDIDATE.kicad_pcb"
DEFAULT_REPORT = ROOT / "reports" / "USB_ROUTED_CANDIDATE_DRC.txt"
DEFAULT_SUMMARY = ROOT / "reports" / "USB_ROUTED_CANDIDATE_SUMMARY.txt"
DEFAULT_MANIFEST = ROOT / "reports" / "USB_ROUTED_CANDIDATE_ROUTES.csv"

USB_WIDTH_MM = 0.127
USB_GAP_MM = 0.127
SIGNAL_WIDTH_MM = 0.15
VBUS_WIDTH_MM = 0.30
GROUND_WIDTH_MM = 0.30
STANDARD_VIA_DIAMETER_MM = 0.45
STANDARD_VIA_DRILL_MM = 0.20
SMALL_VIA_DIAMETER_MM = 0.36
SMALL_VIA_DRILL_MM = 0.16

F = pcbnew.F_Cu
L3 = pcbnew.In2_Cu
B = pcbnew.B_Cu

OWNED_NETS = {
    "GND",
    "VBUS",
    "USB_CC1",
    "USB_CC2",
    "USB_D+",
    "USB_D-",
    "USB_MCU_D+",
    "USB_MCU_D-",
}
DATA_NETS = {"USB_D+", "USB_D-", "USB_MCU_D+", "USB_MCU_D-"}

EXPECTED_PADS: dict[tuple[str, str], tuple[float, float, str]] = {
    ("J1", "1"): (26.7500, 33.2000, "GND"),
    ("J1", "2"): (26.7500, 32.4000, "VBUS"),
    ("J1", "4"): (26.7500, 31.2500, "USB_CC1"),
    ("J1", "5"): (26.7500, 30.7500, "USB_D-"),
    ("J1", "6"): (26.7500, 30.2500, "USB_D+"),
    ("J1", "7"): (26.7500, 29.7500, "USB_D-"),
    ("J1", "8"): (26.7500, 29.2500, "USB_D+"),
    ("J1", "10"): (26.7500, 28.2500, "USB_CC2"),
    ("J1", "11"): (26.7500, 27.6000, "VBUS"),
    ("J1", "12"): (26.7500, 26.8000, "GND"),
    ("U4", "1"): (27.7750, 29.6500, "USB_D+"),
    ("U4", "2"): (27.7750, 30.3500, "USB_D-"),
    ("U4", "3"): (28.6250, 30.0000, "GND"),
    ("U6", "1"): (27.9000, 22.4500, "USB_CC1"),
    ("U6", "2"): (27.9000, 23.7500, "USB_CC2"),
    ("U6", "3"): (29.9000, 23.1000, "GND"),
    ("D2", "1"): (28.0500, 32.7500, "VBUS"),
    ("D2", "2"): (28.7500, 32.7500, "GND"),
    ("C1", "1"): (29.5000, 29.2500, "VBUS"),
    ("C1", "2"): (29.5000, 30.8000, "GND"),
    ("U2", "21"): (32.7625, 28.8500, "VBUS"),
    ("U2", "23"): (32.7625, 29.8500, "USB_CC1"),
    ("U2", "24"): (32.7625, 30.3500, "USB_CC2"),
    ("R10", "1"): (59.9800, 38.0000, "USB_D+"),
    ("R10", "2"): (60.6200, 38.0000, "USB_MCU_D+"),
    ("R11", "1"): (61.4800, 38.0000, "USB_D-"),
    ("R11", "2"): (62.1200, 38.0000, "USB_MCU_D-"),
    ("U1", "34"): (64.4000, 35.6500, "USB_MCU_D-"),
    ("U1", "35"): (64.4000, 34.8500, "USB_MCU_D+"),
}


def mm(value: float) -> int:
    return int(pcbnew.FromMM(float(value)))


def as_mm(value: int) -> float:
    return float(pcbnew.ToMM(value))


def vec(position: tuple[float, float]) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(position[0]), mm(position[1]))


def footprint(board: pcbnew.BOARD, reference: str) -> pcbnew.FOOTPRINT:
    matches = [fp for fp in board.GetFootprints() if fp.GetReference() == reference]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {reference}, found {len(matches)}")
    return matches[0]


def pad(board: pcbnew.BOARD, reference: str, number: str) -> pcbnew.PAD:
    item = footprint(board, reference).FindPadByNumber(number)
    if item is None:
        raise RuntimeError(f"missing pad {reference}.{number}")
    return item


def net(board: pcbnew.BOARD, name: str) -> pcbnew.NETINFO_ITEM:
    item = board.FindNet(name)
    if item is None or int(item.GetNetCode()) <= 0:
        raise RuntimeError(f"missing net {name}")
    return item


def validate_frozen_input(board: pcbnew.BOARD) -> None:
    if list(board.GetTracks()):
        raise RuntimeError("USB stage requires the clean zero-copper R0B board")
    for (reference, number), (expected_x, expected_y, expected_net) in EXPECTED_PADS.items():
        item = pad(board, reference, number)
        position = item.GetPosition()
        actual = (as_mm(position.x), as_mm(position.y))
        if math.dist(actual, (expected_x, expected_y)) > 0.001:
            raise RuntimeError(
                f"{reference}.{number} moved: expected "
                f"({expected_x:.4f}, {expected_y:.4f}), found "
                f"({actual[0]:.4f}, {actual[1]:.4f})"
            )
        if str(item.GetNetname()) != expected_net:
            raise RuntimeError(
                f"{reference}.{number} net changed: expected {expected_net}, "
                f"found {item.GetNetname()}"
            )
    u4 = footprint(board, "U4")
    if abs((float(u4.GetOrientationDegrees()) % 360.0) - 270.0) > 0.01:
        raise RuntimeError("U4 orientation no longer matches reviewed R0B geometry")
    if pcbnew.In1_Cu not in tuple(board.GetEnabledLayers().CuStack()):
        raise RuntimeError("R0B In1.Cu reference layer is not enabled")
    gnd_zone_layers = {
        int(zone.GetLayer())
        for zone in board.Zones()
        if not zone.GetIsRuleArea() and str(zone.GetNetname()) == "GND"
    }
    if gnd_zone_layers != {pcbnew.In1_Cu, pcbnew.B_Cu}:
        raise RuntimeError("expected the frozen In1/B GND zones")


def is_octilinear(
    start: tuple[float, float], end: tuple[float, float]
) -> bool:
    dx = abs(end[0] - start[0])
    dy = abs(end[1] - start[1])
    return (dx > 0.0005 or dy > 0.0005) and (
        dx <= 0.0005 or dy <= 0.0005 or abs(dx - dy) <= 0.0005
    )


def add_track(
    board: pcbnew.BOARD,
    name: str,
    layer: int,
    start: tuple[float, float],
    end: tuple[float, float],
    width_mm: float,
) -> pcbnew.PCB_TRACK:
    if name not in OWNED_NETS:
        raise RuntimeError(f"USB stage attempted unrelated net {name}")
    if layer not in (F, L3, B) or layer == pcbnew.In1_Cu:
        raise RuntimeError(f"USB stage attempted forbidden track layer {layer}")
    if not is_octilinear(start, end):
        raise RuntimeError(f"non-octilinear route: {start} -> {end}")
    item = pcbnew.PCB_TRACK(board)
    item.SetNet(net(board, name))
    item.SetLayer(layer)
    item.SetWidth(mm(width_mm))
    item.SetStart(vec(start))
    item.SetEnd(vec(end))
    board.Add(item)
    return item


def add_path(
    board: pcbnew.BOARD,
    label: str,
    name: str,
    layer: int,
    points: tuple[tuple[float, float], ...],
    width_mm: float,
    manifest: list[dict[str, str | int | float]],
    *,
    length_group: str = "",
) -> float:
    length = 0.0
    for start, end in zip(points, points[1:]):
        add_track(board, name, layer, start, end, width_mm)
        length += math.dist(start, end)
    manifest.append(
        {
            "label": label,
            "net": name,
            "layer": board.GetLayerName(layer),
            "segments": max(0, len(points) - 1),
            "vias": 0,
            "width_mm": width_mm,
            "length_mm": round(length, 4),
            "length_group": length_group,
        }
    )
    return length


def add_via(
    board: pcbnew.BOARD,
    label: str,
    name: str,
    position: tuple[float, float],
    manifest: list[dict[str, str | int | float]],
    *,
    small: bool = False,
) -> pcbnew.PCB_VIA:
    if name not in OWNED_NETS:
        raise RuntimeError(f"USB stage attempted unrelated net {name}")
    if small and name not in {"USB_D+", "USB_D-"}:
        raise RuntimeError("small-via exception is restricted to connector D+/D-")
    diameter = SMALL_VIA_DIAMETER_MM if small else STANDARD_VIA_DIAMETER_MM
    drill = SMALL_VIA_DRILL_MM if small else STANDARD_VIA_DRILL_MM
    item = pcbnew.PCB_VIA(board)
    item.SetNet(net(board, name))
    item.SetPosition(vec(position))
    item.SetWidth(mm(diameter))
    item.SetDrill(mm(drill))
    item.SetViaType(pcbnew.VIATYPE_THROUGH)
    item.SetLayerPair(F, B)
    board.Add(item)
    manifest.append(
        {
            "label": label,
            "net": name,
            "layer": "F.Cu-B.Cu",
            "segments": 0,
            "vias": 1,
            "width_mm": diameter,
            "length_mm": 0.0,
            "length_group": "small_via" if small else "standard_via",
        }
    )
    return item


def fill_ground(board: pcbnew.BOARD) -> None:
    found: set[int] = set()
    for zone in board.Zones():
        if zone.GetIsRuleArea() or str(zone.GetNetname()) != "GND":
            continue
        layer = int(zone.GetLayer())
        if layer in (pcbnew.In1_Cu, pcbnew.B_Cu):
            zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            found.add(layer)
    if found != {pcbnew.In1_Cu, pcbnew.B_Cu}:
        raise RuntimeError("missing an R0B GND reference zone")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def connectivity_count(board: pcbnew.BOARD) -> int:
    board.BuildConnectivity()
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    return int(connectivity.GetUnconnectedCount(False))


def route_data_pair(
    board: pcbnew.BOARD,
    manifest: list[dict[str, str | int | float]],
) -> tuple[float, float]:
    # Reversible connector merge.  Only these two vias use the documented
    # 0.36/0.16 mm mechanical-drill exception.
    add_path(board, "J1_8_TO_U4_1", "USB_D+", F,
             ((26.750, 29.250), (27.375, 29.250), (27.775, 29.650)),
             USB_WIDTH_MM, manifest)
    add_path(board, "J1_5_TO_U4_2", "USB_D-", F,
             ((26.750, 30.750), (27.375, 30.750), (27.775, 30.350)),
             USB_WIDTH_MM, manifest)

    dminus_branch = (27.100, 29.750)
    dplus_branch = (27.250, 30.250)
    add_path(board, "J1_7_BRANCH", "USB_D-", F,
             ((26.750, 29.750), dminus_branch), USB_WIDTH_MM, manifest)
    add_via(board, "J1_7_SMALL_VIA", "USB_D-", dminus_branch, manifest,
            small=True)
    add_path(board, "J1_6_BRANCH", "USB_D+", F,
             ((26.750, 30.250), dplus_branch), USB_WIDTH_MM, manifest)
    add_via(board, "J1_6_SMALL_VIA", "USB_D+", dplus_branch, manifest,
            small=True)

    dplus_escape = (28.250, 28.750)
    dminus_escape = (28.250, 31.250)
    plus_length = add_path(
        board, "U4_DPLUS_ESCAPE", "USB_D+", F,
        ((27.775, 29.650), (27.775, 29.225), dplus_escape),
        USB_WIDTH_MM, manifest, length_group="D+",
    )
    minus_length = add_path(
        board, "U4_DMINUS_ESCAPE", "USB_D-", F,
        ((27.775, 30.350), (27.775, 30.775), dminus_escape),
        USB_WIDTH_MM, manifest, length_group="D-",
    )
    add_via(board, "DPLUS_ESCAPE_VIA", "USB_D+", dplus_escape, manifest)
    add_via(board, "DMINUS_ESCAPE_VIA", "USB_D-", dminus_escape, manifest)

    add_path(board, "J1_6_CROSSOVER", "USB_D+", B,
             (dplus_branch, (26.750, 30.750), (26.250, 30.750),
              (26.250, 29.250), (26.750, 28.750), dplus_escape),
             USB_WIDTH_MM, manifest)
    add_path(board, "J1_7_CROSSOVER", "USB_D-", L3,
             (dminus_branch, (27.600, 29.250), (28.500, 29.250),
              (29.000, 29.750), (29.000, 30.500), dminus_escape),
             USB_WIDTH_MM, manifest)

    # The CC target transitions sit immediately west of U2.  Bring the pair
    # below those standard drills before beginning the controlled long run.
    # The long corridor uses 0.260 mm centre spacing: 0.127 mm copper and
    # 0.133 mm physical gap, retaining a small deterministic DRC margin over
    # the nominal 0.127 mm gap requirement.
    dplus_main = (31.500, 31.500)
    dminus_main = (31.500, 31.760)
    plus_length += add_path(
        board, "DPLUS_PAIR_ENTRY", "USB_D+", L3,
        (dplus_escape, (29.000, 28.750), (31.500, 31.250), dplus_main),
        USB_WIDTH_MM, manifest, length_group="D+",
    )
    minus_length += add_path(
        board, "DMINUS_PAIR_ENTRY", "USB_D-", L3,
        (dminus_escape, (29.000, 31.250), (29.510, 31.760), dminus_main),
        USB_WIDTH_MM, manifest, length_group="D-",
    )

    dplus_resistor_via = (59.980, 37.350)
    dminus_resistor_via = (61.480, 37.350)
    plus_length += add_path(
        board, "DPLUS_LONG_PAIR", "USB_D+", L3,
        (dplus_main, (33.500, 31.500), (35.300, 29.700),
         (53.500, 29.700), (58.000, 34.200)),
        USB_WIDTH_MM, manifest, length_group="D+",
    )
    add_via(board, "DPLUS_RIGHT_LAYER_VIA", "USB_D+", (58.000, 34.200),
            manifest)
    plus_length += add_path(
        board, "DPLUS_RIGHT_B_FANOUT", "USB_D+", B,
        ((58.000, 34.200), (58.000, 35.370), dplus_resistor_via),
        USB_WIDTH_MM, manifest, length_group="D+",
    )
    # A shallow length-tuning excursion on D- compensates the longer
    # R10-to-U1 module-side leg.  It lies in open In2 area, after the PMIC and
    # before the right-side fanout, and never crosses the D+ corridor.
    minus_length += add_path(
        board, "DMINUS_LONG_PAIR", "USB_D-", L3,
        (dminus_main, (33.392, 31.760), (33.500, 31.868),
         (35.408, 29.960), (45.000, 29.960), (46.020, 30.980),
         (46.980, 30.980), (48.000, 29.960), (53.160, 29.960),
         (53.500, 30.300), (58.000, 34.800), (59.480, 36.280),
         (60.910, 36.280), (61.480, 36.850), dminus_resistor_via),
        USB_WIDTH_MM, manifest, length_group="D-",
    )
    add_via(board, "DPLUS_R10_INPUT_VIA", "USB_D+", dplus_resistor_via,
            manifest)
    add_via(board, "DMINUS_R11_INPUT_VIA", "USB_D-", dminus_resistor_via,
            manifest)
    plus_length += add_path(
        board, "DPLUS_TO_R10", "USB_D+", F,
        (dplus_resistor_via, (59.980, 38.000)), USB_WIDTH_MM, manifest,
        length_group="D+",
    )
    minus_length += add_path(
        board, "DMINUS_TO_R11", "USB_D-", F,
        (dminus_resistor_via, (61.480, 38.000)), USB_WIDTH_MM, manifest,
        length_group="D-",
    )

    # Module-side nets after the mandatory 27-ohm resistors.
    dplus_mcu_start = (60.620, 37.350)
    dminus_mcu_start = (62.120, 37.350)
    dplus_mcu_end = (62.700, 34.850)
    dminus_mcu_end = (62.700, 35.650)
    plus_length += add_path(
        board, "R10_OUTPUT_ESCAPE", "USB_MCU_D+", F,
        ((60.620, 38.000), dplus_mcu_start), USB_WIDTH_MM, manifest,
        length_group="D+",
    )
    minus_length += add_path(
        board, "R11_OUTPUT_ESCAPE", "USB_MCU_D-", F,
        ((62.120, 38.000), dminus_mcu_start), USB_WIDTH_MM, manifest,
        length_group="D-",
    )
    add_via(board, "R10_OUTPUT_VIA", "USB_MCU_D+", dplus_mcu_start,
            manifest)
    add_via(board, "R11_OUTPUT_VIA", "USB_MCU_D-", dminus_mcu_start,
            manifest)
    plus_length += add_path(
        board, "DPLUS_MCU_INNER", "USB_MCU_D+", B,
        (dplus_mcu_start, (60.620, 36.930), dplus_mcu_end),
        USB_WIDTH_MM, manifest, length_group="D+",
    )
    minus_length += add_path(
        board, "DMINUS_MCU_INNER", "USB_MCU_D-", B,
        (dminus_mcu_start, (62.517, 37.350), (63.097, 36.770),
         (63.097, 36.047), dminus_mcu_end),
        USB_WIDTH_MM, manifest, length_group="D-",
    )
    add_via(board, "DPLUS_U1_VIA", "USB_MCU_D+", dplus_mcu_end, manifest)
    add_via(board, "DMINUS_U1_VIA", "USB_MCU_D-", dminus_mcu_end, manifest)
    plus_length += add_path(
        board, "DPLUS_TO_U1", "USB_MCU_D+", F,
        (dplus_mcu_end, (64.400, 34.850)), USB_WIDTH_MM, manifest,
        length_group="D+",
    )
    minus_length += add_path(
        board, "DMINUS_TO_U1", "USB_MCU_D-", F,
        (dminus_mcu_end, (64.400, 35.650)), USB_WIDTH_MM, manifest,
        length_group="D-",
    )
    return plus_length, minus_length


def route_cc(
    board: pcbnew.BOARD,
    manifest: list[dict[str, str | int | float]],
) -> None:
    # CC2 remains on F.Cu and touches U6.2 before reaching the PMIC.  The
    # jog at y=28.75 clears C6/C5 while retaining clearance from the CC1
    # target via.
    add_path(board, "CC2_J1_TO_U6", "USB_CC2", F,
             ((26.750, 28.250), (27.550, 28.250), (28.000, 27.800),
              (28.000, 24.000), (27.900, 23.900), (27.900, 23.750)),
             SIGNAL_WIDTH_MM, manifest)
    add_path(board, "CC2_U6_TO_U2", "USB_CC2", F,
             ((27.900, 23.750), (31.700, 23.750), (31.700, 28.750),
              (31.400, 29.050), (31.400, 30.350),
              (32.7625, 30.350)), SIGNAL_WIDTH_MM, manifest)

    # CC1 crosses the connector neck on B.Cu.  It first travels around the
    # connector's lower-left edge, then uses x=30.8 mm as a dedicated trunk;
    # the separate VBUS trunk is 0.6 mm west of it.
    cc1_source = (27.550, 31.250)
    cc1_u6 = (28.500, 22.450)
    cc1_target = (31.850, 29.850)
    add_path(board, "CC1_J1_ESCAPE", "USB_CC1", F,
             ((26.750, 31.250), cc1_source),
             SIGNAL_WIDTH_MM, manifest)
    add_via(board, "CC1_SOURCE_VIA", "USB_CC1", cc1_source, manifest)
    add_path(board, "CC1_U6_ESCAPE", "USB_CC1", F,
             ((27.900, 22.450), cc1_u6), SIGNAL_WIDTH_MM, manifest)
    add_via(board, "CC1_U6_VIA", "USB_CC1", cc1_u6, manifest)
    add_path(board, "CC1_B_TRUNK", "USB_CC1", B,
             (cc1_source, (27.000, 31.800), (26.000, 31.800),
              (26.000, 34.500), (30.800, 34.500),
              (30.800, 23.150), (29.200, 23.150), cc1_u6),
             SIGNAL_WIDTH_MM, manifest)
    add_path(board, "CC1_TARGET_BRANCH", "USB_CC1", B,
             ((30.800, 29.850), cc1_target), SIGNAL_WIDTH_MM, manifest)
    add_via(board, "CC1_TARGET_VIA", "USB_CC1", cc1_target, manifest)
    add_path(board, "CC1_TO_U2", "USB_CC1", F,
             (cc1_target, (32.7625, 29.850)), SIGNAL_WIDTH_MM, manifest)


def route_vbus(
    board: pcbnew.BOARD,
    manifest: list[dict[str, str | int | float]],
) -> None:
    top_via = (27.350, 27.600)
    bottom_via = (27.350, 32.400)
    local_junction = (30.200, 28.850)
    u2_via = (32.150, 28.850)
    for label, position in (
        ("VBUS_TOP_VIA", top_via),
        ("VBUS_BOTTOM_VIA", bottom_via),
        ("VBUS_LOCAL_JUNCTION", local_junction),
        ("VBUS_U2_VIA", u2_via),
    ):
        add_via(board, label, "VBUS", position, manifest)

    add_path(board, "VBUS_J1_TOP", "VBUS", F,
             ((26.750, 27.600), top_via), VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_J1_BOTTOM", "VBUS", F,
             ((26.750, 32.400), bottom_via), VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_D2_TAP", "VBUS", F,
             ((28.050, 32.750), (27.700, 32.400), bottom_via),
             VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_C1_ESCAPE", "VBUS", F,
             ((29.500, 29.250), (29.800, 29.250), local_junction),
             VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_U2_ESCAPE", "VBUS", F,
             (u2_via, (32.7625, 28.850)), VBUS_WIDTH_MM, manifest)

    add_path(board, "VBUS_BOTTOM_B_TRUNK", "VBUS", B,
             (bottom_via, (28.000, 32.400), (28.100, 32.500),
              (29.500, 32.500), (30.200, 31.800), local_junction),
             VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_TOP_B_TRUNK", "VBUS", B,
             (top_via, (28.000, 26.950), (30.200, 26.950),
              local_junction),
             VBUS_WIDTH_MM, manifest)
    add_path(board, "VBUS_INNER_TO_U2", "VBUS", L3,
             (local_junction, u2_via), VBUS_WIDTH_MM, manifest)


def route_usb_ground(
    board: pcbnew.BOARD,
    manifest: list[dict[str, str | int | float]],
) -> None:
    top_j1 = (27.350, 26.800)
    bottom_j1 = (27.350, 33.200)
    u6_ground = (31.300, 22.600)
    d2_ground = (29.500, 33.500)
    for label, position in (
        ("J1_TOP_GND_VIA", top_j1),
        ("J1_BOTTOM_GND_VIA", bottom_j1),
        ("U6_GND_VIA", u6_ground),
        ("D2_GND_VIA", d2_ground),
    ):
        add_via(board, label, "GND", position, manifest)

    add_path(board, "J1_PAD12_GND", "GND", F,
             ((26.750, 26.800), top_j1),
             GROUND_WIDTH_MM, manifest)
    add_path(board, "J1_PAD1_GND", "GND", F,
             ((26.750, 33.200), bottom_j1),
             GROUND_WIDTH_MM, manifest)
    add_path(board, "U4_TO_C1_GND", "GND", F,
             ((28.625, 30.000), (28.625, 30.800), (29.500, 30.800),
              (29.500, 31.500), (30.000, 32.000), (30.000, 33.000),
              d2_ground), GROUND_WIDTH_MM, manifest)
    add_path(board, "U6_GND_ESCAPE", "GND", F,
             ((29.900, 23.100), (30.400, 22.600), u6_ground),
             GROUND_WIDTH_MM, manifest)
    add_path(board, "D2_GND_ESCAPE", "GND", F,
             ((28.750, 32.750), d2_ground),
             GROUND_WIDTH_MM, manifest)


def parse_drc(report: Path) -> tuple[int, int]:
    text = report.read_text(encoding="utf-8", errors="replace")
    drc = re.search(r"\*\* Found (\d+) DRC violations \*\*", text)
    unconnected = re.search(r"\*\* Found (\d+) unconnected pads \*\*", text)
    if drc is None or unconnected is None:
        raise RuntimeError(f"could not parse DRC report {report}")
    return int(drc.group(1)), int(unconnected.group(1))


def copy_project_companions(input_path: Path, output_path: Path) -> None:
    input_stem = input_path.with_suffix("")
    output_stem = output_path.with_suffix("")
    for suffix in (".kicad_pro", ".kicad_dru", ".kicad_prl"):
        source = input_stem.with_suffix(suffix)
        if source.is_file():
            shutil.copy2(source, output_stem.with_suffix(suffix))
    table = input_path.parent / "fp-lib-table"
    if table.is_file():
        shutil.copy2(table, output_path.parent / "fp-lib-table")
    pretty = input_path.parent / "Anticipy_R0B.pretty"
    if pretty.is_dir():
        shutil.copytree(
            pretty,
            output_path.parent / "Anticipy_R0B.pretty",
            dirs_exist_ok=True,
        )


def verify_created_copper(board: pcbnew.BOARD) -> tuple[int, int, int]:
    small = 0
    standard = 0
    vias = 0
    for item in board.GetTracks():
        name = str(item.GetNetname())
        if name not in OWNED_NETS:
            raise RuntimeError(f"unrelated routed net found: {name}")
        if isinstance(item, pcbnew.PCB_VIA):
            vias += 1
            diameter = as_mm(item.GetWidth())
            drill = as_mm(item.GetDrillValue())
            if (
                abs(diameter - SMALL_VIA_DIAMETER_MM) <= 0.001
                and abs(drill - SMALL_VIA_DRILL_MM) <= 0.001
            ):
                if name not in {"USB_D+", "USB_D-"}:
                    raise RuntimeError("small via exists outside connector data fanout")
                small += 1
            elif (
                abs(diameter - STANDARD_VIA_DIAMETER_MM) <= 0.001
                and abs(drill - STANDARD_VIA_DRILL_MM) <= 0.001
            ):
                standard += 1
            else:
                raise RuntimeError(
                    f"unexpected via geometry {diameter:.3f}/{drill:.3f} mm"
                )
        elif int(item.GetLayer()) == pcbnew.In1_Cu and name != "GND":
            raise RuntimeError(f"non-GND signal copper on In1.Cu: {name}")
    if small != 2:
        raise RuntimeError(f"expected exactly two small USB vias, found {small}")
    if small + standard != vias:
        raise RuntimeError("via geometry count mismatch")
    return vias, small, standard


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    input_path = args.input.resolve()
    output_path = args.output.resolve()
    report_path = args.report.resolve()
    summary_path = args.summary.resolve()
    manifest_path = args.manifest.resolve()
    if input_path == output_path:
        parser.error("--output must differ from --input")

    board = pcbnew.LoadBoard(str(input_path))
    validate_frozen_input(board)
    raw_before = connectivity_count(board)
    fill_ground(board)
    filled_before = connectivity_count(board)

    # Only the two explicit reversible-fanout vias may use the USB class floor.
    board.GetDesignSettings().m_ViasMinSize = mm(SMALL_VIA_DIAMETER_MM)
    board.GetDesignSettings().m_MinThroughDrill = mm(SMALL_VIA_DRILL_MM)
    manifest: list[dict[str, str | int | float]] = []
    plus_length, minus_length = route_data_pair(board, manifest)
    route_cc(board, manifest)
    route_vbus(board, manifest)
    route_usb_ground(board, manifest)
    fill_ground(board)
    after = connectivity_count(board)
    via_count, small_vias, standard_vias = verify_created_copper(board)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not pcbnew.WriteDRCReport(
        board, str(report_path), pcbnew.EDA_UNITS_MILLIMETRES, False
    ):
        raise RuntimeError("KiCad did not write the USB candidate DRC report")
    drc, report_unconnected = parse_drc(report_path)
    if report_unconnected != after:
        raise RuntimeError("connectivity API and DRC report disagree")
    if drc != 0:
        raise RuntimeError(
            f"USB candidate rejected with {drc} DRC violations; output withheld"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(output_path), board)
    copy_project_companions(input_path, output_path)
    fields = (
        "label", "net", "layer", "segments", "vias", "width_mm",
        "length_mm", "length_group",
    )
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest)

    skew = abs(plus_length - minus_length)
    summary = (
        "ANTICIPY R0B USB-ONLY ROUTING CANDIDATE — NOT FOR FAB\n"
        f"Input: {input_path}\n"
        f"Output: {output_path}\n"
        f"DRC violations: {drc}\n"
        f"Raw unconnected before GND fill: {raw_before}\n"
        f"Unconnected after baseline GND fill: {filled_before}\n"
        f"Unconnected after USB stage: {after}\n"
        f"USB-stage reduction from filled baseline: {filled_before - after}\n"
        f"Total reduction from raw clean board: {raw_before - after}\n"
        f"D+ routed copper length excluding resistor body: {plus_length:.6f} mm\n"
        f"D- routed copper length excluding resistor body: {minus_length:.6f} mm\n"
        f"Absolute copper-length skew: {skew:.6f} mm\n"
        f"USB nominal width/gap: {USB_WIDTH_MM:.3f}/{USB_GAP_MM:.3f} mm\n"
        f"Created vias: {via_count} total; {small_vias} at "
        f"{SMALL_VIA_DIAMETER_MM:.2f}/{SMALL_VIA_DRILL_MM:.2f} mm; "
        f"{standard_vias} at {STANDARD_VIA_DIAMETER_MM:.2f}/"
        f"{STANDARD_VIA_DRILL_MM:.2f} mm\n"
        "In1 signal copper: 0\n"
        "Impedance status: provisional; fabricator field-solver approval required\n"
        "Release status: BLOCKED while any ratsnest remains and until electrical/DFM review\n"
    )
    summary_path.write_text(summary, encoding="utf-8")
    print(summary, end="")
    print(f"DRC report: {report_path}")
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
