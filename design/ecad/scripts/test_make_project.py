"""Negative tests for make_project.py's check (CLAUDE.md 8: a checker never observed failing
is not evidence).

Run with KiCad's Python from the repository root, after make_project.py has written
design/ecad/source:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_make_project.py

Each test copies the two source files into a temporary directory, corrupts one aspect
and runs `make_project.py --check DIR` in a new process, because pcbnew caches a loaded
project within a process. The unchanged copy must pass; every corruption must fail and be
named in the output. The source files themselves are never modified.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE / "make_project.py"
SOURCE = HERE.parents[0] / "source"
NAME = "usb-power-hub"
EXTS = (".kicad_pcb", ".kicad_pro")


def run_check(edit_pcb=None, edit_pro=None):
    """Copy, corrupt, check. Returns (exit status, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        for ext in EXTS:
            shutil.copyfile(SOURCE / f"{NAME}{ext}", d / f"{NAME}{ext}")
        if edit_pcb:
            p = d / f"{NAME}.kicad_pcb"
            text = p.read_text(encoding="utf-8")
            new = edit_pcb(text)
            assert new != text, "the corruption changed nothing"
            p.write_text(new, encoding="utf-8", newline="\n")
        if edit_pro:
            p = d / f"{NAME}.kicad_pro"
            pro = json.loads(p.read_text(encoding="utf-8"))
            edit_pro(pro)
            p.write_text(json.dumps(pro, indent=2) + "\n", encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), "--check", str(d)],
                           capture_output=True, text=True, encoding="utf-8", timeout=120)
        return r.returncode, r.stdout + r.stderr


def classes(pro):
    return {c["name"]: c for c in pro["net_settings"]["classes"]}


class CheckTest(unittest.TestCase):
    def assertFailsWith(self, status_out, *needles):
        status, out = status_out
        self.assertEqual(status, 1, out)
        self.assertIn("checks: FAIL", out)
        for n in needles:
            self.assertIn(n, out)

    def test_unchanged_copy_passes(self):
        status, out = run_check()
        self.assertEqual(status, 0, out)
        self.assertIn("checks: PASS", out)

    def test_clearance_rule(self):
        def edit(pro):
            pro["board"]["design_settings"]["rules"]["min_clearance"] = 0.10
        self.assertFailsWith(run_check(edit_pro=edit), "m_MinClearance", "rule min_clearance")

    def test_edge_clearance_rule(self):
        def edit(pro):
            pro["board"]["design_settings"]["rules"]["min_copper_edge_clearance"] = 0.5
        self.assertFailsWith(run_check(edit_pro=edit), "m_CopperEdgeClearance")

    def test_usb_pair_gap(self):
        def edit(pro):
            classes(pro)["USB_HS"]["diff_pair_gap"] = 0.20
        self.assertFailsWith(run_check(edit_pro=edit), "USB_HS.diff_pair_gap")

    def test_usb_class_missing(self):
        def edit(pro):
            pro["net_settings"]["classes"] = [classes(pro)["Default"]]
        self.assertFailsWith(run_check(edit_pro=edit), "no net class USB_HS")

    def test_usb_pattern_missing(self):
        def edit(pro):
            pro["net_settings"]["netclass_patterns"] = []
        self.assertFailsWith(run_check(edit_pro=edit), "netclass patterns []")

    def test_prepreg_thickness(self):
        self.assertFailsWith(
            run_check(edit_pcb=lambda t: t.replace("(thickness 0.2104)", "(thickness 0.2)", 1)),
            "stackup layer dielectric 1")

    def test_core_dk(self):
        self.assertFailsWith(
            run_check(edit_pcb=lambda t: t.replace("(epsilon_r 4.6)", "(epsilon_r 4.5)")),
            "stackup Dk 4.6 missing")

    def test_finish(self):
        self.assertFailsWith(
            run_check(edit_pcb=lambda t: t.replace('"HAL SnPb"', '"ENIG"')), "copper finish")

    def test_board_thickness(self):
        self.assertFailsWith(
            run_check(edit_pcb=lambda t: t.replace("\t\t(thickness 1.6)\n",
                                                   "\t\t(thickness 1.2)\n", 1)),
            "board thickness")

    def test_outline(self):
        self.assertFailsWith(
            run_check(edit_pcb=lambda t: t.replace("(end 150 122)", "(end 150 121)")),
            "outline 100.000 x 71.000 mm")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
