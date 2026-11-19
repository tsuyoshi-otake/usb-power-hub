# USB Power-Control Hub — Rev0.7 routing

> **WIP — MANUFACTURING PROHIBITED.** How the placed Rev0.7 board (PLACEMENT_Rev0.7.md) is
> routed, and why. Issue #6 P4, reworked for the machine-placed receptacles and the data-line
> taps (issues #8 and #10, D37 and D38) and for the mirror-symmetric connectors (issue #13, D39,
> Rev0.6: Rev0.5's routing carried where it still stands, a new router session for the rest and
> a new patch). Nothing here has been built or measured.

`design/ecad/scripts/make_pcb.py` builds `source/usb-power-hub.kicad_pcb` from the placement,
this file, the carried record and the committed router session in `routing/`; `scripts/carry.py`
writes that record and `scripts/autoroute.py` that session; `scripts/check_routing.py` checks
the board against this file and runs DRC (`design/ecad/README.md`). Change a track here, never
in KiCad: the next run of `make_pcb.py` rebuilds the board.

## Frame and format

- The board frame of PLACEMENT_Rev0.7.md: origin at the lower-left corner, x right, y up, in mm;
  a board point (x, y) is at (50 + x, 122 − y) on KiCad's sheet.
- A point is `x,y` or `REF.PAD`, the pad's centre; a pad point must be on the row's net.
- A track row draws one track through its points on one layer, at one width. A `via` row places
  one through via (diameter/drill) at its one point.
- `channel_route` rows are channel A's. Channel B gets the same rows moved by the placement's
  `dx` (33.8 mm), each part mapped by the placement's channel table (RS10 → RS20) and `_A` →
  `_B` in the net names. They are the front ends' rows. A port's own rows, from the lift vias at
  its bypass FET to its receptacle, are in the `route` table for each port since D39: OUT B's
  receptacle is not 33.8 mm from OUT A's.

## Layers

JLC04161H-7628 (D27): L1 and L4 are 35 µm, L2 and L3 15.2 µm; L1–L2 and L3–L4 are 0.2104 mm
of 7628 prepreg, L2–L3 the 1.065 mm core. L3's nearest plane is therefore L4, not L2.

| Layer | Use | Reference |
|---|---|---|
| L1 F.Cu | parts, the HS pairs, power trunks, signals | L2 |
| L2 In1.Cu | solid GND plane; no track | — |
| L3 In2.Cu | signals and supplies; none over a B.Cu trunk; GND fill in what is left | L4 |
| L4 B.Cu | power trunks, signals; GND fill in what is left | L3 |

CLAUDE.md 5.1 asks an L3 signal under the analog blocks or a USB pair to have GND on L4 directly
below. In the analog blocks, an L3 signal and an L4 signal may cross, at 45° or more, but may
not run along each other (D36, user, 2026-11-06). Where they cross, L4 below the L3 signal is
a signal for the width of the crossing, not GND. The rule is between two nets: a net over its
own L4 track, where it changes layer at a via, is one signal. `check_routing.py` measures the
angle to 0.1° (the session's 0.1 µm grid moves a 45° track by a few millidegrees).

The analog blocks are the placement's AFE_A, AFE_B, ADC, ADCSUP and REF, named once, in the
`analog` argument of the keepouts table below.
No L3 track runs above the hand-drawn power trunks in those blocks, and none runs under a pair
(router keepouts below).

**Why D36.** The router was given F.Cu and L3 only under the analog blocks, and in every trial
it left 76–78 connections unrouted on 100 × 72 mm. With L4 open there too it left 9 by DRC's
count. That routing had 171 L3/L4 crossings and 29 parallel overlaps, 27 mm in all. The
parallel overlaps are what this rule still excludes. A crossing sends part of the L3 signal's
return current to L2, the analog blocks' reference, for the width of the crossing. This was
judged on paper and has not been measured.

## Widths and currents

IPC-2221 for a 10 °C rise, at the currents of CIRCUIT_DESIGN_Rev0.7.md: 1.221 A, the highest
over-current trip (D34), per port, and 2.46 A from J4 with both ports at it.

| Path | Current | Outer width for ΔT 10 °C | Drawn |
|---|---:|---:|---|
| J4's VBUS pads to F1 (VBUS_J4) | 2.46 A | 1.040 mm | 0.6 mm stubs with two vias per pad, then 2.5 mm on B.Cu |
| the joiner between a receptacle's two VBUS pads (J2, J3) | ≤ 0.61 A, half of a port's current | 0.152 mm | 0.25 mm on F.Cu under the connector body: 0.88 A at 10 °C, 21 °C at the port's full 1.221 A over its 1.2 mm stubs |
| F1 to each port switch (VBUS_IN) | 1.221 A | 0.396 mm | 1.5 / 1.0 mm (A), 3.0 / 1.0 mm (B) |
| a port path (SRC, VSUP, LAD1, VBUS) | 1.221 A | 0.396 mm | 0.6 mm at SOT-23 pads, 1.0–2.0 mm between; VBUS_B's trunk to J3 3.0 mm (D39) |
| LAD2 (MID range only) | ≤ 0.5 A (stuck MID, §4) | 0.396 mm | 0.5–0.6 mm |
| J1's VBUS, J1 to Q53 | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.20 mm, on F.Cu and B.Cu only (router class J1_POWER) |
| V5L, Q53 to the hub, U2, U5 and the dividers | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.31 mm on any layer (router class V5L_POWER); restricted to L1 and L4 it was left unconnected in every trial |
| V5L, C27 into U6 pin 26 (the hub's own V5) | 85 mA typical (CIRCUIT_DESIGN_Rev0.7.md §7.1) | below 0.051 mm | 0.20 mm on F.Cu, one track (route table): the pin is 0.20 mm wide at 0.4 mm pitch, so a 0.31 mm track would not clear its neighbours |

A 0.60/0.30 via passes about 1 A; a port path changes layer through two vias or more at each
end (three for VBUS). Inner layers carry no port current.

The copper of each port's HIGH-range path, from J4's two VBUS pads to the two VBUS pads of the
port's receptacle, is the sum of the nets below between their pads. A `+` joins the pads of one
receptacle into one node: the connector ties its VBUS contacts together, and the current splits
between the two pads by their paths. `check_routing.py` computes each by nodal analysis of the
tracks and vias (20 °C copper, 35 µm outer, 18 µm via plating over 1.6 mm) and holds the sum to
the `limit`, the 40 mΩ CIRCUIT_DESIGN_Rev0.7.md §3.1 allows for copper and connector contacts
together (see Not settled).

<!-- port_path:begin limit=40 -->
| Port | Net | From | To |
|---|---|---|---|
| A | VBUS_J4 | J4.A4+J4.B4 | F1.1 |
| A | VBUS_IN | F1.2 | Q10.3 |
| A | SRC_A | Q10.2 | Q11.2 |
| A | VSUP_A | Q11.3 | RS10.1 |
| A | LAD1_A | RS10.4 | Q17.2 |
| A | VBUS_A | Q17.3 | J2.A4+J2.B4 |
| B | VBUS_J4 | J4.A4+J4.B4 | F1.1 |
| B | VBUS_IN | F1.2 | Q30.3 |
| B | SRC_B | Q30.2 | Q31.2 |
| B | VSUP_B | Q31.3 | RS20.1 |
| B | LAD1_B | RS20.4 | Q37.2 |
| B | VBUS_B | Q37.3 | J3.A4+J3.B4 |
<!-- port_path:end -->

## High-speed pairs

USB_UP (U6 to J1), USB_A (U6 to J2) and USB_B (U6 to J3): W 0.31 mm, S 0.15 mm, so the
conductors' centres are 0.46 mm apart, on L1 over L2 (D27, provisional). Each leaves U6's
0.4 mm-pitch pads at 0.20 mm and widens to 0.31 mm within 1.7 mm of the pad. The N conductor is
on the right of the direction of travel from U6. No pair has a via and none leaves L1:
`check_routing.py` fails a pair net that has a via or a track on any other layer.

**The receptacle end (D37).** A receptacle's D+ and D− pads alternate at a 0.5 mm pitch: N, P, N,
P from west to east on J2 and J3 (B7, A6, A7, B6), and P, N, P, N on J1, which is turned through
180° (B6, A7, A6, B7). Tying the two N pads and the two P pads together would take a
crossing; the pairs take stubs instead, with no via and on L1 only:
- Each pair ends in a lane on the midline of its pads B7 and A6: x = 17.0 on J2, 82.0 on J3 and
  83.0 on J1 (D39). The 0.31 mm conductors stop 2.14 mm short of the pads' outer ends (y = 9.0, and
  y = 63.0 on J1), and 0.20 mm lead-ins, 2.5 mm long, take N to B7 and P to A6. Each lead-in
  lands 0.02 mm off the centre line of its pad.
- A7, the second N pad, joins B7 by a hop of 2.67 mm on the body side of the pad row, 0.16 mm
  from A6's inner end. There the copper lies under the connector body, covered by the solder
  mask only.
- B6, the second P pad, joins the lead-in of A6 by a branch of 2.64 mm on the lead-in side, 1.6 mm
  out from the pad centres. A stub of this length delays a pulse by about 16 ps each way
  (effective permittivity 3.2).
- The router's wire keepouts follow the 0.31 mm conductors, not the lead-ins, so CC1 and CC2 can
  leave pads A5 and B5 beside the lane; the lead-ins keep the board's 0.15 mm clearance. Its via
  keepout follows the lead-ins, hops and branches too (PAIR_LEAD_ANTIPAD, in the three port blocks
  that hold a receptacle with a pair). In the first trial a CC2 via of J2 and of J3 and a CC1 via
  of J1 stood 0.5–0.7 mm from the branch, and the antipad of each cut L2 under it to less than the
  0.30 mm of plane that `check_routing.py` asks beside a pair track.

**The taps (D38, issue #10).** R35–R38 stand on the straight runs of pairs A and B near U6, one
on each side of a pair, with pad 1 overlapping its own conductor's edge by 0.065 mm: the stub of a
tap is one resistor pad. Pair A's run is at x = 91.0, between R36.1 (N) and R35.1 (P); pair B's is
at x = 97.0, between R38.1 (N) and R37.1 (P). Pad 2 of each carries its TAP net to the RP2040, which
the router draws. Pair A runs at x = 90.4 from U6 to y = 21.9 and takes a 45° jog to
x = 91.0 at y = 21.3 (the chicane): at x = 91.0 its P conductor would pass 0.27 mm from the GND via
of Y2.4 (91.875, 22.65), and the fanout keeps 0.5 mm from a pair.

The `pairs` table holds each pair's centreline from its first bend away from U6 to the end of its
0.31 mm conductors. The router keeps 0.5 mm of copper away from the 0.31 mm conductors' edges on
L1 and L3, and keeps its vias' antipads 0.3 mm clear of their L2 footprint (keepouts below). These
keepouts follow the drawn conductors rather than the centreline. GND fanout keeps the same 0.5 mm.

**Skew.** The two conductors of a pair are matched in length. As drawn, the doc rows give
P − N = −0.80 mm (UP), −0.07 mm (A) and −0.00 mm (B), with every track of both nets counted;
`check_routing.py` holds every pair to 1.25 mm on the built board. The terms:
- A 90° bend, two 45° corners, makes its outer conductor 0.76 mm longer than its inner
  one, and N is the outer conductor of a left turn. Net of the bends, UP turns left once, A left
  once and B right once, so they give P − N = −0.76 mm (UP, A) and +0.76 mm (B). A's chicane is a
  left and a right corner, and cancels.
- At U6 the pin that must cross to the far conductor has the longer lead-in, by 0.73 mm: P's in A
  (pin 9 reaches the south conductor under N's lead-in) and N's in B (pin 13 reaches the south
  conductor under P's). That undoes the bends in A and B. UP's pins 20 and 21 leave east with equal
  lead-ins.
- The hop (2.670 mm) is 0.035 mm longer than the branch (2.635 mm).

<!-- pairs:begin -->
| Pair | P | N | Centreline | Why |
|---|---|---|---|---|
| UP | USB_UP_P | USB_UP_N | 97.3,28.0 97.8,28.5 97.8,57.0 97.3,57.5 83.5,57.5 83.0,58.0 83.0,63.0 | U6's east pins north along the east edge, then west along y = 57.5 to J1's lane |
| A | USB_A_P | USB_A_N | 90.9,24.0 90.4,23.5 90.4,21.9 91.0,21.3 91.0,18.4 90.5,17.9 17.5,17.9 17.0,17.4 17.0,9.0 | U6 south past the taps (x = 91.0), then west along y = 17.9 to J2's lane |
| B | USB_B_P | USB_B_N | 96.5,24.0 97.0,23.5 97.0,16.45 96.5,15.95 82.5,15.95 82.0,15.45 82.0,9.0 | U6 south past the taps (x = 97.0), then west along y = 15.95, below A, to J3's lane |
<!-- pairs:end -->

## Hand-drawn tracks

The pairs, the hub's crystal, the Kelvin taps, the port current paths and the VBUS pads of the
receptacles are drawn here; the router connects everything else, CC1 and CC2 of J1–J4 included. A few rows (their Why says so) are connections the router
left open in a trial: drawn here, they are fixed before it starts.

- **Kelvin taps (G2).** Each sense net is one straight 0.20 mm track on L1 from the shunt's
  sense pad to its amplifier resistor, with no via; it carries no load current.
- **Port paths.** The current enters each port at its switch (Q10/Q30), crosses R_H on
  RS10/RS20, and in the HIGH range returns to the port through the bypass FET Q17/Q37. R_M is
  through-hole, so LAD1 runs on L4 from its pad; LAD2 also runs on L4. VBUS_x crosses under the
  pairs on L4 and comes up through three vias beside pad B4 of the port's receptacle (D37); a
  0.25 mm joiner under the connector body ties pad A4 to pad B4, and the port capacitor C116
  (C216 on port B) takes its VBUS from the same vias.
- **VBUS_B's trunk (D39).** J2 stands in front of its front end, so VBUS_A's trunk is 16.8 mm
  long. J3 stands 31.2 mm east of channel B's front end since D39: VBUS_B leaves the lift vias
  at Q37 south, crosses under pair A on L4, runs east along y = 14.0, south of the pair, and
  reaches J3 under pair B's lane, 35.1 mm in all. For 29.8 mm of that it is 3.0 mm wide, which
  keeps port B's copper at 39.12 mΩ of the 40 mΩ (`port_path`; port A's is 35.24 mΩ).
  The pairs above it reference L2, which the trunk does not touch.
- **The corridor crossings (D39).** Pair A runs on L1 along y = 17.9 from U6 to J2's lane, across
  the board, and VBUS_B's trunk on L4 along y = 14.0. Between them lies a strip, y 15.9–16.8,
  where a via clears both: PAIR_ANTIPAD keeps its copper 0.5 mm from the pair's conductor, and
  the trunk's edge is at y = 15.5. A track from the north half of the board to a part south of
  the pair crosses the pair on L4, with L2 between them, changes layer in that strip, and
  crosses the trunk on L1 or L3. Five nets do: BTN_B, LED_ON_B and LED_FLT_B to OUT B's button
  and LED resistors, V12F to the MAU104's filter, and ADC_L_A, which Rev0.5 routed along the
  south edge, to U7. Each continues the open end of its carried track (*Carried from Rev0.5*)
  and is drawn here, before the router, so that the router cannot close the strip. In the first
  trial the trunk ran under the pair (y = 17.0) and the router laid V5L along y = 16.6:
  LED_ON_B, LED_FLT_B and ADC_L_A then had no path on any layer between x = 58.6 and the
  trunk's end (L1: the pair; L3: PAIR_COPLANAR keeps wires out from under a pair, and CLAUDE.md
  5.1 asks for GND on L4 below such a crossing; L4: the trunk). The rows were found by the
  search of *After the router*, on the board with the carried copper and no session. LED_ON_B's
  are drawn by hand, on L3 under R241 and up through a via at the end of R240's stub: the search
  took it on L1 between R241's pads. V12F's rows at R10, C7, C8 and TP3 are drawn with them: the
  router had left those four pads open.
- **The VBUS pads of J1 and J4 (D37).** Each of J4's two VBUS pads (A4, B4) has a 0.6 mm stub to a
  pair of vias, and a 1.5 mm trunk on L4 carries both to F1: 2.46 A, the current of both ports at
  their over-current trip. J1's pads B4 and A4 are joined by a 0.25 mm track under the connector
  body, and the router takes J1's 0.277 A from there to Q53.
- **VBUS_IN** leaves F1's pad on L1 toward port A and on L4 toward port B, so the corridor
  between the front ends and the MCU stays free on L1 for the control lines.
- **U1's escapes (issue #8, P4).** In every trial the router left some of U1's pins open, however
  its costs and keepouts were set: the 0.4 mm-pitch pads stand in a ring of decouplers, test
  pads and the crystal, and each wire laid there closes a lane for the next. The rows whose Why
  names a U1 pin draw those pins before the router starts: to their part where it is a few mm
  away, otherwise 0.4 mm to a via on a free spot (a 0.05 mm grid search with the obstacles of
  *After the router*), and the router joins the via. The 22 parts around U1 stand 0.4–0.8 mm
  further out for it (PLACEMENT_Rev0.7.md, *Deviations*). Rev0.5's router left five U1 pins
  open (BTN_B, LED_ON_B, LED_FLT_B, EVT_L_A and QSPI_SD3) and Rev0.5's patch joined them;
  Rev0.6 carries that copper where it still stands (*Carried from Rev0.5*).

<!-- route:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| USB_UP_N | F.Cu | 0.20 | U6.20 96.55,27.8 96.75,27.77 | U6 lead-in |
| USB_UP_P | F.Cu | 0.20 | U6.21 96.55,28.2 96.75,28.23 | U6 lead-in |
| USB_UP_N | F.Cu | 0.31 | 96.750,27.770 97.395,27.770 98.030,28.405 98.030,57.095 97.395,57.730 83.595,57.730 83.230,58.095 83.230,63.000 | coupled |
| USB_UP_P | F.Cu | 0.31 | 96.750,28.230 97.205,28.230 97.570,28.595 97.570,56.905 97.205,57.270 83.405,57.270 82.770,57.905 82.770,63.000 | coupled |
| USB_UP_N | F.Cu | 0.20 | 83.23,63.0 83.23,65.5 | lead-in to J1 B7 |
| USB_UP_P | F.Cu | 0.20 | 82.77,63.0 82.77,65.5 | lead-in to J1 A6 |
| USB_UP_N | F.Cu | 0.20 | J1.A7 82.25,66.55 83.25,66.55 J1.B7 | A7 to B7, on the body side |
| USB_UP_P | F.Cu | 0.20 | J1.B6 81.75,64.1 82.77,64.1 | B6 to the lead-in of A6, on the lead-in side |
| USB_A_N | F.Cu | 0.20 | U6.8 92.8,24.45 92.6,24.23 | U6 lead-in |
| USB_A_P | F.Cu | 0.20 | U6.9 93.2,24.2 92.77,23.77 92.6,23.77 | U6 lead-in |
| USB_A_N | F.Cu | 0.31 | 92.600,24.230 90.805,24.230 90.170,23.595 90.170,21.805 90.770,21.205 90.770,18.495 90.405,18.130 17.405,18.130 16.770,17.495 16.770,9.000 | coupled |
| USB_A_P | F.Cu | 0.31 | 92.600,23.770 90.995,23.770 90.630,23.405 90.630,21.995 91.230,21.395 91.230,18.305 90.595,17.670 17.595,17.670 17.230,17.305 17.230,9.000 | coupled |
| USB_A_N | F.Cu | 0.20 | 16.77,9.0 16.77,6.5 | lead-in to J2 B7 |
| USB_A_P | F.Cu | 0.20 | 17.23,9.0 17.23,6.5 | lead-in to J2 A6 |
| USB_A_N | F.Cu | 0.20 | J2.A7 17.75,5.45 16.75,5.45 J2.B7 | A7 to B7, on the body side |
| USB_A_P | F.Cu | 0.20 | J2.B6 18.25,7.9 17.23,7.9 | B6 to the lead-in of A6, on the lead-in side |
| USB_B_N | F.Cu | 0.20 | U6.13 94.8,24.2 95.23,23.77 95.4,23.77 | U6 lead-in |
| USB_B_P | F.Cu | 0.20 | U6.14 95.2,24.45 95.4,24.23 | U6 lead-in |
| USB_B_N | F.Cu | 0.31 | 95.400,23.770 96.405,23.770 96.770,23.405 96.770,16.545 96.405,16.180 82.405,16.180 81.770,15.545 81.770,9.000 | coupled |
| USB_B_P | F.Cu | 0.31 | 95.400,24.230 96.595,24.230 97.230,23.595 97.230,16.355 96.595,15.720 82.595,15.720 82.230,15.355 82.230,9.000 | coupled |
| USB_B_N | F.Cu | 0.20 | 81.77,9.0 81.77,6.5 | lead-in to J3 B7 |
| USB_B_P | F.Cu | 0.20 | 82.23,9.0 82.23,6.5 | lead-in to J3 A6 |
| USB_B_N | F.Cu | 0.20 | J3.A7 82.75,5.45 81.75,5.45 J3.B7 | A7 to B7, on the body side |
| USB_B_P | F.Cu | 0.20 | J3.B6 83.25,7.9 82.23,7.9 | B6 to the lead-in of A6, on the lead-in side |
| VBUS_J4 | F.Cu | 0.60 | J4.A4 19.9,63.5 | pad A4 down to its two vias |
| VBUS_J4 | via | 0.60/0.30 | 19.9,64.3 |  |
| VBUS_J4 | via | 0.60/0.30 | 19.9,63.5 |  |
| VBUS_J4 | F.Cu | 0.60 | J4.B4 15.1,63.5 | pad B4 down to its two vias |
| VBUS_J4 | via | 0.60/0.30 | 15.1,64.3 |  |
| VBUS_J4 | via | 0.60/0.30 | 15.1,63.5 |  |
| VBUS_J4 | B.Cu | 2.50 | 19.9,63.9 15.1,63.9 5.0,53.8 F1.1 | both pads to the fuse; F1.1 is through-hole |
| VBUS_J1 | F.Cu | 0.25 | 80.3,65.5 80.3,67.3 84.7,67.3 84.7,65.5 | pad B4 to pad A4, under the connector body |
| XI_HUB | F.Cu | 0.20 | U6.11 94,20.95 Y2.1 | the crystal, between Y2's pads |
| XO_HUB | F.Cu | 0.20 | U6.12 94.4,23.6 94.8,23.2 Y2.3 | the crystal |
| VDD33_HUB | F.Cu | 0.20 | U6.19 U6.18 96.55,27.0 96.8,26.75 | U6's pins 18 and 19, out past the unused pins 15-17 (the router left them open) |
| VDD33_HUB | via | 0.45/0.30 | 96.8,26.75 | 0.64 mm from the UP pair's conductor |
| VDD33_HUB | In2.Cu | 0.20 | 96.8,26.75 95.9,26.75 95.9,30.3 | under U6's east row, clear of the UP pair's keepout |
| VDD33_HUB | via | 0.45/0.30 | 95.9,30.3 | |
| VDD33_HUB | F.Cu | 0.20 | 95.9,30.3 TP13.1 | to the rest of VDD33_HUB at its test point |
| V5L | F.Cu | 0.20 | U6.26 C27.1 | U6's 5 V pin to its decoupler (the router left it open in every trial) |
| VBUS_IN | F.Cu | 1.50 | F1.2 8.2,50.1 3.44,50.1 | to port A's switch |
| VBUS_IN | F.Cu | 1.00 | 3.44,50.1 Q10.3 | |
| VBUS_IN | B.Cu | 3.00 | F1.2 10.1,50.2 37.24,50.2 37.24,48.7 | to port B's switch, under the corridor |
| VBUS_IN | B.Cu | 1.00 | 37.24,48.7 38.4,48.7 | |
| VBUS_IN | via | 0.60/0.30 | 37.24,48.7 | |
| VBUS_IN | via | 0.60/0.30 | 38.4,48.7 | |
| VBUS_IN | F.Cu | 0.80 | Q30.3 37.24,48.7 38.4,48.7 | |
| VBUS_IN | F.Cu | 1.00 | F1.2 11.6,53.3 14.2,53.3 D6.1 | the TVS after the fuse (D25) |
| VBUS_IN | F.Cu | 1.00 | 14.2,53.3 C1.1 | the bulk capacitor |
| VBUS_IN | F.Cu | 0.40 | C1.1 R7.1 | the V_J4 divider |
| VBUS_IN | F.Cu | 0.40 | TP8.1 F1.2 | the test point |
| XIN | F.Cu | 0.15 | 46.05,57.85 46.25,57.85 46.3,57.9 46.9,57.9 47.95,56.85 48.85,56.85 49.35,56.35 | XIN: U1 pin 20 to Y1 pin 1 |
| XIN | F.Cu | 0.15 | 49.6,55.2 49.35,54.95 49.35,54.5 | XIN: Y1 pin 1 to C25 |
| XTAL1_OUT | F.Cu | 0.15 | 48.7,58.75 49.6,59.65 49.6,61 49,61.6 48.6,61.6 | XTAL1_OUT: Y1 pin 3 to R24 |
| V3V3 | F.Cu | 0.15 | 46.05,58.65 46.25,58.65 47.1,59.5 | V3V3: U1 pin 22 to C14 |
| DVDD | F.Cu | 0.15 | 46.05,59.05 46.2,59.05 46.2,59.1 46.25,59.1 46.25,59.15 46.3,59.15 46.3,59.2 46.5,59.4 46.5,59.55 | DVDD: U1 pin 23 to C22, through L3 |
| DVDD | In2.Cu | 0.15 | 46.5,59.55 47.75,59.55 48,59.3 | DVDD: U1 pin 23 to C22, through L3 |
| DVDD | F.Cu | 0.15 | 48,59.3 48.25,59.55 | DVDD: U1 pin 23 to C22, through L3 |
| DVDD | via | 0.45/0.3 | 46.5,59.55 | DVDD: U1 pin 23 to C22, through L3 |
| DVDD | via | 0.45/0.3 | 48,59.3 | DVDD: U1 pin 23 to C22, through L3 |
| DVDD | F.Cu | 0.15 | 38.35,60.2 36.95,60.2 | DVDD: U1 pin 45 to C21 |
| DVDD | F.Cu | 0.15 | 38.35,58.15 38.15,58.15 36.9,56.9 | DVDD: U1 pin 50 to C23 |
| V3V3 | F.Cu | 0.15 | 43.15,62.25 43.15,63.45 42.9,63.7 | V3V3: U1 pin 33 to C15 |
| USB_MCU_P | F.Cu | 0.15 | 38.35,59.4 38.05,59.4 37.4,58.75 | USB_MCU_P: U1 pin 47 to R20, through L3 |
| USB_MCU_P | In2.Cu | 0.15 | 37.4,58.75 35.4,58.75 35.05,58.4 | USB_MCU_P: U1 pin 47 to R20, through L3 |
| USB_MCU_P | F.Cu | 0.15 | 35.05,58.4 34.75,58.7 | USB_MCU_P: U1 pin 47 to R20, through L3 |
| USB_MCU_P | via | 0.45/0.3 | 37.4,58.75 | USB_MCU_P: U1 pin 47 to R20, through L3 |
| USB_MCU_P | via | 0.45/0.3 | 35.05,58.4 | USB_MCU_P: U1 pin 47 to R20, through L3 |
| USB_MCU_N | F.Cu | 0.15 | 38.35,59.8 37.1,59.8 36.9,59.6 36.5,59.6 | USB_MCU_N: U1 pin 46 to R22, through L3 |
| USB_MCU_N | In2.Cu | 0.15 | 36.5,59.6 36.25,59.85 36.3,59.9 35.9,60.3 35.45,60.3 35,60.75 | USB_MCU_N: U1 pin 46 to R22, through L3 |
| USB_MCU_N | F.Cu | 0.15 | 35,60.75 35,60.5 34.9,60.4 | USB_MCU_N: U1 pin 46 to R22, through L3 |
| USB_MCU_N | via | 0.45/0.3 | 36.5,59.6 | USB_MCU_N: U1 pin 46 to R22, through L3 |
| USB_MCU_N | via | 0.45/0.3 | 35,60.75 | USB_MCU_N: U1 pin 46 to R22, through L3 |
| RUN | F.Cu | 0.15 | 46.05,60.25 46.2,60.25 46.35,60.4 46.35,63.4 46.05,63.7 | RUN: U1 pin 26 to R26 |
| SWCLK | F.Cu | 0.15 | 45.2,59.35 44.85,59.35 | SWCLK: U1 pin 24 to a via |
| SWCLK | via | 0.45/0.3 | 44.85,59.35 | SWCLK: U1 pin 24 to a via |
| SWDIO | F.Cu | 0.15 | 45.2,59.85 45.1,59.85 44.45,60.5 | SWDIO: U1 pin 25 to a via |
| SWDIO | via | 0.45/0.3 | 44.45,60.5 | SWDIO: U1 pin 25 to a via |
| DOUT_B_3V | F.Cu | 0.15 | 45.2,60.65 45,60.65 44.65,61 43.35,61 | DOUT_B_3V: U1 pin 27 to a via |
| DOUT_B_3V | via | 0.45/0.3 | 43.35,61 | DOUT_B_3V: U1 pin 27 to a via |
| LED_ON_A | F.Cu | 0.15 | 45.3,61.05 45.3,61.45 | LED_ON_A: U1 pin 28 to a via |
| LED_ON_A | via | 0.45/0.3 | 45.3,61.45 | LED_ON_A: U1 pin 28 to a via |
| OC_A | F.Cu | 0.15 | 40.35,54.55 40.35,54.2 | OC_A: U1 pin 3 to a via |
| OC_A | via | 0.45/0.3 | 40.35,54.2 | OC_A: U1 pin 3 to a via |
| HOLD_M_A | F.Cu | 0.15 | 41.15,55.35 41.15,55.75 | HOLD_M_A: U1 pin 5 to a via |
| HOLD_M_A | via | 0.45/0.3 | 41.15,55.75 | HOLD_M_A: U1 pin 5 to a via |
| HOLD_M_B | F.Cu | 0.15 | 43.95,54.55 43.95,54.2 | HOLD_M_B: U1 pin 12 to a via |
| HOLD_M_B | via | 0.45/0.3 | 43.95,54.2 | HOLD_M_B: U1 pin 12 to a via |
| BTN_A | F.Cu | 0.15 | 42.75,62.25 42.75,62.55 42.65,62.65 | BTN_A: U1 pin 34 to a via |
| BTN_A | via | 0.45/0.3 | 42.65,62.65 | BTN_A: U1 pin 34 to a via |
| TAP_A_P | F.Cu | 0.15 | 41.15,61.4 41.15,61.05 | TAP_A_P: U1 pin 38 to a via |
| TAP_A_P | via | 0.45/0.3 | 41.15,61.05 | TAP_A_P: U1 pin 38 to a via |
| VBUS_A | B.Cu | 1.80 | 20.9,7.9 26.33,7.9 26.33,19.25 | under the pairs, then to the lift vias at the receptacle |
| VBUS_A | via | 0.60/0.30 | 20.9,7.9 |  |
| VBUS_A | via | 0.60/0.30 | 21.7,7.9 |  |
| VBUS_A | via | 0.60/0.30 | 22.5,7.9 |  |
| VBUS_A | F.Cu | 0.60 | J2.B4 19.9,7.9 22.5,7.9 | pad B4 to the lift vias |
| VBUS_A | F.Cu | 0.60 | 19.9,7.9 19.9,9.0 | the port capacitor C116's pad 1 |
| VBUS_A | F.Cu | 0.25 | 15.3,5.9 15.3,4.7 19.7,4.7 19.7,5.9 | pad A4 to pad B4, under the connector body |
| VBUS_B | B.Cu | 1.80 | 60.13,19.25 60.13,18.2 | from the lift vias at Q37, south into the corridor (D39) |
| VBUS_B | B.Cu | 3.00 | 60.13,18.2 60.13,14.0 78.5,14.0 83.6,8.9 | south under pair A, east along y = 14.0, south of the pair, then under pair B's lane to J3 (D39); 3.0 mm wide, because the trunk is 35.1 mm long and port B's path has little to spare (port_path) |
| VBUS_B | B.Cu | 1.80 | 83.6,8.9 84.6,7.9 87.5,7.9 | to the lift vias at the receptacle |
| VBUS_B | via | 0.60/0.30 | 85.9,7.9 |  |
| VBUS_B | via | 0.60/0.30 | 86.7,7.9 |  |
| VBUS_B | via | 0.60/0.30 | 87.5,7.9 |  |
| VBUS_B | F.Cu | 0.60 | J3.B4 84.9,7.9 87.5,7.9 | pad B4 to the lift vias |
| VBUS_B | F.Cu | 0.60 | 84.9,7.9 84.9,9.0 | the port capacitor C216's pad 1 |
| VBUS_B | F.Cu | 0.25 | 80.3,5.9 80.3,4.7 84.7,4.7 84.7,5.9 | pad A4 to pad B4, under the connector body |
| LED_FLT_B | B.Cu | 0.2 | 64.55,70.3 64.55,16.75 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to R241 |
| LED_FLT_B | F.Cu | 0.2 | 64.55,16.75 64.55,13 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to R241 |
| LED_FLT_B | via | 0.45/0.3 | 64.55,16.75 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to R241 |
| BTN_B | B.Cu | 0.2 | 64.05,28.75 64.05,16.25 63.7,15.9 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to SW2 |
| BTN_B | F.Cu | 0.2 | 63.7,15.9 63.7,10.45 66.55,7.6 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to SW2 |
| BTN_B | via | 0.45/0.3 | 63.7,15.9 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to SW2 |
| LED_ON_B | B.Cu | 0.2 | 68.45,48.3 68.45,15.9 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, then on L3 over VBUS_B's trunk to R240 |
| LED_ON_B | via | 0.45/0.3 | 68.45,15.9 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, then on L3 over VBUS_B's trunk to R240 |
| LED_ON_B | In2.Cu | 0.2 | 68.45,15.9 64.5,11.95 64.5,10.5 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, then on L3 over VBUS_B's trunk to R240 |
| LED_ON_B | via | 0.45/0.3 | 64.5,10.5 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, then on L3 over VBUS_B's trunk to R240 |
| V12F | F.Cu | 0.2 | 59.4,9.35 59.4,10.55 | V12F at its moved parts (D39): R10, C7, C8 and TP3 |
| V12F | F.Cu | 0.2 | 57.65,9.7 58.25,10.3 58.8,10.3 | V12F at its moved parts (D39): R10, C7, C8 and TP3 |
| V12F | F.Cu | 0.2 | 61.55,10.9 60.2,10.9 | V12F at its moved parts (D39): R10, C7, C8 and TP3 |
| V12F | F.Cu | 0.2 | 57.6,4 57.6,8.9 | V12F at its moved parts (D39): from the end of the carried track to R11 |
| V12F | B.Cu | 0.2 | 63.55,28.7 63.55,18.25 62.05,16.75 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to TP3 |
| V12F | F.Cu | 0.2 | 62.05,16.75 62.05,11.25 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to TP3 |
| V12F | via | 0.45/0.3 | 62.05,16.75 | corridor crossing (D39): from the end of the carried track, on L4 under pair A, to TP3 |
| ADC_L_A | B.Cu | 0.2 | 59.7,4.35 59.4,4.65 59.4,6.1 65.25,11.95 | corridor crossing (D39): from the end of the carried track to U7, on L3 over VBUS_B's trunk and on L4 under pair A |
| ADC_L_A | In2.Cu | 0.2 | 65.25,11.95 69.6,16.3 | corridor crossing (D39): from the end of the carried track to U7, on L3 over VBUS_B's trunk and on L4 under pair A |
| ADC_L_A | B.Cu | 0.2 | 69.6,16.3 69.6,20.05 | corridor crossing (D39): from the end of the carried track to U7, on L3 over VBUS_B's trunk and on L4 under pair A |
| ADC_L_A | via | 0.45/0.3 | 65.25,11.95 | corridor crossing (D39): from the end of the carried track to U7, on L3 over VBUS_B's trunk and on L4 under pair A |
| ADC_L_A | via | 0.45/0.3 | 69.6,16.3 | corridor crossing (D39): from the end of the carried track to U7, on L3 over VBUS_B's trunk and on L4 under pair A |
<!-- route:end -->

<!-- channel_route:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| RH_SS_A | F.Cu | 0.20 | RS10.2 R119.1 | Kelvin tap |
| RH_SL_A | F.Cu | 0.20 | RS10.3 R121.1 | Kelvin tap |
| RM_SS_A | F.Cu | 0.20 | RS11.2 R125.1 | Kelvin tap |
| RM_SL_A | F.Cu | 0.20 | RS11.3 R127.1 | Kelvin tap |
| RL_SS_A | F.Cu | 0.20 | RS12.2 R131.1 | Kelvin tap |
| RL_SL_A | F.Cu | 0.20 | RS12.3 R133.1 | Kelvin tap |
| SRC_A | F.Cu | 1.20 | Q10.2 1.2,45.8 1.2,42.2 Q11.2 | between the switch FETs |
| SRC_A | F.Cu | 0.20 | R101.2 3.51,44.3 1.2,44.3 | R101's and Q16's source end, north round R101 to the trunk (the router left it open) |
| SRC_A | F.Cu | 0.20 | R101.2 4.288,43.15 Q16.2 | the source end of the gate network: R101, Q16 and R112 (the router left R112 open once) |
| SRC_A | F.Cu | 0.20 | 4.288,43.15 4.288,43.297 R112.2 | |
| GL_A | F.Cu | 0.20 | Q20.3 22.04,36.472 22.04,35.03 R118.1 | the gate network of the LOW range, as the router drew it for channel A (it left channel B open) |
| GL_A | F.Cu | 0.20 | 22.04,35.03 C111.1 23.195,35.125 U13.1 | |
| GL_A | F.Cu | 0.20 | R118.1 22.01,26.467 22.621,25.856 | |
| GL_A | via | 0.45/0.30 | 22.621,25.856 | |
| GL_A | In2.Cu | 0.20 | 22.621,25.856 26.037,25.856 | 2.9 mm from the LAD1 trunk on L4 |
| GL_A | via | 0.45/0.30 | 26.037,25.856 | |
| GL_A | F.Cu | 0.20 | 26.037,25.856 26.037,24.82 26.623,24.235 27.155,24.235 R114.1 | |
| GL_A | F.Cu | 0.20 | R114.1 27.275,23.085 Q18.1 | |
| VSUP_A | F.Cu | 0.60 | Q11.3 2.25,38.1 TP105.1 | |
| VSUP_A | F.Cu | 0.60 | 2.25,38.1 1.35,38.1 1.35,37.0 | to the vias |
| VSUP_A | F.Cu | 0.60 | 2.25,39.2 C101.2 | |
| VSUP_A | F.Cu | 0.40 | C101.2 C102.2 | |
| VSUP_A | via | 0.60/0.30 | 1.35,38.1 | |
| VSUP_A | via | 0.60/0.30 | 1.35,37.0 | |
| VSUP_A | B.Cu | 2.00 | 1.35,38.1 1.35,19.2 2.4,19.2 | down the left edge, under the mirrors |
| VSUP_A | via | 0.60/0.30 | 1.35,19.2 | |
| VSUP_A | via | 0.60/0.30 | 2.4,19.2 | |
| VSUP_A | F.Cu | 0.60 | 1.35,19.2 1.84,19.2 2.4,19.2 | |
| VSUP_A | F.Cu | 0.60 | 1.84,19.2 1.84,19.7 | 0.60 up to R_H's pad: channel B's copy lies over pair A, 0.615 mm from its N conductor |
| VSUP_A | F.Cu | 1.00 | 1.84,19.7 RS10.1 | into R_H |
| LAD1_A | F.Cu | 1.00 | RS10.4 RS11.1 | R_H to R_M |
| LAD1_A | B.Cu | 1.80 | RS11.1 9.78,23.0 27.6,23.0 28.1,22.6 28.1,21.4 | R_M's pad to the HIGH bypass FET |
| LAD1_A | via | 0.60/0.30 | 28.1,22.6 | |
| LAD1_A | via | 0.60/0.30 | 28.1,21.4 | |
| LAD1_A | F.Cu | 0.60 | 28.1,22.6 Q17.2 | |
| LAD1_A | F.Cu | 0.60 | 28.1,21.4 Q17.2 | |
| LAD2_A | F.Cu | 0.60 | RS11.4 RS12.1 | R_M to R_L |
| LAD2_A | B.Cu | 0.50 | RS11.4 24.06,21.0 24.66,21.6 | to the MID bypass FET |
| LAD2_A | via | 0.60/0.30 | 24.66,21.6 | |
| LAD2_A | F.Cu | 0.50 | 24.66,21.6 Q18.2 | |
| VBUS_A | F.Cu | 0.80 | RS12.4 23.72,19.75 26.33,19.75 27.6,19.75 28.9,19.75 29.86,19.75 Q17.3 | R_L's, Q18's and Q17's outputs |
| VBUS_A | F.Cu | 0.60 | 26.33,19.75 26.33,19.25 | |
| VBUS_A | F.Cu | 0.60 | 27.6,19.75 27.6,19.25 | |
| VBUS_A | F.Cu | 0.60 | 28.9,19.75 28.9,19.25 | |
| VBUS_A | via | 0.60/0.30 | 26.33,19.25 | 1.35 mm from pair A's centreline |
| VBUS_A | via | 0.60/0.30 | 27.6,19.25 | |
| VBUS_A | via | 0.60/0.30 | 28.9,19.25 | |
| VBUS_A | B.Cu | 1.00 | 26.33,19.25 27.6,19.25 28.9,19.25 | |
<!-- channel_route:end -->

## GND fanout

Every GND surface pad (SMD, or a connector pad without paste: J5's pad 5) reaches L2 in one of
two ways (`route.py`, `gnd_fanout`).

- **A stub to a plated GND hole of its own part**, where one is in reach: a 0.20 mm track on L1
  that leaves the pad's centre square to the hole's axis, ends 0.05 mm inside the hole's pad
  and is at most 1.0 mm long. The plane joins a plated pad solid, so the pad reaches L2 through
  the hole's wall, a much wider path than a 0.30 mm via. These are the receptacles' contact
  pads A1 and B1 (8 pads), each 0.675 mm from the rear shell slot beside it.
- **A via**, for every other pad: the board's via, the Default class's 0.45/0.30
  (`make_project.py`), on the nearest free spot (16 directions, outward from its part first,
  0.1 mm rings) and a 0.20 mm stub to it. The search keeps 0.15 mm from other copper, 0.5 mm
  from the HS pairs, 0.20 mm from another via's hole (JLCPCB's via figure, the custom rule
  `VIA_HOLE_TO_HOLE`), the board's 0.25 mm hole-to-hole minimum from a pad's hole, and 0.3 mm
  from the edge. A pad's hole is its whole shape: a plated slot is measured to its edge.

Each exposed pad gets five vias, at its centre and at the offset on the four axes, inside the
cross of its paste windows; the residual risk is solder wicking into them (V-MFG-03 inspects
U1 and U6).

**Why the stub (issues #8 and #13).** Until Rev0.5 the search read an oblong hole as a round
one of the drill's width at the pad's centre. The receptacles' plated shell slots (0.60 x
1.70 mm at the rear, 0.60 x 1.40 mm at the front, D37) are oblong: beside each rear slot the
search put the via of the contact pad A1 or B1 on the pad's own row, 0.046 mm from the slot's
hole, which JLCDFM called Danger (issue #8, 2026-11-13; 8 vias) and KiCad's DRC did not see.
Rev0.5's session had been routed around those vias, so its patch deleted them and drew the
stubs. No via fits there: with the slot as a capsule, no free spot existed within 3 mm of
J1.B1, and for J2.B1 and J3.B1 only across the slot, 1.9 mm from the pad (Rev0.5's board). Since
Rev0.6 the fanout draws the stub itself and the patch has no such rows. `check_routing.py`
rule 10 measures every pair of drilled holes with a slot as a capsule, by its own arithmetic.
Until issue #8 the via was 0.45/0.25 with 0.25 mm between all holes, the same 0.50 mm between
two via centres.

<!-- epad:begin -->
| Pad | Offset | Why |
|---|---:|---|
| U1.57 | 1.10 | RP2040's 3.20 mm ePad (G20) |
| U6.0 | 0.95 | CH335F's 2.7 mm ePad, vias to L2 (G21) |
<!-- epad:end -->

## Zones

<!-- zones:begin -->
| Zone | Net | Layer | Stage | Clearance | Min width | Pads | Priority | Why |
|---|---|---|---|---:|---:|---|---:|---|
| L2_GND | GND | In1.Cu | plane | 0.20 | 0.20 | solid | 0 | the solid plane under everything (CLAUDE.md 5.1) |
| L3_GND | GND | In2.Cu | pour | 0.20 | 0.20 | solid | 0 | L4's reference where L3 carries no track |
| L4_GND | GND | B.Cu | pour | 0.20 | 0.20 | thermal | 0 | L3's reference, around the L4 tracks |
<!-- zones:end -->

L1 carries no pour: the pairs' width was computed for a microstrip without coplanar ground
(D27), and between the 0402 parts a pour would leave islands. Every zone removes its islands.

## Carried from Rev0.5

Rev0.6 moves 31 of the 304 parts (D39): J3 with OUT B's port parts (C216, D3, Q33, R203, R204,
R209, R210), J1 with its CC and ESD parts and its soft start (D1, D5, R1, R2, C35–C37, Q53, R34,
TP14), the MAU104 with its filter (U5, C5–C8, R10, TP3), and OUT B's button and LEDs (SW2, D12,
D13, R240, R241). The copper of the other 273 parts stays as Rev0.5 routed it: the router session
and the patch table of Rev0.5, at the commit the table below names. `scripts/carry.py` reads both
from Git history, checks each against the table's SHA-256, and applies them to this revision's
board after the GND fanout, with the functions `make_pcb.py` uses for a session and a patch. Then
it drops what no longer stands, in rounds, until a round drops nothing:

- every carried track or via that KiCad's DRC names in a violation: a short to a pad of a moved
  part, a crossing with a track this document draws (VBUS_B's trunk and the corridor crossings lie
  where Rev0.5 had other runs), a clearance. The whole segment goes, not the part in the way;
- every carried cluster of connected tracks and vias that reaches no pad and no drawn item: what a
  dropped segment left floating.

A carried route that lost its far end stays, with an open end. The router continues from it, or the
patch table does, and the patch table takes away what nobody continued.

`carry.py` writes the result, `routing/carried.json`: the drawn items taken away and every carried
track and via that stands, in the board's nanometres. `make_pcb.py` applies it before it writes the
router input, so the router sees the carried copper as fixed wires and routes what is left open. It
refuses the record when the table below, or the board before the carry (its router input's
SHA-256), is not what the record was made from: run `carry.py`, then `autoroute.py`.
`carry.py --check` builds the record again and compares it with the file.

<!-- carry:begin commit=866ef440b5ad63606609d63caaa09a53cf7046db -->
| Item | Value | SHA-256 |
|---|---|---|
| session | design/ecad/routing/usb-power-hub.ses | c908c2349fcd4965ba991493cdb486820b2334d04959f8732a9f55e16bd9224a |
| patch | design/ecad/ROUTING_Rev0.5.md | 10abeae25a4f004327a07e2dd6e5db76f880a49386d23954b84c480db51299be |
| skip | Slot vias: | - |
<!-- carry:end -->

- `session` and `patch` are paths at that commit; the patch is the patch table of that file.
- `skip`: patch rows whose Why begins with this text are not carried. Rev0.5's *Slot vias* rows
  re-drew the GND stubs at the receptacles' rear slots; since Rev0.6 the GND fanout draws those
  stubs itself (*GND fanout*), and two of the receptacles moved.
- The carried patch's `remove` rows take away drawn items of this board too. Rev0.5's patch had
  replaced 18 tracks and vias of the route table at U1 (BTN_A, DOUT_B_3V, LED_ON_A, RUN, SWDIO,
  TAP_A_P, V3V3) by its own; the route table still draws them, and the record lists them under
  `remove`.

Counts (`carry.py` prints them, and `carried.json` holds the lists): Rev0.5's session adds 1,755
track segments and 142 vias, its patch (259 rows without the skipped ones) 578 and 86, after
taking 254 items away. Of those, 2,005 track segments and 205 vias stand on this board. 115 were
dropped: 40 that DRC named (shorts, crossings and clearances; KiCad does not split them by type
the same way in every run, so the record holds their number alone) and 75 that floated, of 19 nets
(VBUS_J1 20, V12F 16, CC2_B 15, GJ1 12, BTN_B 8, VBUS_B 8, V5L 6, CC2_J1 5, LED_ON_B 5,
LED_FLT_B 4, V12 4, ADC_L_A 2, DCH_B 2, DISG_B 2, GND 2, LEDA_FLT_B 1, LEDA_ON_B 1, TAP_B_P 1,
USB_P1_P 1). DRC counts 36 connections open on the board with the carried copper, before the
router.

Why carried, and not routed again. One router run on the Rev0.6 placement without the carried
copper (37 passes, with VBUS_B's trunk where the first trial had it, under pair A) left 40
connections open by DRC's count, most of them at U1, where Rev0.5 had needed its window re-route
(ROUTING_Rev0.5.md at the commit above, *After the router*). Carried, U1's exposed pad keeps the
plane webs Rev0.5 measured (N 1.66, E 1.70, S 1.65, W 1.80 mm), the analog blocks keep Rev0.5's
tracks, and the router and the patch have 36 connections to make instead of the whole board. None
of Rev0.5's JLCPCB evidence carries over with the copper: Rev0.6's files are new files.

## Router

Freerouting 2.5.0 (the jar and the JRE are named, with their SHA-256, in
`routing/autoroute.json`) routes what the tables above leave, from the board after the plane,
the hand-drawn tracks, the GND fanout and the carried record. `autoroute.py` exports that board's
DSN, adds the classes and keepouts below, runs the router with its optimizer off (it made the
result worse in every trial), and writes `routing/usb-power-hub.ses`. The router's own via is the
board's, 0.45/0.30.
The committed session is 8 passes (`autoroute.py --passes 8`, about 5 minutes). With the carried
copper fixed, more passes change nothing: the router's score was best after pass 2, no later pass
of 16 beat it, and it keeps the best board. Sessions of 3 and of 8 passes from one input were the
same bytes, and so were those of 8 and of 16 (measured on an earlier input of this revision, before
VBUS_B's trunk moved to y = 14.0; the committed input was run once, with 8 passes).
The router models a via by its copper circle alone; the drill appears only in the padstack's name.
KiCad's DSN export sizes the router's keepout around each NPTH hole with the board's
`min_hole_clearance`, so that minimum stays 0.25 mm, and the 0.20 mm figures for vias are custom
rules in `usb-power-hub.kicad_dru` (`make_project.py`, issue #8): a change to the board minimum
changes the router input.
With neck-down switched off the router still narrows a wire where it enters a 0.4 mm-pitch pin
(0.10–0.12 mm seen on this board); `--router.neck_width_um=150` holds such a neck at the
board's 0.15 mm minimum, so DRC's track-width rule holds. The full argument list is in
`autoroute.py` and is recorded with the session in `routing/autoroute.json`.

<!-- classes:begin -->
| Class | Nets | Width | Clearance | Via | Layers | Why |
|---|---|---:|---:|---|---|---|
| FS_LINK | USB_P1_N USB_P1_P USB_P1M_N USB_P1M_P USB_MCU_N USB_MCU_P | 0.20 | 0.20 | - | all | the MCU's Full-Speed link to the hub: 12 Mb/s, not impedance-controlled |
| J1_POWER | VBUS_J1 | 0.20 | 0.15 | - | F.Cu,B.Cu | J1's whole 0.277 A: 0.20 mm of outer copper rises 1 °C, of inner copper 20 °C |
| V5L_POWER | V5L | 0.31 | 0.15 | - | all | the same 0.277 A after the soft start, to loads all over the board: 0.31 mm carries it on L3 too (Widths) |
<!-- classes:end -->

The router's layer preferences, written into its input as its autoroute settings. L3 and L4
prefer crossing directions, so where it lays an L3 track over an L4 track they mostly cross
(D36): in the analog blocks the parallel overlaps fell from 16 to 4 (two runs of one input,
without and with these rows).

<!-- router_layers:begin -->
| Layer | Direction | Against | Why |
|---|---|---:|---|
| In2.Cu | horizontal | 4.0 | the cost of a track against the preferred direction, ×1.0 along it |
| B.Cu | vertical | 4.0 | |
<!-- router_layers:end -->

Its costs, beside the defaults. Four runs of the Rev0.4 input (commit `5a697aa`, not run again
for Rev0.5), with the layer rows above, left by DRC's count: 6 connections unrouted at the
default via cost, 6 with the layer cost at 2.0, 11 with a cheaper rip-up, 2 with vias dearer.

<!-- router_costs:begin -->
| Setting | Value | Why |
|---|---:|---|
| via_costs | 100 | the cost of a via against a track; dearer vias kept more connections on one layer near U1 |
<!-- router_costs:end -->

The plane under the router's vias. On L2 a via of a net other than GND stands in an antipad of
its copper plus the zone's clearance each side, 0.85 mm for the 0.45 mm via, and the fill drops
plane copper narrower than its 0.20 mm minimum. Two such vias closer than 1.05 mm, centre to
centre, therefore make one void, and a row of them makes a slot. The router knows no antipad:
it stood vias 0.62 mm apart, and around U1 they joined into a slot 5.04 mm long that left the
exposed pad no plane copper on its east side (measured on the first Rev0.5 session, which was
not kept; `check_routing.py` rule 9 now measures it on every board). Two rules give the router
the antipad:

- `plane_via`: in the router's input every via padstack is this much larger on In1.Cu, 1.05 mm
  for the 0.45 mm via. 0.60 = 2 × 0.20 (the antipad) + 0.35 (the plane copper wanted between two
  antipads) − 0.15 (the router's own clearance). Vias of different nets then stand 1.20 mm or
  more apart. No track is on In1.Cu, so this costs no routing channel. One router pass on the
  earlier input: 48 pairs of vias closer than 1.20 mm before, none after (closest 1.232 mm).
- `PLANE_HOLES`: no via on In1.Cu within 0.45 mm of the copper or the hole of a drilled pad that
  is not on GND. 0.45 = 0.20 (the pad's antipad) + (0.35 + 0.15) / 2, which leaves the same
  0.35 mm between the pad's antipad and the via's, counting no clearance of the router's.

A GND via has no antipad. The vias this document and the GND fanout place on GND therefore keep
the padstack as KiCad wrote it (a copy named `..._gnd` in the router's input), and a signal via
may stand 0.60 mm from one. A GND via the router adds itself is not told apart and keeps the
larger distance, which costs room and breaks nothing.

The router may put its vias anywhere between U1's pads and its exposed pad: the two rules
above are what keep plane copper there. A ring keepout that allowed a via only in twelve windows,
three on each side, was tried and dropped: it left the north side of the exposed pad 1.51 mm of
plane copper, under rule 9's 1.60 mm (50 % of the pad's 3.20 mm), and 33 connections open
against 24 without it (one router run each).

<!-- keepouts:begin analog=AFE_A,AFE_B,ADC,ADCSUP,REF plane_via=0.60 -->
| Keepout | Layers | Kind | Around | Buffer | Why |
|---|---|---|---|---|---|
| PLANE_HOLES | In1.Cu | via_keepout | drilled-pads | pad+0.45 | plane copper between a drilled pad's antipad and a via's (above) |
| PAIR_COPLANAR | F.Cu,In2.Cu | wire_keepout | pair-tracks | w/2+0.5 | 0.5 mm beyond the edges of each 0.31 mm pair conductor |
| PAIR_ANTIPAD | signal | via_keepout | pair-tracks | w/2+0.5 | the router keeps the via's copper out: the conductor's edge, + the 0.20 antipad of L2, + 0.30 of plane between antipad and conductor |
| PAIR_LEAD_ANTIPAD | signal | via_keepout | pair-leads in PORT_A PORT_B PORT_HOST | w/2+0.5 | the same distance from the 0.20 mm lead-ins, hops and branches at the receptacles; a wire may pass, so CC1 and CC2 leave their pads. U6's lead-ins are left out, as they are in the check, which does not look at L2 within 1.5 mm of an end part's pad |
| TRUNK_L3 | In2.Cu | wire_keepout | B.Cu-rows in analog | w/2+0.3 | no L3 track above an L4 trunk inside the analog blocks: D36 lets an L3 signal cross an L4 signal, and a trunk is wider and carries current, so L3 stays off it |
<!-- keepouts:end -->

## After the router

The committed session adds 251 track segments and 1 via to the carried copper: 207.7 mm on 46
nets, of which V5L takes 65.2 mm, VBUS_J1 25.9 mm and USB_P1_P 22.3 mm. 204 of the segments are
shorter than 1.0 mm, many on nets DRC had counted complete before the router, and two repeat a
carried AMP_L_A segment exactly: same-net copper on copper, which DRC accepts. Why the router
draws them was not looked into; its own count of unrouted connections (99, in
`routing/autoroute.json`) is not DRC's either. The session leaves 9
connections unrouted (DRC's count of unconnected items) and 10 dangling-track warnings, and no
place in the analog blocks where an L3 track runs along an L4 track (D36). The L2 plane is as
Rev0.5's patch left it, because neither the session nor the patch puts a via at U1: the webs of
U1's exposed pad are N 1.66, E 1.70, S 1.65 and W 1.80 mm (rule 9 asks 1.60 mm) and the longest
void is 2.81 mm. `make_pcb.py` draws the patch table on the board after the session and before
the zones are filled. At each point of a `remove` row, the via of its net centred exactly there is
deleted (such a point is the via's position to 7 decimals, as KiCad wrote it), or else every track
of its net through the point. The other rows draw tracks and vias as the route table does. The 42
rows, 10 `remove` and 32 drawn, take 24 track segments away, draw 33 and 12 vias, and leave 0
unconnected items, 0 DRC violations and no D36 place.

The Why column names the stage that wrote a row. The two stages ran in this order, the second on
the board the first left, on a 0.05 mm grid, with every other net's copper, the DSN keepouts and
D36 as obstacles:

1. **Tails.** Seven of the dangling tracks are carried copper that ends where a moved part stood:
   five of GND, at the old places of J3's and of J1's parts, one of V5L (0.23 mm, at Q53's old
   place) and one of LED_FLT_B (1.45 mm, beside the corridor crossing that replaces it). The carry keeps a
   route that lost its far end (*Carried from Rev0.5*); nobody continued these, so each is taken
   away back to the next via, pad or junction.
2. **Moved parts.** The 9 open connections are at the parts D39 moved: V5L at C35 and Q53 (two),
   J1's CC lines at D1, R1 and R2 (CC1_J1 two, CC2_J1 one), CC2_B at J3's pad B5, EN_B at R203 and
   R204, DIS_B at R209, and TAP_B_P, whose straight L1 run of Rev0.5 crossed the place where Q53
   and C35 now stand. Each is one search from the pad, or from the open end of the carried route
   (EN_B: of the 5.3 mm the router drew), to the rest of its net. Three are long: EN_B 31.0 mm (20.3 mm of it on L3 along y = 8.9), DIS_B
   34.0 mm (on L3 between VBUS_B's trunk and pair A, then on L4 under pair B) and TAP_B_P 24.2 mm
   (on L3 under Q53, 1.2 mm beside the line Rev0.5 had it on L1). See *Not settled*, *Long routes*.

Rev0.5's own patch (its window re-route north of U1, the joins at U1, the analog blocks) is not in
this table: it is carried, with Rev0.5's session, by the record (*Carried from Rev0.5*).

The program that wrote the rows (an exact-obstacle search that also takes dead ends away) is a
scratch tool and is not in the repository. The table is its output, and `check_routing.py`, not
the tool, accepts it.

The table belongs to the carried record and to the session whose SHA-256 `routing/autoroute.json`
records. A new record or a new session moves the tracks its rows name, and a `remove` row that
finds nothing stops `make_pcb.py`. After either, rewrite the table.

<!-- patch:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| GND | remove | - | 47.4858,8.9 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 48.5496,10.0621 48.2617,9.3371 49.1559,8.0059 50.05,6.6983 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 69.1157,60.7257 69.9175,61.0514 70.4096,61.0353 70.5076,60.9373 70.7263,60.8752 71.0736,60.6845 72.2619,60.4938 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 73.2594,60.5719 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 74.5986,57.8319 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 75.9387,56.4927 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 76.4948,56.0704 | Tails: a carried track that ends where a moved part stood |
| GND | remove | - | 77.25,65.1539 77.5106,64.3321 77.7713,63.1277 | Tails: a carried track that ends where a moved part stood |
| V5L | remove | - | 75.5825,52.03 | Tails: a carried track that ends where a moved part stood |
| LED_FLT_B | remove | - | 65.375,14.8 | Tails: a carried track that ends where a moved part stood |
| V5L | F.Cu | 0.31 | 84.35,51.8 84.35,50.85 | Moved parts: V5L to C35 and Q53 beside J1 (D39) |
| V5L | F.Cu | 0.31 | 82,51.95 82,50.85 | Moved parts: V5L to C35 and Q53 beside J1 (D39) |
| CC1_J1 | F.Cu | 0.2 | 79.7,60.7 79.1,61.3 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC1_J1 | B.Cu | 0.2 | 79.1,61.3 84.1,66.3 84.1,66.7 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC1_J1 | F.Cu | 0.2 | 84.1,66.7 83.8,66.4 83.8,65.85 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC1_J1 | via | 0.45/0.3 | 79.1,61.3 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC1_J1 | via | 0.45/0.3 | 84.1,66.7 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC1_J1 | F.Cu | 0.2 | 75.4,60.3 75.9,59.8 78.55,59.8 79.15,60.4 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_J1 | F.Cu | 0.2 | 75.35,62.9 75.8,63.35 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_J1 | In2.Cu | 0.2 | 75.8,63.35 79.55,63.35 79.7,63.2 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_J1 | F.Cu | 0.2 | 79.7,63.2 79.7,62.8 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_J1 | via | 0.45/0.3 | 75.8,63.35 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_J1 | via | 0.45/0.3 | 79.7,63.2 | Moved parts: J1's CC lines to D1, R1 and R2 (D39) |
| CC2_B | F.Cu | 0.2 | 84.2,6.15 84.2,5.4 84.15,5.35 | Moved parts: J3's CC2 to D3 and R204 (D39) |
| CC2_B | B.Cu | 0.2 | 84.15,5.35 78.9,10.6 | Moved parts: J3's CC2 to D3 and R204 (D39) |
| CC2_B | F.Cu | 0.2 | 78.9,10.6 79.35,11.05 79.35,12 | Moved parts: J3's CC2 to D3 and R204 (D39) |
| CC2_B | via | 0.45/0.3 | 84.15,5.35 | Moved parts: J3's CC2 to D3 and R204 (D39) |
| CC2_B | via | 0.45/0.3 | 78.9,10.6 | Moved parts: J3's CC2 to D3 and R204 (D39) |
| EN_B | In2.Cu | 0.2 | 45.7,8.9 65.95,8.9 | Moved parts: EN_B from the open end the router left to R203 and R204 (D39) |
| EN_B | F.Cu | 0.2 | 65.95,8.9 76.65,8.9 | Moved parts: EN_B from the open end the router left to R203 and R204 (D39) |
| EN_B | via | 0.45/0.3 | 45.7,8.9 | Moved parts: EN_B from the open end the router left to R203 and R204 (D39) |
| EN_B | via | 0.45/0.3 | 65.95,8.9 | Moved parts: EN_B from the open end the router left to R203 and R204 (D39) |
| DIS_B | F.Cu | 0.2 | 55.3,13.2 57.5,15.4 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | In2.Cu | 0.2 | 57.5,15.4 67.25,15.4 68.65,16.8 79.6,16.8 80.45,15.95 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | B.Cu | 0.2 | 80.45,15.95 83.15,13.25 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | F.Cu | 0.2 | 83.15,13.25 86.35,13.25 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | via | 0.45/0.3 | 57.5,15.4 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | via | 0.45/0.3 | 80.45,15.95 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| DIS_B | via | 0.45/0.3 | 83.15,13.25 | Moved parts: DIS_B from the end of the carried track to R209 (D39) |
| TAP_B_P | F.Cu | 0.2 | 80.05,55.85 80.05,54.2 | Moved parts: TAP_B_P from the end of the carried track to R37 (D39) |
| TAP_B_P | In2.Cu | 0.2 | 80.05,54.2 84.7,49.55 88.35,45.9 95.1,39.15 96.35,39.15 | Moved parts: TAP_B_P from the end of the carried track to R37 (D39) |
| TAP_B_P | via | 0.45/0.3 | 80.05,54.2 | Moved parts: TAP_B_P from the end of the carried track to R37 (D39) |
<!-- patch:end -->

## Not settled

- **Port voltage.** CIRCUIT_DESIGN_Rev0.7.md §3.1 allows about 40 mΩ for the copper and the
  contacts of a port path; `check_routing.py` computes the board copper alone (J4's two VBUS
  pads to the two VBUS pads of the port's receptacle, HIGH range). The contacts of the two
  receptacles and of the plugs are the connector's rating and are not known on paper.
- **One GND net.** CLAUDE.md 5.4 asks for a quiet ADC ground with one defined tie; Rev0.6 has
  one GND net and no net tie, so the ADC shares L2. The port return currents run from J2/J3 to
  J4 west of the ADC block.
- **The HS pairs' impedance** stays D27's model value until JLCPCB's differential calculator
  answers; the receptacle pads, the hop and the branch in each path are OI-26's, with the taps'
  stubs (D38).
- **Copper under the receptacle bodies.** The hop of each N conductor, the joiner between the two
  VBUS pads of J1–J3 and the receptacle's own pads lie under its body, covered by the solder mask
  alone; a wrong pad or shell contact there is a short that only the first board shows (V-MFG-03,
  V-MECH-01).
- **D36's crossings.** Where an L3 signal crosses an L4 signal in the analog blocks, its return
  current leaves L4 for the crossing's width. `check_routing.py` holds every such pair to 45° or
  more and counts them; their effect on the measurement is not computed and is not measured
  until V-MEAS-01 on the first board.
- **Thin webs at U1.** With Rev0.5's copper carried, U1's exposed pad keeps 1.66 mm of plane
  copper on its north side and 1.65 mm on its south, 0.06 and 0.05 mm over rule 9's 1.60 mm (east
  1.70, west 1.80). A row added near U1 later can break it; `make_pcb.py` fails when a web falls
  under the limit. Rule 9 reads the 2-D copper of L2, not the return currents.
- **Port B's margin.** Port B's copper is 39.12 mΩ of the 40 mΩ, 0.88 mΩ to spare, with the trunk
  3.0 mm wide (port A: 35.24 mΩ). D39 put J3 on the far side of the board from Q37, and the trunk
  is 35.1 mm long for it. A change to VBUS_B's rows can break the limit; `check_routing.py` fails
  when it does. The 40 mΩ is copper and contacts together (*Port voltage*, above).
- **Long routes.** The patches, Rev0.5's and this one, join what the router left open where they
  found room, not by the shortest way. V_INJ runs 90.8 mm with 8 vias, BTN_B 80.3 mm, LED_ON_B
  84.0 mm and LED_FLT_B 90.8 mm, and the four taps TAP_A_P, TAP_A_N, TAP_B_P and TAP_B_N
  103.3–111.2 mm (102.9–110.6 mm in Rev0.5). D39 lengthened two of port B's control lines,
  because U1 stays in the west and their parts moved east with J3: EN_B is 88.9 mm (52.7 mm in
  Rev0.5) and DIS_B 83.5 mm (49.4 mm). Both are static while a port measures. The taps sit behind
  their 1 kΩ resistors, so the pairs carry no stub beyond a pad, but what the wire's capacitance
  does to a 12 Mbit/s edge is not computed, and CIRCUIT_DESIGN_Rev0.7.md §3.3 sets no length
  limit. `check_routing.py` has no length rule.
- **L3 beside what it should stay off.** Three places this revision's rows add, each outside what
  a rule of this document forbids, none computed: DIS_B runs on L3 for 9.8 mm along y = 15.4,
  across the 3.0 mm leg of VBUS_B's L4 trunk at x = 60.13 and then for 5.6 mm over the north edge
  of its run along y = 14.0 (that band ends at y = 15.5; `TRUNK_L3` keeps L3 off a trunk only
  inside the analog blocks), and passes ADC_L_A's via at 69.6, 16.3 with 0.175 mm of clearance;
  TAP_B_P crosses the north-east corner of the ADC's supply block on L3 for 5.0 mm,
  under C10 with the L2 plane between, where Rev0.5 crossed it on L1; LED_ON_B and ADC_L_A cross
  the trunk on L3 at 45°. V-MEAS-01 on the first board is where an effect on the reading would
  show.
