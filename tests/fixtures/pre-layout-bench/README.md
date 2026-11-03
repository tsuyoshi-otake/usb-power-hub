# Pre-layout bench kit — purchase list and bench setup (issue #1)

**Question.** What must the user buy, and how must three benches be wired, to close OI-24,
OI-27, OI-28 (bench M / V-MEAS-00), OI-31 (bench A / V-MEAS-06) and the OI-23 remainder
(bench C)? All of them block KiCad capture (`CIRCUIT_DESIGN_Rev0.4.md` §12).

**Answer.** Two orders, both read on 2026-11-03:

- **Akizuki: 41 items, 11,345 yen, shipping free** (the tax-included subtotal is over
  Akizuki's 11,000 yen threshold).
- **LCSC: 2 items, $1.04 plus LCSC's shipping**, which LCSC shows only at checkout. These are
  the OP07CDR and the AO3401A. Akizuki sells neither, and OI-27 is about these exact parts.

Recheck every price and stock figure at order time (V-MFG-02). `dupont-mm` was already
flagged 在庫僅少 (low stock).

| Bench | Check (method and pass criteria: `requirements/verification.md`) | Closes |
|---|---|---|
| M | V-MEAS-00 — one HIGH-range mirror channel: OP07CDR on 0/12 V, AO3401A mirror, 0.1 Ω shunt | OI-27 (single-supply margins, gate headroom, stability), OI-28 (R_M 2.35 W / 10 ms) |
| A | V-MEAS-06 — PGA2040 + one MCP3208 at V_DD 5 V, V_REF 3.3 V | OI-31 (sample stretch, INL, reset state, module facts) |
| C | CH335F module outline, hole grid, pin map, mounted-chip check | OI-24, then the OI-23 re-run |

This directory is a fixture for benches only (`tests/fixtures/`). Nothing here is a
manufacturing document; the board is still WIP — MANUFACTURING PROHIBITED.

## Purchase list

`kit.json` is the source; do not hand-edit figures here. Print both lists and check them:

```
python -I -B tests/fixtures/pre-layout-bench/kit.py
python -I -B tests/fixtures/pre-layout-bench/test_kit.py
```

`kit.py` prints every line, `subtotal: 11,345 yen`, the shipping per carrier from the rule in
`kit.json` `meta` (0 yen here; Sagawa 550 / Yamato 600 yen per parcel below 11,000 yen),
`total: 11,345 yen`, then `LCSC subtotal: $1.04`. Exit 0 means every need is covered, in
stock and above any minimum order; exit 1 lists the problems. `test_kit.py` (21 tests)
corrupts the data to show each check failing.

**Akizuki** (code → `https://akizukidenshi.com/catalog/g/<code>/`):

| Item | Code | Buy | Covers | Note |
|---|---|---|---|---|
| pga2040 | g116762 | 1 | A1 | exact U1 — becomes a bench unit (sockets soldered in) |
| mcp3208 | g100238 | 2 | A3 | exact U7, DIP16: 1 used + 1 spare; the second also lifts the order over the free-shipping line |
| usbc-kit | g113080 | 1 | A6 | connector mounted; no CC resistors fitted |
| ch335f-mod | g129556 | 1 | C1 | kit; photo shows the QFN28 pre-soldered — confirm on the bench |
| mau104 | g104132 | 1 | M5 | exact U5 |
| tsl-shunt | g109588 | 2 | M3 | exact RS10; Kelvin-wire it on univ-pcb |
| mfu-bag | g108805 | 1 bag of 100 | M4 ×3, M14, A11 | exact RS11; **pulsed units never reused** |
| fet-2n7002 | g103919 | 1 pack of 40 | A4 | same part number as design C8545 |
| irlml6344 | g106049 | 1 pack of 10 | M7 | bench-only switch |
| pnp-2sa1015 | g100882 | 1 tape of 10 | A12 | bench-only current sources (Toshiba 2SA1015GR) |
| tl431 | g112018 | 2 | M6 (+1 spare) | stands in for CJ431 |
| az1117 | g116155 | 1 | A5 | stands in for AMS1117-3.3 |
| r100, r2k4, r10k, r1k, r1m, r470, r33k, r15k, r1k5, r5k1 | g108522, g108541, g108550, g108535, g108568, g108532, g108559, g108552, g108537, g108547 | 1 bag each | M8–M13, M18, A6–A8, A12 | 1/4 W 1 % metal film, 100 per bag |
| c22u-mlcc, c10u-mlcc | g108240, g113388 | 1 pack of 10, 1 pack of 20 | M14 ×2; M16 | Murata 0805 MLCC, 22 µF 25 V X5R and 10 µF 25 V B: the design's value, rating, dielectric class and size, because their ESR and DC-bias derating shape the V-MEAS-00 step (see below) |
| c22u, c10u | g117899, g117897 | 1, 1 | A5; A11 | 50 V electrolytic in bench A's two supply filters (see below) |
| c100n, c1u | g113582, g108150 | 1 pack of 10, 1 | M17, A11, A5 | X7R |
| c220p, c330p | g108106, g108064 | 1 pack of 10 each | M15; A7 | C0G (the design's 220 pF is X7R; C0G is the better dielectric) |
| header40, socket42 | g100167, g105779 | 3, 2 strips | S7; A2, C2 | 80 pins allocated; 46 socket contacts |
| adp-sot23, adp-sot223, adp-sop8 | g132111, g117248, g105154 | 1 pack each | S5, S6, S8 | 8 / 1 / 2 used |
| breadboard, jumpers, dupont-mm, univ-pcb | g100315, g130088, g115869, g103231 | 2, 1, 1, 2 | S1–S4 | dupont-mm is **low stock** |
| tact-sw, pot-10k | g103647, g100975 | 2, 2 | A10, A9 | BOOTSEL + RUN; one 3296W pot per current source |

**LCSC** (the same LCSC items that JLCPCB places as Basic parts):

| Item | LCSC | Buy | Covers | Note |
|---|---|---|---|---|
| op07cdr | C7433 | 5 (minimum order) | M1 | TI OP07CDR, SOIC-8, $0.1128 each; on adp-sop8 |
| ao3401a | C15127 | 5 (minimum order) | M2 | AOS AO3401A, SOT-23, $0.0969 each; on adp-sot23 |

The same manufacturer part numbers from another authorized distributor test the same thing;
LCSC is listed because its items are the ones JLCPCB assembles.

## Design parts not sold by Akizuki

| Design part (LCSC) | At Akizuki, 2026-11-03 | Bought |
|---|---|---|
| OP07CDR, SOIC-8 (C7433) | only PDIP-8 OP07s, e.g. ADI's OP07CPZ (g113696): another vendor's die. OI-27 asks how **this** die behaves on 0/12 V, so a result on another die cannot close it | **op07cdr** from LCSC, on an SOP-8 adapter |
| AO3401A, SOT-23 (C15127) | not listed. The nearest P-FET, IRLML6402 (g102553), has V_GS(th) −0.40/−0.55/−1.2 V against the AO3401A's −0.5/−0.9/−1.3 V, so the gate-headroom result would not transfer | **ao3401a** from LCSC |
| AMS1117-3.3, SOT-223 (C6186) | not listed | **az1117**: AZ1117CH-3.3TRG1, same package and dropout class. V3V3 is a supply role on the bench, not a measured path |
| CJ431, SOT-23 (C3113) | not listed | **tl431**: HTC TL431, TO-92, 2.495 V reference. V_INJ is a supply role too |
| through-hole N-MOSFET with R_DS(on) rated at V_GS ≤ 3.3 V | none: 2SK2232 and 2SK4017 are rated at 4 V, TK8S06K3L at 6 V, IRLB3813 and IRLB3034 at 4.5 V, IRLU3410 at 4.0 V, PSMN015N10NS2 at 6 V | **irlml6344**, SOT-23: 37 mΩ max at V_GS 2.5 V, 30 V / 5 A. Not bought: MTN2306AN3 (g117513) |
| 27 Ω USB series resistors | not bought: Pimoroni's schematic shows R1 = R2 = 27R4 on the module | if a module measures without them: 1/4W27Ω carbon g114273, or 22 Ω + 4.7 Ω in series |

Exact design parts bought: PGA2040, MCP3208-CI/P, AE-USB2.0-TYPE-C, AE-QFN28-DIP(CH335F),
MAU104, TSL1TTER100D, MFU100F10RB, 2N7002, OP07CDR, AO3401A. TL431 and AZ1117 stand in for
supply-role parts; IRLML6344 and 2SA1015GR are bench tools.

Passives have the design's values but not its JLCPCB part numbers:

- The resistors and the small capacitors are through-hole; the design's are 0402–0805.
- **The port capacitor and the V12F filter are 0805 MLCCs** of the design's value, rating and
  dielectric class (10 µF 25 V, 22 µF 25 V X5R).
  - The port capacitor's low ESR and its DC-bias derating shape the 0.1 → 1 A step that
    V-MEAS-00 judges for overshoot; the design assumes about 7 µF at 5 V.
  - An electrolytic there would damp the step and could hide ringing.
  - Solder both on univ-pcb.
- **Bench A's two supply filters are electrolytics.**
  - V5A (the MCP3208's VDD; design 10 µF X5R): its ESR enters no reading.
  - V3V3 (the AZ1117 output; design 22 µF ceramic): an electrolytic is kept because the
    1117 family's stability on a ceramic alone is still unconfirmed (parts.md, AMS1117 "To
    confirm"). An oscillating V3V3 would corrupt VREF.

## PGA2040 — how to power it (read before wiring bench A)

Sources, both downloaded 2026-11-03: Pimoroni's product page
<https://shop.pimoroni.com/products/pga2040> and the schematic it links,
<https://cdn.shopify.com/s/files/1/0174/1800/files/pga2040_schematic.pdf> (Pimoroni, generated
04/06/2021).

- **The supply input is the VBUS pad, A2: 3.0–5.5 V.** The schematic labels it
  "Vbus: 3.0V - 5.5V"; the product page says "Input voltage range 3V - 5.5V (on VB pin only)".
  It feeds the module's NCP115AMX330TCG 3.3 V regulator (page: 300 mA max).
- **The 3V3 pad, B3, is that regulator's output.** Never drive it, and never put 5 V on it.
- 3V3_EN (A3) is pulled up to VBUS by R4 = 100 kΩ on the module: leave it open.
- **27 Ω series resistors are fitted:** R1 = R2 = 27R4 between pads A5 (USB_DP) / A6 (USB_DM)
  and the RP2040.
- Flash: W25Q64JVXGIQ. BOOTSEL (A7) reaches its CS through R5 = 1 kΩ.
- Pads used here: VBUS A2, 3V3 B3, RUN A4, USB_DP A5, USB_DM A6, BOOTSEL A7, GND (eight pads,
  A1*8 on the schematic), and the GPIO pads wired below. Leave ADC_VREF (B4) open.
- **The design question (OI-31).** Rev0.4 §6.1 feeds U1 from V3V3 "if it takes 3.3 V". On
  paper both feeds are inside the rating, but at 3.3 V in, the regulator's dropout puts the
  3V3 pad below 3.3 V. Measure the 3V3 pad with VBUS fed from 5 V and again from the bench
  V3V3, idle and with a test build running, and record both in `requirements/parts.md`.
- These are paper facts. OI-31 closes only on a purchased module (V-MEAS-06).
- **The grid cannot straddle a breadboard** (pads on all four edges). Solder socket42
  contacts into the 16 or so used pads and run dupont-mm wires to the breadboard. That
  module then stays a bench unit; the prototypes need their own (41 in stock on
  2026-11-03).

## Instruments (required; not purchased)

If you lack one, use the fallback and record it in the bench notes.

| Instrument | Minimum spec | Fallback |
|---|---|---|
| Adjustable bench supply | 4.5–5.5 V at ≥ 1.5 A: the V-MEAS-00 sweep at 4.59 V and 5.25 V (the resistor fallback draws up to 1.43 A), and the R_M pulse (≈ 4.87 V, 0.49 A) | a fixed 5 V ≥ 1.5 A supply runs only one corner; record the gap |
| 5 V supply for bench M | 5 V ±5 %, ≥ 0.2 A, for the MAU104 input (the design feeds U5 from V5L, J1's 5 V) | second channel of the bench supply |
| PC | builds RP2040 firmware (UF2); its USB port powers bench A through usbc-kit (under 0.1 A) | a PC that cannot build firmware can still flash a UF2 built elsewhere (BOOTSEL drive) and run a serial terminal |
| DMM ×2 | ≥ 40,000 counts, i.e. 0.1 mV on a 4 V range (a 4¾- or 5½-digit meter). 1 LSB at V_REF 3.3 V is 3.3 / 4096 = 0.81 mV | a 4,000- or 20,000-count meter shows 1 mV at 3.3 V (1.2 LSB): INL is then resolved to about ±0.6 LSB, so a result within 1 LSB of the ±2 LSB limit is inconclusive. A 2,000-count meter shows 10 mV at 3.3 V and cannot run this check |
| 4-wire ohmmeter | ≤ 1 mΩ resolution at 10 Ω; a 0.1 % change in R_M is 10 mΩ | manual 4-wire: about 20 mA through R_M via a series resistor; one DMM reads the current, the other the voltage at the resistor body (0.2 V, 4 mW). R = V / I, with the same meters, ranges and current before and after |
| Oscilloscope | ≥ 50 MHz, 2 channels: AMP_H and the gate on the step; R_M's voltage during a pulse | one channel, two passes |
| Electronic load | 0–1.5 A with a step ≤ 10 µs | power resistors, one per sweep point, at 4.59–5.25 V through the 0.1 Ω shunt: 47 Ω ≥ 1 W (0.10–0.11 A; 0.59 W at 5.25 V), 10 Ω ≥ 5 W (0.45–0.52 A; 2.8 W), 4.7 Ω ≥ 10 W (0.96–1.09 A; 5.9 W), and for the 1.2 A end that same 4.7 Ω ∥ a 15 Ω ≥ 3 W (1.25–1.43 A; 1.8 W in the 15 Ω). The step always goes through M7; read the actual current on the meter |
| Calipers | ≥ 0.1 mm resolution, ≥ 50 mm (OI-24 outline and hole grid) | steel rule at 0.5 mm; record the reduced precision |
| Soldering equipment | iron with a fine tip for the SOT-23 and SOP-8 adapters, the 0805 capacitors and the 6.3 mm shunt chip | no clip-on substitute exists for the adapters or the Kelvin joints: without a fine tip, have them soldered elsewhere (a makerspace) before the bench |

## Bench M wiring (V-MEAS-00; design nets in parentheses)

Build on univ-pcb (S4) and a breadboard (S1); every SMD part goes on its adapter. Solder each
SOT-23 by its datasheet's package drawing and mark which adapter pin carries G, S and D. The
adjustable supply plays J4 after F1 (VBUS_IN): 4.59 V emulates J4 = 4.75 V less F1's drop
(D25); 5.25 V is the top corner.

```
adj supply + ──(VSUP_A)──┬── TSL pad A (supply-side Kelvin)
                         │   TSL chip soldered across two islands of univ-pcb (S4)
                         └── TSL pad B (load-side Kelvin) ── VBUS_A node ── load ── GND
R1 100 Ω (r100): TSL pad A sense tap ── 100 Ω ── node X ── AO3401A SOURCE
OP07CDR (SOIC-8 on adp-sop8): pin 7 = V12F, pin 4 = GND, pins 1/8 open;
        pin 3 (+IN) ── 10 kΩ (r10k) ── TSL pad B sense tap; pin 2 (−IN) ── X;
        pin 6 (OUT) ── 1 kΩ (r1k) ── AO3401A GATE
AO3401A DRAIN ── AMP_H ── 2.4 kΩ (r2k4) ∥ 220 pF (c220p) ── GND      ← measure here
V_INJ ── 1 MΩ (r1m) ── X   (pedestal)
```

- **V12 chain:** 5 V bench-M supply → mau104 input; −OUT to GND; +OUT → 10 Ω (mfu-bag) →
  **V12F** → 2 × 22 µF 0805 (c22u-mlcc) to GND. 100 nF (c100n) on the MAU104 input and on
  V12F.
- **V_INJ:** V12F → 1.5 kΩ (r1k5) → **V_INJ** → tl431 cathode; anode → GND; REF ← the tap of
  33 kΩ (V_INJ side) / 15 kΩ (GND side) → 2.495 × (1 + 33/15) = 8.0 V. 1 µF ∥ 100 nF to GND.
- **Port capacitor:** VBUS_A → 10 µF 0805 (c10u-mlcc) → GND, soldered right at the VBUS_A
  node. One 100 nF at the OP07 supply pins.
- **R_M pulse (OI-28):** VSUP_A → R_M (one MFU 10 Ω from mfu-bag, marked) → irlml6344 #1
  drain; source → GND; gate → 1 kΩ → drive pin, and gate → 10 kΩ (M18) → GND so that a
  floating pin keeps it off.
  - Set the supply to about 4.87 V (4.85 V plus 0.485 A × the FET's 37 mΩ and the wiring).
    Adjust until the scope across R_M reads 4.85 V ± 0.05 V in a pulse: that is
    2.35 W ± 2 % (V² / R).
  - Run 100 pulses of 10 ms, at least 1 s apart. V-MEAS-00 does not set the spacing, so record
    the spacing used.
  - Measure R_M by 4-wire before and after the pulses.
- **Load step:** VBUS_A → 47 Ω (0.1 A) to GND. VBUS_A → 4.7 Ω → irlml6344 #2 → GND switches
  about 1 A. That gate also gets 1 kΩ in series and a 10 kΩ pull-down.
- **Drive pins:** a 3.3 V GPIO of the bench-A PGA2040 (bench firmware, below) or a pulse
  generator; tie the bench grounds together.
- **Measure and pass:** sweep 0 → 1.2 A at 4.59 V and at 5.25 V, recording AMP_H, the OP07
  output and the gate. Then the step, then the pulses. The pass criteria are V-MEAS-00's:
  linearity within 0.5 % to 1.2 A, the gate ≥ 0.15 V above the OP07's lowest output,
  overshoot < 10 % with no sustained oscillation, and R_M changed < 0.1 %.

## Bench A wiring (V-MEAS-06)

**Power comes only from the PC's USB port.** usbc-kit's VBUS is the bench's 5 V rail
(**V5**, playing V5L = J1's 5 V). Connect no other 5 V source to it: a second source
back-feeds the PC's port.

- **usbc-kit:** VBUS → V5; GND → GND; D+ → PGA2040 A5; D− → A6. CC1 and CC2 each go through
  5.1 kΩ (r5k1) to GND, so the PC sees a device. Put the resistors on the breadboard, not on
  the kit.
- **pga2040:** VBUS (A2) ← V5; GND pads → GND. Sockets on the used pads, dupont-mm to the
  breadboard. See the section above before applying power.
- **V3V3:** az1117 on adp-sot223, VIN ← V5 (100 nF), VOUT → **V3V3** → 22 µF (c22u) ∥ 100 nF.
  V3V3 feeds only the MCP3208's VREF (pin 15) and the hold-test pull-up. For the OI-31
  supply measurement, it may also feed PGA2040 VBUS instead of V5.
- **mcp3208:** pin 16 VDD ← **V5A** (V5 → 10 Ω from mfu-bag → V5A, 10 µF c10u); pin 15
  VREF ← V3V3; pins 14 AGND and 9 DGND → GND; 100 nF each on VDD, VREF and one input.
  Pinout from DS21298E p. 1: 1–8 CH0–CH7, 9 DGND, 10 CS, 11 DIN, 12 DOUT, 13 CLK, 14 AGND,
  15 VREF, 16 VDD.
- **SCLK, CS, DIN (§6.4):** three 2N7002 on adp-sot23. Gate ← a PGA2040 GPIO; source → GND;
  drain → ADC pin, with a 1.5 kΩ (r1k5) pull-up to **V5**. The shifters invert, so firmware
  drives inverted levels. In reset the drains idle high, which keeps CS deselected.
- **DOUT:** pin 12 → 10 kΩ → tap → 15 kΩ → GND (3.0 V from 5 V); tap → GPIO.
- **CH0 and CH1 source networks (A7) and their drive (A12):**
  - **Network:** node → 1.5 kΩ ∥ 330 pF (c330p) → GND; node → 1 kΩ → ADC pin.
  - **Drive each node with a current, as the mirror drain does:** 2SA1015GR emitter → 470 Ω →
    V5; collector → node; base ← wiper of a pot-10k across V5 and GND.
  - The current is about (V5 − V_wiper − 0.65 V) / 470 Ω. A wiper near 3.3 V gives 2.2 mA, so
    the node sits at 3.3 V; a wiper at the top end gives 0 V.
  - The PNP saturates before the node passes about 3.7 V, so the node cannot reach V5.
  - V_EB drifts by about −2 mV/K, so read the DMM at every step rather than trusting a pot
    setting.
  - **Do not drive the node straight from a pot wiper.** A stiff source removes the
    charge-sharing droop that the native 1.5 µs sample must show (Rev0.4 §3.2 computes 17 LSB
    for this network), and the negative control would then pass when it must fail.
- **Hold test:** one GPIO → 10 kΩ (r10k) → V3V3. Hold RUN (A4) low with a tact-sw, then power
  up with blank flash; measure that GPIO.
- **Buttons:** tact-sw from RUN (A4) to GND, and from BOOTSEL (A7) to GND.
- **Module facts (power off):** measure the resistance across R1 and R2 (expect about
  27.4 Ω) and note the flash marking; a test build reads the 64-bit unique ID (W25Q64JV
  command 4Bh).
- **Pass criteria:** V-MEAS-06's — stretched alternating readings within 0.5 LSB of the
  single-channel ones, native ones off by more than 5 LSB, INL within ±2 LSB, the pulled-up
  GPIO ≥ 2.5 V in reset and after power-up, and the module findings recorded in
  `requirements/parts.md`.

## Bench C — module measurement (OI-24)

Measure the purchased ch335f-mod. Write the results into `requirements/parts.md` (U6), then
re-run `python -I design/experiments/oi-23-placement/placement_study.py`; it must still exit 0.

1. **Outline:** body length, width and height with calipers; lead span and lead width.
2. **Hole grid:** DIP30 pin count, pitch (expect 2.54 mm), **row spacing** (the footprint
   depends on it), and any corner or mounting holes.
3. **Pin map:** seat the module in socket42 contacts (2 × 15). Trace each DIP pin to the
   CH335F function in the CH334/CH335 datasheet (V5, XI/XO, PWREN1–4#, OVCUR1–4#, upstream and
   downstream D+/D−, PSELF, PGANG). Number pins by the module's silkscreen.
4. **Mounted check:** whether the QFN28 ships soldered on, and whether the 12 MHz crystal
   circuit is fully fitted.
5. **Record** the outline, grid, pin-to-function table, the mounted answer, and any
   difference from the photos. Akizuki publishes no module drawing.

## Bench firmware needed (follow-up work — none written here)

- A PIO program that drives the MCP3208 at 1 MHz in two variants: the **native 1.5 µs sample
  phase** and the **stretched 4.5 µs** one (hold the clock inside the sample window;
  DS21298E §6.2 permits an irregular clock). The native one must visibly fail.
- Inverted pad levels for SCLK, CS and DIN (Q50–Q52 invert, §6.4).
- A flash unique-ID reader (W25Q64JV command 4Bh, 64-bit ID) for OI-31's serial-number plan.
- A test build for the GPIO reset-state and 10 kΩ hold-pull-up check (V-MEAS-06).
- Drive pins for bench M: 100 pulses of 10 ms (OI-28) and the load-step toggle.
- A minimal CDC-ACM build to check USB through usbc-kit.

## What can later go on the prototypes

- **May migrate, if still unsoldered and stock still holds (V-MFG-02):** the spare MCP3208
  (and the bench one if it was only on the breadboard), MAU104, usbc-kit, ch335f-mod (bench C
  only measures it), an unused TSL1TTER100D, the unused MFU resistors, and unused sockets,
  headers and adapter boards.
- **Must never migrate:** the PGA2040 with contacts soldered into its pads; the 3 pulsed R_M
  samples (mark them at the pulse test); anything visibly stressed. Keep the wired mirror as
  the bench reference.
- **Never on the product at all:** TL431, AZ1117, IRLML6344, 2SA1015GR and every through-hole
  passive. The bench OP07CDR, AO3401A and 2N7002 do not go on it either: JLCPCB places those
  part types (D13).

## Inputs and their dates

- Akizuki prices, pack sizes and stock: each item's product page, downloaded 2026-11-03.
- Akizuki shipping rule: <https://akizukidenshi.com/catalog/pages/buy.aspx>, 2026-11-03 —
  "商品合計(ご注文小計)が税込11,000円(1万1千円)以上は配送業者によらず送料無料"; Sagawa 550 and
  Yamato 600 yen per parcel; the parcel count can grow with size and weight.
- LCSC: <https://www.lcsc.com/product-detail/C7433.html> and
  <https://www.lcsc.com/product-detail/C15127.html>, 2026-11-03. Code, MPN, brand, package,
  stock, minimum order and price come from the product JSON embedded in each page.
- PGA2040: the Pimoroni product page and schematic above, 2026-11-03.
- MCP3208 pinout and timing: Microchip DS21298E, 2026-11-03.
- MOSFET and regulator facts: Akizuki-served datasheets under `/goodsaffix/`, 2026-11-03
  (IRLML6344, IRLML6402, 2N7002, 2SK2232, 2SK4017, TK8S06K3L, IRLB3813, IRLB3034, IRLU3410,
  PSMN015N10NS2, MTN2306AN3, TL431A, OP07).
- Design: `CIRCUIT_DESIGN_Rev0.4.md` §3.2, §6.1, §6.4 and §12; `requirements/parts.md`;
  `requirements/verification.md` V-MEAS-00 and V-MEAS-06; `CLAUDE.md` §11. All as of
  2026-11-03.

## What this cannot see

- **Stock and price at order time.** Every figure is a 2026-11-03 snapshot.
- **LCSC's shipping charge.** It depends on destination and carrier and appears only at
  checkout. It may well exceed the $1.04 of parts.
- **Kit contents.** Akizuki's text does not list what a キット ships; its photos are
  examples. The CH335F module's mounted QFN is inferred from a photo; bench C confirms it.
- **Whether stand-ins matter.** TL431 and AZ1117 sit in supply roles, and IRLML6344 and
  2SA1015GR are bench tools. The benches, not this list, show whether any of them disturbs a
  reading.
- **Parcel count.** Akizuki may split the order and multiply shipping by size and weight;
  one parcel is assumed.
- **What kit.py proves:** coverage per need and component, pieces per item, required fields
  per vendor, stock against packs, the LCSC minimum order, unique ids, and the arithmetic.
  It does not prove that a `covers` entry is the physically right part, that a `value` key
  names a real value, or that a part suits its role. It was negative-tested (`test_kit.py`)
  before being trusted.
- **Instruments are assumed present.** A fallback lowers a check's precision; it does not
  create the capability.
- **No firmware exists.** The measurements that need it are listed as follow-ups.
- **Nothing here orders anything.** No cart, login or form was used at either vendor.
