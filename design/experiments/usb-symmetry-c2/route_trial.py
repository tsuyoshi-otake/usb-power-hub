"""Trial C2, routed: what the router leaves open on the C2 placement, beside the board's (issue #12).

NOT DESIGN DATA. Everything is built in a scratch directory outside the repository; the tracked
board, its routing document and its router session are read and never written.

Run with KiCad's own Python from the repository root, one stage after the other:

    "<KiCad 9.0>/bin/python.exe" -I -B design/experiments/usb-symmetry-c2/route_trial.py <scratch> base
    ... route_trial.py <scratch> prepare
    ... route_trial.py <scratch> route --java <java.exe> --jar <freerouting-2.5.0.jar>
    ... route_trial.py <scratch> report

base     <scratch>/base: a copy of the board's documents with the patch table emptied, built with
         the committed router session. It is the board as the router left it, before the 275 patch
         rows that closed its open connections: the fair thing to hold a fresh session against.
prepare  <scratch>/c2: a copy with the placement changed by c2_change.py and the routing document
         by c2_routing.py. Builds the board up to the GND fanout (make_pcb.py's own functions),
         runs DRC on it and weighs the port paths, so a hand-drawn row that hits a pad or a trunk
         that is too resistive shows before the router runs.
negative <scratch>/neg-*: the prepare stage on two faulty trunks (NEGATIVE); passes when each
         fault is reported.
route    runs the copy's autoroute.py (Freerouting, about half an hour) and its make_pcb.py.
report   runs each copy's check_pcb.py and check_routing.py, reads the boards, and prints the
         two side by side; writes result.json and a top-side render of each board.

The silkscreen labels are left out of both copies (the silk table is emptied): C2 moves the
parts they name, and the labels are not what this trial is about.

What it CANNOT show: the router is deterministic, so the result belongs to this router input and
to no other: another drawing of the hand-drawn C2 rows (pairs UP and B, the VBUS_B trunk), which
are a first drawing and not an optimised one, gives another count, and on this board 22 extra
pre-route rows once took the open connections from 16 to 41. A connection the router left open
is not shown to be unroutable. No patch is written, so neither board is finished. Nothing here
measures noise from the MAU104, the pairs' impedance or signal quality; the silkscreen, the
enclosure, the lid PCB and JLCPCB's gate are untouched.
Exit status: 0 = the stage ran; 1 = it did not. A FAIL line of a checker is a result, not a
failure of the trial: neither board is expected to pass without its patch.
"""
import collections
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
PLACEMENT = "design/ecad/PLACEMENT_Rev0.5.md"
ROUTING = "design/ecad/ROUTING_Rev0.5.md"
SCRIPTS = "design/ecad/scripts"
PCB = "design/ecad/source/usb-power-hub.kicad_pcb"
RECORD = "design/ecad/routing/autoroute.json"
BOARDS = ("base", "c2")
PAIRS = ("USB_UP", "USB_A", "USB_B")
# DRC types the board before the router always has: the vias the routing document leaves for the
# router to join, and the footprint library, which the pre-route copy stands apart from
PRE_EXPECTED = ("via_dangling", "lib_footprint_issues")
TRUNK = ("| VBUS_B | B.Cu | 3.00 | 60.13,18.2 60.13,17.0 75.5,17.0 83.6,8.9 | trial C2: east under pair A in the"
         " corridor, then under pair B's lane; 3.0 mm because port B has 2.1 mOhm to spare |")
END = "| VBUS_B | B.Cu | 1.80 | 83.6,8.9 84.6,7.9 87.5,7.9 | trial C2: to the lift vias at the receptacle |"
# (name, a line of the C2 routing document, the faulty line, what the prepare stage must then say)
NEGATIVE = (
    ("narrow", TRUNK, TRUNK.replace("| 3.00 |", "| 0.30 |"), "FAIL port B"),
    ("slot", END, END.replace("84.6,7.9 87.5,7.9", "84.6,7.9 87.5,7.9 86.82,5.2"), "FAIL DRC"),
)
STATS = re.compile(r"(\d+) tracks, (\d+) vias; (\d+) In2 track\(s\) in the analog blocks, (\d+) In2/B\.Cu"
                   r" crossing\(s\) there; (.*); (\d+|\?) unconnected items")


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_rows(path, table):
    """Remove the data rows of one marked table; the markers, the header and its rule stay."""
    text = path.read_text(encoding="utf-8")
    m = re.search(rf"(<!-- {table}:begin[^>]*-->\n\|[^\n]*\n\|[-:| ]*\n)(.*?)(<!-- {table}:end -->)", text, re.S)
    if m is None:
        raise SystemExit(f"{path.name}: no table {table}")
    rows = [ln for ln in m.group(2).splitlines() if ln.startswith("|")]
    path.write_text(text[:m.start(2)] + text[m.end(2):], encoding="utf-8", newline="\n")
    return len(rows)


def script(copy, name, *args, timeout=1800):
    """Run one of the copy's own scripts; (exit status, its lines)."""
    r = subprocess.run([sys.executable, "-I", "-B", str(copy / SCRIPTS / name), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip() and "duplicate image" not in ln]
    return r.returncode, lines


def new_copy(scratch, name):
    trial = load(HERE / "trial.py", "trial")
    if scratch == ROOT or ROOT in scratch.parents:
        raise SystemExit(f"{scratch} is inside the repository: give a directory outside it")
    copy = scratch / name
    if copy.exists():
        raise SystemExit(f"{copy} exists: give a new scratch directory, or remove that one yourself")
    trial.copy(copy)
    mp = load(copy / SCRIPTS / "make_pcb.py", f"make_pcb_{name}")
    if mp.ROOT != copy:
        raise SystemExit(f"the copied make_pcb.py resolves its root to {mp.ROOT}, not {copy}")
    return copy, mp


def show(lines, last=12):
    for ln in lines[-last:]:
        print("   ", ln)


# ---- stages ----------------------------------------------------------------------------------
def base(scratch):
    copy, _ = new_copy(scratch, "base")
    n = strip_rows(copy / ROUTING, "patch")
    s = strip_rows(copy / PLACEMENT, "silk")
    print(f"base: {n} patch rows and {s} silk rows left out")
    status, lines = script(copy, "make_pcb.py", "--no-check")
    show(lines)
    print(f"base: make_pcb.py exit {status}")
    return status


def drc(pcb, out):
    cli = pathlib.Path(sys.executable).with_name("kicad-cli.exe")
    r = subprocess.run([str(cli), "pcb", "drc", "--severity-all", "--format", "json", "--units", "mm", "-o", str(out),
                        str(pcb)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    if not out.exists():
        raise SystemExit(f"kicad-cli wrote no DRC report (exit {r.returncode}): {(r.stdout + r.stderr)[-300:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def pre_route(mp, copy):
    """make_pcb.py's build(), stopped after the GND fanout: the board the router is given."""
    pcb, pro, _, dru = mp.proj.paths(mp.SRC)
    place = mp.read_placement(mp.DOC)
    routing, _ = mp.read_routing(mp.DOC, mp.ROUTING)
    out = copy / "pre"
    out.mkdir()
    with tempfile.TemporaryDirectory(dir=copy) as tmp:
        comps, pins = mp.read_netlist(mp.export_netlist(pathlib.Path(tmp)))
    for f in (pro, dru):
        shutil.copyfile(f, out / f.name)
    path = out / pcb.name
    pcbnew.KIID.SeedGenerator(mp.UUID_SEED)
    mp.proj.make_board(path)
    mp.proj.insert_stackup(path)
    board = pcbnew.LoadBoard(str(path))
    nets = {}
    for name in sorted(set(pins.values())):
        nets[name] = pcbnew.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    for ref in sorted(comps, key=mp.natural):
        mp.add_footprint(board, nets, ref, comps[ref], pins, place[ref])
    mp.route.plane(board, routing["zones"], mp.proj.SIZE_MM)
    n_t, n_v = mp.route.apply_rows(board, routing["rows"])
    hs = {n for p in routing["pairs"] for n in p["nets"]}
    n_f, unfanned = mp.route.gnd_fanout(board, routing["epads"], hs,
                                        (mp.proj.VIA_HOLE_TO_HOLE, mp.proj.RULES["min_hole_to_hole"]))
    mp.route.fill(board)
    if not pcbnew.SaveBoard(str(path), board):
        raise SystemExit("pcbnew could not save the board")
    print(f"{copy.name}: {n_t} hand-drawn track segments, {n_v} vias; GND fanout {n_f} vias,"
          f" {len(unfanned)} pad(s) left to the router{': ' + ' '.join(unfanned) if unfanned else ''}")
    # the port paths are hand-drawn, so their copper can be weighed before the router runs
    cr = load(copy / SCRIPTS / "check_routing.py", f"check_routing_{copy.name.replace('-', '_')}")
    rep = cr.Report()
    totals = cr.check_port_paths(rep, board, mp.doc_tables(mp.ROUTING.read_text(encoding="utf-8")))
    print(f"{copy.name}: port paths " + ", ".join(f"{p} {t:.2f} mOhm" for p, t in sorted(totals.items())))
    return path, rep.fails


def prepared(scratch, name, extra=()):
    """A C2 copy named `name`, built up to the GND fanout; extra = (old, new) lines of the routing
    document changed after c2_routing.py. Returns the lines of what is wrong before the router."""
    copy, mp = new_copy(scratch, name)
    load(HERE / "c2_change.py", "c2_change").apply(copy / PLACEMENT)
    n = load(HERE / "c2_routing.py", "c2_routing").apply(copy / ROUTING)
    s = strip_rows(copy / PLACEMENT, "silk")
    text = (copy / ROUTING).read_text(encoding="utf-8")
    for old, new in extra:
        if text.count(old + "\n") != 1:
            raise SystemExit(f"{name}: the line to change is in the routing document {text.count(old)} times: {old}")
        text = text.replace(old + "\n", new + "\n")
    (copy / ROUTING).write_text(text, encoding="utf-8", newline="\n")
    print(f"{name}: placement and routing documents changed; {n} patch rows and {s} silk rows left out")
    path, wrong = pre_route(mp, copy)
    report = drc(path, copy / "pre" / "drc.json")
    kinds = collections.Counter(v["type"] for v in report.get("violations", []))
    waiting = {k: kinds.pop(k) for k in PRE_EXPECTED if k in kinds}
    print(f"{name}: DRC before the router: {sum(kinds.values())} violation(s) {dict(sorted(kinds.items()))},"
          f" beside the expected {waiting}; {len(report.get('unconnected_items', []))} connections for the router")
    for v in report.get("violations", []):
        if v["type"] not in PRE_EXPECTED:
            wrong.append(f"FAIL DRC: {v['severity']} {v['type']}: "
                         + "; ".join(i["description"] for i in v.get("items", [])))
    for ln in wrong:
        print("   ", ln)
    return wrong


def prepare(scratch):
    return 1 if prepared(scratch, "c2") else 0


def negative(scratch):
    """Each fault is drawn into its own copy; the stage passes when every one is reported."""
    ok = True
    for name, old, new, want in NEGATIVE:
        wrong = prepared(scratch, f"neg-{name}", [(old, new)])
        caught = any(want in ln for ln in wrong)
        ok &= caught
        print(f"negative {name}: {'caught' if caught else 'NOT CAUGHT'} (want a line with {want!r})\n")
    return 0 if ok else 1


def route(scratch, argv):
    if len(argv) != 4 or argv[0] != "--java" or argv[2] != "--jar":
        raise SystemExit("usage: route_trial.py <scratch> route --java <java.exe> --jar <freerouting.jar>")
    copy = scratch / "c2"
    status, lines = script(copy, "autoroute.py", "--java", argv[1], "--jar", argv[3], timeout=3 * 3600)
    show(lines, 20)
    print(f"route: autoroute.py exit {status}")
    if status:
        return status
    status, lines = script(copy, "make_pcb.py", "--no-check")
    show(lines)
    print(f"route: make_pcb.py exit {status}")
    return status


# ---- the report ------------------------------------------------------------------------------
def read_board(copy):
    """What the board file itself says: copper per layer, vias, the pairs' lengths."""
    board = pcbnew.LoadBoard(str(copy / PCB))
    length, pair, n_via = collections.Counter(), collections.Counter(), 0
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            n_via += 1
            continue
        mm = pcbnew.ToMM(t.GetLength())
        length[board.GetLayerName(t.GetLayer())] += mm
        net = t.GetNetname()
        if net[:-2] in PAIRS:
            pair[net] += mm
    return dict(length={k: round(v, 1) for k, v in sorted(length.items())}, vias=n_via,
                pairs={k: round(v, 2) for k, v in sorted(pair.items())})


def checker(copy, name):
    out = copy / "reports" / name.split(".")[0]
    status, lines = script(copy, name, "--reports", out)
    fails = [ln for ln in lines if ln.startswith("FAIL ")]
    who = collections.Counter(ln[5:].split(":", 1)[0] for ln in fails)
    kinds = collections.Counter(" ".join(ln.split(":", 2)[1].split()[:2]) for ln in fails if ln.startswith("FAIL DRC:"))
    return dict(status=status, fails=fails, who=dict(sorted(who.items())), drc=dict(sorted(kinds.items())),
                tail=[ln for ln in lines if not ln.startswith("FAIL ")][-4:])


def one(copy):
    r = dict(board=read_board(copy), pcb=checker(copy, "check_pcb.py"), routing=checker(copy, "check_routing.py"))
    for ln in r["routing"]["tail"]:
        m = STATS.search(ln)
        if m:
            r["stats"] = dict(tracks=int(m.group(1)), vias=int(m.group(2)), in2_analog=int(m.group(3)),
                              crossings=int(m.group(4)), ports=m.group(5),
                              unconnected=None if m.group(6) == "?" else int(m.group(6)))
    record = json.loads((copy / RECORD).read_text(encoding="utf-8"))
    r["router"] = {k: record.get(k) for k in ("passes", "router_unrouted", "dsn_sha256", "ses_sha256")}
    cli = pathlib.Path(sys.executable).with_name("kicad-cli.exe")
    png = copy.parent / f"render_{copy.name}_top.png"
    subprocess.run([str(cli), "pcb", "render", "--side", "top", "--width", "1600", "--height", "1152",
                    "--background", "opaque", "-o", str(png), str(copy / PCB)],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    r["render"] = png.name if png.exists() else None
    return r


def report(scratch):
    res = {}
    for name in BOARDS:
        if not (scratch / name / PCB).exists():
            raise SystemExit(f"{scratch / name}: no board; run the stage that builds it")
        res[name] = one(scratch / name)
    (scratch / "result.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n", encoding="utf-8",
                                         newline="\n")
    b, c = res["base"], res["c2"]

    def row(label, f):
        print(f"{label:<46} {str(f(b)):>26} {str(f(c)):>26}")

    print(f"{'':<46} {'board (session, no patch)':>26} {'C2 (new session, no patch)':>26}")
    row("router passes", lambda r: r["router"]["passes"])
    row("router's own unrouted count", lambda r: r["router"]["router_unrouted"])
    row("DRC unconnected items", lambda r: r.get("stats", {}).get("unconnected"))
    row("D36 places (FAIL analog)", lambda r: r["routing"]["who"].get("analog", 0))
    row("tracks / vias", lambda r: f"{r.get('stats', {}).get('tracks')} / {r.get('stats', {}).get('vias')}")
    row("port paths", lambda r: r.get("stats", {}).get("ports"))
    row("check_pcb.py failed", lambda r: len(r["pcb"]["fails"]))
    row("check_routing.py failed", lambda r: len(r["routing"]["fails"]))
    for name in BOARDS:
        r = res[name]
        print(f"\n{name}: check_routing.py FAIL lines by subject: {r['routing']['who']}")
        print(f"{name}: of them DRC violations by type: {r['routing']['drc']}")
        print(f"{name}: check_pcb.py FAIL lines by subject: {r['pcb']['who']}")
        print(f"{name}: track length by layer (mm): {r['board']['length']}; vias {r['board']['vias']}")
        print(f"{name}: pair conductors (mm): {r['board']['pairs']}")
        for ln in r["routing"]["tail"]:
            print(f"{name}: {ln}")
    print(f"\nwrote {scratch / 'result.json'}; renders: {b['render']}, {c['render']}")
    return 0


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) < 3 or argv[2] not in ("base", "prepare", "negative", "route", "report"):
        raise SystemExit("usage: route_trial.py <scratch directory>"
                         " base | prepare | negative | route --java .. --jar .. | report")
    scratch = pathlib.Path(argv[1]).resolve()
    if scratch == ROOT or ROOT in scratch.parents:
        raise SystemExit(f"{scratch} is inside the repository: give a directory outside it")
    scratch.mkdir(parents=True, exist_ok=True)
    if argv[2] == "base":
        return base(scratch)
    if argv[2] == "prepare":
        return prepare(scratch)
    if argv[2] == "negative":
        return negative(scratch)
    if argv[2] == "route":
        return route(scratch, argv[3:])
    return report(scratch)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
