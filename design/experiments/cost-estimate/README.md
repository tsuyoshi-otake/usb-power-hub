# Prototype cost estimate (Rev0.4, 2026-11-03; re-run 2026-11-04 for D29 and D30) — non-authoritative

**Question.** What does a first prototype cost? The order is JLCPCB fabricating **5 bare
PCBs** and assembling **2** of them, plus the Akizuki parts the user solders by hand onto
those 2.

Since D29 (2026-11-04) the MCU is a bare RP2040 (C2040), machine-placed with its flash,
crystal and passives, instead of the hand-soldered PGA2040 module (¥1,680 each). The figures
below are the re-run's, with a price snapshot fetched on 2026-11-04. Since D30 (the same day)
the finish is leaded HASL instead of ENIG, and the plan ships by OCS Express, the cheapest
quoted, instead of UPS (the user: 「UPSじゃなくていい」).

**Answer** (at 160 yen/USD; Japanese import tax, M2 inserts and the enclosure print are not
included):

| Case | JLCPCB order | Akizuki parts | Total, 2 units | Per unit |
|---|---:|---:|---:|---:|
| **Economic PCBA** (recommended) | $55.69 = 8,910 yen | 8,570 – 9,050 yen | **17,480 – 17,960 yen** | 8,740 – 8,980 yen |
| Standard PCBA | $154.80 = 24,768 yen | 8,570 – 9,050 yen | 33,338 – 33,818 yen | 16,669 – 16,909 yen |

With the PGA2040 (before D29), ENIG and UPS, the Economic case was 21,883 – 22,843 yen for
2 units. D29 saved 1,209 – 1,689 yen of that (20,674 – 21,154 yen, still with ENIG and UPS).
That saving is per unit: the module cost 1,680 yen each, and the RP2040, its flash, crystal
and passives cost about $3.8 per board, plus one $3.07 Extended feeder fee per order. D30's
leaded HASL saves $17.40 and OCS Express $2.56 per order: $19.96, 3,194 yen. Akizuki now
charges 550 yen shipping, because the subtotal falls below 11,000 yen.

The Akizuki range is pin headers only, or headers plus sockets for the modules. The lid
panel PCB adds $4.00 (640 yen) if it is ordered in the same JLCPCB order.

Economic PCBA is the recommendation. It charges no feeder fee for Basic parts and $3.07 per
Extended part type; since D29 the board has one, the RP2040. It saves $99.11 (about
15,900 yen) against Standard. Standard is the fallback if the order form refuses this board
for Economic (see "What this cannot see").

This directory is an estimate, not a quote (CLAUDE.md §2: `design/experiments/` is
non-authoritative). The real price is the one shown after the Gerber, BOM and CPL are
uploaded, and CLAUDE.md §9 requires a recheck at every release. Nothing here is orderable:
the board is WIP and has no layout.

## Files

| File | What it is |
|---|---|
| `cost_estimate.py` | The estimate: `python -I -B design/experiments/cost-estimate/cost_estimate.py`. `--fetch` refreshes the price snapshot through `tools/jlc_stock.py`. Exits 1 if the BOM disagrees with the OI-23 placement study, or a part is not Basic and not an approved exception (`APPROVED_EXTENDED`: C2040, D29). |
| `test_cost_estimate.py` | 12 tests. Five corrupt the BOM, the study, the code list or a part's class and expect the check to fail (CLAUDE.md §8). |
| `jlc_prices.json` | JLCPCB assembly-parts API snapshot, 2026-11-04: class, stock, price tiers, attrition (`lossNumber`) and minimum quantity (`leastPatchNumber`) for the 40 machine-placed codes. |

## JLCPCB, Economic PCBA (2 assembled of 5)

| Item | USD | Source |
|---|---:|---|
| PCB: 4 layers, 100 × 72 mm, 1.6 mm, 5 pcs, base price | 8.00 | quote page, shown as "Special Offer" |
| Finish: leaded HASL (D30) | 0.00 | quote page; LeadFree HASL is +5.20, ENIG +17.40 |
| PCBA setup | 8.18 | price page |
| Stencil | 1.53 | price page |
| SMT joints: 650 per board × 2 × $0.0016 | 2.08 | price page; joints from the study's package counts (the QFN-56 counted as 57, its ePad included) |
| Extended-part feeder fee: 1 type (C2040, D29) × $3.07 | 3.07 | price page |
| Confirm Parts Placement | 0.45 | price page; CLAUDE.md §4.2 requires placement checking |
| Components, with attrition | 25.15 | API snapshot |
| Shipping to Japan, OCS Express | 7.23 | quote page, PCB-only parcel (0.24 kg); UPS Worldwide Express Saver was 9.79, DHL 17.62 |
| **Total** | **55.69** | |

Standard PCBA keeps the joint and placement-confirmation fees. Setup rises to 25.56 and the
stencil to 8.21, and it adds feeder loading (40 types × 1.53 = 61.20), packing 0.50 and the
fixture 16.42. Its total is $154.80.

The dearest machine-placed lines are the W25Q128JVSIQ flash ($4.92 for 2 at its 1–9 piece
price), the PSM712 ($3.11), the AO3401A (14 per board, $3.08), the 22 µF capacitors ($2.21),
the RP2040 ($2.18) and the OP07 ($1.34). The 0402 resistors cost cents in total.

## Akizuki (2 units, prices tax included)

| Part | Code | Each | Qty | Yen |
|---|---|---:|---:|---:|
| MCP3208-CI/P | g100238 | 500 | 4 | 2,000 |
| AE-USB2.0-TYPE-C | g113080 | 350 | 8 | 2,800 |
| AE-QFN28-DIP(CH335F) | g129556 | 420 | 2 | 840 |
| MAU104 | g104132 | 520 | 2 | 1,040 |
| TSL1TTER100D | g109588 | 130 | 4 | 520 |
| MF-R300 | g112630 | 40 | 2 | 80 |
| MFU100F10RB, bag of 100 (4 needed) | g108805 | 600 | 1 | 600 |
| Pin header 1 × 40, PH-1x40SG (allowance) | 100167 | 35 | 4 | 140 |
| Shipping: the subtotal is below 11,000 yen | — | — | — | 550 |
| **Headers only** | | | | **8,570** |
| Plus pin sockets 1 × 40, FH2.54-40U1GF8.5-0.5 (allowance) | 110073 | 120 | 4 | +480 |

The part prices are the ones `requirements/parts.md` recorded on 2026-11-03. The headers and
sockets are not selected yet (parts.md "Not yet selected"); their lines are an allowance at
prices read on 2026-11-03. Since D29 the modules need 58 header pins per board (four USB-C
modules × 7 and the CH335F's 30), so the allowance is 2 strips of 40 per board, down from 4.
Below an 11,000 yen subtotal Akizuki charges 550 yen per parcel (Sagawa) or 600 yen
(Yamato). Without the PGA2040 the 2-unit order is below it; 4 units would be above.

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
  same API as `tools/jlc_stock.py`, for D29's 40 codes. The 2026-11-03 snapshot it replaced
  is in Git history.
- **Economic PCBA limits:** JLCPCB blog, "How to Reduce Prototype PCB Assembly Cost (With Real
  Quotes)", `jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype`, published 2026-10-13,
  updated 2026-10-14, read on 2026-11-03.
- **Akizuki:** `requirements/parts.md` (2026-11-03). Shipping rule:
  `akizukidenshi.com/catalog/pages/buy.aspx`, read on 2026-11-03. Header and socket prices from
  the Akizuki search page on 2026-11-03.
- **Exchange rate:** 160 yen/USD as a planning value. A web search on 2026-11-03 found no
  November rate. Its results gave 158.27 on 2026-10-11 (30rates.com) and a 2026 high of 163.85
  on 2026-07-28 (valutafx.com). Neither page was opened, so both figures are second-hand. Every
  ±5 yen moves the Economic total by about ±280 yen.

## Counting

- **Joints and part count** come from the OI-23 study's package counts per block (241
  machine-placed parts, 650 joints per board). The script refuses to run if the BOM's package
  totals disagree with the study.
- **0402 values:** Rev0.4 numbers the passives at capture. The counts per value follow the
  "Use" column of parts.md, and U1's circuit (Rev0.4 §6.5) is counted in full. The 34
  positions that column does not attribute to a value (decoupling, comparator thresholds,
  the OC network, hub straps) are priced at the dearest 0402 code, the 100 nF.
- **Order quantity per code:** need for 2 boards plus `lossNumber`, at least
  `leastPatchNumber`. This is the reading of the API fields, not a documented JLCPCB rule.

## What this cannot see

- **Whether Economic PCBA accepts this board.** The quote form decides only after an upload.
  The JLCPCB blog post (Inputs) lists what forces Standard.
  - This board avoids most of them: parts on Top only, nothing below 0402, no IC pitch below
    0.4 mm (the RP2040's LQFN-56 is exactly 0.4 mm, D29), 2 boards (at most 50), a single
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
  - If it forces Standard, the order is the Standard case: about 15,900 yen more.
- **The real BOM.** The schematic is not captured. The 0402 count is an estimate. The 0402
  line is cents; an added active part is not. If Y1 fails on the first board, its fallback
  (ABM8-272-T3, C20625731) is a second Extended type: another $3.07 per order, and the user's
  decision (Rev0.4 §6.3).
- **The PCBA parcel's shipping.** Only the PCB-only parcel was priced.
- **Rework from HASL.** D30's leaded HASL is not flat, and U1 is a 0.4 mm-pitch QFN with an
  ePad. A bridged or open U1 joint costs a rework or a new board (V-MFG-03); no allowance is
  included.
- **Japanese import tax.** Not included. The rule as understood, not checked against Japan
  Customs today: for personal use, the taxable value is 60 % of the price, and a taxable value of
  10,000 yen or less is exempt. On that rule the Economic order (≈ 5,300 yen taxable) is
  exempt. The Standard order (≈ 14,900 yen) would pay about 1,500 yen of consumption tax plus
  the courier's fee.
- **Possible extra JLCPCB charges.** X-ray inspection applies to leadless packages. The
  RP2040's LQFN-56 is one, so expect it now: 2 × $1.64, not included in the totals. Standard
  PCBA may also add stencil or fixture storage ($4.93 each).
- **Discounts.** The "Special Offer" base price and the new-customer coupons shown on the page
  can change or expire. Neither the coupons nor any other discount is applied.
- **Items with no price yet:** the M2 heat-set inserts (D21), the enclosure print and spare
  parts.
