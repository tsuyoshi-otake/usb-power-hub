"""Check the lid PCB Rev0.1 against its document and the enclosure's lid interface (issue #11).

Run with KiCad's own Python, which carries the pcbnew module, from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/mechanical/scripts/check_lid.py
        [--doc FILE] [--interface FILE] [--src DIR] [--outputs DIR] [--no-drc]

It reads the board as written (a copy, in a temporary directory: nothing in --src is touched)
and measures it against the lid's interface and the document's tables. It does not import
make_lid.py: the copper is the fill the board file holds, the silkscreen is the ink pcbnew
draws, and every keep-clear area is built here from the interface. Checks L01 to L16 are
listed in LID_Rev0.1.md, section 6, with what each proves. One line per check, `PASS Lnn ...`
or `FAIL Lnn ...`; exit status 0 means no FAIL line.

  --doc FILE        the lid document (default design/mechanical/LID_Rev0.1.md)
  --interface FILE  the lid's interface (default the enclosure's LidInterface.json)
  --src DIR         the KiCad project (default design/mechanical/lid)
  --outputs DIR     also check a manufacturing candidate set (L12 to L16), as
                    make_lid_outputs.py writes into manufacturing/working/lid-rev0.1
  --no-drc          skip L11, KiCad's own DRC (the negative tests use it to save time)

What it CANNOT see (the document, section 6): whether a `world` value in the tables is right
(JLCPCB's legend limits, the label a person needs), whether the legend reads well, light
through the window or round it, flatness, JLCPCB's own DFM, how JLCPCB reads the Gerbers
(L16 proves they are KiCad's plot of this board; of the plot itself only the outline, the
copper's extents, the mask windows and the drill hits are read back here), what the drawing
and the two pictures of a set show (their type, page count and size are read, no more), and
whether the interface is right (check_enclosure.py's job).
"""
import argparse
import hashlib
import importlib.util
import io
import json
import math
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from types import SimpleNamespace

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load("lid_spec")
mm = pcbnew.FromMM
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"

POS_TOL = 0.001        # mm: a position or a size on the board against the table or the interface
COPPER_TOL = 0.001     # mm2 of copper tolerated in a keep-clear area (the fill's 1 nm grid)
MISSING_TOL = 0.01     # mm2 of copper tolerated missing where copper is demanded
INK_TOL = 0.0001       # mm2 of silkscreen tolerated in an area it must stay out of
CIRCLE_N = 360         # sides of the polygons that stand for a circle here
# What each port is (CLAUDE.md 1) and what its label must read (CLAUDE.md 6; J4 is D14's
# power-only input, which CLAUDE.md 6 does not name). A demand of this checker, not a copy of
# the legend table: a table that swaps two names builds, and fails L09.
PORT_NAMES = {"J1": "HOST", "J2": "OUT A", "J3": "OUT B", "J4": "5V IN"}
PINHOLE_NAME = "BOOT"  # REQ-BOOT-02: the pinhole reaches SW3
# The candidate set (make_lid_outputs.py): the names are this checker's demand.
OUTPUT_FILES = [f"{spec.PREFIX}_{n}" for n in ("Gerber.zip", "Fabrication_Top.pdf", "Preview_Top.png",
                                              "Preview_Bottom.png", "DRC.json")] + ["RELEASE_MANIFEST.md", "SHA256SUMS.txt"]
GERBER_MEMBERS = [f"{spec.PREFIX}_{n}" for n in ("F_Cu.gtl", "B_Cu.gbl", "F_Silkscreen.gto", "B_Silkscreen.gbo",
                                                "F_Mask.gts", "B_Mask.gbs", "Edge_Cuts.gm1", "PTH.drl", "NPTH.drl",
                                                "PTH-drl_map.gbr", "NPTH-drl_map.gbr")]
# What the zip's files must be a plot of (L16): this checker's own two kicad-cli calls, a demand
# as the names above are. A set plotted with other layers or another origin is not this plot.
PLOT_GERBERS = ["pcb", "export", "gerbers", "-l", "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts",
                "--subtract-soldermask", "--use-drill-file-origin"]
PLOT_DRILL = ["pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot", "--excellon-units", "mm",
              "--excellon-zeros-format", "decimal", "--excellon-oval-format", "alternate", "--excellon-separate-th",
              "--generate-map", "--map-format", "gerberx2"]
STAMP = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:[+-]\d\d:?\d\d)?")   # a creation time: each plot has its own
PREVIEW_MIN_W = 1200   # px: kicad-cli renders a little under the 1600 asked
COPPER =(("F.Cu", pcbnew.F_Cu), ("B.Cu", pcbnew.B_Cu))
FACES = (("top", pcbnew.F_SilkS, pcbnew.F_Mask, pcbnew.F_Cu), ("bottom", pcbnew.B_SilkS, pcbnew.B_Mask, pcbnew.B_Cu))


class Report:
    def __init__(self):
        self.failed = 0
        self.count = 0

    def ok(self, cid, text):
        self.count += 1
        print(f"PASS {cid} {text}")

    def fail(self, cid, text):
        self.count += 1
        self.failed += 1
        print(f"FAIL {cid} {text}")

    def check(self, cond, cid, text, bad):
        self.ok(cid, text) if cond else self.fail(cid, bad)
        return cond


# ---- geometry: the board frame (mm, y up) and KiCad's sheet (nm, y down) -------------------------
def sheet(x, y):
    return pcbnew.VECTOR2I(mm(spec.ORIGIN[0] + x), mm(spec.ORIGIN[1] - y))


def pt(v):
    """A sheet point as a board-frame point in mm."""
    return pcbnew.ToMM(v.x) - spec.ORIGIN[0], spec.ORIGIN[1] - pcbnew.ToMM(v.y)


def poly(points):
    ps = pcbnew.SHAPE_POLY_SET()
    ps.NewOutline()
    for x, y in points:
        v = sheet(x, y)
        ps.Append(v.x, v.y)
    return ps


def rect(x0, y0, x1, y1, grow=0.0):
    return poly([(x0 - grow, y0 - grow), (x1 + grow, y0 - grow), (x1 + grow, y1 + grow), (x0 - grow, y1 + grow)])


def disc(cx, cy, r, outside=False):
    """A polygon for the circle of radius r: inside it (its corners on the circle), or with
    outside=True one that contains it (its sides touch the circle)."""
    rr = r / math.cos(math.pi / CIRCLE_N) if outside else r
    return poly([(cx + rr * math.cos(2 * math.pi * i / CIRCLE_N), cy + rr * math.sin(2 * math.pi * i / CIRCLE_N))
                 for i in range(CIRCLE_N)])


def clone(ps):
    return pcbnew.SHAPE_POLY_SET(ps)


def area(ps):
    return abs(ps.Area()) / 1e12


def inter(a, b):
    r = clone(a)
    r.BooleanIntersection(b)
    return r


def minus(a, b):
    r = clone(a)
    r.BooleanSubtract(b)
    return r


def join(a, b):
    r = clone(a)
    r.BooleanAdd(b)
    return r


def grown(ps, by):
    r = clone(ps)
    r.Inflate(mm(by), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.002))
    return r


def box(ps):
    """(x0, y0, x1, y1) of a polygon set in the board frame."""
    bb = ps.BBox()
    x0, y1 = pt(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop()))
    x1, y0 = pt(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))
    return x0, y0, x1, y1


def box_gap(b, x, y):
    """Distance from a point to a box (0 inside it)."""
    return math.hypot(max(b[0] - x, 0.0, x - b[2]), max(b[1] - y, 0.0, y - b[3]))


def near(a, b, tol=POS_TOL):
    return abs(a - b) <= tol


def same_points(a, b, tol=POS_TOL):
    """Two point lists hold the same points, in any order."""
    rest = list(b)
    for p in a:
        hit = next((q for q in rest if near(p[0], q[0], tol) and near(p[1], q[1], tol)), None)
        if hit is None:
            return False
        rest.remove(hit)
    return not rest


def keep_radius(hole, params, clear):
    """What must stay `clear` away from a hole: a screw's head circle, or the hole itself."""
    return (hole["keepout_d"] if hole["kind"] == "screw" else hole["d"]) / 2 + clear


def fmt(p):
    return f"({p[0]:g}, {p[1]:g})"


# ---- reading the board ---------------------------------------------------------------------------
def read_board(board, max_error):
    """Sort every drawing of the board by what it can be; nothing is dropped (L08 closes the world)."""
    b = SimpleNamespace(edge=[], mask={pcbnew.F_Mask: [], pcbnew.B_Mask: []}, texts=[], silk=[], other=[], copper_drawings=[])
    for d in board.GetDrawings():
        cls, layer = d.GetClass(), d.GetLayer()
        if cls == "PCB_SHAPE" and layer == pcbnew.Edge_Cuts:
            b.edge.append(d)
        elif cls == "PCB_SHAPE" and layer in b.mask:
            b.mask[layer].append(d)
        elif cls == "PCB_TEXT" and layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.texts.append(d)
        elif cls == "PCB_SHAPE" and layer in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            b.silk.append(d)
        elif layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            b.copper_drawings.append(d)
        else:
            b.other.append(d)
    b.fill = {}
    for _, layer in COPPER:
        cu = pcbnew.SHAPE_POLY_SET()
        for z in board.Zones():
            if not z.GetIsRuleArea() and z.IsOnLayer(layer):
                cu.BooleanAdd(z.GetFilledPolysList(layer))
        b.fill[layer] = cu
    b.ink = {}
    for t in b.texts:
        ps = pcbnew.SHAPE_POLY_SET()
        t.TransformTextToPolySet(ps, 0, max_error, pcbnew.ERROR_OUTSIDE)
        ps.Simplify()
        b.ink[id(t)] = ps
    for d in b.silk:
        ps = pcbnew.SHAPE_POLY_SET()
        d.TransformShapeToPolygon(ps, d.GetLayer(), 0, max_error, pcbnew.ERROR_OUTSIDE)
        ps.Simplify()
        b.ink[id(d)] = ps
    return b


def triangle(d):
    """The three corners of a filled silkscreen triangle in the board frame, or None."""
    if d.GetShape() != pcbnew.SHAPE_T_POLY or not d.IsFilled() or d.GetWidth() != 0:
        return None
    shape = d.GetPolyShape()
    if shape.OutlineCount() != 1 or shape.Outline(0).PointCount() != 3:
        return None
    o = shape.Outline(0)
    return [pt(o.CPoint(i)) for i in range(3)]


def ring(d):
    """(centre, centre-line radius, line width) of an unfilled silkscreen circle, or None."""
    if d.GetShape() != pcbnew.SHAPE_T_CIRCLE or d.IsFilled():
        return None
    return pt(d.GetCenter()), pcbnew.ToMM(d.GetRadius()), pcbnew.ToMM(d.GetWidth())


def name_of(board, d):
    if d.GetClass() == "PCB_TEXT":
        return f'"{d.GetText()}"'
    c = pt(d.GetCenter()) if d.GetShape() == pcbnew.SHAPE_T_CIRCLE else None
    if c is None:
        bb = d.GetBoundingBox()
        c = pt(bb.Centre())
    kind = {pcbnew.SHAPE_T_POLY: "polygon", pcbnew.SHAPE_T_CIRCLE: "circle", pcbnew.SHAPE_T_RECT: "rectangle"}.get(d.GetShape(), "drawing")
    return f"{kind} at {fmt((round(c[0], 2), round(c[1], 2)))}"


# ---- L01: the board is built from these inputs ---------------------------------------------------
def check_identity(rep, board, params, legend, interface_path):
    tb = board.GetTitleBlock()
    comments = [tb.GetComment(i) for i in range(9)]
    stamped = [c[len(spec.DIGEST_TAG):] for c in comments if c.startswith(spec.DIGEST_TAG)]
    want = spec.inputs_digest(params, legend, interface_path)
    rep.check(stamped == [want], "L01",
              f"the board is built from this document's tables and this interface (inputs {want[:12]})",
              f"the board names its inputs as {[s[:12] for s in stamped]}; the document's tables and the interface give"
              f" {want[:12]}: rebuild with make_lid.py")
    rep.check(tb.GetRevision() == spec.REVISION, "L01", f"title block revision {spec.REVISION}",
              f"title block revision is {tb.GetRevision()!r}, want {spec.REVISION}")
    rep.check(any("WIP" in c for c in comments), "L01", "the title block states the board is WIP",
              "the title block does not state WIP (CLAUDE.md 3: every revision carries its state)")


def check_files(rep, src):
    """The tracked files are what a Git checkout gives (.gitattributes: eol=lf), so that a
    SHA-256 taken here is the SHA-256 of the committed file."""
    cr = [f"{spec.NICK}.{ext}" for ext in ("kicad_pcb", "kicad_pro")
          if b"\r" in (src / f"{spec.NICK}.{ext}").read_bytes()]
    rep.check(not cr, "L01", "the board and its project file end their lines with LF, as a checkout does",
              f"CR bytes in {cr}: a checkout would give other bytes, and another SHA-256, than these files have")


# ---- L02: the bare board -------------------------------------------------------------------------
def check_board(rep, board, b, interface):
    o = interface["outline"]
    ds = board.GetDesignSettings()
    rep.check(board.GetCopperLayerCount() == 2, "L02", "2 copper layers",
              f"{board.GetCopperLayerCount()} copper layers, want 2 (K1)")
    t = pcbnew.ToMM(ds.GetBoardThickness())
    rep.check(near(t, interface["thickness"]), "L02", f"thickness {t:g} mm, the interface's",
              f"thickness {t:g} mm, the interface says {interface['thickness']:g}")
    corners = None
    if len(b.edge) == 1 and b.edge[0].GetShape() == pcbnew.SHAPE_T_RECT:
        (ax, ay), (bx_, by_) = pt(b.edge[0].GetStart()), pt(b.edge[0].GetEnd())
        corners = (min(ax, bx_), min(ay, by_), max(ax, bx_), max(ay, by_))
    want = (o["x0"], o["y0"], o["x1"], o["y1"])
    rep.check(corners is not None and all(near(a, w) for a, w in zip(corners, want)), "L02",
              f"the outline is one rectangle, {fmt(want[:2])} to {fmt(want[2:])}: the interface's",
              f"the outline is {len(b.edge)} drawing(s) on Edge.Cuts with corners {corners}, want one rectangle {want}")
    aux = pt(ds.GetAuxOrigin())
    rep.check(near(aux[0], o["x0"]) and near(aux[1], o["y0"]), "L02",
              "the plot and drill origin is the lid's lower-left corner",
              f"the plot and drill origin is {fmt(aux)} in the board frame, want {fmt((o['x0'], o['y0']))}:"
              " the Gerbers would not share the interface's frame")
    pads_on_net = [fp.GetReference() for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() != 0]
    zones_on_net = [z.GetZoneName() for z in board.Zones() if z.GetNetCode() != 0]
    bad = []
    if len(board.GetTracks()):
        bad.append(f"{len(board.GetTracks())} track or via item(s)")
    if board.GetNetCount() != 1 or pads_on_net or zones_on_net:
        bad.append(f"{board.GetNetCount() - 1} net(s), pads on a net {pads_on_net}, zones on a net {zones_on_net}")
    if b.copper_drawings:
        bad.append(f"{len(b.copper_drawings)} drawing(s) on a copper layer")
    rep.check(not bad, "L02", "no track, no via, no net and no drawing on a copper layer: the copper is the pour alone",
              "; ".join(bad) + " (K2: the lid carries no net)")


# ---- L03: the holes ------------------------------------------------------------------------------
def check_holes(rep, board, interface):
    want = interface["hole_by_ref"]
    found = {}
    stray = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in found or ref not in want:
            stray.append(ref)
        found.setdefault(ref, fp)
    missing = sorted(set(want) - set(found))
    rep.check(not missing and not stray, "L03", f"the board drills the interface's {len(want)} holes and no other",
              f"holes missing from the board: {missing}; footprints the interface does not name, or named twice: {sorted(stray)}")
    for ref, hole in want.items():
        fp = found.get(ref)
        if fp is None:
            continue
        pads = list(fp.Pads())
        bad = []
        if len(pads) != 1:
            bad.append(f"{len(pads)} pads, want 1")
        else:
            p = pads[0]
            at, drill, size = pt(p.GetPosition()), p.GetDrillSize(), p.GetSize(pcbnew.F_Cu)
            if p.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH:
                bad.append("the hole is plated, want unplated (K4)")
            if drill.x != drill.y or not near(pcbnew.ToMM(drill.x), hole["d"]):
                bad.append(f"drill {pcbnew.ToMM(drill.x):g} x {pcbnew.ToMM(drill.y):g} mm, want round {hole['d']:g}")
            if not (near(at[0], hole["x"]) and near(at[1], hole["y"])):
                bad.append(f"at {fmt(at)}, want {fmt((hole['x'], hole['y']))}")
            if size.x > drill.x or size.y > drill.y:
                bad.append(f"a copper ring: pad {pcbnew.ToMM(size.x):g} mm on a {pcbnew.ToMM(drill.x):g} mm hole")
        if len(list(fp.GraphicalItems())):
            bad.append("the footprint carries a drawing")
        rep.check(not bad, "L03", f"hole {ref} ({hole['kind']}): {hole['d']:g} mm, unplated, at {fmt((hole['x'], hole['y']))}",
                  f"hole {ref}: " + "; ".join(bad))


# ---- L04, L05: the copper ------------------------------------------------------------------------
def keep_clear_areas(interface, params):
    """[(name, polygon)]: where no copper may be, from the interface and the clearances (K3)."""
    o = interface["outline"]
    areas = []
    for hole in interface["holes"]:
        clear = params["head_clear"] if hole["kind"] == "screw" else params["hole_clear"]
        what = "the screw head of" if hole["kind"] == "screw" else "hole"
        areas.append((f"{what} {hole['ref']} + {clear:g}", disc(hole["x"], hole["y"], keep_radius(hole, params, clear))))
    for w in interface["windows"]:
        areas.append((f"window {'/'.join(w['refs'])} + {params['window_clear']:g}", rect(*w["rect"], grow=params["window_clear"])))
    return o, areas


def check_copper(rep, b, interface, params):
    o, areas = keep_clear_areas(interface, params)
    ec, slack = params["edge_clear"], params["copper_slack"]
    inside = rect(o["x0"], o["y0"], o["x1"], o["y1"], grow=-ec)
    demanded = rect(o["x0"], o["y0"], o["x1"], o["y1"], grow=-(ec + slack))
    for hole in interface["holes"]:
        clear = params["head_clear"] if hole["kind"] == "screw" else params["hole_clear"]
        demanded = minus(demanded, disc(hole["x"], hole["y"], keep_radius(hole, params, clear) + slack, outside=True))
    for w in interface["windows"]:
        demanded = minus(demanded, rect(*w["rect"], grow=params["window_clear"] + slack))
    em, hm = params["copper_edge_min"], params["copper_hole_min"]
    least_inside = rect(o["x0"], o["y0"], o["x1"], o["y1"], grow=-em)
    walls = [(h["ref"], disc(h["x"], h["y"], h["d"] / 2 + hm)) for h in interface["holes"]]
    for name, layer in COPPER:
        cu = b.fill[layer]
        bad = []
        worst = area(minus(cu, inside))
        if worst > COPPER_TOL:
            bad.append(f"{worst:.4f} mm2 within {ec:g} mm of the outline")
        for what, region in areas:
            a = area(inter(cu, region))
            worst = max(worst, a)
            if a > COPPER_TOL:
                bad.append(f"{a:.4f} mm2 in {what} mm")
        rep.check(not bad, "L04", f"{name}: no copper within {ec:g} mm of the outline or in the {len(areas)} keep-clear"
                  f" areas round the holes, screw heads and windows (most: {worst:.4f} mm2)",
                  f"{name}: copper where none may be: " + "; ".join(bad))
        bad = []
        a = area(minus(cu, least_inside))
        if a > COPPER_TOL:
            bad.append(f"{a:.4f} mm2 within {em:g} mm of the outline (copper_edge_min)")
        for ref, region in walls:
            a = area(inter(cu, region))
            if a > COPPER_TOL:
                bad.append(f"{a:.4f} mm2 within {hm:g} mm of the wall of hole {ref} (copper_hole_min)")
        rep.check(not bad, "L04", f"{name}: whatever the clearances chosen, no copper within {em:g} mm of the outline or"
                  f" {hm:g} mm of a drilled wall",
                  f"{name}: copper nearer than a board may have it: " + "; ".join(bad))
        gone = area(minus(demanded, cu))
        rep.check(gone <= MISSING_TOL, "L05", f"{name}: copper covers the lid everywhere more than {slack:g} mm from a"
                  f" keep-clear area ({area(cu):.1f} mm2 of copper)",
                  f"{name}: {gone:.3f} mm2 of the lid has no copper where it is demanded (K2: light would pass)")
    f, k = b.fill[pcbnew.F_Cu], b.fill[pcbnew.B_Cu]
    differ = area(minus(f, k)) + area(minus(k, f))
    rep.check(differ <= MISSING_TOL, "L05", "the two sides carry the same copper",
              f"the two sides' copper differs by {differ:.3f} mm2 (K2: equal copper keeps the lid flat)")


# ---- L06: the solder mask ------------------------------------------------------------------------
def check_mask(rep, board, b, interface):
    expansion = board.GetDesignSettings().m_SolderMaskExpansion
    own = [fp.GetReference() for fp in board.GetFootprints() for p in fp.Pads() if p.GetLocalSolderMaskMargin() is not None]
    rep.check(expansion == 0 and not own, "L06", "a mask opening is as drawn: no mask expansion on the board or on a pad",
              f"mask expansion {pcbnew.ToMM(expansion):g} mm on the board, pads with their own margin {own}: an opening would"
              " be wider than drawn")
    windows = interface["windows"]
    for side, _, mask_layer, cu_layer in FACES:
        bad = []
        rects = []
        for d in b.mask[mask_layer]:
            if d.GetShape() == pcbnew.SHAPE_T_RECT and d.IsFilled() and d.GetWidth() == 0:
                (ax, ay), (bx_, by_) = pt(d.GetStart()), pt(d.GetEnd())
                rects.append((min(ax, bx_), min(ay, by_), max(ax, bx_), max(ay, by_)))
            else:
                bad.append(f"a {name_of(board, d)} that is not a filled rectangle")
        for w in windows:
            hit = next((r for r in rects if all(near(a, c) for a, c in zip(r, w["rect"]))), None)
            if hit is None:
                bad.append(f"no opening on window {'/'.join(w['refs'])} {tuple(w['rect'])}")
            else:
                rects.remove(hit)
        bad += [f"an opening {r} that is no window of the interface" for r in rects]
        rep.check(not bad, "L06", f"{side}: the mask is open on each of the {len(windows)} windows, exactly the interface's"
                  " rectangles, and nowhere else but the holes",
                  f"{side} mask: " + "; ".join(bad))
        opening = pcbnew.SHAPE_POLY_SET()
        for d in b.mask[mask_layer]:
            d.TransformShapeToPolygon(opening, mask_layer, 0, mm(0.002), pcbnew.ERROR_OUTSIDE)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                if p.IsOnLayer(mask_layer):
                    at = pt(p.GetPosition())
                    r = pcbnew.ToMM(max(p.GetSize(pcbnew.F_Cu).x, p.GetSize(pcbnew.F_Cu).y)) / 2 + pcbnew.ToMM(expansion)
                    opening.BooleanAdd(disc(at[0], at[1], r, outside=True))
        bare = area(inter(opening, b.fill[cu_layer]))
        rep.check(bare <= COPPER_TOL, "L06", f"{side}: no copper under a mask opening ({area(opening):.2f} mm2 of openings):"
                  " nothing is bare",
                  f"{side}: {bare:.4f} mm2 of copper lies under a mask opening (K3: no bare copper)")


# ---- L07: the legend table's own rules -----------------------------------------------------------
def check_legend_rules(rep, params, legend, interface):
    bad = []
    seen = set()
    for row in legend:
        tag = f"row {row['label']}"
        if row["label"] in seen:
            bad.append(f"{tag}: the label is used twice")
        seen.add(row["label"])
        if row["side"] not in spec.SIDES:
            bad.append(f"{tag}: side {row['side']!r}, want one of {spec.SIDES}")
        if not row["text"] or any(not 0x20 <= ord(ch) <= 0x7E for ch in row["text"]):
            bad.append(f"{tag}: the text {row['text']!r} is empty or not printable ASCII (CLAUDE.md 6: Latin, no CJK)")
        if row["height"] < params["text_min_h"] - 1e-9:
            bad.append(f"{tag}: height {row['height']:g} mm, below {params['text_min_h']:g} (text_min_h)")
        least = max(params["stroke_min"], row["height"] / params["stroke_ratio"])
        if row["stroke"] < least - 1e-9:
            bad.append(f"{tag}: stroke {row['stroke']:g} mm, below {least:.3f} (stroke_min, and height / stroke_ratio)")
        try:
            spec.label_point(interface, row)
        except ValueError as e:
            bad.append(str(e))
    if params["ring_stroke"] < params["stroke_min"] - 1e-9:
        bad.append(f"ring_stroke {params['ring_stroke']:g} mm, below {params['stroke_min']:g} (stroke_min)")
    for key in ("arrow_w", "arrow_h"):
        if params[key] < params["text_min_h"] - 1e-9:
            bad.append(f"{key} {params[key]:g} mm, below {params['text_min_h']:g} (text_min_h): too small to see")
    rep.check(not bad, "L07", f"the legend table: {len(legend)} rows, each Latin, at least {params['text_min_h']:g} mm high with a"
              f" stroke of at least max({params['stroke_min']:g}, height/{params['stroke_ratio']:g}) mm; the ring and the arrows"
              " are no finer",
              "the legend table: " + "; ".join(bad))


# ---- L08: the board carries the table, and nothing else ------------------------------------------
def check_legend_drawn(rep, board, b, params, legend, interface):
    layer_of = {"top": pcbnew.F_SilkS, "bottom": pcbnew.B_SilkS}
    bad = []
    texts = list(b.texts)
    for row in legend:
        try:
            want = spec.label_point(interface, row)
        except ValueError:
            continue                           # L07 names it
        hit = None
        for t in texts:
            at = pt(t.GetPosition())
            if t.GetText() == row["text"] and t.GetLayer() == layer_of.get(row["side"]) and near(at[0], want[0]) and near(at[1], want[1]):
                hit = t
                break
        if hit is None:
            bad.append(f"row {row['label']}: no text {row['text']!r} on the {row['side']} at {fmt(want)}")
            continue
        texts.remove(hit)
        size = hit.GetTextSize()
        wrong = []
        if not (near(pcbnew.ToMM(size.x), row["height"]) and near(pcbnew.ToMM(size.y), row["height"])):
            wrong.append(f"size {pcbnew.ToMM(size.x):g} x {pcbnew.ToMM(size.y):g}, want {row['height']:g}")
        if not near(pcbnew.ToMM(hit.GetTextThickness()), row["stroke"]):
            wrong.append(f"stroke {pcbnew.ToMM(hit.GetTextThickness()):g}, want {row['stroke']:g}")
        if hit.IsMirrored() != (row["side"] == "bottom"):
            wrong.append("mirrored on the top" if hit.IsMirrored() else "not mirrored on the bottom")
        if hit.GetHorizJustify() != pcbnew.GR_TEXT_H_ALIGN_CENTER or hit.GetVertJustify() != pcbnew.GR_TEXT_V_ALIGN_CENTER:
            wrong.append("not centred on its anchor")
        if hit.GetTextAngle().AsDegrees() != 0 or not hit.IsVisible() or hit.IsItalic() or hit.IsBold():
            wrong.append("turned, hidden, italic or bold")
        if wrong:
            bad.append(f"row {row['label']}: " + ", ".join(wrong))
    bad += [f"a text {t.GetText()!r} at {fmt(pt(t.GetPosition()))} that is no row of the table" for t in texts]
    rep.check(not bad, "L08", f"the {len(legend)} texts of the legend table are on the board, each at its place, size and"
              " stroke, and no other text", "legend texts: " + "; ".join(bad))

    bad = []
    shapes = list(b.silk)
    for port in interface["ports"]:
        s, e = spec.inward(port), spec.edge_y(interface, port)
        tip = e + s * params["arrow_tip"]
        base = tip + s * params["arrow_h"]
        want = [(port["x"], tip), (port["x"] - params["arrow_w"] / 2, base), (port["x"] + params["arrow_w"] / 2, base)]
        hit = next((d for d in shapes if d.GetLayer() == pcbnew.F_SilkS and triangle(d) and same_points(triangle(d), want)), None)
        if hit is None:
            bad.append(f"no arrow for port {port['ref']} with corners {[fmt(p) for p in want]}")
        else:
            shapes.remove(hit)
    buttons = [h for h in interface["holes"] if h["kind"] == "button"]
    for hole in buttons:
        hit = None
        for d in shapes:
            r = ring(d)
            if d.GetLayer() == pcbnew.F_SilkS and r and near(r[0][0], hole["x"]) and near(r[0][1], hole["y"]) \
                    and near(r[1], params["ring_d"] / 2) and near(r[2], params["ring_stroke"]):
                hit = d
                break
        if hit is None:
            bad.append(f"no ring of {params['ring_d']:g} mm with a {params['ring_stroke']:g} mm line round {hole['ref']}")
        else:
            shapes.remove(hit)
    bad += [f"a {name_of(board, d)} on the silkscreen that the document does not describe" for d in shapes]
    bad += [f"a {d.GetClass()} on layer {board.GetLayerName(d.GetLayer())} that the document does not describe" for d in b.other]
    shown = [f"{fp.GetReference()}.{f.GetName()}" for fp in board.GetFootprints() for f in fp.GetFields() if f.IsVisible()]
    if shown:
        bad.append(f"footprint texts that would print: {shown}")
    rep.check(not bad, "L08", f"one arrow for each of the {len(interface['ports'])} ports and one ring round each of the"
              f" {len(buttons)} button holes, as the parameters say, and no other drawing",
              "legend drawings: " + "; ".join(bad))


# ---- L09: what the legend must say, read from the ink --------------------------------------------
def check_legend_content(rep, board, b, params, interface):
    o = interface["outline"]
    depth = o["y1"] - o["y0"]
    top = [(t.GetText(), box(b.ink[id(t)])) for t in b.texts if t.GetLayer() == pcbnew.F_SilkS]
    rep.check(any(text == spec.PRODUCT for text, _ in top), "L09", f"the top names the product: {spec.PRODUCT!r}",
              f"no text {spec.PRODUCT!r} on the top (CLAUDE.md 6)")
    revision = board.GetTitleBlock().GetRevision()
    rep.check(bool(revision) and any(revision in text for text, _ in top), "L09",
              f"the top carries the board's revision, {revision}",
              f"no text on the top carries the title block's revision {revision!r} (CLAUDE.md 6)")
    triangles = [tri for tri in (triangle(d) for d in b.silk if d.GetLayer() == pcbnew.F_SilkS) if tri]
    for port in interface["ports"]:
        ref = port["ref"]
        s, e = spec.inward(port), spec.edge_y(interface, port)

        def far(y, s=s, e=e):
            return s * (y - e)                 # how far into the lid from the port's edge

        bad = []
        want = PORT_NAMES.get(ref)
        if want is None:
            rep.fail("L09", f"port {ref}: this checker knows no name for it (PORT_NAMES)")
            continue
        labels = [bx for text, bx in top if text == want]
        label_near = None
        if len(labels) != 1:
            bad.append(f"{len(labels)} texts {want!r} on the top, want 1")
        else:
            bx = labels[0]
            cx = (bx[0] + bx[2]) / 2
            lo, hi = sorted((far(bx[1]), far(bx[3])))
            label_near = lo
            if abs(cx - port["x"]) > params["port_x_tol"]:
                bad.append(f"the ink of {want!r} is centred at x = {cx:.2f}, the port is at {port['x']:g}")
            if not (0 < lo and hi < depth / 2):
                bad.append(f"{want!r} is not on the port's half of the lid")
        mine = []
        for tri in triangles:
            d = sorted(tri, key=lambda p: far(p[1]))
            if abs(d[0][0] - port["x"]) <= params["port_x_tol"] and 0 < far(d[0][1]) and far(d[2][1]) < depth / 2:
                mine.append(d)
        if len(mine) != 1:
            bad.append(f"{len(mine)} arrows at the port, want 1")
        else:
            d = mine[0]
            if not far(d[0][1]) < far(d[1][1]) - POS_TOL:
                bad.append("the arrow does not point at the edge")
            if label_near is not None and far(d[2][1]) > label_near:
                bad.append("the arrow is not between the edge and the label")
        rep.check(not bad, "L09", f"port {ref} ({port['edge']} edge, x = {port['x']:g}): {want!r} over it, and one arrow"
                  " between the label and the edge, pointing at the edge",
                  f"port {ref}: " + "; ".join(bad))
    for hole in interface["holes"]:
        if hole["kind"] == "pinhole":
            gaps = [box_gap(bx, hole["x"], hole["y"]) - hole["d"] / 2 for text, bx in top if text == PINHOLE_NAME]
            rep.check(len(gaps) == 1 and gaps[0] <= params["label_near"], "L09",
                      f"pinhole {hole['ref']}: {PINHOLE_NAME!r} beside it",
                      f"pinhole {hole['ref']}: {len(gaps)} texts {PINHOLE_NAME!r} on the top, at {[round(g, 2) for g in gaps]} mm"
                      f" from the hole's edge; want one within {params['label_near']:g} mm (REQ-BOOT-02)")
        elif hole["kind"] == "button":
            rings = [r for r in (ring(d) for d in b.silk if d.GetLayer() == pcbnew.F_SilkS) if r
                     and near(r[0][0], hole["x"]) and near(r[0][1], hole["y"]) and r[1] - r[2] / 2 > hole["d"] / 2]
            rep.check(len(rings) == 1, "L09", f"button hole {hole['ref']}: one ring round it",
                      f"button hole {hole['ref']}: {len(rings)} rings centred on it and wider than it, want 1")


# ---- L10: silkscreen clearances, measured on the ink ---------------------------------------------
def check_silk_clear(rep, board, b, params, interface):
    o = interface["outline"]
    inside = rect(o["x0"], o["y0"], o["x1"], o["y1"], grow=-params["silk_edge_min"])
    keep = [(f"hole {h['ref']}" if h["kind"] != "screw" else f"the screw head of {h['ref']}",
             disc(h["x"], h["y"], keep_radius(h, params, params["silk_hole_min"]), outside=True)) for h in interface["holes"]]
    keep += [(f"window {'/'.join(w['refs'])}", rect(*w["rect"], grow=params["silk_hole_min"])) for w in interface["windows"]]
    for side, silk_layer, _, _ in FACES:
        items = [(name_of(board, d), b.ink[id(d)]) for d in b.texts + b.silk if d.GetLayer() == silk_layer]
        bad = []
        for name, ink in items:
            if area(minus(ink, inside)) > INK_TOL:
                bad.append(f"{name} is within {params['silk_edge_min']:g} mm of the outline")
            for what, region in keep:
                if area(inter(ink, region)) > INK_TOL:
                    bad.append(f"{name} is within {params['silk_hole_min']:g} mm of {what}")
        for i, (name, ink) in enumerate(items):
            wide = grown(ink, params["silk_gap_min"])
            for other, ink2 in items[i + 1:]:
                if area(inter(wide, ink2)) > INK_TOL:
                    bad.append(f"{name} is within {params['silk_gap_min']:g} mm of {other}")
        rep.check(not bad, "L10", f"{side}: the ink of {len(items)} silkscreen items stays {params['silk_edge_min']:g} mm from"
                  f" the outline, {params['silk_hole_min']:g} mm from every hole, screw head and window, and"
                  f" {params['silk_gap_min']:g} mm from each other",
                  f"{side} silkscreen: " + "; ".join(bad))


# ---- L11: KiCad's own DRC ------------------------------------------------------------------------
def check_drc(rep, pcb, tmp):
    out = tmp / "drc.json"
    r = subprocess.run([str(CLI), "pcb", "drc", "--severity-all", "--format", "json", "-o", str(out), str(pcb)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    if not out.exists():
        rep.fail("L11", f"kicad-cli wrote no DRC report (exit {r.returncode}): {(r.stdout + r.stderr)[-300:]}")
        return
    data = json.loads(out.read_text(encoding="utf-8"))
    kinds = sorted({v.get("type", "?") for v in data.get("violations", [])})
    n, u = len(data.get("violations", [])), len(data.get("unconnected_items", []))
    rep.check(n == 0 and u == 0, "L11", "KiCad's DRC, every severity: 0 violations, 0 unconnected items",
              f"KiCad's DRC: {n} violations {kinds}, {u} unconnected items")


# ---- L12 to L16: the candidate set ---------------------------------------------------------------
def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def pdf_pages(data):
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def not_its_type(name, data):
    """Why a file of the set is not what its name says, or None."""
    if name.endswith(".zip"):
        return None if data.startswith(b"PK") else "no zip archive"
    if name.endswith(".pdf"):
        if not data.startswith(b"%PDF-"):
            return "no PDF"
        return None if pdf_pages(data) == 1 else f"{pdf_pages(data)} pages, want 1"
    if name.endswith(".png"):
        if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
            return "no PNG"
        w, h = struct.unpack(">II", data[16:24])
        return None if w >= PREVIEW_MIN_W else f"{w} x {h} px, want at least {PREVIEW_MIN_W} wide"
    return None


def gerber_ops(text):
    """[(x, y, op, arc)] of a Gerber file in mm: every point it draws to (op 1), moves to (2) or
    flashes at (3); arc is True where the statement carries an I or a J."""
    m = re.search(r"%FSLAX\d(\d)Y\d(\d)\*%", text)
    if not m or "%MOMM*%" not in text:
        raise ValueError("not a millimetre Gerber with a format statement")
    scale = 10 ** int(m.group(1))
    x = y = 0
    ops = []
    for st in re.finditer(r"^(?:G0[123])?(?:X(-?\d+))?(?:Y(-?\d+))?((?:I-?\d+)?(?:J-?\d+)?)D0([123])\*$", text, re.M):
        if st.group(1) is not None:
            x = int(st.group(1))
        if st.group(2) is not None:
            y = int(st.group(2))
        ops.append((x / scale, y / scale, int(st.group(4)), bool(st.group(3))))
    return ops


def gerber_points(text):
    """Every point a Gerber file draws to, moves to or flashes at, in mm."""
    return [(x, y) for x, y, _, _ in gerber_ops(text)]


def drawn_sides(ops):
    """The straight lines a Gerber file draws, each as a sorted pair of points rounded to 1 nm,
    or None if it draws an arc or flashes."""
    sides, at = set(), None
    for x, y, op, arc in ops:
        p = (round(x, 6), round(y, 6))
        if arc or op == 3:
            return None
        if op == 1 and at is not None and p != at:
            sides.add(tuple(sorted((at, p))))
        at = p
    return sides


def fresh_plot(pcb, tmp):
    """{name in the zip: text} of KiCad's plot of the board, made here and now."""
    g = tmp / "plot"
    for args in (PLOT_GERBERS + ["-o", str(g)], PLOT_DRILL + ["-o", f"{g}/"]):
        subprocess.run([str(CLI), *args, str(pcb)], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=600)
    if not g.is_dir():
        return {}
    return {p.name.replace(f"{spec.NICK}-", f"{spec.PREFIX}_"): p.read_bytes().decode("utf-8", "replace")
            for p in g.iterdir() if p.suffix != ".gbrjob"}


def unstamped(text):
    return STAMP.sub("<time>", text.replace("\r\n", "\n"))


def extents(pts):
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)) if pts else None


def excellon_hits(text):
    """[(x, y, diameter)] of an Excellon file in mm with decimal coordinates."""
    if "METRIC" not in text:
        raise ValueError("not a metric Excellon file")
    tools = {m.group(1): float(m.group(2)) for m in re.finditer(r"^T(\d+)C([\d.]+)$", text, re.M)}
    hits, tool = [], None
    for line in text.split("%", 1)[-1].splitlines():
        m = re.fullmatch(r"T(\d+)", line)
        if m:
            tool = m.group(1)
            continue
        m = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)", line)
        if m:
            hits.append((float(m.group(1)), float(m.group(2)), tools.get(tool)))
    return hits


def has_point(pts, x, y):
    return any(near(p[0], x) and near(p[1], y) for p in pts)


def check_outputs(rep, out, src, params, interface):
    names = sorted(p.name for p in out.iterdir()) if out.is_dir() else []
    rep.check(names == sorted(OUTPUT_FILES), "L12", f"the set holds its {len(OUTPUT_FILES)} files and nothing else",
              f"the set in {out} holds {names}, want {sorted(OUTPUT_FILES)}")
    listed = {}
    if (out / "SHA256SUMS.txt").is_file():
        for line in (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            listed[name] = digest
    actual = {n: sha(out / n) for n in names if n != "SHA256SUMS.txt"}
    wrong = sorted(n for n in set(listed) | set(actual) if listed.get(n) != actual.get(n))
    rep.check(bool(listed) and not wrong, "L12", "SHA256SUMS.txt names every other file with its SHA-256",
              f"SHA256SUMS.txt disagrees with the files: {wrong or 'it is empty or missing'}")
    man = (out / "RELEASE_MANIFEST.md").read_text(encoding="utf-8") if (out / "RELEASE_MANIFEST.md").is_file() else ""
    sources = dict(re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", man, re.M))
    current = {f"{spec.NICK}.{ext}": sha(src / f"{spec.NICK}.{ext}") for ext in ("kicad_pcb", "kicad_pro")
               if (src / f"{spec.NICK}.{ext}").is_file()}
    rep.check(bool(sources) and sources == current, "L12", "the set is made from this board: the manifest's source hashes are current",
              f"the manifest names the sources {sorted(sources)} with other hashes than the files in {src} have now:"
              " the set is stale, run make_lid_outputs.py")
    rep.check("| State | WIP |" in man and "MANUFACTURING PROHIBITED" in man, "L12", "the manifest's state is WIP",
              "the manifest does not state `| State | WIP |` and MANUFACTURING PROHIBITED")
    broken = [f"{n} ({why})" for n in names for why in [not_its_type(n, (out / n).read_bytes())] if why]
    rep.check(not broken, "L12", f"the archive is a zip, the drawing a PDF of one page, each picture a PNG at least"
              f" {PREVIEW_MIN_W} px wide",
              f"files that are not what their name says: {broken}")

    members = {}
    zpath = out / f"{spec.PREFIX}_Gerber.zip"
    try:
        with zipfile.ZipFile(io.BytesIO(zpath.read_bytes())) as z:
            # kicad-cli ends its lines with CR LF on Windows; the parsers below read LF
            members = {n: z.read(n).decode("utf-8", "replace").replace("\r\n", "\n") for n in z.namelist()}
    except (OSError, zipfile.BadZipFile) as e:
        rep.fail("L13", f"the Gerber zip does not open: {e}")
    rep.check(sorted(members) == sorted(GERBER_MEMBERS), "L13",
              f"the Gerber zip holds its {len(GERBER_MEMBERS)} files: 2 copper, 2 silkscreen, 2 mask, the outline, 2 drill, 2 drill maps",
              f"the Gerber zip holds {sorted(members)}, want {sorted(GERBER_MEMBERS)}")

    def points(suffix):
        try:
            return gerber_points(members.get(f"{spec.PREFIX}_{suffix}", ""))
        except ValueError:
            return []

    o = interface["outline"]
    want = (o["x0"], o["y0"], o["x1"], o["y1"])
    got = extents(points("Edge_Cuts.gm1"))
    corners = [(o["x0"], o["y0"]), (o["x1"], o["y0"]), (o["x1"], o["y1"]), (o["x0"], o["y1"])]
    want_sides = {tuple(sorted(((round(a[0], 6), round(a[1], 6)), (round(b[0], 6), round(b[1], 6)))))
                  for a, b in zip(corners, corners[1:] + corners[:1])}
    try:
        sides = drawn_sides(gerber_ops(members.get(f"{spec.PREFIX}_Edge_Cuts.gm1", "")))
    except ValueError:
        sides = None
    rep.check(sides == want_sides, "L13",
              f"the outline Gerber draws the four sides of the rectangle {fmt(want[:2])} to {fmt(want[2:])} and nothing"
              " else: the interface's outline in the interface's frame",
              f"the outline Gerber's extents are {got}, want {want}; "
              + ("it draws an arc, a flash or nothing readable" if sides is None else
                 f"lines drawn that are no side of the rectangle: {sorted(sides - want_sides)}; sides not drawn:"
                 f" {sorted(want_sides - sides)}") + ": wrong origin or wrong outline")
    ec = params["edge_clear"]
    want_cu = (o["x0"] + ec, o["y0"] + ec, o["x1"] - ec, o["y1"] - ec)
    for suffix in ("F_Cu.gtl", "B_Cu.gbl"):
        got = extents(points(suffix))
        rep.check(got is not None and all(near(a, w) for a, w in zip(got, want_cu)), "L13",
                  f"{suffix}: the copper runs to {ec:g} mm from the outline on every side",
                  f"{suffix}: the copper's extents are {got}, want {want_cu}")
    for suffix in ("F_Mask.gts", "B_Mask.gbs"):
        pts = points(suffix)
        lost = ["/".join(w["refs"]) for w in interface["windows"]
                if not all(has_point(pts, x, y) for x in w["rect"][0::2] for y in w["rect"][1::2])]
        lost += [h["ref"] for h in interface["holes"] if not has_point(pts, h["x"], h["y"])]
        rep.check(bool(pts) and not lost, "L13", f"{suffix}: an opening at the four corners of each window and at every hole",
                  f"{suffix}: no opening found for {lost}")

    def hits(suffix):
        try:
            return excellon_hits(members.get(f"{spec.PREFIX}_{suffix}", ""))
        except ValueError:
            return None

    npth, pth = hits("NPTH.drl"), hits("PTH.drl")
    want_holes = [(h["x"], h["y"], h["d"]) for h in interface["holes"]]
    same = npth is not None and len(npth) == len(want_holes) and all(
        any(near(a[0], w[0]) and near(a[1], w[1]) and a[2] is not None and near(a[2], w[2]) for a in npth) for w in want_holes)
    rep.check(same, "L14", f"the unplated drill file holds the interface's {len(want_holes)} holes, each at its place and diameter",
              f"the unplated drill file holds {npth}, want {want_holes}")
    rep.check(pth == [], "L14", "the plated drill file holds no hole", f"the plated drill file holds {pth}, want none (K4)")

    try:
        drc = json.loads((out / f"{spec.PREFIX}_DRC.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        rep.fail("L15", f"the set's DRC report does not read: {e}")
        return
    n, u = len(drc.get("violations", [])), len(drc.get("unconnected_items", []))
    rep.check(n == 0 and u == 0 and drc.get("source") == f"{spec.NICK}.kicad_pcb", "L15",
              "the set's DRC report is this board's: 0 violations, 0 unconnected items",
              f"the set's DRC report: {n} violations, {u} unconnected items, source {drc.get('source')!r}")


def check_plot(rep, out, pcb, tmp):
    """L16: the zip's files against a plot made here from the board that L02 to L10 measured."""
    members = {}
    try:
        with zipfile.ZipFile(io.BytesIO((out / f"{spec.PREFIX}_Gerber.zip").read_bytes())) as z:
            members = {n: z.read(n).decode("utf-8", "replace") for n in z.namelist()}
    except (OSError, zipfile.BadZipFile):
        pass                                   # L13 names it
    plot = fresh_plot(pcb, tmp)
    differ = sorted(n for n in set(plot) | set(members) if unstamped(plot.get(n, "")) != unstamped(members.get(n, "")))
    rep.check(bool(plot) and not differ, "L16",
              f"the Gerber zip's {len(plot)} files are KiCad's plot of this board, text for text but the creation times",
              "files of the Gerber zip that are not KiCad's plot of this board: "
              + (", ".join(n[len(spec.PREFIX) + 1:] if n.startswith(spec.PREFIX) else n for n in differ)
                 if plot else "kicad-cli plotted nothing to compare with"))


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--doc", type=pathlib.Path, default=spec.DOC)
    ap.add_argument("--interface", type=pathlib.Path, default=spec.INTERFACE)
    ap.add_argument("--src", type=pathlib.Path, default=spec.SOURCE)
    ap.add_argument("--outputs", type=pathlib.Path)
    ap.add_argument("--no-drc", action="store_true")
    args = ap.parse_args(argv[1:])
    rep = Report()

    def done():
        print(f"lid check: {rep.count} checks, {rep.failed} failed")
        return 1 if rep.failed else 0

    try:
        params, legend = spec.load_doc(args.doc)
        interface = spec.load_interface(args.interface)
    except (OSError, ValueError, KeyError) as e:
        rep.fail("L07", f"the document or the interface does not read: {e}")
        return done()
    pcb = args.src / f"{spec.NICK}.kicad_pcb"
    with tempfile.TemporaryDirectory(prefix="lidcheck-") as tmp:
        tmp = pathlib.Path(tmp)
        board = None
        try:
            for ext in ("kicad_pcb", "kicad_pro"):
                shutil.copy2(args.src / f"{spec.NICK}.{ext}", tmp / f"{spec.NICK}.{ext}")
            board = pcbnew.LoadBoard(str(tmp / pcb.name))
        except Exception as e:                 # pcbnew raises its own types on a file it cannot read
            rep.fail("L02", f"the board does not load from {args.src}: {str(e).splitlines()[0] if str(e) else type(e).__name__}")
        if board is None:
            if not rep.failed:
                rep.fail("L02", f"the board does not load from {args.src}")
            return done()
        b = read_board(board, board.GetDesignSettings().m_MaxError)
        check_identity(rep, board, params, legend, args.interface)
        check_files(rep, args.src)
        check_board(rep, board, b, interface)
        check_holes(rep, board, interface)
        check_copper(rep, b, interface, params)
        check_mask(rep, board, b, interface)
        check_legend_rules(rep, params, legend, interface)
        check_legend_drawn(rep, board, b, params, legend, interface)
        check_legend_content(rep, board, b, params, interface)
        check_silk_clear(rep, board, b, params, interface)
        if not args.no_drc:
            check_drc(rep, tmp / pcb.name, tmp)
        if args.outputs:
            check_outputs(rep, args.outputs, args.src, params, interface)
            check_plot(rep, args.outputs, tmp / pcb.name, tmp)
    return done()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
