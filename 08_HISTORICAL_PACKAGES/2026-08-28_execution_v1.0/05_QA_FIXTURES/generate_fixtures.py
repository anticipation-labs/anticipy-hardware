#!/usr/bin/env python3
"""Generate printable QA fixtures for the Anticipy 51 x 21 x 11 mm pendant.

This package contains two deliberately low-energy fixtures:

1. A padded cassette that reverses slowly about the pendant centre to reveal
   loose internal parts.  The cassette can be mounted face-on or on a 90-degree
   adapter, giving three indexed test axes.
2. A height-adjustable drop release head.  Three spring-open radial fingers are
   blocked by one common lift plate.  Lifting that single plate releases all
   fingers; the pendant then falls freely through the centre opening.

The vertical mast, shaft, bearings, motors, guards, fasteners, springs and pads
are purchased parts listed in BOM.csv.  Printed parts are fixtures, not safety
certifications.  Validate the drop release with the inert dummy and 240 fps
video before putting a battery-powered unit in it.

All dimensions are millimetres.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import csv
import json
import math
import shutil

import cadquery as cq
from cadquery import exporters


ROOT = Path(__file__).resolve().parent
STL_DIR = ROOT / "stl"
STEP_DIR = ROOT / "step"
REPORT_DIR = ROOT / "reports"

PENDANT_L = 51.0
PENDANT_W = 21.0
PENDANT_D = 11.0
PENDANT_EDGE_FILLET = 1.20


@dataclass(frozen=True)
class Orientation:
    name: str
    kind: str
    vector: tuple[float, float, float]


def ensure_dirs() -> None:
    for folder in (STL_DIR, STEP_DIR, REPORT_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    part = cq.Workplane("XY").box(length, width, height, centered=(True, True, False))
    if radius > 0:
        part = part.edges("|Z").fillet(radius)
    return part


def capsule(length: float, width: float, height: float, z0: float = 0.0) -> cq.Workplane:
    """Capsule in XY, extruded in +Z."""
    straight = length - width
    centre = cq.Workplane("XY").rect(straight, width).extrude(height)
    left = cq.Workplane("XY").center(-straight / 2, 0).circle(width / 2).extrude(height)
    right = cq.Workplane("XY").center(straight / 2, 0).circle(width / 2).extrude(height)
    return centre.union(left).union(right).translate((0, 0, z0))


def pendant_shape(clearance: float = 0.0) -> cq.Workplane:
    raw = capsule(
        PENDANT_L + 2 * clearance,
        PENDANT_W + 2 * clearance,
        PENDANT_D + 2 * clearance,
        -(PENDANT_D + 2 * clearance) / 2,
    )
    # Filleting all exterior edges matches the soft pebble gauge closely enough
    # for fixture setup keys.  Fall back to the capsule if a future parameter
    # combination makes the fillet invalid.
    try:
        return raw.edges().fillet(PENDANT_EDGE_FILLET + clearance)
    except Exception:
        return raw


def cyl_x(radius: float, length: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    shape = (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((0, 0, -length / 2))
        .rotate((0, 0, 0), (0, 1, 0), 90)
    )
    return shape.translate(center)


def cyl_y(radius: float, length: float, center=(0.0, 0.0, 0.0)) -> cq.Workplane:
    shape = (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(length)
        .translate((0, 0, -length / 2))
        .rotate((0, 0, 0), (1, 0, 0), 90)
    )
    return shape.translate(center)


def hole_z(part: cq.Workplane, x: float, y: float, radius: float, height: float, z0=-1.0):
    cutter = cq.Workplane("XY").center(x, y).circle(radius).extrude(height).translate((0, 0, z0))
    return part.cut(cutter)


def export_part(name: str, part: cq.Workplane, manifest: dict) -> None:
    stl_path = STL_DIR / f"{name}.stl"
    step_path = STEP_DIR / f"{name}.step"
    exporters.export(part, str(stl_path), tolerance=0.05, angularTolerance=0.10)
    exporters.export(part, str(step_path))
    bb = part.val().BoundingBox()
    manifest[name] = {
        "stl": str(stl_path.relative_to(ROOT)),
        "step": str(step_path.relative_to(ROOT)),
        "bounds_mm": [round(bb.xlen, 3), round(bb.ylen, 3), round(bb.zlen, 3)],
        "volume_mm3": round(part.val().Volume(), 3),
    }


def rattle_parts(manifest: dict) -> dict[str, cq.Workplane]:
    parts: dict[str, cq.Workplane] = {}

    # Cassette dimensions provide a hard stop around a replaceable 95A-TPU
    # liner.  The hard plastic never clamps the cosmetic pendant faces.
    outer_l, outer_w = 70.0, 38.0
    cavity_l, cavity_w = 54.6, 24.9
    bolt_xy = [(29.0, 14.0), (29.0, -14.0), (-29.0, 14.0), (-29.0, -14.0)]

    pod_base = rounded_box(outer_l, outer_w, 9.2, 4.0)
    pod_base = pod_base.cut(capsule(cavity_l, cavity_w, 7.4, 2.0))
    for x, y in bolt_xy:
        pod_base = hole_z(pod_base, x, y, 1.75, 12.0)
    parts["rattle_cassette_base_petg"] = pod_base

    pod_lid = rounded_box(outer_l, outer_w, 7.0, 4.0)
    pod_lid = pod_lid.cut(capsule(cavity_l, cavity_w, 5.1, -0.1))
    # The window lets a removable piezo patch touch the DUT, avoiding fixture
    # sound having to travel through a thick printed lid.
    pod_lid = pod_lid.cut(capsule(36.0, 13.0, 9.0, -1.0))
    for x, y in bolt_xy:
        pod_lid = hole_z(pod_lid, x, y, 1.75, 10.0)
    parts["rattle_cassette_lid_petg"] = pod_lid

    liner_outer = capsule(54.2, 24.5, 6.8)
    liner_inner = capsule(51.5, 21.5, 6.1, 1.0)
    parts["rattle_cassette_liner_base_tpu95a"] = liner_outer.cut(liner_inner)
    liner_top = capsule(54.2, 24.5, 1.0).cut(capsule(39.0, 14.0, 2.0, -0.5))
    parts["rattle_cassette_liner_lid_tpu95a"] = liner_top

    rotor = cq.Workplane("XY").circle(50.0).extrude(6.0)
    rotor = hole_z(rotor, 0, 0, 4.15, 8.0)
    # Purchased clamping hub: four M4 holes on a 32 mm bolt circle.
    for angle in (45, 135, 225, 315):
        x = 16.0 * math.cos(math.radians(angle))
        y = 16.0 * math.sin(math.radians(angle))
        rotor = hole_z(rotor, x, y, 2.15, 8.0)
    # The cassette uses four long M3 screws through lid/base/rotor.
    for x, y in bolt_xy:
        rotor = hole_z(rotor, x, y, 1.75, 8.0)
        nut = (
            cq.Workplane("XY")
            .center(x, y)
            .polygon(6, 6.6)
            .extrude(2.8)
            .translate((0, 0, -0.1))
        )
        rotor = rotor.cut(nut)
    parts["rattle_rotor_disk_petg"] = rotor

    # 90-degree adapter.  Direct cassette-to-rotor mounting tests the thickness
    # axis.  This adapter has two indexed bolt patterns so either the long or
    # short pendant axis can be made parallel to the shaft.
    adapter_base = rounded_box(90.0, 50.0, 6.0, 3.0)
    for x, y in bolt_xy:
        adapter_base = hole_z(adapter_base, x, y, 1.75, 8.0)
    upright = cq.Workplane("XY").box(78.0, 6.0, 78.0).translate((0, 0, 39.0))
    edge_adapter = adapter_base.union(upright)
    for x, z in [(29, 14), (29, -14), (-29, 14), (-29, -14)]:
        edge_adapter = edge_adapter.cut(cyl_y(1.75, 10.0, (x, 0, z + 39.0)))
    for x, z in [(14, 29), (14, -29), (-14, 29), (-14, -29)]:
        edge_adapter = edge_adapter.cut(cyl_y(1.75, 10.0, (x, 0, z + 39.0)))
    # Large root gussets keep layer lines out of the loaded corner.
    for x in (-31.0, 31.0):
        gusset = (
            cq.Workplane("XZ")
            .polyline([(x - 5, 0), (x + 5, 0), (x, 18)])
            .close()
            .extrude(6.0, both=True)
        )
        edge_adapter = edge_adapter.union(gusset)
    parts["rattle_edge_axis_adapter_petg"] = edge_adapter

    # Base plate fits a 256 x 256 mm printer.  The printed base can be replaced
    # by 12 mm plywood using the STEP as a drill template.
    base = rounded_box(230.0, 90.0, 6.0, 6.0)
    # Two bearing towers at x +/-45 and a motor mount at x=-95.
    for x in (-45.0, 45.0):
        for y in (-21.0, 21.0):
            base = hole_z(base, x, y, 2.2, 8.0)
    for x in (-101.0, -89.0):
        for y in (-24.0, 24.0):
            base = hole_z(base, x, y, 2.2, 8.0)
    parts["rattle_base_plate_petg_or_plywood_template"] = base

    tower = cq.Workplane("XY").box(12.0, 55.0, 78.0).translate((0, 0, 39.0))
    tower = tower.union(cq.Workplane("XY").box(34.0, 55.0, 6.0).translate((0, 0, 3.0)))
    tower = tower.cut(cyl_x(4.25, 16.0, (0, 0, 63.0)))
    # 608 bearing pocket from one face: flip the right-hand tower on assembly.
    tower = tower.cut(cyl_x(11.10, 7.3, (2.35, 0, 63.0)))
    for x in (-10.5, 10.5):
        for y in (-21.0, 21.0):
            tower = hole_z(tower, x, y, 2.2, 10.0)
    parts["rattle_608_bearing_tower_petg_print_two"] = tower

    motor_mount = cq.Workplane("XY").box(8.0, 60.0, 66.0).translate((0, 0, 33.0))
    motor_mount = motor_mount.union(
        cq.Workplane("XY").box(34.0, 66.0, 6.0).translate((9.0, 0, 3.0))
    )
    motor_mount = motor_mount.cut(cyl_x(12.0, 12.0, (0, 0, 45.0)))
    for y in (-15.5, 15.5):
        for z in (29.5, 60.5):
            motor_mount = motor_mount.cut(cyl_x(1.75, 12.0, (0, y, z)))
    for x in (-2.0, 20.0):
        for y in (-24.0, 24.0):
            motor_mount = hole_z(motor_mount, x, y, 2.2, 10.0)
    parts["rattle_nema17_mount_petg"] = motor_mount

    # Inert mass/fit dummy: print solid or add washers to match the tested DUT
    # mass.  Never use a damaged battery as the challenge sample.
    parts["inert_51x21x11_pendant_dummy"] = pendant_shape(0.0).translate((0, 0, PENDANT_D / 2))

    for name, part in parts.items():
        export_part(name, part, manifest)
    return parts


def unit(v: tuple[float, float, float]) -> tuple[float, float, float]:
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def cross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def orient_down(shape: cq.Workplane, vector: tuple[float, float, float]) -> cq.Workplane:
    source = unit(vector)
    target = (0.0, 0.0, -1.0)
    d = max(-1.0, min(1.0, dot(source, target)))
    axis = cross(source, target)
    axis_n = math.sqrt(dot(axis, axis))
    if axis_n < 1e-9:
        if d > 0:
            return shape
        return shape.rotate((0, 0, 0), (1, 0, 0), 180.0)
    axis = tuple(c / axis_n for c in axis)
    angle = math.degrees(math.acos(d))
    return shape.rotate((0, 0, 0), axis, angle)


def all_orientations() -> list[Orientation]:
    hx, hy, hz = PENDANT_L / 2, PENDANT_W / 2, PENDANT_D / 2
    out: list[Orientation] = []
    sign = {1: "P", -1: "M"}
    axis_names = ("X", "Y", "Z")
    halves = (hx, hy, hz)

    for axis in range(3):
        for s in (1, -1):
            v = [0.0, 0.0, 0.0]
            v[axis] = s * halves[axis]
            out.append(Orientation(f"F_{axis_names[axis]}{sign[s]}", "face", tuple(v)))

    for a, b in ((0, 1), (0, 2), (1, 2)):
        for sa in (1, -1):
            for sb in (1, -1):
                v = [0.0, 0.0, 0.0]
                v[a] = sa * halves[a]
                v[b] = sb * halves[b]
                name = f"E_{axis_names[a]}{sign[sa]}_{axis_names[b]}{sign[sb]}"
                out.append(Orientation(name, "edge", tuple(v)))

    for sx in (1, -1):
        for sy in (1, -1):
            for sz in (1, -1):
                name = f"C_X{sign[sx]}_Y{sign[sy]}_Z{sign[sz]}"
                out.append(Orientation(name, "corner", (sx * hx, sy * hy, sz * hz)))
    assert len(out) == 26
    return out


def drop_parts(manifest: dict) -> tuple[dict[str, cq.Workplane], list[dict]]:
    parts: dict[str, cq.Workplane] = {}

    # Horizontal annular body.  The pendant falls through the 80 mm centre.
    body = cq.Workplane("XY").circle(75.0).circle(40.0).extrude(8.0)
    finger_angles = (90.0, 210.0, 330.0)

    # Radial pads extend the body beneath each guide without making the entire
    # ring 220 mm in diameter.
    for angle in finger_angles:
        pad = rounded_box(80.0, 34.0, 8.0, 4.0).translate((70.0, 0, 0))
        pad = pad.rotate((0, 0, 0), (0, 0, 1), angle)
        body = body.union(pad)

    def radial_xy(radius: float, tangent: float, angle_deg: float):
        c = math.cos(math.radians(angle_deg))
        s = math.sin(math.radians(angle_deg))
        return radius * c - tangent * s, radius * s + tangent * c

    # Four M3 guide-cap holes and one spring-anchor hole per finger.
    for angle in finger_angles:
        for radius in (35.0, 105.0):
            for tangent in (-12.0, 12.0):
                x, y = radial_xy(radius, tangent, angle)
                body = hole_z(body, x, y, 1.7, 10.0)
        x, y = radial_xy(107.0, 0.0, angle)
        body = hole_z(body, x, y, 1.7, 10.0)

    # Three M4 guide rods keep the common latch plate parallel as one centered
    # solenoid/equal-length three-cord yoke lifts it.
    guide_angles = (30.0, 150.0, 270.0)
    for angle in guide_angles:
        x = 67.0 * math.cos(math.radians(angle))
        y = 67.0 * math.sin(math.radians(angle))
        body = hole_z(body, x, y, 2.15, 10.0)

    # Mounting holes for a purchased aluminum crossbar/L-brackets.
    for x, y in ((-60, 52), (60, 52), (-60, -52), (60, -52)):
        body = hole_z(body, x, y, 2.7, 10.0)
    parts["drop_collet_body_petg"] = body

    guide = rounded_box(85.0, 30.0, 9.0, 3.0)
    channel = cq.Workplane("XY").box(79.0, 11.6, 6.2, centered=(True, True, False)).translate((0, 0, -0.1))
    guide = guide.cut(channel)
    for x in (-35.0, 35.0):
        for y in (-12.0, 12.0):
            guide = hole_z(guide, x, y, 1.7, 12.0)
    parts["drop_finger_guide_petg_print_three"] = guide

    finger = rounded_box(40.0, 10.0, 5.0, 2.0)
    # M4 heat-set insert bore in the inner end.  A purchased M4 nylon screw plus
    # PTFE face provides 0--20 mm adjustment for different projected radii.
    finger = finger.cut(cyl_x(2.6, 8.0, (-16.0, 0, 2.5)))
    finger = hole_z(finger, 15.0, 0.0, 1.2, 7.0)
    parts["drop_radial_finger_petg_print_three"] = finger

    latch = cq.Workplane("XY").circle(95.0).circle(45.0).extrude(4.0).translate((0, 0, 6.0))
    for angle in finger_angles:
        stop = rounded_box(7.0, 18.0, 6.0, 1.5).translate((68.5, 0, 0))
        stop = stop.rotate((0, 0, 0), (0, 0, 1), angle)
        latch = latch.union(stop)
    for angle in guide_angles:
        x = 67.0 * math.cos(math.radians(angle))
        y = 67.0 * math.sin(math.radians(angle))
        latch = hole_z(latch, x, y, 2.3, 12.0)
    # Three equal-length lifting cords attach here and meet at one solenoid eye.
    for angle in (0.0, 120.0, 240.0):
        x = 82.0 * math.cos(math.radians(angle))
        y = 82.0 * math.sin(math.radians(angle))
        latch = hole_z(latch, x, y, 2.0, 12.0)
    parts["drop_common_latch_plate_petg"] = latch

    # Equal-length cords from the latch plate terminate at this rigid yoke.
    # The yoke's centre hole connects to the solenoid clevis.  Its only job is
    # to keep lift geometry symmetric; the three guide rods carry side load.
    # A single triangular plate meshes more reliably than three coincident
    # booleaned arms, while preserving exactly symmetric cord geometry.
    yoke_vertices = [
        (58.0 * math.cos(math.radians(angle)), 58.0 * math.sin(math.radians(angle)))
        for angle in (0.0, 120.0, 240.0)
    ]
    yoke = cq.Workplane("XY").polyline(yoke_vertices).close().extrude(6.0)
    yoke = yoke.edges("|Z").fillet(4.0)
    for angle in (0.0, 120.0, 240.0):
        x = 48.0 * math.cos(math.radians(angle))
        y = 48.0 * math.sin(math.radians(angle))
        yoke = hole_z(yoke, x, y, 2.0, 8.0)
    yoke = hole_z(yoke, 0, 0, 2.2, 8.0)
    parts["drop_three_cord_lift_yoke_petg"] = yoke

    # A print-and-weight dummy is mandatory for release tuning.  Add embedded
    # steel washers until it matches the actual pendant mass, then close holes
    # with tape.  It contains no battery.
    parts["drop_inert_51x21x11_dummy"] = pendant_shape(0.0).translate((0, 0, PENDANT_D / 2))

    for name, part in parts.items():
        export_part(name, part, manifest)

    orientations_csv: list[dict] = []
    clear_device = pendant_shape(0.30)
    exact_device = pendant_shape(0.0)
    for index, orientation in enumerate(all_orientations(), start=1):
        oriented_clear = orient_down(clear_device, orientation.vector)
        oriented_exact = orient_down(exact_device, orientation.vector)
        bbox = oriented_exact.val().BoundingBox()

        # Every pose key puts the DUT centre 40 mm above the key bottom.  Thus
        # all three release fingers remain at the same height.  The shallow
        # 1.5 mm pocket is only a setup reference; lower the key before release.
        center_z = 40.0
        pocket_depth = 1.5
        key_height = center_z + bbox.zmin + pocket_depth
        key_height = max(6.0, key_height)
        key = rounded_box(90.0, 70.0, key_height, 5.0)
        handle_h = min(10.0, key_height)
        handle = rounded_box(24.0, 24.0, handle_h, 4.0).translate((0, 43.0, 0))
        key = key.union(handle)
        key = key.cut(oriented_clear.translate((0, 0, center_z)))
        key_name = f"drop_pose_key_{index:02d}_{orientation.name}"
        export_part(key_name, key, manifest)
        orientations_csv.append(
            {
                "sequence": index,
                "orientation_id": orientation.name,
                "kind": orientation.kind,
                "target_vector_body_xyz_mm": "{:.3f};{:.3f};{:.3f}".format(*orientation.vector),
                "pose_key_stl": f"stl/{key_name}.stl",
                "device_center_above_key_bottom_mm": f"{center_z:.1f}",
                "complete": "",
                "impact_angle_error_deg": "",
                "result": "",
                "notes": "",
            }
        )

    with (ROOT / "drop_orientation_map.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(orientations_csv[0]))
        writer.writeheader()
        writer.writerows(orientations_csv)

    return parts, orientations_csv


def save_assemblies(rattle: dict[str, cq.Workplane], drop: dict[str, cq.Workplane]) -> None:
    # Rattle assembly, face-axis cassette configuration.  Purchased hardware is
    # represented by simple solids; do not print those solids as substitutes.
    assy = cq.Assembly(name="rattle_fixture_face_axis")
    assy.add(rattle["rattle_base_plate_petg_or_plywood_template"], name="base")
    for x, flip in ((-45.0, 0.0), (45.0, 180.0)):
        loc = cq.Location(cq.Vector(x, 0, 6.0), cq.Vector(0, 0, 1), flip)
        assy.add(rattle["rattle_608_bearing_tower_petg_print_two"], loc=loc, name=f"tower_{x:+.0f}")
    shaft = cyl_x(4.0, 125.0, (0, 0, 69.0))
    assy.add(shaft, name="purchased_8mm_shaft")
    rotor_loc = cq.Location(cq.Vector(0, 0, 69.0), cq.Vector(0, 1, 0), 90.0)
    assy.add(rattle["rattle_rotor_disk_petg"], loc=rotor_loc, name="rotor")
    # Cassette is shown against the rotor.  Actual assembly uses four M3 screws.
    cassette_loc = cq.Location(cq.Vector(6.0, 0, 69.0), cq.Vector(0, 1, 0), 90.0)
    assy.add(rattle["rattle_cassette_base_petg"], loc=cassette_loc, name="cassette_base")
    assy.save(str(STEP_DIR / "rattle_fixture_face_axis_assembly.step"))

    # Drop collet closed and released views.  Guides/fingers are transformed
    # from their printable local X direction into three radial directions.
    for state, finger_radius, latch_lift in (("closed", 45.0, 0.0), ("released", 80.0, 10.0)):
        a = cq.Assembly(name=f"drop_release_{state}")
        a.add(drop["drop_collet_body_petg"], name="body")
        for n, angle in enumerate((90.0, 210.0, 330.0), start=1):
            rad = math.radians(angle)
            guide_loc = cq.Location(
                cq.Vector(70 * math.cos(rad), 70 * math.sin(rad), 8.0),
                cq.Vector(0, 0, 1),
                angle,
            )
            finger_loc = cq.Location(
                cq.Vector(finger_radius * math.cos(rad), finger_radius * math.sin(rad), 8.5),
                cq.Vector(0, 0, 1),
                angle,
            )
            a.add(drop["drop_finger_guide_petg_print_three"], loc=guide_loc, name=f"guide_{n}")
            a.add(drop["drop_radial_finger_petg_print_three"], loc=finger_loc, name=f"finger_{n}")
        a.add(
            drop["drop_common_latch_plate_petg"],
            loc=cq.Location(cq.Vector(0, 0, 8.0 + latch_lift)),
            name="common_latch",
        )
        a.save(str(STEP_DIR / f"drop_release_{state}_assembly.step"))


def main() -> None:
    ensure_dirs()
    # Generated outputs are reproducible.  Remove only directories owned by
    # this generator, never arbitrary workspace paths.
    for folder in (STL_DIR, STEP_DIR):
        for item in folder.iterdir():
            if item.is_file():
                item.unlink()

    manifest: dict = {}
    rattle = rattle_parts(manifest)
    drop, orientations = drop_parts(manifest)
    save_assemblies(rattle, drop)

    payload = {
        "pendant_nominal_mm": [PENDANT_L, PENDANT_W, PENDANT_D],
        "printed_part_count": len(manifest),
        "drop_pose_key_count": len(orientations),
        "parts": manifest,
        "notes": [
            "All values are millimetres.",
            "PETG functional parts; TPU 95A only for named cassette liners.",
            "Drop fixture guides the release head, never the falling pendant.",
            "Do not use these files for battery short, crush, puncture, overcharge, or fire tests.",
        ],
    }
    (REPORT_DIR / "fixture_manifest.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Generated {len(manifest)} printable parts and {len(orientations)} pose keys")


if __name__ == "__main__":
    main()
