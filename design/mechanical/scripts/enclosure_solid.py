"""Solids and STL files for the enclosure scripts (manifold3d + numpy).

Shared by make_enclosure.py (which builds the pieces), check_enclosure.py (which builds
only probes with it, and reads the pieces back from their STL files) and
render_enclosure.py. Nothing here knows the enclosure's design.
"""
import pathlib
import struct

import manifold3d
import numpy as np
from manifold3d import Manifold

SEG = 64  # segments of a full circle
STL_DTYPE = np.dtype([("n", "<f4", (3,)), ("v", "<f4", (3, 3)), ("a", "<u2")])


def box(x0, y0, z0, x1, y1, z1):
    if not (x1 > x0 and y1 > y0 and z1 > z0):
        raise ValueError(f"empty box {(x0, y0, z0, x1, y1, z1)}")
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def cyl(x, y, z0, z1, r0, r1=None):
    """A cylinder or cone on a vertical axis; r0 at z0, r1 at z1 (either may be 0)."""
    r1 = r0 if r1 is None else r1
    if not z1 > z0:
        raise ValueError(f"empty cylinder z {z0} .. {z1}")
    if r0 <= 0:  # the point is at the bottom: build it upside down and mirror it
        return Manifold.cylinder(z1 - z0, r1, 0.0, SEG).mirror([0, 0, 1]).translate([x, y, z1])
    return Manifold.cylinder(z1 - z0, r0, r1, SEG).translate([x, y, z0])


def offset_prism(x0, y0, x1, y1, levels):
    """The hull of the rectangle offset outwards by r at each level (z, r), corners rounded.

    An offset with round corners stays at r from the rectangle all the way round, where a
    mitred one stands r * sqrt(2) from each corner.
    """
    ang = np.linspace(0.0, 2 * np.pi, SEG, endpoint=False)
    pts = []
    for z, r in levels:
        for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            if r > 0:
                pts += [(cx + r * np.cos(a), cy + r * np.sin(a), z) for a in ang]
            else:
                pts.append((cx, cy, z))
    return Manifold.hull_points(np.array(pts, dtype=np.float64))


def slot_y(cx, cz, w, h, r, ya, yb):
    """A rounded rectangle w x h (corner radius r) in x-z, centred (cx, cz), from y = ya to yb."""
    parts = []
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = Manifold.cylinder(yb - ya, r, r, SEG).rotate([-90.0, 0.0, 0.0])  # z -> +y
            parts.append(c.translate([cx + sx * (w / 2 - r), ya, cz + sz * (h / 2 - r)]))
    return Manifold.batch_hull(parts)


def hull(points):
    """The convex hull of points (x, y, z)."""
    return Manifold.hull_points(np.array(list(points), dtype=np.float64))


def union(parts):
    out = Manifold()
    for part in parts:
        out = out + part
    return out


def triangles(man):
    """(n, 3, 3) float64 corner coordinates of a manifold's triangles."""
    mesh = man.to_mesh()
    v = np.asarray(mesh.vert_properties, dtype=np.float64)[:, :3]
    f = np.asarray(mesh.tri_verts, dtype=np.int64)
    return v[f]


def apply(tri, m34):
    """Apply a 3 x 4 affine matrix (rotation or mirror | translation) to (n, 3, 3) corners."""
    m = np.asarray(m34, dtype=np.float64)
    out = tri @ m[:, :3].T + m[:, 3]
    if np.linalg.det(m[:, :3]) < 0:
        out = out[:, ::-1, :]
    return out


def inverse(m34):
    m = np.asarray(m34, dtype=np.float64)
    r = np.linalg.inv(m[:, :3])
    return np.hstack([r, (-r @ m[:, 3])[:, None]])


def _lex_less(a, b):
    return ((a[:, 0] < b[:, 0])
            | ((a[:, 0] == b[:, 0]) & ((a[:, 1] < b[:, 1])
                                       | ((a[:, 1] == b[:, 1]) & (a[:, 2] < b[:, 2])))))


def canonical(tri32):
    """Start each triangle at its smallest corner and sort the triangles: one byte order."""
    n = len(tri32)
    rows = np.arange(n)
    first = np.zeros(n, dtype=np.int64)
    first[_lex_less(tri32[:, 1], tri32[:, 0])] = 1
    first[_lex_less(tri32[:, 2], tri32[rows, first])] = 2
    tri32 = tri32[rows[:, None], (first[:, None] + np.arange(3)[None, :]) % 3]
    order = np.lexsort(tri32.reshape(n, 9).T[::-1])
    return tri32[order]


def stl_bytes(tri, name):
    tri32 = canonical(np.asarray(tri, dtype=np.float32))
    t = tri32.astype(np.float64)
    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = np.divide(nrm, ln, out=np.zeros_like(nrm), where=ln > 0)
    rec = np.zeros(len(tri32), dtype=STL_DTYPE)
    rec["n"] = nrm.astype(np.float32)
    rec["v"] = tri32
    header = name.encode("ascii")[:80].ljust(80, b" ")
    return header + struct.pack("<I", len(rec)) + rec.tobytes()


def read_stl(path):
    """(n, 3, 3) float64 corners of a binary STL file."""
    raw = pathlib.Path(path).read_bytes()
    if len(raw) < 84:
        raise ValueError(f"{path}: not a binary STL file")
    n = struct.unpack_from("<I", raw, 80)[0]
    if len(raw) != 84 + 50 * n:
        raise ValueError(f"{path}: {len(raw)} bytes, want {84 + 50 * n} for {n} triangles")
    return np.frombuffer(raw, dtype=STL_DTYPE, count=n, offset=84)["v"].astype(np.float64)


def weld(tri):
    """Vertices and faces of a triangle soup whose shared corners are bit-identical."""
    verts, inv = np.unique(tri.reshape(-1, 3), axis=0, return_inverse=True)
    return verts, np.asarray(inv).reshape(-1, 3)


def to_manifold(tri):
    verts, faces = weld(np.asarray(tri, dtype=np.float32).astype(np.float64))
    mesh = manifold3d.Mesh(vert_properties=verts.astype(np.float32),
                           tri_verts=faces.astype(np.uint32))
    return Manifold(mesh)


def bbox(man):
    b = man.bounding_box()
    return [float(v) for v in b]
