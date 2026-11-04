"""Negative tests for placement_study.py (CLAUDE.md Sec. 8: a checker never seen failing is
not evidence). Each test corrupts one aspect of the layout and expects the named failure.

Usage: python -I design/experiments/oi-23-placement/test_placement_study.py
"""
import copy
import importlib.util
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent


def load():
    spec = importlib.util.spec_from_file_location("placement_study", HERE / "placement_study.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LayoutChecks(unittest.TestCase):
    def setUp(self):
        self.m = load()

    def fails(self):
        return self.m.check_layout()[0]

    def assertFailure(self, text):
        f = self.fails()
        self.assertTrue(any(text in x for x in f), f"expected '{text}' in {f}")

    def test_baseline_passes(self):
        self.assertEqual(self.fails(), [])

    def test_overlap(self):
        self.m.PLACE["J3"] = (30.0, 0.0, 0)            # onto J2
        self.assertFailure("J2 and J3")

    def test_off_board(self):
        self.m.PLACE["U7"] = (95.0, 19.0, 0)           # past the right edge
        self.assertFailure("U7 leaves the board")

    def test_region_too_small(self):
        r, bl = self.m.REGIONS["R_AFEA"]
        self.m.REGIONS["R_AFEA"] = ((r[0], r[1], r[2], 20.0), bl)
        self.assertFailure("R_AFEA: needs")

    def test_package_wider_than_region(self):
        self.m.REGIONS["R_GAP"] = (self.m.REGIONS["R_GAP"][0], ["OC"])   # SOIC-8 into 7 mm
        self.m.REGIONS["R_LDO"] = (self.m.REGIONS["R_LDO"][0], ["LDO"])
        self.assertFalse(any("R_GAP: needs" in x for x in self.fails()))
        r = self.m.REGIONS["R_GAP"][0]
        self.m.REGIONS["R_GAP"] = ((r[0], r[1], 5.0, r[3]), ["OC"])
        self.assertFailure("R_GAP: a OC package does not fit")

    def test_tall_part_under_module(self):
        self.m.UNDER["J4"] = ["J4IN", "TVS4"]          # SMB, 2.3 mm, under a module
        self.m.REGIONS["R_PWR4"] = (self.m.REGIONS["R_PWR4"][0], [])
        self.assertFailure("under J4: TVS4 is 2.3 mm tall")

    def test_block_left_out(self):
        self.m.REGIONS["R_V12"] = (self.m.REGIONS["R_V12"][0], [])
        self.assertFailure("blocks not placed: ['V12']")

    def test_block_placed_twice(self):
        r, bl = self.m.REGIONS["R_TVS1"]
        self.m.REGIONS["R_TVS1"] = (r, bl + ["V12"])   # V12 also stays in R_V12
        self.assertFailure("blocks placed more than once: ['V12']")

    def test_mau_too_close(self):
        self.m.PLACE["U5"] = (77.0, 30.0, 90)          # 1.4 mm from U17
        self.assertFailure("MAU104 is")

    def test_pitch(self):
        self.m.PLACE["J3"] = (38.5, 0.0, 0)            # 20.5 mm is fine
        self.m.REGIONS["R_GAP"] = ((38.5, 16.0, 0.1, 0.1), [])
        self.assertFalse(any("pitch" in x for x in self.fails()))
        self.m.PLACE["J2"] = (19.0, 0.0, 0)            # 19.5 mm is not
        self.assertFailure("J2-J3 pitch")

    def test_connector_off_edge(self):
        self.m.PLACE["J1"] = (66.0, 56.0, 180)
        self.assertFailure("J1 is not on the back edge")

    def test_corridor_through_front_end(self):
        x, y, w, h = self.m.KEEPOUT["USB_CORRIDOR"]
        self.m.KEEPOUT["USB_CORRIDOR"] = (x, y + 4.0, w, h)
        self.assertFailure("USB corridor crosses R_AFEA")

    def test_corridor_misses_hub(self):
        r, bl = self.m.REGIONS["R_HUB"]
        self.m.REGIONS["R_HUB"] = ((r[0], r[1] + 2.0, r[2], r[3] - 2.0), bl)   # 2.5 mm off
        self.assertFailure("USB corridor does not reach the hub (R_HUB)")

    def test_header_too_low(self):
        self.m.HEADER_PLASTIC_MIN = 1.9                # 1.5 mm parts + 0.5 mm need 2.0
        self.assertFailure("header plastic 1.9 mm is below")

    def test_under_rect_over_receptacle(self):
        self.m.USBC_UNDER.append((5.8, 0.5, 8.5, 7.9))  # the pre-D33 rectangle
        self.assertFailure("overlaps the module's receptacle body")

    def test_under_rect_over_insulator(self):
        self.m.USBC_UNDER[0] = (0.5, 8.6, 19.0, 3.4)   # 12.0 > the row's 11.85
        self.assertFailure("overlaps the module's header insulator")

    def test_under_rect_off_module(self):
        self.m.USBC_UNDER[0] = (1.5, 8.2, 19.0, 3.4)   # to x = 20.5
        self.assertFailure("leaves the USB-C module")

    def test_credit_space_is_outline_less_insulators(self):
        self.assertAlmostEqual(self.m.under_space("USBC"),
                               20 * 15 - (7 * 2.54 * 2.5 + 2 * (2 * 2.54) * 2.5), places=6)

    def test_necessary_area_rejects_85x35_with_routing(self):
        k = self.m.break_even_k(85 * 35)
        self.assertIsNotNone(k)
        self.assertGreater(self.m.necessary_area(k)[0], 85 * 35)
        self.assertLessEqual(self.m.necessary_area(round(k - 0.001, 3))[0], 85 * 35)
        self.assertLess(k, 1.05)                       # any real routing space excludes it

    def test_necessary_area_terms_add_up(self):
        for k in self.m.K_SWEEP:
            req, hand, smd, credit, space, low = self.m.necessary_area(k)
            self.assertAlmostEqual(req, hand + 4 * 7 * 7 + smd - credit)
            self.assertEqual(credit, min(space, low))

    def test_credit_counts_only_low_parts(self):
        low = self.m.necessary_area(1.0)[5]
        self.m.UNDER_MAX_H = 0.5                       # now no package qualifies but FID/TC2030
        self.assertLess(self.m.necessary_area(1.0)[5], low)


if __name__ == "__main__":
    unittest.main(verbosity=1)
