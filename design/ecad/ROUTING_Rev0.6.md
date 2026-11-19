# USB Power-Control Hub — Rev0.6 routing

> **WIP — MANUFACTURING PROHIBITED.** How the placed Rev0.6 board (PLACEMENT_Rev0.6.md) is
> routed, and why. Issue #6 P4, reworked for the machine-placed receptacles and the data-line
> taps (issues #8 and #10, D37 and D38). Nothing here has been built or measured.

`design/ecad/scripts/make_pcb.py` builds `source/usb-power-hub.kicad_pcb` from the placement,
this file and the committed router session in `routing/`; `scripts/autoroute.py` writes that
session; `scripts/check_routing.py` checks the board against this file and runs DRC
(`design/ecad/README.md`). Change a track here, never in KiCad: the next run of `make_pcb.py`
rebuilds the board.

## Frame and format

- The board frame of PLACEMENT_Rev0.6.md: origin at the lower-left corner, x right, y up, in mm;
  a board point (x, y) is at (50 + x, 122 − y) on KiCad's sheet.
- A point is `x,y` or `REF.PAD`, the pad's centre; a pad point must be on the row's net.
- A track row draws one track through its points on one layer, at one width. A `via` row places
  one through via (diameter/drill) at its one point.
- `channel_route` rows are channel A's. Channel B gets the same rows moved by the placement's
  `dx` (33.8 mm), each part mapped by the placement's channel table (J2 → J3) and `_A` → `_B`
  in the net names.

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

IPC-2221 for a 10 °C rise, at the currents of CIRCUIT_DESIGN_Rev0.6.md: 1.221 A, the highest
over-current trip (D34), per port, and 2.46 A from J4 with both ports at it.

| Path | Current | Outer width for ΔT 10 °C | Drawn |
|---|---:|---:|---|
| J4's VBUS pads to F1 (VBUS_J4) | 2.46 A | 1.040 mm | 0.6 mm stubs with two vias per pad, then 2.5 mm on B.Cu |
| the joiner between a receptacle's two VBUS pads (J2, J3) | ≤ 0.61 A, half of a port's current | 0.152 mm | 0.25 mm on F.Cu under the connector body: 0.88 A at 10 °C, 21 °C at the port's full 1.221 A over its 1.2 mm stubs |
| F1 to each port switch (VBUS_IN) | 1.221 A | 0.396 mm | 1.5 / 1.0 mm (A), 3.0 / 1.0 mm (B) |
| a port path (SRC, VSUP, LAD1, VBUS) | 1.221 A | 0.396 mm | 0.6 mm at SOT-23 pads, 1.0–2.0 mm between |
| LAD2 (MID range only) | ≤ 0.5 A (stuck MID, §4) | 0.396 mm | 0.5–0.6 mm |
| J1's VBUS, J1 to Q53 | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.20 mm, on F.Cu and B.Cu only (router class J1_POWER) |
| V5L, Q53 to the hub, U2, U5 and the dividers | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.31 mm on any layer (router class V5L_POWER); restricted to L1 and L4 it was left unconnected in every trial |
| V5L, C27 into U6 pin 26 (the hub's own V5) | 85 mA typical (CIRCUIT_DESIGN_Rev0.6.md §7.1) | below 0.051 mm | 0.20 mm on F.Cu, one track (route table): the pin is 0.20 mm wide at 0.4 mm pitch, so a 0.31 mm track would not clear its neighbours |

A 0.60/0.30 via passes about 1 A; a port path changes layer through two vias or more at each
end (three for VBUS). Inner layers carry no port current.

The copper of each port's HIGH-range path, from J4's two VBUS pads to the two VBUS pads of the
port's receptacle, is the sum of the nets below between their pads. A `+` joins the pads of one
receptacle into one node: the connector ties its VBUS contacts together, and the current splits
between the two pads by their paths. `check_routing.py` computes each by nodal analysis of the
tracks and vias (20 °C copper, 35 µm outer, 18 µm via plating over 1.6 mm) and holds the sum to
the `limit`, the 40 mΩ CIRCUIT_DESIGN_Rev0.6.md §3.1 allows for copper and connector contacts
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
- Each pair ends in a lane on the midline of its pads B7 and A6: x = 17.0 on J2, 50.8 on J3 and
  76.5 on J1. The 0.31 mm conductors stop 2.14 mm short of the pads' outer ends (y = 9.0, and
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
| UP | USB_UP_P | USB_UP_N | 97.3,28.0 97.8,28.5 97.8,57.0 97.3,57.5 77.0,57.5 76.5,58.0 76.5,63.0 | U6's east pins north along the east edge, then west along y = 57.5 to J1's lane |
| A | USB_A_P | USB_A_N | 90.9,24.0 90.4,23.5 90.4,21.9 91.0,21.3 91.0,18.4 90.5,17.9 17.5,17.9 17.0,17.4 17.0,9.0 | U6 south past the taps (x = 91.0), then west along y = 17.9 to J2's lane |
| B | USB_B_P | USB_B_N | 96.5,24.0 97.0,23.5 97.0,16.45 96.5,15.95 51.3,15.95 50.8,15.45 50.8,9.0 | U6 south past the taps (x = 97.0), then west along y = 15.95, below A, to J3's lane |
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
  further out for it (PLACEMENT_Rev0.6.md, *Deviations*). Five U1 pins are still open after the
  router (BTN_B, LED_ON_B, LED_FLT_B, EVT_L_A and QSPI_SD3), and the patch joins them
  (*After the router*).

<!-- route:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| USB_UP_N | F.Cu | 0.20 | U6.20 96.55,27.8 96.75,27.77 | U6 lead-in |
| USB_UP_P | F.Cu | 0.20 | U6.21 96.55,28.2 96.75,28.23 | U6 lead-in |
| USB_UP_N | F.Cu | 0.31 | 96.750,27.770 97.395,27.770 98.030,28.405 98.030,57.095 97.395,57.730 77.095,57.730 76.730,58.095 76.730,63.000 | coupled |
| USB_UP_P | F.Cu | 0.31 | 96.750,28.230 97.205,28.230 97.570,28.595 97.570,56.905 97.205,57.270 76.905,57.270 76.270,57.905 76.270,63.000 | coupled |
| USB_UP_N | F.Cu | 0.20 | 76.73,63.0 76.73,65.5 | lead-in to J1 B7 |
| USB_UP_P | F.Cu | 0.20 | 76.27,63.0 76.27,65.5 | lead-in to J1 A6 |
| USB_UP_N | F.Cu | 0.20 | J1.A7 75.75,66.55 76.75,66.55 J1.B7 | A7 to B7, on the body side |
| USB_UP_P | F.Cu | 0.20 | J1.B6 75.25,64.1 76.27,64.1 | B6 to the lead-in of A6, on the lead-in side |
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
| USB_B_N | F.Cu | 0.31 | 95.400,23.770 96.405,23.770 96.770,23.405 96.770,16.545 96.405,16.180 51.205,16.180 50.570,15.545 50.570,9.000 | coupled |
| USB_B_P | F.Cu | 0.31 | 95.400,24.230 96.595,24.230 97.230,23.595 97.230,16.355 96.595,15.720 51.395,15.720 51.030,15.355 51.030,9.000 | coupled |
| USB_B_N | F.Cu | 0.20 | 50.57,9.0 50.57,6.5 | lead-in to J3 B7 |
| USB_B_P | F.Cu | 0.20 | 51.03,9.0 51.03,6.5 | lead-in to J3 A6 |
| USB_B_N | F.Cu | 0.20 | J3.A7 51.55,5.45 50.55,5.45 J3.B7 | A7 to B7, on the body side |
| USB_B_P | F.Cu | 0.20 | J3.B6 52.05,7.9 51.03,7.9 | B6 to the lead-in of A6, on the lead-in side |
| VBUS_J4 | F.Cu | 0.60 | J4.A4 19.9,63.5 | pad A4 down to its two vias |
| VBUS_J4 | via | 0.60/0.30 | 19.9,64.3 |  |
| VBUS_J4 | via | 0.60/0.30 | 19.9,63.5 |  |
| VBUS_J4 | F.Cu | 0.60 | J4.B4 15.1,63.5 | pad B4 down to its two vias |
| VBUS_J4 | via | 0.60/0.30 | 15.1,64.3 |  |
| VBUS_J4 | via | 0.60/0.30 | 15.1,63.5 |  |
| VBUS_J4 | B.Cu | 2.50 | 19.9,63.9 15.1,63.9 5.0,53.8 F1.1 | both pads to the fuse; F1.1 is through-hole |
| VBUS_J1 | F.Cu | 0.25 | 73.8,65.5 73.8,67.3 78.2,67.3 78.2,65.5 | pad B4 to pad A4, under the connector body |
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
| VBUS_A | B.Cu | 1.80 | 20.9,7.9 26.33,7.9 26.33,19.25 | under the pairs, then to the lift vias at the receptacle |
| VBUS_A | via | 0.60/0.30 | 20.9,7.9 |  |
| VBUS_A | via | 0.60/0.30 | 21.7,7.9 |  |
| VBUS_A | via | 0.60/0.30 | 22.5,7.9 |  |
| VBUS_A | F.Cu | 0.60 | J2.B4 19.9,7.9 22.5,7.9 | pad B4 to the lift vias |
| VBUS_A | F.Cu | 0.60 | 19.9,7.9 19.9,9.0 | the port capacitor C116's pad 1 |
| VBUS_A | F.Cu | 0.25 | 15.3,5.9 15.3,4.7 19.7,4.7 19.7,5.9 | pad A4 to pad B4, under the connector body |
<!-- channel_route:end -->

## GND fanout

Every GND surface pad (SMD, or a connector pad without paste: J5's pad 5) gets the board's via,
the Default class's 0.45/0.30 (`make_project.py`; eight of them are deleted again, below), to L2
on the nearest free spot (16 directions, outward
from its part first, 0.1 mm rings) and a 0.20 mm stub to it; the search keeps 0.15 mm from other
copper, 0.5 mm from the HS pairs, 0.20 mm from another via's hole (JLCPCB's via figure, the
custom rule `VIA_HOLE_TO_HOLE`), the board's 0.25 mm hole-to-hole minimum from a pad's hole, and
0.3 mm from the edge. Until issue #8 the via was 0.45/0.25 with 0.25 mm between all holes: the same
0.50 mm between two via centres. The router input of issue #8 equals the one before it except for
the via's name (`450:250` → `450:300`), so every fanout via landed where it was. Each exposed
pad gets five vias, at its centre and at the offset on the four axes, inside the cross of its
paste windows; the residual risk is solder wicking into them (V-MFG-03 inspects U1 and U6).

The search reads a pad's oblong hole as a round hole of the drill's width at the pad's centre
(`route.py`, `_Copper`). The receptacles' plated shell slots (0.60 x 1.70 mm at the rear, 0.60 x
1.40 mm at the front, D37) are oblong: beside each rear slot the search put the via of the
contact pad A1 or B1 on the pad's own row, 0.046 mm from the slot's hole, which JLCDFM called
Danger (issue #8, 2026-11-13; 8 vias) and KiCad's DRC did not see. The session had been routed
around those 8 vias, so they stay in the router's input and the patch (stage 5, below) deletes
them: for J1.B1 no free spot for a via exists within 3 mm, and for J2.B1 and J3.B1 only across
the slot, 1.9 mm from the pad (measured with the slot as a capsule, 0.25 mm of hole-to-hole,
against the board's copper). Each of the 8 contact pads keeps its 0.20 mm stub, which ends
0.05 mm inside the ring of its plated slot's pad, and reaches L2 through the slot's wall (the
plane joins a plated pad solid), a much wider path than a 0.30 mm via. `check_routing.py` rule
10 measures every pair of drilled holes with a slot as a capsule. When a new session is routed,
read the slot as a capsule in `_Copper` and delete stage 5.

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

## Router

Freerouting 2.5.0 (the jar and the JRE are named, with their SHA-256, in
`routing/autoroute.json`) routes what the tables above leave, from the board after the plane,
the hand-drawn tracks and the GND fanout. `autoroute.py` exports that board's DSN, adds the
classes and keepouts below, runs the router with its optimizer off (it made the result worse in
every trial), and writes `routing/usb-power-hub.ses`. The router's own via is the board's, 0.45/0.30.
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

The committed session leaves 16 connections unrouted (DRC's count of unconnected items), 11 places
in the analog blocks where an L3 track runs along an L4 track (D36) and 5 dangling-track warnings,
the stubs of 5 of those connections. Its L2 plane is sound: the webs of U1's exposed pad are
2.06–2.37 mm (rule 9 asks 1.60 mm) and the longest void is 2.81 mm. `make_pcb.py` draws the patch
table on the board after the session and before the zones are filled. At each point of a `remove`
row, the via of its net centred exactly there is deleted (such a point is the via's position to
7 decimals, as KiCad wrote it), or else every track of its net through the point. The other rows
draw tracks and vias as the route table does. The 275 rows, 40 `remove` and 235 drawn, leave 0
unconnected items, 0 DRC violations and no D36 place, and bring U1's webs down to 1.65–1.80 mm
(N 1.66, E 1.70, S 1.65, W 1.80).

The Why column names the stage that wrote a row. The stages ran in this order, each on the board
the one before left, on a 0.05 mm grid, with every other net's copper, the DSN keepouts and D36 as
obstacles:

1. **N window.** North of U1, in x 38.9–46.2, y 60.1–65.6, the router left three U1 pins open (BTN_B
   pin 35, LED_ON_B pin 30, LED_FLT_B pin 31), and routing the window's nets one after another
   left three connections open in the trial that was run (BTN_B, LED_ON_A, CLKOUT). So the window
   is routed as a whole by negotiated congestion: the copper of 14 nets inside it is ripped up
   (*ripped up* rows) and drawn again together with the three open nets (*routed again*,
   *unrouted by the router, joined*). Each net is routed in turn and pays for the cells the other
   nets of the window hold, at a price that grows every iteration, and for the cells where nets
   met before; the vias around U1 are counted as rule 9 counts the voids of L2, and a web under
   1.7 mm is a conflict. The search stopped after 14 iterations with 2 clearance conflicts and
   V3V3's pad 22 unconnected. A `remove` row takes a whole session track, so the tracks the
   re-route left ending in nothing are deleted (*dead end*), the live part of a track that such a
   row also took is drawn again (*the live part*), and a via left with one layer gets a short
   joint (*joint at a via*).
2. **U1 joins.** V3V3 pad 22, EVT_L_A pad 6 and QSPI_SD3 pad 51 are joined to their nets by a search
   with the plane rule off (`plane_via` 0: with it on, no path exists, because the pockets around
   these pads hold no cell where a via keeps the rule), and the webs are measured the way rule 9
   measures them before a row is accepted.
3. **Web nudge.** After the joins the south web was 1.58 mm. DOUT_A_3V's via moved 0.25 mm south,
   and the web is 1.65 mm.
4. **Analog blocks.** The 11 D36 places belong to six nets: ADC_CC1, ADC_CC2, ADC_H_A, ADC_M_A and
   EN_G_A on L3, and LED_FLT_A on L4 (the *D36* rows name the places). They are ripped up and
   routed again, together with the 11 connections the router left open there (INP_L_A, INP_L_B,
   LAD2_B, V_INJ ×7, X_L_B; *unrouted by the router*).
5. **Slot vias.** Not the router's: found by JLCDFM on the first Rev0.5 Gerber (issue #8). The 8
   GND fanout vias beside the receptacles' rear slots, and their stubs, are deleted (*remove*
   rows: the via by its exact position, the stub by its middle), and each stub is drawn again
   from its contact pad into the slot's pad (*stub ends in its plated slot's pad*). See *GND
   fanout*. The routing of every other net is the session's and the stages above, untouched.

The programs that wrote the rows (a negotiated-congestion window router, an exact-obstacle search
and a dead-end remover) are scratch tools and are not in the repository. The table is their
output, and `check_routing.py`, not the tools, accepts it.

The table belongs to the session whose SHA-256 `routing/autoroute.json` records. A new session
moves the router's tracks, and a `remove` row that finds nothing stops `make_pcb.py`. After a
new session, rewrite the table.

<!-- patch:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| BTN_A | remove | - | 42.6500000,62.6500000 42.7500,62.0688 42.7750,61.8625 42.7500,62.4000 42.7000,62.6000 41.6665,57.8497 | N window: ripped up, drawn again below |
| CLKOUT | remove | - | 45.5723000,64.8121000 45.0825,63.3846 45.3628,64.1337 43.6000,62.0988 44.5733,63.1043 45.4675,64.7073 43.9721,62.7322 45.1266,65.2578 | N window: ripped up, drawn again below |
| DOUT_B_3V | remove | - | 43.3500000,61.0000000 44.0000,61.0000 45.4438,60.6000 44.8250,60.8250 45.1000,60.6500 45.2250,60.6250 43.3500,60.1790 | N window: ripped up, drawn again below |
| DVDD | remove | - | 39.0297,60.2000 39.3870,60.1099 44.0846,60.1467 43.7626,61.3246 43.1433,61.5002 46.2748,59.7752 41.4996,60.3002 45.1403,60.0004 43.9382,60.7211 | N window: ripped up, drawn again below |
| LED_FLT_A | remove | - | 44.6019000,62.6526000 44.8000,62.1460 44.7009,62.5536 38.9515,59.8664 43.5472,65.1562 44.6019,63.3771 | N window: ripped up, drawn again below |
| LED_ON_A | remove | - | 45.3000000,61.4500000 45.4937,61.0000 45.3250,61.0250 44.7008,59.8781 | N window: ripped up, drawn again below |
| RUN | remove | - | 46.2750,60.3250 45.9545,64.0945 45.8188,60.2000 46.0250,60.2250 45.8995,65.5505 46.0490,64.7950 46.2000,63.5500 45.8600,63.9450 | N window: ripped up, drawn again below |
| SWCLK | remove | - | 45.5909,65.8530 46.0490,62.9720 45.4495,59.9495 | N window: ripped up, drawn again below |
| SWDIO | remove | - | 44.4500000,60.5000000 44.7750,60.1750 44.1266,62.9220 44.0545,61.8727 42.1273,65.5838 44.1987,63.2532 44.2523,60.6977 | N window: ripped up, drawn again below |
| TAP_A_N | remove | - | 42.0581000,64.2736000 41.4290,63.6446 40.8000,62.4265 54.3359,64.2736 | N window: ripped up, drawn again below |
| TAP_A_P | remove | - | 41.1500000,61.0500000 41.1750,61.8125 41.1500,61.2250 44.3461,61.3260 41.5510,61.4510 42.8860,61.8520 46.0273,60.8000 | N window: ripped up, drawn again below |
| TAP_B_N | remove | - | 39.4652000,63.2802000 39.7326,63.0128 40.0000,62.2914 39.2115,65.0093 39.3383,63.4070 | N window: ripped up, drawn again below |
| TAP_B_P | remove | - | 39.9290000,61.0073000 40.4000,61.6030 40.2194,61.1880 39.9839,61.0073 43.3092,63.0097 42.6203,63.1510 46.8322,63.1808 44.0337,63.0245 43.6640,62.8683 | N window: ripped up, drawn again below |
| V3V3 | remove | - | 39.1812,61.4188 42.7200,63.9300 43.0250,63.5750 39.0535,63.9134 43.9148,66.1596 39.2934,62.1441 43.3495,64.6095 41.7469,60.3684 39.0952,60.6000 39.5605,64.3675 43.1500,62.0688 42.6160,64.4620 43.8524,65.1124 41.1354,64.7550 43.1500,62.8500 43.1750,61.8625 44.0705,60.1324 39.5437,60.4842 | N window: ripped up, drawn again below |
| DOUT_B_3V | remove | - | 44.2362,58.4718 45.1223,57.3882 47.9207,54.3923 59.5784,51.5939 | N window: dead end the re-route left |
| DVDD | remove | - | 40.0507,59.1002 | N window: dead end the re-route left |
| INP_L_A | remove | - | 29.435,26.2074 | N window: dead end the re-route left |
| LED_FLT_A | remove | - | 38.9515000,51.1449999 39.3971,69.0335 42.4926,66.7333 39.2774,51.145 40.0559,69.4792 41.3808,68.3674 40.0187,50.7297 | N window: dead end the re-route left |
| LED_FLT_B | remove | - | 67.6537,13.9958 | N window: dead end the re-route left |
| LED_ON_A | remove | - | 44.1017,58.6418 | N window: dead end the re-route left |
| SWCLK | remove | - | 45.1328,68.3022 45.1328000,70.2933000 | N window: dead end the re-route left |
| SWDIO | remove | - | 40.0558,68.3254 40.0558000,68.9954999 | N window: dead end the re-route left |
| TAP_A_P | remove | - | 48.0933,59.8892 58.2528,58.9785 | N window: dead end the re-route left |
| TAP_B_P | remove | - | 51.2191,61.4361 | N window: dead end the re-route left |
| V3V3 | remove | - | 44.3065,59.5317 44.59,58.8835 45.2555,58.6 | N window: dead end the re-route left |
| DOUT_A_3V | remove | - | 42.6444001,56.2022999 43.4,56.2023 | via nudged 0.25 mm south for the L2 web of U1's south side |
| ADC_CC1 | remove | - | 41.8196000,35.1320000 38.2590,35.6206 33.5991,40.6068 34.3931,36.4145 41.5753,35.3763 27.4467,53.2604 24.4284,59.3816 30.5229,47.0813 76.1493,33.0707 68.9048,34.1413 51.7799,35.1320 62.2356,34.6367 | D36: its L3 run at (75.08, 34.14) ran along L4 ADC_VREF_CHK |
| ADC_CC2 | remove | - | 33.1130000,41.8574000 12.6627,62.8243 16.2319,59.3803 25.9500,51.2323 22.2760,55.7064 32.2499,42.2274 13.1742,62.9567 28.9150,47.4671 13.8316,62.6783 31.8800,43.5497 32.8665,41.8574 12.5303,61.7018 13.1960,60.0460 71.5237,35.5322 63.8210,38.5308 45.6347,41.8574 58.3205,41.6934 59.6534,41.5294 77.9939,33.7661 | D36: its L3 run at (58.48, 41.53) ran along L4 V12F |
| ADC_H_A | remove | - | 3.9017000,37.6016000 3.3359,36.4218 2.7700,33.7030 3.9017,37.2947 50.8522,31.1187 36.9982,39.7067 22.0631,40.1047 4.4622,37.6016 37.3961,35.5123 37.6947,31.4173 69.1957,25.6344 6.2743,38.8531 | D36: its L3 run at (7.53, 40.10) ran along L4 V12F |
| ADC_M_A | remove | - | 14.4630001,31.1517000 14.3906,31.1517 34.7324,39.7224 25.9598,36.1337 20.0378,33.6427 68.9456,23.3444 31.1852,37.9280 36.6774,39.5302 39.4711,29.1404 36.8695,35.5401 53.9119,26.5388 | D36: its L3 runs ran along L4 V12F (4 points) and LED_FLT_A (2 points) |
| EN_G_A | remove | - | 19.7540000,44.8146000 49.0936000,45.8052000 50.8001000,56.9282999 55.4733000,57.9924000 15.4462,36.7148 17.9969,38.6844 16.3659,40.7865 13.7732,35.8715 16.8600,44.9150 15.9025,43.2700 16.3813,44.1713 55.4733,57.6729 14.6253,36.3087 51.7486,55.8535 16.8794,41.5853 17.0939,36.6353 52.8611,54.9050 12.2750,47.4900 15.4250,46.6150 16.3910,42.3591 55.4616,57.3417 15.0215,34.7698 16.7342,35.1295 15.8523,38.6969 17.1470,37.8345 13.5023,34.9361 16.9085,41.3000 13.3360,35.2683 18.7939,41.6679 16.5800,45.4600 50.8001,56.8651 19.2739,44.3346 49.0936,50.5135 48.5983,45.3099 54.9412,57.4603 33.9285,44.8146 | D36: its L3 run at (19.75, 44.81) ran along L4 HOLD_L_A |
| LED_FLT_A | remove | - | 34.7088000,14.3745000 40.4340000,50.3144000 34.4356,13.2732 34.7088,13.9604 40.3460,50.2264 40.2581,42.0433 33.8757,38.7507 40.0748,33.7647 31.6255,37.1489 36.0284,38.9918 35.0726,39.3652 31.9809,37.7807 31.8743,26.9164 31.7499,36.7481 33.2916,15.7918 32.7987,38.1361 39.1882,33.5814 36.4017,37.1416 37.4434,34.6230 | D36: its L4 run at (52.53, 33.59) lay under L3 V12F, and 2 more under ADC_M_A |
| BTN_A | F.Cu | 0.15 | 42.75,62.25 42.75,62.4 41.95,63.2 41.95,63.25 41.15,64.05 41.15,64.25 40.85,64.55 37,64.55 35.75,63.3 | N window: routed again |
| BTN_A | B.Cu | 0.15 | 35.75,63.3 35.75,61.5 38.8,58.45 38.8,57.4 39.95,56.25 40.65,56.95 41.65,55.95 41.65,54.1 | N window: routed again |
| BTN_A | via | 0.45/0.3 | 35.75,63.3 | N window: routed again |
| CLKOUT | F.Cu | 0.15 | 43.55,62.25 43.55,62.6 | N window: routed again |
| CLKOUT | In2.Cu | 0.15 | 43.55,62.6 43.55,62.75 43.25,63.05 43.25,63.1 43.1,63.25 43.15,63.3 43,63.45 44.2,64.65 | N window: routed again |
| CLKOUT | B.Cu | 0.15 | 44.2,64.65 44.4,64.85 44.4,64.9 44.65,65.15 44.65,65.65 | N window: routed again |
| CLKOUT | via | 0.45/0.3 | 43.55,62.6 | N window: routed again |
| CLKOUT | via | 0.45/0.3 | 44.2,64.65 | N window: routed again |
| DOUT_B_3V | F.Cu | 0.15 | 45.2,60.65 44.95,60.65 44.85,60.75 | N window: routed again |
| DOUT_B_3V | In2.Cu | 0.15 | 44.85,60.75 45.3,61.2 45.85,60.65 46,60.65 48.75,63.4 49.15,63.4 49.3,63.55 53.7,63.55 54.15,63.1 | N window: routed again |
| DOUT_B_3V | B.Cu | 0.15 | 54.15,63.1 54.15,51.7 | N window: routed again |
| DOUT_B_3V | In2.Cu | 0.15 | 54.15,51.7 54.1,51.65 | N window: routed again |
| DOUT_B_3V | via | 0.45/0.3 | 44.85,60.75 | N window: routed again |
| DOUT_B_3V | via | 0.45/0.3 | 54.15,63.1 | N window: routed again |
| DOUT_B_3V | via | 0.45/0.3 | 54.15,51.7 | N window: routed again |
| DVDD | F.Cu | 0.15 | 39.15,60.2 39.3,60.2 39.35,60.15 39.4,60.15 39.5,60.05 | N window: routed again |
| DVDD | B.Cu | 0.15 | 47.8,59.3 46.4,57.9 46.3,58 44.3,56 44.3,54.55 44.45,54.4 44.45,53.2 | N window: routed again |
| DVDD | In2.Cu | 0.15 | 44.45,53.2 44.25,53.2 41.65,55.8 42.15,56.3 39.65,58.8 39.75,58.9 | N window: routed again |
| DVDD | via | 0.45/0.3 | 44.45,53.2 | N window: routed again |
| LED_ON_A | F.Cu | 0.15 | 45.6,61.05 45.6,61.15 45.55,61.2 45.75,61.4 45.75,61.45 | N window: routed again |
| LED_ON_A | B.Cu | 0.15 | 45.75,61.45 45.55,61.25 45.55,61.2 45.7,61.05 45.7,60.2 45.2,59.7 45.35,59.55 45.35,59.2 45.3,59.15 45.3,59.1 44.15,57.95 | N window: routed again |
| LED_ON_A | via | 0.45/0.3 | 45.75,61.45 | N window: routed again |
| RUN | F.Cu | 0.15 | 45.7,64.3 45.7,64.7 45.65,64.75 45.65,65.25 | N window: routed again |
| RUN | F.Cu | 0.15 | 46.05,60.25 46.25,60.25 46.35,60.35 | N window: routed again |
| RUN | F.Cu | 0.15 | 46.35,63.45 46.15,63.65 46.15,63.7 46.1,63.75 | N window: routed again |
| SWCLK | F.Cu | 0.15 | 45.3,70.4 45.95,71.05 47.9,71.05 51.1,67.85 | N window: routed again |
| SWCLK | B.Cu | 0.15 | 51.1,67.85 51.1,60.5 51.05,60.45 | N window: routed again |
| SWCLK | In2.Cu | 0.15 | 51.05,60.45 49.55,60.45 49.35,60.25 48.85,60.25 48.45,60.65 48.6,60.8 48.25,61.15 46.95,61.15 46.55,60.75 46.8,60.5 46.3,60 46.25,60 45.4,59.15 45.2,59.15 45.05,59.3 | N window: routed again |
| SWCLK | via | 0.45/0.3 | 51.1,67.85 | N window: routed again |
| SWCLK | via | 0.45/0.3 | 51.05,60.45 | N window: routed again |
| SWDIO | F.Cu | 0.15 | 45.05,59.85 44.85,59.85 44.4,60.3 | N window: routed again |
| SWDIO | B.Cu | 0.15 | 44.4,60.3 43.45,59.35 43.45,59.15 43.2,58.9 42.75,59.35 42.3,58.9 42.2,59 42.05,58.85 42,58.9 41.6,58.5 41.6,58.15 40.95,57.5 39.85,58.6 39.75,58.5 39.6,58.65 39.55,58.65 36.75,61.45 36.75,68.35 | N window: routed again |
| SWDIO | F.Cu | 0.15 | 36.75,68.35 39.25,68.35 39.85,68.95 | N window: routed again |
| SWDIO | via | 0.45/0.3 | 44.4,60.3 | N window: routed again |
| SWDIO | via | 0.45/0.3 | 36.75,68.35 | N window: routed again |
| TAP_A_N | F.Cu | 0.15 | 40.85,61.4 40.85,61.15 40.95,61.05 | N window: routed again |
| TAP_A_N | B.Cu | 0.15 | 40.95,61.05 41.65,61.75 41.45,61.95 41.35,61.85 41.2,62 41.05,61.85 40.95,61.95 40.85,61.85 40.2,61.85 40.15,61.8 40.1,61.85 39.8,61.85 39.6,62.05 38.55,61 37.55,62 37.55,65.6 38.2,66.25 38.2,66.3 38.15,66.35 38.15,66.55 38.4,66.8 38.4,68.85 | N window: routed again |
| TAP_A_N | F.Cu | 0.15 | 38.4,68.85 39.2,68.85 41.75,71.4 52.85,71.4 58.45,65.8 60.45,65.8 60.8,66.15 64.55,66.15 66.4,64.3 | N window: routed again |
| TAP_A_N | via | 0.45/0.3 | 40.95,61.05 | N window: routed again |
| TAP_A_N | via | 0.45/0.3 | 38.4,68.85 | N window: routed again |
| TAP_A_P | F.Cu | 0.15 | 41.25,62.25 41.25,62.55 41.3,62.6 | N window: routed again |
| TAP_A_P | In2.Cu | 0.15 | 41.3,62.6 41.35,62.65 41.25,62.75 41.25,63 41.15,63.1 41.15,63.15 40.9,63.4 | N window: routed again |
| TAP_A_P | B.Cu | 0.15 | 40.9,63.4 40.9,63.45 40.85,63.5 40.9,63.55 40.95,63.55 41.15,63.75 41.15,64.3 41.05,64.4 41.05,64.55 42.35,65.85 42.5,65.7 42.85,66.05 42.85,67.1 43.85,68.1 | N window: routed again |
| TAP_A_P | In2.Cu | 0.15 | 43.85,68.1 45.3,68.1 46.25,69.05 48.25,69.05 48.6,68.7 | N window: routed again |
| TAP_A_P | F.Cu | 0.15 | 48.6,68.7 48.6,67.9 51.55,64.95 51.55,60.2 51.65,60.1 51.65,59.1 | N window: routed again |
| TAP_A_P | In2.Cu | 0.15 | 51.65,59.1 51.6,59.05 | N window: routed again |
| TAP_A_P | via | 0.45/0.3 | 41.3,62.6 | N window: routed again |
| TAP_A_P | via | 0.45/0.3 | 40.9,63.4 | N window: routed again |
| TAP_A_P | via | 0.45/0.3 | 43.85,68.1 | N window: routed again |
| TAP_A_P | via | 0.45/0.3 | 48.6,68.7 | N window: routed again |
| TAP_A_P | via | 0.45/0.3 | 51.65,59.1 | N window: routed again |
| TAP_B_N | F.Cu | 0.15 | 39.95,62.25 39.95,62.4 39.8,62.55 39.45,62.55 39.4,62.5 39.35,62.5 39.25,62.4 39.15,62.4 | N window: routed again |
| TAP_B_N | B.Cu | 0.15 | 39.15,62.4 39.2,62.45 39.2,62.65 38.8,63.05 38.8,66.25 38.65,66.4 | N window: routed again |
| TAP_B_N | In2.Cu | 0.15 | 38.65,66.4 39.2,66.4 | N window: routed again |
| TAP_B_N | via | 0.45/0.3 | 39.15,62.4 | N window: routed again |
| TAP_B_N | via | 0.45/0.3 | 38.65,66.4 | N window: routed again |
| TAP_B_P | F.Cu | 0.15 | 40.35,61.4 40.35,61.3 40,60.95 39.85,60.95 39.6,60.7 | N window: routed again |
| TAP_B_P | B.Cu | 0.15 | 39.6,60.7 39,60.1 37.2,61.9 37.2,66.2 37.25,66.25 | N window: routed again |
| TAP_B_P | In2.Cu | 0.15 | 37.25,66.25 37.15,66.15 37.1,66.15 36.45,66.8 37.25,67.6 45.3,67.6 45.55,67.35 51.5,67.35 52.2,68.05 | N window: routed again |
| TAP_B_P | B.Cu | 0.15 | 52.2,68.05 52.2,60.25 | N window: routed again |
| TAP_B_P | In2.Cu | 0.15 | 52.2,60.25 52.3,60.25 | N window: routed again |
| TAP_B_P | via | 0.45/0.3 | 39.6,60.7 | N window: routed again |
| TAP_B_P | via | 0.45/0.3 | 37.25,66.25 | N window: routed again |
| TAP_B_P | via | 0.45/0.3 | 52.2,68.05 | N window: routed again |
| TAP_B_P | via | 0.45/0.3 | 52.2,60.25 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 45,64.3 45,64.9 45.05,64.95 43.95,66.05 43.95,67.1 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 43.25,61.4 43.25,61.05 | N window: routed again |
| V3V3 | In2.Cu | 0.15 | 43.25,61.05 43.2,61.1 43.25,61.15 43.15,61.25 43.2,61.3 43.05,61.45 43.05,61.5 42.8,61.75 42.75,61.75 42.7,61.8 42.5,61.8 42.45,61.85 41.95,61.85 41.75,62.05 41.55,62.05 41.4,61.9 40.85,61.9 40.8,61.85 40.2,61.85 40.15,61.8 40.1,61.85 33.45,61.85 | N window: routed again |
| V3V3 | via | 0.45/0.3 | 43.25,61.05 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 39.5,61.75 39.3,61.75 38.7,61.15 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 42.6,64.25 42.6,64.45 42.2,64.85 42.1,64.85 42.05,64.9 42,64.9 41.8,65.1 41.8,67.75 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 38.85,63.8 38.6,63.55 37.75,63.55 36.95,62.75 | N window: routed again |
| V3V3 | F.Cu | 0.15 | 36.6,62 36.25,62 | N window: routed again |
| V3V3 | In2.Cu | 0.15 | 36.25,62 36.15,61.9 | N window: routed again |
| V3V3 | via | 0.45/0.3 | 36.25,62 | N window: routed again |
| BTN_B | F.Cu | 0.15 | 42.35,61.4 42.35,61.3 42.1,61.05 42.1,61 | N window: unrouted by the router, joined |
| BTN_B | In2.Cu | 0.15 | 42.1,61 42.05,60.95 42.05,60.75 41.75,60.45 41.8,60.4 41.7,60.3 41.75,60.25 41.35,59.85 41.7,59.5 41.6,59.4 42.1,58.9 42.4,58.9 42.8,58.5 42.7,58.4 42.85,58.25 42.8,58.2 44,57 44.35,57 45.15,56.2 45.5,56.2 47.9,53.8 47.85,53.75 | N window: unrouted by the router, joined |
| BTN_B | B.Cu | 0.15 | 47.85,53.75 47.85,40.5 | N window: unrouted by the router, joined |
| BTN_B | F.Cu | 0.15 | 47.85,40.5 50.3,38.05 50.3,37.9 | N window: unrouted by the router, joined |
| BTN_B | In2.Cu | 0.15 | 50.3,37.9 63.55,37.9 | N window: unrouted by the router, joined |
| BTN_B | B.Cu | 0.15 | 63.55,37.9 63.55,33.95 63.45,33.85 63.45,29.35 64.05,28.75 64.05,9.3 63.75,9 | N window: unrouted by the router, joined |
| BTN_B | F.Cu | 0.15 | 63.75,9 63.55,9 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 42.1,61 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 47.85,53.75 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 47.85,40.5 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 50.3,37.9 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 63.55,37.9 | N window: unrouted by the router, joined |
| BTN_B | via | 0.45/0.3 | 63.75,9 | N window: unrouted by the router, joined |
| LED_ON_B | F.Cu | 0.15 | 44.45,62.25 44.45,62.4 44.7,62.65 44.7,62.7 | N window: unrouted by the router, joined |
| LED_ON_B | B.Cu | 0.15 | 44.7,62.7 45.1,63.1 45.05,63.15 45.15,63.25 45.15,63.5 45.1,63.55 45.1,63.85 44.7,64.25 44.7,64.75 47.3,67.35 49.5,65.15 49.75,65.4 50.1,65.05 50.1,64.7 | N window: unrouted by the router, joined |
| LED_ON_B | In2.Cu | 0.15 | 50.1,64.7 50.3,64.9 62.95,64.9 63.05,64.8 | N window: unrouted by the router, joined |
| LED_ON_B | F.Cu | 0.15 | 63.05,64.8 67.15,60.7 67.15,53.5 67.95,52.7 | N window: unrouted by the router, joined |
| LED_ON_B | B.Cu | 0.15 | 67.95,52.7 67.95,48.8 68.45,48.3 68.45,14.5 | N window: unrouted by the router, joined |
| LED_ON_B | F.Cu | 0.15 | 68.45,14.5 68.75,14.2 | N window: unrouted by the router, joined |
| LED_ON_B | via | 0.45/0.3 | 44.7,62.7 | N window: unrouted by the router, joined |
| LED_ON_B | via | 0.45/0.3 | 50.1,64.7 | N window: unrouted by the router, joined |
| LED_ON_B | via | 0.45/0.3 | 63.05,64.8 | N window: unrouted by the router, joined |
| LED_ON_B | via | 0.45/0.3 | 67.95,52.7 | N window: unrouted by the router, joined |
| LED_ON_B | via | 0.45/0.3 | 68.45,14.5 | N window: unrouted by the router, joined |
| LED_FLT_B | F.Cu | 0.15 | 44,62.25 44,62.4 44.2,62.6 44.2,62.85 44.5,63.15 44.3,63.35 44.3,63.45 | N window: unrouted by the router, joined |
| LED_FLT_B | B.Cu | 0.15 | 44.3,63.45 43.7,64.05 43.7,64.75 43.75,64.8 43.75,65.6 43.85,65.7 43.85,65.95 44.35,66.45 44.35,70.75 45.2,71.6 46.2,70.6 47.2,71.6 48.8,70 49.2,70.4 | N window: unrouted by the router, joined |
| LED_FLT_B | In2.Cu | 0.15 | 49.2,70.4 64.65,70.4 | N window: unrouted by the router, joined |
| LED_FLT_B | B.Cu | 0.15 | 64.65,70.4 64.65,14.8 | N window: unrouted by the router, joined |
| LED_FLT_B | F.Cu | 0.15 | 64.65,14.8 66.1,14.8 67.45,13.45 | N window: unrouted by the router, joined |
| LED_FLT_B | via | 0.45/0.3 | 44.3,63.45 | N window: unrouted by the router, joined |
| LED_FLT_B | via | 0.45/0.3 | 49.2,70.4 | N window: unrouted by the router, joined |
| LED_FLT_B | via | 0.45/0.3 | 64.65,70.4 | N window: unrouted by the router, joined |
| LED_FLT_B | via | 0.45/0.3 | 64.65,14.8 | N window: unrouted by the router, joined |
| TAP_B_P | In2.Cu | 0.2 | 52.9638,59.6914 52.2,60.25 | N window: the live part of a track whose dead end is removed |
| SWCLK | F.Cu | 0.2 | 44.9583,70.2933 45.1328,70.2933 | N window: joint at a via that kept one layer |
| SWCLK | F.Cu | 0.15 | 45.3,70.4 45.1328,70.2933 | N window: joint at a via that kept one layer |
| SWDIO | F.Cu | 0.15 | 39.85,68.95 40.0558,68.9955 | N window: joint at a via that kept one layer |
| TAP_A_P | In2.Cu | 0.2 | 51.6,59.05 67.5016,58.9785 | N window: the live part of a track whose dead end is removed |
| DOUT_B_3V | In2.Cu | 0.2 | 68.4378,51.5939 54.1,51.65 | N window: the live part of a track whose dead end is removed |
| V3V3 | F.Cu | 0.15 | 45.2,58.65 44.85,58.65 44.25,59.25 44.25,59.5 | U1 V3V3 pad 22 joined to V3V3 |
| V3V3 | In2.Cu | 0.15 | 44.25,59.5 43.05,60.7 43.2,60.85 | U1 V3V3 pad 22 joined to V3V3 |
| V3V3 | via | 0.45/0.3 | 44.25,59.5 | U1 V3V3 pad 22 joined to V3V3 |
| EVT_L_A | F.Cu | 0.15 | 41.65,55.35 41.65,55.95 41.35,56.25 40.9,56.25 40.45,55.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | B.Cu | 0.15 | 40.45,55.8 40.45,55 39.4,53.95 39.4,46.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | In2.Cu | 0.15 | 39.4,46.8 26.1,46.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | F.Cu | 0.15 | 26.1,46.8 25.9,47 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | via | 0.45/0.3 | 40.45,55.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | via | 0.45/0.3 | 39.4,46.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| EVT_L_A | via | 0.45/0.3 | 26.1,46.8 | U1 EVT_L_A pad 6 joined to EVT_L_A |
| QSPI_SD3 | F.Cu | 0.15 | 39.15,57.8 39.8,57.8 40.2,57.4 40.2,57.15 | U1 QSPI_SD3 pad 51 joined to QSPI_SD3 |
| QSPI_SD3 | In2.Cu | 0.15 | 40.2,57.15 39.1,56.05 37.15,56.05 36.7,56.5 35.1,56.5 34.45,55.85 | U1 QSPI_SD3 pad 51 joined to QSPI_SD3 |
| QSPI_SD3 | F.Cu | 0.15 | 34.45,55.85 35.5,54.8 35.5,54.4 35.9,54 | U1 QSPI_SD3 pad 51 joined to QSPI_SD3 |
| QSPI_SD3 | via | 0.45/0.3 | 40.2,57.15 | U1 QSPI_SD3 pad 51 joined to QSPI_SD3 |
| QSPI_SD3 | via | 0.45/0.3 | 34.45,55.85 | U1 QSPI_SD3 pad 51 joined to QSPI_SD3 |
| DOUT_A_3V | F.Cu | 0.2 | 42.6444,55.9523 42.8944,56.2023 44.1703,56.2023 | via nudged 0.25 mm south for the L2 web of U1's south side |
| DOUT_A_3V | In2.Cu | 0.2 | 42.6444,55.9523 42.8944,56.2023 43.6692,56.2023 | via nudged 0.25 mm south for the L2 web of U1's south side |
| DOUT_A_3V | via | 0.45/0.3 | 42.6444,55.9523 | via nudged 0.25 mm south for the L2 web of U1's south side |
| INP_L_A | F.Cu | 0.2 | 24.6,23.35 25,22.95 25.75,22.95 26.7,22 26.7,21.15 27.05,20.8 29.15,20.8 29.6,21.25 | unrouted by the router |
| INP_L_A | B.Cu | 0.2 | 29.6,21.25 29.6,24.05 29.45,24.2 | unrouted by the router |
| INP_L_A | F.Cu | 0.2 | 29.45,24.2 29.45,24.55 | unrouted by the router |
| INP_L_A | via | 0.45/0.3 | 29.6,21.25 | unrouted by the router |
| INP_L_A | via | 0.45/0.3 | 29.45,24.2 | unrouted by the router |
| INP_L_B | F.Cu | 0.2 | 62.95,26.4 62.2,27.15 59.4,27.15 58.35,26.1 58.35,23.9 | unrouted by the router |
| LAD2_B | F.Cu | 0.2 | 62.8,23.9 63.05,24.15 | unrouted by the router |
| LAD2_B | B.Cu | 0.2 | 63.05,24.15 63.05,22.8 63.1,22.75 63.1,20.8 62.95,20.65 | unrouted by the router |
| LAD2_B | F.Cu | 0.2 | 62.95,20.65 60.9,20.65 60.25,21.3 59.45,21.3 | unrouted by the router |
| LAD2_B | via | 0.45/0.3 | 63.05,24.15 | unrouted by the router |
| LAD2_B | via | 0.45/0.3 | 62.95,20.65 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 39.4,13.95 39.75,13.6 39.75,11.9 39,11.15 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 26.55,23.8 26.45,23.9 26.4,23.9 26.25,24.05 26.25,24.1 26.2,24.1 26.2,24.15 26.15,24.15 25.9,24.4 25.75,24.4 | unrouted by the router |
| V_INJ | In2.Cu | 0.2 | 25.75,24.4 15.05,24.4 15,24.45 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 25.75,24.4 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 39.1,23.3 39.1,20.35 40.1,19.35 43.95,19.35 46.75,22.15 46.75,23.3 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 38.1,8.7 38.1,9.55 38,9.65 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 60.35,23.8 60.25,23.9 60.2,23.9 60.05,24.05 60.05,24.1 60,24.1 60,24.15 59.95,24.15 59.75,24.35 59.55,24.35 | unrouted by the router |
| V_INJ | In2.Cu | 0.2 | 59.55,24.35 47.5,24.35 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 47.5,24.35 47.05,23.9 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 59.55,24.35 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 47.5,24.35 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 39.8,13.65 41.65,15.5 | unrouted by the router |
| V_INJ | B.Cu | 0.2 | 41.65,15.5 41.65,19.25 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 41.65,19.25 41.65,19.3 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 41.65,15.5 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 41.65,19.25 | unrouted by the router |
| V_INJ | In2.Cu | 0.2 | 25.9,24.55 27.05,24.55 27.3,24.8 33.75,24.8 | unrouted by the router |
| V_INJ | F.Cu | 0.2 | 33.75,24.8 34.2,24.35 35.5,24.35 36.45,25.3 36.45,26.2 37.45,27.2 39.9,27.2 40.55,26.55 40.55,24.5 39.9,23.85 39.15,23.85 | unrouted by the router |
| V_INJ | via | 0.45/0.3 | 33.75,24.8 | unrouted by the router |
| X_L_B | F.Cu | 0.2 | 54.95,23.9 54.95,26.2 55.3,26.55 | unrouted by the router |
| X_L_B | In2.Cu | 0.2 | 55.3,26.55 61.35,26.55 | unrouted by the router |
| X_L_B | via | 0.45/0.3 | 55.3,26.55 | unrouted by the router |
| X_L_B | via | 0.45/0.3 | 61.35,26.55 | unrouted by the router |
| ADC_CC1 | F.Cu | 0.2 | 21.65,62.15 27.5,56.3 27.5,49.95 33.75,43.7 33.75,37.1 33.8,37.05 33.8,37 33.85,37 33.85,36.95 33.9,36.95 33.9,36.9 33.95,36.9 33.95,36.85 34,36.85 34,36.8 34.05,36.8 34.05,36.75 34.1,36.75 34.1,36.7 34.15,36.7 34.15,36.65 34.2,36.65 34.2,36.6 34.25,36.6 34.25,36.55 34.3,36.55 34.3,36.5 34.35,36.5 34.35,36.45 34.4,36.45 34.4,36.4 34.45,36.4 34.45,36.35 34.5,36.35 34.5,36.3 34.55,36.3 34.55,36.25 34.6,36.25 34.6,36.2 34.65,36.2 34.65,36.15 34.7,36.15 34.7,36.1 34.75,36.1 35.2,35.65 40.8,35.65 41.9,34.55 | D36: routed again, no L3 run along an L4 track |
| ADC_CC1 | In2.Cu | 0.2 | 41.9,34.55 75,34.55 76.85,32.7 | D36: routed again, no L3 run along an L4 track |
| ADC_CC1 | via | 0.45/0.3 | 41.9,34.55 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | F.Cu | 0.2 | 13.85,62.6 13.45,63 12.75,63 12.55,62.8 12.55,60.6 15.9,57.25 23.1,57.25 27,53.35 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | In2.Cu | 0.2 | 27,53.35 30.2,53.35 30.35,53.2 40.6,53.2 42.25,51.55 43.8,51.55 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | B.Cu | 0.2 | 43.8,51.55 43.8,39.05 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | In2.Cu | 0.2 | 43.8,39.05 65.2,39.05 67.65,36.6 79.15,36.6 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | F.Cu | 0.2 | 79.15,36.6 79.15,33.1 79.5,32.75 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | via | 0.45/0.3 | 27,53.35 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | via | 0.45/0.3 | 43.8,51.55 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | via | 0.45/0.3 | 43.8,39.05 | D36: routed again, no L3 run along an L4 track |
| ADC_CC2 | via | 0.45/0.3 | 79.15,36.6 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | F.Cu | 0.2 | 3,31.8 3.8,31.8 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | In2.Cu | 0.2 | 3.8,31.8 33.75,31.8 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | F.Cu | 0.2 | 33.75,31.8 34.2,31.8 36.55,34.15 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | B.Cu | 0.2 | 36.55,34.15 36.55,27.9 36.75,27.7 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | In2.Cu | 0.2 | 36.75,27.7 66.7,27.7 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | F.Cu | 0.2 | 66.7,27.7 73.95,20.45 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | via | 0.45/0.3 | 3.8,31.8 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | via | 0.45/0.3 | 33.75,31.8 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | via | 0.45/0.3 | 36.55,34.15 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | via | 0.45/0.3 | 36.75,27.7 | D36: routed again, no L3 run along an L4 track |
| ADC_H_A | via | 0.45/0.3 | 66.7,27.7 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | F.Cu | 0.2 | 14,31.45 14.15,31.3 15.2,31.3 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | B.Cu | 0.2 | 15.2,31.3 15.2,40.25 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | In2.Cu | 0.2 | 15.2,40.25 46.5,40.25 46.75,40 65.6,40 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | F.Cu | 0.2 | 65.6,40 66.35,39.25 66.35,29.4 66.1,29.15 66.1,26.7 71.9,20.9 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | via | 0.45/0.3 | 15.2,31.3 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | via | 0.45/0.3 | 15.2,40.25 | D36: routed again, no L3 run along an L4 track |
| ADC_M_A | via | 0.45/0.3 | 65.6,40 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 53.45,55.2 53.45,55.6 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | In2.Cu | 0.2 | 53.45,55.6 54.85,57 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 54.85,57 55.15,57.3 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 53.45,55.6 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 54.85,57 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 16.25,41.55 16.25,42.5 15.9,42.85 15.9,43.55 16.7,44.35 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 16.55,45.5 16.7,45.35 16.7,44.95 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 10.3,47.3 11.7,45.9 16,45.9 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 17,38.6 17,39.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | In2.Cu | 0.2 | 17,39.15 15.75,39.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 15.75,39.15 15.75,40.4 16.35,41 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 17,39.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 15.75,39.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 52.05,54.8 51.95,54.7 51.6,54.7 51.25,54.35 51.25,52.5 50.9,52.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | B.Cu | 0.2 | 50.9,52.15 50.9,45.35 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | In2.Cu | 0.2 | 50.9,45.35 33.8,45.35 33.2,44.75 17.6,44.75 17.45,44.9 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | F.Cu | 0.2 | 17.45,44.9 17.1,44.9 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 50.9,52.15 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 50.9,45.35 | D36: routed again, no L3 run along an L4 track |
| EN_G_A | via | 0.45/0.3 | 17.45,44.9 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | F.Cu | 0.2 | 34.6,13.6 36.4,15.4 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | B.Cu | 0.2 | 36.4,15.4 36.4,15.9 35.9,16.4 35.9,17.05 39.15,20.3 39.15,33.2 39.5,33.55 39.6,33.45 39.75,33.6 39.75,33.45 39.95,33.65 39.95,33.6 40.2,33.85 40.2,36.1 40.15,36.15 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | F.Cu | 0.2 | 40.15,36.15 45.75,41.75 47.35,41.75 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | B.Cu | 0.2 | 47.35,41.75 47.35,55.15 49.65,57.45 49.65,63.25 49,63.9 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | In2.Cu | 0.2 | 49,63.9 46.5,63.9 45.85,63.25 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | F.Cu | 0.2 | 45.85,63.25 45.2,62.6 45.2,62.45 44.85,62.1 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | via | 0.45/0.3 | 36.4,15.4 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | via | 0.45/0.3 | 40.15,36.15 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | via | 0.45/0.3 | 47.35,41.75 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | via | 0.45/0.3 | 49,63.9 | D36: routed again, no L3 run along an L4 track |
| LED_FLT_A | via | 0.45/0.3 | 45.85,63.25 | D36: routed again, no L3 run along an L4 track |
| GND | remove | - | 79.825,65.6975 79.5125,65.6975 | Slot vias: J1.A1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 72.175,65.6975 72.4875,65.6975 | Slot vias: J1.B1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 21.325,65.6975 21.0125,65.6975 | Slot vias: J4.A1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 13.675,65.6975 13.9875,65.6975 | Slot vias: J4.B1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 21.325,6.3025 21.0125,6.3025 | Slot vias: J2.B1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 13.675,6.3025 13.9875,6.3025 | Slot vias: J2.A1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 55.125,6.3025 54.8125,6.3025 | Slot vias: J3.B1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | remove | - | 47.475,6.3025 47.7875,6.3025 | Slot vias: J3.A1's fanout via, 0.046 mm from its plated slot's hole, and its stub; the stub is drawn again below |
| GND | F.Cu | 0.2 | J1.A1 79.87,65.6975 | Slot vias: J1.A1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J1.B1 72.13,65.6975 | Slot vias: J1.B1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J4.A1 21.37,65.6975 | Slot vias: J4.A1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J4.B1 13.63,65.6975 | Slot vias: J4.B1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J2.B1 21.37,6.3025 | Slot vias: J2.B1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J2.A1 13.63,6.3025 | Slot vias: J2.A1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J3.B1 55.17,6.3025 | Slot vias: J3.B1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
| GND | F.Cu | 0.2 | J3.A1 47.43,6.3025 | Slot vias: J3.A1's stub ends in its plated slot's pad, 0.05 mm inside the ring, the way to L2 |
<!-- patch:end -->

## Not settled

- **Port voltage.** CIRCUIT_DESIGN_Rev0.6.md §3.1 allows about 40 mΩ for the copper and the
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
- **Thin webs at U1.** After the patch U1's exposed pad keeps 1.66 mm of plane copper on its north
  side and 1.65 mm on its south, 0.06 and 0.05 mm over rule 9's 1.60 mm (east 1.70, west 1.80).
  A row added near U1 later can break it; `make_pcb.py` fails when a web falls under the limit.
  Rule 9 reads the 2-D copper of L2, not the return currents.
- **Long routes.** The patch joins what the router left open where it found room, not by the
  shortest way. V_INJ runs 87.9 mm with 8 vias, BTN_B 78.9 mm, LED_ON_B 81.0 mm and LED_FLT_B
  91.0 mm (they were 17.7, 7.6, 4.0 and 1.8 mm of unconnected stubs in the session), and the four
  taps TAP_A_P, TAP_A_N, TAP_B_P and TAP_B_N 102.9–110.6 mm (90.0–109.7 mm in the session). The taps
  sit behind their 1 kΩ resistors, so the pairs carry no stub beyond a pad, but what the wire's
  capacitance does to a 12 Mbit/s edge is not computed, and CIRCUIT_DESIGN_Rev0.6.md §3.3 sets no
  length limit. `check_routing.py` has no length rule.
