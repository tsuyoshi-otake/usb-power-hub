# USB Power-Control Hub — Rev0.4 netlist

> **WIP — MANUFACTURING PROHIBITED.** This is the capture list of
> [`CIRCUIT_DESIGN_Rev0.4.md`](CIRCUIT_DESIGN_Rev0.4.md): every part, every pin and every net
> of Rev0.4 §3–§6.6 with the capture values of D34. The circuit document stays the design;
> this file is its transcription in a form a script can read. Issue #6 P2.

`design/ecad/scripts/make_schematic.py` generates the KiCad schematic from the tables below,
and `design/ecad/scripts/check_schematic.py` compares the netlist that KiCad exports from that
schematic with these tables (`design/ecad/README.md`). Change the circuit here and in the
circuit document together.

## Format

- One row per part. `Pins` lists **every pin of the symbol**, as `number=NET`, separated by
  spaces. `NC` means a no-connect flag; no net is named `NC`.
- `Symbol` is the part id in `design/ecad/libraries/library.json`, which is also the symbol
  name in the project library. The footprint is the symbol's, except for `R` and `C`, whose
  footprint, value, MPN and LCSC number come from the passive table through `Order`.
- `Value` is the register's Value (its `value`, else its id), except for `R` and `C`, whose
  Value is the passive table's, and test pads, whose Value is their net's name.
- `Order` is the JLCPCB code, `Akizuki <code>`, or `none` for a part that is not bought
  (test pads, J5's TC2030-NL footprint). A part with `none`, or whose register sets
  `in_bom: false`, is excluded from the BOM. A hand-soldered Akizuki part stays in KiCad's
  BOM, which is the purchase list, with an `Akizuki` field and no `LCSC` field; the JLCPCB
  BOM and CPL (P5) take only the rows with an `LCSC` field (V-MFG-01).
- In the channel table, `{x}` in a net name is `A` in the row's channel-A part and `B` in its
  channel-B part. A net without `{x}` is shared by both channels.
- Pins that share one position in the symbol (U1's IOVDD and DVDD, the crystals' two G pins)
  are listed one by one, all on the same net.
- Passive numbers: the common block uses R1…, C1…, TP1…; channel A uses R101…, C101…,
  TP101…, and channel B the same + 100. Other channel-B designators follow Rev0.4 §6.2: U and
  RS + 10, Q + 20; D10/D11 → D12/D13, J2 → J3, SW1 → SW2.

## GPIO map (U1, 24 of 30; Rev0.4 §6.4)

| GPIO | Pin | Net | GPIO | Pin | Net |
|---|---:|---|---|---:|---|
| 0 | 2 | EN_A | 12 | 15 | ADC_SCLK_3V |
| 1 | 3 | OC_A | 13 | 16 | ADC_CS_3V |
| 2 | 4 | HOLD_L_A | 14 | 17 | ADC_DIN_3V |
| 3 | 5 | HOLD_M_A | 15 | 18 | DOUT_A_3V |
| 4 | 6 | EVT_L_A | 16 | 27 | DOUT_B_3V |
| 5 | 7 | EVT_M_A | 17 | 28 | LED_ON_A |
| 6 | 8 | EN_B | 18 | 29 | LED_FLT_A |
| 7 | 9 | OC_B | 19 | 30 | LED_ON_B |
| 8 | 11 | HOLD_L_B | 20 | 31 | LED_FLT_B |
| 9 | 12 | HOLD_M_B | 21 | 32 | CLKOUT (GPOUT0, test pad) |
| 10 | 13 | EVT_L_B | 22 | 34 | BTN_A |
| 11 | 14 | EVT_M_B | 23 | 35 | BTN_B |

GPIO24–29 (pins 36–41) are spare and unconnected. The PIO drives SCLK, CS and DIN on
GPIO12–14 and reads DOUT_A and DOUT_B on GPIO15–16, so each group is contiguous.

## Passive parts (D13 Basic; D34 bindings)

The MPN is decoded with the manufacturer's part-number rules, which win over the LCSC listing
parameters. Body length × width is the manufacturer's dimension table (UNI-ROYAL thick-film
sheet §5; Samsung MLCC "Standard & High Capacitors" table; FH MLCC "Product Dimensions",
widest thickness code).

<!-- passives:begin -->
| Order | Kind | Value | MPN | Manufacturer | Package | Footprint | Rating | Body L × W (mm) |
|---|---|---|---|---|---|---|---|---|
| C25076 | R | 100 | 0402WGF1000TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25867 | R | 1.5k | 0402WGF1501TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C22940 | R | 2.4k | 0603WAF2401T5E | UNI-ROYAL | 0603 | R_0603_1608Metric | ±1 %, ±100 ppm/°C, 1/10 W | 1.60±0.10 × 0.80±0.10 |
| C25092 | R | 22 | 0402WGF220JTCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25197 | R | 5.1 | 0603WAF510KT5E | UNI-ROYAL | 0603 | R_0603_1608Metric | ±1 %, ±200 ppm/°C, 1/10 W | 1.60±0.10 × 0.80±0.10 |
| C25744 | R | 10k | 0402WGF1002TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25756 | R | 15k | 0402WGF1502TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25779 | R | 33k | 0402WGF3302TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25905 | R | 5.1k | 0402WGF5101TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25741 | R | 100k | 0402WGF1003TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C26083 | R | 1M | 0402WGF1004TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C11702 | R | 1k | 0402WGF1001TCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±100 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C25077 | R | 10 | 0402WGF100JTCE | UNI-ROYAL | 0402 | R_0402_1005Metric | ±1 %, ±200 ppm/°C, 1/16 W | 1.00±0.10 × 0.50±0.05 |
| C17734 | R | 510 | 0805W8F5100T5E | UNI-ROYAL | 0805 | R_0805_2012Metric | ±1 %, ±100 ppm/°C, 1/8 W | 2.00±0.15 × 1.25+0.15/−0.10 |
| C15850 | C | 10u | CL21A106KAYNNNE | Samsung | 0805 | C_0805_2012Metric | X5R, ±10 %, 25 V | 2.00±0.15 × 1.25±0.15 |
| C45783 | C | 22u | CL21A226MAQNNNE | Samsung | 0805 | C_0805_2012Metric | X5R, ±20 %, 25 V | 2.00±0.15 × 1.25±0.15 |
| C307331 | C | 100n | CL05B104KB54PNC | Samsung | 0402 | C_0402_1005Metric | X7R, ±10 %, 50 V | 1.00±0.05 × 0.50±0.05 |
| C52923 | C | 1u | CL05A105KA5NQNC | Samsung | 0402 | C_0402_1005Metric | X5R, ±10 %, 25 V | 1.00±0.05 × 0.50±0.05 |
| C15195 | C | 10n | CL05B103KB5NNNC | Samsung | 0402 | C_0402_1005Metric | X7R, ±10 %, 50 V | 1.00±0.05 × 0.50±0.05 |
| C1664 | C | 330p | CL10C331JB8NNNC | Samsung | 0603 | C_0603_1608Metric | C0G, ±5 %, 50 V | 1.60±0.10 × 0.80±0.10 |
| C1548 | C | 15p | 0402CG150J500NT | FH | 0402 | C_0402_1005Metric | C0G, ±5 %, 50 V | 1.00±0.20 × 0.50±0.20 |
| C1530 | C | 220p | 0402B221K500NT | FH | 0402 | C_0402_1005Metric | X7R, ±10 %, 50 V | 1.00±0.20 × 0.50±0.20 |
<!-- passives:end -->

## Common block

### Sheet `power` — J1, J4, the rails, V_INJ, VREF_CHK, the comparator threshold

<!-- netlist:begin sheet=power -->
| Ref | Symbol | Value | Order | Pins | Note |
|---|---|---|---|---|---|
| J1 | AE-USB2.0-TYPE-C | AE-USB2.0-TYPE-C | Akizuki g113080 | 1=V5L 2=USB_UP_N 3=USB_UP_P 4=GND 5=CC1_J1 6=CC2_J1 7=GND | HOST: data and logic power |
| R1 | R | 5.1k | C25905 | 1=CC1_J1 2=GND | J1 Rd |
| R2 | R | 5.1k | C25905 | 1=CC2_J1 2=GND | J1 Rd |
| D1 | PSM712-LF-T7 | PSM712-LF-T7 | C32677 | 1=CC1_J1 2=CC2_J1 3=GND | J1 CC ESD, at J1 |
| D5 | SMBJ6.5CA | SMBJ6.5CA | C7420377 | 1=V5L 2=GND | J1 VBUS TVS, at J1 |
| J4 | AE-USB2.0-TYPE-C | AE-USB2.0-TYPE-C | Akizuki g113080 | 1=VBUS_J4 2=NC 3=NC 4=GND 5=CC1_J4 6=CC2_J4 7=GND | PWR IN: power only |
| R3 | R | 5.1k | C25905 | 1=CC1_J4 2=GND | J4 Rd |
| R4 | R | 5.1k | C25905 | 1=CC2_J4 2=GND | J4 Rd |
| D4 | PSM712-LF-T7 | PSM712-LF-T7 | C32677 | 1=CC1_J4 2=CC2_J4 3=GND | J4 CC ESD, at J4 |
| R5 | R | 1k | C11702 | 1=CC1_J4 2=ADC_CC1 | to U17 CH3 |
| R6 | R | 1k | C11702 | 1=CC2_J4 2=ADC_CC2 | to U17 CH4 |
| F1 | MF-R300 | MF-R300 | Akizuki g112630 | 1=VBUS_J4 2=VBUS_IN | J4 input fuse, ahead of D6 (D25) |
| D6 | SMBJ6.5CA | SMBJ6.5CA | C7420377 | 1=VBUS_IN 2=GND | J4 VBUS TVS, after F1 |
| C1 | C | 22u | C45783 | 1=VBUS_IN 2=GND | VBUS_IN bulk |
| R7 | R | 33k | C25779 | 1=VBUS_IN 2=V_J4 | V_J4 divider top |
| R8 | R | 15k | C25756 | 1=V_J4 2=GND | V_J4 divider bottom |
| R9 | R | 1k | C11702 | 1=V_J4 2=ADC_VJ4 | to U7 CH4 |
| U2 | AMS1117-3.3 | AMS1117-3.3 | C6186 | 1=GND 2=V3V3 3=V5L | 3.3 V LDO |
| C2 | C | 10u | C15850 | 1=V5L 2=GND | U2 input |
| C3 | C | 22u | C45783 | 1=V3V3 2=GND | U2 output |
| U5 | MAU104 | MAU104 | Akizuki g104132 | 1=V5L 2=GND 4=GND 6=V12 | isolated 12 V, -Vout tied to GND |
| C5 | C | 1u | C52923 | 1=V5L 2=GND | U5 input, at U5 (D34) |
| C6 | C | 1u | C52923 | 1=V12 2=GND | U5 output, at U5 (D34) |
| R10 | R | 10 | C25077 | 1=V12 2=V12F | V12 filter |
| C7 | C | 22u | C45783 | 1=V12F 2=GND | V12 filter |
| C8 | C | 22u | C45783 | 1=V12F 2=GND | V12 filter |
| R11 | R | 1.5k | C25867 | 1=V12F 2=V_INJ | U4 feed |
| U4 | CJ431 | CJ431 | C3113 | 1=INJ_REF 2=V_INJ 3=GND | V_INJ 8 V shunt regulator, no capacitor (D34) |
| R12 | R | 33k | C25779 | 1=V_INJ 2=INJ_REF | U4 divider top |
| R13 | R | 15k | C25756 | 1=INJ_REF 2=GND | U4 divider bottom |
| R14 | R | 510 | C17734 | 1=V3V3 2=VREF_CHK | U3 feed |
| U3 | CJ431 | CJ431 | C3113 | 1=VREF_CHK 2=VREF_CHK 3=GND | VREF_CHK 2.5 V, no capacitor (D34) |
| R15 | R | 1k | C11702 | 1=VREF_CHK 2=ADC_VREF_CHK | to U7 CH3 |
| FB1 | BLM18PG121SN1D | BLM18PG121SN1D | C14709 | 1=V3V3 2=VDDA | VDDA ferrite |
| C9 | C | 10u | C15850 | 1=VDDA 2=GND | VDDA |
| R16 | R | 10 | C25077 | 1=V5L 2=V5A | V5A filter |
| C10 | C | 10u | C15850 | 1=V5A 2=GND | V5A filter |
| R17 | R | 1k | C11702 | 1=VDDA 2=TH_REF | TH_REF divider top (D34) |
| R18 | R | 5.1k | C25905 | 1=TH_REF 2=TH_LO | TH_REF divider bottom, part 1 (D34) |
| R19 | R | 510 | C17734 | 1=TH_LO 2=GND | TH_REF divider bottom, part 2 (D34) |
| C11 | C | 1u | C52923 | 1=TH_REF 2=GND | TH_REF filter (D34) |
| TP1 | TestPoint | V5L | none | 1=V5L | P11 |
| TP2 | TestPoint | V5A | none | 1=V5A | P11 |
| TP3 | TestPoint | V12F | none | 1=V12F | P11 |
| TP4 | TestPoint | V_INJ | none | 1=V_INJ | P11 |
| TP5 | TestPoint | V3V3 | none | 1=V3V3 | P11 |
| TP6 | TestPoint | VDDA | none | 1=VDDA | P11 |
| TP7 | TestPoint | GND | none | 1=GND | P11 |
| TP8 | TestPoint | VBUS_IN | none | 1=VBUS_IN | P11 |
| TP9 | TestPoint | V_J4 | none | 1=V_J4 | Rev0.4 §12 item 5 (V-MEAS-06) |
| FID1 | Fiducial | Fiducial | none | — | ≥ 3 global fiducials |
| FID2 | Fiducial | Fiducial | none | — | |
| FID3 | Fiducial | Fiducial | none | — | |
| H1 | MountingHole | MountingHole | none | — | heat-set M2 insert (D21) |
| H2 | MountingHole | MountingHole | none | — | |
| H3 | MountingHole | MountingHole | none | — | |
| H4 | MountingHole | MountingHole | none | — | |
<!-- netlist:end -->

### Sheet `mcu` — U1 RP2040, U8 flash, Y1, SWD (Rev0.4 §6.5)

<!-- netlist:begin sheet=mcu -->
| Ref | Symbol | Value | Order | Pins | Note |
|---|---|---|---|---|---|
| U1 | RP2040 | RP2040 | C2040 | 1=V3V3 2=EN_A 3=OC_A 4=HOLD_L_A 5=HOLD_M_A 6=EVT_L_A 7=EVT_M_A 8=EN_B 9=OC_B 10=V3V3 11=HOLD_L_B 12=HOLD_M_B 13=EVT_L_B 14=EVT_M_B 15=ADC_SCLK_3V 16=ADC_CS_3V 17=ADC_DIN_3V 18=DOUT_A_3V 19=GND 20=XIN 21=XOUT 22=V3V3 23=DVDD 24=SWCLK 25=SWDIO 26=RUN 27=DOUT_B_3V 28=LED_ON_A 29=LED_FLT_A 30=LED_ON_B 31=LED_FLT_B 32=CLKOUT 33=V3V3 34=BTN_A 35=BTN_B 36=NC 37=NC 38=NC 39=NC 40=NC 41=NC 42=V3V3 43=V3V3 44=V3V3 45=DVDD 46=USB_MCU_N 47=USB_MCU_P 48=V3V3 49=V3V3 50=DVDD 51=QSPI_SD3 52=QSPI_SCLK 53=QSPI_SD0 54=QSPI_SD2 55=QSPI_SD1 56=QSPI_SS 57=GND | MCU (D29); TESTEN (19) to GND |
| C4 | C | 10u | C15850 | 1=V3V3 2=GND | V3V3 at U1 (reference C17) |
| C12 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 1 (IOVDD) |
| C13 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 10 (IOVDD) |
| C14 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 22 (IOVDD) |
| C15 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 33 (IOVDD) |
| C16 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 42 (IOVDD) |
| C17 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 49 (IOVDD) |
| C18 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 48 (USB_VDD) |
| C19 | C | 100n | C307331 | 1=V3V3 2=GND | at U1 pin 43 (ADC_AVDD) |
| C20 | C | 1u | C52923 | 1=V3V3 2=GND | at U1 pin 44 (VREG_VIN) |
| C21 | C | 1u | C52923 | 1=DVDD 2=GND | at U1 pin 45 (VREG_VOUT) |
| C22 | C | 100n | C307331 | 1=DVDD 2=GND | at U1 pin 23 (DVDD) |
| C23 | C | 100n | C307331 | 1=DVDD 2=GND | at U1 pin 50 (DVDD) |
| R20 | R | 22 | C25092 | 1=USB_MCU_P 2=USB_P1M_P | 27 ohm part 1, next to U1 |
| R21 | R | 5.1 | C25197 | 1=USB_P1M_P 2=USB_P1_P | 27 ohm part 2, next to U1 |
| R22 | R | 22 | C25092 | 1=USB_MCU_N 2=USB_P1M_N | 27 ohm part 1, next to U1 |
| R23 | R | 5.1 | C25197 | 1=USB_P1M_N 2=USB_P1_N | 27 ohm part 2, next to U1 |
| Y1 | X322512MSB4SI | X322512MSB4SI | C9002 | 1=XIN 2=GND 3=XTAL1_OUT 4=GND | U1 crystal |
| R24 | R | 1k | C11702 | 1=XOUT 2=XTAL1_OUT | in XOUT |
| C25 | C | 15p | C1548 | 1=XIN 2=GND | Y1 load |
| C26 | C | 15p | C1548 | 1=XTAL1_OUT 2=GND | Y1 load |
| U8 | W25Q128JVSIQ | W25Q128JVSIQ | C97521 | 1=QSPI_SS 2=QSPI_SD1 3=QSPI_SD2 4=GND 5=QSPI_SD0 6=QSPI_SCLK 7=QSPI_SD3 8=V3V3 | QSPI flash; unique ID = USB serial |
| C24 | C | 100n | C307331 | 1=V3V3 2=GND | at U8 pin 8 |
| R25 | R | 1k | C11702 | 1=QSPI_SS 2=BOOT_SW | BOOTSEL, next to U8 |
| SW3 | TS-1187A-B-A-B | TS-1187A-B-A-B | C318884 | 1=BOOT_SW 2=GND | behind the lid pinhole |
| R26 | R | 10k | C25744 | 1=V3V3 2=RUN | RUN pull-up |
| J5 | TC2030-NL | TC2030-NL (DNL) | none | 1=V3V3 2=SWDIO 3=RUN 4=SWCLK 5=GND 6=NC | SWD, footprint only (debug) |
| TP10 | TestPoint | DVDD | none | 1=DVDD | D29 |
| TP11 | TestPoint | RUN | none | 1=RUN | D29 |
| TP12 | TestPoint | CLKOUT | none | 1=CLKOUT | D29, GPOUT0 (V-MEAS-06) |
<!-- netlist:end -->

### Sheet `hub` — U6 CH335F, Y2 (Rev0.4 §6.6)

<!-- netlist:begin sheet=hub -->
| Ref | Symbol | Value | Order | Pins | Note |
|---|---|---|---|---|---|
| U6 | CH335F | CH335F | C5137013 | 0=GND 1=NC 2=NC 3=NC 4=NC 5=NC 6=USB_P1_N 7=USB_P1_P 8=USB_A_N 9=USB_A_P 10=NC 11=XI_HUB 12=XO_HUB 13=USB_B_N 14=USB_B_P 15=NC 16=NC 17=NC 18=VDD33_HUB 19=VDD33_HUB 20=USB_UP_N 21=USB_UP_P 22=NC 23=VDD33_HUB 24=VDD33_HUB 25=NC 26=V5L 27=GND 28=VDD33_HUB | hub (D31); OVCUR1-4# held inactive |
| Y2 | X322512MSB4SI | X322512MSB4SI | C9002 | 1=XI_HUB 2=GND 3=XO_HUB 4=GND | no load capacitors (G9) |
| C27 | C | 1u | C52923 | 1=V5L 2=GND | at U6 pin 26 (V5) |
| C28 | C | 100n | C307331 | 1=VDD33_HUB 2=GND | at U6 pin 28 (VDD33) |
| C29 | C | 10u | C15850 | 1=VDD33_HUB 2=GND | at U6 pin 28 (VDD33) |
| TP13 | TestPoint | VDD33_HUB | none | 1=VDD33_HUB | D31 |
<!-- netlist:end -->

### Sheet `adc` — U7, U17, the SPI level shifters, U30 (Rev0.4 §3.3, §6.4)

<!-- netlist:begin sheet=adc -->
| Ref | Symbol | Value | Order | Pins | Note |
|---|---|---|---|---|---|
| U7 | MCP3208-CI-P | MCP3208-CI/P | Akizuki g100238 | 1=ADC_L_A 2=ADC_M_A 3=ADC_H_A 4=ADC_VREF_CHK 5=ADC_VJ4 6=GND 7=GND 8=GND 9=GND 10=ADC_CS 11=ADC_DIN 12=DOUT_A 13=ADC_SCLK 14=GND 15=VDDA 16=V5A | port A + VREF_CHK, V_J4 |
| C30 | C | 100n | C307331 | 1=V5A 2=GND | at U7 pin 16 (Vdd) |
| C31 | C | 100n | C307331 | 1=VDDA 2=GND | at U7 pin 15 (Vref) |
| U17 | MCP3208-CI-P | MCP3208-CI/P | Akizuki g100238 | 1=ADC_L_B 2=ADC_M_B 3=ADC_H_B 4=ADC_CC1 5=ADC_CC2 6=GND 7=GND 8=GND 9=GND 10=ADC_CS 11=ADC_DIN 12=DOUT_B 13=ADC_SCLK 14=GND 15=VDDA 16=V5A | port B + J4 CC1, CC2 |
| C32 | C | 100n | C307331 | 1=V5A 2=GND | at U17 pin 16 (Vdd) |
| C33 | C | 100n | C307331 | 1=VDDA 2=GND | at U17 pin 15 (Vref) |
| Q50 | 2N7002 | 2N7002 | C8545 | 1=ADC_SCLK_3V 2=GND 3=ADC_SCLK | SCLK level shifter (inverting) |
| R27 | R | 1.5k | C25867 | 1=V5L 2=ADC_SCLK | pull-up to V5L |
| Q51 | 2N7002 | 2N7002 | C8545 | 1=ADC_CS_3V 2=GND 3=ADC_CS | CS level shifter (inverting) |
| R28 | R | 1.5k | C25867 | 1=V5L 2=ADC_CS | pull-up to V5L |
| Q52 | 2N7002 | 2N7002 | C8545 | 1=ADC_DIN_3V 2=GND 3=ADC_DIN | DIN level shifter (inverting) |
| R29 | R | 1.5k | C25867 | 1=V5L 2=ADC_DIN | pull-up to V5L |
| R30 | R | 10k | C25744 | 1=DOUT_A 2=DOUT_A_3V | DOUT_A divider top |
| R31 | R | 15k | C25756 | 1=DOUT_A_3V 2=GND | DOUT_A divider bottom |
| R32 | R | 10k | C25744 | 1=DOUT_B 2=DOUT_B_3V | DOUT_B divider top |
| R33 | R | 15k | C25756 | 1=DOUT_B_3V 2=GND | DOUT_B divider bottom |
| U30 | LM393DR2G | LM393DR2G | C7955 | 1=EN_G_A 2=AMP_H_A 3=THO_A 4=GND 5=THO_B 6=AMP_H_B 7=EN_G_B 8=V12F | CMP_OC_A, CMP_OC_B (shared); on V12F (D34) |
| C34 | C | 100n | C307331 | 1=V12F 2=GND | at U30 pin 8 |
<!-- netlist:end -->

## Channel block (port A and port B)

### Sheets `channel_a` and `channel_b` (Rev0.4 §3.1, §3.2, §3.4)

<!-- netlist:begin sheet=channel_a,channel_b -->
| Ref A | Ref B | Symbol | Value | Order | Pins | Note |
|---|---|---|---|---|---|---|
| Q10 | Q30 | AO3401A | AO3401A | C15127 | 1=GSW_{x} 2=SRC_{x} 3=VBUS_IN | port switch, input side |
| Q11 | Q31 | AO3401A | AO3401A | C15127 | 1=GSW_{x} 2=SRC_{x} 3=VSUP_{x} | port switch, output side |
| R101 | R201 | R | 1M | C26083 | 1=GSW_{x} 2=SRC_{x} | R_GS, holds the switch off |
| C101 | C201 | C | 10n | C15195 | 1=GSW_{x} 2=VSUP_{x} | C_M soft-start Miller, part 1 (D34) |
| C102 | C202 | C | 10n | C15195 | 1=GSW_{x} 2=VSUP_{x} | C_M soft-start Miller, part 2 (D34) |
| R102 | R202 | R | 100k | C25741 | 1=SSD_{x} 2=GSW_{x} | R_on (D34) |
| Q12 | Q32 | 2N7002 | 2N7002 | C8545 | 1=EN_G_{x} 2=GND 3=SSD_{x} | EN driver |
| R103 | R203 | R | 33k | C25779 | 1=EN_{x} 2=CC1_{x} | Rp from EN |
| R104 | R204 | R | 33k | C25779 | 1=EN_{x} 2=CC2_{x} | Rp from EN |
| R105 | R205 | R | 10k | C25744 | 1=EN_{x} 2=EN_G_{x} | EN series |
| R106 | R206 | R | 100k | C25741 | 1=EN_G_{x} 2=GND | EN_G pull-down (OFF by default) |
| R107 | R207 | R | 100k | C25741 | 1=EN_G_{x} 2=OC_{x} | OC_x reads EN_G |
| Q14 | Q34 | 2N7002 | 2N7002 | C8545 | 1=EN_G_{x} 2=GND 3=DIS_{x} | EN inverter |
| R108 | R208 | R | 10k | C25744 | 1=V3V3 2=DIS_{x} | DIS pull-up |
| R109 | R209 | R | 100k | C25741 | 1=DIS_{x} 2=DISG_{x} | keeps Q13's gate off the fast DIS node (D34) |
| Q13 | Q33 | AO3400A | AO3400A | C20917 | 1=DISG_{x} 2=GND 3=DCH_{x} | VBUS discharge |
| R110 | R210 | R | 1k | C11702 | 1=VBUS_{x} 2=DCH_{x} | discharge load |
| Q15 | Q35 | 2N7002 | 2N7002 | C8545 | 1=DIS_{x} 2=GND 3=FOFF_{x} | fast-off driver |
| R111 | R211 | R | 5.1k | C25905 | 1=FOFF_{x} 2=QB_{x} | R_B, Q16 base (D34) |
| R112 | R212 | R | 100k | C25741 | 1=QB_{x} 2=SRC_{x} | R_BE (D34) |
| Q16 | Q36 | S9012 | S9012 | C8543 | 1=QB_{x} 2=SRC_{x} 3=GSW_{x} | fast-off clamp: gate to common source |
| RS10 | RS20 | TSL1TTER100D | TSL1TTER100D 0.1R | Akizuki g109588 | 1=VSUP_{x} 2=RH_SS_{x} 3=RH_SL_{x} 4=LAD1_{x} | R_H, Kelvin land |
| RS11 | RS21 | MFU100F10RB | MFU100F10RB 10R | Akizuki g108805 | 1=LAD1_{x} 2=RM_SS_{x} 3=RM_SL_{x} 4=LAD2_{x} | R_M, sense at each lead pad |
| RS12 | RS22 | R_Shunt_0805 | 510R 1% 100ppm 0805 | C17734 | 1=LAD2_{x} 2=RL_SS_{x} 3=RL_SL_{x} 4=VBUS_{x} | R_L, Kelvin land |
| Q17 | Q37 | AO3401A | AO3401A | C15127 | 1=GM_{x} 2=LAD1_{x} 3=VBUS_{x} | FET_M, bypasses R_M + R_L |
| R113 | R213 | R | 1M | C26083 | 1=GM_{x} 2=LAD1_{x} | FET_M gate return (OFF bias) |
| Q18 | Q38 | AO3401A | AO3401A | C15127 | 1=GL_{x} 2=LAD2_{x} 3=VBUS_{x} | FET_L, bypasses R_L |
| R114 | R214 | R | 1M | C26083 | 1=GL_{x} 2=LAD2_{x} | FET_L gate return (OFF bias) |
| Q19 | Q39 | 2N7002 | 2N7002 | C8545 | 1=HOLD_M_{x} 2=GND 3=GM_{x} | FET_M hold (default ON) |
| R115 | R215 | R | 10k | C25744 | 1=V3V3 2=HOLD_M_{x} | hold pull-up |
| Q20 | Q40 | 2N7002 | 2N7002 | C8545 | 1=HOLD_L_{x} 2=GND 3=GL_{x} | FET_L hold (default ON) |
| R116 | R216 | R | 10k | C25744 | 1=V3V3 2=HOLD_L_{x} | hold pull-up |
| Q24 | Q44 | 2N7002 | 2N7002 | C8545 | 1=EVTG_M_{x} 2=GND 3=EVT_M_{x} | EVT_M level shifter (inverting) |
| R117 | R217 | R | 100k | C25741 | 1=GM_{x} 2=EVTG_M_{x} | event series |
| Q25 | Q45 | 2N7002 | 2N7002 | C8545 | 1=EVTG_L_{x} 2=GND 3=EVT_L_{x} | EVT_L level shifter (inverting) |
| R118 | R218 | R | 100k | C25741 | 1=GL_{x} 2=EVTG_L_{x} | event series |
| U10 | U20 | OP07CDR | OP07CDR | C7433 | 1=NC 2=X_H_{x} 3=INP_H_{x} 4=GND 5=NC 6=OUT_H_{x} 7=V12F 8=NC | HIGH mirror amp |
| C103 | C203 | C | 100n | C307331 | 1=V12F 2=GND | at U10 pin 7 |
| R119 | R219 | R | 100 | C25076 | 1=RH_SS_{x} 2=X_H_{x} | R1 HIGH |
| R120 | R220 | R | 1M | C26083 | 1=V_INJ 2=X_H_{x} | R_INJ HIGH (pedestal) |
| R121 | R221 | R | 10k | C25744 | 1=RH_SL_{x} 2=INP_H_{x} | +IN guard HIGH |
| R122 | R222 | R | 1k | C11702 | 1=OUT_H_{x} 2=GATE_H_{x} | gate resistor HIGH |
| Q21 | Q41 | AO3401A | AO3401A | C15127 | 1=GATE_H_{x} 2=X_H_{x} 3=AMP_H_{x} | mirror FET HIGH |
| R123 | R223 | R | 2.4k | C22940 | 1=AMP_H_{x} 2=GND | R_OUT HIGH |
| C104 | C204 | C | 220p | C1530 | 1=AMP_H_{x} 2=GND | C_N HIGH |
| R124 | R224 | R | 1k | C11702 | 1=AMP_H_{x} 2=ADC_H_{x} | to the ADC, CH2 |
| U11 | U21 | OP07CDR | OP07CDR | C7433 | 1=NC 2=X_M_{x} 3=INP_M_{x} 4=GND 5=NC 6=OUT_M_{x} 7=V12F 8=NC | MID mirror amp |
| C105 | C205 | C | 100n | C307331 | 1=V12F 2=GND | at U11 pin 7 |
| R125 | R225 | R | 100 | C25076 | 1=RM_SS_{x} 2=X_M_{x} | R1 MID |
| R126 | R226 | R | 1M | C26083 | 1=V_INJ 2=X_M_{x} | R_INJ MID |
| R127 | R227 | R | 10k | C25744 | 1=RM_SL_{x} 2=INP_M_{x} | +IN guard MID |
| R128 | R228 | R | 1k | C11702 | 1=OUT_M_{x} 2=GATE_M_{x} | gate resistor MID |
| Q22 | Q42 | AO3401A | AO3401A | C15127 | 1=GATE_M_{x} 2=X_M_{x} 3=AMP_M_{x} | mirror FET MID |
| R129 | R229 | R | 1.5k | C25867 | 1=AMP_M_{x} 2=GND | R_OUT MID |
| C106 | C206 | C | 330p | C1664 | 1=AMP_M_{x} 2=GND | C_N MID |
| R130 | R230 | R | 1k | C11702 | 1=AMP_M_{x} 2=ADC_M_{x} | to the ADC, CH1 |
| U12 | U22 | OP07CDR | OP07CDR | C7433 | 1=NC 2=X_L_{x} 3=INP_L_{x} 4=GND 5=NC 6=OUT_L_{x} 7=V12F 8=NC | LOW mirror amp |
| C107 | C207 | C | 100n | C307331 | 1=V12F 2=GND | at U12 pin 7 |
| R131 | R231 | R | 100 | C25076 | 1=RL_SS_{x} 2=X_L_{x} | R1 LOW |
| R132 | R232 | R | 1M | C26083 | 1=V_INJ 2=X_L_{x} | R_INJ LOW |
| R133 | R233 | R | 10k | C25744 | 1=RL_SL_{x} 2=INP_L_{x} | +IN guard LOW (the one amplifier input on VBUS_x, G7) |
| R134 | R234 | R | 1k | C11702 | 1=OUT_L_{x} 2=GATE_L_{x} | gate resistor LOW |
| Q23 | Q43 | AO3401A | AO3401A | C15127 | 1=GATE_L_{x} 2=X_L_{x} 3=AMP_L_{x} | mirror FET LOW |
| R135 | R235 | R | 1.5k | C25867 | 1=AMP_L_{x} 2=GND | R_OUT LOW |
| C108 | C208 | C | 330p | C1664 | 1=AMP_L_{x} 2=GND | C_N LOW |
| R136 | R236 | R | 1k | C11702 | 1=AMP_L_{x} 2=ADC_L_{x} | to the ADC, CH0 |
| U13 | U23 | LM393DR2G | LM393DR2G | C7955 | 1=GL_{x} 2=AMP_L_{x} 3=THL_{x} 4=GND 5=THM_{x} 6=AMP_M_{x} 7=GM_{x} 8=V12F | CMP_L (unit A), CMP_M (unit B); amp to -IN (D34) |
| C109 | C209 | C | 100n | C307331 | 1=V12F 2=GND | at U13 pin 8 |
| R137 | R237 | R | 15k | C25756 | 1=TH_REF 2=THL_{x} | CMP_L threshold (D34) |
| C110 | C210 | C | 220p | C1530 | 1=THL_{x} 2=GND | CMP_L hysteresis divider (D34) |
| C111 | C211 | C | 15p | C1548 | 1=GL_{x} 2=THL_{x} | CMP_L hysteresis, output to +IN (D34) |
| R138 | R238 | R | 15k | C25756 | 1=TH_REF 2=THM_{x} | CMP_M threshold (D34) |
| C112 | C212 | C | 220p | C1530 | 1=THM_{x} 2=GND | CMP_M hysteresis divider (D34) |
| C113 | C213 | C | 15p | C1548 | 1=GM_{x} 2=THM_{x} | CMP_M hysteresis, output to +IN (D34) |
| R139 | R239 | R | 15k | C25756 | 1=TH_REF 2=THO_{x} | CMP_OC threshold, to U30 (D34) |
| C114 | C214 | C | 220p | C1530 | 1=THO_{x} 2=GND | CMP_OC hysteresis divider (D34) |
| C115 | C215 | C | 15p | C1548 | 1=EN_G_{x} 2=THO_{x} | CMP_OC hysteresis, output to +IN (D34) |
| J2 | J3 | AE-USB2.0-TYPE-C | AE-USB2.0-TYPE-C | Akizuki g113080 | 1=VBUS_{x} 2=USB_{x}_N 3=USB_{x}_P 4=GND 5=CC1_{x} 6=CC2_{x} 7=GND | OUT A / OUT B |
| C116 | C216 | C | 10u | C15850 | 1=VBUS_{x} 2=GND | port capacitor |
| D2 | D3 | PSM712-LF-T7 | PSM712-LF-T7 | C32677 | 1=CC1_{x} 2=CC2_{x} 3=GND | CC ESD, at the connector |
| R140 | R240 | R | 510 | C17734 | 1=LED_ON_{x} 2=LEDA_ON_{x} | green LED resistor (D34) |
| D10 | D12 | KT-0805G | KT-0805G | C2297 | 1=GND 2=LEDA_ON_{x} | port ON |
| R141 | R241 | R | 510 | C17734 | 1=LED_FLT_{x} 2=LEDA_FLT_{x} | red LED resistor (D34) |
| D11 | D13 | NCD0805R1 | NCD0805R1 | C84256 | 1=GND 2=LEDA_FLT_{x} | port fault |
| SW1 | SW2 | TS-1187A-B-A-B | TS-1187A-B-A-B | C318884 | 1=BTN_{x} 2=GND | port button |
| TP101 | TP201 | TestPoint | OUT_H | none | 1=OUT_H_{x} | Rev0.4 §12 item 5 (V-MEAS-00) |
| TP102 | TP202 | TestPoint | GATE_H | none | 1=GATE_H_{x} | Rev0.4 §12 item 5 (V-MEAS-00) |
| TP103 | TP203 | TestPoint | HOLD_M | none | 1=HOLD_M_{x} | Rev0.4 §12 item 5 (V-MEAS-06) |
| TP104 | TP204 | TestPoint | HOLD_L | none | 1=HOLD_L_{x} | Rev0.4 §12 item 5 (V-MEAS-06) |
| TP105 | TP205 | TestPoint | VSUP | none | 1=VSUP_{x} | P11 |
| TP106 | TP206 | TestPoint | VBUS | none | 1=VBUS_{x} | P11 |
<!-- netlist:end -->

## Schematic-only symbols

KiCad's ERC needs a driver on every net whose pins include a power input but no power output.
These nets get a `PWR_FLAG`, the project library's copy of KiCad's `power:PWR_FLAG` (the
project has no global symbol table to resolve `power:`). It is not a part and does not
appear in the netlist.

<!-- flags:begin -->
| Net | Sheet | Why |
|---|---|---|
| V5L | power | its only source is J1's module pin 1, a passive pin |
| V12F | power | behind R10 |
| VDDA | power | behind FB1 |
| V5A | power | behind R16 |
<!-- flags:end -->

## What this list cannot see

- Whether a value is right: the circuit document and `CIRCUIT_DESIGN_Rev0.4_calc.py` decide
  that. The checker only proves that the schematic carries what this list says.
- Placement notes ("at U1 pin 1") are layout instructions for P3; no netlist shows them.
- Pin functions: the checker compares pin numbers and nets, so a symbol with a wrong pin map
  passes it. The symbols are checked against the datasheets by `check_libraries.py` (P1).
