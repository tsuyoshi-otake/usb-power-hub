# JLCPCB review of release candidate r01 (issues #8 and #10)

**Nothing was ordered and nothing was paid.** This is the short record of what the JLCPCB gate found in r01's files.
The full review (the second JLCDFM run, the placement preview, the quote, the decisions for the user) is
`../r02/JLCPCB_REVIEW.md`. **r01 is superseded by r02: do not order r01.**

| Item | Value |
|---|---|
| What was reviewed | r01's `UsbPowerHub_Main_Rev0.5_Gerber.zip`, `_BOM_JLCPCB.csv` and `_CPL_JLCPCB.csv` of this directory |
| Date | 2026-11-13 (JST), after this directory was committed |
| Validity | holds only while the SHA-256 in `SHA256SUMS.txt` are unchanged |

| Uploaded file | SHA-256 | Where, when (JST) |
|---|---|---|
| `UsbPowerHub_Main_Rev0.5_Gerber.zip` | `7e84abc46af35c1a4dafaaec45791a2ebd52a84bcf4c919087e2f3e7d2fe87ce` | quote form 08:07; JLCDFM (run 1) 08:59 |
| `UsbPowerHub_Main_Rev0.5_BOM_JLCPCB.csv` | `c2a5455389db1466c1e59f17ba812988152e44c914a6735a808e96efce9d7b06` | quote form 08:11 (r02's BOM is the same file) |
| `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | `5316b10fe821ed8d6abbcfa8333f3f9bcbb18fbb348d67447f2293786e8ca623` | quote form 08:11, replaced at 08:39 by r02's CPL |

## What the gate found in r01

| # | Defect | Found by | Fixed in r02 by |
|---|---|---|---|
| 1 | The receptacle C2765186 (J1-J4): JLCPCB places its own model at the CPL point, and the model sat about 1.375 mm toward the receptacle's mouth from the footprint's body centre, which is the point r01's CPL gives. | the placement preview of r01's CPL | a per-part `shift` in the model table `design/ecad/jlcpcb_model_frame.json`, added to the CPL's Mid X/Y: J1-J4's Mid Y moved 1.375 mm away from the mouth |
| 2 | Eight GND fanout vias, beside the rear plated shell slots of the contact pads A1 and B1 of J1-J4, stood 0.046 mm from the slots' holes (the board keeps 0.25 mm; JLCDFM's Danger limit is 0.18 mm). KiCad's DRC did not report them. | JLCDFM run 1: "Plated through-hole spacing" 8 Danger | the vias and their stubs are deleted and each stub is drawn again into its slot's pad (patch stage 5, `ROUTING_Rev0.5.md`); `check_routing.py` rule 10 measures every pair of drilled holes with a slot as a capsule |

## What held for r01 as it is

- Part mapping: 41 parts detected, 41 confirmed, 0 unmatched, 0 substituted (the BOM is r02's file).
- JLCDFM run 1 and run 2 (r02's Gerber) are identical in every item except "Plated through-hole spacing" (8, 0, 0
  against 0, 0, 0): the judgements of `../r02/JLCPCB_REVIEW.md` section 4 hold for r01's Gerber, defect 2 aside.
- The PCB price, $8.00 with the default 0.3 mm via class and no Kelvin or minimum-via line, and the total of
  $51.94 without shipping (read with r01's Gerber and BOM and r02's CPL).

## What was not done

No order, no payment, SAVE TO CART not clicked, no terms or consent accepted. The quote drafts the form
auto-saved and the JLCDFM uploads are listed in `../r02/JLCPCB_REVIEW.md`, section 7.
