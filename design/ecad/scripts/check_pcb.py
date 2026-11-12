"""Check the placed board against the placement document (issue #6 P3; CLAUDE.md 5.2, 8).

Run with KiCad's own Python from the repository root (make_pcb.py runs it after it writes
the board):

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_pcb.py
        [--src DIR] [--lib DIR] [--doc FILE] [--capture FILE] [--reports DIR]

--src holds the KiCad project (default design/ecad/source), --lib the project libraries
(default design/ecad/libraries), --doc the placement document (default
design/ecad/PLACEMENT_Rev0.5.md) and --capture the capture list (default
design/circuit/CIRCUIT_DESIGN_Rev0.5_netlist.md); the tests pass corrupted copies. With
--reports, the DRC report and the exported netlist are kept there. This file reads the
document with its own parser, not make_pcb.py's, and the board with pcbnew.

Board frame: origin at the board's lower-left corner, x right, y up, in mm; a board point
(x, y) is at (50 + x, 122 - y) on KiCad's sheet. Courtyards are taken as the bounding box of
each courtyard outline.

 1. Document: every region and keepout lies on the board; regions do not overlap, except an
    `under` region, which lies inside exactly one `module` region; no keepout overlaps a
    region; every part names an existing region; every under-list height is at most
    UNDER_MAX_H (1.5 mm, the OI-23 study).
 2. Identity (`kicad-cli sch export netlist`): the board's footprints are exactly the
    netlist's components, each with the netlist's footprint, Value, sheet path, fields
    (hidden), BOM exclusion and, pad by pad, net; a pad with no netlist node has no net.
 3. Position: each footprint at the document's x, y (within 0.0005 mm) and rotation, on
    F.Cu, not flipped; each channel-B part at its channel-A part + dx, same rotation.
 4. Top only (REQ-MFG-01): no pad on B.Paste, no SMD pad on B.Cu, no footprint text or
    graphic and no courtyard on a B.* layer.
 5. Outline: Edge.Cuts spans (0, 0)-(100, 72) (D24); every courtyard lies on the board,
    except a USB-C module's receptacle, which may pass the edge its module stands on by the
    library's overhang (1.06 mm) plus COURTYARD_MARGIN; every module outline
    (library.json: origin_in_module, size) lies on the board.
 6. Regions: each part's courtyard lies inside its region; each module's outline is its
    module region.
 7. Keepouts: no courtyard enters a keepout.
 8. Under the modules: a courtyard that enters a module's outline belongs to a footprint on
    the under list, has only SMD pads and its part's region is an `under` region inside that
    outline.
 9. Mechanics: J2 and J3 (OUT A/B) stand on the front edge, J1 and J4 (HOST, 5 V input) on
    the back edge; J2-J3 pitch >= 18 mm (REQ-MECH-02); four mounting holes, one in each
    7 x 7 mm corner; >= 3 fiducials, each a 1.0 mm pad with a 2.0 mm mask opening, not on
    one line (CLAUDE.md 10.3).
10. MAU104: its courtyard is >= SEP_MAU (6.0 mm, the OI-23 study) from every courtyard of a
    part in AFE_A, AFE_B, ADC, ADCSUP or REF.
11. Notes, in the capture list and in the document: "at X pin N" (also "pins N/M",
    "pad N") means the part has a pad on that pin's net within AT_MM (3.0 mm, centre to
    centre) of it; "at X", "next to X" and "after X" mean the two courtyards are within
    NEAR_MM (3.0 mm). A channel-table note is checked for channel B too, its designators
    mapped by the table.
12. DRC (`kicad-cli pcb drc --schematic-parity --severity-all`): no violation of any
    severity and no schematic-parity item. Unconnected items are counted, not failed:
    routing is check_routing.py's (P4).
Exit status: 0 = every check passed; 1 = at least one failed. Each failure prints as
`FAIL <who>: <what>`.

What it CANNOT see:
- whether the placement is good: routability, return paths and thermal spread are P4's.
  Check 11 measures distances, not trace lengths; "toward X" in a note is a direction and is
  not checked, and a note without "at", "next to" or "after" is not checked either.
- part heights: the under list holds the study's planning values, not measured bodies
  (V-MECH-01 measures the built board), and only the footprint name links a part to them.
- footprint correctness: check_libraries.py (P1) checks the lands against the datasheets.
  Courtyards are bounding boxes here, which is exact for the rectangular ones and
  conservative for containment; DRC compares the true outlines with each other.
- the mating plug's overmold and the enclosure (V-MECH-01, CLAUDE.md 7).
"""
import argparse
import importlib.util
import json
import math
import pathlib
import re
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
KICAD = pathlib.Path(sys.executable).resolve().parents[1]
CLI = KICAD / "bin" / "kicad-cli.exe"
ORIGIN = (50.0, 122.0)          # the board's lower-left corner on the sheet (make_project.py)
BOARD = (100.0, 72.0)           # D24
EDGE_TOL = 0.03                 # half the 0.05 mm Edge.Cuts line, plus rounding
POS_TOL = 0.0005
AT_MM = 3.0
NEAR_MM = 3.0
UNDER_MAX_H = 1.5               # OI-23 study: UNDER_MAX_H
SEP_MAU = 6.0                   # OI-23 study: SEP_MAU
PITCH_MIN = 18.0                # REQ-MECH-02
COURTYARD_MARGIN = 0.05         # the library draws the receptacle courtyard 0.045 mm out
CORNER = 7.0                    # the corner keepout of each M2 insert (D21)
ANALOG = ("AFE_A", "AFE_B", "ADC", "ADCSUP", "REF")
FRONT, BACK = ("J2", "J3"), ("J1", "J4")
MODULE_FP = "Module_Akizuki_AE-USB2.0-TYPE-C"
MAU_FP = "Converter_DCDC_Minmax_MAU104_SIP"
KINDS = {"module", "under", "block", "mark"}
B_LAYERS = ("B_SilkS", "B_Fab", "B_CrtYd", "B_Paste", "B_Adhes", "B_Mask", "B_Cu")
PIN_RE = re.compile(r"\bat ([A-Z]+\d+) (?:pins? ((?:\d+/)*\d+)|pad (\d+))\b")
PART_RE = re.compile(r"\b(at|next to|after) ([A-Z]+\d+)\b(?! pins? \d| pad \d)")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")


class Report:
    def __init__(self):
        self.fails, self.count = [], 0

    def check(self, cond, who, what):
        self.count += 1
        if not cond:
            self.fails.append(f"FAIL {who}: {what}")
        return cond


# ---- geometry (board frame) --------------------------------------------------------------
def frame(vec):
    return pcbnew.ToMM(vec.x) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(vec.y)


def box(bb):
    """A pcbnew BOX2I on the sheet as (x0, y0, x1, y1) in the board frame."""
    return (pcbnew.ToMM(bb.GetLeft()) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(bb.GetBottom()),
            pcbnew.ToMM(bb.GetRight()) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(bb.GetTop()))


def courtyard(fp, layer=pcbnew.F_CrtYd):
    s = fp.GetCourtyard(layer)
    return [box(s.Outline(i).BBox()) for i in range(s.OutlineCount())]


def inside(r, outer, tol=1e-6):
    return (r[0] >= outer[0] - tol and r[1] >= outer[1] - tol and
            r[2] <= outer[2] + tol and r[3] <= outer[3] + tol)


def overlap(a, b, tol=1e-6):
    """True when the two rectangles share area (touching edges do not)."""
    return a[0] < b[2] - tol and b[0] < a[2] - tol and a[1] < b[3] - tol and b[1] < a[3] - tol


def gap(rects_a, rects_b):
    best = math.inf
    for a in rects_a:
        for b in rects_b:
            dx = max(b[0] - a[2], a[0] - b[2], 0.0)
            dy = max(b[1] - a[3], a[1] - b[3], 0.0)
            best = min(best, math.hypot(dx, dy))
    return best


def module_outline(fp, params):
    """The module board's rectangle (library.json) placed as the footprint is."""
    ox, oy = params["origin_in_module"]
    w, h = params["size"]
    x0, y0 = frame(fp.GetPosition())
    t = math.radians(fp.GetOrientationDegrees())
    pts = []
    for lx, ly in ((-ox, -oy), (w - ox, -oy), (w - ox, h - oy), (-ox, h - oy)):
        sx_ = lx * math.cos(t) + ly * math.sin(t)          # KiCad local, y down, CCW on screen
        sy_ = -lx * math.sin(t) + ly * math.cos(t)
        pts.append((x0 + sx_, y0 - sy_))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (round(min(xs), 4), round(min(ys), 4), round(max(xs), 4), round(max(ys), 4))


# ---- the documents (own parser) --------------------------------------------------------------
def marked_blocks(text):
    """Yield (kind, argument, [row dict]) for each `<!-- kind:begin ... -->` table."""
    for m in re.finditer(r"<!-- (\w+):begin(?: ([^>]*?))? -->\n(.*?)<!-- \1:end -->", text, re.S):
        lines = [ln for ln in m.group(3).splitlines() if ln.startswith("|")]
        head = [c.strip() for c in lines[0].strip()[1:-1].split("|")]
        rows = []
        for ln in lines[2:]:
            cells = [c.strip() for c in ln.strip()[1:-1].split("|")]
            if len(cells) != len(head):
                raise SystemExit(f"{m.group(1)}: {len(cells)} cells, header {len(head)}: {ln}")
            rows.append(dict(zip(head, cells)))
        yield m.group(1), m.group(2) or "", rows


def read_doc(path):
    regions, keepouts, under, parts, pairs, dx = {}, {}, {}, {}, {}, None
    for kind, arg, rows in marked_blocks(path.read_text(encoding="utf-8")):
        if kind == "regions":
            for r in rows:
                x, y, w, h = (float(r[k]) for k in ("x", "y", "w", "h"))
                regions[r["Region"]] = dict(kind=r["Kind"], rect=(x, y, x + w, y + h))
        elif kind == "keepouts":
            for r in rows:
                x, y, w, h = (float(r[k]) for k in ("x", "y", "w", "h"))
                keepouts[r["Keepout"]] = (x, y, x + w, y + h)
        elif kind == "under":
            under.update({r["Footprint"]: float(r["Height (mm)"]) for r in rows})
        elif kind in ("place", "channel"):
            if kind == "channel":
                dx = float(dict(a.split("=", 1) for a in arg.split())["dx"])
            for r in rows:
                refs = [(r["Ref"], 0.0, "")] if kind == "place" else \
                       [(r["Ref A"], 0.0, "A"), (r["Ref B"], dx, "B")]
                for ref, off, ch in refs:
                    if ref in parts:
                        raise SystemExit(f"{path.name}: {ref} placed twice")
                    parts[ref] = dict(x=float(r["x"]) + off, y=float(r["y"]), rot=int(r["Rot"]),
                                      region=r["Region"].replace("{x}", ch), note=r["Note"],
                                      channel=ch)
                if kind == "channel":
                    pairs[r["Ref A"]] = r["Ref B"]
    return regions, keepouts, under, parts, pairs, dx


def read_capture_notes(path):
    """[(ref, note, {designator map})] from the capture list's part tables."""
    blocks = [rows for kind, _, rows in marked_blocks(path.read_text(encoding="utf-8")) if kind == "netlist"]
    pairs = {r["Ref A"]: r["Ref B"] for rows in blocks for r in rows if "Ref A" in r}
    out = []
    for r in (r for rows in blocks for r in rows):
        if "Ref A" in r:
            out += [(r["Ref A"], r["Note"], {}), (r["Ref B"], r["Note"], pairs)]
        else:
            out.append((r["Ref"], r["Note"], {}))
    return out


# ---- the netlist ------------------------------------------------------------------------------
def run(args):
    r = subprocess.run([str(CLI), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600)
    return r.returncode, r.stdout + r.stderr


def read_netlist(path):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    comps = {}
    for c in sx.walk(sx.first(tree, "components"), "comp"):
        props = {sx.first(p, "name")[1] for p in sx.find(c, "property")}
        fields = {f[1][1]: f[2] for f in sx.find(sx.first(c, "fields") or [], "field") if len(f) > 2}
        sheet = sx.first(sx.first(c, "sheetpath"), "tstamps")[1]
        comps[sx.first(c, "ref")[1]] = dict(
            value=sx.first(c, "value")[1], footprint=sx.first(c, "footprint")[1], fields=fields,
            bom_excluded="exclude_from_bom" in props, path=sheet + sx.first(c, "tstamps")[1])
    pins = {}
    for n in sx.find(sx.first(tree, "nets"), "net"):
        for node in sx.find(n, "node"):
            pins[(sx.first(node, "ref")[1], sx.first(node, "pin")[1])] = sx.first(n, "name")[1]
    return comps, pins


# ---- checks ---------------------------------------------------------------------------------
def check_document(rep, regions, keepouts, under, parts):
    board = (0.0, 0.0) + BOARD
    for name, r in regions.items():
        rep.check(r["kind"] in KINDS, name, f"kind {r['kind']!r} is not one of {sorted(KINDS)}")
        rep.check(inside(r["rect"], board), name, f"region {r['rect']} is not on the board")
    names = sorted(regions)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra, rb = regions[a], regions[b]
            if not overlap(ra["rect"], rb["rect"]):
                continue
            nested = any(u["kind"] == "under" and m["kind"] == "module" and inside(u["rect"], m["rect"])
                         for u, m in ((ra, rb), (rb, ra)))
            rep.check(nested, f"{a}/{b}", "regions overlap")
    for name, r in regions.items():
        if r["kind"] == "under":
            hosts = [m for m, q in regions.items() if q["kind"] == "module" and inside(r["rect"], q["rect"])]
            rep.check(len(hosts) == 1, name, f"lies inside {len(hosts)} module regions: {hosts}")
    for name, k in keepouts.items():
        rep.check(inside(k, board), name, f"keepout {k} is not on the board")
        for rname, r in regions.items():
            rep.check(not overlap(k, r["rect"]), name, f"keepout overlaps region {rname}")
    for fp_name, h in under.items():
        rep.check(h <= UNDER_MAX_H, fp_name, f"under-list height {h} mm > {UNDER_MAX_H} mm")
    for ref, p in parts.items():
        rep.check(p["region"] in regions, ref, f"region {p['region']} does not exist")
        rep.check(p["rot"] in (0, 90, 180, 270), ref, f"rotation {p['rot']}")


def check_identity(rep, fps, comps, pins):
    rep.check(set(fps) == set(comps), "board",
              f"not on the board: {sorted(set(comps) - set(fps))}; not in the netlist: "
              f"{sorted(set(fps) - set(comps))}")
    for ref in sorted(set(fps) & set(comps)):
        fp, c = fps[ref], comps[ref]
        rep.check(fp.GetFPIDAsString() == c["footprint"], ref,
                  f"footprint {fp.GetFPIDAsString()}, netlist {c['footprint']}")
        rep.check(fp.GetValue() == c["value"], ref, f"Value {fp.GetValue()!r}, netlist {c['value']!r}")
        want = pcbnew.KIID_PATH(c["path"]).AsString()
        rep.check(fp.GetPath().AsString() == want, ref, f"path {fp.GetPath().AsString()}, netlist {want}")
        fields = {f.GetName(): f for f in fp.GetFields()}
        for name, text in c["fields"].items():
            if name == "Footprint":
                continue
            f = fields.get(name)
            if rep.check(f is not None and f.GetText() == text, ref,
                         f"field {name} = {f.GetText() if f else None!r}, netlist {text!r}"):
                rep.check(not f.IsVisible(), ref, f"field {name} is visible")
        excluded = bool(fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM)
        rep.check(excluded == c["bom_excluded"], ref, f"BOM exclusion {excluded}, netlist {c['bom_excluded']}")
        numbers = set()
        for pad in fp.Pads():
            num = pad.GetNumber()
            numbers.add(num)
            want = pins.get((ref, num))
            got = pad.GetNetname() if pad.GetNetCode() > 0 else None
            rep.check(got == want, f"{ref}.{num or '(unnumbered)'}", f"net {got}, netlist {want}")
        missing = sorted(n for r, n in pins if r == ref and n not in numbers)
        rep.check(not missing, ref, f"netlist pins with no pad: {missing}")


def check_position(rep, fps, parts, pairs, dx):
    for ref, p in sorted(parts.items()):
        fp = fps.get(ref)
        if fp is None:
            continue
        x, y = frame(fp.GetPosition())
        rep.check(abs(x - p["x"]) <= POS_TOL and abs(y - p["y"]) <= POS_TOL, ref,
                  f"at ({x:.4f}, {y:.4f}), document ({p['x']}, {p['y']})")
        rot = round(fp.GetOrientationDegrees()) % 360
        rep.check(rot == p["rot"], ref, f"rotation {rot}, document {p['rot']}")
        rep.check(fp.GetLayer() == pcbnew.F_Cu and not fp.IsFlipped(), ref, "not on F.Cu")
    for a, b in sorted(pairs.items()):
        fa, fb = fps.get(a), fps.get(b)
        if fa is None or fb is None:
            continue
        (xa, ya), (xb, yb) = frame(fa.GetPosition()), frame(fb.GetPosition())
        same = round(fa.GetOrientationDegrees()) % 360 == round(fb.GetOrientationDegrees()) % 360
        rep.check(abs(xb - xa - dx) <= POS_TOL and abs(yb - ya) <= POS_TOL and same, f"{a}/{b}",
                  f"channel B is at ({xb - xa:+.4f}, {yb - ya:+.4f}) from A, want ({dx:+}, 0), same rotation")


def check_top_only(rep, fps):
    b_layers = {getattr(pcbnew, n) for n in B_LAYERS}
    for ref, fp in sorted(fps.items()):
        for pad in fp.Pads():
            ls = pad.GetLayerSet()
            rep.check(not ls.Contains(pcbnew.B_Paste), f"{ref}.{pad.GetNumber()}", "pad on B.Paste")
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                rep.check(not ls.Contains(pcbnew.B_Cu), f"{ref}.{pad.GetNumber()}", "SMD pad on B.Cu")
        items = list(fp.GraphicalItems()) + list(fp.GetFields())
        bad = sorted({pcbnew.LayerName(i.GetLayer()) for i in items if i.GetLayer() in b_layers})
        rep.check(not bad, ref, f"items on {bad}")
        rep.check(fp.GetCourtyard(pcbnew.B_CrtYd).OutlineCount() == 0, ref, "a courtyard on B.CrtYd")


def check_outline(rep, board, fps, modules):
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    bb = box(board.GetBoardEdgesBoundingBox())
    want = (0.0, 0.0) + BOARD
    rep.check(len(edges) == 1 and all(abs(g - w) <= EDGE_TOL for g, w in zip(bb, want)), "Edge.Cuts",
              f"{len(edges)} shape(s) spanning {tuple(round(v, 3) for v in bb)}, want {want}")
    board_r = (0.0, 0.0) + BOARD
    for ref, fp in sorted(fps.items()):
        rects = courtyard(fp)
        rep.check(bool(rects), ref, "no courtyard")
        if ref not in modules:
            for r in rects:
                rep.check(inside(r, board_r), ref, f"courtyard {tuple(round(v, 3) for v in r)} leaves the board")
            continue
        outline, params = modules[ref]
        rep.check(inside(outline, board_r), ref, f"module outline {outline} leaves the board")
        room = params["overhang"] + COURTYARD_MARGIN
        lo = -room if outline[1] <= 1e-6 else 0.0
        hi = BOARD[1] + room if outline[3] >= BOARD[1] - 1e-6 else BOARD[1]
        for r in rects:
            rep.check(inside(r, (0.0, lo, BOARD[0], hi)), ref,
                      f"courtyard {tuple(round(v, 3) for v in r)} passes the edge by more than {room:.2f} mm")


def check_regions(rep, fps, parts, regions, modules):
    for ref, p in sorted(parts.items()):
        fp, reg = fps.get(ref), regions.get(p["region"])
        if fp is None or reg is None:
            continue
        if ref in modules:
            outline = modules[ref][0]
            rep.check(reg["kind"] == "module" and all(abs(a - b) <= 1e-3 for a, b in zip(outline, reg["rect"])),
                      ref, f"module outline {outline} is not region {p['region']} {reg['rect']}")
            continue
        rep.check(reg["kind"] != "module", ref, f"a part in module region {p['region']}")
        for r in courtyard(fp):
            rep.check(inside(r, reg["rect"]), ref,
                      f"courtyard {tuple(round(v, 3) for v in r)} leaves region {p['region']} {reg['rect']}")


def check_keepouts(rep, fps, keepouts):
    for ref, fp in sorted(fps.items()):
        for name, k in keepouts.items():
            rep.check(not any(overlap(r, k) for r in courtyard(fp)), ref, f"courtyard enters keepout {name}")


def check_under(rep, fps, parts, regions, under, modules):
    for mref, (outline, _) in sorted(modules.items()):
        for ref, fp in sorted(fps.items()):
            if ref == mref or not any(overlap(r, outline) for r in courtyard(fp)):
                continue
            name = fp.GetFPID().GetLibItemName().wx_str()
            rep.check(name in under, ref, f"under {mref}, but {name} is not on the under list")
            smd = all(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in fp.Pads())
            rep.check(smd, ref, f"under {mref} with a through-hole or NPTH pad")
            reg = regions.get(parts.get(ref, {}).get("region"))
            rep.check(reg is not None and reg["kind"] == "under" and inside(reg["rect"], outline), ref,
                      f"under {mref}, but its region is not an under region of {mref}")


def check_mechanics(rep, fps, modules):
    for refs, edge, y in ((FRONT, "front", 0.0), (BACK, "back", BOARD[1])):
        for ref in refs:
            if ref in modules:
                o = modules[ref][0]
                rep.check(abs((o[1] if edge == "front" else o[3]) - y) <= 1e-3, ref,
                          f"module outline {o} does not stand on the {edge} edge")
    if "J2" in modules and "J3" in modules:
        pitch = abs(modules["J3"][0][0] - modules["J2"][0][0])
        rep.check(pitch >= PITCH_MIN, "J2/J3", f"pitch {pitch:.2f} mm < {PITCH_MIN} mm")
    holes = {ref: frame(fp.GetPosition()) for ref, fp in fps.items()
             if fp.GetFPID().GetLibItemName().wx_str().startswith("MountingHole")}
    corners = set()
    for ref, (x, y) in holes.items():
        cx = 0 if x <= CORNER else (1 if x >= BOARD[0] - CORNER else None)
        cy = 0 if y <= CORNER else (1 if y >= BOARD[1] - CORNER else None)
        rep.check(cx is not None and cy is not None, ref, f"hole at ({x:.2f}, {y:.2f}) is in no corner")
        corners.add((cx, cy))
    rep.check(len(holes) == 4 and corners == {(0, 0), (0, 1), (1, 0), (1, 1)}, "holes",
              f"{len(holes)} mounting holes in corners {sorted(c for c in corners if None not in c)}")
    fids = {ref: fp for ref, fp in fps.items()
            if fp.GetFPID().GetLibItemName().wx_str().startswith("Fiducial")}
    for ref, fp in sorted(fids.items()):
        pads = list(fp.Pads())
        ok = len(pads) == 1
        if ok:
            p = pads[0]
            size = (pcbnew.ToMM(p.GetSize().x), pcbnew.ToMM(p.GetSize().y))
            margin = pcbnew.ToMM(p.GetLocalSolderMaskMargin() or 0)
            ok = all(abs(s - 1.0) <= 1e-6 for s in size) and abs(size[0] + 2 * margin - 2.0) <= 1e-6
        rep.check(ok, ref, "not one 1.0 mm pad with a 2.0 mm mask opening")
    pts = [frame(fp.GetPosition()) for fp in fids.values()]
    area = max((abs((b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])) / 2
                for i, a in enumerate(pts) for j, b in enumerate(pts) if j > i
                for k, c in enumerate(pts) if k > j), default=0.0)
    rep.check(len(fids) >= 3 and area > 100.0, "fiducials",
              f"{len(fids)} fiducials spanning {area:.1f} mm^2 (want >= 3, not on one line)")


def check_mau(rep, fps, parts):
    mau = [ref for ref, fp in fps.items() if fp.GetFPID().GetLibItemName().wx_str() == MAU_FP]
    if not rep.check(len(mau) == 1, "MAU104", f"{len(mau)} MAU104 footprints"):
        return
    rm = courtyard(fps[mau[0]])
    for ref, p in sorted(parts.items()):
        if p["region"] in ANALOG and ref in fps:
            g = gap(rm, courtyard(fps[ref]))
            rep.check(g >= SEP_MAU, ref, f"{g:.2f} mm from the MAU104 {mau[0]} (want >= {SEP_MAU} mm)")


def check_notes(rep, fps, notes):
    n = 0
    for src, ref, note, mapping in notes:
        if ref not in fps:
            continue
        for m in PIN_RE.finditer(note):
            other = mapping.get(m.group(1), m.group(1))
            who = f"{ref} ({src})"
            if not rep.check(other in fps, who, f"note {note!r}: no {other} on the board"):
                continue
            n += 1
            for num in (m.group(2) or m.group(3)).split("/"):
                pin = [p for p in fps[other].Pads() if p.GetNumber() == num]
                if not rep.check(pin and pin[0].GetNetCode() > 0, who, f"note {note!r}: {other} pin {num} has no net"):
                    continue
                net = pin[0].GetNetname()
                px, py = frame(pin[0].GetPosition())
                ds = [math.hypot(*(a - b for a, b in zip(frame(q.GetPosition()), (px, py))))
                      for q in fps[ref].Pads() if q.GetNetCode() > 0 and q.GetNetname() == net]
                d = min(ds) if ds else math.inf
                rep.check(d <= AT_MM, who, f"note {note!r}: {d:.2f} mm from {other} pin {num} (want <= {AT_MM} mm)")
        for m in PART_RE.finditer(note):
            other = mapping.get(m.group(2), m.group(2))
            who = f"{ref} ({src})"
            if not rep.check(other in fps, who, f"note {note!r}: no {other} on the board"):
                continue
            n += 1
            g = gap(courtyard(fps[ref]), courtyard(fps[other]))
            rep.check(g <= NEAR_MM, who, f"note {note!r}: courtyard {g:.2f} mm from {other} (want <= {NEAR_MM} mm)")
    return n


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
        items = "; ".join(i["description"] for i in v.get("items", []))
        rep.check(False, "DRC parity", f"{v['type']}: {items}")
    rep.check(True, "DRC", "ran")
    return len(report.get("unconnected_items", []))


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "design" / "ecad" / "source")
    ap.add_argument("--lib", type=pathlib.Path, default=ROOT / "design" / "ecad" / "libraries")
    ap.add_argument("--doc", type=pathlib.Path, default=ROOT / "design" / "ecad" / "PLACEMENT_Rev0.5.md")
    ap.add_argument("--capture", type=pathlib.Path,
                    default=ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.5_netlist.md")
    ap.add_argument("--reports", type=pathlib.Path)
    a = ap.parse_args(argv[1:])
    rep = Report()
    pcb, prl = a.src / f"{NICK}.kicad_pcb", a.src / f"{NICK}.kicad_prl"
    prl_before = prl.exists()
    register = {p["id"]: p for p in json.loads((a.lib / "library.json").read_text(encoding="utf-8"))["parts"]}
    params = {p["footprint"]["name"]: p["footprint"]["params"] for p in register.values()
              if p.get("footprint", {}).get("make") == "usbc_module"}
    regions, keepouts, under, parts, pairs, dx = read_doc(a.doc)
    check_document(rep, regions, keepouts, under, parts)
    board = pcbnew.LoadBoard(str(pcb)) if pcb.exists() else None
    if board is None:
        print(f"FAIL board: pcbnew could not load {pcb}")
        print(f"{rep.count + 1} checks, {len(rep.fails) + 1} failed: FAIL")
        return 1
    fps = {}
    for fp in board.GetFootprints():
        rep.check(fp.GetReference() not in fps, fp.GetReference(), "twice on the board")
        fps[fp.GetReference()] = fp
    modules = {ref: (module_outline(fp, params[fp.GetFPID().GetLibItemName().wx_str()]),
                     params[fp.GetFPID().GetLibItemName().wx_str()])
               for ref, fp in fps.items() if fp.GetFPID().GetLibItemName().wx_str() in params}
    rep.check(set(modules) == set(FRONT + BACK), "modules", f"USB-C modules {sorted(modules)}")
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(a.reports) if a.reports else pathlib.Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        net_path = out / f"{NICK}.net"
        status, log = run(["sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(net_path),
                           str(a.src / f"{NICK}.kicad_sch")])
        if rep.check(net_path.exists(), "netlist", f"kicad-cli exported nothing (exit {status}): {log[-300:]}"):
            comps, pins = read_netlist(net_path)
            check_identity(rep, fps, comps, pins)
        rep.check(set(parts) == set(fps), "document",
                  f"on the board, not in the document: {sorted(set(fps) - set(parts))}; "
                  f"in the document, not on the board: {sorted(set(parts) - set(fps))}")
        check_position(rep, fps, parts, pairs, dx)
        check_top_only(rep, fps)
        check_outline(rep, board, fps, modules)
        check_regions(rep, fps, parts, regions, modules)
        check_keepouts(rep, fps, keepouts)
        check_under(rep, fps, parts, regions, under, modules)
        check_mechanics(rep, fps, modules)
        check_mau(rep, fps, parts)
        notes = [("capture list", ref, note, m) for ref, note, m in read_capture_notes(a.capture)]
        for ref, p in parts.items():
            m = pairs if p["channel"] == "B" else {}
            notes.append(("document", ref, p["note"], m))
        n_notes = check_notes(rep, fps, notes)
        unconnected = check_drc(rep, pcb, out / "drc.json")
    if prl.exists() and not prl_before:
        prl.unlink()                         # LoadBoard and kicad-cli may write the local state
    for line in rep.fails:
        print(line)
    print(f"{len(fps)} footprints, {n_notes} placement notes measured, "
          f"{unconnected if unconnected is not None else '?'} unconnected items (check_routing.py judges them)")
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
