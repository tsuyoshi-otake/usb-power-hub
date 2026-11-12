//! Command-line options.
//!
//! `--demo`                 connect to the demo device at start-up
//! `--screenshot <file.bmp>` capture the client area after `--after` seconds, then exit
//! `--after <seconds>`      delay for `--screenshot` (default 8)
//! `--log`                  start with the logarithmic current axis
//! `--span <seconds>`       initial width of the visible time window (default 5)
//! `--max-minutes <n>`      recording limit (default 10)

#[derive(Debug, Clone, PartialEq)]
pub struct Config {
    pub demo: bool,
    pub screenshot: Option<String>,
    pub after_s: f64,
    pub log: bool,
    pub max_minutes: f64,
    pub span_s: Option<f64>,
}

impl Default for Config {
    fn default() -> Self {
        Config { demo: false, screenshot: None, after_s: 8.0, log: false, max_minutes: 10.0, span_s: None }
    }
}

impl Config {
    pub fn parse<I: IntoIterator<Item = String>>(args: I) -> Result<Config, String> {
        let mut c = Config::default();
        let mut it = args.into_iter();
        while let Some(a) = it.next() {
            match a.as_str() {
                "--demo" => c.demo = true,
                "--log" => c.log = true,
                "--screenshot" => c.screenshot = Some(it.next().ok_or("--screenshot needs a file name")?),
                "--after" => {
                    c.after_s = it.next().and_then(|v| v.parse().ok()).filter(|v: &f64| *v >= 0.0).ok_or("--after needs seconds")?
                }
                "--span" => {
                    c.span_s = Some(it.next().and_then(|v| v.parse().ok()).filter(|v: &f64| *v >= 0.0007).ok_or("--span needs seconds >= 0.0007")?)
                }
                "--max-minutes" => {
                    c.max_minutes =
                        it.next().and_then(|v| v.parse().ok()).filter(|v: &f64| *v > 0.0 && *v <= 120.0).ok_or("--max-minutes needs 0 < n <= 120")?
                }
                other => return Err(format!("unknown option {other}")),
            }
        }
        if c.screenshot.is_some() && !c.demo {
            return Err("--screenshot needs --demo (there is no device to capture otherwise)".into());
        }
        Ok(c)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn p(s: &str) -> Result<Config, String> {
        Config::parse(s.split_whitespace().map(String::from))
    }

    #[test]
    fn parses_options() {
        let c = p("--demo --screenshot a.bmp --after 3.5 --log --max-minutes 2 --span 0.05").unwrap();
        assert!(c.demo && c.log);
        assert_eq!(c.screenshot.as_deref(), Some("a.bmp"));
        assert_eq!(c.after_s, 3.5);
        assert_eq!(c.max_minutes, 2.0);
        assert_eq!(c.span_s, Some(0.05));
        assert_eq!(p("").unwrap(), Config::default());
    }

    #[test]
    fn rejects_bad_options() {
        assert!(p("--bogus").is_err());
        assert!(p("--after").is_err());
        assert!(p("--after x").is_err());
        assert!(p("--screenshot a.bmp").is_err());
        assert!(p("--max-minutes 0").is_err());
    }
}
