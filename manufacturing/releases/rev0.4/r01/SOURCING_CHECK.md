# Sourcing check (V-MFG-02) - Rev0.4, 2026-11-12

Run for the pre-order review (issue #6). Not a release statement: the check is repeated immediately before payment (CLAUDE.md 4.1, V-MFG-02).

- **Assumed order:** 2 boards, the same quantity as the cost estimate and V-MEAS-06 / V-MFG-03 ("both first boards").
- **Rule:** every machine-placed line Basic with >= 500 assembly stock, except C2040 and C5137013 (Extended, the user's D29 and D31, which also need >= 500); no Preferred Extended; every hand-soldered part in stock at Akizuki for the quantity needed.
- **Method:** `tools/jlc_stock.py`'s API functions on every distinct LCSC code of `UsbPowerHub_Main_Rev0.4_BOM_JLCPCB.csv`; the 通販購入可能数 field of each Akizuki product page.
- **Result:** PASS

## Machine-placed parts (JLCPCB assembly pool)

| LCSC | MPN | Package | Class | JLCPCB stock | Per board | Need (2 boards) | Unit price USD (tier of need) | Min / loss |
|---|---|---|---|---:|---:|---:|---:|---|
| C1530 | 0402B221K500NT | 0402 | Basic | 1,242,245 | 8 | 16 | 0.0024 | 20 / 10 |
| C1548 | 0402CG150J500NT | 0402 | Basic | 1,122,079 | 8 | 16 | 0.0026 | 20 / 10 |
| C1664 | CL10C331JB8NNNC | 0603 | Basic | 627,169 | 4 | 8 | 0.0180 | 20 / 10 |
| C2040 | RP2040 | LQFN-56(7x7) | Extended - allowed: RP2040 (D29) | 83,664 | 1 | 2 | 1.0854 | 0 / 0 |
| C2297 | KT-0805G | 0805 | Basic | 1,844,595 | 2 | 4 | 0.0164 | 20 / 10 |
| C3113 | CJ431 | SOT-23 | Basic | 574,667 | 2 | 4 | 0.0365 | 5 / 4 |
| C6186 | AMS1117-3.3 | SOT-223 | Basic | 1,500,105 | 1 | 2 | 0.1938 | 2 / 0 |
| C7433 | OP07CDR | SOIC-8 | Basic | 297,137 | 6 | 12 | 0.1119 | 0 / 0 |
| C7955 | LM393DR2G | SOIC-8 | Basic | 332,771 | 3 | 6 | 0.0592 | 0 / 1 |
| C8543 | S9012 2T1(RANGE:200-350) | SOT-23 | Basic | 353,265 | 2 | 4 | 0.0162 | 10 / 5 |
| C8545 | 2N7002 | SOT-23 | Basic | 6,111,454 | 17 | 34 | 0.0154 | 10 / 8 |
| C9002 | X322512MSB4SI | SMD3225-4P | Basic | 318,098 | 2 | 4 | 0.0953 | 5 / 2 |
| C11702 | 0402WGF1001TCE | 0402 | Basic | 32,211,020 | 21 | 42 | 0.0013 | 20 / 10 |
| C14709 | BLM18PG121SN1D | 0603 | Basic | 1,787,999 | 1 | 2 | 0.0137 | 20 / 14 |
| C15127 | AO3401A | SOT-23 | Basic | 1,615,620 | 15 | 30 | 0.0813 | 5 / 4 |
| C15195 | CL05B103KB5NNNC | 0402 | Basic | 4,579,684 | 4 | 8 | 0.0037 | 20 / 15 |
| C15850 | CL21A106KAYNNNE | 0805 | Basic | 8,203,208 | 7 | 14 | 0.0314 | 20 / 10 |
| C17734 | 0805W8F5100T5E | 0805 | Basic | 1,963,211 | 8 | 16 | 0.0039 | 20 / 10 |
| C20917 | AO3400A | SOT-23 | Basic | 930,114 | 2 | 4 | 0.0801 | 5 / 4 |
| C22940 | 0603WAF2401T5E | 0603 | Basic | 431,986 | 2 | 4 | 0.0026 | 20 / 10 |
| C25076 | 0402WGF1000TCE | 0402 | Basic | 11,232,414 | 6 | 12 | 0.0012 | 20 / 15 |
| C25077 | 0402WGF100JTCE | 0402 | Basic | 3,165,970 | 2 | 4 | 0.0010 | 20 / 15 |
| C25092 | 0402WGF220JTCE | 0402 | Basic | 5,097,425 | 2 | 4 | 0.0033 | 20 / 15 |
| C25197 | 0603WAF510KT5E | 0603 | Basic | 679,492 | 2 | 4 | 0.0029 | 20 / 10 |
| C25741 | 0402WGF1003TCE | 0402 | Basic | 8,919,590 | 14 | 28 | 0.0011 | 20 / 12 |
| C25744 | 0402WGF1002TCE | 0402 | Basic | 20,650,862 | 17 | 34 | 0.0010 | 20 / 15 |
| C25756 | 0402WGF1502TCE | 0402 | Basic | 2,168,899 | 10 | 20 | 0.0011 | 20 / 10 |
| C25779 | 0402WGF3302TCE | 0402 | Basic | 2,213,107 | 7 | 14 | 0.0019 | 20 / 10 |
| C25867 | 0402WGF1501TCE | 0402 | Basic | 1,302,975 | 8 | 16 | 0.0029 | 20 / 15 |
| C25905 | 0402WGF5101TCE | 0402 | Basic | 4,154,325 | 7 | 14 | 0.0014 | 20 / 15 |
| C26083 | 0402WGF1004TCE | 0402 | Basic | 2,519,926 | 12 | 24 | 0.0012 | 20 / 15 |
| C32677 | PSM712-LF-T7 | SOT-23 | Basic | 152,199 | 4 | 8 | 0.3387 | 5 / 1 |
| C45783 | CL21A226MAQNNNE | 0805 | Basic | 3,751,733 | 4 | 8 | 0.1055 | 5 / 4 |
| C52923 | CL05A105KA5NQNC | 0402 | Basic | 10,704,666 | 8 | 16 | 0.0057 | 20 / 12 |
| C84256 | NCD0805R1 | 0805 | Basic | 1,635,573 | 2 | 4 | 0.0131 | 20 / 10 |
| C97521 | W25Q128JVSIQ | SOIC-8-208mil | Basic | 75,759 | 1 | 2 | 2.2574 | 0 / 0 |
| C307331 | CL05B104KB54PNC | 0402 | Basic | 20,459,780 | 26 | 52 | 0.0085 | 20 / 12 |
| C318884 | TS-1187A-B-A-B | SMD-4P,5.1x5.1mm | Basic | 832,765 | 3 | 6 | 0.0215 | 5 / 8 |
| C5137013 | CH335F | QFN-28(4x4) | Extended - allowed: CH335F (D31) | 5,500 | 1 | 2 | 1.1132 | 0 / 0 |
| C7420377 | SMBJ6.5CA | DO-214AA(SMB) | Basic | 1,128,312 | 2 | 4 | 0.0422 | 5 / 4 |

Estimated parts cost at these tiers, 2 boards, need + loss and at least the minimum: 24.73 USD. It excludes the Extended-part fee and every other fee; the quote at JLCPCB is the authority.

## Hand-soldered parts (Akizuki)

| Akizuki | Part | Used by | Price (tax incl.) | 通販購入可能数 | Need | OK |
|---|---|---|---|---:|---:|---|
| g100167 | ピンヘッダー 1×40 (40P) | J1-J4 headers (44 pins per board, cut from 1 x 40 strips) | ￥35(税込) | 8,000 | 3 | yes |
| g100238 | 12bit 8ch ADコンバーター MCP3208-CI/P | U7, U17 | ￥500(税込) | 97 | 4 | yes |
| g104132 | 1W級絶縁型DCDCコンバーター(12V84mA)MAU104 | U5 | ￥520(税込) | 135 | 2 | yes |
| g108805 | 超小型 金属皮膜抵抗 1W10Ω | RS11, RS21 | ￥600(税込) | 170 | 4 | yes |
| g109588 | 電流検出用チップ抵抗器 1W0.1Ω ±0.5% | RS10, RS20 | ￥130(税込) | 351 | 4 | yes |
| g112630 | リセッタブルヒューズ 3A トリップ電流:6A 耐圧:30V MF-R300 | F1 | ￥40(税込) | 2,759 | 2 | yes |
| g113080 | USBtype-CコネクターDIP化キット(シンプル版) | J1, J2, J3, J4 | ￥350(税込) | 673 | 8 | yes |

Not covered: the 12 hand-soldered parts' electrical suitability (requirements/parts.md), stock at the minute of payment, and any part that needs a cable or tool (the user's own).
