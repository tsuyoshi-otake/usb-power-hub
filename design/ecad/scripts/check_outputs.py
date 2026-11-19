"""Check the Rev0.6 manufacturing candidate against the board it was made from (issue #6 P5;
CLAUDE.md 2, 8 Gerber and BOM/CPL gates).

Run with KiCad's own Python from the repository root (make_outputs.py runs it after it writes
the set):

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_outputs.py [--out DIR] [--src DIR]

--out holds the set (default manufacturing/working/rev0.6), --src the KiCad project
(default design/ecad/source); the tests pass corrupted copies. The files are read with this
script's own parsers, the board with pcbnew; nothing of make_outputs.py is imported.

 1. Set: exactly the expected files; SHA256SUMS.txt lists every other file once, with its
    SHA-256.
 2. Manifest: state WIP and "MANUFACTURING PROHIBITED"; every source file it lists has the
    SHA-256 of the file in --src now (a stale set fails), and every .kicad_sch of --src is
    listed; revision, stackup and finish as the board's.
 3. Gerber zip: one file per layer, with JLCPCB's Protel extension, millimetres, its X2
    file function, the date fixed; Edge.Cuts spans the board's outline (100 x 72 mm at
    (0, 0)-(100, 72): the auxiliary origin is the board's lower-left corner, as the CPL's,
    and y points up); B.Paste has no object and B.SilkS no dark one (Top only).
 4. Drill: PTH and NPTH Excellon in mm, each with its map; every hole of the board, counted
    by diameter, plated or not as the board has it (pads and vias); every oblong drill of
    the board (the receptacles' plated shell slots, D37) is a routed slot (G85) of the drill
    file with the same centre, length, width and axis, and the file has no other slot.
 5. BOM: JLCPCB's header; exactly one row per LCSC part (JLCPCB's part mapping selects neither
    of two rows with one LCSC number), Comment and Footprint the row's first designator's Value
    and footprint; the designators are exactly the footprints with an LCSC field that are
    not BOM-excluded; every part's Class is Basic, or Extended for C2040 (D29), C5137013
    (D31) or C2765186 (D37) only (D22).
 6. CPL: JLCPCB's header; the BOM's designators; Mid X/Y the footprint's origin in the
    board frame plus the part's shift in design/ecad/jlcpcb_model_frame.json (--frames), turned
    with the footprint (0.0001 mm), inside the outline; the footprint's origin within MID_TOL
    (0.05 mm) of the centre of its F.Fab body (a Kelvin land's sense pads make its pads' centre
    another point); Layer Top; Rotation the footprint's orientation plus the part's add in that
    table. The table: every entry is used by a BOM line, has an add (90, 180 or 270), a shift
    (two numbers, none longer than SHIFT_MAX) or both, and nothing else changes the CPL.
 7. Hand list: exactly the footprints with an Akizuki field, none of them in the BOM or CPL.
 8. Documents: the schematic PDF has one page per sheet instance; the assembly PDF one page;
    each preview a PNG at least PREVIEW_MIN_W wide with the board's aspect (3 %); ERC and DRC reports with 0 violations, 0 unconnected
    items and 0 parity items.
 9. Privacy and determinism: no file holds a local user path, an e-mail address or a
    creation date other than 1980-01-01 (CLAUDE.md Safety).
Exit status: 0 = every check passed; 1 = at least one failed. Each failure prints as
`FAIL <who>: <what>`.

What it CANNOT see:
- whether JLCPCB reads the files as meant: its DFM, part mapping and placement preview are
  the evidence (CLAUDE.md 8, JLCPCB gate). The uploads of Rev0.4 (2026-11-11 and -12) are
  recorded in manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md with the SHA-256 of the three
  files they saw, Rev0.5's (2026-11-13) in manufacturing/releases/rev0.5/r01/JLCPCB_REVIEW.md
  and r02's; Rev0.6 has had none. This checker does not read those files, so it cannot tell a review that has gone
  stale.
- whether the table's numbers are right: it checks that the CPL follows the table and that the
  table is well formed, not what JLCPCB's models look like. The receptacle C2765186's shift
  (1.375 mm) is what the placement preview showed, to about 0.04 mm, and a preview is not
  JLCPCB's pick-and-place.
- the turn of a shift at 90 and 270 degrees: the four receptacles stand at 0 and 180, where
  the sine is 0. turned() is compared with KiCad's own placement of every pad by
  test_check_outputs.py, at all four orientations.
- Gerber geometry beyond the outline's extent and object counts: the copper is the board's
  because kicad-cli plotted it, and DRC (check_pcb.py) checks the board itself.
- the content of the PDFs and renders beyond their page count and image size.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import pathlib
import re
import struct
import sys
import zipfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
PREFIX = "UsbPowerHub_Main_Rev0.6"
ORIGIN = (50.0, 122.0)
BOARD = (100.0, 72.0)
MID_TOL = 0.05
POS_TOL = 0.0001
SHIFT_MAX = 5.0                           # mm: a guard against a slipped decimal (13.75 for 1.375), not a measurement
EXTENDED = {"C2040": "D29", "C5137013": "D31", "C2765186": "D37"}
PREVIEW_MIN_W = 1200                      # kicad-cli renders a little under the size asked
ASPECT = 100.0 / 72.0
ARTIFACTS = ("Gerber.zip", "BOM_JLCPCB.csv", "CPL_JLCPCB.csv", "HandSolder.csv", "Schematic.pdf",
             "Assembly_Top.pdf", "Preview_Top.png", "Preview_Bottom.png", "ERC.json", "DRC.json")
GERBERS = {"F_Cu.gtl": "Copper,L1,Top", "In1_Cu.g1": "Copper,L2,Inr", "In2_Cu.g2": "Copper,L3,Inr",
           "B_Cu.gbl": "Copper,L4,Bot", "F_Paste.gtp": "Paste,Top", "B_Paste.gbp": "Paste,Bot",
           "F_Silkscreen.gto": "Legend,Top", "B_Silkscreen.gbo": "Legend,Bot",
           "F_Mask.gts": "Soldermask,Top", "B_Mask.gbs": "Soldermask,Bot", "Edge_Cuts.gm1": "Profile,NP"}
DRILLS = ("PTH.drl", "NPTH.drl", "PTH-drl_map.gbr", "NPTH-drl_map.gbr")
BOM_HEAD = ["Comment", "Designator", "Footprint", "JLCPCB Part #"]
CPL_HEAD = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
HAND_HEAD = ["Designator", "Qty", "Manufacturer", "MPN", "Akizuki", "Class", "Footprint"]
PRIVATE = [re.compile(rb"[A-Za-z]:[\\/]+Users[\\/]", re.I), re.compile(rb"/home/[a-z]", re.I),
           re.compile(rb"[\w.+-]+@[\w-]+\.[\w.]+")]
DATE = re.compile(rb"(?<!\d)(\d{4})-(\d\d)-(\d\d)[T ]\d\d:\d\d:\d\d|\(D:(\d{8})")


class Report:
    def __init__(self):
        self.fails, self.count = [], 0

    def check(self, cond, who, what):
        self.count += 1
        if not cond:
            self.fails.append(f"FAIL {who}: {what}")
        return cond


def sha(b):
    return hashlib.sha256(b).hexdigest()


def frame(v):
    return pcbnew.ToMM(v.x) - ORIGIN[0], ORIGIN[1] - pcbnew.ToMM(v.y)


def field(fp, name):
    return fp.GetFieldText(name) if fp.HasFieldByName(name) else ""


def read_csv(rep, who, data, head):
    try:
        rows = list(csv.reader(io.StringIO(data.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as e:
        rep.check(False, who, f"not a UTF-8 CSV: {e}")
        return []
    rep.check(bool(rows) and rows[0] == head, who, f"header {rows[:1]}, want {head}")
    body = rows[1:]
    rep.check(all(len(r) == len(head) for r in body), who, "a row with another number of cells")
    return [dict(zip(head, r)) for r in body if len(r) == len(head)]


# ---- 1, 2 the set and its manifest -------------------------------------------------------------
def check_set(rep, out):
    want = {f"{PREFIX}_{a}" for a in ARTIFACTS} | {"RELEASE_MANIFEST.md", "SHA256SUMS.txt"}
    have = {p.name for p in out.iterdir()} if out.exists() else set()
    rep.check(have == want, "set", f"extra {sorted(have - want)}, missing {sorted(want - have)}")
    sums = {}
    path = out / "SHA256SUMS.txt"
    if rep.check(path.exists(), "SHA256SUMS.txt", "missing"):
        for ln in path.read_text(encoding="utf-8").splitlines():
            m = re.fullmatch(r"([0-9a-f]{64})  (\S+)", ln)
            if rep.check(m is not None, "SHA256SUMS.txt", f"malformed line {ln!r}"):
                rep.check(m.group(2) not in sums, "SHA256SUMS.txt", f"{m.group(2)} listed twice")
                sums[m.group(2)] = m.group(1)
    rep.check(set(sums) == want - {"SHA256SUMS.txt"}, "SHA256SUMS.txt",
              f"lists {sorted(sums)}, want every other file")
    for name, digest in sums.items():
        p = out / name
        if p.exists():
            rep.check(sha(p.read_bytes()) == digest, name, "SHA-256 differs from SHA256SUMS.txt")
    return {n: (out / n).read_bytes() for n in have & want}


def check_manifest(rep, text, src, board, pcb_text):
    who = "RELEASE_MANIFEST.md"
    rep.check("| State | WIP |" in text and "MANUFACTURING PROHIBITED" in text, who, "not marked WIP, manufacturing prohibited")
    rep.check(f"| PCB revision | {board.GetTitleBlock().GetRevision()} |" in text, who, "revision differs from the title block")
    rep.check("JLC04161H-7628" in text, who, "no stackup ID")
    m = re.search(r'\(copper_finish "([^"]*)"\)', pcb_text)
    rep.check(m is not None and m.group(1) == "HAL SnPb" and "leaded HASL" in text and m.group(1) in text, who,
              f"finish: board {m and m.group(1)!r}, want leaded HASL (D30)")
    listed = dict(re.findall(r"^\| `(design/ecad/source/[^`]+)` \| `([0-9a-f]{64})` \|$", text, re.M))
    want = {f"design/ecad/source/{p.name}" for p in src.glob("*.kicad_sch")} | \
           {f"design/ecad/source/{NICK}.{ext}" for ext in ("kicad_pcb", "kicad_pro", "kicad_dru")}
    rep.check(set(listed) == want, who, f"sources listed {sorted(listed)}, want {sorted(want)}")
    for rel, digest in listed.items():
        p = src / pathlib.PurePosixPath(rel).name
        rep.check(p.exists() and sha(p.read_bytes()) == digest, who, f"{rel} has changed since the set was made: stale")


# ---- 3, 4 Gerber and drill ----------------------------------------------------------------------
def gerber_ops(text):
    """(dark objects, clear objects) of a Gerber: D01/D03 under %LPD% vs %LPC%."""
    dark = clear = 0
    polarity = "D"
    for ln in text.splitlines():
        if ln.startswith("%LP"):
            polarity = ln[3]
        elif re.search(r"D0?[13]\*$", ln):
            if polarity == "D":
                dark += 1
            else:
                clear += 1
    return dark, clear


def extent(text):
    xs, ys = [], []
    for m in re.finditer(r"X(-?\d+)Y(-?\d+)D0?[123]\*", text):
        xs.append(int(m.group(1)) / 1e6)
        ys.append(int(m.group(2)) / 1e6)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def board_holes(board):
    holes = {"PTH": {}, "NPTH": {}}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSizeX() > 0:
                kind = "NPTH" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "PTH"
                d = round(pcbnew.ToMM(min(p.GetDrillSizeX(), p.GetDrillSizeY())), 3)
                holes[kind][d] = holes[kind].get(d, 0) + 1
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            d = round(pcbnew.ToMM(t.GetDrillValue()), 3)
            holes["PTH"][d] = holes["PTH"].get(d, 0) + 1
    return holes


def board_slots(board):
    """{"PTH": [...], "NPTH": [...]}: (x, y, length, width, axis) of the board's oblong drills
    (the receptacles' shell slots, D37) in the board frame, sorted; axis is "x" or "y". A pad
    turned by anything but a quarter turn gets axis "?": the drill file's axes are x or y."""
    out = {"PTH": [], "NPTH": []}
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillShape() != pcbnew.PAD_DRILL_SHAPE_OBLONG:
                continue
            sx, sy = pcbnew.ToMM(p.GetDrillSizeX()), pcbnew.ToMM(p.GetDrillSizeY())
            turns = p.GetOrientationDegrees() / 90
            axis = "?" if abs(turns - round(turns)) > 1e-3 else ("x" if (sx > sy) == (round(turns) % 2 == 0) else "y")
            x, y = frame(p.GetPosition())
            kind = "NPTH" if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else "PTH"
            out[kind].append((round(x, 3), round(y, 3), round(max(sx, sy), 3), round(min(sx, sy), 3), axis))
    return {k: sorted(v) for k, v in out.items()}


def excellon(text):
    """(metric, {diameter: holes}, slots): the holes by tool diameter, slots among them; slots are
    the routed ones (G85, KiCad's alternate oval mode) as (x, y, length, width, axis) of the
    slot's centre, its overall length and the tool's diameter, sorted."""
    tools, hits, slots, tool = {}, {}, [], None
    metric = "METRIC" in text.splitlines()[:30] or any(ln.startswith("METRIC") for ln in text.splitlines()[:30])
    for ln in text.splitlines():
        m = re.fullmatch(r"T(\d+)C([\d.]+)", ln)
        if m:
            tools[m.group(1)] = round(float(m.group(2)), 3)
            continue
        m = re.fullmatch(r"T(\d+)", ln)
        if m:
            tool = m.group(1)
            continue
        if tool and re.match(r"X-?[\d.]+Y-?[\d.]+", ln):
            d = tools.get(tool)
            hits[d] = hits.get(d, 0) + 1
            s = re.fullmatch(r"X(-?[\d.]+)Y(-?[\d.]+)G85X(-?[\d.]+)Y(-?[\d.]+)", ln)
            if s:
                x1, y1, x2, y2 = map(float, s.groups())
                slots.append((round((x1 + x2) / 2, 3), round((y1 + y2) / 2, 3),
                              round(math.hypot(x2 - x1, y2 - y1) + d, 3), d, "x" if abs(x2 - x1) > abs(y2 - y1) else "y"))
    return metric, hits, sorted(slots)


def same_slots(got, want, tol=0.0015):
    """The slots of the drill file equal the board's, to the file's 1 micron rounding, axes too."""
    return len(got) == len(want) and all(g[4] == w[4] and all(abs(a - b) <= tol for a, b in zip(g[:4], w[:4]))
                                         for g, w in zip(got, want))


def check_gerber(rep, data, board):
    who = f"{PREFIX}_Gerber.zip"
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as e:
        rep.check(False, who, f"not a zip: {e}")
        return
    names = set(z.namelist())
    want = {f"{PREFIX}_{s}" for s in list(GERBERS) + list(DRILLS)}
    rep.check(names == want, who, f"extra {sorted(names - want)}, missing {sorted(want - names)}")
    W, H = BOARD
    for suffix, function in GERBERS.items():
        name = f"{PREFIX}_{suffix}"
        if name not in names:
            continue
        text = z.read(name).decode("ascii", "replace")
        rep.check("%MOMM*%" in text, name, "not in millimetres")
        rep.check(f"%TF.FileFunction,{function}*%" in text, name, f"file function is not {function}")
        dark, clear = gerber_ops(text)
        if suffix.startswith("B_Paste"):
            rep.check(dark + clear == 0, name, f"{dark + clear} objects on B.Paste (Top-only assembly)")
        elif suffix.startswith("B_Silkscreen"):
            rep.check(dark == 0, name, f"{dark} dark objects on B.SilkS")
        else:
            rep.check(dark > 0, name, "empty")
        if suffix.startswith("Edge_Cuts"):
            e = extent(text)
            want_e = (0.0, 0.0, W, H)   # the auxiliary origin is the board's lower-left corner; y points up
            rep.check(e is not None and all(abs(a - b) <= 0.001 for a, b in zip(e, want_e)), name,
                      f"outline spans {e}, want {want_e}")
    holes, slots = board_holes(board), board_slots(board)
    for kind in ("PTH", "NPTH"):
        name = f"{PREFIX}_{kind}.drl"
        if name not in names:
            continue
        metric, hits, got = excellon(z.read(name).decode("ascii", "replace"))
        rep.check(metric, name, "not METRIC")
        rep.check(hits == holes[kind], name, f"holes by diameter {sorted(hits.items())}, board {sorted(holes[kind].items())}")
        rep.check(same_slots(got, slots[kind]), name,
                  f"slots (x, y, length, width, axis) {got}, board {slots[kind]}")
    return z


# ---- 5, 6, 7 BOM, CPL, hand list ----------------------------------------------------------------
def fab_centre(fp):
    """Centre of the bounding box of the footprint's F.Fab body outline, board frame."""
    boxes = [g.GetBoundingBox() for g in fp.GraphicalItems()
             if g.GetLayer() == pcbnew.F_Fab and g.GetClass() != "PCB_TEXT"]
    if not boxes:
        return None
    x0, x1 = min(b.GetLeft() for b in boxes), max(b.GetRight() for b in boxes)
    y0, y1 = min(b.GetTop() for b in boxes), max(b.GetBottom() for b in boxes)
    return frame(pcbnew.VECTOR2I((x0 + x1) // 2, (y0 + y1) // 2))


def turned(dx, dy, degrees):
    """A vector of a footprint's own frame (x right, y down) in the board's y-down frame, for a
    footprint turned `degrees` counter-clockwise on the screen: where KiCad puts a pad."""
    a = math.radians(degrees)
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def entry_frame(entry):
    """(add, sx, sy) of a table entry. A malformed field counts as absent: check_frames reports it."""
    add, shift = entry.get("add"), entry.get("shift")
    if isinstance(shift, list) and len(shift) == 2 and all(is_number(c) for c in shift):
        sx, sy = float(shift[0]), float(shift[1])
    else:
        sx = sy = 0.0
    return (float(add) if is_number(add) else 0.0), sx, sy


def check_frames(rep, frames, lines):
    """design/ecad/jlcpcb_model_frame.json against the BOM's LCSC numbers: each entry is used, and
    changes the CPL by a quarter-turn rotation, a shift of at most SHIFT_MAX, or both."""
    dead = sorted(set(frames) - set(lines))
    rep.check(not dead, "model frame table", f"entries no BOM line uses: {dead}")
    for lcsc, v in sorted(frames.items()):
        if not rep.check(isinstance(v, dict), "model frame table", f"{lcsc}: an entry that is not an object"):
            continue
        add, shift = v.get("add"), v.get("shift")
        rep.check(add is not None or shift is not None, "model frame table",
                  f"{lcsc}: an entry with neither add nor shift (a part with none is left out)")
        rep.check(add is None or add in (90, 180, 270), "model frame table",
                  f"{lcsc}: add {add!r} is not 90, 180 or 270")
        if shift is not None:
            ok = isinstance(shift, list) and len(shift) == 2 and all(is_number(c) for c in shift)
            rep.check(ok, "model frame table", f"{lcsc}: shift {shift!r} is not [dx, dy] in mm")
            if ok:
                rep.check(0 < math.hypot(*shift) <= SHIFT_MAX, "model frame table",
                          f"{lcsc}: shift {shift} is not between 0 and {SHIFT_MAX:g} mm long")


def check_lists(rep, files, fps, frames):
    bom = read_csv(rep, "BOM", files.get(f"{PREFIX}_BOM_JLCPCB.csv", b""), BOM_HEAD)
    cpl = read_csv(rep, "CPL", files.get(f"{PREFIX}_CPL_JLCPCB.csv", b""), CPL_HEAD)
    hand = read_csv(rep, "hand list", files.get(f"{PREFIX}_HandSolder.csv", b""), HAND_HEAD)
    machine = {r for r, fp in fps.items() if field(fp, "LCSC") and not fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM}
    handset = {r for r, fp in fps.items() if field(fp, "Akizuki") and not fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM}
    seen, lines = [], []
    for row in bom:
        refs = row["Designator"].split(",")
        seen += refs
        lines.append(row["JLCPCB Part #"])
        for n, ref in enumerate(refs):
            fp = fps.get(ref)
            if not rep.check(fp is not None, "BOM", f"{ref} is not on the board"):
                continue
            rep.check(field(fp, "LCSC") == row["JLCPCB Part #"], f"BOM {ref}",
                      f"JLCPCB Part # {row['JLCPCB Part #']}, footprint LCSC {field(fp, 'LCSC')}")
            if n == 0:                       # Comment and Footprint describe the row's first designator
                rep.check(fp.GetValue() == row["Comment"], f"BOM {ref}", f"Comment {row['Comment']!r}, Value {fp.GetValue()!r}")
                name = fp.GetFPID().GetLibItemName().wx_str()
                rep.check(name == row["Footprint"], f"BOM {ref}", f"Footprint {row['Footprint']}, board {name}")
            cls = field(fp, "Class")
            lcsc = field(fp, "LCSC")
            ok = cls == "Basic" or (lcsc in EXTENDED and cls == f"Extended ({EXTENDED[lcsc]})")
            rep.check(ok, f"BOM {ref}", f"class {cls!r} for {lcsc}: Basic only, except C2040 (D29), C5137013 (D31) and C2765186 (D37)")
    rep.check(len(seen) == len(set(seen)), "BOM", "a designator in two rows")
    rep.check(len(lines) == len(set(lines)), "BOM",
              "an LCSC part in two rows: JLCPCB's part mapping selects neither (quote of 2026-11-11)")
    check_frames(rep, frames, lines)
    rep.check(set(seen) == machine, "BOM", f"designators: extra {sorted(set(seen) - machine)}, "
              f"missing {sorted(machine - set(seen))}")
    cpl_refs = [r["Designator"] for r in cpl]
    rep.check(len(cpl_refs) == len(set(cpl_refs)) and set(cpl_refs) == set(seen), "CPL",
              f"designators differ from the BOM's: extra {sorted(set(cpl_refs) - set(seen))}, "
              f"missing {sorted(set(seen) - set(cpl_refs))}")
    W, H = BOARD
    for row in cpl:
        ref, fp = row["Designator"], fps.get(row["Designator"])
        if not rep.check(fp is not None, "CPL", f"{ref} is not on the board"):
            continue
        try:
            x, y, rot = float(row["Mid X"]), float(row["Mid Y"]), float(row["Rotation"])
        except ValueError:
            rep.check(False, f"CPL {ref}", f"not numbers: {row}")
            continue
        fx, fy = frame(fp.GetPosition())
        orient = fp.GetOrientationDegrees() % 360
        add, sx, sy = entry_frame(frames.get(field(fp, "LCSC"), {}))
        kx, ky = turned(sx, sy, orient)
        ex, ey = fx + kx, fy - ky                # the CPL's y points up, the board's down
        what = f"Mid ({x}, {y}), footprint origin ({fx:.4f}, {fy:.4f})"
        if sx or sy:
            what += f" + JLCPCB model shift ({sx:g}, {sy:g}) turned by {orient:g} = ({ex:.4f}, {ey:.4f})"
        rep.check(abs(x - ex) <= POS_TOL and abs(y - ey) <= POS_TOL, f"CPL {ref}", what)
        rep.check(0 < x < W and 0 < y < H, f"CPL {ref}", f"Mid ({x}, {y}) is off the board")
        body = fab_centre(fp)
        if rep.check(body is not None, f"CPL {ref}", "no F.Fab body outline to find its centre"):
            rep.check(abs(body[0] - fx) <= MID_TOL and abs(body[1] - fy) <= MID_TOL, f"CPL {ref}",
                      f"origin ({fx:.3f}, {fy:.3f}) is not its body's centre ({body[0]:.3f}, {body[1]:.3f})")
        rep.check(row["Layer"] == "Top", f"CPL {ref}", f"layer {row['Layer']}")
        want = (orient + add) % 360
        rep.check(abs(rot - want) < 1e-6, f"CPL {ref}",
                  f"rotation {rot}, expected {want:g} (footprint {orient:g} + JLCPCB model {add:g})")
    hrefs = [r["Designator"] for r in hand]
    rep.check(len(hrefs) == len(set(hrefs)) and set(hrefs) == handset, "hand list",
              f"extra {sorted(set(hrefs) - handset)}, missing {sorted(handset - set(hrefs))}")
    rep.check(not set(hrefs) & (set(seen) | set(cpl_refs)), "hand list", "a hand-soldered part in the BOM or CPL")
    for row in hand:
        fp = fps.get(row["Designator"])
        if fp is not None:
            rep.check(row["Akizuki"] == field(fp, "Akizuki") and row["MPN"] == field(fp, "MPN"), f"hand {row['Designator']}",
                      f"Akizuki {row['Akizuki']} / MPN {row['MPN']}, footprint {field(fp, 'Akizuki')} / {field(fp, 'MPN')}")


# ---- 8 documents --------------------------------------------------------------------------------
def sheet_instances(src):
    """Pages kicad-cli prints: the root sheet and every sheet instance below it."""
    def count(path, seen):
        text = path.read_text(encoding="utf-8")
        n = 1
        for m in re.finditer(r'\(property "Sheetfile" "([^"]+)"', text):
            child = path.parent / m.group(1)
            if child not in seen:
                n += count(child, seen | {child})
        return n
    return count(src / f"{NICK}.kicad_sch", set())


def pdf_pages(data):
    return len(re.findall(rb"/Type\s*/Page(?![s\w])", data))


def check_documents(rep, files, src):
    sch = files.get(f"{PREFIX}_Schematic.pdf", b"")
    want = sheet_instances(src)
    rep.check(sch.startswith(b"%PDF-") and pdf_pages(sch) == want, f"{PREFIX}_Schematic.pdf",
              f"{pdf_pages(sch)} pages, want {want} (one per sheet)")
    asm = files.get(f"{PREFIX}_Assembly_Top.pdf", b"")
    rep.check(asm.startswith(b"%PDF-") and pdf_pages(asm) == 1, f"{PREFIX}_Assembly_Top.pdf", f"{pdf_pages(asm)} pages, want 1")
    for side in ("Top", "Bottom"):
        name = f"{PREFIX}_Preview_{side}.png"
        b = files.get(name, b"")
        ok = b[:8] == b"\x89PNG\r\n\x1a\n" and b[12:16] == b"IHDR"
        size = struct.unpack(">II", b[16:24]) if ok else None
        rep.check(ok and size[0] >= PREVIEW_MIN_W and abs(size[0] / size[1] / ASPECT - 1) <= 0.03, name,
                  f"PNG of size {size}, want >= {PREVIEW_MIN_W} px wide at the board's {ASPECT:.3f} aspect")
    for kind in ("ERC", "DRC"):
        name = f"{PREFIX}_{kind}.json"
        try:
            data = json.loads(files.get(name, b"").decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            rep.check(False, name, f"not JSON: {e}")
            continue
        v = sum(len(s.get("violations", [])) for s in data.get("sheets", [])) + len(data.get("violations", []))
        rep.check(v == 0, name, f"{v} violations")
        rep.check(not data.get("unconnected_items") and not data.get("schematic_parity"), name,
                  f"{len(data.get('unconnected_items', []))} unconnected, {len(data.get('schematic_parity', []))} parity items")
        rep.check(kind != "DRC" or "schematic_parity" in data, name, "made without --schematic-parity")


# ---- 9 privacy and determinism ------------------------------------------------------------------
def check_private(rep, files, z):
    blobs = dict(files)
    if z is not None:
        blobs.update({f"zip:{n}": z.read(n) for n in z.namelist()})
    for name, b in blobs.items():
        if name.endswith(".png") or name.endswith(".zip"):
            continue
        for pat in PRIVATE:
            m = pat.search(b)
            rep.check(m is None, name, f"holds {m.group(0)[:40].decode('ascii', 'replace')!r} (a local path or an e-mail address)" if m else "")
        for m in DATE.finditer(b):
            stamp = m.group(0)
            rep.check(stamp.startswith(b"1980-01-01") or stamp == b"(D:19800101", name,
                      f"creation date {stamp.decode()!r}: the set is not deterministic")
    if z is not None:
        rep.check(all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in z.infolist()), "Gerber.zip", "member times are not fixed")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "manufacturing" / "working" / "rev0.6")
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "design" / "ecad" / "source")
    ap.add_argument("--frames", type=pathlib.Path, default=ROOT / "design" / "ecad" / "jlcpcb_model_frame.json")
    a = ap.parse_args(argv[1:])
    rep = Report()
    pcb = a.src / f"{NICK}.kicad_pcb"
    prl = a.src / f"{NICK}.kicad_prl"
    prl_before = prl.exists()
    board = pcbnew.LoadBoard(str(pcb))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    files = check_set(rep, a.out)
    check_manifest(rep, files.get("RELEASE_MANIFEST.md", b"").decode("utf-8", "replace"), a.src, board,
                   pcb.read_text(encoding="utf-8"))
    z = check_gerber(rep, files.get(f"{PREFIX}_Gerber.zip", b""), board)
    check_lists(rep, files, fps, json.loads(a.frames.read_text(encoding="utf-8"))["parts"])
    check_documents(rep, files, a.src)
    check_private(rep, files, z)
    if prl.exists() and not prl_before:
        prl.unlink()
    for line in rep.fails:
        print(line)
    print(f"{len(files)} files in {a.out.name}")
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
