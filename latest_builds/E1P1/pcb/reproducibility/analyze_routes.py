from pathlib import Path
import json,csv,math,collections,heapq,itertools
import numpy as np
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union

OUT=Path(__file__).resolve().parent.parent/'verification'
d=json.loads((OUT/'routing_geometry.json').read_text())
def poly(x):return unary_union([Polygon(v['shell'],v['holes']).buffer(0)for v in x])
planes={i:unary_union([poly(z['polygons'])for z in d['zones']if z['net']=='/GND'and z['layer']==i])for i in range(4)}
tracks=collections.defaultdict(list);pads=collections.defaultdict(list)
for t in d['tracks']:tracks[t['net'].lstrip('/')].append(t)
for p in d['pads']:
 if p['net']:pads[p['net'].lstrip('/')].append(p)
netrows=[];unsupported=[]
for net in sorted(pads):
 ts=tracks[net];lines=[t for t in ts if not t['via']];vias=[t for t in ts if t['via']]
 lengths={i:sum(math.dist(t['start'],t['end'])for t in lines if t['layers']==[i])for i in range(4)}
 row=dict(net=net,unique_pads=len(set((p['ref'],p['pin'])for p in pads[net])),track_segments=len(lines),vias=len(vias),total_track_mm=round(sum(lengths.values()),3),
  min_track_width_mm=min([t['width']for t in lines],default=0),
  max_track_width_mm=max([t['width']for t in lines],default=0),
  **{d['layer_names'][i]+'_mm':round(v,3)for i,v in lengths.items()})
 # This is deliberately a projection screen, not an impedance solver:
 # Adjacent reference projections: F.Cu->In1.Cu, In1.Cu->F.Cu,
 # In2.Cu->B.Cu, B.Cu->In2.Cu. The main B.Cu USB corridor has an
 # actual filled In2 GND reference; its signal-track keepout permits zones.
 for i,ref in [(0,1),(1,0),(2,3),(3,2)]:
  selected=[t for t in lines if t['layers']==[i]]
  miss=0
  for t in selected:
   line=LineString([t['start'],t['end']]);bad=line.difference(planes[ref]);miss+=bad.length
   if net!='GND'and bad.length>0.01:
    unsupported.append(dict(net=net,layer=d['layer_names'][i],reference=d['layer_names'][ref],uuid=t['uuid'],length_without_projected_GND_mm=round(bad.length,4),start=t['start'],end=t['end']))
  row[d['layer_names'][i]+'_without_adjacent_GND_mm']=round(miss,3)
 netrows.append(row)

# Independent geometry connectivity: continuous copper on each layer, linked by
# plated through vias/pads. Shape tolerance is 1 um; the native DRC is authoritative.
connect=[]
for net in sorted(pads):
 layer_shapes=[];geoms=[]
 for i in range(4):
  shapes=[poly(p['polygons'])for p in pads[net]if i in p['layers']]
  shapes += [Point(t['start']).buffer(t['width']/2)if t['via']else LineString([t['start'],t['end']]).buffer(t['width']/2)for t in tracks[net]if i in t['layers']]
  if net=='GND':shapes.append(planes[i])
  u=unary_union(shapes).buffer(.001)
  chunks=list(u.geoms)if hasattr(u,'geoms')else([u]if not u.is_empty else[])
  layer_shapes.append([(len(geoms)+j,g)for j,g in enumerate(chunks)]);geoms+=chunks
 parent=list(range(len(geoms)))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 def join(ids):
  for a in ids[1:]:parent[find(a)]=find(ids[0])
 for t in tracks[net]:
  if t['via']:
   pt=Point(t['start']);join([j for i in t['layers']for j,g in layer_shapes[i]if g.covers(pt)])
 for p in pads[net]:
  if len(p['layers'])>1:
   pg=poly(p['polygons']);join([j for i in p['layers']for j,g in layer_shapes[i]if g.intersects(pg)])
 pad_roots={}
 for p in pads[net]:
  ids=[j for i in p['layers']for j,g in layer_shapes[i]if g.intersects(poly(p['polygons']))]
  roots=set(find(j)for j in ids);pad_roots.setdefault(p['ref']+'.'+p['pin'],set()).update(roots)
 roots=set.union(*pad_roots.values())if pad_roots else set()
 connect.append(dict(net=net,pad_connected_components=len(roots),result='PASS'if len(roots)==1 else'REVIEW',pad_roots={k:sorted(v)for k,v in pad_roots.items()}))

# Approximate routed centerline paths, with electrically overlapping copper
# treated as junctions. Pad spreading, via resistance and package traces excluded.
def route(net,first,last):
 ts=[t for t in tracks[net]if not t['via']];graph=collections.defaultdict(list)
 cuts=[[0.,1.]for t in ts];lines=[LineString([t['start'],t['end']])for t in ts]
 def node(i,f):
  q=lines[i].interpolate(f,normalized=True);return(ts[i]['layers'][0],round(q.x,6),round(q.y,6))
 def edge(a,b,l,width=None,layer=None):
  resistance=0 if width is None else .01724*l/(width*(.035 if layer in [0,3]else .018))/1000
  graph[a].append((b,l,resistance));graph[b].append((a,l,resistance))
 # Centerline crossings and endpoints meeting copper, including non-centered via landings.
 for i,j in itertools.combinations(range(len(ts)),2):
  if ts[i]['layers']!=ts[j]['layers']:continue
  a,b=lines[i],lines[j]
  if a.distance(b)>(ts[i]['width']+ts[j]['width'])/2+.000002:continue
  pairs=[]
  for f in [0.,1.]:
   pt=a.interpolate(f,normalized=True);g=b.project(pt,normalized=True)
   if pt.distance(b)<=ts[j]['width']/2+.000002:pairs.append((f,g))
  for g in [0.,1.]:
   pt=b.interpolate(g,normalized=True);f=a.project(pt,normalized=True)
   if pt.distance(a)<=ts[i]['width']/2+.000002:pairs.append((f,g))
  inter=a.intersection(b)
  if inter.geom_type=='Point':pairs.append((a.project(inter,normalized=True),b.project(inter,normalized=True)))
  for f,g in pairs:cuts[i].append(f);cuts[j].append(g);edge(node(i,f),node(j,g),math.dist(node(i,f)[1:],node(j,g)[1:]))
 contacts=[('via'+str(k),Point(t['start']).buffer(t['width']/2),t['layers'],t['start'])for k,t in enumerate(tracks[net])if t['via']]
 contacts += [(p['ref']+'.'+p['pin'],poly(p['polygons']),p['layers'],p['pos'])for p in pads[net]]
 for key,shape,layers,pos in contacts:
  for i,line in enumerate(lines):
   if ts[i]['layers'][0]in layers and shape.distance(line)<=ts[i]['width']/2+.000002:
    f=line.project(Point(pos),normalized=True);cuts[i].append(f);edge(key,node(i,f),math.dist(pos,node(i,f)[1:]))
 for i,cs in enumerate(cuts):
  cs=sorted(set(round(x,12)for x in cs))
  for a,b in zip(cs,cs[1:]):edge(node(i,a),node(i,b),lines[i].length*(b-a),ts[i]['width'],ts[i]['layers'][0])
 queue=[(0.,0,first,0.)];seq=itertools.count(1);seen=set()
 while queue:
  distance,_,key,res=heapq.heappop(queue)
  if key in seen:continue
  seen.add(key)
  if key==last:return dict(net=net,first=first,last=last,approx_planar_path_with_pad_spreading_mm=round(distance,3),via_height_excluded=True,overlap_junction_distance_costed=True)
  for other,l,r in graph[key]:
   if other not in seen:heapq.heappush(queue,(distance+l,next(seq),other,res+r))
 return dict(net=net,first=first,last=last,error='No route in centerline approximation; inspect native connectivity')
pairs=[('USB_D+','J1.6','R10.1'),('USB_MCU_D+','R10.2','U1.35'),('USB_D-','J1.5','R11.1'),('USB_MCU_D-','R11.2','U1.34'),
 ('PDM_CLK','U1.38','MIC1.3'),('PDM_CLK','MIC1.3','MIC2.3'),('PDM_DATA','R8.2','U1.39'),('PDM_DATA_MIC1','MIC1.4','R8.1'),
 ('I2C_SCL','U1.19','U2.14'),('I2C_SDA','U1.16','U2.13'),('FLASH_SCK','U1.42','U5.6'),('FLASH_IO0','U1.43','U5.5'),('FLASH_IO1','U5.2','U1.46'),
 ('FLASH_CS','U1.44','U5.1'),('SWDCLK','TP2.1','U1.53'),('SWDIO','TP1.1','U1.51'),('3V_MAIN','L2.1','U1.28'),('3V_MAIN','L2.1','U5.8'),('3V_MAIN','L2.1','M1.1'),('VBAT','BT1.1','U2.19'),('VBUS','J1.2','U2.21')]
pairs += [('USB_D+','J1.8','R10.1'),('USB_D-','J1.7','R11.1')]
pairs += [('2V5_AUX','L1.1','U2.1'),('2V5_AUX','L1.1','TP12.1'),('3V_MAIN','L2.1','U2.32')]
paths=[route(*x)for x in pairs]
with(OUT/'all_45_nets.csv').open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=netrows[0]);w.writeheader();w.writerows(netrows)
for name,obj in [('projected_return_gaps.json',unsupported),('independent_copper_connectivity.json',connect),('critical_paths.json',paths)]:
 (OUT/name).write_text(json.dumps(obj,indent=2))
print('Connectivity',collections.Counter(x['result']for x in connect));print(json.dumps(paths,indent=2))
print('Projected ground gaps by net',sorted(((r['net'],round(sum(r[d['layer_names'][i]+'_without_adjacent_GND_mm']for i in range(4)),2))for r in netrows if r['net']!='GND'),key=lambda x:-x[1])[:12])
