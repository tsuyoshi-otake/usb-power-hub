"""Check the project libraries against the parts register's datasheet facts (CLAUDE.md 4.2, 8).

Run with KiCad's own Python from the repository root (make_libraries.py runs it after it
writes the libraries):

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_libraries.py [LIBDIR [SRCDIR]]

LIBDIR holds library.json, usb-power-hub.kicad_sym and usb-power-hub.pretty/ (default
design/ecad/libraries). SRCDIR holds the KiCad project and its library tables (default
design/ecad/source). The checker reads the register's `land` and `pins` (what the datasheets
say) and never the generator's `params`, and it measures footprints as KiCad loads them.

 1. Register: ids unique; the fields the checks use are present.
 2. Symbols: exactly one flattened symbol per register id. Its pin numbers are the register's;
    each pin name is the datasheet's, compared without case and punctuation, or, where the
    register gives a [datasheet, symbol] pair, exactly the symbol spelling. Value, Footprint,
    Datasheet, MPN, LCSC or Akizuki code, Class, in_bom and the designator letters are the
    register's.
 3. Footprints: exactly one file per footprint the register names (a schematic-only symbol,
    footprint `none`, names none and must have an empty Footprint). A stock one is a
    byte-for-byte copy of KiCad's once KiCad's CRLF is read as LF; every one loads in pcbnew; its numbered pads are its
    symbol's pins; its courtyard contains every pad (and, if generated, its F.Fab outline).
    Then a land check per `land.kind`:
    - qfn_land: each pad's inner and outer edge, width and centre are the datasheet land's.
    - qfn, dual, sot23, sot223, chip: coverage. Each pad contains the nominal terminal
      (nominal body, nominal lead length and width, nominal pitch) and its outer edge reaches
      the maximum tip. Pin order is checked as part of it. This is not IPC-7351 fillet
      compliance; it proves the lead lands on its own pad and nowhere else.
    - kelvin_chip: every force and sense pad covers its end's nominal electrode length and
      overlaps its width; the two sense pads leave on one side.
    - pads: exact pad numbers, centres, sizes, mask openings and unplated holes.
    - holes: exact hole positions and numbers, drill inside the datasheet range, annular ring.
    - Kelvin parts: sense pads are joined to their force pads either by the part's electrode
      (no copper, no net tie) or by copper strips inside a KiCad net tie whose groups are
      exactly the force / sense pairs; no strip touches another pad.
    - The USB-C module's courtyard is the OI-23 study's obstacle rectangles, read from the
      study, in the frame where pad 1 sits on the 1 x 7 row's VBUS pin.
 4. Library tables: SRCDIR's fp-lib-table and sym-lib-table name only this library and
    resolve to LIBDIR. No file in LIBDIR, and neither table, holds a CR byte: the repository
    stores LF, so these are the bytes a checkout holds.
 5. kicad-cli exports every symbol and every footprint to SVG (it parses them).
 6. DRC: every footprint is placed on a scratch copy of the project board (its rules, its
    stackup; a larger outline), each pad number on its own net, and `kicad-cli pcb drc` must
    report no violation. Unconnected items are expected (a switch has two pads per pin) and
    are not counted.
Exit status: 0 = every check passed; 1 = at least one failed; each failure prints as
`FAIL <part>: <what>`. NOTE lines list register facts that rest on a proxy or an assumption.

What it CANNOT see:
- whether a datasheet fact in the register was read correctly. The register cites page and
  revision for each one; that citation is the evidence, and a reviewer reads it.
- IPC fillet sizes, paste reduction, or whether a land solders well. Only the coverage rule.
- the generic R and C lands. Their per-value datasheets are bound at P2.
- 3D models; part heights (the strip under a USB-C module is 2D here).
- whether a pin's electrical type suits ERC (P2's ERC sees that).
- the JLCPCB CPL rotation frame (CLAUDE.md 4.2; P5) and the package's pin-1 marking where the
  datasheet prints no pin numbers (AO3401A, AO3400A; see their register notes).
"""
import importlib.util
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
KICAD = pathlib.Path(sys.executable).resolve().parents[1]
KFP = KICAD / "share" / "kicad" / "footprints"
CLI = KICAD / "bin" / "kicad-cli.exe"
TOL = 0.002          # mm: the files carry 4 decimals; pcbnew rounds to 1 nm
MIN_SENSE_OVERLAP = 0.3   # mm of a sense pad across its electrode's width


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")


class Report:
    def __init__(self):
        self.fails, self.notes, self.count = [], [], 0

    def check(self, cond, who, what):
        self.count += 1
        if not cond:
            self.fails.append(f"FAIL {who}: {what}")
        return cond

    def note(self, who, what):
        self.notes.append(f"NOTE {who}: {what}")


def mid(pair):
    return (pair[0] + pair[1]) / 2


def norm(name):
    return re.sub(r"[^A-Z0-9]", "", name.upper())


# ---- footprint measurement (pcbnew) ----------------------------------------------------------
ATTR = {pcbnew.PAD_ATTRIB_PTH: "pth", pcbnew.PAD_ATTRIB_SMD: "smd",
        pcbnew.PAD_ATTRIB_CONN: "conn", pcbnew.PAD_ATTRIB_NPTH: "npth"}


class Pad:
    def __init__(self, p):
        self.num = p.GetNumber()
        self.attr = ATTR[p.GetAttribute()]
        self.circle = p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE
        pos = p.GetPosition()
        self.x, self.y = pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)
        size = p.GetSize(pcbnew.F_Cu)
        w, h = pcbnew.ToMM(size.x), pcbnew.ToMM(size.y)
        rot = round(p.GetOrientationDegrees()) % 180
        self.rotated_badly = rot not in (0, 90)
        self.w, self.h = (h, w) if rot == 90 else (w, h)
        self.drill = pcbnew.ToMM(p.GetDrillSize().x)
        self.paste = p.IsOnLayer(pcbnew.F_Paste)
        self.copper = p.IsOnLayer(pcbnew.F_Cu)
        m = p.GetLocalSolderMaskMargin()
        self.mask_margin = None if m is None else pcbnew.ToMM(m)

    @property
    def box(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2)

    def contains_point(self, x, y):
        if self.circle:
            return math.hypot(x - self.x, y - self.y) <= self.w / 2 + TOL
        x0, y0, x1, y1 = self.box
        return x0 - TOL <= x <= x1 + TOL and y0 - TOL <= y <= y1 + TOL

    def __repr__(self):
        return f"pad {self.num!r} at ({self.x:.4f}, {self.y:.4f}) {self.w:.4f} x {self.h:.4f}"


def shapes(fp, layer):
    out = []
    for g in fp.GraphicalItems():
        if g.GetClass() == "PCB_SHAPE" and g.GetLayer() == layer:
            s, e = g.GetStart(), g.GetEnd()
            out.append((g.GetShapeStr(), pcbnew.ToMM(s.x), pcbnew.ToMM(s.y), pcbnew.ToMM(e.x),
                        pcbnew.ToMM(e.y), pcbnew.ToMM(g.GetWidth())))
    return out


def rects(fp, layer):
    return sorted((min(a, c), min(b, d), max(a, c), max(b, d))
                  for kind, a, b, c, d, _ in shapes(fp, layer) if kind == "Rect")


def same(a, b):
    return abs(a - b) <= TOL


def contains(outer, inner):
    """Rectangle `outer` (x0, y0, x1, y1) contains rectangle `inner`, to TOL."""
    return (outer[0] <= inner[0] + TOL and outer[1] <= inner[1] + TOL
            and outer[2] >= inner[2] - TOL and outer[3] >= inner[3] - TOL)


# ---- per-side frames -------------------------------------------------------------------------
# For a pad on a side of a package, u is the outward distance from the package centre and v
# runs along the side in pin-number order (counter-clockwise, top view, y down).
SIDES = {
    "left": lambda b: ((-b[2], -b[0]), (b[1], b[3])),
    "bottom": lambda b: ((b[1], b[3]), (b[0], b[2])),
    "right": lambda b: ((b[0], b[2]), (-b[3], -b[1])),
    "top": lambda b: ((-b[3], -b[1]), (-b[2], -b[0])),
}


def covers(rep, who, pad, side, u_term, v_term, u_reach):
    """The pad contains the terminal rectangle u_term x v_term and reaches u_reach outward."""
    (u0, u1), (v0, v1) = SIDES[side](pad.box)
    rep.check(u0 <= u_term[0] + TOL and u1 >= u_term[1] - TOL, who,
              f"{pad} does not cover the nominal lead length {u_term[0]:.3f}..{u_term[1]:.3f} "
              f"(pad {u0:.3f}..{u1:.3f} outward)")
    rep.check(v0 <= v_term[0] + TOL and v1 >= v_term[1] - TOL, who,
              f"{pad} does not cover the nominal lead width {v_term[0]:.3f}..{v_term[1]:.3f} "
              f"(pad {v0:.3f}..{v1:.3f} along the side)")
    rep.check(u1 >= u_reach - TOL, who,
              f"{pad} ends at {u1:.3f}, short of the maximum tip {u_reach:.3f}")


def numbered(pads):
    return [p for p in pads if p.num != ""]


def by_number(pads, num):
    return [p for p in pads if p.num == num]


# ---- land checks -----------------------------------------------------------------------------
def quad_side(k, n):
    return ("left", "bottom", "right", "top")[(k - 1) // n], (k - 1) % n


def land_qfn(rep, who, pads, land, exact):
    n, pitch = land["per_side"], land["pitch"]
    signal = [p for p in numbered(pads) if p.num != land["epad_number"]]
    rep.check(sorted(int(p.num) for p in signal) == list(range(1, 4 * n + 1)), who,
              f"signal pads are not 1..{4 * n}: {sorted(p.num for p in signal)}")
    for p in signal:
        side, i = quad_side(int(p.num), n)
        vc = (i - (n - 1) / 2) * pitch
        if exact:
            (u0, u1), (v0, v1) = SIDES[side](p.box)
            rep.check(same(u0, land["inner_span"] / 2) and same(u1, land["outer_span"] / 2), who,
                      f"{p}: edges {u0:.4f}..{u1:.4f} outward, land "
                      f"{land['inner_span'] / 2}..{land['outer_span'] / 2}")
            rep.check(same(v1 - v0, land["pad_width"]) and same((v0 + v1) / 2, vc), who,
                      f"{p}: width {v1 - v0:.4f} at {(v0 + v1) / 2:.4f} along the {side} side, "
                      f"land {land['pad_width']} at {vc:.4f}")
        else:
            body, lt, bw = mid(land["body"]), mid(land["terminal_length"]), mid(land["terminal_width"])
            covers(rep, who, p, side, (body / 2 - lt, body / 2), (vc - bw / 2, vc + bw / 2),
                   land["body"][1] / 2)
    if exact and "side_span" in land:
        for s in ("left", "bottom", "right", "top"):
            vs = [SIDES[s](p.box)[1] for p in signal if quad_side(int(p.num), n)[0] == s]
            span = max(v for _, v in vs) - min(v for v, _ in vs) if vs else 0
            rep.check(same(span, land["side_span"]), who,
                      f"pads along the {s} side span {span:.4f}, land {land['side_span']}")
    ep = by_number(pads, land["epad_number"])
    rep.check(len(ep) == 1, who, f"expected one ePad numbered {land['epad_number']!r}, found {len(ep)}")
    if ep:
        e = ep[0]
        lo, hi = (land["epad"], land["epad"]) if exact else land["epad"]
        rep.check(same(e.x, 0) and same(e.y, 0) and lo - TOL <= e.w <= hi + TOL
                  and lo - TOL <= e.h <= hi + TOL, who, f"ePad {e} is not centred within {lo}..{hi}")


def land_dual(rep, who, pads, land):
    n, pitch = land["per_side"], land["pitch"]
    tip, foot, lw = mid(land["tip_span"]), mid(land["foot"]), mid(land["lead_width"])
    nums = sorted(int(p.num) for p in numbered(pads))
    rep.check(nums == list(range(1, 2 * n + 1)), who, f"pads are not 1..{2 * n}: {nums}")
    for p in numbered(pads):
        k = int(p.num)
        side, i = ("left", k - 1) if k <= n else ("right", k - n - 1)
        vc = (i - (n - 1) / 2) * pitch
        covers(rep, who, p, side, (tip / 2 - foot, tip / 2), (vc - lw / 2, vc + lw / 2),
               land["tip_span"][1] / 2)


def land_sot23(rep, who, pads, land):
    tip, foot, lw, pitch = mid(land["tip_span"]), mid(land["foot"]), mid(land["lead_width"]), land["pitch"]
    rep.check(sorted(p.num for p in numbered(pads)) == ["1", "2", "3"], who, "pads are not 1, 2, 3")
    where = {"1": ("left", -pitch), "2": ("left", pitch), "3": ("right", 0.0)}
    for p in numbered(pads):
        if p.num in where:
            side, vc = where[p.num]
            covers(rep, who, p, side, (tip / 2 - foot, tip / 2), (vc - lw / 2, vc + lw / 2),
                   land["tip_span"][1] / 2)


def land_sot223(rep, who, pads, land):
    tip, foot, lw, pitch = mid(land["tip_span"]), mid(land["foot"]), mid(land["lead_width"]), land["pitch"]
    left = {p.num: p for p in pads if p.x < 0}
    tab = [p for p in pads if p.x > 0]
    rep.check(sorted(left) == ["1", "2", "3"] and len(tab) == 1, who,
              f"expected leads 1, 2, 3 on -x and one tab on +x, found {sorted(left)} and {len(tab)}")
    for num, vc in (("1", -pitch), ("2", 0.0), ("3", pitch)):
        if num in left:
            covers(rep, who, left[num], "left", (tip / 2 - foot, tip / 2), (vc - lw / 2, vc + lw / 2),
                   land["tip_span"][1] / 2)
    if tab:
        t = tab[0]
        tw = mid(land["tab_width"])
        rep.check(t.num == land["tab_number"], who, f"tab is numbered {t.num!r}, not {land['tab_number']!r}")
        covers(rep, who, t, "right", (tip / 2 - foot, tip / 2), (-tw / 2, tw / 2), land["tip_span"][1] / 2)


def end_pads(rep, who, pads, land):
    """The two terminal pads of a chip: `force` if given, else the two numbered pads."""
    nums = land.get("force") or sorted(p.num for p in numbered(pads))
    found = [by_number(pads, n) for n in nums]
    if not rep.check(len(nums) == 2 and all(len(f) == 1 for f in found), who,
                     f"expected one pad each for terminals {nums}"):
        return None
    a, b = sorted((f[0] for f in found), key=lambda p: p.x)
    return a, b


def land_chip(rep, who, pads, land):
    ends = end_pads(rep, who, pads, land)
    if not ends:
        return
    length, tl, tw = mid(land["length"]), mid(land["terminal_length"]), mid(land["terminal_width"])
    for p, side in zip(ends, ("left", "right")):
        covers(rep, who, p, side, (length / 2 - tl, length / 2), (-tw / 2, tw / 2), land["length"][1] / 2)
    lim = land.get("limits", {})
    a, b = ends
    if "pad_length_min" in lim:
        rep.check(min(a.w, b.w) >= lim["pad_length_min"] - TOL, who,
                  f"pad length {min(a.w, b.w):.3f} < {lim['pad_length_min']} (datasheet land)")
    if "gap_max" in lim:
        gap = b.box[0] - a.box[2]
        rep.check(gap <= lim["gap_max"] + TOL, who, f"pad gap {gap:.3f} > {lim['gap_max']} (datasheet land)")
    if "pad_width_min" in lim:
        rep.check(min(a.h, b.h) >= lim["pad_width_min"] - TOL, who,
                  f"pad width {min(a.h, b.h):.3f} < {lim['pad_width_min']} (datasheet land)")


def land_kelvin_chip(rep, who, pads, land):
    ends = end_pads(rep, who, pads, land)
    if not ends:
        return
    length, tl, tw = mid(land["length"]), mid(land["terminal_length"]), mid(land["terminal_width"])
    sense = {}
    for s_num, f_num in land["sense"].items():
        s = by_number(pads, s_num)
        if rep.check(len(s) == 1, who, f"expected one sense pad {s_num!r}"):
            sense[s_num] = (s[0], f_num)
    for p in list(ends) + [s for s, _ in sense.values()]:
        side = "left" if p.x < 0 else "right"
        (u0, u1), (v0, v1) = SIDES[side](p.box)
        rep.check(u0 <= length / 2 - tl + TOL and u1 >= length / 2 - TOL, who,
                  f"{p} does not cover the nominal electrode length {length / 2 - tl:.3f}..{length / 2:.3f}")
        rep.check(u1 >= land["length"][1] / 2 - TOL, who,
                  f"{p} ends at {u1:.3f}, short of the maximum body end {land['length'][1] / 2:.3f}")
        overlap = min(v1, tw / 2) - max(v0, -tw / 2)
        need = tw / 2 if p in ends else MIN_SENSE_OVERLAP
        rep.check(overlap >= need - TOL, who,
                  f"{p} overlaps the nominal electrode width by {overlap:.3f}, needs {need:.3f}")
    for s, f_num in sense.values():
        f = [p for p in ends if p.num == f_num]
        rep.check(bool(f) and (s.x < 0) == (f[0].x < 0), who, f"sense {s} is not at force pad {f_num}'s end")
    if len(sense) == 2:
        ys = [s.y for s, _ in sense.values()]
        rep.check((ys[0] < 0) == (ys[1] < 0), who, "the sense pads leave on opposite sides")


def expand_holes(spec):
    if isinstance(spec, list):
        return spec
    kind, n, pitch, row = spec.split(":")
    n, pitch, row = int(n), float(pitch), float(row)
    half = n // 2
    out = [{"n": str(i + 1), "at": [0.0, round(pitch * i, 4)]} for i in range(half)]
    out += [{"n": str(half + j + 1), "at": [row, round(pitch * (half - 1 - j), 4)]} for j in range(half)]
    assert kind == "dip"
    return out


def match_at(pads, at):
    return [p for p in pads if same(p.x, at[0]) and same(p.y, at[1])]


def land_holes(rep, who, pads, land, fp):
    holes = expand_holes(land.get("holes", []))
    pth = [p for p in pads if p.attr == "pth"]
    npth = [p for p in pads if p.attr == "npth"]
    rep.check(len(pth) == len(holes), who, f"{len(pth)} plated holes, the land has {len(holes)}")
    lo, hi = land.get("drill", [0, 99])
    for h in holes:
        m = match_at(pth, h["at"])
        if not rep.check(len(m) == 1, who, f"no plated hole {h['n']!r} at {h['at']}"):
            continue
        p = m[0]
        rep.check(p.num == h["n"], who, f"hole at {h['at']} is numbered {p.num!r}, not {h['n']!r}")
        rep.check(lo - TOL <= p.drill <= hi + TOL, who, f"{p}: drill {p.drill} outside {lo}..{hi} ({land.get('lead')})")
        ring = (min(p.w, p.h) - p.drill) / 2
        rep.check(ring >= land.get("ring_min", 0) - TOL, who, f"{p}: annular ring {ring:.3f} < {land['ring_min']}")
    land_npth(rep, who, npth, land.get("npth", []))
    body = land.get("body")
    if body:
        one = match_at(pth, [0.0, 0.0])
        fab = rects(fp, pcbnew.F_Fab)
        ok = any(same(x1 - x0, body["size"][0]) and same(y1 - y0, body["size"][1])
                 and same(x0, -body["pin1_from_end"])
                 and (same(y0, -body["row_from_side"]) or same(y1, body["row_from_side"])) for x0, y0, x1, y1 in fab)
        rep.check(bool(one) and ok, who, f"no F.Fab body {body['size']} with pin 1 {body['pin1_from_end']} from "
                  f"its end and the row {body['row_from_side']} from a side: {fab}")
    if "body_between" in land and len(holes) == 2:
        pitch = abs(holes[1]["at"][0] - holes[0]["at"][0])
        biggest = max((p.w for p in pth), default=0)
        rep.check(pitch >= land["body_between"] + biggest - TOL, who,
                  f"lead pitch {pitch} leaves no room for a {land['body_between']} mm body between the pads")


def land_npth(rep, who, npth, spec):
    rep.check(len(npth) == len(spec), who, f"{len(npth)} unplated holes, the land has {len(spec)}")
    for h in spec:
        m = match_at(npth, h["at"])
        rep.check(len(m) == 1 and same(m[0].drill, h["drill"]), who,
                  f"no unplated hole of {h['drill']} mm at {h['at']}")


def land_pads(rep, who, pads, land):
    want = land["pads"]
    smd = [p for p in pads if p.attr in ("smd", "conn")]
    rep.check(len(smd) == len(want), who, f"{len(smd)} SMD pads, the land has {len(want)}")
    for w in want:
        m = [p for p in match_at(smd, w["at"]) if p.num == w["n"]]
        if not rep.check(len(m) == 1, who, f"no pad {w['n']!r} at {w['at']}"):
            continue
        p = m[0]
        rep.check(same(p.w, w["size"][0]) and same(p.h, w["size"][1]), who, f"{p}: size is not {w['size']}")
        if "mask" in w:
            margin = (w["mask"] - w["size"][0]) / 2
            rep.check(p.mask_margin is not None and same(p.mask_margin, margin), who,
                      f"{p}: mask margin {p.mask_margin}, a {w['mask']} mm opening needs {margin}")
    land_npth(rep, who, [p for p in pads if p.attr == "npth"], land.get("npth", []))


def check_tie(rep, who, pads, land, fp, tree):
    groups = [g for node in sx.find(tree, "net_tie_pad_groups") for g in node[1:]]
    copper = [s for s in shapes(fp, pcbnew.F_Cu)]
    if land.get("tie") == "electrode":
        rep.check(not groups and not copper, who, "electrode-joined Kelvin land has a net tie or F.Cu graphics")
        return
    want = sorted(", ".join(sorted((s, f), key=int)) for s, f in land["sense"].items())
    have = sorted(", ".join(sorted((x.strip() for x in g.split(",")), key=int)) for g in groups)
    rep.check(have == want, who, f"net tie groups {have}, expected {want}")
    segs = [s for s in copper if s[0] == "Line"]
    rep.check(len(segs) == len(copper) == len(land["sense"]), who,
              f"expected {len(land['sense'])} F.Cu strips and nothing else, found {[s[0] for s in copper]}")
    for s_num, f_num in land["sense"].items():
        sp, fpad = by_number(pads, s_num), by_number(pads, f_num)
        if not (sp and fpad):
            continue
        sp, fpad = sp[0], fpad[0]
        joined = [s for s in segs if (fpad.contains_point(s[1], s[2]) and sp.contains_point(s[3], s[4]))
                  or (fpad.contains_point(s[3], s[4]) and sp.contains_point(s[1], s[2]))]
        rep.check(len(joined) == 1, who, f"no single F.Cu strip from force pad {f_num} into sense pad {s_num}")
        for seg in joined:
            others = [p for p in pads if p.copper and p.num not in (s_num, f_num)]
            for o in others:
                rep.check(seg_clear(seg, o) > TOL, who, f"strip {f_num}-{s_num} touches {o}")


def seg_clear(seg, pad):
    """Smallest gap between a strip (with its width) and a pad's bounding box, by sampling."""
    _, x0, y0, x1, y1, w = seg
    bx0, by0, bx1, by1 = pad.box
    best = 1e9
    for i in range(101):
        x, y = x0 + (x1 - x0) * i / 100, y0 + (y1 - y0) * i / 100
        dx, dy = max(bx0 - x, 0, x - bx1), max(by0 - y, 0, y - by1)
        best = min(best, math.hypot(dx, dy) - w / 2)
    return best


def check_usbc_courtyard(rep, who, fp, pads, land):
    spec = importlib.util.spec_from_file_location("placement_study", ROOT / land["study"])
    st = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(st)
    row = st.USBC_INSULATORS[0]
    ox, oy = row[0] + st.HDR_PITCH / 2, row[1] + st.HDR_W / 2
    want = []
    for x, y, w, h in st.USBC_INSULATORS:
        want.append((x, y, w, h))
    for label, (x, y, w, h) in st.USBC_BELOW:
        if label == "receptacle body":
            y, h = y - land["receptacle_overhang"], h + land["receptacle_overhang"]
        want.append((x, y, w, h))
    want = sorted((round(x - ox, 4), round(y - oy, 4), round(x + w - ox, 4), round(y + h - oy, 4))
                  for x, y, w, h in want)
    have = rects(fp, pcbnew.F_CrtYd)
    other = [s for s in shapes(fp, pcbnew.F_CrtYd) if s[0] != "Rect"]
    ok = len(have) == len(want) and all(all(same(a, b) for a, b in zip(h, w)) for h, w in zip(have, want))
    rep.check(ok and not other, who, f"courtyard {have} (+{len(other)} other) is not the study's {want}")
    for k in range(7):                        # the row pins, as the study places them
        at = [round(row[0] + st.HDR_PITCH / 2 + k * st.HDR_PITCH - ox, 4), 0.0]
        rep.check(bool(match_at(pads, at)), who, f"no pad on the study's row position {k + 1} {at}")


def courtyard_contains(rep, who, fp, pads, generated):
    fp.BuildCourtyardCaches()
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    if not rep.check(cy.OutlineCount() >= 1, who, "no F.Courtyard outline"):
        return

    def inside(x, y):
        return cy.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y)), -1, 0, False)

    for p in pads:
        x0, y0, x1, y1 = p.box
        if p.circle:
            corners = [(p.x + p.w / 2 * c, p.y + p.w / 2 * s) for c, s in
                       ((1, 0), (-1, 0), (0, 1), (0, -1), (0.7071, 0.7071), (-0.7071, -0.7071),
                        (0.7071, -0.7071), (-0.7071, 0.7071))]
        else:
            corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
        rep.check(all(inside(x, y) for x, y in corners), who, f"{p} reaches outside the courtyard")
    if generated:
        for x0, y0, x1, y1 in rects(fp, pcbnew.F_Fab):
            rep.check(all(inside(x, y) for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1))), who,
                      f"F.Fab rectangle {(x0, y0, x1, y1)} reaches outside the courtyard")


# ---- the checks ------------------------------------------------------------------------------
REQUIRED = ("id", "refs", "order", "symbol", "footprint", "datasheet", "land", "pins")


def footprint_names(part):
    fp = part["footprint"]
    if "none" in fp:                           # schematic-only (PWR_FLAG)
        return [], None
    if "make" in fp:
        return [fp["name"]], None
    stock = fp["stock"] if isinstance(fp["stock"], list) else [fp["stock"]]
    return [s.split(":")[1] for s in stock], stock


def check_register(rep, parts):
    ids = [p.get("id") for p in parts]
    rep.check(len(ids) == len(set(ids)), "register", f"duplicate ids: {sorted(i for i in ids if ids.count(i) > 1)}")
    for p in parts:
        missing = [k for k in REQUIRED if k not in p]
        rep.check(not missing, p.get("id", "?"), f"register entry lacks {missing}")
        for k in ("title", "revision", "url", "pins", "land"):
            rep.check(k in p.get("datasheet", {}), p.get("id", "?"), f"datasheet lacks {k!r}")
        for key in ("proxy", "deferred"):
            if key in p.get("land", {}):
                rep.note(p["id"], f"{key}: {p['land'][key]}")
        for n in p.get("notes", []):
            if n.startswith(("ASSUMED", "UNCERTAIN", "PROVISIONAL", "DERIVED")):
                rep.note(p["id"], n)


def symbol_pins(sym):
    pins = []
    for unit in sx.find(sym, "symbol"):
        for pin in sx.find(unit, "pin"):
            pins.append((sx.first(pin, "number")[1], sx.first(pin, "name")[1]))
    return pins


def check_symbols(rep, parts, sym_path, pretty):
    tree = sx.loads(sym_path.read_text(encoding="utf-8"))
    syms = {s[1]: s for s in sx.find(tree, "symbol")}
    ids = {p["id"] for p in parts}
    rep.check(set(syms) == ids, "symbols", f"library has {sorted(set(syms) - ids)} extra and "
              f"{sorted(ids - set(syms))} missing")
    pins_of = {}
    for part in parts:
        who = part["id"]
        sym = syms.get(who)
        if sym is None:
            continue
        rep.check(sx.first(sym, "extends") is None, who, "symbol is not flattened (extends)")
        pins = symbol_pins(sym)
        nums = [n for n, _ in pins]
        rep.check(len(nums) == len(set(nums)), who, f"duplicate pin numbers {sorted(n for n in nums if nums.count(n) > 1)}")
        got = dict(pins)
        want = part["pins"]
        rep.check(set(got) == set(want), who, f"pin numbers {sorted(got, key=str)} are not the register's "
                  f"{sorted(want, key=str)}")
        for num, ds in want.items():
            if num not in got:
                continue
            if isinstance(ds, list):
                rep.check(got[num] == ds[1], who, f"pin {num} is {got[num]!r}; the datasheet's {ds[0]!r} "
                          f"is expected as {ds[1]!r}")
            else:
                rep.check(norm(got[num]) == norm(ds), who, f"pin {num} is {got[num]!r}, the datasheet says {ds!r}")
        pins_of[who] = set(got)
        props = {p[1]: p[2] for p in sx.find(sym, "property")}
        names, _ = footprint_names(part)
        fp_prop = part["symbol"].get("footprint_property", f"{NICK}:{names[0]}" if names else "")
        rep.check(props.get("Footprint") == fp_prop, who, f"Footprint {props.get('Footprint')!r}, expected {fp_prop!r}")
        if fp_prop:
            rep.check((pretty / f"{fp_prop.split(':')[1]}.kicad_mod").exists(), who, f"{fp_prop} is not in the library")
        rep.check(props.get("Value") == part.get("value", who), who, f"Value {props.get('Value')!r}")
        rep.check(props.get("Datasheet") == (part["datasheet"]["url"] or "~"), who, "Datasheet is not the register's URL")
        if part.get("mpn"):
            rep.check(props.get("MPN") == part["mpn"], who, f"MPN {props.get('MPN')!r}")
        order = part["order"]
        if order["vendor"] == "JLCPCB" and order["code"].startswith("C"):
            rep.check(props.get("LCSC") == order["code"], who, f"LCSC {props.get('LCSC')!r}, expected {order['code']}")
        if order["vendor"] == "Akizuki":
            rep.check(props.get("Akizuki") == order["code"], who, f"Akizuki {props.get('Akizuki')!r}")
        rep.check(props.get("Class") == order["class"], who, f"Class {props.get('Class')!r}")
        in_bom = str(sx.first(sym, "in_bom")[1])
        rep.check(in_bom == ("yes" if part["symbol"].get("in_bom", True) else "no"), who, f"in_bom {in_bom}")
        prefix = re.match(r"([A-Z]+)\d", part["refs"])
        if prefix:
            rep.check(props.get("Reference") == prefix.group(1), who,
                      f"Reference {props.get('Reference')!r} for designators {part['refs']}")
    return pins_of


LAND = {"qfn_land": lambda rep, who, pads, land, fp: land_qfn(rep, who, pads, land, True),
        "qfn": lambda rep, who, pads, land, fp: land_qfn(rep, who, pads, land, False),
        "dual": lambda rep, who, pads, land, fp: land_dual(rep, who, pads, land),
        "sot23": lambda rep, who, pads, land, fp: land_sot23(rep, who, pads, land),
        "sot223": lambda rep, who, pads, land, fp: land_sot223(rep, who, pads, land),
        "chip": lambda rep, who, pads, land, fp: land_chip(rep, who, pads, land),
        "kelvin_chip": lambda rep, who, pads, land, fp: land_kelvin_chip(rep, who, pads, land),
        "pads": lambda rep, who, pads, land, fp: land_pads(rep, who, pads, land),
        "holes": land_holes,
        "generic": lambda rep, who, pads, land, fp: None}


def check_footprints(rep, parts, pretty, pins_of):
    files = {f.stem for f in pretty.glob("*.kicad_mod")}
    wanted = {}
    for part in parts:
        names, stock = footprint_names(part)
        for i, name in enumerate(names):
            wanted.setdefault(name, []).append((part, stock[i] if stock else None))
    rep.check(files == set(wanted), "footprints", f"library has {sorted(files - set(wanted))} extra and "
              f"{sorted(set(wanted) - files)} missing")
    for name, users in sorted(wanted.items()):
        path = pretty / f"{name}.kicad_mod"
        if not path.exists():
            continue
        for part, stock in users:
            who = f"{part['id']} / {name}"
            if stock:
                lib, base = stock.split(":")
                src = KFP / f"{lib}.pretty" / f"{base}.kicad_mod"
                rep.check(path.read_bytes() == src.read_bytes().replace(b"\r\n", b"\n"), who,
                          f"not a byte copy of KiCad's {stock} (its CRLF read as LF)")
            fp = pcbnew.FootprintLoad(str(pretty), name)
            if not rep.check(fp is not None, who, "pcbnew cannot load it"):
                continue
            rep.check(fp.GetFPID().GetLibItemName() == name, who,
                      f"internal name {fp.GetFPID().GetLibItemName()!r} is not the file name")
            tree = sx.loads(path.read_text(encoding="utf-8"))
            pads = [Pad(p) for p in fp.Pads()]
            rep.check(not any(p.rotated_badly for p in pads), who, "a pad is rotated off the 90-degree grid")
            pad_nums = {p.num for p in numbered(pads)}
            rep.check(pad_nums == pins_of.get(part["id"], set()), who,
                      f"numbered pads {sorted(pad_nums, key=str)} are not the symbol's pins "
                      f"{sorted(pins_of.get(part['id'], set()), key=str)}")
            land = part["land"]
            LAND[land["kind"]](rep, who, pads, land, fp)
            if "sense" in land:
                check_tie(rep, who, pads, land, fp, tree)
            if land.get("paste") is False:
                rep.check(not any(p.paste for p in pads), who, "a pad has paste; the land has none")
            if land.get("courtyard_from_study"):
                check_usbc_courtyard(rep, who, fp, pads, land)
            courtyard_contains(rep, who, fp, pads, generated=not stock and not land.get("courtyard_from_study"))
    return sorted(wanted)


def check_tables(rep, srcdir, libdir):
    for table, target in (("fp-lib-table", f"{NICK}.pretty"), ("sym-lib-table", f"{NICK}.kicad_sym")):
        path = srcdir / table
        if not rep.check(path.exists(), "tables", f"{table} is missing"):
            continue
        libs = sx.find(sx.loads(path.read_text(encoding="utf-8")), "lib")
        entries = [{n[0]: n[1] for n in lib[1:] if isinstance(n, list)} for lib in libs]
        rep.check(len(entries) == 1 and entries[0].get("name") == NICK and entries[0].get("type") == "KiCad",
                  "tables", f"{table} should name only {NICK!r}: {entries}")
        if entries:
            uri = entries[0].get("uri", "")
            resolved = pathlib.Path(uri.replace("${KIPRJMOD}", str(srcdir)))
            rep.check(uri.startswith("${KIPRJMOD}/") and resolved.exists()
                      and resolved.resolve() == (libdir / target).resolve(), "tables",
                      f"{table} uri {uri!r} does not resolve to {libdir / target}")


def check_line_endings(rep, srcdir, libdir):
    """The repository stores text as LF (.gitattributes eol=lf); a CR here would not survive
    a commit and checkout, so the checked bytes would not be the committed ones."""
    files = sorted(p for p in libdir.rglob("*") if p.is_file())
    files += [srcdir / t for t in ("fp-lib-table", "sym-lib-table") if (srcdir / t).exists()]
    for path in files:
        rep.check(b"\r" not in path.read_bytes(), "line endings",
                  f"{path.name} has CR bytes; the repository stores LF")


def run(cmd, cwd=None):
    return subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", cwd=cwd, timeout=600)


def check_cli(rep, sym_path, pretty, parts, fp_names):
    with tempfile.TemporaryDirectory(prefix="libcheck-svg-") as tmp:
        t = pathlib.Path(tmp)
        out = run([CLI, "sym", "export", "svg", "--output", t / "sym", sym_path])
        stems = {f.stem for f in (t / "sym").glob("*.svg")} if (t / "sym").exists() else set()
        for part in parts:
            lid = part["id"].lower()
            rep.check(any(s.lower() == lid or s.lower().startswith(lid + "_unit") for s in stems),
                      part["id"], f"kicad-cli exported no SVG for the symbol (exit {out.returncode}: "
                      f"{out.stderr.strip()[:200]})")
        out = run([CLI, "fp", "export", "svg", "--output", t / "fp", pretty])
        stems = {f.stem.lower() for f in (t / "fp").glob("*.svg")} if (t / "fp").exists() else set()
        for name in fp_names:
            rep.check(name.lower() in stems, name, f"kicad-cli exported no SVG for the footprint "
                      f"(exit {out.returncode}: {out.stderr.strip()[:200]})")


def check_drc(rep, srcdir, pretty, fp_names):
    with tempfile.TemporaryDirectory(prefix="libcheck-drc-") as tmp:
        t = pathlib.Path(tmp)
        for ext in (".kicad_pcb", ".kicad_pro"):
            shutil.copyfile(srcdir / f"{NICK}{ext}", t / f"sandbox{ext}")
        (t / "fp-lib-table").write_text(
            f'(fp_lib_table (version 7) (lib (name "{NICK}")(type "KiCad")(uri "{pretty.resolve().as_posix()}")'
            '(options "")(descr "")))\n', encoding="utf-8", newline="\n")
        board = pcbnew.LoadBoard(str(t / "sandbox.kicad_pcb"))
        for d in list(board.GetDrawings()):
            if d.GetLayer() == pcbnew.Edge_Cuts:
                board.Remove(d)
        x, y, row_h, width = 10.0, 10.0, 0.0, 250.0
        multi = set()                          # nets of pad numbers used twice in a footprint
        for k, name in enumerate(fp_names):
            fp = pcbnew.FootprintLoad(str(pretty), name)
            if not rep.check(fp is not None, "DRC", f"{name} cannot be loaded, so it is not placed"):
                continue
            fp.SetFPID(pcbnew.LIB_ID(NICK, name))
            fp.SetReference(f"X{k + 1}")
            box = fp.GetBoundingBox(True, False)
            w, h = pcbnew.ToMM(box.GetWidth()), pcbnew.ToMM(box.GetHeight())
            if x + w > width:
                x, y, row_h = 10.0, y + row_h + 4.0, 0.0
            fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x) - box.GetLeft(), pcbnew.FromMM(y) - box.GetTop()))
            board.Add(fp)
            nets = {}
            for pad in fp.Pads():
                if pad.GetNumber() == "" or pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    continue
                if pad.GetNumber() in nets:
                    multi.add(f"X{k + 1}_{pad.GetNumber()}")
                else:
                    net = pcbnew.NETINFO_ITEM(board, f"X{k + 1}_{pad.GetNumber()}")
                    board.Add(net)
                    nets[pad.GetNumber()] = net
                pad.SetNet(nets[pad.GetNumber()])
            x += w + 4.0
            row_h = max(row_h, h)
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_RECT)
        edge.SetStart(pcbnew.VECTOR2I(0, 0))
        edge.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(width + 10), pcbnew.FromMM(y + row_h + 10)))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(0.05))
        board.Add(edge)
        pcbnew.SaveBoard(str(t / "sandbox.kicad_pcb"), board)
        out = run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--output", t / "drc.json",
                   t / "sandbox.kicad_pcb"], cwd=t)
        if not rep.check((t / "drc.json").exists(), "DRC", f"kicad-cli wrote no report: {out.stderr.strip()[:300]}"):
            return
        data = json.loads((t / "drc.json").read_text(encoding="utf-8"))
        names = {f"X{k + 1}": n for k, n in enumerate(fp_names)}
        found = [v for v in data.get("violations", []) if v.get("severity") not in ("ignore", "exclusion")]
        for v in found:
            items = "; ".join(re.sub(r"\bX\d+\b", lambda m: f"{m.group(0)}={names.get(m.group(0), '?')}",
                                     i.get("description", "")) for i in v.get("items", []))
            rep.check(False, "DRC", f"{v.get('type')} ({v.get('severity')}): {v.get('description')} [{items}]")
        rep.check(True, "DRC", "")
        # An unconnected item is expected only on a net whose pad number occurs twice in one
        # footprint (a switch has two pads per pin): copper inside a footprint joins nothing else.
        # The net name in brackets ([X<k>_<pad>]) identifies it in any kicad-cli language.
        loose = data.get("unconnected_items", [])
        seen = set()
        for v in loose:
            nets = {m for i in v.get("items", []) for m in re.findall(r"\[(X\d+_[^\]]*)\]", i.get("description", ""))}
            seen |= nets
            rep.check(len(nets) == 1 and nets <= multi, "DRC", "unexpected unconnected item: "
                      + "; ".join(i.get("description", "") for i in v.get("items", []))
                      + f" (nets {sorted(nets)}: {[names.get(n.split('_')[0]) for n in nets]})")
        rep.note("DRC", f"{len(fp_names)} footprints placed; {len(found)} violations; {len(loose)} "
                 f"unconnected items, on same-numbered pads only: "
                 f"{sorted(names[n.split('_')[0]] + ' pad ' + n.split('_', 1)[1] for n in seen)}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    libdir = pathlib.Path(argv[1]) if len(argv) > 1 else ROOT / "design" / "ecad" / "libraries"
    srcdir = pathlib.Path(argv[2]) if len(argv) > 2 else ROOT / "design" / "ecad" / "source"
    rep = Report()
    parts = json.loads((libdir / "library.json").read_text(encoding="utf-8"))["parts"]
    sym_path, pretty = libdir / f"{NICK}.kicad_sym", libdir / f"{NICK}.pretty"
    check_register(rep, parts)
    pins_of = check_symbols(rep, parts, sym_path, pretty)
    fp_names = check_footprints(rep, parts, pretty, pins_of)
    check_tables(rep, srcdir, libdir)
    check_line_endings(rep, srcdir, libdir)
    check_cli(rep, sym_path, pretty, parts, [n for n in fp_names if (pretty / f"{n}.kicad_mod").exists()])
    check_drc(rep, srcdir, pretty, [n for n in fp_names if (pretty / f"{n}.kicad_mod").exists()])
    for line in rep.notes + rep.fails:
        print(line)
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
