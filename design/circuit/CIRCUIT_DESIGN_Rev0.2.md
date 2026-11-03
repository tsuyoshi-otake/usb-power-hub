# USB Power-Control Hub — Circuit Design Rev0.2

**State: WIP — MANUFACTURING PROHIBITED**
Date opened: 2026-08-16 (Rev0.1). Revised: 2026-11-03 (Rev0.2).

This document *is* the schematic at this stage. KiCad capture transcribes what is settled
here; it is not where the design happens (CLAUDE.md Section 2). Nothing in this file has been
built or measured. Every part number below is a *candidate* until `requirements/parts.md`
records a confirmed JLCPCB assembly-pool figure against it.

Read this with CLAUDE.md Section 11 (Open Issues) open. Companion documents:
`requirements/product.md` (what the product must do — authority), `requirements/verification.md`
(how each requirement is proven), `requirements/parts.md` (candidates, stock, datasheet facts).

Rev0.1 closed OI-2, OI-3 and OI-4 by decision and opened OI-13. **Rev0.2** records the user's
2026-11-03 decisions D10 (85 × 35 mm, 4 layers) and D11 (USB2514B) with their consequences
(D6 superseded, D12), corrects three Rev0.1 calculations (§3.1 port voltage, §7.1 power budget,
§7.3 stuck-range dissipation), adds the noise budget (§4.1) and the clock tree (§6.3), and opens
OI-16 – OI-22. Items Claude proposes but the user has not approved are in Section 14 and are
**not** decisions.

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
| 7 | ~~Board outline 60 × 24 mm~~ (historical, from `mockup/board-model.js`) | — | **Superseded by fact 9** |
| 8 | All designators/values in `mockup/` are placeholders | CLAUDE.md §0 | Settled |
| 9 | Board outline 85 × 35 mm, 4 layers | User decision, 2026-11-03 (D10) | Settled |
| 10 | USB hub is USB2514B | User decision, 2026-11-03 (D11) | Settled |
| 11 | Part parameters quoted in Rev0.2 | Manufacturer datasheets fetched 2026-11-03, cited per part in `requirements/parts.md` | High for the parameters cited; nothing else about those parts is confirmed |

Everything else below is derived by calculation in this document, or is explicitly marked OPEN.

---

## 2. What this changes versus the mockup

| Mockup showed | Rev0.1 says | Why |
|---|---|---|
| Rd-only upstream, no PD | CH224K-class PD sink, request 9 V | Closes OI-4. 2 × 1 A at 5 V is 10 W; you cannot get that from a 5 V/500 mA contract |
| 4 shunts (10 mΩ / 1 Ω / 100 Ω / 1 k), 1 FET per channel | 3 shunts (20 mΩ / 2 Ω / 200 Ω), 2 bypass FETs + sense mux per channel | Closes OI-3. 4 shunts with 1 switch is not a controllable ladder |
| No comparator | Window comparator per channel, hardware range control | µs-scale ranging cannot be done by MCU polling |
| 12 MHz crystal for MCU only, no hub clock | Rev0.1: one shared 12 MHz oscillator (D6). **Rev0.2: superseded by D11/D12** — Y1 12 MHz → RP2040, Y2 24 MHz → USB2514B | D11 chose a 24 MHz hub, so sharing is impossible |
| 2-terminal shunts | 4-terminal (Kelvin) for the 20 mΩ; Kelvin *land pattern* for the others | Closes OI-11 |
| 6-layer stackup | 4 layers (D10) | OI-10 — no differential pair count justifies 6 |
| 60 × 24 mm outline | 85 × 35 mm (D10) | OI-13 — 75 % component density is not routable; 36 % is comfortable |
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
            └── U2  regulator (buck; buck-boost if OI-17 says so) ──► V5P1 (5.10 V)
                     L1
          V5P1 ──┬── U3  3.3 V digital  ──► V3P3   (P5: small buck or SOT-223 LDO — OI-18)
                 ├── U3B LDO, low-noise ──► V3P3A  (analog, separate)
                 ├── [ ladder A ] ── U13 load switch ── VBUS_A ── J2
                 └── [ ladder B ] ── U23 load switch ── VBUS_B ── J3
```

**Rev0.2 correction — where the 3.3 V rails come from.** The Rev0.1 drawing hung U3 (and,
ambiguously, U3B) on VPD. At the ~200 mA board load (§7.1), a 9 V → 3.3 V linear regulator
dissipates (9 − 3.3) × 0.2 = **1.14 W**; at the 187 °C/W of a SOT-23-5 (TPS7A20 DBV datasheet
figure) that is a **213 °C** junction rise. Not buildable. Rev0.2 draws both rails from V5P1;
how the digital rail is made is OI-18 (Section 14, P5). The analog rail carries ≤ 10 mA, so a
low-noise LDO from V5P1 dissipates ≤ 18 mW.

The buck sets **5.10 V**, not 5.00 V, to leave headroom for the series drop between V5P1 and
the DUT. This is a decision, not an accident — record it in the KiCad schematic as a note next
to U2's feedback divider.

**Rev0.2 correction — what the DUT actually sees.** Rev0.1 claimed ≥ 5.05 V at the DUT,
assuming a 20 mV ladder and a ~30 mV load switch. With the candidate parts, the HIGH-range path
at 1 A is:

| Element | Resistance | Drop at 1 A | Drop at 1.5 A | Source |
|---|---:|---:|---:|---|
| RS1 shunt | 20 mΩ | 20 mV | 30 mV | §4 |
| Q100 + Q101 bypass FETs, in series | 2 × 8.9 mΩ (max) | 17.8 mV | 26.7 mV | CSD25402Q3A, V<sub>GS</sub> = −4.5 V |
| U13 load switch | 80 mΩ (typ) | 80 mV | 120 mV | SY6280AAC |
| **Total** | **117.8 mΩ** | **118 mV** | **177 mV** | |

So the DUT sees **4.98 V** typical at 1 A (4.93 V with the buck at −1 %), and 4.92 V / 4.87 V at
1.5 A — inside the 4.75 V vSafe5V minimum, but not the 5.05 V Rev0.1 promised. Copper and the
connector add more. Whether to raise the setpoint is tied to the regulator choice (OI-17).

**Why buck from 9 V instead of passing 5 V straight through.** A pass-through rail inherits
every millivolt of upstream cable IR drop and every wart of the charger's regulation, and
those land directly on the DUT. An instrument should present a rail it controls. It also
decouples us from what a given source offers at 5 V — 9 V/2 A sources are far more common
than 5 V/3 A ones.

**Rev0.2 caveat — OI-17.** That last sentence is true of *chargers*. J1 is the only power input,
and J1 is also the data upstream, so in normal use it is plugged into the **host PC**. PC USB-C
ports commonly offer only 5 V (vSafe5V, with 1.5 A or 3 A Type-C current). If so, the 9 V
request fails, VPD is ~5 V, and a buck **cannot** produce 5.10 V from it. TPS62130, the
shortlisted buck with a 100 % duty-cycle mode, then passes VPD through minus its own drop;
TPS62933 has no 100 % mode in its datasheet. Whether the intended host offers 9 V is a fact
about the user's PCs, not something this document can settle — see OI-17.

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
   If instead you sense across the whole ladder, two R<sub>DS(on)</sub> (8.9 mΩ max each for
   CSD25402Q3A, TC ≈ +4000 ppm/°C) are in series with a 20 mΩ shunt (TC ≤ 25 ppm/°C) and
   dominate the temperature error — (2 × 8.9 × 4000 + 20 × 25) / 37.8 ≈ **1900 ppm/°C** on the
   total, i.e. ~3.8 % over a 20 °C swing. That is not an instrument. Section 5 records the
   alternatives considered. *(Rev0.1 quoted ~1300 ppm/°C using 5 mΩ FETs and a 15 ppm/°C
   shunt; Rev0.2 uses the candidate FET's datasheet maximum and the shunt requirement.)*

2. **Every range is scaled to the same 20 mV full-scale**, so one amplifier gain and one ADC
   input range serve all three. Range switching changes only the scale factor applied in
   software, never the analog gain.

3. **The bypass FETs default ON** (gate pull-to-ON resistors). A firmware crash, a brownout,
   or an unprogrammed board leaves the ladder at 20 mΩ. Section 7.3 shows why the opposite
   default destroys the board. **Rev0.2:** the pull resistor sets the *default*, not the
   *speed*. Turning a CSD25402Q3A on moves Q<sub>g</sub> = 9.7 nC (max); doing it in 0.5 µs,
   a quarter of the 2 µs budget, needs ≈ 20 mA of active gate drive. A 100 kΩ pull-down
   alone takes milliseconds. The up-range edge must be actively driven (P8).

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

**Rev0.2 — the exact rate follows the ADC clock (§6.3).** ADS131M02 has no internal oscillator
for its modulator: it needs CLKIN, 0.3 – 8.4 MHz in high-resolution mode (8.192 MHz nominal,
64 kSPS maximum). With CLKIN = 8.000 MHz from RP2040 (P6), OSR = 128 gives **31.25 kSPS** —
D8's "32 kSPS" in practice. With the per-sample range code and flags the stream needs
(`requirements/product.md` REQ-HOST-05): 2 ch × 3 B + 1 B flags = 7 B per sample pair,
31.25 k × 7 B = 219 kB/s ≈ **18 %** of Full-Speed bulk.

The hub (U6) enumerates with Microchip's own VID/PID; only the RP2040 function behind port 1
needs an ID of ours (VID/PID still OPEN — `requirements/product.md` REQ-HOST-06).

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
| LOW | 200 Ω | 100 µA | 20 mV | 2 µW | 0805, Kelvin land, ≤ 50 ppm/°C; Rev0.2: rated ≥ 0.25 W for the stuck case (§7.3), which may force 1206 |

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

### 4.1 Noise — Rev0.2 addition

Rev0.1 argued the 0.1 µA floor from offset and drift only. Noise decides it per bandwidth.
INA190 input-referred voltage noise density is **75 nV/√Hz** (datasheet); referred to current
it is 75 nV/√Hz ÷ R<sub>shunt</sub>. Shunt Johnson noise (1.8 nV/√Hz for 200 Ω) is negligible
beside it. The 15.6 kHz column is the Nyquist bound at 31.25 kSPS — an upper bound, since the
ADC's sinc filter is narrower.

| Range | Current noise density | rms at 500 Hz (≈ 1 kSPS output) | rms at 15.6 kHz (raw 31.25 kSPS) |
|---|---:|---:|---:|
| HIGH (20 mΩ) | 3.75 µA/√Hz | 84 µA | 469 µA |
| MID (2 Ω) | 37.5 nA/√Hz | 0.84 µA | 4.7 µA |
| LOW (200 Ω) | 0.375 nA/√Hz | 8.4 nA | 47 nA |

**Consequence:** 0.1 µA is resolved with margin (12 σ) at output rates up to ~1 kSPS. A single
raw 31.25 kSPS LOW-range sample has ~47 nA rms noise, so 0.1 µA is only ~2 σ there. The
resolution requirement must therefore name its bandwidth — it does in
`requirements/product.md` REQ-MEAS-04. This is a property of the amplifier, not of the ADC.

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
| A | One amp across the whole ladder; bypass FETs inside the sensed span | **Rejected.** FET R<sub>DS(on)</sub> TC ≈ 4000 ppm/°C swamps a ≤ 25 ppm/°C shunt on the HIGH range; ≈ 1900 ppm/°C on the total, ~3.8 % error over 20 °C (§3.2; Rev0.1 said 2.6 %), and it self-heats at 1 A |
| B | One amp, analog mux selects which shunt's Kelvin pair is sensed | **Selected.** Switch resistance is outside the sensed span and irrelevant into a high-Z amp input. Cost: one dual mux per channel |
| C | One amp permanently across each shunt (3 amps/channel), mux the low-voltage outputs | Metrologically cleanest, allows per-range gain optimisation. **Rejected on area** — 6 amps total, and Section 11 is already the binding constraint. Recorded as the fallback if B shows mux leakage or charge-injection problems in Rev0.2. **Rev0.2: the rejection reason no longer holds** — D10 took the board from 75 % to 36 % density. Re-evaluation is OI-19 |

The mux (U10/U20) must tolerate a ~5 V common mode, and its leakage must be small against
the smallest sense current. Note the mux sits at the *amplifier input*, where current is
picoamps, so its on-resistance does not matter — only its leakage and charge injection do.

**Rev0.2 — constraints Rev0.1 left implicit.**

- *Mux supply.* "Tolerate ~5 V common mode" means the mux's analog range must include V5P1
  (5.10 V nominal). A mux powered from V3P3A cannot pass it; its input clamps would conduct
  straight into the sense node. The mux must be powered from a rail above V5P1 — VPD — and so
  must be a ≥ 10 V-class part. In the 5 V fallback V5P1 ≤ VPD still holds. The two such
  candidates found have thin assembly stock (TMUX6209PWR 225, ADG1209YRZ-REEL7 919 in SOIC-16;
  `requirements/parts.md`). This is half of OI-19.
- *Amplifier input bias current.* The bias current drawn by the amp's IN− terminal comes from
  the load-side node, so it flows through the sensed shunt and reads as load current. On the
  LOW range, every nanoamp of I<sub>IB</sub> is a nanoamp of error, and its drift is not removed
  by zero calibration. **Requirement: I<sub>IB</sub> ≤ 3 nA (max).** INA190 meets it (0.5 nA
  typ, 3 nA max). An ordinary current-sense amplifier biased from its inputs can draw tens of
  µA — larger than the whole LOW range — so this is a selection constraint, not a footnote.

---

## 6. Nets and designators

### 6.1 Power nets

| Net | Nominal | Source | Notes |
|---|---|---|---|
| `VBUS_IN` | 5 V or PD | J1 | Before PD negotiation this is 5 V |
| `VPD` | 9 V (5 V fallback) | after PD sink | Firmware must be able to read which contract was granted |
| `V5P1` | 5.10 V | U2 buck | Port rail. Sized for 2.5 A |
| `V3P3` | 3.3 V | U3, fed from V5P1 (Rev0.2) | Digital: RP2040, hub, flash. ≤ 190 mA |
| `V3P3A` | 3.3 V | U3B, fed from V5P1 (Rev0.2) | Analog: amps, comparators, ADC AVDD. ≤ 10 mA. Separate regulator, single-point tie. (The sense mux, if topology B stays, is powered from VPD — §5) |
| `VBUS_A` / `VBUS_B` | 4.98 V typ at 1 A (Rev0.2, §3.1) | after ladder + load switch | What the DUT actually sees. Also sensed by RP2040 ADC (P7) |
| `EN_A` / `EN_B` | 3.3 V logic | RP2040 GPIO only | Load-switch enable; resistor to GND, so OFF whenever RP2040 is not driving it (P2, P3) |

### 6.2 Designators

| Ref | Part | Notes |
|---|---|---|
| J1 | USB-C receptacle, upstream | CC1/CC2 to U1 |
| J2, J3 | USB-C receptacle, DUT A/B | Rp on CC, gated by that port's VBUS |
| U1 | PD sink controller | Candidate: **CH224Q** (Rev0.2, P1). CH224K had 0 assembly stock on 2026-11-03 and cannot report the granted current |
| U2 | V5P1 regulator, ≥ 2.5 A | 9 V → 5.10 V. Buck vs buck-boost is OI-17; rating depends on OI-16 |
| U3, U3B | V3P3 digital, V3P3A analog | Both from V5P1. U3 topology is OI-18 |
| U4 | RP2040 | QFN-56 |
| U5 | QSPI flash | USON-8, ≥ 2 MB |
| U6 | USB 2.0 HS hub, 4-port | **USB2514B** (D11). 24 MHz clock from Y2 |
| U7 | ADC, 24-bit, 2 ch simultaneous | Candidate: ADS131M02 (TSSOP-20 or WQFN-20 3 × 3; Rev0.1's "QFN-24" was wrong). Needs CLKIN — §6.3 |
| U8 | Voltage reference | Only if U7's internal ref proves insufficient — OPEN |
| U10 / U20 | Sense mux, ch A / ch B | Dual, 3:1 or 2× SPDT |
| U11 / U21 | Current-sense amp, G = 50, zero-drift | Ch A / ch B |
| U12 / U22 | Window comparator + range logic | Ch A / ch B |
| U13 / U23 | Load switch, current-limited, reverse-blocking, output discharge | Ch A / ch B. Candidate SY6280AAC (P2) |
| Y1 | 12 MHz crystal | RP2040 XOSC only (D12) |
| Y2 | 24 MHz crystal | USB2514B XTALIN/CLKIN only (D12) |
| L1 | Buck inductor | Value with U2 |
| F1 | Upstream protection | eFuse or PTC — OPEN, see OI-7 |
| R100 / R200 | 20 mΩ, 2512, 4-terminal | HIGH shunt, ch A / ch B |
| R101 / R201 | 2 Ω, 1206, Kelvin land | MID shunt |
| R102 / R202 | 200 Ω, 0805, Kelvin land | LOW shunt |
| Q100, Q101 / Q200, Q201 | Bypass FETs | Default ON |
| D1–D3 | USB ESD arrays | One per connector, must cover D+/D−/CC/SBU |
| SW1 | BOOTSEL | Must be reachable with the lid fitted — OI-9 |
| SW2 | User button | |

**The shared oscillator — historical (Rev0.1), superseded by D11.** Rev0.1 noted that RP2040
accepts an external clock on XIN and that FE1.1s runs from 12 MHz, so one 12 MHz CMOS
oscillator could serve both (D6). That only worked with a 12 MHz hub. The trade as it stood:

| | FE1.1s (rejected) | USB2514B (chosen, D11) |
|---|---|---|
| Crystal | 12 MHz — could have shared Y1 | 24 MHz — needs its own (Y2) |
| Cost | Low | Higher |
| USB compliance / reputation | Adequate, widely used, less rigorous | Better characterised |
| Area | Smaller | Larger — affordable after D10 |

**Closed 2026-11-03 by D11** (user): the board's job is to be trusted about what it measures,
so the hub's signal quality outweighs one extra crystal. USB2514B has assembly stock in three
variants (`requirements/parts.md`).

### 6.3 Clock tree — Rev0.2

| Clock | Source | Load | Basis |
|---|---|---|---|
| 12 MHz | Y1 crystal on RP2040 XIN/XOUT | RP2040 XOSC only | D12; RP2040 PLLs derive 48 MHz USB and the system clock from it |
| 24 MHz | Y2 crystal on USB2514B XTALIN/CLKIN | USB2514B only | D12; datasheet DS00001692A: "24 MHz crystal or external 24 MHz clock" |
| 8.000 MHz | RP2040 GPOUT pin, clk_usb (48 MHz) ÷ 6 | ADS131M02 CLKIN | P6 (proposed). An integer divide, so no fractional-divider jitter; within the 0.3 – 8.4 MHz high-resolution range |

Each oscillator now has exactly one load, so G9's fan-out check reduces to "one load each".
The ADC clock was missing in Rev0.1 entirely (OI-22).

---

## 7. Budgets and calculations

### 7.1 Upstream power

**Rev0.2 correction.** Rev0.1 counted the board rails at 3.3 V × 200 mA = 0.66 W. A linear
regulator draws its *output* current at its *input* voltage, so the rails cost what they draw
from their source rail. With both rails on V5P1 (§3.1):

| Item | Value |
|---|---|
| Port load, both channels at 1 A, drawn from V5P1 | 2 × 1 A × 5.10 V = 10.20 W |
| Board rails, ~200 mA drawn from V5P1 (190 mA digital + 10 mA analog) | 0.2 A × 5.10 V = 1.02 W |
| Regulator output total | 11.22 W |
| **Regulator input at 90 % efficiency** | **12.47 W → 1.39 A at 9 V** |

For comparison, the Rev0.1 drawing (rails on VPD) costs 10.20 W / 0.9 + 9 V × 0.2 A = 13.13 W.

**Therefore: full 2 × 1 A still fits a PD source offering 9 V / 1.5 A (13.5 W), with 1.0 W
(8 %) margin.** A 9 V/2 A (18 W) source gives comfortable margin. If both ports may draw
**1.5 A** (what a 22 kΩ Rp advertises), the input is (2 × 1.5 × 5.10 + 1.02) / 0.9 = **18.1 W**,
more than a 9 V/2 A source and more than the 2.5 A U2 rating (3.0 A + 0.2 A). That conflict is
OI-16. A source that grants only 5 V must derate the ports, and firmware must enforce that
rather than browning out; the derating rule is in `requirements/product.md` REQ-PWR-04.

### 7.2 Downstream advertisement

The ports advertise via Rp on CC. 56 kΩ = USB default (500 mA), 22 kΩ = 1.5 A, 10 kΩ = 3.0 A.
Advertising more than the board can deliver is a defect, so Rp must track the granted
upstream contract:

- ~~9 V contract granted → advertise **22 kΩ (1.5 A)**.~~
- ~~5 V fallback → advertise **56 kΩ (default)**.~~

**Rev0.2: the two rules above are withdrawn pending OI-16.** "9 V granted" says nothing about
*how much* current was granted. A 9 V / 1 A source is a valid PD source, and two ports
advertising 1.5 A need ≈ 18 W (§7.1). Rp must be chosen from the granted *power* — which CH224Q
reports (register 0x50, maximum current at the negotiated level, 50 mA units; P1) — and from
how that power is shared between two ports. Even "Default" Rp promises USB 2.0 default current
(500 mA) per port; two ports behind a 5 V / 500 mA upstream cannot honour that either.

Implementation (unchanged): 56 kΩ fixed, plus 36 kΩ switched in parallel by a FET
(56 ∥ 36 = 21.9 kΩ). Rev0.1 gated Rp by that port's own VBUS. **Rev0.2 proposes gating it by
EN_x instead** (P3): a DUT that back-feeds VBUS while the port is OFF would otherwise keep Rp
present, so it never sees a detach. This is 4 resistors + 1 FET per port either way.

### 7.3 Fail-safe — why the bypass FETs default ON

If a bypass FET fails open, or the ladder is left in a low range while the DUT demands full
current.

**Rev0.2 correction.** Rev0.1 tabulated "1 A through it" for every range, including 200 W in
the 200 Ω shunt. A 5.10 V rail cannot drive 1 A through 200 Ω; that would need 200 V. The
current through a stuck shunt is bounded twice: by the rail across the remaining ladder,
V5P1 / R<sub>ladder</sub>, and by the load switch's current limit. Worst case is a shorted DUT:
I = min(V5P1 / R<sub>ladder</sub>, I<sub>lim</sub>), P = I² × R<sub>shunt</sub>. With SY6280AAC
set for 1.6 A nominal, I<sub>lim</sub> ≤ 2.0 A (its device maximum, and the +25 % tolerance
bound):

| Stuck range | R<sub>ladder</sub> | V5P1 / R<sub>ladder</sub> | I (limited to 2.0 A) | P in that shunt | Outcome |
|---|---:|---:|---:|---:|---|
| HIGH (20 mΩ) | ≈ 38 mΩ | 134 A | 2.0 A | 0.08 W | Fine (2512) |
| MID (2 Ω) | ≈ 2.03 Ω (20 mΩ + 2 Ω + Q101) | 2.51 A | 2.0 A | **8.0 W** (12.6 W if the limit fails) | 1206 destroyed |
| LOW (200 Ω) | ≈ 202 Ω | 25.2 mA | 25.2 mA | **0.13 W**, continuous | Above a typical 0805 rating (0.125 W) — specify ≥ 0.25 W or 1206 |

The MID row is the real hazard and Rev0.1's conclusion stands: a stuck MID range destroys its
shunt. The LOW row is not an "instantaneous failure": its dissipation is capped near 0.13 W by
physics, and the DUT simply browns out at 25 mA.

During a *normal* range transition the port capacitor holds the shunt voltage at ≤ 200 mV for
≤ 2 µs (Condition 2): (0.2 V)² / 2 Ω × 2 µs = 40 nJ on MID. Even a hard short arriving while on
MID costs 8 W × 2 µs = 16 µJ before the comparator up-ranges. *(Rev0.1's "~400 µJ" was derived
from the impossible 200 W.)* The danger is a *stuck* state. Hence:

- Gate pull-to-ON resistors on Q100/Q101/Q200/Q201, so the unpowered and the crashed states
  both sit at 20 mΩ.
- The window comparator forces the ladder up on over-range **without** MCU involvement.
- The MID and LOW shunts are specified for pulse energy, not just average power. This is a
  parts-selection constraint that must be carried into `requirements/parts.md` — an ordinary
  thick-film chip resistor's pulse rating is not automatic.
- **Rev0.2:** the comparator cannot help if a bypass FET has *failed open* — it can only
  command the FET. Firmware covers that case: while the range state reads HIGH, a VBUS_x more
  than 300 mV below V5P1 means current is flowing through a shunt that should be bypassed, and
  the port is switched OFF within 10 ms. The MID shunt must survive that window:
  8 W × 10 ms = 80 mJ (G12).

### 7.4 Resolution summary

| | Value |
|---|---|
| ADC LSB referred to current, LOW range | 14 pA (quantisation is not the limit) |
| Uncalibrated amp offset (±25 µV) referred to current, LOW range | 125 nA — **exceeds the 100 nA target** |
| Post-calibration drift (0.1 µV/°C × 20 °C) | 10 nA |
| Amplifier input bias current, INA190, max (Rev0.2, §5) | 3 nA |
| Noise, LOW range, at ≈ 1 kSPS output (Rev0.2, §4.1) | 8.4 nA rms |
| Noise, LOW range, raw 31.25 kSPS (Rev0.2, §4.1) | 47 nA rms |
| Target floor | 100 nA |

The margin exists only because of zero-calibration. Any design change that removes it
invalidates the 0.1 µA claim. Rev0.2 adds a second condition: the 0.1 µA claim holds at
output rates up to ~1 kSPS, not per raw sample.

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
| G5 | Rp gating | Trace J2/J3 CC networks | Rp present only when that port's EN_x is high (Rev0.2 P3; Rev0.1 said "VBUS is present") |
| G6 | Rp value vs. contract | Trace the 36 kΩ switch | Cannot present 22 kΩ unless the rule chosen in OI-16 allows it |
| G7 | Buck output setpoint | Check feedback divider arithmetic | 5.10 V ±1 %, and a schematic note saying why |
| G8 | USB serial number | Inspect firmware descriptor path | Derived per-unit from flash UID; never a constant |
| G9 | Oscillator fan-out | Check Y1 and Y2 loading and any series termination | Y1 drives only RP2040 XIN, Y2 only USB2514B XTALIN; load capacitors match each crystal's C<sub>L</sub> (Rev0.2, §6.3) |
| G10 | ESD coverage | Count protected lines per connector | D+, D−, CC1, CC2, SBU1, SBU2, VBUS all covered (or SBU left unconnected and stated) |
| G11 | Comparator loop | Trace comparator → gate path | No MCU in the path; MCU can only observe and set thresholds |
| G12 | Shunt pulse rating | Read the datasheet pulse curve | Rev0.2: MID shunt survives 8 W for 10 ms (80 mJ, §7.3); LOW shunt rated ≥ 0.25 W continuous. *(Rev0.1 said "1 A for 10 µs", which the LOW range cannot carry.)* |
| G13 | Port-enable ownership (Rev0.2) | Trace EN_A/EN_B | Driven only by RP2040 GPIO, resistor to GND; USB2514B PRTPWR pins not connected to it |
| G14 | Hub straps (Rev0.2) | Inspect USB2514B PRTPWR[x]/BC_EN[x] | Strapped to the battery-charging-disabled level; the hub asserts PRTPWR as soon as configuration completes, so it must never drive a load switch here |
| G15 | Mux supply (Rev0.2, if topology B is kept) | Trace U10/U20 VDD | Powered from VPD, not V3P3A; part rated ≥ 10 V |

---

## 9. Part shortlist — moved

**Rev0.2: the shortlist now lives in `requirements/parts.md`**, the single place where a
candidate's assembly-pool stock (2026-11-03), part class, datasheet-verified parameters, and
remaining checks are recorded. Keeping a second copy here would let the two drift. The
selection constraints this document derives — I<sub>IB</sub> ≤ 3 nA (§5), mux supply above
V5P1 (§5), Q<sub>g</sub> versus gate drive (§3.2), 100 % duty or buck-boost (§3.1, OI-17),
stuck-range ratings (§7.3) — are stated there per part, with a pointer back to the section
that derives them.

---

## 10. Decisions closed

Only decisions the user has made, or their unavoidable consequences, appear here. Proposals
are in Section 14.

| # | Decision | Date | By | Closes |
|---|---|---|---|---|
| D1 | Upstream is a USB-PD sink requesting 9 V, 5 V fallback | 2026-08-16 | User | OI-4 (see OI-17) |
| D2 | ECAD tool is KiCad | 2026-08-16 | User | CLAUDE.md §10.4 |
| D3 | Range = 0.1 µA – 1 A via 3 ranges (20 mΩ / 2 Ω / 200 Ω) + mandatory zero-calibration | 2026-08-16 | Rev0.1 design | OI-3 |
| D4 | Auto-ranging is hardware (comparator → gate), MCU observes only | 2026-08-16 | Rev0.1 design | OI-3 |
| D5 | Sense topology B — mux selects Kelvin taps | 2026-08-16 | Rev0.1 design | OI-11 (re-evaluation: OI-19) |
| D6 | ~~One 12 MHz CMOS oscillator shared by RP2040 and hub, conditional on a 12 MHz hub~~ **SUPERSEDED 2026-11-03 by D11/D12** — the condition failed | 2026-08-16 | Rev0.1 design | ~~OI-2~~ |
| D7 | Upstream control interface is CDC-ACM ×2 (control + stream), driverless | 2026-08-16 | User | new |
| D8 | Rev0.1 sample rate target 32 kSPS | 2026-08-16 | Rev0.1 design | new |
| D9 | Bypass FETs default ON (fail-safe to HIGH range) | 2026-08-16 | Rev0.1 design | new |
| D10 | Board outline **85 × 35 mm, 4 layers** (Rev0.1 §11 option 2, "the low-risk choice") | 2026-11-03 | User | OI-13, OI-10 |
| D11 | USB hub is **USB2514B** | 2026-11-03 | User | CLAUDE.md §10.5 hub choice; supersedes D6 |
| D12 | Two independent clocks: Y1 12 MHz crystal → RP2040; Y2 24 MHz crystal → USB2514B. Consequence of D11, not a free choice: the hub accepts only 24 MHz | 2026-11-03 | Consequence of D11 | OI-2 (reopened by D11, closed by D12) |

---

## 11. OI-13 — Board area. **CLOSED by D10 (2026-11-03): 85 × 35 mm, 4 layers.**

Kept as the record of why the outline changed. The user chose option 2 below. At 85 × 35 mm the
Rev0.1 component area is 36 % of the board, leaving room for the extra Y2 crystal and, if
OI-19 goes that way, four more amplifiers.

The 60 × 24 mm outline in the mockup (historical) does not hold. Component area for the
Rev0.1 design:

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

Status as of Rev0.2 (2026-11-03):

1. ~~Resolve OI-13.~~ **Done** — D10.
2. ~~Choose the hub.~~ **Done** — D11; D6 superseded by D12.
3. Confirm every part against the JLCPCB assembly pool — **first pass done** in
   `requirements/parts.md` (2026-11-03). Two functions have no adequate candidate yet: the
   20 mΩ HIGH shunt (OI-20) and the 5 V-CM sense mux (OI-19). Recheck all stock before upload.
4. ~~Write `requirements/product.md`.~~ **Done** — derating rule (REQ-PWR-04), LOW-range bandwidth
   (REQ-MEAS-07), COM-port contract (REQ-HOST-04), VID/PID (REQ-HOST-06, still OPEN).
5. Decide whether U7's internal reference suffices. Its drift is 20 ppm/°C max (datasheet),
   comparable to the shunt TCR, so it suffices for any accuracy target looser than ~0.1 % over
   20 °C. Blocked on the accuracy target itself (OI-21).
6. Decide the comparator + range-logic implementation. The 2 µs budget in §4 is the acceptance
   criterion; Rev0.2 adds the gate-drive constraint (§3.2, P8). Still OPEN.
7. ~~Settle whether `usb-power-hub` becomes its own Git repository.~~ **Done** — commit
   `4dd10fb` (2026-11-03) closes OI-15.
8. **New in Rev0.2:** resolve OI-16 (port current policy), OI-17 (5 V host power), OI-18
   (3.3 V digital rail), OI-19 (sense topology), OI-20 (HIGH shunt), OI-21 (accuracy target),
   OI-22 (ADC clock), or accept the Section 14 proposals that close them.

---

## 13. Change log

| Rev | Date | Change |
|---|---|---|
| 0.1 | 2026-08-16 | Opened. D1–D9 closed. OI-2/3/4/11 closed by decision. OI-13 (board area) opened as blocking. No part confirmed; no capture started. |
| 0.2 | 2026-11-03 | D10 (85 × 35 mm, 4 L) and D11 (USB2514B) by the user; D6 superseded; D12. OI-13, OI-10 closed; OI-2 reopened and closed. Corrected §3.1 (LDO supply, DUT voltage), §3.2 (TC figure), §7.1 (rails at input voltage), §7.3 (stuck-range physics), G12. Added §4.1 noise, §6.3 clocks, I<sub>IB</sub> and mux-supply constraints, G13–G15, Section 14 proposals. Shortlist moved to `requirements/parts.md` with assembly-pool stock. OI-16 – OI-22 opened. Still no capture. |

---

## 14. Proposed — not decided

Claude's proposals from the 2026-11-03 review. **None is a decision until the user accepts
it**; on acceptance, move it to Section 10 with a D number. Each one names the issue it would
close.

| # | Proposal | Why | Closes |
|---|---|---|---|
| P1 | U1 = **CH224Q** (I2C, 0x22/0x23) instead of CH224K | CH224K: 0 assembly stock (2026-11-03). CH224Q: 16,744; register 0x50 reports the granted current, 0x60–0x8F the full source capability list — what OI-16 needs | Part of OI-16 |
| P2 | U13/U23 = **SY6280AAC** class load switch; EN to GND through a resistor | Datasheet: reverse blocking when disabled (no body diode), 150 Ω output discharge at shutdown, I<sub>lim</sub> = 6800 / R<sub>set</sub> (0.4 – 2 A), thermal shutdown with auto-retry. No fault pin, so firmware supervises from its own current and VBUS measurements | OI-7 (reverse current), part of REQ-PORT |
| P3 | RP2040 is the **only** owner of EN_A/EN_B; Rp gated by EN_x; USB2514B PRTPWR not connected to EN | The hub asserts PRTPWR as soon as its configuration completes, which would power ports at boot, against REQ-PORT-01. Gating Rp by EN rather than VBUS gives a clean detach even if a DUT back-feeds | REQ-PORT-06 |
| P4 | Re-evaluate D5: topology **C** (INA190A2 per shunt, 6 total) + ADS131M06, or a 3.3 V mux on amp outputs | D10 removed the area objection; the 5 V-CM mux must run from VPD, ≥ 10 V class, and both candidates have thin stock; C has no mux leakage or charge injection in the sense path | OI-19 |
| P5 | V3P3 from V5P1 via a small synchronous buck (SY8089 class) or a SOT-223 LDO; V3P3A from V5P1 via a low-noise LDO (TPS7A20 / LP5907 class) | Rev0.1's VPD-fed LDO burns 1.14 W in SOT-23-5. From V5P1 a SOT-23-5 still sees 0.34 W → 64 °C rise at 187 °C/W | OI-18 |
| P6 | ADS131M02 CLKIN = 8.000 MHz from RP2040 GPOUT (clk_usb ÷ 6); 31.25 kSPS | ADC needs an external clock (0.3 – 8.4 MHz); Rev0.1 had none. Integer division keeps jitter low | OI-22 |
| P7 | RP2040 ADC (GPIO26–29) senses VBUS_A, VBUS_B, VPD, V5P1 via dividers | Needed for CYCLE discharge confirmation, back-feed detection, under-voltage fault, and the open-FET check (§7.3) | REQ-PORT-03/04/05 |
| P8 | Active bypass-FET gate drive: ≥ 20 mA turn-ON (gate to GND); level-shifted turn-OFF to V5P1 | Q<sub>g</sub> 9.7 nC max must move in ≤ 0.5 µs; a 3.3 V GPIO cannot hold a P-FET at 5.1 V source OFF | Part of §12 item 6 |
| P9 | J2–J3 centre pitch ≥ **18 mm** | Overmoulds are 12–14 mm (OI-1); 18 mm leaves ≥ 4 mm between the widest pair. Verify with real cables | OI-1 (design input; still needs the cable check) |
| P10 | BOOTSEL: SW1 reachable through a lid pinhole **and** a `BOOT` command | Pinhole recovers a bricked board; the command avoids opening anything in normal updates | OI-9 |
| P11 | SWD on a Tag-Connect TC2030-NL footprint; test pads on VBUS_IN, VPD, V5P1, V3P3, V3P3A, VBUS_A, VBUS_B, GND | The footprint's alignment holes are the fixture datums OI-8 asks for | OI-8 |
| P12 | Heat-set M2 inserts in the printed tub, 4 points (one per corner) | Meets the ≥ 4 mm engagement and ≥ 3-point rules of CLAUDE.md §7 on an 85 × 35 mm board | OI-5 |
