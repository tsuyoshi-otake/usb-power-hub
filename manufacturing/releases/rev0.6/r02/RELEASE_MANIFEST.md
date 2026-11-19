# USB Power-Control Hub Rev0.6, release candidate r02

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** r02 supersedes r01 (issue #13): the
> same board with its silkscreen legend changed, after the user read the legend in a render on 2026-11-19 and
> chose 「直して r02」. No net, part, pad, track, via, zone or hole changed: of the Gerber zip's 15 members only
> `F_Silkscreen.gto` differs from r01's, and the BOM, the CPL and the hand-solder list are r01's byte for byte.
> **JLCPCB has not seen this Gerber zip.** r01's gate of 2026-11-19 (`../r01/JLCPCB_REVIEW.md`) read r01's zip
> with this BOM and this CPL. **Nothing was ordered or paid; the JLCPCB cart of 2026-11-19 holds r01's
> files**, not these. The set becomes orderable only after the gates in "Open gates" and the user's approval
> (CLAUDE.md 3, 8, 12).

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.6, r02 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` |
| Source revision | Git commit `850e817` (2026-11-19T21:23:08+09:00) holds the sources whose SHA-256 is below, with the scripts that wrote them (`make_project.py`, `carry.py`, `route.py`, `make_pcb.py`, `make_outputs.py`), the carried record and the router session in `design/ecad/routing/` |
| Set written | 2026-11-19 (JST), after r01, by `make_outputs.py` from the tracked board; the ten `UsbPowerHub_Main_Rev0.6_*` files are byte-identical to `manufacturing/working/rev0.6/`, which `check_outputs.py` passed (2970 checks) |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27); the user decides at the JLCPCB step with a fresh quote (CIRCUIT_DESIGN_Rev0.6.md §9) |
| Finish | leaded HASL (D30; board setting `HAL SnPb`) |
| Via class | **413 vias, every hole 0.30 mm:** 381 of 0.45 mm pad (ring 0.075 mm) and 32 of 0.60 mm pad (ring 0.150 mm). JLCPCB's standard class "0.3mm/(0.4/0.45mm)". Rev0.5 r02 had 397 |
| Solder mask, silkscreen colour | not decided; the quote of 2026-11-19 took the form's defaults (green, white) |
| Assembly side | Top only (REQ-MFG-01); Economic PCBA |
| Quantities | not decided; the quote of 2026-11-19 was read for 5 boards, 2 assembled |
| Machine-placed parts | 262 footprints, 41 LCSC parts; Extended: C2040, C2765186, C5137013 (D29, D31, D37) |
| Hand-soldered parts | 8 (`UsbPowerHub_Main_Rev0.6_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.6_ERC.json`) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.6_DRC.json`), including JLCPCB's hole figures as custom rules; the slots as capsules are measured by rule 10 of `check_routing.py`, which KiCad's DRC does not do |
| JLCPCB DFM, part mapping, placement preview | **not run on this Gerber zip.** r01's review (`../r01/JLCPCB_REVIEW.md`, 2026-11-19) records three SHA-256: this BOM's and this CPL's, which are unchanged, and r01's Gerber zip's, which is not this one's. What it read of the BOM and the CPL (part mapping 41 of 41 with 0 substituted; the placement preview) was read with r01's Gerber behind it; the copper, mask, paste, outline and drill members it judged in JLCDFM are byte-identical here. Its silkscreen rows were not read then ("silkscreen over a plugged via" was judged by measurement), and r02 adds 12 labels. The user's two decisions of 2026-11-19 stand (the GND via beside D1 pad 3, 「受け入れる」; the 0.60 mm slots, 「このまま」) |
| Quote | none on these files. r01's: $52.85 without shipping on 2026-11-19 (PCB $8.00, Economic PCBA $44.85; 5 boards, 2 assembled), and $53.90 with "Confirm Production file" (the user's choice of that day, without automatic confirmation). A legend does not enter JLCPCB's price formula as far as the quote form shows, but no quote was read for r02 |
| Sourcing | the BOM is the file Rev0.5's check read (`../../rev0.5/r01/SOURCING_CHECK.md`, PASS on 2026-11-13, SHA-256 below). JLCPCB's assembly stock was read again on 2026-11-19 for the 41 codes (all above 500; `../r01/JLCPCB_REVIEW.md` section 3), and the Akizuki stock of the five hand-soldered part types on the same day (all in stock for 2 boards; `../r01/RELEASE_MANIFEST.md`). The stock moves, and the check is repeated before payment |
| EasyEDA import (D32) | `../../rev0.4/r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in; not run on Rev0.6 |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## What changed against r01

Compared file by file with `../r01/` on 2026-11-19:

| File | Against r01 |
|---|---|
| `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv`, `_HandSolder.csv` | byte-identical |
| `_Schematic.pdf`, `_ERC.json`, `_DRC.json`, `_Assembly_Top.pdf`, `_Preview_Bottom.png` | byte-identical |
| `_Gerber.zip` | the same 15 members; 14 are byte-identical (the four copper layers, both masks, both pastes, the outline, the bottom legend, the two drill files and their maps) and `F_Silkscreen.gto` differs |
| `_Preview_Top.png` | shows the new legend |

The board file: with its own `gr_text` nodes and every UUID taken out, the board of commit `850e817` is the
board r01 was made from, node for node (`make_pcb.py` numbers the UUIDs in order, so new texts shift them).

The legend (`design/ecad/PLACEMENT_Rev0.6.md`, *Silkscreen*: 44 labels, 32 in r01):

- Moved, because each read as one word with its neighbour on the same line: `DVDD` (0.30 mm from `CLKOUT`),
  `V_J4` (0.33 mm from `HOLD_M_A`), `V5L` (0.27 mm from `HOLD_M_B`). `check_silk.py` now asks for 1.0 mm.
- Added at the programming parts, which CLAUDE.md 6 asks for: `BOOT` beside SW3, `SWD` beside J5, and a legend
  of J5's six pads in two rows to its right (`2 SWDIO 4 SWCLK 6 NC` above `1 V3V3 3 RUN 5 GND`, as the pad rows
  stand). The pads' 1.27 mm pitch does not take a 1.0 mm text at each pad.
- Added at the eight hand-soldered parts, their references: `F1`, `U5`, `U7`, `U17`, `RS10`, `RS11`, `RS20`,
  `RS21`. Every other reference stays hidden.

## Files

| File | Content |
|---|---|
| `UsbPowerHub_Main_Rev0.6_Assembly_Top.pdf` | assembly drawing |
| `UsbPowerHub_Main_Rev0.6_BOM_JLCPCB.csv` | JLCPCB BOM of the machine-placed parts, one row per LCSC code |
| `UsbPowerHub_Main_Rev0.6_CPL_JLCPCB.csv` | JLCPCB placement list, board frame, mm, degrees counter-clockwise; the receptacle's Mid Y carries its model shift (`design/ecad/jlcpcb_model_frame.json`) |
| `UsbPowerHub_Main_Rev0.6_DRC.json` | kicad-cli DRC report with schematic parity, every severity |
| `UsbPowerHub_Main_Rev0.6_ERC.json` | kicad-cli ERC report, every severity |
| `UsbPowerHub_Main_Rev0.6_Gerber.zip` | Gerbers (Protel extensions), Excellon drill files and drill maps; origin = the board's lower-left corner |
| `UsbPowerHub_Main_Rev0.6_HandSolder.csv` | the parts the user solders by hand (D13) |
| `UsbPowerHub_Main_Rev0.6_Preview_Bottom.png` | 3D render, bottom |
| `UsbPowerHub_Main_Rev0.6_Preview_Top.png` | 3D render, top |
| `UsbPowerHub_Main_Rev0.6_Schematic.pdf` | the schematic, every sheet |
| `SHA256SUMS.txt` | SHA-256 of every file above and of this manifest; `sha256sum -c SHA256SUMS.txt` |

The ECAD source is not copied here: it is tracked in `design/ecad/source/` and identified by the hashes below;
copy it in at approval.

## Sources

| File | SHA-256 |
|---|---|
| `design/ecad/source/adc.kicad_sch` | `aa590d8486ef2cddacac207e0410152467fea7f4b60044592acf798de39ed3a2` |
| `design/ecad/source/channel_a.kicad_sch` | `0c80d6e192e96f2e0b3240a89a563860fd1c5435fe7f6937edc76440c156cf5c` |
| `design/ecad/source/channel_b.kicad_sch` | `34096e4f8e21478b1d535880e9164e1ef2519bf87a42cedab8bbb8cac57686cf` |
| `design/ecad/source/hub.kicad_sch` | `08db1cac38a4860bb27eed1fe5a4478571222260019a6a794316b96199514014` |
| `design/ecad/source/mcu.kicad_sch` | `f890b5f00910a106d2335e6de0d952015636a37739122835b4fc9f73c0cceba3` |
| `design/ecad/source/power.kicad_sch` | `0eb7f4a81b38e27451352e25d47671e5db17380c14ba4fc869ecaa6cb30534cf` |
| `design/ecad/source/usb-power-hub.kicad_dru` | `0eb695361c6ea3b2486ae65fb340897cb3e36312ce58b77c25db4fbd5cfa2e8a` |
| `design/ecad/source/usb-power-hub.kicad_pcb` | `2d5193e7fe906eb7abe6c1c1fe4da1ae3918da55d76649e97de1c605f73cd4ee` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `d8aaca5061a6f72b1d719d4b35e3a59ddce04d5db1349dcb3b746956ee07a343` |

## Akizuki stock (V-MFG-02, the hand-soldered parts)

The hand-solder list is r01's file, and its stock was read on 2026-11-19 (`../r01/RELEASE_MANIFEST.md`,
*Akizuki stock*: all five part types in stock for 2 boards; MCP3208-CI/P marked 在庫僅少 at 41 packs). The
user's Akizuki basket was filled with them that evening at the user's request; no order of it is recorded here.

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| JLCDFM on this Gerber | **not run.** r01's run judged members that are byte-identical here; the legend member is new. The user still decides on the non-plated holes that JLCDFM lists as plated, and chose "Confirm Production file" for it on 2026-11-19 (in the cart, on r01's files) | Claude (run), user |
| Part mapping and placement preview on this BOM and CPL | r01's readings of 2026-11-19, on the same two files: 41 of 41, 0 substituted; J1-J4 and the 7 other moved parts that are not symmetrical read in the preview, one instance of each other class. A viewer reading, not JLCPCB's pick-and-place; "Confirm Parts Placement" is the user's choice | user |
| Quote and cart | not read for r02. The cart saved on 2026-11-19 holds r01's Gerber zip: it must be replaced by this one before an order, or the order makes r01's legend | Claude (upload), user (cart, order) |
| Sourcing | Rev0.5's check of 2026-11-13 read the same BOM file; JLCPCB's stock was read again on 2026-11-19, and so was the Akizuki stock (`../r01/RELEASE_MANIFEST.md`: all five part types in stock for 2 boards; MCP3208-CI/P is marked 在庫僅少 at 41 packs); to be repeated before payment | Claude, before payment |
| Independent check of the set | **run on 2026-11-19, passed**, on these files against the tracked board (`design/ecad/README.md`, *Independent check of a candidate set*). `independent_check_sets.py`: 30 checks, 0 failed; 8 corruptions, 0 missed. `independent_check_positions.py`, with Rev0.5 r02 as the foreign set: 13 checks, 0 failed; 16 corruptions, 0 missed (with r01 as the foreign set it misses 3, as it must: r01's CPL, paste and drill files are these). Neither reads the silkscreen Gerber. The legend is checked on the board by `check_silk.py` (3366 checks, 0 failed; 37 negative tests pass) and was read in a render of the board by Claude | Claude |
| Mechanical overlay | the enclosure and the lid PCB are drawn for this board on paper (Enclosure Rev0.2 and Lid Rev0.2, issue #13 step 7; `design/mechanical/`); nothing is printed and no cable was tried | user (print, cables) |
| EasyEDA import (D32) | blocked at the user's sign-in | user |
| The open issues of CLAUDE.md 11 | OI-1, OI-5, OI-6, OI-8 (panelization), OI-26 and OI-33 stand | user (built board, real cables) |
| User approval before any order or payment | not given | user |

## Residual risks

- **The JLCPCB review of 2026-11-19 is JLCDFM's and a viewer's reading, not JLCPCB's production check**
  (`../r01/JLCPCB_REVIEW.md`), and it read r01's Gerber zip, not this one. JLCDFM's Danger items (via annular ring of the 0.30 mm vias, THT-to-SMD distance, mask
  opening exposing a trace, pad spacing, pad to line spacing, silkscreen over a plugged via, the receptacles'
  plated-slot width) are judged there against measurements on the board, not row by row. JLCDFM's list of items
  changed since Rev0.5's run, and no control run of Rev0.5's Gerber was made.
- A GND via carried from Rev0.5's routing stands 0.059 mm from pad 3 (GND) of D1, which D39 moved beside it: one
  net, so DRC is clean, but the mask between them may not hold. Two older pairs are alike (C27 pad 2 0.090 mm,
  TP13 0.095 mm). No checker of the repository measures a pad against a via of its own net. The user accepted
  the pair as it is on 2026-11-19 (「受け入れる」); the first boards show whether D1's joint wets onto the via.
- The receptacles' 16 plated slots stay 0.60 mm wide, the maker's land (D37), by the user's decision of
  2026-11-19 (「このまま」): under JLCDFM's Danger limit of 0.61 mm and above the 0.35 mm that JLCPCB's
  capabilities page gave on 2026-11-13. JLCPCB's own DFM after an order may still object; a wider slot is a new
  revision. Whether the shell legs reach through them on a 1.6 mm board is OI-33, another question.
- The independent check of 2026-11-19 takes the board file as its reference. It shows that the BOM, the CPL, the
  hand-solder list, the Top paste Gerber and the two drill files are this board's, not that the board is right.
  It does not read the copper, mask or silkscreen Gerbers or a pad's shape.
- The ADC's stock at Akizuki is falling: MCP3208-CI/P (g100238) stood at 72 packs on 2026-11-13 and at 41 on
  2026-11-19, marked 在庫僅少; two boards need 4. If it is sold out when the order is placed, U7 and U17 have no
  second source recorded (`requirements/parts.md`), and the choice of one is the user's (D13).
- 13 via holes stand in a pad, as on Rev0.5: 5 in U1's exposed pad, 6 in U6's, and a 0.60 mm via in pad 3 of
  Q18 and of Q38. Solder can wick into them (V-MFG-03).
- JLCDFM's viewer lists the non-plated drill file as a plated layer, although the file declares itself
  non-plated; how JLCPCB's CAM reads the 15 non-plated holes is seen only in its production file.
- The CPL's origin is the board's lower-left corner. Its Mid is the footprint's origin, plus the JLCPCB model
  shift of `design/ecad/jlcpcb_model_frame.json` for the receptacle C2765186 (J1-J4), and its angles are KiCad's
  plus the model rotation of that table (easy-stick 14.18). The table holds what JLCPCB's placement previews
  showed on Rev0.4's and Rev0.5's files, to about 0.04 mm. A preview is the drawing of JLCPCB's model, not its
  pick-and-place.
- Port B's copper is 39.12 mOhm of the 40 mOhm the circuit document allows (port A 35.24 mOhm): 0.88 mOhm to
  spare, computed from the 2-D copper at the stackup's nominal thickness, not measured.
- The routing document's *Not settled* stands: L3 tracks run beside VBUS_B's trunk and through the corner of the
  ADC's supply block; the MAU104 stands nearer the reference block than on Rev0.5; some joined nets run long
  (EN_B 88.9 mm and DIS_B 83.5 mm, which were 52.7 and 49.4 mm; the four taps 103.3-111.2 mm). `check_routing.py`
  has no length rule.
- Rev0.5's routing is carried where it still stands (2,005 track segments and 205 vias), and the new router
  session adds 251 segments of which 204 are shorter than 1.0 mm and two repeat a carried segment exactly. DRC
  reads the result as clean; why the router draws them was not looked into.
- U1's exposed pad keeps 1.65-1.80 mm of plane copper on its sides, against rule 9's 1.60 mm; the L2 plane is
  checked in the 2-D fill KiCad writes, not in the return currents.
- The board file is the source of truth, not `make_pcb.py`: KiCad's zone filler is not deterministic (measured on
  the Rev0.5 board, `design/ecad/README.md`). This set was made from the tracked board (SHA-256 above). A
  regenerated board can differ in its fill, and a changed Gerber needs a new set.
- The receptacle's land is the maker's, drawn for a 0.80 mm board; this one is 1.6 mm (OI-33). The data-line taps
  (D38) are stubs on the D+ and D- of OUT A and OUT B (OI-26).
- The legend was judged in KiCad's render, not on a printed board: whether JLCPCB's print keeps 1.0 mm text
  with a 0.17 mm line legible is OI-6. The SWD legend stands 5 mm from J5 and names the pads by number; the
  pads carry no number, only J5's pin-1 mark, so a reader must know that the rows mirror the pad rows.
- SW1 and SW2 have no label on this board; the lid carries their legend.
- Nothing has been built or measured. The open issues of CLAUDE.md 11 stand; the set is not orderable until each
  is closed.
