#!/usr/bin/env python3
"""Negative-tested kit checker (CLAUDE.md section 8 rule for automated checks).

Run from the repository root:
    python -I -B tests/fixtures/pre-layout-bench/test_kit.py

The real kit.json must pass; every check is then shown failing on a
deliberately corrupted copy.
"""
from __future__ import annotations

import contextlib
import copy
import importlib.util
import io
import json
import pathlib
import unittest
from decimal import Decimal

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("kit", HERE / "kit.py")
kit_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit_mod)


def real_kit() -> dict:
    return json.loads((HERE / "kit.json").read_text(encoding="utf-8"))


def run_main(kit: dict) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = kit_mod.main(copy.deepcopy(kit))
    return code, out.getvalue(), err.getvalue()


def item(kit: dict, iid: str) -> dict:
    return next(i for i in kit["items"] if i["id"] == iid)


class RealData(unittest.TestCase):
    def test_real_kit_is_clean(self):
        errs = kit_mod.check(real_kit())
        self.assertEqual(errs, [])
        code, out, _ = run_main(real_kit())
        self.assertEqual(code, 0)
        self.assertIn("kit check: OK", out)

    def test_printed_total_is_the_sum_of_its_terms(self):
        kit = real_kit()
        code, out, _ = run_main(kit)
        self.assertEqual(code, 0)
        subtotal, shipping, cheapest = kit_mod.totals(kit)
        self.assertIn(f"subtotal: {subtotal:,} yen", out)
        self.assertIn(f"total: {subtotal + cheapest:,} yen", out)
        want = sum(i["packs_to_buy"] * i["price_yen"]
                   for i in kit["items"] if i["vendor"] == "akizuki")
        self.assertEqual(subtotal, want)
        printed_lines = 0
        for line in out.splitlines():
            if line.startswith("total:"):
                printed = int(line.split("total:")[1].split("yen")[0]
                              .strip().replace(",", ""))
                self.assertEqual(printed, subtotal + cheapest)
            if " pack " in line and " = " in line:
                printed_lines += int(line.split(" = ")[1].split()[0].replace(",", ""))
        self.assertEqual(printed_lines, subtotal)

    def test_lcsc_subtotal_is_the_sum_of_its_lines(self):
        kit = real_kit()
        code, out, _ = run_main(kit)
        self.assertEqual(code, 0)
        lines = [Decimal(line.split(" = ")[1].split()[0])
                 for line in out.splitlines() if " pcs (min " in line]
        self.assertEqual(len(lines), len([i for i in kit["items"] if i["vendor"] == "lcsc"]))
        self.assertEqual(sum(lines, Decimal("0.00")), kit_mod.lcsc_subtotal_usd(kit))
        self.assertIn(f"LCSC subtotal: ${kit_mod.lcsc_subtotal_usd(kit)}", out)


class Corrupted(unittest.TestCase):
    def fails(self, kit: dict, needle: str) -> None:
        errs = kit_mod.check(kit)
        self.assertTrue(errs, "expected the corruption to be detected")
        self.assertTrue(any(needle in e for e in errs),
                        f"{needle!r} not found in {errs}")
        code, _, errout = run_main(kit)
        self.assertEqual(code, 1)
        self.assertIn(needle, errout)

    def test_uncovered_need(self):
        k = real_kit()
        k["items"] = [i for i in k["items"] if i["id"] != "r1m"]  # M12 uncovered
        self.fails(k, "need M12")

    def test_uncovered_need_lcsc(self):
        k = real_kit()
        k["items"] = [i for i in k["items"] if i["id"] != "op07cdr"]  # M1 uncovered
        self.fails(k, "need M1:")

    def test_uncovered_component(self):
        k = real_kit()
        k["items"] = [i for i in k["items"] if i["id"] != "c330p"]
        self.fails(k, "330pF")

    def test_short_quantity(self):
        k = real_kit()
        item(k, "tsl-shunt")["covers"][0]["qty"] = 1  # M3 needs 2
        self.fails(k, "need M3")

    def test_missing_stock(self):
        k = real_kit()
        k["items"][0].pop("stock")
        self.fails(k, "missing field stock")

    def test_missing_akizuki_price(self):
        k = real_kit()
        item(k, "mcp3208").pop("price_yen")
        self.fails(k, "missing field price_yen")

    def test_missing_lcsc_price(self):
        k = real_kit()
        item(k, "ao3401a").pop("price_usd")
        self.fails(k, "missing field price_usd")

    def test_unknown_vendor(self):
        k = real_kit()
        item(k, "op07cdr")["vendor"] = "elsewhere"
        self.fails(k, "unknown vendor elsewhere")

    def test_missing_vendor(self):
        k = real_kit()
        item(k, "pga2040").pop("vendor")
        self.fails(k, "missing field vendor")

    def test_stock_below_packs(self):
        k = real_kit()
        item(k, "pga2040")["stock"] = 0
        self.fails(k, "stock 0 < packs_to_buy")

    def test_lcsc_below_minimum_order(self):
        k = real_kit()
        it = item(k, "op07cdr")
        it["packs_to_buy"] = 2
        it["covers"] = [{"need": "M1", "qty": 2}]
        self.fails(k, "below the minimum order 5")

    def test_allocation_over_pieces(self):
        k = real_kit()
        item(k, "op07cdr")["covers"] = [{"need": "M1", "qty": 6}]  # 6 > 5 bought
        self.fails(k, "allocates")

    def test_orphan_item(self):
        k = real_kit()
        k["items"].append({"id": "ghost", "vendor": "akizuki", "covers": [],
                           "code": "g000000", "title": "x", "url": "u", "pack_size": 1,
                           "packs_to_buy": 1, "price_yen": 1, "stock": 1,
                           "checked": "2026-11-03", "same_as_design": False})
        self.fails(k, "orphaned")

    def test_orphan_unknown_need(self):
        k = real_kit()
        k["items"][0]["covers"] = [{"need": "ZZ9", "qty": 1}]
        self.fails(k, "unknown need")

    def test_duplicate_id(self):
        k = real_kit()
        k["needs"].append(copy.deepcopy(k["needs"][0]))
        self.fails(k, "duplicate need id")

    def test_duplicate_item_id(self):
        k = real_kit()
        k["items"].append(copy.deepcopy(k["items"][0]))
        self.fails(k, "duplicate item id")

    def test_shipping_rule_drives_the_total(self):
        k = real_kit()
        subtotal, shipping, cheapest = kit_mod.totals(k)
        rule = k["meta"]["akizuki_shipping_rule"]
        if subtotal >= rule["free_shipping_subtotal_yen"]:
            self.assertEqual(cheapest, 0)
        else:
            self.assertEqual(cheapest, min(rule["per_parcel_yen"].values()))
        # flip the rule: a corrupted meta must change the computed shipping,
        # proving the code reads it rather than a constant
        k2 = copy.deepcopy(k)
        k2["meta"]["akizuki_shipping_rule"]["free_shipping_subtotal_yen"] = 999999
        _, _, cheap2 = kit_mod.totals(k2)
        self.assertEqual(cheap2, min(rule["per_parcel_yen"].values()))

    def test_lcsc_items_stay_out_of_the_akizuki_subtotal(self):
        k = real_kit()
        before, _, _ = kit_mod.totals(k)
        item(k, "op07cdr")["price_yen"] = 100000  # must be ignored: it is an LCSC item
        after, _, _ = kit_mod.totals(k)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
