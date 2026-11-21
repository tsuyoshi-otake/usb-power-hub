# JLCPCB order of release r01 (issue #14)

**The user ordered this release and paid for it** on 2026-11-20, about 00:40 (JST), from JLCONE, JLCPCB's
desktop application, on another PC. The approval is the user's 「支払いまでやったよ」 of 2026-11-20. Claude
placed no order and made no payment.

**What this file is.** It is not a gate that ran before the order, as `../../rev0.6/r01/JLCPCB_REVIEW.md` is.
The upload, the form, the part mapping, the placement preview and the quote below were read in a session on
that other PC, which had no Git and worked from a ZIP of `main`; the user reported them on 2026-11-20, and this
file records that report. The session that wrote this file saw none of those pages. It checked what can be
checked here: the three SHA-256 against this directory (section 1) and the report's figures against the board
and the earlier reviews (sections 2 to 6). **JLCDFM was never run on Rev0.7** (section 4).

| Item | Value |
|---|---|
| What was ordered | `UsbPowerHub_Main_Rev0.7_Gerber.zip`, `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv` of this directory |
| Ordered and paid | 2026-11-20, about 00:40 (JST), by the user, from JLCONE |
| Quantities | 5 boards, 2 assembled (Economic PCBA, Top side) |
| Amount paid, coupons used | **$30.99**, shipping included, by card; a discount of $31.56 (section 6, read 2026-11-20) |
| Account data | the order number, the file number, the SMT number and the address are not recorded anywhere in this repository |

Evidence: no screenshot and no page text was saved; the other PC kept nothing that this repository can name.

## 1. The files

| Uploaded file | SHA-256 as reported | Against `SHA256SUMS.txt` here |
|---|---|---|
| `UsbPowerHub_Main_Rev0.7_Gerber.zip` | `17882e76666e0e85624400e737cf372c1b14d4d7d15ea101049042b9cd96cd0f` | equal |
| `UsbPowerHub_Main_Rev0.7_BOM_JLCPCB.csv` | `c2a5455389db1466c1e59f17ba812988152e44c914a6735a808e96efce9d7b06` | equal; also Rev0.6 r01's BOM, byte for byte |
| `UsbPowerHub_Main_Rev0.7_CPL_JLCPCB.csv` | `a2f278e692157fd10aef00a79a9378a5643413b0a36f0c0f5293c9bc2fc7e7ac` | equal; also Rev0.6 r01's CPL, byte for byte |

On the other PC the eleven lines of `SHA256SUMS.txt` were checked with `Get-FileHash` (11 of 11 equal, as
reported). Here `sha256sum -c SHA256SUMS.txt` passed on 2026-11-20 before this file was added.

## 2. Options JLCPCB's form took, against the manifest

As reported from JLCONE's form with this Gerber.

| Option | JLCPCB form | Manifest / decision | Verdict |
|---|---|---|---|
| Base material, layers, size, quantity | FR-4, "Detected 4 layer board of 72x100mm", 5 boards | D10, D24 | match |
| Thickness | 1.6 mm | 1.6 mm | match |
| Stackup | "Specify Stackup": **No**; JLC04161H-7628 was not named | D27, "named on the order" | **differs from D27**: the order takes JLCPCB's default stackup for a 1.6 mm 4-layer board, which this repository has not read. D27's pair geometry (W 0.31 / S 0.15 mm) was computed for JLC04161H-7628 |
| Impedance control | none | D27 (not ordered for the prototype) | match |
| Surface finish | HASL (with lead) | D30 | match |
| Copper | outer 1 oz, inner 0.5 oz | outer 0.035 mm, inner 0.0152 mm | match |
| Via size class | 0.3mm/(0.4/0.45mm) | every via 0.30 mm hole | match |
| Via covering | Plugged | the board tents its vias; the form offers Plugged | as on Rev0.5 and Rev0.6 |
| Material type | FR4 TG135 | not in the manifest | recorded |
| Colour, silkscreen | green, white | no decision recorded them before the order | the order decides them |
| Outline tolerance | ±0.2 mm | none | recorded |
| Confirm Production file | **Yes** (+$1.05) | the user's choice of 2026-11-19 on Rev0.6 r01 | match. The box "do not confirm automatically" was **not** ticked: the file is approved by itself 48 hours after JLCPCB has prepared it (wrong: the order page gives about 96 hours, section 8) |
| Assembly | Economic PCBA, Top side, 2 boards, tooling holes added by JLCPCB, parts selected by the customer | D13, REQ-MFG-01 | match |
| Confirm Parts Placement | **No** | CLAUDE.md 4.2 asks for placement checking | JLCPCB's engineers do not send the placement back for a check |
| Build time | PCB 3 days, assembly 3-4 days | none | recorded |
| Product description | Research\Education\DIY > Development Board (HS 847330), chosen by the user | none | recorded |
| Weight | 585.90 g | none | recorded |

## 3. Part mapping

- "41 detected". Extended: C2040 (U1), C5137013 (U6), C2765186 (J1-J4), the three that D29, D31 and D37 allow;
  every other part Basic; **0 substituted**.
- The merged 510 Ω row (C17734, quantity 16) stood unselected with quantity 0 and was ticked by hand, as on
  Rev0.4, Rev0.5 and Rev0.6 (Rev0.6's finding 5).
- The counter read "42 Parts confirmed" on the first pass and "41 Parts confirmed" after *Edit Order*. The "42"
  was not explained on Rev0.6 either.
- **Stock was not read on the day of the order**: `tools/jlc_stock.py` was not run. The last read is of
  2026-11-19 (`../../rev0.6/r01/JLCPCB_REVIEW.md` section 3: every code above 500). The order was accepted with
  the 41 rows selected.

## 4. DFM

**JLCDFM was not run on this Gerber, or on any Rev0.7 file.** The order went out without it.

What is known instead:

- The board passes KiCad's DRC with JLCPCB's hole figures as custom rules, and `check_pcb.py`,
  `check_routing.py` and `check_silk.py` (the manifest).
- Rev0.6 r01's JLCDFM run (`../../rev0.6/r01/JLCPCB_REVIEW.md` section 4) judged copper that this board carries
  everywhere except at J5. Its findings on carried copper stand: the GND via 0.059 mm from D1 pad 3 (accepted by
  the user), the 0.60 mm slots (kept by the user), the vias in the pads of U1, U6, Q18 and Q38.
- New at J5, and read by no JLCPCB tool: eight 1.7 mm pads with 0.84 mm between them, and two GND vias 0.104 mm
  from pads 3 and 5 (one net).
- **The non-plated holes.** Rev0.6's finding 2 stands: JLCDFM's viewer listed the non-plated drill file as a
  plated layer. This board has **12** non-plated holes, not Rev0.6's 15: the 8 receptacle pegs of 0.65 mm and
  H1-H4 of 2.2 mm. J5 has no hole on Rev0.7 (the Tag-Connect land's three 0.991 mm holes are gone). The
  production file is the place to see how JLCPCB's CAM reads them.

## 5. Placement preview

As reported (2-D view, Top):

- No part stands on J5's eight pads. SW3 is beside them and does not overlap.
- J1 and J4 are on the back edge, J2 and J3 on the front edge. The view was cut off at the bottom, so J2 and J3
  were **not read in detail**.
- The CPL is Rev0.6 r01's file, so that review's readings of 2026-11-19 are of these very rows (its section 5).
  They were read with Rev0.6's Gerber behind them; no part moved between the two boards.

A viewer's drawing of JLCPCB's models, not its pick-and-place; and "Confirm Parts Placement" is No.

## 6. Quote and payment

As reported, in USD, without shipping:

| Line | Amount |
|---|---:|
| PCB, 5 boards | 8.00 |
| Confirm Production file | 1.05 |
| **PCB total** | **9.05** |
| PCBA: setup | 8.24 |
| PCBA: stencil | 1.55 |
| PCBA: components (41) | 22.20 |
| PCBA: Extended fee | 9.27 |
| PCBA: SMT | 2.72 |
| PCBA: nitrogen reflow | 0.86 |
| **PCBA total** | **44.84** |
| **Total without shipping** | **53.89** |

The lines add up (9.05 + 44.84 = 53.89). Rev0.6 r01's quote of 2026-11-19 was $52.85, and $53.90 with "Confirm
Production file"; its PCBA lines were not read one by one, so the $0.01 is not located.

- Shipping seen before checkout: OCS Express $8.66, 4 to 6 business days.
- Coupons: in the cart the coupon "$30 Off $50" was seen applied.
- The cart item of Rev0.6 r01 was removed from the cart by the user before the payment.

**What was paid**, read by Claude on 2026-11-20 in the user's Chrome, after the user signed in (「確認して」,
then 「サインインした」), from the order's page and the account's coupon list. Read only; nothing was changed.

| Line | Amount |
|---|---:|
| Merchandise total (PCB $9.05 + PCBA $44.84) | 53.89 |
| Shipping, OCS Express | 8.66 |
| Discount | -31.56 |
| **Order total, paid** | **30.99** |

- The lines add up (53.89 + 8.66 - 31.56 = 30.99). The order list shows the discount spread over the items:
  PCB $3.76 (from $9.05) and PCBA $18.57 (from $44.84), together $22.33.
- Paid by card; submitted 00:42, paid and reviewed 00:44, in production 00:46 (JST, 2026-11-20).
- **Which coupons make up the $31.56 is not shown** on the order's page. The account's list of coupons used
  in the last six months names two that are still valid and so are new: "$30 Off $50" ($30, orders over $50,
  until 2026-12-04) and "BF Prototype $8 - JLCONE" ($8, orders over $20, until 2026-11-29; not among the four
  read on 2026-11-20 before the order). The list names no order, and $30 + $8 = $38 is not $31.56, so how the
  discount is made is not settled here; JLCONE's own desktop discount ("Save $1-$20") is a third possibility.
- The order total, $30.99, is $22.90 below the quote without shipping ($53.89).

Also read on the order's page, not reported from the other PC: "Electrical Test: Flying Probe Fully Test",
"Mark on PCB: Remove Mark", "Appearance Quality: IPC Class 2 Standard", "Silkscreen Technology: Ink-jet
Printing Silkscreen", "Specify Stackup: no", "Confirm Production file: Yes", total weight 0.59 kg. The state
of both items was "Data Preparation": JLCPCB had not yet prepared the production file (section 8, step 1).

## 7. Not done before the order

| Not done | Consequence |
|---|---|
| JLCDFM on Rev0.7's Gerber | section 4; JLCPCB's own review after the order is the only DFM this Gerber gets |
| JLCPCB stock read on the day (`tools/jlc_stock.py`) | section 3 |
| Akizuki stock read on the day | last read 2026-11-19 (`../../rev0.6/r01/RELEASE_MANIFEST.md`); the hand-soldered parts are bought separately |
| Stackup named on the order | section 2 |
| The placement of J2 and J3 read in this order's preview | section 5 |
| The state `MANUFACTURING APPROVED` and the pre-order checklist of CLAUDE.md 12 | the user ordered with the open items of that checklist standing; the manifest lists them |
| The clamp tried on J5 | D40: the first board is the check |

## 8. What comes next

1. ~~**The production file**~~: read on 2026-11-20 (section 9) and **confirmed on 2026-11-21** ("Yes, please proceed to production", submitted by Claude at the user's 「製造に進めて」; the order's tracking reads "<file number> manufacturing data finished." (the number is account data and is not written here) at 12:38:45 JST). Before that it was not confirmed: the order page asked
   for the confirmation "within 94h20m" (read at 11:45 JST, so until about 2026-11-24 10:00 JST), "or your
   order will be produced directly". Not 48 hours as section 2 assumed.
2. ~~The amount paid and the coupons used~~: read on 2026-11-20 (section 6); the split of the discount is
   not shown.
3. The hand-soldered parts from Akizuki (`UsbPowerHub_Main_Rev0.7_HandSolder.csv`).
4. The enclosure and the lid for the Rev0.7 board.

## 9. The production file (read 2026-11-20)

The order page's PCB item read "Data Preparation" with the action "Confirm Production file". Its dialog shows a
Top and a Bottom picture, the link "Download Production file", and the choice "Yes, please proceed to
production" / "Not good, modification needed" with "Submit". Nothing in the dialog was chosen or submitted on 2026-11-20. **On 2026-11-21 the dialog showed the same green previews, and "Yes, please proceed to production" was submitted** (the user: 「製造に進めて」, after JLCPCB had answered that an Economic 4-layer order takes green mask only). The button now reads "Production file Confirmed".
With the user's approval (「読んでいい」, then 「ダウンロードしていい」) the production file was downloaded and
read in `~/tmp/`, outside this repository, and deleted afterwards; none of it is kept here, because it carries
the account's order and file numbers.

- The download: `UsbPowerHub_Main_Rev0.7_Gerber_Y41.zip`, 4,669,658 bytes, SHA-256
  `15ddcb636630bd2ffe6806d66c00ebb5511d27e8e30fbd616e62282f4ebb6a90`. It holds the 15 files of our Gerber zip
  as uploaded, JLCPCB's JSON of the order's parameters, and the CAM output of "JLCCam Pro" (Gerber per layer
  and an ODB++ job).
- Read with scratch scripts that are not kept: the CAM drill layer against our `_PTH.drl` and `_NPTH.drl`
  (position within 0.02 mm), the tool table of the ODB++ job, the CAM mask and copper at J5, the parameter JSON.

| What | In JLCPCB's CAM | Verdict |
|---|---|---|
| The 12 non-plated holes | 8 × 0.65 mm (pegs of J1-J4) and 4 × 2.20 mm (H1-H4) at our positions, tool type `NON_PLATED`, drilled 0.70 and 2.25 mm | as designed; Rev0.6's finding 2 (JLCDFM's viewer showing them as plated) does not reach the CAM |
| The 16 slots of J1-J4 | 16 routed slots at our positions, `PLATED`, finished 0.60 mm (drilled 0.751 mm) | as designed |
| The other plated holes | 415 vias 0.30 mm (`VIA`), 36 × 0.80, 4 × 1.00, 2 × 1.10 mm (`PLATED`) at our positions | as designed |
| **Two holes JLCPCB added** | 2 × 1.152 mm, `NON_PLATED`, at (1.56, 5.84) and (98.44, 66.10) mm, about 3.0 mm from H1 and H4; copper cleared to 1.55 mm on all four layers, bottom mask open 1.35 mm, legend cleared | not in our files: the tooling holes the form says JLCPCB adds for the assembly ("tooling holes added by JLCPCB"), placed inside the board since it has no rails. KiCad finds only the GND pours of L2, L3 and L4 there: no pad, no track and no courtyard within 1.0 mm (H1's and H4's courtyards 1.05 and 1.09 mm away). Accepted as JLCPCB's; the enclosure does not model them |
| J5's eight pads | open in the top mask, 1.715 mm (copper 1.715 mm after JLCPCB's etch compensation; ours 1.70 mm), pin 1 square; no paste in our `F_Paste` | as designed |
| The legend at J5 | the picture of our top legend shows `SWD`, `RUN`, `1 SWDIO 3 GND 5 GND 7 SWCLK` and `2 V3V3 4 RUN 6 NC 8 NC` | as designed; the CAM's own legend layer was not read item by item |
| Stackup | no stackup in the ODB++ job; the parameters name none (`customLaminatedConstructionFlag` false) | as ordered (section 2): JLCPCB's default, not JLC04161H-7628 by name |
| Mask, legend, finish | mask **green** (绿), legend white (白色), leaded HASL (有铅喷锡), vias plugged with ink (过孔塞油) | as ordered. On 2026-11-20 the user said the board was meant to be **black** (「PCBの色なんだけど黒予定だったな」); no decision recorded black before the order (section 2: "no decision recorded them"). In Live Chat on 2026-11-20, about 17:03-17:30 JST, JLCPCB support first raised a $0.00 engineering-fee supplement for black (account message of 17:11:25), then answered that an Economic 4-layer order supports green mask only and the order cannot change to black; the user replied that it stays green. On 2026-11-21 the user decided on green (「緑で進めることにした」). The order's parameters still read green, white |
| Copper, thickness, impedance | outer 1 oz, inner 0.5 oz, 1.6 mm, impedance test not needed | as ordered |

One more download than approved: the first attempt to open the item's "Production file" link, before the
user's 「読んでいい」, downloaded the same zip (same SHA-256) into the user's Downloads folder; it and two later
copies were moved or deleted the same day.
