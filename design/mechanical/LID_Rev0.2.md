# Lid PCB Rev0.2 — the enclosure's top panel (issues #11 and #13)

> **WIP — MANUFACTURING PROHIBITED. NOT ORDERED.** The lid of the enclosure Rev0.4
> (`ENCLOSURE_Rev0.4.md`, E3 and E8), which is drawn for the Rev0.7 main board, as a KiCad
> board. Nothing is ordered, no release exists, and JLCPCB has not seen the files. The legend
> is a first proposal: the user has not seen it on a board.
>
> **Rev0.2 against Rev0.1 (2026-11-19, issue #13).** The main board's connectors stand
> mirror-symmetric since Rev0.6 (D39), and the lid follows through the interface: HOST moved
> from x = 76.0 to 82.5 mm and OUT B from 51.3 to 82.5 mm; OUT B's button hole moved from
> x = 65.3 to 68.5 mm and its window from the button's left to its right (x = 69.1–71.4 mm).
> OUT A's and 5V IN's ports, OUT A's button and window, the pinhole over SW3 and the four screw
> holes stand where they stood. No parameter of §4 changed, and of §5 only the revision's text.
> Lid Rev0.1 was never ordered; its files are in Git history, at commit `de432d1`.

## 1. What it is

A bare 2-layer FR-4 board, 100 × 72 × 1.6 mm, with no part and no net. It lies on the
enclosure's frame, held by four pan-head M2 screws, and does four things:

| Feature | How |
|---|---|
| Closes the case | The main board's outline (E3). |
| Lets the two buttons through | A hole over SW1 and over SW2, for the printed plungers. |
| Shows the four LEDs | A window of bare FR-4 over each port's two LEDs (green: port on, red: port fault), with copper round it on both sides so that only the window lights up. |
| Reaches BOOT | A pinhole over SW3 (REQ-BOOT-02). |
| Names the ports | The silkscreen legend (CLAUDE.md §6). |

## 2. Sources

- **The interface.** `assembly/UsbPowerHub_Enclosure_Rev0.4_LidInterface.json`, which
  `make_enclosure.py` writes from the enclosure document and the main board: the outline, the
  thickness, the seven holes, the two windows and the four ports' positions. No script holds a
  value of it, and this document names its sizes only to describe the board (§1, §7): the
  interface decides. Its frame is the main board's (origin at the
  lower-left corner, x right, y up, mm), seen from above: the front edge (y = 0) is over OUT A
  and OUT B.
- **This document** holds what the interface cannot: how far copper stays from an edge, a hole
  and a window (§4), and the legend (§5). `scripts/make_lid.py` reads both tables; a value is
  changed here and nowhere else.
- **The board.** `lid/usb-power-hub-lid.kicad_pcb` is written by `make_lid.py` and never edited
  in KiCad. Its title block carries the SHA-256 of the two tables and of the interface file,
  so a board built from other values is found (L01).

## 3. Decisions

All made by Claude under the 2026-11-03 delegation, after the user's 「作図する」 (2026-11-18).
Each is provisional and the user may revert any one.

| ID | Decision | Why | Rejected |
|---|---|---|---|
| K1 | 2 copper layers, 1.6 mm FR-4, 1 oz, no named stackup. | The lid carries no signal, so CLAUDE.md §5.1's stackup rule (impedance against a named stackup) has nothing to apply to. 1.6 mm is the interface's `lid_t`. | A thinner lid (the enclosure's posts and plungers are drawn for 1.6 mm). |
| K2 | Copper on both sides, one pour per side, with no net and no connection to anything. | Copper stops the LEDs' light: only the windows light up. The same copper on both sides keeps the panel flat. No via and no exposed pad, so the pours are closed in by solder mask. | No copper (the whole lid would glow round each window). Copper on one side (bows). Tying the pours to the screws (a screw head would then be a bare contact to a floating plate). |
| K3 | Copper stays `edge_clear` from the outline, `hole_clear` from a button hole and the pinhole, `head_clear` from the circle a screw head covers, and `window_clear` from a window. | No copper at a routed edge or a drilled wall, none under a screw head that could cut through the mask, and none in a mask opening: nothing is left bare, so the finish coats nothing. | Plated holes (a plated wall wears off on a plunger). |
| K4 | All seven holes are unplated. | They are mechanical. | — |
| K5 | A window is an opening in the solder mask on both sides, exactly the interface's rectangle, with no copper and no silkscreen in it. | E8: bare FR-4 passes an LED's light. | A drilled window (dust), a light pipe (D13: few part types). |
| K6 | Legend on the top: the product name, `Lid Rev0.2`, a label and an arrow for each port, a ring round each button hole, `BOOT` at the pinhole. Port labels are 3.0 mm high. | CLAUDE.md §6: product name, revision and port labels, Latin, at least 1.0 mm. HOST and 5V IN are the same receptacle on one edge and can be swapped (the 2026-11-13 answer on the ports' positions), so their labels are large and each has an arrow at its port. A button stands 14 mm from its port's arrow, towards the lid's middle, and 51 mm from the other port's. | Kanji (CLAUDE.md §6). A label for the LEDs (two colours in one window; the manual explains them). |
| K7 | Finish, solder mask and silkscreen colours are not chosen here. | No copper is bare, so any finish does. The colours are the user's (the main board's are not decided either). | — |
| K8 | The bottom silkscreen carries the board's name and the text `JLCJLCJLCJLC`. | JLCPCB prints its order number on a board. From memory, not read in this session: with the form's "specify a location" option it prints the number in place of that text. On the bottom it is inside the case. Without the option the text is only a hidden line of letters. | An order number on the top face. |

## 4. Parameters

`Kind`: **design** = chosen here and free to change; **world** = a demand the checker makes
on the design. All in mm, except `stroke_ratio`.

<!-- lid-params:begin -->
| Name | Value | Meaning | Kind |
|---|---:|---|---|
| `edge_clear` | 0.5 | Copper to the lid's outline. | design |
| `hole_clear` | 0.5 | Copper to the edge of a button hole or the pinhole. | design |
| `head_clear` | 0.25 | Copper to the circle a screw head covers (`keepout_d` in the interface). | design |
| `window_clear` | 0.2 | Copper to the edge of a window. | design |
| `zone_min` | 0.25 | Narrowest copper the fill keeps. | design |
| `arrow_w` | 3.0 | Width of a port arrow's base. | design |
| `arrow_h` | 2.0 | Height of a port arrow, base to tip. | design |
| `arrow_tip` | 0.8 | A port arrow's tip to the lid's edge. | design |
| `ring_d` | 6.4 | Centre-line diameter of the ring round a button hole. | design |
| `ring_stroke` | 0.3 | Line width of that ring. | design |
| `copper_edge_min` | 0.3 | Copper to the outline, demanded (CLAUDE.md §5.3). KiCad's DRC does not measure a pour against the outline (§6), so the checker does. | world |
| `copper_hole_min` | 0.25 | Copper to a drilled wall, demanded (the project's DRC rule, the main board's value). | world |
| `text_min_h` | 1.0 | Text height the checker demands (CLAUDE.md §6; JLCPCB's legend limit). | world |
| `stroke_min` | 0.15 | Line width the checker demands of every silkscreen line. | world |
| `stroke_ratio` | 6 | The checker demands a text stroke of at least height / this (JLCPCB's 1:6). | world |
| `silk_edge_min` | 0.5 | Silkscreen to the lid's outline, demanded. | world |
| `silk_hole_min` | 0.3 | Silkscreen to a hole's edge, to a screw head's circle and to a window, demanded. | world |
| `silk_gap_min` | 0.2 | Between two silkscreen items, demanded. | world |
| `port_x_tol` | 0.5 | A port label's ink centre, and its arrow's tip, to the port's x, demanded. | world |
| `label_near` | 3.0 | The `BOOT` label's ink to the pinhole's edge, at most, demanded. | world |
| `copper_slack` | 0.3 | Width of the band round every keep-clear area in which the checker does not demand copper. | world |
<!-- lid-params:end -->

## 5. Legend

One row per text. `Side`: `top` (F.SilkS) or `bottom` (B.SilkS, mirrored). `Anchor`:
`centre` (the lid's centre), a hole of the interface (its centre), or a port of the interface
(the point of the lid's edge above the port). `dx`, `dy` move the text's centre from the
anchor; for a port, `dx` runs along the edge and `dy` into the lid. `Height` is KiCad's glyph
size (width = height) and `Stroke` its line width, in mm. Every text reads left to right from
the front.

The arrows and the rings are not rows: `make_lid.py` draws one arrow per port of the
interface and one ring per button hole, from §4.

<!-- lid-legend:begin -->
| Label | Side | Text | Anchor | dx | dy | Height | Stroke |
|---|---|---|---|---:|---:|---:|---:|
| title | top | USB Power-Control Hub | centre | 0 | 4 | 3.0 | 0.5 |
| revision | top | Lid Rev0.2 | centre | 0 | -1.5 | 1.5 | 0.25 |
| J1 | top | HOST | J1 | 0 | 6.5 | 3.0 | 0.5 |
| J2 | top | OUT A | J2 | 0 | 6.5 | 3.0 | 0.5 |
| J3 | top | OUT B | J3 | 0 | 6.5 | 3.0 | 0.5 |
| J4 | top | 5V IN | J4 | 0 | 6.5 | 3.0 | 0.5 |
| SW3 | top | BOOT | SW3 | 5.75 | 0 | 1.5 | 0.25 |
| ident | bottom | USB Power-Control Hub Lid Rev0.2 | centre | 0 | 4 | 1.5 | 0.25 |
| order | bottom | JLCJLCJLCJLC | centre | 0 | -6 | 1.0 | 0.17 |
<!-- lid-legend:end -->

## 6. What the checker proves, and what it cannot see

`scripts/check_lid.py` loads a copy of the board as written and measures it against the
interface and §4–§5. It does not import `make_lid.py`: the copper is the fill the board file
holds, the silkscreen is the ink pcbnew draws for each text and shape, and every keep-clear
area is built by the checker from the interface. On the repository's files it prints 44
lines, and 59 with `--outputs` (L12–L16).

| Check | Proves | Demand |
|---|---|---|
| L01 | The board was built from this document's two tables and from this interface file (the SHA-256 in its title block); the title block carries `Rev0.2` and `WIP`; the board and its project file end their lines with LF, as a checkout does. | CLAUDE.md §3 (state), §7 (one source) |
| L02 | 2 copper layers, the interface's thickness, one rectangle as the outline (the interface's), the plot and drill origin at the lid's lower-left corner, and no track, via, net or drawing on a copper layer. | K1, K2 |
| L03 | The board drills the interface's seven holes and no other: each one round, unplated, at its place and diameter, without a copper ring. | K4 |
| L04 | On each side: no copper within `edge_clear` of the outline or in the nine keep-clear areas (K3). And, whatever §4's design values are: none within `copper_edge_min` of the outline or `copper_hole_min` of a drilled wall. | K3, CLAUDE.md §5.3 |
| L05 | On each side copper covers the lid everywhere more than `copper_slack` from a keep-clear area; the two sides carry the same copper. | K2 |
| L06 | No mask expansion; on each side the mask is open on each window, exactly the interface's rectangle, and nowhere else but the holes; no copper lies under an opening. | K3, K5 |
| L07 | The legend table keeps its own rules: unique labels, Latin text, height at least `text_min_h`, stroke at least `stroke_min` and height / `stroke_ratio`, an anchor the interface knows; the ring and the arrows are no finer. | CLAUDE.md §6 |
| L08 | The board carries the table's texts, each at its place, size and stroke, one arrow per port and one ring per button hole as §4 says, and no other text or drawing; no footprint text would print. | §5 |
| L09 | Read from the ink, not from the table: the top names the product and the revision; over each port stands the name the checker demands of it (`HOST`, `OUT A`, `OUT B`, `5V IN`, its own list) with one arrow between the label and the edge, pointing at the edge; `BOOT` is within `label_near` of the pinhole; each button hole has one ring. | CLAUDE.md §6, K6, REQ-BOOT-02 |
| L10 | On each side the ink stays `silk_edge_min` from the outline, `silk_hole_min` from every hole, screw head and window, and `silk_gap_min` from other ink. | CLAUDE.md §6 |
| L11 | KiCad's own DRC, every severity: 0 violations, 0 unconnected items. | CLAUDE.md §8 |
| L12 | The candidate set holds its seven files and nothing else; `SHA256SUMS.txt` agrees with them; the manifest's source hashes are the board's and the project file's now; its state is `WIP`; the archive is a zip, the drawing a PDF of one page, each picture a PNG at least 1200 px wide. | CLAUDE.md §2 |
| L13 | The Gerber zip holds its eleven files; the outline Gerber draws the four sides of the interface's rectangle and nothing else; each copper Gerber runs to `edge_clear` from the outline; each mask Gerber has an opening at the four corners of each window and at every hole. | CLAUDE.md §8 (Gerber) |
| L14 | The unplated drill file holds the interface's seven holes, each at its place and diameter; the plated drill file holds none. | K4 |
| L15 | The set's DRC report is this board's: 0 violations, 0 unconnected items. | CLAUDE.md §8 |
| L16 | The zip's eleven files are KiCad's plot of this board: the checker plots the board it has just measured, with its own two `kicad-cli` calls, and compares each file text for text, the creation times apart. | CLAUDE.md §2 (one coordinated set) |

`scripts/test_check_lid.py` builds 110 lids and sets, 106 of which each break one thing, and
asserts the `FAIL` line each must give. No check ID is without a failing test.

L16 was added on 2026-11-18, after an independent verifier changed two files of a set and
restamped the checksums, and the checker passed both: one corner of the outline Gerber moved
by 0.1 mm inside its extents (L13 read the extents only), and one filled region taken out of
the top silkscreen Gerber (no check read that file). L13 now compares the outline side by
side, and L16 sees any change of any of the eleven files.

It cannot see:

- **Whether a `world` value is right.** JLCPCB's legend limits and the copper-to-edge
  distance are CLAUDE.md's values; JLCPCB's pages were not read for the lid.
- **Whether the legend reads well.** L09 finds a name over a port. It does not find a label
  a person misreads, and the pictures prove nothing.
- **What KiCad's DRC does not measure.** Measured on 2026-11-18: a pour drawn 0.1 mm from the
  outline, with 0.3 mm as the project's copper-to-edge rule, gave 0 violations from
  `kicad-cli pcb drc --severity-all`. So L11 says nothing about the pour against the outline;
  L04 measures it. Measured the same day: the script's zone filler keeps no distance by
  itself (it covered an unplated hole that had no rule area), so every keep-clear area is
  drawn by `make_lid.py` and measured here.
- **A refill in KiCad's editor.** The checker reads the fill the file holds. Whether the
  editor's refill gives the same copper was not tried; the board is not edited in KiCad (§2).
- **Whether KiCad's plot is right, and how JLCPCB reads it.** L16 proves the zip is KiCad's
  plot of this board. Of the plot itself L13 and L14 read back the outline, the copper's
  extents, points of the mask openings and the drill hits; that the plotted silkscreen is the
  legend as drawn is KiCad's word. JLCDFM was not run.
- **What the drawing and the pictures show.** L12 reads their type, the PDF's page count and
  the pictures' width. A drawing or a picture of another board, with the checksums written
  anew, passes (the verifier tried both). They are for looking at and prove nothing.
- **Light.** How bright an LED is through 1.6 mm of bare FR-4, how much passes through the
  `window_clear` gap round a window, and whether the copper stops the rest.
- **Flatness, colour, finish** (K7), and whether the interface itself is right
  (`check_enclosure.py`, E11–E13).

## 7. Manufacturing

`scripts/make_lid_outputs.py` writes a candidate set into `manufacturing/working/lid-rev0.2/`
(not tracked, not orderable): the Gerber and drill zip, a 1:1 drawing of the top, a picture
of each side, the DRC report, a `WIP` manifest and the checksums. Two runs write the same
bytes. No release exists.

| Order parameter | Value | From |
|---|---|---|
| Size | 100 × 72 mm | the interface |
| Layers, thickness, copper | 2, 1.6 mm, 1 oz | K1 |
| Holes | 7, all unplated, from 2.0 to 4.6 mm; no plated hole and no slot | the interface; K4 |
| Impedance control, stackup | none, not named | K1 |
| Finish, mask colour, silkscreen colour | not chosen | K7 |
| Order number | "specify a location", if the form offers it | K8 (from memory) |

`design/experiments/cost-estimate/README.md` puts the lid at $4.00 when it is ordered with
the main board; that figure was not read again for these files.

## 8. Not verified

- The user saw a picture of Lid Rev0.1's legend on 2026-11-18 and found the ports' places
  asymmetric (「なんかUSBの位置がアシンメトリーで変だね」), which led to D39 and to this
  revision. The user has not accepted this legend, and nobody has seen it on a manufactured
  board (OI-6). Its texts, sizes and places are a first proposal (K6).
- Nothing is ordered and JLCPCB has not seen the files: no DFM, no quote for this board.
- K8's order-number option is from memory. Without it the bottom carries a line of letters,
  and JLCPCB puts its number where it chooses, possibly on the top.
- The enclosure is not printed, so no lid has lain on a frame: the hole positions follow the
  interface, and the interface follows the enclosure's parameters, which the first print may
  change.
- The LEDs' light through the windows, and what the copper stops (§6).
- A pan head's real diameter. `keepout_d` is the enclosure's `lid_head_keepout_d`, from
  memory (`ENCLOSURE_Rev0.4.md` §8).
- JLCPCB's thickness tolerance (± 10 %) against the plungers' 0.5 mm of play.
