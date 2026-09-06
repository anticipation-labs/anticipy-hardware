#!/usr/bin/env python3
"""Generate the Anticipy v1.3 rugged no-custom-PCB prototype enclosure.

This is a hand-assembled engineering prototype, not a customer-production
enclosure.  It is locked to these controlled parts:

* Seeed XIAO nRF52840 Sense (21.0 x 17.8 mm)
* Adafruit 5683 microSD BFF, directly stacked behind the XIAO
* BBM Battery 602535 protected 500 mAh pouch (35 x 25 x 6 mm)
* Vybronics VCLP1020B002L 10 x 2.1 mm ERM
* B3U-1000P low-profile momentary switch
* insulated, laid-flat discrete MOSFET haptic cluster (12 x 8 x 4 mm max)

The enclosure uses thick PLA walls, two screw posts, positive component bays,
soft-foam shimming and a print-flat reinforced necklace loop.  All dimensions
are millimetres.
"""

from pathlib import Path
import json
import math

import cadquery as cq
from cadquery import exporters
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle
from shapely.geometry import Point, box as shapely_box
import trimesh


ROOT = Path(__file__).resolve().parent

# Exterior.  The 68 mm body is 2 mm shorter than v1.2.  The loop overlaps the
# end of the body instead of being perched on a thin neck, so it prints in the
# XY plane and cannot snap off at a one-line bridge.
BODY_L = 68.0
BODY_W = 33.0
BODY_D = 16.5
CORNER_R = 8.0
WALL = 1.6
FLOOR = 1.6
BASE_TOP = 14.4
LID_SKIN = BODY_D - BASE_TOP
LIP_DEPTH = 0.75

BATTERY = {
    "name": "BBM 602535 protected 500 mAh battery",
    "size": [35.0, 25.0, 6.0],
    "center": [-10.3, 0.0, FLOOR + 0.5 + 3.0],
    "mass_g": 9.0,
}
BOARD = {
    "name": "XIAO nRF52840 Sense plus microSD BFF stack",
    # 0.8 mm XY reserve is already included around the nominal board.
    # 9.6 mm Z accepts direct soldering or carefully trimmed short headers.
    "size": [18.6, 21.8, 9.6],
    "center": [21.0, 0.0, FLOOR + 0.5 + 4.8],
    "mass_g": 4.5,
}
MOTOR = {
    "name": "Vybronics VCLP1020B002L haptic motor",
    "size": [10.0, 10.0, 2.1],
    "center": [-19.5, 0.0, BASE_TOP - 0.25 - 1.05],
    "mass_g": 0.9,
}
DRIVER = {
    "name": "laid-flat insulated haptic driver cluster",
    "size": [12.0, 8.0, 4.0],
    "center": [-3.0, 5.5, BASE_TOP - 0.25 - 2.0],
    "mass_g": 0.6,
}
BUTTON = {
    "name": "B3U-1000P user button",
    "size": [3.0, 2.5, 1.6],
    "center": [3.0, -6.0, BASE_TOP - 0.2 - 0.8],
    "mass_g": 0.1,
}
PARTS = [BATTERY, BOARD, MOTOR, DRIVER, BUTTON]

SCREWS = [(-32.0, 0.0), (32.0, 0.0)]
MIC_XY = (25.8, 7.2)
LED_XY = (25.8, -7.0)


def rounded_rect(length, width, radius, height, z0=0.0):
    return (
        cq.Workplane("XY")
        .sketch()
        .rect(length, width)
        .vertices()
        .fillet(radius)
        .finalize()
        .extrude(height)
        .translate((0, 0, z0))
    )


def cyl(x, y, radius, height, z0=0.0):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z0))


def item_box(item):
    return cq.Workplane("XY").box(*item["size"]).translate(tuple(item["center"]))


# ---------------------------------------------------------------------------
# Base tray
# ---------------------------------------------------------------------------
outer = rounded_rect(BODY_L, BODY_W, CORNER_R, BASE_TOP)
inner = rounded_rect(
    BODY_L - 2 * WALL,
    BODY_W - 2 * WALL,
    CORNER_R - WALL,
    BASE_TOP - FLOOR + 0.2,
    FLOOR,
)
base = outer.cut(inner)

# Strong necklace eye printed in the same plane as the tray.  It overlaps the
# body by 5.5 mm and has 3 mm of material around a 4 mm opening.
loop_cx = -33.0
loop_outer = cyl(loop_cx, 0.0, 5.0, BASE_TOP)
loop_hole = cyl(loop_cx, 0.0, 2.0, BASE_TOP + 1.0, -0.5)
base = base.union(loop_outer).cut(loop_hole)

# End screw posts.  Only M1.4 x 5 mm thread-forming screws are allowed.
for sx, sy in SCREWS:
    post = cyl(sx, sy, 1.55, BASE_TOP - FLOOR, FLOOR)
    pilot = cyl(sx, sy, 0.55, 4.0, BASE_TOP - 3.8)
    base = base.union(post.cut(pilot))

# Battery rails: 0.55 mm nominal gap on each edge, then fill any remaining
# looseness with soft 0.8 mm foam strips.  The open end protects the wire tail.
bx, by, _ = BATTERY["center"]
bl, bw, _ = BATTERY["size"]
CLR = 0.55
RAIL_T = 1.20
RAIL_H = 1.60
for rail in [
    cq.Workplane("XY").box(bl + 2 * CLR + 0.4, RAIL_T, RAIL_H).translate(
        (bx, by + bw / 2 + CLR + RAIL_T / 2, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(bl + 2 * CLR + 0.4, RAIL_T, RAIL_H).translate(
        (bx, by - bw / 2 - CLR - RAIL_T / 2, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(RAIL_T, bw + 2 * CLR, RAIL_H).translate(
        (bx - bl / 2 - CLR - RAIL_T / 2, by, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(RAIL_T, 8.0, RAIL_H).translate(
        (bx + bl / 2 + CLR + RAIL_T / 2, by + 8.0, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(RAIL_T, 8.0, RAIL_H).translate(
        (bx + bl / 2 + CLR + RAIL_T / 2, by - 8.0, FLOOR + RAIL_H / 2)
    ),
]:
    base = base.union(rail)

# Board-stack cradle.  The USB and microSD ends remain open.  These rails plus
# a foam floor stop movement without clamping the PCB.
sx, sy, _ = BOARD["center"]
sl, sw, _ = BOARD["size"]
BCLR = 0.35
for rail in [
    cq.Workplane("XY").box(sl + 2 * BCLR, RAIL_T, RAIL_H).translate(
        (sx, sy + sw / 2 + BCLR + RAIL_T / 2, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(sl + 2 * BCLR, RAIL_T, RAIL_H).translate(
        (sx, sy - sw / 2 - BCLR - RAIL_T / 2, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(RAIL_T, 7.0, RAIL_H).translate(
        (sx - sl / 2 - BCLR - RAIL_T / 2, sy, FLOOR + RAIL_H / 2)
    ),
    cq.Workplane("XY").box(RAIL_T, 7.0, RAIL_H).translate(
        (sx + sl / 2 + BCLR + RAIL_T / 2, sy, FLOOR + RAIL_H / 2)
    ),
]:
    base = base.union(rail)

# Generous hand-assembly openings.  A silicone dust plug can be added after
# bring-up; do not seal the first unit until the runtime test passes.
usb_cut = cq.Workplane("XY").box(11.0, 4.0, 5.2).translate((sx, -BODY_W / 2, 4.3))
sd_cut = cq.Workplane("XY").box(14.0, 4.0, 4.8).translate((sx, BODY_W / 2, 4.3))
base = base.cut(usb_cut).cut(sd_cut)


# ---------------------------------------------------------------------------
# Lid
# ---------------------------------------------------------------------------
lid = rounded_rect(BODY_L, BODY_W, CORNER_R, LID_SKIN, BASE_TOP)
try:
    lid = lid.edges(">Z").fillet(1.0)
except Exception:
    pass

# Alignment lip.  0.25 mm radial gap is intentionally forgiving for silk PLA.
lip_outer = rounded_rect(
    BODY_L - 2 * (WALL + 0.25),
    BODY_W - 2 * (WALL + 0.25),
    CORNER_R - WALL - 0.25,
    LIP_DEPTH,
    BASE_TOP - LIP_DEPTH,
)
lip_inner = rounded_rect(
    BODY_L - 2 * (WALL + 0.85),
    BODY_W - 2 * (WALL + 0.85),
    CORNER_R - WALL - 0.85,
    LIP_DEPTH + 0.2,
    BASE_TOP - LIP_DEPTH - 0.1,
)
lip_ring = lip_outer.cut(lip_inner)
# The screw posts sit at the narrow ends.  Relief notches prevent the
# alignment lip from colliding with those posts when the lid is seated.
for sx0, sy0 in SCREWS:
    lip_ring = lip_ring.cut(cyl(sx0, sy0, 1.90, LIP_DEPTH + 0.4, BASE_TOP - LIP_DEPTH - 0.2))
# The reinforced necklace eye overlaps the left end wall.  Remove the short lip
# segment above that overlap; the remaining perimeter still provides alignment.
loop_lip_relief = cq.Workplane("XY").box(6.0, 12.0, LIP_DEPTH + 0.5).translate(
    (-31.4, 0.0, BASE_TOP - LIP_DEPTH / 2)
)
lip_ring = lip_ring.cut(loop_lip_relief)
lid = lid.union(lip_ring)

for sx0, sy0 in SCREWS:
    lid = lid.cut(cyl(sx0, sy0, 0.82, BODY_D + 1.0, -0.5))

# Microphone holes and a broad, support-free gasket chimney.
for dx in (-1.15, 0.0, 1.15):
    lid = lid.cut(cyl(MIC_XY[0] + dx, MIC_XY[1], 0.38, 3.2, BASE_TOP - 0.3))
chimney_bottom = 12.5
chimney_outer = cq.Workplane("XY").box(6.5, 5.5, BASE_TOP - chimney_bottom).translate(
    (MIC_XY[0], MIC_XY[1], (BASE_TOP + chimney_bottom) / 2)
)
chimney_inner = cq.Workplane("XY").box(4.5, 3.5, BASE_TOP - chimney_bottom + 0.4).translate(
    (MIC_XY[0], MIC_XY[1], (BASE_TOP + chimney_bottom) / 2)
)
lid = lid.union(chimney_outer.cut(chimney_inner))

# Motor guard.  Thin 3M tape holds the motor; a polyimide strap is the backup.
motor_bottom = 10.7
motor_outer = cyl(MOTOR["center"][0], MOTOR["center"][1], 6.2, BASE_TOP - motor_bottom, motor_bottom)
motor_inner = cyl(MOTOR["center"][0], MOTOR["center"][1], 5.35, BASE_TOP - motor_bottom + 0.4, motor_bottom - 0.2)
lid = lid.union(motor_outer.cut(motor_inner))

# Laid-flat discrete driver pocket and wire exit.
hx, hy, _ = DRIVER["center"]
driver_bottom = 9.7
driver_outer = cq.Workplane("XY").box(15.0, 11.0, BASE_TOP - driver_bottom).translate(
    (hx, hy, (BASE_TOP + driver_bottom) / 2)
)
driver_inner = cq.Workplane("XY").box(13.0, 9.0, BASE_TOP - driver_bottom + 0.4).translate(
    (hx, hy, (BASE_TOP + driver_bottom) / 2)
)
driver_guard = driver_outer.cut(driver_inner)
driver_notch = cq.Workplane("XY").box(3.0, 4.0, 1.8).translate(
    (hx + 7.0, hy, driver_bottom + 0.9)
)
lid = lid.union(driver_guard.cut(driver_notch))

# Captive user-button plunger.
button_hole = cyl(BUTTON["center"][0], BUTTON["center"][1], 1.30, 3.2, BASE_TOP - 0.3)
button_guard_bottom = 11.1
button_outer = cq.Workplane("XY").box(5.4, 4.8, BASE_TOP - button_guard_bottom).translate(
    (BUTTON["center"][0], BUTTON["center"][1], (BASE_TOP + button_guard_bottom) / 2)
)
button_inner = cq.Workplane("XY").box(3.6, 3.1, BASE_TOP - button_guard_bottom + 0.4).translate(
    (BUTTON["center"][0], BUTTON["center"][1], (BASE_TOP + button_guard_bottom) / 2)
)
lid = lid.union(button_outer.cut(button_inner)).cut(button_hole)

# Status-light hole.
lid = lid.cut(cyl(LED_XY[0], LED_XY[1], 0.65, 3.2, BASE_TOP - 0.3))


# Captive plunger: use 2.0 mm first; 1.8 and 2.2 mm rescue sizes are included.
for length in (1.8, 2.0, 2.2):
    shaft = cq.Workplane("XY").circle(1.10).extrude(length).translate((0, 0, 0.50))
    flange = cq.Workplane("XY").circle(1.80).extrude(0.50)
    plunger = shaft.union(flange)
    exporters.export(plunger, str(ROOT / f"v13_button_plunger_{str(length).replace('.', 'p')}mm.stl"))


# Export controlled CAD.
exporters.export(base, str(ROOT / "v13_rugged_base.step"))
exporters.export(base, str(ROOT / "v13_rugged_base.stl"))
exporters.export(lid, str(ROOT / "v13_rugged_lid.step"))
exporters.export(lid, str(ROOT / "v13_rugged_lid.stl"))

for item, filename in [
    (BATTERY, "v13_dummy_BBM_602535_battery.stl"),
    (BOARD, "v13_dummy_XIAO_SD_stack.stl"),
    (MOTOR, "v13_dummy_Vybronics_motor.stl"),
    (DRIVER, "v13_dummy_haptic_driver.stl"),
    (BUTTON, "v13_dummy_button.stl"),
]:
    exporters.export(cq.Workplane("XY").box(*item["size"]), str(ROOT / filename))


# ---------------------------------------------------------------------------
# Digital verification
# ---------------------------------------------------------------------------
meshes = {}
for stem in ("v13_rugged_base", "v13_rugged_lid", "v13_button_plunger_2p0mm"):
    mesh = trimesh.load_mesh(ROOT / f"{stem}.stl", force="mesh")
    meshes[stem] = {
        "watertight": bool(mesh.is_watertight),
        "bodies": int(len(mesh.split(only_watertight=False))),
        "extents_mm": [round(float(v), 3) for v in mesh.extents],
    }

inner_l = BODY_L - 2 * WALL
inner_w = BODY_W - 2 * WALL
expanded_battery = [v * 1.15 for v in BATTERY["size"]]
expanded_board = [v * 1.15 for v in BOARD["size"]]
batt_left = BATTERY["center"][0] - expanded_battery[0] / 2
batt_right = BATTERY["center"][0] + expanded_battery[0] / 2
board_left = BOARD["center"][0] - expanded_board[0] / 2
board_right = BOARD["center"][0] + expanded_board[0] / 2
expanded_gap = board_left - batt_right

# Exact solid-intersection checks.  The motor is cylindrical; using its square
# bounding box would incorrectly report its empty corner space as a collision.
base_lid_collision = base.intersect(lid).val().Volume()
motor_shape = cyl(
    MOTOR["center"][0], MOTOR["center"][1], MOTOR["size"][0] / 2,
    MOTOR["size"][2], MOTOR["center"][2] - MOTOR["size"][2] / 2,
)
component_shapes = {
    "battery": item_box(BATTERY),
    "board": item_box(BOARD),
    "motor": motor_shape,
    "driver": item_box(DRIVER),
    "button": item_box(BUTTON),
}
component_collisions = {
    name: {
        "base_mm3": round(shape.intersect(base).val().Volume(), 6),
        "lid_mm3": round(shape.intersect(lid).val().Volume(), 6),
    }
    for name, shape in component_shapes.items()
}

raw_20h = 16_000 * 2 * 20 * 3600
raw_20h_115 = math.ceil(raw_20h * 1.15)
base_mesh = trimesh.load_mesh(ROOT / "v13_rugged_base.stl", force="mesh")
lid_mesh = trimesh.load_mesh(ROOT / "v13_rugged_lid.stl", force="mesh")
pla_mass = (base_mesh.volume + lid_mesh.volume) / 1000.0 * 1.25
retention_mass = 1.8  # screws, foam, tape, wire, microSD
electronics_mass = sum(item["mass_g"] for item in PARTS) + retention_mass

checks = [
    {"check": "base mesh is watertight", "pass": meshes["v13_rugged_base"]["watertight"]},
    {"check": "lid mesh is watertight", "pass": meshes["v13_rugged_lid"]["watertight"]},
    {"check": "one printable body per base/lid", "pass": meshes["v13_rugged_base"]["bodies"] == 1 and meshes["v13_rugged_lid"]["bodies"] == 1},
    {"check": "minimum shell wall is 1.6 mm", "pass": WALL >= 1.6 and FLOOR >= 1.6},
    {"check": "15%-expanded battery width fits inner body", "pass": expanded_battery[1] <= inner_w},
    {"check": "15%-expanded board width fits inner body", "pass": expanded_board[1] <= inner_w},
    {"check": "15%-expanded battery and board remain separated", "pass": expanded_gap > 0},
    {"check": "actual battery height clears lid-mounted motor", "pass": (motor_bottom - (FLOOR + 0.5 + BATTERY["size"][2])) >= 2.0},
    {"check": "board stack fits vertical cavity", "pass": (FLOOR + 0.5 + BOARD["size"][2]) < (BASE_TOP - LIP_DEPTH)},
    {"check": "20h raw audio plus 15% fits 8 GB", "pass": raw_20h_115 < 8_000_000_000},
    {"check": "closed base and lid have zero solid collision", "pass": base_lid_collision < 0.000001},
    {"check": "controlled components have zero enclosure collision", "pass": all(
        values["base_mm3"] < 0.000001 and values["lid_mm3"] < 0.000001
        for values in component_collisions.values()
    )},
]

report = {
    "classification": "48-hour hand-assembled engineering prototype; not production/customer release",
    "body_mm": [BODY_L, BODY_W, BODY_D],
    "body_plus_loop_mm": [round(BODY_L / 2 - (loop_cx - 5.0), 2), BODY_W, BODY_D],
    "minimum_wall_mm": WALL,
    "parts": PARTS,
    "tolerance": {
        "battery_edge_clearance_each_side_mm": CLR,
        "board_edge_clearance_each_side_mm": BCLR,
        "expanded_battery_to_board_gap_mm": round(expanded_gap, 3),
        "note": "15% dimensional envelopes fit in the main cavity; printed rails and foam control actual placement.",
    },
    "storage": {
        "20h_raw_pcm_bytes": raw_20h,
        "20h_raw_pcm_plus_15_percent_bytes": raw_20h_115,
        "recommended_card": "32 GB high-endurance microSD",
    },
    "battery": {
        "capacity_mAh": 500,
        "average_current_limit_for_16h_mA": round(500 / 16, 3),
        "warning": "Runtime is a test gate, not a promise. Measure the sealed unit for 16 hours.",
    },
    "mass_estimate_g": {
        "printed_PLA": round(pla_mass, 2),
        "electronics_and_retention": round(electronics_mass, 2),
        "nominal_total": round(pla_mass + electronics_mass, 2),
        "plus_15_percent": round((pla_mass + electronics_mass) * 1.15, 2),
    },
    "meshes": meshes,
    "solid_collision_mm3": {
        "base_to_lid": round(base_lid_collision, 6),
        "components": component_collisions,
    },
    "checks": checks,
}

failed = [item["check"] for item in checks if not item["pass"]]
(ROOT / "v13_digital_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")

# Internal-layout preview.
fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=180)
ax.add_patch(FancyBboxPatch((-BODY_L / 2, -BODY_W / 2), BODY_L, BODY_W,
                            boxstyle=f"round,pad=0,rounding_size={CORNER_R}",
                            facecolor="#b7b3ad", edgecolor="#222", lw=1.4))
ax.add_patch(Circle((loop_cx, 0), 5.0, facecolor="#b7b3ad", edgecolor="#222"))
ax.add_patch(Circle((loop_cx, 0), 2.0, facecolor="white", edgecolor="#222"))
colors = ["#d9a52e", "#286aa6", "#ab6042", "#77549c", "#278566"]
for item, color in zip(PARTS, colors):
    l, w, _ = item["size"]
    x, y, _ = item["center"]
    ax.add_patch(FancyBboxPatch((x - l / 2, y - w / 2), l, w,
                                boxstyle="round,pad=0.02,rounding_size=0.7",
                                facecolor=color, edgecolor="#111", alpha=0.94))
labels = [
    (-10.3, 0, "500 mAh\nprotected battery"),
    (21.0, 0, "XIAO +\nmicroSD"),
    (-19.5, 0, "motor"),
    (-3.0, 5.5, "driver"),
    (3.0, -6.0, "button"),
]
for x, y, label in labels:
    ax.text(x, y, label, ha="center", va="center", fontsize=7,
            color="#111" if "battery" in label else "white")
ax.annotate("68 mm body", (-34, -21), (34, -21), ha="center", va="center",
            arrowprops=dict(arrowstyle="<->"), fontsize=9)
ax.annotate("33 mm", (41, -16.5), (41, 16.5), ha="center", va="center", rotation=90,
            arrowprops=dict(arrowstyle="<->"), fontsize=9)
ax.set(xlim=(-43, 45), ylim=(-24, 24), aspect="equal")
ax.set_title("Anticipy v1.3: what actually goes inside", weight="bold")
ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "v13_internal_layout.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("FAILED: " + "; ".join(failed))
