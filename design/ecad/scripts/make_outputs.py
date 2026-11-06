"""Write the Rev0.4 manufacturing candidate from the KiCad project (issue #6 P5; CLAUDE.md 2, 8).

Run with KiCad's own Python from the repository root, after make_pcb.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_outputs.py [--no-check]

Output: manufacturing/working/rev0.4/, rebuilt on every run. It is a WIP candidate: never
orderable (CLAUDE.md 2, manufacturing/working/), and not a release. Every file is named
<Product>_<Board>_<Revision>_<Artifact> (CLAUDE.md 2):
- _Gerber.zip: the Gerbers of the 4 copper layers, paste, silkscreen, mask and Edge.Cuts with
  Protel extensions, soldermask subtracted from the silkscreen, plus the Excellon drill
  files (PTH and NPTH apart, mm, decimal, alternate oval mode, absolute origin) and their
  Gerber X2 drill maps: JLCPCB's KiCad settings (help pages read 2026-11-06). Vias are
  tented by the board's own setting.
- _BOM_JLCPCB.csv: Comment, Designator, Footprint, JLCPCB Part #: one row per LCSC part of
  every footprint with an LCSC field that is not excluded from the BOM, the machine-placed
  parts (D13).
- _CPL_JLCPCB.csv: Designator, Mid X, Mid Y, Layer, Rotation for the same parts: the
  footprint origin in the board frame (lower-left corner, y up, mm), Top, KiCad's
  orientation (counter-clockwise, degrees).
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

What it CANNOT see: whether JLCPCB reads the files as meant. The upload's DFM, part mapping
and placement preview (CLAUDE.md 8, JLCPCB gate) are not run: no login or order (issue #6).
"""
import csv
import hashlib
import io
import json
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
OUT = ROOT / "manufacturing" / "working" / "rev0.4"
NICK = "usb-power-hub"
PREFIX = "UsbPowerHub_Main_Rev0.4"
CLI = pathlib.Path(sys.executable).resolve().parents[1] / "bin" / "kicad-cli.exe"
ORIGIN = (50.0, 122.0)                     # the board's lower-left corner on the sheet
LAYERS = "F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
RENDER = ("1600", "1152")                  # 100 x 72 mm at 16 px/mm
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
BOM_HEAD = ["Comment", "Designator", "Footprint", "JLCPCB Part #"]
CPL_HEAD = ["Designator", "Mid X", "Mid Y", "Layer", "Rotation"]
HAND_HEAD = ["Designator", "Qty", "Manufacturer", "MPN", "Akizuki", "Class", "Footprint"]
SOURCES = [f"design/ecad/source/{NICK}.kicad_pcb", f"design/ecad/source/{NICK}.kicad_pro"]
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
    groups = {}
    for fp in machine:
        key = (fp.GetValue(), fp.GetFPID().GetLibItemName().wx_str(), field(fp, "LCSC"))
        groups.setdefault(key, []).append(fp.GetReference())
    rows = [[v, ",".join(refs), name, lcsc] for (v, name, lcsc), refs in groups.items()]
    return csv_bytes(BOM_HEAD, sorted(rows, key=lambda r: natural(r[1].split(",")[0])))


def cpl(machine):
    rows = []
    for fp in machine:
        x = pcbnew.ToMM(fp.GetPosition().x) - ORIGIN[0]
        y = ORIGIN[1] - pcbnew.ToMM(fp.GetPosition().y)
        rot = fp.GetOrientationDegrees() % 360
        rows.append([fp.GetReference(), f"{x:.4f}", f"{y:.4f}", "Top", f"{rot:g}"])
    return csv_bytes(CPL_HEAD, rows)


def hand_list(hand):
    rows = [[fp.GetReference(), "1", field(fp, "Manufacturer"), field(fp, "MPN"), field(fp, "Akizuki"),
             field(fp, "Class"), fp.GetFPID().GetLibItemName().wx_str()] for fp in hand]
    return csv_bytes(HAND_HEAD, rows)


# ---- exports -----------------------------------------------------------------------------------
def gerber_zip(pcb, tmp):
    g = tmp / "gerber"
    status, log = cli("pcb", "export", "gerbers", "-l", LAYERS, "--subtract-soldermask", "-o", g, pcb)
    status2, log2 = cli("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "absolute",
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
        "# USB Power-Control Hub Rev0.4 — manufacturing candidate",
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
        "| Vias | tented front and back (board setting) |",
        "| Assembly side | Top only (REQ-MFG-01) |",
        f"| Machine-placed parts | {len(machine)} footprints, {len(lcsc)} LCSC parts; Extended: {', '.join(extended) or 'none'} (D29, D31) |",
        f"| Hand-soldered parts | {len(hand)} (`{PREFIX}_HandSolder.csv`), in neither BOM nor CPL |",
        f"| Not populated (BOM-excluded) | {len(dnp)}: {' '.join(dnp)} |",
        f"| ERC | {count(erc, 'violations')} violations |",
        f"| DRC | {count(drc, 'violations')} violations, {count(drc, 'unconnected_items')} unconnected items, "
        f"{count(drc, 'schematic_parity')} schematic-parity items |",
        "| JLCPCB DFM, part mapping, placement preview | not run: no upload (issue #6) |",
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
        "- The CPL's origin is the board's lower-left corner and its angles are KiCad's; JLCPCB's",
        "  page states neither the origin nor its own model angles, which differ from a CPL angle",
        "  (easy-stick 14.18). The placement preview is the evidence for every part's position,",
        "  pin 1 and polarity (CLAUDE.md 4.2).",
        "- JLCPCB's DFM check, part mapping and placement preview have not seen this set; they",
        "  are the JLCPCB gate (CLAUDE.md 8), and an upload is the user's decision.",
        "- No footprint is proven on a board or in the JLCPCB preview; no order-time stock check",
        "  has been done (CLAUDE.md 0).",
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
