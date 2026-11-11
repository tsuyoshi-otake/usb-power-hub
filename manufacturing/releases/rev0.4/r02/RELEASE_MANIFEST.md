# USB Power-Control Hub Rev0.4, release candidate r02

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** r02 is r01 with every via drilled at
> 0.30 mm instead of 0.25 mm (issue #8), so that JLCPCB prices the board in its standard via class. The copper,
> the BOM and the CPL are r01's. It becomes orderable only after the user's approval and the gates in
> "Open gates" (CLAUDE.md 3, 8, 12). **r02 supersedes r01: do not order r01.**

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.4, r02 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` (new in r02) |
| Source revision | the sources whose SHA-256 is below, committed together with this directory (`git log -- manufacturing/releases/rev0.4/r02`), with the scripts that wrote them (`make_project.py`, `route.py`, `make_pcb.py`, `make_outputs.py`) |
| Set written | 2026-11-12 (JST) by `make_outputs.py`; the ten `UsbPowerHub_Main_Rev0.4_*` files are byte-identical to `manufacturing/working/rev0.4/`, which `check_outputs.py` passed (2853 checks) |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27) |
| Finish | leaded HASL (D30) |
| Via class | **0.30 mm hole / 0.45 mm pad (334 vias) and 0.30 / 0.60 mm (22): JLCPCB's standard class "0.3mm/(0.4/0.45mm)"**. The form selected it from this Gerber and offers Plugged covering at $0.00 (Tented greyed out) |
| Solder mask, silkscreen colour | not decided; the quote used JLCPCB's form defaults, green and white |
| Assembly side | Top only (REQ-MFG-01); Economic PCBA |
| Quantities | 5 boards, 2 assembled (the quote and the cost estimate) |
| Machine-placed parts | 254 footprints, 40 LCSC parts; Extended: C2040, C5137013 (D29, D31) |
| Hand-soldered parts | 12 (`UsbPowerHub_Main_Rev0.4_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.4_ERC.json`, byte-identical to r01's) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.4_DRC.json`), now including JLCPCB's hole figures as custom rules: via hole to copper 0.20, via to via hole 0.20, PTH hole to copper 0.28, PTH ring 0.15, pad hole to pad hole 0.45 mm |
| JLCPCB DFM, part mapping, placement preview | part mapping and placement preview: r01's (`../r01/JLCPCB_REVIEW.md` sections 3 and 5), valid because the BOM and CPL are byte-identical; JLCDFM: **not run on r02** (open gate below); the via-class quote: `JLCPCB_REVIEW.md` |
| Quote | PCB $8.00 on r02's Gerber (no Kelvin test, no minimum-via fee); with r01's PCBA lines for the identical BOM and CPL, **$47.69 without shipping** (r01: $81.85). `JLCPCB_REVIEW.md` |
| Sourcing | `../r01/SOURCING_CHECK.md` (the same BOM, SHA-256 below), PASS on 2026-11-12; repeated before payment |
| EasyEDA import (D32) | `../r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## Why r02 and not a new PCB revision

CLAUDE.md §2 asks for a new PCB revision for any electrical, layout, footprint or mechanical change, so
that two physically different boards never carry one name. No Rev0.4 board exists: r01 was never ordered,
and nothing was built. The copper is r01's (below), including the silkscreen legend that prints `Rev0.4`;
only the via drill changes. A new revision would change that legend, and r02 would no longer be provably
r01's copper. r01 stays in Git unchanged, superseded by this set. If the user prefers the strict reading,
the change becomes Rev0.5: a silkscreen edit and a regeneration, about 30 minutes plus a 17-minute router run.

## What changed against r01

| File | Against r01 |
|---|---|
| `UsbPowerHub_Main_Rev0.4_Gerber.zip` | the drill: `PTH.drl` and its map; tool 0.250 mm (334 hits) is gone, tool 0.300 mm has 356 hits. `B_Cu.gbl` and `In2_Cu.g2` differ by zone-fill slivers, every one narrower than 6 µm (a 3 µm erosion removes them all; 0.00038 mm² on In2, 0.00010 mm² on B.Cu): KiCad's fill polygonises around a hole whose size changed. Every other member is byte-identical |
| `_BOM_JLCPCB.csv`, `_CPL_JLCPCB.csv`, `_HandSolder.csv`, `_Schematic.pdf`, `_Assembly_Top.pdf`, `_ERC.json`, `_DRC.json` | byte-identical |
| `_Preview_Top.png`, `_Preview_Bottom.png` | the renders show the larger holes |

The board itself was compared item by item with the one r01 was made from (Git `df5df08`): 2206 tracks,
356 via positions and pad diameters, and 300 footprints are identical. The router input differs only in the
via's name (`450:250` → `450:300`), and the new router session equals the old one with that name replaced.

## Files

| File | Content |
|---|---|
| `UsbPowerHub_Main_Rev0.4_Gerber.zip` | Gerbers (Protel extensions), Excellon drill files and drill maps; origin = the board's lower-left corner |
| `UsbPowerHub_Main_Rev0.4_BOM_JLCPCB.csv` | JLCPCB BOM of the machine-placed parts, one row per LCSC code |
| `UsbPowerHub_Main_Rev0.4_CPL_JLCPCB.csv` | JLCPCB placement list, board frame, mm, degrees counter-clockwise, with the JLCPCB model rotation of `design/ecad/jlcpcb_model_rotation.json` |
| `UsbPowerHub_Main_Rev0.4_HandSolder.csv` | the parts the user solders by hand (D13) |
| `UsbPowerHub_Main_Rev0.4_Schematic.pdf` | the schematic, every sheet |
| `UsbPowerHub_Main_Rev0.4_Assembly_Top.pdf` | assembly drawing |
| `UsbPowerHub_Main_Rev0.4_Preview_Top.png`, `_Preview_Bottom.png` | 3D renders |
| `UsbPowerHub_Main_Rev0.4_ERC.json`, `_DRC.json` | kicad-cli reports, every severity |
| `JLCPCB_REVIEW.md` | the via-class quote of r02's Gerber, and what of r01's review still holds |
| `SHA256SUMS.txt` | SHA-256 of every file above; `sha256sum -c SHA256SUMS.txt` |

The ECAD source is not copied here: it is tracked in `design/ecad/source/` and identified by the hashes below;
copy it in at approval.

## Sources

| File | SHA-256 |
|---|---|
| `design/ecad/source/adc.kicad_sch` | `665d93645ced9be77a655755c35c0693ef3d497f01e9ffadae6c7cad0c6e2ac8` |
| `design/ecad/source/channel_a.kicad_sch` | `6ffe3eb2eeba7f5d9ec86e681c436387cba2d63c5c6c73b97a5c5dbae2a5ec0d` |
| `design/ecad/source/channel_b.kicad_sch` | `8db73937fe1b96242c3295f953eb8c777829661a1dd7976309e533202f041c8e` |
| `design/ecad/source/hub.kicad_sch` | `0695ff404a853574ec9be26106195e3dd3b927b90fcf00e095326f61994a2760` |
| `design/ecad/source/mcu.kicad_sch` | `9845c611eb8f1b0c1de71c1874be540bf9300c9c1f093858b49f9b7b59c32fc8` |
| `design/ecad/source/power.kicad_sch` | `7b544303b18c02a25a65bc165ff63195e48126c6e934de571defb1d9e99ebb3e` |
| `design/ecad/source/usb-power-hub.kicad_dru` | `17288f0afbcbc08563d1b0f85728144b9fa73057c067cf40262dfe375c32099d` |
| `design/ecad/source/usb-power-hub.kicad_pcb` | `17991c589fe50840d24de14c37260c1cb34a5307710bab810e336b7f7e7e1ba7` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `ad2fbb70358eae31558f01c830c2dbc5dcdd6f42f34bb461a837e491c62904d1` |

## Open gates (CLAUDE.md 8 and 12), with owners

r01's open gates stand (`../r01/RELEASE_MANIFEST.md`), with these changes:

| Gate | State | Owner |
|---|---|---|
| 0.25 mm via class adds $34.16 | **closed by r02**: the Gerber is priced in the standard class | — |
| JLCDFM on r02's Gerber | **not run**. The via ring is now 0.075 mm, inside JLCPCB's own figure for this class (via pad 0.1 mm, 0.15 mm preferred, larger than the hole) but below the 0.1 mm at which JLCDFM flagged r01's vias | user signs in to JLCDFM, then Claude |
| Material type | the form shows FR4 TG135 selected with the r02 Gerber; r01's via class forced Tg155 | confirm in the cart |
| User approval before any order or payment | not given | user |

## Residual risks

- JLCDFM has not seen the 0.30 mm drill; JLCPCB's own DFM at order time can differ.
- The PCBA lines of the $47.69 are r01's quote for the identical BOM and CPL, not a new quote; prices and
  stock move, and are checked again before payment.
- r01's residual risks stand: the placement preview is JLCPCB's model, no footprint is proven on a board,
  nothing has been built or measured, the open issues of CLAUDE.md 11 stand (OI-1, OI-5, OI-6, OI-8, OI-26),
  the assembled parcel's shipping is priced only in the cart, and X-ray inspection of U1 and U6 may be charged.
