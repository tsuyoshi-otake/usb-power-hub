"""Negative tests for make_project.py's check (CLAUDE.md 8: a checker never observed failing
is not evidence).

Run with KiCad's Python from the repository root, after make_project.py has written
design/ecad/source:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_make_project.py

Each test copies the three source files into a temporary directory, corrupts one aspect
and runs `make_project.py --check DIR` in a new process, because pcbnew caches a loaded
project within a process. The unchanged copy must pass; every corruption must fail and be
named in the output. The source files themselves are never modified.

PegRuleTest does not check the files: it asks KiCad's DRC what the footprint-scoped peg rule
does (D37). It places the receptacle from design/ecad/libraries (make_libraries.py must have
run) on a scratch copy of the project, with a track of another net near the left peg hole.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = HERE / "make_project.py"
SOURCE = HERE.parents[0] / "source"
PRETTY = HERE.parents[0] / "libraries" / "usb-power-hub.pretty"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
RECEPTACLE = "USB_C_Receptacle_SHOUHAN_TYPE-C-16PIN-2MD-073"
PEG_RULE = re.compile(r'\(rule "JLCPCB NPTH to copper[^"]*"\n.*?memberOfFootprint\([^)]*\)"\)\)\n', re.S)
NAME = "usb-power-hub"
EXTS = (".kicad_pcb", ".kicad_pro", ".kicad_dru")


def run_check(edit_pcb=None, edit_pro=None, edit_dru=None):
    """Copy, corrupt, check. Returns (exit status, output).

    edit_dru(path): corrupt or delete the copied custom-rule file."""
    with tempfile.TemporaryDirectory() as tmp:
        d = pathlib.Path(tmp)
        for ext in EXTS:
            shutil.copyfile(SOURCE / f"{NAME}{ext}", d / f"{NAME}{ext}")
        if edit_dru:
            edit_dru(d / f"{NAME}.kicad_dru")
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

    def test_via_drill_back_to_025(self):
        def edit(pro):
            pro["board"]["design_settings"]["rules"]["min_through_hole_diameter"] = 0.25
            classes(pro)["Default"]["via_drill"] = 0.25
        self.assertFailsWith(run_check(edit_pro=edit), "m_MinThroughDrill", "Default.via_drill")

    def test_hole_clearance_rule(self):
        def edit(pro):
            pro["board"]["design_settings"]["rules"]["min_hole_clearance"] = 0.20
        self.assertFailsWith(run_check(edit_pro=edit), "m_HoleClearance", "rule min_hole_clearance")

    def test_hole_to_hole_rule(self):
        def edit(pro):
            pro["board"]["design_settings"]["rules"]["min_hole_to_hole"] = 0.15
        self.assertFailsWith(run_check(edit_pro=edit), "m_HoleToHoleMin")

    def test_pth_rules_missing(self):
        self.assertFailsWith(run_check(edit_dru=lambda p: p.unlink()), "is not the rule set HOLE_RULES")

    def test_pth_rule_loosened(self):
        def edit(p):
            p.write_text(p.read_text(encoding="utf-8").replace("(min 0.28mm)", "(min 0.20mm)"),
                         encoding="utf-8", newline="\n")
        self.assertFailsWith(run_check(edit_dru=edit), "is not the rule set HOLE_RULES")

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


PEG_X, PEG_Y, PEG_R = -2.89, -2.605, 0.325        # the left peg hole, in the footprint's frame
AT = (50.0, 50.0)                                 # where the scratch board puts the receptacle


def peg_drc(track_gap, keep_rule=True):
    """DRC violations of hole clearance on a scratch board: the receptacle with a 0.2 mm track
    of another net `track_gap` mm from the left peg hole's edge. Returns their descriptions."""
    import pcbnew
    with tempfile.TemporaryDirectory(prefix="pegrule-") as tmp:
        d = pathlib.Path(tmp)
        for ext in (".kicad_pro", ".kicad_pcb"):
            shutil.copyfile(SOURCE / f"{NAME}{ext}", d / f"t{ext}")
        dru = (SOURCE / f"{NAME}.kicad_dru").read_text(encoding="utf-8")
        if not keep_rule:
            dru, n = PEG_RULE.subn("", dru)
            assert n == 1, "the peg rule is not in the rules file"
        (d / "t.kicad_dru").write_text(dru, encoding="utf-8", newline="\n")
        board = pcbnew.LoadBoard(str(d / "t.kicad_pcb"))
        for fp in list(board.GetFootprints()):
            board.Remove(fp)
        fp = pcbnew.FootprintLoad(str(PRETTY), RECEPTACLE)
        assert fp is not None, "run make_libraries.py first"
        fp.SetFPID(pcbnew.LIB_ID(NAME, RECEPTACLE))
        fp.SetReference("J9")
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(AT[0]), pcbnew.FromMM(AT[1])))
        board.Add(fp)
        for pad in fp.Pads():
            if pad.GetNumber():
                net = pcbnew.NETINFO_ITEM(board, f"N_{pad.GetNumber()}")
                board.Add(net)
                pad.SetNet(net)
        other = pcbnew.NETINFO_ITEM(board, "OTHER")
        board.Add(other)
        x = AT[0] + PEG_X - PEG_R - track_gap - 0.1           # the track's right edge is track_gap away
        for y0, y1 in ((PEG_Y - 0.6, PEG_Y + 0.6),):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(AT[1] + y0)))
            t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(AT[1] + y1)))
            t.SetWidth(pcbnew.FromMM(0.2))
            t.SetLayer(pcbnew.B_Cu)
            t.SetNet(other)
            board.Add(t)
        pcbnew.SaveBoard(str(d / "t.kicad_pcb"), board)
        subprocess.run([str(CLI), "pcb", "drc", "--format", "json", "--severity-all", "--output",
                        str(d / "drc.json"), str(d / "t.kicad_pcb")], capture_output=True, cwd=d, timeout=120)
        data = json.loads((d / "drc.json").read_text(encoding="utf-8"))
        return [v["description"] + " " + " ".join(i.get("description", "") for i in v.get("items", []))
                for v in data["violations"] if v["type"] == "hole_clearance"]


class PegRuleTest(unittest.TestCase):
    """The peg rule gives the receptacle's unplated pegs JLCPCB's 0.20 mm to other copper, and
    only them: with the rule a track 0.22 mm from a peg hole passes and one 0.15 mm away fails
    by the rule's own figure; without it the board's 0.25 mm fails the 0.22 mm track."""

    def test_track_022_from_peg_passes(self):
        self.assertEqual(peg_drc(0.22), [])

    def test_track_015_from_peg_fails(self):
        found = peg_drc(0.15)
        self.assertEqual(len(found), 1, found)
        self.assertIn("0.2000", found[0])
        self.assertIn("USB-C receptacle pegs", found[0])

    def test_board_minimum_without_the_rule(self):
        found = peg_drc(0.22, keep_rule=False)
        self.assertEqual(len(found), 1, found)
        self.assertIn("0.2500", found[0])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main()
