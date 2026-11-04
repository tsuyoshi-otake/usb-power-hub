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
  - There is no USB-PD and no port regulator: the port voltage is J4's minus up to 0.40 V
    at 1 A (0.48 V when the other port also draws 1 A; the input fuse is shared).
- **Downstream:** two USB-C receptacles (`OUT A`, `OUT B`), each switched on and off
  independently by firmware. They are OFF at power-up and after any reset (REQ-PORT-01),
  and offer Default USB power (500 mA), with a hardware over-current trip at 1.16 A.
- **Measurement:** per port, a 3-range shunt ladder (510 Ω / 10 Ω / 0.1 Ω) with hardware
  up-ranging, discrete current-mirror amplifiers, and two 12-bit MCP3208 ADCs (one per
  port, sampled together), at 14.0 kSPS per channel. Accuracy target: ±(1 % + 3 LSB of the range).
- **Control:** an RP2040 with its own flash and crystal, machine-placed (D29), behind a CH335F hub, enumerating as a driverless CDC-ACM COM
  port. Commands such as `PORT A ON`, `PORT B CYCLE 2000` and `STREAM ON` are listed in
  `requirements/product.md` Section 4.1.
- **Board:** 100 × 72 mm, 4 layers, 1.6 mm FR-4, ENIG (D24). The earlier 85 × 35 mm
  cannot hold the Rev0.4 parts. JLCPCB's instant quote on 2026-11-03 (4 layers, 5 pcs,
  default options) was $8.00 at 85 × 35, 100 × 72 and 100 × 100 mm; ENIG adds $16.90 and
  $17.40 at the two sizes. Recheck the live quote before ordering. The stackup is
  JLC04161H-7628, named on the order, without impedance control for the prototype (D27).
  - JLCPCB machine-places the small parts and the RP2040, all JLCPCB **Basic** except the
    RP2040 itself (Extended, the one exception, D29).
  - You hand-solder the large parts, all bought from **Akizuki**: four USB-C modules,
    the hub module, two DIP16 ADCs, the 12 V module, two shunts per port and the input
    fuse.
  - This is the sourcing rule D13. D22 excludes Preferred Extended parts too, so the
    D+/D− lines of J1–J3 have no ESD protection (`requirements/product.md` §9).

## Documents

Read in this order:

| File | What it holds |
|---|---|
| `CLAUDE.md` | Engineering policy, release discipline, and the open-issue list (Section 11). Every unstruck open issue blocks manufacturing. |
| `requirements/product.md` | What the product must do — the authority. REQ-* IDs, each marked Settled / Delegated / Proposed / Open / Withdrawn. Includes the control protocol. |
| `requirements/verification.md` | How each requirement is proven (V-* IDs: method, pass criterion, limits). |
| `design/circuit/CIRCUIT_DESIGN_Rev0.4.md` | The schematic as a document: topology, nets, designators, calculations, decisions (§10), and what was given up to meet the sourcing rule (§7.4). Rev0.1–Rev0.3 are in Git history. |
| `requirements/parts.md` | Candidate parts: JLCPCB Basic rows (LCSC number, assembly stock, class, date) and Akizuki rows (code, stock, price, date). Candidates only — none is confirmed. |
| `design/experiments/oi-23-placement/` | The OI-23 placement study: why 85 × 35 mm cannot work, and the checked 100 × 72 mm block placement. A trial, not design data. |
| `design/experiments/stackup-impedance/` | The stackup study behind D27: JLCPCB's 4-layer stackups, the 90 Ω USB pair width on each, and a model checked against JLCPCB's single-ended calculator. A non-authoritative study, not design data. |
| `design/experiments/cost-estimate/` | Prototype cost estimate, dated 2026-11-03 and re-run 2026-11-04 for D29: 5 bare PCBs with 2 assembled by JLCPCB, plus the Akizuki parts. An estimate, not a quote. |
| `mockup/` | three.js appearance model of an earlier 60 × 24 mm, 6-layer concept. Reference only; superseded by the board-size decisions D10 and D24 (100 × 72 mm). |

Decisions are D-numbers in the circuit document's §10. Its "By" column says whether the
user made each one, whether it came from the Rev0.1 design, or whether Claude made it
under the user's 2026-11-03 delegation ("Claude (delegated)"). The user may revert a
delegated decision. Rev0.2's proposals (P-numbers) are resolved in §14.

## Re-checking part stock

Stock in `requirements/parts.md` is a dated snapshot. To re-query the JLCPCB
assembly-parts pool (Python 3, standard library only, no install step; checked with 3.13):

```sh
python tools/jlc_stock.py C7433 OP07CDR
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
the circuit document's §12 are done (first: measuring the CH335F module bought for the
board, OI-24, and re-running the OI-23 placement study with it; then drawing the RP2040's
land from its datasheet, G20). The front-end checks are made on the first assembled board, not on a
bench beforehand (decision D28). Firmware does not exist.

## Repository

- Git since 2026-11-03. Commit `4dd10fb` is the design exactly as it was paused
  on 2026-08-16; later commits are the 2026-11-03 revision.
- **Remote:** `origin` is the private GitHub repository `tsuyoshi-otake/usb-power-hub`
  (2026-11-03). Keep it private; do not create a public remote (`CLAUDE.md` Section 2).
- Commit messages are English and describe the change in detail.
