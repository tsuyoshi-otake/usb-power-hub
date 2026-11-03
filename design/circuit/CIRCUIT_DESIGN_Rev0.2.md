# USB Power-Control Hub — Circuit Design Rev0.1

**State: WIP — MANUFACTURING PROHIBITED**
Date opened: 2026-08-16

This document *is* the schematic at this stage. KiCad capture transcribes what is settled
here; it is not where the design happens (CLAUDE.md Section 2). Nothing in this file has been
built or measured. Every part number below is a *candidate* until `requirements/parts.md`
records a confirmed JLCPCB assembly-pool figure against it.

Read this with CLAUDE.md Section 11 (Open Issues) open. This revision closes OI-2, OI-3 and
OI-4 by decision, and opens a new blocking issue (board area, Section 11 below).

---

## 1. Sources of Fact

| # | Fact | Source | Confidence |
|---|---|---|---|
| 1 | Product is a *measurement instrument* that also happens to be a hub | User, this thread | Settled |
| 2 | Upstream power is USB-PD sink | User decision, 2026-08-16 | Settled |
| 3 | ECAD tool is KiCad | User decision, 2026-08-16 | Settled |
| 4 | Measurement range target 0.1 µA – 1 A | User request, 2026-08-16 | Settled as a *target*; see Section 4 |
| 5 | Upstream must enumerate as a COM port and be controllable from it | User request, 2026-08-16 | Settled |
| 6 | RP2040 USB is Full-Speed (12 Mbps) device only — no High-Speed | RP2040 datasheet, well established | High |
| 7 | Board outline 60 × 24 mm | `mockup/board-model.js` | **Contradicted by this design — Section 11** |
| 8 | All designators/values in `mockup/` are placeholders | CLAUDE.md §0 | Settled |

Everything else below is derived by calculation in this document, or is explicitly marked OPEN.

---

## 2. What this changes versus the mockup

| Mockup showed | Rev0.1 says | Why |
|---|---|---|
| Rd-only upstream, no PD | CH224K-class PD sink, request 9 V | Closes OI-4. 2 × 1 A at 5 V is 10 W; you cannot get that from a 5 V/500 mA contract |
| 4 shunts (10 mΩ / 1 Ω / 100 Ω / 1 k), 1 FET per channel | 3 shunts (20 mΩ / 2 Ω / 200 Ω), 2 bypass FETs + sense mux per channel | Closes OI-3. 4 shunts with 1 switch is not a controllable ladder |
| No comparator | Window comparator per channel, hardware range control | µs-scale ranging cannot be done by MCU polling |
| 12 MHz crystal for MCU only | One 12 MHz CMOS oscillator feeding both RP2040 XIN and the hub | Closes OI-2, and costs one part instead of two crystals + four caps |
| 2-terminal shunts | 4-terminal (Kelvin) for the 20 mΩ; Kelvin *land pattern* for the others | Closes OI-11 |
| 6-layer stackup | 4-layer proposed | OI-10 — no differential pair count justifies 6 |
| `PPK2-COMPATIBLE µA→A` on silk | Removed | Third-party trademark used as a compatibility claim (CLAUDE.md §6) |

---

## 3. Topology

### 3.1 Power path

```
          J1 (USB-C, upstream / host)
            │ VBUS_IN
            ├── U1  PD sink (CC1/CC2)  ──► requests 9 V, falls back 5 V
            │
          VPD (9 V nom, 5 V fallback)
            │
            ├── U2  synchronous buck ──► V5P1  (5.10 V, ≤ 2.5 A)
            │        L1
            └── U3  LDO ─────────────► V3P3  (digital)
                     └── U3B LDO ────► V3P3A (analog, separate)

          V5P1 ──┬── [ ladder A ] ── U13 load switch ── VBUS_A ── J2
                 └── [ ladder B ] ── U23 load switch ── VBUS_B ── J3
```

The buck sets **5.10 V**, not 5.00 V, so that after the worst-case ladder burden (20 mV) and
the load-switch drop (~30 mV at 1 A) the DUT still sees ≥ 5.05 V. This is a decision, not an
accident — record it in the KiCad schematic as a note next to U2's feedback divider.

**Why buck from 9 V instead of passing 5 V straight through.** A pass-through rail inherits
every millivolt of upstream cable IR drop and every wart of the charger's regulation, and
those land directly on the DUT. An instrument should present a rail it controls. It also
decouples us from what a given source offers at 5 V — 9 V/2 A sources are far more common
than 5 V/3 A ones.

### 3.2 Measurement front end (one channel shown; ×2)

```
   V5P1 ──┬─ RS1 20 mΩ ─┬─ RS2 2 Ω ─┬─ RS3 200 Ω ─┬─→ U13 load switch → VBUS_A
          │             │           │             │
          │            Q100        Q101           │      Q100/Q101 = bypass FETs
          │        (bypass RS2) (bypass RS3)      │      default ON = HIGH range = safe
          │                                       │
          └──────────── U10 sense mux ────────────┘   selects ONE shunt's Kelvin pair
                              │
                        U11 current-sense amp (G = 50, zero-drift)
                              │
                     ┌────────┴────────┐
                     │                 │
              U7 ADC channel      U12 window comparator
                                        │
                                  range control logic → Q100/Q101
```

Three things about this arrangement are load-bearing:

1. **The mux selects the sense taps, not the current path.** On the HIGH range the amp sees
   only RS1's Kelvin pair; the bypass FETs' R<sub>DS(on)</sub> sits outside the sensed span.
   If instead you sense across the whole ladder, R<sub>DS(on)</sub> (~5 mΩ, TC ≈ +4000 ppm/°C)
   is in series with a 20 mΩ shunt (TC 15 ppm/°C) and dominates the temperature error —
   roughly 1300 ppm/°C on the total, i.e. ~2.6 % over a 20 °C swing. That is not an
   instrument. Section 5 records the alternatives considered.

2. **Every range is scaled to the same 20 mV full-scale**, so one amplifier gain and one ADC
   input range serve all three. Range switching changes only the scale factor applied in
   software, never the analog gain.

3. **The bypass FETs default ON** (gate pull-to-ON resistors). A firmware crash, a brownout,
   or an unprogrammed board leaves the ladder at 20 mΩ. Section 7.3 shows why the opposite
   default destroys the board.

### 3.3 Data path — and the COM port

```
   J1 D+/D- ── U6 USB 2.0 hub (4-port, HS) ─┬─ port 1 ── U4 RP2040   (USB FS device)
                                            ├─ port 2 ── J2 D+/D-    (DUT A passthrough)
                                            └─ port 3 ── J3 D+/D-    (DUT B passthrough)
```

The upstream PC sees a hub, and behind it a composite device on port 1. **That composite
device is what appears as a COM port.**

| Interface | Class | Appears on the PC as | Carries |
|---|---|---|---|
| 0 + 1 | CDC-ACM | `COMn` (Windows) / `/dev/ttyACM0` | Control. ASCII line protocol — open TeraTerm and type |
| 2 + 3 | CDC-ACM #2 | `COMn+1` / `/dev/ttyACM1` | Binary sample stream, framed |

Both are CDC-ACM, so both are driverless on Windows 10/11, macOS and Linux — no WinUSB, no
INF, no Zadig. Control by hand from a terminal is then a first-class use, not an afterthought.

**Design rules this forces (all verifiable, all easy to get wrong):**

- **Every unit must report a unique USB serial number string.** Windows keys COM-number
  assignment on (VID, PID, serial). With a unique serial each board keeps a stable `COMn`
  across replugs; with a missing or duplicated serial the numbers churn and the user's saved
  terminal profile breaks. Derive it from the RP2040 flash unique ID at boot.
- **The control interface must remain usable while the stream interface is running.** Do not
  share a single endpoint pair.
- **The stream is binary and framed.** ASCII would multiply the byte count by ~3.
- VID/PID: **OPEN.** Do not ship a squatted VID. Candidates: a PID under Raspberry Pi's
  RP2040 allocation programme, or pid.codes for open hardware. → `requirements/product.md`.

**The sample-rate ceiling is set here, not by the ADC.** RP2040's USB is Full-Speed only
(Source of Fact 6). Full-Speed bulk tops out near 1188 kB/s theoretical, and a real host
sustains meaningfully less:

| Sample rate | 2 ch × 3 B packed | % of FS bulk |
|---|---:|---:|
| 10 kSPS | 59 kB/s | 5 % |
| 32 kSPS | 188 kB/s | 16 % |
| 100 kSPS | 586 kB/s | 49 % |

32 kSPS is comfortable. 100 kSPS is possible but leaves little headroom and depends on host
behaviour. **Rev0.1 targets 32 kSPS**; anything faster is an explicit future decision that
requires either an MCU with High-Speed USB or on-board buffering with burst readout.

---

## 4. The range ladder — can it actually do 0.1 µA to 1 A?

Yes, with three ranges — but the answer has three conditions attached, and they are the
real design content.

Full-scale shunt voltage is fixed at **20 mV** for every range (amp G = 50 → 1.0 V at the
ADC, against a ±1.2 V ADC full scale — 20 % headroom).

| Range | Shunt | Full scale | Burden at FS | Dissipation at FS | Package |
|---|---:|---:|---:|---:|---|
| HIGH | 20 mΩ | 1 A | 20 mV | 20 mW | 2512, 4-terminal, ≤ 25 ppm/°C |
| MID | 2 Ω | 10 mA | 20 mV | 200 µW | 1206, Kelvin land, ≤ 50 ppm/°C |
| LOW | 200 Ω | 100 µA | 20 mV | 2 µW | 0805, Kelvin land, ≤ 50 ppm/°C |

Three ranges at 100× steps span 10⁶ of full scale. The requested 10⁷ is reached because the
LOW range must resolve well below its own full scale:

**0.1 µA on the LOW range = 100 nA × 200 Ω = 20 µV at the shunt = 1.0 mV at the ADC.**

A 24-bit ADC on a ±1.2 V scale has an LSB of 143 nV, which referred back through G = 50 and
200 Ω is **14 pA**. So quantisation is nowhere near the limit — noise and offset are. Which
gives the three conditions:

**Condition 1 — zero-point calibration is mandatory, not a convenience feature.**
A ±25 µV amplifier input offset is, on the LOW range, **125 nA of error** — larger than the
entire target resolution. Calibrated out, what remains is *drift*: at 0.1 µV/°C over a 20 °C
swing that is 2 µV → **10 nA**. Comfortably inside target. So:
- The amplifier must be zero-drift/chopper. A general-purpose op-amp will not do.
- The firmware must zero with the load switch open, and re-zero on temperature change.
- The mockup's `DOUBLE · ゼロ点校正` legend was right for the wrong reason. It is not a nicety.

**Condition 2 — auto-ranging must be hardware, and the output capacitor is part of the
measurement circuit.**
On the LOW range the ladder is ~202 Ω. If the DUT wakes and demands 1 A, the rail collapses
until the bypass FETs close. Riding through that needs charge at the DUT:

| Transition time | C needed to hold ΔV ≤ 200 mV at 1 A |
|---|---|
| 1 µs | 5 µF |
| 2 µs | 10 µF |
| 5 µs | 25 µF |

10 µF at the port is the working number, which sets the comparator+logic budget at ≈ 2 µs.
An MCU interrupt loop cannot meet that; the range decision must be a comparator driving the
FET gates directly, with the MCU only observing and setting limits.

**That same capacitor costs measurement bandwidth**, and this is an honest limitation of the
architecture rather than something to engineer away:

| Range | τ = R × 10 µF | −3 dB |
|---|---:|---:|
| HIGH (20 mΩ) | 0.2 µs | 796 kHz |
| MID (2 Ω) | 20 µs | 7.96 kHz |
| LOW (200 Ω) | 2 ms | 80 Hz |

**On the LOW range you are measuring the capacitor's charging current, not the DUT's
instantaneous current.** Sub-millisecond detail in the sub-100 µA region is not observable.
This must appear in the product documentation; it is the kind of specification that, left
implicit, gets discovered as a "bug" by the first user.

**Condition 3 — the ladder must fail safe.** See Section 7.3.

**What was rejected and why.** A fourth range (20 kΩ, 1 µA FS) would put 2 mV at the shunt
for 100 nA and make the low end trivially comfortable. It was not taken because it adds a
third bypass FET and a third mux input per channel, worsens the worst-case transient by two
decades (20 kΩ against a 1 A demand), and the board is already over area (Section 11). Three
ranges plus zero-calibration meets the requirement with margin; a fourth range buys precision
we have no way to verify without reference instrumentation we do not own.

---

## 5. Sense topology — decision record

| Option | Description | Verdict |
|---|---|---|
| A | One amp across the whole ladder; bypass FETs inside the sensed span | **Rejected.** FET R<sub>DS(on)</sub> TC ≈ 4000 ppm/°C swamps a 15 ppm/°C shunt on the HIGH range; ~2.6 % error over 20 °C, and it self-heats at 1 A |
| B | One amp, analog mux selects which shunt's Kelvin pair is sensed | **Selected.** Switch resistance is outside the sensed span and irrelevant into a high-Z amp input. Cost: one dual mux per channel |
| C | One amp permanently across each shunt (3 amps/channel), mux the low-voltage outputs | Metrologically cleanest, allows per-range gain optimisation. **Rejected on area** — 6 amps total, and Section 11 is already the binding constraint. Recorded as the fallback if B shows mux leakage or charge-injection problems in Rev0.2 |

The mux (U10/U20) must tolerate a ~5 V common mode, and its leakage must be small against
the smallest sense current. Note the mux sits at the *amplifier input*, where current is
picoamps, so its on-resistance does not matter — only its leakage and charge injection do.

---

## 6. Nets and designators

### 6.1 Power nets

| Net | Nominal | Source | Notes |
|---|---|---|---|
| `VBUS_IN` | 5 V or PD | J1 | Before PD negotiation this is 5 V |
| `VPD` | 9 V (5 V fallback) | after PD sink | Firmware must be able to read which contract was granted |
| `V5P1` | 5.10 V | U2 buck | Port rail. Sized for 2.5 A |
| `V3P3` | 3.3 V | U3 | Digital: RP2040, hub, flash |
| `V3P3A` | 3.3 V | U3B | Analog: amps, mux, comparators, ADC AVDD. Separate regulator, single-point tie |
| `VBUS_A` / `VBUS_B` | 5.05 V typ | after ladder + load switch | What the DUT actually sees |

### 6.2 Designators

| Ref | Part | Notes |
|---|---|---|
| J1 | USB-C receptacle, upstream | CC1/CC2 to U1 |
| J2, J3 | USB-C receptacle, DUT A/B | Rp on CC, gated by that port's VBUS |
| U1 | PD sink controller | Candidate: CH224K |
| U2 | Synchronous buck, ≥ 2.5 A | 9 V → 5.10 V |
| U3, U3B | LDO ×2 | V3P3 digital, V3P3A analog |
| U4 | RP2040 | QFN-56 |
| U5 | QSPI flash | USON-8, ≥ 2 MB |
| U6 | USB 2.0 HS hub, 4-port | Candidate: FE1.1s (12 MHz) or USB2514B (24 MHz) — see below |
| U7 | ADC, 24-bit, 2 ch simultaneous | Candidate: ADS131M02 (QFN-24) |
| U8 | Voltage reference | Only if U7's internal ref proves insufficient — OPEN |
| U10 / U20 | Sense mux, ch A / ch B | Dual, 3:1 or 2× SPDT |
| U11 / U21 | Current-sense amp, G = 50, zero-drift | Ch A / ch B |
| U12 / U22 | Window comparator + range logic | Ch A / ch B |
| U13 / U23 | Load switch, ≥ 1.5 A, controlled slew | Ch A / ch B |
| Y1 | 12 MHz CMOS oscillator | Feeds RP2040 XIN **and** hub XI — see below |
| L1 | Buck inductor | Value with U2 |
| F1 | Upstream protection | eFuse or PTC — OPEN, see OI-7 |
| R100 / R200 | 20 mΩ, 2512, 4-terminal | HIGH shunt, ch A / ch B |
| R101 / R201 | 2 Ω, 1206, Kelvin land | MID shunt |
| R102 / R202 | 200 Ω, 0805, Kelvin land | LOW shunt |
| Q100, Q101 / Q200, Q201 | Bypass FETs | Default ON |
| D1–D3 | USB ESD arrays | One per connector, must cover D+/D−/CC/SBU |
| SW1 | BOOTSEL | Must be reachable with the lid fitted — OI-9 |
| SW2 | User button | |

**The shared oscillator.** RP2040 accepts an external clock on XIN, and FE1.1s runs from
12 MHz. One 12 MHz CMOS oscillator can therefore serve both, replacing two crystals and four
load capacitors — and it closes OI-2 without adding area. This only works if the hub chosen
is a 12 MHz part; USB2514B needs 24 MHz and would need its own oscillator. That trade is:

| | FE1.1s | USB2514B |
|---|---|---|
| Crystal | 12 MHz — **shares Y1** | 24 MHz — needs its own |
| Cost | Low | Higher |
| USB compliance / reputation | Adequate, widely used, less rigorous | Better characterised |
| Area | Smaller | Larger |

**OPEN.** Since this board's job is to be trusted about what it measures, the hub's signal
quality matters more than usual. Resolve in `requirements/parts.md` against assembly-pool
stock, and be willing to pay for USB2514B and a second oscillator.

---

## 7. Budgets and calculations

### 7.1 Upstream power

| Item | Value |
|---|---|
| Port load, both channels at 1 A | 2 × 1 A × 5 V = 10.0 W |
| Buck input at 90 % efficiency | 11.11 W |
| Board rails (RP2040 + hub + analog, ~200 mA at 3.3 V) | 0.66 W |
| **Total** | **11.77 W → 1.31 A at 9 V** |

**Therefore: full 2 × 1 A requires a PD source offering ≥ 9 V / 1.5 A (13.5 W).** A 9 V/2 A
(18 W) source gives comfortable margin. A source that grants only 5 V must derate the ports,
and firmware must enforce that rather than browning out. The derating table belongs in
`requirements/product.md`.

### 7.2 Downstream advertisement

The ports advertise via Rp on CC. 56 kΩ = USB default (500 mA), 22 kΩ = 1.5 A, 10 kΩ = 3.0 A.
Advertising more than the board can deliver is a defect, so Rp must track the granted
upstream contract:

- 9 V contract granted → advertise **22 kΩ (1.5 A)**.
- 5 V fallback → advertise **56 kΩ (default)**.

Implementation: 56 kΩ fixed, plus 36 kΩ switched in parallel by a FET (56 ∥ 36 = 21.9 kΩ).
Rp must remain gated by that port's own VBUS — a port whose load switch is open must not
present Rp. This is 4 resistors + 1 FET per port.

### 7.3 Fail-safe — why the bypass FETs default ON

If a bypass FET fails open, or firmware leaves the ladder in a low range while the DUT draws
full current:

| Stuck range | 1 A through it | Outcome |
|---|---:|---|
| HIGH (20 mΩ) | 20 mW | Fine |
| MID (2 Ω) | **2 W** | 1206 rated 0.25 W — destroyed |
| LOW (200 Ω) | **200 W** | Instantaneous failure |

During a *normal* range transition the exposure is ~2 µs, i.e. ~400 µJ at worst — trivial.
The danger is a *stuck* state. Hence:

- Gate pull-to-ON resistors on Q100/Q101/Q200/Q201, so the unpowered and the crashed states
  both sit at 20 mΩ.
- The window comparator forces the ladder up on over-range **without** MCU involvement.
- The MID and LOW shunts are specified for pulse energy, not just average power. This is a
  parts-selection constraint that must be carried into `requirements/parts.md` — an ordinary
  thick-film chip resistor's pulse rating is not automatic.

### 7.4 Resolution summary

| | Value |
|---|---|
| ADC LSB referred to current, LOW range | 14 pA (quantisation is not the limit) |
| Uncalibrated amp offset (±25 µV) referred to current, LOW range | 125 nA — **exceeds the 100 nA target** |
| Post-calibration drift (0.1 µV/°C × 20 °C) | 10 nA |
| Target floor | 100 nA |

The margin exists only because of zero-calibration. Any design change that removes it
invalidates the 0.1 µA claim.

---

## 8. Manual gates that ERC cannot cover

ERC will not catch any of these. They are checked by a human against the schematic, and the
check is recorded in the release notes with a name and a date.

| # | Gate | Verify | Expect |
|---|---|---|---|
| G1 | Bypass FET default state | Trace each gate net with power removed | Pulled to the ON side; ladder = 20 mΩ |
| G2 | Kelvin sense taps | Inspect each shunt's four connections | Force and sense taps separate at the pad, not joined on a plane |
| G3 | Sense pair routing | Inspect ISENSE_x_P/N | Routed as a tight pair, over quiet ground, not across the buck |
| G4 | Analog/digital ground | Inspect ground topology | Single tie point; no digital return current under the shunts or amp |
| G5 | Rp gating | Trace J2/J3 CC networks | Rp present only when that port's VBUS is present |
| G6 | Rp value vs. contract | Trace the 36 kΩ switch | Cannot present 22 kΩ while on a 5 V contract |
| G7 | Buck output setpoint | Check feedback divider arithmetic | 5.10 V ±1 %, and a schematic note saying why |
| G8 | USB serial number | Inspect firmware descriptor path | Derived per-unit from flash UID; never a constant |
| G9 | Oscillator fan-out | Check Y1 loading and any series termination | Both XIN loads within the oscillator's drive spec |
| G10 | ESD coverage | Count protected lines per connector | D+, D−, CC1, CC2, SBU1, SBU2, VBUS all covered |
| G11 | Comparator loop | Trace comparator → gate path | No MCU in the path; MCU can only observe and set thresholds |
| G12 | Shunt pulse rating | Read the datasheet pulse curve | MID and LOW shunts survive 1 A for 10 µs |

---

## 9. Part shortlist — all UNCONFIRMED

No part below has been checked against the JLCPCB **assembly-parts pool** (distinct from the
LCSC retail pool — CLAUDE.md §4). None may be treated as chosen. `requirements/parts.md` is
where each becomes confirmed, with a stock figure and a date.

| Function | Candidate | What must be confirmed |
|---|---|---|
| PD sink | CH224K | Assembly-pool stock; that 9 V request needs no firmware |
| Buck | TPS62933 / SY8205 / MP2338 class | ≥ 2.5 A, small inductor, assembly-pool stock |
| Hub | FE1.1s vs USB2514B | The trade in §6.2; stock for both |
| ADC | ADS131M02 | 2 ch simultaneous, 32 kSPS, internal ref adequacy, stock |
| Sense amp | Zero-drift current-sense amp, G = 50 | Offset ≤ 25 µV, drift ≤ 0.1 µV/°C, 5 V CM, stock |
| Sense mux | Low-leakage analog mux | Leakage, charge injection, 5 V CM, stock |
| Comparator | Fast comparator, ≤ 100 ns | Total loop ≤ 2 µs including gate drive |
| Load switch | ≥ 1.5 A, controlled slew | Slew slow enough not to trip the DUT's inrush |
| Shunt 20 mΩ | 2512, 4-terminal, ≤ 25 ppm/°C | TCR **specified**, not assumed; stock |
| Shunt 2 Ω / 200 Ω | 1206 / 0805, ≤ 50 ppm/°C | Pulse rating per G12 |
| Oscillator | 12 MHz CMOS | Drive capability for two loads |

---

## 10. Decisions closed in Rev0.1

| # | Decision | Date | Closes |
|---|---|---|---|
| D1 | Upstream is a USB-PD sink requesting 9 V, 5 V fallback | 2026-08-16 | OI-4 |
| D2 | ECAD tool is KiCad | 2026-08-16 | CLAUDE.md §10.4 |
| D3 | Range = 0.1 µA – 1 A via 3 ranges (20 mΩ / 2 Ω / 200 Ω) + mandatory zero-calibration | 2026-08-16 | OI-3 |
| D4 | Auto-ranging is hardware (comparator → gate), MCU observes only | 2026-08-16 | OI-3 |
| D5 | Sense topology B — mux selects Kelvin taps | 2026-08-16 | OI-11 |
| D6 | One 12 MHz CMOS oscillator shared by RP2040 and hub, **conditional on a 12 MHz hub** | 2026-08-16 | OI-2 (conditionally) |
| D7 | Upstream control interface is CDC-ACM ×2 (control + stream), driverless | 2026-08-16 | new |
| D8 | Rev0.1 sample rate target 32 kSPS | 2026-08-16 | new |
| D9 | Bypass FETs default ON (fail-safe to HIGH range) | 2026-08-16 | new |

---

## 11. OI-13 — Board area. **BLOCKING.**

The 60 × 24 mm outline in the mockup does not hold. Component area for the design above:

| Block | Area |
|---|---:|
| USB-C receptacles ×3 | 203 mm² |
| RP2040 + flash + oscillator + decoupling | 130 mm² |
| USB hub + decoupling | 75 mm² |
| PD sink + caps | 30 mm² |
| Buck + inductor + caps | 110 mm² |
| LDOs ×2 | 30 mm² |
| ADC + reference + anti-alias | 60 mm² |
| Analog channel ×2 | 300 mm² |
| ESD ×3, CC networks, output caps | 90 mm² |
| LEDs, switches, test points | 55 mm² |
| **Total component area** | **1083 mm²** |

Against candidate outlines:

| Outline | Area | Density | Verdict |
|---|---:|---:|---|
| 60 × 24 | 1440 mm² | 75 % | **Not routable** |
| 70 × 30 | 2100 mm² | 52 % | Tight |
| 80 × 30 | 2400 mm² | 45 % | Tight — viable on 4 layers with discipline |
| 85 × 35 | 2975 mm² | 36 % | Comfortable |
| 90 × 40 | 3600 mm² | 30 % | Comfortable |

45 % is roughly the ceiling for a routable 4-layer board carrying fine-pitch QFNs, three
USB-C connectors, differential pairs and a quiet analog section. 75 % is not a matter of
trying harder.

**Options, in the order I would take them:**

1. **Grow the board to 80 × 30 mm** (4-layer). Keeps both measured channels and the full
   range. The enclosure grows with it; the mockup's case model becomes obsolete.
2. **85 × 35 mm** if the analog section wants more separation from the buck than 80 × 30
   allows. This is the low-risk choice.
3. **Keep 60 × 24 mm and measure only one channel** — port B becomes switch-only, no shunt
   ladder. Saves ~150 mm² and an ADC channel. Still ~65 % density; probably still too dense.
4. **Two boards** (hub+power / meter) stacked. Solves area, roughly doubles mechanical and
   assembly cost and adds a connector in the current path — which is exactly where you least
   want a connector.

**Recommendation: option 1 (80 × 30 mm, 4 layers).** It is the smallest outline that keeps
everything the product is supposed to do.

**Consequences to follow past this decision** (CLAUDE.md §3, easy-stick 14.4): the enclosure
model, the mounting-hole pattern, the lid PCB outline, the port pitch, and every dimension in
`mockup/` are invalidated by a new outline. OI-1 (two USB-C plugs cannot be inserted at once,
10.8 mm pitch vs 12–14 mm overmoulds) is *not* solved by growing the board — it is solved by
moving J2 and J3 apart, which the extra length now makes possible. Re-check it explicitly.

---

## 12. What must happen before KiCad capture

1. **Resolve OI-13.** Outline is an input to capture, not an output. Blocking.
2. Choose the hub (FE1.1s vs USB2514B). D6 is conditional on this.
3. Confirm every part in Section 9 against the JLCPCB assembly pool, with stock figures and
   a date, in `requirements/parts.md`.
4. Write `requirements/product.md`: the derating table (§7.1), the LOW-range bandwidth
   limitation (§4 Condition 2), the COM-port contract (§3.3), VID/PID.
5. Decide whether U7's internal reference suffices, or U8 is needed.
6. Decide the comparator + range-logic implementation: discrete comparator plus gates, or a
   small logic device. The 2 µs budget in §4 is the acceptance criterion.
7. Settle whether `usb-power-hub` becomes its own Git repository. CLAUDE.md §2 and §3 assume
   Git-tracked change control; today this directory sits inside `C:\Codes`, where
   `tsuyoshi-otake/**` is gitignored, so none of it is under version control. Nothing here is
   recoverable until that is fixed.

---

## 13. Change log

| Rev | Date | Change |
|---|---|---|
| 0.1 | 2026-08-16 | Opened. D1–D9 closed. OI-2/3/4/11 closed by decision. OI-13 (board area) opened as blocking. No part confirmed; no capture started. |
