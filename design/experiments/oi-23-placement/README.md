# OI-23 placement study (Rev0.4) — non-authoritative

**Question.** Does the Rev0.4 part set fit on the board? This is OI-23. D10 fixed the board at
85 × 35 mm before Rev0.3/Rev0.4 moved the large parts onto Akizuki modules and DIP packages.

**Answer.**
- **No: 85 × 35 mm cannot hold Rev0.4, under any layout.**
- A block placement at **100 × 72 mm** passes every check below.
- D24 (2026-11-03) adopts 100 × 72 mm. The user's condition was 「100x100未満ならいいんだっけ」:
  stay inside JLCPCB's 100 × 100 mm price tier. The size inside it came from this study
  (CIRCUIT_DESIGN_Rev0.4.md §10).

This directory is a trial, not design data (CLAUDE.md §2: `design/experiments/` is
non-authoritative). The block positions are a proposal. Nothing here is a footprint, an
outline drawing or a layout.

## Files

| File | What it is |
|---|---|
| `placement_study.py` | The study. Standard library only: `python -I design/experiments/oi-23-placement/placement_study.py --svg layout_100x72.svg`. Exits 1 if a layout check fails. |
| `test_placement_study.py` | 15 tests. Thirteen corrupt one aspect of the layout and expect the checker to name the failure (CLAUDE.md §8); two check that the area bound's printed terms add up and that only low parts earn the under-module credit. |
| `layout_100x72.svg` | The block placement, drawn by the script. The front edge (OUT A / OUT B) is at the bottom. |

## Result 1 — 85 × 35 mm is impossible

The script adds up three things:
- every courtyard, both the hand-soldered parts and the SMD;
- the four mounting-hole keepouts;
- the routing space, as a factor K.

From that total it subtracts the most favourable under-module credit: every single SMD part
no taller than 1.5 mm may sit under a raised module, up to the space there is. The result is
a lower bound on the board area any layout would need.

| K (region area per courtyard area) | Needed | Against 85 × 35 (2,975 mm²) |
|---:|---:|---:|
| 1.0 (no routing space at all) | 3,780 mm² | 1.27 × |
| 1.4 | 4,429 mm² | 1.49 × |
| 1.6 (planning value) | 4,754 mm² | 1.60 × |
| 2.0 | 5,403 mm² | 1.82 × |

K = 1.0 is physically impossible to build, and it still needs 27 % more area than the board
has. That makes the K = 1.0 row a proof, not an estimate.

The inputs:
- **Hand-soldered: 2,639 mm².** Four USB-C modules at 20 × 15 mm (Akizuki drawing), the
  PGA2040 at 21 × 21 mm, the CH335F module at 38.5 × 10.2 mm, two DIP16 at 9.8 × 20.85 mm,
  the MAU104 at 20 × 6.6 mm, and the F1 input fuse at 13 × 5 mm (MF-R300, D25).
- **SMD courtyards: 1,649 mm².** This includes the four hand-soldered shunts (133 mm²). The
  count is 138 × 0402, 41 × SOT-23, 9 × SOIC-8, and the rest as listed in the script.
- **Space under modules: 704 mm²,** all of it credited: the parts no taller than 1.5 mm would
  fill 971 mm² even at K = 1.0. That is 130 mm² under each USB-C module, between its
  shell tabs and pins, and 184 mm² between the CH335F module's pin rows.

Rev0.4 §11 had estimated the SMD content at 1,100–1,200 mm² without counting it. The count
gives 1,516 mm² excluding the shunts.

## Result 2 — a block placement at 100 × 72 mm

![layout](layout_100x72.svg)

**Front edge:**
- OUT A (J2) and OUT B (J3) at a 28 mm pitch;
- a button and LEDs beside each port;
- SW3 (BOOT) and the TC2030 SWD land at the right.

**Behind the ports:**
- a 3 mm USB corridor, kept free of parts, carries D± from the CH335F to J2 and J3;
- the corridor runs in front of the analog front end, not through it.

**Analog band:**
- each port's front end (port switch, shunt ladder, amplifiers, comparators) in one
  27 × 31 mm region;
- the two MCP3208 ADCs beside them.

**Right column:**
- the CH335F, along the right edge;
- the MAU104, 6.4 mm from the nearest ADC.

**Back edge:**
- PWR IN (J4) at the left, with the input fuse F1 in front of it, and HOST (J1) at the right;
- the PGA2040 between them, with the LDO and the OC comparator next to it.

Under the modules: the port-side parts (discharge FET, port capacitor, CC ESD, Rp) sit under
J2 and J3, the input parts under J4 and J1, and Y2 and the hub decoupling under the CH335F.
Only parts no taller than 1.5 mm go there.

Checks that pass:
- every rectangle lies inside the board with ≥ 0.3 mm to the edge;
- no two rectangles are closer than 0.5 mm;
- every block is placed exactly once;
- J1 and J4 sit on the back edge, J2 and J3 on the front edge; the J2–J3 pitch is
  28 mm (≥ 20 mm);
- the MAU104 keeps ≥ 6 mm from the front ends and the ADCs;
- the USB corridor reaches the CH335F, J2 and J3, and crosses neither front-end region;
- every region holds its blocks at K = 1.6. The layout holds up to **K = 1.74**, set by the
  port B front-end region (92 % full at K = 1.6).

## What this study cannot see

- **Routing.** K is a planning assumption. Only capture and layout show that a region routes.
  The front-end regions are the tight ones.
- **Real footprints.** The courtyards are IPC-7351-nominal planning values. The passive
  counts come from the Rev0.4 circuit text and `requirements/parts.md`; capture will number
  them.
- **Measured outlines.** The CH335F module outline was measured off Akizuki's product photo
  against a ruler (OI-24). The PGA2040 pin map is unknown (OI-31), so no SMD is assumed under
  it.
- **Placement inside a region.** For example, it does not check that the shunt ladder keeps
  away from the USB corridor, or that the 12 V trace from the MAU104 reaches the front ends
  cleanly.
- **Mechanical, thermal and EMC behaviour.** It checks no heights except the under-module
  rule. The enclosure, the lid PCB and the mockup all follow the board size and must be redone
  if it changes.
- **Cost.** The script computes none. The JLCPCB instant quote was read by hand on
  2026-11-03 (4 layers, 5 pcs, default options): $8.00 at 85 × 35, 100 × 72 and
  100 × 100 mm, and $30.80 at 130 × 72 mm. ENIG adds $16.90 at 85 × 35 mm and $17.40 at
  100 × 72 mm. Prices change; recheck the live quote at every release (CLAUDE.md §9).
