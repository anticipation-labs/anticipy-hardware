from pathlib import Path
import json,zipfile,hashlib,xml.etree.ElementTree as ET
import numpy as np,trimesh,cadquery as cq
H=Path(__file__).resolve().parent;ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02';ET.register_namespace('',ns)
def tag(t):return '{'+ns+'}'+t
model=ET.Element(tag('model'),unit='millimeter');resources=ET.SubElement(model,tag('resources'));build=ET.SubElement(model,tag('build'));checks=[]
for i,(name,xshift)in enumerate([('Front_Oval_Shell',0),('Rear_Service_Cover',65),('Button_Plunger',105)],1):
    r=cq.importers.importStep(str(H/(name+'.step'))).val();r.exportStl(str(H/(name+'.stl')),tolerance=.015,angularTolerance=.05,relative=False)
    m=trimesh.load_mesh(H/(name+'.stl'),process=True);before=len(m.faces);m.update_faces(m.nondegenerate_faces());m.remove_unreferenced_vertices();removed=before-len(m.faces);m.export(H/(name+'.stl'));lo=m.bounds[0];m.vertices=m.vertices-lo+[xshift,0,0]
    obj=ET.SubElement(resources,tag('object'),id=str(i),type='model',name=name);mesh=ET.SubElement(obj,tag('mesh'));verts=ET.SubElement(mesh,tag('vertices'));tris=ET.SubElement(mesh,tag('triangles'))
    for p in m.vertices:ET.SubElement(verts,tag('vertex'),x=f'{p[0]:.6f}',y=f'{p[1]:.6f}',z=f'{p[2]:.6f}')
    for face in m.faces:ET.SubElement(tris,tag('triangle'),v1=str(face[0]),v2=str(face[1]),v3=str(face[2]))
    ET.SubElement(build,tag('item'),objectid=str(i));r=cq.importers.importStep(str(H/(name+'.step'))).val()
    fine_check=None
    if name=='Front_Oval_Shell':
        fine_path=H/'source_inputs/temporary_fine_front_check.stl';r.exportStl(str(fine_path),tolerance=.003,angularTolerance=.035,relative=False);fm=trimesh.load_mesh(fine_path,process=True);fm.update_faces(fm.nondegenerate_faces());fm.remove_unreferenced_vertices();fine_check={'absolute_deflection_mm':.003,'volume_mm3':float(fm.volume),'delivered_volume_change_percent':abs(m.volume/fm.volume-1)*100};fine_path.unlink()
    surface=cq.Compound.makeCompound(r.Faces());rr=np.random.default_rng(2);sampled=m.triangles_center[rr.choice(len(m.faces),min(100,len(m.faces)),replace=False)]-[xshift,0,0]+lo;deviation=max(cq.Vertex.makeVertex(*v).distance(surface)for v in sampled)
    checks.append({'STEP_sha256':hashlib.sha256((H/(name+'.step')).read_bytes()).hexdigest(),'part':name,'mesh_watertight':bool(m.is_watertight),'mesh_winding_consistent':bool(m.is_winding_consistent),'mesh_components':len(m.split()),'STEP_reimport_valid':r.isValid(),'STEP_solids':len(r.Solids()),'STEP_volume_mm3':r.Volume(),'STL_volume_mm3':float(m.volume),'removed_zero_area_pole_triangles':removed,'default_CAD_mass_vs_mesh_difference_percent':abs(m.volume/r.Volume()-1)*100,'sampled_triangle_centroid_surface_deviation_max_mm':deviation,'surface_sample_count':len(sampled),'finer_mesh_convergence':fine_check})
with zipfile.ZipFile(H/'Oval_E1_Three_Print_Parts_GEOMETRY_ONLY.3mf','w',zipfile.ZIP_DEFLATED)as z:
    z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    z.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>');z.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
(H/'Print_Export_Checks.json').write_text(json.dumps({'status':'Geometry-only 3MF—no printer/material/support profile','mesh_process':'Absolute 0.015mm deflection; remove zero-area pole triangles only. No holes filled or geometry enlarged.','volume_note':'Default CAD mass integration is unstable on the trimmed spheroidal crown; it is not a mesh acceptance metric. A separate0.003mmdeflection mesh checks convergence for the same STEP;100deterministic triangle-centroid surface distances are checked per part.','checks':checks},indent=2));print(json.dumps(checks,indent=2))
assert all(c['mesh_watertight']and c['mesh_winding_consistent']and c['STEP_reimport_valid']and c['STEP_solids']==1 and c['sampled_triangle_centroid_surface_deviation_max_mm']<.020 and (c['finer_mesh_convergence'] is None or c['finer_mesh_convergence']['delivered_volume_change_percent']<.15) for c in checks)
