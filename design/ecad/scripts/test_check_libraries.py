"""Negative tests for check_libraries.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_libraries.py has written the
libraries:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_libraries.py

Each test copies design/ecad/libraries and the project files of design/ecad/source into a
temporary directory, corrupts one thing and runs `check_libraries.py LIBDIR SRCDIR` in a new
process. The unchanged copy must pass; every corruption must fail and be named in the output.
The repository's files are never modified. Each run includes the DRC, about 5 s.
"""
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CHECK = HERE / "check_libraries.py"
LIBDIR = HERE.parent / "libraries"
SRCDIR = HERE.parent / "source"
NICK = "usb-power-hub"
SRC_FILES = (f"{NICK}.kicad_pcb", f"{NICK}.kicad_pro", f"{NICK}.kicad_dru", "fp-lib-table", "sym-lib-table")

_spec = importlib.util.spec_from_file_location("sexpr", HERE / "sexpr.py")
sx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sx)


def run_check(corrupt=None):
    """Copy, corrupt, check. Returns (exit status, output)."""
    with tempfile.TemporaryDirectory(prefix="libtest-") as tmp:
        t = pathlib.Path(tmp)
        lib, src = t / "libraries", t / "source"
        shutil.copytree(LIBDIR, lib)
        src.mkdir()
        for name in SRC_FILES:
            shutil.copyfile(SRCDIR / name, src / name)
        if corrupt:
            corrupt(lib, src)
        out = subprocess.run([sys.executable, "-I", "-B", str(CHECK), str(lib), str(src)],
                             capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=600)
        return out.returncode, out.stdout + out.stderr


def sub(path, pattern, repl, flags=0):
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    assert n == 1 and new != text, f"the corruption of {path.name} matched nothing"
    path.write_text(new, encoding="utf-8", newline="\n")


def fp_path(lib, name):
    return lib / f"{NICK}.pretty" / f"{name}.kicad_mod"


def edit_fp(lib, name, fn):
    """Load a footprint as S-expressions, let fn change it in place, write it back."""
    p = fp_path(lib, name)
    tree = sx.loads(p.read_text(encoding="utf-8"))
    before = sx.dumps(tree)
    fn(tree)
    after = sx.dumps(tree)
    assert after != before, f"the corruption of {name} changed nothing"
    p.write_text(after + "\n", encoding="utf-8", newline="\n")


def silk(tree):
    return [n for n in tree if isinstance(n, list) and n and
            n[0] in ("fp_line", "fp_arc", "fp_circle", "fp_rect", "fp_poly") and sx.first(n, "layer")[1] == "F.SilkS"]


def pad(tree, num):
    return next(n for n in sx.find(tree, "pad") if n[1] == num)


def symbol_block(text, name):
    start = text.index(f'\n\t(symbol "{name}"\n')
    end = text.find('\n\t(symbol "', start + 1)
    return start, (end if end > 0 else len(text))


def edit_symbol(lib, name, fn):
    p = lib / f"{NICK}.kicad_sym"
    text = p.read_text(encoding="utf-8")
    a, b = symbol_block(text, name)
    new = fn(text[a:b])
    assert new != text[a:b], f"the corruption of symbol {name} changed nothing"
    p.write_text(text[:a] + new + text[b:], encoding="utf-8", newline="\n")


def edit_register(lib, fn):
    p = lib / "library.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    fn({part["id"]: part for part in data["parts"]})
    p.write_text(json.dumps(data, indent=1), encoding="utf-8", newline="\n")


RP2040 = "RP2040_QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm"
CH335F = "CH335F_QFN-28-1EP_4x4mm_P0.4mm_EP2.7x2.7mm"
R_H = "R_Shunt_KOA_TSL1_6332Metric_Kelvin"
R_M = "R_Shunt_Axial_MFU_L6.0mm_D2.3mm_P10.16mm_Kelvin"
R_L = "R_Shunt_0805_2012Metric_Kelvin"
MAU = "Converter_DCDC_Minmax_MAU104_SIP"
USBC = "USB_C_Receptacle_SHOUHAN_TYPE-C-16PIN-2MD-073"
USBC_ID = "TYPE-C-16PIN-2MD-073"
TC2030 = "Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical"


class CheckLibrariesFails(unittest.TestCase):
    def assertFailsWith(self, result, *needles):
        status, out = result
        self.assertEqual(status, 1, f"the check passed a corrupted copy:\n{out[-3000:]}")
        for needle in needles:
            self.assertIn(needle, out, f"the failure does not name {needle!r}:\n{out[-3000:]}")

    def test_unchanged_copy_passes(self):
        status, out = run_check()
        self.assertEqual(status, 0, out[-3000:])
        self.assertIn("0 failed: PASS", out)

    def test_qfn_pad_width(self):
        def c(lib, src):
            edit_fp(lib, RP2040, lambda t: pad(t, "1").__setitem__(5, ["size", 0.875, 0.25]))
        self.assertFailsWith(run_check(c), f"FAIL RP2040 / {RP2040}: pad '1'", "width 0.2500")

    def test_qfn_pad_short_of_tip(self):
        def c(lib, src):
            edit_fp(lib, CH335F, lambda t: sx.first(pad(t, "1"), "at").__setitem__(1, -1.55))
        self.assertFailsWith(run_check(c), "short of the maximum tip", "FAIL DRC")

    def test_epad_too_large(self):
        def c(lib, src):
            edit_fp(lib, CH335F, lambda t: pad(t, "0").__setitem__(5, ["size", 3.1, 3.1]))
        self.assertFailsWith(run_check(c), "ePad pad '0'", "FAIL DRC")

    def test_symbol_pin_renamed(self):
        def c(lib, src):
            edit_symbol(lib, "CH335F", lambda b: b.replace('(name "DP1"', '(name "DP5"'))
        self.assertFailsWith(run_check(c), "FAIL CH335F: pin 7 is 'DP5'")

    def test_tl431_pin_order(self):
        """KiCad's TL431DBZ (1 K, 2 REF) in place of TL432DBZ (1 REF, 2 K): CJ431 is 1 REF."""
        def c(lib, src):
            edit_symbol(lib, "CJ431", lambda b: b.replace('(number "1"', '(number "@"')
                        .replace('(number "2"', '(number "1"').replace('(number "@"', '(number "2"'))
        self.assertFailsWith(run_check(c), "FAIL CJ431: pin 1 is 'K'", "FAIL CJ431: pin 2 is 'REF'")

    def test_register_package_changed(self):
        def c(lib, src):
            edit_register(lib, lambda parts: parts["OP07CDR"]["land"].__setitem__("tip_span", [7.0, 7.2]))
        self.assertFailsWith(run_check(c), "FAIL OP07CDR / SOIC-8_3.9x4.9mm_P1.27mm", "short of the maximum tip")

    def test_stock_copy_altered(self):
        def c(lib, src):
            edit_fp(lib, TC2030, lambda t: t.remove(pad(t, "6")))
        self.assertFailsWith(run_check(c), f"differs from KiCad's {TC2030} outside its silkscreen",
                             "are not the symbol's pins")

    def test_stock_copy_with_kicad_crlf(self):
        # KiCad's Windows install ships CRLF; the repository stores LF (.gitattributes), so a
        # raw copy of KiCad's file is not what a checkout holds.
        def c(lib, src):
            p = fp_path(lib, "SOT-23")
            data = p.read_bytes()
            assert b"\r" not in data, "the copy already has CR bytes"
            p.write_bytes(data.replace(b"\n", b"\r\n"))
        self.assertFailsWith(run_check(c), "FAIL line endings: SOT-23.kicad_mod has CR bytes")

    # ---- silkscreen (P5) ------------------------------------------------------------------------
    def test_silk_stroke_thin(self):
        def c(lib, src):
            def f(t):
                sx.first(sx.first(silk(t)[0], "stroke"), "width")[1] = 0.12
            edit_fp(lib, CH335F, f)
        self.assertFailsWith(run_check(c), f"FAIL CH335F / {CH335F}: F.SilkS", "stroke 0.120 mm < 0.15")

    def test_silk_on_pad(self):
        def c(lib, src):
            def f(t):
                at = sx.first(pad(t, "1"), "at")
                x, y = float(at[1]), float(at[2])
                line = next(n for n in silk(t) if n[0] == "fp_line")
                sx.first(line, "start")[1:3] = [round(x - 0.3, 3), y]
                sx.first(line, "end")[1:3] = [round(x + 0.3, 3), y]
            edit_fp(lib, CH335F, f)
        self.assertFailsWith(run_check(c), f"FAIL CH335F / {CH335F}: F.SilkS", "within 0.15 mm of pad '1'")

    def test_stock_silk_reshaped(self):
        def c(lib, src):
            def f(t):
                sx.first(silk(t)[0], "start")[1] = 0.5
            edit_fp(lib, "SOT-23", f)
        self.assertFailsWith(run_check(c), "its F.SilkS shapes are not KiCad's SOT-23 shapes")

    def test_stock_silk_narrower_than_kicad(self):
        def c(lib, src):
            def f(t):
                sx.first(sx.first(silk(t)[0], "stroke"), "width")[1] = 0.1
            edit_fp(lib, "SOT-23", f)
        self.assertFailsWith(run_check(c), "its F.SilkS shapes are not KiCad's SOT-23 shapes",
                             "stroke 0.100 mm < 0.15")

    def test_silk_drop_on_polar_part(self):
        def c(lib, src):
            edit_register(lib, lambda parts: parts["2N7002"]["footprint"].__setitem__("silk_drop", ["SOT-23"]))
        self.assertFailsWith(run_check(c), "FAIL 2N7002 / SOT-23: silk_drop on a part whose pins are not all",
                             "FAIL 2N7002 / SOT-23: silk_drop footprint still has silkscreen")

    def test_silk_drop_stale(self):
        def c(lib, src):
            edit_register(lib, lambda parts: parts["R"]["footprint"]["silk_drop"].append("R_1206_3216Metric"))
        self.assertFailsWith(run_check(c),
                             "FAIL R: silk_drop names footprints the part does not use: ['R_1206_3216Metric']")

    def test_silk_drop_entry_removed(self):
        """C_0402's silkscreen is left out of the file; without its silk_drop entry that is a
        stock copy whose silk shapes are missing."""
        def c(lib, src):
            edit_register(lib, lambda parts: parts["C"]["footprint"].__setitem__("silk_drop", []))
        self.assertFailsWith(run_check(c), "FAIL C / C_0402_1005Metric: its F.SilkS shapes are not KiCad's")

    def test_footprint_missing(self):
        def c(lib, src):
            fp_path(lib, "D_SMB").unlink()
        self.assertFailsWith(run_check(c), "['D_SMB'] missing")

    def test_symbol_orphan(self):
        def c(lib, src):
            edit_symbol(lib, "Fiducial", lambda b: b.replace('(symbol "Fiducial', '(symbol "Fiducial2', 1)
                        .replace('(symbol "Fiducial_', '(symbol "Fiducial2_'))
        self.assertFailsWith(run_check(c), "['Fiducial2'] extra", "['Fiducial'] missing")

    def test_net_tie_removed(self):
        def c(lib, src):
            edit_fp(lib, R_L, lambda t: t.remove(sx.first(t, "net_tie_pad_groups")))
        self.assertFailsWith(run_check(c), "net tie groups []", "FAIL DRC")

    def test_tie_strip_to_wrong_pad(self):
        def strip(t):
            seg = [n for n in sx.find(t, "fp_line") if sx.first(n, "layer")[1] == "F.Cu"][0]
            sx.first(seg, "end")[1] = 0.9125        # pad 1's strip now ends in sense pad 3
        self.assertFailsWith(run_check(lambda lib, src: edit_fp(lib, R_L, strip)),
                             "no single F.Cu strip from force pad 1 into sense pad 2", "FAIL DRC")

    def test_sense_pad_shorts_force_pad(self):
        """Only the DRC sees this one: the sense pad still overlaps its electrode."""
        def c(lib, src):
            edit_fp(lib, R_H, lambda t: sx.first(pad(t, "2"), "at").__setitem__(2, -0.6))
        status, out = run_check(c)
        self.assertFailsWith((status, out), "FAIL DRC")
        self.assertNotIn(f"FAIL TSL1TTER100D / {R_H}", out)

    def test_hand_part_paste(self):
        def c(lib, src):
            edit_fp(lib, R_H, lambda t: sx.first(pad(t, "2"), "layers").append("F.Paste"))
        self.assertFailsWith(run_check(c), "a pad has paste; the land has none")

    def test_sip_drill(self):
        def c(lib, src):
            edit_fp(lib, MAU, lambda t: sx.first(pad(t, "2"), "drill").__setitem__(1, 0.6))
        self.assertFailsWith(run_check(c), "drill 0.6 outside 0.8..1.2")

    def test_receptacle_pad_renumbered(self):
        def c(lib, src):
            edit_fp(lib, USBC, lambda t: pad(t, "A6").__setitem__(1, "A9"))
        self.assertFailsWith(run_check(c), "are not the symbol's pins", "no pad 'A6' at [-0.25, -3.67]")

    def test_receptacle_mirrored(self):
        # The land seen from below: every pad and hole at -x. D+ and D- would swap.
        def mirror(t):
            for n in sx.find(t, "pad"):
                at = sx.first(n, "at")
                at[1] = -at[1]
        self.assertFailsWith(run_check(lambda lib, src: edit_fp(lib, USBC, mirror)),
                             "no pad 'A1' at [-3.2, -3.6875]", "no pad 'B6' at [0.75, -3.67]")

    def test_receptacle_slot_missing(self):
        def drop(t):
            t.remove(next(n for n in sx.find(t, "pad") if n[1] == "S1" and sx.first(n, "at")[2] < -3))
        self.assertFailsWith(run_check(lambda lib, src: edit_fp(lib, USBC, drop)),
                             "3 plated holes, the land has 4 plated slots", "no plated slot 'S1' at [-4.32, -3.105]")

    def test_receptacle_slot_as_round_hole(self):
        def round_hole(t):
            p = next(n for n in sx.find(t, "pad") if n[1] == "S1")
            p[p.index(sx.first(p, "drill"))] = ["drill", 0.6]
        self.assertFailsWith(run_check(lambda lib, src: edit_fp(lib, USBC, round_hole)), "is not [0.6, 1.4]")

    def test_receptacle_peg_015_from_pad(self):
        # A1's near edge 0.015 closer than the drawing's: 0.15 mm from the peg hole. The register's
        # land moves with it, so the pad's own position and size still match. KiCad's DRC does not
        # compare a footprint's own pads with its own holes (tried 2026-11-12: no violation at
        # 0.15 mm, with or without the project's rule), so only npth_copper_min can fail here.
        def fp(t):
            a1 = pad(t, "A1")
            sx.first(a1, "at")[2] = -3.6625
            sx.first(a1, "size")[2] = 1.165
        def reg(parts):
            w = next(x for x in parts[USBC_ID]["land"]["pads"] if x["n"] == "A1")
            w["at"], w["size"] = [-3.2, -3.6625], [0.6, 1.165]
        def c(lib, src):
            edit_fp(lib, USBC, fp)
            edit_register(lib, reg)
        status, out = run_check(c)
        self.assertFailsWith((status, out), "mm from pad 'A1'", "under 0.2 (land.npth_copper_min)")
        self.assertNotIn("no pad 'A1'", out)
        self.assertNotIn("FAIL DRC", out)

    def test_table_uri(self):
        def c(lib, src):
            sub(src / "fp-lib-table", r"/\.\./libraries/", "/../library/")
        self.assertFailsWith(run_check(c), "fp-lib-table uri")


if __name__ == "__main__":
    unittest.main(verbosity=2)
