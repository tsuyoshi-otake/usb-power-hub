# Journal - usb-power-hub

Append-only. One entry per completed unit of work or finding, newest at the
bottom. Promote a learning into [`rules.md`](rules.md) (tooling) or `CLAUDE.md`
Section 13 (board) only once verified.

## 2026-11-03 - Resume the paused project: Git, Rev0.2, requirements, stock check

- **Symptom.** The project had been paused since 2026-08-16. It was not under
  version control (OI-15); the circuit document's board outline (OI-13), layer
  count (OI-10) and hub choice were open; no requirement or verification
  document existed; no part had been checked against the JLCPCB assembly pool.
- **Decisions by the user (this session).** Scope = documents plus JLCPCB stock
  check (no firmware, no KiCad capture). D10 = 85 x 35 mm, 4 layers. D11 =
  USB2514B. ~~D12 (separate 12 / 24 MHz crystals) follows from D11.~~ (withdrawn:
  not a user decision — see the next entry)
- **Root causes found while revising.** Rev0.1 had several calculations that did
  not survive the datasheets: stuck-range dissipation ignored the current limit
  and ladder resistance; board rails were counted at 3.3 V instead of the input
  rail; the LDOs on VPD would dissipate 1.14 W in SOT-23-5; the ADC had no
  clock; "9 V granted -> advertise 1.5 A" ignored the granted current; and J1 is
  a PC port that usually offers 5 V only. Each became a correction in Rev0.2 or
  a new open issue (OI-16 to OI-22).
- **Fix.** Commits:
  - `4dd10fb` snapshot of the design as paused (closes OI-15).
  - `2a83480` pure rename Rev0.1 -> Rev0.2 (keeps `--follow` history).
  - `271ec95` Rev0.2 content, `requirements/` (product, verification, parts),
    `tools/jlc_stock.py`.
  - `6bb3f73` CLAUDE.md brought in line (OI table, Rev0.2 references, 4-layer
    assignment), mockup title fixed (OI-12), README.
- **Verification.** `tools/jlc_stock.py` negative test: unknown code and MPN ->
  exit 1. Live recheck of all 46 LCSC rows: every MPN and class matched, 9 rows
  differed only in stock count (expected drift; the document's figures are
  dated). `git log --follow` on Rev0.2 reaches `4dd10fb`. Independent rubric
  verification: see the next entry.
- **Learning.** JLCPCB datasheet field moved to `dataManualFileAccessIdUrl`;
  encrypted PDFs need `cryptography` in the task venv; pure-rename commit
  before a rewrite. All three promoted to `rules.md`.
- **Still open for the user:** OI-16, OI-17, OI-19, OI-20, OI-21 and the
  proposals P1-P12 in Rev0.2 Section 14.

## 2026-11-03 - Independent verification, round 1: two failures fixed

- **Symptom.** A fresh-context rubric verifier passed C1-C7 and failed two:
  - C8: D12 ("two independent clocks, a consequence of D11") sat in the
    closed-decision table and closed OI-2, but the user never made it.
  - C9: REQ-PORT-02 said a failed `ON`/`CYCLE` always leaves the port OFF,
    while the protocol table said `ERR 02 BAD ARGUMENT` leaves it unchanged;
    V-PORT-02 inherited the contradiction.
  - Side note from C6: V-SAFE-01's 100 mA fault-injection load drops only
    ~0.21 V across a stuck MID ladder, below the 300 mV detection threshold.
- **Root cause.** D12: D11 forces only a 24 MHz hub clock; a second crystal
  (versus an oscillator or an RP2040-derived clock) is a design choice, so
  calling it "unavoidable" promoted a proposal into a decision. C9: the
  command-level rule was written before the per-command table and not
  re-read against it. V-SAFE-01: the load was picked without computing the
  drop against the threshold it was meant to exercise.
- **Fix.** D12 withdrawn and recorded as such; the clock arrangement is now
  proposal P13; OI-2 reopened and blocking. Error states split into "rejected
  for its form" (`ERR 01/02/08`, both ports unchanged) and "failed after
  validation" (`ERR 04/06/07`, port OFF), in REQ-PORT-02, the table and
  V-PORT-02. V-SAFE-01 now runs at 250 mA (~0.53 V, detected) and 100 mA
  (~0.21 V, the documented harmless undetected region); REQ-SAFE-03 and
  Rev0.2 §7.3 state the ~142 mA detection floor.
- **Verification.** Re-run by a new fresh-context verifier; result in the next
  entry.
- **Learning.** "Consequence of a decision" is a claim to check: list the
  alternatives the decision still leaves open; if there are any, it is a
  proposal. Also, a test point chosen to trip a threshold needs the
  threshold arithmetic written next to it.

## 2026-11-03 - Independent verification, round 2: all criteria pass

- **Result.** A second fresh-context verifier (no shared context with round 1)
  passed C1-C9 against commit `98a451e`: Git state, document set and rename
  history, two-way REQ/V trace (42 REQ, 19 V, zero orphans), decision records,
  live stock recheck of all 46 rows (MPN and class unchanged) plus the negative
  test, every recomputed calculation within 2 %, cross-document consistency,
  labelling of proposals, and the port-power contract.
- **Follow-up.** Its one observation: Rev0.2 §11 still read "Recommendation:
  option 1 (80 × 30 mm)" under a CLOSED heading. Relabelled as historical with
  the user's choice (D10) stated next to it.
- **Residual risk.** Everything verified is document consistency and dated
  vendor data. Nothing is built or measured; the stock figures will drift; the
  P13 note "whether RP2040 USB boot accepts another XOSC frequency" is
  unconfirmed because the RP2040 datasheet was not fetched in this session.

## 2026-11-03 - Rev0.3 independent verification, round 1: two failures

- **Symptom.** A fresh-context rubric verifier (`.claude/goal-loop/rev03-consistency/rubric.md`,
  8 criteria, run on the working tree after `1452cb8`) passed C1, C2, C4, C6, C7 and C8.
  Live recheck: all 42 LCSC codes returned their recorded class, Basic or Preferred Extended,
  and none returned plain Extended. It failed two criteria:
  - C3: CLAUDE.md §5.2/§5.3 (lines 285, 286, 320) still told the layout to keep away from
    "the buck converter" / "buck switch node"; Rev0.3 has no buck (D14).
  - C5: Rev0.3 §4 said "the ratio of 13,000 between full scale and the LSB"; 1.37 A /
    0.105 µA is 1.3 × 10^7.
  - Side note (C6): the header quote of the user read 「デカいパーツ」; the user wrote
    「デカくいパーツ」, and the quote also dropped the line 「秋月で購入できるパーツに限って」.
- **Earlier in the same pass (before the verifier).** Writing the calculation script
  exposed a basis mismatch: full-scale figures included the pedestal, but the up-range
  thresholds did not (366 µA vs 365 µA, 18.7 vs 18.6 mA; HIGH's 1.16 A already included it).
  Every threshold-derived figure now includes it: bottoms 292 µA / 14.9 mA, 5.5 % / 6.8 %,
  ≤ 7.8 %, MID burden 0.189 V. The script is committed beside the document as
  `design/circuit/CIRCUIT_DESIGN_Rev0.3_calc.py`.

## 2026-11-03 - Rev0.3 verification, round 2: pass; type pooling; the user's restated rule

- **Fix for round 1.** CLAUDE.md §5.2/§5.3 now name the MAU104 instead of a buck. The
  §4 dynamic-range sentence now gives 1.3 × 10^7 = 4096 × 51 × 62.5. The header quotes the
  user verbatim: 「秋月で購入できるパーツに限って」 and 「デカくいパーツ」.
- **New input from the user.** Mid-loop, the user pasted a six-point rule list
  (「部品はBasic Partsのみ」 … 「パーツの種類や点数は減らすこと」) and asked whether the design
  follows it. Answer given: rule 1 is broken by the two Preferred Extended parts (OI-30),
  rules 2 and 3 are met, and rules 4–6 only partly. The list is recorded in the Rev0.3 header,
  D13, REQ-MFG-05, parts.md and CLAUDE.md §10.3. OI-30 is put to the user again.
- **Type pooling (rule 6).** Machine-placed types went from 42 to 38:
  - 510 Ω 0402 was replaced by the 0805 R_L part.
  - The 20 kΩ was dropped, and the V_J4 divider is now 33 k / 15 k.
  - 10 µF 10 V moved to 25 V.
  - 100 nF 16 V moved to 50 V.
  V3V3 now has 22 µF. The AMS1117 output-capacitor stability needs a datasheet check, which is
  added as a to-confirm in parts.md.
- **Verification.** A new fresh-context verifier, run on the rubric extended to 9 criteria
  (C6 now checks the verbatim quote, C9 the pooling), passed all 9. It ran a live
  recheck of the 38 codes (36 Basic, 2 Preferred Extended, none Extended), read the
  Akizuki pages again (stock unchanged), and recomputed every listed figure.
- **Its non-blocking observations, fixed afterwards; a third, narrow verifier passed 5/5:**
  - "~7 LSB" without U4 was really 1.3 LSB; the figure was left over from the 15 kΩ R_OUT
    draft.
  - "Gain 12 balances the ratios" was wrong: equal ratios need gain 13.5.
  - CLAUDE.md's "tens of LSB" was really up to 8 and 13 LSB.
  All three figures are now printed by the calc script. The datasheet revisions from the
  datasheet pass are recorded in parts.md.
- **Learning.** Promoted to rules.md: Akizuki URLs and markers; `python -I` and UTF-8 output;
  heredoc backslashes; one script and one basis for derived numbers; quote the user
  verbatim.
- **Commits.** `1452cb8` (Rev0.3 content), `673f6c1` (verification fixes, calc script,
  type pooling, the user's restated rule, memory).

## 2026-11-03 - Rev0.4: Basic parts only (D22), PGA2040 + 2 x MCP3208 (D23)

- **Symptom.** The user's restated rule says 「部品はBasic Partsのみ」. Rev0.3 still had two
  Preferred Extended parts, STM32F103C8T6 and SRV05-4 (OI-30). The user answered 「うん、okだよ」,
  then chose 「外して Basic のみにする」 when asked.
- **Root cause.** Rev0.3 read D13 as "never an Extended-only PCBA". A Preferred Extended
  part has no feeder fee, but it is still labelled Extended, so it breaks the literal rule.
- **Fix.**
  - MCU: PGA2040 (Akizuki RP2040 module, D± on its pins).
  - ADC: two MCP3208 DIP16, one per port, at V_DD 5 V and V_REF 3.3 V. They share
    CLK/CS/DIN, and the PIO stretches the sample phase to 4.5 µs. The result is 14.0 kSPS.
  - Other circuit changes:
    - level shifters from pooled types;
    - hold pull-ups changed to 10 kΩ;
    - ROM UF2 bootloader;
    - PSM712 on CC of J1–J4;
    - D± left unprotected.
  - Part types 38 → 35.
  - Decisions: D22 (user), D23 (delegated), new OI-31 / V-MEAS-06 / G19.
- **Investigated on the way.**
  - The MCP3208 rates its inputs only to V_DD + 0.6 V and gives no input-current rating.
    At V_DD = 3.3 V an overranged HIGH node would push 1.1 mA into it. That is why V_DD is
    5 V.
  - The native 1.5 µs sample phase leaves 17 / 31 LSB of residual from the 1.5–2.4 kΩ
    source. That is why the sample phase is stretched.
  - The RP2040 reset pull-down (50–80 kΩ) would hold Rev0.3's 100 kΩ hold pull-ups near
    1 V. That is why they are 10 kΩ.
- **Verification.**
  - The calc script exits 0, and its figures match the documents.
  - A live JLCPCB recheck shows 35 / 35 Basic.
  - A fresh rubric-verifier (sonnet) passed C1–C9 in its first round. The rubric is
    `.claude/goal-loop/rev04-basic-only/rubric.md`.
- **Failure on the way.** The edit script's `Path.write_text` saved seven files as CRLF.
  Git normalized them, but the working copy did not match `eol=lf`. They were converted back
  to LF before commit, and the rule was promoted to rules.md.
- **Residual risks.**
  - Board fit: hand-soldered parts take ≈ 2,800 of 2,975 mm² (OI-23).
  - The PGA2040's supply input and USB resistors are unconfirmed (OI-31).
  - Akizuki has only 41 PGA2040 in stock.
  - At the J4 5.5 V / V5A 4.5 V corner, the HIGH node exceeds the MCP3208 input rating by
    0.18 V; only the 1 kΩ limits the current.
  - D± have no ESD protection.
- **Commit.** `2b30b9f`.

## 2026-11-03 - OI-23 placement study; D24 board outline 100 x 72 mm

- **Symptom.** Rev0.4 put ≈ 2,800 mm² of hand-soldered parts on the 2,975 mm² board that D10
  had fixed at 85 × 35 mm. OI-23 asked for a placement study before capture.
- **Investigation.**
  - Counted every courtyard: hand parts 2,574 mm², SMD 1,649 mm² (Rev0.4 §11 had guessed
    1,100–1,200 mm² for the SMD without counting).
  - The space under raised modules is 704 mm².
  - The lower bound with no routing space is 3,715 mm², so no 85 × 35 layout exists.
  - A block placement at 100 × 72 mm passes all checks at K = 1.6, with headroom to K = 1.74.
  - JLCPCB instant quote, read by hand on 2026-11-03 (4 layers, 5 pcs, default options):
    $8.00 at 85 × 35, 100 × 72 and 100 × 100 mm; $30.80 at 130 × 72 mm.
- **Decision.** The user wrote 「100x100未満ならいいんだっけ」, setting the condition. D24 records
  100 × 72 mm: the condition is the user's, the size is Claude's (delegated).
- **Verification.**
  - Rubric: `.claude/goal-loop/oi-23-d24/rubric.md`, graded by a sonnet rubric-verifier.
  - Round 1 failed C4, C5 and C8:
    - the printed bound showed the space (704) while the code subtracted 442;
    - 1,515 should round to 1,516;
    - README.md carried an undated price claim.
  - Root cause of C4: the credit was taken per block (a block with one tall part lost all
    of its low parts) and the print showed the wrong term.
  - Fix: the credit now counts per part, so the bound is the most favourable one, and a test
    asserts that the printed terms add up.
  - Round 2 passed C1–C9. It also noted that a block placed twice went undetected; a
    duplicate check and its negative test were added (15 tests, all pass).
- **Learning.** Promoted to rules.md under "Design documents": a printed sum shows the terms
  the code used, and a lower bound takes the most favourable value at every step.
- **Residual risks.**
  - The CH335F outline is a photo estimate (OI-24).
  - The header height behind the 1.5 mm under-module rule is not chosen.
  - The study does not route.
  - The mockup and the enclosure must be redrawn for 100 × 72 mm.
- **Commit.** `c1aec4f`.

## 2026-11-03 - D25: J4 input fuse F1 = MF-R300 (closes OI-29)

- **Symptom.** J4 VBUS had no fuse (OI-29). No fuse or PTC is a JLCPCB Basic part: MF-R300 is
  C208487, Extended.
- **Investigation.**
  - Akizuki candidates at ≥ 2.5 A hold: MF-R300 (Bourns, g112630, 2,865 pcs, ¥40) and RGEF300
    (g100769). Only the Bourns datasheet with resistance figures was at hand.
  - MF-R300: 30 V; 3.00 A hold (2.49 A at 40 °C, 2.31 A at 50 °C); 6.00 A trip; R1max 0.08 Ω;
    18.3 mm tall.
  - The worst-case F1 current below the two OC trips is 2.33 A, at 0.43 W.
- **Decision.** D25 (Claude, delegated): F1 sits ahead of D6, so a VBUS_IN short or a crowbarred
  wrong supply trips F1.
- **Cost, from the calc script.**
  - Port drop is now 0.20 / 0.40 / 0.48 V (0.5 A / 1 A / both ports at 1 A).
  - The HIGH mirror gate headroom falls to 0.03–0.36 V, from 0.19–0.44 V.
  - OI-27 and V-MEAS-00 now test the 4.59 V corner.
  - New: REQ-SAFE-04 / V-SAFE-02. F1 was added to the OI-23 study: the bound is 3,780 mm², and
    the layout still passes.
- **Verification.**
  - Rubric `.claude/goal-loop/oi-29-d25/rubric.md`, graded by a sonnet rubric-verifier.
  - Round 1 passed C2–C8 and failed C1: README.md and the Rev0.4 §7.4 table still gave
    0.32 V.
  - Root cause: the stale-figure sweep grepped `0\.32 V at 1 A`, and README wraps that phrase
    across two lines.
  - Fixed. A C1/C8 re-grade passed.
- **Learning.** Promoted to rules.md (sweep for the bare number).
- **Residual risks.**
  - The 0.03 V headroom corner rests on the extrapolated OP07 V_OL (OI-27).
  - The enclosure must clear F1's 18.3 mm height.
  - D6 may not survive a sustained over-voltage.
- **Commit.** `d6d7c3d`.

## 2026-11-03 - D26: how J1's current is declared (closes OI-25)

- **Symptom.** The board draws about 0.21 A from J1, but the CH335F's default descriptor
  declares self-powered, 100 mA (OI-25).
- **Investigation.**
  - The hub must stay self-powered. J2 and J3 are powered from J4, and as a bus-powered hub it
    would offer DUTs only 100 mA.
  - A self-powered hub may draw only one unit load from upstream. Raising its MaxPower
    through the EEPROM (option a) would therefore be non-compliant in itself, and it adds a
    part.
  - Option (b) was feeding the logic from J4. It costs the COM port without J4. It takes
    0.13 A from J4's advertisement, so a Default-only J4 could run no port. It also cuts F1's
    40 °C margin from 0.16 A to 0.03 A.
- **Decision.** D26 (Claude, delegated):
  - The hub stays at its defaults.
  - The RP2040 function declares bMaxPower 200 mA, bus-powered (REQ-HOST-08). Its share is
    126 mA typical, 172 mA with every OP07 at its maximum.
  - The board is specified for 500 mA upstream ports, not bus-powered hubs (product.md §9).
  - V-HOST-01 reads the descriptors and requires J1 ≤ 0.30 A.
- **Verification.** Rubric `.claude/goal-loop/oi-25-d26/rubric.md`, graded by a sonnet
  rubric-verifier: 6 of 6 passed in round 1.
- **Learning.** None new: the bare-number sweep rule was applied, and it found nothing stale.
- **Residual risk.** The RP2040 share rests on a 30 mA estimate for the PGA2040 (OI-31). The
  0.30 A pass limit in V-HOST-01 catches a larger draw.
- **Commit.** `8f18bb2`.

## 2026-11-03 - Prototype cost estimate (5 PCBs, 2 assembled)

- **Request.** The user asked for 「製造コストを試算してPCBA2台基板5枚」.
- **Result.** `design/experiments/cost-estimate/`, at 160 yen/USD:
  - Economic PCBA: JLCPCB $64.77, plus Akizuki 11,520–12,480 yen, for 21,883–22,843 yen for
    2 units.
  - Standard PCBA: 37,008–37,968 yen.
  - Economic is cheaper because D22 made every machine-placed part Basic, and Economic charges
    no feeder fee for Basic parts.
- **Sources.** All read on 2026-11-03:
  - The JLCPCB price page (updated 2026-10-22).
  - The quote page: PCB price and Japan shipping. No order was placed.
  - The API price snapshot `jlc_prices.json`.
  - The JLCPCB blog post of 2026-10-13 for the Economic limits.
  - Akizuki: parts.md and its order page (free shipping from 11,000 yen).
- **Verification.** Rubric `.claude/goal-loop/cost-estimate/rubric.md`, sonnet rubric-verifier.
  - Round 1 failed C6: the FX figures and the blog post had no named source.
  - Round 1 also failed C7: the D26 journal edit was in the working tree. It was committed
    separately as `370703b`.
  - Round 2 passed C1 and C6. C7 failed again because rules.md was edited during grading.
  - Resolved by committing the in-scope files alone. `git show --stat 0d0eae0` lists only
    them.
- **Incident.** The round-1 verifier ran a broad `find ... -exec rm -rf` in
  `~/tmp/usb-power-hub/`. It removed `pdfx/` (the task venv), `ds-verify/`,
  `akizuki-ch335f/`, `akizuki-fuse/`, `fuse-ds/` and `costcheck/`. All six were this task's
  own scratch directories. The user's PNG was untouched.
- **Learning.** Promoted to rules.md:
  - Tell a verifier to delete nothing.
  - JLCPCB help and blog pages are curl-readable.
  - The API's price fields.
  - Also: keep memory edits out of the tree while a verifier grades a scoped change set.
- **Residual risks.**
  - Economic eligibility: a named stackup may count as "special". The ENIG combination is
    unconfirmed.
  - 38 of the 138 0402 positions are unattributed.
  - PCBA parcel shipping and import tax are not priced.
- **Commit.** `0d0eae0`.

## 2026-11-03 - D27: stackup JLC04161H-7628 and the USB 2.0 pair geometry (Devin, SWE-2 Max)

- **Request.** 「じゃあ、続けて。Devin」, then 「を使って。SWE-2 Maxね」: continue with the next
  paper item, the JLCPCB stackup and impedance calculation, with the Devin CLI on swe-2-max.
- **Result.** `design/experiments/stackup-impedance/`: 19 stackups, an HJ + KJ model, and
  25 tests. D27 (Claude, delegated) names JLC04161H-7628 and sets the provisional pair
  W 0.31 / S 0.15 mm on L1 over L2. The pair reads 90.4 Ω in the bare model, and
  99.7 / 82.8 Ω at W −/+20 %. Impedance control is not ordered for the prototype
  ($33.08 + $1.05).
- **Devin rounds.**
  1. Run 1 used IPC-2141A (−9.1 % against JLCPCB's single-ended datum) and quoted an
     unsourced EEVblog figure. Brief fix1.
  2. Run 2 got the HJ thickness correction wrong. It fed du1 into both Z01 and Eeff, which
     gives 48.1 Ω at the datum instead of 50.57 Ω. A fitted Dk 4.04 hid the error. Found by
     the main session's independent implementation and a hand calculation. Brief fix2
     carried the exact formulas and the hand-check value.
  3. Run 3 was correct, but `impedance.py` exited 1 on the real data, because 7628C/F
     cannot reach 90 Ω. The main session rebuilt the exit status around the recommended pair
     and added 5 exit-status tests.
- **Incidents.**
  - A denied `rm` ended a Devin print-mode run with no message. `--export` showed the
    refused call. The denied `rm` of `devin-permtest` was not retried.
  - JLCPCB's differential calculator failed twice (spinner, `TypeError`). Its single-ended
    mode worked after a page reload. No order was placed.
  - The main session's own brief had wrongly told Devin that only 3313 and 1080 lack the
    "Special" label in the calculator. 7628G lacks it too. Corrected in the study README.
- **Verification.** Rubric `.claude/goal-loop/stackup-d27/rubric.md`, sonnet
  rubric-verifier.
  - Round 1: C1–C6 pass. The verifier recomputed the figures, re-downloaded
    `jlcpcb.com/impedance` and matched all 18 named stackups.
  - It disclosed that it had run `git add -N` and then `git reset`. `git status` matched the
    starting state. Its directory `~/tmp/usb-power-hub/verify-d27-1` is left in place.
  - After the pass, the HandCheck docstring rounding was corrected as the verifier noted
    (du1 0.2486, Eeff0 3.3374, Eeff 3.1790). The 25 tests were rerun and pass.
- **Learning.** Promoted to rules.md:
  - JLCPCB stackup pages and the calculator's behaviour.
  - Economic eligibility is the quote page's per-stackup note, not the tab label.
  - Check delegated numeric work against an independent implementation.
  - Forbid verifiers git index writes.
  - Devin CLI invocation and permission behaviour.
- **Residual risks.**
  - JLCPCB's own pair width is not confirmed; rerun the calculator before routing.
  - The pair's solder-mask effect is unquantified, so the widths are an upper bound.
  - The ENIG / Economic combination and impedance control's effect on the PCBA class are
    unseen.
  - HS through the modules and headers is still OI-26.
- **Commit.** `6980850`.

## 2026-11-03 - Private GitHub remote

- **Request.** 「一旦コミットプッシュしちゃいなよ」. The tree was already committed (`4a03ca2`), but
  there was no remote and no GitHub repository. The user chose "private で作成して push" when
  asked.
- **Done.** A secret scan of the 27 tracked files found nothing. Then
  `gh repo create tsuyoshi-otake/usb-power-hub --private --source . --remote origin --push`.
  `gh repo view` reports `PRIVATE`, and `main` tracks `origin/main`.
- **Docs.** CLAUDE.md §0, the OI-15 row and the README's Repository section said "no remote".
  They now name the private remote.

## 2026-11-03 - Pre-layout bench kit (issue #1)

- **Request.** 「進めて」: carry on with issue #1. That means the parts to buy, the instruments
  and the bench wiring for OI-24, OI-27/OI-28 (V-MEAS-00) and OI-31 (V-MEAS-06).
- **Delegation.** Devin (SWE-2 Max) drafted `tests/fixtures/pre-layout-bench/`. Its Akizuki
  figures for 38 items (price, pack, stock) matched the main session's own download of every
  product page. Its titles matched too.
- **Defects in the draft, found by the main session's review and fixed:**
  1. **Substitutes that could not close the issue.** OP07CPZ (ADI, PDIP) and IRLML6402 stood
     in for OP07CDR and AO3401A. OI-27 asks how these exact parts behave. Fix: the exact parts
     from LCSC (C7433, C15127), plus an SOP-8 adapter.
  2. **A negative control that could not fail.** CH0/CH1 were driven from a pot wiper. A stiff
     source removes the charge-sharing droop that V-MEAS-06's native sample must show. Fix: a
     PNP current source per channel.
  3. **Back-feed.** Bench A tied a bench 5 V supply to the USB-C kit's VBUS, which feeds the
     PC's port. Fix: bench A is powered only from the PC's USB port.
  4. **R_M pulse voltage.** The draft said "at 3.3 V", which is the gate drive. 2.35 W in 10 Ω
     needs 4.85 V across R_M. Fix: set it on the scope; pulses ≥ 1 s apart, spacing recorded.
     Gate pull-downs were added, because a floating gate would hold 2.35 W on a 1 W resistor.
  5. **Smaller defects.**
     - The DMM fallback overstated a 3½-digit meter: a 1999-count meter shows 10 mV at 3.3 V.
     - An unsourced scope requirement was removed.
     - The PGA2040 facts were taken from a mirror and a search snippet. They now come from
       Pimoroni's own page and schematic.
     - V3V3 was said to feed the SPI pull-ups. They go to 5 V (§6.4).
     - The socketed PGA2040 was listed as able to move to a prototype.
     - kit.py was Akizuki-only. It now knows the vendor, with LCSC prices in USD and LCSC's
       minimum order.
- **Cost.**
  - Akizuki: 41 items, 11,345 yen, shipping free. The spare MCP3208 (500 yen) is what lifts
    the order over the 11,000 yen line; without it the subtotal is 10,845 yen and shipping costs 550 yen.
  - LCSC: $1.04 plus shipping. The shipping is unknown because LCSC shows it only at checkout.
- **Verification.** 21 tests, each check negative-tested; kit.py exits 0. Rubric
  `.claude/goal-loop/bench-kit/rubric.md`, graded by a sonnet rubric-verifier.
  - Round 1 failed C3 and C5. C3: the port and V12F capacitors were electrolytics, against
    the design's 0805 MLCCs, whose ESR and DC-bias derating shape the step test. C5: PC and
    soldering had no fallback, the resistor fallback reached only 1.07 A at 4.59 V, and
    "4½ digits" does not give 0.1 mV at 3.3 V.
  - The fixes: Murata 0805 MLCCs (g108240, g113388); a resistor set that reaches 1.25 A;
    a DMM of at least 40,000 counts; and real fallbacks.
  - Round 2 passed C1-C7. The verifier re-downloaded all 41 Akizuki pages, both LCSC
    pages and the Pimoroni schematic. It also mutated copies of kit.py, and each disabled
    check made a test fail.
  - After the pass, the 4.7 ohm || 15 ohm fallback was reworded, because the verifier
    read its rating as ambiguous. Its directories `~/tmp/usb-power-hub/verify-bench-1`
    and `verify-bench-2` are left in place.
- **Incident.** The heredoc doubled-backslash rule, already in rules.md, recurred. A heredoc
  edit put real newlines into two string literals in kit.py (SyntaxError). They were fixed
  with Edit.
- **Residual risks.**
  - LCSC's shipping charge is unknown.
  - Stock is volatile: the PGA2040 had 41 and dupont-mm was low.
  - TL431 and AZ1117 stand in for supply-role parts.
  - No bench firmware exists, and nothing is built.
- **Commit.** `7b25e24`.

## 2026-11-04 - D28: desk checks replace the pre-layout bench (issue #2)

- **Symptom / request.** The user decided not to buy the issue #1 bench kit:
  「試験キットは買わない、基板で確かめる。君が机上で確認すればいい」. OI-24, OI-27, OI-28 and
  OI-31 were waiting on that bench.
- **What the datasheets settled (D28, user).**
  - OI-27: TI SLOS099F specifies the OP07 gain on a single 15 V supply, V_O 1.4–11.4 V into
    R_L ≥ 500 kΩ. The AO3401A gate is a ≥ 52 MΩ load, so the row applies, and the HIGH
    mirror's gate headroom at 1 A is 1.63–1.96 V. The old figure, 0.03–0.36 V, was against a
    3.0 V output-low limit that had been extrapolated.
  - OI-28: the MFU rates 6.25 W for 5 s. The stuck-MID fault puts 2.35 W in R_M for ≤ 10 ms,
    so the watchdog timeout must be ≤ 5 s.
  - OI-31, from Pimoroni's schematic: the VBUS pad feeds an on-module NCP115, so on V3V3 the
    3V3 pad is ≥ 3.208 V (USB_VDD minimum 3.135 V). The 27 Ω pair is on the module. The
    W25Q64JV has a 64-bit unique ID (4Bh). The hold gates sit at 2.705–2.887 V against the
    2N7002's 2.5 V maximum threshold.
  - Closed by decision. Each closure names what paper does not settle, and V-MEAS-00 /
    V-MEAS-06 now check it on the first PCBA board: loop stability, R_M's shift after faults,
    MCP3208 INL at 3.3 V, and the stretched sample.
  - OI-24 stays open. The CH335F module bought for the board is measured before layout.
- **Root-cause finds along the way.**
  - V-SAFE-01 could not inject its fault: firmware cannot hold a bypass FET off against the
    LM393. It now removes Q17 / Q18.
  - The MCP3208 Figure 2-2 value was misread from a raster image as −0.5 LSB. The vector
    paths give −0.37.
- **Verification.** Rubric `.claude/goal-loop/desk-checks/rubric.md` (C1–C7), graded by three
  fresh sonnet rubric-verifiers. Each one downloaded the OP07 and MFU datasheets itself.
  - Round 1 failed C1, C2, C4 and C6. The causes: G1 still said ≥ 2.75 V, the INL misread,
    non-numeric pass items, and the AO3401A / 2N7002 entries had no board check.
  - Round 2 failed C4 and C6:
    - V-MEAS-00 cited V-MEAS-02 for a MID gain point that it does not have;
    - the LOW sweep ran to 430 µA, past the 365 µA hardware up-range;
    - the flash check was a marking, not a JEDEC ID;
    - two source dates were missing.
  - Round 3 passed C1–C7. After the pass, CLAUDE.md's stale "D1–D21" was fixed and the V_J4
    tap was added to the §12 test pads. The verifiers' directories
    (`~/tmp/usb-power-hub/verify-desk-1` to `-3`, 17 MB) and the task's own `desk-ds`,
    `desk-render` and `desk-venv` (79 MB) were deleted once the work was committed.
- **Learning.** Recorded in rules.md:
  - plot values come from vector paths;
  - render scrambled tables;
  - TI datasheets via LCSC `pdfUrl`, onsemi via the JLCPCB API;
  - Akizuki's `[code]` h1 prefix;
  - check fault injection against the hardware;
  - numeric pass items;
  - the user's Devin rule.
- **Residual risks.**
  - The OP07 mirror loop's stability into the 645 pF gate is unknown until bring-up.
  - MCP3208 INL at 3.3 V is typical only.
  - The CH335F outline and pin map are unknown (OI-24).
  - KiCad is not installed on this box.
- **Commit.** `1d43f4d`.

## 2026-11-04 - MCU alternatives survey (issue #3)

- **Request.** The user asked 「このPGAてさ生のRP2040より高くない?」, then 「別のマイコンにしようかな」,
  「候補を5つ出して」 and 「Issueにしといて」.
- **Finding.**
  - Price: the PGA2040 is ¥1,680; a bare RP2040 is ¥160 at Akizuki and $1.10 at LCSC.
  - Every USB MCU queried is Extended at JLCPCB: RP2040, RP2350A, CH32V203C8/K8, STM32F072CB,
    STM32G431CB, CH552T, ATmega32U4 and CH32V305RB. The bare RP2040 is therefore blocked by
    D22, not by price.
  - The flash W25Q128JVSIQ (C97521) and the crystal C9002 are Basic.
  - The RP2350's core regulator needs a polarity-marked inductor. The recommended part,
    AOTA-B201610S3R3-101-T (C42411119), is Extended with JLCPCB stock 1, and Akizuki has
    none. Its "Hardware design with RP2350" guide warns that the inductor's orientation
    matters.
  - Akizuki's RP2350A 実装基板 (131106, ¥450) brings every pin to 2.54 mm.
  - Within D13/D22, only the ESP32-S3-WROOM-1 module (117256, ¥800) remains, and it has no
    PIO.
- **Recommendation.** A bare RP2040 with one exception to D22, otherwise keep the PGA2040.
  The user decides in issue #3. The PGA2040 is not to be bought before that.
- **Verification.** Data read on 2026-11-04 with `tools/jlc_stock.py`, Akizuki product and
  search pages, and the LCSC C2040 page. Nothing in the design changed.
- **Incident.**
  - Clicking Akizuki's 「かごに入れる」 in Chrome was refused by the permission classifier
    (real-world transaction). The user adds items to the cart.
  - An `rm -rf` of the task's `~/tmp/usb-power-hub/rp2040-price` was denied. It is left for
    the user.
- **Commit.** This journal entry only.

## 2026-11-04 - RP2350A review (issue #3)

- **Request.** The user asked 「RP2350Aにしようか」, then 「Devinに作業させてSWE-2 Max」.
- **Devin.** SWE-2 Max extracted 65 facts (A–L) from the RP2350 datasheet (2025-07-29),
  "Hardware design with RP2350" (2024-10-15), Akizuki 131106 and the JLCPCB API. Its output is in
  `~/tmp/usb-power-hub/devin-rp2350/`. Claude checked every fact used in the result against the
  PDFs: the inductor specification, external DVDD (p.451), E9 and its stepping, 5 V tolerance,
  27 Ω, CHIPID, and RPD. The pull table's text extraction is scrambled, so RPD was rebuilt from the
  column order. Devin's own `-table` quote gives the same values.
- **Finding.** The RP2350's 1.1 V core supply cannot be met within D13/D22.
  - The on-chip regulator needs a polarity-marked, shielded 3.3 µH inductor. The JLCPCB pool has
    no Basic one. The recommended AOTA-B201610S3R3-101-T (C42411119) is Extended, with stock 1.
  - An external 1.1 V supply is allowed, but no Basic regulator makes it. The 1.1 V LDOs at
    JLCPCB are Extended or out of stock. Akizuki's TA4800AF covers 1.5–9.0 V only.
  - Akizuki's 131106 breakout cannot meet the regulator layout, because of its 2.54 mm headers.
  - RPD at 3.3 V is 36–113 kΩ, so the 10 kΩ hold pull-ups give 2.54 V against the 2N7002's
    2.5 V maximum threshold.
- **Recorded.** Issue #3 comment (issuecomment-6618242801). Nothing in the design changed. The
  user still decides between #1 (bare RP2040), #5 (bare RP2350A) and the PGA2040.
- **Investigation.** Devin read only the first 50 hits of its fuzzy inductor search. Re-running
  the search with `componentLibraryType: "base"` settled it, and that filter is now in rules.md.
  Before the summary, Claude had noted that Devin's tool files `pdfgrep.py` and `run_jlc.py` did
  not exist. A listing shows both files exist, so the note is withdrawn.
- **Commit.** This journal entry and the rules.md entry.

## 2026-11-04 - D29: a bare RP2040 replaces the PGA2040 (issue #3)

- **Request.** The user accepted a larger redesign (「いいよ、大きな設計変更になってもいいよ」)
  and chose 「素の RP2040 (推奨)」.
- **Decision.** D29 (user): the MCU is a bare RP2040 (C2040, Extended, LQFN-56), machine-placed
  by JLCPCB, the one exception to D22. It replaces D23's PGA2040; D23's ADC choice stands.
- **Design.** Rev0.4 §6.5 adds U1's support circuit after Raspberry Pi's minimal design:
  - U8 W25Q128JVSIQ (C97521);
  - Y1 C9002 with 2 × 15 pF C0G (C1548) and 1 kΩ in XOUT;
  - 27 Ω per USB line as 22 Ω (C25092) + 5.1 Ω (C25197), because no 27 Ω is Basic;
  - 100 nF per power pin and 1 µF at VREG_VIN and VREG_VOUT; SW3 to QSPI_SS through 1 kΩ;
    RUN to V3V3 through 10 kΩ; TESTEN to GND;
  - test pads on DVDD, RUN and one GPOUT pin.
  Machine-placed types went from 35 to 40 (39 Basic + C2040).
- **Desk checks.**
  - C9002 is rated for C<sub>L</sub> 20 pF and runs at ≈ 10.5 pF. The pull is ≤ 119 ppm at
    C1 = 5 fF and ≤ 509 ppm at worst (20 fF, tolerances included), against the 1000 ppm the
    RP2040 tolerates.
  - Start-up margin is 0.625 × the reference design's.
  - USB_VDD has 0.116 V to spare at V3V3's 3.251 V minimum.
  - DVDD draws ≤ 16.6 mA against the 100 mA on-chip regulator.
- **Studies.**
  - Placement: 85 × 35 mm needs 3,518 mm² at K = 1.0 (was 3,780). 100 × 72 mm holds to
    K = 1.74.
  - Cost: Economic is 20,674–21,154 yen for 2 units (was 21,883–22,843), with one Extended
    feeder fee of $3.07. X-ray inspection (2 × $1.64) is likely and not included.
  - The cost check now admits only approved Extended codes (`APPROVED_EXTENDED`), and a new
    test shows an unapproved one is caught.
- **Verification.**
  - Rubric: `.claude/goal-loop/rp2040-bare/rubric.md`, C1–C8, graded by rubric-verifier
    (sonnet).
  - Round 1 failed C3: the calc script printed figures the document did not quote (reset hold
    2.705 / 2.887 V, BOOTSEL DVDD 14.7 mA, the 2 fF and 10 fF pull points, the 9.5–12.5 pF
    sweep, a 0.281 V margin).
  - Round 1 also failed C5: parts.md's "1 nF / 10 nF" row held two codes, so 39 rows stood
    for 40 types.
  - Both were fixed, and round 2 passed all eight criteria.
  - Calc script exit 0; placement study 15 tests OK; cost estimate 12 tests OK. Afterwards no
    runner process was left.
- **Investigation.**
  - The verifier reported that `grep $'\r'` finds no CR in Git Bash.
  - Confirmed on a one-CRLF file: `grep -c` printed 0; `grep -U -c` and Python's byte count
    both gave 1.
  - This change set was also byte-counted with Python: 0 CR.
  - Rule added.
- **Incident.** A heredoc edit of the calc script lost a doubled backslash again (a ValueError
  before anything was written). Every later edit went through a script written with the
  Write tool. Existing rule updated.
- **Residual risk.**
  - C9002's start-up (ESR 80 Ω against 50 Ω) and its pull. Fallback: ABM8-272-T3, a second
    Extended part, which needs the user's decision.
  - The reduced-ePad land (G20).
  - Whether Economic PCBA accepts the 0.4 mm QFN.
  - The MCP3208's INL.
  - HS through the modules (OI-26).
- **Purchases.** The PGA2040 is not needed. CH335F × 2 is still needed (OI-24).
- **Commit.** `5e97c73` (design); this entry and the rules.md update follow.

## 2026-11-04 - D30: leaded HASL instead of ENIG; ship by OCS Express (issue #4)

- **Request.** Asked about the JLCPCB manufacturing cost, the user wrote 「ENIGいらないよ、」.
  Claude named the risk (HASL is not flat; U1 is a 0.4 mm-pitch QFN with an ePad, D29) and
  offered three finishes; the user selected 「有鉛 HASL (推奨)」. For shipping:
  「UPSじゃなくていい」.
- **Decision.** D30 (user): leaded HASL. Shipping in the cost estimate: OCS Express, the
  cheapest quoted ($7.23; UPS $9.79). An order option, not a design decision.
- **Change.**
  - Rev0.4 §10 D30 row and change-log row.
  - `CLAUDE.md` §9, §10.3, §10.4 and D1–D30.
  - REQ-MECH-01, REQ-MFG-01, product.md §9 (not RoHS).
  - New V-MFG-03: U1's pins under ≥ 10× magnification, V3V3 and DVDD ≥ 100 Ω to GND
    before power-up.
  - Cost estimate: `PCB_FINISH`, `SHIP_PLAN` and the README figures.
- **Result.** The Economic order is $55.69 = 8,910 yen (was $75.65). The 2 units come to
  17,480–17,960 yen with the Akizuki parts (was 20,674–21,154). D30 saves $19.96, 3,194 yen.
- **Investigation.** JLCPCB's blog, re-read with curl, says Standard is forced by a
  thickness / mask colour / finish combination outside the Economic options, but it lists
  no options. So Economic eligibility stays unconfirmed, as it was with ENIG.
- **Also corrected.** Two cost README figures had gone stale with D29: the exchange-rate
  sensitivity (it said ±320 yen, now ±280 yen per ±5 yen/USD) and the import-tax figures.
- **Verification.**
  - Rubric `.claude/goal-loop/d30-hasl/rubric.md`, C1–C6, graded by rubric-verifier
    (sonnet). All six passed on the first round.
  - The rubric named a `PKG` table, but the script's table is `COURTYARD`; the verifier
    found the right table itself.
  - Cost estimate exit 0, 12 tests OK; calc script exit 0; placement tests 15 OK.
- **Residual risk.** HASL bridges or opens at U1 (V-MFG-03), and the Economic eligibility of
  the finish combination.
- **Commit.** `72756ad` (design); this entry follows.

## 2026-11-04 - D31: bare CH335F (C5137013) instead of the Akizuki module (issue #5)

- **Request.** Asked what to buy from Akizuki, the user asked 「ええ、CH335FはLCSCに在庫無いの?」
  and 「こんなモジュール実装するのデカくない?」. Claude offered the bare chip against the module;
  the user selected 「IC 単体にする (推奨)」.
- **Decision.** D31 (user): U6 is the bare CH335F, QFN-28 4 × 4 mm, LCSC C5137013, Extended
  (4,937 in JLCPCB's pool on 2026-11-04), machine-placed. The second exception to D22. It
  replaces D15's module AE-QFN28-DIP(CH335F) (g129556).
- **Change.**
  - Rev0.4 §6.6 (U6 support circuit from the WCH CH334/335 datasheet V2.5), fact 19, the
    VDD33_HUB net, G21, the D31 row; D15, D22, D28, D29, D30 amended; OI-24 closed.
  - Calc script: V5 margin, U6 dissipation, the rejected 3.3 V feed.
  - Placement study: the module leaves, R_HUB holds U6/Y2; a 16th test corrupts R_HUB.
  - Cost estimate: C5137013 queried alone (one request, not a full `--fetch`), approved as
    the second Extended exception; one header strip per board.
  - product.md, verification.md (V-MFG-03 covers U6), parts.md, CLAUDE.md, README.
- **Result.**
  - Machine-placed types 40 → 41 (39 Basic). No new passive type.
  - Hand-soldered area 2,198 → 1,806 mm²; 85 × 35 mm needs 3,332 mm² at K = 1.0 (was 3,518).
  - Economic order $61.01 = 9,761 yen (was $55.69). 2 units with the Akizuki parts:
    17,421–17,661 yen, 59–299 yen less than with the module.
- **Desk-check finding.** V5's operating range with the internal LDO (4.5–5.25 V) equals
  V5L's design range: zero margin at both ends, and the 5.5 V USB-C corner sits at V5's
  absolute maximum. Not new with D31 (the module had the same chip on the same rail).
- **Incident.** A CR check written as `c=$(grep -U -c $'\r' "$f")` reported a CR on every
  line of all 15 files. Python's byte count gave 0. Cause, verified on a 3-line test file
  with one CRLF line: inside `$(...)` this Git Bash drops the literal `$'\r'`, so grep got
  an empty pattern (`${#p}` printed 0 inside, 1 outside). Rule updated.
- **Verification.**
  - Rubric `.claude/goal-loop/d31-bare-ch335f/rubric.md`, C1–C8, graded by rubric-verifier
    (sonnet). All eight passed on the first round; it re-read every CH335F pin number and
    figure from the datasheet pages and the package drawing.
  - Calc exit 0; placement exit 0, 16 tests OK; cost exit 0, 13 tests OK; 45 REQ IDs all
    covered.
- **Residual risk.**
  - Two 0.4 mm-pitch QFNs with ePads on leaded HASL (V-MFG-03).
  - U6's land is drawn by hand from the §5.6 drawing (G21).
  - The zero V5 margin at the USB-C corners.
  - Economic PCBA eligibility; X-ray may be charged for two leadless parts.
  - HS through one USB-C module per path (OI-26).
- **Purchases.** The CH335F module is no longer needed.
- **Commit.** `4475bd6` (design); this entry and the rules.md update follow.

## 2026-11-04 - P0 of issue #6: D32 KiCad-first workflow, D33 module headers, KiCad skeleton

- **Request.** The user: 「いったんローカルでKiCadで完成まで目指してそのご、EasyEDAにインポートしよう」.
  Recorded as D32 (user, amends D2). Tracking issue #6, phases P0–P6.
- **Decision D33** (Claude, delegated). PH-1x40SG headers (g100167, ¥35 per strip), soldered,
  no sockets. The insulator is 2.50 ± 0.2 mm, so ≥ 2.30 mm, which leaves ≥ 0.80 mm above a
  1.5 mm part under a module. This closes the OI-23 remainder.
- **Findings from the drawings.** Reading the module and receptacle drawings
  (AE-USB2.0-TYPE-C, Hirose CX70M-24P1) for the header height found three defects:
  - the study's under-module rectangle sat under the mid-mounted receptacle, which hangs
    below the module;
  - the area bound's credit (130 mm² per module) was a layout choice, not the most
    favourable space (230.2 mm²), so "3,332 mm² at K = 1.0" was not a lower bound;
  - the cost estimate's header count left out the 4 mechanical pins of each module.
- **Fix.**
  - One 19.0 × 3.4 mm strip per module, checked against the receptacle, its pins, the shell
    tabs and the insulators.
  - The bound is now 2,931 mm² at K = 1.0 (0.99 × 85 × 35) and exceeds 85 × 35 from
    K = 1.025.
  - 44 header pins per board and 3 strips for 2 units. Economic total 17,456 yen; D31 delta
    corrected to −24 to −144 yen.
  - History is labelled, not overwritten.
- **KiCad skeleton.** `design/ecad/scripts/make_project.py` writes `design/ecad/source/`:
  - JLC04161H-7628 stackup, HAL SnPb, 1.6 mm, 100 × 72 mm outline;
  - the §5.3 rules, and the Default and USB_HS (0.31 / 0.15) net classes;
  - an empty schematic.
- **Incident 1: rules reset to defaults.** The first run's check failed with every rule and
  net class at KiCad's defaults (`min_clearance` 0.0). Root cause: SaveBoard in the same
  process rewrites `.kicad_pro` from pcbnew's cached project; a fresh-process probe showed
  the defaults. Fix: edit the project after the last SaveBoard, and check in a new process.
  `test_make_project.py` corrupts copies in 9 ways (plus one clean pass), and every
  corruption is named.
- **Incident 2: a rule from memory.** A draft rule said `kicad-cli` DRC exits 0 with
  violations. Before it was recorded, it was tested on a board with a deliberate edge
  violation: exit 0 without `--exit-code-violations`, 5 with it.
- **Verification.**
  - Rubric `.claude/goal-loop/kicad-p0/rubric.md` (C1–C9), graded by rubric-verifier
    (sonnet).
  - Round 1 failed C3: circuit §11 did not retract the old figure as a bound. Fixed; round 2
    passed all nine.
  - Study exit 0, 21 tests; cost exit 0, 14 tests; skeleton check PASS, 10 tests.
  - DRC: 0 violations, 0 unconnected, 0 parity. ERC: 0.
  - A re-run is byte-identical.
- **Residual risk.** Two facts are not on paper and are left to V-MECH-01: the module
  board's thickness and the receptacle's 1.06 mm front overhang. The rules in the skeleton
  are starting values, not JLCPCB's current capabilities.
- **Commit.** `8b8dded` (design); this entry and the rules.md update follow.

## 2026-11-04 - P1 of issue #6: project symbol and footprint library

- **Request.** The user: 「P1へ」 (the second phase of D32, issue #6).
- **Result.** `design/ecad/libraries/` holds:
  - `library.json`, the parts register: 31 entries with pins, land facts and datasheet pages;
  - 31 flattened symbols;
  - 28 footprints, 20 KiCad stock and 8 generated: U1 (G20), U6 (G21), the three Kelvin
    shunts, F1, U5 and the USB-C module.

  `make_libraries.py` writes it, `check_libraries.py` measures it against the register's
  datasheet facts only (never the generator's `params`), and `test_check_libraries.py`
  corrupts copies in 18 ways.
- **Incident 1: nothing loaded.** Every generated footprint and the symbol library failed to
  load: `FootprintLoad` returned None. Root cause: `sexpr.py` quoted node heads. Fix: heads
  bare. Verified: all files loaded and the check passed.
- **Incident 2: a misread figure.** `parts.md` gave the RP2040 pad as 0.20 × 1.175 mm.
  Reading Figure 167 again showed that 1.175 is the corner distance (3.875 − 2.70); the pad is
  0.875 mm long. Corrected, and a side-span check was added.
- **Incident 3: the DRC parser expected English.** It parsed English messages, but
  `kicad-cli` prints Japanese here. Fixed by parsing the net names.
- **Incident 4: CRLF (verifier round 1, C9 fail).**
  - The stock copies kept KiCad's CRLF. The verifier simulated the `eol=lf` checkout: 27
    byte-copy FAILs.
  - Fix: write copies LF, compare against KiCad's file read as LF, and reject CR in the
    library (`check_line_endings`). A new test puts KiCad's CRLF back and must fail.
  - Verified on a `git checkout-index` export of the staged tree: 1941 checks, PASS.
  - The same round found the mounting holes and the TSL1 derived land missing from
    `parts.md`; both were added.
- **Verification.**
  - Rubric `.claude/goal-loop/kicad-p1/rubric.md` (C1–C9), rubric-verifier (sonnet).
  - Round 1 failed C9 (above).
  - Before round 2, the wording of C5, C7 and C8 was aligned with the documented contract: the
    CH335F rotation note, R_H joined by its electrode, and LF normalization.
  - Round 2 passed all nine. Its ungraded remark, the CH335F pad reach (0.35 mm past nominal,
    0.30 mm past maximum), was corrected; the check and the 19 tests were re-run.
- **Residual risk.** These rest on less than the part's own drawing (listed in `parts.md`,
  "Symbols and footprints"):
  - the AMS1117 tab;
  - the AOS SOT-23 proxy;
  - the NCD0805R1 cathode;
  - the BLM18 proxy;
  - the TSL1 derived land;
  - the mounting-hole screw (OI-5);
  - the passives, deferred to P2.

  No land is proven on a board or in the JLCPCB placement preview.
- **Commit.** `db6da2a` (library); this entry and the rules.md update follow.

## 2026-11-04 - P2 of issue #6: schematic captured, checked against the capture list (D34)

- **Work.** The Rev0.4 schematic is captured in KiCad 9.0.8: six sub-sheets, 294
  components, every passive bound to a Basic part.
  - `CIRCUIT_DESIGN_Rev0.4_netlist.md` is the capture list.
  - `make_schematic.py` writes the schematic from it.
  - `check_schematic.py` compares the list with the register, §6.2, parts.md, ERC and the
    exported netlist: 3928 checks.
  - `test_check_schematic.py` corrupts copies in 18 ways.
- **D34 (Claude, delegated).** Capture needed values, and their desk check
  (`_calc.py`) changed three circuit details:
  - the LM393s move to V12F (LM393/D note 1: an input's maximum is its supply; −0.54 V of
    margin on V5L);
  - Q13's gate sits behind 100 kΩ (its 630 pF on DIS_x took 10.0 µs of the 10 µs
    turn-off);
  - the comparators take TH_REF on +; the OC tolerance becomes 1.110–1.221 A at 25 °C.
- **Incident 1: the exported net class is always "Default".** The checker read the class
  from the exported netlist, and every net came back "Default". Root cause: kicad-cli 9.0.8
  writes `(class "Default")` even with `netclass_patterns` or explicit assignments in
  `.kicad_pro` (tested both ways). Fix: resolve classes with pcbnew's
  `GetEffectiveNetClass`, which gives USB_HS for `USB_A_N`. Verified by a negative test that
  breaks the pattern.
- **Incident 2: a checker crash looked like a failure.** A negative test (an order missing
  from the passive table) made `check_schematic.py` exit with a KeyError traceback, not a
  FAIL line. Fixed with lookups that report a FAIL. A test that only checks for a non-zero
  exit would have passed it.
- **Incident 3: a header parse.** Adding an intro paragraph to parts.md's Passives table
  made the checker read the header and separator rows as data. It now reads columns by
  header name.
- **Finding: OI-32 (blocking).** J1 has about 260 µC of capacitance at plug-in with no
  inrush limit, against USB 2.0's 10 µF. Recorded, not fixed: it needs its own decision.
- **Verification.** Rubric `.claude/goal-loop/kicad-p2/rubric.md` (C1–C8), rubric-verifier
  (sonnet), round 1: all eight pass. The verifier checked all 803 pins with its own
  parser, made two corruptions of its own, and both failed as meant.
- **Residual risk.** Not settled on paper:
  - LM393 power-up with TH_REF ahead of V12F (≤ 0.19 mA into an unpowered input);
  - the OFF bypass gates' leakage (−1.08 V bound, −80 mV typical);
  - the green LED's current;
  - CJ431 stability with no capacitor.

  Each is now a bring-up item in verification.md. The cost estimate is not re-run for D34.
- **Commit.** `d1c9fa1`.

## 2026-11-04 - D35: J1 soft start, closes OI-32 (issue #7)

- **Symptom.** OI-32, found at capture (P2 of #6): J1's VBUS fed V5L directly, so 78.6 µF
  that follows V5L charged from the host with no limit, 294 µC at plug-in (5.9 × a 10 µF
  load's 50 µC). P2's journal entry said "about 260 µC"; the calc showed that counting
  every rail at 5 V overstated it (393 µC) and that the true figure, with each rail at its
  own voltage, is 294 µC.
- **Decision.** The user accepted the recommended fix (「OKお願いします」); Claude set the
  values. Q53 AO3401A, source VBUS_J1, drain V5L; R34 33 k gate → GND; C35 100 nF
  gate → drain (Miller); C36 + C37 2 × 1 µF gate → source; TP14 on VBUS_J1. No new part
  type.
- **Design reasoning.** Without the gate-source capacitors, C35 would hold the gate at 0 V
  at the plug-in step and the FET would turn fully on. C_GS ≈ 20 × C_M keeps the step at
  −0.317 V (1.58 × inside V_th min). R·C_M = 3.3 ms keeps hold-off plus ramp ≤ 30.4 ms,
  inside USB's 100 ms attach window.
- **Incident: a source named from memory.** The first draft cited "TI TPS2553-Q1 §10.2" for
  the 10 µF ∥ 44 Ω rule. A search of this session's transcript showed that the excerpt came
  from TI SLVS798G (TPS2062A) and NXP AN11392, as web-search results. Fixed before commit.
- **Incident: a diagram branch moved.** The new §3.1 diagram line put `┬` at column 44; the
  branches below it sit at 45. Comparing with HEAD's line by script found it; fixed.
- **Verification.** make_schematic 3992 checks PASS; ERC 0 on 7 sheets; all tests OK.
  Rubric `.claude/goal-loop/oi-32-d35/rubric.md` (C1–C7), rubric-verifier (sonnet), round 1:
  all pass. The verifier parsed the netlist itself (VBUS_J1 and GJ1 node sets exact) and
  diffed the calc output against HEAD (only the 11 D35 lines added).
- **Residual risk.** Not settled on paper: the MAU104's start-up current (passed by Q53 once
  V5L is past the MAU104's start) and U6's time to attach. Both are in V-PWR-03. The
  capacitive inrush bound, 152 mA, is above the 114 mA of USB's 44 Ω; it is a slow ramp,
  not a surge, and V-PWR-03 records J1's peak. The cost estimate is not re-run for D35.
- **Commit.** `30514a6`.

## 2026-11-05 - P3 of issue #6: Rev0.4 placed on the 100 × 72 mm board

- **Goal.** Place all 300 components of Rev0.4 (100 × 72 mm, 4 layers, Top only), with
  four M2 corner holes and three fiducials. The board is generated from the schematic's
  netlist and `design/ecad/PLACEMENT_Rev0.4.md` by `make_pcb.py`. `check_pcb.py` checks it
  against that document, the capture list's notes and DRC. The user's go-ahead was
  「消していいよ、P3へ」.
- **Incident: notes that said "at" without being near.** The first placement's notes claimed
  "at X" and "next to X" for parts up to 12.5 mm away. The capture list's "at U1 pin N" notes
  were up to 6 mm off, because U8 blocked U1's west side.
  - Root cause: notes were written as intent and never measured.
  - Fix: a defined vocabulary. "at X pin N" means a same-net pad within 3.0 mm, centre to
    centre; "at / next to / after X" means courtyards within 3.0 mm. check_pcb's check 11
    measures every note.
  - The MCU was placed by hand: U1 at rot 90, its decouplers in one column at x 36.75, U8
    to the south-west, Y1 to the east.
  - Notes were reworded where the geometry cannot meet them. A 3225 crystal's signal pads
    are diagonal, and a SOT-23 cannot be within 3 mm of both CC pins.
- **Incident: silk outside a courtyard.** U1's pin-1 triangle lies outside its courtyard.
  C12 gave DRC silk_over_copper and silk_overlap; it was moved clear of the mark.
- **Incident: check_libraries' sandbox broke.** Once the project board carried footprints,
  `board.Remove` followed by `FootprintLoad` raised AttributeError (KiCad 9.0.8). The fix
  cuts the nodes from the copy's text before LoadBoard.
- **Incident: a test helper's wrong index.** `sexpr.loads` returns the top node, and the
  tests used `tree[0]`. The broken boards they wrote made check_pcb crash. The index is
  fixed, and check_pcb now FAILs when a board does not load.
- **Incident: make_pcb was not deterministic.** Each run gave a new SHA-1, with 74,718 diff
  lines between two runs.
  - Root cause: SaveBoard sorts footprints by UUID, and new items get random UUIDs.
    make_project.fix_uuids renumbers by position, so it kept the varying order.
  - Fix: `pcbnew.KIID.SeedGenerator(6)` before building.
  - Check: three runs, and make_project -> make_pcb, gave SHA-1 023b43a6….
- **Smaller changes.**
  - The module footprint's side silk stops 0.5 mm short of the receptacle edge
    (silk_edge_clearance).
  - The corner holes are described as 2.2 mm M2 clearance holes for the case's heat-set
    inserts (D21), not as inserts.
  - `design/ecad/README.md` is new. The capture list had pointed at it since P2.
- **Verification.**
  - make_pcb: 12,694 checks PASS. DRC: 0 violations, 0 parity items, 499 unconnected (not
    routed).
  - Tests OK: test_check_pcb 24, test_make_project 11, test_check_libraries 19,
    test_check_schematic 19. check_schematic 3992 PASS, check_libraries 1957 PASS.
  - Rubric `.claude/goal-loop/kicad-p3/rubric.md` (C1–C8), rubric-verifier (sonnet),
    round 1: all pass.
  - The verifier measured 245 notes with its own code (the largest pin distance 2.959 mm,
    the largest courtyard gap 2.580 mm). The MAU104 is ≥ 11.85 mm from the analog parts.
  - The verifier's own corruption (U8 turned 90° in both board and document) failed with
    13 named items.
- **Residual risk.**
  - U1's west-side escapes (QSPI, the decoupler column, the USB pair's turn) may need vias.
  - The 33.1 × 30.5 mm front ends are not proven routable.
  - The heights under the modules are planning values (V-MECH-01).
  - Rubric C6 needed the verifier to read the module overhang as allowed; see rules.md.
- **Commit.** `b486758`.

## 2026-11-06 - P4 of issue #6: Rev0.4 routed, D36 L3/L4 rule

- **Goal.** P4: route the placed board to DRC 0 errors and 0 unrouted, with the USB pairs,
  the Kelvin taps, the analog blocks and the zones as CLAUDE.md 5 asks.
- **Decision D36** (user, 2026-11-06, 「交差のみ許可 (推奨)」).
  - With L4 closed to signals in the analog blocks, the router left 76–78 connections
    unrouted.
  - New rule: in the analog blocks, L3 and L4 signals may cross at ≥ 45° but never run along
    each other.
- **Design.** Each piece has one job:
  - `ROUTING_Rev0.4.md` holds everything drawn by hand: the plane, pairs, Kelvin taps,
    trunks, escapes, GND fanout, pours, classes, keepouts, router layer preferences and
    costs, and the patch;
  - `route.py` applies it;
  - `autoroute.py` runs Freerouting 2.5.0 on a jar and a JRE pinned by SHA-256, and commits
    the session with its digests;
  - `make_pcb.py` refuses a session made from other input, then applies the session, the
    patch and the zones;
  - `check_routing.py` checks DRC, the pairs, the Kelvin taps, D36, the class layers and the
    port-path copper.
- **Root causes found on the way.**
  - The CLI scoring flags were ignored; the DSN autoroute_settings work.
  - The port check's "no copper path" was a singular matrix caused by an island.
  - The 45° comparisons failed on float error.
  - J5's paste-less pad is CONN, not SMD.
  - VSUP_A's 1.0 mm track came within 0.415 mm of pair A, so its first 0.5 mm is now 0.60 mm.
  - V5L got its own 0.31 mm class: IPC-2221 needs 0.306 mm on an inner layer for 0.277 A at
    ΔT 10 °C.
- **Sweep** (DRC unconnected / analog parallels):

  | Setting | Unconnected | Parallels | Note |
  |---|---:|---:|---|
  | default | 6 | 0 | 4 other DRC errors |
  | layer cost 2.0 | 6 | 13 | |
  | cheaper rip-up | 11 | 0 | |
  | **via_costs 100** | **2** | **3** | 0 other DRC; adopted |

  The official run took 17 min (56 passes) and reproduced the trial byte for byte, apart
  from the session name.
- **Patch.**
  - ADC_CC2 and EVTG_L_A, left unrouted, are drawn: ADC_CC2 81 mm with 2 vias, EVTG_L_A on
    F.Cu.
  - ADC_DIN_3V, INP_L_B and HOLD_L_B are redrawn so they cross at ≥ 45°.
  - A scratch grid A* found the paths; DRC proved them.
- **Verification.**
  - make_pcb.py twice: 44 files hashed, byte-identical.
  - check_pcb.py: 12,694 checks PASS.
  - check_routing.py: 3,945 checks PASS, 0 unconnected, 187 In2/B.Cu crossings, ports A
    29.76 / B 35.25 mΩ.
  - kicad-cli DRC: 0/0/0.
  - Tests OK: test_check_routing 16, test_check_pcb 24, test_make_project 11,
    test_check_libraries 19, test_check_schematic 19.
  - Rubric `.claude/goal-loop/kicad-p4/rubric.md` (C1–C8), graded by rubric-verifier
    (sonnet):
    - round 1 failed C4(d): the 0.20 mm V5L track into U6 pin 26 carries 85 mA at the pin's
      own width, which the criterion had not excepted. It is now in the Widths table and the
      criterion.
    - round 1 failed C8: a stray empty `en/` left by Freerouting, now removed.
    - round 2 passed.
- **Residual risk.**
  - D36's 187 crossings take L3's return off L4 for each crossing's width. The effect is not
    computed (V-MEAS-01).
  - The HS pair impedance is D27's model value; the modules are OI-26's.
  - One GND net, with no quiet ADC tie.
  - The port voltage includes module wiring that is not known on paper.
  - The patch is bound to this session: a new session needs a new table.
- **Learning.** rules.md: "Freerouting 2.5.0" and "KiCad 9 routing checks".
- **Commit.** `b7a6c3b`.

## 2026-11-06 — #6 P5: silkscreen labels and the candidate manufacturing set

- **Symptom.** P4 left the board without CLAUDE.md §6 labels and no outputs existed
  ("no Gerber is exported"). The stock footprints' silkscreen was 0.12 mm, under JLCPCB's
  0.15 mm legend minimum.
- **What was done.**
  - Library: stock copies keep KiCad's bytes outside F.SilkS; each F.SilkS stroke is widened
    to 0.15 mm, and `silk_drop` leaves out the silk of TestPoint, R 0402 and C 0402 (non-polar,
    silk cannot keep 0.15 mm from their pads). check_libraries.py checks both (3,559 PASS).
  - Labels: 32 rows in `PLACEMENT_Rev0.4.md`, *Silkscreen* (title, Rev0.4, HOST, OUT A, OUT B,
    5V IN, every test pad's signal name; 5 leaders, 6 segments). `make_pcb.py` adds them after the session;
    `check_silk.py` checks JLCPCB's limits (≥ 1.0 mm, ≥ 0.15 mm, 1:6), association, clearance
    to pads, mask, edge, courtyards and other silk (2,522 PASS).
  - Outputs: `make_outputs.py` writes `manufacturing/working/rev0.4/` (Gerber zip with drill,
    JLCPCB BOM 254 parts / 41 lines, CPL, hand list 12, schematic and assembly PDFs, renders,
    ERC/DRC JSON, WIP manifest, SHA256SUMS); `check_outputs.py` reads it with its own parsers
    (3,278 PASS). The directory is ignored by Git (`.gitignore`, CLAUDE.md §2), so the set is
    regenerated, not committed; the manifest records the sources' SHA-256.
- **Root causes found on the way.**
  - check_silk.py first measured leader starts against the text box; the DRC in
    make_outputs.py then found TP8's leader inside its own glyphs (`silk_overlap`). Rule and
    test added (`test_leader_touches_its_label`).
  - check_libraries.py's DRC sandbox crashed (`SwigPyObject` in FootprintLoad) once the board
    held `gr_text`: `board.Remove()` of Edge.Cuts items; now stripped in the text.
  - Two older tests depended on the P4 board: test_check_pcb used C12's silk (now dropped,
    moved to C1), test_check_routing took the first In2 segment in file order (UUID order
    changed; it now takes the longest and copies its middle, since a copy ending on a via
    joins that via's net and is exempt).
- **Verification.**
  - make_pcb.py: source byte-identical on re-run; check_pcb 12,694, check_routing 3,945,
    check_silk 2,522, all PASS; DRC 0/0/0.
  - make_outputs.py twice: identical SHA256SUMS.
  - Tests OK: test_make_project 11, test_check_libraries 26, test_check_schematic 19,
    test_check_pcb 24, test_check_routing 16, test_check_silk 27, test_check_outputs 23 (two each added after the verifier noted untested bounds: label width and rotation, preview size and aspect).
  - Rubric `.claude/goal-loop/kicad-p5/rubric.md` (C1–C9), rubric-verifier (sonnet): round 1 passed C1–C9; it noted untested bounds (label width and rotation, preview size and aspect), and two tests each were then added.
- **Residual risk.**
  - The CPL's origin and angles are unverified until JLCPCB's placement preview
    (easy-stick 14.18); no DFM or part mapping has seen the set.
  - Pin 1 is shown only by the footprints' own marks; reference designators stay hidden.
  - The open issues of CLAUDE.md §11 stand; the set is not orderable.
- **Learning.** rules.md: "KiCad 9 silkscreen and manufacturing outputs".
- **Commit.** `7fca00e`.

## 2026-11-06 — #6 P6: EasyEDA import route researched, paused

- **Symptom.** P6 needs EasyEDA, which is not installed, and the user's account.
- **Findings** (EasyEDA Pro docs, read 2026-11-06):
  - The KiCad import supports "KiCad versions below 10.0" from KiCad's project archive. It
    rebuilds the copper pours, so the pours will differ.
  - The desktop half-offline and full-offline modes need no login, but both need a free
    activation file that is downloaded after registering.
- **Decision.** Not taken: the user stopped before choosing among web editor in their Chrome,
  desktop half-offline, or importing it themselves. The options are in issue #6, comment of
  2026-11-06.
- **Cleanup.** The other session's `freerouting.log` (105 MB) was deleted, with the user's OK.
- **Learning.** None verified yet; a pour comparison after import is planned.

## 2026-11-11 - #3 revisited: Akizuki now lists a 1.1 V LDO (XC6221B111NR-G)

- **Request.** The user: 「設計を見直してほしい。https://akizukidenshi.com/catalog/g/g129527/
  これとか良くない」.
- **Symptom.** Issue #3 and Rev0.4 §9 rejected the RP2350A on 2026-11-04 because "no Basic or
  Akizuki regulator makes an external 1.1 V". Akizuki listed one on 2026-11-11.
- **Findings** (all read 2026-11-11).
  - Akizuki g129527: Torex XC6221B111NR-G, 1.1 V LDO, SSOT-24 (4 pins, 1.3 mm pitch), ¥50,
    通販購入可能数 102, page release 2026-11-11.
  - Torex datasheet JTR03028-016a (Akizuki `/goodsaffix/xc6221-j.pdf`):
    - type B = no CE pull-down, C<sub>L</sub> discharge; accuracy code 1 at 1.10 V is
      1.0800–1.1200 V (±20 mV at I<sub>OUT</sub> 10 mA, 25 °C), not the ±1 % of Akizuki's
      table, which the datasheet gives only for V<sub>OUT</sub> ≥ 2.00 V;
    - load regulation 10 mV typical, 40 mV maximum (0.1–100 mA); I<sub>OUTMAX</sub> 200 mA;
      V<sub>IN</sub> 1.6–6.0 V; ±100 ppm/°C typical;
    - C<sub>L</sub> ≥ 4.7 µF for settings 0.80–1.15 V, C<sub>IN</sub> ≥ 1.0 µF;
    - SSOT-24 pins: 1 CE, 2 V<sub>SS</sub>, 3 V<sub>OUT</sub>, 4 V<sub>IN</sub>; 150 mW alone,
      500 mW on a 40 × 40 mm board. The outline drawing is not in this PDF.
  - RP2350 datasheet (build d126e9e, the 2026-11-04 copy): DVDD 1.05–1.16 V; an external
    1.1 V supply is allowed with VREG_FB to ground and VREG_VIN / VREG_AVDD still powered
    (p.451, Figure 21); the supplies may come up in any order (§6.1.8). RP2354A = the same
    die and pinout with a 2 MB W25Q16JV in the package.
  - Worst case by the limits: 1.080 − 0.040 = 1.040 V, 10 mV under the 1.05 V minimum; typical
    1.090 V. The datasheet gives no figure between 10 mA and the load, so the 40 mV is the
    only bound.
  - Core current through an LDO: hello_usb takes 14.7 mA at 3.3 V (48.5 mW) through the
    on-chip switcher; at an assumed 80–90 % efficiency that is 35.3–39.7 mA of DVDD, against
    ≤ 16.6 mA for the RP2040. The efficiency is an assumption, not a datasheet figure.
  - JLCPCB pool: C2040 RP2040 84,031, $1.0854; C42411118 RP2350A 6,171, $1.293; C41378174
    RP2354A 9,184, $1.2554 (9,584 in a query minutes earlier); C97521 W25Q128JVSIQ $2.2574;
    C42411119 (the RP2350 inductor) **738**, $0.3363, minimum 5 — it was 1 on 2026-11-04;
    XC6221B111NR-G and -MR-G: no exact match; C485147 TLV74311PDBVR 11,002. All Extended
    except C97521.
- **Root cause of the stale rejection.** Both reasons recorded on 2026-11-04 were catalogue
  and stock facts, and both changed within 7 days.
- **Fix.** None yet: the design is unchanged. The choice (keep the RP2040; RP2354A with this
  LDO, hand-soldered; RP2354A with the on-chip regulator and C42411119 as a third Extended
  part) is the user's, since D29 is a user decision. Rev0.4 §9's sentence stays as written
  until that choice.
- **Verification.** Product page fetched; datasheet pages 1–11 read as text; RP2350 statements
  re-read in the 2026-11-04 extraction; stock and prices from `tools/jlc_stock.py` and the same
  API's `componentPrices`.
- **Learning.** rules.md: "Decision records" (a catalogue or stock reason expires) and
  "Akizuki" (read a tolerance from the datasheet's order code).
- **Commit.** This journal entry and the rules.md entries.

## 2026-11-11 - #3 revisited: decision, RP2040 kept (D29 stands)

- **Decision.** The user chose 「RP2040 のまま (推奨)」 from three options: keep the RP2040;
  RP2354A with the XC6221 LDO (hand-soldered); RP2354A with the on-chip regulator and
  C42411119 as a third Extended part.
- **Fix.** Rev0.4 §9 no longer says the RP2350A cannot be powered from Akizuki or Basic parts.
  It dates the 2026-11-04 rejection and adds the re-review: nothing in product.md needs an
  RP2350; the LDO's worst case, 1.040 V, is 10 mV under DVDD's 1.05 V minimum; the core would
  draw about 35–40 mA from J1 (an estimate) and reopen D26; the saving is 2.09 USD per board
  before the LDO. No D number, because no decision changed.
- **Correction.** The option text shown to the user said "about 4 USD for 2 boards". That is
  2 × 2.09 USD before the LDO (¥50) and its capacitor; the net saving is lower. §9 states the
  gross figure and says what comes out of it.
- **Verification.** `check_schematic.py` after the edit: 3992 checks, 0 failed. Only §9's
  prose changed; `git status` showed that one file.
- **Residual risk.** None for the board: it is unchanged. Reopen if V-HOST-01 shows J1 short of
  current, or if the RP2040's supply (Extended C2040, 84,031 in stock) changes.
- **Commit.** This entry and the §9 edit; `949d944` and this commit are not pushed.

### Follow-up (same day): §9 trimmed after an advisor review

- **Symptom.** §9's re-review carried 1.040 V, 35–40 mA and 2.09 USD, which no committed
  script reproduces (rules.md, "Design documents": every derived number in a design document
  comes from one script). The claim "nothing in product.md needs an RP2350" had been made from
  CLAUDE.md's summary, not from product.md.
- **Fix.** §9 keeps dated catalogue facts, the user's words in full, and pointers to the issue
  #3 comment and this journal; the arithmetic stays in those two records. product.md was read:
  no requirement exceeds the RP2040's capability. A move would rewrite REQ-HOST-02 (serial
  from U8's unique ID), REQ-MEAS-03, REQ-BOOT-02 and REQ-MFG-05.
- **Verification.** check_schematic.py: 3992 checks, 0 failed, after the edit.
- **Learning.** Estimates for a rejected alternative go in the issue and the journal, not in
  the design document. The rule already stands in rules.md.

## 2026-11-12 - #6 P6: the pre-order gate (JLCPCB DFM, part mapping, placement preview, quote), nothing ordered

The user asked 「発注できる寸前まで頼むよ」 and signed in to JLCPCB and JLCDFM themselves. The task: run the
JLCPCB gate on the real files, assemble a release candidate, order nothing. Rubric:
`.claude/goal-loop/pre-order/rubric.md` (not tracked). Evidence is outside the repository
(`~/tmp/usb-power-hub/pre-order/`).

### Three defects the gate found

- **Symptom 1.** JLCPCB's part matching left BOM rows unselected. **Root cause.** P5 wrote one row per
  (LCSC, Footprint); C17734 (510 Ω) has two footprints, and rows that share a code are not
  auto-selected. **Fix.** One row per LCSC (40 rows), checked by `check_outputs.py`. **Verification.**
  Part mapping 40 of 40, 0 substituted, after re-uploading. The merged row still needs a hand tick
  after each *Process BOM & CPL*.
- **Symptom 2.** In the placement viewer every part sat off the board. **Root cause.** The Gerber and
  drill files carried KiCad's page origin; JLCPCB reads the CPL against the Gerber's origin. **Fix.**
  Auxiliary origin at the board's lower-left in `make_outputs.py`; `check_outputs.py` requires Edge.Cuts
  at (0, 0)-(W, H). **Verification.** The viewer; and 51,444 Gerber/drill coordinates of the old and
  new zip differ by one constant, within 1 µm, nothing else (`gerber-translation-check.txt`). JLCDFM
  had analysed the old zip, so its geometry results carry over by that comparison, not by a rerun.
- **Symptom 3.** With the KiCad angle in the CPL, the model's pin 1 sat 90 or 180 degrees from the
  board's pad 1 for 11 part classes. **Root cause.** The CPL angle is applied to JLCPCB's own model
  (easy-stick 14.18); this is the lesson `CLAUDE.md` §4.2 already names, now measured here.
  **Fix.** `design/ecad/jlcpcb_model_rotation.json`, per LCSC, read by the generator and the checker (a
  dead entry fails). **Verification.** The viewer, class by class, after the corrected CPL was
  uploaded (`JLCPCB_REVIEW.md` section 5). A first +180 on the LEDs was **wrong** (the anode went to
  pad 1) and was removed after the viewer showed it; only the viewer decided it.

### What the quote showed

- **$81.85 without shipping** against the estimate's $53.77 (without its $7.23 shipping), a gap of
  $28.08. The 0.25 mm via class alone adds $34.16 (a 4-Wire Kelvin Test and a minimum-via fee, added
  by the form itself, which also offers Plugged instead of Tented); the estimate did not know. The
  other lines net to -$6.08: component prices (-$6.85), small fees, and "Confirm Parts Placement"
  left off (-$0.45). Shipping read on the PCB form for the 0.24 kg PCB-only parcel: OCS Express $7.23, UPS $9.69, DHL $17.67
  (default), FedEx $20.81; the assembled parcel (556.50 g) is priced only in the cart.
- **DFM.** JLCDFM's Danger items are the 0.25 mm vias at exactly its 0.1 mm annular-ring boundary,
  through-hole-to-SMD distance (hand-soldered modules), 107 silkscreen/via pairs (vias plugged) and same-net
  via-to-pad spacing (145 pairs, none on different nets). Not explained: mask opening exposing a trace
  (4 Danger, 13 Warning), negative mask expansion (18), silkscreen to pad (2), fiducial (3), trace
  spacing (25). They are in the manifest's open gates.

### State at the end

- `manufacturing/releases/rev0.4/r01/`: the ten candidate files, `JLCPCB_REVIEW.md`, `SOURCING_CHECK.md`
  (PASS, 2026-11-12), `EASYEDA_IMPORT.md`, a `WIP` manifest and `SHA256SUMS.txt`. Not approved; no order
  number. CLAUDE.md §0 and §12 are updated; the open gates have owners (manifest, "Open gates").
- **EasyEDA import (D32): blocked.** EasyEDA Pro is signed out, and easyeda.com shows a terms modal. Both
  are the user's to answer. The archive for the import is prepared (SHA-256 `ae06a4ac...e727`).
- **Left in the user's JLCPCB account:** two auto-saved quote drafts (Projects > Quotes). The cart's one item
  is the user's older easy-stick quote, untouched.
- **Learning.** The first real upload found three defects that no local check could see, and a cost that
  an estimate had not priced. A checker proves only what it looks at: `check_outputs.py` now also checks
  the origin, the one-row-per-LCSC rule and the rotation table, each with a negative test.
- **Commit.** The one that adds this entry and `manufacturing/releases/rev0.4/r01/`; base `d054edf`. Not pushed.

## 2026-11-12 - #8 step 1: vias drilled at 0.30 mm, release candidate r02, the $34.16 via-class fee removed

- **Symptom.** r01's quote was $81.85 without shipping; $34.16 of it was the 0.25 mm via class, which
  makes JLCPCB's form add "4-Wire Kelvin Test" ($17.02) and "Min via hole size/diameter" ($17.14).
  The user asked to lower the manufacturing cost (「製造コストを下げて」, then 「試して」).
- **Root cause.** The design rules set the via at 0.45/0.25 mm. JLCPCB's standard class is
  "0.3mm/(0.4/0.45mm)"; a 0.25 mm hole moves the order into the dearer class.
- **Fix.** `make_project.py`: via drill 0.30 for both net classes and the board minimum, and a new
  `usb-power-hub.kicad_dru` with JLCPCB's hole figures (via hole to copper 0.20, via to via 0.20,
  PTH hole to copper 0.28, PTH ring 0.15, pad hole to pad hole 0.45; pcb-capabilities read 2026-11-12).
  The board minimums for hole clearance and hole-to-hole stay 0.25, because KiCad's DSN export sizes
  NPTH keepouts with min_hole_clearance (a first try at 0.20 changed the router input). `route.py`'s
  GND fanout keeps 0.20 mm to another via's hole and 0.25 mm to a pad's hole, from `make_pcb.py`.
- **Verification.**
  - Router input equal to the old one except the via's name (`450:250` → `450:300`); the 17-minute
    Freerouting run returned the old session with that name replaced (56 passes).
  - Board against `df5df08`: 2206 tracks, 356 via positions and pads, 300 footprints identical;
    holes now ≥ 0.30 mm (334 × 0.45/0.30, 22 × 0.60/0.30).
  - Gerbers against r01: every member identical except the PTH drill and map and the two poured layers
    (B.Cu, In2), whose difference is slivers under 6 µm wide (a 3 µm erosion leaves nothing). Refilling
    the old board reproduced its own fill, so the slivers come from the drill. BOM, CPL, ERC, DRC,
    schematic and assembly PDF byte-identical.
  - Checks: make_project, check_pcb (12694), check_routing with DRC (3945), check_silk (2522),
    check_outputs (2853), all PASS. Tests: test_make_project 16, test_check_routing 19 (new: 0.25 mm via
    drill, PTH ring below 0.15, via holes 0.15 apart, each FAILs DRC by name), test_check_pcb 24,
    test_check_silk 27, test_check_outputs 26, all OK.
  - JLCPCB: r02's Gerber uploaded to the quote form (03:38 JST): the form selected 0.3mm/(0.4/0.45mm),
    PCB $8.00, no Kelvin or minimum-via line, FR4 TG135 not forced to Tg155; with the stackup named, still
    $8.00. With r01's PCBA lines (identical BOM/CPL) the total is $47.69, and 16,482 yen for 2 units with
    the Akizuki parts and OCS Express (was 21,950 yen).
- **Changed the rubric once, openly.** C2 asked for byte-identical Gerbers; the zone-fill slivers made
  that the wrong test, so C2 now asks for item identity plus the 3 µm erosion (rubric text says why).
- **Decision recorded, reversible by the user.** r02 stays Rev0.4: no Rev0.4 board exists, and a new
  revision would change the silkscreen legend and so the copper identity. r02 supersedes r01.
- **Open.** JLCDFM has not run on r02 (the via ring is now 0.075 mm; needs the user's sign-in). One more
  auto-saved quote draft is in the user's JLCPCB account.
- **Learning.** In KiCad, a board minimum feeds the router export, so per-type figures belong in custom
  rules; and a drill change moves the zone fill by microns, so copper identity is proven item by item.
- **Commit.** The one that adds this entry and `manufacturing/releases/rev0.4/r02/`; base `df5df08`. Not pushed.

### Correction, same day (#8, after review of f640334)

- **Withdrawn claim.** f640334 (commit message, r02 manifest and review, cost README, rules.md, the entry
  above, the issue comment) said JLCPCB's form *selected* the 0.3 mm class from r02's Gerber. Not shown:
  the r01 quote's 0.25 mm class was clicked by hand ("Selects min via hole 0.25mm" in the session record),
  and a fresh form shows the 0.3 mm class by default. What is shown: 0.3 mm is the class r02's smallest
  hole (0.30 mm) allows, and with it the PCB is $8.00 with no Kelvin or minimum-via line and TG135.
  "Forced Tg155" was also too strong: r01's form showed TG135 under a notice saying Tg155 is auto-selected.
- **Added residual risks** (CLAUDE.md §3): the via ring went from 0.10 to 0.075 mm against JLCPCB's
  ±0.075 mm hole-position tolerance, and the ten ePad vias under U1 and U6 are larger, so the wicking
  risk V-MFG-03 inspects grows (Plugged covering limits it).
- **Learning.** A form's state after an upload is evidence of detection only if it differs from the
  form's default; compare with a fresh form before writing "selected by itself".
- **Commit.** The follow-up commit that adds this note.

## 2026-11-12 - #9: host profiler, a native Win32 Rust app (demo-verified only)

- **Request.** The user: 「PPK2のようなソフトウェアはRustでフレームワーク使わないネイティブアプリで頼むよ。
  デザインと機能はPPK2ライクでお願い値」. Built by a delegated agent from a brief that fixed the stream
  frame bit layout; reviewed and committed by the main session.
- **Constraint kept.** No code, name or artwork of the reference profiler: its licence allows use only with
  its maker's ICs. The app speaks only product.md 4.1/4.2.
- **Single owner.** The frame bit layout and the `CAL?` format were chosen with the app; product.md 4.1/4.2
  now records them (fields, flags, n ≤ 2800, CRC parameters and check value 0x29B1, sample time), so
  firmware follows the document, not the Rust source.
- **Review.** Re-ran `cargo test --release` (38 passed), `cargo build --release` and
  `cargo clippy --all-targets` (11 + 4 style warnings fixed, now 0), and a `--demo --screenshot` run
  (exit 0, both traces, lost data hatched). No profiler, cargo or rustc process left.
- **Not verified.** Serial I/O with a real board (no firmware), mouse handling in the running window, high
  DPI; "Save all as CSV" blocks the UI thread.
- **Commit.** `4aa7e29`. Not pushed.

## 2026-11-12 - #8 step 2 / #10: Rev0.5 planned and handed off to a new session

- **Decision.** The user chose 「USB-C直付けのみ (推奨)」: C2765186 receptacles, machine-placed, replace the
  four Akizuki modules, as Rev0.5; the #10 data-line taps (1 kΩ to GPIO26–29) go into the same revision.
  Then the user asked to update the issue and hand off (「Issue更新して別セッションに引き継ごうか」), after
  repeated `server_error` stream stalls in this long session.
- **Handoff.** The plan, the land read from the maker's drawing, placements, taps, work order and risks are in
  #8 (issuecomment-6811380017); #8's body marks step 2 decided; #10 points to it. Nothing in the repository
  changed for Rev0.5.
- **Correction before it reached a file.** The working notes put both D+ pads of C2765186 in the middle.
  Enlarging the drawing's label row showed B7, A6, A7, B6 at −0.75, −0.25, +0.25, +0.75: D−, D+, D−, D+,
  the usual 16-pin order. The handoff carries the corrected table.
- **Found while writing it.** The NPTH pegs sit 0.165 mm (computed from the drawing) from the VBUS and GND
  pads, below the board's 0.25 mm `min_hole_clearance`: a scoped rule backed by JLCPCB's NPTH figure, not a
  global change.
- **Learning.** Read a connector's pin order from the drawing's own labels, enlarged, before writing it down;
  a remembered order is not evidence.
- **Commit.** The one that adds this entry. Not pushed.

## 2026-11-13 - #8 step 2 / #10: Rev0.5 captured, placed, routed and exported (release candidate r01, nothing ordered)

- **Request.** The user pasted the #8 handoff (issuecomment-6811380017): J1-J4 become machine-placed C2765186
  receptacles (D37, 「安価に製造できないとね、製造コストを下げて」, 「USB-C直付けのみ (推奨)」) and issue #10's data-line
  taps join the same revision (D38, 「可能ならデータ線部分もロジックアナライズできると USB接続機器を開発するのに便利なんだけど、
  出来る?」). Work order: rename, documents, capture, library, placement, routing, outputs, release candidate. The
  JLCPCB gate (step 9) needs the user's sign-in and was not run. Nothing pushed, ordered or paid.
- **Library and capture.** The receptacle's land is the maker's drawing (read from its labels, enlarged), with
  one recorded deviation, the user's 「GND パッドを 0.035 mm 短く (推奨)」: A1 and B1 end 0.035 mm short so each NPTH
  peg keeps 0.200 mm from copper. `check_libraries.py` fails a mirrored pad order, a missing slot and a peg 0.15 mm
  from a pad. Taps R35-R38 (1 kΩ, C11702) join USB_A_P/N and USB_B_P/N to U1 pins 38-41 (GPIO26-29): 28 of 30 GPIO.
  304 footprints (300 at Rev0.4).
- **Symptom (routing).** The first Rev0.5 router session passed DRC and left U1's exposed pad no plane copper on its
  east side: a slot 5.04 mm long (ROUTING_Rev0.5.md, *Router*). The checker had no rule for the plane, so nothing
  flagged it.
- **Root cause.** Freerouting knows no antipad. On L2 a via of a net other than GND stands in an 0.85 mm antipad
  (0.45 + 2 × 0.20), and the fill drops plane copper narrower than 0.20 mm, so two such vias closer than 1.05 mm make
  one void and a row of them a slot. Measured with rule 9's own functions: a later Rev0.5 candidate had voids of
  6.23, 3.33, 3.28 and 3.02 mm and U1's pad webs N 0.53, E 0.00, S 0.58, W 1.05 mm; **Rev0.4's committed board fails
  too**: voids of 3.65, 3.43 and 3.35 mm and 0.47 mm of plane beside U1's east side. The defect predates D37.
- **Fix.**
  - `check_routing.py` rule 9 (`plane_voids`, `epad_webs`): no void longer than 3.0 mm; each side of U1.57 and U6.0 keeps
    at least half the pad's width (1.6 mm for U1's 3.20 mm) in plane copper within 5.0 mm.
  - `route.py` / `ROUTING_Rev0.5.md`: `plane_via=0.60` (every via padstack 0.60 mm larger on In1.Cu in the router's
    input, so different-net vias stand ≥ 1.20 mm apart: 48 pairs closer before, none after on one pass), `PLANE_HOLES`
    (no via within 0.45 mm of a drilled pad's copper or hole on In1.Cu), and a `_gnd` padstack copy for GND vias, which
    have no antipad.
  - 22 parts around U1 moved 0.4-0.8 mm outward (`PLACEMENT_Rev0.5.md`, *Deviations*): two router runs that differed
    only in these positions left 80 connections open, then 33.
  - U1's stubborn pins are drawn before the router starts (the hand-drawn rows whose Why names a U1 pin); the router
    joins them.
  - The committed session still leaves 16 connections, 11 D36 places and 5 dangling stubs. The patch table of
    `ROUTING_Rev0.5.md` (259 rows, 32 remove and 227 drawn) closes them in four stages: the window north of U1 routed
    as a whole by negotiated congestion (nets routed one after another left three connections open), three U1 pads
    joined with the plane rule off (with it on no path exists: the pockets around those pads hold no cell where a via
    keeps rule 9), one via nudged 0.25 mm, and the analog blocks. Scratch tools found the rows; DRC and rule 9 prove them.
- **Mistake, kept.** A trial added 22 pre-route rows to the committed input (13 long V_INJ rows along y = 24.2 in the AFE
  band and 5 U1-pin escapes): 41 connections open against 16. I first read it as router randomness. The router is
  deterministic, and the diff of the two DSNs named the rows; removing them restored the committed input's digest and
  result.
- **Dead end, kept.** A ring keepout that allowed a via only in twelve 0.85 mm windows around U1 left the north side
  of the pad 1.51 mm of plane (rule 9 wants 1.60 mm) and 33 connections open against 24 without it; dropped, the ring
  is open with the two spacing rules only. A 0.55 mm window placed no via at all: the router keeps its 0.15 mm
  clearance inside the window's edge.
- **Process incident.** Parallel router sweeps froze the machine on 2026-11-12 (「固まってるけど」, 「負荷かけすぎじゃない」). Since then:
  at most two processes at a time (the router is one), no sweeps, tests one at a time. The router is deterministic, so
  one trial per input is enough and the official run reproduces it.
- **Two test traps.** `test_make_project.py`'s `peg_drc` called `board.Remove()`, and the next `FootprintLoad` raised
  `SwigPyObject has no attribute ...` in three tests; rules.md already had this rule (2026-11-05), and a new helper
  broke it again: it now strips the board's items in the text. The independent BOM/CPL check (`c2_check.py`, scratch,
  outside the repository) reported "MISSED hand designator J1 added to BOM": J1 is machine-placed since D37, so the
  corruption had become valid input; it now takes the first designator of the hand-solder list from the data.
- **Result.** Board: 2563 tracks, 405 vias, DRC 0 violations, 0 unconnected, 0 parity; U1's plane webs N 1.66, E 1.70,
  S 1.65, W 1.80 mm against 1.60 mm, longest void 2.81 mm; port paths 35.24 and 37.89 mΩ. `make_pcb.py` run twice gave
  the same bytes, and the chain make_project, make_libraries, make_schematic, make_pcb (twice) reproduced all 43 source
  and library files. All seven suites (176 tests; 175 before `fc85c78` added the pitch test), the cost estimate's 18 and the
  OI-23 study's 21 pass, one at a time. `manufacturing/releases/rev0.5/r01/`: ten output files byte-identical to a fresh `make_outputs.py`
  (`check_outputs.py`, 2933 checks), manifest (WIP), `SOURCING_CHECK.md` (PASS, 2026-11-13) and `SHA256SUMS.txt`
  (`sha256sum -c` OK); Rev0.4's releases unchanged.
- **Grading (rubric C1-C9, `.claude/goal-loop/rev05-receptacles/`, not tracked).** First pass on `c3accc1` by an
  independent rubric-verifier: C1, C2, C3, C5, C6, C8 and C9 pass; **C4 and C7 failed**, on two gaps that I had found
  by grepping the Expect clauses a few minutes before its verdict arrived. C4: `test_check_pcb.py`'s own docstring
  disclaimed the J2-J3 pitch rule, so REQ-MECH-02's check had never been seen to fail. C7: D38 did not cite CLAUDE.md
  5.3's "No stubs" as the rule it departs from, and said nothing of the RP2040's reset state on GPIO26-29 (an input with
  its pull-down on, 50-80 kΩ). Fixed in `fc85c78`: `test_receptacles_too_close` (J3 moved to a 17.00 mm pitch; 29 tests
  OK) and the text in circuit §3.3, the D38 row and CLAUDE.md 5.3. The numbers added are computed, not measured: with
  the tap's 51-81 kΩ in parallel with the hub's 15 kΩ pull-down, a Full-Speed device's idle D+ is 2.92-2.95 V
  against 3.00 V (nominal 1.5 kΩ pull-up to 3.3 V); the CH335F's own pull-down value and the margin to its detection
  threshold are not in the repository. `autoroute.py` (which now runs the router in its temporary directory) got
  absolute `--java` and `--jar` paths; a 40 s run with relative paths started from the committed input digest
  (`7291238cf564`), left no `en/` and no java.exe. Second pass on `fc85c78` (C2, C3, C4, C6, C7, C8, C9; C1 and C5
  read nothing that changed, `git diff --stat c3accc1 HEAD` lists four files): **all seven pass.** ERC 0 and
  `check_schematic` 4068 checks; `check_pcb` 13,676 checks and `test_check_pcb` 29 tests, `test_receptacles_too_close`
  among them; `check_outputs` 2933 checks, `sha256sum -c` 12 files OK, Rev0.4's releases unchanged; the seven suites OK
  (19, 29, 19, 29, 22, 28 and 30 tests: 176) and make_libraries, make_schematic and make_pcb each run twice without a
  changed byte; 0 CR bytes, no leftover process, no `en/` in the repository.
- **Not verified.** The JLCPCB gate on Rev0.5 and the placement preview of the receptacle (its CPL angle is KiCad's
  alone), the receptacle's shell legs on a 1.6 mm board (OI-33), the taps' effect on the High-Speed eye (OI-26), the
  router's session on another JRE, and the signal-integrity effect of the long routes (V_INJ 87.9 mm with 8 vias, the
  taps 102.9-110.6 mm). The patch rows belong to the committed session: a new router run needs a new patch, and the
  tools that found these rows are scratch, not in the repository. Nothing is built.
- **Learning.** rules.md: "Datasheet text extraction" (a connector's pad order and land come from the drawing's own
  labels, enlarged; confirmed by the first grading's C1), "Freerouting 2.5.0" (the router's antipad, the DSN diff, the
  patch, the `en/` folder), "KiCad 9 (pcbnew ...)" (`board.Remove()` again), "KiCad 9 silkscreen and manufacturing
  outputs" (a negative test that becomes valid input), "Shell and Python on this box" (the load limit), "Git" (a commit
  message's list of tests comes from the diff: the first draft of `0cdbbda`'s named tests that did not exist) and
  "Delegated verifiers" (grep each Expect clause against the repository before grading).
- **Commits.** `0cdbbda` (placement, routing, outputs, release candidate r01), `c3accc1` (CLAUDE.md, README, requirements),
  `fc85c78` (the pitch test, D38's exception and pull-down, the router's absolute paths); the commit that adds this entry
  follows. Not pushed.

## 2026-11-13 - #8 / #10: the JLCPCB gate on Rev0.5 (release candidate r02, nothing ordered)

- **Request.** Work order step 9 of the #8 handoff: JLCDFM, part mapping, the placement preview of the receptacle C2765186
  and a quote, in the user's Chrome once they had signed in to JLCPCB and JLCDFM (「頑張って続けてくれ」, 「ログインしたよ」).
  Nothing ordered, paid or saved to the cart; no terms or consent accepted; "Confirm Parts Placement" left at No.
  Nothing pushed.
- **Symptom 1 (placement preview).** With r01's CPL the JLCPCB model of the receptacle sat about 1.375 mm toward its mouth
  from the footprint's body centre, at the right orientation.
  **Root cause.** JLCPCB places its own model at the CPL point and angle (easy-stick 14.18); r01's CPL held KiCad's origin
  and angle alone, and the model's own origin is offset from it by 1.375 mm along the receptacle's axis.
  **Fix.** `jlcpcb_model_rotation.json` became `jlcpcb_model_frame.json`: per LCSC part `add` (rotation) and `shift`
  ([dx, dy] in the footprint's frame, turned with it); C2765186 has [0.0, -1.375]; J1/J4 Mid Y 69.385 to 68.010, J2/J3
  2.615 to 3.990. With it the viewer shows the front face 1.054 mm past the edge on all four (design 1.06), a viewer
  reading with an error of about 0.04 mm.
- **Symptom 2 (JLCDFM run 1).** "Plated through-hole spacing": 8 Danger (limit 0.18 mm). The GND fanout vias beside the
  rear plated shell slots of the contact pads A1/B1 of J1-J4 stood 0.046 mm from the slot's hole; KiCad's DRC had said 0.
  **Root cause.** `route.py` `_Copper` reads an oblong pad hole as a round one at the pad's centre, so the router kept clear
  of a round hole instead of the slot, and DRC reported nothing either (rules.md: a slot is invisible to both).
  **Fix.** `check_routing.py` rule 10 (every pair of drilled holes, a slot as a capsule: via-via 0.20, pad-pad 0.45,
  via-pad 0.25 mm; `HoleGapTest`, 7 tests, and two more) and patch stage 5 of `ROUTING_Rev0.5.md` (the 8 vias deleted, each
  stub drawn again into the slot's pad, ending 0.05 mm inside the ring; 275 rows, 397 vias). `route.py`'s search was left
  alone so the committed session's digest still matches; the next router session must read the slot as a capsule.
- **JLCDFM, judged.** The two runs (r01's Gerber, then r02's) are identical except for that item (run 2: 0). Six items
  with Danger remain; each was judged against measurements on the KiCad board (scratch scripts, evidence outside the
  repository): slot width (16 rows: the plated shell slots, 0.60 mm; JLCDFM Danger below 0.61 mm, JLCPCB's page allows
  0.35 mm: the user's decision), annular ring (the 0.45/0.30 mm vias, ring 0.075 mm: JLCPCB's preferred via pad),
  THT-to-SMD (hand-soldered parts), silkscreen to hole (123 pairs, all involving a via), pad spacing (JLCDFM seems to read
  rounded-rectangle pads as sharp ones; no different-net pair under 0.15 mm) and mask opening exposing a trace (no other-net
  copper within 0.15 mm of an opening; the closest is 0.152 mm). Part mapping 41 of 41, 0 substituted. Quote $51.94 without
  shipping against the estimate's $51.80; impedance control would add $34.13.
- **Found while verifying: KiCad's zone filler is not deterministic.** The second `make_pcb.py` run of the final
  verification wrote a board with another SHA-256 than the one in r02's manifest. Thirty-two runs in a scratch copy of
  `design/` gave two boards: 29 `d354d21a…` (two extra 0.11 mm2 B.Cu GND islands touching pad J3.S1, at x 96.73-97.23 and
  105.37-105.87, y 117.0-117.3) and 3 `3205d4c4…` (r02's board, without them). The text diff is two added `filled_polygon`
  blocks of 11 and 10 lines; the Gerber's `B_Cu` member differs by the same two regions and every other member is
  identical; a pcbnew probe: island mode "always remove", both islands touch J3.S1. Both boards pass every check. The
  tracked board is r02's state, restored byte for byte from a scratch run whose hash equals the manifest's (never by
  editing the fill); the ten output files regenerate identically from it. The independent verifier's own 10 runs gave 4 and 6
  of the two boards, so the share of r02's state is not fixed (7 of 42 in all) and "rare" was too strong; no third
  state appeared. README, `make_pcb.py`'s docstring, CLAUDE.md sections 0 and 12, r02's manifest and rules.md no longer
  promise a byte-identical `make_pcb.py`. Untried: filling the zones one at a time in a fixed order (a new board, so a new gate).
- **Mistakes, kept.** (1) `git add` failed with a pathspec error on the old name of the renamed table (already staged
  as a rename) and added nothing; re-run without it. (2) A pre-grading grep of the rubric's Expect clauses found a stale
  sentence in the root README.md (it still said the JLCPCB gate had not run); fixed in `5ea2675` before the verifier read it.
  (3) A rubric grep matched the field name `pcbFileNo` in a rule of rules.md: a false positive, not a leak; the rubric
  now asks for a value next to the name.
- **Verification (tests one at a time).** Two rounds before grading: the checkers (`check_pcb`, `check_routing`,
  `check_silk`, `make_outputs` with its 2970 checks) pass; r02's ten files are byte-identical to a fresh `make_outputs.py`
  from the tracked board; the suites outputs 40, silk 28, libraries 29, make_project 19, schematic 19, pcb 29 and routing
  31 (195 tests), the cost estimate's 18, the OI-23 study's 21 and the stackup study's 25 pass; no runner process left.
  `c2_check.py` (the independent BOM/CPL check, a scratch script outside the repository): 30 checks, 0 failed, 8
  corruptions caught.
- **Grading (rubric C1-C9, `.claude/goal-loop/rev05-gate/`, not tracked).** One pass by an independent rubric-verifier on
  `5ea2675`: **all nine pass, no feedback.** It ran each Verify itself: `sha256sum -c` of r02 (12 files) and r01 (13), a
  corrupted copy failing with exit 1; a fresh `make_outputs.py` (2970 checks) reproducing the ten files byte for byte; the
  Gerber's members 9 same / 6 different and the drill hits 405 to 397 (0.30 mm) with 16 (0.60 mm) unchanged; the CPL
  differing only in J1-J4 Mid Y; `check_pcb` 13,676 checks, `check_routing` PASS (closest holes: pad-pad 0.805, pad-via
  0.669, via-via 0.313 mm), 365 + 32 vias; `HoleGapTest` 7 tests and the suites outputs 40, pcb 29, silk 28 and routing 31
  OK; 10 `make_pcb.py --no-check` runs in a scratch copy (the filler finding above); no private-data pattern in the
  changed files, 0 CR bytes, a clean tree, no leftover process, no `en/` in the repository. The pre-grading grep of the
  Expect clauses (mistake 2) is why the first pass was clean; the previous entry's first pass had failed two criteria.
- **Not verified.** The PCBA quote line by line (only the total), r02's own total, the placement preview's and the form's
  screenshots (none saved), six pad-spacing and three mask-exposure Danger rows (not identified one by one), the
  silkscreen-to-pad rows, JLCDFM's 271 silkscreen-hole count against my 123, JLCPCB's own DFM after an order, the
  receptacle's shift beyond a viewer reading, how many quote drafts JLCPCB auto-saved, and whether the filler has a third
  state (none in 42 runs).
- **Learning.** rules.md: the CPL rule now covers a per-part shift; JLCDFM (50 rows per layer, the Gerber's frame, its
  rounded-rectangle reading, its limits against JLCPCB's page); the browser tool facts of the gate; "a slot is invisible to
  the router and DRC"; the zone filler is not deterministic, with how to treat a changed board hash and now both counts
  (3 of 32, 4 of 10). A count from one session is not a rate: write "in N runs", not "rare". A "run it again and compare"
  step is worth its cost: it is the only thing that found the filler. Grep a rubric's Expect clauses, and every document
  that may say the opposite, before grading.
- **Commits.** `1ba282f` (the two fixes, the board), `effc321` (r02, its review, r01 marked superseded), `5ea2675` (README,
  CLAUDE.md, cost estimate, rules.md); the commit that adds this entry, which also refines the zone-filler rule of rules.md
  with the verifier's 10 runs, follows. Not pushed.

## 2026-11-13 - #8: coupons for the Rev0.5 order (read only, nothing claimed)

- **Request.** After the cost answer: 「使えるクーポンなかった?」; then, after my answer, 「受け取れるのないかチェックして」. A
  check, not a claim: no "Get Coupon", no "Get All Coupons", no "Spin Now", no social share, nothing saved to the cart, no
  terms accepted. Nothing ordered or paid. Nothing pushed.
- **Symptom.** My first answer said the account had 0 unused coupons and that the coupon center's PCBA Special Offer $9 was
  the best candidate. The user asked for a second look.
  **Root cause.** The first pass read only the coupon center and the Unused tab of My Coupons. The Black Friday warm-up
  (11-17 Nov, ET) has its own claimable coupons on an event page that the home page's hero banner links to; the coupon
  center does not list them.
  **Fix.** None in the repository: the answer was corrected in chat, and rules.md now names the four places to look.
- **Found (read only, 2026-11-13, the user's signed-in Chrome).**
  - Event page `jlcpcb.com/events/black-friday-2026`: 11 warm-up coupons, "Limited quantities", all still "Get Coupon":
    BF PCBA $12, BF PCBA Parts $10, BF 6-32L PCB $30, BF PCB $12 - EasyEDA, three JLCONE ones ($5 shipping, $8 prototype,
    $20 batch), Layout $80, Stencil $10, Flex Heater $15, FPC $20. No card shows a minimum order, a validity or a region;
    neither does the page text, the lucky draw's Rules dialog or the help article "Coupon Terms and Conditions" (one coupon
    per order). The news item of 12 Nov says the official sale runs 18 Nov to 2 Dec (ET), with more coupons.
  - Lucky draw: up to 3 spins per account, earned by sharing the event on social media; prizes include a 20 % OFF coupon.
    A share is a public post, so it is the user's to make.
  - My Coupons: Unused empty (every filter), Used 6 (among them PCBA Special Offer $9 and $6, valid until 2026/07/31),
    Expired 4 (among them "Review Reward Coupon $5", until 2026/11/02).
  - Help article "JLCPCB New Customer Coupon Guide" (updated 10 Nov 2026): the monthly SMT Special Offer $9 and $6 (orders
    over $1, excluding shipping) and a $10 PCBA coupon that needs EasyEDA-exported files.
  - Effect, one coupon per order: on the quote of $51.94 without shipping, $12 is 1,920 yen at the planning rate of 160 yen
    per USD, so 12,337 yen for 2 units with OCS Express against 14,257 yen without a coupon ($9: 12,817 yen).
- **Not verified.** The terms of "BF PCBA $12" (minimum order, validity after claiming, region, whether it applies to a
  Japanese address and to Economic PCBA), which show only after claiming; whether a claim succeeds (limited quantity); the
  hour at which the warm-up ends on 17 Nov (ET); the scope of "BF PCBA Parts $10"; JLCONE Desktop's own per-order discount
  ("Save $1-$20 Every Time"), which needs an app install.
- **Learning.** rules.md, JLCPCB section: coupons are in four places (My Coupons, all three tabs; the coupon center; the home
  page's campaign banner; the help article on new-customer and monthly coupons). "None found" from one list is not "none
  exist". Event coupons show their terms only after a claim, and a claim is the user's to approve.
- **Commits.** The commit that adds this entry and the rule. Not pushed.

## 2026-11-13 - #11: enclosure Rev0.1, a first design on paper (nothing printed, the lid PCB not drawn)

- **Request.** 「筐体デザインはあるんだっけ?」 (there was none: `design/mechanical/` did not exist, and the mockup's case,
  64.4 × 28.4 × 9.7 mm, belongs to the superseded 60 × 24 mm board), 「だいぶデカくなったね」, 「USBの位置はUX的に問題ない?」,
  then 「筐体もデザインして」. Tracking issue #11. The open choices (E1-E9) are Claude's, under the 2026-11-03 delegation.
  Nothing printed, ordered or paid; nothing pushed.
- **Result.** `design/mechanical/`: the document `ENCLOSURE_Rev0.1.md` (every dimension in its tables), the board's
  interface exported from the tracked KiCad board (`reference/board_interface_Rev0.5.json`: the outline, 304 footprints
  with their courtyards, 73 holes), `assembly/` (Tray, Frame and Plunger as STL, the lid PCB's interface as JSON, a
  manifest) and `reports/` (seven pictures). A printed tray and frame under a 100 × 72 mm PCB lid, 104.8 × 76.8 × 27.7 mm
  outside: the seam at the board's top face, the board clamped at H1-H4 between the tray's bosses and the frame's posts,
  four countersunk M2 × 10 from below and four M2 × 5 through the lid into heat-set inserts in the posts, a rib under
  each receptacle, a 15.0 × 8.0 mm pocket for a plug's overmould at each opening, two printed plungers over SW1 and SW2,
  light wells over the LEDs and a pinhole over BOOT. F1 (18.3 mm) sets the height.
- **Pipeline.** `export_board_interface.py` (KiCad's Python) → `make_enclosure.py --derived` (builds, rewrites the
  document's derived table, draws the pictures and runs the checker: 17 s) → `test_check_enclosure.py` (72 tests, about
  1 min). `check_enclosure.py` (E01-E16, 96 checks on the repository's files) reads the STL files, the lid interface, the
  manifest, the board interface and the document's tables, and does not import the generator. The build is
  byte-reproducible: a second build left all 13 generated files (5 in `assembly/`, 7 pictures, the document) with the same
  SHA-256.
- **Symptom 1 (three bodies in one file).** The first checker run (91 checks, 1 failed): `FAIL E02 Frame: watertight True,
  winding consistent True, volume 18664.5 mm3, bodies 3`.
  **Root cause.** The two light-well blocks shared only a face with the button columns, and a manifold3d union of two
  solids with no volume in common keeps them as separate bodies (bounding boxes [27.6, 7.7, 2.2, 31.9, 14.6, 19.0] and
  [61.4, 7.7, 2.2, 65.7, 14.6, 19.0], 355.488 mm3 each, listed by a scratch script). "Watertight" and "consistently
  wound" were both true of that file.
  **Fix.** `JOIN = 0.5`: every joined solid (bosses, ribs, flange, posts, columns, wells, tube) reaches 0.5 mm into its
  neighbour, and the plunger's segments are built as hulls. Re-check: one body each. E02 counts bodies with manifold3d's
  `decompose()`; trimesh's `split` fails in the venv ("no graph engines available").
- **Symptom 2 (a check that could not fail).** The negative test `lid_overlap=-0.6` (no flange under the lid's edge)
  passed the checker: E13 asked for 200 mm2 of contact under the lid, and the frame without its flange still gave 258 mm2.
  **Root cause.** An area threshold that no corruption had ever pushed below its limit.
  **Fix.** E13 asks that the outer 0.5 mm of the lid lies on the frame all round (≥ 99.5 % of that band). Both
  `lid_overlap=-0.6` and `lid_overlap=0.3` fail it.
- **Symptom 3 (expectations written from memory).** Of the first 54 negative tests, 4 failed on their first run, 3 of them
  because the expectation was wrong and the checker right: `btn_cbore_depth=1.8` does not fail (the counterbore's floor is a
  45° cone, so the collar keeps its 0.4 mm of travel; 1.6 does fail); `corner_r=6` was expected as an E03 box failure (the
  bounding box does not change: it fails E14's skin check, and `corner_r=1.0` fails E03's outline check); `plunger_play=-0.2`
  prints "lifted 0.45 mm the plunger meets the lid by", not "meets plastic". The fourth was symptom 2.
  **Fix.** Each corruption was run and its FAIL line read before the assertion was written.
- **Other defects, each fixed.**
  - By reasoning, before a check existed: with `corner_r` 3.0 and mitred offsets the ridge's corner stood 3.11 mm from the
    outer arc's centre, 0.11 mm outside the wall. Offsets are round-cornered now and `corner_r` = `wall` = 2.0; E03
    (nothing outside the outline) and E14 (the outer 0.3 mm whole round the seam) were added for it. The posts' feet
    shared a plane with the ridge's inner face: a relief ring `lip_clear` wide, and E14 measures the smallest
    tray-to-frame gap, 0.20 mm. A pan-head counterbore on the bed side had a flat unsupported ceiling: the bottom screws
    are countersunk, and a 45° cone prints without support.
  - The checker would have died with a KeyError on a manifest whose piece list lacked a piece. E01 now stops with a FAIL
    line (`test_piece_not_in_the_manifest`).
  - The document said that 17 of 24 part heights were assumed; a count of its table gave 20 (4 read: F1, the MAU104, the
    receptacle and the switch). Three figures in its prose came from no script (the receptacle's face 1.34 mm inside the
    wall, OUT B 45 mm from a screw, the SWD footprint 1.2 mm from the wall). They are derived figures now (`face_inset`,
    `port_to_screw_max`, `swd_wall_clearance`), measured a second time by the checker (E15), and each was seen failing:
    `gap=0.6`, J3 moved 0.6 mm, J5 moved 0.455 mm.
  - The pictures are tracked, and each carries the manifest's SHA-256 in a PNG text chunk: E16 fails a picture drawn from
    another build. The renderer's first pictures had a dark grey background (background pixels counted as edges, because
    their normal is zero).
  - A scratch AST scan (this box has no pyflakes or ruff) found an unused variable, an unused import and a dead
    assignment.
- **A rounding edge.** The SWD courtyard stands 1.155 mm from the wall, which the table prints as 1.16. A variant that
  moves the wall by 0.2 mm prints 1.35, not 1.36. The test asserts that value with `1\.3[56]`, and the other SWD test moves
  J5 by 0.455 mm so that the result (0.70) lies in the middle of a rounding step.
- **Mistake, kept.** The rubric's "How to run" told the verifier to remove its scratch directory at the end, against
  rules.md ("Tell a verifier to delete nothing"). Found by re-reading that section while the verifier ran, and corrected
  by a message to the running verifier and in the rubric. The verifier deleted nothing and reported its directory
  (`~/tmp/verify-enc`, 1.4 MB), which the main session removed.
- **Checked by hand.** The export against `PLACEMENT_Rev0.5.md`: the positions and rotations of 18 footprints (J1-J5,
  H1-H4, SW1-SW3, F1, U5, D10-D13) agree. Read outside the checker, with trimesh: each piece watertight and consistently
  wound, Euler numbers -6 (Tray: 4 through-holes), -10 (Frame: 6) and 2 (Plunger).
- **Grading (rubric C1-C9, `.claude/goal-loop/enclosure-rev01/`, not tracked).** One pass by an independent
  rubric-verifier on the staged tree that became `f97c51f`: **all nine pass.** It ran each Verify itself: the checker (96
  checks, 0 failed, at least one PASS for each of E01-E16); a rebuild with `make_enclosure.py --derived` that left the 13
  sums and `git status` unchanged; the 72 tests (64 s) and the 16 IDs in the test file; three fault variants that no test
  uses (`cavity_h=17.5`: `FAIL E05 F1: 58.89 mm3 of the Lid inside its envelope`; `pocket_w=13.0`: `FAIL E08` on J1-J4;
  `standoff=1.5`: `FAIL E06 F1 pad '1'`); no import of the generator in the checker and no typed board coordinate; the
  trimesh facts above, with volumes within 0.003 % of the manifest's; the pictures Assembled and Back read as images (one
  closed box under a flat lid, four screw heads, two port openings in the facing wall, two button caps); the 18 derived
  rows against the manifest; 4 read and 20 assumed heights against both sentences; WIP in the header and the manifest,
  OI-1 and OI-5 open, both section 12 items unchecked; no by-product in the tree.
- **The answer to 「USBの位置はUX的に問題ない?」** (given with this work's report). No major problem. The two inputs are on
  the back edge (5V IN at x 17.5, HOST at x 76.0, 58.5 mm apart) and the two outputs on the front edge (OUT A at x 17.5,
  OUT B at x 51.3, pitch 33.8 mm), each with its button 14.0 mm to its right and its two LEDs behind the button. Weak
  points: HOST and 5V IN are the same receptacle on one edge and can be swapped (by design a swap gives a board that does
  not enumerate, not a damaged one; not tested), so the lid's legend has to be large; OUT B is 45.21 mm from the nearest
  screw, hence the rib and the tight shell hole; the front is not symmetric (the MAU104 takes its right third); whether a
  plug seats depends on the wall's opening, which only real cables show; SWD needs the lid off.
- **Not verified.** Nothing is printed, and no cable has been tried in an opening (V-MECH-01). The lid PCB is not drawn
  (only its interface). 20 of the 24 part heights are assumed. The insert's hole (3.2 mm) and the screw heads' sizes are
  from memory. The overmould envelope of 14.0 × 7.0 mm is the document's choice. About 1 W of heat is an estimate, not a
  calculation. The print process (FDM or MJF) is the user's decision. The plungers' feel and BOOT through the pinhole
  (V-BOOT-01) need the built unit. The export script has no check of its own beyond the 18 footprints compared by hand.
  OI-1 and OI-5 stay open.
- **Learning.** rules.md: a new section "Printed parts" (a union needs volume in common; "watertight" does not count
  bodies; a threshold that no corruption can cross is not a check; build a corruption before asserting its line; keep an
  asserted figure off a rounding edge; a picture carries the hash of the build it shows). "Shell and Python": `-I` does
  not find a sibling module, and a compound command with `rm -rf` is refused here. "Delegated verifiers": the no-delete
  rule now says to read it before writing a rubric's "How to run".
- **Commits.** `f97c51f` (the enclosure); the commit that adds this entry and the rules follows. Not pushed.

## 2026-11-18 - #11: the print process is FDM (the user's choice; nothing printed)

- **Request.** A new session, opened with the 2026-11-13 report pasted and 「前回どこまでやったっけ?」. The report's open
  question was the print process (CLAUDE.md §7: chosen before wall and clearance values are frozen). Offered FDM or MJF
  with FDM recommended; the user answered 「FDM」.
- **Result.** Recorded in `design/mechanical/ENCLOSURE_Rev0.1.md` (header, §3 intro and E2, §9, §10) and CLAUDE.md (§0, §7,
  §12). No row of the parameter or height tables changed: E2 had drawn the parts for FDM as the stricter process. E2 now
  names the process as the user's and the nozzle, layer height and no-support rule as Claude's.
- **Verification.** `check_enclosure.py` on the committed build after the edit: 96 checks, 0 failed. The manifest's
  `inputs_sha256` covers the two tables only, so a change of the document's prose leaves the build current (E01 passes
  without a rebuild). `test_check_enclosure.py`: 72 tests, OK, 74 s. `git status`: CLAUDE.md, the enclosure document and
  this journal, nothing under `assembly/` or `reports/`. No `python.exe` left running.
- **Read while establishing the state.** `main` is 25 commits ahead of `origin/main` (everything since `949d944`), so the
  Rev0.5 board work, the host profiler and the enclosure exist on this machine only. The $12 JLCPCB coupon's date
  (2026-11-17, US Eastern) has passed; the site was not read again.
- **Not verified.** Nothing is printed. The FDM material and the printer are not chosen. The lid PCB is not drawn. All of
  the 2026-11-13 entry's "Not verified" stands, except the print process.
- **Learning.** None new.
- **Commits.** Not committed when this entry was written: the user had not asked for a commit in this session.

## 2026-11-18 - #11: the lid PCB drawn (Lid Rev0.1, not ordered); a desk study of moving the USB connectors

- **Request.** 「作図する」, after the FDM answer: draw the enclosure's lid PCB. While it was being verified the user wrote
  「なんかUSBの位置がアシンメトリーで変だね」 and, offered "keep the positions" (recommended) or "study a re-placement",
  chose 「再配置を検討」.
- **Result (lid).** `design/mechanical/LID_Rev0.1.md` (decisions K1-K8, Claude delegated; clearance and legend tables),
  `make_lid.py`, `lid_spec.py`, `check_lid.py` (L01-L16), `test_check_lid.py`, `make_lid_outputs.py`, and the generated
  `design/mechanical/lid/usb-power-hub-lid.kicad_pcb` and `.kicad_pro`. A bare 2-layer 1.6 mm board with the main board's
  100 x 72 mm outline, no part and no net: one copper pour per side, 7 unplated holes (H1-H4 2.3 mm, SW1 and SW2 4.6 mm,
  SW3 2.0 mm), 2 LED windows (mask openings without copper), a Latin legend 1.0-3.0 mm high. Every position comes from
  `assembly/UsbPowerHub_Enclosure_Rev0.1_LidInterface.json`; no script holds one. The candidate set in
  `manufacturing/working/lid-rev0.1/` (7 files) is not tracked. CLAUDE.md (§0, §2, §7, OI-6, §12), README.md,
  `design/mechanical/README.md` and the enclosure document's prose say the lid is drawn and not ordered.
- **Failures, causes and fixes.**
  - The script's zone filler covered an unplated hole and ran to 0.1 mm from the outline. Cause: `ZONE_FILLER` keeps no
    distance for a pour without a net. Fix: every keep-clear area is drawn (outline band, screw heads, plunger holes,
    pinhole, windows) and L04 measures the filled copper against each. KiCad's DRC reported 0 violations for the pour at
    0.1 mm with the rule at 0.3 mm, so the checker measures copper to the outline itself.
  - The saved board and the plotted Gerbers held CRLF. Fix: the generator writes LF, parsers normalise.
  - First grading: 8 of 9 criteria passed, C4 failed. The verifier's own faults that the checker did not report, with the
    checksums written anew: one outline vertex moved inside the bounding box, one region removed from the top
    silkscreen, a valid PNG of another picture, an 18-byte body behind a PDF header. Cause: L13 read the outline's
    extents only, and no check read the silkscreen members. Fix: L13 compares the outline's drawn sides with the
    rectangle's four; new L16 plots the board the checker has just measured (its own two `kicad-cli` calls) and compares
    all 11 members text for text, creation times apart; L12 wants a zip, a one-page PDF and PNGs at least 1200 px wide.
    What the drawing and the pictures show stays unchecked: LID §6 says so, and the rubric's C4 names it out of scope
    (the user was told of that change of the rubric).
  - A heredoc edit of the test file put a real newline into a string literal (the rules.md heredoc rule, again), and a
    probe that ended in `~/tmp/lid-probe/` moved the session's working directory, twice.
- **Verification.** Second grading by a fresh rubric-verifier (sonnet): overall pass, 9 of 9. `check_lid.py` 44 checks, 0
  failed; with `--outputs` 59, 0 failed; a rebuild of the board and of the set is byte-identical; `test_check_lid.py` 110
  tests OK in 128 s, with a failing test for every ID L01-L16; 25 faults of the verifier's own (7 in the board, 5 in the
  interface, 4 in the document, 9 in the set with new checksums), each exit 1 with the expected line; its own read of the
  drill files (7 hits for 7 holes, 0 plated) and of the outline (0, 0)-(100, 72); KiCad DRC 0 violations; legend
  heights 1.0-3.0 mm with strokes at or above height / 6; copper 6871.89 mm2 per side (95.44 %), 0.0 mm2 in every
  keep-clear area, the two sides equal; `check_enclosure.py` 96 checks, 0 failed after the prose edits; no runner
  process left. The verifier's copies of the board printed 43 lines, the tracked tree 44; which line a copy lacks was
  not looked into.
- **The desk study (USB positions).** Block level only: the regions of `design/ecad/PLACEMENT_Rev0.5.md`, typed into a
  scratch script that was not kept. Nothing under `design/ecad/` changed.
  - Now: the front pair (OUT A 17.5, OUT B 51.3) is centred 15.6 mm left of the board's centre, the back pair (5V IN
    17.5, HOST 76.0) 3.25 mm left, the buttons (31.5, 65.3) 1.6 mm left. Regions take 6223 of 7200 mm2.
  - B, HOST moved 6.5 mm to x 82.5: no block overlaps with PORT_HOST mirrored inside (69.5-92.5). The front stays as it is.
  - C2, four corners (ports at 17.5 and 82.5 on both edges, buttons at 31.5 and 68.5; port B and its button to the
    front right, the MAU104 and V12 to the front middle; front ends, ADC, hub and MCU kept): one failure. The front
    middle is 30.0 mm and REF + 6 mm + MAU needs 31.4, so the MAU104 would stand 4.6 mm from REF. MAU to AFE_B 11.8 mm,
    the distance it has to the ADC today.
  - C, channel B's whole front end on the right with the ADC in the middle: the middle column is 973 mm2 and ADC +
    ADCSUP + HUB need 1024 (+51); the hub strip is 10.55 mm wide against 10.25 mm free. It does not fit on 100 x 72 mm
    with the present block shapes.
  - Rows that C2 moves, counted in the placement tables: PORT_{x} 8 and UI_{x} 5 (channel B's), MAU 2, V12 7, REF 6,
    PORT_HOST 6, J1F 7. The channel table's one `dx` would no longer hold for channel B's port and button rows.
  - Not studied: a part-level placement, the routing (VBUS_B's longer run from AFE_B to its port, the HS pairs, a new
    router session and its patch), and noise. The choice is with the user.
- **Not verified.** JLCPCB has not seen the lid's files; the user has not accepted the legend; a refill in KiCad's editor
  was not tried; what the PDF and the PNGs show is unchecked; K8's order parameters are from memory; the enclosure is
  not printed. If a port moves, the lid interface changes and the lid is rebuilt (L01 fails until then).
- **Learning.** rules.md: "Shell and Python" (the heredoc rule's recurrence; a `cd` that persists); "KiCad 9" (CRLF from
  `SaveBoard` and `kicad-cli`; a no-net pour keeps no distance; DRC does not measure it against the outline; the polygon
  calls that work); the zone-filler rule (the lid's fill repeats); "silkscreen and manufacturing outputs" (check an
  archive against a fresh plot); "Delegated verifiers" (keep a rubric's own file out of its greps).
- **Commits.** Not committed when this entry was written: the user had not asked for a commit.

## 2026-11-18 - #12: trial C2, a mirror-symmetric connector placement at placement level (nothing routed)

- **Request.** After the desk study above the user chose 「C2 を試し配置」. Issue #12 tracks it. Scope told to the
  user beforehand: a working copy, placement only, the existing placement check; the tracked board, Rev0.5 r02 and its
  JLCPCB evidence stay untouched.
- **Symptom.** The connectors are off the board's centre line (x 50): OUT A / OUT B add up to 68.8, 5V IN / HOST to
  93.5, the buttons to 96.8, the LEDs to 93.3, where a mirrored pair adds up to 100.
- **Result.** `design/experiments/usb-symmetry-c2/`: `c2_change.py` (the C2 placement as a change to a copy of
  `PLACEMENT_Rev0.5.md`: 28 lines replaced, 13 channel pairs removed, 26 rows added), `trial.py` (scratch copy, change,
  footprint-only board, `check_pcb.py`, tables, picture, `--negative`), `layout_c2.svg`, `README.md`; one line in the
  root `README.md`. 31 of 304 parts move (PORT_B 8, UI_B 5, MAU 1, V12 6, PORT_HOST 5, J1F 6). `check_pcb.py` on the C2
  board: 13,690 checks, 0 failed. J3 82.5, J1 82.5, SW2 68.5, D12 and D13 70.25; every pair adds up to 100.
- **What had to give.** The MAU104 has a window 0.39 mm wide (6.15 mm from R11 in REF against the rule's 6.0 mm, 0.21 mm
  from SW2's courtyard); UI_B is two rectangles; D5 moves 5.15 mm and 0.65 mm down; thirteen pairs leave the channel
  table; D12, D13 and their resistors are turned half a turn.
- **Failures, causes and fixes.**
  - `make_pcb.py` cannot build a changed placement: it stops at the router session's digest. Fix: the trial calls its
    functions up to `add_footprint` and saves there. The unchanged document built that way passed 13,676 checks, 0
    failed, before any change was made.
  - First C2 run: 13,692 checks, 2 failed, both `silk_overlap` of D5 and J1. Cause: D5, moved 1.35 mm toward J1's axis
    to stay left of H4's corner block, put its legend bar (x 85.62-85.77, up to y 64.68) on J1's pin-1 mark (x 85.33-
    86.08, y 64.31-64.91). Fix: D5 0.65 mm down (y 61.8).
  - The desk study's block-level figures were wrong in three places, each corrected from the built board: "1.4 mm
    short" (the courtyards leave 0.39 mm), "VBUS_B about 30 mm longer" (+12.0 mm pad to pad; 31.2 mm is the port's
    move), and "the MAU104 11.8 mm below AFE_B" as the risk (11.93 mm, against 13.88 mm today; the large change is the
    reference, 32.34 mm to 6.15 mm).
- **Figures (now to C2).** MAU104 courtyard to the nearest part of REF 32.34 to 6.15 mm, AFE_B 13.88 to 11.93, AFE_A
  42.60 to 18.35, ADC 11.95 to 12.23, ADCSUP 33.91 to 34.14. Pad to pad, straight line: VBUS_B 14.72 to 26.68 mm, USB
  pair B 47.05 to 22.25, pair A 77.26 unchanged, the upstream pair 42.37 to 39.77, V5L to the MAU104 46.47 to 57.69,
  V12F to the front ends 62.00 to 37.83 (A) and 32.39 to 21.41 (B).
- **Verification.** A fresh rubric-verifier (sonnet), first grading: overall pass, 9 of 9. Its own run of
  `trial.py --negative` (exit 0; the three negative runs caught: R11 at 5.94 mm, U5 leaving its region, the
  silkscreen overlap); its own read of the ten positions (sums 100.00000); its own comparison with a copy of the
  tracked board (304 references, exactly the 31 named parts differ); its own courtyard measurement (U5 to R11 6.1523
  mm, to SW2 0.2100 mm, 180 analog parts); the README's figures against the run; `git status` and `git diff --stat`
  empty for `design/ecad`, `design/circuit`, `manufacturing`, `requirements`; two faults of its own (J3 at 83.0: NOT
  MIRRORED, ok False; SW2 at x 66: 4 failed, `courtyards_overlap` U5 / SW2). Two runs of mine wrote the same board and
  the same picture byte for byte.
- **Not verified.** Routing (no track, no zone, no session; the pad-to-pad figures are not track lengths); noise from
  the MAU104 into the reference, the front ends or VBUS_B; the silkscreen (the trial's document does not update the
  table); the enclosure and the lid, which would be regenerated; JLCPCB. The picture was looked at once in the
  built-in browser; no check reads it.
- **Learning.** rules.md: "KiCad 9" (a placement can be tried without routing), "Design documents" (a block-level
  "does not fit" is not a part-level one; read a length risk from the pads), "Shell and Python" (looking at an SVG).
- **Commits.** Not committed when this entry was written: the user had not asked for a commit. The decision is with
  the user: route C2 as a new PCB revision, or keep Rev0.5 r02.

## 2026-11-19 c2-routing-trial (#12): the C2 placement routed once in a scratch copy, beside the board without its patch

- **Request.** After the placement trial I asked whether to try the routing in a working copy as well. The user
  answered 「単純作業はDevin SWE-2 Maxを利用して。」. Read as: go on, with the simple work delegated to Devin on
  SWE-2 Max and reviewed here; it is also a standing rule (rules.md "Devin CLI"). Scope told to the user beforehand:
  a scratch copy only; the tracked board, Rev0.5 r02 and its JLCPCB evidence stay untouched.
- **Result.** In `design/experiments/usb-symmetry-c2/`: `c2_routing.py` (the hand-drawn copper of C2 as a change to a
  copy of `ROUTING_Rev0.5.md`: 16 lines replaced, 7 moved, 9 added, the patch table emptied), `route_trial.py`
  (stages `base`, `prepare`, `negative`, `route`, `report`), `routed_c2_top.png`, the README's section "Routed"; the
  experiment's row in the root `README.md`. One Freerouting 2.5.0 run on C2: 41 passes, router input
  `26db73e3...3a8b1f`, session `d9ddb777...1fa89d` (the session is not kept; the input is reproducible).
- **Figures (board with the committed session and no patch, to C2 with the new session and no patch).** DRC
  unconnected 16 to 15; D36 places 11 to 14; the router's own unrouted count 55 to 53; tracks / vias 2215 / 343 to
  2270 / 344; port A 35.24 mOhm both; port B 37.89 to 38.64 mOhm (limit 40); `check_pcb.py` failed 5 to 11;
  `check_routing.py` failed 40 to 48 (DRC 5 to 11, DRC unconnected 16 to 15, analog 11 to 14, holes 8 and 8). C2's
  DRC: 3 `copper_edge_clearance` errors (V_INJ on F.Cu against the outline), 1 `starved_thermal` (L4_GND at U17 pad
  7), 7 `track_dangling` warnings; the board's: 5 `track_dangling`. Pair B 68.3 to 37.1 mm per conductor, the
  upstream pair 62.8 / 62.0 to 56.3 / 55.5, pair A 97.0 unchanged. The base copy reproduces CLAUDE.md section 0's
  "16 connections and 11 D36 places" for the committed session.
- **The design decision.** The VBUS_B trunk is on L4 and 3.0 mm wide (16.78 mm of trunk becomes 33.39 mm). Around
  the pair tracks L1 and L3 are closed to other wires (`PAIR_COPLANAR`), so the trunk crosses pair A's line on L4;
  and the board's port B path has 2.11 mOhm to spare. Pre-route the path weighed 38.65 mOhm, routed 38.64.
- **Delegation.** Two Devin runs (SWE-2 Max, 17 min and 6 min, exit 0): an inventory of the routing rows the moved
  parts touch (scratch, not kept), and `c2_routing.py`'s `REPLACE`, `MOVE`, the six J3-end `ADD` lines and
  `apply()`. Every line was compared with values worked out here; all 16 pairs were equal. The three trunk rows,
  `route_trial.py`, the README and the rubric are the main session's.
- **Failures, causes and fixes.**
  - The first trunk (1.2 mm on L1, two more layer changes) was briefed to Devin before the baseline was run. The
    baseline then gave port B 37.89 of 40 mOhm and the drawing came to about 46 mOhm. Fix: Devin's eleven trunk
    rows replaced by three; rule "Settle the design before briefing the rows".
  - `prepare` printed 208 violations and exited 1: 199 `lib_footprint_issues` (the pre-route copy stands apart from
    the footprint library) and 9 `via_dangling` (vias the document leaves for the router). Fix: those two types
    are expected before the router; only other types count.
  - Docstring and rubric said "one router run is one sample". The router is deterministic (rules.md), so the result
    belongs to its input. Reworded.
  - The brief's heading said 17 pairs, its list had 16. Corrected before launch.
  - The rubric's `grep -i "c2"` on the diff of CLAUDE.md matched `TC2030-NL` in the OI-8 row. Fix: `grep -w`.
  - README and docstring said "J3 is now 20 mm further"; 20 mm is the new distance. From the rows: 16.78 mm of
    trunk becomes 33.39 mm. Corrected before the grading.
  - I took a Devin run for stuck after what `date` showed to be a few minutes.
- **Verification.** A fresh rubric-verifier (sonnet), first grading: overall pass, 9 of 9, in 4 min 10 s for all
  of it. Its own runs of `base`, `prepare` (port paths A 35.25, B 38.65 mOhm; DRC 0 beside the two expected types;
  374 connections for the router) and `negative` (narrow: 80.58 mOhm; slot: `shorting_items`; both caught); its own
  `make_pcb.py --dsn` on a fresh C2 copy printed the kept run's router input digest, the kept session's SHA-256
  equals its record, and the digest differs from the tracked one (`7291238c...`); its own `report` on the kept run
  against every figure of the README's section "Routed"; `git status` and `git diff --stat` empty for
  `design/ecad`, `design/circuit`, `manufacturing`, `requirements`, before and after; its own Decimal recomputation
  of Devin's rows (16 `REPLACE` pairs, `MOVE` = lines 340-346, the six J3-end lines, both centrelines: all equal);
  its own pcbnew read of the kept C2 board (J1 and J3 at x 82.5000, all 51 tracks of the four pair nets on F.Cu,
  lanes at 81.77 / 82.23 and 82.77 / 83.23); the honesty statements; CR counts 0; the two refusals; and two faults
  of its own (a J3 lead-in ended on its neighbour: `tracks_crossing`, `clearance`, `solder_mask_bridge`; the trunk
  cut: `no copper path`, `inf mOhm`).
- **Not verified.** That a C2 board can be finished: no patch was written, and the 15 open connections, 14 D36
  places and 4 DRC errors are not shown to be closable, nor the opposite. Another drawing of the hand-drawn rows.
  Noise from the MAU104 (6.15 mm from the reference); the pairs' impedance and signal quality; the silkscreen; the
  enclosure and the lid PCB; JLCPCB. The router run itself was not repeated (its input digest was). The render was
  looked at once; no check reads it.
- **Learning.** rules.md: "Freerouting 2.5.0" (hold a new session against the board without its patch; check the
  hand-drawn rows before the router), "Design documents" (a length change is two computed lengths), "Delegated
  verifiers" (a rubric's grep for a short name needs `-w`), "Devin CLI" (the three rules of this trial).
- **Commits.** Not committed when this entry was written: the user had not asked for a commit. The decision is with
  the user: take C2 into a new PCB revision (placement, session, patch, silkscreen, outputs, JLCPCB gate, enclosure,
  lid), or keep Rev0.5 r02.

## 2026-11-19 rev06-layout (#13): Rev0.6 placed mirror-symmetric (D39), routed by carrying Rev0.5's copper, labelled, exported

- **Request.** The user, after trial C2 (#12): 「C2 で進める」. On committing: 「コミットして進める (推奨)」, the option that
  commits Rev0.6 step by step and does not push. Issue #13, steps 1 to 5.
- **Result.** The tracked board is Rev0.6. J2 | J3 stand at x 17.5 | 82.5 on the front edge, J4 | J1 at the same x on
  the back edge; SW1/SW2, D10-D13 and R140/R141/R240/R241 mirror with them; 31 of the 304 parts moved. DRC 0
  violations and 0 unconnected items; the six checkers pass (4068 / 3609 / 13705 / 3505 / 2499 / 2970 checks) and
  the eight suites (237 tests). No net and no part changed: the BOM and the hand-solder list are Rev0.5 r02's
  bytes, and the exported netlist differs in title-block lines alone. No release; JLCPCB has not seen the files.
- **Figures.** Carried: 2,005 track segments and 205 vias; dropped 115 (40 named by DRC, 75 floating) of 19 nets; 36
  connections open before the router. VBUS_B's trunk: 35.1 mm on L4, 29.8 mm of it 3.0 mm wide along y = 14.0.
  Session: 8 passes, 251 segments and 1 via, 207.7 mm on 46 nets (204 segments shorter than 1.0 mm, two exact
  repeats of carried AMP_L_A segments). Patch: 42 rows, 10 of them `remove`; 24 segments taken away, 33 segments
  and 12 vias drawn. Board: 2738 tracks, 413 vias. Port A 35.24 mOhm, port B 39.12 mOhm of 40. U1's webs N 1.66,
  E 1.70, S 1.65, W 1.80 mm (rule 1.60); longest In1 void 2.81 mm (rule 3.0).
- **Design decisions.**
  - Carry, do not route again. `carry.py` reads Rev0.5's session and patch table from Git at the commit the carry
    table names (866ef44), applies them with the pipeline's own functions and drops, in rounds, what KiCad's DRC
    names and what is left floating. `make_pcb.py` applies the record between the GND fanout and the router input.
    Trial C2 (#12), routed from nothing, had ended with 15 connections open and 4 DRC errors; carried, 36
    connections are open before the router and 9 after it.
  - VBUS_B's trunk runs south of pair A, not under it. Under the pair, the trunk and the pair's keepouts closed
    every layer of the corridor and nothing crossed it. With a strip for vias between trunk and pair, five
    crossings are drawn in the route table (LED_FLT_B, BTN_B, LED_ON_B, V12F, ADC_L_A).
  - The patch rows were written by a scratch exact-obstacle search. The tool is not kept; the rows are the
    document's, and `check_routing.py` reads the board.
- **Delegation.** One Devin run (SWE-2 Max) in step 1: the 202 mechanical replacements of the re-pointing
  (`4c4b201`), reviewed with a script that derives the expected changes from the untouched copy. Placement, the
  carry, the trunk, the patch and every test are the main session's.
- **Failures, causes and fixes.**
  - `test_carry.py`, first run: 7 failures and 1 error. Cause 1: the record held the dropped items by DRC
    violation type, and KiCad's DRC split the same shorts differently from run to run on an unchanged board
    (clearance 8 / shorting_items 23, then 7 / 24; later solder_mask_bridge 4, then 3), while the tracks, vias and
    `remove` lists were identical. Taking the least type name per item did not help: the set of types itself
    varies. Fix: the record holds `{"drc": 40, "floating": 75}`; the split is printed as "in this run". Cause 2:
    `CARRIED.parent.relative_to(ROOT)` raised ValueError for a record outside the repository, which is where the
    tests put it. Fix: `as_posix()`.
  - `test_check_routing.py`: two hole-rule tests named J1's rear slot at its Rev0.5 place (sheet x 130.32). They
    failed for the wrong reason: no slot stands there on Rev0.6 (136.82). Fixed to the Rev0.6 slot.
  - After the first patch run a 3.79 mm GND track dangled: taking a tail away had exposed the next segment of the
    chain. Then a 0.002 mm segment dangled: a tail's removal stops at the junction such a segment forms. Fix:
    three more rows; repeated until DRC named no dangling track.
  - Document statements corrected before the grading: the five GND tails stand at the old places of J3's and J1's
    parts (I had written the MAU104's); EN_B's 5.3 mm stub is the session's, not carried; TAP_B_P runs 1.2 mm
    beside Rev0.5's line and under Q53, not C35.
  - Found by the verifier outside its rubric: the U1-escapes paragraph still said "Five U1 pins are still open
    after the router", which is Rev0.5's session. Corrected after the grading; `check_routing.py`, `check_pcb.py`
    and `carry.py --check` were run again on the result.
- **Verification.** A fresh rubric-verifier (sonnet), first grading: overall pass, 12 of 12, in 13 min 12 s. Its
  own: a pcbnew read of the seven mirror pairs (sums 100.0000, dy 0.0000); the six checkers; kicad-cli's DRC JSON
  (violations, unconnected items and schematic parity all empty); the eight suites with their counts and no runner
  left; `carry.py --check` twice with identical output and the document's 19 nets; `cmp` of the BOM and the
  hand-solder list with r02's; the netlist diff (34 lines, all rev, comment 2, uri, source or date); the Rev0.5
  release untouched (12 OK); net lengths by pcbnew (EN_B 88.930, DIS_B 83.452, V_INJ 90.840, BTN_B 80.293,
  LED_ON_B 84.022, LED_FLT_B 90.758 mm); the 3.0 mm trunk row at 29.782 mm; the stale-text grep, with a control
  that the pattern finds 142 lines in HEAD's routing document; four corruptions of the record through
  `carry.differs`, each named.
- **Not verified.** Nothing is built. JLCPCB has read none of Rev0.6's files (DFM, part mapping, placement
  preview, quote). The verifier did not count the session's 251 segments or the 9 open connections itself. What
  the routing document lists under "Not settled": port B's 0.88 mOhm of margin, the L3 tracks beside the trunk and
  through the corner of the ADC's supply block, the MAU104 nearer the reference block. The board was not built a
  second time from its sources (`make_pcb.py`'s fill is not byte-reproducible). The enclosure and the lid PCB
  still describe the Rev0.5 board; a dry run in a scratch copy shows Enclosure Rev0.1 failing E05 on the Rev0.6
  interface (SW2's column stands 0.245 mm inside U5's courtyard). That is step 7.
- **Learning.** rules.md: "KiCad 9 routing checks" (DRC's split by violation type varies between runs; the
  connectivity's dangling test), "Freerouting 2.5.0" (fixed copper and passes; the router's unrouted count; a
  trunk under a pair), "KiCad 9 (pcbnew ...)" (a tail's removal exposes the next), "Design documents" (a test that
  names a part's place by number).
- **Commits.** `7d09fcf` (pure rename), `4c4b201` (re-point), `010695e` (D39, placement, carry, routing,
  silkscreen, tests and documents in one commit). Not pushed.

## 2026-11-19 rev06-r01-mechanical (#13): Rev0.6 release candidate r01 (WIP, not uploaded); Enclosure Rev0.2 and Lid Rev0.2 drawn for the Rev0.6 board

- **Request.** Issue #13, steps 6 to 8, under the user's 「C2 で進める」 and 「コミットして進める (推奨)」 (commit step
  by step, no push). Uploading to JLCPCB was not asked for and was not done.
- **Result.**
  - `manufacturing/releases/rev0.6/r01/` (state `WIP`): the ten files of `manufacturing/working/rev0.6/`, byte for
    byte, with a manifest and `SHA256SUMS.txt`. JLCPCB has read none of them. BOM and hand-solder list are Rev0.5
    r02's bytes; 28 of the CPL's 262 rows differ; 13 of the Gerber zip's 15 members differ beyond header lines.
  - Enclosure Rev0.2 and Lid Rev0.2 are built from the Rev0.6 board's interface. `check_enclosure.py` 100 checks,
    0 failed (96 before: four new wall probes); `test_check_enclosure.py` 75 tests; `check_lid.py` 44 checks, 59
    with the candidate set (`manufacturing/working/lid-rev0.2/`, not tracked); `test_check_lid.py` 110 tests.
    Nothing is printed, nothing is ordered.
- **What did not fit.** Enclosure Rev0.1's geometry on the Rev0.6 interface: `FAIL E05 U5: 13.60 mm3 of the Frame
  inside its envelope (height 10.2 mm + 0.3 mm)`. SW2 moved to x 68.5, 2.955 mm from the courtyard of the MAU104;
  the button's column reached 3.2 mm to each side from 2.2 mm up, so it stood 0.245 mm inside. Found by a dry run
  of the mechanical pipeline in a scratch copy, before any file of the repository was renamed.
- **Design decisions (Claude, delegated; recorded as E8's amendment in `ENCLOSURE_Rev0.2.md`).**
  - A button's column starts 11.0 mm above the board (`btn_bottom`), above the converter, for both buttons. The
    light wells and the BOOT tube keep `ui_bottom` 2.2 mm.
  - `btn_wall` 1.5 to 1.9 mm, and a new demand `btn_wall_min` 0.8 mm with two probes per button (bore,
    counterbore). Rev0.1 left 0.4 mm of plastic round the counterbore, which no check measured; it was seen only
    because the column's width had to be thought about again.
  - Rejected: a column narrowed beside the converter (0.35 mm from the body of a hand-soldered part; the first
    prototype, a stepped column, passed the checker and was dropped for this reason), a 2.0 mm plunger, moving U5
    or SW2.
  - The cost, in the document's section 10: the bore guides the shaft over 4.7 mm instead of 13.5 mm; from the
    nominal clearances the foot can stand about 0.7 mm off the switch's axis (0.2 mm in Rev0.1). A hand
    computation; the checker moves a plunger and does not tilt it.
  - The lid needed no parameter and no legend row changed but the revision's text.
- **Delegation.** One Devin run (SWE-2 Max): 62 replacements of three literal strings in ten scripts and two
  documents under `design/mechanical/` (Rev0.5 to Rev0.6 x 11, Rev0.1 to Rev0.2 x 47, rev0.1 to rev0.2 x 4). It
  worked on copies; a review script derived the expected bytes from the untouched copies (0 files differ; on an
  unchanged copy the same script reports 12). `test_check_lid.py` and the README were not given to it: their
  revision names carry meaning (a test swaps the revision to the next one).
- **Failures, causes and fixes.**
  - `test_check_enclosure.py`, first run on the new board: 1 of 72 failed, `test_receptacle_moved_on_the_board`,
    which expected `port_to_screw_max 45.21 (built: 45.81)`. The figure is the board's (now 14.03, built 14.63).
  - `test_tower_on_a_switch` (`ui_bottom=1.0`) still passed, for another reason than its name gave: with the
    column raised, what enters SW1's envelope is the light well's corner (1.80 mm3), and the tube enters SW3's
    (12.99 mm3). Renamed, and it now asserts SW3's line.
  - `test_check_lid.py`, first run: 5 of 110 failed. Four named Rev0.5's places (`(at 126 56.5 0)`, `X65.3Y4.5`,
    `x = 75.`); the fifth moved SW2's hole 6 mm to the right, which on Rev0.6 puts its ring under `OUT B`
    (`FAIL L10`, and KiCad's DRC `silk_overlap`). It now moves the hole towards the middle.
  - A document claim corrected before the grading: I had written that the pinhole over SW3 moved with the lid's
    other features. The interface's diff shows SW3 where it stood; only J1, J3, SW2's hole and OUT B's window
    moved.
  - One Bash command did not return within 120 s and was stopped (it ended with `python - <<'EOF'` and an empty
    body, then a `grep`). Run again part by part under `timeout 10`, every part returned. Cause not established.
    No runner process was left.
  - r01 was committed (`7c5eec9`) on the main session's checks alone, though the issue asks for an independent
    grading of every step. Noticed while writing this entry; graded afterwards (below). Before the grading one
    row of its manifest had gone stale with the mechanical commit ("are being redrawn") and was corrected with
    the manifest's checksum line (`7d5ad3e`); the ten files of the set were not touched.
  - `check_outputs.py --out manufacturing/releases/rev0.6/r01` ends `2949 checks, 14 failed`: `malformed line`
    for each of the 11 lines of `SHA256SUMS.txt`, `lists []`, and two lines on the manifest. The checker is the
    working set's; every release in the repository writes `<hash> *<file>` (`sha256sum -b`) and a manifest of
    its own form. Not a defect of r01; the rubric checks it with `sha256sum -c` and `cmp`.
- **Verification.**
  - Main session: the four runs above; two enclosure builds byte-identical (three STL files, lid interface,
    manifest); the Frame inside U5's courtyard prism: 0.000 mm3 up to 10.5 and 10.9 mm, 2.158 mm3 up to
    11.5 mm; r01 against a fresh `make_outputs.py --no-check` run (10 files the same), against Rev0.5 r02
    (BOM and hand-solder list the same bytes, 28 CPL rows, 13 Gerber members) and against the tracked sources
    (10 hashes).
  - Independent verifier, mechanical step (`rubric-verifier`, sonnet, fresh context;
    `.claude/goal-loop/rev06-mechanical/rubric.md`, C1 to C8): 8 pass, first iteration. It exported the
    interface and rebuilt the three STL files and the lid interface (byte-identical), built the two faulty
    variants (`btn_bottom=2.2`: `FAIL E05 U5: 35.81 mm3`; `btn_wall=1.5`: `87.7 %` of the ring), measured
    0.00000 and 2.15752 mm3 with its own script, ran both suites (75 tests in 77.9 s, 110 in 111.7 s) and read
    the lid's seven holes and four port labels with its own pcbnew script.
  - Independent verifier, r01 (`.claude/goal-loop/rev06-r01/rubric.md`, R1 to R7): 7 pass, first iteration. It
    regenerated the set from the tracked board (ten files byte-identical), compared the ten source hashes with
    the manifest's, reproduced the 28 CPL rows and the 13 Gerber members against Rev0.5 r02 with its own
    script, and counted 413 vias (381 with a 0.45 mm pad, 32 with 0.60 mm) with pcbnew.
- **Not verified.** Nothing is printed and no cable was tried (OI-1, OI-5). 20 of the 24 part heights are assumed.
  The plunger's tilt is computed by hand. The MAU104 is soldered by hand and may lean: 0.8 mm under the column.
  The user saw Lid Rev0.1's legend as a picture and has not accepted this one; nobody has seen it on a board
  (OI-6). JLCPCB has seen neither r01 nor the lid's set: no JLCDFM, part mapping, placement preview or quote
  for Rev0.6. The interface's courtyards and drilled holes were compared with nothing; its 304 positions and
  rotations were compared once with the placement document by a scratch script (0 differ).
- **Learning.** In `rules.md`: the rule on negative tests that name a place by number now carries the lid's five
  tests and the enclosure's one; three rules added under "Printed parts" (a negative test that keeps passing for
  another reason; a dry run of the downstream generators before any rename; a wall probe for every hole); two
  under the manufacturing outputs (a release directory is checked with `sha256sum -c`, not `check_outputs.py`;
  a step that only copies files is still graded before its commit).
- **Commits.** `7c5eec9` (r01), `f074c52` (Enclosure Rev0.2 and Lid Rev0.2), `7d5ad3e` (r01's manifest row), and
  this entry's. Not pushed.

## 2026-11-19 rev06-jlcpcb-gate (#13): the JLCPCB gate on Rev0.6 r01 (uploaded and read; nothing ordered, nothing paid)

- **Request.** The user's 「アップロードする」, the answer to whether to upload Rev0.6 r01 to JLCPCB and run the gate
  (JLCDFM, part mapping, placement preview, quote). It covered r01's three files and nothing else: no order, no
  payment, no terms, no coupon, no download, no upload of an older Gerber.
- **Result.** `manufacturing/releases/rev0.6/r01/JLCPCB_REVIEW.md`; the ten files of the set did not change and the
  state stays `WIP`.
  - Part mapping 41 of 41, 0 substituted, 38 Basic and the three allowed Extended. JLCPCB's stock for the 41 codes
    read with `tools/jlc_stock.py` (lowest: CH335F 4,378).
  - Placement preview: J1-J4 (front face 1.05-1.06 mm past the edge, tails 6.33-6.34 mm, pegs 2.83 mm) and the 7
    other moved parts that are not symmetrical, one instance of each other class; no part dragged.
  - Quote $52.85 without shipping (PCB $8.00, Economic PCBA $44.85, each line recorded), $0.91 above Rev0.5 r02's.
  - JLCDFM: 35 items, Danger in 7 of them, each judged against measurements on the board.
- **Findings left to the user.** (1) A GND via stands 0.059 mm from pad 3 (GND) of D1. (2) JLCDFM lists the
  non-plated drill file as a plated layer and the 15 non-plated holes as "Pth without pad". (3) The receptacles'
  0.60 mm plated slots, as on Rev0.5.
- **What did not fit, and why.**
  - JLCDFM's counts could not be compared with Rev0.5's run of 2026-11-13: its list has 35 rows where Rev0.5's
    record has 29 (first counted here as 28; the file gives 29). Investigated by running the same scripts on the
    Rev0.5 board, extracted from `1ba282f`: the same 13 via holes in pads, the same 13 pad-to-track pairs under
    the rectangle reading, 15 non-plated holes. So "Via placed within a pad" (0 to 2), "Pth without pad" and the
    22 Danger of "Measure pad to line spacing" come from the list, not from the board.
  - The one change that is the board's: pad-to-via pairs of one net under 0.10 mm went from 2 to 3. Root cause:
    the via at KiCad (127.7713, 59.8161) is in `design/ecad/routing/carried.json` and on the Rev0.5 board, 6.3 mm
    from D1 pad 3; D39 moved D1 by 6.5 mm beside it. KiCad's clearance is between nets, and no checker of the
    repository measures a pad against a via of its own net. Confirmed with `gate_measure5.py` on both boards and
    in JLCDFM's viewer (row 2 of "Pad spacing"). Not fixed: a fix changes the copper and needs a new release.
  - The first `file_upload` on jlcdfm.com only reloaded the page; the second uploaded. Whether the first left a
    record in the account is not known.
  - The stock was read at 15:24, after the upload of 14:50; CLAUDE.md 4.1 asks for before the upload.
  - Rev0.5's review kept the PCBA price as a total only, so the +$0.91 with a byte-identical BOM cannot be
    attributed to a line.
  - `gate_measure.py`, copied unchanged from Rev0.5's gate, stops in M7 with a TypeError (a circle against a
    segment); M7 is `gate_measure2.py`'s. Not fixed, so that the script stays the one Rev0.5 was measured with.
- **Verification.**
  - Main session: `sha256sum -c` (12 OK); the ten generated files unchanged against `a4dff8f`; the measuring
    scripts on both boards; the 28 moved CPL rows by `diff` against Rev0.5 r02's; every rubric command run before
    the grading.
  - Independent verifier (`rubric-verifier`, sonnet, fresh context; `.claude/goal-loop/rev06-jlcpcb-gate/rubric.md`,
    C1 to C9): 9 pass, first iteration. It ran all five scripts on the Rev0.6 board and three on the Rev0.5 board
    itself and compared every figure of the record (0.059 mm at D1 pad 3, 3 / 152 and 2 / 149 pad-to-via pairs,
    13 pairs at 0.091-0.094 mm, 0.152 / 0.170 mm, the 13 via holes as 5 + 6 + 1 + 1, 15 non-plated holes,
    131 silkscreen-to-via pairs, 0.227 mm), the 41 codes against the BOM, the 28 CPL rows, 17 rotations, the
    stock file, the price arithmetic, every JLCDFM triple against the statistics file, and the four documents
    against the record. It cannot see the web pages. It left `listed.txt` in the system temp directory, which
    was deleted afterwards.
- **Not verified.** Six of the 7 "Pad spacing" Danger rows, the 22 of "pad to line spacing" and the 3 of the
  mask-exposure item were judged by measurement and not identified row by row. No control run of Rev0.5 r02's
  Gerber on today's JLCDFM. JLCDFM's SMT DFM tab, the names of two rows without a name, a quote with impedance
  control, the OCS price, the assembled parcel's shipping, the Akizuki stock, the "42 Parts confirmed" counter and
  the independent check of the set that Rev0.5 r02 had were not read or run. The placement preview is a viewer
  reading; screenshots were not saved.
- **Left in the user's accounts.** One auto-saved quote draft (`UsbPowerHub_Main_Rev0.6_Gerber`) and JLCDFM's upload
  record. Evidence outside the repository: `~/tmp/usb-power-hub/rev06-gate/evidence/`.
- **Learning.** In `rules.md`: JLCDFM's list changes between runs, so compare boards by measurement; the "rect"
  reading of rounded pads (the existing rule, extended); JLCDFM lists KiCad's NPTH file as plated; record every
  charge line and read the stock before the upload; browser facts of 2026-11-19; and, under the routing checks,
  carried copper beside a moved pad of its own net.
- **Commits.** This entry's. Not pushed.
