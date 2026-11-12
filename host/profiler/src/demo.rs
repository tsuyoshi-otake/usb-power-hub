//! Demo device: answers the control protocol of section 4.1 and produces the byte stream of
//! section 4.2 (through `protocol::encode_frame`, so the host parser is exercised) for two
//! imaginary DUTs. The ranges switch the way the hardware would.

use crate::protocol::{
    encode_frame, Cal, Record, RANGE_HIGH, SAMPLES_PER_FRAME,
};
use crate::store::{ADC_FRAME_US, SAMPLE_PERIOD_US};

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Mode {
    Auto,
    Hold(u8),
}

struct Port {
    on: bool,
    /// While set (milliseconds of device time), the port is cycling and stays off.
    cycle_until_ms: Option<u64>,
    mode: Mode,
    range: u8,
    below: u32,
    settle_next: bool,
}

impl Port {
    fn new() -> Self {
        Port { on: true, cycle_until_ms: None, mode: Mode::Auto, range: 0, below: 0, settle_next: false }
    }
    fn min_range(&self) -> u8 {
        match self.mode {
            Mode::Auto => 0,
            Mode::Hold(r) => r,
        }
    }
}

pub struct DemoDevice {
    rng: u64,
    next_adc_frame: u64,
    ports: [Port; 2],
    pub stream_on: bool,
    cal: Cal,
    /// Device time (ms) of the next injected lost frame / corrupted frame.
    next_lost_ms: u64,
    next_crc_ms: u64,
}

pub const INJECT_PERIOD_MS: u64 = 30_000;
pub const FIRST_LOST_MS: u64 = 4_000;
pub const FIRST_CRC_MS: u64 = 6_000;

impl DemoDevice {
    pub fn new() -> Self {
        DemoDevice {
            rng: 0x2545_F491_4F6C_DD1D,
            next_adc_frame: 0,
            ports: [Port::new(), Port::new()],
            stream_on: false,
            cal: Cal::NOMINAL,
            next_lost_ms: FIRST_LOST_MS,
            next_crc_ms: FIRST_CRC_MS,
        }
    }

    pub fn cal(&self) -> Cal {
        self.cal
    }

    fn rand(&mut self) -> f64 {
        // xorshift64*, uniform in [0, 1)
        self.rng ^= self.rng >> 12;
        self.rng ^= self.rng << 25;
        self.rng ^= self.rng >> 27;
        (self.rng.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
    }

    /// Roughly Gaussian, unit variance (sum of 4 uniforms).
    fn noise(&mut self) -> f64 {
        let s: f64 = (0..4).map(|_| self.rand()).sum();
        (s - 2.0) * 1.732
    }

    fn port_index(tok: &str) -> Option<usize> {
        match tok {
            "A" => Some(0),
            "B" => Some(1),
            _ => None,
        }
    }

    fn state_text(&self, p: usize) -> &'static str {
        if self.ports[p].on { "ON" } else { "OFF" }
    }

    /// Executes one control line and returns the single response line.
    pub fn command(&mut self, line: &str) -> String {
        let up = line.trim().to_ascii_uppercase();
        let t: Vec<&str> = up.split_whitespace().collect();
        let now_ms = self.next_adc_frame;
        match t.as_slice() {
            ["*IDN?"] => "OK USB-POWER-HUB,0.4,DEMO0001,demo-0.1".into(),
            ["STATUS?"] => format!("OK J4=DEFAULT VJ4=5000 A={} B={} RESET=POR", self.state_text(0), self.state_text(1)),
            ["PORT", p, "ON"] => match Self::port_index(p) {
                Some(i) => {
                    self.ports[i].on = true;
                    self.ports[i].cycle_until_ms = None;
                    "OK".into()
                }
                None => "ERR 02 BAD ARGUMENT".into(),
            },
            ["PORT", p, "OFF"] => match Self::port_index(p) {
                Some(i) => {
                    self.ports[i].on = false;
                    self.ports[i].cycle_until_ms = None;
                    "OK".into()
                }
                None => "ERR 02 BAD ARGUMENT".into(),
            },
            ["PORT", p, "CYCLE", rest @ ..] => {
                let ms = match rest {
                    [] => Some(500),
                    [v] => v.parse::<u64>().ok().filter(|v| (1..=10_000).contains(v)),
                    _ => None,
                };
                match (Self::port_index(p), ms) {
                    (Some(i), Some(ms)) => {
                        // Real hardware answers after the port is ON again; the demo answers at once
                        // and keeps the port off for `ms` of device time.
                        self.ports[i].on = false;
                        self.ports[i].cycle_until_ms = Some(now_ms + ms);
                        "OK".into()
                    }
                    _ => "ERR 02 BAD ARGUMENT".into(),
                }
            }
            ["PORT", p] if p.ends_with('?') => match Self::port_index(&p[..p.len() - 1]) {
                Some(i) => format!("OK {}", self.state_text(i)),
                None => "ERR 02 BAD ARGUMENT".into(),
            },
            ["ZERO", p] => match Self::port_index(p) {
                Some(i) if self.ports[i].on => "OK 0,0,0".into(),
                Some(_) => "ERR 05 NOT ALLOWED: PORT OFF".into(),
                None => "ERR 02 BAD ARGUMENT".into(),
            },
            ["CAL?", p] => match Self::port_index(p) {
                Some(_) => self.cal.to_response(),
                None => "ERR 02 BAD ARGUMENT".into(),
            },
            ["RANGE", p, m] => match (Self::port_index(p), *m) {
                (Some(i), "AUTO") => {
                    self.ports[i].mode = Mode::Auto;
                    "OK".into()
                }
                (Some(i), "LOW") => {
                    self.ports[i].mode = Mode::Hold(0);
                    "OK".into()
                }
                (Some(i), "MID") => {
                    self.ports[i].mode = Mode::Hold(1);
                    "OK".into()
                }
                (Some(i), "HIGH") => {
                    self.ports[i].mode = Mode::Hold(2);
                    "OK".into()
                }
                _ => "ERR 02 BAD ARGUMENT".into(),
            },
            ["STREAM", "ON"] => {
                self.stream_on = true;
                self.next_adc_frame = 0;
                self.next_lost_ms = FIRST_LOST_MS;
                self.next_crc_ms = FIRST_CRC_MS;
                "OK".into()
            }
            ["STREAM", "OFF"] => {
                self.stream_on = false;
                "OK".into()
            }
            _ if up.len() > 80 => "ERR 08 LINE TOO LONG".into(),
            _ => "ERR 01 UNKNOWN COMMAND".into(),
        }
    }

    /// True current of the DUT behind port `p` at `t_us` (zero when the port is off).
    fn dut_current(&mut self, p: usize, t_us: u64) -> f64 {
        if !self.ports[p].on {
            return 0.0;
        }
        let n = self.noise();
        if p == 0 {
            // radio-like: 3 uA sleep, 8 mA for 2 ms every 100 ms, 120 mA spike every 2 s
            if t_us % 2_000_000 >= 50_000 && t_us % 2_000_000 < 53_000 {
                120e-3 * (1.0 + 0.01 * n)
            } else if t_us % 100_000 < 2_000 {
                8e-3 * (1.0 + 0.02 * n)
            } else {
                3e-6 + 0.05e-6 * n
            }
        } else {
            // about 45 mA with ripple, plus a 300 mA step for 50 ms every 3 s
            let ripple = 0.8e-3 * (2.0 * std::f64::consts::PI * 1000.0 * t_us as f64 * 1e-6).sin();
            let base = if t_us % 3_000_000 >= 1_000_000 && t_us % 3_000_000 < 1_050_000 { 300e-3 } else { 45e-3 };
            base + ripple + 0.15e-3 * n
        }
    }

    fn sample(&mut self, p: usize, t_us: u64) -> (u16, u8, bool, bool) {
        let cal = self.cal;
        let i_true = self.dut_current(p, t_us);
        let port = &mut self.ports[p];
        if port.range < port.min_range() {
            port.range = port.min_range();
            port.settle_next = true;
        }
        let r = port.range;
        let settling = std::mem::take(&mut port.settle_next);
        let code = (i_true / (cal.gain_na[r as usize] * 1e-9)).round().clamp(0.0, 4095.0) as u16;
        let mut clipped = false;
        if code >= 4095 && r < RANGE_HIGH {
            // over-range: the comparator loop switches to the next range at once
            clipped = true;
            port.range += 1;
            port.settle_next = true;
            port.below = 0;
        } else if r > port.min_range() && i_true < 0.8 * cal.top(r - 1) {
            port.below += 1;
            if port.below >= SAMPLES_PER_FRAME as u32 {
                // 14 samples are 1 ms: firmware steps down after 1 ms below 0.8 x the lower top
                port.range -= 1;
                port.settle_next = true;
                port.below = 0;
            }
        } else {
            port.below = 0;
        }
        (code, r, settling, clipped)
    }

    /// Produces `adc_frames` 1 ms ADC frames as one stream frame (possibly empty when a lost
    /// frame is injected, possibly with one byte corrupted when a CRC error is injected).
    pub fn generate(&mut self, adc_frames: u32) -> Vec<u8> {
        let first = self.next_adc_frame;
        let seq = first as u16;
        let mut recs = Vec::with_capacity(adc_frames as usize * SAMPLES_PER_FRAME);
        for f in 0..adc_frames as u64 {
            let frame_ms = first + f;
            for p in 0..2 {
                if let Some(until) = self.ports[p].cycle_until_ms {
                    if frame_ms >= until {
                        self.ports[p].cycle_until_ms = None;
                        self.ports[p].on = true;
                    }
                }
            }
            for k in 0..SAMPLES_PER_FRAME as u64 {
                let t = frame_ms * ADC_FRAME_US + k * SAMPLE_PERIOD_US;
                let (ca, ra, sa, xa) = self.sample(0, t);
                let (cb, rb, sb, xb) = self.sample(1, t);
                recs.push(Record { code: [ca, cb], range: [ra, rb], settling: [sa, sb], clipped: [xa, xb] });
            }
        }
        self.next_adc_frame += adc_frames as u64;
        if first >= self.next_lost_ms {
            self.next_lost_ms += INJECT_PERIOD_MS;
            return Vec::new();
        }
        let mut bytes = encode_frame(0, seq, &recs);
        if first >= self.next_crc_ms {
            self.next_crc_ms += INJECT_PERIOD_MS;
            bytes[40] ^= 0x10;
        }
        bytes
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::StreamParser;
    use crate::store::{Store, unpack_range, is_settling, is_clipped};

    #[test]
    fn commands() {
        let mut d = DemoDevice::new();
        assert!(d.command("*idn?").starts_with("OK USB-POWER-HUB,"));
        assert_eq!(d.command("PORT A OFF"), "OK");
        assert_eq!(d.command("port a?"), "OK OFF");
        assert_eq!(d.command("ZERO A"), "ERR 05 NOT ALLOWED: PORT OFF");
        assert_eq!(d.command("PORT C ON"), "ERR 02 BAD ARGUMENT");
        assert_eq!(d.command("RANGE A MID"), "OK");
        assert_eq!(d.command("RANGE A FAST"), "ERR 02 BAD ARGUMENT");
        assert_eq!(d.command("FOO"), "ERR 01 UNKNOWN COMMAND");
        assert_eq!(crate::protocol::Cal::parse(&d.command("CAL? B")), Some(Cal::NOMINAL));
    }

    #[test]
    fn stream_goes_through_parser_with_injected_faults() {
        let mut d = DemoDevice::new();
        d.command("STREAM ON");
        let mut p = StreamParser::new();
        let mut frames = Vec::new();
        for _ in 0..800 {
            let b = d.generate(10);
            p.push(&b, &mut frames);
        }
        // 8 s of data: one lost frame at 4 s, one corrupted frame at 6 s
        assert_eq!(p.stats.crc_errors, 1);
        assert_eq!(frames.len(), 800 - 2);
        let mut s = Store::new([Cal::NOMINAL; 2], 10.0);
        for f in &frames {
            s.push_frame(f);
        }
        assert_eq!(s.lost_events, 2); // the lost frame and the dropped corrupt one
        assert_eq!(s.lost_adc_frames, 20);
    }

    #[test]
    fn ranges_follow_the_dut() {
        let mut d = DemoDevice::new();
        d.command("STREAM ON");
        let mut p = StreamParser::new();
        let mut frames = Vec::new();
        for _ in 0..200 {
            let b = d.generate(10);
            p.push(&b, &mut frames);
        }
        let mut s = Store::new([Cal::NOMINAL; 2], 10.0);
        for f in &frames {
            s.push_frame(f);
        }
        let mut seen = [[false; 3]; 2];
        let (mut settle, mut clip) = (0, 0);
        for i in 0..s.len() {
            for (ch, row) in s.ch.iter().zip(seen.iter_mut()) {
                let v = ch.get(i);
                if crate::store::has_data(v) {
                    row[unpack_range(v) as usize] = true;
                }
            }
            let v = s.ch[0].get(i);
            settle += is_settling(v) as u32;
            clip += is_clipped(v) as u32;
        }
        assert!(seen[0][0] && seen[0][1] && seen[0][2], "port A uses all ranges: {seen:?}");
        assert!(seen[1][2]);
        assert!(settle > 0 && clip > 0);
        // sleep current of A is ~3 uA
        let n = s.ch[0].query(20_000, 20_000 + 1400);
        assert!(n.min < 5e-6);
    }

    #[test]
    fn cycle_turns_the_port_back_on() {
        let mut d = DemoDevice::new();
        d.command("STREAM ON");
        assert_eq!(d.command("PORT B CYCLE 20"), "OK");
        assert_eq!(d.command("PORT B?"), "OK OFF");
        d.generate(10);
        assert_eq!(d.command("PORT B?"), "OK OFF");
        d.generate(20);
        assert_eq!(d.command("PORT B?"), "OK ON");
    }
}
