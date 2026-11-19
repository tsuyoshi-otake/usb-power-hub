# USB Power-Control Hub — Parts Selection and Sourcing Record

**State: WIP. No part is chosen.** First pass 2026-11-03 (Rev0.2). Reworked the same day for
circuit Rev0.3 under the user's sourcing rule D13, and for Rev0.4 under D22 (Basic parts only);
amended 2026-11-04 for D29 (the bare RP2040) and D31 (the bare CH335F), and 2026-11-12 for D37 (the
USB-C receptacles C2765186, machine-placed). Every row is a *candidate* until a reviewer
marks it confirmed against the actual PCBA order (CLAUDE.md Section 4.1).

This is the single place for candidates, stock and datasheet facts. The circuit document
(`design/circuit/CIRCUIT_DESIGN_Rev0.7.md`) derives the constraints; this file records which
parts meet them.

## The sourcing rule (D13, user, 2026-11-03)

- **Machine-placed by JLCPCB:** small parts, which MUST be JLCPCB **Basic** with assembly-pool
  stock ≥ 500.
- **Hand-soldered by the user:** large parts, which MUST be **in stock at Akizuki**
  (akizukidenshi.com).
- **Never** an Extended-only PCBA. Where no allowed part does a job, the function is reduced
  (circuit Rev0.7 §7.4).
- **Avoid special or hard-to-source parts**, and **reduce part types and count** (the user's
  restated list, 2026-11-03; quoted in circuit Rev0.4's header). One part per value and one
  voltage rating per value: 41 machine-placed types (the capture, D34, dropped the 1 nF
  C1523; D37 adds the USB-C receptacle C2765186).
- **No Preferred Extended either** (D22, user, 2026-11-03). Rev0.3's two Preferred Extended
  parts are removed; see "Removed in Rev0.4" below.
- **Three exceptions, all Extended, all the user's:**
  - the RP2040, C2040 (D29, 2026-11-04; 「素の RP2040 (推奨)」), which replaces the
    hand-soldered PGA2040 module;
  - the CH335F, C5137013 (D31, 2026-11-04; 「IC 単体にする (推奨)」), which replaces the
    hand-soldered Akizuki CH335F module;
  - the USB-C receptacle, C2765186 (D37, 2026-11-12; 「USB-C直付けのみ (推奨)」), which
    replaces the four hand-soldered Akizuki USB-C modules and their headers.

  Every other machine-placed part is Basic, so the PCBA is not Extended-only (38 of 41 types
  Basic). A fourth exception needs the user's decision.

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
- **Datasheet facts:** text extracted from the manufacturer PDF, 2026-11-03 (and 2026-11-04
  for D28 and D29). Only parameters marked *verified* were read; a part's other properties are
  unconfirmed.
  - D29 (2026-11-04): RP2040 datasheet (build 2025-02-20) and "Hardware design with RP2040"
    (Release 2), from datasheets.raspberrypi.com; Winbond W25Q128JV Rev. J (2024-04-25) and the
    YXC YSX321SL sheet for C9002 (a scanned image, read visually), through the JLCPCB
    assembly-parts API.
  - JLCPCB part-library copies (fetched through the assembly-parts API; the signed URLs
    expire): OP07CDR TI SLOS099F (Jan 2014); AO3401A AOS Rev 3.1 (Dec 2023); AO3400A AOS
    Rev 3 (Dec 2011); LM393DR2G onsemi LM393/D Rev 25; SMBJ6.5CA Zhuhai Hongjiacheng Rev 2.1;
    AMS1117-3.3 AMS (no revision marking); CJ431 JSCJ "M, Oct 2017". (Rev0.3 also read
    STM32F103C8T6 DS5319 Rev 18 and SRV05-4 Rev 2.1; both parts are removed in Rev0.4.)
  - Microchip MCP3204/3208 DS21298E (2008), fetched from microchip.com on 2026-11-03.
  - D31 (2026-11-04): the CH334/CH335 datasheet V2.5 re-read for the bare chip. Its package
    drawing (§5.6) is an image, so the page was rendered from the PDF and read visually.
  - Other sources: CH334/CH335 datasheet V2.5 (WCH; copy at
    `https://akizukidenshi.com/goodsaffix/CH334_335.pdf`); MAU104 Minmax REV:0 2005/04; the
    Akizuki product pages for the module and shunt facts.
- **Recheck** immediately before upload and again before payment (CLAUDE.md §4.1):

```
python tools/jlc_stock.py C2040 C5137013 C2765186 C97521 C7433 C7955 C3113 C6186 C15127 C20917 C8545 C8543 C7420377 C32677 C9002 C2297 C84256 C318884 C14709 C17734 C25905 C25779 C25867 C11702 C25744 C25741 C22940 C25197 C25756 C26083 C25076 C25077 C1664 C1530 C15850 C45783 C307331 C52923 C15195 C1548 C25092
```

Class: **Basic** / **Preferred Extended** / **Extended**, as the API reports it, or **Akizuki**
(hand-soldered). Stock below **500** on a JLCPCB row is flagged ⚠.

---

## Hand-soldered parts (Akizuki)

| Ref | Part | Akizuki code | Model | Stock | Price (tax incl.) | Checked |
|---|---|---|---|---:|---:|---|
| U7, U17 | 12-bit 8-channel SPI ADC, DIP16 | g100238 | MCP3208-CI/P (Microchip) | 733 | ¥500 | 2026-11-03 |
| U5 | 1 W isolated DC-DC, 12 V 84 mA | g104132 | MAU104 (Minmax) | 178 | ¥520 | 2026-11-03 |
| RS10, RS20 | Current-sense chip resistor 0.1 Ω 1 W ±0.5 % | g109588 | TSL1TTER100D (KOA) | 374 | ¥130 | 2026-11-03 |
| RS11, RS21 | Metal-film resistor 10 Ω 1 W ±1 % (1/4 W size) | g108805 | MFU100F10RB (Faithful Link) | 175 bags of 100 | ¥600 / bag | 2026-11-03 |
| F1 | Resettable fuse (PTC), 3.00 A hold / 6.00 A trip, 30 V, radial | g112630 | MF-R300 (Bourns) | 2,865 | ¥40 | 2026-11-03 |

The thinnest is the MAU104, at 178 pcs. The PGA2040 (g116762, 41 pcs on 2026-11-03), U1
until D29, is no longer used; its record is in Git at commit `6774bc5`. Nor is the CH335F
module (AE-QFN28-DIP(CH335F), g129556, ¥420, 453 pcs on 2026-11-03), U6 until D31; its
record is in Git at commit `3e11f68`. Nor are the four USB-C modules (AE-USB2.0-TYPE-C,
g113080, ¥350, 711 pcs on 2026-11-03) and their PH-1x40SG pin headers (g100167, ¥35, 8,000
pcs on 2026-11-04), J1–J4 until D37: the receptacles are machine-placed now. Their record
is in Git at commit `5a697aa`.

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
  - *Desk check (D28; DS21298E, re-read 2026-11-04):* Figure 2-2 (INL vs V<sub>REF</sub> at V<sub>DD</sub> 5 V, typical,
    "not tested or guaranteed") reads about +0.6 / −0.4 LSB at 3.3 V (+0.59 / −0.37 from the
    figure's vector data).
  - *To confirm on the first board (V-MEAS-06, D28):* INL at V<sub>REF</sub> = 3.3 V, and
    the settling with the stretched sample.
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
  - *Land (issue #6 P1):* KOA's TSL / SL / SLN sheet (Oct. 2014, Akizuki
    `/goodsaffix/tsl_sl_rohs.pdf`) gives the TSL1 body (L 6.3 ± 0.3, W 3.1 ± 0.2 mm) and
    electrodes (a 2.4 ± 0.2 mm wide, c 1.2 ± 0.3 mm long) but **no recommended land**. The
    Kelvin land is therefore derived, not the manufacturer's: each end is split across the
    width into a 1.85 mm force pad and a 0.60 mm sense pad, 0.25 mm apart, 2.0 mm long and
    reaching 0.45 mm past the longest body; both sense pads on one side; no paste (hand
    soldered). Footprint `R_Shunt_KOA_TSL1_6332Metric_Kelvin`.
- *Verified (MFU100F10RB page):* 10 Ω, 1 W, ±1 %, ±100 ppm/°C, 6 mm × 2.3 mm axial,
  −55 to 155 °C.
  - *Verified (Faithful Link MFU series datasheet, Akizuki `/goodsaffix/mfu.pdf`, fetched
    2026-11-04; D28):* RCWV = √(P × R), 3.16 V here. Short-time overload 2.5 × RCWV for 5 s
    (6.25 W), ΔR ≤ 1 %; pulse overload 4 × RCWV (16 W), 1 s on / 25 s off, 10,000 cycles,
    ΔR ≤ ±(1 % + 0.05 Ω). The stuck-MID fault, 2.35 W for 10 ms, is inside the short-time
    rating for up to 5 s (Rev0.7 §4).
  - *To confirm on the first board (V-MEAS-00):* R_M shifts < 0.1 % after 100 faults. The
    datasheet bounds the shift only after its harsher test.
- *Verified (MF-R300, Bourns MF-R series datasheet, Akizuki `/goodsaffix/mfr.pdf`,
  fetched 2026-11-03):*
  - V<sub>max</sub> 30 V, I<sub>max</sub> 40 A; I<sub>hold</sub> 3.00 A, I<sub>trip</sub>
    6.00 A at 23 °C.
  - R<sub>min</sub> 0.020 Ω, R<sub>max</sub> 0.05 Ω initial; R1<sub>max</sub> 0.08 Ω one
    hour after reflow or a trip. The design uses R1max.
  - Time to trip ≤ 10.8 s at 15 A; tripped dissipation 2.0 W.
  - Hold / trip vs ambient: 2.49 / 4.98 A at 40 °C, 2.31 / 4.62 A at 50 °C.
  - Body A ≤ 12.0 mm wide, B ≤ 18.3 mm tall, E ≤ 3.0 mm thick; leads 5.1 ± 0.7 mm apart,
    ⌀0.81 mm.
  - **18.3 mm is the tallest part on the board.** The enclosure must clear it, or F1 is
    bent flat (then 12 × 18.3 mm of board).
  - *Lead style (issue #6 P1):* the datasheet's table lists MF-R300 as style 2, whose drawing
    (PDF p3) has straight leads. The footprint `Fuse_Bourns_MF-R300_Style2_P5.10mm` puts the
    holes 5.1 mm apart (C nominal), drilled 1.1 mm for the ⌀0.81 mm lead, with a 12.0 × 3.0 mm
    body. *To confirm when the parts arrive (V-MECH-01):* that Akizuki's MF-R300 are style 2.

**Rejected at Akizuki:**
- g110697 0.1 Ω 5 W metal plate: ±350 ppm/°C.
- g108798 0.1 Ω 1 W metal film: axial, so a Kelvin land is less clean than on the KOA chip.
- g104134 MAU108 ±12 V: the mirror FET gate would see −17 V.
- g116132 Raspberry Pi Pico and g117542 AE-RP2040 kit (and the XIAO RP2040): D+/D− are not
  on the module pins, so the module cannot sit behind the CH335F.
- g117732 MCP3204-BI/P (¥770): 4 channels, and each ADC needs 5 (three amplifiers, two aux).
- g100769 RGEF300 (3.0 A hold, 5.1 A trip, ¥30): rated 16 V, and only a selection guide is
  at hand, with no resistance figures. g101344 VTP210GU (2.1 A) and g112629 MF-R185
  (1.85 A): hold current below the 2.33 A that the OC trips allow at their nominal 1.16 A
  (2.46 A at their highest, D34).
- Nucleo-32 boards: D± on pins, but too few free I/O. Nucleo-F303K8: no USB. Nucleo-64:
  82.5 × 70 mm.

---

## Machine-placed parts (JLCPCB)

All rows checked 2026-11-03 with `tools/jlc_stock.py`; rows added or changed for D29 on
2026-11-04 (marked †), for D31 the same day (marked ‡), and for D37 on 2026-11-12 (marked §).

### Active parts

| Ref | MPN | LCSC | Package | Stock | Class | Role |
|---|---|---|---|---:|---|---|
| U1 † | RP2040 | C2040 | LQFN-56 (7 × 7) | 5,845 | **Extended** (D29) | MCU |
| U6 ‡ | CH335F | C5137013 | QFN-28 (4 × 4) | 4,937 | **Extended** (D31) | USB 2.0 HS hub, 4 downstream ports (MTT) |
| J1–J4 § | TYPE-C 16PIN 2MD(073) (SHOU HAN) | C2765186 | SMD pads + 4 shell slots (8.94 × 7.35 × 3.16) | 1,070,668 | **Extended** (D37) | USB-C receptacles: HOST, PWR IN, OUT A, OUT B (4 per board) |
| U8 † | W25Q128JVSIQ | C97521 | SOIC-8 208 mil | 75,419 | Basic | QSPI flash; its unique ID is the USB serial number |
| U10–U12, U20–U22 | OP07CDR | C7433 | SOIC-8 | 248,598 | Basic | Mirror amplifiers |
| U13, U23, U30 | LM393DR2G | C7955 | SOIC-8 | 357,235 | Basic | Range and OC comparators |
| U2 | AMS1117-3.3 | C6186 | SOT-223 | 1,742,729 | Basic | V3V3 |
| U3, U4 | CJ431 | C3113 | SOT-23 | 689,130 | Basic | VREF_CHK 2.5 V; V_INJ 8 V shunt regulator |
| Q10, Q11, Q17, Q18, Q21–Q23 (+20); Q53 | AO3401A | C15127 | SOT-23 | 1,705,924 | Basic | Port switch, bypass, mirror P-FETs; J1 soft start (15, D35) |
| Q13 (+20) | AO3400A | C20917 | SOT-23 | 956,538 | Basic | VBUS discharge |
| Q12, Q14, Q15, Q19, Q20, Q24, Q25 (+20); Q50–Q52 | 2N7002 | C8545 | SOT-23 | 3,305,126 | Basic | Drivers, inverters, holds, level shifters (17) |
| Q16 (+20) | S9012 | C8543 | SOT-23 | 167,918 | Basic | Fast-off clamp PNP |
| D1–D4 | PSM712-LF-T7 | C32677 | SOT-23 | 130,193 | Basic | CC ESD on J1–J4 |
| D5, D6 | SMBJ6.5CA | C7420377 | DO-214AA (SMB) | 1,186,104 | Basic | J1, J4 VBUS TVS |
| Y1 †, Y2 | X322512MSB4SI (12 MHz) | C9002 | SMD3225-4P | 289,663 | Basic | RP2040 XOSC (Y1); CH335F (Y2) |
| D10, D12 | KT-0805G (green) | C2297 | 0805 | 2,184,199 | Basic | Port ON |
| D11, D13 | NCD0805R1 (red) | C84256 | 0805 | 2,416,659 | Basic | Port fault |
| SW1–SW3 | TS-1187A-B-A-B | C318884 | SMD 5.1 × 5.1 | 1,054,631 | Basic | Port buttons; BOOT (SW3, to QSPI_SS through 1 kΩ) |
| FB1 | BLM18PG121SN1D | C14709 | 0603 | 2,198,407 | Basic | VDDA ferrite |

- *Verified (RP2040, Raspberry Pi RP2040 datasheet build 2025-02-20, and "Hardware design
  with RP2040" Release 2; read 2026-11-04 for D29):*
  - LQFN-56, 7 × 7 mm, 0.4 mm pitch. The ePad is smaller than most; the datasheet says stock
    0.4 mm QFN-56 footprints may need adjusting. Its Figure 167 gives a 3.20 × 3.20 mm ePad
    and 0.20 × 0.875 mm pads between a 6.00 mm inner and a 7.75 mm outer span, 5.40 mm along
    each side. (Its 1.175 mm is the corner distance from the last pad to the outer span, not a
    pad length; this line said 1.175 mm pads until 2026-11-04, issue #6 P1.)
  - *Footprint (issue #6 P1, G20):* `RP2040_QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm`, generated
    from those numbers and checked against them pad by pad (`design/ecad/libraries/`). KiCad
    9.0.8's stock QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm has the same copper.
  - Supplies (Table 634): IOVDD, VREG_VIN and ADC_AVDD 1.62–3.63 V; USB_VDD 3.135–3.63 V;
    DVDD 1.05–1.16 V. The on-chip linear core regulator gives 1.1 V at power-on and supplies up
    to 100 mA; it needs 1 µF close to VREG_VIN and to VREG_VOUT. 100 nF close to each IOVDD,
    DVDD, USB_VDD and ADC_AVDD pin.
  - DVDD current (Table 637, typical / maximum): BOOTSEL active 9.4 / 14.7 mA; the Popcorn
    demo 10.9 / 16.6 mA.
  - USB: 27 Ω series termination on each of USB_DP and USB_DM, close to the chip; pull-ups and
    pull-downs on chip. No tolerance is stated for the 27 Ω.
  - Crystal: the USB bootloader needs 12 MHz; the XOSC tolerates up to 1000 ppm. Recommended
    ABM8-272-T3 (C<sub>L</sub> 10 pF, ESR 50 Ω max, drive 200 µW max), with 2 × 15 pF and
    1 kΩ in XOUT in the reference design, which warns that another crystal must be tested.
  - Boot: QSPI_SS held low at reset selects the USB bootloader; the reference uses 1 kΩ to the
    button, close to the flash, and leaves the 10 kΩ pull-up unfitted (the pad resets pulled
    up). RUN has an internal pull-up and is tied high when unused; TESTEN goes to GND.
  - GPIO: every GPIO pad resets with its pull-down on (PADS_BANK0 PDE = 1, PUE = 0); pull-up
    and pull-down 50–80 kΩ; pins are not rated above IOVDD + 0.5 V. GPOUT0–3 are on GPIO21,
    23, 24 and 25.
  - *To confirm on the first board (V-MEAS-06):* DVDD, the USB series resistance, Y1's start-up
    and frequency; before layout, the land against Figure 167 (Rev0.7 G20).
- *Verified (C2765186, SHOU HAN drawing "TYPE-C 16PIN 2MD(073)" REV. A and its specification,
  as LCSC lists them for C2765186; read 2026-11-12 for D37):*
  - JLCPCB's assembly pool: class Extended (not Preferred), 1,070,668 in stock, $0.0728 each
    at 1–199 pieces, attrition 3, minimum 2 (`tools/jlc_stock.py` and the API's price tiers,
    2026-11-12). Its part page lists it as eligible for Economic PCBA.
  - SMD receptacle with 16 contacts, body 8.94 × 7.35 × 3.16 mm: 12 pads at 0.5 mm pitch
    (A1/B12, A4/B9, B4/A9 and B1/A12 are GND, VBUS, VBUS and GND, 0.60 mm wide; B8 SBU2,
    A5 CC1, B7 DN2, A6 DP1, A7 DN1, B6 DP2, A8 SBU1 and B5 CC2 are 0.30 mm wide), four plated
    shell slots (the shield, NOTE 4-2) and two unplated pegs, ø0.65 mm. The drawing's pad row
    reads B7, A6, A7, B6 from left to right: D−, D+, D−, D+ alternate, so joining A6 to B6
    and A7 to B7 needs one crossing (ROUTING_Rev0.7.md).
  - Rating 5 V, 3 A, −25 to +85 °C. Insertion force 0.5–2.0 kgf, removal 0.8–2.0 kgf,
    10,000 cycles (after them: contact resistance ≤ 0.1 Ω, removal 0.8–2.0 kgf). Contact
    resistance (LLCR) 40 mΩ per pin at most for VBUS, GND and the other pins, 50 mΩ for the
    shield, change ≤ 10 mΩ. J4 carries up to 2.46 A (circuit §7.2) through two VBUS pads, inside
    the 3 A rating.
  - IR reflow: the board at 260 °C held for 10 s (drawing note 6); the specification's
    soldering-heat test says 260 ± 5 °C within 20 s. Hand-soldering iron: 330 ± 5 °C, 3 ± 0.5 s.
  - *Footprint (issue #8, D37):* `USB_C_Receptacle_SHOUHAN_TYPE-C-16PIN-2MD-073`, generated from
    the drawing's recommended land and measured against it by `check_libraries.py`
    (`design/ecad/libraries/library.json`). A1 and B1 are 0.035 mm shorter at their near end
    than the drawing: it leaves 0.165 mm from each peg hole to them, under JLCPCB's 0.20 mm
    non-plated-hole-to-copper figure (the user's choice of 2026-11-12, D37).
  - *To confirm on the first board:* the drawing's land is for a **0.80 mm** board and this one
    is 1.6 mm, so the shell legs may not reach through the slots (V-MFG-03); the part's
    orientation in JLCPCB's placement preview, which is read when the JLCPCB step is run
    (V-MFG-03); and that the enclosure opening carries the insertion force, which now
    reaches the board through the four shell slots (V-MECH-01).
- *Verified (CH335F, WCH CH334/CH335 datasheet V2.5, Akizuki copy; read 2026-11-04 for D31):*
  - Package (§5.6, QFN28_4×4×0.75-0.4, read visually): body 4.0 ± 0.1 mm, height
    0.75 ± 0.05 mm, pitch 0.4 mm; terminals 0.20 ± 0.05 mm wide and 0.35 ± 0.1 mm long; ePad
    2.7 ± 0.2 mm square with a chamfer at the pin 1 corner. The ePad is pin 0, GND
    (Table 1-3).
  - Pins (Table 1-3): 1 LED1/PSELF, 2 PWREN2#, 3 LED2/PGANG, 4 PWREN1#, 5 PWREN4#/SUSP,
    6 DM1, 7 DP1, 8 DM2, 9 DP2, 10 PWREN3#, 11 XI, 12 XO, 13 DM3, 14 DP3, 15 DM4, 16 DP4,
    17 RESET#/CDP, 18 OVCUR4#, 19 OVCUR3#, 20 DMU, 21 DPU, 22 LED3/SCL, 23 OVCUR2#,
    24 OVCUR1#, 25 LED4/SDA, 26 V5, 27 GND, 28 VDD33.
  - Supply (§4.1, §4.2): V5 4.5–5.25 V with the internal LDO, absolute maximum 5.5 V;
    VDD33 3.2–3.5 V from the LDO, which can supply 20 mA to outside loads. V5 needs ≥ 1 µF;
    VDD33 0.1 µF + 10 µF, or 1 µF (Table 1-3). Operating current 85 mA typical with HS
    upstream and 4 HS downstream, 25 mA with 4 FS downstream.
  - Clock: a 12 MHz crystal on XI/XO, load capacitors on chip (Features list).
  - USB: 1.5 kΩ upstream pull-up and the downstream ports' pull-downs on chip (Features list),
    so an unused port's DM/DP pins need nothing.
  - RESET#/CDP: internal pull-up of about 25 kΩ and a power-on reset (§3.2). Left undriven at
    power-up it enables no CDP (Table 3-2); the datasheet recommends leaving it unconnected
    when no external reset is needed.
  - Straps: LED1/PSELF and LED2/PGANG have internal pull-ups; undriven, the hub is
    self-powered and in GANG mode (Table 1-3, §3.3). Without an EEPROM the internal
    configuration holds: 4 ports, MaxPower 32h (100 mA), SELF_POWER 1 (§3.5).
  - OVCUR1–4#: with the default OC_LEVEL = 0, a 2.4 V threshold and a weak internal pull-up,
    24 µA (§3.1, §4.2). PWREN1–4# are outputs.
  - ESD: 6 kV HBM on the USB signal pins (§4.1). −40 to 85 °C. No thermal resistance is
    given.
  - *Land (Rev0.7 G21, issue #6 P1):* §5.6 gives the package only (body 4.0 ± 0.1 mm,
    terminal 0.20 ± 0.05 × 0.35 ± 0.1 mm, ePad 2.7 ± 0.2 mm), no land. The footprint
    `CH335F_QFN-28-1EP_4x4mm_P0.4mm_EP2.7x2.7mm` has 0.80 × 0.20 mm pads centred 1.95 mm out,
    covering each nominal terminal and reaching 0.35 mm past the nominal body edge (0.30 mm
    past the maximum), and a
    2.7 mm ePad, 0.20 mm from the pads; the check measures it against §5.6.
  - *To confirm on the first boards:* U6's joints on leaded HASL (V-MFG-03); Y2 against the
    built-in load capacitors (G9).
- *Verified (W25Q128JVSIQ, Winbond W25Q128JV Rev. J, 2024-04-25, via LCSC C97521, read
  2026-11-04):* 2.7–3.6 V; SOIC-8 208 mil (body 5.18–5.38 mm, lead span 7.70–8.10 mm, height
  ≤ 2.16 mm); the -IQ part has QE fixed to 1; a factory-set 64-bit unique ID read by 4Bh;
  JEDEC ID (9Fh) EFh 4018h; Read Data (03h) up to 50 MHz.
  - *To confirm on the first board (V-MEAS-06):* the JEDEC ID and that two boards' unique IDs
    differ.
- *Verified (OP07C, TI SLOS099F, January 2014; re-read 2026-11-04):*
  - V<sub>OS</sub> 60 µV typ, **no maximum given for the C grade** (OP07D max 150 µV is used
    as the planning bound); drift 0.5 µV/°C typ.
  - I<sub>B</sub> ±1.8 nA typ; noise 10.5 nV/√Hz.
  - Supply ±3 to ±18 V (≥ 6 V total); common mode ±13 V min at ±15 V; output ±12 V into
    10 kΩ at ±15 V.
  - GBW 0.4 min / 0.6 typ MHz; slew 0.3 V/µs.
  - *Desk check (D28; TI SLOS099F, January 2014, via LCSC C7433, fetched 2026-11-04):* the large-signal gain
    row is specified on a single 15 V supply, V<sub>O</sub> = 1.4 V to 11.4 V,
    R<sub>L</sub> ≥ 500 kΩ: A<sub>VD</sub> ≥ 100 V/mV (OP07C, 25 °C). The supply-sensitivity
    row runs from ±3 V. Rev0.7 §3.2 uses 1.4 V as the output low limit and the ±15 V common
    mode range, read rail-relative, for the inputs.
  - *To confirm on the first board (V-MEAS-00):* the gate headroom at 1 A and loop stability.
- *Verified (LM393):*
  - 1.3 µs response at 5 mV overdrive, 300 ns large-signal.
  - Supply 2–36 V; common mode 0 to V<sub>CC</sub> − 1.5 V; V<sub>OS</sub> ±5 mV max.
  - Open-collector output, sink ≥ 6 mA (16 typ).
  - *D34 (onsemi LM393/D Rev. 25, April 2014, via LCSC C7955, fetched 2026-11-04):* note 1:
    below a 36 V supply, an input's absolute maximum equals the supply voltage, so the LM393s
    run from V12F (Rev0.7 §3.2). Common mode 0 to V<sub>CC</sub> − 1.5 V at 25 °C,
    V<sub>CC</sub> − 2.0 V over temperature. V<sub>IO</sub> ±5 / ±9 mV max, I<sub>IB</sub>
    250 / 400 nA max (25 °C / over temperature). I<sub>CC</sub> 0.4 typ / 1.0 max mA for both
    comparators at 25 °C, 2.5 mA max at V<sub>CC</sub> = 30 V. Output leakage 0.1 nA typ at
    V<sub>O</sub> = 5 V, 25 °C; 1 µA max at V<sub>O</sub> = 30 V over temperature.
  - *To confirm on the first board:* the comparators' power-up with TH_REF ahead of V12F
    (V-MEAS-00), and the OFF bypass gates' leakage (V-MEAS-01).
- *Verified (AO3401A):*
  - R<sub>DS(on)</sub> 47 / 60 mΩ at −4.5 V, 60 / 85 mΩ at −2.5 V.
  - V<sub>GS(th)</sub> −0.5 / −0.9 / −1.3 V at −250 µA; Q<sub>g</sub> 7 nC at 4.5 V;
    C<sub>iss</sub> 645 pF, C<sub>oss</sub> 80 pF, C<sub>rss</sub> 55 pF;
    I<sub>GSS</sub> ±100 nA at ±12 V (AOS Rev 3.1, December 2023, fetched 2026-11-04).
  - −30 V; V<sub>GS</sub> ±12 V; I<sub>D</sub> −4 A.
  - *To confirm on the first board (V-MEAS-00):* the HIGH mirror loop into this gate (C<sub>iss</sub>,
    and C<sub>rss</sub> multiplied by the drain node) is stable; the datasheet does not settle it.
  - *D35 (the same sheet via LCSC C15127, fetched 2026-11-04, read from its graphs):* Figure 10,
    single-pulse power junction-to-ambient, about 25 W at 10 ms; Figure 4, R<sub>DS(on)</sub>
    × 1.23 at 70 °C; Figure 7, the gate-charge plateau near −2 V at −4 A. Q53, the J1 soft
    start, takes ≤ 2.26 W for ≤ 6.7 ms (Rev0.7 §3.1). *To confirm:* V-PWR-03.
- *Verified (2N7002, JSCJ / JCET datasheet, September 2016, via LCSC C8545, fetched 2026-11-04):*
  V<sub>th(GS)</sub> 1.0 min / 2.5 max V at 250 µA. Rev0.7 §3.2's reset hold gives its gate
  ≥ 2.70 V. *D34 (the same sheet, page 2):* I<sub>DSS</sub> 80 nA max at V<sub>DS</sub> = 60 V;
  I<sub>GSS</sub> ±80 nA at ±20 V; C<sub>iss</sub> 50 pF max.
  - *To confirm on the first board (V-MEAS-06):* the HOLD gates (Q19, Q20, Q39, Q40) stay
    ≥ 2.5 V with blank flash and with RUN held low.
- *Verified (AO3400A):* R<sub>DS(on)</sub> 19 / 32 mΩ at 4.5 V; V<sub>GS(th)</sub> 0.65 / 1.05 /
  1.45 V. *D34 (via LCSC C20917, fetched 2026-11-04):* C<sub>iss</sub> 630 pF typ, Q<sub>g</sub>
  6 / 7 nC at 4.5 V. That gate on DIS_x directly took 10.0 µs to reach 2.5 V, so it sits
  behind 100 kΩ (DISG_x, Rev0.7 §3.4).
- *Verified (S9012, JSCJ, via LCSC C8543, fetched 2026-11-04; D34):* PNP, I<sub>C</sub> −500 mA,
  V<sub>CEO</sub> −30 V (LCSC listing). h<sub>FE</sub> 120–400 at V<sub>CE</sub> = −1 V,
  I<sub>C</sub> = −50 mA, in ranks L 120–200, H 200–350, J 300–400. C8543 is listed by LCSC
  as "S9012 2T1(RANGE:200-350)", rank H; Rev0.7 §3.4 uses 200–350. *To confirm:* the rank
  marking on the reel.
- *Verified (LEDs, D34):* KT-0805G (C2297) V<sub>F</sub> 2.6–3.1 V at 5 mA, the only
  V<sub>F</sub> figure on its sheet; NCD0805R1 (C84256) V<sub>F</sub> 1.5–2.6 V at 20 mA. At
  510 Ω from a 3.3 V GPIO, the green's current is not guaranteed (Rev0.7 §6.4). *To confirm:*
  V-HOST-01.
- *Verified (AMS1117):*
  - Dropout 1.1 / 1.3 V at 800 mA; 90 °C/W.
  - Minimum load 5 / 10 mA; I<sub>q</sub> 5 / 11 mA; output 3.251–3.349 V.
  - *To confirm:* the output-capacitor stability requirement (capacitance and ESR range) in
    the datasheet, against the 22 µF ceramic on V3V3.
- *Verified (CJ431):*
  - SOT-23 pins: 1 REF, 2 K, 3 A (page 1). That is KiCad's `TL432DBZ` order; KiCad's
    `TL431DBZ` (and JSCJ's own CD431) is 1 K, 2 REF, so the symbol is built on TL432DBZ
    (issue #6 P1).
  - 2.475 / 2.5 / 2.525 V; catalogue lists the ±0.5 % rank.
  - I<sub>K(min)</sub> 0.45 / 1 mA.
  - Deviation over −25 to 85 °C: 4.5 typ / 17 max mV.
  - *D34:* I<sub>ref</sub> ≤ 4 µA, plus ≤ 1.2 µA over temperature, in the V_INJ divider's
    spread. The sheet's text states no load-capacitance limit, and neither CJ431 has a
    capacitor (Rev0.7 §4.1). *To confirm:* V-MEAS-00.
- *Verified (SMBJ6.5CA):* V<sub>RWM</sub> 6.5 V, V<sub>BR</sub> 7.22–7.98 V, clamp 11.2 V,
  I<sub>R</sub> 500 µA max. It sits only on non-measured rails (J1, J4 VBUS) because of that
  leakage.
- *Verified (C9002):* 12 MHz, C<sub>L</sub> 20 pF, ±10 ppm / ±20 ppm, ESR 80 Ω. *D29 (YXC
  YSX321SL sheet, scanned image, read 2026-11-04):* ESR 80 Ω max for 12–15 MHz; drive
  10–200 µW (100 µW typical); C0 3 pF max; ageing ±3 ppm/year; 3.20 × 2.50 × 0.70 mm. No
  motional capacitance is given.
  - *To confirm (G9):* Y2 against the CH335F's built-in load capacitors.
  - *To confirm (V-MEAS-06):* Y1 on the RP2040 XOSC at ≈ 10.5 pF load: start-up and
    frequency (Rev0.7 §6.3). Fallback: ABM8-272-T3 (C20625731, Extended, 7,921 on 2026-11-04,
    the same SMD3225-4P land), which would be a third Extended part (after D29 and D31)
    and needs the user's decision.

### Passives (Basic, by value)

Each Use is the binding in `design/circuit/CIRCUIT_DESIGN_Rev0.7_netlist.md` (D34, issue #6
P2), which lists every reference; counts are for both channels. The tolerance and TCR are
the MPN's, from UNI-ROYAL's code: in `0402WGF100JTCE` the `F` is ±1 % and the `J` in `100J`
is the decimal multiplier (10 Ω), not ±5 %. LCSC's listing parameters disagreed with the MPN
for some rows and were not used.

| Value | Use | LCSC | Package | Stock | Note |
|---|---|---|---|---:|---|
| 510 Ω ±1 % ±100 ppm | R_L shunt (×2, Kelvin land); U3 CJ431 feed from V3V3; TH_REF divider bottom, part 2; LED resistors (×4) | C17734 | 0805 | 2,198,725 | 0.125 W; stuck-LOW 47 mW |
| 100 Ω ±1 % ±100 ppm | Mirror R1 (×6) | C25076 | 0402 | 6,307,501 | — |
| 1.5 kΩ ±1 % ±100 ppm | R_OUT LOW, MID (×4); U4 feed; SCLK/CS/DIN pull-ups to V5L (×3) | C25867 | 0402 | 1,516,858 | — |
| 2.4 kΩ ±1 % ±100 ppm | R_OUT HIGH (×2) | C22940 | 0603 | 1,117,935 | — |
| 22 Ω ±1 % ±100 ppm † | USB D± series, part 1 of 27 Ω (×2) | C25092 | 0402 | 2,697,334 | No 27 Ω is Basic (C25100 is Extended) |
| 5.1 Ω ±1 % ±200 ppm † | USB D± series, part 2 of 27 Ω (×2) | C25197 | 0603 | 131,418 | No 0402 5.1 Ω is Basic; 22 + 5.1 = 27.1 Ω, 26.83–27.37 Ω |
| 10 kΩ ±1 % ±100 ppm | +IN guard (×6), EN series (×2), DIS pull-up (×2), HOLD pull-ups (×4), DOUT divider top (×2), U1 RUN pull-up † | C25744 | 0402 | 16,208,659 | — |
| 15 kΩ ±1 % ±100 ppm | U4 divider (33 k / 15 k → 8.0 V); V_J4 divider bottom; DOUT divider bottom (×2); comparator thresholds CMP_L, CMP_M, CMP_OC (×6) | C25756 | 0402 | 2,494,056 | — |
| 33 kΩ ±1 % ±100 ppm | Rp (×4); U4 divider; V_J4 divider top (5.5 V → 1.72 V); Q53 gate pull-down (D35) | C25779 | 0402 | 2,369,774 | No 36 kΩ is Basic |
| 5.1 kΩ ±1 % ±100 ppm | Rd on J1, J4 CC (×4); TH_REF divider bottom, part 1; R_B, Q16 base (×2) | C25905 | 0402 | 4,938,551 | — |
| 100 kΩ ±1 % ±100 ppm | R_on (×2); EN_G pull-down (×2); OC_x sense of EN_G (×2); DISG, Q13 gate series (×2); R_BE (×2); event series (×4) | C25741 | 0402 | 7,841,979 | — |
| 1 MΩ ±1 % ±100 ppm | R_GS, port switch off (×2); bypass gate return (×4); pedestal R_INJ (×6) | C26083 | 0402 | 2,794,209 | — |
| 1 kΩ ±1 % ±100 ppm | ADC series (×10); gate resistors (×6); discharge load (×2); TH_REF divider top; Y1 XOUT, BOOTSEL (QSPI_SS to SW3) † | C11702 | 0402 | 21,568,761 | — |
| 10 Ω ±1 % ±200 ppm | V12 filter; V5A filter | C25077 | 0402 | 3,068,120 | Not in a measured path |
| 330 pF C0G | C_N on R_OUT LOW, MID (×4) | C1664 | 0603 | 691,081 | — |
| 220 pF X7R | C_N on R_OUT HIGH (×2); comparator hysteresis divider (×6) | C1530 | 0402 | 1,340,537 | No Basic C0G 220 pF found |
| 10 µF 25 V X5R | Port capacitor (×2); VDDA; V5A; U2 input; V3V3 at U1 †; U6 VDD33 ‡ | C15850 | 0805 | 7,996,245 | Effective ≈ 7 µF at 5 V DC bias; bandwidth figures assume 10 µF |
| 22 µF 25 V | VBUS_IN bulk; V12F filter (2 ×); V3V3 (AMS1117 output) | C45783 | 0805 | 3,579,516 | — |
| 100 nF 50 V | All decoupling (one rating for every rail), 25 in all: U1's 10 power pins and U8 †, U6 VDD33 ‡, U7, U17, U30, and each channel's U10–U13; and Q53's Miller capacitor (D35) | C307331 | 0402 | 20,893,452 | — |
| 1 µF 25 V | U5 MAU104 input and output; TH_REF filter; U1 VREG_VIN and VREG_VOUT †; U6 V5 ‡; Q53 gate hold (×2, D35) | C52923 | 0402 | 10,715,829 | — |
| 15 pF C0G ±5 % 50 V † | Y1 load (×2); comparator hysteresis, output to +IN (×6) | C1548 | 0402 | 1,311,598 | As Raspberry Pi's reference |
| 10 nF | C_M, soft-start Miller, 2 × 10 nF per port (×4) | C15195 | 0402 | 5,868,443 | — |

**Removed in Rev0.4 (D22):**

| Was | MPN | LCSC | Class | Now |
|---|---|---|---|---|
| U1 | STM32F103C8T6 | C8734 | Preferred Extended | PGA2040 (Akizuki); since D29 the bare RP2040 |
| D1–D3 | SRV05-4 | C7420376 | Preferred Extended | PSM712 on CC; D± unprotected |
| Y1 load capacitors | 33 pF C0G | C1562 | Basic | Not needed then: Y1 was gone. D29 restored Y1 with 15 pF (C1548) |

**Removed in Rev0.4 (D29, 2026-11-04):**

| Was | Part | Code | Class | Now |
|---|---|---|---|---|
| U1 | PGA2040 RP2040 module (Pimoroni), hand-soldered | Akizuki g116762 | Akizuki | Bare RP2040 C2040 (Extended, the D29 exception), with U8, Y1 and passives machine-placed |

**Removed in Rev0.4 (D31, 2026-11-04):**

| Was | Part | Code | Class | Now |
|---|---|---|---|---|
| U6 | AE-QFN28-DIP(CH335F) USB hub module, hand-soldered | Akizuki g129556 | Akizuki | Bare CH335F C5137013 (Extended, the D31 exception), with its 1 µF, 100 nF and 10 µF machine-placed |

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

## Symbols and footprints (issue #6 P1, 2026-11-04)

`design/ecad/libraries/library.json` is the per-part record of pin names and land facts,
each with the datasheet page it was read from. `check_libraries.py` measures the KiCad
library against it (`design/ecad/libraries/README.md`). Facts that rest on less than the
part's own drawing, and so stay open:

- **AMS1117-3.3 (U2):** the SOT-223 tab is taken as VOUT (pin 2). The AMS sheet says "TAB IS
  OUTPUT" only for TO-252. *To confirm:* continuity tab–pin 2 on a received part.
- **AO3401A, AO3400A:** the AOS sheets give neither a package drawing nor pin numbers. The
  pin order (1 G, 2 S, 3 D) comes from their top view, and the land check uses the JSCJ SOT-23
  dimensions as a proxy.
- **NCD0805R1 (D11, D13):** the sheet never names the terminals. The green-marked terminal
  is read as the cathode. *To confirm:* in the JLCPCB placement preview (CLAUDE.md §4.2).
- **BLM18PG121SN1D (FB1):** the catalog excerpt has only the BLM18A drawing; the 1.6 × 0.8 mm
  body is the same size code.
- **TSL1TTER100D (RS10, RS20):** KOA gives no land, so the 4-pad Kelvin land is derived from
  the body and electrode dimensions: each end is split across its width into a 1.85 mm force
  pad and a 0.60 mm sense pad, 0.25 mm apart, reaching 0.45 mm past the maximum body end. The
  force and sense pads are joined only through the part's electrode. *To confirm:* the joints
  on the first board, and the HIGH-range gain against the reference in V-MEAS-01.
- **Mounting holes (H1–H4):** KiCad's M2 hole with an ISO 7380 button-head courtyard
  (3.5 mm), a provisional choice: the screw and the heat-set insert are not chosen (OI-5).
  *To confirm:* V-MECH-01.
- **Passives:** the R and C footprints are KiCad's IPC-7351 nominal 0402 / 0603 / 0805. Each
  value's own sheet was read when it was bound in the schematic (P2, D34): its body
  dimensions are in the Passives table above, and `check_schematic.py` checks each body
  against its land. That includes R_L's 510 Ω (C17734) on its Kelvin land.

---

## Rev0.2 candidates rejected by D13

All Extended. The full Rev0.2 rows, with stock and datasheet notes, are in Git history
(commit `4e59607`).

| Function | Rev0.2 candidate(s) | Replaced by |
|---|---|---|
| PD sink | CH224Q / CH224A / CH224K | J4 power-only input (D14) |
| Buck / buck-boost | TPS62130, TPS62933, TPS63070 class | None needed |
| 3.3 V regulators | TPS7A20 class, SY8089 class | AMS1117-3.3 |
| MCU + flash | RP2040 + W25Q | Again RP2040 (C2040, D29) + W25Q128JVSIQ; Rev0.3 had STM32F103C8T6, Rev0.4 first the PGA2040 module |
| USB hub + 24 MHz crystal | USB2514B variants + X322524MOB4SI | CH335F (C5137013, D31; the Akizuki module until then) + C9002 |
| ADC | ADS131M02 / M04 / M06 | 2 × MCP3208 (Akizuki); Rev0.3 had the STM32 ADC |
| Current-sense amplifier | INA190A2 | OP07CDR + AO3401A mirror |
| Sense mux | TMUX6209, ADG1209, TMUX1109 | Not needed (topology C) |
| Window comparator | TLV3202, TLV3502 | LM393DR2G |
| Bypass FET | CSD25402Q3A | AO3401A |
| Shunts | WSK2512 (20 mΩ, 10 mΩ, 2 Ω), RT0805 200 Ω | TSL1TTER100D, MFU100F10RB (Akizuki), 510 Ω C17734 |
| Load switch | SY6280AAC, TPS2553, TPS25947 | Back-to-back AO3401A |
| ESD | TPD4E05U06, USBLC6-2SC6 | PSM712 on CC only; D± unprotected (D22). Rev0.3 had SRV05-4 |

## Not yet selected

- ~~**Pin headers and sockets for the modules and the DIP16 ADCs (OI-23).**~~ Selected by
  D33: PH-1x40SG (g100167) under the USB-C modules, no sockets, and the DIP16 ADCs soldered
  directly. Since D37 the modules and their headers are gone; the DIP16 ADCs are still
  soldered directly (see the hand-soldered parts above).
- **Heat-set M2 inserts** (mechanical; not under D13).
