"""Write the lid PCB Rev0.1 as a KiCad 9 board (issue #11): design/mechanical/lid/usb-power-hub-lid.*

Run with KiCad's own Python, which carries the pcbnew module, from the repository root, after
make_enclosure.py (which writes the lid's interface):

    "<KiCad 9.0>/bin/python.exe" -I -B design/mechanical/scripts/make_lid.py
        [--doc FILE] [--interface FILE] [--out DIR] [--no-check]

Inputs: the lid document's parameter and legend tables (design/mechanical/LID_Rev0.1.md) and
the lid's interface (assembly/UsbPowerHub_Enclosure_Rev0.1_LidInterface.json): outline, holes,
windows, ports. No position is typed here.
Output: usb-power-hub-lid.kicad_pcb and .kicad_pro in --out (default design/mechanical/lid),
rebuilt from nothing on every run:
- 2 copper layers, the interface's outline and thickness, lower-left corner at (50, 122) mm on
  the sheet, which is also the auxiliary (plot and drill) origin, as on the main board;
- every hole of the interface as an unplated hole (a footprint with one NPTH pad);
- one copper pour without a net on F.Cu and B.Cu, drawn in from the outline by edge_clear, and
  a rule area that forbids the pour round every hole, screw head and window. The fill made
  here keeps no distance by itself (measured 2026-11-18: it covered an unplated hole that had
  no rule area, and it ran to 0.1 mm from the outline when the pour was drawn there, with
  the board's edge clearance at 0.5 mm), so every keep-clear area is drawn: the pour's own
  outline for the edge, a rule area for the rest. check_lid.py measures the result (L04);
- each window as a filled rectangle on F.Mask and B.Mask: an opening in the solder mask;
- the legend rows as texts, one arrow per port and one ring per button hole;
- the title block, whose fourth comment is the SHA-256 of the inputs (check_lid.py L01).
pcbnew's KIID generator is seeded, so a re-run writes the same bytes (two runs compared on
2026-11-18). KiCad's local-state file (.kicad_prl) is deleted; it is gitignored.

Order matters: SaveBoard rewrites .kicad_pro from pcbnew's cached project, so the project's
rules are edited after the last SaveBoard, and the check runs in a new process.
Then it runs check_lid.py, unless --no-check. Exit status: 0 = written and checked; 1 = a
check failed.

What it CANNOT see: everything check_lid.py lists, and whether the fill is the same on another
KiCad version (the zone filler is not deterministic on the main board; .claude/memory/rules.md).
"""
import argparse
import importlib.util
import json
import math
import pathlib
import subprocess
import sys

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
DATE = "2026-11-18"
CIRCLE_SIDES = 72                          # a keep-clear circle is a polygon that contains it
# Board constraints for KiCad's DRC (CLAUDE.md 5.3 starting values; the lid has no track).
RULES = {
    "min_clearance": 0.15,
    "min_copper_edge_clearance": 0.30,
    "min_hole_clearance": 0.25,
    "min_hole_to_hole": 0.25,
    "min_through_hole_diameter": 0.30,
    "min_text_height": 1.0,
    "min_text_thickness": 0.15,
}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


spec = _load("lid_spec")
mm = pcbnew.FromMM


def sheet(x, y):
    """A board-frame point (mm, y up) on KiCad's sheet."""
    return pcbnew.VECTOR2I(mm(spec.ORIGIN[0] + x), mm(spec.ORIGIN[1] - y))


def polygon(target, points):
    """Append one outline of board-frame points to a SHAPE_POLY_SET."""
    target.NewOutline()
    for x, y in points:
        p = sheet(x, y)
        target.Append(p.x, p.y)


def circle_points(cx, cy, r):
    """A polygon that contains the circle of radius r (its sides touch the circle)."""
    rr = r / math.cos(math.pi / CIRCLE_SIDES)
    return [(cx + rr * math.cos(2 * math.pi * i / CIRCLE_SIDES), cy + rr * math.sin(2 * math.pi * i / CIRCLE_SIDES))
            for i in range(CIRCLE_SIDES)]


def rect_points(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def copper_layers():
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.F_Cu)
    ls.AddLayer(pcbnew.B_Cu)
    return ls


def add_outline(board, o):
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(sheet(o["x0"], o["y1"]))
    edge.SetEnd(sheet(o["x1"], o["y0"]))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.05))
    board.Add(edge)


def add_hole(board, hole):
    fp = pcbnew.FOOTPRINT(board)
    fp.SetReference(hole["ref"])
    fp.SetValue(f"hole {hole['kind']}")
    fp.Reference().SetVisible(False)
    fp.Value().SetVisible(False)
    fp.SetPosition(sheet(hole["x"], hole["y"]))
    fp.SetAttributes(pcbnew.FP_EXCLUDE_FROM_BOM | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_BOARD_ONLY)
    pad = pcbnew.PAD(fp)
    pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
    pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
    size = pcbnew.VECTOR2I(mm(hole["d"]), mm(hole["d"]))
    pad.SetSize(pcbnew.F_Cu, size)             # pad = hole: no copper, and a mask opening of the hole's size
    pad.SetDrillSize(size)
    pad.SetLayerSet(pcbnew.PAD.UnplatedHoleMask())
    pad.SetPosition(sheet(hole["x"], hole["y"]))
    fp.Add(pad)
    board.Add(fp)


def add_pour(board, o, params):
    z = pcbnew.ZONE(board)
    z.SetLayerSet(copper_layers())
    z.SetZoneName("lid copper")
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    z.SetMinThickness(mm(params["zone_min"]))
    c = params["edge_clear"]
    polygon(z.Outline(), rect_points(o["x0"] + c, o["y0"] + c, o["x1"] - c, o["y1"] - c))
    board.Add(z)


def add_keep_clear(board, name, points):
    k = pcbnew.ZONE(board)
    k.SetIsRuleArea(True)
    k.SetZoneName(name)
    k.SetDoNotAllowCopperPour(True)
    k.SetDoNotAllowTracks(False)
    k.SetDoNotAllowVias(False)
    k.SetDoNotAllowPads(False)
    k.SetDoNotAllowFootprints(False)
    k.SetLayerSet(copper_layers())
    polygon(k.Outline(), points)
    board.Add(k)


def add_window(board, rect):
    x0, y0, x1, y1 = rect
    for layer in (pcbnew.F_Mask, pcbnew.B_Mask):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_RECT)
        s.SetStart(sheet(x0, y1))
        s.SetEnd(sheet(x1, y0))
        s.SetLayer(layer)
        s.SetWidth(0)
        s.SetFilled(True)
        board.Add(s)


def add_text(board, row, point):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(row["text"])
    t.SetLayer(pcbnew.F_SilkS if row["side"] == "top" else pcbnew.B_SilkS)
    t.SetPosition(sheet(*point))
    t.SetTextSize(pcbnew.VECTOR2I(mm(row["height"]), mm(row["height"])))
    t.SetTextThickness(mm(row["stroke"]))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    if row["side"] == "bottom":
        t.SetMirrored(True)
    board.Add(t)


def add_arrow(board, interface, port, params):
    """A filled triangle whose tip points at the lid's edge above the port."""
    s, e = spec.inward(port), spec.edge_y(interface, port)
    tip = e + s * params["arrow_tip"]
    base = tip + s * params["arrow_h"]
    a = pcbnew.PCB_SHAPE(board)
    a.SetShape(pcbnew.SHAPE_T_POLY)
    a.SetLayer(pcbnew.F_SilkS)
    a.SetWidth(0)
    a.SetFilled(True)
    pts = pcbnew.VECTOR_VECTOR2I()
    for x, y in ((port["x"], tip), (port["x"] - params["arrow_w"] / 2, base), (port["x"] + params["arrow_w"] / 2, base)):
        pts.append(sheet(x, y))
    a.SetPolyPoints(pts)
    board.Add(a)


def add_ring(board, hole, params):
    r = pcbnew.PCB_SHAPE(board)
    r.SetShape(pcbnew.SHAPE_T_CIRCLE)
    r.SetLayer(pcbnew.F_SilkS)
    r.SetCenter(sheet(hole["x"], hole["y"]))
    r.SetEnd(sheet(hole["x"] + params["ring_d"] / 2, hole["y"]))
    r.SetWidth(mm(params["ring_stroke"]))
    r.SetFilled(False)
    board.Add(r)


def build(pcb_path, params, legend, interface, digest):
    pcbnew.KIID.SeedGenerator(1)               # a re-run then gives every item the same UUID
    board = pcbnew.NewBoard(str(pcb_path))
    board.SetCopperLayerCount(2)
    o = interface["outline"]
    add_outline(board, o)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(interface["thickness"]))
    ds.SetAuxOrigin(sheet(o["x0"], o["y0"]))
    ds.SetGridOrigin(sheet(o["x0"], o["y0"]))
    tb = board.GetTitleBlock()
    tb.SetTitle(f"{spec.PRODUCT} Lid")
    tb.SetRevision(spec.REVISION)
    tb.SetDate(DATE)
    for i, c in enumerate(("WIP - MANUFACTURING PROHIBITED",
                           "Source: design/mechanical/LID_Rev0.1.md",
                           "Interface: UsbPowerHub_Enclosure_Rev0.1_LidInterface.json",
                           spec.DIGEST_TAG + digest)):
        tb.SetComment(i, c)
    for hole in interface["holes"]:
        add_hole(board, hole)
    add_pour(board, o, params)
    for hole in interface["holes"]:
        if hole["kind"] == "screw":
            r = hole["keepout_d"] / 2 + params["head_clear"]
        else:
            r = hole["d"] / 2 + params["hole_clear"]
        add_keep_clear(board, f"keep clear {hole['ref']}", circle_points(hole["x"], hole["y"], r))
    c = params["window_clear"]
    for w in interface["windows"]:
        x0, y0, x1, y1 = w["rect"]
        add_keep_clear(board, "keep clear window " + "/".join(w["refs"]), rect_points(x0 - c, y0 - c, x1 + c, y1 + c))
        add_window(board, w["rect"])
    for row in legend:
        add_text(board, row, spec.label_point(interface, row))
    for port in interface["ports"]:
        add_arrow(board, interface, port, params)
    for hole in interface["holes"]:
        if hole["kind"] == "button":
            add_ring(board, hole, params)
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise SystemExit("pcbnew could not fill the pour")
    if not pcbnew.SaveBoard(str(pcb_path), board):
        raise SystemExit("pcbnew could not save the board")
    # pcbnew ends its lines with CR LF on Windows; the repository stores LF (.gitattributes), so
    # the file is written as a checkout would give it and its SHA-256 is the same on both sides.
    pcb_path.write_bytes(pcb_path.read_bytes().replace(b"\r\n", b"\n"))


def edit_project(pro_path):
    pro = json.loads(pro_path.read_text(encoding="utf-8"))
    pro["board"]["design_settings"]["rules"].update(RULES)
    pro_path.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8", newline="\n")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--doc", type=pathlib.Path, default=spec.DOC)
    ap.add_argument("--interface", type=pathlib.Path, default=spec.INTERFACE)
    ap.add_argument("--out", type=pathlib.Path, default=spec.SOURCE)
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args(argv[1:])
    params, legend = spec.load_doc(args.doc)
    interface = spec.load_interface(args.interface)
    digest = spec.inputs_digest(params, legend, args.interface)
    args.out.mkdir(parents=True, exist_ok=True)
    pcb, pro, prl = (args.out / f"{spec.NICK}.{ext}" for ext in ("kicad_pcb", "kicad_pro", "kicad_prl"))
    for p in (pcb, pro):
        if p.exists():
            p.unlink()                         # regenerated from nothing every run
    build(pcb, params, legend, interface, digest)
    edit_project(pro)                          # last, so no SaveBoard overwrites it
    if prl.exists():
        prl.unlink()
    print(f"wrote {pcb.name} and {pro.name} in {args.out.as_posix()}: {len(interface['holes'])} holes,"
          f" {len(interface['windows'])} windows, {len(legend)} texts, {len(interface['ports'])} arrows;"
          f" inputs {digest[:12]}")
    if args.no_check:
        return 0
    sys.stdout.flush()                         # keep this output ahead of the child's
    return subprocess.run([sys.executable, "-I", "-B", str(HERE / "check_lid.py"), "--doc", str(args.doc),
                           "--interface", str(args.interface), "--src", str(args.out)], check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
