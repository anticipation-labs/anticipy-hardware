#!/usr/bin/env python3
"""Phong-shaded orthographic STL renderer — brushed-metal look for the
Anticipy pendant shells. Painter's algorithm, 2-3 directional lights."""
import struct, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def load_stl(path):
    with open(path, "rb") as f:
        f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        tris = np.zeros((n, 3, 3), dtype=np.float64)
        for i in range(n):
            d = f.read(50)
            for k in range(3):
                tris[i, k] = struct.unpack_from("<3f", d, 12 + 12 * k)
    return tris

def rot(tris, rx=0, ry=0, rz=0):
    for ang, axis in ((rz, 2), (ry, 1), (rx, 0)):
        if ang == 0: continue
        a = np.radians(ang); c, s = np.cos(a), np.sin(a)
        if axis == 0: M = np.array([[1,0,0],[0,c,-s],[0,s,c]])
        elif axis == 1: M = np.array([[c,0,s],[0,1,0],[-s,0,c]])
        else: M = np.array([[c,-s,0],[s,c,0],[0,0,1]])
        tris = tris @ M.T
    return tris

BASE = np.array([0.72, 0.72, 0.74])       # brushed steel
def render(ax, tris, alpha=1.0):
    v1 = tris[:,1]-tris[:,0]; v2 = tris[:,2]-tris[:,0]
    nrm = np.cross(v1, v2)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True); ln[ln==0]=1
    nrm = nrm/ln
    # cull backfaces (viewer at +z)
    keep = nrm[:,2] > -0.05
    tris = tris[keep]; nrm = nrm[keep]
    lights = [ (np.array([0.35, 0.5, 0.78]), 0.75),
               (np.array([-0.6, -0.2, 0.45]), 0.30),
               (np.array([0.1, -0.9, 0.2]), 0.18) ]
    col = np.zeros((len(tris),3)) + 0.13
    for L, inten in lights:
        L = L/np.linalg.norm(L)
        diff = np.clip(nrm @ L, 0, 1)[:,None] * BASE * inten
        H = (L + np.array([0,0,1])); H = H/np.linalg.norm(H)
        spec = np.clip(nrm @ H, 0, 1)[:,None]**28 * 0.55 * inten
        col += diff + spec
    col = np.clip(col, 0, 1)
    # depth-based ambient occlusion: near-front recesses (engraving floors,
    # hole interiors) darken so they read like the real thing
    zc = tris[:,:,2].mean(axis=1)
    zmax = zc.max()
    band = 3.0
    rec = np.clip((zmax - zc) / band, 0, 1)
    flatish = nrm[:,2] > 0.55
    ao = np.ones(len(tris))
    ao[flatish] = 1.0 - 0.42 * rec[flatish]
    col = col * ao[:,None]
    order = np.argsort(zc)
    polys = tris[order][:,:,:2]
    ax.add_collection(PolyCollection(polys, facecolors=col[order],
                                     edgecolors=col[order], linewidths=0.35,
                                     alpha=alpha))

def frame(ax, tris_list, pad=4):
    allp = np.concatenate([t.reshape(-1,3) for t in tris_list])
    ax.set_xlim(allp[:,0].min()-pad, allp[:,0].max()+pad)
    ax.set_ylim(allp[:,1].min()-pad, allp[:,1].max()+pad)
    ax.set_aspect("equal"); ax.axis("off")

def scene(views, out, size=(10,10), bg="#101014"):
    fig, axes = plt.subplots(1, len(views), figsize=size)
    if len(views) == 1: axes=[axes]
    fig.patch.set_facecolor(bg)
    for ax, (title, tlist) in zip(axes, views):
        ax.set_facecolor(bg)
        for t in tlist: render(ax, t)
        frame(ax, tlist)
        if title: ax.set_title(title, color="#c8c8cc", fontsize=11, pad=8)
    plt.tight_layout()
    plt.savefig(out, dpi=130, facecolor=bg, bbox_inches="tight")
    plt.close()
    print("wrote", out)

if __name__ == "__main__":
    front = load_stl("stl/anticipy_v1_front.stl")
    back  = load_stl("stl/anticipy_v1_back.stl")
    # assembled pendant: front half at z 0..11.9 as printed; back half was
    # exported flipped, so unflip and place at z<0
    backu = rot(back.copy(), rx=180)                # parting face up at z 0..-11.9
    asm = np.concatenate([front, backu])

    # 1) FRONT view (viewer looks at +z face)
    scene([("", [asm.copy()])], "beauty_front.png", size=(5.4,10))
    # 2) three-quarter
    tq = rot(asm.copy(), rx=-14, ry=24)
    scene([("", [tq])], "beauty_threequarter.png", size=(6.4,10))
    # 3) BACK view (rotate 180 about y) — engraving visible via lighting
    bk = rot(asm.copy(), ry=180)
    scene([("", [bk])], "beauty_back.png", size=(5.4,10))
    # 4) print plate: 8 halves in 2 rows of 4, as printed (z up -> tilt for iso)
    files = [f"stl/anticipy_v{v}_{h}.stl" for v in (1,2,3,4) for h in ("front","back")]
    plate=[]
    for i,fp in enumerate(files):
        t = load_stl(fp)
        cx = (i%4)*34 - 51; cy = (i//4)*70 - 35
        t = t + np.array([cx, cy, 0])
        plate.append(t)
    iso = [rot(np.concatenate(plate), rx=-38, rz=8)]
    scene([("", iso)], "beauty_plate.png", size=(11,8))
