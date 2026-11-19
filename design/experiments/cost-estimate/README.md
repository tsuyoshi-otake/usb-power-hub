# Prototype cost estimate (Rev0.4, 2026-11-03; re-run 2026-11-04 for D29, D30, D31 and D33; Rev0.5 delta 2026-11-12, quote 2026-11-13) — non-authoritative

**Question.** What does a first prototype cost? The order is JLCPCB fabricating **5 bare
PCBs** and assembling **2** of them, plus the Akizuki parts the user solders by hand onto
those 2.

Since D29 (2026-11-04) the MCU is a bare RP2040 (C2040), machine-placed with its flash,
crystal and passives, instead of the hand-soldered PGA2040 module (¥1,680 each). The figures
below are the re-run's, with a price snapshot fetched on 2026-11-04. Since D30 (the same day)
the finish is leaded HASL instead of ENIG, and the plan ships by OCS Express, the cheapest
quoted, instead of UPS (the user: 「UPSじゃなくていい」). Since D31 (the same day) the hub is a
bare CH335F (C5137013), machine-placed, instead of the hand-soldered Akizuki module. Since D33
(the same day) the USB-C modules are soldered on PH-1x40SG pin headers without sockets, and
the header count includes each module's four mechanical pins: 44 pins per board.

**Not re-run for D34 or D35** (issues #6 P2 and #7, the same day). The capture bound every passive, so the
per-board counts in `cost_estimate.py` no longer match the schematic, and the 1 nF C1523 is
gone (41 → 40 machine-placed types; Standard PCBA's feeder loading falls by one type,
1.53). D35 adds one AO3401A, one 33 kΩ, one 100 nF and two 1 µF per board, no new type.
The figures below are the D33 re-run's.

**Rev0.5 (D37, D38; issues #8 and #10, 2026-11-12)** replaces the four Akizuki USB-C modules
with machine-placed receptacles and adds four 1 kΩ data-line taps per board. The model above
still prices Rev0.4 and is not the base: `cost_estimate.py` prints the delta against release
candidate r02's real quote instead (section "Rev0.5 against r02", below).

**Answer** (at 160 yen/USD; Japanese import tax, M2 inserts and the enclosure print are not
included):

| Case | JLCPCB order | Akizuki parts | Total, 2 units | Per unit |
|---|---:|---:|---:|---:|
| **Economic PCBA** (recommended) | $61.01 = 9,761 yen | 7,695 yen | **17,456 yen** | 8,728 yen |
| Standard PCBA | $158.58 = 25,373 yen | 7,695 yen | 33,068 yen | 16,534 yen |

With the PGA2040 (before D29), ENIG and UPS, the Economic case was 21,883 – 22,843 yen for
2 units. D29 saved 1,209 – 1,689 yen of that (20,674 – 21,154 yen, still with ENIG and UPS).
That saving is per unit: the module cost 1,680 yen each, and the RP2040, its flash, crystal
and passives cost about $3.8 per board, plus one $3.07 Extended feeder fee per order. D30's
leaded HASL saves $17.40 and OCS Express $2.56 per order: $19.96, 3,194 yen. With D29 and
D30 but the CH335F module, the Economic case was 17,480 – 17,960 yen. D31 adds $5.32
(851 yen) to the JLCPCB order: the two chips ($2.23), a second Extended feeder fee ($3.07)
and 23 more joints per board ($0.07), less $0.06 on the 0402 lines. It removes
875 – 995 yen from the Akizuki order: the two modules (840 yen) and one header strip per two
units (35 yen), plus one socket strip (120 yen) in the socketed case. The net is 24 – 144 yen
less. As first recorded, D31's figures counted 7 header pins per USB-C module instead of 11
and gave 910 – 1,150 and 59 – 299 yen, and an Economic case of 17,421 – 17,661 yen; D33
corrected the count and dropped the socketed case. Akizuki charges 550 yen shipping,
because the subtotal is below 11,000 yen.

The lid panel PCB adds $4.00 (640 yen) if it is ordered in the same JLCPCB order.

Economic PCBA is the recommendation. It charges no feeder fee for Basic parts and $3.07 per
Extended part type; since D31 the board has two, the RP2040 and the CH335F. It saves $97.57
(about 15,600 yen) against Standard. Standard is the fallback if the order form refuses this
board for Economic (see "What this cannot see").

This directory is an estimate, not a quote (CLAUDE.md §2: `design/experiments/` is
non-authoritative). The real price is the one shown after the Gerber, BOM and CPL are
uploaded, and CLAUDE.md §9 requires a recheck at every release. Nothing here is orderable:
the board is WIP and has no layout.

## Files

| File | What it is |
|---|---|
| `cost_estimate.py` | The estimate: `python -I -B design/experiments/cost-estimate/cost_estimate.py`. `--fetch` refreshes the price snapshot through `tools/jlc_stock.py`. Exits 1 if the BOM disagrees with the OI-23 placement study, or a part is not Basic and not an approved exception (`APPROVED_EXTENDED`: C2040, D29; C5137013, D31; C2765186, D37). |
| `test_cost_estimate.py` | 18 tests. Six corrupt the BOM, the study, the code list, a part's class or the list of approved exceptions and expect the check to fail (CLAUDE.md §8). One checks that the header strips follow the study's pin count (44 per board, D33) and that a changed count reaches it. Three check the Rev0.5 delta against a hand calculation, against the Akizuki saving (modules and headers) and against a dearer receptacle price tier. |
| `jlc_prices.json` | JLCPCB assembly-parts API snapshot, 2026-11-04 (C2765186: 2026-11-12): class, stock, price tiers, attrition (`lossNumber`) and minimum quantity (`leastPatchNumber`) for 41 codes, the 40 machine-placed types of Rev0.4 (D34) and Rev0.5's receptacle. |

## JLCPCB, Economic PCBA (2 assembled of 5)

| Item | USD | Source |
|---|---:|---|
| PCB: 4 layers, 100 × 72 mm, 1.6 mm, 5 pcs, base price | 8.00 | quote page, shown as "Special Offer" |
| Finish: leaded HASL (D30) | 0.00 | quote page; LeadFree HASL is +5.20, ENIG +17.40 |
| PCBA setup | 8.18 | price page |
| Stencil | 1.53 | price page |
| SMT joints: 673 per board × 2 × $0.0016 | 2.15 | price page; joints from the study's package counts (each QFN counted with its ePad: the QFN-56 as 57, the QFN-28 as 29) |
| Extended-part feeder fee: 2 types (C2040, D29; C5137013, D31) × $3.07 | 6.14 | price page |
| Confirm Parts Placement | 0.45 | price page; CLAUDE.md §4.2 requires placement checking |
| Components, with attrition | 27.32 | API snapshot |
| Shipping to Japan, OCS Express | 7.23 | quote page, PCB-only parcel (0.24 kg); UPS Worldwide Express Saver was 9.79, DHL 17.62 |
| **Total** | **61.01** | |

Standard PCBA keeps the joint and placement-confirmation fees. Setup rises to 25.56 and the
stencil to 8.21, and it adds feeder loading (41 types × 1.53 = 62.73), packing 0.50 and the
fixture 16.42. Its total is $158.58.

The dearest machine-placed lines are the W25Q128JVSIQ flash ($4.92 for 2 at its 1–9 piece
price), the PSM712 ($3.11), the AO3401A (14 per board, $3.08), the CH335F ($2.23), the
22 µF capacitors ($2.21), the RP2040 ($2.18) and the OP07 ($1.34). The 0402 resistors cost
cents in total.

### The real quote, 2026-11-12 (issue #6)

JLCPCB's quote for the actual files (5 boards, 2 assembled, Economic PCBA, leaded HASL) was
**$81.85 without shipping**, against $53.77 for the same lines above (the estimate's $61.01
less $7.23 shipping). The $28.08 difference:

| Cause | USD |
|---|---:|
| The 0.25 mm via class adds "4-Wire Kelvin Test" $17.02 and "Min via hole size/diameter" $17.14; the estimate did not know | +34.16 |
| Components at the quote's prices, 40 items: $20.47 against $27.32 | -6.85 |
| "Nitrogen reflow soldering", not in the estimate | +0.86 |
| SMT assembly $2.39 against $2.15 | +0.24 |
| Setup, stencil, Extended fee: +$0.06, +$0.02, +$0.04 | +0.12 |
| "Confirm Parts Placement" left off (the estimate budgeted it) | -0.45 |

At 160 yen/USD the JLCPCB part is 13,096 yen without shipping; the total of this study, 17,456 yen,
becomes about 21,950 yen if shipping stays at the estimate's $7.23. The form still prices the 0.24 kg
PCB-only parcel at $7.23 for OCS Express on 2026-11-12 (UPS $9.69, DHL $17.67 as the default, FedEx
$20.81); the assembled order weighs 556.50 g on the quote page and is priced only in the cart. The
line-by-line record is in
`manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md`, section 6.

### The via class removed, 2026-11-12 (issue #8)

Release candidate r02 drills every via at 0.30 mm, JLCPCB's standard class "0.3mm/(0.4/0.45mm)",
with the copper unchanged. That class is the quote form's default; r01's 0.25 mm vias needed the
dearer class, which adds the Kelvin test and the minimum-via fee. With r02's Gerber and the 0.3 mm
class the form priced the PCB at $8.00 with neither line
(`manufacturing/releases/rev0.4/r02/JLCPCB_REVIEW.md`). The PCBA lines were not quoted again: the
BOM and CPL are byte-identical to r01's, so r01's lines are carried over.

| | USD | Yen at 160 |
|---|---:|---:|
| JLCPCB without shipping: $81.85 − $34.16 | 47.69 | 7,630 |
| with OCS Express ($7.23, the PCB-only parcel) | 54.92 | 8,787 |
| with the Akizuki parts (7,695 yen) | — | **16,482** |

That is 5,466 yen less than the 21,950 yen above, about 8,240 yen per assembled unit. The assembled
parcel's shipping is still priced only in the cart.

### Rev0.5 against r02, 2026-11-12 (issues #8 and #10, D37 and D38)

The user's cost request, 「安価に製造できないとね、製造コストを下げて」, led to the lever
「USB-C直付けのみ (推奨)」: J1–J4 become the SHOU HAN receptacle C2765186, an Extended part
machine-placed at $0.0728 each (1–199 pieces, snapshot of 2026-11-12), and issue #10 adds four 1 kΩ
taps per board (R35–R38, C11702, a Basic line the board already has). `cost_estimate.py` prices the
change on r02's quote, because its own total above is dearer than the quote and is not the base:

| | USD | Yen at 160 |
|---|---:|---:|
| 11 receptacles: 8 needed + 3 attrition (`lossNumber`) | 0.80 | |
| 8 tap resistors, added to the existing C11702 line | 0.01 | |
| 144 SMT joints: 2 boards × (4 receptacles × 16 + 4 taps × 2) × $0.0016 | 0.23 | |
| A third Extended feeder fee | 3.07 | |
| **JLCPCB order gains** | **4.11** | 658 |
| The 8 modules (g113080, 350 yen each) and the 3 header strips (g100167, 35 yen each) leave the Akizuki order; its 550 yen shipping stays | | −2,905 |
| **Net** | | **−2,247** |

r02's 16,482 yen (above) becomes **14,235 yen for 2 units, 7,118 yen per unit**. The Akizuki order falls
from 7,695 to 4,790 yen, still under the 11,000 yen free-shipping line. What this cannot see: the real
price of the new BOM and CPL, which only the JLCPCB form gives (CLAUDE.md §9); impedance control, which
D37 reopens and does not decide (CIRCUIT_DESIGN_Rev0.7.md §9: $33.08 and an auto-selected $1.05 on
2026-11-03, 5,461 yen at 160 yen/USD); and the receptacle's joints, whose yield the first board shows
(V-MFG-03, OI-33).

**The quote, 2026-11-13 (issue #8, the JLCPCB gate).** JLCPCB's form gave **$51.94 without shipping**
for the Rev0.5 BOM and CPL: PCB $8.00, PCBA lines $43.94 by difference. It was read with r01's Gerber;
r02's Gerber leaves every option of the form unchanged and the PCB line stayed $8.00. That is $0.14
above the delta's $51.80 (r02's $47.69 + $4.11). With OCS Express ($7.23, read on 2026-11-12) the
JLCPCB order is $59.17, 9,467 yen, and with the Akizuki order of 4,790 yen **14,257 yen for 2 units,
7,129 yen per unit**, against the delta's 14,235 yen. Not in it: the PCBA lines one by one (read as a
total), the assembled parcel's shipping (in the cart only; DHL Express $17.67 is the default for the
0.24 kg PCB-only parcel) and impedance control (+$34.13 including the Confirm Production file).
`manufacturing/releases/rev0.5/r02/JLCPCB_REVIEW.md`, section 6.

## Akizuki (2 units, prices tax included)

| Part | Code | Each | Qty | Yen |
|---|---|---:|---:|---:|
| MCP3208-CI/P | g100238 | 500 | 4 | 2,000 |
| AE-USB2.0-TYPE-C | g113080 | 350 | 8 | 2,800 |
| MAU104 | g104132 | 520 | 2 | 1,040 |
| TSL1TTER100D | g109588 | 130 | 4 | 520 |
| MF-R300 | g112630 | 40 | 2 | 80 |
| MFU100F10RB, bag of 100 (4 needed) | g108805 | 600 | 1 | 600 |
| Pin header 1 × 40, PH-1x40SG (D33): 88 pins | g100167 | 35 | 3 | 105 |
| Shipping: the subtotal is below 11,000 yen | — | — | — | 550 |
| **Total** | | | | **7,695** |

The part prices are the ones `requirements/parts.md` recorded on 2026-11-03; the header's
was read on 2026-11-04 (D33). The header pins come from the OI-23 study: each USB-C module
takes 11, its 1 × 7 row and two 1 × 2 mechanical pieces (REQ-MECH-03). A board takes 44,
and two units 88, cut from 3 strips of 40. No sockets are bought (D33). Before D33 the
allowance left out the mechanical pins: it counted 28 pins and 1 strip per board since D31,
and 58 pins and 2 strips per board while the CH335F module's 30 pins were on the board. The
CH335F module (g129556, ¥420) is no longer bought. Below an 11,000 yen subtotal Akizuki
charges 550 yen per parcel (Sagawa) or 600 yen (Yamato). The 2-unit order is below it;
4 units would be above.

## Inputs and their dates

- **JLCPCB PCB price and shipping:** `cart.jlcpcb.com/quote`, read on 2026-11-03. Settings: FR4
  TG135, 4 layers, 100 × 72 mm, 5 pcs, 1.6 mm, green, 1 oz outer / 0.5 oz inner, Industrial,
  3–4 day build, ship to Japan. No order was placed.
- **Stackup and impedance control:** the same quote page, read in a browser on 2026-11-03 for
  D27 (`design/experiments/stackup-impedance/`). "Specify Stackup: Yes" with JLC04161H-7628
  named left the PCB at $25.40 ($8.00 + $17.40 ENIG). "Impedance Control ±10 %" added $33.08
  and auto-selected "Confirm Production file" at $1.05: $59.53 in total.
- **JLCPCB PCBA fees:** `jlcpcb.com/help/article/pcb-assembly-price`, "Last updated on Oct 22,
  2026", read on 2026-11-03.
- **Component prices:** `jlc_prices.json`, fetched on 2026-11-04 (its `checked_utc`) from the
  same API as `tools/jlc_stock.py`, for D29's 40 codes. For D31 the same day, C5137013 was
  queried alone and added with the same fields; the other 40 entries were not re-fetched.
  The 2026-11-03 snapshot it replaced is in Git history.
- **Economic PCBA limits:** JLCPCB blog, "How to Reduce Prototype PCB Assembly Cost (With Real
  Quotes)", `jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype`, published 2026-10-13,
  updated 2026-10-14, read on 2026-11-03.
- **Akizuki:** `requirements/parts.md` (2026-11-03). Shipping rule:
  `akizukidenshi.com/catalog/pages/buy.aspx`, read on 2026-11-03. The header's price and
  stock from its product page (`/catalog/g/g100167/`) on 2026-11-04 (D33).
- **Exchange rate:** 160 yen/USD as a planning value. A web search on 2026-11-03 found no
  November rate. Its results gave 158.27 on 2026-10-11 (30rates.com) and a 2026 high of 163.85
  on 2026-07-28 (valutafx.com). Neither page was opened, so both figures are second-hand. Every
  ±5 yen moves the Economic total by about ±305 yen.

## Counting

- **Joints and part count** come from the OI-23 study's package counts per block (239
  machine-placed parts, 673 joints per board). The script refuses to run if the BOM's package
  totals disagree with the study.
- **0402 values:** Rev0.4 numbers the passives at capture. The counts per value follow the
  "Use" column of parts.md, and U1's and U6's circuits (Rev0.4 §6.5, §6.6) are counted in
  full. The 29 positions that column does not attribute to a value (decoupling, comparator
  thresholds, the OC network) are priced at the dearest 0402 code, the 100 nF.
- **Order quantity per code:** need for 2 boards plus `lossNumber`, at least
  `leastPatchNumber`. This is the reading of the API fields, not a documented JLCPCB rule.

## What this cannot see

- **Whether Economic PCBA accepts this board.** The quote form decides only after an upload.
  The JLCPCB blog post (Inputs) lists what forces Standard.
  - This board avoids most of them: parts on Top only, nothing below 0402, no IC pitch below
    0.4 mm (the RP2040's LQFN-56 and the CH335F's QFN-28 are exactly 0.4 mm, D29, D31), 2 boards (at most 50), a single
    board rather than a V-cut panel, 1.6 mm and 4 layers, and no gold fingers, castellations
    or edge plating.
  - The post names "special stack-ups". That item is settled by D27: on the quote page
    (browser, 2026-11-03) JLC04161H-7628 was the only one of 18 named 4-layer stackups
    without the note "This is a special stackup, and it doesn't support economic PCB
    assembly", and naming it left the PCB price unchanged.
  - Impedance control is **not included**. D27 does not order it for the prototype; it would
    add $33.08 plus $1.05 for the auto-selected "Confirm Production file". Whether it would
    change the assembly class is unseen.
  - One item remains open: whether green mask, 1.6 mm and leaded HASL (D30) form an Economic
    combination is not confirmed. The blog says Standard is forced by "a thickness, solder
    mask color, and surface finish combination outside the Economic options", but does not
    list the options (re-read 2026-11-04).
  - If it forces Standard, the order is the Standard case: about 15,600 yen more.
- **The real BOM.** The schematic is not captured. The 0402 count is an estimate. The 0402
  line is cents; an added active part is not. If Y1 fails on the first board, its fallback
  (ABM8-272-T3, C20625731) is a third Extended type: another $3.07 per order, and the user's
  decision (Rev0.4 §6.3).
- **The PCBA parcel's shipping.** Only the PCB-only parcel was priced.
- **Rework from HASL.** D30's leaded HASL is not flat, and U1 and U6 are 0.4 mm-pitch QFNs
  with ePads. A bridged or open joint on either costs a rework or a new board (V-MFG-03); no
  allowance is included.
- **Japanese import tax.** Not included. The rule as understood, not checked against Japan
  Customs today: for personal use, the taxable value is 60 % of the price, and a taxable value of
  10,000 yen or less is exempt. On that rule the Economic order (≈ 5,900 yen taxable) is
  exempt. The Standard order (≈ 15,200 yen) would pay about 1,500 yen of consumption tax plus
  the courier's fee.
- **Possible extra JLCPCB charges.** X-ray inspection applies to leadless packages. The
  RP2040's LQFN-56 and the CH335F's QFN-28 are two, so expect it: 2 × $1.64 if it is charged
  per board, not included in the totals. Standard
  PCBA may also add stencil or fixture storage ($4.93 each).
- **Discounts.** The "Special Offer" base price and the new-customer coupons shown on the page
  can change or expire. Neither the coupons nor any other discount is applied.
- **Items with no price yet:** the M2 heat-set inserts (D21), the enclosure print and spare
  parts.
