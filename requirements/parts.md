# USB Power-Control Hub — Parts Selection and Sourcing Record

**State: WIP. No part is chosen.** First pass 2026-11-03 (Rev0.2). Reworked the same day for
circuit Rev0.3 under the user's sourcing rule D13, and for Rev0.4 under D22 (Basic parts only). Every row is a *candidate* until a reviewer
marks it confirmed against the actual PCBA order (CLAUDE.md Section 4.1).

This is the single place for candidates, stock and datasheet facts. The circuit document
(`design/circuit/CIRCUIT_DESIGN_Rev0.4.md`) derives the constraints; this file records which
parts meet them.

## The sourcing rule (D13, user, 2026-11-03)

- **Machine-placed by JLCPCB:** small parts, which MUST be JLCPCB **Basic** with assembly-pool
  stock ≥ 500.
- **Hand-soldered by the user:** large parts, which MUST be **in stock at Akizuki**
  (akizukidenshi.com).
- **Never** an Extended-only PCBA. Where no allowed part does a job, the function is reduced
  (circuit Rev0.4 §7.4).
- **Avoid special or hard-to-source parts**, and **reduce part types and count** (the user's
  restated list, 2026-11-03; quoted in circuit Rev0.4's header). One part per value and one
  voltage rating per value: 35 machine-placed types.
- **No Preferred Extended either** (D22, user, 2026-11-03). Rev0.3's two Preferred Extended
  parts are removed; see "Removed in Rev0.4" below.

## How the numbers were obtained

- **JLCPCB stock and class:** `python tools/jlc_stock.py <LCSC numbers>` on 2026-11-03 (UTC).
  - The tool queries the JLCPCB **assembly-parts** pool. That is the authoritative pool; LCSC
    retail stock is a different one (CLAUDE.md §4.1, easy-stick lesson 14.8).
  - Its docstring lists what it cannot see — chiefly electrical suitability, stock at order
    time, and footprints.
- **The Basic catalogue (fact 13 in the circuit document)** was enumerated from the same API on
  2026-11-03: 351 Basic parts — 182 resistors, 88 MLCCs and 81 others. Among the 81 there is no
  microcontroller, USB hub, USB-C receptacle, USB D± ESD array, current-sense amplifier,
  analog mux, multi-channel ADC or fuse.
- **Akizuki stock:** the product page's 通販購入可能数 field, read on 2026-11-03.
  - Akizuki stock changes daily, and no checked tool reads it.
  - Recheck it by hand at order time (V-MFG-02).
- **Datasheet facts:** text extracted from the manufacturer PDF, 2026-11-03. Only parameters
  marked *verified* were read; a part's other properties are unconfirmed.
  - JLCPCB part-library copies (fetched through the assembly-parts API; the signed URLs
    expire): OP07CDR TI SLOS099F (Jan 2014); AO3401A AOS Rev 3.1 (Dec 2023); AO3400A AOS
    Rev 3 (Dec 2011); LM393DR2G onsemi LM393/D Rev 25; SMBJ6.5CA Zhuhai Hongjiacheng Rev 2.1;
    AMS1117-3.3 AMS (no revision marking); CJ431 JSCJ "M, Oct 2017". (Rev0.3 also read
    STM32F103C8T6 DS5319 Rev 18 and SRV05-4 Rev 2.1; both parts are removed in Rev0.4.)
  - Microchip MCP3204/3208 DS21298E (2008), fetched from microchip.com on 2026-11-03.
  - Other sources: CH334/CH335 datasheet V2.5 (WCH; copy at
    `https://akizukidenshi.com/goodsaffix/CH334_335.pdf`); MAU104 Minmax REV:0 2005/04; the
    Akizuki product pages for the module and shunt facts.
- **Recheck** immediately before upload and again before payment (CLAUDE.md §4.1):

```
python tools/jlc_stock.py C7433 C7955 C3113 C6186 C15127 C20917 C8545 C8543 C7420377 C32677 C9002 C2297 C84256 C318884 C14709 C17734 C25905 C25779 C25867 C11702 C25744 C25741 C22940 C25756 C26083 C25076 C25077 C1664 C1530 C15850 C45783 C307331 C52923 C1523 C15195
```

Class: **Basic** / **Preferred Extended** / **Extended**, as the API reports it, or **Akizuki**
(hand-soldered). Stock below **500** on a JLCPCB row is flagged ⚠.

---

## Hand-soldered parts (Akizuki)

| Ref | Part | Akizuki code | Model | Stock | Price (tax incl.) | Checked |
|---|---|---|---|---:|---:|---|
| U1 | RP2040 module, 21 × 21 mm, 2.54 mm grid, headers not fitted | g116762 | PGA2040 (Pimoroni) | 41 | ¥1,680 | 2026-11-03 |
| U7, U17 | 12-bit 8-channel SPI ADC, DIP16 | g100238 | MCP3208-CI/P (Microchip) | 733 | ¥500 | 2026-11-03 |
| J1–J4 | USB Type-C receptacle DIP kit (simple), 4 per board | g113080 | AE-USB2.0-TYPE-C | 711 | ¥350 | 2026-11-03 |
| U6 | CH335F 4-port USB hub breakout module kit | g129556 | AE-QFN28-DIP(CH335F) | 453 | ¥420 | 2026-11-03 |
| U5 | 1 W isolated DC-DC, 12 V 84 mA | g104132 | MAU104 (Minmax) | 178 | ¥520 | 2026-11-03 |
| RS10, RS20 | Current-sense chip resistor 0.1 Ω 1 W ±0.5 % | g109588 | TSL1TTER100D (KOA) | 374 | ¥130 | 2026-11-03 |
| RS11, RS21 | Metal-film resistor 10 Ω 1 W ±1 % (1/4 W size) | g108805 | MFU100F10RB (Faithful Link) | 175 bags of 100 | ¥600 / bag | 2026-11-03 |

The thinnest is the PGA2040, at 41 pcs: enough for prototypes, but check it first. The next
is the MAU104, at 178.

- *Verified (PGA2040: Akizuki page; Pimoroni schematic):*
  - RP2040 on a 21 × 21 mm board with a 2.54 mm grid of plated holes; pin headers are not
    fitted.
  - USB_DP, USB_DM, BOOTSEL, RUN, SWCLK and SWDIO are brought out to pins, with all 30 GPIO.
    This is why it, and not the Pico or the AE-RP2040 kit, can sit behind the CH335F.
  - *To confirm (OI-31, V-MEAS-06):* the supply input (3.3 V only, or 5 V with an on-module
    regulator), whether 27 Ω D+/D− series resistors are fitted, the flash part and its unique
    ID, the crystal, and the module's exact pin map for the footprint.
- *Verified (MCP3208, Microchip DS21298E):*
  - 12-bit, 8 single-ended channels, SPI; V<sub>DD</sub> 2.7–5.5 V; V<sub>REF</sub> 0.25 V to
    V<sub>DD</sub>.
  - INL ±1.0 typ / ±2 max LSB (C grade), DNL ±1 LSB max; offset ±3 LSB, gain ±5 LSB max
    (both removed by calibration). Specified at V<sub>DD</sub> = V<sub>REF</sub> = 5 V.
  - f<sub>CLK</sub> 1.0 MHz max at V<sub>DD</sub> 2.7 V, 2.0 MHz at 5 V; 20 clocks per
    conversion; t<sub>HI</sub>, t<sub>LO</sub> ≥ 250 ns.
  - Sample phase 1.5 clocks, through a 1 kΩ switch onto 20 pF; pin capacitance 7 pF. The
    clock need not be constant or symmetric as long as each timing limit is met, and the held
    sample is good for 1.2 ms (§6.2). The sample phase can therefore be stretched.
  - Inputs rated −0.6 V to V<sub>DD</sub> + 0.6 V; **no input-current rating**. Leakage
    ±1 µA max.
  - V<sub>IH</sub> 0.7 V<sub>DD</sub>; V<sub>OH</sub> ≥ 4.1 V at 4.5 V; I<sub>DD</sub>
    400 µA max; V<sub>REF</sub> current 150 µA max.
  - *To confirm (OI-31, V-MEAS-06):* INL at V<sub>REF</sub> = 3.3 V (only typical curves),
    and the settling with the stretched sample.
- *Verified (AE-USB2.0-TYPE-C page, schematic, drawing):*
  - Pins on one 1 × 7 row, 2.54 mm pitch: VBUS, D−, D+, GND, CC1, CC2, GND.
  - Plus mechanical pins beside the receptacle.
  - **No CC resistors are fitted**, so the same kit serves as host (J1, J4: add Rd) and as
    downstream port (J2, J3: add Rp).
  - Rated 48 V, 5 A. Board ≈ 20 mm wide, the dimension that makes the J2–J3 pitch ≥ 20 mm.
  - SBU is not brought out.
- *Verified (CH335F module page; CH335 datasheet):*
  - DIP30, 3.3–5 V; HS upstream and downstream, MTT.
  - **Needs an external 12 MHz crystal** (load capacitors built into the chip).
  - V5 4.5–5.25 V, 85 mA typical.
  - PSELF strap on pin 1/LED1 (pulled up = self-powered by default); PGANG on pin 3/LED2.
  - PWREN1–4# on pins 4, 2, 10, 5; OVCUR1–4# on pins 24, 23, 19, 18.
  - EEPROM-configurable descriptor; default MaxPower 0x32 (100 mA).
  - *To confirm (OI-24):* the module's outline, its pin-to-function map, and whether the
    QFN28 comes mounted. Akizuki publishes no module drawing.
- *Verified (MAU104 datasheet, Minmax REV:0 2005/04):*
  - Output 12 V, 84 mA max, 1.5 mA min load. Accuracy ±1 % typ / ±3 % max.
  - Line regulation ±1.2 % per 1 % V<sub>in</sub>; load regulation 7 % max (20–100 % load).
  - Ripple 50 mVpp typ / 75 mVpp max; switching ~100 kHz.
  - Input 4.5–5.5 V, 30 mA typ no-load input current; efficiency 78 %.
  - Isolation capacitance 60 pF typ; output short circuit 0.5 s max.
  - Used at ≈ 15 mA typ / 30 mA max load (6 × OP07), which is **below the 20 % point where load
    regulation is specified**. Its output is not trusted as a reference; U4 regulates V_INJ.
- *Verified (TSL1TTER100D page):* 0.1 Ω, 1 W, ±0.5 %, ±100 ppm/°C, 6.3 × 3.1 × 1 mm, metal
  terminals, −55 to 180 °C.
  - It is a 2-terminal part. The Kelvin connection is made by the 4-pad land pattern
    (CLAUDE.md §5.4, G2).
  - *To confirm:* KOA's recommended land, and a land split for Kelvin sense.
- *Verified (MFU100F10RB page):* 10 Ω, 1 W, ±1 %, ±100 ppm/°C, 6 mm × 2.3 mm axial,
  −55 to 155 °C.
  - *To confirm (OI-28):* short-time overload — it must survive 2.35 W for 10 ms in the
    stuck-MID fault.

**Rejected at Akizuki:**
- g110697 0.1 Ω 5 W metal plate: ±350 ppm/°C.
- g108798 0.1 Ω 1 W metal film: axial, so a Kelvin land is less clean than on the KOA chip.
- g104134 MAU108 ±12 V: the mirror FET gate would see −17 V.
- g116132 Raspberry Pi Pico and g117542 AE-RP2040 kit (and the XIAO RP2040): D+/D− are not
  on the module pins, so the module cannot sit behind the CH335F.
- g117732 MCP3204-BI/P (¥770): 4 channels, and each ADC needs 5 (three amplifiers, two aux).
- Nucleo-32 boards: D± on pins, but too few free I/O. Nucleo-F303K8: no USB. Nucleo-64:
  82.5 × 70 mm.

---

## Machine-placed parts (JLCPCB)

All rows checked 2026-11-03 with `tools/jlc_stock.py`.

### Active parts

| Ref | MPN | LCSC | Package | Stock | Class | Role |
|---|---|---|---|---:|---|---|
| U10–U12, U20–U22 | OP07CDR | C7433 | SOIC-8 | 248,598 | Basic | Mirror amplifiers |
| U13, U23, U30 | LM393DR2G | C7955 | SOIC-8 | 357,235 | Basic | Range and OC comparators |
| U2 | AMS1117-3.3 | C6186 | SOT-223 | 1,742,729 | Basic | V3V3 |
| U3, U4 | CJ431 | C3113 | SOT-23 | 689,130 | Basic | VREF_CHK 2.5 V; V_INJ 8 V shunt regulator |
| Q10, Q11, Q17, Q18, Q21–Q23 (+20) | AO3401A | C15127 | SOT-23 | 1,705,924 | Basic | Port switch, bypass, mirror P-FETs (14) |
| Q13 (+20) | AO3400A | C20917 | SOT-23 | 956,538 | Basic | VBUS discharge |
| Q12, Q14, Q15, Q19, Q20, Q24, Q25 (+20); Q50–Q52 | 2N7002 | C8545 | SOT-23 | 3,305,126 | Basic | Drivers, inverters, holds, level shifters (17) |
| Q16 (+20) | S9012 | C8543 | SOT-23 | 167,918 | Basic | Fast-off clamp PNP |
| D1–D4 | PSM712-LF-T7 | C32677 | SOT-23 | 130,193 | Basic | CC ESD on J1–J4 |
| D5, D6 | SMBJ6.5CA | C7420377 | DO-214AA (SMB) | 1,186,104 | Basic | J1, J4 VBUS TVS |
| Y2 | X322512MSB4SI (12 MHz) | C9002 | SMD3225-4P | 303,806 | Basic | CH335F |
| D10, D12 | KT-0805G (green) | C2297 | 0805 | 2,184,199 | Basic | Port ON |
| D11, D13 | NCD0805R1 (red) | C84256 | 0805 | 2,416,659 | Basic | Port fault |
| SW1–SW3 | TS-1187A-B-A-B | C318884 | SMD 5.1 × 5.1 | 1,054,631 | Basic | Port buttons; BOOT |
| FB1 | BLM18PG121SN1D | C14709 | 0603 | 2,198,407 | Basic | VDDA ferrite |

- *Verified (OP07C, TI):*
  - V<sub>OS</sub> 60 µV typ, **no maximum given for the C grade** (OP07D max 150 µV is used
    as the planning bound); drift 0.5 µV/°C typ.
  - I<sub>B</sub> ±1.8 nA typ; noise 10.5 nV/√Hz.
  - Supply ±3 to ±18 V (≥ 6 V total); common mode ±13 V min at ±15 V; output ±12 V into
    10 kΩ at ±15 V.
  - GBW 0.4 min / 0.6 typ MHz; slew 0.3 V/µs.
  - *Assumed, to verify (OI-27):* common mode 2–10 V and output low ≤ 3.0 V on 0 / 12 V.
- *Verified (LM393):*
  - 1.3 µs response at 5 mV overdrive, 300 ns large-signal.
  - Supply 2–36 V; common mode 0 to V<sub>CC</sub> − 1.5 V; V<sub>OS</sub> ±5 mV max.
  - Open-collector output, sink ≥ 6 mA (16 typ).
- *Verified (AO3401A):*
  - R<sub>DS(on)</sub> 47 / 60 mΩ at −4.5 V, 60 / 85 mΩ at −2.5 V.
  - V<sub>GS(th)</sub> −0.5 / −0.9 / −1.3 V; Q<sub>g</sub> 7 nC at 4.5 V; C<sub>iss</sub> 645 pF.
  - −30 V; V<sub>GS</sub> ±12 V; I<sub>D</sub> −4 A.
- *Verified (AO3400A):* R<sub>DS(on)</sub> 19 / 32 mΩ at 4.5 V; V<sub>GS(th)</sub> 0.65 / 1.05 /
  1.45 V.
- *Verified (AMS1117):*
  - Dropout 1.1 / 1.3 V at 800 mA; 90 °C/W.
  - Minimum load 5 / 10 mA; I<sub>q</sub> 5 / 11 mA; output 3.251–3.349 V.
  - *To confirm:* the output-capacitor stability requirement (capacitance and ESR range) in
    the datasheet, against the 22 µF ceramic on V3V3.
- *Verified (CJ431):*
  - 2.475 / 2.5 / 2.525 V; catalogue lists the ±0.5 % rank.
  - I<sub>K(min)</sub> 0.45 / 1 mA.
  - Deviation over −25 to 85 °C: 4.5 typ / 17 max mV.
- *Verified (SMBJ6.5CA):* V<sub>RWM</sub> 6.5 V, V<sub>BR</sub> 7.22–7.98 V, clamp 11.2 V,
  I<sub>R</sub> 500 µA max. It sits only on non-measured rails (J1, J4 VBUS) because of that
  leakage.
- *Verified (C9002):* 12 MHz, C<sub>L</sub> 20 pF, ±10 ppm / ±20 ppm, ESR 80 Ω.
  - *To confirm (G9):* Y2 against the CH335F's built-in load capacitors.

### Passives (Basic, by value)

| Value | Use | LCSC | Package | Stock | Note |
|---|---|---|---|---:|---|
| 510 Ω ±1 % ±100 ppm | R_L shunt; U3 CJ431 feed from V3V3 | C17734 | 0805 | 2,198,725 | 0.125 W; stuck-LOW 47 mW |
| 100 Ω ±1 % ±100 ppm | Mirror R1 (×6) | C25076 | 0402 | 6,307,501 | — |
| 1.5 kΩ ±1 % ±100 ppm | R_OUT LOW, MID (×4); U4 feed; SCLK/CS/DIN pull-ups to V5L (×3) | C25867 | 0402 | 1,516,858 | — |
| 2.4 kΩ ±1 % ±100 ppm | R_OUT HIGH (×2) | C22940 | 0603 | 1,117,935 | — |
| 10 kΩ | +IN guard (×6), EN series, DIS pull-up, HOLD pull-ups (×4), DOUT divider top (×2) | C25744 | 0402 | 16,208,659 | — |
| 15 kΩ | U4 divider (33 k / 15 k → 8.0 V); V_J4 divider bottom; DOUT divider bottom (×2) | C25756 | 0402 | 2,494,056 | — |
| 33 kΩ | Rp (×4); U4 divider; V_J4 divider top (5.5 V → 1.72 V) | C25779 | 0402 | 2,369,774 | No 36 kΩ is Basic |
| 5.1 kΩ | Rd on J1, J4 CC (×4) | C25905 | 0402 | 4,938,551 | — |
| 100 kΩ | EN_G pull-down, event series | C25741 | 0402 | 7,841,979 | — |
| 1 MΩ | Bypass gate return (×4), pedestal R_INJ (×6) | C26083 | 0402 | 2,794,209 | — |
| 1 kΩ | ADC series, discharge, gate resistors, LEDs | C11702 | 0402 | 21,568,761 | — |
| 10 Ω | V12 filter; V5A filter | C25077 | 0402 | 3,068,120 | ±5 % (MPN …100J…); not in a measured path |
| 330 pF C0G | C_N on R_OUT LOW, MID | C1664 | 0603 | 691,081 | — |
| 220 pF X7R | C_N on R_OUT HIGH | C1530 | 0402 | 1,340,537 | No Basic C0G 220 pF found |
| 10 µF 25 V X5R | Port capacitor (×2); VDDA; V5A; bulk | C15850 | 0805 | 7,996,245 | Effective ≈ 7 µF at 5 V DC bias; bandwidth figures assume 10 µF |
| 22 µF 25 V | VBUS_IN bulk; V12F filter (2 ×); V3V3 (AMS1117 output) | C45783 | 0805 | 3,579,516 | — |
| 100 nF 50 V | All decoupling (one rating for every rail) | C307331 | 0402 | 20,893,452 | — |
| 1 µF 25 V | Regulator, CJ431 | C52923 | 0402 | 10,715,829 | — |
| 1 nF / 10 nF | Comparator hysteresis, soft-start Miller | C1523 / C15195 | 0402 | 2,345,349 / 5,868,443 | Values set at capture |

**Removed in Rev0.4 (D22):**

| Was | MPN | LCSC | Class | Now |
|---|---|---|---|---|
| U1 | STM32F103C8T6 | C8734 | Preferred Extended | PGA2040 (Akizuki) |
| D1–D3 | SRV05-4 | C7420376 | Preferred Extended | PSM712 on CC; D± unprotected |
| Y1 load capacitors | 33 pF C0G | C1562 | Basic | Not needed: Y1 is gone |

**Rejected in the Basic catalogue:**
- C25334 0.1 Ω 1206: **±800 ppm/°C**, which alone would use 0.8 % of the 1 % budget over
  10 °C.
- C17903 / C22859 10 Ω: ±400 ppm/°C, and 0.25 W against a 2.35 W fault.
- No Schottky clamp for the ADC inputs: BAT54C/BAT54S are Extended, and the Basic 1 A
  Schottkys (1N5819WS C191023, B5819W C8598) leak µA into the measured node. Running the
  MCP3208 from 5 V removes the need (circuit §3.2).
- OP07 is the only precision op-amp in Basic. LM358 / LM324 have 7 mV / 30 µV/°C offset, and
  TL072 3 mV.

---

## Rev0.2 candidates rejected by D13

All Extended. The full Rev0.2 rows, with stock and datasheet notes, are in Git history
(commit `4e59607`).

| Function | Rev0.2 candidate(s) | Replaced by |
|---|---|---|
| PD sink | CH224Q / CH224A / CH224K | J4 power-only input (D14) |
| Buck / buck-boost | TPS62130, TPS62933, TPS63070 class | None needed |
| 3.3 V regulators | TPS7A20 class, SY8089 class | AMS1117-3.3 |
| MCU + flash | RP2040 + W25Q | PGA2040 RP2040 module (Akizuki); Rev0.3 had STM32F103C8T6 |
| USB hub + 24 MHz crystal | USB2514B variants + X322524MOB4SI | CH335F module (Akizuki) + C9002 |
| ADC | ADS131M02 / M04 / M06 | 2 × MCP3208 (Akizuki); Rev0.3 had the STM32 ADC |
| Current-sense amplifier | INA190A2 | OP07CDR + AO3401A mirror |
| Sense mux | TMUX6209, ADG1209, TMUX1109 | Not needed (topology C) |
| Window comparator | TLV3202, TLV3502 | LM393DR2G |
| Bypass FET | CSD25402Q3A | AO3401A |
| Shunts | WSK2512 (20 mΩ, 10 mΩ, 2 Ω), RT0805 200 Ω | TSL1TTER100D, MFU100F10RB (Akizuki), 510 Ω C17734 |
| Load switch | SY6280AAC, TPS2553, TPS25947 | Back-to-back AO3401A |
| ESD | TPD4E05U06, USBLC6-2SC6 | PSM712 on CC only; D± unprotected (D22). Rev0.3 had SRV05-4 |

## Not yet selected

- **J4 input fuse (OI-29).** No fuse or PTC is Basic. Akizuki resettable fuses are the
  candidates, and must be checked for hold current ≥ 2.5 A at 5 V.
- **Pin headers and sockets for the modules and the DIP16 ADCs (OI-23).** These are Akizuki
  parts; their height decides what fits underneath.
- **Heat-set M2 inserts** (mechanical; not under D13).
