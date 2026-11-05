"""Check the routed Rev0.4 board against its routing document (issue #6 P4; CLAUDE.md 5, 8).

Run with KiCad's own Python from the repository root, after make_pcb.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_routing.py
        [--src DIR] [--doc ROUTING.md] [--placement PLACEMENT.md] [--reports DIR]

What it checks, each against design/ecad/ROUTING_Rev0.4.md:
1. DRC with schematic parity: no violation of any severity, no unconnected item, no parity
   issue (Section 8, Routing gate: zero unrouted nets).
2. In1.Cu is a plane layer holding only the GND zone, with no track or arc on it.
3. The HS pairs: every track of a pair net is on F.Cu, except the N conductor's crossing on
   B.Cu; widths are 0.20 (the lead-ins at U6) or 0.31 mm; along the document's centreline each
   0.31 mm conductor is 0.23 mm from it, or, where the pair's Tune cell names that conductor and
   span, 0.23 mm up to 0.23 mm + the bump height (never nearer its partner); the two conductors' lengths (a via counted as 1.53 mm,
   L1 to L4) differ by at most SKEW_MM.
4. The pairs' surroundings: no copper of another net within 0.5 mm of a coupled conductor on
   F.Cu or on In2.Cu (pads of U6 and of the pair's module excepted); the In1 GND fill under each
   pair conductor reaches 0.3 mm beyond its edges, except within EXEMPT_MM of a via of the
   pair's own nets or of a pad of its module (their antipads).
5. The Kelvin taps (rows whose Why is "Kelvin tap"): exactly the document's straight 0.20 mm
   F.Cu tracks, and no via, on each sense net.
6. CLAUDE.md 5.1 as D36 applies it in the analog blocks (the keepouts table's `analog`
   argument): an In2.Cu track that enters one of them and a B.Cu track of another net within
   0.3 mm below it cross at 45 degrees or more (less 0.1 degree: the session's 0.1 um grid puts
   a 45-degree track a few millidegrees off); they never run along each other. A net over its
   own B.Cu track, at the via where it changes layer, is one signal, not two.
7. Router classes with a layer list: their nets' tracks only on those layers.
8. The port path copper of the port_path table: the sum per port at most its limit.

What it CANNOT see: whether a track is a good one (lengths and detours DRC accepts), current
density inside a pad or a via other than by the nodal model, the impedance of the pairs (D27's
model value) or what the module and header add, and anything off the board. Rule 6 is checked
on whole In2 segments that touch an analog region, so a segment that only grazes a region's
edge is held to the rule along its whole length.
Exit status: 0 = every check passed; 1 = a check failed.
"""
import argparse
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
VIA_LENGTH_MM = 1.53               # L1 to L4 of JLC04161H-7628, 1.6 mm less the outer copper
ANALOG_RULE_MM = 0.30
CROSS_DEG = 45                     # D36: an In2 and a B.Cu track in an analog block may only cross
CROSS_TOL_DEG = 0.1                # the session's 0.1 um grid: a 45-degree track measures 44.99x
SAMPLE_MM = 0.1
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


def in_span(p, span):
    """Whether p projects onto the centreline between the Tune span's two points."""
    (xa, ya), (xb, yb) = span
    ux, uy = xb - xa, yb - ya
    t = ((p[0] - xa) * ux + (p[1] - ya) * uy) / (ux * ux + uy * uy)
    return 0.0 <= t <= 1.0


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


def _module_of(board, nets):
    """The parts at the far end of a pair: every part with a pad on its nets except U6."""
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
        ends_parts = _module_of(board, nets)
        own_t = [t for t in all_tracks if t.GetNetname() in nets]
        own_v = [v for v in all_vias if v.GetNetname() in nets]
        exempt = [frame(v.GetPosition()) for v in own_v]
        for f in board.GetFootprints():
            if f.GetReference() in ends_parts:
                exempt += [frame(p.GetPosition()) for p in f.Pads()]
        lengths = {n: 0.0 for n in nets}
        coupled = []
        for t in own_t:
            a, b = ends(t)
            w = round(to_mm(t.GetWidth()), 3)
            lengths[t.GetNetname()] += math.hypot(b[0] - a[0], b[1] - a[1])
            layer = t.GetLayer()
            rep.check(layer == pcbnew.F_Cu or (layer == pcbnew.B_Cu and t.GetNetname() == pair["nets"][1]),
                      f"pair {name}", f"{t.GetNetname()} track on {board.GetLayerName(layer)}")
            rep.check(w in PAIR_WIDTHS, f"pair {name}", f"{t.GetNetname()} track {w} mm wide at {a}")
            if layer != pcbnew.F_Cu:
                continue
            is_coupled = False
            tune = pair["tune"]
            tuned = tune is not None and t.GetNetname() == tune["net"]
            for p in samples(a, b):
                d, inside = interior(p, line)
                if w == 0.31 and inside:
                    is_coupled = True
                    hi = HALF_GAP + tune["height"] if tuned and in_span(p, tune["span"]) else HALF_GAP
                    rep.check(HALF_GAP - 0.01 <= d <= hi + 0.01, f"pair {name}",
                              f"{t.GetNetname()} {d:.3f} mm from the centreline at ({p[0]:.2f}, {p[1]:.2f}),"
                              f" want {HALF_GAP}" + (f" to {hi:.2f}" if hi > HALF_GAP else ""))
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
        for v in own_v:
            lengths[v.GetNetname()] += VIA_LENGTH_MM
        lp, ln = (lengths[n] for n in pair["nets"])
        rep.check(abs(lp - ln) <= SKEW_MM, f"pair {name}",
                  f"P {lp:.2f} mm, N {ln:.2f} mm: skew {abs(lp - ln):.2f} mm > {SKEW_MM}")
        rep.check(bool(coupled), f"pair {name}", "no coupled conductor along the centreline")
        check_isolation(rep, board, name, nets, ends_parts, coupled)


def check_isolation(rep, board, name, nets, ends_parts, coupled):
    items = []
    for f in board.GetFootprints():
        if f.GetReference() in ends_parts or f.GetReference() == "U6":
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
    """Ohms between pads a and b ('REF.PAD') of one net, by nodal analysis of its copper."""
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
                return ("pad", k)
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
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
