# USB Power-Control Hub Rev0.7, release candidate r01

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** The first release candidate of Rev0.7
> (issue #14, D40), made on the user's 「r01 を作る」 of 2026-11-19: the Rev0.6 board with J5, the SWD land,
> changed to eight bare pads at 2.54 mm at the back edge for a spring-pin clamp. No mounted part changed: the
> BOM, the CPL and the hand-solder list are Rev0.6 r02's byte for byte.
> **JLCPCB has seen none of these files.** No JLCDFM run, no placement preview and no quote was read for
> them. **Nothing was ordered or paid; the JLCPCB cart of 2026-11-19 holds Rev0.6 r01's files**, not these.
> The set becomes orderable only after the gates in "Open gates" and the user's approval (CLAUDE.md 3, 8, 12).

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.7, r01 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` |
| Source revision | Git commit `474dea4` (2026-11-19T22:22:23+09:00) holds the sources whose SHA-256 is below, with the scripts that wrote them (`make_project.py`, `make_libraries.py`, `carry.py`, `route.py`, `make_pcb.py`, `make_outputs.py`), the carried record and the router session in `design/ecad/routing/` |
| Set written | 2026-11-19 (JST) by `make_outputs.py` from the tracked board; the ten `UsbPowerHub_Main_Rev0.7_*` files are byte-identical to `manufacturing/working/rev0.7/`, written twice with the same SHA-256, which `check_outputs.py` passed (2970 checks) |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27); the user decides at the JLCPCB step with a fresh quote (CIRCUIT_DESIGN_Rev0.7.md §9) |
| Finish | leaded HASL (D30; board setting `HAL SnPb`) |
| Via class | **415 vias, every hole 0.30 mm:** 383 of 0.45 mm pad (ring 0.075 mm) and 32 of 0.60 mm pad (ring 0.150 mm). JLCPCB's standard class "0.3mm/(0.4/0.45mm)". Rev0.6 r02 had 413 |
| Solder mask, silkscreen colour | not decided |
| Assembly side | Top only (REQ-MFG-01); Economic PCBA |
| Quantities | not decided; Rev0.6's quote was read for 5 boards, 2 assembled |
| Machine-placed parts | 262 footprints, 41 LCSC parts; Extended: C2040, C2765186, C5137013 (D29, D31, D37) |
| Hand-soldered parts | 8 (`UsbPowerHub_Main_Rev0.7_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.7_ERC.json`) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.7_DRC.json`), including JLCPCB's hole figures as custom rules; the slots as capsules are measured by rule 10 of `check_routing.py`, which KiCad's DRC does not do |
| JLCPCB DFM, part mapping, placement preview | **none on these files.** Rev0.6 r01's review (`../../rev0.6/r01/JLCPCB_REVIEW.md`, 2026-11-19) records three SHA-256: this BOM's and this CPL's, which are unchanged, and Rev0.6 r01's Gerber zip's. What it read of the BOM and the CPL (part mapping 41 of 41 with 0 substituted; the placement preview) was read with another Gerber behind it. Its JLCDFM run does not carry over: the copper, the top mask, the legend and both drill files differ here |
| Quote | none on these files. Rev0.6 r01's: $52.85 without shipping on 2026-11-19 (PCB $8.00, Economic PCBA $44.85; 5 boards, 2 assembled) |
| Sourcing | the BOM is the file Rev0.5's check read (`../../rev0.5/r01/SOURCING_CHECK.md`, PASS on 2026-11-13). JLCPCB's assembly stock was read again on 2026-11-19 for the 41 codes (all above 500; `../../rev0.6/r01/JLCPCB_REVIEW.md` section 3), and the Akizuki stock of the five hand-soldered part types on the same day (`../../rev0.6/r01/RELEASE_MANIFEST.md`). The stock moves, and the check is repeated before payment |
| EasyEDA import (D32) | `../../rev0.4/r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in; not run on Rev0.7 |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## What changed against Rev0.6 r02

Compared file by file with `../../rev0.6/r02/` on 2026-11-19:

| File | Against Rev0.6 r02 |
|---|---|
| `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv`, `_HandSolder.csv` | byte-identical |
| `_ERC.json`, `_DRC.json` | byte-identical |
| `_Schematic.pdf`, `_Assembly_Top.pdf`, `_Preview_Top.png`, `_Preview_Bottom.png` | differ: the revision in the title block, and J5 |
| `_Gerber.zip` | the same 15 members by name. With the revision text made equal, the outline and the bottom paste are the same text and the 13 others differ. A text comparison does not tell a moved shape from a renumbered aperture, so the list below is from the drill files and from the board, not from the layers' text |

The holes, from the two Excellon files:

- Plated: 473 hits, 471 on Rev0.6 r02. Six are new and four are gone, all between x = 41.9 and 54.5 mm and
  y = 67.8 and 70.8 mm, at J5: new at (41.96, 69.13), (42.055, 70.4), (46.945, 70.4), (49.6, 70.8),
  (49.62, 67.85), (54.5, 69.75); gone at (43.85, 68.1), (45.77, 67.846), (48.6, 68.7), (49.2, 70.4).
- Non-plated: 12 hits, 15 on Rev0.6 r02. The three 0.991 mm holes of the Tag-Connect land are gone
  ((41.96, 69.2), (47.04, 70.216), (47.04, 68.184)); J5 has no hole.

The board (`design/ecad/PLACEMENT_Rev0.7.md`, `design/ecad/ROUTING_Rev0.7.md`, CIRCUIT_DESIGN_Rev0.7.md §10 D40):

- J5 is the footprint `SWD_Pads_2x04_P2.54mm_D1.7mm_Clamp` at (44.5, 69.13): eight round pads of 1.7 mm on
  F.Cu with a mask opening and no paste, pad 1 square. Edge row, 1.60 mm inside the back edge: 1 SWDIO, 3 GND,
  5 GND, 7 SWCLK at x = 40.69, 43.23, 45.77, 48.31 mm. Inner row, 4.14 mm inside the edge: 2 V3V3, 4 RUN,
  6 and 8 not connected.
- Rev0.6's copper is carried except at J5; 17 route rows and 5 patch rows of the routing document draw the
  tracks there, and a new router session joins the rest.
- The legend names J5's pads in two rows (`1 SWDIO 3 GND 5 GND 7 SWCLK`, `2 V3V3 4 RUN 6 NC 8 NC`).

## Files

| File | Content |
|---|---|
| `UsbPowerHub_Main_Rev0.7_Assembly_Top.pdf` | assembly drawing |
| `UsbPowerHub_Main_Rev0.7_BOM_JLCPCB.csv` | JLCPCB BOM of the machine-placed parts, one row per LCSC code |
| `UsbPowerHub_Main_Rev0.7_CPL_JLCPCB.csv` | JLCPCB placement list, board frame, mm, degrees counter-clockwise; the receptacle's Mid Y carries its model shift (`design/ecad/jlcpcb_model_frame.json`) |
| `UsbPowerHub_Main_Rev0.7_DRC.json` | kicad-cli DRC report with schematic parity, every severity |
| `UsbPowerHub_Main_Rev0.7_ERC.json` | kicad-cli ERC report, every severity |
| `UsbPowerHub_Main_Rev0.7_Gerber.zip` | Gerbers (Protel extensions), Excellon drill files and drill maps; origin = the board's lower-left corner |
| `UsbPowerHub_Main_Rev0.7_HandSolder.csv` | the parts the user solders by hand (D13) |
| `UsbPowerHub_Main_Rev0.7_Preview_Bottom.png` | 3D render, bottom |
| `UsbPowerHub_Main_Rev0.7_Preview_Top.png` | 3D render, top |
| `UsbPowerHub_Main_Rev0.7_Schematic.pdf` | the schematic, every sheet |
| `SHA256SUMS.txt` | SHA-256 of every file above and of this manifest; `sha256sum -c SHA256SUMS.txt` |

The ECAD source is not copied here: it is tracked in `design/ecad/source/` and identified by the hashes below;
copy it in at approval.

## Sources

| File | SHA-256 |
|---|---|
| `design/ecad/source/adc.kicad_sch` | `a93ba29c411fba16ef2f1bb056c1536dda270a99ad8f93c82cd9cbf52bf72f35` |
| `design/ecad/source/channel_a.kicad_sch` | `81725c5c177a7afa4327c05ade5a6b9116a7eb2c766fc9ad77ec7256bea15c16` |
| `design/ecad/source/channel_b.kicad_sch` | `690831afcbe3338789d644abeb67ab76421bdfcc409d2f23a4c3a22bb7545d74` |
| `design/ecad/source/hub.kicad_sch` | `9c18b278534cbc5cab0b3386d905442f27fb3b6ff27f3e326d24812e4edd23b1` |
| `design/ecad/source/mcu.kicad_sch` | `6a1cb73a9f8a44463dd97d6d03a6dae04a3e9c622b438410f53921549d3a08dc` |
| `design/ecad/source/power.kicad_sch` | `9fca702b8226e2ce9d9c5b7b658682a978b9169ac812a39d41a886e585c796af` |
| `design/ecad/source/usb-power-hub.kicad_dru` | `0eb695361c6ea3b2486ae65fb340897cb3e36312ce58b77c25db4fbd5cfa2e8a` |
| `design/ecad/source/usb-power-hub.kicad_pcb` | `35294b5d44efbd1b792cdf4bea1a6537804437c6528ec7ec480ee579fdb0d213` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `f500133eba9545d412906d0d57a0291252a978345b4eff93171fca09267fbb26` |

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| JLCDFM on this Gerber | **not run.** Rev0.6's run does not carry over. The user's two decisions of 2026-11-19 on Rev0.6 concern copper that is carried here (the GND via beside D1 pad 3, 「受け入れる」; the 0.60 mm slots, 「このまま」); the non-plated holes that JLCDFM listed as plated wait for the order | Claude (run), user |
| Part mapping and placement preview | not run with this Gerber. The BOM and the CPL are the two files Rev0.6 r01's gate read (41 of 41, 0 substituted). "Confirm Parts Placement" is the user's choice | Claude (run), user |
| Quote and cart | not read. The cart saved on 2026-11-19 holds Rev0.6 r01's Gerber zip: it must be replaced by this one before an order, or the order makes the Tag-Connect land. Nothing in the cart is deleted without the user's OK | Claude (upload), user (cart, order) |
| Sourcing | read on 2026-11-19 for the same BOM and hand-solder list; to be repeated before payment | Claude, before payment |
| Independent check of the set | **run on 2026-11-19, passed**, on these files against the tracked board (`design/ecad/README.md`, *Independent check of a candidate set*). `independent_check_sets.py`: 30 checks, 0 failed; 8 corruptions, 0 missed. `independent_check_positions.py`, with Rev0.5 r02 as the foreign set (Rev0.6's CPL is this one's byte for byte): 13 checks, 0 failed; 16 corruptions, 0 missed. Neither reads the copper, mask or silkscreen Gerbers. On the board: `check_pcb.py`, `check_routing.py` and `check_silk.py` pass, and a fresh-context verifier passed the nine criteria of `.claude/goal-loop/rev07-swd-pads/rubric.md` | Claude |
| The clamp on J5 | **not tried.** The clamp is the variant "2.54mm Double row 4P" of an AliExpress listing without a dimensioned drawing (D40); its row distance, its reach and its pin diameter are not known. The user does not measure it before manufacture (2026-11-19: 「まあ、届くよ」, 「図らなくていいよ」); the first board is the check | user (first board) |
| Mechanical overlay | the enclosure and the lid PCB are drawn for the Rev0.6 board (Enclosure Rev0.2, Lid Rev0.2). They are not redrawn for Rev0.7, and `design/mechanical/` still reads `board_interface_Rev0.6.json`: neither was checked against the new land or against a clamp that takes the board's edge from above and below | Claude (redraw), user (print, cables) |
| EasyEDA import (D32) | blocked at the user's sign-in | user |
| The open issues of CLAUDE.md 11 | OI-1, OI-5, OI-6, OI-8 (panelization, and the clamp's fit), OI-26 and OI-33 stand | user (built board, real cables) |
| User approval before any order or payment | not given | user |

## Residual risks

- **J5's land is an estimate.** The pad size (1.7 mm), the rows' distance from the edge (1.60 and 4.14 mm) and
  the row order were set without the clamp's drawing. If the clamp's rows are not 2.54 mm apart, or its jaw
  does not reach 4.2 mm, the inner row (V3V3, RUN and the two free pads) is not met; SWDIO, SWCLK and GND are in
  the edge row. A different land is a new revision.
- The gap between two J5 pads is 0.84 mm, and the two GND fan-out vias stand 0.104 mm from pads 3 and 5 (one
  net, so DRC is clean). A spring pin that lands off-centre by more than a pad's radius touches mask, not a
  neighbour, but nothing guides the pins: the board has no hole at J5.
- What the clamp's lower jaw meets was not checked. The bottom face under J5 carries tracks and vias under
  mask (B.Cu rows of the routing document run there), and a jaw that presses on it, or one with pins of its
  own, presses on that mask.
- **No JLCPCB tool has read this set.** Every JLCDFM judgement on record is of another Gerber zip.
- The risks of Rev0.6 r02's manifest that concern carried copper and unchanged parts stand
  (`../../rev0.6/r02/RELEASE_MANIFEST.md`, *Residual risks*): the GND via 0.059 mm from D1 pad 3, the 0.60 mm
  slots, the 13 vias in pads, the non-plated drill file read as plated, the CPL's frame, port B's copper at
  39.12 mΩ of 40 mΩ (not recomputed by hand here; `check_routing.py` passes its limit), the routing document's
  *Not settled*, U1's plane webs, the zone filler's non-determinism, OI-33 and OI-26, and MCP3208-CI/P's
  falling stock at Akizuki.
- The independent check takes the board file as its reference. It shows that the BOM, the CPL, the hand-solder
  list, the Top paste Gerber and the two drill files are this board's, not that the board is right.
- The legend was judged in KiCad's render, not on a printed board (OI-6).
- Nothing has been built or measured. The open issues of CLAUDE.md 11 stand; the set is not orderable until each
  is closed.
