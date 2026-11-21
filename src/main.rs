use clap::Parser;
use indicatif::{ProgressBar, ProgressStyle};
use media_to_mp3::downloader::{get_ffmpeg_path, MediaDownloader};
use media_to_mp3::gui::MediaToMp3App;
use media_to_mp3::i18n::{self, t};
use media_to_mp3::selftest::run_selftest;
use media_to_mp3::version::VERSION;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

#[derive(Parser, Debug)]
#[command(
    name = "media-to-mp3",
    about = "Media to MP3 Converter in Rust (YouTube & Facebook)",
    version = VERSION
)]
struct Args {
    /// One or more video URLs to download (CLI mode)
    #[arg(name = "URL")]
    urls: Vec<String>,

    /// Display language (vi / en)
    #[arg(long, default_value = "vi")]
    lang: String,

    /// Self-check FFmpeg and functions without network
    #[arg(long)]
    check: bool,

    /// Output folder
    #[arg(short = 'o', long = "output")]
    output: Option<PathBuf>,

    /// Audio format (mp3, m4a, wav, flac)
    #[arg(short = 'f', long = "format", default_value = "mp3")]
    format: String,

    /// MP3 quality (128, 192, 320 kbps)
    #[arg(short = 'b', long = "bitrate", default_value = "320")]
    bitrate: String,

    /// Do not embed thumbnail
    #[arg(long = "no-thumbnail")]
    no_thumbnail: bool,

    /// Do not detect Artist - Title from the title
    #[arg(long = "no-tags")]
    no_tags: bool,

    /// Run in command-line mode
    #[arg(long)]
    cli: bool,

    /// Run background clipboard monitor
    #[arg(long = "monitor")]
    monitor: bool,

    /// Force launch graphical user interface (GUI)
    #[arg(long = "gui")]
    gui: bool,
}

fn main() {
    let args = Args::parse();

    // Set language
    i18n::set_language(&args.lang);

    if args.check {
        if let Err(e) = run_selftest() {
            eprintln!("Selftest error: {}", e);
            std::process::exit(1);
        }
        return;
    }

    if args.monitor {
        println!("{}", t("switch_clipboard", &[]));
        let running = Arc::new(AtomicBool::new(true));
        let r = running.clone();

        let _monitor = media_to_mp3::clipboard::ClipboardMonitor::new(
            move |url, platform| {
                println!(
                    "{}",
                    t(
                        "dlg_detect_title",
                        &[("platform", &platform), ("url", &url)]
                    )
                );
            },
            std::time::Duration::from_millis(800),
        );

        println!("Clipboard monitor active. Press Ctrl+C to exit.");
        while r.load(Ordering::SeqCst) {
            std::thread::sleep(std::time::Duration::from_secs(1));
        }
        return;
    }

    // If explicit CLI mode requested or URLs given, run CLI
    if !args.urls.is_empty() || (args.cli && !args.gui) {
        if args.urls.is_empty() {
            println!("{}", t("cli_need_url", &[]));
            return;
        }

        if get_ffmpeg_path().is_none() {
            eprintln!("{}", t("cli_no_ffmpeg", &[]));
            std::process::exit(1);
        }

        let downloader = MediaDownloader::new(args.output.clone());
        let total = args.urls.len();
        let mut done_count = 0;

        for (idx, url) in args.urls.iter().enumerate() {
            println!(
                "\n[{}/{}] {}",
                idx + 1,
                total,
                t("cli_downloading", &[("url", url)])
            );
            println!("{}", t("cli_format", &[("fmt", &args.format)]));
            println!(
                "{}",
                t(
                    "cli_save_dir",
                    &[("dir", &downloader.download_dir.to_string_lossy())]
                )
            );

            let pb = ProgressBar::new(100);
            pb.set_style(
                ProgressStyle::default_bar()
                    .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}% ({eta})")
                    .unwrap()
                    .progress_chars("#>-"),
            );

            let pb_progress = pb.clone();
            let progress_cb = move |status: &str, percent: f64, _speed: u64, _eta: u64| {
                if status == "converting" {
                    pb_progress.set_message("⚡ Converting...");
                } else {
                    pb_progress.set_position(percent as u64);
                }
            };

            let pb_finish = pb.clone();
            let final_path_arc = Arc::new(std::sync::Mutex::new(String::new()));
            let final_path_clone = final_path_arc.clone();

            let finished_cb = move |path: String| {
                pb_finish.finish_with_message("Done!");
                *final_path_clone.lock().unwrap() = path;
            };

            let error_msg_arc = Arc::new(std::sync::Mutex::new(String::new()));
            let error_msg_clone = error_msg_arc.clone();
            let pb_err = pb.clone();

            let error_cb = move |err: String| {
                pb_err.abandon_with_message(format!("Error: {}", err));
                *error_msg_clone.lock().unwrap() = err;
            };

            downloader.download_audio(
                url,
                &args.format,
                &args.bitrate,
                args.output.as_deref(),
                !args.no_thumbnail,
                !args.no_tags,
                progress_cb,
                finished_cb,
                error_cb,
            );

            let err = error_msg_arc.lock().unwrap().clone();
            if !err.is_empty() {
                eprintln!("\n{}", t("err_prefix", &[("msg", &err)]));
            } else {
                let final_path = final_path_arc.lock().unwrap().clone();
                println!("\n{}", t("cli_done", &[("path", &final_path)]));
                done_count += 1;
            }
        }

        println!(
            "\n{}",
            t(
                "cli_summary",
                &[
                    ("done", &done_count.to_string()),
                    ("total", &total.to_string())
                ]
            )
        );
        return;
    }

    // Default: Launch modern native GUI with eframe
    let native_options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_inner_size([960.0, 680.0])
            .with_min_inner_size([800.0, 560.0])
            .with_title("Media to MP3 - YouTube & Facebook"),
        ..Default::default()
    };

    let _ = eframe::run_native(
        "Media to MP3",
        native_options,
        Box::new(|cc| Ok(Box::new(MediaToMp3App::new(cc)))),
    );
}
