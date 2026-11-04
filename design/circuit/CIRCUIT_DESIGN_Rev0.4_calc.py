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
- tolerances and temperature; it uses typical or bounding datasheet values as
  noted. The OP07 limits come from TI SLOS099F's 15 V single-supply row, applied
  to the 12 V rail (D28); the mirror loop's stability is not computed at all;
- the MCP3208's real sampling network: the S/H settling below uses the
  datasheet's Figure 4-1 model (1 kohm switch, 20 pF, 7 pF pin) and assumes the
  sample capacitor starts at the previous channel's voltage (checked on the
  first board, V-MEAS-06);
- layout parasitics, comparator delay spread, and the real gate charge;
- Y1's motional capacitance C1 (not on the C9002 sheet, so it is swept) and the
  RP2040 oscillator's own gain: crystal start-up is only compared, as a ratio, with
  Raspberry Pi's reference design (checked on the first board, V-MEAS-06);
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
i_mid = 5.0 / (SPAN["MID"] + RSW + RWIRE)
p_mid = i_mid * i_mid * RS["MID"]
rcwv = math.sqrt(1.0 * RS["MID"])      # Faithful Link MFU: RCWV = sqrt(rated power x R), 1 W
p_sto = (2.5 * rcwv) ** 2 / RS["MID"]  # short-time overload: 2.5 x RCWV for 5 s, dR <= 1 %
p_pul = (4.0 * rcwv) ** 2 / RS["MID"]  # pulse overload: 4 x RCWV, 1 s on / 25 s off, 10,000 cycles
print(f"R_M (MFU100F10RB) RCWV {rcwv:.2f} V: short-time overload {p_sto:.2f} W for 5 s"
      f" ({p_sto*5:.1f} J), pulse overload {p_pul:.1f} W for 1 s ({p_pul:.0f} J) x 10,000;"
      f" fault {p_mid:.2f} W for 10 ms = {p_mid*10e-3*1e3:.1f} mJ ->"
      f" power {p_sto/p_mid:.1f}x, energy {p_sto*5/(p_mid*10e-3):.0f}x inside the 5 s rating;"
      f" {p_mid:.2f} W stays inside it for up to 5 s")

print("\n== Sec. 3.1 / Sec. 7.2 DUT voltage at the port on HIGH (F1 shared, at R1max)")
for i, other in ((0.5, 0.0), (1.0, 0.0), (1.0, 1.0)):
    drop = i * (RSW + SPAN["HIGH"] + RWIRE) + (i + other) * RF1
    print(f"I={i} A, other port {other} A: drop={drop:.3f} V  port at J4 5.00 V={5-drop:.3f}"
          f"  at 4.75 V={4.75-drop:.3f}")
print(f"4.75 V at the port at 0.5 A needs J4 >= {4.75 + 0.5*(RSW+SPAN['HIGH']+RWIRE+RF1):.3f} V")

print("\n== Sec. 3.2 mirror FET gate headroom at HIGH full scale 1 A (|V_GS(th)| 1.3 V)")
VOL_AVD = 1.4    # SLOS099F A_VD row: V_CC = 15 V single supply, V_O = 1.4..11.4 V, R_L >= 500 kohm
VOL_EXT = 3.0    # Rev0.4 extrapolation from V_OM +-12 V into 10 kohm at +-15 V (superseded, D28)
gates = []
for vj4 in (5.0, 4.75):
    for other in (0.0, 1.0):
        src = vj4 - (1.0 + other) * RF1 - 1.0 * (RSW + RS["HIGH"] + RWIRE)
        gate = src - 1.3
        gates.append(gate)
        print(f"J4={vj4}, other port {other} A: source {src:.3f} V gate~{gate:.3f} V"
              f"  headroom={gate-VOL_AVD:.2f} V over the {VOL_AVD} V row"
              f" ({gate-VOL_EXT:.2f} V over the old {VOL_EXT} V extrapolation)")
print(f"without F1, old basis: headroom {5.0-1.0*(RSW+RS['HIGH']+RWIRE)-1.3-VOL_EXT:.2f} V at J4 5.0,"
      f" {4.75-1.0*(RSW+RS['HIGH']+RWIRE)-1.3-VOL_EXT:.2f} V at J4 4.75")
print(f"V-MEAS-00 low supply: J4 4.75 V less F1 at 2 A = {4.75-2*RF1:.2f} V")

print("\n== Sec. 3.2 OP07 on V12F, against SLOS099F (D28 desk check)")
V12_MIN = 12.0 * (1 - 0.03 - 0.05 * 1.2) - 10.0 * 30e-3   # MAU104 -3 % max, J1 at -5 % x 1.2 line
                                         # regulation, less 10 ohm at the 30 mA maximum load
VOH_AVD = 15.0 - 11.4                    # the same row's upper end sits 3.6 V below V+
CM_LO, CM_HI = 4.4, 5.25                 # mirror input common mode (port supply range)
print(f"V12F min {V12_MIN:.2f} V -> linear output {VOL_AVD:.1f}..{V12_MIN-VOH_AVD:.2f} V;"
      f" the gate spans {min(gates):.2f} V (HIGH at 1 A, worst corner) to {CM_HI:.2f} V (off, at the source)")
print(f"common mode {CM_LO}..{CM_HI} V: {CM_LO:.2f} V above V-, {V12_MIN-CM_HI:.2f} V below V+"
      f" (VICR +-13 V at +-15 V = 2 V from each rail; kSVS row runs at +-3 V, i.e. 3 V from each)")
IGSS = 100e-9                            # AO3401A I_GSS max at V_GS +-12 V
print(f"gate DC load: I_GSS {IGSS*1e9:.0f} nA at <= {CM_HI:.2f} V -> >= {CM_HI/IGSS/1e6:.0f} Mohm"
      " against the row's 500 kohm")
CISS, CRSS = 645e-12, 55e-12
print(f"gate network pole, 1 kohm into C_iss {CISS*1e12:.0f} pF: {1/(2*math.pi*1e3*CISS)/1e3:.0f} kHz,"
      f" against OP07 GBW 0.4 min / 0.6 typ MHz; C_rss {CRSS*1e12:.0f} pF is Miller-multiplied by the"
      " drain node: stability is NOT settled here (V-MEAS-00 at bring-up)")

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
loads = {"CH335F": 85, "RP2040 + W25Q128JV flash with USB, estimate": 30, "MAU104 input": 70,
         "LM393 x3": 3, "LEDs": 5, "AMS1117 Iq": 5, "CJ431 x2 + dividers": 2,
         "MCP3208 x2 (0.4 mA max each)": 1, "SPI level shifters, 3 x 5 V / 1.5 kohm": 10}
print(f"total {sum(loads.values())} mA")
hub = loads["CH335F"]
func = sum(loads.values()) - hub
mau_extra = 6 * 2.5 * 12.0 / 0.78 / 5.0     # every OP07 at 5 mA max instead of 2.5 typ; MAU104 78 %
print(f"hub {hub} mA (declares 100 mA); MCU function {func} mA typ, {func + mau_extra:.0f} mA with"
      f" every OP07 at max (J1 then {hub + func + mau_extra:.0f} mA) -> function declares 200 mA (D26),"
      f" declarations total {100 + 200} mA")
v3v3 = {"RP2040 + W25Q128JV flash, estimate": 30, "LEDs, Rp, pull-ups, VDDA, CJ431 U3 (as Rev0.3)": 15,
        "HOLD pull-ups 4 x 3.3 V / 10 kohm": 1.3, "MCP3208 V_REF x2": 0.3}
i3 = sum(v3v3.values())
p = (5.0 - 3.3) * i3 / 1e3
print(f"V3V3 load {i3:.1f} mA; AMS1117: {p:.3f} W -> {p*90:.1f} C rise at 90 C/W")

print("\n== Sec. 7.1 / Sec. 6.1 U1, the bare RP2040 (D29), and U8 on V3V3")
V3V3_MIN, V3V3_MAX = 3.251, 3.349   # AMS1117-3.3 output (parts.md)
RAILS = {"USB_VDD": (3.135, 3.63), "IOVDD": (1.62, 3.63), "VREG_VIN": (1.62, 3.63),
         "ADC_AVDD": (1.62, 3.63), "W25Q128JV VCC": (2.7, 3.6)}   # RP2040 DS Table 634; Winbond
for pin, (lo, hi) in RAILS.items():
    print(f"{pin} {lo}-{hi} V on V3V3 {V3V3_MIN}-{V3V3_MAX} V: margin {V3V3_MIN-lo:+.3f} V low,"
          f" {hi-V3V3_MAX:+.3f} V high")
I_DVDD = {"BOOTSEL active": 14.7, "Popcorn demo": 16.6}   # DS Table 637, maximum column, mA
for case, i in I_DVDD.items():
    print(f"DVDD {case} {i} mA max vs the on-chip regulator's 100 mA: {100/i:.1f} x;"
          f" its loss (V3V3 max - 1.1 V) x I = {(V3V3_MAX-1.1)*i:.0f} mW")

print("\n== Sec. 7.1 / Sec. 6.6 U6, the bare CH335F (D31), on V5L")
V5L_MIN, V5L_MAX, V5L_CORNER = 4.5, 5.25, 5.5   # design range (Sec. 3.2); the USB-C 5.5 V corner
V5_OP = (4.5, 5.25)                             # CH334/335 DS V2.5 Sec. 4.2, internal LDO on
V5_ABS = 5.5                                    # DS Sec. 4.1, absolute maximum
print(f"V5 {V5_OP[0]}-{V5_OP[1]} V on V5L {V5L_MIN}-{V5L_MAX} V: margin {V5L_MIN-V5_OP[0]:+.2f} V low,"
      f" {V5_OP[1]-V5L_MAX:+.2f} V high; at the {V5L_CORNER} V corner {V5_ABS-V5L_CORNER:+.2f} V"
      f" to the {V5_ABS} V absolute maximum")
for v in (5.0, V5L_MAX):
    print(f"U6 at {hub} mA from {v} V: {v*hub:.0f} mW, of which its LDO (V5 - 3.3 V) {(v-3.3)*hub:.0f} mW")
i3_hub = i3 + hub
p_alt = (5.0 - 3.3) * i3_hub / 1e3
print(f"not adopted, V5 and VDD33 fed from V3V3 (DS Sec. 6.1): U6 {3.3*hub:.0f} mW, but V3V3 carries"
      f" {i3_hub:.1f} mA and the AMS1117 {p_alt:.3f} W -> {p_alt*90:.1f} C rise at 90 C/W")

print("\n== Sec. 3.3 USB series termination per line: 22 ohm (C25092) + 5.1 ohm (C25197), both +-1 %")
r_nom = 22.0 + 5.1
r_lo, r_hi = 0.99 * r_nom, 1.01 * r_nom
print(f"{r_nom:.1f} ohm, {r_lo:.2f}-{r_hi:.2f} ohm against the 27 ohm the RP2040 requires"
      f" ({100*(r_lo/27-1):+.1f} % / {100*(r_hi/27-1):+.1f} %; the datasheet states no tolerance)")

print("\n== Sec. 6.3 Y1 = C9002 (C_L 20 pF) on the RP2040 XOSC with the reference 2 x 15 pF")
CL_RATED = 20e-12                    # C9002
C_CAP = 15e-12                       # two 15 pF C0G (C1548), "Hardware design with RP2040"
C_STRAY = (2e-12, 3e-12, 5e-12)      # the reference design assumes 3 pF; swept
C0 = (1e-12, 3e-12)                  # C9002 shunt capacitance: 3 pF max; 1 pF as a low bound
C1 = (2e-15, 5e-15, 10e-15, 20e-15)  # motional capacitance: not on the C9002 sheet; swept
TOL = 10 + 20 + 3                    # ppm: tolerance at 25 C + over temperature + first year
print(f"load as built {(C_CAP/2 + 3e-12)*1e12:.1f} pF (3 pF stray), swept"
      f" {(C_CAP/2 + C_STRAY[0])*1e12:.1f}-{(C_CAP/2 + C_STRAY[-1])*1e12:.1f} pF,"
      f" against the {CL_RATED*1e12:.0f} pF it is rated for")
for c1 in C1:
    pull = max(c1 / 2 * (1 / (c0 + C_CAP / 2 + cs) - 1 / (c0 + CL_RATED)) * 1e6
               for cs in C_STRAY for c0 in C0)
    print(f"C1 {c1*1e15:.0f} fF: pulled high by <= {pull:.0f} ppm; with +-{TOL} ppm"
          f" <= {pull + TOL:.0f} ppm, against the 1000 ppm the RP2040 tolerates")
gain = ((3e-12 + CL_RATED) / (3e-12 + C_CAP / 2 + 3e-12)) ** 2
print(f"loading it to 20 pF instead (2 x 33 pF) raises the oscillator's critical gain"
      f" {gain:.1f} x (g_m,crit ~ ESR (C0 + C_L)^2)")
print(f"start-up margin against the reference crystal (ABM8-272-T3, ESR 50 ohm max, C0 3 pF max),"
      f" same load: 50 / 80 = {50/80:.3f} x")

print("\n== Sec. 3.2 reset hold (D28 desk check)")
for rpd in (50e3, 80e3):
    v = V3V3_MIN * rpd / (rpd + 10e3 * 1.01)
    print(f"reset hold: RP2040 pull-down {rpd/1e3:.0f} k vs 10 k +1 % to V3V3 min -> gate {v:.3f} V"
          f" vs 2N7002 V_th max 2.5 V at 250 uA (it then sinks only Q17/Q18's 1 Mohm return,"
          f" <= {5.25/1e6*1e6:.2f} uA at a 5.25 V port)")
print(f"MAU104 load: 6 x OP07 at 2.5 typ / 5 max mA = {6*2.5:.0f} / {6*5:.0f} mA")
