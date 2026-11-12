//! Stream framing (requirements/product.md section 4.2, bit layout chosen for issue #9) and the
//! `CAL?` response of the control protocol (section 4.1).
//!
//! # Stream frame (all multi-byte fields little endian)
//!
//! ```text
//! A5 5A            sync
//! version  u8      = 1
//! flags    u8      bit 0 fault A, bit 1 fault B (port opened by hardware), others 0
//! sequence u16     index of the frame's first 1 ms ADC frame (wraps at 65536)
//! n        u16     number of records, a multiple of 14 (n / 14 ADC frames), n > 0
//! n records, 5 bytes each
//! crc      u16     CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, no reflection, xorout 0)
//!                  over version .. last record (everything after the sync bytes)
//! ```
//!
//! # Record (5 bytes)
//!
//! ```text
//! code A u16   12-bit conversion of channel A (upper 4 bits are masked off on parse)
//! code B u16   same for channel B
//! byte         bits 0-1 range A, bits 2-3 range B (0 LOW, 1 MID, 2 HIGH, 3 reserved),
//!              bit 4 settling A, bit 5 clipped A, bit 6 settling B, bit 7 clipped B
//! ```
//!
//! # Timing
//!
//! Each 1 ms ADC frame holds 14 samples. Sample k (0..13) of ADC frame f is taken at
//! `f * 1000 us + k * 69 us` (13 * 69 + 103 = 1000). A sequence number other than the previous
//! one plus n / 14 (mod 65536) is lost data (see `store`).
//!
//! # Conversion
//!
//! `I = (code - offset) * gain` per channel and range, from `CAL? A` / `CAL? B`, whose response
//! this tool parses as `OK LOW=<gain_nA_per_code>,<offset_code> MID=<g>,<o> HIGH=<g>,<o>`.

pub const SYNC: [u8; 2] = [0xA5, 0x5A];
pub const VERSION: u8 = 1;
pub const HEADER_LEN: usize = 8;
pub const RECORD_LEN: usize = 5;
pub const CRC_LEN: usize = 2;
pub const SAMPLES_PER_FRAME: usize = 14;
/// Upper bound on n that the parser accepts (200 ADC frames = 200 ms). A larger n is a corrupt
/// header, and waiting for its payload would stall the resynchronisation.
pub const MAX_RECORDS: usize = SAMPLES_PER_FRAME * 200;

pub const FLAG_FAULT_A: u8 = 1;
pub const FLAG_FAULT_B: u8 = 2;

/// Range codes: 0 LOW, 1 MID, 2 HIGH, 3 reserved (the store reads 3 as "no data").
pub const RANGE_HIGH: u8 = 2;

/// CRC-16/CCITT-FALSE. `crc16(b"123456789") == 0x29B1`.
pub fn crc16(data: &[u8]) -> u16 {
    let mut crc: u16 = 0xFFFF;
    for &b in data {
        crc ^= (b as u16) << 8;
        for _ in 0..8 {
            crc = if crc & 0x8000 != 0 { (crc << 1) ^ 0x1021 } else { crc << 1 };
        }
    }
    crc
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Record {
    pub code: [u16; 2],
    pub range: [u8; 2],
    pub settling: [bool; 2],
    pub clipped: [bool; 2],
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Frame {
    pub flags: u8,
    pub seq: u16,
    pub records: Vec<Record>,
}

impl Frame {
    /// Number of 1 ms ADC frames in this stream frame.
    pub fn adc_frames(&self) -> u16 {
        (self.records.len() / SAMPLES_PER_FRAME) as u16
    }
}

/// Serialises a frame. `records.len()` must be a non-zero multiple of 14 (a programming error
/// otherwise, since only the demo device and the tests call this).
pub fn encode_frame(flags: u8, seq: u16, records: &[Record]) -> Vec<u8> {
    assert!(!records.is_empty() && records.len().is_multiple_of(SAMPLES_PER_FRAME), "n must be a multiple of 14");
    let mut v = Vec::with_capacity(HEADER_LEN + records.len() * RECORD_LEN + CRC_LEN);
    v.extend_from_slice(&SYNC);
    v.push(VERSION);
    v.push(flags);
    v.extend_from_slice(&seq.to_le_bytes());
    v.extend_from_slice(&(records.len() as u16).to_le_bytes());
    for r in records {
        v.extend_from_slice(&r.code[0].to_le_bytes());
        v.extend_from_slice(&r.code[1].to_le_bytes());
        let b = (r.range[0] & 3)
            | (r.range[1] & 3) << 2
            | (r.settling[0] as u8) << 4
            | (r.clipped[0] as u8) << 5
            | (r.settling[1] as u8) << 6
            | (r.clipped[1] as u8) << 7;
        v.push(b);
    }
    let crc = crc16(&v[2..]);
    v.extend_from_slice(&crc.to_le_bytes());
    v
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct ParserStats {
    pub frames: u64,
    pub crc_errors: u64,
    /// Runs of bytes that were skipped to find a sync (garbage, or a header that failed its checks).
    pub sync_losses: u64,
    pub skipped_bytes: u64,
}

/// Incremental parser: feed it whatever the port delivers, collect whole frames.
#[derive(Default)]
pub struct StreamParser {
    buf: Vec<u8>,
    skipping: bool,
    pub stats: ParserStats,
}

impl StreamParser {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn reset(&mut self) {
        self.buf.clear();
        self.skipping = false;
    }

    fn skip(&mut self, n: usize, garbage: bool) {
        self.stats.skipped_bytes += n as u64;
        if garbage && !self.skipping {
            self.stats.sync_losses += 1;
        }
        self.skipping = true;
    }

    pub fn push(&mut self, data: &[u8], out: &mut Vec<Frame>) {
        self.buf.extend_from_slice(data);
        let mut pos = 0usize;
        loop {
            let rest = &self.buf[pos..];
            match rest.windows(2).position(|w| w == SYNC) {
                None => {
                    // A trailing lone 0xA5 may be the first half of a sync split across reads.
                    let keep = usize::from(rest.last() == Some(&SYNC[0]));
                    let drop = rest.len() - keep;
                    if drop > 0 {
                        self.skip(drop, true);
                    }
                    pos += drop;
                    break;
                }
                Some(off) => {
                    if off > 0 {
                        self.skip(off, true);
                    }
                    pos += off;
                }
            }
            let rest = &self.buf[pos..];
            if rest.len() < HEADER_LEN {
                break;
            }
            let version = rest[2];
            let flags = rest[3];
            let seq = u16::from_le_bytes([rest[4], rest[5]]);
            let n = u16::from_le_bytes([rest[6], rest[7]]) as usize;
            if version != VERSION || n == 0 || !n.is_multiple_of(SAMPLES_PER_FRAME) || n > MAX_RECORDS {
                self.skip(2, true);
                pos += 2;
                continue;
            }
            let total = HEADER_LEN + n * RECORD_LEN + CRC_LEN;
            if rest.len() < total {
                break;
            }
            let body_end = total - CRC_LEN;
            let want = u16::from_le_bytes([rest[body_end], rest[body_end + 1]]);
            if crc16(&rest[2..body_end]) != want {
                self.stats.crc_errors += 1;
                self.skip(2, false);
                pos += 2;
                continue;
            }
            let mut records = Vec::with_capacity(n);
            for r in rest[HEADER_LEN..body_end].chunks_exact(RECORD_LEN) {
                let b = r[4];
                records.push(Record {
                    code: [
                        u16::from_le_bytes([r[0], r[1]]) & 0x0FFF,
                        u16::from_le_bytes([r[2], r[3]]) & 0x0FFF,
                    ],
                    range: [b & 3, (b >> 2) & 3],
                    settling: [b & 0x10 != 0, b & 0x40 != 0],
                    clipped: [b & 0x20 != 0, b & 0x80 != 0],
                });
            }
            out.push(Frame { flags, seq, records });
            self.stats.frames += 1;
            self.skipping = false;
            pos += total;
        }
        self.buf.drain(..pos);
    }
}

/// Calibration of one channel: gain in nA per code and offset in codes, per range.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Cal {
    pub gain_na: [f64; 3],
    pub offset: [f64; 3],
}

impl Cal {
    /// Nominal values used by the demo device: full scale 409.6 uA, 20.9 mA, 1.305 A.
    pub const NOMINAL: Cal = Cal { gain_na: [100.0, 5100.0, 318_750.0], offset: [0.0; 3] };

    /// Current in amperes. `range` must be 0..=2.
    pub fn amps(&self, range: u8, code: u16) -> f64 {
        let r = (range as usize).min(2);
        (code as f64 - self.offset[r]) * self.gain_na[r] * 1e-9
    }

    /// Largest current the range can report (code 4095).
    pub fn top(&self, range: u8) -> f64 {
        self.amps(range, 4095)
    }

    /// Text of the `CAL?` response, as the device sends it.
    pub fn to_response(self) -> String {
        format!(
            "OK LOW={},{} MID={},{} HIGH={},{}",
            self.gain_na[0], self.offset[0], self.gain_na[1], self.offset[1], self.gain_na[2], self.offset[2]
        )
    }

    /// Parses `OK LOW=<g>,<o> MID=<g>,<o> HIGH=<g>,<o>`. Gains must be finite and positive.
    pub fn parse(resp: &str) -> Option<Cal> {
        let mut it = resp.split_whitespace();
        if it.next()? != "OK" {
            return None;
        }
        let mut cal = Cal { gain_na: [0.0; 3], offset: [0.0; 3] };
        for (i, name) in ["LOW", "MID", "HIGH"].iter().enumerate() {
            let tok = it.next()?;
            let val = tok.strip_prefix(name)?.strip_prefix('=')?;
            let (g, o) = val.split_once(',')?;
            let g: f64 = g.parse().ok()?;
            let o: f64 = o.parse().ok()?;
            if !(g.is_finite() && g > 0.0 && o.is_finite()) {
                return None;
            }
            cal.gain_na[i] = g;
            cal.offset[i] = o;
        }
        if it.next().is_some() {
            return None;
        }
        Some(cal)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn recs(n: usize, base: u16) -> Vec<Record> {
        (0..n)
            .map(|i| Record {
                code: [(base + i as u16) & 0xFFF, (base + 7 * i as u16) & 0xFFF],
                range: [(i % 3) as u8, ((i + 1) % 3) as u8],
                settling: [i % 5 == 0, i % 7 == 0],
                clipped: [i % 11 == 0, i % 13 == 0],
            })
            .collect()
    }

    fn parse_all(bytes: &[u8]) -> (Vec<Frame>, ParserStats) {
        let mut p = StreamParser::new();
        let mut out = Vec::new();
        p.push(bytes, &mut out);
        (out, p.stats)
    }

    #[test]
    fn crc_check_value() {
        assert_eq!(crc16(b"123456789"), 0x29B1);
        assert_eq!(crc16(b""), 0xFFFF);
    }

    #[test]
    fn frame_roundtrip_and_layout() {
        let r = recs(28, 100);
        let bytes = encode_frame(FLAG_FAULT_B, 0x1234, &r);
        assert_eq!(&bytes[..2], &[0xA5, 0x5A]);
        assert_eq!(bytes[2], 1);
        assert_eq!(bytes[3], 2);
        assert_eq!(&bytes[4..6], &[0x34, 0x12]);
        assert_eq!(&bytes[6..8], &[28, 0]);
        assert_eq!(bytes.len(), 8 + 28 * 5 + 2);
        // record 0: code A = 100, code B = 100, range A 0, range B 1, settling A and B, clipped A and B
        assert_eq!(&bytes[8..13], &[100, 0, 100, 0, 0b1111_0100]);
        let (f, st) = parse_all(&bytes);
        assert_eq!(f.len(), 1);
        assert_eq!(f[0].flags, FLAG_FAULT_B);
        assert_eq!(f[0].seq, 0x1234);
        assert_eq!(f[0].records, r);
        assert_eq!(st.crc_errors, 0);
        assert_eq!(st.sync_losses, 0);
    }

    #[test]
    fn resync_after_garbage_and_split_reads() {
        let a = encode_frame(0, 0, &recs(14, 1));
        let b = encode_frame(0, 1, &recs(14, 50));
        let mut stream = vec![0x00, 0xA5, 0x11, 0xFF, 0xA5];
        stream.extend_from_slice(&a);
        stream.extend_from_slice(&[1, 2, 3, 0xA5]);
        stream.extend_from_slice(&b);
        // whole
        let (f, st) = parse_all(&stream);
        assert_eq!(f.iter().map(|x| x.seq).collect::<Vec<_>>(), vec![0, 1]);
        assert_eq!(st.sync_losses, 2);
        // byte by byte gives the same frames
        let mut p = StreamParser::new();
        let mut out = Vec::new();
        for byte in &stream {
            p.push(std::slice::from_ref(byte), &mut out);
        }
        assert_eq!(out.iter().map(|x| x.seq).collect::<Vec<_>>(), vec![0, 1]);
        assert_eq!(p.stats.sync_losses, 2);
    }

    #[test]
    fn bad_crc_is_counted_and_next_frame_survives() {
        let mut a = encode_frame(0, 0, &recs(14, 1));
        let b = encode_frame(0, 1, &recs(14, 9));
        a[20] ^= 0x40;
        let mut s = a;
        s.extend_from_slice(&b);
        let (f, st) = parse_all(&s);
        assert_eq!(f.len(), 1);
        assert_eq!(f[0].seq, 1);
        assert_eq!(st.crc_errors, 1);
    }

    #[test]
    fn n_not_multiple_of_14_is_rejected() {
        // Hand-built frame with n = 15 and a valid CRC: it must still be refused.
        let mut v = vec![0xA5, 0x5A, 1, 0, 0, 0, 15, 0];
        v.extend(std::iter::repeat_n(0u8, 15 * 5));
        let crc = crc16(&v[2..]);
        v.extend_from_slice(&crc.to_le_bytes());
        let good = encode_frame(0, 3, &recs(14, 1));
        v.extend_from_slice(&good);
        let (f, st) = parse_all(&v);
        assert_eq!(f.len(), 1);
        assert_eq!(f[0].seq, 3);
        assert!(st.sync_losses >= 1);
        // n = 0 and a wrong version are refused as well
        let mut z = vec![0xA5, 0x5A, 1, 0, 0, 0, 0, 0, 0, 0];
        z.extend_from_slice(&good);
        assert_eq!(parse_all(&z).0.len(), 1);
        let mut w = encode_frame(0, 4, &recs(14, 1));
        w[2] = 2;
        assert_eq!(parse_all(&w).0.len(), 0);
    }

    #[test]
    fn oversized_n_does_not_stall() {
        let mut v = vec![0xA5, 0x5A, 1, 0, 0, 0];
        v.extend_from_slice(&(14u16 * 4000).to_le_bytes());
        v.extend_from_slice(&encode_frame(0, 9, &recs(14, 1)));
        assert_eq!(parse_all(&v).0.len(), 1);
    }

    #[test]
    fn cal_parse() {
        let c = Cal::parse("OK LOW=100,0 MID=5100,2.5 HIGH=318750,-1").unwrap();
        assert_eq!(c.gain_na, [100.0, 5100.0, 318750.0]);
        assert_eq!(c.offset, [0.0, 2.5, -1.0]);
        assert_eq!(Cal::parse(&Cal::NOMINAL.to_response()), Some(Cal::NOMINAL));
        assert!(Cal::parse("OK LOW=100,0 MID=5100,0").is_none());
        assert!(Cal::parse("ERR 02 BAD ARGUMENT").is_none());
        assert!(Cal::parse("OK LOW=0,0 MID=1,0 HIGH=1,0").is_none());
        assert!(Cal::parse("OK LOW=1,0 MID=1,0 HIGH=1,0 X").is_none());
    }

    #[test]
    fn conversion() {
        let c = Cal { gain_na: [100.0, 5100.0, 318_750.0], offset: [10.0, 0.0, 0.0] };
        assert!((c.amps(0, 110) - 10e-6).abs() < 1e-15);
        assert!((c.amps(1, 100) - 510e-6).abs() < 1e-12);
        assert!((c.top(0) - 409.5e-6 + 1e-6).abs() < 1e-9); // (4095-10)*0.1uA
        assert!((Cal::NOMINAL.top(0) - 409.5e-6).abs() < 1e-9);
    }
}
