# JLCPCB review of release candidate r02 (issues #8 and #10)

**Nothing was ordered and nothing was paid.** The user signed in to JLCPCB and JLCDFM themselves; Claude read the
pages and uploaded the files below to the quote form and to JLCDFM. SAVE TO CART was not clicked, no terms or
consent were accepted, and "Confirm Parts Placement" was left at No.

This is Rev0.5's first pass through the gate. It ran on r01's files and found two defects (section 1); r02 is r01
with both fixed. The second JLCDFM run and the refresh of the PCB quote used r02's Gerber; the placement preview
and the PCBA price used r01's Gerber with r02's CPL. r01's own record is `../r01/JLCPCB_REVIEW.md`.

| Item | Value |
|---|---|
| What was reviewed | `UsbPowerHub_Main_Rev0.5_Gerber.zip`, `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv` of this directory, and r01's Gerber and CPL (the files r02 replaced) |
| Dates | 2026-11-13, 08:06 to 09:46 (JST) |
| Validity | holds only while the three SHA-256 of this directory's files below are unchanged; any regenerated file needs a new review |

| Uploaded file | SHA-256 | Where, when (JST) |
|---|---|---|
| r02 `UsbPowerHub_Main_Rev0.5_Gerber.zip` | `41af84dc911364b14808d185179c80a4babfd0f7c71122c264821f89236ec30c` | JLCDFM 09:23; quote form 09:38 (the working copy, which the regeneration of 09:41 reproduced byte for byte) |
| `UsbPowerHub_Main_Rev0.5_BOM_JLCPCB.csv` (r01's is the same file) | `c2a5455389db1466c1e59f17ba812988152e44c914a6735a808e96efce9d7b06` | quote form 08:11 |
| r02 `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | `cd02c0990b34bf9fc7f8f2976b0d2d4a16d7ab786b2ca535d85445f9b626b130` | quote form 08:39 (the "trial CPL") |
| r01 Gerber | `7e84abc46af35c1a4dafaaec45791a2ebd52a84bcf4c919087e2f3e7d2fe87ce` | quote form 08:07; JLCDFM 08:59 |
| r01 CPL | `5316b10fe821ed8d6abbcfa8333f3f9bcbb18fbb348d67447f2293786e8ca623` | quote form 08:11, replaced at 08:39 |

Evidence is kept **outside the repository**, in `~/tmp/usb-power-hub/rev05-gate/evidence/`: `jlcdfm-statistics.txt`
(both JLCDFM runs), `uploads.txt` (the table above with the form's state) and `scripts/` (the measuring scripts
and their output, `gate_measure.out` and `gate_measure2.out`). Screenshots of the placement preview and of the
quote form were **not saved to disk**: what they showed is recorded below from the session. Account data (draft
and upload IDs) is not recorded anywhere.

## 1. Defects the gate found (both fixed in r02)

| # | Defect | Found by | Fix | Where it lives now |
|---|---|---|---|---|
| 1 | JLCPCB places its own model of the receptacle C2765186 at the CPL point, and the model sat about 1.375 mm toward the receptacle's mouth from the footprint's body centre, at the right orientation (r01's CPL held KiCad's origin and angle alone). | the placement preview of r01's CPL | The model table gained a second field, `shift`: [dx, dy] in the footprint's own frame, added to the footprint's origin for the CPL's Mid X/Y. C2765186 has [0.0, -1.375]. In the CPL, J1 and J4 moved from Mid Y 69.385 to 68.010 mm and J2 and J3 from 2.615 to 3.990 mm; nothing else in the CPL changed (262 rows compared). The table was `jlcpcb_model_rotation.json` and is now `jlcpcb_model_frame.json`. | `design/ecad/jlcpcb_model_frame.json`, `make_outputs.py`, `check_outputs.py` (it fails an entry no BOM line uses, an entry with neither field, an `add` that is not a quarter turn and a shift past its limit) |
| 2 | Eight GND fanout vias, one beside the rear plated shell slot of each contact pad A1 and B1 of J1-J4, stood 0.046 mm from that slot's hole: the board keeps 0.25 mm between a via's hole and a pad's hole, and JLCDFM's Danger limit is 0.18 mm. | JLCDFM run 1: "Plated through-hole spacing" 8 Danger | The 8 vias and their stubs are deleted, and each stub is drawn again from its contact pad into the slot's pad, ending 0.05 mm inside the ring (patch stage 5 of `ROUTING_Rev0.5.md`, 275 rows, r01's had 259). r02 has 397 vias, r01 had 405. | `design/ecad/ROUTING_Rev0.5.md`, `check_routing.py` rule 10 |

Root cause of 2: the router's search reads an oblong pad hole as a round hole at the pad's centre (`route.py`,
`_Copper`), and KiCad's DRC did not report these 8 (0 violations on r01). Rule 10 of `check_routing.py` now
measures every pair of drilled holes with a slot as a capsule (via to via 0.20 mm, pad to pad 0.45 mm, via to pad
0.25 mm) and was negative-tested against deliberately placed vias (`test_check_routing.py`, `HoleGapTest`).
`route.py`'s search was not changed (only its docstring), because a different input would no longer match the
committed router session; the next router session must read the slot as a capsule and drop stage 5
(`ROUTING_Rev0.5.md`, *GND fanout*).

What differs between r01 and r02, compared member by member: of the Gerber's 15 members, 9 are byte-identical and
6 differ (`F_Cu`, `In1_Cu`, `In2_Cu`, `B_Cu`, `PTH.drl` with 405 → 397 hits of the 0.300 mm tool, and its map);
the 16 plated slot hits (0.600 mm tool) and the NPTH file are unchanged. BOM, hand-solder list, schematic PDF,
assembly PDF, ERC and DRC reports are byte-identical; the two renders differ.

Not a new defect, repeated from Rev0.4: JLCPCB did not select the merged 510 Ω row (C17734, quantity 16)
by itself; it was ticked by hand after *Process BOM & CPL*.

## 2. Options JLCPCB's form took, against the manifest

Read on 2026-11-13, in the form with r01's Gerber (08:07 on) and again after r02's Gerber was uploaded (09:38).

| Option | JLCPCB form | Manifest / decision | Verdict |
|---|---|---|---|
| Base material, layers, size, quantity | FR-4, "4 layer board of 72x100mm", 5 boards, single PCB | D10, D24 | match |
| Thickness | 1.6 mm | 1.6 mm | match |
| Stackup | "Specify Stackup: Yes", JLC04161H-7628, set by hand in the first session, $8.00; the form of 09:38 was left at its default "No" and also showed $8.00 | D27, named on the order | match when named; name it on the order |
| Impedance control | No requirement | D27 (not ordered for the prototype) | match; decision for the user (section 8) |
| Surface finish | HASL (with lead) | D30 | match |
| Copper | outer 1 oz, inner 0.5 oz | outer 0.035 mm, inner 0.0152 mm | match |
| Via size class | 0.3mm/(0.4/0.45mm), the form's default; no 4-Wire Kelvin Test line, no minimum-via line | every via 0.30 mm hole (issue #8) | match |
| Via covering | Plugged, $0.00 | the board tents its vias; the form offers Plugged | as in Rev0.4 |
| Material type | FR4 TG135 | not in the manifest | confirm in the cart |
| Colour, silkscreen | form defaults, not changed | no decision records them | defaults taken |
| Assembly | Economic PCBA, Top only, 2 boards | D13, REQ-MFG-01 | match |
| Confirm Parts Placement | **No** ($0.00) | CLAUDE.md 4.2 asks for placement checking | **decision for the user** (section 8) |
| Build time | PCB 3-4 days, assembly 3-4 days | none | recorded |

The PCBA options showed solder paste "High temp." next to leaded HASL, as in Rev0.4. Not examined further;
confirm it in the cart.

## 3. Part mapping

- Bill of Materials tab, "Top Side": **41 parts detected, 41 parts confirmed**.
- The 41 matched LCSC codes equal the 41 codes of the BOM file one for one: **0 unmatched, 0 substituted**.
- Library type: 38 Basic, 3 Extended (C2040 RP2040, C5137013 CH335F, C2765186 receptacle; D29, D31, D37). No
  Preferred Extended.
- The receptacle's row shows quantity 11 for the 8 the two boards need. Not explained here; `design/experiments/
  cost-estimate/` budgeted 8 needed + 3 attrition from JLCPCB's `lossNumber`, which is the likely reason. Read
  the cart.

## 4. DFM (JLCDFM, PCB DFM check, signed in by the user)

Statistics are (Danger, Warning, Good); the page text is in `evidence/jlcdfm-statistics.txt`. **Run 1** analysed
r01's Gerber, **run 2** r02's. The two runs are identical in every item but one: "Plated through-hole spacing",
8 / 0 / 0 in run 1 and 0 / 0 / 0 in run 2 (defect 2). The table gives run 2's numbers.

JLCDFM lists only the first 50 results of each item per layer (not sorted across the board), so a count of 100
is a cap, and the rows read are samples. Measurements are on the KiCad board (`scripts/gate_measure.py`,
`gate_measure2.py`); JLCDFM's viewer is in the Gerber's frame (x = x_KiCad - 50 mm, y = 122 mm - y_KiCad). JLCDFM's
thresholds are its own and differ from JLCPCB's published capabilities (the slot row).

| Item | D / W / G | Judgement | Evidence |
|---|---|---|---|
| Plated through-hole spacing | 0 / 0 / 0 (run 1: **8** / 0 / 0) | Run 1's 8 are defect 2 (0.046 mm, Danger below 0.18 mm). Gone in run 2; `check_routing.py` rule 10 finds no via hole within 0.25 mm of a pad's hole. | run 1 and run 2; `check_routing.py` |
| Via to PTH spacing | 0 / 0 / 0 | clean | run 2 |
| **Slot width check** | **16** / 0 / 0 | The 16 are the plated shell slots of J1-J4 (4 each: 0.60 × 1.40 mm at the front, 0.60 × 1.70 mm at the rear; the maker's land, D37). JLCDFM's limits are Danger below 0.61 mm, Warning 0.61-0.81 mm, Good above 0.81 mm; JLCPCB's capabilities page (read 2026-11-13) gives a minimum plated slot width of 0.35 mm for multi-layer boards and a slot length of at least twice the width, which the slots meet. The two disagree and nothing was changed: **decision for the user** (section 8). | `jlcdfm-statistics.txt` |
| Annular ring | **100** / 0 / 0 | The rows are the 365 vias of 0.45 mm pad and 0.30 mm hole: ring 0.075 mm, under JLCDFM's Danger limit (0.1 mm) and exactly JLCPCB's preferred via pad, 0.15 mm larger than the hole. The dialog says via results of this check may be ignored. The 32 vias of 0.60 mm pad have a 0.150 mm ring, and all 58 plated pad holes (the 16 slots included) have at least 0.200 mm. | `gate_measure.out` M1 |
| THT to SMD | **50** / 0 / 0 | Concerns hand-soldering access (JLCDFM's limit is 2.03 mm). The through-hole footprints are the hand-soldered F1, RS11, RS21, U5, U7 and U17 (D13); JLCPCB machine-places SMD only. 55 pad pairs are closer than 2.03 mm; the closest is 0.62 mm (U7 pins 15 and 16 against C31 and C30). Not a machine-assembly defect; a soldering-iron reach to check by hand. | `gate_measure.out` M4 |
| Silkscreen to hole | **50** / 0 / 0 | 609 silkscreen items against 470 holes: every pair closer than 0.18 mm involves a **via** (123 pairs, 112 of them Danger, none near a pad hole or a receptacle slot). JLCDFM counts 271, which was not reconciled. The vias are plugged, so JLCPCB may clip the legend over one. | `gate_measure.out` M5 |
| Pad spacing | **6** / 11 / 44 | JLCDFM appears to read KiCad's rounded-rectangle pads as plain rectangles: with sharp corners the same measure reproduces its first row (C20 pad 1 against a V3V3 via: 0.05 mm sharp, 0.105 mm on the real shape). On the real shapes, 2 pad-to-via pairs are under 0.10 mm and 149 are 0.10-0.15 mm, **all on one net**; no pair on different nets is under 0.15 mm (DRC clearance 0.15 mm, 0 violations). Reproduced for the first row only; the 6 rows are not identified one by one. | `gate_measure.out` M2, `gate_measure2.out` M2b |
| Solder mask opening exposing trace | **3** / 12 / 40 | No track or via of another net lies within 0.15 mm of any mask opening (the closest is 0.152 mm: J1 pad B1 against a VBUS_J1 track). The 57 pairs under 0.08 mm and the 185 of 0.08-0.15 mm are a pad and a track or via of its **own** net. JLCDFM's three Danger rows (0.02, 0.04, 0.05 mm) were not identified one by one. | `gate_measure.out` M3, `gate_measure2.out` M3b |
| Negative soldermask expansion | 0 / **84** / 0 | The project's global mask expansion is 0 (`pad_to_mask_clearance`), so each opening equals its pad: intended. The rows read are 1.0 and 1.6 mm round through-hole pads. How JLCPCB's CAM treats it was not seen. | `jlcdfm-statistics.txt` |
| Plated through-hole to trace clearance | 0 / **40** / 60 | Warning by construction: hole radius, ring 0.075 mm and the 0.15 mm clearance make 0.225 mm. Measured: the closest plated hole to a track of another net is 0.227 mm (F.Cu and B.Cu), against JLCDFM's Danger limit of 0.18 mm; 46 Warning, 0 Danger. | `gate_measure2.out` M7 |
| Fiducial | 0 / **3** / 0 | Three fiducials, flashed at the board's positions as 1.0 mm copper with a 2.0 mm mask opening (`check_outputs.py`); JLCDFM lists all three as Warning for detection, not for geometry. | `check_outputs.py` |
| Trace spacing | 0 / **21** / 39 | The project minimum is 0.15 mm, equal to JLCDFM's Warning boundary. Measured per layer between nets: 0.150 mm on F.Cu, 0.152 mm on In2 and B.Cu; none under 0.15 mm. | `gate_measure.out` M6 |
| Silkscreen line width | 0 / **50** / 0 | 0.15 mm equals JLCDFM's Warning boundary and JLCPCB's minimum; CLAUDE.md 6 asks for at least 0.15 mm. | `jlcdfm-statistics.txt` |
| Silkscreen to pad | 0 / **2** / 48 | Not read. Residual risk. | `jlcdfm-statistics.txt` |
| All other items | 0 Danger, 0 Warning | sharp trace corner, BGA pad, via in pad, trace to board edge, unconnected trace end, trace width, pad to board edge, via to pad, mask bridge, multi-segment mask opening, unconnected and missing holes, short slot detection | `jlcdfm-statistics.txt` |

JLCPCB runs its own DFM again after an order (4-6 hours) and may differ from JLCDFM.

## 5. Placement preview (JLCPCB's 3D viewer, with r02's CPL)

Each class was selected in the part list and read for the model's pin-1 or polarity mark against the board's pin 1.
The classes are Rev0.4's, and their rotations in `design/ecad/jlcpcb_model_frame.json` are unchanged; every row
down to the switches was read again on 2026-11-13, the row of symmetrical parts was not, and the receptacle's row
is new. No screenshots were saved.

| Class (LCSC, designators) | CPL rotation | Verdict |
|---|---|---|
| RP2040 C2040, U1; crystals C9002, Y1 and Y2 | KiCad angle | model mark agrees with the board's pin 1 |
| CH335F C5137013, U6 | +270 | agrees |
| W25Q128JVSIQ C97521, U8 | +270 | agrees |
| OP07CDR C7433 and LM393DR2G C7955 | +270 | agrees |
| AMS1117-3.3 C6186, U2 | +180 | agrees |
| SOT-23: PSM712 C32677, AO3401A C15127, AO3400A C20917, 2N7002 C8545, S9012 C8543, CJ431 C3113 | +180 | agrees |
| LEDs D10-D13 | KiCad angle | "+" (anode) on pad 2 |
| TS-1187A SW1-SW3 | KiCad angle | four-pin switch, glanced at only |
| Resistors (the new taps R35-R38 included), capacitors, FB1, SMBJ6.5CA D5 and D6 | KiCad angle | symmetrical parts; Rev0.4's reading, **not read again** |
| **C2765186, J1-J4** | KiCad angle, **shift [0.0, -1.375]** | new class, see below |

The receptacle was read first with r01's CPL (the model sat about 1.375 mm toward its mouth, defect 1), then with
the shifted CPL. On all four receptacles the viewer then showed: front face **1.054 mm past the board edge**
(design 1.06 mm), contact tails centred 6.325 mm (J1, J4) and 6.34 mm (J2, J3) from the edge against the pad
row's centre at 6.285 mm, pegs 2.82 mm either side of the axis (design 2.89 mm); the four are alike. The reading
error is about 0.04 mm. This is the drawing of JLCPCB's model, not its pick-and-place, and the preview ran with
r01's Gerber in the form, whose copper differs from r02's only at the 8 vias and 8 stubs of defect 2. JLCPCB's own
check after ordering is the last word (CLAUDE.md 4.2).

## 6. Price, lead time, and the difference from the estimate

Read on 2026-11-13 (USD, the account's currency).

| Line | Value |
|---|---:|
| PCB, "Special Offer" (4 layers, 5 boards), with r02's Gerber at 09:38; no Kelvin test, no minimum-via line | 8.00 |
| **Total without shipping**, read with r01's Gerber and r02's BOM and CPL | **51.94** |
| PCBA lines (setup, stencil, 41 parts, Extended fees, SMT), by difference; read as a total, not line by line | 43.94 |
| Rev0.4 r02's quote, for comparison (`../../rev0.4/r02/JLCPCB_REVIEW.md`): total / PCBA lines | 47.69 / 39.69 |
| `design/experiments/cost-estimate/` predicted for Rev0.5: Rev0.4 r02 plus the order's gain | 47.69 + 4.11 = 51.80 |

- The real total is $0.14 above the estimate. r02's Gerber changes no option of the form and the PCBA lines do not
  read the Gerber, so $51.94 is expected to hold for r02; r02's own total was not read.
- Impedance control, if ordered: +$34.13 including the Confirm Production file fee (read on the form).
- Shipping to Japan: DHL Express $17.67, the form's default, for the 0.24 kg PCB-only parcel. OCS Express $7.23
  was read on 2026-11-12 (`../../rev0.4/r01/JLCPCB_REVIEW.md` section 6) and not read again. The assembled parcel
  is priced only in the cart.
- With OCS Express: $59.17, 9,467 yen at the planning rate of 160 yen/USD. With the Akizuki parts (4,790 yen, the
  estimate's figure): **14,257 yen for 2 units**, 7,129 yen per unit, against the estimate's 14,235 yen and
  Rev0.4 r02's 16,482 yen.
- Lead time shown: PCB 3-4 days, assembly 3-4 days, plus the carrier's.

## 7. What was not done, and what is left in the user's accounts

- No order, no payment, **SAVE TO CART not clicked**, no terms or consent accepted.
- JLCPCB auto-saved quote drafts under My Account > Projects > **Quotes** for the uploads of 08:07 and 09:38 (the
  list was not opened, so the count is not known). Remove each with its "..." menu > Delete. JLCDFM keeps the two
  uploads of 08:59 and 09:23 in its history.
- The cart's one item is the user's earlier easy-stick quote; it was not touched.
- One click on "My Account" opened the Order History page; nothing in it was read or changed.
- The EasyEDA import (D32) was not done: `../../rev0.4/r01/EASYEDA_IMPORT.md`.
- The stock check of `../r01/SOURCING_CHECK.md` (2026-11-13) holds, because the BOM is the same file; repeat it
  before payment.

## 8. Decisions for the user

1. **Slot width.** JLCDFM calls the receptacles' 0.60 mm plated slots Danger; JLCPCB's capabilities page allows
   0.35 mm. Accept and let JLCPCB's own DFM decide, or widen the slots, which means leaving the maker's land (a
   new revision).
2. **The 8 slot vias.** r02 deletes them and ties each contact pad's stub into the slot's pad; the alternative is
   a re-route of the neighbourhood with the slot read as a capsule. The first is done and checked (rule 10).
3. **Impedance control:** +$34.13 including the Confirm Production file fee; D37 removed the modules that made it
   pointless.
4. **Confirm Parts Placement:** off. CLAUDE.md 4.2 wants placement checked, and the receptacle's shift is a
   viewer measurement (about 0.04 mm); JLCPCB's DFM after the order checks the placement again.
5. **Shipping method:** DHL Express $17.67 (default) against OCS Express $7.23; the cart prices the real parcel.
6. **Material and paste:** confirm FR4 TG135 and "High temp." paste with leaded HASL in the cart.
7. **Receptacle quantity:** 11 shown for 8 needed; confirm in the cart what is bought and charged.
8. **Approval of r02, and its name:** approval is not given. r02 keeps the name Rev0.5 although its copper differs
   from r01's in 8 vias and 8 stubs, as Rev0.4's r02 did for its via drill (`RELEASE_MANIFEST.md`, *Why r02 and
   not a new PCB revision*); the strict reading of CLAUDE.md 2 would make it Rev0.6.
