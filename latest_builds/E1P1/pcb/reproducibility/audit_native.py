from pathlib import Path
import pcbnew as p,json,hashlib,collections,xml.etree.ElementTree as ET,csv
W=Path(__file__).resolve().parent.parent;el=W/'electrical';v=W/'verification';name='Anticipy_R1_E1_PROTOTYPE';pcb=el/(name+'.kicad_pcb');raw=pcb.read_bytes();b=p.LoadBoard(str(pcb));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu];xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
def ring(r):return[xy(r.CPoint(i))for i in range(r.PointCount())]
def polys(poly):return[dict(shell=ring(poly.COutline(i)),holes=[ring(poly.CHole(i,j))for j in range(poly.HoleCount(i))])for i in range(poly.OutlineCount())]
d=dict(pads=[],tracks=[],zones=[],keepouts=[],outline=[],layer_names=[b.GetLayerName(l)for l in layers]);fps=[];boardnets=collections.defaultdict(set)
for f in b.GetFootprints():
 fps.append(dict(ref=f.GetReference(),value=f.GetValue(),footprint=str(f.GetFPID().GetLibItemName()),dnp=f.IsDNP(),exclude_pos=f.IsExcludedFromPosFiles(),exclude_bom=f.IsExcludedFromBOM(),pos=xy(f.GetPosition()),angle=f.GetOrientationDegrees(),side='bottom'if f.IsFlipped()else'top'))
 for q in f.Pads():
  poly=p.SHAPE_POLY_SET();q.TransformShapeToPolygon(poly,p.B_Cu if f.IsFlipped()else p.F_Cu,0,1000,p.ERROR_INSIDE)
  d['pads'].append(dict(ref=f.GetReference(),pin=q.GetNumber(),net=q.GetNetname(),dnp=f.IsDNP(),pos=xy(q.GetPosition()),layers=[i for i,l in enumerate(layers)if q.IsOnLayer(l)],polygons=polys(poly),drill=xy(q.GetDrillSize())))
  if q.GetNetname():boardnets[str(q.GetNetname()).lstrip('/')].add((f.GetReference(),str(q.GetNumber())))
 for z in f.Zones():
  if z.GetIsRuleArea():d['keepouts'].append(dict(owner=f.GetReference(),polygons=polys(z.Outline()),layers=[i for i,l in enumerate(layers)if z.IsOnLayer(l)],tracks=z.GetDoNotAllowTracks(),vias=z.GetDoNotAllowVias()))
for z in b.Zones():
 if z.GetIsRuleArea():d['keepouts'].append(dict(owner='board',polygons=polys(z.Outline()),layers=[i for i,l in enumerate(layers)if z.IsOnLayer(l)],tracks=z.GetDoNotAllowTracks(),vias=z.GetDoNotAllowVias()))
 else:
  for i,l in enumerate(layers):
   if z.IsOnLayer(l):d['zones'].append(dict(net=z.GetNetname(),layer=i,polygons=polys(z.GetFilledPolysList(l))))
for t in b.GetTracks():
 via=isinstance(t,p.PCB_VIA)
 d['tracks'].append(dict(start=xy(t.GetStart()),end=xy(t.GetEnd()),width=p.ToMM(t.GetWidth(p.F_Cu)if via else t.GetWidth()),net=t.GetNetname(),layers=list(range(4))if via else[layers.index(t.GetLayer())],via=via,uuid=t.m_Uuid.AsString(),drill=p.ToMM(t.GetDrillValue())if via else None))
for z in b.GetDrawings():
 if z.GetLayer()==p.Edge_Cuts:d['outline'].append(dict(shape=int(z.GetShape()),start=xy(z.GetStart()),end=xy(z.GetEnd()),width=p.ToMM(z.GetWidth())))
netxml=ET.parse(v/'native_netlist.xml').getroot();schematicnets={n.get('name').lstrip('/'):set((q.get('ref'),q.get('pin'))for q in n.findall('node'))for n in netxml.find('nets')if not n.get('name').startswith('unconnected-')};expected={n.lstrip('/'):set(tuple(q)for q in qs)for n,qs in json.loads((el/'E1_expected_connectivity.json').read_text()).items()}
parity=[]
for label,left in [('fresh_schematic',schematicnets),('expected_map',expected)]:
 for net in sorted(set(left)|set(boardnets)):
  if left.get(net,set())!=boardnets.get(net,set()):parity.append(dict(source=label,net=net,missing_in_pcb=sorted(left.get(net,set())-boardnets.get(net,set())),extra_in_pcb=sorted(boardnets.get(net,set())-left.get(net,set()))))
c=b.GetConnectivity();assert c.Build(b);c.RecalculateRatsnest();pp={q.m_Uuid.AsString():q for f in b.GetFootprints()for q in f.Pads()if q.GetNetname()};parent={uid:uid for uid in pp}
def find(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for uid,q in pp.items():
 for it in c.GetConnectedItems(q):
  other=it.m_Uuid.AsString()
  if other in pp and it.GetNetname()==q.GetNetname():parent[find(other)]=find(uid)
groups=collections.defaultdict(lambda:collections.defaultdict(list))
for uid,q in pp.items():groups[q.GetNetname()][find(uid)].append(q.GetParentFootprint().GetReference()+'.'+q.GetNumber())
project=json.loads((el/(name+'.kicad_pro')).read_text());severity=project['board']['design_settings']['rule_severities'];ercrules=project['erc']['rule_severities'];custom=(el/(name+'.kicad_dru')).read_text()
power_required={'U2.32':'3V_MAIN','L2.1':'3V_MAIN','C8.1':'3V_MAIN','U2.1':'2V5_AUX','L1.1':'2V5_AUX','C7.1':'2V5_AUX','TP12.1':'2V5_AUX','U2.12':'3V_MAIN','U2.28':'3V_MAIN','U5.8':'3V_MAIN'};padnet={q['ref']+'.'+q['pin']:q['net'].lstrip('/')for q in d['pads']};power={ref:dict(expected=net,actual=padnet.get(ref),pass_check=padnet.get(ref)==net)for ref,net in power_required.items()}
report=dict(source=str(pcb),source_sha256=hashlib.sha256(raw).hexdigest(),kicad_version=p.GetBuildVersion(),board_thickness_mm=p.ToMM(b.GetDesignSettings().GetBoardThickness()),copper_layers=d['layer_names'],footprint_count=len(fps),physical_pad_count=len(d['pads']),named_net_pad_count=len(pp),named_net_count=len(boardnets),track_segments=sum(not t['via']for t in d['tracks']),via_count=sum(t['via']for t in d['tracks']),zones=len(d['zones']),schematic_to_pcb_and_expected_map={'status':'PASS'if not parity else'FAIL','mismatches':parity},native_saved_copper_unconnected_count=c.GetUnconnectedCount(False),native_connected_pad_groups={str(n):list(gs.values())for n,gs in groups.items()},power_contract={'status':'PASS'if all(z['pass_check']for z in power.values())else'FAIL','checks':power},ignored_DRC_categories=[n for n,z in severity.items()if z=='ignore'],ignored_ERC_categories=[n for n,z in ercrules.items()if z=='ignore'],DRC_exclusions=project['board']['design_settings']['drc_exclusions'],ERC_exclusions=project['erc']['erc_exclusions'],board_rules=project['board']['design_settings']['rules'],custom_rules=custom,source_unchanged=raw==pcb.read_bytes())
(v/'native_board_audit.json').write_text(json.dumps(report,indent=2)+'\n');(v/'routing_geometry.json').write_text(json.dumps(d));(v/'native_population.json').write_text(json.dumps(fps,indent=2)+'\n');print(json.dumps({k:z for k,z in report.items()if k not in['native_connected_pad_groups','board_rules','custom_rules','power_contract']},indent=2))
