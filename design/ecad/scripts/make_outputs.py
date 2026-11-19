"""Write the Rev0.7 manufacturing candidate from the KiCad project (issue #6 P5; CLAUDE.md 2, 8).

Run with KiCad's own Python from the repository root, after make_pcb.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_outputs.py [--no-check]

Output: manufacturing/working/rev0.7/, rebuilt on every run. It is a WIP candidate: never
orderable (CLAUDE.md 2, manufacturing/working/), and not a release. Every file is named
<Product>_<Board>_<Revision>_<Artifact> (CLAUDE.md 2):
- _Gerber.zip: the Gerbers of the 4 copper layers, paste, silkscreen, mask and Edge.Cuts with
  Protel extensions, soldermask subtracted from the silkscreen, plus the Excellon drill
  files (PTH and NPTH apart, mm, decimal, alternate oval mode) and their Gerber X2 drill
  maps: JLCPCB's KiCad settings (help pages read 2026-11-06), except the origin: the
  Gerbers and the drills use the board's auxiliary origin, its lower-left corner, as the CPL
  does. With the sheet's absolute origin JLCPCB's placement preview drew every part 50 mm
  left of and 122 mm above the board (quote of 2026-11-11, issue #6). Vias are tented by the
  board's own setting.
- _BOM_JLCPCB.csv: Comment, Designator, Footprint, JLCPCB Part #: one row per LCSC part of
  every footprint with an LCSC field that is not excluded from the BOM, the machine-placed
  parts (D13). A part on two footprints is one row, with the first designator's Comment and
  Footprint: JLCPCB's part mapping does not select two rows of one LCSC number.
- _CPL_JLCPCB.csv: Designator, Mid X, Mid Y, Layer, Rotation for the same parts: the
  footprint origin in the board frame (lower-left corner, y up, mm) plus the part's JLCPCB
  model shift (turned with the footprint), Top, KiCad's orientation plus the part's JLCPCB
  model rotation (counter-clockwise, degrees). design/ecad/jlcpcb_model_frame.json holds
  both: JLCPCB's models are not drawn at KiCad's zero (the placement preview of 2026-11-11
  showed the CH335F, the SOIC-8s, the SOT-23s and the SOT-223 90 or 180 degrees off, issue
  #6) and not about the footprint's origin (the preview of 2026-11-13 showed the USB-C
  receptacle's model 1.375 mm toward its mouth of the footprint's centre, issue #8).
- _HandSolder.csv: the parts with an Akizuki field, which the user solders (D13, V-MFG-01);
  they are in neither the BOM nor the CPL.
- _Schematic.pdf, _Assembly_Top.pdf (F.Fab and the outline with the title block: the
  designators the silkscreen leaves out), _Preview_Top.png and _Preview_Bottom.png
  (kicad-cli pcb render), _ERC.json and _DRC.json (kicad-cli, every severity).
- RELEASE_MANIFEST.md (state WIP) and SHA256SUMS.txt.
A re-run writes the same bytes: the creation dates kicad-cli writes are replaced by
1980-01-01 00:00:00 (same length, so a PDF's offsets hold), the reports' paths are made
relative and their dates fixed, and the zip carries fixed times. manufacturing/working/ is
not tracked (.gitignore: disposable candidates), so the manifest records each source file's
SHA-256 instead of a Git commit, and check_outputs.py fails a set older than its sources.

Then it runs check_outputs.py in a new process, unless --no-check.
Exit status: 0 = written and checked; 1 = a check failed or an export failed.

What it CANNOT see: whether JLCPCB reads the files as meant. The uploads of Rev0.4 (2026-11-11
and -12: DFM, part mapping, placement preview, quote; issues #6 and #8) are recorded in
manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md (and r02's) with the SHA-256 of the Gerber
zip, BOM and CPL they saw; Rev0.5's (2026-11-13, issue #8) in manufacturing/releases/rev0.5/
r01/JLCPCB_REVIEW.md and r02's; Rev0.6's (2026-11-19, issue #13) in manufacturing/releases/
rev0.6/r01/JLCPCB_REVIEW.md; Rev0.7 has had none. This script does not read those files: a change to a source, to
this script or to jlcpcb_model_frame.json that changes one of those three hashes makes a review
stale. The table's shift for the receptacle C2765186 (J1-J4) is what the placement preview
showed, to about 0.04 mm; whether JLCPCB's pick-and-place puts the part where its viewer draws
the model is not something any file here shows.
"""
import csv
import hashlib
import io
import json
import math
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "design" / "ecad" / "source"
FRAMES = ROOT / "design" / "ecad" / "jlcpcb_model_frame.json"
OUT = ROOT / "manufacturing" / "working" / "rev0.7"
NICK = "usb-power-hub"
PREFIX = "UsbPowerHub_Main_Rev0.7"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
ORIGIN = (50.0, 122.0)                     # the board's lower-left corner on the sheet
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
RENDER = ("1600", "1152")                  # 100 x 72 mm at 16 px/mm
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
BOM_HEAD = ["Comment", "Designator", "Footprint", "JLCPCB Part #"]
CPL_HEAD = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
HAND_HEAD = ["Designator", "Qty", "Manufacturer", "MPN", "Akizuki", "Class", "Footprint"]
SOURCES = [f"design/ecad/source/{NICK}.{ext}" for ext in ("kicad_pcb", "kicad_pro", "kicad_dru")]
DATES = [
    (re.compile(rb"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d\d:\d\d"), b"1980-01-01T00:00:00+00:00"),
    (re.compile(rb"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d[+-]\d{4}"), b"1980-01-01T00:00:00+0000"),
    (re.compile(rb"date \d{4}-\d\d-\d\d \d\d:\d\d:\d\d"), b"date 1980-01-01 00:00:00"),
    (re.compile(rb"\(D:\d{14}"), b"(D:19800101000000"),
]


def cli(*args):
    r = subprocess.run([str(CLI), *map(str, args)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=900)
    return r.returncode, r.stdout + r.stderr


def fixed(data):
    for pat, rep in DATES:
        data = pat.sub(lambda m: rep, data)
    return data


def natural(ref):
    m = re.match(r"([A-Z]+)(\d+)$", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def csv_bytes(head, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n", quoting=csv.QUOTE_ALL)
    w.writerow(head)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def field(fp, name):
    return fp.GetFieldText(name) if fp.HasFieldByName(name) else ""


# ---- the parts lists ---------------------------------------------------------------------------
def parts(board):
    machine, hand = [], []
    for fp in board.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM:
            continue
        if field(fp, "LCSC"):
            machine.append(fp)
        elif field(fp, "Akizuki"):
            hand.append(fp)
        else:
            raise SystemExit(f"{fp.GetReference()}: in the BOM, with neither an LCSC nor an Akizuki field")
    return sorted(machine, key=lambda f: natural(f.GetReference())), sorted(hand, key=lambda f: natural(f.GetReference()))


def bom(machine):
    """One row per LCSC part. Comment and Footprint come from the row's first designator (natural
    order): JLCPCB's part mapping leaves two rows with one LCSC number unselected ("Multiple
    lines in the BOM have been matched to the same part", quote of 2026-11-11, issue #6), so the
    510 ohm 0805 of R14 and of the Kelvin shunts RS12/RS22 (C17734) share one row. The CPL names
    no footprint, so the placement does not depend on the row's footprint name."""
    groups = {}
    for fp in machine:
        groups.setdefault(field(fp, "LCSC"), []).append(fp)
    rows = []
    for lcsc, fps in groups.items():
        first = fps[0]                       # `machine` is in natural designator order
        rows.append([first.GetValue(), ",".join(f.GetReference() for f in fps),
                     first.GetFPID().GetLibItemName().wx_str(), lcsc])
    return csv_bytes(BOM_HEAD, sorted(rows, key=lambda r: natural(r[1].split(",")[0])))


def model_frames():
    """{LCSC: (rotation degrees, (dx, dy) mm)} from design/ecad/jlcpcb_model_frame.json (see its _doc)."""
    table = json.loads(FRAMES.read_text(encoding="utf-8"))["parts"]
    return {lcsc: (float(v.get("add", 0)), tuple(float(c) for c in v.get("shift", (0.0, 0.0))))
            for lcsc, v in table.items()}


def turned(dx, dy, degrees):
    """(dx, dy) in a footprint's own frame (x right, y down) as a vector of the board's y-down frame,
    for a footprint turned `degrees` counter-clockwise on the screen. KiCad places a pad this way:
    test_check_outputs.py compares it with every pad of the board, at 0, 90, 180 and 270 degrees."""
    a = math.radians(degrees)
    return dx * math.cos(a) + dy * math.sin(a), -dx * math.sin(a) + dy * math.cos(a)


def cpl(machine):
    """Mid = the footprint's origin plus its part's JLCPCB model shift turned with the footprint;
    Rotation = the footprint's KiCad orientation plus its part's JLCPCB model rotation."""
    frames = model_frames()
    rows = []
    for fp in machine:
        add, (sx, sy) = frames.get(field(fp, "LCSC"), (0.0, (0.0, 0.0)))
        kx, ky = turned(sx, sy, fp.GetOrientationDegrees())
        x = pcbnew.ToMM(fp.GetPosition().x) + kx - ORIGIN[0]
        y = ORIGIN[1] - (pcbnew.ToMM(fp.GetPosition().y) + ky)
        rot = (fp.GetOrientationDegrees() + add) % 360
        rows.append([fp.GetReference(), f"{x:.4f}", f"{y:.4f}", "Top", f"{rot:g}"])
    return csv_bytes(CPL_HEAD, rows)


def hand_list(hand):
    rows = [[fp.GetReference(), "1", field(fp, "Manufacturer"), field(fp, "MPN"), field(fp, "Akizuki"),
             field(fp, "Class"), fp.GetFPID().GetLibItemName().wx_str()] for fp in hand]
    return csv_bytes(HAND_HEAD, rows)


# ---- exports -----------------------------------------------------------------------------------
def gerber_zip(pcb, tmp):
    g = tmp / "gerber"
    status, log = cli("pcb", "export", "gerbers", "-l", LAYERS, "--subtract-soldermask", "--use-drill-file-origin",
                        "-o", g, pcb)
    status2, log2 = cli("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot",
                        "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
                        "--excellon-oval-format", "alternate", "--excellon-separate-th",
                        "--generate-map", "--map-format", "gerberx2", "-o", f"{g}/", pcb)
    files = sorted(p for p in g.iterdir() if p.suffix != ".gbrjob")
    if status or status2 or len(files) != 15:
        raise SystemExit(f"Gerber/drill export: exit {status}/{status2}, {len(files)} files:\n{log}\n{log2}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            info = zipfile.ZipInfo(p.name.replace(f"{NICK}-", f"{PREFIX}_"), FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, fixed(p.read_bytes()))
    return buf.getvalue()


def pdf(kind, args, tmp, name):
    """kicad-cli <kind> export pdf; args end with the input file."""
    out = tmp / name
    status, log = cli(kind, "export", "pdf", "-o", out, *args)
    if not out.exists():
        raise SystemExit(f"{name}: kicad-cli exit {status}: {log[-400:]}")
    return fixed(out.read_bytes())


def render(pcb, side, tmp):
    out = tmp / f"render-{side}.png"
    status, log = cli("pcb", "render", "--side", side, "--width", RENDER[0], "--height", RENDER[1],
                      "--background", "opaque", "-o", out, pcb)
    if not out.exists():
        raise SystemExit(f"render {side}: kicad-cli exit {status}: {log[-400:]}")
    return out.read_bytes()


def report(kind, args, path, tmp):
    out = tmp / f"{kind}.json"
    status, log = cli(*args, "--format", "json", "--severity-all", "-o", out, path)
    if not out.exists():
        raise SystemExit(f"{kind}: kicad-cli exit {status}: {log[-400:]}")
    data = json.loads(out.read_text(encoding="utf-8"))
    data["source"] = pathlib.Path(data.get("source", "")).name
    data["date"] = "1980-01-01T00:00:00+0000"
    return (json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"), data


def count(data, key):
    if key == "violations" and "sheets" in data:          # the ERC report lists them per sheet
        return sum(len(s.get("violations", [])) for s in data["sheets"])
    return len(data.get(key, []))


# ---- the manifest ------------------------------------------------------------------------------
def sha(data):
    return hashlib.sha256(data).hexdigest()


def manifest(board, pcb, machine, hand, files, erc, drc, sources):
    tb = board.GetTitleBlock()
    m = re.search(r'\(copper_finish "([^"]*)"\)', pcb.read_text(encoding="utf-8"))
    finish = m.group(1) if m else "none"   # the stackup descriptor is not reachable from Python
    ds = board.GetDesignSettings()
    lcsc = sorted({field(fp, "LCSC") for fp in machine})
    extended = sorted({field(fp, "LCSC") for fp in machine if not field(fp, "Class").startswith("Basic")})
    dnp = sorted((fp.GetReference() for fp in board.GetFootprints()
                  if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_BOM), key=natural)
    lines = [
        "# USB Power-Control Hub Rev0.7 — manufacturing candidate",
        "",
        "> **State: WIP — MANUFACTURING PROHIBITED.** A candidate set in `manufacturing/working/`:",
        "> never orderable, not a release (CLAUDE.md 2, 3). Written by",
        "> `design/ecad/scripts/make_outputs.py`; `check_outputs.py` checks it.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| PCB revision | {tb.GetRevision()} |",
        "| Release number | none: a working candidate, not a release |",
        "| State | WIP |",
        f"| ECAD | KiCad {pcbnew.GetMajorMinorPatchVersion()}, project `design/ecad/source/{NICK}.kicad_pro` |",
        "| Git commit | not recorded: `manufacturing/working/` is not tracked (.gitignore); the set is regenerated from the sources whose SHA-256 is below |",
        f"| Dimensions | 100 × 72 mm (D24), {pcbnew.ToMM(ds.GetBoardThickness()):g} mm thick |",
        f"| Layers | {board.GetCopperLayerCount()} (D10) |",
        "| Stackup | JLC04161H-7628 (D27), named on the order |",
        "| Copper | outer 0.035 mm, inner 0.0152 mm (the board's stackup) |",
        "| Impedance control | not ordered for the prototype (D27) |",
        f"| Finish | leaded HASL (D30; board setting `{finish}`) |",
        "| Mask, silkscreen colour | not decided; no decision records them |",
        "| Vias | 0.45 mm copper, 0.30 mm drill: JLCPCB's standard class \"0.3mm/(0.4/0.45mm)\" (issue #8); tented front and back (board setting); JLCPCB's form offers Plugged, not Tented, at $0.00 for this board (2026-11-12) |",
        "| Assembly side | Top only (REQ-MFG-01) |",
        f"| Machine-placed parts | {len(machine)} footprints, {len(lcsc)} LCSC parts; Extended: {', '.join(extended) or 'none'} (D29, D31, D37) |",
        f"| Hand-soldered parts | {len(hand)} (`{PREFIX}_HandSolder.csv`), in neither BOM nor CPL |",
        f"| Not populated (BOM-excluded) | {len(dnp)}: {' '.join(dnp)} |",
        f"| ERC | {count(erc, 'violations')} violations |",
        f"| DRC | {count(drc, 'violations')} violations, {count(drc, 'unconnected_items')} unconnected items, "
        f"{count(drc, 'schematic_parity')} schematic-parity items |",
        "| JLCPCB DFM, part mapping, placement preview | none for Rev0.7. Rev0.6's review (`manufacturing/releases/rev0.6/r01/JLCPCB_REVIEW.md`), Rev0.5's (`manufacturing/releases/rev0.5/r02/JLCPCB_REVIEW.md`, r01's beside it) and Rev0.4's (`manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md`, r02's beside it) hold only for the Gerber zip, BOM and CPL whose SHA-256 they record: they saw other files and do not carry over |",
        "| Firmware | none |",
        "| JLCPCB order number | none |",
        "| Approver, approval time | none: WIP |",
        "",
        "## Files",
        "",
        "| File | Content |",
        "|---|---|",
    ]
    lines += [f"| `{name}` | {what} |" for name, what in files]
    lines += ["", "## Sources", "", "| File | SHA-256 |", "|---|---|"]
    lines += [f"| `{rel}` | `{digest}` |" for rel, digest in sources]
    lines += [
        "",
        "## Residual risks",
        "",
        "- The CPL's origin is the board's lower-left corner. Its Mid is the footprint's origin, plus the",
        "  JLCPCB model shift of design/ecad/jlcpcb_model_frame.json for the receptacle C2765186 (J1-J4),",
        "  and its angles are KiCad's plus the model rotation of that table (easy-stick 14.18). The table",
        "  holds what JLCPCB's placement previews showed: the rotations on 2026-11-11 (Rev0.4,",
        "  manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md) and the receptacle's shift on 2026-11-13",
        "  (Rev0.5, manufacturing/releases/rev0.5/r01/JLCPCB_REVIEW.md), to about 0.04 mm. A preview is",
        "  the drawing of JLCPCB's model, not its pick-and-place; JLCPCB checks the final placement again",
        "  in its DFM Analysis 4-6 hours after an order.",
        "- The receptacle's land is the maker's, drawn for a 0.80 mm board; this one is 1.6 mm",
        "  (OI-33). Whether the shell legs reach through the plated slots and the joints carry the",
        "  plug's insertion force shows only on the first board (V-MFG-03, V-MECH-01).",
        "- JLCDFM has not read this Gerber. Its Danger items on Rev0.5's (via annular ring of the",
        "  0.30 mm vias, THT-to-SMD distance, mask opening exposing a trace, pad spacing, silkscreen",
        "  over a plugged via, the receptacles' plated-slot width) are judged one by one in",
        "  manufacturing/releases/rev0.5/r02/JLCPCB_REVIEW.md: most are JLCDFM's own reading of the",
        "  geometry, the slot width is a decision for the user. The lands and the via class are the",
        "  same here, so the same items are to be expected; JLCPCB's own DFM at order time can differ.",
        "- No footprint is proven on a board; no order-time stock check has been done (CLAUDE.md 0).",
        "- The open issues of CLAUDE.md 11 stand; the set is not orderable until each is closed.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if argv[1:] not in ([], ["--no-check"]):
        raise SystemExit("usage: make_outputs.py [--no-check]")
    pcb, sch = SRC / f"{NICK}.kicad_pcb", SRC / f"{NICK}.kicad_sch"
    prl = SRC / f"{NICK}.kicad_prl"
    prl_before = prl.exists()
    board = pcbnew.LoadBoard(str(pcb))
    machine, hand = parts(board)
    sheets = sorted(SRC.glob("*.kicad_sch"))
    sources = [(p.relative_to(ROOT).as_posix(), sha(p.read_bytes()))
               for p in sorted([ROOT / s for s in SOURCES] + sheets)]
    out = {}
    with tempfile.TemporaryDirectory(prefix="outputs-") as tmp:
        tmp = pathlib.Path(tmp)
        out["Gerber.zip"] = (gerber_zip(pcb, tmp), "Gerbers (Protel extensions), Excellon drill files and drill maps")
        out["BOM_JLCPCB.csv"] = (bom(machine), "JLCPCB BOM of the machine-placed parts")
        out["CPL_JLCPCB.csv"] = (cpl(machine), "JLCPCB placement list, board frame, mm, degrees counter-clockwise")
        out["HandSolder.csv"] = (hand_list(hand), "the parts the user solders by hand (D13)")
        out["Schematic.pdf"] = (pdf("sch", [sch], tmp, "sch.pdf"), "the schematic, every sheet")
        out["Assembly_Top.pdf"] = (pdf("pcb", ["--layers", "F.Fab,Edge.Cuts", "--include-border-title",
                                               "--mode-single", "--exclude-value", pcb], tmp, "asm.pdf"),
                                   "assembly drawing: F.Fab designators and outline, title block")
        out["Preview_Top.png"] = (render(pcb, "top", tmp), "3D render, top")
        out["Preview_Bottom.png"] = (render(pcb, "bottom", tmp), "3D render, bottom")
        erc_bytes, erc = report("erc", ["sch", "erc"], sch, tmp)
        drc_bytes, drc = report("drc", ["pcb", "drc", "--schematic-parity"], pcb, tmp)
        out["ERC.json"] = (erc_bytes, "kicad-cli ERC report, every severity")
        out["DRC.json"] = (drc_bytes, "kicad-cli DRC report with schematic parity, every severity")
    files = [(f"{PREFIX}_{k}", v[1]) for k, v in out.items()]
    data = {f"{PREFIX}_{k}": v[0] for k, v in out.items()}
    data["RELEASE_MANIFEST.md"] = manifest(board, pcb, machine, hand, files, erc, drc, sources)
    data["SHA256SUMS.txt"] = "".join(f"{sha(b)}  {n}\n" for n, b in sorted(data.items())).encode("utf-8")
    if OUT.exists():
        for p in OUT.iterdir():
            if p.is_file() and p.name not in data:
                p.unlink()                   # the directory holds only this script's output
    OUT.mkdir(parents=True, exist_ok=True)
    for name, b in data.items():
        (OUT / name).write_bytes(b)
    if prl.exists() and not prl_before:
        prl.unlink()
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}: {len(data)} files; {len(machine)} machine-placed,"
          f" {len(hand)} hand-soldered; ERC {count(erc, 'violations')}, DRC {count(drc, 'violations')}"
          f" violations, {count(drc, 'unconnected_items')} unconnected")
    if argv[1:] == ["--no-check"]:
        return 0
    sys.stdout.flush()
    return subprocess.run([sys.executable, "-I", "-B", str(HERE / "check_outputs.py")]).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
