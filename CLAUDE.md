# USB Power-Control Hub — Hardware Engineering Guide

Ported from [`../easy-stick/CLAUDE.md`](../easy-stick/CLAUDE.md), reduced to what
this board actually needs. That file stays the fuller reference. Its verified
incident record now lives in
[`../easy-stick/docs/engineering-lessons/README.md`](../easy-stick/docs/engineering-lessons/README.md)
(lessons 14.1–14.26; "easy-stick 14.n" below cites one of them). Read the relevant
lesson before reusing a footprint, before trusting an automated check, and before
recording a change as cost-neutral. Those incidents happened on a sibling board
with the same vendor chain and apply here.

Written in English so that CAD data, manufacturing files, Git history, and
supplier communication use one unambiguous vocabulary.

Requirement words: **MUST** = mandatory for release. **SHOULD** = expected
unless a documented tradeoff proves otherwise. **MAY** = optional.

---

## 0. Current State

> **WIP — MANUFACTURING PROHIBITED.**
>
> The circuit design exists as a document —
> `design/circuit/CIRCUIT_DESIGN_Rev0.4.md` (redesigned 2026-11-03 under the user's
> sourcing rule D13, then limited to Basic parts only by D22; Rev0.1–Rev0.3 are in
> Git history) — together with the
> requirements set in `requirements/`
> (`product.md`, `verification.md`, `parts.md`). That is currently the whole of
> the design. There is **no netlist, no schematic capture, no layout, no
> manufacturing output**. Candidate parts have been looked up in the JLCPCB
> assembly pool and at Akizuki (`requirements/parts.md`, dated stock), but **none
> is confirmed**:
> no footprint is verified and no order-time stock check has been done. Nothing
> has been built or measured.
>
> The other thing that exists is a three.js appearance mockup
> (`mockup/`). Component names such as `U2_usb_hub` in it are placeholders, not
> procurement specifications, and D10/D24 (100 × 72 mm, 4 layers) supersede its
> outline and layer count. Section 11 lists the blocking issues.
>
> The repository is under Git since 2026-11-03 (commit `4dd10fb` is the design
> as it was paused on 2026-08-16). There is no remote.

The mockup is a **mechanical and layout intent reference only**. Per easy-stick
14.15/14.19: an artifact kept as a reference is evidence for the thing it is
kept for and for nothing else. Its coordinates are a placement proposal; its
stackup, pad shapes, and part sizes are **not** design data.

---

## 1. Scope and Priorities

Product architecture:

- FR-4 PCB, 1.6 mm, **100 × 72 mm, 4 layers** (D10 as amended by D24, 2026-11-03).
  The user set the 4 layers (D10) and the limit that the outline stays within 100 × 100 mm,
  JLCPCB's base price tier (D24; the quote figures and their date are in that row). The
  OI-23 placement study set the size, because 85 × 35 mm
  cannot hold the Rev0.4 parts. Closes OI-13 and OI-10.
- Assembly (D13, REQ-MFG-01):
  - JLCPCB machine-places the SMD parts, on Top only.
  - The user hand-solders the large Akizuki parts (modules, two shunts); through-hole
    pins are soldered from Bottom.
  - No part body on Bottom; Bottom is copper, vias and mask.
- USB-C receptacles ×4, all Akizuki modules: host data and logic power (J1), a
  power-only 5 V input (J4), and 2 switched downstream ports (J2, J3).
- No USB-PD. Port power is J4's own 5 V, unregulated (D14).
- Precision current measurement, **0.1 µA – 1 A**: 3-range shunt ladder with
  hardware up-ranging, discrete current-mirror amplifiers, and two 12-bit
  MCP3208 ADCs (one per channel), two independent channels sampled together.
- Enumerates as a **CDC-ACM COM port** on the upstream PC; driverless control.
- Sourcing rule D13: JLCPCB **Basic** parts for PCBA, **Akizuki** parts for
  hand soldering, never an Extended-only PCBA; JLCPCB PCB/PCBA services.
  D22 (user) excludes Preferred Extended parts too.
- Enclosure: 3D-printed tub + a second PCB used as the top panel.
- Git holds design sources, manufacturing releases, decisions, and QA evidence.

When rules conflict, use this priority:

1. Electrical and user safety.
2. Functional and mechanical requirements.
3. **Measurement accuracy** (this board is an instrument — see Section 5.4).
4. Signal integrity, power integrity, ESD robustness, durability.
5. Manufacturability, inspectability, testability.
6. Supply continuity and assembly yield.
7. Cost.
8. Visual refinement.

Low price never justifies an unverified footprint, marginal spacing, unknown
polarity, incomplete routing, or missing test coverage.

---

## 2. Repository Layout and Release Discipline

This repo follows the per-project subtree used by `easy-stick`, with its
`projects/<slug>/` level removed — this is a single-product repo, not a
monorepo. Nothing lives above the product; the repo root *is* the product.

**Create a directory only when real work needs it.** The tree below is the
target shape, not a scaffold to pre-create. An empty directory committed for
appearance is a defect, not organization.

```text
usb-power-hub/
├─ CLAUDE.md                    # this file — policy + product requirements + open issues
├─ README.md                    # what the product is, how to build and program it
├─ tools/                       # repo scripts (jlc_stock.py — JLCPCB assembly-pool lookup)
├─ requirements/
│  ├─ product.md                # what the product must do (authority)
│  ├─ parts.md                  # per-part selection and sourcing record
│  └─ verification.md           # how each requirement is proven
├─ design/
│  ├─ circuit/                  # CIRCUIT_DESIGN_Rev<X.Y>.md — the schematic, as a document,
│  │                            #   and its _calc.py, which reproduces the document's numbers
│  ├─ ecad/                     # captured schematic + PCB
│  │  ├─ source/                #   exported source snapshots
│  │  ├─ libraries/             #   project-only symbols and footprints
│  │  ├─ previews/              #   2D/3D and vendor placement previews
│  │  └─ reports/               #   ERC, DRC, unrouted-net output
│  ├─ mechanical/
│  │  ├─ reference/             #   authoritative outline and connector geometry
│  │  ├─ assembly/              #   enclosure CAD, lid PCB, fit studies
│  │  └─ reports/
│  └─ experiments/              # non-authoritative trials
├─ firmware/                    # RP2040 (PGA2040) — src/ include/ tests/ tools/ reports/
├─ manufacturing/
│  ├─ working/                  # disposable candidate exports — never orderable
│  └─ releases/<rev>/<rNN>/     # immutable approved or ordered releases
├─ tests/                       # fixtures/ reports/ — physical test evidence
├─ docs/
│  └─ decisions/                # one file per closed architectural decision (until
│                               #   created, decisions D1–D21 live in circuit §10)
└─ mockup/                      # the three.js appearance model — reference only
```

Two deliberate differences from `easy-stick`:

- `design/ecad/` replaces its `design/easyeda/`. The directory was named before
  the tool was chosen; KiCad was then chosen (D2, Section 10.4). The name stays
  tool-neutral so a later tool change does not rename the tree.
- Its `projects/<slug>/mechanical/` sibling of `design/mechanical/` is drift,
  not intent. Mechanical data lives under `design/mechanical/` only.

**`design/circuit/` is where the schematic starts.** The circuit is designed as
a reviewable document — topology, nets, designators, calculated values, closed
and open decisions — *before* it is captured in an ECAD tool. Capture
transcribes a design that is already settled; it is not where the design
happens.

An approved release MUST contain exactly one coordinated set of: ECAD source
export, schematic PDF, Gerber ZIP, drill files, BOM, CPL, assembly drawing,
fabrication/stackup drawing, 2D/3D previews, ERC + DRC + unrouted-net results,
test evidence, `RELEASE_MANIFEST.md`, and `SHA256SUMS.txt`.

The manifest MUST record: PCB revision and release number; state (`WIP` /
`REVIEWED` / `ORDERED` / `REJECTED`); ECAD document identity; Git commit and
time; dimensions, layer count, thickness, copper weight, mask, silkscreen,
finish, **impedance-control option and stackup ID**; assembly side, quantities,
DNP list; exact relative paths of source/Gerber/BOM/CPL; ERC/DRC/DFM results;
firmware commit or binary checksum; JLCPCB order number when ordered; residual
risks, approver, approval time.

**Never overwrite an ordered release.** New release number for regenerated
output; new PCB revision for any electrical, layout, footprint, or mechanical
change. Never rewrite or delete ordered-release history.

Naming and Git:

- lowercase kebab-case directories; ISO dates `YYYY-MM-DD`.
- Manufacturing files: `<Product>_<Board>_<Revision>_<Artifact>`.
- Keep PCB revision (`Rev1.0`) separate from release iteration (`r01`).
- No `final`, `new`, `latest`, `fix` in release file names. No spaces, no
  non-ASCII, no parentheses.
- Commit messages in English, describing the change in detail and referencing
  the tracking Issue number.
- **Do not create a public remote repository.**

---

## 3. Design States and Change Control

Every PCB revision MUST carry one explicit state. No implicit state is allowed.

| State | Meaning |
|---|---|
| `WIP` | Incomplete. Not orderable. |
| `REVIEW` | Electrically and mechanically complete, under verification. |
| `RELEASE CANDIDATE` | Frozen while manufacturing output is reviewed. |
| `MANUFACTURING APPROVED` | Approved source of order files. |
| `OBSOLETE` | Retained for history. Not orderable. |

A design with unresolved ERC, DRC, unrouted nets, unknown footprint
orientation, or an unverified mechanical outline **remains `WIP`**.

For every material change: state why it is required → identify affected
requirements, nets, footprints, manufacturing files, and tests → update the
schematic before or with the PCB → re-run ERC and DRC → re-export source →
regenerate **all** output from the same revision → record the result in Git.

Never hand-edit a BOM or CPL without recording the transformation and proving it
still matches the source revision.

**Follow a change's consequences past the commit that made it** (easy-stick
14.4). A change can be cost-neutral *and* create the condition that spends the
cost later. When recording a change as neutral, enumerate what else moved with
it, not only what was added and removed.

---

## 4. Parts and Footprints

### 4.1 Selection

A generic value such as `10 uF`, `USB hub`, or `QFN-36` is **not** a
procurement specification. Before final placement, record for every mounted
part: manufacturer, MPN, LCSC number, package and dimensions, electrical rating
and tolerance, temperature range, **temperature coefficient where it affects
measurement**, polarity/Pin 1 convention, JLCPCB Basic/Extended class, current
stock, lifecycle, and approved alternates.

Selection order: electrical/safety suitability → package and footprint
certainty → lifecycle and stock stability → assembly yield → Basic-part
availability → price.

Prefer Basic parts when all technical requirements are met, but never change
value, voltage rating, dielectric, tolerance, TCR, ESD capacitance, polarity, or
package only to avoid an Extended setup fee.

Use the **JLCPCB assembly-parts inventory** shown for the actual PCBA order as
the authoritative stock signal — LCSC retail stock is a different pool and is
not a substitute (easy-stick 14.8). For commodity passives require ≥500 units of
visible JLCPCB assembly stock, prefer >1,000. Recheck immediately before upload
and again before payment.

### 4.2 Footprints

For every symbol and footprint: record MPN, LCSC number, package, source URL or
datasheet revision, and reviewer. Check pin numbers against the **package
drawing**, not the symbol image. Check pad size, pitch, gap, span, courtyard,
mask expansion, and paste apertures against the manufacturer's recommended land.

- **A part number is not a footprint** (easy-stick 14.1). A library footprint
  carrying the correct LCSC number can still have the wrong land pattern.
  Verify before reuse, including footprints already present in this repo.
- **Anchor Pin 1 to a physical feature of the part** (easy-stick 14.3). Where
  the part carries a moulded polarity marker, number that terminal pin 1 — then
  the component's own marker *is* the footprint's pin-1 indicator and the two
  cannot drift apart.
- **A CPL angle and a JLCPCB component-model angle are different frames**
  (easy-stick 14.18). A numerically correct CPL angle does not mean the physical
  orientation is correct. Verify in the JLCPCB placement preview.
- Never use the 3D model as electrical evidence.

Orientation is a manufacturing property, not a cosmetic preference. Align
polarized parts to one or two common directions where routing permits; keep
Pin 1 markers visible after assembly; give every LED and diode an unambiguous
cathode mark; mark connector Pin 1.

---

## 5. Stackup, Placement, and Routing

### 5.1 Stackup

The stackup MUST be a **real JLCPCB stackup selected by name**, not a
hand-invented layer table. The mockup's dielectric thicknesses are fictional and
MUST NOT be used.

- Choose the JLCPCB stackup ID at design start and record it in the manifest.
  **Chosen: JLC04161H-7628** (D27, 2026-11-03), named on the order. It was the only
  named 4-layer stackup on the quote page without JLCPCB's special-stackup note,
  which excludes Economic PCBA. Study: `design/experiments/stackup-impedance/`.
- Compute USB 2.0 differential geometry **against that stackup**, using
  JLCPCB's impedance calculator, before routing. Its differential calculation
  returned no result on 2026-11-03, so D27's W 0.31 / S 0.15 mm is a model
  value and stays provisional until that rerun.
- Order with the impedance-control option if HS eye margin depends on it. D27
  does not order it for the prototype: the D± path also runs through modules
  and headers that it cannot control (OI-26), and FS is the fallback.

Layer assignment (4 layers, D10): L1 signal + parts / L2 solid GND / L3 power
pours + low-speed signals / L4 GND + low-speed. **L2 MUST remain unbroken under
every USB pair**, and every L1 USB pair references L2 only. L3 signals that cross
under the analog block or a USB pair need a GND reference on L4 directly below.
Confirm against the chosen JLCPCB 4-layer stackup before routing (Section 5.1).

### 5.2 Placement

Place parts to minimize crossings before drawing traces.

- Protection goes at the connector, not near the MCU.
- Decouplers go at the supply pins, not wherever space remains.
- Keep USB parts close to their receptacle.
- **Keep the analog front end (shunts, range FETs, amps, ADC, Vref) in one
  contiguous block, away from the MAU104 DC-DC module, the hub, and LED switching.**
- Keep the MAU104's input and output loops (≈ 100 kHz switching) small and away from
  the ADC.
- Leave optical inspection access to Pin 1 and polarity marks.
- Every mounted body and paste aperture on Top.

Review placement with unrouted ratsnest lines before routing. If several nets
cross in one area, move or rotate parts rather than accepting extra vias.

### 5.3 Routing

Route in this order: USB differential pairs → connector ESD return paths →
VBUS power path and shunt ladder → **analog sense and Vref** → MCU decoupling →
ground-critical paths → SWD → LEDs and low-speed signals → ground zones and
stitching.

Conservative starting rules — these are starting values, not a replacement for
current, impedance, creepage, or thermal calculation:

| Item | Preferred starting value |
|---|---:|
| Signal trace width | 0.15–0.20 mm |
| Trace spacing | ≥ 0.15 mm |
| USB 2.0 differential | 90 Ω ±10 %: W 0.31 / S 0.15 mm on L1 over L2 of JLC04161H-7628 (D27; model 90.4 Ω, provisional until JLCPCB's differential calc is rerun) |
| VBUS trunk | sized for target current + margin; see OI-4 |
| Via diameter / drill | 0.45 / 0.25 mm (0.60 / 0.30 mm where space allows) |
| Copper to routed edge | ≥ 0.30 mm |
| Silkscreen text height | ≥ 1.0 mm Latin (see Section 6) |
| Silkscreen stroke | ≥ 0.15 mm |

USB 2.0 high-speed:

- Route each pair as a length-matched, tightly-coupled differential pair on one
  layer where practical.
- **Never split the reference plane under a pair.** Stitch GND at every layer
  transition near the pair.
- Keep pairs away from the MAU104, the shunt ladder, and LED drive.
- No stubs. No test points on the pairs.

Power:

- Route VBUS to protection and bulk capacitance first.
- One short wide trunk, not a chain through narrow passive pads.
- Estimate current and temperature rise before reducing width. Include inrush,
  hot-plug, and fault states — not only typical idle.
- Do not create an isolated copper island and assume it is connected.

Ground:

- Pour GND on Top and Bottom where practical; stitch at USB entry, ESD devices,
  the MCU, layer transitions, and board edges.
- Remove isolated islands. Refill zones after every routing or keepout change.
- Keep high-frequency return paths directly under their signals.

### 5.4 Measurement Integrity (specific to this board)

This board is an instrument. These are functional requirements, not polish.

- **Every shunt MUST use a Kelvin (4-wire) land pattern.** A 2-terminal shunt
  footprint puts trace and solder resistance directly into the reading.
- Sense traces MUST leave the shunt symmetrically, be routed as a tight pair,
  and carry no load current.
- Keep the ADC and Vref on a quiet local ground with a single defined tie to the
  main plane. Do not route load-return current under the ADC.
- Vref MUST have its own decoupling at its pins and a short path to the ADC
  reference pin.
- Shunt resistors MUST specify tolerance **and** TCR. The Rev0.4 accuracy budget
  (§4.2) assumes ±100 ppm/°C for every shunt and for each R_OUT / R1 pair. The
  Basic 0.1 Ω part at ±800 ppm/°C is not equivalent. Tolerance is removed by
  per-unit gain calibration; TCR is not.
- Nothing that leaks may connect between a shunt and the DUT. The port switch, all
  gate networks, the mirrors' R1 and every divider sit on the supply side; VBUS_x
  carries only the port capacitor, the discharge FET and one 10 kΩ amplifier input
  (Rev0.4 §3.1, G7).
- Range switching MUST be verified for both settling time and over-range
  survival. The architecture is fixed by D9/D17 (Rev0.4 §10). What is *not* yet
  established is that a built board meets the ≤ 3 µs-per-stage ranging budget,
  holds the new range within 100 µs, and survives a stuck range. These are
  bring-up measurements, not review items.
- The bypass FETs' R<sub>DS(on)</sub> MUST stay outside the sensed span. Its
  temperature coefficient is ~4000 ppm/°C against a ±100 ppm/°C shunt. Topology C
  guarantees this, because each amplifier senses only its own shunt (Rev0.4 §5).
- Zero-point calibration is a **functional requirement**, not a feature. Without
  it, the OP07 offset and the deliberate pedestal current that keeps the current
  mirror out of its dead zone (Rev0.4 §4.1) put up to 8 LSB (LOW, MID) or 13 LSB (HIGH)
  on the zero reading, against a 0.1 µA resolution of 1 LSB.

---

## 6. Silkscreen

Silkscreen is an assembly and service interface.

MUST include: product name, PCB revision, Pin 1 for every IC and the SWD
interface, LED/diode polarity, port labels (`HOST` / `OUT A` / `OUT B`), and
signal names at test and programming pads.

Rules:

- **Latin text ≥ 1.0 mm height, ≥ 0.15 mm stroke.**
- **CJK glyphs MUST be ≥ 2.0 mm, or not used.** A 0.8 mm kanji fills in and is
  unreadable. Prefer Latin plus icons on the user-facing panel — this is the
  fix for OI-6.
- Keep text off pads, paste, holes, slots, and the enclosure's port openings.
- Do not let reference text cross the board edge.
- One reading direction per functional area.
- Keep labels visible after assembly and after the lid is fitted.
- Do not use silkscreen to repair unclear copper or footprint geometry.
- Remove duplicate, obsolete, mirrored, or clipped text.

Review in ECAD 2D, 3D, a Gerber viewer with copper and mask visible, and the
JLCPCB manufacturing preview.

Do not print a third party's product name as a compatibility claim on the
silkscreen (`PPK2-COMPATIBLE` in the mockup). Describe the function instead.

---

## 7. Enclosure

The enclosure is part of the release, not an afterthought.

- The board outline, mounting holes, connector positions, and every case
  opening MUST come from **one** dimension source. Record which file is
  authoritative; the three.js mockup is not it.
- Connector openings MUST clear the **mating plug's overmold**, not just the
  receptacle shell. Verify against a real cable, not a datasheet outline.
- Fastener bosses MUST give at least 2 × D thread engagement (≥ 4 mm for M2),
  or use heat-set inserts. See OI-5.
- Fit the board on ≥ 3 mounting points, with at least one near each connector
  end. Repeated insertion force must not be carried by the solder joints.
- Print process (FDM / MJF) MUST be chosen before wall and clearance values are
  frozen; they differ.
- The lid PCB is a manufactured board and follows every rule in this file:
  own revision, own Gerber set, own release entry.

---

## 8. Design Gates

A revision may advance only when every gate reaches an explicit state.

| Gate | Verify | Expect |
|---|---|---|
| Requirements | Review mandatory functions and exceptions | Every requirement testable and owned |
| Power budget | Compute source, sink, and per-port budget against the negotiated contract | Advertised current is deliverable; OI-4 closed |
| Schematic | Run ERC; inspect power, USB, CC, analog, SWD | Zero critical errors |
| Footprints | Compare datasheets: pads, pitch, Pin 1, polarity, package | Every mounted part proven; every shunt is Kelvin |
| Stackup | Confirm JLCPCB stackup ID and impedance calculation | Differential geometry computed against the ordered stackup |
| Mechanical | Overlay outline, holes, connectors, and case openings | Plug overmold clears; ≥ 3 mounting points |
| Placement | Inspect Top/Bottom assembly and access | Zero Bottom mounted parts |
| Routing | Run DRC; inspect pairs, analog sense, return continuity | Zero critical violations, zero unrouted nets, no fragmented reference plane |
| Ground | Refill zones; inspect return continuity | No unintended split or isolated island |
| Gerber | Inspect every layer, outline, drill, fiducials | Export matches the frozen PCB; ≥ 3 global fiducials present |
| BOM/CPL | Compare designator sets, packages, side, coordinates, rotation | One-to-one agreement |
| JLCPCB | Inspect DFM, part mapping, placement preview | No unknown substitution, polarity, or off-board part |
| Functional | Test power, enumeration, switching, measurement accuracy vs a reference meter | All acceptance tests pass |
| Release | Validate manifest and checksums | One immutable coordinated release |

“Exported”, “uploaded”, or “quote created” is **not** a terminal state. Each
must end as approved, rejected, or returned to `WIP` with an owner and reason.

**A checker only proves what it looks at** (easy-stick 14.2). When adding an
automated check, write down what it *cannot* see next to the check itself, and
negative-test it against a deliberately corrupted input before relying on it. A
checker never observed failing is not evidence.

---

## 9. Cost and JLCPCB

Cost optimization begins in architecture, not at checkout.

- Use the **fewest layers** that satisfy signal, ground, and EMC requirements
  (OI-10). The 4→6 layer step is the single largest cost lever on this board.
- Keep machine assembly Top-only, and hand assembly to the large Akizuki parts (D13).
- Standard thickness, copper weight, trace, spacing, drill, via options.
- Minimize unique part types and Extended-part feeder changes.
- 0201 assembly carries a per-part cost and yield penalty. Use 0402 as the
  default and 0201 only where area genuinely forces it.
- Prototype before volume. Compare **total landed cost**: components, setup,
  panel rails, engineering fees, shipping, rework, yield.

Do **not** optimize by: choosing an unknown footprint; removing decoupling or
ESD protection; reducing copper or clearance below robust margins; lowering a
voltage/temperature/TCR rating without analysis; selecting a part only because
it is in stock today; skipping placement confirmation; ordering an incomplete
board to save a review cycle.

ENIG is the assumed finish (flat surface for fine-pitch QFN and 0201). Recheck
the live quote and capability page at every release — limits, fees, lead time,
inventory, and auto-confirmation deadlines change.

---

## 10. Product Requirements

Status: **WIP — MANUFACTURING PROHIBITED.**

### 10.1 Intent

A 2-channel switched USB-C hub that measures each downstream port's current
over a wide dynamic range, so a device under test can be power-profiled and
power-cycled from the host.

### 10.2 Functional blocks (from the mockup — historical)

**Superseded by `design/circuit/CIRCUIT_DESIGN_Rev0.4.md` §6.2, which is the
authoritative designator and block list.** This table is kept only as the record
of what the mockup claimed and what was wrong with it; do not design from it.

| Ref | Function | Mockup placeholder | Status |
|---|---|---|---|
| J1 | USB-C upstream (host) | — | outline only |
| J2, J3 | USB-C downstream, switched | — | pitch fails, see OI-1 |
| U1 | MCU | RP2040, QFN-56 | needs 12 MHz XTAL + QSPI flash |
| U2 | USB 2.0 hub, 4-port | QFN-36 | needs own 24 MHz XTAL, see OI-2 |
| U3, L1 | Buck regulator | QFN-8 + 2.5×2.0 | rail voltages undefined |
| U4 | 3V3 LDO | SOT-23-5 | — |
| U5 | QSPI flash | USON-8 | — |
| U6 | ADC, 24-bit | QFN-24 | part not selected |
| U7, U8 | Range amplifiers | QFN-16 | part not selected |
| U9, U10 | Load switches | QFN-8 | need reverse blocking, see OI-7 |
| U11 | Voltage reference | SOT-23-5 | TCR spec required |
| Q1, Q2 | Range-switch FETs | SOT-23-6 ×1/ch | count insufficient, see OI-3 |
| Q3, Q4 | CC Rp gating FETs | SOT-23-6 | — |
| D1–D3 | ESD arrays | SOT-23-6 | channel count short, see OI-7 |
| RS1–RS4 | Shunt ladder 10 mΩ / 1 Ω / 100 Ω / 1 k | 2512/0805/0402/0402 | Kelvin required; 1 Ω power rating fails, see OI-3 |
| SW1, SW2 | Per-port tactile switches | — | — |
| D10–D17 | Status LEDs ×8 | — | — |
| — | SWD | 6 pads @ 1.27 mm | no fixture datums, see OI-8 |

### 10.3 Fixed requirements

`requirements/product.md` is the authority for requirements (REQ-* IDs, each
traced to a V-* entry in `requirements/verification.md`). This list is the
summary; where the two differ, `product.md` wins and this list is the defect.

- Board thickness 1.6 mm, ENIG. **Outline 100 × 72 mm, 4 layers (D10, D24),** inside
  100 × 100 mm. Stackup JLC04161H-7628, no impedance control for the prototype (D27).
  JLCPCB machine-places Top SMD only; the large Akizuki parts are hand-soldered
  (D13, REQ-MFG-01).
- **Sourcing (D13, user):** machine-placed parts are JLCPCB Basic and in stock;
  hand-soldered parts are in stock at Akizuki; never an Extended-only PCBA
  (REQ-MFG-05). Avoid special or hard-to-source parts; keep part types and count low.
  Preferred Extended parts are excluded too (D22, user).
- Port power comes from **J4, a power-only 5 V USB-C input**. J1 carries data and
  logic power only, and there is no USB-PD (D14, superseding D1).
- Downstream presents Rp on both CC pins only while its port is ON, so the DUT
  detaches cleanly. Rp = 33 kΩ is sourced from the port's EN pin and advertises
  Default power (REQ-PORT-07, D18). The ports never advertise, in total, more than
  J4 advertises (REQ-PWR-03/04).
- Each downstream port MUST be independently switchable under firmware control.
- The board MUST enumerate on the upstream PC as a **CDC-ACM COM port** and be
  fully controllable from a plain terminal — driverless on Windows, macOS and
  Linux (D7). Each unit MUST report a unique USB serial number, or Windows COM
  numbering will not be stable across replugs.
- Measurement range **0.1 µA – 1 A** per channel, by 3 hardware ranges plus
  mandatory zero-point calibration. Up-ranging is a hardware comparator loop,
  not firmware polling (D4 as amended by D17); firmware holds and down-ranges.
- Firmware recovery MUST be reachable without disassembly (REQ-BOOT-01; see OI-9).
- ≥ 3 global fiducials, 1 mm copper / 2 mm mask opening.

### 10.4 Decisions closed

Recorded in `design/circuit/CIRCUIT_DESIGN_Rev0.4.md` Section 10 (D1–D27; D12 is
withdrawn and not reused).

- **User decisions:** KiCad (D2), CDC-ACM ×2 (D7), 4 layers (D10), the outline limit of
  100 × 100 mm (D24, 「100x100未満ならいいんだっけ」),
  the sourcing rule (D13), and Basic parts only, with no Preferred Extended (D22,
  「外して Basic のみにする」). D1 (PD sink) and D11 (USB2514B) were also user
  decisions; both are superseded because their parts are Extended.
- **Under the delegation:** on 2026-11-03 the user delegated the open choices
  (「推奨で任せるよ」). Claude recorded D14–D21: J4 power input, CH335F hub,
  topology C with current mirrors, the port path, the clocks, the accuracy target,
  and the adoption of P9–P12. After D22, Claude recorded D23: the PGA2040 RP2040
  module and two MCP3208 ADCs, superseding D16's STM32F103. Within D24's limit, Claude
  chose the 100 × 72 mm outline from the OI-23 study, and D25 put the MF-R300 input fuse
  on J4 (OI-29), and D26 set how J1's current is declared (OI-25). D27 named the
  JLC04161H-7628 stackup and the provisional USB pair geometry, without impedance
  control for the prototype. Each is labelled
  "Claude (delegated)", and the user may revert any one.

### 10.5 Still undecided — record the decision before layout starts

- **OI-31:** the PGA2040's supply input, USB series resistors and flash, and the
  MCP3208 sampling assumptions. U1's footprint and power wiring depend on it.
- **OI-23 (remainder):** re-run the placement study with the measured CH335F outline
  (OI-24) and the chosen header height. The board area itself is settled by D24.
- **OI-27, OI-28:** bench-check the OP07 single-supply margins and R_M's overload
  before layout.
- USB VID/PID. Do not ship a squatted VID.
- Whether the mockup's placement is kept at all. Assume not.

---

## 11. Open Issues

OI-1 – OI-15 were found by review of the mockup on 2026-08-16; OI-16 – OI-22 by the
review that produced Rev0.2 on 2026-11-03; OI-23 – OI-30 by the Rev0.3 redesign under
the sourcing rule D13 (2026-11-03); OI-31 by the Rev0.4 change to Basic parts only
(D22, 2026-11-03). Every issue not struck through is **blocking**.
Numbers are stable; close them in Git with evidence, do not renumber.

- "Closed by decision" means the design intent is settled but nothing is built or
  measured. Reopen the issue if the built board disagrees.
- A decision marked "Claude (delegated)" was made under the user's 2026-11-03 delegation,
  and the user may revert it.
- "Rev0.4 §n" refers to `design/circuit/CIRCUIT_DESIGN_Rev0.4.md`. Rev0.3 and Rev0.4
  share their section numbers.
- The Rev0.2 text is at commit `4e59607`:
  `git show 4e59607:design/circuit/CIRCUIT_DESIGN_Rev0.2.md`.
- The Rev0.3 text is at commit `4e43692`:
  `git show 4e43692:design/circuit/CIRCUIT_DESIGN_Rev0.3.md`.

| ID | Issue | Evidence |
|---|---|---|
| OI-1 | **Two USB-C plugs cannot be inserted at once.** The mockup's downstream pitch is 10.8 mm; plug overmolds are 12–14 mm. *Rev0.3:* J2/J3 are 20 mm-wide Akizuki modules placed side by side, so the pitch is ≥ 20 mm (D21, REQ-MECH-02). Open until checked with real cables (V-MECH-01). | `PORT_Z = 5.4` in the mockup; Rev0.4 §10 D21 |
| OI-2 | ~~No crystal for the USB hub.~~ **Closed by decision** (D19, Claude delegated, 2026-11-03): a 12 MHz Basic crystal (C9002), Y2 → CH335F; the MCU module carries its own crystal, so D23 removed Y1 (→ STM32 HSE). The history: D6's shared oscillator was superseded by D11; the USB2514B (24 MHz) was itself superseded by D13. Y2 against CH335F's built-in load capacitors is checked at bring-up (G9). | Rev0.4 §6.3 |
| OI-3 | ~~Range switching unimplementable.~~ **Closed by decision** (D9/D17): ranges 0.1 Ω / 10 Ω / 510 Ω in a nested bypass ladder, LM393 up-ranging ≤ 3 µs per stage, firmware hold ≤ 100 µs, bypass default ON. Bring-up proves the budget (V-MEAS-02). | Rev0.4 §3.2, §4 |
| OI-4 | ~~Power budget contradicts the spec.~~ **Closed by decision** (D14): D1's PD sink is superseded; port power comes from J4, a power-only 5 V input. Its USB-C advertisement drives the advertisement and budget rules (REQ-PWR-04/05). | Rev0.4 §3.1, §7.2 |
| OI-5 | **Fastening will not survive use.** 2 × M2 at one end only, 1.6 mm thread engagement (want ≥ 4 mm), and the PCB itself is not clamped. *Rev0.3:* heat-set M2 inserts at 4 corners adopted (D21). Open until built and checked (V-MECH-01). | boss height = `GAP` = 1.6 |
| OI-6 | **Silkscreen below fab minimum.** Reference designators 0.80 mm; user-facing kanji 0.81 mm. | canvas px/mm scale |
| OI-7 | ~~Protection incomplete.~~ **Closed by decision** (D18), with two residuals moved to their own issues. ESD: PSM712 on the CC pins of J1–J4; D+/D− of J1–J3 are unprotected since D22 removed SRV05-4 (product.md §9). TVS: SMBJ6.5CA on the J1 and J4 VBUS. Reverse blocking: back-to-back AO3401A. No TVS on VBUS_A/B, by design: its leakage would be measured, and the port capacitor absorbs ESD. No common-mode choke: not needed for USB 2.0, and none is Basic. Residual: the J4 fuse (OI-29, closed by D25). SRV05-4's class (OI-30) ended with its removal (D22). | Rev0.4 §3.1, §3.4, G10 |
| OI-8 | **Not testable.** Zero fiducials for 0201 placement; no panelization defined; SWD pads have no fixture datums. *Rev0.3:* TC2030-NL SWD footprint and test pads adopted (D21, REQ-MFG-03/04). Panelization still undefined. | — |
| OI-9 | ~~BOOTSEL unreachable with the lid fitted.~~ **Closed by decision** (D21 as amended by D23): the RP2040 ROM USB bootloader (UF2 drive), entered by `BOOT` or by SW3 on BOOTSEL through a lid pinhole. It is in mask ROM, so no firmware state removes it; SWD is for debug only. Reopen if V-BOOT-01 fails. | REQ-BOOT-02 |
| OI-10 | ~~6 layers may be unjustified.~~ **Closed by decision** (D10, user, 2026-11-03): 4 layers. Reopen if signal-integrity or EMC review of the routed board disagrees. | Rev0.4 §10 |
| OI-11 | ~~Shunts are 2-terminal.~~ **Closed by decision** (D17, topology C): each shunt has its own amplifier and Kelvin connection. R_H is a 2-terminal chip on a 4-pad land; R_M has its sense taken at each lead pad; R_L is 0805. No FET R<sub>DS(on)</sub> is inside a sensed span. | Rev0.4 §3.2, §5, G2 |
| OI-12 | ~~Documentation disagrees with itself.~~ **Closed 2026-11-03:** the mockup's `<title>` and caption now state the 60 × 24 mm its model actually has, and that the mockup is superseded by D10 (now D24). | `mockup/usb-power-hub-board.html` |
| OI-13 | ~~Board area — 60 × 24 mm is not routable (75 % density).~~ **Closed by decision** (D10, user, 2026-11-03): **85 × 35 mm, 4 layers**. Every mockup dimension and the enclosure model are invalidated by it. The module-heavy part mix of Rev0.3 and Rev0.4 did not fit, so D24 enlarged the outline to **100 × 72 mm** (OI-23). | Rev0.4 §10, §11 |
| OI-14 | ~~Sample rate capped by the host interface.~~ **Closed by decision** (D17 as amended by D23): the rate is 14.0 kSPS per channel, set by two MCP3208 at a 1 MHz clock with a stretched sample phase, and the stream uses 5.9 % of Full-Speed bulk. Faster profiling would need a faster ADC: that is a new decision, not a defect. | Rev0.4 §3.3 |
| OI-15 | ~~The repository is not under version control.~~ **Closed 2026-11-03:** `usb-power-hub` is its own Git repository on branch `main`, no remote; commit `4dd10fb` is the unmodified snapshot of the design as it was paused. | `git log` |
| OI-16 | ~~Downstream current policy is undefined.~~ **Closed by decision** (D18): each port advertises Default (Rp 33 kΩ, 500 mA). A port is enabled only while J4's advertisement covers all ON ports. Measured over-budget opens the larger port (`FAULT:BUDGET`). Hardware OC trips at 1.16 A. | Rev0.4 §7.2; REQ-PWR-04/05 |
| OI-17 | ~~The 9 V request (D1) assumes an upstream that may not exist.~~ **Closed by decision** (D14): no PD; port power comes from J4, so it no longer depends on the host PC. The cost is a second cable and an unregulated port voltage (product.md §9). | Rev0.4 §3.1 |
| OI-18 | ~~The 3.3 V rails as drawn overheat.~~ **Closed by decision** (D14): AMS1117-3.3 (SOT-223) from J1 5 V dissipates 0.079 W, a 7 °C rise (47 mA in Rev0.4). The op-amps run from the MAU104, not from a 3.3 V rail. | Rev0.4 §7.1 |
| OI-19 | ~~Sense topology D5 needs re-evaluation.~~ **Closed by decision** (D17): topology C, with discrete OP07CDR + AO3401A current mirrors. No mux and no current-sense amplifier is Basic. | Rev0.4 §5 |
| OI-20 | ~~No stocked HIGH shunt meets the specification.~~ **Closed by decision** (D17/D20): R_H = 0.1 Ω ±0.5 % ±100 ppm/°C KOA TSL1TTER100D (Akizuki, 374 pcs), inside the ±1 % budget. The Basic 0.1 Ω part (±800 ppm/°C) is rejected. | Rev0.4 §4.2; `requirements/parts.md` |
| OI-21 | ~~No accuracy requirement exists.~~ **Closed by decision** (D20): ±(1 % of reading + 3 LSB of the active range) within ±10 °C of calibration, after gain and zero calibration. | REQ-MEAS-05; Rev0.4 §4.2 |
| OI-22 | ~~The ADC has no clock.~~ **Closed by decision** (D23, replacing D17's on-chip ADC): two external MCP3208, clocked at 1 MHz by the RP2040 PIO. | Rev0.4 §3.3 |
| OI-23 | **Board fit: area settled, outlines not measured.** The placement study (`design/experiments/oi-23-placement/`, 15 tests) proved that 85 × 35 mm cannot hold Rev0.4: even with no routing space and every low part credited under a module, it needs 3,780 mm² (F1 included, D25) against 2,975 mm². D24 set 100 × 72 mm, where a block placement passes every check at routing factor K = 1.6 (headroom to K = 1.74). Still open: the CH335F outline is measured off a product photo (OI-24), and the header height behind the study's 1.5 mm under-module rule is not chosen. Re-run the study with both; it must still exit 0. | Rev0.4 §11; study README |
| OI-24 | **CH335F module outline and pin map unknown.** Akizuki publishes no drawing for AE-QFN28-DIP(CH335F). Measure a purchased module, and confirm that the QFN comes mounted and how DIP30 maps to the chip's pins. | `requirements/parts.md` U6 |
| OI-25 | ~~J1 current is misdeclared.~~ **Closed by decision** (D26, Claude delegated, 2026-11-03): the CH335F stays self-powered at its default 100 mA, and the RP2040 function declares bMaxPower 200 mA. That covers its 126 mA typical share of J1's ≈ 0.21 A (172 mA with every OP07 at its maximum). USB still charges the upstream port only 100 mA, so the board is specified for 500 mA upstream ports and not for bus-powered hubs. Options (a) and (b) are recorded as rejected in D26. Reopen if V-HOST-01 measures more than 0.30 A from J1. | Rev0.4 §7.1, §10 |
| OI-26 | **HS signal integrity through the modules is unverified.** D± pass through 2.54 mm headers and Akizuki module layouts. The fallback is that DUTs enumerate at FS. | Rev0.4 §3.3; V-HOST-01 |
| OI-27 | **OP07 single-supply operation is extrapolated.** Unverified: common mode 2–10 V and output low ≤ 3.0 V on 0 / 12 V (extrapolated from ±15 V specs); the mirror gate's headroom at 1 A, which F1 (D25) cuts to 0.11–0.36 V with one port loaded and to 0.03 V at J4 = 4.75 V with both ports at 1 A; loop stability into a 645 pF gate. Bench-check before layout (V-MEAS-00). | Rev0.4 §3.2 |
| OI-28 | **R_M short-time overload is unverified.** A stuck-MID short puts 2.35 W into a 1 W axial resistor for up to 10 ms. | Rev0.4 §4; V-MEAS-00 |
| OI-29 | ~~No input fuse on J4.~~ **Closed by decision** (D25, Claude delegated, 2026-11-03): F1 = Bourns MF-R300 (Akizuki g112630; 3.00 A hold, 2.49 A at 40 °C; 6.00 A trip; 30 V), ahead of the J4 TVS. Its 0.08 Ω (R1max) costs up to 0.16 V at 2 A, which moves into OI-27 and V-MEAS-00. No fuse or PTC is Basic, so it is hand-soldered. Reopen if V-SAFE-02 fails. | Rev0.4 §3.1, §7.2; `requirements/parts.md` |
| OI-30 | ~~Two Preferred Extended parts need the user's decision.~~ **Closed by decision** (D22, user, 2026-11-03): Basic parts only. STM32F103C8T6 (C8734) and SRV05-4 (C7420376) are removed; D23 replaces the MCU with the PGA2040 and two MCP3208, and D± of J1–J3 lose their ESD protection. | Rev0.4 §9, §10 D22/D23 |
| OI-31 | **PGA2040 and MCP3208 assumptions unverified.** From a purchased PGA2040, confirm the supply input (3.3 V only, or 5 V through an on-module regulator), whether the 27 Ω USB series resistors are on the module, and that the flash reports a 64-bit unique ID. Bench-check the MCP3208's stretched sample phase (≤ 0.21 LSB computed), its INL at V<sub>REF</sub> = 3.3 V, and the RP2040's reset pull-down against the 10 kΩ hold pull-ups. The fallback for the sample phase is double conversion at 8 kSPS; a failure otherwise reopens D23. | Rev0.4 §3.2, §3.3, §6.2; V-MEAS-06 |

---

## 12. Pre-Order Checklist

- [ ] PCB revision correct; `MANUFACTURING APPROVED` recorded in this file.
- [ ] All Section 11 open issues closed with evidence in Git.
- [ ] Frozen source export committed.
- [ ] ERC critical errors: 0. DRC critical errors: 0. Unrouted nets: 0.
- [ ] Board dimensions and mechanical overlay accepted against the authoritative
      mechanical source.
- [ ] JLCPCB stackup ID recorded; differential impedance computed against it.
- [ ] Machine-placed components on Top only. Bottom paste apertures: 0. Hand-soldered
      parts are listed separately and appear in neither BOM nor CPL (V-MFG-01).
- [ ] Every BOM line Basic, with no Preferred Extended (D22); every hand-soldered
      part in stock at Akizuki (V-MFG-02).
- [ ] Every shunt uses a Kelvin land pattern.
- [ ] ≥ 3 fiducials present in the Gerber.
- [ ] Silkscreen: Latin ≥ 1.0 mm, no CJK below 2.0 mm, nothing clipped.
- [ ] BOM MPN, LCSC number, package, quantity, JLCPCB assembly stock, and
      Basic/Extended status reviewed.
- [ ] BOM and CPL designator sets match; every CPL entry is Top and inside the
      outline.
- [ ] Pin 1 of every IC, LED cathodes, ESD and connector orientation verified in
      the JLCPCB placement preview.
- [ ] Enclosure fit verified against a real USB-C cable, not a drawing.
- [ ] Gerber, BOM, CPL, source, manifest, and checksums share one revision.
- [ ] JLCPCB DFM, part mapping, and placement preview accepted.
- [ ] Prototype or first-article evidence attached.
- [ ] Final landed cost, shipping, and lead time reviewed.
- [ ] **User approval obtained before order submission or payment.**

---

## 13. Verified Practices Learned Here

Empty. Add an entry only after a learning has been **verified on this board**.
Update an entry in place rather than appending a second copy, and delete one
later shown to be wrong. A plausible-sounding rule with no incident behind it
belongs in Sections 1–12 as policy, not here.

Until this section has content, the easy-stick lesson index
(`../easy-stick/docs/engineering-lessons/README.md`) is the incident record to
read. Process learnings from working this repository (tooling, Git) are kept in
`.claude/memory/rules.md`, not here — this section is for the board.
