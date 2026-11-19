# USB Power-Control Hub Rev0.6, release candidate r01

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** r01 is the first candidate set of
> Rev0.6 (issue #13): the board with its four USB-C receptacles mirror-symmetric about x = 50 mm (D39). No net
> and no part changed against Rev0.5; the copper, the silkscreen and the CPL are new. The JLCPCB gate ran on
> these files on 2026-11-19 (`JLCPCB_REVIEW.md`): JLCDFM, part mapping, the placement preview and a quote. It
> changed no file and left decisions for the user. **Nothing was ordered or paid.** The set becomes orderable
> only after the gates in "Open gates" and the user's approval (CLAUDE.md 3, 8, 12).

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.6, r01 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` |
| Source revision | Git commit `010695e` (2026-11-19T13:35:10+09:00) holds the sources whose SHA-256 is below, with the scripts that wrote them (`make_project.py`, `carry.py`, `route.py`, `make_pcb.py`, `make_outputs.py`), the carried record and the router session in `design/ecad/routing/` |
| Set written | 2026-11-19 (JST) by `make_outputs.py` from the tracked board; the ten `UsbPowerHub_Main_Rev0.6_*` files are byte-identical to `manufacturing/working/rev0.6/`, which `check_outputs.py` passed (2970 checks) |
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
| JLCPCB DFM, part mapping, placement preview | run on these files on 2026-11-19, **not accepted** (`JLCPCB_REVIEW.md`). Part mapping 41 of 41, 0 substituted. Placement preview: the four receptacles and every moved part that is not symmetrical read, one instance of each other class. JLCDFM: every Danger item judged against measurements; of its three findings the user accepted one on 2026-11-19 (a GND via 0.059 mm from D1 pad 3, 「受け入れる」) and two wait for the user (the non-plated holes that JLCDFM lists as plated, the 0.60 mm plated slots). The review holds only for the three SHA-256 it records |
| Quote | $52.85 without shipping on 2026-11-19 (PCB $8.00, Economic PCBA $44.85; 5 boards, 2 assembled), `JLCPCB_REVIEW.md` section 6. Rev0.5 r02's was $51.94 |
| Sourcing | the BOM is the file Rev0.5's check read (`../../rev0.5/r01/SOURCING_CHECK.md`, PASS on 2026-11-13, SHA-256 below). JLCPCB's assembly stock was read again on 2026-11-19 for the 41 codes (all above 500; `JLCPCB_REVIEW.md` section 3); the Akizuki stock was not. The stock moves, and the check is repeated before payment |
| EasyEDA import (D32) | `../../rev0.4/r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in; not run on Rev0.6 |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## What changed against Rev0.5 r02

Rev0.6 is a layout revision (CLAUDE.md §2: a new PCB revision for any layout change). Compared file by file with
`../../rev0.5/r02/` on 2026-11-19:

| File | Against Rev0.5 r02 |
|---|---|
| `_BOM_JLCPCB.csv`, `_HandSolder.csv` | byte-identical |
| `_CPL_JLCPCB.csv` | 28 of its 262 rows differ, the machine-placed parts D39 moved: C5 C6 C7 C8 C35 C36 C37 C216 D1 D3 D5 D12 D13 J1 J3 Q33 Q53 R1 R2 R10 R34 R203 R204 R209 R210 R240 R241 SW2. J1's Mid X 76.0 to 82.5 and J3's 51.3 to 82.5; their Mid Y still carries the receptacle's model shift (68.010 and 3.990). Three more parts moved and are in no CPL: U5 (hand-soldered), TP3 and TP14 (not populated) |
| `_Gerber.zip` | the same 15 members; 13 differ beyond their header lines. `Edge_Cuts` and `B_Paste` have the same body: the outline did not move, and there is no paste on the bottom. 413 vias, not 397 |
| `_Schematic.pdf`, `_ERC.json` | the schematic's title blocks say Rev0.6; the exported netlist differs from Rev0.5's in title-block lines alone (rev, comment 2, source, date, library uri) |
| `_Assembly_Top.pdf`, `_Preview_Top.png`, `_Preview_Bottom.png` | show the new placement and copper |
| `_DRC.json` | 0 violations, as r02's |

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
| `JLCPCB_REVIEW.md` | the JLCPCB gate of 2026-11-19 on the Gerber zip, the BOM and the CPL above: findings, options, part mapping, JLCDFM, placement preview, quote, and the decisions left to the user |
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
| `design/ecad/source/usb-power-hub.kicad_pcb` | `0ea3ec5bf9f6309e2f45f6bc3d2a7329b86e0dcf87b728ef13e65c1bcbbbdff3` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `d8aaca5061a6f72b1d719d4b35e3a59ddce04d5db1349dcb3b746956ee07a343` |

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| JLCDFM on this Gerber | run on 2026-11-19, **not accepted**: the user accepted the GND via beside D1 pad 3 on 2026-11-19 (「受け入れる」) and still decides on "Confirm Production file" for the non-plated holes and on the 0.60 mm plated slots (`JLCPCB_REVIEW.md` sections 1 and 8). Six "Pad spacing", 22 "pad to line spacing" and 3 mask-exposure Danger rows were judged by measurement and not identified one by one | user |
| Part mapping and placement preview on this BOM and CPL | run on 2026-11-19: 41 of 41, 0 substituted; J1-J4 and the 7 other moved parts that are not symmetrical read in the preview, one instance of each other class. A viewer reading, not JLCPCB's pick-and-place; "Confirm Parts Placement" is the user's choice | user |
| Quote | read on 2026-11-19: $52.85 without shipping. Not read: the assembled parcel's shipping, a quote with impedance control | user, in the cart |
| Sourcing | Rev0.5's check of 2026-11-13 read the same BOM file; JLCPCB's stock was read again on 2026-11-19, the Akizuki stock was not; to be repeated before payment | Claude, before payment |
| Independent check of the set | **not run** on Rev0.6's files (Rev0.5 r02 had one, CLAUDE.md 12) | Claude |
| Mechanical overlay | the enclosure and the lid PCB are drawn for this board on paper (Enclosure Rev0.2 and Lid Rev0.2, issue #13 step 7; `design/mechanical/`); nothing is printed and no cable was tried | user (print, cables) |
| EasyEDA import (D32) | blocked at the user's sign-in | user |
| The open issues of CLAUDE.md 11 | OI-1, OI-5, OI-6, OI-8 (panelization), OI-26 and OI-33 stand | user (built board, real cables) |
| User approval before any order or payment | not given | user |

## Residual risks

- **The JLCPCB review of 2026-11-19 is JLCDFM's and a viewer's reading, not JLCPCB's production check**
  (`JLCPCB_REVIEW.md`). JLCDFM's Danger items (via annular ring of the 0.30 mm vias, THT-to-SMD distance, mask
  opening exposing a trace, pad spacing, pad to line spacing, silkscreen over a plugged via, the receptacles'
  plated-slot width) are judged there against measurements on the board, not row by row. JLCDFM's list of items
  changed since Rev0.5's run, and no control run of Rev0.5's Gerber was made.
- A GND via carried from Rev0.5's routing stands 0.059 mm from pad 3 (GND) of D1, which D39 moved beside it: one
  net, so DRC is clean, but the mask between them may not hold. Two older pairs are alike (C27 pad 2 0.090 mm,
  TP13 0.095 mm). No checker of the repository measures a pad against a via of its own net. The user accepted
  the pair as it is on 2026-11-19 (「受け入れる」); the first boards show whether D1's joint wets onto the via.
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
- Nothing has been built or measured. The open issues of CLAUDE.md 11 stand; the set is not orderable until each
  is closed.
