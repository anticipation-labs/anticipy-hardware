#!/usr/bin/env python3
"""Multi-layer maze router for the Anticipy ANT-PROD-R0 EVT board.

Grid A* on F/In2/B with In1 reserved as the ground plane. GND is solved with
planes + stitching (tools/add_zones.py). KiCad DRC is the referee.
Run with KiCad's Python:  python route_board.py
"""
import heapq
import math
from collections import defaultdict

import pcbnew

try:
    import wx
    _a = wx.App(False)
except Exception:
    pass

ROOT = "/Users/omarebrahim/Downloads/Anticipy_PROD_R0_EVT_KiCad"
BOARD_PATH = f"{ROOT}/Anticipy_PROD_R0_EVT.kicad_pcb"

CELL = 0.05
X0, X1 = 19.4, 69.6
Y0, Y1 = 19.4, 40.6
NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1
F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LIDX = {F: 0, IN2: 1, B: 2}
# In2 reserved as GND plane; routed on F and B only
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


def cx(x):
    return int(round((x - X0) / CELL))


def cy(y):
    return int(round((y - Y0) / CELL))


def px(i):
    return X0 + i * CELL


def py(j):
    return Y0 + j * CELL


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


CELL = 0.05  # mm grid
X0, X1 = 19.4, 69.6
Y0, Y1 = 19.4, 40.6
NX = int(round((X1 - X0) / CELL)) + 1
NY = int(round((Y1 - Y0) / CELL)) + 1

F, IN2, B = pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu
LAYERS = [F, IN2, B]
LIDX = {layer: i for i, layer in enumerate(LAYERS)}

TRACK_SIGNAL = 0.20
VIA_PAD = 0.45
VIA_DRILL = 0.20
CLEAR = 0.14
EDGE_CLEAR = 0.45

POWER_W = {
    "VBUS": 0.45, "VBAT": 0.30, "VSYS": 0.45, "3V_MAIN": 0.35,
    "3V_SD": 0.30, "3V_MIC": 0.30, "LDO2_OUT": 0.30, "VBUSOUT": 0.30,
    "HAPTIC_NEG": 0.35, "VSET1": 0.20, "VSET2": 0.20, "NTC": 0.20,
    "SW1": 0.45, "SW2": 0.45, "DCCH": 0.25,
}
VIA_COST = 55.0
VIA_RAD_CELLS = 9  # via keepout radius in cells (0.45 pad + clearance ~ 0.36mm)

board = pcbnew.LoadBoard(BOARD_PATH)


def cx(x):
    return int(round((x - X0) / CELL))


def cy(y):
    return int(round((y - Y0) / CELL))


def px(i):
    return X0 + i * CELL


def py(j):
    return Y0 + j * CELL


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
        pads.append({
            "ref": ref, "num": p.GetNumber(), "net": p.GetNetname(),
            "x": pcbnew.ToMM(pos.x), "y": pcbnew.ToMM(pos.y),
            "hw": hw, "hh": hh, "front": front,
        })

nets = defaultdict(list)
for p in pads:
    if p["net"]:
        nets[p["net"]].append(p)
print(f"pads {len(pads)} nets {len(nets)}", flush=True)

import heapq
import math
from collections import defaultdict

# (pcbnew imports and grid constants are in the head section)

HARD = -1  # cell hard-blocked (other nets never)

# soft-cost state
use_count = None   # dict[(li,i,j)] -> dict[net -> True]
hist = None        # dict[(li,i,j)] -> penalty


def init_soft():
    global use_count, hist, blocked, owner
    use_count = defaultdict(dict)
    hist = defaultdict(float)
    base = bytearray(NX * NY)
    for i in range(NX):
        for j in range(NY):
            if not inside_board(px(i), py(j)) or in_keepout(px(i), py(j)):
                base[i * NY + j] = 1
    blocked = [[bytearray(base[i * NY:(i + 1) * NY]) for i in range(NX)] for _ in range(3)]
    owner = [[dict() for _ in range(NX)] for _ in range(3)]
    # pads: hard own / hard inflate
    for p in pads:
        li = LIDX[F] if p["front"] else LIDX[B]
        for i in range(max(0, cx(p["x"] - p["hw"])), min(NX, cx(p["x"] + p["hw"]) + 1)):
            for j in range(max(0, cy(p["y"] - p["hh"])), min(NY, cy(p["y"] + p["hh"]) + 1)):
                o = owner[li][i].get(j)
                if o is None:
                    owner[li][i][j] = p["net"]
                elif o != p["net"]:
                    owner[li][i][j] = HARD
    for p in pads:
        li = LIDX[F] if p["front"] else LIDX[B]
        hw, hh = p["hw"] + CLEAR, p["hh"] + CLEAR
        for i in range(max(0, cx(p["x"] - hw)), min(NX, cx(p["x"] + hw) + 1)):
            for j in range(max(0, cy(p["y"] - hh)), min(NY, cy(p["y"] + hh) + 1)):
                if owner[li][i].get(j) is None:
                    owner[li][i][j] = p["net"]


def cell_cost(li, i, j, net):
    """Cost of entering a cell for net; None = forbidden."""
    if not (0 <= i < NX and 0 <= j < NY):
        return None
    if blocked[li][i][j]:
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
    total = 0.0
    for li in range(3):
        for di, dj in VIA_DISK:
            c = cell_cost(li, i + di, j + dj, net)
            if c is None:
                return None
            total += 0.0
    # via placement cost: present usage + history of the disk
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
    return 55.0 + total


def astar_path(terms, net, widths):
    """Route one leg between two terminals with soft costs.
    Terminal: ('P', li, i, j) or ('V', i, j)."""
    start, goal = terms
    # state: (li,i,j); for V terminals all three layers available
    def init_states(t):
        if t[0] == "P":
            return [(t[1], t[2], t[3])]
        return [(li, t[1], t[2]) for li in (0, 1, 2)]

    starts, goals = init_states(start), init_states(goal)
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
        if exp > 300000:
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


net_owner_claims = defaultdict(set)  # net -> cells where commit set owner


def commit(net, path, width):
    """Add geometry usage for a routed path (with vias where layer changes)."""
    w = width
    rad = max(4, int((w / 2.0 + CLEAR) / CELL))
    cells = []
    vias = []
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
                o = owner[li][i + di].get(j + dj)
                if o is None:
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
                    for (pi, pj) in placed:
                        if math.hypot(vi - pi, vj - pj) < 12:
                            ok = False
                            break
                    if not ok:
                        continue
                    # escape corridor must be placeable: any cost path
                    steps = max(abs(vi - i0), abs(vj - j0))
                    li = LIDX[F] if p["front"] else LIDX[B]
                    corridor = []
                    fine = True
                    for s in range(steps + 1):
                        ci = int(round(i0 + (vi - i0) * s / steps))
                        cj = int(round(j0 + (vj - j0) * s / steps))
                        if cell_cost(li, ci, cj, p["net"]) is None:
                            fine = False
                            break
                        corridor.append((ci, cj))
                    if not fine:
                        continue
                    escapes[(p["ref"], p["num"])] = (vi, vj)
                    placed.append((vi, vi)) if False else placed.append((vi, vj))
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
    print(f"escape vias: {len(escapes)}", flush=True)


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
            geom[net] = {"cells": [], "vias": []}
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
            path = astar_path((terms[ci], terms[ri]), net, w)
            if path is None:
                ok = False
                break
            c, v = commit(net, path, w)
            cells.extend(c)
            vias.extend(v)
            connected.append(ri)
            remaining.remove(ri)
        geom[net] = {"cells": cells, "vias": vias, "complete": ok}
        if not ok:
            geom[net]["failed_leg"] = True
    return geom


init_soft()
place_escapes()

base_order = sorted([n for n in nets if n != "GND"],
                    key=lambda n: (0 if n not in POWER_W else 1,
                                   math.hypot(max(p["x"] for p in nets[n]) - min(p["x"] for p in nets[n]),
                                              max(p["y"] for p in nets[n]) - min(p["y"] for p in nets[n]))))

geom = {}
order = list(base_order)
for it in range(14):
    if it > 0:
        # remove and re-route nets involved in conflicts (worst first)
        bad = conflicts()
        if not bad:
            break
        reroute = [n for n, _ in sorted(bad.items(), key=lambda kv: -kv[1])]
        for n in reroute:
            remove_net(n)
        order = reroute + [n for n in base_order if n not in reroute]
        for n in list(geom.keys()):
            if n in reroute:
                del geom[n]
    g = route_all([n for n in order if n not in geom])
    geom.update(g)
    bad = conflicts()
    nfail = sum(1 for v in geom.values() if v.get("failed_leg"))
    print(f"== iter {it + 1}: conflicts {sum(len(u) - 1 for u in use_count.values() if len(u) > 1)}, "
          f"nets-in-conflict {len(bad)}, incomplete {nfail}", flush=True)
    if not bad and nfail == 0:
        break
    # bump history on conflicted cells
    for key, u in use_count.items():
        if len(u) > 1:
            hist[key] += 8.0

routes = {}
failed = []
for net, v in geom.items():
    if v.get("failed_leg") or not v["cells"] and len(nets[net]) > 1:
        failed.append(net)
    else:
        routes[net] = v
print(f"final: routed {len(routes)}, failed {len(failed)}: {failed}", flush=True)

layer_kicad = {0: pcbnew.F_Cu, 1: pcbnew.In2_Cu, 2: pcbnew.B_Cu}
for net, v in routes.items():
    nc = board.GetNetcodeFromNetname(net)
    if not nc:
        continue
    w = POWER_W.get(net, TRACK_SIGNAL)
    for (i, j) in v["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(px(i)), pcbnew.FromMM(py(j))))
        via.SetWidth(pcbnew.FromMM(VIA_PAD))
        via.SetDrill(pcbnew.FromMM(VIA_DRILL))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNetCode(nc)
        board.Add(via)
    # group cells by layer and merge collinear runs
    bylayer = {0: [], 1: [], 2: []}
    for (li, i, j) in v["cells"]:
        bylayer[li].append((i, j))
    for li, cells in bylayer.items():
        if not cells:
            continue
        # order cells into chains (they may branch at vias; handle greedily)
        remaining = set(cells)
        while remaining:
            start = next(iter(remaining))
            chain = [start]
            remaining.discard(start)
            # extend forward/backward greedily
            for dirn in (1, -1):
                cur = chain[-1] if dirn == 1 else chain[0]
                while True:
                    nxts = [c for c in remaining
                            if abs(c[0] - cur[0]) + abs(c[1] - cur[1]) == 1]
                    if len(nxts) != 1:
                        break
                    nxt = nxts[0]
                    remaining.discard(nxt)
                    if dirn == 1:
                        chain.append(nxt)
                    else:
                        chain.insert(0, nxt)
                    cur = chain[-1] if dirn == 1 else chain[0]
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
                k = e

pcbnew.SaveBoard(BOARD_PATH, board)
print("board saved", flush=True)
