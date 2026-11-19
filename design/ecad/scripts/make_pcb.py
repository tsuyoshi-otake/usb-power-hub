"""Place, route and label the Rev0.7 board from its documents (issue #6 P3-P5; CLAUDE.md 5, 6).

Run with KiCad's own Python from the repository root, after make_schematic.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_pcb.py [--no-check]
    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_pcb.py --dsn <out.dsn>

Inputs:
- the schematic in design/ecad/source; its netlist is exported with kicad-cli, so the board
  carries exactly what the schematic carries;
- design/ecad/libraries/usb-power-hub.pretty, the project footprints;
- design/ecad/PLACEMENT_Rev0.7.md, the position and rotation of every part, and the
  silkscreen labels (its silk table);
- design/ecad/ROUTING_Rev0.7.md, the plane, the hand-drawn tracks, the GND fanout, the zones,
  the carry table, the classes and keepouts of the router, and the patch drawn after it;
- design/ecad/routing/carried.json, the previous revision's routing that still stands on this
  board (carry.py writes it from the sources the carry table names);
- design/ecad/routing/usb-power-hub.ses, the router's session, with routing/autoroute.json, the
  SHA-256 of the router input it was made from (autoroute.py writes both).
Output: design/ecad/source/usb-power-hub.kicad_pcb, rebuilt from nothing on every run:
- the skeleton of make_project.py (outline, stackup, finish, title block), written by its own
  functions;
- one footprint per netlist component: its footprint, Value, fields (hidden, on F.Fab), sheet
  path, BOM exclusion and pad nets, at the document's position and rotation, on F.Cu;
- the reference designators hidden on F.SilkS; they stay on F.Fab. 300 designators at 1.0 mm
  (CLAUDE.md 6) do not fit;
- the routing, in route.py's order: the In1 plane, the hand-drawn tracks, the GND fanout, the
  carried record's tracks and vias, the session's, the patch table's, the pours, and every zone
  filled;
- the silk table's labels, each a text on F.SilkS with its leader segments. They are added
  after the session, so they are not in the router input; the footprints' own silkscreen is.
The UUID generator is seeded, so the items come out in the same order, and
make_project.fix_uuids derives every UUID from its position. A re-run writes the same bytes
except for one thing: KiCad's zone filler (route.fill) is not deterministic. In 3 of 32 runs
(2026-11-13) it left out two 0.11 mm2 islands of the B.Cu GND pour that touch pad J3.S1 (at
x 96.73-97.23 and 105.37-105.87, y 117.0-117.3 mm), which the other 29 runs kept; the board then
differs by those two filled polygons, and the Gerber's B_Cu member with it. The tracked board is
therefore the source of truth (release r02 was made from a run without the islands): do not
regenerate it to compare, and do not treat a changed board hash after a re-run as a changed design.

The carried record is applied only when it names the commit, the two SHA-256 and the skip texts
of the document's carry table, and the SHA-256 of the router input of the board before it (plane,
hand-drawn tracks, GND fanout; the document's classes and keepouts): a change to the schematic,
the placement or those parts of the routing document makes the record stale, and the script
stops and asks for carry.py.
The session is imported only when the router input of this run (KiCad's DSN of the board before
the session, the carried copper included, with the document's classes and keepouts) has the
SHA-256 autoroute.json records: a change before that step makes the session stale, and the script
stops and asks for autoroute.py. --dsn writes that router input and stops; autoroute.py calls it
so.

Order: make_project.py writes a bare board when it runs, so this script runs after it, and
after make_schematic.py. The board is built in a temporary directory: the source project is
never loaded, so pcbnew cannot write its cache back to the .kicad_pro (see make_project.py),
and the script stops if the .kicad_pro bytes changed anyway. Then it runs
make_project.py --check, check_pcb.py, check_routing.py and check_silk.py, each in a new
process, unless --no-check.
Exit status: 0 = written and checked; 1 = a check failed or a document is malformed.

What it CANNOT see: whether the placement, the routing or the labels are good. The documents
give the reason for each position, track and label; check_pcb.py, check_routing.py and
check_silk.py check the rules they list, and DRC the clearances.
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ECAD = ROOT / "design" / "ecad"
SRC = ECAD / "source"
LIB = ECAD / "libraries" / "usb-power-hub.pretty"
DOC = ECAD / "PLACEMENT_Rev0.7.md"
ROUTING = ECAD / "ROUTING_Rev0.7.md"
NAME = "usb-power-hub"
SESSION = ECAD / "routing" / f"{NAME}.ses"
RECORD = ECAD / "routing" / "autoroute.json"
CARRIED = ECAD / "routing" / "carried.json"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
SKIP_FIELDS = {"Footprint"}                 # the footprint itself carries it
ROTATIONS = {0, 90, 180, 270}
SILK_ROTATIONS = {0, 90}                    # left to right, bottom to top: one reading side
UUID_SEED = 6                               # any fixed value; 6 is the issue number


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")
proj = _load("make_project")
route = _load("route")


# ---- the placement document ------------------------------------------------------------------
def doc_tables(text):
    """{kind: (argument dict, [row dict])} for every marked table."""
    out = {}
    for m in re.finditer(r"<!-- (\w+):begin(?: ([^>]*?))? -->\n(.*?)<!-- \1:end -->", text, re.S):
        kind, arg, body = m.groups()
        lines = [ln for ln in body.splitlines() if ln.startswith("|")]
        head = [c.strip() for c in lines[0].strip().strip("|").split("|")]
        rows = []
        for ln in lines[2:]:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != len(head):
                raise SystemExit(f"{kind}: row has {len(cells)} cells, header {len(head)}: {ln}")
            rows.append(dict(zip(head, cells)))
        args = dict(a.split("=", 1) for a in (arg or "").split())
        out[kind] = (args, rows)
    return out


def read_placement(path):
    """ref -> (x, y, rotation) in the board frame: origin at the lower-left corner, y up."""
    tables = doc_tables(path.read_text(encoding="utf-8"))
    place = {}

    def add(ref, x, y, rot):
        if ref in place:
            raise SystemExit(f"{ref} is placed twice in {path.name}")
        if rot not in ROTATIONS:
            raise SystemExit(f"{ref}: rotation {rot} is not one of {sorted(ROTATIONS)}")
        place[ref] = (x, y, rot)

    for r in tables["place"][1]:
        add(r["Ref"], float(r["x"]), float(r["y"]), int(r["Rot"]))
    args, rows = tables["channel"]
    dx = float(args["dx"])
    for r in rows:
        x, y, rot = float(r["x"]), float(r["y"]), int(r["Rot"])
        add(r["Ref A"], x, y, rot)
        add(r["Ref B"], round(x + dx, 4), y, rot)
    return place


def read_silk(path):
    """[label dict] of the silk table: text, centre, rotation, glyph size, stroke, leader points."""
    out = []
    for r in doc_tables(path.read_text(encoding="utf-8"))["silk"][1]:
        rot = int(r["Rot"])
        if rot not in SILK_ROTATIONS:
            raise SystemExit(f"silk {r['Label']}: rotation {rot} is not one of {sorted(SILK_ROTATIONS)}")
        leader = [] if r["Leader"] == "-" else             [tuple(float(v) for v in pt.split(",")) for pt in r["Leader"].split()]
        if len(leader) == 1 or any(len(pt) != 2 for pt in leader):
            raise SystemExit(f"silk {r['Label']}: a leader needs two or more x,y points: {r['Leader']}")
        out.append(dict(label=r["Label"], text=r["Text"], x=float(r["x"]), y=float(r["y"]), rot=rot,
                        width=float(r["Width"]), height=float(r["Height"]), stroke=float(r["Stroke"]),
                        leader=leader))
    return out


def read_routing(place_doc, routing_doc):
    """(route.read of the routing document, {region: (x, y, w, h)} of the placement)."""
    ptables = doc_tables(place_doc.read_text(encoding="utf-8"))
    args, rows = ptables["channel"]
    refs = {r["Ref A"]: r["Ref B"] for r in rows}
    routing = route.read(doc_tables(routing_doc.read_text(encoding="utf-8")), refs, float(args["dx"]))
    regions = {r["Region"]: tuple(float(r[k]) for k in ("x", "y", "w", "h")) for r in ptables["regions"][1]}
    return routing, regions


# ---- the netlist ------------------------------------------------------------------------------
def export_netlist(out):
    path = out / f"{NAME}.net"
    r = subprocess.run([str(CLI), "sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(path),
                        str(SRC / f"{NAME}.kicad_sch")], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    if not path.exists():
        raise SystemExit(f"kicad-cli exported no netlist (exit {r.returncode}): {r.stdout + r.stderr}")
    return path


def read_netlist(path):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    comps = {}
    for c in sx.walk(sx.first(tree, "components"), "comp"):
        props = {}
        for p in sx.find(c, "property"):
            v = sx.first(p, "value")
            props[sx.first(p, "name")[1]] = v[1] if v else None
        fields = [(f[1][1], f[2]) for f in sx.find(sx.first(c, "fields") or [], "field") if len(f) > 2]
        comps[sx.first(c, "ref")[1]] = dict(
            value=sx.first(c, "value")[1], footprint=sx.first(c, "footprint")[1], fields=fields,
            props=props, path=sx.first(sx.first(c, "sheetpath"), "tstamps")[1] + sx.first(c, "tstamps")[1])
    pins = {}
    for n in sx.find(sx.first(tree, "nets"), "net"):
        name = sx.first(n, "name")[1]
        for node in sx.find(n, "node"):
            pins[(sx.first(node, "ref")[1], sx.first(node, "pin")[1])] = name
    return comps, pins


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def read_inputs(tmp):
    """(comps, pins, place, routing, regions, silk): the schematic's netlist, exported into tmp,
    and the two documents. It stops if they do not name the same parts."""
    place = read_placement(DOC)
    routing, regions = read_routing(DOC, ROUTING)
    silk = read_silk(DOC)
    comps, pins = read_netlist(export_netlist(tmp))
    unplaced = sorted(set(comps) - set(place), key=natural)
    unknown = sorted(set(place) - set(comps), key=natural)
    if unplaced or unknown:
        raise SystemExit(f"{DOC.name}: not placed: {' '.join(unplaced) or '-'};"
                         f" not in the netlist: {' '.join(unknown) or '-'}")
    return comps, pins, place, routing, regions, silk


# ---- the board -------------------------------------------------------------------------------
def to_sheet(x, y):
    ox, oy = proj.ORIGIN_MM
    return pcbnew.VECTOR2I(pcbnew.FromMM(ox + x), pcbnew.FromMM(oy - y))


def add_footprint(board, nets, ref, comp, pins, at):
    lib, name = comp["footprint"].split(":")
    fp = pcbnew.FootprintLoad(str(LIB), name)
    if fp is None:
        raise SystemExit(f"{ref}: footprint {name} is not in {LIB.name}")
    fp.SetFPIDAsString(comp["footprint"])
    fp.SetReference(ref)
    fp.SetValue(comp["value"])
    fp.SetPath(pcbnew.KIID_PATH(comp["path"]))
    fp.SetSheetname(comp["props"].get("Sheetname") or "")
    fp.SetSheetfile(comp["props"].get("Sheetfile") or "")
    for fname, text in comp["fields"]:
        if fname in SKIP_FIELDS:
            continue
        fp.SetField(fname, text)
        field = fp.GetFieldByName(fname)
        field.SetVisible(False)
        field.SetLayer(pcbnew.F_Fab)
    attrs = fp.GetAttributes()
    if "exclude_from_bom" in comp["props"]:
        attrs |= pcbnew.FP_EXCLUDE_FROM_BOM
    fp.SetAttributes(attrs)
    fp.Reference().SetVisible(False)
    board.Add(fp)
    x, y, rot = at
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(to_sheet(x, y))
    for pad in fp.Pads():
        net = pins.get((ref, pad.GetNumber()))
        if net is not None:
            pad.SetNet(nets[net])
    return fp


def add_silk(board, silk):
    """Each label as a centred F.SilkS text; its leader as segments of the label's stroke."""
    for s in silk:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(s["text"])
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(s["width"]), pcbnew.FromMM(s["height"])))
        t.SetTextThickness(pcbnew.FromMM(s["stroke"]))
        t.SetTextAngleDegrees(s["rot"])
        t.SetPosition(to_sheet(s["x"], s["y"]))
        board.Add(t)
        for a, b in zip(s["leader"], s["leader"][1:]):
            seg = pcbnew.PCB_SHAPE(board)
            seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
            seg.SetLayer(pcbnew.F_SilkS)
            seg.SetWidth(pcbnew.FromMM(s["stroke"]))
            seg.SetStart(to_sheet(*a))
            seg.SetEnd(to_sheet(*b))
            board.Add(seg)
    return len(silk), sum(max(len(s["leader"]) - 1, 0) for s in silk)


def router_input(board, routing, regions, tmp):
    """KiCad's DSN of the board as it stands, with the routing document's classes and keepouts."""
    raw = tmp / "router-raw.dsn"
    raw.unlink(missing_ok=True)
    pcbnew.ExportSpecctraDSN(board, str(raw))
    if not raw.exists():
        raise SystemExit("pcbnew exported no DSN")

    def pad_frame(token, net):
        return route.to_frame(route.pad_position(board, token, net))
    keepouts = route.keepout_polygons(routing, regions, pad_frame, route.drilled_boxes(board))
    return route.post_dsn(raw.read_text(encoding="utf-8"), routing, keepouts, route.board_via(board))


def session():
    """The committed session's text, after checking it against its record."""
    if not (SESSION.exists() and RECORD.exists()):
        raise SystemExit(f"no router session in {SESSION.parent.relative_to(ROOT).as_posix()}: run autoroute.py")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    data = SESSION.read_bytes()
    if hashlib.sha256(data).hexdigest() != record["ses_sha256"]:
        raise SystemExit(f"{SESSION.name} is not the session {RECORD.name} records: run autoroute.py")
    return data.decode("utf-8"), record


def carried(carry, base):
    """routing/carried.json, after checking that carry.py made it from the sources the routing
    document's carry table names, and for this board: base is the digest of the router input of
    the board before the carried routing."""
    if not CARRIED.exists():
        raise SystemExit(f"no {CARRIED.name} in {CARRIED.parent.as_posix()}: run carry.py")
    record = json.loads(CARRIED.read_text(encoding="utf-8"))
    named = {k: carry[k] for k in ("commit", "session_sha256", "patch_sha256", "skip")}
    if {k: record.get(k) for k in named} != named:
        raise SystemExit(f"{CARRIED.name} was not made from the sources the carry table of {ROUTING.name}"
                         f" names: run carry.py")
    if record.get("base_dsn_sha256") != base:
        raise SystemExit(f"{CARRIED.name} was made for another board ({str(record.get('base_dsn_sha256'))[:12]},"
                         f" this board {base[:12]}): the schematic, the placement or the routing document"
                         f" changed; run carry.py, then autoroute.py")
    return record


def base_board(pcb, comps, pins, place, routing):
    """Write the skeleton to pcb and return it loaded, placed, with the In1 plane, the hand-drawn
    tracks and the GND fanout: what the carried routing and the router start from."""
    # pcbnew writes the footprints sorted by UUID, and gives each new item a random one. Seeding
    # the generator makes the UUIDs, and so the footprint order, the same on every run;
    # make_project.fix_uuids then renumbers them by position in the file.
    pcbnew.KIID.SeedGenerator(UUID_SEED)
    proj.make_board(pcb)
    proj.insert_stackup(pcb)
    board = pcbnew.LoadBoard(str(pcb))
    nets = {}
    for name in sorted(set(pins.values())):
        nets[name] = pcbnew.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    for ref in sorted(comps, key=natural):
        add_footprint(board, nets, ref, comps[ref], pins, place[ref])
    route.plane(board, routing["zones"], proj.SIZE_MM)
    n_t, n_v = route.apply_rows(board, routing["rows"])
    hs = {n for p in routing["pairs"] for n in p["nets"]}
    n_f, joined, unfanned = route.gnd_fanout(board, routing["epads"], hs,
                                             (proj.VIA_HOLE_TO_HOLE, proj.RULES["min_hole_to_hole"]))
    print(f"routing document: {n_t} track segments, {n_v} vias; GND fanout: {n_f} vias,"
          f" {len(joined)} pad(s) joined to a plated hole of their part"
          f"{': ' + ' '.join(joined) if joined else ''},"
          f" {len(unfanned)} pad(s) left to the router{': ' + ' '.join(unfanned) if unfanned else ''}")
    return board


def build(pcb, comps, pins, place, routing, regions, silk, tmp, dsn_out=None):
    """Write the placed and routed board to pcb; with dsn_out, write the router input instead."""
    board = base_board(pcb, comps, pins, place, routing)
    if routing["carry"]:
        base = route.dsn_digest(router_input(board, routing, regions, tmp))
        c_t, c_v, c_r = route.apply_carried(board, carried(routing["carry"], base))
        print(f"carried from {routing['carry']['commit'][:7]}: {c_t} track segments, {c_v} vias,"
              f" {c_r} drawn item(s) taken away")
    dsn = router_input(board, routing, regions, tmp)
    digest = route.dsn_digest(dsn)
    if dsn_out is not None:
        dsn_out.write_text(dsn, encoding="utf-8", newline="\n")
        return digest
    text, record = session()
    if record["dsn_sha256"] != digest:
        raise SystemExit(f"{SESSION.name} was routed from another router input ({record['dsn_sha256'][:12]},"
                         f" this board {digest[:12]}): the schematic, the placement or the routing"
                         f" document changed; run autoroute.py")
    s_t, s_v = route.import_session(board, text, sx)
    p_t, p_v, p_r = route.apply_patch(board, routing["patch"])
    route.pours(board, routing["zones"], proj.SIZE_MM)
    print(f"session: {s_t} track segments, {s_v} vias; patch: {p_t} track segments, {p_v} vias,"
          f" {p_r} item(s) removed; {len(list(board.Zones()))} zones filled")
    n_l, n_s = add_silk(board, silk)
    print(f"silkscreen: {n_l} labels, {n_s} leader segments")
    if not pcbnew.SaveBoard(str(pcb), board):
        raise SystemExit("pcbnew could not save the board")
    return digest


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    dsn_out = None
    if len(argv) == 3 and argv[1] == "--dsn":
        dsn_out = pathlib.Path(argv[2]).resolve()
    elif argv[1:] not in ([], ["--no-check"]):
        raise SystemExit("usage: make_pcb.py [--no-check | --dsn <out.dsn>]")
    pcb, pro, prl, _ = proj.paths(SRC)
    pro_before = pro.read_bytes()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        comps, pins, place, routing, regions, silk = read_inputs(tmp)
        work = tmp / "board"
        work.mkdir()
        # a copy of the project beside the board, so pcbnew loads its rules and net classes
        # (the router input carries them) and any cache it writes lands in the copy
        shutil.copyfile(pro, work / pro.name)
        digest = build(work / pcb.name, comps, pins, place, routing, regions, silk, tmp, dsn_out)
        if dsn_out is not None:
            print(f"wrote {dsn_out}: router input {digest}")
            return 0
        shutil.copyfile(work / pcb.name, pcb)
    n = proj.fix_uuids(pcb, "pcb")
    if prl.exists():
        prl.unlink()
    if pro.read_bytes() != pro_before:
        pro.write_bytes(pro_before)
        raise SystemExit(f"{pro.name} changed while the board was built; restored. Not checked.")
    print(f"wrote {pcb.relative_to(ROOT).as_posix()}: {len(comps)} footprints, "
          f"{len(set(pins.values()))} nets, {n} uuid(s) fixed")
    if argv[1:] == ["--no-check"]:
        return 0
    sys.stdout.flush()
    status = 0
    for script, args in (("make_project.py", ["--check"]), ("check_pcb.py", []), ("check_routing.py", []),
                         ("check_silk.py", [])):
        status |= subprocess.run([sys.executable, "-I", "-B", str(HERE / script), *args]).returncode
    return 1 if status else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
