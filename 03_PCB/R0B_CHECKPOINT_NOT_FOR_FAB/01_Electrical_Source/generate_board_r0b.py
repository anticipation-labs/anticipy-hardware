#!/usr/bin/env python3
"""Generate the ANT-PROD-R0B EVT KiCad PCB from the frozen design spec.

Run with KiCad's system Python::

    /usr/bin/python3 generate_board_r0b.py

This generator creates the board outline, exact footprints, net assignments,
placement, mechanical envelopes, net classes, and ground-plane intent. Routing
is a separate reviewed step; an unrouted output is never fabrication-ready.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import pcbnew

from design_spec_r0b import COMPONENT_BY_REF, NETS, PARTS, PART_BY_REF, ROOT_UUID
from footprint_builders_r0b import (
    add_battery_envelope,
    add_motor_envelope,
    make_button_access_target,
    make_cmm3424,
    make_esd441_dpy,
    make_indicator_lightpipe_target,
    make_led,
    make_pogo_pad,
    make_usb4500,
    make_wirepads,
)


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "Anticipy_PROD_R0B_EVT.kicad_pcb"
FP_ROOT = Path("/usr/share/kicad/footprints")
LOCAL_FP_LIB = ROOT / "Anticipy_R0B.pretty"


def mm(value: float) -> int:
    return pcbnew.FromMM(float(value))


def vec(x: float, y: float) -> pcbnew.VECTOR2I:
    return pcbnew.VECTOR2I(mm(x), mm(y))


board = pcbnew.BOARD()
board.GetDesignSettings().SetCopperLayerCount(4)
board.GetDesignSettings().SetBoardThickness(mm(0.8))


def add_net(name: str) -> pcbnew.NETINFO_ITEM:
    item = pcbnew.NETINFO_ITEM(board, name)
    board.Add(item)
    return item


NET = {name: add_net(name) for name in NETS}


# Placement values are centres/origins in global KiCad millimetres. J1 is the
# exception documented by its manufacturer: its origin is the straight PCB
# edge/connector-centreline intersection, not its body centre.
PLACEMENT: dict[str, tuple[float, float, float]] = {
    "J1": (20.00, 30.00, 90.0),
    # Rotate the two-line USB ESD array so D+ is above D-, matching U1's USB
    # pad order.  This removes an otherwise unavoidable differential-pair
    # crossover.  The 0.20 mm inboard shift adds fan-out room while retaining
    # a clean placement DRC against J1 and the adjacent VBUS capacitor.
    "U4": (28.20, 30.00, 270.0),
    # CC-line shunt protection sits at the connector end of the board.  The
    # compacted courtyard retains the official SOT-323 copper land pattern.
    "U6": (28.90, 23.10, 0.0),
    # The complete nPM1300 power cell below is a 180-degree rotation of
    # Nordic's official QEAA config-4 v1.2 pick-and-place layout.  Rotating the
    # reference cell puts USB/charger pins toward J1 and both buck cells toward
    # the open board centre without changing the manufacturer's topology.
    "U2": (35.20, 28.60, 180.0),
    "MIC1": (46.30, 23.90, 0.0),
    "MIC2": (51.20, 23.90, 0.0),
    "U5": (48.20, 30.70, 0.0),
    # Rotation 0 places the module's all-layer antenna keepout along the top
    # edge (Y=21.50).  The rear motor occupies only Y>=27.50, so no motor metal
    # sits under the antenna.  The sealed-unit RF test remains a release gate.
    "U1": (59.75, 29.50, 0.0),
    "BT1": (54.40, 28.80, 90.0),
    "SW1": (30.00, 36.30, 0.0),
    "LED1": (34.00, 36.70, 0.0),
    "U3": (51.30, 36.45, 0.0),
    "Q1": (45.95, 36.50, 180.0),
    "D1": (42.35, 35.00, 0.0),
    "D2": (28.40, 32.75, 0.0),
    "M1": (54.40, 33.00, 90.0),
    # The ties remain beside their Nordic reference return cells, but do not
    # overlap the capacitor lands.  Short, reviewed PVSS traces connect pad 1;
    # pad 2 then enters the single continuous GND plane.
    "NT1": (43.15, 33.50, 0.0),
    "NT2": (43.60, 23.50, 90.0),
    "R5": (48.90, 35.00, 0.0),
    "R6": (48.90, 36.30, 0.0),
    "R7": (53.25, 33.15, 90.0),
    "R8": (47.30, 26.80, 0.0),
    "R9": (52.10, 26.80, 0.0),
    # Raytac's mandatory 27-ohm USB elements and its two local 10-uF caps fit
    # side-by-side in the 1.5-mm corridor below the module.  Their 0402/0201
    # lands retain 0.5 mm copper-to-edge clearance on the 18-mm board.
    "R10": (60.30, 38.00, 0.0),
    "R11": (61.80, 38.00, 0.0),
    "C17": (53.25, 31.25, 90.0),
    "C18": (53.30, 28.80, 90.0),
    "C19": (45.30, 26.80, 0.0),
    "C20": (50.10, 26.80, 0.0),
    "C21": (49.80, 38.20, 0.0),
    "C22": (40.00, 36.80, 0.0),
    "C23": (37.30, 36.80, 0.0),
    "C24": (53.35, 36.60, 90.0),
    "C25": (58.50, 38.00, 0.0),
    "C26": (63.50, 38.00, 0.0),
    "C27": (51.50, 38.20, 0.0),
}

# Official Nordic nPM1300-QEAA config-4 v1.2 coordinates, transformed from
# Altium mil/Y-up into KiCad mm/Y-down and then rotated 180 degrees about U2.
# Controlled source SHA-256:
# d714c8c54fa508df5ffd01099bd945ef4d48ba4411dd75f06c0a6bfbbb76d936
NPM1300_REFERENCE_PLACEMENT: dict[str, tuple[float, float, float]] = {
    "C15": (39.625, 25.800, 0.0),
    "C14": (39.625, 31.900, 0.0),
    "C16": (30.750, 27.675, 90.0),
    "C13": (35.800, 24.600, 90.0),
    "C10": (34.600, 34.100, 90.0),
    "C9": (33.400, 34.100, 90.0),
    "C8": (41.925, 25.750, 0.0),
    "R4": (33.100, 24.600, 90.0),
    "R3": (32.500, 24.600, 90.0),
    "R2": (35.000, 24.600, 90.0),
    "R1": (34.400, 24.600, 90.0),
    "C4": (29.500, 27.400, 270.0),
    "C2": (40.025, 30.150, 90.0),
    "C5": (30.700, 30.650, 90.0),
    "C6": (30.175, 25.500, 0.0),
    "L1": (41.900, 30.625, 90.0),
    "L2": (42.400, 27.575, 180.0),
    "C1": (29.500, 30.025, 90.0),
    "C3": (40.025, 27.550, 270.0),
    "C7": (40.700, 32.950, 0.0),
}
PLACEMENT.update(NPM1300_REFERENCE_PLACEMENT)

# Rear-side pogo pads are accessible during bare-PCBA test and become covered
# by the battery only after first-article electrical approval.  1.50 mm pitch
# gives 0.50 mm copper-to-copper spacing for the 1.0 mm pads.
for index in range(9):
    PLACEMENT[f"TP{index + 1}"] = (35.00 + 1.50 * index, 30.00, 0.0)
for index in range(5):
    PLACEMENT[f"TP{index + 10}"] = (35.00 + 1.50 * index, 31.50, 0.0)


def load_stock(footprint_id: str, reference: str, value: str,
               x: float, y: float, rotation: float) -> pcbnew.FOOTPRINT:
    library, name = footprint_id.split(":", 1)
    fp = pcbnew.FootprintLoad(str(FP_ROOT / f"{library}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"KiCad footprint not found: {footprint_id}")
    fp.SetReference(reference)
    fp.SetValue(value)
    fp.SetFPIDAsString(footprint_id)
    fp.SetPosition(vec(x, y))
    fp.SetOrientationDegrees(rotation)
    board.Add(fp)
    return fp


def load_stock_compact_courtyard(
    stock_id: str,
    local_name: str,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float,
    max_local_x: float,
    max_local_y: float,
) -> pcbnew.FOOTPRINT:
    """Clone a verified stock land pattern with a controlled R0B courtyard.

    Copper, mask, paste, fab geometry, antenna keepouts, and 3-D models remain
    untouched.  Only the stock courtyard margin is reduced to 0.25 mm for U1
    and 0.15 mm for the sub-1.5-mm U4 body, consistent with KiCad library
    convention.  Actual copper/mask clearance remains enforced independently.
    """

    fp = load_stock(stock_id, reference, value, x, y, rotation)
    fp.SetFPIDAsString(f"Anticipy_R0B:{local_name}")
    for graphic in fp.GraphicalItems():
        if reference == "U4" and graphic.GetLayer() == pcbnew.F_SilkS:
            # At 270 degrees the stock DRT polarity polygon clips the solder
            # mask.  Keep it in the assembly source on F.Fab, where it remains
            # useful without creating an unprintable silkscreen warning.
            graphic.SetLayer(pcbnew.F_Fab)
        if reference == "U1" and graphic.GetLayer() == pcbnew.F_SilkS:
            start = graphic.GetStart0()
            end = graphic.GetEnd0()
            if min(pcbnew.ToMM(start.y), pcbnew.ToMM(end.y)) < -7.50:
                # The module's top body line follows the board edge.  Preserve
                # it on assembly drawings without asking the fab to clip ink.
                graphic.SetLayer(pcbnew.Dwgs_User)
        if graphic.GetLayer() != pcbnew.F_CrtYd:
            continue
        for getter, setter in (
            (graphic.GetStart0, graphic.SetStart0),
            (graphic.GetEnd0, graphic.SetEnd0),
        ):
            point = getter()
            local_x = max(-max_local_x, min(max_local_x, pcbnew.ToMM(point.x)))
            local_y = max(-max_local_y, min(max_local_y, pcbnew.ToMM(point.y)))
            setter(vec(local_x, local_y))
    return fp


def create_footprint(reference: str) -> pcbnew.FOOTPRINT:
    component = PART_BY_REF[reference]
    x, y, rotation = PLACEMENT[reference]
    value = component.value
    if reference == "J1":
        fp = make_usb4500(board, reference, value, x, y, rotation,
                          include_edge_cuts=False)
    elif reference in {"MIC1", "MIC2"}:
        fp = make_cmm3424(board, reference, value, x, y, rotation)
    elif reference == "LED1":
        fp = make_led(board, reference, value, x, y, rotation)
    elif reference == "D2":
        fp = make_esd441_dpy(board, reference, value, x, y, rotation)
    elif reference == "U1":
        fp = load_stock_compact_courtyard(
            "RF_Module:Raytac_MDBT50Q", "Raytac_MDBT50Q_R0B",
            reference, value, x, y, rotation, 5.50, 8.00,
        )
    elif reference == "U4":
        fp = load_stock_compact_courtyard(
            "Package_TO_SOT_SMD:Texas_DRT-3", "Texas_DRT-3_R0B",
            reference, value, x, y, rotation, 0.65, 0.55,
        )
    elif reference == "U6":
        fp = load_stock_compact_courtyard(
            "Package_TO_SOT_SMD:SOT-323_SC-70", "TI_DCK_SC70_3_R0B",
            reference, value, x, y, rotation, 1.25, 0.90,
        )
    elif reference == "BT1":
        fp = make_wirepads(
            board, reference, value, x, y, 3, 1.27, rotation, bottom=True
        )
    elif reference == "M1":
        fp = make_wirepads(
            board, reference, value, x, y, 2, 1.27, rotation, bottom=True
        )
    elif reference.startswith("TP"):
        fp = make_pogo_pad(
            board, reference, value, x, y, rotation, bottom=True
        )
    else:
        fp = load_stock(component.footprint, reference, value, x, y, rotation)
    fp.SetPath(pcbnew.KIID_PATH(
        f"/{ROOT_UUID}/{COMPONENT_BY_REF[reference]['symbol_uuid']}"
    ))
    return fp


FOOTPRINTS = {part.ref: create_footprint(part.ref) for part in PARTS}


def set_net(reference: str, pad_number: str, net_name: str) -> None:
    pads = [p for p in FOOTPRINTS[reference].Pads()
            if p.GetNumber() == str(pad_number)]
    if not pads:
        raise KeyError(f"{reference} pad {pad_number} missing")
    for pad in pads:
        pad.SetNet(NET[net_name])


for part in PARTS:
    for pin in part.pins:
        if pin.net is not None:
            set_net(part.ref, pin.number, pin.net)


# Mechanical-only reference envelopes. They are excluded from the BOM/CPL by
# the builder and deliberately do not participate in schematic connectivity.
MH_BAT = add_battery_envelope(
    board, "MH_BAT", 40.05, 30.00, 0.0, bottom=True,
    length=26.0, width=15.5,
)
MH_MOTOR = add_motor_envelope(
    board, "MH_MOTOR", 60.55, 32.50, 0.0, bottom=True, diameter=10.0,
)
MH_BUTTON = make_button_access_target(
    board, "MH_BUTTON", 30.00, 36.30, opening_diameter=1.50,
)
MH_LED = make_indicator_lightpipe_target(
    board, "MH_LED", 34.00, 36.70,
    aperture_diameter=1.00, lightpipe_keepout_diameter=1.60,
)


# Closed concave outline with the exact 9.24 x 6.20 mm USB U-cutout at left.
# It is 45.8 x 18.0 mm overall: within the 47 x 18 mm rush-quote PCB envelope
# and inside the frozen 51 x 21 mm product exterior.
OUTLINE_POINTS = [
    (26.20, 25.38),  # USB cutout upper inboard corner
    (26.20, 34.62),
    (20.00, 34.62),  # lower cutout mouth
    (20.50, 35.80),
    (21.50, 36.70),
    (24.50, 38.30),
    (28.50, 39.00),
    (58.50, 39.00),
    (63.80, 39.00),
    (65.00, 38.50),
    (65.80, 37.70),
    (65.80, 22.30),
    (65.00, 21.50),
    (63.80, 21.00),
    (58.50, 21.00),
    (28.50, 21.00),
    (24.50, 21.70),
    (21.50, 23.30),
    (20.50, 24.20),
    (20.00, 25.38),  # upper cutout mouth
]


def add_segment(a: tuple[float, float], b: tuple[float, float],
                layer: int = pcbnew.Edge_Cuts, width: float = 0.10) -> None:
    segment = pcbnew.PCB_SHAPE(board)
    segment.SetShape(pcbnew.SHAPE_T_SEGMENT)
    segment.SetStart(vec(*a))
    segment.SetEnd(vec(*b))
    segment.SetLayer(layer)
    segment.SetWidth(mm(width))
    board.Add(segment)


for start, end in zip(OUTLINE_POINTS, OUTLINE_POINTS[1:] + OUTLINE_POINTS[:1]):
    add_segment(start, end)


def add_zone(layer: int, net_name: str) -> pcbnew.ZONE:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(NET[net_name])
    zone.SetLocalClearance(mm(0.127))
    # Use solid pad connections on the thin 0.8 mm board.  The two USB shell
    # stakes sit beside the mid-mount cutout and cannot physically support the
    # default two-spoke thermal.  Solid connection also gives the uninterrupted
    # In1 reference plane the lowest practical impedance.  This setting was
    # verified after zone fill: it removes the four S3/S4 starved-thermal DRC
    # errors without relaxing any copper, hole, or edge-clearance rule.
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    polygon = zone.Outline()
    polygon.NewOutline()
    for x, y in OUTLINE_POINTS:
        polygon.Append(mm(x), mm(y))
    board.Add(zone)
    return zone


# L2 is the uninterrupted RF/digital reference plane. A bottom ground fill is
# also present, but it may be interrupted by routing. The Raytac footprint's
# manufacturer keepout excludes both zones from the antenna area.  Battery,
# motor, wire lands, and pogo pads are rear-side post-PCBA features; all reflow
# components stay on the top for one-pass assembly.
add_zone(pcbnew.In1_Cu, "GND")
add_zone(pcbnew.B_Cu, "GND")


def add_text(text: str, x: float, y: float, layer: int,
             size: float = 0.45) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(vec(x, y))
    item.SetLayer(layer)
    item.SetTextHeight(mm(size))
    item.SetTextWidth(mm(size))
    item.SetTextThickness(mm(0.10))
    board.Add(item)


for fp in board.GetFootprints():
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)

add_text("R0B", 29.1, 22.20, pcbnew.Dwgs_User, 0.80)
add_text("ANT-PROD-R0B EVT / NOT FOR FAB", 34.0, 38.10,
         pcbnew.Dwgs_User, 0.42)
add_text("USB 90R GEOMETRY: FAB STACKUP REQUIRED", 42.0, 22.10,
         pcbnew.Dwgs_User, 0.40)
add_text("REAR BATTERY 26x15.5x4.8 MAX", 40.05, 30.0,
         pcbnew.Dwgs_User, 0.42)
add_text("TOP-RIGHT RF WINDOW: POLYCARBONATE ONLY", 59.6, 22.3,
         pcbnew.Dwgs_User, 0.38)


# Conservative rush-fab defaults: 5/5 mil and 0.20/0.45 mm PTH vias.  The
# absolute board floor permits exactly two explicitly placed 0.36/0.16 mm
# mechanical through vias in the reversible USB-C fanout; Canadian Circuits
# publishes about 6 mil as its mechanical-drill floor, but rush-CAM approval is
# still a release gate.  All ordinary routing keeps the 0.45/0.20 mm default.
# USB differential width/gap remains provisional until the fabricator supplies
# the actual 0.8 mm stack-up calculation.
settings = board.GetDesignSettings()
settings.m_MinClearance = mm(0.127)
settings.m_TrackMinWidth = mm(0.127)
settings.m_ViasMinSize = mm(0.36)
settings.m_MinThroughDrill = mm(0.16)
# Zero is the absolute board-level floor so the project rule file can express
# the GCT connector's intentional edge intersection.  A 0.50 mm custom rule
# restores the normal edge clearance for every item not owned by J1.
settings.m_CopperEdgeClearance = mm(0.0)
default_nc = board.GetAllNetClasses()["Default"]
default_nc.SetClearance(mm(0.127))
default_nc.SetTrackWidth(mm(0.127))
default_nc.SetViaDiameter(mm(0.45))
default_nc.SetViaDrill(mm(0.20))


# Persist custom footprints as an editable project-local KiCad library. This
# makes Update PCB from Schematic work without relying only on embedded copies.
if not LOCAL_FP_LIB.exists():
    pcbnew.FootprintLibCreate(str(LOCAL_FP_LIB))
for reference in (
    "J1", "MIC1", "LED1", "D2", "U1", "U4", "U6", "BT1", "M1", "TP1",
):
    footprint = FOOTPRINTS[reference]
    if reference == "U1":
        # Footprint rule areas use board coordinates in KiCad 7.  Translate a
        # duplicate to the library origin before saving or the antenna
        # keepouts would be stored at the placed board coordinate.
        footprint = footprint.Duplicate()
        footprint.SetPosition(vec(0.0, 0.0))
        footprint.SetOrientationDegrees(0.0)
    pcbnew.FootprintSave(str(LOCAL_FP_LIB), footprint)
for mechanical in (MH_BAT, MH_MOTOR, MH_BUTTON, MH_LED):
    pcbnew.FootprintSave(str(LOCAL_FP_LIB), mechanical)


pcbnew.SaveBoard(str(OUT), board)


def persist_physical_stackup() -> None:
    """Embed a 0.80-mm four-layer *provisional* physical stackup.

    KiCad otherwise exports this generated four-layer board as 1.60 mm in
    STEP even though ``general/thickness`` says 0.80 mm.  These dielectric
    values are a controlled geometry placeholder; the fabricator must replace
    them with its impedance-controlled construction before release.
    """

    stackup = '''    (stackup
      (layer "F.SilkS" (type "Top Silk Screen") (color "White"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (color "Green") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 1" (type "prepreg") (thickness 0.105) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.018))
      (layer "dielectric 2" (type "core") (thickness 0.484) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.018))
      (layer "dielectric 3" (type "prepreg") (thickness 0.105) (material "FR4") (epsilon_r 4.2) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.035))
      (layer "B.Mask" (type "Bottom Solder Mask") (color "Green") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen") (color "White"))
      (copper_finish "ENIG")
      (dielectric_constraints no)
    )
'''
    text = OUT.read_text(encoding="utf-8")
    marker = "  (setup\n"
    if marker not in text:
        raise RuntimeError("cannot locate KiCad setup block for stackup")
    if "    (stackup\n" in text:
        raise RuntimeError("generated board unexpectedly already has a stackup")
    OUT.write_text(text.replace(marker, marker + stackup, 1), encoding="utf-8")


persist_physical_stackup()


def persist_project_netclasses() -> None:
    """Keep the USB fanout class deterministic across board regeneration.

    KiCad stores named net classes and their net assignments in the project
    JSON rather than the PCB file.  ``SaveBoard`` can rewrite that JSON, so the
    generator restores this narrowly scoped class only after saving the board.
    """
    project_path = OUT.with_suffix(".kicad_pro")
    if not project_path.is_file():
        raise RuntimeError(f"missing KiCad project file: {project_path}")
    project = json.loads(project_path.read_text(encoding="utf-8"))
    net_settings = project.setdefault("net_settings", {})
    usb_class = {
        "bus_width": 12,
        "clearance": 0.127,
        "diff_pair_gap": 0.127,
        "diff_pair_via_gap": 0.127,
        "diff_pair_width": 0.127,
        "line_style": 0,
        "microvia_diameter": 0.3,
        "microvia_drill": 0.1,
        "name": "USB_FS_FANOUT",
        "pcb_color": "rgba(0, 0, 0, 0.000)",
        "schematic_color": "rgba(0, 0, 0, 0.000)",
        "track_width": 0.127,
        "via_diameter": 0.36,
        "via_drill": 0.16,
        "wire_width": 6,
    }
    classes = [
        item for item in net_settings.get("classes", [])
        if item.get("name") != usb_class["name"]
    ]
    classes.append(usb_class)
    net_settings["classes"] = classes
    assignments = dict(net_settings.get("netclass_assignments") or {})
    assignments["USB_D+"] = usb_class["name"]
    assignments["USB_D-"] = usb_class["name"]
    assignments["USB_MCU_D+"] = usb_class["name"]
    assignments["USB_MCU_D-"] = usb_class["name"]
    net_settings["netclass_assignments"] = assignments
    project_path.write_text(
        json.dumps(project, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


persist_project_netclasses()


with (ROOT / "pad_net_report.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(["reference", "value", "pad", "net", "x_mm", "y_mm", "side"])
    for fp in sorted(board.GetFootprints(), key=lambda item: item.GetReference()):
        if fp.GetReference().startswith("MH_"):
            continue
        for pad in fp.Pads():
            pos = pad.GetPosition()
            writer.writerow([
                fp.GetReference(), fp.GetValue(), pad.GetNumber(), pad.GetNetname(),
                f"{pcbnew.ToMM(pos.x):.4f}", f"{pcbnew.ToMM(pos.y):.4f}",
                "B" if fp.IsFlipped() else "F",
            ])


with (ROOT / "BOM.csv").open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow([
        "reference", "quantity_per_board", "value", "manufacturer", "mpn",
        "footprint", "side", "description", "datasheet",
    ])
    for part in PARTS:
        if part.mpn == "TESTPAD":
            continue
        side = "Rear / hand solder" if part.ref in {"BT1", "M1"} else "Top"
        writer.writerow([
            part.ref, 1, part.value, part.manufacturer, part.mpn, part.footprint,
            side, part.description, part.datasheet,
        ])

print(f"Generated {OUT}")
print(f"Electrical footprints: {len(PARTS)}; named nets: {len(NETS)}")
print("Routing status: UNROUTED - fabrication export remains blocked")
