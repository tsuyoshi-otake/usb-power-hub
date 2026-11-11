# JLCPCB review of release candidate r02 (issue #8)

**Nothing was ordered and nothing was paid.** The user's JLCPCB session was still signed in; Claude uploaded
r02's Gerber to the quote form, read it, and saved nothing to the cart. The upload creates an auto-saved draft
under My Account > Projects > Quotes, as r01's did.

This review records only what r02 changes. Everything else is r01's review (`../r01/JLCPCB_REVIEW.md`), which
holds for r02 where the files are byte-identical.

| Item | Value |
|---|---|
| What was reviewed | `UsbPowerHub_Main_Rev0.4_Gerber.zip` of this directory |
| Date | 2026-11-12, 03:38 to 03:41 (JST) |
| Validity | holds only while the Gerber SHA-256 below is unchanged |

| Uploaded file | SHA-256 |
|---|---|
| `UsbPowerHub_Main_Rev0.4_Gerber.zip` | `ff1dc4cd79faaa912c23e2927b94a077557647d4b75f50c1994d5a84b9ff3d30` |

Evidence is kept outside the repository, in `~/tmp/usb-power-hub/cost-down/jlcpcb/`:
`r02-via-class-1794422288548-171.jpg` (the form right after the upload),
`r02-material-stackup-1794422438715-172.jpg` and `r02-stackup-via-1794422467082-174.jpg` (after the stackup
was named), and, for the comparison by hand on a fresh form, `screenshot-1794419899783-167.jpg` (0.25 mm class,
$45.65) and `screenshot-1794419963795-169.jpg` (0.3 mm class, $8.00).

## 1. The form with r02's Gerber

| Option | JLCPCB form | r01's form | Verdict |
|---|---|---|---|
| Detected board | "4 layer board of 72x100mm" | the same | match |
| Min via hole size/diameter | **0.3mm/(0.4/0.45mm)**, the form's default, left as it was | 0.25mm/(0.35/0.4mm), selected by hand to match r01's 0.25 mm vias | the standard class; r02's smallest hole is 0.30 mm, so this is the class to order |
| Via covering | Plugged, $0.00 (Tented greyed out) | the same | unchanged |
| Material type | FR4 TG135 | FR4 TG135 shown, but the 0.25 mm class's notice said FR4 Tg155 is selected automatically (unresolved) | TG135, no notice to resolve |
| Stackup | "Specify Stackup: Yes", JLC04161H-7628, set by hand as in r01; the price stayed $8.00 | the same | match (D27) |
| Surface finish, copper, thickness | HASL (with lead); 1 oz / 0.5 oz; 1.6 mm | the same | match |

The form does not show that it read the via size from the Gerber: a fresh form with no Gerber also shows the
0.3 mm class at $8.00 (`screenshot-1794419963795-169.jpg`). What is shown is that the class r02 needs carries
neither fee: with the 0.25 mm class, which r01's vias needed, the form adds both lines by itself.

## 2. Price

| Line | r01 | r02 | Difference |
|---|---:|---:|---:|
| PCB, "Special Offer" (4 layers, 5 boards) | 8.00 | 8.00 | 0.00 |
| 4-Wire Kelvin Test | 17.02 | — | **−17.02** |
| Min via hole size/diameter | 17.14 | — | **−17.14** |
| Via covering, surface finish, build time 3-4 days | 0.00 | 0.00 | 0.00 |
| PCBA lines (setup, stencil, 40 components, Extended fee, SMT, nitrogen reflow) | 39.69 | 39.69, carried over | — |
| **Total without shipping** | **81.85** | **47.69** | **−34.16** |

The PCBA lines were not quoted again: the BOM and CPL are byte-identical to r01's, and the price of a part
does not depend on the via drill. Shipping, read on the same form: DHL Express $17.67 (the default) for the
0.24 kg PCB-only parcel, as for r01; the assembled parcel is priced only in the cart.

At 160 yen/USD with OCS Express ($7.23): $54.92, 8,787 yen; with the Akizuki parts (7,695 yen), 16,482 yen for
2 units, against 21,950 yen with r01 (`design/experiments/cost-estimate/README.md`).

## 3. What still holds from r01, and what does not

| r01 section | For r02 |
|---|---|
| 1. Defects found (BOM rows, Gerber origin, model rotation) | fixed in the generator; r02 is written by it |
| 3. Part mapping, 40 of 40 | holds: the BOM is byte-identical |
| 4. JLCDFM | **does not hold for the drill.** The vias' ring is now 0.075 mm, JLCPCB's preferred figure for this class (via pad 0.15 mm larger than the hole), but below the 0.1 mm at which JLCDFM flagged r01's vias. JLCDFM says via results of its annular-ring check may be ignored. It needs the user's sign-in to run again. The other items concern copper, mask and silkscreen, which are unchanged |
| 5. Placement preview | holds: the CPL is byte-identical, and the preview places parts on Top copper that did not change |
| 6. Price | replaced by section 2 above |
| 8. Decisions for the user | the via-class decision is closed by r02; the others stand |

## 4. Left in the user's account

- One more auto-saved quote draft (r02's Gerber) under My Account > Projects > Quotes, beside r01's. It can be
  deleted with "..." > Delete. Its draft ID is account data and is not recorded here.
- The cart icon showed 1 item before this upload. This review added nothing to the cart.
