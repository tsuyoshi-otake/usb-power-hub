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
  field.
- **The search is fuzzy.** A query returns near-matches; only an exact LCSC-code
  or case-insensitive MPN match counts as found. A search with no exact hit
  (e.g. `TMUX6109`, 2026-11-03) is "not stocked", not "stocked under another
  name".

## Akizuki (akizukidenshi.com)

- **Search:** `https://akizukidenshi.com/catalog/goods/search.aspx?keyword=<kw>&search=x`.
  Each hit is a `<dl class="block-cart-i--goods ...">` block; the product link is
  `/catalog/g/g<digits>/` with the name in `title=`, price in `block-cart-i--price`, and the
  purchasable quantity in `block-cart-i--available_purchase` (the page's 通販購入可能数).
  **Product page:** `/catalog/g/g<digits>/`; its documents are under `/goodsaffix/*.pdf`.
  Space requests >= 2 s apart and back off on errors. Verified 2026-11-03 on the five
  Akizuki rows of `requirements/parts.md`. No committed tool reads Akizuki yet, so stock is
  rechecked by hand at order time (V-MFG-02).

## Datasheet text extraction

- Some vendor PDFs are encrypted (CH224Q, USB2514B on 2026-11-03). `pypdf` then
  fails with "cryptography>=3.1 is required"; install `cryptography` into the
  same **task venv** (never the global interpreter, never `~/tmp/pdfvenv`).
- Text extraction is fine for parameter tables. Pin numbers come from the
  package drawing, not from extracted text (easy-stick lesson 14.26, in its
  "Extends 14.12" paragraph: `pdftotext -layout` scrambles pin tables).

## Git

- **A rename plus a heavy rewrite in one commit loses the history link.** `git`
  scores the pair below its similarity threshold and records delete + add, so
  `git log --follow` stops at the new name. Commit the pure rename first, then
  the content. Verified 2026-11-03: `2a83480` (rename only) keeps
  `git log --follow -- design/circuit/CIRCUIT_DESIGN_Rev0.2.md` reaching
  `4dd10fb`.

## Decision records

- **"A consequence of decision Dn" is a claim to check, not a label.** List the
  alternatives Dn still leaves open; if any remain, the item is a proposal
  (Rev0.2 §14), and it must not close an open issue. Verified 2026-11-03: D12
  ("two crystals, a consequence of D11") was withdrawn after an independent
  verifier showed D11 forces only a 24 MHz hub clock; it is now P13 and OI-2 is
  open again.

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
  is itself pasted.)
- **`Path.write_text` on Windows writes CRLF.** An edit script that read LF files with
  `read_text` and saved them with `write_text(s, encoding="utf-8")` left all seven edited
  files CRLF (675 of 675 lines in CLAUDE.md, counted in the bytes on 2026-11-03). Git's
  `eol=lf` attribute normalizes the commit, but the working copy keeps CRLF until the next
  checkout. Pass `newline="\n"` to `write_text`, or use `write_bytes`.

## Design documents

- **Every derived number in a design document comes from one committed script, and every
  column uses one basis.** Verified 2026-11-03: writing `CIRCUIT_DESIGN_Rev0.3_calc.py`
  exposed full-scale currents computed with the pedestal and thresholds without it (366 µA
  vs 365 µA), which no reviewer of the document alone had flagged.
- **Quote the user verbatim, typos included, and quote every message that set the rule.**
  Verified 2026-11-03: the Rev0.3 header had "corrected" 「デカくい」 to 「デカい」 and dropped one
  line of the user's message; an independent verifier caught it.

