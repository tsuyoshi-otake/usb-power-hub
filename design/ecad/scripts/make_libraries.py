"""Write the project symbol and footprint libraries of Rev0.7 from the parts register.

Run with KiCad's own Python from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_libraries.py

Input: design/ecad/libraries/library.json, the parts register (one entry per symbol; its
"about" list explains the fields). Output:
- design/ecad/libraries/usb-power-hub.kicad_sym: every symbol, flattened. A stock symbol is
  copied from KiCad's library with its `extends` chain resolved, renamed to the register id,
  and given the register's Value, Footprint, Datasheet and sourcing properties. Two symbols
  are drawn here (CH335F, the USB-C receptacle), from the register's pin lists. One is
  schematic-only (PWR_FLAG, footprint `none`): it has no Footprint and no footprint file.
- design/ecad/libraries/usb-power-hub.pretty/: one file per footprint. A stock footprint is
  KiCad's file with its CRLF line endings written as LF: KiCad's Windows install ships CRLF,
  and the repository stores LF (.gitattributes `eol=lf`), so a checkout must hold the same
  bytes as this output. Its silkscreen is then made manufacturable (P5): JLCPCB's legend
  needs strokes of at least 0.15 mm, and KiCad draws 0.12 mm, so each F.SilkS stroke is
  widened to 0.15 mm; a footprint in the register's `silk_drop` (0402 R and C, the test
  pad: non-polar, and their silk cannot keep 0.15 mm from their pads) loses its silkscreen.
  Nothing else in the file changes. Eight are generated from the register's `params`:
  the two QFN lands (G20, G21), three Kelvin shunt lands (CLAUDE.md 5.4), the MF-R300
  radial, the MAU104 SIP and the USB-C receptacle (D37).
- design/ecad/source/fp-lib-table and sym-lib-table: the project's library tables.

Then it runs check_libraries.py in a new process. That checker measures the written files
against the register's datasheet facts (`land`, `pins`), never against `params`, so a wrong
parameter here shows up there. Exit status: 0 = written and checked; 1 = the check failed.

The output is deterministic: a re-run writes the same bytes.
"""
import copy
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LIBDIR = ROOT / "design" / "ecad" / "libraries"
SRCDIR = ROOT / "design" / "ecad" / "source"
NICK = "usb-power-hub"
KICAD = pathlib.Path(sys.executable).resolve().parents[1]      # .../KiCad/9.0
KSYM = KICAD / "share" / "kicad" / "symbols"
KFP = KICAD / "share" / "kicad" / "footprints"
SILK_W = 0.15       # mm: JLCPCB legend minimum line width (pcb-capabilities, Legend, 2026-11-06)
SILK_SHAPES = ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")
S = sx.Sym


# ---- symbols ---------------------------------------------------------------------------------
_SYMLIBS = {}


def stock_lib(lib):
    if lib not in _SYMLIBS:
        tree = sx.loads((KSYM / f"{lib}.kicad_sym").read_text(encoding="utf-8"))
        _SYMLIBS[lib] = {s[1]: s for s in sx.find(tree, "symbol")}
    return _SYMLIBS[lib]


def rename_units(sym, old, new):
    for unit in sx.find(sym, "symbol"):
        assert unit[1].startswith(old + "_"), (old, unit[1])
        unit[1] = new + unit[1][len(old):]


def flatten(lib, name):
    """The stock symbol `name` with its `extends` chain resolved, as one symbol named `name`."""
    syms = stock_lib(lib)
    s = syms[name]
    ext = sx.first(s, "extends")
    if ext is None:
        return copy.deepcopy(s)
    base = flatten(lib, ext[1])
    rename_units(base, ext[1], name)
    base[1] = name
    own = {p[1]: p for p in sx.find(s, "property")}
    for i, node in enumerate(base):
        if isinstance(node, list) and node[:1] == ["property"] and node[1] in own:
            base[i] = copy.deepcopy(own.pop(node[1]))
    tail = next(i for i, n in enumerate(base) if isinstance(n, list) and n[0] == "symbol")
    for p in own.values():                     # properties the base does not have
        base.insert(tail, copy.deepcopy(p))
        tail += 1
    return base


def prop(name, value, at=(0, 0, 0), hide=True):
    effects = ["effects", ["font", ["size", 1.27, 1.27]]]
    if hide:
        effects.append(["hide", S("yes")])
    return ["property", name, value, ["at", *at], effects]


def part_footprint(part):
    fp = part["footprint"]
    if "none" in fp:                           # a schematic-only symbol (PWR_FLAG)
        return []
    if "make" in fp:
        return [fp["name"]]
    stock = fp["stock"]
    return [s.split(":")[1] for s in (stock if isinstance(stock, list) else [stock])]


def footprint_property(part):
    if "footprint_property" in part["symbol"]:
        return part["symbol"]["footprint_property"]
    names = part_footprint(part)
    return f"{NICK}:{names[0]}" if names else ""


def sourcing_props(part):
    order = part["order"]
    props = []
    if part.get("mpn"):
        props.append(("MPN", part["mpn"]))
    if part.get("manufacturer"):
        props.append(("Manufacturer", part["manufacturer"]))
    if order["vendor"] == "JLCPCB" and order["code"].startswith("C"):
        props.append(("LCSC", order["code"]))
    if order["vendor"] == "Akizuki":
        props.append(("Akizuki", order["code"]))
    props.append(("Class", order["class"]))
    return props


def description(part):
    who = " ".join(x for x in (part.get("manufacturer"), part.get("mpn")) if x)
    order = part["order"]
    where = f"{order['vendor']} {order['code']}".strip()
    return f"{who or part['id']}; {where} ({order['class']}); register: {NICK} library.json"


def set_properties(sym, part):
    """Replace the identity properties of a symbol node with the register's."""
    fps = part_footprint(part)
    values = {
        "Value": part.get("value", part["id"]),
        "Footprint": footprint_property(part),
        "Datasheet": part["datasheet"]["url"] or "~",
        "Description": description(part),
    }
    if fps:
        values["ki_fp_filters"] = " ".join(fps)
    keep = []
    for node in sym:
        if isinstance(node, list) and node[:1] == ["property"]:
            if node[1] in ("ki_keywords",):
                continue
            if node[1] in values:
                node[2] = values.pop(node[1])
        keep.append(node)
    sym[:] = keep
    tail = next(i for i, n in enumerate(sym) if isinstance(n, list) and n[0] == "symbol")
    for name, value in list(values.items()) + sourcing_props(part):
        sym.insert(tail, prop(name, value))
        tail += 1
    sx.first(sym, "in_bom")[1] = S("yes" if part["symbol"].get("in_bom", True) else "no")
    prefix = re.match(r"([A-Z]+)\d", part["refs"])
    if prefix:                                 # the register's designator letters (U5, RS10, ...)
        next(p for p in sx.find(sym, "property") if p[1] == "Reference")[2] = prefix.group(1)


def pin_node(num, name, etype, x, y, angle):
    font = ["effects", ["font", ["size", 1.27, 1.27]]]
    return ["pin", S(etype), S("line"), ["at", x, y, angle], ["length", 2.54],
            ["name", name, font], ["number", num, copy.deepcopy(font)]]


def grid(v, step=2.54):
    return round(round(v / step) * step, 4)


def custom_symbol(part):
    """A box symbol: pins on four sides at 2.54 mm pitch, 2.54 mm long. [] in a side's list is
    a gap. Symbol coordinates have y up."""
    c = part["symbol"]["custom"]
    left, right = c.get("left", []), c.get("right", [])
    top, bottom = c.get("top", []), c.get("bottom", [])
    rows = max(len(left), len(right), 1)
    longest = (max((len(p[1]) for p in left if p), default=0)
               + max((len(p[1]) for p in right if p), default=0))
    across = max(len(top), len(bottom), 1)
    half_w = max(5.08, grid((longest * 1.0 + 3.6) / 2 + 1.27, 2.54), (across + 1) * 2.54)
    y_top = 2.54 * (rows // 2)
    box_top, box_bottom = y_top + 2.54, y_top - rows * 2.54
    pins = []
    for i, p in enumerate(left):
        if p:
            pins.append(pin_node(p[0], p[1], p[2], -half_w - 2.54, round(y_top - 2.54 * i, 4), 0))
    for i, p in enumerate(right):
        if p:
            pins.append(pin_node(p[0], p[1], p[2], half_w + 2.54, round(y_top - 2.54 * i, 4), 180))
    for side, y, angle in ((top, box_top + 2.54, 270), (bottom, box_bottom - 2.54, 90)):
        for i, p in enumerate(side):
            x = round((i - (len(side) - 1) / 2) * 5.08, 4)
            pins.append(pin_node(p[0], p[1], p[2], x, round(y, 4), angle))
    name = part["id"]
    body = ["symbol", f"{name}_0_1",
            ["rectangle", ["start", -half_w, round(box_top, 4)], ["end", half_w, round(box_bottom, 4)],
             ["stroke", ["width", 0.254], ["type", S("default")]], ["fill", ["type", S("background")]]]]
    sym = ["symbol", name, ["pin_names", ["offset", 1.016]], ["exclude_from_sim", S("no")],
           ["in_bom", S("yes")], ["on_board", S("yes")],
           ["property", "Reference", c["reference"], ["at", -half_w, round(box_top + 1.27, 4), 0],
            ["effects", ["font", ["size", 1.27, 1.27]], ["justify", S("left")]]],
           ["property", "Value", part.get("value", name), ["at", half_w, round(box_top + 1.27, 4), 0],
            ["effects", ["font", ["size", 1.27, 1.27]], ["justify", S("right")]]],
           prop("Footprint", "", (-half_w, round(box_bottom - 5.08, 4), 0)),
           prop("Datasheet", "", (0, 0, 0)),
           prop("Description", c["description"], (0, 0, 0)),
           body, ["symbol", f"{name}_1_1", *pins], ["embedded_fonts", S("no")]]
    set_properties(sym, part)
    for node in sx.find(sym, "property"):      # the box carries its own description
        if node[1] == "Description":
            node[2] = f"{c['description']}. {description(part)}"
    return sym


def make_symbol(part):
    if "custom" in part["symbol"]:
        return custom_symbol(part)
    lib, name = part["symbol"]["base"].split(":")
    sym = flatten(lib, name)
    rename_units(sym, name, part["id"])
    sym[1] = part["id"]
    set_properties(sym, part)
    return sym


def write_symbols(parts, path):
    lib = ["kicad_symbol_lib", ["version", 20241209], ["generator", "kicad_symbol_editor"],
           ["generator_version", "9.0"]]
    lib += [make_symbol(p) for p in parts]
    path.write_text(sx.dumps(lib) + "\n", encoding="utf-8", newline="\n")


# ---- footprint building blocks ---------------------------------------------------------------
def stroke(width):
    return ["stroke", ["width", width], ["type", S("solid")]]


def line(a, b, layer, width):
    return ["fp_line", ["start", *a], ["end", *b], stroke(width), ["layer", layer]]


def rect(a, b, layer, width, fill=False):
    return ["fp_rect", ["start", *a], ["end", *b], stroke(width),
            ["fill", S("yes" if fill else "no")], ["layer", layer]]


def poly(pts, layer, width, fill=True):
    return ["fp_poly", ["pts", *[["xy", *p] for p in pts]], stroke(width),
            ["fill", S("yes" if fill else "no")], ["layer", layer]]


def text_effects(size=1.0, thickness=0.15):
    return ["effects", ["font", ["size", size, size], ["thickness", thickness]]]


def header(name, descr, tags, attr, ref_at, value_at, extra=()):
    fp = ["footprint", name, ["version", 20241229], ["generator", "make_libraries.py"],
          ["layer", "F.Cu"], ["descr", descr], ["tags", tags],
          ["property", "Reference", "REF**", ["at", *ref_at, 0], ["layer", "F.SilkS"], text_effects()],
          ["property", "Value", name, ["at", *value_at, 0], ["layer", "F.Fab"], text_effects()]]
    fp += list(extra)
    fp.append(["attr", *[S(a) for a in attr]])
    return fp


def fab_ref(at):
    return ["fp_text", S("user"), "${REFERENCE}", ["at", *at, 0], ["layer", "F.Fab"],
            text_effects(0.8, 0.12)]


def smd_pad(num, at, size, layers=("F.Cu", "F.Mask", "F.Paste"), shape="roundrect", rratio=0.25):
    pad = ["pad", num, S("smd"), S(shape), ["at", *at], ["size", *size], ["layers", *layers]]
    if shape == "roundrect":
        pad.append(["roundrect_rratio", rratio])
    return pad


def tht_pad(num, at, size, drill, shape="circle"):
    return ["pad", num, S("thru_hole"), S(shape), ["at", *at], ["size", size, size],
            ["drill", drill], ["layers", "*.Cu", "*.Mask"]]


def model(path):
    return ["model", path, ["offset", ["xyz", 0, 0, 0]], ["scale", ["xyz", 1, 1, 1]],
            ["rotate", ["xyz", 0, 0, 0]]]


def r(v):
    return round(v, 4)


# ---- footprint generators --------------------------------------------------------------------
def gen_qfn(name, p, part):
    """QFN with a square body, pin 1 at the top of the left side, counter-clockwise (top view)."""
    n, pitch, (plen, pw), c, e = p["per_side"], p["pitch"], p["pad"], p["pad_centre"], p["epad"]
    half_b = p["body"] / 2
    outer = c + plen / 2
    court = r(outer + 0.25)
    off = [(i - (n - 1) / 2) * pitch for i in range(n)]
    fp = header(name, f"{part['mpn']} {part['manufacturer']}, {4 * n} pins + ePad, "
                f"{p['body']} x {p['body']} mm, {pitch} mm pitch; land: {part['datasheet']['land']}",
                "QFN NoLead", ["smd"], (0, r(-court - 0.7)), (0, r(court + 0.7)))
    silk = r(half_b + 0.11)
    first = r((n - 1) / 2 * pitch + pw / 2 + 0.26)
    for sxn, syn in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        corner = (r(sxn * silk), r(syn * silk))
        fp.append(line(corner, (r(sxn * first), r(syn * silk)), "F.SilkS", SILK_W))
        fp.append(line(corner, (r(sxn * silk), r(syn * first)), "F.SilkS", SILK_W))
    y1 = r(-(n - 1) / 2 * pitch)
    tip = r(outer + 0.27)
    fp.append(poly([(-tip, y1), (r(-tip - 0.25), r(y1 + 0.18)), (r(-tip - 0.25), r(y1 - 0.18))],
                   "F.SilkS", SILK_W))
    fp.append(rect((-court, -court), (court, court), "F.CrtYd", 0.05))
    ch = min(1.0, half_b / 4)
    fp.append(poly([(r(-half_b + ch), -half_b), (half_b, -half_b), (half_b, half_b), (-half_b, half_b),
                    (-half_b, r(-half_b + ch))], "F.Fab", 0.1, fill=False))
    fp.append(fab_ref((0, 0)))
    num = 1
    for side in range(4):
        for i in range(n):
            o = off[i]
            if side == 0:
                at, size = (r(-c), r(o)), (plen, pw)
            elif side == 1:
                at, size = (r(o), r(c)), (pw, plen)
            elif side == 2:
                at, size = (r(c), r(-o)), (plen, pw)
            else:
                at, size = (r(-o), r(-c)), (pw, plen)
            fp.append(smd_pad(str(num), at, size))
            num += 1
    g, win = p["paste_grid"], r(p["paste_fraction"] * e)
    for ix in range(g):
        for iy in range(g):
            at = (r((ix - (g - 1) / 2) * e / g), r((iy - (g - 1) / 2) * e / g))
            fp.append(smd_pad("", at, (win, win), layers=("F.Paste",), rratio=0.25))
    fp.append(["pad", p["epad_number"], S("smd"), S("rect"), ["at", 0, 0], ["size", e, e],
               ["property", S("pad_prop_heatsink")], ["layers", "F.Cu", "F.Mask"], ["zone_connect", 2]])
    fp.append(["embedded_fonts", S("no")])
    if p.get("model"):
        fp.append(model(p["model"]))
    return fp


def gen_kelvin_chip(name, p, part):
    """A 2-terminal chip on a 4-pad land: each end split across the width into a force pad and a
    sense pad. Pads 1 (force) and 2 (sense) at -x, 4 (force) and 3 (sense) at +x."""
    x0, x1 = p["x"]
    fy, sy = p["force_y"], p["sense_y"]
    xc, plen = r((x0 + x1) / 2), r(x1 - x0)
    layers = ("F.Cu", "F.Mask", "F.Paste") if p["paste"] else ("F.Cu", "F.Mask")
    bl, bw = p["body"][0] / 2, p["body"][1] / 2
    cx, cy = r(x1 + 0.25), r(max(bw, fy[1], -sy[0]) + 0.25)
    fp = header(name, f"{part['mpn']} {part['manufacturer']} on a derived Kelvin land (force 1/4, "
                f"sense 2/3); KOA gives no land; body {p['body'][0]} x {p['body'][1]} mm",
                "resistor shunt Kelvin 4-terminal", ["smd"], (0, r(-cy - 0.7)), (0, r(cy + 0.7)))
    silk_x = r(x0 - 0.26)
    for y in (r(-bw - 0.11), r(bw + 0.11)):
        fp.append(line((-silk_x, y), (silk_x, y), "F.SilkS", SILK_W))
    fp.append(rect((-cx, -cy), (cx, cy), "F.CrtYd", 0.05))
    fp.append(rect((-bl, -bw), (bl, bw), "F.Fab", 0.1))
    fp.append(fab_ref((0, 0)))
    fyc, fh = r((fy[0] + fy[1]) / 2), r(fy[1] - fy[0])
    syc, sh = r((sy[0] + sy[1]) / 2), r(sy[1] - sy[0])
    fp.append(smd_pad("1", (-xc, fyc), (plen, fh), layers, rratio=0.1))
    fp.append(smd_pad("2", (-xc, syc), (plen, sh), layers, rratio=0.1))
    fp.append(smd_pad("3", (xc, syc), (plen, sh), layers, rratio=0.1))
    fp.append(smd_pad("4", (xc, fyc), (plen, fh), layers, rratio=0.1))
    fp.append(["embedded_fonts", S("no")])
    return fp


def stock_pads(lib_name):
    lib, name = lib_name.split(":")
    tree = sx.loads((KFP / f"{lib}.pretty" / f"{name}.kicad_mod").read_text(encoding="utf-8"))
    return {pad[1]: pad for pad in sx.find(tree, "pad")}


def tie_props():
    return [["net_tie_pad_groups", "1, 2", "3, 4"]]


def gen_chip_kelvin_tie(name, p, part):
    """A stock chip land, its pads renumbered 1 and 4, with a sense pad (F.Cu only, under the
    mask) beyond each and joined to it by a copper strip: a KiCad net tie."""
    pads = stock_pads(p["stock"])
    a, b = copy.deepcopy(pads["1"]), copy.deepcopy(pads["2"])
    b[1] = "4"
    ax, b_x = sx.first(a, "at")[1], sx.first(b, "at")[1]
    ph = sx.first(a, "size")[2]
    s, sy, tw = p["sense_pad"], p["sense_y"], p["tie_width"]
    top = r(sy - s / 2)
    cx, cy_top, cy_bot = r(abs(ax) + sx.first(a, "size")[1] / 2 + 0.25), r(top - 0.25), r(ph / 2 + 0.25)
    fp = header(name, f"Chip resistor 0805 on KiCad's R_0805_2012Metric land (pads 1, 4) with a "
                f"sense pad at each end (2, 3) joined by copper (net tie); register: {part['id']}",
                "resistor shunt Kelvin net tie 0805", ["smd"], (0, r(cy_top - 0.7)), (0, r(cy_bot + 0.7)),
                extra=tie_props())
    fp.append(line((-0.227064, -0.735), (0.227064, -0.735), "F.SilkS", SILK_W))
    fp.append(line((-0.227064, 0.735), (0.227064, 0.735), "F.SilkS", SILK_W))
    fp.append(rect((-cx, cy_top), (cx, cy_bot), "F.CrtYd", 0.05))
    fp.append(rect((-1.0, -0.625), (1.0, 0.625), "F.Fab", 0.1))
    fp.append(fab_ref((0, 0)))
    for x, num in ((ax, "2"), (b_x, "3")):
        fp.append(line((x, r(-ph / 2 + 0.2)), (x, sy), "F.Cu", tw))
    fp += [a, smd_pad("2", (ax, sy), (s, s), ("F.Cu",), "rect"),
           smd_pad("3", (b_x, sy), (s, s), ("F.Cu",), "rect"), b]
    fp.append(["embedded_fonts", S("no")])
    return fp


def gen_axial_kelvin(name, p, part):
    """An axial resistor, leads 1 and 4, with an F.Cu sense pad beside each lead pad, joined to
    its annular ring by copper (net tie)."""
    pitch, d, pad, s, sy, tw = p["pitch"], p["drill"], p["pad"], p["sense_pad"], p["sense_at"], p["tie_width"]
    bl, bd = p["body"]
    x0, x1 = r((pitch - bl) / 2), r((pitch + bl) / 2)
    cy_top, cy_bot = r(sy - s / 2 - 0.25), r(bd / 2 + 0.11 + 0.25)
    fp = header(name, f"{part['mpn']} {part['manufacturer']}, axial, lead pitch {pitch} mm, "
                f"sense pads 2, 3 tied to leads 1, 4 (net tie); body {bl} x {bd} mm max",
                "resistor axial shunt Kelvin net tie", ["through_hole"], (r(pitch / 2), r(cy_top - 0.7)),
                (r(pitch / 2), r(cy_bot + 0.7)), extra=tie_props())
    sb = r(bd / 2 + 0.11)
    fp.append(rect((r(x0 - 0.11), -sb), (r(x1 + 0.11), sb), "F.SilkS", SILK_W))
    fp.append(line((r(pad / 2 + 0.3), 0), (r(x0 - 0.11), 0), "F.SilkS", SILK_W))
    fp.append(line((r(x1 + 0.11), 0), (r(pitch - pad / 2 - 0.3), 0), "F.SilkS", SILK_W))
    fp.append(rect((r(-pad / 2 - 0.25), cy_top), (r(pitch + pad / 2 + 0.25), cy_bot), "F.CrtYd", 0.05))
    fp.append(rect((x0, r(-bd / 2)), (x1, r(bd / 2)), "F.Fab", 0.1))
    fp.append(line((0, 0), (x0, 0), "F.Fab", 0.1))
    fp.append(line((x1, 0), (pitch, 0), "F.Fab", 0.1))
    fp.append(fab_ref((r(pitch / 2), 0)))
    for x in (0, pitch):
        fp.append(line((x, r(-pad / 4)), (x, sy), "F.Cu", tw))
    fp += [tht_pad("1", (0, 0), pad, d, "rect"), smd_pad("2", (0, sy), (s, s), ("F.Cu",), "circle"),
           smd_pad("3", (pitch, sy), (s, s), ("F.Cu",), "circle"), tht_pad("4", (pitch, 0), pad, d)]
    fp.append(["embedded_fonts", S("no")])
    return fp


def gen_radial(name, p, part):
    pitch, d, pad = p["pitch"], p["drill"], p["pad"]
    bw, bt = p["body"]
    x0, x1, yb = r(pitch / 2 - bw / 2), r(pitch / 2 + bw / 2), r(bt / 2)
    fp = header(name, f"{part['mpn']} {part['manufacturer']} PTC, radial, style 2 straight leads, "
                f"pitch {pitch} mm, body {bw} x {bt} mm max", "PTC polyfuse radial", ["through_hole"],
                (r(pitch / 2), r(-yb - 1.3)), (r(pitch / 2), r(yb + 1.3)))
    fp.append(rect((r(x0 - 0.11), r(-yb - 0.11)), (r(x1 + 0.11), r(yb + 0.11)), "F.SilkS", SILK_W))
    fp.append(rect((r(x0 - 0.5), r(-yb - 0.5)), (r(x1 + 0.5), r(yb + 0.5)), "F.CrtYd", 0.05))
    fp.append(rect((x0, -yb), (x1, yb), "F.Fab", 0.1))
    fp.append(fab_ref((r(pitch / 2), 0)))
    fp += [tht_pad("1", (0, 0), pad, d), tht_pad("2", (pitch, 0), pad, d)]
    fp.append(["embedded_fonts", S("no")])
    return fp


def gen_sip(name, p, part):
    x0, y0, x1, y1 = p["body"]
    fp = header(name, f"{part['mpn']} {part['manufacturer']} 1 W DC-DC, SIP-7 single output (pins 1, 2, "
                f"4, 6 fitted), body {r(x1 - x0)} x {r(y1 - y0)} mm", "DCDC SIP Minmax", ["through_hole"],
                (r((x0 + x1) / 2), r(y0 - 1.3)), (r((x0 + x1) / 2), r(y1 + 1.3)))
    fp.append(rect((r(x0 - 0.11), r(y0 - 0.11)), (r(x1 + 0.11), r(y1 + 0.11)), "F.SilkS", SILK_W))
    fp.append(line((r(x0 - 0.4), r(y0 - 0.4)), (r(x0 - 0.4), 0.8), "F.SilkS", SILK_W))
    fp.append(rect((r(x0 - 0.25), r(y0 - 0.25)), (r(x1 + 0.25), r(y1 + 0.25)), "F.CrtYd", 0.05))
    fp.append(rect((x0, y0), (x1, y1), "F.Fab", 0.1))
    fp.append(fab_ref((r((x0 + x1) / 2), r((y0 + y1) / 2 + 1.0))))
    for num, x in p["pins"]:
        fp.append(tht_pad(num, (x, 0), p["pad"], p["drill"], "rect" if num == "1" else "circle"))
    fp.append(["embedded_fonts", S("no")])
    return fp


def gen_usbc_receptacle(name, p, part):
    """A USB-C receptacle with one row of SMD contacts and four plated shell slots (D37), in its
    drawing's top view: origin at the body centre, the plug opening (product edge) toward +y,
    contact A1 at -x. Every land length is measured from the front slots' centre line, as
    the drawing dimensions it; `trim` shortens a pad at its near end (the end toward the
    opening) to keep the unplated pegs' clearance (library.json)."""
    bw, bd = p["body"]
    front = r(bd / 2)                          # the product edge, at the body's front face
    y0 = r(front - p["front_face"])            # the front slots' centre line
    near, far = p["pad_row"]
    court = r(max(bw / 2, max(s["x"] + s["pad"][0] / 2 for s in p["slots"])) + p["courtyard_margin"])
    back = r(y0 - far - p["courtyard_margin"])
    fp = header(name, f"{part['mpn']} {part['manufacturer']} USB Type-C receptacle, 16 contacts in one SMD "
                f"row, 4 plated shell slots, 2 unplated pegs; land: {part['datasheet']['land']}",
                "USB Type-C receptacle SMD", ["smd"], (0, r(back - 1.2)), (0, r(y0 + 0.9)))
    # Silkscreen: the body's sides between the slots, and a pin-1 arrow behind contact A1.
    gap = SILK_W / 2 + 0.15 + 0.03            # JLCPCB's 0.15 mm from a mask opening, and 0.03 spare
    sx_ = r(bw / 2 + 0.11)
    rear = next(s for s in p["slots"] if s["behind"] > 0)
    fronts = next(s for s in p["slots"] if s["behind"] == 0)
    top, bottom = r(y0 - rear["behind"] + rear["pad"][1] / 2 + gap), r(y0 - fronts["pad"][1] / 2 - gap)
    for sgn in (-1, 1):
        fp.append(line((r(sgn * sx_), top), (r(sgn * sx_), bottom), "F.SilkS", SILK_W))
    a1 = next(x for n, x, _ in p["pads"] if n == "A1")
    tip = r(y0 - far - gap - 0.05)
    fp.append(poly([(a1, tip), (r(a1 - 0.3), r(tip - 0.45)), (r(a1 + 0.3), r(tip - 0.45))], "F.SilkS", SILK_W))
    fp.append(rect((-court, back), (court, r(front + p["courtyard_margin"])), "F.CrtYd", 0.05))
    fp.append(rect((r(-bw / 2), r(-bd / 2)), (r(bw / 2), front), "F.Fab", 0.1))
    fp.append(line((r(-bw / 2), r(front - 0.3)), (r(bw / 2), r(front - 0.3)), "F.Fab", 0.1))
    fp.append(fab_ref((0, r(y0 - 1.0))))
    for num, x, w in p["pads"]:
        n_end = r(near + p.get("trim", {}).get(num, 0.0))
        fp.append(smd_pad(num, (x, r(y0 - (n_end + far) / 2)), (w, r(far - n_end)), shape="rect"))
    for s in p["slots"]:
        for sgn in (-1, 1):
            fp.append(["pad", "S1", S("thru_hole"), S("oval"), ["at", r(sgn * s["x"]), r(y0 - s["behind"])],
                       ["size", *s["pad"]], ["drill", S("oval"), *s["hole"]], ["layers", "*.Cu", "*.Mask"]])
    h = p["npth"]
    for sgn in (-1, 1):
        fp.append(["pad", "", S("np_thru_hole"), S("circle"), ["at", r(sgn * h["x"]), r(y0 - h["behind"])],
                   ["size", h["drill"], h["drill"]], ["drill", h["drill"]], ["layers", "*.Cu", "*.Mask"]])
    fp.append(["embedded_fonts", S("no")])
    return fp


def gen_pad_grid(name, p, part):
    """Bare pads on a grid, for the spring pins of a clamp (issue #14): no paste, no hole, no
    part. Origin at the grid's centre; `pads` gives [number, column, row], column 0 at -x and
    row 0 at -y. Pad 1 is square, the others round, and a silkscreen bar stands beside pad 1's
    row end."""
    pitch, d = p["pitch"], p["pad"]
    cols, rows = p["grid"]
    xs = [r((i - (cols - 1) / 2) * pitch) for i in range(cols)]
    ys = [r((j - (rows - 1) / 2) * pitch) for j in range(rows)]
    x0, x1, y0, y1 = r(xs[0] - d / 2), r(xs[-1] + d / 2), r(ys[0] - d / 2), r(ys[-1] + d / 2)
    fp = header(name, f"{cols} x {rows} bare pads of {d} mm at {pitch} mm pitch for a spring-pin clamp, "
                f"no part fitted", "SWD pogo clamp test pads", ["smd", "exclude_from_pos_files", "exclude_from_bom"],
                (0, r(y1 + 1.3)), (0, r(y1 + 2.6)))
    one = next(q for q in p["pads"] if q[0] == "1")
    fp.append(line((r(x0 - 0.4), r(ys[one[2]] - d / 2)), (r(x0 - 0.4), r(ys[one[2]] + d / 2)), "F.SilkS", SILK_W))
    fp.append(rect((r(x0 - 0.6), r(y0 - 0.25)), (r(x1 + 0.25), r(y1 + 0.25)), "F.CrtYd", 0.05))
    fp.append(rect((x0, y0), (x1, y1), "F.Fab", 0.1))
    fp.append(fab_ref((0, 0)))
    for num, col, row in p["pads"]:
        fp.append(smd_pad(num, (xs[col], ys[row]), (d, d), layers=("F.Cu", "F.Mask"),
                          shape="rect" if num == "1" else "circle"))
    fp.append(["embedded_fonts", S("no")])
    return fp


GENERATORS = {"qfn": gen_qfn, "kelvin_chip": gen_kelvin_chip, "chip_kelvin_tie": gen_chip_kelvin_tie,
              "axial_kelvin": gen_axial_kelvin, "radial": gen_radial, "sip": gen_sip,
              "usbc_receptacle": gen_usbc_receptacle, "pad_grid": gen_pad_grid}


def write_footprints(parts, pretty):
    pretty.mkdir(parents=True, exist_ok=True)
    for old in pretty.glob("*.kicad_mod"):     # generated output only: rewritten below
        old.unlink()
    for part in parts:
        fp = part["footprint"]
        if "none" in fp:
            continue
        if "make" in fp:
            node = GENERATORS[fp["make"]](fp["name"], fp["params"], part)
            (pretty / f"{fp['name']}.kicad_mod").write_text(sx.dumps(node) + "\n", encoding="utf-8",
                                                            newline="\n")
            continue
        drop = set(fp.get("silk_drop", []))
        for lib_name in (fp["stock"] if isinstance(fp["stock"], list) else [fp["stock"]]):
            lib, name = lib_name.split(":")
            dst = pretty / f"{name}.kicad_mod"
            if not dst.exists():
                text = (KFP / f"{lib}.pretty" / f"{name}.kicad_mod").read_bytes().decode("utf-8")
                dst.write_bytes(adapt_stock(text.replace("\r\n", "\n"), name in drop).encode("utf-8"))
            drop.discard(name)
        if drop:
            raise SystemExit(f"{part['id']}: silk_drop names {sorted(drop)}, which it does not use")


def adapt_stock(text, drop):
    """KiCad's stock footprint text with JLCPCB's legend limits (library.json `about`): each
    F.SilkS shape's stroke widened to SILK_W, or every F.SilkS shape left out when `drop`.
    Text-level, so the rest of the file stays KiCad's bytes; check_libraries.py compares it
    with KiCad's file and measures the limits itself."""
    lines, out, i, seen = text.split("\n"), [], 0, 0
    while i < len(lines):
        m = re.fullmatch(r"\t\((\w+)", lines[i])
        if m and m.group(1) in SILK_SHAPES:
            j = lines.index("\t)", i)
            block = lines[i:j + 1]
            if '\t\t(layer "F.SilkS")' in block:
                seen += 1
                if drop:
                    i = j + 1
                    continue
                block = [re.sub(r"^(\t\t\t\(width )([0-9.]+)\)$",
                                lambda w: w.group(1) + (f"{SILK_W:g}" if float(w.group(2)) < SILK_W
                                                        else w.group(2)) + ")", ln) for ln in block]
            out += block
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    if drop and not seen:
        raise SystemExit("silk_drop on a footprint without silkscreen")
    return "\n".join(out)


def write_tables(src):
    descr = "Rev0.7 parts, generated by design/ecad/scripts/make_libraries.py from library.json"
    (src / "fp-lib-table").write_text(
        "(fp_lib_table\n\t(version 7)\n"
        f'\t(lib (name "{NICK}")(type "KiCad")(uri "${{KIPRJMOD}}/../libraries/{NICK}.pretty")'
        f'(options "")(descr "{descr}"))\n)\n', encoding="utf-8", newline="\n")
    (src / "sym-lib-table").write_text(
        "(sym_lib_table\n\t(version 7)\n"
        f'\t(lib (name "{NICK}")(type "KiCad")(uri "${{KIPRJMOD}}/../libraries/{NICK}.kicad_sym")'
        f'(options "")(descr "{descr}"))\n)\n', encoding="utf-8", newline="\n")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parts = json.loads((LIBDIR / "library.json").read_text(encoding="utf-8"))["parts"]
    write_symbols(parts, LIBDIR / f"{NICK}.kicad_sym")
    write_footprints(parts, LIBDIR / f"{NICK}.pretty")
    write_tables(SRCDIR)
    print(f"wrote {len(parts)} symbols, {len(list((LIBDIR / f'{NICK}.pretty').glob('*.kicad_mod')))} "
          "footprints, 2 library tables")
    return subprocess.run([sys.executable, "-I", "-B", str(HERE / "check_libraries.py")]).returncode


if __name__ == "__main__":
    sys.exit(main())
