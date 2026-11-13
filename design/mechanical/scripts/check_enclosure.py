"""Check the enclosure's files against the board interface and the document.

Run with the CAD venv's Python (manifold3d, numpy, trimesh), from the repository root:

    ~/tmp/cadvenv/Scripts/python.exe -I -B design/mechanical/scripts/check_enclosure.py

It reads the STL files as written, puts each back into the assembly frame with the
manifest's matrix, and tests them with probes built here from the board interface and the
document's tables: it does not import make_enclosure.py. Checks E01 to E16 are listed in
ENCLOSURE_Rev0.1.md, section 7, with what they prove. Exit status 0 means no FAIL line.

What it cannot see (the document, section 7): whether a `world` value in the tables is
right (a cable's overmould, the insert, an assumed part height), the print itself
(shrinkage, sag, a thin web the slicer drops), strength, light, heat, the unit in the
hand, and what a picture shows (E16 reads only the build a picture names).
V-MECH-01 and V-BOOT-01 stay open whatever this prints.

  --dir DIR         the pieces (default design/mechanical/assembly)
  --doc FILE        the document      --interface FILE   the board interface
  --board FILE      the KiCad board the interface must still describe
  --pictures DIR    the pictures of these pieces (default design/mechanical/reports for
                    the default --dir; for another --dir they are checked only if given)
"""
import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import struct
import sys
from types import SimpleNamespace

import numpy as np
import trimesh

HERE = pathlib.Path(__file__).resolve().parent


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load("enclosure_spec")
S = _load("enclosure_solid")

TOL = 0.02      # mm3: what two touching faces overlap by after float32 round-off
SLAB = 0.05     # mm: thickness of the slabs that measure a contact area
OVERHANG = -0.72  # a face's downward normal beyond 45 degrees (cos 45 = 0.707)
EDGE = 0.5      # mm: the width of the lid's edge that must lie on the frame all round


class Report:
    def __init__(self):
        self.failed = 0
        self.count = 0

    def ok(self, cid, text):
        self.count += 1
        print(f"PASS {cid} {text}")

    def fail(self, cid, text):
        self.count += 1
        self.failed += 1
        print(f"FAIL {cid} {text}")

    def check(self, cond, cid, text, bad):
        self.ok(cid, text) if cond else self.fail(cid, bad)
        return cond


def vol(a, b):
    return (a ^ b).volume()


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def png_source(path):
    """The text of a PNG file's text chunk named Source, or None."""
    raw = pathlib.Path(path).read_bytes()
    at = 8
    while raw[:8] == b"\x89PNG\r\n\x1a\n" and at + 8 <= len(raw):
        n, tag = struct.unpack(">I4s", raw[at:at + 8])
        data = raw[at + 8:at + 8 + n]
        if tag == b"tEXt" and data.startswith(b"Source\x00"):
            return data[7:].decode("latin-1")
        at += 12 + n
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", type=pathlib.Path, default=spec.ASSEMBLY)
    ap.add_argument("--doc", type=pathlib.Path, default=spec.DOC)
    ap.add_argument("--interface", type=pathlib.Path, default=spec.INTERFACE)
    ap.add_argument("--board", type=pathlib.Path, default=None)
    ap.add_argument("--pictures", type=pathlib.Path, default=None)
    args = ap.parse_args()
    if args.pictures is None and args.dir.resolve() == spec.ASSEMBLY.resolve():
        args.pictures = spec.REPORTS
    R = Report()

    params, heights = spec.load_doc(args.doc)
    p = SimpleNamespace(**params)
    board = spec.load_interface(args.interface)
    o, t = board["outline"], board["thickness"]
    bx0, by0, bx1, by1 = o["x0"], o["y0"], o["x1"], o["y1"]
    xi0, yi0, xi1, yi1 = bx0 - p.gap, by0 - p.gap, bx1 + p.gap, by1 + p.gap
    xo0, yo0, xo1, yo1 = xi0 - p.wall, yi0 - p.wall, xi1 + p.wall, yi1 + p.wall
    z_bottom = -t - p.standoff - p.floor
    z_top, z_lid = p.cavity_h, p.cavity_h + p.lid_t

    # ---- E01 the files ------------------------------------------------------------------------
    mpath = args.dir / spec.MANIFEST
    if not mpath.is_file():
        R.fail("E01", f"no manifest {mpath.name} in {args.dir}")
        print("enclosure check: stopped, 1 failed")
        return 1
    manifest = json.loads(mpath.read_text(encoding="ascii"))
    names = [q["name"] for q in manifest["pieces"]]
    stop = not R.check(names == ["Tray", "Frame", "Plunger"], "E01", "pieces: Tray, Frame, Plunger",
                       f"pieces {names}, want Tray, Frame, Plunger")
    for q in manifest["pieces"] + [dict(manifest["lid_interface"], name="LidInterface")]:
        f = args.dir / q["file"]
        if not f.is_file():
            R.fail("E01", f"{q['file']}: missing")
            stop = True
        elif sha256(f) != q["sha256"]:
            R.fail("E01", f"{q['file']}: SHA-256 differs from the manifest's")
        else:
            R.ok("E01", f"{q['file']}: SHA-256 as in the manifest")
    R.check(manifest["document"]["inputs_sha256"] == spec.inputs_digest(params, heights), "E01",
            "built from the document's tables as they stand",
            "the document's tables changed after the pieces were built")
    R.check(not manifest["overrides"], "E01", "no parameter overridden",
            f"built with overrides {manifest['overrides']}: not the document's design")
    R.check(manifest["board_interface"]["sha256"] == sha256(args.interface), "E01",
            "built from the board interface as it stands",
            "the board interface changed after the pieces were built")
    bpath = args.board or (spec.ROOT / board["source"]["path"])
    R.check(bpath.is_file() and sha256(bpath) == board["source"]["sha256"], "E01",
            "the board interface describes the tracked board",
            f"the board {bpath.name} changed after its interface was exported: "
            "run export_board_interface.py")
    if stop:
        print(f"enclosure check: stopped, {R.failed} failed")
        return 1

    # ---- E02 each STL is one closed body ------------------------------------------------------
    printed = {q["name"]: S.read_stl(args.dir / q["file"]) for q in manifest["pieces"]}
    before = R.failed
    for name, tri in printed.items():
        verts, faces = S.weld(tri)
        mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        closed = mesh.is_watertight and mesh.is_winding_consistent and mesh.volume > 0
        bodies = len(S.to_manifold(tri).decompose()) if closed else 0
        R.check(closed and bodies == 1, "E02", f"{name}: one closed body, {len(tri)} triangles, "
                f"{mesh.volume / 1000:.2f} cm3",
                f"{name}: watertight {mesh.is_watertight}, winding consistent "
                f"{mesh.is_winding_consistent}, volume {mesh.volume:.1f} mm3, "
                f"bodies {bodies if closed else 'not counted'}")
    if R.failed > before:
        print(f"enclosure check: stopped (the other checks need closed bodies), {R.failed} failed")
        return 1

    asm = {q["name"]: [S.to_manifold(S.apply(printed[q["name"]], m)) for m in q["to_assembly"]]
           for q in manifest["pieces"]}
    tray, frame, plungers = asm["Tray"][0], asm["Frame"][0], asm["Plunger"]
    lid_if = json.loads((args.dir / manifest["lid_interface"]["file"]).read_text(encoding="ascii"))
    lo = lid_if["outline"]
    lid = S.box(lo["x0"], lo["y0"], lid_if["underside_above_board"], lo["x1"], lo["y1"],
                lid_if["underside_above_board"] + lid_if["thickness"])
    for hole in lid_if["holes"]:
        lid = lid - S.cyl(hole["x"], hole["y"], z_top - 5.0, z_lid + 5.0, hole["d"] / 2)

    # ---- E03 size -----------------------------------------------------------------------------
    def box_is(name, man, want):
        got = S.bbox(man)
        R.check(all(abs(a - b) <= 0.01 for a, b in zip(got, want)), "E03",
                f"{name}: x {got[0]:.2f} .. {got[3]:.2f}, y {got[1]:.2f} .. {got[4]:.2f}, "
                f"z {got[2]:.2f} .. {got[5]:.2f}",
                f"{name}: box {[round(v, 3) for v in got]}, want {[round(v, 3) for v in want]}")

    box_is("Tray", tray, [xo0, yo0, z_bottom, xo1, yo1, p.lip_h])
    box_is("Frame", frame, [xo0, yo0, 0.0, xo1, yo1, z_top])

    def outline(shrink, za, zb):
        """The outer outline with its round corners, `shrink` inside it, as a prism."""
        r = p.corner_r
        return S.Manifold.batch_hull([S.cyl(cx, cy, za, zb, r - shrink)
                                      for cx in (xo0 + r, xo1 - r) for cy in (yo0 + r, yo1 - r)])

    space = (S.box(xo0 - 5, yo0 - 5, z_bottom - 1, xo1 + 5, yo1 + 5, z_top + 1)
             - outline(0.0, z_bottom - 2, z_top + 2))
    for sname, solid in (("Tray", tray), ("Frame", frame)):
        v = vol(solid, space)
        R.check(v <= TOL, "E03", f"{sname}: nothing outside the outline and its {p.corner_r:g} mm corners",
                f"{sname}: {v:.3f} mm3 outside the outline and its {p.corner_r:g} mm corners")

    # ---- E04 printable without support --------------------------------------------------------
    bed_min = {"Tray": 200.0, "Frame": 200.0, "Plunger": 5.0}
    for name, tri in printed.items():
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        area = np.linalg.norm(n, axis=1) / 2
        nz = np.divide(n[:, 2], 2 * area, out=np.zeros(len(n)), where=area > 0)
        zmin = tri[:, :, 2].min()
        on_bed = (tri[:, :, 2].max(axis=1) < zmin + 1e-3)
        bed = float(area[on_bed & (nz < -0.99)].sum())
        hang = float(area[(nz < OVERHANG) & ~on_bed].sum())
        R.check(abs(zmin) <= 1e-3 and bed >= bed_min[name], "E04",
                f"{name}: stands on the bed on {bed:.0f} mm2",
                f"{name}: lowest point z {zmin:.3f}, {bed:.1f} mm2 on the bed, "
                f"want 0 and >= {bed_min[name]:.0f} mm2")
        R.check(hang <= 0.5, "E04", f"{name}: no face steeper than 45 degrees hangs in the air",
                f"{name}: {hang:.1f} mm2 of faces steeper than 45 degrees hang in the air "
                "in the print orientation")

    # ---- E05 the parts ------------------------------------------------------------------------
    usb = {r["ref"]: r for r in spec.receptacles(board)}
    envelopes, tallest = [], (0.0, "")
    for fp in board["footprints"]:
        name = spec.footprint_name(fp)
        if name not in heights:
            R.fail("E05", f"{fp['ref']}: no height in the document for {name}")
            continue
        h = heights[name]
        tallest = max(tallest, (h, fp["ref"]))
        if h <= 0:
            continue
        if fp["ref"] in usb:
            s = -1.0 if usb[fp["ref"]]["edge"] == "front" else 1.0
            ya, yb = sorted((fp["y"] + s * p.usb_shell_len / 2, fp["y"] - s * p.usb_shell_len / 2))
            env = S.box(fp["x"] - p.usb_shell_w / 2, ya, 0.0, fp["x"] + p.usb_shell_w / 2, yb, h)
        else:
            x0, y0, x1, y1 = fp["courtyard"]
            if x0 < xi0 or y0 < yi0 or x1 > xi1 or y1 > yi1:
                R.fail("E05", f"{fp['ref']}: its courtyard leaves the cavity")
            env = S.box(x0, y0, 0.0, x1, y1, h + p.part_margin)
        envelopes.append((fp["ref"], h, env))
    every = S.union([e for _r, _h, e in envelopes])
    bad = 0
    for sname, solid in (("Tray", tray), ("Frame", frame), ("Lid", lid)):
        if vol(every, solid) > TOL:
            for ref, h, env in envelopes:
                v = vol(env, solid)
                if v > TOL:
                    bad += 1
                    R.fail("E05", f"{ref}: {v:.2f} mm3 of the {sname} inside its envelope "
                           f"(height {h:g} mm + {p.part_margin:g} mm)")
    if not bad:
        R.ok("E05", f"{len(envelopes)} parts clear of tray, frame and lid; the tallest "
             f"({tallest[1]}, {tallest[0]:g} mm) is {z_top - tallest[0]:.2f} mm under the lid")

    # ---- E06 the leads under the board --------------------------------------------------------
    mount = {ref for ref, _x, _y in spec.mounting_holes(board)}
    stubs = []
    for hole in board["holes"]:
        if hole["ref"] in mount:
            continue
        r = max(hole["drill"]) / 2 + (0.5 if hole["plated"] else 0.2)
        stubs.append((hole, S.cyl(hole["x"], hole["y"], -t - p.tht_stub, -t, r)))
    bad = 0
    if vol(S.union([s for _h, s in stubs]), tray) > TOL:
        for hole, stub in stubs:
            v = vol(stub, tray)
            if v > TOL:
                bad += 1
                R.fail("E06", f"{hole['ref']} pad '{hole['pad']}' at ({hole['x']}, {hole['y']}): "
                       f"{v:.2f} mm3 of the Tray within {p.tht_stub:g} mm below its hole")
    if not bad:
        R.ok("E06", f"{len(stubs)} holes: the tray clears {p.tht_stub:g} mm of lead below each")

    # ---- E07 how the board is held ------------------------------------------------------------
    pcb = S.box(bx0, by0, -t, bx1, by1, 0.0)
    for sname, solid in (("Tray", tray), ("Frame", frame)):
        v = vol(pcb, solid)
        R.check(v <= TOL, "E07", f"the board does not enter the {sname}",
                f"{v:.2f} mm3 of the {sname} inside the board")
    holes = spec.mounting_holes(board)
    for ref, hx, hy in holes:
        x0, y0, x1, y1 = max(hx - 3, bx0), max(hy - 3, by0), min(hx + 3, bx1), min(hy + 3, by1)
        under = vol(tray, S.box(x0, y0, -t - SLAB, x1, y1, -t)) / SLAB
        over = vol(frame, S.box(x0, y0, 0.0, x1, y1, SLAB)) / SLAB
        R.check(under >= 15 and over >= 15, "E07",
                f"{ref}: the board lies on {under:.0f} mm2 of boss under {over:.0f} mm2 of post",
                f"{ref}: {under:.1f} mm2 of boss below and {over:.1f} mm2 of post above, "
                "want >= 15 mm2 each")
    R.check(len(holes) >= 3, "E07", f"{len(holes)} mounting points",
            f"{len(holes)} mounting points, want >= 3")
    for edge, y_edge in (("front", by0), ("back", by1)):
        if not any(r["edge"] == edge for r in usb.values()):
            continue
        near = [ref for ref, _hx, hy in holes if abs(hy - y_edge) <= 10]
        R.check(len(near) >= 1, "E07", f"the {edge} edge has mounting points {', '.join(near)}",
                f"no mounting point within 10 mm of the {edge} edge, which carries receptacles")
    for ref, r in usb.items():
        s = -1.0 if r["edge"] == "front" else 1.0
        y_edge = by0 if s < 0 else by1
        ya, yb = sorted((y_edge, y_edge - s * 4.0))
        z_rib = -t - p.rib_gap
        area = vol(tray, S.box(r["cx"] - 1.5, ya, z_rib - SLAB - 0.001, r["cx"] + 1.5, yb,
                               z_rib - 0.001)) / SLAB
        touch = vol(tray, S.box(r["cx"] - 1.5, ya, z_rib + 0.01, r["cx"] + 1.5, yb, -t))
        R.check(area >= 8 and touch <= TOL, "E07",
                f"{ref}: {area:.0f} mm2 of rib {p.rib_gap:g} mm under the board's edge",
                f"{ref}: {area:.1f} mm2 of rib {p.rib_gap:g} mm under the board's edge "
                f"(want >= 8 mm2) and {touch:.2f} mm3 above that level (want 0)")

    # ---- E08 the port openings ----------------------------------------------------------------
    for ref, r in usb.items():
        fp = board["by_ref"][ref]
        s = -1.0 if r["edge"] == "front" else 1.0
        y_face = fp["y"] + s * p.usb_shell_len / 2
        c = p.shell_clear - 0.02
        ya, yb = sorted((y_face + s * 5.0, y_face - s * p.usb_shell_len))
        probe = S.box(r["cx"] - p.usb_shell_w / 2 - c, ya, -c, r["cx"] + p.usb_shell_w / 2 + c, yb,
                      p.usb_shell_h + c)
        v = vol(probe, tray) + vol(probe, frame)
        R.check(v <= TOL, "E08", f"{ref}: {p.shell_clear:g} mm around the shell",
                f"{ref}: {v:.2f} mm3 of plastic within {p.shell_clear:g} mm of the shell")
        ya, yb = sorted((y_face, y_face + s * 25.0))
        plug = S.slot_y(r["cx"], p.usb_shell_h / 2, p.plug_w, p.plug_h, p.plug_r, ya, yb)
        vt, vf = vol(plug, tray), vol(plug, frame)
        R.check(vt + vf <= TOL, "E08",
                f"{ref}: an overmould of {p.plug_w:g} x {p.plug_h:g} mm reaches the receptacle's face",
                f"{ref}: an overmould of {p.plug_w:g} x {p.plug_h:g} mm meets the tray "
                f"({vt:.2f} mm3) or the frame ({vf:.2f} mm3) before the receptacle's face")
        x0 = r["cx"] + p.usb_shell_w / 2 + p.shell_clear + 0.3
        z0 = p.usb_shell_h / 2 + 0.1
        ya, yb = sorted((y_face + s * 6.0, y_face - s * 3.0))
        web = vol(frame, S.box(x0, ya, z0, x0 + 0.2, yb, z0 + 0.2)) / 0.04
        r["web"] = web
        R.check(web >= p.web_min, "E08", f"{ref}: a web of {web:.2f} mm closes the pocket",
                f"{ref}: web {web:.2f} mm between pocket and cavity, want >= {p.web_min:g} mm")

    # ---- E09 the fasteners --------------------------------------------------------------------
    z_head = z_bottom + (p.csk_d - p.csk_head_d) / 2
    e_bottom = z_head + p.bottom_screw_len
    e_lid = p.lid_screw_len - p.lid_t
    e_max = p.insert_hole_depth - 0.5
    R.check(p.engage_min <= e_bottom <= e_max, "E09",
            f"bottom screws: {e_bottom:.2f} mm of thread in the post's insert",
            f"bottom screws: {e_bottom:.2f} mm of thread above the board, want "
            f"{p.engage_min:g} .. {e_max:g} mm")
    R.check(p.engage_min <= e_lid <= e_max, "E09",
            f"lid screws: {e_lid:.2f} mm of thread in the post's insert",
            f"lid screws: {e_lid:.2f} mm of thread below the lid, want {p.engage_min:g} .. {e_max:g} mm")
    head_h = (p.csk_head_d - p.screw_d) / 2
    hole_r = p.insert_hole_d / 2
    lid_screw = {(h["x"], h["y"]): h for h in lid_if["holes"] if h["kind"] == "screw"}
    for ref, hx, hy in holes:
        shaft = S.cyl(hx, hy, z_bottom - 1.0, max(e_bottom, 0.5), (p.screw_d + 0.1) / 2)
        flush = S.cyl(hx, hy, z_bottom, z_bottom + head_h, p.csk_head_d / 2, p.screw_d / 2)
        deep = S.cyl(hx, hy, z_head + 0.3, z_head + 0.3 + head_h, p.csk_head_d / 2, p.screw_d / 2)
        v = vol(shaft, tray) + vol(shaft, frame) + vol(flush, tray)
        seat = vol(deep, tray)
        R.check(v <= TOL and seat > 0.05, "E09",
                f"{ref}: the bottom screw passes, and its head sinks flush and seats",
                f"{ref}: {v:.2f} mm3 of plastic in the bottom screw's way (want 0), "
                f"{seat:.2f} mm3 of seat under its head (want > 0.05)")
        top = S.cyl(hx, hy, z_top - max(e_lid, 0.5), z_lid + 1.0, (p.screw_d + 0.1) / 2)
        v = vol(top, frame) + vol(top, lid)
        R.check(v <= TOL and (hx, hy) in lid_screw, "E09", f"{ref}: the lid screw passes",
                f"{ref}: {v:.2f} mm3 in the lid screw's way, lid hole "
                f"{'present' if (hx, hy) in lid_screw else 'missing'}")
        for where, za, zb in (("foot", 0.05, p.insert_hole_depth - 0.05),
                              ("top", z_top - p.insert_hole_depth + 0.05, z_top - 0.05)):
            ring = (S.cyl(hx, hy, za, zb, hole_r + p.insert_wall_min - 0.02)
                    - S.cyl(hx, hy, za - 1.0, zb + 1.0, hole_r + 0.02))
            solid = vol(ring, frame) / ring.volume()
            empty = vol(S.cyl(hx, hy, za, zb, hole_r - 0.03), frame)
            R.check(solid >= 0.995 and empty <= TOL, "E09",
                    f"{ref} {where}: a {p.insert_hole_d:g} mm insert hole in "
                    f"{p.insert_wall_min:g} mm of plastic",
                    f"{ref} {where}: {100 * solid:.1f} % of the {p.insert_wall_min:g} mm ring "
                    f"around the insert hole is plastic (want 100), {empty:.2f} mm3 in the hole")

    # ---- E10 the buttons ----------------------------------------------------------------------
    buttons, others = spec.switches(board)
    lid_btn = {(h["x"], h["y"]) for h in lid_if["holes"] if h["kind"] == "button"}
    R.check(len(plungers) == len(buttons), "E10", f"{len(buttons)} buttons, {len(plungers)} plungers",
            f"{len(buttons)} port buttons on the board, {len(plungers)} plungers")
    for b, plunger in zip(buttons, plungers):
        ref = b["ref"]
        sw_h = heights[spec.footprint_name(board["by_ref"][ref])]
        bb = S.bbox(plunger)
        cx, cy = (bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2
        R.check(abs(cx - b["x"]) <= 0.02 and abs(cy - b["y"]) <= 0.02 and abs(bb[2] - sw_h) <= 0.02,
                "E10", f"{ref}: the plunger stands on the actuator at {sw_h:g} mm",
                f"{ref}: plunger axis ({cx:.2f}, {cy:.2f}), foot at {bb[2]:.2f} mm; switch at "
                f"({b['x']}, {b['y']}), actuator at {sw_h:g} mm")
        rest = vol(plunger, frame) + vol(plunger, lid)
        down = plunger.translate([0, 0, -(p.sw_travel + 0.15)])
        pressed = vol(down, frame)
        side = 0.0
        for dx, dy in ((0.15, 0), (-0.15, 0), (0, 0.15), (0, -0.15)):
            moved = plunger.translate([dx, dy, 0])
            side += vol(moved, frame) + vol(moved, lid)
        R.check(rest <= TOL and pressed <= TOL and side <= TOL, "E10",
                f"{ref}: the plunger is free at rest, {p.sw_travel + 0.15:g} mm down and "
                "0.15 mm to each side",
                f"{ref}: the plunger meets plastic: {rest:.2f} mm3 at rest, {pressed:.2f} mm3 "
                f"pressed {p.sw_travel + 0.15:g} mm, {side:.2f} mm3 moved 0.15 mm sideways")
        wander = min(vol(plunger.translate([dx, dy, 0]), frame)
                     for dx, dy in ((0.5, 0), (-0.5, 0), (0, 0.5), (0, -0.5)))
        R.check(wander > 0.05, "E10", f"{ref}: the bore keeps the plunger within 0.5 mm",
                f"{ref}: the plunger can move 0.5 mm sideways without meeting the frame")
        up_free = vol(plunger.translate([0, 0, p.plunger_play - 0.05]), lid)
        up_stop = vol(plunger.translate([0, 0, p.plunger_play + 0.6]), lid)
        R.check(up_free <= TOL and up_stop > 0.05, "E10",
                f"{ref}: the lid keeps the plunger in, with {p.plunger_play:g} mm of play",
                f"{ref}: lifted {p.plunger_play - 0.05:g} mm the plunger meets the lid by "
                f"{up_free:.2f} mm3 (want 0); lifted {p.plunger_play + 0.6:g} mm by "
                f"{up_stop:.2f} mm3 (want > 0.05: it must not leave)")
        proud = bb[5] - z_lid
        R.check(proud >= p.sw_travel + 0.5 and (b["x"], b["y"]) in lid_btn, "E10",
                f"{ref}: the cap stands {proud:.2f} mm above the lid",
                f"{ref}: cap {proud:.2f} mm above the lid (want >= {p.sw_travel + 0.5:g}), lid hole "
                f"{'present' if (b['x'], b['y']) in lid_btn else 'missing'}")

    # ---- E11 the LEDs -------------------------------------------------------------------------
    windows = [w["rect"] for w in lid_if["windows"]]
    for fp in board["footprints"]:
        name = spec.footprint_name(fp)
        if not name.startswith("LED_"):
            continue
        x, y, h = fp["x"], fp["y"], heights[name]
        seen = vol(frame, S.box(x - 0.5, y - 0.5, h + 0.01, x + 0.5, y + 0.5, z_top))
        win = any(w[0] <= x - 0.5 and w[1] <= y - 0.5 and w[2] >= x + 0.5 and w[3] >= y + 0.5
                  for w in windows)
        R.check(seen <= TOL and win, "E11", f"{fp['ref']}: a free path up to a window in the lid",
                f"{fp['ref']}: {seen:.2f} mm3 of frame above it, window in the lid "
                f"{'present' if win else 'missing'}")
    for w in windows:
        za, zb = p.ui_bottom + 1.0, z_top - 1.0
        ring = (S.box(w[0] - 0.6, w[1] - 0.6, za, w[2] + 0.6, w[3] + 0.6, zb)
                - S.box(w[0] - 0.1, w[1] - 0.1, za - 1.0, w[2] + 0.1, w[3] + 0.1, zb + 1.0))
        solid = vol(ring, frame) / ring.volume()
        R.check(solid >= 0.995, "E11",
                f"window at ({w[0]:.2f}, {w[1]:.2f}): a closed light well below it",
                f"window at ({w[0]:.2f}, {w[1]:.2f}): {100 * solid:.1f} % of the wall around "
                "its light well is plastic, want 100")

    # ---- E12 the pinhole ----------------------------------------------------------------------
    lid_pin = {(h["x"], h["y"]) for h in lid_if["holes"] if h["kind"] == "pinhole"}
    for b in others:
        sw_h = heights[spec.footprint_name(board["by_ref"][b["ref"]])]
        wire = S.cyl(b["x"], b["y"], sw_h + 0.01, z_lid + 1.0, p.clip_d / 2)
        v = vol(wire, frame) + vol(wire, lid)
        r0 = p.sw_actuator_d / 2 + 0.15
        za, zb = p.ui_bottom + 1.0, z_top - 1.0
        ring = S.cyl(b["x"], b["y"], za, zb, r0 + 0.5) - S.cyl(b["x"], b["y"], za - 1, zb + 1, r0)
        solid = vol(ring, frame) / ring.volume()
        R.check(v <= TOL and solid >= 0.995 and (b["x"], b["y"]) in lid_pin, "E12",
                f"{b['ref']}: a {p.clip_d:g} mm wire reaches the actuator through the lid, in a "
                f"tube no wider than {2 * r0:g} mm",
                f"{b['ref']}: {v:.2f} mm3 in the wire's way, {100 * solid:.1f} % of the tube's "
                f"wall is plastic (want 100), pinhole in the lid "
                f"{'present' if (b['x'], b['y']) in lid_pin else 'missing'}")

    # ---- E13 the lid --------------------------------------------------------------------------
    v = vol(lid, frame)
    fz = S.bbox(frame)[5]
    same = [lo["x0"], lo["y0"], lo["x1"], lo["y1"]] == [bx0, by0, bx1, by1]
    R.check(v <= TOL and abs(lid_if["underside_above_board"] - fz) <= 0.01 and same, "E13",
            "the lid has the board's outline and lies on the frame's top face",
            f"{v:.2f} mm3 of the lid inside the frame; lid underside at "
            f"{lid_if['underside_above_board']:g} mm, frame top at {fz:.2f} mm; outline "
            f"{'the' if same else 'not the'} board's")
    under = S.box(lo["x0"], lo["y0"], fz - SLAB, lo["x1"], lo["y1"], fz)
    seat = vol(frame, under) / SLAB
    band = under - S.box(lo["x0"] + EDGE, lo["y0"] + EDGE, fz - 1.0,
                         lo["x1"] - EDGE, lo["y1"] - EDGE, fz + 1.0)
    edge = vol(frame, band) / band.volume()
    R.check(edge >= 0.995, "E13",
            f"the lid's outer {EDGE:g} mm lies on the frame all round; {seat:.0f} mm2 of contact "
            "in all",
            f"{100 * edge:.1f} % of the lid's outer {EDGE:g} mm lies on the frame, want 100; "
            f"{seat:.1f} mm2 of contact in all")
    for ref, hx, hy in holes:
        x0, y0, x1, y1 = max(hx - 3, bx0), max(hy - 3, by0), min(hx + 3, bx1), min(hy + 3, by1)
        a = vol(frame, S.box(x0, y0, fz - SLAB, x1, y1, fz)) / SLAB
        R.check(a >= 15, "E13", f"{ref}: {a:.0f} mm2 of post under the lid",
                f"{ref}: {a:.1f} mm2 of post under the lid, want >= 15 mm2")

    # ---- E14 the seam -------------------------------------------------------------------------
    v = vol(tray, frame)
    gap = tray.min_gap(frame, 2.0)
    R.check(v <= TOL and abs(gap - p.seam_gap) <= 0.02, "E14",
            f"tray and frame do not touch: the smallest gap is {gap:.2f} mm",
            f"{v:.2f} mm3 shared by tray and frame; smallest gap {gap:.3f} mm, want "
            f"{p.seam_gap:g} mm")
    pockets = S.union([S.box(r["cx"] - p.pocket_w / 2 - 0.5, (yo0 if r["edge"] == "front" else yi1) - 1,
                             z_bottom, r["cx"] + p.pocket_w / 2 + 0.5,
                             (yi0 if r["edge"] == "front" else yo1) + 1, z_top)
                       for r in usb.values()])
    for sname, solid, za in (("Tray", tray, -0.15), ("Frame", frame, p.seam_gap + 0.05)):
        skin = outline(0.0, za, za + 0.1) - outline(0.3, za - 1, za + 2) - pockets
        whole = vol(skin, solid) / skin.volume()
        R.check(whole >= 0.995, "E14",
                f"{sname}: its outer 0.3 mm is whole all round the seam, outside the pockets",
                f"{sname}: {100 * whole:.1f} % of its outer 0.3 mm at the seam is plastic, "
                "want 100 outside the pockets")

    # ---- E15 the document's derived figures ---------------------------------------------------
    tb, fb, pb = S.bbox(tray), S.bbox(frame), S.bbox(plungers[0])

    def face_inset(ref, r):
        y = board["by_ref"][ref]["y"]
        if r["edge"] == "front":
            return (y - p.usb_shell_len / 2) - min(tb[1], fb[1])
        return max(tb[4], fb[4]) - (y + p.usb_shell_len / 2)

    def to_screw(ref):
        fp = board["by_ref"][ref]
        return min(math.hypot(fp["x"] - hx, fp["y"] - hy) for _r, hx, hy in holes)

    swd = [f["courtyard"] for f in board["footprints"]
           if spec.footprint_name(f).startswith("Tag-Connect")]
    measured = {
        "outer_x": max(tb[3], fb[3]) - min(tb[0], fb[0]),
        "outer_y": max(tb[4], fb[4]) - min(tb[1], fb[1]),
        "outer_z": fb[5] + lid_if["thickness"] - tb[2],
        "printed_z": fb[5] - tb[2],
        "tray_z": float(np.ptp(printed["Tray"][:, :, 2])),
        "frame_z": float(np.ptp(printed["Frame"][:, :, 2])),
        "lid_margin": lo["x0"] - min(tb[0], fb[0]),
        "web_t": min(r["web"] for r in usb.values()),
        "face_inset": min(face_inset(ref, r) for ref, r in usb.items()),
        "port_to_screw_max": max(to_screw(ref) for ref in usb),
        # the frame's nearest face beside the footprint, above the seam's chamfer and below the lid
        "swd_wall_clearance": min((frame.min_gap(S.box(c[0], c[1], 3.0, c[2], c[3], 10.0), 20.0)
                                   for c in swd), default=-1.0),
        "lid_clearance_min": fb[5] - tallest[0],
        "bottom_engagement": e_bottom,
        "lid_engagement": e_lid,
        "plunger_len": pb[5] - pb[2],
        "tray_volume": tray.volume() / 1000,
        "frame_volume": frame.volume() / 1000,
        "plunger_volume": plungers[0].volume() / 1000,
    }
    try:
        doc = spec.load_derived(args.doc)
    except ValueError as exc:
        doc = {}
        R.fail("E15", str(exc))
    wrong = [f"{k} {doc.get(k)} (built: {v:.2f})" for k, v in measured.items()
             if k not in doc or abs(doc[k] - v) > 0.0051]
    extra = sorted(set(doc) - set(measured))
    R.check(not wrong and not extra, "E15",
            f"the document's {len(measured)} derived figures are the built files'",
            f"derived figures differ: {'; '.join(wrong + [f'{k} is not measured' for k in extra])}")

    # ---- E16 the pictures ---------------------------------------------------------------------
    if args.pictures is None:
        print("SKIP E16 no pictures given for this directory (--pictures)")
    else:
        want = spec.source_tag(mpath)
        pngs = sorted(args.pictures.glob(f"{spec.PREFIX}*.png"))
        old = [f.name for f in pngs if png_source(f) != want]
        if not pngs:
            R.fail("E16", f"no pictures in {args.pictures.name}: run render_enclosure.py")
        else:
            R.check(not old, "E16", f"{len(pngs)} pictures, each drawn from these files",
                    f"{len(old)} of {len(pngs)} pictures were not drawn from these files "
                    f"({', '.join(old[:3])}{', ...' if len(old) > 3 else ''}): "
                    "run render_enclosure.py")

    print(f"enclosure check: {R.count} checks, {R.failed} failed")
    return 1 if R.failed else 0


if __name__ == "__main__":
    sys.exit(main())
