# Prototype cost estimate (Rev0.4, 2026-11-03) — non-authoritative

**Question.** What does a first prototype cost? The order is JLCPCB fabricating **5 bare
PCBs** and assembling **2** of them, plus the Akizuki parts the user solders by hand onto
those 2.

**Answer** (at 160 yen/USD; Japanese import tax, M2 inserts and the enclosure print are not
included):

| Case | JLCPCB order | Akizuki parts | Total, 2 units | Per unit |
|---|---:|---:|---:|---:|
| **Economic PCBA** (recommended) | $64.77 = 10,363 yen | 11,520 – 12,480 yen | **21,883 – 22,843 yen** | 10,941 – 11,421 yen |
| Standard PCBA | $159.30 = 25,488 yen | 11,520 – 12,480 yen | 37,008 – 37,968 yen | 18,504 – 18,984 yen |

The Akizuki range is pin headers only, or headers plus sockets for the modules. The lid
panel PCB adds $4.00 (640 yen) if it is ordered in the same JLCPCB order.

Economic PCBA is the recommendation. It charges no feeder fee for Basic parts, and D22 made
every machine-placed part Basic, so it saves $94.53 (about 15,100 yen) against Standard.
Standard is the fallback if the order form refuses this board for Economic (see "What this
cannot see").

This directory is an estimate, not a quote (CLAUDE.md §2: `design/experiments/` is
non-authoritative). The real price is the one shown after the Gerber, BOM and CPL are
uploaded, and CLAUDE.md §9 requires a recheck at every release. Nothing here is orderable:
the board is WIP and has no layout.

## Files

| File | What it is |
|---|---|
| `cost_estimate.py` | The estimate: `python -I -B design/experiments/cost-estimate/cost_estimate.py`. `--fetch` refreshes the price snapshot through `tools/jlc_stock.py`. Exits 1 if the BOM disagrees with the OI-23 placement study or a part is not Basic. |
| `test_cost_estimate.py` | 11 tests. Four corrupt the BOM, the study or the code list and expect the check to fail (CLAUDE.md §8). |
| `jlc_prices.json` | JLCPCB assembly-parts API snapshot, 2026-11-03: class, stock, price tiers, attrition (`lossNumber`) and minimum quantity (`leastPatchNumber`) for the 35 machine-placed codes. |

## JLCPCB, Economic PCBA (2 assembled of 5)

| Item | USD | Source |
|---|---:|---|
| PCB: 4 layers, 100 × 72 mm, 1.6 mm, 5 pcs, base price | 8.00 | quote page, shown as "Special Offer" |
| ENIG finish (CLAUDE.md §9) | 17.40 | quote page; LeadFree HASL is +5.20, leaded HASL +0.00 |
| PCBA setup | 8.18 | price page |
| Stencil | 1.53 | price page |
| SMT joints: 545 per board × 2 × $0.0016 | 1.74 | price page; joints from the study's package counts |
| Extended-part feeder fee | 0.00 | none: every machine-placed part is Basic (D22) |
| Confirm Parts Placement | 0.45 | price page; CLAUDE.md §4.2 requires placement checking |
| Components, with attrition | 17.67 | API snapshot |
| Shipping to Japan, UPS Worldwide Express Saver | 9.79 | quote page, PCB-only parcel (0.24 kg); OCS Express was 7.23, DHL 17.62 |
| **Total** | **64.77** | |

Standard PCBA keeps the joint and placement-confirmation fees. Setup rises to 25.56 and the
stencil to 8.21, and it adds feeder loading (35 types × 1.53 = 53.55), packing 0.50 and the
fixture 16.42. Its total is $159.30.

The dearest machine-placed lines are the AO3401A (14 per board, $3.08), the PSM712 ($3.11),
the 22 µF capacitors ($2.21) and the OP07 ($1.36). The 0402 resistors cost cents in total.

## Akizuki (2 units, prices tax included)

| Part | Code | Each | Qty | Yen |
|---|---|---:|---:|---:|
| PGA2040 | g116762 | 1,680 | 2 | 3,360 |
| MCP3208-CI/P | g100238 | 500 | 4 | 2,000 |
| AE-USB2.0-TYPE-C | g113080 | 350 | 8 | 2,800 |
| AE-QFN28-DIP(CH335F) | g129556 | 420 | 2 | 840 |
| MAU104 | g104132 | 520 | 2 | 1,040 |
| TSL1TTER100D | g109588 | 130 | 4 | 520 |
| MF-R300 | g112630 | 40 | 2 | 80 |
| MFU100F10RB, bag of 100 (4 needed) | g108805 | 600 | 1 | 600 |
| Pin header 1 × 40, PH-1x40SG (allowance) | 100167 | 35 | 8 | 280 |
| Shipping: free from 11,000 yen | — | — | — | 0 |
| **Headers only** | | | | **11,520** |
| Plus pin sockets 1 × 40, FH2.54-40U1GF8.5-0.5 (allowance) | 110073 | 120 | 8 | +960 |

The part prices are the ones `requirements/parts.md` recorded on 2026-11-03. The headers and
sockets are not selected yet (parts.md "Not yet selected"); their lines are an allowance at
prices read on 2026-11-03. Below an 11,000 yen subtotal Akizuki charges 550 yen per parcel
(Sagawa) or 600 yen (Yamato), so a single unit's parts would pay it.

## Inputs and their dates

- **JLCPCB PCB price and shipping:** `cart.jlcpcb.com/quote`, read on 2026-11-03. Settings: FR4
  TG135, 4 layers, 100 × 72 mm, 5 pcs, 1.6 mm, green, 1 oz outer / 0.5 oz inner, Industrial,
  3–4 day build, ship to Japan. No order was placed.
- **JLCPCB PCBA fees:** `jlcpcb.com/help/article/pcb-assembly-price`, "Last updated on Oct 22,
  2026", read on 2026-11-03.
- **Component prices:** `jlc_prices.json`, fetched on 2026-11-03 (its `checked_utc`) from the
  same API as `tools/jlc_stock.py`.
- **Economic PCBA limits:** JLCPCB blog, "How to Reduce Prototype PCB Assembly Cost (With Real
  Quotes)", `jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype`, published 2026-10-13,
  updated 2026-10-14, read on 2026-11-03.
- **Akizuki:** `requirements/parts.md` (2026-11-03). Shipping rule:
  `akizukidenshi.com/catalog/pages/buy.aspx`, read on 2026-11-03. Header and socket prices from
  the Akizuki search page on 2026-11-03.
- **Exchange rate:** 160 yen/USD as a planning value. A web search on 2026-11-03 found no
  November rate. Its results gave 158.27 on 2026-10-11 (30rates.com) and a 2026 high of 163.85
  on 2026-07-28 (valutafx.com). Neither page was opened, so both figures are second-hand. Every
  ±5 yen moves the Economic total by about ±320 yen.

## Counting

- **Joints and part count** come from the OI-23 study's package counts per block (220
  machine-placed parts, 545 joints per board). The script refuses to run if the BOM's package
  totals disagree with the study.
- **0402 values:** Rev0.4 numbers the passives at capture. The counts per value follow the
  "Use" column of parts.md. The 38 positions that column does not attribute to a value
  (decoupling, comparator thresholds, the OC network, hub straps, the two 27 Ω resistors of
  OI-31) are priced at the dearest 0402 code, the 100 nF.
- **Order quantity per code:** need for 2 boards plus `lossNumber`, at least
  `leastPatchNumber`. This is the reading of the API fields, not a documented JLCPCB rule.

## What this cannot see

- **Whether Economic PCBA accepts this board.** The quote form decides only after an upload.
  The JLCPCB blog post (Inputs) lists what forces Standard.
  - This board avoids most of them: parts on Top only, nothing below 0402, no IC pitch below
    0.4 mm, 2 boards (at most 50), a single board rather than a V-cut panel, 1.6 mm and 4
    layers, and no gold fingers, castellations or edge plating.
  - Two items remain open:
    - The post names "special stack-ups". CLAUDE.md §5.1 requires a named JLCPCB stackup and
      possibly impedance control, and whether that counts is not known.
    - Whether green mask, 1.6 mm and ENIG form an Economic combination is not confirmed.
  - If either forces Standard, the order is the Standard case: about 15,100 yen more.
- **The real BOM.** The schematic is not captured. The 0402 count and the 27 Ω pair are
  estimates, and OI-31 may remove or add parts. The 0402 line is cents; an added active part
  is not.
- **The PCBA parcel's shipping.** Only the PCB-only parcel was priced.
- **Japanese import tax.** Not included. The rule as understood, not checked against Japan
  Customs today: for personal use, the taxable value is 60 % of the price, and a taxable value of
  10,000 yen or less is exempt. On that rule the Economic order (≈ 6,200 yen taxable) is
  exempt. The Standard order (≈ 15,300 yen) would pay about 1,500 yen of consumption tax plus
  the courier's fee.
- **Possible extra JLCPCB charges.** X-ray inspection applies to leadless packages; if the
  4-pad 3225 crystal counts, it adds 2 × $1.64. Standard PCBA may also add stencil or fixture
  storage ($4.93 each).
- **Discounts.** The "Special Offer" base price and the new-customer coupons shown on the page
  can change or expire. Neither the coupons nor any other discount is applied.
- **Items with no price yet:** the M2 heat-set inserts (D21), the enclosure print and spare
  parts.
