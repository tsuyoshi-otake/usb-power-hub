# JLCPCB review of release candidate r01 (issue #13)

**Nothing was ordered and nothing was paid.** The pages were read in the user's own Chrome, where the user was
signed in; Claude entered no credentials on either site. Claude uploaded the three files below to the quote form
and the Gerber to JLCDFM, after the user's 「アップロードする」 of 2026-11-19. SAVE TO CART was not clicked, no
terms or consent were accepted (the form's "I agree to the Terms and Conditions" box was not ticked), no coupon
was claimed, nothing was downloaded, and "Confirm Parts Placement" was left at No.

This is Rev0.6's first pass through the gate. It found **no defect that changes a file of this directory**, and
three findings that are the user's to decide (section 1). The state stays `WIP`. After the gate, on 2026-11-19,
the user accepted the first of them as it is (finding 1, 「受け入れる」); the other two wait.

| Item | Value |
|---|---|
| What was reviewed | `UsbPowerHub_Main_Rev0.6_Gerber.zip`, `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv` of this directory |
| Dates | 2026-11-19, about 14:50 to 15:25 (JST) |
| Validity | holds only while the three SHA-256 below are unchanged; any regenerated file needs a new review |

| Uploaded file | SHA-256 | Where, when (JST) |
|---|---|---|
| `UsbPowerHub_Main_Rev0.6_Gerber.zip` | `b855cf2ac981fe152d9dff3bf4af296d89d7bca320b6e1ba31eec70838f1ff5d` | quote form about 14:50; JLCDFM 15:05:41 (the page only reloaded) and again about 15:06 (uploaded) |
| `UsbPowerHub_Main_Rev0.6_BOM_JLCPCB.csv` (the file Rev0.5 r02 also has) | `c2a5455389db1466c1e59f17ba812988152e44c914a6735a808e96efce9d7b06` | quote form about 14:52 |
| `UsbPowerHub_Main_Rev0.6_CPL_JLCPCB.csv` | `a2f278e692157fd10aef00a79a9378a5643413b0a36f0c0f5293c9bc2fc7e7ac` | quote form about 14:52 |

Evidence is kept **outside the repository**, in `~/tmp/usb-power-hub/rev06-gate/evidence/`: `quote.txt`,
`part-mapping.txt` (with `bom_codes.txt` and `matched_codes.txt`), `placement.txt`, `jlcdfm-statistics.txt`,
`stock-2026-11-19.txt` and `scripts/` (the measuring scripts and their output). `gate_measure.py` and
`gate_measure2.py` are Rev0.5's, unchanged; `gate_measure3.py`, `gate_measure4.py` and `gate_measure5.py` are new.
Screenshots were **not saved to disk**: what they showed is recorded below and in those text files. Account data
(the quote's file number, JLCDFM's upload ID, draft IDs) is not recorded anywhere.

## 1. What the gate found

No file of r01 changed. Three findings needed the user's decision (section 8): finding 1 is decided, findings 2
and 3 wait. Three more are records.

| # | Finding | Found by | Judgement |
|---|---|---|---|
| 1 | **A GND via stands 0.059 mm from pad 3 (GND) of D1.** The via (0.45 mm land, 0.30 mm hole) is at KiCad (127.7713, 59.8161), Gerber frame (77.77, 62.18); D1, J1's PSM712, moved from x = 122.4 to 128.9 mm with J1 (D39). The via is not new: it is in `design/ecad/routing/carried.json`, the routing carried from Rev0.5, and on the Rev0.5 board, where D1's pad 3 stood 6.3 mm from it. | JLCDFM "Pad spacing", row 2 (0.06 mm, a 0.45 mm round land against a 1.475 × 0.60 mm pad beside J1's left rear slot); `gate_measure5.out`, `gate_measure5_rev05.out` | One net, so no short and no DRC violation (KiCad's clearance is between nets; no checker of this repository measures a pad against a via of its own net). The risk is the 0.059 mm strip of solder mask between the pad's opening and the via: it may not hold, and D1's joint can then wet onto the via's land. The board already has two such pairs from Rev0.5 (C27 pad 2, 0.090 mm; TP13, 0.095 mm), which Rev0.5's review accepted. **Decided by the user on 2026-11-19: accepted as it is** (「受け入れる」, the answer to 「D1 脇の GND ビア（同一ネット、間隔 0.059 mm）はこのまま受け入れますか？」; Claude had recommended accepting). The via stays, and the first boards show whether D1's joint wets onto it. The alternative was to move the via in a new release. |
| 2 | **JLCDFM lists the non-plated drill file as a plated layer.** Both `..._NPTH.drl` and `..._PTH.drl` appear as "Plated drill layers", and the new item "Pth without pad" lists the 15 non-plated holes twice (30 Warning: 8 receptacle pegs of 0.65 mm, 3 holes of J5 of 0.991 mm, H1-H4 of 2.2 mm). | JLCDFM's layer list and "Pth without pad" | Not a defect of the file: its header says `TF.FileFunction,NonPlated,1,4,NPTH` and its three tools carry `TA.AperFunction,NonPlated,NPTH,ComponentDrill`. Whether JLCPCB's CAM reads it as JLCDFM's viewer does is seen only in the production file. **Decision for the user**: order with "Confirm Production file", or accept. |
| 3 | **The receptacles' plated slots are 0.60 mm wide**, under JLCDFM's Danger limit of 0.61 mm ("Slot width check", 16 Danger). | JLCDFM | As on Rev0.5 and still open: JLCPCB's capabilities page gave 0.35 mm as the minimum plated slot width (read 2026-11-13, not read again). **Decision for the user.** |
| 4 | JLCDFM's item list changed between 2026-11-13 and 2026-11-19: 35 rows now, 29 in Rev0.5's record (its three "Unconnected via" rows counted as three). The six new rows: "Measure pad to line spacing" (a row without a name), "Pth without pad", "Via without pad", a second "Trace spacing" row and two rows without a name over the bottom copper. | reading the page | Counts of Rev0.5's run and of this one cannot be compared item by item. Where an item is new or its count moved, the two boards were measured instead (section 4, *The two boards, measured*). A control run of Rev0.5 r02's Gerber on today's JLCDFM was not made: the user's OK covered Rev0.6 r01's files. |
| 5 | JLCPCB did not select the merged 510 Ω row (C17734, quantity 16) by itself; it was ticked by hand after *Process BOM & CPL*. The counter then read "41 parts detected, 42 Parts confirmed". | the Bill of Materials tab | Repeated from Rev0.4 and Rev0.5. The "42" is not explained; read the cart. |
| 6 | The total is $0.91 above Rev0.5 r02's with a byte-identical BOM. | the Quote & Order tab | Which line moved is not known: Rev0.5's PCBA lines were not read one by one (section 6). |

## 2. Options JLCPCB's form took, against the manifest

Read on 2026-11-19 in the form with this Gerber (`quote.txt`).

| Option | JLCPCB form | Manifest / decision | Verdict |
|---|---|---|---|
| Base material, layers, size, quantity | FR-4, "Detected 4 layer board of 72x100mm", 5 boards, single PCB | D10, D24 | match |
| Thickness | 1.6 mm | 1.6 mm | match |
| Stackup | "Specify Stackup": **No**, the form's default; not set to JLC04161H-7628 | D27, named on the order | **name it on the order** (section 8) |
| Impedance control | No requirement | D27 (not ordered for the prototype) | match; decision for the user (section 8) |
| Surface finish | HASL(with lead) | D30 | match |
| Copper | outer 1 oz, inner 0.5 oz | outer 0.035 mm, inner 0.0152 mm | match |
| Via size class | 0.3mm/(0.4/0.45mm); no 4-Wire Kelvin Test line, no minimum-via line | every via 0.30 mm hole | match |
| Via covering | Plugged, $0.00 | the board tents its vias; the form offers Plugged | as on Rev0.5 |
| Material type | FR4 TG135 | not in the manifest | confirm in the cart |
| Colour, silkscreen | Green, White: form defaults, not changed | no decision records them | defaults taken |
| Outline tolerance, mark, test | ±0.2 mm (Regular), Remove Mark, Flying Probe Fully Test | none | defaults taken |
| Assembly | Economic PCBA, Top Side, 2 boards (the form's default is 5), tooling holes added by JLCPCB | D13, REQ-MFG-01 | match |
| Confirm Parts Placement | **No** | CLAUDE.md 4.2 asks for placement checking | **decision for the user** (section 8) |
| Build time | PCB 3 days, assembly 3-4 days | none | recorded |

The PCBA options showed solder paste "High temp." next to leaded HASL, as on Rev0.4 and Rev0.5. Not examined
further; confirm it in the cart.

## 3. Part mapping and stock

- Bill of Materials tab, "Top Side": **41 parts detected**; 40 rows selected by the form, the 41st by hand
  (finding 5).
- The 41 matched LCSC codes equal the 41 codes of the BOM file one for one: **0 unmatched, 0 substituted**
  (`matched_codes.txt` against `bom_codes.txt`).
- Library type: 38 Basic, 3 Extended (C2040 RP2040, C5137013 CH335F, C2765186 receptacle; D29, D31, D37). No
  Preferred Extended.
- The receptacle's row shows quantity 11 for the 8 the two boards need, as on Rev0.5. Read the cart.
- Stock on the day of the upload, `tools/jlc_stock.py` on the 41 codes at 15:24 (`stock-2026-11-19.txt`, exit 0:
  every code matched exactly): 38 Basic and 3 Extended; the lowest are C5137013 (CH335F) 4,378, C97521
  (W25Q128JVSIQ) 72,478 and C2040 (RP2040) 75,345, every one above the 500 of CLAUDE.md 4.1. The Akizuki stock of
  the hand-soldered parts was **not** read again (`../../rev0.5/r01/SOURCING_CHECK.md`, 2026-11-13). Repeat both
  before payment.

## 4. DFM (JLCDFM, PCB DFM check)

Statistics are (Danger, Warning, Good); the page text is in `evidence/jlcdfm-statistics.txt`. JLCDFM lists only
the first 50 results of an item, so a count of 50 or 100 is a cap and the rows read are samples. Measurements are
on the KiCad board (`scripts/gate_measure*.py`); JLCDFM's viewer is in the Gerber's frame (x = x_KiCad - 50 mm,
y = 122 mm - y_KiCad). JLCDFM's thresholds are its own and differ from JLCPCB's published capabilities (the slot
row). In brackets: Rev0.5 r02's count of 2026-11-13, where the item existed then and differs.

| Item | D / W / G | Judgement | Evidence |
|---|---|---|---|
| **Slot width check** | **16** / 0 / 0 | The plated shell slots of J1-J4 (4 each: 0.60 × 1.40 mm at the front, 0.60 × 1.70 mm at the rear; the maker's land, D37). Finding 3: **decision for the user**. | `jlcdfm-statistics.txt`; `gate_measure3.out` M10 |
| **"Measure pad to line spacing"** (row without a name; new item) | **22** / 34 / 44 | JLCDFM names the pads of these rows "rect" (0.60 × 1.95, 0.60 × 1.475, 1.625 × 0.65 and 0.56 × 0.62 mm), and the Gerber draws them with RoundRect aperture macros of 0.15 mm corner radius. Read as plain rectangles, the board gives 13 pad-to-track pairs of different nets at 0.091-0.094 mm, the same number as JLCDFM's rows at "0.09mm", and 6 more under 0.100 mm (JLCDFM lists 9 Danger rows at "0.1mm"; 3 not reconciled). **On the real shapes the closest pad-to-track pair of different nets is 0.152 mm on F.Cu** (U1 pin 14, EVT_M_B, against EVT_L_B) and 0.170 mm on B.Cu (DRC clearance 0.15 mm, 0 violations). The 22 rows were not identified one by one. | `gate_measure3.out` M8 |
| **Pad spacing** | **7** / 15 / 39 [6 / 11 / 44] | The Danger rows are a 0.45 mm via land against a pad: 0.05, 0.07 and 0.08 mm at 0402 pads, 0.06 mm at a SOT-23 pad, three of 0.09 mm at SOIC-8 pads. Row 2 (0.06 mm) is **finding 1** (D1 pad 3), identified in the viewer; the other six were not identified one by one. On the real shapes, 3 pad-to-via pairs are under 0.10 mm (D1 pad 3 0.059, C27 pad 2 0.090, TP13 0.095) and 152 are 0.10-0.15 mm, **all on one net**; no pair on different nets is under 0.15 mm. With the pads read as rectangles the board gives 16 pairs under 0.10 mm, 3 of them on different nets (U2 pin 2, U30 pin 4, U20 pin 8), against JLCDFM's 7: that reading explains the rows' kind and is not an exact model of JLCDFM. | `gate_measure.out` M2, `gate_measure2.out` M2b, `gate_measure5.out` |
| Annular ring | **100** / 0 / 0 | The 381 vias of 0.45 mm pad and 0.30 mm hole: ring 0.075 mm, under JLCDFM's Danger limit (0.1 mm); it is the via of JLCPCB's standard class "0.3mm/(0.4/0.45mm)". The dialog says via results of this check may be ignored. The 32 vias of 0.60 mm pad have a 0.150 mm ring, and all 58 plated pad holes (the 16 slots included) have at least 0.200 mm. | `gate_measure.out` M1 |
| tht to smd | **50** / 0 / 0 | Hand-soldering access (JLCDFM's limit is 2.03 mm). The through-hole footprints are the hand-soldered F1, RS11, RS21, U5, U7 and U17 (D13). 55 pad pairs are closer than 2.03 mm; the closest is 0.62 mm (U7 pins 15 and 16 against C31 and C30). Not a machine-assembly defect. | `gate_measure.out` M4 |
| Silkscreen to hole | **50** / 0 / 0 | 609 silkscreen items against 486 holes: every pair closer than 0.18 mm involves a **via** (131 pairs, 119 of them under 0.13 mm; none at a pad hole or a slot). JLCDFM counts 314, which was not reconciled. The vias are plugged, so JLCPCB may clip the legend over one. | `gate_measure.out` M5 |
| Solder mask opening exposing trace | **3** / 10 / 40 [3 / 12 / 40] | No track or via of another net lies within 0.15 mm of a mask opening (the closest is 0.152 mm: U17 pin 6, GND, against an ADC_DIN track). The 58 pairs under 0.08 mm and the 186 of 0.08-0.15 mm are a pad and a track or via of its **own** net. JLCDFM's three Danger rows (0.04, 0.05, 0.06 mm) were not identified one by one. | `gate_measure.out` M3, `gate_measure2.out` M3b |
| Via placed within a pad | 0 / **2** / 0 [0 / 0 / 0] | The two rows are the centre thermal via of U1's exposed pad and of U6's (identified in the viewer). On the board 13 via holes touch a pad: 5 in U1's exposed pad and 6 in U6's (`ROUTING_Rev0.6.md` draws five in each; the sixth is a GND via at the edge of U6's pad), and one 0.60 mm via in pad 3 of Q18 (VBUS_A) and of Q38 (VBUS_B). **The Rev0.5 board has the same 13**, where JLCDFM listed none: the count moved with JLCDFM. Solder can wick into a via under U1, U6, Q18 or Q38: V-MFG-03 on the first boards. | `gate_measure3.out` and `gate_measure3_rev05.out` M9 |
| Pth without pad (new item) | 0 / **30** / 0 | Finding 2: the 15 non-plated holes, listed twice. | `gate_measure3.out` M10 |
| Negative soldermask expansion | 0 / **84** / 0 | The project's global mask expansion is 0, so each opening equals its pad: intended. The rows read are 1.0 and 1.6 mm round through-hole pads. How JLCPCB's CAM treats it was not seen. | `jlcdfm-statistics.txt` |
| Plated through-hole to trace clearance | 0 / **41** / 59 [0 / 40 / 60] | Warning by construction: hole radius, ring 0.075 mm and the 0.15 mm clearance make 0.225 mm. Measured: the closest plated hole to a track of another net is 0.227 mm (F.Cu and B.Cu), against JLCDFM's Danger limit of 0.18 mm; 47 Warning, 0 Danger. | `gate_measure2.out` M7 |
| Trace spacing | 0 / **32** / 29 [0 / 21 / 39] | The project minimum is 0.15 mm, equal to JLCDFM's Warning boundary; the Warning rows read are 0.15 mm between 0.31 mm tracks, the USB pairs' own gap. Measured between nets: 0.150 mm on F.Cu (USB_A_N against USB_A_P), 0.152 mm on In2 and B.Cu; none under 0.15 mm. | `gate_measure.out` M6 |
| Fiducial | 0 / **3** / 0 | Three fiducials of 1.0 mm copper, listed as Warning for detection, not for geometry. | `check_outputs.py` |
| Silkscreen line width | 0 / **50** / 0 | 0.15 mm equals JLCDFM's Warning boundary and JLCPCB's minimum; CLAUDE.md 6 asks for at least 0.15 mm. | `jlcdfm-statistics.txt` |
| Silkscreen to pad | 0 / **2** / 48 | Measured this time: the only two pairs under 0.18 mm are J5's own silkscreen lines against J5 pad 1 (0.787 mm round), 0.166 mm each; JLCDFM's two rows are 0.17 mm at a 31 mil round pad. J5 is the unpopulated SWD pad pattern. | `gate_measure4.out` |
| Two rows without a name (bottom copper, objects "... surface") | 0 / 0 / 50 each | Good only. Their names were not read. | `jlcdfm-statistics.txt` |
| All other items | 0 Danger, 0 Warning | sharp trace corner, BGA pad, trace to board edge, the second trace-spacing row, unconnected trace end, trace width, pad to board edge, via to pad, mask bridge, multi-segment mask opening, the three unconnected-via rows, missing plated hole, **plated through-hole spacing** (Rev0.5's defect 2), short slot detection, via to PTH spacing, via without pad | `jlcdfm-statistics.txt` |

JLCDFM's SMT DFM tab was not read. JLCPCB runs its own DFM again after an order and may differ from JLCDFM.

### The two boards, measured

The same scripts on the Rev0.6 board (SHA-256 `0ea3ec5b...`, the manifest's) and on the Rev0.5 board of commit
`1ba282f` (SHA-256 `3205d4c4...`, Rev0.5 r02's):

| Measure | Rev0.6 | Rev0.5 |
|---|---|---|
| Vias | 413 | 397 |
| Pad to via, real shapes, under 0.10 mm / 0.10-0.15 mm (all on one net) | 3 / 152 | 2 / 149 |
| Pad to track, different nets, pads read as rectangles, at 0.091-0.094 mm | 13 pairs | 13 pairs |
| Pad to track, different nets, real shapes, closest on F.Cu / B.Cu | 0.152 / 0.170 mm | 0.152 / 0.158 mm |
| Via holes touching a pad | 13 | the same 13 |
| Non-plated holes | 15 | 15 |
| Mask opening to own-net copper, under 0.08 mm / 0.08-0.15 mm | 58 / 186 | 57 / 185 |

So the items that are new or moved in JLCDFM's list come from the list, with one exception that is the board's:
the pad-to-via pair of finding 1.

## 5. Placement preview (JLCPCB's viewer, 2D, Top, with this CPL)

Each part was selected in the fitted view, fitted, and read for the model's pin-1 dot or polarity mark against the
board's pin 1 (`placement.txt`). No part was dragged; the viewer's undo button stayed greyed to the end.

Of the CPL's 262 rows, 28 differ from Rev0.5 r02's. 19 of the 28 are symmetrical parts (C5 C6 C7 C8 C35 C36 C37
C216, D5, R1 R2 R10 R34 R203 R204 R209 R210 R240 R241) and 9 are not (D1 D3 D12 D13 J1 J3 Q33 Q53 SW2): **all 9
were read.**

| Class (LCSC), instance read | CPL rotation | Verdict |
|---|---|---|
| **Receptacle C2765186, J1 J2 J3 J4** (J1 and J3 moved) | shift [0.0, -1.375] | front face 1.05-1.06 mm past the board edge (design 1.06), tails 6.33-6.34 mm from the edge (pad row 6.285), pegs 2.83 mm either side (design 2.89); reading error about 0.04 mm; J2 and J3 are 65.0 mm apart by the cursor readout |
| RP2040 C2040, U1; crystal C9002, Y1 | 90 | dot on the board's pin-1 mark |
| W25Q128JVSIQ C97521, U8 | 270 | agrees |
| AMS1117-3.3 C6186, U2 | 180 | agrees |
| CH335F C5137013, U6 | 270 | agrees |
| OP07CDR C7433, U10; LM393DR2G C7955, U13 | 0 | agrees |
| AO3401A C15127, **Q53** (moved); AO3400A C20917, **Q33** (moved) | 90, 180 | agrees |
| 2N7002 C8545, Q12; S9012 C8543, Q16; CJ431 C3113, U3 | 0, 90, 180 | agrees |
| PSM712 C32677, **D1 and D3** (moved) | 0 | agrees |
| LEDs C2297 **D12** and C84256 **D13** (moved) | 180 | "+" (anode) on pad 2; the silkscreen frame is closed at pad 1, the cathode |
| TS-1187A C318884, **SW2** (moved) | 90 | body centred on its four pads |

Not read again: the other instances of each class (Y2, U4, U11, U12, U20-U23, U30, D2, D4, D10, D11, Q13, SW1,
SW3 and the rest of the transistors) and the symmetrical parts (resistors, capacitors, FB1, D5, D6). This is the
drawing of JLCPCB's model, not its pick-and-place; JLCPCB's own check after ordering is the last word (CLAUDE.md
4.2).

## 6. Price and lead time

Read on 2026-11-19 at about 15:04 (USD, the account's currency; `quote.txt`).

| Line | Value |
|---|---:|
| PCB, "Special Offer" (4 layers, 5 boards); no Kelvin test, no minimum-via line | 8.00 |
| Setup fee | 8.24 |
| Stencil | 1.55 |
| Components (41 items) | 22.21 |
| Extended components fee | 9.27 |
| SMT assembly | 2.72 |
| Nitrogen reflow soldering | 0.86 |
| Economic PCBA price (the six lines above; Panel and Large Size $0.00) | 44.85 |
| **Total without shipping** | **52.85** |
| Rev0.5 r02's total of 2026-11-13, for comparison (`../../rev0.5/r02/JLCPCB_REVIEW.md`) | 51.94 |

- $0.91 above Rev0.5 r02 with the same BOM file (finding 6).
- Shipping: DHL Express $17.67, the form's default, for the 0.24 kg PCB-only parcel. The Quote & Order tab gives
  585.90 g. OCS Express was not read today ($7.23 on 2026-11-12). The assembled parcel is priced only in the cart.
- With OCS Express at that older figure: $60.08, 9,613 yen at the planning rate of 160 yen/USD. With the Akizuki
  parts (4,790 yen, the estimate's figure): **14,403 yen for 2 units**, against Rev0.5 r02's 14,257 yen.
- Impedance control was not priced today (+$34.13 on 2026-11-13).
- Lead time shown: PCB 3 days, assembly 3-4 days, plus the carrier's.

## 7. What was not done, and what is left in the user's accounts

- No order, no payment, **SAVE TO CART not clicked**, no terms or consent accepted, no coupon claimed, nothing
  downloaded. "My Account" and the cart were not opened.
- JLCPCB auto-saved a quote draft named `UsbPowerHub_Main_Rev0.6_Gerber` (last saved 15:04) under My Account >
  Projects > **Quotes**. Remove it with its "..." menu > Delete. The list was not opened, so what else is in it
  (Rev0.5's drafts of 2026-11-13) is not known.
- JLCDFM keeps the upload of about 15:06 in its history; whether the attempt of 15:05:41, which only reloaded the
  page, left a second record is not known.
- Not run: a control of Rev0.5 r02's Gerber on today's JLCDFM (finding 4), JLCDFM's SMT DFM tab, a quote with
  impedance control, the OCS price, the independent check of the set that Rev0.5 r02 had (CLAUDE.md 12), the
  Akizuki stock.
- The EasyEDA import (D32) was not done: `../../rev0.4/r01/EASYEDA_IMPORT.md`.

## 8. Decisions for the user

1. **D1's GND via** (finding 1): **decided on 2026-11-19, accepted** (「受け入れる」): the 0.059 mm of mask between
   D1 pad 3 and a via of its own net stays. The alternative was to move the via, which changes the copper and
   needs a new release and this gate again.
2. **Non-plated holes** (finding 2): order with "Confirm Production file" to see how JLCPCB's CAM reads the 15
   holes, or accept JLCDFM's reading as its viewer's.
3. **Slot width** (finding 3): accept and let JLCPCB's own DFM decide, or widen the slots, which means leaving the
   maker's land (a new revision).
4. **Stackup and impedance control:** name JLC04161H-7628 on the order ("Specify Stackup: Yes"); impedance control
   was +$34.13 on 2026-11-13 and is not priced for this set.
5. **Confirm Parts Placement:** off. The receptacle's shift is a viewer measurement (about 0.04 mm).
6. **Shipping method**, and in the cart: FR4 TG135, "High temp." paste with leaded HASL, the receptacle quantity
   (11 shown for 8 needed), the "42 Parts confirmed".
7. **A control run** of Rev0.5 r02's Gerber on today's JLCDFM, if the comparison by measurement is not enough: it
   needs the user's OK to upload that file.
8. **Approval of r01** is not given. The open issues of CLAUDE.md 11 stand.
