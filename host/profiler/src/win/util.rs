//! Small helpers shared by the Win32 modules.

pub fn wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

pub fn from_wide(buf: &[u16]) -> String {
    let n = buf.iter().position(|&c| c == 0).unwrap_or(buf.len());
    String::from_utf16_lossy(&buf[..n])
}

pub const fn rgb(r: u8, g: u8, b: u8) -> u32 {
    r as u32 | (g as u32) << 8 | (b as u32) << 16
}

pub fn loword(v: usize) -> u32 {
    (v & 0xFFFF) as u32
}

pub fn hiword(v: usize) -> u32 {
    ((v >> 16) & 0xFFFF) as u32
}

/// Signed x coordinate packed in an LPARAM.
pub fn get_x(lp: isize) -> i32 {
    (lp & 0xFFFF) as u16 as i16 as i32
}

pub fn get_y(lp: isize) -> i32 {
    ((lp >> 16) & 0xFFFF) as u16 as i16 as i32
}
