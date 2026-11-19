"""The C2 placement (issue #12) as a change to design/ecad/PLACEMENT_Rev0.5.md.

One home for the trial's positions. `apply()` rewrites a COPY of the placement document; every old
line must be in it exactly once, so a placement document that has moved on stops the trial instead
of giving it a different board.

C2, "four corners": the four USB-C receptacles and the two buttons mirror about the board's centre
line x = 50.

    front edge:  OUT A (J2) x 17.5   SW1 x 31.5   |   SW2 x 68.5   OUT B (J3) x 82.5
    back edge:   5V IN (J4) x 17.5                |                HOST  (J1) x 82.5

Channel A, both front ends, the ADCs, the hub, the MCU and the 5 V input stay where they are.
"""

# (old line, new line)
REPLACE = [
    ("# USB Power-Control Hub — Rev0.5 placement",
     "# USB Power-Control Hub — Rev0.5 placement, trial C2\n\n"
     "> **TRIAL C2 (issue #12): not the board's placement.** `design/experiments/usb-symmetry-c2/` applies\n"
     "> this change to a scratch copy to see whether a mirror-symmetric connector placement passes\n"
     "> `check_pcb.py`. The board is not routed from it, and the silkscreen table below is not updated."),

    # Regions. OUT B takes the front right, where the MAU104 stood; the MAU104 takes the front middle.
    ("| PORT_A | block | 7.0 | 0.0 | 21.0 | 15.5 | J2 and its port parts | OUT A at the front edge; J2–J3 pitch 33.8 mm ≥ 18 mm (REQ-MECH-02) |",
     "| PORT_A | block | 7.0 | 0.0 | 21.0 | 15.5 | J2 and its port parts | OUT A at the front left; J2–J3 pitch 65.0 mm ≥ 18 mm (REQ-MECH-02) |"),
    ("| PORT_B | block | 40.8 | 0.0 | 21.0 | 15.5 | J3 and its port parts | PORT_A + 33.8 mm |",
     "| PORT_B | block | 72.0 | 0.0 | 21.0 | 15.5 | J3 and its port parts | OUT B at the front right: PORT_A + 65.0 mm, so J3 (x 82.5) mirrors J2 (x 17.5) about the centre line x 50 |"),
    ("| PORT_HOST | block | 66.0 | 58.5 | 23.0 | 13.5 | J1 and its port parts | HOST at the back edge, next to the hub strip |",
     "| PORT_HOST | block | 70.0 | 58.5 | 23.0 | 13.5 | J1 and its port parts | HOST at the back right: J1 (x 82.5) mirrors J4 (x 17.5); next to the hub strip |"),
    ("| V12 | block | 72.4 | 7.7 | 20.1 | 7.3 | C5–C8, R10, TP3 | the MAU104's capacitors and the V12F filter |",
     "| V12 | block | 45.4 | 7.7 | 19.6 | 7.3 | C5–C8, R10, TP3 | the MAU104's capacitors and the V12F filter, moved with U5 |"),
    ("| MAU | block | 72.4 | 0.5 | 20.1 | 6.7 | U5 | the MAU104 at the front right, ≥ 6 mm from the analog parts |",
     "| MAU | block | 45.4 | 0.5 | 20.2 | 6.7 | U5 | the MAU104 in the front middle, between REF and OUT B's button, ≥ 6 mm from the analog parts |"),
    # UI_B becomes two rectangles: the MAU104's courtyard ends at x 65.495, 0.42 mm right of where
    # the LED resistors' courtyards begin (x 65.075), but below them (y 7.2 against y 9.555).
    ("| UI_B | block | 61.8 | 0.5 | 7.0 | 14.5 | SW2, D12, D13, R240, R241 | UI_A + 33.8 mm |",
     "| UI_B | block | 65.0 | 9.0 | 7.0 | 6.0 | D12, D13, R240, R241 | OUT B's LEDs, the mirror of OUT A's about x 50 |\n"
     "| UI_B_SW | block | 65.65 | 0.5 | 6.35 | 8.0 | SW2 | OUT B's button, the mirror of SW1; a rectangle of its own, because the MAU104's courtyard reaches x 65.495 below y 7.2 |"),

    # Keepouts: the lanes follow their receptacles.
    ("| USB_UP_LANE | 75.6 | 56.5 | 23.9 | 2 | the HS pair from J1 down the right edge to U6 |",
     "| USB_UP_LANE | 82.1 | 56.5 | 17.4 | 2 | the HS pair from J1 down the right edge to U6 |"),
    ("| USB_LANE_B | 49.9 | 8.5 | 1.8 | 7 | the HS pair from the corridor down to J3's pads |",
     "| USB_LANE_B | 81.1 | 8.5 | 1.8 | 7 | the HS pair from the corridor down to J3's pads |"),
    ("| USB_UP_RISER | 75.6 | 58.5 | 1.8 | 6.1 | the HS pair from the lane keepout above up to J1's pads |",
     "| USB_UP_RISER | 82.1 | 58.5 | 1.8 | 6.1 | the HS pair from the lane keepout above up to J1's pads |"),

    # The MAU104 and its capacitors: every part 26.95 mm to the left. The window for U5 is 0.39 mm
    # wide: x 47.67 keeps 6.0 mm from R11 (REF), x 48.06 touches SW2's courtyard.
    ("| C5 | 74.85 | 8.7 | 90 | V12 | at U5 pin 1 |", "| C5 | 47.9 | 8.7 | 90 | V12 | at U5 pin 1 |"),
    ("| C6 | 87.55 | 8.7 | 90 | V12 | at U5 pin 6 |", "| C6 | 60.6 | 8.7 | 90 | V12 | at U5 pin 6 |"),
    ("| C7 | 86.45 | 11.6 | 90 | V12 | at R10 pin 2 |", "| C7 | 59.5 | 11.6 | 90 | V12 | at R10 pin 2 |"),
    ("| C8 | 83.55 | 9.6 | 180 | V12 | at R10 pin 2 |", "| C8 | 56.6 | 9.6 | 180 | V12 | at R10 pin 2 |"),
    ("| R10 | 86.4 | 8.7 | 90 | V12 | at U5 pin 6 |", "| R10 | 59.45 | 8.7 | 90 | V12 | at U5 pin 6 |"),
    ("| TP3 | 88.65 | 10.9 | 0 | V12 | at R10 pin 2 |", "| TP3 | 61.7 | 10.9 | 0 | V12 | at R10 pin 2 |"),
    ("| U5 | 74.8 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |",
     "| U5 | 47.85 | 5.6 | 0 | MAU | pins north, toward its capacitors in V12 |"),

    # HOST: J1, its port parts and its soft start 6.5 mm to the right. D5 only 5.15 mm, so that it
    # stays left of the corner block of the hole H4, and 0.65 mm down, so that its legend clears
    # J1's pin-1 mark (at y 62.45 DRC reports the two as overlapping).
    ("| J1 | 76 | 69.385 | 180 | PORT_HOST | HOST receptacle; front face 1.06 mm past the back edge |",
     "| J1 | 82.5 | 69.385 | 180 | PORT_HOST | HOST receptacle; front face 1.06 mm past the back edge |"),
    ("| D1 | 72.4 | 61.6 | 180 | PORT_HOST | J1 CC ESD, at J1 |", "| D1 | 78.9 | 61.6 | 180 | PORT_HOST | J1 CC ESD, at J1 |"),
    ("| D5 | 84.2 | 62.45 | 0 | PORT_HOST | J1 VBUS TVS, at J1 |", "| D5 | 89.35 | 61.8 | 0 | PORT_HOST | J1 VBUS TVS, at J1 |"),
    ("| R1 | 69.3 | 60.4 | 0 | PORT_HOST | J1 Rd CC1 |", "| R1 | 75.8 | 60.4 | 0 | PORT_HOST | J1 Rd CC1 |"),
    ("| R2 | 69.3 | 62.8 | 0 | PORT_HOST | J1 Rd CC2 |", "| R2 | 75.8 | 62.8 | 0 | PORT_HOST | J1 Rd CC2 |"),
    ("| C35 | 78.4 | 51.9 | 180 | J1F | GJ1, next to C37 |", "| C35 | 84.9 | 51.9 | 180 | J1F | GJ1, next to C37 |"),
    ("| C36 | 77.9 | 53.7 | 90 | J1F | GJ1, next to R34 |", "| C36 | 84.4 | 53.7 | 90 | J1F | GJ1, next to R34 |"),
    ("| C37 | 79.05 | 53.55 | 90 | J1F | GJ1, next to C36 |", "| C37 | 85.55 | 53.55 | 90 | J1F | GJ1, next to C36 |"),
    ("| Q53 | 75.55 | 53 | 270 | J1F | GJ1, next to C36 |", "| Q53 | 82.05 | 53 | 270 | J1F | GJ1, next to C36 |"),
    ("| R34 | 78.45 | 55.3 | 0 | J1F | GJ1, next to C36 |", "| R34 | 84.95 | 55.3 | 0 | J1F | GJ1, next to C36 |"),
    ("| TP14 | 80.75 | 53.15 | 0 | J1F | VBUS_J1, next to C37 |", "| TP14 | 87.25 | 53.15 | 0 | J1F | VBUS_J1, next to C37 |"),
]

# Channel B's port and button are no longer "channel A + 33.8 mm" (check_pcb.py holds every pair
# of the channel table to that), so these thirteen pairs leave the channel table ...
REMOVE = [
    "| C116 | C216 | 21.3 | 9.2 | 0 | PORT_{x} | port capacitor, at J2 pad B4 |",
    "| D2 | D3 | 14.1 | 11.3 | 180 | PORT_{x} | CC ESD, next to J2, west of the lane |",
    "| D10 | D12 | 29.75 | 10.5 | 0 | UI_{x} | OUT A ON LED |",
    "| D11 | D13 | 29.75 | 13 | 0 | UI_{x} | OUT A FAULT LED |",
    "| J2 | J3 | 17.5 | 2.615 | 0 | PORT_{x} | OUT A receptacle; front face 1.06 mm past the front edge |",
    "| Q13 | Q33 | 25 | 11.9 | 0 | PORT_{x} | discharge FET |",
    "| R103 | R203 | 12.4 | 8.9 | 0 | PORT_{x} | Rp CC1 |",
    "| R104 | R204 | 12.4 | 14.2 | 0 | PORT_{x} | Rp CC2 |",
    "| R109 | R209 | 22 | 13.2 | 0 | PORT_{x} | Q13 gate resistor |",
    "| R110 | R210 | 24.4 | 8.9 | 0 | PORT_{x} | discharge resistor, next to C116 |",
    "| R140 | R240 | 33.25 | 10.5 | 180 | UI_{x} | D10 series |",
    "| R141 | R241 | 33.25 | 13 | 180 | UI_{x} | D11 series |",
    "| SW1 | SW2 | 31.5 | 4.5 | 90 | UI_{x} | OUT A button |",
]

# ... and stand in the common table, before its end: channel A where it was, channel B's port at
# A + 65.0 mm, its button and LEDs at 100 - x. Each LED and its resistor are turned half a turn,
# so that their pins 2 (the LED's anode net) still face each other.
ADD = [
    "| C116 | 21.3 | 9.2 | 0 | PORT_A | port capacitor, at J2 pad B4 |",
    "| D2 | 14.1 | 11.3 | 180 | PORT_A | CC ESD, next to J2, west of the lane |",
    "| D10 | 29.75 | 10.5 | 0 | UI_A | OUT A ON LED |",
    "| D11 | 29.75 | 13 | 0 | UI_A | OUT A FAULT LED |",
    "| J2 | 17.5 | 2.615 | 0 | PORT_A | OUT A receptacle; front face 1.06 mm past the front edge |",
    "| Q13 | 25 | 11.9 | 0 | PORT_A | discharge FET |",
    "| R103 | 12.4 | 8.9 | 0 | PORT_A | Rp CC1 |",
    "| R104 | 12.4 | 14.2 | 0 | PORT_A | Rp CC2 |",
    "| R109 | 22 | 13.2 | 0 | PORT_A | Q13 gate resistor |",
    "| R110 | 24.4 | 8.9 | 0 | PORT_A | discharge resistor, next to C116 |",
    "| R140 | 33.25 | 10.5 | 180 | UI_A | D10 series |",
    "| R141 | 33.25 | 13 | 180 | UI_A | D11 series |",
    "| SW1 | 31.5 | 4.5 | 90 | UI_A | OUT A button |",
    "| C216 | 86.3 | 9.2 | 0 | PORT_B | port capacitor, at J3 pad B4 |",
    "| D3 | 79.1 | 11.3 | 180 | PORT_B | CC ESD, next to J3, west of the lane |",
    "| D12 | 70.25 | 10.5 | 180 | UI_B | OUT B ON LED |",
    "| D13 | 70.25 | 13 | 180 | UI_B | OUT B FAULT LED |",
    "| J3 | 82.5 | 2.615 | 0 | PORT_B | OUT B receptacle; front face 1.06 mm past the front edge |",
    "| Q33 | 90 | 11.9 | 0 | PORT_B | discharge FET |",
    "| R203 | 77.4 | 8.9 | 0 | PORT_B | Rp CC1 |",
    "| R204 | 77.4 | 14.2 | 0 | PORT_B | Rp CC2 |",
    "| R209 | 87 | 13.2 | 0 | PORT_B | Q33 gate resistor |",
    "| R210 | 89.4 | 8.9 | 0 | PORT_B | discharge resistor, next to C216 |",
    "| R240 | 66.75 | 10.5 | 0 | UI_B | D12 series |",
    "| R241 | 66.75 | 13 | 0 | UI_B | D13 series |",
    "| SW2 | 68.5 | 4.5 | 90 | UI_B_SW | OUT B button |",
]
ADD_BEFORE = "<!-- place:end -->"

# The regions whose parts the change may move. trial.py fails if a part of any other region moved.
MAY_MOVE = ("PORT_B", "UI_B", "UI_B_SW", "MAU", "V12", "PORT_HOST", "J1F")


def apply(path, extra=()):
    """Rewrite the placement document at `path`. `extra` holds further (old, new) lines, applied
    after the change: trial.py's negative runs use it."""
    text = path.read_bytes().decode("utf-8")
    if "\r" in text:
        raise SystemExit(f"{path.name}: carriage returns in the document")
    lines = text.split("\n")

    def only(line):
        n = lines.count(line)
        if n != 1:
            raise SystemExit(f"{path.name}: {n} lines, not 1: {line}")
        return lines.index(line)

    for old, new in REPLACE:
        lines[only(old)] = new
    for old in REMOVE:
        del lines[only(old)]
    end = only(ADD_BEFORE)
    lines[end:end] = ADD
    for old, new in extra:
        lines[only(old)] = new
    path.write_bytes("\n".join(lines).encode("utf-8"))
