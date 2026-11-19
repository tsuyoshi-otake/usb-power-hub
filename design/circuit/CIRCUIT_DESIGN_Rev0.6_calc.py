#!/usr/bin/env python3
"""Reproduce the calculated numbers quoted in CIRCUIT_DESIGN_Rev0.5.md.

Usage:
    python design/circuit/CIRCUIT_DESIGN_Rev0.5_calc.py

Every section header names the document section that quotes its output. The
inputs below are the Rev0.4 component values (Rev0.5's D37 and D38 change none of
them) and datasheet or catalogue figures recorded in requirements/parts.md. Change a value here and in the
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

# ---- inputs (Rev0.4 values, unchanged by Rev0.5) -------------------------------------------------
VDDA = 3.3                    # MCP3208 V_REF = VDDA (its V_DD is V5A, 5 V)
LSB = VDDA / 4096             # 12-bit
RS = {"LOW": 510.0, "MID": 10.0, "HIGH": 0.1}    # shunts R_L, R_M, R_H
R1 = 100.0                    # mirror input resistor, every range
ROUT = {"LOW": 1500.0, "MID": 1500.0, "HIGH": 2400.0}
CN = {"LOW": 330e-12, "MID": 330e-12, "HIGH": 220e-12}
RDS = 0.060                   # AO3401A R_DS(on) max at -4.5 V
RSW = 2 * RDS                 # back-to-back port switch
RWIRE = 0.040                 # traces and the receptacles' contacts, estimate (headers gone, D37)
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
# V12F at its lowest: MAU104 -3 % max, J1 at -5 % x 1.2 line regulation, less the 10 ohm filter
# at the maximum load. Since D34 that load is 6 x OP07 (5 mA max), 3 x LM393 (2.5 mA, the 30 V
# row as a bound) and U4's feed resistor, which itself depends on V12F (solved below).
I_OP07_MAX, I_LM393_MAX = 6 * 5e-3, 3 * 2.5e-3
R_FEED_U4 = 1.5e3                        # V12F -> V_INJ, U4's cathode resistor
VREF431 = (2.475, 2.525)                 # CJ431 V_ref
IREF431_MAX = 4e-6 + 1.2e-6              # CJ431 I_ref max at 25 C plus its deviation over temperature
VINJ_MIN = VREF431[0] * (1 + 33e3 * 0.99 / (15e3 * 1.01))
VINJ_MAX = VREF431[1] * (1 + 33e3 * 1.01 / (15e3 * 0.99)) + IREF431_MAX * 33e3 * 1.01
V12_RAW_MIN = 12.0 * (1 - 0.03 - 0.05 * 1.2)
V12_MIN = V12_RAW_MIN
for _ in range(50):                      # fixed point: the U4 feed current depends on V12F
    V12_MIN = V12_RAW_MIN - 10.0 * (I_OP07_MAX + I_LM393_MAX + (V12_MIN - VINJ_MIN) / (R_FEED_U4 * 0.99))
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
def mau_in(ma_12v):
    """J1 current in mA for a V12 load in mA: 12 V out of 5 V in at the MAU104's 78 %."""
    return ma_12v * 12.0 / 0.78 / 5.0


# Since D34 the three LM393s run from V12F, so their 0.4 mA typical (LM393/D, 5 V row) each is
# a MAU104 load; their bound is the 30 V row's 2.5 mA max.
loads = {"CH335F": 85, "RP2040 + W25Q128JV flash with USB, estimate": 30,
         "MAU104 input (6 x OP07, 3 x LM393 typ)": 70 + mau_in(3 * 0.4),
         "LEDs": 5, "AMS1117 Iq": 5, "CJ431 x2 + dividers": 2,
         "MCP3208 x2 (0.4 mA max each)": 1, "SPI level shifters, 3 x 5 V / 1.5 kohm": 10}
print(f"total {sum(loads.values()):.0f} mA (MAU104 input {loads['MAU104 input (6 x OP07, 3 x LM393 typ)']:.1f} mA)")
hub = loads["CH335F"]
func = sum(loads.values()) - hub
mau_extra = mau_in(6 * 2.5 + 3 * (2.5 - 0.4))   # every OP07 at 5 mA max, every LM393 at 2.5 mA max
print(f"hub {hub} mA (declares 100 mA); MCU function {func:.0f} mA typ, {func + mau_extra:.0f} mA with"
      f" every OP07 and LM393 at max (J1 then {hub + func + mau_extra:.0f} mA) -> function declares 200 mA (D26),"
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

# ---- D34: capture values (issue #6 P2) ---------------------------------------
# Datasheets read for D34 (via LCSC, 2026-11-04): onsemi LM393/D Rev. 25 (C7955); JSCJ CJ431
# (C3113); AOS AO3400A Rev 3 (C20917); JSCJ 2N7002 (C8545); S9012 (C8543); KT-0805G (C2297);
# NCD0805R1 (C84256). The facts used are recorded in requirements/parts.md.
print("\n== Sec. 3.2 LM393 supply (D34): V5L or V12F")
VICR_25, VICR_T = 1.5, 2.0              # common mode tops out at V_CC - 1.5 V (25 C), - 2.0 V (0-70 C)
V_NODE_OVR = 5.25 * ROUT["HIGH"] / (ROUT["HIGH"] + R1 + RDS)   # overranged HIGH node at J4 5.25 V
for name, vcc in (("V5L min", V5L_MIN), ("V12F min", V12_MIN)):
    print(f"on {name} {vcc:.2f} V: common mode to {vcc-VICR_25:.2f} V (25 C) / {vcc-VICR_T:.2f} V (0-70 C)"
          f" vs the {VTH:.2f} V threshold; input absolute maximum = V_CC (LM393/D note 1) vs an"
          f" overranged node at {V_NODE_OVR:.2f} V -> margin {vcc-V_NODE_OVR:+.2f} V")
print(f"V12F min with the LM393s and U4's feed on it: {V12_MIN:.2f} V (OP07 {I_OP07_MAX*1e3:.0f} mA +"
      f" LM393 {I_LM393_MAX*1e3:.1f} mA + U4 feed {(V12_MIN-VINJ_MIN)/(R_FEED_U4*0.99)*1e3:.2f} mA through 10 ohm)")
V12_MAX = 12.0 * (1 + 0.03 + 0.05 * 1.2)
i_mau = I_OP07_MAX + I_LM393_MAX + (V12_MAX - VINJ_MIN) / (R_FEED_U4 * 0.99)
print(f"MAU104 load at most {i_mau*1e3:.1f} mA (V12 {V12_MAX:.2f} V max, no filter drop) vs its 84 mA rating")

print("\n== Sec. 4.1 / Sec. 6.1 CJ431 cathode currents (I_K(min) 1 mA max) and V_INJ")
ik_u4 = ((V12_MIN - VINJ_MAX) / (R_FEED_U4 * 1.01) - VINJ_MAX / (48e3 * 0.99)
         - 6 * (VINJ_MAX - 4.4) / (1e6 * 0.99))
ik_u4_max = (V12_MAX - VINJ_MIN) / (R_FEED_U4 * 0.99)
print(f"V_INJ {VINJ_MIN:.3f}..{VINJ_MAX:.3f} V (V_ref, 33 k / 15 k at 1 %, I_ref <= {IREF431_MAX*1e6:.1f} uA);"
      f" U4 I_K >= {ik_u4*1e3:.2f} mA at V12F min, <= {ik_u4_max*1e3:.2f} mA ({ik_u4_max*VINJ_MAX*1e3:.0f} mW)")
inj_min = (VINJ_MIN - 5.25) / (RINJ * 1.01)
print(f"pedestal injection at V_INJ min and a 5.25 V port: {inj_min*1e6:.2f} uA = {inj_min/(VOS/R1):.2f} x"
      f" the {VOS/R1*1e6:.2f} uA needed")
ik_u3 = ((V3V3_MIN - VREF431[1]) / (510 * 1.01), (V3V3_MAX - VREF431[0]) / (510 * 0.99))
print(f"U3 I_K {ik_u3[0]*1e3:.2f}..{ik_u3[1]*1e3:.2f} mA from V3V3 through 510 ohm (no capacitor at either CJ431)")

print("\n== Sec. 3.2 / Sec. 3.4 comparator threshold TH_REF (D34): VDDA - 1 k - TH_REF - 5.1 k + 510 ohm - GND")
RA, RB = 1e3, 5.1e3 + 510.0
ratio = (RB / (RA + RB), RB * 0.99 / (RA * 1.01 + RB * 0.99), RB * 1.01 / (RA * 0.99 + RB * 1.01))
RTH = RA * RB / (RA + RB)
R_IN = 15e3                               # per comparator, TH_REF -> + input
IIB = (250e-9, 400e-9)                    # LM393 I_IB max, 25 C / 0-70 C; flows out of the pins (note 7)
VIO = (5e-3, 9e-3)                        # LM393 V_IO max, 25 C / 0-70 C
print(f"TH_REF nominal {VDDA*ratio[0]:.4f} V; ratio {ratio[1]:.5f}..{ratio[2]:.5f} (+-{100*(ratio[2]/ratio[0]-1):.2f} %);"
      f" Thevenin {RTH:.0f} ohm with 1 uF -> {RTH*1e-6*1e3:.2f} ms")
print(f"bias at 25 C: 6 inputs x {IIB[0]*1e9:.0f} nA into {RTH:.0f} ohm = {6*IIB[0]*RTH*1e3:.2f} mV,"
      f" plus {IIB[0]*R_IN*1e3:.2f} mV across each 15 k; at the - input {IIB[0]*ROUT['HIGH']*1e3:.2f} mV"
      f" across R_OUT HIGH (constant, removed by zero calibration)")
print(f"power-up: until V12F is up, + input current <= {VDDA*ratio[2]*1.015/R_IN*1e3:.2f} mA through 15 k"
      " (LM393/D note 1 limits the input to V_CC; not settled on paper, checked at bring-up)")


def oc_trip(t_hot):
    """OC trip current bounds in A: initial tolerances, plus drift over t_hot degrees from 25 C."""
    vio = VIO[1] if t_hot else VIO[0]
    iib = IIB[1] if t_hot else IIB[0]
    drift_k = (2 * 100e-6 + 100e-6) * t_hot          # R_OUT/R1 ratio and R_H, +-100 ppm/C each
    k_lo = RS["HIGH"] * 0.995 * ROUT["HIGH"] * 0.99 / (R1 * 1.01) * (1 - drift_k)
    k_hi = RS["HIGH"] * 1.005 * ROUT["HIGH"] * 1.01 / (R1 * 0.99) * (1 + drift_k)
    vth_lo = V3V3_MIN * ratio[1]
    vth_hi = V3V3_MAX * ratio[2] + 6 * iib * RTH + iib * R_IN
    ped_lo = (VINJ_MIN - 5.25) / (RINJ * 1.01) * ROUT["HIGH"] * 0.99
    ped_hi = (VINJ_MAX - 4.4) / (RINJ * 0.99) * ROUT["HIGH"] * 1.01
    vos_out = VOS * ROUT["HIGH"] / R1
    lo = (vth_lo - vio - ped_hi - iib * ROUT["HIGH"] - vos_out) / k_hi
    hi = (vth_hi + vio - ped_lo + vos_out) / k_lo
    return lo, hi


it_nom = (VDDA * ratio[0] - PED["HIGH"]) / K["HIGH"]
lo25, hi25 = oc_trip(0)
lo70, hi70 = oc_trip(45)
lo40, hi40 = oc_trip(15)
print(f"OC trip nominal {it_nom:.3f} A; at 25 C {lo25:.3f}..{hi25:.3f} A ({100*(lo25/it_nom-1):+.1f} / {100*(hi25/it_nom-1):+.1f} %);"
      f" over 0-70 C {oc_trip(25)[0]:.3f}..{hi70:.3f} A")
print(f"F1 at 40 C: both trips at their highest {2*hi40:.2f} A vs I_hold {IHOLD_F1[40]:.2f} A -> margin"
      f" {IHOLD_F1[40]-2*hi40:+.2f} A; dissipation {(2*hi40)**2*RF1:.2f} W at R1max")

print("\n== Sec. 3.2 / Sec. 3.4 comparator hysteresis (D34): 15 pF output -> + input, 220 pF + input -> GND")
C_FB, C_IN = 15e-12, 220e-12
for name, swing in (("bypass gate (4.4..5.25 V port, V_OL 0.4 V)", (4.4 - 0.4, 5.25)),
                    ("EN_G (OC)", (3.1 * 100 / 110 * 0.98 - 0.4, 3.349 * 100 / 110 * 1.02))):
    print(f"{name}: kick {swing[0]*C_FB/(C_FB+C_IN)*1e3:.0f}..{swing[1]*C_FB/(C_FB+C_IN)*1e3:.0f} mV,"
          f" decaying with tau {R_IN*(C_FB+C_IN)*1e6:.2f} us; lowest + input"
          f" {V3V3_MIN*ratio[1]-swing[1]*C_FB/(C_FB+C_IN):.2f} V (>= -0.3 V)")
print(f"extra load on the output node: {C_FB*C_IN/(C_FB+C_IN)*1e12:.1f} pF (bypass gate C_iss 645 pF)")

print("\n== Sec. 3.4 soft start (D34): R_on 100 k, C_M 2 x 10 nF gate-to-VSUP, R_GS 1 Mohm")
R_ON, R_GS, C_M = 100e3, 1e6, 2 * 10e-9
for vs in (4.4, 4.75, 5.0, 5.25):
    vgs = -vs * R_GS / (R_ON + R_GS)
    rds = 0.060 + max(0.0, (4.5 + vgs) / 2.0) * (0.085 - 0.060)   # linear between the -4.5 / -2.5 V rows
    print(f"V_S {vs:.2f} V: final V_GS {vgs:.2f} V -> R_DS(on) <= {rds*1e3:.1f} mOhm"
          f" (linear between the AO3401A -4.5 V and -2.5 V rows, an over-estimate)")
VPL = (0.5, 2.5)                          # |V_GS| on the Miller plateau: V_th min ... a generous bound
t_ss = []
for vs in (4.4, 5.25):
    for vpl in VPL:
        for cm, ron in ((C_M * 0.9, R_ON * 0.99), (C_M * 1.1, R_ON * 1.01)):
            i_net = (vs - vpl) / ron - vpl / R_GS
            t_ss.append(cm * vs / i_net)
print(f"turn-on ramp {min(t_ss)*1e3:.2f}..{max(t_ss)*1e3:.2f} ms (V_S 4.4..5.25 V, plateau |V_GS| 0.5..2.5 V,"
      f" C_M +-10 %, R_on +-1 %) vs >= 1 ms (REQ-PORT-08); inrush into 10 uF <= {CPORT*5.25/min(t_ss)*1e3:.0f} mA")

print("\n== Sec. 3.4 fast turn-off (D34): DIS rise, Q16 base drive, charge to move")
CISS_Q13, CISS_Q15 = 630e-12, 50e-12      # AO3400A typ; 2N7002 max
R_DIS, R_DISG = 10e3, 100e3
tau_old = R_DIS * (CISS_Q13 + CISS_Q15)
print(f"Q13 gate on DIS directly (Rev0.4 as drawn): tau {tau_old*1e6:.1f} us -> 2.5 V (2N7002 V_th max) after"
      f" {tau_old*math.log(V3V3_MIN/(V3V3_MIN-2.5))*1e6:.1f} us")
v_inf = V3V3_MIN * R_DISG / (R_DIS + R_DISG)
tau_new = (R_DIS * R_DISG / (R_DIS + R_DISG)) * CISS_Q15
print(f"Q13 gate through 100 k: DIS steps to {v_inf:.2f} V with tau {tau_new*1e9:.0f} ns -> 2.5 V after"
      f" {tau_new*math.log(v_inf/(v_inf-2.5))*1e6:.2f} us; Q13 itself follows with tau"
      f" {(R_DIS+R_DISG)*CISS_Q13*1e6:.0f} us (discharge is not time-critical)")
R_B, R_BE, VBE = 5.1e3, 100e3, 0.75
HFE = (200, 350)                          # S9012 C8543 is rank H (LCSC model "S9012 2T1(RANGE:200-350)"): 200-350 at -50 mA
for vs in (4.4, 5.25):
    ib = (vs - VBE) / (R_B * 1.01) - VBE / R_BE
    print(f"V_S {vs:.2f} V: I_B {ib*1e3:.2f} mA -> I_C {HFE[0]*ib*1e3:.0f}..{HFE[1]*ib*1e3:.0f} mA"
          " (S9012 I_C max 500 mA)")
q_off = C_M * 1.1 * (5.25 + 5.25 * R_GS / (R_ON + R_GS) - 0.0) + 2 * 7e-9
ib_min = (4.4 - VBE) / (R_B * 1.01) - VBE / R_BE
print(f"charge to move: C_M from -{5.25*R_GS/(R_ON+R_GS):.2f} V to +5.25 V (VSUP collapsing into a short)"
      f" + 2 x Q_g 7 nC = {q_off*1e9:.0f} nC -> {q_off/(HFE[0]*ib_min)*1e6:.1f} us at the lowest I_C")
dvdt = 5.25 / (SPAN["HIGH"] * CPORT)
print(f"C_M current while VSUP falls into a short ({dvdt/1e6:.1f} V/us from tau {SPAN['HIGH']*CPORT*1e6:.1f} us):"
      f" {C_M*1.1*dvdt*1e3:.0f} mA vs Q16 >= {HFE[0]*ib_min*1e3:.0f} mA")
t_off = 1.3e-6 + tau_new * math.log(v_inf / (v_inf - 2.5)) + q_off / (HFE[0] * ib_min)
print(f"OC to open: LM393 1.3 us + DIS {tau_new*math.log(v_inf/(v_inf-2.5))*1e6:.2f} us + gate {q_off/(HFE[0]*ib_min)*1e6:.1f} us"
      f" = {t_off*1e6:.1f} us vs 10 us (REQ-PORT-05)")

print("\n== Sec. 3.4 EN_G and the 2N7002s it drives (Q12, Q14)")
for voh in (3.1, V3V3_MAX):
    print(f"EN {voh:.2f} V -> EN_G {voh*100e3*0.99/(10e3*1.01+100e3*0.99):.2f}..{voh*100e3*1.01/(10e3*0.99+100e3*1.01):.2f} V"
          f" vs 2N7002 V_th max 2.5 V at 250 uA; Q14 sinks DIS's {V3V3_MAX/R_DIS*1e3:.2f} mA")
print(f"LM393 sinking EN_G: {V3V3_MAX/(10e3*0.99)*1e3:.2f} mA through the 10 k vs its 6 mA minimum")

print("\n== Sec. 6.4 LEDs (D34): 510 ohm from a GPIO")
for name, vf in (("green KT-0805G, V_F 2.6..3.1 V +-0.05 at 5 mA", (2.55, 3.15)),
                 ("red NCD0805R1, V_F 1.5..2.6 V at 20 mA", (1.5, 2.6))):
    lo = max(0.0, (3.1 - vf[1]) / (510 * 1.01))
    hi = (V3V3_MAX - vf[0]) / (510 * 0.99)
    print(f"{name}: {lo*1e3:.2f}..{hi*1e3:.2f} mA (pin 3.1..{V3V3_MAX} V; V_F at the stated current is a bound)")

print("\n== Sec. 3.2 leakage onto a bypass gate held OFF by 1 Mohm (LOW and MID accuracy)")
IOL_MAX, IDSS_2N7002 = 1e-6, 80e-9       # LM393 I_OL max at V_O 30 V, 0-70 C; 2N7002 I_DSS at 60 V
print(f"datasheet bounds at their own (harsher) conditions: LM393 I_OL {IOL_MAX*1e9:.0f} nA + 2N7002 I_DSS"
      f" {IDSS_2N7002*1e9:.0f} nA -> V_GS {-(IOL_MAX+IDSS_2N7002)*1e6:.2f} V vs AO3401A V_th -0.5 V min;"
      f" typical I_OL 0.1 nA -> {-(0.1e-9+IDSS_2N7002)*1e6*1e3:.0f} mV (checked by V-MEAS-01)")

print("\n== Sec. 3.1 / Sec. 7.1 J1 soft start (D35, OI-32): Q53 AO3401A between VBUS_J1 and V5L")
# Q53: source VBUS_J1 (J1 pin 1, D5), drain V5L. R34 33 k gate -> GND turns it on; C35 100 nF
# gate -> drain (V5L) is the Miller capacitor that sets V5L's ramp; C36 + C37, 2 x 1 uF gate ->
# source, hold the gate at the source when VBUS_J1 steps up at plug-in. No gate-source resistor:
# the gate ends at GND, V_GS = -V_J1.
R_G, C_MJ, C_GSJ = 33e3, 100e-9, 2 * 1e-6
TOL_R, TOL_C = 0.01, 0.10                   # +-1 % resistors; +-10 % X7R / X5R capacitors
CISS_J, CRSS_J = 645e-12, 55e-12            # AO3401A (parts.md)
VTH_J = (0.5, 1.3)                          # |V_GS(th)| min / max at 250 uA
VPL_J = (0.5, 2.0)                          # |Miller plateau|: V_th min, and Figure 7's 2 V at 4 A as a bound
VJ1 = (4.4, 5.25)                           # J1 VBUS at the board: USB 2.0's 4.40 V device minimum, host maximum
VJ1_CORNER = 5.5                            # USB-C corner, for the plug-in step only
# Capacitance whose voltage follows V5L during the ramp (nominal, from the capture list): V5L
# itself, V5A behind 10 ohm, V3V3 and VDDA (and TH_REF behind 1 k) behind the AMS1117, which
# tracks its input in dropout, U6's VDD33 and U1's DVDD behind their on-chip regulators. The
# MAU104's 45 uF on V12/V12F is charged by the MAU104 itself and is not in this sum.
C_FOLLOW = {"V5L: C2 10u, C5 1u, C27 1u": 12e-6,
            "V5A: C10 10u, C30 + C32 100n": 10.2e-6,
            "V3V3: C3 22u, C4 10u, C20 1u, C12-C19 + C24 9 x 100n": 33.9e-6,
            "VDDA: C9 10u, C31 + C33 100n; TH_REF C11 1u": 11.2e-6,
            "VDD33_HUB: C29 10u, C28 100n": 10.1e-6,
            "DVDD: C21 1u, C22 + C23 100n": 1.2e-6}
RAIL_V = (5.0, 5.0, 3.3, 3.3, 3.3, 1.1)     # each group's final voltage, in C_FOLLOW's order
c_l = sum(C_FOLLOW.values())
c_l_hi = c_l * 1.2                          # +20 % bound on the sum (the 22 uF parts are +-20 %)
q_plug = sum(c * v for c, v in zip(C_FOLLOW.values(), RAIL_V))
print(f"capacitance following V5L: {c_l*1e6:.1f} uF nominal, {c_l_hi*1e6:.1f} uF bound;"
      f" without a soft start J1 delivers {q_plug*1e6:.0f} uC at plug-in, {q_plug/50e-6:.1f} x"
      f" a 10 uF load's 50 uC at 5 V")
# 1. Plug-in: VBUS_J1 steps in microseconds. The gate divides between C_GS (to the source) and
#    C_M + C_rss (to the drain, held at 0 V by c_l), so V_GS jumps by the C_M share.
step = VJ1_CORNER * (C_MJ * (1 + TOL_C) + CRSS_J) / (C_GSJ * (1 - TOL_C) + C_MJ * (1 + TOL_C) + CISS_J)
print(f"plug-in step: V_GS {-step:.3f} V at {VJ1_CORNER} V (C_GS -10 %, C_M +10 %) vs V_th {-VTH_J[0]} V min:"
      f" {VTH_J[0]/step:.2f} x margin")
# 2. Hold-off: the gate falls from V_S * a through R_G, tau = R_G (C_GS + C_M); Q53 starts to
#    conduct when V_S - V_G reaches |V_th|.
def hold(r, cgs, cm, vs, vth):
    tau = r * (cgs + cm + CISS_J)
    a = (cgs + CISS_J) / (cgs + cm + CISS_J)
    return tau * math.log(a * vs / (vs - vth))
t_hold_lo = hold(R_G * (1 - TOL_R), C_GSJ * (1 - TOL_C), C_MJ * (1 + TOL_C), VJ1[1], VTH_J[0])
t_hold_hi = hold(R_G * (1 + TOL_R), C_GSJ * (1 + TOL_C), C_MJ * (1 - TOL_C), VJ1[0], VTH_J[1])
print(f"hold-off after plug-in: {t_hold_lo*1e3:.1f}..{t_hold_hi*1e3:.1f} ms")
# 3. Ramp: on the Miller plateau the gate is at V_S - |V_pl|, and R_G's current charges C_M as
#    V5L rises: dV/dt = (V_S - |V_pl|) / (R_G C_M).
dvdt_hi = (VJ1[1] - VPL_J[0]) / (R_G * (1 - TOL_R) * C_MJ * (1 - TOL_C))
dvdt_lo = (VJ1[0] - VPL_J[1]) / (R_G * (1 + TOL_R) * C_MJ * (1 + TOL_C))
t_ramp_lo, t_ramp_hi = VJ1[1] / dvdt_hi, VJ1[0] / dvdt_lo
i_c_nom = c_l * (5.0 - 1.0) / (R_G * C_MJ)
i_c_hi = c_l_hi * dvdt_hi
print(f"ramp: {dvdt_lo/1e3:.3f}..{dvdt_hi/1e3:.3f} V/ms, {t_ramp_lo*1e3:.1f}..{t_ramp_hi*1e3:.1f} ms;"
      f" capacitive inrush {i_c_nom*1e3:.0f} mA nominal (5 V, |V_pl| 1 V), <= {i_c_hi*1e3:.0f} mA bound,"
      f" against {5.0/44*1e3:.0f} mA for USB's 44 ohm (the 10 uF || 44 ohm load)")
t_up = t_hold_hi + t_ramp_hi
print(f"plug-in to V5L up: <= {t_up*1e3:.1f} ms; the hub must signal attach within 100 ms of VBUS valid,"
      f" leaving >= {100 - t_up*1e3:.0f} ms for U6's own start (not on its sheet; V-PWR-03)")
# 4. Q53 during the ramp: V_DS falls linearly from V_S to 0 while it carries the capacitive
#    current plus the loads that start on the way (bounded by J1's maximum).
I_J1_MAX = (85 + func + mau_extra) / 1e3     # Sec. 7.1 above: every OP07 and LM393 at its maximum
p_pk = VJ1[1] * (i_c_hi + I_J1_MAX)
e_ramp = 0.5 * VJ1[1] * (i_c_hi + I_J1_MAX) * t_ramp_hi
print(f"Q53 in the ramp: <= {p_pk:.2f} W peak, <= {e_ramp*1e3:.1f} mJ over <= {t_ramp_hi*1e3:.1f} ms"
      f" vs about 25 W for 10 ms single pulse (AO3401A Figure 10, read from the graph)")
# 5. Fully on: V_GS = -V_J1. R_DS(on) between the -4.5 V (60 mohm) and -2.5 V (85 mohm) maxima,
#    linear, times Figure 4's 1.23 at 70 C.
def rds_j(vgs):
    return 0.060 + max(0.0, 4.5 - vgs) / 2.0 * 0.025
for vs in (VJ1[0], 4.75):
    r25 = rds_j(vs)
    print(f"V_J1 {vs:.2f} V: R_DS(on) <= {r25*1e3:.1f} mohm at 25 C, {r25*1.23*1e3:.1f} at 70 C;"
          f" at J1 {I_J1_MAX*1e3:.0f} mA the drop is <= {I_J1_MAX*r25*1e3:.0f} / {I_J1_MAX*r25*1.23*1e3:.0f} mV,"
          f" {I_J1_MAX**2*r25*1.23*1e3:.1f} mW")
drop_hi = I_J1_MAX * rds_j(VJ1[0]) * 1.23
print(f"V5L >= {V5L_MIN} V (U6 V5 and MAU104 minimum) now needs J1 >= {V5L_MIN + drop_hi:.3f} V at the receptacle")
