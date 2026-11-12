//! Main window: class registration, native controls of the left panel, message handling.
//!
//! All window state lives in one `Ui` behind a `RefCell`. A message that arrives while the `Ui`
//! is already borrowed (a nested message sent by a Win32 call made from a handler) falls through
//! to `DefWindowProcW`, so the borrow rules hold without aliasing `&mut`.

use super::canvas::{BackBuffer, Canvas, Font, Fonts};
use super::dialog;
use super::paint::{self, PanelHeader, BG_PANEL};
use super::serial::{com_number, list_ports, SerialPort};
use super::shot;
use super::util::{get_x, get_y, hiword, loword, wide};
use crate::app::{App, Conn};
use crate::config::Config;
use crate::layout::Layout;
use std::cell::RefCell;
use std::collections::HashMap;
use std::ptr::{null, null_mut};
use std::time::{Duration, Instant};
use windows_sys::Win32::Foundation::*;
use windows_sys::Win32::Graphics::Gdi::*;
use windows_sys::Win32::System::LibraryLoader::GetModuleHandleW;
use windows_sys::Win32::UI::HiDpi::{AdjustWindowRectExForDpi, GetDpiForSystem, GetDpiForWindow, SetProcessDpiAwarenessContext, DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2};
use windows_sys::Win32::UI::Input::KeyboardAndMouse::{EnableWindow, GetKeyState, ReleaseCapture, SetCapture, VK_CONTROL};
use windows_sys::Win32::UI::WindowsAndMessaging::*;

const TIMER_ID: usize = 1;
const TIMER_MS: u32 = 33;

const ID_PORTS: i32 = 101;
const ID_CONNECT: i32 = 102;
const ID_IDN: i32 = 103;
const ID_TOGGLE: [i32; 2] = [110, 120];
const ID_CYCLE: [i32; 2] = [111, 121];
const ID_STATE: [i32; 2] = [112, 122];
const ID_RANGE: [i32; 2] = [130, 131];
const ID_SHOW: [i32; 2] = [132, 133];
const ID_LOG: i32 = 134;
const ID_REC: i32 = 140;
const ID_CLEAR: i32 = 141;
const ID_FOLLOW: i32 = 142;
const ID_LIMIT: i32 = 143;
const ID_INFO: i32 = 144;
const ID_SAVE_SEL: i32 = 150;
const ID_SAVE_ALL: i32 = 151;

const BM_GETCHECK: u32 = 0x00F0;
const BM_SETCHECK: u32 = 0x00F1;
const CB_ADDSTRING: u32 = 0x0143;
const CB_GETCURSEL: u32 = 0x0147;
const CB_RESETCONTENT: u32 = 0x014B;
const CB_SETCURSEL: u32 = 0x014E;
const CBN_SELCHANGE: u32 = 1;
const CBN_DROPDOWN: u32 = 7;
const LIMITS_MIN: [f64; 4] = [1.0, 5.0, 10.0, 30.0];

struct Shot {
    path: String,
    after: Duration,
}

struct Ui {
    hwnd: HWND,
    app: App,
    fonts: Option<Fonts>,
    dpi: u32,
    scale: f64,
    w: i32,
    h: i32,
    controls: Vec<(i32, HWND)>,
    cached_text: HashMap<i32, String>,
    headers: Vec<PanelHeader>,
    ports: Vec<String>,
    panel_brush: HBRUSH,
    shot: Option<Shot>,
    started: Instant,
    cfg: Config,
}

fn ptr_slot(hwnd: HWND) -> *const RefCell<Ui> {
    // SAFETY: GWLP_USERDATA holds either 0 or the pointer stored in WM_NCCREATE.
    unsafe { GetWindowLongPtrW(hwnd, GWLP_USERDATA) as *const RefCell<Ui> }
}

impl Ui {
    fn ctl(&self, id: i32) -> HWND {
        self.controls.iter().find(|c| c.0 == id).map_or(null_mut(), |c| c.1)
    }

    fn add(&mut self, class: &str, text: &str, style: u32, id: i32) {
        let (c, t) = (wide(class), wide(text));
        // SAFETY: class and text are NUL-terminated and outlive the call; hwnd is our window.
        let h = unsafe {
            CreateWindowExW(
                0,
                c.as_ptr(),
                t.as_ptr(),
                WS_CHILD | WS_VISIBLE | style,
                0,
                0,
                10,
                10,
                self.hwnd,
                id as usize as HMENU,
                GetModuleHandleW(null()),
                null(),
            )
        };
        self.controls.push((id, h));
    }

    fn create_controls(&mut self) {
        let tab = WS_TABSTOP;
        let combo = tab | WS_VSCROLL | 3; // CBS_DROPDOWNLIST
        let check = tab | 3; // BS_AUTOCHECKBOX
        let ellipsis = 0x4000; // SS_ENDELLIPSIS
        self.add("COMBOBOX", "", combo, ID_PORTS);
        self.add("BUTTON", "Connect", tab, ID_CONNECT);
        self.add("STATIC", "Not connected", 0, ID_IDN);
        for p in 0..2 {
            let n = ["A", "B"][p];
            self.add("STATIC", &format!("Port {n}"), 0, -1 - p as i32);
            self.add("BUTTON", "ON", tab, ID_TOGGLE[p]);
            self.add("BUTTON", "CYCLE", tab, ID_CYCLE[p]);
            self.add("STATIC", "-", ellipsis, ID_STATE[p]);
        }
        for p in 0..2 {
            let n = ["A", "B"][p];
            self.add("STATIC", &format!("Range {n}"), 0, -10 - p as i32);
            self.add("COMBOBOX", "", combo, ID_RANGE[p]);
            for m in ["Auto", "High", "Mid", "Low"] {
                self.send_text(ID_RANGE[p], CB_ADDSTRING, m);
            }
            self.msg(ID_RANGE[p], CB_SETCURSEL, 0, 0);
        }
        self.add("BUTTON", "Show trace A", check, ID_SHOW[0]);
        self.add("BUTTON", "Show trace B", check, ID_SHOW[1]);
        self.add("BUTTON", "Log scale", check, ID_LOG);
        self.add("BUTTON", "Start", tab, ID_REC);
        self.add("BUTTON", "Clear", tab, ID_CLEAR);
        self.add("BUTTON", "Follow live", check, ID_FOLLOW);
        self.add("STATIC", "Limit", 0, -20);
        self.add("COMBOBOX", "", combo, ID_LIMIT);
        for m in ["1 minute", "5 minutes", "10 minutes", "30 minutes"] {
            self.send_text(ID_LIMIT, CB_ADDSTRING, m);
        }
        let sel = LIMITS_MIN.iter().position(|&m| m == self.app.max_minutes).unwrap_or(2);
        self.msg(ID_LIMIT, CB_SETCURSEL, sel, 0);
        self.add("STATIC", "", 0, ID_INFO);
        self.add("BUTTON", "Save selection as CSV", tab, ID_SAVE_SEL);
        self.add("BUTTON", "Save all as CSV", tab, ID_SAVE_ALL);
        self.msg(ID_SHOW[0], BM_SETCHECK, 1, 0);
        self.msg(ID_SHOW[1], BM_SETCHECK, 1, 0);
        self.msg(ID_LOG, BM_SETCHECK, self.app.view.log as usize, 0);
        self.refresh_ports();
        self.apply_font();
        self.layout_controls();
    }

    fn msg(&self, id: i32, m: u32, w: usize, l: isize) -> isize {
        // SAFETY: the handle belongs to a control of this window.
        unsafe { SendMessageW(self.ctl(id), m, w, l) }
    }

    fn send_text(&self, id: i32, m: u32, text: &str) {
        let t = wide(text);
        // SAFETY: t is NUL-terminated and outlives the synchronous SendMessage.
        unsafe {
            SendMessageW(self.ctl(id), m, 0, t.as_ptr() as isize);
        }
    }

    fn set_text(&mut self, id: i32, text: &str) {
        if self.cached_text.get(&id).map(String::as_str) == Some(text) {
            return;
        }
        let t = wide(text);
        // SAFETY: t is NUL-terminated and outlives the call.
        unsafe {
            SetWindowTextW(self.ctl(id), t.as_ptr());
        }
        self.cached_text.insert(id, text.to_string());
    }

    fn enable(&self, id: i32, on: bool) {
        // SAFETY: the handle belongs to a control of this window.
        unsafe {
            EnableWindow(self.ctl(id), on as i32);
        }
    }

    fn checked(&self, id: i32) -> bool {
        self.msg(id, BM_GETCHECK, 0, 0) == 1
    }

    fn apply_font(&self) {
        let Some(f) = &self.fonts else { return };
        let font = f.handle(Font::Normal);
        for (_, h) in &self.controls {
            // SAFETY: control handles belong to this window; the font outlives the controls' use.
            unsafe {
                SendMessageW(*h, WM_SETFONT, font as usize, 1);
            }
        }
    }

    fn refresh_ports(&mut self) {
        let current = self.selected_port();
        let mut items = vec!["Demo device".to_string()];
        items.extend(list_ports());
        self.msg(ID_PORTS, CB_RESETCONTENT, 0, 0);
        for i in &items {
            self.send_text(ID_PORTS, CB_ADDSTRING, i);
        }
        let sel = current.and_then(|c| items.iter().position(|i| *i == c)).unwrap_or(0);
        self.msg(ID_PORTS, CB_SETCURSEL, sel, 0);
        self.ports = items;
    }

    fn selected_port(&self) -> Option<String> {
        let i = self.msg(ID_PORTS, CB_GETCURSEL, 0, 0);
        (i >= 0).then(|| self.ports.get(i as usize).cloned()).flatten()
    }

    fn px(&self, v: i32) -> i32 {
        (v as f64 * self.scale).round() as i32
    }

    fn place(&self, id: i32, x: i32, y: i32, w: i32, h: i32) {
        let (x, y, w, h) = (self.px(x), self.px(y), self.px(w), self.px(h));
        // SAFETY: the handle belongs to a control of this window.
        unsafe {
            MoveWindow(self.ctl(id), x, y, w, h, 1);
        }
    }

    fn layout_controls(&mut self) {
        let x = 14;
        let fw = 232;
        self.headers.clear();
        let header = |s: &mut Self, text: &'static str, y: i32| {
            s.headers.push(PanelHeader { text, x: s.px(x), y: s.px(y), w: s.px(fw) });
        };
        header(self, "DEVICE", 12);
        self.place(ID_PORTS, x, 34, fw, 260);
        self.place(ID_CONNECT, x, 64, fw, 28);
        self.place(ID_IDN, x, 98, fw, 34);

        header(self, "PORTS", 142);
        for p in 0..2 {
            let y = 166 + p as i32 * 32;
            self.place(-1 - p as i32, x, y + 4, 40, 20);
            self.place(ID_TOGGLE[p], x + 44, y, 62, 28);
            self.place(ID_CYCLE[p], x + 110, y, 62, 28);
            self.place(ID_STATE[p], x + 178, y + 4, 54, 20);
        }

        header(self, "MEASUREMENT", 238);
        for (p, &id) in ID_RANGE.iter().enumerate() {
            let y = 262 + p as i32 * 30;
            self.place(-10 - p as i32, x, y + 3, 64, 20);
            self.place(id, x + 68, y, 100, 260);
        }
        self.place(ID_SHOW[0], x, 326, fw, 22);
        self.place(ID_SHOW[1], x, 350, fw, 22);
        self.place(ID_LOG, x, 374, fw, 22);

        header(self, "RECORDING", 410);
        self.place(ID_REC, x, 434, 112, 28);
        self.place(ID_CLEAR, x + 120, 434, 112, 28);
        self.place(ID_FOLLOW, x, 470, fw, 22);
        self.place(-20, x, 500, 64, 20);
        self.place(ID_LIMIT, x + 68, 497, 100, 260);
        self.place(ID_INFO, x, 530, fw, 36);

        header(self, "EXPORT", 580);
        self.place(ID_SAVE_SEL, x, 604, fw, 28);
        self.place(ID_SAVE_ALL, x, 638, fw, 28);
    }

    fn sync_controls(&mut self) {
        let a = &self.app;
        let connected = a.conn == Conn::Connected;
        let busy = a.conn != Conn::Disconnected;
        let connect_text = if busy { "Disconnect" } else { "Connect" };
        let idn = match a.conn {
            Conn::Connected => a.idn.clone(),
            Conn::Connecting => "Connecting...".to_string(),
            Conn::Disconnected => "Not connected".to_string(),
        };
        let toggles: Vec<(String, String)> = (0..2)
            .map(|p| {
                let on = a.port_state[p] == "ON";
                (if on { "Turn OFF" } else { "Turn ON" }.to_string(), a.port_text(p))
            })
            .collect();
        let rec_text = if a.recording { "Stop" } else { "Start" };
        let info = format!(
            "{:.1} kSPS per channel\nRecorded {} of {} min",
            a.rate_sps / 1000.0,
            crate::fmt::duration(a.len_us()),
            a.max_minutes
        );
        let follow = a.view.follow;
        let log = a.view.log;
        self.set_text(ID_CONNECT, connect_text);
        self.set_text(ID_IDN, &idn);
        for p in 0..2 {
            self.set_text(ID_TOGGLE[p], &toggles[p].0);
            self.set_text(ID_STATE[p], &toggles[p].1);
            self.enable(ID_TOGGLE[p], connected);
            self.enable(ID_CYCLE[p], connected);
            self.enable(ID_RANGE[p], connected);
        }
        self.set_text(ID_REC, rec_text);
        self.enable(ID_REC, connected);
        self.set_text(ID_INFO, &info);
        self.enable(ID_PORTS, !busy);
        if self.checked(ID_FOLLOW) != follow {
            self.msg(ID_FOLLOW, BM_SETCHECK, follow as usize, 0);
        }
        if self.checked(ID_LOG) != log {
            self.msg(ID_LOG, BM_SETCHECK, log as usize, 0);
        }
        self.app.dirty_controls = false;
    }

    fn layout(&self) -> Layout {
        Layout::compute(self.w, self.h, self.scale, self.app.visible_channels().len())
    }

    fn invalidate(&self) {
        // SAFETY: our own window; null rect invalidates the whole client area without erasing.
        unsafe {
            InvalidateRect(self.hwnd, null(), 0);
        }
    }

    fn paint_into(&self, hdc: HDC) {
        let Some(fonts) = &self.fonts else { return };
        let lay = self.layout();
        // SAFETY: hdc is the valid device context handed to WM_PAINT / WM_PRINTCLIENT.
        unsafe {
            let bb = BackBuffer::new(hdc, self.w, self.h);
            {
                let mut c = Canvas::new(bb.dc, fonts);
                paint::paint(&mut c, &self.app, &lay, self.w, self.h, &self.headers);
            }
            bb.blit_to(hdc);
        }
    }

    fn connect_clicked(&mut self) {
        if self.app.conn != Conn::Disconnected {
            self.app.disconnect();
            return;
        }
        match self.selected_port() {
            Some(name) if name != "Demo device" => {
                let Some(n) = com_number(&name) else {
                    self.app.notice = Some(format!("Unsupported port name {name}"));
                    return;
                };
                let stream_name = format!("COM{}", n + 1);
                let ctrl = SerialPort::open(&name);
                let stream = SerialPort::open(&stream_name);
                match (ctrl, stream) {
                    (Ok(c), Ok(s)) => self.app.connect_serial(Box::new(c), Box::new(s), &format!("{name} (stream {stream_name})")),
                    (Err(e), _) => self.app.notice = Some(format!("Cannot open {name}: {e}")),
                    (_, Err(e)) => self.app.notice = Some(format!("Cannot open stream port {stream_name}: {e}")),
                }
            }
            _ => self.app.connect_demo(),
        }
    }

    fn save_csv(&mut self, selection_only: bool) {
        let name = if selection_only { "selection.csv" } else { "recording.csv" };
        let Some(path) = dialog::save_csv(self.hwnd, name) else { return };
        match self.app.export_csv(&path, selection_only) {
            Ok(n) => self.app.notice = Some(format!("Saved {n} samples to {path}")),
            Err(e) => dialog::error_box(self.hwnd, &format!("Cannot save {path}: {e}")),
        }
    }

    fn command(&mut self, id: i32, code: u32) {
        match id {
            ID_PORTS if code == CBN_DROPDOWN => self.refresh_ports(),
            ID_CONNECT => self.connect_clicked(),
            ID_TOGGLE_A | ID_TOGGLE_B => {
                let p = (id == ID_TOGGLE_B) as usize;
                let verb = if self.app.port_state[p] == "ON" { "OFF" } else { "ON" };
                self.app.port_command(p, verb);
            }
            ID_CYCLE_A | ID_CYCLE_B => self.app.port_command((id == ID_CYCLE_B) as usize, "CYCLE"),
            ID_RANGE_A | ID_RANGE_B if code == CBN_SELCHANGE => {
                let p = (id == ID_RANGE_B) as usize;
                let sel = self.msg(id, CB_GETCURSEL, 0, 0);
                if sel >= 0 {
                    self.app.set_range_mode(p, sel as usize);
                }
            }
            ID_SHOW_A | ID_SHOW_B => {
                self.app.show = [self.checked(ID_SHOW[0]), self.checked(ID_SHOW[1])];
                self.app.update_view();
            }
            ID_LOG => self.app.set_log(self.checked(ID_LOG)),
            ID_REC => {
                let on = !self.app.recording;
                self.app.set_recording(on);
            }
            ID_CLEAR => self.app.clear(),
            ID_FOLLOW => self.app.set_follow(self.checked(ID_FOLLOW)),
            ID_LIMIT if code == CBN_SELCHANGE => {
                let sel = self.msg(ID_LIMIT, CB_GETCURSEL, 0, 0);
                if let Some(m) = (sel >= 0).then(|| LIMITS_MIN.get(sel as usize)).flatten() {
                    self.app.set_max_minutes(*m);
                }
            }
            ID_SAVE_SEL => self.save_csv(true),
            ID_SAVE_ALL => self.save_csv(false),
            _ => {}
        }
        self.sync_controls();
        self.invalidate();
    }

    fn set_dpi(&mut self, dpi: u32) {
        self.dpi = dpi;
        self.scale = dpi as f64 / 96.0;
        self.fonts = Some(Fonts::new(dpi));
        self.apply_font();
        self.layout_controls();
    }

    fn on_timer(&mut self) {
        self.app.tick();
        self.sync_controls();
        self.invalidate();
    }

    fn shot_due(&self) -> Option<String> {
        let s = self.shot.as_ref()?;
        (self.started.elapsed() >= s.after).then(|| s.path.clone())
    }
}

// Control ids used in `command` patterns.
const ID_TOGGLE_A: i32 = ID_TOGGLE[0];
const ID_TOGGLE_B: i32 = ID_TOGGLE[1];
const ID_CYCLE_A: i32 = ID_CYCLE[0];
const ID_CYCLE_B: i32 = ID_CYCLE[1];
const ID_RANGE_A: i32 = ID_RANGE[0];
const ID_RANGE_B: i32 = ID_RANGE[1];
const ID_SHOW_A: i32 = ID_SHOW[0];
const ID_SHOW_B: i32 = ID_SHOW[1];

unsafe extern "system" fn wnd_proc(hwnd: HWND, msg: u32, wp: WPARAM, lp: LPARAM) -> LRESULT {
    if msg == WM_NCCREATE {
        let cs = lp as *const CREATESTRUCTW;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (*cs).lpCreateParams as isize);
        return DefWindowProcW(hwnd, msg, wp, lp);
    }
    let slot = ptr_slot(hwnd);
    if slot.is_null() {
        return DefWindowProcW(hwnd, msg, wp, lp);
    }
    if msg == WM_NCDESTROY {
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, 0);
        drop(Box::from_raw(slot as *mut RefCell<Ui>));
        return DefWindowProcW(hwnd, msg, wp, lp);
    }
    let cell = &*slot;
    let Ok(mut ui) = cell.try_borrow_mut() else {
        return DefWindowProcW(hwnd, msg, wp, lp);
    };
    match msg {
        WM_CREATE => {
            ui.hwnd = hwnd;
            let dpi = GetDpiForWindow(hwnd);
            ui.set_dpi(if dpi == 0 { 96 } else { dpi });
            ui.create_controls();
            SetTimer(hwnd, TIMER_ID, TIMER_MS, None);
            if ui.cfg.demo {
                ui.app.connect_demo();
            }
            ui.sync_controls();
            0
        }
        WM_SIZE => {
            ui.w = (lp & 0xFFFF) as i32;
            ui.h = ((lp >> 16) & 0xFFFF) as i32;
            ui.invalidate();
            0
        }
        WM_GETMINMAXINFO => {
            let mmi = lp as *mut MINMAXINFO;
            (*mmi).ptMinTrackSize.x = ui.px(1000);
            (*mmi).ptMinTrackSize.y = ui.px(720);
            0
        }
        WM_DPICHANGED => {
            let dpi = loword(wp);
            ui.set_dpi(dpi);
            let r = &*(lp as *const RECT);
            SetWindowPos(hwnd, null_mut(), r.left, r.top, r.right - r.left, r.bottom - r.top, SWP_NOZORDER | SWP_NOACTIVATE);
            ui.invalidate();
            0
        }
        WM_ERASEBKGND => {
            // Native children (themed checkboxes) ask their parent to paint their background.
            let hdc = wp as HDC;
            let mut rc: RECT = std::mem::zeroed();
            GetClipBox(hdc, &mut rc);
            SetDCBrushColor(hdc, BG_PANEL);
            FillRect(hdc, &rc, GetStockObject(DC_BRUSH) as HBRUSH);
            1
        }
        WM_PAINT => {
            let mut ps: PAINTSTRUCT = std::mem::zeroed();
            let hdc = BeginPaint(hwnd, &mut ps);
            ui.paint_into(hdc);
            EndPaint(hwnd, &ps);
            0
        }
        WM_PRINTCLIENT => {
            ui.paint_into(wp as HDC);
            0
        }
        WM_CTLCOLORSTATIC | WM_CTLCOLORBTN => {
            let hdc = wp as HDC;
            SetBkColor(hdc, BG_PANEL);
            SetTextColor(hdc, super::util::rgb(32, 36, 44));
            ui.panel_brush as LRESULT
        }
        WM_COMMAND => {
            let id = loword(wp) as i32;
            let code = hiword(wp);
            ui.command(id, code);
            0
        }
        WM_TIMER => {
            ui.on_timer();
            let due = ui.shot_due();
            drop(ui);
            if let Some(path) = due {
                finish_screenshot(hwnd, cell, &path);
            }
            0
        }
        WM_LBUTTONDOWN | WM_RBUTTONDOWN => {
            let lay = ui.layout();
            let (x, y) = (get_x(lp), get_y(lp));
            if ui.app.mouse_down(&lay, msg == WM_LBUTTONDOWN, x, y) {
                SetCapture(hwnd);
            }
            ui.sync_controls();
            ui.invalidate();
            0
        }
        WM_MOUSEMOVE => {
            let lay = ui.layout();
            ui.app.mouse_move(&lay, get_x(lp), get_y(lp));
            ui.sync_controls();
            ui.invalidate();
            0
        }
        WM_LBUTTONUP | WM_RBUTTONUP => {
            ui.app.mouse_up();
            ReleaseCapture();
            ui.invalidate();
            0
        }
        WM_LBUTTONDBLCLK => {
            let lay = ui.layout();
            ui.app.double_click(&lay, get_x(lp), get_y(lp));
            ui.sync_controls();
            ui.invalidate();
            0
        }
        WM_MOUSEWHEEL => {
            let mut pt = POINT { x: get_x(lp), y: get_y(lp) };
            ScreenToClient(hwnd, &mut pt);
            let delta = (hiword(wp) as u16 as i16) as f64 / 120.0;
            let ctrl = GetKeyState(VK_CONTROL as i32) < 0;
            let lay = ui.layout();
            ui.app.wheel(&lay, pt.x, pt.y, delta, ctrl);
            ui.sync_controls();
            ui.invalidate();
            0
        }
        WM_DESTROY => {
            KillTimer(hwnd, TIMER_ID);
            ui.app.disconnect();
            PostQuitMessage(0);
            0
        }
        _ => {
            drop(ui);
            DefWindowProcW(hwnd, msg, wp, lp)
        }
    }
}

/// Runs outside any borrow of the `Ui`, because the capture sends WM_PAINT to this very window.
unsafe fn finish_screenshot(hwnd: HWND, cell: &RefCell<Ui>, path: &str) {
    {
        let mut ui = cell.borrow_mut();
        ui.shot = None;
        ui.app.select_fraction(0.35, 0.51);
        ui.sync_controls();
        ui.invalidate();
    }
    UpdateWindow(hwnd);
    let code = match shot::capture_client(hwnd, path) {
        Ok(()) => 0,
        Err(e) => {
            dialog::error_box(hwnd, &format!("Screenshot failed: {e}"));
            2
        }
    };
    PostQuitMessage(code);
}

pub fn run(cfg: Config) -> i32 {
    // SAFETY: standard window-class registration, creation and message loop on this thread.
    unsafe {
        SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);
        let hinst = GetModuleHandleW(null());
        let class = wide("UsbPowerProfilerWindow");
        let wc = WNDCLASSEXW {
            cbSize: std::mem::size_of::<WNDCLASSEXW>() as u32,
            style: CS_DBLCLKS,
            lpfnWndProc: Some(wnd_proc),
            cbClsExtra: 0,
            cbWndExtra: 0,
            hInstance: hinst,
            hIcon: null_mut(),
            hCursor: LoadCursorW(null_mut(), IDC_ARROW),
            hbrBackground: null_mut(),
            lpszMenuName: null(),
            lpszClassName: class.as_ptr(),
            hIconSm: null_mut(),
        };
        if RegisterClassExW(&wc) == 0 {
            dialog::error_box(null_mut(), "Cannot register the window class");
            return 1;
        }
        let mut app = App::new(cfg.max_minutes);
        app.view.log = cfg.log;
        if let Some(s) = cfg.span_s {
            app.view.span = s * 1e6;
        }
        let shot = cfg.screenshot.clone().map(|path| Shot { path, after: Duration::from_secs_f64(cfg.after_s) });
        let ui = Box::new(RefCell::new(Ui {
            hwnd: null_mut(),
            app,
            fonts: None,
            dpi: 96,
            scale: 1.0,
            w: 0,
            h: 0,
            controls: Vec::new(),
            cached_text: HashMap::new(),
            headers: Vec::new(),
            ports: Vec::new(),
            panel_brush: CreateSolidBrush(BG_PANEL),
            shot,
            started: Instant::now(),
            cfg,
        }));
        let brush = ui.borrow().panel_brush;
        let dpi = GetDpiForSystem();
        let style = WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN;
        let mut rc = RECT { left: 0, top: 0, right: (1280 * dpi / 96) as i32, bottom: (800 * dpi / 96) as i32 };
        AdjustWindowRectExForDpi(&mut rc, style, 0, 0, dpi);
        let title = wide("USB Power Profiler");
        let raw = Box::into_raw(ui);
        let hwnd = CreateWindowExW(
            0,
            class.as_ptr(),
            title.as_ptr(),
            style | WS_VISIBLE,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            rc.right - rc.left,
            rc.bottom - rc.top,
            null_mut(),
            null_mut(),
            hinst,
            raw as *const std::ffi::c_void,
        );
        if hwnd.is_null() {
            drop(Box::from_raw(raw));
            DeleteObject(brush as _);
            dialog::error_box(null_mut(), "Cannot create the main window");
            return 1;
        }
        let mut msg: MSG = std::mem::zeroed();
        while GetMessageW(&mut msg, null_mut(), 0, 0) > 0 {
            if IsDialogMessageW(hwnd, &msg) == 0 {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
        }
        DeleteObject(brush as _);
        msg.wParam as i32
    }
}
