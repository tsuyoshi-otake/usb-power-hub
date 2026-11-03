# USB Power-Control Hub

A 2-channel switched USB-C hub that measures each downstream port's current from
0.1 µA to 1 A, so a device under test can be power-profiled and power-cycled from
the host PC over a plain COM port.

> **Status: WIP — MANUFACTURING PROHIBITED.** The design exists only as documents.
> There is no schematic capture, no layout, no manufacturing output, no firmware,
> and nothing has been built or measured. Do not order anything from this
> repository.

## What it is meant to do

- **Two USB-C inputs:**
  - `HOST` (J1) carries data and logic power from the PC.
  - `PWR IN` (J4) is a power-only 5 V input that feeds the ports. Its USB-C current
    advertisement is read and enforced.
  - There is no USB-PD and no port regulator: the port voltage is J4's minus up to 0.32 V
    at 1 A.
- **Downstream:** two USB-C receptacles (`OUT A`, `OUT B`), each switched on and off
  independently by firmware. They are OFF at power-up and after any reset (REQ-PORT-01),
  and offer Default USB power (500 mA), with a hardware over-current trip at 1.16 A.
- **Measurement:** per port, a 3-range shunt ladder (510 Ω / 10 Ω / 0.1 Ω) with hardware
  up-ranging, discrete current-mirror amplifiers, and the MCU's 12-bit ADCs, at 18.5 kSPS
  per channel. Accuracy target: ±(1 % + 3 LSB of the range).
- **Control:** STM32F103 behind a CH335F hub, enumerating as a driverless CDC-ACM COM
  port. Commands such as `PORT A ON`, `PORT B CYCLE 2000` and `STREAM ON` are listed in
  `requirements/product.md` Section 4.1.
- **Board:** 85 × 35 mm, 4 layers, 1.6 mm FR-4, ENIG.
  - JLCPCB machine-places the small parts, all JLCPCB **Basic**.
  - You hand-solder the large parts, all bought from **Akizuki**: four USB-C modules,
    the hub module, the 12 V module and two shunts.
  - This is the sourcing rule D13. Two Preferred Extended parts await a decision (OI-30).

## Documents

Read in this order:

| File | What it holds |
|---|---|
| `CLAUDE.md` | Engineering policy, release discipline, and the open-issue list (Section 11). Every unstruck open issue blocks manufacturing. |
| `requirements/product.md` | What the product must do — the authority. REQ-* IDs, each marked Settled / Delegated / Proposed / Open / Withdrawn. Includes the control protocol. |
| `requirements/verification.md` | How each requirement is proven (V-* IDs: method, pass criterion, limits). |
| `design/circuit/CIRCUIT_DESIGN_Rev0.3.md` | The schematic as a document: topology, nets, designators, calculations, decisions (§10), and what was given up to meet the sourcing rule (§7.4). Rev0.1/Rev0.2 are in Git history. |
| `requirements/parts.md` | Candidate parts: JLCPCB Basic rows (LCSC number, assembly stock, class, date) and Akizuki rows (code, stock, price, date). Candidates only — none is confirmed. |
| `mockup/` | three.js appearance model of an earlier 60 × 24 mm, 6-layer concept. Reference only; superseded by the 85 × 35 mm decision (D10). |

Decisions are D-numbers in the circuit document's §10. Its "By" column says whether the
user made each one, whether it came from the Rev0.1 design, or whether Claude made it
under the user's 2026-11-03 delegation ("Claude (delegated)"). The user may revert a
delegated decision. Rev0.2's proposals (P-numbers) are resolved in §14.

## Re-checking part stock

Stock in `requirements/parts.md` is a dated snapshot. To re-query the JLCPCB
assembly-parts pool (Python 3, standard library only, no install step; checked with 3.13):

```sh
python tools/jlc_stock.py C8734 STM32F103C8T6
python tools/jlc_stock.py --all OP07      # list every hit, for finding candidates
```

The full command for every listed part is at the top of `requirements/parts.md`.
Exit status: 0 = every query matched exactly, 1 = some query did not, 2 = the API
failed. The tool's docstring lists what it cannot see — electrical suitability,
order-time stock, footprints, price, and lifecycle. Akizuki stock has no tool: read the
product page (codes in `requirements/parts.md`) at order time.

## Viewing the mockup

The mockup loads three.js from unpkg, so it needs a network connection and an
HTTP server (ES modules do not load from `file://`):

```sh
python -m http.server 8000 --directory mockup
# then open http://localhost:8000/usb-power-hub-board.html
```

## Building and programming

Not possible yet. Schematic capture (KiCad, decision D2) starts after the items in
the circuit document's §12 are done (first: the user's decision on OI-30, and the
OI-23 placement study). Firmware does not exist.

## Repository

- Git since 2026-11-03. Commit `4dd10fb` is the design exactly as it was paused
  on 2026-08-16; later commits are the 2026-11-03 revision.
- **No remote.** Do not create a public remote (`CLAUDE.md` Section 2).
- Commit messages are English and describe the change in detail.
