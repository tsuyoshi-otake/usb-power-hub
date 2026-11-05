"""Place the Rev0.4 board from the placement document (issue #6 P3; CLAUDE.md 5.2).

Run with KiCad's own Python from the repository root, after make_schematic.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_pcb.py [--no-check]

Inputs:
- the schematic in design/ecad/source; its netlist is exported with kicad-cli, so the board
  carries exactly what the schematic carries;
- design/ecad/libraries/usb-power-hub.pretty, the project footprints;
- design/ecad/PLACEMENT_Rev0.4.md, the position and rotation of every part.
Output: design/ecad/source/usb-power-hub.kicad_pcb, rebuilt from nothing on every run:
- the skeleton of make_project.py (outline, stackup, finish, title block), written by its own
  functions;
- one footprint per netlist component: its footprint, Value, fields (hidden, on F.Fab), sheet
  path, BOM exclusion and pad nets, at the document's position and rotation, on F.Cu;
- the reference designators hidden on F.SilkS; they stay on F.Fab. 300 designators at 1.0 mm
  (CLAUDE.md 6) do not fit, and the silkscreen labels CLAUDE.md 6 requires come with routing
  (P4).
No tracks, vias or zones. The UUID generator is seeded, so the footprints come out in the same
order, and make_project.fix_uuids derives every UUID from its position: a re-run writes the same
bytes.

Order: make_project.py writes a bare board when it runs, so this script runs after it, and
after make_schematic.py. The board is built in a temporary directory: the source project is
never loaded, so pcbnew cannot write its cache back to the .kicad_pro (see make_project.py),
and the script stops if the .kicad_pro bytes changed anyway. Then it runs
make_project.py --check and check_pcb.py, each in a new process, unless --no-check.
Exit status: 0 = written and checked; 1 = a check failed or the document is malformed.

What it CANNOT see: whether the placement is good. The document's Note column gives the
reason for each position; check_pcb.py checks the rules it lists, and DRC the courtyards.
"""
import importlib.util
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
DOC = ECAD / "PLACEMENT_Rev0.4.md"
NAME = "usb-power-hub"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
SKIP_FIELDS = {"Footprint"}                 # the footprint itself carries it
ROTATIONS = {0, 90, 180, 270}
UUID_SEED = 6                               # any fixed value; 6 is the issue number


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")
proj = _load("make_project")


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


def build(pcb, comps, pins, place):
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
    if not pcbnew.SaveBoard(str(pcb), board):
        raise SystemExit("pcbnew could not save the board")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[1:] not in ([], ["--no-check"]):
        raise SystemExit("usage: make_pcb.py [--no-check]")
    pcb, pro, prl = proj.paths(SRC)
    pro_before = pro.read_bytes()
    place = read_placement(DOC)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        comps, pins = read_netlist(export_netlist(tmp))
        unplaced = sorted(set(comps) - set(place), key=natural)
        unknown = sorted(set(place) - set(comps), key=natural)
        if unplaced or unknown:
            raise SystemExit(f"{DOC.name}: not placed: {' '.join(unplaced) or '-'};"
                             f" not in the netlist: {' '.join(unknown) or '-'}")
        work = tmp / "board"
        work.mkdir()
        build(work / pcb.name, comps, pins, place)
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
    for script, args in (("make_project.py", ["--check"]), ("check_pcb.py", [])):
        status |= subprocess.run([sys.executable, "-I", "-B", str(HERE / script), *args]).returncode
    return 1 if status else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
