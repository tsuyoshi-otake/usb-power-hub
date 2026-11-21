"""Draw the enclosure from its STL files: assembled, open, exploded, back, front, the cover.

Run with the CAD venv's Python, from the repository root:

    ~/tmp/cadvenv/Scripts/python.exe -I -B design/mechanical/scripts/render_enclosure.py

It reads   the manifest, the STL files and the lid interface in design/mechanical/assembly,
           the board interface and the document's tables
and writes design/mechanical/reports/UsbPowerHub_Enclosure_Rev0.4_<View>.png

The pictures are for looking at and prove nothing. Each carries, in a PNG text chunk, the
SHA-256 of the manifest it was drawn from; the checker reads that and nothing else of a
picture (E16), so a picture of an older build is found.
What is drawn and is not a file: the board's parts (their courtyards, drawn 0.25 mm
smaller, raised to the document's heights), the lid (a plate with the lid interface's
holes; its legend does not exist yet) and the lid's screw heads.

  --dir DIR   read the pieces from there       --out DIR   write the pictures there
"""
import argparse
import importlib.util
import json
import pathlib
import struct
import sys
import zlib
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

PRINTED = (196, 200, 206)
PLUNGER = (236, 150, 48)
COVER = (150, 158, 170)
BOARD = (30, 108, 70)
LID = (26, 78, 58)
WINDOW = (214, 200, 120)
STEEL = (176, 178, 184)
BODY = (58, 60, 66)
COLOURS = {"Fuse_": (222, 176, 40), "Converter_": (34, 34, 38), "DIP-": (40, 40, 44),
           "USB_C_": STEEL, "SW_Push": (150, 152, 158), "R_Shunt": (120, 96, 70),
           "Crystal": STEEL, "D_SMB": (40, 40, 44)}


class Scene:
    def __init__(self):
        self.tri, self.col, self.obj, self.n = [], [], [], 0

    def add(self, tri, colour, dz=0.0, dy=0.0):
        tri = np.asarray(tri, dtype=np.float64) + np.array([0.0, dy, dz])
        self.tri.append(tri)
        self.col.append(np.tile(np.array(colour, dtype=np.float64), (len(tri), 1)))
        self.obj.append(np.full(len(tri), self.n))
        self.n += 1

    def solid(self, man, colour, dz=0.0):
        self.add(S.triangles(man), colour, dz)


def render(scene, az, el, width, height, ss=2, margin=40):
    tri = np.concatenate(scene.tri)
    col = np.concatenate(scene.col)
    obj = np.concatenate(scene.obj)
    a, e = np.radians(az), np.radians(el)
    to_cam = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    fwd = -to_cam
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    ln = np.linalg.norm(n, axis=1, keepdims=True)
    n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 0)
    keep = (n @ to_cam > 1e-9) & (ln[:, 0] > 0)
    tri, col, obj, n = tri[keep], col[keep], obj[keep], n[keep]

    w, h = width * ss, height * ss
    px, py, pz = tri @ right, tri @ up, tri @ fwd
    scale = min((w - 2 * margin * ss) / (px.max() - px.min()),
                (h - 2 * margin * ss) / (py.max() - py.min()))
    sx = (px - (px.max() + px.min()) / 2) * scale + w / 2
    sy = h / 2 - (py - (py.max() + py.min()) / 2) * scale

    zbuf = np.full((h, w), np.inf)
    fid = np.full((h, w), -1, dtype=np.int64)
    for i in range(len(tri)):
        x0, x1, x2 = sx[i]
        y0, y1, y2 = sy[i]
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-12:
            continue
        ax, bx = max(int(np.floor(min(x0, x1, x2))), 0), min(int(np.ceil(max(x0, x1, x2))), w - 1)
        ay, by = max(int(np.floor(min(y0, y1, y2))), 0), min(int(np.ceil(max(y0, y1, y2))), h - 1)
        if ax > bx or ay > by:
            continue
        gx = (np.arange(ax, bx + 1) + 0.5)[None, :]
        gy = (np.arange(ay, by + 1) + 0.5)[:, None]
        la = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / det
        lb = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / det
        lc = 1.0 - la - lb
        z = la * pz[i, 0] + lb * pz[i, 1] + lc * pz[i, 2]
        sub = zbuf[ay:by + 1, ax:bx + 1]
        hit = (la >= -1e-9) & (lb >= -1e-9) & (lc >= -1e-9) & (z < sub)
        if hit.any():
            sub[hit] = z[hit]
            fid[ay:by + 1, ax:bx + 1][hit] = i

    key = np.array([-0.35, -0.55, 0.76])
    key /= np.linalg.norm(key)
    fill = np.array([0.8, 0.3, 0.5])
    fill /= np.linalg.norm(fill)
    shade = 0.36 + 0.52 * np.clip(n @ key, 0, 1) + 0.16 * np.clip(n @ fill, 0, 1)
    lit = np.clip(col * shade[:, None], 0, 255)
    bg = fid < 0
    img = np.where(bg[..., None], np.array([247.0, 247.0, 245.0]), lit[fid])
    nb = np.where(bg[..., None], 0.0, n[fid])
    ob = np.where(bg, -1, obj[fid])
    zb = np.where(bg, 1e9, zbuf)
    edge = np.zeros((h, w), dtype=bool)
    for sl_a, sl_b in (((slice(None), slice(1, None)), (slice(None), slice(None, -1))),
                       ((slice(1, None), slice(None)), (slice(None, -1), slice(None)))):
        both = (ob[sl_a] >= 0) & (ob[sl_b] >= 0)
        d = ((ob[sl_a] != ob[sl_b])
             | (both & ((nb[sl_a] * nb[sl_b]).sum(-1) < 0.8))
             | (both & (np.abs(zb[sl_a] - zb[sl_b]) > 1.2)))
        edge[sl_a] |= d
        edge[sl_b] |= d
    img[edge] *= 0.28
    img = img.reshape(height, ss, width, ss, 3).mean(axis=(1, 3))
    return np.clip(img + 0.5, 0, 255).astype(np.uint8)


def write_png(path, rgb, source):
    """An 8-bit RGB PNG with `source` in a text chunk named Source."""
    h, w, _ = rgb.shape
    raw = np.hstack([np.zeros((h, 1), dtype=np.uint8), rgb.reshape(h, w * 3)]).tobytes()

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    pathlib.Path(path).write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"tEXt", b"Source\x00" + source.encode("latin-1"))
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def load(directory):
    params, heights = spec.load_doc()
    board = spec.load_interface()
    directory = pathlib.Path(directory)
    manifest = json.loads((directory / spec.MANIFEST).read_text(encoding="ascii"))
    lid = json.loads((directory / manifest["lid_interface"]["file"]).read_text(encoding="ascii"))
    pieces = {}
    for piece in manifest["pieces"]:
        tri = S.read_stl(directory / piece["file"])
        pieces[piece["name"]] = [S.apply(tri, m) for m in piece["to_assembly"]]
    return SimpleNamespace(p=SimpleNamespace(**params), heights=heights, board=board, lid=lid,
                           pieces=pieces)


def colour_of(name):
    for prefix, colour in COLOURS.items():
        if name.startswith(prefix):
            return colour
    return BODY


def add_board(scene, d, dz):
    o, t = d.board["outline"], d.board["thickness"]
    scene.solid(S.box(o["x0"], o["y0"], -t, o["x1"], o["y1"], 0.0), BOARD, dz)
    led = 0
    for fp in d.board["footprints"]:
        name = spec.footprint_name(fp)
        h = d.heights[name]
        if h <= 0:
            continue
        x0, y0, x1, y1 = fp["courtyard"]
        colour = colour_of(name)
        if name.startswith("USB_C_"):                      # the shell, not the courtyard
            x0, x1 = fp["x"] - d.p.usb_shell_w / 2, fp["x"] + d.p.usb_shell_w / 2
            y0, y1 = fp["y"] - d.p.usb_shell_len / 2, fp["y"] + d.p.usb_shell_len / 2
        else:
            x0, y0, x1, y1 = x0 + 0.25, y0 + 0.25, x1 - 0.25, y1 - 0.25
        if name.startswith("LED_"):
            colour = (60, 190, 90) if led % 2 == 0 else (214, 60, 50)
            led += 1
        scene.solid(S.box(x0, y0, 0.0, x1, y1, h), colour, dz)


def add_lid(scene, d, dz, screws=True):
    o, t, z = d.lid["outline"], d.lid["thickness"], d.lid["underside_above_board"]
    plate = S.box(o["x0"], o["y0"], z, o["x1"], o["y1"], z + t)
    for hole in d.lid["holes"]:
        plate = plate - S.cyl(hole["x"], hole["y"], z - 1.0, z + t + 1.0, hole["d"] / 2)
    scene.solid(plate, LID, dz)
    for win in d.lid["windows"]:
        x0, y0, x1, y1 = win["rect"]
        scene.solid(S.box(x0, y0, z + t, x1, y1, z + t + 0.03), WINDOW, dz)
    if screws:
        for hole in d.lid["holes"]:
            if hole["kind"] == "screw":
                scene.solid(S.cyl(hole["x"], hole["y"], z + t, z + t + 1.3, 1.9, 1.5), STEEL, dz)


def views(d):
    def assembled():
        s = Scene()
        s.add(d.pieces["Tray"][0], PRINTED)
        s.add(d.pieces["Frame"][0], PRINTED)
        s.add(d.pieces["Cover"][0], COVER)
        add_board(s, d, 0.0)
        for tri in d.pieces["Plunger"]:
            s.add(tri, PLUNGER)
        add_lid(s, d, 0.0)
        return s

    def opened():
        s = Scene()
        s.add(d.pieces["Tray"][0], PRINTED)
        s.add(d.pieces["Frame"][0], PRINTED)
        s.add(d.pieces["Cover"][0], COVER)
        add_board(s, d, 0.0)
        for tri in d.pieces["Plunger"]:
            s.add(tri, PLUNGER)
        return s

    def exploded():
        s = Scene()
        s.add(d.pieces["Tray"][0], PRINTED)
        s.add(d.pieces["Cover"][0], COVER, dy=16.0)      # drawn out of the back wall
        add_board(s, d, 16.0)
        s.add(d.pieces["Frame"][0], PRINTED, 44.0)
        for tri in d.pieces["Plunger"]:
            s.add(tri, PLUNGER, 60.0)
        add_lid(s, d, 72.0)
        return s

    def tray_and_board():
        s = Scene()
        s.add(d.pieces["Tray"][0], PRINTED)
        add_board(s, d, 0.0)
        return s

    def frame_below():
        s = Scene()
        s.add(d.pieces["Frame"][0], PRINTED)
        return s

    def cover_alone():
        s = Scene()
        s.add(d.pieces["Cover"][0], COVER)
        return s

    def cover_drawn():
        s = Scene()
        s.add(d.pieces["Tray"][0], PRINTED)
        s.add(d.pieces["Frame"][0], PRINTED)
        s.add(d.pieces["Cover"][0], COVER, dy=12.0)      # drawn out, as it goes in
        add_board(s, d, 0.0)
        return s

    return [
        ("Assembled", assembled(), -62, 32, 1500, 950),
        ("Back", assembled(), 118, 32, 1500, 950),
        ("Open", opened(), -62, 52, 1500, 1050),
        ("Exploded", exploded(), -62, 20, 1300, 1500),
        ("Front", assembled(), -90, 8, 1600, 560),
        ("TrayBoard", tray_and_board(), -62, 42, 1500, 1000),
        ("FrameUnderside", frame_below(), -62, -38, 1500, 950),
        ("BackUnderside", assembled(), 118, -32, 1500, 950),
        ("CoverDrawn", cover_drawn(), 118, 32, 1500, 950),
        ("Cover", cover_alone(), -118, 28, 1100, 900),
        ("CoverUnderside", cover_alone(), 62, -42, 1100, 900),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", type=pathlib.Path, default=spec.ASSEMBLY)
    ap.add_argument("--out", type=pathlib.Path, default=spec.REPORTS)
    args = ap.parse_args()
    d = load(args.dir)
    source = spec.source_tag(args.dir / spec.MANIFEST)
    args.out.mkdir(parents=True, exist_ok=True)
    for name, scene, az, el, w, h in views(d):
        path = args.out / f"{spec.PREFIX}{name}.png"
        write_png(path, render(scene, az, el, w, h), source)
        print(f"wrote {path.name} ({w} x {h})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
