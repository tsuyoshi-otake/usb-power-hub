"""Negative tests for check_routing.py (CLAUDE.md 8: a checker never observed failing is not
evidence).

Run with KiCad's Python from the repository root, after make_pcb.py has written the routed
board:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_routing.py

Each test copies design/ecad/source and design/ecad/libraries into a temporary directory,
copies the routing and placement documents beside them, corrupts the copies, and runs
check_routing.py on them in a new process. The unchanged copy must pass. Every corruption
must fail, and the failure must be named in the output. The repository's files are never
modified. Each run includes DRC, about 10 s.

The two tests of the plane (rule 9) add vias and fill the zones of the corrupted copy again,
because the checker reads the stored fill.

Not covered here:
- The In1 zone's net and layer type (make_pcb.py builds them from the zones table).
- The In1 fill rule under the pairs: removing fill also breaks DRC's zone connectivity first.
- Rule 9 on U6's exposed pad, and on the north, east and south of U1's: one side of one pad
  stands for the eight, which one function measures.
"""
import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

HERE = pathlib.Path(__file__).resolve().parent
CHECK = HERE / "check_routing.py"
ECAD = HERE.parent
DOCS = {"doc": ECAD / "ROUTING_Rev0.5.md", "placement": ECAD / "PLACEMENT_Rev0.5.md"}
ORIGIN = (50.0, 122.0)

_spec = importlib.util.spec_from_file_location("sexpr", HERE / "sexpr.py")
sx = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sx)


def refill_zones(path):
    """Fill every zone of a board file again, as make_pcb.py does after the routing: the checker
    reads the stored fill, so a corruption that must show in the plane is refilled first."""
    import pcbnew
    board = pcbnew.LoadBoard(str(path))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    if not pcbnew.SaveBoard(str(path), board):
        raise AssertionError("pcbnew could not save the refilled board")


def run_check(board=None, refill=False, **edit_text):
    """Copy, corrupt, check. Returns (exit status, output).

    board(tree): edit the board's parsed S-expression in place; refill: fill the zones of the
    corrupted board again.
    doc / placement = edit(text): return the corrupted text.
    """
    with tempfile.TemporaryDirectory(prefix="routetest-") as tmp:
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
            if refill:
                refill_zones(p)
        r = subprocess.run([sys.executable, "-I", "-B", str(CHECK), "--src", str(src), *args],
                           capture_output=True, text=True, encoding="utf-8", timeout=900)
        return r.returncode, r.stdout + r.stderr


# ---- board edits (sheet coordinates in the file; the helpers take the board frame) -----------


def sheet(x, y):
    return round(ORIGIN[0] + x, 6), round(ORIGIN[1] - y, 6)


def net_code(tree, name):
    return next(n[1] for n in sx.find(tree, "net") if len(n) > 2 and n[2] == name)


def segments(tree, name, layer=None):
    code = net_code(tree, name)
    return [s for s in sx.find(tree, "segment") if sx.first(s, "net")[1] == code
            and (layer is None or sx.first(s, "layer")[1] == layer)]


def ends(seg):
    return [sx.first(seg, "start"), sx.first(seg, "end")]


def segments_on(tree, layer):
    return [s for s in sx.find(tree, "segment") if sx.first(s, "layer")[1] == layer]


def add_segment(tree, name, a, b, width, layer):
    tree.append(["segment", ["start", *sheet(*a)], ["end", *sheet(*b)], ["width", width],
                 ["layer", layer], ["net", net_code(tree, name)], ["uuid", str(uuid.uuid4())]])


def add_via(tree, name, at_sheet, drill=0.30):
    tree.append(["via", ["at", *at_sheet], ["size", 0.45], ["drill", drill], ["layers", "F.Cu", "B.Cu"],
                 ["net", net_code(tree, name)], ["uuid", str(uuid.uuid4())]])


def vias_of(tree, name):
    code = net_code(tree, name)
    return [v for v in sx.find(tree, "via") if sx.first(v, "net")[1] == code]


def tht_pads(tree):
    """(footprint reference, pad node) of every plated through-hole pad with a round drill."""
    out = []
    for f in sx.find(tree, "footprint"):
        ref = next((p[2] for p in sx.find(f, "property") if len(p) > 2 and p[1] == "Reference"), None)
        for p in sx.find(f, "pad"):
            drill = sx.first(p, "drill")
            if p[2] == "thru_hole" and drill is not None and len(drill) == 2:
                out.append((ref, p))
    return out


def footprint_at(tree, ref):
    """The position of a part, board frame."""
    for f in sx.find(tree, "footprint"):
        if any(len(p) > 2 and p[1] == "Reference" and p[2] == ref for p in sx.find(f, "property")):
            at = sx.first(f, "at")
            return at[1] - ORIGIN[0], ORIGIN[1] - at[2]
    raise AssertionError(f"no part {ref}")


def remove(tree, items):
    ids = {id(i) for i in items}
    tree[:] = [x for x in tree if id(x) not in ids]


# ---- document edits ---------------------------------------------------------------------------


def sub_once(pattern, repl):

    def edit(text):
        new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
        assert n == 1, pattern
        return new
    return edit


def kelvin_net():
    text = DOCS["doc"].read_text(encoding="utf-8")
    m = re.search(r"^\| (\w+) \| F\.Cu \| 0\.20 \| [^|]* \| Kelvin tap \|", text, re.M)
    assert m, "no Kelvin tap row in the routing document"
    return m.group(1)


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

    # ---- DRC and the plane --------------------------------------------------------------------

    def test_routed_segment_removed(self):
        def edit(tree):
            remove(tree, segments(tree, "ADC_CS")[:1])
        self.assertFailsWith(run_check(board=edit), "FAIL DRC unconnected")

    def test_track_on_in1(self):
        self.assertFailsWith(run_check(board=lambda t: add_segment(t, "GND", (5.0, 70.0), (8.0, 70.0), 0.2, "In1.Cu")),
                             "FAIL In1.Cu: 1 track(s) on the plane layer")

    # ---- the pairs ----------------------------------------------------------------------------

    def test_pair_width_changed(self):
        def edit(tree):
            s = next(s for s in segments(tree, "USB_UP_P") if sx.first(s, "width")[1] == 0.31)
            sx.first(s, "width")[1] = 0.25
        self.assertFailsWith(run_check(board=edit), "FAIL pair UP: USB_UP_P track 0.25 mm wide")

    def test_pair_conductor_off_centreline(self):
        def edit(tree):
            # the long westward run of USB_A_P at y 17.67: 0.05 mm further from N
            y = sheet(0, 17.67)[1]
            s = next(s for s in segments(tree, "USB_A_P", "F.Cu")
                     if all(abs(e[2] - y) < 1e-6 for e in ends(s)) and abs(ends(s)[0][1] - ends(s)[1][1]) > 30)
            for e in ends(s):
                e[2] = round(e[2] + 0.05, 6)
        self.assertFailsWith(run_check(board=edit), "FAIL pair A: USB_A_P 0.280 mm from the centreline")

    def test_pair_via(self):
        # a via on a pair's net anywhere: the pairs have none (D37)
        self.assertFailsWith(run_check(board=lambda t: add_via(t, "USB_B_N", sheet(60.0, 40.0))),
                             "FAIL pair B: 1 via(s) on USB_B_N USB_B_P")

    def test_pair_track_on_back_layer(self):
        def edit(tree):
            sx.first(segments(tree, "USB_A_N", "F.Cu")[0], "layer")[1] = "B.Cu"
        self.assertFailsWith(run_check(board=edit), "FAIL pair A: USB_A_N track on B.Cu")

    # ---- JLCPCB's hole figures (make_project.py RULES and PTH_RULES, issue #8) -----------------

    def test_via_drill_025(self):
        def edit(tree):
            sx.first(vias_of(tree, "GND")[0], "drill")[1] = 0.25
        self.assertFailsWith(run_check(board=edit), "FAIL DRC", "drill_out_of_range")

    def test_pth_ring_below_015(self):
        def edit(tree):
            # the first round PTH pad: copper 0.20 mm wider than its drill, a 0.10 mm ring, which
            # the board's via minimum (0.075) allows and the PTH rule (0.15) does not
            _, pad = tht_pads(tree)[0]
            d = sx.first(pad, "drill")[1]
            sx.first(pad, "size")[1:3] = [round(d + 0.2, 3), round(d + 0.2, 3)]
        self.assertFailsWith(run_check(board=edit), "FAIL DRC", "annular_width")

    def test_via_holes_015_apart(self):
        def edit(tree):
            # a second GND via 0.45 mm from a GND via: 0.15 mm between the 0.30 mm holes
            at = sx.first(vias_of(tree, "GND")[0], "at")
            add_via(tree, "GND", (round(at[1] + 0.45, 6), at[2]))
        self.assertFailsWith(run_check(board=edit), "FAIL DRC", "hole_to_hole")

    def test_copper_near_pair(self):
        # 0.415 mm from USB_A_P's edge, on F.Cu, away from any other copper of the corridor
        self.assertFailsWith(run_check(board=lambda t: add_segment(t, "V3V3", (50.0, 17.0), (51.0, 17.0), 0.2, "F.Cu")),
                             "FAIL pair A: PCB_TRACK V3V3 within 0.5 mm of USB_A_P on F.Cu")

    # ---- Kelvin taps, the analog rule, classes, the port path ---------------------------------

    def test_via_on_kelvin_tap(self):
        net = kelvin_net()

        def edit(tree):
            add_via(tree, net, ends(segments(tree, net)[0])[0][1:3])
        self.assertFailsWith(run_check(board=edit), f"FAIL Kelvin {net}: 1 via(s)")

    def test_b_cu_under_analog_in2_track(self):
        def edit(tree):
            # the longest In2 track inside AFE_A (x 0.5-33.6, y 19-49.5) of a net other than
            # V3V3, its middle 60 % copied onto B.Cu as a V3V3 track (a net over its own B.Cu
            # track is exempt). The longest, not the first: the file's segment order follows
            # the UUIDs. The middle, not the whole: a copy ending on the In2 track's via would
            # join that via's net when the board loads, and be exempt.
            other = net_code(tree, "V3V3")
            best = None
            for s in sx.find(tree, "segment"):
                if sx.first(s, "layer")[1] != "In2.Cu" or sx.first(s, "net")[1] == other:
                    continue
                (x0, y0), (x1, y1) = ((e[1] - ORIGIN[0], ORIGIN[1] - e[2]) for e in ends(s))
                if all(1.0 < x < 33.0 and 20.0 < y < 49.0 for x, y in ((x0, y0), (x1, y1))):
                    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
                    if best is None or length > best[0]:
                        best = (length, s)
            if best is None:
                raise AssertionError("no In2 track inside AFE_A")
            s = best[1]
            (_, ax, ay), (_, bx, by) = ends(s)
            at = [[k, ax + f * (bx - ax), ay + f * (by - ay)] for k, f in (("start", 0.2), ("end", 0.8))]
            width = sx.first(s, "width")
            tree.append(["segment", *at, width, ["layer", "B.Cu"], ["net", other], ["uuid", str(uuid.uuid4())]])
        self.assertFailsWith(run_check(board=edit), "FAIL analog: In2 ")

    def test_crossing_in_analog_allowed(self):
        """D36: a 90-degree In2 crossing over a B.Cu track in AFE_A is allowed and counted."""
        def crossings(out):
            m = re.search(r"(\d+) In2/B\.Cu crossing\(s\) there", out)
            self.assertIsNotNone(m, out)
            return int(m.group(1))

        def edit(tree):
            # the middle of the first straight B.Cu track inside AFE_A longer than 2 mm, not V3V3,
            # crossed at 90 degrees by a 0.6 mm In2 track of V3V3
            other = net_code(tree, "V3V3")
            for s in segments_on(tree, "B.Cu"):
                if sx.first(s, "net")[1] == other:
                    continue
                (x0, y0), (x1, y1) = ((e[1] - ORIGIN[0], ORIGIN[1] - e[2]) for e in ends(s))
                if not all(1.0 < x < 33.0 and 20.0 < y < 49.0 for x, y in ((x0, y0), (x1, y1))):
                    continue
                if x0 == x1 and abs(y1 - y0) > 2.0:
                    a, b = ((x0 - 0.3, (y0 + y1) / 2), (x0 + 0.3, (y0 + y1) / 2))
                elif y0 == y1 and abs(x1 - x0) > 2.0:
                    a, b = (((x0 + x1) / 2, y0 - 0.3), ((x0 + x1) / 2, y0 + 0.3))
                else:
                    continue
                tree.append(["segment", ["start", *sheet(*a)], ["end", *sheet(*b)], ["width", 0.2],
                             ["layer", "In2.Cu"], ["net", other], ["uuid", str(uuid.uuid4())]])
                return
            raise AssertionError("no straight B.Cu track inside AFE_A")
        base = crossings(run_check()[1])
        status, out = run_check(board=edit)
        self.assertNotIn("FAIL analog", out)
        self.assertEqual(crossings(out), base + 1, out)

    def test_class_layer_broken(self):
        def edit(tree):
            s = segments(tree, "VBUS_J1", "F.Cu")[0]
            sx.first(s, "layer")[1] = "In2.Cu"
        self.assertFailsWith(run_check(board=edit), "FAIL class J1_POWER: ")

    def test_port_trunk_removed(self):
        def edit(tree):
            # SRC_A's 1.20 mm trunk between the switch FETs (ROUTING_Rev0.5.md, x 1.2)
            x = sheet(1.2, 0)[0]
            trunk = [s for s in segments(tree, "SRC_A", "F.Cu")
                     if sx.first(s, "width")[1] == 1.2 and all(abs(e[1] - x) < 1e-6 for e in ends(s))]
            assert len(trunk) == 1, trunk
            remove(tree, trunk)
        self.assertFailsWith(run_check(board=edit), "FAIL port A: SRC_A Q10.2 -> Q11.2: no copper path")

    def test_port_net_island_elsewhere(self):
        """A stray island of a port net leaves the path's resistance computable."""
        status, out = run_check(board=lambda t: add_segment(t, "SRC_A", (5.0, 70.0), (6.0, 70.0), 0.2, "F.Cu"))
        self.assertEqual(status, 1, out)
        self.assertIn("FAIL DRC", out)
        self.assertNotIn("FAIL port A", out)

    @staticmethod
    def remove_joiner(tree, net="VBUS_A"):
        """The 0.25 mm F.Cu joiner under the receptacle between its two VBUS pads (D37)."""
        joiner = [s for s in segments(tree, net, "F.Cu") if sx.first(s, "width")[1] == 0.25]
        assert len(joiner) == 3, joiner
        remove(tree, joiner)

    def test_joined_receptacle_pads_are_one_node(self):
        """With the joiner gone pad A4 is unconnected (DRC says so), but the port path to the
        pair `J2.A4+J2.B4` is still found through pad B4: the contacts are one node."""
        status, out = run_check(board=self.remove_joiner)
        self.assertEqual(status, 1, out)
        self.assertIn("FAIL DRC unconnected", out)
        self.assertNotIn("FAIL port A", out)

    def test_single_receptacle_pad_has_no_path_without_the_joiner(self):
        doc = sub_once(r"^\| A \| VBUS_A \| Q17\.3 \| J2\.A4\+J2\.B4 \|$", "| A | VBUS_A | Q17.3 | J2.A4 |")
        self.assertFailsWith(run_check(board=self.remove_joiner, doc=doc),
                             "FAIL port A: VBUS_A Q17.3 -> J2.A4: no copper path")

    # ---- the plane (rule 9) -------------------------------------------------------------------

    def test_plane_slot(self):
        """Four vias of one signal net 0.9 mm apart: their 0.85 mm antipads join into one void
        2.7 + 0.85 = 3.55 mm long, over the 3.0 mm limit."""
        at = (60.0, 40.0)

        def edit(tree):
            for k in range(4):
                add_via(tree, "V3V3", sheet(at[0] + 0.9 * k, at[1]))
        status, out = run_check(board=edit, refill=True)
        self.assertEqual(status, 1, out)
        slots = re.findall(r"FAIL L2 slot: void ([\d.]+) mm long, x ([\d.]+)\.\.([\d.]+), y ([\d.]+)\.\.([\d.]+),", out)
        self.assertEqual(len(slots), 1, out)
        length, x0, x1, y0, y1 = map(float, slots[0])
        self.assertGreaterEqual(length, 3.5, out)
        self.assertTrue(x0 <= at[0] and at[0] + 2.7 <= x1 and y0 <= at[1] <= y1, out)

    def test_plane_perforated_at_epad(self):
        """Five vias 1.10 mm apart down the west of U1's exposed pad, between it and the pad
        row: each antipad is its own 0.85 mm void, so there is no slot, but only the 0.25 mm
        webs between them join the pad's area to the plane on that side: about 1 mm of the
        pad's 3.20 mm, under the 1.60 mm rule 9 wants. The west is chosen because it carries
        none of the document's escapes of U1's pins (the north and east do); the unchanged copy
        passes with at least 1.60 mm there, so a web below it comes from these five vias."""
        def edit(tree):
            cx, cy = footprint_at(tree, "U1")
            for k in range(-2, 3):
                add_via(tree, "V3V3", sheet(cx - 1.6 - 0.7, cy + 1.10 * k))
        status, out = run_check(board=edit, refill=True)
        self.assertEqual(status, 1, out)
        m = re.search(r"FAIL L2 web U1\.57 W: ([\d.]+) mm of plane copper", out)
        self.assertIsNotNone(m, out)
        self.assertLess(float(m.group(1)), 1.6, out)

    def test_port_path_limit_lowered(self):
        doc = sub_once(r"<!-- port_path:begin limit=40 -->", "<!-- port_path:begin limit=1 -->")
        self.assertFailsWith(run_check(doc=doc), "FAIL port A: ", "limit 1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
