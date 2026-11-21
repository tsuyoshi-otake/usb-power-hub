"""Negative tests for check_enclosure.py (CLAUDE.md 8: a checker never observed failing is
not evidence).

Run with the CAD venv's Python from the repository root:

    ~/tmp/cadvenv/Scripts/python.exe -I -B design/mechanical/scripts/test_check_enclosure.py

Each test builds the enclosure into a temporary directory, with one parameter overridden
(make_enclosure.py --set) or with one file corrupted afterwards, and runs check_enclosure.py
on it in a new process. The unchanged build must pass; every corruption must fail and be
named in the output. The repository's files are never modified. A test that edits a built
file also corrects its SHA-256 in the manifest, so that only the check under test fails.
The whole run takes about 2 min.
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
MAKE = HERE / "make_enclosure.py"
CHECK = HERE / "check_enclosure.py"


def _load(name):
    s = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load("enclosure_spec")
S = _load("enclosure_solid")
draw = _load("render_enclosure")


def run(script, *args):
    r = subprocess.run([sys.executable, "-I", "-B", str(script), *map(str, args)],
                       capture_output=True, text=True, encoding="utf-8", timeout=600)
    return r.returncode, r.stdout + r.stderr


def variant(*sets, edit=None, doc=None, interface=None, board=None, pictures=None):
    """Build with the overrides, apply edit(directory), check; doc/interface/board(text) -> text.

    pictures(directory, pictures_directory) fills a directory that the checker is then given.
    """
    with tempfile.TemporaryDirectory(prefix="enclosuretest-") as tmp:
        t = pathlib.Path(tmp)
        out = t / "assembly"
        args = [a for s in sets for a in ("--set", s)]
        rc, text = run(MAKE, "--no-check", "--out", out, *args)
        assert rc == 0, f"the build failed:\n{text}"
        if edit:
            edit(out)
        extra = []
        if pictures:
            (t / "reports").mkdir()
            pictures(out, t / "reports")
            extra += ["--pictures", t / "reports"]
        for flag, change, src in (("--doc", doc, spec.DOC), ("--interface", interface, spec.INTERFACE),
                                  ("--board", board, spec.ROOT / "design" / "ecad" / "source"
                                   / "usb-power-hub.kicad_pcb")):
            if change:
                old = src.read_text(encoding="utf-8")
                new = change(old)
                assert new != old, f"the {flag} corruption changed nothing"
                (t / src.name).write_text(new, encoding="utf-8", newline="\n")
                extra += [flag, t / src.name]
        return run(CHECK, "--dir", out, *extra)


# ---- corruptions of the built files -----------------------------------------------------------
def manifest_of(out):
    path = out / spec.MANIFEST
    return path, json.loads(path.read_text(encoding="ascii"))


def picture(pic, source):
    draw.write_png(pic / f"{spec.PREFIX}Assembled.png", np.zeros((2, 2, 3), dtype=np.uint8), source)


def save_manifest(path, manifest):
    path.write_bytes((json.dumps(manifest, indent=1) + "\n").encode("ascii"))


def rewrite_stl(name, change):
    """change(tri, to_assembly) -> (tri, to_assembly); the manifest follows the new file."""
    def edit(out):
        path, manifest = manifest_of(out)
        piece = next(q for q in manifest["pieces"] if q["name"] == name)
        tri, back = change(S.read_stl(out / piece["file"]), piece["to_assembly"])
        data = S.stl_bytes(tri, f"corrupted {name}")
        (out / piece["file"]).write_bytes(data)
        piece["sha256"], piece["to_assembly"] = hashlib.sha256(data).hexdigest(), back
        save_manifest(path, manifest)
    return edit


def rewrite_lid(change):
    def edit(out):
        path, manifest = manifest_of(out)
        f = out / manifest["lid_interface"]["file"]
        lid = json.loads(f.read_text(encoding="ascii"))
        change(lid)
        data = (json.dumps(lid, indent=1) + "\n").encode("ascii")
        f.write_bytes(data)
        manifest["lid_interface"]["sha256"] = hashlib.sha256(data).hexdigest()
        save_manifest(path, manifest)
    return edit


def as_json(change):
    """A corruption of a JSON text: change(parsed) edits it in place."""
    def edit(text):
        data = json.loads(text)
        change(data)
        return json.dumps(data, indent=1) + "\n"
    return edit


def moved(ref, dx=0.0, dy=0.0):
    """A corruption of the board interface: one footprint and its courtyard moved."""
    def change(board):
        fp = next(f for f in board["footprints"] if f["ref"] == ref)
        fp["x"], fp["y"] = round(fp["x"] + dx, 4), round(fp["y"] + dy, 4)
        fp["courtyard"] = [round(v + d, 4) for v, d in zip(fp["courtyard"], (dx, dy, dx, dy))]
    return as_json(change)


def compose(back, m34):
    """The matrices `back` after m34: new_to_assembly(p) = back(m34(p))."""
    m = np.vstack([np.asarray(m34, dtype=float), [0, 0, 0, 1]])
    return [(np.vstack([np.asarray(b, dtype=float), [0, 0, 0, 1]]) @ m)[:3].tolist() for b in back]


def turned_over(tri, back):
    hi = tri.reshape(-1, 3).max(axis=0)
    flip = [[1, 0, 0, 0], [0, -1, 0, hi[1]], [0, 0, -1, hi[2]]]      # its own inverse
    return S.apply(tri, flip), compose(back, flip)


def lifted(tri, back):
    return tri + np.array([0, 0, 1.0]), compose(back, [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, -1.0]])


def reshaped(change):
    """A corruption of a piece's shape: change(solid in the assembly frame) -> solid."""
    def edit(tri, back):
        man = change(S.to_manifold(S.apply(tri, back[0])))
        return S.apply(S.triangles(man), S.inverse(back[0])), back
    return edit


def shifted(dx=0.0, dy=0.0, dz=0.0):
    """A corruption of a piece's place: the STL as built, its to_assembly matrix moved."""
    def edit(tri, back):
        return tri, [[row[:3] + [row[3] + d] for row, d in zip(m, (dx, dy, dz))] for m in back]
    return edit


def one_triangle_less(tri, back):
    return tri[1:], back


def with_a_crumb(tri, back):
    crumb = S.triangles(S.box(50, 50, 50, 51, 51, 51))
    return np.concatenate([tri, crumb]), back


# ---- corruptions of the document --------------------------------------------------------------
def table_value(tag, name, value):
    def change(text):
        a, b = text.index(f"<!-- {tag}:begin -->"), text.index(f"<!-- {tag}:end -->")
        new, n = re.subn(r"^(\| `" + re.escape(name) + r"` \| )[^|]*(\|)", rf"\g<1>{value} \g<2>",
                         text[a:b], flags=re.M)
        assert n == 1, f"no row {name} in the {tag} table"
        return text[:a] + new + text[b:]
    return change


def drop_row(tag, name):
    def change(text):
        a, b = text.index(f"<!-- {tag}:begin -->"), text.index(f"<!-- {tag}:end -->")
        new, n = re.subn(r"^\| `" + re.escape(name) + r"` \|.*\n", "", text[a:b], flags=re.M)
        assert n == 1, f"no row {name} in the {tag} table"
        return text[:a] + new + text[b:]
    return change


class CheckEnclosure(unittest.TestCase):
    def assertFailsWith(self, result, *needles):
        rc, out = result
        self.assertEqual(rc, 1, out)
        for needle in needles:
            self.assertIn(needle, out)

    def test_unchanged_passes(self):
        rc, out = variant(pictures=lambda out, pic: picture(pic, spec.source_tag(out / spec.MANIFEST)))
        self.assertEqual(rc, 0, out)
        self.assertNotIn("FAIL", out)
        self.assertNotIn("SKIP", out)
        self.assertIn("PASS E16 1 pictures, each drawn from these files", out)
        self.assertRegex(out, r"enclosure check: \d+ checks, 0 failed")

    # E01 -------------------------------------------------------------------------------------
    def test_no_manifest(self):
        self.assertFailsWith(variant(edit=lambda out: (out / spec.MANIFEST).unlink()),
                             "FAIL E01 no manifest UsbPowerHub_Enclosure_Rev0.5_Manifest.json")

    def test_piece_not_in_the_manifest(self):
        def edit(out):
            path, manifest = manifest_of(out)
            manifest["pieces"] = manifest["pieces"][:2]
            save_manifest(path, manifest)
        self.assertFailsWith(variant(edit=edit),
                             "FAIL E01 pieces ['Tray', 'Frame'], want Tray, Frame, Plunger, Cover",
                             "enclosure check: stopped")

    def test_cover_not_in_the_manifest(self):
        def edit(out):
            path, manifest = manifest_of(out)
            manifest["pieces"] = manifest["pieces"][:3]
            save_manifest(path, manifest)
        self.assertFailsWith(variant(edit=edit), "FAIL E01 pieces ['Tray', 'Frame', 'Plunger'], "
                             "want Tray, Frame, Plunger, Cover", "enclosure check: stopped")

    def test_stl_edited_after_the_build(self):
        def edit(out):
            f = out / f"{spec.PREFIX}Tray.stl"
            raw = bytearray(f.read_bytes())
            raw[200] ^= 1
            f.write_bytes(bytes(raw))
        self.assertFailsWith(variant(edit=edit),
                             "FAIL E01 UsbPowerHub_Enclosure_Rev0.5_Tray.stl: SHA-256 differs")

    def test_piece_missing(self):
        self.assertFailsWith(variant(edit=lambda out: (out / f"{spec.PREFIX}Plunger.stl").unlink()),
                             "FAIL E01 UsbPowerHub_Enclosure_Rev0.5_Plunger.stl: missing")

    def test_document_value_changed_after_the_build(self):
        self.assertFailsWith(variant(doc=table_value("params", "gap", "0.5")),
                             "FAIL E01 the document's tables changed after the pieces were built")

    def test_override_is_named(self):
        self.assertFailsWith(variant("wall=2.5"), "FAIL E01 built with overrides {'wall': 2.5}")

    def test_interface_changed_after_the_build(self):
        self.assertFailsWith(variant(interface=lambda t: t.replace('"x": 5.0,', '"x": 6.0,', 1)),
                             "FAIL E01 the board interface changed after the pieces were built")

    def test_board_changed_after_the_export(self):
        self.assertFailsWith(variant(board=lambda t: t + "\n"),
                             "FAIL E01 the board usb-power-hub.kicad_pcb changed after its "
                             "interface was exported")

    # E02 -------------------------------------------------------------------------------------
    def test_open_mesh(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Frame", one_triangle_less)),
                             "FAIL E02 Frame: watertight False")

    def test_second_body(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Plunger", with_a_crumb)),
                             "FAIL E02 Plunger: watertight True", "bodies 2")

    # E03 -------------------------------------------------------------------------------------
    def test_wall_differs_from_the_document(self):
        self.assertFailsWith(variant("wall=1.5"), "FAIL E03 Tray: box", "FAIL E03 Frame: box")

    def test_corners_sharper_than_the_document(self):
        self.assertFailsWith(variant("corner_r=1.0"), "FAIL E03 Tray: ", "FAIL E03 Frame: ",
                             "mm3 outside the outline and its 2 mm corners")

    def test_body_leaves_the_outline(self):
        def bump(tri, back):
            lump = S.triangles(S.box(-2.0, -2.0, 3.0, 2.0, 2.0, 5.0))      # past a round corner
            whole = S.to_manifold(S.apply(tri, back[0])) + S.to_manifold(lump)
            return S.apply(S.triangles(whole), S.inverse(back[0])), back
        self.assertFailsWith(variant(edit=rewrite_stl("Frame", bump)),
                             "FAIL E03 Frame: ", "mm3 outside the outline and its 2 mm corners")

    # E04 -------------------------------------------------------------------------------------
    def test_frame_printed_the_other_way_up(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Frame", turned_over)),
                             "FAIL E04 Frame: ", "mm2 of faces steeper than 45 degrees hang in the air")

    def test_cover_printed_the_other_way_up(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Cover", turned_over)),
                             "FAIL E04 Cover: ", "mm2 of faces steeper than 45 degrees hang in the air")

    def test_piece_above_the_bed(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Tray", lifted)),
                             "FAIL E04 Tray: lowest point z 1.000")

    def test_unchanged_frame_hangs_only_at_the_lids_seat(self):
        rc, out = variant()
        self.assertRegex(out, r"PASS E04 Frame: the only faces that hang are the lid's seat, "
                              r"1\.6 mm above the bed: 628 mm2 to support")

    def test_frame_face_that_hangs_beside_the_lids_seat(self):
        # a ledge on the back wall's inner face, 11 mm above the board: turned over for
        # printing it hangs 9.6 mm above the bed, and it is not the lid's seat
        ledge = reshaped(lambda man: man + S.box(60.0, 70.4, 10.0, 66.0, 72.6, 11.0))
        rc, out = variant(edit=rewrite_stl("Frame", ledge))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E04 Frame: 1[0-9]\.\d mm2 of faces steeper than 45 degrees "
                              r"hang in the air in the print orientation, the lid's seat "
                              r"\(628\.\d mm2 at 1\.6 mm above the bed\) not counted")

    def test_seat_is_no_excuse_for_another_piece(self):
        # the tray has no seat: a flat face 1.6 mm above its bed, over a hole in the floor,
        # is a hanging face
        shelf = reshaped(lambda man: man + S.box(40.0, 30.0, -5.5, 50.0, 40.0, -4.5)
                         - S.box(42.0, 32.0, -7.2, 48.0, 38.0, -5.5))
        rc, out = variant(edit=rewrite_stl("Tray", shelf))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E04 Tray: \d+\.\d mm2 of faces steeper than 45 degrees hang "
                              r"in the air in the print orientation\n")

    # E05 -------------------------------------------------------------------------------------
    def test_cavity_lower_than_the_tallest_part(self):
        self.assertFailsWith(variant("cavity_h=18.0"), "FAIL E05 F1: ", "of the Lid inside its envelope")

    def test_tube_on_its_switch(self):
        rc, out = variant("ui_bottom=1.0")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E05 SW3: \d+\.\d\d mm3 of the Frame inside its envelope")

    def test_column_beside_the_converter(self):
        # Rev0.1's column, from ui_bottom up, on the Rev0.6 board: SW2 stands beside the MAU104
        rc, out = variant("btn_bottom=2.2")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E05 U5: \d+\.\d\d mm3 of the Frame inside its envelope "
                              r"\(height 10\.2 mm \+ 0\.3 mm\)")
        self.assertNotIn("FAIL E05 SW", out)

    def test_part_under_the_covers_wedge(self):
        # C3 moved to the back edge, under the wedge that reaches over the board
        rc, out = variant(interface=moved("C3", dy=4.0))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E05 C3: \d+\.\d\d mm3 of the Cover inside its envelope")

    def test_part_without_a_height(self):
        name = "Fuse_Bourns_MF-R300_Style2_P5.10mm"
        self.assertFailsWith(variant(doc=drop_row("heights", name)),
                             f"FAIL E05 F1: no height in the document for {name}")

    def test_courtyard_outside_the_cavity(self):
        def change(board):
            f1 = next(f for f in board["footprints"] if f["ref"] == "F1")
            f1["courtyard"][0] = -1.0
        self.assertFailsWith(variant(interface=as_json(change)),
                             "FAIL E05 F1: its courtyard leaves the cavity")

    # E06 -------------------------------------------------------------------------------------
    def test_floor_under_the_leads(self):
        self.assertFailsWith(variant("standoff=2.0"), "FAIL E06 F1 pad '1'",
                             "of the Tray within 2.5 mm below its hole")

    def test_rib_under_a_peg(self):
        self.assertFailsWith(variant("rib_w=6.5"), "FAIL E06 J2 pad ''")

    # E07 -------------------------------------------------------------------------------------
    def test_no_boss_under_a_hole(self):
        self.assertFailsWith(variant("boss_reach=-3.2"), "FAIL E07 H1: 0.0 mm2 of boss below")

    def test_no_post_on_a_hole(self):
        self.assertFailsWith(variant("post_reach=-3.2"), "FAIL E07 H1: ", "mm2 of post above",
                             "FAIL E13 H1: ", "mm2 of post under the lid, want >= 15 mm2")

    def test_rib_touches_the_board(self):
        self.assertFailsWith(variant("rib_gap=0"), "FAIL E07 J1: ", "mm3 above that level (want 0)")

    def test_rib_too_short(self):
        self.assertFailsWith(variant("rib_len=0.6"), "FAIL E07 J2: ",
                             "under the board's edge (want >= 8 mm2)")

    def test_board_inside_the_tray(self):
        self.assertFailsWith(variant("gap=-0.3"), "FAIL E07 ", "of the Tray inside the board")

    def test_board_with_two_mounting_holes(self):
        def change(board):
            for key in ("footprints", "holes"):
                board[key] = [f for f in board[key] if f["ref"] not in ("H3", "H4")]
        self.assertFailsWith(variant(interface=as_json(change)),
                             "FAIL E07 2 mounting points, want >= 3",
                             "FAIL E07 no mounting point within 10 mm of the back edge, which "
                             "carries receptacles")

    # E08 -------------------------------------------------------------------------------------
    def test_shell_hole_too_tight(self):
        self.assertFailsWith(variant("shell_clear=0.1"), "FAIL E08 J1: ",
                             "of plastic within 0.3 mm of the shell")

    def test_pocket_narrower_than_the_overmould(self):
        self.assertFailsWith(variant("pocket_w=12"), "FAIL E08 J2: an overmould of 14 x 7 mm meets")

    def test_pocket_stops_short_of_the_face(self):
        self.assertFailsWith(variant("face_proud=-0.5"), "FAIL E08 J3: an overmould of 14 x 7 mm meets")

    def test_no_web_behind_the_pocket(self):
        self.assertFailsWith(variant("face_proud=0.5"), "FAIL E08 J4: web 0.16 mm")

    # E09 -------------------------------------------------------------------------------------
    def test_bottom_screw_too_short(self):
        self.assertFailsWith(variant(doc=table_value("params", "bottom_screw_len", "8.0")),
                             "FAIL E09 bottom screws: 1.10 mm of thread above the board")

    def test_lid_screw_too_long(self):
        self.assertFailsWith(variant(doc=table_value("params", "lid_screw_len", "8.0")),
                             "FAIL E09 lid screws: 6.40 mm of thread below the lid")

    def test_countersink_smaller_than_the_head(self):
        self.assertFailsWith(variant("csk_d=3.0"), "FAIL E09 H1: ", "of plastic in the bottom screw's way")

    def test_head_falls_through(self):
        self.assertFailsWith(variant("csk_d=7.0"), "FAIL E09 H2: ",
                             "0.00 mm3 of seat under its head (want > 0.05)")

    def test_post_too_thin_for_an_insert(self):
        self.assertFailsWith(variant("post_reach=2.0"), "FAIL E09 H1 foot: ", "FAIL E09 H1 top: ")

    def test_insert_hole_smaller_than_the_document(self):
        self.assertFailsWith(variant("insert_hole_d=2.6"), "FAIL E09 H3 foot: ", "mm3 in the hole")

    def test_lid_without_a_screw_hole(self):
        def change(lid):
            lid["holes"] = [h for h in lid["holes"] if h["ref"] != "H1"]
        self.assertFailsWith(variant(edit=rewrite_lid(change)),
                             "FAIL E09 H1: ", "in the lid screw's way, lid hole missing")

    # E10 -------------------------------------------------------------------------------------
    def test_plunger_held_down_by_the_lid(self):
        self.assertFailsWith(variant("plunger_play=-0.2"),
                             "FAIL E10 SW1: lifted 0.45 mm the plunger meets the lid by")

    def test_bore_too_tight(self):
        self.assertFailsWith(variant("btn_bore_d=3.1"), "FAIL E10 SW2: the plunger meets plastic",
                             "moved 0.15 mm sideways")

    def test_bore_too_loose(self):
        self.assertFailsWith(variant("btn_bore_d=5.0", "btn_cbore_d=6.4"),
                             "FAIL E10 SW1: the plunger can move 0.5 mm sideways")

    def test_counterbore_in_a_thin_wall(self):
        # Rev0.1's wall: 1.5 mm round the bore leaves 0.4 mm round the counterbore
        rc, out = variant("btn_wall=1.5")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E10 SW1: \d\d\.\d % of the 0\.8 mm ring around the plunger's "
                              r"counterbore is plastic, want 100")
        self.assertIn("PASS E10 SW1: 0.8 mm of plastic all round the plunger's bore", out)

    def test_bore_in_a_thin_wall(self):
        rc, out = variant("btn_wall=0.5")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E10 SW2: \d\d\.\d % of the 0\.8 mm ring around the plunger's "
                              r"bore is plastic, want 100")

    def test_plunger_leaves_through_the_lid(self):
        self.assertFailsWith(variant("lid_btn_d=5.4"), "FAIL E10 SW1: lifted", "it must not leave")

    def test_cap_too_low(self):
        self.assertFailsWith(variant("plunger_proud=0.3"), "FAIL E10 SW1: cap 0.30 mm above the lid")

    def test_collar_lands_before_the_switch_clicks(self):
        rc, out = variant("btn_cbore_depth=1.6")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E10 SW1: the plunger meets plastic: 0\.00 mm3 at rest, "
                              r"(?!0\.00 )\d+\.\d\d mm3 pressed 0\.4 mm, 0\.00 mm3 moved")

    def test_switch_lower_than_the_plunger_assumes(self):
        name = "SW_Push_1P1T_XKB_TS-1187A"
        self.assertFailsWith(variant(doc=table_value("heights", name, "1.2")),
                             "FAIL E10 SW1: plunger axis", "foot at 1.50 mm", "actuator at 1.2 mm")

    def test_lid_without_a_button_hole(self):
        def change(lid):
            lid["holes"] = [h for h in lid["holes"] if h["ref"] != "SW1"]
        self.assertFailsWith(variant(edit=rewrite_lid(change)),
                             "FAIL E10 SW1: the plunger meets plastic",
                             "FAIL E10 SW1: cap 1.00 mm above the lid", "lid hole missing")

    def test_plunger_missing(self):
        def edit(out):
            path, manifest = manifest_of(out)
            piece = next(q for q in manifest["pieces"] if q["name"] == "Plunger")
            piece["to_assembly"] = piece["to_assembly"][:1]
            save_manifest(path, manifest)
        self.assertFailsWith(variant(edit=edit), "FAIL E10 2 port buttons on the board, 1 plungers")

    # E11 -------------------------------------------------------------------------------------
    def test_frame_over_an_led(self):
        self.assertFailsWith(variant("led_well_margin=-0.8"), "FAIL E11 D10: ", "mm3 of frame above it")

    def test_light_well_wall_too_thin(self):
        self.assertFailsWith(variant("led_wall=0.3"), "FAIL E11 window at (28.60, 9.90): ")

    def test_lid_without_a_window(self):
        def change(lid):
            lid["windows"] = lid["windows"][1:]
        self.assertFailsWith(variant(edit=rewrite_lid(change)),
                             "FAIL E11 D10: 0.00 mm3 of frame above it, window in the lid missing")

    # E12 -------------------------------------------------------------------------------------
    def test_pinhole_too_small_for_the_wire(self):
        self.assertFailsWith(variant("lid_boot_d=0.5"), "FAIL E12 SW3: ", "in the wire's way")

    def test_tube_wider_than_the_actuator(self):
        self.assertFailsWith(variant("boot_bore_d=4.0"), "FAIL E12 SW3: 0.00 mm3 in the wire's way",
                             "of the tube's wall is plastic (want 100)")

    def test_lid_without_the_pinhole(self):
        def change(lid):
            lid["holes"] = [h for h in lid["holes"] if h["kind"] != "pinhole"]
        self.assertFailsWith(variant(edit=rewrite_lid(change)), "FAIL E12 SW3: ",
                             "pinhole in the lid missing")

    # E13 -------------------------------------------------------------------------------------
    def test_lid_smaller_than_the_board(self):
        def change(lid):
            lid["outline"]["x1"] = 98.0
        self.assertFailsWith(variant(edit=rewrite_lid(change)), "FAIL E13 ",
                             "outline not the board's")

    def test_no_flange_under_the_lid(self):
        self.assertFailsWith(variant("lid_overlap=-0.6"), "FAIL E13 ",
                             "% of the lid's outer 0.5 mm lies on the frame, want 100")

    def test_flange_narrower_than_the_lid_needs(self):
        self.assertFailsWith(variant("lid_overlap=0.3"), "FAIL E13 ",
                             "% of the lid's outer 0.5 mm lies on the frame, want 100")

    def test_lid_lower_than_the_frame(self):
        def change(lid):
            lid["underside_above_board"] = 18.0
        self.assertFailsWith(variant(edit=rewrite_lid(change)), "FAIL E13 ", "lid underside at 18 mm")

    def test_lid_above_its_seat(self):
        def change(lid):
            lid["underside_above_board"] = 19.5
        self.assertFailsWith(variant(edit=rewrite_lid(change)), "FAIL E13 ",
                             "lid underside at 19.5 mm, the frame's seat at 19.00 mm")

    # E14 -------------------------------------------------------------------------------------
    def test_no_seam_gap(self):
        self.assertFailsWith(variant("seam_gap=0"), "FAIL E14 ", "smallest gap 0.000 mm, want 0.2 mm")

    def test_ridge_binds_in_the_chamfer(self):
        self.assertFailsWith(variant("lip_clear=0.05"), "FAIL E14 ", "smallest gap 0.035 mm")

    def test_chamfer_cuts_through_the_wall(self):
        self.assertFailsWith(variant("lip_clear=1.2"), "FAIL E14 Frame: ",
                             "of its outer 0.3 mm at the seam is plastic")

    def test_corners_rounder_than_the_document(self):
        self.assertFailsWith(variant("corner_r=6"), "FAIL E14 Tray: ", "FAIL E14 Frame: ",
                             "of its outer 0.3 mm at the seam is plastic")

    # E17 -------------------------------------------------------------------------------------
    def test_opening_narrower_than_the_clamp_needs(self):
        rc, out = variant("clamp_clear=0.2")
        self.assertFailsWith((rc, out), "FAIL E17 J5: ", "within 0.75 mm of a clamp 16.5 mm wide",
                             "clamp_opening_w 18.0 (built: 16.90)")
        self.assertIn("PASS E17 J5: the SWD land is at the back edge", out)

    def test_floor_under_the_lower_jaw(self):
        # 6.5 and not less: the generator refuses a floor opening too short for the cover's foot
        rc, out = variant("clamp_reach=6.5")
        self.assertFailsWith((rc, out), "FAIL E17 J5: ", "mm3 of the tray and 0.00 mm3 of the frame")

    def test_window_lower_than_the_upper_jaw(self):
        rc, out = variant("clamp_up=4")
        self.assertFailsWith((rc, out), "FAIL E17 J5: 0.00 mm3 of the tray and ",
                             "clamp_bridge_h 8.6 (built: 16.60)")

    def test_no_wall_left_above_the_opening(self):
        rc, out = variant("clamp_up=17")
        self.assertFailsWith((rc, out), "FAIL E17 Frame: ",
                             "of the 3 mm of wall above the opening is plastic, want 100")
        self.assertIn("PASS E17 J5: a clamp 16.5 mm wide reaches", out)

    def test_opening_runs_into_a_port_pocket(self):
        rc, out = variant("clamp_w=36")
        self.assertFailsWith((rc, out), "FAIL E17 Tray: ", "FAIL E17 Frame: ",
                             "of the 1 mm of wall at the opening's left side is plastic, want 100")

    def test_swd_land_moved_along_the_edge(self):
        rc, out = variant(interface=moved("J5", dx=2.0))
        self.assertFailsWith((rc, out), "FAIL E17 J5: ", "mm3 of the frame within 0.75 mm of a clamp")

    def test_swd_land_not_at_the_edge(self):
        self.assertFailsWith(variant(interface=moved("J5", dy=-3.0)),
                             "FAIL E17 J5: its courtyard x 39.195 .. 49.455 ends 3.45 mm from the "
                             "back edge")

    def test_seam_open_beside_the_opening(self):
        # the seam's exemption is the document's opening and no wider
        self.assertFailsWith(variant("clamp_clear=2.5"), "FAIL E14 Tray: ", "FAIL E14 Frame: ")

    # E18 -------------------------------------------------------------------------------------
    def test_cover_without_clearance(self):
        self.assertFailsWith(variant("cover_clear=0"), "FAIL E18 Cover: at rest it shares mm3 with ",
                             "smallest gap 0.000 mm, want >= 0.14 mm")

    def test_cover_loose_in_the_wall(self):
        self.assertFailsWith(variant("cover_clear=0.7"), "FAIL E18 Cover: ",
                             "gaps left 0.70, right 0.70, top 0.70, bottom 0.60 mm (want 0.05 .. 0.6)")

    def test_cover_proud_of_the_wall(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Cover", shifted(dy=0.5))),
                             "FAIL E03 Cover: ", "mm3 outside the outline and its 2 mm corners",
                             "outer face at y 74.90, wall at 74.40")

    def test_cover_shorter_than_the_opening(self):
        cut = reshaped(lambda man: man ^ S.box(0.0, 0.0, -20.0, 100.0, 100.0, 10.8))
        self.assertFailsWith(variant(edit=rewrite_stl("Cover", cut)), "FAIL E18 Cover: ", "top 1.20",
                             "raised 0.5 mm it shares 0.00 mm3 with the frame (want > 0.05)")

    def test_detents_that_do_not_reach_the_floor(self):
        self.assertFailsWith(variant("cover_catch=0.2"), "FAIL E18 Cover: pulled 1.0 mm outwards "
                             "it meets the tray by left 0.00, right 0.00 mm3")

    def test_no_room_for_a_finger_to_bend(self):
        rc, out = variant("cover_slit=0.2")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E18 Cover: left [1-9]\.\d\d, right [1-9]\.\d\d mm3 in the "
                              r"0\.50 mm a finger bends into \(want 0\)")

    def test_finger_thinner_than_the_document_says(self):
        rc, out = variant("cover_arm_w=0.3")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E18 Cover: .* fingers left \d\d\.\d\d, right \d\d\.\d\d "
                              r"% plastic \(want 100\)")

    def test_finger_bent_too_far(self):
        self.assertFailsWith(variant("cover_catch=1.2"), "FAIL E18 Cover: ",
                             "strain 2.08 %, want <= 1.5")

    def test_cover_without_its_wedge(self):
        self.assertFailsWith(variant("cover_ledge=0"), "FAIL E18 Cover: ",
                             "dropped 0.7 mm it shares 0.000 mm3 with the board (want > 0.02")

    def test_wedge_that_a_push_drives_into_the_board(self):
        rc, out = variant("cover_ledge_gap=0.1")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E18 Cover: pushed in 0\.3 mm it shares mm3 with tray \d+\.\d\d, "
                              r"frame 0\.00, board 0\.[0-9]*[1-9]")

    def test_cover_that_hangs_below_the_tray(self):
        self.assertFailsWith(variant("cover_lift=0.4"), "FAIL E18 Cover: ",
                             "hanging on the board its underside is 0.00 mm above the tray's")

    def test_foot_that_does_not_reach_the_floors_end(self):
        cut = reshaped(lambda man: man ^ S.box(0.0, 65.4, -20.0, 100.0, 100.0, 30.0))
        self.assertFailsWith(variant(edit=rewrite_stl("Cover", cut)),
                             "FAIL E18 Cover: pushed in 0.3 mm it shares mm3 with tray 0.00")

    def test_no_slot_for_a_fingernail(self):
        rc, out = variant("cover_pull_l=0.5")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E18 Cover: .*; [1-9]\d*\.\d\d mm3 in the fingernail's slot "
                              r"of 8 x 3 mm \(want 0\)")

    def test_foot_that_leaves_the_floor_open(self):
        self.assertFailsWith(variant("cover_pull_l=5"), "FAIL E18 Cover: its foot closes 60.6 % of "
                             "the floor's opening (want >= 65)")

    def test_cover_that_cannot_leave_through_the_wall(self):
        # a lump on the inner face, above the opening's top: free at rest, held by the frame
        lump = reshaped(lambda man: man + S.box(40.0, 71.6, 11.0, 49.0, 72.6, 11.6)
                        + S.box(40.0, 71.6, 11.0, 49.0, 72.2, 14.0))
        rc, out = variant(edit=rewrite_stl("Cover", lump))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E18 Cover: without its detents it meets, on its way out, mm3 "
                              r"of tray 0\.00, frame [1-9]\d*\.\d\d")
        self.assertIn("PASS E18 Cover: at rest it touches nothing", out)

    def test_lead_over_the_covers_foot(self):
        # a foot 2 mm too thick, under a through-hole that the real board does not have there
        def hole(board):
            board["holes"].append({"ref": "TPX", "pad": "1", "x": 44.5, "y": 70.4,
                                   "drill": [1.0, 1.0], "plated": True})
        lump = reshaped(lambda man: man + S.box(42.0, 70.0, -5.6, 47.0, 71.0, -3.1))
        rc, out = variant(edit=rewrite_stl("Cover", lump), interface=as_json(hole))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E06 TPX pad '1' at \(44\.5, 70\.4\): \d+\.\d\d mm3 of the "
                              r"Cover within 2\.5 mm below its hole")

    # E19 -------------------------------------------------------------------------------------
    def test_lid_tight_in_its_pocket(self):
        rc, out = variant("rim_clear=0.1")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E19 [1-9]\d*\.\d\d mm3 of the frame within 0\.3 mm of the "
                              r"lid's edge or over the lid \(want 0\); the lid's edge is 0\.10 mm "
                              r"from the wall, want 0\.3 \.\. 0\.6 mm")

    def test_lid_loose_in_its_pocket(self):
        self.assertFailsWith(variant("rim_clear=0.9"),
                             "FAIL E19 0.00 mm3 of the frame within 0.3 mm of the lid's edge or "
                             "over the lid (want 0); the lid's edge is 0.90 mm from the wall, "
                             "want 0.3 .. 0.6 mm")

    def test_lid_thinner_than_the_wall_is_high(self):
        def change(lid):
            lid["thickness"] = 1.0
        self.assertFailsWith(variant(edit=rewrite_lid(change)),
                             "FAIL E19 the wall round the lid ends 20.60 mm above the board and "
                             "the lid's top face is at 20.00 mm: the wall stands 0.60 mm proud")

    def test_lid_thicker_than_the_wall_is_high(self):
        def change(lid):
            lid["thickness"] = 2.0
        self.assertFailsWith(variant(edit=rewrite_lid(change)),
                             "FAIL E19 the wall round the lid ends 20.60 mm above the board and "
                             "the lid's top face is at 21.00 mm: the lid stands 0.40 mm proud")

    def test_frame_without_the_wall_round_the_lid(self):
        # the frame as it was until Rev0.4: it ends at the lid's seat
        cut = reshaped(lambda man: man ^ S.box(-10.0, -10.0, -1.0, 110.0, 82.0, 19.0))
        self.assertFailsWith(variant(edit=rewrite_stl("Frame", cut)),
                             "FAIL E03 Frame: box",
                             "FAIL E19 the wall round the lid ends 19.00 mm above the board and "
                             "the lid's top face is at 20.60 mm: the lid stands 1.60 mm proud",
                             "the lid's edge is 3.00 mm from the wall, want 0.3 .. 0.6 mm",
                             "FAIL E19 inf mm3 of the wall round the lid is missing")

    def test_frame_that_laps_over_the_lid(self):
        # a tab on the front wall's top that reaches 1.0 mm over the lid, 0.1 mm above it:
        # the lid lies free and cannot be lifted out
        tab = reshaped(lambda man: man + S.box(40.0, -1.6, 20.3, 46.0, -0.5, 21.2)
                       + S.box(40.0, -1.6, 20.7, 46.0, 1.0, 21.2))
        rc, out = variant(edit=rewrite_stl("Frame", tab))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E19 [1-9]\d*\.\d\d mm3 of the frame within 0\.3 mm of the "
                              r"lid's edge or over the lid \(want 0\)")
        self.assertIn("PASS E13 the lid has the board's outline and lies on its seat", out)

    def test_notch_in_the_wall_round_the_lid(self):
        # a slot 1 mm wide through the front wall, from 0.3 mm above the seat to the top
        notch = reshaped(lambda man: man - S.box(60.0, -3.0, 19.3, 61.0, -0.2, 21.0))
        rc, out = variant(edit=rewrite_stl("Frame", notch))
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E19 [1-9]\.\d\d mm3 of the wall round the lid is missing "
                              r"between the gap and the outline")
        self.assertIn("PASS E19 the wall round the lid ends flush with the lid's top face", out)

    # E15 -------------------------------------------------------------------------------------
    def test_seat_wider_than_the_document_says(self):
        rc, out = variant("lid_overlap=1.5")
        self.assertEqual(rc, 1, out)
        self.assertRegex(out, r"FAIL E15 derived figures differ: frame_support_area 6\.28 "
                              r"\(built: [78]\.\d\d\)")

    def test_cover_figure_edited(self):
        self.assertFailsWith(variant(doc=table_value("derived", "cover_engage", "0.50")),
                             "FAIL E15 derived figures differ: cover_engage 0.5 (built: 0.40)")

    def test_derived_figure_edited(self):
        rc, out = variant(doc=table_value("derived", "outer_z", "27.00"))
        self.assertFailsWith((rc, out), "FAIL E15 derived figures differ: outer_z 27.0 (built: 27.70)")
        self.assertIn("PASS E01 built from the document's tables as they stand", out)
        self.assertEqual(out.count("FAIL"), 1, out)

    def test_derived_figure_that_nothing_measures(self):
        row = "| `lid_area` | 7200.00 | mm2 | Not measured by the checker. |\n"
        self.assertFailsWith(
            variant(doc=lambda t: t.replace("<!-- derived:end -->", row + "<!-- derived:end -->")),
            "FAIL E15 derived figures differ: lid_area is not measured")

    def test_walls_farther_out_than_the_document_says(self):
        rc, out = variant("gap=0.6")
        self.assertFailsWith((rc, out), "FAIL E15 derived figures differ: ",
                             "face_inset 1.34 (built: 1.54)")

    def test_receptacle_moved_on_the_board(self):
        self.assertFailsWith(variant(interface=moved("J3", dx=-0.6)),
                             "FAIL E15 derived figures differ: ",
                             "port_to_screw_max 14.03 (built: 14.63)")

    def test_no_derived_table(self):
        self.assertFailsWith(variant(doc=lambda t: t.replace("<!-- derived:begin -->", "")),
                             "FAIL E15 no derived table in the enclosure document")

    # E16 -------------------------------------------------------------------------------------
    def test_picture_of_another_build(self):
        here = spec.source_tag(spec.ASSEMBLY / spec.MANIFEST)      # the repository's build
        self.assertFailsWith(variant("plunger_proud=1.2", pictures=lambda out, pic: picture(pic, here)),
                             "FAIL E16 1 of 1 pictures were not drawn from these files "
                             "(UsbPowerHub_Enclosure_Rev0.5_Assembled.png): run render_enclosure.py")

    def test_picture_that_names_no_build(self):
        def pictures(out, pic):
            (pic / f"{spec.PREFIX}Open.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            picture(pic, spec.source_tag(out / spec.MANIFEST))
        self.assertFailsWith(variant(pictures=pictures),
                             "FAIL E16 1 of 2 pictures were not drawn from these files "
                             "(UsbPowerHub_Enclosure_Rev0.5_Open.png)")

    def test_no_pictures(self):
        self.assertFailsWith(variant(pictures=lambda out, pic: None),
                             "FAIL E16 no pictures in reports: run render_enclosure.py")

    def test_pictures_not_given_is_said(self):
        rc, out = variant()
        self.assertEqual(rc, 0, out)
        self.assertIn("SKIP E16 no pictures given for this directory (--pictures)", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
