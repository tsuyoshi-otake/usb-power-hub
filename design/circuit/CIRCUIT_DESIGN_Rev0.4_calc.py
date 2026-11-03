#!/usr/bin/env python3
"""Reproduce the calculated numbers quoted in CIRCUIT_DESIGN_Rev0.4.md.

Usage:
    python design/circuit/CIRCUIT_DESIGN_Rev0.4_calc.py

Every section header names the document section that quotes its output. The
inputs below are the Rev0.4 component values and datasheet or catalogue
figures recorded in requirements/parts.md. Change a value here and in the
document together; the document is the design, this script is its arithmetic.

What this script CANNOT see (CLAUDE.md Section 8 - a checker only proves what
it looks at):
- whether an input value is the one the document and parts.md actually state:
  it holds its own copy of them;
- tolerances, temperature, and the OP07 single-supply behaviour it assumes
  (OI-27); it uses typical or bounding datasheet values as noted;
- the MCP3208's real sampling network: the S/H settling below uses the
  datasheet's Figure 4-1 model (1 kohm switch, 20 pF, 7 pF pin) and assumes the
  sample capacitor starts at the previous channel's voltage (OI-31);
- layout parasitics, comparator delay spread, and the real gate charge;
- anything about part availability or footprints.
"""
import math

# ---- inputs (Rev0.4 values) -------------------------------------------------
VDDA = 3.3                    # MCP3208 V_REF = VDDA (its V_DD is V5A, 5 V)
LSB = VDDA / 4096             # 12-bit
RS = {"LOW": 510.0, "MID": 10.0, "HIGH": 0.1}    # shunts R_L, R_M, R_H
R1 = 100.0                    # mirror input resistor, every range
ROUT = {"LOW": 1500.0, "MID": 1500.0, "HIGH": 2400.0}
CN = {"LOW": 330e-12, "MID": 330e-12, "HIGH": 220e-12}
RDS = 0.060                   # AO3401A R_DS(on) max at -4.5 V
RSW = 2 * RDS                 # back-to-back port switch
RWIRE = 0.040                 # traces, headers and receptacle, estimate
RF1 = 0.080                   # F1 MF-R300 R1max (1 h after reflow or trip); Rmin 0.020
IHOLD_F1 = {23: 3.00, 40: 2.49, 50: 2.31}   # F1 hold current vs ambient (Bourns derating)
VTH = 2.80                    # LM393 up-range / OC threshold at the amp output
VINJ, RINJ = 8.0, 1e6         # pedestal injection (U4 CJ431 8 V through 1 Mohm)
VOS = 150e-6                  # OP07D max V_os, used as a bound (OP07C has no max)
CPORT = 10e-6                 # port capacitor
STAGE = 3e-6                  # ranging budget per stage
FCLK = 1.0e6                  # MCP3208 clock: 1 MHz is guaranteed down to V_DD 2.7 V
T_SAMPLE = 4.5e-6            # sample phase as stretched by the RP2040 PIO (native 1.5 clocks)
CLK_PER_CONV = 20            # datasheet: f_CLK = 20 x f_SAMPLE
R_SER = 1e3                  # series resistor, amplifier node -> ADC pin
C_PIN, C_S, R_SS = 7e-12, 20e-12, 1e3   # MCP3208 Figure 4-1 input model
K = {r: RS[r] * ROUT[r] / R1 for r in RS}        # V per A at the amp output
PED = {r: (VINJ - 5.0) / RINJ * ROUT[r] for r in RS}   # pedestal at the amp output, 5.0 V port
IT = {r: (VTH - PED[r]) / K[r] for r in RS}      # current at which the comparator trips
SPAN = {"LOW": RS["HIGH"] + RS["MID"] + RS["LOW"],   # ladder resistance on each range
        "MID": RS["HIGH"] + RS["MID"] + RDS,         # FET_L bypasses R_L
        "HIGH": RS["HIGH"] + RDS}                    # FET_M bypasses R_M + R_L

print("== Sec. 3.2 / Sec. 4 transfer, pedestal, thresholds (pedestal at a 5.0 V port)")
for r in ("LOW", "MID", "HIGH"):
    ped = PED[r]
    print(f"{r:4s} G={ROUT[r]/R1:.0f} k={K[r]:.4g} V/A  LSB={LSB/K[r]:.4g} A  3LSB={3*LSB/K[r]:.4g} A"
          f"  clip={(VDDA-ped)/K[r]:.4g} A  I_T={IT[r]:.4g} A"
          f"  ped={ped*1e3:.3g} mV ({ped/LSB:.1f} LSB)  tauN={ROUT[r]*CN[r]*1e6:.3g} us")
print(f"LSB ratio MID/LOW={K['LOW']/K['MID']:.1f}  HIGH/MID={K['MID']/K['HIGH']:.1f}")

print("\n== Sec. 4.1 pedestal injection over a 4.4-5.25 V port supply")
inj = [(VINJ - vx) / RINJ for vx in (5.25, 4.4)]
print(f"injection {inj[0]*1e6:.2f}..{inj[1]*1e6:.2f} uA; needed > V_os/R1 = {VOS/R1*1e6:.2f} uA"
      f" -> margin {inj[0]/(VOS/R1):.2f}x")
print(f"LOW pedestal slope vs port voltage: {ROUT['LOW']/RINJ*1e3:.2g} mV/V")
for r in ("LOW", "HIGH"):
    vos_out = VOS * ROUT[r] / R1
    print(f"{r} zero error before calibration: pedestal {PED[r]/LSB:.1f} LSB"
          f" + |V_os| x G {vos_out/LSB:.1f} LSB = up to {(PED[r]+vos_out)/LSB:.1f} LSB")
dv12 = 12.0 * 0.05 * 1.2      # J1 +-5 %, MAU104 line regulation 1.2 % per 1 %
print(f"without U4 (R_INJ fed from V12): +-5 % on J1 moves V12 by {dv12:.2f} V ->"
      f" LOW pedestal by {dv12/RINJ*ROUT['LOW']*1e3:.2f} mV = {dv12/RINJ*ROUT['LOW']/LSB:.1f} LSB"
      " (load regulation below 20 % load is not specified and adds to this)")

print("\n== Sec. 3.2 MID gain that would equalise the two range ratios")
ratio = math.sqrt(K["LOW"] / K["HIGH"])
g_mid = K["LOW"] / ratio / RS["MID"]
print(f"equal ratio {ratio:.1f} -> MID gain {g_mid:.2f} (R_OUT {g_mid*R1:.0f} ohm);"
      f" gain 12 gives {K['LOW']/(RS['MID']*12):.2f} / {RS['MID']*12/K['HIGH']:.1f}")

print("\n== Sec. 4 burden at the up-range threshold (whole ladder)")
for r in ("LOW", "MID"):
    it = IT[r]
    print(f"{r} I_T={it*1e3:.4g} mA  ladder={SPAN[r]:.2f} ohm  burden={it*SPAN[r]:.4f} V")
print(f"HIGH at 1 A: {1.0*SPAN['HIGH']:.2f} V")

print("\n== Sec. 4 bottom-of-range floor (down-range at 0.8 * I_T of the range below)")
for r, below in (("MID", "LOW"), ("HIGH", "MID")):
    i = 0.8 * IT[below]
    f = 3 * LSB / K[r]
    print(f"{r} bottom={i*1e3:.4g} mA  3LSB={f*1e6:.4g} uA = {100*f/i:.2f} % (+1 % = {1+100*f/i:.2f} %)")

print("\n== Sec. 4 port bandwidth with the 10 uF port capacitor")
for r in ("LOW", "MID", "HIGH"):
    tau = SPAN[r] * CPORT
    print(f"{r} tau={tau*1e6:.4g} us  f={1/(2*math.pi*tau):.4g} Hz")

print("\n== Sec. 4 ride-through: step while on LOW, two stages, port cap supplies it")
for istep in (1.0, 0.3):
    print(f"{istep} A: {istep*2*STAGE/CPORT:.2f} V at 3 us/stage, {istep*2*4e-6/CPORT:.2f} V at 4 us/stage")

print("\n== Sec. 4 stuck range into a short at the port (J4 5.0 V, below the OC trip)")
for r in ("LOW", "MID"):
    i = 5.0 / (SPAN[r] + RSW + RWIRE)
    print(f"stuck {r}: I={i:.4g} A  P({RS[r]:g} ohm)={i*i*RS[r]:.3g} W")

print("\n== Sec. 3.1 / Sec. 7.2 DUT voltage at the port on HIGH (F1 shared, at R1max)")
for i, other in ((0.5, 0.0), (1.0, 0.0), (1.0, 1.0)):
    drop = i * (RSW + SPAN["HIGH"] + RWIRE) + (i + other) * RF1
    print(f"I={i} A, other port {other} A: drop={drop:.3f} V  port at J4 5.00 V={5-drop:.3f}"
          f"  at 4.75 V={4.75-drop:.3f}")
print(f"4.75 V at the port at 0.5 A needs J4 >= {4.75 + 0.5*(RSW+SPAN['HIGH']+RWIRE+RF1):.3f} V")

print("\n== Sec. 3.2 mirror FET gate headroom at HIGH full scale 1 A (|V_GS(th)| 1.3 V, OP07 V_OL 3.0 V)")
for vj4 in (5.0, 4.75):
    for other in (0.0, 1.0):
        src = vj4 - (1.0 + other) * RF1 - 1.0 * (RSW + RS["HIGH"] + RWIRE)
        gate = src - 1.3
        print(f"J4={vj4}, other port {other} A: source {src:.3f} V gate~{gate:.3f} V"
              f"  headroom={gate-3.0:.2f} V")
print(f"without F1: headroom {5.0-1.0*(RSW+RS['HIGH']+RWIRE)-1.3-3.0:.2f} V at J4 5.0,"
      f" {4.75-1.0*(RSW+RS['HIGH']+RWIRE)-1.3-3.0:.2f} V at J4 4.75")
print(f"V-MEAS-00 low supply: J4 4.75 V less F1 at 2 A = {4.75-2*RF1:.2f} V")

print("\n== Sec. 7.2 F1 hold margin and dissipation (both ports just below the OC trip)")
i_f1 = 2 * IT["HIGH"]
for t, ih in IHOLD_F1.items():
    print(f"{t} C: I_hold {ih:.2f} A vs {i_f1:.2f} A -> margin {ih - i_f1:+.2f} A")
print(f"F1 dissipation at {i_f1:.2f} A and R1max: {i_f1*i_f1*RF1:.2f} W")

print("\n== Sec. 3.3 ADC timing and stream (2 x MCP3208, shared CLK/CS/DIN, one DOUT each)")
t_conv = CLK_PER_CONV / FCLK + (T_SAMPLE - 1.5 / FCLK)
scan = 3 * t_conv
n_scan = int((1e-3 - t_conv) / scan)          # scans per 1 ms frame, one aux conversion per frame
rate = n_scan / 1e-3
print(f"t_conv={t_conv*1e6:.3g} us (native {CLK_PER_CONV/FCLK*1e6:.3g} us + {(T_SAMPLE-1.5/FCLK)*1e6:.3g} us stretch)"
      f"  scan={scan*1e6:.3g} us  {n_scan} scans + 1 aux per 1 ms ->"
      f" {rate/1e3:.4g} kSPS; idle {(1e-3-n_scan*scan-t_conv)*1e6:.3g} us per frame")
print(f"stream: 5 B/pair -> {5*rate/1e3:.4g} kB/s = {100*5*rate/1.188e6:.2f} % of FS bulk (1188 kB/s)")
dbl = 2 * CLK_PER_CONV / FCLK
n_dbl = int((1e-3 - CLK_PER_CONV / FCLK) / (3 * dbl))
print(f"fallback without stretching, each channel converted twice: {n_dbl} scans per 1 ms -> {n_dbl} kSPS")


def sh_residual(rout, cn, t_s, v0, vprev, dt=0.25e-9):
    """Error of the sampled voltage at the end of the sample phase, in LSB."""
    vn = vp = v0
    vs = vprev
    im = v0 / rout
    for _ in range(int(t_s / dt)):
        i_ser = (vn - vp) / R_SER
        i_ss = (vp - vs) / R_SS
        vn += dt * (im - vn / rout - i_ser) / cn
        vp += dt * (i_ser - i_ss) / C_PIN
        vs += dt * i_ss / C_S
    return (vs - v0) / LSB


for r in ("LOW", "HIGH"):
    res = {t: max(abs(sh_residual(ROUT[r], CN[r], t, VDDA, 0.0)), abs(sh_residual(ROUT[r], CN[r], t, 0.0, VDDA)))
           for t in (1.5 / FCLK, T_SAMPLE)}
    print(f"{r} S/H residual, 3.3 V step between channels: native 1.5 us {res[1.5/FCLK]:.3g} LSB,"
          f" stretched {T_SAMPLE*1e6:.3g} us {res[T_SAMPLE]:.3g} LSB")
for j4, v5 in ((5.25, 4.5), (5.5, 4.75), (5.5, 4.5)):
    for r in ("LOW", "HIGH"):
        node = j4 * ROUT[r] / (ROUT[r] + R1 + RDS)
        print(f"overrange J4={j4} V, V5A={v5} V: {r} node max {node:.2f} V vs pin abs max {v5+0.6:.2f} V"
              f" -> margin {v5+0.6-node:+.2f} V")
node_hi = 5.25 * ROUT["HIGH"] / (ROUT["HIGH"] + R1 + RDS)
print(f"(with V_DD = 3.3 V instead, the HIGH node at J4 5.25 V would drive"
      f" {(node_hi-3.9)/R_SER*1e3:.2f} mA through 1 kohm into a pin rated only to 3.9 V)")

print("\n== Sec. 3.2 ranging stage time: node tau + LM393 1.3 us + 7 nC gate charge at 6 mA")
for r in ("LOW", "MID"):
    t = ROUT[r] * CN[r] + 1.3e-6 + 7e-9 / 6e-3
    print(f"{r} {t*1e6:.3g} us worst")
c_gate = 1e-9
print(f"latch window: tau={1e6*c_gate*1e3:.3g} ms, |V_GS| 5 V -> 1.3 V in"
      f" {1e6*c_gate*math.log(5/1.3)*1e3:.3g} ms")

print("\n== Sec. 3.4 CC voltage at the DUT: Rp 33 k +-1 % from EN (V_OH 2.9-3.3 V), DUT Rd 5.1 k +-10 %")
vmin = 2.9 * (5.1e3 * 0.9) / (5.1e3 * 0.9 + 33e3 * 1.01)
vmax = 3.3 * (5.1e3 * 1.1) / (5.1e3 * 1.1 + 33e3 * 0.99)
print(f"{vmin:.3f}..{vmax:.3f} V (Default vRd window 0.25-0.61 V)")

print("\n== Sec. 7.1 J1 load (typical) and AMS1117")
loads = {"CH335F": 85, "RP2040 (PGA2040) + USB, estimate": 30, "MAU104 input": 70,
         "LM393 x3": 3, "LEDs": 5, "AMS1117 Iq": 5, "CJ431 x2 + dividers": 2,
         "MCP3208 x2 (0.4 mA max each)": 1, "SPI level shifters, 3 x 5 V / 1.5 kohm": 10}
print(f"total {sum(loads.values())} mA")
v3v3 = {"RP2040 (PGA2040), estimate": 30, "LEDs, Rp, pull-ups, VDDA, CJ431 U3 (as Rev0.3)": 15,
        "HOLD pull-ups 4 x 3.3 V / 10 kohm": 1.3, "MCP3208 V_REF x2": 0.3}
i3 = sum(v3v3.values())
p = (5.0 - 3.3) * i3 / 1e3
print(f"V3V3 load {i3:.1f} mA; AMS1117: {p:.3f} W -> {p*90:.1f} C rise at 90 C/W")
print(f"MAU104 load: 6 x OP07 at 2.5 typ / 5 max mA = {6*2.5:.0f} / {6*5:.0f} mA")
