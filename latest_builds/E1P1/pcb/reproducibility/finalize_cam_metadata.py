"""Correct KiCad job bounding metadata to the routed profile centerline.

KiCad includes the 0.10 mm Edge.Cuts graphic stroke in job Size. The actual
routed contour and all copper/drill data remain unchanged. Process requirements
such as Type VII filling are carried by the explicit fabrication specification.
"""
from pathlib import Path
import json,hashlib,shutil
P=Path(__file__).resolve().parent.parent; V=P/'verification'; M=P/'manufacturing'
d=json.loads((V/'routing_geometry.json').read_text())
assert all(s['shape']==0 for s in d['outline']),'Handle arcs explicitly before deriving bounds'
pts=[p for s in d['outline'] for p in [s['start'],s['end']]]
size={'X':round(max(p[0] for p in pts)-min(p[0] for p in pts),6),'Y':round(max(p[1] for p in pts)-min(p[1] for p in pts),6)}
assert size=={'X':45.75,'Y':17.88}
jpath=M/'gerbers/Anticipy_R1_E1_PROTOTYPE-job.gbrjob';j=json.loads(jpath.read_text());old=j['GeneralSpecs']['Size']
assert all(abs(old[k]-size[k])<1e-6 or abs(old[k]-size[k]-.1)<1e-6 for k in size)
if old!=size:shutil.copyfile(jpath,V/'native_job_before_profile_size_correction.json')
j['GeneralSpecs']['Size']=size;jpath.write_text(json.dumps(j,indent=2)+'\n')
(V/'CAM_Job_Metadata_Receipt.json').write_text(json.dumps({'native_job_size_includes_graphic_stroke_mm':old,'released_job_profile_centerline_size_mm':size,'scope':'Gerber-job size metadata only; copper, masks, profile and drill files untouched','job_sha256':hashlib.sha256(jpath.read_bytes()).hexdigest(),'via_fill_cap_specification':'All137 TypeVII as fabrication specification/coordinate CSV; do not rely on Gerber-job flags to communicate this process'},indent=2))
print('Released Gerber job profile size',size)
