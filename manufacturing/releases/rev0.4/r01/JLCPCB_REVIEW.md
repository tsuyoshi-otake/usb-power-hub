# JLCPCB review of the Rev0.4 candidate (issue #6, P6)

**Nothing was ordered and nothing was paid.** The quote draft was never saved to the cart, no terms
were accepted, and "Confirm Parts Placement" was left at No. The user signed in to JLCPCB and JLCDFM
themselves; Claude read the pages and uploaded the three files below to a draft.

| Item | Value |
|---|---|
| What was reviewed | `UsbPowerHub_Main_Rev0.4_Gerber.zip`, `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv` of this directory |
| Dates | JLCDFM 2026-11-11; quote, part mapping and placement preview 2026-11-11 23:22 to 2026-11-12 00:25 (JST) |
| Validity | holds only while the three SHA-256 below are unchanged; any regenerated file needs a new review |

| Uploaded file | SHA-256 |
|---|---|
| `UsbPowerHub_Main_Rev0.4_Gerber.zip` | `51caab59ad8be01cbbf6f584aa1429cb9c557917f9751d067aaa9bef2c719f9c` |
| `UsbPowerHub_Main_Rev0.4_BOM_JLCPCB.csv` | `4cc290755740e59dcad420f66f281f10b49ba5565b7b2e5aa3e8e22f28b8a595` |
| `UsbPowerHub_Main_Rev0.4_CPL_JLCPCB.csv` | `98d1065054ba546cd61d2a75304fb660a4df0afe00165ebb963a1b4ae7c8789c` |

Evidence (screenshots, page text, measuring scripts) is kept **outside the repository**, in
`~/tmp/usb-power-hub/pre-order/` (`jlcpcb/`, `local/`, `easyeda/`), because the screenshots can show
account details and JLCPCB's draft IDs. Every file named below is in `jlcpcb/` unless a path is given.

## 1. Defects the gate found (all fixed before the final upload)

| # | Defect | Fix | Where it lives now |
|---|---|---|---|
| 1 | BOM rows that share one LCSC code were not auto-selected by JLCPCB's part matching. | `make_outputs.py` writes one BOM row per LCSC code (40 rows). The one merged 510 Ω row (C17734) still had to be ticked by hand after *Process BOM & CPL*. | `make_outputs.py`, `check_outputs.py` (one-row-per-LCSC check) |
| 2 | JLCPCB places the CPL against the Gerber's own origin. The Gerber and drill files carried KiCad's page origin, so the CPL (origin: the board's lower-left corner) sat off the copper by that corner's offset, 50 mm in x and 122 mm in y. | Gerber and drill are written with the auxiliary origin at the board's lower-left corner, the CPL's origin. `check_outputs.py` checks that Edge.Cuts spans (0, 0)-(W, H). | `make_outputs.py`, `check_outputs.py` |
| 3 | The CPL angle is applied to JLCPCB's own model of the part, not to KiCad's footprint (easy-stick 14.18). With the KiCad angle alone the model's pin 1 sat 90 or 180 degrees from the board's pad 1 for 11 part classes. | A per-LCSC rotation table, read by both the generator and the checker; a dead entry fails the check. | `design/ecad/jlcpcb_model_rotation.json` |
| 3a | A first try added +180 degrees to the LEDs. The viewer's "+" (anode) mark then sat on pad 1; the KiCad angle alone put it on pad 2. | Removed; the LEDs have no table entry. | `jlcpcb_model_rotation.json` `_doc` |

## 2. Options JLCPCB's form took, against the manifest

Screenshots: `final-1794409552836-122.jpg`, `final-1794409552837-123.jpg`, `final-1794409552838-124.jpg`.

| Option | JLCPCB form | Manifest / decision | Verdict |
|---|---|---|---|
| Base material, layers, size, quantity | FR-4, 4 layers, 100 × 72 mm, 5 boards, single PCB | D10, D24 | match |
| Thickness | 1.6 mm | 1.6 mm | match |
| Stackup | "Specify Stackup: Yes", JLC04161H-7628 | D27 | match |
| Impedance control | No requirement | D27 (not ordered) | match |
| Surface finish | HASL (with lead) | D30 | match |
| Copper | outer 1 oz, inner 0.5 oz | outer 0.035 mm, inner 0.0152 mm | match |
| Via size class | 0.25 mm hole / 0.35-0.4 mm pad | board vias 0.25 / 0.45 mm | match (costs money, section 6) |
| Via covering | **Plugged** (the form greys out Tented), $0.00 | manifest said "tented" | **changed**: the manifest now records Plugged as what JLCPCB offers for this via class |
| Material type | form shows FR4 TG135; the via-class notice says "FR4 Tg155" is selected automatically | not in the manifest | **unresolved**: confirm what the cart finally shows |
| Colour, silkscreen | Green, White (form defaults) | no decision records them | defaults taken |
| Confirm Production file, 2D barcode, gold fingers, UL mark, etc. | No / removed | none requested | match |
| Assembly | Economic PCBA, Top only, 2 boards (BOM quantities are 2 × per-board) | D13, REQ-MFG-01 | match |
| Confirm Parts Placement | **No** ($0.00) | CLAUDE.md 4.2 asks for placement checking | **decision for the user** (section 8) |
| Build time | PCB 3 days, assembly 3-4 days | none | recorded |

The PCBA options also showed solder paste "High temp." next to leaded HASL. Not examined further;
confirm it in the cart.

## 3. Part mapping

Screenshots: `final-1794409597716-125.jpg`, `final-1794409597717-126.jpg`; page text `part-mapping.txt`.

- Bill of Materials tab, "Top Side": **40 parts detected, 40 parts confirmed**, source JLCPCB for every row.
- The 40 matched LCSC codes equal the 40 codes of the BOM file one for one: **0 unmatched, 0 substituted**.
- Library type: 38 Basic, 2 Extended (C2040 RP2040, C5137013 CH335F; D29, D31). No Preferred Extended.

## 4. DFM (JLCDFM, PCB DFM check, signed in by the user)

Statistics are (Danger, Warning, Good). Page text: `jlcdfm-pcb-dfm-summary.txt`; an example dialog:
`jlcdfm-screenshot-1794406053450-24.jpg`. JLCDFM lists only the first 50 results of each item.
**JLCDFM analysed the zip made before the origin fix (defect 2).** `gerber-translation-check.txt` compares
that zip with the final one line by line: all 51,444 coordinate lines differ by one constant translation
(within 1 µm of rounding), nothing else differs. Spacing, ring and width results therefore carry over;
this is a proof by comparison, not a rerun.

| Item | D / W / G | Judgement | Evidence |
|---|---|---|---|
| Annular ring | **100** / 0 / 0 | The 50 rows shown are 0.25 mm hole in a 0.45 mm pad: the vias, ring 0.100 mm, exactly JLCDFM's Danger boundary (0.1 mm) and the project rule `min_via_annular_width` 0.1. The dialog says via results may be ignored; the form accepts the 0.25 mm via class. Not proven for the 276 rows not shown. | `...-24.jpg`, `dfm-other-measurements.txt` |
| THT to SMD | **50** / 0 / 0 | Concerns hand or wave soldering access (2.03 mm). The through-hole parts are the Akizuki modules and headers the user solders (D13); JLCPCB machine-places SMD only. Not a machine-assembly defect; not measured. | `jlcdfm-pcb-dfm-summary.txt` |
| Pad spacing | **2** / 8 / 68 | Measured with the KiCad board: of 356 vias and 856 pads, 145 via-to-pad pairs are 0.11 mm or closer, **all on the same net, none on different nets**. The two Danger rows are not identified one by one. Different-net spacing is covered by the DRC (clearance 0.15 mm, 0 violations). | `dfm-via-pad-gap.txt` |
| Silkscreen to hole | **50** / 0 / 0 | Measured: 612 silkscreen items, 449 holes; every silkscreen/hole pair closer than 0.13 mm is a **via** (107 pairs); none near a pad hole. Vias are plugged. Risk: JLCPCB may clip legend over a via. | `dfm-silk-hole-gap.txt` |
| Silkscreen line width | 0 / **50** / 0 | Footprint outlines are 0.15 mm (574), board lines 0.17 mm (6), text 0.17 mm (30) and 0.20 mm (2). 0.15 mm equals JLCDFM's Warning boundary and JLCPCB's minimum; CLAUDE.md 6 asks for at least 0.15 mm. | `dfm-other-measurements.txt` |
| Trace spacing | 0 / **25** / 25 | Project minimum is 0.15 mm (rule and DRC clean); JLCDFM's warning band is not stated in the text copied. Not measured further. | `dfm-other-measurements.txt` |
| Fiducial | 0 / **3** / 0 | Three fiducials, each flashed at the board's position in the Gerber as a 1.0 mm copper circle with a 2.0 mm mask opening (`local/c2_check.py`), 2.5 mm from the left/right edge. The warning's reason was not read. **Open.** | `dfm-other-measurements.txt` |
| Solder mask opening exposing trace | **4** / 13 / 38 | **Not measured, not explained.** Residual risk. | none |
| Negative soldermask expansion | 0 / **18** / 0 | Not explained: no pad in the board has a negative local mask margin and the global expansion is 0.0 mm. Residual risk. | `dfm-other-measurements.txt` |
| Silkscreen to pad | 0 / **2** / 48 | Not read. Residual risk. | `jlcdfm-pcb-dfm-summary.txt` |
| All other items | 0 Danger, 0 Warning | sharp corner, BGA pad, via in pad, trace to edge, unconnected end, trace width, pad to edge, PTH to trace, via to pad, mask bridge, multi-segment mask opening, drill items | `jlcdfm-pcb-dfm-summary.txt` |

JLCPCB runs its own DFM again after an order (4-6 hours) and may differ from JLCDFM.

## 5. Placement preview (JLCPCB's 3D viewer, final CPL)

Each class was selected in the part list and read for the model's pin-1 / polarity mark against the
board's pin 1 (from `local/pin1.py`: the footprint centre to the pad numbered 1, in the Gerber frame).
The magenta/purple dot is the model's pin 1; the LED "+" is the anode.

| Class (LCSC, designators) | CPL rotation | Verdict | Screenshot / basis |
|---|---|---|---|
| RP2040 C2040, U1 | KiCad angle | model mark at the bottom-left = board pin 1 (-2.60, -3.44 mm from centre) | `class-1794410386230-137.jpg` |
| X322512MSB4SI C9002, Y1 (Y2 as Y1) | KiCad angle | Y1 mark at the bottom-right = board pin 1 (+0.85, -1.10 mm) | `class-1794410386230-137.jpg` |
| CH335F C5137013, U6 | +270 | mark at the top of the left column = board pin 1 | `class-1794410386231-138.jpg` |
| W25Q128JVSIQ C97521, U8 | +270 | mark at the top-left lead = board pin 1 | `class-1794410386231-139.jpg` |
| OP07CDR C7433, U10-U12, U20-U22 | +270 | marks agree with the board's pin 1 | `class-1794410386232-140.jpg` |
| LM393DR2G C7955, U13, U23, U30 | +270 | as C7433 | `class-1794410386233-141.jpg` |
| AMS1117-3.3 C6186, U2 | +180 | mark at the three-lead side's top lead = board pin 1 | `class-1794410386233-142.jpg` |
| PSM712 C32677, D1-D4 | +180 | the model's two-lead side lies on the board's two-pad side | `class-1794410409818-143.jpg`, `-144.jpg` |
| SMBJ6.5CA C7420377, D5, D6 | KiCad angle | bidirectional TVS, no polarity | `class-1794410439881-149.jpg` |
| AO3401A C15127, 2N7002 C8545, AO3400A C20917, S9012 C8543, CJ431 C3113 (SOT-23) | +180 | model pin 1 agrees with the board's after the table; part-list row of the highlighted class is behind the viewer's 3MF panel in these frames | `class-1794410409819-145.jpg`, `-146.jpg`, `class-1794410439880-147.jpg`, `class-1794410439881-150.jpg`, `class-1794410439882-151.jpg` |
| TS-1187A C318884, SW1-SW3 | KiCad angle | four-pin switch, no polarity; SW3 shown on its pads | `class-1794410439880-148.jpg` |
| KT-0805G C2297, NCD0805R1 C84256, D10-D13 | KiCad angle | "+" (anode) on pad 2 | `final-1794409656028-129.jpg` |
| Resistors, capacitors, FB1 C14709 | KiCad angle | symmetrical parts | `final-1794409656027-127.jpg`, `-128.jpg` |

The rotations come from `design/ecad/jlcpcb_model_rotation.json`; its `seen` fields record what the
viewer showed for each class before the table. The viewer is JLCPCB's model, not a guarantee of the
physical part: JLCPCB's own check after ordering is the last word (CLAUDE.md 4.2).

## 6. Price, lead time, and the difference from the estimate

Quote on 2026-11-12 00:23 (USD, the account's currency). Screenshots: `final-1794409682530-130.jpg`,
`final-1794409682531-131.jpg`, `quote-total-1794410640613-157.jpg`.

| Line | Quote | Estimate (`design/experiments/cost-estimate/`) | Difference |
|---|---:|---:|---:|
| PCB, "Special Offer" (4 layers, 5 boards) | 8.00 | 8.00 | 0.00 |
| 4-Wire Kelvin Test | 17.02 | - | **+17.02** |
| Min via hole size/diameter | 17.14 | - | **+17.14** |
| Via covering | 0.00 | - | 0.00 |
| PCBA setup | 8.24 | 8.18 | +0.06 |
| Stencil | 1.55 | 1.53 | +0.02 |
| Components, 40 items | 20.47 | 27.32 | -6.85 |
| Extended components fee | 6.18 | 6.14 | +0.04 |
| SMT assembly | 2.39 | 2.15 | +0.24 |
| Nitrogen reflow soldering | 0.86 | - | +0.86 |
| Confirm Parts Placement | not selected | 0.45 | -0.45 |
| **Total without shipping** | **81.85** | **53.77** | **+28.08** |

- **Cause of the jump:** the 0.25 mm via class adds the 4-Wire Kelvin Test and a minimum-via-size fee
  automatically ($34.16 together). The estimate did not know. Without them the quote is $47.69,
  $6.08 below the estimate, mostly from the component prices at the quote.
- **Shipping to Japan**, read on the PCB form on 2026-11-12 (`shipping-1794411393890-164.jpg`,
  `shipping-panel-1794411384681-162.jpg`): OCS Express $7.23 (4-6 business days), UPS Worldwide Express
  Saver $9.69 (3-5), DHL Express $17.67 (1-3; the form's default, left unchanged), FedEx Express $20.81
  (2-4), S.F. Express Economy $16.35 (5-9), OCS NEP $4.51 (4-6; at most 0.6 kg and 10 x 10 cm). These are
  prices for the form's 0.24 kg PCB-only parcel. The quote page weighs the assembled order at 556.50 g and
  the cart prices that parcel, so the real shipping may be higher. Nothing was selected.
- Total with the estimate's carrier (OCS Express): $89.08, 14,253 yen at the planning rate of 160 yen/USD;
  with the default DHL Express: $99.52. With the Akizuki parts (7,695 yen) the estimate's total of 17,456 yen
  becomes about 21,950 yen (OCS Express).
- Lead time shown: PCB 3 days, assembly 3-4 days, plus the carrier's 4-6 business days (OCS Express). The
  PCB form, reopened with "Change PCB", showed the build time "3-4 days" selected ("3 days" is offered for
  PCBA only); both cost $0.00.

## 7. What was not done, and what is left in the user's accounts

- No order, no payment, **SAVE TO CART not clicked**, no terms or consent accepted.
- Two quote drafts, `UsbPowerHub_Main_Rev0.4_G...` (2026-11-11 23:22:53 and 23:54:22), are in
  jlcpcb.com > My Account > Projects > **Quotes** (`screenshot-1794409763222-133.jpg`). JLCPCB saved them
  on upload; they hold the three files above. Remove each with its "..." menu > Delete.
- The cart's one item is the user's earlier easy-stick quote; it was not touched.
- The EasyEDA import was not done: see `EASYEDA_IMPORT.md`.

## 8. Decisions for the user

1. **The 0.25 mm via class costs $34.16 more.** Accept it, or move the vias to the 0.30 mm class
   (hole 0.30 mm, pad 0.45 mm or more). The second is a layout change and a new revision, not a setting.
2. **Confirm Parts Placement:** the estimate budgeted $0.45; the quote has it off. CLAUDE.md 4.2 wants
   placement checked; JLCPCB's post-order DFM does it anyway.
3. **Shipping method:** the form's default is DHL Express, $17.67; the estimate assumed OCS Express, $7.23,
   which takes 4-6 days. The cart prices the real parcel; choose there.
4. **Material and solder paste:** confirm "FR4 TG135 or Tg155" and "High temp." paste with leaded HASL in
   the cart before paying.
