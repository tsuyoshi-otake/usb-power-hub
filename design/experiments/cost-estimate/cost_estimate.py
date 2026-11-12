#!/usr/bin/env python3
"""Prototype cost estimate: 5 bare PCBs, 2 of them assembled by JLCPCB, plus the Akizuki parts.

Non-authoritative (design/experiments). Every input below is dated; README.md lists the
sources and what this estimate cannot see.

Usage (from the repository root):
    python -I -B design/experiments/cost-estimate/cost_estimate.py
    python -I -B design/experiments/cost-estimate/cost_estimate.py --fetch

The first form computes from the committed price snapshot. ``--fetch`` refreshes that
snapshot from the JLCPCB assembly-parts API first, through tools/jlc_stock.py, which owns
the API client and its rate limiting. Exit status: 0 = computed; 1 = a BOM code is missing
from the snapshot, or is not Basic without being an approved exception (APPROVED_EXTENDED);
2 = the fetch failed.

The model prices Rev0.4 (the D33 re-run, with D34's C1523 removal). Rev0.5 (D37, D38) is priced
as a delta on release candidate r02's quote: see rev05_delta().
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SNAPSHOT = HERE / "jlc_prices.json"

BOARDS_PCB = 5          # bare PCBs fabricated
BOARDS_PCBA = 2         # of which JLCPCB assembles
JPY_PER_USD = 160.0     # planning rate; ~158 on 2026-10-11, 2026 high 163.85 (README)

# ---- JLCPCB PCB, read off cart.jlcpcb.com/quote on 2026-11-03 --------------------------
# 4 layers, 100 x 72 mm, 1.6 mm, 5 pcs, FR4 TG135, green, 1 oz / 0.5 oz, 3-4 day build.
PCB_BASE_USD = 8.00                                      # shown as "Special Offer"
PCB_FINISH_USD = {"HASL (with lead)": 0.00, "LeadFree HASL": 5.20, "ENIG": 17.40}
PCB_FINISH = "HASL (with lead)"                          # D30 (user, 2026-11-04); was ENIG
LID_PCB_USD = 4.00      # the lid panel: 2 layers, 100 x 72 mm, 5 pcs, HASL (CLAUDE.md §7)
# Shipping to Japan for the PCB-only parcel (0.24 kg). A PCBA parcel is heavier; the real
# figure appears only after the Gerber and BOM are uploaded.
SHIP_JP_USD = {"OCS Express": 7.23, "UPS Worldwide Express Saver": 9.79, "DHL Express": 17.62}
SHIP_PLAN = "OCS Express"            # the cheapest quoted; the user: not UPS (2026-11-04)

# ---- JLCPCB PCBA fees, jlcpcb.com/help/article/pcb-assembly-price ("Oct 22, 2026") ------
ECONOMIC = {"setup": 8.18, "stencil": 1.53, "joint": 0.0016, "extended_feeder": 3.07}
STANDARD = {"setup": 25.56, "stencil": 8.21, "joint": 0.0016, "feeder_per_type": 1.53,
            "packing_base": 0.50, "packing_per_cm2": 0.00003, "fixture": 16.42,
            "min_smt_per_board": 0.48, "handling_min_gap": 14.93}
CONFIRM_PLACEMENT = 0.45   # JLCPCB "Confirm Parts Placement"; CLAUDE.md §4.2 wants the preview
BOARD_AREA_CM2 = 10.0 * 7.2

# ---- Machine-placed BOM, per board ----------------------------------------------------
# Actives and the passives with an exact count: Rev0.4 §6.2 designators and parts.md.
EXACT = {
    "C2040": ("RP2040", "QFN-56", 1),
    "C5137013": ("CH335F USB hub", "QFN-28", 1),
    "C97521": ("W25Q128JVSIQ flash", "SOIC-8-208", 1),
    "C7433": ("OP07CDR", "SOIC-8", 6),
    "C7955": ("LM393DR2G", "SOIC-8", 3),
    "C6186": ("AMS1117-3.3", "SOT-223", 1),
    "C3113": ("CJ431", "SOT-23", 2),
    "C15127": ("AO3401A", "SOT-23", 14),
    "C20917": ("AO3400A", "SOT-23", 2),
    "C8545": ("2N7002", "SOT-23", 17),
    "C8543": ("S9012", "SOT-23", 2),
    "C32677": ("PSM712-LF-T7", "SOT-23", 4),
    "C7420377": ("SMBJ6.5CA", "SMB", 2),
    "C9002": ("12 MHz crystal (Y1, Y2)", "3225", 2),
    "C2297": ("LED green", "0805", 2),
    "C84256": ("LED red", "0805", 2),
    "C318884": ("tact switch", "TACT", 3),
    "C14709": ("ferrite 120 ohm", "0603", 1),
    "C1664": ("330 pF C0G", "0603", 4),
    "C22940": ("2.4 kohm", "0603", 2),
    "C25197": ("5.1 ohm (USB 27 ohm, part 2)", "0603", 2),
    "C17734": ("510 ohm", "0805", 3),
    "C45783": ("22 uF", "0805", 4),
    "C15850": ("10 uF", "0805", 7),
}
# 0402 passives: positions are numbered at capture, so these counts come from parts.md's
# "Use" column. The positions not attributed to a value (decoupling, comparator thresholds,
# the OC network) are REMAINDER_0402 and are priced at the dearest 0402 code.
# U1's circuit (Rev0.4 Sec. 6.5, D29) is attributed in full: 100 nF x 11, 1 uF x 2,
# 15 pF x 2, 22 ohm x 2, 1 kohm x 2, 10 kohm x 1. So is U6's (Sec. 6.6, D31): 1 uF at V5
# and 100 nF at VDD33; its 10 uF is one of the seven C15850.
EST_0402 = {
    "C25076": ("100 ohm", 6), "C25867": ("1.5 kohm", 8), "C25744": ("10 kohm", 17),
    "C25756": ("15 kohm", 4), "C25779": ("33 kohm", 6), "C25905": ("5.1 kohm", 4),
    "C25741": ("100 kohm", 6), "C26083": ("1 Mohm", 10), "C11702": ("1 kohm", 20),
    "C25077": ("10 ohm", 2), "C1530": ("220 pF", 2), "C307331": ("100 nF", 20),
    "C52923": ("1 uF", 7), "C15195": ("10 nF", 2),
    "C1548": ("15 pF C0G (Y1 load)", 2), "C25092": ("22 ohm (USB 27 ohm, part 1)", 2),
}
PINS = {"0402": 2, "0603": 2, "0805": 2, "SOT-23": 3, "SOIC-8": 8, "SOT-223": 4, "SMB": 2,
        "3225": 4, "TACT": 4, "QFN-56": 57, "QFN-28": 29,
        "SOIC-8-208": 8}                         # each QFN: its pins + the ePad
# The sourcing rule is Basic only (D13, D22). The user's exceptions, each with its decision:
APPROVED_EXTENDED = {"C2040": "D29", "C5137013": "D31", "C2765186": "D37"}
NOT_MACHINE = {"TSL-KELVIN", "AXIAL-10", "TC2030", "FID"}   # hand parts and bare lands

# ---- Akizuki, per board unless noted (requirements/parts.md, 2026-11-03, tax incl.) -----
AKIZUKI = [  # (part, code, yen each, per board); the PGA2040 (g116762) left with D29 and
    # the CH335F module (g129556) with D31
    ("MCP3208-CI/P", "g100238", 500, 2),
    ("AE-USB2.0-TYPE-C", "g113080", 350, 4),
    ("MAU104", "g104132", 520, 1),
    ("TSL1TTER100D", "g109588", 130, 2),
    ("MF-R300", "g112630", 40, 1),
]
AKIZUKI_ONCE = [("MFU100F10RB, bag of 100 (4 needed)", "g108805", 600)]
# Module headers (D33): PH-1x40SG strips of 40, broken into pieces; no sockets. Price and
# stock read off Akizuki on 2026-11-04. The pins per board come from the OI-23 study: 11 per
# USB-C module, the 1 x 7 row and two 1 x 2 mechanical pieces (REQ-MECH-03).
HEADER = ("pin header 1x40, PH-1x40SG (D33)", "g100167", 35)
HEADER_STRIP_PINS = 40
AKIZUKI_FREE_SHIPPING_YEN = 11000                     # subtotal, tax incl.
AKIZUKI_SHIPPING_YEN = 550                             # Sagawa, per parcel (from 2025-10-01)


def load_study():
    path = ROOT / "design" / "experiments" / "oi-23-placement" / "placement_study.py"
    spec = importlib.util.spec_from_file_location("placement_study", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def package_totals(blocks) -> dict[str, int]:
    """Machine-placed part count per package, from the placement study's blocks."""
    out: dict[str, int] = {}
    for parts in blocks.values():
        for pkg, n in parts:
            if pkg not in NOT_MACHINE:
                out[pkg] = out.get(pkg, 0) + n
    return out


def remainder_0402(totals: dict[str, int]) -> int:
    return totals["0402"] - sum(n for _, n in EST_0402.values())


def check_bom(totals: dict[str, int]) -> list[str]:
    """Every package total in the study must equal the BOM's; returns the mismatches."""
    bom: dict[str, int] = {}
    for _, pkg, n in EXACT.values():
        bom[pkg] = bom.get(pkg, 0) + n
    errs = [f"{pkg}: study {totals.get(pkg, 0)} vs BOM {bom.get(pkg, 0)}"
            for pkg in sorted((set(totals) | set(bom)) - {"0402"})
            if totals.get(pkg, 0) != bom.get(pkg, 0)]
    if remainder_0402(totals) < 0:
        errs.append(f"0402: values attribute {sum(n for _, n in EST_0402.values())} positions,"
                    f" more than the study's {totals.get('0402', 0)}")
    return errs


def joints(totals: dict[str, int]) -> int:
    return sum(PINS[p] * n for p, n in totals.items())


def tier_price(prices: list[dict], qty: int) -> float:
    for t in sorted(prices, key=lambda t: t["startNumber"]):
        if t["startNumber"] <= qty and (t["endNumber"] == -1 or qty <= t["endNumber"]):
            return float(t["productPrice"])
    raise ValueError(f"no price tier for quantity {qty}")


def order_qty(per_board: int, boards: int, item: dict) -> int:
    """Assumed JLCPCB rule: need + attrition, at least the minimum patch quantity."""
    need = per_board * boards + int(item.get("lossNumber") or 0)
    return max(need, int(item.get("leastPatchNumber") or 0), int(item.get("minPurchaseNum") or 1))


def parts_cost(snapshot: dict, rem_0402: int, boards: int) -> tuple[float, list[tuple]]:
    rows = []
    for code, (name, _pkg, n) in EXACT.items():
        it = snapshot[code]
        q = order_qty(n, boards, it)
        rows.append((code, name, n, q, tier_price(it["componentPrices"], q)))
    for code, (name, n) in EST_0402.items():
        it = snapshot[code]
        q = order_qty(n, boards, it)
        rows.append((code, name, n, q, tier_price(it["componentPrices"], q)))
    dearest = max(EST_0402, key=lambda c: tier_price(snapshot[c]["componentPrices"], 1))
    q = rem_0402 * boards
    rows.append(("(" + dearest + ")", "0402 positions not attributed to a value", rem_0402, q,
                 tier_price(snapshot[dearest]["componentPrices"], 1)))
    return sum(q * p for *_, q, p in rows), rows


def class_errors(parts: dict, codes: list[str]) -> list[str]:
    """Codes missing from the snapshot, or not Basic without an approved exception."""
    errs = []
    for c in codes:
        if c not in parts:
            errs.append(f"{c}: not in the snapshot")
        elif parts[c]["componentLibraryType"] != "base" and c not in APPROVED_EXTENDED:
            errs.append(f"{c}: {parts[c]['componentLibraryType']}, not Basic")
    return errs


def extended_codes(parts: dict, codes: list[str]) -> list[str]:
    return [c for c in codes if parts[c]["componentLibraryType"] != "base"]


def pcba_fees(n_joints_total: int, n_types: int, n_boards: int,
              n_extended: int) -> dict[str, dict[str, float]]:
    smt = n_joints_total * ECONOMIC["joint"]
    eco = {"setup": ECONOMIC["setup"], "stencil": ECONOMIC["stencil"], "SMT joints": smt,
           f"Extended feeders ({n_extended})": ECONOMIC["extended_feeder"] * n_extended,
           "confirm placement": CONFIRM_PLACEMENT}
    smt_s = n_joints_total * STANDARD["joint"]
    surcharge = max(0.0, STANDARD["min_smt_per_board"] * n_boards - smt_s)
    std = {"setup": STANDARD["setup"], "stencil": STANDARD["stencil"], "SMT joints": smt_s,
           "feeder loading": STANDARD["feeder_per_type"] * n_types,
           "packing": STANDARD["packing_base"] + STANDARD["packing_per_cm2"] * BOARD_AREA_CM2,
           "fixture (1-29 pcs)": STANDARD["fixture"], "single-board surcharge": surcharge,
           "confirm placement": CONFIRM_PLACEMENT}
    gap = sum(std.values()) - sum(eco.values())
    std["handling (gap below $14.93)"] = max(0.0, STANDARD["handling_min_gap"] - gap)
    return {"Economic": eco, "Standard": std}


def header_pins_per_board(study) -> int:
    """Module header pins per board: pins per USB-C module x the modules the study places."""
    return study.HDR_PINS_USBC * sum(1 for k in study.HAND_PARTS.values() if k == "USBC")


def akizuki_cost(n_units: int, header_pins: int,
                 without: tuple[str, ...] = ()) -> tuple[int, list[tuple]]:
    """Akizuki order for n_units, less the codes in `without`; header_pins per board, cut from
    shared 40-pin strips."""
    rows = [(p, c, y, k * n_units) for p, c, y, k in AKIZUKI if c not in without]
    rows += [(p, c, y, 1) for p, c, y in AKIZUKI_ONCE]
    strips = math.ceil(header_pins * n_units / HEADER_STRIP_PINS)
    if strips:
        rows.append((f"{HEADER[0]}, {header_pins * n_units} pins", HEADER[1], HEADER[2], strips))
    sub = sum(y * q for _, _, y, q in rows)
    ship = 0 if sub >= AKIZUKI_FREE_SHIPPING_YEN else AKIZUKI_SHIPPING_YEN
    rows.append(("shipping (free from 11,000 yen)", "-", ship, 1))
    return sub + ship, rows


# ---- Rev0.5 against r02 (D37, D38; issues #8, #10) --------------------------------------
# The four USB-C modules per board (Akizuki AE-USB2.0-TYPE-C) become machine-placed
# receptacles, C2765186 (Extended): 12 pads and 4 shell slots, 16 joints each. Four 1 kohm taps
# (C11702, 2 joints each) join the board. The base is release candidate r02, whose quote the
# JLCPCB form gave on 2026-11-12 (manufacturing/releases/rev0.4/r02/JLCPCB_REVIEW.md); the
# model's own total above is dearer than that quote and is not the base.
RECEPTACLE = "C2765186"
RECEPTACLES_PER_BOARD, RECEPTACLE_JOINTS = 4, 16
TAP = "C11702"
TAPS_PER_BOARD, TAP_JOINTS = 4, 2
MODULE_CODE = "g113080"                 # AE-USB2.0-TYPE-C: leaves the Akizuki order
R02_JLCPCB_USD = 54.92                  # PCB + PCBA + parts + OCS Express, r02 (4 = 47.69 + 7.23)


def rev05_delta(parts: dict, boards: int, header_pins: int) -> dict[str, float]:
    """Rev0.5 against r02: what JLCPCB's order gains (USD) and Akizuki's loses (yen)."""
    rec = parts[RECEPTACLE]
    qty = order_qty(RECEPTACLES_PER_BOARD, boards, rec)
    receptacles = qty * tier_price(rec["componentPrices"], qty)
    # the tap resistors join an existing C11702 line, so only their own pieces are added
    taps = TAPS_PER_BOARD * boards * tier_price(parts[TAP]["componentPrices"], 1)
    n_joints = boards * (RECEPTACLES_PER_BOARD * RECEPTACLE_JOINTS + TAPS_PER_BOARD * TAP_JOINTS)
    joints_usd = n_joints * ECONOMIC["joint"]
    feeder = ECONOMIC["extended_feeder"]
    added_usd = receptacles + taps + joints_usd + feeder
    old, _ = akizuki_cost(boards, header_pins)
    new, _ = akizuki_cost(boards, 0, without=(MODULE_CODE,))
    base_yen = R02_JLCPCB_USD * JPY_PER_USD + old
    net_yen = added_usd * JPY_PER_USD - (old - new)
    return {"receptacle_qty": qty, "receptacles_usd": receptacles, "taps_usd": taps,
            "joints": n_joints, "joints_usd": joints_usd, "feeder_usd": feeder,
            "added_usd": added_usd, "akizuki_old": old, "akizuki_new": new,
            "base_yen": base_yen, "net_yen": net_yen, "total_yen": base_yen + net_yen}


def snapshot_codes() -> list[str]:
    """Every code the snapshot holds: the Rev0.4 BOM and Rev0.5's receptacle."""
    return list(EXACT) + list(EST_0402) + [RECEPTACLE]


def fetch(codes: list[str]) -> int:
    path = ROOT / "tools" / "jlc_stock.py"
    spec = importlib.util.spec_from_file_location("jlc_stock", path)
    jlc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(jlc)
    import time
    keep = ("componentCode", "componentModelEn", "componentLibraryType", "stockCount",
            "componentPrices", "leastPatchNumber", "lossNumber", "minPurchaseNum")
    out = {"checked_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(), "parts": {}}
    for i, code in enumerate(codes):
        if i:
            time.sleep(jlc.REQUEST_SPACING_S)
        try:
            items = jlc._post(code, 10)
        except jlc.ApiError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        hit = [it for it in items if jlc.is_exact(code, it)]
        if hit:
            out["parts"][code] = {k: hit[0].get(k) for k in keep}
    SNAPSHOT.write_bytes((json.dumps(out, indent=1, ensure_ascii=True) + "\n").encode())
    return 0


def main(argv: list[str]) -> int:
    codes = list(EXACT) + list(EST_0402)
    if "--fetch" in argv and fetch(snapshot_codes()):
        return 2
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    parts = snap["parts"]
    bad = class_errors(parts, codes)
    if bad:
        print("sourcing rule (D13, D22): " + "; ".join(bad), file=sys.stderr)
        return 1
    ext = extended_codes(parts, codes)

    study = load_study()
    totals = package_totals(study.BLOCKS)
    errs = check_bom(totals)
    if errs:
        print("BOM disagrees with the placement study: " + "; ".join(errs), file=sys.stderr)
        return 1
    rem = remainder_0402(totals)
    nj = joints(totals)
    print(f"== Machine-placed BOM ({len(codes)} types, snapshot {snap['checked_utc']}; Extended:"
          f" {', '.join(f'{c} ({APPROVED_EXTENDED[c]})' for c in ext) or 'none'})")
    print(f"parts per board {sum(totals.values())}; joints per board {nj}; "
          f"0402 positions not attributed to a value {rem}")
    comp, rows = parts_cost(parts, rem, BOARDS_PCBA)
    for code, name, n, q, p in rows:
        print(f"  {code:<10} {name:<42} {n:>3}/board  order {q:>4} x ${p:.4f} = ${q*p:6.2f}")
    print(f"components for {BOARDS_PCBA} boards: ${comp:.2f}")

    pcb = PCB_BASE_USD + PCB_FINISH_USD[PCB_FINISH]
    print(f"\n== PCB: {BOARDS_PCB} pcs, 4 layers, 100 x 72 mm, {PCB_FINISH}: ${pcb:.2f}"
          f" (other finishes: " + ", ".join(f"{k} ${PCB_BASE_USD+v:.2f}"
                                            for k, v in PCB_FINISH_USD.items()) + ")")
    fees = pcba_fees(nj * BOARDS_PCBA, len(codes), BOARDS_PCBA, len(ext))
    ship = SHIP_JP_USD[SHIP_PLAN]
    totals_usd = {}
    for tier, f in fees.items():
        fee = sum(f.values())
        totals_usd[tier] = pcb + fee + comp + ship
        print(f"\n== {tier} PCBA, {BOARDS_PCBA} boards: fees ${fee:.2f}")
        for k, v in f.items():
            print(f"  {k:<30} ${v:7.2f}")
        print(f"JLCPCB order (PCB + PCBA + parts + {SHIP_PLAN} ${ship:.2f}):"
              f" ${totals_usd[tier]:.2f} = {totals_usd[tier]*JPY_PER_USD:,.0f} yen")

    pins = header_pins_per_board(study)
    print(f"\n== Akizuki, hand-soldered parts for {BOARDS_PCBA} units"
          f" ({pins} module header pins per board)")
    aki, arows = akizuki_cost(BOARDS_PCBA, pins)
    for p, c, y, q in arows:
        print(f"  {p:<62} {c:>8} {y:>5} x {q:>2} = {y*q:>6,}")
    print(f"Akizuki order: {aki:,} yen")

    print(f"\n== Total at {JPY_PER_USD:.0f} yen/USD (excludes Japanese import tax, M2 inserts,"
          " enclosure print)")
    for tier, usd in totals_usd.items():
        tot = usd * JPY_PER_USD + aki
        print(f"{tier}: {tot:,.0f} yen for {BOARDS_PCBA} units ({tot/BOARDS_PCBA:,.0f} yen per unit)")
    print(f"lid PCB, if ordered with it: +${LID_PCB_USD:.2f} = {LID_PCB_USD*JPY_PER_USD:,.0f} yen")

    bad = class_errors(parts, [RECEPTACLE, TAP])
    if bad:
        print("sourcing rule (D13, D22): " + "; ".join(bad), file=sys.stderr)
        return 1
    d = rev05_delta(parts, BOARDS_PCBA, pins)
    print(f"\n== Rev0.5 against r02 (D37 receptacles, D38 taps), {BOARDS_PCBA} units")
    print(f"JLCPCB adds: {d['receptacle_qty']} x {RECEPTACLE} ${d['receptacles_usd']:.2f},"
          f" 8 taps ${d['taps_usd']:.2f}, {d['joints']} joints ${d['joints_usd']:.2f},"
          f" a third Extended feeder ${d['feeder_usd']:.2f}: ${d['added_usd']:.2f}"
          f" = {d['added_usd']*JPY_PER_USD:,.0f} yen")
    print(f"Akizuki: {d['akizuki_old']:,} -> {d['akizuki_new']:,} yen (the "
          f"{RECEPTACLES_PER_BOARD * BOARDS_PCBA} modules and the header strips leave)")
    print(f"r02 {d['base_yen']:,.0f} yen -> Rev0.5 {d['total_yen']:,.0f} yen for {BOARDS_PCBA} units"
          f" ({d['net_yen']:+,.0f} yen; {d['total_yen']/BOARDS_PCBA:,.0f} yen per unit)")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
