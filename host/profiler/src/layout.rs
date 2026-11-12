//! Window layout in device pixels. Platform independent; `scale` is dpi / 96.

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
pub struct Rect {
    pub l: i32,
    pub t: i32,
    pub r: i32,
    pub b: i32,
}

impl Rect {
    pub fn new(l: i32, t: i32, r: i32, b: i32) -> Rect {
        Rect { l, t, r, b }
    }
    pub fn w(&self) -> i32 {
        self.r - self.l
    }
    pub fn h(&self) -> i32 {
        self.b - self.t
    }
    pub fn contains(&self, x: i32, y: i32) -> bool {
        x >= self.l && x < self.r && y >= self.t && y < self.b
    }
}

pub const LANE_ROWS: i32 = 3;

#[derive(Clone, Debug, Default)]
pub struct Layout {
    pub scale: f64,
    pub panel: Rect,
    pub stats: [Rect; 2],
    /// Chart including its axis labels.
    pub chart: Rect,
    /// Plot area proper (inside the axes).
    pub plot: Rect,
    /// One lane rectangle per visible channel (A first), aligned with the plot's x range.
    pub lanes: Vec<Rect>,
    pub markers: Rect,
    /// One text line explaining the lane colours and markers.
    pub legend: Rect,
    pub minimap: Rect,
    pub status: Rect,
}

impl Layout {
    pub fn px(&self, v: i32) -> i32 {
        (v as f64 * self.scale).round() as i32
    }

    pub fn compute(w: i32, h: i32, scale: f64, visible_channels: usize) -> Layout {
        let mut lay = Layout { scale, ..Default::default() };
        let px = |v: i32| (v as f64 * scale).round() as i32;
        let margin = px(12);
        lay.status = Rect::new(0, h - px(24), w, h);
        lay.panel = Rect::new(0, 0, px(260), lay.status.t);
        let x0 = lay.panel.r + margin;
        let x1 = (w - margin).max(x0 + px(200));
        let half = (x1 - x0 - margin) / 2;
        let stats_h = px(84);
        lay.stats[0] = Rect::new(x0, margin, x0 + half, margin + stats_h);
        lay.stats[1] = Rect::new(x1 - half, margin, x1, margin + stats_h);

        lay.minimap = Rect::new(x0, lay.status.t - px(8) - px(64), x1, lay.status.t - px(8));
        let lane_h = px(LANE_ROWS * 6 + 4);
        let lanes_h = visible_channels as i32 * lane_h + px(12);
        lay.legend = Rect::new(x0, lay.minimap.t - px(6) - px(15), x1, lay.minimap.t - px(6));
        let lanes_b = lay.legend.t - px(2);
        let lanes_t = lanes_b - lanes_h;
        lay.chart = Rect::new(x0, lay.stats[0].b + px(10), x1, lanes_t - px(6));
        lay.plot = Rect::new(chart_left(&lay.chart, scale), lay.chart.t + px(8), lay.chart.r - px(14), lay.chart.b - px(22));
        for i in 0..visible_channels as i32 {
            let t = lanes_t + i * lane_h;
            lay.lanes.push(Rect::new(lay.plot.l, t, lay.plot.r, t + px(LANE_ROWS * 6)));
        }
        lay.markers = Rect::new(lay.plot.l, lanes_b - px(8), lay.plot.r, lanes_b);
        lay
    }
}

fn chart_left(chart: &Rect, scale: f64) -> i32 {
    chart.l + (66.0 * scale).round() as i32
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn regions_do_not_overlap_and_fit() {
        for (w, h, s, n) in [(1280, 800, 1.0, 2), (1920, 1080, 1.5, 1), (900, 600, 1.0, 0), (2560, 1440, 2.0, 2)] {
            let l = Layout::compute(w, h, s, n);
            assert!(l.plot.w() > 100 && l.plot.h() > 50, "{w}x{h}: plot {:?}", l.plot);
            assert!(l.stats[0].b < l.chart.t);
            assert!(l.chart.b <= l.lanes.first().map_or(l.markers.t, |r| r.t));
            assert!(l.markers.b <= l.legend.t);
            assert!(l.legend.b < l.minimap.t);
            assert!(l.minimap.b <= l.status.t);
            assert!(l.stats[0].r < l.stats[1].l);
            assert_eq!(l.lanes.len(), n);
            assert!(l.panel.r < l.plot.l);
        }
    }
}
