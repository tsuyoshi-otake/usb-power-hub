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
