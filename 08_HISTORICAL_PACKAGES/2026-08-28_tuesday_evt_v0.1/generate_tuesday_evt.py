#!/usr/bin/env python3
"""Generate the strict-size Anticipy Tuesday EVT mechanical package.

This is a component-level Anticipy build, not a re-labelled finished recorder.
It uses a Seeed XIAO nRF52840 Sense, an Adafruit 5683 microSD BFF, a protected
502025 200 mAh pouch cell, a tactile switch, and a small ERM motor.

The CAD proves only nominal fit. The width clearance is intentionally tiny,
the battery source lacks production documentation, and no sealed unit has been
electrically or mechanically tested. It is an EVT package, not a production or
customer release.
"""

from pathlib import Path
import json
import math

import cadquery as cq
from cadquery import exporters
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from shapely.geometry import Point, box as shapely_box
import trimesh


ROOT = Path(__file__).resolve().parent

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
dejavu_regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
dejavu_bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
if dejavu_regular.exists() and dejavu_bold.exists():
    pdfmetrics.registerFont(TTFont("AnticipySans", str(dejavu_regular)))
    pdfmetrics.registerFont(TTFont("AnticipySans-Bold", str(dejavu_bold)))
    FONT_REGULAR = "AnticipySans"
    FONT_BOLD = "AnticipySans-Bold"

# PLAUD NotePin S: 51 x 21 x 11 mm. The user's absolute +10% ceiling is
# 56.1 x 23.1 x 12.1 mm. This nominal body leaves 0.1 mm on every axis.
BODY_L = 56.00
BODY_W = 23.00
FRAME_H = 10.43
FACE_SKIN = 0.635
FACE_ADHESIVE = 0.15
BODY_D = FRAME_H + 2 * (FACE_SKIN + FACE_ADHESIVE)
CORNER_R = 7.00
WALL = 0.50

# Brushed aluminum covers the battery and chain end; color-matched polymer
# covers the complete radio/board nose. This keeps metal off the chip antenna.
FACE_SPLIT_X = 4.40
FACE_SEAM = 0.12

# A 4.2 mm wearable opening lives in the otherwise unusable rounded tip.
CHAIN_CENTER = (-24.50, 0.0)
CHAIN_HOLE_D = 4.20
CHAIN_PARTITION_X = -21.70

# Delivered items must be measured and binned. These are controlled nominal
# envelopes, not a claimed production tolerance stack.
BATTERY = {
    "name": "protected 502025 200 mAh LiPo",
    "size": [25.0, 20.0, 5.0],
    "center": [-8.40, 0.0, 2.85],
    "mass_g": 5.0,
}
BOARD = {
    "name": "XIAO nRF52840 Sense + Adafruit 5683 direct stack",
    # BFF published size is 21.4 x 17.7 x 2.9 mm. Rotate the complete stack
    # so USB-C faces the -Y wall and the antenna remains in the polymer nose.
    "size": [17.8, 21.4, 7.5],
    "center": [13.70, 0.0, 3.90],
    "mass_g": 4.2,
}
MOTOR = {
    "name": "Vybronics VC0625B001L ERM",
    "size": [6.0, 6.0, 2.5],
    "center": [-14.3, 5.6, 7.75],
    "mass_g": 0.5,
}
HAPTIC = {
    "name": "insulated discrete haptic driver",
    "size": [8.0, 5.0, 1.5],
    "center": [-5.0, -5.7, 7.20],
    "mass_g": 0.3,
}
BUTTON = {
    "name": "C&K PTS810 tactile switch",
    "size": [4.2, 3.2, 2.5],
    # Mounted to the rigid bridge, not the pouch. This position reproduces the
    # Anticipy reference's button in the upper third of the hanging pendant.
    "center": [-8.0, 0.0, 7.80],
    "mass_g": 0.1,
}
PARTS = [BATTERY, BOARD, MOTOR, HAPTIC, BUTTON]

# Feature centers are transformed from Seeed's official XIAO nRF52840 Sense
# STEP model (downloaded 2026-08-29). The rotated board puts USB-C at -Y.
# The real direct stack must still be dry-fitted before sealing.
MIC_XY = (18.29, 9.69)
LED_XY = (19.41, -9.08)
BUTTON_XY = (-8.00, 0.0)
USB_CENTER_X = BOARD["center"][0]


def rounded_rect_2d(length, width, radius):
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
    out = core_x.union(core_y)
    for sx in (-1, 1):
        for sy in (-1, 1):
            out = out.union(
                Point(sx * (length / 2 - radius), sy * (width / 2 - radius)).buffer(radius, quad_segs=96)
            )
    return out


def part_box(part):
    return cq.Workplane("XY").box(*part["size"]).translate(tuple(part["center"]))


def footprint(part):
    sx, sy, _ = part["size"]
    cx, cy, _ = part["center"]
    return shapely_box(cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2)


def cyl_at(x, y, radius, height, z0=0.0):
    return cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z0))


def export_pair(shape, stem):
    exporters.export(shape, str(ROOT / f"{stem}.step"))
    exporters.export(shape, str(ROOT / f"{stem}.stl"), tolerance=0.01, angularTolerance=0.1)


# Polymer structural frame.
outer = rounded_rect_solid(BODY_L, BODY_W, CORNER_R, FRAME_H)
inner = rounded_rect_solid(
    BODY_L - 2 * WALL,
    BODY_W - 2 * WALL,
    CORNER_R - WALL,
    FRAME_H + 0.4,
    -0.2,
)
frame = outer.cut(inner)

# Fill and drill the load-bearing chain tip. The partition keeps metal rings,
# cut edges and the pouch cell physically separated.
chain_fill_len = CHAIN_PARTITION_X + BODY_L / 2
chain_fill = cq.Workplane("XY").box(chain_fill_len, BODY_W - 0.6, FRAME_H).translate(
    ((CHAIN_PARTITION_X - BODY_L / 2) / 2, 0, FRAME_H / 2)
)
chain_hole = cyl_at(*CHAIN_CENTER, CHAIN_HOLE_D / 2, FRAME_H + 2.0, -1.0)
frame = frame.union(chain_fill).cut(chain_hole)

# Low end-stop between cell and board, with a central insulated lead passage.
divider_x = 4.35
divider = cq.Workplane("XY").box(0.45, BODY_W - 0.8, 1.15).translate((divider_x, 0, 0.575))
wire_notch = cq.Workplane("XY").box(0.9, 4.2, 0.95).translate((divider_x, 0, 0.75))
frame = frame.union(divider.cut(wire_notch))

# USB-C exits through the polymer -Y wall. Final Z trim follows measurement of
# the actual direct-soldered board stack.
usb_cut = cq.Workplane("XY").box(9.8, 2.0, 4.8).translate((USB_CENTER_X, -BODY_W / 2, 3.65))
frame = frame.cut(usb_cut)

# Ledges carry a separate rigid bridge above the pouch. No hard component,
# adhesive blob or motor is allowed to press on the battery.
for x0, x1, y0 in [
    (-20.65, 3.80, -10.85),
    (-20.65, 3.80, 10.85),
]:
    ledge = cq.Workplane("XY").box(x1 - x0, 0.60, 0.55).translate(
        ((x0 + x1) / 2, y0, 5.575)
    )
    frame = frame.union(ledge)

battery_bridge = (
    cq.Workplane("XY").box(24.35, 21.10, 0.60, centered=(True, True, False))
    .edges("|Z").fillet(0.55)
)

# Hybrid faces: brushed aluminum plus a full-width polymer RF nose.
full_face = rounded_rect_solid(BODY_L, BODY_W, CORNER_R, FACE_SKIN)
metal_right = FACE_SPLIT_X - FACE_SEAM / 2
metal_len = metal_right + BODY_L / 2
metal_halfspace = cq.Workplane("XY").box(metal_len, BODY_W + 4, FACE_SKIN + 1).translate(
    ((-BODY_L / 2 + metal_right) / 2, 0, FACE_SKIN / 2)
)
nose_left = FACE_SPLIT_X + FACE_SEAM / 2
nose_len = BODY_L / 2 - nose_left
nose_halfspace = cq.Workplane("XY").box(nose_len, BODY_W + 4, FACE_SKIN + 1).translate(
    ((nose_left + BODY_L / 2) / 2, 0, FACE_SKIN / 2)
)
front_metal = full_face.intersect(metal_halfspace)
back_metal = full_face.intersect(metal_halfspace)
front_nose = full_face.intersect(nose_halfspace)
back_nose = full_face.intersect(nose_halfspace)

for name in ("front", "back"):
    target = front_metal if name == "front" else back_metal
    target = target.cut(cyl_at(*CHAIN_CENTER, CHAIN_HOLE_D / 2, FACE_SKIN + 1, -0.5))
    if name == "front":
        front_metal = target
    else:
        back_metal = target

front_metal = front_metal.cut(cyl_at(*BUTTON_XY, 1.80, FACE_SKIN + 1, -0.5))

# One acoustic hole, one circular button, and one tiny light are the only
# visible details. A three-hole grille would add no function to this one-mic
# EVT and would move the appearance away from the Anticipy reference.
front_nose = front_nose.cut(cyl_at(*MIC_XY, 0.55, FACE_SKIN + 1, -0.5))
front_nose = front_nose.cut(cyl_at(*LED_XY, 0.52, FACE_SKIN + 1, -0.5))

def make_button_plunger(stem_length):
    """Flush face puck, captive rear flange, then stem toward the switch."""
    cap = cq.Workplane("XY").circle(1.70).extrude(FACE_SKIN)
    flange = cq.Workplane("XY").circle(2.00).extrude(0.25).translate((0, 0, FACE_SKIN))
    stem = (
        cq.Workplane("XY").circle(1.00).extrude(stem_length)
        .translate((0, 0, FACE_SKIN + 0.25))
    )
    return cap.union(flange).union(stem)


button_plungers = {
    "1p15": make_button_plunger(1.15),
    "1p30": make_button_plunger(1.30),
    "1p45": make_button_plunger(1.45),
}
button_plunger = button_plungers["1p30"]

# Fit checks.
outer_poly = rounded_rect_polygon(BODY_L, BODY_W, CORNER_R)
inner_poly = rounded_rect_polygon(BODY_L - 2 * WALL, BODY_W - 2 * WALL, CORNER_R - WALL)
component_gap = footprint(BATTERY).distance(footprint(BOARD))
chain_boss = Point(*CHAIN_CENTER).buffer(CHAIN_HOLE_D / 2 + 0.70, quad_segs=96)
chain_to_battery = chain_boss.distance(footprint(BATTERY))


def z_bounds(part):
    z = part["center"][2]
    h = part["size"][2]
    return z - h / 2, z + h / 2


checks = [
    {"name": "body within +10% ceiling", "pass": BODY_L <= 56.1 and BODY_W <= 23.1 and BODY_D <= 12.1},
    {"name": "R7 Anticipy rounded outline", "pass": math.isclose(CORNER_R, 7.0)},
    {"name": "battery nominal footprint inside rounded cavity", "pass": bool(inner_poly.covers(footprint(BATTERY)))},
    {"name": "board nominal footprint inside rounded cavity", "pass": bool(inner_poly.covers(footprint(BOARD)))},
    {"name": "battery and board have nominal wire gap", "pass": component_gap >= 0.65},
    {"name": "chain boss clears nominal battery", "pass": chain_to_battery >= 0.70},
    {"name": "battery clears chain partition", "pass": footprint(BATTERY).bounds[0] >= CHAIN_PARTITION_X + 0.70},
    {"name": "battery stays below rigid bridge", "pass": z_bounds(BATTERY)[1] <= 5.35 + 1e-6},
    {"name": "board stack clears face", "pass": z_bounds(BOARD)[1] <= FRAME_H - 0.35},
    {"name": "haptic parts clear face", "pass": max(z_bounds(MOTOR)[1], z_bounds(HAPTIC)[1]) <= FRAME_H - 0.35},
    {"name": "button clears face", "pass": z_bounds(BUTTON)[1] <= FRAME_H - 0.35},
]

failed = [c["name"] for c in checks if not c["pass"]]
if failed:
    raise SystemExit("fit checks failed: " + "; ".join(failed))

# Exports and verification.
export_pair(frame, "anticipy_strict_evt_polymer_frame")
export_pair(battery_bridge, "anticipy_strict_evt_battery_bridge")
export_pair(front_metal, "anticipy_strict_evt_front_aluminum")
export_pair(back_metal, "anticipy_strict_evt_back_aluminum")
export_pair(front_nose, "anticipy_strict_evt_front_rf_nose")
export_pair(back_nose, "anticipy_strict_evt_back_rf_nose")
for suffix, plunger in button_plungers.items():
    exporters.export(
        plunger,
        str(ROOT / f"anticipy_strict_evt_button_plunger_{suffix}.stl"),
        tolerance=0.01,
        angularTolerance=0.1,
    )

for part in PARTS:
    stem = "dummy_" + part["name"].lower().replace(" ", "_").replace("/", "_")
    exporters.export(part_box(part), str(ROOT / f"{stem}.stl"), tolerance=0.01)

# Twelve frames on one 256 mm-class printer plate: build 12 to yield 10.
plate_parts = []
for row in range(3):
    for col in range(4):
        plate_parts.append(frame.translate((-88.5 + col * 59.0, -27.0 + row * 27.0, 0)))
frame_plate = cq.Compound.makeCompound([p.val() for p in plate_parts])
exporters.export(frame_plate, str(ROOT / "anticipy_strict_evt_12_frame_plate.stl"), tolerance=0.02, angularTolerance=0.15)

# Twelve complete sets of printed bridge/front-nose/back-nose pieces.
accessory_parts = []
grid_x = [-75, -45, -15, 15, 45, 75]
grid_y = [-75, -45, -15, 15, 45, 75]
for row, y in enumerate(grid_y):
    shape = battery_bridge if row < 2 else front_nose if row < 4 else back_nose
    for x in grid_x:
        accessory_parts.append(shape.translate((x, y, 0)))
accessory_plate = cq.Compound.makeCompound([p.val() for p in accessory_parts])
exporters.export(
    accessory_plate,
    str(ROOT / "anticipy_strict_evt_12_accessory_sets_plate.stl"),
    tolerance=0.02,
    angularTolerance=0.15,
)

# A small fit plate provides four of each flush-button stem length.
button_parts = []
for row, suffix in enumerate(("1p15", "1p30", "1p45")):
    for col in range(4):
        button_parts.append(button_plungers[suffix].translate((-9 + col * 6, -6 + row * 6, 0)))
button_plate = cq.Compound.makeCompound([p.val() for p in button_parts])
exporters.export(
    button_plate,
    str(ROOT / "anticipy_strict_evt_12_button_fit_plate.stl"),
    tolerance=0.01,
    angularTolerance=0.1,
)

assembly = cq.Assembly(name="Anticipy_Strict_Tuesday_EVT")
assembly.add(back_metal.translate((0, 0, -(FACE_SKIN + FACE_ADHESIVE))), name="back_aluminum")
assembly.add(back_nose.translate((0, 0, -(FACE_SKIN + FACE_ADHESIVE))), name="back_rf_nose")
assembly.add(frame, name="polymer_frame")
assembly.add(front_metal.translate((0, 0, FRAME_H + FACE_ADHESIVE)), name="front_aluminum")
assembly.add(front_nose.translate((0, 0, FRAME_H + FACE_ADHESIVE)), name="front_rf_nose")
assembly.add(battery_bridge.translate((BATTERY["center"][0], 0, 5.55)), name="battery_bridge")
installed_plunger = button_plunger.rotate((0, 0, 0), (1, 0, 0), 180).translate(
    (BUTTON_XY[0], BUTTON_XY[1], FRAME_H + FACE_ADHESIVE + FACE_SKIN)
)
assembly.add(installed_plunger, name="flush_button_plunger_nominal")
for idx, part in enumerate(PARTS):
    assembly.add(part_box(part), name=f"component_{idx}")
assembly.save(str(ROOT / "anticipy_strict_evt_nominal_assembly.step"))

mesh_names = [
    "anticipy_strict_evt_polymer_frame",
    "anticipy_strict_evt_battery_bridge",
    "anticipy_strict_evt_front_rf_nose",
    "anticipy_strict_evt_back_rf_nose",
    "anticipy_strict_evt_button_plunger_1p30",
]
mesh_report = {}
for name in mesh_names:
    mesh = trimesh.load_mesh(ROOT / f"{name}.stl", process=True)
    mesh_report[name] = {
        "watertight": bool(mesh.is_watertight),
        "body_count": len(mesh.split(only_watertight=False)),
        "bounds_mm": (mesh.bounds[1] - mesh.bounds[0]).round(4).tolist(),
    }

report = {
    "classification": "strict-size component-built EVT; nominal CAD only; not customer-release-ready",
    "finished_body_mm": [BODY_L, BODY_W, BODY_D],
    "official_reference_mm": [51.0, 21.0, 11.0],
    "hard_10_percent_ceiling_mm": [56.1, 23.1, 12.1],
    "outline_radius_mm": CORNER_R,
    "materials": {
        "structure_and_rf_nose": "printed non-conductive polymer",
        "front_and_back_battery_end": f"{FACE_SKIN:.2f} mm brushed aluminum",
        "rf_nose_finish": "color-matched silver non-conductive finish",
        "reason_for_hybrid": "continuous metal over the XIAO antenna would reduce BLE performance",
    },
    "board_feature_source": {
        "model": "Seeed Studio XIAO nRF52840 Sense official STEP",
        "url": "https://files.seeedstudio.com/wiki/XIAO-BLE/seeed-studio-xiao-nrf52840-3d-model.zip",
        "verified_features": ["PCB envelope", "USB-C", "MSM261D3526H1CPM microphone", "LED", "ANT1"],
    },
    "components": PARTS,
    "nominal_xy_gap_mm": round(float(component_gap), 3),
    "chain_boss_to_battery_gap_mm": round(float(chain_to_battery), 3),
    "battery_runtime_gate": {
        "nominal_capacity_mAh": 200,
        "usable_capacity_assumption_percent": 85,
        "16h_average_current_ceiling_mA": round(200 * 0.85 / 16, 3),
        "status": "must be measured on a sealed unit; not yet proven",
    },
    "release_hold": [
        "measure and bin every XIAO/BFF stack and battery before assembly",
        "build and test unit 1 before cutting or assembling the remaining 11",
        "prove charge current, cell temperature, BLE range, audio, SD and button/haptic",
        "do not claim 16 hours until a sealed unit passes a continuous runtime test",
        "the Tuesday battery source and its production UN38.3/SDS packet are not yet verified",
    ],
    "checks": checks,
    "meshes": mesh_report,
}
(ROOT / "strict_evt_fit_report.json").write_text(json.dumps(report, indent=2) + "\n")

# Dimensioned layout drawing.
fig, ax = plt.subplots(figsize=(10.5, 5.4), dpi=180)
ox, oy = outer_poly.exterior.xy
ax.fill(ox, oy, color="#9b9b9b", ec="#111", lw=1.2)
ax.axvline(FACE_SPLIT_X, color="#111", lw=1.0, ls="--")
colors = {
    BATTERY["name"]: "#d5a52f",
    BOARD["name"]: "#266c9c",
    MOTOR["name"]: "#a95d40",
    HAPTIC["name"]: "#74579b",
    BUTTON["name"]: "#28866b",
}
for part in PARTS:
    sx, sy, _ = part["size"]
    cx, cy, _ = part["center"]
    ax.add_patch(FancyBboxPatch(
        (cx - sx / 2, cy - sy / 2), sx, sy,
        boxstyle="round,pad=0.01,rounding_size=0.35",
        facecolor=colors[part["name"]], edgecolor="#111", alpha=0.92,
    ))
ax.add_patch(Circle(CHAIN_CENTER, CHAIN_HOLE_D / 2, color="#111", fill=False, lw=1.1))
ax.text(BATTERY["center"][0], 0, "protected 200 mAh\n25 x 20 x 5", ha="center", va="center", fontsize=7)
ax.text(BOARD["center"][0], 0, "XIAO + microSD\n17.8 x 21.4", ha="center", va="center", fontsize=7, color="white")
ax.text(0, 15.0, "Anticipy strict +10% component-built EVT", ha="center", fontsize=13, weight="bold")
ax.text(0, 12.9, "56.0 x 23.0 x 12.0 mm · R7 · aluminum battery end + polymer RF nose", ha="center", fontsize=8)
ax.annotate("56.0 mm", (-BODY_L / 2, -14), (BODY_L / 2, -14), ha="center", arrowprops=dict(arrowstyle="<->"), fontsize=8)
ax.set_aspect("equal")
ax.set_xlim(-34, 34)
ax.set_ylim(-16, 17)
ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "anticipy_strict_evt_internal_layout.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# Front appearance check in the hanging orientation. This is deliberately a
# flat engineering render, not a photorealistic promise.
metal_poly = outer_poly.intersection(shapely_box(-100, -100, FACE_SPLIT_X - FACE_SEAM / 2, 100))
nose_poly = outer_poly.intersection(shapely_box(FACE_SPLIT_X + FACE_SEAM / 2, -100, 100, 100))
fig, ax = plt.subplots(figsize=(4.2, 7.0), dpi=220)
for poly, color in ((metal_poly, "#55585b"), (nose_poly, "#5d6063")):
    px, py = poly.exterior.xy
    ax.fill(py, [-v for v in px], color=color, ec="#151515", lw=1.0)
ax.add_patch(Circle((CHAIN_CENTER[1], -CHAIN_CENTER[0]), CHAIN_HOLE_D / 2, facecolor="#111", edgecolor="#9a9a9a", lw=0.7))
ax.add_patch(Circle((BUTTON_XY[1], -BUTTON_XY[0]), 1.70, facecolor="#b9b9b9", edgecolor="#1a1a1a", lw=0.7))
ax.add_patch(Circle((LED_XY[1], -LED_XY[0]), 0.52, facecolor="#d8f2ff", edgecolor="#7a99aa", lw=0.35))
ax.add_patch(Circle((MIC_XY[1], -MIC_XY[0]), 0.55, facecolor="#101010", edgecolor="none"))
ax.text(0, -34.0, "Front appearance check · 56.0 × 23.0 × 12.0 mm", ha="center", fontsize=8)
ax.set_aspect("equal")
ax.set_xlim(-15, 15)
ax.set_ylim(-36, 33)
ax.axis("off")
fig.tight_layout()
fig.savefig(ROOT / "anticipy_strict_evt_front_appearance.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# Exact-scale cutting template. ReportLab uses physical page units, so 1 mm in
# CAD is exactly 1 mm in the PDF when printed at 100 percent.
metal_poly = outer_poly.intersection(shapely_box(-100, -100, FACE_SPLIT_X - FACE_SEAM / 2, 100))
pdf_path = ROOT / "anticipy_strict_evt_aluminum_template.pdf"
c = canvas.Canvas(str(pdf_path), pagesize=letter)
c.setTitle("Anticipy strict EVT aluminum face templates")


def pdf_poly(poly, ox_mm, oy_mm):
    path = c.beginPath()
    coords = list(poly.exterior.coords)
    path.moveTo((ox_mm + coords[0][0]) * mm, (oy_mm + coords[0][1]) * mm)
    for x, y in coords[1:]:
        path.lineTo((ox_mm + x) * mm, (oy_mm + y) * mm)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


c.setLineWidth(0.25 * mm)
c.setFont(FONT_BOLD, 13)
c.drawString(22 * mm, 260 * mm, "ANTICIPY STRICT EVT - 1:1 ALUMINUM CAPS")
c.setFont(FONT_REGULAR, 8)
c.drawString(22 * mm, 252 * mm, "Print at 100 percent. Do not use Fit, Shrink, or Scale to page.")

for label, oy, include_button in (
    ("FRONT - chain and button holes", 211, True),
    ("BACK - chain hole only", 163, False),
):
    ox = 65
    pdf_poly(metal_poly, ox, oy)
    c.circle((ox + CHAIN_CENTER[0]) * mm, (oy + CHAIN_CENTER[1]) * mm, CHAIN_HOLE_D / 2 * mm, stroke=1, fill=0)
    if include_button:
        c.circle((ox + BUTTON_XY[0]) * mm, (oy + BUTTON_XY[1]) * mm, 1.80 * mm, stroke=1, fill=0)
    c.setFont(FONT_BOLD, 8)
    c.drawString(105 * mm, (oy - 2) * mm, label)

c.line(35 * mm, 115 * mm, 85 * mm, 115 * mm)
c.line(35 * mm, 113.5 * mm, 35 * mm, 116.5 * mm)
c.line(85 * mm, 113.5 * mm, 85 * mm, 116.5 * mm)
c.setFont(FONT_REGULAR, 8)
c.drawCentredString(60 * mm, 109 * mm, "50.0 mm calibration bar")

c.setFont(FONT_BOLD, 9)
c.drawString(22 * mm, 91 * mm, "MATERIAL")
c.setFont(FONT_REGULAR, 8)
c.drawString(22 * mm, 85 * mm, "0.60-0.65 mm 5052 aluminum. Deburr every edge.")
c.drawString(22 * mm, 79 * mm, "Cut one front/back pair and dry-fit unit 1 before cutting 11 more pairs.")
c.setFont(FONT_BOLD, 8)
c.drawString(22 * mm, 69 * mm, "HOLD: no hard edge, screw, burr, or adhesive lump may press on the pouch cell.")
c.showPage()
c.save()

print(json.dumps({
    "finished_body_mm": [BODY_L, BODY_W, BODY_D],
    "nominal_component_gap_mm": round(float(component_gap), 3),
    "chain_to_battery_gap_mm": round(float(chain_to_battery), 3),
    "checks": f"{len(checks)}/{len(checks)} passed",
    "mesh_report": mesh_report,
}, indent=2))
