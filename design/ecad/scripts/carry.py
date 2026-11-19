"""Carry the previous revision's routing onto this revision's board (issues #13 and #14;
ROUTING_Rev0.7.md, "Carried from Rev0.6").

Run with KiCad's own Python from the repository root, after make_schematic.py and before
autoroute.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/carry.py [--check]

A layout revision moves or changes a few parts (Rev0.6, D39: 31 of 304; Rev0.7, D40: J5 alone).
The copper of the other parts stays as the previous revision had it,
so the routing of the analog blocks and of U1 does not change with a connector's position. What
this script does:
1. It builds the board as make_pcb.py does up to the GND fanout (make_pcb.base_board).
2. It reads the sources the routing document's carry table names, at the commit the table
   names, with `git show`, and checks each against the table's SHA-256: the previous revision's
   own carried record if it had one (the table's optional `carried` row; Rev0.7 carries Rev0.6,
   which carried Rev0.5), its router session, and its routing document, whose patch table holds
   what was drawn after that
   session.
3. It applies them in that order with the pipeline's own functions (route.apply_carried,
   route.import_session, route.apply_patch),
   less the patch rows whose Why begins with a text the table skips. The patch's remove rows
   take away drawn items of this board too, where the previous revision had replaced them.
4. It drops what no longer stands, in rounds, until a round drops nothing. First every carried
   cluster of connected tracks and vias that reaches no pad and no item of step 1 goes: it
   floats (pcbnew's connectivity gives the neighbours of each item). Then KiCad's DRC runs, and
   every carried track or via it names in a violation goes, whole: a short to a moved part's pad,
   a crossing with a drawn track, a clearance. The plane is filled again before each of the two.
   DRC's track_dangling and via_dangling are not reasons to drop: a carried route that lost its
   far end stays, open-ended, for the router or the patch table to continue.
5. It writes design/ecad/routing/carried.json: the sources, the digest of the router input of the
   board of step 1, how many items floated and how many DRC named, the drawn items taken away,
   and every carried track and via that stands, in the board's nanometres. make_pcb.py applies
   the record between the GND fanout and the router input, so the router sees the carried copper
   as fixed and routes only what is left open. DRC's violation type for a dropped item is printed
   and not recorded: for the same board KiCad names one short shorting_items in one run and
   solder_mask_bridge in another (seen in 2 of 2 series of runs), while the items it names, and
   so the record, were the same in every run.
With --check it builds the record again and compares it with the tracked file.

What it CANNOT see: whether the carried routing is good on this board. It keeps whatever DRC does
not object to. A carried track that now passes a moved part at a legal clearance stays; so does
a detour whose reason was a part that is no longer there, and an open end nobody continues, which
DRC then reports on the finished board until the patch table takes it away. D36, the plane rule,
the hole rule and the port path are not looked at here: check_routing.py checks them on the
finished board. It connects nothing: what a dropped route leaves open is the router's and the
patch's work. A segment in the way is dropped whole, however little of it is in the way.
The sources come from Git history: without the commit the table names, it stops.
Exit status: 0 = the record is written, or --check found it equal; 1 = otherwise.
"""
import collections
import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
DANGLING = {"track_dangling", "via_dangling"}     # a carried route's open end: it stays for the router
MAX_ROUNDS = 40
LISTS = ("remove", "tracks", "vias")              # written one item to a line


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


mp = _load("make_pcb")
route = mp.route


def source(commit, path, sha):
    """The text of path at commit, from Git history, after checking its SHA-256."""
    r = subprocess.run(["git", "-C", str(mp.ROOT), "show", f"{commit}:{path}"], capture_output=True, timeout=120)
    if r.returncode:
        raise SystemExit(f"carry: git has no {path} at {commit[:7]}:"
                         f" {r.stderr.decode('utf-8', 'replace').strip()[:200]}")
    if hashlib.sha256(r.stdout).hexdigest() != sha:
        raise SystemExit(f"carry: {path} at {commit[:7]} is not the file the carry table names"
                         f" ({hashlib.sha256(r.stdout).hexdigest()[:12]}, table {sha[:12]})")
    return r.stdout.decode("utf-8")


def drc(pcb, out):
    """KiCad's DRC report of a saved board, as JSON."""
    out.unlink(missing_ok=True)
    r = subprocess.run([str(mp.CLI), "pcb", "drc", "--severity-all", "--format", "json", "--units", "mm",
                        "-o", str(out), str(pcb)], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=900)
    if not out.exists():
        raise SystemExit(f"carry: kicad-cli wrote no DRC report (exit {r.returncode}): {(r.stdout + r.stderr)[-300:]}")
    return json.loads(out.read_text(encoding="utf-8"))


def prune(board, mine):
    """Remove the tracks and vias of `mine` (UUIDs) that float: those of a cluster of connected
    tracks and vias that reaches no pad and no item outside `mine`. Returns the removed items."""
    board.BuildConnectivity()
    conn = board.GetConnectivity()
    tracks = {t.m_Uuid.AsString(): t for t in board.GetTracks()}
    seen, gone = set(), []
    for u in tracks:
        if u in seen or u not in mine:
            continue
        seen.add(u)
        cluster, queue, held = [], [u], False
        while queue:
            x = queue.pop()
            cluster.append(x)
            held = held or x not in mine or len(conn.GetConnectedPads(tracks[x])) > 0
            for n in conn.GetConnectedTracks(tracks[x]):
                nu = n.m_Uuid.AsString()
                if nu not in seen:
                    seen.add(nu)
                    queue.append(nu)
        if not held:
            gone += [tracks[x] for x in cluster]
    for t in gone:
        board.Remove(t)
    return gone


def compute(tmp):
    """(record, summary lines): the carried routing for the board the documents describe."""
    comps, pins, place, routing, regions, _ = mp.read_inputs(tmp)
    carry = routing["carry"]
    if carry is None:
        raise SystemExit(f"carry: {mp.ROUTING.name} has no carry table")
    session = source(carry["commit"], carry["session"], carry["session_sha256"])
    patch_doc = source(carry["commit"], carry["patch"], carry["patch_sha256"])
    rows = [r for r in route.patch_rows(mp.doc_tables(patch_doc)) if not r["why"].startswith(tuple(carry["skip"]))]
    work = tmp / "carry"
    work.mkdir()
    pcb, pro, _, dru = mp.proj.paths(mp.SRC)
    for f in (pro, dru):                     # DRC reads the rules and the net classes beside the board
        shutil.copyfile(f, work / f.name)
    path = work / pcb.name
    board = mp.base_board(path, comps, pins, place, routing)
    base_digest = route.dsn_digest(mp.router_input(board, routing, regions, tmp))
    base = {t.m_Uuid.AsString(): route.item_key(board, t) for t in board.GetTracks()}
    c_t = c_v = 0
    if "carried" in carry:               # the previous revision had carried copper of its own
        c_t, c_v, _ = route.apply_carried(board, json.loads(source(carry["commit"], carry["carried"], carry["carried_sha256"])))
    s_t, s_v = route.import_session(board, session, mp.sx)
    p_t, p_v, p_r = route.apply_patch(board, rows)
    left = {t.m_Uuid.AsString() for t in board.GetTracks()}
    remove = sorted(key for u, key in base.items() if u not in left)
    mine = left - set(base)
    lines = [f"sources at {carry['commit'][:7]}: carried record {c_t} track segments, {c_v} vias; session {s_t} track segments, {s_v} vias; patch"
             f" ({len(rows)} rows) {p_t} track segments, {p_v} vias, {p_r} item(s) removed, of which"
             f" {len(remove)} drawn by this revision's document"]
    dropped = collections.Counter()
    by_net = collections.Counter()

    def drop(items, why):
        for t in items:
            dropped[why] += 1
            by_net[t.GetNetname()] += 1

    other = collections.Counter()
    for rnd in range(1, MAX_ROUNDS + 1):
        route.fill(board)                    # connectivity and DRC read the plane's fill
        gone = prune(board, mine)
        drop(gone, "floating")
        if gone:
            route.fill(board)
        if not pcbnew.SaveBoard(str(path), board):
            raise SystemExit("carry: pcbnew could not save the board")
        report = drc(path, work / "drc.json")
        live = {t.m_Uuid.AsString(): t for t in board.GetTracks() if t.m_Uuid.AsString() in mine}
        named = {}
        other.clear()
        for v in report.get("violations", []):
            hit = [i["uuid"] for i in v.get("items", []) if i.get("uuid") in live and v["type"] not in DANGLING]
            for u in hit:
                named.setdefault(u, v["type"])
            if not hit:
                other[v["type"]] += 1
        for u, typ in named.items():
            board.Remove(live[u])
            drop([live[u]], typ)
        print(f"round {rnd}: {len(gone)} floating, {len(named)} named by DRC; {len(live) - len(named)} stand")
        sys.stdout.flush()
        if not named:
            break
    else:
        raise SystemExit(f"carry: still dropping after {MAX_ROUNDS} rounds")
    kept = [t for t in board.GetTracks() if t.m_Uuid.AsString() in mine]
    tracks, vias = route.carried_items(board, kept)
    floating = dropped.pop("floating", 0)
    by_drc = sum(dropped.values())
    # DRC's own split of what it names is not in the record: one run calls a short shorting_items
    # and the next solder_mask_bridge, and --check compares the record with the file
    record = dict(commit=carry["commit"], carried_sha256=carry.get("carried_sha256"), session_sha256=carry["session_sha256"],
                  patch_sha256=carry["patch_sha256"], skip=carry["skip"], base_dsn_sha256=base_digest,
                  dropped=dict(drc=by_drc, floating=floating), remove=[list(k) for k in remove],
                  tracks=tracks, vias=vias)
    lines += [f"kept {len(tracks)} track segments and {len(vias)} vias; dropped {floating + by_drc}: {floating}"
              f" floating, {by_drc} named by DRC (in this run: "
              + (", ".join(f"{k} {n}" for k, n in sorted(dropped.items())) or "none") + ")",
              "nets that lost copper: " + ", ".join(f"{n} {c}" for n, c in sorted(by_net.items(), key=lambda kv: (-kv[1], kv[0]))),
              f"left open: {len(report.get('unconnected_items', []))} connection(s) by DRC; DRC violations that"
              f" name no carried item: " + (", ".join(f"{k} {n}" for k, n in sorted(other.items())) or "none")]
    return record, lines


def dumps(record):
    """The record as JSON text, the three item lists one item to a line."""
    out = []
    for k, v in record.items():
        if k in LISTS and v:
            out.append(f' {json.dumps(k)}: [\n' + ",\n".join("  " + json.dumps(r) for r in v) + "\n ]")
        else:
            out.append(f" {json.dumps(k)}: {json.dumps(v)}")
    text = "{\n" + ",\n".join(out) + "\n}\n"
    if json.loads(text) != record:
        raise SystemExit("carry: the record does not survive its own JSON")
    return text


def differs(record, old):
    """None if the text `old` is the record as dumps() writes it; else what differs."""
    if old == dumps(record):
        return None
    try:
        was = json.loads(old)
    except ValueError:
        return "the file is not JSON"
    if not isinstance(was, dict):
        return "the file is not a record"
    keys = [k for k in dict.fromkeys([*record, *was]) if was.get(k) != record.get(k)]
    return (", ".join(keys) + " differ") if keys else "the layout of the text differs"


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[1:] not in ([], ["--check"]):
        raise SystemExit("usage: carry.py [--check]")
    with tempfile.TemporaryDirectory() as tmp:
        record, lines = compute(pathlib.Path(tmp))
    print("\n".join(lines))
    rel = mp.CARRIED.relative_to(mp.ROOT).as_posix()
    if argv[1:] == ["--check"]:
        if not mp.CARRIED.exists():
            print(f"FAIL: no {rel}")
            return 1
        what = differs(record, mp.CARRIED.read_text(encoding="utf-8"))
        print(f"PASS: {rel} is the record this run makes" if what is None else
              f"FAIL: {rel} is not the record this run makes: {what}")
        return 0 if what is None else 1
    mp.CARRIED.write_text(dumps(record), encoding="utf-8", newline="\n")
    print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
