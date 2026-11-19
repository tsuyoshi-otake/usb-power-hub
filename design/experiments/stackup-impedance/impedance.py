#!/usr/bin/env python3
"""USB 2.0 90-ohm differential geometry on the JLCPCB 4-layer 1.6 mm stackups.

Non-authoritative (design/experiments). Reads stackups.json next to this file
and prints, for every stackup, the edge-coupled surface-microstrip differential
impedance Zdiff over a grid of trace width W and pair gap S (L1 trace over the
L2 ground plane), then solves W for Zdiff = 90 ohm at S = 0.15/0.20/0.25 mm and
the W window that keeps Zdiff inside 81-99 ohm (90 +/-10%).

Model — static (f = 0) closed forms:

* Single microstrip: Hammerstad-Jensen, with its TWO separate finite-thickness
  width corrections (one for the air-line impedance, a smaller one for the
  dielectric):
    E. Hammerstad and O. Jensen, "Accurate Models for Microstrip
    Computer-Aided Design", IEEE MTT-S Int. Microwave Symp. Digest, 1980,
    pp. 407-409.
        du1 = (tau/pi) * ln(1 + 4e / (tau * coth^2(sqrt(6.517 u))))   # air
        dur = 0.5 * (1 + 1/cosh(sqrt(Er - 1))) * du1                  # dielectric
        u1 = u + du1,   ur = u + dur,   tau = T/H
        Z01(x) = (eta0 / 2 pi) * ln(F(x)/x + sqrt(1 + (2/x)^2)), eta0 = 376.73
        Eeff   = Eeff0(ur, Er) * (Z01(u1) / Z01(ur))^2
        Z0     = Z01(ur) / sqrt(Eeff)
  with Eeff0(u, Er) = (Er+1)/2 + (Er-1)/2 * (1 + 10/u)^(-a(u) b(Er)) and
  F(u) = 6 + (2 pi - 6) * exp(-(30.666/u)^0.7528). Putting the single air
  increment du1 into both Z01 and Eeff (as an earlier revision did) answers
  ~48 ohm at JLCPCB's 14.85 mil datum width where this formulation answers
  50.57 ohm — the test suite pins the 50.57 value.

* Edge-coupled pair: Kirschning-Jansen static even/odd impedances
    M. Kirschning and R. H. Jansen, "Accurate Wide-Range Design Equations for
    the Frequency-Dependent Characteristic of Parallel Coupled Microstrip
    Lines", IEEE Trans. MTT-32, no. 1, 1984, pp. 83-90 (+ 1985 correction).
    Zdiff = 2 * Z_odd. KJ assumes zero-thickness strips; as an approximation
    the corrected dielectric width ratio ur of the single line is used as
    the KJ width ratio u throughout, and ee/zl are the single-line
    relations Eeff0(ur) and Z01(ur)/sqrt(Eeff0(ur)) evaluated at ur.
* Stated validity: 0.1 <= u = W/H <= 10, 0.1 <= g = S/H <= 10, 1 < Er <= 18
    (KJ); u here spans ~0.5-4 and g ~0.2-3.5, inside the range.

IPC-2141A is kept ONLY as a printed comparison column: at the published Dk it
gives 13.50 mil for JLCPCB's 50-ohm bare datum (14.85 mil), a -9% miss the
test suite asserts stays outside +/-3%, while the HJ model lands at ~15.15
mil (+2%).

Reference vs JLCPCB — JLCPCB's own calculator (browser run, 2026-11-03)
gives, for JLC04161H-7628, a 50-ohm non-coplanar single-ended trace of
14.85 mil WITHOUT solder mask (14.12 mil with). The model above solves
~15.15 mil at the page's nominal Dk 4.4 — +2%.

NOT modelled (and the direction of each effect):
  * solder mask over the pair (JLCPCB: 0.6 mil on copper, Er 3.8) — lowers
    impedance. JLCPCB's own 14.12-vs-14.85 mil pair measures it on a single
    line: the bare model reads 14.12 mil as ~52.0 ohm, i.e. the mask removes
    ~2 ohm at 50 ohm. On the pair the mask also fills the inter-trace gap
    and the effect is larger; it is NOT quantified here.
  * etch trapezoid (JLCPCB's calculator takes top = base - 0.7 mil) — the
    narrower conductor raises impedance slightly, partially cancelling the
    mask.
  * ENIG — thin; approximately negligible for impedance, adds some loss.
Net: a masked, etched board should land BELOW the bare numbers here, more so
on the pair than the single-ended ~2 ohm; the solved widths are an upper
bound. JLCPCB's own impedance calculator is the authority (CLAUDE.md 5.1);
its differential run returned no result on 2026-11-03 (page error), so the
pair values here are model values and must be re-confirmed.

Usage (from the repository root):
    python -I -B design/experiments/stackup-impedance/impedance.py

Exit status: 0 = every stackup has its data, and the recommended pair (REC_W_MM,
REC_S_MM on REC_STACKUP_ID, the D27 starting geometry) lands inside 81-99 ohm.
1 = a stackup is missing needed data (H, Dk, T), the recommended stackup is
absent, or the recommended pair leaves 81-99 ohm. A stackup that cannot reach
90 ohm within W 0.10-0.60 mm is reported as UNREACHABLE but is not an error:
it is a finding about that stackup (JLC04161H-7628C and -7628F on the current
data), not a defect of the study.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
STACKUPS_JSON = HERE / "stackups.json"

MIL_MM = 0.0254

# JLCPCB calculator parameter (user guide, "Sep 16, 2026"): finished 1 oz outer
# copper is 1.6 mil = 0.04064 mm — plating adds about 5.6 um over the 0.035 mm
# base foil the stackup tables list.
T_OUTER_MM = 1.6 * MIL_MM

# JLCPCB's own impedance calculator, run in a browser by the main session on
# 2026-11-03 (https://jlcpcb.com/pcb-impedance-calculator), Rigid / 4 layers /
# 1.6 mm / inner 0.5 oz / outer 1 oz, stackup tab JLC04161H-7628, signal L1,
# bottom reference L2: a 50-ohm "Single Ended (Non coplanar)" trace comes out
# at 14.85 mil without solder mask and 14.12 mil with. The "Differential Pair
# (Non coplanar)" run returned no result (the page threw an error), so the
# pair has no JLCPCB reference — this single-ended datum is the comparison
# anchor instead.
JLCPCB_SE_TARGET_OHM = 50.0
JLCPCB_SE_BARE_MIL = 14.85
JLCPCB_SE_MASKED_MIL = 14.12
JLCPCB_REF_STACKUP_ID = "JLC04161H-7628"

TARGET_OHM = 90.0
BAND_OHM = (81.0, 99.0)                    # 90 ohm +/-10%
GAPS_MM = (0.15, 0.20, 0.25)               # routing rule: spacing >= 0.15 mm
W_SOLVE_RANGE_MM = (0.10, 0.60)            # solve window for W (board-practical)
W_SEARCH_HI_MM = 2.0                       # wider bracket, only to label "needs >0.60"
GRID_W_MM = (0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60)

# Recommended USB High-Speed pair on L1 over L2: the D27 starting geometry in
# design/circuit/CIRCUIT_DESIGN_Rev0.6.md section 10 and CLAUDE.md 5.3. Change it
# there and here together. TRACK_TOL is JLCPCB's track-width tolerance
# (capabilities page), applied with S held fixed.
REC_STACKUP_ID = "JLC04161H-7628"
REC_W_MM = 0.31
REC_S_MM = 0.15
TRACK_TOL = 0.20

ETA0 = 376.73                              # free-space wave impedance, ohm


# ---------------------------------------------------------------- model: HJ

def _hj_a(u: float) -> float:
    return (1.0 + math.log((u ** 4 + (u / 52.0) ** 2) / (u ** 4 + 0.432)) / 49.0
            + math.log(1.0 + (u / 18.1) ** 3) / 18.7)


def _hj_b(er: float) -> float:
    return 0.564 * ((er - 0.9) / (er + 3.0)) ** 0.053


def eeff_microstrip(u: float, er: float) -> float:
    """Eeff0(u, Er): HJ static effective permittivity at width ratio u = W/H."""
    return (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / u) ** (
        -_hj_a(u) * _hj_b(er))


def z_air_u(u: float) -> float:
    """Z01(u): impedance of the AIR-filled microstrip at width ratio u (HJ)."""
    f_u = 6.0 + (2.0 * math.pi - 6.0) * math.exp(-((30.666 / u) ** 0.7528))
    return ETA0 / (2.0 * math.pi) * math.log(
        f_u / u + math.sqrt(1.0 + (2.0 / u) ** 2))


def z0_u(u: float, er: float) -> float:
    """Thin-strip microstrip Z0 at width ratio u: Z01(u) / sqrt(Eeff0(u))."""
    return z_air_u(u) / math.sqrt(eeff_microstrip(u, er))


def du1(u: float, tau: float) -> float:
    """HJ air width increment for finite strip thickness, tau = T/H."""
    if tau <= 0.0:
        return 0.0
    coth = 1.0 / math.tanh(math.sqrt(6.517 * u))
    return (tau / math.pi) * math.log(1.0 + 4.0 * math.e / (tau * coth * coth))


def dur(u: float, tau: float, er: float) -> float:
    """HJ dielectric width increment: 0.5 (1 + sech(sqrt(Er-1))) * du1."""
    return 0.5 * (1.0 + 1.0 / math.cosh(math.sqrt(er - 1.0))) * du1(u, tau)


def z0_microstrip(w: float, h: float, t: float, er: float) -> float:
    """Single-ended surface microstrip Z0, Hammerstad-Jensen with both
    thickness corrections (u1 for the air line, ur for the dielectric)."""
    u = w / h
    u1 = u + du1(u, t / h)
    ur = u + dur(u, t / h, er)
    z1, zr = z_air_u(u1), z_air_u(ur)
    ee = eeff_microstrip(ur, er) * (z1 / zr) ** 2
    return zr / math.sqrt(ee)


def _bisect(func, target: float, lo: float, hi: float) -> float | None:
    """Bisection on a decreasing func(x); returns x with func(x)=target."""
    if func(lo) - target < 0 or func(hi) - target > 0:
        return None
    for _ in range(120):
        mid = (lo + hi) / 2.0
        if func(mid) - target > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def solve_w_se(target: float, h: float, t: float, er: float,
               w_lo: float = 0.02, w_hi: float = 5.0) -> float | None:
    """Bisection for the W giving single-ended Z0 = target; None if unbracketed."""
    return _bisect(lambda w: z0_microstrip(w, h, t, er), target, w_lo, w_hi)


# ------------------------------------------------------- model: KJ pair

def even_odd(w: float, s: float, h: float, t: float, er: float
             ) -> tuple[float, float]:
    """Kirschning-Jansen static even/odd impedances (ohm) of the edge-coupled
    pair. The KJ equations assume zero-thickness strips; as an approximation
    the single line's dielectric width ratio ur is used as the KJ width
    ratio u throughout, and ee/zl are the single-line relations evaluated
    at ur."""
    u = w / h + dur(w / h, t / h, er)
    g = s / h
    ee = eeff_microstrip(u, er)
    zl = z0_u(u, er)

    v = u * (20.0 + g * g) / (10.0 + g * g) + g * math.exp(-g)
    ee_e = (er + 1.0) / 2.0 + (er - 1.0) / 2.0 * (1.0 + 10.0 / v) ** (
        -_hj_a(v) * _hj_b(er))

    a_o = 0.7287 * (ee - (er + 1.0) / 2.0) * (1.0 - math.exp(-0.179 * u))
    b_o = 0.747 * er / (0.15 + er)
    c_o = b_o - (b_o - 0.207) * math.exp(-0.414 * u)
    d_o = 0.593 + 0.694 * math.exp(-0.562 * u)
    ee_o = ee + ((er + 1.0) / 2.0 + a_o - ee) * math.exp(-c_o * g ** d_o)

    q1 = 0.8695 * u ** 0.194
    q2 = 1.0 + 0.7519 * g + 0.189 * g ** 2.31
    q3 = (0.1975 + (16.6 + (8.4 / g) ** 6) ** (-0.387)
          + math.log(g ** 10 / (1.0 + (g / 3.4) ** 10)) / 241.0)
    q4 = (2.0 * q1 / q2) / (math.exp(-g) * u ** q3
                            + (2.0 - math.exp(-g)) * u ** (-q3))
    q5 = 1.794 + 1.14 * math.log(1.0 + 0.638 / (g + 0.517 * g ** 2.43))
    q6 = (0.2305 + math.log(g ** 10 / (1.0 + (g / 5.8) ** 10)) / 281.3
          + math.log(1.0 + 0.598 * g ** 1.154) / 5.1)
    q7 = (10.0 + 190.0 * g * g) / (1.0 + 82.3 * g ** 3)
    q8 = math.exp(-6.5 - 0.95 * math.log(g) - (g / 0.15) ** 5)
    q9 = math.log(q7) * (q8 + 1.0 / 16.5)
    q10 = (q2 * q4 - q5 * math.exp(math.log(u) * q6 * u ** (-q9))) / q2

    z0f = 377.0
    z_e = zl * math.sqrt(ee / ee_e) / (1.0 - zl / z0f * math.sqrt(ee) * q4)
    z_o = zl * math.sqrt(ee / ee_o) / (1.0 - zl / z0f * math.sqrt(ee) * q10)
    return z_e, z_o


def zdiff(w: float, s: float, h: float, t: float, er: float) -> float:
    """Differential impedance = 2 x odd-mode, Kirschning-Jansen."""
    return 2.0 * even_odd(w, s, h, t, er)[1]


# -------------------------------------------------- comparison: IPC-2141A

def z0_ipc(w: float, h: float, t: float, er: float) -> float:
    """IPC-2141A surface microstrip (comparison only, see docstring)."""
    return 87.0 / math.sqrt(er + 1.41) * math.log(5.98 * h / (0.8 * w + t))


def zdiff_ipc(w: float, s: float, h: float, t: float, er: float) -> float:
    """IPC-2141A edge-coupled pair (comparison only)."""
    return 2.0 * z0_ipc(w, h, t, er) * (1.0 - 0.48 * math.exp(-0.96 * s / h))


def solve_w_se_ipc(target: float, h: float, t: float, er: float,
                   w_lo: float = 0.01, w_hi: float = 5.0) -> float | None:
    """IPC-2141A single-ended width solve (comparison only)."""
    return _bisect(lambda w: z0_ipc(w, h, t, er), target, w_lo, w_hi)


def solve_w_diff_ipc(target: float, s: float, h: float, t: float, er: float,
                     w_lo: float = W_SOLVE_RANGE_MM[0],
                     w_hi: float = W_SOLVE_RANGE_MM[1]) -> float | None:
    """IPC-2141A pair width solve (comparison only)."""
    return _bisect(lambda w: zdiff_ipc(w, s, h, t, er), target, w_lo, w_hi)


# ------------------------------------------------------------- stackup data

def dk_eff(plies: list[dict]) -> float:
    """Effective Dk of stacked prepreg plies (thickness-weighted harmonic mean)."""
    total = sum(p["thickness_mm"] for p in plies)
    return total / sum(p["thickness_mm"] / p["dk"] for p in plies)


def l1_l2(st: dict) -> tuple[float, float]:
    """(H, published effective Dk) between L1 and L2 for one stackup."""
    plies = st.get("prepreg_top") or []
    if not plies:
        raise ValueError("no L1-L2 prepreg plies recorded")
    h = 0.0
    for p in plies:
        if p.get("thickness_mm") is None or p.get("dk") is None:
            raise ValueError(f"prepreg ply {p!r} lacks thickness_mm or dk")
        h += p["thickness_mm"]
    if h <= 0:
        raise ValueError("L1-L2 dielectric height is not positive")
    return h, dk_eff(plies)


def total_thickness(st: dict) -> float:
    cu = st["copper"]
    inn = st["inner"]
    return (cu["outer_mm"] + sum(p["thickness_mm"] for p in st["prepreg_top"])
            + inn["l2_copper_mm"] + inn["core_mm"] + inn["l3_copper_mm"]
            + sum(p["thickness_mm"] for p in st["prepreg_bottom"])
            + cu["bottom_mm"])


BOARD_THICKNESS_MM = 1.6
# JLCPCB capabilities page: thickness tolerance +/-10% for boards >= 1.0 mm,
# i.e. a finished 1.6 mm board is 1.44-1.76 mm.
THICKNESS_TOL = 0.10


def check_stackup(st: dict) -> list[str]:
    """Problems that keep a stackup out of the impedance study."""
    errs = []
    try:
        l1_l2(st)
    except ValueError as exc:
        errs.append(str(exc))
    cu = st.get("copper") or {}
    if cu.get("outer_mm") is None or cu.get("inner_mm") is None:
        errs.append("copper thickness missing")
    if (st.get("inner") or {}).get("core_mm") is None:
        errs.append("core thickness missing")
    try:
        tot = total_thickness(st)
    except (KeyError, TypeError):
        errs.append("layer sum cannot be computed: value missing")
    else:
        lo = BOARD_THICKNESS_MM * (1 - THICKNESS_TOL)
        hi = BOARD_THICKNESS_MM * (1 + THICKNESS_TOL)
        if not lo <= tot <= hi:
            errs.append(f"layer sum {tot:.4f} mm outside {lo:.2f}-{hi:.2f} mm "
                        "(JLCPCB +/-10% for boards >= 1.0 mm)")
    return errs


def solve_w(target: float, s: float, h: float, t: float, er: float,
            w_lo: float = W_SOLVE_RANGE_MM[0], w_hi: float = W_SOLVE_RANGE_MM[1]
            ) -> float | None:
    """Bisection for the W in [w_lo, w_hi] giving Zdiff = target; None if none."""
    return _bisect(lambda w: zdiff(w, s, h, t, er), target, w_lo, w_hi)


def _fmt_w(w: float | None) -> str:
    return "n/a" if w is None else f"{w:.3f}"


def recommended_pair(st: dict) -> tuple[float, float, float]:
    """Zdiff of the recommended pair on stackup st: (nominal, W -TRACK_TOL, W +TRACK_TOL)."""
    h, dk = l1_l2(st)
    return tuple(zdiff(REC_W_MM * k, REC_S_MM, h, T_OUTER_MM, dk)
                 for k in (1.0, 1.0 - TRACK_TOL, 1.0 + TRACK_TOL))


def main(stackups: list[dict] | None = None) -> int:
    if stackups is None:
        stackups = json.loads(STACKUPS_JSON.read_text(encoding="utf-8"))["stackups"]
    by_id = {s["id"]: s for s in stackups}

    print("Hammerstad-Jensen microstrip + Kirschning-Jansen edge-coupled pair "
          "(static), L1 over L2 ground, published Dk.")
    print(f"T = {T_OUTER_MM:.4f} mm (JLCPCB calculator: finished 1 oz outer = 1.6 mil); "
          "solder mask, etch trapezoid and ENIG are NOT modelled (mask lowers Z, "
          "narrowed etch raises it slightly, ENIG ~negligible).")

    # -- Comparison vs JLCPCB's own single-ended datum ------------------------
    ref = by_id.get(JLCPCB_REF_STACKUP_ID)
    print("\nReference vs JLCPCB's own calculator (browser run 2026-11-03, "
          f"{JLCPCB_REF_STACKUP_ID}, L1/L2):")
    if ref is not None and not check_stackup(ref):
        h_ref, dk_ref = l1_l2(ref)
        w50_hj = solve_w_se(JLCPCB_SE_TARGET_OHM, h_ref, T_OUTER_MM, dk_ref)
        w50_ipc = solve_w_se_ipc(JLCPCB_SE_TARGET_OHM, h_ref, T_OUTER_MM, dk_ref)
        w_datum = JLCPCB_SE_BARE_MIL * MIL_MM
        z_masked = z0_microstrip(JLCPCB_SE_MASKED_MIL * MIL_MM,
                                 h_ref, T_OUTER_MM, dk_ref)
        print(f"  JLCPCB 50-ohm single-ended, no mask: W = {JLCPCB_SE_BARE_MIL} mil "
              f"(with mask: {JLCPCB_SE_MASKED_MIL} mil)")
        print(f"  HJ model at published Dk {dk_ref:.2f}: W = {w50_hj / MIL_MM:.2f} mil "
              f"({(w50_hj / w_datum - 1) * 100:+.1f}%)")
        print(f"  IPC-2141A comparison: W = {w50_ipc / MIL_MM:.2f} mil "
              f"({(w50_ipc / w_datum - 1) * 100:+.1f}%)")
        print(f"  mask effect on a single line: bare Z0({JLCPCB_SE_MASKED_MIL} mil) "
              f"= {z_masked:.1f} ohm -> mask removes ~{z_masked - 50.0:.1f} ohm "
              "at 50 ohm; on the pair it is larger and not quantified")
    else:
        print(f"  WARNING: reference stackup {JLCPCB_REF_STACKUP_ID} missing or "
              "has no usable data.")

    # ---------------------------------------------------------------- loop
    problems: list[str] = []
    n_usable = 0
    for st in stackups:
        errs = check_stackup(st)
        try:
            tot = f"{total_thickness(st):.4f} mm"
        except (KeyError, TypeError):
            tot = "n/a"
        print(f"\n=== {st['id']}  (sum {tot}) ===")
        if errs:
            print("  missing data: " + "; ".join(errs))
            problems.append(f"{st['id']}: {'; '.join(errs)}")
            continue
        h, dk = l1_l2(st)
        plies = "+".join(f"{p['style']}x{p['thickness_mm']}mm" for p in st["prepreg_top"])
        print(f"  L1-L2: H = {h:.4f} mm ({plies}), Dk = {dk:.3f}")
        print("   W\\S   " + "   ".join(f"S={s:.2f} KJ|IPC" for s in GAPS_MM)
              + "   <- Zdiff [ohm]")
        for w in GRID_W_MM:
            cells = "   ".join(
                f"{zdiff(w, s, h, T_OUTER_MM, dk):5.1f}|{zdiff_ipc(w, s, h, T_OUTER_MM, dk):5.1f}"
                for s in GAPS_MM)
            print(f"  {w:>5.2f}  {cells}")
        solved_anywhere = False
        for s in GAPS_MM:
            w90 = solve_w(TARGET_OHM, s, h, T_OUTER_MM, dk)
            w90_ipc = solve_w_diff_ipc(TARGET_OHM, s, h, T_OUTER_MM, dk)
            if w90 is None:
                wide = solve_w(TARGET_OHM, s, h, T_OUTER_MM, dk,
                               w_hi=W_SEARCH_HI_MM)
                print(f"  S={s:.2f}: no W in {W_SOLVE_RANGE_MM[0]}-"
                      f"{W_SOLVE_RANGE_MM[1]} mm reaches {TARGET_OHM:.0f} ohm"
                      + (f" (needs ~{wide:.3f} mm)" if wide else " (impossible data)"))
                continue
            solved_anywhere = True
            w99 = solve_w(BAND_OHM[1], s, h, T_OUTER_MM, dk)
            w81 = solve_w(BAND_OHM[0], s, h, T_OUTER_MM, dk)
            print(f"  S={s:.2f}: W90 = {w90:.3f} mm KJ / {_fmt_w(w90_ipc)} mm IPC; "
                  f"81-99 window {_fmt_w(w99)}-{_fmt_w(w81)} mm")
        if not solved_anywhere:
            print(f"  UNREACHABLE: no W in {W_SOLVE_RANGE_MM[0]}-{W_SOLVE_RANGE_MM[1]} mm "
                  f"reaches {TARGET_OHM:.0f} ohm at any gap (a finding, not an error)")
        else:
            n_usable += 1
    print(f"\n{len(stackups)} stackups: {n_usable} with a reachable 90-ohm W, "
          f"{len(stackups) - n_usable} missing/unreachable")

    rec = by_id.get(REC_STACKUP_ID)
    if rec is None or check_stackup(rec):
        problems.append(f"recommended stackup {REC_STACKUP_ID} absent or missing data")
    else:
        z_nom, z_narrow, z_wide = recommended_pair(rec)
        print(f"\nRecommended pair on {REC_STACKUP_ID}: W = {REC_W_MM:.2f} mm, "
              f"S = {REC_S_MM:.2f} mm -> Zdiff = {z_nom:.1f} ohm (bare model); "
              f"W -{TRACK_TOL:.0%} -> {z_narrow:.1f} ohm, W +{TRACK_TOL:.0%} -> "
              f"{z_wide:.1f} ohm (S held)")
        if not BAND_OHM[0] <= z_nom <= BAND_OHM[1]:
            problems.append(f"recommended pair gives {z_nom:.1f} ohm, outside "
                            f"{BAND_OHM[0]:.0f}-{BAND_OHM[1]:.0f} ohm")
    if problems:
        for p in problems:
            print("PROBLEM: " + p, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
