//! Capture of a window's client area into a 24-bit BMP file (used by `--screenshot`).

use std::io::{self, Write};
use windows_sys::Win32::Foundation::{HWND, RECT};
use windows_sys::Win32::Graphics::Gdi::*;
use windows_sys::Win32::Storage::Xps::PrintWindow;
use windows_sys::Win32::UI::WindowsAndMessaging::GetClientRect;

const PW_CLIENTONLY: u32 = 1;
const PW_RENDERFULLCONTENT: u32 = 2;

pub fn capture_client(hwnd: HWND, path: &str) -> io::Result<()> {
    let (w, h, pixels) = grab(hwnd)?;
    let stride = ((w * 3 + 3) & !3) as usize;
    let data_len = stride * h as usize;
    let mut out = Vec::with_capacity(54 + data_len);
    out.extend_from_slice(b"BM");
    out.extend_from_slice(&((54 + data_len) as u32).to_le_bytes());
    out.extend_from_slice(&[0; 4]);
    out.extend_from_slice(&54u32.to_le_bytes());
    out.extend_from_slice(&40u32.to_le_bytes());
    out.extend_from_slice(&w.to_le_bytes());
    out.extend_from_slice(&h.to_le_bytes()); // positive height: rows stored bottom-up
    out.extend_from_slice(&1u16.to_le_bytes());
    out.extend_from_slice(&24u16.to_le_bytes());
    out.extend_from_slice(&[0; 4]); // BI_RGB
    out.extend_from_slice(&(data_len as u32).to_le_bytes());
    out.extend_from_slice(&[0; 16]); // resolution, palette sizes
    out.extend_from_slice(&pixels);
    std::fs::File::create(path)?.write_all(&out)
}

/// Returns (width, height, bottom-up BGR rows padded to 4 bytes).
fn grab(hwnd: HWND) -> io::Result<(i32, i32, Vec<u8>)> {
    // SAFETY: standard GDI capture sequence; every object created here is released before return.
    unsafe {
        let mut rc = RECT { left: 0, top: 0, right: 0, bottom: 0 };
        GetClientRect(hwnd, &mut rc);
        let (w, h) = (rc.right - rc.left, rc.bottom - rc.top);
        if w <= 0 || h <= 0 {
            return Err(io::Error::other("empty client area"));
        }
        let hdc = GetDC(hwnd);
        let mem = CreateCompatibleDC(hdc);
        let bmp = CreateCompatibleBitmap(hdc, w, h);
        let old = SelectObject(mem, bmp as _);
        let printed = PrintWindow(hwnd, mem, PW_CLIENTONLY | PW_RENDERFULLCONTENT);
        let stride = ((w * 3 + 3) & !3) as usize;
        let mut buf = vec![0u8; stride * h as usize];
        let mut bi: BITMAPINFO = std::mem::zeroed();
        bi.bmiHeader.biSize = std::mem::size_of::<BITMAPINFOHEADER>() as u32;
        bi.bmiHeader.biWidth = w;
        bi.bmiHeader.biHeight = h;
        bi.bmiHeader.biPlanes = 1;
        bi.bmiHeader.biBitCount = 24;
        let lines = GetDIBits(mem, bmp, 0, h as u32, buf.as_mut_ptr() as _, &mut bi, DIB_RGB_COLORS);
        SelectObject(mem, old);
        DeleteObject(bmp as _);
        DeleteDC(mem);
        ReleaseDC(hwnd, hdc);
        if printed == 0 || lines == 0 {
            return Err(io::Error::other("PrintWindow or GetDIBits failed"));
        }
        Ok((w, h, buf))
    }
}
