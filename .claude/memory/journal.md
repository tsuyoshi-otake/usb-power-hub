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
