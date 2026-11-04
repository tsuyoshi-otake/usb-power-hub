"""Tests for cost_estimate.py. Run: python -I -B design/experiments/cost-estimate/test_cost_estimate.py

Each check that guards the BOM is also run against a corrupted copy, which it must reject
(CLAUDE.md §8: a checker never observed failing is not evidence).
"""
import copy
import importlib.util
import json
import pathlib
import re
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cost_estimate", HERE / "cost_estimate.py")
ce = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ce)
STUDY = ce.load_study()


def parts_md_codes():
    text = (ce.ROOT / "requirements" / "parts.md").read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if l.startswith("python tools/jlc_stock.py C"))
    return re.findall(r"C\d+", line)


class Bom(unittest.TestCase):
    def test_bom_matches_the_placement_study(self):
        self.assertEqual(ce.check_bom(ce.package_totals(STUDY.BLOCKS)), [])

    def test_a_wrong_count_is_caught(self):
        saved = ce.EXACT["C8545"]
        try:
            ce.EXACT["C8545"] = (saved[0], saved[1], saved[2] + 1)
            errs = ce.check_bom(ce.package_totals(STUDY.BLOCKS))
        finally:
            ce.EXACT["C8545"] = saved
        self.assertTrue(any(e.startswith("SOT-23") for e in errs), errs)

    def test_a_study_change_is_caught(self):
        blocks = copy.deepcopy(STUDY.BLOCKS)
        blocks["AMPS_A"].append(("SOIC-8", 1))
        errs = ce.check_bom(ce.package_totals(blocks))
        self.assertTrue(any(e.startswith("SOIC-8") for e in errs), errs)

    def test_too_many_0402_values_is_caught(self):
        totals = ce.package_totals(STUDY.BLOCKS)
        totals["0402"] = sum(n for _, n in ce.EST_0402.values()) - 1
        self.assertTrue(any(e.startswith("0402") for e in ce.check_bom(totals)))

    def test_codes_are_the_40_in_parts_md(self):
        bom = list(ce.EXACT) + list(ce.EST_0402)
        md = parts_md_codes()
        self.assertEqual(len(md), 40)
        self.assertEqual(sorted(bom), sorted(md))
        self.assertNotEqual(sorted(bom[1:]), sorted(md))      # a dropped code would show

    def test_snapshot_is_basic_except_the_approved_exception(self):
        snap = json.loads(ce.SNAPSHOT.read_text(encoding="utf-8"))["parts"]
        codes = list(ce.EXACT) + list(ce.EST_0402)
        self.assertEqual(ce.class_errors(snap, codes), [])
        self.assertEqual(ce.extended_codes(snap, codes), ["C2040"])
        self.assertEqual(ce.APPROVED_EXTENDED, {"C2040": "D29"})

    def test_an_unapproved_extended_part_is_caught(self):
        snap = json.loads(ce.SNAPSHOT.read_text(encoding="utf-8"))["parts"]
        bad = copy.deepcopy(snap)
        bad["C7433"]["componentLibraryType"] = "expand"
        errs = ce.class_errors(bad, list(ce.EXACT))
        self.assertTrue(any(e.startswith("C7433") for e in errs), errs)
        del bad["C9002"]
        self.assertTrue(any(e.startswith("C9002: not in") for e in ce.class_errors(bad, ["C9002"])))


class Arithmetic(unittest.TestCase):
    def test_joints(self):
        self.assertEqual(ce.joints({"0402": 1, "SOIC-8": 1, "SOT-23": 2}), 2 + 8 + 6)

    def test_tier_price(self):
        tiers = [{"startNumber": 20, "endNumber": -1, "productPrice": 0.5},
                 {"startNumber": 1, "endNumber": 19, "productPrice": 1.0}]
        self.assertEqual(ce.tier_price(tiers, 19), 1.0)
        self.assertEqual(ce.tier_price(tiers, 20), 0.5)
        with self.assertRaises(ValueError):
            ce.tier_price(tiers[:1], 5)

    def test_order_qty(self):
        self.assertEqual(ce.order_qty(3, 2, {"lossNumber": 4, "leastPatchNumber": 20}), 20)
        self.assertEqual(ce.order_qty(17, 2, {"lossNumber": 5, "leastPatchNumber": 0}), 39)

    def test_economic_fees(self):
        fees = ce.pcba_fees(1090, 40, 2, 1)["Economic"]
        self.assertAlmostEqual(sum(fees.values()), 8.18 + 1.53 + 1090 * 0.0016 + 3.07 + 0.45,
                               places=6)
        none = ce.pcba_fees(1090, 40, 2, 0)["Economic"]
        self.assertAlmostEqual(sum(fees.values()) - sum(none.values()), 3.07, places=6)

    def test_akizuki_free_shipping_threshold(self):
        seen = set()
        for units in (1, 2, 4):
            yen, rows = ce.akizuki_cost(units, False)
            ship = rows[-1][2]
            free = yen - ship >= ce.AKIZUKI_FREE_SHIPPING_YEN
            self.assertEqual(ship, 0 if free else ce.AKIZUKI_SHIPPING_YEN, units)
            seen.add(free)
        self.assertEqual(seen, {True, False})          # both branches exercised


if __name__ == "__main__":
    unittest.main()
