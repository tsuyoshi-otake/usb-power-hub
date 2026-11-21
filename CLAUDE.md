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

> **Rev0.7 r01 is ORDERED (2026-11-20). Every other release stays WIP, and no further order is
> placed without the user's approval.**
>
> **The tracked board is Rev0.7 (issue #14, D40, 2026-11-19); its release
> `manufacturing/releases/rev0.7/r01/` is in the state `ORDERED`: the user ordered it from JLCPCB and
> paid for it on 2026-11-20, about 00:40 (JST), from JLCONE on another PC (5 boards, 2 assembled;
> `JLCPCB_REVIEW.md` there; approval 「支払いまでやったよ」). Its ten manufacturing files are never
> overwritten: any change is a new release number or a new revision (Section 2). The order went out
> with gates open: JLCDFM never ran on Rev0.7, the stackup JLC04161H-7628 was not named on the order
> ("Specify Stackup" stayed No), the stock was not read on the day, and the open issues of Section 11
> stand. "Confirm Production file" is Yes. The production file was read on 2026-11-20 and is not
> confirmed (`JLCPCB_REVIEW.md` §9): holes, slots and J5 as designed, no stackup named, two tooling
> holes added by JLCPCB, the mask **green** (the user meant black, but JLCPCB takes only green on an Economic 4-layer order, and the user kept green on 2026-11-21). Unconfirmed, it
> goes to production by itself about 2026-11-24 10:00 JST. Nothing has been built or measured.** After the
> user's 「2.54で端にしてねこんなので挟むから。SWD経由で君にデバッグまで自動化して開発したいからさ。」
> (with a picture of two spring-pin clamps), J5, the SWD land, is eight bare pads, 1.7 mm at
> 2.54 mm pitch, 1.6 mm inside the back edge: 1 SWDIO, 3 and 5 GND, 7 SWCLK in the edge row, 2 V3V3,
> 4 RUN, 6 and 8 unconnected in the inner row. The Tag-Connect TC2030-NL land is gone. No mounted
> part changes: the BOM, the CPL and the hand-solder list are Rev0.6 r02's byte for byte. Rev0.6's
> copper is carried (`carry.py`, now from a revision that carried one itself), the tracks at J5 are
> drawn in `ROUTING_Rev0.7.md`, and `check_pcb.py`, `check_routing.py` and `check_silk.py` pass on
> the tracked board. **Not done for Rev0.7:** JLCDFM (never run), the production file's reading, the
> hand-soldered parts' purchase at Akizuki, and the
> clamp itself: it has two rows and eight pins (user, 2026-11-19: 「2 列 8 ピン」; the variant
> "2.54mm Double row 4P" of an AliExpress listing, D40) and is 16.5 mm wide (user, 2026-11-20:
> 「なる程、16.5mm がクランプの横幅」), but its
> drawing is not known, so the pad size, the distance from the edge and the row
> order are estimates until the real clamp is tried on a board; the user does not measure it before
> manufacture (「図らなくていいよ」). At that width the clamp covers C3's courtyard by 0.87 mm
> (D40; `design/mechanical/ENCLOSURE_Rev0.3.md` §10): not settled on paper. The enclosure is drawn
> for this board since 2026-11-20 (Enclosure Rev0.3, with an opening for the clamp), and the lid
> (Lid Rev0.2) is built again from its interface; neither is printed or ordered. Below, every statement about a
> release or a JLCPCB gate is Rev0.6's or older; "Rev0.6" in a sentence
> about placement or routing still describes this board except at J5.
>
> The circuit design exists as a document —
> `design/circuit/CIRCUIT_DESIGN_Rev0.7.md` (redesigned 2026-11-03 under the user's
> sourcing rule D13, then limited to Basic parts only by D22, with three exceptions: the bare
> RP2040 by D29 and the bare CH335F by D31 on 2026-11-04, and the USB-C receptacle by D37 on
> 2026-11-12; Rev0.1–Rev0.5 are in Git history: Rev0.4, the file before D37 and D38, at
> commit `5a697aa`, and Rev0.5, the file before its rename for the layout revision Rev0.6
> (issue #13), at commit `866ef44`) — together with the requirements set in `requirements/`
> (`product.md`, `verification.md`, `parts.md`). There is **no orderable manufacturing output**.
> The board is captured, placed, routed and labelled in KiCad 9.0.8 (D32, issues #6, #8 and
> #10): a generated project in `design/ecad/source/` (4-layer JLC04161H-7628 stackup,
> 100 × 72 mm outline, §5.3 starting rules, the USB_HS net class), written by
> `design/ecad/scripts/make_project.py`. The schematic is captured (P2, D34): six
> sub-sheets and 304 components (294 at D34; D35, issue #7, added J1's soft start; D38 added
> the four 1 kΩ data-line taps R35–R38), every passive bound to a Basic LCSC part, ERC with
> 0 violations. `make_schematic.py` writes it from
> `design/circuit/CIRCUIT_DESIGN_Rev0.7_netlist.md`, and `check_schematic.py` compares the
> exported netlist with that list, with the circuit document's §6.2 and with
> `requirements/parts.md`. The parts are placed (P3): `make_pcb.py` builds the board from
> the exported netlist and `design/ecad/PLACEMENT_Rev0.7.md`, and `check_pcb.py` checks it
> against that document, the capture list's placement notes and DRC. J1–J4 are the SMD
> receptacles C2765186 (D37) on the board's edges, each front face 1.06 mm past the outline,
> mirror-symmetric about x = 50 mm since Rev0.6 (D39): J2 and J3 at x = 17.5 and 82.5 mm on
> the front edge, J4 and J1 at the same x on the back edge. 22 parts around U1 stand
> 0.4–0.8 mm further out than in Rev0.4, so that the router can
> leave the 0.4 mm-pitch pins. The board is routed (P4, D36): `make_pcb.py` adds the tracks, the
> zones and the patch of `design/ecad/ROUTING_Rev0.7.md`, the routing carried from Rev0.5
> (`design/ecad/routing/carried.json`, written by `carry.py`) and the Freerouting session in
> `design/ecad/routing/` (written by `autoroute.py`). `check_routing.py` checks the result
> against that document: DRC with 0 violations and 0 unconnected items, the USB pairs, the
> Kelvin taps, D36's L3/L4 rule, the port-path copper and, new in Rev0.5, the L2 plane (its
> rule 9: no void in it longer than 3.0 mm, and at least half of every side of the exposed
> pads of U1 and U6 kept in plane copper) and the distance between drilled holes (its rule 10:
> a plated slot is a capsule, which KiCad's DRC does not measure). The router knows no antipad, so its vias split the
> plane until the document gave it one (`plane_via`, ROUTING_Rev0.7.md, *Router*); Rev0.4's
> committed board fails the rule, with voids up to 3.65 mm and 0.47 mm of plane beside the
> east side of U1's pad. Rev0.6 moved 31 of the 304 parts (D39) and routed only what they
> touch: Rev0.5's session and patch are carried where they still stand (2,005 track segments
> and 205 vias; 115 dropped), VBUS_B's trunk to J3 and five crossings of pair A's corridor are
> drawn in the document, a new 8-pass session adds 251 segments, and a patch of 42 rows takes
> seven carried tails away and joins the 9 connections the session left open. U1's plane webs
> stay 1.65–1.80 mm against rule 9's 1.60 mm, and port B's copper is 39.12 mΩ of the 40 mΩ
> (port A 35.24 mΩ). Nothing is routed by hand in KiCad. The silkscreen
> labels are placed (P5): `make_pcb.py` adds the table in `PLACEMENT_Rev0.7.md`, *Silkscreen*,
> and `check_silk.py` checks it against JLCPCB's legend limits and CLAUDE.md §6. A candidate
> manufacturing set (P5) is written by `make_outputs.py` into `manufacturing/working/rev0.7/`
> and checked by `check_outputs.py`: Gerber and drill, JLCPCB BOM and CPL, the hand-solder
> list, schematic and assembly PDFs, renders, ERC/DRC reports, and a `WIP` manifest. It is
> not tracked (`.gitignore`), is regenerated byte-identically from the tracked board
> (`make_outputs.py`; `make_pcb.py` is not byte-reproducible in the pours' fill, see
> `design/ecad/README.md`), and is **not orderable**. Rev0.6's release candidate is
> `manufacturing/releases/rev0.6/r02/` (state `WIP`, issue #13): the same ten files with a
> manifest and checksums. It supersedes r01 by its silkscreen alone (user, 2026-11-19, after
> reading the legend in a render: 「直して r02」): 44 labels for 32, three run-together pairs
> parted, `BOOT`, `SWD` and J5's pad names added, and the references of the eight hand-soldered
> parts shown. Of the Gerber zip's 15 members only the top legend differs from r01's, and the
> BOM, the CPL and the hand-solder list are r01's byte for byte. **JLCPCB has not seen r02's
> Gerber zip, and the user's JLCPCB cart of 2026-11-19 holds r01's files.** What follows is
> r01's gate. The JLCPCB gate ran on r01 on 2026-11-19 (its `JLCPCB_REVIEW.md`;
> **nothing ordered, nothing paid**, no approval): part mapping 41 of 41 with 0 substituted, the
> placement preview (the four receptacles and every moved part that is not symmetrical), JLCDFM
> with each Danger item judged against measurements on the board, and a quote of $52.85 without
> shipping. It changed no file and left three findings to the user: a GND via carried from
> Rev0.5's routing stands 0.059 mm from pad 3 of D1 (one net), JLCDFM lists the non-plated drill
> file as plated, and the receptacles' slots are 0.60 mm wide. On 2026-11-19 the user accepted the
> first as it is (「受け入れる」) and kept the slots at 0.60 mm (「このまま」); the drill-file
> finding waits for the order. The review holds only for the files whose
> SHA-256 it records. The candidate before it is Rev0.5's,
> `manufacturing/releases/rev0.5/r02/` (state `WIP`,
> **nothing ordered, nothing paid**, no approval), with its manifest, checksums and the gate's
> `JLCPCB_REVIEW.md`; r01 beside it is superseded and keeps the stock check of the shared BOM
> (`SOURCING_CHECK.md`, 2026-11-13). The JLCPCB gate ran on Rev0.5 on 2026-11-13 (issues #8 and
> #10), on r01's files, and found two defects: JLCPCB's model of the receptacle sat 1.375 mm off
> the CPL point (fixed by the per-part `shift` of `design/ecad/jlcpcb_model_frame.json`, which
> held rotations only as `jlcpcb_model_rotation.json`), and eight vias stood 0.046 mm from the
> receptacles' plated slots (fixed in r02). It read part mapping (41 of 41, 0 substituted),
> the placement preview per part class, JLCDFM (each Danger item judged; the receptacles' 0.60
> mm slot width was left to the user, who kept it on 2026-11-19, at Rev0.6's gate) and a quote of
> $51.94 without shipping, and it holds
> only for the files whose SHA-256 the review records. The gate ran on
> Rev0.4 (issue #6, 2026-11-11/12): JLCDFM, part mapping (40 of 40, 0 substituted), the
> placement preview read per part class, a quote of $81.85 without shipping, and, with every
> via drilled at 0.30 mm (issue #8, r02), $47.69. Those reviews and the blocked EasyEDA
> import (`EASYEDA_IMPORT.md`, D32) are in `manufacturing/releases/rev0.4/`, whose r01 and r02
> Rev0.5 supersedes; its BOM, CPL and copper differ, so none of that evidence carries over,
> except what the gate found in the generator: BOM rows sharing an LCSC code, the Gerber
> origin against the CPL's, and the JLCPCB model rotation, fixed in Rev0.4 and kept.
> `design/ecad/README.md` gives the order to run the generators in. The project
> library exists (P1): a symbol and a footprint for every Rev0.7 part in
> `design/ecad/libraries/`, each land measured by `check_libraries.py` against the
> datasheet numbers recorded in `library.json`. Candidate parts have been looked up in the JLCPCB
> assembly pool and at Akizuki (`requirements/parts.md`, dated stock), but **none
> is confirmed**:
> no footprint is proven on a board, and the stock check of 2026-11-13 is repeated at order
> time. Nothing has been built or measured.
>
> The other thing that exists is a three.js appearance mockup
> (`mockup/`). Component names such as `U2_usb_hub` in it are placeholders, not
> procurement specifications, and D10/D24 (100 × 72 mm, 4 layers) supersede its
> outline and layer count. Section 11 lists the blocking issues.
>
> The enclosure is a first design on paper (issue #11, 2026-11-13; Rev0.2 for the Rev0.6
> board, issue #13, 2026-11-19; Rev0.3 for the Rev0.7 board, issue #14, 2026-11-20):
> `design/mechanical/ENCLOSURE_Rev0.3.md`, a printed tray and frame under a PCB lid,
> 104.8 × 76.8 × 27.7 mm, with its decisions E1–E10 (Claude, delegated). Rev0.2 followed the
> mirror-symmetric connectors (D39) and starts each button's column 11.0 mm above the board,
> over the MAU104 that now stands beside SW2 (E8 as amended); Rev0.1's tower stood inside that
> part's courtyard. Rev0.3 adds an opening for the SWD clamp (E10), 18.0 mm wide and centred on
> J5, through the back wall of tray and frame up to 12.0 mm above the board and through the
> tray's floor 8.0 mm inside the edge; of the clamp only the width is known, so its reach and
> height there are estimates. Its STL files, the
> lid PCB's interface and seven pictures are generated from that document and from the
> board's interface (`design/mechanical/reference/`, exported from the tracked KiCad board) by
> `make_enclosure.py`, and checked by `check_enclosure.py` (`design/mechanical/README.md`).
> **Nothing is printed and no cable has been tried in an opening**;
> 20 of the 24 part heights it clears are assumed. The print process is FDM (user,
> 2026-11-18; Section 7); its material is not chosen. OI-1 and OI-5 stay open.
>
> The lid PCB is drawn (issue #11, 2026-11-18, after the user's 「作図する」; built again on
> 2026-11-20 from Enclosure Rev0.3's interface, the same board but for its title block; Lid Rev0.2 for
> the Rev0.6 board, issue #13, 2026-11-19: its holes, window and port labels follow the
> enclosure's interface to the mirrored places, and no parameter of its own changed):
> `design/mechanical/LID_Rev0.2.md`, a bare 2-layer board with the main board's outline, no
> part and no net, with its decisions K1–K8 (Claude, delegated). `make_lid.py` writes the
> KiCad board in `design/mechanical/lid/` from that document and the enclosure's lid
> interface, `check_lid.py` checks it (L01–L16), and `make_lid_outputs.py` writes an untracked
> candidate set into `manufacturing/working/lid-rev0.2/`. **It is not ordered, it has no
> release, JLCPCB has not seen its files, and the user has not seen its legend on a board.**
>
> The repository is under Git since 2026-11-03 (commit `4dd10fb` is the design
> as it was paused on 2026-08-16). Its one remote, `origin`, is the **private**
> GitHub repository `tsuyoshi-otake/usb-power-hub`, created on 2026-11-03 at the
> user's request 「一旦コミットプッシュしちゃいなよ」. Section 2 asks that it stay private. **On 2026-11-20 `gh repo view` reports it PUBLIC** (it was PRIVATE at the push of that day, about 00:35 JST); the user set it and keeps it public (「publicに変更」), under the MIT licence since that day. Its history carries the committer's e-mail address.

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
  - JLCPCB machine-places the SMD parts, on Top only, the RP2040 MCU with its flash and
    crystal (D29), the CH335F hub (D31) and the four USB-C receptacles (D37) included.
  - The user hand-solders the large Akizuki parts (the MAU104, two DIP16 ADCs, the
    shunts R_H and R_M, the fuse F1); through-hole pins are soldered from Bottom.
  - No part body on Bottom; Bottom is copper, vias and mask.
- USB-C receptacles ×4, SMD with plated shell slots, C2765186 (D37; Akizuki modules on
  PH-1x40SG headers until Rev0.4): host data and logic power (J1), a power-only 5 V input
  (J4), and 2 switched downstream ports (J2, J3). Four RP2040 GPIO tap the D+ and D− of J2
  and J3 through 1 kΩ for a Low-Speed and Full-Speed capture (D38, issue #10).
- No USB-PD. Port power is J4's own 5 V, unregulated (D14).
- Precision current measurement, **0.1 µA – 1 A**: 3-range shunt ladder with
  hardware up-ranging, discrete current-mirror amplifiers, and two 12-bit
  MCP3208 ADCs (one per channel), two independent channels sampled together.
- Enumerates as a **CDC-ACM COM port** on the upstream PC; driverless control.
- Sourcing rule D13: JLCPCB **Basic** parts for PCBA, **Akizuki** parts for
  hand soldering, never an Extended-only PCBA; JLCPCB PCB/PCBA services.
  D22 (user) excludes Preferred Extended parts too. D29, D31 and D37 (user) admit three
  Extended parts, the RP2040 (C2040), the CH335F (C5137013) and the USB-C receptacle
  (C2765186).
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
│  ├─ ecad/                     # captured schematic + PCB (KiCad until the EasyEDA import, D32)
│  │  ├─ scripts/               #   generators and checks run with KiCad's Python
│  │  ├─ source/                #   the KiCad project (source of truth, D32)
│  │  ├─ libraries/             #   project-only symbols and footprints
│  │  ├─ previews/              #   2D/3D and vendor placement previews
│  │  └─ reports/               #   ERC, DRC, unrouted-net output
│  ├─ mechanical/               # ENCLOSURE_Rev<X.Y>.md, LID_Rev<X.Y>.md — the enclosure and
│  │  │                         #   its lid PCB, as documents
│  │  ├─ scripts/               #   generators and checks: the enclosure's run with the CAD
│  │  │                         #   venv's Python, the lid's with KiCad's
│  │  ├─ reference/             #   authoritative outline and connector geometry
│  │  ├─ assembly/              #   enclosure CAD, the lid PCB's interface, fit studies
│  │  ├─ lid/                   #   the lid PCB's KiCad project (generated, never edited)
│  │  └─ reports/               #   pictures of the generated enclosure
│  └─ experiments/              # non-authoritative trials
├─ firmware/                    # RP2040 (bare chip, D29) — src/ include/ tests/ tools/ reports/
├─ host/
│  └─ profiler/                 # PC software: native Win32 Rust current profiler (issue #9)
├─ manufacturing/
│  ├─ working/                  # disposable candidate exports — never orderable
│  └─ releases/<rev>/<rNN>/     # immutable approved or ordered releases
├─ tests/                       # fixtures/ reports/ — physical test evidence
├─ docs/
│  └─ decisions/                # one file per closed architectural decision (until
│                               #   created, decisions D1–D40 live in circuit §10)
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
- The remote repository is public by the user's decision of 2026-11-20 (「publicに変更」), under the MIT
  licence (`LICENSE`; 「LICENSEはMITでいいよ」). No account data, credential or address goes into it.

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
  did not order it for the prototype: the D± path also ran through modules
  and headers that it could not control (OI-26), and FS is the fallback. D37 removed the
  modules and headers, which reopens the question; the user decides it at the JLCPCB step
  with a fresh quote (circuit §9).

Layer assignment (4 layers, D10): L1 signal + parts / L2 solid GND / L3 power
pours + low-speed signals / L4 GND + low-speed. **L2 MUST remain unbroken under
every USB pair**, and every L1 USB pair references L2 only. L3 signals that cross
under the analog block or a USB pair need a GND reference on L4 directly below.
In the analog blocks an L3 and an L4 signal may cross at 45° or more, but never run
along each other (D36, user, 2026-11-06); a crossing has a signal, not GND, below it
for the crossing's width. Confirm against the chosen JLCPCB 4-layer stackup before routing (Section 5.1).

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
| Via diameter / drill | 0.45 / 0.30 mm (0.60 / 0.30 mm where space allows): JLCPCB's standard via class "0.3mm/(0.4/0.45mm)". A 0.25 mm drill puts the order in the "0.25mm/(0.35/0.4mm)" class, which adds a 4-Wire Kelvin Test and a minimum-via fee ($34.16 on r01's quote, issue #8) |
| Copper to routed edge | ≥ 0.30 mm |
| Silkscreen text height | ≥ 1.0 mm Latin (see Section 6) |
| Silkscreen stroke | ≥ 0.15 mm |

USB 2.0 high-speed:

- Route each pair as a length-matched, tightly-coupled differential pair on one
  layer where practical.
- **Never split the reference plane under a pair.** Stitch GND at every layer
  transition near the pair.
- Keep pairs away from the MAU104, the shunt ladder, and LED drive.
- No stubs, except the four 1 kΩ data-line taps of D38 (issue #10), each a stub of one resistor
  pad. No test points on the pairs.

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
  (Rev0.7 §3.1, G7).
- Range switching MUST be verified for both settling time and over-range
  survival. The architecture is fixed by D9/D17 (Rev0.7 §10). What is *not* yet
  established is that a built board meets the ≤ 3 µs-per-stage ranging budget,
  holds the new range within 100 µs, and survives a stuck range. These are
  bring-up measurements, not review items.
- The bypass FETs' R<sub>DS(on)</sub> MUST stay outside the sensed span. Its
  temperature coefficient is ~4000 ppm/°C against a ±100 ppm/°C shunt. Topology C
  guarantees this, because each amplifier senses only its own shunt (Rev0.7 §5).
- Zero-point calibration is a **functional requirement**, not a feature. Without
  it, the OP07 offset and the deliberate pedestal current that keeps the current
  mirror out of its dead zone (Rev0.7 §4.1) put up to 8 LSB (LOW, MID) or 13 LSB (HIGH)
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
  authoritative; the three.js mockup is not it. It is
  `design/mechanical/reference/board_interface_Rev0.7.json`, written from the tracked
  KiCad board by `design/mechanical/scripts/export_board_interface.py` (issue #11; exported
  again from the Rev0.6 board, issue #13, and from the Rev0.7 board, issue #14).
- Connector openings MUST clear the **mating plug's overmold**, not just the
  receptacle shell. Verify against a real cable, not a datasheet outline.
- Fastener bosses MUST give at least 2 × D thread engagement (≥ 4 mm for M2),
  or use heat-set inserts. See OI-5.
- Fit the board on ≥ 3 mounting points, with at least one near each connector
  end. Repeated insertion force must not be carried by the solder joints.
- Print process (FDM / MJF) MUST be chosen before wall and clearance values are
  frozen; they differ. **Chosen: FDM** (user, 2026-11-18: the choice 「FDM」;
  `design/mechanical/ENCLOSURE_Rev0.3.md` E2). The enclosure's values were drawn for it and
  stay provisional until the first print.
- The lid PCB is a manufactured board and follows every rule in this file:
  own revision, own Gerber set, own release entry. It is Lid Rev0.2
  (`design/mechanical/LID_Rev0.2.md`, state `WIP`, no release), drawn from the enclosure's
  lid interface and from nothing else. Lid Rev0.1, for the Rev0.5 board, was never ordered.

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

The finish is **leaded HASL** (D30, user, 2026-11-04), not ENIG. HASL is not flat: U1 and U6,
the 0.4 mm-pitch RP2040 and CH335F QFNs with ePads (D29, D31), are the parts it puts at
risk, and V-MFG-03 inspects their joints on the first boards. Recheck
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

**Superseded by `design/circuit/CIRCUIT_DESIGN_Rev0.7.md` §6.2, which is the
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

- Board thickness 1.6 mm, leaded HASL (D30; ENIG until then). **Outline 100 × 72 mm, 4 layers (D10, D24),** inside
  100 × 100 mm. Stackup JLC04161H-7628, no impedance control for the prototype (D27).
  JLCPCB machine-places Top SMD only; the large Akizuki parts are hand-soldered
  (D13, REQ-MFG-01).
- **Sourcing (D13, user):** machine-placed parts are JLCPCB Basic and in stock;
  hand-soldered parts are in stock at Akizuki; never an Extended-only PCBA
  (REQ-MFG-05). Avoid special or hard-to-source parts; keep part types and count low.
  Preferred Extended parts are excluded too (D22, user). Three exceptions, all Extended and
  all the user's: the RP2040, C2040 (D29), the CH335F, C5137013 (D31) and the USB-C
  receptacle, C2765186 (D37); a fourth one needs the user's decision.
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

Recorded in `design/circuit/CIRCUIT_DESIGN_Rev0.7.md` Section 10 (D1–D40; D12 is
withdrawn and not reused).

- **User decisions:** KiCad (D2), CDC-ACM ×2 (D7), 4 layers (D10), the outline limit of
  100 × 100 mm (D24, 「100x100未満ならいいんだっけ」),
  the sourcing rule (D13), and Basic parts only, with no Preferred Extended (D22,
  「外して Basic のみにする」), and no pre-layout bench: desk checks now, the first board
  confirms (D28, 2026-11-04, 「試験キットは買わない、基板で確かめる。君が机上で確認すればいい」),
  and the bare RP2040 (C2040) as the first Extended part, machine-placed, replacing D23's
  PGA2040 module (D29, 2026-11-04: 「このPGAてさ生のRP2040より高くない?」,
  「いいよ、大きな設計変更になってもいいよ」, and the choice 「素の RP2040 (推奨)」),
  and leaded HASL instead of ENIG (D30, 2026-11-04: 「ENIGいらないよ、」, then the choice
  「有鉛 HASL (推奨)」), and the bare CH335F (C5137013) as the second Extended part,
  machine-placed, replacing D15's Akizuki module (D31, 2026-11-04:
  「ええ、CH335FはLCSCに在庫無いの?」, 「こんなモジュール実装するのデカくない?」, and the
  choice 「IC 単体にする (推奨)」), and the ECAD workflow, amending D2: capture and lay out
  in KiCad 9.0.8 until the design is complete, then import into EasyEDA (D32, 2026-11-04:
  「いったんローカルでKiCadで完成まで目指してそのご、EasyEDAにインポートしよう」), and J1's
  soft start, an AO3401A between J1's VBUS and V5L, whose values Claude set (D35, 2026-11-04:
  「OKお願いします」, accepting the recommended fix for OI-32), and L3/L4 crossings in the
  analog blocks (D36, 2026-11-06: the choice 「交差のみ許可 (推奨)」, after the router left
  76–78 connections unrouted with L4 closed there), and the USB-C receptacle C2765186 as the
  third Extended part, machine-placed, replacing the four Akizuki modules and their headers
  (D37, 2026-11-12: the cost request 「安価に製造できないとね、製造コストを下げて」 and the
  choice 「USB-C直付けのみ (推奨)」, then 「GND パッドを 0.035 mm 短く (推奨)」 for its land),
  and the data-line taps (D38, 2026-11-12: 「可能ならデータ線部分もロジックアナライズできると
  USB接続機器を開発するのに便利なんだけど、出来る?」; the circuit is Claude's),
  and the mirror-symmetric connectors, a layout revision, Rev0.6 (D39, issue #13: looking at the lid
  PCB's legend, 「なんかUSBの位置がアシンメトリーで変だね」, the choices 「再配置を検討」 and
  「C2 を試し配置」 on 2026-11-18, and after the trial 「C2 で進める」 on 2026-11-19; Claude had
  recommended keeping Rev0.5's positions), and the SWD land at 2.54 mm at the board edge, for a
  spring-pin clamp, a new revision, Rev0.7 (D40, issue #14, 2026-11-19:
  「このボードへの書き込みってどこ?2.54ピッチで4x2?」, then, with a picture of two clamps,
  「2.54で端にしてねこんなので挟むから。SWD経由で君にデバッグまで自動化して開発したいからさ。」; the
  pitch and the place are the user's, the land of 2 × 4 pads and its pin order are Claude's).
  D1 (PD sink) and D11 (USB2514B) were also user decisions; both are superseded because
  their parts are Extended.
- **Under the delegation:** on 2026-11-03 the user delegated the open choices
  (「推奨で任せるよ」). Claude recorded D14–D21: J4 power input, CH335F hub
  (on the Akizuki module until D31), topology C with current mirrors, the port path, the clocks, the accuracy target,
  and the adoption of P9–P12. After D22, Claude recorded D23: the PGA2040 RP2040
  module and two MCP3208 ADCs, superseding D16's STM32F103 (D29 has since replaced the
  module with the bare RP2040; D23's ADC choice stands). Within D24's limit, Claude
  chose the 100 × 72 mm outline from the OI-23 study, and D25 put the MF-R300 input fuse
  on J4 (OI-29), and D26 set how J1's current is declared (OI-25). D27 named the
  JLC04161H-7628 stackup and the provisional USB pair geometry, without impedance
  control for the prototype. D33 chose the module headers, PH-1x40SG soldered without
  sockets (OI-23; superseded for the USB-C modules by D37). D34 set the values left to capture (issue #6 P2); its desk check moved
  the LM393s to V12F and Q13's gate behind 100 kΩ, and widened the OC trip tolerance to
  1.110–1.221 A. Each is labelled
  "Claude (delegated)", and the user may revert any one.

### 10.5 Still undecided — record the decision before layout starts

- USB VID/PID. Do not ship a squatted VID.
- Whether the mockup's placement is kept at all. Assume not.

---

## 11. Open Issues

OI-1 – OI-15 were found by review of the mockup on 2026-08-16; OI-16 – OI-22 by the
review that produced Rev0.2 on 2026-11-03; OI-23 – OI-30 by the Rev0.3 redesign under
the sourcing rule D13 (2026-11-03); OI-31 by the Rev0.4 change to Basic parts only
(D22, 2026-11-03); OI-32 by the capture (issue #6 P2, 2026-11-04); OI-33 by the receptacle's
library capture (issue #8, 2026-11-12). Every issue not struck through is **blocking**.
Numbers are stable; close them in Git with evidence, do not renumber.

- "Closed by decision" means the design intent is settled but nothing is built or
  measured. Reopen the issue if the built board disagrees.
- A decision marked "Claude (delegated)" was made under the user's 2026-11-03 delegation,
  and the user may revert it.
- "Rev0.7 §n" refers to `design/circuit/CIRCUIT_DESIGN_Rev0.7.md`. Rev0.3, Rev0.4,
  Rev0.5, Rev0.6 and Rev0.7 share their section numbers.
- The Rev0.2 text is at commit `4e59607`:
  `git show 4e59607:design/circuit/CIRCUIT_DESIGN_Rev0.2.md`.
- The Rev0.3 text is at commit `4e43692`:
  `git show 4e43692:design/circuit/CIRCUIT_DESIGN_Rev0.3.md`.
- The Rev0.4 text is at commit `5a697aa`:
  `git show 5a697aa:design/circuit/CIRCUIT_DESIGN_Rev0.4.md`.
- The Rev0.6 text is at commit `ebc4fdb`:
  `git show ebc4fdb:design/circuit/CIRCUIT_DESIGN_Rev0.6.md`.
- The Rev0.5 text is at commit `866ef44`:
  `git show 866ef44:design/circuit/CIRCUIT_DESIGN_Rev0.5.md`.

| ID | Issue | Evidence |
|---|---|---|
| OI-1 | **Two USB-C plugs cannot be inserted at once.** The mockup's downstream pitch is 10.8 mm; plug overmolds are 12–14 mm. *Rev0.3:* J2/J3 are 20 mm-wide Akizuki modules placed side by side, so the pitch is ≥ 20 mm (D21, REQ-MECH-02). *Rev0.5 (D37):* J2 and J3 are 8.94 mm receptacles, 33.8 mm apart. *Rev0.6 (D39):* 65.0 mm apart. *Enclosure Rev0.1 (issue #11), Rev0.2 (issue #13) and Rev0.3 (issue #14, for the Rev0.7 board):* each opening has a 15.0 × 8.0 mm pocket for the plug's overmould, on paper. Open until checked with real cables (V-MECH-01). | `PORT_Z = 5.4` in the mockup; Rev0.7 §10 D21, D37, D39; `design/mechanical/ENCLOSURE_Rev0.3.md` E6 |
| OI-2 | ~~No crystal for the USB hub.~~ **Closed by decision** (D19, Claude delegated, 2026-11-03): a 12 MHz Basic crystal (C9002), Y2 → CH335F. D23 removed Y1 (→ STM32 HSE) because the MCU module carried its own crystal; D29 restored Y1, the same C9002, → RP2040 XOSC, checked on the first board (V-MEAS-06). The history: D6's shared oscillator was superseded by D11; the USB2514B (24 MHz) was itself superseded by D13. Y2 against CH335F's built-in load capacitors is checked at bring-up (G9). | Rev0.7 §6.3 |
| OI-3 | ~~Range switching unimplementable.~~ **Closed by decision** (D9/D17): ranges 0.1 Ω / 10 Ω / 510 Ω in a nested bypass ladder, LM393 up-ranging ≤ 3 µs per stage, firmware hold ≤ 100 µs, bypass default ON. Bring-up proves the budget (V-MEAS-02). | Rev0.7 §3.2, §4 |
| OI-4 | ~~Power budget contradicts the spec.~~ **Closed by decision** (D14): D1's PD sink is superseded; port power comes from J4, a power-only 5 V input. Its USB-C advertisement drives the advertisement and budget rules (REQ-PWR-04/05). | Rev0.7 §3.1, §7.2 |
| OI-5 | **Fastening will not survive use.** 2 × M2 at one end only, 1.6 mm thread engagement (want ≥ 4 mm), and the PCB itself is not clamped. *Rev0.3:* heat-set M2 inserts at 4 corners adopted (D21). *Rev0.5 (D37):* the plug's force enters the PCB through each receptacle's four shell slots, read in V-MECH-01 with OI-33. *Enclosure Rev0.1 (issue #11), Rev0.2 (issue #13) and Rev0.3 (issue #14, for the Rev0.7 board):* on paper, four bosses and posts clamp the board at H1–H4, the screws go into heat-set inserts (3.10 mm and 3.40 mm of thread), and a rib stands under each receptacle; on Rev0.6 every receptacle stands 14.0 mm from a screw (OUT B stood 45.2 mm from one). Open until built and checked (V-MECH-01). | boss height = `GAP` = 1.6; `design/mechanical/ENCLOSURE_Rev0.3.md` E4, E7 |
| OI-6 | **Silkscreen below fab minimum.** Reference designators 0.80 mm; user-facing kanji 0.81 mm. *Lid Rev0.1 (issue #11) and Rev0.2 (issue #13):* the user-facing panel is the lid PCB, and its legend is Latin, 1.0–3.0 mm high, on paper (`check_lid.py` L07, L09, L10). Open until a legend is seen on a manufactured board. | canvas px/mm scale; `design/mechanical/LID_Rev0.2.md` §5 |
| OI-7 | ~~Protection incomplete.~~ **Closed by decision** (D18), with two residuals moved to their own issues. ESD: PSM712 on the CC pins of J1–J4; D+/D− of J1–J3 are unprotected since D22 removed SRV05-4 (product.md §9). TVS: SMBJ6.5CA on the J1 and J4 VBUS. Reverse blocking: back-to-back AO3401A. No TVS on VBUS_A/B, by design: its leakage would be measured, and the port capacitor absorbs ESD. No common-mode choke: not needed for USB 2.0, and none is Basic. Residual: the J4 fuse (OI-29, closed by D25). SRV05-4's class (OI-30) ended with its removal (D22). | Rev0.7 §3.1, §3.4, G10 |
| OI-8 | **Not testable.** Zero fiducials for 0201 placement; no panelization defined; SWD pads have no fixture datums. *Rev0.3:* TC2030-NL SWD footprint and test pads adopted (D21, REQ-MFG-03/04). *Rev0.7 (D40, issue #14):* the SWD land is eight bare pads at 2.54 mm, 1.6 mm inside the back edge, for a spring-pin clamp whose jaw takes the board edge as its datum; the clamp's drawing is not known and its fit is not tried; it is 16.5 mm wide (user, 2026-11-20), and Enclosure Rev0.3 has an opening for it (E10). Panelization still undefined. | Rev0.7 §10 D40; `design/ecad/libraries/library.json` (SWD-PADS-2x4) |
| OI-9 | ~~BOOTSEL unreachable with the lid fitted.~~ **Closed by decision** (D21 as amended by D23 and D29): the RP2040 ROM USB bootloader (UF2 drive), entered by `BOOT` or by SW3 through a lid pinhole (SW3 pulls QSPI_SS low through 1 kΩ, D29). It is in mask ROM, so no firmware state removes it; SWD is for debug only. Reopen if V-BOOT-01 fails. | REQ-BOOT-02 |
| OI-10 | ~~6 layers may be unjustified.~~ **Closed by decision** (D10, user, 2026-11-03): 4 layers. Reopen if signal-integrity or EMC review of the routed board disagrees. | Rev0.7 §10 |
| OI-11 | ~~Shunts are 2-terminal.~~ **Closed by decision** (D17, topology C): each shunt has its own amplifier and Kelvin connection. R_H is a 2-terminal chip on a 4-pad land; R_M has its sense taken at each lead pad; R_L is 0805. No FET R<sub>DS(on)</sub> is inside a sensed span. | Rev0.7 §3.2, §5, G2 |
| OI-12 | ~~Documentation disagrees with itself.~~ **Closed 2026-11-03:** the mockup's `<title>` and caption now state the 60 × 24 mm its model actually has, and that the mockup is superseded by D10 (now D24). | `mockup/usb-power-hub-board.html` |
| OI-13 | ~~Board area — 60 × 24 mm is not routable (75 % density).~~ **Closed by decision** (D10, user, 2026-11-03): **85 × 35 mm, 4 layers**. Every mockup dimension and the enclosure model are invalidated by it. The module-heavy part mix of Rev0.3 and Rev0.4 did not fit, so D24 enlarged the outline to **100 × 72 mm** (OI-23). | Rev0.7 §10, §11 |
| OI-14 | ~~Sample rate capped by the host interface.~~ **Closed by decision** (D17 as amended by D23): the rate is 14.0 kSPS per channel, set by two MCP3208 at a 1 MHz clock with a stretched sample phase, and the stream uses 5.9 % of Full-Speed bulk. Faster profiling would need a faster ADC: that is a new decision, not a defect. | Rev0.7 §3.3 |
| OI-15 | ~~The repository is not under version control.~~ **Closed 2026-11-03:** `usb-power-hub` is its own Git repository on branch `main` (no remote then; a private one was added later that day, §0); commit `4dd10fb` is the unmodified snapshot of the design as it was paused. | `git log` |
| OI-16 | ~~Downstream current policy is undefined.~~ **Closed by decision** (D18): each port advertises Default (Rp 33 kΩ, 500 mA). A port is enabled only while J4's advertisement covers all ON ports. Measured over-budget opens the larger port (`FAULT:BUDGET`). Hardware OC trips at 1.16 A. | Rev0.7 §7.2; REQ-PWR-04/05 |
| OI-17 | ~~The 9 V request (D1) assumes an upstream that may not exist.~~ **Closed by decision** (D14): no PD; port power comes from J4, so it no longer depends on the host PC. The cost is a second cable and an unregulated port voltage (product.md §9). | Rev0.7 §3.1 |
| OI-18 | ~~The 3.3 V rails as drawn overheat.~~ **Closed by decision** (D14): AMS1117-3.3 (SOT-223) from J1 5 V dissipates 0.079 W, a 7 °C rise (47 mA in Rev0.4). The op-amps run from the MAU104, not from a 3.3 V rail. | Rev0.7 §7.1 |
| OI-19 | ~~Sense topology D5 needs re-evaluation.~~ **Closed by decision** (D17): topology C, with discrete OP07CDR + AO3401A current mirrors. No mux and no current-sense amplifier is Basic. | Rev0.7 §5 |
| OI-20 | ~~No stocked HIGH shunt meets the specification.~~ **Closed by decision** (D17/D20): R_H = 0.1 Ω ±0.5 % ±100 ppm/°C KOA TSL1TTER100D (Akizuki, 374 pcs), inside the ±1 % budget. The Basic 0.1 Ω part (±800 ppm/°C) is rejected. | Rev0.7 §4.2; `requirements/parts.md` |
| OI-21 | ~~No accuracy requirement exists.~~ **Closed by decision** (D20): ±(1 % of reading + 3 LSB of the active range) within ±10 °C of calibration, after gain and zero calibration. | REQ-MEAS-05; Rev0.7 §4.2 |
| OI-22 | ~~The ADC has no clock.~~ **Closed by decision** (D23, replacing D17's on-chip ADC): two external MCP3208, clocked at 1 MHz by the RP2040 PIO. | Rev0.7 §3.3 |
| OI-23 | ~~Board fit: area settled, header height not chosen.~~ **Closed by decision** (D24 for the area; D33, Claude delegated, 2026-11-04, for the header). *D37 (2026-11-12) removed the four USB-C modules and their headers: what follows is the record of Rev0.4, and the study is kept, not re-run.* PH-1x40SG headers, soldered, insulator ≥ 2.30 mm, leaving ≥ 0.80 mm above a 1.5 mm part under a module. The study (`design/experiments/oi-23-placement/`, 21 tests, exits 0) now reads the space under each USB-C module from the module and receptacle drawings. Its area bound credits each module's outline less its header insulators: at K = 1.0 (no routing space) 2,931 mm², 1.5 % under 85 × 35 mm (2,975 mm²), which it exceeds from K = 1.025, so 85 × 35 mm stays excluded for any routable layout. The pre-D33 figure, 3,332 mm² at K = 1.0, credited only 130 mm² per module and was not a lower bound. At 100 × 72 mm the block placement passes every check at K = 1.6 (headroom to K = 1.74), with the under-module parts in one 19.0 × 3.4 mm strip per module, clear of the receptacle. Not settled on paper: the module board's thickness and the receptacle's 1.06 mm overhang (V-MECH-01). Reopen if V-MECH-01 fails. | Rev0.7 §10 D33, §11; study README |
| OI-24 | ~~CH335F module outline and pin map unknown.~~ **Closed by decision** (D31, user, 2026-11-04): the Akizuki module (AE-QFN28-DIP(CH335F)), for which Akizuki published no drawing, is replaced by the bare CH335F (C5137013), machine-placed. Its package drawing (QFN28_4X4X0.75-0.4, §5.6) and pin table are in the WCH CH334/335 datasheet V2.5; U6's land is drawn from that drawing before layout (G21). D28 had left the module to be measured before layout. Reopen if D31 is reverted. | Rev0.7 §6.6, §10 D31; `requirements/parts.md` U6 |
| OI-25 | ~~J1 current is misdeclared.~~ **Closed by decision** (D26, Claude delegated, 2026-11-03): the CH335F stays self-powered at its default 100 mA, and the RP2040 function declares bMaxPower 200 mA. That covers its 127 mA typical share of J1's ≈ 0.21 A (192 mA with every OP07 and LM393 at its maximum, since D34). USB still charges the upstream port only 100 mA, so the board is specified for 500 mA upstream ports and not for bus-powered hubs. Options (a) and (b) are recorded as rejected in D26. Reopen if V-HOST-01 measures more than 0.30 A from J1. | Rev0.7 §7.1, §10 |
| OI-26 | **HS signal integrity through the receptacle land is unverified.** Each HS path ends at the pads of a USB-C receptacle on this board (J1 upstream, J2 or J3 downstream), through a hop of D− and a branch of D+ that join its alternating pads, and the paths of J2 and J3 carry the stubs of the D38 taps. Until D37 each path crossed an Akizuki USB-C module and its 2.54 mm headers; since D31 the hub itself is on the board. The fallback is that DUTs enumerate at FS, and the taps are removable. | Rev0.7 §3.3; V-HOST-01 |
| OI-27 | ~~OP07 single-supply operation is extrapolated.~~ **Closed by decision** (D28, user, 2026-11-04): no bench; desk-checked, and the first board confirms. TI SLOS099F specifies the gain on a single 15 V supply with the output at 1.4–11.4 V into ≥ 500 kΩ, so the gate headroom at 1 A is 1.63–1.96 V (it was read as 0.03–0.36 V against a 3.0 V limit). The 4.4–5.25 V common mode sits ≥ 4.40 V from V− and ≥ 5.28 V from V+ (D34), wider than the specified ±15 V and ±3 V conditions. Loop stability into the 645 pF gate is not settled on paper and is accepted as bring-up risk. Reopen if V-MEAS-00 fails at bring-up. | Rev0.7 §3.2, §10 D28 |
| OI-28 | ~~R_M short-time overload is unverified.~~ **Closed by decision** (D28, user, 2026-11-04): the Faithful Link MFU datasheet rates it for 2.5 × RCWV for 5 s (6.25 W, ΔR ≤ 1 %) and for 4 × RCWV pulses (16 W, 1 s on / 25 s off, 10,000 cycles). The stuck-MID fault puts 2.35 W in it for ≤ 10 ms, or until the watchdog fires (timeout ≤ 5 s). Its < 0.1 % shift after the fault is checked on the first board. Reopen if V-MEAS-00 fails at bring-up. | Rev0.7 §4, §10 D28 |
| OI-29 | ~~No input fuse on J4.~~ **Closed by decision** (D25, Claude delegated, 2026-11-03): F1 = Bourns MF-R300 (Akizuki g112630; 3.00 A hold, 2.49 A at 40 °C; 6.00 A trip; 30 V), ahead of the J4 TVS. Its 0.08 Ω (R1max) costs up to 0.16 V at 2 A, which moves into OI-27 and V-MEAS-00. No fuse or PTC is Basic, so it is hand-soldered. Reopen if V-SAFE-02 fails. | Rev0.7 §3.1, §7.2; `requirements/parts.md` |
| OI-30 | ~~Two Preferred Extended parts need the user's decision.~~ **Closed by decision** (D22, user, 2026-11-03): Basic parts only. STM32F103C8T6 (C8734) and SRV05-4 (C7420376) are removed; D23 replaces the MCU with the PGA2040 and two MCP3208, and D± of J1–J3 lose their ESD protection. D29 (user, 2026-11-04) has since replaced the PGA2040 with the bare RP2040, one of the two Extended parts (the other is D31's CH335F). | Rev0.7 §9, §10 D22/D23 |
| OI-31 | ~~PGA2040 and MCP3208 assumptions unverified.~~ **Closed by decision** (D28, user, 2026-11-04), from Pimoroni's schematic and the datasheets. The supply input is the VBUS pad, 3.0–5.5 V, into an on-module NCP115; on V3V3 it leaves ≥ 3.208 V on the 3V3 pad, above the RP2040's 3.135 V USB_VDD minimum. The 27 Ω pair is on the module. The W25Q64JVXGIQ flash has a 64-bit unique ID (4Bh). The RP2040 resets its GPIO with a 50–80 kΩ pull-down, against which the 10 kΩ hold pull-ups give ≥ 2.70 V, above the 2N7002's 2.5 V maximum threshold. Not settled on paper and accepted as bring-up risk: the MCP3208's INL at V<sub>REF</sub> = 3.3 V (typical only) and the stretched sample (≤ 0.21 LSB computed). The fallback for the sample phase is double conversion at 8 kSPS; an INL failure reopens D23. **D29 (user, 2026-11-04) removed the PGA2040,** so the module items above (supply input and NCP115, 27 Ω pair, W25Q64JV, pad positions) are history. The bare RP2040's support circuit was desk-checked instead (Rev0.7 §3.3, §6.3, §7.1) and is confirmed on the first board (V-MEAS-06); before layout, U1's land is drawn from the RP2040 datasheet's Figure 167 (Rev0.7 §12 item 2, G20). The MCP3208 items and the reset hold stand. | Rev0.7 §3.2, §3.3, §6.5, §7.1, §10 D28/D29; V-MEAS-06 |
| OI-32 | ~~J1's inrush is not limited.~~ **Closed by decision** (D35, the fix by the user, 2026-11-04; the values by Claude). Found at capture (issue #6 P2): 78.6 µF follows V5L, so J1 would deliver 294 µC at plug-in with no limit, 5.9 × a 10 µF load's 50 µC; USB 2.0 allows 10 µF directly across VBUS, or inrush limiting (TI SLVS798G and NXP AN11392, as web-search excerpts; the USB 2.0 text itself has not been read here).Q53, an AO3401A between VBUS_J1 and V5L with a Miller capacitor, ramps V5L in 3.2–6.7 ms after a 2.5–23.7 ms hold-off: 95 mA nominal and ≤ 152 mA of capacitive inrush, V5L up ≤ 30.4 ms after plug-in, ≤ 21 mV of drop (J1 ≥ 4.52 V). Not settled on paper: the MAU104's start-up current and U6's time to attach. Reopen if V-PWR-03 fails. | Rev0.7 §3.1, §10 D35; V-PWR-03 |
| OI-33 | **The receptacle's shell land is drawn for a 0.80 mm board.** The maker's recommended land for C2765186 assumes a 0.80 mm PCB; this board is 1.6 mm, so the shell legs may not reach through the plated slots, and the plug's insertion force (0.5–2.0 kgf) enters the PCB through those four joints and the two pegs. Found at the library capture (issue #8, 2026-11-12). Not settled on paper. The first board shows it: V-MFG-03 (the slots, from the Bottom) and V-MECH-01 (50 cycles). Reopen D37 if either fails. | Rev0.7 §1 fact 20, §10 D37; V-MFG-03; V-MECH-01 |

---

## 12. Pre-Order Checklist

Status on 2026-11-13 (issues #8 and #10, Rev0.5): `[x]` = done, with the evidence named;
`[ ]` = not done, with the owner. The candidate release is `manufacturing/releases/rev0.5/r02/`
(state `WIP`; nothing ordered, nothing paid). It supersedes Rev0.5's r01, whose JLCPCB gate found
two defects, and Rev0.4's r01 and r02: the copper, the BOM and the CPL all changed, so their JLCPCB
evidence does not carry over. The `[x]` items hold for r02 only: any regenerated file needs them again.

**Rev0.6 (issue #13, 2026-11-19) has the release candidate `manufacturing/releases/rev0.6/r01/`
(state `WIP`; nothing ordered, nothing paid), and no `[x]` below is Rev0.6's.** Its
copper and its CPL are new; its BOM and its hand-solder list are Rev0.5 r02's, byte for byte, and
its exported netlist differs from Rev0.5's in the title block alone. On the tracked Rev0.6 board
and its candidate set (r01, byte-identical to the untracked `manufacturing/working/rev0.6/`) the
generators' own checkers pass
(`check_schematic.py`, `check_libraries.py`, `check_pcb.py`, `check_routing.py`, `check_silk.py`,
`check_outputs.py`: ERC and DRC 0, 0 unconnected, Top only, the Kelvin lands, the three lands, the
fiducials, BOM against CPL). The JLCPCB gate ran on r01's files on 2026-11-19
(`manufacturing/releases/rev0.6/r01/JLCPCB_REVIEW.md`), and what it read holds only while the three
SHA-256 it records stand: the part mapping (41 of 41, 0 substituted, 38 Basic and the three allowed
Extended), JLCPCB's assembly stock on that day (every code above 500), the placement preview (J1-J4
and every moved part that is not symmetrical, one instance of each other class) and a quote of
$52.85 without shipping. JLCDFM ran and is **not accepted**: on 2026-11-19 the user accepted the
GND via 0.059 mm from D1 pad 3 as it is (「受け入れる」) and kept the receptacles' plated slots at
0.60 mm (「このまま」), and still decides on the non-plated holes that JLCDFM lists as plated. The
independent check of the set ran on r01's files on 2026-11-19 and passed, by two scripts that are
in the repository since that day (`design/ecad/scripts/`; `design/ecad/README.md`, *Independent
check of a candidate set*): `independent_check_sets.py`, the check Rev0.5 r02 had as the scratch
script `c2_check.py` (30 checks, 0 failed; 8 corruptions, 0 missed), which reads no position, and
`independent_check_positions.py`, at the first run the scratch script `c2_ext_rev06.py` (13 checks,
0 failed; 16 corruptions, 0 missed), which compares the BOM, the CPL, the hand-solder list, the Top
paste Gerber and the two drill files with the tracked board. It takes the board as right and reads
no copper, mask or silkscreen layer. The Akizuki stock of the five hand-soldered part types was read
on 2026-11-19 (the manifest's *Akizuki stock*): all in stock for 2 boards, at the prices of
2026-11-13; MCP3208-CI/P (g100238) is marked 在庫僅少 at 41 packs, 72 on 2026-11-13. Not done on
Rev0.6's files: the assembled parcel's shipping and a quote with impedance control.

**Rev0.7 (issue #14) has the release `manufacturing/releases/rev0.7/r01/`, state `ORDERED`: the user
ordered and paid on 2026-11-20 (`JLCPCB_REVIEW.md` there), with this checklist's open items standing.
No `[x]` below is Rev0.7's.** Its
copper differs from Rev0.6's at J5 and its top mask, top legend and Gerber zip are new; its BOM, its
CPL and its hand-solder list are Rev0.6 r02's byte for byte. On the tracked board and r01's files
(byte-identical to the untracked `manufacturing/working/rev0.7/`) the generators' checkers pass (`check_schematic.py`,
`check_libraries.py`, `check_pcb.py`, `check_routing.py`, `check_silk.py`, `check_outputs.py`) and so
do the two independent checks (`independent_check_sets.py`, `independent_check_positions.py`, with
Rev0.5 r02 as the foreign set: Rev0.6's CPL is this one's byte for byte and would prove nothing). Not
done on Rev0.7: JLCDFM, the stock reads on the day of the order, the stackup's name on the order, a print of the
enclosure (Rev0.3, drawn for the new land on 2026-11-20), and the clamp on a board
(`manufacturing/releases/rev0.7/r01/RELEASE_MANIFEST.md`, *Open gates*). Read at the order, as the
user reported: the part mapping (41 parts, 0 substituted), the placement preview (J2 and J3 not in
detail) and a quote of $53.89 without shipping.

**r02 (2026-11-19) supersedes r01 by its top silkscreen alone**
(`manufacturing/releases/rev0.6/r02/RELEASE_MANIFEST.md`, *What changed against r01*). The paragraph
above is r01's: its part mapping, placement preview and stock reads are of the BOM and the CPL that
r02 keeps byte for byte, and its JLCDFM run and quote are of r01's Gerber zip, of which r02 keeps 14
of 15 members. On r02's files the generators' checkers pass (`check_silk.py`: 44 labels, 3366 checks)
and so do the two independent checks (30 checks and 8 corruptions; 13 checks and 16 corruptions, with
Rev0.5 r02 as the foreign set). Not done on r02: JLCDFM, a quote, and the cart, which holds r01's
files.

- [ ] PCB revision correct; `MANUFACTURING APPROVED` recorded in this file. *Not done: the state is
      `WIP`; the user approves.*
- [ ] All Section 11 open issues closed with evidence in Git. *Not done: OI-1, OI-5, OI-6, OI-8
      (panelization), OI-26 and OI-33 stand; they need a built board, real cables or the user's decision.*
- [ ] Frozen source export committed. *Partly: the KiCad source is tracked and its SHA-256 is in the
      manifest; the copy into the release directory is made at approval.*
- [x] ERC critical errors: 0. DRC critical errors: 0. Unrouted nets: 0. *`check_schematic.py`,
      `check_pcb.py`, `check_routing.py` exit 0; `r02/UsbPowerHub_Main_Rev0.5_ERC.json`, `_DRC.json`.*
- [ ] Board dimensions and mechanical overlay accepted against the authoritative
      mechanical source. *Not done: `design/mechanical/` holds a first enclosure on paper (Rev0.3 since 2026-11-20; Rev0.2,
      drawn for the Rev0.6 board, issues #11 and #13; `check_enclosure.py` passes on its files) and
      nothing is printed. The print process is FDM (user, 2026-11-18); the user accepts the overlay.
      The lid PCB is a board of its own (Lid Rev0.2, `WIP`, `check_lid.py` passes on its files); this
      checklist is the main board's and does not cover it.*
- [ ] JLCPCB stackup ID recorded; differential impedance computed against it. *Half: the ID
      (JLC04161H-7628) is recorded; the impedance is D27's model value, JLCPCB's calculator was not rerun
      (Claude).*
- [x] Machine-placed components on Top only. Bottom paste apertures: 0. Hand-soldered
      parts are listed separately and appear in neither BOM nor CPL (V-MFG-01). *`check_outputs.py`, and
      the independent check, `c2_check.py` (a scratch script outside the repository then, in
      `~/tmp/usb-power-hub/pre-order/local/`, and `design/ecad/scripts/independent_check_sets.py`
      since 2026-11-19: 30 checks, 0 failed; 8 corruptions, 0 missed; run on r02's files on
      2026-11-13).*
- [x] Every BOM line Basic except C2040, C5137013 and C2765186, the three Extended parts D29, D31
      and D37 allow; no Preferred Extended (D22, D29, D31, D37); every hand-soldered part in
      stock at Akizuki (V-MFG-02). *`r01/SOURCING_CHECK.md` (r02's BOM is the same file), PASS on
      2026-11-13; repeat before payment.*
- [x] Every shunt uses a Kelvin land pattern. *`check_routing.py` (Kelvin taps).*
- [x] U1's LQFN-56 land follows the RP2040 datasheet's Figure 167 (the reduced
      3.20 mm ePad), not a stock QFN-56 footprint (G20). *`check_libraries.py`, `library.json`.*
- [x] U6's QFN-28 land follows the CH334/335 datasheet's §5.6 drawing (0.4 mm pitch,
      2.7 mm ePad), not a stock QFN-28 footprint (G21). *`check_libraries.py`, `library.json`.*
- [x] The receptacle's land (J1–J4, C2765186) follows the maker's drawing, with one recorded
      deviation: the two GND pads A1 and B1 are 0.035 mm shorter, the user's choice (D37). *`check_libraries.py`,
      `library.json`; its fit on a 1.6 mm board is OI-33.*
- [x] ≥ 3 fiducials present in the Gerber. *FID1-FID3 flashed at the board's positions, 1.0 mm in
      F_Cu and 2.0 mm in F_Mask (`c2_check.py`).*
- [ ] Silkscreen: Latin ≥ 1.0 mm, no CJK below 2.0 mm, nothing clipped. *Half: `check_silk.py` passes on
      the board; whether JLCPCB clips the legend is seen only after an order.*
- [x] BOM MPN, LCSC number, package, quantity, JLCPCB assembly stock, and
      Basic/Extended status reviewed. *`r01/SOURCING_CHECK.md` (41 parts; r02's BOM is the same file).*
- [x] BOM and CPL designator sets match; every CPL entry is Top and inside the
      outline. *`check_outputs.py`, `c2_check.py`.*
- [x] Pin 1 of every IC, LED cathodes, ESD and connector orientation verified in
      the JLCPCB placement preview. *`r02/JLCPCB_REVIEW.md` section 5 (2026-11-13): every machine-placed
      class read, the receptacle C2765186 included. Its model sat 1.375 mm off the CPL point in r01; r02's
      CPL carries the shift, read on J1-J4 to about 0.04 mm. A viewer reading, not JLCPCB's pick-and-place:
      JLCPCB checks again after an order. The symmetrical parts (R, C, FB1, SMBJ6.5CA) were not read again.*
- [ ] Enclosure fit verified against a real USB-C cable, not a drawing. *Not done (user).*
- [x] Gerber, BOM, CPL, source, manifest, and checksums share one revision. *`r02`:
      `sha256sum -c SHA256SUMS.txt`; its ten `UsbPowerHub_Main_Rev0.5_*` files equal a fresh
      `make_outputs.py` run from the tracked board, whose SHA-256 the manifest records.*
- [ ] JLCPCB DFM, part mapping, and placement preview accepted. *Half: run on 2026-11-13
      (`r02/JLCPCB_REVIEW.md`). Part mapping 41 of 41, 0 substituted; JLCDFM's 6 Danger items judged
      against measurements, except 6 pad-spacing and 3 mask-exposure rows that were not identified one by
      one, and the silkscreen-to-pad rows, which were not read. The receptacles' 0.60 mm plated slots are
      JLCDFM Danger (below 0.61 mm) though JLCPCB's capabilities page allows 0.35 mm: left to the user
      then, who kept them at 0.60 mm on 2026-11-19, at Rev0.6's gate (「このまま」) (user).*
- [ ] Prototype or first-article evidence attached. *Nothing is built.*
- [ ] Final landed cost, shipping, and lead time reviewed. *Half: the quote of 2026-11-13 is $51.94
      without shipping (PCB $8.00; read with r01's Gerber and r02's BOM and CPL; r02's own total and the
      PCBA lines one by one were not read), against the estimate's $51.80 (`design/experiments/
      cost-estimate/`, "Rev0.5 against r02"): 14,257 yen for 2 units with OCS Express ($7.23, read on
      2026-11-12) and the Akizuki parts. DHL Express is the form's default at $17.67 for the 0.24 kg
      PCB-only parcel; the assembled parcel's shipping is in the cart only. Lead time: PCB 3-4 days,
      assembly 3-4 days. Impedance control would add $34.13 (user, in the cart).*
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
