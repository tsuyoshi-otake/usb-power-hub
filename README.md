# USB Power-Control Hub

A 2-channel switched USB-C hub that measures each downstream port's current from
0.1 µA to 1 A, so a device under test can be power-profiled and power-cycled from
the host PC over a plain COM port.

> **Status: WIP — MANUFACTURING PROHIBITED.** The design exists only as documents.
> There is no schematic capture, no layout, no manufacturing output, no firmware,
> and nothing has been built or measured. Do not order anything from this
> repository.

## What it is meant to do

- **Upstream:** one USB-C receptacle to the host. USB-PD sink requesting 9 V
  (5 V fallback), bucked to a regulated 5.10 V port rail.
- **Downstream:** two USB-C receptacles (`OUT A`, `OUT B`), each switched on and
  off independently by firmware; OFF at power-up and after any reset
  (proposed, REQ-PORT-01).
- **Measurement:** per port, a 3-range shunt ladder (20 mΩ / 2 Ω / 200 Ω) with
  hardware auto-ranging and a 24-bit ADC, ≈ 32 kSPS per channel (31.25 kSPS
  with the proposed 8 MHz ADC clock).
- **Control:** RP2040 behind a USB2514B hub, enumerating as a driverless CDC-ACM
  COM port. Commands such as `PORT A ON`, `PORT B CYCLE 2000`, `STREAM ON` — see
  `requirements/product.md` Section 4.1.
- **Board:** 85 × 35 mm, 4 layers, 1.6 mm FR-4, Top-side assembly, ENIG; LCSC
  parts and JLCPCB PCBA.

## Documents

Read in this order:

| File | What it holds |
|---|---|
| `CLAUDE.md` | Engineering policy, release discipline, and the open-issue list (Section 11). Every unstruck open issue blocks manufacturing. |
| `requirements/product.md` | What the product must do — the authority. REQ-* IDs, each marked Settled / Proposed / Open. Includes the control protocol. |
| `requirements/verification.md` | How each requirement is proven (V-* IDs: method, pass criterion, limits). |
| `design/circuit/CIRCUIT_DESIGN_Rev0.2.md` | The schematic as a document: topology, nets, designators, calculations, closed decisions (§10), and proposals awaiting a decision (§14). |
| `requirements/parts.md` | Candidate parts with LCSC number, JLCPCB assembly stock, class, and the date checked. Candidates only — none is confirmed. |
| `mockup/` | three.js appearance model of an earlier 60 × 24 mm, 6-layer concept. Reference only; superseded by the 85 × 35 mm decision (D10). |

Closed decisions are D-numbers in the circuit document's §10; its "By" column
says whether the user made each one or it came from the Rev0.1 design. A
proposal (P-number, §14) is not a decision until the user accepts it and it is
moved into §10.

## Re-checking part stock

Stock in `requirements/parts.md` is a dated snapshot. To re-query the JLCPCB
assembly-parts pool (Python 3, standard library only, no install step; checked with 3.13):

```sh
python tools/jlc_stock.py C58940 USB2514BI-AEZG-TR
python tools/jlc_stock.py --all INA190      # list every hit, for finding candidates
```

The full command for every listed part is at the top of `requirements/parts.md`.
Exit status: 0 = every query matched exactly, 1 = some query did not, 2 = the API
failed. The tool's docstring lists what it cannot see — electrical suitability,
order-time stock, footprints, price, and lifecycle.

## Viewing the mockup

The mockup loads three.js from unpkg, so it needs a network connection and an
HTTP server (ES modules do not load from `file://`):

```sh
python -m http.server 8000 --directory mockup
# then open http://localhost:8000/usb-power-hub-board.html
```

## Building and programming

Not possible yet. Schematic capture (KiCad, decision D2) starts after the open
issues in `CLAUDE.md` Section 10.5 are decided. Firmware does not exist.

## Repository

- Git since 2026-11-03. Commit `4dd10fb` is the design exactly as it was paused
  on 2026-08-16; later commits are the 2026-11-03 revision.
- **No remote.** Do not create a public remote (`CLAUDE.md` Section 2).
- Commit messages are English and describe the change in detail.
