"""OI-23 placement study: can the Rev0.4 part set sit on the board?

Usage (standard library only):
    python -I design/experiments/oi-23-placement/placement_study.py [--svg OUT.svg]

It answers two questions for CIRCUIT_DESIGN_Rev0.4.md:
1. Necessary area. Could ANY layout of 85 x 35 mm (D10, before D24) hold the part set? It sums every
   courtyard, subtracts every square millimetre that could hold SMD parts under a raised
   module, and compares the result with the board area. Routing space is zero in the most
   favourable case (K = 1.0), so a fail there is a proof, not an estimate.
2. A concrete block placement (LAYOUT, 100 x 72 mm, adopted as D24). It checks that:
   - every rectangle lies inside the board;
   - no two rectangles overlap;
   - each SMD region holds the courtyards of its blocks times the routing factor K;
   - every package fits the region's smaller side;
   - only parts no taller than UNDER_MAX_H sit under a module;
   - the connectors sit on their edges, and the J2-J3 pitch is at least 20 mm;
   - the MAU104 keeps SEP_MAU from the analog front end and the ADCs;
   - a USB corridor runs from the CH335F to J2 and J3 without crossing the analog front end.
   It exits 1 if any check fails.

What it CANNOT see (write these next to any result quoted from it):
- routing: K is a planning assumption, so its sensitivity is printed. Only capture and
  layout prove that a region routes;
- real footprints: courtyards are IPC-7351-nominal planning values (COURTYARD), and passive
  counts come from the Rev0.4 circuit text and requirements/parts.md, numbered at capture;
- the CH335F module outline (measured from Akizuki's product photo against a ruler, OI-24)
  and the PGA2040 pin map (OI-31). No SMD is assumed under the PGA2040 for that reason;
- heights, except through the under-module rule; enclosure, thermal and EMC behaviour;
- the placement inside each region (for example, that the shunt ladder keeps away from the
  USB corridor). The SVG draws regions, not parts.
"""
import argparse
import sys

K = 1.6               # routing factor: region area per courtyard area (planning value)
K_SWEEP = (1.0, 1.4, 1.6, 2.0)
UNDER_MAX_H = 1.5     # mm: tallest part allowed under a module on 2.5 mm header plastic
SEP_MAU = 6.0         # mm: MAU104 courtyard to analog front end and ADC courtyards
CLEAR = 0.5           # mm: minimum gap between rectangles
EDGE = 0.3            # mm: rectangle to board edge (CLAUDE.md 5.3 copper to edge)

# ---- planning courtyards: (area mm2, short side mm, max height mm) ----------------------
COURTYARD = {
    "0402": (1.82, 0.98, 0.55),      # KiCad R_0402_1005Metric: 1.86 x 0.98
    "0603": (4.32, 1.46, 0.95),      # R_0603_1608Metric: 2.96 x 1.46
    "0805": (6.38, 1.90, 1.45),      # C_0805_2012Metric: 3.36 x 1.90; 22 uF is 1.25 + 0.2
    "SOT-23": (10.3, 3.04, 1.12),    # SOT-23: 3.4 x 3.04
    "SOIC-8": (39.2, 5.30, 1.75),    # SOIC-8_3.9x4.9mm_P1.27mm: 7.4 x 5.3
    "SOT-223": (60.6, 7.30, 1.80),   # SOT-223-3_TabPin2: 8.3 x 7.3
    "SMB": (33.0, 4.50, 2.30),       # D_SMB: 7.3 x 4.5
    "3225": (16.7, 3.70, 0.80),      # Crystal_SMD_3225-4Pin: 4.5 x 3.7
    "TACT": (43.0, 6.10, 3.50),      # TS-1187A 5.1 x 5.1 body, legs out: ~7.0 x 6.1
    "TC2030": (45.0, 4.50, 0.00),    # TC2030-NL land with its keepout: ~10 x 4.5
    "FID": (9.0, 3.00, 0.00),        # 1 mm copper, 2 mm mask opening, 3 x 3 keepout
    "TSL-KELVIN": (32.0, 4.00, 1.00),  # TSL1TTER100D 6.3 x 3.1 on a 4-pad Kelvin land
    "AXIAL-10": (34.7, 2.80, 2.50),  # MFU100F10RB 6 x 2.3, 10.16 mm pitch: 12.4 x 2.8
}

# ---- SMD blocks: name -> [(package, count)] -----------------------------------------------
# Per channel (A; B is the same). Counts follow Rev0.4 Sec. 3 and parts.md "Use" columns.
CHANNEL = {
    # port side, under J2/J3: Q13 discharge + its 1 k, port capacitor, D2 PSM712, Rp x 2
    "PORT": [("SOT-23", 2), ("0402", 3), ("0805", 1)],
    # supply side: Q10/Q11 switch, Q12 EN driver, Q14/Q15 inverter + fast-off, Q16 clamp;
    # EN series, DIS pull-up, EN_G pull-down, gate resistors x 3, soft-start 10 nF
    "PSW": [("SOT-23", 6), ("0402", 7)],
    # R_H, R_M (hand), R_L, bypass FETs Q17/Q18, holds Q19/Q20; gate returns, hold pull-ups
    "LADDER": [("TSL-KELVIN", 1), ("AXIAL-10", 1), ("0805", 1), ("SOT-23", 4), ("0402", 4)],
    # U10-U12, Q21-Q23; R1 x 3, R_OUT x 3, C_N x 3, R_INJ x 3, +IN guard x 3, ADC series
    # x 3, decoupling x 3
    "AMPS": [("SOIC-8", 3), ("SOT-23", 3), ("0402", 18), ("0603", 3)],
    # U13, Q24/Q25 EVT shifters; EVT series x 2, OC read, thresholds x 4, hysteresis x 4,
    # decoupling
    "CMP": [("SOIC-8", 1), ("SOT-23", 2), ("0402", 12)],
    # SW, green + red LED, 2 resistors
    "UI": [("TACT", 1), ("0805", 2), ("0402", 2)],
}
COMMON = {
    "J4IN": [("SOT-23", 1), ("0402", 5), ("0805", 1)],   # D4, Rd x 2, V_J4 divider, 100 nF, 22 uF
    "TVS4": [("SMB", 1)],                                 # D6
    "J1IN": [("SOT-23", 1), ("0402", 3)],                 # D1, Rd x 2, 100 nF
    "TVS1": [("SMB", 1)],                                 # D5
    "LDO": [("SOT-223", 1), ("0805", 3), ("0402", 2), ("0603", 1)],  # U2, 22u, 10u x 2, FB1
    "V12": [("SOT-23", 1), ("0402", 7), ("0805", 2)],     # U4, 10R, feed, divider, 1u x 2, 22u x 2
    "ADCSUP": [("SOT-23", 4), ("0402", 13), ("0805", 2)],  # Q50-Q52, U3; pull-ups, DOUT dividers
    "OC": [("SOIC-8", 1), ("0402", 7)],                   # U30 and its network
    "MCUF": [("TACT", 1), ("TC2030", 1)],                 # SW3 BOOT, SWD land
    "PGASUP": [("0402", 4), ("0805", 1)],                 # decoupling, 27 ohm x 2 (OI-31)
    "HUB": [("3225", 1), ("0402", 5), ("0805", 1)],       # Y2, decoupling, straps
    "FID": [("FID", 1)],
}


def blocks():
    out = {}
    for ch in ("A", "B"):
        for k, v in CHANNEL.items():
            out[f"{k}_{ch}"] = v
    out.update(COMMON)
    out["FID2"] = COMMON["FID"]
    out["FID3"] = COMMON["FID"]
    return out


BLOCKS = blocks()


def court(block):
    return sum(COURTYARD[p][0] * n for p, n in BLOCKS[block])


def need(block, k):
    """Region area a block needs. A fiducial is a keepout, not a routed part: no K."""
    return court(block) * (1.0 if block.startswith("FID") else k)


def short_side(block):
    return max(COURTYARD[p][1] for p, _ in BLOCKS[block])


def height(block):
    return max(COURTYARD[p][2] for p, _ in BLOCKS[block])


# ---- hand-soldered parts and their under-module areas -------------------------------------
# USB-C module (AE-USB2.0-TYPE-C drawing): 20 x 15 mm, receptacle edge at local y = 0.
# Mechanical 2 x 2 pins at x 2.38 / 17.62, y 2.94 / 5.48; shell tabs at x ~3.8-5.3 and
# ~14.8-16.3; the 1 x 7 pin row at y 13.1. Free under it: between the tab columns, and the
# strip between the lower tabs and the pin row.
USBC_UNDER = [(5.8, 0.5, 8.5, 7.9), (0.5, 8.4, 19.0, 3.3)]
# CH335F module (photo estimate): 38.5 x 10.2 mm, two rows of 15 pins 7.62 mm apart.
CH335_UNDER = [(0.5, 2.64, 37.5, 4.92)]

HAND = {  # name: (w, h, under-rects in local frame)
    "USBC": (20.0, 15.0, USBC_UNDER),
    "PGA2040": (21.0, 21.0, []),          # pin map unknown (OI-31): nothing assumed under it
    "CH335F": (38.5, 10.2, CH335_UNDER),
    "DIP16": (9.8, 20.85, []),            # DIP-16_W7.62mm courtyard
    "MAU104": (20.0, 6.6, []),            # 19.5 x 6.1 SIP body, courtyard
}
HAND_PARTS = {  # designator: kind
    "J1": "USBC", "J2": "USBC", "J3": "USBC", "J4": "USBC",
    "U1": "PGA2040", "U6": "CH335F", "U7": "DIP16", "U17": "DIP16", "U5": "MAU104",
}


def under_area(kind):
    return sum(w * h for _, _, w, h in HAND[kind][2])


# ---- 1. necessary area ----------------------------------------------------------------------
def necessary_area(k, mh=4 * 7 * 7):
    """Lower bound on the board area: (needed, hand, smd, credit, space, qualifying).

    The under-module credit is the most favourable one: every single part no taller than
    UNDER_MAX_H may sit under a module (counted per part, not per block), up to the space
    there is. A real layout gets less, so a board smaller than this bound cannot work.
    """
    hand = sum(HAND[kd][0] * HAND[kd][1] for kd in HAND_PARTS.values())
    smd = sum(need(b, k) for b in BLOCKS)
    space = sum(under_area(kd) for kd in HAND_PARTS.values())
    qualifying = sum(COURTYARD[p][0] * n * (1.0 if b.startswith("FID") else k)
                     for b in BLOCKS for p, n in BLOCKS[b] if COURTYARD[p][2] <= UNDER_MAX_H)
    credit = min(space, qualifying)
    return hand + mh + smd - credit, hand, smd, credit, space, qualifying


# ---- 2. the concrete layout (100 x 72 mm) --------------------------------------------------
W, H = 100.0, 72.0
# Hand parts: designator -> (x, y, rotation). Rotation 0: local y = 0 at the board's y = 0
# side (front edge); 180: local y = 0 at the back edge; 90: module turned, long side along y.
PLACE = {
    "J2": (18.0, 0.0, 0), "J3": (46.0, 0.0, 0),        # OUT A / OUT B, front edge
    "J4": (7.5, 57.0, 180), "J1": (66.0, 57.0, 180),   # PWR IN / HOST, back edge
    "U7": (55.5, 19.0, 0), "U17": (65.8, 19.0, 0),     # ADCs next to the front ends
    "U6": (89.3, 19.0, 90),                            # CH335F, right edge, upstream end at J1
    "U5": (82.0, 30.0, 90),                            # MAU104, digital side
    "U1": (30.0, 50.0, 0),                             # PGA2040
}
KEEPOUT = {  # mounting holes (heat-set M2, D21) and the USB corridor
    "MH1": (0.0, 0.0, 7.0, 7.0), "MH2": (93.0, 0.0, 7.0, 7.0),
    "MH3": (0.0, 65.0, 7.0, 7.0), "MH4": (93.0, 65.0, 7.0, 7.0),
    "USB_CORRIDOR": (18.0, 15.5, 71.3, 3.0),
}
REGIONS = {  # top-side SMD regions: name -> ((x, y, w, h), [blocks])
    "R_UIA": ((7.5, 0.5, 10.0, 14.5), ["UI_A"]),
    "R_GAP": ((38.5, 0.5, 7.0, 14.5), []),
    "R_UIB": ((66.5, 0.5, 13.0, 14.5), ["UI_B"]),
    "R_MCUF": ((80.0, 0.5, 12.5, 14.5), ["MCUF"]),
    "R_AFEA": ((0.5, 19.0, 27.0, 31.0), ["PSW_A", "LADDER_A", "AMPS_A", "CMP_A"]),
    "R_AFEB": ((28.0, 19.0, 27.0, 30.5), ["PSW_B", "LADDER_B", "AMPS_B", "CMP_B"]),
    "R_ADCS": ((55.5, 40.5, 20.1, 7.0), ["ADCSUP"]),
    "R_V12": ((76.5, 19.0, 12.3, 10.5), ["V12"]),
    "R_TVS1": ((76.5, 50.5, 12.3, 6.0), ["TVS1"]),
    "R_PWR4": ((7.5, 50.5, 20.0, 6.0), ["TVS4"]),
    "R_LDO": ((51.5, 50.0, 14.0, 21.5), ["LDO", "PGASUP", "OC"]),
    "R_F1": ((1.0, 8.5, 3.0, 3.0), ["FID"]),
    "R_F2": ((96.0, 8.5, 3.0, 3.0), ["FID2"]),
    "R_F3": ((1.0, 61.0, 3.0, 3.0), ["FID3"]),
}
UNDER = {  # under-module assignments: designator -> [blocks]
    "J2": ["PORT_A"], "J3": ["PORT_B"], "J4": ["J4IN"], "J1": ["J1IN"], "U6": ["HUB"],
}
ANALOG = ["R_AFEA", "R_AFEB", "U7", "U17"]   # MAU104 keeps SEP_MAU from these


def hand_rect(des):
    x, y, rot = PLACE[des]
    w, h, _ = HAND[HAND_PARTS[des]]
    return (x, y, h, w) if rot in (90, 270) else (x, y, w, h)


def under_rects(des):
    x, y, rot = PLACE[des]
    w, h, rects = HAND[HAND_PARTS[des]]
    out = []
    for lx, ly, lw, lh in rects:
        if rot == 0:
            out.append((x + lx, y + ly, lw, lh))
        elif rot == 180:
            out.append((x + w - lx - lw, y + h - ly - lh, lw, lh))
        else:  # 90: long side along y
            out.append((x + ly, y + lx, lh, lw))
    return out


def gap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    dx = max(bx - (ax + aw), ax - (bx + bw), 0.0)
    dy = max(by - (ay + ah), ay - (by + bh), 0.0)
    if dx == 0.0 and dy == 0.0:
        ix = min(ax + aw, bx + bw) - max(ax, bx)
        iy = min(ay + ah, by + bh) - max(ay, by)
        return -min(ix, iy)          # overlap depth
    return (dx * dx + dy * dy) ** 0.5


def check_layout():
    fails = []
    rects = {d: hand_rect(d) for d in PLACE}
    rects.update(KEEPOUT)
    rects.update({n: r for n, (r, _) in REGIONS.items()})
    for n, (x, y, w, h) in rects.items():
        lim = 0.0 if n.startswith("MH") else EDGE
        if n in ("J1", "J2", "J3", "J4"):
            lim = 0.0                 # the receptacle edge sits on the board edge
        if x < lim - 1e-9 or y < lim - 1e-9 or x + w > W - lim + 1e-9 or y + h > H - lim + 1e-9:
            fails.append(f"{n} leaves the board")
    names = list(rects)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            g = gap(rects[a], rects[b])
            if g < CLEAR - 1e-9:
                fails.append(f"{a} and {b} are {g:.2f} mm apart (< {CLEAR})")
    used = []
    for n, (r, bl) in REGIONS.items():
        nd = sum(need(b, K) for b in bl)
        area = r[2] * r[3]
        if nd > area + 1e-9:
            fails.append(f"{n}: needs {nd:.0f} mm2, has {area:.0f}")
        for b in bl:
            used.append(b)
            if short_side(b) > min(r[2], r[3]):
                fails.append(f"{n}: a {b} package does not fit its {min(r[2], r[3]):.1f} mm side")
    for d, bl in UNDER.items():
        ur = under_rects(d)
        cap = sum(w * h for _, _, w, h in ur)
        nd = sum(need(b, K) for b in bl)
        if nd > cap + 1e-9:
            fails.append(f"under {d}: needs {nd:.0f} mm2, has {cap:.0f}")
        for b in bl:
            used.append(b)
            if height(b) > UNDER_MAX_H:
                fails.append(f"under {d}: {b} is {height(b)} mm tall (> {UNDER_MAX_H})")
            if short_side(b) > max(min(w, h) for _, _, w, h in ur):
                fails.append(f"under {d}: {b} does not fit")
    missing = set(BLOCKS) - set(used)
    if missing:
        fails.append(f"blocks not placed: {sorted(missing)}")
    twice = sorted({b for b in used if used.count(b) > 1})
    if twice:
        fails.append(f"blocks placed more than once: {twice}")
    # connectors on their edges, pitch
    for d in ("J2", "J3"):
        if hand_rect(d)[1] != 0.0:
            fails.append(f"{d} is not on the front edge")
    for d in ("J1", "J4"):
        x, y, w, h = hand_rect(d)
        if abs(y + h - H) > 1e-9:
            fails.append(f"{d} is not on the back edge")
    pitch = PLACE["J3"][0] - PLACE["J2"][0]
    if pitch < 20.0:
        fails.append(f"J2-J3 pitch {pitch} mm < 20")
    # MAU104 separation
    mau = hand_rect("U5")
    for n in ANALOG:
        r = rects[n]
        g = gap(mau, r)
        if g < SEP_MAU:
            fails.append(f"MAU104 is {g:.1f} mm from {n} (< {SEP_MAU})")
    # USB corridor: reaches the CH335F and both port pin rows, crosses no analog region
    cor = KEEPOUT["USB_CORRIDOR"]
    for n in ("R_AFEA", "R_AFEB"):
        if gap(cor, rects[n]) < 0:
            fails.append(f"USB corridor crosses {n}")
    if gap(cor, hand_rect("U6")) > CLEAR + 1e-9:
        fails.append("USB corridor does not reach the CH335F")
    for d in ("J2", "J3"):
        if gap(cor, hand_rect(d)) > CLEAR + 1e-9:
            fails.append(f"USB corridor does not reach {d}")
    return fails, rects, pitch


def svg(path, rects):
    s = 6.0
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*s+20:.0f}" height="{H*s+20:.0f}"'
           f' viewBox="-10 -10 {W*s+20:.0f} {H*s+20:.0f}" font-family="sans-serif" font-size="9">',
           f'<rect x="0" y="0" width="{W*s}" height="{H*s}" fill="#1f5f3a" stroke="#000"/>']

    def r(x, y, w, h, fill, stroke, label, dash=False, colour="#fff", bottom=False):
        yy = (H - y - h) * s          # front edge (y = 0) drawn at the bottom
        d = ' stroke-dasharray="4,3"' if dash else ""
        out.append(f'<rect x="{x*s:.1f}" y="{yy:.1f}" width="{w*s:.1f}" height="{h*s:.1f}"'
                   f' fill="{fill}" stroke="{stroke}"{d}/>')
        if label:
            ty = yy + h * s - 4 if bottom else yy + 11
            out.append(f'<text x="{x*s+3:.1f}" y="{ty:.1f}" fill="{colour}">{label}</text>')

    for n, (rc, bl) in REGIONS.items():
        r(*rc, "#3c8d5a", "#9fe0b0", n[2:] + (": " + ", ".join(bl) if bl and not n.startswith("R_F") else ""))
    for n in KEEPOUT:
        r(*KEEPOUT[n], "#555" if n.startswith("MH") else "#2a4f8f", "#ccc", n)
    for d in PLACE:
        x, y, w, h = hand_rect(d)
        r(x, y, w, h, "none", "#ffd24a", f"{d} {HAND_PARTS[d]}", colour="#ffd24a", bottom=True)
        for ur in under_rects(d):
            r(*ur, "none", "#ffd24a", "", dash=True)
    out.append(f'<text x="2" y="{H*s+9:.0f}" fill="#000">front edge (OUT A / OUT B); '
               f'{W:.0f} x {H:.0f} mm; yellow = hand-soldered, dashed = SMD under module</text>')
    out.append("</svg>")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--svg", help="write the layout drawing to this path")
    a = ap.parse_args()
    total = sum(court(b) for b in BLOCKS)
    hand_shunts = sum(COURTYARD[p][0] * n for b in BLOCKS for p, n in BLOCKS[b]
                      if p in ("TSL-KELVIN", "AXIAL-10"))
    print(f"SMD courtyard {total:.0f} mm2 (of which hand shunts {hand_shunts:.0f}),"
          f" {sum(n for b in BLOCKS for p, n in BLOCKS[b] if p == '0402')} x 0402,"
          f" {sum(n for b in BLOCKS for p, n in BLOCKS[b] if p == 'SOT-23')} x SOT-23,"
          f" {sum(n for b in BLOCKS for p, n in BLOCKS[b] if p == 'SOIC-8')} x SOIC-8")
    print("\n== 1. necessary area (85 x 35 = 2975 mm2)")
    for k in K_SWEEP:
        req, hand, smd, credit, space, qualifying = necessary_area(k)
        print(f"K={k}: hand {hand:.0f} + holes 196 + SMD {smd:.0f} - under-module credit"
              f" {credit:.0f} = {req:.0f} mm2 -> {req/2975:.2f} x the 85 x 35 board;"
              f" smallest 100-wide board {req/100:.1f} mm deep"
              f" (credit = min(space {space:.0f}, low parts {qualifying:.0f}))")
    fails, rects, pitch = check_layout()
    print(f"\n== 2. layout {W:.0f} x {H:.0f} mm, K={K}")
    for n, (rc, bl) in REGIONS.items():
        if bl and not n.startswith("R_F"):
            nd = sum(need(b, K) for b in bl)
            print(f"{n:7s} {rc[2]*rc[3]:5.0f} mm2, uses {nd:5.0f} ({100*nd/(rc[2]*rc[3]):3.0f} %): {', '.join(bl)}")
    for d, bl in UNDER.items():
        cap = sum(w * h for _, _, w, h in under_rects(d))
        nd = sum(need(b, K) for b in bl)
        print(f"under {d:3s} {cap:5.0f} mm2, uses {nd:5.0f} ({100*nd/cap:3.0f} %): {', '.join(bl)}")
    kmax = min([r[2] * r[3] / sum(court(b) for b in bl)
                for n, (r, bl) in REGIONS.items() if bl and not n.startswith("R_F")] +
               [sum(w * h for _, _, w, h in under_rects(d)) / sum(court(b) for b in bl)
                for d, bl in UNDER.items()])
    print(f"this layout holds the blocks up to K = {kmax:.2f} (the tightest region sets it)")
    mau = hand_rect("U5")
    print(f"J2-J3 pitch {pitch:.0f} mm; MAU104 to the analog parts >= "
          f"{min(gap(mau, rects[n]) for n in ANALOG):.1f} mm")
    if a.svg:
        svg(a.svg, rects)
        print(f"wrote {a.svg}")
    print("\nlayout checks: " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        print("  - " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
