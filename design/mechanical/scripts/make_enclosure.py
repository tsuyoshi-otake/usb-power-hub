"""Build the enclosure's printed pieces and the lid's interface from the document.

Run with the CAD venv's Python (manifold3d, numpy), from the repository root:

    ~/tmp/cadvenv/Scripts/python.exe -I -B design/mechanical/scripts/make_enclosure.py

It reads   design/mechanical/ENCLOSURE_Rev0.2.md   (the params and heights tables)
           design/mechanical/reference/board_interface_Rev0.6.json
and writes design/mechanical/assembly/UsbPowerHub_Enclosure_Rev0.2_Tray.stl, _Frame.stl,
           _Plunger.stl (each in its print orientation), _LidInterface.json, _Manifest.json
then draws the pictures (render_enclosure.py, about 20 s) and runs check_enclosure.py.
Exit status 0 means written, drawn and checked.

  --derived      also rewrite the document's derived-figures table
  --out DIR      write there instead of design/mechanical/assembly (the negative tests);
                 no pictures are drawn of such a build
  --set k=v      override a parameter (the negative tests); the manifest records it
  --no-check     neither draw nor check

Frame of the solids built here: the board frame with z = 0 at the board's top face
(the document, section 2). A piece is turned into its print orientation only when it is
written; the manifest holds the matrix that puts it back.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import pathlib
import subprocess
import sys
from types import SimpleNamespace

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load("enclosure_spec")
S = _load("enclosure_solid")


# ---- where things are ------------------------------------------------------------------------
def geometry(p, heights, board):
    o = board["outline"]
    g = SimpleNamespace()
    g.bx0, g.by0, g.bx1, g.by1 = o["x0"], o["y0"], o["x1"], o["y1"]
    g.t = board["thickness"]
    g.xi0, g.yi0, g.xi1, g.yi1 = g.bx0 - p.gap, g.by0 - p.gap, g.bx1 + p.gap, g.by1 + p.gap
    g.xo0, g.yo0 = g.xi0 - p.wall, g.yi0 - p.wall
    g.xo1, g.yo1 = g.xi1 + p.wall, g.yi1 + p.wall
    g.midx, g.midy = (g.bx0 + g.bx1) / 2, (g.by0 + g.by1) / 2
    g.z_pcb = -g.t                       # the board's bottom face
    g.z_floor = g.z_pcb - p.standoff     # the floor's top face
    g.z_bottom = g.z_floor - p.floor
    g.z_top = p.cavity_h                 # the frame's top face, the lid's underside
    g.z_lid = p.cavity_h + p.lid_t
    g.holes = spec.mounting_holes(board)
    if len(g.holes) < 3:
        raise ValueError("fewer than 3 mounting holes on the board")

    g.ports = []
    for r in spec.receptacles(board):
        fp = board["by_ref"][r["ref"]]
        s = -1.0 if r["edge"] == "front" else 1.0      # outward direction in y
        y_face = fp["y"] + s * p.usb_shell_len / 2
        g.ports.append(SimpleNamespace(
            ref=r["ref"], cx=r["cx"], edge=r["edge"], sign=s, y_face=y_face,
            y_floor=y_face - s * p.face_proud,          # the pocket's floor
            y_in=g.yi0 if s < 0 else g.yi1, y_out=g.yo0 if s < 0 else g.yo1))

    buttons, others = spec.switches(board)
    g.buttons, g.pinholes = [], []
    for b in buttons:
        sw_h = heights[spec.footprint_name(board["by_ref"][b["ref"]])]
        half = p.btn_bore_d / 2 + p.btn_wall
        front = b["y"] < g.midy
        lx = sum(l[1] for l in b["leds"]) / len(b["leds"])
        ly0 = min(l[2] for l in b["leds"]) - p.led_well_margin
        ly1 = max(l[2] for l in b["leds"]) + p.led_well_margin
        well = (lx - p.led_well_w / 2, ly0, lx + p.led_well_w / 2, ly1)
        if front:
            col = (b["x"] - half, g.yi0, b["x"] + half, b["y"] + half)
            block = (well[0] - p.led_wall, col[3], well[2] + p.led_wall, ly1 + p.led_wall)
            room = ly0 - col[3]
        else:
            col = (b["x"] - half, b["y"] - half, b["x"] + half, g.yi1)
            block = (well[0] - p.led_wall, ly0 - p.led_wall, well[2] + p.led_wall, col[1])
            room = col[1] - ly1
        if room < p.led_wall:
            raise ValueError(f"{b['ref']}: its LEDs stand {room:.2f} mm from the button's column")
        if min(col[2], block[2]) - max(col[0], block[0]) < 1.0:
            raise ValueError(f"{b['ref']}: the light well does not join the button's column")
        g.buttons.append(SimpleNamespace(ref=b["ref"], x=b["x"], y=b["y"], h=sw_h, col=col,
                                         block=block, well=well,
                                         leds=[l[0] for l in b["leds"]]))
    for b in others:
        sw_h = heights[spec.footprint_name(board["by_ref"][b["ref"]])]
        half = p.boot_bore_d / 2 + p.boot_wall
        if b["y"] > g.midy:
            block = (b["x"] - half, b["y"] - half, b["x"] + half, g.yi1)
        else:
            block = (b["x"] - half, g.yi0, b["x"] + half, b["y"] + half)
        g.pinholes.append(SimpleNamespace(ref=b["ref"], x=b["x"], y=b["y"], h=sw_h, block=block))

    # the plunger, at rest on its switch
    g.cone_h = (p.plunger_collar_d - p.plunger_cap_d) / 2
    g.z_cap = g.z_lid + p.plunger_proud              # the cap's top
    g.z_collar_top = g.z_top - p.plunger_play        # where the cone meets the cap
    g.z_collar = g.z_collar_top - g.cone_h - p.plunger_collar_h   # the collar's underside
    return g


JOIN = 0.5  # two solids that only share a face stay two bodies: overlap them by this much


def corner(g, hx, hy, reach, join=0.0):
    """The rectangle from the two nearest walls (`join` into them) to `reach` past a hole."""
    x0, x1 = (g.xi0 - join, hx + reach) if hx < g.midx else (hx - reach, g.xi1 + join)
    y0, y1 = (g.yi0 - join, hy + reach) if hy < g.midy else (hy - reach, g.yi1 + join)
    return x0, y0, x1, y1


# ---- the pieces ------------------------------------------------------------------------------
def shell(p, g, z0, z1, chamfer_at):
    """The outer body between z0 and z1: rounded vertical edges, one chamfered end."""
    c, r = p.edge_chamfer, p.corner_r
    parts = []
    for cx in (g.xo0 + r, g.xo1 - r):
        for cy in (g.yo0 + r, g.yo1 - r):
            if chamfer_at == "bottom":
                parts += [S.cyl(cx, cy, z0 + c, z1, r), S.cyl(cx, cy, z0, z1, r - c)]
            else:
                parts += [S.cyl(cx, cy, z0, z1 - c, r), S.cyl(cx, cy, z0, z1, r - c)]
    return S.Manifold.batch_hull(parts)


def port_cutters(p, g):
    """Per port: the overmould pocket from outside, and the shell's hole through the web."""
    cuts = []
    zc = p.usb_shell_h / 2                      # the opening's centre above the board
    hw = p.usb_shell_w / 2 + p.shell_clear
    for port in g.ports:
        s = port.sign
        ya, yb = sorted((port.y_out + s * 1.0, port.y_floor))
        cuts.append(S.slot_y(port.cx, zc, p.pocket_w, p.pocket_h, p.pocket_r, ya, yb))
        ya, yb = sorted((port.y_floor + s * 0.5, port.y_in - s * 1.0))
        cuts.append(S.box(port.cx - hw, ya, -p.shell_clear, port.cx + hw, yb,
                          p.usb_shell_h + p.shell_clear))
    return S.union(cuts)


def build_tray(p, g):
    body = shell(p, g, g.z_bottom, 0.0, "bottom")
    grow = p.lip_h + p.lip_top
    ridge = S.offset_prism(g.xi0, g.yi0, g.xi1, g.yi1,
                           [(-JOIN, grow), (0.0, grow), (p.lip_h, p.lip_top)])
    cavity = S.box(g.xi0, g.yi0, g.z_floor, g.xi1, g.yi1, p.lip_h + 1.0)
    tray = (body + ridge) - cavity
    for _ref, hx, hy in g.holes:
        x0, y0, x1, y1 = corner(g, hx, hy, p.boss_reach, JOIN)
        tray = tray + S.box(x0, y0, g.z_floor - JOIN, x1, y1, g.z_pcb)
    for port in g.ports:
        y0, y1 = ((g.yi0 - JOIN, g.yi0 + p.rib_len) if port.sign < 0
                  else (g.yi1 - p.rib_len, g.yi1 + JOIN))
        tray = tray + S.box(port.cx - p.rib_w / 2, y0, g.z_floor - JOIN, port.cx + p.rib_w / 2, y1,
                            g.z_pcb - p.rib_gap)
    sink = (p.csk_d - p.screw_clear_d) / 2      # a 90 degree countersink is as deep as wide
    for _ref, hx, hy in g.holes:
        tray = tray - S.cyl(hx, hy, g.z_bottom - 1.0, g.z_pcb + 1.0, p.screw_clear_d / 2)
        tray = tray - S.cyl(hx, hy, g.z_bottom - 0.5, g.z_bottom + sink,
                            p.csk_d / 2 + 0.5, p.screw_clear_d / 2)
    return tray - port_cutters(p, g)


def build_frame(p, g):
    body = shell(p, g, p.seam_gap, g.z_top, "top")
    cavity = S.box(g.xi0, g.yi0, -1.0, g.xi1, g.yi1, g.z_top + 1.0)
    frame = body - cavity
    flange = (S.box(g.xi0 - JOIN, g.yi0 - JOIN, g.z_top - p.flange_t,
                    g.xi1 + JOIN, g.yi1 + JOIN, g.z_top)
              - S.box(g.bx0 + p.lid_overlap, g.by0 + p.lid_overlap, g.z_top - p.flange_t - 1.0,
                      g.bx1 - p.lid_overlap, g.by1 - p.lid_overlap, g.z_top + 1.0))
    frame = frame + flange
    for _ref, hx, hy in g.holes:
        x0, y0, x1, y1 = corner(g, hx, hy, p.post_reach, JOIN)
        frame = frame + S.box(x0, y0, 0.0, x1, y1, g.z_top)

    cuts = []
    for b in g.buttons:
        front = b.y < g.midy
        c, k = list(b.col), list(b.block)
        c[1 if front else 3] += -JOIN if front else JOIN     # the column, into the wall
        k[1 if front else 3] += -JOIN if front else JOIN     # the light well, into the column
        # the column starts above the tallest part beside a button (btn_bottom); the light
        # well beside it comes down to the LEDs (ui_bottom)
        frame = frame + S.box(c[0], c[1], p.btn_bottom, c[2], c[3], g.z_top)
        frame = frame + S.box(k[0], k[1], p.ui_bottom, k[2], k[3], g.z_top)
        cuts.append(S.cyl(b.x, b.y, p.ui_bottom - 1.0, g.z_top + 1.0, p.btn_bore_d / 2))
        z_cb = g.z_top - p.btn_cbore_depth
        cone = (p.btn_cbore_d - p.btn_bore_d) / 2
        cuts.append(S.cyl(b.x, b.y, z_cb, g.z_top + 1.0, p.btn_cbore_d / 2))
        cuts.append(S.cyl(b.x, b.y, z_cb - cone, z_cb, p.btn_bore_d / 2, p.btn_cbore_d / 2))
        cuts.append(S.box(b.well[0], b.well[1], p.ui_bottom - 1.0, b.well[2], b.well[3],
                          g.z_top + 1.0))
    for h in g.pinholes:
        k = list(h.block)
        k[3 if h.y > g.midy else 1] += JOIN if h.y > g.midy else -JOIN          # into the wall
        frame = frame + S.box(k[0], k[1], p.ui_bottom, k[2], k[3], g.z_top)
        cuts.append(S.cyl(h.x, h.y, p.ui_bottom - 1.0, g.z_top + 1.0, p.boot_bore_d / 2))

    # the chamfer that clears the tray's ridge by lip_clear, measured horizontally; a ring,
    # so that it takes the walls' inner edge and leaves the posts' feet
    apex = p.lip_h + p.lip_top + p.lip_clear
    chamfer = S.offset_prism(g.xi0, g.yi0, g.xi1, g.yi1,
                             [(p.seam_gap - 0.5, apex - p.seam_gap + 0.5), (apex, 0.0)]) - cavity
    # nothing of the frame within lip_clear of the ridge's inner face, up to lip_clear above it
    relief = (S.box(g.xi0, g.yi0, -1.0, g.xi1, g.yi1, p.lip_h + p.lip_clear)
              - S.box(g.xi0 + p.lip_clear, g.yi0 + p.lip_clear, -2.0,
                      g.xi1 - p.lip_clear, g.yi1 - p.lip_clear, p.lip_h + p.lip_clear + 1.0))
    frame = frame - chamfer - relief
    r = p.insert_hole_d / 2
    for _ref, hx, hy in g.holes:
        cuts.append(S.cyl(hx, hy, -1.0, p.insert_hole_depth, r))                 # the foot
        z_blind = g.z_top - p.insert_hole_depth                                  # the top:
        cuts.append(S.cyl(hx, hy, z_blind, g.z_top + 1.0, r))                    # its blind end
        cuts.append(S.cyl(hx, hy, z_blind - r, z_blind, 0.0, r))                 # is a 45 degree cone
    return frame - S.union(cuts) - port_cutters(p, g)


def build_plunger(p, g, b):
    r_cap = p.plunger_cap_d / 2
    z_cone = g.z_collar_top - g.cone_h
    hull = S.Manifold.batch_hull
    return S.union([
        S.cyl(b.x, b.y, b.h, g.z_collar + 0.2, p.plunger_d / 2),                 # the shaft
        hull([S.cyl(b.x, b.y, g.z_collar, z_cone, p.plunger_collar_d / 2),       # the collar
              S.cyl(b.x, b.y, z_cone, g.z_collar_top, p.plunger_collar_d / 2, r_cap)]),
        hull([S.cyl(b.x, b.y, g.z_collar_top - 0.2, g.z_cap - p.plunger_chamfer, r_cap),  # the cap
              S.cyl(b.x, b.y, g.z_cap - p.plunger_chamfer, g.z_cap, r_cap,
                    r_cap - p.plunger_chamfer)]),
    ])


def lid_interface(p, g, board):
    holes = [{"ref": ref, "kind": "screw", "x": hx, "y": hy, "d": p.lid_screw_d,
              "keepout_d": p.lid_head_keepout_d} for ref, hx, hy in g.holes]
    holes += [{"ref": b.ref, "kind": "button", "x": b.x, "y": b.y, "d": p.lid_btn_d}
              for b in g.buttons]
    holes += [{"ref": h.ref, "kind": "pinhole", "x": h.x, "y": h.y, "d": p.lid_boot_d}
              for h in g.pinholes]
    rnd = lambda v: [round(x, 4) for x in v]
    contact = [{"what": f"post {ref}", "rect": rnd(corner(g, hx, hy, p.post_reach))}
               for ref, hx, hy in g.holes]
    contact += [{"what": f"tower {b.ref}", "rect": rnd(b.col)} for b in g.buttons]
    contact += [{"what": f"light well {b.ref}", "rect": rnd(b.block)} for b in g.buttons]
    contact += [{"what": f"tube {h.ref}", "rect": rnd(h.block)} for h in g.pinholes]
    return {
        "schema": 1,
        "about": "Interface of the enclosure's lid PCB, written by "
                 "design/mechanical/scripts/make_enclosure.py. Do not edit.",
        "frame": "the board frame of board_interface_Rev0.6.json; the lid's outline is the "
                 "main board's, seen from above",
        "outline": {"x0": g.bx0, "y0": g.by0, "x1": g.bx1, "y1": g.by1},
        "thickness": p.lid_t,
        "underside_above_board": g.z_top,
        "holes": holes,
        "windows": [{"refs": b.leds, "rect": rnd(b.well),
                     "note": "no copper and no solder mask on either side: bare FR-4 passes "
                             "the LEDs' light"} for b in g.buttons],
        "ports": [{"ref": q.ref, "x": q.cx, "edge": q.edge} for q in g.ports],
        "frame_contact": {"edge_band": p.lid_overlap, "rects": contact},
    }


# ---- figures for the document ----------------------------------------------------------------
def derived(p, g, heights, board, volumes):
    tall_h, tall_ref = max((heights[spec.footprint_name(f)], f["ref"])
                           for f in board["footprints"])
    head_top = g.z_bottom + (p.csk_d - p.csk_head_d) / 2
    web = min(abs(q.y_floor - q.y_in) for q in g.ports)
    far, far_ref = max((min(math.hypot(board["by_ref"][q.ref]["x"] - hx,
                                       board["by_ref"][q.ref]["y"] - hy) for _r, hx, hy in g.holes),
                        q.ref) for q in g.ports)
    swd = min((min(c[0] - g.xi0, c[1] - g.yi0, g.xi1 - c[2], g.yi1 - c[3]), f["ref"])
              for f in board["footprints"] if spec.footprint_name(f).startswith("Tag-Connect")
              for c in [f["courtyard"]])
    return [
        ("outer_x", g.xo1 - g.xo0, "mm", "Outer width (along the port edges)."),
        ("outer_y", g.yo1 - g.yo0, "mm", "Outer depth (front to back)."),
        ("outer_z", g.z_lid - g.z_bottom, "mm", "Height, tray's underside to the lid's top face."),
        ("printed_z", g.z_top - g.z_bottom, "mm", "Height without the lid."),
        ("tray_z", p.lip_h - g.z_bottom, "mm", "The tray's print height."),
        ("frame_z", g.z_top, "mm", "The frame's print height."),
        ("lid_margin", g.bx0 - g.xo0, "mm", "Frame's top face left free around the lid."),
        ("web_t", web, "mm", "Web between an overmould pocket and the cavity."),
        ("face_inset", min(abs(q.y_out - q.y_face) for q in g.ports), "mm",
         "A receptacle's face inside the wall's outer face."),
        ("port_to_screw_max", far, "mm",
         f"The receptacle farthest from a screw ({far_ref}) to its nearest mounting hole."),
        ("swd_wall_clearance", swd[0], "mm",
         f"The SWD footprint's courtyard ({swd[1]}) to the nearest wall."),
        ("lid_clearance_min", p.cavity_h - tall_h, "mm",
         f"Tallest part ({tall_ref}, {tall_h:g} mm) to the lid's underside."),
        ("bottom_engagement", head_top + p.bottom_screw_len, "mm",
         "Bottom screw's thread above the board's top face, in the post's insert."),
        ("lid_engagement", p.lid_screw_len - p.lid_t, "mm",
         "Lid screw's thread below the lid, in the post's insert."),
        ("plunger_len", g.z_cap - g.buttons[0].h, "mm", "Plunger length."),
        ("tray_volume", volumes["Tray"] / 1000.0, "cm3", "Solid volume of the tray."),
        ("frame_volume", volumes["Frame"] / 1000.0, "cm3", "Solid volume of the frame."),
        ("plunger_volume", volumes["Plunger"] / 1000.0, "cm3", "Solid volume of one plunger."),
    ]


def derived_table(rows):
    out = ["| Name | Value | Unit | Meaning |", "|---|---:|---|---|"]
    for name, value, unit, meaning in rows:
        out.append(f"| `{name}` | {value:.2f} | {unit} | {meaning} |")
    return "\n".join(out) + "\n"


# ---- files -----------------------------------------------------------------------------------
def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=pathlib.Path, default=spec.ASSEMBLY)
    ap.add_argument("--set", action="append", default=[], metavar="k=v")
    ap.add_argument("--derived", action="store_true")
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args()

    params, heights = spec.load_doc()
    overrides = {}
    for item in args.set:
        k, _, v = item.partition("=")
        if k not in params:
            print(f"FAIL: no parameter {k!r} in the document")
            return 1
        overrides[k] = float(v)
    digest = spec.inputs_digest(params, heights)
    p = SimpleNamespace(**{**params, **overrides})
    board = spec.load_interface()
    missing = sorted({spec.footprint_name(f) for f in board["footprints"]} - set(heights))
    if missing:
        print(f"FAIL: no height in the document for {missing}")
        return 1
    g = geometry(p, heights, board)

    solids = {"Tray": build_tray(p, g), "Frame": build_frame(p, g),
              "Plunger": build_plunger(p, g, g.buttons[0])}
    back = {  # print frame -> assembly frame
        "Tray": [[[1, 0, 0, g.xo0], [0, 1, 0, g.yo0], [0, 0, 1, g.z_bottom]]],
        "Frame": [[[1, 0, 0, g.xo0], [0, -1, 0, g.yo1], [0, 0, -1, g.z_top]]],
        "Plunger": [[[1, 0, 0, b.x], [0, -1, 0, b.y], [0, 0, -1, g.z_cap]] for b in g.buttons],
    }
    how = {"Tray": "as modelled, the floor on the bed",
           "Frame": "turned over, its top face on the bed",
           "Plunger": "turned over, the cap on the bed"}

    args.out.mkdir(parents=True, exist_ok=True)
    pieces, volumes = [], {}
    for name, man in solids.items():
        if man.status() != S.manifold3d.Error.NoError or man.volume() <= 0:
            print(f"FAIL: {name} is not a solid ({man.status()})")
            return 1
        volumes[name] = man.volume()
        tri = S.apply(S.triangles(man), S.inverse(back[name][0]))
        data = S.stl_bytes(tri, f"UsbPowerHub Enclosure Rev0.2 {name}")
        file = f"{spec.PREFIX}{name}.stl"
        (args.out / file).write_bytes(data)
        lo, hi = tri.reshape(-1, 3).min(axis=0), tri.reshape(-1, 3).max(axis=0)
        pieces.append({
            "name": name, "file": file, "sha256": sha256(data), "triangles": int(len(tri)),
            "volume_mm3": round(volumes[name], 2),
            "print_size": [round(float(v), 3) for v in hi - lo],
            "print": how[name], "quantity": len(back[name]),
            "to_assembly": back[name],
        })
        print(f"{file}: {len(tri)} triangles, {volumes[name] / 1000:.1f} cm3, "
              f"prints {hi[0] - lo[0]:.1f} x {hi[1] - lo[1]:.1f} x {hi[2] - lo[2]:.1f} mm")

    lid_text = json.dumps(lid_interface(p, g, board), indent=1, ensure_ascii=True) + "\n"
    lid_file = f"{spec.PREFIX}LidInterface.json"
    (args.out / lid_file).write_bytes(lid_text.encode("ascii"))

    rows = derived(p, g, heights, board, volumes)
    manifest = {
        "schema": 1,
        "about": "Enclosure Rev0.2, written by design/mechanical/scripts/make_enclosure.py. "
                 "Do not edit.",
        "state": "WIP",
        "revision": "Rev0.2",
        "document": {"path": "design/mechanical/ENCLOSURE_Rev0.2.md", "inputs_sha256": digest},
        "overrides": overrides,
        "board_interface": {
            "path": "design/mechanical/reference/board_interface_Rev0.6.json",
            "sha256": sha256(spec.INTERFACE.read_bytes()),
            "board_sha256": board["source"]["sha256"],
        },
        "frame": "assembly frame: the board frame, z = 0 at the board's top face, z up, mm; "
                 "a piece's to_assembly rows are [r00 r01 r02 t] applied to its STL coordinates",
        "pieces": pieces,
        "lid_interface": {"file": lid_file, "sha256": sha256(lid_text.encode("ascii"))},
        "derived": {name: round(value, 4) for name, value, _u, _m in rows},
        "tools": {"python": sys.version.split()[0], "numpy": np.__version__,
                  "manifold3d": importlib.metadata.version("manifold3d")},
    }
    (args.out / spec.MANIFEST).write_bytes(
        (json.dumps(manifest, indent=1, ensure_ascii=True) + "\n").encode("ascii"))
    print(f"wrote {len(pieces)} STL files, {lid_file} and the manifest to {args.out}")

    if args.derived:
        if overrides:
            print("FAIL: --derived with --set would write an override into the document")
            return 1
        spec.write_derived(derived_table(rows))
        print("rewrote the document's derived-figures table")
    if args.no_check:
        return 0
    sys.stdout.flush()                                     # keep this output ahead of theirs
    python = [sys.executable, "-I", "-B"]
    if args.out.resolve() == spec.ASSEMBLY.resolve():      # the repository's build: its pictures
        rc = subprocess.run(python + [str(HERE / "render_enclosure.py")]).returncode
        if rc:
            return rc
    return subprocess.run(python + [str(HERE / "check_enclosure.py"),
                                    "--dir", str(args.out)]).returncode


if __name__ == "__main__":
    sys.exit(main())
