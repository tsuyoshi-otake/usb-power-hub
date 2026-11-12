//! Everything that calls the Win32 API. This module tree is the only place with `unsafe`.

mod canvas;
mod dialog;
mod paint;
mod serial;
mod shot;
mod ui;
mod util;

pub use ui::run;

/// Message box without an owner window (start-up errors).
pub fn error(text: &str) {
    dialog::error_box(std::ptr::null_mut(), text);
}
