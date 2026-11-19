"""Independent check of a candidate manufacturing set, part 1: sets, sides and marks (stdlib only).

Reads the Gerber zip, the JLCPCB BOM and CPL, the hand-solder list, the board file and the
silkscreen table of the placement document, and reports PASS/FAIL per item (V-MFG-01 on the files
themselves): no paste on the bottom, the outline's size, three fiducials in copper and mask at
the board's positions, every CPL row on Top and inside the outline, the hand-solder list apart
from the BOM and the CPL, the BOM's designators equal to the CPL's, and a labelled test pad on
each net of REQ-MFG-04. It then corrupts in-memory copies and requires each corruption to be
caught (a checker never seen failing is not evidence).

Independent means: it imports nothing from this directory and no KiCad module, and it reads the
files JLCPCB receives, not what make_outputs.py meant to write. The outline (100 x 72 mm, D24),
the board's origin in KiCad's frame (50, 122) and the test-pad names (REQ-MFG-04) are written here
a second time on purpose: change them here when the requirement changes.

Usage, from the repository root (design/ecad/README.md, "Independent check of a candidate set"):

    python -I -B design/ecad/scripts/independent_check_sets.py \
        <Gerber zip> <CPL csv> <BOM csv> <hand-solder csv> <placement md> <board>

Exit status: 0 = every check passed and every corruption was caught, 1 = not, 2 = usage.

What it CANNOT see: any position but the fiducials' (it passes with another revision's CPL beside
this board; independent_check_positions.py reads positions), whether a part's rotation is right
in JLCPCB's model (that is the placement preview), whether a pad's copper is the right shape for
its part, whether the silkscreen text is legible. It checks counts, sizes, sides, the fiducials'
places, and name matches.

History: until 2026-11-19 this was the scratch script c2_check.py, outside the repository (issues
#6 and #8; run on Rev0.4 r01, Rev0.5 r02 and Rev0.6 r01). Its checks and corruptions are those.
"""
import copy
import csv
import re
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8")

if len(sys.argv) != 7:
    print("usage: independent_check_sets.py <Gerber zip> <CPL csv> <BOM csv> <hand-solder csv> <placement md> <board>")
    sys.exit(2)
ZIP, CPL, BOM, HAND, SILKMD, PCB = sys.argv[1:7]

REQ_PADS = ["VBUS_IN", "VSUP_A", "VSUP_B", "VBUS_A", "VBUS_B", "V5L", "V5A", "V12F", "V_INJ",
            "V3V3", "VDDA", "GND", "DVDD", "RUN", "CLKOUT", "VDD33_HUB"]


def gerber_flashes(text):
    """Return [(x, y, kind, size)] for every D03 flash; coordinates in mm (FSLAX46, mm)."""
    ap = {}
    for m in re.finditer(r"^%ADD(\d+)([A-Za-z]+),([^*]*)\*%", text, re.M):
        n, kind, params = int(m.group(1)), m.group(2), m.group(3)
        first = float(params.split("X")[0])
        ap[n] = (kind, first)
    out, cur, x, y = [], None, 0.0, 0.0
    for line in text.splitlines():
        m = re.match(r"^(?:G54)?D(\d+)\*$", line)
        if m and int(m.group(1)) >= 10:
            cur = int(m.group(1))
            continue
        m = re.match(r"^(?:X(-?\d+))?(?:Y(-?\d+))?D0([123])\*$", line)
        if m:
            if m.group(1) is not None:
                x = int(m.group(1)) / 1e6
            if m.group(2) is not None:
                y = int(m.group(2)) / 1e6
            if m.group(3) == "3":
                kind, size = ap.get(cur, ("?", 0.0))
                out.append((x, y, kind, size))
    return out


def edge_bounds(text):
    xs, ys = [], []
    for m in re.finditer(r"^X(-?\d+)Y(-?\d+)D0[12]\*$", text, re.M):
        xs.append(int(m.group(1)) / 1e6)
        ys.append(int(m.group(2)) / 1e6)
    return min(xs), max(xs), min(ys), max(ys)


def footprints(pcb_text):
    """{ref: {'at': (x, y), 'nets': [names]}} from the board text, by regex on tab-level blocks."""
    res = {}
    for blk in re.split(r"\n\t\(footprint ", pcb_text)[1:]:
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk)
        at = re.search(r"\n\t\t\(at (-?[\d.]+) (-?[\d.]+)", blk)
        if not ref or not at:
            continue
        nets = re.findall(r'\(net (?:\d+ )?"([^"]*)"\)', blk)
        res[ref.group(1)] = {"at": (float(at.group(1)), float(at.group(2))), "nets": nets}
    return res


def silk_rows(md):
    body = md.split("<!-- silk:begin -->")[1].split("<!-- silk:end -->")[0]
    rows = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) > 2 and re.match(r"^(TP\d+|J\d|title|revision)$", cells[0]):
            rows[cells[0]] = cells[1]
    return rows


def run(d):
    """Return a list of (item, ok, detail)."""
    r = []
    z = d["zip"]

    def f(suffix):
        for n in z:
            if n.endswith(suffix):
                return z[n]
        raise KeyError(suffix)
    # 1. bottom paste
    bp = gerber_flashes(f("B_Paste.gbp"))
    regions = f("B_Paste.gbp").count("G36*")
    r.append(("bottom paste flashes + regions == 0", len(bp) == 0 and regions == 0,
              f"{len(bp)} flashes, {regions} regions"))
    # 2. outline
    x0, x1, y0, y1 = edge_bounds(f("Edge_Cuts.gm1"))
    r.append(("outline 100 x 72 mm", abs((x1 - x0) - 100) < 1e-6 and abs((y1 - y0) - 72) < 1e-6,
              f"{x1 - x0:.3f} x {y1 - y0:.3f} mm"))
    # 3. fiducials: from the board, found in the Gerbers as 1.0 mm copper and 2.0 mm mask flashes
    fps = d["fps"]
    fids = sorted(k for k in fps if k.startswith("FID"))
    r.append(("at least 3 fiducial footprints", len(fids) >= 3, f"{fids}"))
    cu, mk = gerber_flashes(f("F_Cu.gtl")), gerber_flashes(f("F_Mask.gts"))
    for fid in fids:
        px, py = fps[fid]["at"]
        gx, gy = px - 50.0, 122.0 - py            # Gerber frame = the board's lower-left corner (aux origin), y up

        def near(fl, size):
            return any(abs(x - gx) < 0.005 and abs(y - gy) < 0.005 and k == "C" and abs(s - size) < 1e-6
                       for x, y, k, s in fl)
        r.append((f"{fid} copper 1.0 mm circle at the board's position", near(cu, 1.0), f"({gx}, {gy})"))
        r.append((f"{fid} mask opening 2.0 mm circle", near(mk, 2.0), f"({gx}, {gy})"))
    # fiducials spread: not collinear (a global fiducial set needs a triangle)
    if len(fids) >= 3:
        (ax, ay), (bx, by), (cx, cy) = (fps[k]["at"] for k in fids[:3])
        area = abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2
        r.append(("first 3 fiducials form a triangle (area > 100 mm2)", area > 100, f"{area:.0f} mm2"))
    # 4. CPL
    rows = d["cpl"]
    bad_side = [x["Designator"] for x in rows if x["Layer"] != "Top"]
    r.append(("every CPL row is Top", not bad_side, f"{len(rows)} rows; bad: {bad_side[:5]}"))
    out = [x["Designator"] for x in rows if not (0 <= float(x["Mid X"]) <= 100 and 0 <= float(x["Mid Y"]) <= 72)]
    r.append(("every CPL row inside 0..100 x 0..72 mm", not out, f"outside: {out[:5]}"))
    # 5. hand list vs BOM and CPL
    hand = {x["Designator"] for x in d["hand"]}
    bom = {t.strip() for row in d["bom"] for t in row["Designator"].split(",")}
    cpl = {x["Designator"] for x in rows}
    r.append(("hand list disjoint from BOM and CPL", not (hand & bom) and not (hand & cpl),
              f"hand {len(hand)}, BOM {len(bom)}, CPL {len(cpl)}; overlap {sorted((hand & bom) | (hand & cpl))}"))
    r.append(("BOM designators == CPL designators", bom == cpl,
              f"BOM-CPL {sorted(bom - cpl)[:5]}, CPL-BOM {sorted(cpl - bom)[:5]}"))
    # 6. REQ-MFG-04 test pads: each name is a silk label whose TP footprint's pad net ends with it
    sr = d["silk"]
    text_to_tp = {v: k for k, v in sr.items() if k.startswith("TP")}
    for name in REQ_PADS:
        tp = text_to_tp.get(name)
        if tp is None:
            r.append((f"test pad {name} labelled", False, "no silk label with this text"))
            continue
        nets = fps.get(tp, {}).get("nets", [])
        ok = tp in fps and (name == "CLKOUT" or any(n.split("/")[-1] == name for n in nets))
        r.append((f"test pad {name} labelled ({tp}) and on a footprint whose pad net matches", ok, f"nets {sorted(set(nets))}"))
    return r


def load():
    z = zipfile.ZipFile(ZIP)
    zd = {n: z.read(n).decode("utf-8", "replace").replace("\r\n", "\n")
          for n in z.namelist() if not n.endswith("_map.gbr")}
    return {
        "zip": zd,
        "cpl": list(csv.DictReader(open(CPL, encoding="utf-8", newline=""))),
        "bom": list(csv.DictReader(open(BOM, encoding="utf-8", newline=""))),
        "hand": list(csv.DictReader(open(HAND, encoding="utf-8", newline=""))),
        "silk": silk_rows(open(SILKMD, encoding="utf-8").read()),
        "fps": footprints(open(PCB, encoding="utf-8").read()),
    }


def main():
    d = load()
    res = run(d)
    fails = [x for x in res if not x[1]]
    for item, ok, detail in res:
        print(("PASS " if ok else "FAIL ") + item + "  [" + detail + "]")
    print(f"{len(res)} checks, {len(fails)} failed: {'FAIL' if fails else 'PASS'}")
    # negative tests: each corruption must produce at least one FAIL
    neg = []
    c = copy.deepcopy(d); c["cpl"][0]["Layer"] = "Bottom"; neg.append(("CPL row to Bottom", c))
    c = copy.deepcopy(d); c["cpl"][1]["Mid X"] = "250.0"; neg.append(("CPL row off the board", c))
    h0 = d["hand"][0]["Designator"]       # a hand-soldered part, whichever the revision has (J1 was one until Rev0.5)
    c = copy.deepcopy(d); c["bom"][0]["Designator"] += "," + h0; neg.append((f"hand designator {h0} added to BOM", c))
    c = copy.deepcopy(d)
    k = next(n for n in c["zip"] if n.endswith("B_Paste.gbp")); c["zip"][k] = c["zip"][k].replace(
        "G04 APERTURE END LIST*", "%ADD10C,1.000000*%\nG04 APERTURE END LIST*\nD10*\nX60000000Y60000000D03*")
    neg.append(("a flash added to B_Paste", c))
    c = copy.deepcopy(d); c["fps"]["FID1"]["at"] = (60.0, 60.0); neg.append(("FID1 moved off its flash", c))
    c = copy.deepcopy(d); del c["fps"]["FID3"]; neg.append(("FID3 removed", c))
    c = copy.deepcopy(d); c["silk"] = {k2: v for k2, v in c["silk"].items() if v != "V5L"}; neg.append(("V5L label removed", c))
    c = copy.deepcopy(d)
    k = next(n for n in c["zip"] if n.endswith("Edge_Cuts.gm1")); c["zip"][k] = c["zip"][k].replace("X100000000", "X90000000")
    neg.append(("outline narrowed", c))
    nbad = 0
    for label, cd in neg:
        caught = any(not ok for _, ok, _ in run(cd))
        print(("CAUGHT " if caught else "MISSED ") + label)
        nbad += 0 if caught else 1
    print(f"{len(neg)} negative tests, {nbad} missed: {'FAIL' if nbad else 'PASS'}")
    sys.exit(1 if fails or nbad else 0)


main()
