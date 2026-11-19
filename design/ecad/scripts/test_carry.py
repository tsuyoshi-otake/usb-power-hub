"""Negative tests for the carried routing: carry.py, route.apply_carried and make_pcb.carried
(CLAUDE.md 8: a checker never observed failing is not evidence).

Run with KiCad's Python from the repository root, after carry.py has written
design/ecad/routing/carried.json:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_carry.py

The tests of class Record build the carried routing once, as carry.py does (about 10 s: a DRC
run a round), and compare it with the tracked record and with corrupted copies of its text.
The other tests run in this process, on small boards made here and on records written into a
temporary directory. The repository's files are never modified.

Not covered here:
- Whether the carried copper is good on this board: check_routing.py judges the finished board.
- The DRC rounds of carry.compute one by one: the Record tests run them, uncorrupted. That a
  carried item DRC objects to is dropped shows in the record itself (its `dropped` counts) and
  in check_routing.py's DRC of the finished board.
- make_pcb.py end to end with a stale record: the three refusals of make_pcb.carried are tested
  as that function's, not through a whole build.
"""
import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("carry", HERE / "carry.py")
carry = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(carry)
mp = carry.mp
route = mp.route
mm = pcbnew.FromMM
SHA = "0123456789abcdef" * 4


def table(rows, args="commit=abc1234"):
    """route._carry of a carry table with these rows."""
    text = f"<!-- carry:begin {args} -->\n| Item | Value | SHA-256 |\n|---|---|---|\n" + \
        "".join(f"| {a} | {b} | {c} |\n" for a, b, c in rows) + "<!-- carry:end -->\n"
    return route._carry(mp.doc_tables(text))


GOOD = [("session", "a/b.ses", SHA), ("patch", "a/ROUTING.md", SHA), ("skip", "Slot vias:", "-")]


def fails(case, call, *needles):
    """call() must stop with a message that holds every needle."""
    with case.assertRaises(SystemExit) as ctx:
        call()
    for n in needles:
        case.assertIn(n, str(ctx.exception))


class Table(unittest.TestCase):
    def test_good_table(self):
        got = table(GOOD)
        self.assertEqual((got["commit"], got["session"], got["patch"], got["skip"]),
                         ("abc1234", "a/b.ses", "a/ROUTING.md", ["Slot vias:"]))
        self.assertEqual((got["session_sha256"], got["patch_sha256"]), (SHA, SHA))

    def test_no_table_carries_nothing(self):
        self.assertIsNone(route._carry({}))

    def test_no_commit(self):
        fails(self, lambda: table(GOOD, args="analog=x"), "commit")

    def test_no_patch_row(self):
        fails(self, lambda: table(GOOD[:1]), "one session and one patch")

    def test_two_sessions(self):
        fails(self, lambda: table(GOOD + [("session", "c.ses", SHA)]), "carry:")

    def test_sha_too_short(self):
        fails(self, lambda: table([("session", "a/b.ses", SHA[:-1])] + GOOD[1:]), "carry:")

    def test_unknown_item(self):
        fails(self, lambda: table(GOOD + [("zone", "x", "-")]), "carry:")


def small_board():
    """(board, {name: net}, pad): two nets, and one 0402 whose first pad is on N1."""
    board = pcbnew.BOARD()
    nets = {}
    for name in ("N1", "N2"):
        nets[name] = pcbnew.NETINFO_ITEM(board, name)
        board.Add(nets[name])
    fp = pcbnew.FootprintLoad(str(mp.LIB), "R_0402_1005Metric")
    board.Add(fp)
    fp.SetPosition(pcbnew.VECTOR2I(mm(100), mm(100)))
    pad = list(fp.Pads())[0]
    pad.SetNet(nets["N1"])
    return board, nets, pad


def keys(board):
    return sorted(route.item_key(board, t) for t in board.GetTracks())


class Apply(unittest.TestCase):
    def setUp(self):
        self.board, self.nets, _ = small_board()
        self.drawn = route.add_track(self.board, self.nets["N1"], pcbnew.VECTOR2I(mm(110), mm(110)),
                                     pcbnew.VECTOR2I(mm(112), mm(110)), 0.2, pcbnew.F_Cu)
        self.record = dict(remove=[list(route.item_key(self.board, self.drawn))],
                           tracks=[["N2", "F.Cu", 289999, 120000001, 120000000, 121000000, 120000003]],
                           vias=[["N2", 121000000, 120000003, 450000, 300000]])

    def test_record_is_applied_to_the_nanometre(self):
        self.assertEqual(route.apply_carried(self.board, self.record), (1, 1, 1))
        self.assertEqual(keys(self.board), [("N2", "F.Cu", 120000001, 120000000, 121000000, 120000003),
                                            ("N2", "via", 121000000, 120000003)])
        segs, vias = route.carried_items(self.board, self.board.GetTracks())
        self.assertEqual((segs, vias), (self.record["tracks"], self.record["vias"]))

    def test_key_does_not_depend_on_the_direction(self):
        back = route.add_track(self.board, self.nets["N1"], self.drawn.GetEnd(), self.drawn.GetStart(), 0.2,
                               pcbnew.F_Cu)
        self.assertEqual(route.item_key(self.board, back), route.item_key(self.board, self.drawn))

    def test_item_to_take_away_is_missing(self):
        self.record["remove"][0][2] += 1
        fails(self, lambda: route.apply_carried(self.board, self.record), "to take away", "run carry.py")

    def test_item_to_take_away_is_listed_twice(self):
        self.record["remove"] *= 2
        fails(self, lambda: route.apply_carried(self.board, self.record), "to take away")

    def test_net_is_not_on_the_board(self):
        self.record["tracks"][0][0] = "N9"
        fails(self, lambda: route.apply_carried(self.board, self.record), "no net N9", "run carry.py")

    def test_via_net_is_not_on_the_board(self):
        self.record["vias"][0][0] = "N9"
        fails(self, lambda: route.apply_carried(self.board, self.record), "no net N9")


class Prune(unittest.TestCase):
    def test_only_what_floats_goes(self):
        board, nets, pad = small_board()
        n1 = nets["N1"]

        def track(x1, y1, x2, y2):
            return route.add_track(board, n1, pcbnew.VECTOR2I(mm(x1), mm(y1)), pcbnew.VECTOR2I(mm(x2), mm(y2)),
                                   0.2, pcbnew.F_Cu)
        at = pad.GetPosition()
        on_pad = route.add_track(board, n1, at, pcbnew.VECTOR2I(at.x, at.y + mm(2)), 0.2, pcbnew.F_Cu)
        behind = route.add_track(board, n1, pcbnew.VECTOR2I(at.x, at.y + mm(2)), pcbnew.VECTOR2I(at.x, at.y + mm(4)),
                                 0.2, pcbnew.F_Cu)
        afloat = [track(120, 120, 122, 120), track(122, 120, 122, 122)]
        via = route.add_via(board, n1, pcbnew.VECTOR2I(mm(122), mm(122)), 0.45, 0.30)
        drawn = track(130, 130, 132, 130)
        on_drawn = track(132, 130, 134, 130)
        mine = {t.m_Uuid.AsString() for t in (on_pad, behind, *afloat, via, on_drawn)}
        gone = carry.prune(board, mine)
        self.assertEqual(sorted(route.item_key(board, t) for t in gone),
                         sorted(route.item_key(board, t) for t in (*afloat, via)))
        self.assertEqual(len(board.GetTracks()), 4)
        self.assertEqual(carry.prune(board, mine), [])

    def test_a_floating_item_that_is_not_carried_stays(self):
        board, nets, _ = small_board()
        t = route.add_track(board, nets["N1"], pcbnew.VECTOR2I(mm(120), mm(120)), pcbnew.VECTOR2I(mm(122), mm(120)),
                            0.2, pcbnew.F_Cu)
        self.assertEqual(carry.prune(board, set()), [])
        self.assertEqual(carry.prune(board, {t.m_Uuid.AsString()}), [t])


class Stale(unittest.TestCase):
    CARRY = dict(commit="abc1234", session_sha256=SHA, patch_sha256=SHA, skip=["Slot vias:"])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="carrytest-")
        self.kept = mp.CARRIED
        mp.CARRIED = pathlib.Path(self.tmp.name) / "carried.json"
        self.record = dict(self.CARRY, base_dsn_sha256="b" * 64, remove=[], tracks=[], vias=[])

    def tearDown(self):
        mp.CARRIED = self.kept
        self.tmp.cleanup()

    def write(self, **change):
        mp.CARRIED.write_text(json.dumps(dict(self.record, **change)), encoding="utf-8")

    def test_record_for_this_board_is_taken(self):
        self.write()
        self.assertEqual(mp.carried(self.CARRY, "b" * 64), self.record)

    def test_no_record(self):
        fails(self, lambda: mp.carried(self.CARRY, "b" * 64), "no carried.json", "run carry.py")

    def test_made_for_another_board(self):
        self.write()
        fails(self, lambda: mp.carried(self.CARRY, "c" * 64), "made for another board", "run carry.py")

    def test_made_from_another_commit(self):
        self.write(commit="def5678")
        fails(self, lambda: mp.carried(self.CARRY, "b" * 64), "not made from the sources", "run carry.py")

    def test_made_from_another_session(self):
        self.write(session_sha256="f" * 64)
        fails(self, lambda: mp.carried(self.CARRY, "b" * 64), "not made from the sources")

    def test_made_from_another_patch(self):
        self.write(patch_sha256="f" * 64)
        fails(self, lambda: mp.carried(self.CARRY, "b" * 64), "not made from the sources")

    def test_made_with_another_skip(self):
        self.write(skip=[])
        fails(self, lambda: mp.carried(self.CARRY, "b" * 64), "not made from the sources")


class Source(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.carry = mp.read_routing(mp.DOC, mp.ROUTING)[0]["carry"]

    def test_document_names_a_source_git_has(self):
        text = carry.source(self.carry["commit"], self.carry["session"], self.carry["session_sha256"])
        self.assertIn("(session", text)

    def test_another_file_at_that_commit(self):
        fails(self, lambda: carry.source(self.carry["commit"], self.carry["patch"], self.carry["session_sha256"]),
              "is not the file the carry table names")

    def test_no_such_file_at_that_commit(self):
        fails(self, lambda: carry.source(self.carry["commit"], "design/ecad/routing/none.ses", SHA), "git has no")

    def test_no_such_commit(self):
        fails(self, lambda: carry.source("0" * 40, self.carry["session"], self.carry["session_sha256"]), "git has no")


class Record(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with tempfile.TemporaryDirectory(prefix="carrytest-") as tmp:
            cls.record, _ = carry.compute(pathlib.Path(tmp))
        cls.text = mp.CARRIED.read_text(encoding="utf-8")

    def corrupt(self, edit):
        was = json.loads(self.text)
        edit(was)
        return carry.dumps(was)

    def test_tracked_record_is_what_carry_makes(self):
        self.assertIsNone(carry.differs(self.record, self.text))

    def test_a_track_is_missing(self):
        self.assertEqual(carry.differs(self.record, self.corrupt(lambda r: r["tracks"].pop(7))), "tracks differ")

    def test_a_dropped_track_is_back(self):
        def edit(r):
            r["tracks"].append(["GND", "F.Cu", 200000, 100000000, 100000000, 101000000, 100000000])
        self.assertEqual(carry.differs(self.record, self.corrupt(edit)), "tracks differ")

    def test_a_via_moved_by_a_nanometre(self):
        def edit(r):
            r["vias"][3][1] += 1
        self.assertEqual(carry.differs(self.record, self.corrupt(edit)), "vias differ")

    def test_a_drawn_item_is_no_longer_taken_away(self):
        self.assertEqual(carry.differs(self.record, self.corrupt(lambda r: r["remove"].pop())), "remove differ")

    def test_another_board(self):
        def edit(r):
            r["base_dsn_sha256"] = "0" * 64
        self.assertEqual(carry.differs(self.record, self.corrupt(edit)), "base_dsn_sha256 differ")

    def test_a_count_of_dropped_items_changed(self):
        def edit(r):
            r["dropped"]["drc"] += 1
        self.assertEqual(carry.differs(self.record, self.corrupt(edit)), "dropped differ")

    def test_dropped_holds_no_violation_type(self):
        # DRC's split by type is not the same in every run (carry.py, step 5)
        self.assertEqual(sorted(self.record["dropped"]), ["drc", "floating"])

    def test_text_laid_out_otherwise(self):
        self.assertEqual(carry.differs(self.record, json.dumps(json.loads(self.text), indent=1) + "\n"),
                         "the layout of the text differs")

    def test_not_json(self):
        self.assertEqual(carry.differs(self.record, self.text[:-3]), "the file is not JSON")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    unittest.main(verbosity=2)
