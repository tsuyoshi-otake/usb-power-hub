# USB Power-Control Hub — Product Requirements

**State: WIP — MANUFACTURING PROHIBITED.** Opened 2026-11-03.

This file is the authority for **what** the product must do (CLAUDE.md Section 2).
**How** it is done: `design/circuit/CIRCUIT_DESIGN_Rev0.2.md`. **How each requirement is
proven:** `requirements/verification.md` — every `REQ-` here has at least one `V-` there.

Status legend:

| Status | Meaning |
|---|---|
| **Settled** | Traced to a user decision (D-number) or a CLAUDE.md MUST. Change only with the user |
| **Proposed** | Written by Claude on 2026-11-03 to fill a gap. **Not approved.** Becomes Settled when the user accepts it |
| **Open** | Cannot be written until the named Open Issue (CLAUDE.md Section 11) is resolved |

IDs are stable. Never renumber; retire an ID by marking it `Withdrawn` with a reason.

---

## 1. Power input

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-PWR-01 | J1 is a USB-PD sink that requests 9 V and falls back to 5 V. | Settled | D1. See OI-17: a PC host port usually offers only 5 V |
| REQ-PWR-02 | Firmware can read the granted contract: voltage **and** maximum current. Without PD, it determines the Type-C current level (Default / 1.5 A / 3.0 A); if it cannot, it assumes Default (500 mA). | Proposed | Rev0.2 §7.2, P1 (CH224Q register 0x50) |
| REQ-PWR-03 | The downstream ports never advertise, in total, more current than the granted upstream power can deliver after board consumption and conversion loss. | Settled | CLAUDE.md §10.3 |
| REQ-PWR-04 | **Derating.** Before enabling a port, firmware checks the port's allotted current against the remaining budget, budget = (granted power × 0.9) − 1.02 W board rails, divided by 5.10 V. A port that does not fit is refused (REQ-PORT-02, `ERR 04`), never enabled into a brown-out. | Proposed | Rev0.2 §7.1 |
| REQ-PWR-05 | The mapping from granted power to each port's Rp level (Default / 1.5 A) and allotted current. | Open — OI-16 | Rev0.2 §7.2 |

## 2. Port power control

This section answers "can firmware stop power to a port?": yes, and this is the contract.

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-PORT-01 | **Default state OFF.** Each port is OFF at power-up, after any reset (power-on, brown-out, watchdog, `BOOT`), while the RP2040 is unprogrammed, and whenever firmware is not actively driving the enable. Implementation: EN_x has a resistor to GND, so an undriven GPIO means OFF. A firmware hang is turned into a reset by the RP2040 watchdog (timeout ≤ 500 ms, fed only from the main loop), so a hang also ends OFF. | Proposed | Gap in Rev0.1; P2 |
| REQ-PORT-02 | **ON / OFF / CYCLE commands** on the control port, per Section 4.1. Every command returns exactly one terminal line: `OK` or `ERR <nn> <TEXT>`. `OFF` always succeeds. `ON` and `CYCLE` leave the port OFF whenever they return `ERR`. | Proposed | CLAUDE.md §10.3 "independently switchable under firmware control" (Settled); command set is new |
| REQ-PORT-03 | **CYCLE discharge.** `PORT x CYCLE [ms]` switches OFF, waits until VBUS_x < **0.8 V** (vSafe0V), then holds OFF for `ms` (100 – 60000, default 1000), then switches ON. If VBUS_x has not fallen below 0.8 V within **1000 ms** of switching OFF, the port stays OFF and the command returns `ERR 06 DISCHARGE TIMEOUT`. The load switch's output discharge (150 Ω on the SY6280 candidate) does the discharging. | Proposed | P2, P7 |
| REQ-PORT-04 | **Back-feed.** While a port is OFF its load switch blocks reverse current from the DUT. If VBUS_x stays above 0.8 V for more than 100 ms while OFF, the port reports `OFF:BACKFEED`, and `ON` / `CYCLE` are refused with `ERR 07 BACKFEED` until VBUS_x falls below 0.8 V. Enabling into a back-feeding DUT would let current flow backwards through the switch. | Proposed | OI-7, P2 |
| REQ-PORT-05 | **Over-current and under-voltage.** The load switch limits current in hardware. In addition, firmware switches the port OFF and latches `FAULT:OVERCURRENT` if the measured port current exceeds its allotted current for more than 10 ms, and `FAULT:UNDERVOLTAGE` if VBUS_x is below 4.4 V for more than 10 ms while ON. Firmware never retries automatically. A fault is cleared only by `PORT x OFF` (acknowledge, port stays OFF) or `PORT x ON` (acknowledge and retry). | Proposed | P2, P7 |
| REQ-PORT-06 | **Single owner.** The RP2040 GPIO driving EN_x is the only thing that switches a port. The USB hub's port-power pins do not drive it, and no host-side hub request (e.g. a hub-class port-power command) changes it. | Proposed | P3; USB2514B asserts PRTPWR on its own (datasheet) |
| REQ-PORT-07 | Each port presents Rp on CC1 and CC2 only while that port is ON (gated by EN_x), so the DUT sees a detach when the port switches OFF. | Proposed change of a Settled requirement — CLAUDE.md §10.3 gates Rp by "port VBUS"; P3 changes that to EN_x because a back-feeding DUT keeps VBUS up | P3 |
| REQ-PORT-08 | The two ports switch independently; switching one never glitches the other's VBUS by more than 100 mV. | Settled (independence) / Proposed (100 mV figure) | CLAUDE.md §10.3 |

## 3. Measurement

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MEAS-01 | Each port's current is measured from 0.1 µA to 1 A. | Settled | D3 |
| REQ-MEAS-02 | Three hardware ranges (20 mΩ / 2 Ω / 200 Ω). Up-ranging on over-range is done by hardware without the MCU, within 2 µs. | Settled | D3, D4 |
| REQ-MEAS-03 | Zero-point calibration is a function, not an option: `ZERO x` with the port OFF; firmware asks for a re-zero when the RP2040 die temperature has moved more than 5 °C since the last zero. | Settled (mandatory zero) / Proposed (5 °C trigger) | D3, Rev0.1 §4 Condition 1 |
| REQ-MEAS-04 | **Resolution with its bandwidth.** 0.1 µA is resolved on the LOW range at output rates ≤ 1 kSPS (calculated noise 8.4 nA rms). At the raw 31.25 kSPS rate the LOW-range noise is ~47 nA rms; the documentation states this. | Proposed | Rev0.2 §4.1 |
| REQ-MEAS-05 | Accuracy over 15 – 35 °C. Proposed target: ±0.5 % of reading after per-unit, per-range gain calibration, plus the offset terms of Rev0.2 §7.4. | Open — OI-21 | Rev0.2 §12 item 5 |
| REQ-MEAS-06 | Every sample carries its range code and two flags: *in-transition* (the sample overlaps a range change) and *clipped* (over the top range, > ~1.2 A). | Proposed | Rev0.2 §3.3 |
| REQ-MEAS-07 | **Documented limitation:** with the 10 µF port capacitor, the LOW range's current bandwidth is ~80 Hz (MID ~8 kHz, HIGH ~800 kHz). Below 100 µA, sub-millisecond detail is not observable. The user documentation must say so. | Settled | Rev0.1 §4 Condition 2 |
| REQ-MEAS-08 | Sample rate 31.25 kSPS per channel, two channels simultaneous (D8's 32 kSPS target as realised by an 8.000 MHz ADC clock). | Settled (≈ 32 kSPS) / Proposed (exact rate) | D8, P6 |

## 4. Host interface

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-HOST-01 | The board enumerates as a USB hub with a composite CDC-ACM ×2 device behind it: control (`COMn`) and stream (`COMn+1`), driverless on Windows 10/11, macOS and Linux. | Settled | D7 |
| REQ-HOST-02 | Every unit reports a unique USB serial number derived from the RP2040 flash unique ID, so its COM numbers are stable across replugs. | Settled | CLAUDE.md §10.3, G8 |
| REQ-HOST-03 | The control port stays usable while the stream port is running. | Settled | Rev0.1 §3.3 |
| REQ-HOST-04 | The control port implements the protocol in Section 4.1. | Proposed | New |
| REQ-HOST-05 | The stream is binary and framed per Section 4.2. | Settled (binary, framed) / Proposed (frame layout) | Rev0.1 §3.3 |
| REQ-HOST-06 | The RP2040 function uses a VID/PID we are entitled to (a Raspberry Pi PID allocation or pid.codes), never a squatted one. Value not yet chosen. | Settled (rule) / Open (value) | CLAUDE.md §10.5 |
| REQ-HOST-07 | DUT data passes through a USB 2.0 High-Speed hub (USB2514B) on each downstream port. | Settled | D11 |

### 4.1 Control protocol v0 — Proposed

Line-based ASCII, so a plain terminal (TeraTerm, PuTTY, `screen`) is a complete client.

- A command is one line, ≤ 80 characters, terminated by CR, LF or CRLF; case-insensitive;
  tokens separated by spaces. No echo; enable local echo in the terminal if wanted.
- **Every command produces exactly one response line**: `OK`, `OK <data>`, or
  `ERR <nn> <TEXT>`. The control port sends nothing unsolicited; faults are seen with
  `PORT x?` / `STATUS?` and in the stream flags.
- Commands run one at a time, in order. `CYCLE` returns only after the port is ON again (or
  has failed and been left OFF), at most 1000 ms + hold time + 100 ms. The stream keeps running
  meanwhile.

| Command | Success response | Failure responses (port state after failure) |
|---|---|---|
| `*IDN?` | `OK USB-POWER-HUB,<pcb rev>,<serial>,<fw version>` | — |
| `STATUS?` | `OK CONTRACT=<9V\|5V\|NONE> IMAX=<mA> A=<state> B=<state> RESET=<POR\|BOD\|WDT\|BOOT>` | — |
| `PORT <A\|B> ON` | `OK` | `ERR 04 INSUFFICIENT POWER` (OFF) · `ERR 07 BACKFEED` (OFF) |
| `PORT <A\|B> OFF` | `OK` (always; clears a FAULT) | — |
| `PORT <A\|B> CYCLE [ms]` | `OK` once ON again | `ERR 02 BAD ARGUMENT` (unchanged) · `ERR 04` / `ERR 07` (OFF) · `ERR 06 DISCHARGE TIMEOUT` (OFF) |
| `PORT <A\|B>?` | `OK ON` · `OK OFF` · `OK OFF:BACKFEED` · `OK FAULT:OVERCURRENT` · `OK FAULT:UNDERVOLTAGE` | — |
| `ZERO <A\|B>` | `OK <offset in nA>` | `ERR 05 NOT ALLOWED: PORT ON` |
| `RANGE <A\|B> <AUTO\|HIGH\|MID\|LOW>` | `OK` — hardware up-ranging still overrides a forced low range (REQ-MEAS-02) | `ERR 02 BAD ARGUMENT` |
| `STREAM <ON\|OFF>` | `OK` | — |
| `BOOT` | `OK`, then reboot into the USB bootloader within 100 ms; ports OFF (REQ-PORT-01) | — |
| anything else | — | `ERR 01 UNKNOWN COMMAND` · `ERR 08 LINE TOO LONG` |

`<state>` is one of the `PORT x?` responses without `OK `.

### 4.2 Stream framing — Proposed

- Frame: sync `0xA5 0x5A`, version (u8), flags (u8), sequence number (u16, wraps), sample
  count n (u16), n sample records, CRC-16/CCITT over everything after the sync bytes.
- Sample record: channel A (i24), channel B (i24), one byte of per-channel range code
  (2 bits each), in-transition and clipped flags (REQ-MEAS-06) — 7 bytes. At 31.25 kSPS that is
  219 kB/s, about 18 % of Full-Speed bulk.
- A gap in sequence numbers is reported by the host tool as lost data, never silently bridged.

## 5. Recovery and programming

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-BOOT-01 | BOOTSEL recovery is reachable without disassembly. | Settled | CLAUDE.md §10.3 |
| REQ-BOOT-02 | Method: the `BOOT` command for normal updates, and SW1 behind a lid pinhole for a board whose firmware no longer answers. | Proposed | P10, OI-9 |

## 6. Mechanical

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MECH-01 | PCB 85 × 35 mm, 1.6 mm, 4 layers, ENIG. | Settled | D10, CLAUDE.md §10.3 |
| REQ-MECH-02 | Two USB-C plugs fit J2 and J3 at the same time, verified with real cables. Design input: J2–J3 centre pitch ≥ 18 mm. | Settled (requirement, OI-1) / Proposed (18 mm) | OI-1, P9 |
| REQ-MECH-03 | ≥ 3 mounting points, at least one near each connector end; insertion force is not carried by solder joints. | Settled | CLAUDE.md §7 |
| REQ-MECH-04 | Fasteners have ≥ 4 mm thread engagement or use heat-set inserts. | Settled (rule) / Proposed (heat-set M2 ×4, P12) | CLAUDE.md §7, OI-5 |
| REQ-MECH-05 | Case openings clear the mating plug's overmould, verified with a real cable. | Settled | CLAUDE.md §7 |

## 7. Manufacturing and test

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-MFG-01 | All mounted parts on Top; ENIG; JLCPCB PCBA. | Settled | CLAUDE.md §1, §10.3 |
| REQ-MFG-02 | ≥ 3 global fiducials, 1 mm copper / 2 mm mask opening. | Settled | CLAUDE.md §10.3 |
| REQ-MFG-03 | SWD reachable by a fixture with mechanical datums. Method: Tag-Connect TC2030-NL footprint. | Settled (need, OI-8) / Proposed (method, P11) | OI-8 |
| REQ-MFG-04 | Test pads on VBUS_IN, VPD, V5P1, V3P3, V3P3A, VBUS_A, VBUS_B and GND. | Proposed | P11 |

## 8. Safety and fail-safe

| ID | Requirement | Status | Source |
|---|---|---|---|
| REQ-SAFE-01 | The shunt-bypass FETs are ON whenever nothing drives them, so the ladder sits at the HIGH range. | Settled | D9 |
| REQ-SAFE-02 | Over-range forces the HIGH range in hardware, with no MCU in the path. | Settled | D4, G11 |
| REQ-SAFE-03 | A bypass FET that fails open is detected by firmware (VBUS_x > 300 mV below V5P1 while the range state is HIGH) and the port is switched OFF within 10 ms; the MID shunt survives that window (80 mJ). | Proposed | Rev0.2 §7.3 |

## 9. Documented limitations (for the user manual)

- LOW-range bandwidth ~80 Hz (REQ-MEAS-07).
- 0.1 µA resolution applies at ≤ 1 kSPS output rates (REQ-MEAS-04).
- Sample rate is capped by Full-Speed USB, not by the ADC (OI-14).
- On a 5 V-only upstream the port voltage is not regulated, and ports may be refused for lack
  of power (OI-17, REQ-PWR-04).
- The DUT sees ≈ 4.98 V at 1 A, not 5.10 V (Rev0.2 §3.1).
