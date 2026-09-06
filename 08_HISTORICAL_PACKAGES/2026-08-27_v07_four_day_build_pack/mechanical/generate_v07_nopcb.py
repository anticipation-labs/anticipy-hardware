#!/usr/bin/env python3
"""Generate the Anticipy v0.7 no-custom-PCB retained founder prototype.

This is a four-day hand-assembly enclosure for verified off-the-shelf modules.
It is deliberately larger than the 51 x 21 x 11 mm production target.  All
dimensions are millimetres.  The output is an engineering prototype, not a
customer-production or certified wearable release.
"""

from pathlib import Path
import json
import math

import cadquery as cq
from cadquery import exporters
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
import trimesh


ROOT = Path(__file__).resolve().parent

# Honest rapid-prototype envelope.  The 35 x 25 x 6 mm protected pouch plus
# 15% XY placement reserve cannot fit a 26.3 mm finished width.
BODY_L = 76.0
BODY_W = 33.0
BODY_D = 19.0
WALL = 1.20
BASE_TOP = 17.30
LID_TOP = BODY_D
LID_SKIN = LID_TOP - BASE_TOP
LIP_DEPTH = 1.00
CHAIN_X = 31.0
CHAIN_R = 3.40
CHAIN_KEEP_R = 4.30

CARRIER_Z0 = 8.50
CARRIER_H = 0.80
CARRIER_L = 50.0
CARRIER_W = 28.40
BOARD_Z0 = 9.50

# Component envelopes are controlled physical maxima for this prototype CAD.
# Delivered parts must be measured before a live-battery assembly is closed.
BATTERY = {
    "name": "BBM protected 602535 500 mAh pack",
    "size": [35.0, 25.0, 6.0],
    "center": [-6.5, 0.0, 4.40],
    "mass_g": 10.0,
}
MOTOR = {
    "name": "Vybronics VCLP1020B002L ERM",
    "size": [10.0, 10.0, 2.10],
    "center": [19.5, -9.0, 2.55],
    "mass_g": 0.9,
}
HAPTIC = {
    "name": "haptic driver + 100 uF bulk-cap cluster",
    # Controlled hand-built envelope includes SMD transistor/resistors/diode,
    # 100 nF ceramic and a low-profile 100 uF bulk capacitor.  A tall radial
    # electrolytic is not accepted; it must fit this 11 x 7 x 6 mm gauge.
    "size": [11.0, 7.0, 6.0],
    "center": [20.5, 6.0, 4.30],
    "mass_g": 1.2,
}
SWITCH = {
    "name": "C&K OS102011MA1QN1 hard-off switch",
    "size": [8.60, 4.30, 4.70],
    "center": [19.0, 12.5, 4.15],
    "mass_g": 0.8,
}
BFF = {
    "name": "Adafruit Audio BFF 5769 with microSD",
    "size": [21.0, 17.70, 5.0],
    "center": [-12.0, 0.0, BOARD_Z0 + 5.0 / 2],
    "mass_g": 1.6,
}
XIAO = {
    # Rotated 90 degrees: physical 21.0 x 17.8 becomes CAD X=17.8, Y=21.0.
    "name": "Seeed XIAO nRF52840 Sense headerless",
    "size": [17.80, 21.0, 3.20],
    "center": [11.0, 0.0, BOARD_Z0 + 3.20 / 2],
    "mass_g": 2.5,
}
BUTTON = {
    "name": "C&K KSC201G-LFS button",
    "size": [6.20, 6.20, 3.50],
    "center": [-29.0, 0.0, 12.75],
    "mass_g": 0.5,
}

LOWER_PARTS = [BATTERY, MOTOR, HAPTIC, SWITCH]
UPPER_PARTS = [BFF, XIAO, BUTTON]
ALL_PARTS = LOWER_PARTS + UPPER_PARTS

# Four M2 x 8 screw bosses deliberately sit outside the battery and module
# envelopes.  They are asymmetric so the lid cannot be installed backwards.
SCREWS = [(-30.0, -9.0), (-30.0, 9.0), (28.0, -11.0), (30.0, 9.0)]


def capsule_solid(length: float, width: float, height: float, z0: float = 0.0):
    straight = length - width
    middle = cq.Workplane("XY").rect(straight, width).extrude(height)
    left = cq.Workplane("XY").center(-straight / 2, 0).circle(width / 2).extrude(height)
    right = cq.Workplane("XY").center(straight / 2, 0).circle(width / 2).extrude(height)
    return middle.union(left).union(right).translate((0, 0, z0))


def capsule_polygon(length: float, width: float):
    half_line = (length - width) / 2
    return LineString([(-half_line, 0), (half_line, 0)]).buffer(width / 2, quad_segs=96)


def box_shape(item):
    return cq.Workplane("XY").box(*item["size"]).translate(tuple(item["center"]))


def cyl_at(x, y, radius, height, z0):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z0))


# -------------------------------------------------------------------------
# Base shell: deep tray, reinforced chain eye, screw bosses, battery cradle,
# motor/driver/switch pockets, carrier ledges and button tower.
# -------------------------------------------------------------------------
outer_base = capsule_solid(BODY_L, BODY_W, BASE_TOP)
inner_base = capsule_solid(BODY_L - 2 * WALL, BODY_W - 2 * WALL, BASE_TOP, WALL)
chain_cut = cyl_at(CHAIN_X, 0, CHAIN_R, BODY_D + 2, -1)
base = outer_base.cut(inner_base).cut(chain_cut)

# Reinforced chain load path.
chain_boss = cyl_at(CHAIN_X, 0, CHAIN_KEEP_R + 0.45, BASE_TOP - WALL, WALL).cut(
    cyl_at(CHAIN_X, 0, CHAIN_R, BASE_TOP + 1, WALL - 0.2)
)
base = base.union(chain_boss)

# Screw bosses with blind 1.6 mm pilots.  M2 screws never enter battery space.
for sx, sy in SCREWS:
    boss = cyl_at(sx, sy, 2.60, BASE_TOP - WALL, WALL)
    # 7.4 mm blind thread-forming depth, open at the boss top.  An M2 x 8
    # button-head screw loses roughly 1 mm in the lid before entering the boss.
    pilot = cyl_at(sx, sy, 0.80, 7.50, BASE_TOP - 7.40)
    # Cut the blind pilot from the boss before unioning; doing the operations in
    # the opposite order can leave a disconnected positive pilot body in STEP.
    base = base.union(boss.cut(pilot))
    direction = 1 if sy > 0 else -1
    rib_len = max(1.0, BODY_W / 2 - abs(sy) - 1.0)
    rib = cq.Workplane("XY").box(1.20, rib_len + 0.6, 8.0).translate(
        (sx, sy + direction * (rib_len / 2), 5.2)
    )
    base = base.union(rib)

# Battery cradle, deliberately open at the left for leads and stretch-release tab.
bcx, bcy, _ = BATTERY["center"]
bl, bw, _ = BATTERY["size"]
rail_h = 1.05
rail_t = 0.80
gap = 0.40
for rail in [
    cq.Workplane("XY").box(bl + 2 * gap, rail_t, rail_h).translate(
        (bcx, bcy + bw / 2 + gap + rail_t / 2, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(bl + 2 * gap, rail_t, rail_h).translate(
        (bcx, bcy - bw / 2 - gap - rail_t / 2, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, bw + 2 * gap + 2 * rail_t, rail_h).translate(
        (bcx + bl / 2 + gap + rail_t / 2, bcy, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, 4.0, rail_h).translate(
        (bcx - bl / 2 - gap - rail_t / 2, bcy + 8.0, WALL + rail_h / 2)
    ),
    cq.Workplane("XY").box(rail_t, 4.0, rail_h).translate(
        (bcx - bl / 2 - gap - rail_t / 2, bcy - 8.0, WALL + rail_h / 2)
    ),
]:
    base = base.union(rail.edges("|Z").fillet(0.18))

# Battery lead and pull-tab routes contain no sharp edge.
lead_notch = cq.Workplane("XY").box(4.5, 3.0, 2.0).translate(
    (bcx - bl / 2 - gap, 0, WALL + 0.9)
)
base = base.cut(lead_notch)

# Motor cup and two printable hard keepers.  Motor is beside, never over, pouch.
mx, my, _ = MOTOR["center"]
motor_floor = cyl_at(mx, my, 5.35, 0.20, WALL)
motor_wall = cyl_at(mx, my, 5.40, 3.55, WALL).cut(cyl_at(mx, my, 5.15, 3.7, WALL - 0.05))
base = base.union(motor_floor).union(motor_wall)
for kx in (mx - 4.75, mx + 4.75):
    keeper = cq.Workplane("XY").box(0.90, 3.2, 0.60).translate((kx, my, 4.35))
    base = base.union(keeper)

# Discrete haptic driver pocket with wire exits.  The tiny hand-soldered cluster
# is retained by the four hard fences plus thin 3M 300LSE/9448A PSA and a
# removable Kapton cross-strap; a printed overhead clip would collide with the
# adjacent switch's 15%-expanded service envelope.
hx, hy, _ = HAPTIC["center"]
hl, hw, hh = HAPTIC["size"]
for x, y, sx, sy in [
    (hx - hl / 2 - 0.4, hy, 0.8, hw + 1.6),
    (hx + hl / 2 + 0.4, hy, 0.8, hw + 1.6),
    (hx, hy - hw / 2 - 0.4, hl + 1.6, 0.8),
    (hx, hy + hw / 2 + 0.4, hl + 1.6, 0.8),
]:
    base = base.union(cq.Workplane("XY").box(sx, sy, 1.2).translate((x, y, WALL + 0.6)))

# Hard-off switch pocket and side opening.  Actual pin function must be metered.
sx, sy, _ = SWITCH["center"]
sl, sw, sh = SWITCH["size"]
switch_floor = cq.Workplane("XY").box(sl + 1.2, sw + 0.8, 0.4).translate((sx, sy, WALL + 0.2))
switch_keeper_bottom = (SWITCH["center"][2] - sh / 2) + 1.15 * sh + 0.12
switch_keeper = cq.Workplane("XY").box(3.0, sw + 2.0, 0.70).translate(
    (sx, sy, switch_keeper_bottom + 0.35)
)
base = base.union(switch_floor).union(switch_keeper)

# Carrier ledges sit outside the 15%-expanded battery width and carry all board load.
for y in (-14.82, 14.82):
    base = base.union(cq.Workplane("XY").box(49.0, 0.90, 0.80).translate((0, y, CARRIER_Z0 - 0.40)))
for x in (-25.35, 25.35):
    # Full-height end stops join the floor, so the carrier capture cannot
    # become a disconnected printed island.
    end_h = CARRIER_Z0 + CARRIER_H - WALL
    stop_y = 0.0 if x < 0 else -1.0
    stop_len = 8.0 if x < 0 else 2.0
    base = base.union(cq.Workplane("XY").box(0.70, stop_len, end_h).translate(
        (x, stop_y, WALL + end_h / 2)
    ))

# Four-legged button tower, outside the battery and both board envelopes.
bx, by, _ = BUTTON["center"]
tower_plate_z0 = 10.20
for dx in (-2.75, 2.75):
    for dy in (-2.75, 2.75):
        leg = cq.Workplane("XY").box(1.10, 1.10, tower_plate_z0 - WALL).translate(
            (bx + dx, by + dy, (tower_plate_z0 + WALL) / 2)
        )
        base = base.union(leg)
button_platform = cq.Workplane("XY").box(7.6, 7.6, 0.80).translate((bx, by, tower_plate_z0 + 0.40))
base = base.union(button_platform)
for x, y, sx0, sy0 in [
    (bx - 3.50, by, 0.70, 7.4),
    (bx + 3.50, by, 0.70, 7.4),
    (bx, by - 3.50, 7.4, 0.70),
    (bx, by + 3.50, 7.4, 0.70),
]:
    base = base.union(cq.Workplane("XY").box(sx0, sy0, 1.2).translate((x, y, 11.40)))

# USB-C and power-switch openings.  The generous pilot openings are not sealed.
usb_cut = cq.Workplane("XY").box(11.0, 4.0, 4.8).translate((XIAO["center"][0], -BODY_W / 2, 11.0))
switch_cut = cq.Workplane("XY").box(11.0, 4.0, 6.0).translate((sx, BODY_W / 2, 4.0))
base = base.cut(usb_cut).cut(switch_cut).cut(chain_cut)


# -------------------------------------------------------------------------
# Separate board carrier: rigid deck, hard XY fences, printable edge clips,
# wire pass-throughs.  It rests on shell ledges and is preloaded only at edges.
# -------------------------------------------------------------------------
carrier = cq.Workplane("XY").box(CARRIER_L, CARRIER_W, CARRIER_H).edges("|Z").fillet(2.8).translate(
    (0, 0, CARRIER_Z0 + CARRIER_H / 2)
)
for wx, wy in [(-0.3, -11.5), (-0.3, 11.5), (21.0, 0.0), (-23.0, 0.0)]:
    carrier = carrier.cut(cq.Workplane("XY").box(4.0, 2.4, 1.6).translate((wx, wy, CARRIER_Z0 + 0.4)))


def add_board_bay(carrier_shape, part, board_h, rotate_usb_gap=False):
    cx, cy, _ = part["center"]
    px, py, _ = part["size"]
    fence_h = 1.25
    zc = CARRIER_Z0 + CARRIER_H + fence_h / 2
    # Short segmented fences keep solderable edges and the XIAO USB end accessible.
    for ex in (-1, 1):
        x = cx + ex * (px / 2 + 0.35)
        carrier_shape = carrier_shape.union(
            cq.Workplane("XY").box(0.70, 4.0, fence_h).translate((x, cy, zc))
        )
    for ey in (-1, 1):
        y = cy + ey * (py / 2 + 0.35)
        segments = [cx - px * 0.28, cx + px * 0.28]
        for segx in segments:
            if rotate_usb_gap and ey < 0 and abs(segx - cx) < px * 0.35:
                continue
            carrier_shape = carrier_shape.union(
                cq.Workplane("XY").box(3.2, 0.70, fence_h).translate((segx, y, zc))
            )
    # Two tool-releasable edge clips.  Minimum feature is 0.70 mm for P2S printing.
    clip_top = BOARD_Z0 + board_h + 0.45
    clip_positions = (cx - px * 0.32, cx) if rotate_usb_gap else (cx - px * 0.28, cx + px * 0.28)
    for clipx in clip_positions:
        clipy = cy + py / 2 + 0.42
        stem_h = clip_top - (CARRIER_Z0 + CARRIER_H)
        stem = cq.Workplane("XY").box(2.6, 0.70, stem_h).translate(
            (clipx, clipy, CARRIER_Z0 + CARRIER_H + stem_h / 2)
        )
        hook = cq.Workplane("XY").box(2.6, 1.10, 0.45).translate(
            (clipx, clipy - 0.20, clip_top - 0.225)
        )
        carrier_shape = carrier_shape.union(stem).union(hook)
    return carrier_shape


carrier = add_board_bay(carrier, BFF, BFF["size"][2])
carrier = add_board_bay(carrier, XIAO, XIAO["size"][2], rotate_usb_gap=True)


# -------------------------------------------------------------------------
# Screw-closed lid: alignment lip, four fasteners, carrier preload pillars,
# direct microphone duct and guided rear button.
# -------------------------------------------------------------------------
lid_skin = capsule_solid(BODY_L, BODY_W, LID_SKIN, BASE_TOP)
lip_outer = capsule_solid(BODY_L - 3.0, BODY_W - 3.0, LIP_DEPTH, BASE_TOP - LIP_DEPTH)
lip_inner = capsule_solid(BODY_L - 4.4, BODY_W - 4.4, LIP_DEPTH + 0.2, BASE_TOP - LIP_DEPTH - 0.1)
lid_lip = lip_outer.cut(lip_inner)
lid = lid_skin.union(lid_lip).cut(chain_cut)

for sx0, sy0 in SCREWS:
    through = cyl_at(sx0, sy0, 1.15, 3.0, BASE_TOP - 0.3)
    counter = cyl_at(sx0, sy0, 2.20, 0.75, BODY_D - 0.75)
    # The alignment lip clears the full base boss OD; the smaller through-hole
    # remains in the exterior skin for the M2 screw shank.
    boss_relief = cyl_at(sx0, sy0, 2.90, LIP_DEPTH + 0.10, BASE_TOP - LIP_DEPTH)
    lid = lid.cut(through).cut(counter).cut(boss_relief)

# Edge-only compression pillars capture the carrier without touching boards/pouch.
for px, py in [(-20.0, -13.55), (-20.0, 13.55), (20.0, -13.55), (20.0, 13.55)]:
    pillar_bottom = CARRIER_Z0 + CARRIER_H + 0.20
    pillar = cq.Workplane("XY").box(3.0, 1.20, BASE_TOP - pillar_bottom).translate(
        (px, py, pillar_bottom + (BASE_TOP - pillar_bottom) / 2)
    )
    lid = lid.union(pillar)

# XIAO microphone position from the known rotated-board pilot datum.
mic_x = XIAO["center"][0] + 4.57
mic_y = XIAO["center"][1] + 8.95
mic_hole = cyl_at(mic_x, mic_y, 0.70, 7.0, 12.5)
mic_boss = cyl_at(mic_x, mic_y, 1.70, 4.35, 12.95).cut(cyl_at(mic_x, mic_y, 0.70, 4.6, 12.8))
lid = lid.union(mic_boss).cut(mic_hole)

# Button guide.  Print three plungers and choose the shortest clean click.
button_hole = cyl_at(bx, by, 1.65, 6.0, 13.5)
button_guide = cyl_at(bx, by, 2.45, BASE_TOP - 14.70, 14.70).cut(
    cyl_at(bx, by, 1.65, BASE_TOP - 14.50, 14.50)
)
lid = lid.union(button_guide).cut(button_hole).cut(chain_cut)


# -------------------------------------------------------------------------
# Printable plungers and inert gauges.
# -------------------------------------------------------------------------
plungers = {}
for travel in (4.0, 4.3, 4.6):
    stem = cq.Workplane("XY").circle(1.40).extrude(travel)
    head = cq.Workplane("XY").circle(1.90).extrude(0.55).translate((0, 0, travel))
    p = stem.union(head)
    key = f"v07_button_plunger_{str(travel).replace('.', 'p')}"
    plungers[key] = p


def export_shape(name, shape):
    exporters.export(shape, str(ROOT / f"{name}.step"))
    exporters.export(shape, str(ROOT / f"{name}.stl"), tolerance=0.035, angularTolerance=0.08)


export_shape("v07_base_shell", base)
export_shape("v07_lid", lid)
export_shape("v07_carrier", carrier)
for name, shape in plungers.items():
    export_shape(name, shape)

for item, filename in [
    (BATTERY, "v07_dummy_battery_35x25x6"),
    (BFF, "v07_dummy_audio_bff_21x17p7x5"),
    (XIAO, "v07_dummy_xiao_rotated_17p8x21x3p2"),
    (HAPTIC, "v07_dummy_haptic_cap_cluster_11x7x6"),
    (SWITCH, "v07_dummy_switch_8p6x4p3x4p7"),
    (BUTTON, "v07_dummy_button_6p2x6p2x3p5"),
]:
    gauge = cq.Workplane("XY").box(*item["size"]).translate((0, 0, item["size"][2] / 2))
    export_shape(filename, gauge)
motor_gauge = cq.Workplane("XY").circle(MOTOR["size"][0] / 2).extrude(MOTOR["size"][2])
export_shape("v07_dummy_motor_10x2p1", motor_gauge)


# Full mechanical assembly STEP with controlled component envelopes.
assembly = cq.Assembly(name="Anticipy v0.7 no-custom-PCB retained prototype")
assembly.add(base, name="P2S printed base", color=cq.Color(0.72, 0.73, 0.75))
assembly.add(lid, name="P2S printed lid", color=cq.Color(0.30, 0.31, 0.34))
assembly.add(carrier, name="P2S printed board carrier", color=cq.Color(0.20, 0.22, 0.25))
colors = {
    BATTERY["name"]: cq.Color(0.90, 0.68, 0.15),
    MOTOR["name"]: cq.Color(0.72, 0.35, 0.20),
    HAPTIC["name"]: cq.Color(0.48, 0.34, 0.58),
    SWITCH["name"]: cq.Color(0.28, 0.28, 0.30),
    BFF["name"]: cq.Color(0.10, 0.45, 0.28),
    XIAO["name"]: cq.Color(0.12, 0.34, 0.58),
    BUTTON["name"]: cq.Color(0.40, 0.40, 0.42),
}
for item in ALL_PARTS:
    if item is MOTOR:
        shape = cyl_at(item["center"][0], item["center"][1], item["size"][0] / 2, item["size"][2], item["center"][2] - item["size"][2] / 2)
    else:
        shape = box_shape(item)
    assembly.add(shape, name=item["name"], color=colors[item["name"]])
assembly.save(str(ROOT / "v07_full_assembly.step"))


# -------------------------------------------------------------------------
# Independent geometry and margin checks.
# -------------------------------------------------------------------------
inner_poly = capsule_polygon(BODY_L - 2 * WALL, BODY_W - 2 * WALL)
chain_keep_poly = Point(CHAIN_X, 0).buffer(CHAIN_KEEP_R, quad_segs=96)


def footprint(item, scale=1.0):
    sx0, sy0, _ = item["size"]
    cx, cy, _ = item["center"]
    p = Polygon([
        (cx - sx0 / 2, cy - sy0 / 2),
        (cx + sx0 / 2, cy - sy0 / 2),
        (cx + sx0 / 2, cy + sy0 / 2),
        (cx - sx0 / 2, cy + sy0 / 2),
    ])
    return affinity.scale(p, xfact=scale, yfact=scale, origin=(cx, cy))


expanded = {}
for item in ALL_PARTS:
    if item is MOTOR:
        expanded[item["name"]] = Point(item["center"][0], item["center"][1]).buffer(
            item["size"][0] / 2 * 1.15, quad_segs=64
        )
    else:
        expanded[item["name"]] = footprint(item, 1.15)

margin_inside = {
    name: inner_poly.covers(poly) and not poly.intersects(chain_keep_poly)
    for name, poly in expanded.items()
}

expanded_collisions = []
for group in (LOWER_PARTS, UPPER_PARTS):
    for i, a in enumerate(group):
        for b in group[i + 1:]:
            if expanded[a["name"]].intersection(expanded[b["name"]]).area > 0.001:
                expanded_collisions.append(f"{a['name']} / {b['name']}")

actual_collisions = []
for i, a in enumerate(ALL_PARTS):
    amin = np.array(a["center"]) - np.array(a["size"]) / 2
    amax = np.array(a["center"]) + np.array(a["size"]) / 2
    for b in ALL_PARTS[i + 1:]:
        bmin = np.array(b["center"]) - np.array(b["size"]) / 2
        bmax = np.array(b["center"]) + np.array(b["size"]) / 2
        if np.all(np.minimum(amax, bmax) - np.maximum(amin, bmin) > 0.01):
            actual_collisions.append(f"{a['name']} / {b['name']}")


def physical_shape(item):
    if item is MOTOR:
        return cyl_at(
            item["center"][0], item["center"][1], item["size"][0] / 2,
            item["size"][2], item["center"][2] - item["size"][2] / 2,
        )
    return box_shape(item)


component_structure_collisions = []
for item in ALL_PARTS:
    pshape = physical_shape(item)
    for structure_name, structure in (("base", base), ("carrier", carrier), ("lid", lid)):
        volume = sum(s.Volume() for s in pshape.intersect(structure).solids().vals())
        if volume > 0.001:
            component_structure_collisions.append(
                {"component": item["name"], "structure": structure_name, "volume_mm3": volume}
            )

printed_part_collisions = []
for a_name, a_shape, b_name, b_shape in (
    ("base", base, "carrier", carrier),
    ("base", base, "lid", lid),
    ("carrier", carrier, "lid", lid),
):
    volume = sum(s.Volume() for s in a_shape.intersect(b_shape).solids().vals())
    if volume > 0.001:
        printed_part_collisions.append(
            {"parts": f"{a_name} / {b_name}", "volume_mm3": volume}
        )

z_gaps = {
    "floor_to_battery": BATTERY["center"][2] - BATTERY["size"][2] / 2 - WALL,
    "battery_to_carrier": CARRIER_Z0 - (BATTERY["center"][2] + BATTERY["size"][2] / 2),
    "carrier_to_boards": BOARD_Z0 - (CARRIER_Z0 + CARRIER_H),
    "xiao_to_lid": BASE_TOP - (XIAO["center"][2] + XIAO["size"][2] / 2),
    "audio_bff_to_lid": BASE_TOP - (BFF["center"][2] + BFF["size"][2] / 2),
    "button_to_lid": BASE_TOP - (BUTTON["center"][2] + BUTTON["size"][2] / 2),
}

# A component's seating surface is controlled by its hard cradle/carrier.  The
# 15% Z reserve therefore grows upward from that surface instead of pretending
# the part can float through the floor.  Keeper gaps include a small printable
# relief after the expanded maximum height.
def seated_top_115(item):
    nominal_bottom = item["center"][2] - item["size"][2] / 2
    return nominal_bottom + 1.15 * item["size"][2]


z_margin_gaps = {
    "battery_115_to_carrier": CARRIER_Z0 - seated_top_115(BATTERY),
    "motor_115_to_keeper": 4.05 - seated_top_115(MOTOR),
    "haptic_115_to_carrier": CARRIER_Z0 - seated_top_115(HAPTIC),
    "switch_115_to_keeper": switch_keeper_bottom - seated_top_115(SWITCH),
    "audio_bff_115_to_lid": BASE_TOP - seated_top_115(BFF),
    "xiao_115_to_lid": BASE_TOP - seated_top_115(XIAO),
    "button_115_to_lid": BASE_TOP - seated_top_115(BUTTON),
}

# Check printable mesh integrity and estimate mass.
primary_names = ["v07_base_shell", "v07_lid", "v07_carrier", *plungers.keys()]
mesh_checks = {}
plastic_volume_mm3 = 0.0
for name in primary_names:
    mesh = trimesh.load_mesh(ROOT / f"{name}.stl")
    shells = mesh.split(only_watertight=False)
    # Blind holes appear as negative, disconnected inner shells in STL while
    # still belonging to one printable solid.  Count only positive outer shells
    # as physical bodies; retain void-shell count for auditability.
    positive_bodies = sum(1 for shell in shells if shell.volume > 0)
    negative_void_shells = sum(1 for shell in shells if shell.volume < 0)
    mesh_checks[name] = {
        "watertight": bool(mesh.is_watertight),
        "positive_bodies": int(positive_bodies),
        "negative_void_shells": int(negative_void_shells),
        "bounds": np.round(mesh.extents, 3).tolist(),
    }
    if name in ("v07_base_shell", "v07_lid", "v07_carrier"):
        plastic_volume_mm3 += abs(mesh.volume)

plastic_mass_g = plastic_volume_mm3 / 1000 * 1.25
hardware_mass_g = 0.8 + 1.5  # four M2 screws plus foam/tape/wires
electronics_mass_g = sum(p["mass_g"] for p in ALL_PARTS)
nominal_mass_g = plastic_mass_g + hardware_mass_g + electronics_mass_g
mass_15_g = nominal_mass_g * 1.15

checks = [
    ("finished envelope", BODY_L == 76 and BODY_W == 33 and BODY_D == 19),
    ("15% XY envelopes inside cavity and outside chain keepout", all(margin_inside.values())),
    ("15% same-layer envelopes do not overlap", not expanded_collisions),
    ("actual component boxes do not collide", not actual_collisions),
    ("actual components do not intersect printed structure", not component_structure_collisions),
    ("base, carrier and lid close without solid interference", not printed_part_collisions),
    ("all explicit Z gaps positive", min(z_gaps.values()) > 0),
    ("15% seated Z envelopes retain positive keeper/lid gaps", min(z_margin_gaps.values()) > 0),
    ("primary print meshes watertight", all(v["watertight"] for v in mesh_checks.values())),
    ("one positive body per primary print mesh", all(v["positive_bodies"] == 1 for v in mesh_checks.values())),
]

report = {
    "classification": "four-day no-custom-PCB founder prototype; not customer production",
    "finished_envelope_mm": [BODY_L, BODY_W, BODY_D],
    "reference_target_mm": [51, 21, 11],
    "excess_over_target_mm": [BODY_L - 51, BODY_W - 21, BODY_D - 11],
    "margin_inside": margin_inside,
    "expanded_collisions": expanded_collisions,
    "actual_collisions": actual_collisions,
    "component_structure_collisions": component_structure_collisions,
    "printed_part_collisions": printed_part_collisions,
    "z_gaps_mm": z_gaps,
    "z_margin_15_percent_gaps_mm": z_margin_gaps,
    "mesh_checks": mesh_checks,
    "mass": {
        "printed_plastic_estimate_g": round(plastic_mass_g, 2),
        "electronics_assumption_g": round(electronics_mass_g, 2),
        "screws_foam_tape_wires_assumption_g": round(hardware_mass_g, 2),
        "nominal_total_estimate_g": round(nominal_mass_g, 2),
        "with_15_percent_uncertainty_g": round(mass_15_g, 2),
    },
    "checks": [{"name": n, "pass": p} for n, p in checks],
}
(ROOT / "v07_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")

lines = [
    "# Anticipy v0.7 no-custom-PCB retained fit report",
    "",
    "Classification: four-day hand-assembled founder prototype, not customer production.",
    "",
]
for index, (name, passed) in enumerate(checks, 1):
    lines.append(f"{index}. {'PASS' if passed else 'FAIL'} — {name}")
lines += [
    "",
    f"Finished envelope: {BODY_L:.1f} × {BODY_W:.1f} × {BODY_D:.1f} mm.",
    "The 51 × 21 × 11 mm target is not claimed because the protected 35 × 25 × 6 mm pack alone needs 40.25 × 28.75 mm XY reservation after the 15% margin.",
    f"Printed plastic estimate: {plastic_mass_g:.2f} g.",
    f"Nominal complete estimate: {nominal_mass_g:.2f} g; with 15% uncertainty: {mass_15_g:.2f} g.",
    "Mass remains a physical weigh-in gate because supplier pack, wiring, foam and screw weights are not controlled here.",
    "",
    "Positive digital clearance does not prove battery runtime, drop survival, acoustics, RF range, sealing or electrical safety.",
]
(ROOT / "V07_FIT_REPORT.md").write_text("\n".join(lines) + "\n")


# Layout image.
fig, ax = plt.subplots(figsize=(11, 5.4), dpi=180)
outline = capsule_polygon(BODY_L, BODY_W)
xo, yo = outline.exterior.xy
ax.fill(xo, yo, color="#d5d7da", ec="#111", lw=1.2)
ax.add_patch(Circle((CHAIN_X, 0), CHAIN_R, fc="white", ec="#111"))
palette = {
    BATTERY["name"]: "#e4b83e", MOTOR["name"]: "#ba6a45", HAPTIC["name"]: "#7a5793",
    SWITCH["name"]: "#555", BFF["name"]: "#26734d", XIAO["name"]: "#285c91",
    BUTTON["name"]: "#777",
}
for item in ALL_PARTS:
    sx0, sy0, _ = item["size"]
    cx, cy, _ = item["center"]
    if item is MOTOR:
        ax.add_patch(Circle((cx, cy), sx0 / 2, fc=palette[item["name"]], ec="#111"))
    else:
        ax.add_patch(FancyBboxPatch((cx - sx0 / 2, cy - sy0 / 2), sx0, sy0,
            boxstyle="round,pad=0.02,rounding_size=0.6", fc=palette[item["name"]], ec="#111", alpha=.92))
    short = {
        BATTERY["name"]: "500 mAh\nunder carrier", MOTOR["name"]: "motor",
        HAPTIC["name"]: "driver", SWITCH["name"]: "off",
        BFF["name"]: "Audio BFF\n+ microSD", XIAO["name"]: "XIAO", BUTTON["name"]: "button",
    }[item["name"]]
    ax.text(cx, cy, short, ha="center", va="center", fontsize=6.5,
            color="white" if item not in (BATTERY,) else "#3b3100")
ax.text(0, 22, "Anticipy v0.7 — retained no-custom-PCB prototype", ha="center", fontsize=13, weight="bold")
ax.text(0, 19, "battery below carrier · boards above · motor/driver beside pouch · four-screw lid", ha="center", fontsize=8)
ax.annotate("76 mm", xy=(-38, -20), xytext=(38, -20), ha="center", va="center",
            arrowprops=dict(arrowstyle="<->"), fontsize=8)
ax.annotate("33 mm", xy=(-45, -16.5), xytext=(-45, 16.5), ha="center", va="center", rotation=90,
            arrowprops=dict(arrowstyle="<->"), fontsize=8)
ax.set_aspect("equal"); ax.set_xlim(-48, 48); ax.set_ylim(-24, 24); ax.axis("off")
fig.tight_layout(); fig.savefig(ROOT / "v07_internal_layout.png", bbox_inches="tight", facecolor="white"); plt.close(fig)


# GLB visual inspection scene from exact exported meshes and controlled blocks.
scene = trimesh.Scene()
for filename, name, color in [
    ("v07_base_shell.stl", "base", [185, 187, 191, 210]),
    ("v07_lid.stl", "lid", [60, 63, 68, 100]),
    ("v07_carrier.stl", "carrier", [45, 48, 52, 190]),
]:
    mesh = trimesh.load_mesh(ROOT / filename)
    mesh.visual.face_colors = color
    scene.add_geometry(mesh, node_name=name)
for item in ALL_PARTS:
    if item is MOTOR:
        mesh = trimesh.creation.cylinder(radius=5.0, height=2.10, sections=48)
        mesh.apply_translation(item["center"])
    else:
        mesh = trimesh.creation.box(item["size"])
        mesh.apply_translation(item["center"])
    mesh.visual.face_colors = [70, 130, 95, 255]
    scene.add_geometry(mesh, node_name=item["name"])
scene.export(ROOT / "v07_fit_check.glb")


# Generic millimetre-scale 3MF plates.  Slicer settings remain in the guide.
def plate(filename, entries):
    s = trimesh.Scene()
    for name, source, offset, flip in entries:
        mesh = trimesh.load_mesh(ROOT / source)
        if flip:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        mesh.apply_translation([0, 0, -mesh.bounds[0, 2]])
        mesh.apply_translation(offset)
        if mesh.bounds[0, 2] < -1e-6:
            raise RuntimeError(f"{name} below build plate")
        s.add_geometry(mesh, node_name=name)
    s.export(ROOT / filename, file_type="3mf")


plate("P2S_v07_nopcb_retained.3mf", [
    ("v07 base", "v07_base_shell.stl", (-48, 0, 0), False),
    ("v07 lid exterior down", "v07_lid.stl", (48, 0, 0), True),
    ("v07 carrier", "v07_carrier.stl", (0, 42, 0), False),
    ("plunger 4.0", "v07_button_plunger_4p0.stl", (-10, -32, 0), False),
    ("plunger 4.3", "v07_button_plunger_4p3.stl", (0, -32, 0), False),
    ("plunger 4.6", "v07_button_plunger_4p6.stl", (10, -32, 0), False),
])

plate("P2S_v07_fit_gauges.3mf", [
    ("battery", "v07_dummy_battery_35x25x6.stl", (-45, -22, 0), False),
    ("Audio BFF", "v07_dummy_audio_bff_21x17p7x5.stl", (0, -22, 0), False),
    ("XIAO", "v07_dummy_xiao_rotated_17p8x21x3p2.stl", (35, -22, 0), False),
    ("motor", "v07_dummy_motor_10x2p1.stl", (-40, 22, 0), False),
    ("driver + cap", "v07_dummy_haptic_cap_cluster_11x7x6.stl", (-15, 22, 0), False),
    ("switch", "v07_dummy_switch_8p6x4p3x4p7.stl", (10, 22, 0), False),
    ("button", "v07_dummy_button_6p2x6p2x3p5.stl", (35, 22, 0), False),
])

if not all(p for _, p in checks):
    raise SystemExit("V07 VERIFICATION FAILED — inspect v07_fit_report.json")

for name, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} | {name}")
print(f"PASS | envelope | {BODY_L:.1f} x {BODY_W:.1f} x {BODY_D:.1f} mm")
print(f"INFO | mass | nominal {nominal_mass_g:.2f} g; +15% {mass_15_g:.2f} g")
print("Created P2S_v07_nopcb_retained.3mf and P2S_v07_fit_gauges.3mf")
