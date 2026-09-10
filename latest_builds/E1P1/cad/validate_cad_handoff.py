"""Validate final handoff exports without modifying PCB or shell geometry."""
from pathlib import Path
import hashlib, json, platform
import importlib.metadata
from datetime import datetime, timezone
import cadquery as cq
import trimesh

HERE = Path(__file__).resolve().parent
EXPECTED_PCB = '78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36'
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

pcb = HERE.parent / 'pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb'
assert digest(pcb) == EXPECTED_PCB
contract = HERE / 'source_inputs/Final_PCB_Mechanical_Contract.json'
assert json.loads(contract.read_text())['boards']['E1P1']['source_sha256'] == EXPECTED_PCB
geometry = json.loads((HERE / 'Oval_E1_Checks.json').read_text())
assert geometry['PCB_sha256'] == EXPECTED_PCB
assert geometry['check_count'] == 2826 and not geometry['failures']
assert geometry['all_shapes_valid']
assert geometry['U4_native_position_mm'] == [28.15, 29.45]
assert geometry['maximum_component_envelopes_mm']['C23']['LWT'] == [2.2, 1.45, 1.45]

light_step = HERE / 'Clear_Lightpipe.step'
light_stl = HERE / 'Clear_Lightpipe.stl'
solid = cq.importers.importStep(str(light_step)).val()
solid.exportStl(str(light_stl), tolerance=.015, angularTolerance=.05, relative=False)
mesh = trimesh.load_mesh(light_stl, process=True)
before = len(mesh.faces)
mesh.update_faces(mesh.nondegenerate_faces())
mesh.remove_unreferenced_vertices()
removed = before - len(mesh.faces)
mesh.export(light_stl)
light_result = {
    'STEP_sha256': digest(light_step),
    'STL_sha256': digest(light_stl),
    'STEP_reimport_valid': solid.isValid(),
    'STEP_solids': len(solid.Solids()),
    'STL_watertight': bool(mesh.is_watertight),
    'STL_winding_consistent': bool(mesh.is_winding_consistent),
    'STL_components': len(mesh.split()),
    'removed_zero_area_triangles': removed,
    'surface_deflection_setting_mm': .015,
    'mesh_method': 'Remove degenerate pole triangles only; no hole filling or dimension changes.',
    'status': 'Separate optical part. Material, optical finishing and adhesive require approval and physical testing.',
}
assert light_result['STEP_reimport_valid'] and light_result['STEP_solids'] == 1
assert light_result['STL_watertight'] and light_result['STL_winding_consistent'] and light_result['STL_components'] == 1
(HERE / 'Lightpipe_Export_Checks.json').write_text(json.dumps(light_result, indent=2) + '\n')

assembly_results = []
for name in ['Oval_E1_Assembly_FIT_CANDIDATE.step', 'Oval_E1_Exploded_VIEW_ONLY.step']:
    shape = cq.importers.importStep(str(HERE / name)).val()
    result = {'file': name, 'sha256': digest(HERE / name), 'valid': shape.isValid(), 'solid_count': len(shape.Solids())}
    assert result['valid'] and result['solid_count'] > 1
    assembly_results.append(result)

receipt = {
    'generated_UTC': datetime.now(timezone.utc).isoformat(),
    'status': 'Matched final-PCB fit candidate. Not physically qualified or 30 x 14 x 8 mm.',
    'PCB_relative_to_cad': '../pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb',
    'PCB_sha256': EXPECTED_PCB,
    'bundled_mechanical_contract_sha256': digest(contract),
    'native_source_used_during_geometry_run': geometry['native_source'],
    'sibling_PCB_independently_matches_source_used': True,
    'check_count': geometry['check_count'],
    'failures': geometry['failures'],
    'nominal_external_LWT_mm': [56, 35, 14.8],
    'computed_external_LWT_mm': geometry['outer_LWT_mm'],
    'U4_native_XY_mm': geometry['U4_native_position_mm'],
    'selected_C23_max_LWT_mm': geometry['maximum_component_envelopes_mm']['C23']['LWT'],
    'assembly_STEP_reimport': assembly_results,
    'dependencies': {'python': platform.python_version(), **{n: importlib.metadata.version(n) for n in ['cadquery', 'numpy', 'matplotlib', 'shapely', 'trimesh']}},
    'sources_sha256': {n: digest(HERE / n) for n in ['build_oval_e1.py', 'harness_fragment.py', 'render_details.py', 'package_print_parts.py', 'validate_cad_handoff.py', 'source_inputs/render_helpers.py']},
    'physical_qualification_performed': False,
    'unchanged_native_PCB_verified': digest(pcb) == EXPECTED_PCB,
}
(HERE / 'CAD_Rebuild_Receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
files = []
for p in sorted(HERE.rglob('*')):
    if p.is_file() and p.name != 'CAD_File_Manifest.json' and '__pycache__' not in p.parts:
        files.append({'path': str(p.relative_to(HERE)), 'bytes': p.stat().st_size, 'sha256': digest(p)})
(HERE / 'CAD_File_Manifest.json').write_text(json.dumps({'PCB_sha256': EXPECTED_PCB, 'scope': 'CAD files only; this manifest excludes itself.', 'files': files}, indent=2) + '\n')
print(json.dumps({'geometry_checks': receipt['check_count'], 'failures': receipt['failures'], 'lightpipe': light_result, 'assembly_STEP_reimport': assembly_results, 'manifest_file_count': len(files)}, indent=2))
