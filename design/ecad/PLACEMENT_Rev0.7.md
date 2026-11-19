# USB Power-Control Hub — Rev0.7 placement

> **WIP — MANUFACTURING PROHIBITED.** Where every part of Rev0.7 sits on the
> 100 × 72 mm board (D24), and why, with its silkscreen labels. Issue #6 P3 and P5, reworked
> for the machine-placed USB-C receptacles of issue #8 (D37) and the data-line taps of issue #10
> (D38), for the mirror-symmetric connectors of issue #13 (D39, Rev0.6) and for J5's clamp pads at
> the back edge (issue #14, D40, Rev0.7); placement problems
> that routing (P4) finds are fixed here, in this file.

`design/ecad/scripts/make_pcb.py` builds `source/usb-power-hub.kicad_pcb` from this file and
the captured schematic, and `design/ecad/scripts/check_pcb.py` checks the board against this
file, the capture list's placement notes and DRC (`design/ecad/README.md`). Change a position
here, never in KiCad: the next run of `make_pcb.py` rebuilds the board.

## Frame and format

- Board frame: origin at the board's lower-left corner, x to the right, y up, in mm. The
  front edge (OUT A, OUT B) is y = 0; the back edge (HOST, the 5 V input) is y = 72. On
  KiCad's sheet a board point (x, y) is at (50 + x, 122 − y), the origin make_project.py
  sets.
- `x`, `y` are the footprint's origin as the project library draws it: the centre for chips
  and passives, and the body centre for the USB-C receptacles; pin 1 for the DIP16 ADCs, the
  MAU104, the axial shunt and the fuse.
- A receptacle's opening faces its edge: J2 and J3 at Rot 0 on the front edge, J1 and J4 at
  Rot 180 on the back edge. Its front slots' centres are 1.54 mm from that edge, so its front
  face stands 1.06 mm past it (the datasheet's 2.60 mm from the slots to the product edge,
  D37). Its pads are on the board side of the slots, 4.17–5.32 mm behind them.
- `Rot` is KiCad's orientation, counter-clockwise, 0/90/180/270.
- Every part is on the top side (F.Cu), none mirrored (REQ-MFG-01).
- In the channel table, channel B is channel A moved by `dx` in x: the same y, the same
  rotation. `{x}` in a region name is `A` or `B`. The table holds the two front ends.
- Sixteen parts of each channel sheet are in the common table, because they cannot be 33.8 mm
  from their twin. R139/C114/C115 and R239/C214/C215 are the over-current threshold filters at
  U30's inputs (Rev0.7 §3.4): U30 is shared, so the two sets sit beside it. The other thirteen
  are a port's receptacle, its port parts, its button and its LEDs (J2, C116, D2, Q13, R103,
  R104, R109, R110, SW1, D10, D11, R140, R141, and channel B's): since D39 OUT B stands
  65.0 mm from OUT A, so that J3 mirrors J2 about the board's centre line (*Mirrored parts*).
- A note's `at X pin N` (also `pins N/M`, `pad N`; a receptacle's pads are named A1 to B8)
  means the part has a pad on that pin's net
  within 3.0 mm of it, centre to centre; `at X`, `next to X` and `after X` mean the two
  courtyards are within 3.0 mm. `toward X` gives a direction only. `check_pcb.py` measures
  every `at`, `next to` and `after` note, here and in the capture list, on the built board.

## Regions

The floorplan is the OI-23 study's (`design/experiments/oi-23-placement/`), changed where
the real footprints did not fit it; the changes are listed under *Deviations from the study*.
A `block` holds the parts that name it. A `mark` holds one fiducial or one mounting hole.
Regions do not overlap. A USB-C receptacle stands in its PORT block with the parts of its CC,
VBUS and discharge nets; for the region test its courtyard is cut to the board, because its
front face is past the edge.

<!-- regions:begin -->
| Region | Kind | x | y | w | h | Holds | Why |
|---|---|---:|---:|---:|---:|---|---|
| PORT_A | block | 7.0 | 0.0 | 21.0 | 15.5 | J2 and its port parts | OUT A at the front left; J2–J3 pitch 65.0 mm ≥ 18 mm (REQ-MECH-02) |
| PORT_B | block | 72.0 | 0.0 | 21.0 | 15.5 | J3 and its port parts | OUT B at the front right: PORT_A + 65.0 mm, so J3 (x 82.5) mirrors J2 (x 17.5) about the centre line x 50 |
| PORT_PWR | block | 7.0 | 57.0 | 21.0 | 15.0 | J4 and its port parts | 5 V input at the back edge, above F1 |
| PORT_HOST | block | 70.0 | 58.5 | 23.0 | 13.5 | J1 and its port parts | HOST at the back right: J1 (x 82.5) mirrors J4 (x 17.5); next to the hub strip |
| AFE_A | block | 0.5 | 19.0 | 33.1 | 30.5 | channel A front end | shunt ladder, current mirrors, comparators, port switch, hold and event FETs |
| AFE_B | block | 34.3 | 19.0 | 33.1 | 30.5 | channel B front end | AFE_A + 33.8 mm |
| ADC | block | 68 | 19 | 20.95 | 21.75 | U7, U17, C30, C31 | the two MCP3208 beside the front ends, inputs facing them; its edge with HUB, x 88.95, lies between U7's courtyard (to 88.895) and R36's (from 88.975) |
| ADCSUP | block | 68 | 41 | 20.3 | 8.5 | level shifters, DOUT dividers, VDDA and V5A filters, U3 | the ADCs' support, between them and the MCU's SPI |
| HUB | block | 88.95 | 18.5 | 10.55 | 37.5 | U6, Y2, C27–C29, R35–R38, TP13 | right-edge strip: ports A/B leave south into the corridor, HOST north to J1; the D38 taps stand on the pairs at U6 |
| PWR4 | block | 0.5 | 50.0 | 27.0 | 6.9 | F1, D6, C1, R7–R9, TP7–TP9 | J4's input: fuse, TVS after it (D25), bulk, the V_J4 divider |
| MCU | block | 28.0 | 50.0 | 23.0 | 21.5 | U1, U8, Y1, SW3, J5 and their passives | U1's channel GPIOs face the front ends (south) |
| LDO | block | 51.5 | 50.0 | 14.0 | 21.5 | U2, U30, TH_REF divider, the threshold filters | 3.3 V regulator and the over-current comparator between the channels |
| J1F | block | 66.0 | 50.0 | 22.95 | 6.0 | D5, Q53, R34, C35–C37, TP14 | J1's TVS and soft start (D35), at J1's VBUS pin |
| V12 | block | 45.4 | 7.7 | 19.6 | 7.3 | C5–C8, R10, TP3 | the MAU104's capacitors and the V12F filter, moved with U5 |
| MAU | block | 45.4 | 0.5 | 20.2 | 6.7 | U5 | the MAU104 in the front middle, between REF and OUT B's button, ≥ 6 mm from the analog parts |
| REF | block | 35.5 | 0.5 | 5.3 | 14.5 | U4, R11–R13, TP4 | V_INJ reference, between the two front ends |
| UI_A | block | 28.0 | 0.5 | 7.0 | 14.5 | SW1, D10, D11, R140, R141 | OUT A's button and LEDs beside its port |
| UI_B | block | 65.0 | 9.0 | 7.0 | 6.0 | D12, D13, R240, R241 | OUT B's LEDs, the mirror of OUT A's about x 50 |
| UI_B_SW | block | 65.65 | 0.5 | 6.35 | 8.0 | SW2 | OUT B's button, the mirror of SW1; a rectangle of its own, because the MAU104's courtyard reaches x 65.495 below y 7.2 |
| FID1 | mark | 1.0 | 8.5 | 3.0 | 3.0 | FID1 | global fiducial, front left |
| FID2 | mark | 96.0 | 8.5 | 3.0 | 3.0 | FID2 | global fiducial, front right |
| FID3 | mark | 1.0 | 61.0 | 3.0 | 3.0 | FID3 | global fiducial, back left |
| MH1 | mark | 0.0 | 0.0 | 7.0 | 7.0 | H1 | M2 clearance hole for the case's heat-set insert (D21), corner keepout |
| MH2 | mark | 93.0 | 0.0 | 7.0 | 7.0 | H2 | as MH1 |
| MH3 | mark | 0.0 | 65.0 | 7.0 | 7.0 | H3 | as MH1 |
| MH4 | mark | 93.0 | 65.0 | 7.0 | 7.0 | H4 | as MH1 |
<!-- regions:end -->

## Keepouts

No part's courtyard may enter these. Tracks may. The three lane keepouts lie inside port
blocks, where the HS pair of a receptacle runs between the corridor and its pad row; a
courtyard there would close the lane.

<!-- keepouts:begin -->
| Keepout | x | y | w | h | Why |
|---|---:|---:|---:|---:|---|
| USB_CORRIDOR | 16 | 15.5 | 73.3 | 3 | the HS pairs from U6 to J2 and J3 (the study's corridor) |
| USB_UP_LANE | 82.1 | 56.5 | 17.4 | 2 | the HS pair from J1 down the right edge to U6 |
| USB_LANE_A | 16.1 | 8.5 | 1.8 | 7 | the HS pair from the corridor down to J2's pads |
| USB_LANE_B | 81.1 | 8.5 | 1.8 | 7 | the HS pair from the corridor down to J3's pads |
| USB_UP_RISER | 82.1 | 58.5 | 1.8 | 6.1 | the HS pair from the lane keepout above up to J1's pads |
<!-- keepouts:end -->

## USB-C receptacles

J1–J4 are the SHOU HAN TYPE-C 16PIN 2MD(073) receptacle, C2765186, machine-placed on Top
(D37). The body is 8.94 × 7.35 mm and the courtyard 10.14 × 8.42 mm. One row of 12 SMD pads
lies 3.67 mm behind the origin, the two NPTH pegs just in front of it, and four plated shell
slots on both sides of it (`library.json`, measured by `check_libraries.py`).

- The front face stands 1.06 mm past the board edge, the overhang the Rev0.4 module's
  receptacle had; V-MECH-01 measures it with the case and a real plug. For the region test
  the courtyard is cut to the outline (*Regions*).
- The HS pair reaches the pad row through a lane from the corridor (*Keepouts*), so no
  courtyard stands in a lane.
- A port's own parts stand beside its receptacle: the CC network west of the lane, the port
  capacitor and the discharge circuit east of it (Rev0.7 §3.1).

## Common parts

<!-- place:begin -->
| Ref | x | y | Rot | Region | Note |
|---|---:|---:|---:|---|---|
| C1 | 13.25 | 55.8 | 180 | PWR4 | VBUS_IN, next to R7 |
| C2 | 52.9 | 62.65 | 90 | LDO | at U2 pin 3 |
| C3 | 52.9 | 66.25 | 90 | LDO | at U2 pin 2 |
| C4 | 34.15 | 62.6 | 90 | MCU | V3V3 bulk, next to U1 beside the decoupler column |
| C5 | 47.9 | 8.7 | 90 | V12 | at U5 pin 1 |
| C6 | 60.6 | 8.7 | 90 | V12 | at U5 pin 6 |
| C7 | 59.5 | 11.6 | 90 | V12 | at R10 pin 2 |
| C8 | 56.6 | 9.6 | 180 | V12 | at R10 pin 2 |
| C9 | 83.4 | 47.05 | 90 | ADCSUP | VDDA, next to TP6 |
| C10 | 86.3 | 47.15 | 0 | ADCSUP | V5A, next to TP2 |
| C11 | 56.6 | 56.8 | 90 | LDO | TH_REF, next to R139 |
| C12 | 39.25 | 52.6 | 180 | MCU | at U1 pin 1, clear of its pin-1 mark |
| C13 | 42.85 | 52.8 | 180 | MCU | at U1 pin 10 |
| C14 | 47.35 | 60.2 | 90 | MCU | at U1 pin 22 |
| C15 | 43.2 | 63.98 | 0 | MCU | at U1 pin 33 (IOVDD) |
| C16 | 39.6 | 63.98 | 0 | MCU | at U1 pin 42 (IOVDD) |
| C17 | 36.2 | 57.74 | 180 | MCU | at U1 pin 49 (IOVDD) |
| C18 | 36.2 | 58.85 | 180 | MCU | at U1 pin 48 (USB_VDD), below the USB pins |
| C19 | 36.2 | 62.57 | 180 | MCU | at U1 pin 43 (ADC_AVDD) |
| C20 | 36.2 | 61.46 | 180 | MCU | at U1 pin 44 (VREG_VIN) |
| C21 | 36.2 | 60.35 | 180 | MCU | at U1 pin 45 (VREG_VOUT) |
| C22 | 48.5 | 60.25 | 90 | MCU | at U1 pin 23 |
| C23 | 36.2 | 56.63 | 180 | MCU | at U1 pin 50 (DVDD) |
| C24 | 34.05 | 56.62 | 180 | MCU | at U8 pin 8 |
| C25 | 49.65 | 54.2 | 0 | MCU | at Y1 pin 1 |
| C26 | 50.09 | 59.85 | 0 | MCU | at Y1 pin 3 |
| C27 | 93.1 | 30.25 | 180 | HUB | at U6 pin 26 |
| C28 | 91.05 | 30.25 | 180 | HUB | at U6 pin 28 |
| C29 | 92.3 | 32.6 | 90 | HUB | at U6 pin 28 |
| C30 | 70.1 | 29.5 | 0 | ADC | at U7 pin 16 |
| C31 | 72.65 | 29.5 | 0 | ADC | at U7 pin 15 |
| C32 | 69.55 | 42 | 90 | ADCSUP | at U17 pin 16 |
| C33 | 72.1 | 42 | 90 | ADCSUP | at U17 pin 15 |
| C34 | 57.95 | 56.8 | 90 | LDO | at U30 pin 8 |
| C35 | 84.9 | 51.9 | 180 | J1F | GJ1, next to C37 |
| C36 | 84.4 | 53.7 | 90 | J1F | GJ1, next to R34 |
| C37 | 85.55 | 53.55 | 90 | J1F | GJ1, next to C36 |
| C114 | 52.2 | 56.8 | 90 | LDO | THO_A, next to R139 |
| C115 | 55.45 | 56.85 | 270 | LDO | THO_A, next to R139 |
| C214 | 61.5 | 51.1 | 0 | LDO | THO_B, next to R239 |
| C215 | 59.85 | 54.05 | 270 | LDO | EN_G_B, next to U30 |
| D1 | 78.9 | 61.6 | 180 | PORT_HOST | J1 CC ESD, at J1 |
| D4 | 17.25 | 62.3 | 270 | PORT_PWR | J4 CC ESD, at J4 |
| D5 | 89.35 | 61.8 | 0 | PORT_HOST | J1 VBUS TVS, at J1 |
| D6 | 18.8 | 53.3 | 0 | PWR4 | VBUS_IN TVS after F1 (D25) |
| F1 | 5 | 52.55 | 0 | PWR4 | J4's fuse, pad 1 toward J4's VBUS pads |
| FB1 | 82.3 | 44.4 | 180 | ADCSUP | V3V3, next to R14 |
| FID1 | 2.5 | 10 | 0 | FID1 | global fiducial |
| FID2 | 97.5 | 10 | 0 | FID2 | global fiducial |
| FID3 | 2.5 | 62.5 | 0 | FID3 | global fiducial |
| H1 | 3.5 | 3.5 | 0 | MH1 | M2 clearance hole, front left; the screw goes into the case's heat-set insert (D21) |
| H2 | 96.5 | 3.5 | 0 | MH2 | M2 clearance hole, front right; the screw goes into the case's heat-set insert (D21) |
| H3 | 3.5 | 68.5 | 0 | MH3 | M2 clearance hole, back left; the screw goes into the case's heat-set insert (D21) |
| H4 | 96.5 | 68.5 | 0 | MH4 | M2 clearance hole, back right; the screw goes into the case's heat-set insert (D21) |
| J1 | 82.5 | 69.385 | 180 | PORT_HOST | HOST receptacle; front face 1.06 mm past the back edge |
| J4 | 17.5 | 69.385 | 180 | PORT_PWR | 5 V input receptacle; front face 1.06 mm past the back edge |
| J5 | 44.5 | 69.13 | 0 | MCU | SWD pads for a clamp (2 x 4 at 2.54 mm), north of U1; the edge row stands 1.6 mm inside the back edge (issue #14) |
| Q50 | 72.05 | 44.8 | 0 | ADCSUP | ADC_SCLK, next to R27 |
| Q51 | 76.4 | 42.75 | 0 | ADCSUP | ADC_CS, next to R28 |
| Q52 | 76.15 | 46.4 | 0 | ADCSUP | ADC_DIN, next to R29 |
| Q53 | 82.05 | 53 | 270 | J1F | GJ1, next to C36 |
| R1 | 75.8 | 60.4 | 0 | PORT_HOST | J1 Rd CC1 |
| R2 | 75.8 | 62.8 | 0 | PORT_HOST | J1 Rd CC2 |
| R3 | 20.9 | 61 | 0 | PORT_PWR | J4 Rd CC1 |
| R4 | 13.6 | 61 | 0 | PORT_PWR | J4 Rd CC2 |
| R5 | 20.9 | 62.4 | 0 | PORT_PWR | CC1_J4, next to R3 |
| R6 | 13.6 | 62.4 | 0 | PORT_PWR | CC2_J4, next to R4 |
| R7 | 16.15 | 56.25 | 0 | PWR4 | V_J4, next to R8 |
| R8 | 18.25 | 56.25 | 0 | PWR4 | V_J4, next to R7 |
| R9 | 25.95 | 51.7 | 0 | PWR4 | V_J4, next to TP9 |
| R10 | 59.45 | 8.7 | 90 | V12 | at U5 pin 6 |
| R11 | 39.35 | 10.85 | 180 | REF | V_INJ, next to R12 |
| R12 | 37.75 | 10.4 | 90 | REF | INJ_REF, next to R13 |
| R13 | 36.6 | 10.15 | 270 | REF | INJ_REF, next to R12 |
| R14 | 81.35 | 42.5 | 180 | ADCSUP | VREF_CHK, next to R15 |
| R15 | 79 | 42.15 | 270 | ADCSUP | VREF_CHK, next to R14 |
| R16 | 72.35 | 47.65 | 270 | ADCSUP | V5L, next to R27 |
| R17 | 61.5 | 52.25 | 180 | LDO | TH_REF, next to R239 |
| R18 | 61.05 | 53.9 | 90 | LDO | TH_REF, next to R17 |
| R19 | 63.45 | 54.4 | 0 | LDO | TH_LO, next to R18 |
| R20 | 34.2 | 59 | 180 | MCU | USB D+ 22 ohm, next to U1: the pair leaves pins 46/47 west |
| R21 | 41.7 | 65.6 | 0 | MCU | USB D+ 5.1 ohm, next to U1 |
| R22 | 34.2 | 60.13 | 180 | MCU | USB D- 22 ohm, next to U1 |
| R23 | 38.5 | 65.36 | 0 | MCU | USB D- 5.1 ohm, next to U1, where the pair turns east |
| R24 | 47.85 | 61.85 | 0 | MCU | XTAL1_OUT, next to C26 |
| R25 | 29.5 | 57.1 | 90 | MCU | BOOTSEL, next to U8 at its pin 1 |
| R26 | 45.35 | 64 | 0 | MCU | RUN, next to TP11 |
| R27 | 73.55 | 47.65 | 270 | ADCSUP | V5L, next to R16 |
| R28 | 79 | 44.5 | 270 | ADCSUP | V5L, next to R29 |
| R29 | 80.15 | 44.6 | 90 | ADCSUP | V5L, next to R28 |
| R30 | 69 | 43.6 | 180 | ADCSUP | DOUT_A_3V, next to R31 |
| R31 | 68.6 | 46.85 | 90 | ADCSUP | DOUT_A_3V, next to R30 |
| R32 | 69 | 48.5 | 180 | ADCSUP | DOUT_B_3V, next to R33 |
| R33 | 70.2 | 47.35 | 0 | ADCSUP | DOUT_B_3V, next to R32 |
| R34 | 84.95 | 55.3 | 0 | J1F | GJ1, next to C36 |
| R139 | 53.85 | 56.4 | 180 | LDO | THO_A, next to C114 |
| R239 | 59.9 | 51.9 | 270 | LDO | at U30 pin 5 |
| SW3 | 31.85 | 68.6 | 0 | MCU | BOOTSEL button, under the lid pinhole |
| TP1 | 64.45 | 52.05 | 0 | LDO | V5L, toward R16 pin 1 |
| TP2 | 87.25 | 44.95 | 0 | ADCSUP | V5A, next to C10 |
| TP3 | 61.7 | 10.9 | 0 | V12 | at R10 pin 2 |
| TP4 | 38.3 | 8.25 | 0 | REF | V_INJ, next to R12 |
| TP5 | 54.5 | 59.2 | 0 | LDO | V3V3, next to U2 |
| TP6 | 85 | 44.15 | 0 | ADCSUP | VDDA, next to C9 |
| TP7 | 8.05 | 55.8 | 0 | PWR4 |  |
| TP8 | 10.3 | 55.8 | 0 | PWR4 | VBUS_IN, next to F1 |
| TP9 | 23.8 | 51.85 | 0 | PWR4 | V_J4, next to R9 |
| TP10 | 48 | 63.55 | 0 | MCU | DVDD, next to C22 |
| TP11 | 45.75 | 65.7 | 0 | MCU | RUN, next to R26 |
| TP12 | 48 | 65.75 | 0 | MCU | CLKOUT, next to U1 |
| TP13 | 95.25 | 30.8 | 0 | HUB | VDD33_HUB, next to U6 |
| TP14 | 87.25 | 53.15 | 0 | J1F | VBUS_J1, next to C37 |
| U1 | 42.2 | 58.4 | 90 | MCU | rot 90: channel GPIOs south, SPI and crystal east, USB and QSPI west |
| U2 | 58.5 | 64 | 0 | LDO | AMS1117 |
| U3 | 80.25 | 47.45 | 0 | ADCSUP | VREF_CHK, next to R15 |
| U4 | 37.8 | 13.25 | 180 | REF | INJ_REF, next to R12 |
| U5 | 47.85 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |
| U6 | 94 | 27 | 0 | HUB | ports A/B south to the corridor, HOST east, MCU port west |
| U7 | 69.6 | 20.15 | 90 | ADC | inputs 1-3 on the south-west row, facing the front ends |
| U8 | 33 | 53.05 | 0 | MCU | QSPI flash south-west of U1, pins 5-8 toward U1 pins 51-56 |
| U17 | 69.6 | 32 | 90 | ADC | as U7, above it |
| U30 | 55.5 | 53 | 0 | LDO | over-current comparator, both channels |
| Y1 | 49.1 | 57 | 90 | MCU | next to U1 at its pins 20/21 |
| Y2 | 94 | 21.8 | 0 | HUB | next to U6 at its pins 11/12; moved 0.5 mm down in P4, so the lead-ins of pairs A and B pass above it |
| R35 | 92.1 | 19.3 | 0 | HUB | D38 tap, USB_A_P on U6's pair |
| R36 | 89.9 | 19.3 | 180 | HUB | D38 tap, USB_A_N on U6's pair |
| R37 | 98.1 | 19.3 | 0 | HUB | D38 tap, USB_B_P on U6's pair |
| R38 | 95.9 | 19.3 | 180 | HUB | D38 tap, USB_B_N on U6's pair |
| C116 | 21.3 | 9.2 | 0 | PORT_A | port capacitor, at J2 pad B4 |
| D2 | 14.1 | 11.3 | 180 | PORT_A | CC ESD, next to J2, west of the lane |
| D10 | 29.75 | 10.5 | 0 | UI_A | OUT A ON LED |
| D11 | 29.75 | 13 | 0 | UI_A | OUT A FAULT LED |
| J2 | 17.5 | 2.615 | 0 | PORT_A | OUT A receptacle; front face 1.06 mm past the front edge |
| Q13 | 25 | 11.9 | 0 | PORT_A | discharge FET |
| R103 | 12.4 | 8.9 | 0 | PORT_A | Rp CC1 |
| R104 | 12.4 | 14.2 | 0 | PORT_A | Rp CC2 |
| R109 | 22 | 13.2 | 0 | PORT_A | Q13 gate resistor |
| R110 | 24.4 | 8.9 | 0 | PORT_A | discharge resistor, next to C116 |
| R140 | 33.25 | 10.5 | 180 | UI_A | D10 series |
| R141 | 33.25 | 13 | 180 | UI_A | D11 series |
| SW1 | 31.5 | 4.5 | 90 | UI_A | OUT A button |
| C216 | 86.3 | 9.2 | 0 | PORT_B | port capacitor, at J3 pad B4 |
| D3 | 79.1 | 11.3 | 180 | PORT_B | CC ESD, next to J3, west of the lane |
| D12 | 70.25 | 10.5 | 180 | UI_B | OUT B ON LED |
| D13 | 70.25 | 13 | 180 | UI_B | OUT B FAULT LED |
| J3 | 82.5 | 2.615 | 0 | PORT_B | OUT B receptacle; front face 1.06 mm past the front edge |
| Q33 | 90 | 11.9 | 0 | PORT_B | discharge FET |
| R203 | 77.4 | 8.9 | 0 | PORT_B | Rp CC1 |
| R204 | 77.4 | 14.2 | 0 | PORT_B | Rp CC2 |
| R209 | 87 | 13.2 | 0 | PORT_B | Q33 gate resistor |
| R210 | 89.4 | 8.9 | 0 | PORT_B | discharge resistor, next to C216 |
| R240 | 66.75 | 10.5 | 0 | UI_B | D12 series |
| R241 | 66.75 | 13 | 0 | UI_B | D13 series |
| SW2 | 68.5 | 4.5 | 90 | UI_B_SW | OUT B button |
<!-- place:end -->

## Channel parts

<!-- channel:begin dx=33.8 -->
| Ref A | Ref B | x | y | Rot | Region | Note |
|---|---|---:|---:|---:|---|---|
| C101 | C201 | 5.05 | 39 | 180 | AFE_{x} | GSW_A, next to C102 |
| C102 | C202 | 5.05 | 37.85 | 180 | AFE_{x} | GSW_A, next to C101 |
| C103 | C203 | 5.4 | 32.3 | 0 | AFE_{x} | at U10 pin 7 |
| C104 | C204 | 2.26 | 30.45 | 0 | AFE_{x} | at Q21 drain |
| C105 | C205 | 16.4 | 32.3 | 0 | AFE_{x} | at U11 pin 7 |
| C106 | C206 | 13.26 | 30.25 | 0 | AFE_{x} | at Q22 drain |
| C107 | C207 | 27.4 | 32.3 | 0 | AFE_{x} | at U12 pin 7 |
| C108 | C208 | 24.26 | 30.25 | 0 | AFE_{x} | at Q23 drain |
| C109 | C209 | 23.1 | 40.65 | 90 | AFE_{x} | at U13 pin 8 |
| C110 | C210 | 30.3 | 36.3 | 0 | AFE_{x} | at U13 pin 3 |
| C111 | C211 | 23.1 | 34.55 | 270 | AFE_{x} | at U13 pin 1 |
| C112 | C212 | 30.3 | 40.95 | 0 | AFE_{x} | at U13 pin 5 |
| C113 | C213 | 26.6 | 41.95 | 0 | AFE_{x} | at U13 pin 7 |
| Q10 | Q30 | 2.5 | 47.5 | 0 | AFE_{x} | SRC_A, next to R101 |
| Q11 | Q31 | 2.25 | 40.55 | 270 | AFE_{x} | GSW_A, next to R101 |
| Q12 | Q32 | 16 | 42.25 | 180 | AFE_{x} | EN_G_A, next to R106 |
| Q14 | Q34 | 16.25 | 36.95 | 270 | AFE_{x} | EN_G_A, next to Q12 |
| Q15 | Q35 | 11 | 35 | 90 | AFE_{x} | DIS_A, next to Q14 |
| Q16 | Q36 | 5.85 | 41.6 | 270 | AFE_{x} | SRC_A, next to R101 |
| Q17 | Q37 | 29.865 | 21 | 270 | AFE_{x} | bypasses R_M and R_L: LAD1 to VBUS |
| Q18 | Q38 | 26.325 | 21 | 270 | AFE_{x} | bypasses R_L: LAD2 to VBUS |
| Q19 | Q39 | 26.5 | 44.55 | 270 | AFE_{x} | HOLD_M_A, next to R115 |
| Q20 | Q40 | 21.85 | 37.6 | 270 | AFE_{x} | GL_A, next to R118 |
| Q21 | Q41 | 2.26 | 26.3 | 90 | AFE_{x} | H mirror FET, source at U10 pin 2 |
| Q22 | Q42 | 13.26 | 26.3 | 90 | AFE_{x} | M mirror FET |
| Q23 | Q43 | 24.26 | 26.3 | 90 | AFE_{x} | L mirror FET |
| Q24 | Q44 | 22.55 | 47.7 | 180 | AFE_{x} | EVTG_M_A, toward R117 pin 2 |
| Q25 | Q45 | 20.8 | 43.8 | 90 | AFE_{x} | EVTG_L_A, toward R118 pin 2 |
| R101 | R201 | 3 | 43.15 | 0 | AFE_{x} | SRC_A, next to Q16 |
| R102 | R202 | 8.85 | 41.15 | 180 | AFE_{x} | GSW_A, next to Q16 |
| R105 | R205 | 10 | 48 | 270 | AFE_{x} | EN_G_A, toward R107 pin 1 |
| R106 | R206 | 16.35 | 44.65 | 180 | AFE_{x} | EN_G_A, next to R107 |
| R107 | R207 | 16.3 | 46.25 | 90 | AFE_{x} | EN_G_A, next to R106 |
| R108 | R208 | 17.45 | 46.85 | 270 | AFE_{x} | V3V3, toward R116 pin 1 |
| R111 | R211 | 7.75 | 44.2 | 180 | AFE_{x} | QB_A, next to R112 |
| R112 | R212 | 5.7 | 44.2 | 180 | AFE_{x} | QB_A, next to R111 |
| R113 | R213 | 30.4 | 23.6 | 180 | AFE_{x} | Q17 gate to source |
| R114 | R214 | 28.3 | 23.6 | 0 | AFE_{x} | Q18 gate to source |
| R115 | R215 | 28.9 | 44.8 | 90 | AFE_{x} | at Q19 pin 1 |
| R116 | R216 | 21.9 | 40.65 | 270 | AFE_{x} | at Q20 pin 1 |
| R117 | R217 | 23.65 | 42.25 | 180 | AFE_{x} | at U13 pin 7 |
| R118 | R218 | 21.5 | 35 | 180 | AFE_{x} | at U13 pin 1 |
| R119 | R219 | 2.6 | 23.6 | 0 | AFE_{x} | at RS10 pad 2 (sense) |
| R120 | R220 | 4.6 | 23.6 | 180 | AFE_{x} | V_INJ into X_H |
| R121 | R221 | 7.6 | 23.6 | 0 | AFE_{x} | at RS10 pad 3 (sense) |
| R122 | R222 | 7.6 | 32.3 | 0 | AFE_{x} | U10 pin 6 to Q21 gate |
| R123 | R223 | 2.26 | 29.1 | 0 | AFE_{x} | H mirror load at Q21 drain |
| R124 | R224 | 2.26 | 31.55 | 0 | AFE_{x} | AMP_H to the ADC |
| R125 | R225 | 10.3 | 23.6 | 0 | AFE_{x} | at RS11 pad 2 (sense) |
| R126 | R226 | 12.6 | 23.6 | 180 | AFE_{x} | V_INJ into X_M |
| R127 | R227 | 19.45 | 23.6 | 180 | AFE_{x} | at RS11 pad 3 (sense) |
| R128 | R228 | 18.6 | 32.3 | 0 | AFE_{x} | U11 pin 6 to Q22 gate |
| R129 | R229 | 13.26 | 28.85 | 0 | AFE_{x} | M mirror load at Q22 drain |
| R130 | R230 | 13.26 | 31.7 | 0 | AFE_{x} | AMP_M to the ADC |
| R131 | R231 | 21.5 | 23.6 | 180 | AFE_{x} | at RS12 pad 2 (sense) |
| R132 | R232 | 26.3 | 23.6 | 180 | AFE_{x} | V_INJ into X_L |
| R133 | R233 | 23.85 | 23.6 | 0 | AFE_{x} | at RS12 pad 3 (sense) |
| R134 | R234 | 29.6 | 32.3 | 0 | AFE_{x} | U12 pin 6 to Q23 gate |
| R135 | R235 | 24.26 | 28.85 | 0 | AFE_{x} | L mirror load at Q23 drain |
| R136 | R236 | 24.26 | 31.7 | 0 | AFE_{x} | AMP_L to the ADC |
| R137 | R237 | 30.35 | 35.1 | 180 | AFE_{x} | at U13 pin 3 |
| R138 | R238 | 29.9 | 39.3 | 90 | AFE_{x} | at U13 pin 5 |
| RS10 | RS20 | 4.595 | 21 | 0 | AFE_{x} | R_H: VSUP enters at pad 1 (west); sense pads north |
| RS11 | RS21 | 9.785 | 21 | 0 | AFE_{x} | R_M after R_H; sense pads north |
| RS12 | RS22 | 22.81 | 20.5 | 0 | AFE_{x} | R_L after R_M; pad 4 toward the port's VBUS pads |
| TP101 | TP201 | 6.8 | 34.05 | 0 | AFE_{x} | at R122 pin 1 |
| TP102 | TP202 | 3.7 | 34.05 | 0 | AFE_{x} | GATE_H_A, next to R122 |
| TP103 | TP203 | 27.5 | 47.7 | 0 | AFE_{x} | at Q19 pin 1 |
| TP104 | TP204 | 19.3 | 34.45 | 0 | AFE_{x} | HOLD_L_A, next to Q20 |
| TP105 | TP205 | 2.95 | 37.35 | 0 | AFE_{x} | VSUP_A, next to C102 |
| TP106 | TP206 | 31.75 | 32.9 | 0 | AFE_{x} | VBUS test pad |
| U10 | U20 | 6.8 | 28 | 90 | AFE_{x} | H amplifier, inputs south toward RS10 |
| U11 | U21 | 17.8 | 28 | 90 | AFE_{x} | M amplifier |
| U12 | U22 | 28.8 | 28 | 90 | AFE_{x} | L amplifier |
| U13 | U23 | 26.5 | 37.6 | 90 | AFE_{x} | range comparators between the M/L amplifiers and Q17/Q18 |
<!-- channel:end -->

## Mirrored parts

D39 (issue #13): the user found the connectors' positions odd (「なんかUSBの位置がアシンメトリーで変だね」)
and chose the mirrored placement C2 of issue #12 (「C2 で進める」). Each pair below stands mirrored
about the board's centre line, x = `axis`: the two x add up to 100.0, the y is the same, and the
rotation is the same or the mirrored one (180 − Rot). `check_pcb.py` holds every row on the
built board.

<!-- mirror:begin axis=50.0 -->
| Ref A | Ref B | Why |
|---|---|---|
| J2 | J3 | OUT A and OUT B on the front edge, x 17.5 and 82.5 |
| J4 | J1 | the 5 V input and HOST on the back edge, x 17.5 and 82.5 |
| SW1 | SW2 | the port buttons, x 31.5 and 68.5 |
| D10 | D12 | the ON LEDs, x 29.75 and 70.25 |
| D11 | D13 | the FAULT LEDs |
| R140 | R240 | the ON LEDs' resistors, on the inner side of each LED |
| R141 | R241 | the FAULT LEDs' resistors |
<!-- mirror:end -->

What is mirrored is the origin of each of these parts, which is what the case's openings, the
buttons' plungers and the light pipes follow. A pair is the same part twice, not a mirror
image: both receptacles' pad rows run the same way, and each port's own parts (CC network,
port capacitor, discharge) are OUT A's moved by 65.0 mm, not mirrored. Nothing between the
connectors is symmetric: the front ends stay 33.8 mm apart at the left, and the ADCs, the hub
strip and the MAU104 stand where they fit.

## Silkscreen

The labels CLAUDE.md §6 asks of the board (P5): the product name and revision, a port label
beside each USB-C receptacle, the net name at every test pad, and, since release r02 (issue #13,
2026-11-19), the names of the SWD pads, `BOOT` at SW3 and the reference of each hand-soldered
part. `make_pcb.py` writes each row as a text on F.SilkS, with its leader, after the routing;
`check_silk.py` checks them.

- `x`, `y` are the text's centre in the board frame; `Rot` is 0 (left to right) or 90 (bottom
  to top). `Width` and `Height` are KiCad's glyph size and `Stroke` the line width, in mm.
  JLCPCB's legend limits are a 1.0 mm text height, a 0.15 mm line and a line-to-height ratio
  of 1:6 (pcb-capabilities, Legend, read 2026-11-06), so a stroke is at least
  max(0.15, height / 6): 0.17 mm at 1.0 mm, 0.2 mm at 1.2 mm. A 0.8 mm width keeps the
  1.0 mm height and is used where a long name has no room at 1.0.
- A label without a leader sits beside its test pad: within 1.5 mm of the pad, and its centre
  is nearer that pad than any other test pad's. Where no such spot is free, `Leader` gives a
  0.15 mm silk line as board points, from the label to 0.3 mm off its pad's edge. TP8's leader
  runs under TP7 because J4's outline and F1 close every straight path; GATE_H_x's labels sit
  above OUT_H_x's pads, so both of those pads have leaders. TP11's label stands 6.3 mm west of
  its pad, the nearest of seven spots that clear the strip's parts and silk, with a 4.0 mm leader.
- The port labels sit just outside their receptacle's courtyard, on the board, so they stay
  visible with the receptacle soldered and are not under the case's port openings, which are
  at the board edge. Each stands on its receptacle's outer side, so the four are mirrored like
  the receptacles (D39).
- Two labels on one line stand at least 1.0 mm apart, one glyph: `DVDD` and `CLKOUT` stood
  0.30 mm apart until r02 and read as one word in the render, as did `V_J4` beside `HOLD_M_A`
  (0.33 mm) and `HOLD_M_B` beside `V5L` (0.27 mm). `DVDD` moved 0.95 mm down its line, `V_J4`
  above its pad and `V5L` to the right of its pad.
- Reference designators stay hidden (300 at 1.0 mm do not fit); the assembly drawing carries
  them. The eight hand-soldered parts are the exception, since r02: the user places them by
  hand, so each has its reference within 1.5 mm of its courtyard (`F1`, `U5`, `U7`, `U17`,
  `RS10`, `RS11`, `RS20`, `RS21`). Pin 1 and polarity are the footprints' own marks
  (check_libraries.py keeps them on every polar part).
- J5's eight pads stand 0.84 mm apart, 1.6 mm inside the back edge, and a clamp's pins land on
  them, so their names are not between them: they are
  a legend to the right of J5: one row per pad row, the odd pads (the edge row) above the even
  ones as on
  the board, each pad as `<number> <net>` from left to right (`NC`: no net). `SWD` stands left
  of J5 and `BOOT` left of SW3. SW1 and SW2, the port buttons, have no label on this board:
  each stands beside its port's receptacle, and the lid carries their legend.

<!-- silk:begin -->
| Label | Text | x | y | Rot | Width | Height | Stroke | Leader |
|---|---|---:|---:|---:|---:|---:|---:|---|
| title | USB Power-Control Hub | 66 | 16 | 0 | 1.2 | 1.2 | 0.2 | - |
| revision | Rev0.7 | 82.5 | 16 | 0 | 1.2 | 1.2 | 0.2 | - |
| J1 | HOST | 90.4 | 69.5 | 0 | 1 | 1 | 0.17 | - |
| J2 | OUT A | 9.6 | 3 | 0 | 1 | 1 | 0.17 | - |
| J3 | OUT B | 90.4 | 3 | 0 | 1 | 1 | 0.17 | - |
| J4 | 5V IN | 9.6 | 69.5 | 0 | 0.8 | 1 | 0.17 | - |
| TP1 | V5L | 67 | 52.05 | 0 | 1 | 1 | 0.17 | - |
| TP2 | V5A | 87.4 | 43.25 | 0 | 1 | 1 | 0.17 | - |
| TP3 | V12F | 62.3 | 12.5 | 0 | 1 | 1 | 0.17 | - |
| TP4 | V_INJ | 38.35 | 6.55 | 0 | 1 | 1 | 0.17 | - |
| TP5 | V3V3 | 57.35 | 59.15 | 0 | 1 | 1 | 0.17 | - |
| TP6 | VDDA | 85 | 41.75 | 0 | 1 | 1 | 0.17 | - |
| TP7 | GND | 5.55 | 56.75 | 0 | 1 | 1 | 0.17 | - |
| TP8 | VBUS_IN | 3.6 | 55.2 | 0 | 1 | 1 | 0.17 | 6.7,54.7 10.3,54.7 10.3,55.0 |
| TP9 | V_J4 | 24.5 | 53.6 | 0 | 1 | 1 | 0.17 | - |
| TP10 | DVDD | 49.7 | 62.6 | 90 | 1 | 1 | 0.17 | - |
| TP11 | RUN | 37.6 | 66.9 | 0 | 1 | 1 | 0.17 | 39.15,66.55 44.3,66.55 45,66.25 |
| TP12 | CLKOUT | 50.45 | 68.4 | 90 | 1 | 1 | 0.17 | - |
| TP13 | VDD33_HUB | 97.25 | 30.85 | 90 | 1 | 1 | 0.17 | - |
| TP14 | VBUS_J1 | 87.3 | 50.7 | 0 | 1 | 1 | 0.17 | - |
| TP101 | OUT_H_A | 10.2 | 29.85 | 90 | 0.8 | 1 | 0.17 | 9.569,32.373 7.546,33.761 |
| TP102 | GATE_H_A | 6.7 | 36.65 | 0 | 0.8 | 1 | 0.17 | 3.986,36.016 3.819,34.841 |
| TP103 | HOLD_M_A | 29.3 | 49.4 | 0 | 1 | 1 | 0.17 | - |
| TP104 | HOLD_L_A | 21.2 | 30.9 | 90 | 1 | 1 | 0.17 | - |
| TP105 | VSUP_A | 1.15 | 36.35 | 90 | 0.8 | 1 | 0.17 | - |
| TP106 | VBUS_A | 33.45 | 32.9 | 90 | 1 | 1 | 0.17 | - |
| TP201 | OUT_H_B | 44 | 29.8 | 90 | 1 | 1 | 0.17 | 43.369,32.909 41.344,33.755 |
| TP202 | GATE_H_B | 40.7 | 36.65 | 0 | 0.8 | 1 | 0.17 | 37.929,36.016 37.674,34.831 |
| TP203 | HOLD_M_B | 61.95 | 49.4 | 0 | 1 | 1 | 0.17 | - |
| TP204 | HOLD_L_B | 55 | 30.9 | 90 | 1 | 1 | 0.17 | - |
| TP205 | VSUP_B | 33.35 | 37.55 | 0 | 0.8 | 1 | 0.17 | - |
| TP206 | VBUS_B | 67.25 | 32.95 | 90 | 1 | 1 | 0.17 | - |
| SW3 | BOOT | 26 | 68.6 | 0 | 1 | 1 | 0.17 | - |
| J5 | SWD | 37.58 | 70.25 | 0 | 1 | 1 | 0.17 | - |
| J5.odd | 1 SWDIO 3 GND 5 GND 7 SWCLK | 61.6 | 70.3 | 0 | 0.8 | 1 | 0.17 | - |
| J5.even | 2 V3V3 4 RUN 6 NC 8 NC | 60.07 | 68.9 | 0 | 0.8 | 1 | 0.17 | - |
| F1 | F1 | 7.5 | 49.5 | 0 | 1 | 1 | 0.17 | - |
| U5 | U5 | 51.5 | 8.5 | 0 | 1 | 1 | 0.17 | - |
| U7 | U7 | 90.25 | 23 | 0 | 1 | 1 | 0.17 | - |
| U17 | U17 | 90.6 | 36 | 0 | 1 | 1 | 0.17 | - |
| RS10 | RS10 | 4.6 | 18 | 0 | 1 | 1 | 0.17 | - |
| RS11 | RS11 | 14.9 | 18 | 0 | 1 | 1 | 0.17 | - |
| RS20 | RS20 | 38.4 | 18 | 0 | 1 | 1 | 0.17 | - |
| RS21 | RS21 | 48.7 | 18 | 0 | 1 | 1 | 0.17 | - |
<!-- silk:end -->

## Deviations from the study

| Study | Here | Why |
|---|---|---|
| R_AFEA / R_AFEB 27 × 31 mm | AFE_A / AFE_B 33.1 × 30.5 mm | the library's courtyards are larger than the study's planning ones (an SOT-23 is 13.8 mm², not 10.3); at 27 mm the channel filled 72 % before routing |
| J2 / J3 as modules at x 18 / 46 | receptacles at x 17.5 / 82.5 (pitch 65.0 mm) | D37: a receptacle, its origin the body centre, not the module's pin 1. D39: J3 mirrors J2 about x 50 (until Rev0.5 it stood at its own front end, x 51.3, pitch 33.8 mm), so OUT B's port parts are 31.2 mm east of channel B's front end and VBUS_B crosses that distance on L4 (`ROUTING_Rev0.7.md`) |
| J1 / J4 as modules at the back edge | receptacles, J1 at x 82.5 and J4 at x 17.5 | D37: 1.06 mm past the back edge, J4 above F1. D39: J1 mirrors J4; it moved 6.5 mm east of Rev0.5's x 76.0, toward the hub strip, and its TVS and soft start (J1F) with it |
| U7 / U17 at x 55.5 / 65.8, upright | stacked at x 68, rotated 90° | the wider front ends took that space; turned, each ADC's inputs face the front ends |
| MAU104 at (82, 30), turned | front middle, courtyard (45.5, 0.55)–(65.5, 7.15) | the ADCs took its region, and since D39 OUT B's port parts the front right, where it stood until Rev0.5. Its courtyard is 6.15 mm from R11's in REF, the nearest analog part (the rule is ≥ 6.0 mm, `check_pcb.py`), and 0.21 mm from SW2's: a window 0.39 mm wide in x. In Rev0.5 the nearest analog part was U7 at 11.95 mm, and REF was 32.34 mm away |
| R_MCUF (SW3, J5, test pads) at the front | in MCU, beside U1 | REQ-BOOT-02 needs only a lid pinhole, and the lid is a PCB with its own drill; SWD stays at U1 |
| U30 with R_LDO's OC block | in LDO, with both channels' threshold filters | as the study; the filters are not in the channel template (see the format notes) |
| parts in a strip under each module | none under a receptacle | D37: the receptacle has no header and no space under it, so those parts stand beside the lane |
| U1's decouplers, the crystal Y1 and the parts around them, 0.45–0.65 mm from U1's pads | 22 parts 0.4–0.8 mm further out | P4, issue #8: a 0.4 mm-pitch QFN needs a lane between each pad and the part in front of it. Two router runs whose inputs differed only in these parts' positions left 80 connections open, most at U1's pins, and then 33 |

## Not settled here

- Routing (P4) can move any part; this file then changes, not the board.
- The receptacle's overhang (1.06 mm), its fit in the case and the insertion force on its shell
  slots are not settled on paper; V-MECH-01 measures the built board.
- The MAU104 beside the reference (D39). The 6.0 mm rule is a planning distance from the OI-23
  study, not a noise calculation. At 6.15 mm from R11 the converter (about 100 kHz) is five times
  closer to V_INJ's parts than in Rev0.5, and nothing on paper says what it puts on the
  readings; V-MEAS-04 measures the built board.
- U1's west side is the densest spot. Its QSPI pins 51–56 reach U8 to the south-west, the
  decouplers of pins 43–45 and 48–50 stand in one column at x 36.2, and the USB pair leaves
  pins 46/47 west through R20/R22, then turns north and east past R23 and R21. P4 moved this
  block outward (*Deviations*) and drew the escapes the router left open
  (`ROUTING_Rev0.7.md`, *Hand-drawn tracks*).
