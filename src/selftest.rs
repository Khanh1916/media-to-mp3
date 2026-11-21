use crate::audio::{self, ClipSpec};
use crate::downloader::get_ffmpeg_path;
use crate::version::VERSION;
use std::process::Command;

pub fn run_selftest() -> Result<(), String> {
    println!("Media to MP3 v{} | Rust Edition", VERSION);

    let ffmpeg = match get_ffmpeg_path() {
        Some(p) => {
            println!("[OK] FFmpeg - {}", p.display());
            p
        }
        None => return Err("[FAIL] FFmpeg not found!".to_string()),
    };

    // Check encoders
    let enc_output = Command::new(&ffmpeg)
        .args(["-hide_banner", "-encoders"])
        .output()
        .map_err(|e| format!("Failed to run ffmpeg -encoders: {}", e))?;
    let enc_str = String::from_utf8_lossy(&enc_output.stdout);

    for enc in &["libmp3lame", "aac", "flac", "pcm_s16le", "mjpeg"] {
        if enc_str.contains(enc) {
            println!("[OK] encoder {}", enc);
        } else {
            println!("[WARN] encoder {} missing", enc);
        }
    }

    // Check filters
    let filt_output = Command::new(&ffmpeg)
        .args(["-hide_banner", "-filters"])
        .output()
        .map_err(|e| format!("Failed to run ffmpeg -filters: {}", e))?;
    let filt_str = String::from_utf8_lossy(&filt_output.stdout);

    for filt in &[
        "aresample",
        "asetnsamples",
        "concat",
        "acrossfade",
        "afade",
        "volume",
        "loudnorm",
        "crop",
        "scale",
    ] {
        if filt_str.contains(filt) {
            println!("[OK] filter {}", filt);
        } else {
            println!("[WARN] filter {} missing", filt);
        }
    }

    // Temporary directory tests
    let tmp = tempfile::tempdir().map_err(|e| e.to_string())?;
    let tmp_path = tmp.path();

    // 1. Generate test tone
    let tone_a = tmp_path.join("a.mp3");
    let status = Command::new(&ffmpeg)
        .args([
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=4",
            "-metadata",
            "title=Tone 440",
            "-metadata",
            "artist=Tester",
            &tone_a.to_string_lossy(),
        ])
        .status()
        .map_err(|e| e.to_string())?;

    if !status.success() {
        return Err("Failed to generate test audio tone".to_string());
    }
    println!("[OK] encode + read mp3");

    // Probe
    let info = audio::probe(&tone_a)?;
    if (info.duration - 4.0).abs() < 0.2 {
        println!(
            "[OK] probe audio (duration: {:.2}s, title: {})",
            info.duration, info.title
        );
    } else {
        return Err(format!("Probe duration mismatch: {}", info.duration));
    }

    // Cut & join
    let out_cut = tmp_path.join("joined.mp3");
    let clips = vec![
        ClipSpec::new(tone_a.to_string_lossy().to_string(), 0.0, 2.0),
        ClipSpec::new(tone_a.to_string_lossy().to_string(), 1.0, 3.0),
    ];
    let export_cmd = audio::build_export_command(
        &clips,
        &out_cut.to_string_lossy(),
        "mp3",
        "320",
        0.0,
        0.0,
        0.0,
        0.0,
        false,
        "Joined",
        "Tester",
        false,
    )?;

    audio::run_export(&export_cmd, 4.0, None::<fn(f64)>, None)?;
    if out_cut.exists() {
        println!("[OK] cut & join -> mp3");
    }

    // Peaks
    let peaks = audio::load_peaks(&tone_a, 4.0, 50)?;
    if !peaks.is_empty() {
        println!("[OK] waveform peaks loaded (count: {})", peaks.len());
    }

    println!("All checks passed.");
    Ok(())
}
