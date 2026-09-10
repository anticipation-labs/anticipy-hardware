"""Smooth E1 oval CASE FIT CANDIDATE. No fabrication/physical qualification claim."""
from pathlib import Path
import json,math,itertools,hashlib,ast,zipfile
import cadquery as cq
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
HERE=Path(__file__).resolve().parent
D=json.loads((HERE/'source_inputs/Final_PCB_Mechanical_Contract.json').read_text())['boards']['E1P1']
PCB_SOURCE=HERE.parent/'pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb'
if not PCB_SOURCE.exists():
    PCB_SOURCE=HERE.parent.parent/'Anticipy_E1P1_PCB_Manufacturing_Release_2026-09-09/pcb/electrical/Anticipy_R1_E1_PROTOTYPE.kicad_pcb'
if not PCB_SOURCE.exists():raise FileNotFoundError('Provide the immutable PCB release beside this package, or place its pcb/ directory beside cad/.')
SOURCE_SHA=hashlib.sha256(PCB_SOURCE.read_bytes()).hexdigest()
EXPECTED_PCB_SHA='78fe28acde6ceb3ab33aac8af503d4c418540cce31979cc91d3add5e5d0bec36'
assert SOURCE_SHA==EXPECTED_PCB_SHA==D['source_sha256'], 'PCB source must match the frozen handoff contract'
MAX_COMPONENTS=D['component_maximum_body_dimensions_mm']
P={'L':56.,'W':35.0,'H':14.8,'center_x':44.,'center_y':31.25,'wall':1.2,'back_plate_h':1.2,'seam_z':1.2,'pcb_bottom':9.1,'pcb_h':.8,'superellipse_power':3.2,'crown_axes':[120.,50.,35.], 'battery_center':[44.,35.6],'battery_max':[38.5,18.5,6.0],'battery_z':1.5,'battery_install_gap':.35,'motor_center':[38.,20.45],'motor_guard_D_H':[10.6,2.7],'motor_z':1.5}
CX,CY=P['center_x'],P['center_y'];BT=P['pcb_bottom']+P['pcb_h'];parts=[]
def box(x,y,z,w,l,h):return cq.Workplane('XY').box(w,l,h,centered=(True,True,False)).translate((x,-y,z)).val()
def cyl(x,y,z,d,h):return cq.Workplane('XY').center(x,-y).circle(d/2).extrude(h).translate((0,0,z)).val()
def super_prism(L,W,z,h):
    n=P['superellipse_power'];vv=[]
    for t in np.linspace(0,2*math.pi,160,endpoint=False):
        c,s=math.cos(t),math.sin(t);vv.append(cq.Vector(CX+L/2*math.copysign(abs(c)**(2/n),c),-CY+W/2*math.copysign(abs(s)**(2/n),s),z))
    edge=cq.Edge.makeSpline(vv,periodic=True);wire=cq.Wire.assembleEdges([edge]);return cq.Solid.extrudeLinear(wire,[],cq.Vector(0,0,h))
def crown(top):
    a,b,c=P['crown_axes'];s=cq.Workplane('XY').sphere(1).val().transformGeometry(cq.Matrix([[a,0,0,0],[0,b,0,0],[0,0,c,0],[0,0,0,1]]));return s.translate((CX,-CY,top-c))
def add(n,s,k='part',col='#566675',note=''):parts.append({'name':n,'shape':s,'kind':k,'color':col,'note':note})
def bounds(s):
    b=s.BoundingBox();return [[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax],[b.xlen,b.ylen,b.zlen]]
outer=super_prism(P['L'],P['W'],0,P['H']+1).intersect(crown(P['H']))
# Round the crown-to-side and back-to-side edges; no front screw flange.
outer=cq.Workplane(obj=outer).edges().fillet(.65).val()
inner=super_prism(P['L']-2*P['wall'],P['W']-2*P['wall'],P['back_plate_h'],P['H']).intersect(crown(P['H']-P['wall']))
front=outer.cut(inner).intersect(box(CX,CY,P['seam_z'],100,100,30))
back=outer.intersect(box(CX,CY,0,100,100,P['seam_z']))
# Board uses the frozen release outline and native poses, including the corrected U4 location.
polygon=[]
for x,y in D['outline']['ordered_closed_polygon_native_mm'][:-1]:
    polygon.append((x,y))
pcb=cq.Workplane('XY').polyline([(x,-y)for x,y in polygon]).close().extrude(P['pcb_h']).translate((0,0,P['pcb_bottom'])).val()
components={};inflated={}
for f in D['footprints']:
    ref=f['ref']
    if ref.startswith(('TP','NT')) or ref in ['BT1','M1','TH1'] or 'dnp' in f['attributes_native']:continue
    boxes=[m.get('bbox_native_xy_top_datum_z_mm')for m in f['models']if m.get('bbox_native_xy_top_datum_z_mm')]
    lo=[min(b[0][k]for b in boxes)for k in range(3)];hi=[max(b[1][k]for b in boxes)for k in range(3)]
    if ref=='J1':lo[0]=19.7
    x,y=(lo[0]+hi[0])/2,(lo[1]+hi[1])/2;w,l,h=[hi[k]-lo[k]for k in range(3)]
    if ref in MAX_COMPONENTS:
        ml,mw,mh=MAX_COMPONENTS[ref]['LWT'];ang=math.radians(f['rotation_deg'])
        w=abs(ml*math.cos(ang))+abs(mw*math.sin(ang));l=abs(ml*math.sin(ang))+abs(mw*math.cos(ang));h=mh
        x,y=f['position_native_mm'];lo[2]=0.0 if f['layer']=='F.Cu' else -P['pcb_h']-mh;hi[2]=lo[2]+mh
    components[ref]=box(x,y,BT+lo[2],w,l,h)
    zlo=lo[2]-(.2 if f['layer']=='B.Cu' or ref=='J1'else 0);zhi=hi[2]+(.2 if f['layer']=='F.Cu'or ref=='J1'else 0)
    inflated[ref]=box(x,y,BT+zlo,w+.4,l+.4,zhi-zlo)
    add(ref+'_native_body',components[ref],'part','#c3a269' if ref=='J1' else '#526173','Selected maximum body dimensions; an additional0.20mm per XY side and above is tested.' if ref in MAX_COMPONENTS else 'Nominal library/planning model envelope; inflated versions tested separately.')
add('PCB_cropped_native_outline',pcb,'pcb','#408878','Final78fe E1 PCB outline and component poses;45.75x17.88x0.8mm, not30mm hardware.')
bx,by=P['battery_center'];bl,bw,bh=P['battery_max'];battery=box(bx,by,P['battery_z'],bl,bw,bh);gap=P['battery_install_gap'];battery_install=box(bx,by,P['battery_z']-.05,bl+2*gap,bw+2*gap,bh+.10)
add('Jauch_LP561836JU_protected_pack_MAX_aftercycling',battery,'battery','#9fadb4','350mAh minimum/370typ; protected pack max38.5x18.5x6.0 aftercycling. Leads and separate NTC remain to approve.')
mx,my=P['motor_center'];md,mh=P['motor_guard_D_H'];motor=cyl(mx,my,P['motor_z'],md,mh);add('Existing_10mm_motor_installation_guard',motor,'motor','#b28d59','10.2mm published/model diameter plus0.2mm radial allowance;2.7mm height includes mounting guard. Exact lead exit/mount still qualify.')
# Actual USB-C opening: fixed J1 front plane X19.7, Y30.
zc=BT-.4
usb_gauge=box(10,30,zc-3.25,19.4,10.8,6.5)
usb_cut=box(10,30,zc-3.55,20,11.4,7.1)
front=front.cut(usb_cut);back=back.cut(usb_cut)
# Rear screw access: M2x4 pan-head planning hardware, no screws on the front.
# Direct M2 tapped polymer pillars; pullout/cycle life and printprocess not qualified.
for i,x in enumerate([20.8,67.5],1):
    y=30.;pillar=cyl(x,y,1.2,5.6,3.9)
    # Low rib connects each pillar to the nearby outer end below the USB tunnel.
    end=(CX-P['L']/2+.5) if i==1 else (CX+P['L']/2-.5)
    rib=box((x+end)/2,y,1.2,abs(x-end)+1.,4.0,2.2).intersect(outer)
    front=front.fuse(pillar).fuse(rib)
    # Back plate carries a local thick bearing pad; mating socket is cleared.
    bearing=cyl(x,y,0,5.8,2.2).intersect(outer)
    back=back.fuse(bearing)
    front=front.cut(cyl(x,y,1.19,6.1,1.21))
    front=front.cut(cyl(x,y,2.35,1.6,2.9))
    back=back.cut(cyl(x,y,-.1,2.2,2.5)).cut(cyl(x,y,-.1,4.4,1.45))
    screw=cyl(x,y,.05,4.,1.3).fuse(cyl(x,y,1.35,2.,4.))
    add(f'Rear_M2x4_screw_{i}_PLANNING',screw,'hardware','#99a5aa','Rear recessed pan head; exact screw/pilot/tap and insertion force require supplier selection.')
# PCB supports on back cover; vertical stems live outside battery, arms above it.
# Top-edge supports stay beside battery. Bottom supports bridge above cell with clear gap.
for i,(x,y) in enumerate([(31.5,min(y for x,y in polygon)),(48.7,min(y for x,y in polygon)),(34,max(y for x,y in polygon)),(49,max(y for x,y in polygon))],1):
    stem_y=18.1 if y<30 else 46.25
    stem=box(x,stem_y,1.0,2.0,1.4,P['pcb_bottom']-1.0)
    sy=(stem_y+y)/2
    arm=box(x,sy,P['pcb_bottom']-.55,2.,abs(stem_y-y)+.6,.55)
    back=back.fuse(stem).fuse(arm)
    # Flat thin pad at the native edge; copper-pad contacts checked separately.
# A board-outline guide constrains XY with0.35mm clearance; attached to the rear support arms.
from shapely.geometry import Polygon
pp=Polygon(polygon);po=pp.buffer(1.35,join_style=2);pi=pp.buffer(.35,join_style=2)
def polyshape(poly,z,h):return cq.Workplane('XY').polyline([(x,-y)for x,y in poly.exterior.coords[:-1]]).close().extrude(h).translate((0,0,z)).val()
guide=polyshape(po,P['pcb_bottom']-.20,1.35).cut(polyshape(pi,P['pcb_bottom']-.21,1.37)).cut(inflated['J1']).cut(usb_cut).intersect(inner)
# Pocket every underside pad locally; the routedPCB solder lands never bear on the guide.
for ff in D['footprints']:
    for pad in ff['pads']:
        if 'B.Cu' not in pad['layers']:continue
        x,y=pad['position_native_mm'];w,l=pad['size_mm']
        ps=box(0,0,P['pcb_bottom']-.3,w+.3,l+.3,.6).rotate((0,0,0),(0,0,1),pad['rotation_deg']).translate((x,-y,0))
        guide=guide.cut(ps)
back=back.fuse(guide)
# Upper polymer stops plus thin compliant pads capture PCB against the rear supports.
for x,y in [(31.5,min(y for x,y in polygon)),(48.7,min(y for x,y in polygon)),(34,max(y for x,y in polygon)),(49,max(y for x,y in polygon))]:
    front=front.fuse(box(x,y,BT+.3,.8,.6,P['H']-BT).intersect(outer))
    add(f'PCB_capture_pad_{x}_{y}',box(x,y,BT,.8,.6,.3),'board_pad','#454943','0.3mm compliant pad; compression and solder-mask contact require assembly coupon verification.')
# Microphone remains TOP port at its corrected original native coordinate.
portx,porty=46.3,23.12;mic_top=BT+1.25
acoustic=cyl(portx,porty,mic_top-.02,1.2,P['H']-mic_top+.2)
chimney=cyl(portx,porty,mic_top+.4,3.,P['H']-mic_top).intersect(outer)
front=front.fuse(chimney).cut(acoustic)
gasket=cyl(portx,porty,mic_top,2.7,.4).cut(acoustic);add('Microphone_gasket',gasket,'seal','#343c40','Planning foam gasket0.4mm; sensitivity and sealing not physically tested.')
# LED aperture/lightpipe and a recessed button cap, both aligned to actual PCB.
ledx,ledy=34.,36.7;led_top=BT+.6
ledhole=cyl(ledx,ledy,led_top,1.8,P['H']-led_top+.2)
front=front.cut(ledhole)
front=front.fuse(cyl(ledx,ledy,led_top+1.0,3.6,P['H']-led_top).intersect(outer)).cut(ledhole)
light=cyl(ledx,ledy,led_top+.30,1.65,P['H']-led_top).intersect(outer).fuse(cyl(ledx,ledy,led_top+.5,2.7,.4))
add('Lightpipe_retaining_adhesive',cyl(ledx,ledy,led_top+1.05,1.8,.3).cut(cyl(ledx,ledy,led_top+1.04,1.65,.32)),'adhesive','#adc6c0','Nonconductive optical adhesive annulus; exact material/creep not qualified.')
add('LED_clear_lightpipe',light,'control','#bdc9bf','0.30mm LED airgap; internal collar and adhesive gauge retain the lightpipe. Optical material/adhesive requires supplier selection.')
sx,sy=30.,36.3;switch_top=BT+1.6
buttonhole=cyl(sx,sy,switch_top,3.0,P['H']-switch_top+.2)
front=front.cut(buttonhole)
front=front.fuse(cyl(sx,sy,12.99,5.,P['H']-12.99).intersect(outer)).cut(buttonhole)
button=cyl(sx,sy,switch_top+.8,2.6,P['H']-switch_top).intersect(outer).fuse(cyl(sx,sy,switch_top+.3,1.4,.5)).fuse(cyl(sx,sy,12.55,4.0,.4))
add('Recessed_button_plunger',button,'control','#c9a55f','Flush crown-following cap with4mmretaining collar and1.4mmnose. 0.3mmnominal free travel then assumed0.2mmactuation; verify exact switch stroke/force and add environmental membrane ifrequired.')
# Rounded back-only lanyard bore through a molded boss; avoids E1 antenna exclusion.
# Polymer boss stays inside outer dimensions; removable textile loop is not included.
loopx,loopy=23.0,20.0
loopboss=box(loopx,loopy,1.2,5.0,4.0,3.6).intersect(outer)
front=front.fuse(loopboss)
loopbore=cq.Workplane('YZ').center(-loopy,3.).circle(1.0).extrude(14).translate((14,0,0)).val()
front=front.cut(loopbore)
add('Textile_lanyard_internal_knot_guard',box(27.5,20.,1.7,4.,4.,2.6),'textile','#7d6955','Two fine textile strands pass through the2mmshort-end bore and tie inside this knot gauge before closure. Cord/knot size and pullout needtesting; externalloop isnotmodeled.')
# Make mating shell seam real and leave backcover removable.
front=front.clean();back=back.clean()
add('Front_oval_shell',front,'shell','#c6a369','Nonconductive polymer; gold is visual finish proposal, not metal certification.')
add('Rear_service_cover',back,'shell','#b5915c','Rear-only screw heads; no fragile snap fit assumed. Prototype printing needs supplier tolerance review.')
exec(compile((HERE/'harness_fragment.py').read_text(),str(HERE/'harness_fragment.py'),'exec'))
checks=[]
def check(name,a,b=None):
    
    if b is None:v=float(a)
    else:
        aa,bb=a.BoundingBox(),b.BoundingBox()
        disjoint=any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-9 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-9 for k in 'xyz')
        v=0. if disjoint else a.intersect(b).Volume()
    checks.append({'check':name,'value_mm3':max(v,0),'pass':v<1e-6})
for n,s in [('PCB',pcb),*[(r+'_expanded',s)for r,s in inflated.items()],('battery_installation',battery_install),('motor',motor),('USB_gauge',usb_gauge)]:
    check(n+' vs front',s,front);check(n+' vs back',s,back)
for n,s in inflated.items():check('battery_installation vs '+n,battery_install,s);check('motor vs '+n,motor,s)
check('battery vs motor',battery_install,motor);check('front vs back',front,back)
for n,s in [('battery',battery_install),('motor',motor)]:
    check(n+' outside outer',s.cut(outer).Volume())
for r in D['rf_enclosure_metal_exclusion_regions_native_mm']:
    lo,hi=r['bounds_xy_mm'];rf=box((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0,hi[0]-lo[0],hi[1]-lo[1],P['H'])
    for p in parts:
        if p['kind'] in ['battery','motor','hardware']:check(p['name']+' vs RF exclusion',p['shape'],rf)
for p in parts:
    if p['kind'] in ['hardware','control','seal','board_pad','adhesive']:
        if p['kind']!='hardware':check(p['name']+' vs front',p['shape'],front);check(p['name']+' vs back',p['shape'],back)
        check(p['name']+' vs battery',p['shape'],battery_install)
# Real pad-vs-support check for exposed backside pads with0.10mm planar allowance.
for f in D['footprints']:
    for p in f['pads']:
        if 'B.Cu' not in p['layers']:continue
        x,y=p['position_native_mm'];w,l=p['size_mm'];z=P['pcb_bottom']-.12
        pad=box(0,0,z,w+.2,l+.2,.12).rotate((0,0,0),(0,0,1),p['rotation_deg']).translate((x,-y,0))
        check(f['ref']+'/'+p['number']+' underside pad vs back support',pad,back)
# Explicit harness collision tests: only exact intended wire-to-own-terminal joints are exempt.
harness=[p for p in parts if p['kind'] in ['wire','joint','ntc']]
intentional=[]
for p in harness:
    for n,ss in [('front',front),('back',back),('PCB',pcb),('battery',battery),('motor',motor),*inflated.items()]:check(p['name']+' vs '+n,p['shape'],ss)
    for q in harness:
        if q['name']>=p['name']:continue
        own=(p['name'].startswith('BATTERY_NEG') and q['name'].startswith('BATTERY_NEG'))or(p['name'].startswith('BATTERY_POS')and q['name'].startswith('BATTERY_POS'))
        ntcjoint=p['name'].startswith('Separate_10k_NTC')and q['name'].startswith('NTC_wire') or q['name'].startswith('Separate_10k_NTC')and p['name'].startswith('NTC_wire')
        if own or ntcjoint:
            intentional.append({'parts':[p['name'],q['name']],'volume_mm3':p['shape'].intersect(q['shape']).Volume(),'reason':'exact own-terminal solder/thermistor lead attachment'});continue
        check(p['name']+' vs '+q['name'],p['shape'],q['shape'])
for p in parts:
    check(p['name']+' outside enclosing oval',p['shape'].cut(outer).Volume())
    if p['kind'] in ['control','seal','board_pad','adhesive','hardware']:
        for ref,ss in inflated.items():
            if p['name']=='Microphone_gasket' and ref=='MIC1':
                check('Microphone free gasket vs nominal actual MIC1',p['shape'],components['MIC1']);intentional.append({'parts':['Microphone_gasket','MIC1_expanded_assembly_allowance'],'volume_mm3':p['shape'].intersect(ss).Volume(),'reason':'0.4mmfreefoam gasket reserves up to0.2mmcompression for the extra MIC mounting-height allowance; requirescompression/leaktest'})
            else:check(p['name']+' vs expanded '+ref,p['shape'],ss)
        check(p['name']+' vs PCB',p['shape'],pcb);check(p['name']+' vs motor',p['shape'],motor)
    if p['kind']=='hardware':
        check(p['name']+' vs back counterbore',p['shape'],back)
        x=20.8 if p['name'].endswith('_1_PLANNING')else 67.5
        thread_zone=cyl(x,30,2.35,2.01,3.1)
        check(p['name']+' vs front outside threaded pilot',p['shape'].cut(thread_zone),front)
# Button0.50mmstroke:0.30mm nominal free gap then0.20mm actuator travel.
# This tests an explicit actuator allowance; manufacturer switch travel/force must confirm it.
actuator_zone=cyl(sx,sy,switch_top-.21,1.42,.42)
for down in [0,.1,.2,.3,.4,.5]:
    moving=button.translate((0,0,-down));check(f'button at travel{down} vs shell',moving,front)
    for ref,ss in inflated.items():check(f'button at travel{down} vs '+ref,moving,ss.cut(actuator_zone)if ref=='SW1'else ss)
check('microphone air bore through front shell',acoustic,front)
check('lanyard bore continuous from exterior to cavity',loopbore,front)
for pp in parts:
    if pp['kind']=='textile':
        for n,ss in [('front',front),('back',back),('battery',battery_install),('motor',motor),('PCB',pcb),*inflated.items()]:check(pp['name']+' vs '+n,pp['shape'],ss)
for f in D['footprints']:
    for pad in f['pads']:
        if 'F.Cu' not in pad['layers']:continue
        x,y=pad['position_native_mm'];w,l=pad['size_mm']
        ps=box(0,0,BT,w+.2,l+.2,.3).rotate((0,0,0),(0,0,1),pad['rotation_deg']).translate((x,-y,0))
        for pp in parts:
            if pp['kind']=='board_pad':check(f['ref']+'/'+pad['number']+' front pad vs '+pp['name'],ps,pp['shape'])
result={'status':'FINAL_PCB_MATCHED_OVAL_CASE_FIT_CANDIDATE_NOT_PHYSICALLY_QUALIFIED','parameters':P,'maximum_component_envelopes_mm':MAX_COMPONENTS,'U4_native_position_mm':[28.15,29.45],'native_source':str(PCB_SOURCE),'PCB_sha256':SOURCE_SHA,'PCB_LWT_mm':[pcb.BoundingBox().xlen,pcb.BoundingBox().ylen,pcb.BoundingBox().zlen],'outer_default_CAD_volume_mm3_for_diagnostic_only':outer.Volume(),'outer_LWT_mm':[outer.BoundingBox().xlen,outer.BoundingBox().ylen,outer.BoundingBox().zlen],'print_part_solid_counts':{'front':len(front.Solids()),'back':len(back.Solids()),'button':len(button.Solids()),'lightpipe':len(light.Solids())},'all_shapes_valid':all(p['shape'].isValid() for p in parts),'intentional_terminal_joints':intentional,'fasteners':{'quantity':2,'thread':'M2','underhead_length_mm':4.,'head_max_diameter_mm':4.,'head_max_height_mm':1.3,'tip_max_z_mm':5.35,'tip_vertical_gap_to_PCB_mm':P['pcb_bottom']-5.35,'retention':'TapM2threadin1.6mmpilotof5.6mmpolymerpillar; supplier mustapprovepulloutandcycles'},'check_count':len(checks),'checks':checks,'failures':[c for c in checks if not c['pass']],'unclosed':['Supplier-confirmed battery/motor wire exit, OD, bend radius, trim/strain relief and selected NTC adhesive','Screw/pilot/tap pullout and cycle tests','Button switch stroke/force, retaining collar fit, lightpipe adhesive and environmental sealing','Acoustic and RF performance with finish and textile loop','Complete fit of manufactured tolerances','16-hour runtime and physical charging qualification']}
(HERE/'Oval_E1_Checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'outer':result['outer_LWT_mm'],'checks':len(checks),'valid':result['all_shapes_valid'],'failures':result['failures']},indent=2))
if result['failures'] or not result['all_shapes_valid']:raise SystemExit(2)
for name,s in [('Front_Oval_Shell',front),('Rear_Service_Cover',back),('Button_Plunger',button),('Clear_Lightpipe',light)]:
    cq.exporters.export(s,str(HERE/(name+'.step')))
    # File is in assembled coordinates; orient in slicer as described in handoff.
    s.exportStl(str(HERE/(name+'.stl')),tolerance=.015,angularTolerance=.05,relative=False)
assembly=cq.Assembly(name='ANTICIPY_OVAL_E1_FIT_CANDIDATE');exploded=cq.Assembly(name='ANTICIPY_OVAL_E1_EXPLODED_VIEW')
for p in parts:
    color=cq.Color(*to_rgb(p['color']));assembly.add(p['shape'],name=p['name'],color=color)
    dz=12 if p['name']=='Front_oval_shell' else -8 if p['name']=='Rear_service_cover' else 0
    exploded.add(p['shape'].translate((0,0,dz)),name=p['name'],color=color)
assembly.save(str(HERE/'Oval_E1_Assembly_FIT_CANDIDATE.step'));exploded.save(str(HERE/'Oval_E1_Exploded_VIEW_ONLY.step'))
# Render exact modeled shapes; gold is display color, not a fictitious metal enclosure.
helper=HERE/'source_inputs/render_helpers.py';nodes=ast.parse(helper.read_text());fs=[n for n in nodes.body if isinstance(n,ast.FunctionDef) and n.name in ['render','canvas','picture','note','save']]
r={'np':np,'math':math,'plt':plt,'to_rgb':to_rgb,'INK':'#223a46','MUTED':'#5b6b74','WARN':'#9a5c32','OUT':HERE};exec(compile(ast.Module(body=fs,type_ignores=[]),str(helper),'exec'),r)
f=r['canvas']('Anticipy / smooth oval E1','Matched to the final E1P1 PCB. Curved crown, hidden rear screws; gold is display color only.',(15,10));ax,pr=r['picture'](f,[.02,.12,.7,.75],parts,elev=65,azim=-72,size=1400)
f.text(.75,.72,f"{P['L']:g} × {P['W']:g} × {P['H']:g} mm",fontsize=18,weight='bold',color='#223a46');f.text(.75,.64,'Protected 350 mAh battery\nExisting E1 electronics\nUSB-C port\nCharging disabled\nTop microphone opening\nLED window and button\nRear service cover',va='top',linespacing=1.7,color='#223a46');f.text(.04,.05,'Geometric fit candidate. Wire gauges and controls are modeled; actual fit, RF, runtime, charging and manufacturing tolerances remain unqualified.',fontsize=11,color='#9a5c32');r['save'](f,'Oval_E1_Gold_Exterior.png')
f=r['canvas']('Anticipy / inside the oval E1','Final PCB poses, including corrected U4. Top shell removed; selected maximum bodies and other planning envelopes are shown.',(15,10));inside=[p for p in parts if p['name']!='Front_oval_shell'];ax,pr=r['picture'](f,[.02,.12,.74,.75],inside,elev=55,azim=-70,size=1400)
f.text(.77,.72,'The radio area stays clear',fontsize=15,weight='bold',color='#223a46');f.text(.77,.63,'Battery sits away from\nthe antenna exclusion.\nMotor sits beside the pack.\nThe PCB sits above both.',va='top',linespacing=1.7,color='#223a46');f.text(.04,.05,'Assembly details are provisional. The cell is a selected candidate with documented dimensions; stock is not allocation or delivery.',fontsize=11,color='#9a5c32');r['save'](f,'Oval_E1_Inside.png')
