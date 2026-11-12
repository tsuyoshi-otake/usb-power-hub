//! Sample store: one u16 per sample per channel (12-bit code, 2 range bits, settling, clipped), a
//! min/max/sum pyramid so that any query costs O(log n), lost-data and fault spans, and CSV export.
//!
//! The sample index is the time axis: index i is sample `i % 14` of ADC frame `i / 14`, taken at
//! `time_us(i)` after the start of the recording. Lost data is filled with `NO_DATA` samples so that
//! the index stays equal to the time; nothing ever bridges them.

use crate::protocol::{Cal, Frame, SAMPLES_PER_FRAME};
use std::io::{self, Write};

pub const SAMPLE_PERIOD_US: u64 = 69;
pub const ADC_FRAME_US: u64 = 1000;
/// Samples per second per channel (14 per millisecond).
pub const SAMPLE_RATE: f64 = 14_000.0;
const BLOCK: u64 = 32;

pub const NO_DATA: u16 = 3 << 12;

pub fn pack(code: u16, range: u8, settling: bool, clipped: bool) -> u16 {
    (code & 0x0FFF) | ((range as u16 & 3) << 12) | (settling as u16) << 14 | (clipped as u16) << 15
}
pub fn unpack_code(p: u16) -> u16 {
    p & 0x0FFF
}
pub fn unpack_range(p: u16) -> u8 {
    ((p >> 12) & 3) as u8
}
pub fn is_settling(p: u16) -> bool {
    p & 0x4000 != 0
}
pub fn is_clipped(p: u16) -> bool {
    p & 0x8000 != 0
}
pub fn has_data(p: u16) -> bool {
    unpack_range(p) != 3
}

/// Microseconds from the start of the recording to sample `i`.
pub fn time_us(i: u64) -> u64 {
    (i / 14) * ADC_FRAME_US + (i % 14) * SAMPLE_PERIOD_US
}

/// Index of the last sample taken at or before `t_us` (0 for t < 0).
pub fn index_at(t_us: f64) -> u64 {
    if t_us <= 0.0 {
        return 0;
    }
    let f = (t_us / ADC_FRAME_US as f64).floor();
    let r = t_us - f * ADC_FRAME_US as f64;
    let k = ((r / SAMPLE_PERIOD_US as f64).floor() as u64).min(13);
    f as u64 * 14 + k
}

pub const MASK_SETTLING: u8 = 0x08;
pub const MASK_CLIPPED: u8 = 0x10;

#[derive(Clone, Copy, Debug)]
pub struct Node {
    pub min: f32,
    pub max: f32,
    pub sum: f64,
    pub count: u32,
    /// bits 0-2: ranges present (LOW, MID, HIGH); bit 3 settling; bit 4 clipped.
    pub mask: u8,
}

impl Node {
    pub const EMPTY: Node = Node { min: f32::INFINITY, max: f32::NEG_INFINITY, sum: 0.0, count: 0, mask: 0 };

    pub fn add(&mut self, amps: f64, packed: u16) {
        self.min = self.min.min(amps as f32);
        self.max = self.max.max(amps as f32);
        self.sum += amps;
        self.count += 1;
        self.mask |= 1 << unpack_range(packed);
        if is_settling(packed) {
            self.mask |= MASK_SETTLING;
        }
        if is_clipped(packed) {
            self.mask |= MASK_CLIPPED;
        }
    }

    pub fn merge(&mut self, o: &Node) {
        self.min = self.min.min(o.min);
        self.max = self.max.max(o.max);
        self.sum += o.sum;
        self.count += o.count;
        self.mask |= o.mask;
    }

    pub fn mean(&self) -> Option<f64> {
        (self.count > 0).then(|| self.sum / self.count as f64)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Span {
    pub start: u64,
    pub end: u64,
}

pub struct Channel {
    pub cal: Cal,
    data: Vec<u16>,
    /// levels[0][j] covers samples [j*32, j*32+32); levels[k+1][j] merges levels[k][2j], levels[k][2j+1].
    levels: Vec<Vec<Node>>,
}

impl Channel {
    fn new(cal: Cal) -> Self {
        Channel { cal, data: Vec::new(), levels: Vec::new() }
    }

    pub fn len(&self) -> u64 {
        self.data.len() as u64
    }

    pub fn get(&self, i: u64) -> u16 {
        self.data[i as usize]
    }

    pub fn amps_at(&self, i: u64) -> Option<f64> {
        let p = *self.data.get(i as usize)?;
        has_data(p).then(|| self.cal.amps(unpack_range(p), unpack_code(p)))
    }

    fn push(&mut self, p: u16) {
        self.data.push(p);
        let n = self.data.len() as u64;
        if n.is_multiple_of(BLOCK) {
            let node = self.node_of(n - BLOCK, n);
            self.push_node(0, node);
        }
    }

    fn push_node(&mut self, lvl: usize, node: Node) {
        if self.levels.len() <= lvl {
            self.levels.push(Vec::new());
        }
        self.levels[lvl].push(node);
        let len = self.levels[lvl].len();
        if len.is_multiple_of(2) {
            let mut m = self.levels[lvl][len - 2];
            m.merge(&self.levels[lvl][len - 1]);
            self.push_node(lvl + 1, m);
        }
    }

    /// Brute-force scan of [i0, i1), used for the unaligned edges and by the tests.
    pub fn node_of(&self, i0: u64, i1: u64) -> Node {
        let mut n = Node::EMPTY;
        let end = i1.min(self.len());
        for i in i0..end {
            let p = self.data[i as usize];
            if has_data(p) {
                n.add(self.cal.amps(unpack_range(p), unpack_code(p)), p);
            }
        }
        n
    }

    /// Min / max / sum / count / flags over [i0, i1) in O(log n).
    pub fn query(&self, i0: u64, i1: u64) -> Node {
        let i1 = i1.min(self.len());
        if i0 >= i1 {
            return Node::EMPTY;
        }
        let b0 = i0.div_ceil(BLOCK);
        let b1 = i1 / BLOCK;
        if b0 >= b1 {
            return self.node_of(i0, i1);
        }
        let mut acc = self.node_of(i0, b0 * BLOCK);
        acc.merge(&self.node_of(b1 * BLOCK, i1));
        let (mut a, mut b) = (b0 as usize, b1 as usize);
        let mut lvl = 0;
        while a < b {
            if a & 1 == 1 {
                acc.merge(&self.levels[lvl][a]);
                a += 1;
            }
            if b & 1 == 1 {
                b -= 1;
                acc.merge(&self.levels[lvl][b]);
            }
            a >>= 1;
            b >>= 1;
            lvl += 1;
        }
        acc
    }
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct PushOutcome {
    pub stored: bool,
    /// ADC frames missing before this frame (sequence gap).
    pub lost_adc_frames: u32,
    pub full: bool,
}

pub struct Store {
    pub ch: [Channel; 2],
    pub lost: Vec<Span>,
    pub fault: [Vec<Span>; 2],
    next_seq: Option<u16>,
    max_samples: u64,
    pub lost_events: u64,
    pub lost_adc_frames: u64,
}

impl Store {
    pub fn new(cal: [Cal; 2], max_minutes: f64) -> Self {
        Store {
            ch: [Channel::new(cal[0]), Channel::new(cal[1])],
            lost: Vec::new(),
            fault: [Vec::new(), Vec::new()],
            next_seq: None,
            max_samples: (max_minutes * 60.0 * SAMPLE_RATE) as u64,
            lost_events: 0,
            lost_adc_frames: 0,
        }
    }

    /// Samples per channel.
    pub fn len(&self) -> u64 {
        self.ch[0].len()
    }

    pub fn duration_us(&self) -> f64 {
        time_us(self.len()) as f64
    }

    pub fn set_max_minutes(&mut self, m: f64) {
        self.max_samples = (m * 60.0 * SAMPLE_RATE) as u64;
    }

    /// Forget the sequence number: the next frame is not compared with the previous one. Used when
    /// the stream is (re)started or recording resumes after a pause.
    pub fn resync(&mut self) {
        self.next_seq = None;
    }

    fn mark(spans: &mut Vec<Span>, start: u64, end: u64) {
        match spans.last_mut() {
            Some(l) if l.end == start => l.end = end,
            _ => spans.push(Span { start, end }),
        }
    }

    pub fn push_frame(&mut self, f: &Frame) -> PushOutcome {
        let n = f.records.len() as u64;
        let gap = match self.next_seq {
            Some(e) => f.seq.wrapping_sub(e) as u64,
            None => 0,
        };
        // The frame is only stored whole, so a limit hit never leaves half a frame.
        if self.len() + gap * SAMPLES_PER_FRAME as u64 + n > self.max_samples {
            return PushOutcome { stored: false, lost_adc_frames: 0, full: true };
        }
        self.next_seq = Some(f.seq.wrapping_add(f.adc_frames()));
        if gap > 0 {
            let s = self.len();
            let e = s + gap * SAMPLES_PER_FRAME as u64;
            for c in 0..2 {
                for _ in s..e {
                    self.ch[c].push(NO_DATA);
                }
            }
            Self::mark(&mut self.lost, s, e);
            self.lost_events += 1;
            self.lost_adc_frames += gap;
        }
        let start = self.len();
        for r in &f.records {
            for c in 0..2 {
                self.ch[c].push(pack(r.code[c], r.range[c], r.settling[c], r.clipped[c]));
            }
        }
        for c in 0..2 {
            if f.flags & (1 << c) != 0 {
                Self::mark(&mut self.fault[c], start, start + n);
            }
        }
        PushOutcome { stored: true, lost_adc_frames: gap as u32, full: false }
    }

    /// Spans overlapping [i0, i1).
    pub fn spans_in<'a>(spans: &'a [Span], i0: u64, i1: u64) -> impl Iterator<Item = &'a Span> + 'a {
        let first = spans.partition_point(|s| s.end <= i0);
        spans[first..].iter().take_while(move |s| s.start < i1)
    }

    pub fn stats(&self, c: usize, i0: u64, i1: u64) -> Option<Stats> {
        let i1 = i1.min(self.len());
        if i0 >= i1 {
            return None;
        }
        let n = self.ch[c].query(i0, i1);
        let avg = n.mean()?;
        let duration_s = (i1 - i0) as f64 / SAMPLE_RATE;
        Some(Stats {
            average: avg,
            max: n.max as f64,
            duration_s,
            // Lost samples carry no current: the charge counts recorded samples only.
            charge: n.sum / SAMPLE_RATE,
        })
    }

    /// CSV of samples [i0, i1): `time_us,A_current_A,A_range,A_flags,B_current_A,B_range,B_flags`.
    /// One row per sample; a row is skipped only when both channels have no data (lost data), so
    /// the time column shows the gap. Flags: `S` settling, `C` clipped, `-` none.
    pub fn write_csv<W: Write>(&self, w: &mut W, i0: u64, i1: u64) -> io::Result<()> {
        writeln!(w, "time_us,A_current_A,A_range,A_flags,B_current_A,B_range,B_flags")?;
        let i1 = i1.min(self.len());
        for i in i0..i1 {
            let (pa, pb) = (self.ch[0].get(i), self.ch[1].get(i));
            if !has_data(pa) && !has_data(pb) {
                continue;
            }
            write!(w, "{}", time_us(i))?;
            for (c, p) in [(0usize, pa), (1, pb)] {
                if has_data(p) {
                    let r = unpack_range(p);
                    let a = self.ch[c].cal.amps(r, unpack_code(p));
                    write!(w, ",{:.6e},{},{}", a, ["LOW", "MID", "HIGH"][r as usize], flag_text(p))?;
                } else {
                    write!(w, ",,,")?;
                }
            }
            writeln!(w)?;
        }
        Ok(())
    }
}

fn flag_text(p: u16) -> &'static str {
    match (is_settling(p), is_clipped(p)) {
        (false, false) => "-",
        (true, false) => "S",
        (false, true) => "C",
        (true, true) => "SC",
    }
}

#[derive(Clone, Copy, Debug)]
pub struct Stats {
    pub average: f64,
    pub max: f64,
    pub duration_s: f64,
    /// coulombs
    pub charge: f64,
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::Record;

    fn frame(seq: u16, adc_frames: usize, f: impl FnMut(usize) -> Record) -> Frame {
        Frame { flags: 0, seq, records: (0..adc_frames * 14).map(f).collect() }
    }

    fn rec(code: u16, range: u8) -> Record {
        Record { code: [code, 4095 - code], range: [range, (range + 1) % 3], settling: [false; 2], clipped: [false; 2] }
    }

    fn store() -> Store {
        Store::new([Cal::NOMINAL; 2], 10.0)
    }

    #[test]
    fn time_mapping() {
        assert_eq!(time_us(0), 0);
        assert_eq!(time_us(13), 13 * 69);
        assert_eq!(time_us(14), 1000);
        assert_eq!(time_us(15), 1069);
        for i in [0u64, 1, 13, 14, 27, 28, 1000, 123_457] {
            assert_eq!(index_at(time_us(i) as f64), i);
            assert_eq!(index_at(time_us(i) as f64 + 68.0), i.min(i));
        }
        assert_eq!(index_at(-5.0), 0);
        assert_eq!(index_at(999.0), 13);
    }

    #[test]
    fn lost_data_detection_and_u16_wrap() {
        let mut s = store();
        // frames of 2 ADC frames; the seq runs through the wrap point 65535 -> 0
        let o = s.push_frame(&frame(65532, 2, |i| rec(i as u16, 0)));
        assert!(o.stored);
        assert_eq!(o.lost_adc_frames, 0);
        let o = s.push_frame(&frame(65534, 2, |i| rec(i as u16, 0)));
        assert_eq!(o.lost_adc_frames, 0);
        assert_eq!(s.lost_events, 0);
        assert_eq!(s.len(), 56);
        // next expected is 0 (65534 + 2 mod 65536); 0 is no gap
        let o = s.push_frame(&frame(0, 2, |i| rec(i as u16, 0)));
        assert_eq!(o.lost_adc_frames, 0);
        // expected 2, got 5: 3 ADC frames lost
        let o = s.push_frame(&frame(5, 2, |i| rec(i as u16, 0)));
        assert_eq!(o.lost_adc_frames, 3);
        assert_eq!(s.lost_events, 1);
        assert_eq!(s.lost_adc_frames, 3);
        assert_eq!(s.lost, vec![Span { start: 84, end: 84 + 42 }]);
        assert_eq!(s.len(), 84 + 42 + 28);
        // gap across the wrap: expected 7, got 65535 -> 65528 lost
        let o = s.push_frame(&frame(65535, 2, |i| rec(i as u16, 0)));
        assert_eq!(o.lost_adc_frames, 65528);
        // the lost samples are filled with NO_DATA and carry no current
        assert!(!has_data(s.ch[0].get(100)));
        assert!(s.ch[0].amps_at(100).is_none());
        assert!(s.ch[0].amps_at(0).is_some());
    }

    #[test]
    fn resync_does_not_report_loss() {
        let mut s = store();
        s.push_frame(&frame(10, 1, |i| rec(i as u16, 0)));
        s.resync();
        let o = s.push_frame(&frame(500, 1, |i| rec(i as u16, 0)));
        assert_eq!(o.lost_adc_frames, 0);
        assert_eq!(s.lost_events, 0);
    }

    #[test]
    fn limit_stops_whole_frames() {
        let mut s = Store::new([Cal::NOMINAL; 2], 0.0001); // 0.0001 min = 84 samples
        assert!(s.push_frame(&frame(0, 3, |i| rec(i as u16, 0))).stored); // 42
        assert!(s.push_frame(&frame(3, 3, |i| rec(i as u16, 0))).stored); // 84
        let o = s.push_frame(&frame(6, 1, |i| rec(i as u16, 0)));
        assert!(!o.stored && o.full);
        assert_eq!(s.len(), 84);
    }

    #[test]
    fn query_matches_brute_force() {
        let mut s = store();
        let mut seq = 0u16;
        let mut x = 12345u32;
        for k in 0..400 {
            let n = 1 + (k % 4);
            let fr = frame(seq, n, |_| {
                x = x.wrapping_mul(1664525).wrapping_add(1013904223);
                let r = ((x >> 8) % 3) as u8;
                let mut rc = rec(((x >> 12) & 0xFFF) as u16, r);
                rc.settling[0] = (x >> 3).is_multiple_of(17);
                rc.clipped[1] = (x >> 5).is_multiple_of(19);
                rc
            });
            seq = seq.wrapping_add(n as u16);
            // a lost gap now and then
            if k % 37 == 36 {
                seq = seq.wrapping_add(3);
            }
            s.push_frame(&fr);
        }
        let len = s.len();
        assert!(len > 10_000);
        let mut y = 99u64;
        for _ in 0..3000 {
            y = y.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let a = (y >> 33) % (len + 50);
            y = y.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let b = a + (y >> 33) % 5000;
            for c in 0..2 {
                let q = s.ch[c].query(a, b);
                let r = s.ch[c].node_of(a, b);
                assert_eq!(q.count, r.count, "count {a}..{b}");
                assert_eq!(q.min, r.min, "min {a}..{b}");
                assert_eq!(q.max, r.max, "max {a}..{b}");
                assert_eq!(q.mask, r.mask, "mask {a}..{b}");
                assert!((q.sum - r.sum).abs() <= 1e-9 * (1.0 + r.sum.abs()), "sum {a}..{b}");
            }
        }
        // whole-store query agrees too
        let q = s.ch[0].query(0, len);
        let r = s.ch[0].node_of(0, len);
        assert_eq!((q.count, q.min, q.max), (r.count, r.min, r.max));
    }

    #[test]
    fn statistics_and_charge() {
        let mut s = store();
        // 1000 ADC frames = 1 s. Channel A: LOW range code 1000 -> 100 uA constant.
        for k in 0..10u16 {
            s.push_frame(&frame(k * 100, 100, |_| Record {
                code: [1000, 0],
                range: [0, 2],
                settling: [false; 2],
                clipped: [false; 2],
            }));
        }
        assert_eq!(s.len(), 14_000);
        let st = s.stats(0, 0, 14_000).unwrap();
        assert!((st.average - 100e-6).abs() < 1e-12);
        assert!((st.max - 100e-6).abs() < 1e-9);
        assert!((st.duration_s - 1.0).abs() < 1e-12);
        assert!((st.charge - 100e-6).abs() < 1e-10); // 100 uA for 1 s = 100 uC
        // half a second
        let st = s.stats(0, 0, 7000).unwrap();
        assert!((st.charge - 50e-6).abs() < 1e-10);
        assert!(s.stats(0, 5, 5).is_none());
        // channel B is zero amps
        assert_eq!(s.stats(1, 0, 14_000).unwrap().average, 0.0);
    }

    #[test]
    fn charge_excludes_lost_data() {
        let mut s = store();
        let c = |_| Record { code: [1000, 0], range: [0, 0], settling: [false; 2], clipped: [false; 2] };
        s.push_frame(&frame(0, 10, c));
        s.push_frame(&frame(20, 10, c)); // 10 ADC frames lost
        let st = s.stats(0, 0, s.len()).unwrap();
        assert_eq!(s.len(), 420);
        assert_eq!(s.ch[0].query(0, s.len()).count, 280);
        assert!((st.duration_s - 0.03).abs() < 1e-12);
        assert!((st.charge - 100e-6 * 0.02).abs() < 1e-12);
    }

    #[test]
    fn fault_and_lost_spans() {
        let mut s = store();
        let mut f = frame(0, 2, |i| rec(i as u16, 0));
        f.flags = 1;
        s.push_frame(&f);
        let mut f = frame(2, 1, |i| rec(i as u16, 0));
        f.flags = 1;
        s.push_frame(&f);
        assert_eq!(s.fault[0], vec![Span { start: 0, end: 42 }]);
        assert!(s.fault[1].is_empty());
        assert_eq!(Store::spans_in(&s.fault[0], 10, 11).count(), 1);
        assert_eq!(Store::spans_in(&s.fault[0], 42, 50).count(), 0);
    }

    #[test]
    fn csv_format() {
        let mut s = store();
        let mut f = frame(0, 1, |_| Record { code: [10, 20], range: [0, 1], settling: [false; 2], clipped: [false; 2] });
        f.records[0].settling[0] = true;
        f.records[1].clipped[1] = true;
        s.push_frame(&f);
        s.push_frame(&frame(2, 1, |_| rec(1, 0))); // one ADC frame lost between
        let mut out = Vec::new();
        s.write_csv(&mut out, 0, 14).unwrap();
        let text = String::from_utf8(out).unwrap();
        let lines: Vec<&str> = text.lines().collect();
        assert_eq!(lines[0], "time_us,A_current_A,A_range,A_flags,B_current_A,B_range,B_flags");
        assert_eq!(lines.len(), 15);
        assert_eq!(lines[1], "0,1.000000e-6,LOW,S,1.020000e-4,MID,-");
        assert_eq!(lines[2], "69,1.000000e-6,LOW,-,1.020000e-4,MID,C");
        // rows covering the lost frame are skipped
        let mut out = Vec::new();
        s.write_csv(&mut out, 0, s.len()).unwrap();
        let text = String::from_utf8(out).unwrap();
        assert_eq!(text.lines().count(), 1 + 14 + 14);
        assert!(text.lines().nth(15).unwrap().starts_with("2000,"));
    }
}
