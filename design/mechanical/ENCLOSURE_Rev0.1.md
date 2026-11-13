# Enclosure Rev0.1 — printed tray and frame under a PCB lid (issue #11)

> **WIP — NOT PRINTED, NOT ORDERED.** This is a first design on paper for the Rev0.5 board
> (100 × 72 mm). Nothing has been printed, no cable has been tried in an opening, and the lid
> PCB is not drawn yet. Every dimension here is a parameter that the first print may change.
> The print process is not chosen (CLAUDE.md §7); the values assume FDM (E2) and stay
> provisional until the user chooses.

## 1. What it is

Four printed pieces, one PCB and sixteen pieces of hardware:

| Piece | Made by | What it does |
|---|---|---|
| Tray | printed, floor on the bed | Floor and the walls up to the board's top face. Four corner bosses carry the board; a rib under each receptacle carries the board's edge. |
| Frame | printed, upside down (its top face on the bed) | The walls above the board. Four corner posts clamp the board onto the bosses and carry the lid. Two towers guide the button plungers and hold a light well over each port's two LEDs; a tube guides a paperclip to SW3. |
| Plunger × 2 | printed, cap on the bed | Carries a finger's push through the lid to SW1 and SW2. |
| Lid | PCB, 100 × 72 × 1.6 mm, the main board's outline and hole positions | The top panel and its legend. Lies on the frame. **Not drawn yet**: this step writes its interface (holes, windows) only. |
| Hardware | bought | 8 heat-set M2 inserts, 4 countersunk M2 × 10 screws (bottom), 4 pan-head M2 × 5 screws (lid). |

The seam between tray and frame is at the board's top face. That puts every port opening in
a notch that is open towards the seam, so no piece needs support material in its print
orientation (checked: E04).

## 2. Frames and sources

- **Assembly frame.** The placement document's board frame (origin at the board's lower-left
  corner, x to the right, y up, mm) with z = 0 at the board's **top** face and z up. The
  board is z −1.6 … 0. The front edge (y = 0) carries OUT A and OUT B; the back edge
  (y = 72) carries 5V IN and HOST.
- **One dimension source (CLAUDE.md §7).** The board's outline, thickness, hole and footprint
  positions and courtyards come from `reference/board_interface_Rev0.5.json`, which
  `scripts/export_board_interface.py` writes from the tracked KiCad board. Nothing about the
  board is typed into this document or the scripts.
- **This document** holds what the board file cannot: the enclosure's parameters (§4) and the
  parts' heights (§5). `scripts/make_enclosure.py` reads both tables; a value is changed
  here and nowhere else.
- The three.js mockup's enclosure (64.4 × 28.4 × 9.7 mm, for the 60 × 24 mm board) is not a
  source for anything here.

## 3. Decisions

All made by Claude under the 2026-11-03 delegation while answering the user's request
「筐体もデザインして」 (2026-11-13). Each is provisional and the user may revert any one.

| ID | Decision | Why | Rejected |
|---|---|---|---|
| E1 | Tray + frame + PCB lid, seam at the board's top face. | CLAUDE.md §1 fixes "3D-printed tub + a second PCB used as the top panel". The board carries its receptacles on its edges, 1.06 mm past the outline, so it cannot be lowered into a one-piece tub with closed port holes. With the seam at the board's top face the board drops into the tray, and the frame comes down over the receptacles. | A one-piece tub with slots open to the rim (the lid would have to close the slots: a PCB cannot). A tub split at the ports' centre line (the frame would then print with overhangs). |
| E2 | Designed for FDM, 0.4 mm nozzle, 0.2 mm layers, no support material. | The stricter process: an overhang-free part also prints in MJF or SLA, and 0.3–0.4 mm clearances cover either. The process itself stays the user's choice (CLAUDE.md §7). | Freezing wall and clearance values for one process before the user chooses. |
| E3 | The lid is 100 × 72 mm, the main board's outline, and lies **on** the frame's top face inside a 2.4 mm margin. | It stays in the 100 × 100 mm price tier the main board was sized for (D24), and a seat recessed into the frame would be an overhang in the frame's print orientation. | A lid as large as the frame's outline (104.8 × 76.8 mm, outside the tier). A recessed seat. |
| E4 | Fastening: four countersunk M2 × 10 from below, through the tray's bosses and the board's holes H1–H4 into heat-set inserts in the posts' feet; the lid by four pan-head M2 × 5 into inserts in the posts' tops. | REQ-MECH-04 and D21 call for heat-set M2 inserts at the four corners. Posts and bosses clamp the board itself (OI-5: "the PCB itself is not clamped" in the mockup). A countersink prints without support on the bed side; a counterbore's flat ceiling does not. | One long screw through lid, post and board (M2 × 30 is not a stock length). Self-tapping screws into plastic (thread engagement, REQ-MECH-04). |
| E5 | A 0.2 mm designed gap at the seam, with a 45° ridge on the tray's wall inside a chamfer on the frame's. | The posts must land on the board before the walls meet, or the board is not clamped. The ridge closes the line of sight through the gap. | A butt seam (a 0.2 mm slit at the board's level all round). |
| E6 | Each port opening is a hole for the receptacle's shell behind a pocket for the plug's overmould (15.0 × 8.0 mm), whose floor is 0.1 mm behind the receptacle's face. | The receptacle's face is 1.34 mm inside the wall's outer face. Without the pocket an overmould would meet the wall before the plug seats (REQ-MECH-05). The pocket lets any overmould up to 14.0 × 7.0 mm reach the receptacle itself. | Thinning the whole wall to 0.7 mm. Moving the receptacles (a board change). |
| E7 | A rib under each receptacle, 0.1 mm below the board, and a shell hole that follows the shell at 0.3 mm. | REQ-MECH-03: the plug's force should not rest on the solder joints alone, and OI-33 leaves the shell legs' reach through a 1.6 mm board unproven. The rib takes a cable pushed down; the hole's edge takes one pulled up or sideways. OUT B stands 45.2 mm from the nearest screw (§6). | Relying on the four corner screws alone. |
| E8 | Buttons by loose printed plungers, captive under the lid; LEDs through one light well per port to a window of bare FR-4 in the lid; SW3 through a 2.0 mm pinhole and a guide tube. | SW1, SW2 and SW3 are 1.5 mm tall and the lid is 19 mm above the board. A plunger needs no part to buy; bare FR-4 passes an LED's light and needs no light pipe; REQ-BOOT-02 names the pinhole. | Flexures in the lid (the lid is a PCB). Bought light pipes (D13: few part types). |
| E9 | No vents. | About 1 W in a 104.8 × 76.8 mm box. Not calculated: an estimate from the board's supply current, and the first unit is measured. | Slots in the tray's floor or the walls (dust, and light from the LEDs). |

## 4. Parameters

`Kind`: **design** = chosen here and free to change; **world** = a fact about a bought or
soldered part, or a demand the checker makes on the design. All in mm.

<!-- params:begin -->
| Name | Value | Meaning | Kind |
|---|---:|---|---|
| `gap` | 0.4 | Board edge to the inner face of the walls. | design |
| `wall` | 2.0 | Wall thickness. | design |
| `corner_r` | 2.0 | Radius of the outer vertical edges. Equal to `wall`: the cavity's corners are sharp, so the wall keeps its thickness round each corner. | design |
| `edge_chamfer` | 0.6 | Chamfer of the tray's bottom edge and the frame's top edge (both on the bed when printed). | design |
| `floor` | 2.0 | Thickness of the tray's floor. | design |
| `standoff` | 3.5 | Board's bottom face to the floor. | design |
| `cavity_h` | 19.0 | Board's top face to the lid's underside. | design |
| `lid_t` | 1.6 | Thickness of the lid PCB. | world |
| `seam_gap` | 0.2 | Gap between the tray's wall and the frame's wall (E5). | design |
| `lip_h` | 0.8 | Height of the tray's ridge above the seam. | design |
| `lip_top` | 0.4 | Width of the ridge's flat top. | design |
| `lip_clear` | 0.3 | Horizontal clearance between the ridge and the frame. | design |
| `lid_overlap` | 0.8 | Width of the frame's flange under the lid's edge. | design |
| `flange_t` | 1.2 | Thickness of that flange. | design |
| `boss_reach` | 3.0 | A tray boss reaches this far past its hole's centre. | design |
| `post_reach` | 3.2 | A frame post reaches this far past its hole's centre. | design |
| `screw_clear_d` | 2.3 | Screw hole through the tray's bosses. | design |
| `csk_d` | 4.4 | Countersink diameter at the tray's bottom face (90°). | design |
| `insert_hole_d` | 3.2 | Hole for a heat-set insert. Set from the insert's data sheet when it is bought. | design |
| `insert_hole_depth` | 4.5 | Depth of that hole. | design |
| `insert_wall_min` | 1.5 | Plastic the checker demands around an insert hole. | world |
| `screw_d` | 2.0 | M2 thread diameter. | world |
| `csk_head_d` | 4.0 | Countersunk M2 head diameter. | world |
| `bottom_screw_len` | 10.0 | Bottom screw length, head included. | world |
| `lid_screw_len` | 5.0 | Lid screw length under the head. | world |
| `lid_screw_d` | 2.3 | Screw hole in the lid. | design |
| `lid_head_keepout_d` | 4.5 | Area of the lid a pan head covers. | world |
| `engage_min` | 2.0 | Thread engagement in an insert that the checker demands. | world |
| `usb_shell_w` | 8.94 | Receptacle shell width (C2765186 drawing). | world |
| `usb_shell_h` | 3.16 | Receptacle shell height above the board. | world |
| `usb_shell_len` | 7.35 | Receptacle shell length; the footprint's origin is its middle. | world |
| `shell_clear` | 0.3 | Shell hole's clearance around the shell. | design |
| `plug_w` | 14.0 | Width of the overmould the opening must pass. | world |
| `plug_h` | 7.0 | Height of that overmould. | world |
| `plug_r` | 1.5 | Its corner radius. | world |
| `pocket_w` | 15.0 | Width of the overmould pocket. | design |
| `pocket_h` | 8.0 | Height of the pocket, centred on the receptacle's opening. | design |
| `pocket_r` | 2.0 | Corner radius of the pocket. | design |
| `face_proud` | 0.1 | The receptacle's face stands this far in front of the pocket's floor. | design |
| `web_min` | 0.4 | Thickness the checker demands of the web between pocket and cavity. | world |
| `rib_w` | 4.0 | Width of the rib under a receptacle. | design |
| `rib_len` | 6.0 | Length of that rib from the wall. | design |
| `rib_gap` | 0.1 | Rib's top to the board's bottom face. | design |
| `ui_bottom` | 2.2 | Underside of the towers and the tube above the board. | design |
| `btn_bore_d` | 3.4 | Bore for a plunger's shaft. | design |
| `btn_wall` | 1.5 | Wall around that bore. | design |
| `btn_cbore_d` | 5.6 | Counterbore for a plunger's collar. | design |
| `btn_cbore_depth` | 2.2 | Depth of that counterbore below the frame's top. | design |
| `plunger_d` | 3.0 | Plunger shaft diameter. | design |
| `plunger_collar_d` | 5.0 | Plunger collar diameter. | design |
| `plunger_collar_h` | 0.7 | Height of the collar's cylinder (a 45° cone joins it to the cap). | design |
| `plunger_cap_d` | 4.0 | Plunger cap diameter. | design |
| `plunger_proud` | 1.0 | The cap stands this far above the lid at rest. | design |
| `plunger_play` | 0.5 | Collar's top to the lid's underside at rest. | design |
| `plunger_chamfer` | 0.3 | Chamfer of the cap's top edge. | design |
| `lid_btn_d` | 4.6 | Button hole in the lid. | design |
| `sw_travel` | 0.25 | Travel of TS-1187A (drawing: 0.2 ± 0.1; specification text: 0.25). | world |
| `sw_actuator_d` | 2.0 | Actuator diameter of TS-1187A. | world |
| `led_well_w` | 2.3 | Inner width of a light well. | design |
| `led_well_margin` | 0.6 | A well reaches this far past its LEDs' centres. | design |
| `led_wall` | 1.0 | Wall of a light well. | design |
| `boot_bore_d` | 2.0 | Bore of the tube over SW3. | design |
| `boot_wall` | 1.0 | Wall of that tube. | design |
| `lid_boot_d` | 2.0 | Pinhole in the lid over SW3. | design |
| `clip_d` | 0.9 | Paperclip wire the checker passes through the pinhole. | world |
| `part_margin` | 0.3 | Free height the checker demands above every part. | world |
| `tht_stub` | 2.5 | Lead length below the board the tray must clear. Leads are trimmed to it. | world |
<!-- params:end -->

## 5. Part heights

Height above the board's top face, by footprint. `read` = read from the part's drawing in
this repository's record or in this session; `assumed` = the package's usual maximum, from
memory, **not read from a data sheet**. An assumed height is confirmed on the first board.
A footprint with height 0 carries no body (pads, holes).

<!-- heights:begin -->
| Footprint | Height | Basis |
|---|---:|---|
| `Fuse_Bourns_MF-R300_Style2_P5.10mm` | 18.3 | read: `requirements/parts.md` F1, B max. The tallest part. |
| `Converter_DCDC_Minmax_MAU104_SIP` | 10.2 | read: Minmax MAU100 data sheet REV:0 2005/04, p6, case 19.5 × 6.1 × 10.2 mm. |
| `DIP-16_W7.62mm` | 5.4 | assumed: seated DIP, 5.33 mm maximum. |
| `USB_C_Receptacle_SHOUHAN_TYPE-C-16PIN-2MD-073` | 3.16 | read: SHOU HAN TYPE-C 16PIN 2MD(073) drawing REV. A. |
| `R_Shunt_Axial_MFU_L6.0mm_D2.3mm_P10.16mm_Kelvin` | 3.0 | assumed: a 2.3 mm body lying on bent leads. |
| `D_SMB` | 2.65 | assumed: DO-214AA. |
| `SOIC-8_5.3x5.3mm_P1.27mm` | 2.2 | assumed: 208 mil SOIC. |
| `SOT-223-3_TabPin2` | 1.8 | assumed. |
| `SOIC-8_3.9x4.9mm_P1.27mm` | 1.75 | assumed: 150 mil SOIC. |
| `SW_Push_1P1T_XKB_TS-1187A` | 1.5 | read: XKB TS-1187A drawing, height code A; the actuator's top. |
| `C_0805_2012Metric` | 1.5 | assumed. |
| `SOT-23` | 1.2 | assumed. |
| `R_Shunt_KOA_TSL1_6332Metric_Kelvin` | 1.2 | assumed. |
| `LED_0805_2012Metric` | 1.1 | assumed. |
| `C_0603_1608Metric` | 1.0 | assumed. |
| `L_0603_1608Metric` | 1.0 | assumed. |
| `Crystal_SMD_3225-4Pin_3.2x2.5mm` | 1.0 | assumed. |
| `RP2040_QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` | 0.9 | assumed. |
| `CH335F_QFN-28-1EP_4x4mm_P0.4mm_EP2.7x2.7mm` | 0.85 | assumed. |
| `R_0805_2012Metric` | 0.7 | assumed. |
| `R_Shunt_0805_2012Metric_Kelvin` | 0.7 | assumed. |
| `C_0402_1005Metric` | 0.6 | assumed. |
| `R_0603_1608Metric` | 0.6 | assumed. |
| `R_0402_1005Metric` | 0.5 | assumed. |
| `TestPoint_Pad_D1.0mm` | 0 | a pad. |
| `Fiducial_1mm_Mask2mm` | 0 | a pad. |
| `MountingHole_2.2mm_M2_ISO7380` | 0 | a hole. |
| `Tag-Connect_TC2030-IDC-NL_2x03_P1.27mm_Vertical` | 0 | pads and holes; the cable is fitted with the lid off. |
<!-- heights:end -->

## 6. Derived figures

Written by `make_enclosure.py --derived` and compared with the built files by
`check_enclosure.py` (E15). Do not edit by hand.

<!-- derived:begin -->
| Name | Value | Unit | Meaning |
|---|---:|---|---|
| `outer_x` | 104.80 | mm | Outer width (along the port edges). |
| `outer_y` | 76.80 | mm | Outer depth (front to back). |
| `outer_z` | 27.70 | mm | Height, tray's underside to the lid's top face. |
| `printed_z` | 26.10 | mm | Height without the lid. |
| `tray_z` | 7.90 | mm | The tray's print height. |
| `frame_z` | 19.00 | mm | The frame's print height. |
| `lid_margin` | 2.40 | mm | Frame's top face left free around the lid. |
| `web_t` | 0.56 | mm | Web between an overmould pocket and the cavity. |
| `face_inset` | 1.34 | mm | A receptacle's face inside the wall's outer face. |
| `port_to_screw_max` | 45.21 | mm | The receptacle farthest from a screw (J3) to its nearest mounting hole. |
| `swd_wall_clearance` | 1.16 | mm | The SWD footprint's courtyard (J5) to the nearest wall. |
| `lid_clearance_min` | 0.70 | mm | Tallest part (F1, 18.3 mm) to the lid's underside. |
| `bottom_engagement` | 3.10 | mm | Bottom screw's thread above the board's top face, in the post's insert. |
| `lid_engagement` | 3.40 | mm | Lid screw's thread below the lid, in the post's insert. |
| `plunger_len` | 20.10 | mm | Plunger length. |
| `tray_volume` | 20.50 | cm3 | Solid volume of the tray. |
| `frame_volume` | 18.76 | cm3 | Solid volume of the frame. |
| `plunger_volume` | 0.17 | cm3 | Solid volume of one plunger. |
<!-- derived:end -->

## 7. What the checker proves, and what it cannot see

`scripts/check_enclosure.py` reads the STL files as written, puts each back into the
assembly frame with the manifest's transform, and tests them against probes it builds itself
from the board interface and §4–§5:

| Check | Proves | Requirement |
|---|---|---|
| E01 | The files are the ones the manifest names; they were built from this document's tables and from the interface of the tracked board. | CLAUDE.md §7 (one source) |
| E02 | Each STL is one closed, consistently wound body. | — |
| E03 | Outer size: board + 2 × (gap + wall), and the height from §4. Nothing of tray or frame stands outside that outline and its `corner_r` corners. | — |
| E04 | In its print orientation each piece stands on the bed and has no face steeper than 45° that hangs in the air. | E2 |
| E05 | No printed piece and no lid enters any part's courtyard below the part's height + `part_margin`. | — |
| E06 | The tray clears every through-hole lead by `tht_stub`. | — |
| E07 | The board lies on four bosses, is clamped by four posts, and has a rib under every receptacle; every edge with a receptacle has two mounting points. | REQ-MECH-03 |
| E08 | Every shell hole clears its shell; an overmould of `plug_w` × `plug_h` reaches every receptacle's face; a web closes each pocket. | REQ-MECH-05 (design input only) |
| E09 | The screws pass, the heads sink flush, the thread engagement is within limits, and every insert hole has `insert_wall_min` of plastic around it. | REQ-MECH-04 |
| E10 | Each plunger stands on its switch, moves the switch's travel without touching anything, cannot leave through the lid, and stands proud of it. | — |
| E11 | Each LED has a free path to a window in the lid, inside a closed well. | — |
| E12 | A paperclip wire reaches SW3 through the lid, inside a tube no wider than the actuator allows. | REQ-BOOT-02 (design input only) |
| E13 | The lid has the board's outline and lies on the frame's top face without entering it; its outer 0.5 mm lies on the frame all round, and it lies on every post. | E3 |
| E14 | Tray and frame do not touch: the smallest gap is `seam_gap`. The outer 0.3 mm of both walls is whole all round the seam, outside the port pockets. | E5 |
| E15 | §6's figures are the built files' figures. | — |
| E16 | Every picture in `reports/` names the build it was drawn from, and it is this one. | — |

It cannot see:

- **What a picture shows.** E16 reads the manifest's SHA-256 that the renderer wrote into
  each PNG, and nothing else of it. The pictures are for looking at and prove nothing.
- **Whether a `world` value is right.** A cable's real overmould, the insert that is bought,
  a part's real height where §5 says `assumed`, the lid's real thickness (JLCPCB: ± 10 %).
- **The print.** Shrinkage, elephant's foot, sagging bridges, a 0.56 mm web that a slicer
  drops, a 2.0 mm vertical bore that closes up. Clearances are nominal.
- **Strength and stiffness.** Whether the posts hold an insert under a screw's pull, whether
  the walls bow, whether a rib or a hole's edge really takes a plug's force (OI-33).
- **Light.** How bright an LED is through 1.6 mm of bare FR-4, and what leaks between the
  two LEDs of one well (one well serves green and red by design).
- **Heat** (E9), **feel** (a loose plunger rattles), and **the legend** (the lid is not drawn).
- **V-MECH-01 and V-BOOT-01.** Both need the built unit and real cables. This check is a
  desk check ahead of them and closes neither OI-1 nor OI-5.

## 8. Hardware

Not bought, not chosen by part number. The parameters in §4 follow the usual dimensions,
from memory; each is set again from the bought part's data sheet before printing.

| Qty | Item | Used for | Parameter it sets |
|---:|---|---|---|
| 8 | Heat-set insert M2, brass, for a 3.2 mm hole, 3–4 mm long | Post feet (4) and post tops (4) | `insert_hole_d`, `insert_hole_depth` |
| 4 | Countersunk screw M2 × 10 (90° head, 4.0 mm) | Tray → board → post feet | `csk_d`, `csk_head_d`, `bottom_screw_len` |
| 4 | Pan-head screw M2 × 5 | Lid → post tops | `lid_screw_len`, `lid_head_keepout_d` |

## 9. Printing and assembly

Printing (E2): tray as modelled, floor on the bed; frame turned over, its top face on the
bed; plungers cap down. The STL files are already in these orientations. No support
material, no brim needed by the design; 0.2 mm layers, 3 perimeters.

Assembly:

1. Press the eight inserts into the frame's posts with a soldering iron, flush with each
   face.
2. Lay the board in the tray; the receptacles' shells rest in their notches.
3. Lower the frame over the board; the shells pass into the frame's notches.
4. Turn the stack over and drive the four countersunk screws through the tray.
5. Drop a plunger, shaft first, into each tower.
6. Lay the lid on the frame, caps through their holes, and drive the four lid screws.

SWD (J5) is reached with the lid off. The TC2030 footprint's courtyard stands 1.16 mm from
the back wall (§6); whether the cable's head fits beside the wall is not checked.

## 10. Not verified

- Nothing is printed. No fit, no cable, no screw has been tried.
- The lid PCB (its own revision, Gerber set and release, CLAUDE.md §7) is not drawn. This
  step fixes its outline, holes and windows in `assembly/UsbPowerHub_Enclosure_Rev0.1_LidInterface.json`.
- Of the 24 part heights in §5 that belong to a body, 20 are assumed. The four that were read
  are F1, the MAU104, the receptacle and the switch.
- The insert's hole diameter and the screws' head sizes are from memory (§8).
- The overmould envelope is this document's choice (14.0 × 7.0 mm). OI-1 records
  overmoulds of 12–14 mm; no cable was measured.
- F1 decides the height: 18.3 mm of a 27.7 mm box. `requirements/parts.md` notes that F1
  may be bent flat instead. That is a change of the board's assembly, not made here; with it
  the cavity could follow the MAU104 (10.2 mm).
