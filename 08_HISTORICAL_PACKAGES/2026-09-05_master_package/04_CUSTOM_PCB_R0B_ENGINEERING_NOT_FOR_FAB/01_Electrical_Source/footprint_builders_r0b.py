#!/usr/bin/env python3
"""Custom KiCad 7 footprint builders for the Anticipy R0B PCB.

All dimensions are millimetres and all land patterns are expressed as viewed
from the component side.  The functions build front-side footprints first and
then use KiCad's native ``Flip`` operation when ``bottom=True``; consequently
pads, fabrication, courtyard, and silkscreen geometry stay together on either
side of the board.

Primary dimensional sources (local copies used during implementation):

* GCT USB4500 drawing 31/05/23, sheet 1/2: ``/tmp/USB4500.pdf``
* Same Sky CMM-3424DT-26165-TR datasheet 02/27/2025, page 4:
  ``/tmp/mic.pdf``

USB4500 coordinate convention
-----------------------------
The USB footprint origin is on the product centreline at the nominal straight
PCB edge.  Local +Y points from the connector mouth into the board.  The
required 9.24 mm wide U-cutout runs from Y=0 to Y=6.20.  The SMT contact lands
start at the rear of that cutout.  Set ``include_edge_cuts=True`` only when the
surrounding board outline terminates at X=+/-4.62, Y=0; otherwise use the
Dwgs.User cutout as the authoritative outline guide and merge it into the
board outline generator.

USB pad mapping
---------------
The connector has sixteen USB-C contacts but the official land pattern merges
the paired power contacts into twelve physical lands.  The numbered lands are:

    1 A1/B12 GND       2 A4/B9 VBUS       3 B8 SBU2
    4 A5 CC1           5 B7 D-            6 A6 D+
    7 A7 D-            8 B6 D+            9 A8 SBU1
   10 B5 CC2          11 B4/A9 VBUS      12 B1/A12 GND

The four plated shell slots use pad numbers ``S1`` through ``S4`` (rear left,
rear right, front left, front right) so the board/schematic connection table
can explicitly prove that every shell stake is grounded.

Known drawing interpretation
----------------------------
The USB contact X coordinates, slot X coordinates, slot sizes, 4.00 mm slot
row pitch, 9.24 mm cutout width, and 6.20 mm cutout depth are dimensioned by
GCT.  The 1.10 mm SMT-land length and the body Y=-0.30..6.20 envelope follow
the same drawing's component-side recommended-layout datum.  GCT does not
publish a courtyard; the one here is a conservative 0.25 mm manufacturing
allowance rounded outward to the 0.05 mm grid.  Confirm the U-cutout against a
physical connector or GCT's native ECAD model before fabrication release.

The Same Sky microphone land pattern is reproduced directly: 0.35 x 2.30 mm
outer lands, 1.30 x 0.35 mm end lands, and 0.45 x 0.95 mm inner lands.  It is a
TOP-port microphone: there is deliberately no PCB acoustic hole.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import pcbnew


__all__ = [
    "USB4500_CONTACTS",
    "USB4500_CUTOUT_HALF_WIDTH",
    "USB4500_CUTOUT_DEPTH",
    "USB4500_NOMINAL_BOARD_EDGE_Y",
    "make_usb4500",
    "make_cmm3424",
    "make_led",
    "make_esd441_dpy",
    "make_pogo_pad",
    "make_wirepads",
    "add_battery_envelope",
    "add_motor_envelope",
    "make_button_access_target",
    "make_indicator_lightpipe_target",
]


def mm(value: float) -> int:
    """Convert millimetres to KiCad internal units."""

    return pcbnew.FromMM(float(value))


def vec(x: float, y: float) -> pcbnew.VECTOR2I:
    """Create a KiCad vector from millimetres."""

    return pcbnew.VECTOR2I(mm(x), mm(y))


@dataclass(frozen=True)
class UsbContact:
    number: str
    signal: str
    x: float
    width: float


USB4500_CONTACTS: tuple[UsbContact, ...] = (
    UsbContact("1", "A1/B12 GND", -3.20, 0.60),
    UsbContact("2", "A4/B9 VBUS", -2.40, 0.60),
    UsbContact("3", "B8 SBU2", -1.75, 0.30),
    UsbContact("4", "A5 CC1", -1.25, 0.30),
    UsbContact("5", "B7 D-", -0.75, 0.30),
    UsbContact("6", "A6 D+", -0.25, 0.30),
    UsbContact("7", "A7 D-", +0.25, 0.30),
    UsbContact("8", "B6 D+", +0.75, 0.30),
    UsbContact("9", "A8 SBU1", +1.25, 0.30),
    UsbContact("10", "B5 CC2", +1.75, 0.30),
    UsbContact("11", "B4/A9 VBUS", +2.40, 0.60),
    UsbContact("12", "B1/A12 GND", +3.20, 0.60),
)

USB4500_CUTOUT_HALF_WIDTH = 4.62
USB4500_CUTOUT_DEPTH = 6.20
USB4500_NOMINAL_BOARD_EDGE_Y = 0.0


def _new_footprint(board: pcbnew.BOARD, reference: str, value: str,
                   library_name: str) -> pcbnew.FOOTPRINT:
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(reference)
    fp.SetValue(value)
    if hasattr(fp, "SetFPIDAsString"):
        fp.SetFPIDAsString(f"Anticipy_R0B:{library_name}")
    board.Add(fp)
    return fp


def _set_text(fp: pcbnew.FOOTPRINT, reference_xy: tuple[float, float],
              value_xy: tuple[float, float]) -> None:
    """Give generated reference/value fields useful local defaults."""

    ref = fp.Reference()
    ref.SetPosition(vec(*reference_xy))
    ref.SetLayer(pcbnew.F_SilkS)
    ref.SetTextHeight(mm(0.80))
    ref.SetTextWidth(mm(0.80))
    ref.SetTextThickness(mm(0.12))

    value = fp.Value()
    value.SetPosition(vec(*value_xy))
    value.SetLayer(pcbnew.F_Fab)
    value.SetTextHeight(mm(0.65))
    value.SetTextWidth(mm(0.65))
    value.SetTextThickness(mm(0.10))


def _place(fp: pcbnew.FOOTPRINT, x: float, y: float, rotation: float,
           bottom: bool) -> pcbnew.FOOTPRINT:
    # Children are created in local coordinates while the footprint is at the
    # origin.  Rotate/translate only after all geometry has been added.
    fp.SetOrientationDegrees(float(rotation))
    fp.SetPosition(vec(x, y))
    if bottom:
        fp.Flip(fp.GetPosition(), False)
    return fp


def _add_segment(fp: pcbnew.FOOTPRINT, start: tuple[float, float],
                 end: tuple[float, float], layer: int,
                 width: float = 0.10) -> pcbnew.FP_SHAPE:
    shape = pcbnew.FP_SHAPE(fp)
    shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
    # FP_SHAPE stores footprint graphics in local ``*0`` coordinates.  The
    # board-space setters update only the transformed cache; KiCad 7 then
    # serializes the untouched local coordinates as ``(start 0 0) (end 0 0)``.
    # SetStart0/SetEnd0 are therefore required for generated footprint files.
    shape.SetStart0(vec(*start))
    shape.SetEnd0(vec(*end))
    shape.SetLayer(layer)
    shape.SetWidth(mm(width))
    fp.Add(shape)
    return shape


def _add_polyline(fp: pcbnew.FOOTPRINT, points: Sequence[tuple[float, float]],
                  layer: int, width: float = 0.10,
                  closed: bool = False) -> None:
    pairs = list(zip(points, points[1:]))
    if closed and len(points) > 2:
        pairs.append((points[-1], points[0]))
    for start, end in pairs:
        _add_segment(fp, start, end, layer, width)


def _add_rectangle(fp: pcbnew.FOOTPRINT, x1: float, y1: float,
                   x2: float, y2: float, layer: int,
                   width: float = 0.10) -> None:
    _add_polyline(fp, ((x1, y1), (x2, y1), (x2, y2), (x1, y2)),
                  layer, width, closed=True)


def _add_circle_segments(fp: pcbnew.FOOTPRINT, cx: float, cy: float,
                         diameter: float, layer: int, width: float = 0.10,
                         segments: int = 32) -> None:
    # Segment approximation is intentionally used instead of FP_SHAPE circle
    # setters because their Python signatures differ between KiCad 7/8/9.
    import math

    radius = diameter / 2.0
    points = [
        (cx + radius * math.cos(2.0 * math.pi * i / segments),
         cy + radius * math.sin(2.0 * math.pi * i / segments))
        for i in range(segments)
    ]
    _add_polyline(fp, points, layer, width, closed=True)


def _add_smd_pad(fp: pcbnew.FOOTPRINT, number: str, x: float, y: float,
                 size_x: float, size_y: float,
                 shape: int = pcbnew.PAD_SHAPE_ROUNDRECT,
                 roundrect_ratio: float = 0.12) -> pcbnew.PAD:
    pad = pcbnew.PAD(fp)
    pad.SetNumber(str(number))
    pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
    pad.SetShape(shape)
    if shape == pcbnew.PAD_SHAPE_ROUNDRECT:
        pad.SetRoundRectRadiusRatio(roundrect_ratio)
    pad.SetSize(vec(size_x, size_y))
    pad.SetPosition(vec(x, y))
    pad.SetPos0(vec(x, y))
    pad.SetLayerSet(pad.SMDMask())
    fp.Add(pad)
    return pad


def _add_plated_oblong(fp: pcbnew.FOOTPRINT, number: str, x: float, y: float,
                       copper_x: float, copper_y: float,
                       drill_x: float, drill_y: float) -> pcbnew.PAD:
    """Add a plated oval annulus around an oblong routed drill."""

    pad = pcbnew.PAD(fp)
    pad.SetNumber(str(number))
    pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
    pad.SetShape(pcbnew.PAD_SHAPE_OVAL)
    pad.SetSize(vec(copper_x, copper_y))
    pad.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_OBLONG)
    pad.SetDrillSize(vec(drill_x, drill_y))
    pad.SetPosition(vec(x, y))
    pad.SetPos0(vec(x, y))
    pad.SetLayerSet(pad.PTHMask())
    fp.Add(pad)
    return pad


def _mark_mechanical_only(fp: pcbnew.FOOTPRINT) -> None:
    """Exclude an enclosure-alignment target from BOM and placement outputs."""

    attrs = 0
    if hasattr(pcbnew, "FP_EXCLUDE_FROM_BOM"):
        attrs |= pcbnew.FP_EXCLUDE_FROM_BOM
    if hasattr(pcbnew, "FP_EXCLUDE_FROM_POS_FILES"):
        attrs |= pcbnew.FP_EXCLUDE_FROM_POS_FILES
    if attrs and hasattr(fp, "SetAttributes"):
        fp.SetAttributes(attrs)


def make_usb4500_03_1_a(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    include_edge_cuts: bool = False,
) -> pcbnew.FOOTPRINT:
    """Build the GCT USB4500-03-1-A 0.8 mm mid-mount receptacle.

    The local origin is the nominal board-edge/connector-centreline
    intersection.  ``include_edge_cuts`` draws only the three sides of the
    9.24 x 6.20 mm U-cutout; the main board outline must connect its two open
    endpoints at X=+/-4.62, Y=0.
    """

    fp = _new_footprint(board, reference, "USB4500-03-1-A",
                        "USB_C_Receptacle_GCT_USB4500-03-1-A_MidMount")

    # Official twelve-land pattern.  Pads are 1.10 mm long in local Y and
    # begin at the rear cutout edge (Y=6.20).
    for contact in USB4500_CONTACTS:
        _add_smd_pad(fp, contact.number, contact.x, 6.75,
                     contact.width, 1.10, pcbnew.PAD_SHAPE_RECT)

    # Official plated shell-slot geometry.  The rear pair uses the smaller
    # 1.40 mm routed drill; the front pair uses the 1.80 mm drill.
    _add_plated_oblong(fp, "S1", -5.62, 5.60,
                       1.00, 1.80, 0.60, 1.40)
    _add_plated_oblong(fp, "S2", +5.62, 5.60,
                       1.00, 1.80, 0.60, 1.40)
    _add_plated_oblong(fp, "S3", -5.62, 1.60,
                       1.00, 2.20, 0.60, 1.80)
    _add_plated_oblong(fp, "S4", +5.62, 1.60,
                       1.00, 2.20, 0.60, 1.80)

    # Exact 9.24 mm U-cutout routing guide.  Dwgs.User is always present so a
    # board-outline generator can consume/trace it without duplicating cuts.
    cutout = ((-4.62, 0.00), (-4.62, 6.20),
              (+4.62, 6.20), (+4.62, 0.00))
    _add_polyline(fp, cutout, pcbnew.Dwgs_User, 0.10)
    if include_edge_cuts:
        _add_polyline(fp, cutout, pcbnew.Edge_Cuts, 0.10)

    # 8.94 x 6.50 mm body envelope from the GCT mechanical view.  The shell
    # spring/retention tabs are represented separately by their plated slots.
    _add_rectangle(fp, -4.47, -0.30, +4.47, +6.20, pcbnew.F_Fab, 0.10)
    _add_segment(fp, (-4.47, 0.00), (+4.47, 0.00), pcbnew.F_Fab, 0.10)
    # These three shell-front lines are outside the finished PCB because the
    # receptacle is mid-mounted.  Keep them as assembly geometry rather than
    # sending off-board silkscreen to fabrication.
    _add_segment(fp, (-4.45, -0.45), (+4.45, -0.45), pcbnew.Dwgs_User, 0.15)
    _add_segment(fp, (-4.60, -0.45), (-4.60, +0.35), pcbnew.Dwgs_User, 0.15)
    _add_segment(fp, (+4.60, -0.45), (+4.60, +0.35), pcbnew.Dwgs_User, 0.15)

    # Conservative courtyard: GCT gives no courtyard.  This contains the
    # shell slots, body, and contact lands plus at least 0.25 mm.
    _add_rectangle(fp, -6.40, -0.85, +6.40, +7.55,
                   pcbnew.F_CrtYd, 0.05)

    # Pin-1 marker adjacent to the leftmost combined GND land.
    _add_circle_segments(fp, -4.00, 7.20, 0.35, pcbnew.F_SilkS, 0.10, 16)
    _set_text(fp, (0.0, 8.35), (0.0, 9.25))
    return _place(fp, x, y, rotation, bottom)


def make_cmm_3424dt_26165_tr(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
) -> pcbnew.FOOTPRINT:
    """Build Same Sky's exact top-view land pattern for its top-port PDM mic."""

    fp = _new_footprint(board, reference, "CMM-3424DT-26165-TR",
                        "SameSky_CMM-3424DT-26165-TR_TopPort_PDM")

    # Coordinates are relative to the centre of the 3.00 x 4.00 mm package.
    # Pin order/pad orientation follows the manufacturer's "Recommended PCB
    # Layout -- Top View", not an inferred bottom view.
    lands = (
        ("1", +0.425, +0.675, 0.45, 0.95),  # VDD
        ("2", +0.425, -0.675, 0.45, 0.95),  # SELECT
        ("3", -0.425, -0.675, 0.45, 0.95),  # CLOCK
        ("4", -0.425, +0.675, 0.45, 0.95),  # DATA
        ("5", +0.000, +1.725, 1.30, 0.35),  # GND
        ("6", +1.225, +0.000, 0.35, 2.30),  # GND
        ("7", +0.000, -1.725, 1.30, 0.35),  # GND
        ("8", -1.225, +0.000, 0.35, 2.30),  # GND
    )
    for number, pad_x, pad_y, size_x, size_y in lands:
        _add_smd_pad(fp, number, pad_x, pad_y, size_x, size_y,
                     pcbnew.PAD_SHAPE_RECT)

    # Exact package envelope and top acoustic-port target.  A top-port part
    # does not need (and must not receive) a PCB sound hole.
    _add_rectangle(fp, -1.50, -2.00, +1.50, +2.00, pcbnew.F_Fab, 0.10)
    # The top acoustic port is offset 0.48 mm toward the drawing's top.  KiCad
    # screen Y increases downward, hence local Y=-0.48 here.
    port_y = -0.48
    _add_circle_segments(fp, 0.0, port_y, 0.25, pcbnew.F_Fab, 0.08, 20)
    _add_circle_segments(fp, 0.0, port_y, 0.65, pcbnew.Dwgs_User, 0.08, 24)
    _add_segment(fp, (-0.45, port_y), (+0.45, port_y), pcbnew.Dwgs_User, 0.06)
    _add_segment(fp, (0.0, port_y - 0.45), (0.0, port_y + 0.45),
                 pcbnew.Dwgs_User, 0.06)

    # Corner-only silk avoids printing under the acoustic face and lands.
    corner = 0.50
    for sx in (-1.0, +1.0):
        for sy in (-1.0, +1.0):
            x_outer, y_outer = sx * 1.65, sy * 2.15
            _add_segment(fp, (x_outer, y_outer),
                         (x_outer - sx * corner, y_outer), pcbnew.F_SilkS, 0.12)
            _add_segment(fp, (x_outer, y_outer),
                         (x_outer, y_outer - sy * corner), pcbnew.F_SilkS, 0.12)

    # Pin-1 indicator beside the lower-left inner land.
    _add_circle_segments(fp, +0.85, +1.35, 0.28, pcbnew.F_SilkS, 0.10, 16)
    _add_rectangle(fp, -1.80, -2.30, +1.80, +2.30,
                   pcbnew.F_CrtYd, 0.05)
    _set_text(fp, (0.0, -2.70), (0.0, +2.70))
    return _place(fp, x, y, rotation, bottom)


def make_battery_wire_termination(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = True,
    *,
    body_length: float = 29.0,
    body_width: float = 15.5,
    pad_pitch: float = 1.27,
) -> pcbnew.FOOTPRINT:
    """Three hand-solder lands plus the installed rear-battery envelope.

    The footprint origin is the battery body centre.  Pads 1/2/3 are
    VBAT+/NTC/GND and sit at the local left-hand wire-exit edge.  The installed
    body envelope defaults to 29.0 x 15.5 mm; thickness (4.8 mm) belongs in the
    mechanical STEP/assembly drawing because a PCB footprint is 2-D.
    """

    fp = _new_footprint(board, reference, "LiPo_1S_3Wire_29x15.5x4.8",
                        "Battery_LiPo_3Wire_Solder_29x15.5")
    pad_x = -body_length / 2.0 - 0.75
    for number, pad_y in (("1", -pad_pitch), ("2", 0.0), ("3", +pad_pitch)):
        _add_smd_pad(fp, number, pad_x, pad_y, 1.80, 0.90,
                     pcbnew.PAD_SHAPE_ROUNDRECT, 0.18)

    _add_rectangle(fp, -body_length / 2.0, -body_width / 2.0,
                   +body_length / 2.0, +body_width / 2.0,
                   pcbnew.F_Fab, 0.10)
    courtyard_left = min(-body_length / 2.0 - 0.25,
                         pad_x - 0.90 - 0.25)
    _add_rectangle(fp, courtyard_left,
                   -body_width / 2.0 - 0.25,
                   +body_length / 2.0 + 0.25,
                   +body_width / 2.0 + 0.25,
                   pcbnew.F_CrtYd, 0.05)
    _add_polyline(fp, ((pad_x - 0.35, -pad_pitch - 0.65),
                       (pad_x, -pad_pitch - 1.00),
                       (pad_x + 0.35, -pad_pitch - 0.65)),
                  pcbnew.F_SilkS, 0.15)
    _set_text(fp, (0.0, -body_width / 2.0 - 0.85),
              (0.0, +body_width / 2.0 + 0.85))
    return _place(fp, x, y, rotation, bottom)


def make_haptic_coin_motor(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    motor_diameter: float = 10.0,
) -> pcbnew.FOOTPRINT:
    """Two wire lands and adhesive/mechanical circle for VCLP1020B002L."""

    fp = _new_footprint(board, reference, "VCLP1020B002L",
                        "Haptic_VCLP1020B002L_WirePads")
    body_r = motor_diameter / 2.0
    # Both wire lands are on the same exit side, outside the adhesive disc.
    _add_smd_pad(fp, "1", body_r + 1.00, -1.00, 1.20, 1.60,
                 pcbnew.PAD_SHAPE_ROUNDRECT, 0.18)
    _add_smd_pad(fp, "2", body_r + 1.00, +1.00, 1.20, 1.60,
                 pcbnew.PAD_SHAPE_ROUNDRECT, 0.18)
    _add_circle_segments(fp, 0.0, 0.0, motor_diameter,
                         pcbnew.F_Fab, 0.10, 40)
    _add_circle_segments(fp, 0.0, 0.0, motor_diameter,
                         pcbnew.Dwgs_User, 0.08, 40)
    # Courtyard encloses the motor and the external solder pads.
    _add_rectangle(fp, -body_r - 0.25, -body_r - 0.25,
                   body_r + 1.85, body_r + 0.25,
                   pcbnew.F_CrtYd, 0.05)
    _add_segment(fp, (-1.0, -body_r - 0.20), (+1.0, -body_r - 0.20),
                 pcbnew.F_SilkS, 0.12)
    _add_polyline(fp, ((body_r + 0.65, -1.80),
                       (body_r + 1.00, -2.15),
                       (body_r + 1.35, -1.80)),
                  pcbnew.F_SilkS, 0.15)
    _set_text(fp, (0.0, -body_r - 0.75), (0.0, body_r + 0.75))
    return _place(fp, x, y, rotation, bottom)


def make_button_access_target(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    opening_diameter: float = 1.50,
) -> pcbnew.FOOTPRINT:
    """Mechanical-only enclosure target centred on the switch actuator."""

    fp = _new_footprint(board, reference, "BUTTON_ACCESS_TARGET",
                        "Mechanical_Button_Access_Target")
    _mark_mechanical_only(fp)
    _add_circle_segments(fp, 0.0, 0.0, opening_diameter,
                         pcbnew.Dwgs_User, 0.10, 24)
    _add_circle_segments(fp, 0.0, 0.0, opening_diameter + 0.50,
                         pcbnew.F_Fab, 0.08, 24)
    # This target intentionally overlays the physical switch, so a component
    # courtyard would create a false collision.  Keep the enclosure clearance
    # on Dwgs.User instead.
    _add_rectangle(fp, -opening_diameter / 2.0 - 0.30,
                   -opening_diameter / 2.0 - 0.30,
                   +opening_diameter / 2.0 + 0.30,
                   +opening_diameter / 2.0 + 0.30,
                   pcbnew.Dwgs_User, 0.05)
    _set_text(fp, (0.0, -1.65), (0.0, +1.65))
    return _place(fp, x, y, rotation, bottom)


def make_indicator_lightpipe_target(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    aperture_diameter: float = 1.00,
    lightpipe_keepout_diameter: float = 1.60,
) -> pcbnew.FOOTPRINT:
    """Mechanical-only light-pipe/aperture target aligned over the RGB LED."""

    fp = _new_footprint(board, reference, "LIGHTPIPE_TARGET_1MM",
                        "Mechanical_Indicator_Lightpipe_Target")
    _mark_mechanical_only(fp)
    _add_circle_segments(fp, 0.0, 0.0, aperture_diameter,
                         pcbnew.Dwgs_User, 0.10, 24)
    _add_circle_segments(fp, 0.0, 0.0, lightpipe_keepout_diameter,
                         pcbnew.F_Fab, 0.08, 24)
    # The optical target overlays LED1 by design.  Put its envelope on
    # Dwgs.User, not F.CrtYd, to avoid a false component-overlap DRC error.
    _add_rectangle(fp, -lightpipe_keepout_diameter / 2.0 - 0.25,
                   -lightpipe_keepout_diameter / 2.0 - 0.25,
                   +lightpipe_keepout_diameter / 2.0 + 0.25,
                   +lightpipe_keepout_diameter / 2.0 + 0.25,
                   pcbnew.Dwgs_User, 0.05)
    _set_text(fp, (0.0, -1.55), (0.0, +1.55))
    return _place(fp, x, y, rotation, bottom)


# ---- Stable generator-facing API ----------------------------------------

def make_usb4500(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    include_edge_cuts: bool = False,
) -> pcbnew.FOOTPRINT:
    """Stable wrapper used by ``generate_board_r0b.py``.

    ``value`` is accepted so the schematic, BOM, and PCB can share the exact
    project value.  The geometry remains locked to USB4500-03-1-A.
    """

    fp = make_usb4500_03_1_a(
        board, reference, x, y, rotation, bottom,
        include_edge_cuts=include_edge_cuts,
    )
    fp.SetValue(value)
    return fp


def make_cmm3424(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
) -> pcbnew.FOOTPRINT:
    """Stable generator wrapper for CMM-3424DT-26165-TR."""

    fp = make_cmm_3424dt_26165_tr(board, reference, x, y, rotation, bottom)
    fp.SetValue(value)
    return fp


def make_led(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
) -> pcbnew.FOOTPRINT:
    """APHB1608LVBDSEKJ3C bi-colour LED plus 1 mm optical target.

    Pad map: 1 blue cathode, 2 blue anode, 3 red cathode, 4 red anode.
    The 0.50 x 0.40 mm lands and 1.60 x 0.80 mm body are carried from the
    controlled R0B component selection.  The optical target is mechanical; the
    enclosure/light-pipe designer still must tolerance the assembled LED
    height and light-pipe standoff.
    """

    fp = _new_footprint(board, reference, value,
                        "LED_Kingbright_APHB1608LVBDSEKJ3C")
    for number, pad_x, pad_y in (
        ("1", +0.60, -0.35),
        ("2", -0.60, -0.35),
        ("3", +0.60, +0.35),
        ("4", -0.60, +0.35),
    ):
        _add_smd_pad(fp, number, pad_x, pad_y, 0.50, 0.40,
                     pcbnew.PAD_SHAPE_RECT)
    _add_rectangle(fp, -0.80, -0.40, +0.80, +0.40, pcbnew.F_Fab, 0.08)
    _add_rectangle(fp, -1.10, -0.70, +1.10, +0.70, pcbnew.F_CrtYd, 0.05)
    _add_circle_segments(fp, 0.0, 0.0, 1.00, pcbnew.Dwgs_User, 0.08, 24)
    _add_polyline(fp, ((+0.95, -0.55), (+1.20, -0.80), (+0.70, -0.80)),
                  pcbnew.F_SilkS, 0.12)
    _set_text(fp, (0.0, -1.10), (0.0, +1.10))
    return _place(fp, x, y, rotation, bottom)


def make_esd441_dpy(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
) -> pcbnew.FOOTPRINT:
    """Build TI's DPY0002A X1SON land pattern for ESD441.

    The official recommended land pattern uses two 0.30 x 0.50 mm pads on
    0.70 mm centres.  Pin 1 is the protected IO/VBUS node and pin 2 is GND.
    """

    fp = _new_footprint(board, reference, value, "TI_DPY0002A_X1SON")
    _add_smd_pad(fp, "1", -0.35, 0.0, 0.30, 0.50,
                 pcbnew.PAD_SHAPE_ROUNDRECT, 0.16)
    _add_smd_pad(fp, "2", +0.35, 0.0, 0.30, 0.50,
                 pcbnew.PAD_SHAPE_ROUNDRECT, 0.16)
    _add_rectangle(fp, -0.50, -0.30, +0.50, +0.30, pcbnew.F_Fab, 0.05)
    _add_rectangle(fp, -0.70, -0.50, +0.70, +0.50, pcbnew.F_CrtYd, 0.05)
    _add_circle_segments(fp, -0.50, -0.36, 0.16, pcbnew.F_SilkS, 0.05, 12)
    _set_text(fp, (0.0, -0.85), (0.0, +0.85))
    return _place(fp, x, y, rotation, bottom)


def make_wirepads(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    count: int,
    pitch: float = 1.27,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    pad_size: tuple[float, float] = (0.90, 1.80),
) -> pcbnew.FOOTPRINT:
    """Create 2+ centred hand-solder wire lands numbered left-to-right."""

    if count < 2:
        raise ValueError("wire-pad count must be at least two")
    fp = _new_footprint(board, reference, value,
                        f"WirePads_{count}_P{pitch:.2f}mm")
    start_x = -(count - 1) * pitch / 2.0
    for index in range(count):
        _add_smd_pad(fp, str(index + 1), start_x + index * pitch, 0.0,
                     pad_size[0], pad_size[1],
                     pcbnew.PAD_SHAPE_ROUNDRECT, 0.18)
    half_x = (count - 1) * pitch / 2.0 + pad_size[0] / 2.0
    _add_rectangle(fp, -half_x - 0.25, -pad_size[1] / 2.0 - 0.25,
                   +half_x + 0.25, +pad_size[1] / 2.0 + 0.25,
                   pcbnew.F_CrtYd, 0.05)
    _add_polyline(fp, ((start_x - 0.35, -1.20),
                       (start_x, -1.55), (start_x + 0.35, -1.20)),
                  pcbnew.F_SilkS, 0.12)
    _set_text(fp, (0.0, -1.90), (0.0, +1.90))
    return _place(fp, x, y, rotation, bottom)


def make_pogo_pad(
    board: pcbnew.BOARD,
    reference: str,
    value: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = True,
    *,
    pad_diameter: float = 1.00,
    courtyard_diameter: float = 1.30,
) -> pcbnew.FOOTPRINT:
    """Compact single-land factory pogo target with no silkscreen.

    The 1.00 mm copper target supports a spring probe while the 1.30 mm
    courtyard permits 1.50 mm pitch without false courtyard collisions.  It
    is excluded from the BOM and placement file because it is a PCB feature,
    not an assembled component.
    """

    fp = _new_footprint(board, reference, value, "PogoPad_D1.0mm")
    _mark_mechanical_only(fp)
    _add_smd_pad(fp, "1", 0.0, 0.0, pad_diameter, pad_diameter,
                 pcbnew.PAD_SHAPE_CIRCLE)
    _add_circle_segments(fp, 0.0, 0.0, courtyard_diameter,
                         pcbnew.F_CrtYd, 0.05, 24)
    _set_text(fp, (0.0, -1.10), (0.0, +1.10))
    return _place(fp, x, y, rotation, bottom)


def add_battery_envelope(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = True,
    *,
    length: float = 29.0,
    width: float = 15.5,
) -> pcbnew.FOOTPRINT:
    """Add the rear battery body/clearance only; use ``make_wirepads`` for BT1.

    This is a post-PCBA installed volume, not a reflow component courtyard.
    Its clearance outline therefore lives on Dwgs.User so intended pogo pads
    under the removable test-stage battery do not create false courtyard DRC.
    """

    fp = _new_footprint(board, reference, f"BATTERY_ENVELOPE_{length}x{width}",
                        "Mechanical_Battery_Envelope")
    _mark_mechanical_only(fp)
    _add_rectangle(fp, -length / 2.0, -width / 2.0,
                   +length / 2.0, +width / 2.0, pcbnew.F_Fab, 0.10)
    _add_rectangle(fp, -length / 2.0 - 0.25, -width / 2.0 - 0.25,
                   +length / 2.0 + 0.25, +width / 2.0 + 0.25,
                   pcbnew.Dwgs_User, 0.05)
    _set_text(fp, (0.0, -width / 2.0 - 0.80),
              (0.0, +width / 2.0 + 0.80))
    return _place(fp, x, y, rotation, bottom)


def add_motor_envelope(
    board: pcbnew.BOARD,
    reference: str,
    x: float,
    y: float,
    rotation: float = 0.0,
    bottom: bool = False,
    *,
    diameter: float = 10.0,
) -> pcbnew.FOOTPRINT:
    """Add the post-PCBA adhesive motor volume; use wire pads for M1."""

    fp = _new_footprint(board, reference, f"MOTOR_ENVELOPE_D{diameter}",
                        "Mechanical_CoinMotor_Envelope")
    _mark_mechanical_only(fp)
    _add_circle_segments(fp, 0.0, 0.0, diameter, pcbnew.F_Fab, 0.10, 40)
    _add_circle_segments(fp, 0.0, 0.0, diameter, pcbnew.Dwgs_User, 0.08, 40)
    _add_rectangle(fp, -diameter / 2.0 - 0.25, -diameter / 2.0 - 0.25,
                   +diameter / 2.0 + 0.25, +diameter / 2.0 + 0.25,
                   pcbnew.Dwgs_User, 0.05)
    _set_text(fp, (0.0, -diameter / 2.0 - 0.75),
              (0.0, +diameter / 2.0 + 0.75))
    return _place(fp, x, y, rotation, bottom)


def _pad_map(fp: pcbnew.FOOTPRINT) -> dict[str, list[pcbnew.PAD]]:
    result: dict[str, list[pcbnew.PAD]] = {}
    for pad in fp.Pads():
        result.setdefault(pad.GetNumber(), []).append(pad)
    return result


def _self_test(write_board: bool = False) -> None:
    """Instantiate every helper and check the critical pad invariants."""

    board = pcbnew.BOARD()
    usb = make_usb4500(board, "J1", "USB4500-03-1-A", 20.0, 20.0,
                       include_edge_cuts=False)
    mic = make_cmm3424(board, "MIC1", "CMM-3424DT-26165-TR", 40.0, 20.0)
    battery = make_battery_wire_termination(board, "BT1", 60.0, 25.0,
                                             bottom=True)
    motor = make_haptic_coin_motor(board, "M1", 85.0, 20.0)
    led = make_led(board, "LED1", "APHB1608LVBDSEKJ3C", 100.0, 20.0)
    esd = make_esd441_dpy(board, "D2", "ESD441DPYR", 105.0, 20.0)
    wires = make_wirepads(board, "BT2", "BATTERY_WIRES", 110.0, 20.0, 3)
    pogo = make_pogo_pad(board, "TP1", "TESTPAD", 118.0, 20.0)
    add_battery_envelope(board, "MH_BAT", 130.0, 25.0)
    add_motor_envelope(board, "MH_MOTOR", 155.0, 20.0)
    make_button_access_target(board, "MH1", 170.0, 20.0)
    make_indicator_lightpipe_target(board, "MH2", 180.0, 20.0)

    usb_pads = _pad_map(usb)
    assert set(usb_pads) == ({str(i) for i in range(1, 13)} |
                             {"S1", "S2", "S3", "S4"})
    assert all(len(usb_pads[name]) == 1 for name in ("S1", "S2", "S3", "S4"))
    assert sum(len(items) for items in usb_pads.values()) == 16
    assert set(_pad_map(mic)) == {str(i) for i in range(1, 9)}
    assert set(_pad_map(battery)) == {"1", "2", "3"}
    assert set(_pad_map(motor)) == {"1", "2"}
    assert set(_pad_map(led)) == {"1", "2", "3", "4"}
    assert set(_pad_map(esd)) == {"1", "2"}
    assert set(_pad_map(wires)) == {"1", "2", "3"}
    assert set(_pad_map(pogo)) == {"1"}
    assert battery.IsFlipped()

    # A previous KiCad-7 API misuse wrote every generated graphic as a
    # zero-length segment even though it looked populated before saving.
    # Check local geometry, which is what KiCad serializes in a footprint.
    graphics_checked = 0
    required_layers = {
        pcbnew.F_Fab,
        pcbnew.F_CrtYd,
        pcbnew.F_SilkS,
        pcbnew.Dwgs_User,
    }
    layers_seen: set[int] = set()
    for footprint in board.GetFootprints():
        for graphic in footprint.GraphicalItems():
            if graphic.GetShape() != pcbnew.SHAPE_T_SEGMENT:
                continue
            graphics_checked += 1
            assert graphic.GetStart0() != graphic.GetEnd0(), (
                f"zero-length graphic in {footprint.GetReference()} on "
                f"layer {graphic.GetLayerName()}"
            )
            layers_seen.add(graphic.GetLayer())
    assert graphics_checked > 0
    assert required_layers <= layers_seen, (
        "self-test did not exercise all required custom-graphics layers"
    )

    if write_board:
        output = Path(__file__).with_name("footprint_builders_r0b_selftest.kicad_pcb")
        pcbnew.SaveBoard(str(output), board)
        print(f"Wrote {output}")
    print(
        "R0B footprint self-test passed: USB=16 pads, MIC=8, BAT=3, "
        f"MOTOR=2, GRAPHICS={graphics_checked} nonzero segments"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-board", action="store_true",
                        help="also write a visual KiCad self-test board")
    args = parser.parse_args()
    _self_test(write_board=args.write_board)
