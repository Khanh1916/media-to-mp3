use once_cell::sync::Lazy;
use regex::Regex;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

pub struct AudioFormatDef {
    pub label: &'static str,
    pub bitrates: Option<&'static [&'static str]>,
    pub thumbnail: bool,
}

pub static AUDIO_FORMATS: Lazy<HashMap<&'static str, AudioFormatDef>> = Lazy::new(|| {
    let mut m = HashMap::new();
    m.insert(
        "mp3",
        AudioFormatDef {
            label: "MP3",
            bitrates: Some(&["320", "192", "128"]),
            thumbnail: true,
        },
    );
    m.insert(
        "m4a",
        AudioFormatDef {
            label: "M4A (AAC)",
            bitrates: None,
            thumbnail: true,
        },
    );
    m.insert(
        "wav",
        AudioFormatDef {
            label: "WAV",
            bitrates: None,
            thumbnail: false,
        },
    );
    m.insert(
        "flac",
        AudioFormatDef {
            label: "FLAC",
            bitrates: None,
            thumbnail: true,
        },
    );
    m
});

static NOISE_WORDS: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?i)\b(official|officiel|music|musical|video|audio|lyrics?|visuali[sz]er|m/?v|clip|remaster(?:ed)?|4k|8k|uhd|hd|hq|\d{3,4}p|full|vietsub|engsub|lời bài hát|loi bai hat)\b").unwrap()
});

static BRACKETS: Lazy<Regex> =
    Lazy::new(|| Regex::new(r"\s*[(\[{【]([^()\[\]{}【】]*)[)\]}】]").unwrap());

static PIPE_SEP: Lazy<Regex> = Lazy::new(|| Regex::new(r"\s+[|｜]\s+").unwrap());

static DASH_SEP: Lazy<Regex> = Lazy::new(|| Regex::new(r"\s+[-–—~]\s+").unwrap());

static NON_WORD_DIGIT: Lazy<Regex> = Lazy::new(|| Regex::new(r"[\W\d_]+").unwrap());

pub fn is_noise(text: &str) -> bool {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return true;
    }
    if !NOISE_WORDS.is_match(trimmed) {
        return false;
    }
    let stripped = NOISE_WORDS.replace_all(trimmed, " ");
    let without_symbols = NON_WORD_DIGIT.replace_all(&stripped, "");
    without_symbols.trim().is_empty()
}

pub fn clean_uploader(uploader: Option<&str>) -> String {
    let mut name = uploader.unwrap_or("").trim().to_string();
    if let Some(pos) = name.rfind(" - Topic") {
        if pos + " - Topic".len() == name.len() {
            name.truncate(pos);
        }
    }
    if name.ends_with("VEVO") {
        name.truncate(name.len() - 4);
        name = name.trim().to_string();
    }
    let re_official = Regex::new(r"(?i)\s+Official(?:\s+Channel)?$").unwrap();
    let cleaned = re_official.replace(&name, "");
    cleaned.trim().to_string()
}

pub fn parse_artist_title(title: &str, uploader: Option<&str>) -> (String, String) {
    let text = BRACKETS
        .replace_all(title, |caps: &regex::Captures| {
            let inside = caps.get(1).map_or("", |m| m.as_str());
            if is_noise(inside) {
                ""
            } else {
                let m = caps.get(0).unwrap();
                &title[m.start()..m.end()]
            }
        })
        .trim()
        .to_string();

    let pipe_parts: Vec<&str> = PIPE_SEP
        .split(&text)
        .map(|p| p.trim())
        .filter(|p| !p.is_empty() && !is_noise(p))
        .collect();

    let (artist, mut track) = if pipe_parts.len() >= 2 {
        (pipe_parts[0].to_string(), pipe_parts[1].to_string())
    } else {
        let base_text = if !pipe_parts.is_empty() {
            pipe_parts[0]
        } else {
            &text
        };
        let dash_parts: Vec<&str> = DASH_SEP.split(base_text).map(|p| p.trim()).collect();
        if dash_parts.len() == 2 && !dash_parts[0].is_empty() && !dash_parts[1].is_empty() {
            (dash_parts[0].to_string(), dash_parts[1].to_string())
        } else {
            (clean_uploader(uploader), base_text.to_string())
        }
    };

    track = track
        .trim_matches(|c| c == ' ' || c == '-' || c == '–' || c == '—' || c == '|')
        .to_string();
    if track.is_empty() {
        track = title.trim().to_string();
    }

    (artist.trim().to_string(), track)
}

pub fn identify_platform(url: &str) -> &'static str {
    let lower = url.to_lowercase();
    if lower.contains("youtube.com") || lower.contains("youtu.be") {
        "YouTube"
    } else if lower.contains("facebook.com") || lower.contains("fb.watch") {
        "Facebook"
    } else if lower.contains("tiktok.com") {
        "TikTok"
    } else if lower.contains("soundcloud.com") {
        "SoundCloud"
    } else {
        "Video Link"
    }
}

pub fn is_valid_url(url: &str) -> bool {
    let trimmed = url.trim();
    if trimmed.is_empty() {
        return false;
    }
    let pattern = Regex::new(
        r"(?i)^(https?://)?(www\.|m\.|web\.)?(youtube\.com|youtu\.be|facebook\.com|fb\.watch|tiktok\.com|soundcloud\.com)/[^\s]+$",
    ).unwrap();
    pattern.is_match(trimmed)
}

pub fn get_ffmpeg_path() -> Option<PathBuf> {
    // 1. System PATH
    if let Ok(path) = which::which("ffmpeg") {
        return Some(path);
    }

    // 2. Local check
    for candidate in &["ffmpeg.exe", "ffmpeg", "bin/ffmpeg.exe", "bin/ffmpeg"] {
        let p = PathBuf::from(candidate);
        if p.is_file() {
            return Some(p);
        }
    }

    // 3. Common Python imageio_ffmpeg or system paths
    #[cfg(target_os = "windows")]
    {
        if let Ok(local_appdata) = std::env::var("LOCALAPPDATA") {
            let py_scripts = PathBuf::from(&local_appdata)
                .join("Programs")
                .join("Python")
                .join("Python313")
                .join("Scripts")
                .join("ffmpeg.exe");
            if py_scripts.is_file() {
                return Some(py_scripts);
            }
        }
    }

    None
}

pub fn default_download_dir() -> PathBuf {
    if let Some(music) = dirs::audio_dir() {
        if music.exists() {
            return music;
        }
    }
    dirs::download_dir().unwrap_or_else(|| PathBuf::from("."))
}

#[derive(Clone)]
pub struct MediaDownloader {
    pub download_dir: PathBuf,
    pub is_cancelled: Arc<AtomicBool>,
}

impl MediaDownloader {
    pub fn new(download_dir: Option<PathBuf>) -> Self {
        Self {
            download_dir: download_dir.unwrap_or_else(default_download_dir),
            is_cancelled: Arc::new(AtomicBool::new(false)),
        }
    }

    pub fn cancel(&self) {
        self.is_cancelled.store(true, Ordering::SeqCst);
    }

    #[allow(clippy::too_many_arguments)]
    pub fn download_audio<P, F, E>(
        &self,
        url: &str,
        fmt: &str,
        bitrate: &str,
        output_dir: Option<&Path>,
        embed_thumbnail: bool,
        parse_metadata: bool,
        progress_callback: P,
        finished_callback: F,
        error_callback: E,
    ) where
        P: Fn(&str, f64, u64, u64) + Send + 'static, // status, percent, speed, eta
        F: Fn(String) + Send + 'static,              // final path
        E: Fn(String) + Send + 'static,              // error message
    {
        self.is_cancelled.store(false, Ordering::SeqCst);
        let ffmpeg = match get_ffmpeg_path() {
            Some(p) => p,
            None => {
                error_callback("FFmpeg not found".to_string());
                return;
            }
        };

        let target_dir = output_dir.unwrap_or(&self.download_dir);
        let out_template = target_dir.join("%(title)s.%(ext)s");

        // Prefer yt-dlp executable, fallback to python -m yt_dlp
        let (prog, mut args) = if which::which("yt-dlp").is_ok() {
            ("yt-dlp".to_string(), Vec::new())
        } else {
            (
                "python".to_string(),
                vec!["-m".to_string(), "yt_dlp".to_string()],
            )
        };

        args.push("--extract-audio".to_string());
        args.push("--audio-format".to_string());
        args.push(fmt.to_string());

        if fmt == "mp3" {
            args.push("--audio-quality".to_string());
            args.push(format!("{}k", bitrate));
        }

        args.push("--ffmpeg-location".to_string());
        args.push(ffmpeg.to_string_lossy().to_string());

        args.push("-o".to_string());
        args.push(out_template.to_string_lossy().to_string());

        if embed_thumbnail && fmt != "wav" {
            args.push("--embed-thumbnail".to_string());
        }

        if parse_metadata {
            args.push("--add-metadata".to_string());
        }

        args.push("--newline".to_string());
        args.push(url.to_string());

        let mut child = match Command::new(&prog)
            .args(&args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(c) => c,
            Err(e) => {
                error_callback(format!("Failed to run yt-dlp: {}", e));
                return;
            }
        };

        use std::io::{BufRead, BufReader};
        let stdout = child.stdout.take().expect("stdout");
        let reader = BufReader::new(stdout);

        let dl_re = Regex::new(r"\[download\]\s+(\d+(?:\.\d+)?)%").unwrap();
        let mut final_path = String::new();

        for line in reader.lines().map_while(Result::ok) {
            if self.is_cancelled.load(Ordering::SeqCst) {
                let _ = child.kill();
                error_callback("cancelled".to_string());
                return;
            }

            if line.contains("[ExtractAudio]") || line.contains("[FixupM4a]") {
                progress_callback("converting", 100.0, 0, 0);
            } else if let Some(caps) = dl_re.captures(&line) {
                if let Ok(pct) = caps[1].parse::<f64>() {
                    progress_callback("downloading", pct, 1024 * 512, 5);
                }
            } else if line.contains("[download] Destination:") {
                if let Some(dest) = line.split("Destination:").nth(1) {
                    final_path = dest.trim().to_string();
                }
            }
        }

        let status = child.wait();
        match status {
            Ok(s) if s.success() => {
                finished_callback(final_path);
            }
            Ok(s) => {
                error_callback(format!("yt-dlp exited with code {:?}", s.code()));
            }
            Err(e) => {
                error_callback(e.to_string());
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_artist_title() {
        let (artist, track) = parse_artist_title(
            "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
            None,
        );
        assert_eq!(artist, "Rick Astley");
        assert_eq!(track, "Never Gonna Give You Up");

        let (artist2, track2) = parse_artist_title(
            "SƠN TÙNG M-TP | CHÚNG TA CỦA TƯƠNG LAI | OFFICIAL MUSIC VIDEO",
            None,
        );
        assert_eq!(artist2, "SƠN TÙNG M-TP");
        assert_eq!(track2, "CHÚNG TA CỦA TƯƠNG LAI");

        let (artist3, track3) = parse_artist_title("Đen - Bài Này Chill Phết ft. MIN (M/V)", None);
        assert_eq!(artist3, "Đen");
        assert_eq!(track3, "Bài Này Chill Phết ft. MIN");

        let (artist4, track4) =
            parse_artist_title("Shape of You [Official Lyric Video]", Some("Ed Sheeran"));
        assert_eq!(artist4, "Ed Sheeran");
        assert_eq!(track4, "Shape of You");
    }

    #[test]
    fn test_platform_identification() {
        assert_eq!(
            identify_platform("https://www.youtube.com/watch?v=123"),
            "YouTube"
        );
        assert_eq!(identify_platform("https://fb.watch/123"), "Facebook");
        assert_eq!(
            identify_platform("https://tiktok.com/@user/video/123"),
            "TikTok"
        );
    }
}
