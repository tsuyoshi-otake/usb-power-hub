"""Negative tests for check_schematic.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_schematic.py has written the
schematic:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_schematic.py

Each test copies design/ecad/source and design/ecad/libraries into a temporary directory
(the sym-lib-table finds the library at ../libraries), copies the netlist document, the
circuit document and requirements/parts.md beside them, corrupts one thing and runs
check_schematic.py on the copies in a new process. The unchanged copy must pass; every
corruption must fail and be named in the output. The repository's files are never modified.
Each run includes ERC and a netlist export, about 2 s.
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
CHECK = HERE / "check_schematic.py"
ECAD = HERE.parent
DOCS = {"doc": ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.4_netlist.md",
        "circuit": ROOT / "design" / "circuit" / "CIRCUIT_DESIGN_Rev0.4.md",
        "parts": ROOT / "requirements" / "parts.md"}

_spec = importlib.util.spec_from_file_location("sexpr", HERE / "sexpr.py")
sx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sx)


def run_check(sheet=None, edit_sheet=None, edit_pro=None, **edit_text):
    """Copy, corrupt, check. Returns (exit status, output).

    sheet + edit_sheet(tree): edit that sheet's parsed S-expression in place.
    edit_pro(text), doc / circuit / parts = edit(text): return the corrupted text.
    """
    with tempfile.TemporaryDirectory(prefix="schtest-") as tmp:
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
        if edit_sheet:
            p = src / f"{sheet}.kicad_sch"
            tree = sx.loads(p.read_text(encoding="utf-8"))
            before = sx.dumps(tree)
            edit_sheet(tree)
            assert sx.dumps(tree) != before, "the sheet corruption changed nothing"
            p.write_text(sx.dumps(tree) + "\n", encoding="utf-8", newline="\n")
        if edit_pro:
            p = src / "usb-power-hub.kicad_pro"
            text = p.read_text(encoding="utf-8")
            new = edit_pro(text)
            assert new != text, "the project corruption changed nothing"
            p.write_text(new, encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--src", str(src),
                            "--lib", str(t / "libraries"), *args],
                           capture_output=True, text=True, encoding="utf-8", timeout=300)
        return r.returncode, r.stdout + r.stderr


def prop(node, name):
    return next(p for p in sx.find(node, "property") if p[1] == name)


def symbol(tree, ref):
    return next(s for s in sx.find(tree, "symbol") if prop(s, "Reference")[2] == ref)


def drop(tree, node):
    tree[:] = [x for x in tree if x is not node]


def first_label(tree, net):
    return next(g for g in sx.find(tree, "global_label") if g[1] == net)


def sub_once(pattern, repl):
    def edit(text):
        new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
        assert n == 1, pattern
        return new
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

    # ---- the schematic ----------------------------------------------------------------------
    def test_label_deleted(self):
        """A pin left on its stub alone: ERC sees the dangling wire, the netlist the lost pin."""
        def edit(tree):
            drop(tree, first_label(tree, "CC1_J1"))
        self.assertFailsWith(run_check("power", edit), "FAIL ERC", "the document says 'CC1_J1'")

    def test_label_renamed(self):
        def edit(tree):
            first_label(tree, "EN_G_A")[1] = "EN_G_Z"
        self.assertFailsWith(run_check("channel_a", edit), "exported net is not a document net",
                             "EN_G_Z")

    def test_power_flag_removed(self):
        def edit(tree):
            flag = next(s for s in sx.find(tree, "symbol")
                        if sx.first(s, "lib_id")[1] == "usb-power-hub:PWR_FLAG")
            drop(tree, flag)
        self.assertFailsWith(run_check("power", edit), "power_pin_not_driven")

    def test_value_changed(self):
        def edit(tree):
            prop(symbol(tree, "R1"), "Value")[2] = "5.2k"
        self.assertFailsWith(run_check("power", edit), "FAIL R1: Value '5.2k'")

    def test_footprint_changed(self):
        def edit(tree):
            prop(symbol(tree, "R1"), "Footprint")[2] = "usb-power-hub:R_0603_1608Metric"
        self.assertFailsWith(run_check("power", edit), "FAIL R1: footprint")

    def test_lcsc_changed(self):
        def edit(tree):
            prop(symbol(tree, "R1"), "LCSC")[2] = "C25904"
        self.assertFailsWith(run_check("power", edit), "FAIL R1: LCSC 'C25904'")

    def test_bom_exclusion_dropped(self):
        def edit(tree):
            j5 = symbol(tree, "J5")
            sx.first(j5, "in_bom")[1] = sx.Sym("yes")
        self.assertFailsWith(run_check("mcu", edit), "FAIL J5: excluded from BOM: False")

    def test_component_deleted(self):
        def edit(tree):
            drop(tree, symbol(tree, "C101"))
        self.assertFailsWith(run_check("channel_a", edit), "only in the document: ['C101']")

    # ---- the netlist document ---------------------------------------------------------------
    def test_doc_pin_dropped(self):
        edit = sub_once(r"^(\| R1 \| R \| 5\.1k \| C25905 \| 1=CC1_J1) 2=GND", r"\1")
        self.assertFailsWith(run_check(doc=edit), "FAIL R1: pins ['2'] differ")

    def test_doc_net_changed(self):
        edit = sub_once(r"^(\| R1 \| R \| 5\.1k \| C25905 \| 1=CC1_J1 2=)GND", r"\1V5L")
        self.assertFailsWith(run_check(doc=edit), "FAIL R1.2: on net 'GND', the document says 'V5L'")

    def test_doc_nc_on_connected_pin(self):
        edit = sub_once(r"^(\| R1 \| R \| 5\.1k \| C25905 \| 1=CC1_J1 2=)GND", r"\1NC")
        self.assertFailsWith(run_check(doc=edit), "FAIL R1.2: marked NC but on net 'GND'")

    def test_doc_order_not_in_passive_table(self):
        edit = sub_once(r"^(\| R1 \| R \| 5\.1k \| )C25905", r"\1C25904")
        self.assertFailsWith(run_check(doc=edit), "ordered as C25904, which the passive table")

    def test_doc_body_wrong_size(self):
        edit = sub_once(r"^(\| C25076 \|.*\| )1\.00±0\.10 × 0\.50±0\.05 \|$", r"\g<1>1.60±0.10 × 0.80±0.10 |")
        self.assertFailsWith(run_check(doc=edit), "is not the R_0402_1005Metric size")

    def test_doc_flag_net_unknown(self):
        edit = sub_once(r"^\| V5L \| power \|", "| V5X | power |")
        self.assertFailsWith(run_check(doc=edit), "PWR_FLAG net V5X is not a document net")

    # ---- the circuit document, parts.md, the project ----------------------------------------
    def test_circuit_designator_missing(self):
        edit = sub_once(r"^\| SW3 \| BOOT button", "| SW9 | BOOT button")
        self.assertFailsWith(run_check(circuit=edit), "FAIL circuit 6.2", "SW3", "SW9")

    def test_parts_package_changed(self):
        edit = sub_once(r"^(\| 2\.4 kΩ .*\| C22940 \| )0603", r"\g<1>0402")
        self.assertFailsWith(run_check(parts=edit), "C22940 is 0402 there, 0603")

    def test_parts_code_missing(self):
        edit = sub_once(r"^\| 10 nF \|.*\n", "")
        self.assertFailsWith(run_check(parts=edit), "lacks ['C15195']")

    def test_usb_pattern_removed(self):
        edit = sub_once(r'"pattern": "USB_\*"', '"pattern": "USBX_*"')
        self.assertFailsWith(run_check(edit_pro=edit), "USB pair outside the class", "USB_UP_P")


if __name__ == "__main__":
    unittest.main(verbosity=2)
