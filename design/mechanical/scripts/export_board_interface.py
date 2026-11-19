"""Write the board's mechanical interface, read from the tracked KiCad board.

Run with KiCad 9.0's own Python, from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/mechanical/scripts/export_board_interface.py

It reads   design/ecad/source/usb-power-hub.kicad_pcb
and writes design/mechanical/reference/board_interface_Rev0.6.json

The enclosure never copies a board dimension by hand: the outline, the mounting
holes, every footprint's position and courtyard and every drilled hole come from
this file (CLAUDE.md section 7, "one dimension source").

Frame of the output: the placement document's board frame (PLACEMENT_Rev0.6.md),
origin at the board's lower-left corner, x to the right, y up, in mm. A KiCad
sheet point (xk, yk) is (xk - 50, 122 - yk). A courtyard is given as its bounding
box in that frame.

What this script cannot see: a part's height (the enclosure document holds the
height table), and anything that is not in the board file (the plug, the cable).
"""
import hashlib
import json
import pathlib
import sys

import pcbnew

ROOT = pathlib.Path(__file__).resolve().parents[3]
BOARD = ROOT / "design" / "ecad" / "source" / "usb-power-hub.kicad_pcb"
OUT = ROOT / "design" / "mechanical" / "reference" / "board_interface_Rev0.6.json"
ORIGIN_X, ORIGIN_Y = 50.0, 122.0  # make_project.py's board origin on the sheet


def bx(nm):
    return round(pcbnew.ToMM(nm) - ORIGIN_X, 4)


def by(nm):
    return round(ORIGIN_Y - pcbnew.ToMM(nm), 4)


def main():
    out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    raw = BOARD.read_bytes()
    board = pcbnew.LoadBoard(str(BOARD))
    if board is None:
        print("FAIL: the board did not load")
        return 1

    xs, ys = [], []
    for d in board.GetDrawings():
        if d.GetLayer() != pcbnew.Edge_Cuts:
            continue
        for p in (d.GetStart(), d.GetEnd()):
            xs.append(bx(p.x))
            ys.append(by(p.y))
    if not xs:
        print("FAIL: no Edge.Cuts drawing")
        return 1
    outline = {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)}

    footprints, holes = [], []
    for fp in sorted(board.GetFootprints(), key=lambda f: f.GetReference()):
        ref = fp.GetReference()
        pos = fp.GetPosition()
        fp.BuildCourtyardCaches()
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        if cy.OutlineCount() > 0:
            b = cy.BBox()
            court = [bx(b.GetLeft()), by(b.GetBottom()), bx(b.GetRight()), by(b.GetTop())]
        else:
            court = None
        fpid = fp.GetFPID()
        footprints.append({
            "ref": ref,
            "footprint": f"{fpid.GetLibNickname().wx_str()}:{fpid.GetLibItemName().wx_str()}",
            "value": fp.GetValue(),
            "x": bx(pos.x),
            "y": by(pos.y),
            "rot": round(fp.GetOrientationDegrees(), 3),
            "side": "top" if fp.GetLayer() == pcbnew.F_Cu else "bottom",
            "courtyard": court,
        })
        for pad in fp.Pads():
            drill = pad.GetDrillSize()
            if drill.x <= 0:
                continue
            p = pad.GetPosition()
            holes.append({
                "ref": ref,
                "pad": pad.GetNumber(),
                "x": bx(p.x),
                "y": by(p.y),
                "drill": [round(pcbnew.ToMM(drill.x), 4), round(pcbnew.ToMM(drill.y), 4)],
                "plated": pad.GetAttribute() != pcbnew.PAD_ATTRIB_NPTH,
            })

    data = {
        "schema": 1,
        "about": "Mechanical interface of the Rev0.6 board, written by "
                 "design/mechanical/scripts/export_board_interface.py. Do not edit.",
        "source": {
            "path": "design/ecad/source/usb-power-hub.kicad_pcb",
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "frame": "origin at the board's lower-left corner, x right, y up, mm "
                 "(PLACEMENT_Rev0.6.md); KiCad sheet (xk, yk) = (x + 50, 122 - y)",
        "thickness": round(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()), 4),
        "outline": outline,
        "footprints": footprints,
        "holes": sorted(holes, key=lambda h: (h["ref"], h["pad"], h["x"], h["y"])),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=1, ensure_ascii=True) + "\n"
    out.write_bytes(text.encode("ascii"))
    print(f"outline {outline}, thickness {data['thickness']} mm, "
          f"{len(footprints)} footprints, {len(holes)} drilled pads")
    print(f"wrote {out.relative_to(ROOT).as_posix() if out.is_relative_to(ROOT) else out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
