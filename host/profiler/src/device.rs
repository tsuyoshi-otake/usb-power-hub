//! Device session: threads that talk to the demo device or to the two CDC-ACM ports and hand
//! `Msg` values to the UI thread through a channel.
//!
//! * control port (COMn): one line out, one line back (section 4.1);
//! * stream port (COMn+1): raw bytes, parsed on the UI thread.

use crate::demo::DemoDevice;
use crate::protocol::Cal;
use std::io::{self, Read, Write};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{channel, Receiver, RecvTimeoutError, Sender};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

/// A byte-oriented serial port whose `read` returns `Ok(0)` when nothing arrived within its
/// timeout (the Windows implementation sets a 100 ms read timeout).
pub trait Port: Read + Write + Send {}
impl<T: Read + Write + Send> Port for T {}

pub enum Cmd {
    Line(String),
}

pub enum Msg {
    /// Handshake finished: identity and calibration of both channels.
    Connected { idn: String, cal: [Cal; 2] },
    Response { cmd: String, resp: String },
    Stream(Vec<u8>),
    Closed(Option<String>),
}

pub struct Session {
    tx: Sender<Cmd>,
    pub rx: Receiver<Msg>,
    stop: Arc<AtomicBool>,
}

impl Session {
    pub fn send(&self, line: &str) {
        let _ = self.tx.send(Cmd::Line(line.to_string()));
    }
}

impl Drop for Session {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
    }
}

const CONTROL_TIMEOUT: Duration = Duration::from_millis(2500);

pub fn start_demo() -> Session {
    let (tx, cmd_rx) = channel::<Cmd>();
    let (msg_tx, rx) = channel::<Msg>();
    let stop = Arc::new(AtomicBool::new(false));
    let stop2 = stop.clone();
    thread::Builder::new()
        .name("demo-device".into())
        .spawn(move || {
            let mut dev = DemoDevice::new();
            let idn = dev.command("*IDN?");
            let cal = [dev.cal(), dev.cal()];
            let _ = msg_tx.send(Msg::Connected { idn: idn.trim_start_matches("OK ").to_string(), cal });
            dev.command("STREAM ON");
            let t0 = Instant::now();
            let mut produced_ms = 0u64;
            while !stop2.load(Ordering::Relaxed) {
                while let Ok(Cmd::Line(l)) = cmd_rx.try_recv() {
                    let resp = dev.command(&l);
                    if l.trim().eq_ignore_ascii_case("STREAM ON") {
                        produced_ms = t0.elapsed().as_millis() as u64;
                    }
                    let _ = msg_tx.send(Msg::Response { cmd: l, resp });
                }
                let target = t0.elapsed().as_millis() as u64;
                if dev.stream_on && target >= produced_ms + 10 {
                    // frames of 10 ADC frames (n = 140), as many as real time requires
                    while produced_ms + 10 <= target {
                        let bytes = dev.generate(10);
                        produced_ms += 10;
                        if !bytes.is_empty() && msg_tx.send(Msg::Stream(bytes)).is_err() {
                            return;
                        }
                    }
                } else if !dev.stream_on {
                    produced_ms = target;
                }
                thread::sleep(Duration::from_millis(4));
            }
        })
        .expect("spawn demo thread");
    Session { tx, rx, stop }
}

/// Reads one response line (without the terminator), `Ok(None)` on timeout.
fn read_line(port: &mut dyn Port, stop: &AtomicBool, timeout: Duration) -> io::Result<Option<String>> {
    let deadline = Instant::now() + timeout;
    let mut line = Vec::new();
    let mut buf = [0u8; 64];
    loop {
        if stop.load(Ordering::Relaxed) || Instant::now() > deadline {
            return Ok(None);
        }
        let n = port.read(&mut buf)?;
        for &b in &buf[..n] {
            if b == b'\n' || b == b'\r' {
                if !line.is_empty() {
                    return Ok(Some(String::from_utf8_lossy(&line).into_owned()));
                }
            } else {
                line.push(b);
            }
        }
    }
}

fn transact(port: &mut dyn Port, stop: &AtomicBool, line: &str) -> io::Result<String> {
    port.write_all(line.as_bytes())?;
    port.write_all(b"\n")?;
    port.flush()?;
    read_line(port, stop, CONTROL_TIMEOUT)?
        .ok_or_else(|| io::Error::new(io::ErrorKind::TimedOut, format!("no response to {line}")))
}

fn handshake(ctrl: &mut dyn Port, stop: &AtomicBool) -> Result<(String, [Cal; 2]), String> {
    let e = |e: io::Error| e.to_string();
    let idn = transact(ctrl, stop, "*IDN?").map_err(e)?;
    let idn = idn.strip_prefix("OK ").ok_or_else(|| format!("unexpected *IDN? response: {idn}"))?.to_string();
    let mut cal = [Cal::NOMINAL; 2];
    for (i, name) in ["A", "B"].iter().enumerate() {
        let r = transact(ctrl, stop, &format!("CAL? {name}")).map_err(e)?;
        cal[i] = Cal::parse(&r).ok_or_else(|| format!("bad CAL? {name} response: {r}"))?;
    }
    Ok((idn, cal))
}

/// Starts the control and stream threads on two opened ports. Not exercised by a unit test: it
/// needs a real device (see the README of this directory).
pub fn start_serial(mut ctrl: Box<dyn Port>, mut stream: Box<dyn Port>) -> Session {
    let (tx, cmd_rx) = channel::<Cmd>();
    let (msg_tx, rx) = channel::<Msg>();
    let stop = Arc::new(AtomicBool::new(false));

    let (m, s) = (msg_tx.clone(), stop.clone());
    thread::Builder::new()
        .name("serial-stream".into())
        .spawn(move || {
            let mut buf = vec![0u8; 8192];
            while !s.load(Ordering::Relaxed) {
                match stream.read(&mut buf) {
                    Ok(0) => {}
                    Ok(n) => {
                        if m.send(Msg::Stream(buf[..n].to_vec())).is_err() {
                            return;
                        }
                    }
                    Err(e) => {
                        let _ = m.send(Msg::Closed(Some(format!("stream port: {e}"))));
                        return;
                    }
                }
            }
        })
        .expect("spawn stream thread");

    let (m, s) = (msg_tx, stop.clone());
    thread::Builder::new()
        .name("serial-control".into())
        .spawn(move || {
            match handshake(ctrl.as_mut(), &s) {
                Ok((idn, cal)) => {
                    let _ = m.send(Msg::Connected { idn, cal });
                }
                Err(e) => {
                    let _ = m.send(Msg::Closed(Some(e)));
                    return;
                }
            }
            if let Err(e) = transact(ctrl.as_mut(), &s, "STREAM ON") {
                let _ = m.send(Msg::Closed(Some(e.to_string())));
                return;
            }
            while !s.load(Ordering::Relaxed) {
                match cmd_rx.recv_timeout(Duration::from_millis(50)) {
                    Ok(Cmd::Line(l)) => match transact(ctrl.as_mut(), &s, &l) {
                        Ok(resp) => {
                            let _ = m.send(Msg::Response { cmd: l, resp });
                        }
                        Err(e) => {
                            let _ = m.send(Msg::Closed(Some(e.to_string())));
                            return;
                        }
                    },
                    Err(RecvTimeoutError::Timeout) => {}
                    Err(RecvTimeoutError::Disconnected) => return,
                }
            }
            let _ = transact(ctrl.as_mut(), &AtomicBool::new(false), "STREAM OFF");
        })
        .expect("spawn control thread");
    Session { tx, rx, stop }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::VecDeque;

    /// Scripted control port: answers each written line from a table.
    struct Script {
        out: VecDeque<u8>,
        pending: Vec<u8>,
        table: Vec<(&'static str, &'static str)>,
    }
    impl Read for Script {
        fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
            let n = buf.len().min(self.out.len()).min(5);
            for b in buf.iter_mut().take(n) {
                *b = self.out.pop_front().unwrap();
            }
            if n == 0 {
                std::thread::sleep(Duration::from_millis(1));
            }
            Ok(n)
        }
    }
    impl Write for Script {
        fn write(&mut self, b: &[u8]) -> io::Result<usize> {
            for &c in b {
                if c == b'\n' {
                    let l = String::from_utf8(std::mem::take(&mut self.pending)).unwrap();
                    if let Some((_, r)) = self.table.iter().find(|(k, _)| *k == l) {
                        self.out.extend(r.bytes());
                        self.out.extend(b"\r\n");
                    }
                } else {
                    self.pending.push(c);
                }
            }
            Ok(b.len())
        }
        fn flush(&mut self) -> io::Result<()> {
            Ok(())
        }
    }

    #[test]
    fn handshake_reads_identity_and_calibration() {
        let mut p = Script {
            out: VecDeque::new(),
            pending: vec![],
            table: vec![
                ("*IDN?", "OK USB-POWER-HUB,0.4,S1,fw"),
                ("CAL? A", "OK LOW=100,1 MID=5100,0 HIGH=318750,0"),
                ("CAL? B", "OK LOW=101,0 MID=5100,0 HIGH=318750,0"),
            ],
        };
        let stop = AtomicBool::new(false);
        let (idn, cal) = handshake(&mut p, &stop).unwrap();
        assert_eq!(idn, "USB-POWER-HUB,0.4,S1,fw");
        assert_eq!(cal[0].offset[0], 1.0);
        assert_eq!(cal[1].gain_na[0], 101.0);
    }

    #[test]
    fn handshake_fails_on_error_response() {
        let mut p = Script {
            out: VecDeque::new(),
            pending: vec![],
            table: vec![("*IDN?", "OK X,1,2,3"), ("CAL? A", "ERR 02 BAD ARGUMENT")],
        };
        assert!(handshake(&mut p, &AtomicBool::new(false)).unwrap_err().contains("CAL? A"));
    }

    #[test]
    fn demo_session_delivers_connected_and_stream() {
        let s = start_demo();
        let mut got_conn = false;
        let mut bytes = 0usize;
        let t0 = Instant::now();
        while t0.elapsed() < Duration::from_millis(400) {
            match s.rx.recv_timeout(Duration::from_millis(50)) {
                Ok(Msg::Connected { .. }) => got_conn = true,
                Ok(Msg::Stream(b)) => bytes += b.len(),
                _ => {}
            }
        }
        assert!(got_conn);
        // ~400 ms real time = ~40 frames of 710 bytes, allow for scheduling slack
        assert!(bytes > 10 * 700, "bytes = {bytes}");
    }
}
