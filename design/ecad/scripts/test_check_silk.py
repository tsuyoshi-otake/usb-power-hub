"""Negative tests for check_silk.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_pcb.py has written the board:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_silk.py

Each test copies design/ecad/source into a temporary directory, copies the placement
document beside it, corrupts the copies and runs check_silk.py on them in a new process. A test that moves a label edits the board and the document's silk
table alike, so that only the rule under test breaks. The unchanged copy must pass; every
corruption must fail and be named in the output. The repository's files are never modified.
Each run takes about 2 s.
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
CHECK = HERE / "check_silk.py"
ECAD = HERE.parent
DOC = ECAD / "PLACEMENT_Rev0.5.md"
ORIGIN = (50.0, 122.0)
COLS = ("Label", "Text", "x", "y", "Rot", "Width", "Height", "Stroke", "Leader")

_spec = importlib.util.spec_from_file_location("sexpr", HERE / "sexpr.py")
sx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sx)


def run_check(board=None, doc=None):
    """Copy, corrupt, check. board(tree) edits the parsed board; doc(text) returns new text."""
    with tempfile.TemporaryDirectory(prefix="silktest-") as tmp:
        t = pathlib.Path(tmp)
        src = t / "source"
        shutil.copytree(ECAD / "source", src)
        text = DOC.read_text(encoding="utf-8")
        if doc:
            new = doc(text)
            assert new != text, "the document corruption changed nothing"
            text = new
        (t / DOC.name).write_text(text, encoding="utf-8", newline="\n")
        if board:
            p = src / "usb-power-hub.kicad_pcb"
            tree = sx.loads(p.read_text(encoding="utf-8"))
            before = sx.dumps(tree)
            board(tree)
            assert sx.dumps(tree) != before, "the board corruption changed nothing"
            p.write_text(sx.dumps(tree) + "\n", encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--src", str(src),
                            "--doc", str(t / DOC.name)],
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        return r.returncode, r.stdout + r.stderr


# ---- the silk table ---------------------------------------------------------------------------
def silk_span(text):
    return text.index("<!-- silk:begin -->"), text.index("<!-- silk:end -->")


def row_cells(text, label):
    a, b = silk_span(text)
    m = re.search(r"^\| " + re.escape(label) + r" \|.*$", text[a:b], re.M)
    assert m, f"no silk row {label}"
    return a + m.start(), a + m.end(), [c.strip() for c in m.group(0).strip()[1:-1].split("|")]


def set_row(label, **cols):
    """Rewrite cells of one silk row; cols are COLS names."""
    def edit(text):
        s, e, cells = row_cells(text, label)
        for k, v in cols.items():
            cells[COLS.index(k)] = str(v)
        return text[:s] + "| " + " | ".join(cells) + " |" + text[e:]
    return edit


def drop_row(label):
    def edit(text):
        s, e, _ = row_cells(text, label)
        return text[:s] + text[e + 1:]
    return edit


def dup_row(label):
    def edit(text):
        s, e, _ = row_cells(text, label)
        return text[:e + 1] + text[s:e + 1] + text[e + 1:]
    return edit


# ---- the board --------------------------------------------------------------------------------
def gr_text(tree, text):
    hits = [n for n in sx.find(tree, "gr_text") if n[1] == text]
    assert len(hits) == 1, f"{len(hits)} gr_text {text!r}"
    return hits[0]


def move_text(text, x, y, rot=None):
    def edit(tree):
        at = sx.first(gr_text(tree, text), "at")
        at[1:3] = [round(ORIGIN[0] + x, 6), round(ORIGIN[1] - y, 6)]
        if rot is not None:
            at[3:4] = [rot]
    return edit


def retext(old, new):
    def edit(tree):
        gr_text(tree, old)[1] = new
    return edit


def font(text, key, *vals):
    def edit(tree):
        f = sx.first(sx.first(sx.first(gr_text(tree, text), "effects"), "font"), key)
        f[1:] = list(vals)
    return edit


def silk_line(tree, x0, y0):
    """The board's own F.SilkS gr_line that starts at board point (x0, y0)."""
    want = [round(ORIGIN[0] + x0, 6), round(ORIGIN[1] - y0, 6)]
    for n in sx.find(tree, "gr_line"):
        st = sx.first(n, "start")
        if [round(float(v), 6) for v in st[1:3]] == want and sx.first(n, "layer")[1] == "F.SilkS":
            return n
    raise AssertionError(f"no silk line from ({x0}, {y0})")


def set_line(x0, y0, start=None, end=None):
    def edit(tree):
        n = silk_line(tree, x0, y0)
        for key, pt in (("start", start), ("end", end)):
            if pt:
                sx.first(n, key)[1:3] = [round(ORIGIN[0] + pt[0], 6), round(ORIGIN[1] - pt[1], 6)]
    return edit


def footprint(tree, ref):
    return next(f for f in sx.find(tree, "footprint")
                if next(p for p in sx.find(f, "property") if p[1] == "Reference")[2] == ref)


def fp_silk(fp):
    return [n for n in fp if isinstance(n, list) and n and n[0] in ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly")
            and sx.first(n, "layer")[1] == "F.SilkS"]


def both(*edits):
    def edit(tree):
        for e in edits:
            e(tree)
    return edit


class CheckSilkTest(unittest.TestCase):
    def assertFailsWith(self, result, *needles):
        status, out = result
        self.assertEqual(status, 1, out[-2000:])
        for n in needles:
            self.assertIn(n, out, out[-2000:])

    def test_unchanged_passes(self):
        status, out = run_check()
        self.assertEqual(status, 0, out[-2000:])
        self.assertIn("0 failed: PASS", out)

    # ---- 1 the table ---------------------------------------------------------------------------
    def test_thin_stroke(self):
        self.assertFailsWith(run_check(board=font("GND", "thickness", 0.15), doc=set_row("TP7", Stroke="0.15")),
                             "FAIL silk TP7: stroke 0.15 mm < 0.167 mm")

    def test_low_text(self):
        self.assertFailsWith(run_check(board=font("GND", "size", 1, 0.8), doc=set_row("TP7", Height="0.8")),
                             "FAIL silk TP7: height 0.8 mm < 1.0 mm")

    def test_narrow_text(self):
        self.assertFailsWith(run_check(board=font("GND", "size", 0.7, 1), doc=set_row("TP7", Width="0.7")),
                             "FAIL silk TP7: width 0.7 mm < 0.8 mm")

    def test_rotation_not_0_or_90(self):
        self.assertFailsWith(run_check(doc=set_row("TP7", Rot="45")), "FAIL silk TP7: rotation 45, want 0 or 90")

    def test_label_twice(self):
        self.assertFailsWith(run_check(doc=dup_row("TP7")), "FAIL silk TP7: labelled twice in the table")

    # ---- 2 board = table ----------------------------------------------------------------------
    def test_board_text_differs(self):
        self.assertFailsWith(run_check(board=retext("GND", "GNX")),
                             "FAIL silk TP7: 0 board texts match the table row 'GND'",
                             "FAIL board silk: text 'GNX'")

    def test_stray_board_line(self):
        def add(tree):
            line = sx.loads(sx.dumps(silk_line(tree, 6.7, 54.7)))
            sx.first(line, "start")[1:3] = [ORIGIN[0] + 50.0, ORIGIN[1] - 40.0]
            sx.first(line, "end")[1:3] = [ORIGIN[0] + 51.0, ORIGIN[1] - 40.0]
            tree.append(line)
        self.assertFailsWith(run_check(board=add), "FAIL board silk: shape at (50.0, 40.0) is not a table leader")

    def test_label_on_back(self):
        def edit(tree):
            sx.first(gr_text(tree, "GND"), "layer")[1] = "B.SilkS"
        self.assertFailsWith(run_check(board=edit), "FAIL board silk: 1 item(s) on B.SilkS")

    def test_designator_visible(self):
        def edit(tree):
            p = next(p for p in sx.find(footprint(tree, "U2"), "property") if p[1] == "Reference")
            p.remove(sx.first(p, "hide"))
        self.assertFailsWith(run_check(board=edit), "FAIL U2: text 'U2' is visible on the silkscreen")

    # ---- 3 content ----------------------------------------------------------------------------
    def test_missing_label(self):
        def edit(tree):
            tree.remove(gr_text(tree, "V_J4"))
        self.assertFailsWith(run_check(board=edit, doc=drop_row("TP9")), "FAIL TP9: no silk label")

    def test_wrong_net_name(self):
        self.assertFailsWith(run_check(board=retext("GND", "AGND"), doc=set_row("TP7", Text="AGND")),
                             "FAIL silk TP7: text 'AGND', its pad's net 'GND'")

    def test_port_label_wrong(self):
        self.assertFailsWith(run_check(board=retext("OUT A", "OUT 1"), doc=set_row("J2", Text="OUT 1")),
                             "FAIL silk J2: port label 'OUT A' missing")

    def test_port_label_far(self):
        """OUT A moved 2.0 mm west: its ink ends about 2.4 mm from J2's courtyard."""
        self.assertFailsWith(run_check(board=move_text("OUT A", 7.6, 3.0), doc=set_row("J2", x="7.6")),
                             "FAIL silk J2: port label 2.")

    def test_port_label_on_the_receptacle(self):
        self.assertFailsWith(run_check(board=move_text("OUT A", 17.5, 3.0), doc=set_row("J2", x="17.5")),
                             "FAIL silk J2: port label 0.00 mm from J2's courtyard, want outside and <= 1.5 mm")

    def test_title_mismatch(self):
        self.assertFailsWith(run_check(board=retext("Rev0.5", "Rev0.6"), doc=set_row("revision", Text="Rev0.6")),
                             "FAIL silk revision: want the title block's 'Rev0.5'")

    # ---- 4 association ------------------------------------------------------------------------
    def test_label_far_without_leader(self):
        self.assertFailsWith(run_check(board=move_text("V_J4", 23.8, 47.5), doc=set_row("TP9", y="47.5")),
                             "FAIL silk TP9: not within 1.5 mm of TP9's pad and has no leader")

    def test_label_reads_as_neighbour(self):
        """GND moved beside TP8: still within 1.5 mm of TP7, but nearer TP8."""
        self.assertFailsWith(run_check(board=move_text("GND", 10.6, 57.2), doc=set_row("TP7", x="10.6", y="57.2")),
                             "FAIL silk TP7: centre", "reads as TP8's")

    def test_leader_to_wrong_pad(self):
        self.assertFailsWith(run_check(board=set_line(10.3, 54.7, end=(8.05, 55.0)),
                                       doc=set_row("TP8", Leader="6.7,54.7 10.3,54.7 8.05,55.0")),
                             "FAIL silk TP8: leader ends", "from TP7.1, nearer than TP8")

    def test_leader_detached(self):
        self.assertFailsWith(run_check(board=set_line(6.7, 54.7, start=(5.5, 53.9)),
                                       doc=set_row("TP8", Leader="5.5,53.9 10.3,54.7 10.3,55.0")),
                             "FAIL silk TP8: leader starts at (5.5, 53.9), more than 0.3 mm from its label")

    def test_leader_touches_its_label(self):
        """The defect the first build had: TP8's leader started inside VBUS_IN's last glyph."""
        self.assertFailsWith(run_check(board=set_line(6.7, 54.7, start=(6.518, 54.7)),
                                       doc=set_row("TP8", Leader="6.518,54.7 10.3,54.7 10.3,55.0")),
                             "FAIL silk TP8: leader segment from", "touches its label's glyphs")

    # ---- 5 clearance --------------------------------------------------------------------------
    def test_label_on_pad(self):
        self.assertFailsWith(run_check(board=move_text("V_J4", 23.8, 51.5), doc=set_row("TP9", y="51.5")),
                             "FAIL silk TP9 label: < 0.15 mm from TP9.1's mask opening")

    def test_label_off_edge(self):
        self.assertFailsWith(run_check(board=move_text("VSUP_A", 0.7, 36.35), doc=set_row("TP105", x="0.7")),
                             "FAIL silk TP105 label: ink", "is not 0.5 mm inside the board")

    def test_label_in_courtyard(self):
        self.assertFailsWith(run_check(board=move_text("5V IN", 18.8, 53.3), doc=set_row("J4", x="18.8", y="53.3")),
                             "FAIL silk J4 label: enters D6's courtyard")

    def test_label_touches_label(self):
        self.assertFailsWith(run_check(board=move_text("GND", 5.55, 56.2), doc=set_row("TP7", y="56.2")),
                             "FAIL silk TP7 label: < 0.1 mm from silk TP8 label")

    # ---- 6 footprint silkscreen ---------------------------------------------------------------
    def test_polar_part_without_silk(self):
        def edit(tree):
            fp = footprint(tree, "U2")
            for n in fp_silk(fp):
                fp.remove(n)
        self.assertFailsWith(run_check(board=edit), "FAIL U2: a polar part with no silkscreen")

    def test_footprint_silk_on_other_pad(self):
        """F1 (pin 1 at (5, 52.55), rotation 0): one of its silk lines moved over TP7's pad."""
        def edit(tree):
            n = fp_silk(footprint(tree, "F1"))[0]
            sx.first(n, "start")[1:3] = [2.8, -3.25]
            sx.first(n, "end")[1:3] = [3.3, -3.25]
        self.assertFailsWith(run_check(board=edit), "FAIL F1: silkscreen < 0.15 mm from TP7.1's mask opening")

    def test_footprint_silk_thin(self):
        def edit(tree):
            n = fp_silk(footprint(tree, "F1"))[0]
            sx.first(sx.first(n, "stroke"), "width")[1] = 0.12
        self.assertFailsWith(run_check(board=edit), "FAIL F1: silkscreen stroke 0.12 mm < 0.15 mm")


if __name__ == "__main__":
    unittest.main(verbosity=2)
