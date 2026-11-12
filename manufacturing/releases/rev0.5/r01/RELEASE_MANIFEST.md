# USB Power-Control Hub Rev0.5, release candidate r01

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** r01 is the first candidate of Rev0.5
> (issues #8 and #10): the four USB-C connectors J1-J4 are machine-placed receptacles, C2765186 (D37), and the
> data lines of OUT A and OUT B are tapped through 1 kΩ to RP2040 GPIO26-29 (D38). The JLCPCB gate (JLCDFM,
> part mapping, placement preview, quote) has **not run on it**: it needs the user's sign-in. It becomes
> orderable only after the user's approval and the gates in "Open gates" (CLAUDE.md 3, 8, 12). Rev0.4's r01 and
> r02 are superseded by it: its copper, BOM and CPL are not theirs.

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.5, r01 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` |
| Source revision | the sources whose SHA-256 is below, committed together with this directory (`git log -- manufacturing/releases/rev0.5/r01`), with the scripts that wrote them (`make_project.py`, `route.py`, `make_pcb.py`, `check_routing.py`, `make_outputs.py`) and the router session in `design/ecad/routing/` |
| Set written | 2026-11-13 (JST) by `make_outputs.py`; the ten `UsbPowerHub_Main_Rev0.5_*` files are byte-identical to `manufacturing/working/rev0.5/`, which `check_outputs.py` passed (2933 checks) |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27); D37 removed the modules and headers that made it pointless, which reopens the question, and the user decides it at the JLCPCB step with a fresh quote (CIRCUIT_DESIGN_Rev0.5.md §9) |
| Finish | leaded HASL (D30; board setting `HAL SnPb`) |
| Via class | every via 0.30 mm hole: JLCPCB's standard class "0.3mm/(0.4/0.45mm)" (issue #8), no 0.25 mm drill |
| Solder mask, silkscreen colour | not decided; no decision records them |
| Assembly side | Top only (REQ-MFG-01) |
| Quantities | 5 boards, 2 assembled (the cost estimate; no quote exists for Rev0.5) |
| Machine-placed parts | 262 footprints, 41 LCSC parts; Extended: C2040, C2765186, C5137013 (D29, D31, D37) |
| Hand-soldered parts | 8 (`UsbPowerHub_Main_Rev0.5_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.5_ERC.json`) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.5_DRC.json`), including JLCPCB's hole figures as custom rules |
| JLCPCB DFM, part mapping, placement preview | **not run on r01.** Rev0.4's review (`../../rev0.4/r01/JLCPCB_REVIEW.md`, r02's beside it) saw other files and does not carry over |
| Quote | none. The cost estimate prices Rev0.5 against Rev0.4 r02's quote: `design/experiments/cost-estimate/README.md`, "Rev0.5 against r02" |
| Sourcing | `SOURCING_CHECK.md` (c2a5455389db... is the BOM it was run on), PASS on 2026-11-13; repeated before payment |
| EasyEDA import (D32) | `../../rev0.4/r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in; not run on Rev0.5 |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## What changed against Rev0.4's r02

| File | Against Rev0.4 r02 |
|---|---|
| `UsbPowerHub_Main_Rev0.5_BOM_JLCPCB.csv` | C11702: 21 to 25 (+R35 R36 R37 R38); C2765186: 0 to 4 (+J1 J2 J3 J4) |
| `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | the same parts at new places, the receptacles at the board edges, the four taps; 22 parts around U1 stand 0.4-0.8 mm further out (`design/ecad/PLACEMENT_Rev0.5.md`, *Deviations*) |
| `UsbPowerHub_Main_Rev0.5_HandSolder.csv` | J1-J4 (the Akizuki modules) and their headers are gone; the hand-soldered parts are the eight of the list |
| `UsbPowerHub_Main_Rev0.5_Gerber.zip` | new copper and drill: the receptacles' pads, the four plated shell slots of each (the PTH drill file) and the two NPTH pegs; the routing is the session's plus the 259-row patch of `design/ecad/ROUTING_Rev0.5.md`, with 405 vias at 0.30 mm |

## Files

| File | Content |
|---|---|
| `UsbPowerHub_Main_Rev0.5_Assembly_Top.pdf` | assembly drawing |
| `UsbPowerHub_Main_Rev0.5_BOM_JLCPCB.csv` | JLCPCB BOM of the machine-placed parts, one row per LCSC code |
| `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | JLCPCB placement list, board frame, mm, degrees counter-clockwise; the receptacle's angle is KiCad's alone (no entry in `design/ecad/jlcpcb_model_rotation.json`) |
| `UsbPowerHub_Main_Rev0.5_DRC.json` | kicad-cli DRC report with schematic parity, every severity |
| `UsbPowerHub_Main_Rev0.5_ERC.json` | kicad-cli ERC report, every severity |
| `UsbPowerHub_Main_Rev0.5_Gerber.zip` | Gerbers (Protel extensions), Excellon drill files and drill maps; origin = the board's lower-left corner |
| `UsbPowerHub_Main_Rev0.5_HandSolder.csv` | the parts the user solders by hand (D13) |
| `UsbPowerHub_Main_Rev0.5_Preview_Bottom.png` | 3D render, bottom |
| `UsbPowerHub_Main_Rev0.5_Preview_Top.png` | 3D render, top |
| `UsbPowerHub_Main_Rev0.5_Schematic.pdf` | the schematic, every sheet |
| `SOURCING_CHECK.md` | the stock and class of every BOM line at JLCPCB and of every hand-soldered part at Akizuki, 2026-11-13 |
| `SHA256SUMS.txt` | SHA-256 of every file above; `sha256sum -c SHA256SUMS.txt` |

The ECAD source is not copied here: it is tracked in `design/ecad/source/` and identified by the hashes below;
copy it in at approval.

## Sources

| File | SHA-256 |
|---|---|
| `design/ecad/source/adc.kicad_sch` | `f9b0a957307a4022e13ccd06d34c85886a95fa8835e8817a52ee3ebc6c5bbe25` |
| `design/ecad/source/channel_a.kicad_sch` | `780530fdb71fef229ef4818ed8f745a041a1e7c038866ef5c6d9a8b6229be78e` |
| `design/ecad/source/channel_b.kicad_sch` | `d256ca3cf38c383fa885e8173edbf675d70f26a019a0449b0a54de439a1002bc` |
| `design/ecad/source/hub.kicad_sch` | `30a7596158320ae8349c183ed6c82ef655cd9adfc1a3ee3f950bc084b8c29e65` |
| `design/ecad/source/mcu.kicad_sch` | `477b919bdfde028e28721c7ee8f6f88a9968e2a3698a9dfcb34c5fcde015ce1b` |
| `design/ecad/source/power.kicad_sch` | `ff87065408e47146b6583c1146b5ee2763a836d3f1db241919ff57246ec80ee5` |
| `design/ecad/source/usb-power-hub.kicad_dru` | `0eb695361c6ea3b2486ae65fb340897cb3e36312ce58b77c25db4fbd5cfa2e8a` |
| `design/ecad/source/usb-power-hub.kicad_pcb` | `52cfe1e8a1ca30f779a392175161e5f01073e26d844880a258cea72947a2507a` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `549dcaf43c7faff12ebdd68f0a309c870dd74462f670a853985e89809b48326d` |

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| JLCDFM on r01's Gerber | **not run** (needs the sign-in); the via ring is 0.075 mm, inside JLCPCB's figure for the standard class, below the 0.1 mm at which JLCDFM flagged Rev0.4's r01 | user signs in to JLCDFM, then Claude |
| Part mapping and placement preview, with the receptacle's CPL angle | **not run**: C2765186 is new to the gate and has no entry in `jlcpcb_model_rotation.json`; the preview must be read for it before an order | user signs in, then Claude |
| The quote of Rev0.5's BOM and CPL, with the third Extended feeder fee and the impedance-control option | **none** | user, at the JLCPCB step |
| EasyEDA import (D32) | blocked at the user's sign-in | user |
| The open issues of CLAUDE.md 11 | OI-1, OI-5, OI-6, OI-8 (panelization), OI-26 and OI-33 stand | user (built board, real cables) |
| User approval before any order or payment | not given | user |

## Residual risks

- The CPL's origin is the board's lower-left corner and its angles are KiCad's plus the
  JLCPCB model rotation of design/ecad/jlcpcb_model_rotation.json (easy-stick 14.18). That
  table holds what Rev0.4's placement preview of 2026-11-11 showed
  (manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md). The receptacle C2765186 (J1-J4)
  is not in it: its CPL angle is KiCad's alone, and nobody has seen how JLCPCB's model sits
  on the footprint. The preview must be read for it before an order, and JLCPCB checks the
  final placement again in its DFM Analysis 4-6 hours after one.
- The receptacle's land is the maker's, drawn for a 0.80 mm board; this one is 1.6 mm
  (OI-33). Whether the shell legs reach through the plated slots and the joints carry the
  plug's insertion force shows only on the first board (V-MFG-03, V-MECH-01).
- JLCDFM's Danger items of Rev0.4's r01 (via annular ring, THT-to-SMD distance, mask opening
  exposing a trace, silkscreen over a plugged via) are judged in that review. It ran on the
  0.25 mm via drill; the 0.30 mm drill (issue #8) leaves a 0.075 mm via ring, which JLCDFM
  has not seen, and it has not seen the receptacles. JLCPCB's own DFM at order time can differ.
- No footprint is proven on a board; no order-time stock check has been done (CLAUDE.md 0).
- The open issues of CLAUDE.md 11 stand; the set is not orderable until each is closed.
- The receptacle's GND pads A1 and B1 are 0.035 mm shorter than the maker's land (the user's choice, D37), so
  that each NPTH peg keeps 0.200 mm from copper; the joint area under the plug's force is slightly smaller.
- The data-line taps (D38) are 1 kΩ stubs on the D+ and D- of OUT A and OUT B, an exception to CLAUDE.md 5.3
  "No stubs"; whether they cost High-Speed eye margin at the receptacle land is OI-26's, and the fallback is
  that devices enumerate at Full-Speed.
- The L2 plane is checked in the 2-D fill KiCad writes (`check_routing.py` rule 9), not in the return currents:
  a void shorter than 3.0 mm still lengthens a return path. After the routing patch U1's exposed pad keeps
  1.65-1.80 mm of plane copper on its sides, against rule 9's 1.60 mm.
- The router's session left 16 connections and 11 D36 places open, and a 259-row patch of
  `design/ecad/ROUTING_Rev0.5.md` (*After the router*) closes them; the programs that wrote the patch are
  scratch tools outside the repository, and a new session needs a new patch. Some joined nets run long: V_INJ
  87.9 mm, the buttons' and LEDs' lines 78.9-91.0 mm, the four taps 102.9-110.6 mm. `check_routing.py` has no
  length rule, and what the taps' wire capacitance does to a 12 Mbit/s edge is not computed.
- The sourcing check is of 2026-11-13 and the stock moves; the third Extended feeder fee is in no quote.
- Nothing has been built or measured. The open issues of CLAUDE.md 11 stand; the set is not orderable until each is closed.
