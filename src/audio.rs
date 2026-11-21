use crate::downloader::get_ffmpeg_path;
use once_cell::sync::Lazy;
use regex::Regex;
use std::collections::HashMap;
use std::io::{BufRead, BufReader};
use std::path::Path;
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

pub const SAMPLE_RATE: u32 = 44100;

pub static EXPORT_CODECS: Lazy<HashMap<&'static str, Vec<&'static str>>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert("mp3", vec!["-c:a", "libmp3lame"]);
    m.insert("m4a", vec!["-c:a", "aac"]);
    m.insert("wav", vec!["-c:a", "pcm_s16le"]);
    m.insert("flac", vec!["-c:a", "flac", "-sample_fmt", "s16"]);
    m
});

pub static COVER_FORMATS: &[&str] = &["mp3", "m4a", "flac"];

#[derive(Debug, Clone, PartialEq)]
pub struct AudioInfo {
    pub duration: f64,
    pub title: String,
    pub artist: String,
    pub has_cover: bool,
}

#[derive(Debug, Clone, PartialEq)]
pub struct ClipSpec {
    pub path: String,
    pub start: f64,
    pub end: f64,
}

impl ClipSpec {
    pub fn new<S: Into<String>>(path: S, start: f64, end: f64) -> Self {
        Self {
            path: path.into(),
            start,
            end,
        }
    }

    pub fn length(&self) -> f64 {
        (self.end - self.start).max(0.0)
    }
}

pub fn format_time(seconds: f64, precise: bool) -> String {
    let sec = seconds.max(0.0);
    let hours = (sec / 3600.0).floor() as u64;
    let rem = sec % 3600.0;
    let minutes = (rem / 60.0).floor() as u64;
    let secs = rem % 60.0;

    if precise {
        let sec_str = format!("{:04.1}", secs);
        if hours >= 1 {
            format!("{}:{:02}:{}", hours, minutes, sec_str)
        } else {
            format!("{}:{}", minutes, sec_str)
        }
    } else {
        let sec_int = secs.floor() as u64;
        if hours >= 1 {
            format!("{}:{:02}:{:02}", hours, minutes, sec_int)
        } else {
            format!("{}:{:02}", minutes, sec_int)
        }
    }
}

pub fn parse_time(text: &str) -> Result<f64, String> {
    let cleaned = text.trim().replace(',', ".");
    if cleaned.is_empty() {
        return Err("empty time".to_string());
    }
    let parts: Vec<&str> = cleaned.split(':').collect();
    if parts.len() > 3 {
        return Err(text.to_string());
    }

    let mut total = 0.0;
    for part in parts {
        let val: f64 = part.parse().map_err(|_| text.to_string())?;
        if val < 0.0 {
            return Err(text.to_string());
        }
        total = total * 60.0 + val;
    }
    Ok(total)
}

pub fn effective_crossfade(clips: &[ClipSpec], crossfade: f64) -> f64 {
    if clips.len() < 2 || crossfade <= 0.0 {
        return 0.0;
    }
    let min_len = clips
        .iter()
        .map(|c| c.length())
        .fold(f64::INFINITY, f64::min);
    crossfade.min(min_len / 2.0 - 0.05).max(0.0)
}

pub fn output_duration(clips: &[ClipSpec], crossfade: f64) -> f64 {
    let total: f64 = clips.iter().map(|c| c.length()).sum();
    let xf = effective_crossfade(clips, crossfade);
    (total - xf * (clips.len() - 1) as f64).max(0.0)
}

pub fn probe<P: AsRef<Path>>(path: P) -> Result<AudioInfo, String> {
    let ffmpeg = get_ffmpeg_path().ok_or_else(|| "FFmpeg not found".to_string())?;
    let output = Command::new(&ffmpeg)
        .args(["-hide_banner", "-i", &path.as_ref().to_string_lossy()])
        .output()
        .map_err(|e| format!("Failed to run ffmpeg: {}", e))?;

    let stderr = String::from_utf8_lossy(&output.stderr);
    let dur_re = Regex::new(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)").unwrap();
    let caps = dur_re
        .captures(&stderr)
        .ok_or_else(|| "Could not find duration in audio file".to_string())?;

    let h: f64 = caps[1].parse().unwrap_or(0.0);
    let m: f64 = caps[2].parse().unwrap_or(0.0);
    let s: f64 = caps[3].parse().unwrap_or(0.0);
    let duration = h * 3600.0 + m * 60.0 + s;

    let has_cover = stderr.contains("(attached pic)");

    let header = stderr.split("Stream #").next().unwrap_or("");
    let tag_re = Regex::new(r"(?m)^\s{4}(\w+)\s*:\s?(.*)$").unwrap();
    let mut title = String::new();
    let mut artist = String::new();

    for tag_caps in tag_re.captures_iter(header) {
        let key = tag_caps[1].to_lowercase();
        let val = tag_caps[2].trim().to_string();
        if key == "title" {
            title = val;
        } else if key == "artist" {
            artist = val;
        }
    }

    Ok(AudioInfo {
        duration,
        title,
        artist,
        has_cover,
    })
}

#[allow(clippy::chunks_exact_to_as_chunks)]
pub fn load_peaks<P: AsRef<Path>>(
    path: P,
    duration: f64,
    buckets: usize,
) -> Result<Vec<f32>, String> {
    let ffmpeg = get_ffmpeg_path().ok_or_else(|| "FFmpeg not found".to_string())?;
    let rate = (2_000_000.0 / duration.max(1.0))
        .round()
        .clamp(400.0, 8000.0) as u32;

    let output = Command::new(&ffmpeg)
        .args([
            "-v",
            "error",
            "-i",
            &path.as_ref().to_string_lossy(),
            "-vn",
            "-ac",
            "1",
            "-ar",
            &rate.to_string(),
            "-f",
            "s16le",
            "-",
        ])
        .output()
        .map_err(|e| format!("FFmpeg failed: {}", e))?;

    let bytes = output.stdout;
    let sample_count = bytes.len() / 2;
    if sample_count == 0 {
        return Ok(vec![0.0; buckets]);
    }

    let mut samples = Vec::with_capacity(sample_count);
    for chunk in bytes.chunks_exact(2) {
        let s = i16::from_le_bytes([chunk[0], chunk[1]]);
        samples.push(s);
    }

    let step = (samples.len() / buckets).max(1);
    let mut peaks = Vec::with_capacity(buckets);

    for chunk in samples.chunks(step) {
        let max_val = chunk
            .iter()
            .copied()
            .map(|x| (x as f32).abs())
            .fold(0.0f32, f32::max);
        peaks.push(max_val / 32768.0);
    }

    let top = peaks.iter().copied().fold(0.0f32, f32::max).max(1.0);
    for p in &mut peaks {
        *p /= top;
    }

    Ok(peaks)
}

#[allow(clippy::too_many_arguments)]
pub fn build_export_command(
    clips: &[ClipSpec],
    out_path: &str,
    fmt: &str,
    bitrate: &str,
    fade_in: f64,
    fade_out: f64,
    gain_db: f64,
    crossfade: f64,
    normalize: bool,
    title: &str,
    artist: &str,
    keep_cover: bool,
) -> Result<Vec<String>, String> {
    if clips.is_empty() {
        return Err("no clips".to_string());
    }
    if !EXPORT_CODECS.contains_key(fmt) {
        return Err(format!("unsupported format {}", fmt));
    }
    let ffmpeg = get_ffmpeg_path()
        .map(|p| p.to_string_lossy().to_string())
        .unwrap_or_else(|| "ffmpeg".to_string());

    let mut cmd = vec![ffmpeg, "-hide_banner".to_string(), "-y".to_string()];

    for clip in clips {
        cmd.extend([
            "-ss".to_string(),
            format!("{:.3}", clip.start),
            "-t".to_string(),
            format!("{:.3}", clip.length()),
            "-i".to_string(),
            clip.path.clone(),
        ]);
    }

    let mut filters = Vec::new();
    for i in 0..clips.len() {
        filters.push(format!(
            "[{}:a:0]aresample={},aformat=sample_fmts=fltp:channel_layouts=stereo,asetnsamples=n=1024:p=0[c{}]",
            i, SAMPLE_RATE, i
        ));
    }

    let xf = effective_crossfade(clips, crossfade);
    let joined = if clips.len() == 1 {
        "c0".to_string()
    } else if xf > 0.0 {
        let mut prev = "c0".to_string();
        for i in 1..clips.len() {
            let next_tag = format!("x{}", i);
            filters.push(format!(
                "[{}][c{}]acrossfade=d={:.3}:c1=tri:c2=tri[{}]",
                prev, i, xf, next_tag
            ));
            prev = next_tag;
        }
        prev
    } else {
        let mut inputs = String::new();
        for i in 0..clips.len() {
            inputs.push_str(&format!("[c{}]", i));
        }
        filters.push(format!("{}concat=n={}:v=0:a=1[j]", inputs, clips.len()));
        "j".to_string()
    };

    let total = output_duration(clips, crossfade);
    let mut effects = Vec::new();

    if fade_in > 0.0 {
        effects.push(format!("afade=t=in:st=0:d={:.3}", fade_in.min(total)));
    }
    if fade_out > 0.0 {
        let fo = fade_out.min(total);
        effects.push(format!(
            "afade=t=out:st={:.3}:d={:.3}",
            (total - fo).max(0.0),
            fo
        ));
    }
    if gain_db.abs() > 0.001 {
        effects.push(format!("volume={:+.1}dB", gain_db));
    }
    if normalize {
        effects.push("loudnorm=I=-14:TP=-1.5:LRA=11".to_string());
    }
    effects.push(format!("aresample={}", SAMPLE_RATE));

    filters.push(format!("[{}]{}[out]", joined, effects.join(",")));

    cmd.push("-filter_complex".to_string());
    cmd.push(filters.join(";"));

    cmd.push("-map".to_string());
    cmd.push("[out]".to_string());

    if keep_cover && COVER_FORMATS.contains(&fmt) {
        cmd.extend([
            "-map".to_string(),
            "0:v:0?".to_string(),
            "-c:v".to_string(),
            "copy".to_string(),
            "-disposition:v:0".to_string(),
            "attached_pic".to_string(),
            "-metadata:s:v".to_string(),
            "title=Album cover".to_string(),
            "-metadata:s:v".to_string(),
            "comment=Cover (front)".to_string(),
        ]);
    }

    if let Some(codec_args) = EXPORT_CODECS.get(fmt) {
        for arg in codec_args {
            cmd.push(arg.to_string());
        }
    }

    if fmt == "mp3" {
        cmd.extend([
            "-b:a".to_string(),
            format!("{}k", bitrate),
            "-id3v2_version".to_string(),
            "3".to_string(),
            "-write_id3v1".to_string(),
            "1".to_string(),
        ]);
    } else if fmt == "m4a" {
        cmd.extend(["-b:a".to_string(), "256k".to_string()]);
    }

    cmd.extend([
        "-ar".to_string(),
        SAMPLE_RATE.to_string(),
        "-map_metadata".to_string(),
        "-1".to_string(),
        "-map_chapters".to_string(),
        "-1".to_string(),
    ]);

    if !title.is_empty() {
        cmd.extend(["-metadata".to_string(), format!("title={}", title)]);
    }
    if !artist.is_empty() {
        cmd.extend(["-metadata".to_string(), format!("artist={}", artist)]);
    }

    cmd.extend([
        "-progress".to_string(),
        "pipe:1".to_string(),
        "-nostats".to_string(),
        out_path.to_string(),
    ]);

    Ok(cmd)
}

pub fn run_export<F>(
    cmd: &[String],
    total_seconds: f64,
    progress_callback: Option<F>,
    cancel_flag: Option<Arc<AtomicBool>>,
) -> Result<(), String>
where
    F: Fn(f64) + Send + 'static,
{
    if cmd.is_empty() {
        return Err("empty command".to_string());
    }

    let mut child = Command::new(&cmd[0])
        .args(&cmd[1..])
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to spawn ffmpeg: {}", e))?;

    let stdout = child.stdout.take().expect("stdout");
    let reader = BufReader::new(stdout);
    let time_re = Regex::new(r"out_time=(\d+):(\d+):(\d+(?:\.\d+)?)").unwrap();

    for line in reader.lines().map_while(Result::ok) {
        if let Some(ref cf) = cancel_flag {
            if cf.load(Ordering::SeqCst) {
                let _ = child.kill();
                return Err("cancelled".to_string());
            }
        }

        if let Some(caps) = time_re.captures(&line) {
            if let Some(ref cb) = progress_callback {
                if total_seconds > 0.0 {
                    let h: f64 = caps[1].parse().unwrap_or(0.0);
                    let m: f64 = caps[2].parse().unwrap_or(0.0);
                    let s: f64 = caps[3].parse().unwrap_or(0.0);
                    let done = h * 3600.0 + m * 60.0 + s;
                    cb((done / total_seconds).clamp(0.0, 1.0));
                }
            }
        }
    }

    let status = child.wait().map_err(|e| e.to_string())?;
    if !status.success() {
        return Err(format!("FFmpeg failed with exit code {:?}", status.code()));
    }

    if let Some(ref cb) = progress_callback {
        cb(1.0);
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_format_time() {
        assert_eq!(format_time(83.25, true), "1:23.2");
        assert_eq!(format_time(3723.0, true), "1:02:03.0");
        assert_eq!(format_time(213.4, false), "3:33");
        assert_eq!(format_time(-5.0, true), "0:00.0");
    }

    #[test]
    fn test_parse_time() {
        assert_eq!(parse_time("1:23.5").unwrap(), 83.5);
        assert_eq!(parse_time("83,5").unwrap(), 83.5);
        assert_eq!(parse_time("1:02:03").unwrap(), 3723.0);
        assert_eq!(parse_time(" 7 ").unwrap(), 7.0);

        assert!(parse_time("").is_err());
        assert!(parse_time("abc").is_err());
        assert!(parse_time("1:2:3:4").is_err());
        assert!(parse_time("-1").is_err());
    }

    #[test]
    fn test_crossfade_calculations() {
        let clips = vec![ClipSpec::new("a", 0.0, 10.0), ClipSpec::new("b", 0.0, 3.0)];
        let xf = effective_crossfade(&clips, 5.0);
        assert!((xf - 1.45).abs() < 1e-4);

        assert_eq!(effective_crossfade(&clips[..1], 5.0), 0.0);
        assert!((output_duration(&clips, 1.0) - 12.0).abs() < 1e-4);
        assert!((output_duration(&clips, 0.0) - 13.0).abs() < 1e-4);
    }
}
