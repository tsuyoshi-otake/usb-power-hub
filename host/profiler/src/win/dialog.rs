//! Common dialogs and message boxes.

use super::util::{from_wide, wide};
use windows_sys::Win32::Foundation::HWND;
use windows_sys::Win32::UI::Controls::Dialogs::{GetSaveFileNameW, OPENFILENAMEW, OFN_OVERWRITEPROMPT, OFN_PATHMUSTEXIST};
use windows_sys::Win32::UI::WindowsAndMessaging::{MessageBoxW, MB_ICONERROR, MB_OK};

/// "Save as" dialog for a CSV file. Returns the chosen path, or `None` when cancelled.
pub fn save_csv(owner: HWND, default_name: &str) -> Option<String> {
    let mut file = [0u16; 1024];
    for (d, s) in file.iter_mut().zip(default_name.encode_utf16()) {
        *d = s;
    }
    let filter: Vec<u16> = "CSV files (*.csv)\0*.csv\0All files\0*.*\0\0".encode_utf16().collect();
    let ext = wide("csv");
    // SAFETY: the structure is zero-initialised and every pointer it holds outlives the call.
    unsafe {
        let mut ofn: OPENFILENAMEW = std::mem::zeroed();
        ofn.lStructSize = std::mem::size_of::<OPENFILENAMEW>() as u32;
        ofn.hwndOwner = owner;
        ofn.lpstrFilter = filter.as_ptr();
        ofn.lpstrFile = file.as_mut_ptr();
        ofn.nMaxFile = file.len() as u32;
        ofn.lpstrDefExt = ext.as_ptr();
        ofn.Flags = OFN_OVERWRITEPROMPT | OFN_PATHMUSTEXIST;
        if GetSaveFileNameW(&mut ofn) == 0 {
            return None;
        }
    }
    Some(from_wide(&file))
}

pub fn error_box(owner: HWND, text: &str) {
    let t = wide(text);
    let title = wide("USB Power Profiler");
    // SAFETY: both strings are NUL-terminated and outlive the call.
    unsafe {
        MessageBoxW(owner, t.as_ptr(), title.as_ptr(), MB_OK | MB_ICONERROR);
    }
}
