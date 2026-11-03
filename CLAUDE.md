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
> `design/circuit/CIRCUIT_DESIGN_Rev0.2.md` (revised 2026-11-03; Rev0.1 is in Git
> history) — together with the requirements set in `requirements/`
> (`product.md`, `verification.md`, `parts.md`). That is currently the whole of
> the design. There is **no netlist, no schematic capture, no layout, no
> manufacturing output**. Candidate parts have been looked up in the JLCPCB
> assembly pool (`requirements/parts.md`, dated stock), but **none is confirmed**:
> no footprint is verified and no order-time stock check has been done. Nothing
> has been built or measured.
>
> The other thing that exists is a three.js appearance mockup
> (`mockup/`). Component names such as `U2_usb_hub` in it are placeholders, not
> procurement specifications, and Rev0.2 (85 × 35 mm, 4 layers, D10) supersedes
> its outline and layer count. Section 11 lists the blocking issues.
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

- FR-4 PCB, 1.6 mm, **85 × 35 mm, 4 layers** (D10, decided by the user
  2026-11-03; closes OI-13 and OI-10).
- Surface-mount, Top-side assembly. Bottom reserved for copper, vias, and mask.
- USB-C receptacles ×3 (1 upstream host, 2 switched downstream).
- USB-PD sink upstream, 9 V requested, bucked to a regulated 5.10 V port rail.
- Precision current measurement, **0.1 µA – 1 A**: 3-range shunt ladder with
  hardware auto-ranging + 24-bit ADC, two independent channels.
- Enumerates as a **CDC-ACM COM port** on the upstream PC; driverless control.
- LCSC parts and JLCPCB PCB/PCBA services.
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
│  ├─ circuit/                  # CIRCUIT_DESIGN_Rev<X.Y>.md — the schematic, as a document
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
├─ firmware/                    # RP2040 — src/ include/ tests/ tools/ reports/
├─ manufacturing/
│  ├─ working/                  # disposable candidate exports — never orderable
│  └─ releases/<rev>/<rNN>/     # immutable approved or ordered releases
├─ tests/                       # fixtures/ reports/ — physical test evidence
├─ docs/
│  └─ decisions/                # one file per closed architectural decision (until
│                               #   created, decisions D1–D11 live in circuit §10)
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
- Compute USB 2.0 differential geometry **against that stackup**, using
  JLCPCB's impedance calculator, before routing.
- Order with the impedance-control option if HS eye margin depends on it.

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
  contiguous block, away from the buck converter, the hub, and LED switching.**
- Keep the buck converter's switching loop small and away from the ADC.
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
| USB 2.0 differential | per JLCPCB calc for 90 Ω ±10 % |
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
- Keep pairs away from the buck switch node, the shunt ladder, and LED drive.
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
- Shunt resistors MUST specify tolerance **and** TCR. A 200 ppm/°C part is not
  equivalent to the HIGH-shunt specification of ≤ 25 ppm/°C (Rev0.2 §4; no
  stocked part meets it yet — OI-20). Tolerance is removed by per-unit gain
  calibration; TCR is not.
- Range switching MUST be verified for both settling time and over-range
  survival. The architecture is fixed by D3/D4/D9 (Rev0.2 §10); what is *not*
  yet established is that a built board meets the 2 µs ranging budget or
  survives a stuck low range. Both are bring-up measurements, not review items.
- The bypass FETs' R<sub>DS(on)</sub> MUST stay outside the sensed span. Its
  temperature coefficient is ~4000 ppm/°C against a ≤ 25 ppm/°C shunt; inside
  the span it makes the total ≈ 1900 ppm/°C (Rev0.2 §3.2, §5).
- Zero-point calibration is a **functional requirement**, not a feature. Without
  it the amplifier's input offset alone exceeds the 0.1 µA resolution target by
  more than a factor of one (Rev0.2 §4, Condition 1).

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
- Keep assembly Top-only.
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

**Superseded by `design/circuit/CIRCUIT_DESIGN_Rev0.2.md` §6.2, which is the
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

- Board thickness 1.6 mm, Top-side assembly, ENIG. **Outline 85 × 35 mm, 4
  layers (D10).**
- Upstream is a **USB-PD sink** requesting 9 V with 5 V fallback (D1). Whether
  the intended host can grant 9 V at all is OI-17.
- Downstream presents Rp on both CC pins and removes it when its port is switched
  off, so the DUT detaches cleanly. Rev0.1 gated Rp by port VBUS; P3 proposes
  gating it by the port's EN signal instead (REQ-PORT-07). The Rp *value* must
  never advertise more than can be delivered; the rule that sets it is OI-16.
- Each downstream port MUST be independently switchable under firmware control.
- The board MUST enumerate on the upstream PC as a **CDC-ACM COM port** and be
  fully controllable from a plain terminal — driverless on Windows, macOS and
  Linux (D7). Each unit MUST report a unique USB serial number, or Windows COM
  numbering will not be stable across replugs.
- Measurement range **0.1 µA – 1 A** per channel, by 3 hardware ranges plus
  mandatory zero-point calibration (D3). Auto-ranging is a hardware comparator
  loop, not firmware polling (D4).
- BOOTSEL recovery MUST be reachable without disassembly (see OI-9).
- ≥ 3 global fiducials, 1 mm copper / 2 mm mask opening.

### 10.4 Decisions closed

Recorded in `design/circuit/CIRCUIT_DESIGN_Rev0.2.md` Section 10 (D1–D11).
ECAD tool = **KiCad** (D2). Upstream power contract, measurement range, ranging
architecture, sense topology, host interface, and ladder fail-safe state are
closed there. D6 (one shared 12 MHz oscillator) is **superseded**: D10 (85 × 35
mm, 4 layers) and D11 (USB2514B hub) were decided by the user on 2026-11-03. The
replacement clock arrangement is proposal P13, not a decision — OI-2 is open.

### 10.5 Still undecided — record the decision before layout starts

- **Power:** downstream current policy (OI-16) and what happens on a 5 V-only
  host (OI-17). Both change the power-path topology, so they block capture.
- **Measurement:** sense topology B vs C (OI-19), the HIGH shunt (OI-20), and
  the accuracy target (OI-21), which also decides whether the ADC's internal
  reference suffices or a discrete reference is needed.
- **Clocks** (OI-2): accept or replace P13 (separate 12 MHz and 24 MHz crystals).
- **Proposals P1–P13** in Rev0.2 §14 — each is a candidate decision awaiting
  the user, not a decision.
- USB VID/PID. Do not ship a squatted VID.
- Whether the mockup's placement is kept at all. Assume not.

---

## 11. Open Issues

OI-1 – OI-15 were found by review of the mockup on 2026-08-16; OI-16 – OI-22 by the
review that produced Rev0.2 on 2026-11-03. Every issue not struck through is
**blocking**. Numbers are stable; close them in Git with evidence, do not renumber.
"Closed by decision" means the design intent is settled but nothing is built or
measured — reopen if the built board disagrees. "Rev0.2 §n" refers to
`design/circuit/CIRCUIT_DESIGN_Rev0.2.md`; "P n" to its Section 14 proposals, which
are **not** decisions until the user accepts them.

| ID | Issue | Evidence |
|---|---|---|
| OI-1 | **Two USB-C plugs cannot be inserted at once.** Downstream receptacle pitch is 10.8 mm (shell gap 1.86 mm); plug overmolds are 12–14 mm. Growing the board (OI-13) makes a fix possible but does not itself fix it — J2/J3 must actually be moved apart, and the new pitch re-checked against a real overmould. *2026-11-03:* D10 provides the length; P9 proposes ≥ 18 mm centre pitch (REQ-MECH-02). Open until checked with real cables (V-MECH-01). | `PORT_Z = 5.4` in the mockup; Rev0.2 §14 P9 |
| OI-2 | **No crystal for the USB hub.** Closed by decision (D6) on 2026-08-16 with one shared 12 MHz oscillator; **reopened 2026-11-03** because D11 chose the 24 MHz USB2514B, so the shared oscillator no longer works. P13 proposes Y1 12 MHz crystal → RP2040 only and Y2 24 MHz crystal → USB2514B only. Open until the user accepts a clock arrangement. | Rev0.2 §6.3, §10, §14 P13 |
| OI-3 | ~~Range switching unimplementable.~~ **Closed by decision** (D3/D4/D9): 3 ranges 20 mΩ / 2 Ω / 200 Ω, 2 bypass FETs + sense mux per channel, hardware comparator loop with a 2 µs budget, FETs default ON. *2026-11-03:* the stuck-range dissipation figures were corrected; the conclusion stands. | Rev0.2 §4, §7.3 |
| OI-4 | ~~Power budget contradicts the spec.~~ **Closed by decision** (D1): PD sink requests 9 V; buck to 5.10 V; 2 × 1 A needs ≥ 13.5 W upstream. *2026-11-03:* rails recounted at V5P1 (1.02 W, not 0.66 W) — 2 × 1 A still fits 13.5 W with 8 % margin. The Rp rule moved to OI-16, the 9 V assumption to OI-17. | Rev0.2 §7.1 |
| OI-5 | **Fastening will not survive use.** 2 × M2 at one end only, 1.6 mm thread engagement (want ≥ 4 mm), and the PCB itself is not clamped. *2026-11-03:* P12 proposes heat-set M2 inserts at 4 corners. | boss height = `GAP` = 1.6 |
| OI-6 | **Silkscreen below fab minimum.** Reference designators 0.80 mm; user-facing kanji 0.81 mm. | canvas px/mm scale |
| OI-7 | **Protection incomplete.** 2-terminal footprint for a 4-terminal common-mode choke; ESD channel count short of USB-C's D±/CC/SBU; no VBUS TVS; no reverse-current blocking on the outputs. *2026-11-03:* reverse blocking is covered by the SY6280AAC candidate (P2; datasheet: no body diode, blocks when disabled); TPD4E05U06 is the D±/CC ESD candidate. VBUS TVS and the CMC footprint remain open. | `FB1_cmc`, `D1`–`D3`; `requirements/parts.md` |
| OI-8 | **Not testable.** Zero fiducials for 0201 placement; no panelization defined; SWD pads have no fixture datums. *2026-11-03:* P11 proposes a TC2030-NL SWD footprint and test pads (REQ-MFG-02/03/04). Panelization still undefined. | — |
| OI-9 | **BOOTSEL unreachable with the lid fitted.** *2026-11-03:* P10 proposes a `BOOT` command plus a lid pinhole (REQ-BOOT-02). | `BOOT_pad_*` |
| OI-10 | ~~6 layers may be unjustified.~~ **Closed by decision** (D10, user, 2026-11-03): 4 layers. Reopen if signal-integrity or EMC review of the routed board disagrees. | Rev0.2 §10 |
| OI-11 | ~~Shunts are 2-terminal.~~ **Closed by decision** (D5): 20 mΩ is a 4-terminal part; 2 Ω and 200 Ω get Kelvin land patterns; an analog mux selects which Kelvin pair the amp sees, keeping FET R<sub>DS(on)</sub> outside the sensed span. Re-evaluation of the mux: OI-19. | Rev0.2 §5 |
| OI-12 | ~~Documentation disagrees with itself.~~ **Closed 2026-11-03:** the mockup's `<title>` and caption now state the 60 × 24 mm its model actually has, and that the mockup is superseded by D10. | `mockup/usb-power-hub-board.html` |
| OI-13 | ~~Board area — 60 × 24 mm is not routable (75 % density).~~ **Closed by decision** (D10, user, 2026-11-03): **85 × 35 mm, 4 layers**, 36 % density. Every mockup dimension and the enclosure model are invalidated by it; OI-1 and OI-5 follow from that. | Rev0.2 §11 |
| OI-14 | **Sample rate is capped by the host interface, not the ADC.** RP2040's USB is Full-Speed only; 32 kSPS × 2 ch uses ~16 % of FS bulk, 100 kSPS uses ~49 %. D8 targets 32 kSPS — 31.25 kSPS with the 8 MHz ADC clock, ~18 % of FS bulk including per-sample flags. If faster profiling is a real requirement, it needs an MCU with High-Speed USB or burst-buffered readout — that is an architecture change, not a firmware tweak. | Rev0.2 §3.3 |
| OI-15 | ~~The repository is not under version control.~~ **Closed 2026-11-03:** `usb-power-hub` is its own Git repository on branch `main`, no remote; commit `4dd10fb` is the unmodified snapshot of the design as it was paused. | `git log` |
| OI-16 | **Downstream current policy is undefined.** Rev0.1 advertised 1.5 A (22 kΩ Rp) on any 9 V contract, but "9 V granted" does not say how much current was granted. Two ports at 1.5 A need 18.1 W at the input (more than a 9 V / 2 A source) and 3.2 A from U2 (rated 2.5 A), while the measurement full scale is 1 A (ADC clips ≈ 1.2 A). Decide each port's allotted current (1.0 or 1.5 A) and the rule from granted power to Rp. CH224Q makes the granted current readable (P1). | Rev0.2 §7.1, §7.2; REQ-PWR-05 |
| OI-17 | **The 9 V request (D1) assumes an upstream that may not exist.** J1 is the only power input and also the data upstream, so it normally connects to the host PC — and PC USB-C ports commonly offer only 5 V. A buck cannot make 5.10 V from 5 V (TPS62933 has no 100 % duty mode; TPS62130 can only pass VPD through), and a non-PD source does not report its current. Decide which host(s) the product must work from (measure them with V-PWR-01), then: buck-boost (TPS63070, 2 A; TPS55288), a second power-only input, or an accepted unregulated 5 V mode. | Rev0.2 §3.1; `requirements/parts.md` U2 |
| OI-18 | **The 3.3 V rails as drawn overheat.** Rev0.1 fed the LDOs from VPD: (9 − 3.3) V × 0.2 A = 1.14 W in SOT-23-5, ≈ 213 °C junction rise. Fed from V5P1, a SOT-23-5 LDO still rises ≈ 64 °C at 190 mA. P5: digital rail from a small buck (SY8089 class) or a SOT-223 LDO; analog rail from a low-noise LDO on V5P1. | Rev0.2 §3.1; TPS7A20 R<sub>θJA</sub> 187.1 °C/W |
| OI-19 | **Sense topology D5 needs re-evaluation.** Its alternative C (one amplifier per shunt) was rejected only on area, which D10 removed. Meanwhile the 5 V-common-mode mux of topology B must be powered from VPD as a ≥ 10 V-class part, and the two candidates found have 225 pcs (TMUX6209PWR) and 919 pcs (ADG1209, SOIC-16). Decide B vs C (P4). | Rev0.2 §5; `requirements/parts.md` U10/U20 |
| OI-20 | **No stocked HIGH shunt meets the specification** (20 mΩ, 4-terminal, ≤ 25 ppm/°C). The only candidate found, Vishay WSK2512R0200FEA, had 14 pcs on 2026-11-03 and is specified ±35 ppm/°C. Options: relax to ≤ 50 ppm/°C (≈ 0.07 % over 20 °C — needs OI-21 first); 10 mΩ WSK2512R0100FEA (822 pcs) at G = 100 (topology C) or at half scale with G = 50; another vendor's 4-terminal part. | `requirements/parts.md` shunts |
| OI-21 | **No accuracy requirement exists.** Range and resolution are specified; accuracy is not. Without it the HIGH-shunt TCR (OI-20), the internal-versus-external reference question (U8; internal drift is 20 ppm/°C max), and the calibration procedure cannot be closed. Proposed: ±0.5 % of reading after per-unit gain calibration. | REQ-MEAS-05 |
| OI-22 | **The ADC has no clock.** ADS131M02 requires an external CLKIN (0.3 – 8.4 MHz in high-resolution mode); Rev0.1 gave it none. P6: 8.000 MHz from an RP2040 GPOUT pin (clk_usb ÷ 6), giving 31.25 kSPS. | Rev0.2 §6.3; ADS131M02 datasheet |

---

## 12. Pre-Order Checklist

- [ ] PCB revision correct; `MANUFACTURING APPROVED` recorded in this file.
- [ ] All Section 11 open issues closed with evidence in Git.
- [ ] Frozen source export committed.
- [ ] ERC critical errors: 0. DRC critical errors: 0. Unrouted nets: 0.
- [ ] Board dimensions and mechanical overlay accepted against the authoritative
      mechanical source.
- [ ] JLCPCB stackup ID recorded; differential impedance computed against it.
- [ ] Mounted components on Top only. Bottom paste apertures: 0.
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
