"""Read the lid document's tables and the lid's interface.

Shared by make_lid.py, check_lid.py and make_lid_outputs.py, so that a value has one home:
- design/mechanical/LID_Rev0.2.md holds the lid's own choices (its parameter and legend tables);
- design/mechanical/assembly/UsbPowerHub_Enclosure_Rev0.5_LidInterface.json, which
  make_enclosure.py writes, holds the outline, the holes, the windows and the ports.
Pure Python: no pcbnew here, so the tables can be read by any interpreter.
"""
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[3]
MECH = ROOT / "design" / "mechanical"
DOC = MECH / "LID_Rev0.2.md"
INTERFACE = MECH / "assembly" / "UsbPowerHub_Enclosure_Rev0.5_LidInterface.json"
SOURCE = MECH / "lid"                      # the KiCad project make_lid.py writes
WORKING = ROOT / "manufacturing" / "working" / "lid-rev0.2"
NICK = "usb-power-hub-lid"
PRODUCT = "USB Power-Control Hub"
REVISION = "Rev0.2"
PREFIX = "UsbPowerHub_Lid_Rev0.2"
ORIGIN = (50.0, 122.0)                     # the lid's lower-left corner on KiCad's sheet, as the main board's
DIGEST_TAG = "inputs sha256 "              # the title block comment that names the inputs (L01)
SIDES = ("top", "bottom")
LEGEND_COLUMNS = ("Label", "Side", "Text", "Anchor", "dx", "dy", "Height", "Stroke")


def _table(text, tag):
    m = re.search(rf"<!-- {tag}:begin -->\n(.*?)<!-- {tag}:end -->", text, re.S)
    if not m:
        raise ValueError(f"no {tag} table in the lid document")
    rows = []
    for line in m.group(1).splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] in ("Name", "Label") or set(cells[0]) <= set("-: "):
            continue
        rows.append(cells)
    return rows


def load_doc(path=DOC):
    """Return (params, legend): name -> number, and the legend rows as dicts in table order.
    A legend row keeps its cells as written, plus dx, dy, height and stroke as floats."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    params = {}
    for cells in _table(text, "lid-params"):
        name = cells[0].strip("`")
        if name in params:
            raise ValueError(f"parameter {name} is listed twice")
        params[name] = float(cells[1])
    legend = []
    for cells in _table(text, "lid-legend"):
        if len(cells) != len(LEGEND_COLUMNS):
            raise ValueError(f"legend row {cells[0]}: {len(cells)} cells, want {len(LEGEND_COLUMNS)}")
        row = dict(zip((c.lower() for c in LEGEND_COLUMNS), cells))
        for key in ("dx", "dy", "height", "stroke"):
            row[key] = float(row[key])
        legend.append(row)
    return params, legend


def load_interface(path=INTERFACE):
    data = json.loads(pathlib.Path(path).read_text(encoding="ascii"))
    data["hole_by_ref"] = {h["ref"]: h for h in data["holes"]}
    data["port_by_ref"] = {p["ref"]: p for p in data["ports"]}
    return data


def inputs_digest(params, legend, interface_path=INTERFACE):
    """SHA-256 of what the board is built from: the two tables' values and the interface file.
    The document's prose may change; a value may not."""
    text = json.dumps({"params": params, "legend": legend,
                       "interface": hashlib.sha256(pathlib.Path(interface_path).read_bytes()).hexdigest()},
                      sort_keys=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def edge_y(interface, port):
    """y of the lid's edge a port lies under: the front edge is y0, the back edge y1."""
    o = interface["outline"]
    return o["y0"] if port["edge"] == "front" else o["y1"]


def inward(port):
    """+1 or -1: the y direction from a port's edge into the lid."""
    return 1.0 if port["edge"] == "front" else -1.0


def label_point(interface, row):
    """Where a legend row's text is anchored (its centre), in the board frame.
    Anchor `centre`: the lid's centre, plus (dx, dy).
    Anchor a hole: the hole's centre, plus (dx, dy).
    Anchor a port: the point of the lid's edge above the port, dx along the edge and dy into the lid."""
    a = row["anchor"]
    o = interface["outline"]
    if a == "centre":
        return (o["x0"] + o["x1"]) / 2 + row["dx"], (o["y0"] + o["y1"]) / 2 + row["dy"]
    if a in interface["hole_by_ref"]:
        h = interface["hole_by_ref"][a]
        return h["x"] + row["dx"], h["y"] + row["dy"]
    if a in interface["port_by_ref"]:
        p = interface["port_by_ref"][a]
        return p["x"] + row["dx"], edge_y(interface, p) + inward(p) * row["dy"]
    raise ValueError(f"legend row {row['label']}: anchor {a} is neither `centre`, a hole nor a port of the interface")
