#!/usr/bin/env python3
"""COUPON_FIRST plate: 4 joint-calibration slices (1 tongue back + grooves at
0.16/0.22/0.28, notch count = which). ~10 min print. Print in the SAME
filament + profile as the pendant plate or the calibration doesn't transfer."""
import struct, zipfile
import numpy as np

FILES = [
    ("stl_v5/coupon_back.stl",     "tongue (mate against each front)"),
    ("stl_v5/coupon_front_16.stl", "groove 0.16 - 1 notch"),
    ("stl_v5/coupon_front_22.stl", "groove 0.22 - 2 notches"),
    ("stl_v5/coupon_front_28.stl", "groove 0.28 - 3 notches"),
]

def load(path):
    with open(path,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        t=np.zeros((n,3,3),np.float32)
        for i in range(n):
            d=f.read(50)
            for k in range(3): t[i,k]=struct.unpack_from('<3f',d,12+12*k)
    return t

def mesh_xml(tris, oid, name):
    v = tris.reshape(-1,3)
    keys = np.round(v/0.001).astype(np.int64)
    uniq, inv = np.unique(keys, axis=0, return_inverse=True)
    verts = uniq*0.001
    faces = inv.reshape(-1,3)
    sv = "".join(f'<vertex x="{x:.3f}" y="{y:.3f}" z="{z:.3f}"/>' for x,y,z in verts)
    st = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a,b,c in faces)
    return (f'<object id="{oid}" type="model" name="{name}">'
            f'<mesh><vertices>{sv}</vertices><triangles>{st}</triangles></mesh></object>')

objects, items = [], []
for i,(path,name) in enumerate(FILES):
    tris = load(path)
    mn = tris.reshape(-1,3).min(0)
    tris = tris - mn
    objects.append(mesh_xml(tris, i+1, name))
    tx, ty = 100 + (i % 4)*20, 110
    items.append(f'<item objectid="{i+1}" transform="1 0 0 0 1 0 0 0 1 {tx} {ty} 0"/>')

model = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<model unit="millimeter" xml:lang="en-US" '
 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
 '<metadata name="Title">Anticipy click-joint coupon - print FIRST</metadata>'
 f'<resources>{"".join(objects)}</resources>'
 f'<build>{"".join(items)}</build></model>')

ct = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
 '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
rels = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
 '<Relationship Target="/3D/3dmodel.model" Id="rel-1" '
 'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')

with zipfile.ZipFile("COUPON_FIRST.3mf", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct)
    z.writestr("_rels/.rels", rels)
    z.writestr("3D/3dmodel.model", model)
print("wrote COUPON_FIRST.3mf")
