//! Application state and behaviour, independent of Win32: connection, recording, the chart view
//! (zoom, pan, selection) and the mouse interaction rules. The `win` module only translates
//! window messages into calls on `App` and draws what `App` holds.

use crate::device::{self, Msg, Port, Session};
use crate::fmt;
use crate::layout::{Layout, Rect};
use crate::protocol::{Cal, StreamParser, FLAG_FAULT_A, FLAG_FAULT_B};
use crate::store::{self, Node, Stats, Store};
use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::time::{Duration, Instant};

pub const DEFAULT_SPAN_US: f64 = 5_000_000.0;
pub const MIN_SPAN_US: f64 = 700.0;
pub const LOG_FLOOR: f64 = 1e-9;
pub const LOG_CEIL: f64 = 10.0;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Conn {
    Disconnected,
    Connecting,
    Connected,
}

#[derive(Clone, Debug)]
pub struct View {
    pub t0: f64,
    pub span: f64,
    pub y0: f64,
    pub y1: f64,
    pub y_auto: bool,
    pub log: bool,
    pub follow: bool,
}

impl View {
    pub fn new() -> View {
        View { t0: 0.0, span: DEFAULT_SPAN_US, y0: 0.0, y1: 1e-3, y_auto: true, log: false, follow: true }
    }

    pub fn t_to_x(&self, t: f64, plot: &Rect) -> f64 {
        plot.l as f64 + (t - self.t0) / self.span * plot.w() as f64
    }

    pub fn x_to_t(&self, x: f64, plot: &Rect) -> f64 {
        self.t0 + (x - plot.l as f64) / plot.w() as f64 * self.span
    }

    fn yv(&self, v: f64) -> f64 {
        if self.log { v.clamp(LOG_FLOOR, LOG_CEIL).log10() } else { v }
    }

    fn yinv(&self, u: f64) -> f64 {
        if self.log { 10f64.powf(u) } else { u }
    }

    /// Pixel row of a current value.
    pub fn v_to_y(&self, v: f64, plot: &Rect) -> f64 {
        let (a, b) = (self.yv(self.y0), self.yv(self.y1));
        plot.b as f64 - (self.yv(v) - a) / (b - a) * plot.h() as f64
    }

    pub fn y_to_v(&self, y: f64, plot: &Rect) -> f64 {
        let (a, b) = (self.yv(self.y0), self.yv(self.y1));
        self.yinv(a + (plot.b as f64 - y) / plot.h() as f64 * (b - a))
    }

    /// Zoom the time axis by `factor` (< 1 zooms in) keeping `anchor_t` at the same pixel.
    pub fn zoom_time(&mut self, anchor_t: f64, factor: f64, max_span: f64) {
        let new_span = (self.span * factor).clamp(MIN_SPAN_US, max_span.max(MIN_SPAN_US));
        let f = new_span / self.span;
        self.t0 = anchor_t - (anchor_t - self.t0) * f;
        self.span = new_span;
    }

    /// Zoom the current axis around `anchor_v`; switches to a manual range.
    pub fn zoom_y(&mut self, anchor_v: f64, factor: f64) {
        let (a, b) = (self.yv(self.y0), self.yv(self.y1));
        let c = self.yv(anchor_v);
        let mut lo = c - (c - a) * factor;
        let mut hi = c + (b - c) * factor;
        if self.log {
            if hi - lo < 0.3 {
                let m = (hi + lo) / 2.0;
                lo = m - 0.15;
                hi = m + 0.15;
            }
            lo = lo.max(LOG_FLOOR.log10());
            hi = hi.min(LOG_CEIL.log10());
            if hi <= lo {
                return;
            }
        } else if hi - lo < 1e-9 {
            return;
        }
        self.y0 = self.yinv(lo);
        self.y1 = self.yinv(hi);
        self.y_auto = false;
    }

    /// Pan the current axis by `dy` pixels (positive moves the content down).
    pub fn pan_y(&mut self, dy: f64, plot: &Rect) {
        let (a, b) = (self.yv(self.y0), self.yv(self.y1));
        let d = dy / plot.h() as f64 * (b - a);
        let (mut lo, mut hi) = (a + d, b + d);
        if self.log {
            let (flo, fhi) = (LOG_FLOOR.log10(), LOG_CEIL.log10());
            if lo < flo {
                hi += flo - lo;
                lo = flo;
            }
            if hi > fhi {
                lo -= hi - fhi;
                hi = fhi;
            }
        }
        self.y0 = self.yinv(lo);
        self.y1 = self.yinv(hi);
        self.y_auto = false;
    }

    pub fn clamp(&mut self, len_us: f64) {
        self.span = self.span.clamp(MIN_SPAN_US, len_us.max(DEFAULT_SPAN_US));
        self.t0 = self.t0.min(len_us - self.span).max(0.0);
    }
}

#[derive(Clone, Copy, Debug)]
enum Drag {
    None,
    Select { anchor_t: f64, start_x: i32, moved: bool },
    Pan { last_x: i32, last_y: i32 },
    Minimap,
}

pub const RANGE_MODES: [&str; 4] = ["AUTO", "HIGH", "MID", "LOW"];

pub struct App {
    pub store: Store,
    parser: StreamParser,
    session: Option<Session>,
    pub conn: Conn,
    pub conn_label: String,
    pub idn: String,
    pub notice: Option<String>,
    pub view: View,
    pub selection: Option<(f64, f64)>,
    pub show: [bool; 2],
    pub recording: bool,
    pub max_minutes: f64,
    pub port_state: [String; 2],
    pub stream_fault: [bool; 2],
    pub range_mode: [usize; 2],
    pub rate_sps: f64,
    rate_frames: u64,
    rate_since: Instant,
    last_poll: Instant,
    drag: Drag,
    pub dirty_controls: bool,
}

impl App {
    pub fn new(max_minutes: f64) -> App {
        App {
            store: Store::new([Cal::NOMINAL; 2], max_minutes),
            parser: StreamParser::new(),
            session: None,
            conn: Conn::Disconnected,
            conn_label: String::new(),
            idn: String::new(),
            notice: None,
            view: View::new(),
            selection: None,
            show: [true, true],
            recording: false,
            max_minutes,
            port_state: ["-".into(), "-".into()],
            stream_fault: [false; 2],
            range_mode: [0, 0],
            rate_sps: 0.0,
            rate_frames: 0,
            rate_since: Instant::now(),
            last_poll: Instant::now(),
            drag: Drag::None,
            dirty_controls: true,
        }
    }

    // ---- connection -------------------------------------------------------------------------

    fn attach(&mut self, s: Session, label: &str) {
        self.disconnect();
        self.session = Some(s);
        self.conn = Conn::Connecting;
        self.conn_label = label.to_string();
        self.notice = None;
        self.dirty_controls = true;
    }

    pub fn connect_demo(&mut self) {
        self.attach(device::start_demo(), "Demo device");
    }

    pub fn connect_serial(&mut self, ctrl: Box<dyn Port>, stream: Box<dyn Port>, label: &str) {
        self.attach(device::start_serial(ctrl, stream), label);
    }

    pub fn disconnect(&mut self) {
        self.session = None; // dropping the session stops its threads
        if self.conn != Conn::Disconnected {
            self.conn = Conn::Disconnected;
            self.recording = false;
            self.port_state = ["-".into(), "-".into()];
            self.rate_sps = 0.0;
            self.dirty_controls = true;
        }
    }

    pub fn send(&mut self, line: &str) {
        if let Some(s) = &self.session {
            s.send(line);
        }
    }

    /// Port command followed by a state query.
    pub fn port_command(&mut self, port: usize, verb: &str) {
        let n = ["A", "B"][port];
        self.send(&format!("PORT {n} {verb}"));
        self.send(&format!("PORT {n}?"));
    }

    pub fn set_range_mode(&mut self, port: usize, mode: usize) {
        if mode < RANGE_MODES.len() {
            self.range_mode[port] = mode;
            let n = ["A", "B"][port];
            self.send(&format!("RANGE {n} {}", RANGE_MODES[mode]));
        }
    }

    // ---- recording --------------------------------------------------------------------------

    pub fn set_recording(&mut self, on: bool) {
        if on && !self.recording {
            self.store.resync();
        }
        self.recording = on && self.conn == Conn::Connected;
        self.dirty_controls = true;
    }

    pub fn clear(&mut self) {
        let cal = [self.store.ch[0].cal, self.store.ch[1].cal];
        self.store = Store::new(cal, self.max_minutes);
        self.selection = None;
        self.view.t0 = 0.0;
        self.dirty_controls = true;
    }

    pub fn set_max_minutes(&mut self, m: f64) {
        self.max_minutes = m;
        self.store.set_max_minutes(m);
    }

    // ---- periodic work ----------------------------------------------------------------------

    /// Drains the device channel, updates counters and the view. Called by the 30 fps timer.
    pub fn tick(&mut self) {
        let mut msgs = Vec::new();
        if let Some(s) = &self.session {
            while let Ok(m) = s.rx.try_recv() {
                msgs.push(m);
            }
        }
        let mut frames = Vec::new();
        for m in msgs {
            match m {
                Msg::Connected { idn, cal } => {
                    self.idn = idn;
                    self.conn = Conn::Connected;
                    self.store = Store::new(cal, self.max_minutes);
                    self.parser.reset();
                    self.selection = None;
                    self.view.t0 = 0.0;
                    self.recording = true;
                    self.send("PORT A?");
                    self.send("PORT B?");
                    self.dirty_controls = true;
                }
                Msg::Response { cmd, resp } => self.on_response(&cmd, &resp),
                Msg::Stream(bytes) => {
                    if self.conn == Conn::Connected {
                        frames.clear();
                        self.parser.push(&bytes, &mut frames);
                        for f in &frames {
                            self.rate_frames += f.adc_frames() as u64;
                            self.stream_fault = [f.flags & FLAG_FAULT_A != 0, f.flags & FLAG_FAULT_B != 0];
                            if self.recording {
                                let o = self.store.push_frame(f);
                                if o.full {
                                    self.recording = false;
                                    self.notice = Some("Recording limit reached; recording stopped".into());
                                    self.dirty_controls = true;
                                }
                            }
                        }
                    }
                }
                Msg::Closed(e) => {
                    self.notice = e;
                    self.disconnect();
                }
            }
        }
        let now = Instant::now();
        let dt = now.duration_since(self.rate_since);
        if dt >= Duration::from_secs(1) {
            self.rate_sps = self.rate_frames as f64 * 14.0 / dt.as_secs_f64();
            self.rate_frames = 0;
            self.rate_since = now;
        }
        if self.conn == Conn::Connected && now.duration_since(self.last_poll) >= Duration::from_secs(1) {
            self.last_poll = now;
            self.send("PORT A?");
            self.send("PORT B?");
        }
        self.update_view();
    }

    fn on_response(&mut self, cmd: &str, resp: &str) {
        let c = cmd.trim().to_ascii_uppercase();
        if let Some(rest) = resp.strip_prefix("OK ") {
            match c.as_str() {
                "PORT A?" => self.port_state[0] = rest.to_string(),
                "PORT B?" => self.port_state[1] = rest.to_string(),
                _ => {}
            }
            self.dirty_controls = true;
        } else if resp.starts_with("ERR") {
            self.notice = Some(format!("{cmd}: {resp}"));
        }
    }

    pub fn len_us(&self) -> f64 {
        self.store.duration_us()
    }

    pub fn update_view(&mut self) {
        let len = self.len_us();
        if self.view.follow {
            self.view.span = self.view.span.clamp(MIN_SPAN_US, len.max(DEFAULT_SPAN_US));
            self.view.t0 = (len - self.view.span).max(0.0);
        } else {
            self.view.clamp(len);
        }
        if self.view.y_auto {
            self.auto_y();
        }
    }

    fn visible_nodes(&self) -> Option<Node> {
        let (i0, i1) = self.window_range();
        let mut acc = Node::EMPTY;
        for c in 0..2 {
            if self.show[c] {
                acc.merge(&self.store.ch[c].query(i0, i1));
            }
        }
        (acc.count > 0).then_some(acc)
    }

    fn auto_y(&mut self) {
        let Some(n) = self.visible_nodes() else {
            return;
        };
        let (mn, mx) = (n.min as f64, n.max as f64);
        if self.view.log {
            let lo = mn.max(1e-8).log10().floor();
            let hi = mx.max(1e-7).log10().ceil();
            let lo = if hi - lo < 2.0 { hi - 2.0 } else { lo };
            self.view.y0 = 10f64.powf(lo);
            self.view.y1 = 10f64.powf(hi);
        } else {
            let lo = mn.min(0.0);
            let hi = mx.max(lo + 1e-7);
            let step = fmt::nice_step(hi - lo, 5.0);
            self.view.y1 = (hi / step).ceil() * step;
            self.view.y0 = if lo < 0.0 { (lo / step).floor() * step } else { 0.0 };
        }
    }

    pub fn set_log(&mut self, log: bool) {
        self.view.log = log;
        self.view.y_auto = true;
        self.update_view();
    }

    pub fn set_follow(&mut self, follow: bool) {
        self.view.follow = follow;
        self.dirty_controls = true;
        self.update_view();
    }

    // ---- ranges and statistics ----------------------------------------------------------------

    /// Sample index range [i0, i1) of the visible window.
    pub fn window_range(&self) -> (u64, u64) {
        let i0 = store::index_at(self.view.t0);
        let i1 = (store::index_at(self.view.t0 + self.view.span) + 1).min(self.store.len());
        (i0.min(i1), i1)
    }

    pub fn selection_range(&self) -> Option<(u64, u64)> {
        let (a, b) = self.selection?;
        let i0 = store::index_at(a);
        let i1 = (store::index_at(b) + 1).min(self.store.len());
        (i0 < i1).then_some((i0, i1))
    }

    pub fn window_stats(&self, c: usize) -> Option<Stats> {
        let (i0, i1) = self.window_range();
        self.store.stats(c, i0, i1)
    }

    pub fn selection_stats(&self, c: usize) -> Option<Stats> {
        let (i0, i1) = self.selection_range()?;
        self.store.stats(c, i0, i1)
    }

    /// Selects the part of the visible window between two fractions of its width (used by the
    /// command-line screenshot, which has no mouse).
    pub fn select_fraction(&mut self, from: f64, to: f64) {
        let (t0, span) = (self.view.t0, self.view.span);
        self.selection = Some((t0 + span * from, t0 + span * to));
    }

    // ---- export -----------------------------------------------------------------------------

    /// Writes the CSV and returns the number of samples covered.
    pub fn export_csv(&self, path: &str, selection_only: bool) -> io::Result<u64> {
        let (i0, i1) = if selection_only {
            self.selection_range().ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "no selection"))?
        } else {
            (0, self.store.len())
        };
        if i0 >= i1 {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "nothing recorded"));
        }
        let mut w = BufWriter::new(File::create(path)?);
        self.store.write_csv(&mut w, i0, i1)?;
        w.flush()?;
        Ok(i1 - i0)
    }

    // ---- status ---------------------------------------------------------------------------

    pub fn status_left(&self) -> String {
        let c = match self.conn {
            Conn::Disconnected => "Disconnected".to_string(),
            Conn::Connecting => format!("Connecting to {}...", self.conn_label),
            Conn::Connected => format!("Connected: {}", self.conn_label),
        };
        match &self.notice {
            Some(e) => format!("{c}   |   {e}"),
            None => c,
        }
    }

    pub fn status_right(&self) -> String {
        format!(
            "{:.1} kSPS received   |   Lost: {} ({} ms)   |   CRC errors: {}   |   Resyncs: {}",
            self.rate_sps / 1000.0,
            self.store.lost_events,
            self.store.lost_adc_frames,
            self.parser.stats.crc_errors,
            self.parser.stats.sync_losses
        )
    }

    pub fn port_text(&self, p: usize) -> String {
        if self.conn != Conn::Connected {
            "-".into()
        } else if self.stream_fault[p] && !self.port_state[p].starts_with("FAULT") {
            "FAULT".into()
        } else {
            self.port_state[p].clone()
        }
    }

    pub fn visible_channels(&self) -> Vec<usize> {
        (0..2).filter(|&c| self.show[c]).collect()
    }

    // ---- mouse ------------------------------------------------------------------------------

    fn minimap_to_t(&self, x: i32, lay: &Layout) -> f64 {
        let f = (x - lay.minimap.l) as f64 / lay.minimap.w().max(1) as f64;
        f.clamp(0.0, 1.0) * self.len_us()
    }

    fn center_on(&mut self, t: f64) {
        self.view.follow = false;
        self.view.t0 = t - self.view.span / 2.0;
        self.view.clamp(self.len_us());
        self.dirty_controls = true;
    }

    /// Returns true when the window should capture the mouse.
    pub fn mouse_down(&mut self, lay: &Layout, left: bool, x: i32, y: i32) -> bool {
        if lay.minimap.contains(x, y) && left {
            self.drag = Drag::Minimap;
            let t = self.minimap_to_t(x, lay);
            self.center_on(t);
            return true;
        }
        if !lay.plot.contains(x, y) {
            return false;
        }
        let t = self.view.x_to_t(x as f64, &lay.plot);
        if left {
            self.drag = Drag::Select { anchor_t: t, start_x: x, moved: false };
        } else {
            self.drag = Drag::Pan { last_x: x, last_y: y };
        }
        true
    }

    pub fn mouse_move(&mut self, lay: &Layout, x: i32, y: i32) {
        match self.drag {
            Drag::None => {}
            Drag::Minimap => {
                let t = self.minimap_to_t(x, lay);
                self.center_on(t);
            }
            Drag::Select { anchor_t, start_x, moved } => {
                let moved = moved || (x - start_x).abs() >= 3;
                if moved {
                    let xx = (x as f64).clamp(lay.plot.l as f64, lay.plot.r as f64);
                    let t = self.view.x_to_t(xx, &lay.plot).clamp(0.0, self.len_us());
                    let a = anchor_t.clamp(0.0, self.len_us());
                    self.selection = Some((a.min(t), a.max(t)));
                }
                self.drag = Drag::Select { anchor_t, start_x, moved };
            }
            Drag::Pan { last_x, last_y } => {
                let dt = -(x - last_x) as f64 / lay.plot.w() as f64 * self.view.span;
                if dt != 0.0 || y != last_y {
                    self.view.follow = false;
                    self.dirty_controls = true;
                    self.view.t0 += dt;
                    self.view.clamp(self.len_us());
                    if !self.view.y_auto {
                        self.view.pan_y((y - last_y) as f64, &lay.plot);
                    }
                }
                self.drag = Drag::Pan { last_x: x, last_y: y };
            }
        }
    }

    pub fn mouse_up(&mut self) {
        if let Drag::Select { moved: false, .. } = self.drag {
            self.selection = None; // a click without a drag clears the selection
        }
        self.drag = Drag::None;
    }

    /// `notches` > 0 is wheel up (zoom in).
    pub fn wheel(&mut self, lay: &Layout, x: i32, y: i32, notches: f64, ctrl: bool) {
        if !lay.plot.contains(x, y) {
            return;
        }
        let factor = 0.8f64.powf(notches);
        if ctrl {
            let v = self.view.y_to_v(y as f64, &lay.plot);
            self.view.zoom_y(v, factor);
        } else {
            let len = self.len_us();
            let anchor = if self.view.follow { self.view.t0 + self.view.span } else { self.view.x_to_t(x as f64, &lay.plot) };
            self.view.zoom_time(anchor, factor, len.max(DEFAULT_SPAN_US));
        }
        self.update_view();
    }

    pub fn double_click(&mut self, lay: &Layout, x: i32, y: i32) {
        if lay.plot.contains(x, y) || lay.minimap.contains(x, y) {
            self.view.span = DEFAULT_SPAN_US;
            self.view.y_auto = true;
            self.view.follow = true;
            self.selection = None;
            self.dirty_controls = true;
            self.update_view();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::protocol::{Frame, Record};

    fn plot() -> Rect {
        Rect::new(100, 50, 1100, 450)
    }

    fn app_with(seconds: u32) -> App {
        let mut a = App::new(10.0);
        a.conn = Conn::Connected;
        a.recording = true;
        for k in 0..seconds {
            a.store.push_frame(&Frame {
                flags: 0,
                seq: (k * 1000) as u16,
                records: (0..14_000)
                    .map(|i| Record {
                        code: [(i % 100) as u16 + 10, 5],
                        range: [0, 1],
                        settling: [false; 2],
                        clipped: [false; 2],
                    })
                    .collect(),
            });
        }
        a
    }

    #[test]
    fn time_zoom_keeps_anchor_pixel() {
        let mut v = View::new();
        v.t0 = 2_000_000.0;
        let p = plot();
        let x = 400.0;
        let t = v.x_to_t(x, &p);
        v.zoom_time(t, 0.5, 60e6);
        assert!((v.x_to_t(x, &p) - t).abs() < 1e-6);
        assert!((v.span - 2_500_000.0).abs() < 1e-6);
        v.zoom_time(t, 1e-9, 60e6);
        assert_eq!(v.span, MIN_SPAN_US);
    }

    #[test]
    fn y_mapping_roundtrip_linear_and_log() {
        let p = plot();
        let mut v = View::new();
        v.y0 = 0.0;
        v.y1 = 0.1;
        assert!((v.v_to_y(0.05, &p) - 250.0).abs() < 1e-9);
        assert!((v.y_to_v(v.v_to_y(0.033, &p), &p) - 0.033).abs() < 1e-12);
        v.log = true;
        v.y0 = 1e-6;
        v.y1 = 1.0;
        assert!((v.v_to_y(1e-3, &p) - 250.0).abs() < 1e-9);
        assert!((v.y_to_v(v.v_to_y(2e-4, &p), &p) / 2e-4 - 1.0).abs() < 1e-9);
        let before = v.y_to_v(100.0, &p);
        v.zoom_y(before, 0.5);
        assert!((v.y_to_v(100.0, &p) / before - 1.0).abs() < 1e-9);
        assert!(!v.y_auto);
    }

    #[test]
    fn follow_keeps_right_edge_on_newest() {
        let mut a = app_with(8);
        a.update_view();
        assert!((a.view.t0 + a.view.span - a.len_us()).abs() < 1.0);
        // panning leaves follow mode and the window stays put when data grows
        let lay = Layout::compute(1280, 800, 1.0, 2);
        a.mouse_down(&lay, false, lay.plot.l + 100, lay.plot.t + 10);
        a.mouse_move(&lay, lay.plot.l + 300, lay.plot.t + 10);
        a.mouse_up();
        assert!(!a.view.follow);
        let t0 = a.view.t0;
        assert!(t0 < 8e6 - a.view.span);
        a.update_view();
        assert_eq!(a.view.t0, t0);
    }

    #[test]
    fn selection_by_drag_and_clear_by_click() {
        let mut a = app_with(8);
        a.update_view();
        let lay = Layout::compute(1280, 800, 1.0, 2);
        let y = lay.plot.t + 20;
        a.mouse_down(&lay, true, lay.plot.l + 100, y);
        a.mouse_move(&lay, lay.plot.l + 300, y);
        a.mouse_up();
        let (s, e) = a.selection.unwrap();
        assert!(e > s);
        assert!(((e - s) / a.view.span - 200.0 / lay.plot.w() as f64).abs() < 1e-9);
        assert!(a.selection_stats(0).is_some());
        a.mouse_down(&lay, true, lay.plot.l + 50, y);
        a.mouse_up();
        assert!(a.selection.is_none());
    }

    #[test]
    fn minimap_click_moves_window_and_double_click_resets() {
        let mut a = app_with(20);
        a.update_view();
        let lay = Layout::compute(1280, 800, 1.0, 2);
        let mid = (lay.minimap.l + lay.minimap.r) / 2;
        a.mouse_down(&lay, true, mid, lay.minimap.t + 5);
        a.mouse_up();
        assert!(!a.view.follow);
        assert!((a.view.t0 + a.view.span / 2.0 - a.len_us() / 2.0).abs() < 1.0);
        a.double_click(&lay, lay.plot.l + 5, lay.plot.t + 5);
        assert!(a.view.follow && a.view.y_auto && a.view.span == DEFAULT_SPAN_US);
    }

    #[test]
    fn window_stats_cover_the_window() {
        let a = {
            let mut a = app_with(8);
            a.update_view();
            a
        };
        let st = a.window_stats(0).unwrap();
        assert!((st.duration_s - 5.0).abs() < 0.01);
        assert!(st.average > 0.0);
        // channel B has constant code 5 on MID: 25.5 uA
        assert!((a.window_stats(1).unwrap().average - 5.0 * 5.1e-6).abs() < 1e-9);
    }

    #[test]
    fn export_selection_requires_selection() {
        let a = app_with(2);
        let dir = std::env::temp_dir().join("usb-power-profiler-test.csv");
        assert!(a.export_csv(dir.to_str().unwrap(), true).is_err());
        let n = a.export_csv(dir.to_str().unwrap(), false).unwrap();
        assert_eq!(n, 28_000);
        let text = std::fs::read_to_string(&dir).unwrap();
        assert_eq!(text.lines().count(), 28_001);
        std::fs::remove_file(&dir).unwrap();
    }

    #[test]
    fn port_command_state_text() {
        let mut a = App::new(1.0);
        a.conn = Conn::Connected;
        a.on_response("PORT A?", "OK FAULT:OVERCURRENT");
        assert_eq!(a.port_text(0), "FAULT:OVERCURRENT");
        a.on_response("port b?", "OK ON");
        assert_eq!(a.port_text(1), "ON");
        a.stream_fault[1] = true;
        assert_eq!(a.port_text(1), "FAULT");
        a.on_response("RANGE A MID", "ERR 02 BAD ARGUMENT");
        assert!(a.notice.is_some());
    }
}
