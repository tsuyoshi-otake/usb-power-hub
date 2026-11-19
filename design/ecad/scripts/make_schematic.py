"""Write the Rev0.6 schematic (issue #6 P2) from the netlist document.

Run with KiCad's own Python from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_schematic.py

Input:
- design/circuit/CIRCUIT_DESIGN_Rev0.6_netlist.md: every part, pin and net, in the tables
  between its `<!-- ...:begin -->` / `<!-- ...:end -->` markers;
- design/ecad/libraries/usb-power-hub.kicad_sym: the project symbols, embedded unchanged,
  PWR_FLAG (the ERC driver marker, schematic-only) included.
Output, in design/ecad/source/:
- usb-power-hub.kicad_sch: the root sheet, one sheet block per netlist sheet;
- power, mcu, hub, adc, channel_a and channel_b .kicad_sch.

Every pin ends in a 2.54 mm wire and a global label that carries its net name, or in a
no-connect flag; no wire runs between two parts. Pins that share one position in a symbol
(U1's IOVDD and DVDD, a crystal's two G pins) share one label. Parts are packed in rows in
table order. A passive takes its footprint, value, MPN, manufacturer and LCSC number from
the passive table through its `Order`; every other part keeps its symbol's properties and
the table's Value. A part whose Order is `none` (test pads, fiducials, holes, the
footprint-only SWD connector) is not in the BOM. UUIDs are derived from names (uuid5), so
a re-run writes the same bytes.

Then it runs check_schematic.py, which compares the netlist KiCad exports from these files
with the document. Exit status: 0 = written and checked; 1 = a check failed.

What it CANNOT see: whether the document's circuit is right (CIRCUIT_DESIGN_Rev0.6.md and
its _calc.py decide that), and the readability of the drawing. A sheet made of labels shows
connectivity, not signal flow.
"""
import copy
import importlib.util
import pathlib
import re
import subprocess
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DOC = ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.6_netlist.md"
LIB = ROOT / "design" / "ecad" / "libraries" / "usb-power-hub.kicad_sym"
OUT = ROOT / "design" / "ecad" / "source"
NICK = "usb-power-hub"
FLAG = "PWR_FLAG"
SHEETS = ("power", "mcu", "hub", "adc", "channel_a", "channel_b")
SHEET_TITLES = {"power": "J1, J4, rails, V_INJ, VREF_CHK, comparator threshold",
                "mcu": "U1 RP2040, U8 flash, Y1, SWD", "hub": "U6 CH335F, Y2, data-line taps",
                "adc": "U7, U17 MCP3208, SPI level shifters, U30 OC comparators",
                "channel_a": "Port A: switch, ladder, mirrors, comparators, J2",
                "channel_b": "Port B: switch, ladder, mirrors, comparators, J3"}
GRID = 2.54
STUB = 2.54
FONT = 1.27
PAPERS = (("A3", 420.0, 297.0), ("A2", 594.0, 420.0), ("A1", 841.0, 594.0))
MARGIN, BOTTOM = 15.24, 45.72         # frame margin; bottom band kept clear of the title block
GAP = 5.08                            # between packed items


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")
S = sx.Sym
proj = _load("make_project")          # title block, UUID namespace, project name


def uid(*parts):
    return str(uuid.uuid5(proj.UUID_NS, "sch/" + "/".join(str(p) for p in parts)))


# ---- the netlist document ------------------------------------------------------------------
def doc_tables(text):
    """[(kind, argument, [row dict])] for every marked table, in document order."""
    out = []
    for m in re.finditer(r"<!-- (\w+):begin(?: ([^>]*?))? -->\n(.*?)<!-- \1:end -->", text, re.S):
        kind, arg, body = m.groups()
        lines = [ln for ln in body.splitlines() if ln.startswith("|")]
        head = [c.strip() for c in lines[0].strip().strip("|").split("|")]
        rows = []
        for ln in lines[2:]:
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if len(cells) != len(head):
                raise SystemExit(f"netlist table {kind} {arg}: row has {len(cells)} cells: {ln}")
            rows.append(dict(zip(head, cells)))
        out.append((kind, arg or "", rows))
    return out


def parse_pins(cell, where):
    if cell in ("—", "-", ""):
        return {}
    pins = {}
    for tok in cell.split():
        num, sep, net = tok.partition("=")
        if not sep or not num or not net or num in pins:
            raise SystemExit(f"{where}: bad pin token {tok!r}")
        pins[num] = net
    return pins


def read_doc(path=DOC):
    parts, passives, flags = {}, {}, []
    for kind, arg, rows in doc_tables(path.read_text(encoding="utf-8")):
        if kind == "passives":
            for r in rows:
                passives[r["Order"]] = r
        elif kind == "flags":
            flags += rows
        elif kind == "netlist":
            sheets = arg.removeprefix("sheet=").split(",")
            for r in rows:
                refs = [r["Ref"]] if "Ref" in r else [r["Ref A"], r["Ref B"]]
                if len(refs) != len(sheets):
                    raise SystemExit(f"netlist {arg}: {len(refs)} refs for {len(sheets)} sheets")
                for ref, sheet, x in zip(refs, sheets, "AB"):
                    if ref in parts:
                        raise SystemExit(f"{ref} appears twice")
                    pins = parse_pins(r["Pins"], ref)
                    parts[ref] = {"ref": ref, "sheet": sheet, "symbol": r["Symbol"],
                                  "value": r["Value"], "order": r["Order"],
                                  "pins": {n: v.replace("{x}", x) for n, v in pins.items()}}
        else:
            raise SystemExit(f"unknown table kind {kind}")
    return parts, passives, flags


# ---- the symbol library ----------------------------------------------------------------------
class Pin:
    def __init__(self, node, unit):
        at = sx.first(node, "at")
        self.num = sx.first(node, "number")[1]
        self.etype = str(node[1])
        self.x, self.y, self.angle = float(at[1]), float(at[2]), int(at[3]) % 360
        self.unit = unit

    def end(self, ox, oy):
        """The connection point on the sheet (the library's Y axis points up)."""
        return (round(ox + self.x, 4), round(oy - self.y, 4))

    def outward(self):
        return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[self.angle]


class LibSymbol:
    def __init__(self, node):
        self.node = node
        self.name = node[1]
        self.pins, self.points = {}, {}
        self.units = 1
        for sub in sx.find(node, "symbol"):
            m = re.fullmatch(re.escape(self.name) + r"_(\d+)_(\d+)", sub[1])
            unit, style = int(m.group(1)), int(m.group(2))
            if style > 1:
                continue                         # De Morgan bodies are not used
            self.units = max(self.units, unit)
            for p in sx.find(sub, "pin"):
                pin = Pin(p, unit)
                self.pins.setdefault(pin.num, pin)
            self.points.setdefault(unit, []).extend(graphic_points(sub))
        self.props = {p[1]: p for p in sx.find(node, "property")
                      if not (isinstance(p[1], S) and p[1] == "private")}   # library-only
        self.in_bom = str(sx.first(node, "in_bom")[1]) == "yes"

    def unit_pins(self, unit):
        return [p for p in self.pins.values() if p.unit in (0, unit)]

    def unit_points(self, unit):
        return self.points.get(0, []) + self.points.get(unit, [])


def graphic_points(sub):
    pts = []
    for head in ("rectangle", "polyline", "arc", "circle", "text", "bezier"):
        for g in sx.walk(sub, head):
            if head == "circle":
                c, r = sx.first(g, "center"), float(sx.first(g, "radius")[1])
                pts += [(c[1] - r, c[2] - r), (c[1] + r, c[2] + r)]
                continue
            for key in ("start", "end", "mid", "at"):
                n = sx.first(g, key)
                if n:
                    pts.append((n[1], n[2]))
            for xy in sx.walk(g, "xy"):
                pts.append((xy[1], xy[2]))
    for p in sx.walk(sub, "pin"):
        at = sx.first(p, "at")
        pts.append((at[1], at[2]))
    return [(float(x), float(y)) for x, y in pts]


def load_library():
    lib = sx.loads(LIB.read_text(encoding="utf-8"))
    return {s[1]: LibSymbol(s) for s in sx.find(lib, "symbol")}


# ---- schematic nodes ---------------------------------------------------------------------------
def effects(size=FONT, justify=None, hide=False):
    e = ["effects", ["font", ["size", size, size]]]
    if justify:
        e.append(["justify", *[S(j) for j in justify.split()]])
    if hide:
        e.append(["hide", S("yes")])
    return e


def label_width(text):
    return len(text) * FONT * 0.9 + 4.0


def global_label(net, x, y, direction, key):
    angle = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[direction]
    just = "left" if angle in (0, 90) else "right"
    return ["global_label", net, ["shape", S("passive")], ["at", x, y, angle],
            ["fields_autoplaced", S("yes")], effects(justify=just), ["uuid", uid(key, "label")],
            ["property", "Intersheetrefs", "${INTERSHEET_REFS}", ["at", x, y, angle],
             effects(justify=just, hide=True)]]


def wire(a, b, key):
    return ["wire", ["pts", ["xy", *a], ["xy", *b]], ["stroke", ["width", 0], ["type", S("default")]],
            ["uuid", uid(key, "wire")]]


def no_connect(pt, key):
    return ["no_connect", ["at", *pt], ["uuid", uid(key, "nc")]]


def instance_props(lsym, ox, oy, overrides):
    """The library's properties at their library offsets, with the instance's values."""
    out = []
    for name, p in lsym.props.items():
        if name.startswith("ki_"):
            continue
        at = sx.first(p, "at")
        node = ["property", name, overrides.pop(name, p[2]),
                ["at", round(ox + at[1], 4), round(oy - at[2], 4), at[3]],
                copy.deepcopy(sx.first(p, "effects"))]
        out.append(node)
    for name, value in overrides.items():                 # properties the library lacks
        out.append(["property", name, value, ["at", ox, oy, 0], effects(hide=True)])
    return out


class Item:
    """One placed symbol unit with its stubs, labels and flags, in local coordinates."""

    def __init__(self, ref, lsym, unit, pins_to_nets, lib_id, values, in_bom, sheet):
        self.ref, self.lsym, self.unit, self.lib_id = ref, lsym, unit, lib_id
        self.values, self.in_bom, self.sheet = values, in_bom, sheet
        self.nets = pins_to_nets
        groups = {}
        for pin in lsym.unit_pins(unit):
            groups.setdefault(pin.end(0, 0), []).append(pin)
        self.groups = groups
        for pt, pins in groups.items():
            nets = {pins_to_nets[p.num] for p in pins}
            if len(nets) != 1:
                raise SystemExit(f"{ref}: pins {[p.num for p in pins]} share a position but not a net: {nets}")
        xs, ys = [], []
        for x, y in lsym.unit_points(unit):
            xs.append(x)
            ys.append(-y)
        for (x, y), pins in groups.items():
            net = pins_to_nets[pins[0].num]
            if net == "NC":
                continue
            dx, dy = pins[0].outward()
            reach = STUB + label_width(net)
            xs.append(x + dx * reach)
            ys.append(y + dy * reach)
            if dx == 0:                          # a vertical label is a font height wide
                xs += [x - FONT, x + FONT]
        for name in ("Reference", "Value"):
            p = lsym.props.get(name)
            if p is not None and sx.first(sx.first(p, "effects"), "hide") is None:
                at = sx.first(p, "at")
                w = len(self.values.get(name, p[2])) * FONT * 0.9 / 2 + 1.0
                xs += [at[1] - w, at[1] + w]
                ys += [-at[2] - FONT, -at[2] + FONT]
        if not xs:
            xs, ys = [-GRID, GRID], [-GRID, GRID]
        self.box = (min(xs), min(ys), max(xs), max(ys))

    def size(self):
        return self.box[2] - self.box[0], self.box[3] - self.box[1]

    def emit(self, ox, oy, project, path):
        """The symbol node plus its wires, labels and no-connect flags at origin (ox, oy)."""
        lsym = self.lsym
        props = instance_props(lsym, ox, oy, dict(self.values))
        sym = ["symbol", ["lib_id", self.lib_id], ["at", ox, oy, 0], ["unit", self.unit],
               ["exclude_from_sim", S("no")], ["in_bom", S("yes" if self.in_bom else "no")],
               ["on_board", S("yes")], ["dnp", S("no")], ["uuid", uid(self.sheet, self.ref, self.unit)]]
        sym += props
        for pin in sorted(lsym.unit_pins(self.unit), key=lambda p: natural(p.num)):
            sym.append(["pin", pin.num, ["uuid", uid(self.sheet, self.ref, "pin", pin.num)]])
        sym.append(["instances", ["project", project,
                                  ["path", path, ["reference", self.ref], ["unit", self.unit]]]])
        extra, points = [], []
        for (x, y), pins in sorted(self.groups.items()):
            net = self.nets[pins[0].num]
            end = (round(ox + x, 4), round(oy + y, 4))
            key = (self.sheet, self.ref, pins[0].num)
            if net == "NC":
                if pins[0].etype != "no_connect":     # a no_connect pin needs no flag
                    extra.append(no_connect(end, key))
                points.append((end, None, "NC"))
                continue
            dx, dy = pins[0].outward()
            tip = (round(end[0] + dx * STUB, 4), round(end[1] + dy * STUB, 4))
            extra.append(wire(end, tip, key))
            extra.append(global_label(net, *tip, (dx, dy), key))
            points.append((end, tip, net))
        return sym, extra, points


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def pack(items):
    """Shelf-pack items into the smallest paper that holds them; returns (paper, origins)."""
    for name, w, h in PAPERS:
        x0, y0, xmax, ymax = MARGIN, MARGIN, w - MARGIN, h - BOTTOM
        x, y, row_h, origins = x0, y0, 0.0, []
        ok = True
        for it in items:
            iw, ih = it.size()
            if x + iw > xmax and x > x0:
                x, y, row_h = x0, y + row_h + GAP, 0.0
            ox, oy = snap(x - it.box[0] + GRID), snap(y - it.box[1] + GRID)
            if ox + it.box[2] > xmax or oy + it.box[3] > ymax:
                ok = False
                break
            origins.append((ox, oy))
            x = ox + it.box[2] + GAP
            row_h = max(row_h, oy + it.box[3] - y)
        if ok:
            return name, origins
    raise SystemExit("the items do not fit on A1")


def check_geometry(sheet, placed):
    """No two nets meet at a point, and no stub passes over another connection point."""
    owner = {}
    for end, tip, net in placed:
        for pt in (end, tip):
            if pt is None:
                continue
            if owner.setdefault(pt, net) != net:
                raise SystemExit(f"{sheet}: {net} and {owner[pt]} meet at {pt}")
    for end, tip, net in placed:
        if tip is None:
            continue
        (x1, y1), (x2, y2) = end, tip
        for (px, py), other in owner.items():
            if (px, py) in (end, tip):
                continue
            if min(x1, x2) <= px <= max(x1, x2) and min(y1, y2) <= py <= max(y1, y2):
                raise SystemExit(f"{sheet}: the {net} stub at {end} crosses {other} at {(px, py)}")


def title_block(sub=None):
    comments = list(proj.COMMENTS) + ([f"Sheet: {sub}"] if sub else [])
    return ["title_block", ["title", proj.TITLE], ["date", proj.DATE], ["rev", proj.REV],
            *[["comment", i + 1, c] for i, c in enumerate(comments)]]


def lib_symbol_node(lsym, lib_id):
    node = copy.deepcopy(lsym.node)
    node[1] = lib_id
    return node


def build_sheet(sheet, parts, passives, syms, flags, root_uuid, sheet_uuid):
    items, used = [], {}
    path = f"/{root_uuid}/{sheet_uuid}"
    for ref, part in parts.items():          # table order
        if part["sheet"] != sheet:
            continue
        lsym = syms[part["symbol"]]
        pins = part["pins"]
        want = set(lsym.pins)
        if set(pins) != want:
            raise SystemExit(f"{ref}: pins {sorted(set(pins) ^ want, key=natural)} differ from "
                             f"symbol {lsym.name}")
        values = {"Reference": ref, "Value": part["value"]}
        if part["symbol"] in ("R", "C"):
            pv = passives.get(part["order"])
            if pv is None or pv["Kind"] != part["symbol"] or pv["Value"] != part["value"]:
                raise SystemExit(f"{ref}: order {part['order']} is not a {part['symbol']} "
                                 f"of {part['value']} in the passive table")
            values.update({"Footprint": f"{NICK}:{pv['Footprint']}", "MPN": pv["MPN"],
                           "Manufacturer": pv["Manufacturer"], "LCSC": part["order"],
                           "Description": f"{pv['Value']} {pv['Rating']}, {pv['Package']}; "
                                          f"{pv['Manufacturer']} {pv['MPN']}; JLCPCB "
                                          f"{part['order']} (Basic)"})
        in_bom = lsym.in_bom and part["order"] != "none"
        lib_id = f"{NICK}:{lsym.name}"
        used[lib_id] = lsym
        for unit in range(1, lsym.units + 1):
            items.append(Item(ref, lsym, unit, pins, lib_id, values, in_bom, sheet))
    for n, f in enumerate(flags, 1):
        if f["Sheet"] != sheet:
            continue
        ref = f"#FLG{n:02d}"
        lib_id = f"{NICK}:{FLAG}"
        used[lib_id] = syms[FLAG]
        items.append(Item(ref, syms[FLAG], 1, {"1": f["Net"]}, lib_id,
                          {"Reference": ref, "Value": "PWR_FLAG"}, True, sheet))
    paper, origins = pack(items)
    body, placed = [], []
    wires = []
    for it, (ox, oy) in zip(items, origins):
        sym, extra, points = it.emit(ox, oy, proj.NAME, path)
        body.append(sym)
        wires += extra
        placed += points
    check_geometry(sheet, placed)
    node = ["kicad_sch", ["version", 20250114], ["generator", "eeschema"],
            ["generator_version", "9.0"], ["uuid", uid("file", sheet)], ["paper", paper],
            title_block(SHEET_TITLES[sheet]),
            ["lib_symbols", *[lib_symbol_node(used[k], k) for k in sorted(used)]]]
    node += wires + body
    return node, paper, len(items)


def build_root(root_uuid, sheet_uuids):
    node = ["kicad_sch", ["version", 20250114], ["generator", "eeschema"],
            ["generator_version", "9.0"], ["uuid", root_uuid], ["paper", "A3"], title_block(),
            ["lib_symbols"]]
    for i, sheet in enumerate(SHEETS):
        x, y = 30.48 + (i % 3) * 120.65, 40.64 + (i // 3) * 60.96
        node.append(["sheet", ["at", x, y], ["size", 88.9, 30.48],
                     ["exclude_from_sim", S("no")], ["in_bom", S("yes")], ["on_board", S("yes")],
                     ["dnp", S("no")], ["stroke", ["width", 0.1524], ["type", S("solid")]],
                     ["fill", ["color", 0, 0, 0, 0.0]], ["uuid", sheet_uuids[sheet]],
                     ["property", "Sheetname", sheet, ["at", x, round(y - 0.7116, 4), 0],
                      effects(justify="left bottom")],
                     ["property", "Sheetfile", f"{sheet}.kicad_sch",
                      ["at", x, round(y + 31.0484, 4), 0], effects(justify="left top")],
                     ["instances", ["project", proj.NAME,
                                    ["path", f"/{root_uuid}", ["page", str(i + 2)]]]]])
    node += [["sheet_instances", ["path", "/", ["page", "1"]]], ["embedded_fonts", S("no")]]
    return node


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:]:
        raise SystemExit("usage: make_schematic.py")
    parts, passives, flags = read_doc()
    syms = load_library()
    unknown = sorted({p["symbol"] for p in parts.values()} - set(syms))
    if unknown:
        raise SystemExit(f"symbols not in the library: {unknown}")
    root_uuid = str(uuid.uuid5(proj.UUID_NS, "sch/root"))      # make_project.py's root sheet
    sheet_uuids = {s: uid("sheet", s) for s in SHEETS}
    stray = sorted({p["sheet"] for p in parts.values()} - set(SHEETS))
    if stray:
        raise SystemExit(f"sheets not in SHEETS: {stray}")
    report = []
    for sheet in SHEETS:
        node, paper, n = build_sheet(sheet, parts, passives, syms, flags, root_uuid,
                                     sheet_uuids[sheet])
        (OUT / f"{sheet}.kicad_sch").write_text(sx.dumps(node) + "\n", encoding="utf-8",
                                                newline="\n")
        report.append(f"{sheet} {paper} {n} items")
    (OUT / f"{NICK}.kicad_sch").write_text(sx.dumps(build_root(root_uuid, sheet_uuids)) + "\n",
                                           encoding="utf-8", newline="\n")
    print(f"wrote {len(parts)} parts on {len(SHEETS)} sheets: " + "; ".join(report))
    sys.stdout.flush()
    checker = HERE / "check_schematic.py"
    if not checker.exists():
        print("check_schematic.py not found: not checked")
        return 1
    return subprocess.run([sys.executable, "-I", "-B", str(checker)]).returncode


if __name__ == "__main__":
    sys.exit(main())
