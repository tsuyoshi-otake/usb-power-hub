"""Independent check of a candidate manufacturing set, part 2: codes and positions (stdlib only).

independent_check_sets.py reads counts, sides, the outline, the fiducials, the designator sets and
the test-pad labels. Every one of its 30 checks passes with another revision's CPL beside this
board: it reads no position. A layout revision moves parts (Rev0.6, issue #13, D39: 31 of them), so
this part reads positions. It takes the board's text, by regex, as the reference, and compares the
files JLCPCB receives with it:

  X1  the BOM, the CPL and the hand-solder list name exactly the board's parts, with its codes
  X5  no designator is listed twice
  X2  every CPL point is the footprint's origin, plus the documented JLCPCB model shift
  X3  every CPL rotation is the footprint's angle, plus the documented JLCPCB model turn
  X4  every paste pad of the board has its own flash in the Top paste Gerber, and no flash is left
  X6  every hole of the board (via, plated pad, slot, non-plated pad) has its own hit in the right
      drill file, at its position, with its diameter, and no hit is left

It then corrupts in-memory copies and requires each corruption to fail the check it aims at (a
checker never seen failing is not evidence). Three corruptions put the previous release's files in
the place of this set's: its CPL, its Gerber zip, and its two drill files inside this zip.

Independent means: it imports nothing from this directory and no KiCad module, and it reads the
files JLCPCB receives, not what make_outputs.py meant to write.

Usage, from the repository root (design/ecad/README.md, "Independent check of a candidate set"):

    python -I -B design/ecad/scripts/independent_check_positions.py \
        <Gerber zip> <CPL csv> <BOM csv> <hand-solder csv> <board> <model frame json> \
        <previous release's Gerber zip> <previous release's CPL csv>

The previous release must be one whose parts and holes stand elsewhere (the last release of the
PCB revision before a layout change). Where its CPL, its paste flashes or its drill hits equal this
set's, the substitution is no corruption, and it is reported as MISSED.

Exit status: 0 = every check passed and every corruption was caught, 1 = not, 2 = usage.

What it CANNOT see: whether the board itself is right (it is the reference: a wrong footprint
position on the board passes), the copper, mask and silkscreen layers (only paste and drill are
compared with the board), a pad's shape or size, whether JLCPCB's model really sits as the frame
table says (that is the placement preview), the documented shift and turn themselves (the table is
read, not judged), stock, price, and anything of the schematic. It reads the same board file that
make_outputs.py plots, so it finds a fault of the generator, not of the board.

History: until 2026-11-19 this was the scratch script c2_ext_rev06.py, outside the repository
(issue #13; run on Rev0.6 r01). Its checks and corruptions are those.
"""
import copy
import csv
import hashlib
import json
import math
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) != 9:
    print("usage: independent_check_positions.py <Gerber zip> <CPL csv> <BOM csv> <hand-solder csv> <board> "
          "<model frame json> <previous release's Gerber zip> <previous release's CPL csv>")
    sys.exit(2)
ZIP, CPL, BOM, HAND, PCB, FRAME, PREV_ZIP, PREV_CPL = sys.argv[1:9]

TOL_CPL = 6e-5      # the CPL has 4 decimals
TOL_GBR = 0.002     # the Gerber has 6 decimals; pad positions are sums of 4-decimal numbers
TOL_DRL = 0.0011    # the drill files have 3 decimals


def gerber_flashes(text):
    """Return [(x, y)] for every D03 flash; coordinates in mm (FSLAX46, mm)."""
    out, x, y = [], 0.0, 0.0
    for line in text.splitlines():
        m = re.match(r"^(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])\*$", line)
        if m:
            if m.group(1) is not None:
                x = int(m.group(1)) / 1e6
            if m.group(2) is not None:
                y = int(m.group(2)) / 1e6
            if m.group(3) == "3":
                out.append((x, y))
    return out


def drill_hits(text):
    """Return [(x, y, diameter, travel)]; a G85 slot is reported at its midpoint with its travel."""
    tools, cur, out = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^T(\d+)C([\d.]+)$", line)
        if m:
            tools[int(m.group(1))] = float(m.group(2))
            continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = int(m.group(1))
            continue
        m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)(?:G85X(-?[\d.]+)Y(-?[\d.]+))?$", line)
        if m:
            x, y = float(m.group(1)), float(m.group(2))
            if m.group(3) is None:
                out.append((x, y, tools[cur], 0.0))
            else:
                x2, y2 = float(m.group(3)), float(m.group(4))
                out.append(((x + x2) / 2, (y + y2) / 2, tools[cur], math.hypot(x2 - x, y2 - y)))
    return out


def board(pcb_text):
    """Footprints, pads and holes from the board's text. Positions in the Gerber frame (aux origin, y up)."""
    m = re.search(r"\(aux_axis_origin (-?[\d.]+) (-?[\d.]+)\)", pcb_text)
    ox, oy = float(m.group(1)), float(m.group(2))
    fps, pads, holes = {}, [], []
    for blk in re.split(r"\n\t\(footprint ", pcb_text)[1:]:
        blk = blk.split("\n\t)\n", 1)[0]
        name = re.match(r'"([^"]*)"', blk).group(1).split(":")[-1]
        ref = re.search(r'\n\t\t\(property "Reference" "([^"]+)"', blk).group(1)
        at = re.search(r"\n\t\t\(at (-?[\d.]+) (-?[\d.]+)(?: (-?[\d.]+))?\)", blk)
        fx, fy, ang = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        attr = re.search(r"\n\t\t\(attr ([^)]*)\)", blk)
        if ref in fps:
            raise SystemExit(f"reference {ref} twice on the board")
        fps[ref] = {
            "name": name, "x": fx, "y": fy, "ang": ang,
            "layer": re.search(r'\n\t\t\(layer "([^"]+)"\)', blk).group(1),
            "attr": attr.group(1).split() if attr else [],
            "props": dict(re.findall(r'\n\t\t\(property "([^"]+)" "([^"]*)"', blk)),
        }
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        for pm in re.finditer(r'\n\t\t\(pad "([^"]*)" (\w+) (\w+)\n(.*?)\n\t\t\)', blk, re.S):
            body = pm.group(4)
            pa = re.search(r"\(at (-?[\d.]+) (-?[\d.]+)", body)
            lx, ly = float(pa.group(1)), float(pa.group(2))
            x, y = fx + lx * c + ly * s - ox, oy - (fy - lx * s + ly * c)
            layers = re.findall(r'"([^"]+)"', re.search(r"\(layers ([^)]*)\)", body).group(1))
            pads.append({"ref": ref, "pad": pm.group(1), "x": x, "y": y, "layers": layers})
            dr = re.search(r"\(drill (?:oval )?([\d.]+)(?: ([\d.]+))?", body)
            if pm.group(2) in ("thru_hole", "np_thru_hole"):
                a = float(dr.group(1))
                b = float(dr.group(2)) if dr.group(2) else a
                holes.append({"what": f"{ref}.{pm.group(1)}", "x": x, "y": y, "dia": min(a, b),
                              "travel": abs(a - b), "plated": pm.group(2) == "thru_hole"})
    for vm in re.finditer(r"\n\t\(via\n(.*?)\n\t\)", pcb_text, re.S):
        at = re.search(r"\(at (-?[\d.]+) (-?[\d.]+)\)", vm.group(1))
        dr = re.search(r"\(drill ([\d.]+)\)", vm.group(1))
        holes.append({"what": "via", "x": float(at.group(1)) - ox, "y": oy - float(at.group(2)),
                      "dia": float(dr.group(1)), "travel": 0.0, "plated": True})
    return fps, pads, holes


def member(z, suffix):
    hit = [n for n in z if n.endswith(suffix)]
    if len(hit) != 1:
        raise KeyError(f"{suffix}: {hit}")
    return hit[0]


def match(wanted, got, same):
    """Give each wanted item its own got item. Return (unmatched wanted, unused got)."""
    used, miss = set(), []
    for w in wanted:
        for i, g in enumerate(got):
            if i not in used and same(w, g):
                used.add(i)
                break
        else:
            miss.append(w)
    return miss, [g for i, g in enumerate(got) if i not in used]


def run(d):
    """Return a list of (id, item, ok, detail)."""
    r = []
    fps, pads, holes, z, frame = d["fps"], d["pads"], d["holes"], d["zip"], d["frame"]
    cpl, bom, hand = d["cpl"], d["bom"], d["hand"]
    lcsc = {k: v["props"]["LCSC"] for k, v in fps.items() if v["props"].get("LCSC")}
    aki = {k: v["props"]["Akizuki"] for k, v in fps.items() if v["props"].get("Akizuki")}
    cpl_refs = [x["Designator"] for x in cpl]
    hand_refs = [x["Designator"] for x in hand]
    bom_refs, bom_code = [], {}
    for row in bom:
        for t in row["Designator"].split(","):
            t = t.strip()
            bom_refs.append(t)
            bom_code[t] = row["JLCPCB Part #"]

    # X1: the three lists name exactly the board's parts
    ok = set(lcsc) == set(cpl_refs) == set(bom_refs)
    r.append(("X1a", "footprints with an LCSC code == CPL designators == BOM designators", ok,
              f"board {len(lcsc)}, CPL {len(set(cpl_refs))}, BOM {len(set(bom_refs))}; "
              f"board-CPL {sorted(set(lcsc) - set(cpl_refs))[:5]}, CPL-board {sorted(set(cpl_refs) - set(lcsc))[:5]}, "
              f"board-BOM {sorted(set(lcsc) - set(bom_refs))[:5]}, BOM-board {sorted(set(bom_refs) - set(lcsc))[:5]}"))
    bad = sorted(t for t in set(bom_refs) if lcsc.get(t) != bom_code[t])
    r.append(("X1b", "every BOM designator carries its footprint's LCSC code", not bad,
              f"{len(set(bom_code.values()))} codes; bad {bad[:5]}"))
    # A BOM line is one LCSC part. Where that part sits on two footprints the line carries the first
    # designator's (make_outputs.py's rule since Rev0.4: JLCPCB's part mapping does not select two
    # lines of one LCSC number). Asking every designator for the line's footprint name would fail on
    # RS12 and RS22, the 510 ohm part on the Kelvin land.
    bad, mixed = [], []
    for row in bom:
        refs = [t.strip() for t in row["Designator"].split(",")]
        names = sorted({fps[t]["name"] for t in refs if t in fps})
        if refs[0] not in fps or fps[refs[0]]["name"] != row["Footprint"]:
            bad.append(refs[0])
        if len(names) > 1:
            mixed.append(f"{row['JLCPCB Part #']} on {names}")
    r.append(("X1c", "every BOM line carries the footprint name of its first designator", not bad,
              f"bad {bad[:5]}; lines whose part sits on more than one footprint: {mixed}"))
    bad = sorted(x["Designator"] for x in hand if aki.get(x["Designator"]) != x["Akizuki"]
                 or fps[x["Designator"]]["name"] != x["Footprint"])
    r.append(("X1d", "hand-solder list == footprints with an Akizuki code, with their codes and names",
              set(hand_refs) == set(aki) and not bad, f"board {len(aki)}, list {len(set(hand_refs))}; bad {bad[:5]}"))

    def wrong(k, v):
        codes, excluded = (k in lcsc) + (k in aki), "exclude_from_bom" in v["attr"]
        return codes == 2 or (codes == 1) == excluded
    bad = sorted(k for k, v in fps.items() if wrong(k, v))
    none = sum(1 for k in fps if k not in lcsc and k not in aki)
    r.append(("X1e", "a footprint has one code, or none and is excluded from the BOM", not bad,
              f"{len(fps)} footprints: {len(lcsc)} LCSC, {len(aki)} Akizuki, {none} without a part; bad {bad[:5]}"))
    bad = sorted(k for k, v in fps.items() if (k in lcsc or k in aki) and v["layer"] != "F.Cu")
    r.append(("X1f", "every footprint with a part is on the Top side", not bad, f"bad {bad[:5]}"))

    # X5: nothing twice
    dup = sorted({t for lst in (cpl_refs, bom_refs, hand_refs) for t in lst if lst.count(t) > 1})
    r.append(("X5", "no designator twice in the CPL, the BOM or the hand-solder list", not dup,
              f"CPL {len(cpl_refs)} rows, BOM {len(bom_refs)} designators in {len(bom)} lines, hand {len(hand_refs)}; twice {dup[:5]}"))

    # X2, X3: the CPL against the board and the documented model frame
    badp, badr, worst, shifted, turned = [], [], 0.0, [], set()
    for row in cpl:
        ref = row["Designator"]
        fp = fps.get(ref)
        if fp is None:
            badp.append(ref)
            badr.append(ref)
            continue
        ent = frame.get(lcsc.get(ref), {})
        dx, dy = ent.get("shift", [0.0, 0.0])
        c, s = math.cos(math.radians(fp["ang"])), math.sin(math.radians(fp["ang"]))
        ex = fp["x"] + dx * c + dy * s - d["origin"][0]
        ey = d["origin"][1] - (fp["y"] - dx * s + dy * c)
        e = max(abs(float(row["Mid X"]) - ex), abs(float(row["Mid Y"]) - ey))
        worst = max(worst, e)
        if e > TOL_CPL:
            badp.append(ref)
        if "shift" in ent:
            shifted.append(ref)
        if "add" in ent:
            turned.add(ref)
        da = (float(row["Rotation"]) - fp["ang"] - ent.get("add", 0)) % 360
        if min(da, 360 - da) > 0.01:
            badr.append(ref)
    r.append(("X2", "every CPL point is its footprint's origin plus the documented model shift", not badp,
              f"{len(cpl)} rows, worst {worst:.6f} mm; with a shift {sorted(shifted)}; bad {len(badp)}: {sorted(badp)[:8]}"))
    r.append(("X3", "every CPL rotation is its footprint's angle plus the documented model turn", not badr,
              f"{len(cpl)} rows, {len(turned)} with a turn; bad {len(badr)}: {sorted(badr)[:8]}"))

    # X4: paste
    ptext = z[member(z, "F_Paste.gtp")]
    fl = gerber_flashes(ptext)
    pp = [p for p in pads if "F.Paste" in p["layers"]]
    regions = ptext.count("G36*")
    r.append(("X4a", "Top paste flashes == paste pads of the board, no region", len(fl) == len(pp) and regions == 0,
              f"{len(fl)} flashes, {len(pp)} pads, {regions} regions"))
    miss, left = match(pp, fl, lambda p, g: abs(p["x"] - g[0]) < TOL_GBR and abs(p["y"] - g[1]) < TOL_GBR)
    r.append(("X4b", "every paste pad has its own flash at its position, and no flash is left", not miss and not left,
              f"pads without a flash {len(miss)}: {sorted({p['ref'] for p in miss})[:8]}; flashes left {len(left)}"))

    # X6: holes
    for plated, suffix, cid in ((True, "_PTH.drl", "X6a"), (False, "_NPTH.drl", "X6b")):
        hs = [h for h in holes if h["plated"] == plated]
        hits = drill_hits(z[member(z, suffix)])
        miss, left = match(hs, hits, lambda h, g: abs(h["x"] - g[0]) < TOL_DRL and abs(h["y"] - g[1]) < TOL_DRL
                           and abs(h["dia"] - g[2]) < TOL_DRL and abs(h["travel"] - g[3]) < TOL_DRL)
        slots = sum(1 for h in hs if h["travel"] > 0)
        r.append((cid, f"every {'plated' if plated else 'non-plated'} hole of the board has its own hit in {suffix[1:]}, and no hit is left",
                  not miss and not left,
                  f"board {len(hs)} ({sum(1 for h in hs if h['what'] == 'via')} vias, {slots} slots), file {len(hits)}; "
                  f"holes without a hit {len(miss)}: {sorted({h['what'] for h in miss})[:6]}; hits left {len(left)}"))
    return r


def read_zip(path):
    z = zipfile.ZipFile(path)
    return {n: z.read(n).decode("utf-8", "replace").replace("\r\n", "\n")
            for n in z.namelist() if not n.endswith("_map.gbr")}


def read_csv(path):
    return list(csv.DictReader(open(path, encoding="utf-8", newline="")))


def load():
    pcb_text = open(PCB, encoding="utf-8").read()
    fps, pads, holes = board(pcb_text)
    m = re.search(r"\(aux_axis_origin (-?[\d.]+) (-?[\d.]+)\)", pcb_text)
    return {
        "zip": read_zip(ZIP), "cpl": read_csv(CPL), "bom": read_csv(BOM), "hand": read_csv(HAND),
        "frame": json.load(open(FRAME, encoding="utf-8"))["parts"],
        "fps": fps, "pads": pads, "holes": holes, "origin": (float(m.group(1)), float(m.group(2))),
    }


def main():
    for label, path in (("zip", ZIP), ("cpl", CPL), ("bom", BOM), ("hand", HAND), ("board", PCB),
                        ("frame", FRAME), ("previous zip", PREV_ZIP), ("previous cpl", PREV_CPL)):
        print(f"sha256 {label}: {hashlib.sha256(open(path, 'rb').read()).hexdigest()}")
    d = load()
    res = run(d)
    fails = [x for x in res if not x[2]]
    for cid, item, ok, detail in res:
        print(("PASS " if ok else "FAIL ") + cid + " " + item + "  [" + detail + "]")
    print(f"{len(res)} checks, {len(fails)} failed: {'FAIL' if fails else 'PASS'}")

    # negative tests: each corruption must fail the check it aims at
    neg = []
    c = copy.deepcopy(d); c["cpl"] = read_csv(PREV_CPL)
    neg.append(("the previous release's CPL in the place of this one", "X2", c))
    c = copy.deepcopy(d); c["zip"] = read_zip(PREV_ZIP)
    neg.append(("the previous release's Gerber zip in the place of this one", "X4b", c))
    c = copy.deepcopy(d); prev = read_zip(PREV_ZIP)
    for suffix in ("_PTH.drl", "_NPTH.drl"):
        c["zip"][member(c["zip"], suffix)] = prev[member(prev, suffix)]
    neg.append(("the previous release's two drill files inside this zip", "X6a", c))
    c = copy.deepcopy(d); c["cpl"][5]["Rotation"] = str((float(c["cpl"][5]["Rotation"]) + 90) % 360)
    neg.append((f"the CPL rotation of {d['cpl'][5]['Designator']} turned by 90 degrees", "X3", c))
    c = copy.deepcopy(d)
    j1 = next(x for x in c["cpl"] if x["Designator"] == "J1"); j1["Mid Y"] = f"{float(j1['Mid Y']) + 1.375:.4f}"
    neg.append(("J1's Mid Y moved by the model shift, 1.375 mm", "X2", c))
    c = copy.deepcopy(d); c["cpl"][7]["Mid X"] = f"{float(c['cpl'][7]['Mid X']) + 0.01:.4f}"
    neg.append((f"the Mid X of {d['cpl'][7]['Designator']} moved by 0.01 mm", "X2", c))
    c = copy.deepcopy(d)
    gone = c["cpl"].pop(9)["Designator"]
    for row in c["bom"]:
        row["Designator"] = ",".join(t for t in row["Designator"].split(",") if t.strip() != gone)
    neg.append((f"{gone} taken out of both the CPL and the BOM", "X1a", c))
    c = copy.deepcopy(d); c["cpl"].append(dict(c["cpl"][3]))
    neg.append((f"the CPL row of {d['cpl'][3]['Designator']} written twice", "X5", c))
    c = copy.deepcopy(d)
    first = c["bom"][0]["Designator"].split(",")
    c["bom"][0]["Designator"] = ",".join(first[1:]); c["bom"][1]["Designator"] += "," + first[0]
    neg.append((f"{first[0]} moved to another BOM line", "X1b", c))
    c = copy.deepcopy(d); c["bom"][2]["Footprint"] = "X_" + c["bom"][2]["Footprint"]
    neg.append((f"the footprint name of BOM line {d['bom'][2]['JLCPCB Part #']} changed", "X1c", c))
    c = copy.deepcopy(d); c["hand"][0]["Akizuki"] = "g000000"
    neg.append((f"the Akizuki code of {d['hand'][0]['Designator']} changed", "X1d", c))
    c = copy.deepcopy(d)
    k = member(c["zip"], "F_Paste.gtp"); lines = c["zip"][k].split("\n")
    last = max(i for i, s in enumerate(lines) if s.endswith("D03*")); del lines[last]; c["zip"][k] = "\n".join(lines)
    neg.append(("one flash taken out of the Top paste Gerber", "X4b", c))
    c = copy.deepcopy(d)
    k = member(c["zip"], "_PTH.drl"); lines = c["zip"][k].split("\n")
    first_hit = next(i for i, s in enumerate(lines) if re.match(r"^X[-\d.]+Y[-\d.]+$", s)); del lines[first_hit]
    c["zip"][k] = "\n".join(lines)
    neg.append(("one hit taken out of the plated drill file", "X6a", c))
    c = copy.deepcopy(d)
    k = member(c["zip"], "_NPTH.drl")
    c["zip"][k] = re.sub(r"(?m)^X(-?[\d.]+)Y", lambda m: f"X{float(m.group(1)) + 0.1:.3f}Y", c["zip"][k])
    neg.append(("every non-plated hit moved 0.1 mm in X", "X6b", c))
    c = copy.deepcopy(d); c["fps"][d["cpl"][11]["Designator"]]["layer"] = "B.Cu"
    neg.append((f"{d['cpl'][11]['Designator']} put on the Bottom side of the board", "X1f", c))
    c = copy.deepcopy(d); c["fps"][d["cpl"][13]["Designator"]]["attr"].append("exclude_from_bom")
    neg.append((f"{d['cpl'][13]['Designator']} marked as excluded from the BOM on the board", "X1e", c))
    nbad = 0
    for label, want, cd in neg:
        failed = [cid for cid, _, ok, _ in run(cd) if not ok]
        caught = want in failed
        print(("CAUGHT " if caught else "MISSED ") + label + f"  [aimed at {want}; failed: {','.join(failed) or 'none'}]")
        nbad += 0 if caught else 1
    print(f"{len(neg)} negative tests, {nbad} missed: {'FAIL' if nbad else 'PASS'}")
    sys.exit(1 if fails or nbad else 0)


main()
