# USB Power-Control Hub Rev0.4, release candidate r01

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** This is the set assembled for the
> pre-order review (issue #6): it is what would be uploaded, with the JLCPCB review that was made on it.
> It becomes orderable only after the user's approval and the gates in "Open gates" (CLAUDE.md 3, 8, 12).

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.4, r01 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro` |
| Source revision | `design/ecad/source/` and `design/ecad/libraries/` last changed in Git commit `7fca00e66d21fcb9f5008167c050045849b66aa9` (2026-11-06 09:01 +09:00) and unchanged since; the SHA-256 of each source file is below. The scripts that wrote this set (`design/ecad/scripts/make_outputs.py`, `check_outputs.py`) and `design/ecad/jlcpcb_model_rotation.json` are in the commit that adds this directory (`git log -- manufacturing/releases/rev0.4/r01`) |
| Set written | 2026-11-12 (JST); `make_outputs.py` run twice gives the same `SHA256SUMS.txt` |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27) |
| Finish | leaded HASL (D30) |
| Via class | 0.25 mm hole / 0.45 mm pad; JLCPCB's form offers Plugged covering at $0.00 (Tented greyed out) |
| Solder mask, silkscreen colour | not decided; the quote used JLCPCB's form defaults, green and white |
| Assembly side | Top only (REQ-MFG-01); Economic PCBA |
| Quantities | 5 boards, 2 assembled (the quote and the cost estimate) |
| Machine-placed parts | 254 footprints, 40 LCSC parts; Extended: C2040, C5137013 (D29, D31) |
| Hand-soldered parts | 12 (`UsbPowerHub_Main_Rev0.4_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.4_ERC.json`) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.4_DRC.json`) |
| JLCPCB DFM, part mapping, placement preview | reviewed 2026-11-11/12: `JLCPCB_REVIEW.md` (JLCDFM: every Danger and Warning item listed one by one with a judgement, the unexplained ones marked; part mapping 40 of 40, 0 substituted; placement read per class). Holds only while the Gerber, BOM and CPL SHA-256 in `SHA256SUMS.txt` are the ones recorded there |
| Quote | $81.85 without shipping (5 boards, 2 assembled), lead time PCB 3 days + assembly 3-4 days; `JLCPCB_REVIEW.md` section 6 |
| Sourcing | `SOURCING_CHECK.md`, PASS on 2026-11-12; repeated before payment |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

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
| `JLCPCB_REVIEW.md` | the JLCPCB quote, DFM, part-mapping and placement review |
| `SOURCING_CHECK.md` | V-MFG-02 stock check |
| `EASYEDA_IMPORT.md` | the EasyEDA import (D32): blocked at the user's sign-in |
| `SHA256SUMS.txt` | SHA-256 of every file above; `sha256sum -c SHA256SUMS.txt` |

The ten `UsbPowerHub_Main_Rev0.4_*` files are byte-identical to what `make_outputs.py` writes into
`manufacturing/working/rev0.4/`; `check_outputs.py` checks that set. The ECAD source is not copied here:
it is tracked in `design/ecad/source/` and identified by the hashes below; copy it in at approval.

## Sources

| File | SHA-256 |
|---|---|
| `design/ecad/source/adc.kicad_sch` | `665d93645ced9be77a655755c35c0693ef3d497f01e9ffadae6c7cad0c6e2ac8` |
| `design/ecad/source/channel_a.kicad_sch` | `6ffe3eb2eeba7f5d9ec86e681c436387cba2d63c5c6c73b97a5c5dbae2a5ec0d` |
| `design/ecad/source/channel_b.kicad_sch` | `8db73937fe1b96242c3295f953eb8c777829661a1dd7976309e533202f041c8e` |
| `design/ecad/source/hub.kicad_sch` | `0695ff404a853574ec9be26106195e3dd3b927b90fcf00e095326f61994a2760` |
| `design/ecad/source/mcu.kicad_sch` | `9845c611eb8f1b0c1de71c1874be540bf9300c9c1f093858b49f9b7b59c32fc8` |
| `design/ecad/source/power.kicad_sch` | `7b544303b18c02a25a65bc165ff63195e48126c6e934de571defb1d9e99ebb3e` |
| `design/ecad/source/usb-power-hub.kicad_pcb` | `4b1dcc686683a6e00482709415745872660ee27a6380417c1eeab2e744677db9` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `03a1889469324d4b5c22b3317d7f91ec655875c017946a9beeb40d46b0b4a6b1` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `ad2fbb70358eae31558f01c830c2dbc5dcdd6f42f34bb461a837e491c62904d1` |

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| User approval before any order or payment | not given | user |
| OI-1: two USB-C plugs side by side (module pitch >= 20 mm) | open until checked with real cables (V-MECH-01) | user, with a built board |
| OI-5: fastening, heat-set M2 inserts at 4 corners | open until built and checked (V-MECH-01) | user, with a built board |
| OI-6: silkscreen below fab minimum | not closed in CLAUDE.md 11: `check_silk.py` passes against JLCPCB's legend limits, but the legend was not reviewed in JLCPCB's manufacturing preview, and the DFM warns on the 0.15 mm line width | Claude, after the user decides |
| OI-8: not testable | fiducials (3) and the SWD pads exist; **panelization is still undefined** (the quote is "single PCB") | user decides, then Claude |
| OI-26: HS signal integrity through the modules | unverified until a board exists (V-HOST-01); FS is the fallback | bring-up |
| Mechanical gate: outline, holes, connector openings from one source | **no `design/mechanical/` exists**; print process (FDM or MJF) not chosen | user decides, then Claude |
| Enclosure fit against a real USB-C cable | not done | user |
| Differential impedance computed against JLC04161H-7628 | **not done**: D27's W 0.31 / S 0.15 mm is a model value; JLCPCB's differential calculator returned no result on 2026-11-03 and was not rerun | Claude |
| DFM items not explained: mask opening exposing a trace (4 Danger, 13 Warning), negative mask expansion (18), silkscreen to pad (2), fiducial (3), trace spacing (25) | see `JLCPCB_REVIEW.md` section 4; JLCPCB's own DFM after an order may differ | Claude, then JLCPCB's post-order DFM |
| 0.25 mm via class adds $34.16 (Kelvin test + minimum via fee) | decision pending (accept, or move to a 0.30 mm class: a new revision) | user |
| Confirm Parts Placement ($0.45) off; shipping method and price; material TG135 or Tg155; solder paste "High temp." with leaded HASL | to confirm in the cart before paying | user |
| EasyEDA import (D32) | blocked at the user's sign-in and terms prompt (`EASYEDA_IMPORT.md`) | user signs in, then Claude |
| Prototype or first-article evidence | nothing built or measured | bring-up |
| Stock check at order time, and again before payment | done 2026-11-12 only | Claude, immediately before payment |

## Residual risks

- The placement was read in JLCPCB's viewer for every oriented part class after the origin and model-rotation
  fixes; JLCPCB checks the final placement again in its DFM Analysis 4-6 hours after an order, and the
  viewer is JLCPCB's model, not the physical part (easy-stick 14.18).
- JLCDFM ran on the Gerber made before the origin fix; the final one differs by a pure translation
  (`JLCPCB_REVIEW.md` section 4). Its Danger items (0.25 mm via annular ring at exactly 0.1 mm, THT-to-SMD
  distance, silkscreen over plugged vias, same-net via-to-pad spacing) are judged there, not removed.
- No footprint is proven on a board; nothing has been built or measured.
- The open issues of CLAUDE.md 11 stand (OI-1, OI-5, OI-6, OI-8, OI-26); the set is not orderable until each
  is closed with evidence.
- The shipping cost of the PCBA parcel is unknown, so the landed cost is not known (the quote is $81.85 without it).
- X-ray inspection of the two leadless parts (RP2040 LQFN-56, CH335F QFN-28) may be charged per board; it is
  not in the quote.
