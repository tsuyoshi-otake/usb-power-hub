# USB Power-Control Hub — Product Requirements

**State: WIP — MANUFACTURING PROHIBITED.** Opened 2026-11-03. Revised for circuit Rev0.4
on 2026-11-03; amended 2026-11-04 for D29 (the bare RP2040), D30 (leaded HASL) and D31 (the bare CH335F).

This file is the authority for **what** the product must do (CLAUDE.md Section 2).
**How** it is done: `design/circuit/CIRCUIT_DESIGN_Rev0.4.md`. **How each requirement is
proven:** `requirements/verification.md` — every `REQ-` here has at least one `V-` there.

Status legend:

| Status | Meaning |
|---|---|
| **Settled** | Traced to a user decision (D-number) or a CLAUDE.md MUST. Change only with the user |
| **Delegated** | Decided by Claude under the user's 2026-11-03 delegation (circuit Rev0.4 §10, D14–D21 and D23; D23's MCU choice is superseded by D29 and D15's hub module by D31, both user decisions). Binding until the user reverts it; the user may revert any one |
| **Proposed** | Written by Claude to fill a gap and **not** covered by the delegation. Becomes Settled when the user accepts it |
| **Open** | Cannot be written until the named Open Issue (CLAUDE.md Section 11) is resolved |
| **Withdrawn** | Retired with a reason; the ID is not reused |

IDs are stable. Never renumber; retire an ID by marking it `Withdrawn` with a reason.

---

## 1. Power input

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-PWR-01 | Port power comes from **J4**, a power-only USB-C receptacle that presents Rd = 5.1 kΩ on CC1 and CC2. J4 MUST be a 5 V source. J1 (host) powers the logic only, and never the ports. *Rev0.2 text (PD sink on J1, D1) is superseded.* | Delegated | D14 (D1 superseded by D13) |
| REQ-PWR-02 | Firmware reads J4's Type-C current advertisement (Default / 1.5 A / 3.0 A) from the CC voltages. If neither CC shows Rp (legacy cable or no source), it reports `J4=NONE` when VBUS_IN is absent and `J4=DEFAULT` when VBUS_IN is present. | Delegated | D14 |
| REQ-PWR-03 | The downstream ports never advertise, in total, more current than the power input can deliver. | Settled | CLAUDE.md §10.3 |
| REQ-PWR-04 | **Advertisement rule.** Each port advertises Default USB power (500 mA). `PORT x ON` is accepted only if (ports already ON + 1) × 0.5 A ≤ J4's advertised current; otherwise it returns `ERR 04` and the port stays OFF. With J4 absent, every `ON` returns `ERR 04`. | Delegated | D18; implements REQ-PWR-03 |
| REQ-PWR-05 | **Budget rule.** If the two ports' measured currents together exceed J4's advertised current for > 50 ms, firmware switches OFF the port drawing more and latches `FAULT:BUDGET`. | Delegated | D18 (closes OI-16) |

## 2. Port power control

This section answers "can firmware stop power to a port?": yes, and this is the contract.

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-PORT-01 | **Default state OFF.** Each port is OFF at power-up, after any reset (power-on, brown-out, watchdog, `BOOT`), while the MCU is unprogrammed, unpowered or in its ROM bootloader, and whenever firmware is not actively driving EN_x. Implementation: EN_G_x has 100 kΩ to GND, so an undriven GPIO means OFF. A firmware hang is turned into a reset by the RP2040 watchdog (enabled by firmware as the first thing at boot, timeout ≤ 500 ms, fed only from the main loop; until it is enabled the ports are in their reset state, OFF), so a hang also ends OFF. | Delegated | D18, D23 |
| REQ-PORT-02 | **ON / OFF / CYCLE commands** on the control port, per Section 4.1. Every command returns exactly one terminal line: `OK` or `ERR <nn> <TEXT>`. `OFF` always succeeds. A command rejected for its form (`ERR 01`, `ERR 02`, `ERR 08`) is refused before any action and leaves both ports unchanged. `ON` and `CYCLE` that fail after validation (`ERR 04`) leave the port OFF. | Delegated | CLAUDE.md §10.3 "independently switchable under firmware control" (Settled); command set D21/§4.1 |
| REQ-PORT-03 | **CYCLE discharge, timed.** `PORT x CYCLE [ms]` switches the port OFF with its discharge FET ON (1 kΩ), holds OFF for `ms` (100 – 60000, default 1000), then switches ON under REQ-PWR-04. The 100 ms minimum is ≥ 5 τ for 20 µF of total port capacitance (board 10 µF + DUT ≤ 10 µF), so VBUS_x is below 0.8 V (vSafe0V) before ON. VBUS_x is not measured (circuit §3.1); this is verified by measurement (V-PORT-03), not checked at run time. *Rev0.2's `ERR 06 DISCHARGE TIMEOUT` is withdrawn.* | Delegated | D18 |
| REQ-PORT-04 | **Back-feed blocked, not detected.** While a port is OFF the back-to-back switch blocks current from a DUT that drives VBUS_x, which sees the 1 kΩ discharge load. Back-feed is not detected, because measuring VBUS_x would add a leakage that the LOW range measures. *Rev0.2's `OFF:BACKFEED` and `ERR 07` are withdrawn.* | Delegated (reduced function, circuit §7.4) | D18 |
| REQ-PORT-05 | **Faults.** Hardware opens the port within 10 µs when its current exceeds 1.16 A (±3 %); firmware then latches `FAULT:OVERCURRENT`. Firmware also latches `FAULT:UNDERVOLTAGE` and switches both ports OFF if V_J4 is below 4.4 V for more than 10 ms while a port is ON. It latches `FAULT:BUDGET` (REQ-PWR-05) and `FAULT:STUCKRANGE` (REQ-SAFE-03). Firmware never retries automatically. A fault is cleared only by `PORT x OFF` (acknowledge, port stays OFF) or `PORT x ON` (acknowledge and retry). | Delegated | D18 |
| REQ-PORT-06 | **Single owner.** The MCU GPIO driving EN_x is the only thing that switches a port. The CH335F's PWREN# pins are not connected, and no host-side hub request (e.g. a hub-class port-power command) changes the port. | Delegated | Rev0.2 P3, adopted in D18 |
| REQ-PORT-07 | Each port presents Rp = 33 kΩ to 3.3 V on CC1 and CC2, **sourced from the EN_x pin itself**, so Rp is present only while that port is commanded ON and disappears at reset. The DUT sees a detach when the port switches OFF. | Delegated change of a Settled requirement — CLAUDE.md §10.3 originally gated Rp by "port VBUS"; a back-feeding DUT would keep VBUS up | Rev0.2 P3, adopted in D18 |
| REQ-PORT-08 | The two ports switch independently. Switching one never glitches the other's VBUS by more than 100 mV (turn-on is soft-started ≥ 1 ms). | Settled (independence) / Delegated (100 mV figure) | CLAUDE.md §10.3 |

## 3. Measurement

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MEAS-01 | Each port's current is measured from 0.1 µA to 1 A. | Settled | User request 2026-08-16 |
| REQ-MEAS-02 | Three ranges, 510 Ω / 10 Ω / 0.1 Ω shunts in a nested bypass ladder. Up-ranging on over-range is done by hardware without the MCU, ≤ 3 µs per stage. Firmware holds the new range within 100 µs and does all down-ranging (below 0.8 × the lower range's threshold for 1 ms). | Delegated | D17 (supersedes D3; amends D4) |
| REQ-MEAS-03 | Zero-point calibration is a function, not an option: `ZERO x` with the port **ON and nothing attached** (the ladder is unpowered while OFF). Firmware asks for a re-zero when the RP2040's on-chip temperature sensor has moved more than 5 °C since the last zero. | Settled (mandatory zero) / Delegated (procedure, 5 °C trigger) | D3, D17 |
| REQ-MEAS-04 | **Resolution:** 0.1 µA = 1 LSB on the LOW range at the full 14.0 kSPS output rate. The calculated amplifier noise (≈ 2.5 nA rms) is far below 1 LSB, so no lower output rate is needed for it. | Delegated | Circuit §4, §4.1 |
| REQ-MEAS-05 | **Accuracy** ±(1 % of reading + 3 LSB of the active range) within ±10 °C of the calibration temperature, after per-unit gain calibration and zero-cal. Floors: LOW 0.32 µA, MID 16 µA, HIGH 1.0 mA. Just after a down-range the floor is up to 5.5 % (MID, 292 µA) or 6.8 % (HIGH, 14.9 mA) of the reading. | Delegated | D20 (closes OI-21) |
| REQ-MEAS-06 | Every sample carries its range code and three flags: *settling* (the sample overlaps a range change), *clipped* (over the top of HIGH, > 1.37 A), and *fault* (the port opened). | Delegated | Circuit §3.3 |
| REQ-MEAS-07 | **Documented limitation:** with the 10 µF port capacitor, the current bandwidth is ~31 Hz on LOW, ~1.6 kHz on MID and ~100 kHz on HIGH. Below 365 µA, sub-10 ms detail is not observable. The user documentation must say so. | Settled (limitation) / Delegated (values) | Rev0.1 §4 Condition 2; circuit §4 |
| REQ-MEAS-08 | Sample rate 14.0 kSPS per channel, both channels sampled simultaneously (one ADC per port on a shared clock and chip select). *Replaces D8's 32 kSPS and Rev0.3's 18.5 kSPS.* | Delegated | D17, D23 |

## 4. Host interface

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-HOST-01 | The board enumerates as a USB hub with a composite CDC-ACM ×2 device behind it: control (`COMn`) and stream (`COMn+1`), driverless on Windows 10/11, macOS and Linux. | Settled | D7 |
| REQ-HOST-02 | Every unit reports a unique USB serial number derived from the 64-bit unique ID of the QSPI flash U8 (W25Q128JVSIQ: factory-set, read by instruction 4Bh, D29; V-MEAS-06 reads it on the first boards and checks that two boards differ), so its COM numbers are stable across replugs. | Settled | CLAUDE.md §10.3, G8, D29 |
| REQ-HOST-03 | The control port stays usable while the stream port is running. | Settled | Rev0.1 §3.3 |
| REQ-HOST-04 | The control port implements the protocol in Section 4.1. | Delegated | D21 |
| REQ-HOST-05 | The stream is binary and framed per Section 4.2. | Settled (binary, framed) / Delegated (frame layout) | Rev0.1 §3.3 |
| REQ-HOST-06 | The MCU's USB function uses a VID/PID we are entitled to (pid.codes for open hardware, or a purchased VID), never a squatted one. Value not yet chosen. | Settled (rule) / Open (value) | CLAUDE.md §10.5 |
| REQ-HOST-07 | DUT data passes through a USB 2.0 High-Speed hub (CH335F, U6) on each downstream port. Each HS path still passes through one Akizuki USB-C module and its headers (J1, and J2 or J3; since D31 the hub itself is on the board). HS through them is unverified (OI-26); if HS fails at bring-up, FS operation is the documented fallback. | Delegated | D15, D31 (D11 superseded by D13) |
| REQ-HOST-08 | **Power declaration.** The MCU function's configuration descriptor declares bus-powered with bMaxPower 200 mA. The CH335F stays self-powered (PSELF default) and declares its default 100 mA. | Delegated | D26 |

### 4.1 Control protocol v0 — Delegated

Line-based ASCII, so a plain terminal (TeraTerm, PuTTY, `screen`) is a complete client.

- A command is one line, ≤ 80 characters, terminated by CR, LF or CRLF; case-insensitive;
  tokens separated by spaces. No echo; enable local echo in the terminal if wanted.
- **Every command produces exactly one response line**: `OK`, `OK <data>`, or
  `ERR <nn> <TEXT>`. The control port sends nothing unsolicited; faults are seen with
  `PORT x?` / `STATUS?` and in the stream flags.
- Commands run one at a time, in order. `CYCLE` returns only after the port is ON again (or
  has failed and been left OFF), at most hold time + 100 ms. The stream keeps running
  meanwhile.

| Command | Success response | Failure responses (port state after failure) |
|---|---|---|
| `*IDN?` | `OK USB-POWER-HUB,<pcb rev>,<serial>,<fw version>` | — |
| `STATUS?` | `OK J4=<NONE\|DEFAULT\|1.5A\|3.0A> VJ4=<mV> A=<state> B=<state> RESET=<POR\|BOD\|WDT\|BOOT>` | — |
| `PORT <A\|B> ON` | `OK` | `ERR 02 BAD ARGUMENT` (unchanged) · `ERR 04 INSUFFICIENT POWER` (OFF) |
| `PORT <A\|B> OFF` | `OK` (always; clears a FAULT) | — |
| `PORT <A\|B> CYCLE [ms]` | `OK` once ON again | `ERR 02 BAD ARGUMENT` (unchanged) · `ERR 04` (OFF) |
| `PORT <A\|B>?` | `OK ON` · `OK OFF` · `OK FAULT:OVERCURRENT` · `OK FAULT:UNDERVOLTAGE` · `OK FAULT:BUDGET` · `OK FAULT:STUCKRANGE` | — |
| `ZERO <A\|B>` | `OK <offset per range, nA>` | `ERR 05 NOT ALLOWED: PORT OFF` |
| `CAL? <A\|B>` | `OK <gain and offset per range>` — what the host tool needs to convert stream codes to amperes | `ERR 02 BAD ARGUMENT` |
| `RANGE <A\|B> <AUTO\|HIGH\|MID\|LOW>` | `OK` — a fixed range is a firmware hold; hardware up-ranging still overrides it on over-range (REQ-SAFE-02), and firmware returns to it after 1 ms below threshold | `ERR 02 BAD ARGUMENT` |
| `STREAM <ON\|OFF>` | `OK` | — |
| `BOOT` | `OK`, then reboot into the RP2040 ROM USB bootloader within 100 ms; ports OFF (REQ-PORT-01) | — |
| anything else | — | `ERR 01 UNKNOWN COMMAND` · `ERR 08 LINE TOO LONG` |

`<state>` is one of the `PORT x?` responses without `OK `. Error codes `ERR 06` and
`ERR 07` were Rev0.2's discharge-timeout and back-feed errors. They are **withdrawn** (REQ-PORT-03,
REQ-PORT-04) and are not reused.

### 4.2 Stream framing — Delegated

- Frame: sync `0xA5 0x5A`, version (u8), flags (u8), sequence number (u16, wraps), sample
  count n (u16), n sample records, CRC-16/CCITT over everything after the sync bytes.
- Timing: the ADCs deliver 1 ms frames of 14 samples, 69 µs apart, with a 103 µs gap across
  each frame's aux conversion (circuit §3.3). A stream frame carries whole 1 ms ADC frames
  (n is a multiple of 14), and its sequence number is the index of its first 1 ms ADC frame.
  The host therefore knows every sample's time exactly.
- Sample record, 5 bytes:
  - channel A (u16, one 12-bit conversion of the active range's amplifier);
  - channel B (u16, the same);
  - one byte holding each channel's range code (2 bits each) and the settling and clipped
    flags (REQ-MEAS-06).
- At 14.0 kSPS that is 70.0 kB/s, about 5.9 % of Full-Speed bulk.
- The host tool converts codes to amperes with the constants from `CAL?`. Fault events are
  carried in the frame `flags` byte.
- A sequence number other than the previous one + n / 14 is reported by the host tool as lost
  data, never silently bridged.

## 5. Recovery and programming

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-BOOT-01 | Firmware recovery is reachable without disassembly. | Settled | CLAUDE.md §10.3 |
| REQ-BOOT-02 | Method: the RP2040 ROM USB bootloader (a UF2 drive), which is in ROM and cannot be erased. It is entered by the `BOOT` command for normal updates, or by holding SW3 (behind a lid pinhole, wired to U1's QSPI_SS through 1 kΩ placed next to U8, Raspberry Pi's reference arrangement) while J1 is plugged in when the application no longer answers. No per-board programming over SWD is needed. | Delegated (method) / Settled (wiring, D29) | D21 as amended by D23 and D29 (Rev0.2 P10) |

## 6. Mechanical

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MECH-01 | PCB 100 × 72 mm, 1.6 mm, 4 layers, leaded HASL (D30; not RoHS), JLCPCB stackup JLC04161H-7628 named on the order. The outline stays within 100 × 100 mm (JLCPCB's base price tier as quoted on 2026-11-03, the user's condition in D24). A block placement is checked; the module header height is still OI-23 (OI-24 is closed by D31). | Settled (4 layers, ≤ 100 × 100 mm, finish) / Delegated (100 × 72 mm, stackup) | D10, D24, D27, D30, CLAUDE.md §10.3 |
| REQ-MECH-02 | Two USB-C plugs fit J2 and J3 at the same time, verified with real cables. Design input: J2–J3 centre pitch ≥ 18 mm. The J2/J3 modules are 20 mm wide, so side-by-side placement gives ≥ 20 mm. | Settled (requirement, OI-1) / Delegated (18 mm) | OI-1, D21 |
| REQ-MECH-03 | ≥ 3 mounting points, at least one near each connector end; insertion force is not carried by solder joints. The connector modules' mechanical pins are soldered, and the modules sit on the PCB, not on their header pins alone. | Settled | CLAUDE.md §7 |
| REQ-MECH-04 | Fasteners have ≥ 4 mm thread engagement or use heat-set inserts. | Settled (rule) / Delegated (heat-set M2 ×4) | CLAUDE.md §7, D21 |
| REQ-MECH-05 | Case openings clear the mating plug's overmould, verified with a real cable. | Settled | CLAUDE.md §7 |

## 7. Manufacturing and test

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MFG-01 | JLCPCB PCBA places SMD parts on Top only, the MCU U1, its flash U8 and crystal Y1 included (D29), and the hub U6 with its crystal Y2 (D31). The user hand-solders the Akizuki modules and large parts after delivery: through-hole pins are soldered from Bottom, and the two large SMD shunts on Top. No part body on Bottom; leaded HASL (D30). | Settled | D13, D29, D30, D31; changes CLAUDE.md §1 "Top-side assembly" |
| REQ-MFG-02 | ≥ 3 global fiducials, 1 mm copper / 2 mm mask opening. | Settled | CLAUDE.md §10.3 |
| REQ-MFG-03 | SWD reachable by a fixture with mechanical datums, for debug; programming does not need it (REQ-BOOT-02). Method: Tag-Connect TC2030-NL footprint. | Settled (need, OI-8) / Delegated (method) | OI-8, D21 |
| REQ-MFG-04 | Test pads on VBUS_IN, VSUP_A, VSUP_B, VBUS_A, VBUS_B, V5L, V5A, V12F, V_INJ, V3V3, VDDA and GND; since D29 also on U1's DVDD, RUN and one GPOUT clock pin (GPIO21, 23, 24 or 25), which V-MEAS-06 reads; since D31 also on U6's VDD33_HUB, which V-MFG-03 reads. | Delegated (D21) / Settled (the D29 and D31 pads) | D21, D29, D31 |
| REQ-MFG-05 | **Sourcing.** Every machine-placed part is JLCPCB **Basic** with ≥ 500 assembly-pool stock at order time, with **two exceptions: the RP2040, C2040 (Extended, D29), and the CH335F, C5137013 (Extended, D31)**, which need the same ≥ 500 stock. Every hand-soldered part is in stock at Akizuki at order time. No other Extended part of any kind, Preferred Extended included; a third one needs the user's decision. Special or hard-to-source parts SHOULD be avoided, and part types and count SHOULD be kept low. | Settled | D13, D22, D29, D31 |

## 8. Safety and fail-safe

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-SAFE-01 | The shunt-bypass FETs are ON whenever the MCU does not drive them (hold transistors pulled up), so the ladder sits at the HIGH range. | Settled | D9 |
| REQ-SAFE-02 | Over-range up-ranges in hardware with no MCU in the path; over-current opens the port in hardware. | Settled | D4, G11 |
| REQ-SAFE-03 | **Stuck range.** Firmware switches the port OFF within 10 ms and latches `FAULT:STUCKRANGE` when an amplifier whose shunt is commanded bypassed reads more than 10 % of the active range's current (and > 50 LSB), or sits at its own clip level, for 10 ms. Healthy parallel conduction through a bypassed shunt is ≤ 0.8 %. This covers a bypass FET that fails open and a hold that does not take. Detection floor: 1 mA. Below it a stuck range dissipates < 1 mW and is harmless. R_M must survive 2.35 W for that 10 ms window: the MFU is rated 6.25 W for 5 s (D28), and V-MEAS-00 checks its shift on the first board. | Delegated | Circuit §4 stuck-range table |
| REQ-SAFE-04 | **Input fuse.** J4's VBUS passes a resettable fuse ahead of the TVS. It holds the largest load the port OC trips allow (2 × 1.16 A) at 40 °C ambient, and it opens on a short of VBUS_IN or on a source above the TVS breakdown. | Delegated | D25 |

## 9. Documented limitations (for the user manual)

- **Two cables:** J1 to the PC for data and control, and J4 to a 5 V USB-C supply for port
  power. Without J4 the ports cannot turn on.
- **Not RoHS-compliant:** the PCB finish is leaded HASL (D30).
- **Port voltage is J4's voltage minus up to 0.40 V at 1 A** (0.20 V at 0.5 A, 0.48 V when
  the other port also draws 1 A; the input fuse F1 is shared). It is not regulated, and
  below 4.75 V it is outside USB 2.0's downstream-port range (circuit §3.1).
- **Each port offers Default USB power (500 mA).** With a Default-only J4 supply, one port
  at a time (REQ-PWR-04).
- **Bandwidth:** ~31 Hz on LOW, ~1.6 kHz on MID, ~100 kHz on HIGH (REQ-MEAS-07).
- **Accuracy near the bottom of MID and HIGH** is 5–7 % of the reading (REQ-MEAS-05).
- **A step from deep sleep to 1 A** dips the port by ~0.6 V for ~6 µs while the ranges
  switch (circuit §4).
- **Back-feed** is blocked but not reported (REQ-PORT-04).
- **The sample rate (14.0 kSPS) is set by the ADC conversion time** (OI-14). On HIGH, current
  detail above 7 kHz aliases into the samples; the average current is preserved (circuit §3.3).
- **No ESD protection on D+/D− of J1, J2 and J3** (D22). Only the hub chip's own protection
  remains: all three pairs run to U6, whose USB pins are rated 6 kV HBM (CH334/335 datasheet
  §4.1). Discharge yourself and the cable before plugging in, as with a bare development
  board.
- **Plug J1 into a port that supplies 500 mA** (a PC port or a self-powered hub), not into a
  bus-powered hub. J1 draws ≈ 0.21 A typical, ≈ 0.26 A with every OP07 at its maximum. The
  hub declares 100 mA and the control function 200 mA, but USB charges the upstream port
  only the hub's 100 mA (D26).
