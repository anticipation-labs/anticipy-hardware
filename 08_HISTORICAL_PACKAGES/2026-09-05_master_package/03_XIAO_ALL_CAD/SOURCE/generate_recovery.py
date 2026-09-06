"""Anticipy exact-shell recovery geometry, v0.2.

Purpose
-------
Reuse the exact historical 51 x 22 mm body and matching hooked face geometry while
making enough Z room for:

* Seeed XIAO nRF52840 Sense (official STEP envelope 22.482 x 17.780 x 4.460)
* protected LiPo envelope up to 25 x 10 x 5.5 mm,
* Vybronics VCLP1020B002L tolerance envelope up to 10.2 x 2.3 mm and a
  discrete driver zone; the screw-retained Renata architecture separately
  qualifies a conservative motor fit envelope up to 10.2 x 10.2 x 2.7 mm, or
* conditional DTP401525-class 25.3 x 15 x 4.0 mm protected-pack envelope
  with the driver island rotated into the battery/motor gap, or
* full-swept 11.29 x 4.03 mm barrel ERM measurement reference (not Unit 001).

The historical body contains a 1 mm-high PCB shelf that a simple 48 x 19 x 8
capsule model misses.  This generator imports the exact historical body and
face STEP solids and boolean-checks the shelf, face hooks, complete hook slide
path, spacer, bridge and every component envelope.  A 4.50 mm-rise printed
mid-band preserves the historical body and face geometry. When no ordered
shell is physically available, the generator also exports watertight STL
copies of both shell pieces for black PETG printing. The standard bands are
structurally bonded to the body; a separate Renata-only band can instead be
clamped by two keyed printed posts and M2 screws through the body floor.  The
original face hooks remain removable through replicated slide-and-lock
channels in either band.

This remains a fit/reference generator, not proof that an unmeasured battery
is electrically or mechanically safe or that an actual MJF part matches CAD.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import cadquery as cq


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
OUT.mkdir(exist_ok=True)
PACKAGED_REFERENCE_ROOT = ROOT / "reference"
LEGACY_REFERENCE_ROOT = (
    ROOT.parent
    / "devin_github_stage"
    / "historical_narrow_51x22x11_commit_23b5cec"
    / "out"
)
REFERENCE_ROOT = (
    PACKAGED_REFERENCE_ROOT
    if (PACKAGED_REFERENCE_ROOT / "alu_body.step").exists()
    and (PACKAGED_REFERENCE_ROOT / "alu_face_front_v3.step").exists()
    else LEGACY_REFERENCE_ROOT
)
BODY_STEP = REFERENCE_ROOT / "alu_body.step"
FACE_STEP = REFERENCE_ROOT / "alu_face_front_v3.step"

# Ordered-shell nominal geometry (mm), recovered from the exact generator.
SHELL_L = 51.0
SHELL_W = 22.0
BODY_H = 10.0
FLOOR_T = 1.0
CAVITY_L = 48.0
CAVITY_W = 19.0
ORIGINAL_CLEAR_H = 8.0
REBATE_L = 49.5
REBATE_W = 20.5
FACE_L = 47.8
FACE_W = 20.3
FACE_T = 1.0

# Exact historical internal shelf / battery-bay geometry.
BATTERY_BAY_L = 38.5
BATTERY_BAY_W = 13.0
SHELF_BOTTOM_GLOBAL = 5.2
SHELF_TOP_GLOBAL = 6.2
SHELF_TOP_FROM_FLOOR = SHELF_TOP_GLOBAL - FLOOR_T

# The visible height added to the original 10 mm closed shell.  The ring
# itself starts at the old face underside, one millimetre below body top, so
# total ring height is RISE + FACE_T.  The 4.50 mm rise supports a documented
# 5.5 mm-finished pack while retaining 0.59 mm nominal clearance below the
# original 1 mm face hooks.
RISE = 4.50
RING_TOTAL_H = RISE + FACE_T
MAIN_CLEAR_H = ORIGINAL_CLEAR_H + RISE
HOOK_DROP = 1.0
HOOK_ZONE_CLEAR_H = MAIN_CLEAR_H - HOOK_DROP

# Original face slide-and-lock geometry, reproduced in the printed band.
HOOK_L = 3.0
HOOK_CLR = 0.2
SLIDE = 1.5
LEG_DROP = 1.0
FOOT_D = 0.6
LIP_T = 0.5
HOOK_XS = (-10.0, 10.0)
WALL_IN = CAVITY_W / 2
CH_OUT = WALL_IN + FOOT_D + HOOK_CLR / 2

# Measured/declared maximum component envelopes.
XIAO_L = 22.4819811502
XIAO_W = 17.7800000000
XIAO_H = 4.4600000149
BAT_L = 25.0
BAT_W = 10.0
BAT_H = 5.5
# The nominal motor can may be described as 4 x 8 mm, but the full rotating /
# finished envelope supplied for fit control is 11.29 x 4.03 mm.  The larger
# values, not the marketing can size, control all geometry below.
MOTOR_L = 11.29
MOTOR_D = 4.03
# Finished, insulated SMD motor-driver island. This is deliberately larger
# than the bare component bodies so solder, a thin carrier, and insulation are
# controlled by the same no-load fit gate. Axial/through-hole parts do not fit.
DRIVER_L = 8.0
DRIVER_W = 4.0
DRIVER_H = 2.0

# Alternate architecture: the ordered Vybronics coin ERM at its 10.2 x 2.3 mm
# datasheet tolerance envelope, with short candidates or the documented 24 mm
# Renata-class cell.  All batteries are conservatively gauged at 5.5 mm
# finished height in this architecture.
ALT_BAT_LS = (12.0, 15.0, 24.0, 25.0)
ALT_BAT_W = 10.0
ALT_BAT_H = 5.5
ALT_COIN_D = 10.2
ALT_COIN_T = 2.3
ALT_BAT_LEFTS = {12.0: -12.1, 15.0: -13.0, 24.0: -15.5, 25.0: -16.0}
# The screw-retained Renata architecture has a separate conservative motor
# envelope.  It covers both the ordered 10.2 x 2.3 mm Vybronics tolerance box
# and the Lee PID10431 listing's 10.0 x 2.7 mm body without changing the
# thinner Vybronics-only layouts elsewhere in this generator.  Mechanical fit
# does not qualify the Lee motor's maker, current, duty, polarity or driver.
PRIMARY_RENATA_MOTOR_MAX_D = 10.2
PRIMARY_RENATA_MOTOR_MAX_T = 2.7
# Local counter candidate's listed body, retained as its own exact-size gauge.
LEE_COIN_D = 10.0
LEE_COIN_T = 2.7

# Conditional Plan B geometry.  SparkFun PRT-13853's archived DTP401525
# drawing specifies T<=4.0, W<=15.0, L<=25.0 and L2<=25.3 mm.  The 25.3 mm
# total length controls this fit model.  This geometry does not prove that a
# similarly advertised local cell (including Lee PID8834) is the same pack;
# manufacturer identity, protection, charge limits and matching UN38.3 remain
# separate release gates.
PLAN_B_BAT_L = 25.3
PLAN_B_BAT_W = 15.0
PLAN_B_BAT_H = 4.0
PLAN_B_BAT_C = (-4.15, 0.0)
PLAN_B_COIN_C = (18.4, 0.0)
PLAN_B_DRIVER_L = 4.0
PLAN_B_DRIVER_W = 8.0
PLAN_B_DRIVER_H = DRIVER_H
PLAN_B_DRIVER_C = (10.9, 0.0)

# Optional no-adhesive closure for the primary 24 x 10 mm Renata-class
# battery/Vybronics layout only.  Two support-free mounting ears are added to
# a separate band.  Keyed printed posts pass through the ears and are pulled
# against the body floor by M2 x 10 mm countersunk screws.  The original
# adhesive bands and conditional Plan B remain unchanged.
SCREW_TOWER_CENTRES = ((11.0, 3.0), (11.0, -3.0))
SCREW_EAR_X = 5.0
SCREW_EAR_INNER_Y = 1.0
SCREW_POST_SHAFT = 3.6
SCREW_POST_SOCKET = 3.9
SCREW_POST_HEAD = 5.6
SCREW_POST_HEAD_T = 0.8
SCREW_POST_INSTALLED_H = BODY_H - FLOOR_T
SCREW_PILOT_D = 1.60
SCREW_BODY_CLEAR_D = 2.20
SCREW_BODY_CLEAR_MAX_D = 2.40
SCREW_COUNTERSINK_MAX_D = 4.0
SCREW_JIG_GUIDE_D = 1.0

# Historical antenna-window bounds used by the drill audit.  The through
# opening is 7 x 14 mm at x=19.5; its shallow flange recess is 10 x 17 mm.
ANTENNA_WINDOW_X = 19.5
ANTENNA_WINDOW_THROUGH_L = 7.0
ANTENNA_WINDOW_THROUGH_W = 14.0
ANTENNA_WINDOW_RECESS_L = 10.0
ANTENNA_WINDOW_RECESS_W = 17.0

# Shipping-build stack allowances.  The bridge seats just above the exact
# shelf top rather than sending long legs through the shelf.
FLOOR_INSULATION = 0.05
SHELF_SEAT_GAP = 0.02
BATTERY_FREE_GAP = 0.40
BRIDGE_PAD_H = (
    FLOOR_INSULATION
    + BAT_H
    + BATTERY_FREE_GAP
    - (SHELF_TOP_FROM_FLOOR + SHELF_SEAT_GAP)
)
BRIDGE_DECK_T = 0.40
BOARD_ADHESIVE = 0.10
BATTERY_TO_BRIDGE_FREE = (
    SHELF_TOP_FROM_FLOOR
    + SHELF_SEAT_GAP
    + BRIDGE_PAD_H
    - (FLOOR_INSULATION + BAT_H)
)
CELL_TO_BOARD_BARRIER = BATTERY_TO_BRIDGE_FREE + BRIDGE_DECK_T + BOARD_ADHESIVE
BRIDGE_DECK_UNDERSIDE_REL = FLOOR_INSULATION + BAT_H + BATTERY_TO_BRIDGE_FREE
BRIDGE_INSTALL_TOP_REL = BRIDGE_DECK_UNDERSIDE_REL + BRIDGE_DECK_T
TOP_CLEARANCE = 0.25

# Layout coordinates in the shell frame. USB is at -X, antenna at +X.
# XIAO bbox is conservative; the narrower USB nose has additional real room.
XIAO_C = (-6.0, 0.0)
# The 25 mm fallback cell must remain inside the 38.5 x 13 mm shelf opening.
# This location blocks the complete conservative antenna zone, so the local
# short cell below is the RF-preferred architecture.
BAT_C = (-3.5, 0.0)
# The full-swept barrel envelope is rotated 90 degrees so it also remains
# inside the shelf opening.  This gives real clearance without trimming PA12.
MOTOR_C = (12.75, 0.0)
# Upper side strip: outside the battery, both motor alternatives, bridge feet,
# and the XIAO's last-5-mm antenna keepout while remaining below the raised PCB.
DRIVER_C = (-5.0, 7.3)

# Antenna keepout is the last 5 mm at the non-USB end of the XIAO bbox.
ANT_L = 5.0
ANT_X0 = XIAO_C[0] + XIAO_L / 2 - ANT_L
ANT_X1 = XIAO_C[0] + XIAO_L / 2

# Microphone location derived from the official XIAO STEP model.  The model's
# microphone centre is (-8.9295, +4.5874) relative to board centre with USB at
# +X.  Rotating the board so USB faces shell -X gives (+8.9295, -4.5874).
MIC_C = (XIAO_C[0] + 8.9295, -4.5874)


def capsule(length: float, width: float) -> cq.Sketch:
    return cq.Sketch().slot(length - width, width, angle=0)


def capsule_contains_point(
    x: float,
    y: float,
    margin: float = 0.0,
    length: float = CAVITY_L,
    width: float = CAVITY_W,
) -> bool:
    radius = width / 2 - margin
    straight_half = (length - width) / 2
    if abs(y) > radius:
        return False
    if abs(x) <= straight_half:
        return True
    return (abs(x) - straight_half) ** 2 + y**2 <= radius**2 + 1e-9


def rectangle_corners(cx: float, cy: float, length: float, width: float):
    for x in (cx - length / 2, cx + length / 2):
        for y in (cy - width / 2, cy + width / 2):
            yield x, y


def rect_in_capsule(
    cx: float,
    cy: float,
    item_length: float,
    item_width: float,
    margin: float = 0.0,
    capsule_length: float = CAVITY_L,
    capsule_width: float = CAVITY_W,
):
    return all(
        capsule_contains_point(x, y, margin, capsule_length, capsule_width)
        for x, y in rectangle_corners(cx, cy, item_length, item_width)
    )


def circle_in_capsule(
    cx: float,
    cy: float,
    diameter: float,
    margin: float = 0.0,
    capsule_length: float = CAVITY_L,
    capsule_width: float = CAVITY_W,
):
    """Exact circle-in-capsule test using erosion by the circle radius."""
    effective_radius = capsule_width / 2 - diameter / 2 - margin
    straight_half = (capsule_length - capsule_width) / 2
    if effective_radius < 0 or abs(cy) > effective_radius:
        return False
    if abs(cx) <= straight_half:
        return True
    return (abs(cx) - straight_half) ** 2 + cy**2 <= effective_radius**2 + 1e-9


def rect_gap(a, b):
    """Signed closest plan gap for axis-aligned rectangles."""
    ax, ay, al, aw = a
    bx, by, bl, bw = b
    gx = abs(ax - bx) - (al + bl) / 2
    gy = abs(ay - by) - (aw + bw) / 2
    if gx >= 0 and gy >= 0:
        return math.hypot(gx, gy)
    if gx >= 0:
        return gx
    if gy >= 0:
        return gy
    return -min(-gx, -gy)


def export(obj, name: str):
    cq.exporters.export(obj, str(OUT / name))


def moved_shape(obj, vector):
    """Return a translated CadQuery shape without mutating the source."""
    shape = obj.val() if isinstance(obj, cq.Workplane) else obj
    return shape.translate(vector)


def intersection_volume(a, b) -> float:
    """Exact OCC boolean overlap volume in cubic millimetres."""
    a_shape = a.val() if isinstance(a, cq.Workplane) else a
    b_shape = b.val() if isinstance(b, cq.Workplane) else b
    return float(a_shape.intersect(b_shape).Volume())


def make_spacer(tongue_clearance_per_side: float = 0.20):
    """Raised band with exact historical face-hook slide channels.

    The lower annulus nests in the old body rebate.  The upper annulus carries
    a new copy of the historical T-slot geometry so the ordered face can still
    drop at +0.75 mm and slide to its -0.75 mm locked position.
    """
    # 0..1 mm nests in the body's existing top rebate.
    lower_l = REBATE_L - 2 * tongue_clearance_per_side
    lower_w = REBATE_W - 2 * tongue_clearance_per_side
    lower = cq.Workplane("XY").placeSketch(capsule(lower_l, lower_w)).extrude(FACE_T)
    # 1..5 mm is the shell-width visible band.
    upper = (
        cq.Workplane("XY")
        .placeSketch(capsule(SHELL_L, SHELL_W))
        .extrude(RISE)
        .translate((0, 0, FACE_T))
    )
    ring = lower.union(upper)

    # Preserve the nominal 48 x 19 mm component opening up to the face ledge.
    inner = cq.Workplane("XY").placeSketch(capsule(CAVITY_L, CAVITY_W)).extrude(RING_TOTAL_H)
    ring = ring.cut(inner)

    # Reproduce the full historical 49.5 x 20.5 rebate.  The face is shorter
    # by the 1.5 mm slide travel, leaving 0.10 mm nominal end clearance at both
    # the drop and locked positions.
    face_recess = (
        cq.Workplane("XY")
        .placeSketch(capsule(REBATE_L, REBATE_W))
        .extrude(FACE_T)
        .translate((0, 0, RING_TOTAL_H - FACE_T))
    )
    ring = ring.cut(face_recess)

    plate_bot = RISE
    ch_top = plate_bot - LIP_T
    ch_bot = plate_bot - LEG_DROP - 0.1
    for tx in HOOK_XS:
        for sy in (1, -1):
            y0 = WALL_IN if sy > 0 else -CH_OUT
            drop_notch = (
                cq.Workplane("XY")
                .box(
                    HOOK_L + 2 * HOOK_CLR,
                    CH_OUT - WALL_IN,
                    plate_bot - ch_bot,
                    centered=(True, False, False),
                )
                .translate((tx, y0, ch_bot))
            )
            slide_channel = (
                cq.Workplane("XY")
                .box(
                    HOOK_L + 2 * HOOK_CLR + SLIDE,
                    CH_OUT - WALL_IN,
                    ch_top - ch_bot,
                    centered=(False, False, False),
                )
                .translate((tx - HOOK_L / 2 - HOOK_CLR - SLIDE, y0, ch_bot))
            )
            ring = ring.cut(drop_notch).cut(slide_channel)

    # Continue/enlarge the USB tunnel through the -X end of the raised band.
    # Final size must be transferred from the actual dry-fit, not blindly cut.
    usb = (
        cq.Workplane("XY")
        .box(4.0, 10.0, RING_TOTAL_H + 0.40, centered=(True, True, True))
        .translate((-SHELL_L / 2, 0, RING_TOTAL_H / 2))
    )
    return ring.cut(usb)


def make_primary_renata_screw_spacer(
    tongue_clearance_per_side: float = 0.20,
):
    """Separate Renata-only band with two support-free keyed mounting ears.

    Print in the same tongue-down orientation as the adhesive-only band.  The
    ears occupy local Z=0..1 mm, so every added surface grows directly from
    the build plate.  Separate square posts enter from the open case and clamp
    the ears; no unsupported downward screw tower is printed on the band.
    """
    band = make_spacer(tongue_clearance_per_side)
    for _, centre_y in SCREW_TOWER_CENTRES:
        if centre_y > 0:
            y_min = SCREW_EAR_INNER_Y
            y_max = CAVITY_W / 2 + 0.20
        else:
            y_min = -(CAVITY_W / 2 + 0.20)
            y_max = -SCREW_EAR_INNER_Y
        ear = (
            cq.Workplane("XY")
            .box(
                SCREW_EAR_X,
                y_max - y_min,
                FACE_T,
                centered=(True, True, False),
            )
            .translate((SCREW_TOWER_CENTRES[0][0], (y_min + y_max) / 2, 0))
        )
        band = band.union(ear)

    for centre in SCREW_TOWER_CENTRES:
        socket = (
            cq.Workplane("XY")
            .box(
                SCREW_POST_SOCKET,
                SCREW_POST_SOCKET,
                FACE_T + 0.20,
                centered=(True, True, False),
            )
            .translate((*centre, -0.10))
        )
        band = band.cut(socket)
    return band.clean()


def make_primary_renata_retainer_post_installed():
    """One keyed M2 post in installed coordinates, bottom at the body floor."""
    shaft = cq.Workplane("XY").box(
        SCREW_POST_SHAFT,
        SCREW_POST_SHAFT,
        SCREW_POST_INSTALLED_H,
        centered=(True, True, False),
    )
    head = (
        cq.Workplane("XY")
        .box(
            SCREW_POST_HEAD,
            SCREW_POST_HEAD,
            SCREW_POST_HEAD_T,
            centered=(True, True, False),
        )
        .translate((0, 0, SCREW_POST_INSTALLED_H))
    )
    # A 9.2 mm blind pilot receives the M2 x 10 screw after it crosses the
    # 1 mm nylon floor.  The remaining 0.6 mm roof prevents a visible hole in
    # the retainer head; actual screw length is still a physical release gate.
    pilot_depth = SCREW_POST_INSTALLED_H + 0.20
    pilot = (
        cq.Workplane("XY")
        .circle(SCREW_PILOT_D / 2)
        .extrude(pilot_depth + 0.10)
        .translate((0, 0, -0.10))
    )
    return shaft.union(head).cut(pilot).clean()


def make_primary_renata_retainer_posts_installed():
    """Both keyed posts in shell XY coordinates and installed floor-relative Z."""
    post = make_primary_renata_retainer_post_installed().val()
    return cq.Compound.makeCompound(
        [moved_shape(post, (*centre, 0)) for centre in SCREW_TOWER_CENTRES]
    )


def make_primary_renata_retainer_posts_print_pair():
    """Two posts, head-down on the build plate, with printable separation."""
    installed = make_primary_renata_retainer_post_installed().val()
    total_h = SCREW_POST_INSTALLED_H + SCREW_POST_HEAD_T
    head_down = moved_shape(installed.mirror("XY"), (0, 0, total_h))
    return cq.Compound.makeCompound(
        [
            moved_shape(head_down, (-4.0, 0, 0)),
            moved_shape(head_down, (4.0, 0, 0)),
        ]
    )


def make_primary_renata_body_drill_jig():
    """USB-keyed slip-over centre-marking jig; never a final drill bushing."""
    outer = cq.Workplane("XY").placeSketch(capsule(52.0, 23.0)).extrude(1.80)
    underside = cq.Workplane("XY").placeSketch(capsule(51.30, 22.30)).extrude(1.0)
    jig = outer.cut(underside)
    jig = (
        jig.faces(">Z")
        .workplane()
        .pushPoints(SCREW_TOWER_CENTRES)
        .hole(SCREW_JIG_GUIDE_D)
    )
    # The notch points to the shell's -X USB end and prevents a silent 180°
    # orientation error when the two centres are transferred to the body.
    notch = (
        cq.Workplane("XY")
        .box(2.4, 3.0, 2.2, centered=(True, True, False))
        .translate((-26.0, 0, 0.9))
    )
    return jig.cut(notch).clean()


def make_battery_safety_bridge():
    """Shelf-seated bridge; print deck-down and flip for installation.

    Four pads seat 0.02 mm above the exact shelf top, not through it.  The
    installed deck underside clears a true 5.50 mm pack on 0.05 mm insulation
    by 0.40 mm.
    """
    deck_l, deck_w, deck_t = 22.0, 17.40, BRIDGE_DECK_T
    pad_xy = 1.40
    deck = (
        cq.Workplane("XY")
        .box(deck_l, deck_w, deck_t, centered=(True, True, False))
        .translate((*XIAO_C, 0))
    )
    # Clear plastic and adhesive from the last 5 mm antenna region.
    antenna_window = (
        cq.Workplane("XY")
        .box(5.30, 13.60, deck_t + 0.20, centered=(True, True, False))
        .translate(((ANT_X0 + ANT_X1) / 2, 0, -0.10))
    )
    # Edge-open route for a relaxed short-cell lead loop.  It does not open a
    # hard-part path directly over the pouch.
    lead_notch = (
        cq.Workplane("XY")
        .box(3.0, 3.2, deck_t + 0.20, centered=(True, True, False))
        .translate((-2.0, -7.2, -0.10))
    )
    bridge = deck.cut(antenna_window).cut(lead_notch)
    for px, py in ((-16.0, 7.6), (-16.0, -7.6), (4.0, 7.8), (4.0, -7.8)):
        pad = (
            cq.Workplane("XY")
            .box(pad_xy, pad_xy, BRIDGE_PAD_H, centered=(True, True, False))
            .translate((px, py, deck_t))
        )
        bridge = bridge.union(pad)
    return bridge.clean()


def make_lower_gauge():
    """Bench-only lower-layer placement gauge; do not install in a ship unit."""
    base = cq.Workplane("XY").placeSketch(capsule(47.40, 18.40)).extrude(0.80)
    pockets = (
        cq.Workplane("XY")
        .box(BAT_L + 0.20, BAT_W + 0.20, 0.60, centered=(True, True, False))
        .translate((*BAT_C, 0.20))
        .union(
            cq.Workplane("XY")
            .box(MOTOR_D + 0.20, MOTOR_L + 0.20, 0.60, centered=(True, True, False))
            .translate((*MOTOR_C, 0.20))
        )
        .union(
            cq.Workplane("XY")
            .box(DRIVER_L + 0.20, DRIVER_W + 0.20, 0.60, centered=(True, True, False))
            .translate((*DRIVER_C, 0.20))
        )
    )
    return base.cut(pockets)


def make_xiao_gauge():
    """Bench-only plan gauge for the conservative official STEP bbox."""
    base = cq.Workplane("XY").placeSketch(capsule(47.40, 18.40)).extrude(0.80)
    pocket = (
        cq.Workplane("XY")
        .box(XIAO_L + 0.20, XIAO_W + 0.20, 0.60, centered=(True, True, False))
        .translate((*XIAO_C, 0.20))
    )
    return base.cut(pocket)


def alt_battery_center(length: float):
    return (ALT_BAT_LEFTS[length] + length / 2, 0.0)


def alt_coin_center(length: float):
    """Put the Vybronics motor opposite the cell with a gauge rim at the end."""
    # 18.6 mm made the 10.2 mm clearance pocket exactly tangent to the
    # 47.4 mm gauge boundary, creating a non-manifold STL edge. Moving the
    # motor 0.2 mm inward preserves a positive gauge wall.  The production
    # motor tolerance envelope is now 10.2 mm, so the retained wall is 0.1 mm.
    return (-18.4, 0.0) if length <= 15.0 else (18.4, 0.0)


def make_alt_local_lower_gauge(length: float):
    """Bench plan gauge for cell + Vybronics tolerance envelope + driver."""
    bc = alt_battery_center(length)
    base = cq.Workplane("XY").placeSketch(capsule(47.40, 18.40)).extrude(0.80)
    battery_pocket = (
        cq.Workplane("XY")
        .box(length + 0.20, ALT_BAT_W + 0.20, 0.60, centered=(True, True, False))
        .translate((*bc, 0.20))
    )
    coin_pocket = (
        cq.Workplane("XY")
        .center(*alt_coin_center(length))
        .circle((ALT_COIN_D + 0.20) / 2)
        .extrude(0.60)
        .translate((0, 0, 0.20))
    )
    driver_pocket = (
        cq.Workplane("XY")
        .box(DRIVER_L + 0.20, DRIVER_W + 0.20, 0.60, centered=(True, True, False))
        .translate((*DRIVER_C, 0.20))
    )
    return base.cut(battery_pocket.union(coin_pocket).union(driver_pocket))


def make_plan_b_lower_gauge():
    """Bench-only DTP401525/Vybronics/rotated-driver placement gauge.

    The 8 x 4 x 2 mm finished driver island is rotated so its 4 mm dimension
    occupies the X gap.  The finished hard parts have 0.40 mm nominal plan
    gaps; the pockets add 0.10 mm clearance per side and retain 0.20 mm gauge
    lands between them.  Never install this gauge in a unit.
    """
    base = cq.Workplane("XY").placeSketch(capsule(47.40, 18.40)).extrude(0.80)
    battery_pocket = (
        cq.Workplane("XY")
        .box(
            PLAN_B_BAT_L + 0.20,
            PLAN_B_BAT_W + 0.20,
            0.60,
            centered=(True, True, False),
        )
        .translate((*PLAN_B_BAT_C, 0.20))
    )
    coin_pocket = (
        cq.Workplane("XY")
        .center(*PLAN_B_COIN_C)
        .circle((ALT_COIN_D + 0.20) / 2)
        .extrude(0.60)
        .translate((0, 0, 0.20))
    )
    driver_pocket = (
        cq.Workplane("XY")
        .box(
            PLAN_B_DRIVER_L + 0.20,
            PLAN_B_DRIVER_W + 0.20,
            0.60,
            centered=(True, True, False),
        )
        .translate((*PLAN_B_DRIVER_C, 0.20))
    )
    return base.cut(battery_pocket.union(coin_pocket).union(driver_pocket))


def make_mic_drill_jig():
    """Slip-over guide with a 1.0 mm straight microphone guide hole."""
    outer = cq.Workplane("XY").placeSketch(capsule(52.0, 23.0)).extrude(1.80)
    underside = (
        cq.Workplane("XY")
        .placeSketch(capsule(51.30, 22.30))
        .extrude(1.0)
    )
    jig = outer.cut(underside)
    jig = jig.faces(">Z").workplane().pushPoints([MIC_C]).hole(1.0)
    # USB-end orientation notch in the outer -X rim.
    notch = (
        cq.Workplane("XY")
        .box(2.4, 3.0, 2.2, centered=(True, True, False))
        .translate((-26.0, 0, 0.9))
    )
    return jig.cut(notch)


def make_reference_assembly():
    z_cell = FLOOR_INSULATION
    z_xiao = FLOOR_INSULATION + BAT_H + CELL_TO_BOARD_BARRIER
    battery = (
        cq.Workplane("XY")
        .box(BAT_L, BAT_W, BAT_H, centered=(True, True, False))
        .translate((*BAT_C, z_cell))
    )
    xiao = (
        cq.Workplane("XY")
        .box(XIAO_L, XIAO_W, XIAO_H, centered=(True, True, False))
        .translate((*XIAO_C, z_xiao))
    )
    motor = (
        cq.Workplane("XZ")
        .circle(MOTOR_D / 2)
        .extrude(MOTOR_L / 2, both=True)
        .translate((*MOTOR_C, FLOOR_INSULATION + MOTOR_D / 2))
    )
    driver = (
        cq.Workplane("XY")
        .box(DRIVER_L, DRIVER_W, DRIVER_H, centered=(True, True, False))
        .translate((*DRIVER_C, FLOOR_INSULATION))
    )
    antenna = (
        cq.Workplane("XY")
        .box(ANT_L, XIAO_W, 0.40, centered=(True, True, False))
        .translate(((ANT_X0 + ANT_X1) / 2, XIAO_C[1], z_xiao + XIAO_H))
    )
    bridge_installed = (
        make_battery_safety_bridge()
        .mirror(mirrorPlane="XY")
        .translate((0, 0, BRIDGE_INSTALL_TOP_REL))
    )

    asm = cq.Assembly(name="ordered_shell_recovery_reference")
    asm.add(battery, name="MAX_finished_battery_25x10x5p5", color=cq.Color(0.25, 0.25, 0.25))
    asm.add(xiao, name="XIAO_official_bbox", color=cq.Color(0.10, 0.55, 0.20))
    asm.add(motor, name="barrel_motor_FULL_SWEPT_11p29x4p03", color=cq.Color(0.75, 0.75, 0.78))
    asm.add(driver, name="haptic_driver_zone", color=cq.Color(0.35, 0.20, 0.10))
    asm.add(bridge_installed, name="battery_safety_bridge_installed", color=cq.Color(0.15, 0.30, 0.75, 0.65))
    asm.add(antenna, name="antenna_keepout_last_5mm", color=cq.Color(1.0, 0.10, 0.10, 0.45))
    return asm, {
        "battery": battery,
        "xiao": xiao,
        "barrel_motor": motor,
        "driver": driver,
        "bridge": bridge_installed,
    }


def make_alt_local_reference(length: float):
    bc = alt_battery_center(length)
    coin_centre = alt_coin_center(length)
    z_xiao = FLOOR_INSULATION + ALT_BAT_H + CELL_TO_BOARD_BARRIER
    battery = (
        cq.Workplane("XY")
        .box(length, ALT_BAT_W, ALT_BAT_H, centered=(True, True, False))
        .translate((*bc, FLOOR_INSULATION))
    )
    xiao = (
        cq.Workplane("XY")
        .box(XIAO_L, XIAO_W, XIAO_H, centered=(True, True, False))
        .translate((*XIAO_C, z_xiao))
    )
    coin = (
        cq.Workplane("XY")
        .center(*coin_centre)
        .circle(ALT_COIN_D / 2)
        .extrude(ALT_COIN_T)
        .translate((0, 0, FLOOR_INSULATION))
    )
    driver = (
        cq.Workplane("XY")
        .box(DRIVER_L, DRIVER_W, DRIVER_H, centered=(True, True, False))
        .translate((*DRIVER_C, FLOOR_INSULATION))
    )
    antenna = (
        cq.Workplane("XY")
        .box(ANT_L, XIAO_W, 0.40, centered=(True, True, False))
        .translate(((ANT_X0 + ANT_X1) / 2, XIAO_C[1], z_xiao + XIAO_H))
    )
    bridge_installed = (
        make_battery_safety_bridge()
        .mirror(mirrorPlane="XY")
        .translate((0, 0, BRIDGE_INSTALL_TOP_REL))
    )
    asm = cq.Assembly(name=f"alternate_battery_{length:g}_Vybronics_10p2")
    asm.add(battery, name=f"MAX_finished_battery_{length:g}x10x5p5", color=cq.Color(0.25, 0.25, 0.25))
    asm.add(xiao, name="XIAO_official_bbox", color=cq.Color(0.10, 0.55, 0.20))
    asm.add(coin, name="Vybronics_VCLP1020B002L_MAX_10p2x2p3", color=cq.Color(0.75, 0.75, 0.78))
    asm.add(driver, name="haptic_driver_zone", color=cq.Color(0.35, 0.20, 0.10))
    asm.add(bridge_installed, name="battery_safety_bridge_installed", color=cq.Color(0.15, 0.30, 0.75, 0.65))
    asm.add(antenna, name="antenna_keepout_last_5mm", color=cq.Color(1.0, 0.10, 0.10, 0.45))
    return asm, {
        "battery": battery,
        "xiao": xiao,
        "coin_motor": coin,
        "driver": driver,
        "bridge": bridge_installed,
    }


def make_primary_renata_qualified_parts():
    """Renata screw-layout parts with its conservative motor fit envelope.

    This intentionally leaves every general alternate layout at the ordered
    Vybronics 10.2 x 2.3 mm tolerance envelope.  Only the screw-retained
    24 mm Renata architecture is qualified mechanically to 10.2 x 2.7 mm.
    """
    _, parts = make_alt_local_reference(24.0)
    parts = dict(parts)
    parts["coin_motor"] = (
        cq.Workplane("XY")
        .center(*alt_coin_center(24.0))
        .circle(PRIMARY_RENATA_MOTOR_MAX_D / 2)
        .extrude(PRIMARY_RENATA_MOTOR_MAX_T)
        .translate((0, 0, FLOOR_INSULATION))
    )
    z_xiao = FLOOR_INSULATION + ALT_BAT_H + CELL_TO_BOARD_BARRIER
    parts["antenna_keepout"] = (
        cq.Workplane("XY")
        .box(ANT_L, XIAO_W, 0.40, centered=(True, True, False))
        .translate(
            (
                (ANT_X0 + ANT_X1) / 2,
                XIAO_C[1],
                z_xiao + XIAO_H,
            )
        )
    )
    return parts


def make_plan_b_reference():
    """Conditional 25.3 x 15 x 4 mm cell and rotated-driver reference."""
    battery = (
        cq.Workplane("XY")
        .box(
            PLAN_B_BAT_L,
            PLAN_B_BAT_W,
            PLAN_B_BAT_H,
            centered=(True, True, False),
        )
        .translate((*PLAN_B_BAT_C, FLOOR_INSULATION))
    )
    # Keep the existing shelf-seated bridge and its board elevation.  It gives
    # this thinner cell more free space without requiring a second bridge.
    z_xiao = FLOOR_INSULATION + BAT_H + CELL_TO_BOARD_BARRIER
    xiao = (
        cq.Workplane("XY")
        .box(XIAO_L, XIAO_W, XIAO_H, centered=(True, True, False))
        .translate((*XIAO_C, z_xiao))
    )
    coin = (
        cq.Workplane("XY")
        .center(*PLAN_B_COIN_C)
        .circle(ALT_COIN_D / 2)
        .extrude(ALT_COIN_T)
        .translate((0, 0, FLOOR_INSULATION))
    )
    driver = (
        cq.Workplane("XY")
        .box(
            PLAN_B_DRIVER_L,
            PLAN_B_DRIVER_W,
            PLAN_B_DRIVER_H,
            centered=(True, True, False),
        )
        .translate((*PLAN_B_DRIVER_C, FLOOR_INSULATION))
    )
    bridge_installed = (
        make_battery_safety_bridge()
        .mirror(mirrorPlane="XY")
        .translate((0, 0, BRIDGE_INSTALL_TOP_REL))
    )

    asm = cq.Assembly(name="conditional_plan_b_DTP401525_Vybronics")
    asm.add(battery, name="MAX_DTP401525_envelope_25p3x15x4", color=cq.Color(0.25, 0.25, 0.25))
    asm.add(xiao, name="XIAO_official_bbox", color=cq.Color(0.10, 0.55, 0.20))
    asm.add(coin, name="Vybronics_VCLP1020B002L_MAX_10p2x2p3", color=cq.Color(0.75, 0.75, 0.78))
    asm.add(driver, name="rotated_driver_zone_4x8x2", color=cq.Color(0.35, 0.20, 0.10))
    asm.add(bridge_installed, name="existing_battery_safety_bridge", color=cq.Color(0.15, 0.30, 0.75, 0.65))
    return asm, {
        "battery": battery,
        "xiao": xiao,
        "coin_motor": coin,
        "driver_rotated": driver,
        "bridge": bridge_installed,
    }


def exact_shell_audit(
    spacer,
    spacer_loose,
    screw_spacer,
    screw_spacer_loose,
    screw_posts_installed,
    primary_parts,
    alternate_parts,
    primary_renata_parts,
    plan_b_parts,
):
    """Audit the real historical body/face solids, not a clean capsule.

    Coordinates in the component references are relative to the interior floor.
    The imported body floor top is global Z=1.0 mm.  The mid-band tongue nests
    in the body's original Z=9..10 mm rebate, and the raised face underside is
    global Z=13.0 mm.
    """
    if not BODY_STEP.exists() or not FACE_STEP.exists():
        raise FileNotFoundError(
            f"Exact shell references missing: {BODY_STEP} / {FACE_STEP}"
        )

    body = cq.importers.importStep(str(BODY_STEP)).val()
    face = cq.importers.importStep(str(FACE_STEP)).val()
    ring_z = BODY_H - FACE_T
    face_z = ring_z + RISE
    body_floor_z = FLOOR_T

    exact = {
        "reference_files": {
            "body": "reference/alu_body.step",
            "face": "reference/alu_face_front_v3.step",
        },
        "reference_bounds_mm": {
            "body": [
                body.BoundingBox().xlen,
                body.BoundingBox().ylen,
                body.BoundingBox().zlen,
            ],
            "face_with_hooks": [
                face.BoundingBox().xlen,
                face.BoundingBox().ylen,
                face.BoundingBox().zlen,
            ],
        },
        "assembly_positions_mm": {
            "midband_global_z": ring_z,
            "face_global_z": face_z,
            "face_drop_x": SLIDE / 2,
            "face_locked_x": -SLIDE / 2,
            "component_floor_global_z": body_floor_z,
        },
    }

    rings = {
        "nominal": moved_shape(spacer, (0, 0, ring_z)),
        "loose": moved_shape(spacer_loose, (0, 0, ring_z)),
        "PRIMARY_RENATA_ONLY_M2_nominal": moved_shape(
            screw_spacer, (0, 0, ring_z)
        ),
        "PRIMARY_RENATA_ONLY_M2_loose": moved_shape(
            screw_spacer_loose, (0, 0, ring_z)
        ),
    }
    exact["body_to_midband_intersection_mm3"] = {
        name: intersection_volume(body, ring) for name, ring in rings.items()
    }

    # Sample the physical face motion: vertical drop at the unlocked X
    # position, then the complete horizontal hook-lock slide. The imported
    # face includes all four hook solids below its main plate.
    face_drop_path = {}
    face_path = {}
    for ring_name, ring in rings.items():
        drop_samples = {}
        for index in range(13):
            z = face_z + 3.0 - 3.0 * index / 12
            positioned_face = moved_shape(face, (SLIDE / 2, 0, z))
            drop_samples[f"z_{z:+.3f}"] = intersection_volume(
                ring, positioned_face
            )
        face_drop_path[ring_name] = drop_samples

        samples = {}
        for index in range(21):
            x = SLIDE / 2 - SLIDE * index / 20
            positioned_face = moved_shape(face, (x, 0, face_z))
            samples[f"x_{x:+.3f}"] = intersection_volume(ring, positioned_face)
        face_path[ring_name] = samples
    exact["face_to_midband_drop_path_intersection_mm3"] = face_drop_path
    exact["face_to_midband_slide_path_intersection_mm3"] = face_path

    def audit_layout(parts):
        global_parts = {
            name: moved_shape(part, (0, 0, body_floor_z))
            for name, part in parts.items()
        }
        result = {
            "part_to_body_intersection_mm3": {},
            "part_to_nominal_midband_intersection_mm3": {},
            "part_to_locked_face_intersection_mm3": {},
            "part_pair_intersection_mm3": {},
        }
        locked_face = moved_shape(face, (-SLIDE / 2, 0, face_z))
        for name, part in global_parts.items():
            result["part_to_body_intersection_mm3"][name] = intersection_volume(
                part, body
            )
            result["part_to_nominal_midband_intersection_mm3"][name] = (
                intersection_volume(part, rings["nominal"])
            )
            result["part_to_locked_face_intersection_mm3"][name] = (
                intersection_volume(part, locked_face)
            )
        names = sorted(global_parts)
        # Board-to-bridge contact is intentional through a controlled adhesive
        # layer and is modeled as zero-volume touching surfaces, not overlap.
        for i, left in enumerate(names):
            for right in names[i + 1 :]:
                result["part_pair_intersection_mm3"][f"{left}__{right}"] = (
                    intersection_volume(global_parts[left], global_parts[right])
                )
        return result

    exact["primary_25mm_cell_barrel_layout"] = audit_layout(primary_parts)
    exact["alternate_battery_Vybronics_layouts"] = {
        f"battery_{length:g}x10x5p5": audit_layout(parts)
        for length, parts in alternate_parts.items()
    }
    exact["conditional_plan_b_DTP401525_Vybronics_layout"] = audit_layout(
        plan_b_parts
    )

    def audit_face_motion_against_parts(parts):
        global_parts = {
            name: moved_shape(part, (0, 0, body_floor_z))
            for name, part in parts.items()
        }
        samples = {}
        for index in range(13):
            z = face_z + 3.0 - 3.0 * index / 12
            positioned_face = moved_shape(face, (SLIDE / 2, 0, z))
            samples[f"drop_z_{z:+.3f}"] = {
                name: intersection_volume(positioned_face, part)
                for name, part in global_parts.items()
            }
        for index in range(21):
            x = SLIDE / 2 - SLIDE * index / 20
            positioned_face = moved_shape(face, (x, 0, face_z))
            samples[f"slide_x_{x:+.3f}"] = {
                name: intersection_volume(positioned_face, part)
                for name, part in global_parts.items()
            }
        return samples

    exact["face_to_components_drop_and_slide_path_intersection_mm3"] = {
        "primary_25mm_cell_barrel_layout": audit_face_motion_against_parts(
            primary_parts
        ),
        **{
            f"battery_{length:g}x10x5p5_Vybronics": audit_face_motion_against_parts(
                parts
            )
            for length, parts in alternate_parts.items()
        },
        "conditional_plan_b_DTP401525_Vybronics": audit_face_motion_against_parts(
            plan_b_parts
        ),
    }

    # The no-adhesive closure is intentionally narrower than the general fit
    # study: it is released only with the 24 x 10 x 5.5 mm Renata-class cell,
    # a motor no larger than 10.2 x 10.2 x 2.7 mm, and the ordinary 8 x 4 mm
    # driver placement.  That conservative motor envelope covers the listed
    # Lee PID10431 body but does not qualify its electrical identity.
    # The post pair is represented after installation, with its shaft bottoms
    # exactly touching the inside face of the 1 mm body floor.
    screw_ring = rings["PRIMARY_RENATA_ONLY_M2_nominal"]
    posts_global = moved_shape(
        screw_posts_installed, (0, 0, body_floor_z)
    )
    renata_parts_global = {
        name: moved_shape(part, (0, 0, body_floor_z))
        for name, part in primary_renata_parts.items()
    }
    individual_posts_global = {
        f"post_{index}": moved_shape(
            make_primary_renata_retainer_post_installed(),
            (*centre, body_floor_z),
        )
        for index, centre in enumerate(SCREW_TOWER_CENTRES, start=1)
    }

    screw_face_path = {}
    for index in range(13):
        z = face_z + 3.0 - 3.0 * index / 12
        positioned_face = moved_shape(face, (SLIDE / 2, 0, z))
        screw_face_path[f"drop_z_{z:+.3f}"] = intersection_volume(
            positioned_face, posts_global
        )
    for index in range(21):
        x = SLIDE / 2 - SLIDE * index / 20
        positioned_face = moved_shape(face, (x, 0, face_z))
        screw_face_path[f"slide_x_{x:+.3f}"] = intersection_volume(
            positioned_face, posts_global
        )

    full_height_drill_axes = {}
    floor_clearance_holes = {}
    conservative_countersinks = {}
    for index, centre in enumerate(SCREW_TOWER_CENTRES, start=1):
        full_height_drill_axes[f"post_{index}"] = (
            cq.Workplane("XY")
            .center(*centre)
            .circle(SCREW_BODY_CLEAR_MAX_D / 2)
            .extrude(BODY_H + RISE + 1.0)
            .translate((0, 0, -0.50))
            .val()
        )
        floor_clearance_holes[f"post_{index}"] = (
            cq.Workplane("XY")
            .center(*centre)
            .circle(SCREW_BODY_CLEAR_MAX_D / 2)
            .extrude(FLOOR_T + 0.20)
            .translate((0, 0, -0.10))
            .val()
        )
        # A cylinder is deliberately more conservative than the shallow 90°
        # cone made in practice: if this envelope misses a feature, the actual
        # countersink misses it too.  Stop at the real screw head, never at a
        # nominal depth or this maximum diameter.
        conservative_countersinks[f"post_{index}"] = (
            cq.Workplane("XY")
            .center(*centre)
            .circle(SCREW_COUNTERSINK_MAX_D / 2)
            .extrude(FLOOR_T + 0.20)
            .translate((0, 0, -0.10))
            .val()
        )

    antenna_through_bbox = (
        cq.Workplane("XY")
        .box(
            ANTENNA_WINDOW_THROUGH_L,
            ANTENNA_WINDOW_THROUGH_W,
            FLOOR_T + 0.20,
            centered=(True, True, False),
        )
        .translate((ANTENNA_WINDOW_X, 0, -0.10))
        .val()
    )
    antenna_recess_bbox = (
        cq.Workplane("XY")
        .box(
            ANTENNA_WINDOW_RECESS_L,
            ANTENNA_WINDOW_RECESS_W,
            0.70,
            centered=(True, True, False),
        )
        .translate((ANTENNA_WINDOW_X, 0, 0.40))
        .val()
    )

    # Dedicated conservative motor qualification for the screw-retained
    # Renata architecture.  The 10.2 mm diameter is the larger Vybronics
    # tolerance diameter; 2.7 mm is the taller Lee listed thickness.  Testing
    # their combined bounding envelope is stricter than either listed body.
    qualified_motor = renata_parts_global["coin_motor"]
    locked_face = moved_shape(face, (-SLIDE / 2, 0, face_z))
    qualified_motor_face_path = {}
    for index in range(13):
        z = face_z + 3.0 - 3.0 * index / 12
        positioned_face = moved_shape(face, (SLIDE / 2, 0, z))
        qualified_motor_face_path[f"drop_z_{z:+.3f}"] = intersection_volume(
            positioned_face, qualified_motor
        )
    for index in range(21):
        x = SLIDE / 2 - SLIDE * index / 20
        positioned_face = moved_shape(face, (x, 0, face_z))
        qualified_motor_face_path[f"slide_x_{x:+.3f}"] = (
            intersection_volume(positioned_face, qualified_motor)
        )

    qualified_motor_to_parts = {
        name: intersection_volume(qualified_motor, part)
        for name, part in renata_parts_global.items()
        if name != "coin_motor"
    }
    qualified_motor_to_posts = {
        name: intersection_volume(qualified_motor, post)
        for name, post in individual_posts_global.items()
    }
    qualified_motor_to_drill_axes = {
        name: intersection_volume(qualified_motor, axis)
        for name, axis in full_height_drill_axes.items()
    }
    motor_bbox = qualified_motor.BoundingBox()
    bridge_bbox = renata_parts_global["bridge"].BoundingBox()
    xiao_bbox = renata_parts_global["xiao"].BoundingBox()
    band_bbox = screw_ring.BoundingBox()
    face_bbox = locked_face.BoundingBox()
    qualified_motor_z_clearances = {
        "to_bridge_lowest_geometry": bridge_bbox.zmin - motor_bbox.zmax,
        "to_xiao_bottom": xiao_bbox.zmin - motor_bbox.zmax,
        "to_screw_band_bottom": band_bbox.zmin - motor_bbox.zmax,
        "to_locked_face_lowest_geometry": face_bbox.zmin - motor_bbox.zmax,
        "to_recovered_main_clear_height": (
            body_floor_z + MAIN_CLEAR_H - motor_bbox.zmax
        ),
    }
    qualified_motor_audit = {
        "mechanical_envelope_max_mm": [
            PRIMARY_RENATA_MOTOR_MAX_D,
            PRIMARY_RENATA_MOTOR_MAX_D,
            PRIMARY_RENATA_MOTOR_MAX_T,
        ],
        "existing_centre_xy_mm": alt_coin_center(24.0),
        "covers_listed_Lee_PID10431_body_mm": [
            LEE_COIN_D,
            LEE_COIN_D,
            LEE_COIN_T,
        ],
        "mechanical_fit_does_not_qualify_electrical_identity": True,
        "to_exact_nylon_body_intersection_mm3": intersection_volume(
            qualified_motor, body
        ),
        "to_screw_band_intersection_mm3": intersection_volume(
            qualified_motor, screw_ring
        ),
        "to_locked_nylon_face_intersection_mm3": intersection_volume(
            qualified_motor, locked_face
        ),
        "to_full_nylon_face_drop_and_slide_path_intersection_mm3": (
            qualified_motor_face_path
        ),
        "to_primary_parts_intersection_mm3": qualified_motor_to_parts,
        "to_each_retainer_post_intersection_mm3": qualified_motor_to_posts,
        "to_each_full_height_2p4mm_drill_axis_intersection_mm3": (
            qualified_motor_to_drill_axes
        ),
        "global_z_bounds_mm": [motor_bbox.zmin, motor_bbox.zmax],
        "positive_z_clearances_mm": qualified_motor_z_clearances,
    }

    component_to_drill_axis = {}
    for drill_name, drill_axis in full_height_drill_axes.items():
        component_to_drill_axis[drill_name] = {
            name: intersection_volume(drill_axis, part)
            for name, part in renata_parts_global.items()
        }

    countersink_to_antenna = {}
    clearance_to_antenna = {}
    body_floor_material = {}
    for drill_name in full_height_drill_axes:
        clearance = floor_clearance_holes[drill_name]
        countersink = conservative_countersinks[drill_name]
        body_floor_material[drill_name] = intersection_volume(clearance, body)
        clearance_to_antenna[drill_name] = {
            "through_opening_bbox": intersection_volume(
                clearance, antenna_through_bbox
            ),
            "flange_recess_bbox": intersection_volume(
                clearance, antenna_recess_bbox
            ),
        }
        countersink_to_antenna[drill_name] = {
            "through_opening_bbox": intersection_volume(
                countersink, antenna_through_bbox
            ),
            "flange_recess_bbox": intersection_volume(
                countersink, antenna_recess_bbox
            ),
        }

    screw_to_components = {
        "band": {
            name: intersection_volume(screw_ring, part)
            for name, part in renata_parts_global.items()
        },
        "posts": {
            name: intersection_volume(posts_global, part)
            for name, part in renata_parts_global.items()
        },
    }
    plan_b_driver_global = moved_shape(
        plan_b_parts["driver_rotated"], (0, 0, body_floor_z)
    )
    plan_b_post_driver_overlap = intersection_volume(
        posts_global, plan_b_driver_global
    )
    exact["PRIMARY_RENATA_ONLY_M2_screw_retention"] = {
        "scope": "24x10x5.5_mm_Renata_class_cell_plus_motor_envelope_max_10p2x10p2x2p7",
        "explicitly_incompatible_with_conditional_plan_b": True,
        "post_centres_xy_mm": SCREW_TOWER_CENTRES,
        "band_to_body_intersection_mm3": exact[
            "body_to_midband_intersection_mm3"
        ]["PRIMARY_RENATA_ONLY_M2_nominal"],
        "posts_to_body_intersection_mm3": intersection_volume(
            posts_global, body
        ),
        "posts_to_band_intersection_mm3": intersection_volume(
            posts_global, screw_ring
        ),
        "face_to_posts_drop_and_slide_path_intersection_mm3": screw_face_path,
        "band_and_posts_to_primary_components_intersection_mm3": (
            screw_to_components
        ),
        "full_height_2p4mm_max_drill_axis_to_primary_components_intersection_mm3": (
            component_to_drill_axis
        ),
        "2p4mm_max_floor_hole_to_antenna_features_intersection_mm3": (
            clearance_to_antenna
        ),
        "4p0mm_max_countersink_envelope_to_antenna_features_intersection_mm3": (
            countersink_to_antenna
        ),
        "exact_body_material_on_each_2p4mm_max_floor_axis_mm3": body_floor_material,
        "conditional_plan_b_rotated_driver_to_posts_intersection_mm3": (
            plan_b_post_driver_overlap
        ),
        "plan_b_rejection_passes_when_intersection_is_positive": (
            plan_b_post_driver_overlap > 1e-6
        ),
        "qualified_motor_max_envelope_audit": qualified_motor_audit,
    }

    all_volumes = []
    all_volumes.extend(exact["body_to_midband_intersection_mm3"].values())
    for ring_samples in exact[
        "face_to_midband_drop_path_intersection_mm3"
    ].values():
        all_volumes.extend(ring_samples.values())
    for ring_samples in exact[
        "face_to_midband_slide_path_intersection_mm3"
    ].values():
        all_volumes.extend(ring_samples.values())
    for layout in [
        exact["primary_25mm_cell_barrel_layout"],
        *exact["alternate_battery_Vybronics_layouts"].values(),
        exact["conditional_plan_b_DTP401525_Vybronics_layout"],
    ]:
        for section in layout.values():
            all_volumes.extend(section.values())
    for layout_samples in exact[
        "face_to_components_drop_and_slide_path_intersection_mm3"
    ].values():
        for part_volumes in layout_samples.values():
            all_volumes.extend(part_volumes.values())
    all_volumes.extend(screw_face_path.values())
    for section in screw_to_components.values():
        all_volumes.extend(section.values())
    for section in component_to_drill_axis.values():
        all_volumes.extend(section.values())
    for section in clearance_to_antenna.values():
        all_volumes.extend(section.values())
    for section in countersink_to_antenna.values():
        all_volumes.extend(section.values())
    all_volumes.extend(
        [
            qualified_motor_audit[
                "to_exact_nylon_body_intersection_mm3"
            ],
            qualified_motor_audit["to_screw_band_intersection_mm3"],
            qualified_motor_audit[
                "to_locked_nylon_face_intersection_mm3"
            ],
        ]
    )
    all_volumes.extend(qualified_motor_face_path.values())
    all_volumes.extend(qualified_motor_to_parts.values())
    all_volumes.extend(qualified_motor_to_posts.values())
    all_volumes.extend(qualified_motor_to_drill_axes.values())
    all_volumes.extend(
        [
            exact["PRIMARY_RENATA_ONLY_M2_screw_retention"][
                "posts_to_body_intersection_mm3"
            ],
            exact["PRIMARY_RENATA_ONLY_M2_screw_retention"][
                "posts_to_band_intersection_mm3"
            ],
        ]
    )

    # OCC booleans sometimes report numerical dust at touching faces.  A
    # 1e-6 mm^3 ceiling is far below any printable or physical interference.
    tolerance = 1e-6
    exact["intersection_value_count"] = len(all_volumes)
    exact["intersection_tolerance_mm3"] = tolerance
    exact["maximum_intersection_mm3"] = max(all_volumes, default=0.0)
    exact["all_exact_intersections_within_tolerance"] = all(
        value <= tolerance for value in all_volumes
    )
    if not exact["all_exact_intersections_within_tolerance"]:
        raise AssertionError(
            "Exact historical shell audit failed; see exact-shell report values"
        )
    if min(qualified_motor_z_clearances.values()) <= 0:
        raise AssertionError(
            "PRIMARY_RENATA_ONLY 10.2 x 10.2 x 2.7 mm motor lacks positive Z clearance"
        )
    minimum_floor_material = (
        math.pi * (SCREW_BODY_CLEAR_MAX_D / 2) ** 2 * 0.99
    )
    exact["PRIMARY_RENATA_ONLY_M2_screw_retention"][
        "minimum_required_body_floor_material_per_2p4mm_axis_mm3"
    ] = minimum_floor_material
    if not all(
        volume >= minimum_floor_material
        for volume in body_floor_material.values()
    ):
        raise AssertionError(
            "M2 drill axis does not cross a complete 1 mm body-floor region"
        )
    if plan_b_post_driver_overlap <= tolerance:
        raise AssertionError(
            "Plan B incompatibility audit failed: posts no longer reject the rotated driver"
        )

    exact_asm = cq.Assembly(name="exact_historical_shell_recovery")
    exact_asm.add(body, name="historical_body", color=cq.Color(0.78, 0.78, 0.82))
    exact_asm.add(rings["nominal"], name="printed_midband", color=cq.Color(0.08, 0.08, 0.10))
    exact_asm.add(
        moved_shape(face, (-SLIDE / 2, 0, face_z)),
        name="historical_face_locked",
        color=cq.Color(0.88, 0.88, 0.90),
    )
    for name, part in primary_parts.items():
        exact_asm.add(
            moved_shape(part, (0, 0, body_floor_z)),
            name=f"primary_{name}",
        )
    exact_asm.export(str(OUT / "EXACT_historical_body_face_recovery_assembly.step"))

    screw_asm = cq.Assembly(name="PRIMARY_RENATA_ONLY_M2_screw_retention")
    screw_asm.add(body, name="historical_body", color=cq.Color(0.78, 0.78, 0.82))
    screw_asm.add(
        screw_ring,
        name="M2_screw_retained_midband",
        color=cq.Color(0.08, 0.08, 0.10),
    )
    screw_asm.add(
        posts_global,
        name="two_keyed_retainer_posts",
        color=cq.Color(0.15, 0.30, 0.75),
    )
    screw_asm.add(
        moved_shape(face, (-SLIDE / 2, 0, face_z)),
        name="historical_face_locked",
        color=cq.Color(0.88, 0.88, 0.90),
    )
    for name, part in primary_renata_parts.items():
        screw_asm.add(
            moved_shape(part, (0, 0, body_floor_z)),
            name=f"PRIMARY_RENATA_{name}",
        )
    screw_asm.export(
        str(OUT / "PRIMARY_RENATA_ONLY_M2_screw_retention_reference.step")
    )
    return exact


def fit_report(exact_shell):
    stack = FLOOR_INSULATION + BAT_H + CELL_TO_BOARD_BARRIER + XIAO_H + TOP_CLEARANCE
    height_shortage = stack - ORIGINAL_CLEAR_H
    battery_right = BAT_C[0] + BAT_L / 2
    antenna_overlap = max(0.0, min(battery_right, ANT_X1) - max(BAT_C[0] - BAT_L / 2, ANT_X0))
    checks = {
        "xiao_plan_inside_nominal_capsule": rect_in_capsule(*XIAO_C, XIAO_L, XIAO_W),
        "battery_plan_inside_nominal_capsule": rect_in_capsule(*BAT_C, BAT_L, BAT_W),
        "motor_plan_inside_nominal_capsule": rect_in_capsule(*MOTOR_C, MOTOR_D, MOTOR_L),
        "driver_plan_inside_nominal_capsule": rect_in_capsule(*DRIVER_C, DRIVER_L, DRIVER_W),
        "original_8mm_height_fits": stack <= ORIGINAL_CLEAR_H,
        "raised_main_height_fits": stack <= MAIN_CLEAR_H,
        "raised_hook_zone_fits_without_top_allowance": (
            FLOOR_INSULATION + BAT_H + CELL_TO_BOARD_BARRIER + XIAO_H <= HOOK_ZONE_CLEAR_H
        ),
    }
    alternate_local = {}
    for length in ALT_BAT_LS:
        bc = alt_battery_center(length)
        coin_centre = alt_coin_center(length)
        batt_right = bc[0] + length / 2
        overlap = max(0.0, min(batt_right, ANT_X1) - max(bc[0] - length / 2, ANT_X0))
        batt_left = bc[0] - length / 2
        if coin_centre[0] < bc[0]:
            coin_gap = batt_left - (coin_centre[0] + ALT_COIN_D / 2)
        else:
            coin_gap = coin_centre[0] - ALT_COIN_D / 2 - batt_right
        alternate_local[f"battery_{length:g}x10x5p5_Vybronics_10p2x2p3"] = {
            "battery_centre_mm": bc,
            "coin_centre_mm": coin_centre,
            "battery_inside_capsule": rect_in_capsule(*bc, length, ALT_BAT_W),
            "coin_inside_capsule_exact_circle_test": circle_in_capsule(*coin_centre, ALT_COIN_D),
            "coin_shell_radial_margin_mm": CAVITY_W / 2 - ALT_COIN_D / 2 - (abs(coin_centre[0]) - (CAVITY_L - CAVITY_W) / 2),
            "coin_to_battery_plan_gap_mm": coin_gap,
            "battery_foil_overlap_into_last_5mm_antenna_zone": overlap,
            "antenna_tip_not_over_battery": ANT_X1 - max(ANT_X0, batt_right),
            "vertical_required_mm": stack,
            "raised_main_margin_mm": MAIN_CLEAR_H - stack,
            "coin_to_bridge_vertical_clearance_mm": BRIDGE_DECK_UNDERSIDE_REL - (FLOOR_INSULATION + ALT_COIN_T),
        }

    plan_b_battery_right = PLAN_B_BAT_C[0] + PLAN_B_BAT_L / 2
    plan_b_battery_left = PLAN_B_BAT_C[0] - PLAN_B_BAT_L / 2
    plan_b_driver_left = PLAN_B_DRIVER_C[0] - PLAN_B_DRIVER_L / 2
    plan_b_driver_right = PLAN_B_DRIVER_C[0] + PLAN_B_DRIVER_L / 2
    plan_b_coin_left = PLAN_B_COIN_C[0] - ALT_COIN_D / 2
    plan_b_cell_top = FLOOR_INSULATION + PLAN_B_BAT_H
    shelf_underside_from_floor = SHELF_BOTTOM_GLOBAL - FLOOR_T
    plan_b_overlap = max(
        0.0,
        min(plan_b_battery_right, ANT_X1)
        - max(plan_b_battery_left, ANT_X0),
    )
    conditional_plan_b = {
        "status": "CAD candidate only; exact received pack identity, documents, caliper measurements, lead route and no-pressure closure remain mandatory",
        "documented_reference": "SparkFun PRT-13853 / Data Power DTP401525; not evidence that Lee PID8834 is the same pack",
        "battery_total_envelope_mm": [
            PLAN_B_BAT_L,
            PLAN_B_BAT_W,
            PLAN_B_BAT_H,
        ],
        "battery_centre_mm": PLAN_B_BAT_C,
        "Vybronics_motor_envelope_mm": [ALT_COIN_D, ALT_COIN_D, ALT_COIN_T],
        "motor_centre_mm": PLAN_B_COIN_C,
        "rotated_driver_envelope_mm": [
            PLAN_B_DRIVER_L,
            PLAN_B_DRIVER_W,
            PLAN_B_DRIVER_H,
        ],
        "driver_centre_mm": PLAN_B_DRIVER_C,
        "existing_bridge_reused": True,
        "battery_inside_capsule": rect_in_capsule(
            *PLAN_B_BAT_C, PLAN_B_BAT_L, PLAN_B_BAT_W
        ),
        "motor_inside_capsule_exact_circle_test": circle_in_capsule(
            *PLAN_B_COIN_C, ALT_COIN_D
        ),
        "driver_inside_capsule": rect_in_capsule(
            *PLAN_B_DRIVER_C, PLAN_B_DRIVER_L, PLAN_B_DRIVER_W
        ),
        "battery_to_driver_plan_gap_mm": plan_b_driver_left
        - plan_b_battery_right,
        "driver_to_motor_plan_gap_mm": plan_b_coin_left
        - plan_b_driver_right,
        "battery_top_from_floor_mm": plan_b_cell_top,
        "historical_shelf_underside_from_floor_mm": shelf_underside_from_floor,
        "nominal_battery_to_shelf_underside_gap_mm": shelf_underside_from_floor
        - plan_b_cell_top,
        "existing_bridge_deck_underside_from_floor_mm": BRIDGE_DECK_UNDERSIDE_REL,
        "nominal_battery_to_bridge_gap_mm": BRIDGE_DECK_UNDERSIDE_REL
        - plan_b_cell_top,
        "battery_foil_overlap_into_last_5mm_antenna_zone": plan_b_overlap,
    }

    renata_battery_right = alt_battery_center(24.0)[0] + 24.0 / 2
    screw_post_left = SCREW_TOWER_CENTRES[0][0] - SCREW_POST_SHAFT / 2
    screw_post_right = SCREW_TOWER_CENTRES[0][0] + SCREW_POST_SHAFT / 2
    xiao_right = XIAO_C[0] + XIAO_L / 2
    primary_motor_left = (
        alt_coin_center(24.0)[0] - PRIMARY_RENATA_MOTOR_MAX_D / 2
    )
    antenna_through_left = (
        ANTENNA_WINDOW_X - ANTENNA_WINDOW_THROUGH_L / 2
    )
    antenna_recess_left = (
        ANTENNA_WINDOW_X - ANTENNA_WINDOW_RECESS_L / 2
    )
    primary_renata_screw_retention = {
        "status": "CAD PASS against exact historical STEP; physical drill coupon, actual M2 screw and destructive retention tests remain mandatory",
        "scope": "Renata ICP501022UPM / part 100640 envelope <=24x10x5.5 mm plus mechanically qualified motor envelope <=10.2x10.2x2.7 mm",
        "motor_qualification": {
            "mechanical_envelope_max_mm": [
                PRIMARY_RENATA_MOTOR_MAX_D,
                PRIMARY_RENATA_MOTOR_MAX_D,
                PRIMARY_RENATA_MOTOR_MAX_T,
            ],
            "ordered_Vybronics_is_inside_envelope": True,
            "listed_Lee_PID10431_body_is_inside_envelope": True,
            "Lee_release_still_requires": [
                "received finished body passes the max-envelope gauge",
                "manufacturer and part identity",
                "rated voltage, current, startup/stall peak and duty limit",
                "matched driver and firmware polarity",
                "open- and closed-case electrical, thermal, audio, BLE/RF, haptic and abuse tests",
            ],
        },
        "not_compatible_with": [
            "conditional Plan B 25.3x15x4 mm battery plus rotated 4x8x2 mm driver",
            "barrel-motor primary layout",
            "either adhesive-only midband filename",
        ],
        "print_files": [
            "PRINT_FULL_SHELL_body_exact_historical_geometry.stl",
            "PRINT_FULL_SHELL_hooked_face_exact_historical_geometry.stl",
            "PRIMARY_RENATA_ONLY_M2_screw_retained_midband_rise_4p50mm_nominal.stl",
            "PRINT_TWO_PRIMARY_RENATA_ONLY_M2_keyed_retainer_posts_HEAD_DOWN.stl",
            "PRIMARY_RENATA_ONLY_M2_body_drill_marking_jig_USB_NOTCH.stl",
            "PRIMARY_RENATA_ONLY_MEASURE_MAX_coin_motor_10p2x2p7.stl",
        ],
        "post_centres_xy_mm": SCREW_TOWER_CENTRES,
        "post_geometry_mm": {
            "keyed_shaft_square": SCREW_POST_SHAFT,
            "band_socket_square": SCREW_POST_SOCKET,
            "head_square": SCREW_POST_HEAD,
            "head_thickness": SCREW_POST_HEAD_T,
            "installed_shaft_height": SCREW_POST_INSTALLED_H,
            "printed_blind_M2_pilot_diameter": SCREW_PILOT_D,
        },
        "body_drill_geometry_mm": {
            "jig_marking_holes": SCREW_JIG_GUIDE_D,
            "preferred_body_clearance_holes": SCREW_BODY_CLEAR_D,
            "maximum_audited_body_clearance_holes": (
                SCREW_BODY_CLEAR_MAX_D
            ),
            "approved_imperial_substitute": "3/32 inch = 2.38125 mm",
            "countersink_included_angle_deg": 90,
            "conservative_max_countersink_diameter": SCREW_COUNTERSINK_MAX_D,
            "rule": "stop as soon as the actual flat-head screw is flush; 4.0 mm is an audit ceiling, not a machining target",
        },
        "target_fastener": {
            "description": "M2 x 10 mm flat countersunk screw, 2 required plus spares",
            "local_candidate": "Lee's Electronic PID6836; online finish is unspecified",
            "url": "https://leeselectronic.com/en/product/6836-screw-m2x10mm-flat-countersunk-10pcspkg.html",
        },
        "nominal_hard_part_plan_gaps_mm": {
            "Renata_battery_to_post_shaft": screw_post_left
            - renata_battery_right,
            "post_shaft_to_primary_motor_max_x_envelope": primary_motor_left
            - screw_post_right,
            "XIAO_to_post_shaft": screw_post_left - xiao_right,
            "2p4mm_max_hole_edge_to_antenna_through_opening_bbox": (
                antenna_through_left
                - (
                    SCREW_TOWER_CENTRES[0][0]
                    + SCREW_BODY_CLEAR_MAX_D / 2
                )
            ),
            "2p4mm_max_hole_edge_to_antenna_flange_recess_bbox": (
                antenna_recess_left
                - (
                    SCREW_TOWER_CENTRES[0][0]
                    + SCREW_BODY_CLEAR_MAX_D / 2
                )
            ),
            "4p0mm_countersink_edge_to_antenna_flange_recess_bbox": (
                antenna_recess_left
                - (
                    SCREW_TOWER_CENTRES[0][0]
                    + SCREW_COUNTERSINK_MAX_D / 2
                )
            ),
        },
        "assembly_release_gates": [
            "Use an empty sacrificial body for the first drill and countersink; remove the battery, PCB, motor and antenna-window insert before every drilling operation.",
            "Seat the USB-notched jig, transfer both centres through its 1.0 mm holes, remove the jig, drill 1.0 mm pilots, then enlarge the body to 2.2 mm preferred or no more than the audited 2.4 mm; a 3/32 inch (2.381 mm) bit is allowed.",
            "Make each 90 degree countersink from the outside and stop when the actual M2 flat head is flush; never drill to the 4.0 mm audit ceiling by measurement alone.",
            "Hand-thread or M2x0.4 tap the actual printed post's 1.6 mm blind pilot before final assembly; reject splitting, whitening, loose threads or a bottomed screw.",
            "Deburr, vacuum and inspect both sides until no plastic or metal swarf remains before any battery returns to the enclosure.",
            "Torque only until the post head seats and the band cannot lift; use thread-safe low-strength retention only after material compatibility is proven, never extra torque.",
            "Release only after 100 vigorous hand shakes, a controlled 1 m drop sequence onto a protected hard surface, torsion, face removal/reinstall and a second electrical/thermal/RF test show no loosening, cracks or battery contact.",
        ],
    }

    report = {
        "status": "CAD PASS with 4.50 mm-rise band against exact historical body/face geometry; a printed or ordered physical shell and all finished components still require gauges and no-load closure",
        "ordered_shell_nominal_mm": {
            "outer_closed_original": [51.0, 22.0, 10.0],
            "cavity_plan": [48.0, 19.0],
            "original_clear_height": ORIGINAL_CLEAR_H,
            "recovered_main_clear_height": MAIN_CLEAR_H,
            "recovered_hook_zone_clear_height": HOOK_ZONE_CLEAR_H,
            "recovered_outer_height": BODY_H + RISE,
        },
        "component_envelopes_mm": {
            "xiao_official_step_bbox": [XIAO_L, XIAO_W, XIAO_H],
            "battery_finished_maximum": [BAT_L, BAT_W, BAT_H],
            "Vybronics_VCLP1020B002L_tolerance_max": [
                ALT_COIN_D,
                ALT_COIN_D,
                ALT_COIN_T,
            ],
            "PRIMARY_RENATA_ONLY_motor_mechanical_max": [
                PRIMARY_RENATA_MOTOR_MAX_D,
                PRIMARY_RENATA_MOTOR_MAX_D,
                PRIMARY_RENATA_MOTOR_MAX_T,
            ],
            "barrel_motor_full_swept": [MOTOR_L, MOTOR_D, MOTOR_D],
            "driver_reserved": [DRIVER_L, DRIVER_W, DRIVER_H],
        },
        "layout_centres_mm": {
            "xiao": XIAO_C,
            "battery": BAT_C,
            "motor": MOTOR_C,
            "driver": DRIVER_C,
            "microphone_drill": MIC_C,
            "antenna_keepout_x": [ANT_X0, ANT_X1],
        },
        "vertical_budget_mm": {
            "floor_insulation": FLOOR_INSULATION,
            "battery": BAT_H,
            "cell_to_board_barrier_and_expansion": CELL_TO_BOARD_BARRIER,
            "xiao": XIAO_H,
            "top_clearance": TOP_CLEARANCE,
            "required": stack,
            "original_shortage": height_shortage,
            "recovered_main_margin": MAIN_CLEAR_H - stack,
            "recovered_hook_margin_before_top_allowance": HOOK_ZONE_CLEAR_H
            - (FLOOR_INSULATION + BAT_H + CELL_TO_BOARD_BARRIER + XIAO_H),
        },
        "plan_clearances_mm": {
            "battery_to_motor": rect_gap((*BAT_C, BAT_L, BAT_W), (*MOTOR_C, MOTOR_D, MOTOR_L)),
            "battery_to_driver": rect_gap((*BAT_C, BAT_L, BAT_W), (*DRIVER_C, DRIVER_L, DRIVER_W)),
            "battery_foil_overlap_into_last_5mm_antenna_zone": antenna_overlap,
            "antenna_tip_not_over_battery": ANT_X1 - max(ANT_X0, battery_right),
        },
        "checks": checks,
        "alternate_battery_Vybronics_motor": alternate_local,
        "conditional_plan_b_DTP401525_Vybronics": conditional_plan_b,
        "PRIMARY_RENATA_ONLY_M2_screw_retention": (
            primary_renata_screw_retention
        ),
        "exact_historical_shell_boolean_audit": exact_shell,
        "hard_gates": [
            "Measure the ACTUAL MJF cavity and every finished component; nominal CAD is not a ship authorization.",
            "Use either the <=25.0 x 10.0 x 5.5 mm primary battery envelope or the named DTP401525 Plan B <=25.3 x 15.0 x 4.0 mm envelope; never mix their layouts or gauges.",
            "Use only a protected 1S cell whose datasheet explicitly permits the configured 50 mA charge current.",
            "Meter polarity before soldering; never rely on wire colour or JST convention.",
            "Use either the ordered PA12 shell or the supplied full-shell PETG prints only after physical fit, closed-case BLE, audio, thermal and drop tests pass.",
            "A 24-25 mm battery lies under the conservative antenna zone; a real closed-case RF test is mandatory.",
            "The Plan B battery has only 0.15 mm nominal clearance below the historical shelf; any physical friction, thickness over 4.00 mm, pouch/wrap/tab mark or shell load is a rejection.",
            "SparkFun PRT-13853/DTP401525 and Lee PID8834 are not interchangeable identities. Neither is a shipping battery without an exact received label, matching datasheet and matching UN38.3 record.",
            "Lee PID160959/PID8834, PID10431/PID104281 and Lee driver parts are delivery fallbacks only until manufacturer, finished dimensions, electrical limits and polarity are counter-verified.",
            "Do not install either printed plan gauge; they are measurement fixtures only.",
            "The PRIMARY_RENATA_ONLY M2 screw-retained band is a separate architecture. Never combine it with Plan B, the barrel-motor layout, or either adhesive-only band.",
        ],
    }
    assert all(v for k, v in checks.items() if k != "original_8mm_height_fits")
    assert not checks["original_8mm_height_fits"]
    return report


def sha256_manifest():
    lines = []
    for path in sorted(OUT.iterdir()):
        if path.name == "SHA256SUMS.txt" or not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.name}")
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def remove_superseded_outputs():
    """Remove only generator-owned filenames made misleading by this revision."""
    names = [
        "ALT_LOCAL_MEASURE_coin_motor_10x2p7.step",
        "ALT_LOCAL_MEASURE_coin_motor_10x2p7.stl",
    ]
    for length in ALT_BAT_LS:
        tag = f"{length:g}".replace(".", "p")
        names.extend(
            [
                f"ALT_LOCAL_BENCH_ONLY_lower_fit_gauge_batt{tag}_coin10.step",
                f"ALT_LOCAL_BENCH_ONLY_lower_fit_gauge_batt{tag}_coin10.stl",
                f"ALT_LOCAL_layout_batt{tag}_coin10.step",
            ]
        )
    for name in names:
        (OUT / name).unlink(missing_ok=True)


def main():
    remove_superseded_outputs()
    spacer = make_spacer(0.20)
    spacer_loose = make_spacer(0.30)
    screw_spacer = make_primary_renata_screw_spacer(0.20)
    screw_spacer_loose = make_primary_renata_screw_spacer(0.30)
    screw_posts_installed = make_primary_renata_retainer_posts_installed()
    screw_posts_print_pair = make_primary_renata_retainer_posts_print_pair()
    screw_body_drill_jig = make_primary_renata_body_drill_jig()
    bridge = make_battery_safety_bridge()
    lower_gauge = make_lower_gauge()
    xiao_gauge = make_xiao_gauge()
    mic_jig = make_mic_drill_jig()
    asm, primary_parts = make_reference_assembly()
    battery = primary_parts["battery"]
    xiao = primary_parts["xiao"]
    motor = primary_parts["barrel_motor"]
    full_print_body = cq.importers.importStep(str(BODY_STEP))
    full_print_face = cq.importers.importStep(str(FACE_STEP))

    vybronics_motor = (
        cq.Workplane("XY").circle(ALT_COIN_D / 2).extrude(ALT_COIN_T)
    )
    primary_renata_motor_max = (
        cq.Workplane("XY")
        .circle(PRIMARY_RENATA_MOTOR_MAX_D / 2)
        .extrude(PRIMARY_RENATA_MOTOR_MAX_T)
    )
    lee_fallback_motor = (
        cq.Workplane("XY").circle(LEE_COIN_D / 2).extrude(LEE_COIN_T)
    )
    driver_envelope = cq.Workplane("XY").box(
        DRIVER_L, DRIVER_W, DRIVER_H, centered=(True, True, False)
    )
    plan_b_battery = cq.Workplane("XY").box(
        PLAN_B_BAT_L,
        PLAN_B_BAT_W,
        PLAN_B_BAT_H,
        centered=(True, True, False),
    )
    plan_b_gauge = make_plan_b_lower_gauge()
    plan_b_asm, plan_b_parts = make_plan_b_reference()
    primary_renata_parts = make_primary_renata_qualified_parts()
    alternate_parts = {}
    for length in ALT_BAT_LS:
        length_tag = f"{length:g}".replace(".", "p")
        alt_battery = cq.Workplane("XY").box(
            length, ALT_BAT_W, ALT_BAT_H, centered=(True, True, False)
        )
        alt_gauge = make_alt_local_lower_gauge(length)
        alt_asm, alt_parts = make_alt_local_reference(length)
        alternate_parts[length] = alt_parts
        for obj, stem in (
            (alt_battery, f"ALT_LOCAL_MEASURE_MAX_battery_{length_tag}x10x5p5"),
            (alt_gauge, f"ALT_BENCH_ONLY_lower_fit_gauge_batt{length_tag}_Vybronics10p2"),
        ):
            export(obj, f"{stem}.step")
            export(obj, f"{stem}.stl")
        alt_asm.export(
            str(OUT / f"ALT_layout_batt{length_tag}_Vybronics10p2.step")
        )

    export(
        vybronics_motor,
        "MEASURE_MAX_Vybronics_VCLP1020B002L_10p2x2p3.step",
    )
    export(
        vybronics_motor,
        "MEASURE_MAX_Vybronics_VCLP1020B002L_10p2x2p3.stl",
    )
    export(
        lee_fallback_motor,
        "FALLBACK_ONLY_MEASURE_Lee_PID10431_10x2p7.step",
    )
    export(
        lee_fallback_motor,
        "FALLBACK_ONLY_MEASURE_Lee_PID10431_10x2p7.stl",
    )
    export(
        primary_renata_motor_max,
        "PRIMARY_RENATA_ONLY_MEASURE_MAX_coin_motor_10p2x2p7.step",
    )
    export(
        primary_renata_motor_max,
        "PRIMARY_RENATA_ONLY_MEASURE_MAX_coin_motor_10p2x2p7.stl",
    )
    export(
        plan_b_battery,
        "PLAN_B_MEASURE_MAX_DTP401525_total_25p3x15x4.step",
    )
    export(
        plan_b_battery,
        "PLAN_B_MEASURE_MAX_DTP401525_total_25p3x15x4.stl",
    )
    export(
        plan_b_gauge,
        "PLAN_B_BENCH_ONLY_lower_fit_gauge_DTP401525_Vybronics_driver_rotated.step",
    )
    export(
        plan_b_gauge,
        "PLAN_B_BENCH_ONLY_lower_fit_gauge_DTP401525_Vybronics_driver_rotated.stl",
    )
    plan_b_asm.export(
        str(
            OUT
            / "PLAN_B_layout_DTP401525_Vybronics_driver_rotated.step"
        )
    )
    export(driver_envelope, "MEASURE_MAX_finished_driver_island_8x4x2.step")
    export(driver_envelope, "MEASURE_MAX_finished_driver_island_8x4x2.stl")
    export(
        full_print_body,
        "PRINT_FULL_SHELL_body_exact_historical_geometry.stl",
    )
    export(
        full_print_face,
        "PRINT_FULL_SHELL_hooked_face_exact_historical_geometry.stl",
    )

    for obj, stem in (
        (spacer, "ordered_shell_midband_rise_4p50mm_nominal"),
        (spacer_loose, "ordered_shell_midband_rise_4p50mm_loose_tongue"),
        (
            screw_spacer,
            "PRIMARY_RENATA_ONLY_M2_screw_retained_midband_rise_4p50mm_nominal",
        ),
        (
            screw_spacer_loose,
            "PRIMARY_RENATA_ONLY_M2_screw_retained_midband_rise_4p50mm_loose_tongue",
        ),
        (
            screw_posts_print_pair,
            "PRINT_TWO_PRIMARY_RENATA_ONLY_M2_keyed_retainer_posts_HEAD_DOWN",
        ),
        (
            screw_body_drill_jig,
            "PRIMARY_RENATA_ONLY_M2_body_drill_marking_jig_USB_NOTCH",
        ),
        (bridge, "PRINT_DECK_DOWN_then_FLIP_battery_safety_bridge"),
        (lower_gauge, "BENCH_ONLY_lower_component_fit_gauge"),
        (xiao_gauge, "BENCH_ONLY_xiao_plan_fit_gauge"),
        (mic_jig, "mic_drill_jig_usb_end_notched"),
        (battery, "MEASURE_MAX_finished_battery_25x10x5p5"),
        (xiao, "MEASURE_XIAO_official_bbox_22p482x17p78x4p46"),
        (motor, "MEASURE_motor_4x8"),
    ):
        export(obj, f"{stem}.step")
        export(obj, f"{stem}.stl")

    exact_shell = exact_shell_audit(
        spacer,
        spacer_loose,
        screw_spacer,
        screw_spacer_loose,
        screw_posts_installed,
        primary_parts,
        alternate_parts,
        primary_renata_parts,
        plan_b_parts,
    )
    asm.export(str(OUT / "ordered_shell_layout_reference.step"))
    (OUT / "FIT_REPORT.json").write_text(
        json.dumps(fit_report(exact_shell), indent=2) + "\n"
    )
    sha256_manifest()


if __name__ == "__main__":
    main()
