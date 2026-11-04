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
