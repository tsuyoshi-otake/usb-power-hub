# USB Power Profiler (host app, issue #9)

A native Windows application that records and plots the two current channels of the USB
Power-Control Hub, switches its ports and exports the samples as CSV. It is written in Rust
against the Win32 API directly (`windows-sys`); there is no GUI framework. The layout and
functions follow the usual power-profiler pattern: device and port controls on the left, a
live current plot with window and selection statistics, range and marker lanes, and an
overview strip of the whole recording.

It contains no code, name or artwork of any other profiler. It speaks only this board's
protocol: the control protocol of `requirements/product.md` §4.1 and the stream framing of
§4.2, which `src/protocol.rs` implements and tests.

## State

- **Firmware does not exist yet**, so the app has only been run against its built-in demo
  device (`src/demo.rs`), which produces the §4.2 stream with injected CRC errors and lost
  frames.
- Not verified: serial I/O with a real board, UI clicks and mouse handling in the running
  window (the logic is unit-tested in `src/app.rs`, the window itself only by screenshot),
  high-DPI displays. "Save all as CSV" writes on the UI thread, so a long recording blocks
  the window while it is written.
- Windows 10/11 only.

## Build and run

Needs a Rust toolchain with the MSVC target (checked with rustc 1.96.0). From this directory:

```sh
cargo test --release                 # 38 unit tests
cargo build --release                # target/release/usb-power-profiler.exe
target/release/usb-power-profiler.exe --demo
```

Options: `--demo` (connect to the demo device), `--screenshot <file.bmp>` with `--after <s>`
(capture the window and exit; needs `--demo`), `--log` (logarithmic current axis),
`--span <s>` (initial window width), `--max-minutes <n>` (recording limit).

With a board: pick its control port (`COMn`) in the DEVICE list and press Connect; the app
opens the stream port as `COMn+1` (REQ-HOST-01) and starts recording.

## Use

| Action | Effect |
|---|---|
| Left drag on the plot | select a time span; the SELECTION box shows its average, max, duration and charge |
| Left click on the plot | clear the selection |
| Right drag on the plot | pan (stops following the live edge) |
| Wheel / Ctrl + wheel | zoom time / zoom current |
| Click or drag on the overview strip | move the window there |
| Double click | back to the live 5 s window |
| Turn ON/OFF, CYCLE | `PORT x ON/OFF/CYCLE` |
| Range | `RANGE x AUTO/LOW/MID/HIGH` |

Charge is the sum of the samples divided by 14,000 per second; lost data is excluded from
it and drawn as a hatched band. CSV columns: `time_us,A_current_A,A_range,A_flags,B_current_A,B_range,B_flags`.

## Layout

| Path | What it holds |
|---|---|
| `src/protocol.rs` | stream frame parser and encoder, CRC, `CAL?` parsing |
| `src/store.rs` | sample storage, min/max/sum pyramid for O(log n) queries, lost-data and fault spans, CSV |
| `src/app.rs` | view state, statistics, mouse logic (platform independent) |
| `src/device.rs`, `src/demo.rs` | device sessions: serial ports and the demo device |
| `src/win/` | the Win32 layer, the only `unsafe` code (`#![deny(unsafe_code)]` elsewhere) |
