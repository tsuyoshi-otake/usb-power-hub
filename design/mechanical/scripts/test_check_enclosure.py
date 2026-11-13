"""Negative tests for check_enclosure.py (CLAUDE.md 8: a checker never observed failing is
not evidence).

Run with the CAD venv's Python from the repository root:

    ~/tmp/cadvenv/Scripts/python.exe -I -B design/mechanical/scripts/test_check_enclosure.py

Each test builds the enclosure into a temporary directory, with one parameter overridden
(make_enclosure.py --set) or with one file corrupted afterwards, and runs check_enclosure.py
on it in a new process. The unchanged build must pass; every corruption must fail and be
named in the output. The repository's files are never modified. A test that edits a built
file also corrects its SHA-256 in the manifest, so that only the check under test fails.
The whole run takes about 1 min.
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
                             "FAIL E01 no manifest UsbPowerHub_Enclosure_Rev0.1_Manifest.json")

    def test_piece_not_in_the_manifest(self):
        def edit(out):
            path, manifest = manifest_of(out)
            manifest["pieces"] = manifest["pieces"][:2]
            save_manifest(path, manifest)
        self.assertFailsWith(variant(edit=edit),
                             "FAIL E01 pieces ['Tray', 'Frame'], want Tray, Frame, Plunger",
                             "enclosure check: stopped")

    def test_stl_edited_after_the_build(self):
        def edit(out):
            f = out / f"{spec.PREFIX}Tray.stl"
            raw = bytearray(f.read_bytes())
            raw[200] ^= 1
            f.write_bytes(bytes(raw))
        self.assertFailsWith(variant(edit=edit),
                             "FAIL E01 UsbPowerHub_Enclosure_Rev0.1_Tray.stl: SHA-256 differs")

    def test_piece_missing(self):
        self.assertFailsWith(variant(edit=lambda out: (out / f"{spec.PREFIX}Plunger.stl").unlink()),
                             "FAIL E01 UsbPowerHub_Enclosure_Rev0.1_Plunger.stl: missing")

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

    def test_piece_above_the_bed(self):
        self.assertFailsWith(variant(edit=rewrite_stl("Tray", lifted)),
                             "FAIL E04 Tray: lowest point z 1.000")

    # E05 -------------------------------------------------------------------------------------
    def test_cavity_lower_than_the_tallest_part(self):
        self.assertFailsWith(variant("cavity_h=18.0"), "FAIL E05 F1: ", "of the Lid inside its envelope")

    def test_tower_on_a_switch(self):
        self.assertFailsWith(variant("ui_bottom=1.0"), "FAIL E05 SW1: ",
                             "of the Frame inside its envelope")

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

    # E15 -------------------------------------------------------------------------------------
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
        self.assertRegex(out, r"swd_wall_clearance 1\.16 \(built: 1\.3[56]\)")      # 1.355 exactly

    def test_receptacle_moved_on_the_board(self):
        self.assertFailsWith(variant(interface=moved("J3", dx=-0.6)),
                             "FAIL E15 derived figures differ: ",
                             "port_to_screw_max 45.21 (built: 45.81)")

    def test_swd_footprint_nearer_the_wall(self):
        self.assertFailsWith(variant(interface=moved("J5", dy=0.455)),
                             "FAIL E15 derived figures differ: swd_wall_clearance 1.16 (built: 0.70)")

    def test_no_derived_table(self):
        self.assertFailsWith(variant(doc=lambda t: t.replace("<!-- derived:begin -->", "")),
                             "FAIL E15 no derived table in the enclosure document")

    # E16 -------------------------------------------------------------------------------------
    def test_picture_of_another_build(self):
        here = spec.source_tag(spec.ASSEMBLY / spec.MANIFEST)      # the repository's build
        self.assertFailsWith(variant("plunger_proud=1.2", pictures=lambda out, pic: picture(pic, here)),
                             "FAIL E16 1 of 1 pictures were not drawn from these files "
                             "(UsbPowerHub_Enclosure_Rev0.1_Assembled.png): run render_enclosure.py")

    def test_picture_that_names_no_build(self):
        def pictures(out, pic):
            (pic / f"{spec.PREFIX}Open.png").write_bytes(b"\x89PNG\r\n\x1a\n")
            picture(pic, spec.source_tag(out / spec.MANIFEST))
        self.assertFailsWith(variant(pictures=pictures),
                             "FAIL E16 1 of 2 pictures were not drawn from these files "
                             "(UsbPowerHub_Enclosure_Rev0.1_Open.png)")

    def test_no_pictures(self):
        self.assertFailsWith(variant(pictures=lambda out, pic: None),
                             "FAIL E16 no pictures in reports: run render_enclosure.py")

    def test_pictures_not_given_is_said(self):
        rc, out = variant()
        self.assertEqual(rc, 0, out)
        self.assertIn("SKIP E16 no pictures given for this directory (--pictures)", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
