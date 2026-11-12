"""Negative tests for check_outputs.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_outputs.py has written the set:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_outputs.py

Each test copies manufacturing/working/rev0.5 and design/ecad/source into a temporary
directory, corrupts the copies and runs check_outputs.py on them in a new process. After a
corruption the test rewrites SHA256SUMS.txt (and, when it edits the board, the manifest's
source hashes), so that only the rule under test breaks; the tests of those two rules leave
them as the corruption left them. The unchanged copy must pass; every corruption must fail
and be named in the output. The repository's files are never modified. Each run takes under
1 s.
"""
import hashlib
import io
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = pathlib.Path(__file__).resolve().parent
CHECK = HERE / "check_outputs.py"
ROOT = HERE.parents[2]
OUT = ROOT / "manufacturing" / "working" / "rev0.5"
SRC = ROOT / "design" / "ecad" / "source"
ROTATIONS = ROOT / "design" / "ecad" / "jlcpcb_model_rotation.json"
PREFIX = "UsbPowerHub_Main_Rev0.5"
ZIP = f"{PREFIX}_Gerber.zip"
BOM = f"{PREFIX}_BOM_JLCPCB.csv"
CPL = f"{PREFIX}_CPL_JLCPCB.csv"
PCB = "usb-power-hub.kicad_pcb"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rehash(out):
    """Rewrite SHA256SUMS.txt for the files now in out."""
    names = sorted(p.name for p in out.iterdir() if p.name != "SHA256SUMS.txt")
    text = "".join(f"{sha((out / n).read_bytes())}  {n}\n" for n in names)
    (out / "SHA256SUMS.txt").write_text(text, encoding="utf-8", newline="\n")


def rehash_sources(out, src):
    """Rewrite the manifest's source SHA-256 for the files now in src."""
    p = out / "RELEASE_MANIFEST.md"
    text = p.read_text(encoding="utf-8")

    def sub(m):
        return f"| `{m.group(1)}` | `{sha((src / pathlib.PurePosixPath(m.group(1)).name).read_bytes())}` |"
    p.write_text(re.sub(r"^\| `(design/ecad/source/[^`]+)` \| `[0-9a-f]{64}` \|$", sub, text, flags=re.M),
                 encoding="utf-8", newline="\n")


def edit(path, old, new, count=1):
    b = path.read_bytes()
    assert old in b, f"{old!r} not in {path.name}"
    path.write_bytes(b.replace(old, new, count))


def edit_zip(out, member=None, change=None, drop=None, when=(1980, 1, 1, 0, 0, 0)):
    """Rebuild the Gerber zip: change(text) -> text for one member, drop one, or set the times."""
    p = out / ZIP
    src = zipfile.ZipFile(io.BytesIO(p.read_bytes()))
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for info in src.infolist():
            if info.filename == drop:
                continue
            data = src.read(info.filename)
            if info.filename == member:
                new = change(data.decode("ascii")).encode("ascii")
                assert new != data, f"the change to {member} changed nothing"
                data = new
            z.writestr(zipfile.ZipInfo(info.filename, date_time=when), data)
    p.write_bytes(buf.getvalue())


def run_check(corrupt=None, sums=True):
    """Copy, corrupt(out, src), rehash unless sums is False, check."""
    with tempfile.TemporaryDirectory(prefix="outtest-") as tmp:
        t = pathlib.Path(tmp)
        out, src = t / "rev0.5", t / "source"
        shutil.copytree(OUT, out)
        shutil.copytree(SRC, src)
        table = t / ROTATIONS.name              # a corruption reaches it as src.parent / ROTATIONS.name
        shutil.copy(ROTATIONS, table)
        if corrupt:
            corrupt(out, src)
        if sums:
            rehash(out)
        r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--out", str(out), "--src", str(src),
                            "--rotations", str(table)],
                           capture_output=True, text=True, encoding="utf-8", timeout=600)
        return r.returncode, r.stdout + r.stderr


class CheckOutputsTest(unittest.TestCase):
    def assertFails(self, corrupt, *needles, sums=True):
        code, out = run_check(corrupt, sums)
        self.assertEqual(code, 1, out)
        for n in needles:
            self.assertIn(n, out)

    def test_unchanged_passes(self):
        code, out = run_check()
        self.assertEqual(code, 0, out)
        self.assertIn("0 failed: PASS", out)

    # ---- 1, 2 the set and its manifest
    def test_extra_file(self):
        self.assertFails(lambda o, s: (o / "notes.txt").write_text("x"), "FAIL set: extra ['notes.txt']")

    def test_missing_file(self):
        self.assertFails(lambda o, s: (o / f"{PREFIX}_Preview_Bottom.png").unlink(),
                         f"missing ['{PREFIX}_Preview_Bottom.png']")

    def test_hash_mismatch(self):
        self.assertFails(lambda o, s: edit(o / CPL, b'"C1","13.2500"', b'"C1","13.2501"'),
                         f"FAIL {CPL}: SHA-256 differs from SHA256SUMS.txt", sums=False)

    def test_stale_source(self):
        self.assertFails(lambda o, s: (s / "usb-power-hub.kicad_pro").write_bytes(
            (s / "usb-power-hub.kicad_pro").read_bytes() + b"\n"),
            "design/ecad/source/usb-power-hub.kicad_pro has changed since the set was made: stale")

    def test_state_not_wip(self):
        self.assertFails(lambda o, s: edit(o / "RELEASE_MANIFEST.md", b"| State | WIP |", b"| State | ORDERED |"),
                         "FAIL RELEASE_MANIFEST.md: not marked WIP")

    # ---- 3, 4 Gerber and drill
    def test_gerber_layer_missing(self):
        self.assertFails(lambda o, s: edit_zip(o, drop=f"{PREFIX}_In1_Cu.g1"),
                         f"FAIL {ZIP}: extra [], missing ['{PREFIX}_In1_Cu.g1']")

    def test_bottom_paste_object(self):
        self.assertFails(lambda o, s: edit_zip(o, f"{PREFIX}_B_Paste.gbp", lambda t: t.replace("M02*", "X0Y0D03*\nM02*")),
                         "1 objects on B.Paste")

    def test_outline_moved(self):
        self.assertFails(lambda o, s: edit_zip(o, f"{PREFIX}_Edge_Cuts.gm1",
                                               lambda t: re.sub(r"X100000000Y", "X101000000Y", t)),
                         f"FAIL {PREFIX}_Edge_Cuts.gm1: outline spans")

    def test_drill_hit_missing(self):
        self.assertFails(lambda o, s: edit_zip(o, f"{PREFIX}_PTH.drl",
                                               lambda t: re.sub(r"(?m)^T1(\r?\n)X[^\r\n]+\r?\n", r"T1\1", t, count=1)),
                         f"FAIL {PREFIX}_PTH.drl: holes by diameter")

    def test_zip_times_not_fixed(self):
        self.assertFails(lambda o, s: edit_zip(o, when=(2026, 11, 6, 10, 0, 0)), "member times are not fixed")

    # ---- 5, 6, 7 BOM, CPL, hand list
    def test_bom_designator_dropped(self):
        self.assertFails(lambda o, s: edit(o / BOM, b'"C1,C3,', b'"C3,'),
                         "FAIL BOM: designators: extra [], missing ['C1']")

    def test_lcsc_part_in_two_rows(self):
        """C45783 split over two BOM rows: the designators are all there, but JLCPCB selects neither row."""
        self.assertFails(lambda o, s: edit(o / BOM, b'"C1,C3,C7,C8"',
                                           b'"C1","C_0805_2012Metric","C45783"\n"22u","C3,C7,C8"'),
                         "FAIL BOM: an LCSC part in two rows")

    def test_hand_part_in_bom(self):
        def corrupt(o, s):
            b = (o / BOM).read_bytes()
            (o / BOM).write_bytes(b + b'"MF-R300","F1","Fuse_Bourns_MF-R300_Style2_P5.10mm","C1"\n')
        self.assertFails(corrupt, "FAIL BOM: designators: extra ['F1']", "a hand-soldered part in the BOM or CPL")

    def test_extended_class_not_allowed(self):
        def corrupt(o, s):
            p = s / PCB
            text = p.read_text(encoding="utf-8")
            i = text.index('(property "Reference" "C1"')
            j = text.index('(property "Class" "Basic"', i)
            p.write_text(text[:j] + '(property "Class" "Extended (D29)"' + text[j + len('(property "Class" "Basic"'):],
                         encoding="utf-8", newline="\n")
            rehash_sources(o, s)
        self.assertFails(corrupt, "FAIL BOM C1: class 'Extended (D29)'")

    def test_cpl_shifted(self):
        self.assertFails(lambda o, s: edit(o / CPL, b'"C1","13.2500"', b'"C1","13.3000"'),
                         "FAIL CPL C1: Mid (13.3, 55.8), footprint origin (13.2500, 55.8000)")

    def test_cpl_rotation(self):
        self.assertFails(lambda o, s: edit(o / CPL, b'"55.8000","Top","180"', b'"55.8000","Top","90"'),
                         "FAIL CPL C1: rotation 90.0, expected 180 (footprint 180 + JLCPCB model 0)")

    def test_cpl_model_rotation_missing(self):
        """U6 (CH335F, C5137013) is placed at its KiCad angle 0 plus the model's 270."""
        self.assertFails(lambda o, s: edit(o / CPL, b'"U6","94.0000","27.0000","Top","270"',
                                           b'"U6","94.0000","27.0000","Top","0"'),
                         "FAIL CPL U6: rotation 0.0, expected 270 (footprint 0 + JLCPCB model 270)")

    def test_model_rotation_table_dead_entry(self):
        self.assertFails(lambda o, s: edit(s.parent / ROTATIONS.name, b'"C6186": {"add": 180,',
                                           b'"C9999999": {"add": 180,'),
                         "FAIL model rotation table: entries no BOM line uses: ['C9999999']")

    def test_cpl_bottom(self):
        self.assertFails(lambda o, s: edit(o / CPL, b'"55.8000","Top"', b'"55.8000","Bottom"'),
                         "FAIL CPL C1: layer Bottom")

    # ---- 8 documents
    def test_schematic_page_missing(self):
        def corrupt(o, s):
            p = o / f"{PREFIX}_Schematic.pdf"
            b = p.read_bytes()
            m = re.search(rb"/Type\s*/Page(?![s\w])", b)
            p.write_bytes(b[:m.start()] + b"/Type /Pagx" + b[m.end():])
        self.assertFails(corrupt, f"FAIL {PREFIX}_Schematic.pdf:", "(one per sheet)")

    def test_preview_wrong_aspect(self):
        # the IHDR height of the top render doubled: the board's 100:72 aspect is lost
        def corrupt(o, s):
            p = o / f"{PREFIX}_Preview_Top.png"
            b = bytearray(p.read_bytes())
            h = int.from_bytes(b[20:24], "big")
            b[20:24] = (2 * h).to_bytes(4, "big")
            p.write_bytes(bytes(b))
        self.assertFails(corrupt, f"FAIL {PREFIX}_Preview_Top.png: PNG of size")

    def test_preview_too_small(self):
        def corrupt(o, s):
            p = o / f"{PREFIX}_Preview_Bottom.png"
            b = bytearray(p.read_bytes())
            w, h = int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
            b[16:24] = (w // 2).to_bytes(4, "big") + (h // 2).to_bytes(4, "big")
            p.write_bytes(bytes(b))
        self.assertFails(corrupt, f"FAIL {PREFIX}_Preview_Bottom.png: PNG of size")

    def test_drc_violation(self):
        def corrupt(o, s):
            p = o / f"{PREFIX}_DRC.json"
            edit(p, b'"violations": []', b'"violations": [{"type": "clearance"}]')
        self.assertFails(corrupt, f"FAIL {PREFIX}_DRC.json: 1 violations")

    # ---- 9 privacy and determinism
    def test_private_path(self):
        self.assertFails(lambda o, s: edit(o / "RELEASE_MANIFEST.md", b"| State | WIP |",
                                           b"| State | WIP |\nC:\\Users\\someone\\board"),
                         "FAIL RELEASE_MANIFEST.md: holds 'C:\\\\Users\\\\'")

    def test_creation_date(self):
        self.assertFails(lambda o, s: edit(o / f"{PREFIX}_ERC.json", b"1980-01-01", b"2026-11-06"),
                         f"FAIL {PREFIX}_ERC.json: creation date '2026-11-06")


if __name__ == "__main__":
    unittest.main(verbosity=2)
