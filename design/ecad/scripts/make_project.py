"""Write the KiCad 9 project skeleton of Rev0.5 (D32): design/ecad/source/usb-power-hub.*

Run with KiCad's own Python, which carries the pcbnew module, from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_project.py

It writes three files:
- usb-power-hub.kicad_dru: JLCPCB's hole figures for vias and PTH pads (HOLE_RULES), as
  custom DRC rules, which override the board minimums of the .kicad_pro (issue #8);
- usb-power-hub.kicad_pcb: 4 copper layers; the JLC04161H-7628 stackup (D27), read from
  design/experiments/stackup-impedance/stackups.json, which holds JLCPCB's published table;
  leaded HASL (D30); 1.6 mm nominal thickness; the 100 x 72 mm outline (D24), lower-left
  corner at (50, 122) mm on the sheet, which is also the drill and placement origin; the
  title block.
- usb-power-hub.kicad_pro: the CLAUDE.md 5.3 starting rules as board constraints, and two
  net classes: Default, and USB_HS with D27's provisional pair, W 0.31 / S 0.15 mm, which
  every net named USB_* joins (the captured D+/D- nets, issue #6 P2).
The schematic files are make_schematic.py's; this script does not touch them, but shares
its title block and UUID namespace with them. make_pcb.py rebuilds the board with every part
placed, from make_board() and insert_stackup() here, so it runs after this script
(design/ecad/README.md).
UUIDs are derived from names (uuid5), so a re-run writes the same bytes. KiCad's local-state
file (.kicad_prl) is deleted; it is gitignored and KiCad recreates it.

Order matters. pcbnew caches the project of a board it has loaded, and SaveBoard writes that
cache back to .kicad_pro, so the project is edited after the last SaveBoard, and the check
runs in a new process (`--check [DIR]`), where pcbnew reads only what is in the files.
test_make_project.py corrupts copies of the files and expects the check to name each fault.
Exit status: 0 = written and checked; 1 = a check failed.

What it CANNOT see (CLAUDE.md 8):
- whether the constraints are JLCPCB's current capabilities (CLAUDE.md 9: recheck at every
  release);
- what the custom rules do on a board: that is DRC's, and test_check_routing.py shows each
  rule failing a corrupted board;
- the VBUS trunk width, which needs a current and temperature-rise calculation before
  routing (issue #6, P4);
- which nets are USB pairs: USB_HS is assigned by the name pattern USB_*, and
  check_schematic.py checks that exactly the netlist document's D+/D- nets carry it;
- the solder-mask thickness and the dielectric loss tangent, which JLCPCB's stackup table
  does not give. KiCad adds its defaults, 0.01 mm per mask and tan d 0.02, so its stackup
  editor sums to 1.6062 mm, while the board keeps 1.6 mm, the thickness ordered (D27).
"""
import json
import pathlib
import re
import subprocess
import sys
import uuid

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "design" / "ecad" / "source"
NAME = "usb-power-hub"
STACKUPS = ROOT / "design" / "experiments" / "stackup-impedance" / "stackups.json"
STACKUP_ID = "JLC04161H-7628"                        # D27
FINISH = "HAL SnPb"                                  # KiCad's name for leaded HASL (D30)
ORIGIN_MM = (50.0, 122.0)                            # board lower-left on the sheet
SIZE_MM = (100.0, 72.0)                              # D24
THICKNESS_MM = 1.6                                   # CLAUDE.md 1, the ordered thickness
DATE = "2026-11-04"
TITLE = "USB Power-Control Hub"
REV = "Rev0.5"
COMMENTS = ("WIP - MANUFACTURING PROHIBITED",
            "Source: design/circuit/CIRCUIT_DESIGN_Rev0.5.md",
            "Stackup JLC04161H-7628 (D27), leaded HASL (D30)")
UUID_NS = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/tsuyoshi-otake/usb-power-hub")

# CLAUDE.md 5.3 starting values (mm). They are starting rules, not a capability limit. The hole
# figures are JLCPCB's (pcb-capabilities, read 2026-11-12, issue #8): the via drill is 0.30 mm,
# because a 0.25 mm via hole puts the order in the "0.25mm/(0.35/0.4mm)" class, which adds
# "4-Wire Kelvin Test", "Min via hole size/diameter" and FR4 Tg155 ($37.65 on the quote form,
# 2026-11-12). The via copper stays 0.45 mm: 0.15 mm larger than the hole, JLCPCB's preferred margin.
RULES = {
    "min_clearance": 0.15,               # trace spacing >= 0.15
    "min_track_width": 0.15,             # signal 0.15-0.20
    "min_via_diameter": 0.45,            # via 0.45 / 0.30 (0.60 / 0.30 where space allows)
    "min_through_hole_diameter": 0.30,   # the standard via class "0.3mm/(0.4/0.45mm)"
    "min_via_annular_width": 0.075,      # (0.45 - 0.30) / 2
    # Every other hole. KiCad's DSN export also sizes the router's keepout around each NPTH hole
    # with min_hole_clearance, so lowering it changes the router input (issue #8).
    "min_hole_clearance": 0.25,          # JLCPCB: NPTH to track 0.2; vias and PTH: HOLE_RULES
    "min_hole_to_hole": 0.25,            # vias and pad holes: HOLE_RULES
    "min_copper_edge_clearance": 0.30,   # copper to routed edge >= 0.30
    "min_text_height": 1.0,              # Latin silkscreen >= 1.0 mm (CLAUDE.md 6)
    "min_text_thickness": 0.15,          # stroke >= 0.15 mm
}
# JLCPCB's hole figures for vias and for plated through-hole (PTH) pads, as custom rules
# (.kicad_dru); a custom rule overrides the board minimum above (tried 2026-11-12: a via rule of
# 0.20 under a board minimum of 0.25 removed all 199 via hole_clearance violations).
# KiCad applies a pair rule to both items' holes, in either order, so a rule cannot give a via's
# hole 0.20 mm and a PTH pad's hole 0.28 mm in the same via-pad pair: the via rule governs that
# pair. The PTH side still holds: a PTH ring >= 0.15 mm plus the 0.15 mm copper clearance keeps
# every other net's copper >= 0.30 mm from a PTH hole.
VIA_HOLE_CLEARANCE = 0.20                # JLCPCB "Via hole to Track"
VIA_HOLE_TO_HOLE = 0.20                  # JLCPCB "Via Hole-to-Hole Spacing"; route.py's fanout too
HOLE_RULES = f"""(version 1)
# Written by design/ecad/scripts/make_project.py; JLCPCB pcb-capabilities, read 2026-11-12 (issue #8).
(rule "JLCPCB via hole to copper {VIA_HOLE_CLEARANCE:.2f}"
  (constraint hole_clearance (min {VIA_HOLE_CLEARANCE:.2f}mm))
  (condition "A.Type == 'Via'"))
(rule "JLCPCB via hole to via hole {VIA_HOLE_TO_HOLE:.2f}"
  (constraint hole_to_hole (min {VIA_HOLE_TO_HOLE:.2f}mm))
  (condition "A.Type == 'Via' && B.Type == 'Via'"))
(rule "JLCPCB PTH to copper 0.28"
  (constraint hole_clearance (min 0.28mm))
  (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole' && B.Type != 'Via'"))
(rule "JLCPCB PTH annular ring 0.15"
  (constraint annular_width (min 0.15mm))
  (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'"))
(rule "JLCPCB pad hole to pad hole 0.45"
  (constraint hole_to_hole (min 0.45mm))
  (condition "A.Type == 'Pad' && B.Type == 'Pad'"))
"""
TRACK_WIDTHS = [0.15, 0.20, 0.31]
VIAS = [(0.45, 0.30), (0.60, 0.30)]
USB_PAIR = (0.31, 0.15)                  # D27: W / S on L1 over L2, provisional
CLASSES = {
    "Default": {"track_width": 0.20, "clearance": 0.15, "via_diameter": 0.45,
                "via_drill": 0.30},
    "USB_HS": {"track_width": USB_PAIR[0], "clearance": 0.15, "via_diameter": 0.45,
               "via_drill": 0.30, "diff_pair_width": USB_PAIR[0],
               "diff_pair_gap": USB_PAIR[1]},
}
NETCLASS_PATTERNS = [("USB_HS", "USB_*")]    # the netlist document names every D+/D- net USB_*


def mm(v):
    return pcbnew.FromMM(v)


def stackup():
    """The JLC04161H-7628 layer list: (KiCad layer, type, thickness, material, Dk)."""
    data = json.loads(STACKUPS.read_text(encoding="utf-8"))
    s = next(x for x in data["stackups"] if x["id"] == STACKUP_ID)
    (pt,), (pb,) = s["prepreg_top"], s["prepreg_bottom"]
    inner = s["inner"]
    return [
        ("F.Cu", "copper", s["copper"]["outer_mm"], None, None),
        ("dielectric 1", "prepreg", pt["thickness_mm"], pt["style"], pt["dk"]),
        ("In1.Cu", "copper", inner["l2_copper_mm"], None, None),
        ("dielectric 2", "core", inner["core_mm"], "FR4", inner["core_dk"]),
        ("In2.Cu", "copper", inner["l3_copper_mm"], None, None),
        ("dielectric 3", "prepreg", pb["thickness_mm"], pb["style"], pb["dk"]),
        ("B.Cu", "copper", s["copper"]["bottom_mm"], None, None),
    ]


def stackup_sexpr(layers):
    t = "\t\t\t"
    out = ["\t\t(stackup",
           f'{t}(layer "F.SilkS"\n{t}\t(type "Top Silk Screen")\n{t})',
           f'{t}(layer "F.Paste"\n{t}\t(type "Top Solder Paste")\n{t})',
           f'{t}(layer "F.Mask"\n{t}\t(type "Top Solder Mask")\n{t})']
    for name, typ, th, mat, dk in layers:
        body = [f'(type "{typ}")', f"(thickness {th:g})"]
        if mat:
            body += [f'(material "{mat}")', f"(epsilon_r {dk:g})"]
        out.append(f'{t}(layer "{name}"\n' + "".join(f"{t}\t{b}\n" for b in body) + f"{t})")
    out += [f'{t}(layer "B.Mask"\n{t}\t(type "Bottom Solder Mask")\n{t})',
            f'{t}(layer "B.Paste"\n{t}\t(type "Bottom Solder Paste")\n{t})',
            f'{t}(layer "B.SilkS"\n{t}\t(type "Bottom Silk Screen")\n{t})',
            f'{t}(copper_finish "{FINISH}")',
            f"{t}(dielectric_constraints no)",
            "\t\t)"]
    return "\n".join(out) + "\n"


def make_board(pcb_path):
    board = pcbnew.NewBoard(str(pcb_path))
    board.SetCopperLayerCount(4)
    x0, y1 = ORIGIN_MM
    x1, y0 = x0 + SIZE_MM[0], y1 - SIZE_MM[1]
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(pcbnew.VECTOR2I(mm(x0), mm(y0)))
    edge.SetEnd(pcbnew.VECTOR2I(mm(x1), mm(y1)))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mm(0.05))
    board.Add(edge)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(mm(THICKNESS_MM))
    ds.SetAuxOrigin(pcbnew.VECTOR2I(mm(x0), mm(y1)))
    ds.SetGridOrigin(pcbnew.VECTOR2I(mm(x0), mm(y1)))
    tb = board.GetTitleBlock()
    tb.SetTitle(TITLE)
    tb.SetRevision(REV)
    tb.SetDate(DATE)
    for i, c in enumerate(COMMENTS):
        tb.SetComment(i, c)
    if not pcbnew.SaveBoard(str(pcb_path), board):
        raise SystemExit("pcbnew could not save the board")


def insert_stackup(pcb_path):
    text = pcb_path.read_text(encoding="utf-8")
    if "(stackup" in text:
        raise SystemExit("the new board already has a stackup")
    text = text.replace("\t(setup\n", "\t(setup\n" + stackup_sexpr(stackup()), 1)
    pcb_path.write_text(text, encoding="utf-8", newline="\n")


def edit_project(pro_path):
    pro = json.loads(pro_path.read_text(encoding="utf-8"))
    dsj = pro["board"]["design_settings"]
    dsj["rules"].update(RULES)
    dsj["track_widths"] = [0.0] + TRACK_WIDTHS          # entry 0 = "use net class"
    dsj["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}] + [
        {"diameter": d, "drill": h} for d, h in VIAS]
    dsj["diff_pair_dimensions"] = [{"gap": 0.0, "via_gap": 0.0, "width": 0.0},
                                   {"gap": USB_PAIR[1], "via_gap": USB_PAIR[1],
                                    "width": USB_PAIR[0]}]
    template = next(c for c in pro["net_settings"]["classes"] if c["name"] == "Default")
    classes = []
    for name, vals in CLASSES.items():
        c = dict(template)
        c.update(vals)
        c["name"] = name
        if name != "Default":
            c["priority"] = 0
        classes.append(c)
    pro["net_settings"]["classes"] = classes
    pro["net_settings"]["netclass_patterns"] = [{"netclass": c, "pattern": p}
                                                for c, p in NETCLASS_PATTERNS]
    pro_path.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8", newline="\n")


def fix_uuids(path, prefix):
    """Replace every uuid with one derived from its position, so re-runs are identical."""
    n = 0

    def sub(m):
        nonlocal n
        n += 1
        return f'(uuid "{uuid.uuid5(UUID_NS, f"{prefix}/{n}")}")'

    text = re.sub(r'\(uuid "[0-9a-fA-F-]{36}"\)', sub, path.read_text(encoding="utf-8"))
    path.write_text(text, encoding="utf-8", newline="\n")
    return n


API_RULES = {  # pcbnew design-settings attribute -> RULES key, read back in a fresh process
    "m_MinClearance": "min_clearance", "m_TrackMinWidth": "min_track_width",
    "m_ViasMinSize": "min_via_diameter", "m_MinThroughDrill": "min_through_hole_diameter",
    "m_ViasMinAnnularWidth": "min_via_annular_width",
    "m_HoleClearance": "min_hole_clearance", "m_HoleToHoleMin": "min_hole_to_hole",
    "m_CopperEdgeClearance": "min_copper_edge_clearance",
}
API_CLASS = {"track_width": "GetTrackWidth", "clearance": "GetClearance",
             "via_diameter": "GetViaDiameter", "via_drill": "GetViaDrill",
             "diff_pair_width": "GetDiffPairWidth", "diff_pair_gap": "GetDiffPairGap"}


def check(pcb_path, pro_path, dru_path):
    """Run in a fresh process: pcbnew caches a loaded project, so only a new process
    shows what KiCad reads from the files."""
    fails = []
    if not dru_path.exists() or dru_path.read_text(encoding="utf-8") != HOLE_RULES:
        fails.append(f"{dru_path.name} is not the rule set HOLE_RULES")
    board = pcbnew.LoadBoard(str(pcb_path))
    ds = board.GetDesignSettings()
    for attr, key in API_RULES.items():
        got = pcbnew.ToMM(getattr(ds, attr))
        if abs(got - RULES[key]) > 1e-6:
            fails.append(f"pcbnew reads {attr} = {got}, want {RULES[key]}")
    ns = ds.m_NetSettings
    for name, vals in CLASSES.items():
        nc = ns.GetDefaultNetclass() if name == "Default" else ns.GetNetClassByName(name)
        if nc is None or nc.GetName() != name:
            fails.append(f"pcbnew finds no net class {name}")
            continue
        for k, v in vals.items():
            got = pcbnew.ToMM(getattr(nc, API_CLASS[k])())
            if abs(got - v) > 1e-6:
                fails.append(f"pcbnew reads {name}.{k} = {got}, want {v}")
    if board.GetCopperLayerCount() != 4:
        fails.append(f"copper layers {board.GetCopperLayerCount()}")
    if abs(pcbnew.ToMM(ds.GetBoardThickness()) - THICKNESS_MM) > 1e-6:
        fails.append(f"board thickness {pcbnew.ToMM(ds.GetBoardThickness())} mm")
    edges = [d for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts]
    if len(edges) != 1:
        fails.append(f"{len(edges)} Edge.Cuts shapes")
    else:
        bb = edges[0].GetBoundingBox()
        w = pcbnew.ToMM(bb.GetWidth()) - 0.05
        h = pcbnew.ToMM(bb.GetHeight()) - 0.05
        if abs(w - SIZE_MM[0]) > 1e-6 or abs(h - SIZE_MM[1]) > 1e-6:
            fails.append(f"outline {w:.3f} x {h:.3f} mm")
    text = pcb_path.read_text(encoding="utf-8")
    for name, typ, th, mat, dk in stackup():
        m = re.search(r'\(layer "' + re.escape(name) + r'"\s*\(type "' + typ +
                      r'"\)\s*(?:\(color "[^"]*"\)\s*)?\(thickness ([0-9.]+)\)', text)
        if not m or abs(float(m.group(1)) - th) > 1e-9:
            fails.append(f"stackup layer {name}: {m.group(1) if m else 'missing'}, want {th}")
        if mat and f"(epsilon_r {dk:g})" not in text:
            fails.append(f"stackup Dk {dk} missing")
    if f'(copper_finish "{FINISH}")' not in text:
        fails.append("copper finish")
    pro = json.loads(pro_path.read_text(encoding="utf-8"))
    rules = pro["board"]["design_settings"]["rules"]
    for k, v in RULES.items():
        if abs(rules.get(k, -1) - v) > 1e-9:
            fails.append(f"rule {k} = {rules.get(k)}, want {v}")
    got = {c["name"]: c for c in pro["net_settings"]["classes"]}
    for name, vals in CLASSES.items():
        for k, v in vals.items():
            if name not in got or abs(got[name].get(k, -1) - v) > 1e-9:
                fails.append(f"net class {name}.{k} != {v}")
    patterns = [(p.get("netclass"), p.get("pattern"))
                for p in pro["net_settings"].get("netclass_patterns") or []]
    if patterns != NETCLASS_PATTERNS:
        fails.append(f"netclass patterns {patterns}, want {NETCLASS_PATTERNS}")
    return fails


def paths(out=OUT):
    return (out / f"{NAME}.kicad_pcb", out / f"{NAME}.kicad_pro", out / f"{NAME}.kicad_prl",
            out / f"{NAME}.kicad_dru")


def run_check(out):
    pcb, pro, prl, dru = paths(out)
    fails = check(pcb, pro, dru)
    if prl.exists():
        prl.unlink()                         # LoadBoard may recreate the local-state file
    print("checks: " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  - " + f)
    return 1 if fails else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:2] == ["--check"]:
        if len(sys.argv) > 3:
            raise SystemExit("usage: make_project.py [--check [DIR]]")
        return run_check(pathlib.Path(sys.argv[2]) if len(sys.argv) == 3 else OUT)
    if sys.argv[1:]:
        raise SystemExit("usage: make_project.py [--check [DIR]]")
    OUT.mkdir(parents=True, exist_ok=True)
    pcb, pro, prl, dru = paths()
    for p in (pcb, pro):
        if p.exists():
            p.unlink()                       # regenerated from scratch every run
    dru.write_text(HOLE_RULES, encoding="utf-8", newline="\n")
    make_board(pcb)
    insert_stackup(pcb)
    # round trip: pcbnew reads the stackup text back and writes it normalized
    board = pcbnew.LoadBoard(str(pcb))
    if not pcbnew.SaveBoard(str(pcb), board):
        raise SystemExit("pcbnew could not re-save the board")
    n = fix_uuids(pcb, "pcb")
    edit_project(pro)                        # last, so no SaveBoard overwrites it
    if prl.exists():
        prl.unlink()
    print(f"wrote {pcb.name}, {pro.name}, {dru.name} in {OUT.relative_to(ROOT).as_posix()};"
          f" {n} board uuid(s) fixed; the board is bare: run make_pcb.py to place the parts")
    th = sum(t for _, _, t, _, _ in stackup())
    print(f"stackup {STACKUP_ID}: copper + dielectric {th:.4f} mm; finish {FINISH};"
          f" net classes {', '.join(CLASSES)}")
    sys.stdout.flush()                       # keep this output ahead of the child's
    return subprocess.run([sys.executable, "-I", "-B", str(pathlib.Path(__file__).resolve()),
                           "--check"], check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
