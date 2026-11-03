"""Tests for impedance.py. Run: python -I -B design/experiments/stackup-impedance/test_impedance.py

Each check that guards the data is also run against a corrupted copy, which it must
reject (CLAUDE.md section 8: a checker never observed failing is not evidence).

The main model reference is JLCPCB's own impedance calculator, run in a browser
by the main session on 2026-11-03 (https://jlcpcb.com/pcb-impedance-calculator):
on JLC04161H-7628 a 50-ohm non-coplanar single-ended trace is 14.85 mil WITHOUT
solder mask (14.12 mil with). The differential run returned no result.
"""
import contextlib
import copy
import importlib.util
import io
import json
import math
import pathlib
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("impedance", HERE / "impedance.py")
imp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imp)

DATA = json.loads((HERE / "stackups.json").read_text(encoding="utf-8"))
STACKUPS = DATA["stackups"]
BY_ID = {s["id"]: s for s in STACKUPS}
JLC7628 = BY_ID[imp.JLCPCB_REF_STACKUP_ID]
H_7628, DK_7628 = imp.l1_l2(JLC7628)
T = imp.T_OUTER_MM
MIL = imp.MIL_MM
W_DATUM = imp.JLCPCB_SE_BARE_MIL * MIL          # 14.85 mil, JLCPCB, no mask


class HandCheck(unittest.TestCase):
    """Pin the HJ thickness correction to a worked value.

    H 0.2104 mm, T 1.6 mil, Er 4.4, W 14.85 mil (u 1.7927): du1 0.2486,
    dur 0.1627, Z01(u1) 88.0, Z01(ur) 90.17, Eeff0(ur) 3.3374,
    Eeff 3.1790 -> Z0 = 50.57 ohm. An earlier revision fed the single air
    increment du1 into both Z01 and Eeff and answered ~48-49 ohm; this test
    would have caught that defect.
    """

    def test_corrected_model_gives_50_57(self):
        z0 = imp.z0_microstrip(W_DATUM, H_7628, T, 4.4)
        self.assertAlmostEqual(z0, 50.57, delta=0.1)

    def test_single_increment_variant_fails_the_check(self):
        # The defective form: air increment du1 into Z01 and Eeff both.
        u = W_DATUM / H_7628
        u1 = u + imp.du1(u, T / H_7628)
        z_old = imp.z_air_u(u1) / math.sqrt(imp.eeff_microstrip(u1, 4.4))
        self.assertGreater(abs(z_old - 50.57), 0.5)


class JlcpcbCalculatorReference(unittest.TestCase):
    """MAIN reference: the model, without mask, must reproduce JLCPCB's
    calculator. At the page's published Dk 4.4 the model solves ~15.15 mil
    for the bare 50-ohm datum — +2%, inside +/-3% in width."""

    def test_hj_width_within_3pct_of_jlcpcb_datum(self):
        w = imp.solve_w_se(imp.JLCPCB_SE_TARGET_OHM, H_7628, T, DK_7628)
        self.assertAlmostEqual(w / W_DATUM, 1.0, delta=0.03)

    def test_ipc2141a_misses_the_same_tolerance(self):
        # The model choice itself is tested: at the SAME published Dk,
        # IPC-2141A gives ~13.50 mil, a ~9% miss — outside +/-3%.
        w_ipc = imp.solve_w_se_ipc(imp.JLCPCB_SE_TARGET_OHM, H_7628, T, DK_7628)
        self.assertGreater(abs(w_ipc / W_DATUM - 1.0), 0.03)

    def test_corrupted_dk_breaks_the_reference(self):
        # Negative test: a Dk corrupted +20% must move the solved width
        # outside the 3% reproduction tolerance, so the check can fail.
        w_bad = imp.solve_w_se(imp.JLCPCB_SE_TARGET_OHM, H_7628, T, DK_7628 * 1.2)
        self.assertGreater(abs(w_bad / W_DATUM - 1.0), 0.03)

    def test_mask_effect_on_single_line_is_small_and_correct_direction(self):
        # JLCPCB's masked-board width is 14.12 mil; the bare model reads that
        # width as ~52.0 ohm, i.e. the mask removes ~2 ohm at 50 ohm.
        # Bound is loose but pins direction and order of magnitude.
        drop = imp.z0_microstrip(imp.JLCPCB_SE_MASKED_MIL * MIL,
                                 H_7628, T, DK_7628) - 50.0
        self.assertGreater(drop, 1.0)
        self.assertLess(drop, 3.0)


class PhysicalSanity(unittest.TestCase):
    def test_odd_mode_below_even_mode(self):
        for s in imp.GAPS_MM:
            z_e, z_o = imp.even_odd(0.30, s, H_7628, T, DK_7628)
            self.assertLess(z_o, z_e)

    def test_pair_converges_to_two_single_lines_at_wide_gap(self):
        # At S >> H the coupling vanishes and Zdiff approaches twice the
        # pair model's own single-line value zl = z0_u(ur).
        w = 0.30
        z_far = imp.zdiff(w, 5.0, H_7628, T, DK_7628)
        ur = w / H_7628 + imp.dur(w / H_7628, T / H_7628, DK_7628)
        z_two = 2.0 * imp.z0_u(ur, DK_7628)
        self.assertAlmostEqual(z_far / z_two, 1.0, delta=0.01)

    def test_zdiff_falls_as_w_rises(self):
        for s in imp.GAPS_MM:
            self.assertGreater(imp.zdiff(0.15, s, H_7628, T, DK_7628),
                               imp.zdiff(0.20, s, H_7628, T, DK_7628))

    def test_zdiff_falls_as_s_falls(self):
        for w in (0.15, 0.25, 0.35):
            self.assertGreater(imp.zdiff(w, 0.20, H_7628, T, DK_7628),
                               imp.zdiff(w, 0.15, H_7628, T, DK_7628))


class SolverAgainstCorruption(unittest.TestCase):
    """A corrupted input must move the answer far enough to be caught.

    JLCPCB's standard impedance tolerance is +/-10% (capabilities page), so a
    |Zdiff - 90| above half that band (4.5 ohm) at the solved width means the
    geometry no longer meets target with real margin.
    """

    def setUp(self):
        self.w90 = imp.solve_w(90.0, 0.15, H_7628, T, DK_7628)
        self.assertIsNotNone(self.w90)
        self.assertAlmostEqual(
            imp.zdiff(self.w90, 0.15, H_7628, T, DK_7628), 90.0, places=4)

    def test_dk_plus_20pct_is_caught(self):
        moved = imp.zdiff(self.w90, 0.15, H_7628, T, DK_7628 * 1.20)
        self.assertGreater(abs(moved - 90.0), 4.5)
        w2 = imp.solve_w(90.0, 0.15, H_7628, T, DK_7628 * 1.20)
        self.assertNotAlmostEqual(w2, self.w90, delta=0.02)

    def test_halved_height_is_caught(self):
        moved = imp.zdiff(self.w90, 0.15, H_7628 / 2, T, DK_7628)
        self.assertGreater(abs(moved - 90.0), 4.5)

    def test_unreachable_target_returns_none(self):
        self.assertIsNone(imp.solve_w(400.0, 0.15, H_7628, T, DK_7628))


def run_main(stackups):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return imp.main(stackups)


class ExitStatus(unittest.TestCase):
    """The exit status guards the recommended pair (D27) and the data, not the
    feasibility of every stackup: 7628C/F are unreachable on the real data, and
    main() must still return 0 for it."""

    def test_real_data_exits_0_with_unreachable_stackups_present(self):
        self.assertEqual(run_main(copy.deepcopy(STACKUPS)), 0)

    def test_recommended_pair_is_inside_the_band(self):
        z_nom, z_narrow, z_wide = imp.recommended_pair(JLC7628)
        self.assertTrue(81.0 <= z_nom <= 99.0, z_nom)
        self.assertGreater(z_narrow, z_nom)
        self.assertLess(z_wide, z_nom)

    def test_missing_data_exits_1(self):
        bad = copy.deepcopy(STACKUPS)
        next(s for s in bad if s["id"] == "JLC04161H-3313")["prepreg_top"][0]["dk"] = None
        self.assertEqual(run_main(bad), 1)

    def test_absent_recommended_stackup_exits_1(self):
        bad = [s for s in copy.deepcopy(STACKUPS) if s["id"] != imp.REC_STACKUP_ID]
        self.assertEqual(run_main(bad), 1)

    def test_recommended_pair_out_of_band_exits_1(self):
        # A halved L1-L2 prepreg (and a core grown to keep the total) drops the
        # recommended pair far below 81 ohm; main() must refuse it.
        bad = copy.deepcopy(STACKUPS)
        st = next(s for s in bad if s["id"] == imp.REC_STACKUP_ID)
        st["prepreg_top"][0]["thickness_mm"] /= 2
        st["inner"]["core_mm"] += st["prepreg_top"][0]["thickness_mm"]
        self.assertLess(imp.recommended_pair(st)[0], 81.0)
        self.assertEqual(run_main(bad), 1)


class StackupData(unittest.TestCase):
    """stackups.json sanity: totals inside JLCPCB's +/-10% thickness tolerance
    (1.44-1.76 mm for a 1.6 mm board, capabilities page), every needed value
    present, ply Dk consistent with the page's dielectric-constant table."""

    def test_nineteen_stackups_present(self):
        self.assertEqual(len(STACKUPS), 19)
        self.assertIn("No requirement", BY_ID)

    def test_every_stackup_has_data_and_passes_checks(self):
        for st in STACKUPS:
            self.assertEqual(imp.check_stackup(st), [], st["id"])

    def test_every_stackup_sums_to_1_6mm_within_jlcpcb_tolerance(self):
        for st in STACKUPS:
            total = imp.total_thickness(st)
            self.assertTrue(1.44 <= total <= 1.76,
                            f"{st['id']}: {total:.4f} mm outside 1.44-1.76")

    def test_corrupted_stackup_is_rejected(self):
        bad = copy.deepcopy(JLC7628)
        bad["inner"]["core_mm"] = 0.20          # sum drops to ~0.72 mm
        self.assertGreaterEqual(imp.total_thickness(bad), 0.0)   # it computes
        self.assertFalse(1.44 <= imp.total_thickness(bad) <= 1.76)
        self.assertNotEqual(imp.check_stackup(bad), [])

    def test_missing_dk_is_rejected(self):
        bad = copy.deepcopy(JLC7628)
        bad["prepreg_top"][0]["dk"] = None
        self.assertNotEqual(imp.check_stackup(bad), [])

    def test_ply_dk_matches_published_table(self):
        table = DATA["meta"]["dielectric_constants"]["prepreg"]
        for st in STACKUPS:
            for ply in st["prepreg_top"] + st["prepreg_bottom"]:
                self.assertEqual(ply["dk"], table[ply["style"]],
                                 f"{st['id']} {ply['style']}")
            self.assertEqual(st["inner"]["core_dk"],
                             DATA["meta"]["dielectric_constants"]["core"])

    def test_default_stackup_is_identical_to_jlc04161h_7628(self):
        def bare(s):
            s = copy.deepcopy(s)
            s.pop("id"), s.pop("ordinal_on_page")
            return s
        self.assertEqual(bare(BY_ID["No requirement"]), bare(JLC7628))


if __name__ == "__main__":
    unittest.main()
