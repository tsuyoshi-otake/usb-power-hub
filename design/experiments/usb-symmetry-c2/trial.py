"""Trial C2 (issue #12): does a mirror-symmetric USB connector placement pass check_pcb.py?

A non-authoritative experiment. It never writes to the tracked board: it copies design/ecad and the
two files its scripts read into a NEW scratch directory, applies c2_change.py to the copy of
PLACEMENT_Rev0.5.md, builds a board with footprints only (make_pcb.py's own functions, stopped
before routing), and runs the copy's check_pcb.py on it.

    "<KiCad 9.0>/bin/python.exe" -I -B design/experiments/usb-symmetry-c2/trial.py <new scratch directory> [--negative]

It prints check_pcb.py's verdict, the mirror table, the parts that moved, the MAU104's distance to
the analog parts and a few pad-to-pad distances before and after, writes <scratch>/layout_c2.svg,
and exits 0 only if check_pcb.py passes, every pair mirrors about x = 50 and no part outside the
regions c2_change.py names has moved. --negative then breaks the placement three ways and expects
check_pcb.py to fail each time (about three more minutes).

What it CANNOT show:
- anything about routing. The board it builds has no copper but the pads: no track, no zone, no
  router session, so nothing about the USB pairs' geometry, VBUS_B's drop, the L2 plane or DRC
  between copper. The pad-to-pad figures are straight lines, not track lengths.
- noise from the MAU104 into the front ends, the reference or VBUS_B. check_pcb.py's 6.0 mm rule
  is a distance between courtyards, nothing more.
- the silkscreen labels (the board has none; the document's silkscreen table is not updated), the
  enclosure and the lid PCB, which follow the board's interface and would have to be redrawn.
- that JLCPCB accepts anything: a changed placement is a new PCB revision (CLAUDE.md, section 2).
"""
import importlib.util
import math
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COPIES = ("design/ecad", "design/circuit/CIRCUIT_DESIGN_Rev0.5_netlist.md",
          "design/experiments/stackup-impedance/stackups.json")
DOC = "design/ecad/PLACEMENT_Rev0.5.md"
PCB = "design/ecad/source/usb-power-hub.kicad_pcb"
CENTRE = 50.0
TOL = 0.001
# What a user sees from outside: the receptacles, the buttons and the LEDs. (left, right)
MIRROR = (("J2", "J3"), ("J4", "J1"), ("SW1", "SW2"), ("D10", "D12"), ("D11", "D13"))
FACE = {ref for pair in MIRROR for ref in pair}
LABELS = {"J2": "OUT A", "J3": "OUT B", "J4": "5V IN", "J1": "HOST"}
# (what, net, from, to): the shortest pad-to-pad line on that net; from/to is a part or a region.
SPANS = (
    ("VBUS_B, shunt ladder to OUT B", "VBUS_B", "RS22", "J3"),
    ("USB pair B, hub to OUT B", "USB_B_P", "U6", "J3"),
    ("USB pair A, hub to OUT A", "USB_A_P", "U6", "J2"),
    ("USB upstream pair, HOST to hub", "USB_UP_P", "J1", "U6"),
    ("V5L, J1's soft start to the MAU104", "V5L", "Q53", "U5"),
    ("V12F, its filter to the channel A front end", "V12F", "R10", "AFE_A"),
    ("V12F, its filter to the channel B front end", "V12F", "R10", "AFE_B"),
)
# (what, a line of the changed document, its replacement, a word check_pcb.py must then print)
NEGATIVE = (
    ("the MAU104 0.25 mm to the left, toward REF",
     "| U5 | 47.85 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |",
     "| U5 | 47.6 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |",
     "from the MAU104"),
    ("the MAU104 0.25 mm to the right, into SW2",
     "| U5 | 47.85 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |",
     "| U5 | 48.1 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |",
     "leaves region MAU"),
    ("D5 back up at y 62.45, onto J1's pin-1 mark",
     "| D5 | 89.35 | 61.8 | 0 | PORT_HOST | J1 VBUS TVS, at J1 |",
     "| D5 | 89.35 | 62.45 | 0 | PORT_HOST | J1 VBUS TVS, at J1 |",
     "silk_overlap"),
)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def copy(scratch):
    for rel in COPIES:
        src, dst = ROOT / rel, scratch / rel
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def build(mp, scratch):
    """make_pcb.py's build(), stopped after the footprints. make_pcb.py itself cannot build a
    changed placement: it stops when the router's session no longer matches the board."""
    pcb, pro, prl, _ = mp.proj.paths(mp.SRC)
    pro_before = pro.read_bytes()
    place = mp.read_placement(mp.DOC)
    with tempfile.TemporaryDirectory(dir=scratch) as tmp:
        tmp = pathlib.Path(tmp)
        comps, pins = mp.read_netlist(mp.export_netlist(tmp))
        unplaced = sorted(set(comps) - set(place), key=mp.natural)
        unknown = sorted(set(place) - set(comps), key=mp.natural)
        if unplaced or unknown:
            raise SystemExit(f"{mp.DOC.name}: not placed: {' '.join(unplaced) or '-'};"
                             f" not in the netlist: {' '.join(unknown) or '-'}")
        work = tmp / "board"
        work.mkdir()
        shutil.copyfile(pro, work / pro.name)
        out = work / pcb.name
        pcbnew.KIID.SeedGenerator(mp.UUID_SEED)
        mp.proj.make_board(out)
        mp.proj.insert_stackup(out)
        board = pcbnew.LoadBoard(str(out))
        nets = {}
        for name in sorted(set(pins.values())):
            nets[name] = pcbnew.NETINFO_ITEM(board, name)
            board.Add(nets[name])
        for ref in sorted(comps, key=mp.natural):
            mp.add_footprint(board, nets, ref, comps[ref], pins, place[ref])
        if not pcbnew.SaveBoard(str(out), board):
            raise SystemExit("pcbnew could not save the board")
        shutil.copyfile(out, pcb)
    mp.proj.fix_uuids(pcb, "pcb")
    if prl.exists():
        prl.unlink()
    if pro.read_bytes() != pro_before:
        pro.write_bytes(pro_before)


def check(scratch):
    """Run the scratch copy's check_pcb.py; its defaults point into the scratch copy."""
    r = subprocess.run([sys.executable, "-I", "-B", str(scratch / "design/ecad/scripts/check_pcb.py"),
                        "--reports", str(scratch / "reports")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    lines = [ln for ln in (r.stdout + r.stderr).splitlines() if ln.strip() and "duplicate image" not in ln]
    return r.returncode, lines


def measure(scratch, cp):
    regions, keepouts, parts, _, _ = cp.read_doc(scratch / DOC)
    board = pcbnew.LoadBoard(str(scratch / PCB))
    at, yard, pads = {}, {}, {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        x, y = cp.frame(fp.GetPosition())
        at[ref] = (round(x, 4), round(y, 4), round(fp.GetOrientationDegrees()) % 360)
        yard[ref] = cp.courtyard(fp)
        pads[ref] = [(pad.GetNetname(), cp.frame(pad.GetPosition())) for pad in fp.Pads()]
    return dict(regions=regions, keepouts=keepouts, parts=parts, at=at, yard=yard, pads=pads)


def members(m, name):
    return [name] if name in m["at"] else sorted(r for r, p in m["parts"].items() if p["region"] == name)


def span(m, net, a, b):
    pa = [xy for ref in members(m, a) for n, xy in m["pads"].get(ref, []) if n == net]
    pb = [xy for ref in members(m, b) for n, xy in m["pads"].get(ref, []) if n == net]
    return min((math.dist(p, q) for p in pa for q in pb), default=None)


def nearest(m, cp, ref, region):
    """(gap in mm, part): the courtyard of `region` nearest to ref's courtyard."""
    return min(((cp.gap(m["yard"][ref], m["yard"][o]), o) for o in members(m, region) if o in m["yard"]),
               default=(None, "-"))


def mm(v):
    return "   n/a" if v is None else f"{v:6.2f}"


def report(before, after, status, lines, change, cp):
    ok = status == 0
    print(f"check_pcb.py on the C2 board: exit {status}: {lines[-1] if lines else 'no output'}")
    for ln in lines:
        if ln.startswith("FAIL"):
            print("  " + ln)

    print(f"\nmirror about x = {CENTRE:g} (left + right = {2 * CENTRE:g}, the same y):")
    for left, right in MIRROR:
        (lx, ly, _), (rx, ry, _) = after["at"][left], after["at"][right]
        was = before["at"][left][0] + before["at"][right][0]
        good = abs(lx + rx - 2 * CENTRE) <= TOL and abs(ly - ry) <= TOL
        ok &= good
        print(f"  {left:4s} ({lx:6.2f}, {ly:6.3f})  {right:4s} ({rx:6.2f}, {ry:6.3f})"
              f"  sum {lx + rx:7.2f} (now {was:6.2f})  {'ok' if good else 'NOT MIRRORED'}")

    moved = sorted(r for r in after["at"] if before["at"].get(r) != after["at"][r])
    by_region = {}
    for ref in moved:
        by_region.setdefault(after["parts"][ref]["region"], []).append(ref)
    print(f"\nparts moved: {len(moved)} of {len(after['at'])}")
    for region in sorted(by_region):
        print(f"  {region:9s} {len(by_region[region]):2d}: {' '.join(by_region[region])}")
    stray = sorted(r for r in by_region if r not in change.MAY_MOVE)
    ok &= bool(moved) and not stray
    print(f"  moved outside {', '.join(change.MAY_MOVE)}: {', '.join(stray) or 'none'}")

    print("\nMAU104 (U5) courtyard to the nearest courtyard of an analog region, mm (check_pcb.py wants >= 6.0):")
    for region in cp.ANALOG:
        (g0, r0), (g1, r1) = nearest(before, cp, "U5", region), nearest(after, cp, "U5", region)
        print(f"  {region:7s} now {mm(g0)} ({r0:5s})   C2 {mm(g1)} ({r1})")
    g, _ = nearest(after, cp, "U5", "SW2")
    print(f"  U5 courtyard to SW2's courtyard in C2: {mm(g).strip()} mm")

    print("\npad to pad on one net, straight line, mm (not a track length):")
    for what, net, a, b in SPANS:
        d0, d1 = span(before, net, a, b), span(after, net, a, b)
        delta = "" if d0 is None or d1 is None else f"  ({d1 - d0:+.1f})"
        print(f"  {what:44s} now {mm(d0)}   C2 {mm(d1)}{delta}")
    return ok, set(moved)


def picture(path, before, after, moved):
    """Both placements, courtyards only, front edge down. Orange: receptacles, buttons, LEDs.
    Blue: the other parts the trial moves."""
    s, margin, head, foot = 7.0, 30.0, 56.0, 30.0
    w, h = 100.0, 72.0
    panel = head + h * s + foot
    width, height = 2 * margin + w * s, 2 * panel + 40.0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" font-family="sans-serif">',
           f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>']

    def rect(r, top, attrs):
        return (f'<rect x="{margin + r[0] * s:.2f}" y="{top + (h - r[3]) * s:.2f}" width="{(r[2] - r[0]) * s:.2f}"'
                f' height="{(r[3] - r[1]) * s:.2f}" {attrs}/>')

    def text(x, y, top, body, attrs):
        return f'<text x="{margin + x * s:.2f}" y="{top + (h - y) * s:.2f}" {attrs}>{body}</text>'

    for k, (title, m) in enumerate((("Now: Rev0.5 r02, the tracked board", before),
                                    ("Trial C2: placement only, not routed", after))):
        top = k * panel + head
        out.append(f'<text x="{margin:.0f}" y="{top - 36:.0f}" font-size="15" font-weight="bold" fill="#202124">{title}</text>')
        out.append(rect((0.0, 0.0, w, h), top, 'fill="#f6f5f0" stroke="#3c4043" stroke-width="1.2"'))
        for name, reg in sorted(m["regions"].items()):
            out.append(rect(reg["rect"], top, 'fill="none" stroke="#9aa0a6" stroke-width="0.6" stroke-dasharray="3 2"'))
            if reg["kind"] == "block":
                out.append(text(reg["rect"][0] + 0.4, reg["rect"][3] - 1.5, top, name, 'font-size="8" fill="#80868b"'))
        for name, r in sorted(m["keepouts"].items()):
            out.append(rect(r, top, 'fill="#d93025" fill-opacity="0.14"'))
        for ref in sorted(m["yard"]):
            fill = "#e8710a" if ref in FACE else "#1a73e8" if ref in moved else "#bdc1c6"
            for r in m["yard"][ref]:
                out.append(rect(r, top, f'fill="{fill}" fill-opacity="0.85" stroke="#ffffff" stroke-width="0.3"'))
        x = margin + CENTRE * s
        out.append(f'<line x1="{x:.2f}" y1="{top - 8:.0f}" x2="{x:.2f}" y2="{top + h * s + 8:.0f}"'
                   ' stroke="#188038" stroke-width="1" stroke-dasharray="6 4"/>')
        for ref, label in sorted(LABELS.items()):
            px, py, _ = m["at"][ref]
            ty = -3.3 if py < h / 2 else h + 2.1
            out.append(text(px, ty, top, f"{label} x {px:g}", 'font-size="11" text-anchor="middle" fill="#202124"'))
        for ref in ("SW1", "SW2"):
            px, py, _ = m["at"][ref]
            out.append(text(px, py - 0.6, top, ref, 'font-size="9" text-anchor="middle" fill="#ffffff"'))
        ux = (m["yard"]["U5"][0][0] + m["yard"]["U5"][0][2]) / 2
        uy = (m["yard"]["U5"][0][1] + m["yard"]["U5"][0][3]) / 2
        out.append(text(ux, uy - 0.6, top, "MAU104", 'font-size="10" text-anchor="middle" fill="#ffffff"'))
    y = 2 * panel + 16
    legend = (("#e8710a", "receptacles, buttons, LEDs"), ("#1a73e8", "other parts the trial moves"),
              ("#bdc1c6", "parts that stay"), ("#d93025", "keepouts: USB pair lanes"))
    for k, (colour, label) in enumerate(legend):
        x = margin + k * 178
        opacity = "0.14" if colour == "#d93025" else "0.85"
        out.append(f'<rect x="{x:.0f}" y="{y - 10:.0f}" width="14" height="12" fill="{colour}" fill-opacity="{opacity}" stroke="#9aa0a6" stroke-width="0.5"/>')
        out.append(f'<text x="{x + 20:.0f}" y="{y:.0f}" font-size="11" fill="#202124">{label}</text>')
    out.append("</svg>")
    path.write_bytes(("\n".join(out) + "\n").encode("utf-8"))


def negatives(mp, scratch, change):
    """A checker never seen failing is no evidence: break the C2 placement and expect a FAIL."""
    doc, ok = scratch / DOC, True
    print("\nnegative runs (each must make check_pcb.py fail):")
    for what, old, new, word in NEGATIVE:
        shutil.copyfile(ROOT / DOC, doc)
        change.apply(doc, extra=[(old, new)])
        build(mp, scratch)
        status, lines = check(scratch)
        hits = [ln for ln in lines if ln.startswith("FAIL") and word in ln]
        caught = status != 0 and bool(hits)
        ok &= caught
        print(f"  {what}: exit {status}, {'caught' if caught else 'NOT CAUGHT'}"
              + (f": {hits[0][:110]}" if hits else ""))
    shutil.copyfile(ROOT / DOC, doc)
    change.apply(doc)
    build(mp, scratch)
    return ok


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in argv[1:] if a != "--negative"]
    if len(args) != 1:
        raise SystemExit("usage: trial.py <new scratch directory> [--negative]")
    scratch = pathlib.Path(args[0]).resolve()
    if scratch == ROOT or ROOT in scratch.parents:
        raise SystemExit(f"{scratch} is inside the repository: give a directory outside it")
    if scratch.exists() and any(scratch.iterdir()):
        raise SystemExit(f"{scratch} is not empty: give a new directory")
    copy(scratch)
    change = load(HERE / "c2_change.py", "c2_change")
    cp = load(scratch / "design/ecad/scripts/check_pcb.py", "check_pcb")
    mp = load(scratch / "design/ecad/scripts/make_pcb.py", "make_pcb")
    if cp.ROOT != scratch or mp.ROOT != scratch:
        raise SystemExit(f"the copied scripts resolve their root to {cp.ROOT} and {mp.ROOT}, not {scratch}")
    before = measure(scratch, cp)              # the copy of the tracked, routed board
    change.apply(scratch / DOC)
    build(mp, scratch)
    status, lines = check(scratch)
    after = measure(scratch, cp)
    ok, moved = report(before, after, status, lines, change, cp)
    picture(scratch / "layout_c2.svg", before, after, moved)
    print(f"\nwrote {scratch / 'layout_c2.svg'}")
    if "--negative" in argv[1:]:
        ok &= negatives(mp, scratch, change)
    print(f"\ntrial C2: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
