# USB Power-Control Hub Rev0.5, release candidate r02

> **State: WIP. Not approved, not ordered, MANUFACTURING PROHIBITED.** r02 is r01 after the JLCPCB gate
> (issues #8 and #10): the gate found two defects in r01 (`JLCPCB_REVIEW.md`, section 1), and r02 fixes both. Eight
> GND fanout vias that stood 0.046 mm from the receptacles' plated shell slots are gone, and the CPL places the
> receptacles where JLCPCB's model covers the footprint. The BOM is r01's. It becomes orderable only after the
> user's approval and the gates in "Open gates" (CLAUDE.md 3, 8, 12). **r02 supersedes r01: do not order r01.**

| Item | Value |
|---|---|
| PCB revision, release number | Rev0.5, r02 |
| State | WIP |
| ECAD | KiCad 9.0.8, project `design/ecad/source/usb-power-hub.kicad_pro`, with the custom rules `usb-power-hub.kicad_dru` |
| Source revision | the sources whose SHA-256 is below, committed together with this directory (`git log -- manufacturing/releases/rev0.5/r02`), with the scripts that wrote them (`make_project.py`, `route.py`, `make_pcb.py`, `check_routing.py`, `make_outputs.py`) and the router session in `design/ecad/routing/` |
| Set written | 2026-11-13 (JST) by `make_outputs.py`; the ten `UsbPowerHub_Main_Rev0.5_*` files are byte-identical to `manufacturing/working/rev0.5/`, which `check_outputs.py` passed (2970 checks) |
| Dimensions | 100 × 72 mm (D24), 1.6 mm thick |
| Layers | 4 (D10) |
| Stackup | JLC04161H-7628 (D27), named on the order |
| Copper | outer 0.035 mm (1 oz), inner 0.0152 mm (0.5 oz) |
| Impedance control | not ordered for the prototype (D27); the form offers it at +$34.13 including the Confirm Production file fee, and the user decides at the JLCPCB step (CIRCUIT_DESIGN_Rev0.5.md §9) |
| Finish | leaded HASL (D30; board setting `HAL SnPb`) |
| Via class | **397 vias, every hole 0.30 mm:** 365 of 0.45 mm pad (ring 0.075 mm) and 32 of 0.60 mm pad (ring 0.150 mm). JLCPCB's standard class "0.3mm/(0.4/0.45mm)", the form's default: no 4-Wire Kelvin Test line and no minimum-via line. The form offers Plugged covering at $0.00 |
| Solder mask, silkscreen colour | not decided; the form's defaults were not changed |
| Assembly side | Top only (REQ-MFG-01); Economic PCBA |
| Quantities | 5 boards, 2 assembled (the quote form) |
| Machine-placed parts | 262 footprints, 41 LCSC parts; Extended: C2040, C2765186, C5137013 (D29, D31, D37) |
| Hand-soldered parts | 8 (`UsbPowerHub_Main_Rev0.5_HandSolder.csv`), in neither BOM nor CPL |
| Not populated (DNP, BOM-excluded) | 34: FID1 FID2 FID3 H1 H2 H3 H4 J5 TP1 TP2 TP3 TP4 TP5 TP6 TP7 TP8 TP9 TP10 TP11 TP12 TP13 TP14 TP101 TP102 TP103 TP104 TP105 TP106 TP201 TP202 TP203 TP204 TP205 TP206 |
| ERC | 0 violations (`UsbPowerHub_Main_Rev0.5_ERC.json`, byte-identical to r01's) |
| DRC | 0 violations, 0 unconnected items, 0 schematic-parity items (`UsbPowerHub_Main_Rev0.5_DRC.json`), including JLCPCB's hole figures as custom rules; the slots as capsules are measured by rule 10 of `check_routing.py`, which KiCad's DRC does not do |
| JLCPCB DFM, part mapping, placement preview | **run on 2026-11-13**: `JLCPCB_REVIEW.md`. JLCDFM on this Gerber: Danger in 6 items, each judged there (via annular ring 100, THT to SMD 50, silkscreen to hole 50, pad spacing 6, mask opening exposing a trace 3, slot width 16), most of them JLCDFM's own reading of the geometry; the slot width is a decision for the user. Part mapping 41 of 41, 0 substituted. Placement preview read per class, the receptacle's shift read on all four |
| Quote | PCB $8.00 on this Gerber; **$51.94 without shipping**, read with r01's Gerber and this BOM and CPL (the PCBA lines were read as a total). `JLCPCB_REVIEW.md`, section 6 |
| Sourcing | `../r01/SOURCING_CHECK.md` (the same BOM, SHA-256 below), PASS on 2026-11-13; repeated before payment |
| EasyEDA import (D32) | `../../rev0.4/r01/EASYEDA_IMPORT.md`: blocked at the user's sign-in; not run on Rev0.5 |
| Firmware | none |
| JLCPCB order number | **none: nothing was ordered or paid** |
| Approver, approval time | **none** |

## Why r02 and not a new PCB revision

CLAUDE.md §2 asks for a new PCB revision for any electrical, layout, footprint or mechanical change, so that two
physically different boards never carry one name. No Rev0.5 board exists: r01 was never ordered, and nothing was
built. r02's copper differs from r01's in 8 vias and their 8 stubs (below), and both print `Rev0.5` on the silkscreen.
This is Rev0.4's precedent (r01 to r02 for a via drill, `../../rev0.4/r02/RELEASE_MANIFEST.md`). r01 stays in Git
with its data files unchanged, superseded by this set. If the user prefers the strict reading, the change becomes
Rev0.6: a silkscreen edit and a regeneration of the outputs.

## What changed against r01

| File | Against r01 |
|---|---|
| `UsbPowerHub_Main_Rev0.5_Gerber.zip` | 6 of its 15 members differ: `F_Cu`, `In1_Cu`, `In2_Cu`, `B_Cu`, `PTH.drl` and `PTH-drl_map`. The 8 GND fanout vias beside the receptacles' rear slots (contact pads A1 and B1 of J1-J4) and their stubs are gone, and each stub is drawn again into its slot's pad (patch stage 5, 275 rows against 259): 397 vias, not 405, so the 0.300 mm tool has 397 hits, not 405. The slots (0.600 mm tool, 16 hits) and the NPTH file are unchanged |
| `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | J1-J4 only, and only Mid Y: J1 and J4 69.385 to 68.010, J2 and J3 2.615 to 3.990, the JLCPCB model shift of `design/ecad/jlcpcb_model_frame.json` (1.375 mm away from the receptacle's mouth). The other 258 rows are byte-identical |
| `_BOM_JLCPCB.csv`, `_HandSolder.csv`, `_Schematic.pdf`, `_Assembly_Top.pdf`, `_ERC.json`, `_DRC.json` | byte-identical |
| `_Preview_Top.png`, `_Preview_Bottom.png` | the renders show the new copper |
| `JLCPCB_REVIEW.md` | new: the gate's record |
| `SOURCING_CHECK.md` | not copied: r01's holds, the BOM being the same file |

## Files

| File | Content |
|---|---|
| `UsbPowerHub_Main_Rev0.5_Assembly_Top.pdf` | assembly drawing |
| `UsbPowerHub_Main_Rev0.5_BOM_JLCPCB.csv` | JLCPCB BOM of the machine-placed parts, one row per LCSC code |
| `UsbPowerHub_Main_Rev0.5_CPL_JLCPCB.csv` | JLCPCB placement list, board frame, mm, degrees counter-clockwise; the receptacle's Mid Y carries its model shift (`design/ecad/jlcpcb_model_frame.json`) |
| `UsbPowerHub_Main_Rev0.5_DRC.json` | kicad-cli DRC report with schematic parity, every severity |
| `UsbPowerHub_Main_Rev0.5_ERC.json` | kicad-cli ERC report, every severity |
| `UsbPowerHub_Main_Rev0.5_Gerber.zip` | Gerbers (Protel extensions), Excellon drill files and drill maps; origin = the board's lower-left corner |
| `UsbPowerHub_Main_Rev0.5_HandSolder.csv` | the parts the user solders by hand (D13) |
| `UsbPowerHub_Main_Rev0.5_Preview_Bottom.png` | 3D render, bottom |
| `UsbPowerHub_Main_Rev0.5_Preview_Top.png` | 3D render, top |
| `UsbPowerHub_Main_Rev0.5_Schematic.pdf` | the schematic, every sheet |
| `JLCPCB_REVIEW.md` | the JLCPCB gate: defects found, form options, part mapping, JLCDFM, placement preview, price, decisions |
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
| `design/ecad/source/usb-power-hub.kicad_pcb` | `3205d4c42fe63b5acdec07c3e2959914dbbca246025d93fb2a04ccfc96125530` |
| `design/ecad/source/usb-power-hub.kicad_pro` | `18855e6bcff3b380e29a02d015d9cefb415c34bdfc1f93b9b75d02a17d05725a` |
| `design/ecad/source/usb-power-hub.kicad_sch` | `549dcaf43c7faff12ebdd68f0a309c870dd74462f670a853985e89809b48326d` |

## Open gates (CLAUDE.md 8 and 12), with owners

| Gate | State | Owner |
|---|---|---|
| JLCDFM on r02's Gerber | **run** (2026-11-13): 6 items with Danger, each judged in `JLCPCB_REVIEW.md` section 4; the 16 slot-width Danger rows are a decision for the user, the other items are JLCDFM's own reading of the geometry or hand-soldering reach; the 6 pad-spacing and 3 mask-exposure Danger rows are not identified one by one | user decides the slot width |
| Part mapping and placement preview, with the receptacle's model shift | **run** (2026-11-13): 41 of 41 parts, 0 substituted; the shift [0.0, -1.375] read on J1-J4 to about 0.04 mm. A viewer reading, not JLCPCB's pick-and-place | — (JLCPCB checks again after an order) |
| The quote of Rev0.5's BOM and CPL | read as a total only ($51.94 without shipping, with r01's Gerber); r02's own total, the line-by-line PCBA table, the cart's shipping and the Confirm Parts Placement option are not read or not chosen | user, at the JLCPCB step |
| EasyEDA import (D32) | blocked at the user's sign-in | user |
| The open issues of CLAUDE.md 11 | OI-1, OI-5, OI-6, OI-8 (panelization), OI-26 and OI-33 stand | user (built board, real cables) |
| User approval before any order or payment | not given | user |

## Residual risks

- The CPL's origin is the board's lower-left corner. Its Mid is the footprint's origin, plus the JLCPCB model
  shift of design/ecad/jlcpcb_model_frame.json for the receptacle C2765186 (J1-J4), and its angles are KiCad's
  plus the model rotation of that table (easy-stick 14.18). The table holds what JLCPCB's placement previews
  showed: the rotations on 2026-11-11 (Rev0.4, manufacturing/releases/rev0.4/r01/JLCPCB_REVIEW.md) and the
  receptacle's shift on 2026-11-13 (JLCPCB_REVIEW.md of this directory), to about 0.04 mm. A preview is the
  drawing of JLCPCB's model, not its pick-and-place; JLCPCB checks the final placement again in its DFM Analysis
  4-6 hours after an order. "Confirm Parts Placement" was left at No.
- The receptacle's land is the maker's, drawn for a 0.80 mm board; this one is 1.6 mm (OI-33). Whether the shell
  legs reach through the plated slots and the joints carry the plug's insertion force shows only on the first
  board (V-MFG-03, V-MECH-01). JLCDFM calls the slots' 0.60 mm width Danger, JLCPCB's capabilities page allows
  0.35 mm: the user's decision (JLCPCB_REVIEW.md, section 8).
- The 8 GND contact pads A1 and B1 of the receptacles have no fanout via any more: each reaches L2 through its
  plated shell slot's pad, by a 0.20 mm stub that ends 0.05 mm inside the slot's ring. The path is wide, because
  the plane joins a plated pad solid, but neither its inductance nor the plated wall's current capacity is
  measured; the first board shows it.
- JLCDFM's Danger items of this Gerber (via annular ring of the 0.30 mm vias, THT-to-SMD distance, mask opening
  exposing a trace, pad spacing, silkscreen over a plugged via, the receptacles' plated-slot width) are judged one
  by one in JLCPCB_REVIEW.md: most are JLCDFM's own reading of the geometry, the slot width is a decision for the
  user. JLCPCB's own DFM at order time can differ.
- The receptacle's GND pads A1 and B1 are 0.035 mm shorter than the maker's land (the user's choice, D37), so that
  each NPTH peg keeps 0.200 mm from copper; the joint area under the plug's force is slightly smaller.
- The data-line taps (D38) are 1 kΩ stubs on the D+ and D- of OUT A and OUT B, an exception to CLAUDE.md 5.3 "No
  stubs"; whether they cost High-Speed eye margin at the receptacle land is OI-26's, and the fallback is that
  devices enumerate at Full-Speed.
- The L2 plane is checked in the 2-D fill KiCad writes (`check_routing.py` rule 9), not in the return currents: a
  void shorter than 3.0 mm still lengthens a return path. After the routing patch U1's exposed pad keeps
  1.65-1.80 mm of plane copper on its sides, against rule 9's 1.60 mm.
- The router's session left 16 connections and 11 D36 places open, and a 275-row patch of
  `design/ecad/ROUTING_Rev0.5.md` (*After the router*, stages 1-5) closes them; the programs that wrote the first
  four stages are scratch tools outside the repository, and a new session needs a new patch. Some joined nets run
  long: V_INJ 87.9 mm, the buttons' and LEDs' lines 78.9-91.0 mm, the four taps 102.9-110.6 mm.
  `check_routing.py` has no length rule, and what the taps' wire capacitance does to a 12 Mbit/s edge is not
  computed.
- The board file is the source of truth, not `make_pcb.py`: KiCad's zone filler is not deterministic. Over 32
  scratch runs of 2026-11-13, 3 left out two 0.11 mm2 islands of the B.Cu GND pour that touch pad J3.S1 and 29 kept
  them; the Gerber's `B_Cu` member differs by exactly those two regions (checked member by member). This release
  was made from the board without them (SHA-256 above, tracked), and its Gerber is the one JLCDFM and the quote
  form read. A regenerated board can differ in those regions, and a changed Gerber needs a new review.
  Details: `design/ecad/README.md`.
- The sourcing check is of 2026-11-13 and the stock moves; the quantity JLCPCB shows for the receptacle (11 for 8)
  and its Extended feeder fee are read in the cart.
- Nothing has been built or measured. The open issues of CLAUDE.md 11 stand; the set is not orderable until each
  is closed.
