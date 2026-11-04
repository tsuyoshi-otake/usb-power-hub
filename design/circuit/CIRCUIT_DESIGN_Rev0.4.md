# USB Power-Control Hub — Circuit Design Rev0.4

**State: WIP — MANUFACTURING PROHIBITED**
Date opened: 2026-08-16 (Rev0.1). Revised: 2026-11-03 (Rev0.2, Rev0.3 and Rev0.4, all the same day).
Amended 2026-11-04 (D28: the pre-layout bench is replaced by desk checks, §12; D29: the
PGA2040 module is replaced by a bare RP2040 that JLCPCB places, §6.5; D30: leaded HASL
instead of ENIG, §10; D31: the CH335F module is replaced by the bare chip, which JLCPCB
places, §6.6).

This document *is* the schematic at this stage. KiCad capture transcribes what is settled
here; it is not where the design happens (CLAUDE.md Section 2). Nothing in this file has been
built or measured. Every part number below is a *candidate* until `requirements/parts.md`
records it as confirmed against the actual PCBA order.

Read this with CLAUDE.md Section 11 (Open Issues) open. Companion documents:
`requirements/product.md` (what the product must do — authority), `requirements/verification.md`
(how each requirement is proven), `requirements/parts.md` (candidates, stock, datasheet facts).

**What Rev0.3 and Rev0.4 are.** On 2026-11-03 the user set a sourcing rule (D13) and delegated the open
design choices to Claude's recommendation:

> 推奨で任せるよ、JLCPCBでExtendedでしか製造できないPCBAにはしないでね

and, in a following message:

> 秋月で購入できるパーツに限って
> JLCPCBでExtendedは無しLSCSパーツで在庫があるやつか、秋月で在庫があるやつ。小さいパーツは実装大変なのでPCBA前提で、デカくいパーツだけね

Later the same day the user restated the rule as a list:

> 【部品選定・実装ルール】
> ・実装はJLCPCB。部品はBasic Partsのみ
> ・PCBAに載せる部品はLCSCで豊富な在庫があるもの
> ・手はんだ部品は秋月電子で在庫があるもの
> ・小さい部品はPCBAに任せること
> ・特殊な部品や調達しにくい部品は極力避ける
> ・パーツの種類や点数は減らすこと

"Basic Parts only" read against the two Preferred Extended parts in Rev0.3 (STM32F103C8T6
and SRV05-4), so OI-30 was put to the user again. The user answered:

> うん、okだよ

and, asked to choose between keeping the two parts and removing them, selected
「外して Basic のみにする」 (remove them; Basic parts only). That is D22. **Rev0.4 is that
redesign:** the MCU becomes an Akizuki RP2040 module with two Akizuki DIP ADCs (D23), and
the D+/D− lines of J1–J3 lose their ESD array.

**D29 (2026-11-04).** The user asked about the module's price:

> このPGAてさ生のRP2040より高くない?

After a review of the alternatives (issue #3), the user accepted a larger change,

> いいよ、大きな設計変更になってもいいよ

and, asked which MCU to redesign with, selected 「素の RP2040 (推奨)」 (the bare RP2040). The
RP2040 (C2040) is now machine-placed by JLCPCB with its flash, crystal and passives (§6.5).
It was the board's first Extended part, an exception to D22 that the user made.

**D31 (2026-11-04).** Asked what to buy from Akizuki, the user asked about the hub:

> ええ、CH335FはLCSCに在庫無いの?

and, while the answer was being written,

> こんなモジュール実装するのデカくない?

Offered the bare chip against the Akizuki module, the user selected 「IC 単体にする (推奨)」
(the bare chip). The CH335F (C5137013, QFN-28 4 × 4 mm) is now machine-placed by JLCPCB with
its crystal and capacitors (§6.6). It is the second Extended part, the user's second
exception to D22; D22 otherwise stands.

Most of the Rev0.2 design needed Extended parts: RP2040, CH224Q, USB2514B, ADS131M02, INA190,
the TMUX mux, the 4-terminal shunt, and the TPD4E05 ESD array. Rev0.3 therefore redesigns the
board from the parts that D13 allows. Where no allowed part can do a job, the function is
reduced, and Section 7.4 and `requirements/product.md` §9 say what was lost.

Decisions made under the delegation are recorded in Section 10 as **"Claude (delegated)"**.
They are decisions, because the user handed them over, but the user can revert any one of
them; each row names what reverting it would reopen. Rev0.4 has no Preferred Extended part.
Every machine-placed part is JLCPCB Basic (D22, Section 9) except two Extended parts, each an
exception the user made: the RP2040 (C2040, D29) and the CH335F (C5137013, D31).

---

## 1. Sources of Fact

| # | Fact | Source | Confidence |
|---|---|---|---|
| 1 | Product is a *measurement instrument* that also happens to be a hub | User, 2026-08-16 | Settled |
| 2 | ~~Upstream power is USB-PD sink~~ | User decision, 2026-08-16 (D1) | **Superseded** by D13 → D14: CH224x is Extended |
| 3 | ECAD tool is KiCad | User decision, 2026-08-16 (D2) | Settled |
| 4 | Measurement range target 0.1 µA – 1 A | User request, 2026-08-16 | Settled as a *target*; Section 4 |
| 5 | Upstream must enumerate as a COM port and be controllable from it | User request, 2026-08-16 | Settled |
| 6 | ~~STM32F103 USB is Full-Speed (12 Mbps) device only~~ | DS5319 Rev 18 | **Superseded** by D22 → D23: the MCU is now an RP2040 (fact 15) |
| 7 | ~~Board outline 60 × 24 mm~~ | `mockup/board-model.js` | **Superseded by fact 9** |
| 8 | All designators/values in `mockup/` are placeholders | CLAUDE.md §0 | Settled |
| 9 | ~~Board outline 85 × 35 mm~~, 4 layers | User decision, 2026-11-03 (D10) | 4 layers settled; **outline superseded by fact 17** (D24) |
| 10 | ~~USB hub is USB2514B~~ | User decision, 2026-11-03 (D11) | **Superseded** by D13 → D15: every USB2514B variant is Extended |
| 11 | Part parameters quoted here | Manufacturer datasheets fetched 2026-11-03 and 2026-11-04 (the D28 desk checks, D29 and D31), cited per part in `requirements/parts.md` | High for the parameters cited; nothing else about those parts is confirmed |
| 12 | Sourcing rule: JLCPCB **Basic** parts in assembly stock for machine-placed parts; **Akizuki** parts in stock for large hand-soldered parts; no Extended-only PCBA | User decision, 2026-11-03 (D13) | Settled |
| 13 | JLCPCB Basic holds 351 parts: 182 resistors, 88 MLCCs, 81 others. None of the 81 is a microcontroller, a USB hub, a USB-C receptacle, a USB D± ESD array, a current-sense amplifier, a multi-channel ADC or a fuse | JLCPCB assembly-parts list, 2026-11-03 (`requirements/parts.md`) | High as of that date |
| 14 | Akizuki stock, part numbers and specifications | akizukidenshi.com product pages, 2026-11-03 | High as of that date; stock changes daily |
| 15 | RP2040 (C2040, LQFN-56 7 × 7 mm, 0.4 mm pitch, reduced 3.20 mm ePad): USB 1.1 Full-Speed device with on-chip PHY and D+ pull-up, 4 KB USB packet memory, 30 GPIO with per-pin edge interrupts, PIO, ROM USB bootloader (needs a 12 MHz crystal), on-chip 1.1 V core regulator (100 mA). Its support circuit follows Raspberry Pi's minimal design (§6.5). Until D29 the MCU was the PGA2040 module (D23; its facts are in Git at commit `6774bc5`) | RP2040 datasheet (build 2025-02-20); "Hardware design with RP2040" (Release 2, 2026); Winbond W25Q128JV Rev. J (2024-04-25); YXC YSX321SL sheet for C9002 | High for the parameters cited (D29 desk check). A built board confirms the support circuit (V-MEAS-06) |
| 16 | MCP3208-CI/P: 12-bit, 8 ch, SPI; INL ±2 LSB max (C grade); f<sub>CLK</sub> 1 MHz at V<sub>DD</sub> 2.7 V, 2 MHz at 5 V; sample phase 1.5 clocks through a 1 kΩ switch onto 20 pF; inputs rated −0.6 V to V<sub>DD</sub> + 0.6 V, no input-current rating; the clock need not be constant as long as each timing limit is met | Microchip DS21298E, fetched 2026-11-03 | High |
| 17 | Board outline 100 × 72 mm, 4 layers | D24, 2026-11-03: the user's condition 「100x100未満ならいいんだっけ」 (stay within 100 × 100 mm), size chosen by Claude from the OI-23 study | Settled; block placement checked, routing not |
| 18 | JLCPCB stackup JLC04161H-7628 (1 oz outer, 7628 prepreg 0.2104 mm, Dk 4.4); the only named 4-layer stackup on the quote page without the special-stackup note. JLCPCB's calculator gives 14.85 mil for 50 Ω single-ended on L1 without mask; its differential calculation returned no result | `jlcpcb.com/impedance` (curl) and the quote page and impedance calculator (browser), 2026-11-03; D27 | High for the stackup data and the single-ended datum. The 90 Ω pair width is a model value, provisional until JLCPCB's differential calculator is rerun |
| 19 | CH335F (C5137013, QFN28 4 × 4 × 0.75 mm, 0.4 mm pitch, 2.7 mm ePad = GND): USB 2.0 High-Speed hub (MTT), 4 downstream ports; V5 4.5–5.25 V through an internal LDO to VDD33 (3.2–3.5 V, 20 mA available outside); 85 mA typical with HS upstream and 4 HS ports; 12 MHz crystal with on-chip load capacitors; on-chip 1.5 kΩ upstream pull-up, downstream pull-downs and power-on reset; 6 kV HBM on the USB pins. Until D31 it came on the Akizuki AE-QFN28-DIP module (its record is at Git commit `3e11f68`) | WCH CH334/CH335 datasheet V2.5 (Akizuki's copy), read 2026-11-04; pin table, §4.1–§4.2, §5.6 package drawing | High for the parameters cited (D31 desk check). A built board confirms them (V-MFG-03, V-HOST-01) |

Everything else below is derived by calculation in this document, or is explicitly marked OPEN.
The arithmetic is reproduced by `CIRCUIT_DESIGN_Rev0.4_calc.py` beside this file
(`python design/circuit/CIRCUIT_DESIGN_Rev0.4_calc.py`); change a value there and here together.

---

## 2. What Rev0.3 and Rev0.4 change versus Rev0.2

A row that names only one design is the same in Rev0.3 and Rev0.4.

| Rev0.2 had | Rev0.3 / Rev0.4 has | Why |
|---|---|---|
| USB-PD sink (CH224Q) on J1, 9 V, buck to 5.10 V | **J4, a power-only 5 V USB-C input** for port power; J1 carries data and logic power only. No PD, no buck | CH224x and every buck candidate are Extended (D13). This also removes OI-17: port power no longer depends on what the host PC can grant |
| RP2040 + QSPI flash | Rev0.3: STM32F103C8T6. Rev0.4: PGA2040, an RP2040 module (Akizuki), hand-soldered on headers (D23). **Since D29: a bare RP2040 (C2040) with a W25Q128JV flash and a 12 MHz crystal, machine-placed** | No MCU is Basic, and the user ruled out Preferred Extended (D22). D29 (user) admits the RP2040 as an Extended part instead of the dearer module (§9) |
| USB2514B (24 MHz) | Rev0.3, Rev0.4: **CH335F** on an Akizuki DIP module (12 MHz crystal on our board). **Since D31: the bare CH335F (C5137013, QFN-28), machine-placed** | Every USB2514B variant is Extended. The module was a 38.5 × 10.2 mm hand-soldered part with no published drawing; D31 (user) admits the bare chip as the second Extended part (§6.6, §9) |
| ADS131M02 24-bit ADC | Rev0.3: STM32 12-bit ADC ×2. **Rev0.4: two MCP3208 12-bit SPI ADCs (Akizuki DIP16), one per port, converting at the same instant** | The 24-bit ADC is Extended, and the RP2040's own ADC is too coarse for the 3-LSB floor. Resolution at the bottom of the MID and HIGH ranges is the cost (§4, §7.4) |
| INA190 + 5 V-CM mux (topology B), or INA190 ×6 (topology C) | **Topology C with discrete high-side current mirrors**: OP07CDR + AO3401A per shunt, 6 per board | There is no Basic current-sense amplifier or mux. OP07CDR is Basic. The mirror needs a supply above the 5 V common mode, so a MAU104 isolated 12 V module (Akizuki) is added |
| Shunts 20 mΩ / 2 Ω / 200 Ω | **0.1 Ω / 10 Ω / 510 Ω** | 12-bit ADC and Basic/Akizuki availability (§4). The Basic 0.1 Ω part has ±800 ppm/°C, so R_H is an Akizuki KOA part with ±100 ppm/°C |
| SY6280AAC load switch | **Back-to-back AO3401A pair** + 2N7002 drive + fast turn-off | The load switch is Extended. The back-to-back pair blocks reverse current with the port off (OI-7) |
| TPD4E05U06 ESD | Rev0.3: SRV05-4 on D± and CC. **Rev0.4: PSM712 on the CC lines of J1–J4; D+/D− unprotected** | SRV05-4 is Preferred Extended (D22), and no Basic part protects D± (§7.4) |
| 32 kSPS | Rev0.3: 18.5 kSPS. **Rev0.4: 14.0 kSPS** per channel | Set by the MCP3208's clock and the stretched sampling time this source impedance needs (§3.3) |
| Comparator loop, MCU observes only (D4) | Hardware up-ranging; **firmware holds the new range within 100 µs and does all down-ranging** | Holding the range in hardware needs a latch or one-shot that Basic does not offer. Firmware already owns down-ranging (§3.2, D17) |

Rev0.2's other content still applies unless a section below replaces it: Kelvin sensing, the
default-ON ladder (D9), the CDC-ACM interface (D7), and the gates in Section 8.

---

## 3. Topology

### 3.1 Power path

```
 J4 (Akizuki USB-C module, power only)
   CC1,CC2 ── Rd 5.1 kΩ ×2 to GND ── 1 kΩ ── U17 CH3, CH4    (read J4's advertisement)
   CC1,CC2 ── D4 PSM712 (ESD)
   VBUS ── F1 MF-R300 ── D6 SMBJ6.5CA ── 22 µF ── VBUS_IN ──┬── divider 33k/15k ── U7 CH4  (V_J4)
                                                            ├── port A path (below)
                                                            └── port B path

 port x path (x = A, B; designators shown for A — B: U/RS +10, Q +20):
   VBUS_IN ── Q10 ─┐┌─ Q11 ── VSUP_A ── RS10 R_H ── RS11 R_M ── RS12 R_L ── VBUS_A ── 10 µF ── J2 VBUS
       (AO3401A back-to-back,       0.1 Ω       10 Ω        510 Ω       │
        common source, gates tied)   └─ Q17 bypasses R_M+R_L ┘           ├── Q13 AO3400A + 1 kΩ to GND (discharge)
                                                 └─ Q18 bypasses R_L ┘   └── nothing else (no divider, no TVS)

 J1 (Akizuki USB-C module, host data + logic power)
   CC1,CC2 ── Rd 5.1 kΩ ×2 to GND;  D1 PSM712 on CC1, CC2;  D+, D− unprotected (D22)
   VBUS ── D5 SMBJ6.5CA ── V5L (logic 5 V) ──┬── U6 CH335F V5 (its VDD33: §6.6)
                                             ├── U13, U23, U30 LM393 (comparators)
                                             ├── 10 Ω + 10 µF ── V5A ── U7, U17 MCP3208 V_DD
                                             ├── U5 MAU104 ── V12 ── 10 Ω / 2×22 µF ── V12F ──┬── U10–U12, U20–U22 OP07 V+
                                             │                                             └── U4 CJ431 shunt reg ── V_INJ (8 V)
                                             └── U2 AMS1117-3.3 ── V3V3 (22 µF) ──┬── U1 RP2040 3.3 V pins, U8 flash (U1's core: its own 1.1 V regulator, §7.1)
                                                                                  └── ferrite + 10 µF ── VDDA (U7, U17 V_REF)
```

**Why the switch sits upstream of the ladder.** Any current that leaves the circuit
between a shunt and the DUT is measured as load current. The switch's gate network, the
bypass FETs' gate networks, and the mirror amplifiers' R1 connections are therefore all on
the supply side of the shunt they would disturb. The only things on VBUS_x are the port
capacitor, the discharge FET, and the LOW amplifier's +IN through 10 kΩ. That is why VBUS_x
has no voltage divider and no TVS: either would add a leakage that the LOW range measures.

**Port voltage at the DUT.** Each port's path has the switch (2 × 60 mΩ max), R_H (0.1 Ω),
the MID-bypass FET (60 mΩ max) and about 40 mΩ of copper and module wiring, 0.32 Ω in total.
F1 (0.08 Ω at R1max, D25) is shared by both ports, so its drop depends on the sum:

| Load | Drop | Port, J4 = 5.00 V | Port, J4 = 4.75 V |
|---:|---:|---:|---:|
| 0.5 A, other port off | 0.20 V | 4.80 V | 4.55 V |
| 1.0 A, other port off | 0.40 V | 4.60 V | 4.35 V |
| 1.0 A, other port at 1.0 A | 0.48 V | 4.52 V | 4.27 V |

USB 2.0 asks for ≥ 4.75 V at a downstream port. This board meets that only at 0.5 A from a
source at ≥ 4.95 V (≥ 4.91 V without F1). It is an instrument port, not a compliant hub port, and
`requirements/product.md` §9 states this as a limitation. Rev0.2 regulated the port to
5.10 V and avoided this, but its buck is Extended.

**J4 advertisement.** J4 presents Rd on both CC pins, so any USB-C source supplies 5 V. The
active CC pin's voltage across 5.1 kΩ shows the advertised current: Default 0.25–0.61 V,
1.5 A 0.70–1.16 V, 3.0 A 1.31–2.04 V (USB Type-C vRd ranges). The ADC resolves this
trivially. Firmware uses it for the budget rule in §7.2. **J4 MUST be 5 V.** A source that
puts more than 5.5 V on VBUS without a PD contract is out of specification. D6 (SMBJ6.5CA,
clamping at 11.2 V) protects against transients, not against a wrong supply. **F1**
(MF-R300: 3.00 A hold, 6.00 A trip, 30 V) sits ahead of D6 (D25). A short on VBUS_IN, or a
source above D6's breakdown that D6 crowbars, then ends with F1 tripped rather than with
burned copper. D6 itself may not survive a sustained over-voltage. V_J4 is measured after
F1, so firmware sees F1's drop and its trip.

### 3.2 Measurement front end (one channel shown; ×2)

Each shunt has its own amplifier: a high-side current mirror built from an OP07CDR and an
AO3401A P-FET.

```
 supply side of shunt ──┬─────────── R1 100 Ω ──── X ──── Q (AO3401A) source
                        │                          │      Q gate ── 1 kΩ ── OP07 out
                      R_s (Kelvin)          OP07 −IN ── X
                        │                   OP07 +IN ── 10 kΩ ── load side of shunt (Kelvin)
 load side of shunt ────┘                   V_INJ ── 1 MΩ ── X            (pedestal, §4.1)
                                            Q drain ── AMP_r_x ── R_OUT ∥ C_N ── GND
                                                         ├── 1 kΩ ── MCP3208 input (U7 port A, U17 port B)
                                                         └── LM393 + input (comparator)
```

The loop forces X to the load-side voltage, so the current in R1 is I · R_s / R1. That
current flows out of the FET drain into R_OUT, so **V_out = I · R_s · R_OUT / R1**. The
mirror current is drawn from the supply side of the shunt and is not measured.

| Range | R_s | R1 | R_OUT | C_N | Gain | V/A | Full scale (3.3 V) | Up-range at 2.80 V |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LOW | 510 Ω (0805, Basic) | 100 Ω | 1.5 kΩ | 330 pF C0G | 15 | 7650 | 431 µA | 365 µA |
| MID | 10 Ω (1 W axial, Akizuki) | 100 Ω | 1.5 kΩ | 330 pF C0G | 15 | 150 | 22.0 mA | 18.6 mA |
| HIGH | 0.1 Ω (1 W chip, Akizuki) | 100 Ω | 2.4 kΩ | 220 pF | 24 | 2.4 | 1.37 A | OC trip 1.16 A |

The R1, R_OUT and C_N values are all Basic. Equal range ratios (≈ 56 each) would need a MID
gain of about 13.5 (R_OUT ≈ 1.36 kΩ). The MID gain is 15 instead, which reuses the 1.5 kΩ
part already fitted for LOW (one part type fewer). The ratios are 51 (MID/LOW) and 62.5
(HIGH/MID).

**Supplies and margins.** The OP07s run from V12F (MAU104 output, isolated, −V_out tied to
GND), with the inputs at the ~5 V port common mode:

- *Common mode:* OP07 is specified at ±15 V with ±13 V minimum common-mode range, i.e. 2 V
  from each rail, and its supply-sensitivity row runs down to ±3 V, i.e. with the inputs
  3 V from each rail. The 4.4–5.25 V inputs sit 4.40 V above V− and at least 5.37 V below
  V12F (10.62 V at its lowest: MAU104 −3 %, J1 at −5 % through its line regulation, and the
  10 Ω filter at 30 mA). That is wider than either specified condition, on each side. It is
  still a rail-relative reading of a split-supply spec, which a built board confirms
  (V-MEAS-00, D28).
- *Mirror FET gate:* the gate has to sit about |V<sub>GS(th)</sub>| (≤ 1.3 V at 250 µA; the
  mirror carries 1 mA at HIGH full scale) below the source. At HIGH full scale (1 A), with
  F1 at R1max and the other port off, the source is at 4.66 V (J4 = 5.00 V), so the gate is
  ≈ 3.36 V. With J4 = 4.75 V it is ≈ 3.11 V, and ≈ 3.03 V when the other port also draws
  1 A through the shared F1.
- *OP07 output low (D28 desk check, TI SLOS099F):* the large-signal gain row is specified on
  a **single 15 V supply** with V<sub>O</sub> = 1.4 V to 11.4 V into R<sub>L</sub> ≥ 500 kΩ
  (A<sub>VD</sub> ≥ 100 V/mV, OP07C, 25 °C). The gate is a DC load of ≥ 52 MΩ (AO3401A
  I<sub>GSS</sub> ≤ 100 nA), so that row applies. It puts the output low limit at 1.4 V
  above V−. On V12F the same row's upper end, 3.6 V below V+, is 7.02 V, above the 5.25 V the
  gate needs to turn the FET off. The headroom is therefore **1.63–1.96 V**. Rev0.4 had read
  the output low limit as 3.0 V (±12 V into 10 kΩ at ±15 V), which left 0.03–0.36 V.
- *Loop stability:* not settled on paper. The 1 kΩ gate resistor into C<sub>iss</sub>
  645 pF is a pole at 247 kHz, inside the OP07's 0.4–0.6 MHz gain-bandwidth, and
  C<sub>rss</sub> 55 pF is Miller-multiplied by the drain node. No simulator or vendor model
  was run (D28). V-MEAS-00's step test at bring-up decides it. The gate resistor (0402) and
  C_N (0402 / 0603) can be changed by rework; a fix that needs a new part position needs a
  board revision, which is the risk D28 accepts.
- *Gate safety:* on a 0 / 12 V supply the gate-source voltage stays between about −5 V and
  +7 V, inside AO3401A's ±12 V rating. A ±12 V supply (MAU108) was rejected because the
  gate could then see −17 V.
- *Unpowered inputs:* the 10 kΩ at +IN limits current into an unpowered OP07. Because the
  switch is upstream, the ladder is unpowered whenever the port is off. The only case left
  is J1 unplugged with the port on, which cannot happen: the MCU is off, so the port is off.

**Nested bypass ladder and default state (D9 kept).** In series per channel: R_H → R_M → R_L.

| FET | Bypasses | Gate network |
|---|---|---|
| Q17 (FET_M) | R_M + R_L | 1 MΩ gate→source (OFF bias); Q19 2N7002 gate→GND; LM393 CMP_M output gate→GND |
| Q18 (FET_L) | R_L | 1 MΩ gate→source; Q20 2N7002 gate→GND; LM393 CMP_L output gate→GND |

- Q19 and Q20 have their gates pulled up to V3V3 by 10 kΩ. The RP2040 resets every GPIO to
  an input with its pull-down on (PADS_BANK0 PDE resets to 1; 50–80 kΩ, RP2040 datasheet
  §5.5). At V3V3's 3.251 V minimum, 10 kΩ (+1 %) keeps the gate at 2.705 V against the
  50 kΩ end and 2.887 V against the 80 kΩ end, so ≥ 2.70 V, above the 2N7002's 2.5 V maximum
  threshold (at 250 µA; it then sinks only the 1 MΩ return, ≤ 5.25 µA at a 5.25 V port).
  Rev0.3's 100 kΩ would leave it near 1 V. At reset both bypasses are therefore ON and the
  ladder is in **HIGH** (D9).
- The MCU's HOLD_M_x / HOLD_L_x pins drive Q19 / Q20 gates. Driving one low releases that
  bypass, which is a down-range.
- Ranges: HIGH = Q17 ON. MID = Q17 OFF, Q18 ON. LOW = both OFF.
- Each amplifier sees only its own shunt, so no FET R<sub>DS(on)</sub> is inside a sensed span.

**Up-ranging is hardware; holding is firmware.** CMP_L watches the LOW amplifier and CMP_M
the MID amplifier, each against 2.80 V from a VDDA divider with hysteresis.

1. When an output exceeds 2.80 V, the LM393 open-collector output pulls that bypass gate
   low. No MCU is in this path (G11).
2. The bypassed amplifier's input then collapses, and the comparator releases.
3. The 1 MΩ then starts returning the gate to OFF, with τ ≈ 1 ms at ~1 nF gate
   capacitance. The FET would leave conduction about 1.35 ms later.
4. Before that, firmware sees the comparator edge on EVT_L_x / EVT_M_x and asserts the
   matching HOLD pin. The gate node swings up to the port supply (≈ 5 V), which no RP2040 pin
   may see. EVT is therefore a 2N7002 inverter (Q24/Q25, Q44/Q45): its gate reads the node
   through 100 kΩ, its drain is the GPIO with the internal pull-up, and EVT rises when the
   bypass turns ON. Every RP2040 GPIO has its own edge interrupt. The requirement is to
   assert HOLD within 100 µs, a 13× margin.

If firmware is hung, the range hiccups between two states about every millisecond.
Measurements are then wrong, but nothing is stressed. The RP2040 watchdog resets the MCU,
which returns ports OFF and the ladder to HIGH. Unlike Rev0.3's option-byte IWDG, it is
enabled by firmware, as the first thing at boot; until then the ports are in their reset
state, OFF (§7.3).

**Down-ranging is firmware.** Firmware releases one stage when the current has been below
0.8 × the lower range's up-range threshold for 1 ms. The 1 MΩ gate return makes the
transition take about 1–2 ms, and those samples are flagged as settling.

**Ranging time per stage.** Three contributions:
- the comparator node's τ = R_OUT · C_N ≈ 0.5 µs;
- LM393 response, 1.3 µs at 5 mV overdrive (300 ns at large overdrive);
- AO3401A gate charge, 7 nC at 4.5 V, at the LM393's minimum 6 mA sink: 1.2 µs.

That is **≤ 3.0 µs worst case per stage**, which replaces Rev0.2's 2 µs. LOW → HIGH needs two
stages in sequence: in LOW the whole ladder is 520 Ω, so the MID amplifier cannot reach its
threshold until the LOW stage has bypassed R_L.

**Why C_N sits across R_OUT and not at the ADC pin.** Putting the anti-alias capacitor at the
pin behind a series resistor would add a slow pole to the comparator's node. With 1 kΩ + 10 nF,
the LOW node's response becomes τ ≈ 25 µs, and the ranging budget fails. Instead:
- C_N sets one ~0.5 µs pole that the comparator and the ADC share.
- The port capacitor band-limits the current itself: 31 Hz on LOW, 1.6 kHz on MID (§4).
- The ADC needs a long sampling time so that charge sharing with C_N settles. The MCP3208
  samples for only 1.5 clocks (1.5 µs at 1 MHz). After a 3.3 V step between successive
  channels that would leave 17 LSB (LOW, MID) to 31 LSB (HIGH) of error. The RP2040 PIO
  therefore stretches the sample phase to 4.5 µs by holding the clock; the datasheet allows
  an irregular clock as long as each timing limit is met (DS21298E §6.2). The residual is
  then 0.06 LSB (LOW, MID) and 0.21 LSB (HIGH). These figures come from the datasheet's
  input model; V-MEAS-06 checks them on the first board (D28).

**Overrange stays inside the ADC's ratings because the MCP3208 runs from 5 V.** An
overranged amplifier node rises almost to the port supply: 4.92 V (LOW, MID) and 5.04 V
(HIGH) at J4 = 5.25 V. The MCP3208 rates its inputs only to V<sub>DD</sub> + 0.6 V and
gives no input-current rating.
- At V<sub>DD</sub> = 3.3 V the HIGH node would push about 1.1 mA through the 1 kΩ into a
  pin rated to 3.9 V.
- At V<sub>DD</sub> = V5A (5 V; V<sub>REF</sub> stays 3.3 V, so the transfer and every
  range figure are unchanged) the node stays inside the rating, with 0.06–0.18 V of margin,
  for J4 ≤ 5.25 V and V5L ≥ 4.5 V.
- Only at the USB-C corner, J4 = 5.5 V together with V5L = 4.5 V, does the HIGH node exceed
  the rating, by up to 0.18 V; the 1 kΩ then limits the current.

Samples taken during a range change are flagged in any case.

### 3.3 Data path — and the COM port

```
   J1 D+/D- ── U6 CH335F (HS hub, 4 downstream) ────────┬─ port 1 ── U1 RP2040 (USB FS device)
                                                        ├─ port 2 ── J2 D+/D-   (DUT A passthrough)
                                                        ├─ port 3 ── J3 D+/D-   (DUT B passthrough)
                                                        └─ port 4    unused
```

The host sees a hub, and behind it a composite device on port 1. That device has two
CDC-ACM functions (D7, unchanged):

| Interface | Class | Appears on the PC as | Carries |
|---|---|---|---|
| 0 + 1 | CDC-ACM | `COMn` / `/dev/ttyACM0` | Control. ASCII line protocol |
| 2 + 3 | CDC-ACM #2 | `COMn+1` / `/dev/ttyACM1` | Binary sample stream, framed |

The RP2040 has 4 KB of USB packet memory, so the two CDC-ACM functions fit with room to
spare.

Rev0.2's design rules all carry over:
- The unique serial number comes from the 64-bit unique ID of U8, the flash. The RP2040 has
  no unique ID of its own; the Pico SDK reads the flash's. U8 is a W25Q128JVSIQ (C97521,
  Basic), which has a factory-set, read-only 64-bit unique ID read by instruction 4Bh
  (Winbond W25Q128JV, Rev. J, 2024-04-25). A test build reads it at bring-up (V-MEAS-06).
  Until D29 the PGA2040's own W25Q64JV did this.
- The control interface stays usable while the stream runs.
- The stream is binary.
- VID/PID is still OPEN (REQ-HOST-06); pid.codes is the candidate for an open-hardware ID.

The RP2040's D+ pull-up is on chip and under firmware control, so firmware decides when to
attach and no external pull-up is fitted. The RP2040 needs a 27 Ω series resistor on each
of USB_DP and USB_DM, close to the chip (RP2040 datasheet p. 11; "Hardware design with
RP2040" p. 11). No 27 Ω resistor is Basic (C25100, 27 Ω 0402, is Extended), so each line
takes two Basic resistors in series next to U1: 22 Ω (C25092, 0402) and 5.1 Ω (C25197, 0603;
no 0402 5.1 Ω is Basic), both ±1 %. That is 27.1 Ω, 26.83–27.37 Ω (−0.6 % / +1.4 %); the
datasheet states no tolerance. The PGA2040 carried its own pair until D29.

**Sample rate (replaces D8 and Rev0.3's 18.5 kSPS).**
- U7 converts port A's three amplifiers and U17 port B's. The two MCP3208s share CLK, CS and
  DIN, and each has its own DOUT, so both ports are sampled at the same instant
  (REQ-MEAS-08). The RP2040 PIO runs the bus.
- f<sub>CLK</sub> = 1 MHz, the rate the MCP3208 guarantees down to V<sub>DD</sub> = 2.7 V.
  A conversion takes 20 clocks plus the 3 µs sample stretch (§3.2): 23 µs.
- One scan (LOW, MID, HIGH) takes 69 µs. Each 1 ms frame holds 14 scans and one aux
  conversion, with 11 µs idle → **14.0 kSPS per channel**.
- The aux conversion alternates between CH3 (U7: VREF_CHK; U17: J4 CC1) and CH4 (U7: V_J4;
  U17: J4 CC2), so each aux input is read every 2 ms.
- Samples are 69 µs apart inside a frame; across the aux conversion the gap is 103 µs. The
  stream carries the frame position, so the host knows each sample's time exactly.
- No averaging: each output sample is one conversion. Rev0.3 averaged four.
- On HIGH, DUT current content between 7 kHz and the ~100 kHz port bandwidth (§4) aliases
  into the output. The average current is preserved unless the DUT's current is periodic at
  a multiple of the sample rate; waveform detail above 7 kHz is lost.
- If stretching the sample phase fails at bring-up, the fallback converts each channel twice
  and keeps the second result, at 8 kSPS (V-MEAS-06).

| Output | Bytes per sample pair | Rate | % of FS bulk (1188 kB/s) |
|---|---:|---:|---:|
| 14.0 kSPS, 2 ch | 5 (2 × u16 + 1 B ranges/flags) | 70.0 kB/s | 5.9 % |

The host interface is not the ceiling: the ADC conversion time is (OI-14).

**HS through the modules.** The CH335F hub is High-Speed upstream and downstream (MTT), so a
DUT on J2/J3 can run at HS. Each HS path, however, passes through an Akizuki USB-C breakout
module, its 2.54 mm headers and an unknown module layout: J1 upstream, J2 or J3 downstream.
Since D31 the hub sits on the board itself, so a path crosses one module and header instead
of two. HS eye margin is unverified, and the fallback is that DUTs enumerate at FS. This is OI-26, verified at bring-up (V-HOST-01). On the board
itself the pairs start at W = 0.31 mm, S = 0.15 mm on L1 over L2 of JLC04161H-7628, without
impedance control (D27).

### 3.4 Port switching, Rp, over-current and discharge (per port)

```
 MCU EN_x ──┬── 33 kΩ ── J2 CC1     (Rp, present only while EN_x is high)
            ├── 33 kΩ ── J2 CC2
            └── 10 kΩ ── EN_G_x ──┬── 100 kΩ to GND
                                  ├── LM393 CMP_OC_x output (open collector)
                                  ├── Q12 2N7002 gate → pulls switch gate low via R_on  (port ON, soft start)
                                  └── Q14 2N7002 inverter → DIS_x (10 kΩ pull-up to V3V3)
                                          DIS_x ── Q13 AO3400A gate (discharge VBUS_A via 1 kΩ)
                                          DIS_x ── Q15 2N7002 → Q16 S9012 PNP: switch gate to common source (fast OFF)
```

- **Rp = 33 kΩ to 3.3 V on both CC pins, sourced from the EN_x pin itself.** No 36 kΩ is
  Basic. With a DUT's Rd = 5.1 kΩ ± 10 %, the DUT sees 0.35–0.48 V, inside the Default
  window (0.25–0.61 V). Rp disappears whenever EN_x is low or the MCU is in reset, so the
  DUT sees a clean detach (REQ-PORT-07). The board advertises **Default USB power only**
  (§7.2).
- **Soft start ≥ 1 ms:** turn-on goes through R_on with a gate–drain Miller capacitor; the
  values are set at capture against the 10 µF port capacitor. **Turn-off ≤ 10 µs:** Q16
  clamps the gate to the common source as soon as DIS_x rises. The OC comparator therefore
  opens the port fast even though turn-on is slow.
- **Over-current:** CMP_OC_x compares the HIGH amplifier against 2.80 V, which is 1.16 A
  (±3 %). It pulls EN_G_x low directly, and the port opens in hardware. Firmware sees the
  edge (OC_x, a GPIO edge interrupt), drives EN_x low, and latches `FAULT:OVERCURRENT`.
  - If firmware does not respond, the port retries with a ≥ 1 ms soft start and trips again,
    a bounded hiccup, until the watchdog resets the MCU.
- **Reset state:** EN_x pins are inputs at reset (with the RP2040's pull-down on), and the
  100 kΩ holds EN_G_x low. Result:
  switch OFF, discharge ON, Rp absent, ladder in HIGH.
- **Back-feed:** with the port off, the back-to-back pair blocks a DUT that drives VBUS_x,
  and the DUT sees the 1 kΩ discharge load. VBUS_x is not measured (§3.1), so back-feed is
  **blocked but not detected**. This is a reduction against Rev0.2 (REQ-PORT-04).

---

## 4. The range ladder — can it actually do 0.1 µA to 1 A?

| Range | Used from (after down-range) | Up-range at | LSB | Floor = 3 LSB | Burden at up-range | Bandwidth (10 µF port C) |
|---|---:|---:|---:|---:|---:|---:|
| LOW | 0 | 365 µA | 0.105 µA | 0.32 µA | 0.190 V (whole ladder, 520 Ω) | 31 Hz (τ 5.2 ms) |
| MID | 292 µA | 18.6 mA | 5.37 µA | 16 µA | 0.189 V (10.2 Ω) | 1.6 kHz (τ 102 µs) |
| HIGH | 14.9 mA | OC 1.16 A | 0.336 mA | 1.0 mA | 0.16 V at 1 A | ~100 kHz (τ 1.6 µs) |

**Resolution 0.1 µA** is 1 LSB on LOW (0.105 µA). It is resolved, though at the floor of the
accuracy specification. **Range to 1 A** is HIGH at 2.4 V, below both the OC trip and the
ADC clip. The bottom of MID and HIGH is the weak spot: at 292 µA on MID, 3 LSB is 5.5 % of
the reading, and at 14.9 mA on HIGH it is 6.8 %. A 12-bit converter covering 0.1 µA – 1.37 A
in three ranges cannot do better. The span from the top of HIGH to one LOW LSB is fixed at
1.37 A / 0.105 µA ≈ 1.3 × 10⁷. Each range has 4096 codes, so the two range ratios must
multiply to ≈ 3,200 (51 × 62.5). Each range therefore spans about 50–60×, and the overlap
region sits ~50 LSB above the bottom.

**Ride-through.** While on LOW, a DUT step is supplied by the 10 µF port capacitor during the
two ranging stages, so the port sags by I · t / C:

| Step from LOW | Two stages at 3 µs | If a stage takes 4 µs |
|---:|---:|---:|
| 1 A | 0.60 V | 0.80 V |
| 0.3 A | 0.18 V | 0.24 V |

A DUT that wakes from deep sleep straight into 1 A therefore sees a ~0.6 V dip. Most MCUs
ride through this. Radios with brown-out at 4.3 V on a 5 V input may not. This is stated as a
limitation, not hidden.

**Stuck range** (a bypass FET fails OFF, or firmware holds the wrong range) into a short at
the port:

| Stuck in | Current | Shunt dissipation | What stops it |
|---|---:|---:|---|
| LOW | 9.6 mA | 47 mW in 510 Ω 0805 (0.125 W) | Nothing needed |
| MID | 0.48 A | **2.35 W in R_M (1 W part)** | Below the OC trip. Firmware sees the MID amplifier saturated with the bypass commanded ON, and opens the port within 10 ms. The watchdog is the backstop, so firmware sets its timeout to ≤ 5 s. R_M (Faithful Link MFU datasheet) is rated for 2.5 × RCWV for 5 s (6.25 W, ΔR ≤ 1 %) and for 4 × RCWV pulses (16 W, 1 s on / 25 s off, 10,000 cycles). 2.35 W is therefore inside its short-time rating for up to 5 s (D28). The datasheet bounds the resistance shift only after that harsher test, so the < 0.1 % shift after a 10 ms fault is checked at bring-up (V-MEAS-00) |
| HIGH | Limited by J4's source | R_H 1 W | OC trip at 1.16 A |

### 4.1 Noise and offset

**Noise is not the limit.** OP07 input noise is 10.5 nV/√Hz. Over the whole ~0.3 MHz C_N
band, all of which aliases into the unaveraged 14 kSPS output, it is ≪ 1 LSB on every range:
about 2.5 nA rms on LOW against a 105 nA LSB. The 12-bit quantization and the converter's INL
dominate.

**Offset is a dead zone unless it is biased.** A current mirror conducts in one direction
only. If the op-amp offset is negative, currents below |V<sub>OS</sub>| / R_s read as zero.
OP07C has no published maximum. OP07D's 150 µV maximum, used as the planning bound, gives
0.29 µA of dead zone on LOW, larger than the 0.1 µA target.

**Fix: a pedestal current injected into node X** from V_INJ (CJ431 shunt regulator at 8 V
from V12F) through 1 MΩ.
- The mirror then always conducts at zero load.
- The injection is 2.75–3.6 µA over a 4.4–5.25 V port supply. That is ≥ 1.8× the 1.5 µA
  needed to cancel 150 µV across R1 = 100 Ω.
- The pedestal is 4.5 mV (5.6 LSB) on LOW and MID, and 7.2 mV (8.9 LSB) on HIGH. Zero
  calibration removes it.
- It moves with the port supply by R_OUT / R_INJ = 1.5 mV/V on LOW, which is 0.20 µA per
  volt. Firmware corrects it from V_J4 (U7 CH4). After correction, ±2 % resistor tolerance
  leaves < 0.04 LSB per volt.

Without V_INJ regulation, the MAU104 output would track J1 (line regulation ±1.2 % per 1 %):
a ±5 % J1 change would move the LOW pedestal by 1.3 LSB. Its load regulation below 20 % load
is not specified and would add to that. Either drift happens after zero calibration and
would use up part of the 3-LSB accuracy floor. That is why U4 exists.

**Zero calibration stays mandatory** (REQ-MEAS-03). Zero-cal is per range, with the port ON
and nothing attached. It also absorbs these constant offsets, which are all well under 1
LSB of the range that sees them:
- the discharge FET's I<sub>DSS</sub> (port on, gate low);
- port-capacitor leakage;
- OP07 I<sub>B</sub> through the +IN 10 kΩ (1.8 nA typical);
- the 5 µA of the held bypass's 1 MΩ: it flows through R_H, or through R_H + R_M for FET_L.

Capacitor leakage can rise with voltage and temperature. MLCC insulation resistance at
10 µF is the largest unknown on LOW, and it is measured at bring-up (V-MEAS-01).

### 4.2 Accuracy target (D20; closes OI-21)

**±(1 % of reading + 3 LSB of the active range)** within ±10 °C of the calibration
temperature, after per-unit gain calibration and zero-cal. The floors are LOW 0.32 µA,
MID 16 µA and HIGH 1.0 mA.

| Contributor (±10 °C) | Size |
|---|---:|
| Shunt TCR (±100 ppm/°C) | 0.10 % |
| R_OUT / R1 ratio, two ±100 ppm/°C thick-film parts | 0.20 % |
| CJ431 used to measure VDDA (U7 CH3) — ratiometric correction | 0.12 % |
| OP07 drift 0.5 µV/°C typ × 10 °C, referred to input | 0.01 µA LOW, 0.5 µA MID, 50 µA HIGH |
| ADC INL (MCP3208-C ±1 / ±2 LSB typ / max, specified at V<sub>REF</sub> = 5 V; typical +0.6 / −0.4 LSB at 3.3 V in DS21298E Figure 2-2 (read from its vector data), not guaranteed; V-MEAS-06 checks it) | inside the 3 LSB floor |
| S/H residual after the stretched sample (§3.2) | ≤ 0.21 LSB, inside the floor |
| Gain calibration residual | ≤ 0.3 % (against a reference meter, V-MEAS-02) |

The total is ≤ 0.7 % plus the floor, which leaves 0.3 % of margin to the 1 % target. The
target was set to what this part set can meet. Rev0.2's ±0.5 % proposal needed the 24-bit
ADC and the ≤ 25 ppm/°C shunt, both Extended.

---

## 5. Sense topology — decision record

| Topology | What it needs | Verdict |
|---|---|---|
| A — one amp, sense across the whole ladder | FET R<sub>DS(on)</sub> inside the span (≈ 1900 ppm/°C) | Rejected in Rev0.1 |
| B — one amp + mux selecting Kelvin taps | ≥ 10 V-class analog mux | Rejected in Rev0.3: no mux is Basic or at Akizuki in SMD |
| C — one amp per shunt | 6 current-sense amplifiers | **Adopted** (D17), with discrete OP07 + P-FET mirrors because no current-sense amplifier is Basic |

C also removes mux leakage and charge injection from the sensed path, which made it the
better choice even in Rev0.2 once D10 removed the area objection (OI-19).

---

## 6. Nets and designators

### 6.1 Power nets

| Net | From | Voltage | Feeds |
|---|---|---|---|
| VBUS_IN | J4 VBUS through F1 (D6 to GND) | 5 V (source) less F1's drop, ≤ 0.16 V at 2 A | Port switches, V_J4 divider |
| VSUP_A / VSUP_B | Port switch output | ≈ VBUS_IN | Ladder supply side, mirror R1s |
| VBUS_A / VBUS_B | Ladder load side | ≈ VBUS_IN − 0.32 V at 1 A | J2 / J3 VBUS, port C, discharge |
| V5L | J1 VBUS via D5 | 5 V (host) | U6 CH335F V5, LM393 ×3, MAU104, AMS1117, V5A, SPI level-shifter pull-ups |
| VDD33_HUB | U6's internal LDO (VDD33, pin 28) | 3.2–3.5 V | U6 only, and its four OVCUR# pins (held inactive). Not tied to V3V3 (§6.6) |
| V5A | V5L via 10 Ω + 10 µF | 5 V | U7, U17 MCP3208 V<sub>DD</sub> |
| V12 / V12F | MAU104 / after 10 Ω + 2 × 22 µF 25 V | ≈ 12 V / ≈ 11.7 V | OP07 ×6, U4 |
| V_INJ | U4 CJ431 shunt regulator | 8.0 V | Six 1 MΩ pedestal resistors |
| V3V3 | AMS1117-3.3 | 3.3 V | U1's IOVDD, USB_VDD, VREG_VIN and ADC_AVDD; U8 flash (§6.5, §7.1); pull-ups, Rp (via EN pins), LEDs |
| DVDD | U1's on-chip regulator (VREG_VOUT, pin 45) | 1.1 V | U1 DVDD pins 23 and 50 only |
| VDDA | V3V3 via ferrite + RC | 3.3 V | U7, U17 V<sub>REF</sub> (the ADC full scale), comparator threshold dividers |
| VREF_CHK | U3 CJ431 | 2.5 V | U7 CH3 only (measures VDDA) |

### 6.2 Designators

Channel A uses the numbers below. **Channel B is the same circuit with U and RS numbers + 10
and Q numbers + 20** (U10 → U20, RS10 → RS20, Q10 → Q30). U30 is shared. Passives are
numbered at capture.

| Ref | Function | Part (source) | Class |
|---|---|---|---|
| J1 | USB-C host (data + logic power) | AE-USB2.0-TYPE-C (Akizuki g113080) | Hand |
| J2, J3 | USB-C OUT A / OUT B | AE-USB2.0-TYPE-C (Akizuki g113080) | Hand |
| J4 | USB-C PWR IN (power only) | AE-USB2.0-TYPE-C (Akizuki g113080) | Hand |
| U1 | MCU, support circuit in §6.5 | RP2040 (C2040), LQFN-56 7 × 7 mm | **Extended** (D29) |
| U8 | QSPI flash, 16 MB; its 64-bit unique ID is the USB serial number | W25Q128JVSIQ (C97521), SOIC-8 208 mil | Basic |
| U2 | 3.3 V LDO | AMS1117-3.3 (C6186) | Basic |
| U3 | VDDA check reference, 2.5 V | CJ431 (C3113) | Basic |
| U4 | V_INJ shunt regulator, 8 V | CJ431 (C3113) | Basic |
| U5 | Isolated 12 V for the op-amps | MAU104 (Akizuki g104132) | Hand |
| U6 | USB 2.0 HS hub, support circuit in §6.6 | CH335F (C5137013), QFN-28 4 × 4 mm | **Extended** (D31) |
| U7 | ADC: CH0–CH2 port A LOW / MID / HIGH, CH3 VREF_CHK, CH4 V_J4, CH5–CH7 to GND | MCP3208-CI/P (Akizuki g100238) | Hand (DIP16) |
| U17 | ADC: CH0–CH2 port B LOW / MID / HIGH, CH3 J4 CC1, CH4 J4 CC2, CH5–CH7 to GND | MCP3208-CI/P (Akizuki g100238) | Hand (DIP16) |
| U10, U11, U12 | Mirror amp HIGH / MID / LOW | OP07CDR (C7433) | Basic |
| U13 | CMP_L_A, CMP_M_A | LM393DR2G (C7955) | Basic |
| U30 | CMP_OC_A, CMP_OC_B (shared) | LM393DR2G (C7955) | Basic |
| RS10 | R_H 0.1 Ω 1 W ±0.5 % ±100 ppm/°C, Kelvin land | TSL1TTER100D (Akizuki g109588) | Hand (SMD 6.3 × 3.1 mm) |
| RS11 | R_M 10 Ω 1 W ±1 % ±100 ppm/°C | MFU100F10RB (Akizuki g108805) | Hand (axial) |
| RS12 | R_L 510 Ω ±1 % ±100 ppm/°C, 0805 | C17734 | Basic |
| Q10, Q11 | Port switch, back-to-back | AO3401A (C15127) | Basic |
| Q12 | EN driver | 2N7002 (C8545) | Basic |
| Q13 | VBUS discharge (with 1 kΩ) | AO3400A (C20917) | Basic |
| Q14, Q15 | EN inverter, fast-off driver | 2N7002 (C8545) | Basic |
| Q16 | Fast-off clamp | S9012 (C8543) | Basic |
| Q17, Q18 | Bypass FET_M, FET_L | AO3401A (C15127) | Basic |
| Q19, Q20 | Bypass hold (default ON) | 2N7002 (C8545) | Basic |
| Q21, Q22, Q23 | Mirror FET HIGH / MID / LOW | AO3401A (C15127) | Basic |
| Q24, Q25 | EVT_M, EVT_L level shifters (inverting) | 2N7002 (C8545) | Basic |
| Q50, Q51, Q52 | SCLK, CS, DIN level shifters to 5 V (inverting; shared by U7 and U17) | 2N7002 (C8545) | Basic |
| D1, D2, D3 | ESD on J1 / J2 / J3 CC1, CC2 (D+/D− unprotected, D22) | PSM712-LF-T7 (C32677) | Basic |
| D4 | ESD on J4 CC1, CC2 | PSM712-LF-T7 (C32677) | Basic |
| D5, D6 | TVS on J1 / J4 VBUS | SMBJ6.5CA (C7420377) | Basic |
| F1 | J4 input resettable fuse, ahead of D6 | MF-R300 (Akizuki g112630) | Hand (radial, 12.0 × 3.0 mm body, 18.3 mm tall) |
| D10, D11 | Port A LED green / red | KT-0805G (C2297) / NCD0805R1 (C84256) | Basic |
| D12, D13 | Port B LED green / red | same | Basic |
| Y1 | 12 MHz → U1 XOSC, with 2 × 15 pF C0G (C1548) and 1 kΩ in XOUT (§6.3) | X322512MSB4SI (C9002) | Basic |
| Y2 | 12 MHz → U6 XI/XO, no load capacitors (§6.6) | X322512MSB4SI (C9002) | Basic |
| SW1, SW2 | Port A / B button | TS-1187A-B-A-B (C318884) | Basic |
| SW3 | BOOT button behind a lid pinhole | TS-1187A-B-A-B (C318884) | Basic |
| FB1 | VDDA ferrite | BLM18PG121SN1D (C14709) | Basic |
| — | SWD, for debug only (programming uses the ROM USB bootloader) | Tag-Connect TC2030-NL footprint (no part), routed to U1's SWCLK (pin 24) / SWD (pin 25) | — |

"Hand" means a large part bought from Akizuki and soldered by the user. The modules go on
pin headers, and their through-hole pins are soldered from the Bottom side. That changes
CLAUDE.md §1's "Top-side assembly": JLCPCB places only Top SMD, and the user adds the
through-hole and large parts afterwards (REQ-MFG-01).

### 6.3 Clock tree

| Clock | Source | Consumer | Notes |
|---|---|---|---|
| Y1 12 MHz | C9002, 2 × 15 pF C0G (C1548), 1 kΩ in series with XOUT | RP2040 XOSC (XIN pin 20, XOUT pin 21) | PLLs give the system clock and the 48 MHz USB clock; the ROM USB bootloader needs 12 MHz. Rated C<sub>L</sub> 20 pF, run at ≈ 10.5 pF: see below (G20, V-MEAS-06) |
| Y2 12 MHz | C9002 | U6 CH335F XI (pin 11) / XO (pin 12) | CH335F has built-in crystal load capacitors; C9002's 20 pF C<sub>L</sub> may not match them. Measure the frequency against USB's ±500 ppm at bring-up (G9) |
| SCLK | RP2040 PIO | U7, U17 | 1 MHz; sample phase stretched to 4.5 µs (§3.2, §3.3) |

The hub's crystal is independent of the MCU, so the hub does not depend on MCU firmware to
run. This closes OI-2 (D19). D23 removed Y1 because the module had its own crystal; D29
restores it, as the same part as Y2.

**Y1 is not Raspberry Pi's recommended crystal (D29 desk check).** Raspberry Pi recommends
the Abracon ABM8-272-T3: C<sub>L</sub> 10 pF, ESR 50 Ω max, drive 200 µW max, loaded by
2 × 15 pF (7.5 pF + an assumed 3 pF stray = 10.5 pF) with 1 kΩ in XOUT against over-drive
("Hardware design with RP2040" p. 10). It is Extended (C20625731), so it would be a third
exception to D22, after D29 and D31. Y1 is C9002 instead, with the same load and resistor:
- *Frequency.* C9002 is rated for C<sub>L</sub> 20 pF (±10 ppm at 25 °C, ±20 ppm over
  temperature, ±3 ppm per year), so 10.5 pF pulls it high. Its sheet gives no motional
  capacitance C1, so the calc script sweeps it, and takes the worst case over a load of
  9.5–12.5 pF (2–5 pF stray) and C0 of 1–3 pF. The pull is ≤ 48 ppm at C1 = 2 fF (≤ 81 ppm
  with the tolerances), ≤ 119 ppm at 5 fF (≤ 152 ppm) and ≤ 238 ppm at 10 fF (≤ 271 ppm);
  even at a 20 fF bound it is ≤ 476 ppm (≤ 509 ppm), inside the 1000 ppm the RP2040
  tolerates (RP2040 datasheet p. 181).
- *Start-up.* C9002's ESR is 80 Ω max, against the reference's 50 Ω. With the same load and
  C0 ≤ 3 pF on both, the start-up margin is 0.625 × the reference design's. Loading C9002 to
  its rated 20 pF (2 × 33 pF) would not help: it raises the oscillator's critical gain 2.9 ×.
- *Drive level.* C9002 is rated 10–200 µW (100 µW typical), the same 200 µW maximum as the
  reference crystal that the 1 kΩ is chosen for.

Raspberry Pi warns that another crystal must be tested even when its specification is
similar. V-MEAS-06 tests start-up over 100 power cycles and the frequency on the first
boards. If it fails, ABM8-272-T3 fits the same 3225 four-pad land, and it needs the user's
decision as a third Extended part.

### 6.4 MCU pin budget (RP2040, 30 GPIO)

| Group | Pins | Count |
|---|---|---:|
| ADC bus | SCLK, CS, DIN (shared, through Q50–Q52); DOUT_A, DOUT_B (through 10 kΩ / 15 kΩ dividers) | 5 |
| Per port × 2 | EN, OC event, HOLD_L, HOLD_M, EVT_L, EVT_M | 12 |
| LEDs, buttons | 4 + 2 (SW1, SW2) | 6 |
| Clock test pad (D29) | One of GPIO21, 23, 24, 25 (GPOUT0–3), to a test pad for V-MEAS-06 | 1 |
| **Total** | | **24 of 30** |

USB D±, QSPI, SWD and RUN have dedicated pins. SW3 goes to QSPI_SS through 1 kΩ (BOOTSEL,
§6.5), not to a GPIO (REQ-BOOT-02). Six GPIO are spare, including the four that reach the
RP2040's own ADC.

RP2040 pins are not 5 V-tolerant, so every 5 V signal is translated:
- **SCLK, CS, DIN.** The MCP3208s run from 5 V, so their input-high threshold is
  0.7 × V<sub>DD</sub> = 3.5 V, above what an RP2040 pin drives. Each line is a 2N7002
  inverter with a 1.5 kΩ pull-up to V5L (rising edge ≈ 120 ns, fine at 1 MHz). Firmware
  inverts the three outputs in the RP2040 pad control, so the PIO program runs in true
  polarity. An RP2040 in reset leaves CS high, deselected.
- **DOUT.** Each reaches its pin through a 10 kΩ / 15 kΩ divider: 4.1–5.25 V becomes
  2.5–3.2 V, above the RP2040's 2.0 V input-high threshold.
- **EVT** inputs: §3.2. **OC_x** reads EN_G_x, which never exceeds 3.3 V, through 100 kΩ.
- **HOLD** pins drive Q19/Q20 gates at 3.3 V, against 10 kΩ pull-ups (§3.2).

### 6.5 U1 support circuit (D29)

U1 follows Raspberry Pi's minimal design ("Hardware design with RP2040", Release 2; its
Figure 11 schematic, RPI-RP2040-MINIMAL R3). Where this board differs, the row says why. Pin
numbers are from the RP2040 datasheet's pin tables.

| U1 pin (number) | Connects to | Parts, placed at the pin |
|---|---|---|
| IOVDD (1, 10, 22, 33, 42, 49) | V3V3 | 100 nF each (6) |
| USB_VDD (48) | V3V3 | 100 nF. The reference shares one capacitor between pins 48 and 49 for space; the datasheet asks for one at each pin |
| ADC_AVDD (43) | V3V3 | 100 nF. The RP2040's own ADC is not used |
| VREG_VIN (44) | V3V3 | 1 µF (C52923), close to pin 44 |
| VREG_VOUT (45) → DVDD (23, 50) | DVDD, 1.1 V | 1 µF close to pin 45; 100 nF at each DVDD pin (2); a DVDD test pad |
| GND (57, the ePad) | GND | Reduced ePad, 3.20 × 3.20 mm (datasheet Figure 167, derived from its geometry); the land is drawn from that figure, not taken from a stock QFN-56 footprint (G20) |
| USB_DP (47), USB_DM (46) | U6 CH335F port 1, DP1 (7) / DM1 (6) | 22 Ω + 5.1 Ω in series per line, next to U1 (§3.3) |
| XIN (20), XOUT (21) | Y1 | 15 pF C0G from each crystal terminal to GND; 1 kΩ between XOUT and Y1. Short traces (§6.3) |
| QSPI_SS (56), QSPI_SCLK (52), QSPI_SD0–SD3 (53, 55, 54, 51) | U8 /CS, CLK, IO0–IO3 | Direct and short. No external pull-up on QSPI_SS: the pad resets with its pull-up on, and the reference leaves its 10 kΩ unfitted |
| QSPI_SS (56), again | SW3 (BOOT) to GND, through 1 kΩ | The 1 kΩ sits next to U8. It lets the QSPI_SS pin safely over-drive the button's pull to ground ("Hardware design with RP2040" p. 9) |
| RUN (26) | V3V3 through 10 kΩ; a RUN test pad | The pin has an internal pull-up and the datasheet says to tie it high when unused; the 10 kΩ makes the tie explicit, and the pad resets U1 during bring-up |
| TESTEN (19) | GND | — |
| SWCLK (24), SWD (25) | TC2030-NL | — |
| GPIO0–29 | §6.4 | — |
| U8 VCC (8) | V3V3 | 100 nF at the pin |

Parts this adds: U1, U8, Y1; 10 + 1 × 100 nF, 2 × 1 µF, 2 × 15 pF, 2 × 22 Ω, 2 × 5.1 Ω,
2 × 1 kΩ (XOUT, BOOTSEL) and 1 × 10 kΩ (RUN); and a local 10 µF on V3V3 at U1, as the
reference design's C17. Every 3.3 V pin and the flash share V3V3, so the flash's chip select
and supply rise together, as the flash requires at power-up.

### 6.6 U6 support circuit (D31)

U6 follows the WCH CH334/CH335 datasheet (V2.5): its pin table, §3 and §4, and the §5.6
package drawing (QFN28_4X4X0.75-0.4). The chip carries its own crystal load capacitors, the
upstream 1.5 kΩ D+ pull-up, the downstream pull-downs, a power-on reset and an internal
configuration, so its support circuit is small. Pin numbers are the datasheet's.

| U6 pin (number) | Connects to | Parts, placed at the pin |
|---|---|---|
| V5 (26) | V5L | 1 µF (C52923); the datasheet asks for at least 1 µF |
| VDD33 (28) | VDD33_HUB, the output of U6's own LDO | 100 nF (C307331) + 10 µF (C15850), the datasheet's 0.1 µF + 10 µF option; a VDD33_HUB test pad. Not tied to V3V3 |
| GND (27), ePad (0) | GND | ePad 2.7 × 2.7 mm (±0.2), with vias to L2; the land is drawn from the §5.6 drawing, not taken from a stock QFN-28 footprint (G21) |
| XI (11), XO (12) | Y2 (C9002) | No load capacitors: they are on the chip (G9). Short traces |
| DMU (20), DPU (21) | J1 D− / D+ | Direct. The 1.5 kΩ pull-up is on the chip |
| DM1 (6), DP1 (7) | U1 USB_DM / USB_DP | Through U1's 22 Ω + 5.1 Ω per line, next to U1 (§3.3, §6.5) |
| DM2 (8), DP2 (9) | J2 D− / D+ | Direct |
| DM3 (13), DP3 (14) | J3 D− / D+ | Direct |
| DM4 (15), DP4 (16) | Not connected | Port 4 is unused; its on-chip pull-downs keep it empty |
| RESET#/CDP (17) | Not connected | About 25 kΩ internal pull-up and the power-on reset. Undriven at power-up it enables no CDP (datasheet Table 3-2) |
| OVCUR1# (24), OVCUR2# (23), OVCUR3# (19), OVCUR4# (18) | VDD33_HUB, directly | Held inactive. Over-current is the port path's job (§3.4). The default threshold (OC_LEVEL = 0) is 2.4 V, below VDD33_HUB's 3.2 V minimum |
| PWREN1# (4), PWREN2# (2), PWREN3# (10), PWREN4#/SUSP (5) | Not connected | Outputs. Port power is switched by U1 only (G13, REQ-PORT-06) |
| LED1/PSELF (1), LED2/PGANG (3) | Not connected | Sampled at reset against their internal pull-ups: high is self-powered (D26) and ganged over-current mode, which is irrelevant with PWREN# unused (G14) |
| LED3/SCL (22), LED4/SDA (25) | Not connected | No EEPROM: SDA's built-in pull-up reads no device, and the internal configuration holds (4 ports, MaxPower 32h = 100 mA, self-powered; datasheet §3.5). No hub LEDs |

Parts this adds: U6 only, as a new type (C5137013). Its 1 µF, 100 nF and 10 µF reuse C52923,
C307331 and C15850, and Y2 was on the board before D31.

**U6's supply (D31 desk check; `CIRCUIT_DESIGN_Rev0.4_calc.py`).**
- V5 runs on V5L with the internal LDO on. The datasheet's range for that, 4.5–5.25 V
  (§4.2), equals V5L's design range (§3.2): the margin is +0.00 V at both ends. At the USB-C
  5.5 V corner V5L is +0.00 V from V5's 5.5 V absolute maximum (§4.1). This is not new with
  D31: the module carried the same chip on the same rail.
- At 85 mA typical, U6 dissipates 425 mW from 5.0 V, of which its LDO (V5 − 3.3 V) takes
  145 mW; from 5.25 V, 446 mW and 166 mW. The datasheet gives no thermal resistance. The
  ePad is soldered to GND with vias to L2, and the dissipation is the same as on the module.
- VDD33_HUB is the LDO's output, which can supply 20 mA to outside loads (§4.2). Nothing
  outside U6 draws from it: the OVCUR# ties sit at the rail their own pull-ups go to.
- The datasheet warns that a device hot-plugged on a downstream port can dip the hub's 5 V
  into a low-voltage reset (§6.1). Here J2 and J3 take VBUS from J4, not from V5L.
- Not adopted: feeding V5 and VDD33 together from 3.3 V, which the datasheet recommends for
  industrial-grade and on-board hubs (§6.1, §6.4). U6 would then dissipate 280 mW, but V3V3
  would carry 131.6 mA and the AMS1117 0.224 W, a 20.1 °C rise at 90 °C/W, against 0.079 W
  and 7 °C now (§7.1). It would also put the hub on the MCU's rail.

---

## 7. Budgets and calculations

### 7.1 J1 (logic) power

| Load | Typical |
|---|---:|
| U6 CH335F (datasheet §4.2: HS upstream and 4 HS ports; 25 mA with 4 FS ports) | 85 mA |
| RP2040 and W25Q128JV flash with USB — an estimate | 30 mA |
| MAU104 input (6 × OP07 ≈ 15 mA out; 30 mA no-load input) | 70 mA |
| LM393 × 3, LEDs, AMS1117 I<sub>q</sub>, CJ431 × 2 | 15 mA |
| MCP3208 × 2 and the three SPI level-shifter pull-ups | 11 mA |
| **Total** | **≈ 0.21 A** |

V3V3 carries ≈ 47 mA, so AMS1117 dissipates (5.0 − 3.3) V × 47 mA = 0.079 W, a 7 °C rise at
90 °C/W. This closes OI-18 on this rail.

**U1's supply (D29 desk check).** Every 3.3 V pin of U1 and the flash U8 sit on V3V3
directly, as in Raspberry Pi's minimal design (§6.5). V3V3 is 3.251–3.349 V (AMS1117-3.3).
- USB_VDD needs 3.135–3.63 V; IOVDD, VREG_VIN and ADC_AVDD 1.62–3.63 V (RP2040 datasheet
  Table 634); U8 2.7–3.6 V (W25Q128JV). The tightest is USB_VDD's minimum, with 0.116 V to
  spare. The highest V3V3 leaves 0.281 V below the RP2040's 3.63 V maximum and 0.251 V below
  U8's; the 1.62 V minimum of IOVDD, VREG_VIN and ADC_AVDD has 1.631 V to spare, and U8's
  2.7 V minimum 0.551 V.
- The core (DVDD, 1.05–1.16 V) comes from U1's own linear regulator, which supplies up to
  100 mA. The largest DVDD current in the datasheet's measurements is 16.6 mA (Table 637,
  maximum column, the Popcorn demo), 6.0 × inside it, and the regulator then dissipates
  ≤ 37 mW inside U1. In the ROM bootloader (BOOTSEL active) it is 14.7 mA: 6.8 × and 33 mW.
- The HOLD pull-ups (§3.2) and U1's IO share V3V3, so they ramp together. That was also why
  D28 kept the module on V3V3.

D28 checked the PGA2040's on-module NCP115 running in dropout instead; that calculation left
with the module (D29).

**How J1's current is declared (D26, closes OI-25).**

- The CH335F stays **self-powered** (PSELF at its default) and declares its default 100 mA
  (MaxPower 0x32, its internal configuration without an EEPROM; §6.6). It takes 85 mA, inside the one unit load a self-powered hub may draw
  from upstream.
- It has to be self-powered: J2 and J3 are powered from J4. A bus-powered hub would offer
  its DUTs only 100 mA, so a host would refuse a DUT whose configuration asks for 500 mA.
- The RP2040 function takes the other 126 mA, or 172 mA with every OP07 at its maximum. It
  declares **bMaxPower 200 mA, bus-powered** (REQ-HOST-08).
- The declarations add up to 300 mA, against ≈ 0.21 A typical and ≈ 0.26 A with every OP07
  at its maximum supply current. But USB charges the upstream port only the hub's 100 mA:
  it counts the function's power against the self-powered hub's own supply.
- The board therefore needs an upstream port that supplies 500 mA, such as a PC port or a
  self-powered hub. It is not supported behind a bus-powered hub (`requirements/product.md`
  §9).

### 7.2 J4 (port) power and the port policy (D18; closes OI-16)

- Each port advertises **Default USB power** via Rp = 33 kΩ, which promises the DUT 500 mA.
- The hardware OC trip is at 1.16 A per port, and the measurement range is 1 A.
- **Advertisement rule (firmware, REQ-PWR-04):** a port is enabled only if (ports already
  ON + 1) × 0.5 A ≤ J4's advertised current (Default 0.5 A / 1.5 A / 3.0 A, read from
  U17 CH3/CH4). Otherwise `PORT x ON` returns `ERR 04`. A Default-only J4 therefore runs one
  port at a time, and the two ports together never advertise more than J4 can deliver
  (REQ-PWR-03).
- **Budget rule (firmware, REQ-PWR-05):** if the two ports' measured currents together exceed
  J4's advertised current for > 50 ms, the port drawing more is switched OFF and latched as
  `FAULT:BUDGET`. This catches a DUT that draws more than the 500 mA it was offered.
- `STATUS?` reports which advertisement J4 shows.
- **F1 (D25).** The most current F1 carries below the two OC trips is 2 × 1.16 A ≈ 2.33 A.
  F1 holds 3.00 A at 23 °C and 2.49 A at 40 °C ambient (Bourns derating chart), and it
  dissipates 0.43 W at 2.33 A and R1max. At 50 °C (2.31 A) both ports held just below
  their trips could trip F1. That failure is safe: both ports lose power, and firmware sees
  V_J4 fall.

### 7.3 Fail-safe

| Condition | Ports | Ladder | Rp | Discharge |
|---|---|---|---|---|
| MCU in reset / unprogrammed / in the ROM bootloader / J1 unplugged | OFF (EN_G pulled down) | HIGH (Q19/Q20 pulled up) or unpowered | Absent | ON (or unpowered) |
| J4 unplugged | No port power | — | Per EN | — |
| Firmware hung | Hold state, until watchdog reset (timeout ≤ 5 s, §4) → as row 1 | Hiccup between ranges | Per EN | Per EN |
| OC trip | OFF in hardware ≤ 10 µs | — | Until firmware drops EN | ON |

The bypass FETs default ON for the reason Rev0.2 gave: a stuck LOW range against a real load
starves the DUT and dissipates in a 0805.

### 7.4 What Rev0.3 and Rev0.4 gave up to meet D13 and D22

| Lost or reduced | Rev0.2 | Rev0.4 (Rev0.3 where different) | Recorded as |
|---|---|---|---|
| Regulated port voltage | 5.10 V | J4 voltage minus ≤ 0.40 V at 1 A (≤ 0.48 V with both ports at 1 A, F1 shared) | product.md §9 |
| Power from the host alone | PD 9 V from J1 | A second cable (J4) is required for port power | REQ-PWR-01 |
| Port voltage measurement and back-feed detection | ADC on VBUS_A/B | None (would be measured as load current); CYCLE discharge is timed | REQ-PORT-03, REQ-PORT-04 |
| Accuracy at the bottom of MID/HIGH | 24-bit | 12-bit: ≤ 7.8 % of reading at 14.9 mA | REQ-MEAS-05 |
| Sample rate | 31.25 kSPS | 14.0 kSPS, unaveraged (Rev0.3: 18.5 kSPS) | REQ-MEAS-08 |
| Hardware-only range latch | D4 | Firmware hold within 100 µs | D17 |
| ROM USB bootloader | RP2040 BOOTSEL | Regained: the RP2040 ROM bootloader (Rev0.3: a DFU bootloader in flash, written once over SWD) | REQ-BOOT-02 |
| ESD on D+/D− of J1–J3 | TPD4E05U06 | **None**; only the CH335F's on-chip protection remains, 6 kV HBM on its USB pins (datasheet §4.1) (Rev0.3: SRV05-4) | product.md §9 |
| Top-only assembly | All SMD by JLCPCB | Modules (the four USB-C modules and the MAU104), two DIP16 ADCs, R_H, R_M and F1 hand-soldered. The MCU is machine-placed again since D29 (it was a module under D23), and the hub since D31 (it was a module under D15) | REQ-MFG-01 |
| Basic parts only | — | Two Extended parts, the RP2040 (D29) and the CH335F (D31): two Extended feeder fees per order | REQ-MFG-05 |

---

## 8. Manual gates that ERC cannot cover

Checked by a human against the schematic; recorded in the release notes with a name and date.

| # | Gate | Verify | Expect |
|---|---|---|---|
| G1 | Bypass FET default state | Trace each gate net with MCU unpowered and J4 present | Q19/Q20 gates pulled to V3V3 by 10 kΩ (≥ 2.70 V at V3V3 min against the RP2040's 50 kΩ minimum reset pull-down, §3.2); with V3V3 absent the port switch is also off |
| G2 | Kelvin sense taps | Inspect R_H (4-pad land), R_M (sense at each lead pad), R_L | Force and sense joined only at the pad; sense traces carry no load current |
| G3 | Sense pair routing | Inspect each amp's +IN / R1 pair | Tight pair, over L2 GND, away from MAU104 and the hub (U6) |
| G4 | Analog ground | Inspect ground topology | ADC, amp outputs and VDDA return on a quiet region; no port load current under them |
| G5 | Rp gating | Trace J2/J3 CC | Rp sourced from EN_x only; no other path to V3V3 or VBUS |
| G6 | Rp value | Read the CC resistors | 33 kΩ (Default); no 22 kΩ or 10 kΩ anywhere on J2/J3 CC |
| G7 | Leakage on VBUS_x | List every net connection on VBUS_A/B | Port C, discharge FET drain path, LOW amp +IN via 10 kΩ, connector — nothing else |
| G8 | USB serial number | Inspect firmware descriptor path | From U8's 64-bit unique ID (instruction 4Bh); never a constant |
| G9 | Hub crystal | Y2 against CH335F built-in capacitors | Y2 frequency inside ±500 ppm on a built board |
| G10 | ESD coverage | Count protected lines | J1–J4 CC1, CC2 on PSM712; J1–J3 D+/D− unprotected by decision (D22) and listed as such in the release notes; J1/J4 VBUS on SMBJ6.5CA; SBU not connected (modules do not bring it out) |
| G11 | Comparator loop | Trace comparator → gate | No MCU in the up-range path; MCU only holds and releases |
| G12 | Shunt ratings | Datasheets | R_L ≥ 0.125 W for 47 mW stuck-LOW; R_M short-time overload ≥ 2.35 W for 10 ms (the MFU datasheet gives 6.25 W for 5 s, D28) |
| G13 | Port-enable ownership | Trace EN_x | Driven only by an RP2040 GPIO; U6's PWREN1–4# not connected; OVCUR1–4# tied to VDD33_HUB, inactive (§6.6) |
| G14 | Hub straps | U6 PSELF, PGANG, SCL/SDA | PSELF and PGANG not connected, so their internal pull-ups select self-powered (D26) and ganged mode, which is irrelevant (PWREN# unused); no EEPROM, so the internal configuration holds (§6.6) |
| G15 | 5 V signals into the MCU | RP2040 pin table and every net on a GPIO | No GPIO net can exceed 3.3 V: EVT through Q24/Q25 (Q44/Q45), DOUT through 10 kΩ / 15 kΩ, OC_x from EN_G_x through 100 kΩ, SCLK/CS/DIN driven through Q50–Q52 |
| G16 | Op-amp supply and pedestal | Trace V12F, V_INJ | V_INJ = 8 V from U4; six 1 MΩ to the six X nodes; no op-amp on V5L or V3V3 |
| G17 | Fast turn-off | Trace DIS_x → Q15 → Q16 | Q16 clamps gate to common source when EN_G_x is low |
| G18 | Through-hole side | Inspect footprints | Every Akizuki module, DIP and axial part is through-hole, soldered from Bottom; no SMD on Bottom |
| G19 | ADC supply and inputs | Trace U7/U17 | V<sub>DD</sub> = V5A, V<sub>REF</sub> = VDDA; every used input through 1 kΩ; CH5–CH7 to GND |
| G20 | U1 support circuit (D29) | Trace every U1 pin against §6.5; compare U1's land with the RP2040 datasheet's Figure 167 and U8's with the Winbond package drawing | 100 nF at each of the 10 power pins and 1 µF at pins 44 and 45, each at its pin; 22 Ω + 5.1 Ω in each of D+ / D− next to U1; Y1 with 2 × 15 pF and 1 kΩ on XOUT, on short traces; 1 kΩ from QSPI_SS to SW3 next to U8; TESTEN to GND; RUN to V3V3 through 10 kΩ; a 3.20 mm ePad; test pads on DVDD, RUN and the GPOUT clock pin |
| G21 | U6 support circuit (D31) | Trace every U6 pin against §6.6; compare U6's land with the CH334/335 datasheet's §5.6 drawing (QFN28_4X4X0.75-0.4) | 1 µF at V5, 100 nF + 10 µF at VDD33, each at its pin; VDD33_HUB not tied to V3V3, with a test pad; Y2 straight to XI/XO with no load capacitors; DMU/DPU to J1, DM1/DP1 to U1's resistors, DM2/DP2 to J2, DM3/DP3 to J3; port 4, RESET#/CDP, PWREN1–4#, PSELF, PGANG, SCL and SDA unconnected; OVCUR1–4# to VDD33_HUB; 0.4 mm pitch, 0.20 mm terminals and a 2.7 mm ePad to GND with vias |

---

## 9. Parts — moved, and the sourcing rule

The shortlist lives in `requirements/parts.md`. It is the single place for each part's class,
dated stock (JLCPCB assembly pool or Akizuki), datasheet facts and remaining checks.

**The D13 rule as applied:**

1. Small parts are machine-placed by JLCPCB and MUST be **Basic**, with assembly stock
   ≥ 500. All Basic parts here had ≥ 130,000 (2026-11-03; D29's additions on 2026-11-04).
2. Large parts are hand-soldered by the user and MUST be **in stock at Akizuki**. The
   thinnest is the MAU104, at 178 pcs on 2026-11-03. (The PGA2040, at 41, left with D29.)
3. No Extended part of any kind, Preferred Extended included (D22). Rev0.3's two Preferred
   Extended parts, STM32F103C8T6 (C8734) and SRV05-4 (C7420376), are removed. **Two
   exceptions, both the user's (2026-11-04):** the RP2040, C2040 (D29), with 5,845 in
   JLCPCB's assembly pool, and the CH335F, C5137013 (D31), with 4,937, both read on
   2026-11-04. Each costs one Extended feeder fee per order. D13's "never an Extended-only
   PCBA" still holds: 39 of the 41 machine-placed types are Basic. A third exception needs
   the user's decision.
4. Special or hard-to-source parts are avoided where an allowed alternative exists. The
   remaining single-source parts are the Akizuki modules and shunts. Since D29 the MCU, and
   since D31 the hub, are JLCPCB parts; their supply risk is C2040's and C5137013's assembly
   stock, which the order-time recheck covers (V-MFG-02).
5. Part types are pooled: one part per value, and one voltage rating per value. On
   2026-11-03 this removed four machine-placed types (42 → 38): 510 Ω 0402 (U3 feed now uses
   the 0805 R_L part), 20 kΩ (the V_J4 divider is now 33 k / 15 k, the U4 values), 10 µF 10 V
   (the 25 V part) and 100 nF 16 V (the 50 V part). Rev0.4 removes three more (38 → 35):
   C8734, C7420376 and C1562 (Y1's load capacitors). It adds none: the level shifters,
   dividers, pull-ups and V5A filter reuse 2N7002, 1.5 kΩ, 10 kΩ, 15 kΩ, 10 Ω and 10 µF.
   D29 adds five (35 → 40): C2040 (RP2040), C97521 (flash), C1548 (15 pF, Y1's load), and
   C25092 (22 Ω) and C25197 (5.1 Ω), the two halves of each 27 Ω USB resistor. Y1 reuses
   C9002 (Y2's part), and the decoupling, regulator capacitors, XOUT and BOOTSEL resistors and
   RUN pull-up reuse 100 nF, 1 µF, 1 kΩ and 10 kΩ. D31 adds one (40 → 41): C5137013
   (CH335F). Its V5 and VDD33 capacitors reuse 1 µF, 100 nF and 10 µF, and Y2 was already on
   the board.

**Rev0.3's strictly-Basic fallback became the design** (D22, D23), with one change of
module. Rev0.3 named the Akizuki g117542 kit or the Raspberry Pi Pico. Neither brings D+/D−
out to its pins, so neither can sit behind the CH335F. Rev0.4 used the PGA2040, which puts
USB_DP and USB_DM on pins (Pimoroni's schematic). Nucleo-32 boards bring D± out but leave too
few I/O. ESP32-S2 modules draw more J1 current and have no PIO to clock two ADCs in
lockstep with a stretched sample phase.

**D29 replaced the module with the bare chip.** The PGA2040 cost ¥1,680 per unit and had
the thinnest stock of any part (41 at Akizuki). The RP2040 itself, its flash, crystal and
passives are JLCPCB parts at a fraction of that, and one Extended feeder fee
(`design/experiments/cost-estimate/`). The RP2350A was reviewed for issue #3 as well and
rejected: its on-chip core regulator needs a shielded 3.3 µH inductor, which no Basic part
provides (the recommended one, C42411119, is Extended with 1 in stock), and no Basic or
Akizuki regulator makes an external 1.1 V instead. It would need at least two Extended parts.

**D31 replaced the hub module with the bare chip.** The module (AE-QFN28-DIP(CH335F),
Akizuki g129556, ¥420) was 38.5 × 10.2 mm of hand-soldered DIP30 on headers, with no
published outline or pin map (OI-24). The chip, C5137013, costs $1.1169 at JLCPCB's 1–9
tier (2026-11-04) plus a second Extended feeder fee ($3.07 per order). For the 2-unit
Economic order the total changes by −59 to −299 yen (`design/experiments/cost-estimate/`).

With no D± ESD part left, J1–J3 D+/D− are unprotected. CLAUDE.md §9 says not to remove ESD
protection. The user accepted this cost in D22, and it is recorded as a limitation (§7.4,
`requirements/product.md` §9). The CC lines keep PSM712 (Basic; 12 V standoff, but too much
capacitance for D±).

---

## 10. Decisions

Only decisions the user has made, the delegated ones, and their unavoidable consequences
appear here.

| # | Decision | Date | By | Closes |
|---|---|---|---|---|
| D1 | ~~Upstream is a USB-PD sink requesting 9 V~~ **SUPERSEDED by D14** — every PD sink part is Extended (D13) | 2026-08-16 | User | ~~OI-4~~ |
| D2 | ECAD tool is KiCad | 2026-08-16 | User | CLAUDE.md §10.4 |
| D3 | ~~3 ranges 20 mΩ / 2 Ω / 200 Ω~~ **SUPERSEDED by D17** (0.1 / 10 / 510 Ω) | 2026-08-16 | Rev0.1 design | OI-3 |
| D4 | Up-ranging is hardware (comparator → gate). **Amended by D17:** firmware holds the new range and does all down-ranging | 2026-08-16 | Rev0.1 design | OI-3 |
| D5 | ~~Sense topology B~~ **SUPERSEDED by D17** (topology C) | 2026-08-16 | Rev0.1 design | ~~OI-11~~ |
| D6 | ~~One shared 12 MHz oscillator~~ **SUPERSEDED** 2026-11-03 by D11, now by D19 | 2026-08-16 | Rev0.1 design | ~~OI-2~~ |
| D7 | Upstream control interface is CDC-ACM ×2 (control + stream), driverless | 2026-08-16 | User | — |
| D8 | ~~32 kSPS~~ **SUPERSEDED by D17**: 14.0 kSPS since D23 (Rev0.3: 18.5 kSPS) | 2026-08-16 | Rev0.1 design | — |
| D9 | Bypass FETs default ON (fail-safe to HIGH range) | 2026-08-16 | Rev0.1 design | — |
| D10 | Board outline ~~85 × 35 mm~~, **4 layers**. **Outline amended by D24** (100 × 72 mm) | 2026-11-03 | User | OI-13, OI-10 |
| D11 | ~~USB hub is USB2514B~~ **SUPERSEDED by D15** — every variant is Extended (D13) | 2026-11-03 | User | — |
| D13 | **Sourcing rule:** JLCPCB Basic parts in stock for machine-placed small parts; Akizuki parts in stock for large hand-soldered parts; never an Extended-only PCBA. Functions that cannot be built this way are reduced. Restated the same day as a list that adds: avoid special or hard-to-source parts, and reduce part types and count | 2026-11-03 | **User** | — |
| D14 | Port power from **J4, a power-only 5 V USB-C input** (Rd 5.1 kΩ, advertisement read by ADC); J1 = data + logic power; no PD, no buck. *Revert → reopens OI-4, OI-17* | 2026-11-03 | Claude (delegated) | OI-4, OI-17, OI-18 |
| D15 | Hub = **CH335F** on the Akizuki module, port 1 → MCU, 2 → J2, 3 → J3. **Amended by D31:** the bare chip (C5137013), machine-placed; the port assignment stands. *Revert → no allowed hub remains* | 2026-11-03 | Claude (delegated) | — |
| D16 | ~~MCU = STM32F103C8T6~~ **SUPERSEDED by D23** — Preferred Extended, ruled out by D22 | 2026-11-03 | Claude (delegated) | — |
| D17 | Measurement = topology C with OP07 + AO3401A current mirrors; ladder 0.1 / 10 / 510 Ω nested bypass; LM393 up-ranging; firmware hold ≤ 100 µs and down-ranging; 12-bit ADC (**amended by D23:** two MCP3208, 14.0 kSPS; was the STM32 dual ADC, 18.5 kSPS); pedestal injection. Supersedes D3, D5, D8; amends D4 | 2026-11-03 | Claude (delegated) | OI-19, OI-20, OI-22, OI-3 (re-closed) |
| D18 | Port path = back-to-back AO3401A, EN-sourced Rp 33 kΩ (Default), hardware OC at 1.16 A with fast turn-off, discharge at reset, firmware budget rule against J4's advertisement | 2026-11-03 | Claude (delegated) | OI-16, OI-7 (in part) |
| D19 | Clocks: Y2, a 12 MHz Basic crystal → CH335F. **Amended by D23:** Y1 (→ STM32) removed; the RP2040 module has its own crystal. **Amended by D29:** Y1 returns, C9002 → RP2040 XOSC (§6.3) | 2026-11-03 | Claude (delegated) | OI-2 |
| D20 | Accuracy target ±(1 % + 3 LSB of the active range), ±10 °C of calibration, after gain and zero calibration | 2026-11-03 | Claude (delegated) | OI-21 |
| D21 | Rev0.2 proposals adopted: P9 (≥ 18 mm port pitch; the 20 mm-wide modules side by side meet it), P10 (BOOT command + lid pinhole; **amended by D23:** the RP2040 ROM USB bootloader, where Rev0.3 had a flash DFU bootloader), P11 (TC2030-NL + test pads; SWD is now for debug only), P12 (heat-set M2 inserts, 4 corners) | 2026-11-03 | Claude (delegated) | OI-9 (design); OI-1, OI-5, OI-8 still need physical checks |
| D22 | **Basic parts only:** no Preferred Extended part either. STM32F103C8T6 and SRV05-4 are removed, accepting the costs Claude stated beforehand: an Akizuki RP2040 module plus a DIP ADC, a lower sample rate, and no D± ESD on J1–J3. The user answered 「うん、okだよ」 and then selected 「外して Basic のみにする」. Two exceptions since, both the user's: D29 (the RP2040) and D31 (the CH335F) | 2026-11-03 | **User** | OI-30 |
| D23 | MCU = **PGA2040** (RP2040 module, Akizuki); ADC = **2 × MCP3208-CI/P** (Akizuki DIP16) at V<sub>DD</sub> 5 V, sharing CLK/CS/DIN, sample phase stretched by the PIO, 14.0 kSPS with both ports sampled at once; PSM712 on J1–J3 CC, D± unprotected; RP2040 ROM USB bootloader; hold pull-ups 10 kΩ; level shifters on EVT and the ADC bus. Supersedes D16; amends D17, D19, D21. **Amended by D29:** the MCU is a bare RP2040 (C2040), no longer the PGA2040; the ADC part of D23 stands. *Revert → no Basic-only MCU remains; reverting D22 instead restores Rev0.3* | 2026-11-03 | Claude (delegated) | — (opens OI-31) |
| D24 | Board outline **100 × 72 mm**, 4 layers; amends D10's 85 × 35 mm. The OI-23 study (`design/experiments/oi-23-placement/`) shows that Rev0.4 needs at least 3,715 mm² (no routing space, every low part credited under a module; 3,780 mm² once D25 added F1), against 2,975 mm². The user's condition, 「100x100未満ならいいんだっけ」, is that the outline stays within JLCPCB's 100 × 100 mm base price tier. JLCPCB instant quote, 2026-11-03, 4 layers, 5 pcs, default options: $8.00 at 85 × 35, 100 × 72 and 100 × 100 mm; $30.80 at 130 × 72 mm (a $25 engineering fee appears). ENIG adds $16.90 at 85 × 35 and $17.40 at 100 × 72 mm. The size inside the tier is Claude's choice. *Revert → no 85 × 35 layout exists; a smaller outline needs a new study run* | 2026-11-03 | **User** (condition) + Claude (delegated, size) | OI-23 (area only; outlines still open) |
| D25 | **J4 input fuse F1 = Bourns MF-R300** (Akizuki g112630), ahead of D6. 3.00 A hold (2.49 A at 40 °C) against the 2.33 A the OC trips allow; 6.00 A trip; 30 V, so a wrong supply up to 30 V that D6 crowbars trips F1. Cost: R1max 0.08 Ω adds up to 0.16 V of drop with both ports at 1 A, which cuts the HIGH mirror's gate headroom to 0.03 V in the J4 = 4.75 V corner (OI-27, V-MEAS-00; **D28:** 1.63 V against TI's single-supply row, §3.2). Fallbacks if the bench check (since D28, V-MEAS-00 at bring-up) fails: firmware flags HIGH readings while V_J4 (measured after F1) is below the measured limit, or revert D25. Rejected: relying on the source's own protection, because a hand-soldered board can short upstream of the port OC. *Revert → OI-29 reopens; no other Akizuki PTC has a datasheet with resistance figures at hand* | 2026-11-03 | Claude (delegated) | OI-29 |
| D26 | **J1 power declaration.** The CH335F stays self-powered (PSELF default, 100 mA), because J2 and J3 are powered from J4: as a bus-powered hub it would offer DUTs only 100 mA. The RP2040 function declares bMaxPower 200 mA, bus-powered, against its 126 mA typical, 172 mA with every OP07 at its maximum. The board is specified for upstream ports that supply 500 mA, not for bus-powered hubs. Rejected: (a) raising the hub's MaxPower through the CH335F EEPROM, since a self-powered hub may draw only one unit load from upstream, so a larger figure is itself non-compliant, and it adds a part; (b) feeding the MCU and analog from J4. That is compliant, but it removes the COM port whenever J4 is absent. It also takes ≈ 0.13 A out of J4's advertisement, so a Default-only J4 could run no port (REQ-PWR-04), and it cuts F1's 40 °C hold margin from 0.16 A to ≈ 0.03 A. *Revert → OI-25 reopens with (a) and (b)* | 2026-11-03 | Claude (delegated) | OI-25 |
| D27 | **Stackup JLC04161H-7628**, named on the order ("Specify Stackup: Yes"): 1 oz outer, 7628 prepreg 0.2104 mm (Dk 4.4) between L1 and L2, 1.065 mm core, 1.5862 mm in total; the layer use stays CLAUDE.md §5.1's. On the quote page (browser, 2026-11-03) it was the only one of 18 named 4-layer stackups without the note "This is a special stackup, and it doesn't support economic PCB assembly", naming it left the PCB price at $25.40, and "No requirement" shows the same build. **USB 2.0 pair: W = 0.31 mm, S = 0.15 mm on L1 over L2**, 90.4 Ω in the bare Hammerstad–Jensen + Kirschning–Jansen model at the published Dk (99.7 / 82.8 Ω at W −/+20 %, S held). The model reproduces JLCPCB's own single-ended 50 Ω width to +2 %, but JLCPCB's differential calculator returned no result, so the geometry is **provisional**: rerun that calculator (or ask JLCPCB) for 90 Ω at S = 0.15 mm before routing, and use its width. Study: `design/experiments/stackup-impedance/`. **Impedance control is not ordered for the prototype.** It costs $33.08 plus an auto-selected $1.05 "Confirm Production file" ($59.53 instead of $25.40). It controls only the board segment, while D± also pass through Akizuki modules and 2.54 mm headers (OI-26), and FS is the documented fallback (REQ-HOST-07). Its effect on the Economic PCBA class is also unseen. Rejected: the other 17 named stackups (the special-stackup note); 7628C/F also reach no 90 Ω width within 0.60 mm. *Revert → the order says "No requirement", which shows the same build but names nothing. Reopen impedance control if V-HOST-01's HS test fails and the fault is traced to the board-level pair, or if a later revision routes D± without the modules and headers* | 2026-11-03 | Claude (delegated) | — (CLAUDE.md §5.1 stackup ID) |
| D28 | **No pre-layout bench: desk checks now, the first PCBA prototype confirms.** The bench kit of issue #1 is not bought. The user: 「試験キットは買わない、基板で確かめる。君が机上で確認すればいい」. The assumptions it was to check are desk-checked from datasheets (§3.2, §4, §7.1; `CIRCUIT_DESIGN_Rev0.4_calc.py`), and V-MEAS-00 and V-MEAS-06 move to bring-up. **Settled on paper:** the OP07 common mode and output low limit (TI's single-supply gain row; gate headroom 1.63–1.96 V, was 0.03–0.36 V); R_M's survival of the stuck-MID fault (6.25 W for 5 s rating); the PGA2040's supply input, 27 Ω pair and flash unique ID; U1 on V3V3; the reset hold. **Not settled on paper, accepted as bring-up risk:** the mirror loop's stability, R_M's < 0.1 % shift after the fault, the MCP3208's INL at V<sub>REF</sub> 3.3 V and its stretched sample. A failure there costs a board revision instead of a bench rebuild. Not covered by D28: the CH335F module's outline (OI-24), which needed the module itself before layout; D31 removed the module and closes OI-24. *Revert → the kit is in Git at commit 609bfb7 (`tests/fixtures/pre-layout-bench/`), and OI-27, OI-28, OI-31 reopen as bench checks.* (D29 removed the PGA2040, so its three items here are superseded by D29's own desk check: §3.3, §6.3, §7.1.) | 2026-11-04 | **User** | OI-27, OI-28, OI-31 |
| D29 | **MCU = a bare RP2040 (C2040, Extended, LQFN-56), machine-placed by JLCPCB: an exception to D22 (the second is D31).** Replaces D23's PGA2040. The support circuit follows Raspberry Pi's minimal design (§6.5): U8 W25Q128JVSIQ (C97521); Y1 C9002 with 2 × 15 pF and 1 kΩ in XOUT (§6.3); 27 Ω per USB line as 22 Ω + 5.1 Ω (§3.3); 100 nF per power pin and 1 µF at VREG_VIN and VREG_VOUT; SW3 to QSPI_SS through 1 kΩ; RUN to V3V3 through 10 kΩ; TESTEN to GND. Machine-placed types 35 → 40; the hand-soldered PGA2040 (¥1,680, 41 in stock) goes. The user asked 「このPGAてさ生のRP2040より高くない?」, accepted a larger redesign with 「いいよ、大きな設計変更になってもいいよ」, and selected 「素の RP2040 (推奨)」. Costs: one Extended feeder fee per order; a 0.4 mm-pitch QFN with a non-standard ePad to draw (G20); a crystal other than Raspberry Pi's recommendation, checked on the first boards (V-MEAS-06). *Revert → D23's PGA2040 returns (Git commit `6774bc5`), and D31 is D22's only exception* | 2026-11-04 | **User** | — (amends D19, D23) |
| D30 | **Surface finish: leaded HASL, not ENIG.** Asked about the JLCPCB cost, the user wrote 「ENIGいらないよ、」. Claude named the risk and offered leaded HASL, lead-free HASL or ENIG, and the user selected 「有鉛 HASL (推奨)」. The 5 PCBs cost $8.00 instead of $25.40 (quote of 2026-11-03). **Risk accepted:** HASL is not flat. U1 (RP2040, 0.4 mm-pitch LQFN-56 with an ePad, D29) is the part it affects; when D30 was made, the next finest pitch on the board was SOT-23's 0.95 mm. A bridged or open U1 joint costs a rework or a board. V-MFG-03 inspects U1 on the first boards. **Amended by D31:** U6 (CH335F, 0.4 mm-pitch QFN-28 with an ePad) is a second such part, and V-MFG-03 inspects it too. The board is not RoHS-compliant. Whether green mask, 1.6 mm and leaded HASL form an Economic PCBA combination is as unconfirmed as it was with ENIG. *Revert → ENIG, +$17.40 per 5 PCBs; CLAUDE.md §9's ENIG text is at commit `4a04218`* | 2026-11-04 | **User** | — (changes CLAUDE.md §9's ENIG assumption) |
| D31 | **Hub = a bare CH335F (C5137013, Extended, QFN-28 4 × 4 mm), machine-placed by JLCPCB: a second exception to D22.** Replaces D15's Akizuki module, AE-QFN28-DIP(CH335F) (g129556). The support circuit follows the WCH datasheet (§6.6): 1 µF at V5; 100 nF + 10 µF at VDD33, on its own net VDD33_HUB; Y2 straight to XI/XO; OVCUR1–4# tied inactive; every other control pin unconnected. Machine-placed types 40 → 41, with no new passive type. Asked what to buy from Akizuki, the user asked 「ええ、CH335FはLCSCに在庫無いの?」 and 「こんなモジュール実装するのデカくない?」; offered the bare chip against the module, the user selected 「IC 単体にする (推奨)」. Gains: the 38.5 × 10.2 mm module and one header strip per board go (hand-soldered area 2,198 → 1,806 mm²); OI-24 closes, because the datasheet gives the package drawing and the pin table; each HS path crosses one module and header instead of two (OI-26). Costs: a second Extended feeder fee per order ($3.07); a second 0.4 mm-pitch QFN with an ePad on leaded HASL (D30, V-MFG-03) and a land to draw (G21); V5's operating range has no margin against V5L's (§6.6), as it had on the module. The 2-unit Economic total changes by −59 to −299 yen. *Revert → D15's module returns (its record is at Git commit `3e11f68`), OI-24 reopens, and D29 is D22's only exception* | 2026-11-04 | **User** | OI-24 (amends D15, D30) |

D12 was withdrawn on 2026-11-03 and is not reused.

---

## 11. OI-13 / OI-23 — Board area. **D10's 85 × 35 mm is amended by D24 (2026-11-03): 100 × 72 mm, 4 layers.**

Rev0.2's option study (in Git history, commit `4e59607`) assumed an all-SMD board at 36 %
density. Rev0.3 and Rev0.4 moved the large parts onto Akizuki modules and DIP packages, and
the OI-23 placement study (`design/experiments/oi-23-placement/`, run with `python -I`)
counted the result:

- **Hand-soldered parts: 1,806 mm².** Four USB-C modules at 20 × 15 mm, two DIP16 at
  9.8 × 20.85 mm, the MAU104 at 20 × 6.6 mm and the F1 fuse at 13 × 5 mm (D25). Until D29
  the PGA2040 added 21 × 21 mm, and until D31 the CH335F module 38.5 × 10.2 mm (measured off
  a photo, OI-24).
- **SMD courtyards: 1,850 mm²,** including the two hand-soldered shunts per port (133 mm²);
  since D29 U1, U8, Y1 and their passives in a 23 × 21.5 mm region where the PGA2040 sat;
  and since D31 U6, Y2 and U6's capacitors in R_HUB, the 10.2 × 38.5 mm strip where the
  CH335F module sat. Rev0.4 as first written had estimated 1,100–1,200 mm² without counting;
  the count gives 1,717 mm² without the shunts (1,695 mm² before D31, 1,516 mm² before D29).
- **Space under raised modules: 519 mm²,** for parts up to 1.5 mm tall: 130 mm² under each
  USB-C module. The parts that low would fill 1,116 mm² even at K = 1.0, so the bound
  credits all 519 mm². The CH335F module's 184 mm² left with it (D31).

With the four mounting-hole keepouts, the board needs at least 3,332 mm² with no routing
space at all (K = 1.0), and 4,426 mm² at the planning value K = 1.6 (3,518 and 4,599 mm²
before D31; 3,780 and 4,754 mm² before D29). The 85 × 35 mm board has 2,975 mm², so no layout of it exists. D24 sets
100 × 72 mm (7,200 mm²), where the study's block placement passes every check: board bounds,
clearances, region capacity at K = 1.6 (headroom to K = 1.74), connector edges, a 28 mm
J2–J3 pitch, the MAU104 ≥ 6 mm from the analog parts, and a USB corridor that runs in front
of the front ends rather than through them. Neither the Full-Speed link from U6 to U1 nor
the upstream pair from J1 to U6 has a corridor of its own in the study.

What stays open is in OI-23 (CLAUDE.md §11): the header height. The measured CH335F outline
left with the module (D31). The study does not route; capture and layout do.

---

## 12. What must happen before KiCad capture

Status as of 2026-11-04 (D28, D29, D31). OI-30 is closed by D22; OI-27, OI-28 and OI-31 by
D28; OI-24 by D31.

1. ~~**OI-24**: measure the CH335F module's outline and DIP30 pin map.~~ Closed by D31: the
   module is gone, and the bare chip's package drawing and pin table are in its datasheet
   (§5.6, Table 1-3). **D31's item instead:** draw U6's QFN-28 land from that drawing
   (0.4 mm pitch, 0.20 mm terminals, 2.7 mm ePad) rather than a stock footprint (G21,
   CLAUDE.md §4.2). **The OI-23 remainder:** the board area is settled (D24, §11); choose the
   USB-C module headers and their height, enter it in
   `design/experiments/oi-23-placement/placement_study.py` (its 1.5 mm under-module rule),
   and re-run it: it must still exit 0.
2. ~~**OI-31**: confirm the PGA2040's supply input, USB series resistors and flash.~~ Settled
   on paper by D28, then superseded by D29: the PGA2040 is gone, so there are no module pad
   positions to check. **D29's item instead:** draw U1's LQFN-56 land from the RP2040
   datasheet's Figure 167 (the reduced 3.20 mm ePad) rather than a stock QFN-56 footprint,
   and U8's from the Winbond package drawing (G20, CLAUDE.md §4.2).
3. ~~**OI-25**: decide how J1's 0.21 A is declared.~~ Closed by D26.
4. ~~**OI-29**: choose the J4 input fuse.~~ Closed by D25 (F1 = MF-R300).
5. ~~Bench-check the assumptions this design rests on, before layout.~~ Replaced by D28: the
   desk checks are in §3.2, §4 and §7.1. V-MEAS-00 and V-MEAS-06 run on the first board, so
   **capture adds test pads** for them: on the HIGH mirrors' OP07 outputs (U10, U20) and FET
   gates (Q21, Q41), on the HOLD gates (Q19, Q20, Q39, Q40), and on the V_J4 divider tap
   (U7 CH4), which V-MEAS-06's ADC sweep reads against the DMM. D29 adds three: DVDD, RUN,
   and the GPOUT clock pin (§6.4). D31 adds one: VDD33_HUB (§6.6).
6. Recheck all stock immediately before upload and again before payment (CLAUDE.md §4.1).

---

## 13. Change log

| Rev | Date | Change |
|---|---|---|
| 0.1 | 2026-08-16 | Opened. D1–D9 closed. OI-2/3/4/11 closed by decision. OI-13 (board area) opened as blocking. No part confirmed; no capture started. |
| 0.2 | 2026-11-03 | D10 (85 × 35 mm, 4 L) and D11 (USB2514B) by the user; D6 superseded, replacement clocks proposed (P13). OI-13, OI-10 closed; OI-2 reopened. Corrected §3.1, §3.2, §7.1, §7.3, G12. Added §4.1 noise, §6.3 clocks, G13–G15, Section 14 proposals. Shortlist moved to `requirements/parts.md`. OI-16 – OI-22 opened. |
| 0.3 | 2026-11-03 | D13 (sourcing rule) by the user, with the open choices delegated. Redesigned from Basic and Akizuki parts: J4 power-only input (D14), CH335F (D15), STM32F103C8T6 (D16), discrete current-mirror topology C with 0.1 / 10 / 510 Ω and pedestal injection (D17), back-to-back port switch (D18), two 12 MHz crystals (D19), accuracy target (D20), proposals P9–P12 adopted (D21). D1, D3, D5, D8, D11 superseded; D4 amended. OI-2, 4, 7 (part), 9, 16–22 closed by decision; OI-23 – OI-30 opened. Still no capture. |
| 0.4 | 2026-11-03 | D22 (Basic parts only, no Preferred Extended) by the user closes OI-30. MCU and ADC redesigned (D23): PGA2040 RP2040 module and two MCP3208 DIP16 ADCs at V<sub>DD</sub> 5 V, 14.0 kSPS; SRV05-4 removed, PSM712 on J1–J3 CC, D± unprotected; Y1 removed; ROM USB bootloader; hold pull-ups 10 kΩ; EVT and ADC-bus level shifters. D16 superseded; D8, D17, D19, D21 amended. OI-31 opened. Machine-placed part types 38 → 35. Still no capture. |
| 0.4 | 2026-11-03 | Amended: D24 (user condition, Claude's size) sets the board outline to 100 × 72 mm, 4 layers, amending D10, from the OI-23 placement study. §11 rewritten with counted areas; §12 item 1 and fact 9/17 updated. No circuit change. |
| 0.4 | 2026-11-03 | Amended: D25 (Claude, delegated) adds F1, an MF-R300 resettable fuse ahead of D6, and closes OI-29. §3.1 path and port-voltage table, §3.2 gate headroom, §6.2, §7.2 and §12 updated; F1 added to the OI-23 study. Machine-placed types unchanged (35). |
| 0.4 | 2026-11-03 | Amended: D26 (Claude, delegated) sets how J1's current is declared and closes OI-25: the hub stays self-powered at 100 mA, the RP2040 function declares 200 mA, and bus-powered upstream hubs are unsupported. §7.1, G14 and §12 updated. No circuit change. |
| 0.4 | 2026-11-03 | Amended: D27 (Claude, delegated) names the stackup JLC04161H-7628 and sets the provisional USB 2.0 pair at W 0.31 / S 0.15 mm, without impedance control for the prototype, from the stackup-impedance study. Fact 18 and §3.3 updated. No circuit change. |
| 0.4 | 2026-11-04 | Amended: D28 (user) replaces the pre-layout bench with desk checks and closes OI-27, OI-28 and OI-31 by decision; OI-24 stays open. §3.2 (OP07 output low from the single-supply row, headroom 1.63–1.96 V; loop stability left to bring-up; reset hold), §3.3 (27 Ω pair on the module, flash unique ID), §4 (R_M ratings; watchdog ≤ 5 s), §6.1, §7.1 (U1 on V3V3 with the module's NCP115 in dropout), §7.3, G12, §12 and facts 11 and 15 updated. No circuit change; §12 adds test pads to the capture list. |
| 0.4 | 2026-11-04 | Amended: D29 (user) replaces the PGA2040 module (D23) with a bare RP2040 (C2040), machine-placed, the one Extended part. Added U8 flash, Y1, 22 Ω + 5.1 Ω per USB line, decoupling, BOOTSEL and RUN networks (§6.5) and G20; D19, D23 and D28 amended. §1–§3.3, §6.1–§6.5, §7.1, §7.4, §8, §9, §11, §12 and §14 updated. Machine-placed types 35 → 40 (39 Basic + C2040). Still no capture. |
| 0.4 | 2026-11-04 | Amended: D30 (user) sets the finish to leaded HASL instead of ENIG; V-MFG-03 inspects U1's joints for the risk it accepts. No circuit change. |
| 0.4 | 2026-11-04 | Amended: D31 (user) replaces the CH335F module (D15) with the bare CH335F (C5137013), machine-placed, the second Extended part, and closes OI-24. Added §6.6 (U6 support circuit, the VDD33_HUB net), fact 19 and G21; D15, D22, D28, D29 and D30 amended. Header, §1, §2, §3.1, §3.3, §6.1–§6.3, §6.5, §7.1, §7.4, §8, §9, §11, §12 and §14 updated; the placement study and the cost estimate re-run. Machine-placed types 40 → 41 (39 Basic + C2040 + C5137013). Still no capture. |

---

## 14. Rev0.2 proposals — resolution

Rev0.3 and Rev0.4 open no new proposals: under the delegation, Claude's choices are
recorded in Section 10 instead.

| # | Rev0.2 proposal | Outcome (Rev0.4) |
|---|---|---|
| P1 | CH224Q PD sink | Withdrawn — Extended; no PD (D14) |
| P2 | SY6280AAC load switch | Withdrawn — Extended; back-to-back AO3401A (D18) |
| P3 | MCU sole owner of EN; Rp gated by EN; hub PRTPWR not connected | **Adopted** in D18 (Rp is now *sourced* from EN; CH335F PWREN# not connected) |
| P4 | Topology C | **Adopted** in D17, with discrete mirrors instead of INA190 |
| P5 | 3.3 V rail from a buck or SOT-223 LDO | Superseded — AMS1117-3.3 (SOT-223) from 5 V J1 (§7.1) |
| P6 | ADS131M02 CLKIN from RP2040 | Withdrawn — the ADS131M02 is Extended. Rev0.4's MCP3208s are clocked by the RP2040 PIO instead |
| P7 | RP2040 ADC on VBUS_A/B, VPD, V5P1 | Withdrawn — VBUS_x is not measured (§3.1); V_J4 is (U7 CH4) |
| P8 | Active bypass gate drive | Superseded — LM393 sink + 1 MΩ return + firmware hold (§3.2) |
| P9 | J2–J3 pitch ≥ 18 mm | **Adopted** (D21) |
| P10 | BOOTSEL via pinhole + `BOOT` command | **Adopted** (D21); since D23 as proposed, with the RP2040 ROM bootloader |
| P11 | TC2030-NL SWD + test pads | **Adopted** (D21); test pads now on VBUS_IN, VSUP_A/B, VBUS_A/B, V5L, V5A, V12F, V_INJ, V3V3, VDDA, GND, since D29 DVDD, RUN and the GPOUT clock pin, and since D31 VDD33_HUB |
| P12 | Heat-set M2 inserts, 4 corners | **Adopted** (D21) |
| P13 | Y1 12 MHz + Y2 24 MHz | Replaced — Y1 and Y2 are both 12 MHz C9002: Y2 → CH335F (D19), Y1 → RP2040 (D29; D23 had removed Y1) |
