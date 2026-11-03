# USB Power-Control Hub — Verification Plan

**State: WIP.** Opened 2026-11-03. Nothing below has been executed — no board exists.

Every requirement in `requirements/product.md` is covered by at least one entry here, and
every entry cites the requirements it proves. Design-review gates G1 – G15 live in
`design/circuit/CIRCUIT_DESIGN_Rev0.2.md` Section 8; entries here reference them rather than
restate them. CLAUDE.md Section 8 ("Functional" gate) requires these to pass before release.

**Stages:** *Design review* (against schematic/layout, before order) · *Bring-up* (first
article, bench) · *Production* (every unit, by fixture).

**Rule for automated checks** (CLAUDE.md Section 8): a script that grades a result must say
what it cannot see, and must be shown failing on a deliberately corrupted input before its
pass counts. Entries that rely on a script note this under *Limits*.

**Common equipment:** 4-channel oscilloscope (≥ 100 MHz) · 6½-digit DMM used as the reference
ammeter · programmable electronic load with ≤ 10 µs step · bench supply with current readout ·
USB-PD sources: 9 V/1.5 A, 9 V/3 A, 5 V/3 A Type-C current, and a plain 5 V/500 mA port ·
the intended host PCs · Type-C sink tester (Rd = 5.1 kΩ) · ≥ 3 different USB-C cables including
the widest overmould on hand.

---

## Power input

### V-PWR-01 — Contract negotiation and readback
- **Covers:** REQ-PWR-01, REQ-PWR-02
- **When:** Bring-up
- **Method:** Connect J1 to each PD source and to each intended host PC. Read `STATUS?`.
  Compare `CONTRACT` and `IMAX` with the source's advertised capability (PD analyser, or the
  source's label for fixed supplies).
- **Pass:** 9 V sources → `CONTRACT=9V`, `IMAX` within 50 mA of the source's PDO current.
  5 V-only sources → `CONTRACT=5V` and `IMAX` equal to the Type-C current level, or 500 when
  it cannot be determined. Record which host PCs grant 9 V — this is OI-17's evidence.

### V-PWR-02 — Power budget and advertisement
- **Covers:** REQ-PWR-03, REQ-PWR-04, REQ-PWR-05
- **When:** Design review (G6) + Bring-up
- **Method:** For each source, enable A, then B, at each allotted current the OI-16 rule
  permits. Measure CC voltage on J2/J3 with the sink tester to read the advertised level. Load
  each enabled port to its allotted current and watch VBUS_IN on the scope for 60 s.
- **Pass:** The sum of advertised currents never exceeds the REQ-PWR-04 budget. A port that
  does not fit returns `ERR 04` and stays OFF. VBUS_IN never sags below 4.5 V and the source
  never trips. (REQ-PWR-05 has no pass criterion until OI-16 is closed; record the
  observations meanwhile.)

## Port power control

### V-PORT-01 — Default OFF in every reset path
- **Covers:** REQ-PORT-01, REQ-PORT-06
- **When:** Design review (G13, G14) + Bring-up
- **Method:** Scope VBUS_A and VBUS_B, 10 µF + 10 mA load on each, through: first power-up
  with blank flash; power-up with firmware; brown-out (ramp VBUS_IN 5 V → 3 V → 5 V at
  1 V/ms); watchdog reset (test build that stops feeding it); `BOOT`. Separately, with ports
  ON, send a USB hub-class `ClearPortFeature(PORT_POWER)` from the host (e.g. `uhubctl`).
- **Pass:** In every reset path VBUS_x stays below 0.8 V, with no excursion above 0.8 V longer
  than 10 µs. The hub-class request leaves VBUS_x unchanged (single owner). G13 and G14 pass.

### V-PORT-02 — Command contract
- **Covers:** REQ-PORT-02, REQ-HOST-04
- **When:** Bring-up + every firmware release
- **Method:** A host script sends every command in product.md §4.1, including each failure
  case, plus 10,000 random lines (random tokens, lengths 0 – 120, mixed terminators). It counts
  response lines and checks port state with `PORT x?` after each.
- **Pass:** Exactly one response line per command line; each response matches the table;
  after every `ERR 04` / `ERR 06` / `ERR 07` from `ON`/`CYCLE` the port is OFF; after every
  `ERR 01` / `ERR 02` / `ERR 08` both ports are in the state they had before the command.
- **Limits:** The script sees only the control port. It cannot see VBUS — V-PORT-03 does. It
  must first be run against a firmware build with a deliberately duplicated response line and
  shown to fail.

### V-PORT-03 — CYCLE discharges before re-enabling
- **Covers:** REQ-PORT-03
- **When:** Bring-up
- **Method:** DUT side = 10 µF plus loads of 0, 10 mA and 1 A. Run `PORT A CYCLE 100` and
  `PORT A CYCLE 1000`; scope VBUS_A. Then hold VBUS_A up with a 5.0 V supply through 1 kΩ and
  run `PORT A CYCLE 100`.
- **Pass:** VBUS_A falls below 0.8 V before the hold time starts; the hold time is within
  ±10 ms of the request; `OK` arrives after VBUS_A is back above 4.75 V. In the held-up case,
  `ERR 06 DISCHARGE TIMEOUT` arrives 1000 ± 50 ms after the OFF edge and the port stays OFF.

### V-PORT-04 — Back-feed while OFF
- **Covers:** REQ-PORT-04
- **When:** Bring-up
- **Method:** Port A OFF. Apply 5.25 V from a bench supply to J2 VBUS and measure the current
  it delivers. Wait 200 ms, query `PORT A?`, then send `PORT A ON`.
- **Pass:** Reverse current ≤ 10 µA (the board is not powered from the DUT); `OK OFF:BACKFEED`
  within 200 ms; `ON` returns `ERR 07 BACKFEED` and VBUS_A stays at the applied voltage with no
  forward conduction.

### V-PORT-05 — Over-current and under-voltage faults
- **Covers:** REQ-PORT-05
- **When:** Bring-up
- **Method:** Step the electronic load from 0 to 120 % of the allotted current; then to a hard
  short; then hold V5P1 low enough to bring VBUS_A below 4.4 V. Observe for 10 s after each
  trip.
- **Pass:** The port switches OFF 10 – 20 ms after the condition starts; `PORT A?` reports the
  right fault; no automatic re-enable within 10 s; `PORT A OFF` clears to `OFF`; `PORT A ON`
  re-enables when the load is removed.

### V-PORT-06 — Rp gating and port independence
- **Covers:** REQ-PORT-07, REQ-PORT-08
- **When:** Design review (G5) + Bring-up
- **Method:** Sink tester on J2. Toggle port A; measure CC1/CC2. With port B at 1 A, toggle
  port A 100 times while scoping VBUS_B.
- **Pass:** CC < 0.2 V within 1 ms of OFF; Rp level present only while ON, including during
  the V-PORT-04 back-feed condition; VBUS_B deviates by ≤ 100 mV.

## Measurement

### V-MEAS-01 — Range, accuracy and sample rate against a reference
- **Covers:** REQ-MEAS-01, REQ-MEAS-05, REQ-MEAS-08
- **When:** Bring-up (all points) + Production (one point per range)
- **Method:** Reference DMM in series with a stable load at 0.1 µA, 1 µA, 10 µA, 90 µA, 1 mA,
  9 mA, 100 mA and 1 A, at 15, 25 and 35 °C ambient, after `ZERO`. Average 1 s of board
  readings per point. Measure the sample rate from frame sequence numbers over 60 s.
- **Pass:** Every point reads within the REQ-MEAS-05 limit once OI-21 sets it (until then,
  record the error table); 0.1 µA is distinguishable from 0 (REQ-MEAS-01); sample rate
  31.25 kSPS ± 0.1 %.

### V-MEAS-02 — Hardware up-ranging without the MCU
- **Covers:** REQ-MEAS-02, REQ-SAFE-02
- **When:** Design review (G11) + Bring-up
- **Method:** Range LOW, 10 µA load, step to 1 A with the electronic load. Scope the bypass
  FET gates and VBUS_A. Repeat with the RP2040 held in reset (RUN low).
- **Pass:** Both bypass FETs fully ON within 2 µs of the step; VBUS_A dips by ≤ 200 mV; same
  result with the RP2040 in reset.

### V-MEAS-03 — Zero calibration
- **Covers:** REQ-MEAS-03
- **When:** Bring-up + Production
- **Method:** Port OFF, `ZERO A`. Read 10 s on the LOW range. Warm the board by 6 °C (hot air
  at a distance, or a chamber) and check for the re-zero prompt. Send `ZERO A` with the port ON.
- **Pass:** Post-zero reading |I| ≤ 20 nA (offset drift + I<sub>IB</sub>, Rev0.2 §7.4); prompt
  shown after > 5 °C change; `ZERO` with port ON returns `ERR 05`.

### V-MEAS-04 — Noise and LOW-range bandwidth
- **Covers:** REQ-MEAS-04, REQ-MEAS-07
- **When:** Bring-up
- **Method:** Port ON, DUT side = 10 µF only. Record 10 s raw and averaged to 1 kSPS; compute
  rms. Then step a resistive load from 50 µA to 100 µA on the LOW range and measure the 10 – 90 %
  rise of the reading.
- **Pass:** ≤ 10 nA rms at 1 kSPS and ≤ 60 nA rms raw (calculation: 8.4 nA and 47 nA). LOW-range
  rise time 4.4 ms ± 30 % (2.2 τ, τ = 200 Ω × 10 µF) — confirming the limitation the manual
  must state.

### V-MEAS-05 — Sample flags and stream integrity
- **Covers:** REQ-MEAS-06, REQ-HOST-05
- **When:** Bring-up + every firmware release
- **Method:** Record a stream while forcing range changes and a 1.5 A clip. Parse it with the
  host tool. Then feed the tool a copy with flipped bytes and a copy with 10 frames removed.
- **Pass:** Every sample overlapping a range change carries *in-transition*; samples above
  ~1.2 A carry *clipped*; corrupted frames are rejected on CRC; the removed frames are reported
  as a sequence gap.
- **Limits:** The parser sees only what the firmware sent; it cannot tell whether a flag
  *should* have been set — that comes from the scope capture of the gate signals taken at the
  same time.

## Host interface

### V-HOST-01 — Enumeration, identity, hub passthrough
- **Covers:** REQ-HOST-01, REQ-HOST-02, REQ-HOST-06, REQ-HOST-07
- **When:** Bring-up (three OSes) + Production (serial uniqueness)
- **Method:** Plug into Windows 11, macOS and Linux. Inspect the device tree. Replug 5 times
  into different ports. Plug a High-Speed USB device into J2 and J3. Compare the RP2040
  function's VID/PID with the allocation record.
- **Pass:** USB2514B hub plus one composite device with two CDC-ACM interfaces; no driver
  install on any OS; two units report different serials; COM numbers stable across replugs;
  the DUT enumerates at High-Speed; VID/PID matches an allocation we hold.

### V-HOST-02 — Control during streaming
- **Covers:** REQ-HOST-03
- **When:** Bring-up + every firmware release
- **Method:** Stream at 31.25 kSPS for 10 min while sending 1,000 `PORT A?` commands at random
  intervals.
- **Pass:** No sequence gaps; every command answered within 50 ms.

## Recovery and programming

### V-BOOT-01 — BOOTSEL with the lid fitted
- **Covers:** REQ-BOOT-01, REQ-BOOT-02
- **When:** Bring-up
- **Method:** Fully assembled unit: send `BOOT`. Then erase the flash (so firmware is gone),
  press SW1 through the pinhole and replug.
- **Pass:** The RP2040 bootloader drive appears both times without opening the case.

## Mechanical

### V-MECH-01 — Outline, connectors, fastening
- **Covers:** REQ-MECH-01, REQ-MECH-02, REQ-MECH-03, REQ-MECH-04, REQ-MECH-05
- **When:** Design review (mechanical overlay) + Bring-up (real parts)
- **Method:** Measure the Gerber outline and the fabricated board. Insert the two widest
  cables on hand into J2 and J3 together, lid fitted. Count mounting points and measure thread
  engagement or insert depth. Insert and remove a cable 50 times.
- **Pass:** 85.0 × 35.0 mm ± 0.2 mm, 4 layers per the fab drawing; both plugs seat fully
  together; ≥ 3 mounting points, one near each connector end; ≥ 4 mm engagement or heat-set
  inserts; no solder-joint cracking or board movement after 50 cycles.

## Manufacturing and test

### V-MFG-01 — Assembly-side, fiducials, test access
- **Covers:** REQ-MFG-01, REQ-MFG-02, REQ-MFG-03, REQ-MFG-04
- **When:** Design review (Gerber / CPL) + JLCPCB DFM
- **Method:** Inspect the Gerber set and CPL; inspect the JLCPCB placement preview.
- **Pass:** Bottom paste apertures 0 and every CPL entry on Top; 3 fiducials with 1 mm copper /
  2 mm mask; TC2030-NL footprint with its alignment holes; every REQ-MFG-04 test pad present
  and labelled.

## Safety and fail-safe

### V-SAFE-01 — Fail-safe ladder
- **Covers:** REQ-SAFE-01, REQ-SAFE-03
- **When:** Design review (G1, G12) + Bring-up
- **Method:** Unpowered board: 4-wire resistance from V5P1 to the load-switch input of each
  channel. Then a fault-injection build that holds one bypass FET OFF while the range logic
  reports HIGH, run twice: with a 250 mA load (≈ 0.53 V drop, above the 300 mV threshold)
  and with a 100 mA load (≈ 0.21 V, below it — the documented undetected region).
- **Pass:** Unpowered ladder ≈ 38 mΩ (HIGH range: shunt + two FETs), not 2 Ω or 202 Ω;
  at 250 mA the port switches OFF within 10 ms and the MID shunt is undamaged (resistance
  unchanged within its tolerance); at 100 mA the port stays ON and the reported current
  agrees with a reference meter within the REQ-MEAS-05 target.
