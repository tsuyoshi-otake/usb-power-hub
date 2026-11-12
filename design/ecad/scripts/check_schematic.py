"""Check the captured schematic against the netlist document (issue #6 P2; CLAUDE.md 8).

Run with KiCad's own Python from the repository root (make_schematic.py runs it after it
writes the schematic):

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_schematic.py
        [--src DIR] [--lib DIR] [--doc FILE] [--circuit FILE] [--parts FILE] [--reports DIR]

--src holds the KiCad project (default design/ecad/source), --lib the project libraries
(default design/ecad/libraries), --doc the netlist document (default
design/circuit/CIRCUIT_DESIGN_Rev0.5_netlist.md), --circuit the circuit document and --parts
requirements/parts.md (the tests pass corrupted copies). With --reports, the ERC report and
the exported netlist are kept there. This file reads the document with its own parser, not the
generator's.

 1. Document: every part's symbol is a register id (library.json) and its pins are exactly
    the register's pin numbers; a non-passive Value is the register's Value (test pads keep
    their net name); an Order is the register's JLCPCB code, `Akizuki <code>` or `none`, and
    a passive's Order is a row of the passive table with the same kind and value; every net
    has at least two pins; every passive row is used; every PWR_FLAG net exists.
 2. Passive bodies: each bound part's body (the passive table, from its sheet) has the EIA
    size its footprint is named for, within 0.05 mm, and on the footprint as pcbnew loads it
    the pads span at least the longest body and leave a gap shorter than the shortest one,
    and are at least as tall as the nominal width. R_L's Kelvin land (RS12, RS22) is checked
    the same way against C17734's body.
 3. Circuit document 6.2: its designators, with channel B's U and RS + 10 and Q + 20, are
    exactly the document's non-passive parts.
 4. requirements/parts.md: its Passives table lists exactly the passive table's LCSC codes,
    each with the same package.
 5. ERC (`kicad-cli sch erc --severity-all`): no violation of any severity, on every sheet.
 6. Netlist (`kicad-cli sch export netlist`): the components are the document's parts, with
    its Value, the register's or the passive table's footprint, LCSC / Akizuki / MPN fields,
    and BOM exclusion exactly for Order `none` and the register's in_bom = false; every pin
    is on the document's net, and a pin the document marks NC is alone on an unconnected
    net; every exported net is a document net.
 7. Net classes: resolved by pcbnew from the project's net settings (the patterns
    make_project.py writes), the nets in USB_HS are exactly the nets on a USB D+/D- pin
    (J1-J3 pins 2-3, U6 DMU/DPU and DM1-DP3, U1 USB_DM/DP) and the nets between two series
    resistors that lie on such nets (the 22 ohm + 5.1 ohm pairs), each with its partner.
Exit status: 0 = every check passed; 1 = at least one failed. Each failure prints as
`FAIL <who>: <what>`.

What it CANNOT see:
- whether the document's circuit is right: that is CIRCUIT_DESIGN_Rev0.5.md and its
  _calc.py. This checker proves only that the schematic carries what the document says.
- pin functions: it compares pin numbers. A symbol with a wrong pin map passes here;
  check_libraries.py (P1) checks the pin names against the datasheets.
- terminal-band dimensions of the passives (their sheets give them, the passive table does
  not), so the land check proves that a body of any length in its tolerance reaches both
  pads, not how much solder fillet it gets.
- placement notes ("at U1 pin 1"): layout (P3) has to honour them.
- the net class in the exported netlist: kicad-cli 9.0.8 writes "Default" there whatever the
  project assigns, so check 7 asks pcbnew instead. Whether eeschema itself shows USB_HS is
  not checked; only the board uses the class.
"""
import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NICK = "usb-power-hub"
KICAD = pathlib.Path(sys.executable).resolve().parents[1]
CLI = KICAD / "bin" / "kicad-cli.exe"
CIRCUIT = ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.5.md"
PARTS_MD = ROOT / "requirements" / "parts.md"
NON_PARTS = {"R", "C", "TestPoint", "Fiducial", "MountingHole"}   # not in circuit 6.2
USB_PINS = {"J1": ("2", "3"), "J2": ("2", "3"), "J3": ("2", "3"),
            "U6": ("6", "7", "8", "9", "13", "14", "20", "21"), "U1": ("46", "47")}
EIA_TOL = 0.051


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sx = _load("sexpr")


class Report:
    def __init__(self):
        self.fails, self.count = [], 0

    def check(self, cond, who, what):
        self.count += 1
        if not cond:
            self.fails.append(f"FAIL {who}: {what}")
        return cond


# ---- the netlist document (own parser) ---------------------------------------------------------
def marked_blocks(text):
    """Yield (kind, argument, header cells, row cell lists) for each marked table."""
    kind = None
    for line in text.splitlines():
        m = re.match(r"<!-- (\w+):(begin|end)(?: (.*?))? -->$", line.strip())
        if m and m.group(2) == "begin":
            kind, arg, rows = m.group(1), m.group(3) or "", []
            continue
        if m and m.group(2) == "end":
            yield kind, arg, rows[0], rows[2:]
            kind = None
            continue
        if kind and line.startswith("|"):
            rows.append([c.strip() for c in line.strip()[1:-1].split("|")])


def read_doc(path):
    parts, passives, flags, order = {}, {}, [], []
    for kind, arg, head, rows in marked_blocks(path.read_text(encoding="utf-8")):
        recs = [dict(zip(head, r)) for r in rows]
        if any(len(r) != len(head) for r in rows):
            raise SystemExit(f"{path.name}: a {kind} row has the wrong cell count")
        if kind == "passives":
            passives.update({r["Order"]: r for r in recs})
        elif kind == "flags":
            flags += recs
        elif kind == "netlist":
            sheets = arg.split("=", 1)[1].split(",")
            for r in recs:
                refs = [r[k] for k in ("Ref", "Ref A", "Ref B") if k in r]
                for ref, sheet, ch in zip(refs, sheets, ("A", "B")):
                    pins = {}
                    if r["Pins"] not in ("—", "-"):
                        for tok in r["Pins"].split():
                            num, net = tok.split("=", 1)
                            pins[num] = net.replace("{x}", ch)
                    if ref in parts:
                        raise SystemExit(f"{path.name}: {ref} twice")
                    parts[ref] = dict(sheet=sheet, symbol=r["Symbol"], value=r["Value"],
                                      order=r["Order"], pins=pins)
                    order.append(ref)
    return parts, passives, flags


def doc_nets(parts):
    nets = {}
    for ref, p in parts.items():
        for num, net in p["pins"].items():
            if net != "NC":
                nets.setdefault(net, set()).add((ref, num))
    return nets


def register_value(reg):
    return reg.get("value", reg["id"])


def register_order(reg):
    o = reg["order"]
    if o["vendor"] == "JLCPCB":
        return o["code"]
    if o["vendor"] == "Akizuki":
        return f"Akizuki {o['code']}"
    return "none"


def register_footprints(reg):
    fp = reg["footprint"]
    if "none" in fp:
        return []
    if "make" in fp:
        return [fp["name"]]
    stock = fp["stock"] if isinstance(fp["stock"], list) else [fp["stock"]]
    return [s.split(":")[1] for s in stock]


def check_document(rep, parts, passives, flags, register):
    for ref, p in parts.items():
        reg = register.get(p["symbol"])
        if not rep.check(reg is not None, ref, f"symbol {p['symbol']} is not in library.json"):
            continue
        rep.check(set(p["pins"]) == set(reg["pins"]), ref,
                  f"pins {sorted(set(p['pins']) ^ set(reg['pins']))} differ from the register's")
        if p["symbol"] in ("R", "C"):
            pv = passives.get(p["order"])
            rep.check(pv is not None and pv["Kind"] == p["symbol"] and pv["Value"] == p["value"],
                      ref, f"{p['symbol']} {p['value']} ordered as {p['order']}, which the passive "
                      "table does not list with that kind and value")
        else:
            if p["symbol"] != "TestPoint":
                rep.check(p["value"] == register_value(reg), ref,
                          f"Value {p['value']!r}, the register's is {register_value(reg)!r}")
            rep.check(p["order"] == register_order(reg), ref,
                      f"Order {p['order']!r}, the register's is {register_order(reg)!r}")
    for net, nodes in sorted(doc_nets(parts).items()):
        rep.check(len(nodes) >= 2, net, f"only one pin: {sorted(nodes)}")
    used = {p["order"] for p in parts.values()}
    for order in passives:
        rep.check(order in used, order, "passive table row is used by no part")
    nets = doc_nets(parts)
    for f in flags:
        rep.check(f["Net"] in nets, "flags", f"PWR_FLAG net {f['Net']} is not a document net")


# ---- passive bodies on their footprints ---------------------------------------------------------
def dims(cell):
    """'1.00±0.10 × 0.50±0.05' -> [(nominal, min, max), (nominal, min, max)]."""
    out = []
    for m in re.finditer(r"([\d.]+)(?:±([\d.]+)|\+([\d.]+)/[−-]([\d.]+))", cell):
        nom = float(m.group(1))
        plus = float(m.group(2) or m.group(3))
        minus = float(m.group(2) or m.group(4))
        out.append((nom, nom - minus, nom + plus))
    return out


def pad_boxes(fp):
    out = []
    for pad in fp.Pads():
        bb = pad.GetBoundingBox()
        out.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetRight()),
                    pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetBottom())))
    return out


def check_body(rep, who, fp_name, body, pretty):
    m = re.search(r"_(\d{2})(\d{2})Metric", fp_name)
    (ln, lmin, lmax), (wn, wmin, wmax) = body
    if m:
        el, ew = int(m.group(1)) / 10, int(m.group(2)) / 10
        rep.check(abs(ln - el) <= EIA_TOL and abs(wn - ew) <= EIA_TOL + 0.05 * (ew == 1.2), who,
                  f"body {ln} x {wn} mm is not the {fp_name} size {el} x {ew} mm")
    fp = pcbnew.FootprintLoad(str(pretty), fp_name)
    if not rep.check(fp is not None, who, f"pcbnew cannot load {fp_name}"):
        return
    boxes = pad_boxes(fp)
    left = [b for b in boxes if (b[0] + b[1]) / 2 < 0]
    right = [b for b in boxes if (b[0] + b[1]) / 2 > 0]
    if not rep.check(left and right, who, f"{fp_name}: pads are not on both sides"):
        return
    span = max(b[1] for b in right) - min(b[0] for b in left)
    gap = min(b[0] for b in right) - max(b[1] for b in left)
    rep.check(span >= lmax - 1e-6, who, f"{fp_name}: pads span {span:.3f} mm < longest body {lmax} mm")
    rep.check(gap < lmin, who, f"{fp_name}: pad gap {gap:.3f} mm >= shortest body {lmin} mm")
    if len(left) == 1:
        height = min(b[3] - b[2] for b in boxes)
        rep.check(height >= wn - 1e-6, who, f"{fp_name}: pads {height:.3f} mm tall < body width {wn} mm")


def check_passive_lands(rep, parts, passives, register, pretty):
    for order, pv in sorted(passives.items()):
        body = dims(pv["Body L × W (mm)"])
        if not rep.check(len(body) == 2, order, f"body {pv['Body L × W (mm)']!r} is not L × W"):
            continue
        if not rep.check(pv["Kind"] in ("R", "C"), order, f"kind {pv['Kind']!r} is not R or C"):
            continue
        stock = register_footprints(register[pv["Kind"]])
        rep.check(pv["Footprint"] in stock, order, f"footprint {pv['Footprint']} is not one of the "
                  f"register's {pv['Kind']} footprints")
        code = re.search(r"_(\d{4})Metric", pv["Footprint"])
        eia = {"1005": "0402", "1608": "0603", "2012": "0805"}.get(code.group(1) if code else "")
        rep.check(eia == pv["Package"], order, f"package {pv['Package']} on {pv['Footprint']}")
        check_body(rep, order, pv["Footprint"], body, pretty)
    for ref, p in parts.items():
        if p["symbol"] == "R_Shunt_0805":
            pv = passives.get(p["order"])
            if rep.check(pv is not None, ref, f"{p['order']} is not in the passive table"):
                check_body(rep, ref, register_footprints(register[p["symbol"]])[0],
                           dims(pv["Body L × W (mm)"]), pretty)


# ---- the circuit document and parts.md ----------------------------------------------------------
def section(text, start, stop):
    a = text.index(start)
    return text[a:text.index(stop, a)]


def check_designators(rep, parts, circuit):
    sec = section(circuit, "### 6.2 Designators", "### 6.3")
    refs = set()
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not line.startswith("| ") or cells[0] in ("Ref", "—") or set(cells[0]) <= set("-"):
            continue
        refs |= {r.strip() for r in cells[0].split(",")}
    for r in list(refs):                     # channel B: U and RS + 10, Q + 20 (6.2's own rule)
        m = re.fullmatch(r"(U|RS|Q)(\d+)", r)
        if m:
            kind, n = m.group(1), int(m.group(2))
            if (kind in ("U", "RS") and 10 <= n <= 16) or (kind == "Q" and 10 <= n <= 29):
                refs.add(f"{kind}{n + (20 if kind == 'Q' else 10)}")
    have = {r for r, p in parts.items() if p["symbol"] not in NON_PARTS}
    rep.check(refs == have, "circuit 6.2", f"designators only in 6.2: {sorted(refs - have)}; "
              f"only in the netlist document: {sorted(have - refs)}")


def check_parts_md(rep, passives, parts_md):
    sec = section(parts_md, "### Passives (Basic, by value)", "\n**")
    rows = [[c.strip() for c in line.strip().strip("|").split("|")]
            for line in sec.splitlines() if line.startswith("|")]
    if not rep.check(len(rows) > 2 and {"LCSC", "Package"} <= set(rows[0]), "parts.md",
                     "the Passives table has no LCSC and Package columns"):
        return
    col, pkg_col = rows[0].index("LCSC"), rows[0].index("Package")
    listed = {r[col]: r[pkg_col] for r in rows[2:]}
    rep.check(set(listed) == set(passives), "parts.md", f"Passives lists {sorted(set(listed) - set(passives))} "
              f"that the netlist document does not, and lacks {sorted(set(passives) - set(listed))}")
    for order, pkg in listed.items():
        if order in passives:
            rep.check(pkg == passives[order]["Package"], "parts.md",
                      f"{order} is {pkg} there, {passives[order]['Package']} in the passive table")


# ---- kicad-cli: ERC and the exported netlist ----------------------------------------------------
def run(args):
    r = subprocess.run([str(CLI), *args], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=600)
    return r.returncode, r.stdout + r.stderr


def check_erc(rep, root_sch, out):
    status, log = run(["sch", "erc", "--format", "json", "--severity-all", "--units", "mm",
                       "-o", str(out), str(root_sch)])
    if not rep.check(out.exists(), "ERC", f"kicad-cli wrote no report (exit {status}): {log[-300:]}"):
        return
    report = json.loads(out.read_text(encoding="utf-8"))
    sheets = [s["path"] for s in report["sheets"]]
    rep.check(len(sheets) == 7, "ERC", f"checked {len(sheets)} sheets: {sheets}")
    for s in report["sheets"]:
        for v in s["violations"]:
            items = "; ".join(i["description"] for i in v["items"])
            rep.check(False, "ERC", f"{v['severity']} {v['type']} on {s['path']}: {items}")


def read_netlist(path):
    tree = sx.loads(path.read_text(encoding="utf-8"))
    comps = {}
    for c in sx.walk(sx.first(tree, "components"), "comp"):
        fields = {f[1][1]: f[2] for f in sx.find(sx.first(c, "fields") or [], "field")
                  if len(f) > 2}
        props = {sx.first(p, "name")[1] for p in sx.find(c, "property")}
        comps[sx.first(c, "ref")[1]] = dict(value=sx.first(c, "value")[1],
                                           footprint=(sx.first(c, "footprint") or [None, ""])[1],
                                           fields=fields, no_bom="exclude_from_bom" in props)
    nets = {}
    for n in sx.find(sx.first(tree, "nets"), "net"):
        nodes = {(sx.first(x, "ref")[1], sx.first(x, "pin")[1]) for x in sx.find(n, "node")}
        nets[sx.first(n, "name")[1]] = dict(nodes=nodes)
    return comps, nets


def check_netlist(rep, parts, passives, register, comps, nets):
    rep.check(set(comps) == set(parts), "netlist", f"components only in the export: "
              f"{sorted(set(comps) - set(parts))}; only in the document: {sorted(set(parts) - set(comps))}")
    pin_net = {}
    for name, n in nets.items():
        for node in n["nodes"]:
            pin_net[node] = name
    for ref, p in parts.items():
        c, reg = comps.get(ref), register.get(p["symbol"])
        if c is None or reg is None:             # reported above: missing part, unknown symbol
            continue
        rep.check(c["value"] == p["value"], ref, f"Value {c['value']!r}, the document's {p['value']!r}")
        want_fp = None
        if p["symbol"] in ("R", "C"):
            rep.check(c["fields"].get("LCSC") == p["order"], ref, f"LCSC {c['fields'].get('LCSC')!r}")
            pv = passives.get(p["order"])        # None: check_document reported the order
            if pv:
                want_fp = f"{NICK}:{pv['Footprint']}"
                rep.check(c["fields"].get("MPN") == pv["MPN"], ref, f"MPN {c['fields'].get('MPN')!r}")
        else:
            fps = register_footprints(reg)
            want_fp = f"{NICK}:{fps[0]}" if fps else ""
            o = reg["order"]
            if o["vendor"] == "JLCPCB":
                rep.check(c["fields"].get("LCSC") == o["code"], ref, f"LCSC {c['fields'].get('LCSC')!r}")
            if o["vendor"] == "Akizuki":
                rep.check(c["fields"].get("Akizuki") == o["code"], ref, f"Akizuki {c['fields'].get('Akizuki')!r}")
        if want_fp is not None:
            rep.check(c["footprint"] == want_fp, ref, f"footprint {c['footprint']!r}, want {want_fp!r}")
        want_no_bom = p["order"] == "none" or reg["symbol"].get("in_bom") is False
        rep.check(c["no_bom"] == want_no_bom, ref, f"excluded from BOM: {c['no_bom']}, want {want_no_bom}")
        for num, net in sorted(p["pins"].items()):
            got = pin_net.get((ref, num))
            if net == "NC":
                rep.check(got is not None and got.startswith("unconnected-(")
                          and len(nets[got]["nodes"]) == 1, f"{ref}.{num}",
                          f"marked NC but on net {got!r}")
            else:
                rep.check(got == net, f"{ref}.{num}", f"on net {got!r}, the document says {net!r}")
    dnets = doc_nets(parts)
    for name, n in sorted(nets.items()):
        if name.startswith("unconnected-("):
            continue
        if rep.check(name in dnets, name, "exported net is not a document net"):
            rep.check(n["nodes"] == dnets[name], name, f"pins {sorted(n['nodes'] ^ dnets[name])} differ")


def check_netclasses(rep, parts, nets, board_path):
    """Resolve each exported net through the project's net settings, as pcbnew will.

    The export's own (class ...) is not evidence: kicad-cli 9.0.8 writes "Default" there even
    for a net named in .kicad_pro netclass_assignments (tried 2026-11-04).
    """
    settings = pcbnew.LoadBoard(str(board_path)).GetDesignSettings().m_NetSettings
    on_pin = {net for ref, pins in USB_PINS.items() for num in pins
              if (net := parts.get(ref, {}).get("pins", {}).get(num)) not in (None, "NC")}
    want = set(on_pin)
    for name, n in nets.items():                 # the node between two series resistors
        refs = {r for r, _ in n["nodes"]}
        if len(n["nodes"]) == 2 and all(parts.get(r, {}).get("symbol") == "R" for r in refs):
            others = {net for r in refs for num, net in parts[r]["pins"].items() if net != name}
            if others <= on_pin:
                want.add(name)
    got = {name for name in nets if settings.GetEffectiveNetClass(name).GetName() == "USB_HS"}
    rep.check(got == want, "USB_HS", f"in the class but no USB pair: {sorted(got - want)}; "
              f"USB pair outside the class: {sorted(want - got)}")
    for name in sorted(got):
        partner = re.sub(r"_P$", "_N", name) if name.endswith("_P") else re.sub(r"_N$", "_P", name)
        rep.check(partner in got, name, f"no partner {partner} in USB_HS")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", type=pathlib.Path, default=ROOT / "design" / "ecad" / "source")
    ap.add_argument("--lib", type=pathlib.Path, default=ROOT / "design" / "ecad" / "libraries")
    ap.add_argument("--doc", type=pathlib.Path,
                    default=ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.5_netlist.md")
    ap.add_argument("--circuit", type=pathlib.Path, default=CIRCUIT)
    ap.add_argument("--parts", type=pathlib.Path, default=PARTS_MD)
    ap.add_argument("--reports", type=pathlib.Path)
    a = ap.parse_args(argv[1:])
    rep = Report()
    register = {p["id"]: p for p in json.loads((a.lib / "library.json").read_text(encoding="utf-8"))["parts"]}
    parts, passives, flags = read_doc(a.doc)
    check_document(rep, parts, passives, flags, register)
    check_passive_lands(rep, parts, passives, register, a.lib / f"{NICK}.pretty")
    check_designators(rep, parts, a.circuit.read_text(encoding="utf-8"))
    check_parts_md(rep, passives, a.parts.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(a.reports) if a.reports else pathlib.Path(tmp)
        out.mkdir(parents=True, exist_ok=True)
        root = a.src / f"{NICK}.kicad_sch"
        check_erc(rep, root, out / "erc.json")
        net_path = out / f"{NICK}.net"
        status, log = run(["sch", "export", "netlist", "--format", "kicadsexpr", "-o", str(net_path),
                           str(root)])
        if rep.check(net_path.exists(), "netlist", f"kicad-cli exported nothing (exit {status}): {log[-300:]}"):
            comps, nets = read_netlist(net_path)
            check_netlist(rep, parts, passives, register, comps, nets)
            check_netclasses(rep, parts, nets, a.src / f"{NICK}.kicad_pcb")
    for line in rep.fails:
        print(line)
    print(f"{rep.count} checks, {len(rep.fails)} failed: {'FAIL' if rep.fails else 'PASS'}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
