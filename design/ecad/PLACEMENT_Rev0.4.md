# USB Power-Control Hub — Rev0.4 placement

> **WIP — MANUFACTURING PROHIBITED.** Where every part of Rev0.4 sits on the
> 100 × 72 mm board (D24), and why. Issue #6 P3. No routing exists yet (P4); placement
> problems that routing finds are fixed here, in this file.

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
  and passives; pin 1 for the USB-C modules, the DIP16 ADCs, the MAU104, the axial shunt and
  the fuse.
- `Rot` is KiCad's orientation, counter-clockwise, 0/90/180/270.
- Every part is on the top side (F.Cu), none mirrored (REQ-MFG-01).
- In the channel table, channel B is channel A moved by `dx` in x: the same y, the same
  rotation. `{x}` in a region name is `A` or `B`.
- Three parts of each channel sheet are in the common table: R139/C114/C115 and R239/C214/C215,
  the over-current threshold filters at U30's inputs (Rev0.4 §3.4). U30 is shared, so the two
  sets sit beside it and cannot be 33.8 mm apart.
- A note's `at X pin N` (also `pins N/M`, `pad N`) means the part has a pad on that pin's net
  within 3.0 mm of it, centre to centre; `at X`, `next to X` and `after X` mean the two
  courtyards are within 3.0 mm. `toward X` gives a direction only. `check_pcb.py` measures
  every `at`, `next to` and `after` note, here and in the capture list, on the built board.

## Regions

The floorplan is the OI-23 study's (`design/experiments/oi-23-placement/`), changed where
the real footprints did not fit it; the changes are listed under *Deviations from the study*.
A `block` holds the parts that name it. A `module` is a USB-C module's outline
(library.json: `origin_in_module`, `size`); an `under` region lies inside one and holds only
parts low enough to sit below the module (*Parts under the modules*). A `mark` holds one
fiducial or one mounting hole. Regions do not overlap, except an `under` region inside its
module.

<!-- regions:begin -->
| Region | Kind | x | y | w | h | Holds | Why |
|---|---|---:|---:|---:|---:|---|---|
| MOD_A | module | 7.5 | 0.0 | 20.0 | 15.0 | J2 | OUT A at the front edge; J2–J3 pitch 33.8 mm ≥ 18 mm (REQ-MECH-02) |
| MOD_B | module | 41.3 | 0.0 | 20.0 | 15.0 | J3 | OUT B at the front edge |
| MOD_PWR | module | 7.5 | 57.0 | 20.0 | 15.0 | J4 | 5 V input at the back edge, above F1 |
| MOD_HOST | module | 66.0 | 57.0 | 20.0 | 15.0 | J1 | HOST at the back edge, next to the hub strip |
| UNDER_A | under | 7.5 | 7.93 | 20.0 | 3.92 | J2's port parts | CC ESD, Rp, port capacitor, discharge FET, at J2's pins |
| UNDER_B | under | 41.3 | 7.93 | 20.0 | 3.92 | J3's port parts | as UNDER_A |
| UNDER_PWR | under | 7.5 | 60.15 | 20.0 | 3.92 | D4, R3–R6 | J4's CC parts at its pins |
| UNDER_HOST | under | 66.0 | 60.15 | 20.0 | 3.92 | D1, R1, R2 | J1's CC parts at its pins |
| AFE_A | block | 0.5 | 19.0 | 33.1 | 30.5 | channel A front end | shunt ladder, current mirrors, comparators, port switch, hold and event FETs |
| AFE_B | block | 34.3 | 19.0 | 33.1 | 30.5 | channel B front end | AFE_A + 33.8 mm |
| ADC | block | 68.0 | 19.0 | 21.0 | 21.75 | U7, U17, C30, C31 | the two MCP3208 beside the front ends, inputs facing them |
| ADCSUP | block | 68.0 | 41.0 | 21.0 | 8.5 | level shifters, DOUT dividers, VDDA and V5A filters, U3 | the ADCs' support, between them and the MCU's SPI |
| HUB | block | 89.5 | 19.0 | 10.0 | 37.0 | U6, Y2, C27–C29, TP13 | right-edge strip: ports A/B leave south into the corridor, HOST north to J1 |
| PWR4 | block | 0.5 | 50.0 | 27.0 | 6.9 | F1, D6, C1, R7–R9, TP7–TP9 | J4's input: fuse, TVS after it (D25), bulk, the V_J4 divider |
| MCU | block | 28.0 | 50.0 | 23.0 | 21.5 | U1, U8, Y1, SW3, J5 and their passives | U1's channel GPIOs face the front ends (south) |
| LDO | block | 51.5 | 50.0 | 14.0 | 21.5 | U2, U30, TH_REF divider, the threshold filters | 3.3 V regulator and the over-current comparator between the channels |
| J1F | block | 66.0 | 50.0 | 23.0 | 6.0 | D5, Q53, R34, C35–C37, TP14 | J1's TVS and soft start (D35), at J1's VBUS pin |
| V12 | block | 72.4 | 7.7 | 20.1 | 7.3 | C5–C8, R10, TP3 | the MAU104's capacitors and the V12F filter |
| MAU | block | 72.4 | 0.5 | 20.1 | 6.7 | U5 | the MAU104 at the front right, ≥ 6 mm from the analog parts |
| REF | block | 35.5 | 0.5 | 5.3 | 14.5 | U4, R11–R13, TP4 | V_INJ reference, between the two front ends |
| UI_A | block | 28.0 | 0.5 | 7.0 | 14.5 | SW1, D10, D11, R140, R141 | OUT A's button and LEDs beside its port |
| UI_B | block | 61.8 | 0.5 | 7.0 | 14.5 | SW2, D12, D13, R240, R241 | UI_A + 33.8 mm |
| FID1 | mark | 1.0 | 8.5 | 3.0 | 3.0 | FID1 | global fiducial, front left |
| FID2 | mark | 96.0 | 8.5 | 3.0 | 3.0 | FID2 | global fiducial, front right |
| FID3 | mark | 1.0 | 61.0 | 3.0 | 3.0 | FID3 | global fiducial, back left |
| MH1 | mark | 0.0 | 0.0 | 7.0 | 7.0 | H1 | M2 clearance hole for the case's heat-set insert (D21), corner keepout |
| MH2 | mark | 93.0 | 0.0 | 7.0 | 7.0 | H2 | as MH1 |
| MH3 | mark | 0.0 | 65.0 | 7.0 | 7.0 | H3 | as MH1 |
| MH4 | mark | 93.0 | 65.0 | 7.0 | 7.0 | H4 | as MH1 |
<!-- regions:end -->

## Keepouts

No part's courtyard may enter these. Tracks may.

<!-- keepouts:begin -->
| Keepout | x | y | w | h | Why |
|---|---:|---:|---:|---:|---|
| USB_CORRIDOR | 18.0 | 15.5 | 71.3 | 3.0 | the HS pairs from U6 to J2 and J3 (the study's corridor) |
| USB_UP_LANE | 70.0 | 56.0 | 29.5 | 1.0 | the HS pair from J1 down the right edge to U6 |
<!-- keepouts:end -->

## Parts under the modules

A module stands on its PH-1x40SG headers, whose insulator is ≥ 2.30 mm (D33). A part whose
courtyard enters a module's outline must be on this list, no taller than 1.5 mm
(`UNDER_MAX_H`), which leaves the 0.5 mm `UNDER_CLEAR` of the study. Heights are the study's
planning values (`placement_study.py`, `COURTYARD`), not measured.

<!-- under:begin -->
| Footprint | Height (mm) | Source |
|---|---:|---|
| R_0402_1005Metric | 0.55 | study COURTYARD "0402" |
| C_0402_1005Metric | 0.55 | study COURTYARD "0402" |
| C_0805_2012Metric | 1.45 | study COURTYARD "0805" (22 uF is 1.25 + 0.2) |
| SOT-23 | 1.12 | study COURTYARD "SOT-23" |
<!-- under:end -->

The free band under a module is the space between its courtyard rectangles: from the header
insulator (local y −1.25) to the receptacle's shell tabs (−5.17), 3.92 mm. D33's study drew
a 3.4 mm strip with a further 0.25 mm on each side; an SOT-23's courtyard (3.49 mm) does not
fit that strip and fits the band. Each courtyard already carries its part's margin, and DRC
checks them against each other.

## Common parts

<!-- place:begin -->
| Ref | x | y | Rot | Region | Note |
|---|---:|---:|---:|---|---|
| C1 | 13.25 | 55.8 | 180 | PWR4 | VBUS_IN, next to R7 |
| C2 | 52.9 | 62.65 | 90 | LDO | at U2 pin 3 |
| C3 | 52.9 | 66.25 | 90 | LDO | at U2 pin 2 |
| C4 | 34.6 | 62.6 | 90 | MCU | V3V3 bulk, next to U1 beside the decoupler column |
| C5 | 74.85 | 8.7 | 90 | V12 | at U5 pin 1 |
| C6 | 87.55 | 8.7 | 90 | V12 | at U5 pin 6 |
| C7 | 86.45 | 11.6 | 90 | V12 | at R10 pin 2 |
| C8 | 83.55 | 9.6 | 180 | V12 | at R10 pin 2 |
| C9 | 83.4 | 47.05 | 90 | ADCSUP | VDDA, next to TP6 |
| C10 | 86.3 | 47.15 | 0 | ADCSUP | V5A, next to TP2 |
| C11 | 56.6 | 56.8 | 90 | LDO | TH_REF, next to R139 |
| C12 | 39.25 | 53.4 | 180 | MCU | at U1 pin 1, clear of its pin-1 mark |
| C13 | 42.85 | 53.6 | 180 | MCU | at U1 pin 10 |
| C14 | 47 | 60.2 | 90 | MCU | at U1 pin 22 |
| C15 | 43.2 | 63.18 | 0 | MCU | at U1 pin 33 (IOVDD) |
| C16 | 39.6 | 63.18 | 0 | MCU | at U1 pin 42 (IOVDD) |
| C17 | 36.75 | 57.74 | 180 | MCU | at U1 pin 49 (IOVDD) |
| C18 | 36.75 | 58.85 | 180 | MCU | at U1 pin 48 (USB_VDD), below the USB pins |
| C19 | 36.75 | 62.57 | 180 | MCU | at U1 pin 43 (ADC_AVDD) |
| C20 | 36.75 | 61.46 | 180 | MCU | at U1 pin 44 (VREG_VIN) |
| C21 | 36.75 | 60.35 | 180 | MCU | at U1 pin 45 (VREG_VOUT) |
| C22 | 48.15 | 60.25 | 90 | MCU | at U1 pin 23 |
| C23 | 36.75 | 56.63 | 180 | MCU | at U1 pin 50 (DVDD) |
| C24 | 34.6 | 56.62 | 180 | MCU | at U8 pin 8 |
| C25 | 49.65 | 54.2 | 0 | MCU | at Y1 pin 1 |
| C26 | 49.75 | 59.85 | 0 | MCU | at Y1 pin 3 |
| C27 | 93.1 | 30.25 | 180 | HUB | at U6 pin 26 |
| C28 | 91.05 | 30.25 | 180 | HUB | at U6 pin 28 |
| C29 | 92.3 | 32.6 | 90 | HUB | at U6 pin 28 |
| C30 | 70.1 | 29.5 | 0 | ADC | at U7 pin 16 |
| C31 | 72.65 | 29.5 | 0 | ADC | at U7 pin 15 |
| C32 | 69.55 | 42 | 90 | ADCSUP | at U17 pin 16 |
| C33 | 72.1 | 42 | 90 | ADCSUP | at U17 pin 15 |
| C34 | 57.95 | 56.8 | 90 | LDO | at U30 pin 8 |
| C35 | 78.4 | 51.9 | 180 | J1F | GJ1, next to C37 |
| C36 | 77.9 | 53.7 | 90 | J1F | GJ1, next to R34 |
| C37 | 79.05 | 53.55 | 90 | J1F | GJ1, next to C36 |
| C114 | 52.2 | 56.8 | 90 | LDO | THO_A, next to R139 |
| C115 | 55.45 | 56.85 | 270 | LDO | THO_A, next to R139 |
| C214 | 61.5 | 51.1 | 0 | LDO | THO_B, next to R239 |
| C215 | 59.85 | 54.05 | 270 | LDO | EN_G_B, next to U30 |
| D1 | 79.8 | 62.11 | 0 | UNDER_HOST | CC ESD, at J1 on its CC pins |
| D4 | 21.3 | 62.11 | 0 | UNDER_PWR | CC ESD, at J4 on its CC pins |
| D5 | 70 | 53.2 | 0 | J1F | VBUS_J1 TVS at J1 |
| D6 | 18.8 | 53.3 | 0 | PWR4 | VBUS_IN TVS after F1 (D25) |
| F1 | 5 | 52.55 | 0 | PWR4 | J4's fuse, pad 1 toward J4 pin 1 |
| FB1 | 82.3 | 44.4 | 180 | ADCSUP | V3V3, next to R14 |
| FID1 | 2.5 | 10 | 0 | FID1 | global fiducial |
| FID2 | 97.5 | 10 | 0 | FID2 | global fiducial |
| FID3 | 2.5 | 62.5 | 0 | FID3 | global fiducial |
| H1 | 3.5 | 3.5 | 0 | MH1 | M2 clearance hole, front left; the screw goes into the case's heat-set insert (D21) |
| H2 | 96.5 | 3.5 | 0 | MH2 | M2 clearance hole, front right; the screw goes into the case's heat-set insert (D21) |
| H3 | 3.5 | 68.5 | 0 | MH3 | M2 clearance hole, back left; the screw goes into the case's heat-set insert (D21) |
| H4 | 96.5 | 68.5 | 0 | MH4 | M2 clearance hole, back right; the screw goes into the case's heat-set insert (D21) |
| J1 | 68.38 | 58.9 | 0 | MOD_HOST | HOST; receptacle past the back edge |
| J4 | 9.88 | 58.9 | 0 | MOD_PWR | 5 V input; receptacle past the back edge |
| J5 | 44.5 | 69.2 | 0 | MCU | SWD (TC2030-NL), north of U1 |
| Q50 | 72.05 | 44.8 | 0 | ADCSUP | ADC_SCLK, next to R27 |
| Q51 | 76.4 | 42.75 | 0 | ADCSUP | ADC_CS, next to R28 |
| Q52 | 76.15 | 46.4 | 0 | ADCSUP | ADC_DIN, next to R29 |
| Q53 | 75.55 | 53 | 270 | J1F | GJ1, next to C36 |
| R1 | 77.15 | 61.3 | 90 | UNDER_HOST | at J1 pin 5 |
| R2 | 82.85 | 60.85 | 0 | UNDER_HOST | at J1 pin 6 |
| R3 | 18.65 | 61.3 | 90 | UNDER_PWR | at J4 pin 5 |
| R4 | 23.95 | 61.35 | 90 | UNDER_PWR | at J4 pin 6 |
| R5 | 17.5 | 61.35 | 90 | UNDER_PWR | CC1_J4, next to R3 |
| R6 | 25.6 | 60.85 | 0 | UNDER_PWR | CC2_J4, next to R4 |
| R7 | 16.15 | 56.25 | 0 | PWR4 | V_J4, next to R8 |
| R8 | 18.25 | 56.25 | 0 | PWR4 | V_J4, next to R7 |
| R9 | 25.95 | 51.7 | 0 | PWR4 | V_J4, next to TP9 |
| R10 | 86.4 | 8.7 | 90 | V12 | at U5 pin 6 |
| R11 | 39.35 | 10.85 | 180 | REF | V_INJ, next to R12 |
| R12 | 37.75 | 10.4 | 90 | REF | INJ_REF, next to R13 |
| R13 | 36.6 | 10.15 | 270 | REF | INJ_REF, next to R12 |
| R14 | 81.35 | 42.5 | 180 | ADCSUP | VREF_CHK, next to R15 |
| R15 | 79 | 42.15 | 270 | ADCSUP | VREF_CHK, next to R14 |
| R16 | 72.35 | 47.65 | 270 | ADCSUP | V5L, next to R27 |
| R17 | 61.5 | 52.25 | 180 | LDO | TH_REF, next to R239 |
| R18 | 61.05 | 53.9 | 90 | LDO | TH_REF, next to R17 |
| R19 | 63.45 | 54.4 | 0 | LDO | TH_LO, next to R18 |
| R20 | 34.7 | 59 | 180 | MCU | USB D+ 22 ohm, next to U1: the pair leaves pins 46/47 west |
| R21 | 41.7 | 65.6 | 0 | MCU | USB D+ 5.1 ohm, next to U1 |
| R22 | 34.7 | 60.13 | 180 | MCU | USB D- 22 ohm, next to U1 |
| R23 | 38.5 | 64.56 | 0 | MCU | USB D- 5.1 ohm, next to U1, where the pair turns east |
| R24 | 47.5 | 61.85 | 0 | MCU | XTAL1_OUT, next to C26 |
| R25 | 29.5 | 57.1 | 90 | MCU | BOOTSEL, next to U8 at its pin 1 |
| R26 | 45.35 | 63.2 | 0 | MCU | RUN, next to TP11 |
| R27 | 73.55 | 47.65 | 270 | ADCSUP | V5L, next to R16 |
| R28 | 79 | 44.5 | 270 | ADCSUP | V5L, next to R29 |
| R29 | 80.15 | 44.6 | 90 | ADCSUP | V5L, next to R28 |
| R30 | 69 | 43.6 | 180 | ADCSUP | DOUT_A_3V, next to R31 |
| R31 | 68.6 | 46.85 | 90 | ADCSUP | DOUT_A_3V, next to R30 |
| R32 | 69 | 48.5 | 180 | ADCSUP | DOUT_B_3V, next to R33 |
| R33 | 70.2 | 47.35 | 0 | ADCSUP | DOUT_B_3V, next to R32 |
| R34 | 78.45 | 55.3 | 0 | J1F | GJ1, next to C36 |
| R139 | 53.85 | 56.4 | 180 | LDO | THO_A, next to C114 |
| R239 | 59.9 | 51.9 | 270 | LDO | at U30 pin 5 |
| SW3 | 31.85 | 68.6 | 0 | MCU | BOOTSEL button, under the lid pinhole |
| TP1 | 64.45 | 52.05 | 0 | LDO | V5L, toward R16 pin 1 |
| TP2 | 87.25 | 44.95 | 0 | ADCSUP | V5A, next to C10 |
| TP3 | 88.65 | 10.9 | 0 | V12 | at R10 pin 2 |
| TP4 | 38.3 | 8.25 | 0 | REF | V_INJ, next to R12 |
| TP5 | 54.5 | 59.2 | 0 | LDO | V3V3, next to U2 |
| TP6 | 85 | 44.15 | 0 | ADCSUP | VDDA, next to C9 |
| TP7 | 8.05 | 55.8 | 0 | PWR4 |  |
| TP8 | 10.3 | 55.8 | 0 | PWR4 | VBUS_IN, next to F1 |
| TP9 | 23.8 | 51.85 | 0 | PWR4 | V_J4, next to R9 |
| TP10 | 48 | 63.55 | 0 | MCU | DVDD, next to C22 |
| TP11 | 45.75 | 64.9 | 0 | MCU | RUN, next to R26 |
| TP12 | 48 | 65.75 | 0 | MCU | CLKOUT, next to U1 |
| TP13 | 95.25 | 30.8 | 0 | HUB | VDD33_HUB, next to U6 |
| TP14 | 80.75 | 53.15 | 0 | J1F | VBUS_J1, next to C37 |
| U1 | 42.2 | 58.4 | 90 | MCU | rot 90: channel GPIOs south, SPI and crystal east, USB and QSPI west |
| U2 | 58.5 | 64 | 0 | LDO | AMS1117 |
| U3 | 80.25 | 47.45 | 0 | ADCSUP | VREF_CHK, next to R15 |
| U4 | 37.8 | 13.25 | 180 | REF | INJ_REF, next to R12 |
| U5 | 74.8 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |
| U6 | 94 | 27 | 0 | HUB | ports A/B south to the corridor, HOST east, MCU port west |
| U7 | 69.6 | 20.15 | 90 | ADC | inputs 1-3 on the south-west row, facing the front ends |
| U8 | 33 | 53.05 | 0 | MCU | QSPI flash south-west of U1, pins 5-8 toward U1 pins 51-56 |
| U17 | 69.6 | 32 | 90 | ADC | as U7, above it |
| U30 | 55.5 | 53 | 0 | LDO | over-current comparator, both channels |
| Y1 | 48.3 | 57 | 90 | MCU | next to U1 at its pins 20/21 |
| Y2 | 94 | 22.3 | 0 | HUB | next to U6 at its pins 11/12 |
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
| C116 | C216 | 25.6 | 9.9 | 180 | UNDER_{x} | port capacitor, at J2 on its VBUS pin |
| D2 | D3 | 13.7 | 9.89 | 0 | UNDER_{x} | CC ESD, at J2 on its CC pins |
| D10 | D12 | 29.75 | 10.5 | 0 | UI_{x} | OUT A ON LED |
| D11 | D13 | 29.75 | 13 | 0 | UI_{x} | OUT A FAULT LED |
| J2 | J3 | 25.12 | 13.1 | 180 | MOD_{x} | OUT A; receptacle 1.06 mm past the front edge |
| Q10 | Q30 | 2.5 | 47.5 | 0 | AFE_{x} | SRC_A, next to R101 |
| Q11 | Q31 | 2.25 | 40.55 | 270 | AFE_{x} | GSW_A, next to R101 |
| Q12 | Q32 | 16 | 42.25 | 180 | AFE_{x} | EN_G_A, next to R106 |
| Q13 | Q33 | 20.6 | 9.89 | 0 | UNDER_{x} | discharge FET |
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
| R103 | R203 | 9.6 | 9.9 | 90 | UNDER_{x} | Rp CC1 |
| R104 | R204 | 10.9 | 9.9 | 90 | UNDER_{x} | Rp CC2 |
| R105 | R205 | 10 | 48 | 270 | AFE_{x} | EN_G_A, toward R107 pin 1 |
| R106 | R206 | 16.35 | 44.65 | 180 | AFE_{x} | EN_G_A, next to R107 |
| R107 | R207 | 16.3 | 46.25 | 90 | AFE_{x} | EN_G_A, next to R106 |
| R108 | R208 | 17.45 | 46.85 | 270 | AFE_{x} | V3V3, toward R116 pin 1 |
| R109 | R209 | 17.9 | 9.9 | 270 | UNDER_{x} | Q13 gate resistor |
| R110 | R210 | 23.2 | 9.9 | 90 | UNDER_{x} | discharge resistor, at J2 on its VBUS pin |
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
| R140 | R240 | 33.25 | 10.5 | 180 | UI_{x} | D10 series |
| R141 | R241 | 33.25 | 13 | 180 | UI_{x} | D11 series |
| RS10 | RS20 | 4.595 | 21 | 0 | AFE_{x} | R_H: VSUP enters at pad 1 (west); sense pads north |
| RS11 | RS21 | 9.785 | 21 | 0 | AFE_{x} | R_M after R_H; sense pads north |
| RS12 | RS22 | 22.81 | 20.5 | 0 | AFE_{x} | R_L after R_M; pad 4 above J2 pin 1 |
| SW1 | SW2 | 31.5 | 4.5 | 90 | UI_{x} | OUT A button |
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

## Deviations from the study

| Study | Here | Why |
|---|---|---|
| R_AFEA / R_AFEB 27 × 31 mm | AFE_A / AFE_B 33.1 × 30.5 mm | the library's courtyards are larger than the study's planning ones (an SOT-23 is 13.8 mm², not 10.3); at 27 mm the channel filled 72 % before routing |
| J2 / J3 at x 18 / 46 | x 7.5 / 41.3 (pitch 33.8 mm) | each module sits under its own front end, so the pitch equals the front ends' |
| U7 / U17 at x 55.5 / 65.8, upright | stacked at x 68, rotated 90° | the wider front ends took that space; turned, each ADC's inputs face the front ends |
| MAU104 at (82, 30), turned | front right, (72.45, 0.55)–(92.45, 7.15) | the ADCs took its region; it stays ≥ 6 mm from every analog region |
| R_MCUF (SW3, J5, test pads) at the front | in MCU, beside U1 | REQ-BOOT-02 needs only a lid pinhole, and the lid is a PCB with its own drill; SWD stays at U1 |
| U30 with R_LDO's OC block | in LDO, with both channels' threshold filters | as the study; the filters are not in the channel template (see the format notes) |
| 3.4 mm strip under each module | 3.92 mm band | see *Parts under the modules* |

## Not settled here

- Routing (P4) can move any part; this file then changes, not the board.
- The silkscreen labels of CLAUDE.md §6 (product name, revision, Pin 1, port labels, test-pad
  names) come with routing.
- The heights under the modules are planning values; V-MECH-01 measures the built board.
- U1's west side is the densest spot. Its QSPI pins 51–56 reach U8 to the south-west, the
  decouplers of pins 43–45 and 48–50 stand in one column at x 36.75, and the USB pair leaves
  pins 46/47 west through R20/R22, then turns north and east past R23 and R21. P4 decides
  which of these escapes take a via; if they do not route, this block moves.
