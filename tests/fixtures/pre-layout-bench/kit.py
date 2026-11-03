#!/usr/bin/env python3
"""Pre-layout bench kit: check kit.json and print the purchase lists (Akizuki, LCSC).

Usage (from the repository root):
    python -I -B tests/fixtures/pre-layout-bench/kit.py

Checks (each one is also exercised by a negative test in test_kit.py):
  * every need is covered: for each component of the need, the pieces that
    covering items of the same 'value' allocate to it meet its qty;
  * an item never allocates more pieces than pack_size x packs_to_buy;
  * every item names a known vendor and has a code, its vendor's price field,
    a stock figure and a checked date;
  * stock >= packs_to_buy;
  * an LCSC item buys at least its minimum order (min_buy);
  * no orphaned item (every covers entry names a real need);
  * no duplicate need or item ids.

Akizuki shipping is computed from meta.akizuki_shipping_rule, not from a
constant, over Akizuki items only. LCSC shipping is not computed: LCSC shows it
at checkout, and kit.json records no rule for it.
Exit 0 when clean, 1 on any problem.
"""
from __future__ import annotations

import json
import pathlib
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

HERE = pathlib.Path(__file__).resolve().parent
KIT_JSON = HERE / "kit.json"

REQUIRED_ITEM_FIELDS = (
    "id", "vendor", "covers", "code", "title", "url", "pack_size", "packs_to_buy",
    "stock", "checked", "same_as_design",
)
# vendor -> fields that vendor's items must also carry
VENDOR_FIELDS = {
    "akizuki": ("price_yen",),
    "lcsc": ("price_usd", "min_buy"),
}
CENT = Decimal("0.01")


def load_kit(path: pathlib.Path = KIT_JSON) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def vendor_items(kit: dict, vendor: str) -> list[dict]:
    return [i for i in kit["items"] if i.get("vendor") == vendor]


def check(kit: dict) -> list[str]:
    """Return every problem found; an empty list means the kit is clean."""
    errs: list[str] = []
    needs = kit.get("needs", [])
    items = kit.get("items", [])
    need_by_id = {n["id"]: n for n in needs}

    for label, seq in (("need", needs), ("item", items)):
        seen = set()
        for e in seq:
            eid = e.get("id")
            if eid in seen:
                errs.append(f"duplicate {label} id: {eid}")
            seen.add(eid)

    # coverage: per need (and per component), allocated pieces must meet the qty
    covered: dict[str, dict[str, int]] = {n["id"]: {} for n in needs}
    covered_plain: dict[str, int] = {n["id"]: 0 for n in needs}
    for it in items:
        for cov in it.get("covers", []):
            nid = cov.get("need")
            if nid not in need_by_id:
                errs.append(f"item {it.get('id')}: covers unknown need {nid}")
                continue
            q = int(cov.get("qty", 0))
            val = it.get("value", it.get("id"))
            covered[nid][val] = covered[nid].get(val, 0) + q
            covered_plain[nid] += q
    for n in needs:
        comps = n.get("components")
        if comps:
            for c in comps:
                got = covered[n["id"]].get(c["value"], 0)
                if got < c["qty"]:
                    errs.append(
                        f"need {n['id']}: component {c['value']} short:"
                        f" {got} of {c['qty']} covered")
        elif covered_plain[n["id"]] < n["qty"]:
            errs.append(
                f"need {n['id']}: short: {covered_plain[n['id']]} of {n['qty']} covered")

    for it in items:
        iid = it.get("id")
        vendor = it.get("vendor")
        fields = REQUIRED_ITEM_FIELDS
        if vendor is not None and vendor not in VENDOR_FIELDS:
            errs.append(f"item {iid}: unknown vendor {vendor}")
        else:
            fields = fields + VENDOR_FIELDS.get(vendor, ())
        for f in fields:
            if f not in it or it[f] in (None, ""):
                errs.append(f"item {iid}: missing field {f}")
        if not it.get("covers"):
            errs.append(f"item {iid}: orphaned (covers no need)")
            continue
        try:
            pieces = int(it["pack_size"]) * int(it["packs_to_buy"])
            alloc = sum(int(c.get("qty", 0)) for c in it["covers"])
            if alloc > pieces:
                errs.append(
                    f"item {iid}: allocates {alloc} pieces but"
                    f" {it['pack_size']} x {it['packs_to_buy']} = {pieces}")
            if it.get("stock") is not None and int(it["stock"]) < int(it["packs_to_buy"]):
                errs.append(
                    f"item {iid}: stock {it['stock']} < packs_to_buy"
                    f" {it['packs_to_buy']}")
            if vendor == "lcsc" and it.get("min_buy") is not None \
                    and pieces < int(it["min_buy"]):
                errs.append(
                    f"item {iid}: {pieces} pieces is below the minimum order"
                    f" {it['min_buy']}")
            if vendor == "lcsc" and it.get("price_usd") not in (None, ""):
                Decimal(str(it["price_usd"]))
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            errs.append(f"item {iid}: bad numeric field ({exc!r})")
    return errs


def totals(kit: dict) -> tuple[int, dict[str, int], int]:
    """Akizuki (subtotal, shipping per carrier, cheapest shipping) from the meta rule."""
    subtotal = sum(int(i["packs_to_buy"]) * int(i["price_yen"])
                   for i in vendor_items(kit, "akizuki"))
    rule = kit["meta"]["akizuki_shipping_rule"]
    per_parcel = rule["per_parcel_yen"]
    if subtotal >= int(rule["free_shipping_subtotal_yen"]):
        shipping = {k: 0 for k in per_parcel}
    else:
        shipping = {k: int(v) for k, v in per_parcel.items()}
    cheapest = min(shipping.values()) if shipping else 0
    return subtotal, shipping, cheapest


def lcsc_line_usd(item: dict) -> Decimal:
    """Pieces x unit price, rounded to the cent as LCSC's extended price is."""
    pieces = int(item["pack_size"]) * int(item["packs_to_buy"])
    return (Decimal(str(item["price_usd"])) * pieces).quantize(CENT, rounding=ROUND_HALF_UP)


def lcsc_subtotal_usd(kit: dict) -> Decimal:
    return sum((lcsc_line_usd(i) for i in vendor_items(kit, "lcsc")), Decimal("0.00"))


def render(kit: dict) -> str:
    """The two purchase lists with their totals, as printed by main()."""
    subtotal, shipping, cheapest = totals(kit)
    rule = kit["meta"]["akizuki_shipping_rule"]
    out = [f"== Akizuki purchase list (yen, tax incl., checked {kit['meta']['date']})"]
    for i in vendor_items(kit, "akizuki"):
        line = int(i["packs_to_buy"]) * int(i["price_yen"])
        sub = "" if i.get("same_as_design") else " (not a design part)"
        out.append(f"  {i['id']:<11} {i['code']:<8} pack {i['pack_size']:>3} x {i['packs_to_buy']:<2} "
                   f"@ {i['price_yen']:>5} = {line:>6,}  "
                   f"[{', '.join(c['need'] for c in i['covers'])}]{sub}")
    out.append(f"subtotal: {subtotal:,} yen")
    ship_parts = ", ".join(f"{k} {v} yen/parcel" for k, v in shipping.items())
    out.append(f"shipping: {ship_parts}"
               f" (rule: free at >= {rule['free_shipping_subtotal_yen']:,} yen"
               " subtotal; parcels can multiply with size/weight)")
    out.append(f"total: {subtotal + cheapest:,} yen"
               f" ({subtotal:,} + {cheapest} shipping, cheapest carrier)")
    out.append("")
    out.append(f"== LCSC purchase list (USD, checked {kit['meta']['date']})")
    for i in vendor_items(kit, "lcsc"):
        pieces = int(i["pack_size"]) * int(i["packs_to_buy"])
        out.append(f"  {i['id']:<11} {i['code']:<8} {pieces:>3} pcs (min {i['min_buy']})"
                   f" @ {i['price_usd']} = {lcsc_line_usd(i)}"
                   f"  [{', '.join(c['need'] for c in i['covers'])}]")
    out.append(f"LCSC subtotal: ${lcsc_subtotal_usd(kit)}"
               " (shipping not computed: LCSC shows it at checkout)")
    return "\n".join(out)


def main(kit: dict) -> int:
    errs = check(kit)
    try:
        print(render(kit))
    except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
        errs.append(f"cannot total the kit ({exc!r})")
    if errs:
        print("\nPROBLEMS:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("kit check: OK")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(load_kit()))
