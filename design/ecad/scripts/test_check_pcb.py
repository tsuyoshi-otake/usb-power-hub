"""Negative tests for check_pcb.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_pcb.py has written the board:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_pcb.py

Each test copies design/ecad/source and design/ecad/libraries into a temporary directory
(the sym-lib-table finds the library at ../libraries), copies the placement document and the
capture list beside them, corrupts the copies and runs check_pcb.py on them in a new process.
A test that moves a part edits the board and the document alike, so that only the rule under
test breaks. The unchanged copy must pass; every corruption must fail and be named in the
output. The repository's files are never modified. Each run includes DRC and a netlist
export, about 3 s.

Not covered here: the J2-J3 pitch rule (moving J3 means moving all of channel B) and the
board-outline rule (make_project.py --check and test_make_project.py own the outline).
"""
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHECK = HERE / "check_pcb.py"
ECAD = HERE.parent
DOCS = {"doc": ECAD / "PLACEMENT_Rev0.4.md",
        "capture": ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.4_netlist.md"}
ORIGIN = (50.0, 122.0)

_spec = importlib.util.spec_from_file_location("sexpr", HERE / "sexpr.py")
sx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sx)


def run_check(board=None, **edit_text):
    """Copy, corrupt, check. Returns (exit status, output).

    board(tree): edit the board's parsed S-expression in place.
    doc / capture = edit(text): return the corrupted text.
    """
    with tempfile.TemporaryDirectory(prefix="pcbtest-") as tmp:
        t = pathlib.Path(tmp)
        src = t / "source"
        shutil.copytree(ECAD / "source", src)
        shutil.copytree(ECAD / "libraries", t / "libraries")
        args = []
        for key, path in DOCS.items():
            dst = t / path.name
            text = path.read_text(encoding="utf-8")
            if key in edit_text:
                new = edit_text[key](text)
                assert new != text, f"the {key} corruption changed nothing"
                text = new
            dst.write_text(text, encoding="utf-8", newline="\n")
            args += [f"--{key}", str(dst)]
        if board:
            p = src / "usb-power-hub.kicad_pcb"
            tree = sx.loads(p.read_text(encoding="utf-8"))
            before = sx.dumps(tree)
            board(tree)
            assert sx.dumps(tree) != before, "the board corruption changed nothing"
            p.write_text(sx.dumps(tree) + "\n", encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--src", str(src),
                            "--lib", str(t / "libraries"), *args],
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        return r.returncode, r.stdout + r.stderr


# ---- board edits ------------------------------------------------------------------------------
def prop(node, name):
    return next(p for p in sx.find(node, "property") if p[1] == name)


def footprint(tree, ref):
    return next(f for f in sx.find(tree, "footprint") if prop(f, "Reference")[2] == ref)


def move(tree, ref, x, y, rot=None):
    at = sx.first(footprint(tree, ref), "at")
    at[1:] = [round(ORIGIN[0] + x, 6), round(ORIGIN[1] - y, 6)] + \
             ([rot] if rot else [] if rot is not None else at[3:4])


# ---- document edits ---------------------------------------------------------------------------
def sub_once(pattern, repl):
    def edit(text):
        new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
        assert n == 1, pattern
        return new
    return edit


def row(ref, x=None, y=None, region=None):
    """Edit one row of the common table: | Ref | x | y | Rot | Region | Note |."""
    def edit(text):
        m = re.search(rf"^\| {ref} \|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", text, re.M)
        assert m, ref
        cells = [m.group(i).strip() for i in range(1, 5)]
        for i, v in ((0, x), (1, y), (3, region)):
            if v is not None:
                cells[i] = f"{v:g}" if isinstance(v, float) else v
        return text[:m.start()] + f"| {ref} | " + " | ".join(cells) + " |" + text[m.end():]
    return edit


class CheckTest(unittest.TestCase):
    def assertFailsWith(self, status_out, *needles):
        status, out = status_out
        self.assertEqual(status, 1, out)
        self.assertRegex(out, r"\d+ checks, [1-9]\d* failed: FAIL")
        for n in needles:
            self.assertIn(n, out)

    def test_unchanged_copy_passes(self):
        status, out = run_check()
        self.assertEqual(status, 0, out)
        self.assertRegex(out, r"\d+ checks, 0 failed: PASS")

    # ---- position and identity ----------------------------------------------------------------
    def test_board_part_moved(self):
        self.assertFailsWith(run_check(board=lambda t: move(t, "C12", 39.75, 53.4)),
                             "FAIL C12: at (39.7500, 53.4000), document (39.25, 53.4)")

    def test_document_position_changed(self):
        self.assertFailsWith(run_check(doc=row("C12", y=53.0)),
                             "FAIL C12: at (39.2500, 53.4000), document (39.25, 53.0)")

    def test_board_rotation_changed(self):
        self.assertFailsWith(run_check(board=lambda t: move(t, "C12", 39.25, 53.4, 90)),
                             "FAIL C12: rotation 90, document 180")

    def test_channel_b_moved_on_board(self):
        def edit(tree):
            at = sx.first(footprint(tree, "C201"), "at")
            at[1] = round(at[1] + 0.5, 6)
        self.assertFailsWith(run_check(board=edit), "FAIL C201: at (", "FAIL C101/C201: channel B")

    def test_channel_row_changed(self):
        edit = sub_once(r"^\| C101 \| C201 \| 5\.05 \|", "| C101 | C201 | 5.15 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL C101: at (", "FAIL C201: at (")

    def test_pad_net_changed(self):
        def edit(tree):
            pad = next(p for p in sx.find(footprint(tree, "C12"), "pad") if p[1] == "1")
            net = sx.first(pad, "net")
            gnd = next(sx.first(p, "net") for p in sx.find(footprint(tree, "C12"), "pad") if p[1] == "2")
            net[1:] = gnd[1:]
        self.assertFailsWith(run_check(board=edit), "FAIL C12.1: net GND, netlist V3V3", "FAIL DRC")

    def test_value_changed(self):
        def edit(tree):
            prop(footprint(tree, "C12"), "Value")[2] = "220n"
        self.assertFailsWith(run_check(board=edit), "FAIL C12: Value '220n', netlist '100n'")

    def test_field_made_visible(self):
        def edit(tree):
            p = prop(footprint(tree, "C12"), "LCSC")
            p[:] = [x for x in p if not (isinstance(x, list) and x and x[0] == "hide")]
        self.assertFailsWith(run_check(board=edit), "FAIL C12: field LCSC is visible")

    def test_fiducial_removed(self):
        def edit(tree):
            fp = footprint(tree, "FID3")
            tree[:] = [x for x in tree if x is not fp]
        self.assertFailsWith(run_check(board=edit), "FAIL fiducials: 2 fiducials",
                             "not on the board: ['FID3']")

    # ---- top side only ------------------------------------------------------------------------
    def test_pad_on_b_paste(self):
        def edit(tree):
            pad = next(p for p in sx.find(footprint(tree, "C12"), "pad") if p[1] == "1")
            layers = sx.first(pad, "layers")
            layers[1:] = ["B.Paste" if v == "F.Paste" else v for v in layers[1:]]
        self.assertFailsWith(run_check(board=edit), "FAIL C12.1: pad on B.Paste")

    def test_graphic_on_b_silk(self):
        def edit(tree):
            line = next(g for g in sx.find(footprint(tree, "C12"), "fp_line")
                        if sx.first(g, "layer")[1] == "F.SilkS")
            sx.first(line, "layer")[1] = "B.SilkS"
        self.assertFailsWith(run_check(board=edit), "FAIL C12: items on ['B.Silkscreen']")

    # ---- regions, keepouts, modules, mechanics ------------------------------------------------
    def test_part_under_module_not_on_list(self):
        doc = row("TP7", x=15.0, y=62.1, region="UNDER_PWR")
        self.assertFailsWith(run_check(board=lambda t: move(t, "TP7", 15.0, 62.1), doc=doc),
                             "FAIL TP7: under J4, but TestPoint_Pad_D1.0mm is not on the under list")

    def test_part_in_keepout(self):
        doc = row("TP4", x=40.0, y=17.0)
        self.assertFailsWith(run_check(board=lambda t: move(t, "TP4", 40.0, 17.0), doc=doc),
                             "FAIL TP4: courtyard enters keepout USB_CORRIDOR",
                             "FAIL TP4: courtyard (38.952, 15.954, 41.045, 18.046) leaves region REF")

    def test_analog_part_near_mau104(self):
        self.assertFailsWith(run_check(doc=row("C5", region="ADC")), "from the MAU104 U5",
                             "leaves region ADC")

    def test_module_off_back_edge(self):
        doc = row("J4", y=57.9)
        self.assertFailsWith(run_check(board=lambda t: move(t, "J4", 9.88, 57.9, 0), doc=doc),
                             "FAIL J4: module outline (7.5, 56.0, 27.5, 71.0) does not stand on the back edge")

    def test_hole_out_of_corner(self):
        doc = row("H2", x=50.0)
        self.assertFailsWith(run_check(board=lambda t: move(t, "H2", 50.0, 3.5, 0), doc=doc),
                             "FAIL H2: hole at (50.00, 3.50) is in no corner", "FAIL holes")

    def test_courtyards_overlap(self):
        doc = row("C13", x=39.25, y=53.6)
        self.assertFailsWith(run_check(board=lambda t: move(t, "C13", 39.25, 53.6), doc=doc),
                             "courtyards_overlap")

    # ---- the documents ------------------------------------------------------------------------
    def test_regions_overlap(self):
        edit = sub_once(r"^\| MCU \| block \| 28\.0 \|", "| MCU | block | 27.0 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL MCU/PWR4: regions overlap")

    def test_under_height_too_tall(self):
        edit = sub_once(r"^\| C_0805_2012Metric \| 1\.45 \|", "| C_0805_2012Metric | 1.65 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL C_0805_2012Metric: under-list height 1.65")

    def test_capture_pin_note_broken(self):
        edit = sub_once(r"\| at U1 pin 1 \(IOVDD\) \|", "| at U1 pin 30 (IOVDD) |")
        self.assertFailsWith(run_check(capture=edit), "FAIL C12 (capture list): note 'at U1 pin 30 (IOVDD)'")

    def test_capture_part_note_broken(self):
        edit = sub_once(r"J4 VBUS TVS, after F1", "J4 VBUS TVS, after U5")
        self.assertFailsWith(run_check(capture=edit), "FAIL D6 (capture list): note 'J4 VBUS TVS, after U5'")

    def test_document_note_broken(self):
        edit = sub_once(r"at U1 pin 1, clear of its pin-1 mark", "at U1 pin 22, clear of its pin-1 mark")
        self.assertFailsWith(run_check(doc=edit), "FAIL C12 (document): note 'at U1 pin 22")

    def test_channel_b_note_mapped(self):
        """A channel-table note names channel A's parts. Channel B is checked too (C203 fails
        here), and with the designators mapped: the unchanged copy, where C203's note reads
        "at U10 pin 7" and C203 sits 33.8 mm from U10, passes."""
        edit = sub_once(r"^(\| C103 \| C203 \|.*\| )at U10 pin 7 \|", r"\1at U12 pin 7 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL C103 (document): note 'at U12 pin 7'",
                             "FAIL C203 (document): note 'at U12 pin 7': ")


if __name__ == "__main__":
    unittest.main(verbosity=2)
