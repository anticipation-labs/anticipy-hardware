#!/usr/bin/env python3
"""One-shot final build: negotiated routing of all nets, zones, stitching,
via normalization, dedupe — all in ONE process so soft state never desyncs.
Run with KiCad's Python: python final_build.py
"""
import heapq
import json
import math
import os
import sys
from collections import defaultdict

try:
    import wx
    _a = wx.App(False)
except Exception:
    pass

import pcbnew

ROOT = "/Users/omarebrahim/Downloads/Anticipy_PROD_R0_EVT_KiCad"
BOARD_PATH = f"{ROOT}/Anticipy_PROD_R0_EVT.kicad_pcb"

CELL = 0.05
X0, X1 = 19.4, 69.6
Y0, Y1 = 19.4, 40.6
NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LIDX = {F: 0, IN2: 1, B: 2}
TRACK_SIGNAL = 0.20
VIA_PAD = 0.45
VIA_DRILL = 0.20
CLEAR = 0.14
EDGE_CLEAR = 0.45
VIA_RAD_CELLS = 9
POWER_W = {
    "VBUS": 0.45, "VBAT": 0.30, "VSYS": 0.45, "3V_MAIN": 0.35,
    "3V_SD": 0.30, "3V_MIC": 0.30, "LDO2_OUT": 0.30, "VBUSOUT": 0.30,
    "HAPTIC_NEG": 0.35, "VSET1": 0.20, "VSET2": 0.20, "NTC": 0.20,
    "SW1": 0.45, "SW2": 0.45, "DCCH": 0.25,
}
VIA_COST = 55.0
MOVES = ((-1, 0), (1, 0), (0, -1), (0, 1))

board = pcbnew.LoadBoard(BOARD_PATH)


def cx(x): return int(round((x - X0) / CELL))
def cy(y): return int(round((y - Y0) / CELL))
def px(i): return X0 + i * CELL
def py(j): return Y0 + j * CELL


def inside_board(x, y):
    if 30.0 <= x <= 59.0:
        return 20.0 + EDGE_CLEAR <= y <= 40.0 - EDGE_CLEAR
    if x < 30.0:
        dx, dy = x - 30.0, y - 30.0
        return dx * dx + dy * dy <= (10.0 - EDGE_CLEAR) ** 2
    dx, dy = x - 59.0, y - 30.0
    return dx * dx + dy * dy <= (10.0 - EDGE_CLEAR) ** 2


def in_keepout(x, y):
    return x >= 64.85 and 23.6 <= y <= 36.4


pads = []
for fp in board.GetFootprints():
    ref = fp.GetReference()
    front = not fp.IsFlipped()
    rot = fp.GetOrientationDegrees() % 180.0
    swapped = abs(rot - 90.0) < 45.0
    for p in fp.Pads():
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
            continue
        pos = p.GetPosition()
        sx = pcbnew.ToMM(p.GetSize().x) / 2.0
        sy = pcbnew.ToMM(p.GetSize().y) / 2.0
        hw, hh = (sy, sx) if swapped else (sx, sy)
        pads.append({"ref": ref, "num": p.GetNumber(), "net": p.GetNetname(),
                     "x": pcbnew.ToMM(pos.x), "y": pcbnew.ToMM(pos.y),
                     "hw": hw, "hh": hh, "front": front})

nets = defaultdict(list)
for p in pads:
    if p["net"]:
        nets[p["net"]].append(p)
print(f"pads {len(pads)} nets {len(nets)}", flush=True)

blocked = None
owner = None
use_count = defaultdict(dict)
hist = defaultdict(float)
net_owner_claims = defaultdict(set)


def init_soft():
    global blocked, owner
    base = bytearray(NX * NY)
    for i in range(NX):
        for j in range(NY):
            if not inside_board(px(i), py(j)) or in_keepout(px(i), py(j)):
                base[i * NY + j] = 1
    blocked = [[bytearray(base[i * NY:(i + 1) * NY]) for i in range(NX)] for _ in range(3)]
    owner = [[dict() for _ in range(NX)] for _ in range(3)]
    for p in pads:
        li = LIDX[F] if p["front"] else LIDX[B]
        for i in range(max(0, cx(p["x"] - p["hw"])), min(NX, cx(p["x"] + p["hw"]) + 1)):
            for j in range(max(0, cy(p["y"] - p["hh"])), min(NY, cy(p["y"] + p["hh"]) + 1)):
                if owner[li][i].get(j) is None:
                    owner[li][i][j] = p["net"]
    for p in pads:
        li = LIDX[F] if p["front"] else LIDX[B]
        hw, hh = p["hw"] + CLEAR, p["hh"] + CLEAR
        for i in range(max(0, cx(p["x"] - hw)), min(NX, cx(p["x"] + hw) + 1)):
            for j in range(max(0, cy(p["y"] - hh)), min(NY, cy(p["y"] + hh) + 1)):
                if owner[li][i].get(j) is None:
                    owner[li][i][j] = p["net"]


def free(li, i, j, net):
    o = owner[li][i].get(j)
    return o is None or o == net


def cell_cost(li, i, j, net):
    if not (0 <= i < NX and 0 <= j < NY) or blocked[li][i][j]:
        return None
    o = owner[li][i].get(j)
    if o is not None and o != net:
        return None
    c = 1.0 + hist[(li, i, j)]
    u = use_count.get((li, i, j))
    if u:
        for other in u:
            if other != net:
                c += 14.0
                break
    return c


VIA_DISK = [(di, dj) for di in range(-VIA_RAD_CELLS, VIA_RAD_CELLS + 1)
            for dj in range(-VIA_RAD_CELLS, VIA_RAD_CELLS + 1)
            if di * di + dj * dj <= VIA_RAD_CELLS * VIA_RAD_CELLS]


def via_cost_at(net, i, j):
    total = 55.0
    for li in range(3):
        for di, dj in VIA_DISK:
            c = cell_cost(li, i + di, j + dj, net)
            if c is None:
                return None
    for li in range(3):
        for di, dj in VIA_DISK:
            key = (li, i + di, j + dj)
            u = use_count.get(key)
            if u:
                for other in u:
                    if other != net:
                        total += 6.0
                        break
            total += hist[key] * 0.2
    return total


def hwidth(net):
    return POWER_W.get(net, TRACK_SIGNAL) / 2.0 + CLEAR


def astar_path(terms, net):
    start, goal = terms

    def states(t):
        if t[0] == "P":
            return [(t[1], t[2], t[3])]
        return [(li, t[1], t[2]) for li in (0, 1, 2)]

    starts, goals = states(start), states(goal)
    goalset = set(goals)
    pq = []
    parent = {}
    best = {}
    for s in starts:
        c0 = cell_cost(*s, net)
        if c0 is None:
            continue
        g0 = c0
        best[s] = g0
        h0 = min(math.hypot(s[1] - g[1], s[2] - g[2]) for g in goals)
        heapq.heappush(pq, (g0 + h0, g0, s))
    exp = 0
    while pq:
        f, g, node = heapq.heappop(pq)
        if node in goalset:
            path = []
            cur = node
            while cur is not None:
                path.append(cur)
                cur = parent.get(cur)
            return path[::-1]
        if g > best.get(node, 1e18):
            continue
        exp += 1
        if exp > 260000:
            return None
        li, i, j = node
        for di, dj in MOVES:
            ii, jj = i + di, j + dj
            cc = cell_cost(li, ii, jj, net)
            if cc is None:
                continue
            ng = g + cc
            nxt = (li, ii, jj)
            if ng < best.get(nxt, 1e18):
                best[nxt] = ng
                parent[nxt] = node
                hh = min(math.hypot(ii - g[1], jj - g[2]) for g in goals)
                heapq.heappush(pq, (ng + hh, ng, nxt))
        for lli in range(3):
            if lli == li:
                continue
            vc = via_cost_at(net, i, j)
            if vc is None:
                break
            ng = g + vc
            nxt = (lli, i, j)
            if ng < best.get(nxt, 1e18):
                best[nxt] = ng
                parent[nxt] = node
                hh = min(math.hypot(i - g[1], j - g[2]) for g in goals)
                heapq.heappush(pq, (ng + hh, ng, nxt))
    return None


def commit(net, path, width):
    rad = max(4, int((width / 2.0 + CLEAR) / CELL))
    cells, vias = [], []
    for k in range(len(path)):
        li, i, j = path[k]
        cells.append((li, i, j))
        if k + 1 < len(path) and path[k + 1][0] != li:
            vias.append((i, j))
    for (li, i, j) in cells:
        key = (li, i, j)
        use_count[key][net] = True
        if owner[li][i].get(j) is None:
            owner[li][i][j] = net
            net_owner_claims[net].add(key)
    for (i, j) in vias:
        for (di, dj) in VIA_DISK:
            for li in range(3):
                key = (li, i + di, j + dj)
                use_count[key][net] = True
                if owner[li][i + di].get(j + dj) is None:
                    owner[li][i + di][j + dj] = net
                    net_owner_claims[net].add(key)
    return cells, vias


def remove_net(net):
    for key in list(use_count.keys()):
        u = use_count[key]
        if net in u:
            del u[net]
            if not u:
                del use_count[key]
    for key in net_owner_claims.pop(net, set()):
        li, i, j = key
        if owner[li][i].get(j) == net:
            del owner[li][i][j]
            blocked[li][i][j] = 0


def conflicts():
    bad = defaultdict(int)
    for key, u in use_count.items():
        if len(u) > 1:
            for n in u:
                bad[n] += 1
    return bad


ESCAPE_REFS = {"U1", "U2", "J1"}
escapes = {}


def place_escapes():
    escapes.clear()
    by_ref = defaultdict(list)
    for p in pads:
        if p["ref"] in ESCAPE_REFS and p["net"]:
            by_ref[p["ref"]].append(p)
    placed = []
    for ref in ("U2", "U1", "J1"):
        plist = by_ref.get(ref, [])
        if not plist:
            continue
        cxm = sum(p["x"] for p in plist) / len(plist)
        cym = sum(p["y"] for p in plist) / len(plist)
        plist.sort(key=lambda p: (p["y"] if abs(p["x"] - cxm) < abs(p["y"] - cym) else p["x"]))
        for p in plist:
            i0, j0 = cx(p["x"]), cy(p["y"])
            dx, dy = p["x"] - cxm, p["y"] - cym
            n = math.hypot(dx, dy) or 1.0
            ux, uy = dx / n, dy / n
            done = False
            for dist in (16, 20, 24, 28, 32, 38, 44, 50):
                for lat in (0, 5, -5, 9, -9, 13, -13):
                    vi = int(round(i0 + ux * dist - uy * lat))
                    vj = int(round(j0 + uy * dist + ux * lat))
                    if not (0 <= vi < NX and 0 <= vj < NY):
                        continue
                    if not inside_board(px(vi), py(vj)) or in_keepout(px(vi), py(vj)):
                        continue
                    ok = True
                    for (pi2, pj2) in placed:
                        if math.hypot(vi - pi2, vj - pj2) < 12:
                            ok = False
                            break
                    if not ok:
                        continue
                    steps = max(abs(vi - i0), abs(vj - j0))
                    corridor = []
                    fine = True
                    for s in range(steps + 1):
                        ci = int(round(i0 + (vi - i0) * s / steps))
                        cj = int(round(j0 + (vj - j0) * s / steps))
                        if cell_cost(li := (LIDX[F] if p["front"] else LIDX[B]), ci, cj, p["net"]) is None:
                            fine = False
                            break
                        corridor.append((ci, cj))
                    if not fine:
                        continue
                    li = LIDX[F] if p["front"] else LIDX[B]
                    escapes[(p["ref"], p["num"])] = (vi, vj)
                    placed.append((vi, vj))
                    for (ci, cj) in corridor:
                        key = (li, ci, cj)
                        use_count[key][p["net"]] = True
                        if owner[li][ci].get(cj) is None:
                            owner[li][ci][cj] = p["net"]
                    for (di, dj) in VIA_DISK:
                        for lli in range(3):
                            key = (lli, vi + di, vj + dj)
                            use_count[key][p["net"]] = True
                            if owner[lli][vi + di].get(vj + dj) is None:
                                owner[lli][vi + di][vj + dj] = p["net"]
                    done = True
                    break
                if done:
                    break
    print(f"escapes: {len(escapes)}", flush=True)


def terminal_of(p):
    key = (p["ref"], p["num"])
    if key in escapes:
        return ("V", escapes[key][0], escapes[key][1])
    li = LIDX[F] if p["front"] else LIDX[B]
    return ("P", li, cx(p["x"]), cy(p["y"]))


def route_all(order):
    geom = {}
    for net in order:
        plist = sorted(nets[net], key=lambda q: (q["x"], q["y"]))
        terms = [terminal_of(p) for p in plist]
        w = POWER_W.get(net, TRACK_SIGNAL)
        if len(terms) < 2:
            geom[net] = {"cells": [], "vias": [], "complete": True}
            continue
        remaining = list(range(len(terms)))
        connected = [remaining.pop(0)]
        cells, vias = [], []
        ok = True
        while remaining:
            best = None
            for ci in connected:
                for ri in remaining:
                    d = math.hypot(terms[ci][-2] - terms[ri][-2], terms[ci][-1] - terms[ri][-1])
                    if best is None or d < best[0]:
                        best = (d, ci, ri)
            _, ci, ri = best
            path = astar_path((terms[ci], terms[ri]), net)
            if path is None:
                ok = False
                break
            c, v = commit(net, path, w)
            cells.extend(c)
            vias.extend(v)
            connected.append(ri)
            remaining.remove(ri)
        geom[net] = {"cells": cells, "vias": vias, "complete": ok}
        print(("OK  " if ok else "FAIL ") + net, flush=True)
    return geom


# ============ PHASE 1: negotiate all nets ============
init_soft()
place_escapes()

base_order = sorted([n for n in nets if n != "GND"],
                    key=lambda n: (0 if n not in POWER_W else 1,
                                   math.hypot(max(p["x"] for p in nets[n]) - min(p["x"] for p in nets[n]),
                                              max(p["y"] for p in nets[n]) - min(p["y"] for p in nets[n]))))
geom = {}
order = list(base_order)
best = None
for it in range(12):
    for net in order:
        if net in geom:
            remove_net(net)
    g = route_all(order)
    geom.update(g)
    bad = conflicts()
    bad_total = sum(len(u) - 1 for u in use_count.values() if len(u) > 1)
    incomplete = [n for n, v in geom.items() if not v.get("complete")]
    print(f"== pass {it + 1}: conflict-nets {len(bad)}, incomplete {len(incomplete)}: {incomplete}", flush=True)
    score = len(bad) + len(incomplete)
    if best is None or score < best[0]:
        best = (score, json.loads(json.dumps({k: v for k, v in geom.items()})))
    if score == 0:
        break
    for key, u in use_count.items():
        if len(u) > 1:
            hist[key] += 8.0
    order = incomplete + [n for n, _ in sorted(bad.items(), key=lambda kv: -kv[1])] + base_order
    # dedupe keep order
    seen = set()
    order = [n for n in order if not (n in seen or seen.add(n))]

# restore best geometry state
geom = best[1]
print(f"best score {best[0]}", flush=True)

# ============ PHASE 2: gap-fill incomplete nets from clean state ============
for attempt in range(3):
    incomplete = [n for n, v in geom.items() if not v.get("complete")]
    if not incomplete:
        break
    print(f"== gap-fill {attempt + 1}: {incomplete}", flush=True)
    for net in incomplete:
        remove_net(net)
    hist.clear()
    # route incomplete first, then let neighbors yield (soft costs)
    g = route_all(incomplete + [n for n in base_order if n not in incomplete and n in geom])
    geom.update(g)

# ============ PHASE 3: write geometry ============
layer_kicad = {0: F, 1: IN2, 2: B}
nc_map = {}
for net in nets:
    nc_map[net] = board.GetNetcodeFromNetname(net)

track_count = 0
via_count = 0
for net, v in geom.items():
    nc = nc_map.get(net)
    if not nc:
        continue
    w = POWER_W.get(net, TRACK_SIGNAL)
    for (i, j) in v["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px(i)), pcbnew.FromMM(py(j))))
        via.SetWidth(pcbnew.FromMM(VIA_PAD))
        via.SetDrill(pcbnew.FromMM(VIA_DRILL))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(F, B)
        via.SetNetCode(nc)
        board.Add(via)
        via_count += 1
    bylayer = {0: [], 1: [], 2: []}
    for c in v["cells"]:
        bylayer[c[0]].append((c[1], c[2]))
    for li, cells in bylayer.items():
        if not cells:
            continue
        from collections import defaultdict as dd
        deg = dd(list)
        cset = set(cells)
        for (i, j) in cells:
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (i + di, j + dj)
                if n in cset:
                    deg[(i, j)].append(n)
        visited = set()
        chains = []
        for e in [c for c in cells if len(deg[c]) == 1]:
            if e in visited:
                continue
            chain = [e]
            visited.add(e)
            cur = e
            prev = None
            while True:
                nbrs = [n for n in deg[cur] if n != prev and n not in visited]
                if not nbrs:
                    break
                nxt = nbrs[0]
                visited.add(nxt)
                chain.append(nxt)
                prev, cur = cur, nxt
            if len(chain) > 1:
                chains.append(chain)
        for c in cells:
            if c not in visited:
                chain = [c]
                visited.add(c)
                cur = c
                prev = None
                while True:
                    nbrs = [n for n in deg[cur] if n != prev and n not in visited]
                    if not nbrs:
                        break
                    nxt = nbrs[0]
                    visited.add(nxt)
                    chain.append(nxt)
                    prev, cur = cur, nxt
                if len(chain) > 1:
                    chains.append(chain)
        for chain in chains:
            k = 0
            while k < len(chain) - 1:
                i, j = chain[k]
                di, dj = chain[k + 1][0] - i, chain[k + 1][1] - j
                e = k + 1
                while e + 1 < len(chain):
                    d2 = (chain[e + 1][0] - chain[e][0], chain[e + 1][1] - chain[e][1])
                    if d2 != (di, dj):
                        break
                    e += 1
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(px(chain[k][0])), pcbnew.FromMM(py(chain[k][1]))))
                t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(px(chain[e][0])), pcbnew.FromMM(py(chain[e][1]))))
                t.SetWidth(pcbnew.FromMM(w))
                t.SetLayer(layer_kicad[li])
                t.SetNetCode(nc)
                board.Add(t)
                track_count += 1
                k = e
print(f"written: {track_count} tracks, {via_count} vias", flush=True)

# ============ PHASE 4: GND plane on In1 + pours F/B + GND via-in-pad ============
gnd_nc = board.GetNetcodeFromNetname("GND")
import math as _m
capsule = []
for i in range(17):
    ang = _m.radians(-90 + i * 180 / 16)
    capsule.append((59.0 + 10.0 * _m.cos(ang), 30.0 + 10.0 * _m.sin(ang)))
for i in range(17):
    ang = _m.radians(90 + i * 180 / 16)
    capsule.append((30.0 + 10.0 * _m.cos(ang), 30.0 + 10.0 * _m.sin(ang)))

for li_name, li_id in (("In1.Cu", pcbnew.In1_Cu), ("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu)):
    zone = pcbnew.ZONE(board)
    zone.SetNetCode(gnd_nc)
    zone.SetLayer(li_id)
    zone.SetLocalClearance(pcbnew.FromMM(0.2))
    try:
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_MODE.SOLID if li_name == "In1.Cu" else pcbnew.ZONE_CONNECTION_MODE.THERMAL)
    except Exception:
        pass
    out = zone.Outline()
    out.NewOutline()
    for (x, y) in capsule:
        out.Append(pcbnew.FromMM(x), pcbnew.FromMM(y))
    zone.SetIsFilled(False)
    board.Add(zone)
print("zones added", flush=True)

# GND via-in-pad: every GND pad gets a via at its center (connects to plane)
gnd_vias = 0
for p in pads:
    if p["net"] != "GND":
        continue
    via = pcbnew.PCB_VIA(board)
    via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(p["x"]), pcbnew.FromMM(p["y"])))
    via.SetWidth(pcbnew.FromMM(VIA_PAD))
    via.SetDrill(pcbnew.FromMM(VIA_DRILL))
    via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetLayerPair(F, B)
    via.SetNetCode(gnd_nc)
    board.Add(via)
    gnd_vias += 1
print(f"GND stitch vias: {gnd_vias}", flush=True)

# ============ PHASE 5: fill zones ============
try:
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print("zones filled", flush=True)
except Exception as e:
    print("zone fill error:", e, flush=True)

pcbnew.SaveBoard(BOARD_PATH, board)
print("SAVED", flush=True)

# save route data for reference
json.dump({k: {"cells": [list(c) for c in v["cells"]], "vias": v["vias"], "complete": v.get("complete")}
           for k, v in geom.items()}, open(f"{ROOT}/tools/final_routes.json", "w"))
print("BUILD DONE", flush=True)
