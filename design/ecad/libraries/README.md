# Project libraries (Rev0.5, issues #6 P1, P5, #8)

The KiCad symbol and footprint library for every part in Rev0.5 §6.2. State: **WIP**. No
land here has been soldered or seen in the JLCPCB placement preview.

| File | What it is | Written by |
|---|---|---|
| `library.json` | The parts register: one entry per symbol, with its pins and land facts and the datasheet page each was read from | hand (the evidence) |
| `usb-power-hub.kicad_sym` | 32 symbols, flattened (no `extends`): one per part, and PWR_FLAG, because the project has no global symbol table (P2) | `make_libraries.py` |
| `usb-power-hub.pretty/` | 28 footprints: 20 copies of KiCad 9.0.8 stock (its CRLF written as LF, its silkscreen adapted, below), 8 generated | `make_libraries.py` |
| `../source/fp-lib-table`, `../source/sym-lib-table` | the project's library tables (`${KIPRJMOD}/../libraries/...`) | `make_libraries.py` |

Do not edit the `.kicad_sym` or `.pretty` by hand. Change `library.json` or the generator,
then regenerate.

## Regenerate and check

From the repository root, with KiCad's own Python:

```sh
"<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/make_libraries.py        # write + check
"<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/check_libraries.py       # check only
"<KiCad 9.0>/bin/python.exe" -I -B design/ecad/scripts/test_check_libraries.py  # 29 tests (a clean copy, 28 corruptions), about 85 s
```

`check_libraries.py` exits 0 only if every check passes. Its docstring lists what it checks
and what it cannot see. In short:

- each symbol's pins against the datasheet pin names;
- each footprint's pads against its symbol's pins;
- each land against the datasheet's numbers in `land`;
- stock copies against KiCad's, its CRLF read as LF: byte for byte outside the F.SilkS
  shapes, and each F.SilkS shape KiCad's with its stroke widened, or none for a `silk_drop`
  footprint;
- every F.SilkS stroke ≥ 0.15 mm and ≥ 0.15 mm from the footprint's own mask openings
  (JLCPCB's legend limits, `library.json` `about`); `silk_drop` only on non-polar parts and
  only on footprints the part uses;
- no CR byte in any file here: the repository stores LF (`.gitattributes`), so the checked
  bytes are the ones a checkout holds;
- Kelvin net ties against their force / sense pairs;
- the library tables;
- a parse by `kicad-cli`;
- a DRC run of every footprint on a copy of the project board with its rules.

## Register fields

- `land`: what the datasheet says, in its own terms. The checker reads only this.
  `footprint.params` are the generator's design choices, so a wrong parameter shows up as a
  land failure.
- `land.kind` names the check:
  - `qfn_land` (U1): exact; the datasheet gives a land.
  - `qfn` (U6), `dual`, `sot23`, `sot223`, `chip`: coverage. Each pad contains the nominal
    terminal and reaches past the maximum tip. This is not IPC fillet compliance.
  - `kelvin_chip` (RS10/RS20): the derived 4-pad land.
  - `pads` and `holes`: exact positions.
  - `generic` (R, C): deferred to P2.
- `pins`: number → datasheet name. A `[datasheet, symbol]` pair means the stock symbol spells
  the pin differently. A plain name is compared ignoring case and punctuation.
- `proxy`, and notes starting with `ASSUMED`, `UNCERTAIN`, `PROVISIONAL` or `DERIVED`, are
  printed by the checker as `NOTE` lines. `requirements/parts.md` ("Symbols and footprints")
  lists the open ones.

## Generated footprints

| Footprint | Part | Source of the geometry |
|---|---|---|
| `RP2040_QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm` | U1 | RP2040 datasheet Figure 167 (G20) |
| `CH335F_QFN-28-1EP_4x4mm_P0.4mm_EP2.7x2.7mm` | U6 | CH334/335 datasheet §5.6 package (G21) |
| `R_Shunt_KOA_TSL1_6332Metric_Kelvin` | RS10, RS20 (R_H) | KOA TSL body and electrodes; land derived (KOA gives none) |
| `R_Shunt_Axial_MFU_L6.0mm_D2.3mm_P10.16mm_Kelvin` | RS11, RS21 (R_M) | MFU body; sense pads tied at each lead (net tie) |
| `R_Shunt_0805_2012Metric_Kelvin` | RS12, RS22 (R_L) | KiCad R_0805 land, sense pads tied at each pad (net tie) |
| `Fuse_Bourns_MF-R300_Style2_P5.10mm` | F1 | Bourns MF-R table and style 2 drawing |
| `Converter_DCDC_Minmax_MAU104_SIP` | U5 | MAU100 pin pattern and body |
| `USB_C_Receptacle_SHOUHAN_TYPE-C-16PIN-2MD-073` | J1–J4 | the maker's drawing of C2765186 (sheet 1 of 1): 12 contacts, 4 plated shell slots, 2 unplated pegs (D37) |

The receptacle's land is the maker's recommended one, which the drawing gives for a 0.80 mm
board; this board is 1.6 mm (OI-33). Contacts A1 and B1 (GND) are 0.035 mm shorter at their near
end than the drawing: it leaves 0.165 mm from each peg hole to them, and JLCPCB asks 0.20 mm
between an unplated hole and copper. `usb-power-hub.kicad_dru` holds a rule for this
footprint's pegs alone. The courtyard is the body's outline and the shell pads' plus 0.25 mm;
the front face lies past the board edge, so `check_pcb.py` cuts it to the board.
