# Enclosure Rev0.5 — printed tray, frame and cover, a PCB lid let into the frame (issues #11, #13 and #14)

> **WIP — NOT PRINTED, NOT ORDERED.** This is a first design on paper for the Rev0.7 board
> (100 × 72 mm), which is ordered since 2026-11-20 and not yet delivered. Nothing has been
> printed and no cable has been tried in an opening. The lid
> PCB is drawn from this document's interface (`LID_Rev0.2.md`) and is not
> ordered. Every dimension here is a parameter that the first print may change.
> The print process is FDM (the user's choice, 2026-11-18; E2), and every printed piece is
> matte black (the user's, 2026-11-21; E2). The filament's material and the printer
> are not chosen, and the values stay provisional until the first print.
>
> **Rev0.5 against Rev0.4 (2026-11-21, issue #14).** The frame's wall goes on up round the
> lid, as high as the lid is thick, so that the lid lies in a pocket and its edge is no
> longer seen (E12). The user asked for it on a rendered picture of the unit, in which the
> lid lay on the frame and showed 1.6 mm of bare PCB edge all round: 「ここのPCBぶぶんは筐体に
> 収めないと」, and then, of the forms offered, 「ふたと同じ高さの壁で囲う」 (2026-11-21). The
> outer size is the same, 104.8 × 76.8 × 27.7 mm: the wall's top is where the lid's top face
> was. One thing is given up: the frame is now printed on support material, 1.6 mm high,
> under the lid's seat (E2 and E3 as amended). The tray, the plungers, the cover and the
> lid's interface are Rev0.4's. Enclosure Rev0.4 was never printed; its files are in Git
> history, at commit `d06cdea`.
>
> **Rev0.4 against Rev0.3 (2026-11-21, issue #14).** One piece is new: a printed cover for
> the clamp's opening (E11), after the user saw the opening in a picture of the finished unit
> (「これ蓋ないの?」, then 「蓋欲しいよ」, 2026-11-21). It closes the back wall's opening and the
> floor's, is pushed in from the back and pulled out by a fingernail, and comes off before
> the clamp goes on. The tray gains two notches in its floor for the cover's detents;
> the frame, the plungers and the lid's interface are Rev0.3's. Enclosure Rev0.3 was never
> printed; its files are in Git history, at commit `560dd11`.
>
> **Rev0.3 against Rev0.2 (2026-11-20, issue #14).** The Rev0.7 board has its SWD land, J5,
> as eight bare pads at the back edge, for a spring-pin clamp (D40). No part moved, so every
> opening, rib, tower and well of Rev0.2 stands where it stood. One thing is new: an opening
> for the clamp through the back wall of tray and frame and through the tray's floor (E10),
> 18.0 mm wide, after the user gave the clamp's width (「なる程、16.5mm がクランプの横幅」,
> 2026-11-20). The clamp's drawing is not known: its jaws' thickness and reach are
> estimates (§10). Enclosure Rev0.2 was never printed; its files are in Git history, at
> commit `a97c54f`.
>
> **Rev0.2 against Rev0.1 (2026-11-19, issue #13).** The Rev0.6 board has its connectors
> mirror-symmetric (D39). The openings, ribs, button towers and light wells follow the board's
> interface to their new places with no parameter changed. One thing did not fit: OUT B's
> button now stands beside the MAU104, and Rev0.1's tower stood inside that part's courtyard.
> A button's column now starts above the converter (`btn_bottom`, E8 as amended), its wall is
> 1.9 mm instead of 1.5 mm (`btn_wall`), and the checker measures the plastic round a
> plunger's bore and counterbore (`btn_wall_min`, E10). Enclosure Rev0.1 was never printed;
> its files are in Git history, at commit `de432d1`.

## 1. What it is

Five printed pieces, one PCB and sixteen pieces of hardware:

| Piece | Made by | What it does |
|---|---|---|
| Tray | printed, floor on the bed | Floor and the walls up to the board's top face. Four corner bosses carry the board; a rib under each receptacle carries the board's edge. |
| Frame | printed, upside down (the top of its wall on the bed), with support under the lid's seat (E12) | The walls above the board, carried on round the lid up to the lid's top face. Four corner posts clamp the board onto the bosses and carry the lid. Two towers guide the button plungers and hold a light well over each port's two LEDs; a tube guides a paperclip to SW3. A tower's column, which holds the plunger, starts 11.0 mm above the board; its light well and the tube come down to 2.2 mm. |
| Plunger × 2 | printed, cap on the bed | Carries a finger's push through the lid to SW1 and SW2. |
| Cover | printed, as it sits, its foot on the bed | Closes the SWD clamp's opening while the clamp is off: a slab in the back wall's opening and a foot in the floor's. Two spring fingers at the foot's sides click into notches of the tray's floor. |
| Lid | PCB, 100 × 72 × 1.6 mm, the main board's outline and hole positions | The top panel and its legend. Lies in the frame, on its seat, 0.4 mm inside the wall, its top face flush with the wall's top (E12). This document writes its interface (outline, holes, windows, port positions); the board itself is `LID_Rev0.2.md`, drawn from that interface and not ordered. |
| Hardware | bought | 8 heat-set M2 inserts, 4 countersunk M2 × 10 screws (bottom), 4 pan-head M2 × 5 screws (lid). |

The seam between tray and frame is at the board's top face. That puts every port opening in
a notch that is open towards the seam, so no opening needs support material in its piece's
print orientation. One face does since Rev0.5: the lid's seat in the frame, which hangs
1.6 mm above the bed (E12). No other face of any piece hangs (checked: E04).

## 2. Frames and sources

- **Assembly frame.** The placement document's board frame (origin at the board's lower-left
  corner, x to the right, y up, mm) with z = 0 at the board's **top** face and z up. The
  board is z −1.6 … 0. The front edge (y = 0) carries OUT A and OUT B; the back edge
  (y = 72) carries 5V IN and HOST.
- **One dimension source (CLAUDE.md §7).** The board's outline, thickness, hole and footprint
  positions and courtyards come from `reference/board_interface_Rev0.7.json`, which
  `scripts/export_board_interface.py` writes from the tracked KiCad board. Nothing about the
  board is typed into this document or the scripts.
- **This document** holds what the board file cannot: the enclosure's parameters (§4) and the
  parts' heights (§5). `scripts/make_enclosure.py` reads both tables; a value is changed
  here and nowhere else.
- The three.js mockup's enclosure (64.4 × 28.4 × 9.7 mm, for the 60 × 24 mm board) is not a
  source for anything here.

## 3. Decisions

All made by Claude under the 2026-11-03 delegation while answering the user's request
「筐体もデザインして」 (2026-11-13), except the print process in E2, which the user chose on
2026-11-18. E8's amendment is Claude's too, made on 2026-11-19 for the Rev0.6 board
(issue #13). E11 and E12 answer requests of the user's (2026-11-21); their rows say what
is the user's in them. Each is provisional and the user may revert any one.

| ID | Decision | Why | Rejected |
|---|---|---|---|
| E1 | Tray + frame + PCB lid, seam at the board's top face. | CLAUDE.md §1 fixes "3D-printed tub + a second PCB used as the top panel". The board carries its receptacles on its edges, 1.06 mm past the outline, so it cannot be lowered into a one-piece tub with closed port holes. With the seam at the board's top face the board drops into the tray, and the frame comes down over the receptacles. | A one-piece tub with slots open to the rim (the lid would have to close the slots: a PCB cannot). A tub split at the ports' centre line (the frame would then print with overhangs). |
| E2 | Printed by FDM (**user**, 2026-11-18: the choice 「FDM」, offered with MJF, FDM recommended). 0.4 mm nozzle, 0.2 mm layers, no support material (Claude); since Rev0.5 the frame is the exception, with support under the lid's seat only (E12). Colour: matte black for all five printed pieces, the plungers included (**user**, 2026-11-21: 「全部黒だよマット」, on a picture of the unit with a white case). The four lid screws, the only ones seen from above, are black too (Claude's reading of 「全部」). | CLAUDE.md §7 wants the process chosen before wall and clearance values are frozen. The colour changes no value in §4. The parts were drawn for FDM from the start, as the stricter process (no overhang, 0.3–0.4 mm clearances), so the choice changes no value in §4. The first print is a fit check, and a changed opening or clearance is printed again. | MJF (offered, not chosen): its walls and clearances would have been reviewed before freezing. Freezing the values before the user chose. |
| E3 | The lid is 100 × 72 mm, the main board's outline. Until Rev0.4 it lay **on** the frame's top face inside a 2.4 mm margin; since Rev0.5 that face is a seat inside the wall (E12). | It stays in the 100 × 100 mm price tier the main board was sized for (D24). Until Rev0.4: a seat recessed into the frame would be an overhang in the frame's print orientation. That is still so, and E12 accepts it. | A lid as large as the frame's outline (104.8 × 76.8 mm, outside the tier). A recessed seat: rejected until Rev0.4, taken in Rev0.5 at the user's request (E12). |
| E4 | Fastening: four countersunk M2 × 10 from below, through the tray's bosses and the board's holes H1–H4 into heat-set inserts in the posts' feet; the lid by four pan-head M2 × 5 into inserts in the posts' tops. | REQ-MECH-04 and D21 call for heat-set M2 inserts at the four corners. Posts and bosses clamp the board itself (OI-5: "the PCB itself is not clamped" in the mockup). A countersink prints without support on the bed side; a counterbore's flat ceiling does not. | One long screw through lid, post and board (M2 × 30 is not a stock length). Self-tapping screws into plastic (thread engagement, REQ-MECH-04). |
| E5 | A 0.2 mm designed gap at the seam, with a 45° ridge on the tray's wall inside a chamfer on the frame's. | The posts must land on the board before the walls meet, or the board is not clamped. The ridge closes the line of sight through the gap. | A butt seam (a 0.2 mm slit at the board's level all round). |
| E6 | Each port opening is a hole for the receptacle's shell behind a pocket for the plug's overmould (15.0 × 8.0 mm), whose floor is 0.1 mm behind the receptacle's face. | The receptacle's face is 1.34 mm inside the wall's outer face. Without the pocket an overmould would meet the wall before the plug seats (REQ-MECH-05). The pocket lets any overmould up to 14.0 × 7.0 mm reach the receptacle itself. | Thinning the whole wall to 0.7 mm. Moving the receptacles (a board change). |
| E7 | A rib under each receptacle, 0.1 mm below the board, and a shell hole that follows the shell at 0.3 mm. | REQ-MECH-03: the plug's force should not rest on the solder joints alone, and OI-33 leaves the shell legs' reach through a 1.6 mm board unproven. The rib takes a cable pushed down; the hole's edge takes one pulled up or sideways. On the Rev0.6 board every receptacle stands 14.0 mm from its nearest screw (§6); on Rev0.5, OUT B stood 45.2 mm from one. | Relying on the four corner screws alone. |
| E8 | Buttons by loose printed plungers, captive under the lid; LEDs through one light well per port to a window of bare FR-4 in the lid; SW3 through a 2.0 mm pinhole and a guide tube. | SW1, SW2 and SW3 are 1.5 mm tall and the lid is 19 mm above the board. A plunger needs no part to buy; bare FR-4 passes an LED's light and needs no light pipe; REQ-BOOT-02 names the pinhole. | Flexures in the lid (the lid is a PCB). Bought light pipes (D13: few part types). |
| E8, amended in Rev0.2 | A button's column starts 11.0 mm above the board (`btn_bottom`) instead of 2.2 mm, in 1.9 mm of wall (`btn_wall`; 1.5 mm in Rev0.1). The light wells and the tube still come down to 2.2 mm (`ui_bottom`). | On the Rev0.6 board SW2 stands 2.955 mm from the courtyard of the MAU104 (U5, 10.2 mm tall). Rev0.1's column reached 3.2 mm to each side of its button from 2.2 mm up, so it stood 0.245 mm inside that courtyard: E05 failed with 13.60 mm³ of the frame in U5's envelope. A column that starts above the converter clears it whatever its width. That let the wall grow to leave 0.8 mm round the counterbore, two perimeters of the nozzle; Rev0.1 left 0.4 mm there and no check measured it. Both towers are built alike. The cost: the bore guides a plunger over 4.7 mm instead of 13.5 mm (§10). | A column narrowed beside the converter (1.2 mm of wall, 0.35 mm from the body of a hand-soldered part). A thinner plunger (a 2.0 mm shaft, printed 20 mm long). Moving U5 or SW2 (a change of the board that D39 has just placed). |
| E9 | No vents. | About 1 W in a 104.8 × 76.8 mm box. Not calculated: an estimate from the board's supply current, and the first unit is measured. | Slots in the tray's floor or the walls (dust, and light from the LEDs). E10's opening is not a vent; it is the one place where dust enters and light leaves while its cover (E11) is off. |
| E10 (Rev0.3, Claude, 2026-11-20) | An opening for the SWD clamp, centred on J5: 18.0 mm wide (`clamp_w` + 2 × `clamp_clear`), through the back wall of the tray and of the frame up to 12.0 mm above the board (`clamp_up`), and through the tray's floor from 8.0 mm inside the board's back edge (`clamp_reach`). 8.6 mm of the frame's wall stays above it, up to the wall's top (7.0 mm until Rev0.4, when the wall ended under the lid's edge). | D40: the user debugs through SWD with a spring-pin clamp that grips the board's edge from above and below (「SWD経由で君にデバッグまで自動化して開発したいからさ。」), so the clamp must reach J5 with the unit closed. The clamp is 16.5 mm wide (user, 2026-11-20); its drawing is not known, so the opening does not depend on the jaws' thickness: below the board it is open down to the desk, 5.5 mm, and the unit can be lifted. Both cuts are open towards the seam or the bed, so no piece gains an overhang (E04). | SWD only with the frame and tray off (the unit could not be debugged as it is used). A window in the frame alone (the tray's wall and floor stand in the lower jaw's way). A door or plug for the opening (a fifth printed piece; the first print shows whether dust or light matters): rejected in Rev0.3, added in Rev0.4 at the user's request (E11). |
| E11 (Rev0.4, the request the **user**'s, 2026-11-21: 「蓋欲しいよ」; the shape Claude's) | A loose printed cover for E10's opening, pushed in from the back. A slab fills the wall's opening, flush with the wall, with `cover_clear` round it; a foot fills the floor's opening. At each side of the foot a finger 0.8 mm wide, free of the foot's plate over its whole length, carries a 45° detent that stands 0.4 mm behind the side of the floor's opening, in a notch of the tray's floor. A 45° wedge on the slab's inner face reaches 0.6 mm over the board's back edge. A slot of 8 × 3 mm through the foot takes a fingernail. | The opening is 18.0 × 19.1 mm in the back wall and shows the board; the user wants it closed when the clamp is off. What holds the cover: the floor's end stops it inwards after 0.2 mm, the detents hold it against being drawn out, the frame's wall above stops it upwards after 0.2 mm, and with the unit lifted it drops 0.4 mm until the wedge lies on the board's edge. The wedge's gap is twice the inward play, so a push on the cover ends on the tray and not on the board. The cover prints as it sits, with no support: the wedge's underside is at 45°, and the fingers lie flat, so their layers run along them. The slot is open through the foot because a blind recess would be a bridge on the bed side (E04). | A cover held by friction alone (nothing to check, and the first print decides the fit). A cover that slides in from below (it falls out when the unit is lifted). A flat ledge over the board instead of the wedge (an overhang, E04). Rails in the sides of the wall's opening (they cut the wall that E17 keeps whole at each side). A hinged door (a pin or a living hinge, in a wall 2.0 mm thick). |
| E12 (Rev0.5, 2026-11-21; the request and the form the **user**'s: on a rendered picture of the unit, the lid's edge marked in red, 「ここのPCBぶぶんは筐体に収めないと」, then 「ふたと同じ高さの壁で囲う」; the construction Claude's) | The frame's wall goes on up round the lid by the lid's thickness (`lid_t`, 1.6 mm). It keeps the wall's 2.0 mm and its outer face; its inner face stands `rim_clear` (0.4 mm) from the lid's edge; its top is flush with the lid's top face and carries the chamfer that the frame's top edge had. The lid lies in the pocket this makes, on the seat that was the frame's top face (flange, posts, towers, light wells, tube). The wall is one piece with the frame. The frame is printed turned over as before, now standing on the wall's top, and the lid's seat, 6.28 cm², is printed on support material 1.6 mm high. With the screws out the lid has no edge to grip: the unit is turned over and the lid falls into the hand. | With the lid lying on the frame, 1.6 mm of the PCB's routed edge showed all round the top of the unit, bare laminate on a matte black case; the user saw it in the pictures and wants it inside the case. As high as the lid: the user's words. One piece with the frame: a separate ring would be 2.0 × 1.6 mm in section and 355 mm round, with a seam all round where the edge showed before. Turned over with support: every face that needs it is 1.6 mm above the bed with nothing below it, so the support stands on the bed, is 8 layers high and is reached from the open side; the lid then covers the faces it leaves. The outer size does not change. | A frame that laps over the lid's edge (offered to the user, not chosen: it covers the lid's outer 0.8 mm and holds the lid only with the frame's own screws). A separate ring, glued on (offered, not chosen). The frame printed the right way up (the towers would hang 11.0 mm and the light wells 2.2 mm above the bed, inside the cavity: more support, and harder to remove). A 45° face from the seat out to the wall's top instead of support (the gap round the lid would be 2.0 mm wide at the top). A wall higher than the lid, to guard the legend (not what the user said). A notch in the wall for a fingernail (the edge would show again there). |

## 4. Parameters

`Kind`: **design** = chosen here and free to change; **world** = a fact about a bought or
soldered part, or a demand the checker makes on the design. All in mm, except
`cover_strain_max`, in %.

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
| `rim_clear` | 0.4 | Gap between the lid's edge and the wall that stands round it (E12). Equal to `gap`, so the wall's inner face runs straight up from the cavity. | design |
| `rim_clear_min` | 0.3 | Gap round the lid that the checker demands: ± 0.2 mm on the lid's outline (JLCPCB's routing tolerance, from memory, not read on this day) and as much on a printed pocket. | world |
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
| `ui_bottom` | 2.2 | Underside of the light wells and the tube above the board. | design |
| `btn_bottom` | 11.0 | Underside of a button's column above the board: 0.8 mm above the MAU104 (10.2 mm), which stands beside SW2 on the Rev0.6 board (E8). | design |
| `btn_bore_d` | 3.4 | Bore for a plunger's shaft. | design |
| `btn_wall` | 1.9 | Wall around that bore; it leaves `btn_wall_min` around the counterbore. | design |
| `btn_wall_min` | 0.8 | Plastic the checker demands around a plunger's bore and counterbore: two perimeters of a 0.4 mm nozzle (E2). | world |
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
| `clamp_w` | 16.5 | Width of the SWD clamp (user, 2026-11-20; AliExpress listing of D40, "2.54mm Double row 4P"). Not measured here. | world |
| `clamp_clear` | 0.75 | Free width at each side of the clamp in its opening. | design |
| `clamp_reach` | 8.0 | The tray's floor is open this far inside the board's back edge. An estimate: J5's inner row is 4.14 mm inside. | design |
| `clamp_up` | 12.0 | Top of the opening in the frame's wall, above the board. An estimate of the upper jaw's height at the wall. | design |
| `cover_clear` | 0.2 | Gap between the cover and the opening: at each side, at the top and at the foot's end (E11). | design |
| `cover_lift` | 0.6 | The cover's underside above the tray's underside, at rest. | design |
| `cover_arm_w` | 0.8 | Width of the spring finger at each side of the cover's foot: two perimeters of a 0.4 mm nozzle. | design |
| `cover_slit` | 0.8 | Slit between a finger and the foot's plate. | design |
| `cover_catch` | 0.6 | Height of the 45° detent at a finger's end, from the finger's face. | design |
| `cover_ledge` | 0.6 | The cover's wedge reaches this far over the board's back edge. | design |
| `cover_ledge_gap` | 0.4 | The wedge's 45° face above the board's top edge, at rest. Twice `cover_clear`: pushed in to its stop, the cover is still 0.2 mm from the board. | design |
| `cover_ledge_h` | 0.8 | Height of the wedge's end face. | design |
| `cover_pull_w` | 8.0 | Width of the slot through the foot that takes a fingernail. | design |
| `cover_pull_l` | 3.0 | Length of that slot. | design |
| `cover_strain_max` | 1.5 | Strain, in %, that the checker allows at a finger's root. An assumption for PLA and PETG, not read from a data sheet. | world |
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
| `SWD_Pads_2x04_P2.54mm_D1.7mm_Clamp` | 0 | pads; a clamp grips them through the opening of E10. |
<!-- heights:end -->

## 6. Derived figures

Written by `make_enclosure.py --derived` and compared with the built files by
`check_enclosure.py` (E15). Do not edit by hand.

<!-- derived:begin -->
| Name | Value | Unit | Meaning |
|---|---:|---|---|
| `outer_x` | 104.80 | mm | Outer width (along the port edges). |
| `outer_y` | 76.80 | mm | Outer depth (front to back). |
| `outer_z` | 27.70 | mm | Height, tray's underside to the top of the wall round the lid, which is the lid's top face. |
| `tray_z` | 7.90 | mm | The tray's print height. |
| `frame_z` | 20.60 | mm | The frame's print height. |
| `rim_h` | 1.60 | mm | Height of the wall round the lid above the lid's seat: the lid's thickness. |
| `rim_gap` | 0.40 | mm | Gap between the lid's edge and the wall round it. |
| `rim_wall` | 2.00 | mm | Thickness of the wall round the lid, below its chamfer. |
| `frame_support_area` | 6.28 | cm2 | The lid's seat, which hangs above the bed when the frame is printed: the area that needs support material. |
| `web_t` | 0.56 | mm | Web between an overmould pocket and the cavity. |
| `face_inset` | 1.34 | mm | A receptacle's face inside the wall's outer face. |
| `port_to_screw_max` | 14.03 | mm | The receptacle farthest from a screw (J4) to its nearest mounting hole. |
| `clamp_opening_w` | 18.00 | mm | Width of the clamp's opening in the back wall, centred on the SWD land (J5). |
| `clamp_bridge_h` | 8.60 | mm | Height of the frame's wall that is left above the clamp's opening, up to the wall's top. |
| `lid_clearance_min` | 0.70 | mm | Tallest part (F1, 18.3 mm) to the lid's underside. |
| `bottom_engagement` | 3.10 | mm | Bottom screw's thread above the board's top face, in the post's insert. |
| `lid_engagement` | 3.40 | mm | Lid screw's thread below the lid, in the post's insert. |
| `plunger_len` | 20.10 | mm | Plunger length. |
| `cover_z` | 18.30 | mm | The cover's print height. |
| `cover_engage` | 0.40 | mm | A detent of the cover behind the side of the opening in the tray's floor. |
| `cover_gap_min` | 0.14 | mm | Smallest gap between the cover at rest and the tray or the frame. |
| `cover_strain` | 0.83 | % | Strain at a finger's root while its detent passes the opening's side (1.5 x width x deflection / length squared). |
| `tray_volume` | 19.93 | cm3 | Solid volume of the tray. |
| `frame_volume` | 18.84 | cm3 | Solid volume of the frame. |
| `plunger_volume` | 0.17 | cm3 | Solid volume of one plunger. |
| `cover_volume` | 0.82 | cm3 | Solid volume of the cover. |
<!-- derived:end -->

## 7. What the checker proves, and what it cannot see

`scripts/check_enclosure.py` reads the STL files as written, puts each back into the
assembly frame with the manifest's transform, and tests them against probes it builds itself
from the board interface and §4–§5:

| Check | Proves | Requirement |
|---|---|---|
| E01 | The files are the ones the manifest names; they were built from this document's tables and from the interface of the tracked board. | CLAUDE.md §7 (one source) |
| E02 | Each STL is one closed, consistently wound body. | — |
| E03 | Outer size: board + 2 × (gap + wall), and the height from §4; the frame ends at the lid's top face. Nothing of tray, frame or cover stands outside that outline and its `corner_r` corners. | — |
| E04 | In its print orientation each piece stands on the bed and has no face steeper than 45° that hangs in the air. One exception, in the frame only: flat faces at the lid's thickness above the bed, which are the lid's seat; their area is reported as what the print supports (§6, `frame_support_area`). | E2, E12 |
| E05 | No printed piece and no lid enters any part's courtyard below the part's height + `part_margin`. | — |
| E06 | The tray and the cover clear every through-hole lead by `tht_stub`. | — |
| E07 | The board lies on four bosses, is clamped by four posts, and has a rib under every receptacle; every edge with a receptacle has two mounting points. | REQ-MECH-03 |
| E08 | Every shell hole clears its shell; an overmould of `plug_w` × `plug_h` reaches every receptacle's face; a web closes each pocket. | REQ-MECH-05 (design input only) |
| E09 | The screws pass, the heads sink flush, the thread engagement is within limits, and every insert hole has `insert_wall_min` of plastic around it. | REQ-MECH-04 |
| E10 | Each plunger stands on its switch, moves the switch's travel without touching anything, cannot leave through the lid, and stands proud of it. Its bore, from the column's underside to the cone, and its counterbore each have `btn_wall_min` of plastic all round. | E8 |
| E11 | Each LED has a free path to a window in the lid, inside a closed well. | — |
| E12 | A paperclip wire reaches SW3 through the lid, inside a tube no wider than the actuator allows. | REQ-BOOT-02 (design input only) |
| E13 | The lid has the board's outline and lies on its seat, the top of what the frame has inside that outline, without entering the frame; its outer 0.5 mm lies on the frame all round, and it lies on every post. | E3 |
| E14 | Tray and frame do not touch: the smallest gap is `seam_gap`. The outer 0.3 mm of both walls is whole all round the seam, outside the port pockets and the clamp's opening. | E5 |
| E15 | §6's figures are the built files' figures. | — |
| E16 | Every picture in `reports/` names the build it was drawn from, and it is this one. | — |
| E17 | The SWD land is at the back edge, inside the opening's width. A box `clamp_w` wide with `clamp_clear` at each side, from `clamp_reach` inside the board's edge outwards and from below the tray up to `clamp_up`, holds no plastic of tray or frame. 1.0 mm of whole wall stands at each side of the opening in both pieces, and 3.0 mm of whole wall above it in the frame. | E10, D40 (design input only) |
| E18 | The cover at rest touches neither tray, frame, board nor lid, with at least 0.7 × `cover_clear` everywhere (a 45° face). It fills the wall's opening, flush with the wall, with gaps of 0.05 to 0.6 mm round it; its foot closes at least 65 % of the floor's opening, and the fingernail's slot is free from below. Pulled 1.0 mm outwards, each detent meets the tray's floor, and it stands at least `cover_clear` + 0.1 mm behind the opening's side. Each finger is whole, has room to bend by that much and 0.1 mm more, and the strain at its root is below `cover_strain_max`. With its detents cut off, the cover slides 12 mm out through the wall and touches nothing. Pushed in 0.3 mm it is in the tray's floor and not in the board; dropped 0.7 mm it is in the board (it cannot fall out), and hanging on the board its underside is still above the tray's; raised 0.5 mm it is in the frame. | E11 |
| E19 | The frame ends flush with the lid's top face. The lid's edge is at least `rim_clear_min` and at most 0.6 mm from the frame above the seat, and a box `rim_clear_min` wider than the lid on every side, from the seat up to 10 mm above the unit, holds no plastic: nothing stands over the lid, and it lifts straight out. Between that gap and the outline, from the seat up to the chamfer, the wall is whole all round (less than 0.05 mm³ missing). | E12 |

It cannot see:

- **What a picture shows.** E16 reads the manifest's SHA-256 that the renderer wrote into
  each PNG, and nothing else of it. The pictures are for looking at and prove nothing.
- **Whether a `world` value is right.** A cable's real overmould, the insert that is bought,
  a part's real height where §5 says `assumed`, the lid's real thickness (JLCPCB: ± 10 %).
- **The print.** Shrinkage, elephant's foot, sagging bridges, a 0.56 mm web that a slicer
  drops, a 2.0 mm vertical bore that closes up. Clearances are nominal. E04 counts the area
  under the lid's seat that a print supports; it knows nothing of the support itself, of
  how it comes off, or of the face it leaves for the lid to lie on.
- **The lid's fit in its pocket.** E19 has the nominal gap, 0.4 mm. The real one is a routed
  PCB outline in a printed pocket whose mouth is the print's first layer (§10).
- **Strength and stiffness.** Whether the posts hold an insert under a screw's pull, whether
  the walls bow, whether a rib or a hole's edge really takes a plug's force (OI-33).
- **Light.** How bright an LED is through 1.6 mm of bare FR-4, and what leaks between the
  two LEDs of one well (one well serves green and red by design).
- **A plunger's tilt.** E10 moves a plunger down, up and sideways. It does not tilt it, and
  the bore that guides it is 4.7 mm long (§10).
- **The clamp.** E17's box is this document's guess at a clamp of which only the width is
  known. It takes the footprint's origin as the middle of the land, and it does not look at
  the parts on the board under the upper jaw (§10).
- **The cover's fit.** E18 moves a rigid cover and computes a finger's strain from a beam
  formula. It does not bend a finger, and it knows no friction: the force that draws the
  cover out, whether the detents click, whether a printed finger 0.8 mm wide breaks, and
  whether the cover rattles are the first print's findings (§10).
- **Heat** (E9), **feel** (a loose plunger rattles), and **the legend** (the lid's own
  document and checker, `LID_Rev0.2.md` §6).
- **V-MECH-01 and V-BOOT-01.** Both need the built unit and real cables. This check is a
  desk check ahead of them and closes neither OI-1 nor OI-5.

## 8. Hardware

Not bought, not chosen by part number. The parameters in §4 follow the usual dimensions,
from memory; each is set again from the bought part's data sheet before printing.

| Qty | Item | Used for | Parameter it sets |
|---:|---|---|---|
| 8 | Heat-set insert M2, brass, for a 3.2 mm hole, 3–4 mm long | Post feet (4) and post tops (4) | `insert_hole_d`, `insert_hole_depth` |
| 4 | Countersunk screw M2 × 10 (90° head, 4.0 mm) | Tray → board → post feet | `csk_d`, `csk_head_d`, `bottom_screw_len` |
| 4 | Pan-head screw M2 × 5, black (E2) | Lid → post tops | `lid_screw_len`, `lid_head_keepout_d` |

## 9. Printing and assembly

Printing (FDM, E2): tray as modelled, floor on the bed; frame turned over, the top of the
wall round the lid on the bed; plungers cap down; the cover as it sits, its foot and the
slab's lower edge on the bed. The STL files are already in these orientations. No brim
needed by the design; 0.2 mm layers, 3 perimeters. No support material for the tray, the
plungers and the cover. The frame is sliced with support **from the bed only**: it then
stands under the lid's seat alone, 1.6 mm (8 layers) high over 6.28 cm², inside the wall
(E12, E04). Support "everywhere" would also fill the bores and the port notches and is not
wanted. The support is broken out from the open side before the inserts go in. The filament
is matte black (E2); its material is not chosen (§10).

Assembly:

1. Press the eight inserts into the frame's posts with a soldering iron, flush with each
   face.
2. Lay the board in the tray; the receptacles' shells rest in their notches.
3. Lower the frame over the board; the shells pass into the frame's notches.
4. Turn the stack over and drive the four countersunk screws through the tray.
5. Drop a plunger, shaft first, into each tower.
6. Lay the lid into the frame's pocket, caps through their holes, and drive the four lid
   screws. Its top face is then level with the wall's top.

7. Push the cover into the opening in the back wall, foot first along the desk, until its
   two fingers click and its face is flush with the wall.

To take the lid off: the four lid screws out, a hand over the lid, the unit turned over.
The lid has no edge to grip and falls into the hand, and the two plungers follow it. A lid
that sticks is pushed out from inside, after the bottom screws, the tray and the board are
off. Not tried (§10).

SWD (J5) is reached with the unit closed: lift the unit, hook a fingernail into the slot in
the cover's foot and draw the cover out backwards; the clamp then enters the opening in the
back wall (E10) and grips the board's edge, its pins on J5's eight pads. Not tried (§10).

## 10. Not verified

- Nothing is printed. No fit, no cable, no screw has been tried.
- **The wall round the lid (E12) is drawn, not printed.** Four things wait for a print.
  The support under the lid's seat: whether it comes off clean from a face 1.2 mm wide along
  the walls, and how flat it leaves the seat (the lid is drawn down onto the four posts by
  its screws, and a rough flange under its edge may leave a gap that light shows through).
  The pocket's mouth: it is the print's first layer, and an elephant's foot narrows it; the
  gap is 0.4 mm a side, and JLCPCB's tolerance on a routed outline is taken as ± 0.2 mm
  from memory, not read on this day. Flushness: the lid's thickness is 1.6 mm ± 10 %
  (§7), so its top face can stand 0.16 mm above or below the wall's top, and the seat's
  finish adds to that. And taking the lid off by turning the unit over (§9), which lets
  the plungers fall out. The wall's top face is 1.4 mm wide beside its 0.6 mm chamfer, and
  the whole frame stands on it while it prints (4.92 cm² on the bed, measured by E04).
- E2 fixes the process (FDM) and the colour (matte black) only. The material (PLA, PETG or
  another) and the printer are not chosen, and no filament is bought.
- The lid PCB (its own revision, Gerber set and release, CLAUDE.md §7) is drawn as Lid Rev0.2
  (`LID_Rev0.2.md`) from `assembly/UsbPowerHub_Enclosure_Rev0.5_LidInterface.json`, which this
  document fixes. It is not ordered and has no release; what is not verified of it is in its
  own §8. A change here that moves a hole, a window or a port needs the lid built again.
- **The clamp's opening (E10) is drawn for a clamp nobody here has seen.** Its width,
  16.5 mm, is the user's figure; the jaws' thickness, their reach over the board and the
  height of the upper jaw at the wall are not known. `clamp_reach` 8.0 mm and `clamp_up`
  12.0 mm are estimates, and the user does not measure the clamp before the board arrives
  (D40). The first print, or the clamp on the bare board, is the check.
- **The cover (E11) is drawn, not printed.** Its clearances are 0.2 mm (0.14 mm across the
  detents' 45° faces), which a first FDM print may close or leave loose. The fingers are
  0.8 mm wide and bend by 0.4 mm over 7.6 mm; the strain, 0.83 %, comes from a beam formula
  and a limit of 1.5 % that was not read from a data sheet. By the same formula, with a
  modulus of 3 GPa and a friction of 0.3 assumed, the cover is drawn out with about 2 N:
  computed by hand, not by the checker. The wedge lies on the board's bare edge when the
  unit is lifted, with the cover's own weight (about 1 g). Lifted, the cover hangs 0.4 mm
  lower, so the gap above it is then 0.6 mm. The board's place in the tray can differ by
  the screws' play; the wedge's gap allows 0.2 mm of it. The slots of the fingers and the
  fingernail's slot leave 29 % of the floor's opening open.
- **A capacitor stands under the clamp's width.** The clamp, 16.5 mm wide and centred on J5,
  covers x 36.25 … 52.75 mm. C3 (0805, 1.5 mm assumed) has its courtyard at x 51.88 … 53.92
  and y 64.5 … 68.0, 4.0 mm inside the back edge; J5's inner row is 4.14 mm inside. If the
  upper jaw's body is as wide as the clamp and reaches more than 4.0 mm over the board at
  less than 1.5 mm above it, it meets C3 by up to 0.87 mm in x. That is a matter of the
  board, which is ordered, not of the enclosure; it was found here because the width became
  known after the order. Not settled on paper.
- A plunger's guide is short since Rev0.2. The bore holds the shaft between 11.0 and 15.7 mm
  above the board (4.7 mm; 13.5 mm in Rev0.1), and the foot stands 9.5 mm below it. From the
  nominal clearances (a 3.0 mm shaft in a 3.4 mm bore, a 4.0 mm cap in the lid's 4.6 mm hole)
  the foot can stand about 0.7 mm off the switch's axis, against about 0.2 mm in Rev0.1; a
  3.0 mm foot then still covers the middle of the 2.0 mm actuator. Computed by hand, not by
  the checker, and not tried. If the first print rattles or misses the switch, the next step
  is a guide below 11.0 mm that is open towards the converter.
- The MAU104 is soldered by hand and may lean. The column's underside is 0.8 mm above its
  10.2 mm, and OUT B's light well stands 2.55 mm to the side of its courtyard.
- Of the 24 part heights in §5 that belong to a body, 20 are assumed. The four that were read
  are F1, the MAU104, the receptacle and the switch.
- The insert's hole diameter and the screws' head sizes are from memory (§8).
- The overmould envelope is this document's choice (14.0 × 7.0 mm). OI-1 records
  overmoulds of 12–14 mm; no cable was measured.
- F1 decides the height: 18.3 mm of a 27.7 mm box. `requirements/parts.md` notes that F1
  may be bent flat instead. That is a change of the board's assembly, not made here; with it
  the cavity could follow the MAU104 (10.2 mm).
