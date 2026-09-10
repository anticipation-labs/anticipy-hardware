# Reproducing the released checks and CAM

Use KiCad 10.0.6 with its bundled pcbnew Python module. `audit_native.py` needs a fresh `verification/native_netlist.xml`. `analyze_routes.py` needs NumPy and Shapely. Paths for the current Mac KiCad executable are explicit in the scripts; adjust for another platform.

1. Run `verify_native.py` to perform full native DRC, schematic parity, ERC and XML netlist export.
2. Run `audit_native.py` with KiCad's Python, then `analyze_routes.py` with NumPy/Shapely. These inspect the saved copper. All 45 nets must pass; the approximate centerline length extractor's FLASH_CS limitation is separately documented and does not override filled-polygon connectivity.
3. Run `export_current.py`. On this Mac use a valid absolute FONTCONFIG_FILE when rendering PDF. This creates native PDF inputs, Gerbers, drills, positions and IPC-D-356.
4. Run `export_fitted_stencil.py` with KiCad's Python. It overwrites the primary paste Gerbers with exactly the 47 fitted parts; its temporary source never changes the released PCB.
5. Run `finalize_cam_metadata.py` to correct the Gerber-job bounding metadata from KiCad's stroke-inclusive box to the exact routed profile centerline. Copper, outline, masks and drills are untouched.

The combined release PDF contains the native PDF inputs; separate uncombined PDFs are build intermediates. The release STEP was exported with an explicit list of all 47 fitted references, not with `--no-unspecified`, because four fitted custom footprints use the default unspecified assembly-type attribute. The exact export command is in `verification/STEP_Export_Receipt.json`.

Do not refill, save or edit the frozen board merely to open/view it. Any intentional design change needs a new revision and a repeat of the checks and CAM generation. The final saved copper was filled in KiCad PCB Editor; its native and independent connectivity evidence is included. No design-rule categories are disabled; the scoped reference-cell courtyard and intentional connector-edge rules are documented in the electrical audit.
