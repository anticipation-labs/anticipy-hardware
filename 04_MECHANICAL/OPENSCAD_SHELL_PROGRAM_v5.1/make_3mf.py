#!/usr/bin/env python3
"""Build a single 3MF containing all 8 pendant halves arranged in a 2x4
grid, ready to open in Bambu Studio and slice. Plain core-spec 3MF."""
import struct, zipfile, io
import numpy as np

FILES = [(f"stl/anticipy_v{v}_{h}.stl", f"V{v} {h}") for v in (1,2,3,4) for h in ("front","back")]

def load(path):
    with open(path,'rb') as f:
        f.read(80); n=struct.unpack('<I',f.read(4))[0]
        t=np.zeros((n,3,3),np.float32)
        for i in range(n):
            d=f.read(50)
            for k in range(3): t[i,k]=struct.unpack_from('<3f',d,12+12*k)
    return t

def mesh_xml(tris, oid, name):
    # weld vertices
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
    # normalize to origin (min corner at 0)
    mn = tris.reshape(-1,3).min(0)
    tris = tris - mn
    oid = i+1
    objects.append(mesh_xml(tris, oid, name))
    col, row = i % 4, i // 4
    tx, ty = 30 + col*34, 40 + row*72
    items.append(f'<item objectid="{oid}" transform="1 0 0 0 1 0 0 0 1 {tx} {ty} 0"/>')

model = ('<?xml version="1.0" encoding="UTF-8"?>'
 '<model unit="millimeter" xml:lang="en-US" '
 'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
 '<metadata name="Title">Anticipy pendant shells - all 4 variants</metadata>'
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

with zipfile.ZipFile("PRINT_ME_anticipy_all8.3mf", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ct)
    z.writestr("_rels/.rels", rels)
    z.writestr("3D/3dmodel.model", model)
print("wrote PRINT_ME_anticipy_all8.3mf")
