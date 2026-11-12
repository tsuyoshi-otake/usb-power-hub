# USB Power-Control Hub — Rev0.4 routing

> **WIP — MANUFACTURING PROHIBITED.** How the placed Rev0.4 board (PLACEMENT_Rev0.4.md) is
> routed, and why. Issue #6 P4. Nothing here has been built or measured.

`design/ecad/scripts/make_pcb.py` builds `source/usb-power-hub.kicad_pcb` from the placement,
this file and the committed router session in `routing/`; `scripts/autoroute.py` writes that
session; `scripts/check_routing.py` checks the board against this file and runs DRC
(`design/ecad/README.md`). Change a track here, never in KiCad: the next run of `make_pcb.py`
rebuilds the board.

## Frame and format

- The board frame of PLACEMENT_Rev0.4.md: origin at the lower-left corner, x right, y up, in mm;
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

IPC-2221 for a 10 °C rise, at the currents of CIRCUIT_DESIGN_Rev0.4.md: 1.221 A, the highest
over-current trip (D34), per port, and 2.46 A from J4 with both ports at it.

| Path | Current | Outer width for ΔT 10 °C | Drawn |
|---|---:|---:|---|
| J4 VBUS to F1 (VBUS_J4) | 2.46 A | 1.040 mm | 1.5 mm on B.Cu |
| F1 to each port switch (VBUS_IN) | 1.221 A | 0.396 mm | 1.5 / 1.0 mm (A), 2.0 / 1.0 mm (B) |
| a port path (SRC, VSUP, LAD1, VBUS) | 1.221 A | 0.396 mm | 0.6 mm at SOT-23 pads, 1.0–2.0 mm between |
| LAD2 (MID range only) | ≤ 0.5 A (stuck MID, §4) | 0.396 mm | 0.5–0.6 mm |
| J1's VBUS, J1 to Q53 | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.20 mm, on F.Cu and B.Cu only (router class J1_POWER) |
| V5L, Q53 to the hub, U2, U5 and the dividers | 0.277 A | 0.051 mm (inner: 0.306 mm) | 0.31 mm on any layer (router class V5L_POWER); restricted to L1 and L4 it was left unconnected in every trial |
| V5L, C27 into U6 pin 26 (the hub's own V5) | 85 mA typical (CIRCUIT_DESIGN_Rev0.4.md §7.1) | below 0.051 mm | 0.20 mm on F.Cu, one track (route table): the pin is 0.20 mm wide at 0.4 mm pitch, so a 0.31 mm track would not clear its neighbours |

A 0.60/0.30 via passes about 1 A; a port path changes layer through two vias or more at each
end (three for VBUS). Inner layers carry no port current.

The copper of each port's HIGH-range path, J4's VBUS pin to the module's VBUS pin, is the sum of
the nets below between their pads; `check_routing.py` computes each by nodal analysis of the
tracks and vias (20 °C copper, 35 µm outer, 18 µm via plating over 1.6 mm) and holds the sum to
the `limit`, the 40 mΩ CIRCUIT_DESIGN_Rev0.4.md §3.1 allows for copper and module wiring
together (see Not settled).

<!-- port_path:begin limit=40 -->
| Port | Net | From | To |
|---|---|---|---|
| A | VBUS_J4 | J4.1 | F1.1 |
| A | VBUS_IN | F1.2 | Q10.3 |
| A | SRC_A | Q10.2 | Q11.2 |
| A | VSUP_A | Q11.3 | RS10.1 |
| A | LAD1_A | RS10.4 | Q17.2 |
| A | VBUS_A | Q17.3 | J2.1 |
| B | VBUS_J4 | J4.1 | F1.1 |
| B | VBUS_IN | F1.2 | Q30.3 |
| B | SRC_B | Q30.2 | Q31.2 |
| B | VSUP_B | Q31.3 | RS20.1 |
| B | LAD1_B | RS20.4 | Q37.2 |
| B | VBUS_B | Q37.3 | J3.1 |
<!-- port_path:end -->

## High-speed pairs

USB_UP (U6 to J1), USB_A (U6 to J2) and USB_B (U6 to J3): W 0.31 mm, S 0.15 mm, so the
conductors' centres are 0.46 mm apart, on L1 over L2 (D27, provisional). Each leaves U6's
0.4 mm-pitch pads at 0.20 mm and widens at the first bend. The N conductor is on the right of
the direction of travel from U6. Between U6 and J2/J3 the order reverses, so USB_A_N and
USB_B_N cross under their P conductor through one via each, 0.5 mm before the header, and run
the last 5 mm on L4; USB_UP needs no crossing, because it reaches J1 from the north, under the
module.

The `pairs` table holds each pair's centreline from its first bend away from U6. The router
keeps 0.5 mm of copper away from the 0.31 mm conductors' edges on L1 and L3, and keeps its
vias' antipads 0.3 mm clear of their L2 footprint (keepouts below). These keepouts follow the
drawn conductors rather than the centreline, so they cover the tuning bumps and the ends at the
modules. GND fanout keeps the same 0.5 mm.

**Skew.** The two conductors of a pair are matched in length, with a via counted as 1.53 mm
(L1 to L4). As drawn, the doc rows give UP −0.02 mm, A +0.00 mm and B +0.24 mm (P − N);
check_routing.py holds every pair to 1.25 mm on the built board.
- USB_UP turns left three times with N on the outside, and N's end at J1 jogs 2.54 mm west.
  Together these make N 3.13 mm longer. P makes this up with eight bumps on the right-edge
  run: 0.47 mm away from N, 45° sides, 0.62 mm flat, every 2.18 mm, from y 31.0 to 47.82
  (the `Tune` column). That span is clear of parts, and the keepouts follow the bumps.
- For USB_A and USB_B, P was longer: it runs on to the far pin of the module while N drops
  through its crossing via. P now takes a 45° diagonal to its pin instead of an L.

<!-- pairs:begin -->
| Pair | P | N | Centreline | Tune | Why |
|---|---|---|---|---|---|
| UP | USB_UP_P | USB_UP_N | 97.3,28.0 97.8,28.5 97.8,64.0 97.3,64.5 73.7,64.5 73.2,64.0 73.2,61.4 | P 97.8,31.0 97.8,47.82 0.47 | U6 north along the right edge, then west under J1 to its pins |
| A | USB_A_P | USB_A_N | 90.9,24.0 90.4,23.5 90.4,18.4 89.9,17.9 23.8,17.9 | - | U6 south, then west in the corridor to J2 |
| B | USB_B_P | USB_B_N | 96.5,24.0 97.0,23.5 97.0,16.45 96.5,15.95 57.8,15.95 | - | U6 south, then west in the corridor to J3, below A |
<!-- pairs:end -->

## Hand-drawn tracks

The pairs, the hub's crystal, the Kelvin taps and the port current paths are drawn here; the
router connects everything else. A few rows (their Why says so) are connections the router
left open in a trial: drawn here, they are fixed before it starts.

- **Kelvin taps (G2).** Each sense net is one straight 0.20 mm track on L1 from the shunt's
  sense pad to its amplifier resistor, with no via; it carries no load current.
- **Port paths.** The current enters each port at its switch (Q10/Q30), crosses R_H on
  RS10/RS20, and in the HIGH range returns to the port through the bypass FET Q17/Q37. R_M is
  through-hole, so LAD1 runs on L4 from its pad; LAD2 also runs on L4. VBUS_x crosses under the
  pairs on L4 to the module's VBUS pin.
- **VBUS_IN** leaves F1's pad on L1 toward port A and on L4 toward port B, so the corridor
  between the front ends and the MCU stays free on L1 for the control lines.

<!-- route:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| USB_UP_N | F.Cu | 0.20 | U6.20 96.55,27.8 96.75,27.77 | U6 lead-in |
| USB_UP_P | F.Cu | 0.20 | U6.21 96.55,28.2 96.75,28.23 | U6 lead-in |
| USB_UP_N | F.Cu | 0.31 | 96.75,27.77 97.395,27.77 98.03,28.405 98.03,64.095 97.395,64.73 73.605,64.73 72.97,64.095 72.97,61.4 | coupled |
| USB_UP_P | F.Cu | 0.31 | 96.75,28.23 97.205,28.23 97.57,28.595 97.57,31.00 97.1,31.47 97.1,32.09 97.57,32.56 97.57,33.18 97.1,33.65 97.1,34.27 97.57,34.74 97.57,35.36 97.1,35.83 97.1,36.45 97.57,36.92 97.57,37.54 97.1,38.01 97.1,38.63 97.57,39.10 97.57,39.72 97.1,40.19 97.1,40.81 97.57,41.28 97.57,41.90 97.1,42.37 97.1,42.99 97.57,43.46 97.57,44.08 97.1,44.55 97.1,45.17 97.57,45.64 97.57,46.26 97.1,46.73 97.1,47.35 97.57,47.82 97.57,63.905 97.205,64.27 73.795,64.27 73.43,63.905 73.43,61.4 | coupled, with the eight tuning bumps (Skew) |
| USB_UP_N | F.Cu | 0.31 | 72.97,61.4 70.92,59.35 J1.2 | to J1 D− |
| USB_UP_P | F.Cu | 0.31 | 73.43,61.4 J1.3 | to J1 D+ |
| USB_A_N | F.Cu | 0.20 | U6.8 92.8,24.45 92.6,24.23 | U6 lead-in |
| USB_A_P | F.Cu | 0.20 | U6.9 93.2,24.2 92.77,23.77 92.6,23.77 | U6 lead-in |
| USB_A_N | F.Cu | 0.31 | 92.6,24.23 90.805,24.23 90.17,23.595 90.17,18.495 89.805,18.13 23.8,18.13 23.6,18.33 | coupled, then to the crossing via |
| USB_A_P | F.Cu | 0.31 | 92.6,23.77 90.995,23.77 90.63,23.405 90.63,18.305 89.995,17.67 23.8,17.67 | coupled |
| USB_A_N | via | 0.45/0.30 | 23.6,18.33 | the crossing |
| USB_A_N | B.Cu | 0.31 | 23.6,18.33 22.58,17.31 J2.2 | under P to J2 D− |
| USB_A_P | F.Cu | 0.31 | 23.8,17.67 22.76,17.67 20.04,14.95 J2.3 | to J2 D+, diagonal to match N (skew) |
| USB_B_N | F.Cu | 0.20 | U6.13 94.8,24.2 95.23,23.77 95.4,23.77 | U6 lead-in |
| USB_B_P | F.Cu | 0.20 | U6.14 95.2,24.45 95.4,24.23 | U6 lead-in |
| USB_B_N | F.Cu | 0.31 | 95.4,23.77 96.405,23.77 96.77,23.405 96.77,16.545 96.405,16.18 57.8,16.18 57.6,16.38 | coupled, then to the crossing via |
| USB_B_P | F.Cu | 0.31 | 95.4,24.23 96.595,24.23 97.23,23.595 97.23,16.355 96.595,15.72 57.8,15.72 | coupled |
| USB_B_N | via | 0.45/0.30 | 57.6,16.38 | the crossing |
| USB_B_N | B.Cu | 0.31 | 57.6,16.38 56.38,15.16 J3.2 | under P to J3 D− |
| USB_B_P | F.Cu | 0.31 | 57.8,15.72 56.46,15.72 J3.3 | to J3 D+, diagonal to match N (skew) |
| XI_HUB | F.Cu | 0.20 | U6.11 94,20.95 Y2.1 | the crystal, between Y2's pads |
| XO_HUB | F.Cu | 0.20 | U6.12 94.4,23.6 94.8,23.2 Y2.3 | the crystal |
| VDD33_HUB | F.Cu | 0.20 | U6.19 U6.18 96.55,27.0 96.8,26.75 | U6's pins 18 and 19, out past the unused pins 15-17 (the router left them open) |
| VDD33_HUB | via | 0.45/0.30 | 96.8,26.75 | 0.64 mm from the UP pair's conductor |
| VDD33_HUB | In2.Cu | 0.20 | 96.8,26.75 95.9,26.75 95.9,30.3 | under U6's east row, clear of the UP pair's keepout |
| VDD33_HUB | via | 0.45/0.30 | 95.9,30.3 | |
| VDD33_HUB | F.Cu | 0.20 | 95.9,30.3 TP13.1 | to the rest of VDD33_HUB at its test point |
| XOUT | F.Cu | 0.20 | U1.21 44.25,58.2 | U1's escape inward, between its pad row and its ePad (the router left it open) |
| XOUT | via | 0.45/0.30 | 44.25,58.2 | 0.225 mm from the ePad |
| SWCLK | F.Cu | 0.20 | U1.24 44.7,59.35 | U1's escape inward |
| SWCLK | via | 0.45/0.30 | 44.7,59.35 | |
| SWDIO | F.Cu | 0.20 | U1.25 45.0,59.8 44.25,60.25 | U1's escape inward, staggered from SWCLK's via |
| SWDIO | via | 0.45/0.30 | 44.25,60.25 | |
| USB_MCU_N | F.Cu | 0.20 | U1.46 39.65,59.8 | U1's escape inward |
| USB_MCU_N | via | 0.45/0.30 | 39.65,59.8 | |
| QSPI_SCLK | F.Cu | 0.20 | U1.52 37.924,57.4 | U1's escape west, between its pads and C17 (the router left it open) |
| QSPI_SCLK | via | 0.45/0.30 | 37.924,57.4 | 0.19 mm from C17's pad |
| V3V3 | F.Cu | 0.20 | U1.22 46.35,58.6 46.35,59.1 C14.1 | pin 22 to its decoupler, clear of Y1's pad (the router left it open) |
| DVDD | F.Cu | 0.20 | U1.23 45.1,59.0 44.75,58.75 | U1's escape inward: pin 22's decoupler track blocks the east side |
| DVDD | via | 0.45/0.30 | 44.75,58.75 | |
| RUN | F.Cu | 0.20 | U1.26 46.158,60.2 46.37,60.412 46.37,62.69 R26.2 | pin 26 to its pull-up (the router left it open) |
| V5L | F.Cu | 0.20 | U6.26 C27.1 | U6's 5 V pin to its decoupler (the router left it open in every trial) |
| VBUS_J4 | B.Cu | 1.50 | J4.1 F1.1 | J4 to the fuse; both through-hole |
| VBUS_IN | F.Cu | 1.50 | F1.2 8.2,50.1 3.44,50.1 | to port A's switch |
| VBUS_IN | F.Cu | 1.00 | 3.44,50.1 Q10.3 | |
| VBUS_IN | B.Cu | 2.00 | F1.2 10.1,50.2 37.24,50.2 37.24,48.7 | to port B's switch, under the corridor |
| VBUS_IN | B.Cu | 1.00 | 37.24,48.7 38.4,48.7 | |
| VBUS_IN | via | 0.60/0.30 | 37.24,48.7 | |
| VBUS_IN | via | 0.60/0.30 | 38.4,48.7 | |
| VBUS_IN | F.Cu | 0.80 | Q30.3 37.24,48.7 38.4,48.7 | |
| VBUS_IN | F.Cu | 1.00 | F1.2 11.6,53.3 14.2,53.3 D6.1 | the TVS after the fuse (D25) |
| VBUS_IN | F.Cu | 1.00 | 14.2,53.3 C1.1 | the bulk capacitor |
| VBUS_IN | F.Cu | 0.40 | C1.1 R7.1 | the V_J4 divider |
| VBUS_IN | F.Cu | 0.40 | TP8.1 F1.2 | the test point |
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
| LAD1_A | B.Cu | 1.50 | RS11.1 9.78,23.0 27.6,23.0 28.1,22.6 28.1,21.4 | R_M's pad to the HIGH bypass FET |
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
| VBUS_A | B.Cu | 1.50 | 26.33,19.25 26.33,14.4 J2.1 | under the pairs to the module's VBUS pin |
| VBUS_A | F.Cu | 0.60 | J2.1 26.55,11.6 C116.1 | the port capacitor |
<!-- channel_route:end -->

## GND fanout

Every GND surface pad (SMD, or a connector pad without paste: J5's pad 5) gets the board's via,
the Default class's 0.45/0.30 (`make_project.py`), to L2 on the nearest free spot (16 directions, outward
from its part first, 0.1 mm rings) and a 0.20 mm stub to it; the search keeps 0.15 mm from other
copper, 0.5 mm from the HS pairs, 0.20 mm from another via's hole (JLCPCB's via figure, the
custom rule `VIA_HOLE_TO_HOLE`), the board's 0.25 mm hole-to-hole minimum from a pad's hole, and
0.3 mm from the edge. Until issue #8 the via was 0.45/0.25 with 0.25 mm between all holes: the same
0.50 mm between two via centres. The router input of issue #8 equals the one before it except for
the via's name (`450:250` → `450:300`), so every fanout via landed where it was. Each exposed
pad gets five vias, at its centre and at the offset on the four axes, inside the cross of its
paste windows; the residual risk is solder wicking into them (V-MFG-03 inspects U1 and U6).

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

Its costs, beside the defaults. Four runs of one input, with the layer rows above, left by DRC's
count: 6 connections unrouted at the default via cost, 6 with the layer cost at 2.0, 11 with a
cheaper rip-up, 2 with vias dearer.

<!-- router_costs:begin -->
| Setting | Value | Why |
|---|---:|---|
| via_costs | 100 | the cost of a via against a track; dearer vias kept more connections on one layer near U1 |
<!-- router_costs:end -->

<!-- keepouts:begin analog=AFE_A,AFE_B,ADC,ADCSUP,REF -->
| Keepout | Layers | Kind | Around | Buffer | Why |
|---|---|---|---|---|---|
| PAIR_COPLANAR | F.Cu,In2.Cu | wire_keepout | pair-tracks | w/2+0.5 | 0.5 mm beyond the edges of each 0.31 mm pair conductor |
| PAIR_ANTIPAD | signal | via_keepout | pair-tracks | w/2+0.5 | the router keeps the via's copper out: the conductor's edge, + the 0.20 antipad of L2, + 0.30 of plane between antipad and conductor |
| TRUNK_L3 | In2.Cu | wire_keepout | B.Cu-rows in analog | w/2+0.3 | no L3 track above an L4 trunk inside the analog blocks: D36 lets an L3 signal cross an L4 signal, and a trunk is wider and carries current, so L3 stays off it |
<!-- keepouts:end -->

## After the router

The committed session leaves 2 connections unrouted (DRC's count) and 3 places in the analog
blocks where an L3 track runs along an L4 track (D36). `make_pcb.py` draws the patch table on the
board after the session and before the zones are filled. At each point of a `remove` row, the
via of its net centred exactly there is deleted, or else every track of its net through the point. The other
rows draw tracks and vias as the route table does. Each row
was found by a 0.1 mm grid search over the session's board, with every other net's copper, the
DSN keepouts and D36 as obstacles, and `check_routing.py` checks the result.

The table belongs to the session whose SHA-256 `routing/autoroute.json` records. A new session
moves the router's tracks, and a `remove` row that finds nothing stops `make_pcb.py`. After a
new session, rewrite the table.

<!-- patch:begin -->
| Net | Layer | Width | Points | Why |
|---|---|---:|---|---|
| EVTG_L_A | F.Cu | 0.20 | Q25.1 19.8,38.7 19.7,38.6 19.7,36.3 R118.2 | unrouted by the router |
| ADC_CC2 | F.Cu | 0.20 | R6.2 27.2,60.8 | unrouted by the router: J4's CC2 to U17 CH4, a DC level, so its 81 mm and 2 vias cost nothing |
| ADC_CC2 | via | 0.45/0.30 | 27.2,60.8 | |
| ADC_CC2 | B.Cu | 0.20 | 27.2,60.8 28.8,60.8 39.2,71.2 47.4,71.2 60.4,58.2 60.4,46.6 | |
| ADC_CC2 | via | 0.45/0.30 | 60.4,46.6 | |
| ADC_CC2 | In2.Cu | 0.20 | 60.4,46.6 66.2,40.8 70,40.8 71,39.8 70.7,39.5 77.1,33.1 78.66,33.1 U17.5 | |
| ADC_DIN_3V | remove | - | 72.4855,46.9005 57.8169,48.4490 | its L3 corner at (70.94, 48.45) ran along L4 LED_ON_B |
| ADC_DIN_3V | In2.Cu | 0.20 | 74.0340,45.3520 71.3,48.086 71.3,48.4 71.2,48.5 44.8,48.5 44.6968,48.4490 | |
| INP_L_B | remove | - | 58.6559,27.7707 59.3775,28.2257 59.8178,28.3993 59.9914,28.5728 60.4868,28.5728 62.1086,27.4464 | its L4 stub at y 28.23 ran 0.15 mm under L3 GATE_L_B; its via moves off that track |
| INP_L_B | B.Cu | 0.20 | 58.2009,27.3158 58.2,28.6 59.2,29.6 60.1,28.7 | |
| INP_L_B | via | 0.45/0.30 | 60.1,28.7 | |
| INP_L_B | F.Cu | 0.20 | 60.1,28.7 60.7,28.1 61.6,28.1 63.2,26.5 63.2350,26.3199 | |
| HOLD_L_B | remove | - | 53.1096,40.6495 52.6689,44.4294 | its L4 diagonal ran along L3 TH_REF's jog at (53.05, 40.03) |
| HOLD_L_B | B.Cu | 0.20 | 53.5504,40.2088 53.5504,43.2185 52.6689,44.1 52.6689,47.7685 | |
<!-- patch:end -->

## Not settled

- **Port voltage.** CIRCUIT_DESIGN_Rev0.4.md §3.1 allows about 40 mΩ for the copper and the
  module wiring of a port path; `check_routing.py` computes the board copper alone (J4's pin
  to the module's VBUS pin, HIGH range). The modules' wiring is not known on paper.
- **One GND net.** CLAUDE.md 5.4 asks for a quiet ADC ground with one defined tie; Rev0.4 has
  one GND net and no net tie, so the ADC shares L2. The port return currents run from J2/J3 to
  J4 west of the ADC block.
- **The HS pairs' impedance** stays D27's model value until JLCPCB's differential calculator
  answers; the modules and headers in each path are OI-26's.
- **D36's crossings.** Where an L3 signal crosses an L4 signal in the analog blocks, its return
  current leaves L4 for the crossing's width. `check_routing.py` holds every such pair to 45° or
  more and counts them; their effect on the measurement is not computed and is not measured
  until V-MEAS-01 on the first board.
