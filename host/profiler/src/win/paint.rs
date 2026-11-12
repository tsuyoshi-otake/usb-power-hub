//! Drawing of everything that is not a native control: panel headers, statistics boxes, chart,
//! range lanes, markers, minimap and status bar. Safe code on top of `Canvas`.

use super::canvas::{Align, Canvas, Font};
use super::util::rgb;
use crate::app::{App, Conn, View};
use crate::fmt;
use crate::layout::{Layout, Rect, LANE_ROWS};
use crate::store::{self, Node, Span, Store, MASK_CLIPPED, MASK_SETTLING};

pub const BG_PANEL: u32 = rgb(238, 239, 242);
pub const BG_MAIN: u32 = rgb(247, 248, 250);
const WHITE: u32 = rgb(255, 255, 255);
const BORDER: u32 = rgb(204, 208, 215);
const TEXT: u32 = rgb(32, 36, 44);
const TEXT_DIM: u32 = rgb(100, 106, 118);
const GRID: u32 = rgb(228, 231, 236);
const GRID_MINOR: u32 = rgb(240, 242, 245);
const SEL_FILL: u32 = rgb(214, 230, 252);
const SEL_EDGE: u32 = rgb(70, 120, 210);
const LOST: u32 = rgb(200, 40, 60);
const FAULT: u32 = rgb(150, 0, 20);
const SETTLING: u32 = rgb(0, 150, 136);
const CLIPPED: u32 = rgb(230, 60, 40);
pub const TRACE: [u32; 2] = [rgb(30, 110, 220), rgb(240, 135, 15)];
const TRACE_LIGHT: [u32; 2] = [rgb(170, 200, 242), rgb(248, 205, 150)];
const RANGE_COLOR: [u32; 3] = [rgb(76, 175, 80), rgb(245, 180, 20), rgb(150, 70, 190)]; // LOW, MID, HIGH
const CH_NAME: [&str; 2] = ["A", "B"];

/// A section header of the left panel, placed by the UI module.
pub struct PanelHeader {
    pub text: &'static str,
    pub x: i32,
    pub y: i32,
    pub w: i32,
}

pub fn paint(c: &mut Canvas, app: &App, lay: &Layout, client_w: i32, client_h: i32, headers: &[PanelHeader]) {
    c.fill(Rect::new(0, 0, client_w, client_h), BG_MAIN);
    paint_panel(c, lay, headers);
    let rows = app.visible_channels();
    for (i, title) in ["WINDOW", "SELECTION"].iter().enumerate() {
        let (stats, span_us) = if i == 0 {
            ([app.window_stats(0), app.window_stats(1)], Some(app.view.span))
        } else {
            let s = [app.selection_stats(0), app.selection_stats(1)];
            (s, app.selection.map(|(a, b)| b - a))
        };
        paint_stats(c, lay, lay.stats[i], title, span_us, &stats, &rows);
    }
    paint_chart(c, app, lay);
    paint_lanes(c, app, lay);
    paint_minimap(c, app, lay);
    paint_status(c, app, lay);
}

fn paint_panel(c: &mut Canvas, lay: &Layout, headers: &[PanelHeader]) {
    c.fill(lay.panel, BG_PANEL);
    c.vline(lay.panel.r - 1, lay.panel.t, lay.panel.b, BORDER);
    for h in headers {
        c.text(h.x, h.y, h.text, TEXT_DIM, Font::Header, Align::Left);
        let ty = h.y + c.text_height(Font::Header) + lay.px(2);
        c.hline(h.x, h.x + h.w, ty, BORDER);
    }
}

fn paint_stats(c: &mut Canvas, lay: &Layout, r: Rect, title: &str, span_us: Option<f64>, stats: &[Option<store::Stats>; 2], rows: &[usize]) {
    let px = |v: i32| lay.px(v);
    c.fill(r, WHITE);
    c.outline(r, BORDER);
    c.text(r.l + px(10), r.t + px(6), title, TEXT_DIM, Font::Header, Align::Left);
    if let Some(s) = span_us {
        c.text(r.r - px(10), r.t + px(6), &fmt::duration(s), TEXT_DIM, Font::Small, Align::Right);
    }
    let x0 = r.l + px(34);
    let cw = (r.r - px(10) - x0) / 4;
    for (i, h) in ["Average", "Max", "Duration", "Charge"].iter().enumerate() {
        c.text(x0 + i as i32 * cw, r.t + px(26), h, TEXT_DIM, Font::Small, Align::Left);
    }
    for (k, &ch) in rows.iter().enumerate() {
        let y = r.t + px(44) + k as i32 * px(18);
        c.text(r.l + px(12), y, CH_NAME[ch], TRACE[ch], Font::Bold, Align::Left);
        let vals: [String; 4] = match &stats[ch] {
            Some(s) => [
                fmt::si(s.average, "A"),
                fmt::si(s.max, "A"),
                fmt::duration(s.duration_s * 1e6),
                fmt::si(s.charge, "C"),
            ],
            None => ["-".into(), "-".into(), "-".into(), "-".into()],
        };
        for (i, v) in vals.iter().enumerate() {
            c.text(x0 + i as i32 * cw, y, v, TEXT, Font::Normal, Align::Left);
        }
    }
}

fn paint_axes(c: &mut Canvas, v: &View, plot: &Rect, lay: &Layout, len_us: f64) {
    let _ = len_us;
    let ph = plot.h() as f64;
    // current axis
    if v.log {
        let (d0, d1) = (v.y0.log10().ceil() as i32, v.y1.log10().floor() as i32);
        let decade_px = ph / (v.y1.log10() - v.y0.log10()).max(1e-9);
        for d in (d0 - 1)..=(d1 + 1) {
            if decade_px > 36.0 {
                for m in [2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0] {
                    let val = m * 10f64.powi(d);
                    if val > v.y0 && val < v.y1 {
                        let y = v.v_to_y(val, plot).round() as i32;
                        c.hline(plot.l, plot.r, y, GRID_MINOR);
                    }
                }
            }
            let val = 10f64.powi(d);
            if val >= v.y0 * 0.9999 && val <= v.y1 * 1.0001 {
                let y = v.v_to_y(val, plot).round() as i32;
                c.hline(plot.l, plot.r, y, GRID);
                c.text(plot.l - lay.px(6), y - lay.px(7), &fmt::amp_decade(val), TEXT_DIM, Font::Small, Align::Right);
            }
        }
    } else {
        let step = fmt::nice_step(v.y1 - v.y0, (ph / lay.px(46) as f64).max(2.0));
        let mut k = (v.y0 / step).ceil();
        while k * step <= v.y1 + step * 1e-9 {
            let val = k * step;
            let y = v.v_to_y(val, plot).round() as i32;
            c.hline(plot.l, plot.r, y, GRID);
            c.text(plot.l - lay.px(6), y - lay.px(7), &fmt::amp_tick(val, step), TEXT_DIM, Font::Small, Align::Right);
            k += 1.0;
        }
    }
    // time axis
    let step = fmt::nice_step(v.span, (plot.w() as f64 / lay.px(100) as f64).max(2.0));
    let mut k = (v.t0 / step).ceil();
    while k * step <= v.t0 + v.span {
        let t = k * step;
        let x = v.t_to_x(t, plot).round() as i32;
        c.vline(x, plot.t, plot.b, GRID);
        c.text(x, plot.b + lay.px(4), &fmt::time_tick(t, step), TEXT_DIM, Font::Small, Align::Center);
        k += 1.0;
    }
}

fn span_x(v: &View, plot: &Rect, s: &Span) -> (i32, i32) {
    let a = v.t_to_x(store::time_us(s.start) as f64, plot).floor() as i32;
    let b = v.t_to_x(store::time_us(s.end) as f64, plot).ceil() as i32;
    (a, b.max(a + 5))
}

fn paint_chart(c: &mut Canvas, app: &App, lay: &Layout) {
    let plot = lay.plot;
    let v = &app.view;
    c.fill(plot, WHITE);
    paint_axes(c, v, &plot, lay, app.len_us());
    c.clip(plot);
    // selection behind the traces
    if let Some((a, b)) = app.selection {
        let (xa, xb) = (v.t_to_x(a, &plot).round() as i32, v.t_to_x(b, &plot).round() as i32);
        c.fill(Rect::new(xa, plot.t, xb.max(xa + 1), plot.b), SEL_FILL);
        c.vline(xa, plot.t, plot.b, SEL_EDGE);
        c.vline(xb, plot.t, plot.b, SEL_EDGE);
    }
    let (i0, i1) = app.window_range();
    for ch in 0..2 {
        if app.show[ch] {
            paint_trace(c, &app.store, ch, v, &plot, i0, i1);
        }
    }
    // lost data is never bridged: mark it across the whole plot
    for s in Store::spans_in(&app.store.lost, i0, i1.max(i0 + 1)) {
        let (xa, xb) = span_x(v, &plot, s);
        c.hatch(Rect::new(xa, plot.t, xb, plot.b), LOST);
        c.vline(xa, plot.t, plot.b, LOST);
        c.vline(xb - 1, plot.t, plot.b, LOST);
    }
    c.unclip();
    if let Some((a, b)) = app.selection {
        let xa = v.t_to_x(a, &plot).round() as i32;
        let xb = v.t_to_x(b, &plot).round() as i32;
        let label = fmt::duration(b - a);
        let cx = ((xa + xb) / 2).clamp(plot.l + lay.px(30), plot.r - lay.px(30));
        c.text(cx, plot.t + lay.px(3), &label, SEL_EDGE, Font::Small, Align::Center);
    }
    c.outline(plot, BORDER);
    if app.store.len() == 0 {
        let msg = match app.conn {
            Conn::Connected => "Waiting for samples...",
            _ => "Not connected: pick a port or the demo device and press Connect",
        };
        c.text((plot.l + plot.r) / 2, (plot.t + plot.b) / 2 - lay.px(8), msg, TEXT_DIM, Font::Normal, Align::Center);
    }
}

fn paint_trace(c: &mut Canvas, store: &Store, ch: usize, v: &View, plot: &Rect, i0: u64, i1: u64) {
    let chan = &store.ch[ch];
    let n = i1.saturating_sub(i0);
    let to_pt = |t_us: f64, a: f64| (v.t_to_x(t_us, plot).round() as i32, v.v_to_y(a, plot).round() as i32);
    if n as i32 <= plot.w() * 2 {
        // few samples per pixel: draw the samples themselves, broken at lost data
        let mut run: Vec<(i32, i32)> = Vec::new();
        let flush = |c: &mut Canvas, run: &mut Vec<(i32, i32)>| {
            match run.len() {
                0 => {}
                1 => c.fill(Rect::new(run[0].0 - 1, run[0].1 - 1, run[0].0 + 2, run[0].1 + 2), TRACE[ch]),
                _ => c.polyline(run, TRACE[ch], 1),
            }
            run.clear();
        };
        let dots = (n as i32) < plot.w() / 3;
        for i in i0.saturating_sub(1)..i1.min(chan.len()) {
            match chan.amps_at(i) {
                Some(a) => {
                    let p = to_pt(store::time_us(i) as f64, a);
                    run.push(p);
                    if dots {
                        c.fill(Rect::new(p.0 - 1, p.1 - 1, p.0 + 2, p.1 + 2), TRACE[ch]);
                    }
                }
                None => flush(c, &mut run),
            }
        }
        flush(c, &mut run);
        return;
    }
    // many samples per pixel: one min/max envelope per pixel column, plus the column mean
    let mut mean: Vec<(i32, i32)> = Vec::new();
    for x in plot.l..plot.r {
        let ia = store::index_at(v.x_to_t(x as f64, plot));
        if ia >= chan.len() {
            break;
        }
        let ib = store::index_at(v.x_to_t(x as f64 + 1.0, plot)).max(ia + 1);
        let n = chan.query(ia, ib);
        let Some(m) = n.mean() else {
            if mean.len() > 1 {
                c.polyline(&mean, TRACE[ch], 1);
            }
            mean.clear();
            continue;
        };
        let ytop = v.v_to_y(n.max as f64, plot).round() as i32;
        let ybot = v.v_to_y(n.min as f64, plot).round() as i32;
        c.fill(Rect::new(x, ytop.min(ybot), x + 1, ytop.max(ybot) + 1), TRACE_LIGHT[ch]);
        mean.push((x, v.v_to_y(m, plot).round() as i32));
    }
    if mean.len() > 1 {
        c.polyline(&mean, TRACE[ch], 1);
    }
}

fn paint_lanes(c: &mut Canvas, app: &App, lay: &Layout) {
    let plot = lay.plot;
    let v = &app.view;
    let row_h = lay.px(6);
    let rows = app.visible_channels();
    let mut union = vec![Node::EMPTY; plot.w().max(0) as usize];
    for (k, &ch) in rows.iter().enumerate() {
        let lane = lay.lanes[k];
        let th = c.text_height(Font::Bold);
        c.text(plot.l - lay.px(8), lane.t + (lane.h() - th) / 2, CH_NAME[ch], TRACE[ch], Font::Bold, Align::Right);
        c.fill(lane, rgb(236, 238, 242));
        for x in plot.l..plot.r {
            let ia = store::index_at(v.x_to_t(x as f64, &plot));
            let ib = store::index_at(v.x_to_t(x as f64 + 1.0, &plot)).max(ia + 1);
            let n = app.store.ch[ch].query(ia, ib);
            if n.count == 0 {
                continue;
            }
            union[(x - plot.l) as usize].merge(&n);
            for r in 0..3 {
                if n.mask & (1 << r) != 0 {
                    // HIGH on the top row, LOW on the bottom row
                    let y = lane.t + (LANE_ROWS - 1 - r) * row_h;
                    c.fill(Rect::new(x, y, x + 1, y + row_h - 1), RANGE_COLOR[r as usize]);
                }
            }
        }
        c.outline(lane, BORDER);
    }
    // marker row: settling and clipped samples, fault and lost spans
    let m = lay.markers;
    c.fill(m, rgb(236, 238, 242));
    let half = m.h() / 2;
    for (i, n) in union.iter().enumerate() {
        let x = plot.l + i as i32;
        if n.mask & MASK_SETTLING != 0 {
            c.fill(Rect::new(x, m.t, x + 1, m.t + half), SETTLING);
        }
        if n.mask & MASK_CLIPPED != 0 {
            c.fill(Rect::new(x, m.t, x + 1, m.t + half), CLIPPED);
        }
    }
    let (i0, i1) = app.window_range();
    let lo = store::index_at(v.t0);
    let _ = i0;
    c.clip(Rect::new(plot.l, m.t, plot.r, m.b));
    for ch in 0..2 {
        if !app.show[ch] {
            continue;
        }
        for s in Store::spans_in(&app.store.fault[ch], lo, i1.max(lo + 1)) {
            let (xa, xb) = span_x(v, &plot, s);
            c.fill(Rect::new(xa, m.t + half, xb, m.b), FAULT);
        }
    }
    let top = lay.lanes.first().map_or(m.t, |l| l.t);
    for s in Store::spans_in(&app.store.lost, lo, i1.max(lo + 1)) {
        let (xa, xb) = span_x(v, &plot, s);
        c.hatch(Rect::new(xa, top, xb, m.b), LOST);
        c.fill(Rect::new(xa, m.t + half, xb, m.b), LOST);
    }
    c.unclip();
    c.outline(m, BORDER);

    // legend
    let l = lay.legend;
    let mut x = l.l;
    let y = l.t + lay.px(1);
    let sq = lay.px(8);
    let item = |c: &mut Canvas, color: u32, hatch: bool, text: &str, x: &mut i32| {
        let r = Rect::new(*x, y + lay.px(3), *x + sq, y + lay.px(3) + sq);
        if hatch {
            c.fill(r, WHITE);
            c.hatch(r, color);
            c.outline(r, color);
        } else {
            c.fill(r, color);
        }
        c.text(*x + sq + lay.px(4), y, text, TEXT_DIM, Font::Small, Align::Left);
        *x += sq + lay.px(4) + c.text_width(text, Font::Small) + lay.px(14);
    };
    c.text(x, y, "Range:", TEXT_DIM, Font::Small, Align::Left);
    x += c.text_width("Range:", Font::Small) + lay.px(8);
    item(c, RANGE_COLOR[0], false, "LOW", &mut x);
    item(c, RANGE_COLOR[1], false, "MID", &mut x);
    item(c, RANGE_COLOR[2], false, "HIGH", &mut x);
    x += lay.px(10);
    c.text(x, y, "Markers:", TEXT_DIM, Font::Small, Align::Left);
    x += c.text_width("Markers:", Font::Small) + lay.px(8);
    item(c, SETTLING, false, "settling", &mut x);
    item(c, CLIPPED, false, "clipped", &mut x);
    item(c, FAULT, false, "fault (port opened)", &mut x);
    item(c, LOST, true, "lost data", &mut x);
}

fn paint_minimap(c: &mut Canvas, app: &App, lay: &Layout) {
    let r = lay.minimap;
    c.fill(r, WHITE);
    let len = app.store.len();
    let len_us = app.len_us();
    if len == 0 {
        c.outline(r, BORDER);
        c.text((r.l + r.r) / 2, (r.t + r.b) / 2 - lay.px(7), "Overview of the recording", TEXT_DIM, Font::Small, Align::Center);
        return;
    }
    // window position
    let w = r.w() as f64;
    let wx0 = (r.l as f64 + app.view.t0 / len_us * w).round() as i32;
    let wx1 = (r.l as f64 + (app.view.t0 + app.view.span) / len_us * w).round() as i32;
    c.fill(Rect::new(wx0.max(r.l), r.t, wx1.min(r.r).max(wx0 + 2), r.b), SEL_FILL);
    // log scale from 100 nA to the largest value seen
    let mut gmax = 1e-6f64;
    for ch in 0..2 {
        if app.show[ch] {
            gmax = gmax.max(app.store.ch[ch].query(0, len).max as f64);
        }
    }
    let hi = gmax.log10().ceil();
    let lo = hi - (hi + 7.0).clamp(2.0, 7.0); // down to 100 nA, but at least 2 decades
    let inner = Rect::new(r.l + 1, r.t + lay.px(3), r.r - 1, r.b - lay.px(3));
    let ymap = |a: f64| -> i32 {
        let f = ((a.max(1e-12).log10() - lo) / (hi - lo)).clamp(0.0, 1.0);
        (inner.b as f64 - f * inner.h() as f64).round() as i32
    };
    for ch in 0..2 {
        if !app.show[ch] {
            continue;
        }
        let mut mean = Vec::new();
        for x in r.l..r.r {
            let ia = ((x - r.l) as f64 / w * len as f64) as u64;
            let ib = (((x - r.l + 1) as f64 / w * len as f64) as u64).max(ia + 1);
            let n = app.store.ch[ch].query(ia, ib);
            let Some(m) = n.mean() else {
                if mean.len() > 1 {
                    c.polyline(&mean, TRACE[ch], 1);
                }
                mean.clear();
                continue;
            };
            let (yt, yb) = (ymap(n.max as f64), ymap(n.min as f64));
            c.fill(Rect::new(x, yt.min(yb), x + 1, yt.max(yb) + 1), TRACE_LIGHT[ch]);
            mean.push((x, ymap(m)));
        }
        if mean.len() > 1 {
            c.polyline(&mean, TRACE[ch], 1);
        }
    }
    for s in &app.store.lost {
        let xa = r.l + (store::time_us(s.start) as f64 / len_us * w) as i32;
        let xb = r.l + (store::time_us(s.end) as f64 / len_us * w) as i32;
        c.fill(Rect::new(xa, r.t, xb.max(xa + 1), r.b), LOST);
    }
    c.outline(Rect::new(wx0, r.t, wx1.max(wx0 + 2), r.b), SEL_EDGE);
    c.outline(Rect::new(wx0 + 1, r.t + 1, wx1.max(wx0 + 2) - 1, r.b - 1), SEL_EDGE);
    c.outline(r, BORDER);
    c.text(r.r - lay.px(6), r.t + lay.px(3), &fmt::duration(len_us), TEXT_DIM, Font::Small, Align::Right);
}

fn paint_status(c: &mut Canvas, app: &App, lay: &Layout) {
    let r = lay.status;
    c.fill(r, rgb(226, 229, 234));
    c.hline(r.l, r.r, r.t, BORDER);
    let ty = r.t + (r.h() - c.text_height(Font::Small)) / 2;
    c.text(r.l + lay.px(10), ty, &app.status_left(), TEXT, Font::Small, Align::Left);
    c.text(r.r - lay.px(10), ty, &app.status_right(), TEXT, Font::Small, Align::Right);
}
