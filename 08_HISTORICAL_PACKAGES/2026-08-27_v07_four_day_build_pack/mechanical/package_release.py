#!/usr/bin/env python3
"""Create a deterministic, explicitly allow-listed v0.7 prototype release ZIP."""

from pathlib import Path
import hashlib
import json
import shutil
import zipfile


ROOT = Path(__file__).resolve().parent
ZIP_NAME = "Anticipy_v07_noPCB_four_day_prototype.zip"

FILES = [
    "P2S_v07_fit_gauges.3mf",
    "P2S_v07_nopcb_retained.3mf",
    "V07_FIT_REPORT.md",
    "V07_PRINT_AND_ASSEMBLY_GUIDE.md",
    "generate_v07_nopcb.py",
    "v07_fit_report.json",
    "v07_internal_layout.png",
    "v07_fit_check.glb",
    "v07_full_assembly.step",
    "v07_base_shell.step", "v07_base_shell.stl",
    "v07_lid.step", "v07_lid.stl",
    "v07_carrier.step", "v07_carrier.stl",
    "v07_button_plunger_4p0.step", "v07_button_plunger_4p0.stl",
    "v07_button_plunger_4p3.step", "v07_button_plunger_4p3.stl",
    "v07_button_plunger_4p6.step", "v07_button_plunger_4p6.stl",
    "v07_dummy_audio_bff_21x17p7x5.step", "v07_dummy_audio_bff_21x17p7x5.stl",
    "v07_dummy_battery_35x25x6.step", "v07_dummy_battery_35x25x6.stl",
    "v07_dummy_button_6p2x6p2x3p5.step", "v07_dummy_button_6p2x6p2x3p5.stl",
    "v07_dummy_haptic_cap_cluster_11x7x6.step", "v07_dummy_haptic_cap_cluster_11x7x6.stl",
    "v07_dummy_motor_10x2p1.step", "v07_dummy_motor_10x2p1.stl",
    "v07_dummy_switch_8p6x4p3x4p7.step", "v07_dummy_switch_8p6x4p3x4p7.stl",
    "v07_dummy_xiao_rotated_17p8x21x3p2.step", "v07_dummy_xiao_rotated_17p8x21x3p2.stl",
]

for stale in ("v07_dummy_haptic_11x7x3p5.step", "v07_dummy_haptic_11x7x3p5.stl"):
    old = ROOT / stale
    if old.exists():
        archive = ROOT / "superseded_unshipped"
        archive.mkdir(exist_ok=True)
        shutil.move(str(old), str(archive / old.name))

missing = [name for name in FILES if not (ROOT / name).is_file()]
if missing:
    raise SystemExit(f"Missing release files: {missing}")

hashes = {}
for name in FILES:
    hashes[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()

(ROOT / "SHA256SUMS.txt").write_text(
    "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes))
)

manifest = {
    "classification": "four-day no-custom-PCB founder prototype; not customer production",
    "envelope_mm": [76.0, 33.0, 19.0],
    "mass_estimate_g": {"nominal": 36.91, "plus_15_percent": 42.44},
    "first_print": "P2S_v07_fit_gauges.3mf",
    "enclosure_print": "P2S_v07_nopcb_retained.3mf",
    "files": sorted(FILES + ["SHA256SUMS.txt"]),
}
(ROOT / "RELEASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")

zip_entries = FILES + ["SHA256SUMS.txt", "RELEASE_MANIFEST.json"]
with zipfile.ZipFile(ROOT / ZIP_NAME, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for name in sorted(zip_entries):
        data = (ROOT / name).read_bytes()
        info = zipfile.ZipInfo(f"Anticipy_v07_noPCB/{name}", date_time=(2026, 8, 28, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        zf.writestr(info, data)

with zipfile.ZipFile(ROOT / ZIP_NAME) as zf:
    bad = zf.testzip()
    if bad:
        raise SystemExit(f"ZIP CRC failure: {bad}")

print(f"Created {ZIP_NAME} with {len(zip_entries)} files")
print(hashlib.sha256((ROOT / ZIP_NAME).read_bytes()).hexdigest())

