//! GDI drawing primitives. All drawing in `paint.rs` goes through `Canvas`, so this is the only
//! place that touches device contexts for painting.

use super::util::wide;
use crate::layout::Rect;
use windows_sys::Win32::Foundation::{POINT, RECT, SIZE};
use windows_sys::Win32::Graphics::Gdi::*;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Font {
    Normal,
    Small,
    Bold,
    Header,
}

pub struct Fonts {
    fonts: [HFONT; 4],
}

impl Fonts {
    pub fn new(dpi: u32) -> Fonts {
        let make = |pt: i32, weight: i32| -> HFONT {
            let face = wide("Segoe UI");
            let h = -((pt * dpi as i32 + 36) / 72);
            // SAFETY: face is NUL-terminated and outlives the call.
            unsafe { CreateFontW(h, 0, 0, 0, weight, 0, 0, 0, 1, 0, 0, 5, 0, face.as_ptr()) }
        };
        Fonts { fonts: [make(9, 400), make(8, 400), make(9, 700), make(8, 700)] }
    }

    pub fn handle(&self, f: Font) -> HFONT {
        self.fonts[f as usize]
    }
}

impl Drop for Fonts {
    fn drop(&mut self) {
        for f in self.fonts {
            // SAFETY: the fonts were created by CreateFontW and are deleted once.
            unsafe {
                DeleteObject(f as _);
            }
        }
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Align {
    Left,
    Center,
    Right,
}

pub struct Canvas<'a> {
    hdc: HDC,
    fonts: &'a Fonts,
}

fn rc(r: Rect) -> RECT {
    RECT { left: r.l, top: r.t, right: r.r, bottom: r.b }
}

impl<'a> Canvas<'a> {
    /// # Safety
    /// `hdc` must be a valid device context that outlives the canvas.
    pub unsafe fn new(hdc: HDC, fonts: &'a Fonts) -> Canvas<'a> {
        SetBkMode(hdc, 1);
        Canvas { hdc, fonts }
    }

    pub fn fill(&mut self, r: Rect, color: u32) {
        if r.r <= r.l || r.b <= r.t {
            return;
        }
        let rr = rc(r);
        // SAFETY: hdc is valid (Canvas::new contract); the stock DC brush needs no cleanup.
        unsafe {
            SetDCBrushColor(self.hdc, color);
            FillRect(self.hdc, &rr, GetStockObject(DC_BRUSH) as HBRUSH);
        }
    }

    pub fn outline(&mut self, r: Rect, color: u32) {
        self.fill(Rect::new(r.l, r.t, r.r, r.t + 1), color);
        self.fill(Rect::new(r.l, r.b - 1, r.r, r.b), color);
        self.fill(Rect::new(r.l, r.t, r.l + 1, r.b), color);
        self.fill(Rect::new(r.r - 1, r.t, r.r, r.b), color);
    }

    pub fn hline(&mut self, x0: i32, x1: i32, y: i32, color: u32) {
        self.fill(Rect::new(x0, y, x1, y + 1), color);
    }

    pub fn vline(&mut self, x: i32, y0: i32, y1: i32, color: u32) {
        self.fill(Rect::new(x, y0, x + 1, y1), color);
    }

    pub fn polyline(&mut self, pts: &[(i32, i32)], color: u32, width: i32) {
        if pts.len() < 2 {
            return;
        }
        let p: Vec<POINT> = pts.iter().map(|&(x, y)| POINT { x, y }).collect();
        // SAFETY: the pen is selected, used and deleted within this call; p outlives the call.
        unsafe {
            let pen = CreatePen(0, width, color);
            let old = SelectObject(self.hdc, pen as _);
            Polyline(self.hdc, p.as_ptr(), p.len() as i32);
            SelectObject(self.hdc, old);
            DeleteObject(pen as _);
        }
    }

    /// Diagonal hatch lines on a transparent background.
    pub fn hatch(&mut self, r: Rect, color: u32) {
        if r.r <= r.l || r.b <= r.t {
            return;
        }
        let rr = rc(r);
        // SAFETY: the brush is created and deleted within this call.
        unsafe {
            let br = CreateHatchBrush(3, color);
            FillRect(self.hdc, &rr, br);
            DeleteObject(br as _);
        }
    }

    pub fn clip(&mut self, r: Rect) {
        // SAFETY: hdc is valid; SaveDC / RestoreDC are paired by `unclip`.
        unsafe {
            SaveDC(self.hdc);
            IntersectClipRect(self.hdc, r.l, r.t, r.r, r.b);
        }
    }

    pub fn unclip(&mut self) {
        // SAFETY: restores the state saved by `clip`.
        unsafe {
            RestoreDC(self.hdc, -1);
        }
    }

    pub fn text_width(&mut self, s: &str, font: Font) -> i32 {
        let w: Vec<u16> = s.encode_utf16().collect();
        let mut size = SIZE { cx: 0, cy: 0 };
        // SAFETY: w and size are valid for the call.
        unsafe {
            let old = SelectObject(self.hdc, self.fonts.handle(font) as _);
            GetTextExtentPoint32W(self.hdc, w.as_ptr(), w.len() as i32, &mut size);
            SelectObject(self.hdc, old);
        }
        size.cx
    }

    pub fn text_height(&mut self, font: Font) -> i32 {
        let mut size = SIZE { cx: 0, cy: 0 };
        let w = [b'A' as u16];
        // SAFETY: w and size are valid for the call.
        unsafe {
            let old = SelectObject(self.hdc, self.fonts.handle(font) as _);
            GetTextExtentPoint32W(self.hdc, w.as_ptr(), 1, &mut size);
            SelectObject(self.hdc, old);
        }
        size.cy
    }

    /// Draws `s` with its top at `y`; `x` is the left, centre or right edge according to `align`.
    pub fn text(&mut self, x: i32, y: i32, s: &str, color: u32, font: Font, align: Align) {
        let w: Vec<u16> = s.encode_utf16().collect();
        let width = self.text_width(s, font);
        let x = match align {
            Align::Left => x,
            Align::Center => x - width / 2,
            Align::Right => x - width,
        };
        // SAFETY: w is valid for the call; the previous font is restored.
        unsafe {
            let old = SelectObject(self.hdc, self.fonts.handle(font) as _);
            SetTextColor(self.hdc, color);
            TextOutW(self.hdc, x, y, w.as_ptr(), w.len() as i32);
            SelectObject(self.hdc, old);
        }
    }
}

/// Off-screen bitmap the size of the client area; dropped after the blit.
pub struct BackBuffer {
    pub dc: HDC,
    bmp: HBITMAP,
    old: HGDIOBJ,
    w: i32,
    h: i32,
}

impl BackBuffer {
    /// # Safety
    /// `target` must be a valid device context.
    pub unsafe fn new(target: HDC, w: i32, h: i32) -> BackBuffer {
        let dc = CreateCompatibleDC(target);
        let bmp = CreateCompatibleBitmap(target, w.max(1), h.max(1));
        let old = SelectObject(dc, bmp as _);
        BackBuffer { dc, bmp, old, w, h }
    }

    /// # Safety
    /// `target` must be a valid device context.
    pub unsafe fn blit_to(&self, target: HDC) {
        BitBlt(target, 0, 0, self.w, self.h, self.dc, 0, 0, SRCCOPY);
    }
}

impl Drop for BackBuffer {
    fn drop(&mut self) {
        // SAFETY: objects created in `new`, released once.
        unsafe {
            SelectObject(self.dc, self.old);
            DeleteObject(self.bmp as _);
            DeleteDC(self.dc);
        }
    }
}
