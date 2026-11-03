# JLCPCB 4-layer stackup and USB 2.0 90-ohm geometry (Rev0.4, 2026-11-03) — non-authoritative

**Question.** Which JLCPCB 4-layer 1.6 mm stackup should the board name, and
what trace width / gap does a 90 ohm USB 2.0 differential pair need on L1
against the L2 ground plane?

**Answer.** **JLC04161H-7628.** Judged in order:

(a) It is a standard, selectable JLCPCB stackup for 4 layers / 1.6 mm /
1 oz outer / 0.5 oz inner — the combination the quote page showed for this
board on 2026-11-03. In JLCPCB's impedance calculator its tab is the only one
labelled "Standard", and it carries the recommendation icon. 3313, 1080 and
7628G show only their finished thickness; every other 4-layer tab is labelled
"Special" (or 特殊).

(b) It is the build JLCPCB shows when no stackup is specified, and the only
named one that Economic PCBA does not exclude. The quote page (browser, 2026-11-03) offers
"No requirement" plus 18 named stackups; the "No requirement" dialog shows
exactly this build-up (0.035 / 7628 0.2104 / 0.0152 / core 1.065 / 0.0152 /
7628 0.2104 / 0.035 mm). **Only JLC04161H-7628 carries no note; each of the
other 17 shows "* This is a special stackup, and it doesn't support economic
PCB assembly."** Naming it keeps the quoted $25.40. The other stackups'
prices were not read.

(c) Its 90 ohm geometry on L1 fits the routing rules and the 2.54 mm header
field. **Recommended pair: W = 0.31 mm, S = 0.15 mm** — the model gives
Zdiff = 90.4 ohm at that rounded width. Pair pitch 2W + S = 0.77 mm, the
smallest of the three gaps and the easiest escape between header pins;
S = 0.15 mm is exactly the routing-rule minimum spacing, and because it
needs the smallest trace width it also suffers the smallest absolute width
spread under JLCPCB's +/-20% track tolerance. The un-modelled solder mask
pulls real impedance *below* the bare numbers, so rounding the width down
(0.313 to 0.31 mm, which raises the bare value to 90.4 ohm) is the safer
direction. `impedance.py` prints this pair on its "Recommended pair" line and
exits 1 if it ever leaves 81–99 ohm.

| Gap S | W for 90 ohm | 81–99 ohm window | pair pitch |
|---:|---:|---:|---:|
| 0.15 mm | **0.313 mm** | 0.252 – 0.389 mm | 0.78 mm |
| 0.20 mm | 0.342 mm | 0.280 – 0.420 mm | 0.88 mm |
| 0.25 mm | 0.362 mm | 0.299 – 0.441 mm | 0.97 mm |

(L1 microstrip over L2 GND, prepreg 7628: H = 0.2104 mm, Dk 4.4, finished
outer copper 1.6 mil. Bare Hammerstad-Jensen + Kirschning-Jansen model —
see Method and What this cannot see. For comparison, the IPC-2141A column
in impedance.py's output reads 0.253/0.285/0.310 mm — visibly low, the same
-9% bias it shows on JLCPCB's single-ended datum.)

(d) Other findings:

- The other 17 stackups all carry JLCPCB's "special stackup / no economic
  PCB assembly" note, so none of them is a candidate while the order uses
  Economic PCBA, whatever its geometry.
- Thin-prepreg options give narrower pairs: 1080 needs W = 0.144 mm at
  S = 0.15, 3313 needs 0.178, 2116 needs 0.203. Those widths suit the
  0.15–0.20 mm routing preference better than 7628's, and a fixed track-width
  error is a larger fraction of them. The special-stackup note rules them out
  first.
- Thick-prepreg options want wide pairs: 7628A 0.407 mm, 2116B/D 0.438,
  7628E 0.496, 2116A 0.531, 7628G 0.557, 7628B 0.574. 7628C and 7628F cannot
  reach 90 ohm within W <= 0.60 mm at any listed gap (~0.61–0.80 mm);
  impedance.py reports them as UNREACHABLE, a finding about those stackups,
  not an error.
- The earlier IPC-2141A answer (W = 0.253 mm at S = 0.15) reads **98.9 ohm**
  under this model — right at the edge of the 81–99 band; the model change
  moves the width, not just the labels.
- **+/-20% track-width tolerance:** on the recommended W = 0.31 mm,
  S = 0.15 mm, with S held, it sweeps Zdiff over 82.8–99.7 ohm (99.7 ohm at
  W-20%, 82.8 ohm at W+20%), nearly the whole USB +/-10% band. Reported here for
  the impedance-control decision, which D27 makes (Rev0.4 §10); the order
  page prices the option at +$33.08, which also auto-selects "Confirm
  Production file" +$1.05: $59.53 total.

## Files

| File | What it is |
|---|---|
| `stackups.json` | All 19 4-layer 1.6 mm stackups on the JLCPCB impedance page (outer 1 oz / inner 0.5 oz), layer by layer, every number copied from the page; plus sources, dates, the dielectric-constant table, solder-mask parameters, and the "No requirement" default note. |
| `impedance.py` | `python -I -B design/experiments/stackup-impedance/impedance.py`. Hammerstad-Jensen + Kirschning-Jansen model at the published Dk; prints the Zdiff grid (KJ, with IPC-2141A comparison), solves W per stackup, and prints the recommended pair (D27). Exit 0 = every stackup has its data and the recommended pair is inside 81–99 ohm; 1 = data missing, the recommended stackup absent, or the recommended pair out of band. A stackup that cannot reach 90 ohm is reported as UNREACHABLE, not as an error. |
| `test_impedance.py` | 25 tests. Hand-check of the HJ thickness correction (50.57 ohm at the datum geometry), JLCPCB-calculator reference at the published Dk (HJ within +/-3% in width; IPC-2141A misses it), the exit status on real and corrupted data, corrupted-input tests, monotonicity, stackup-sum vs JLCPCB's +/-10% thickness tolerance. |

## Inputs and their dates

Downloaded pages (all `curl -sL -A "Mozilla/5.0"` on 2026-11-03; raw copies
outside the repo under `~/tmp/usb-power-hub/devin-stackup/dl-*/`):

- `https://jlcpcb.com/impedance` — the 19 stackup tables, prepreg Dk table
  (7628 = 4.4, 3313 = 4.1, 1080 = 3.91, 2116 = 4.16), core Dk 4.6, solder-mask
  parameters (0.6 mil on copper, Er 3.8), min trace 3.5 mil. The page shows
  **no "last updated" date**. Its HTML renders the 1.6 mm / 1 oz / 0.5 oz tab
  combination (`checked` buttons); other thickness/copper tabs exist but were
  not in the fetched HTML.
- `https://jlcpcb.com/help/article/user-guide-to-the-jlcpcb-impedance-calculator`
  — "Last updated on Sep 16, 2026". Calculator parameters: finished outer 1 oz
  = 1.6 mil, inner 0.5 oz = 0.6 mil, trace top = base - 0.7 mil; differential
  range 50–150 ohm; NP-155F core for 4–8 layers.
- `https://jlcpcb.com/capabilities/pcb-capabilities` — no date shown.
  Board-thickness tolerance +/-10% for >= 1.0 mm (1.44–1.76 mm for 1.6 mm);
  impedance tolerance +/-10% standard, +/-5% on request; inner copper
  "0.5oz by default"; track-width tolerance +/-20%.
- `https://jlcpcb.com/blog/reduce-pcb-assembly-cost-prototype` — published
  2026-10-13. The "requires Standard PCBA" list includes "Special stack-ups,
  or a thickness, solder mask color, and surface finish combination outside
  the Economic options".

Browser readings by the main session on 2026-11-03 (no order placed; these
pages need a browser and were not curl-able):

- `https://jlcpcb.com/pcb-impedance-calculator` — Rigid, 4 layers, 1.6 mm,
  inner 0.5 oz, outer 1 oz, unit mil, stackup tab
  "JLC04161H-7628(Standard/Finished thickness 1.59mm±10%)", signal L1, bottom
  reference L2:
  - Single Ended (Non coplanar) **with** solder mask, 50 ohm: W = 14.12 mil
  - Single Ended (Non coplanar) **without** solder mask, 50 ohm:
    W = 14.85 mil — the reference datum the tests check against
  - Differential Pair (Non coplanar), 90 ohm, spacing 8 mil and 0.2 mm:
    **no result** — the width stayed a spinner in two attempts and the page
    threw `TypeError: e.some is not a function`. The pair has no JLCPCB
    reference value.
  - Tab labels: JLC04161H-7628 is the only tab labelled "Standard", with the
    recommendation icon. 3313, 1080 and 7628G carry only their finished
    thickness; every other 4-layer tab is labelled "Special" (or 特殊). The
    calculator also lists JLC04161H-1080C, which the quote page does not
    offer.
- `cart.jlcpcb.com/quote` — settings: 4 layers, 100 x 72 mm, 5 pcs, 1.6 mm,
  green, ENIG 1 U", 1 oz outer / 0.5 oz inner. Price $25.40.
  - "Specify Stackup: Yes" offers "No requirement" plus 18 named stackups;
    "No requirement" shows the JLC04161H-7628 build.
  - Only JLC04161H-7628 carries no note; each of the other 17 shows the
    special-stackup / no-economic-assembly note quoted under Answer (b).
    Selecting 7628 by name leaves the price at $25.40.
  - "Impedance Control: ±10% (±5Ω if value≤50Ω)" adds $33.08; the page then
    auto-selects "Confirm Production file" for $1.05 — $59.53 in total.
  - The PCB Assembly section asks for a Gerber upload first, so the
    Economic/Standard choice — and whether ENIG or impedance control
    changes it — could not be seen.

Model references:

- E. Hammerstad and O. Jensen, "Accurate Models for Microstrip Computer-Aided
  Design", IEEE MTT-S International Microwave Symposium Digest, 1980,
  pp. 407–409.
- M. Kirschning and R. H. Jansen, "Accurate Wide-Range Design Equations for
  the Frequency-Dependent Characteristic of Parallel Coupled Microstrip
  Lines", IEEE Trans. MTT-32, no. 1, 1984, pp. 83–90 (and the 1985
  correction). Validity: 0.1 <= W/H, S/H <= 10, 1 < Er <= 18; this study
  spans W/H ~0.5–4, S/H ~0.2–3.5.
- IPC-2141A is kept only as a printed comparison column (its forms are also
  printed as Eq. 3 of Analog Devices MT-094).

## Method

- Model: **Hammerstad-Jensen** (1980) for the single microstrip, with its two
  separate finite-thickness width corrections — the air increment du1 for the
  air-line impedance Z01, and the smaller dielectric increment
  dur = 0.5(1 + sech(sqrt(Er-1)))·du1 for the effective permittivity:
  Eeff = Eeff0(ur)·(Z01(u1)/Z01(ur))², Z0 = Z01(ur)/sqrt(Eeff). An earlier
  revision folded the single air increment into both terms and answered
  ~48 ohm where this gives 50.57 ohm at JLCPCB's datum width — the test
  suite pins the correct value and shows the old form failing it.
- Pair: **Kirschning-Jansen** (1984) static even/odd impedances,
  Zdiff = 2·Z_odd. KJ assumes zero-thickness strips; as an approximation the
  corrected dielectric width ratio ur is used as the KJ width ratio, with
  ee/zl the single-line relations evaluated at ur.
- Reference vs JLCPCB: their calculator says a bare 50-ohm single-ended
  trace on JLC04161H-7628 is 14.85 mil; the model solves ~15.15 mil at the
  page's published Dk 4.4 (+2%, inside the +/-3% the tests assert). At the
  same Dk IPC-2141A gives 13.50 mil (-9%), outside the tolerance — the model
  choice is itself tested.
- Inputs per stackup: H = sum of L1–L2 prepreg plies; Dk = thickness-weighted
  harmonic mean of the plies' published per-glass Dk (series dielectric; a
  derivation, not a JLCPCB-published value); T = 1.6 mil finished outer
  copper per the user guide (the stackup tables list the 0.035 mm base foil).
- W solved by bisection in 0.10–0.60 mm at S = 0.15/0.20/0.25 mm for 90 ohm
  and for both 81/99 ohm band edges.
- Solder mask, quantified on a single line only: JLCPCB's own
  masked-vs-bare widths (14.12 vs 14.85 mil) read, under the bare model, as
  the mask removing **~2 ohm at 50 ohm** on one trace. On the pair the mask
  also fills the inter-trace gap and the effect is larger; it is NOT
  quantified here — no pair mask correction is invented.
- Not modelled (direction of effect): solder mask lowers impedance; the
  etch trapezoid (top = base - 0.7 mil) narrows the conductor and raises it
  slightly, partially cancelling; ENIG is approximately negligible for
  impedance though it adds some loss. Net: a masked, etched board should
  land below the bare numbers here, more so on the pair than the
  single-ended ~2 ohm — the solved widths are an upper bound.

## How to rerun

```text
python -I -B design/experiments/stackup-impedance/impedance.py
python -I -B design/experiments/stackup-impedance/test_impedance.py
```

`impedance.py` exits 0 on the current data. JLC04161H-7628C and -7628F are
printed as UNREACHABLE (no W <= 0.60 mm reaches 90 ohm at any listed gap);
that is a finding about those two stackups, not a study failure.

## What this cannot see

- **JLCPCB's differential calculator result does not exist.** The pair run
  on 2026-11-03 returned no result (page `TypeError`). The pair numbers here
  are model values checked against JLCPCB's *single-ended* datum — the best
  available anchor, but not JLCPCB's pair answer. Someone must re-run the
  calculator when it works, or ask JLCPCB support for the pair width.
- **Solder mask, etch factor and ENIG are not modelled** in the pair
  computation; the mask is quantified only for a single line (~2 ohm at
  50 ohm) and its pair effect is larger and unquantified. Real widths for
  90 ohm will come out narrower than the bare-model values.
- **Economic vs Standard PCBA eligibility for this order is still unseen**
  — the quote page demands a Gerber upload before showing assembly options,
  so whether ENIG or the impedance-control option changes the assembly
  class is unknown. (The stackup side is now settled: 7628 alone carries no
  special-stackup note.)
- **The HS path through the Akizuki modules and 2.54 mm headers (OI-26) is
  outside this study.** This study sizes the board-level pair only; module
  layout and headers are the dominant unknown for HS eye margin.
- **Static model:** the closed forms are quasi-static; dispersion at USB HS
  frequencies slightly lowers Er_eff and is ignored.
- **Other copper-weight stackups exist** (2 oz outer, 1/2 oz inner tabs) but
  are not in the fetched HTML; this file covers only the board's own
  1 oz / 0.5 oz set.
- **No "last updated" date on the stackup page itself;** JLCPCB has changed
  prepreg styles before (user guide: 3313 replaced 2313). Re-fetch before
  ordering.
- **Published Dk is nominal**; the pressed-prepreg value JLCPCB actually
  delivers can differ. The single-ended datum shows the model is on the
  right basis (+2% in width), but the true pair answer still needs
  JLCPCB's calculator.
- **Frequency/mode detail:** single-ended and common-mode impedances,
  pair-to-pair skew, and the 27 ohm series-resistor question (OI-31) are out
  of scope.
