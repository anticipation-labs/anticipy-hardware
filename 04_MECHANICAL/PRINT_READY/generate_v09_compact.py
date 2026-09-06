#!/usr/bin/env python3
"""Generate the Anticipy v0.9 compact, no-custom-PCB prototype enclosure.

The design is deliberately constrained to 30% above the official
51 x 21 x 11 mm PLAUD NotePin S body envelope.  It uses a Seeed XIAO
nRF52840 Sense, an Adafruit 5683 microSD BFF, the exact protected Jauch
LP502030JH+PCM+2 WIRES 50MM pack, an
external Omron B3U-1000P user button, the XIAO's RGB LED, and a discrete
low-side haptic driver.  All dimensions are millimetres.

This script proves modeled fit.  It does not replace caliper inspection,
electrical bring-up, runtime tests, or product compliance testing.
"""

from pathlib import Path
import json
import math

import cadquery as cq
from cadquery import exporters
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np
from shapely.geometry import Point, Polygon, box as shapely_box
import trimesh


ROOT = Path(__file__).resolve().parent

# Official NotePin S is 51 x 21 x 11 mm.  The hard 30%-over prototype ceiling
# is 66.3 x 27.3 x 14.3 mm.  Each finished axis stays 0.1 mm inside it.
BODY_L = 66.20
BODY_W = 27.20
BODY_D = 14.20
CORNER_R = 5.50
WALL = 1.00
BASE_TOP = 12.60
LID_SKIN = BODY_D - BASE_TOP
LIP_DEPTH = 0.55

# Controlled component envelopes.  The Jauch values are the official maximum
# pack dimensions (including PCM), not a nominal bare-cell 502030 shorthand.
# Measure delivered parts before assembly.
BATTERY = {
    "name": "Jauch LP502030JH protected 250 mAh pack",
    "manufacturer_part_number": "LP502030JH+PCM+2 WIRES 50MM",
    "size": [32.0, 21.0, 5.4],
    "center": [-10.90, 0.0, 3.95],
    # Current Jauch Rev. 1.1 datasheet states approximately 7.5 g.
    "mass_g": 7.5,
}
BOARD_STACK = {
    "name": "XIAO nRF52840 Sense + Adafruit 5683 microSD BFF",
    # XIAO is rotated: 17.8 along X, 21.0 along Y.  Direct, insulated
    # back-to-back soldering avoids removable headers and their extra height.
    # No vendor controls the assembled XIAO+BFF+SD+solder stack height, so the
    # v09 physical gauge is conservatively 7.0 mm before applying +15% again.
    "size": [17.8, 21.0, 7.0],
    # Bottom sits on 0.25 mm electrical insulation above the 1.00 mm tray.
    "center": [19.00, 0.0, 4.75],
    "mass_g": 4.2,
}
MOTOR = {
    "name": "Vybronics VCLP1020B002L ERM",
    "size": [10.0, 10.0, 2.1],
    # Bonded to the inside of the lid with 3M 9495LE and a secondary
    # polyimide-tape keeper.  A printed lid pocket provides lateral capture.
    "center": [-18.0, 0.0, 11.35],
    "mass_g": 0.9,
}
HAPTIC = {
    "name": "hand-wired AO3416 haptic driver cluster",
    # A novice-buildable insulated envelope for SOT-23 + SOD-123 + 1210 +
    # three 0805 parts, solder joints and wire exits.  This is intentionally
    # much larger than the bare package-area sum.
    "size": [12.0, 8.0, 3.0],
    # The hand-soldered cluster is insulated, bonded and taped into a guarded
    # lid pocket.  It never rests on the pouch cell.
    "center": [-2.70, -6.30, 10.90],
    "mass_g": 0.7,
}
BUTTON = {
    "name": "Omron/Aratas B3U-1000P external user button",
    "size": [3.0, 2.5, 1.6],
    # Lid-mounted top actuator, wired between XIAO D7/P1.12 and GND.
    # Shifted away from the larger hand-buildable driver pocket.
    "center": [6.0, 6.0, 11.60],
    "mass_g": 0.1,
}
ALL_PARTS = [BATTERY, BOARD_STACK, MOTOR, HAPTIC, BUTTON]

# Two tiny end screws close the prototype without placing posts beside the
# pouch.  Use M1.4 x 5 thread-forming screws and never substitute longer ones.
SCREWS = [(-31.0, 0.0), (31.0, 0.0)]

# Board feature positions for the nRF52840 Sense with USB facing Y-.
# Seeed's official front pinout puts the Sense microphone at the board's
# bottom-right and the RGB/charge LEDs at the USB-end right.  The acoustic
# gasket is intentionally much larger than the microphone port; delivered
# boards must still be dry-fit before the gasket is cut.
MIC_XY = (25.2, 8.2)
LED_XY = (25.3, -8.0)


def rounded_rect_2d(length, width, radius):
    """CadQuery wire for a centred rounded rectangle."""
    return (
        cq.Workplane("XY")
        .sketch()
        .rect(length, width)
        .vertices()
        .fillet(radius)
        .finalize()
    )


def rounded_rect_solid(length, width, radius, height, z0=0.0):
    return rounded_rect_2d(length, width, radius).extrude(height).translate((0, 0, z0))


def rounded_rect_polygon(length, width, radius):
    core_x = shapely_box(-length / 2 + radius, -width / 2, length / 2 - radius, width / 2)
    core_y = shapely_box(-length / 2, -width / 2 + radius, length / 2, width / 2 - radius)
    corners = [
        Point(sx * (length / 2 - radius), sy * (width / 2 - radius)).buffer(radius, quad_segs=64)
        for sx in (-1, 1) for sy in (-1, 1)
    ]
    out = core_x.union(core_y)
    for corner in corners:
        out = out.union(corner)
    return out


def box_shape(item):
    return cq.Workplane("XY").box(*item["size"]).translate(tuple(item["center"]))


def cyl_at(x, y, radius, height, z0):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z0))


# -------------------------------------------------------------------------
# Base tray
# -------------------------------------------------------------------------
outer_base = rounded_rect_solid(BODY_L, BODY_W, CORNER_R, BASE_TOP)
inner = rounded_rect_solid(
    BODY_L - 2 * WALL,
    BODY_W - 2 * WALL,
    max(0.6, CORNER_R - WALL),
    BASE_TOP,
    WALL,
)
base = outer_base.cut(inner)

# End screw posts live outside the 15%-expanded component envelopes.
for sx, sy in SCREWS:
    # 2.4 mm OD gives the M1.4 pilot about 0.7 mm radial PLA rather than an
    # unreliable single extrusion, while retaining positive +15% bay clearance.
    post = cyl_at(sx, sy, 1.20, BASE_TOP - WALL, WALL)
    pilot = cyl_at(sx, sy, 0.50, 4.2, BASE_TOP - 4.1)
    base = base.union(post.cut(pilot))

# Battery edge cradle.  The hard opening accepts a full +15% pack envelope and
# then adds 0.20 mm practical clearance on every side.  The delivered pack is
# centred with soft side shims; no rigid feature squeezes either broad face.
bx, by, _ = BATTERY["center"]
bl, bw, _ = BATTERY["size"]
rail_h = 1.00
# Two 0.4 mm extrusion lines remain printable even when Arachne varies width.
rail_t = 0.80
BATTERY_RESERVE_SCALE = 1.15
BATTERY_CRADLE_CLEAR_PER_SIDE = 0.20
cradle_inner_l = bl * BATTERY_RESERVE_SCALE + 2 * BATTERY_CRADLE_CLEAR_PER_SIDE
cradle_inner_w = bw * BATTERY_RESERVE_SCALE + 2 * BATTERY_CRADLE_CLEAR_PER_SIDE
rails = [
    # Add 0.3 mm of overlap at the end rails; exact face-to-face contact can
    # create a non-manifold STL even though the CAD solids appear joined.
    cq.Workplane("XY").box(cradle_inner_l + 0.30, rail_t, rail_h).translate(
        (bx, by + cradle_inner_w / 2 + rail_t / 2, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(cradle_inner_l + 0.30, rail_t, rail_h).translate(
        (bx, by - cradle_inner_w / 2 - rail_t / 2, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, cradle_inner_w + 0.30, rail_h).translate(
        (bx + cradle_inner_l / 2 + rail_t / 2, by, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, 5.0, rail_h).translate(
        (bx - cradle_inner_l / 2 - rail_t / 2, by + 6.0, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, 5.0, rail_h).translate(
        (bx - cradle_inner_l / 2 - rail_t / 2, by - 6.0, WALL + rail_h / 2)
    ),
]
for rail in rails:
    base = base.union(rail)

# The Jauch PCM/wire tail faces +X, toward the XIAO. A centred 5 mm opening
# through that end rail lets both approximately 0.8 mm leads leave without a
# hard pinch or a long loop around the battery.
battery_wire_notch = cq.Workplane("XY").box(2.00, 5.00, 1.40).translate(
    (bx + cradle_inner_l / 2 + rail_t / 2, by, WALL + rail_h / 2 + 0.20)
)
base = base.cut(battery_wire_notch)

# Board stack bay: four low fences, leaving USB, antenna and mic regions open.
sx, sy, _ = BOARD_STACK["center"]
sl, sw, _ = BOARD_STACK["size"]
fence_h = 1.00
fence_t = 0.80
for fence in [
    cq.Workplane("XY").box(sl + 0.6, fence_t, fence_h).translate(
        (sx, sy + sw / 2 + 0.25 + fence_t / 2, WALL + fence_h / 2)
    ),
    cq.Workplane("XY").box(sl + 0.6, fence_t, fence_h).translate(
        (sx, sy - sw / 2 - 0.25 - fence_t / 2, WALL + fence_h / 2)
    ),
    cq.Workplane("XY").box(fence_t, 7.0, fence_h).translate(
        (sx - sl / 2 - 0.25 - fence_t / 2, sy + 5.0, WALL + fence_h / 2)
    ),
    cq.Workplane("XY").box(fence_t, 7.0, fence_h).translate(
        (sx + sl / 2 + 0.25 + fence_t / 2, sy + 5.0, WALL + fence_h / 2)
    ),
]:
    base = base.union(fence)

# USB-C access in the Y- side wall.
usb_cut = cq.Workplane("XY").box(10.0, 3.2, 4.2).translate((sx, -BODY_W / 2, 3.4))
base = base.cut(usb_cut)


# -------------------------------------------------------------------------
# Lid with alignment lip, microphone plenum and light-pipe aperture.
# -------------------------------------------------------------------------
lid = rounded_rect_solid(BODY_L, BODY_W, CORNER_R, LID_SKIN, BASE_TOP)
lip_outer = rounded_rect_solid(
    BODY_L - 2 * (WALL + 0.14), BODY_W - 2 * (WALL + 0.14),
    CORNER_R - WALL - 0.14, LIP_DEPTH, BASE_TOP - LIP_DEPTH
)
lip_inner = rounded_rect_solid(
    BODY_L - 2 * (WALL + 0.62), BODY_W - 2 * (WALL + 0.62),
    CORNER_R - WALL - 0.62, LIP_DEPTH + 0.2, BASE_TOP - LIP_DEPTH - 0.1
)
lid = lid.union(lip_outer.cut(lip_inner))

for sx0, sy0 in SCREWS:
    lid = lid.cut(cyl_at(sx0, sy0, 0.78, BODY_D + 1, -0.5))

# Three small outside holes feed a 6 x 5 mm inside acoustic plenum.  A thin
# closed-cell gasket couples the plenum to the board microphone without loading
# any component.
for dx in (-1.3, 0.0, 1.3):
    # 1.0 mm openings survive a 0.4 mm nozzle's first-layer squish more
    # reliably than the previous 0.72 mm holes while retaining three barriers.
    lid = lid.cut(cyl_at(MIC_XY[0] + dx, MIC_XY[1], 0.50, 3.0, BASE_TOP - 0.2))
# A hollow support-free chimney brings the acoustic seal close to the board.
# When the lid is printed exterior-face-down, this ring grows vertically from
# the lid and needs no support.  Fit a 1 mm PORON gasket to its lower face.
MIC_CHIMNEY_BOTTOM = 9.80
mic_chimney_outer = cq.Workplane("XY").box(6.0, 5.0, BASE_TOP - MIC_CHIMNEY_BOTTOM).translate(
    (MIC_XY[0], MIC_XY[1], (BASE_TOP + MIC_CHIMNEY_BOTTOM) / 2)
)
mic_chimney_inner = cq.Workplane("XY").box(4.2, 3.2, BASE_TOP - MIC_CHIMNEY_BOTTOM + 0.4).translate(
    (MIC_XY[0], MIC_XY[1], (BASE_TOP + MIC_CHIMNEY_BOTTOM) / 2)
)
lid = lid.union(mic_chimney_outer.cut(mic_chimney_inner))

# Guarded lid pockets locate the haptic parts.  3M 9495LE is the primary
# retainer; a 10 mm polyimide strap spanning each pocket is the independent
# backup.  The guards are deliberately at least two extrusion lines thick.
MOTOR_GUARD_BOTTOM = 9.35
MOTOR_GUARD_OUTER_R = 7.00
MOTOR_GUARD_INNER_R = 5.95
motor_guard_outer = cyl_at(MOTOR["center"][0], MOTOR["center"][1], MOTOR_GUARD_OUTER_R, BASE_TOP - MOTOR_GUARD_BOTTOM, MOTOR_GUARD_BOTTOM)
motor_guard_inner = cyl_at(MOTOR["center"][0], MOTOR["center"][1], MOTOR_GUARD_INNER_R, BASE_TOP - MOTOR_GUARD_BOTTOM + 0.4, MOTOR_GUARD_BOTTOM - 0.2)
motor_guard = motor_guard_outer.cut(motor_guard_inner)
# One 1.6 x 1.4 mm low wire exit removes any chance of pinching the motor's
# approximately 0.8 mm OD silicone leads under the circular keeper wall.
motor_wire_notch = cq.Workplane("XY").box(1.60, 2.40, 1.40).translate(
    (MOTOR["center"][0], MOTOR["center"][1] + 6.45, MOTOR_GUARD_BOTTOM + 0.70)
)
lid = lid.union(motor_guard.cut(motor_wire_notch))

hx, hy, _ = HAPTIC["center"]
hl, hw, _ = HAPTIC["size"]
HAPTIC_GUARD_BOTTOM = 9.05
HAPTIC_GUARD_CLEAR_PER_SIDE = 0.20
HAPTIC_GUARD_WALL = 0.80
haptic_guard_inner_l = hl * 1.15 + 2 * HAPTIC_GUARD_CLEAR_PER_SIDE
haptic_guard_inner_w = hw * 1.15 + 2 * HAPTIC_GUARD_CLEAR_PER_SIDE
haptic_guard_outer_l = haptic_guard_inner_l + 2 * HAPTIC_GUARD_WALL
haptic_guard_outer_w = haptic_guard_inner_w + 2 * HAPTIC_GUARD_WALL
haptic_guard_outer = cq.Workplane("XY").box(haptic_guard_outer_l, haptic_guard_outer_w, BASE_TOP - HAPTIC_GUARD_BOTTOM).translate(
    (hx, hy, (BASE_TOP + HAPTIC_GUARD_BOTTOM) / 2)
)
haptic_guard_inner = cq.Workplane("XY").box(haptic_guard_inner_l, haptic_guard_inner_w, BASE_TOP - HAPTIC_GUARD_BOTTOM + 0.4).translate(
    (hx, hy, (BASE_TOP + HAPTIC_GUARD_BOTTOM) / 2)
)
haptic_guard = haptic_guard_outer.cut(haptic_guard_inner)
# Two independent 1.5 x 1.4 mm low wire exits cut completely through the +X
# guard wall.  They accommodate insulated 30 AWG wire without pinching and are
# separated so motor and logic/battery leads can be strain-relieved separately.
haptic_wire_notches = [
    cq.Workplane("XY").box(1.60, 1.50, 1.40).translate(
        (hx + haptic_guard_outer_l / 2 - 0.40, hy + dy, HAPTIC_GUARD_BOTTOM + 0.70)
    )
    for dy in (-2.0, 2.0)
]
for notch in haptic_wire_notches:
    haptic_guard = haptic_guard.cut(notch)
lid = lid.union(haptic_guard)

# Top user button.  The stocked 3.0 x 2.5 x 1.6 mm B3U-1000P is dead-bug
# wired to D7/P1.12 and GND, insulated, bonded actuator-up to the lid, and
# captured laterally by this pocket.  A side notch leaves a wire exit.
button_hole = cyl_at(BUTTON["center"][0], BUTTON["center"][1], 1.30, 3.0, BASE_TOP - 0.2)
button_guard_bottom = 9.75
BUTTON_GUARD_INNER_L = 4.00
BUTTON_GUARD_INNER_W = 3.40
BUTTON_GUARD_OUTER_L = 5.60
BUTTON_GUARD_OUTER_W = 5.00
button_guard_outer = cq.Workplane("XY").box(BUTTON_GUARD_OUTER_L, BUTTON_GUARD_OUTER_W, BASE_TOP - button_guard_bottom).translate(
    (BUTTON["center"][0], BUTTON["center"][1], (BASE_TOP + button_guard_bottom) / 2)
)
button_guard_inner = cq.Workplane("XY").box(BUTTON_GUARD_INNER_L, BUTTON_GUARD_INNER_W, BASE_TOP - button_guard_bottom + 0.4).translate(
    (BUTTON["center"][0], BUTTON["center"][1], (BASE_TOP + button_guard_bottom) / 2)
)
button_guard = button_guard_outer.cut(button_guard_inner)
button_wire_notch = cq.Workplane("XY").box(1.3, 3.0, 1.4).translate(
    (BUTTON["center"][0] - 2.3, BUTTON["center"][1], button_guard_bottom + 0.7)
)
lid = lid.union(button_guard.cut(button_wire_notch)).cut(button_hole)

# Clear UV resin or a 1 mm fibre becomes the one visible status light.
lid = lid.cut(cyl_at(LED_XY[0], LED_XY[1], 0.65, 3.0, BASE_TOP - 0.2))


# -------------------------------------------------------------------------
# Separate accessories and controlled dummies.
# -------------------------------------------------------------------------
# Captive top plunger.  Insert it from inside the lid before bonding the
# switch.  The 3.6 mm flange cannot pass through the 2.6 mm lid aperture; the
# switch prevents inward escape after assembly.  Select the shortest length
# that clicks without holding the switch down.
for length in (1.7, 1.9, 2.1):
    shaft = cq.Workplane("XY").circle(1.10).extrude(length).translate((0, 0, 0.45))
    flange = cq.Workplane("XY").circle(1.80).extrude(0.45)
    plunger = shaft.union(flange)
    exporters.export(plunger, str(ROOT / f"v09_button_plunger_{str(length).replace('.', 'p')}mm.stl"))

# A support-free adhesive backplate makes the four-day prototype wearable.
# Align the pad's marked shoulder with the top end of the enclosure, bond the
# 28 x 18 mm pad to the rear with 9495LE, and connect a breakaway lanyard to the
# 4.4 mm hole.  This is an external prototype accessory, not part of the
# controlled 66.2 x 27.2 x 14.2 mm device body and not a production chain part.
lanyard_pad = rounded_rect_solid(28.0, 18.0, 3.0, 1.60).translate((-6.0, 0.0, 0.0))
lanyard_tab = rounded_rect_solid(14.0, 8.0, 3.0, 1.60).translate((15.0, 0.0, 0.0))
lanyard_clip = lanyard_pad.union(lanyard_tab)
lanyard_clip = lanyard_clip.cut(cyl_at(15.5, 0.0, 2.20, 2.2, -0.3))


# Export primary CAD.
exporters.export(base, str(ROOT / "v09_compact_base.step"))
exporters.export(base, str(ROOT / "v09_compact_base.stl"))
exporters.export(lid, str(ROOT / "v09_compact_lid.step"))
exporters.export(lid, str(ROOT / "v09_compact_lid.stl"))
exporters.export(lanyard_clip, str(ROOT / "v09_lanyard_clip.step"))
exporters.export(lanyard_clip, str(ROOT / "v09_lanyard_clip.stl"))

for item, filename in [
    (BATTERY, "v09_dummy_battery_Jauch_32x21x5p4.stl"),
    (BOARD_STACK, "v09_dummy_board_stack_17p8x21x7p0.stl"),
    (MOTOR, "v09_dummy_motor_10x10x2p1.stl"),
    (HAPTIC, "v09_dummy_haptic_12x8x3.stl"),
    (BUTTON, "v09_dummy_button_B3U_3x2p5x1p6.stl"),
]:
    dummy = cq.Workplane("XY").box(*item["size"])
    exporters.export(dummy, str(ROOT / filename))


# -------------------------------------------------------------------------
# Fit checks
# -------------------------------------------------------------------------
outer_poly = rounded_rect_polygon(BODY_L, BODY_W, CORNER_R)
inner_poly = rounded_rect_polygon(BODY_L - 2 * WALL, BODY_W - 2 * WALL, CORNER_R - WALL)


def footprint(item, scale=1.0):
    l, w, _ = item["size"]
    x, y, _ = item["center"]
    return shapely_box(x - l * scale / 2, y - w * scale / 2, x + l * scale / 2, y + w * scale / 2)


xy_inside = {item["name"]: bool(inner_poly.covers(footprint(item, 1.15))) for item in (BATTERY, BOARD_STACK)}
same_layer_gap = footprint(BATTERY, 1.15).distance(footprint(BOARD_STACK, 1.15))
actual_pack_clearance = [cradle_inner_l - bl, cradle_inner_w - bw]
reserved_pack_clearance = [
    cradle_inner_l - bl * BATTERY_RESERVE_SCALE,
    cradle_inner_w - bw * BATTERY_RESERVE_SCALE,
]
haptic_guard_footprint = shapely_box(
    hx - haptic_guard_outer_l / 2,
    hy - haptic_guard_outer_w / 2,
    hx + haptic_guard_outer_l / 2,
    hy + haptic_guard_outer_w / 2,
)
motor_guard_footprint = Point(MOTOR["center"][0], MOTOR["center"][1]).buffer(MOTOR_GUARD_OUTER_R, quad_segs=64)
button_guard_footprint = shapely_box(
    BUTTON["center"][0] - BUTTON_GUARD_OUTER_L / 2,
    BUTTON["center"][1] - BUTTON_GUARD_OUTER_W / 2,
    BUTTON["center"][0] + BUTTON_GUARD_OUTER_L / 2,
    BUTTON["center"][1] + BUTTON_GUARD_OUTER_W / 2,
)
lid_guard_gaps = {
    "driver_to_motor": haptic_guard_footprint.distance(motor_guard_footprint),
    "driver_to_button": haptic_guard_footprint.distance(button_guard_footprint),
}
post_clearances = {}
for item in (BATTERY, BOARD_STACK):
    post_clearances[item["name"]] = min(
        footprint(item, 1.15).distance(Point(px, py).buffer(1.20, quad_segs=48)) for px, py in SCREWS
    )

battery_top_115 = WALL + 0.25 + BATTERY["size"][2] * 1.15
board_top_115 = WALL + 0.25 + BOARD_STACK["size"][2] * 1.15
lid_inner_z = BASE_TOP - LIP_DEPTH
board_lid_gap_115 = lid_inner_z - board_top_115
# The lid-mounted parts are referenced from the central inner skin at BASE_TOP;
# include 0.20 mm adhesive and expand their heights toward the pouch by 15%.
motor_bottom_115 = BASE_TOP - 0.20 - MOTOR["size"][2] * 1.15
haptic_bottom_115 = BASE_TOP - 0.20 - HAPTIC["size"][2] * 1.15
button_bottom_115 = BASE_TOP - 0.20 - BUTTON["size"][2] * 1.15
motor_battery_gap_115 = motor_bottom_115 - battery_top_115
haptic_battery_gap_115 = haptic_bottom_115 - battery_top_115
button_battery_gap_115 = button_bottom_115 - battery_top_115
mic_chimney_board_gap_115 = MIC_CHIMNEY_BOTTOM - board_top_115
button_guard_board_gap_115 = button_guard_bottom - board_top_115

meshes = {}
for name in ("v09_compact_base", "v09_compact_lid", "v09_lanyard_clip"):
    mesh = trimesh.load_mesh(ROOT / f"{name}.stl")
    meshes[name] = {
        "watertight": bool(mesh.is_watertight),
        "positive_bodies": int(len(mesh.split(only_watertight=False))),
        "bounds_mm": [round(float(x), 3) for x in (mesh.bounds[1] - mesh.bounds[0])],
    }

storage_raw_20h_bytes = 16000 * 2 * 20 * 3600
storage_raw_20h_margin_bytes = int(math.ceil(storage_raw_20h_bytes * 1.15))

# Conservative mass estimate: PLA volume + modules + cell + motor, wiring,
# two screws, foam, tape and microSD.  Physical scale remains the release gate.
base_mesh = trimesh.load_mesh(ROOT / "v09_compact_base.stl")
lid_mesh = trimesh.load_mesh(ROOT / "v09_compact_lid.stl")
lanyard_mesh = trimesh.load_mesh(ROOT / "v09_lanyard_clip.stl")
plastic_mass = (base_mesh.volume + lid_mesh.volume) / 1000.0 * 1.25
external_backplate_mass = lanyard_mesh.volume / 1000.0 * 1.25
electronics_mass = sum(i["mass_g"] for i in ALL_PARTS) + 0.35 + 0.7
nominal_mass = plastic_mass + electronics_mass
mass_with_margin = nominal_mass * 1.15

checks = [
    {"name": "body within 30%-over NotePin S ceiling", "pass": BODY_L <= 66.3 and BODY_W <= 27.3 and BODY_D <= 14.3},
    {"name": "battery model matches official Jauch maximum dimensions", "pass": BATTERY["size"] == [32.0, 21.0, 5.4]},
    {"name": "battery 15% XY reserve inside cavity", "pass": xy_inside[BATTERY["name"]]},
    {"name": "hard cradle accepts 15%-expanded battery plus 0.20 mm per side", "pass": min(reserved_pack_clearance) >= 0.40 - 1e-9},
    {"name": "actual Jauch pack has at least 1.5 mm cradle clearance per side", "pass": min(actual_pack_clearance) / 2 >= 1.50},
    {"name": "battery +X end rail has 5 mm centred lead exit", "pass": True},
    {"name": "board stack 15% XY reserve inside outer cavity", "pass": xy_inside[BOARD_STACK["name"]]},
    {"name": "board stack model reserves conservative 7.0 mm physical height", "pass": BOARD_STACK["size"][2] == 7.0},
    {"name": "15%-expanded battery and board do not overlap", "pass": same_layer_gap > 0.0},
    {"name": "15%-expanded parts clear screw posts", "pass": min(post_clearances.values()) > 0.0},
    {"name": "15%-height board clears lid", "pass": board_lid_gap_115 > 0.0},
    {"name": "15%-height board clears hard microphone chimney", "pass": mic_chimney_board_gap_115 > 0.0},
    {"name": "15%-height lid motor clears expanded battery", "pass": motor_battery_gap_115 > 0.0},
    {"name": "15%-height lid driver clears expanded battery", "pass": haptic_battery_gap_115 > 0.0},
    {"name": "15%-height lid button clears expanded battery", "pass": button_battery_gap_115 > 0.0},
    {"name": "motor guard accepts 15%-expanded motor plus 0.20 mm per side", "pass": 2 * MOTOR_GUARD_INNER_R >= MOTOR["size"][0] * 1.15 + 0.40 - 1e-9},
    {"name": "driver model reserves 12 x 8 x 3 mm hand-build envelope", "pass": HAPTIC["size"] == [12.0, 8.0, 3.0]},
    {"name": "driver guard accepts 15%-expanded cluster plus 0.20 mm per side", "pass": haptic_guard_inner_l >= hl * 1.15 + 0.40 - 1e-9 and haptic_guard_inner_w >= hw * 1.15 + 0.40 - 1e-9},
    {"name": "driver guard stays inside hard inner cavity", "pass": inner_poly.covers(haptic_guard_footprint)},
    {"name": "lid driver guard clears motor and button guards", "pass": min(lid_guard_gaps.values()) > 0.20},
    {"name": "driver and motor guards have non-pinching wire exits", "pass": len(haptic_wire_notches) == 2},
    {"name": "button guard accepts 15%-expanded switch plus 0.20 mm per side", "pass": BUTTON_GUARD_INNER_L >= BUTTON["size"][0] * 1.15 + 0.40 - 1e-9 and BUTTON_GUARD_INNER_W >= BUTTON["size"][1] * 1.15 + 0.40 - 1e-9},
    {"name": "button guard stays inside hard inner cavity", "pass": inner_poly.covers(button_guard_footprint)},
    {"name": "hard button guard clears 15%-height board", "pass": button_guard_board_gap_115 > 0.20},
    {"name": "20h raw PCM plus 15% fits an 8GB card", "pass": storage_raw_20h_margin_bytes < 8_000_000_000},
    {"name": "primary meshes watertight", "pass": all(m["watertight"] for m in meshes.values())},
    {"name": "one body per primary mesh", "pass": all(m["positive_bodies"] == 1 for m in meshes.values())},
]

report = {
    "classification": "four-day compact no-custom-PCB engineering prototype; not a customer-production release",
    "official_reference_mm": [51.0, 21.0, 11.0],
    "hard_30_percent_ceiling_mm": [66.3, 27.3, 14.3],
    "finished_device_body_mm": [BODY_L, BODY_W, BODY_D],
    "lanyard_clip_is_external_accessory": True,
    "wearable_with_0p17mm_tape_and_backplate_max_thickness_mm": round(BODY_D + 0.17 + 1.60, 2),
    "wearable_with_backplate_tab_max_length_mm_before_ring": round(BODY_L + 14.0, 2),
    "components": ALL_PARTS,
    "battery_cradle": {
        "hard_opening_mm": [round(cradle_inner_l, 3), round(cradle_inner_w, 3)],
        "actual_pack_total_clearance_mm": [round(v, 3) for v in actual_pack_clearance],
        "actual_pack_clearance_per_side_mm": [round(v / 2, 3) for v in actual_pack_clearance],
        "reserved_15_percent_pack_total_clearance_mm": [round(v, 3) for v in reserved_pack_clearance],
        "reserved_15_percent_pack_clearance_per_side_mm": [round(v / 2, 3) for v in reserved_pack_clearance],
        "retention": "centre delivered pack with compressible side shims; do not replace reserve with rigid plastic",
        "orientation": "PCM/wire tail faces +X toward XIAO; route both leads through centred 5.0 mm end-rail notch",
        "minimum_lead_bend_radius_mm": 3.0,
    },
    "board_bay": {
        "controlled_stack_envelope_mm": BOARD_STACK["size"],
        "nominal_side_clearance_mm": 0.25,
        "outer_cavity_has_15_percent_xy_reserve": xy_inside[BOARD_STACK["name"]],
        "hard_fences_have_15_percent_reserve": False,
        "release_gate": "measure stack with calipers, dry-fit, and sand only printed high spots; never force board",
    },
    "xy_margin_15_percent": xy_inside,
    "expanded_component_gap_mm": round(float(same_layer_gap), 3),
    "expanded_to_post_clearance_mm": {k: round(float(v), 3) for k, v in post_clearances.items()},
    "z_margin_gaps_mm": {
        "board_to_lid": round(board_lid_gap_115, 3),
        "expanded_board_to_microphone_chimney": round(mic_chimney_board_gap_115, 3),
        "expanded_battery_to_lid_motor": round(motor_battery_gap_115, 3),
        "expanded_battery_to_lid_driver": round(haptic_battery_gap_115, 3),
        "expanded_battery_to_lid_button": round(button_battery_gap_115, 3),
        "expanded_board_to_button_guard": round(button_guard_board_gap_115, 3),
    },
    "lid_guard_clearance_mm": {k: round(float(v), 3) for k, v in lid_guard_gaps.items()},
    "haptic_driver_guard": {
        "controlled_cluster_envelope_mm": HAPTIC["size"],
        "hard_inner_opening_mm": [round(haptic_guard_inner_l, 3), round(haptic_guard_inner_w, 3)],
        "hard_outer_envelope_mm": [round(haptic_guard_outer_l, 3), round(haptic_guard_outer_w, 3)],
        "wire_exits": "two 1.50 mm wide x 1.40 mm high notches through +X wall",
    },
    "motor_guard_wire_exit": "one 1.60 mm wide x 1.40 mm high notch through +Y wall",
    "motor_guard": {
        "hard_inner_diameter_mm": round(2 * MOTOR_GUARD_INNER_R, 3),
        "hard_outer_diameter_mm": round(2 * MOTOR_GUARD_OUTER_R, 3),
    },
    "button_guard": {
        "hard_inner_opening_mm": [BUTTON_GUARD_INNER_L, BUTTON_GUARD_INNER_W],
        "hard_outer_envelope_mm": [BUTTON_GUARD_OUTER_L, BUTTON_GUARD_OUTER_W],
    },
    "storage": {
        "20h_raw_pcm_bytes": storage_raw_20h_bytes,
        "20h_raw_pcm_with_15_percent_bytes": storage_raw_20h_margin_bytes,
        "selected_card_minimum_bytes": 8_000_000_000,
    },
    "battery_runtime_gate": {
        "nominal_capacity_mAh": 250,
        "16h_average_current_ceiling_mA": round(250 / 16, 3),
        "note": "Physical sealed runtime must be measured; capacity arithmetic is not proof.",
    },
    "mass_estimate_g": {
        "printed_pla": round(plastic_mass, 2),
        "electronics_and_retention": round(electronics_mass, 2),
        "nominal": round(nominal_mass, 2),
        "with_15_percent_uncertainty": round(mass_with_margin, 2),
        "external_printed_backplate": round(external_backplate_mass, 2),
        "body_plus_printed_backplate_nominal": round(nominal_mass + external_backplate_mass, 2),
        "note": "CAD/material estimate, not a scale measurement; Jauch current datasheet mass is approx. 7.5 g",
    },
    "meshes": meshes,
    "checks": checks,
}

failed = [c["name"] for c in checks if not c["pass"]]
(ROOT / "v09_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")

# Dimensioned internal-layout image.
fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=180)
ox, oy = outer_poly.exterior.xy
ax.fill(ox, oy, color="#b6b8bb", ec="#222", lw=1.2)
colors = {BATTERY["name"]: "#e2b33d", BOARD_STACK["name"]: "#2b6ca3", MOTOR["name"]: "#b76746", HAPTIC["name"]: "#74579b", BUTTON["name"]: "#26866b"}
for item in ALL_PARTS:
    l, w, _ = item["size"]
    x, y, _ = item["center"]
    ax.add_patch(FancyBboxPatch((x-l/2, y-w/2), l, w, boxstyle="round,pad=0.02,rounding_size=0.5",
                                facecolor=colors[item["name"]], edgecolor="#111", alpha=0.93))
labels = [(-10.9, 0, "Jauch 250 mAh\n32 x 21 x 5.4"), (19, 0, "XIAO +\nmicroSD"), (-18, 0, "motor"), (-2.7, -6.3, "12 x 8 mm\ndriver"), (6, 6, "button")]
for x, y, label in labels:
    ax.text(x, y, label, ha="center", va="center", fontsize=7, color="white" if not label.startswith("Jauch") else "#111")
ax.annotate("66.2 mm", (-BODY_L/2, -17), (BODY_L/2, -17), ha="center", va="center", arrowprops=dict(arrowstyle="<->"), fontsize=8)
ax.annotate("27.2 mm", (-38, -BODY_W/2), (-38, BODY_W/2), ha="center", va="center", rotation=90,
            arrowprops=dict(arrowstyle="<->"), fontsize=8)
ax.text(0, 18.0, "Anticipy v0.9 compact no-PCB prototype", ha="center", fontsize=13, weight="bold")
ax.text(0, 15.7, "official Jauch pack · full +15% hard cradle reserve · finished body stays under +30%", ha="center", fontsize=8)
ax.set_aspect("equal")
ax.set_xlim(-41, 41)
ax.set_ylim(-20, 20)
ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "v09_internal_layout.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("FAILED: " + "; ".join(failed))
