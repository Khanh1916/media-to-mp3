use serde::{Deserialize, Serialize};
use std::fs::{self, File};
use std::io::Write;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Settings {
    pub download_dir: String,
    pub format: String,
    pub bitrate: String,
    pub embed_thumbnail: bool,
    pub parse_metadata: bool,
    pub clipboard_monitor: bool,
    pub language: String,
    pub window_geometry: String,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            download_dir: String::new(),
            format: "mp3".to_string(),
            bitrate: "320".to_string(),
            embed_thumbnail: true,
            parse_metadata: true,
            clipboard_monitor: true,
            language: "vi".to_string(),
            window_geometry: String::new(),
        }
    }
}

pub fn config_dir() -> PathBuf {
    #[cfg(target_os = "windows")]
    {
        if let Ok(appdata) = std::env::var("APPDATA") {
            return PathBuf::from(appdata).join("MediaToMP3");
        }
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("AppData")
            .join("Roaming")
            .join("MediaToMP3")
    }
    #[cfg(target_os = "macos")]
    {
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join("Library")
            .join("Application Support")
            .join("MediaToMP3")
    }
    #[cfg(not(any(target_os = "windows", target_os = "macos")))]
    {
        if let Ok(xdg) = std::env::var("XDG_CONFIG_HOME") {
            return PathBuf::from(xdg).join("media-to-mp3");
        }
        dirs::home_dir()
            .unwrap_or_else(|| PathBuf::from("."))
            .join(".config")
            .join("media-to-mp3")
    }
}

pub fn config_path() -> PathBuf {
    config_dir().join("settings.json")
}

pub fn load_settings<P: AsRef<Path>>(path: Option<P>) -> Settings {
    let resolved_path = match path {
        Some(p) => p.as_ref().to_path_buf(),
        None => config_path(),
    };

    if !resolved_path.exists() {
        return Settings::default();
    }

    let content = match fs::read_to_string(&resolved_path) {
        Ok(c) => c,
        Err(_) => return Settings::default(),
    };

    let raw: serde_json::Value = match serde_json::from_str(&content) {
        Ok(v) => v,
        Err(_) => return Settings::default(),
    };

    let obj = match raw.as_object() {
        Some(o) => o,
        None => return Settings::default(),
    };

    let mut settings = Settings::default();

    if let Some(val) = obj.get("download_dir").and_then(|v| v.as_str()) {
        settings.download_dir = val.to_string();
    }
    if let Some(val) = obj.get("format").and_then(|v| v.as_str()) {
        settings.format = val.to_string();
    }
    if let Some(val) = obj.get("bitrate").and_then(|v| v.as_str()) {
        settings.bitrate = val.to_string();
    }
    if let Some(val) = obj.get("embed_thumbnail").and_then(|v| v.as_bool()) {
        settings.embed_thumbnail = val;
    }
    if let Some(val) = obj.get("parse_metadata").and_then(|v| v.as_bool()) {
        settings.parse_metadata = val;
    }
    if let Some(val) = obj.get("clipboard_monitor").and_then(|v| v.as_bool()) {
        settings.clipboard_monitor = val;
    }
    if let Some(val) = obj.get("language").and_then(|v| v.as_str()) {
        settings.language = val.to_string();
    }
    if let Some(val) = obj.get("window_geometry").and_then(|v| v.as_str()) {
        settings.window_geometry = val.to_string();
    }

    settings
}

pub fn save_settings<P: AsRef<Path>>(settings: &Settings, path: Option<P>) -> std::io::Result<()> {
    let resolved_path = match path {
        Some(p) => p.as_ref().to_path_buf(),
        None => config_path(),
    };

    if let Some(parent) = resolved_path.parent() {
        fs::create_dir_all(parent)?;
    }

    let tmp_path = resolved_path.with_extension("tmp");
    let json_str = serde_json::to_string_pretty(settings)?;

    {
        let mut file = File::create(&tmp_path)?;
        file.write_all(json_str.as_bytes())?;
        file.sync_all()?;
    }

    fs::rename(&tmp_path, &resolved_path)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_missing_file_gives_defaults() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("sub").join("settings.json");
        assert_eq!(load_settings(Some(&path)), Settings::default());
    }

    #[test]
    fn test_round_trip() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("sub").join("settings.json");
        let settings = Settings {
            format: "flac".to_string(),
            language: "en".to_string(),
            embed_thumbnail: false,
            ..Default::default()
        };

        save_settings(&settings, Some(&path)).unwrap();
        assert_eq!(load_settings(Some(&path)), settings);
        assert!(!path.with_extension("tmp").exists());
    }

    #[test]
    fn test_wrong_types_and_unknown_keys_are_ignored() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("sub").join("settings.json");
        fs::create_dir_all(path.parent().unwrap()).unwrap();

        let json = r#"{"format": 3, "embed_thumbnail": "yes", "language": "en", "other": 1}"#;
        fs::write(&path, json).unwrap();

        let loaded = load_settings(Some(&path));
        assert_eq!(loaded.format, "mp3");
        assert!(loaded.embed_thumbnail);
        assert_eq!(loaded.language, "en");
    }

    #[test]
    fn test_corrupt_file_gives_defaults() {
        let tmp = tempfile::tempdir().unwrap();
        let path = tmp.path().join("sub").join("settings.json");
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(&path, "{not json").unwrap();

        assert_eq!(load_settings(Some(&path)), Settings::default());
    }
}
