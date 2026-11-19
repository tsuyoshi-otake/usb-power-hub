"""Negative tests for check_lid.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's own Python from the repository root:

    "<KiCad 9.0>/bin/python.exe" -I -B design/mechanical/scripts/test_check_lid.py

The lid is built once from the repository's document and interface into a temporary
directory, with its candidate set. Each test then makes one fault and runs check_lid.py on
it in a new process; the fault must give a FAIL line of the check it is aimed at, with the
words that name it. A fault is made in one of four ways:
- built: the lid is built from a changed document or interface and checked against the same
  one (a table that breaks a rule of the checker);
- drifted: the lid is built from a changed document or interface, the board's record of its
  inputs is rewritten to the repository's, and it is checked against the repository's (a
  board that is not what its inputs say: L01 passes, so the measuring check stands alone);
- edited: the board file's text is changed after the build;
- set: a file of the candidate set is changed, and SHA256SUMS.txt is written anew.
The unchanged lid and its set must pass, and so must a lid whose interface moves a port and
a hole (nothing is typed twice). The repository's files are never modified. KiCad's DRC (L11)
runs only in the tests that name it; the whole run takes about 2.5 min.
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
MAKE = HERE / "make_lid.py"
CHECK = HERE / "check_lid.py"
OUTPUTS = HERE / "make_lid_outputs.py"


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load("lid_spec")
DOC_TEXT = spec.DOC.read_bytes().decode("utf-8")
INT_TEXT = spec.INTERFACE.read_bytes().decode("ascii")
PCB = f"{spec.NICK}.kicad_pcb"
ZIP = f"{spec.PREFIX}_Gerber.zip"
STATE = {"n": 0}


def run(script, *args):
    r = subprocess.run([sys.executable, "-I", "-B", str(script), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    return r.returncode, r.stdout + r.stderr


def setUpModule():
    STATE["tmp"] = pathlib.Path(tempfile.mkdtemp(prefix="lidtest-"))
    STATE["ref"] = STATE["tmp"] / "ref"
    rc, text = run(MAKE, "--no-check", "--out", STATE["ref"])
    assert rc == 0, f"the reference build failed:\n{text}"
    STATE["out"] = STATE["tmp"] / "out"
    rc, text = run(OUTPUTS, "--no-check", "--src", STATE["ref"], "--out", STATE["out"])
    assert rc == 0, f"the reference set failed:\n{text}"


def tearDownModule():
    shutil.rmtree(STATE["tmp"], ignore_errors=True)


def fresh():
    STATE["n"] += 1
    d = STATE["tmp"] / f"v{STATE['n']:03d}"
    d.mkdir()
    return d


# ---- changing the document and the interface ----------------------------------------------------
def param(name, value):
    def change(text):
        out, n = re.subn(rf"(\| `{name}` \| )[-0-9.]+( \|)", lambda m: f"{m.group(1)}{value}{m.group(2)}", text)
        assert n == 1, f"parameter {name} not found once"
        return out
    return change


def _legend(text, edit):
    lines = text.split("\n")
    a = next(i for i, line in enumerate(lines) if "lid-legend:begin" in line)
    z = next(i for i, line in enumerate(lines) if "lid-legend:end" in line)
    lines[a + 1:z] = edit(lines[a + 1:z])
    return "\n".join(lines)


def row(label, **cells):
    """Change cells of the legend row `label`; the keys are the column names in lower case."""
    cols = [c.lower() for c in spec.LEGEND_COLUMNS]

    def edit(rows):
        hits = [i for i, line in enumerate(rows) if line.startswith(f"| {label} |")]
        assert len(hits) == 1, f"legend row {label} not found once"
        vals = [c.strip() for c in rows[hits[0]].strip().strip("|").split("|")]
        for key, value in cells.items():
            vals[cols.index(key)] = str(value)
        rows[hits[0]] = "| " + " | ".join(vals) + " |"
        return rows
    return lambda text: _legend(text, edit)


def no_row(label):
    def edit(rows):
        keep = [line for line in rows if not line.startswith(f"| {label} |")]
        assert len(keep) == len(rows) - 1, f"legend row {label} not found once"
        return keep
    return lambda text: _legend(text, edit)


def new_row(*vals):
    return lambda text: _legend(text, lambda rows: rows + ["| " + " | ".join(map(str, vals)) + " |"])


def both(*changes):
    def change(text):
        for c in changes:
            text = c(text)
        return text
    return change


def interface(edit):
    def change(text):
        data = json.loads(text)
        edit(data)
        return json.dumps(data, indent=1) + "\n"
    return change


def hole(data, ref):
    return next(h for h in data["holes"] if h["ref"] == ref)


def port(data, ref):
    return next(p for p in data["ports"] if p["ref"] == ref)


# ---- changing the board file's text -------------------------------------------------------------
def swap(old, new, count=1):
    def edit(text):
        assert old in text, f"{old!r} is not in the board file"
        return text.replace(old, new, count)
    return edit


def resub(pattern, repl):
    def edit(text):
        out, n = re.subn(pattern, repl, text, count=1)
        assert n == 1, f"{pattern!r} does not match the board file"
        return out
    return edit


def append(snippet):
    """Add one item at the end of the board file, before its closing parenthesis."""
    def edit(text):
        body = text.rstrip()
        assert body.endswith(")")
        return body[:-1] + snippet.strip("\n") + "\n)\n"
    return edit


def cut(marker, which=0):
    """Remove the parenthesised block that starts at the `which`-th occurrence of `marker`."""
    def edit(text):
        at = -1
        for _ in range(which + 1):
            at = text.index(marker, at + 1)
        depth, i, quoted = 0, at, False
        while True:
            ch = text[i]
            if quoted:
                if ch == "\\":
                    i += 1
                elif ch == '"':
                    quoted = False
            elif ch == '"':
                quoted = True
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        start = text.rfind("\n", 0, at) + 1
        end = i + 1
        if text[end:end + 1] == "\n":
            end += 1
        return text[:start] + text[end:]
    return edit


UUID = "00000000-0000-4000-8000-00000000000"
TRACK = f"""
	(segment
		(start 100 100)
		(end 110 100)
		(width 0.2)
		(layer "F.Cu")
		(net 0)
		(uuid "{UUID}1")
	)
"""


def line_on(layer):
    return f"""
	(gr_line
		(start 100 100)
		(end 110 100)
		(stroke
			(width 0.2)
			(type default)
		)
		(layer "{layer}")
		(uuid "{UUID}2")
	)
"""


MASK_RECT = f"""
	(gr_rect
		(start 100 98)
		(end 110 102)
		(stroke
			(width 0)
			(type default)
		)
		(fill yes)
		(layer "F.Mask")
		(uuid "{UUID}3")
	)
"""
TEXT = f"""
	(gr_text "X"
		(at 100 100 0)
		(layer "F.SilkS")
		(uuid "{UUID}4")
		(effects
			(font
				(size 1.5 1.5)
				(thickness 0.25)
			)
		)
	)
"""


def variant(doc=None, iface=None, check="built", check_doc=None, check_iface=None, edit=None, restamp=False, drc=False):
    """Build a lid (or copy the reference one when nothing is changed), optionally edit the
    board file, and check it. check="built": against what it was built from; "reference":
    against the repository's document and interface, changed by check_doc/check_iface if given.
    restamp: write the checked inputs' digest into the board first, so that L01 passes."""
    d = fresh()
    bdoc, bint = d / "LID.md", d / "LidInterface.json"
    bdoc.write_bytes((doc(DOC_TEXT) if doc else DOC_TEXT).encode("utf-8"))
    bint.write_bytes((iface(INT_TEXT) if iface else INT_TEXT).encode("ascii"))
    src = d / "lid"
    if doc or iface:
        rc, text = run(MAKE, "--no-check", "--doc", bdoc, "--interface", bint, "--out", src)
        assert rc == 0, f"the build failed:\n{text}"
    else:
        shutil.copytree(STATE["ref"], src)
    cdoc, cint = (bdoc, bint) if check == "built" else (spec.DOC, spec.INTERFACE)
    if check_doc:
        cdoc = d / "LID_check.md"
        cdoc.write_bytes(check_doc(DOC_TEXT).encode("utf-8"))
    if check_iface:
        cint = d / "LidInterface_check.json"
        cint.write_bytes(check_iface(INT_TEXT).encode("ascii"))
    if restamp or edit:
        pcb = src / PCB
        text = pcb.read_bytes().decode("utf-8")
        if restamp:
            digest = spec.inputs_digest(*spec.load_doc(cdoc), cint)
            text, n = re.subn(re.escape(spec.DIGEST_TAG) + "[0-9a-f]{64}", spec.DIGEST_TAG + digest, text)
            assert n == 1, "the board carries no inputs digest"
        if edit:
            new = edit(text)
            assert new != text, "the edit changed nothing"
            text = new
        pcb.write_bytes(text.encode("utf-8"))
    args = ["--doc", cdoc, "--interface", cint, "--src", src]
    return run(CHECK, *args, *([] if drc else ["--no-drc"]))


def restamp_set(out):
    sums = "".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
                   for p in sorted(out.iterdir()) if p.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_bytes(sums.encode("utf-8"))


def set_variant(edit, restamp=True, src_edit=None):
    """Copy the reference set, change it, and check it with the reference board."""
    d = fresh()
    out = d / "out"
    shutil.copytree(STATE["out"], out)
    src = STATE["ref"]
    if src_edit:
        src = d / "lid"
        shutil.copytree(STATE["ref"], src)
        src_edit(src)
    edit(out)
    if restamp:
        restamp_set(out)
    return run(CHECK, "--src", src, "--outputs", out, "--no-drc")


def member(suffix, change):
    """Change one member of the Gerber zip: change(bytes) -> bytes, or None to drop it."""
    def edit(out):
        with zipfile.ZipFile(out / ZIP) as z:
            members = {n: z.read(n) for n in z.namelist()}
        name = f"{spec.PREFIX}_{suffix}"
        new = change(members[name])
        assert new != members[name], "the edit changed nothing"
        if new is None:
            del members[name]
        else:
            members[name] = new
        with zipfile.ZipFile(out / ZIP, "w", zipfile.ZIP_DEFLATED) as z:
            for n, data in members.items():
                z.writestr(n, data)
    return edit


def bytes_swap(old, new):
    def change(data):
        assert old in data, f"{old!r} is not in the file"
        return data.replace(old, new, 1)
    return change


class LidTest(unittest.TestCase):
    def fails(self, result, cid, *phrases, alone=False, with_plot=False):
        """The check cid fails with these words. alone: no other check fails. with_plot: none but
        L16 does, which fails for every changed member of the Gerber zip, whatever the change."""
        rc, text = result
        fails = [line for line in text.splitlines() if line.startswith("FAIL ")]
        mine = [line for line in fails if line.startswith(f"FAIL {cid} ")]
        self.assertEqual(rc, 1, text)
        self.assertTrue(mine, f"no FAIL {cid} line:\n{text}")
        for p in phrases:
            self.assertTrue(any(p in line for line in mine), f"no FAIL {cid} line says {p!r}:\n" + "\n".join(fails))
        if alone:
            self.assertEqual(fails, mine, "other checks failed too:\n" + "\n".join(fails))
        if with_plot:
            plot = [line for line in fails if line.startswith("FAIL L16 ")]
            self.assertEqual(len(plot), 1, "L16 does not report the changed member:\n" + "\n".join(fails))
            self.assertEqual(sorted(fails), sorted(mine + plot), "other checks failed too:\n" + "\n".join(fails))

    def passes(self, result, *ids):
        rc, text = result
        self.assertEqual(rc, 0, text)
        self.assertNotIn("FAIL", text)
        self.assertRegex(text, r"lid check: \d+ checks, 0 failed")
        for cid in ids:
            self.assertIn(f"PASS {cid} ", text)


class Unchanged(LidTest):
    def test_reference_lid_passes_every_board_check(self):
        self.passes(variant(drc=True), *(f"L{i:02d}" for i in range(1, 12)))

    def test_reference_set_passes_every_set_check(self):
        self.passes(set_variant(lambda out: None, restamp=False), "L12", "L13", "L14", "L15", "L16")

    def test_a_moved_port_and_a_moved_hole_take_their_legend_along(self):
        def move(data):
            port(data, "J1")["x"] = 60.0
            hole(data, "SW3")["x"] += 10.0
            hole(data, "SW2")["x"] += 6.0
        self.passes(variant(iface=interface(move), drc=True), "L03", "L08", "L09", "L10", "L11")


class L01Identity(LidTest):
    def test_a_table_value_changed_after_the_build(self):
        self.fails(variant(check="reference", check_doc=param("zone_min", 0.3)), "L01", "rebuild with make_lid.py", alone=True)

    def test_the_interface_changed_after_the_build(self):
        def edit(data):
            data["underside_above_board"] = 18.0
        self.fails(variant(check="reference", check_iface=interface(edit)), "L01", "rebuild with make_lid.py", alone=True)

    def test_another_revision_in_the_title_block(self):
        self.fails(variant(edit=swap('(rev "Rev0.1")', '(rev "Rev0.2")')), "L01", "title block revision is 'Rev0.2'")

    def test_no_wip_in_the_title_block(self):
        self.fails(variant(edit=swap("WIP - MANUFACTURING PROHIBITED", "APPROVED")), "L01", "does not state WIP", alone=True)

    def test_a_board_file_with_cr_lf_lines(self):
        self.fails(variant(edit=lambda text: text.replace("\n", "\r\n")), "L01", f"CR bytes in ['{PCB}']", alone=True)


class L02Board(LidTest):
    def test_no_board(self):
        d = fresh()
        self.fails(run(CHECK, "--src", d, "--no-drc"), "L02", "does not load")

    def test_four_copper_layers(self):
        edit = swap('(0 "F.Cu" signal)\n', '(0 "F.Cu" signal)\n\t\t(4 "In1.Cu" signal)\n\t\t(6 "In2.Cu" signal)\n')
        self.fails(variant(edit=edit), "L02", "4 copper layers, want 2")

    def test_another_thickness(self):
        self.fails(variant(edit=swap("(thickness 1.6)", "(thickness 1)")), "L02", "thickness 1 mm, the interface says 1.6", alone=True)

    def test_a_narrower_outline(self):
        self.fails(variant(edit=swap("(end 150 122)", "(end 149 122)")), "L02", "the outline is")

    def test_an_outline_of_another_interface(self):
        def edit(data):
            data["outline"]["x1"] = 99.0
        self.fails(variant(check="reference", check_iface=interface(edit), restamp=True), "L02", "the outline is")

    def test_the_plot_origin_off_the_corner(self):
        self.fails(variant(edit=swap("(aux_axis_origin 50 122)", "(aux_axis_origin 50 50)")), "L02",
                   "the plot and drill origin is (0, 72)", alone=True)

    def test_a_track(self):
        self.fails(variant(edit=append(TRACK)), "L02", "1 track or via item(s)", alone=True)

    def test_a_net(self):
        self.fails(variant(edit=swap('(net 0 "")\n', '(net 0 "")\n\t(net 1 "GND")\n')), "L02", "1 net(s)", alone=True)

    def test_a_drawing_on_copper(self):
        self.fails(variant(edit=append(line_on("F.Cu"))), "L02", "1 drawing(s) on a copper layer", alone=True)


class L03Holes(LidTest):
    def test_a_hole_missing(self):
        def edit(data):
            data["holes"].remove(hole(data, "H4"))
        self.fails(variant(iface=interface(edit), check="reference", restamp=True), "L03", "holes missing from the board: ['H4']")

    def test_a_hole_too_many(self):
        def edit(data):
            data["holes"].append({"ref": "H9", "kind": "pinhole", "x": 50.0, "y": 20.0, "d": 2.0})
        self.fails(variant(iface=interface(edit), check="reference", restamp=True), "L03", "does not name, or named twice: ['H9']")

    def test_a_hole_moved(self):
        def edit(data):
            hole(data, "SW1")["x"] = 32.0
        self.fails(variant(iface=interface(edit), check="reference", restamp=True), "L03", "hole SW1: at (32, 4.5), want (31.5, 4.5)")

    def test_a_hole_of_another_diameter(self):
        def edit(data):
            hole(data, "SW2")["d"] = 4.0
        self.fails(variant(iface=interface(edit), check="reference", restamp=True), "L03", "hole SW2: drill 4 x 4 mm, want round 4.6")

    def test_a_plated_hole(self):
        self.fails(variant(edit=swap("np_thru_hole", "thru_hole")), "L03", "the hole is plated, want unplated")

    def test_a_copper_ring(self):
        self.fails(variant(edit=swap("(size 2.3 2.3)", "(size 3.3 3.3)")), "L03", "a copper ring: pad 3.3 mm on a 2.3 mm hole")

    def test_a_second_pad_in_a_hole_footprint(self):
        pad = ('\t\t(pad "" np_thru_hole circle\n\t\t\t(at 1 0)\n\t\t\t(size 1 1)\n\t\t\t(drill 1)\n'
               '\t\t\t(layers "*.Cu" "*.Mask")\n\t\t\t(uuid "' + UUID + '5")\n\t\t)\n')
        self.fails(variant(edit=swap("\t\t(embedded_fonts no)\n", pad + "\t\t(embedded_fonts no)\n")), "L03", "hole H2: 2 pads, want 1")

    def test_a_drawing_in_a_hole_footprint(self):
        line = ('\t\t(fp_line\n\t\t\t(start -1 0)\n\t\t\t(end 1 0)\n\t\t\t(stroke\n\t\t\t\t(width 0.2)\n\t\t\t\t(type default)\n\t\t\t)\n'
                '\t\t\t(layer "F.SilkS")\n\t\t\t(uuid "' + UUID + '6")\n\t\t)\n')
        self.fails(variant(edit=swap("\t\t(attr board_only", line + "\t\t(attr board_only")), "L03",
                   "hole H2: the footprint carries a drawing")


class L04KeepClear(LidTest):
    def drifted(self, change):
        return variant(doc=change, check="reference", restamp=True)

    def test_copper_too_near_a_button_hole(self):
        self.fails(self.drifted(param("hole_clear", 0.1)), "L04", "in hole SW1 + 0.5 mm", "in hole SW3 + 0.5 mm", alone=True)

    def test_copper_under_a_screw_head(self):
        self.fails(self.drifted(param("head_clear", -0.5)), "L04", "in the screw head of H1 + 0.25 mm", alone=True)

    def test_copper_too_near_a_window(self):
        self.fails(self.drifted(param("window_clear", 0)), "L04", "in window D10/D11 + 0.2 mm", alone=True)

    def test_copper_too_near_the_outline(self):
        self.fails(self.drifted(param("edge_clear", 0.3)), "L04", "within 0.5 mm of the outline", alone=True)

    def test_a_clearance_chosen_below_what_a_board_may_have_at_the_outline(self):
        """The table and the board agree, and KiCad's DRC passes: it does not measure a pour
        against the outline. Only the checker's own measurement names it."""
        result = variant(doc=param("edge_clear", 0.1), drc=True)
        self.fails(result, "L04", "F.Cu: copper nearer than a board may have it", "B.Cu: copper nearer than a board may have it",
                   "within 0.3 mm of the outline (copper_edge_min)", alone=True)
        self.assertIn("PASS L11 KiCad's DRC, every severity: 0 violations", result[1])

    def test_a_clearance_chosen_below_what_a_board_may_have_at_a_hole(self):
        self.fails(variant(doc=param("hole_clear", 0.1)), "L04", "within 0.25 mm of the wall of hole SW1 (copper_hole_min)",
                   "within 0.25 mm of the wall of hole SW3 (copper_hole_min)", alone=True)


class L05Copper(LidTest):
    def test_copper_missing_round_a_hole(self):
        self.fails(variant(doc=param("hole_clear", 2.0), check="reference", restamp=True), "L05",
                   "F.Cu:", "B.Cu:", "has no copper where it is demanded", alone=True)

    def test_one_side_without_copper(self):
        self.fails(variant(edit=cut("(filled_polygon", 1)), "L05", "B.Cu:", "the two sides' copper differs", alone=True)


class L06Mask(LidTest):
    def test_mask_expansion(self):
        self.fails(variant(edit=swap("(pad_to_mask_clearance 0)", "(pad_to_mask_clearance 0.6)")), "L06",
                   "mask expansion 0.6 mm on the board", "of copper lies under a mask opening", alone=True)

    def test_a_pad_with_its_own_mask_margin(self):
        edit = swap('(layers "*.Cu" "*.Mask")\n', '(layers "*.Cu" "*.Mask")\n\t\t\t(solder_mask_margin 0.2)\n')
        self.fails(variant(edit=edit), "L06", "pads with their own margin ['H2']", alone=True)

    def test_a_window_closed_on_the_bottom(self):
        self.fails(variant(edit=cut("(gr_rect", 2)), "L06", "bottom mask: no opening on window D10/D11", alone=True)

    def test_an_opening_that_is_no_window(self):
        self.fails(variant(edit=append(MASK_RECT)), "L06", "top mask: an opening", "that is no window of the interface",
                   "of copper lies under a mask opening", alone=True)

    def test_a_window_in_another_place(self):
        def edit(data):
            data["windows"][0]["rect"] = [33.6, 9.9, 35.9, 13.6]
        self.fails(variant(iface=interface(edit), check="reference", restamp=True), "L06",
                   "top mask: no opening on window D10/D11", "bottom mask: no opening on window D10/D11")

    def test_a_window_drawn_as_a_frame(self):
        self.fails(variant(edit=swap("(fill yes)", "(fill no)")), "L06", "top mask: a rectangle at", "that is not a filled rectangle")


class L07LegendRules(LidTest):
    def test_a_text_too_small(self):
        self.fails(variant(doc=row("revision", height=0.8, stroke=0.15)), "L07", "row revision: height 0.8 mm, below 1")

    def test_a_stroke_too_fine(self):
        self.fails(variant(doc=row("revision", stroke=0.1)), "L07", "row revision: stroke 0.1 mm, below 0.250", alone=True)

    def test_a_text_that_is_not_latin(self):
        self.fails(variant(doc=row("J1", text="ホスト")), "L07", "row J1: the text", "not printable ASCII")

    def test_a_label_used_twice(self):
        self.fails(variant(doc=new_row("title", "top", "TWICE", "centre", 0, 12, 1.5, 0.25)), "L07", "row title: the label is used twice", alone=True)

    def test_a_side_that_does_not_exist(self):
        self.fails(variant(doc=row("order", side="inner")), "L07", "row order: side 'inner'")

    def test_an_anchor_that_does_not_exist(self):
        self.fails(variant(check="reference", check_doc=row("revision", anchor="SW9")), "L07",
                   "legend row revision: anchor SW9 is neither")

    def test_a_ring_too_fine(self):
        self.fails(variant(doc=param("ring_stroke", 0.1)), "L07", "ring_stroke 0.1 mm, below 0.15", alone=True)

    def test_an_arrow_too_small(self):
        self.fails(variant(doc=param("arrow_h", 0.5)), "L07", "arrow_h 0.5 mm, below 1", alone=True)

    def test_a_document_without_its_legend_table(self):
        self.fails(variant(check="reference", check_doc=lambda t: t.replace("lid-legend:begin", "lid-legend:start")), "L07",
                   "does not read: no lid-legend table")


class L08LegendDrawn(LidTest):
    def test_a_text_moved_on_the_board(self):
        self.fails(variant(edit=resub(r'(\(gr_text "HOST"\s+\(at )126 ', r"\g<1>127 ")), "L08",
                   "row J1: no text 'HOST' on the top at (76, 65.5)", "a text 'HOST' at (77, 65.5) that is no row of the table")

    def test_a_text_of_another_size(self):
        self.fails(variant(doc=row("revision", height=2.0, stroke=0.4), check="reference", restamp=True), "L08",
                   "row revision: size 2 x 2, want 1.5, stroke 0.4, want 0.25", alone=True)

    def test_a_bottom_text_not_mirrored(self):
        self.fails(variant(edit=swap("\t\t\t(justify mirror)\n", "")), "L08", "row order: not mirrored on the bottom", alone=True)

    def test_a_text_turned(self):
        self.fails(variant(edit=swap("(at 126 56.5 0)", "(at 126 56.5 90)")), "L08", "row J1: turned, hidden, italic or bold")

    def test_a_text_that_is_no_row(self):
        self.fails(variant(edit=append(TEXT)), "L08", "a text 'X' at (50, 22) that is no row of the table", alone=True)

    def test_an_arrow_missing(self):
        self.fails(variant(edit=cut("(gr_poly", 0)), "L08", "no arrow for port J4")

    def test_an_arrow_of_another_shape(self):
        self.fails(variant(doc=param("arrow_w", 4.0), check="reference", restamp=True), "L08", "no arrow for port J1",
                   "that the document does not describe", alone=True)

    def test_a_ring_of_another_diameter(self):
        self.fails(variant(doc=param("ring_d", 7.0), check="reference", restamp=True), "L08",
                   "no ring of 6.4 mm with a 0.3 mm line round SW1", alone=True)

    def test_a_line_on_the_silkscreen(self):
        self.fails(variant(edit=append(line_on("F.SilkS"))), "L08", "on the silkscreen that the document does not describe", alone=True)

    def test_a_line_on_another_layer(self):
        self.fails(variant(edit=append(line_on("F.Fab"))), "L08", "a PCB_SHAPE on layer F.Fab that the document does not describe", alone=True)

    def test_a_footprint_text_that_would_print(self):
        self.fails(variant(edit=swap("(hide yes)", "(hide no)")), "L08", "footprint texts that would print: ['H2.Reference']", alone=True)


class L09LegendContent(LidTest):
    def test_two_port_names_swapped(self):
        self.fails(variant(doc=both(row("J1", text="5V IN"), row("J4", text="HOST"))), "L09",
                   "port J1: the ink of 'HOST' is centred at x = 17.", "port J4: the ink of '5V IN' is centred at x = 75.", alone=True)

    def test_a_port_name_misspelt(self):
        self.fails(variant(doc=row("J3", text="OUT 2")), "L09", "port J3: 0 texts 'OUT B' on the top, want 1", alone=True)

    def test_a_label_beside_its_port(self):
        self.fails(variant(doc=row("J2", dx=3)), "L09", "port J2: the ink of 'OUT A' is centred at x = 20.", alone=True)

    def test_a_label_on_the_other_half(self):
        self.fails(variant(doc=row("J3", dy=50)), "L09", "port J3: 'OUT B' is not on the port's half of the lid")

    def test_no_product_name(self):
        self.fails(variant(doc=row("title", text="Power Hub")), "L09", "no text 'USB Power-Control Hub' on the top", alone=True)

    def test_another_revision_on_the_top(self):
        self.fails(variant(doc=row("revision", text="Lid Rev0.2")), "L09", "no text on the top carries the title block's revision 'Rev0.1'",
                   alone=True)

    def test_boot_far_from_its_pinhole(self):
        self.fails(variant(doc=row("SW3", dx=12)), "L09", "pinhole SW3: 1 texts 'BOOT' on the top", "want one within 3 mm", alone=True)

    def test_no_boot_label(self):
        self.fails(variant(doc=no_row("SW3")), "L09", "pinhole SW3: 0 texts 'BOOT' on the top", alone=True)

    def test_no_arrow_at_a_port(self):
        self.fails(variant(edit=cut("(gr_poly", 0)), "L09", "port J4: 0 arrows at the port, want 1")

    def test_an_arrow_that_does_not_point_at_the_edge(self):
        edit = swap("(xy 67.5 50.8) (xy 66 52.8) (xy 69 52.8)", "(xy 67.5 50.8) (xy 66 50.8) (xy 69 52.8)")
        self.fails(variant(edit=edit), "L09", "port J4: the arrow does not point at the edge")

    def test_a_port_this_checker_cannot_name(self):
        def edit(data):
            data["ports"].append({"ref": "J5", "x": 50.0, "edge": "back"})
        self.fails(variant(iface=interface(edit)), "L09", "port J5: this checker knows no name for it", alone=True)

    def test_an_arrow_behind_its_label(self):
        self.fails(variant(doc=param("arrow_tip", 9)), "L09", "port J2: the arrow is not between the edge and the label", alone=True)

    def test_a_ring_narrower_than_its_hole(self):
        self.fails(variant(doc=param("ring_d", 4.0)), "L09", "button hole SW1: 0 rings centred on it and wider than it")


class L10SilkClear(LidTest):
    def test_a_label_over_the_outline(self):
        self.fails(variant(doc=row("J4", dx=-12)), "L10", 'top silkscreen: "5V IN" is within 0.5 mm of the outline')

    def test_a_label_over_a_screw_head(self):
        self.fails(variant(doc=row("revision", anchor="H1", dx=0, dy=0)), "L10", '"Lid Rev0.1" is within 0.3 mm of the screw head of H1')

    def test_a_label_over_the_pinhole(self):
        self.fails(variant(doc=row("SW3", dx=3.8)), "L10", '"BOOT" is within 0.3 mm of hole SW3', alone=True)

    def test_a_label_over_a_window(self):
        self.fails(variant(doc=row("revision", anchor="SW1", dx=-1.75, dy=7.25)), "L10", '"Lid Rev0.1" is within 0.3 mm of window D10/D11',
                   alone=True)

    def test_two_texts_too_close(self):
        self.fails(variant(doc=row("revision", dy=1.6)), "L10", '"Lid Rev0.1" is within 0.2 mm of "USB Power-Control Hub"', alone=True)

    def test_a_ring_too_near_its_hole(self):
        self.fails(variant(doc=param("ring_d", 5.2)), "L10", "circle at (31.5, 4.5) is within 0.3 mm of hole SW1", alone=True)

    def test_a_text_too_close_on_the_bottom(self):
        self.fails(variant(doc=row("order", dy=2.5)), "L10", "bottom silkscreen:", '"JLCJLCJLCJLC" is within 0.2 mm of "USB Power-Control Hub Lid Rev0.1"', alone=True)


class L11Drc(LidTest):
    def test_copper_at_a_hole(self):
        self.fails(variant(doc=param("hole_clear", 0.1), drc=True), "L11", "KiCad's DRC: 6 violations ['hole_clearance']")

    def test_a_text_below_the_project_rule(self):
        self.fails(variant(doc=row("revision", height=0.8, stroke=0.15), drc=True), "L11", "KiCad's DRC:", "text_height")


class L12Set(LidTest):
    def test_a_file_missing(self):
        self.fails(set_variant(lambda out: (out / f"{spec.PREFIX}_Preview_Top.png").unlink()), "L12", "the set in", "holds")

    def test_a_file_too_many(self):
        self.fails(set_variant(lambda out: (out / "notes.txt").write_bytes(b"x")), "L12", "notes.txt", alone=True)

    def test_a_file_changed_after_the_sums(self):
        def edit(out):
            p = out / f"{spec.PREFIX}_Fabrication_Top.pdf"
            p.write_bytes(p.read_bytes() + b"\n")
        self.fails(set_variant(edit, restamp=False), "L12", "SHA256SUMS.txt disagrees with the files", "Fabrication_Top.pdf", alone=True)

    def test_a_set_older_than_its_board(self):
        def touch(src):
            p = src / f"{spec.NICK}.kicad_pro"
            p.write_bytes(p.read_bytes() + b"\n")
        self.fails(set_variant(lambda out: None, src_edit=touch), "L12", "the set is stale, run make_lid_outputs.py", alone=True)

    def test_a_manifest_that_is_not_wip(self):
        def edit(out):
            p = out / "RELEASE_MANIFEST.md"
            p.write_bytes(p.read_bytes().replace(b"| State | WIP |", b"| State | REVIEWED |"))
        self.fails(set_variant(edit), "L12", "the manifest does not state", alone=True)

    def test_a_picture_that_is_no_picture(self):
        self.fails(set_variant(lambda out: (out / f"{spec.PREFIX}_Preview_Bottom.png").write_bytes(b"not a picture")), "L12",
                   "files that are not what their name says", "Preview_Bottom.png (no PNG)", alone=True)

    def test_a_picture_too_small_to_be_the_render(self):
        def shrink(out):
            p = out / f"{spec.PREFIX}_Preview_Top.png"
            data = p.read_bytes()
            p.write_bytes(data[:16] + (64).to_bytes(4, "big") + (46).to_bytes(4, "big") + data[24:])
        self.fails(set_variant(shrink), "L12", "Preview_Top.png (64 x 46 px, want at least 1200 wide)", alone=True)

    def test_a_drawing_that_is_only_a_pdf_header(self):
        self.fails(set_variant(lambda out: (out / f"{spec.PREFIX}_Fabrication_Top.pdf").write_bytes(b"%PDF-1.4 and no page")),
                   "L12", "Fabrication_Top.pdf (0 pages, want 1)", alone=True)


def first_region(data):
    """The file without its first filled region (G36 to G37)."""
    a = data.index(b"G36*")
    z = data.index(b"G37*", a) + len(b"G37*")
    return data[:a] + data[z:]


class L13Gerber(LidTest):
    def test_a_layer_missing(self):
        self.fails(set_variant(member("B_Mask.gbs", lambda data: None)), "L13", "the Gerber zip holds")

    def test_a_zip_that_does_not_open(self):
        self.fails(set_variant(lambda out: (out / ZIP).write_bytes(b"PK is not enough")), "L13", "the Gerber zip does not open")

    def test_the_outline_off_its_frame(self):
        shift = lambda data: data.replace(b"X0Y", b"X50000000Y").replace(b"X100000000Y", b"X150000000Y")  # noqa: E731
        self.fails(set_variant(member("Edge_Cuts.gm1", shift)), "L13", "the outline Gerber's extents are (50.0, 0.0, 150.0, 72.0)",
                   with_plot=True)

    def test_one_corner_of_the_outline_moved_inside_its_extents(self):
        cut_corner = bytes_swap(b"X100000000Y72000000D01*", b"X99900000Y72000000D01*")
        self.fails(set_variant(member("Edge_Cuts.gm1", cut_corner)), "L13",
                   "the outline Gerber's extents are (0.0, 0.0, 100.0, 72.0), want (0.0, 0.0, 100.0, 72.0); lines drawn",
                   "no side of the rectangle: [((0.0, 72.0), (99.9, 72.0)), ((99.9, 72.0), (100.0, 0.0))]",
                   "sides not drawn: [((0.0, 72.0), (100.0, 72.0)), ((100.0, 0.0), (100.0, 72.0))]", with_plot=True)

    def test_a_line_across_the_outline(self):
        across = bytes_swap(b"M02*", b"X100000000Y0D01*\r\nM02*")
        self.fails(set_variant(member("Edge_Cuts.gm1", across)), "L13",
                   "no side of the rectangle: [((0.0, 72.0), (100.0, 0.0))]; sides not drawn: []", with_plot=True)

    def test_an_outline_with_an_arc(self):
        arc = bytes_swap(b"X100000000Y0D01*", b"G03X100000000Y0I0J-36000000D01*")
        self.fails(set_variant(member("Edge_Cuts.gm1", arc)), "L13", "it draws an arc, a flash or nothing readable", with_plot=True)

    def test_copper_beyond_its_inset(self):
        self.fails(set_variant(member("F_Cu.gtl", bytes_swap(b"X99500000", b"X99800000"))), "L13",
                   "F_Cu.gtl: the copper's extents are (0.5, 0.5, 99.8, 71.5)", with_plot=True)

    def test_a_window_missing_from_the_mask(self):
        self.fails(set_variant(member("B_Mask.gbs", first_region)), "L13", "B_Mask.gbs: no opening found for ['D10/D11']",
                   with_plot=True)

    def test_a_hole_missing_from_the_mask(self):
        self.fails(set_variant(member("F_Mask.gts", bytes_swap(b"X31850000Y68600000D03*", b"X41850000Y68600000D03*"))), "L13",
                   "F_Mask.gts: no opening found for ['SW3']", with_plot=True)


class L14Drill(LidTest):
    def test_a_hole_moved(self):
        self.fails(set_variant(member("NPTH.drl", bytes_swap(b"X31.5Y4.5", b"X31.6Y4.5"))), "L14", "the unplated drill file holds",
                   with_plot=True)

    def test_a_tool_of_another_diameter(self):
        self.fails(set_variant(member("NPTH.drl", bytes_swap(b"T3C4.600", b"T3C4.000"))), "L14", "the unplated drill file holds",
                   with_plot=True)

    def test_a_hole_missing(self):
        self.fails(set_variant(member("NPTH.drl", bytes_swap(b"X65.3Y4.5\r\n", b""))), "L14", "the unplated drill file holds",
                   with_plot=True)

    def test_a_plated_hole(self):
        add = lambda data: data.replace(b"%\r\n", b"T1C0.300\r\n%\r\n", 1).replace(b"M30", b"T1\r\nX10.0Y10.0\r\nM30")  # noqa: E731
        self.fails(set_variant(member("PTH.drl", add)), "L14", "the plated drill file holds [(10.0, 10.0, 0.3)], want none",
                   with_plot=True)


class L15Report(LidTest):
    def report(self, change):
        def edit(out):
            p = out / f"{spec.PREFIX}_DRC.json"
            data = json.loads(p.read_text(encoding="utf-8"))
            change(data)
            p.write_bytes((json.dumps(data, indent=2) + "\n").encode("utf-8"))
        return set_variant(edit)

    def test_a_report_with_a_violation(self):
        def change(data):
            data["violations"].append({"type": "clearance", "severity": "error", "description": "x", "items": []})
        self.fails(self.report(change), "L15", "the set's DRC report: 1 violations", alone=True)

    def test_a_report_that_does_not_read(self):
        self.fails(set_variant(lambda out: (out / f"{spec.PREFIX}_DRC.json").write_bytes(b"{")), "L15",
                   "the set's DRC report does not read", alone=True)

    def test_a_report_of_another_board(self):
        def change(data):
            data["source"] = "usb-power-hub.kicad_pcb"
        self.fails(self.report(change), "L15", "source 'usb-power-hub.kicad_pcb'", alone=True)


class L16Plot(LidTest):
    """Faults that no read-back of L13 or L14 sees: L16 alone must report them."""

    def test_a_region_missing_from_the_top_silkscreen(self):
        self.fails(set_variant(member("F_Silkscreen.gto", first_region)), "L16", "not KiCad's plot of this board: F_Silkscreen.gto",
                   alone=True)

    def test_a_region_missing_from_the_bottom_copper(self):
        # the extents stay, because the first region of the fill is not the only one that reaches them
        self.fails(set_variant(member("B_Cu.gbl", first_region)), "L16", "B_Cu.gbl")

    def test_a_drill_map_of_another_hole(self):
        self.fails(set_variant(member("NPTH-drl_map.gbr", bytes_swap(b"X31", b"X32"))), "L16",
                   "not KiCad's plot of this board: NPTH-drl_map.gbr", alone=True)

    def test_two_members_changed(self):
        def edit(out):
            member("F_Silkscreen.gto", first_region)(out)
            member("B_Silkscreen.gbo", bytes_swap(b"D01*", b"D02*"))(out)
        self.fails(set_variant(edit), "L16", "B_Silkscreen.gbo, F_Silkscreen.gto", alone=True)

    def test_a_set_plotted_at_another_time_is_this_plot(self):
        later = lambda data: data.replace(b"1980-01-01T00:00:00+00:00", b"2026-11-18T09:30:00+09:00").replace(  # noqa: E731
            b"date 1980-01-01 00:00:00", b"date 2026-11-18 09:30:00")
        self.passes(set_variant(member("F_Cu.gtl", later)), "L13", "L16")


if __name__ == "__main__":
    unittest.main(verbosity=1)
