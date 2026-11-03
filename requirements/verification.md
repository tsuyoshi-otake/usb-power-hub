# USB Power-Control Hub — Verification Plan

**State: WIP.** Opened 2026-11-03; revised for circuit Rev0.4 on 2026-11-03. Nothing below has
been executed — no board exists.

Every requirement in `requirements/product.md` is covered by at least one entry here, and
every entry cites the requirements it proves. Design-review gates G1 – G19 live in
`design/circuit/CIRCUIT_DESIGN_Rev0.4.md` Section 8; entries here reference them rather than
restate them. CLAUDE.md Section 8 ("Functional" gate) requires these to pass before release.

**Stages:** *Design review* (against schematic/layout, before order) · *Bench* (a hand-built
sub-circuit, before layout) · *Bring-up* (first article, bench) · *Production* (every unit, by
fixture).

**Rule for automated checks** (CLAUDE.md Section 8): a script that grades a result must say
what it cannot see, and must be shown failing on a deliberately corrupted input before its
pass counts. Entries that rely on a script note this under *Limits*.

**Common equipment:**
- 4-channel oscilloscope (≥ 100 MHz);
- 6½-digit DMM used as the reference ammeter;
- programmable electronic load with ≤ 10 µs step;
- bench supply with current readout;
- USB-C 5 V sources advertising Default, 1.5 A and 3.0 A, plus a USB-A charger with an
  A-to-C legacy cable;
- the intended host PCs;
- Type-C sink tester (Rd = 5.1 kΩ);
- ≥ 3 different USB-C cables, including the widest overmould on hand;
- an SWD probe with a TC2030-NL cable (debug only; programming uses the ROM USB bootloader).

---

## Power input

### V-PWR-01 — J4 advertisement readback
- **Covers:** REQ-PWR-01, REQ-PWR-02
- **When:** Bring-up
- **Method:** With J1 on a host PC, connect J4 in turn to each USB-C source, to the legacy
  cable, and to nothing. Read `STATUS?`. Then disconnect J4 and try `PORT A ON`. Measure the
  current J1 draws with all ports OFF and with both ports ON.
- **Pass:**
  - `J4=` matches each source's advertisement. The legacy cable gives `DEFAULT`; nothing
    connected gives `NONE`.
  - `VJ4` agrees with a DMM within 2 %.
  - With J4 absent, `PORT A ON` returns `ERR 04`.
  - J1 current is unchanged within 10 mA by port state: the ports draw nothing from J1.

### V-PWR-02 — Advertisement and budget rules
- **Covers:** REQ-PWR-03, REQ-PWR-04, REQ-PWR-05
- **When:** Design review (G6) + Bring-up
- **Method:**
  1. With a Default J4, enable A, then B.
  2. Repeat with a 1.5 A J4.
  3. Measure CC on J2/J3 with the sink tester.
  4. With a 1.5 A J4 and both ports ON, load A to 1.0 A and B to 0.6 A for 1 s, and scope the
     enable signals.
- **Pass:**
  - Default J4: A → `OK`; B → `ERR 04` with B OFF.
  - 1.5 A J4: both `OK`.
  - CC on each ON port reads the Default level (0.35–0.48 V across the 5.1 kΩ tester).
  - Overload case: A switches OFF 50–70 ms after the overload starts, `PORT A?` reports
    `FAULT:BUDGET`, and B stays ON.

## Port power control

### V-PORT-01 — Default OFF in every reset path
- **Covers:** REQ-PORT-01, REQ-PORT-06
- **When:** Design review (G13, G14) + Bring-up
- **Method:** Scope VBUS_A and VBUS_B, with 10 µF + 10 mA load on each, through each of:
  - first power-up with blank flash;
  - power-up with firmware;
  - brown-out (ramp J1 5 V → 2 V → 5 V at 1 V/ms);
  - watchdog reset (a test build that stops feeding it);
  - `BOOT`, and SW3 held at plug-in (ROM bootloader);
  - J1 unplugged with J4 present.

  Separately, with ports ON, send a USB hub-class `ClearPortFeature(PORT_POWER)` from the
  host (e.g. `uhubctl`).
- **Pass:**
  - In every reset path VBUS_x stays below 0.8 V, with no excursion above 0.8 V longer than
    10 µs.
  - The hub-class request leaves VBUS_x unchanged (single owner).
  - G13 and G14 pass.

### V-PORT-02 — Command contract
- **Covers:** REQ-PORT-02, REQ-HOST-04
- **When:** Bring-up + every firmware release
- **Method:** A host script sends every command in product.md §4.1, including each failure
  case, plus 10,000 random lines (random tokens, lengths 0 – 120, mixed terminators). It counts
  response lines and checks port state with `PORT x?` after each.
- **Pass:**
  - Exactly one response line per command line, and each response matches the table.
  - After every `ERR 04` from `ON`/`CYCLE` the port is OFF.
  - After every `ERR 01` / `ERR 02` / `ERR 08` both ports are in the state they had before
    the command.
  - `ERR 06` and `ERR 07` never appear (withdrawn).
- **Limits:** The script sees only the control port. It cannot see VBUS; V-PORT-03 does. It
  must first be run against a firmware build with a deliberately duplicated response line, and
  shown to fail.

### V-PORT-03 — CYCLE discharges before re-enabling
- **Covers:** REQ-PORT-03
- **When:** Bring-up
- **Method:** DUT side = 10 µF, and 10 µF + 10 µF, each with loads of 0, 10 mA and 1 A. Run
  `PORT A CYCLE 100` and `PORT A CYCLE 1000`, and scope VBUS_A.
- **Pass:**
  - VBUS_A is below 0.8 V before the port turns back ON, in every case including 20 µF with
    no load.
  - The OFF time is within ±10 ms of the request.
  - `OK` arrives after VBUS_A is back above 4.4 V.

### V-PORT-04 — Back-feed while OFF
- **Covers:** REQ-PORT-04
- **When:** Bring-up
- **Method:** Port A OFF. Apply 5.25 V from a bench supply to J2 VBUS and measure the current
  it delivers, and the voltage on VSUP_A and VBUS_IN (J4 disconnected). Then `PORT A?`.
- **Pass:**
  - The supply delivers 5.25 mA ± 10 %, which is the 1 kΩ discharge load and nothing else.
  - VSUP_A and VBUS_IN stay below 0.5 V, so no current reaches J4 or port B.
  - `PORT A?` reports `OK OFF`. Back-feed is not detected, by design.

### V-PORT-05 — Faults
- **Covers:** REQ-PORT-05
- **When:** Bring-up
- **Method:**
  - Step the electronic load from 0 to 1.3 A, then apply a hard short; scope the switch gate
    and VBUS_A.
  - Lower J4 (bench supply) to 4.3 V with a port ON.
  - Repeat the short with a firmware build that ignores the OC event.
  - Observe for 10 s after each trip.
- **Pass:**
  - The port opens within 10 µs of crossing 1.16 A (±3 %), and `PORT A?` reports
    `FAULT:OVERCURRENT`.
  - Under-voltage opens both ports 10–20 ms after V_J4 < 4.4 V, with `FAULT:UNDERVOLTAGE`.
  - No automatic re-enable within 10 s; `PORT A OFF` clears to `OFF`; `PORT A ON` re-enables
    once the load is removed.
  - With the OC event ignored, the hiccup's duty cycle is < 1 %, and the watchdog resets the MCU
    within 500 ms when the test build also stops feeding it.

### V-PORT-06 — Rp gating and port independence
- **Covers:** REQ-PORT-07, REQ-PORT-08
- **When:** Design review (G5) + Bring-up
- **Method:**
  - Sink tester on J2. Toggle port A, measure CC1/CC2, and repeat with the MCU held in reset.
  - With port B at 1 A, toggle port A 100 times while scoping VBUS_B.
- **Pass:**
  - CC < 0.2 V within 1 ms of OFF, and while the MCU is in reset.
  - Default level while ON, including while J2 VBUS is back-driven as in V-PORT-04.
  - VBUS_B deviates by ≤ 100 mV.

## Measurement

### V-MEAS-00 — Front-end assumptions, before layout
- **Covers:** REQ-MEAS-01, REQ-MEAS-02 (design assumptions behind them; OI-27, OI-28)
- **When:** Bench (one channel hand-built from the same parts)
- **Method:**
  - Build one mirror (OP07CDR on 0/12 V, AO3401A, R1 100 Ω, R_OUT 2.4 kΩ, pedestal 1 MΩ from
    8 V) on the 0.1 Ω shunt. Sweep 0 → 1.2 A at J4 = 4.75 V and 5.25 V, and measure the OP07
    output and gate voltage.
  - Apply a 0.1 → 1 A step and look for ringing.
  - Pulse R_M with 2.35 W for 10 ms, 100 times, and remeasure it.
- **Pass:**
  - The output is linear within 0.5 % to 1.2 A at both supplies, with the gate ≥ 0.15 V above
    the OP07's lowest output.
  - Overshoot < 10 % and no sustained oscillation (add the 1 kΩ gate resistor first).
  - R_M changes < 0.1 %.
  - Failing any of these reopens D17 before layout.

### V-MEAS-06 — ADC sampling and MCU interface, before layout
- **Covers:** REQ-MEAS-05, REQ-MEAS-08, REQ-SAFE-01 (design assumptions behind them; OI-31)
- **When:** Bench (a PGA2040 and one MCP3208 at V<sub>DD</sub> 5 V, V<sub>REF</sub> 3.3 V,
  wired as in circuit §3.2 and §6.4)
- **Method:**
  - Drive CH0 and CH1 each from 1.5 kΩ ∥ 330 pF through 1 kΩ, one at 0 V and one at 3.3 V
    (a current into the 1.5 kΩ, as the mirror does). Convert them alternately, first with the
    native 1.5 µs sample and then with the 4.5 µs stretched sample; compare with a single-
    channel reading of each.
  - Sweep CH0 from 0 to 3.3 V against the reference DMM in 64 steps.
  - Hold the RP2040 in reset (RUN low), then power it with blank flash; measure a GPIO that has
    a 10 kΩ pull-up to 3.3 V, as Q19/Q20's gates do.
  - Inspect the PGA2040: its supply input, the D+/D− series resistance from module pin to
    RP2040 pin, the flash part number, and the unique ID read by a test build.
- **Pass:**
  - Stretched: the alternating readings agree with the single-channel ones within 0.5 LSB.
    Native: they disagree by more than 5 LSB, which shows the test can fail.
  - INL within ±2 LSB at V<sub>REF</sub> = 3.3 V.
  - The pulled-up GPIO stays ≥ 2.5 V in reset and after power-up.
  - The module findings are recorded in `requirements/parts.md`; a missing 27 Ω pair or a
    flash without a unique ID is added to the design before layout.
  - Failing any of the first three reopens D23 before layout.

### V-MEAS-01 — Range, accuracy and sample rate against a reference
- **Covers:** REQ-MEAS-01, REQ-MEAS-05, REQ-MEAS-08
- **When:** Bring-up (all points) + Production (one point per range)
- **Method:**
  - Reference DMM in series with a stable load at 0.1 µA, 0.3 µA, 1 µA, 10 µA, 300 µA, 1 mA,
    15 mA, 100 mA and 1 A, after `ZERO`.
  - Run at the calibration temperature and at ±10 °C.
  - Average 1 s of board readings per point.
  - Measure the sample rate from frame sequence numbers over 60 s.
  - Measure the MLCC leakage contribution on LOW by repeating 0.1 µA with the port capacitor
    lifted.
- **Pass:**
  - Every point within ±(1 % + 3 LSB of its range); points just above a down-range threshold
    are judged against that floor.
  - 0.1 µA is distinguishable from 0.
  - Sample rate 14.0 kSPS ± 0.1 % (14 samples per 1 ms frame).
  - Record the leakage figure in `requirements/parts.md`.

### V-MEAS-02 — Hardware up-ranging and firmware hold
- **Covers:** REQ-MEAS-02, REQ-SAFE-02
- **When:** Design review (G11) + Bring-up
- **Method:**
  - Range LOW, 10 µA load. Step to 300 mA and to 1 A with the electronic load. Scope both
    bypass gates, the EVT pins, the HOLD pins and VBUS_A.
  - Repeat with the MCU held in reset after setting LOW through a test build: hold released,
    then RUN low.
- **Pass:**
  - Each stage's bypass gate is below −3.5 V V<sub>GS</sub> within 3 µs of its comparator
    threshold.
  - VBUS_A dips ≤ 0.25 V at 300 mA and ≤ 0.8 V at 1 A.
  - HOLD is asserted within 100 µs of the EVT edge.
  - With the MCU in reset, the ladder is already HIGH (hold pull-ups), so the step causes no
    LOW-range dip.

### V-MEAS-03 — Zero calibration
- **Covers:** REQ-MEAS-03
- **When:** Bring-up + Production
- **Method:**
  - Port ON, nothing attached, `ZERO A`. Read 10 s on LOW.
  - Change J4 from 4.8 V to 5.2 V and read again (pedestal correction).
  - Warm the board by 6 °C and check for the re-zero prompt.
  - Send `ZERO A` with the port OFF.
- **Pass:**
  - Post-zero reading |I| ≤ 0.32 µA (3 LSB) at both J4 voltages.
  - The re-zero prompt appears after a > 5 °C change.
  - `ZERO` with the port OFF returns `ERR 05`.

### V-MEAS-04 — Noise and LOW-range bandwidth
- **Covers:** REQ-MEAS-04, REQ-MEAS-07
- **When:** Bring-up
- **Method:**
  - Port ON, DUT side = 10 µF only. Record 10 s at 14.0 kSPS and compute the rms.
  - Step a resistive load from 50 µA to 100 µA on LOW, and measure the 10 – 90 % rise of the
    reading.
  - Repeat on MID with 5 mA → 10 mA.
- **Pass:**
  - ≤ 1 LSB rms (0.105 µA) on LOW.
  - LOW rise time 11.4 ms ± 30 % (2.2 τ, τ = 520 Ω × 10 µF); MID 0.22 ms ± 30 %. This
    confirms the limitation the manual must state.

### V-MEAS-05 — Sample flags and stream integrity
- **Covers:** REQ-MEAS-06, REQ-HOST-05
- **When:** Bring-up + every firmware release
- **Method:**
  - Record a stream while forcing range changes, a 1.5 A clip and an OC trip.
  - Parse it with the host tool.
  - Then feed the tool a copy with flipped bytes and a copy with 10 frames removed.
- **Pass:**
  - Every sample overlapping a range change carries *settling*.
  - Samples above 1.37 A carry *clipped*, and the trip carries *fault*.
  - Corrupted frames are rejected on CRC, and the removed frames are reported as a sequence
    gap.
- **Limits:** The parser sees only what the firmware sent. It cannot tell whether a flag
  *should* have been set; that comes from the scope capture of the gate signals taken at the
  same time.

## Host interface

### V-HOST-01 — Enumeration, identity, hub passthrough
- **Covers:** REQ-HOST-01, REQ-HOST-02, REQ-HOST-06, REQ-HOST-07
- **When:** Bring-up (three OSes) + Production (serial uniqueness)
- **Method:**
  - Plug into Windows 11, macOS and Linux, and inspect the device tree.
  - Replug 5 times into different ports.
  - Plug a High-Speed USB device (a USB 2.0 flash drive) into J2 and J3, and run a 1 GB
    read/verify on each.
  - Compare the MCU's USB VID/PID with the allocation record.
- **Pass:**
  - A CH335F hub plus one composite device with two CDC-ACM interfaces; no driver install on
    any OS.
  - Two units report different serials, and COM numbers stay stable across replugs.
  - The DUT enumerates at High-Speed and the transfer verifies with no errors. If it falls
    back to FS, record it against OI-26.
  - VID/PID matches an allocation we hold.

### V-HOST-02 — Control during streaming
- **Covers:** REQ-HOST-03
- **When:** Bring-up + every firmware release
- **Method:** Stream at 14.0 kSPS for 10 min while sending 1,000 `PORT A?` commands at random
  intervals.
- **Pass:** No sequence gaps; every command answered within 50 ms.

## Recovery and programming

### V-BOOT-01 — Recovery with the lid fitted
- **Covers:** REQ-BOOT-01, REQ-BOOT-02
- **When:** Bring-up
- **Method:**
  - Fully assembled unit: send `BOOT`.
  - Then load a firmware that never answers on USB, hold SW3 through the pinhole, and replug
    J1.
- **Pass:**
  - The RP2040 boot drive appears both times without opening the case, and new firmware
    copied to it as a UF2 file flashes and runs.
  - With the ROM bootloader there are no bootloader pages to protect; Rev0.3's
    write-protection check is not needed.

## Mechanical

### V-MECH-01 — Outline, connectors, fastening
- **Covers:** REQ-MECH-01, REQ-MECH-02, REQ-MECH-03, REQ-MECH-04, REQ-MECH-05
- **When:** Design review (mechanical overlay with real module outlines, OI-23) + Bring-up
  (real parts)
- **Method:**
  - Run `python -I design/experiments/oi-23-placement/placement_study.py` with the measured
    module outlines and the chosen header height entered (design review). It must exit 0.
  - Measure the Gerber outline and the fabricated board.
  - Insert the two widest cables on hand into J2 and J3 together, lid fitted.
  - Count mounting points and measure thread engagement or insert depth.
  - Insert and remove a cable 50 times per connector module.
- **Pass:**
  - 100.0 × 72.0 mm ± 0.2 mm, 4 layers per the fab drawing.
  - Both plugs seat fully together.
  - ≥ 3 mounting points, one near each connector end; ≥ 4 mm engagement or heat-set inserts.
  - After 50 cycles, no solder-joint cracking and no module movement.

## Manufacturing and test

### V-MFG-01 — Assembly side, fiducials, test access
- **Covers:** REQ-MFG-01, REQ-MFG-02, REQ-MFG-03, REQ-MFG-04
- **When:** Design review (Gerber / CPL) + JLCPCB DFM
- **Method:** Inspect the Gerber set and the CPL, the JLCPCB placement preview, and the
  hand-assembly list.
- **Pass:**
  - Bottom paste apertures 0, and every CPL entry on Top.
  - Every hand-soldered part is in the hand-assembly list and in none of the BOM or CPL.
  - 3 fiducials with 1 mm copper / 2 mm mask.
  - TC2030-NL footprint with its alignment holes.
  - Every REQ-MFG-04 test pad present and labelled.
  - G18 passes.

### V-MFG-02 — Sourcing rule at order time
- **Covers:** REQ-MFG-05
- **When:** Design review, immediately before upload and again before payment
- **Method:**
  - Run `python tools/jlc_stock.py` on every LCSC code in the BOM.
  - Open each hand-soldered part's Akizuki page and record its stock.
  - Compare each BOM line's class with the rule.
- **Pass:**
  - Every BOM line is Basic with ≥ 500 assembly stock; no Preferred Extended line (D22).
  - Every hand-soldered part shows stock ≥ the build quantity.
- **Limits:** `jlc_stock.py` sees the class and stock only, not suitability. It was shown
  failing (exit 1) on a non-existent code on 2026-11-03. Akizuki stock is read by hand,
  because there is no checked tool.

## Safety and fail-safe

### V-SAFE-01 — Fail-safe ladder and stuck range
- **Covers:** REQ-SAFE-01, REQ-SAFE-03
- **When:** Design review (G1, G12) + Bring-up
- **Method:**
  1. MCU unpowered, J4 present, port forced ON by a test jumper: 4-wire resistance from VSUP_A
     to VBUS_A.
  2. A fault-injection build that holds one bypass FET OFF while the range state reports
     HIGH, run with 0.5 mA and 300 mA loads.
  3. Repeat step 2 for the LOW-bypass FET in MID.
- **Pass:**
  - The ladder is ≈ 0.16 Ω (HIGH: R_H + FET_M), not 10 Ω or 520 Ω.
  - At 300 mA the port switches OFF within 10 ms with `FAULT:STUCKRANGE`, and R_M is within
    its tolerance afterwards.
  - At 0.5 mA, which is below the 1 mA detection floor, the port may stay ON and the
    dissipation stays below 1 mW.
