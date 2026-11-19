"""Write the lid's manufacturing candidate from its KiCad board (issue #11; CLAUDE.md 2, 7).

Run with KiCad's own Python from the repository root, after make_lid.py:

    "<KiCad 9.0>/bin/python.exe" -I -B design/mechanical/scripts/make_lid_outputs.py
        [--src DIR] [--out DIR] [--no-check]

Output: manufacturing/working/lid-rev0.1/ (--out), rebuilt on every run. It is a WIP
candidate: never orderable (CLAUDE.md 2, manufacturing/working/), not a release, and not
tracked (.gitignore). Every file is named <Product>_<Board>_<Revision>_<Artifact>:
- _Gerber.zip: the Gerbers of the 2 copper layers, both silkscreens, both masks and Edge.Cuts
  with Protel extensions, soldermask subtracted from the silkscreen, the Excellon drill files
  (plated and unplated apart, mm, decimal) and their Gerber X2 drill maps. The settings are
  the main board's (design/ecad/scripts/make_outputs.py), the auxiliary origin included: the
  lid's lower-left corner is (0, 0), as in the lid's interface.
- _Fabrication_Top.pdf: the outline, the holes, the top silkscreen and the top mask openings
  with the title block, at 1:1: print it to see the legend at its real size.
- _Preview_Top.png, _Preview_Bottom.png: kicad-cli's render of the board.
- _DRC.json: kicad-cli's DRC report, every severity.
- RELEASE_MANIFEST.md (state WIP) and SHA256SUMS.txt.
The board and its project are copied into a temporary directory and exported from there, so
nothing in --src is touched. A re-run writes the same bytes: see `fixed` in make_outputs.py.
The manifest records the SHA-256 of the board and of its project file, and the board's own
record of its inputs; check_lid.py fails a set older than its board (L12).

The export helpers (kicad-cli call, creation-date scrubbing, PDF, render, report) are the
main board's: this script loads design/ecad/scripts/make_outputs.py by path and uses them,
so that the rule for a reproducible export has one home.

Then it runs check_lid.py --outputs in a new process, unless --no-check.
Exit status: 0 = written and checked; 1 = a check failed or an export failed.

What it CANNOT see: whether JLCPCB reads the files as meant. No file of the lid has been
uploaded; JLCDFM and a quote come at the JLCPCB gate, after the user has accepted the legend.
"""
import argparse
import importlib.util
import io
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

import pcbnew

HERE = pathlib.Path(__file__).resolve().parent


def _load(path):
    s = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(s)
    s.loader.exec_module(mod)
    return mod


spec = _load(HERE / "lid_spec.py")
K = _load(spec.ROOT / "design" / "ecad" / "scripts" / "make_outputs.py")   # cli, fixed, pdf, render, report, count, sha
LAYERS = "F.Cu,B.Cu,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
GERBER_FILES = 11                          # 7 Gerbers, 2 drill files, 2 drill maps


def gerber_zip(pcb, tmp):
    g = tmp / "gerber"
    status, log = K.cli("pcb", "export", "gerbers", "-l", LAYERS, "--subtract-soldermask", "--use-drill-file-origin",
                        "-o", g, pcb)
    status2, log2 = K.cli("pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot",
                          "--excellon-units", "mm", "--excellon-zeros-format", "decimal",
                          "--excellon-oval-format", "alternate", "--excellon-separate-th",
                          "--generate-map", "--map-format", "gerberx2", "-o", f"{g}/", pcb)
    files = sorted(p for p in g.iterdir() if p.suffix != ".gbrjob") if g.is_dir() else []
    if status or status2 or len(files) != GERBER_FILES:
        raise SystemExit(f"Gerber/drill export: exit {status}/{status2}, {len(files)} files:\n{log}\n{log2}")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            info = zipfile.ZipInfo(p.name.replace(f"{spec.NICK}-", f"{spec.PREFIX}_"), K.FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, K.fixed(p.read_bytes()))
    return buf.getvalue()


def manifest(board, files, drc, sources):
    tb = board.GetTitleBlock()
    ds = board.GetDesignSettings()
    box = board.GetBoardEdgesBoundingBox()
    line = max((d.GetWidth() for d in board.GetDrawings() if d.GetLayer() == pcbnew.Edge_Cuts), default=0)
    width, height = (pcbnew.ToMM(v - line) for v in (box.GetWidth(), box.GetHeight()))
    holes = {}
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            d = pcbnew.ToMM(pad.GetDrillSize().x)
            holes[d] = holes.get(d, 0) + 1
    inputs = next((tb.GetComment(i) for i in range(9) if tb.GetComment(i).startswith(spec.DIGEST_TAG)), "none")
    lines = [
        f"# {spec.PRODUCT} Lid {tb.GetRevision()} — manufacturing candidate",
        "",
        "> **State: WIP — MANUFACTURING PROHIBITED.** A candidate set in `manufacturing/working/`:",
        "> never orderable, not a release (CLAUDE.md 2, 3). Written by",
        "> `design/mechanical/scripts/make_lid_outputs.py`; `check_lid.py --outputs` checks it.",
        "",
        "| Item | Value |",
        "|---|---|",
        f"| PCB revision | {tb.GetRevision()} |",
        "| Release number | none: a working candidate, not a release |",
        "| State | WIP |",
        f"| ECAD | KiCad {pcbnew.GetMajorMinorPatchVersion()}, project `design/mechanical/lid/{spec.NICK}.kicad_pro` |",
        "| Git commit | not recorded: `manufacturing/working/` is not tracked (.gitignore); the set is regenerated from the sources whose SHA-256 is below |",
        f"| Inputs | `{inputs}`: the lid document's tables and the lid's interface (check_lid.py L01) |",
        f"| Dimensions | {width:g} × {height:g} mm, {pcbnew.ToMM(ds.GetBoardThickness()):g} mm thick |",
        f"| Layers | {board.GetCopperLayerCount()} |",
        "| Stackup | none named: the lid carries no signal (K1) |",
        "| Copper | 1 oz on both sides: one pour per side, no net, closed in by solder mask (K2) |",
        "| Impedance control | none |",
        "| Finish | not decided: no copper is bare, so any finish does (K7) |",
        "| Mask, silkscreen colour | not decided (K7) |",
        "| Holes | " + ", ".join(f"{n} × {d:g} mm" for d, n in sorted(holes.items())) + ", all unplated (K4); no via |",
        "| Assembly | none: a bare board, no BOM and no CPL |",
        f"| DRC | {K.count(drc, 'violations')} violations, {K.count(drc, 'unconnected_items')} unconnected items |",
        "| JLCPCB DFM, quote | not run: no file of the lid has been uploaded |",
        "| Order number | the bottom silkscreen carries `JLCJLCJLCJLC` (K8); the order form's option is not read yet |",
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
    lines += [f"| `{name}` | `{digest}` |" for name, digest in sources]
    lines += [
        "",
        "## Residual risks",
        "",
        "- The legend is a first proposal; the user has not seen it on a board.",
        "- Light: how much of an LED's light the bare FR-4 window passes, and how much shows through",
        "  the solder mask beside the copper, is seen only on a built lid.",
        "- JLCPCB has not seen the files: no JLCDFM run, no quote, colours and finish not chosen.",
        "- The enclosure the lid closes is not printed (ENCLOSURE_Rev0.1.md): the holes' positions",
        "  are the enclosure's drawing, not a measured part.",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", type=pathlib.Path, default=spec.SOURCE)
    ap.add_argument("--out", type=pathlib.Path, default=spec.WORKING)
    ap.add_argument("--no-check", action="store_true")
    args = ap.parse_args(argv[1:])
    names = [f"{spec.NICK}.{ext}" for ext in ("kicad_pcb", "kicad_pro")]
    sources = [(n, K.sha((args.src / n).read_bytes())) for n in names]
    out = {}
    with tempfile.TemporaryDirectory(prefix="lidoutputs-") as tmp:
        tmp = pathlib.Path(tmp)
        work = tmp / "board"
        work.mkdir()
        for n in names:
            shutil.copy2(args.src / n, work / n)
        pcb = work / names[0]
        board = pcbnew.LoadBoard(str(pcb))
        out["Gerber.zip"] = (gerber_zip(pcb, tmp), "Gerbers (Protel extensions), Excellon drill files and drill maps")
        out["Fabrication_Top.pdf"] = (K.pdf("pcb", ["--layers", "Edge.Cuts,F.SilkS,F.Mask", "--include-border-title",
                                                    "--mode-single", pcb], tmp, "fab.pdf"),
                                      "top view at 1:1: outline, holes, silkscreen, mask openings, title block")
        out["Preview_Top.png"] = (K.render(pcb, "top", tmp), "render, top")
        out["Preview_Bottom.png"] = (K.render(pcb, "bottom", tmp), "render, bottom")
        drc_bytes, drc = K.report("drc", ["pcb", "drc"], pcb, tmp)
        out["DRC.json"] = (drc_bytes, "kicad-cli DRC report, every severity")
        files = [(f"{spec.PREFIX}_{k}", v[1]) for k, v in out.items()]
        data = {f"{spec.PREFIX}_{k}": v[0] for k, v in out.items()}
        data["RELEASE_MANIFEST.md"] = manifest(board, files, drc, sources)
    data["SHA256SUMS.txt"] = "".join(f"{K.sha(b)}  {n}\n" for n, b in sorted(data.items())).encode("utf-8")
    if args.out.exists():
        for p in args.out.iterdir():
            if p.is_file() and p.name not in data:
                p.unlink()                     # the directory holds only this script's output
    args.out.mkdir(parents=True, exist_ok=True)
    for name, b in data.items():
        (args.out / name).write_bytes(b)
    print(f"wrote {args.out.as_posix()}: {len(data)} files; DRC {K.count(drc, 'violations')} violations,"
          f" {K.count(drc, 'unconnected_items')} unconnected")
    if args.no_check:
        return 0
    sys.stdout.flush()
    return subprocess.run([sys.executable, "-I", "-B", str(HERE / "check_lid.py"), "--src", str(args.src),
                           "--outputs", str(args.out)], check=False).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv))
