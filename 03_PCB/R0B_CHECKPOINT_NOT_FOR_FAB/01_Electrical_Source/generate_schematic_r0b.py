#!/usr/bin/env python3
"""Generate an editable, deterministic KiCad 7 R0B schematic.

All electrical assignments and intentional no-connects come from
``design_spec_r0b.py``.  Connectivity uses local labels at pin endpoints; the
companion verifier compares KiCad's exported netlist with the source spec.
"""

from __future__ import annotations

from pathlib import Path
import re

from design_spec_r0b import PARTS, PROJECT, ROOT_UUID, SCHEMATIC_VERSION, uid


ROOT = Path(__file__).resolve().parent
OUT = ROOT / f"{PROJECT}.kicad_sch"


def q(value: object) -> str:
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"') + '"'


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", value).strip("_")


def electrical_type(name: str) -> str:
    allowed = {
        "input", "output", "bidirectional", "tri_state", "passive",
        "free", "unspecified", "power_in", "power_out", "open_collector",
        "open_emitter", "no_connect",
    }
    return name if name in allowed else "passive"


def pin_sides(part) -> tuple[list, list]:
    # Alternating pins makes large symbols compact and keeps deterministic
    # endpoints for the labels/no-connect markers.
    midpoint = (len(part.pins) + 1) // 2
    return list(part.pins[:midpoint]), list(part.pins[midpoint:])


def body_height(part) -> float:
    left, right = pin_sides(part)
    return max(10.16, (max(len(left), len(right), 2) + 1) * 2.54)


def local_pin_positions(part) -> dict[str, tuple[str, float, float, int]]:
    result: dict[str, tuple[str, float, float, int]] = {}
    for side, pins in (("left", pin_sides(part)[0]), ("right", pin_sides(part)[1])):
        for index, pin in enumerate(pins):
            local_y = (index - (len(pins) - 1) / 2) * 2.54
            if side == "left":
                result[pin.number] = (side, -15.24, local_y, 0)
            else:
                result[pin.number] = (side, 15.24, local_y, 180)
    return result


def library_symbol(part) -> str:
    name = f"R0B_{safe_id(part.ref)}"
    height = body_height(part)
    out = f'''    (symbol {q("Anticipy:" + name)}
      (pin_names (offset 0.8))
      (in_bom yes) (on_board yes)
      (property "Reference" {q(re.sub(r"[0-9]+$", "", part.ref) or "U")} (at 0 {-height/2-2.54:.3f} 0)
        (effects (font (size 1.27 1.27))))
      (property "Value" {q(part.value)} (at 0 {-height/2-5.08:.3f} 0)
        (effects (font (size 1.27 1.27))))
      (property "Footprint" {q(part.footprint)} (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
      (property "Datasheet" {q(part.datasheet)} (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
      (property "Manufacturer" {q(part.manufacturer)} (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
      (property "MPN" {q(part.mpn)} (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
      (property "Description" {q(part.description)} (at 0 0 0)
        (effects (font (size 1.27 1.27)) hide))
      (symbol {q(name + "_0_1")}
        (rectangle (start -12.70 {-height/2:.3f}) (end 12.70 {height/2:.3f})
          (stroke (width 0) (type default)) (fill (type background))))
      (symbol {q(name + "_1_1")}
'''
    positions = local_pin_positions(part)
    for pin in part.pins:
        _, px, py, angle = positions[pin.number]
        out += (
            f'        (pin {electrical_type(pin.electrical_type)} line '
            f'(at {px:.3f} {py:.3f} {angle}) (length 2.54)\n'
            f'          (name {q(pin.name)} (effects (font (size 0.9 0.9))))\n'
            f'          (number {q(pin.number)} (effects (font (size 0.9 0.9)))))\n'
        )
    out += "      )\n    )\n"
    return out


def layout() -> dict[str, tuple[float, float]]:
    positions: dict[str, tuple[float, float]] = {
        "U1": (55, 85), "U2": (105, 85), "U3": (155, 62),
        "U4": (155, 100), "U5": (205, 70), "MIC1": (205, 105),
        "MIC2": (255, 105), "J1": (255, 62), "BT1": (305, 60),
        "SW1": (305, 85), "LED1": (305, 110), "Q1": (355, 60),
        "D1": (355, 82), "M1": (355, 104), "NT1": (405, 60),
        "NT2": (405, 82), "L1": (405, 104), "L2": (405, 126),
    }
    small = [p for p in PARTS if p.ref not in positions]
    for index, item in enumerate(small):
        col, row = divmod(index, 10)
        positions[item.ref] = (55 + col * 50, 190 + row * 20)
    return positions


def symbol_instance(part, x: float, y: float) -> str:
    name = f"R0B_{safe_id(part.ref)}"
    instance_uuid = uid(f"symbol-instance-{part.ref}")
    height = body_height(part)
    dnp = "yes" if part.dnp else "no"
    out = f'''  (symbol (lib_id {q("Anticipy:" + name)}) (at {x:.3f} {y:.3f} 0) (unit 1)
    (in_bom yes) (on_board yes) (uuid {instance_uuid})
    (property "Reference" {q(part.ref)} (at {x:.3f} {y-height/2-2.54:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Value" {q(part.value)} (at {x:.3f} {y-height/2-5.08:.3f} 0)
      (effects (font (size 1.27 1.27))))
    (property "Footprint" {q(part.footprint)} (at {x:.3f} {y:.3f} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" {q(part.datasheet)} (at {x:.3f} {y:.3f} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Manufacturer" {q(part.manufacturer)} (at {x:.3f} {y:.3f} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "MPN" {q(part.mpn)} (at {x:.3f} {y:.3f} 0)
      (effects (font (size 1.27 1.27)) hide))
    (property "Description" {q(part.description)} (at {x:.3f} {y:.3f} 0)
      (effects (font (size 1.27 1.27)) hide))
'''
    for pin in part.pins:
        out += f'    (pin {q(pin.number)} (uuid {uid(f"pin-instance-{part.ref}-{pin.number}")}))\n'
    out += (
        f'    (instances (project {q(PROJECT)} '
        f'(path {q("/" + ROOT_UUID + "/" + instance_uuid)} '
        f'(reference {q(part.ref)}) (unit 1))))\n  )\n'
    )
    return out


def endpoint_items(part, x: float, y: float) -> str:
    out = ""
    for pin in part.pins:
        side, local_x, local_y, _ = local_pin_positions(part)[pin.number]
        sheet_x = x + local_x
        # KiCad mirrors library-symbol Y when placing it on the sheet.
        sheet_y = y - local_y
        if pin.net is None:
            out += (
                f'  (no_connect (at {sheet_x:.3f} {sheet_y:.3f}) '
                f'(uuid {uid(f"no-connect-{part.ref}-{pin.number}")}))\n'
            )
        else:
            angle = 180 if side == "left" else 0
            justify = " (justify right bottom)" if side == "left" else " (justify left bottom)"
            out += (
                f'  (label {q(pin.net)} (at {sheet_x:.3f} {sheet_y:.3f} {angle})\n'
                f'    (effects (font (size 0.8 0.8)){justify}) '
                f'(uuid {uid(f"label-{part.ref}-{pin.number}-{pin.net}")}))\n'
            )
    return out


def make_schematic() -> str:
    positions = layout()
    out = f'''(kicad_sch (version {SCHEMATIC_VERSION}) (generator eeschema)
  (uuid {ROOT_UUID})
  (paper "A0")
  (title_block
    (title "Anticipy ANT-PROD-R0B electrical design")
    (date "2026-08-29") (rev "R0B EVT") (company "Anticipy")
    (comment 1 "EDITABLE ENGINEERING CHECKPOINT - NOT RELEASED FOR FABRICATION")
    (comment 2 "Connectivity is verified from KiCad netlist; CLI ERC is unavailable in KiCad 7"))
  (lib_symbols
'''
    for item in PARTS:
        out += library_symbol(item)
    out += "  )\n"
    for item in PARTS:
        x, y = positions[item.ref]
        out += symbol_instance(item, x, y)
        out += endpoint_items(item, x, y)
    notes = (
        (455, 25, "R0B EVT / NOT FOR FABRICATION / HUMAN FIRST-ARTICLE REVIEW REQUIRED"),
        (455, 30, "POWER: USB-C -> nPM1300 -> 3V_MAIN / 3V_FLASH; 3V_MIC from LDO1."),
        (455, 35, "USB CC1/CC2 connect directly to nPM1300. Do not fit external 5.1k Rd resistors."),
        (455, 40, "BUTTON: SW1 switches SHPHLD to GND only; PMIC_INT reports state to MCU."),
        (455, 45, "BATTERY: LP451528-class protected 3-wire 10k NTC pack; final drawing/certs are a release gate."),
        (455, 50, "STORAGE: 4-Gbit raw SLC NAND requires ECC, bad-block, filesystem and power-loss firmware."),
        (455, 55, "RF: module footprint all-layer antenna keepout and final 9.5-mm exterior metal-free window."),
        (455, 60, "LED: anodes on VSYS, cathodes on nPM1300 sinks; firmware duty-cycle required."),
    )
    for index, (x, y, note) in enumerate(notes):
        out += (
            f'  (text {q(note)} (at {x} {y} 0)\n'
            f'    (effects (font (size 1.0 1.0))) (uuid {uid(f"note-{index}")}))\n'
        )
    out += '  (sheet_instances (path "/" (page "1")))\n)\n'
    return out


def main() -> None:
    OUT.write_text(make_schematic(), encoding="utf-8")
    print(f"Generated {OUT}")
    print(f"Parts: {len(PARTS)}; explicit no-connects: "
          f"{sum(pin.net is None for part in PARTS for pin in part.pins)}")


if __name__ == "__main__":
    main()
