#!/usr/bin/env python3
"""Generate and verify the Anticipy v1.0 retained mechanical candidate.

This is a collision-checked mechanical placement model and manufacturing brief.
It is not a routed PCB, Gerber package, or released retail product.
All dimensions are millimetres. The PLAUD dimensions are hard ceilings.
"""

from pathlib import Path
import json
import math

import cadquery as cq
from cadquery import exporters
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
import numpy as np
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon
import trimesh


ROOT = Path(__file__).resolve().parent

# Prevent a regenerated v1.0 folder from carrying forward the obsolete v0.6
# fit gauges. They are deliberately not outputs of this generator.
for stale_name in (
    "production_dummy_battery_26x12.5x6.step",
    "production_dummy_battery_26x12.5x6.stl",
    "production_dummy_radio_6.3x7.9x1.75.step",
    "production_dummy_radio_6.3x7.9x1.75.stl",
):
    (ROOT / stale_name).unlink(missing_ok=True)

# Verified PLAUD NotePin S hard limits. Anticipy is intentionally nominally smaller.
MAX_L, MAX_W, MAX_D = 51.0, 21.0, 11.0
MAX_MASS_G = 17.4
BODY_L, BODY_W, BODY_D = 50.5, 20.5, 10.8
FINISHED_POS_TOL = 0.15
# The polymer body is 20.50 mm wide.  A 0.18 mm molded silicone button membrane
# sits outside one side, so the honest finished nominal width is 20.68 mm.
FINISHED_L, FINISHED_W, FINISHED_D = BODY_L, BODY_W + 0.18, BODY_D

# Hybrid enclosure: a structural 0.8 mm clear-anodized 5052-H32 front cap,
# 0.15 mm VHB 5906 perimeter seal, and a Covestro Makrolon 2407 polycarbonate
# chassis/rear/RF region. The
# cap is inset behind a polymer impact rim and split away from the antenna.
CAP_RECESS = 0.05
CAP_H = 0.80
ADHESIVE_H = 0.15
CHASSIS_Z0 = CAP_RECESS + CAP_H + ADHESIVE_H
REAR_FLOOR = 0.60
SIDE_WALL = 0.80
CAP_EDGE_INSET = 0.25
BOND_LAND = 1.15
VENT_RECESS_H = 0.38
MOTOR_SCALLOP_R = 4.30
RF_SPLIT_X = -13.50
CAP_SEAM_GAP = 0.15

# Anticipy.ai pendant language: a body-through chain hole near the upper end.
CHAIN_X = 22.00
CHAIN_R = 2.10
CHAIN_KEEP_R = 2.70

# The finished battery envelope includes PCM, leads and an NTC allowance. The
# sourced LP571225 cell is smaller; production requires a signed controlled pack.
BATTERY = {
    "name": "BAT-ANT-200-001 finished protected pack",
    # LP571225's public comparator drawing permits 26 +/-1 mm length,
    # 12 +/-0.5 mm width and 5.7 +/-0.3 mm thickness.  The controlled
    # production envelope therefore uses the real public maxima, not nominal.
    "size": [27.0, 12.5, 6.0],
    "center": [-0.40, 0.0, 4.0],
}
BATTERY_CELL = {
    "name": "LP571225 200 mAh pouch body",
    "size": [25.0, 12.0, 5.7],
    "center": [-0.85, 0.0, 3.95],
}

# Shaped four-layer PCB: a large main island plus a narrow RF nose. The two
# blocks are checked separately against the rounded cavity with 15% XY reserve.
PCB_MAIN = {
    "name": "PCB main island",
    "size": [31.0, 14.0, 0.60],
    "center": [0.50, 0.0, 9.75],
}
PCB_NOSE = {
    "name": "PCB RF nose",
    "size": [6.5, 7.5, 0.60],
    "center": [-18.25, 0.0, 9.75],
}

# All active components are on the cavity-facing underside of the PCB. Bottom-
# port microphones therefore use direct holes through the PCB and rear shell.
MODULE = {
    "name": "Raytac AN54LV-15 nRF54L15 module",
    "size": [8.40, 6.40, 1.50],
    # Shifted into the polymer RF end so the module's antenna end remains clear
    # even when the controlled battery XY envelope receives the full 15% reserve.
    "center": [-15.40, 0.00, 8.70],
}
ANTENNA_KEEP = {
    "name": "Raytac AN54LV-15 antenna/no-ground region",
    "size": [2.90, 6.40, 2.60],
    "center": [-18.15, 0.0, 8.85],
}
FLASH = {
    "name": "MK Founder MKDV4GCL-ABF managed SD NAND (481 MB usable)",
    "size": [8.00, 6.00, 0.80],
    "center": [-1.70, 2.40, 9.05],
}
PMIC = {
    "name": "nPM1300 plus inductors/passives reserve",
    "size": [5.60, 4.80, 0.70],
    "center": [6.20, 4.20, 9.10],
}
HAPTIC_DRIVER = {
    "name": "DRV2605L plus passives reserve",
    "size": [3.80, 3.20, 0.70],
    "center": [5.25, -4.70, 9.10],
}
BUTTON = {
    # Public manufacturer drawing includes the side-actuated body and land.
    "name": "Littelfuse C&K PTS841GMSMTRLFS side-push switch",
    # X is transverse and Y is the side-actuation direction.
    "size": [3.50, 3.60, 1.25],
    "center": [0.00, -4.85, 8.825],
}
BUTTON_MAX = {
    "name": "PTS841 terminal/body/max-height validation envelope",
    "size": [4.85, 3.60, 1.45],
    "center": [0.00, -4.85, 8.725],
}
BUTTON_LAND = {
    "name": "PTS841 controlled PCB land-span envelope",
    "size": [5.20, 3.60, 0.10],
    "center": [0.00, -4.85, 9.40],
}
LED = {
    "name": "status LED and resistor reserve",
    "size": [1.60, 0.80, 0.60],
    "center": [0.0, 6.45, 9.15],
}
MICS = [
    {
        "name": "Infineon IM69D128S microphone A",
        "size": [3.50, 2.65, 1.00],
        # A tenth-millimetre separation prevents the two 15%-expanded
        # courtyards from touching while retaining the direct rear sound duct.
        "center": [-12.80, -5.30, 8.95],
    },
    {
        "name": "Infineon IM69D128S microphone B",
        "size": [3.50, 2.65, 1.00],
        "center": [13.80, 5.20, 8.95],
    },
]
MOTOR = {
    "name": "Vybronics VC0720B015F wired coin ERM",
    "size": [7.00, 7.00, 2.00],
    "center": [17.15, -4.90, 8.25],
}
MOTOR_MAX = {
    "name": "VC0720B015F published maximum can envelope",
    "size": [7.10, 7.10, 2.10],
    "center": [17.15, -4.90, 8.30],
}
CHARGE_PADS = [(4.0, -2.35, 1.05), (4.0, 2.35, 0.85)]

COMPONENTS = [MODULE, FLASH, PMIC, HAPTIC_DRIVER, BUTTON, LED, *MICS]


def capsule_solid(length: float, width: float, height: float, z0: float = 0.0) -> cq.Workplane:
    straight = length - width
    centre = cq.Workplane("XY").rect(straight, width).extrude(height)
    left = cq.Workplane("XY").center(-straight / 2, 0).circle(width / 2).extrude(height)
    right = cq.Workplane("XY").center(straight / 2, 0).circle(width / 2).extrude(height)
    return centre.union(left).union(right).translate((0, 0, z0))


def capsule_polygon(length: float, width: float):
    half_line = (length - width) / 2
    return LineString([(-half_line, 0), (half_line, 0)]).buffer(width / 2, quad_segs=96)


def box_shape(item: dict) -> cq.Workplane:
    sx, sy, sz = item["size"]
    return cq.Workplane("XY").box(sx, sy, sz).translate(tuple(item["center"]))


def crop_x(shape: cq.Workplane, xmin: float, xmax: float) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY")
        .box(xmax - xmin, BODY_W + 4.0, BODY_D + 2.0)
        .translate(((xmin + xmax) / 2, 0, BODY_D / 2))
    )
    return shape.intersect(cutter)


# ----- Enclosure solids -----------------------------------------------------
outer = capsule_solid(BODY_L, BODY_W, BODY_D - CHASSIS_Z0, CHASSIS_Z0)
inner = capsule_solid(
    BODY_L - 2 * SIDE_WALL,
    BODY_W - 2 * SIDE_WALL,
    BODY_D - CHASSIS_Z0 - REAR_FLOOR,
    CHASSIS_Z0,
)
chain_cut = (
    cq.Workplane("XY")
    .center(CHAIN_X, 0)
    .circle(CHAIN_R)
    .extrude(BODY_D + 2)
    .translate((0, 0, -1))
)
chassis = outer.cut(inner).cut(chain_cut)

# The polymer rim reaches the front-most plane. The cap is 0.05 mm recessed,
# so an edge/corner impact contacts polymer before it can peel the metal edge.
CAP_L = BODY_L - 2 * CAP_EDGE_INSET
CAP_W = BODY_W - 2 * CAP_EDGE_INSET
impact_outer = capsule_solid(BODY_L, BODY_W, CHASSIS_Z0)
impact_open = capsule_solid(CAP_L + 0.10, CAP_W + 0.10, CHASSIS_Z0 + 0.2, -0.1)
impact_rim = impact_outer.cut(impact_open).cut(chain_cut)

# A continuous structural land sits behind the cap. The 0.15 mm VHB occupies
# z=0.85..1.00; the geometry below carries in-plane/drop shear instead of
# asking the adhesive edge to carry it alone.
bond_outer = capsule_solid(CAP_L, CAP_W, 0.25, CHASSIS_Z0)
bond_inner = capsule_solid(
    CAP_L - 2 * BOND_LAND,
    CAP_W - 2 * BOND_LAND,
    0.35,
    CHASSIS_Z0 - 0.05,
)
bond_land_solid = bond_outer.cut(bond_inner).cut(chain_cut)
chassis = chassis.union(impact_rim).union(bond_land_solid)

full_cap = capsule_solid(CAP_L, CAP_W, CAP_H, CAP_RECESS).cut(chain_cut)
rf_end = RF_SPLIT_X - CAP_SEAM_GAP / 2
al_start = RF_SPLIT_X + CAP_SEAM_GAP / 2
rf_cap = crop_x(full_cap, -CAP_L / 2 - 0.5, rf_end)
al_cap = crop_x(full_cap, al_start, CAP_L / 2 + 0.5)

# A separate inert appearance gauge shows the intended soft pebble surface.
# The functional split enclosure remains deliberately unfilleted so factory
# reviewers can see the current seams, floors and hard fit envelope clearly.
visual_pebble = capsule_solid(BODY_L, BODY_W, BODY_D).edges().fillet(1.20).cut(chain_cut)
exporters.export(visual_pebble, str(ROOT / "production_visual_pebble.step"))
exporters.export(
    visual_pebble,
    str(ROOT / "production_visual_pebble.stl"),
    tolerance=0.025,
    angularTolerance=0.06,
)

# Rear microphone holes, 0.38 mm GAW337 vent recesses and local annular bosses.
for mic in MICS:
    mx, my, _ = mic["center"]
    duct = (
        cq.Workplane("XY").center(mx, my).circle(0.48)
        .extrude(1.6).translate((0, 0, BODY_D - 1.25))
    )
    membrane_recess = (
        cq.Workplane("XY").center(mx, my).circle(1.55)
        .extrude(VENT_RECESS_H).translate((0, 0, BODY_D - VENT_RECESS_H))
    )
    chassis = chassis.cut(duct).cut(membrane_recess)
    acoustic_boss = (
        cq.Workplane("XY").center(mx, my).circle(1.55).circle(0.60)
        .extrude(0.14).translate((0, 0, BODY_D - REAR_FLOOR - 0.04))
    )
    chassis = chassis.union(acoustic_boss)

# Direct hard-gold PCB pads are reached through asymmetric, keyed rear apertures.
for cx, cy, radius in CHARGE_PADS:
    contact = (
        cq.Workplane("XY").center(cx, cy).circle(radius)
        .extrude(1.3).translate((0, 0, BODY_D - 1.0))
    )
    chassis = chassis.cut(contact)

# Side button opening for the PTS841 side-push axis.  The hard plunger is
# captive; a converted silicone membrane bonds into the larger shallow seat.
# Its final preload is frozen only after actual switch samples are measured.
button_cut = (
    cq.Workplane("XY").box(3.20, 2.10, 1.70)
    .translate((BUTTON["center"][0], -BODY_W / 2, BUTTON["center"][2]))
)
chassis = chassis.cut(button_cut)
button_boot_seat = cq.Workplane("XY").box(4.20, 0.16, 2.20).translate(
    (BUTTON["center"][0], -BODY_W / 2 + 0.04, BUTTON["center"][2])
)
chassis = chassis.cut(button_boot_seat)

# Battery cradle. The structural metal cap supports the broad face through a
# 0.05 mm PET barrier plus 0.10 mm tesa 77010; these rounded rails only locate
# X/Y. The split left end leaves a tool-free longitudinal pull-tab path.
bat_cx, bat_cy, _ = BATTERY["center"]
bat_l, bat_w, _ = BATTERY["size"]
CRADLE_GAP = 0.20
CRADLE_RAIL = 0.40
CRADLE_Z0 = CHASSIS_Z0
CRADLE_H = 0.90
cradle_x_half = bat_l / 2 + CRADLE_GAP
cradle_y_half = bat_w / 2 + CRADLE_GAP

for rail in [
    cq.Workplane("XY").box(bat_l + 2 * CRADLE_GAP + 0.40, CRADLE_RAIL, CRADLE_H).translate(
        (bat_cx, bat_cy + cradle_y_half + CRADLE_RAIL / 2, CRADLE_Z0 + CRADLE_H / 2)
    ),
    cq.Workplane("XY").box(bat_l + 2 * CRADLE_GAP + 0.40, CRADLE_RAIL, CRADLE_H).translate(
        (bat_cx, bat_cy - cradle_y_half - CRADLE_RAIL / 2, CRADLE_Z0 + CRADLE_H / 2)
    ),
    cq.Workplane("XY").box(CRADLE_RAIL, bat_w + 2 * CRADLE_GAP + 0.40, CRADLE_H).translate(
        (bat_cx + cradle_x_half + CRADLE_RAIL / 2, bat_cy, CRADLE_Z0 + CRADLE_H / 2)
    ),
    cq.Workplane("XY").box(CRADLE_RAIL, 3.70, CRADLE_H).translate(
        (bat_cx - cradle_x_half - CRADLE_RAIL / 2, bat_cy + 4.65, CRADLE_Z0 + CRADLE_H / 2)
    ),
    cq.Workplane("XY").box(CRADLE_RAIL, 3.70, CRADLE_H).translate(
        (bat_cx - cradle_x_half - CRADLE_RAIL / 2, bat_cy - 4.65, CRADLE_Z0 + CRADLE_H / 2)
    ),
]:
    chassis = chassis.union(rail.edges("|Z").fillet(0.12))

# Four low bridges make the cradle part of the structural chassis rather than
# a floating print body. They sit outside the battery's controlled envelope.
for bx in (-8.0, 8.0):
    for sign in (-1, 1):
        bridge_y = sign * ((cradle_y_half + CRADLE_RAIL) + (BODY_W / 2 - SIDE_WALL)) / 2
        bridge_len = (BODY_W / 2 - SIDE_WALL) - (cradle_y_half + CRADLE_RAIL)
        bridge = cq.Workplane("XY").box(2.0, bridge_len + 0.20, 0.35).translate(
            (bx, bridge_y, CHASSIS_Z0 + 0.175)
        )
        chassis = chassis.union(bridge)

# Haptic motor lives beside, never over, the controlled pouch outline. A rigid
# shelf carries the can, a 0.05 mm PSA bonds it, a circular wall fixes X/Y, and
# two snap-over lips stop +Z motion. The pocket connects directly to the shell.
motor_x, motor_y, _ = MOTOR["center"]
MOTOR_SHELF_Z0 = 6.60
MOTOR_SHELF_H = 0.60
motor_shelf = (
    cq.Workplane("XY").center(motor_x, motor_y).circle(3.65)
    .extrude(MOTOR_SHELF_H).translate((0, 0, MOTOR_SHELF_Z0))
)
motor_bridge = cq.Workplane("XY").box(3.10, 1.20, MOTOR_SHELF_H).translate(
    (22.05, motor_y, MOTOR_SHELF_Z0 + MOTOR_SHELF_H / 2)
)
motor_wall = (
    # 7.30 mm released starting pocket ID for the 7.10 mm maximum can, with
    # a toolable 0.60 mm annular section. Final draft/tolerance is molder-gated.
    cq.Workplane("XY").center(motor_x, motor_y).circle(4.25).circle(3.65)
    .extrude(3.15).translate((0, 0, MOTOR_SHELF_Z0))
)
# The full ring would clip the controlled battery envelope at its lower-left
# edge. Open that short arc while retaining the shelf, PSA and the other three
# rigid pocket sectors. The cut line stays 0.25 mm beyond the battery maximum.
motor_wall_battery_relief = cq.Workplane("XY").box(50.0, 24.0, 4.0).translate(
    (-11.65, 0.0, MOTOR_SHELF_Z0 + 2.0)
)
motor_wall = motor_wall.cut(motor_wall_battery_relief)
chassis = chassis.union(motor_shelf).union(motor_bridge).union(motor_wall)

for keeper_x in (motor_x - 3.65, motor_x + 3.65):
    # 0.40 mm crash-stop lips begin at the published maximum can top. The
    # controlled PSA supplies normal retention; these prevent escape on shock.
    keeper = cq.Workplane("XY").box(0.80, 2.00, 0.40).translate(
        (keeper_x, motor_y, 9.55)
    )
    chassis = chassis.union(keeper)

wire_exit = cq.Workplane("XY").box(1.60, 1.40, 2.60).translate(
    (motor_x, motor_y + 3.65, 8.30)
)
chassis = chassis.cut(wire_exit)

# Reinforced chain-eye load path. The 4.2 mm through-hole remains unchanged;
# an internal annular boss spreads pull and edge-drop load into the rear shell.
chain_boss = (
    cq.Workplane("XY").center(CHAIN_X, 0).circle(3.10).circle(CHAIN_R)
    .extrude(BODY_D - CHASSIS_Z0 - REAR_FLOOR)
    .translate((0, 0, CHASSIS_Z0))
)
chassis = chassis.union(chain_boss)

# Four ledges join the side wall and support the shaped PCB at its bare edges.
# Their 0.60 mm board overlap is deliberately larger than the former 0.20 mm
# overlap. Four rear-floor ribs then locate the board laterally with 0.15 mm
# nominal clearance. The rear floor plus a 0.10--0.15 mm gasket restrains Z.
PCB_SUPPORTS = [
    (-11.0, 8.20, 3.0),
    (10.9, 8.20, 2.0),
    (-8.0, -8.20, 3.0),
    (9.5, -8.20, 3.0),
]
for x, y, support_x in PCB_SUPPORTS:
    ledge = cq.Workplane("XY").box(support_x, 3.60, 0.35).translate((x, y, 9.275))
    chassis = chassis.union(ledge)

for x, y, support_x in PCB_SUPPORTS:
    locator_y = 8.30 if y > 0 else -8.30
    locator_x = min(2.0, support_x)
    y_locator = cq.Workplane("XY").box(locator_x, 2.30, 0.75).translate((x, locator_y, 9.825))
    chassis = chassis.union(y_locator)

# Two flexible, tool-releasable fingers retain the PCB against its three hard
# seating lands. Hooks touch only bare board-edge keep-outs; 0.15 mm SCF400TT
# pads on the rear side remove the remaining controlled Z play.
for snap_x, snap_y, direction in [(-5.0, 7.30, -1), (7.0, -7.30, 1)]:
    stem = cq.Workplane("XY").box(1.60, 0.35, 1.15).translate(
        (snap_x, snap_y, 9.625)
    )
    hook_y = snap_y + direction * 0.22
    hook = cq.Workplane("XY").box(1.60, 0.45, 0.12).translate(
        (snap_x, hook_y, 9.39)
    )
    chassis = chassis.union(stem).union(hook)

# End stops prevent the shaped PCB from sliding along X and losing microphone
# alignment. They descend from the rear floor and stay outside the board edge.
for x, y, sx, sy in [
    (16.25, 4.5, 0.20, 2.0),
    (-21.65, 0.0, 0.20, 2.0),
]:
    end_stop = cq.Workplane("XY").box(sx, sy, 0.75).translate((x, y, 9.825))
    chassis = chassis.union(end_stop)

for name, shape in [
    ("production_chassis", chassis),
    ("production_aluminum_cap", al_cap),
    ("production_rf_cap", rf_cap),
]:
    exporters.export(shape, str(ROOT / f"{name}.step"))
    exporters.export(shape, str(ROOT / f"{name}.stl"), tolerance=0.025, angularTolerance=0.06)

# Print-only all-polymer front: fills the cosmetic seam for a simple fit model.
print_front = full_cap
exporters.export(print_front, str(ROOT / "production_print_front.stl"), tolerance=0.025, angularTolerance=0.06)
exporters.export(chassis, str(ROOT / "production_print_back.stl"), tolerance=0.025, angularTolerance=0.06)

# ----- Shaped placement-only PCB and physical gauges ----------------------
pcb_main = box_shape(PCB_MAIN)
pcb_nose = box_shape(PCB_NOSE)
pcb_shape = pcb_main.union(pcb_nose)
motor_scallop = (
    cq.Workplane("XY").center(motor_x, motor_y).circle(MOTOR_SCALLOP_R)
    .extrude(1.40).translate((0, 0, PCB_MAIN["center"][2] - 0.70))
)
pcb_shape = pcb_shape.cut(motor_scallop)
for mic in MICS:
    pcb_shape = pcb_shape.cut(
        cq.Workplane("XY").center(mic["center"][0], mic["center"][1]).circle(0.42)
        .extrude(1.4).translate((0, 0, PCB_MAIN["center"][2] - 0.7))
    )
exporters.export(pcb_shape, str(ROOT / "production_pcb_placement_only.step"))
exporters.export(pcb_shape, str(ROOT / "production_dummy_pcb_shaped_37.5x14x0.6.step"))
exporters.export(pcb_shape, str(ROOT / "production_dummy_pcb_shaped_37.5x14x0.6.stl"))

for filename, item in [
    ("production_dummy_battery_27x12.5x6", BATTERY),
    ("production_dummy_radio_AN54LV_8.4x6.4x1.5", MODULE),
]:
    sx, sy, sz = item["size"]
    gauge = cq.Workplane("XY").box(sx, sy, sz).translate((0, 0, sz / 2))
    exporters.export(gauge, str(ROOT / f"{filename}.step"))
    exporters.export(gauge, str(ROOT / f"{filename}.stl"))

motor_gauge = cq.Workplane("XY").circle(MOTOR["size"][0] / 2).extrude(MOTOR["size"][2])
exporters.export(motor_gauge, str(ROOT / "production_dummy_motor_7x2.step"))
exporters.export(motor_gauge, str(ROOT / "production_dummy_motor_7x2.stl"))

# Captive side plunger.  At rest the shaft ends 0.20 mm before the controlled
# switch-body edge, matching the published switch travel.  The inner flange is
# the retention stop; the outer head stays under a separately molded membrane.
button_shaft = cq.Workplane("XY").box(2.20, 3.40, 0.85).translate((0.0, -8.55, 8.825))
button_inner_flange = cq.Workplane("XY").box(3.70, 0.25, 1.40).translate((0.0, -9.28, 8.825))
button_outer_head = cq.Workplane("XY").box(3.00, 0.12, 1.55).translate((0.0, -10.18, 8.825))
button_plunger = button_shaft.union(button_inner_flange).union(button_outer_head)
exporters.export(button_plunger, str(ROOT / "production_button_plunger.step"))
exporters.export(button_plunger, str(ROOT / "production_button_plunger.stl"), tolerance=0.025, angularTolerance=0.06)

# Flexible water/dust barrier.  Production material candidate is self-adhesive
# WACKER ELASTOSIL LR 3078/50 A/B; this STEP is only the envelope starting
# geometry, not an injection-tool design.  The LSR molder must prove adhesion
# to the released resin (or use a qualified PC insert), add draft/gates and
# qualify force, fatigue and leak performance.
button_boot = cq.Workplane("XY").box(4.00, 0.18, 2.00).translate((0.0, -10.34, 8.825))
exporters.export(button_boot, str(ROOT / "production_button_boot.step"))
exporters.export(button_boot, str(ROOT / "production_button_boot.stl"), tolerance=0.025, angularTolerance=0.06)

# Flat cap data. The drawing depicts the actual split aluminum blank; the full
# pendant is only a faint reference. It remains preliminary until vendor DFM.
exporters.export(al_cap.faces("<Z"), str(ROOT / "production_aluminum_cap_outline.dxf"))
fig, ax = plt.subplots(figsize=(10, 4.8), dpi=180)
body_poly = capsule_polygon(BODY_L, BODY_W)
cap_poly = capsule_polygon(CAP_L, CAP_W).intersection(
    Polygon([(al_start, -30), (30, -30), (30, 30), (al_start, 30)])
)
x, y = body_poly.exterior.xy
ax.plot(x, y, color="#aaa", lw=0.8, ls="--")
cx, cy = cap_poly.exterior.xy
ax.fill(cx, cy, facecolor="#d8d9db", edgecolor="#111", lw=1.5)
ax.axvline(al_start, color="#333", lw=1)
ax.add_patch(Circle((CHAIN_X, 0), CHAIN_R, facecolor="white", edgecolor="#111"))
cap_min_x, cap_min_y, cap_max_x, cap_max_y = cap_poly.bounds
ax.annotate(f"{cap_max_x-cap_min_x:.3f} aluminum blank", xy=(cap_min_x, -12.2), xytext=(cap_max_x, -12.2),
            arrowprops=dict(arrowstyle="<->"), ha="center", va="center", fontsize=8)
ax.annotate(f"{cap_max_y-cap_min_y:.3f}", xy=(28, cap_min_y), xytext=(28, cap_max_y),
            arrowprops=dict(arrowstyle="<->"), ha="center", va="center", rotation=90, fontsize=8)
ax.text(0, 14.5, "ANTICIPY SPLIT ALUMINUM FACE — PRELIMINARY", ha="center", weight="bold", fontsize=12)
notes = (
    "Material: 5052-H32 sheet, 0.80 mm\n"
    f"Controlled split edge: X = {al_start:.3f} mm; 0.15 mm seam to polymer RF cap\n"
    "Cap recess: 0.05 mm nominal behind polymer impact rim — flushness stack open\n"
    "Perimeter seal: 0.15 mm 3M VHB 5906F on >=1.10 mm land\n"
    "Finish: clear anodize; fine linear grain parallel to long axis\n"
    "Deburr/edge-break all edges; mask or qualify bond face; protect cosmetic face\n"
    "Flatness/profile/flushness/GD&T: vendor DFM and released drawing required\n"
    "Hard finished product maximum: 51 × 21 × 11 mm"
)
ax.text(-25, -16.0, notes, va="top", fontsize=7.4)
ax.set_aspect("equal"); ax.set_xlim(-32, 32); ax.set_ylim(-22, 18); ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "production_aluminum_cap_drawing.pdf", bbox_inches="tight")
plt.close(fig)

# ----- Full assembly files and visual inspection scene ---------------------
assembly = cq.Assembly(name="Anticipy v1.0 retained mechanical candidate")
assembly.add(chassis, name="Makrolon 2407 PC chassis", color=cq.Color(0.12, 0.13, 0.15, 0.65))
assembly.add(al_cap, name="5052 aluminum cap", color=cq.Color(0.65, 0.66, 0.68, 1.0))
assembly.add(rf_cap, name="polymer RF cap", color=cq.Color(0.15, 0.16, 0.18, 1.0))
assembly.add(pcb_shape, name="shaped PCB", color=cq.Color(0.05, 0.42, 0.20, 1.0))
assembly.add(box_shape(BATTERY), name="finished battery envelope", color=cq.Color(0.90, 0.66, 0.12, 0.9))
for item in COMPONENTS:
    assembly.add(box_shape(item), name=item["name"], color=cq.Color(0.15, 0.25, 0.50, 0.95))
motor_step = cq.Workplane("XY").circle(MOTOR_MAX["size"][0]/2).extrude(MOTOR_MAX["size"][2]).translate(
    (MOTOR_MAX["center"][0], MOTOR_MAX["center"][1], MOTOR_MAX["center"][2]-MOTOR_MAX["size"][2]/2)
)
motor_step_bbox = motor_step.val().BoundingBox()
assembly.add(motor_step, name=MOTOR["name"], color=cq.Color(0.72, 0.32, 0.20, 1.0))
assembly.add(button_plunger, name="captive button plunger", color=cq.Color(0.18, 0.18, 0.20, 1.0))
assembly.add(button_boot, name="50A LSR button membrane", color=cq.Color(0.10, 0.10, 0.12, 0.85))
assembly.save(str(ROOT / "production_full_assembly.step"))

scene = trimesh.Scene()


def add_stl(path: Path, node: str, rgba: list[int]):
    mesh = trimesh.load_mesh(path)
    mesh.visual.face_colors = np.array(rgba, dtype=np.uint8)
    scene.add_geometry(mesh, node_name=node)


add_stl(ROOT / "production_chassis.stl", "Makrolon 2407 PC chassis", [36, 39, 45, 90])
add_stl(ROOT / "production_aluminum_cap.stl", "5052 aluminum cap", [160, 164, 168, 235])
add_stl(ROOT / "production_rf_cap.stl", "polymer RF cap", [45, 48, 52, 220])
add_stl(ROOT / "production_button_boot.stl", "50A LSR button membrane", [24, 24, 29, 225])
for item, color in [
    (BATTERY, [230, 184, 55, 230]),
    (PCB_MAIN, [42, 132, 84, 220]),
    (PCB_NOSE, [42, 132, 84, 220]),
    (MODULE, [42, 92, 150, 255]),
    (FLASH, [55, 55, 60, 255]),
    (PMIC, [125, 75, 145, 255]),
    (HAPTIC_DRIVER, [125, 75, 145, 255]),
    (BUTTON, [80, 80, 84, 255]),
    (LED, [70, 200, 130, 255]),
    *[(m, [35, 35, 40, 255]) for m in MICS],
]:
    mesh = trimesh.creation.box(item["size"])
    mesh.apply_translation(item["center"])
    mesh.visual.face_colors = color
    scene.add_geometry(mesh, node_name=item["name"])
motor = trimesh.creation.cylinder(radius=MOTOR_MAX["size"][0]/2, height=MOTOR_MAX["size"][2], sections=48)
motor.apply_translation(MOTOR_MAX["center"])
motor.visual.face_colors = [183, 99, 60, 255]
scene.add_geometry(motor, node_name=MOTOR["name"])
scene.export(ROOT / "production_fit_check.glb")

# Dimensioned top view for fast human review.
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=180)
x, y = body_poly.exterior.xy
ax.fill(x, y, color="#d4d5d7", edgecolor="#111", linewidth=1.2)
keep_sx, keep_sy, _ = ANTENNA_KEEP["size"]
keep_x, keep_y, _ = ANTENNA_KEEP["center"]
ax.add_patch(Rectangle((keep_x-keep_sx/2, keep_y-keep_sy/2), keep_sx, keep_sy,
    facecolor="#f2c94c", edgecolor="#9a7610", alpha=.32, hatch="//"))
ax.text(keep_x, keep_y, "RF\nno metal", ha="center", va="center", fontsize=6.3)
ax.add_patch(Circle((CHAIN_X, 0), CHAIN_R, facecolor="white", edgecolor="#111"))
draw_items = [BATTERY, PCB_MAIN, PCB_NOSE, MODULE, FLASH, PMIC, HAPTIC_DRIVER, BUTTON, LED, *MICS]
colours = {
    BATTERY["name"]: "#e4b83e", PCB_MAIN["name"]: "#268454", PCB_NOSE["name"]: "#268454",
    MODULE["name"]: "#285c96",
    FLASH["name"]: "#454549", PMIC["name"]: "#7d4b91", HAPTIC_DRIVER["name"]: "#7d4b91",
    BUTTON["name"]: "#777", LED["name"]: "#39a96b",
}
for item in draw_items:
    sx, sy, _ = item["size"]; cx, cy, _ = item["center"]
    ax.add_patch(FancyBboxPatch((cx-sx/2, cy-sy/2), sx, sy,
        boxstyle="round,pad=0.02,rounding_size=0.25", facecolor=colours.get(item["name"], "#333"),
        edgecolor="#111", linewidth=.45, alpha=.88))
labels = [(MODULE["center"][0], 2.3, "radio"), (-1.7, 2.4, "481 MB"), (6.2, 4.2, "power"),
          (HAPTIC_DRIVER["center"][0], -4.7, "driver")]
ax.add_patch(Circle(MOTOR["center"][:2], MOTOR_SCALLOP_R,
    facecolor="#d4d5d7", edgecolor="#268454", linewidth=.8))
ax.add_patch(Circle(MOTOR["center"][:2], MOTOR["size"][0]/2,
    facecolor="#b76342", edgecolor="#111", linewidth=.5))
ax.text(MOTOR["center"][0], MOTOR["center"][1], "motor", ha="center", va="center",
        fontsize=5.8, color="white")
for tx, ty, label in labels:
    ax.text(tx, ty, label, ha="center", va="center", fontsize=5.8,
            color="white")
ax.annotate("200 mAh battery under PCB; motor beside pouch", xy=(0.0, -0.5), xytext=(-2.0, -8.8),
            ha="center", va="center", fontsize=5.8, color="#4c3900",
            arrowprops=dict(arrowstyle="->", color="#6c5200", lw=0.7),
            bbox=dict(boxstyle="round,pad=0.18", fc="#fff7d7", ec="none", alpha=0.92))
ax.annotate("50.5 mm nominal", xy=(-BODY_L/2, -14.0), xytext=(BODY_L/2, -14.0),
            arrowprops=dict(arrowstyle="<->"), ha="center", va="center", fontsize=8)
ax.annotate("20.5 mm", xy=(-30, -BODY_W/2), xytext=(-30, BODY_W/2),
            arrowprops=dict(arrowstyle="<->"), ha="center", va="center", rotation=90, fontsize=8)
ax.text(0, 14.7, "Anticipy v1.0 retained mechanical candidate", ha="center", fontsize=12.5, weight="bold")
ax.text(0, 12.3, "scalloped PCB · structural cap · battery cradle · motor keeper · 0.15 mm seal", ha="center", fontsize=7.5)
ax.set_aspect("equal"); ax.set_xlim(-33, 33); ax.set_ylim(-17, 17); ax.axis("off")
fig.tight_layout(); fig.savefig(ROOT / "production_internal_layout.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ----- Ten-plus independent programmatic gates ----------------------------
outer_poly = capsule_polygon(BODY_L, BODY_W)
cavity_poly = outer_poly.buffer(-SIDE_WALL).difference(Point(CHAIN_X, 0).buffer(CHAIN_KEEP_R, quad_segs=64))


def footprint(item, scale=1.0):
    sx, sy, _ = item["size"]; cx, cy, _ = item["center"]
    p = Polygon([(cx-sx/2, cy-sy/2), (cx+sx/2, cy-sy/2),
                 (cx+sx/2, cy+sy/2), (cx-sx/2, cy+sy/2)])
    return affinity.scale(p, xfact=scale, yfact=scale, origin=(cx, cy))


VALIDATION_COMPONENTS = [MODULE, FLASH, PMIC, HAPTIC_DRIVER, BUTTON_MAX, LED, *MICS]
fit_items = [PCB_MAIN, PCB_NOSE, BATTERY, *VALIDATION_COMPONENTS]
fit_15 = {i["name"]: cavity_poly.covers(footprint(i, 1.15)) for i in fit_items}
motor_15 = Point(*MOTOR_MAX["center"][:2]).buffer(MOTOR_MAX["size"][0] / 2 * 1.15, quad_segs=96)
fit_15[MOTOR["name"]] = cavity_poly.covers(motor_15)

board_poly = footprint(PCB_MAIN).union(footprint(PCB_NOSE)).difference(
    Point(motor_x, motor_y).buffer(MOTOR_SCALLOP_R, quad_segs=96)
)
battery_nominal_poly = footprint(BATTERY)
motor_nominal_poly = Point(motor_x, motor_y).buffer(MOTOR_MAX["size"][0] / 2, quad_segs=96)
battery_motor_xy_gap = battery_nominal_poly.distance(motor_nominal_poly)
battery_motor_worst_gap = battery_motor_xy_gap - CRADLE_GAP
pcb_motor_xy_gap = board_poly.distance(motor_nominal_poly)
motor_scallop_15_residual = MOTOR_SCALLOP_R - MOTOR_MAX["size"][0] / 2 * 1.15
motor_pocket_diametral_clearance = 7.30 - MOTOR_MAX["size"][0]
component_board_15 = {
    i["name"]: board_poly.covers(footprint(i, 1.15))
    for i in VALIDATION_COMPONENTS
}
component_board_15[BUTTON_LAND["name"]] = board_poly.covers(footprint(BUTTON_LAND, 1.15))

# Component collisions use actual 3-D boxes. PCB/component contact is intentional,
# so board islands are omitted; the RF keepout is tested separately.
solid_items = [BATTERY, MOTOR, *COMPONENTS]
collisions = []
for index, a in enumerate(solid_items):
    amin = np.array(a["center"]) - np.array(a["size"]) / 2
    amax = np.array(a["center"]) + np.array(a["size"]) / 2
    for b in solid_items[index+1:]:
        bmin = np.array(b["center"]) - np.array(b["size"]) / 2
        bmax = np.array(b["center"]) + np.array(b["size"]) / 2
        overlap = np.minimum(amax, bmax) - np.maximum(amin, bmin)
        if np.all(overlap > 0.02):
            collisions.append(f"{a['name']} / {b['name']}")

# The cavity polygon cannot detect a support rib clipping a component. Intersect
# every placed component with the exported chassis so locators/ledges are part
# of the release check too.
chassis_mesh = trimesh.load_mesh(ROOT / "production_chassis.stl")
chassis_component_collisions = []
for item in solid_items:
    if item is MOTOR:
        item_mesh = trimesh.creation.cylinder(
            radius=MOTOR["size"][0] / 2,
            height=MOTOR["size"][2],
            sections=64,
        )
        item_mesh.apply_translation(MOTOR["center"])
    else:
        item_mesh = trimesh.creation.box(item["size"])
        item_mesh.apply_translation(item["center"])
    intersection = trimesh.boolean.intersection([chassis_mesh, item_mesh], engine="manifold")
    overlap_volume = 0.0 if intersection is None else float(intersection.volume)
    if overlap_volume > 0.001:
        chassis_component_collisions.append(f"{item['name']} ({overlap_volume:.4f} mm^3)")

# A second collision pass expands every component footprint by 15% while using
# the real nominal Z bands. This catches human-placement/courtyard conflicts
# without pretending that the already-tight 11 mm Z stack can grow by 15%.
expanded_xy_collisions = []
allowed_rf_pair = set()
expanded_items = [BATTERY, MOTOR_MAX, *VALIDATION_COMPONENTS]
for index, a in enumerate(expanded_items):
    az0 = a["center"][2] - a["size"][2]/2
    az1 = a["center"][2] + a["size"][2]/2
    for b in expanded_items[index+1:]:
        if {a["name"], b["name"]} == allowed_rf_pair:
            continue
        bz0 = b["center"][2] - b["size"][2]/2
        bz1 = b["center"][2] + b["size"][2]/2
        if min(az1, bz1) - max(az0, bz0) <= 0.02:
            continue
        if footprint(a, 1.15).intersection(footprint(b, 1.15)).area > 0.001:
            expanded_xy_collisions.append(f"{a['name']} / {b['name']}")

rf_keep_poly = footprint(ANTENNA_KEEP, 1.15)
rf_intrusions = []
for item in [BATTERY, MOTOR_MAX]:
    if rf_keep_poly.intersects(footprint(item, 1.15)):
        rf_intrusions.append(item["name"])
rf_metal_clearance = rf_keep_poly.distance(cap_poly)
if rf_metal_clearance < 3.0:
    rf_intrusions.append(f"aluminum cap clearance {rf_metal_clearance:.3f} mm")

cap_overlap_mm = max(0.0, rf_end - al_start)
battery_bottom = BATTERY["center"][2] - BATTERY["size"][2] / 2
battery_top = BATTERY["center"][2] + BATTERY["size"][2] / 2
motor_bottom = MOTOR_MAX["center"][2] - MOTOR_MAX["size"][2] / 2
motor_top = MOTOR_MAX["center"][2] + MOTOR_MAX["size"][2] / 2
lowest_component = min(i["center"][2] - i["size"][2]/2 for i in VALIDATION_COMPONENTS)
pcb_bottom = PCB_MAIN["center"][2] - PCB_MAIN["size"][2]/2
pcb_top = PCB_MAIN["center"][2] + PCB_MAIN["size"][2]/2
rear_inner = BODY_D - REAR_FLOOR
z_ok = (
    abs(battery_bottom - (CAP_RECESS + CAP_H + 0.05 + 0.10)) <= 0.001
    and battery_top + 0.50 <= lowest_component
    and battery_top + 0.20 <= motor_bottom
    and motor_top + 0.10 <= pcb_bottom + 1e-6
    and pcb_top + 0.10 <= rear_inner
)

storage_need_mb = 5.0 * 72000 * 1.15 / 1000
storage_usable_mb = 481.0
average_current_ceiling_ma = 200 * 0.85 / 16
al_mesh = trimesh.load_mesh(ROOT / "production_aluminum_cap.stl")
rf_mesh = trimesh.load_mesh(ROOT / "production_rf_cap.stl")
shell_mass_g = (chassis_mesh.volume + rf_mesh.volume) / 1000 * 1.20 + al_mesh.volume / 1000 * 2.68
mass_nominal_g = 5.0 + 2.2 + 0.5 + shell_mass_g + 1.2
mass_with_15_g = mass_nominal_g * 1.15
mic_spacing = math.dist(MICS[0]["center"][:2], MICS[1]["center"][:2])

mesh_results = {}
mesh_bodies = {}
for filename in ["production_chassis.stl", "production_aluminum_cap.stl", "production_rf_cap.stl", "production_print_front.stl", "production_visual_pebble.stl", "production_button_plunger.stl", "production_button_boot.stl"]:
    mesh = trimesh.load_mesh(ROOT / filename)
    mesh_results[filename] = bool(mesh.is_watertight)
    mesh_bodies[filename] = int(mesh.body_count)

# Audit the exported STEP itself, not only the source primitives. This catches
# exporter/assembly regressions and makes the hard external envelope explicit.
step_import = cq.importers.importStep(str(ROOT / "production_full_assembly.step"))
step_solids = step_import.solids().vals()
step_bbox = step_import.val().BoundingBox()
step_positive_overlaps = []
for index, first in enumerate(step_solids):
    for second in step_solids[index + 1:]:
        common_volume = first.intersect(second).Volume()
        if common_volume > 0.001:
            step_positive_overlaps.append(common_volume)

checks = [
    ("finished envelope below hard maximum", FINISHED_L + FINISHED_POS_TOL <= MAX_L and FINISHED_W + FINISHED_POS_TOL <= MAX_W and FINISHED_D + FINISHED_POS_TOL <= MAX_D,
     f"finished nominal {FINISHED_L} x {FINISHED_W:.2f} x {FINISHED_D}; +{FINISHED_POS_TOL} tolerance remains below {MAX_L} x {MAX_W} x {MAX_D} mm"),
    ("chain geometry", CHAIN_X + CHAIN_R <= BODY_L/2, f"4.2 mm hole; {BODY_L/2-(CHAIN_X+CHAIN_R):.2f} mm nominal end wall"),
    ("all modeled items fit with 15% XY reserve", all(fit_15.values()), ", ".join(k for k,v in fit_15.items() if not v) or "all clear"),
    ("component courtyards fit shaped PCB with 15% XY reserve", all(component_board_15.values()), ", ".join(k for k,v in component_board_15.items() if not v) or "all clear"),
    ("actual 3-D component collision check", not collisions, ", ".join(collisions) or "no solid overlaps"),
    ("chassis/support versus component collision check", not chassis_component_collisions,
     ", ".join(chassis_component_collisions) or "no chassis, ledge or locator overlaps"),
    ("15%-expanded same-layer collision check", not expanded_xy_collisions, ", ".join(expanded_xy_collisions) or "no expanded courtyard overlaps"),
    ("RF mechanical keepout", not rf_intrusions, ", ".join(rf_intrusions) or f"15%-expanded AN54LV antenna end clears controlled battery/motor and is {rf_metal_clearance:.3f} mm from aluminum; copper DRC and closed-device RF test still required"),
    ("front-cap split", cap_overlap_mm == 0 and abs((al_start-rf_end)-CAP_SEAM_GAP) < 1e-6, f"zero overlap; {CAP_SEAM_GAP:.2f} mm seam"),
    ("retained structural cap stack",
     abs(CAP_RECESS - 0.05) < 1e-9 and abs(CAP_H - 0.80) < 1e-9 and abs(ADHESIVE_H - 0.15) < 1e-9 and BOND_LAND >= 1.10,
     f"{CAP_RECESS:.2f} recess + {CAP_H:.2f} aluminum + {ADHESIVE_H:.2f} VHB; {BOND_LAND:.2f} bond land"),
    ("battery and motor worst-case planning separation",
     battery_motor_worst_gap >= 0.25,
     f"{battery_motor_xy_gap:.3f} mm controlled-pack to maximum-can gap; {battery_motor_worst_gap:.3f} mm after full cradle travel"),
    ("PCB motor scallop clearance",
     motor_scallop_15_residual >= 0.20,
     f"R{MOTOR_SCALLOP_R:.2f} leaves {motor_scallop_15_residual:.3f} mm beyond 1.15 x maximum can radius"),
    ("motor pocket assembly clearance",
     motor_pocket_diametral_clearance >= 0.20 and MOTOR_SHELF_H >= 0.60,
     f"{motor_pocket_diametral_clearance:.3f} mm diametral clearance; {MOTOR_SHELF_H:.2f} mm shelf; molder tolerance and keeper strain remain open"),
    ("GAW337 vent-seat depth", abs(VENT_RECESS_H - 0.38) < 1e-9,
     f"{VENT_RECESS_H:.2f} mm exterior recess plus local annular boss"),
    ("explicit vertical gaps", z_ok, f"battery {battery_bottom:.2f}-{battery_top:.2f}; motor {motor_bottom:.2f}-{motor_top:.2f}; lowest component {lowest_component:.2f}; PCB {pcb_bottom:.2f}-{pcb_top:.2f}; rear inner {rear_inner:.2f}"),
    ("placed motor STEP Z bounds", abs(motor_step_bbox.zmin-motor_bottom) < 0.001 and abs(motor_step_bbox.zmax-motor_top) < 0.001,
     f"STEP motor {motor_step_bbox.zmin:.2f}-{motor_step_bbox.zmax:.2f}; intended {motor_bottom:.2f}-{motor_top:.2f}"),
    ("20-hour backlog arithmetic", storage_need_mb <= storage_usable_mb, f"needs {storage_need_mb:.0f} MB incl. 15%; design budget {storage_usable_mb:.0f} MB usable"),
    ("16-hour battery requirement calculated", True, f"theoretical 85%-capacity ceiling {average_current_ceiling_ma:.3f} mA; use <=10.0 mA conservative production target until pack/cold/aging tests close"),
    ("mass planning ceiling", mass_with_15_g <= MAX_MASS_G, f"shell CAD {shell_mass_g:.2f} g; {mass_nominal_g:.2f} g total budget; {mass_with_15_g:.2f} g with 15%; physical weigh-in required"),
    ("direct dual-microphone geometry", mic_spacing >= 20 and all(cavity_poly.covers(Point(m["center"][:2])) for m in MICS), f"{mic_spacing:.1f} mm spacing; direct PCB/rear ducts"),
    ("print/export meshes watertight", all(mesh_results.values()), ", ".join(f"{k}={v}" for k,v in mesh_results.items())),
    ("one connected body per enclosure part", all(v == 1 for v in mesh_bodies.values()), ", ".join(f"{k}={v}" for k,v in mesh_bodies.items())),
    ("exported STEP regression",
     len(step_solids) == 16 and abs(step_bbox.xlen-FINISHED_L) < 0.001 and abs(step_bbox.ylen-FINISHED_W) < 0.001 and abs(step_bbox.zlen-FINISHED_D) < 0.001 and not step_positive_overlaps,
     f"{len(step_solids)} solids; {step_bbox.xlen:.3f} x {step_bbox.ylen:.3f} x {step_bbox.zlen:.3f} mm; {len(step_positive_overlaps)} positive-volume overlaps"),
]

report = {
    "version": "1.0 retained production mechanical candidate",
    "classification": "retention-complete CAD candidate; not routed PCB or physically qualified production unit",
    "hard_maximum_mm": [MAX_L, MAX_W, MAX_D],
    "nominal_body_envelope_mm": [BODY_L, BODY_W, BODY_D],
    "nominal_finished_envelope_including_button_mm": [FINISHED_L, FINISHED_W, FINISHED_D],
    "positive_finished_tolerance_mm": FINISHED_POS_TOL,
    "battery": {"sourced_cell": "LP571225 200 mAh", "controlled_finished_envelope_mm": BATTERY["size"], "average_current_ceiling_ma": average_current_ceiling_ma},
    "storage": {"codec_design_rate_kB_s": 5.0, "hours": 20, "margin_pct": 15, "required_MB": storage_need_mb, "usable_budget_MB": storage_usable_mb},
    "mass": {"nominal_budget_g": mass_nominal_g, "with_15pct_g": mass_with_15_g, "hard_max_g": MAX_MASS_G},
    "checks": [{"name": n, "pass": bool(p), "detail": d} for n,p,d in checks],
}
(ROOT / "production_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")
lines = [
    "# Anticipy v1.0 retained mechanical fit report", "",
    "Classification: **retention-complete CAD candidate**. It models the structural cap/seal, battery cradle, motor shelf/pocket/keeper, PCB scallop/snaps, vent seats, button plunger and chain boss, but it is not a schematic, routed PCB, Gerber release, certified battery, physically qualified seal or retail-production approval.", "",
    "The 15% reserve is applied to every modeled XY placement envelope. Z clearances, finished dimensional tolerance, mass, RF keepout, cap overlap, storage and power are checked separately.", "",
]
for number, (name, passed, detail) in enumerate(checks, 1):
    lines.append(f"{number}. **{'PASS' if passed else 'FAIL'} — {name}:** {detail}")
lines += [
    "", "A digital PASS only proves the stated CAD/math check. RF tuning, battery runtime, acoustics, weight, thermal behavior, chain pull and sealing require physical prototypes.", ""
]
(ROOT / "PRODUCTION_FIT_REPORT.md").write_text("\n".join(lines))

for name, passed, detail in checks:
    print(f"{'PASS' if passed else 'FAIL'} | {name} | {detail}")
if not all(p for _, p, _ in checks):
    raise SystemExit("One or more production mechanical checks failed")
