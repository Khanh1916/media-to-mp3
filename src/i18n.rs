use once_cell::sync::Lazy;
use regex::Regex;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;

static STRIP_EMOJI: Lazy<AtomicBool> = Lazy::new(|| {
    #[cfg(target_os = "linux")]
    {
        AtomicBool::new(true)
    }
    #[cfg(not(target_os = "linux"))]
    {
        AtomicBool::new(false)
    }
});

static CURRENT_LANGUAGE: Lazy<Mutex<String>> = Lazy::new(|| Mutex::new("vi".to_string()));

static EMOJI_REGEX: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"[\x{10000}-\x{10ffff}\x{2300}-\x{23ff}\x{2600}-\x{27bf}\x{2b00}-\x{2bff}\x{fe00}-\x{fe0f}]+\s?").unwrap()
});

static STRINGS_MAP: Lazy<HashMap<String, HashMap<String, String>>> = Lazy::new(|| {
    let raw: Value =
        serde_json::from_str(include_str!("strings.json")).expect("valid strings.json");
    let mut map = HashMap::new();
    if let Some(obj) = raw.as_object() {
        for (lang, entries) in obj {
            let mut lang_map = HashMap::new();
            if let Some(entries_obj) = entries.as_object() {
                for (k, v) in entries_obj {
                    if let Some(s) = v.as_str() {
                        lang_map.insert(k.clone(), s.to_string());
                    }
                }
            }
            map.insert(lang.clone(), lang_map);
        }
    }
    map
});

pub fn set_strip_emoji(strip: bool) {
    STRIP_EMOJI.store(strip, Ordering::SeqCst);
}

pub fn get_strip_emoji() -> bool {
    STRIP_EMOJI.load(Ordering::SeqCst)
}

pub fn set_language(lang: &str) {
    if lang == "vi" || lang == "en" {
        let mut l = CURRENT_LANGUAGE.lock().unwrap();
        *l = lang.to_string();
    }
}

pub fn get_language() -> String {
    CURRENT_LANGUAGE.lock().unwrap().clone()
}

pub fn plain(text: &str) -> String {
    EMOJI_REGEX.replace_all(text, "").trim().to_string()
}

pub fn t(key: &str, params: &[(&str, &str)]) -> String {
    let lang = get_language();
    let text = STRINGS_MAP
        .get(&lang)
        .and_then(|m| m.get(key))
        .or_else(|| STRINGS_MAP.get("vi").and_then(|m| m.get(key)))
        .map(|s| s.as_str())
        .unwrap_or(key);

    let mut result = text.to_string();
    for (k, v) in params {
        let pattern = format!("{{{}}}", k);
        result = result.replace(&pattern, v);
    }

    if get_strip_emoji() {
        plain(&result)
    } else {
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_plain_emoji() {
        assert_eq!(plain("🔴 YouTube Video"), "YouTube Video");
        assert_eq!(plain("Tải ⬇ nhạc"), "Tải nhạc");
    }

    #[test]
    fn test_i18n_language_and_params() {
        set_language("en");
        assert_eq!(get_language(), "en");
        let done_msg = t("st_done", &[]);
        assert!(done_msg.contains("Done"));

        set_language("xx");
        assert_eq!(get_language(), "en");

        assert_eq!(t("no_such_key", &[]), "no_such_key");

        set_language("vi");
        assert_eq!(get_language(), "vi");
        let msg = t("st_error", &[("error", "mất kết nối")]);
        assert!(msg.contains("mất kết nối"));
    }
}
