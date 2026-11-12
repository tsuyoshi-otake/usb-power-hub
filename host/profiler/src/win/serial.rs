//! Serial ports through the Win32 communications API.

use super::util::{from_wide, wide};
use std::io::{self, Read, Write};
use std::ptr::{null, null_mut};
use windows_sys::Win32::Devices::Communication::{
    GetCommState, PurgeComm, SetCommState, SetCommTimeouts, COMMTIMEOUTS, DCB, PURGE_RXCLEAR, PURGE_TXCLEAR,
};
use windows_sys::Win32::Foundation::{CloseHandle, GENERIC_READ, GENERIC_WRITE, HANDLE, INVALID_HANDLE_VALUE};
use windows_sys::Win32::Storage::FileSystem::{CreateFileW, ReadFile, WriteFile, FILE_ATTRIBUTE_NORMAL, OPEN_EXISTING};
use windows_sys::Win32::System::Registry::{RegCloseKey, RegEnumValueW, RegOpenKeyExW, HKEY, HKEY_LOCAL_MACHINE, KEY_READ};

pub struct SerialPort {
    handle: HANDLE,
}

// The handle is only used from the thread that owns the SerialPort (it is moved into it).
unsafe impl Send for SerialPort {}

impl SerialPort {
    /// Opens `COMn` (the `\\.\` prefix is added here) with a 100 ms read timeout: `read` returns
    /// `Ok(0)` when nothing arrived.
    pub fn open(name: &str) -> io::Result<SerialPort> {
        let path = wide(&format!("\\\\.\\{name}"));
        // SAFETY: plain Win32 calls with valid, NUL-terminated and correctly sized arguments; the
        // handle is closed by Drop on every path once the SerialPort exists.
        unsafe {
            let h = CreateFileW(
                path.as_ptr(),
                GENERIC_READ | GENERIC_WRITE,
                0,
                null(),
                OPEN_EXISTING,
                FILE_ATTRIBUTE_NORMAL,
                null_mut(),
            );
            if h == INVALID_HANDLE_VALUE {
                return Err(io::Error::last_os_error());
            }
            let port = SerialPort { handle: h };
            let mut dcb: DCB = std::mem::zeroed();
            dcb.DCBlength = std::mem::size_of::<DCB>() as u32;
            if GetCommState(h, &mut dcb) == 0 {
                return Err(io::Error::last_os_error());
            }
            dcb.BaudRate = 115_200;
            dcb.ByteSize = 8;
            dcb.Parity = 0; // NOPARITY
            dcb.StopBits = 0; // ONESTOPBIT
            // fBinary, fDtrControl = DTR_CONTROL_ENABLE, fRtsControl = RTS_CONTROL_ENABLE; no flow control.
            dcb._bitfield = 1 | (1 << 4) | (1 << 12);
            if SetCommState(h, &dcb) == 0 {
                return Err(io::Error::last_os_error());
            }
            let t = COMMTIMEOUTS {
                ReadIntervalTimeout: u32::MAX,
                ReadTotalTimeoutMultiplier: u32::MAX,
                ReadTotalTimeoutConstant: 100,
                WriteTotalTimeoutMultiplier: 0,
                WriteTotalTimeoutConstant: 1000,
            };
            if SetCommTimeouts(h, &t) == 0 {
                return Err(io::Error::last_os_error());
            }
            PurgeComm(h, PURGE_RXCLEAR | PURGE_TXCLEAR);
            Ok(port)
        }
    }
}

impl Read for SerialPort {
    fn read(&mut self, buf: &mut [u8]) -> io::Result<usize> {
        let mut n = 0u32;
        let len = buf.len().min(u32::MAX as usize) as u32;
        // SAFETY: buf is valid for len bytes and n is a valid out pointer.
        let ok = unsafe { ReadFile(self.handle, buf.as_mut_ptr(), len, &mut n, null_mut()) };
        if ok == 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(n as usize)
        }
    }
}

impl Write for SerialPort {
    fn write(&mut self, buf: &[u8]) -> io::Result<usize> {
        let mut n = 0u32;
        let len = buf.len().min(u32::MAX as usize) as u32;
        // SAFETY: buf is valid for len bytes and n is a valid out pointer.
        let ok = unsafe { WriteFile(self.handle, buf.as_ptr(), len, &mut n, null_mut()) };
        if ok == 0 {
            Err(io::Error::last_os_error())
        } else {
            Ok(n as usize)
        }
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}

impl Drop for SerialPort {
    fn drop(&mut self) {
        // SAFETY: the handle was returned by CreateFileW and is closed exactly once.
        unsafe {
            CloseHandle(self.handle);
        }
    }
}

/// Port names from HKLM\HARDWARE\DEVICEMAP\SERIALCOMM, sorted by number (`COM3`, `COM10`).
pub fn list_ports() -> Vec<String> {
    let mut out = Vec::new();
    let key = wide("HARDWARE\\DEVICEMAP\\SERIALCOMM");
    // SAFETY: registry enumeration with buffers whose sizes are passed alongside.
    unsafe {
        let mut hkey: HKEY = null_mut();
        if RegOpenKeyExW(HKEY_LOCAL_MACHINE, key.as_ptr(), 0, KEY_READ, &mut hkey) != 0 {
            return out;
        }
        for index in 0.. {
            let mut name = [0u16; 256];
            let mut name_len = name.len() as u32;
            let mut ty = 0u32;
            let mut data = [0u8; 256];
            let mut data_len = data.len() as u32;
            let r = RegEnumValueW(
                hkey,
                index,
                name.as_mut_ptr(),
                &mut name_len,
                null_mut(),
                &mut ty,
                data.as_mut_ptr(),
                &mut data_len,
            );
            if r != 0 {
                break; // ERROR_NO_MORE_ITEMS or a real error: stop either way
            }
            if ty == 1 {
                // REG_SZ
                let w: Vec<u16> = data[..data_len as usize].chunks_exact(2).map(|c| u16::from_le_bytes([c[0], c[1]])).collect();
                let s = from_wide(&w);
                if !s.is_empty() {
                    out.push(s);
                }
            }
        }
        RegCloseKey(hkey);
    }
    out.sort_by_key(|n| (com_number(n).unwrap_or(u32::MAX), n.clone()));
    out
}

pub fn com_number(name: &str) -> Option<u32> {
    name.strip_prefix("COM")?.parse().ok()
}
