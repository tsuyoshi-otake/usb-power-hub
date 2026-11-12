//! USB Power Profiler: native Win32 current profiler for the USB Power-Control Hub (issue #9).
//! No GUI framework: `win` calls the Win32 API directly through windows-sys; everything else is
//! platform independent and unit-tested.

#![cfg_attr(not(test), windows_subsystem = "windows")]
#![deny(unsafe_code)]

mod app;
mod config;
mod demo;
mod device;
mod fmt;
mod layout;
mod protocol;
mod store;
#[allow(unsafe_code)]
mod win;

fn main() {
    let cfg = match config::Config::parse(std::env::args().skip(1)) {
        Ok(c) => c,
        Err(e) => {
            // No console in a windows-subsystem build: say it in a message box.
            win::error(&format!("{e}\n\nOptions: --demo --screenshot <file.bmp> --after <s> --log --span <s> --max-minutes <n>"));
            std::process::exit(2);
        }
    };
    std::process::exit(win::run(cfg));
}
