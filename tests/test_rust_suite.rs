use media_to_mp3::audio::{self, ClipSpec};
use media_to_mp3::clipboard::extract_supported_url;
use media_to_mp3::config::{load_settings, save_settings, Settings};
use media_to_mp3::downloader::parse_artist_title;
use media_to_mp3::i18n::{self, t};

#[test]
fn test_config_lifecycle() {
    let tmp = tempfile::tempdir().unwrap();
    let path = tmp.path().join("settings.json");

    // Missing file gives default
    assert_eq!(load_settings(Some(&path)), Settings::default());

    // Save and reload
    let custom = Settings {
        format: "flac".to_string(),
        bitrate: "192".to_string(),
        language: "en".to_string(),
        ..Default::default()
    };
    save_settings(&custom, Some(&path)).unwrap();

    let loaded = load_settings(Some(&path));
    assert_eq!(loaded, custom);
}

#[test]
fn test_i18n_translation_and_formatting() {
    i18n::set_language("vi");
    let vi_msg = t(
        "queue_summary",
        &[
            ("total", "5"),
            ("active", "1"),
            ("pending", "2"),
            ("done", "2"),
        ],
    );
    assert!(vi_msg.contains("5 bài"));
    assert!(vi_msg.contains("1 đang tải"));

    i18n::set_language("en");
    let en_msg = t(
        "queue_summary",
        &[
            ("total", "5"),
            ("active", "1"),
            ("pending", "2"),
            ("done", "2"),
        ],
    );
    assert!(en_msg.contains("5 items"));
    assert!(en_msg.contains("1 downloading"));
    i18n::set_language("vi");
}

#[test]
fn test_downloader_parser_comprehensive() {
    let cases = vec![
        (
            "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
            None,
            ("Rick Astley", "Never Gonna Give You Up"),
        ),
        (
            "SƠN TÙNG M-TP | CHÚNG TA CỦA TƯƠNG LAI | OFFICIAL MUSIC VIDEO",
            None,
            ("SƠN TÙNG M-TP", "CHÚNG TA CỦA TƯƠNG LAI"),
        ),
        (
            "Đen - Bài Này Chill Phết ft. MIN (M/V)",
            None,
            ("Đen", "Bài Này Chill Phết ft. MIN"),
        ),
        (
            "Artist – Song (Live at Wembley) [Remix]",
            None,
            ("Artist", "Song (Live at Wembley) [Remix]"),
        ),
        (
            "Shape of You [Official Lyric Video]",
            Some("Ed Sheeran"),
            ("Ed Sheeran", "Shape of You"),
        ),
        ("Song Name", Some("Artist - Topic"), ("Artist", "Song Name")),
    ];

    for (input, uploader, (expected_artist, expected_track)) in cases {
        let (artist, track) = parse_artist_title(input, uploader);
        assert_eq!(
            artist, expected_artist,
            "Failed artist for input: {}",
            input
        );
        assert_eq!(track, expected_track, "Failed track for input: {}", input);
    }
}

#[test]
fn test_audio_crossfade_and_duration() {
    let clips = vec![
        ClipSpec::new("track1.mp3", 0.0, 10.0),
        ClipSpec::new("track2.mp3", 0.0, 5.0),
    ];
    let xf = audio::effective_crossfade(&clips, 2.0);
    assert!(xf > 0.0 && xf <= 2.0);

    let dur = audio::output_duration(&clips, 2.0);
    assert!((13.0..15.0).contains(&dur));
}

#[test]
fn test_audio_export_command_builder() {
    let clips = vec![
        ClipSpec::new("a.mp3", 5.0, 15.0),
        ClipSpec::new("b.m4a", 0.0, 20.0),
    ];
    let cmd = audio::build_export_command(
        &clips,
        "out.mp3",
        "mp3",
        "320",
        1.0,
        2.0,
        -3.0,
        1.5,
        true,
        "Test Title",
        "Test Artist",
        true,
    )
    .unwrap();

    let cmd_str = cmd.join(" ");
    assert!(cmd_str.contains("out.mp3"));
    assert!(cmd_str.contains("-filter_complex"));
    assert!(cmd_str.contains("acrossfade=d=1.500"));
    assert!(cmd_str.contains("loudnorm"));
    assert!(cmd_str.contains("volume=-3.0dB"));
    assert!(cmd_str.contains("title=Test Title"));
    assert!(cmd_str.contains("artist=Test Artist"));
}

#[test]
fn test_clipboard_detection() {
    let sample = "Check https://www.youtube.com/watch?v=dQw4w9WgXcQ now";
    let res = extract_supported_url(sample);
    assert!(res.is_some());
    let (url, platform) = res.unwrap();
    assert_eq!(platform, "YouTube");
    assert!(url.contains("youtube.com/watch?v=dQw4w9WgXcQ"));
}
