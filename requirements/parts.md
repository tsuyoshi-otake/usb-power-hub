# USB Power-Control Hub — Parts Selection and Sourcing Record

**State: WIP. No part is chosen.** First pass 2026-11-03. Every row is a *candidate* until a
reviewer marks it confirmed against the actual PCBA order (CLAUDE.md Section 4.1).

This is the single place for candidates, assembly-pool stock and datasheet facts. The circuit
document (`design/circuit/CIRCUIT_DESIGN_Rev0.2.md`) derives the constraints; this file records
which parts meet them.

## How the numbers were obtained

- **Stock and class:** `python tools/jlc_stock.py <LCSC numbers or MPNs>` on 2026-11-03 (UTC).
  The tool queries the JLCPCB **assembly-parts** pool, which is the authoritative one; LCSC
  retail stock is a different pool (CLAUDE.md §4.1, easy-stick lesson 14.8). Its docstring
  lists what it cannot see — chiefly: electrical suitability, stock at order time, footprints.
- **Datasheet facts:** text extracted from the manufacturer PDF that the same API links
  (`dataManualFileAccessIdUrl`), 2026-11-03. Only parameters marked *verified* were read; a
  part's other properties are unconfirmed.
- **Recheck** immediately before upload and again before payment (CLAUDE.md §4.1):

```
python tools/jlc_stock.py C46061833 C42459160 C970725 C43590 C3200405 C111875 C109322 C2864583 C78988 C6186 C485517 C2862740 C80670 C2040 C2843335 C2999380 C97521 C58940 C16251 C220679 C2922448 C5215160 C5121509 C5215171 C3658008 C654763 C2673338 C2870223 C1852074 C2869854 C478075 C48618 C55136 C55266 C2864845 C111356 C2865523 C1517429 C3985410 C105360 C3997408 C865287 C9002 C70590 C138714 C7519
```

Class: **Basic** / **Preferred Extended** / **Extended**, as the API reports it. Stock below
**500** is flagged ⚠ (CLAUDE.md §4.1 floor for commodity passives, applied here to every part
as a warning level).

---

## Power

### U1 — USB-PD sink

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| CH224Q | C46061833 | DFN-10-EP (2 × 2) | 16,744 | Extended | 2026-11-03 | **Candidate** (P1) |
| CH224A | C42459160 | ESSOP-10 | 9,106 | Extended | 2026-11-03 | Alternate, same I2C map |
| CH224K | C970725 | ESSOP-10 | 0 ⚠ | Extended | 2026-11-03 | **Rejected** — no stock; no current readback |

- *Verified (CH224Q/CH224A datasheet):* 400 kHz I2C, 7-bit address 0x22 or 0x23; enabled when
  the part is in single-resistor configuration. Registers: 0x09 protocol status, 0x0A voltage
  request, **0x50 maximum available current at the current PD level (50 mA units, valid only
  after a PD handshake)**, 0x60–0x8F full source capability data.
- *To confirm:* CC and VBUS pin voltage ratings; what the part reports for a non-PD source
  (REQ-PWR-02 needs the Type-C current level then).

### U2 — V5P1 regulator (topology depends on OI-17, rating on OI-16)

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| TPS62130RGTR | C43590 | QFN-16-EP (3 × 3) | 23,099 | Extended | 2026-11-03 | Buck candidate |
| TPS62933DRLR | C3200405 | SOT-583 | 23,878 | Extended | 2026-11-03 | Rev0.1 candidate — not recommended |
| SY8205FCC | C111875 | SOIC-8-EP | 13,406 | Extended | 2026-11-03 | Rev0.1 candidate — not checked |
| TPS63070RNMR | C109322 | VQFN-15-HR (2.5 × 3) | 24,738 | Extended | 2026-11-03 | Buck-boost candidate (OI-17) |
| TPS55288RPMR | C2864583 | VQFN-26-HR (3.5 × 4) | 4,270 | Extended | 2026-11-03 | Buck-boost alternate (OI-17) |

- *Verified:* TPS62130 — up to 3 A continuous, **100 % duty-cycle mode** (datasheet §9.4.3).
  TPS62933 — no 100 % duty-cycle mode found in the datasheet text. TPS63070 — V<sub>IN</sub>
  2.0–16 V once started (V<sub>OUT</sub> ≥ 3 V); **I<sub>OUT</sub> 2 A** when V<sub>IN</sub> or
  V<sub>OUT</sub> ≥ 4.5 V and V<sub>OUT</sub>/V<sub>IN</sub> ≤ 1; 3.6 A switch. TPS55288 — 36 V,
  16 A buck-boost with I2C.
- *Constraint (Rev0.2 §7.1):* ≥ 2.2 A at V5P1 for 2 × 1 A plus rails; ≥ 3.2 A if both ports may
  draw 1.5 A (OI-16). TPS63070's 2 A is short of 2.2 A. *To confirm:* efficiency at the actual
  operating point; inductor size and saturation current.

### U3 — V3P3 digital (OI-18)

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| SY8089AAAC | C78988 | SOT-23-5 | 20,137 | Extended | 2026-11-03 | Buck option (P5) — not checked |
| AMS1117-3.3 | C6186 | SOT-223 | 1,747,814 | Basic | 2026-11-03 | LDO option (P5) — not checked |
| TLV75733PDBVR | C485517 | SOT-23-5 | 27,169 | Extended | 2026-11-03 | Not recommended: SOT-23-5 from V5P1 at 190 mA |

- *Constraint (Rev0.2 §3.1):* 190 mA from V5P1. A linear regulator dissipates 0.34 W; at
  ~187 °C/W (SOT-23-5) that is a 64 °C rise. *To confirm for each option:* θ<sub>JA</sub>,
  dropout at 5.10 V, stability with ceramic output capacitors.

### U3B — V3P3A analog

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| TPS7A2033PDBVR | C2862740 | SOT-23-5 | 133,199 | Extended | 2026-11-03 | **Candidate** |
| LP5907MFX-3.3/NOPB | C80670 | SOT-23-5 | 61,765 | Extended | 2026-11-03 | Alternate — not checked |

- *Verified:* TPS7A20 R<sub>θJA</sub> 187.1 °C/W (DBV). At ≤ 10 mA from V5P1: 18 mW, 3.4 °C rise.
- *To confirm:* output noise; PSRR at the U2 switching frequency.

## Digital

| Ref | MPN | LCSC | Package | Stock | Class | Checked | Role / note |
|---|---|---|---|---:|---|---|---|
| U4 | RP2040 | C2040 | LQFN-56 (7 × 7) | 7,060 | Extended | 2026-11-03 | MCU (fixed by architecture) |
| U5 | W25Q16JVUXIQ | C2843335 | USON-8-EP (2 × 3) | 450 ⚠ | Extended | 2026-11-03 | Rev0.1 size; thin stock |
| U5 | W25Q32JVUUIQ | C2999380 | USON-8 (3 × 4) | 2,151 | Extended | 2026-11-03 | Alternate |
| U5 | W25Q128JVSIQ | C97521 | SOIC-8-208mil | 76,583 | Basic | 2026-11-03 | Alternate; larger footprint |

### U6 — USB hub (D11)

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| USB2514BI-AEZG-TR | C58940 | TQFN-36-EP (6 × 6) | 6,527 | Extended | 2026-11-03 | **Candidate** (−40 to +85 °C) |
| USB2514B-AEZC-TR | C16251 | VQFN-36-EP (6 × 6) | 11,727 | Extended | 2026-11-03 | Alternate (0 to +85 °C) |
| USB2514B-I/M2 | C220679 | SQFN-36-EP (6 × 6) | 2,287 | Extended | 2026-11-03 | Alternate |

- *Verified (DS00001692A):* 24 MHz crystal or external 24 MHz clock. Configured Hi-Speed supply
  current 70 mA typ / 85 mA max (USB2514Bi, base current with one downstream port), plus an
  increment per additional port. Individual or ganged port power. **PRTPWR is asserted as soon
  as hardware configuration completes**, and PRTPWR[x]/BC_EN[x] pins are sampled as
  battery-charging straps — hence G13/G14 and P3.
- *To confirm:* the per-additional-port increment; strap levels; RBIAS value.

### Clocks (D12)

| Ref | MPN | LCSC | Package | Stock | Class | Checked | Note |
|---|---|---|---|---:|---|---|---|
| Y1 | X322512MSB4SI (12 MHz) | C9002 | SMD3225-4P | 302,846 | Basic | 2026-11-03 | RP2040 XOSC. *To confirm:* C<sub>L</sub>, ESR against the RP2040 hardware design guide |
| Y2 | X322524MOB4SI (24 MHz) | C70590 | SMD3225-4P | 168,790 | Extended | 2026-11-03 | USB2514B. *To confirm:* C<sub>L</sub>, total tolerance inside USB's ±500 ppm |

## Analog front end

### U7 — ADC

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| ADS131M02IPWR | C2922448 | TSSOP-20 | 8,840 | Extended | 2026-11-03 | **Candidate** |
| ADS131M02IRUKR | C5215160 | WQFN-20 (3 × 3) | 6,398 | Extended | 2026-11-03 | Smaller alternate |
| ADS131M04IRUKR | C5121509 | WQFN-20 (3 × 3) | 8,102 | Extended | 2026-11-03 | 4-channel, not proposed |
| ADS131M06IRSNR | C5215171 | QFN-32 (4 × 4) | 1,362 | Extended | 2026-11-03 | Needed if OI-19 chooses topology C |

- *Verified (ADS131M02):* **external CLKIN required**, 0.3 – 8.4 MHz in high-resolution mode
  (8.192 MHz nominal), data rate up to 64 kSPS; internal reference 1.2 V, drift 7.5 typ /
  **20 max ppm/°C**. Rev0.1's "QFN-24" package was wrong — the parts are TSSOP-20 / WQFN-20.

### U11 / U21 — current-sense amplifier

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| INA190A2IDCKR | C2870223 | SC-70-6 | 3,136 | Extended | 2026-11-03 | **Candidate** (G = 50) |
| INA190A2IDDFR | C1852074 | TSOT-23-8 | 631 | Extended | 2026-11-03 | Alternate package |
| INA186A2IDDFR | C2869854 | TSOT-23-8 | 37,724 | Extended | 2026-11-03 | **Rejected** — drift |

- *Requirements (Rev0.1 §4, Rev0.2 §5):* offset ≤ 25 µV, drift ≤ 0.1 µV/°C, I<sub>IB</sub> ≤ 3 nA,
  common mode covering 5.1 V.
- *Verified (INA190):* V<sub>OS</sub> ±15 µV max; drift 10 typ / **80 max nV/°C**;
  I<sub>IB</sub> 0.5 typ / **3 max nA**; V<sub>CM</sub> −0.2 to 40 V; gain-error drift 7 ppm/°C max;
  noise 75 nV/√Hz RTI. Meets all four.
- *Verified (INA186):* drift 0.05 typ / **0.5 max µV/°C** — fails the 0.1 µV/°C requirement.

### U10 / U20 — sense mux (only if topology B is kept, OI-19)

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| TMUX6209PWR | C3658008 | TSSOP-16 | 225 ⚠ | Extended | 2026-11-03 | 36 V-class; thin stock — not checked |
| ADG1209YRZ-REEL7 | C654763 | SOIC-16 | 919 | Extended | 2026-11-03 | 12 V-class dual 4:1; large package — not checked |
| TMUX1109PWR | C2673338 | TSSOP-16 | 31 ⚠ | Extended | 2026-11-03 | Rejected on stock |

- *Constraint (Rev0.2 §5):* analog range must include V5P1, so VDD from VPD and a ≥ 10 V-class
  part; leakage and charge injection small against 100 nA. No candidate found with both
  adequate stock and a small package — one of the two reasons for OI-19.

### U12 / U22 — window comparator

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| TLV3202AIDGKR | C478075 | VSSOP-8 | 2,341 | Extended | 2026-11-03 | Candidate (dual → window) — not checked |
| TLV3502AIDCNR | C48618 | SOT-23-8 | 3,235 | Extended | 2026-11-03 | Faster alternate — not checked |

- *To confirm:* propagation delay; the whole comparator → gate path must fit 2 µs (§4, P8).

### Q100/Q101, Q200/Q201 — bypass FETs

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| CSD25402Q3A | C111356 | VSONP-8 (3.3 × 3.3) | 15,148 | Extended | 2026-11-03 | **Candidate** |
| CSD25404Q3 | C2865523 | VSON-CLIP-8 (3.3 × 3.3) | 2,627 | Extended | 2026-11-03 | Alternate — not checked |

- *Verified (CSD25402Q3A):* P-channel, V<sub>DS</sub> −20 V; R<sub>DS(on)</sub> 7.7 typ / **8.9 max mΩ**
  at V<sub>GS</sub> −4.5 V (13.3 / 15.9 mΩ at −2.5 V); Q<sub>g</sub> 7.5 typ / **9.7 max nC**.
  Used in Rev0.2 §3.1 (port voltage), §3.2 (TC), P8 (gate drive).

### Shunts

| Ref | MPN | LCSC | Package | Stock | Class | Checked | Role / note |
|---|---|---|---|---:|---|---|---|
| R100/R200 (20 mΩ) | WSK2512R0200FEA | C1517429 | 2512, 4-terminal | 14 ⚠ | Extended | 2026-11-03 | **Blocked — OI-20**: stock, and TCR ±35 ppm/°C > ≤ 25 |
| R100/R200 option | WSK2512R0100FEA (10 mΩ) | C3985410 | 2512, 4-terminal | 822 | Extended | 2026-11-03 | OI-20 option; ±35 ppm/°C |
| reference only | FMF25FPJR020-LH (20 mΩ) | C105360 | 2512, 2-terminal | 41,815 | Extended | 2026-11-03 | Not acceptable: D5 requires a 4-terminal part |
| R101/R201 (2 Ω) | WSK25122L000FEA | C3997408 | 2512, 4-terminal | 164 ⚠ | Extended | 2026-11-03 | Option; thin stock; TCR above 0.2 Ω not extracted. No 1206 candidate found yet |
| R102/R202 (200 Ω) | RT0805BRD07200RL | C865287 | 0805 | 129,254 | Extended | 2026-11-03 | Thin film, 0.1 %. *To confirm:* TCR (code "D"), power rating against the 0.13 W stuck case (§7.3) — may need the 1206 size |

- *Verified (Vishay WSK2512):* TCR **±35 ppm/°C for 0.005 – 0.2 Ω** (±75 for 3 – 4.9 mΩ). So the only
  stocked 4-terminal 20 mΩ part misses Rev0.1's ≤ 25 ppm/°C requirement *and* has 14 pcs.
- *Requirements (Rev0.1 §4, Rev0.2 §7.3):* HIGH ≤ 25 ppm/°C, 4-terminal; MID ≤ 50 ppm/°C and
  survives 8 W for 10 ms (80 mJ); LOW ≤ 50 ppm/°C and ≥ 0.25 W continuous.

## Port path and protection

### U13 / U23 — load switch

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| SY6280AAC | C55136 | SOT-23-5 | 81,756 | Extended | 2026-11-03 | **Candidate** (P2) |
| TPS2553DBVR | C55266 | SOT-23-6 | 45,331 | Extended | 2026-11-03 | Alternate |
| TPS259474LRPWR | C2864845 | VQFN-10-HR (2 × 2) | 3,537 | Extended | 2026-11-03 | eFuse alternate — not checked |

- *Verified (SY6280):* IN 2.4 – 5.5 V (6 V abs max); R<sub>DS(on)</sub> 80 mΩ typ;
  I<sub>lim</sub> = 6800 / R<sub>set</sub>, 0.75 / 1.0 / 1.25 A min/typ/max at 6.8 kΩ, settable
  0.4 – 2 A; EN active high, "do not float"; **reverse blocking at shutdown (no body diode)**;
  **150 Ω output discharge at shutdown**; thermal shutdown 130 °C, auto-restart at 110 °C;
  short-circuit foldback to 50 %; θ<sub>JA</sub> 200 °C/W; **no fault output**.
- *Verified (TPS2553):* 2.5 – 6.5 V; current limit set by R<sub>ILIM</sub> 15 – 232 kΩ; FAULT
  output for over-current and reverse voltage; turns off when OUT exceeds IN by 135 mV for 4 ms;
  reverse leakage ≤ 1 µA at V<sub>OUT</sub> 6.5 V, V<sub>IN</sub> 0 V. No output discharge found
  in the text, so REQ-PORT-03 would need an added discharge path.

### ESD

| MPN | LCSC | Package | Stock | Class | Checked | Role |
|---|---|---|---:|---|---|---|
| TPD4E05U06DQAR | C138714 | USON-10 (1 × 2.5) | 120,539 | Extended | 2026-11-03 | 4-line array per connector (D+, D−, CC1, CC2) — not checked |
| USBLC6-2SC6 | C7519 | SOT-23-6L | 40,130 | Extended | 2026-11-03 | Alternate — not checked |

- VBUS TVS (J1 at up to 9 V, J2/J3 at 5 V): **not yet selected** (OI-7).

## Not yet searched

Buck inductor L1; CC Rp switch FET; status LEDs; tactile switches; USB-C receptacles J1–J3
(their footprints drive OI-1); passives. Each needs a row here before capture.
