"""Route the Rev0.6 board from the routing document (issue #6 P4; CLAUDE.md 5.1, 5.3, 5.4).

A library, not a script. make_pcb.py owns the board file and calls it after placing the parts;
autoroute.py calls it to build Freerouting's input. Both parse the documents with
make_pcb.doc_tables and hand this module the tables.

The routed board is built in this order (design/ecad/ROUTING_Rev0.6.md):
1. `plane()`: In1.Cu becomes a plane layer holding the document's In1 zone (GND).
2. `apply_rows()`: the hand-drawn tracks and vias of the `route` table and, for both channels,
   the `channel_route` table; channel B is channel A moved by dx, with the placement's
   Ref A -> Ref B map and `_A` -> `_B` in the net names.
3. `gnd_fanout()`: every GND SMD pad gets a short stub and a via to the plane, and each exposed
   pad of the `epad` table a pattern of vias.
4. `import_session()`: the committed Freerouting session (routing/usb-power-hub.ses): the
   tracks and vias the router added. `export_dsn()` writes the router's input from the board of
   steps 1-3 with the document's classes and keepouts; its SHA-256 is recorded next to the
   session, so a session made from another input is refused.
5. `pours()`: the remaining zones, then every zone is filled.
"""
import hashlib
import math
import re

import pcbnew

ORIGIN = (50.0, 122.0)            # the board's lower-left corner on the sheet (make_project.py)
LAYERS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
PAD_RE = re.compile(r"([A-Z]+\d+)\.(\w+)$")
mm = pcbnew.FromMM


def to_sheet(x, y):
    return pcbnew.VECTOR2I(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))


def to_frame(vec):
    return pcbnew.ToMM(vec.x) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(vec.y)


# ---- the routing document ------------------------------------------------------------------
def _num(text, what):
    try:
        return float(text)
    except ValueError:
        raise SystemExit(f"{what}: {text!r} is not a number") from None


def _row(r, kind):
    net, layer, width, pts = r["Net"], r["Layer"], r["Width"], r["Points"].split()
    if layer == "remove":
        if kind != "patch" or not pts:
            raise SystemExit(f"{kind}: a remove row belongs to the patch table and takes points: {r}")
        return dict(net=net, layer=layer, points=pts, why=r.get("Why", ""))
    if layer == "via":
        if len(pts) != 1:
            raise SystemExit(f"{kind}: a via row takes one point: {r}")
        d, drill = (_num(v, f"{kind} {net} via") for v in width.split("/"))
        return dict(net=net, layer=layer, via=(d, drill), points=pts, why=r.get("Why", ""))
    if layer not in LAYERS or layer == "In1.Cu":
        raise SystemExit(f"{kind}: {net} on {layer!r}; tracks go on F.Cu, In2.Cu or B.Cu")
    if len(pts) < 2:
        raise SystemExit(f"{kind}: a track row takes two points or more: {r}")
    return dict(net=net, layer=layer, width=_num(width, f"{kind} {net} width"), points=pts,
                why=r.get("Why", ""))


def channel_b(row, refs, dx):
    """Channel A's row moved to channel B: x + dx, Ref A -> Ref B, net _A -> _B."""
    if not row["net"].endswith("_A"):
        raise SystemExit(f"channel_route: net {row['net']} is not a channel-A net (_A)")
    pts = []
    for p in row["points"]:
        m = PAD_RE.match(p)
        if m:
            if m.group(1) not in refs:
                raise SystemExit(f"channel_route: {m.group(1)} has no channel-B part")
            pts.append(f"{refs[m.group(1)]}.{m.group(2)}")
        else:
            x, y = p.split(",")
            pts.append(f"{round(_num(x, 'x') + dx, 4)},{y}")
    return dict(row, net=row["net"][:-2] + "_B", points=pts)


def read(tables, refs, dx):
    """The routing document's tables -> {zones, pairs, rows, classes, keepouts, epads}.

    tables: make_pcb.doc_tables of ROUTING_Rev0.6.md; refs: the placement's Ref A -> Ref B
    (J2 -> J3 among them); dx: the placement's channel offset.
    """
    need = ("zones", "pairs", "route", "channel_route", "epad", "classes", "keepouts", "router_layers",
            "router_costs")
    missing = [k for k in need if k not in tables]
    if missing:
        raise SystemExit(f"ROUTING: no table {', '.join(missing)}")
    rows = [_row(r, "route") for r in tables["route"][1]]
    patch = [_row(r, "patch") for r in tables["patch"][1]] if "patch" in tables else []
    chan = [_row(r, "channel_route") for r in tables["channel_route"][1]]
    rows += chan + [channel_b(r, refs, dx) for r in chan]
    zones = []
    for z in tables["zones"][1]:
        zones.append(dict(name=z["Zone"], net=z["Net"], layer=z["Layer"], stage=z["Stage"],
                          clearance=_num(z["Clearance"], z["Zone"]), min_width=_num(z["Min width"], z["Zone"]),
                          pads=z["Pads"], priority=int(z["Priority"])))
    pairs = []
    for p in tables["pairs"][1]:
        pts = [tuple(_num(v, p["Pair"]) for v in t.split(",")) for t in p["Centreline"].split()]
        pairs.append(dict(name=p["Pair"], nets=(p["P"], p["N"]), centreline=pts))
    classes = []
    for c in tables["classes"][1]:
        via = tuple(_num(v, c["Class"]) for v in c["Via"].split("/")) if c["Via"] != "-" else None
        layers = None if c["Layers"] == "all" else c["Layers"].split(",")
        for layer in layers or ():
            if layer not in LAYERS or layer == "In1.Cu":
                raise SystemExit(f"class {c['Class']}: layer {layer!r}")
        classes.append(dict(name=c["Class"], nets=c["Nets"].split(), width=_num(c["Width"], c["Class"]),
                            clearance=_num(c["Clearance"], c["Class"]), via=via, layers=layers))
    analog = tables["keepouts"][0].get("analog", "").split(",")
    if analog == [""]:
        raise SystemExit("ROUTING: the keepouts table names no analog blocks (analog=...)")
    if "plane_via" not in tables["keepouts"][0]:
        raise SystemExit("ROUTING: the keepouts table does not say how much larger a via is on In1.Cu"
                         " for the router (plane_via=<mm>)")
    plane_via = _num(tables["keepouts"][0]["plane_via"], "plane_via")
    keepouts = []
    for k in tables["keepouts"][1]:
        keepouts.append(dict(name=k["Keepout"], layers=k["Layers"].split(","), kind=k["Kind"],
                             around=k["Around"].split(), buffer=k["Buffer"]))
    epads = {e["Pad"]: _num(e["Offset"], e["Pad"]) for e in tables["epad"][1]}
    router_layers = []
    for x in tables["router_layers"][1]:
        if x["Layer"] not in LAYERS or x["Layer"] == "In1.Cu" or x["Direction"] not in ("horizontal", "vertical"):
            raise SystemExit(f"router_layers: {x['Layer']} {x['Direction']}")
        router_layers.append(dict(layer=x["Layer"], direction=x["Direction"], against=_num(x["Against"], x["Layer"])))
    router_costs = []
    for x in tables["router_costs"][1]:
        if x["Setting"] not in ("via_costs", "plane_via_costs", "start_ripup_costs") or not x["Value"].isdigit():
            raise SystemExit(f"router_costs: {x['Setting']} {x['Value']}")
        router_costs.append((x["Setting"], int(x["Value"])))
    return dict(zones=zones, pairs=pairs, rows=rows, classes=classes, keepouts=keepouts, epads=epads,
                analog=analog, plane_via=plane_via, router_layers=router_layers, router_costs=router_costs,
                patch=patch)


# ---- board items ---------------------------------------------------------------------------
def pad_position(board, token, net):
    ref, num = PAD_RE.match(token).groups()
    fp = board.FindFootprintByReference(ref)
    if fp is None:
        raise SystemExit(f"route: no part {ref}")
    pads = [p for p in fp.Pads() if p.GetNumber() == num]
    if len(pads) != 1:
        raise SystemExit(f"route: {token} names {len(pads)} pads")
    if pads[0].GetNetname() != net:
        raise SystemExit(f"route: {token} is on {pads[0].GetNetname()}, not {net}")
    return pads[0].GetPosition()


def _point(board, token, net):
    if PAD_RE.match(token):
        return pad_position(board, token, net)
    x, y = token.split(",")
    return to_sheet(_num(x, "x"), _num(y, "y"))


def add_via(board, net, at, d, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(at)
    v.SetWidth(mm(d))
    v.SetDrill(mm(drill))
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(net)
    board.Add(v)
    return v


def add_track(board, net, a, b, width, layer):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(a)
    t.SetEnd(b)
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def apply_patch(board, rows):
    """The patch table, after the session: at each point of a remove row, the via of its net
    centred exactly there is deleted, or else every track of its net through the point (and it
    fails if there is neither: the patch was written for another session); then the other rows
    are drawn like the route table's. Returns (tracks, vias, removed)."""
    removed = 0
    for r in (r for r in rows if r["layer"] == "remove"):
        for p in r["points"]:
            at = to_sheet(*(_num(v, f"patch {r['net']}") for v in p.split(",")))
            own = [t for t in board.GetTracks() if t.GetNetname() == r["net"]]
            hit = [t for t in own if t.GetClass() == "PCB_VIA" and t.GetPosition() == at] or \
                [t for t in own if t.GetClass() != "PCB_VIA" and t.HitTest(at, 0)]
            if not hit:
                raise SystemExit(f"patch: no {r['net']} track or via at {p}: the patch was written for another session")
            for t in hit:
                board.Remove(t)
            removed += len(hit)
    n_t, n_v = apply_rows(board, [r for r in rows if r["layer"] != "remove"])
    return n_t, n_v, removed


def apply_rows(board, rows):
    n_t = n_v = 0
    for r in rows:
        net = board.FindNet(r["net"])
        if net is None:
            raise SystemExit(f"route: no net {r['net']}")
        pts = [_point(board, p, r["net"]) for p in r["points"]]
        if r["layer"] == "via":
            add_via(board, net, pts[0], *r["via"])
            n_v += 1
            continue
        for a, b in zip(pts, pts[1:]):
            add_track(board, net, a, b, r["width"], LAYERS[r["layer"]])
            n_t += 1
    return n_t, n_v


def _zone(board, z, outline):
    zone = pcbnew.ZONE(board)
    zone.SetLayer(LAYERS[z["layer"]])
    net = board.FindNet(z["net"])
    if net is None:
        raise SystemExit(f"zone {z['name']}: no net {z['net']}")
    zone.SetNet(net)
    o = zone.Outline()
    o.NewOutline()
    for x, y in outline:
        o.Append(mm(ORIGIN[0] + x), mm(ORIGIN[1] - y))
    zone.SetLocalClearance(mm(z["clearance"]))
    zone.SetMinThickness(mm(z["min_width"]))
    zone.SetPadConnection({"solid": pcbnew.ZONE_CONNECTION_FULL,
                           "thermal": pcbnew.ZONE_CONNECTION_THERMAL}[z["pads"]])
    zone.SetAssignedPriority(z["priority"])
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    zone.SetZoneName(z["name"])
    board.Add(zone)
    return zone


def board_outline(size, inset):
    """The outline (board frame; size = make_project.SIZE_MM) moved in by inset."""
    w, h = size
    return [(inset, inset), (w - inset, inset), (w - inset, h - inset), (inset, h - inset)]


EDGE = 0.30                        # copper to the routed edge (make_project.py RULES)


def plane(board, zones, size):
    """In1.Cu becomes a plane layer with the document's plane-stage zones (board-wide)."""
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    for z in zones:
        if z["stage"] == "plane":
            _zone(board, z, board_outline(size, EDGE))


def pours(board, zones, size):
    """The document's pour-stage zones (board-wide), then every zone filled."""
    for z in zones:
        if z["stage"] == "pour":
            _zone(board, z, board_outline(size, EDGE))
    fill(board)


def fill(board):
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


# ---- GND fanout ----------------------------------------------------------------------------
# The fanout's via is the board's Default class via (board_via). The hole-to-hole spacing it keeps
# is make_project.py's, which make_pcb.py passes in: VIA_HOLE_TO_HOLE (JLCPCB's via figure, a
# custom rule) to another via, the board's min_hole_to_hole to a pad's hole.
FAN_STUB = 0.20
FAN_CLR = 0.15
FAN_HS_CLR = 0.50                  # the HS pairs keep 0.5 mm of coplanar clearance
FAN_GRID = 2.0
FAN_STEPS = 14                     # candidate rings 0.1 mm apart
FAN_DIRECTIONS = 16


class _Copper:
    """The board's copper items, bucketed on a grid: (net, item, frame box, hole or None). A hole
    is (x, y, radius): a pad's from its position and the drill's width, so an oblong hole, a
    plated slot, is read as a round one at its centre. That put the GND fanout via of 8
    receptacle contact pads 0.046 mm from a slot's hole (issue #8); ROUTING_Rev0.6.md's patch,
    stage 5, deletes them, because the committed session was routed around them, and
    check_routing.py rule 10 measures the slot as a capsule. Read it as a capsule here before the
    next session is routed."""

    def __init__(self, board):
        self.items, self.grid = [], {}
        for f in board.GetFootprints():
            for p in f.Pads():
                hole = None
                if p.GetDrillSize().x > 0:
                    hole = (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y),
                            pcbnew.ToMM(p.GetDrillSize().x) / 2)
                self.add(p, hole)
        for t in board.GetTracks():
            hole = None
            if t.GetClass() == "PCB_VIA":
                hole = (pcbnew.ToMM(t.GetPosition().x), pcbnew.ToMM(t.GetPosition().y),
                        pcbnew.ToMM(t.GetDrillValue()) / 2)
            self.add(t, hole)

    def add(self, item, hole):
        bb = item.GetBoundingBox()
        box = tuple(pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))
        k = len(self.items)
        self.items.append((item.GetNetname(), item, box, hole))
        for gx in range(int(box[0] // FAN_GRID), int(box[2] // FAN_GRID) + 1):
            for gy in range(int(box[1] // FAN_GRID), int(box[3] // FAN_GRID) + 1):
                self.grid.setdefault((gx, gy), []).append(k)

    def near(self, box):
        seen = set()
        for gx in range(int(box[0] // FAN_GRID), int(box[2] // FAN_GRID) + 1):
            for gy in range(int(box[1] // FAN_GRID), int(box[3] // FAN_GRID) + 1):
                for k in self.grid.get((gx, gy), ()):
                    if k not in seen:
                        seen.add(k)
                        yield self.items[k]


def board_via(board):
    """(diameter, drill) in mm: the Default class's via, from the project make_project.py writes."""
    nc = board.GetDesignSettings().m_NetSettings.GetDefaultNetclass()
    return pcbnew.ToMM(nc.GetViaDiameter()), pcbnew.ToMM(nc.GetViaDrill())


def _clear(cu, net, shape, box, layers, hs, hole=None, hole_clr=None):
    """hole_clr: (to a via's hole, to a pad's hole) in mm, for a via at `hole`."""
    for inet, item, ibox, ihole in cu.near(box):
        if ibox[0] > box[2] or ibox[2] < box[0] or ibox[1] > box[3] or ibox[3] < box[1]:
            continue
        if hole and ihole and math.hypot(ihole[0] - hole[0], ihole[1] - hole[1]) < \
                ihole[2] + hole[2] + hole_clr[item.GetClass() != "PCB_VIA"] + 0.01:
            return False
        if inet == net:
            continue
        clr = FAN_HS_CLR if inet in hs else FAN_CLR
        for layer in layers:
            if item.IsOnLayer(layer) and item.GetEffectiveShape(layer).Collide(shape, mm(clr + 0.01)):
                return False
    return True


def gnd_fanout(board, epads, hs_nets, hole_clr):
    """GND vias: each exposed pad of `epads` gets a centre via and four at the offset; every
    other GND surface pad (SMD, or a connector pad without paste such as J5's) gets the board's
    via (board_via) on the nearest free spot of 16 directions, outward
    first, and a 0.2 mm stub to it. hole_clr = (to a via's hole, to a pad's hole) in mm, the
    hole-to-hole spacing it keeps. Returns (vias, pads left without one)."""
    fan_via = board_via(board)
    gnd = board.FindNet("GND")
    cu = _Copper(board)
    x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (board.GetBoardEdgesBoundingBox().GetLeft(),
                                                board.GetBoardEdgesBoundingBox().GetTop(),
                                                board.GetBoardEdgesBoundingBox().GetRight(),
                                                board.GetBoardEdgesBoundingBox().GetBottom()))
    all_layers = list(LAYERS.values())
    n, failed = 0, []
    pads = []
    for f in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        for p in sorted(f.Pads(), key=lambda p: p.GetNumber()):
            key = f"{f.GetReference()}.{p.GetNumber()}"
            if key in epads:
                if p.GetNetname() != "GND":
                    raise SystemExit(f"epad {key} is on {p.GetNetname()}, not GND")
                c, off = p.GetPosition(), mm(epads[key])
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    v = add_via(board, gnd, pcbnew.VECTOR2I(c.x + dx * off, c.y + dy * off), *fan_via)
                    cu.add(v, (pcbnew.ToMM(v.GetPosition().x), pcbnew.ToMM(v.GetPosition().y), fan_via[1] / 2))
                    n += 1
            elif p.GetNetname() == "GND" and p.GetAttribute() in (pcbnew.PAD_ATTRIB_SMD, pcbnew.PAD_ATTRIB_CONN):
                pads.append((key, p))
    r = fan_via[0] / 2
    for key, p in pads:
        cx, cy = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
        fp = p.GetParentFootprint()
        fx, fy = pcbnew.ToMM(fp.GetPosition().x), pcbnew.ToMM(fp.GetPosition().y)
        bb = p.GetBoundingBox()
        hx, hy = pcbnew.ToMM(bb.GetWidth()) / 2, pcbnew.ToMM(bb.GetHeight()) / 2
        out = math.atan2(cy - fy, cx - fx) if (cx, cy) != (fx, fy) else 0.0
        dirs = sorted((k * 2 * math.pi / FAN_DIRECTIONS for k in range(FAN_DIRECTIONS)),
                      key=lambda a: abs(math.remainder(a - out, 2 * math.pi)))
        cands = []
        for step in range(FAN_STEPS):
            for a in dirs:
                ux, uy = math.cos(a), math.sin(a)
                edge = min(hx / abs(ux) if abs(ux) > 1e-9 else 1e9, hy / abs(uy) if abs(uy) > 1e-9 else 1e9)
                d = edge + 0.10 + r + 0.1 * step
                cands.append((d, cx + ux * d, cy + uy * d))
        cands.sort(key=lambda t: t[0])
        for _, x, y in cands:
            if not (x0 + r + EDGE <= x <= x1 - r - EDGE and y0 + r + EDGE <= y <= y1 - r - EDGE):
                continue
            circ = pcbnew.SHAPE_CIRCLE(pcbnew.VECTOR2I(mm(x), mm(y)), mm(r))
            box = (x - r - 1, y - r - 1, x + r + 1, y + r + 1)
            if not _clear(cu, "GND", circ, box, all_layers, hs_nets, (x, y, fan_via[1] / 2), hole_clr):
                continue
            seg = pcbnew.SHAPE_SEGMENT(pcbnew.VECTOR2I(mm(cx), mm(cy)), pcbnew.VECTOR2I(mm(x), mm(y)), mm(FAN_STUB))
            sbox = (min(cx, x) - 1, min(cy, y) - 1, max(cx, x) + 1, max(cy, y) + 1)
            if not _clear(cu, "GND", seg, sbox, [pcbnew.F_Cu], hs_nets):
                continue
            v = add_via(board, gnd, pcbnew.VECTOR2I(mm(x), mm(y)), *fan_via)
            cu.add(v, (x, y, fan_via[1] / 2))
            t = add_track(board, gnd, pcbnew.VECTOR2I(mm(cx), mm(cy)), pcbnew.VECTOR2I(mm(x), mm(y)),
                          FAN_STUB, pcbnew.F_Cu)
            cu.add(t, None)
            n += 1
            break
        else:
            failed.append(key)
    return n, failed


# ---- Freerouting ---------------------------------------------------------------------------
def _rects(poly, buf):
    out = []
    for (xa, ya), (xb, yb) in zip(poly, poly[1:]):
        ln = math.hypot(xb - xa, yb - ya)
        if ln == 0:
            continue
        ux, uy = (xb - xa) / ln, (yb - ya) / ln
        nx, ny = -uy, ux
        a, b = (xa - ux * buf, ya - uy * buf), (xb + ux * buf, yb + uy * buf)
        out.append([(a[0] + nx * buf, a[1] + ny * buf), (b[0] + nx * buf, b[1] + ny * buf),
                    (b[0] - nx * buf, b[1] - ny * buf), (a[0] - nx * buf, a[1] - ny * buf)])
    return out


def _poly_set(polys):
    s = pcbnew.SHAPE_POLY_SET()
    for poly in polys:
        s.NewOutline()
        for x, y in poly:
            s.Append(mm(x), mm(y))
    return s


def _clip(polys, boxes):
    """The parts of polys inside the (x, y, w, h) boxes, as polygons (board frame)."""
    a = _poly_set(polys)
    a.Simplify()
    b = _poly_set([[(x, y), (x + w, y), (x + w, y + h), (x, y + h)] for x, y, w, h in boxes])
    b.Simplify()
    a.BooleanIntersection(b)
    out = []
    for i in range(a.OutlineCount()):
        o = a.Outline(i)
        out.append([(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())])
    return out


def _row_points(row, pad_frame):
    return [pad_frame(t, row["net"]) if PAD_RE.match(t) else tuple(map(float, t.split(",")))
            for t in row["points"]]


def _buffer_mm(k, base="w/2"):
    """The mm of a keepout's `w/2+<mm>` buffer, the distance beyond the half-width of each track,
    or of its `pad+<mm>` buffer, the distance beyond a drilled pad's copper and hole."""
    m = re.fullmatch(re.escape(base) + r"\+([\d.]+)", k["buffer"])
    if not m:
        raise SystemExit(f"keepout {k['name']}: buffer {k['buffer']!r}, want {base}+<mm>")
    return float(m.group(1))


def drilled_boxes(board):
    """(x0, y0, x1, y1), board frame, of every drilled pad that is not on GND: its copper and its
    hole. On the plane each of them stands in a void; a GND pad stands in the copper."""
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x <= 0 or p.GetNetname() == "GND":
                continue
            bb = p.GetBoundingBox()
            c, d = p.GetPosition(), p.GetDrillSize()
            xs = [bb.GetLeft(), bb.GetRight(), c.x - d.x // 2, c.x + d.x // 2]
            ys = [bb.GetTop(), bb.GetBottom(), c.y - d.y // 2, c.y + d.y // 2]
            (xa, ya), (xb, yb) = to_frame(pcbnew.VECTOR2I(min(xs), min(ys))), to_frame(pcbnew.VECTOR2I(max(xs), max(ys)))
            out.append((min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)))
    return sorted(out)


def _within(k, routing, regions):
    """The (x, y, w, h) boxes of the placement regions after `in` in the keepout's Around cell
    (`analog`: the keepouts table's analog blocks), or None when the cell has no `in`."""
    tail = k["around"][1:]
    if not tail:
        return None
    names = routing["analog"] if tail[1:] == ["analog"] else tail[1:]
    if tail[0] != "in" or not names:
        raise SystemExit(f"keepout {k['name']}: want '{k['around'][0]}' or '{k['around'][0]} in REGION ...'")
    for name in names:
        if name not in regions:
            raise SystemExit(f"keepout {k['name']}: no placement region {name}")
    return [regions[n] for n in names]


def keepout_polygons(routing, regions, pad_frame, drilled=()):
    """[(layer, kind, polygon)] in the board frame, from the document's keepout rules.

    regions: {name: (x, y, w, h)} of the placement; pad_frame(token, net) -> (x, y) for pad
    points of the B.Cu rows and of the pairs' leads; drilled: drilled_boxes of the board."""
    out = []
    for k in routing["keepouts"]:
        polys = []
        head = k["around"][0]
        if head == "drilled-pads":
            # around every drilled pad that is not on GND, `pad+<mm>` beyond its copper and hole
            buf = _buffer_mm(k, "pad")
            if len(k["around"]) != 1 or not drilled:
                raise SystemExit(f"keepout {k['name']}: want 'drilled-pads' alone, and a board with drilled pads")
            polys = [[(x0 - buf, y0 - buf), (x1 + buf, y0 - buf), (x1 + buf, y1 + buf), (x0 - buf, y1 + buf)]
                     for x0, y0, x1, y1 in drilled]
        elif head == "box":
            # "box X0,Y0,X1,Y1": that rectangle of the board frame, as it is written.
            # "box X0,Y0,X1,Y1 open X,Y ...": the rectangle less a square window of side `buffer`
            # centred on each X,Y, as rectangles (a DSN keepout has no hole)
            try:
                x0, y0, x1, y1 = (float(v) for v in k["around"][1].split(","))
                opened = len(k["around"]) > 2
                if opened and (k["around"][2] != "open" or len(k["around"]) < 4):
                    raise ValueError
                at = [tuple(float(v) for v in a.split(",")) for a in k["around"][3:]]
                side = float(k["buffer"]) if opened else 0.0
                if not (x0 < x1 and y0 < y1) or any(len(a) != 2 for a in at) or (k["buffer"] != "-") != opened:
                    raise ValueError
            except (IndexError, ValueError):
                raise SystemExit(f"keepout {k['name']}: want 'box X0,Y0,X1,Y1' with X0 < X1, Y0 < Y1 and buffer "
                                 "'-', or 'box X0,Y0,X1,Y1 open X,Y ...' with the windows' side as buffer") from None
            wins = [(x - side / 2, y - side / 2, x + side / 2, y + side / 2) for x, y in at]
            ys = sorted({y0, y1} | {y for w in wins for y in (w[1], w[3]) if y0 < y < y1})
            for ya, yb in zip(ys, ys[1:]):
                x = x0
                for w in sorted(w for w in wins if w[1] < yb and w[3] > ya):
                    if w[0] > x:
                        polys.append([(x, ya), (w[0], ya), (w[0], yb), (x, yb)])
                    x = max(x, w[2])
                if x < x1:
                    polys.append([(x, ya), (x1, ya), (x1, yb), (x, yb)])
        elif head in ("pair-tracks", "pair-leads"):
            # "pair-tracks": around the drawn 0.31 mm conductors of the pairs. "pair-leads": around
            # the 0.20 mm lead-ins at U6 and at the receptacles, the hops and the branches. Both
            # take "in REGION ...". The document keeps wires off the conductors only, so CC1 and CC2
            # can leave their pads beside a lane; a via is kept off the leads too
            buf = _buffer_mm(k)
            within = _within(k, routing, regions)
            nets = {n for p in routing["pairs"] for n in p["nets"]}
            for r in routing["rows"]:
                if r["net"] in nets and r["layer"] != "via" and (r["width"] > 0.2) == (head == "pair-tracks"):
                    rects = _rects(_row_points(r, pad_frame), r["width"] / 2 + buf)
                    polys += rects if within is None else _clip(rects, within)
        elif head == "B.Cu-rows":
            # "B.Cu-rows" or "B.Cu-rows in REGION ..." ("in analog": the analog blocks): around
            # the document's B.Cu tracks, clipped to the named placement regions when given
            buf = _buffer_mm(k)
            within = _within(k, routing, regions)
            for r in routing["rows"]:
                if r["layer"] == "B.Cu":
                    rects = _rects(_row_points(r, pad_frame), r["width"] / 2 + buf)
                    polys += rects if within is None else _clip(rects, within)
        else:
            for name in k["around"]:
                if name not in regions:
                    raise SystemExit(f"keepout {k['name']}: no placement region {name}")
                x, y, w, h = regions[name]
                polys.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
        for layer in k["layers"]:
            if layer != "signal" and layer not in LAYERS:
                raise SystemExit(f"keepout {k['name']}: layer {layer!r}")
            out += [(layer, k["kind"], p) for p in polys]
    return out


def _um(x, y):
    return f"{(ORIGIN[0] + x) * 1000:.0f} {-(ORIGIN[1] - y) * 1000:.0f}"


def _class_names(text, i):
    """Net names of a DSN (class ...) body from offset i: (names, offset of the first '(')."""
    names = []
    while True:
        while text[i].isspace():
            i += 1
        if text[i] in "()":
            return names, i
        if text[i] == '"':
            j = text.index('"', i + 1) + 1
        else:
            j = i
            while not text[j].isspace() and text[j] not in '()"':
                j += 1
        names.append(text[i:j])
        i = j


def post_dsn(text, routing, keepouts, via):
    """KiCad's DSN -> the router's input: the document's classes (their nets moved out of
    KiCad's classes), their via padstacks, and the keepouts. `via` is the board's (diameter,
    drill) in mm (board_via), the via KiCad names in the structure's via line."""
    via_name = f"Via[0-3]_{round(via[0] * 1000)}:{round(via[1] * 1000)}_um"
    structure_via = re.compile(r'^    \(via "' + re.escape(via_name) + r'"[^)\n]*\)$', re.M)
    moved = {n for c in routing["classes"] for n in c["nets"]}
    out, pos = [], 0
    for m in re.finditer(r"\(class (\S+) ", text):
        if m.start() < pos:
            continue
        names, i = _class_names(text, m.end())
        out.append(text[pos:m.end()] + " ".join(n for n in names if n not in moved) + "\n      ")
        pos = i
    text = "".join(out) + text[pos:]
    vias, blocks = [], []
    for c in routing["classes"]:
        circuit = ""
        if c["via"]:
            d, drill = (round(v * 1000) for v in c["via"])
            name = f"Via[0-3]_{d}:{drill}_um"
            if name not in text and name not in vias:
                vias.append(name)
                shapes = "".join(f"      (shape (circle {L} {d}))\n" for L in LAYERS)
                text = text.replace("  )\n  (network", f'    (padstack "{name}"\n{shapes}      (attach off)\n    )\n'
                                    "  )\n  (network", 1)
            circuit += f'        (use_via "{name}")\n'
        if c["layers"]:
            circuit += f'        (use_layer {" ".join(c["layers"])})\n'
        if circuit:
            circuit = f"      (circuit\n{circuit}      )\n"
        blocks.append(f"    (class {c['name']} {' '.join(c['nets'])}\n{circuit}      (rule\n"
                      f"        (width {c['width'] * 1000:.0f})\n        (clearance {c['clearance'] * 1000:.0f})\n"
                      f"      )\n    )\n")
    i = text.index("  (wiring")
    j = text.rindex("  )\n", 0, i)
    text = text[:j] + "".join(blocks) + text[j:]
    # on the plane a via of another net stands in its antipad: every via padstack is plane_via
    # larger on In1.Cu, so the router keeps plane copper between two antipads. A GND via has no
    # antipad: the vias already on GND keep a copy of the padstack as KiCad wrote it
    grow = round(routing["plane_via"] * 1000)
    stack = re.compile(r'    \(padstack "(Via\[0-3\]_\d+:\d+_um)"\n(?:      \(shape \(circle \S+ \d+\)\)\n)+'
                       r'      \(attach off\)\n    \)\n')
    text = stack.sub(lambda m: m.group(0) + m.group(0).replace(m.group(1), m.group(1) + "_gnd", 1), text)
    text, gnd = re.subn(r'^(    \(via "Via\[0-3\]_\d+:\d+_um)("  \S+ \S+ \(net GND\))', r"\1_gnd\2", text, flags=re.M)
    if gnd == 0:
        raise SystemExit("DSN: no via on GND in the wiring")

    def on_plane(m):
        return re.sub(r"\(circle In1\.Cu (\d+)\)", lambda s: f"(circle In1.Cu {int(s.group(1)) + grow})", m.group(0))
    text, n = re.subn(r'    \(padstack "Via\[0-3\]_\d+:\d+_um"\n(?:      \(shape \(circle \S+ \d+\)\)\n)+', on_plane, text)
    if n == 0 or text.count("(circle In1.Cu") < n:
        raise SystemExit("DSN: no via padstack with a circle on In1.Cu to enlarge")
    m = structure_via.search(text)
    if m is None:
        raise SystemExit(f"DSN: no structure via line naming the board's via {via_name}")
    line = m.group(0)[:-1] + "".join(f' "{v}"' for v in vias) + ")"
    # the router's costs and layer preferences (router_costs, router_layers), read after the layer
    # scopes; fanout, routing and vias stay on, the optimizer off, as autoroute.py's arguments say
    rules = "".join(f"      ({k} {v})\n" for k, v in routing["router_costs"])
    rules += "".join(f"      (layer_rule {x['layer']} (active on) (preferred_direction {x['direction']})"
                    f" (preferred_direction_trace_costs 1.0) (against_preferred_direction_trace_costs {x['against']}))\n"
                    for x in routing["router_layers"])
    if text.count("    (boundary") != 1:
        raise SystemExit("DSN: no single structure boundary to put the autoroute settings before")
    text = text.replace("    (boundary", "    (autoroute_settings\n      (fanout on)\n      (autoroute on)\n"
                        "      (postroute off)\n      (vias on)\n" + rules + "    )\n    (boundary", 1)
    m = structure_via.search(text)
    ko ="".join(f'    ({kind} "" (polygon {layer} 0  {"  ".join(_um(x, y) for x, y in poly + [poly[0]])}))\n'
                 for layer, kind, poly in keepouts)
    return text[:m.start()] + ko + line + text[m.end():]


def dsn_digest(text):
    """SHA-256 of a DSN without its first line, which names the file it was written to."""
    return hashlib.sha256(text.split("\n", 1)[1].encode("utf-8")).hexdigest()


def import_session(board, text, sx):
    """Add the routed (not protected) wires and vias of a Specctra session. Returns counts."""
    text = re.sub(r'\(string_quote\s+"\)', "", text)
    routes = sx.first(sx.loads(text), "routes")
    res = sx.first(routes, "resolution")
    scale = {"um": 1e-3, "mm": 1.0, "mil": 0.0254}[str(res[1])] / float(res[2])
    vias = {}
    for ps in sx.find(sx.first(routes, "library_out") or ["library_out"], "padstack"):
        m = re.search(r"_(\d+):(\d+)_um", ps[1])
        vias[ps[1]] = (int(m.group(1)) / 1000, int(m.group(2)) / 1000)
    layers = {board.GetLayerName(i): i for i in LAYERS.values()}

    def protected(node):
        t = sx.first(node, "type")
        return t is not None and str(t[1]) == "protect"
    n_t = n_v = 0
    added = []
    for net in sx.find(sx.first(routes, "network_out"), "net"):
        ni = board.FindNet(str(net[1]))
        if ni is None:
            raise SystemExit(f"session: no net {net[1]} on the board")
        for w in sx.find(net, "wire"):
            if protected(w):
                continue
            path = sx.first(w, "path")
            layer, width = layers[str(path[1])], float(path[2]) * scale
            pts = [pcbnew.VECTOR2I(mm(float(path[i]) * scale), mm(-float(path[i + 1]) * scale))
                   for i in range(3, len(path), 2)]
            for a, b in zip(pts, pts[1:]):
                # the router rounds a protected wire's end onto its grid and joins the two
                # with a sub-micron stub; the board keeps the document's wire, so drop the stub
                if (a - b).EuclideanNorm() < mm(STUB_MM):
                    continue
                add_track(board, ni, a, b, width, layer)
                n_t += 1
        for v in sx.find(net, "via"):
            if protected(v):
                continue
            added.append(add_via(board, ni, pcbnew.VECTOR2I(mm(float(v[2]) * scale), mm(-float(v[3]) * scale)),
                                 *vias[v[1]]))
            n_v += 1
    return n_t, n_v - drop_dangling(board, added)


STUB_MM = 0.002


def drop_dangling(board, vias):
    """Remove the vias of `vias` that join fewer than two copper layers: a track end, a pad of
    the net, or (for a plane net) the plane counts for its layer. Returns how many went."""
    planes = {z.GetNetname() for z in board.Zones() if z.GetLayer() == pcbnew.In1_Cu}
    by_net = {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            by_net.setdefault(t.GetNetname(), []).append(t)
    pads = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            pads.setdefault(p.GetNetname(), []).append(p)
    gone = 0
    for v in vias:
        at, r, net = v.GetPosition(), v.GetWidth(pcbnew.F_Cu) // 2, v.GetNetname()
        hit = {pcbnew.In1_Cu} if net in planes else set()
        for t in by_net.get(net, ()):
            if min((t.GetStart() - at).EuclideanNorm(), (t.GetEnd() - at).EuclideanNorm()) <= r:
                hit.add(t.GetLayer())
        for p in pads.get(net, ()):
            for layer in LAYERS.values():
                if p.IsOnLayer(layer) and p.HitTest(at):
                    hit.add(layer)
        if len(hit) < 2:
            board.Remove(v)
            gone += 1
    return gone
