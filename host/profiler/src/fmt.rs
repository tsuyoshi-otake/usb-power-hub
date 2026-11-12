//! Number formatting with SI prefixes and "nice" axis steps.

const PREFIXES: [(&str, f64); 4] = [("n", 1e-9), ("µ", 1e-6), ("m", 1e-3), ("", 1.0)];

fn prefix_for(a: f64) -> (&'static str, f64) {
    prefix_biased(a, 1.0)
}

/// Smallest-unit prefix whose scale is at most `a * bias` (a tolerance of 1e-6 absorbs the
/// rounding of values such as 10^-6 computed by powi).
fn prefix_biased(a: f64, bias: f64) -> (&'static str, f64) {
    let mut best = PREFIXES[0];
    for p in PREFIXES {
        if a * bias * 1.000001 >= p.1 {
            best = p;
        }
    }
    best
}

/// Three significant digits with an SI prefix: `3.000 µA`, `45.0 mA`, `1.30 A`.
pub fn si(v: f64, unit: &str) -> String {
    if v == 0.0 {
        return format!("0 {unit}");
    }
    let (p, s) = prefix_for(v.abs());
    let x = v / s;
    let d = if x.abs() >= 100.0 { 1 } else if x.abs() >= 10.0 { 2 } else { 3 };
    format!("{x:.d$} {p}{unit}")
}

/// Duration: `812 µs`, `5.000 ms`, `12.50 s`.
pub fn duration(us: f64) -> String {
    let a = us.abs();
    let (x, u) = if a < 1000.0 { (us, "µs") } else if a < 1e6 { (us / 1e3, "ms") } else { (us / 1e6, "s") };
    let d = if x.abs() >= 100.0 { 1 } else if x.abs() >= 10.0 { 2 } else { 3 };
    format!("{x:.d$} {u}")
}

/// 1, 2, 5 x 10^k step giving about `target` steps over `range`.
pub fn nice_step(range: f64, target: f64) -> f64 {
    let raw = (range / target.max(1.0)).max(f64::MIN_POSITIVE);
    let mag = 10f64.powf(raw.log10().floor());
    let m = raw / mag;
    let f = if m < 1.5 { 1.0 } else if m < 3.5 { 2.0 } else if m < 7.5 { 5.0 } else { 10.0 };
    f * mag
}

fn decimals(step_in_unit: f64) -> usize {
    if step_in_unit >= 1.0 {
        0
    } else {
        ((-step_in_unit.log10()).ceil() as i64).clamp(0, 6) as usize
    }
}

/// Axis label of a value on a linear axis whose ticks are `step` apart; all labels of the axis
/// share one prefix and one number of decimals.
pub fn amp_tick(v: f64, step: f64) -> String {
    let (p, s) = prefix_biased(step, 10.0);
    let x = if v.abs() < step * 1e-6 { 0.0 } else { v / s };
    format!("{:.*} {p}A", decimals(step / s), x)
}

/// Axis label for a decade tick on a log axis.
pub fn amp_decade(v: f64) -> String {
    let (p, s) = prefix_for(v.abs());
    let x = v / s;
    format!("{} {p}A", if (1.0..1e4).contains(&x) { format!("{}", x.round() as i64) } else { format!("{x}") })
}

/// Time axis label (relative to the start of the recording).
pub fn time_tick(t_us: f64, step_us: f64) -> String {
    let (s, u) = if step_us >= 5e5 {
        (1e6, "s")
    } else if step_us >= 100.0 {
        (1e3, "ms")
    } else {
        (1.0, "µs")
    };
    format!("{:.*} {u}", decimals(step_us / s), t_us / s)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn si_prefixes() {
        assert_eq!(si(3e-6, "A"), "3.000 µA");
        assert_eq!(si(0.045, "A"), "45.00 mA");
        assert_eq!(si(1.305, "A"), "1.305 A");
        assert_eq!(si(0.0, "A"), "0 A");
        assert_eq!(si(61.5e-3, "C"), "61.50 mC");
        assert_eq!(si(5e-11, "A"), "0.050 nA");
        assert_eq!(si(-2e-3, "A"), "-2.000 mA");
    }

    #[test]
    fn durations() {
        assert_eq!(duration(812.0), "812.0 µs");
        assert_eq!(duration(5000.0), "5.000 ms");
        assert_eq!(duration(12.5e6), "12.50 s");
    }

    #[test]
    fn ticks() {
        assert_eq!(nice_step(100.0, 5.0), 20.0);
        assert_eq!(nice_step(0.7, 5.0), 0.1);
        assert_eq!(amp_tick(0.04, 0.02), "40 mA");
        assert_eq!(amp_tick(0.0, 0.02), "0 mA");
        assert_eq!(amp_tick(2.5e-6, 5e-7), "2.5 µA");
        assert_eq!(amp_decade(1e-6), "1 µA");
        assert_eq!(amp_decade(1e-1), "100 mA");
        assert_eq!(time_tick(1500.0, 500.0), "1.5 ms");
        assert_eq!(time_tick(3e6, 1e6), "3 s");
    }
}
