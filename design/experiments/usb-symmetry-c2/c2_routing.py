"""Trial C2 (issue #12) as a change to design/ecad/ROUTING_Rev0.5.md.

One home for the trial's tracks. `apply()` rewrites a COPY of the routing document;
every old line must be in it exactly once, so a routing document that has moved on
stops the trial instead of giving it a different board.

C2 moves J3 to the front right and J1 to the back right: pair B's lane and its
lead-ins, hop and branch at J3 move 31.2 mm east, pair UP's lane and its lead-ins,
hop and branch at J1 move 6.5 mm east, and the VBUS_B trunk leaves channel_route
for the hand-drawn table, which also gains a copy of VBUS_A's J2 end at J3.
The patch table is emptied: its rows belong to the committed router session.

Who wrote what (the user, 2026-11-19: simple work goes to Devin on SWE-2 Max). The REPLACE and
MOVE lines, the six J3-end ADD lines and apply() were written by Devin from a brief that gave
every value or its arithmetic rule, and were checked line by line against values worked out
separately. The three trunk lines of ADD are the main session's: the design decision of the
trial. The trunk is on L4 and 3.0 mm wide because the board's port B path stands at 37.89 mOhm
of its 40 mOhm limit, and the trunk grows from 16.8 mm to 33.4 mm. A first drawing with a
1.2 mm trunk on L1 was estimated at about 46 mOhm and was dropped before any run.
"""

# (old line, new line)
REPLACE = [
    ("| UP | USB_UP_P | USB_UP_N | 97.3,28.0 97.8,28.5 97.8,57.0 97.3,57.5 77.0,57.5 76.5,58.0 76.5,63.0 | U6's east pins north along the east edge, then west along y = 57.5 to J1's lane |",
     "| UP | USB_UP_P | USB_UP_N | 97.3,28.0 97.8,28.5 97.8,57.0 97.3,57.5 83.5,57.5 83.0,58.0 83.0,63.0 | U6's east pins north along the east edge, then west along y = 57.5 to J1's lane |"),
    ("| B | USB_B_P | USB_B_N | 96.5,24.0 97.0,23.5 97.0,16.45 96.5,15.95 51.3,15.95 50.8,15.45 50.8,9.0 | U6 south past the taps (x = 97.0), then west along y = 15.95, below A, to J3's lane |",
     "| B | USB_B_P | USB_B_N | 96.5,24.0 97.0,23.5 97.0,16.45 96.5,15.95 82.5,15.95 82.0,15.45 82.0,9.0 | U6 south past the taps (x = 97.0), then west along y = 15.95, below A, to J3's lane |"),
    ('| USB_UP_N | F.Cu | 0.31 | 96.750,27.770 97.395,27.770 98.030,28.405 98.030,57.095 97.395,57.730 77.095,57.730 76.730,58.095 76.730,63.000 | coupled |',
     '| USB_UP_N | F.Cu | 0.31 | 96.750,27.770 97.395,27.770 98.030,28.405 98.030,57.095 97.395,57.730 83.595,57.730 83.230,58.095 83.230,63.000 | coupled |'),
    ('| USB_UP_P | F.Cu | 0.31 | 96.750,28.230 97.205,28.230 97.570,28.595 97.570,56.905 97.205,57.270 76.905,57.270 76.270,57.905 76.270,63.000 | coupled |',
     '| USB_UP_P | F.Cu | 0.31 | 96.750,28.230 97.205,28.230 97.570,28.595 97.570,56.905 97.205,57.270 83.405,57.270 82.770,57.905 82.770,63.000 | coupled |'),
    ('| USB_UP_N | F.Cu | 0.20 | 76.73,63.0 76.73,65.5 | lead-in to J1 B7 |',
     '| USB_UP_N | F.Cu | 0.20 | 83.23,63.0 83.23,65.5 | lead-in to J1 B7 |'),
    ('| USB_UP_P | F.Cu | 0.20 | 76.27,63.0 76.27,65.5 | lead-in to J1 A6 |',
     '| USB_UP_P | F.Cu | 0.20 | 82.77,63.0 82.77,65.5 | lead-in to J1 A6 |'),
    ('| USB_UP_N | F.Cu | 0.20 | J1.A7 75.75,66.55 76.75,66.55 J1.B7 | A7 to B7, on the body side |',
     '| USB_UP_N | F.Cu | 0.20 | J1.A7 82.25,66.55 83.25,66.55 J1.B7 | A7 to B7, on the body side |'),
    ('| USB_UP_P | F.Cu | 0.20 | J1.B6 75.25,64.1 76.27,64.1 | B6 to the lead-in of A6, on the lead-in side |',
     '| USB_UP_P | F.Cu | 0.20 | J1.B6 81.75,64.1 82.77,64.1 | B6 to the lead-in of A6, on the lead-in side |'),
    ('| VBUS_J1 | F.Cu | 0.25 | 73.8,65.5 73.8,67.3 78.2,67.3 78.2,65.5 | pad B4 to pad A4, under the connector body |',
     '| VBUS_J1 | F.Cu | 0.25 | 80.3,65.5 80.3,67.3 84.7,67.3 84.7,65.5 | pad B4 to pad A4, under the connector body |'),
    ('| USB_B_N | F.Cu | 0.31 | 95.400,23.770 96.405,23.770 96.770,23.405 96.770,16.545 96.405,16.180 51.205,16.180 50.570,15.545 50.570,9.000 | coupled |',
     '| USB_B_N | F.Cu | 0.31 | 95.400,23.770 96.405,23.770 96.770,23.405 96.770,16.545 96.405,16.180 82.405,16.180 81.770,15.545 81.770,9.000 | coupled |'),
    ('| USB_B_P | F.Cu | 0.31 | 95.400,24.230 96.595,24.230 97.230,23.595 97.230,16.355 96.595,15.720 51.395,15.720 51.030,15.355 51.030,9.000 | coupled |',
     '| USB_B_P | F.Cu | 0.31 | 95.400,24.230 96.595,24.230 97.230,23.595 97.230,16.355 96.595,15.720 82.595,15.720 82.230,15.355 82.230,9.000 | coupled |'),
    ('| USB_B_N | F.Cu | 0.20 | 50.57,9.0 50.57,6.5 | lead-in to J3 B7 |',
     '| USB_B_N | F.Cu | 0.20 | 81.77,9.0 81.77,6.5 | lead-in to J3 B7 |'),
    ('| USB_B_P | F.Cu | 0.20 | 51.03,9.0 51.03,6.5 | lead-in to J3 A6 |',
     '| USB_B_P | F.Cu | 0.20 | 82.23,9.0 82.23,6.5 | lead-in to J3 A6 |'),
    ('| USB_B_N | F.Cu | 0.20 | J3.A7 51.55,5.45 50.55,5.45 J3.B7 | A7 to B7, on the body side |',
     '| USB_B_N | F.Cu | 0.20 | J3.A7 82.75,5.45 81.75,5.45 J3.B7 | A7 to B7, on the body side |'),
    ('| USB_B_P | F.Cu | 0.20 | J3.B6 52.05,7.9 51.03,7.9 | B6 to the lead-in of A6, on the lead-in side |',
     '| USB_B_P | F.Cu | 0.20 | J3.B6 83.25,7.9 82.23,7.9 | B6 to the lead-in of A6, on the lead-in side |'),
    ('# USB Power-Control Hub — Rev0.5 routing',
     "# USB Power-Control Hub — Rev0.5 routing\n\n> **TRIAL C2 (issue #12): not the board's routing.** This copy was rewritten by `design/experiments/usb-symmetry-c2/c2_routing.py` for a routing trial of the connector placement C2 (`README.md` there). The pairs UP and B, the VBUS_B trunk and the rows at J1 and J3 differ from the board's, and the patch table is empty: its rows belong to the committed router session."),
]

# VBUS_A's J2 end: out of channel_route, into route, before its end.
MOVE = [
    '| VBUS_A | B.Cu | 1.80 | 20.9,7.9 26.33,7.9 26.33,19.25 | under the pairs, then to the lift vias at the receptacle |',
    '| VBUS_A | via | 0.60/0.30 | 20.9,7.9 |  |',
    '| VBUS_A | via | 0.60/0.30 | 21.7,7.9 |  |',
    '| VBUS_A | via | 0.60/0.30 | 22.5,7.9 |  |',
    '| VBUS_A | F.Cu | 0.60 | J2.B4 19.9,7.9 22.5,7.9 | pad B4 to the lift vias |',
    "| VBUS_A | F.Cu | 0.60 | 19.9,7.9 19.9,9.0 | the port capacitor C116's pad 1 |",
    '| VBUS_A | F.Cu | 0.25 | 15.3,5.9 15.3,4.7 19.7,4.7 19.7,5.9 | pad A4 to pad B4, under the connector body |',
]

# VBUS_B's trunk, and its J3 end (VBUS_A's J2 end, 65.0 mm east).
ADD = [
    '| VBUS_B | B.Cu | 1.80 | 60.13,19.25 60.13,18.2 | trial C2: from the lift vias at Q37 |',
    "| VBUS_B | B.Cu | 3.00 | 60.13,18.2 60.13,17.0 75.5,17.0 83.6,8.9 | trial C2: east under pair A in the corridor, then under pair B's lane; 3.0 mm because port B has 2.1 mOhm to spare |",
    '| VBUS_B | B.Cu | 1.80 | 83.6,8.9 84.6,7.9 87.5,7.9 | trial C2: to the lift vias at the receptacle |',
    '| VBUS_B | via | 0.60/0.30 | 85.9,7.9 |  |',
    '| VBUS_B | via | 0.60/0.30 | 86.7,7.9 |  |',
    '| VBUS_B | via | 0.60/0.30 | 87.5,7.9 |  |',
    '| VBUS_B | F.Cu | 0.60 | J3.B4 84.9,7.9 87.5,7.9 | pad B4 to the lift vias |',
    "| VBUS_B | F.Cu | 0.60 | 84.9,7.9 84.9,9.0 | the port capacitor C216's pad 1 |",
    '| VBUS_B | F.Cu | 0.25 | 80.3,5.9 80.3,4.7 84.7,4.7 84.7,5.9 | pad A4 to pad B4, under the connector body |',
]
ADD_BEFORE = "<!-- route:end -->"
PATCH_BEGIN = "<!-- patch:begin -->"
PATCH_END = "<!-- patch:end -->"


def apply(path):
    """Rewrite the routing document at `path`; returns the number of patch rows removed."""
    text = path.read_bytes().decode("utf-8")
    if "\r" in text:
        raise SystemExit(f"{path.name}: carriage returns in the document")
    lines = text.split("\n")

    def only(line):
        n = lines.count(line)
        if n != 1:
            raise SystemExit(f"{path.name}: {n} lines, not 1: {line}")
        return lines.index(line)

    for old, _ in REPLACE:
        only(old)
    for line in MOVE:
        only(line)

    for old, new in REPLACE:
        lines[only(old)] = new
    for line in MOVE:
        del lines[only(line)]
    end = only(ADD_BEFORE)
    lines[end:end] = MOVE + ADD

    begin = only(PATCH_BEGIN)
    sep = next(i for i in range(begin + 1, len(lines)) if lines[i].startswith("|---"))
    end = only(PATCH_END)
    removed = end - sep - 1
    del lines[sep + 1:end]

    path.write_bytes("\n".join(lines).encode("utf-8"))
    return removed
