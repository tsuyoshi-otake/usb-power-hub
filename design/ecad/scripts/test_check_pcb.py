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

Not covered here: the board-outline rule (make_project.py --check and test_make_project.py own
the outline). The J2-J3 pitch rule is covered by test_receptacles_too_close, which moves J3
alone, so that the checker names other lines as well as the pitch. The mirror rule (D39) has
no test for a button or LED row removed from its table: the checker does not see that (its
own "not checked" list says so).
The board in design/ecad/source must be the placed one: make_pcb.py writes it.
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
DOCS = {"doc": ECAD / "PLACEMENT_Rev0.6.md",
        "capture": ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.6_netlist.md"}
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
        self.assertFailsWith(run_check(board=lambda t: move(t, "C12", 39.75, 52.6)),
                             "FAIL C12: at (39.7500, 52.6000), document (39.25, 52.6)")

    def test_document_position_changed(self):
        self.assertFailsWith(run_check(doc=row("C12", y=53.0)),
                             "FAIL C12: at (39.2500, 52.6000), document (39.25, 53.0)")

    def test_board_rotation_changed(self):
        self.assertFailsWith(run_check(board=lambda t: move(t, "C12", 39.25, 52.6, 90)),
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
        # C1, an 0805: the 0402s carry no silkscreen since P5 (library.json silk_drop)
        def edit(tree):
            line = next(g for g in sx.find(footprint(tree, "C1"), "fp_line")
                        if sx.first(g, "layer")[1] == "F.SilkS")
            sx.first(line, "layer")[1] = "B.SilkS"
        self.assertFailsWith(run_check(board=edit), "FAIL C1: items on ['B.Silkscreen']")

    # ---- regions, keepouts, receptacles, mechanics --------------------------------------------
    def test_part_in_keepout(self):
        doc = row("TP4", x=40.0, y=17.0)
        self.assertFailsWith(run_check(board=lambda t: move(t, "TP4", 40.0, 17.0), doc=doc),
                             "FAIL TP4: courtyard enters keepout USB_CORRIDOR",
                             "FAIL TP4: courtyard (39.002, 16.004, 40.995, 17.996) leaves region REF")

    def test_part_in_lane_keepout(self):
        """The lane keepouts lie inside a port block; a part's courtyard may not enter one.
        USB_LANE_A is widened to x 20.1, over C116 (courtyard from x 19.7)."""
        edit = sub_once(r"^\| USB_LANE_A \| 16\.1 \| 8\.5 \| 1\.8 \|", "| USB_LANE_A | 16.1 | 8.5 | 4 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL C116: courtyard enters keepout USB_LANE_A")

    def test_keepout_straddles_a_region(self):
        edit = sub_once(r"^\| USB_UP_LANE \| 82\.1 \| 56\.5 \|", "| USB_UP_LANE | 82.1 | 55 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL USB_UP_LANE: keepout lies partly in region(s)")

    def test_analog_part_near_mau104(self):
        self.assertFailsWith(run_check(doc=row("C5", region="ADC")), "from the MAU104 U5",
                             "leaves region ADC")

    def test_receptacle_off_its_overhang(self):
        """J4 moved 1.4 mm south: its front face stands 0.34 mm past the back edge, not 1.06."""
        doc = row("J4", y=67.985)
        self.assertFailsWith(run_check(board=lambda t: move(t, "J4", 17.5, 67.985, 180), doc=doc),
                             "FAIL J4: front face at y = 71.660, opening +1 along y; want the opening "
                             "toward the back edge (+1) and the face at y = 73.06")

    def test_receptacle_past_the_edge(self):
        """J2 and J3 moved 1.0 mm south: the courtyard passes the front edge by 2.3 mm, more
        than the 1.31 mm a receptacle may (the overhang plus the library's courtyard margin).
        Both move, so that the pair stays mirrored."""
        def edit(text):
            return row("J3", y=1.615)(row("J2", y=1.615)(text))

        def board(tree):
            move(tree, "J2", 17.5, 1.615)
            move(tree, "J3", 82.5, 1.615)
        self.assertFailsWith(run_check(board=board, doc=edit),
                             "passes the edge it stands on by more than 1.31 mm",
                             "FAIL J2: front face at y = -2.060, opening -1 along y")

    def test_receptacles_too_close(self):
        """J3 moved 48.0 mm toward J2: the pitch of 17.00 mm is under REQ-MECH-02's 18 mm, so two
        plugs would not fit side by side. Only J3 moves (OUT B's own parts stay behind), so
        the checker names other lines too, the mirror rule's among them; the pitch line is the
        one under test."""
        self.assertFailsWith(run_check(board=lambda t: move(t, "J3", 34.5, 2.615)),
                             "FAIL J2/J3: pitch 17.00 mm < 18.0 mm", "FAIL J2|J3: (17.5000, 2.6150)")

    # ---- the mirror table (D39) ---------------------------------------------------------------
    def test_mirror_pair_moved_in_x(self):
        """SW2 0.5 mm east, on the board and in the document: only the mirror rule knows that
        it belongs opposite SW1."""
        doc = row("SW2", x=69.0)
        self.assertFailsWith(run_check(board=lambda t: move(t, "SW2", 69.0, 4.5), doc=doc),
                             "FAIL SW1|SW2: (31.5000, 4.5000) rotation 90 and (69.0000, 4.5000) rotation 90 "
                             "are not mirrored about x = 50: want x_a + x_b = 100")

    def test_mirror_pair_moved_in_y(self):
        doc = row("D12", y=10.8)
        self.assertFailsWith(run_check(board=lambda t: move(t, "D12", 70.25, 10.8), doc=doc),
                             "FAIL D10|D12: (29.7500, 10.5000) rotation 0 and (70.2500, 10.8000) rotation 180")

    def test_mirror_pair_turned(self):
        """D12 at 90: neither D10's rotation (0) nor its mirror image (180)."""
        edit = sub_once(r"^\| D12 \| 70\.25 \| 10\.5 \| 180 \|", "| D12 | 70.25 | 10.5 | 90 |")
        self.assertFailsWith(run_check(board=lambda t: move(t, "D12", 70.25, 10.5, 90), doc=edit),
                             "FAIL D10|D12: (29.7500, 10.5000) rotation 0 and (70.2500, 10.5000) rotation 90")

    def test_mirror_axis_changed(self):
        edit = sub_once(r"<!-- mirror:begin axis=50\.0 -->", "<!-- mirror:begin axis=49.0 -->")
        self.assertFailsWith(run_check(doc=edit), "FAIL J2|J3: ", "are not mirrored about x = 49: want x_a + x_b = 98",
                             "FAIL J4|J1: ", "FAIL SW1|SW2: ")

    def test_mirror_table_names_a_missing_part(self):
        edit = sub_once(r"^\| SW1 \| SW2 \|", "| SW1 | SW9 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL SW1|SW9: the mirror table names a part that is not on "
                             "the board, or one part twice")

    def test_mirror_table_without_a_receptacle_pair(self):
        """The front pair's row removed: the pair would no longer be held, so the table itself
        fails."""
        edit = sub_once(r"^\| J2 \| J3 \| OUT A and OUT B on the front edge[^\n]*\n", "")
        self.assertFailsWith(run_check(doc=edit), "FAIL mirror table: the receptacle pairs J2|J3 and J1|J4 are "
                             "not both in the mirror table (D39)")

    def test_receptacle_turned_around(self):
        """J4 at rotation 0 opens toward the board's interior, not the back edge."""
        edit = sub_once(r"^\| J4 \| 17\.5 \| 69\.385 \| 180 \|", "| J4 | 17.5 | 69.385 | 0 |")
        self.assertFailsWith(run_check(board=lambda t: move(t, "J4", 17.5, 69.385, 0), doc=edit),
                             "FAIL J4: front face at y = 65.710, opening -1 along y")

    def test_hole_out_of_corner(self):
        doc = row("H2", x=50.0)
        self.assertFailsWith(run_check(board=lambda t: move(t, "H2", 50.0, 3.5, 0), doc=doc),
                             "FAIL H2: hole at (50.00, 3.50) is in no corner", "FAIL holes")

    def test_courtyards_overlap(self):
        doc = row("C13", x=39.25, y=52.8)
        self.assertFailsWith(run_check(board=lambda t: move(t, "C13", 39.25, 52.8), doc=doc),
                             "courtyards_overlap")

    # ---- the documents ------------------------------------------------------------------------
    def test_regions_overlap(self):
        edit = sub_once(r"^\| MCU \| block \| 28\.0 \|", "| MCU | block | 27.0 |")
        self.assertFailsWith(run_check(doc=edit), "FAIL MCU/PWR4: regions overlap")

    def test_region_kind_of_the_module_design(self):
        """Rev0.4's `module` and `under` kinds are gone with the modules."""
        edit = sub_once(r"^\| PORT_A \| block \|", "| PORT_A | module |")
        self.assertFailsWith(run_check(doc=edit), "FAIL PORT_A: kind 'module' is not one of ['block', 'mark']")

    def test_document_note_names_a_receptacle_pad(self):
        """"at J2 pad B4" is a pad of a receptacle, named with a letter. Read as "at J2" it
        would pass on the courtyards alone, so a wrong pad name must fail on its own."""
        edit = sub_once(r"port capacitor, at J2 pad B4", "port capacitor, at J2 pad A5")
        self.assertFailsWith(run_check(doc=edit), "FAIL C116 (document): note 'port capacitor, at J2 pad A5'")

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
