use arboard::Clipboard;
use once_cell::sync::Lazy;
use regex::Regex;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread::{self, JoinHandle};
use std::time::Duration;

static YT_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?i)https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch\?v=|shorts/|live/|embed/)|youtu\.be/)[a-zA-Z0-9_-]+[^\s]*").unwrap()
});

static FB_PATTERN: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"(?i)https?://(?:www\.|m\.|web\.)?(?:facebook\.com/(?:watch/?\?v=|reel/|[^/\s]+/videos/|share/(?:v|r)/)|fb\.watch/)[a-zA-Z0-9_-]+[^\s]*").unwrap()
});

pub fn extract_supported_url(text: &str) -> Option<(String, String)> {
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return None;
    }

    if let Some(m) = YT_PATTERN.find(trimmed) {
        return Some((m.as_str().to_string(), "YouTube".to_string()));
    }

    if let Some(m) = FB_PATTERN.find(trimmed) {
        return Some((m.as_str().to_string(), "Facebook".to_string()));
    }

    None
}

pub struct ClipboardMonitor {
    running: Arc<AtomicBool>,
    enabled: Arc<AtomicBool>,
    handle: Option<JoinHandle<()>>,
}

impl ClipboardMonitor {
    pub fn new<F>(on_detected: F, check_interval: Duration) -> Self
    where
        F: Fn(String, String) + Send + Sync + 'static,
    {
        let running = Arc::new(AtomicBool::new(true));
        let enabled = Arc::new(AtomicBool::new(true));

        let running_clone = running.clone();
        let enabled_clone = enabled.clone();

        let handle = thread::spawn(move || {
            let mut last_copied = String::new();
            if let Ok(mut cb) = Clipboard::new() {
                if let Ok(text) = cb.get_text() {
                    last_copied = text.trim().to_string();
                }
            }

            while running_clone.load(Ordering::SeqCst) {
                if enabled_clone.load(Ordering::SeqCst) {
                    if let Ok(mut cb) = Clipboard::new() {
                        if let Ok(current_text) = cb.get_text() {
                            let trimmed = current_text.trim();
                            if !trimmed.is_empty() && trimmed != last_copied {
                                last_copied = trimmed.to_string();
                                if let Some((url, platform)) = extract_supported_url(trimmed) {
                                    on_detected(url, platform);
                                }
                            }
                        }
                    }
                }
                thread::sleep(check_interval);
            }
        });

        Self {
            running,
            enabled,
            handle: Some(handle),
        }
    }

    pub fn set_enabled(&self, val: bool) {
        self.enabled.store(val, Ordering::SeqCst);
    }

    pub fn is_enabled(&self) -> bool {
        self.enabled.load(Ordering::SeqCst)
    }

    pub fn stop(&mut self) {
        self.running.store(false, Ordering::SeqCst);
        if let Some(h) = self.handle.take() {
            let _ = h.join();
        }
    }
}

impl Drop for ClipboardMonitor {
    fn drop(&mut self) {
        self.stop();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extract_youtube_url() {
        let text = "Check out this song: https://www.youtube.com/watch?v=dQw4w9WgXcQ it is great";
        let res = extract_supported_url(text);
        assert!(res.is_some());
        let (url, platform) = res.unwrap();
        assert_eq!(platform, "YouTube");
        assert!(url.contains("youtube.com/watch?v=dQw4w9WgXcQ"));
    }

    #[test]
    fn test_extract_facebook_url() {
        let text = "Video: https://fb.watch/xyz123456/ watch now";
        let res = extract_supported_url(text);
        assert!(res.is_some());
        let (url, platform) = res.unwrap();
        assert_eq!(platform, "Facebook");
        assert!(url.contains("fb.watch/xyz123456/"));
    }

    #[test]
    fn test_unsupported_url() {
        let text = "https://example.com/not-media";
        assert!(extract_supported_url(text).is_none());
    }
}
