"""Check the routed Rev0.5 board against its routing document (issue #6 P4; CLAUDE.md 5, 8).

Run with KiCad's own Python from the repository root, after make_pcb.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_routing.py
        [--src DIR] [--doc ROUTING.md] [--placement PLACEMENT.md] [--reports DIR]

What it checks, each against design/ecad/ROUTING_Rev0.5.md:
1. DRC with schematic parity: no violation of any severity, no unconnected item, no parity
   issue (Section 8, Routing gate: zero unrouted nets).
2. In1.Cu is a plane layer holding only the GND zone, with no track or arc on it.
3. The HS pairs: every track of a pair net is on F.Cu and the pair's nets have no via; widths
   are 0.20 (the lead-ins at U6 and at the receptacle, the hop and the branch of D37) or
   0.31 mm; along the document's centreline each 0.31 mm conductor is 0.23 mm from it; the two
   conductors' lengths, every track counted, differ by at most SKEW_MM.
4. The pairs' surroundings: no copper of another net within 0.5 mm of a coupled conductor on
   F.Cu or on In2.Cu (pads of U6 and of the pair's end parts, the receptacle and the tap
   resistors, excepted); the In1 GND fill under each pair track reaches 0.3 mm beyond its
   edges, except within EXEMPT_MM of a pad of an end part (their antipads).
5. The Kelvin taps (rows whose Why is "Kelvin tap"): exactly the document's straight 0.20 mm
   F.Cu tracks, and no via, on each sense net.
6. CLAUDE.md 5.1 as D36 applies it in the analog blocks (the keepouts table's `analog`
   argument): an In2.Cu track that enters one of them and a B.Cu track of another net within
   0.3 mm below it cross at 45 degrees or more (less 0.1 degree: the session's 0.1 um grid puts
   a 45-degree track a few millidegrees off); they never run along each other. A net over its
   own B.Cu track, at the via where it changes layer, is one signal, not two.
7. Router classes with a layer list: their nets' tracks only on those layers.
8. The port path copper of the port_path table: the sum per port at most its limit. A `+`
   joins the pads of one receptacle into one node (the plug ties its VBUS contacts).
9. The In1 GND plane is one sheet, not a perforated one (CLAUDE.md 5.1, 8: no fragmented
   reference plane). A void is one outline of the zone's outline less its stored fill.
   a. Slots: no void is longer than PLANE_SLOT_MM between its two farthest points. The limit
      stands just above the longest void one hole makes on this board (2.81 mm, a square
      through-hole pad) and above the three merged vias of a hand-drawn power group (2.60 mm);
      it is not a field calculation. What it catches is four or more antipads merged in a row.
   b. The exposed pads of the epad table: on each of the pad's four sides, the plane copper
      that joins the pad's area to the plane outside is at least EPAD_WEB of the pad's side.
      A side's sector lies between the pad's two diagonals, from the pad's edge out to
      EPAD_REACH_MM. Its web is the least copper a line from one diagonal to the other must
      cross, voids being free to cross (a shortest path over the voids).

What it CANNOT see: whether a track is a good one (lengths and detours DRC accepts), current
density inside a pad or a via other than by the nodal model, the impedance of the pairs (D27's
model value) or what the receptacle's pads, the hop and the branch add, and anything off the
board. Rule 6 is checked
on whole In2 segments that touch an analog region, so a segment that only grazes a region's
edge is held to the rule along its whole length.
Rule 9 reads the fill stored in the board file and does not refill it: a stale fill is seen
only through DRC. It measures copper widths, not inductance, and does not know which signal
crosses which void. 9a does not see a row of short voids with narrow webs between them, away
from an exposed pad. 9b looks only at the parts of the epad table and only as far as its
reach; a void that reaches across a diagonal counts in both sectors up to the diagonal. Copper
islands inside a void count as void. Neither looks at the pours on In2.Cu and B.Cu.
Exit status: 0 = every check passed; 1 = a check failed.
"""
import argparse
import heapq
import importlib.util
import json
import math
import pathlib
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
HALF_GAP = 0.23                    # D27: S 0.15 + W 0.31 -> conductor centres 0.46 mm apart
PAIR_WIDTHS = (0.20, 0.31)
COPLANAR_MM = 0.50
L2_MARGIN_MM = 0.30
EXEMPT_MM = 1.5
SKEW_MM = 1.25
ANALOG_RULE_MM = 0.30
CROSS_DEG = 45                     # D36: an In2 and a B.Cu track in an analog block may only cross
CROSS_TOL_DEG = 0.1                # the session's 0.1 um grid: a 45-degree track measures 44.99x
SAMPLE_MM = 0.1
PLANE_SLOT_MM = 3.0                # rule 9a: the longest void allowed in the In1 GND fill
EPAD_WEB = 0.5                     # rule 9b: of the exposed pad's side, the least copper on each side
EPAD_REACH_MM = 5.0                # rule 9b: how far beyond the exposed pad its four sectors reach
SLIVER_MM = 0.05                   # the fill stands this far inside the zone's outline at most
RHO = 1.72e-8                      # ohm m, copper at 20 C
THICK = {pcbnew.F_Cu: 35e-6, pcbnew.B_Cu: 35e-6, pcbnew.In1_Cu: 15.2e-6, pcbnew.In2_Cu: 15.2e-6}
BARREL_M, PLATING_M = 1.6e-3, 18e-6


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


make_pcb = _load("make_pcb")
route = make_pcb.route
mm = pcbnew.FromMM
to_mm = pcbnew.ToMM


class Report:
    def __init__(self):
        self.fails, self.count = [], 0

    def check(self, cond, who, what):
        self.count += 1
        if not cond:
            self.fails.append(f"FAIL {who}: {what}")
        return cond


# ---- geometry, board frame (mm) -------------------------------------------------------------
def frame(vec):
    return route.to_frame(vec)


def seg_dist(p, a, b):
    """(distance from p to segment ab, parameter t in [0, 1] of the nearest point)."""
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy), t


def interior(p, line, end_mm=0.3, bend_mm=0.5):
    """(distance to the polyline, True when the nearest point is end_mm or more from its ends
    and bend_mm or more from a bend: at a 45-degree bend the offset conductor's corner lies
    0.23 / cos(22.5) = 0.249 mm from the centreline's corner, which is correct geometry)."""
    best, at = 1e9, 0.0
    run, bends = 0.0, []
    for a, b in zip(line, line[1:]):
        d, t = seg_dist(p, a, b)
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if d < best:
            best, at = d, run + t * L
        run += L
        bends.append(run)
    bends = bends[:-1]
    return best, end_mm <= at <= run - end_mm and all(abs(at - s) >= bend_mm for s in bends)


def samples(a, b, step=SAMPLE_MM):
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / step))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


def tracks(board):
    return [t for t in board.GetTracks() if t.GetClass() in ("PCB_TRACK", "PCB_ARC")]


def vias(board):
    return [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]


def ends(t):
    return frame(t.GetStart()), frame(t.GetEnd())


def run(args):
    r = subprocess.run([str(CLI), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    return r.returncode, r.stdout + r.stderr


# ---- checks ---------------------------------------------------------------------------------
def check_drc(rep, pcb, out):
    status, log = run(["pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
                       "--units", "mm", "-o", str(out), str(pcb)])
    if not rep.check(out.exists(), "DRC", f"kicad-cli wrote no report (exit {status}): {log[-300:]}"):
        return None
    report = json.loads(out.read_text(encoding="utf-8"))
    for v in report.get("violations", []):
        items = "; ".join(i["description"] for i in v.get("items", []))
        rep.check(False, "DRC", f"{v['severity']} {v['type']}: {items}")
    for v in report.get("schematic_parity", []):
        rep.check(False, "DRC parity", f"{v['type']}: {'; '.join(i['description'] for i in v.get('items', []))}")
    u = report.get("unconnected_items", [])
    for v in u[:40]:
        rep.check(False, "DRC unconnected", "; ".join(i["description"] for i in v.get("items", [])))
    rep.check(len(u) <= 40, "DRC unconnected", f"{len(u)} unconnected items in all")
    return len(u)


def check_in1(rep, board):
    rep.check(board.GetLayerType(pcbnew.In1_Cu) == pcbnew.LT_POWER, "In1.Cu", "is not a plane (power) layer")
    on = [t for t in tracks(board) if t.GetLayer() == pcbnew.In1_Cu]
    rep.check(not on, "In1.Cu", f"{len(on)} track(s) on the plane layer")
    zones = [z for z in board.Zones() if z.IsOnLayer(pcbnew.In1_Cu)]
    rep.check(len(zones) == 1 and zones[0].GetNetname() == "GND", "In1.Cu",
              f"zones {[(z.GetZoneName(), z.GetNetname()) for z in zones]}, want one GND zone")


def _end_parts(board, nets):
    """The parts at the ends of a pair's nets: every part with a pad on them except U6 (the
    receptacle and, for the downstream pairs, the tap resistors)."""
    refs = set()
    for f in board.GetFootprints():
        if f.GetReference() != "U6" and any(p.GetNetname() in nets for p in f.Pads()):
            refs.add(f.GetReference())
    return refs


def check_pairs(rep, board, routing):
    fill = None
    zones = [z for z in board.Zones() if z.IsOnLayer(pcbnew.In1_Cu) and z.GetNetname() == "GND"]
    if zones:
        fill = zones[0].GetFilledPolysList(pcbnew.In1_Cu)
    all_tracks, all_vias = tracks(board), vias(board)
    for pair in routing["pairs"]:
        name, nets, line = pair["name"], set(pair["nets"]), pair["centreline"]
        end_parts = _end_parts(board, nets)
        own_t = [t for t in all_tracks if t.GetNetname() in nets]
        own_v = [v for v in all_vias if v.GetNetname() in nets]
        rep.check(not own_v, f"pair {name}", f"{len(own_v)} via(s) on {' '.join(sorted(nets))}")
        exempt = []
        for f in board.GetFootprints():
            if f.GetReference() in end_parts:
                exempt += [frame(p.GetPosition()) for p in f.Pads()]
        lengths = {n: 0.0 for n in nets}
        coupled = []
        for t in own_t:
            a, b = ends(t)
            w = round(to_mm(t.GetWidth()), 3)
            lengths[t.GetNetname()] += math.hypot(b[0] - a[0], b[1] - a[1])
            layer = t.GetLayer()
            rep.check(layer == pcbnew.F_Cu, f"pair {name}", f"{t.GetNetname()} track on {board.GetLayerName(layer)}")
            rep.check(w in PAIR_WIDTHS, f"pair {name}", f"{t.GetNetname()} track {w} mm wide at {a}")
            if layer != pcbnew.F_Cu:
                continue
            is_coupled = False
            for p in samples(a, b):
                d, inside = interior(p, line)
                if w == 0.31 and inside:
                    is_coupled = True
                    rep.check(abs(d - HALF_GAP) <= 0.01, f"pair {name}",
                              f"{t.GetNetname()} {d:.3f} mm from the centreline at ({p[0]:.2f}, {p[1]:.2f}),"
                              f" want {HALF_GAP}")
            if is_coupled:
                coupled.append(t)
            if fill is not None:
                ux, uy = b[0] - a[0], b[1] - a[1]
                L = math.hypot(ux, uy) or 1.0
                nx, ny = -uy / L, ux / L
                off = w / 2 + L2_MARGIN_MM
                for p in samples(a, b, 0.2):
                    if any(math.hypot(p[0] - q[0], p[1] - q[1]) < EXEMPT_MM for q in exempt):
                        continue
                    for k in (-1, 0, 1):
                        q = (p[0] + k * off * nx, p[1] + k * off * ny)
                        if not fill.Contains(route.to_sheet(*q)):
                            rep.check(False, f"pair {name}", f"no In1 GND under {t.GetNetname()} at "
                                      f"({q[0]:.2f}, {q[1]:.2f})")
                            break
        lp, ln = (lengths[n] for n in pair["nets"])
        rep.check(abs(lp - ln) <= SKEW_MM, f"pair {name}",
                  f"P {lp:.2f} mm, N {ln:.2f} mm: skew {abs(lp - ln):.2f} mm > {SKEW_MM}")
        rep.check(bool(coupled), f"pair {name}", "no coupled conductor along the centreline")
        check_isolation(rep, board, name, nets, end_parts, coupled)


def check_isolation(rep, board, name, nets, end_parts, coupled):
    items = []
    for f in board.GetFootprints():
        if f.GetReference() in end_parts or f.GetReference() == "U6":
            continue
        items += [p for p in f.Pads() if p.GetNetname() not in nets]
    items += [t for t in board.GetTracks() if t.GetNetname() not in nets]
    clr = mm(COPLANAR_MM) - 1000
    for t in coupled:
        shape = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
        bb = t.GetBoundingBox()
        bb.Inflate(mm(COPLANAR_MM + 1.0))
        for it in items:
            if not bb.Intersects(it.GetBoundingBox()):
                continue
            for layer in (pcbnew.F_Cu, pcbnew.In2_Cu):
                if it.IsOnLayer(layer) and it.GetEffectiveShape(layer).Collide(shape, clr):
                    what = it.GetParentFootprint().GetReference() + "." + it.GetNumber() \
                        if it.GetClass() == "PAD" else f"{it.GetClass()} {it.GetNetname()}"
                    rep.check(False, f"pair {name}", f"{what} within {COPLANAR_MM} mm of {t.GetNetname()} on "
                              f"{board.GetLayerName(layer)} at {tuple(round(v, 2) for v in frame(t.GetStart()))}")


def check_kelvin(rep, board, routing):
    rows = [r for r in routing["rows"] if r.get("why") == "Kelvin tap"]
    rep.check(bool(rows), "Kelvin", "the document names no Kelvin tap")
    for r in rows:
        net = r["net"]
        want = [frame(route.pad_position(board, p, net)) if route.PAD_RE.match(p) else
                tuple(map(float, p.split(","))) for p in r["points"]]
        segs = [ends(t) for t in tracks(board) if t.GetNetname() == net]
        vs = [v for v in vias(board) if v.GetNetname() == net]
        rep.check(not vs, f"Kelvin {net}", f"{len(vs)} via(s)")
        for t in tracks(board):
            if t.GetNetname() == net:
                rep.check(t.GetLayer() == pcbnew.F_Cu and abs(to_mm(t.GetWidth()) - 0.20) < 1e-6,
                          f"Kelvin {net}", f"track on {board.GetLayerName(t.GetLayer())}, {to_mm(t.GetWidth())} mm")
        doc = [(want[i], want[i + 1]) for i in range(len(want) - 1)]

        def same(s, d):
            return all(math.hypot(s[k][0] - d[j][0], s[k][1] - d[j][1]) < 1e-3 for k, j in ((0, 0), (1, 1))) or \
                all(math.hypot(s[k][0] - d[j][0], s[k][1] - d[j][1]) < 1e-3 for k, j in ((0, 1), (1, 0)))
        rep.check(len(segs) == len(doc) and all(any(same(s, d) for s in segs) for d in doc),
                  f"Kelvin {net}", f"{len(segs)} track(s) on the board, the document draws {len(doc)}")


def check_analog(rep, board, routing, regions):
    """D36: inside the analog blocks an In2 track and a B.Cu track of another net within
    ANALOG_RULE_MM of each other must cross at CROSS_DEG or more. Returns how many In2 tracks enter the blocks and how
    many In2/B.Cu crossings they make there."""
    missing = [n for n in routing["analog"] if n not in regions]
    rep.check(not missing, "analog", f"no placement region {missing}")
    boxes = [regions[n] for n in routing["analog"] if n in regions]
    b_tracks = [t for t in tracks(board) if t.GetLayer() == pcbnew.B_Cu]
    clr = mm(ANALOG_RULE_MM) - 1000
    n = crossings = 0
    for t in tracks(board):
        if t.GetLayer() != pcbnew.In2_Cu:
            continue
        a, b = ends(t)
        if not any(any(x <= p[0] <= x + w and y <= p[1] <= y + h for p in samples(a, b, 0.5)) for x, y, w, h in boxes):
            continue
        n += 1
        shape = pcbnew.SHAPE_SEGMENT(t.GetStart(), t.GetEnd(), t.GetWidth())
        for u in b_tracks:
            if u.GetNetCode() != t.GetNetCode() and u.GetEffectiveShape(pcbnew.B_Cu).Collide(shape, clr):
                c, d = ends(u)
                ang = _angle(a, b, c, d)
                crossings += ang >= CROSS_DEG - CROSS_TOL_DEG
                rep.check(ang >= CROSS_DEG - CROSS_TOL_DEG, "analog",
                          f"In2 {t.GetNetname()} at {tuple(round(v, 2) for v in a)} runs along B.Cu "
                          f"{u.GetNetname()} within {ANALOG_RULE_MM} mm below it ({ang:.0f} deg, want >= {CROSS_DEG})")
    rep.check(True, "analog", "ran")
    return n, crossings


def _angle(a, b, c, d):
    """The angle between segments ab and cd, 0-90 degrees (0 for a zero-length one)."""
    u, v = (b[0] - a[0], b[1] - a[1]), (d[0] - c[0], d[1] - c[1])
    lu, lv = math.hypot(*u), math.hypot(*v)
    if lu == 0 or lv == 0:
        return 0.0
    return math.degrees(math.acos(min(1.0, abs(u[0] * v[0] + u[1] * v[1]) / (lu * lv))))


def check_class_layers(rep, board, routing):
    for c in routing["classes"]:
        if not c["layers"]:
            continue
        allowed = {route.LAYERS[name] for name in c["layers"]}
        for t in tracks(board):
            if t.GetNetname() in c["nets"]:
                rep.check(t.GetLayer() in allowed, f"class {c['name']}",
                          f"{t.GetNetname()} track on {board.GetLayerName(t.GetLayer())}")


def net_resistance(board, net, a, b):
    """Ohms between a and b of one net, by nodal analysis of its copper. Each end is a pad
    ('REF.PAD') or several joined by '+': pads that the part itself ties together (a receptacle's
    two VBUS contacts, which the plug shorts) are one node, and the current splits between them."""
    joined = {pad: end for end in (a, b) for pad in end.split("+")}
    pads = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetname() == net:
                pads[f"{f.GetReference()}.{p.GetNumber()}"] = p
    nodes = {}

    def node(key):
        return nodes.setdefault(key, len(nodes))

    def at(pt, layer):
        for k, p in pads.items():
            if p.IsOnLayer(layer) and p.HitTest(pt):
                return ("pad", joined.get(k, k))
        return ("pt", layer, round(pt.x / 5000), round(pt.y / 5000))      # 5 um: joins the router's 0.5 um stubs
    edges = []
    items = [t for t in board.GetTracks() if t.GetNetname() == net]
    for t in items:
        if t.GetClass() == "PCB_VIA":
            d = t.GetDrillValue() * 1e-9
            r = RHO * BARREL_M / (math.pi * (d + PLATING_M) * PLATING_M)
            edges.append((node(at(t.GetPosition(), pcbnew.F_Cu)), node(at(t.GetPosition(), pcbnew.B_Cu)), r))
            continue
        L = t.GetLayer()
        pts = [t.GetStart(), t.GetEnd()]
        for u in items:
            qs = (u.GetPosition(),) if u.GetClass() == "PCB_VIA" else (u.GetStart(), u.GetEnd())
            for q in qs:
                if u is not t and (u.GetClass() == "PCB_VIA" or u.GetLayer() == L) and t.HitTest(q, 0):
                    pts.append(q)
        s = t.GetStart()
        ex, ey = t.GetEnd().x - s.x, t.GetEnd().y - s.y
        ln2 = ex * ex + ey * ey or 1
        pts = sorted({(p.x, p.y) for p in pts}, key=lambda p: ((p[0] - s.x) * ex + (p[1] - s.y) * ey) / ln2)
        w = t.GetWidth() * 1e-9
        for p, q in zip(pts, pts[1:]):
            na, nb = node(at(pcbnew.VECTOR2I(*p), L)), node(at(pcbnew.VECTOR2I(*q), L))
            if na != nb:
                edges.append((na, nb, RHO * math.hypot(q[0] - p[0], q[1] - p[1]) * 1e-9 / (w * THICK[L])))
    ia, ib = nodes.get(("pad", a)), nodes.get(("pad", b))
    if ia is None or ib is None:
        return None
    # solve a's island of copper only: another island of the same net (a stub the router left,
    # a group joined only through a zone) would make the whole matrix singular
    adj = {}
    for i, j, _ in edges:
        adj.setdefault(i, set()).add(j)
        adj.setdefault(j, set()).add(i)
    island, todo = {ia}, [ia]
    while todo:
        for j in adj.get(todo.pop(), ()):
            if j not in island:
                island.add(j)
                todo.append(j)
    if ib not in island:
        return float("inf")
    edges = [e for e in edges if e[0] in island]
    idx = [k for k in sorted(island) if k != ib]
    pos = {k: i for i, k in enumerate(idx)}
    m = len(idx)
    A = [[0.0] * m for _ in range(m)]
    for i, j, r in edges:
        g = 1 / r
        for x, y, v in ((i, i, g), (j, j, g), (i, j, -g), (j, i, -g)):
            if x != ib and y != ib:
                A[pos[x]][pos[y]] += v
    rhs = [0.0] * m
    rhs[pos[ia]] = 1.0
    for c in range(m):
        p = max(range(c, m), key=lambda r: abs(A[r][c]))
        if abs(A[p][c]) < 1e-12:
            return float("inf")
        A[c], A[p], rhs[c], rhs[p] = A[p], A[c], rhs[p], rhs[c]
        for r in range(c + 1, m):
            f = A[r][c] / A[c][c]
            if f:
                for k in range(c, m):
                    A[r][k] -= f * A[c][k]
                rhs[r] -= f * rhs[c]
    x = [0.0] * m
    for c in range(m - 1, -1, -1):
        x[c] = (rhs[c] - sum(A[c][k] * x[k] for k in range(c + 1, m))) / A[c][c]
    return x[pos[ia]]


def check_port_paths(rep, board, tables):
    if not rep.check("port_path" in tables, "port path", "no port_path table in the document"):
        return {}
    args, rows = tables["port_path"]
    limit = float(args["limit"])
    totals = {}
    for r in rows:
        ohm = net_resistance(board, r["Net"], r["From"], r["To"])
        if not rep.check(ohm is not None and ohm != float("inf"), f"port {r['Port']}",
                         f"{r['Net']} {r['From']} -> {r['To']}: no copper path"):
            ohm = float("inf")
        totals[r["Port"]] = totals.get(r["Port"], 0.0) + ohm * 1e3
    for port, total in totals.items():
        rep.check(total <= limit, f"port {port}", f"{total:.2f} mOhm of copper, limit {limit}")
    return totals


# ---- rule 9: the In1 plane ------------------------------------------------------------------
def _ring(chain):
    return [frame(chain.CPoint(j)) for j in range(chain.PointCount())]


def _box(ring):
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    return min(xs), min(ys), max(xs), max(ys)


def _box_gap(p, q):
    return math.hypot(max(p[0] - q[2], q[0] - p[2], 0.0), max(p[1] - q[3], q[1] - p[3], 0.0))


def plane_voids(board):
    """The voids of the In1 GND fill as a SHAPE_POLY_SET: the zone's outline, drawn in by
    SLIVER_MM, less the stored fill. None when the board has no In1 GND zone."""
    zones = [z for z in board.Zones() if z.IsOnLayer(pcbnew.In1_Cu) and z.GetNetname() == "GND"]
    if not zones:
        return None
    voids = pcbnew.SHAPE_POLY_SET(zones[0].Outline())
    voids.Deflate(mm(SLIVER_MM), pcbnew.CORNER_STRATEGY_ALLOW_ACUTE_CORNERS, mm(0.005))
    voids.BooleanSubtract(zones[0].GetFilledPolysList(pcbnew.In1_Cu))
    return voids


def caliper(ring):
    """The distance between the two farthest points of a closed polyline."""
    return max(math.hypot(p[0] - q[0], p[1] - q[1]) for k, p in enumerate(ring) for q in ring[k:])


def _crosses(a, b, c, d):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    return (side(a, b, c) > 0) != (side(a, b, d) > 0) and (side(c, d, a) > 0) != (side(c, d, b) > 0)


def _ring_to_line(ring, a, b):
    """The distance from a closed polyline to the segment ab: 0 when they cross."""
    best = min(seg_dist(v, a, b)[0] for v in ring)
    for c, d in zip(ring, ring[1:] + ring[:1]):
        if _crosses(a, b, c, d):
            return 0.0
        best = min(best, seg_dist(a, c, d)[0], seg_dist(b, c, d)[0])
    return best


def _ring_to_ring(p, q):
    """The distance between two closed polylines that do not cross: it is at a vertex of one."""
    return min(seg_dist(v, c, d)[0] for r, s in ((p, q), (q, p)) for v in r for c, d in zip(s, s[1:] + s[:1]))


def epad_webs(voids, box, reach):
    """{side: mm} for the exposed pad `box` = (x0, y0, x1, y1): on each side N, E, S, W the least
    plane copper a line from one diagonal of the pad to the other must cross inside the side's
    sector, which reaches `reach` beyond the pad. Voids are free to cross, so this is a shortest
    path from the left diagonal to the right one over the void pieces of the sector; the pad's
    own edge, which costs its whole length, is the longest such line."""
    x0, y0, x1, y1 = box
    X0, Y0, X1, Y1 = x0 - reach, y0 - reach, x1 + reach, y1 + reach
    sectors = {"N": ((x0, y1), (x1, y1), (X1, Y1), (X0, Y1)), "E": ((x1, y1), (x1, y0), (X1, Y0), (X1, Y1)),
               "S": ((x1, y0), (x0, y0), (X0, Y0), (X1, Y0)), "W": ((x0, y0), (x0, y1), (X0, Y1), (X0, Y0))}
    out = {}
    for name, (a, b, c, d) in sectors.items():
        sector = pcbnew.SHAPE_POLY_SET()
        sector.NewOutline()
        for p in (a, b, c, d):
            sector.Append(route.to_sheet(*p))
        part = pcbnew.SHAPE_POLY_SET(voids)
        part.BooleanIntersection(sector)
        rings = [_ring(part.Outline(i)) for i in range(part.OutlineCount())]
        boxes = [_box(r) for r in rings]
        direct = math.hypot(b[0] - a[0], b[1] - a[1])
        n = len(rings)
        left, right = n, n + 1
        adj = {k: [] for k in range(n + 2)}

        def join(i, j, w):
            if w < direct:                       # a longer step never beats the pad's own edge
                adj[i].append((j, w))
                adj[j].append((i, w))
        adj[left].append((right, direct))
        for i in range(n):
            join(left, i, _ring_to_line(rings[i], a, d))
            join(i, right, _ring_to_line(rings[i], b, c))
            for j in range(i + 1, n):
                if _box_gap(boxes[i], boxes[j]) < direct:
                    join(i, j, _ring_to_ring(rings[i], rings[j]))
        dist, heap = {left: 0.0}, [(0.0, left)]
        while heap:
            du, u = heapq.heappop(heap)
            if du > dist.get(u, 1e9):
                continue
            for v, w in adj[u]:
                if du + w < dist.get(v, 1e9):
                    dist[v] = du + w
                    heapq.heappush(heap, (du + w, v))
        out[name] = dist[right]
    return out


def _epad_box(board, token):
    ref, num = route.PAD_RE.match(token).groups()
    fp = board.FindFootprintByReference(ref)
    pads = [p for p in fp.Pads() if p.GetNumber() == num] if fp else []
    if len(pads) != 1:
        return None
    bb = pads[0].GetBoundingBox()
    (xa, ya), (xb, yb) = (frame(pcbnew.VECTOR2I(x, y)) for x, y in ((bb.GetLeft(), bb.GetTop()),
                                                                     (bb.GetRight(), bb.GetBottom())))
    return min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)


def check_plane(rep, board, routing):
    """Rule 9. Returns (the longest void in mm, {pad: {side: web in mm}}) for the statistics."""
    voids = plane_voids(board)
    if not rep.check(voids is not None, "L2", "no In1 GND zone to measure"):
        return None, {}
    holes = [(v.GetPosition(), f"via {v.GetNetname()}") for v in vias(board)]
    for f in board.GetFootprints():
        holes += [(p.GetPosition(), f"{f.GetReference()}.{p.GetNumber()}") for p in f.Pads() if p.GetDrillSize().x > 0]
    longest = 0.0
    for i in range(voids.OutlineCount()):
        ring = _ring(voids.Outline(i))
        length = caliper(ring)
        longest = max(longest, length)
        if length > PLANE_SLOT_MM:
            one = pcbnew.SHAPE_POLY_SET()
            one.AddOutline(voids.Outline(i))
            inside = sorted({name for at, name in holes if one.Contains(at)})
            x0, y0, x1, y1 = _box(ring)
            rep.check(False, "L2 slot", f"void {length:.2f} mm long, x {x0:.2f}..{x1:.2f}, y {y0:.2f}..{y1:.2f}, "
                      f"limit {PLANE_SLOT_MM}: {len(inside)} hole(s) in it: {' '.join(inside)[:160]}")
    rep.check(True, "L2 slot", "ran")
    webs = {}
    for token in routing["epads"]:
        box = _epad_box(board, token)
        if not rep.check(box is not None, f"L2 web {token}", "no such pad on the board"):
            continue
        side = box[2] - box[0]
        if not rep.check(abs((box[3] - box[1]) - side) < 1e-3, f"L2 web {token}", f"pad box {box} is not square"):
            continue
        webs[token] = epad_webs(voids, box, EPAD_REACH_MM)
        for name, web in webs[token].items():
            rep.check(web >= EPAD_WEB * side - 1e-6, f"L2 web {token} {name}",
                      f"{web:.2f} mm of plane copper on this side, {100 * web / side:.0f} % of the pad's "
                      f"{side:.2f} mm, want >= {100 * EPAD_WEB:.0f} % within {EPAD_REACH_MM} mm")
    return longest, webs


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "design" / "ecad" / "source")
    ap.add_argument("--doc", type=pathlib.Path, default=make_pcb.ROUTING)
    ap.add_argument("--placement", type=pathlib.Path, default=make_pcb.DOC)
    ap.add_argument("--reports", type=pathlib.Path)
    a = ap.parse_args(argv[1:])
    rep = Report()
    pcb, prl = a.src / f"{NICK}.kicad_pcb", a.src / f"{NICK}.kicad_prl"
    prl_before = prl.exists()
    routing, regions = make_pcb.read_routing(a.placement, a.doc)
    tables = make_pcb.doc_tables(a.doc.read_text(encoding="utf-8"))
    board = pcbnew.LoadBoard(str(pcb))
    check_in1(rep, board)
    check_pairs(rep, board, routing)
    check_kelvin(rep, board, routing)
    n_in2, n_cross = check_analog(rep, board, routing, regions)
    check_class_layers(rep, board, routing)
    totals = check_port_paths(rep, board, tables)
    longest, webs = check_plane(rep, board, routing)
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(a.reports) if a.reports else pathlib.Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        unconnected = check_drc(rep, pcb, out / "drc.json")
    if prl.exists() and not prl_before:
        prl.unlink()
    for line in rep.fails:
        print(line)
    ports = ", ".join(f"port {p} {t:.2f} mOhm" for p, t in sorted(totals.items()))
    print(f"{len(tracks(board))} tracks, {len(vias(board))} vias; {n_in2} In2 track(s) in the analog blocks,"
          f" {n_cross} In2/B.Cu crossing(s) there;"
          f" {ports}; {unconnected if unconnected is not None else '?'} unconnected items")
    print(f"In1 plane: longest void {'?' if longest is None else f'{longest:.2f}'} mm; " + "; ".join(
        f"{token} web " + " ".join(f"{side} {web:.2f}" for side, web in sides.items()) + " mm"
        for token, sides in webs.items()))
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
