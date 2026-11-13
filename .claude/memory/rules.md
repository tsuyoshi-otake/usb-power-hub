# Verified learnings - usb-power-hub

Distilled rules about **working this repository** (tools, vendor APIs, Git).
Board-design learnings belong in `CLAUDE.md` Section 13 once verified on this
board. Add a rule only after it was observed; update in place; delete one that
turns out wrong. The append-only log is [`journal.md`](journal.md).

## JLCPCB assembly-parts API

- **Stock and class:** `POST https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`
  with `{"currentPage":1,"pageSize":N,"keyword":"..."}`. Use `tools/jlc_stock.py`
  rather than re-deriving it. `componentLibraryType == "base"` is a Basic part;
  anything else is Extended (`preferredComponentFlag` marks Preferred Extended).
  Verified 2026-11-03 on the 46 rows of `requirements/parts.md`.
- **Datasheets:** `dataManualFileAccessId` now comes back `null`; the usable field
  is `dataManualFileAccessIdUrl`, a signed storage URL that expires (observed:
  about 30 minutes). Fetch it immediately after the search and check that the
  body starts with `%PDF` before trusting it. Verified 2026-11-03. This changes
  the route described in easy-stick lesson 14.7, which used the `...AccessId`
  field. It is also the route when the manufacturer and Mouser refuse scripted
  fetches: onsemi's NCP115 (Rev. 4) came this way, by searching C603503.
  Verified 2026-11-04.
- **The search is fuzzy.** A query returns near-matches; only an exact LCSC-code
  or case-insensitive MPN match counts as found. A search with no exact hit
  (e.g. `TMUX6109`, 2026-11-03) is "not stocked", not "stocked under another
  name".
- **"Is any Basic part X?" needs the server-side filter.** Add
  `"componentLibraryType":"base"` to the same request body: the API then returns Basic
  parts only. `tools/jlc_stock.py --all` shows only the first page of fuzzy hits (50 of
  5,192 for `3.3uH`), so a Basic part deeper in the list is missed. Verified 2026-11-04:
  `inductor`, `Inductors` and `10uH` each returned the same two Basic parts (C1035, C1046);
  `Ferrite Beads` returned 4 and `LDO` 6, all Basic; `3.3uH` returned 0.

- **Prices:** the same search returns `componentPrices`, a list of tiers (`startNumber`,
  `endNumber` with -1 = open-ended, `productPrice` in USD), plus `leastPatchNumber` (20 on the
  passives) and `lossNumber` (attrition). How JLCPCB combines the last two at order time is not
  documented; `design/experiments/cost-estimate/` reads them as need + loss, at least
  `leastPatchNumber`. Verified 2026-11-03 on the 35 machine-placed codes.
- **JLCPCB help and blog pages are server-rendered.** `curl -sL -A "Mozilla/5.0"` returns the
  full text, prices included (`/help/article/pcb-assembly-price`,
  `/blog/reduce-pcb-assembly-cost-prototype`, 2026-11-03), so a verifier can check fee
  constants without a browser. The quote calculator at `cart.jlcpcb.com/quote` is not: it
  needs the browser, and its PCBA section requires a Gerber upload before it shows a price.
- **Stackups:** `jlcpcb.com/impedance` is curl-readable too: every stackup table and the Dk
  table come back in the HTML. Verified 2026-11-03 by the main session and again by a
  verifier's fresh download. The impedance calculator `/pcb-impedance-calculator` needs the
  browser. On 2026-11-03 its single-ended mode answered after a page reload. Its
  differential mode returned no width in two attempts: the result stayed a spinner and
  the page threw `TypeError: e.some is not a function`.
- **Economic eligibility of a stackup is the quote page's per-stackup note, not the
  calculator's tab label.** The quote page marks each excluded stackup "This is a special
  stackup, and it doesn't support economic PCB assembly". The calculator labels only some
  tabs "Special": 3313, 1080 and 7628G have no label there, yet all three carry the note.
  Verified 2026-11-03 on all 18 named 4-layer 1.6 mm stackups.

## Akizuki (akizukidenshi.com)

- **Search:** `https://akizukidenshi.com/catalog/goods/search.aspx?keyword=<kw>&search=x`.
  Each hit is a `<dl class="block-cart-i--goods ...">` block; the product link is
  `/catalog/g/g<digits>/` with the name in `title=`, price in `block-cart-i--price`, and the
  purchasable quantity in `block-cart-i--available_purchase` (the page's 通販購入可能数).
  **Product page:** `/catalog/g/g<digits>/`; its documents are under `/goodsaffix/*.pdf`.
  Space requests >= 2 s apart and back off on errors. Verified 2026-11-03 on the five
  Akizuki rows of `requirements/parts.md`. No committed tool reads Akizuki yet, so stock is
  rechecked by hand at order time (V-MFG-02).
- **Pages are UTF-8, and a search keyword is UTF-8 percent-encoded.** Decoding a page as cp932
  gives mojibake, and a cp932-encoded keyword returns no hits (`金属皮膜抵抗 470Ω` found
  g108532 only when UTF-8-encoded).
- **Fields on a product page:**
  - name: `<h1 ... block-goods-name ...>`. Its text starts with a `[<code>]` prefix
    (e.g. `[108805]`), so strip `^\[\d+\]\s*` before comparing titles. Verified 2026-11-04:
    every one of 43 titles compared NG until stripped, then all matched;
  - pack: `block-goods-price--qty` (e.g. 1袋100本入);
  - tax-included price: `block-goods-price--price`;
  - purchasable stock: the one `<div class="block-goods-detail-available_purchase">`.
  The bulk-purchase blocks lower on the page belong to related products: a regex over any
  "available_purchase" field returned their stock.
- **Read a regulator's tolerance from the datasheet's order-code table, not from the product
  page's 主な仕様.** g129527 (XC6221B111NR-G) lists 出力電圧精度 ±1 %; Torex's sheet gives
  ±1 % only for V<sub>OUT</sub> ≥ 2.00 V, and ±20 mV (1.080–1.120 V) for the 1.10 V part.
  Verified 2026-11-11.
- **The shipping rule is on `/catalog/pages/buy.aspx`, server-rendered.**
- Verified 2026-11-03 on 43 product pages by the main session, and again by two verifiers'
  fresh downloads.

## LCSC (lcsc.com)

- **A product page `https://www.lcsc.com/product-detail/C<n>.html` is curl-readable.** It embeds
  a JSON block with `productCode`, `productModel`, `brandNameEn`, `encapStandard`,
  `stockNumber`, `minBuyNumber` and `productPriceList` (`ladder`, `usdPrice`, `extPrice`).
  Read figures from that JSON, not from the page's FAQ prose, which was stale. Verified
  2026-11-03 on C7433 and C15127, and again by a verifier.
- **TI datasheets come from the product page's `pdfUrl`.** ti.com answered scripted fetches
  with 404. The `pdfUrl` in C7433's page JSON (`datasheet.lcsc.com/datasheet/pdf/...`)
  served TI's SLOS099F. Verified 2026-11-04, and again by two verifiers' downloads. The LCSC
  search API answered "Access Denied" to the same session.
- **No public page read gave the shipping charge to Japan.** The shipping page lists only
  promotions, so LCSC's charge is known only at checkout (2026-11-03).
- **Read a passive's tolerance and TCR from its MPN, not from LCSC's listing parameters.**
  Some listings disagreed with the MPN (2026-11-04, #6 P2). In UNI-ROYAL's code, as in
  `0402WGF100JTCE`, the `F` is ±1 % and the `J` in `100J` is the decimal multiplier (10 Ω),
  not ±5 %.

## Datasheet text extraction

- Some vendor PDFs are encrypted (CH224Q, USB2514B on 2026-11-03). `pypdf` then
  fails with "cryptography>=3.1 is required"; install `cryptography` into the
  same **task venv** (never the global interpreter, never `~/tmp/pdfvenv`).
- Text extraction is fine for parameter tables. Pin numbers come from the
  package drawing, not from extracted text (easy-stick lesson 14.26, in its
  "Extends 14.12" paragraph: `pdftotext -layout` scrambles pin tables).
- **When a parameter table's conditions come out scrambled, render the page and read the
  image.** `page.get_pixmap(dpi=...)` with PyMuPDF in a task venv. Verified 2026-11-04 on
  SLOS099F page 4: the single-supply A<sub>VD</sub> row's conditions (V<sub>O</sub> 1.4–11.4 V,
  R<sub>L</sub> ≥ 500 kΩ) were legible only in the rendered page.
- **Read a plotted value from the figure's vector paths, not from a rendered image.**
  `page.get_drawings()` gives the curve's line segments. Calibrate the axes from the tick
  labels' positions in `page.get_text("words")`, then interpolate. Verified 2026-11-04 on
  MCP3208 DS21298E Figure 2-2 at V<sub>REF</sub> 3.3 V: the image was read as −0.5 LSB, the
  vector paths give −0.37 LSB. An independent verifier caught the difference, and the main
  session's own path extraction reproduced it.
- **Read a connector's pad order and land from the drawing's own labels, enlarged, not from
  memory or a familiar pinout.** Verified 2026-11-12/13 (#8): the C2765186 pads alternate the
  two signal rows (A1 A4 B8 A5 B7 A6 A7 B6 A8 B5 B4 B1 from left to right in the top view).
  The land came from the maker's "RECOMMENDED PCB LAYOUT" page, rendered and enlarged, and
  `check_libraries.py` fails a mirrored order. The first independent grading (C1) re-read the
  same drawing and agreed with every figure within 0.002 mm, bar the 0.035 mm the user chose
  for pads A1 and B1.

## Git

- **A rename plus a heavy rewrite in one commit loses the history link.** `git`
  scores the pair below its similarity threshold and records delete + add, so
  `git log --follow` stops at the new name. Commit the pure rename first, then
  the content. Verified 2026-11-03: `2a83480` (rename only) keeps
  `git log --follow -- design/circuit/CIRCUIT_DESIGN_Rev0.2.md` reaching
  `4dd10fb`.
- **Write a commit message's list of tests from the diff, not from memory or the rubric.**
  The first draft of #8's main commit (`0cdbbda`) named tests that did not exist, among them
  "pitch below 18 mm", which the rubric's Expect clause also listed. `git diff --cached -U0 |
  grep "def test_"` gave the real names and the message was rewritten before the commit
  (2026-11-13). The pitch test did not exist until `fc85c78`.

## Decision records

- **"A consequence of decision Dn" is a claim to check, not a label.** List the
  alternatives Dn still leaves open; if any remain, the item is a proposal
  (Rev0.2 §14), and it must not close an open issue. Verified 2026-11-03: D12
  ("two crystals, a consequence of D11") was withdrawn after an independent
  verifier showed D11 forces only a 24 MHz hub clock; it is now P13 and OI-2 is
  open again.
- **A rejection that rests on a catalogue or stock fact expires: re-run the lookup when the
  question returns.** Verified 2026-11-11 (#3): the RP2350A was rejected on 2026-11-04
  because Akizuki had no 1.1 V regulator and JLCPCB held 1 of its inductor (C42411119).
  Seven days later Akizuki listed XC6221B111NR-G (g129527) and the inductor stood at 738.
  Record such a reason with its date and the query that produced it.

## Shell and Python on this box

- **`python -I` ignores `PYTHONIOENCODING`.** Non-ASCII output then comes out in the console
  code page and is garbled (`§` printed as mojibake on 2026-11-03). Call
  `sys.stdout.reconfigure(encoding="utf-8")` in the script, or keep a script's output ASCII,
  as `design/circuit/CIRCUIT_DESIGN_Rev0.3_calc.py` does.
- **Pass multi-line Python through a quoted heredoc (`python -I - <<'EOF'`) or a file written
  with the Write tool, never through `-c` with mixed quotes.** A `-c` string holding both quote
  kinds failed with "unexpected EOF while looking for matching `''" (2026-11-03); the
  quoted-heredoc form ran every non-ASCII edit of this session correctly.
- **In that heredoc, a doubled backslash arrives as one.** A Python literal written as
  `"<bs><bs>n"` reached Python as `"<bs>n"` and put a real newline into the generated file
  (SyntaxError, 2026-11-03). Build a literal backslash with `chr(92)`, or write the script with
  the Write tool. (`<bs>` stands for a backslash here, so this rule does not depend on how it
  is itself pasted.) It recurred on 2026-11-03, when a heredoc edit put real newlines into two
  string literals of the bench kit's `kit.py`, and again on 2026-11-04 in an edit of
  `CIRCUIT_DESIGN_Rev0.4_calc.py` (a `str.index` ValueError, before anything was written).
  It recurred once more on 2026-11-04 (D31): a heredoc script appending to `journal.md`
  wrote `<bs>r` as two real CR bytes before its next assertion failed, so a failing
  assertion does not prove that nothing was written. Re-read this rule before any heredoc
  that writes code or text with a backslash; an edit script written with the Write tool and
  run by path avoided it for every later edit that day.
- **`Path.write_text` on Windows writes CRLF.** An edit script that read LF files with
  `read_text` and saved them with `write_text(s, encoding="utf-8")` left all seven edited
  files CRLF (675 of 675 lines in CLAUDE.md, counted in the bytes on 2026-11-03). Git's
  `eol=lf` attribute normalizes the commit, but the working copy keeps CRLF until the next
  checkout. Pass `newline="\n"` to `write_text`, or use `write_bytes`.
- **Git Bash's `grep` does not see CR bytes: use `grep -U`, or count them in Python.** GNU
  grep 3.0 here reads files in text mode. On a file holding one CRLF line, `grep -c $'\r'`
  printed 0, `grep -U -c $'\r'` printed 1, and Python's `open(p, "rb").read().count(b"\r")`
  gave 1 (2026-11-04). An independent verifier found it while running a rubric's
  `xargs grep -l $'\r'` check, so that check had never been able to fail. A rubric's CR
  criterion uses `grep -U` or the Python byte count.
  Inside a command substitution this Git Bash drops a literal `$'\r'`: `c=$(grep -U -c $'\r'
  "$f")` greps for the empty pattern and counts every line. On a 3-line file with one CRLF
  line it printed 3, the same grep outside `$(...)` printed 1, and `${#p}` of `$'\r'` was 0
  inside and 1 outside (2026-11-04). Assign the pattern to a variable outside the
  substitution, or count in Python. The simplest exact form is `tr -cd '\r' < "$f" | wc -c`: it
  counts bytes, works inside `$(...)` too, and its negative control `printf 'a\r\nb\n' | tr -cd
  '\r' | wc -c` prints 1 (checked 2026-11-13, #8, after `n=$(grep -c $'\r' journal.md)` printed
  1336, every line of a file with no CR byte: the rule above, hit again after a context reset).
- **Run at most two heavy processes at a time, and one test suite at a time.** A parallel
  sweep of Freerouting runs froze this box on 2026-11-12 (#8; the user: 「固まってるけど」,
  then 「負荷かけすぎじゃない」). Since then the router, each test suite and each KiCad
  check run alone, with a timeout. The router is deterministic (see "Freerouting 2.5.0"),
  so one trial per input is enough and the official run reproduces it.

## Design documents

- **A stale-figure sweep greps the bare number, never the number plus its words.** Markdown
  wraps lines. In the D25 change, `grep "0\.32 V at 1 A"` missed README.md's "0.32 V" /
  "at 1 A" split across two lines. An independent verifier found it. Grep `0\.32` and read
  every hit. Verified 2026-11-03.
- **Every derived number in a design document comes from one committed script, and every
  column uses one basis.** Verified 2026-11-03: writing `CIRCUIT_DESIGN_Rev0.3_calc.py`
  exposed full-scale currents computed with the pedestal and thresholds without it (366 µA
  vs 365 µA), which no reviewer of the document alone had flagged.
  The document quotes every figure the script prints for it, sweep points and secondary
  cases included, or the script stops printing that figure. Verified 2026-11-04: an
  independent verifier failed the D29 round on figures the script printed and the document
  did not quote (the reset hold's 2.705 / 2.887 V, the BOOTSEL DVDD case, two crystal-pull
  sweep points, the load sweep, a 0.281 V margin). The second round passed once they were
  quoted.
- **One LCSC code per row in a parts table.** A stated type count is checked against the
  rows. A "1 nF / 10 nF" row holding two codes made 39 rows for 40 types, and a verifier's
  count failed it (2026-11-04). Split such a row in two.
- **A printed sum shows the terms the code actually used, and a lower bound takes the most
  favourable value at every step.** Verified 2026-11-03:
  - `placement_study.py` printed "under-module 704" while subtracting min(704, 442);
  - its credit was per block, so one tall part removed a block's low parts from the credit,
    which weakened a bound meant as a proof;
  - an independent verifier recomputed the printed terms and caught it.
  A test now asserts that the printed terms add up.
  Second incident, 2026-11-04 (D33, #6): the bound credited the space the layout used under
  each USB-C module (130 mm²), not the largest the geometry allows (the outline less the
  header insulators, 230.2 mm²), so "3,332 mm² at K = 1.0" was not a lower bound. Reading
  the module and receptacle drawings for the header height found it, and also that the
  layout's rectangle sat under the mid-mounted receptacle. A credit for space under a part
  comes from that part's drawing and its connector's, never from a layout choice.
- **Check a fault-injection step against what drives the node in hardware.** V-SAFE-01 asked
  firmware to hold a bypass FET off to simulate a stuck range. Rev0.4 §3.2 has the LM393 turn
  the bypass on in hardware whenever its amplifier overranges, so the step could not produce
  the fault. It now removes Q17 / Q18 on one board. Found 2026-11-04 by reading the gate
  network; fixed in `1d43f4d`.
- **A verification entry's pass items are numbers with units, and each names what its
  failure reopens.** Verified 2026-11-04: an independent verifier, grading against that
  criterion, found three gaps. "No sustained oscillation" is now ±1 % within 100 µs. "The
  flash is a W25Q64JV" is now JEDEC ID EFh 4017h. A LOW sweep to 430 µA could not run past the
  365 µA hardware up-range.
- **Name a source only after finding, in this session, the text that came from it.** Verified
  2026-11-04 (D35, #7): a draft cited "TI TPS2553-Q1 §10.2" for USB's 10 µF ∥ 44 Ω rule; a
  search of the session transcript showed the excerpt came from TI SLVS798G and NXP AN11392
  web-search results. Say "as web-search excerpts" when the primary text was not read.
- **After replacing a line of an ASCII diagram, compare its branch column with the old
  line's.** Verified 2026-11-04 (D35): the new §3.1 line put `┬` at column 44 while the
  branches below sit at 45; a script comparing `str.index("┬")` with HEAD's line found it.
- **Quote the user verbatim, typos included, and quote every message that set the rule.**
  Verified 2026-11-03: the Rev0.3 header had "corrected" 「デカくい」 to 「デカい」 and dropped one
  line of the user's message; an independent verifier caught it.


## KiCad 9 (pcbnew from KiCad's own Python)

- **Run scripts with `<KiCad 9.0>/bin/python.exe -I -B`.** It carries `pcbnew` and works
  isolated. It prints "Adding duplicate image handler" lines on stderr; filter them with
  `grep -v "duplicate image"` and read the exit status from `${PIPESTATUS[0]}`.
- **SaveBoard rewrites `.kicad_pro` from pcbnew's cached project.** Verified 2026-11-04 (#6):
  `make_project.py` edited the project JSON, then ran a LoadBoard/SaveBoard round trip in the
  same process, and every rule and net class came back at KiCad's defaults
  (`min_clearance` 0.0, no USB_HS). Edit `.kicad_pro` after the last SaveBoard, and check
  the result in a new process; only there does pcbnew read just the files.
- **The stackup cannot be set through the Python API.** Insert the `(stackup ...)`
  S-expression text right after `(setup` and let a LoadBoard/SaveBoard round trip normalize
  it. KiCad keeps the layers and adds mask thickness 0.01 mm and loss tangent 0.02 (observed
  2026-11-04). The general `(thickness 1.6)` stays the nominal board thickness.
- **Replace every `(uuid "...")` with uuid5 of its position for byte-identical re-runs.**
  Verified 2026-11-04: two runs of `make_project.py` gave the same SHA-256 for all three files.
  That fixes the values, not the order: see the next rule for a board with footprints.
- **SaveBoard writes footprints sorted by UUID, and pcbnew gives each new item a random one.**
  The first `make_pcb.py` wrote a new footprint order on every run (2026-11-05, #6 P3: three
  SHA-1s, 74,718 diff lines between two runs), and renumbering by position kept the order.
  `pcbnew.KIID.SeedGenerator(n)` before creating anything fixed it: three runs, and the
  sequence `make_project.py` -> `make_pcb.py`, gave one SHA-1.
- **Do not `board.Remove()` any item and then call `FootprintLoad` in the same process.**
  In KiCad 9.0.8 the later `FootprintLoad` raised `AttributeError` on a `SwigPyObject`
  (2026-11-05, #6 P3, footprints; again 2026-11-06, #6 P5, Edge.Cuts drawings, in
  check_libraries' DRC sandbox; a third time 2026-11-13, #8, when a new `peg_drc` helper in
  `test_make_project.py` broke three tests). Cut the `footprint`, `segment`, `arc`, `via`,
  `zone` and every `gr_*` node from the board's text before `LoadBoard`: 3559 checks PASS.
  A new test helper that edits a board does it in the text from the start.
- **A footprint's silkscreen can lie outside its courtyard.** The RP2040 land's pin-1
  triangle sits outside the courtyard, so a 0402 placed clear of the courtyard still gave DRC
  `silk_over_copper` and `silk_overlap` (2026-11-05, #6 P3). Courtyard spacing does not guard
  silk: run DRC with `--severity-all` after every placement change.
- **`design/ecad/scripts/sexpr.py`'s `loads` returns the top node itself.** `tree[0]` is its
  head symbol (`kicad_pcb`), not the node. A test that indexed `tree[0]` wrote broken boards,
  `LoadBoard` returned None, and the checker crashed instead of failing (2026-11-05, #6 P3).
  `check_pcb.py` now prints a FAIL line when the board does not load.
- **`kicad-cli pcb drc` exits 0 even with violations unless `--exit-code-violations` is
  passed.** Verified 2026-11-04 on a copy with a track 0.05 mm from the edge: 2 violations
  (`copper_edge_clearance`, `track_dangling`), exit 0 without the flag, 5 with it. `sch erc`
  has the same flag. Pass it, and also count `violations`, `unconnected_items`,
  `schematic_parity` and, for ERC, `sheets[*].violations` in the JSON report.
- **Write S-expression node heads bare.** A generated `.kicad_mod` or `.kicad_sym` whose
  heads were quoted (`("footprint" ...)`) did not load: `pcbnew.FootprintLoad` returned None
  and `kicad-cli` could not read the library (2026-11-04, #6 P1). Writing every head bare
  fixed all of them.
- **`kicad-cli` messages follow the locale (Japanese on this box).** A regex for the English
  "Pad … of …" in the DRC JSON matched nothing (2026-11-04). Parse structured fields such as
  the net names in `[...]`, not the description text.
- **`FOOTPRINT.GetNetTiePadGroups()` is not iterable from Python** (a bare SWIG vector,
  probed 2026-11-04). Read `net_tie_pad_groups` from the file's S-expression instead.
- **KiCad's Windows install ships CRLF; the repository stores LF.** The 20 stock footprints
  copied byte for byte kept CRLF. An LF copy, which is what `eol=lf` gives a checkout, failed
  27 byte-copy checks: a verifier simulated this on 2026-11-04 (#6 P1).
  - Write copies with `.replace(b"\r\n", b"\n")`, and compare against the vendor file
    normalized the same way.
  - Reject CR bytes in the checked tree.
  - To prove a checker on the committed bytes, stage the files and run it on
    `git checkout-index -a --prefix=<dir>/`. That passed, 1941 checks.
- **KiCad's `TL431DBZ` symbol is TI's SOT-23 order (1 K, 2 REF); JSCJ's CJ431 is 1 REF,
  2 CATHODE, 3 ANODE, which is KiCad's `TL432DBZ`** (CJ431 page 1 and the stock symbol, read
  2026-11-04). Never pick a TL431-family symbol by name: compare the pin numbers with the
  maker's own sheet.
- **A land drawing's figure can be a corner distance, not a pad length.** Check each figure
  against the span arithmetic before recording it. RP2040 Figure 167's 1.175 mm is
  3.875 − 2.70, the pad corner to the side's end. The pad length is (7.75 − 6.00) / 2 =
  0.875 mm (read visually 2026-11-04). KiCad's stock `QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm`
  has the same copper; only its paste windows differ (1.29 vs 1.28 mm).
- **An exported netlist does not carry net classes.** Verified 2026-11-04 (#6 P2):
  `kicad-cli 9.0.8 sch export netlist` wrote `(class "Default")` on every net, both with
  `netclass_patterns` and with explicit `netclass_assignments` in `.kicad_pro`. Resolve a
  class with pcbnew: `LoadBoard(pcb).GetDesignSettings().m_NetSettings
  .GetEffectiveNetClass(name).GetName()` gave USB_HS for `USB_A_N`.
- **Put PWR_FLAG in the project library.** This box has no global sym-lib-table, so
  `power:PWR_FLAG` does not resolve. A project-library copy gave ERC 0 violations on 7
  sheets (#6 P2). Removing a flag gave `power_pin_not_driven`, so ERC does see it.
- **A negative test must look for the checker's FAIL line, not only its exit status.**
  A corrupted input made `check_schematic.py` die with a KeyError traceback, which also
  exits 1 (2026-11-04, #6 P2). Assert the summary line (`N checks, M failed: FAIL`) and
  the failing item's name.

## Freerouting 2.5.0 (from autoroute.py)

- **The DSN `(autoroute_settings ...)` scope is applied, and its CLI twins are not.**
  - `--router.scoring.*` flags gave scores identical to a run without them.
  - The same costs in the DSN changed the result:
    - layer direction preferences (In2 horizontal, B.Cu vertical, against 4.0) cut the
      analog L3/L4 parallel overlaps from 16 to 4;
    - `via_costs 100` cut DRC's unconnected count from 6 to 2.
  - Placement: after the last `(layer ...)` scope, before `(boundary`. Placed before the
    layers it gave a parse error and a NullPointerException.
  - Verified 2026-11-06, #6 P4.
- **The router is deterministic.**
  - The same DSN, jar, JRE and arguments gave the same session byte for byte, apart from
    the session name on lines 1–2.
  - One trial per setting is therefore enough, and the committed session is reproducible.
  - Verified twice: full3a/full4p, and the trial full8_v100 against the official
    autoroute.py run (b7a6c3b).
- **The router's unrouted count is not DRC's.**
  - For b7a6c3b's session the router reported 18 unrouted and 820 violations.
  - DRC on the same session found 2 unconnected and 0 violations.
  - Judge only by `check_routing.py` / DRC.
- **The session file is written only when the router stops.**
  - It stops after 10 passes without improvement, or at `max_passes`.
  - Killing it (or TaskStop on its Bash task) leaves no `.ses`, and can leave the JVM
    running; list java.exe afterwards.
  - A background Bash task can end while its python and java children run on. Wait on the
    output file or the PID, not on the task.
- **`-l en` with file logging on writes `<cwd>/en/freerouting.log`.**
  - Pass `--logging.file.enabled=false`.
  - Even then an empty `en/` was left in the repo and failed rubric C8 (2026-11-06).
  - `autoroute.py` therefore runs the router with `cwd` set to its temporary directory, and
    makes `--java` and `--jar` absolute for that (a relative path would break the run).
    Checked 2026-11-13 (#8) with relative paths and a 40 s timeout: the run started from the
    committed input's digest, no `en/` appeared in the working directory or the repository,
    and no java.exe was left.
- **With neck-down off, the router still narrows a wire to 0.10–0.12 mm at a 0.4 mm-pitch
  pin.** `--router.neck_width_um=150` holds it at the board minimum, so DRC's track-width
  rule passes (#6 P4).
- **Match the right log line in a wait loop.** `Fanout stage completed` also matches
  `stage completed`; match `Auto-routing stage completed`.
- **For the last few defects, a patch after the session is cheaper than another sweep.**
  - The patch is a document table of remove rows and drawn rows.
  - A remove row that finds nothing stops the build, so a stale patch cannot apply silently
    to a new session.
  - The last 2 unconnected and 3 overlaps were found with a scratch 0.1 mm grid A*. Its
    obstacles were other nets' copper, the DSN keepouts, the hole clearance and D36. DRC
    then proved the result.
  - Off-grid endpoints make 44° segments, so set end points by hand to exactly 45° or 90°.
  - The first grid search left out the 0.25 mm hole clearance for tracks, and DRC caught it.
- **A patch belongs to one router session.** (#8, 2026-11-13)
  - The Rev0.5 patch is 259 rows (32 remove, 227 drawn) in four stages. It closes the
    committed session's 16 open connections and 11 D36 places. A new router run needs a new
    patch, and the scratch tools that found the rows are not in the repository.
  - In the window north of U1, nets routed one after another left three connections open;
    the window routed as a whole by negotiated congestion closed them.
  - Three U1 pads were joined with the plane rule off. With it on no path exists: the
    pockets around those pads hold no cell where a via keeps rule 9.
- **Freerouting knows no antipad, so a DRC-clean board can still have a broken L2 plane.**
  (#8, 2026-11-13)
  - On L2 a via of another net stands in an 0.85 mm antipad (0.45 + 2 x 0.20) and the fill
    drops plane copper narrower than 0.20 mm. Two such vias closer than 1.05 mm make one
    void, a row of them a slot. The first Rev0.5 session passed DRC and left U1's exposed pad
    no plane copper on its east side (a slot 5.04 mm long); Rev0.4's committed board has
    voids up to 3.65 mm, and nothing had flagged them.
  - Give the router the antipad (`route.py`, ROUTING_Rev0.5.md *Router*): every via padstack
    0.60 mm larger on In1.Cu (`plane_via`, so different-net vias stand at least 1.20 mm
    apart; 48 pairs closer before, none after, on one pass), a keepout around drilled pads
    (`PLANE_HOLES`), and a copy `_gnd` of the padstack for GND vias, which have no antipad.
  - Check the plane itself: `check_routing.py` rule 9 (no void over 3.0 mm; at least half of
    each side of an exposed pad kept in plane copper within 5.0 mm). DRC has no such rule.
- **A worse result from a changed router input has a cause in the input: diff the two DSNs
  before calling it randomness.** (#8, 2026-11-13) A trial with 22 extra pre-route rows
  (13 long V_INJ rows along y = 24.2 among them, and 5 U1-pin escapes) left 41 connections
  open against 16. I first read that as noise; the router is deterministic, the DSN diff
  named the rows, and removing them restored the committed input's digest and result.

## KiCad 9 routing checks

- **Solve a net's copper resistance only on the island that holds the first pad.**
  - Any isolated island of the net makes the full conductance matrix singular, and the
    check reported "no copper path".
  - BFS from pad a; inf if pad b is not reached. Verified by `test_port_net_island_elsewhere`
    (#6 P4).
- **Compare a 45° design rule with a tolerance (0.1°).** About 20 exact-45° crossings
  measured 44.99…° and failed without it (#6 P4).
- **A connector pad without paste is `PAD_ATTRIB_CONN`, not SMD.** Include it when
  collecting surface pads; an SMD-only GND fanout missed J5's pad 5.
- **`PCB_VIA.GetWidth()` takes a layer in KiCad 9** (`GetWidth(pcbnew.F_Cu)`).
- **A track's class name is `PCB_TRACK`.** A test that expected `SEGMENT` in a FAIL line
  failed once the checker printed `GetClass()` (#6 P4).
- **Check what a note parser will read as a designator.** check_pcb.py read "at P3" in a
  placement note as part P3, and failed (#6 P4).

## KiCad 9 hole rules (#8, 2026-11-12)

- **A looser custom rule in `<project>.kicad_dru` overrides the stricter board minimum.** A via
  `hole_clearance` rule of 0.20 under a board `min_hole_clearance` of 0.25 gave 0 violations; without
  the rule, 199. A stricter custom rule is enforced too: a 0.10 mm PTH ring fails the DRU's 0.15 mm
  `annular_width` rule (`test_pth_ring_below_015`). Use the board minimum as the default and the DRU
  for per-type figures.
- **A pair rule matches the two items in either order and constrains both holes.** A rule with
  `A.Type == 'Pad' && Through-hole` also flagged the via's hole against PTH copper. Exclude the other
  type explicitly (`B.Type != 'Via'`) and give that pair its own rule.
- **KiCad's DSN export sizes the router's NPTH keepouts with `min_hole_clearance`.** Changing it from
  0.25 to 0.20 shrank two keepouts (2700→2600, 1490.6→1390.6 µm) and changed the router input. Keep the
  board minimum fixed when the router input must stay the same.
- **Changing only a via's drill changes the zone fill.** The poured layers (B.Cu, In2) differed by
  slivers under 6 µm wide, although the hole's knockout lies inside the copper's. Refilling the old
  board alone reproduced its own fill in the runs tried then (not guaranteed: next rule). Prove
  "copper unchanged" by tracks, via positions and pads, footprints, plus a 3 µm erosion of the fill
  difference, not by Gerber bytes.
- **KiCad's zone filler is not deterministic, so `make_pcb.py`'s board is not byte-reproducible.**
  (#8, 2026-11-13) Same inputs, 32 runs (a scratch copy of `design/`, `make_pcb.py --no-check`, 5 s
  each): 29 gave board `d354d21a…`, 3 gave `3205d4c4…`, which lacks two 0.11 mm² B.Cu GND islands that
  touch pad J3.S1 (text diff: two added `filled_polygon` blocks of 11 and 10 lines; the Gerber's
  `B_Cu` member differs by the same two regions and every other member is identical). Both boards
  pass DRC, `check_pcb`, `check_routing`, `check_silk` and every suite. It surfaced only because the
  final "run it again and compare" step compared the board's hash with the one in the release
  manifest, and r02's was the less frequent state. The share is not fixed: 3 of 32 runs here, 4 of
  the independent verifier's own 10 (7 of 42 together), and no third state in the 42. Rules: the
  tracked board is the source of truth and the manifest records its hash; never regenerate it to
  prove a release; diff a changed hash after a re-run (two `filled_polygon` blocks?) before looking
  for a changed design; to get a given board back, re-run in a scratch copy of `design/` until the
  hash matches, never edit the fill by hand. `make_outputs.py` is deterministic for a given board.
  Not tried: filling the zones one at a time in a fixed order, which may remove the variation.
  Verified by: the 32 runs, `diff` of the two boards, a Gerber member comparison, a pcbnew probe
  (island mode 0 = always remove; both islands touch `J3.S1`), and the verifier's 10 runs (4 ×
  `3205d4c4…`, 6 × `d354d21a…`, the diff exactly the two blocks).
- **Freerouting with the same input repeats its session.** The 17-minute run on input that differed
  only in the via's padstack name gave the old session with that name replaced (56 passes both times).
- **A slot (an oblong hole) is invisible to both the router's search and KiCad's DRC.** (#8, 2026-11-13)
  `route.py` `_Copper` reads an oblong pad hole as a round hole at the pad's centre, so beside each rear
  shell slot of the receptacles it put the GND via of contact pad A1 or B1 0.046 mm from the slot's hole
  (8 vias). The board had 0 DRC violations; JLCDFM's plated-through-hole spacing called them Danger (below
  0.18 mm), and the board's own limit is 0.25 mm. `check_routing.py` rule 10 now measures every pair of
  drilled holes with a slot as a capsule (via-via 0.20, pad-pad 0.45, via-pad 0.25 mm). The router's
  input must not change (its digest is checked), so the patch deletes the 8 vias and ties each stub into
  the slot's pad (stage 5); the next session reads the slot as a capsule in `_Copper`.

## KiCad 9 silkscreen and manufacturing outputs

- **JLCPCB's legend needs line ≥ 0.15 mm, height ≥ 1.0 mm and a line-to-height ratio of
  1:6** (pcb-capabilities, Legend, read 2026-11-06). The ratio decides the stroke: 0.17 mm at
  1.0 mm, 0.2 mm at 1.2 mm. KiCad's stock footprints draw silk at 0.12 mm, so a byte copy
  fails the limit; `make_libraries.py` widens it and drops it on non-polar parts
  (`silk_drop`) whose silk cannot keep 0.15 mm from their pads (#6 P5).
- **Measure a label by its ink, not its text box.** `PCB_TEXT.GetEffectiveShape().BBox()`
  is the stroked glyphs; the text box is larger. A leader start measured against the box
  passed check_silk.py and was 0.2 mm short of the glyphs (2026-11-06, #6 P5).
- **KiCad DRC flags `silk_overlap` when a leader touches its own label.** check_silk.py had
  passed TP8's leader, which began inside the glyphs of VBUS_IN; `kicad-cli pcb drc` in
  make_outputs.py found it. A leader now must start ≤ 0.3 mm from its glyphs without
  touching them, and test_leader_touches_its_label proves the rule (#6 P5).
- **Freerouting ignores the silkscreen.** Widening the stock footprints' silk changed the
  DSN's digest, and a re-route gave the same session byte for byte (#6 P5). Labels are added
  after the session and kept out of the router input, so they never invalidate it.
- **The stackup's copper finish is not reachable from Python** (`m_FinishType` raised
  AttributeError, 9.0.8). Read `(copper_finish "HAL SnPb")` from the board text.
- **In a Gerber, y points up, so the sheet's y is negated.** The 100 × 72 mm outline at the
  sheet's (50, 50)–(150, 122) spans y −122..−50 in the Edge.Cuts file (#6 P5). That is why the
  set must be written with the auxiliary origin at the board's lower-left corner (#6 P6):
  JLCPCB reads the CPL against the Gerber's own origin, and with the page origin every part sat
  50 mm / 122 mm off the copper in the placement viewer. After the change the Edge.Cuts spans
  (0, 0)–(100, 72) (`check_outputs.py`), and every Gerber and drill coordinate differs from the old
  set by one constant (checked line by line, 51,444 coordinates, within 1 µm).
- **`kicad-cli pcb render` writes a little under the size asked** (1568 × 1120 for
  1600 × 1152). Check a render's width floor and aspect, not its exact size.
- **Fix creation dates to make an output set deterministic.** kicad-cli stamps Gerbers,
  drill files, PDFs and JSON reports with the run time; replacing each with a same-length
  1980-01-01 stamp and writing zip members with fixed times gave two runs identical
  SHA256SUMS (#6 P5).
- **One LCSC part can sit on two footprints, but the BOM has one row per LCSC.** C17734 (510 Ω)
  is both R_0805 and the Kelvin 0805 shunt land. P5 wrote one row per (LCSC, Footprint); JLCPCB's
  part matching then left the rows that share a code unselected (#6 P6, 2026-11-11). Now the BOM
  has one row per LCSC (40 rows) and the Footprint column shows the first footprint; the part
  mapping reads 40 of 40. The merged C17734 row still had to be ticked by hand after each
  *Process BOM & CPL*.
- **`manufacturing/working/` is ignored by Git** (`.gitignore`: disposable candidates). A
  candidate set is regenerated, never committed; its manifest records the sources' SHA-256
  instead of a commit, and check_outputs.py fails a stale set.
- **A negative test that picks "the first" item in file order breaks when the file is
  re-saved.** SaveBoard orders segments by UUID; P5's re-save made test_check_routing pick a
  0.7 mm stub ending on a via, whose B.Cu copy joined the via's net and was exempt (#6 P5).
  Pick by a property (the longest) and keep a copied track off the original's endpoints.
- **A negative test that names a designator stops being a fault when the part changes
  class.** (#8, 2026-11-13) The independent BOM/CPL check's corruption "hand designator J1
  added to BOM" reported MISSED after D37 made J1 machine-placed: the input was valid now,
  and the checker was right. Take the corrupted item from the data (the first designator of
  the hand-solder list), and read a MISSED as "is it still a fault?" before touching the
  checker.

## JLCPCB quote, placement preview and the account (#6 P6, 2026-11-11/12)

- **A CPL angle and a CPL point are applied to JLCPCB's own model of the part** (easy-stick 14.18), so
  the KiCad angle alone was wrong for 11 classes: U6, U8, the OP07 and LM393 SOICs by +270; the SOT-23
  family, the PSM712 and the SOT-223 by +180. The table is `design/ecad/jlcpcb_model_frame.json` (until
  2026-11-13 `jlcpcb_model_rotation.json`, rotations only), keyed by LCSC number (the model belongs to
  the part, not the footprint): `add` is a rotation, `shift` a position in the footprint's own frame,
  turned with it. In the viewer the magenta or purple dot is the model's pin 1 and the LED's "+" is
  the anode. Confirm each class only after the corrected CPL is uploaded: a first +180 on the LEDs
  put the anode on pad 1 and was removed.
- **The receptacle C2765186's model sat about 1.375 mm toward its mouth from the footprint's body
  centre** (#8, 2026-11-13: the CPL point is the footprint origin, the model's origin is elsewhere).
  The entry is `shift: [0.0, -1.375]`; J1-J4's CPL Mid Y moved by 1.375 mm away from the mouth. With it
  the viewer showed, on all four: front face 1.054 mm past the board edge (design 1.06 mm), tails
  6.325 mm (J1, J4) and 6.34 mm (J2, J3) from the edge against the pad row at 6.285 mm, pegs 2.82 mm
  either side (design 2.89 mm), reading error about 0.04 mm. Read a connector class twice: with the KiCad
  point first, to see the offset, then with the corrected CPL.
- **The 0.25 mm via class costs $34.16.** The form adds "4-Wire Kelvin Test" ($17.02) and
  "Min via hole size/diameter" ($17.14) by itself, and offers Plugged, not Tented, at $0.00
  (2026-11-12, 4 layers, 100 × 72 mm). An estimate that ignores the via class is $28 short.
  Drill every via at ≥ 0.30 mm with a ≥ 0.45 mm pad, and the board fits "0.3mm/(0.4/0.45mm)", the
  form's default: $8.00 with neither line, FR4 TG135 (r02, issue #8). The form does not show that it
  reads the via size from the Gerber (a fresh form shows the same default); choose the class from the
  board's smallest hole.
- **JLCDFM lists only the first 50 results of an item per layer** (a count of 100 is a cap) and says
  via results of the annular-ring check may be ignored. Judge an item by measuring the board (via-to-pad
  pairs by net, silkscreen against holes), not by the 50 rows. Keep a note of what stays unexplained.
  (#8, 2026-11-13, https://jlcdfm.com/ with the user's sign-in: a Details dialog gives each item's limits
  and rows; its viewer is in the Gerber's frame, x = x_KiCad - 50 mm, y = 122 mm - y_KiCad, so a row's
  position finds the part on the KiCad board; a row click recentres the view.)
- **JLCDFM appears to read KiCad's rounded-rectangle pads as plain rectangles.** Its first pad-spacing
  row was a C20 pad against a V3V3 via at 0.05 mm; with sharp corners the same measure gives 0.05 mm and
  the real shape 0.105 mm (checked for that row only). On the real shapes every pad-to-via pair under
  0.15 mm was on one net, and different nets are the DRC's (0.15 mm clearance).
- **JLCDFM's limits are its own and can contradict JLCPCB's capabilities page.** Plated slot width:
  JLCDFM Danger below 0.61 mm, Warning 0.61-0.81, Good above 0.81; JLCPCB's page (read 2026-11-13) gives
  0.35 mm minimum for multi-layer boards with a length of at least twice the width. 16 Danger rows for the
  receptacles' 0.60 mm slots were left to the user. Its plated-hole spacing: Danger below 0.18 mm,
  Warning 0.18-0.2 mm.
- **Browser tool facts (Claude in Chrome, 2026-11-13).** `browser_batch` takes `{"actions": [{"name": ...,
  "input": {...}}]}` (`calls` is rejected); `computer` has `hover`, not `mouse_move`; a JavaScript result is cut
  at about 1,000 characters, so print compactly. A JLCDFM Details dialog is the `_eda-modal-body_...` div,
  found by its text (`.el-dialog` is not it). A click on "My Account" on the quote page navigates that tab to
  Order History, where screenshots are refused: read the drafts another way or leave them. Close only the tabs
  of the session's own group; the tab group can vanish after a navigation error.
- **Uploading to JLCPCB creates auto-saved drafts** under My Account > Projects > **Quotes**; the
  pcbFileNo in the URL is account data and does not go into the repository. Tell the user the
  drafts exist and how to delete them ("..." > Delete). BOM upload, JLCDFM and EasyEDA Pro's
  Import KiCad all need the user's own sign-in; EasyEDA also shows a terms modal on easyeda.com,
  which only the user answers.
- **Browser evidence:** `computer screenshot` keeps nothing unless `save_to_disk` is true; a
  large `zoom` region can time out (take a plain scaled screenshot instead). Screenshots can show
  account details, so they live outside the repository.
- **JLCPCB coupons live in four places, and the coupon center is only one** (#8, 2026-11-13). A first pass
  over the coupon center and My Coupons ("0 unused; PCBA Special Offer $9 is the best") missed the Black
  Friday warm-up coupons, which are claimable only on the event page (`jlcpcb.com/events/black-friday-2026`;
  the home page's hero banner links to it): "BF PCBA $12" and ten more, limited quantity, with no minimum
  order, validity or region on the card, in the page text, in the lucky draw's Rules dialog or in the help
  article "Coupon Terms and Conditions". Look, in this order, at: My Coupons, **all three tabs** (Used shows
  what the account has redeemed, e.g. the monthly PCBA Special Offers); `/coupon-center`; the home page's
  banner and the campaign page it links to; the help article "JLCPCB New Customer Coupon Guide" (the monthly
  coupons, and a $10 PCBA coupon that needs EasyEDA-exported files). A coupon's terms show only after it is
  claimed, and claiming is an account change: the user says yes first. One coupon per order, so only the
  largest applicable one counts. Switching the wallet's tabs and opening a "Rules" dialog are read only;
  "Get Coupon", "Get All Coupons", "Spin Now" and the social-share icons are not (a share is a public post).
  A JavaScript call that prints hrefs is blocked as "Cookie/query string data": read a link's `href` with
  `read_page` on its ref.

## Delegated verifiers

- **Tell a verifier to delete nothing.** A rubric that said "delete it when done" let a
  rubric-verifier run `find -maxdepth 1 -type d ! -name 'dl-*' -exec rm -rf` in
  `~/tmp/usb-power-hub/` on 2026-11-03. That removed six sibling directories of this task,
  the `pdfx` venv among them. Deletes of those same directories from the main session had
  been denied. `ls` before and after showed the loss. Give the verifier one new directory of
  its own, forbid every delete, and have it report the path. The main session cleans up.
  Forbid git commands that write to the index as well: a verifier told only "edit, move or
  delete nothing" ran `git add -N` on the graded directory on 2026-11-03. It undid this with
  `git reset` and disclosed it.
- **Check delegated numeric work against an independent implementation and a hand-worked
  value, not only against the reference it was fitted to.** A fitted parameter can absorb a
  formula bug. Verified 2026-11-03: Devin's Hammerstad–Jensen thickness correction gave
  48.1 Ω where the formula gives 50.57 Ω. A fitted Dk of 4.04, against the published 4.4,
  still made its single-ended width match JLCPCB's. The main session's own implementation
  exposed it. The fix was to forbid the fit and pin the hand-worked value in a test.
- **Review a delegated test plan against the open issue's question, not only against its own
  checker.** A plan can pass its own tests and still be unable to answer the issue.
  Verified 2026-11-03: Devin's bench kit passed its 13 tests, yet
  - its substitute OP07 die and P-FET could not close OI-27, which is about the exact parts;
  - its V-MEAS-06 negative control could not fail (a stiff pot source removes the droop);
  - its bench A back-fed a supply into the PC's USB VBUS.
  The main session's review against V-MEAS-00/06 and the design found all three.

- **Write a rubric criterion's documented exceptions into the criterion itself.** C6 of the
  P3 rubric asked that every courtyard lie inside its region; the four USB-C modules'
  receptacles overhang the board edge by 1.06 mm, which the placement document allows. The
  verifier had to interpret, and said so (2026-11-05, #6 P3). A literal reading would have
  failed a correct board.
- **Grep each Expect clause's key phrase against the repository before launching the
  verifier.** The first grading of the Rev0.5 rubric failed C4 and C7 (2026-11-13, #8): no
  test made the J2-J3 pitch rule fail (the test file's own docstring disclaimed it), and D38
  cited neither CLAUDE.md 5.3's "No stubs" nor the RP2040's reset pull-down. A grep of the
  clauses' own words found both gaps a few minutes before the verdict arrived, so one
  grading pass went to what a grep finds.

## Devin CLI

- **Give Devin only simple tasks, and review its output yourself.** The user, 2026-11-04:
  「devinには簡単な作業だけさせてね。君がしっかりレビューしてね」. Simple means bounded,
  mechanical work with an observable result: fetch and tabulate, run a given script,
  reformat. Design judgement, test plans and numeric models stay with the main session.
  Every Devin result is reviewed by the main session against the issue's question. The
  backing is the two 2026-11-03 judgement delegations (the stackup model and the bench kit).
  Both needed the main session's review to find their defects (see "Delegated verifiers").

- **Invocation that worked (2026-11-03):** `devin --config <cfg.json> --permission-mode
  dangerous --model swe-2-max --respect-workspace-trust false --export <transcript.json>
  --prompt-file <brief.md> -p`. Continue the same session with `-r <session-name>`.
  `devin list` is an interactive TUI, not scriptable output.
- **In print mode a denied tool call ends the run without a message.** Deny rules still apply
  under `--permission-mode dangerous`. Read the `--export` transcript to see which call was
  refused. Verified 2026-11-03 with a permission test whose denied `rm` cancelled the run.
  It recurred on the bench-kit run, when Devin tried to delete its own downloaded PDFs. A
  brief therefore forbids deleting even Devin's own files. Resume with `-r` and a reminder.
- **Devin also loads `~/.claude/skills`.** A brief's rules therefore compete with the global
  skills, so a brief states its file scope, its no-delete and no-commit rules, and the
  interpreter flags (`python -I -B`, LF) explicitly. Observed 2026-11-03.
- **Keep memory edits out of the tree while a verifier grades a scoped change set.** A
  "only the files in scope changed" criterion failed twice on 2026-11-03, once for a journal
  entry and once for rules.md, both written while the verifier ran. Commit the graded files
  first, then the memory files.
