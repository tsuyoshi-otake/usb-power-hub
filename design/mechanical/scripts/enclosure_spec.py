"""Read the enclosure document's tables and the board interface.

Shared by make_enclosure.py, check_enclosure.py and render_enclosure.py, so that
a parameter has one home: design/mechanical/ENCLOSURE_Rev0.2.md. Pure Python.
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
MECH = ROOT / "design" / "mechanical"
DOC = MECH / "ENCLOSURE_Rev0.2.md"
INTERFACE = MECH / "reference" / "board_interface_Rev0.6.json"
ASSEMBLY = MECH / "assembly"
REPORTS = MECH / "reports"
PREFIX = "UsbPowerHub_Enclosure_Rev0.2_"
MANIFEST = f"{PREFIX}Manifest.json"


def source_tag(manifest_path):
    """What a picture carries to name the build it was drawn from (checked as E16)."""
    data = pathlib.Path(manifest_path).read_bytes()
    return f"{MANIFEST} sha256 {hashlib.sha256(data).hexdigest()}"


def _table(text, tag):
    m = re.search(rf"<!-- {tag}:begin -->\n(.*?)<!-- {tag}:end -->", text, re.S)
    if not m:
        raise ValueError(f"no {tag} table in the enclosure document")
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("Name", "Footprint") or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def load_doc(path=DOC):
    """Return (params, heights): name -> mm, footprint name -> mm."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    params = {}
    for cells in _table(text, "params"):
        name = cells[0].strip("`")
        if name in params:
            raise ValueError(f"parameter {name} is listed twice")
        params[name] = float(cells[1])
    heights = {}
    for cells in _table(text, "heights"):
        name = cells[0].strip("`")
        if name in heights:
            raise ValueError(f"footprint {name} is listed twice")
        heights[name] = float(cells[1])
    return params, heights


def inputs_digest(params, heights):
    """SHA-256 of the two input tables' values: prose may change, a value may not."""
    text = json.dumps({"params": params, "heights": heights}, sort_keys=True)
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def load_derived(path=DOC):
    """The document's derived-figures table: name -> value."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return {cells[0].strip("`"): float(cells[1]) for cells in _table(text, "derived")}


def write_derived(table, path=DOC):
    path = pathlib.Path(path)
    text = path.read_text(encoding="utf-8")
    a = text.index("<!-- derived:begin -->") + len("<!-- derived:begin -->\n")
    b = text.index("<!-- derived:end -->")
    path.write_text(text[:a] + table + text[b:], encoding="utf-8", newline="\n")


def load_interface(path=INTERFACE):
    data = json.loads(pathlib.Path(path).read_text(encoding="ascii"))
    data["by_ref"] = {f["ref"]: f for f in data["footprints"]}
    return data


def footprint_name(fp):
    return fp["footprint"].split(":", 1)[1]


def receptacles(board):
    """J1-J4 as dicts: ref, cx (x of the opening's centre), edge 'front' (y = 0) or 'back'."""
    out = []
    width = board["outline"]["y1"] - board["outline"]["y0"]
    for fp in board["footprints"]:
        if footprint_name(fp).startswith("USB_C_Receptacle"):
            out.append({"ref": fp["ref"], "cx": fp["x"],
                        "edge": "front" if fp["y"] < width / 2 else "back"})
    return sorted(out, key=lambda r: r["ref"])


def mounting_holes(board):
    return sorted(((f["ref"], f["x"], f["y"]) for f in board["footprints"]
                   if footprint_name(f).startswith("MountingHole")), key=lambda h: h[0])


def switches(board):
    """Tact switches as (ref, x, y); a port button is one with two LEDs within 10 mm."""
    sw = [(f["ref"], f["x"], f["y"]) for f in board["footprints"]
          if footprint_name(f).startswith("SW_Push")]
    leds = [(f["ref"], f["x"], f["y"]) for f in board["footprints"]
            if footprint_name(f).startswith("LED_")]
    ports, others = [], []
    for ref, x, y in sorted(sw):
        near = sorted(l for l in leds if abs(l[1] - x) < 10 and abs(l[2] - y) < 10)
        (ports if len(near) == 2 else others).append({"ref": ref, "x": x, "y": y, "leds": near})
    return ports, others
