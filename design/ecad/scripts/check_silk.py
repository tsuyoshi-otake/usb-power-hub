"""Check the board's silkscreen against the placement document's silk table (issue #6 P5;
CLAUDE.md 6).

Run with KiCad's own Python from the repository root (make_pcb.py runs it after it writes
the board):

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_silk.py
        [--src DIR] [--doc FILE]

--src holds the KiCad project (default design/ecad/source) and --doc the placement document
(default design/ecad/PLACEMENT_Rev0.6.md); the tests pass corrupted copies. The document is read with
check_pcb.py's parser, not make_pcb.py's, and the board with pcbnew. Distances are pcbnew's
own shape collisions: a text is its stroked glyphs, a pad its F.Mask opening.

JLCPCB's legend limits (pcb-capabilities, Legend, read 2026-11-06): a 1.0 mm text height, a
0.15 mm line, a 1:6 line-to-height ratio and 0.15 mm from pad to silkscreen.

 1. Table: each label once; Rot 0 or 90; height >= MIN_H (1.0 mm), width >= MIN_W (0.8 mm),
    stroke >= max(MIN_STROKE (0.15 mm), height / 6).
 2. Board = table: the board's own F.SilkS texts are exactly the table's labels (text,
    centre, rotation, glyph size, stroke) and its own F.SilkS shapes exactly their leader
    segments; nothing of the board's own is on B.SilkS; no footprint text is visible on a
    silkscreen layer (the reference designators stay hidden).
 3. Content (CLAUDE.md 6): the title block's title and revision; a port label beside each
    USB-C receptacle (HOST, OUT A, OUT B, 5V IN); at every test pad exactly one label, its
    pad's net name; a label with its reference at every hand-soldered part (a footprint whose
    Class field starts with "Hand"), since the user finds its place by it; the function labels
    of PART_LABELS (BOOT at SW3, SWD at J5); and the legend of J5's programming pads, one row
    for the even pads and one for the odd ones, each "<pad> <net>" in pad order, NC for a pad
    without a net.
 4. Association: a test-pad label without a leader is within BESIDE_MM (1.5 mm) of its pad,
    and its centre is nearer that pad's centre than any other test pad's. A leader starts
    within LEAD_START_MM (0.3 mm) of its label without touching its glyphs (KiCad's DRC
    flags that as silk overlap) and ends within LEAD_END_MM (0.6 mm) of its pad's edge,
    nearer that pad than any other pad on the board. A port label lies outside
    its receptacle's courtyard and within BESIDE_MM of it. A part label (a hand-soldered part's
    reference, a function label) is within BESIDE_MM of its part's courtyard and nearer it than
    any other labelled part's. A legend row is within LEGEND_MM (6.0 mm) of J5's courtyard, the
    even row on the side of J5 where its even pads are, and the pads of a row run left to right
    in pad order, as its text does.
 5. Clearance of every label and leader: on the board, >= EDGE_MM (0.5 mm) from its edge;
    >= PAD_MM (0.15 mm) from every F.Mask opening; >= SILK_MM (0.1 mm) from every footprint's
    silkscreen and from every other label (a label's own leader excepted); a label enters no
    courtyard; a leader enters no courtyard but a test pad's, which carries no body.
    Two labels with the same rotation that share a line (their inks overlap across the reading
    direction) are >= WORD_MM (1.0 mm, one glyph) apart along it: closer, they read as one
    word (DVDD and CLKOUT did, 0.30 mm apart, until Rev0.6 r02).
 6. Footprint silkscreen on the board: every stroke >= MIN_STROKE, inside the board outline,
    >= PAD_MM from every other footprint's F.Mask opening (check_libraries.py measures it
    against the footprint's own), and every polar part (U, D, Q, Y and the SWD connector J5)
    keeps some.
Exit status: 0 = every check passed; 1 = at least one failed. Each failure prints as
`FAIL <who>: <what>`.

What it CANNOT see:
- whether a footprint's silkscreen marks pin 1 or the cathode: check 6 only finds that a
  polar part has silkscreen; check_libraries.py keeps a stock footprint's marks as KiCad drew
  them and the generated ones as make_libraries.py draws them. The JLCPCB placement preview
  is the evidence for orientation (CLAUDE.md 4.2).
- legibility after printing, and whether a label is under a case opening (V-MECH-01). A
  part's body above the board is its courtyard.
- whether a reader takes the legend's rows for J5's pad rows: rule 4 checks their order, not
  that anyone reads them so. The pads themselves carry no name: 1.0 mm text does not fit their
  1.27 mm pitch.
- KiCad's DRC checks silk-to-silk and silk-to-copper overlap too; check_pcb.py runs it.
"""
import argparse
import importlib.util
import math
import pathlib
import sys

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
MIN_H = 1.0
MIN_W = 0.8
MIN_STROKE = 0.15
RATIO = 6.0
PAD_MM = 0.15
SILK_MM = 0.1
EDGE_MM = 0.5
BESIDE_MM = 1.5
LEAD_START_MM = 0.3
LEAD_END_MM = 0.6
WORD_MM = 1.0
LEGEND_MM = 6.0
PART_LABELS = {"SW3": "BOOT", "J5": "SWD"}
LEGEND_REF = "J5"
LEGEND_ROWS = {"J5.even": 0, "J5.odd": 1}       # label: pad number modulo 2
HAND = "Hand"
TOL = 0.0005
PORTS = {"J1": "HOST", "J2": "OUT A", "J3": "OUT B", "J4": "5V IN"}
POLAR = ("U", "D", "Q", "Y")
POLAR_REFS = ("J5",)
SILK = (pcbnew.F_SilkS, pcbnew.B_SilkS)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cp = _load("check_pcb")
frame, box, Report = cp.frame, cp.box, cp.Report
mm = pcbnew.FromMM


def sheet(x, y):
    return pcbnew.VECTOR2I(mm(cp.ORIGIN[0] + x), mm(cp.ORIGIN[1] - y))


def read_silk(path):
    for kind, _, rows in cp.marked_blocks(path.read_text(encoding="utf-8")):
        if kind == "silk":
            return rows
    raise SystemExit(f"{path.name}: no silk table")


def rect_gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return math.hypot(dx, dy)


def centre(r):
    return ((r[0] + r[2]) / 2, (r[1] + r[3]) / 2)


# ---- 1 the table -------------------------------------------------------------------------------
def check_table(rep, rows):
    labels = {}
    for r in rows:
        who = f"silk {r['Label']}"
        rep.check(r["Label"] not in labels, who, "labelled twice in the table")
        try:
            lab = dict(text=r["Text"], x=float(r["x"]), y=float(r["y"]), rot=int(r["Rot"]),
                       w=float(r["Width"]), h=float(r["Height"]), stroke=float(r["Stroke"]),
                       leader=[] if r["Leader"] == "-" else
                       [tuple(float(v) for v in pt.split(",")) for pt in r["Leader"].split()])
        except ValueError as e:
            rep.check(False, who, f"malformed row: {e}")
            continue
        rep.check(lab["rot"] in (0, 90), who, f"rotation {lab['rot']}, want 0 or 90")
        rep.check(lab["h"] >= MIN_H - 1e-9, who, f"height {lab['h']} mm < {MIN_H} mm")
        rep.check(lab["w"] >= MIN_W - 1e-9, who, f"width {lab['w']} mm < {MIN_W} mm")
        want = max(MIN_STROKE, lab["h"] / RATIO)
        rep.check(lab["stroke"] >= want - 1e-9, who,
                  f"stroke {lab['stroke']} mm < {want:.3f} mm (0.15 mm, 1:6 of the height)")
        rep.check(len(lab["leader"]) != 1 and all(len(p) == 2 for p in lab["leader"]), who,
                  f"leader needs two or more x,y points: {r['Leader']}")
        labels[r["Label"]] = lab
    return labels


# ---- 2 board = table ---------------------------------------------------------------------------
def board_silk(board):
    texts, shapes, back = [], [], []
    for d in board.GetDrawings():
        if d.GetLayer() == pcbnew.B_SilkS:
            back.append(d)
        elif d.GetLayer() == pcbnew.F_SilkS:
            (texts if d.GetClass() == "PCB_TEXT" else shapes).append(d)
    return texts, shapes, back


def text_matches(t, lab):
    x, y = frame(t.GetPosition())
    size = t.GetTextSize()
    return (t.GetText() == lab["text"] and abs(x - lab["x"]) <= TOL and abs(y - lab["y"]) <= TOL and
            abs(t.GetTextAngleDegrees() - lab["rot"]) < 1e-6 and
            abs(pcbnew.ToMM(size.x) - lab["w"]) <= TOL and abs(pcbnew.ToMM(size.y) - lab["h"]) <= TOL and
            abs(pcbnew.ToMM(t.GetTextThickness()) - lab["stroke"]) <= TOL)


def seg_matches(s, a, b, stroke):
    if s.GetShape() != pcbnew.SHAPE_T_SEGMENT or abs(pcbnew.ToMM(s.GetWidth()) - stroke) > TOL:
        return False
    p, q = frame(s.GetStart()), frame(s.GetEnd())
    return all(abs(u - v) <= TOL for u, v in zip(p + q, a + b))


def check_board_table(rep, board, labels):
    texts, shapes, back = board_silk(board)
    found = {}
    for name, lab in labels.items():
        hits = [t for t in texts if text_matches(t, lab)]
        if rep.check(len(hits) == 1, f"silk {name}",
                     f"{len(hits)} board texts match the table row {lab['text']!r} at ({lab['x']}, {lab['y']})"):
            found[name] = hits[0]
        segs = []
        for a, b in zip(lab["leader"], lab["leader"][1:]):
            m = [s for s in shapes if seg_matches(s, a, b, lab["stroke"])]
            if rep.check(len(m) == 1, f"silk {name}", f"leader segment {a}-{b}: {len(m)} board segments match"):
                segs.append(m[0])
        lab["segs"] = segs
    used = {id(t) for t in found.values()} | {id(s) for lab in labels.values() for s in lab["segs"]}
    for t in texts:
        rep.check(id(t) in used, "board silk", f"text {t.GetText()!r} at {frame(t.GetPosition())} is not in the table")
    for s in shapes:
        rep.check(id(s) in used, "board silk", f"shape at {frame(s.GetStart())} is not a table leader")
    rep.check(not back, "board silk", f"{len(back)} item(s) on B.SilkS")
    for fp in board.GetFootprints():
        for t in list(fp.GetFields()) + [g for g in fp.GraphicalItems() if g.GetClass() == "PCB_TEXT"]:
            if t.GetLayer() in SILK:
                rep.check(not t.IsVisible(), fp.GetReference(), f"text {t.GetText()!r} is visible on the silkscreen")
    return found


# ---- 3 content, 4 association ------------------------------------------------------------------
def tp_pads(fps):
    out = {}
    for ref, fp in fps.items():
        if ref.startswith("TP"):
            pads = list(fp.Pads())
            out[ref] = pads[0] if len(pads) == 1 else None
    return out


def ink(t):
    return box(t.GetEffectiveShape().BBox())


def check_content(rep, board, labels, found, fps, receptacles):
    tb = board.GetTitleBlock()
    for name, want in (("title", tb.GetTitle()), ("revision", tb.GetRevision())):
        rep.check(name in labels and labels[name]["text"] == want, f"silk {name}",
                  f"want the title block's {want!r}, table {labels.get(name, {}).get('text')!r}")
    for ref, want in PORTS.items():
        lab = labels.get(ref)
        if not rep.check(lab is not None and lab["text"] == want, f"silk {ref}",
                         f"port label {want!r} missing (table: {lab and lab['text']!r})"):
            continue
        if ref in found and ref in receptacles:
            r, crt = ink(found[ref]), receptacles[ref]
            g = rect_gap(r, crt)
            rep.check(not cp.overlap(r, crt) and g <= BESIDE_MM, f"silk {ref}",
                      f"port label {g:.2f} mm from {ref}'s courtyard, want outside and <= {BESIDE_MM} mm")
    pads = tp_pads(fps)
    for ref, pad in sorted(pads.items()):
        if not rep.check(pad is not None, ref, "a test pad with other than one pad"):
            continue
        lab = labels.get(ref)
        if not rep.check(lab is not None, ref, "no silk label"):
            continue
        rep.check(lab["text"] == pad.GetNetname(), f"silk {ref}",
                  f"text {lab['text']!r}, its pad's net {pad.GetNetname()!r}")
    parts = dict(PART_LABELS)
    parts.update({ref: ref for ref, fp in fps.items() if fp_class(fp).startswith(HAND)})
    for ref, want in sorted(parts.items()):
        lab = labels.get(ref)
        if not rep.check(lab is not None, ref, "no silk label"):
            continue
        rep.check(lab["text"] == want, f"silk {ref}", f"text {lab['text']!r}, want {want!r}")
    legend = legend_texts(fps.get(LEGEND_REF))
    for name, want in sorted(legend.items()):
        lab = labels.get(name)
        if rep.check(lab is not None, name, "no silk legend row"):
            rep.check(lab["text"] == want, f"silk {name}", f"text {lab['text']!r}, its pads' nets give {want!r}")
    for name in labels:
        rep.check(name in pads or name in PORTS or name in ("title", "revision") or name in parts
                  or name in LEGEND_ROWS, f"silk {name}",
                  "labels no test pad, port, title-block field, labelled part or legend row")
    check_part_labels(rep, parts, found, fps)
    check_legend(rep, labels, found, fps.get(LEGEND_REF))
    for ref, pad in pads.items():
        if pad is None or ref not in found:
            continue
        check_association(rep, ref, labels[ref], found[ref], pad, pads, fps)


def fp_class(fp):
    f = fp.GetFieldByName("Class")
    return f.GetText() if f else ""


def crt_box(fp):
    rects = cp.courtyard(fp)
    return (min(r[0] for r in rects), min(r[1] for r in rects),
            max(r[2] for r in rects), max(r[3] for r in rects)) if rects else None


def numbered(fp):
    return sorted((int(p.GetNumber()), p) for p in fp.Pads() if p.GetNumber().isdigit())


def legend_texts(fp):
    """{row label: text} of the programming connector's pads: "<pad> <net>" in pad order."""
    if fp is None:
        return {}
    out = {}
    for name, parity in LEGEND_ROWS.items():
        cells = []
        for n, p in numbered(fp):
            if n % 2 == parity:
                net = p.GetNetname()
                cells.append(f"{n} {'NC' if not net or net.startswith('unconnected-') else net}")
        out[name] = " ".join(cells)
    return out


def check_part_labels(rep, parts, found, fps):
    boxes = {ref: crt_box(fps[ref]) for ref in parts if ref in fps}
    for ref in sorted(parts):
        if ref not in found:
            continue
        if not rep.check(boxes.get(ref) is not None, f"silk {ref}", f"{ref} is not on the board or has no courtyard"):
            continue
        r = ink(found[ref])
        own = rect_gap(r, boxes[ref])
        rep.check(own <= BESIDE_MM, f"silk {ref}",
                  f"{own:.2f} mm from {ref}'s courtyard, want <= {BESIDE_MM} mm")
        for other, b in boxes.items():
            if other != ref and b is not None:
                d = rect_gap(r, b)
                rep.check(d > own, f"silk {ref}",
                          f"{d:.2f} mm from {other}'s courtyard, {own:.2f} mm from {ref}'s: reads as {other}'s")


def check_legend(rep, labels, found, fp):
    if fp is None or crt_box(fp) is None or any(n not in found for n in LEGEND_ROWS):
        return
    crt = crt_box(fp)
    ys = {}
    for name, parity in LEGEND_ROWS.items():
        r = ink(found[name])
        g = rect_gap(r, crt)
        rep.check(g <= LEGEND_MM, f"silk {name}", f"{g:.2f} mm from {LEGEND_REF}'s courtyard, want <= {LEGEND_MM} mm")
        rep.check(labels[name]["rot"] == 0, f"silk {name}", "a legend row reads left to right")
        pads = [frame(p.GetPosition()) for n, p in numbered(fp) if n % 2 == parity]
        rep.check(all(a[0] < b[0] - 1e-6 and abs(a[1] - b[1]) < 1e-6 for a, b in zip(pads, pads[1:])),
                  f"silk {name}", f"{LEGEND_REF}'s pads of this row do not run left to right in pad order")
        ys[name] = (centre(r)[1], pads[0][1] if pads else 0.0)
    (ye, pe), (yo, po) = ys["J5.even"], ys["J5.odd"]
    rep.check((ye - yo) * (pe - po) > 0, "silk J5.even",
              f"row at y {ye:.2f}, the odd row at {yo:.2f}: not on the side of {LEGEND_REF}'s even pads "
              f"(y {pe:.2f}, odd pads {po:.2f})")


def pad_dist(pad, pt):
    """Distance from a board point to a pad's copper, by pcbnew's collision, 0.005 mm steps."""
    shape = pad.GetEffectiveShape(pcbnew.F_Cu)
    v = sheet(*pt)
    lo, hi = 0.0, 20.0
    if shape.Collide(v, 0):
        return 0.0
    if not shape.Collide(v, mm(hi)):
        return hi
    while hi - lo > 0.005:
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if shape.Collide(v, mm(mid)) else (mid, hi)
    return hi


def check_association(rep, ref, lab, text, pad, pads, fps):
    who = f"silk {ref}"
    if not lab["leader"]:
        near = text.GetEffectiveShape().Collide(pad.GetEffectiveShape(pcbnew.F_Cu), mm(BESIDE_MM))
        rep.check(near, who, f"not within {BESIDE_MM} mm of {ref}'s pad and has no leader")
        c = centre(ink(text))
        own = math.dist(c, frame(pad.GetPosition()))
        for other, p in pads.items():
            if other != ref and p is not None:
                d = math.dist(c, frame(p.GetPosition()))
                rep.check(d > own, who, f"centre {d:.2f} mm from {other}, {own:.2f} mm from {ref}: reads as {other}'s")
        return
    start, end = lab["leader"][0], lab["leader"][-1]
    rep.check(text.GetEffectiveShape().Collide(sheet(*start), mm(LEAD_START_MM)), who,
              f"leader starts at {start}, more than {LEAD_START_MM} mm from its label")
    for seg in lab["segs"]:                  # KiCad's DRC flags a leader touching its text
        rep.check(not text.GetEffectiveShape().Collide(seg.GetEffectiveShape(pcbnew.F_SilkS), 0), who,
                  f"leader segment from {frame(seg.GetStart())} touches its label's glyphs")
    own = pad_dist(pad, end)
    rep.check(own <= LEAD_END_MM, who, f"leader ends {own:.3f} mm from {ref}'s pad (want <= {LEAD_END_MM} mm)")
    for fref, fp in fps.items():
        for p in fp.Pads():
            if (fref == ref) or rect_gap(box(p.GetBoundingBox()), (end[0], end[1], end[0], end[1])) > own + 0.01:
                continue
            d = pad_dist(p, end)
            rep.check(d > own, who, f"leader ends {d:.3f} mm from {fref}.{p.GetNumber()}, nearer than {ref} ({own:.3f} mm)")


# ---- 5 clearance of the labels -------------------------------------------------------------------
def mask_openings(fps):
    out = []
    for ref, fp in fps.items():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Mask):
                s = p.GetEffectiveShape(pcbnew.F_Mask)
                out.append((ref, p, s, box(s.BBox())))
    return out


def fp_silk(fps):
    out = []
    for ref, fp in fps.items():
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_SilkS and g.GetClass() != "PCB_TEXT":
                s = g.GetEffectiveShape(pcbnew.F_SilkS)
                out.append((ref, g, s, box(s.BBox())))
    return out


def courtyards(fps):
    out = []
    for ref, fp in fps.items():
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount():
            out.append((ref, cy, box(cy.BBox())))
    return out


def near(items, r, reach):
    return [it for it in items if rect_gap(it[-1], r) <= reach]


def check_clearance(rep, labels, found, fps, openings, fsilk, crts):
    W, H = cp.BOARD
    items = []                               # (label, kind, shape, rect)
    for name, t in found.items():
        s = t.GetEffectiveShape()
        items.append((name, "label", s, box(s.BBox())))
        for seg in labels[name]["segs"]:
            s = seg.GetEffectiveShape(pcbnew.F_SilkS)
            items.append((name, "leader", s, box(s.BBox())))
    for name, kind, s, r in items:
        who = f"silk {name} {kind}"
        rep.check(r[0] >= EDGE_MM - 1e-6 and r[1] >= EDGE_MM - 1e-6 and r[2] <= W - EDGE_MM + 1e-6 and
                  r[3] <= H - EDGE_MM + 1e-6, who,
                  f"ink {tuple(round(v, 3) for v in r)} is not {EDGE_MM} mm inside the board")
        for ref, p, ms, _ in near(openings, r, PAD_MM + 0.01):
            rep.check(not s.Collide(ms, mm(PAD_MM) - 1), who, f"< {PAD_MM} mm from {ref}.{p.GetNumber()}'s mask opening")
        for ref, g, gs, _ in near(fsilk, r, SILK_MM + 0.01):
            rep.check(not s.Collide(gs, mm(SILK_MM) - 1), who, f"< {SILK_MM} mm from {ref}'s silkscreen")
        for ref, cy, _ in near(crts, r, 0.0):
            if kind == "leader" and ref.startswith("TP"):
                continue
            rep.check(not cy.Collide(s, 0), who, f"enters {ref}'s courtyard")
    for i, (a, ka, sa, ra) in enumerate(items):
        for b, kb, sb, rb in items[i + 1:]:
            if a == b or rect_gap(ra, rb) > SILK_MM + 0.01:
                continue
            rep.check(not sa.Collide(sb, mm(SILK_MM) - 1), f"silk {a} {ka}", f"< {SILK_MM} mm from silk {b} {kb}")
    words = [(n, labels[n]["rot"], r) for n, k, _, r in items if k == "label"]
    for i, (a, rota, ra) in enumerate(words):
        for b, rotb, rb in words[i + 1:]:
            if rota != rotb:
                continue
            ax = 0 if rota == 0 else 1       # the reading axis; 1 - ax is across it
            across = min(ra[3 - ax], rb[3 - ax]) - max(ra[1 - ax], rb[1 - ax])
            along = max(rb[ax] - ra[ax + 2], ra[ax] - rb[ax + 2])
            rep.check(across <= 1e-6 or along >= WORD_MM - 1e-6, f"silk {a} label",
                      f"{along:.2f} mm from silk {b} on one line: reads as one word (want >= {WORD_MM} mm)")


# ---- 6 footprint silkscreen ----------------------------------------------------------------------
def check_footprint_silk(rep, fps, openings, fsilk):
    W, H = cp.BOARD
    have = {}
    for ref, g, s, r in fsilk:
        have[ref] = have.get(ref, 0) + 1
        w = pcbnew.ToMM(g.GetWidth())
        rep.check(w >= MIN_STROKE - 1e-6, ref, f"silkscreen stroke {w} mm < {MIN_STROKE} mm")
        rep.check(r[0] >= -1e-6 and r[1] >= -1e-6 and r[2] <= W + 1e-6 and r[3] <= H + 1e-6, ref,
                  f"silkscreen {tuple(round(v, 3) for v in r)} leaves the board")
        for oref, p, ms, _ in near(openings, r, PAD_MM + 0.01):
            if oref != ref:
                rep.check(not s.Collide(ms, mm(PAD_MM) - 1), ref,
                          f"silkscreen < {PAD_MM} mm from {oref}.{p.GetNumber()}'s mask opening")
    for ref in fps:
        if ref.startswith(POLAR) or ref in POLAR_REFS:
            rep.check(have.get(ref, 0) > 0, ref, "a polar part with no silkscreen")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "design" / "ecad" / "source")
    ap.add_argument("--doc", type=pathlib.Path, default=ROOT / "design" / "ecad" / "PLACEMENT_Rev0.6.md")
    a = ap.parse_args(argv[1:])
    rep = Report()
    pcb, prl = a.src / f"{NICK}.kicad_pcb", a.src / f"{NICK}.kicad_prl"
    prl_before = prl.exists()
    labels = check_table(rep, read_silk(a.doc))
    board = pcbnew.LoadBoard(str(pcb)) if pcb.exists() else None
    if board is None:
        print(f"FAIL board: pcbnew could not load {pcb}")
        print(f"{rep.count + 1} checks, {len(rep.fails) + 1} failed: FAIL")
        return 1
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    receptacles = {}
    for ref in PORTS:
        rects = cp.courtyard(fps[ref]) if ref in fps else []
        if rects:
            receptacles[ref] = (min(r[0] for r in rects), min(r[1] for r in rects),
                                max(r[2] for r in rects), max(r[3] for r in rects))
    found = check_board_table(rep, board, labels)
    check_content(rep, board, labels, found, fps, receptacles)
    openings, fsilk, crts = mask_openings(fps), fp_silk(fps), courtyards(fps)
    check_clearance(rep, labels, found, fps, openings, fsilk, crts)
    check_footprint_silk(rep, fps, openings, fsilk)
    if prl.exists() and not prl_before:
        prl.unlink()
    for line in rep.fails:
        print(line)
    n_lead = sum(len(lab.get("segs", [])) for lab in labels.values())
    print(f"{len(labels)} labels, {n_lead} leader segments, {len(fsilk)} footprint silkscreen items")
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
